"""
tests/test_dashboard_analytics.py
---------------------------------
Sprint 6 — Executive BI Dashboard: Analytics Engines & Endpoint Tests

Covers:
  1. Sales Analytics Engine (daily, weekly, monthly, date range filtering, product ranking, prediction history).
  2. Inventory Analytics Engine (stock trend, turnover, low stock, dead stock, prediction history).
  3. REST API Endpoint GET /api/dashboard/analytics:
     - Sales analytics (daily, weekly, monthly)
     - Inventory analytics (stock trend, turnover, low/dead stock)
     - Date filtering query parameters (?start=...&end=...)
     - Parameter validation (invalid type / invalid range -> HTTP 400)
"""

from __future__ import annotations

import importlib.util
import os
import sys
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.dashboard.analytics.sales_analytics import get_sales_analytics
from app.dashboard.analytics.inventory_analytics import get_inventory_analytics

# Load Flask app factory
_SPEC = importlib.util.spec_from_file_location("app_entry", os.path.join(_ROOT, "app.py"))
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ============================================================================ #
# 1. Sales Analytics Engine Tests                                              #
# ============================================================================ #

class TestSalesAnalytics:

    def test_sales_analytics_daily_trend(self):
        result = get_sales_analytics(range_type="daily")
        assert "trend" in result
        assert "labels" in result
        assert "datasets" in result
        assert "product_performance" in result
        assert "prediction_history" in result
        assert "summary" in result

        # Trend points structure
        assert len(result["trend"]) > 0
        point = result["trend"][0]
        assert "date" in point
        assert "revenue" in point
        assert "volume" in point
        assert isinstance(point["revenue"], float)
        assert isinstance(point["volume"], int)

    def test_sales_analytics_weekly_trend(self):
        result = get_sales_analytics(range_type="weekly")
        assert len(result["trend"]) > 0
        assert result["summary"]["range_type"] == "weekly"

    def test_sales_analytics_monthly_trend(self):
        result = get_sales_analytics(range_type="monthly")
        assert len(result["trend"]) > 0
        assert result["summary"]["range_type"] == "monthly"

    def test_sales_analytics_date_filtering(self):
        start = "2026-05-01"
        end = "2026-06-30"
        result = get_sales_analytics(range_type="daily", start_date=start, end_date=end)
        for point in result["trend"]:
            assert point["date"] >= start
            assert point["date"] <= end

    def test_sales_analytics_product_performance_ranking(self):
        result = get_sales_analytics(top_products_limit=5)
        prods = result["product_performance"]
        assert len(prods) <= 5
        assert len(prods) > 0
        p1 = prods[0]
        assert "product" in p1
        assert "revenue" in p1
        assert "volume" in p1
        assert "share_pct" in p1
        # Descending order check
        if len(prods) > 1:
            assert prods[0]["revenue"] >= prods[1]["revenue"]

    def test_sales_analytics_prediction_history(self):
        result = get_sales_analytics()
        history = result["prediction_history"]
        assert isinstance(history, list)
        if len(history) > 0:
            rec = history[0]
            assert "forecast_value" in rec
            assert "confidence" in rec


# ============================================================================ #
# 2. Inventory Analytics Engine Tests                                          #
# ============================================================================ #

