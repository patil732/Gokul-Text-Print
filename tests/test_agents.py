"""
tests/test_agents.py
--------------------
Comprehensive Unit and Integration Test Suite for Sprint 5 / Sprint 4 Enhancement:
Multi-Agent AI Executive Business Copilot.

Tests:
  1. SalesAgent isolation and strict JSON schema tests.
  2. InventoryAgent isolation and strict JSON schema tests.
  3. KnowledgeAgent isolation and strict JSON schema tests.
  4. Non-prose constraint validation (ensures sub-agents return data only).
  5. Extensibility tests for ManagerAgent registry.
  6. Intent routing unit tests.
  7. PromptBuilder formatting unit tests.
  8. End-to-end integration tests for POST /api/agent/ask and GET /api/agent/status.
"""

from __future__ import annotations

import os
import sys
import unittest.mock as mock
import pytest

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app

from app.agents.base import BaseAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.manager_agent import ManagerAgent
from app.agents.prompt_builder import build_copilot_prompt
from app.agents.sales_agent import SalesAgent
from app.rag.chat_service import ChatProvider, reset_chat_provider, set_chat_provider


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class MockChatProvider(ChatProvider):
    def complete(self, system_prompt: str, user_message: str) -> str:
        return (
            "Based on our synthesis of Sales (-12.4% growth) and Inventory (Critical 4 days remaining), "
            "we recommend immediate restocking to safety levels while curtailing speculative expansion."
        )


# ============================================================================ #
# 1. Sub-Agent Isolation & Strict JSON Output Tests
# ============================================================================ #

class TestSalesAgent:
    """Validate SalesAgent in complete isolation."""

    @mock.patch("app.agents.sales_agent.call_api")
    def test_sales_agent_returns_structured_json(self, mock_call):
        # Mock recommendation and forecast endpoints
        def fake_call(endpoint, **kwargs):
            if "recommendation" in endpoint:
                return {
                    "status": "success",
                    "data": {
                        "growth_rate": -0.124,
                        "forecast_value": 485000.0,
                        "confidence_score": 0.825,
                        "decision": "Reduce Inventory",
                    }
                }
            return {
                "status": "success",
                "data": {
                    "predicted_sales": 485000.0,
                    "confidence": 0.825,
                }
            }

        mock_call.side_effect = fake_call
        agent = SalesAgent()
        res = agent.run("What is our 30 day sales outlook?")

        assert isinstance(res, dict), "SalesAgent must return a dictionary"
        assert res["domain"] == "sales"
        assert res["sales_growth"] == -12.4
        assert res["forecast"] == 485000.0
        assert res["recommendation"] == "Reduce Inventory"
        assert res["confidence"] == 0.825

        # Strict Isolation Constraint: Zero inventory or RAG keys
        forbidden_keys = {"stock_health", "remaining_days", "safety_stock", "policy", "chunks"}
        for k in forbidden_keys:
            assert k not in res, f"SalesAgent leaked unauthorized domain key '{k}'"

    @mock.patch("app.agents.sales_agent.call_api")
    def test_sales_agent_no_freeform_prose(self, mock_call):
        mock_call.return_value = {
            "status": "success",
            "data": {"growth_rate": 0.05, "forecast_value": 100000.0, "decision": "Increase Production"}
        }
        agent = SalesAgent()
        res = agent.run()

        # Enforce that all string values are short categorical codes, not paragraphs
        for k, v in res.items():
            if isinstance(v, str):
                assert len(v.split()) < 15, f"SalesAgent field '{k}' contains free-form conversational prose: '{v}'"


