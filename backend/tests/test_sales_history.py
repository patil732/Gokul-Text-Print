"""
tests/test_sales_history.py
----------------------------
Sprint 2 — Sales Prediction History Table & Endpoint Unit/Integration Tests

Coverage
--------
1. Migration & DB Schema: sales_prediction_history table created with correct columns.
2. Helper Function: log_sales_prediction_history() inserts valid records.
3. Forecast & Recommendation Integration: generate_forecast() and get_recommendation() write to sales_prediction_history.
4. API Endpoint: GET /api/sales/history returns paginated results ordered by prediction_date DESC.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import uuid

import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.common.prediction_service import log_sales_prediction_history
from app.ml.sales.forecast import generate_forecast, _get_engine
from app.ml.sales.recommendation import get_recommendation
from database.db import get_db_connection, init_db

# ── Load Flask app factory ───────────────────────────────────────────────── #
_SPEC    = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module", autouse=True)
def ensure_db_schema():
    """Ensure database schema and sales_prediction_history table exist."""
    init_db()
    _engine = _get_engine()
    _engine.load()


@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================================ #
# 1. DB Schema & Migration Tests
# ============================================================================ #

class TestSalesHistoryDBSchema:
    """Verify sales_prediction_history table structure in SQLite."""

    def test_sales_prediction_history_table_exists(self):
        conn = get_db_connection()
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sales_prediction_history'"
        ).fetchone()
        conn.close()
        assert row is not None, "Table 'sales_prediction_history' must exist in DB."

    def test_sales_prediction_history_column_names(self):
        conn = get_db_connection()
        cursor = conn.execute("PRAGMA table_info(sales_prediction_history)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()

        expected_columns = [
            "prediction_id",
            "prediction_date",
            "forecast_period",
            "forecast_value",
            "recommendation",
            "confidence",
            "model_version",
        ]
        for col in expected_columns:
            assert col in columns, f"Column '{col}' missing from sales_prediction_history."


# ============================================================================ #
# 2. Logging Helper Function Tests
# ============================================================================ #

class TestLogSalesPredictionHistory:
    """Unit tests for log_sales_prediction_history()."""

    def test_log_sales_prediction_history_creates_record(self):
        test_id = str(uuid.uuid4())
        returned_id = log_sales_prediction_history(
            forecast_period="30_days",
            forecast_value=500000.0,
            recommendation="Increase Production",
            confidence=0.85,
            model_version="v_test_1",
            prediction_id=test_id,
        )

        assert returned_id == test_id

        conn = get_db_connection()
        row = conn.execute(
            "SELECT * FROM sales_prediction_history WHERE prediction_id = ?",
            (test_id,),
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["forecast_period"] == "30_days"
        assert row["forecast_value"] == 500000.0
        assert row["recommendation"] == "Increase Production"
        assert row["confidence"] == 0.85
        assert row["model_version"] == "v_test_1"


# ============================================================================ #
# 3. Forecast & Recommendation Integration Tests
# ============================================================================ #

class TestSalesHistoryPipelineIntegration:
    """Ensure generate_forecast() and get_recommendation() write to history."""

    def test_generate_forecast_writes_to_history(self):
        res = generate_forecast("7_days")
        assert "predicted_sales" in res

        conn = get_db_connection()
        row = conn.execute(
            "SELECT * FROM sales_prediction_history WHERE forecast_period = '7_days' ORDER BY prediction_date DESC LIMIT 1"
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["forecast_period"] == "7_days"
        assert row["forecast_value"] == res["predicted_sales"]

    def test_get_recommendation_writes_recommendation_to_history(self):
        res = get_recommendation("30_days")
        assert "decision" in res

        conn = get_db_connection()
        row = conn.execute(
            "SELECT * FROM sales_prediction_history WHERE recommendation = ? ORDER BY prediction_date DESC LIMIT 1",
            (res["decision"],),
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["recommendation"] == res["decision"]
        assert row["forecast_value"] == res["predicted_sales"]


# ============================================================================ #
# 4. API Endpoint Tests: GET /api/sales/history
# ============================================================================ #

class TestSalesHistoryAPIEndpoint:
    """Test GET /api/sales/history endpoint."""

    def test_get_sales_history_status_200(self, flask_client):
        resp = flask_client.get("/api/sales/history")
        assert resp.status_code == 200

    def test_get_sales_history_response_schema(self, flask_client):
        resp = flask_client.get("/api/sales/history")
        body = resp.get_json()

        assert body["status"] == "success"
        assert "page" in body
        assert "per_page" in body
        assert "total_records" in body
        assert "total_pages" in body
        assert "data" in body
        assert isinstance(body["data"], list)

    def test_get_sales_history_record_fields(self, flask_client):
        resp = flask_client.get("/api/sales/history")
        data = resp.get_json()["data"]

        assert len(data) > 0, "History data should contain entries after forecast run."
        record = data[0]

        expected_keys = [
            "prediction_id",
            "prediction_date",
            "forecast_period",
            "forecast_value",
            "recommendation",
            "confidence",
            "model_version",
        ]
        for key in expected_keys:
            assert key in record, f"Key '{key}' missing from sales history record."

    def test_get_sales_history_ordered_descending_by_date(self, flask_client):
        resp = flask_client.get("/api/sales/history?limit=20")
        data = resp.get_json()["data"]

        if len(data) > 1:
            dates = [rec["prediction_date"] for rec in data]
            assert dates == sorted(dates, reverse=True), "History entries must be ordered by prediction_date DESC."

    def test_get_sales_history_pagination(self, flask_client):
        resp_p1 = flask_client.get("/api/sales/history?page=1&limit=2")
        resp_p2 = flask_client.get("/api/sales/history?page=2&limit=2")

        body1 = resp_p1.get_json()
        body2 = resp_p2.get_json()

        assert body1["page"] == 1
        assert body1["per_page"] == 2
        assert body2["page"] == 2
        assert body2["per_page"] == 2

        if body1["total_records"] >= 4:
            assert body1["data"] != body2["data"], "Page 1 and Page 2 must return different records."


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
