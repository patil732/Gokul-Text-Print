"""
tests/test_dashboard_recommendations.py
---------------------------------------
Unit & Integration Tests for Executive Dashboard Recommendation Aggregator (Sprint 6).

Covers:
  1. Mocked outputs from all four intelligence sources:
     - Sales Engine (Sprint 2)
     - Inventory Engine (Sprint 3)
     - Knowledge Engine (Sprint 4)
     - Manager Agent (Sprint 5)
  2. Correct normalization into standard schema:
     { recommendation, reason, confidence, priority, source, timestamp }
  3. Priority derivation rules, including inventory "Critical" health override to HIGH.
  4. Priority-sorted ordering (HIGH > MEDIUM > LOW, then confidence descending).
  5. API endpoint GET /api/dashboard/recommendations (status 200, query filters, error handling).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from app.dashboard.recommendations.aggregator import (
    RecommendationAggregator,
    aggregate_recommendations,
)


@pytest.fixture
def aggregator():
    return RecommendationAggregator()


@pytest.fixture
def mock_sales_output():
    return {
        "raw_decision": "Increase Production",
        "reason": "Projected sales growth of +18.5% over 30_days warrants capacity expansion.",
        "confidence": 0.88,
        "growth_rate": 18.5,
        "forecast_period": "30_days",
        "source": "sales",
        "timestamp": "2026-09-09T10:00:00",
    }


@pytest.fixture
def mock_inventory_critical_low_confidence():
    """Inventory item with Critical health but LOW confidence (0.45). Must derive HIGH priority."""
    return {
        "raw_decision": "Stockout Risk",
        "recommendation": "Restock Immediately",
        "reason": "Inventory health is Critical (Stockout Risk). Immediate replenishment recommended.",
        "confidence": 0.45,
        "stock_health": "Critical",
        "source": "inventory",
        "timestamp": "2026-09-09T10:05:00",
    }


@pytest.fixture
def mock_inventory_healthy():
    return {
        "raw_decision": "Stock Sufficient",
        "recommendation": "Maintain Replenishment Cycle",
        "reason": "Inventory levels are healthy across warehouse facilities.",
        "confidence": 0.65,
        "stock_health": "Healthy",
        "source": "inventory",
        "timestamp": "2026-09-09T10:06:00",
    }


@pytest.fixture
def mock_knowledge_output():
    return {
        "policy": "Safety stock buffer of 500 units must be maintained for cotton yarn at all times.",
        "sources": ["Inventory Policy.pdf", "SOP.pdf"],
        "reason": "Governed by standard operating policy (Inventory Policy.pdf).",
        "confidence": 0.92,
        "source": "knowledge",
        "timestamp": "2026-09-09T10:07:00",
    }


@pytest.fixture
def mock_manager_outputs():
    return [
        {
            "answer": "Recommendation: Increase inventory orders by 25% and negotiate supplier discounts.",
            "question": "Should we increase inventory next quarter?",
            "confidence": 0.72,
            "agents_used": ["sales", "inventory"],
            "source": "manager",
            "timestamp": "2026-09-09T10:10:00",
        },
        {
            "answer": "Maintain current operational cadence with bi-weekly quality audits.",
            "question": "Are operations aligned with company standards?",
            "confidence": 0.50,
            "agents_used": ["knowledge"],
            "source": "manager",
            "timestamp": "2026-09-09T10:12:00",
        },
    ]


# --------------------------------------------------------------------------- #
# 1. Normalization Tests
# --------------------------------------------------------------------------- #

class TestNormalization:
    REQUIRED_KEYS = {"recommendation", "reason", "confidence", "priority", "source", "timestamp"}

    def test_normalize_sales_output(self, aggregator, mock_sales_output):
        normalized = aggregator.normalize_item(mock_sales_output, source="sales")
        assert set(normalized.keys()) == self.REQUIRED_KEYS
        assert normalized["recommendation"] == "Increase Production"
        assert "growth of +18.5%" in normalized["reason"]
        assert normalized["confidence"] == 0.88
        assert normalized["priority"] == "HIGH"
        assert normalized["source"] == "sales"
        assert normalized["timestamp"] == "2026-09-09T10:00:00"

    def test_normalize_inventory_output(self, aggregator, mock_inventory_critical_low_confidence):
        normalized = aggregator.normalize_item(mock_inventory_critical_low_confidence, source="inventory")
        assert set(normalized.keys()) == self.REQUIRED_KEYS
        assert normalized["recommendation"] == "Restock Immediately"
        assert normalized["confidence"] == 0.45
        assert normalized["source"] == "inventory"
        # Critical health must produce HIGH priority even with 0.45 confidence
        assert normalized["priority"] == "HIGH"

    def test_normalize_knowledge_output(self, aggregator, mock_knowledge_output):
        normalized = aggregator.normalize_item(mock_knowledge_output, source="knowledge")
        assert set(normalized.keys()) == self.REQUIRED_KEYS
        assert "Safety stock buffer" in normalized["recommendation"]
        assert "Inventory Policy.pdf" in normalized["reason"]
        assert normalized["confidence"] == 0.92
        assert normalized["priority"] == "HIGH"
        assert normalized["source"] == "knowledge"

    def test_normalize_manager_output_extracts_recommendation(self, aggregator, mock_manager_outputs):
        m_item = mock_manager_outputs[0]
        normalized = aggregator.normalize_item(m_item, source="manager")
        assert set(normalized.keys()) == self.REQUIRED_KEYS
        assert "Increase inventory orders" in normalized["recommendation"]
        assert "Derived from multi-agent synthesis" in normalized["reason"]
        assert normalized["confidence"] == 0.72
        assert normalized["priority"] == "MEDIUM"
        assert normalized["source"] == "manager"


# --------------------------------------------------------------------------- #
# 2. Priority Derivation Rules
# --------------------------------------------------------------------------- #

class TestPriorityDerivation:
    """
    Validates source-specific rules:
      - Inventory Critical health -> HIGH regardless of confidence
      - Inventory Warning health -> MEDIUM (or HIGH if conf >= 0.85)
      - Sales extreme growth / high confidence -> HIGH
      - Knowledge high score -> HIGH
      - Manager confidence tiers
    """

    def test_inventory_critical_health_overrides_low_confidence(self, aggregator):
        # Extremely low confidence (0.15) must STILL be HIGH due to Critical health
        p = aggregator.derive_priority(
            confidence=0.15,
            source="inventory",
            metadata={"stock_health": "Critical", "raw_decision": "Stockout Risk"},
        )
        assert p == "HIGH"

    def test_inventory_warning_health_medium_priority(self, aggregator):
        p = aggregator.derive_priority(
            confidence=0.60,
            source="inventory",
            metadata={"stock_health": "Warning", "raw_decision": "Low Stock"},
        )
        assert p == "MEDIUM"

    def test_inventory_healthy_low_confidence_low_priority(self, aggregator):
        p = aggregator.derive_priority(
            confidence=0.40,
            source="inventory",
            metadata={"stock_health": "Healthy", "raw_decision": "Stock Sufficient"},
        )
        assert p == "LOW"

    def test_sales_extreme_growth_high_priority(self, aggregator):
        p = aggregator.derive_priority(
            confidence=0.65,
            source="sales",
            metadata={"growth_rate": 16.0},
        )
        assert p == "HIGH"

    def test_sales_moderate_growth_medium_priority(self, aggregator):
        p = aggregator.derive_priority(
            confidence=0.68,
            source="sales",
            metadata={"growth_rate": 5.0},
        )
        assert p == "MEDIUM"

    def test_sales_low_confidence_low_priority(self, aggregator):
        p = aggregator.derive_priority(
            confidence=0.45,
            source="sales",
            metadata={"growth_rate": 2.0},
        )
        assert p == "LOW"

    def test_knowledge_high_confidence_high_priority(self, aggregator):
        p = aggregator.derive_priority(confidence=0.90, source="knowledge")
        assert p == "HIGH"

    def test_knowledge_medium_confidence_medium_priority(self, aggregator):
        p = aggregator.derive_priority(confidence=0.70, source="knowledge")
        assert p == "MEDIUM"

    def test_knowledge_low_confidence_low_priority(self, aggregator):
        p = aggregator.derive_priority(confidence=0.55, source="knowledge")
        assert p == "LOW"

    def test_manager_confidence_tiering(self, aggregator):
        assert aggregator.derive_priority(confidence=0.85, source="manager") == "HIGH"
        assert aggregator.derive_priority(confidence=0.68, source="manager") == "MEDIUM"
        assert aggregator.derive_priority(confidence=0.45, source="manager") == "LOW"


# --------------------------------------------------------------------------- #
# 3. Aggregation & Sorting Order Tests
# --------------------------------------------------------------------------- #

class TestAggregationAndSorting:
    def test_mocked_four_sources_aggregation_and_sort_order(
        self,
        aggregator,
        mock_sales_output,
        mock_inventory_critical_low_confidence,
        mock_inventory_healthy,
        mock_knowledge_output,
        mock_manager_outputs,
    ):
        """
        Aggregate mocked inputs from all 4 sources and verify sort order:
        HIGH > MEDIUM > LOW, with confidence descending within each tier.
        """
        results = aggregator.aggregate(
            sales_raw=mock_sales_output,                            # HIGH (conf 0.88)
            inventory_raw=mock_inventory_critical_low_confidence,   # HIGH (conf 0.45 override)
            knowledge_raw=mock_knowledge_output,                    # HIGH (conf 0.92)
            manager_raws=mock_manager_outputs,                      # Item 0: MEDIUM (conf 0.72), Item 1: LOW (conf 0.50)
        )

        assert len(results) == 5

        # Check all sources are represented
        sources = {item["source"] for item in results}
        assert sources == {"sales", "inventory", "knowledge", "manager"}

        # Verify priority sorting order
        priorities = [item["priority"] for item in results]
        high_items = [p for p in priorities if p == "HIGH"]
        med_items = [p for p in priorities if p == "MEDIUM"]
        low_items = [p for p in priorities if p == "LOW"]

        assert len(high_items) == 3
        assert len(med_items) == 1
        assert len(low_items) == 1

        # Confirm all HIGH items precede MEDIUM, which precede LOW
        assert priorities == ["HIGH", "HIGH", "HIGH", "MEDIUM", "LOW"]

        # Within the HIGH tier, check secondary sorting by confidence descending:
        # Knowledge (0.92) > Sales (0.88) > Inventory (0.45)
        high_confs = [item["confidence"] for item in results if item["priority"] == "HIGH"]
        assert high_confs == [0.92, 0.88, 0.45]

    def test_priority_filtering(
        self,
        aggregator,
        mock_sales_output,
        mock_inventory_critical_low_confidence,
        mock_knowledge_output,
        mock_manager_outputs,
    ):
        results_high = aggregator.aggregate(
            sales_raw=mock_sales_output,
            inventory_raw=mock_inventory_critical_low_confidence,
            knowledge_raw=mock_knowledge_output,
            manager_raws=mock_manager_outputs,
            priority_filter="HIGH",
        )
        assert len(results_high) == 3
        assert all(item["priority"] == "HIGH" for item in results_high)

        results_med = aggregator.aggregate(
            sales_raw=mock_sales_output,
            inventory_raw=mock_inventory_critical_low_confidence,
            knowledge_raw=mock_knowledge_output,
            manager_raws=mock_manager_outputs,
            priority_filter="MEDIUM",
        )
        assert len(results_med) == 1
        assert results_med[0]["priority"] == "MEDIUM"

    def test_limit_parameter(
        self,
        aggregator,
        mock_sales_output,
        mock_inventory_critical_low_confidence,
        mock_knowledge_output,
        mock_manager_outputs,
    ):
        results = aggregator.aggregate(
            sales_raw=mock_sales_output,
            inventory_raw=mock_inventory_critical_low_confidence,
            knowledge_raw=mock_knowledge_output,
            manager_raws=mock_manager_outputs,
            limit=2,
        )
        assert len(results) == 2
        # Should be the top 2 highest priority items
        assert results[0]["confidence"] >= results[1]["confidence"]


# --------------------------------------------------------------------------- #
# 4. HTTP Endpoint Integration Tests (GET /api/dashboard/recommendations)
# --------------------------------------------------------------------------- #

class TestRecommendationsEndpoint:
    @pytest.fixture
    def client(self):
        import importlib.util
        import os
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location("app_entry", os.path.join(root_dir, "app.py"))
        app_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_mod)
        app = app_mod.create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_endpoint_returns_status_200(self, client):
        resp = client.get("/api/dashboard/recommendations")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["status"] == "success"
        assert "count" in payload
        assert "data" in payload
        assert "elapsed_ms" in payload
        assert isinstance(payload["data"], list)

    def test_endpoint_items_have_required_schema(self, client):
        resp = client.get("/api/dashboard/recommendations")
        payload = resp.get_json()
        data = payload["data"]
        assert len(data) > 0, "Expected at least one recommendation"
        for item in data:
            assert "recommendation" in item
            assert "reason" in item
            assert "confidence" in item
            assert "priority" in item
            assert "source" in item
            assert "timestamp" in item
            assert item["priority"] in ("HIGH", "MEDIUM", "LOW")
            assert 0.0 <= item["confidence"] <= 1.0

    def test_endpoint_priority_filter(self, client):
        resp = client.get("/api/dashboard/recommendations?priority=high")
        assert resp.status_code == 200
        payload = resp.get_json()
        for item in payload["data"]:
            assert item["priority"] == "HIGH"

    def test_endpoint_invalid_priority_returns_400(self, client):
        resp = client.get("/api/dashboard/recommendations?priority=urgent")
        assert resp.status_code == 400
        payload = resp.get_json()
        assert payload["status"] == "error"
        assert "Invalid priority" in payload["message"]

    def test_endpoint_limit_query_param(self, client):
        resp = client.get("/api/dashboard/recommendations?limit=2")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert len(payload["data"]) <= 2
        assert payload["count"] <= 2

    def test_endpoint_invalid_limit_returns_400(self, client):
        resp = client.get("/api/dashboard/recommendations?limit=abc")
        assert resp.status_code == 400
        payload = resp.get_json()
        assert payload["status"] == "error"
        assert "Invalid limit" in payload["message"]
