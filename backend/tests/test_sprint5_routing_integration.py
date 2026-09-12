"""
tests/test_sprint5_routing_integration.py
------------------------------------------
Sprint 5 — Agent Routing & Orchestration Integration Tests

Covers the four canonical routing scenarios specified in the Definition of Done:

  Scenario A — Sales-Only Question
      Only SalesAgent.can_handle() returns True.
      InventoryAgent and KnowledgeAgent must NOT execute.

  Scenario B — Inventory-Only Question
      Only InventoryAgent.can_handle() returns True.
      SalesAgent must NOT execute.

  Scenario C — Knowledge-Only Policy Question
      Only KnowledgeAgent.can_handle() returns True (explicit SOP keyword).
      SalesAgent and InventoryAgent must NOT execute.

  Scenario D — Combined Question (All-Three Agents)
      All three agents handle the query.
      orchestrate() must invoke all three, merge outputs, call LLM, and return
      a response containing agent_details for every active agent.

Additional coverage:
  - Negative: agents with irrelevant queries are not invoked (call_count==0).
  - Prompt Builder: sections appear iff the corresponding agent ran.
  - Confidence: result.confidence == mean(agent confidences).
  - POST /api/agents/manager Flask endpoint contract per scenario.
  - AgentResponse schema validation for each agent detail.
  - Deterministic fallback when LLM is unavailable.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import unittest.mock as mock
from typing import Any, Dict, Optional

import pytest

# ── Project root on sys.path ─────────────────────────────────────────────── #
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Load Flask application factory ───────────────────────────────────────── #
_SPEC = importlib.util.spec_from_file_location(
    "app_entry", os.path.join(_ROOT, "app.py")
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app

from app.agents.base_agent import AgentResponse, BaseAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.manager_agent import ManagerAgent
from app.agents.prompt_builder import build_prompt
from app.agents.sales_agent import SalesAgent
from app.rag.chat_service import ChatProvider, reset_chat_provider, set_chat_provider


# ─────────────────────────────────────────────────────────────────────────── #
# Shared mock API payloads (identical shape to live API responses)
# ─────────────────────────────────────────────────────────────────────────── #

_SALES_API_OK = {
    "status": "success",
    "data": {
        "growth_rate": -0.124,
        "forecast_value": 480_000.0,
        "decision": "Reduce Inventory",
        "top_product": "Cotton Fabric",
        "confidence_score": 0.825,
    },
}

_INVENTORY_API_OK = {
    "status": "success",
    "decision": "Reorder Required",
    "probability": 0.882,
    "remaining_days": 4,
    "safety_stock": 200,
}

_KNOWLEDGE_API_OK = {
    "status": "success",
    "chunks": [
        {
            "chunk_text": "Section 4.1: Reorder when stock reaches the safety level of 200 units.",
            "source_document": "Inventory_Policy.pdf",
            "page_number": 3,
            "score": 0.94,
        }
    ],
    "sources": ["Inventory_Policy.pdf"],
}


class _DeterministicLLM(ChatProvider):
    """Mock LLM that always returns a predictable recommendation string."""

    def complete(self, system_prompt: str, user_message: str) -> str:
        return (
            "Based on the multi-agent analysis: Sales show a declining trend (-12.4%). "
            "Inventory is Critical with only 4 days of stock remaining. "
            "Enterprise policy mandates reorder at safety level. "
            "**Recommendation**: Increase inventory orders by 30% immediately."
        )


# ─────────────────────────────────────────────────────────────────────────── #
# Fixtures
# ─────────────────────────────────────────────────────────────────────────── #

@pytest.fixture(scope="module")
def flask_client():
    """Module-scoped Flask test client — created once for all API tests."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def manager():
    """Fresh ManagerAgent per test."""
    return ManagerAgent()


# ============================================================================ #
# UNIT TESTS — can_handle() routing correctness                                #
# ============================================================================ #