class TestInventoryAgent:
    """Validate InventoryAgent in complete isolation."""

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_inventory_agent_returns_structured_json(self, mock_call):
        mock_call.return_value = {
            "status": "success",
            "decision": "Reorder Required",
            "probability": 0.878,
            "confidence": "High",
        }
        agent = InventoryAgent()
        res = agent.run("Check warehouse inventory")

        assert isinstance(res, dict)
        assert res["domain"] == "inventory"
        assert res["decision"] == "Reorder Required"
        assert res["stock_health"] == "Critical"
        assert res["remaining_days"] == 4
        assert res["confidence"] == 0.878

        # Strict Isolation Constraint: Zero sales or RAG keys
        forbidden_keys = {"sales_growth", "forecast", "revenue", "policy", "sources"}
        for k in forbidden_keys:
            assert k not in res, f"InventoryAgent leaked unauthorized domain key '{k}'"

    @mock.patch("app.agents.inventory_agent.call_api")
    def test_inventory_agent_no_freeform_prose(self, mock_call):
        mock_call.return_value = {"status": "success", "decision": "Optimal Stock", "probability": 0.9}
        agent = InventoryAgent()
        res = agent.run()

        for k, v in res.items():
            if isinstance(v, str):
                assert len(v.split()) < 15, f"InventoryAgent field '{k}' contains free-form prose: '{v}'"


class TestKnowledgeAgent:
    """Validate KnowledgeAgent in complete isolation."""

    @mock.patch("app.agents.knowledge_agent.call_api")
    def test_knowledge_agent_returns_structured_json(self, mock_call):
        mock_call.return_value = {
            "status": "success",
            "chunks": [
                {
                    "chunk_text": "Section 4.1: Reorder when stock reaches safety level of 200 units.",
                    "source_document": "Inventory_Policy.pdf",
                    "page_number": 2,
                    "score": 0.94,
                }
            ],
            "sources": ["Inventory_Policy.pdf"],
        }
        agent = KnowledgeAgent()
        res = agent.run("What is the company policy for reorders?")

        assert isinstance(res, dict)
        assert res["domain"] == "knowledge"
        assert "policy" in res
        assert isinstance(res["sources"], list)
        assert len(res["sources"]) == 1
        # sources is now list[str] (document names); rich detail is in source_details
        assert res["sources"][0] == "Inventory_Policy.pdf"
        # source_details carries the per-chunk structured info
        assert isinstance(res["source_details"], list)
        assert res["source_details"][0]["document"] == "Inventory_Policy.pdf"
        assert res["source_details"][0]["page"] == 2


# ============================================================================ #
# 2. Prompt Builder & Manager Agent Routing Tests
# ============================================================================ #

class TestPromptBuilder:
    """Validate prompt assembly from merged agent outputs."""

    def test_build_copilot_prompt_structure(self):
        merged = {
            "sales": {
                "sales_growth": -12.4,
                "forecast": 480000.0,
                "recommendation": "Reduce Inventory",
                "market_trend": "Declining",
                "top_product": "Cotton Fabric",
                "confidence": 0.825,
            },
            "inventory": {
                "stock_health": "Critical",
                "decision": "Reorder Required",
                "remaining_days": 4,
                "recommendation": "Restock immediately",
                "confidence": 0.88,
            },
            "knowledge": {
                "policy": "Reorder when stock reaches safety level.",
                "sources": [{"document": "Inventory_Policy.pdf", "page": 2}],
            },
        }

        system_prompt, user_message = build_copilot_prompt("Should we increase inventory?", merged)

        assert "Gokul Tex Print Executive Business Copilot" in system_prompt
        assert "Should we increase inventory?" in user_message
        assert "[SALES INTELLIGENCE]" in user_message
        assert "-12.4%" in user_message
        assert "[INVENTORY INTELLIGENCE]" in user_message
        assert "Critical" in user_message
        assert "[ENTERPRISE POLICIES & SOPs]" in user_message
        assert "Inventory_Policy.pdf" in user_message


