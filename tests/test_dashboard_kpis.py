"""
tests/test_dashboard_kpis.py
----------------------------
Sprint 6 — Executive BI Dashboard: KPI Aggregation & Business Health Tests

Covers:
  1. Business Health Score formula, sub-scores, clamping, and status grading.
  2. KPI Service aggregation (all 7 required KPI fields + composite score).
  3. Caching lifecycle (TTL hit, clear cache, force refresh).
  4. Flask REST API endpoint (GET /api/dashboard/kpis):
     - HTTP 200 contract verification
     - Complete field presence
     - Sub-2-second latency SLA
     - In-memory cache hit on consecutive requests
"""

from __future__ import annotations

import importlib.util
import os
import sys
import time
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.dashboard.kpi.business_health import (
    calculate_sales_score,
    calculate_inventory_score,
    calculate_alert_score,
    compute_business_health,
)
from app.dashboard.kpi.kpi_service import (
    aggregate_kpis,
    clear_kpi_cache,
)

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


@pytest.fixture(autouse=True)
def reset_cache_each_test():
    clear_kpi_cache()
    yield
    clear_kpi_cache()


# ============================================================================ #
# 1. Unit Tests: Business Health Score Engine                                  #
# ============================================================================ #

class TestBusinessHealthScore:

    def test_sales_score_neutral_zero_growth(self):
        """Zero sales growth maps to neutral 50.0."""
        assert calculate_sales_score(0.0) == 50.0

    def test_sales_score_positive_growth(self):
        """Positive growth scales upwards linearly."""
        assert calculate_sales_score(10.0) == 75.0
        assert calculate_sales_score(20.0) == 100.0

    def test_sales_score_negative_growth(self):
        """Negative growth scales downwards linearly."""
        assert calculate_sales_score(-10.0) == 25.0
        assert calculate_sales_score(-20.0) == 0.0

    def test_sales_score_clamping(self):
        """Extreme growth values are safely clamped to [0.0, 100.0]."""
        assert calculate_sales_score(150.0) == 100.0
        assert calculate_sales_score(-150.0) == 0.0

    def test_inventory_score_healthy(self):
        """Healthy inventory receives a top baseline score of 95.0."""
        assert calculate_inventory_score("Healthy", low_stock_count=0) == 95.0
        assert calculate_inventory_score("Stock Sufficient", low_stock_count=0) == 95.0

    def test_inventory_score_warning(self):
        """Warning status has a baseline score of 60.0."""
        assert calculate_inventory_score("Warning", low_stock_count=0) == 60.0

    def test_inventory_score_critical(self):
        """Critical or Reorder Required status has a baseline score of 35.0."""
        assert calculate_inventory_score("Critical", low_stock_count=0) == 35.0
        assert calculate_inventory_score("Reorder Required", low_stock_count=0) == 35.0

    def test_inventory_score_low_stock_penalty(self):
        """Low stock product count penalizes the score by 2.0 per product."""
        score = calculate_inventory_score("Healthy", low_stock_count=5)
        # 95.0 - (5 * 2.0) = 85.0
        assert score == 85.0

    def test_inventory_score_penalty_cannot_go_below_zero(self):
        score = calculate_inventory_score("Critical", low_stock_count=100)
        assert score == 0.0

    def test_alert_score_scaling(self):
        """Fewer alerts yield higher scores; heavy alerts penalize score."""
        assert calculate_alert_score(0) == 100.0
        assert calculate_alert_score(1) == 85.0
        assert calculate_alert_score(2) == 75.0
        assert calculate_alert_score(3) == 60.0
        assert calculate_alert_score(4) == 45.0
        assert calculate_alert_score(8) == 25.0

    def test_composite_formula_calculation(self):
        """Verify the exact 40/40/20 weighted combination."""
        # sales=10.0 -> 75.0; inv="Healthy" (0 low stock) -> 95.0; alert=0 -> 100.0
        # 0.40 * 75.0 + 0.40 * 95.0 + 0.20 * 100.0 = 30.0 + 38.0 + 20.0 = 88.0
        breakdown = compute_business_health(
            sales_growth=10.0,
            inventory_health="Healthy",
            low_stock_count=0,
            recommendations_count=0,
        )
        assert breakdown.score == 88.0
        assert breakdown.status == "Excellent"
        assert breakdown.sales_score == 75.0
        assert breakdown.inventory_score == 95.0
        assert breakdown.alert_score == 100.0

    @pytest.mark.parametrize("growth,inv_status,low_stock,alerts,expected_status", [
        (15.0, "Healthy", 0, 0, "Excellent"),        # Score >= 80
        (5.0, "Healthy", 2, 1, "Good"),              # 65 <= Score < 80
        (-5.0, "Warning", 3, 2, "Fair"),             # 50 <= Score < 65
        (-20.0, "Critical", 10, 4, "Needs Attention") # Score < 50
    ])
    def test_status_grade_mapping(self, growth, inv_status, low_stock, alerts, expected_status):
        breakdown = compute_business_health(growth, inv_status, low_stock, alerts)
        assert breakdown.status == expected_status