class TestCanHandleRouting:
    """
    Verify that each agent's can_handle() method returns exactly the right
    True/False for every scenario without any external API calls.
    """

    # ── Scenario A: Sales-only questions ─────────────────────────────────── #

    @pytest.mark.parametrize("query", [
        "What is our revenue forecast for this quarter?",
        "What is the sales growth rate over the last 30 days?",
        "Show me the top product performance by sales volume.",
        "What is our monthly income trend?",
    ])
    def test_sales_can_handle_sales_queries(self, query):
        assert SalesAgent().can_handle(query) is True, (
            f"SalesAgent should handle sales query: '{query}'"
        )

    @pytest.mark.parametrize("query", [
        "What is our revenue forecast for this quarter?",
        "What is the sales growth rate over the last 30 days?",
    ])
    def test_inventory_cannot_handle_pure_sales_queries(self, query):
        """Inventory agent must NOT claim pure sales questions."""
        assert InventoryAgent().can_handle(query) is False, (
            f"InventoryAgent must NOT handle pure sales query: '{query}'"
        )

    # ── Scenario B: Inventory-only questions ─────────────────────────────── #

    @pytest.mark.parametrize("query", [
        "How many days of stock do we have remaining in the warehouse?",
        "What is the current reorder status for raw materials?",
        "Check our warehouse stock level and restocking needs.",
        "What is the current stockout risk for thread supplies?",
    ])
    def test_inventory_can_handle_inventory_queries(self, query):
        assert InventoryAgent().can_handle(query) is True, (
            f"InventoryAgent should handle inventory query: '{query}'"
        )

    @pytest.mark.parametrize("query", [
        "How many days of stock do we have remaining in the warehouse?",
        "What is the current reorder status for raw materials?",
    ])
    def test_sales_cannot_handle_pure_inventory_queries(self, query):
        """Sales agent must NOT claim pure inventory / warehouse questions."""
        assert SalesAgent().can_handle(query) is False, (
            f"SalesAgent must NOT handle pure inventory query: '{query}'"
        )

    # ── Scenario C: Knowledge / policy questions ──────────────────────────── #

    @pytest.mark.parametrize("query", [
        "What is the standard operating procedure for quality compliance?",
        "What does the company policy say about quality control defects?",
        "Find the guideline for employee conduct.",
        "According to our manual, what is the approved inspection protocol?",
    ])
    def test_knowledge_can_handle_policy_queries(self, query):
        assert KnowledgeAgent().can_handle(query) is True, (
            f"KnowledgeAgent should handle policy query: '{query}'"
        )

    @pytest.mark.parametrize("query", [
        "What is the standard operating procedure for quality compliance?",
        "What does the company policy say about safety compliance?",
    ])
    def test_sales_cannot_handle_pure_policy_queries(self, query):
        assert SalesAgent().can_handle(query) is False, (
            f"SalesAgent must NOT handle pure policy query: '{query}'"
        )

    @pytest.mark.parametrize("query", [
        "What is the standard operating procedure for quality compliance?",
        "Find the guideline for employee conduct.",
    ])
    def test_inventory_cannot_handle_pure_policy_queries(self, query):
        assert InventoryAgent().can_handle(query) is False, (
            f"InventoryAgent must NOT handle pure policy query: '{query}'"
        )

    # ── Scenario D: Combined questions (all three) ────────────────────────── #

    @pytest.mark.parametrize("query", [
        "Based on company policy and our sales forecast, should we restock the warehouse inventory?",
        "According to safety guidelines and projected sales demand, should we increase warehouse stock?",
    ])
    def test_all_three_can_handle_combined_queries(self, query):
        assert SalesAgent().can_handle(query) is True, (
            f"SalesAgent should handle combined query: '{query}'"
        )
        assert InventoryAgent().can_handle(query) is True, (
            f"InventoryAgent should handle combined query: '{query}'"
        )
        assert KnowledgeAgent().can_handle(query) is True, (
            f"KnowledgeAgent should handle combined query: '{query}'"
        )


# ============================================================================ #
# UNIT TESTS — ManagerAgent._select_agents() routing                          #
# ============================================================================ #