class TestManagerAgent:
    """Validate ManagerAgent intent routing, parallel execution, and extensibility."""

    def test_intent_routing_single_domains(self):
        mgr = ManagerAgent()
        assert mgr.route_intent("What is our projected sales revenue?") == ["sales"]
        assert mgr.route_intent("Check current warehouse stock level") == ["inventory"]
        assert mgr.route_intent("What is company standard operating procedure?") == ["knowledge"]

    def test_intent_routing_cross_domain(self):
        mgr = ManagerAgent()
        agents = mgr.route_intent("Should we increase inventory?")
        assert "sales" in agents
        assert "inventory" in agents
        assert "knowledge" in agents

    def test_manager_extensibility_custom_agent(self):
        """Confirm adding a new domain agent requires zero changes to other agents."""
        class FinanceAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "finance"

            def run(self, question: str = "") -> dict:
                return {"domain": "finance", "operating_cashflow": 1200000.0, "status": "Healthy"}

        mgr = ManagerAgent()
        assert "finance" not in mgr.registered_agents

        mgr.register_agent("finance", FinanceAgent())
        assert "finance" in mgr.registered_agents
        assert len(mgr.registered_agents) == 4

    @mock.patch("app.agents.sales_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.knowledge_agent.call_api")
    def test_manager_ask_orchestration(self, mock_k, mock_inv, mock_sales):
        mock_sales.return_value = {
            "status": "success",
            "data": {"growth_rate": -0.124, "forecast_value": 480000.0, "decision": "Reduce Inventory"}
        }
        mock_inv.return_value = {
            "status": "success",
            "decision": "Reorder Required",
            "probability": 0.88,
        }
        mock_k.return_value = {
            "status": "success",
            "chunks": [{"chunk_text": "Reorder policy rule.", "source_document": "Policy.pdf", "page_number": 1}],
        }

        set_chat_provider(MockChatProvider())
        try:
            mgr = ManagerAgent()
            result = mgr.ask("Should we increase inventory?")

            assert result["status"] == "success"
            assert "answer" in result
            assert "Sales (-12.4% growth)" in result["answer"]
            assert set(result["agents_used"]) == {"sales", "inventory", "knowledge"}
            assert "sales" in result["raw_data"]
            assert "inventory" in result["raw_data"]
            assert "knowledge" in result["raw_data"]
        finally:
            reset_chat_provider()


# ============================================================================ #
# 3. End-to-End API Integration Tests (POST /api/agent/ask)
# ============================================================================ #

class TestAgentAPIEndpoints:
    """Validate Flask REST API endpoints."""

    def test_get_agent_status(self, client):
        resp = client.get("/api/agent/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "online"
        assert "sales" in data["registered_agents"]
        assert "inventory" in data["registered_agents"]
        assert "knowledge" in data["registered_agents"]

    def test_post_agent_ask_empty_returns_400(self, client):
        resp = client.post("/api/agent/ask", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"

    @mock.patch("app.agents.sales_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.knowledge_agent.call_api")
    def test_post_agent_ask_integration(self, mock_k, mock_inv, mock_sales, client):
        mock_sales.return_value = {
            "status": "success",
            "data": {"growth_rate": -0.124, "forecast_value": 480000.0, "decision": "Reduce Inventory"}
        }
        mock_inv.return_value = {
            "status": "success",
            "decision": "Reorder Required",
            "probability": 0.88,
        }
        mock_k.return_value = {
            "status": "success",
            "chunks": [{"chunk_text": "Reorder policy rule.", "source_document": "Policy.pdf", "page_number": 1}],
        }

        set_chat_provider(MockChatProvider())
        try:
            resp = client.post("/api/agent/ask", json={"question": "Should we increase inventory?"})
            assert resp.status_code == 200
            data = resp.get_json()

            assert data["status"] == "success"
            assert data["question"] == "Should we increase inventory?"
            assert "Sales (-12.4% growth)" in data["answer"]
            assert "sales" in data["agents_used"]
            assert "inventory" in data["agents_used"]
            assert "knowledge" in data["agents_used"]
            assert isinstance(data["raw_data"], dict)
            assert data["raw_data"]["sales"]["sales_growth"] == -12.4
        finally:
            reset_chat_provider()
