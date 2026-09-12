"""
tests/test_dashboard_v2.py
--------------------------
Comprehensive unit and integration tests for Sprint 6 Executive Dashboard V2:
  - Database schema for `dashboard_preferences`
  - GET /api/dashboard/preferences (defaults & user-specific retrieval)
  - POST /api/dashboard/preferences (persisting theme, pin order, filters)
  - Partial update / merge behavior
  - Dashboard V2 layout rendering & legacy panel ID preservation
"""

import os
import sys
import json
import sqlite3
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ["PYTEST_CURRENT_TEST"] = "1"


@pytest.fixture(scope="module")
def app():
    """Create Flask test client without background scheduler."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_entry", os.path.join(_ROOT, "app.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    test_app = m.create_app()
    test_app.config["TESTING"] = True
    return test_app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


class TestDashboardPreferences:
    """Test preferences storage, retrieval, and defaults."""

    def test_preferences_table_exists(self):
        from database.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dashboard_preferences'")
        row = cursor.fetchone()
        conn.close()
        assert row is not None, "dashboard_preferences table must exist in SQLite schema"

    def test_get_preferences_returns_default_for_new_user(self, client):
        res = client.get("/api/dashboard/preferences?user=brand_new_executive_user")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert data["user"] == "brand_new_executive_user"
        prefs = data["data"]
        assert prefs["theme"] in ("light", "dark")
        assert "widget-alerts" in prefs["pinned_widgets"] or "widget-kpis" in prefs["pinned_widgets"]
        assert "widget_order" in prefs
        assert "chart_filters" in prefs
        assert data.get("is_default") is True

    def test_post_preferences_saves_and_retrieves(self, client):
        custom_prefs = {
            "theme": "dark",
            "pinned_widgets": ["widget-kpis", "widget-recommendations"],
            "widget_order": [
                "widget-kpis",
                "widget-recommendations",
                "widget-alerts",
                "widget-charts",
                "widget-chat",
                "widget-specialist-engines",
            ],
            "chart_filters": {
                "sales_range": "weekly",
                "inventory_range": "weekly",
                "start_date": "2026-08-01",
                "end_date": "2026-08-31",
            },
        }

        # Save preferences
        post_res = client.post(
            "/api/dashboard/preferences",
            json={"user": "ceo_v2_test", "preferences": custom_prefs},
        )
        assert post_res.status_code == 200
        post_data = post_res.get_json()
        assert post_data["status"] == "success"
        assert post_data["data"]["theme"] == "dark"
        assert post_data["data"]["chart_filters"]["sales_range"] == "weekly"

        # Fetch back saved preferences
        get_res = client.get("/api/dashboard/preferences?user=ceo_v2_test")
        assert get_res.status_code == 200
        get_data = get_res.get_json()
        assert get_data["status"] == "success"
        assert get_data["data"]["theme"] == "dark"
        assert get_data["data"]["pinned_widgets"] == ["widget-kpis", "widget-recommendations"]
        assert get_data["data"]["chart_filters"]["start_date"] == "2026-08-01"

    def test_post_preferences_partial_merge(self, client):
        # Update only theme
        partial_res = client.post(
            "/api/dashboard/preferences",
            json={"user": "ceo_v2_test", "preferences": {"theme": "light"}},
        )
        assert partial_res.status_code == 200
        data = partial_res.get_json()["data"]
        # Theme updated
        assert data["theme"] == "light"
        # Previous pinned_widgets preserved from earlier test
        assert data["pinned_widgets"] == ["widget-kpis", "widget-recommendations"]
        assert data["chart_filters"]["sales_range"] == "weekly"

    def test_post_invalid_payload_returns_400(self, client):
        res = client.post(
            "/api/dashboard/preferences",
            data="not-valid-json",
            content_type="application/json",
        )
        assert res.status_code == 400


class TestDashboardV2Layout:
    """Test CEO Dashboard HTML contains all V2 layout widgets and preserves legacy panels."""

    def test_ceo_dashboard_unauthenticated_redirects(self, client):
        res = client.get("/ceo")
        assert res.status_code in (302, 401, 403)

    def test_ceo_dashboard_authenticated_renders_v2(self, client):
        with client.session_transaction() as sess:
            sess["user"] = "ceo"
            sess["role"] = "ceo"

        res = client.get("/ceo")
        assert res.status_code == 200
        html = res.data.decode("utf-8")

        # 1. Personalization toolbar
        assert "theme-toggle" in html or "toggleTheme" in html
        assert "fullscreen" in html.lower() or "toggleFullscreen" in html
        assert "refresh" in html.lower() or "refreshDashboard" in html

        # 2. Prominent Alerts Banner
        assert "widget-alerts" in html or "alerts-top-banner" in html or "active-alerts-banner" in html

        # 3. Top Row KPI Cards
        assert "widget-kpis" in html or "v2-kpi-cards" in html

        # 4. Executive Analytics Charts
        assert "widget-charts" in html or "v2-analytics-row" in html

        # 5. Consolidated Recommendations
        assert "widget-recommendations" in html or "v2-recommendations" in html

        # 6. Executive AI Chat
        assert "widget-chat" in html or "copilot" in html.lower()

        # 7. Preserved Legacy Specialist Intelligence Panels (MUST NOT BE BROKEN)
        # Sales engine elements
        assert "salesForecastChart" in html
        assert "sales-kpi-total-revenue" in html
        assert "sales-shap-features-list" in html
        # Inventory engine elements
        assert "inventory-decision-text" in html
        assert "inventory-confidence" in html
        # What-if simulator
        assert "sim-sales" in html
        assert "sim-stock" in html
        # Document repository table
        assert "documents-table-body" in html