class TestManagerRouting:
    """
    Validate ManagerAgent's internal routing logic produces the correct
    agent selection for all four scenario types.
    """

    # ── Scenario A ────────────────────────────────────────────────────────── #

    def test_scenario_a_sales_only_routing(self, manager):
        """Sales-only question: only SalesAgent is selected."""
        selected = manager.route_intent("What is the quarterly revenue forecast?")
        assert "sales" in selected, "SalesAgent must be selected for sales question"
        assert "inventory" not in selected, (
            "InventoryAgent must NOT be selected for a pure sales question"
        )

    def test_scenario_a_route_returns_list(self, manager):
        selected = manager.route_intent("What is the quarterly revenue forecast?")
        assert isinstance(selected, list)
        assert len(selected) >= 1

    # ── Scenario B ────────────────────────────────────────────────────────── #

    def test_scenario_b_inventory_only_routing(self, manager):
        """Inventory-only question: only InventoryAgent is selected."""
        selected = manager.route_intent(
            "How many days of stock do we have remaining in the warehouse?"
        )
        assert "inventory" in selected, "InventoryAgent must be selected"
        assert "sales" not in selected, (
            "SalesAgent must NOT be selected for a pure inventory question"
        )

    # ── Scenario C ────────────────────────────────────────────────────────── #

    def test_scenario_c_knowledge_only_routing(self, manager):
        """Knowledge-only question: only KnowledgeAgent is selected."""
        selected = manager.route_intent(
            "What is the standard operating procedure for quality compliance?"
        )
        assert "knowledge" in selected, "KnowledgeAgent must be selected"
        assert "sales" not in selected, (
            "SalesAgent must NOT be selected for a pure SOP question"
        )
        assert "inventory" not in selected, (
            "InventoryAgent must NOT be selected for a pure SOP question"
        )

    # ── Scenario D ────────────────────────────────────────────────────────── #

    def test_scenario_d_combined_all_three_routing(self, manager):
        """Combined executive question triggers all three agents."""
        selected = manager.route_intent("Should we increase inventory levels next week?")
        assert "sales" in selected, "SalesAgent must be selected for combined question"
        assert "inventory" in selected, "InventoryAgent must be selected"
        assert "knowledge" in selected, "KnowledgeAgent must be selected"

    def test_scenario_d_route_returns_all_registered(self, manager):
        """All selected agents must exist in the registry."""
        question = "Should we increase inventory levels next week?"
        selected = manager.route_intent(question)
        for name in selected:
            assert name in manager.registered_agents, (
                f"Routed agent '{name}' is not in the registry"
            )


# ============================================================================ #
# INTEGRATION TESTS — execute() is only called for agents that were selected  #
# ============================================================================ #