class TestInventoryAnalytics:

    def test_inventory_analytics_stock_trend(self):
        result = get_inventory_analytics(range_type="daily")
        assert "stock_trend" in result
        assert "inventory_turnover" in result
        assert "low_stock_analysis" in result
        assert "dead_stock_analysis" in result
        assert "prediction_history" in result
        assert "summary" in result

        assert len(result["stock_trend"]) > 0
        item = result["stock_trend"][0]
        assert "date" in item
        assert "stock" in item
        assert "production" in item

    def test_inventory_analytics_weekly_and_monthly(self):
        w = get_inventory_analytics(range_type="weekly")
        m = get_inventory_analytics(range_type="monthly")
        assert len(w["stock_trend"]) > 0
        assert len(m["stock_trend"]) > 0

    def test_inventory_turnover_metrics(self):
        result = get_inventory_analytics()
        to = result["inventory_turnover"]
        assert "turnover_ratio" in to
        assert "days_in_inventory" in to
        assert "velocity_status" in to
        assert isinstance(to["turnover_ratio"], float)
        assert isinstance(to["days_in_inventory"], float)

    def test_inventory_low_stock_analysis(self):
        result = get_inventory_analytics(top_items_limit=5)
        ls = result["low_stock_analysis"]
        assert "total_low_stock_count" in ls
        assert "threshold" in ls
        assert "items" in ls
        assert ls["total_low_stock_count"] > 0
        if len(ls["items"]) > 0:
            it = ls["items"][0]
            assert "item_code" in it
            assert "current_stock" in it
            assert "deficit" in it

    def test_inventory_dead_stock_analysis(self):
        result = get_inventory_analytics(top_items_limit=5)
        ds = result["dead_stock_analysis"]
        assert "total_dead_stock_count" in ds
        assert "dead_stock_value" in ds
        assert "dead_stock_ratio_pct" in ds
        assert "items" in ds
        assert ds["total_dead_stock_count"] > 0
        if len(ds["items"]) > 0:
            it = ds["items"][0]
            assert "item_code" in it
            assert "holding_units" in it
            assert "estimated_value" in it

    def test_inventory_analytics_date_filtering(self):
        start = "2026-04-01"
        end = "2026-06-30"
        result = get_inventory_analytics(range_type="daily", start_date=start, end_date=end)
        for point in result["stock_trend"]:
            assert point["date"] >= start
            assert point["date"] <= end


# ============================================================================ #
# 3. HTTP REST API Endpoint Tests: GET /api/dashboard/analytics              #
# ============================================================================ #

class TestAnalyticsEndpoint:

    def test_endpoint_sales_default(self, client):
        resp = client.get("/api/dashboard/analytics?type=sales")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["analytics_type"] == "sales"
        assert body["range"] == "daily"
        assert "trend" in body["data"]
        assert "datasets" in body["data"]

    def test_endpoint_sales_weekly_and_monthly(self, client):
        resp_w = client.get("/api/dashboard/analytics?type=sales&range=weekly")
        assert resp_w.status_code == 200
        assert resp_w.get_json()["range"] == "weekly"

        resp_m = client.get("/api/dashboard/analytics?type=sales&range=monthly")
        assert resp_m.status_code == 200
        assert resp_m.get_json()["range"] == "monthly"

    def test_endpoint_sales_date_filtered(self, client):
        start = "2026-05-01"
        end = "2026-06-15"
        resp = client.get(f"/api/dashboard/analytics?type=sales&range=daily&start={start}&end={end}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["start_date"] == start
        assert body["end_date"] == end
        trend = body["data"]["trend"]
        for pt in trend:
            assert pt["date"] >= start
            assert pt["date"] <= end

    def test_endpoint_inventory_default(self, client):
        resp = client.get("/api/dashboard/analytics?type=inventory")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["analytics_type"] == "inventory"
        assert "stock_trend" in body["data"]
        assert "inventory_turnover" in body["data"]
        assert "low_stock_analysis" in body["data"]
        assert "dead_stock_analysis" in body["data"]

    def test_endpoint_inventory_date_filtered(self, client):
        start = "2026-03-01"
        end = "2026-05-31"
        resp = client.get(f"/api/dashboard/analytics?type=inventory&range=weekly&start={start}&end={end}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["start_date"] == start
        assert body["end_date"] == end
        assert len(body["data"]["stock_trend"]) > 0

    def test_endpoint_invalid_type_returns_400(self, client):
        resp = client.get("/api/dashboard/analytics?type=marketing")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["status"] == "error"
        assert "Must be 'sales' or 'inventory'" in body["message"]

    def test_endpoint_invalid_range_returns_400(self, client):
        resp = client.get("/api/dashboard/analytics?type=sales&range=yearly")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["status"] == "error"
        assert "Must be 'daily', 'weekly', or 'monthly'" in body["message"]
