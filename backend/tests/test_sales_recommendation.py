"""
tests/test_sales_recommendation.py
------------------------------------
Sprint 2 — Sales Recommendation Rules Engine Unit Tests.

Two test layers:
  1. Unit tests for apply_rules() — pure function, no I/O, no mocking.
     Covers all three rule branches and boundary / edge values.

  2. Integration tests for GET /api/sales/recommendation using the real
     Flask test client.  The forecast engine is monkey-patched so tests
     are deterministic and fast (no model disk I/O required).

Test classes
------------
  TestRulesEngineUnit          — apply_rules() correctness for all branches
  TestRulesEngineBoundary      — exact threshold edge cases
  TestApplyRulesReasonStrings  — reason content contains key data
  TestGetRecommendationEndpoint — Flask integration (decision, reason, confidence)
  TestRecommendationSchema     — full response schema validation
  TestRecommendationValidation — invalid period query param → 400
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from typing import Any, Dict
from unittest.mock import patch, MagicMock

import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.sales.recommendation import (
    apply_rules,
    DECISION_INCREASE,
    DECISION_REDUCE,
    DECISION_MAINTAIN,
    get_recommendation,
)

# ── Flask app factory ─────────────────────────────────────────────────────── #
_SPEC    = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app

# --------------------------------------------------------------------------- #
# Shared constants
# --------------------------------------------------------------------------- #

_INCREASE_THRESHOLD = 15.0
_REDUCE_THRESHOLD   = -10.0

_REQUIRED_ENDPOINT_KEYS = {
    "status", "decision", "reason", "confidence",
    "growth_rate", "forecast_period", "predicted_sales",
    "model_type", "version",
}

# Synthetic forecast stubs keyed by growth_rate scenario
def _fake_forecast(growth_rate: float, confidence: float = 0.75) -> Dict[str, Any]:
    return {
        "forecast_period":  "30_days",
        "predicted_sales":  600_000.0,
        "growth_rate":      growth_rate,
        "confidence":       confidence,
        "model_type":       "xgboost",
        "version":          "test_v1",
        "elapsed_ms":       3.5,
    }


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================================ #
# 1. Unit tests — apply_rules() only, no I/O
# ============================================================================ #

class TestRulesEngineUnit:
    """
    Verify that apply_rules() maps growth_rate to the correct decision
    for all three branches.
    """

    # ── Branch 1: growth_rate > 15 % → Increase Production ─────────── #

    @pytest.mark.parametrize("growth_rate", [15.01, 20.0, 50.0, 100.0])
    def test_high_growth_gives_increase_decision(self, growth_rate):
        result = apply_rules(growth_rate, confidence=0.80)
        assert result["decision"] == DECISION_INCREASE, (
            f"growth_rate={growth_rate:.2f}% should give '{DECISION_INCREASE}', "
            f"got '{result['decision']}'."
        )

    # ── Branch 2: growth_rate < -10 % → Reduce Inventory ───────────── #

    @pytest.mark.parametrize("growth_rate", [-10.01, -20.0, -50.0, -100.0])
    def test_low_growth_gives_reduce_decision(self, growth_rate):
        result = apply_rules(growth_rate, confidence=0.65)
        assert result["decision"] == DECISION_REDUCE, (
            f"growth_rate={growth_rate:.2f}% should give '{DECISION_REDUCE}', "
            f"got '{result['decision']}'."
        )

    # ── Branch 3: -10 % ≤ growth_rate ≤ 15 % → Maintain ───────────── #

    @pytest.mark.parametrize("growth_rate", [0.0, 5.0, -5.0, 14.99, -9.99, 15.0, -10.0])
    def test_normal_growth_gives_maintain_decision(self, growth_rate):
        result = apply_rules(growth_rate, confidence=0.60)
        assert result["decision"] == DECISION_MAINTAIN, (
            f"growth_rate={growth_rate:.2f}% should give '{DECISION_MAINTAIN}', "
            f"got '{result['decision']}'."
        )

    # ── Return dict always has required keys ────────────────────────── #

    @pytest.mark.parametrize("growth_rate, confidence", [
        (20.0, 0.90),
        (-15.0, 0.55),
        (0.0, 0.70),
    ])
    def test_result_has_required_keys(self, growth_rate, confidence):
        result = apply_rules(growth_rate, confidence)
        for key in ("decision", "reason", "confidence"):
            assert key in result, (
                f"apply_rules() result missing key '{key}' for "
                f"growth_rate={growth_rate}."
            )

    # ── Confidence is passed through unchanged (rounded to 4dp) ─────── #

    @pytest.mark.parametrize("confidence", [0.0, 0.5, 0.999, 1.0])
    def test_confidence_passed_through(self, confidence):
        result = apply_rules(0.0, confidence)
        assert abs(result["confidence"] - round(confidence, 4)) < 1e-9, (
            f"confidence mismatch: expected {confidence}, got {result['confidence']}."
        )

    # ── Decision is always one of the three known labels ────────────── #

    @pytest.mark.parametrize("growth_rate", [-50.0, -10.01, -10.0, 0.0, 15.0, 15.01, 50.0])
    def test_decision_is_known_label(self, growth_rate):
        result = apply_rules(growth_rate, 0.70)
        assert result["decision"] in {DECISION_INCREASE, DECISION_REDUCE, DECISION_MAINTAIN}, (
            f"Unknown decision label '{result['decision']}' for growth_rate={growth_rate}."
        )


# ============================================================================ #
# 2. Boundary / threshold edge cases
# ============================================================================ #

class TestRulesEngineBoundary:
    """Exact boundary values — thresholds are strict (> and <, not >= and <=)."""

    def test_exactly_at_increase_threshold_gives_maintain(self):
        """growth_rate == 15.0 is NOT > 15.0 → Maintain."""
        result = apply_rules(15.0, 0.80)
        assert result["decision"] == DECISION_MAINTAIN

    def test_just_above_increase_threshold_gives_increase(self):
        result = apply_rules(15.001, 0.80)
        assert result["decision"] == DECISION_INCREASE

    def test_exactly_at_reduce_threshold_gives_maintain(self):
        """growth_rate == -10.0 is NOT < -10.0 → Maintain."""
        result = apply_rules(-10.0, 0.65)
        assert result["decision"] == DECISION_MAINTAIN

    def test_just_below_reduce_threshold_gives_reduce(self):
        result = apply_rules(-10.001, 0.65)
        assert result["decision"] == DECISION_REDUCE

    def test_custom_thresholds_respected(self):
        """Custom thresholds override the defaults."""
        result = apply_rules(
            growth_rate=5.0,
            confidence=0.70,
            increase_threshold=3.0,   # lower than default 15.0
            reduce_threshold=-5.0,    # higher than default -10.0
        )
        assert result["decision"] == DECISION_INCREASE, (
            "With increase_threshold=3.0, growth_rate=5.0 should → Increase."
        )

    def test_custom_reduce_threshold(self):
        result = apply_rules(
            growth_rate=-3.0,
            confidence=0.60,
            increase_threshold=15.0,
            reduce_threshold=-2.0,    # higher than default -10.0
        )
        assert result["decision"] == DECISION_REDUCE, (
            "With reduce_threshold=-2.0, growth_rate=-3.0 should → Reduce."
        )


# ============================================================================ #
# 3. Reason string content
# ============================================================================ #

class TestApplyRulesReasonStrings:
    """Reason strings must reference the growth_rate and confidence."""

    def test_increase_reason_mentions_growth_rate(self):
        result = apply_rules(20.0, 0.88)
        assert "+20.00%" in result["reason"] or "20.00%" in result["reason"], (
            "Increase reason should mention the growth_rate value."
        )

    def test_reduce_reason_mentions_growth_rate(self):
        result = apply_rules(-15.0, 0.55)
        assert "-15.00%" in result["reason"], (
            "Reduce reason should mention the negative growth_rate value."
        )

    def test_maintain_reason_mentions_range(self):
        result = apply_rules(3.0, 0.70)
        # Reason should reference the normal operating range
        assert "-10.0" in result["reason"] and "15.0" in result["reason"], (
            "Maintain reason should mention both threshold values."
        )

    def test_reason_is_non_empty_string(self):
        for gr in (20.0, -15.0, 0.0):
            result = apply_rules(gr, 0.70)
            assert isinstance(result["reason"], str) and len(result["reason"]) > 20, (
                f"reason for growth_rate={gr} should be a meaningful string."
            )

    def test_reason_mentions_confidence(self):
        """Each reason string should cite the model confidence."""
        for gr in (20.0, -15.0, 0.0):
            result = apply_rules(gr, 0.80)
            assert "80%" in result["reason"] or "0.80" in result["reason"], (
                f"reason for growth_rate={gr} should mention confidence=80%."
            )


# ============================================================================ #
# 4. Integration tests — GET /api/sales/recommendation (Flask test client)
# ============================================================================ #

class TestGetRecommendationEndpoint:
    """
    Hit the real Flask endpoint with generate_forecast() monkeypatched so
    tests are deterministic and fast regardless of model state.
    """

    def _get(self, flask_client, growth_rate: float, period: str = "30_days"):
        """
        Monkey-patch generate_forecast() to return a synthetic result,
        then call GET /api/sales/recommendation.
        """
        fake = _fake_forecast(growth_rate)
        with patch("app.ml.sales.recommendation.generate_forecast", return_value=fake):
            with patch("app.ml.sales.recommendation._store_recommendation", return_value=42):
                resp = flask_client.get(
                    f"/api/sales/recommendation?forecast_period={period}"
                )
        return resp

    # ── Status 200 for all valid periods ────────────────────────────── #

    @pytest.mark.parametrize("period", ["7_days", "30_days", "90_days"])
    def test_status_200_for_valid_periods(self, flask_client, period):
        resp = self._get(flask_client, growth_rate=0.0, period=period)
        assert resp.status_code == 200, (
            f"Expected 200 for period='{period}', got {resp.status_code}. "
            f"Body: {resp.get_data(as_text=True)}"
        )

    # ── Three decision branches via endpoint ────────────────────────── #

    def test_high_growth_returns_increase(self, flask_client):
        resp = self._get(flask_client, growth_rate=20.0)
        body = resp.get_json()
        assert body["decision"] == DECISION_INCREASE, (
            f"growth_rate=20% should give '{DECISION_INCREASE}', got '{body['decision']}'."
        )

    def test_low_growth_returns_reduce(self, flask_client):
        resp = self._get(flask_client, growth_rate=-15.0)
        body = resp.get_json()
        assert body["decision"] == DECISION_REDUCE, (
            f"growth_rate=-15% should give '{DECISION_REDUCE}', got '{body['decision']}'."
        )

    def test_normal_growth_returns_maintain(self, flask_client):
        resp = self._get(flask_client, growth_rate=5.0)
        body = resp.get_json()
        assert body["decision"] == DECISION_MAINTAIN, (
            f"growth_rate=5% should give '{DECISION_MAINTAIN}', got '{body['decision']}'."
        )

    # ── Response schema ──────────────────────────────────────────────── #

    def test_response_has_required_keys(self, flask_client):
        resp = self._get(flask_client, growth_rate=0.0)
        body = resp.get_json()
        for key in ("decision", "reason", "confidence"):
            assert key in body, f"Required key '{key}' missing from recommendation response."

    def test_reason_is_non_empty_string(self, flask_client):
        resp = self._get(flask_client, growth_rate=5.0)
        body = resp.get_json()
        assert isinstance(body["reason"], str) and len(body["reason"]) > 10

    def test_confidence_is_bounded(self, flask_client):
        resp = self._get(flask_client, growth_rate=5.0)
        body = resp.get_json()
        assert 0.0 <= body["confidence"] <= 1.0


# ============================================================================ #
# 5. Full response schema
# ============================================================================ #

class TestRecommendationSchema:
    """Verify all fields in the API response."""

    @pytest.fixture(scope="class")
    @classmethod
    def body(cls, flask_client):
        fake = _fake_forecast(5.0)
        with patch("app.ml.sales.recommendation.generate_forecast", return_value=fake):
            with patch("app.ml.sales.recommendation._store_recommendation", return_value=99):
                resp = flask_client.get("/api/sales/recommendation")
        return resp.get_json()

    @pytest.mark.parametrize("key", sorted(_REQUIRED_ENDPOINT_KEYS))
    def test_required_key_present(self, body, key):
        assert key in body, f"Key '{key}' missing from recommendation response."

    def test_status_is_success(self, body):
        assert body["status"] == "success"

    def test_decision_is_valid_label(self, body):
        assert body["decision"] in {DECISION_INCREASE, DECISION_REDUCE, DECISION_MAINTAIN}

    def test_confidence_float_in_range(self, body):
        c = body["confidence"]
        assert isinstance(c, float) and 0.0 <= c <= 1.0

    def test_growth_rate_is_float(self, body):
        import math
        gr = body["growth_rate"]
        assert isinstance(gr, (int, float)) and math.isfinite(gr)

    def test_predicted_sales_is_non_negative(self, body):
        assert body["predicted_sales"] >= 0

    def test_forecast_period_is_string(self, body):
        assert isinstance(body["forecast_period"], str)

    def test_model_type_is_non_empty_string(self, body):
        mt = body["model_type"]
        assert isinstance(mt, str) and len(mt) > 0

    def test_version_is_non_empty_string(self, body):
        v = body["version"]
        assert isinstance(v, str) and len(v) > 0


# ============================================================================ #
# 6. Input validation on the endpoint
# ============================================================================ #

class TestRecommendationValidation:
    """Bad query params → 400."""

    def test_invalid_period_returns_400(self, flask_client):
        resp = flask_client.get("/api/sales/recommendation?forecast_period=1_year")
        assert resp.status_code == 400

    def test_invalid_period_response_has_valid_values(self, flask_client):
        resp = flask_client.get("/api/sales/recommendation?forecast_period=bad")
        body = resp.get_json()
        assert "valid_values" in body
        assert set(body["valid_values"]) == {"7_days", "30_days", "90_days"}

    def test_missing_period_uses_default_30_days(self, flask_client):
        """No ?forecast_period → defaults to 30_days → 200."""
        fake = _fake_forecast(5.0)
        with patch("app.ml.sales.recommendation.generate_forecast", return_value=fake):
            with patch("app.ml.sales.recommendation._store_recommendation", return_value=1):
                resp = flask_client.get("/api/sales/recommendation")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["forecast_period"] == "30_days"


# ============================================================================ #
# 7. get_recommendation() stores to decision_history (side-effect)
# ============================================================================ #

class TestRecommendationStorage:
    """Verify that get_recommendation() calls _store_recommendation."""

    def test_store_called_on_get_recommendation(self):
        fake = _fake_forecast(5.0)
        with patch("app.ml.sales.recommendation.generate_forecast", return_value=fake) as m_fc:
            with patch(
                "app.ml.sales.recommendation._store_recommendation", return_value=77
            ) as m_store:
                result = get_recommendation(forecast_period="7_days")

        m_store.assert_called_once()
        assert result["stored_id"] == 77

    def test_store_receives_correct_decision(self):
        fake = _fake_forecast(20.0)   # → Increase Production
        with patch("app.ml.sales.recommendation.generate_forecast", return_value=fake):
            with patch(
                "app.ml.sales.recommendation._store_recommendation", return_value=1
            ) as m_store:
                get_recommendation(forecast_period="30_days")

        call_kwargs = m_store.call_args
        # First positional arg is decision
        stored_decision = call_kwargs.kwargs.get("decision") or call_kwargs.args[0]
        assert stored_decision == DECISION_INCREASE, (
            f"Expected '{DECISION_INCREASE}' stored, got '{stored_decision}'."
        )

    def test_store_failure_does_not_raise(self):
        """If DB write fails, get_recommendation() should still return normally."""
        fake = _fake_forecast(5.0)
        with patch("app.ml.sales.recommendation.generate_forecast", return_value=fake):
            with patch(
                "app.ml.sales.recommendation._store_recommendation",
                side_effect=Exception("DB error"),
            ):
                # This should not raise — _store_recommendation's exception is
                # caught internally and returns None.
                # We patch at module level so the exception propagates to
                # get_recommendation(); the wrapper in recommendation.py
                # should handle it gracefully.
                try:
                    result = get_recommendation(forecast_period="7_days")
                    # If it returns, stored_id should be None or an int
                    assert result["stored_id"] is None or isinstance(result["stored_id"], int)
                except Exception as exc:
                    pytest.fail(f"get_recommendation() should not raise on DB error: {exc}")


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