class TestAgentExecutionIsolation:
    """
    Confirm that agents whose can_handle() returns False are never invoked.
    Uses mock.patch on call_api and asserts call counts per scenario.
    """

    # ── Scenario A: Sales-only ─────────────────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_scenario_a_only_sales_executes(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        """
        Pure sales question -> only SalesAgent.call_api is invoked.
        Inventory and Knowledge call_api must have zero calls.
        """
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the quarterly revenue forecast?"
            )
            assert result["status"] == "success"
            assert "sales" in result["agents_used"]
            assert "inventory" not in result["agents_used"], (
                "InventoryAgent must NOT execute for a pure sales question"
            )
            assert mock_inv.call_count == 0, (
                f"InventoryAgent.call_api was called {mock_inv.call_count} times — must be 0"
            )
            assert mock_knowledge.call_count == 0, (
                f"KnowledgeAgent.call_api was called {mock_knowledge.call_count} times — must be 0"
            )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_scenario_a_agent_details_contains_only_sales(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the quarterly revenue forecast?"
            )
            details = result["agent_details"]
            assert "sales" in details
            assert "inventory" not in details, (
                "agent_details must not contain inventory for a sales-only question"
            )
        finally:
            reset_chat_provider()

    # ── Scenario B: Inventory-only ────────────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api")
    def test_scenario_b_only_inventory_executes(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        """
        Pure inventory question -> only InventoryAgent.call_api is invoked.
        SalesAgent call_api must have zero calls.
        """
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "How many days of stock do we have remaining in the warehouse?"
            )
            assert result["status"] == "success"
            assert "inventory" in result["agents_used"]
            assert "sales" not in result["agents_used"], (
                "SalesAgent must NOT execute for a pure inventory question"
            )
            assert mock_sales.call_count == 0, (
                f"SalesAgent.call_api was called {mock_sales.call_count} times — must be 0"
            )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api")
    def test_scenario_b_sales_data_absent_from_result(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "How many days of stock do we have remaining in the warehouse?"
            )
            assert "inventory" in result["agent_details"]
            assert "sales" not in result["agent_details"]
        finally:
            reset_chat_provider()

    # ── Scenario C: Knowledge-only ────────────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.sales_agent.call_api")
    def test_scenario_c_only_knowledge_executes(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        """
        Pure policy question -> only KnowledgeAgent.call_api is invoked.
        Sales and Inventory call_api must have zero calls.
        """
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the standard operating procedure for quality compliance?"
            )
            assert result["status"] == "success"
            assert "knowledge" in result["agents_used"]
            assert "sales" not in result["agents_used"], (
                "SalesAgent must NOT execute for a pure policy question"
            )
            assert "inventory" not in result["agents_used"], (
                "InventoryAgent must NOT execute for a pure policy question"
            )
            assert mock_sales.call_count == 0, (
                f"SalesAgent.call_api called {mock_sales.call_count} times — expected 0"
            )
            assert mock_inv.call_count == 0, (
                f"InventoryAgent.call_api called {mock_inv.call_count} times — expected 0"
            )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.sales_agent.call_api")
    def test_scenario_c_source_details_in_knowledge_data(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        """KnowledgeAgent data must include source_details list."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the standard operating procedure for quality compliance?"
            )
            k_detail = result["agent_details"]["knowledge"]
            assert "source_details" in k_detail["data"], (
                "KnowledgeAgent agent_details.data must contain 'source_details'"
            )
            assert isinstance(k_detail["data"]["source_details"], list)
        finally:
            reset_chat_provider()

    # ── Scenario D: All-three combined ───────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_scenario_d_all_three_execute(self, mock_sales, mock_inv, mock_knowledge):
        """Combined question triggers Sales, Inventory, and Knowledge agents."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            assert result["status"] == "success"
            assert set(result["agents_used"]) == {"sales", "inventory", "knowledge"}, (
                f"Expected all three agents, got: {result['agents_used']}"
            )
            assert mock_sales.call_count >= 1, "SalesAgent.call_api not called"
            assert mock_inv.call_count >= 1, "InventoryAgent.call_api not called"
            assert mock_knowledge.call_count >= 1, "KnowledgeAgent.call_api not called"
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_scenario_d_agent_details_all_three_present(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            details = result["agent_details"]
            assert "sales" in details
            assert "inventory" in details
            assert "knowledge" in details
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_scenario_d_llm_answer_in_response(
        self, mock_sales, mock_inv, mock_knowledge
    ):
        """LLM answer from mock must appear in the orchestrate result."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            answer = result["answer"]
            assert isinstance(answer, str) and len(answer) > 20
            assert "Recommendation" in answer or "recommendation" in answer.lower()
        finally:
            reset_chat_provider()


# ============================================================================ #
# INTEGRATION TESTS — Structured data from each agent is correct               #
# ============================================================================ #

class TestAgentStructuredInsights:
    """
    Validate that the structured data returned by each agent in agent_details
    matches the expected schema and values derived from the mocked API responses.
    """

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_sales_agent_returns_sales_growth(self, _):
        """SalesAgent data contains correct growth rate (-12.4%)."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the quarterly revenue forecast?"
            )
            sales_data = result["agent_details"]["sales"]["data"]
            assert "sales_growth" in sales_data
            assert abs(sales_data["sales_growth"] - (-12.4)) < 0.01, (
                f"Expected -12.4, got {sales_data['sales_growth']}"
            )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_sales_agent_returns_forecast(self, _):
        """SalesAgent data contains correct forecast value."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the quarterly revenue forecast?"
            )
            sales_data = result["agent_details"]["sales"]["data"]
            assert "forecast" in sales_data
            assert sales_data["forecast"] == 480_000.0
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_sales_agent_derives_market_trend(self, _):
        """SalesAgent derives market_trend: growth < -5 -> Declining."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the quarterly revenue forecast?"
            )
            sales_data = result["agent_details"]["sales"]["data"]
            assert sales_data["market_trend"] == "Declining"
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    def test_inventory_agent_returns_stock_health(self, _):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "How many days of stock do we have remaining in the warehouse?"
            )
            inv_data = result["agent_details"]["inventory"]["data"]
            assert "stock_health" in inv_data
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    def test_inventory_agent_returns_reorder_decision(self, _):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "How many days of stock do we have remaining in the warehouse?"
            )
            inv_data = result["agent_details"]["inventory"]["data"]
            assert "decision" in inv_data
            assert inv_data["decision"] == "Reorder Required"
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_knowledge_agent_returns_policy_string(self, _):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the standard operating procedure for quality compliance?"
            )
            k_data = result["agent_details"]["knowledge"]["data"]
            assert "policy" in k_data
            assert isinstance(k_data["policy"], str) and len(k_data["policy"]) > 0
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_knowledge_agent_returns_correct_source_document(self, _):
        """KnowledgeAgent source_details contains the expected document name."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What is the standard operating procedure for quality compliance?"
            )
            k_data = result["agent_details"]["knowledge"]["data"]
            doc_names = [s["document"] for s in k_data["source_details"]]
            assert "Inventory_Policy.pdf" in doc_names, (
                f"Expected 'Inventory_Policy.pdf' in {doc_names}"
            )
        finally:
            reset_chat_provider()


