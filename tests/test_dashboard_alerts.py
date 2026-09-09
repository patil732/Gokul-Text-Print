"""
tests/test_dashboard_alerts.py
------------------------------
Unit & Integration Tests for Threshold-Based Operational Alert Engine (Sprint 6).

Covers:
  1. Triggering each of the 6 alert types with mock data and confirming correct priority assignment:
     - Sales Drop (CRITICAL / HIGH) & Sales Spike (MEDIUM)
     - Low Stock (CRITICAL / HIGH) & Overstock (MEDIUM)
     - ETL Failure (CRITICAL)
     - Model Failure (HIGH / CRITICAL)
     - AI Confidence Drop (MEDIUM / HIGH)
     - Missing Data (CRITICAL / HIGH)
  2. Database persistence in alerts table (UUID PK, alert_type, priority, message, status, timestamp).
  3. Correct priority-then-recency sort ordering (CRITICAL > HIGH > MEDIUM > LOW, then created_at DESC).
  4. REST endpoint GET /api/dashboard/alerts (HTTP 200, schema adherence, priority & limit query filters, 400 validation).
  5. Integration with Step 5 reports: verify generated reports include active alerts from AlertEngine.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.dashboard.alerts import AlertEngine
from database.db import get_db_connection

# Load Flask app factory from app.py
_SPEC = importlib.util.spec_from_file_location("app_entry", os.path.join(_ROOT, "app.py"))
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


@pytest.fixture
def engine():
    eng = AlertEngine()
    eng.clear_alerts()
    yield eng
    eng.clear_alerts()


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ============================================================================ #
# 1. Alert Type Triggering & Priority Assignment Tests
# ============================================================================ #

class TestAlertTriggersAndPriorities:

    def test_trigger_sales_drop_and_spike(self, engine):
        # 1. Severe drop <= -25% -> CRITICAL
        crit_drop = engine.check_sales_anomaly(-28.5)
        assert crit_drop is not None
        assert crit_drop["alert_type"] == "SALES_DROP"
        assert crit_drop["priority"] == "CRITICAL"
        assert "-28.5%" in crit_drop["message"]

        # 2. Notable drop <= -15% -> HIGH
        high_drop = engine.check_sales_anomaly(-18.0)
        assert high_drop is not None
        assert high_drop["alert_type"] == "SALES_DROP"
        assert high_drop["priority"] == "HIGH"
        assert "-18.0%" in high_drop["message"]

        # 3. Notable spike >= +25% -> MEDIUM
        spike = engine.check_sales_anomaly(32.0)
        assert spike is not None
        assert spike["alert_type"] == "SALES_SPIKE"
        assert spike["priority"] == "MEDIUM"
        assert "+32.0%" in spike["message"]

        # 4. Normal range (-5%) -> None
        normal = engine.check_sales_anomaly(5.0)
        assert normal is None

    def test_trigger_low_stock_and_overstock(self, engine):
        # 1. Critical low stock (>= 10 products or health == "Critical") -> CRITICAL
        crit_inv = engine.check_inventory_levels(low_stock_count=12, stock_health="Critical")
        assert len(crit_inv) >= 1
        assert crit_inv[0]["alert_type"] == "LOW_STOCK"
        assert crit_inv[0]["priority"] == "CRITICAL"

        # 2. Warning low stock (1-9 products) -> HIGH
        warn_inv = engine.check_inventory_levels(low_stock_count=4, stock_health="Warning")
        assert len(warn_inv) >= 1
        assert warn_inv[0]["alert_type"] == "LOW_STOCK"
        assert warn_inv[0]["priority"] == "HIGH"

        # 3. Overstock / dead stock items -> MEDIUM
        over_inv = engine.check_inventory_levels(low_stock_count=0, overstock_count=6)
        assert len(over_inv) == 1
        assert over_inv[0]["alert_type"] == "OVERSTOCK"
        assert over_inv[0]["priority"] == "MEDIUM"

    def test_trigger_etl_failure(self, engine):
        # 1. ETL failure -> CRITICAL
        fail_etl = engine.check_etl_status(etl_success=False, error_msg="Database connection timeout to ERP Bin doctype")
        assert fail_etl is not None
        assert fail_etl["alert_type"] == "ETL_FAILURE"
        assert fail_etl["priority"] == "CRITICAL"
        assert "Database connection timeout" in fail_etl["message"]

        # 2. ETL success -> None
        ok_etl = engine.check_etl_status(etl_success=True)
        assert ok_etl is None

    def test_trigger_model_failure(self, engine):
        # 1. Model runtime exception -> HIGH
        fail_model = engine.check_model_health(model_error="Matrix dimensions mismatch during inference", model_name="XGBoost Sales")
        assert fail_model is not None
        assert fail_model["alert_type"] == "MODEL_FAILURE"
        assert fail_model["priority"] == "HIGH"
        assert "XGBoost Sales" in fail_model["message"]

        # 2. Degraded accuracy below 50% -> HIGH
        degraded = engine.check_model_health(accuracy=0.42, model_name="Inventory Classifier")
        assert degraded is not None
        assert degraded["alert_type"] == "MODEL_FAILURE"
        assert degraded["priority"] == "HIGH"
        assert "42.0%" in degraded["message"]

    def test_trigger_ai_confidence_drop(self, engine):
        # 1. Severe drop < 40% -> HIGH
        sev_conf = engine.check_ai_confidence(confidence=0.34, source="sales recommendation")
        assert sev_conf is not None
        assert sev_conf["alert_type"] == "AI_CONFIDENCE_DROP"
        assert sev_conf["priority"] == "HIGH"
        assert "34.0%" in sev_conf["message"]

        # 2. Moderate drop < 60% -> MEDIUM
        mod_conf = engine.check_ai_confidence(confidence=0.52, source="inventory recommendation")
        assert mod_conf is not None
        assert mod_conf["alert_type"] == "AI_CONFIDENCE_DROP"
        assert mod_conf["priority"] == "MEDIUM"
        assert "52.0%" in mod_conf["message"]

        # 3. Healthy confidence >= 60% -> None
        good_conf = engine.check_ai_confidence(confidence=0.85)
        assert good_conf is None

    def test_trigger_missing_data(self, engine):
        # 1. Zero rows ingested -> CRITICAL
        zero_data = engine.check_missing_data(current_row_count=0)
        assert zero_data is not None
        assert zero_data["alert_type"] == "MISSING_DATA"
        assert zero_data["priority"] == "CRITICAL"

        # 2. Missing columns -> CRITICAL
        missing_cols = engine.check_missing_data(current_row_count=500, missing_columns=["reorder_level", "total_stock"])
        assert missing_cols is not None
        assert missing_cols["alert_type"] == "MISSING_DATA"
        assert missing_cols["priority"] == "CRITICAL"
        assert "reorder_level" in missing_cols["message"]

        # 3. Row count below threshold (e.g. 40 < 100) -> HIGH
        low_data = engine.check_missing_data(current_row_count=40, expected_min_rows=100)
        assert low_data is not None
        assert low_data["alert_type"] == "MISSING_DATA"
        assert low_data["priority"] == "HIGH"
        assert "40 rows" in low_data["message"]


# ============================================================================ #
# 2. Persistence and Priority Sorting Order Tests
# ============================================================================ #

class TestAlertPersistenceAndSorting:

    def test_create_and_query_alerts_schema(self, engine):
        alert = engine.create_alert(
            alert_type="LOW_STOCK",
            priority="CRITICAL",
            message="Immediate stock replenishment required for fabric dyes.",
        )

        assert "alert_id" in alert
        assert alert["priority"] == "CRITICAL"
        assert alert["status"] == "ACTIVE"
        assert alert["alert_type"] == "LOW_STOCK"

        # Verify in database
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert["alert_id"],)).fetchone()
            assert row is not None
            assert row["alert_id"] == alert["alert_id"]
            assert row["alert_type"] == "LOW_STOCK"
            assert row["priority"] == "CRITICAL"
            assert row["status"] == "ACTIVE"

    def test_priority_sorting_order(self, engine):
        """
        Insert alerts across all 4 priorities and confirm order:
        CRITICAL > HIGH > MEDIUM > LOW.
        """
        engine.create_alert("OVERSTOCK", "MEDIUM", "Stagnant inventory item")
        engine.create_alert("ETL_FAILURE", "CRITICAL", "Ingestion crashed")
        engine.create_alert("SALES_SPIKE", "LOW", "Minor sales bump")
        engine.create_alert("MODEL_FAILURE", "HIGH", "Model degraded")

        active = engine.get_active_alerts()
        assert len(active) == 4

        priorities = [a["priority"] for a in active]
        assert priorities == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def test_resolve_alert(self, engine):
        alert = engine.create_alert("LOW_STOCK", "HIGH", "Stock low")
        assert len(engine.get_active_alerts()) == 1

        resolved = engine.resolve_alert(alert["alert_id"])
        assert resolved is True
        assert len(engine.get_active_alerts()) == 0


# ============================================================================ #
# 3. REST API Endpoint Tests (GET /api/dashboard/alerts)
# ============================================================================ #

class TestAlertEndpoint:

    def test_endpoint_returns_status_200(self, client, engine):
        engine.create_alert("ETL_FAILURE", "CRITICAL", "ETL failed during scheduled sync")
        engine.create_alert("SALES_DROP", "HIGH", "Sales declined by 18%")

        resp = client.get("/api/dashboard/alerts")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert "count" in body
        assert "data" in body
        assert "elapsed_ms" in body
        assert len(body["data"]) >= 2
        assert body["data"][0]["priority"] == "CRITICAL"
        assert body["data"][1]["priority"] == "HIGH"

    def test_endpoint_priority_filter(self, client, engine):
        engine.create_alert("LOW_STOCK", "CRITICAL", "Critical stockout")
        engine.create_alert("OVERSTOCK", "MEDIUM", "Medium dead stock")

        resp = client.get("/api/dashboard/alerts?priority=CRITICAL")
        assert resp.status_code == 200
        body = resp.get_json()
        assert all(a["priority"] == "CRITICAL" for a in body["data"])

    def test_endpoint_limit_parameter(self, client, engine):
        for i in range(5):
            engine.create_alert("AI_CONFIDENCE_DROP", "MEDIUM", f"Drop {i}")

        resp = client.get("/api/dashboard/alerts?limit=2")
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body["data"]) == 2
        assert body["count"] == 2

    def test_endpoint_invalid_priority_returns_400(self, client):
        resp = client.get("/api/dashboard/alerts?priority=EMERGENCY")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["status"] == "error"
        assert "Invalid priority" in body["message"]

    def test_endpoint_invalid_limit_returns_400(self, client):
        resp = client.get("/api/dashboard/alerts?limit=xyz")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["status"] == "error"
        assert "Invalid limit" in body["message"]


# ============================================================================ #
# 4. Reports Integration Tests
# ============================================================================ #

class TestReportsAlertWiring:

    def test_reports_include_active_alerts_from_engine(self, engine):
        """
        Verify that Step 5 reports pull live alerts created by AlertEngine.
        """
        from app.dashboard.reports import build_daily_report, export_csv

        # Create live alerts in database
        engine.create_alert("LOW_STOCK", "CRITICAL", "Live database alert: Fabric stockout breach")

        daily = build_daily_report()
        assert len(daily.alerts) > 0
        alert_msgs = [a.get("message", "") for a in daily.alerts]
        assert any("Fabric stockout breach" in m for m in alert_msgs)

        # Confirm alerts are present in exported CSV
        csv_text = export_csv(daily)
        assert "OPERATIONAL ALERTS" in csv_text
        assert "Fabric stockout breach" in csv_text
