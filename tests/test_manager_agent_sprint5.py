"""
tests/test_manager_agent_sprint5.py
------------------------------------
Sprint 5 Step 6 — ManagerAgent Integration Tests

Validates the full orchestration pipeline:
  1. can_handle() routing selects the right agents per query.
  2. All three agents are triggered for a cross-domain question.
  3. orchestrate() merges outputs and returns confidence + agent_details.
  4. build_prompt() output is passed to the LLM (verified via mock).
  5. register_agent() extensibility — FinanceAgent added with zero routing changes.
  6. POST /api/agents/manager returns all required schema fields.
  7. Empty question returns 400.
  8. Agent failures are isolated and don't crash the pipeline.
  9. Confidence is computed as mean of agent confidences.
 10. agent_details contains full AgentResponse schema per agent.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest.mock as mock
from typing import Any, Dict, Optional

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Load Flask app
_SPEC = importlib.util.spec_from_file_location(
    "app_entry", os.path.join(_ROOT, "app.py")
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app

from app.agents.base_agent import AgentResponse, BaseAgent
from app.agents.manager_agent import ManagerAgent
from app.rag.chat_service import ChatProvider, reset_chat_provider, set_chat_provider


# ─────────────────────────────────────────────────────────────────────────── #
# Fixtures & helpers
# ─────────────────────────────────────────────────────────────────────────── #

INVENTORY_QUESTION = "Should we increase inventory next week?"


class _MockLLM(ChatProvider):
    """Deterministic LLM that echoes the structured prompt back as its answer."""
    def complete(self, system_prompt: str, user_message: str) -> str:
        return (
            "Based on multi-agent analysis: Sales show declining trend. "
            "Inventory is Critical with 4 days remaining. "
            "Policy recommends reorder at safety level. "
            "Recommendation: Increase inventory immediately."
        )


# Typical agent API mock return values
_SALES_API_RESPONSE = {
    "status": "success",
    "data": {
        "growth_rate": -0.124,
        "forecast_value": 480000.0,
        "decision": "Reduce Inventory",
        "top_product": "Cotton Fabric",
    },
}

_INVENTORY_API_RESPONSE = {
    "status": "success",
    "decision": "Reorder Required",
    "probability": 0.88,
    "remaining_days": 4,
    "safety_stock": 200,
}

_KNOWLEDGE_API_RESPONSE = {
    "status": "success",
    "chunks": [
        {
            "chunk_text": "Reorder when stock reaches safety level of 200 units.",
            "source_document": "Inventory Policy.pdf",
            "page_number": 3,
            "score": 0.94,
        }
    ],
    "sources": ["Inventory Policy.pdf"],
}


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def manager():
    return ManagerAgent()


# ─────────────────────────────────────────────────────────────────────────── #
# 1. Registry
# ─────────────────────────────────────────────────────────────────────────── #

class TestRegistry:

    def test_three_agents_registered_by_default(self, manager):
        assert set(manager.registered_agents) == {"sales", "inventory", "knowledge"}

    def test_register_new_agent_no_routing_changes_needed(self, manager):
        """Adding a FinanceAgent requires ZERO changes to ManagerAgent routing."""
        class FinanceAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "finance"

            def can_handle(self, query: str) -> bool:
                return "cashflow" in query.lower() or "finance" in query.lower()

            def execute(self, context: Optional[Dict] = None) -> AgentResponse:
                return AgentResponse(
                    agent_name="finance",
                    status="success",
                    data={"cashflow": 1_200_000.0, "health": "Healthy"},
                    confidence=0.95,
                )

        assert "finance" not in manager.registered_agents
        manager.register_agent(FinanceAgent())
        assert "finance" in manager.registered_agents
        assert len(manager.registered_agents) == 4


# ─────────────────────────────────────────────────────────────────────────── #
# 2. Intent routing via can_handle()
# ─────────────────────────────────────────────────────────────────────────── #

class TestRouting:

    def test_inventory_question_includes_all_three_agents(self, manager):
        selected = manager.route_intent(INVENTORY_QUESTION)
        assert "sales" in selected
        assert "inventory" in selected
        assert "knowledge" in selected

    def test_pure_sales_question_routes_to_sales(self, manager):
        selected = manager.route_intent("What is the revenue forecast this quarter?")
        assert "sales" in selected

    def test_pure_inventory_question_routes_to_inventory(self, manager):
        selected = manager.route_intent("How much stock remains in the warehouse?")
        assert "inventory" in selected

    def test_policy_question_routes_to_knowledge(self, manager):
        selected = manager.route_intent("What is the SOP for procurement?")
        assert "knowledge" in selected

    def test_route_returns_only_registered_agents(self, manager):
        selected = manager.route_intent(INVENTORY_QUESTION)
        for name in selected:
            assert name in manager.registered_agents


# ─────────────────────────────────────────────────────────────────────────── #
# 3. orchestrate() schema
# ─────────────────────────────────────────────────────────────────────────── #

class TestOrchestrateSchema:

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_returns_dict(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            assert isinstance(result, dict)
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_status_is_success(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            assert result["status"] == "success"
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_required_top_level_keys(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            for key in ("status", "question", "answer", "agents_used", "confidence", "agent_details"):
                assert key in result, f"Missing key '{key}' in orchestrate() result"
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_question_is_echoed(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            assert result["question"] == INVENTORY_QUESTION
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_answer_is_non_empty_string(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            assert isinstance(result["answer"], str)
            assert len(result["answer"]) > 10
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_confidence_is_float_in_range(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            conf = result["confidence"]
            assert isinstance(conf, float)
            assert 0.0 <= conf <= 1.0
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_agents_used_is_list(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            assert isinstance(result["agents_used"], list)
        finally:
            reset_chat_provider()


# ─────────────────────────────────────────────────────────────────────────── #
# 4. Integration — all three agents triggered for inventory question
# ─────────────────────────────────────────────────────────────────────────── #

class TestAllThreeAgentsTriggered:

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_all_three_agents_in_agents_used(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            assert "sales" in result["agents_used"]
            assert "inventory" in result["agents_used"]
            assert "knowledge" in result["agents_used"]
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_agent_details_contains_all_three_keys(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            details = result["agent_details"]
            assert "sales" in details
            assert "inventory" in details
            assert "knowledge" in details
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_each_agent_detail_has_schema_keys(self, *_):
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            for name, detail in result["agent_details"].items():
                for key in ("agent_name", "status", "data", "confidence", "timestamp"):
                    assert key in detail, (
                        f"agent_details['{name}'] missing key '{key}'"
                    )
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_answer_grounded_in_merged_data(self, *_):
        """LLM mock returns text referencing inventory/sales — answer must not be empty."""
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            answer = result["answer"]
            # The mock LLM answer contains "inventory" and "recommendation"
            assert "inventory" in answer.lower() or "recommendation" in answer.lower()
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_confidence_is_mean_of_agent_confidences(self, *_):
        """confidence = mean(agent.confidence for active agents)."""
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            details = result["agent_details"]
            expected = round(
                sum(d["confidence"] for d in details.values()) / len(details), 4
            )
            assert abs(result["confidence"] - expected) < 0.001
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_build_prompt_called_with_merged_data(self, *_):
        """Verify build_prompt() is called during orchestration."""
        set_chat_provider(_MockLLM())
        with mock.patch(
            "app.agents.manager_agent.build_prompt", wraps=__import__(
                "app.agents.prompt_builder", fromlist=["build_prompt"]
            ).build_prompt
        ) as mock_build:
            try:
                ManagerAgent().orchestrate(INVENTORY_QUESTION)
                assert mock_build.called, "build_prompt() was not called by orchestrate()"
                call_kwargs = mock_build.call_args
                # First positional arg is agent_outputs (dict), second is question
                agent_outputs_arg = call_kwargs[0][0]
                assert isinstance(agent_outputs_arg, dict)
            finally:
                reset_chat_provider()


# ─────────────────────────────────────────────────────────────────────────── #
# 5. Edge cases
# ─────────────────────────────────────────────────────────────────────────── #

class TestEdgeCases:

    def test_empty_question_returns_error(self, manager):
        result = manager.orchestrate("")
        assert result["status"] == "error"
        assert result["agents_used"] == []
        assert result["confidence"] == 0.0

    def test_whitespace_only_question_returns_error(self, manager):
        result = manager.orchestrate("   ")
        assert result["status"] == "error"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    @mock.patch("app.agents.sales_agent.call_api", side_effect=Exception("Sales API down"))
    @mock.patch("app.agents.inventory_agent.call_api", side_effect=Exception("Inventory API down"))
    def test_failed_agents_isolated_pipeline_continues(self, *_):
        """If sales and inventory fail, knowledge still runs and pipeline returns a result."""
        set_chat_provider(_MockLLM())
        try:
            result = ManagerAgent().orchestrate("What does company policy say?")
            assert result["status"] == "success"
            assert isinstance(result["answer"], str)
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_llm_failure_returns_structured_fallback(self, *_):
        """When LLM is unavailable, orchestrate() returns a deterministic fallback."""
        # Do NOT set a chat provider — force the exception path
        reset_chat_provider()
        try:
            result = ManagerAgent().orchestrate(INVENTORY_QUESTION)
            assert result["status"] == "success"
            assert isinstance(result["answer"], str)
            # Fallback always includes "Recommendation"
            assert "Recommendation" in result["answer"]
        finally:
            reset_chat_provider()


# ─────────────────────────────────────────────────────────────────────────── #
# 6. POST /api/agents/manager Flask endpoint
# ─────────────────────────────────────────────────────────────────────────── #

class TestManagerEndpoint:

    @pytest.fixture(autouse=True)
    def _setup_client(self, client):
        self._client = client

    def test_missing_question_returns_400(self):
        resp = self._client.post("/api/agents/manager", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["status"] == "error"

    def test_empty_question_returns_400(self):
        resp = self._client.post("/api/agents/manager", json={"question": ""})
        assert resp.status_code == 400

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_returns_200_on_valid_question(self, mock_k, mock_inv, mock_s):
        set_chat_provider(_MockLLM())
        try:
            resp = self._client.post(
                "/api/agents/manager",
                json={"question": INVENTORY_QUESTION},
            )
            assert resp.status_code == 200
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_response_contains_required_schema_keys(self, mock_k, mock_inv, mock_s):
        set_chat_provider(_MockLLM())
        try:
            resp = self._client.post(
                "/api/agents/manager",
                json={"question": INVENTORY_QUESTION},
            )
            body = resp.get_json()
            for key in ("status", "question", "answer", "agents_used", "confidence", "agent_details"):
                assert key in body, f"Response missing key '{key}'"
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_all_three_agents_present_in_response(self, mock_k, mock_inv, mock_s):
        set_chat_provider(_MockLLM())
        try:
            body = self._client.post(
                "/api/agents/manager",
                json={"question": INVENTORY_QUESTION},
            ).get_json()
            assert "sales" in body["agents_used"]
            assert "inventory" in body["agents_used"]
            assert "knowledge" in body["agents_used"]
            assert "sales" in body["agent_details"]
            assert "inventory" in body["agent_details"]
            assert "knowledge" in body["agent_details"]
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_confidence_is_numeric(self, mock_k, mock_inv, mock_s):
        set_chat_provider(_MockLLM())
        try:
            body = self._client.post(
                "/api/agents/manager",
                json={"question": INVENTORY_QUESTION},
            ).get_json()
            conf = body["confidence"]
            assert isinstance(conf, (int, float))
            assert 0.0 <= conf <= 1.0
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_answer_is_non_empty_string(self, mock_k, mock_inv, mock_s):
        set_chat_provider(_MockLLM())
        try:
            body = self._client.post(
                "/api/agents/manager",
                json={"question": INVENTORY_QUESTION},
            ).get_json()
            assert isinstance(body["answer"], str)
            assert len(body["answer"]) > 20
        finally:
            reset_chat_provider()

    @mock.patch("app.agents.sales_agent.call_api", return_value=_SALES_API_RESPONSE)
    @mock.patch("app.agents.inventory_agent.call_api", return_value=_INVENTORY_API_RESPONSE)
    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_KNOWLEDGE_API_RESPONSE)
    def test_agent_details_each_has_schema(self, mock_k, mock_inv, mock_s):
        set_chat_provider(_MockLLM())
        try:
            body = self._client.post(
                "/api/agents/manager",
                json={"question": INVENTORY_QUESTION},
            ).get_json()
            for name, detail in body["agent_details"].items():
                for key in ("agent_name", "status", "data", "confidence", "timestamp"):
                    assert key in detail, (
                        f"agent_details['{name}'] missing '{key}'"
                    )
        finally:
            reset_chat_provider()

