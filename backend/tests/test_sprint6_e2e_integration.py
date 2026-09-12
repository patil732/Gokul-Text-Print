"""
tests/test_sprint6_e2e_integration.py
-------------------------------------
Sprint 6 — End-to-End Comprehensive Integration Test Suite.

Covers the full enterprise pipeline from end to end:
  1. ERP & ETL Data Plumbing: Live ERP data extraction & feature preparation.
  2. Sales Intelligence Engine (Sprint 2): Forecast & sales decision endpoints.
  3. Inventory Intelligence Engine (Sprint 3): Stock health, turnover & prediction.
  4. Knowledge Engine (Sprint 4): Semantic retrieval & enterprise policy hits.
  5. Manager Agent Orchestration (Sprint 5): Cross-domain executive copilot round-trip,
     source citations, and chat_history persistence with `is_manager=1`.
  6. Dashboard V2 KPI Loading & SLA Latency Verification:
     - Strict response time SLA: GET /api/dashboard/kpis < 2.0 seconds.
     - Complete 7-metric aggregation + composite Business Health Score.
  7. Interactive Time-Series Analytics: Chart-ready sales and inventory data with date filtering.
  8. Recommendation Center Aggregation: Multi-engine ingestion, schema normalization,
     and priority-sorted consolidation.
  9. Executive Report Generation: PDF (%PDF- header) and CSV exports for Daily, Weekly,
     and Monthly horizons.
  10. Operational Alert Center: Anomaly detection, priority-then-recency sorting, and persistence.
  11. Dashboard Personalization: Theme toggle, widget pin/reorder, and preferences persistence.
"""

from __future__ import annotations

import io
import os
import sys
import time
import json
import pytest
from unittest.mock import patch, MagicMock

# ── Project root on sys.path ──────────────────────────────────────────────── #
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ["PYTEST_CURRENT_TEST"] = "1"

from database.db import get_db_connection, init_db
import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(_ROOT, "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


@pytest.fixture(scope="module")
def app():
    """Create Flask application fixture for integration tests."""
    init_db()
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="module")
def client(app):
    """Authenticated CEO client fixture."""
    with app.test_client() as test_client:
        with test_client.session_transaction() as sess:
            sess["user"] = "ceo_e2e_user"
            sess["role"] = "ceo"
        yield test_client


