"""
tests/test_inventory_agent_sprint5.py
--------------------------------------
Sprint 5 — InventoryAgent Unit Tests

Validates (mirroring test_sales_agent_sprint5.py structure):
  1. can_handle() correctly identifies inventory-domain queries.
  2. can_handle() correctly rejects non-inventory queries.
  3. execute() always returns a valid AgentResponse conforming to the shared schema.
  4. execute() data dict contains ONLY structured fields (never prose).
  5. execute() data contains zero sales or knowledge keys.
  6. POST /api/agents/inventory endpoint returns a well-formed AgentResponse.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import os
import sys
import unittest.mock as mock

import pytest

# ── Project root ────────────────────────────────────────────────────────── #
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.agents.base_agent import AgentResponse
from app.agents.inventory_agent import InventoryAgent, _INVENTORY_KEYWORDS

# ── Flask app factory ────────────────────────────────────────────────────── #
_SPEC = importlib.util.spec_from_file_location(
    "app_entry", os.path.join(_ROOT, "app.py")
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def agent():
    return InventoryAgent()


# ─────────────────────────────────────────────────────────────────────────── #
# Mock API responses
# ─────────────────────────────────────────────────────────────────────────── #

_MOCK_PREDICT_CRITICAL = {
    "status": "success",
    "domain": "inventory",
    "decision": "Reorder Required",
    "prediction": 1,
    "confidence": "High",
    "probability": 0.9231,
    "version": "v1.2",
    "model_status": {
        "model_type": "xgboost",
        "version": "v1.2",
        "accuracy": 0.9231,
        "trained_at": "2026-08-01",
    },
}

_MOCK_PREDICT_HEALTHY = {
    "status": "success",
    "domain": "inventory",
    "decision": "Stock Sufficient",
    "prediction": 0,
    "confidence": "High",
    "probability": 0.87,
    "version": "v1.2",
    "model_status": {
        "model_type": "xgboost",
        "version": "v1.2",
        "accuracy": 0.9231,
        "trained_at": "2026-08-01",
    },
}

_MOCK_METRICS = {
    "status": "success",
    "model_name": "inventory",
    "version": "v1.2",
    "model_type": "xgboost",
    "accuracy": 0.9231,
    "trained_at": "2026-08-01",
    "metrics": {"precision": 0.91, "recall": 0.93},
}


# ─────────────────────────────────────────────────────────────────────────── #
# 1. can_handle() — Positive cases
# ─────────────────────────────────────────────────────────────────────────── #

class TestCanHandle:

    @pytest.mark.parametrize("query", [
        "How much stock do we have left?",
        "Is there a risk of stockout this week?",
        "When should we reorder cotton thread?",
        "Check our warehouse inventory levels",
        "Restocking schedule for raw materials",
        "What is the available fabric supply?",
        "Is our replenishment cycle optimal?",
        "How many remaining days before we run out of dye?",
        "Are we seeing any dead stock in the warehouse?",
        "Fast moving vs slow moving inventory breakdown",
        "Should we restock immediately?",
        "Check if safety stock is sufficient",
        "Procurement planning for next quarter",
    ])
    def test_returns_true_for_inventory_queries(self, agent, query):
        assert agent.can_handle(query) is True, (
            f"can_handle() should return True for inventory query: '{query}'"
        )

    @pytest.mark.parametrize("query", [
        "What is our revenue forecast for next month?",
        "Which product has the highest sales growth?",
        "Show me pricing trends for cotton fabric",
        "Upload the latest compliance document",
        "What does the SOP say about production?",
        "Are customer orders increasing this quarter?",
    ])
    def test_returns_false_for_non_inventory_queries(self, agent, query):
        assert agent.can_handle(query) is False, (
            f"can_handle() should return False for non-inventory query: '{query}'"
        )

    def test_returns_false_for_empty_string(self, agent):
        assert agent.can_handle("") is False

    def test_returns_false_for_whitespace_only(self, agent):
        assert agent.can_handle("   ") is False

    def test_keyword_set_covers_required_terms(self):
        required = {"stock", "inventory", "reorder", "restocking", "warehouse", "stockout"}
        assert required.issubset(_INVENTORY_KEYWORDS)


# ─────────────────────────────────────────────────────────────────────────── #
# 2. execute() — Schema validation
# ─────────────────────────────────────────────────────────────────────────── #

class TestExecuteSchema:

    def _call(self, agent, mock_call, predict_data=None, metrics_data=None):
        """Utility: configure mock and run execute()."""
        predict_data = predict_data or _MOCK_PREDICT_CRITICAL
        metrics_data = metrics_data or _MOCK_METRICS

        def _side_effect(endpoint, **kwargs):
            if "metrics" in endpoint:
                return metrics_data
            return predict_data

        mock_call.side_effect = _side_effect
        return agent.execute()

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_returns_agent_response_instance(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert isinstance(resp, AgentResponse)

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_agent_name_is_inventory(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert resp.agent_name == "inventory"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_status_success_on_good_api(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert resp.status == "success"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_confidence_is_float_in_range(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert isinstance(resp.confidence, float)
        assert 0.0 <= resp.confidence <= 1.0

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_timestamp_is_present(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert resp.timestamp and isinstance(resp.timestamp, str)

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_data_contains_required_keys(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        required = {
            "stock_health", "remaining_days", "recommendation",
            "decision", "confidence_level", "model_version", "model_type",
        }
        missing = required - set(resp.data.keys())
        assert not missing, f"execute() data is missing keys: {missing}"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_critical_decision_maps_to_correct_health(self, mock_call, agent):
        resp = self._call(agent, mock_call, predict_data=_MOCK_PREDICT_CRITICAL)
        assert resp.data["stock_health"] == "Critical"
        assert resp.data["remaining_days"] == 4
        assert "restock" in resp.data["recommendation"].lower()

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_healthy_decision_maps_correctly(self, mock_call, agent):
        resp = self._call(agent, mock_call, predict_data=_MOCK_PREDICT_HEALTHY)
        assert resp.data["stock_health"] == "Healthy"
        assert resp.data["remaining_days"] > 10

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_recommendation_is_short_categorical(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        rec = resp.data["recommendation"]
        assert isinstance(rec, str)
        assert len(rec.split()) <= 10, f"recommendation looks like prose: '{rec}'"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_stock_health_is_valid_enum(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert resp.data["stock_health"] in ("Critical", "Warning", "Healthy")

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_remaining_days_is_integer(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert isinstance(resp.data["remaining_days"], int)

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_model_metadata_captured(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        assert resp.data["model_version"] in ("v1.2", "v1.0")
        assert resp.data["model_type"] == "xgboost"


# ─────────────────────────────────────────────────────────────────────────── #
# 3. Isolation — zero cross-domain keys
# ─────────────────────────────────────────────────────────────────────────── #

class TestIsolation:

    _FORBIDDEN_KEYS = {
        # Sales keys
        "sales_growth", "forecast", "top_product", "market_trend", "forecast_period",
        # Knowledge keys
        "sources", "chunks", "documents", "policy",
    }

    def _call(self, agent, mock_call):
        def _side_effect(endpoint, **kwargs):
            return _MOCK_METRICS if "metrics" in endpoint else _MOCK_PREDICT_CRITICAL
        mock_call.side_effect = _side_effect
        return agent.execute()

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_no_sales_or_knowledge_keys_in_data(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        leaks = self._FORBIDDEN_KEYS & set(resp.data.keys())
        assert not leaks, f"InventoryAgent data leaked cross-domain keys: {leaks}"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_no_cross_domain_keys_in_to_dict(self, mock_call, agent):
        resp = self._call(agent, mock_call)
        flat = resp.to_dict()
        leaks = self._FORBIDDEN_KEYS & set(flat.keys())
        assert not leaks, f"AgentResponse.to_dict() leaked cross-domain keys: {leaks}"

    def test_no_sales_imports_in_module(self):
        import app.agents.inventory_agent as mod
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = (
                    node.module if isinstance(node, ast.ImportFrom) else
                    ", ".join(alias.name for alias in node.names)
                ) or ""
                assert "sales" not in module.lower(), (
                    f"InventoryAgent imports sales module: '{module}'"
                )
                assert "knowledge" not in module.lower(), (
                    f"InventoryAgent imports knowledge module: '{module}'"
                )


# ─────────────────────────────────────────────────────────────────────────── #
# 4. to_dict() and error handling
# ─────────────────────────────────────────────────────────────────────────── #

class TestToDict:

    def _call(self, agent, mock_call):
        def _se(endpoint, **kw):
            return _MOCK_METRICS if "metrics" in endpoint else _MOCK_PREDICT_CRITICAL
        mock_call.side_effect = _se
        return agent.execute().to_dict()

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_to_dict_has_all_schema_keys(self, mock_call, agent):
        d = self._call(agent, mock_call)
        for key in ("agent_name", "status", "data", "confidence", "timestamp"):
            assert key in d, f"to_dict() missing schema key: '{key}'"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_to_dict_data_is_dict(self, mock_call, agent):
        d = self._call(agent, mock_call)
        assert isinstance(d["data"], dict)

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_error_status_on_api_exception(self, mock_call, agent):
        mock_call.side_effect = Exception("Connection refused")
        resp = agent.execute()
        assert resp.status == "error"
        assert resp.error is not None
        assert resp.data == {}
        assert resp.confidence == 0.0


# ─────────────────────────────────────────────────────────────────────────── #
# 5. Flask endpoint POST /api/agents/inventory
# ─────────────────────────────────────────────────────────────────────────── #

class TestInventoryAgentEndpoint:

    def _mock_side_effect(self, endpoint, **kw):
        return _MOCK_METRICS if "metrics" in endpoint else _MOCK_PREDICT_CRITICAL

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_endpoint_returns_200(self, mock_call, client):
        mock_call.side_effect = self._mock_side_effect
        resp = client.post("/api/agents/inventory", json={"question": "stock levels"})
        assert resp.status_code == 200

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_endpoint_response_has_schema_keys(self, mock_call, client):
        mock_call.side_effect = self._mock_side_effect
        resp = client.post("/api/agents/inventory", json={"question": "reorder check"})
        body = resp.get_json()
        for key in ("agent_name", "status", "data", "confidence", "timestamp"):
            assert key in body, f"Response missing schema key '{key}'"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_endpoint_data_has_required_inventory_fields(self, mock_call, client):
        mock_call.side_effect = self._mock_side_effect
        resp = client.post("/api/agents/inventory", json={})
        body = resp.get_json()
        data = body.get("data", {})
        for field in ("stock_health", "remaining_days", "recommendation", "decision"):
            assert field in data, f"data missing field '{field}'"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_endpoint_agent_name_is_inventory(self, mock_call, client):
        mock_call.side_effect = self._mock_side_effect
        body = client.post("/api/agents/inventory", json={}).get_json()
        assert body["agent_name"] == "inventory"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_endpoint_no_question_still_succeeds(self, mock_call, client):
        mock_call.side_effect = self._mock_side_effect
        resp = client.post("/api/agents/inventory", json={})
        assert resp.status_code == 200

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_endpoint_critical_stock_health_in_response(self, mock_call, client):
        mock_call.side_effect = self._mock_side_effect
        body = client.post("/api/agents/inventory", json={"question": "stockout risk"}).get_json()
        assert body["data"]["stock_health"] == "Critical"
