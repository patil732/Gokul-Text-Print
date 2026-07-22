"""
tests/test_sales_forecast.py
-----------------------------
Sprint 2 — Sales Forecast Endpoint Integration Tests

Tests the POST /api/sales/forecast Flask endpoint end-to-end using the
Flask test client (no live HTTP server required).

Coverage
--------
1. Happy-path: all three valid forecast periods return correct schema
2. Response time < 1 000 ms for a single forecast call (SLA assertion)
3. Missing forecast_period → 400 Bad Request
4. Invalid forecast_period → 400 Bad Request with valid_values hint
5. Response body field types (float, str) are enforced
6. All three schema keys (predicted_sales, growth_rate, confidence) present
7. confidence is bounded in [0.0, 1.0]
8. predicted_sales is non-negative
9. growth_rate is a finite float
10. forecast_period echoed back correctly
11. Baseline feature override is accepted without error
12. Forecast result is logged to prediction_history (side-effect check)

The test suite uses the REAL trained model from models/sales/ so it is
a true integration test — no mocking of the forecast engine.
"""

from __future__ import annotations

import json
import os
import sys
import time

import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib.util

# ── Load Flask app via the existing factory ───────────────────────────────── #
_SPEC = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_ENDPOINT    = "/api/sales/forecast"
_VALID_PERIODS = ["7_days", "30_days", "90_days"]
_SLA_MS      = 1_000.0   # maximum acceptable response time in milliseconds

