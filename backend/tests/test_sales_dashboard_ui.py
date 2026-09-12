"""
tests/test_sales_dashboard_ui.py
---------------------------------
Sprint 2 — Sales Intelligence Dashboard Panel UI & API Tests

Coverage
--------
1. GET /api/sales/dashboard_data returns 200 with KPI & chart series payload.
2. GET /ceo renders the executive dashboard HTML template with all required
   Sales Intelligence KPI cards, AI Panel elements, and Chart canvas elements.
3. Dynamic forecast horizon selector triggers forecast & recommendation API calls.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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

@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Authenticate as CEO
        with client.session_transaction() as sess:
            sess["user"] = "ceo_test_user"
            sess["role"] = "ceo"
        yield client


# ============================================================================ #
# 1. GET /api/sales/dashboard_data Tests
# ============================================================================ #

class TestSalesDashboardDataAPI:
    """Test dashboard data endpoint powering the Sales Intelligence charts."""

    def test_dashboard_data_endpoint_status_200(self, flask_client):
        resp = flask_client.get("/api/sales/dashboard_data")
        assert resp.status_code == 200

    def test_dashboard_data_schema(self, flask_client):
        resp = flask_client.get("/api/sales/dashboard_data")
        body = resp.get_json()

        assert body["status"] == "success"
        assert "kpis" in body
        assert "sales_trend" in body
        assert "revenue_trend" in body
        assert "product_performance" in body
        assert "monthly_comparison" in body

    def test_kpis_payload(self, flask_client):
        resp = flask_client.get("/api/sales/dashboard_data")
        kpis = resp.get_json()["kpis"]

        assert "total_revenue" in kpis
        assert "growth_rate" in kpis
        assert isinstance(kpis["total_revenue"], (int, float))
        assert kpis["total_revenue"] > 0

    def test_chart_series_non_empty(self, flask_client):
        resp = flask_client.get("/api/sales/dashboard_data")
        body = resp.get_json()

        assert len(body["sales_trend"]["dates"]) > 0
        assert len(body["revenue_trend"]["revenue"]) > 0
        assert len(body["product_performance"]["products"]) > 0
        assert len(body["monthly_comparison"]["months"]) > 0


# ============================================================================ #
# 2. Executive Dashboard Template Element Verification
# ============================================================================ #

class TestCEODashboardTemplate:
    """Verify Sales Intelligence Panel elements in ceo_dashboard.html."""

    @pytest.fixture(scope="class")
    @classmethod
    def page_html(cls, flask_client):
        resp = flask_client.get("/ceo")
        assert resp.status_code == 200
        return resp.get_data(as_text=True)

    def test_sales_intelligence_header_present(self, page_html):
        assert "Sales Intelligence Engine" in page_html

    @pytest.mark.parametrize("kpi_id", [
        "sales-kpi-total-revenue",
        "sales-kpi-growth-rate",
        "sales-kpi-forecast",
        "sales-kpi-recommendation",
    ])
    def test_sales_kpi_card_element_present(self, page_html, kpi_id):
        assert f'id="{kpi_id}"' in page_html

    @pytest.mark.parametrize("ai_element_id", [
        "sales-ai-decision",
        "sales-ai-confidence-badge",
        "sales-ai-model-type",
        "sales-ai-version",
        "sales-ai-reason",
        "sales-shap-features-list",
    ])
    def test_sales_ai_panel_element_present(self, page_html, ai_element_id):
        assert f'id="{ai_element_id}"' in page_html

    @pytest.mark.parametrize("chart_id", [
        "salesForecastChart",
        "salesVolumeTrendChart",
        "revenueTrendChart",
        "productPerformanceChart",
        "monthlyComparisonChart",
    ])
    def test_sales_chart_canvas_present(self, page_html, chart_id):
        assert f'id="{chart_id}"' in page_html

    def test_horizon_selector_buttons_present(self, page_html):
        assert "setForecastPeriod('7_days')" in page_html
        assert "setForecastPeriod('30_days')" in page_html
        assert "setForecastPeriod('90_days')" in page_html

    def test_shap_explanation_plots_embedded(self, page_html):
        assert "/static/sales_explanations/shap_summary.png" in page_html
        assert "/static/sales_explanations/feature_importance.png" in page_html


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