# ============================================================================ #
# INTEGRATION TESTS — Prompt Builder combines outputs correctly                 #
# ============================================================================ #

class TestPromptBuilderIntegration:
    """
    Verify that build_prompt() produces correctly labelled sections
    for whichever agents ran, and omits sections for agents that did not run.
    """

    def test_sales_section_contains_growth_figure(self):
        prompt = build_prompt(
            {
                "sales": {
                    "sales_growth": -12.4,
                    "forecast": 480_000.0,
                    "recommendation": "Reduce Inventory",
                    "market_trend": "Declining",
                }
            },
            "What is our sales outlook?",
        )
        assert "-12.4" in prompt

    def test_inventory_section_contains_stock_health(self):
        prompt = build_prompt(
            {
                "inventory": {
                    "stock_health": "Critical",
                    "remaining_days": 4,
                    "decision": "Reorder Required",
                    "recommendation": "Restock immediately",
                }
            },
            "How is our inventory?",
        )
        assert "Critical" in prompt

    def test_knowledge_section_contains_policy_excerpt(self):
        prompt = build_prompt(
            {
                "knowledge": {
                    "policy": "Reorder when stock reaches 200 units.",
                    "sources": ["Inventory_Policy.pdf"],
                    "source_details": [
                        {"document": "Inventory_Policy.pdf", "page": 3, "score": 0.94}
                    ],
                    "relevant_chunks": 1,
                    "query_used": "standard operating procedure",
                }
            },
            "What does the SOP say?",
        )
        assert "200 units" in prompt

    def test_combined_prompt_contains_all_three_data_points(self):
        prompt = build_prompt(
            {
                "sales": {
                    "sales_growth": -12.4,
                    "forecast": 480_000.0,
                    "recommendation": "Reduce Inventory",
                    "market_trend": "Declining",
                },
                "inventory": {
                    "stock_health": "Critical",
                    "remaining_days": 4,
                    "decision": "Reorder Required",
                    "recommendation": "Restock",
                },
                "knowledge": {
                    "policy": "Reorder at safety level.",
                    "sources": ["Policy.pdf"],
                    "source_details": [],
                    "relevant_chunks": 1,
                    "query_used": "reorder policy",
                },
            },
            "Should we increase inventory?",
        )
        assert "-12.4" in prompt
        assert "Critical" in prompt
        assert "safety level" in prompt

    def test_prompt_omits_sales_key_when_sales_absent(self):
        """If sales key is absent, prompt must NOT fabricate sales data fields."""
        prompt = build_prompt(
            {
                "inventory": {
                    "stock_health": "Normal",
                    "remaining_days": 30,
                    "decision": "Optimal Stock",
                    "recommendation": "Maintain",
                }
            },
            "Is our inventory healthy?",
        )
        assert "sales_growth" not in prompt

    def test_prompt_omits_inventory_key_when_inventory_absent(self):
        prompt = build_prompt(
            {
                "sales": {
                    "sales_growth": 8.2,
                    "forecast": 600_000.0,
                    "recommendation": "Increase Production",
                    "market_trend": "Growing",
                }
            },
            "What are our sales doing?",
        )
        assert "stock_health" not in prompt

    def test_prompt_always_contains_original_question(self):
        question = "UNIQUE_CEO_QUESTION_SENTINEL_42"
        prompt = build_prompt({"sales": {"sales_growth": 5.0}}, question)
        assert question in prompt

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_build_prompt_called_during_orchestration(self, *_):
        """build_prompt() is actually invoked by orchestrate()."""
        set_chat_provider(_DeterministicLLM())
        with mock.patch(
            "app.agents.manager_agent.build_prompt",
            wraps=__import__(
                "app.agents.prompt_builder", fromlist=["build_prompt"]
            ).build_prompt,
        ) as mock_bp:
            try:
                ManagerAgent().orchestrate("Should we increase inventory levels next week?")
                assert mock_bp.called, "build_prompt() must be called by orchestrate()"
                agent_outputs_arg = mock_bp.call_args[0][0]
                assert isinstance(agent_outputs_arg, dict)
                assert "sales" in agent_outputs_arg
                assert "inventory" in agent_outputs_arg
                assert "knowledge" in agent_outputs_arg
            finally:
                reset_chat_provider()


