"""
tests/test_sales_agent_sprint5.py
----------------------------------
Sprint 5 — SalesAgent Unit Tests

Validates:
  1. can_handle() correctly identifies sales-domain queries.
  2. can_handle() correctly rejects non-sales queries.
  3. execute() always returns a valid AgentResponse conforming to the shared schema.
  4. execute() data dict contains ONLY structured fields (never prose).
  5. execute() data contains zero inventory or knowledge keys.
  6. POST /api/agents/sales endpoint returns a well-formed AgentResponse.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest.mock as mock

import pytest

# ── Project root ────────────────────────────────────────────────────────── #
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.agents.base_agent import AgentResponse
from app.agents.sales_agent import SalesAgent, _SALES_KEYWORDS

# ── Flask app factory ────────────────────────────────────────────────────── #
_SPEC = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(_ROOT, "app.py"),
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
    return SalesAgent()


# ─────────────────────────────────────────────────────────────────────────── #
# 1. can_handle() — Positive cases
# ─────────────────────────────────────────────────────────────────────────── #

class TestCanHandle:

    @pytest.mark.parametrize("query", [
        "What is our sales growth this month?",
        "Show me revenue forecasts for Q3",
        "Which product has the highest demand?",
        "Forecast cotton fabric volumes for 30 days",
        "What is the market trend for fabric orders?",
        "How is pricing affecting our profit margins?",
        "Top product performance this quarter",
        "Are customers buying more this week?",
        "Weekly sales target met?",
        "Volume and turnover for cotton",
    ])
    def test_returns_true_for_sales_queries(self, agent, query):
        assert agent.can_handle(query) is True, (
            f"can_handle() should return True for sales query: '{query}'"
        )

    @pytest.mark.parametrize("query", [
        "How much stock is left in the warehouse?",
        "Reorder policy for raw materials",
        "What does the SOP say about dye quality?",
        "Upload a new compliance document",
        "Inventory health check",
        "Stock remaining days for thread",
    ])
    def test_returns_false_for_non_sales_queries(self, agent, query):
        assert agent.can_handle(query) is False, (
            f"can_handle() should return False for non-sales query: '{query}'"
        )

    def test_returns_false_for_empty_string(self, agent):
        assert agent.can_handle("") is False

    def test_returns_false_for_none_like_query(self, agent):
        assert agent.can_handle("   ") is False

    def test_keyword_set_covers_required_terms(self):
        required = {"sale", "sales", "revenue", "growth", "forecast", "product", "performance"}
        assert required.issubset(_SALES_KEYWORDS)


# ─────────────────────────────────────────────────────────────────────────── #
# 2. execute() — Schema validation
# ─────────────────────────────────────────────────────────────────────────── #

_MOCK_REC_RESPONSE = {
    "status": "success",
    "data": {
        "growth_rate": -0.124,
        "forecast_value": 480000.0,
        "confidence_score": 0.825,
        "decision": "Reduce Inventory",
    },
}

_MOCK_FC_RESPONSE = {
    "status": "success",
    "data": {
        "predicted_sales": 480000.0,
        "confidence": 0.825,
    },
}


class TestExecuteSchema:

    @mock.patch("app.agents.sales_agent.call_api")
    def test_returns_agent_response_instance(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute({"query": "What are our sales projections?"})
        assert isinstance(resp, AgentResponse)

    @mock.patch("app.agents.sales_agent.call_api")
    def test_agent_name_is_sales(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        assert resp.agent_name == "sales"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_status_is_success_on_good_api(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        assert resp.status == "success"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_confidence_is_float_in_range(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        assert isinstance(resp.confidence, float)
        assert 0.0 <= resp.confidence <= 1.0

    @mock.patch("app.agents.sales_agent.call_api")
    def test_timestamp_is_present(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        assert resp.timestamp and isinstance(resp.timestamp, str)

    @mock.patch("app.agents.sales_agent.call_api")
    def test_data_contains_required_keys(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        required = {"sales_growth", "forecast", "recommendation", "market_trend",
                    "top_product", "forecast_period"}
        assert required.issubset(set(resp.data.keys())), (
            f"Missing keys: {required - set(resp.data.keys())}"
        )

    @mock.patch("app.agents.sales_agent.call_api")
    def test_sales_growth_computed_correctly(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        # growth_rate = -0.124 → should be converted to -12.4%
        assert resp.data["sales_growth"] == -12.4

    @mock.patch("app.agents.sales_agent.call_api")
    def test_forecast_is_numeric(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        assert isinstance(resp.data["forecast"], (int, float))
        assert resp.data["forecast"] >= 0

    @mock.patch("app.agents.sales_agent.call_api")
    def test_recommendation_is_short_categorical(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        rec = resp.data["recommendation"]
        assert isinstance(rec, str)
        # Must not be free-form prose (≤ 10 words)
        assert len(rec.split()) <= 10, f"recommendation looks like prose: '{rec}'"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_market_trend_is_valid_enum(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        assert resp.data["market_trend"] in ("Growing", "Stable", "Declining")

    @mock.patch("app.agents.sales_agent.call_api")
    def test_forecast_period_reflects_query(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute({"query": "What is the 7 day sales trend?"})
        assert resp.data["forecast_period"] == "7_days"


# ─────────────────────────────────────────────────────────────────────────── #
# 3. Isolation constraints — zero cross-domain fields
# ─────────────────────────────────────────────────────────────────────────── #

class TestIsolation:

    _FORBIDDEN_KEYS = {"stock_health", "remaining_days", "safety_stock",
                       "policy", "sources", "chunks", "reorder"}

    @mock.patch("app.agents.sales_agent.call_api")
    def test_no_inventory_or_knowledge_keys_in_data(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = agent.execute()
        leaks = self._FORBIDDEN_KEYS & set(resp.data.keys())
        assert not leaks, f"SalesAgent data leaked cross-domain keys: {leaks}"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_no_inventory_or_knowledge_keys_in_to_dict(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        flat = agent.execute().to_dict()
        leaks = self._FORBIDDEN_KEYS & set(flat.keys())
        assert not leaks, f"AgentResponse.to_dict() leaked cross-domain keys: {leaks}"

    def test_no_inventory_imports_in_module(self):
        import ast, inspect
        import app.agents.sales_agent as mod
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = (
                    node.module if isinstance(node, ast.ImportFrom) else
                    ", ".join(alias.name for alias in node.names)
                ) or ""
                assert "inventory" not in module.lower(), (
                    f"SalesAgent imports inventory module: '{module}'"
                )
                assert "knowledge" not in module.lower(), (
                    f"SalesAgent imports knowledge module: '{module}'"
                )


# ─────────────────────────────────────────────────────────────────────────── #
# 4. to_dict() compatibility with AgentResponse schema
# ─────────────────────────────────────────────────────────────────────────── #

class TestToDict:

    @mock.patch("app.agents.sales_agent.call_api")
    def test_to_dict_has_all_schema_keys(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        d = agent.execute().to_dict()
        for key in ("agent_name", "status", "data", "confidence", "timestamp"):
            assert key in d, f"to_dict() missing schema key: '{key}'"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_to_dict_data_is_dict(self, mock_call, agent):
        mock_call.return_value = _MOCK_REC_RESPONSE
        d = agent.execute().to_dict()
        assert isinstance(d["data"], dict)

    @mock.patch("app.agents.sales_agent.call_api")
    def test_error_status_on_api_failure(self, mock_call, agent):
        mock_call.side_effect = Exception("Connection refused")
        resp = agent.execute()
        assert resp.status == "error"
        assert resp.error is not None
        assert resp.data == {}


# ─────────────────────────────────────────────────────────────────────────── #
# 5. Flask endpoint POST /api/agents/sales
# ─────────────────────────────────────────────────────────────────────────── #

class TestSalesAgentEndpoint:

    @mock.patch("app.agents.sales_agent.call_api")
    def test_endpoint_returns_200(self, mock_call, client):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = client.post("/api/agents/sales", json={"question": "sales forecast"})
        assert resp.status_code == 200

    @mock.patch("app.agents.sales_agent.call_api")
    def test_endpoint_response_has_schema_keys(self, mock_call, client):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = client.post("/api/agents/sales", json={"question": "sales forecast"})
        body = resp.get_json()
        for key in ("agent_name", "status", "data", "confidence", "timestamp"):
            assert key in body, f"Response missing key '{key}'"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_endpoint_data_has_required_sales_fields(self, mock_call, client):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = client.post("/api/agents/sales", json={})
        body = resp.get_json()
        data = body.get("data", {})
        for field in ("sales_growth", "forecast", "recommendation", "market_trend"):
            assert field in data, f"data missing field '{field}'"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_endpoint_no_question_still_succeeds(self, mock_call, client):
        mock_call.return_value = _MOCK_REC_RESPONSE
        resp = client.post("/api/agents/sales", json={})
        assert resp.status_code == 200