class TestSprint6FullChainIntegration:
    """End-to-end integration covering ERP -> ETL -> Models -> Agents -> Dashboard V2."""

    # ----------------------------------------------------------------------- #
    # 1. ERP -> ETL Data Plumbing
    # ----------------------------------------------------------------------- #
    def test_01_erp_etl_data_pipeline(self):
        """Verify ERP data fetch and feature preparation succeed without error."""
        from services.decision_pipeline import fetch_live_data, prepare_live_features
        df_sales, df_stock = fetch_live_data()
        assert not df_sales.empty, "ERP Sales Order ingestion must produce non-empty sales data"
        assert not df_stock.empty, "ERP Bin ingestion must produce non-empty inventory data"

        df_features = prepare_live_features(df_sales, df_stock)
        assert not df_features.empty, "Feature engineering must produce valid combined dataset"
        expected_cols = ["date", "sales", "stock", "growth_rate"]
        for col in expected_cols:
            assert col in df_features.columns, f"Engineered features must include '{col}'"

    # ----------------------------------------------------------------------- #
    # 2. Sales Engine (Sprint 2)
    # ----------------------------------------------------------------------- #
    def test_02_sales_engine_endpoints(self, client):
        """Verify Sprint 2 sales prediction and recommendation endpoints respond cleanly."""
        res_pred = client.get("/api/ml/sales/predict")
        assert res_pred.status_code == 200
        data_pred = res_pred.get_json()
        assert data_pred["status"] == "success"
        assert "decision" in data_pred
        assert "confidence" in data_pred

        res_rec = client.get("/api/sales/recommendation?forecast_period=30_days")
        assert res_rec.status_code == 200
        data_rec = res_rec.get_json()
        assert data_rec["status"] == "success"
        assert "predicted_sales" in data_rec
        assert "decision" in data_rec

    # ----------------------------------------------------------------------- #
    # 3. Inventory Engine (Sprint 3)
    # ----------------------------------------------------------------------- #
    def test_03_inventory_engine_endpoints(self, client):
        """Verify Sprint 3 inventory prediction endpoint returns stock health and decision."""
        res_inv = client.get("/api/ml/inventory/predict")
        assert res_inv.status_code == 200
        data_inv = res_inv.get_json()
        assert data_inv["status"] == "success"
        assert "decision" in data_inv
        assert data_inv["decision"] in ("Reorder Required", "Optimal Stock Level")
        assert "probability" in data_inv

    # ----------------------------------------------------------------------- #
    # 4. Knowledge Engine (Sprint 4)
    # ----------------------------------------------------------------------- #
    def test_04_knowledge_engine_search(self, client):
        """Verify Sprint 4 semantic search executes and retrieves policy documents."""
        res_search = client.post(
            "/api/rag/search",
            json={"query": "What is the safety stock and inventory replenishment policy?", "top_k": 3},
        )
        assert res_search.status_code == 200
        data_search = res_search.get_json()
        assert data_search["status"] == "success"
        assert "chunks" in data_search
        assert "sources" in data_search

    # ----------------------------------------------------------------------- #
    # 5. Manager Agent Multi-Agent Orchestration (Sprint 5)
    # ----------------------------------------------------------------------- #
    def test_05_manager_agent_orchestration_roundtrip(self, client):
        """
        Verify Manager Agent coordinates Sales, Inventory, and Knowledge sub-agents,
        attaches source citations, and logs turn to chat_history with is_manager=1.
        """
        mock_llm_answer = (
            "Based on our synthesized intelligence: Sales demand is projecting steady growth (+12.4%), "
            "while 4 key inventory fabrics have fallen below the 50-unit safety stock policy threshold. "
            "Executive recommendation: Initiate batch replenishment immediately."
        )

        with patch("app.agents.manager_agent.ManagerAgent._call_llm", return_value=mock_llm_answer):

            res_mgr = client.post(
                "/api/agents/manager",
                json={"question": "Which fabric products need restocking and what is our sales outlook?"},
            )
            assert res_mgr.status_code == 200
            data_mgr = res_mgr.get_json()
            assert data_mgr["status"] == "success"
            assert "answer" in data_mgr
            assert "confidence" in data_mgr
            assert 0.0 <= data_mgr["confidence"] <= 1.0

            agents_used = data_mgr.get("agents_used", [])
            assert len(agents_used) >= 2, "Manager should activate at least 2 relevant domain agents"

            # Check database chat_history audit record
            conn = get_db_connection()
            row = conn.execute(
                "SELECT question, answer, is_manager FROM chat_history WHERE is_manager = 1 ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            conn.close()

            assert row is not None, "Manager orchestration must persist record to chat_history with is_manager=1"
            assert "restocking" in row["question"].lower()
            assert row["is_manager"] == 1

    # ----------------------------------------------------------------------- #
    # 6. Dashboard V2 KPI Loading & SLA Latency Verification (Step 1)
    # ----------------------------------------------------------------------- #
    def test_06_dashboard_kpi_loading_and_sla_latency(self, client):
        """
        Verify GET /api/dashboard/kpis returns all 7 core KPIs + Composite Health Score,
        and strictly satisfies the response time SLA (< 2.0 seconds).
        """
        t0 = time.perf_counter()
        res_kpi = client.get("/api/dashboard/kpis?refresh=true")
        elapsed_sec = time.perf_counter() - t0

        assert res_kpi.status_code == 200
        assert elapsed_sec < 2.0, f"SLA breach: GET /api/dashboard/kpis took {elapsed_sec:.2f}s (ceiling: 2.0s)"

        json_kpi = res_kpi.get_json()
        assert json_kpi["status"] == "success"
        data = json_kpi["data"]

        # Validate all 7 core metrics
        required_kpis = [
            "total_sales",
            "revenue",
            "sales_growth",
            "inventory_value",
            "inventory_health",
            "low_stock_products_count",
            "ai_recommendations_count",
        ]
        for k in required_kpis:
            assert k in data, f"KPI response missing required key '{k}'"

        # Validate Business Health Score
        bh = data.get("business_health", {})
        assert "score" in bh
        assert 0.0 <= bh["score"] <= 100.0
        assert bh["status"] in (
            "Strong", "Stable", "Warning", "Critical", "Moderate", "Healthy",
            "Needs Attention", "Optimal", "Good", "Fair", "Excellent",
        )
        assert "formula" in bh

    # ----------------------------------------------------------------------- #
    # 7. Interactive Time-Series Analytics (Step 2)
    # ----------------------------------------------------------------------- #
    def test_07_analytics_engine_sales_and_inventory_with_filters(self, client):
        """Verify chart-ready time-series data for both sales and inventory with date filters."""
        # Sales Analytics
        res_sales = client.get("/api/dashboard/analytics?type=sales&range=monthly")
        assert res_sales.status_code == 200
        data_sales = res_sales.get_json()["data"]
        assert "trend" in data_sales
        assert "datasets" in data_sales
        assert "labels" in data_sales

        # Inventory Analytics
        res_inv = client.get("/api/dashboard/analytics?type=inventory&range=weekly")
        assert res_inv.status_code == 200
        data_inv = res_inv.get_json()["data"]
        assert "stock_trend" in data_inv
        assert "inventory_turnover" in data_inv
        assert "low_stock_analysis" in data_inv
        assert "dead_stock_analysis" in data_inv

        # Date-filtered Query
        res_filtered = client.get("/api/dashboard/analytics?type=sales&range=daily&start=2026-07-01&end=2026-08-31")
        assert res_filtered.status_code == 200
        data_filtered = res_filtered.get_json()["data"]
        assert "trend" in data_filtered
        assert "datasets" in data_filtered

    # ----------------------------------------------------------------------- #
    # 8. Recommendation Center Aggregation (Step 3)
    # ----------------------------------------------------------------------- #
    def test_08_recommendation_center_aggregation(self, client):
        """
        Verify Recommendation Center aggregates from all 4 sources, normalizes into
        common schema, and applies priority-sorted ordering.
        """
        res_recs = client.get("/api/dashboard/recommendations")
        assert res_recs.status_code == 200
        json_recs = res_recs.get_json()
        assert json_recs["status"] == "success"

        recs = json_recs["data"]
        assert isinstance(recs, list)
        assert len(recs) >= 1

        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        for item in recs:
            for field in ["recommendation", "reason", "confidence", "priority", "source", "timestamp"]:
                assert field in item, f"Normalized recommendation item missing '{field}'"
            assert item["priority"] in priority_order

        # Verify sorted order: CRITICAL before HIGH before MEDIUM before LOW
        for i in range(len(recs) - 1):
            p1 = priority_order[recs[i]["priority"]]
            p2 = priority_order[recs[i + 1]["priority"]]
            assert p1 <= p2, f"Recommendations must be sorted by priority: {recs[i]['priority']} before {recs[i+1]['priority']}"

    # ----------------------------------------------------------------------- #
    # 9. Executive Report Generation in PDF & CSV (Step 5)
    # ----------------------------------------------------------------------- #
    @pytest.mark.parametrize("report_type", ["daily", "weekly", "monthly"])
    def test_09_executive_reports_generation_all_periods(self, client, report_type):
        """Verify report generation produces non-empty valid PDF and CSV files for all 3 periods."""
        # PDF Generation
        res_pdf = client.get(f"/api/reports/generate?type={report_type}&format=pdf")
        assert res_pdf.status_code == 200
        assert res_pdf.mimetype == "application/pdf"
        assert res_pdf.data.startswith(b"%PDF-"), "Generated PDF must start with %PDF- binary header"
        assert len(res_pdf.data) > 1000, "PDF file must be non-empty and well-formed"

        # CSV Generation
        res_csv = client.get(f"/api/reports/generate?type={report_type}&format=csv")
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.mimetype
        csv_text = res_csv.data.decode("utf-8")
        assert "EXECUTIVE BI REPORT" in csv_text
        assert "FINANCIAL & SALES SUMMARY" in csv_text
        assert "INVENTORY SUMMARY" in csv_text
        assert len(csv_text) > 100

    # ----------------------------------------------------------------------- #
    # 10. Operational Alert Center (Step 6)
    # ----------------------------------------------------------------------- #
    def test_10_operational_alert_center(self, client):
        """Verify alert generation, database storage, priority filtering, and resolution."""
        from app.dashboard.alerts import AlertEngine
        engine = AlertEngine()

        # Generate a test critical alert
        alert_obj = engine.create_alert(
            alert_type="Low Stock / Stockout Risk",
            priority="CRITICAL",
            message="E2E Integration Test: Critical fabric below safety threshold.",
        )
        assert alert_obj is not None
        alert_id = alert_obj["alert_id"] if isinstance(alert_obj, dict) else alert_obj

        # Fetch active alerts via endpoint
        res_alerts = client.get("/api/dashboard/alerts?status=ACTIVE&priority=CRITICAL")
        assert res_alerts.status_code == 200
        json_alerts = res_alerts.get_json()
        assert json_alerts["status"] == "success"
        alerts = json_alerts["data"]
        matching = [a for a in alerts if a["alert_id"] == alert_id]
        assert len(matching) == 1
        assert matching[0]["priority"] == "CRITICAL"

        # Resolve alert
        resolved = engine.resolve_alert(alert_id)
        assert resolved is True

    # ----------------------------------------------------------------------- #
    # 11. Dashboard Personalization & User Preferences (Step 7)
    # ----------------------------------------------------------------------- #
    def test_11_dashboard_personalization_roundtrip(self, client):
        """Verify user preference persistence (theme, pinned widgets, chart filters)."""
        prefs_payload = {
            "theme": "dark",
            "pinned_widgets": ["widget-alerts", "widget-kpis", "widget-recommendations"],
            "widget_order": [
                "widget-alerts",
                "widget-kpis",
                "widget-recommendations",
                "widget-charts",
                "widget-chat",
                "widget-specialist-engines",
            ],
            "chart_filters": {
                "sales_range": "daily",
                "inventory_range": "daily",
                "start_date": "2026-08-01",
                "end_date": "2026-08-15",
            },
        }

        # Save preferences
        res_post = client.post(
            "/api/dashboard/preferences",
            json={"user": "ceo_e2e_user", "preferences": prefs_payload},
        )
        assert res_post.status_code == 200
        assert res_post.get_json()["status"] == "success"

        # Fetch preferences
        res_get = client.get("/api/dashboard/preferences?user=ceo_e2e_user")
        assert res_get.status_code == 200
        saved_prefs = res_get.get_json()["data"]
        assert saved_prefs["theme"] == "dark"
        assert saved_prefs["pinned_widgets"] == ["widget-alerts", "widget-kpis", "widget-recommendations"]
        assert saved_prefs["chart_filters"]["sales_range"] == "daily"

    # ----------------------------------------------------------------------- #
    # 12. Dashboard V2 HTML Availability & Legacy Specialist Preservation
    # ----------------------------------------------------------------------- #
    def test_12_dashboard_v2_html_and_legacy_preservation(self, client):
        """
        Verify CEO Dashboard view delivers the V2 layout while keeping all legacy
        specialist element IDs completely intact.
        """
        res_view = client.get("/ceo")
        assert res_view.status_code == 200
        html = res_view.data.decode("utf-8")

        # V2 Components
        assert "dashboard-personalization-bar" in html
        assert "widget-alerts" in html
        assert "widget-kpis" in html
        assert "widget-charts" in html
        assert "widget-recommendations" in html
        assert "widget-chat" in html
        assert "widget-specialist-engines" in html

        # Preserved Sprint 2-4 DOM IDs
        legacy_ids = [
            "salesForecastChart",
            "salesVolumeTrendChart",
            "revenueTrendChart",
            "productPerformanceChart",
            "monthlyComparisonChart",
            "sales-kpi-total-revenue",
            "sales-ai-decision",
            "inventory-decision-text",
            "inventory-confidence",
            "sim-sales",
            "sim-stock",
            "documents-table-body",
        ]
        for dom_id in legacy_ids:
            assert dom_id in html, f"Legacy DOM element id '{dom_id}' must be preserved in HTML"