# ============================================================================ #
# INTEGRATION TESTS — Confidence score computation                              #
# ============================================================================ #

class TestConfidenceComputation:

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_confidence_equals_mean_of_active_agents(self, *_):
        """confidence == mean(agent_details[n].confidence) for each agent that ran."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            details = result["agent_details"]
            expected_mean = round(
                sum(d["confidence"] for d in details.values()) / len(details), 4
            )
            assert abs(result["confidence"] - expected_mean) < 1e-3, (
                f"Confidence {result['confidence']!r} != expected mean {expected_mean!r}"
            )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_confidence_within_valid_range(self, *_):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            assert 0.0 <= result["confidence"] <= 1.0
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_confidence_is_float_type(self, *_):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            assert isinstance(result["confidence"], float)
        finally:
            reset_chat_provider()


# ============================================================================ #
# INTEGRATION TESTS — AgentResponse schema validation                          #
# ============================================================================ #

class TestAgentResponseSchema:

    _REQUIRED_KEYS = ("agent_name", "status", "data", "confidence", "timestamp")

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_all_agent_details_have_required_keys(self, *_):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            for agent_name, detail in result["agent_details"].items():
                for key in self._REQUIRED_KEYS:
                    assert key in detail, (
                        f"agent_details['{agent_name}'] missing required key '{key}'"
                    )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_agent_name_matches_dict_key(self, *_):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            for key, detail in result["agent_details"].items():
                assert detail["agent_name"] == key
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_all_agent_statuses_are_non_error(self, *_):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            for name, detail in result["agent_details"].items():
                assert detail["status"] in ("success", "warning"), (
                    f"Agent '{name}' returned status='{detail['status']}'"
                )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_all_agent_data_fields_are_dicts(self, *_):
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            for name, detail in result["agent_details"].items():
                assert isinstance(detail["data"], dict), (
                    f"agent_details['{name}'].data is not a dict: {type(detail['data'])}"
                )
        finally:
            reset_chat_provider()


# ============================================================================ #
# API INTEGRATION TESTS — POST /api/agents/manager Flask endpoint              #
# ============================================================================ #

class TestManagerEndpointScenarios:
    """End-to-end HTTP tests against the real Flask app for all four scenarios."""

    @pytest.fixture(autouse=True)
    def _bind_client(self, flask_client):
        self._client = flask_client

    def test_empty_body_returns_400(self):
        resp = self._client.post("/api/agents/manager", json={})
        assert resp.status_code == 400
        assert resp.get_json()["status"] == "error"

    def test_empty_question_returns_400(self):
        resp = self._client.post("/api/agents/manager", json={"question": ""})
        assert resp.status_code == 400

    def test_whitespace_question_returns_400(self):
        resp = self._client.post("/api/agents/manager", json={"question": "   "})
        assert resp.status_code == 400

    # ── Scenario A via HTTP ───────────────────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_http_scenario_a_sales_only(self, mock_s, mock_i, mock_k):
        set_chat_provider(_DeterministicLLM())
        try:
            resp = self._client.post(
                "/api/agents/manager",
                json={"question": "What is the quarterly revenue forecast?"},
            )
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["status"] == "success"
            assert "sales" in body["agents_used"]
            assert "inventory" not in body["agents_used"]
            assert "sales" in body["agent_details"]
            assert "inventory" not in body["agent_details"]
        finally:
            reset_chat_provider()

    # ── Scenario B via HTTP ───────────────────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api")
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api")
    def test_http_scenario_b_inventory_only(self, mock_s, mock_i, mock_k):
        set_chat_provider(_DeterministicLLM())
        try:
            resp = self._client.post(
                "/api/agents/manager",
                json={"question": "How many days of stock do we have remaining in the warehouse?"},
            )
            assert resp.status_code == 200
            body = resp.get_json()
            assert "inventory" in body["agents_used"]
            assert "sales" not in body["agents_used"]
            assert "inventory" in body["agent_details"]
            assert "sales" not in body["agent_details"]
        finally:
            reset_chat_provider()

    # ── Scenario C via HTTP ───────────────────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api")
    @mock.patch("app.agents.sales_agent.call_api")
    def test_http_scenario_c_knowledge_only(self, mock_s, mock_i, mock_k):
        set_chat_provider(_DeterministicLLM())
        try:
            resp = self._client.post(
                "/api/agents/manager",
                json={"question": "What is the standard operating procedure for quality compliance?"},
            )
            assert resp.status_code == 200
            body = resp.get_json()
            assert "knowledge" in body["agents_used"]
            assert "sales" not in body["agents_used"]
            assert "inventory" not in body["agents_used"]
            k_detail = body["agent_details"]["knowledge"]
            assert "source_details" in k_detail["data"]
        finally:
            reset_chat_provider()

    # ── Scenario D via HTTP ───────────────────────────────────────────────── #

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_http_scenario_d_all_three(self, mock_s, mock_i, mock_k):
        set_chat_provider(_DeterministicLLM())
        try:
            resp = self._client.post(
                "/api/agents/manager",
                json={"question": "Should we increase inventory levels next week?"},
            )
            assert resp.status_code == 200
            body = resp.get_json()
            assert body["status"] == "success"
            assert set(body["agents_used"]) == {"sales", "inventory", "knowledge"}
            assert "sales" in body["agent_details"]
            assert "inventory" in body["agent_details"]
            assert "knowledge" in body["agent_details"]
            for key in ("status", "question", "answer", "agents_used", "confidence", "agent_details"):
                assert key in body, f"Response missing key '{key}'"
            assert 0.0 <= body["confidence"] <= 1.0
            assert isinstance(body["answer"], str) and len(body["answer"]) > 20
        finally:
            reset_chat_provider()


# ============================================================================ #
# INTEGRATION TESTS — Edge cases & fallbacks                                   #
# ============================================================================ #

class TestEdgeCasesAndFallbacks:

    def test_empty_question_returns_error_status(self, manager):
        result = manager.orchestrate("")
        assert result["status"] == "error"
        assert result["agents_used"] == []
        assert result["confidence"] == 0.0

    def test_whitespace_question_returns_error_status(self, manager):
        result = manager.orchestrate("   \t  ")
        assert result["status"] == "error"

    @mock.patch(
        "app.agents.sales_agent.call_api",
        side_effect=Exception("Sales API unreachable"),
    )
    @mock.patch(
        "app.agents.inventory_agent.call_api",
        side_effect=Exception("Inventory API unreachable"),
    )
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    def test_two_agent_failures_pipeline_survives(self, *_):
        """If Sales and Inventory agents fail, Knowledge still completes the pipeline."""
        set_chat_provider(_DeterministicLLM())
        try:
            result = ManagerAgent().orchestrate(
                "What does company policy say about procurement?"
            )
            assert result["status"] == "success"
            assert isinstance(result["answer"], str)
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_OK)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_OK)
    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_OK)
    def test_llm_failure_returns_deterministic_fallback(self, *_):
        """When no LLM provider is set, orchestrate() uses the structured fallback."""
        reset_chat_provider()
        try:
            result = ManagerAgent().orchestrate(
                "Should we increase inventory levels next week?"
            )
            assert result["status"] == "success"
            assert isinstance(result["answer"], str) and len(result["answer"]) > 10
            assert "Recommendation" in result["answer"], (
                f"Fallback answer must contain 'Recommendation': {result['answer'][:200]}"
            )
        finally:
            reset_chat_provider()