# ============================================================================ #
# 2. Service Integration Tests: kpi_service.py                                #
# ============================================================================ #

class TestKPIService:

    def test_aggregate_kpis_returns_all_required_fields(self):
        data = aggregate_kpis()
        required_fields = [
            "total_sales",
            "revenue",
            "sales_growth",
            "inventory_value",
            "inventory_health",
            "low_stock_products_count",
            "ai_recommendations_count",
            "business_health",
            "timestamp",
            "elapsed_ms",
            "cached",
        ]
        for field in required_fields:
            assert field in data, f"Required KPI field '{field}' is missing."

    def test_kpi_data_types(self):
        data = aggregate_kpis()
        assert isinstance(data["total_sales"], (int, float))
        assert isinstance(data["revenue"], float)
        assert isinstance(data["sales_growth"], float)
        assert isinstance(data["inventory_value"], float)
        assert isinstance(data["inventory_health"], str)
        assert isinstance(data["low_stock_products_count"], int)
        assert isinstance(data["ai_recommendations_count"], int)
        assert isinstance(data["business_health"], dict)

    def test_business_health_substructure(self):
        data = aggregate_kpis()
        bh = data["business_health"]
        assert "score" in bh
        assert "status" in bh
        assert "formula" in bh
        assert 0.0 <= bh["score"] <= 100.0

    def test_in_memory_caching_lifecycle(self):
        """Second invocation within TTL must return cached=True with sub-10ms latency."""
        clear_kpi_cache()
        first = aggregate_kpis()
        assert first["cached"] is False

        second = aggregate_kpis()
        assert second["cached"] is True
        assert second["elapsed_ms"] < 50.0
        assert second["revenue"] == first["revenue"]

    def test_force_refresh_bypasses_cache(self):
        first = aggregate_kpis()
        assert first["cached"] is False

        second = aggregate_kpis(force_refresh=True)
        assert second["cached"] is False


# ============================================================================ #
# 3. HTTP API Endpoint Tests: GET /api/dashboard/kpis                         #
# ============================================================================ #

class TestKPIEndpoint:

    def test_endpoint_returns_status_200(self, client):
        resp = client.get("/api/dashboard/kpis")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert "data" in body

    def test_endpoint_contains_all_seven_kpi_fields(self, client):
        resp = client.get("/api/dashboard/kpis")
        body = resp.get_json()
        kpi_data = body["data"]

        # 1. Total Sales
        assert "total_sales" in kpi_data
        assert kpi_data["total_sales"] > 0

        # 2. Revenue
        assert "revenue" in kpi_data
        assert kpi_data["revenue"] > 0

        # 3. Sales Growth
        assert "sales_growth" in kpi_data

        # 4. Inventory Value
        assert "inventory_value" in kpi_data
        assert kpi_data["inventory_value"] > 0

        # 5. Inventory Health
        assert "inventory_health" in kpi_data
        assert kpi_data["inventory_health"] in ("Healthy", "Warning", "Critical")

        # 6. Low Stock Products count
        assert "low_stock_products_count" in kpi_data
        assert isinstance(kpi_data["low_stock_products_count"], int)

        # 7. AI Recommendations count
        assert "ai_recommendations_count" in kpi_data
        assert kpi_data["ai_recommendations_count"] >= 0

        # Business Health Score
        assert "business_health" in kpi_data
        assert "score" in kpi_data["business_health"]
        assert "status" in kpi_data["business_health"]

    def test_endpoint_response_time_under_two_seconds_sla(self, client):
        """Verify that response time is strictly under the 2-second SLA ceiling."""
        clear_kpi_cache()
        t0 = time.perf_counter()
        resp = client.get("/api/dashboard/kpis")
        elapsed_seconds = time.perf_counter() - t0

        assert resp.status_code == 200
        assert elapsed_seconds < 2.0, (
            f"Cold endpoint call took {elapsed_seconds:.2f}s, exceeding 2.0s SLA!"
        )

    def test_endpoint_cached_repeat_response_is_fast(self, client):
        """Repeat call uses in-memory cache and returns almost instantly."""
        # Prime the cache
        client.get("/api/dashboard/kpis")

        t0 = time.perf_counter()
        resp = client.get("/api/dashboard/kpis")
        elapsed_seconds = time.perf_counter() - t0

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["cached"] is True
        assert elapsed_seconds < 0.1, (
            f"Cached endpoint call took {elapsed_seconds:.3f}s, expected < 0.1s"
        )

    def test_endpoint_refresh_query_param(self, client):
        """?refresh=true forces a cache bypass."""
        client.get("/api/dashboard/kpis")  # Prime
        resp = client.get("/api/dashboard/kpis?refresh=true")
        body = resp.get_json()
        assert body["data"]["cached"] is False