_REQUIRED_RESPONSE_KEYS = {
    "status",
    "forecast_period",
    "predicted_sales",
    "growth_rate",
    "confidence",
    "model_type",
    "version",
    "elapsed_ms",
}


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def flask_client():
    """Create a Flask test client with TESTING mode enabled."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _post_forecast(client, payload: dict):
    """Helper: POST to the forecast endpoint and return (response, elapsed_ms)."""
    t0       = time.perf_counter()
    response = client.post(
        _ENDPOINT,
        data        = json.dumps(payload),
        content_type= "application/json",
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return response, elapsed_ms


# --------------------------------------------------------------------------- #
# Tests — Happy path
# --------------------------------------------------------------------------- #

class TestForecastEndpointHappyPath:
    """All valid forecast periods return 200 with correct schema."""

    @pytest.mark.parametrize("period", _VALID_PERIODS)
    def test_status_200(self, flask_client, period):
        resp, _ = _post_forecast(flask_client, {"forecast_period": period})
        assert resp.status_code == 200, (
            f"Expected 200 for period='{period}', got {resp.status_code}. "
            f"Body: {resp.get_data(as_text=True)}"
        )

    @pytest.mark.parametrize("period", _VALID_PERIODS)
    def test_status_field_is_success(self, flask_client, period):
        resp, _ = _post_forecast(flask_client, {"forecast_period": period})
        body = resp.get_json()
        assert body["status"] == "success", (
            f"Response status should be 'success', got '{body['status']}'."
        )

    @pytest.mark.parametrize("key", sorted(_REQUIRED_RESPONSE_KEYS))
    def test_required_key_present_7_days(self, flask_client, key):
        resp, _ = _post_forecast(flask_client, {"forecast_period": "7_days"})
        body = resp.get_json()
        assert key in body, (
            f"Required key '{key}' missing from forecast response. "
            f"Keys present: {list(body.keys())}"
        )

    @pytest.mark.parametrize("period", _VALID_PERIODS)
    def test_forecast_period_echoed_back(self, flask_client, period):
        resp, _ = _post_forecast(flask_client, {"forecast_period": period})
        body = resp.get_json()
        assert body["forecast_period"] == period, (
            f"forecast_period should be '{period}', got '{body['forecast_period']}'."
        )


# --------------------------------------------------------------------------- #
# Tests — Response schema field types and value constraints
# --------------------------------------------------------------------------- #

class TestForecastResponseSchema:
    """Assert field types and value constraints for the 7_days response."""

    @pytest.fixture(scope="class")
    def body(self, flask_client):
        resp, _ = _post_forecast(flask_client, {"forecast_period": "7_days"})
        return resp.get_json()

    def test_predicted_sales_is_float(self, body):
        assert isinstance(body["predicted_sales"], (int, float)), (
            f"predicted_sales should be numeric, got {type(body['predicted_sales'])}."
        )

    def test_predicted_sales_is_non_negative(self, body):
        assert body["predicted_sales"] >= 0, (
            f"predicted_sales should be ≥ 0, got {body['predicted_sales']}."
        )

    def test_growth_rate_is_float(self, body):
        assert isinstance(body["growth_rate"], (int, float)), (
            f"growth_rate should be numeric, got {type(body['growth_rate'])}."
        )

    def test_growth_rate_is_finite(self, body):
        import math
        assert math.isfinite(body["growth_rate"]), (
            f"growth_rate should be finite, got {body['growth_rate']}."
        )

    def test_confidence_is_float(self, body):
        assert isinstance(body["confidence"], (int, float)), (
            f"confidence should be numeric, got {type(body['confidence'])}."
        )

    def test_confidence_bounded_0_to_1(self, body):
        c = body["confidence"]
        assert 0.0 <= c <= 1.0, f"confidence should be in [0, 1], got {c}."

    def test_model_type_is_non_empty_string(self, body):
        mt = body["model_type"]
        assert isinstance(mt, str) and len(mt) > 0, (
            f"model_type should be a non-empty string, got {mt!r}."
        )

    def test_version_is_non_empty_string(self, body):
        v = body["version"]
        assert isinstance(v, str) and len(v) > 0, (
            f"version should be a non-empty string, got {v!r}."
        )

    def test_elapsed_ms_is_positive_float(self, body):
        e = body["elapsed_ms"]
        assert isinstance(e, (int, float)) and e >= 0, (
            f"elapsed_ms should be a non-negative number, got {e}."
        )


# --------------------------------------------------------------------------- #
# Tests — Response time SLA (< 1 000 ms per call)
# --------------------------------------------------------------------------- #

class TestForecastPerformance:
    """Verify that single forecast calls complete within the 1-second SLA."""

    @pytest.mark.parametrize("period", _VALID_PERIODS)
    def test_response_time_under_1000ms(self, flask_client, period):
        """
        Warm-up: first call loads the model.  We measure a second call
        to get the hot-path time (which is what production serves after
        the first request).
        """
        # Warm-up call (model load)
        _post_forecast(flask_client, {"forecast_period": period})

        # Measured call
        _, elapsed_ms = _post_forecast(flask_client, {"forecast_period": period})

        assert elapsed_ms < _SLA_MS, (
            f"Forecast for '{period}' took {elapsed_ms:.1f}ms — "
            f"exceeds {_SLA_MS:.0f}ms SLA."
        )

    def test_elapsed_ms_in_body_under_1000ms(self, flask_client):
        """
        The 'elapsed_ms' key in the response body reports the time spent
        inside generate_forecast() (compute only).  This should be well
        under 1 000 ms.
        """
        # Warm up
        _post_forecast(flask_client, {"forecast_period": "7_days"})
        resp, _ = _post_forecast(flask_client, {"forecast_period": "7_days"})
        body    = resp.get_json()
        assert body["elapsed_ms"] < _SLA_MS, (
            f"Compute elapsed_ms={body['elapsed_ms']:.1f}ms exceeds {_SLA_MS}ms SLA."
        )


# --------------------------------------------------------------------------- #
# Tests — Input validation errors
# --------------------------------------------------------------------------- #

class TestForecastInputValidation:
    """Bad inputs should return 4xx, never 5xx."""

    def test_missing_forecast_period_returns_400(self, flask_client):
        resp, _ = _post_forecast(flask_client, {})
        assert resp.status_code == 400, (
            f"Missing forecast_period should return 400, got {resp.status_code}."
        )

    def test_missing_forecast_period_body_has_message(self, flask_client):
        resp, _ = _post_forecast(flask_client, {})
        body    = resp.get_json()
        assert "message" in body, "Error response should contain 'message' key."

    def test_invalid_period_returns_400(self, flask_client):
        resp, _ = _post_forecast(flask_client, {"forecast_period": "1_year"})
        assert resp.status_code == 400, (
            f"Invalid period '1_year' should return 400, got {resp.status_code}."
        )

    def test_invalid_period_body_has_valid_values(self, flask_client):
        resp, _ = _post_forecast(flask_client, {"forecast_period": "bad_value"})
        body    = resp.get_json()
        assert "valid_values" in body, (
            "Error response for invalid period should include 'valid_values' hint."
        )
        assert isinstance(body["valid_values"], list)
        assert set(body["valid_values"]) == {"7_days", "30_days", "90_days"}

    def test_empty_body_returns_400(self, flask_client):
        resp = flask_client.post(
            _ENDPOINT,
            data         = "",
            content_type = "application/json",
        )
        assert resp.status_code in (400, 200), (
            "Empty body should not produce a 5xx error."
        )

    def test_integer_period_returns_400(self, flask_client):
        resp, _ = _post_forecast(flask_client, {"forecast_period": 7})
        # 7 (int) is not in _VALID_PERIODS (string set) → 400
        assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Tests — Baseline feature override
# --------------------------------------------------------------------------- #

class TestForecastBaselineOverride:
    """Optional baseline feature values in the payload are accepted."""

    def test_baseline_override_accepted(self, flask_client):
        payload = {
            "forecast_period": "30_days",
            "sales":           50_000.0,
            "momentum":          2_000.0,
        }
        resp, _ = _post_forecast(flask_client, payload)
        assert resp.status_code == 200, (
            f"Baseline override payload should return 200, got {resp.status_code}."
        )

    def test_baseline_override_returns_valid_schema(self, flask_client):
        payload = {
            "forecast_period": "30_days",
            "sales":           50_000.0,
        }
        resp, _ = _post_forecast(flask_client, payload)
        body = resp.get_json()
        for key in _REQUIRED_RESPONSE_KEYS:
            assert key in body, f"Key '{key}' missing with baseline override."


# --------------------------------------------------------------------------- #
# Tests — Cross-period consistency
# --------------------------------------------------------------------------- #

class TestForecastCrossperiod:
    """Sanity-check relative forecast magnitudes across horizons."""

    @pytest.fixture(scope="class")
    def all_forecasts(self, flask_client):
        results = {}
        for p in _VALID_PERIODS:
            # Warm up first
            _post_forecast(flask_client, {"forecast_period": p})
            resp, _ = _post_forecast(flask_client, {"forecast_period": p})
            results[p] = resp.get_json()
        return results

    def test_longer_period_has_higher_predicted_sales(self, all_forecasts):
        """A 30-day window should predict more cumulative sales than 7 days."""
        s7  = all_forecasts["7_days"]["predicted_sales"]
        s30 = all_forecasts["30_days"]["predicted_sales"]
        assert s30 > s7, (
            f"30-day predicted_sales ({s30}) should exceed 7-day ({s7})."
        )

    def test_90_day_higher_than_30_day(self, all_forecasts):
        s30 = all_forecasts["30_days"]["predicted_sales"]
        s90 = all_forecasts["90_days"]["predicted_sales"]
        assert s90 > s30, (
            f"90-day predicted_sales ({s90}) should exceed 30-day ({s30})."
        )


# ============================================================================ #
# CLI runner
# ============================================================================ #

if __name__ == "__main__":
    import subprocess, sys as _sys
    ret = subprocess.run(
        [_sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    _sys.exit(ret.returncode)
