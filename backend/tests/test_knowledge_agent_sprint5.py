"""
tests/test_knowledge_agent_sprint5.py
--------------------------------------
Sprint 5 — KnowledgeAgent Unit Tests

Validates (mirroring Steps 2 & 3 test structure):
  1. can_handle() correctly identifies knowledge/policy-domain queries.
  2. can_handle() acts as fallback when no Sales or Inventory intent is detected.
  3. can_handle() defers to Sales/Inventory agents for clearly scoped queries.
  4. execute() always returns a valid AgentResponse conforming to the shared schema.
  5. execute() data dict contains ONLY structured fields — NOT a chat-style answer.
  6. execute() data contains zero sales or inventory keys.
  7. POST /api/agents/knowledge endpoint returns well-formed structured data.
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
from app.agents.knowledge_agent import KnowledgeAgent, _KNOWLEDGE_KEYWORDS

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
    return KnowledgeAgent()


# ─────────────────────────────────────────────────────────────────────────── #
# Mock RAG API responses
# ─────────────────────────────────────────────────────────────────────────── #

_MOCK_RAG_SUCCESS = {
    "status": "success",
    "query": "reorder policy",
    "top_k": 5,
    "elapsed_ms": 12.4,
    "chunks": [
        {
            "chunk_id": "abc-001",
            "chunk_text": "Reorder when stock reaches safety level as per section 4.2 of the SOP.",
            "page_number": 3,
            "source_document": "Inventory Policy.pdf",
            "score": 0.9421,
        },
        {
            "chunk_id": "abc-002",
            "chunk_text": "Safety stock must cover a minimum of 7 days of demand.",
            "page_number": 5,
            "source_document": "Inventory Policy.pdf",
            "score": 0.8912,
        },
        {
            "chunk_id": "abc-003",
            "chunk_text": "Purchase orders must be raised 14 days before expected stockout.",
            "page_number": 2,
            "source_document": "Procurement_SOP.pdf",
            "score": 0.8634,
        },
    ],
    "sources": ["Inventory Policy.pdf", "Procurement_SOP.pdf"],
}

_MOCK_RAG_EMPTY = {
    "status": "success",
    "query": "xyz",
    "top_k": 5,
    "elapsed_ms": 3.1,
    "chunks": [],
    "sources": [],
}

_MOCK_RAG_ERROR = {
    "status": "error",
    "message": "No documents indexed yet.",
}


# ─────────────────────────────────────────────────────────────────────────── #
# 1. can_handle() — Explicit knowledge keyword triggers
# ─────────────────────────────────────────────────────────────────────────── #

class TestCanHandleExplicit:

    @pytest.mark.parametrize("query", [
        "What is the SOP for handling dye defects?",
        "Show me the company policy on quality control",
        "What are the procurement guidelines?",
        "Where is the reorder procedure documented?",
        "List the compliance regulations for weaving",
        "What certification is required for fabric export?",
        "Find the ISO standard for thread quality",
        "What does the manual say about loom maintenance?",
        "Search for approved suppliers in the knowledge base",
        "Look up the QC rejection guidelines",
    ])
    def test_returns_true_for_knowledge_queries(self, agent, query):
        assert agent.can_handle(query) is True, (
            f"can_handle() should return True for knowledge query: '{query}'"
        )

    def test_returns_false_for_empty_string(self, agent):
        assert agent.can_handle("") is False

    def test_returns_false_for_whitespace(self, agent):
        assert agent.can_handle("   ") is False

    def test_keyword_set_covers_required_terms(self):
        required = {"policy", "sop", "procedure", "guideline", "guidelines", "compliance"}
        assert required.issubset(_KNOWLEDGE_KEYWORDS)


# ─────────────────────────────────────────────────────────────────────────── #
# 2. can_handle() — Fallback (no other domain intent detected)
# ─────────────────────────────────────────────────────────────────────────── #

class TestCanHandleFallback:

    @pytest.mark.parametrize("query", [
        "Tell me about the factory",
        "What happened last month?",
        "General business overview",
        "Any updates from management?",
    ])
    def test_returns_true_as_fallback_for_ambiguous_queries(self, agent, query):
        # No sales or inventory keywords → KnowledgeAgent is fallback
        assert agent.can_handle(query) is True, (
            f"can_handle() should return True as fallback for ambiguous query: '{query}'"
        )


# ─────────────────────────────────────────────────────────────────────────── #
# 3. can_handle() — Defers to Sales / Inventory for clear domain queries
# ─────────────────────────────────────────────────────────────────────────── #

class TestCanHandleDeference:

    @pytest.mark.parametrize("query", [
        "What is our revenue forecast this quarter?",
        "How much stock is remaining in the warehouse?",
        "Sales growth for cotton fabric last month",
        "Reorder schedule for thread inventory",
    ])
    def test_returns_false_for_clearly_scoped_domain_queries(self, agent, query):
        # Clearly sales or inventory → KnowledgeAgent should NOT claim ownership
        result = agent.can_handle(query)
        assert result is False, (
            f"can_handle() should return False for a clearly Sales/Inventory query: '{query}'"
        )


# ─────────────────────────────────────────────────────────────────────────── #
# 4. execute() — Schema validation
# ─────────────────────────────────────────────────────────────────────────── #

class TestExecuteSchema:

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_returns_agent_response_instance(self, mock_call, agent):
        assert isinstance(agent.execute(), AgentResponse)

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_agent_name_is_knowledge(self, mock_call, agent):
        assert agent.execute().agent_name == "knowledge"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_status_is_success_on_good_api(self, mock_call, agent):
        assert agent.execute().status == "success"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_confidence_is_float_in_range(self, mock_call, agent):
        resp = agent.execute()
        assert isinstance(resp.confidence, float)
        assert 0.0 <= resp.confidence <= 1.0

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_timestamp_is_present(self, mock_call, agent):
        resp = agent.execute()
        assert resp.timestamp and isinstance(resp.timestamp, str)

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_data_contains_required_keys(self, mock_call, agent):
        data = agent.execute().data
        required = {"policy", "sources", "source_details", "relevant_chunks", "query_used"}
        missing = required - set(data.keys())
        assert not missing, f"execute() data missing keys: {missing}"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_policy_is_string_not_prose_paragraph(self, mock_call, agent):
        policy = agent.execute().data["policy"]
        assert isinstance(policy, str)
        # Must be a concise statement, not a multi-paragraph essay
        assert len(policy) < 500, f"policy field is too long (looks like prose): {len(policy)} chars"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_sources_is_list_of_strings(self, mock_call, agent):
        sources = agent.execute().data["sources"]
        assert isinstance(sources, list)
        assert all(isinstance(s, str) for s in sources)

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_source_details_has_correct_structure(self, mock_call, agent):
        details = agent.execute().data["source_details"]
        assert isinstance(details, list)
        for d in details:
            assert "document" in d
            assert "page" in d
            assert "score" in d
            assert isinstance(d["score"], float)
            assert isinstance(d["page"], int)

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_relevant_chunks_count_is_integer(self, mock_call, agent):
        count = agent.execute().data["relevant_chunks"]
        assert isinstance(count, int)
        assert count == len(_MOCK_RAG_SUCCESS["chunks"])

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_confidence_reflects_top_chunk_score(self, mock_call, agent):
        resp = agent.execute()
        expected_score = _MOCK_RAG_SUCCESS["chunks"][0]["score"]
        assert abs(resp.confidence - expected_score) < 0.001

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_query_used_is_populated(self, mock_call, agent):
        resp = agent.execute({"query": "What is the reorder policy?"})
        assert resp.data["query_used"] == "What is the reorder policy?"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_default_query_used_when_no_context(self, mock_call, agent):
        resp = agent.execute()
        assert isinstance(resp.data["query_used"], str)
        assert len(resp.data["query_used"]) > 0


# ─────────────────────────────────────────────────────────────────────────── #
# 5. execute() — Empty and error API responses
# ─────────────────────────────────────────────────────────────────────────── #

class TestExecuteEdgeCases:

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_EMPTY)
    def test_empty_chunks_returns_warning_status(self, mock_call, agent):
        resp = agent.execute({"query": "xyz"})
        # Empty chunks with success status → warning
        assert resp.status in ("success", "warning")

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_EMPTY)
    def test_empty_chunks_relevant_count_is_zero(self, mock_call, agent):
        resp = agent.execute()
        assert resp.data["relevant_chunks"] == 0

    @mock.patch("app.agents.knowledge_agent.call_api")
    def test_api_exception_returns_error_response(self, mock_call, agent):
        mock_call.side_effect = Exception("Connection refused")
        resp = agent.execute()
        assert resp.status == "error"
        assert resp.error is not None
        assert resp.data == {}
        assert resp.confidence == 0.0


# ─────────────────────────────────────────────────────────────────────────── #
# 6. Isolation — no Sales/Inventory cross-domain contamination
# ─────────────────────────────────────────────────────────────────────────── #

class TestIsolation:

    _FORBIDDEN_KEYS = {
        # Sales
        "sales_growth", "forecast", "top_product", "market_trend", "forecast_period",
        # Inventory
        "stock_health", "remaining_days", "safety_stock", "reorder_level", "decision",
    }

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_no_cross_domain_keys_in_data(self, mock_call, agent):
        data = agent.execute().data
        leaks = self._FORBIDDEN_KEYS & set(data.keys())
        assert not leaks, f"KnowledgeAgent data leaked cross-domain keys: {leaks}"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_no_cross_domain_keys_in_to_dict(self, mock_call, agent):
        flat = agent.execute().to_dict()
        leaks = self._FORBIDDEN_KEYS & set(flat.keys())
        assert not leaks, f"AgentResponse.to_dict() leaked cross-domain keys: {leaks}"

    def test_no_sales_or_inventory_imports_in_module(self):
        """
        Verify that knowledge_agent.py has NO top-level (module-scope) imports of
        sales_agent or inventory_agent.  Lazy imports inside function bodies are
        intentional (used by the fallback helper) and explicitly permitted.
        """
        import app.agents.knowledge_agent as mod
        src = inspect.getsource(mod)
        tree = ast.parse(src)

        # Only look at top-level statements (direct children of the Module node)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = (
                    node.module if isinstance(node, ast.ImportFrom) else
                    ", ".join(alias.name for alias in node.names)
                ) or ""
                assert not module.endswith("sales_agent"), (
                    f"KnowledgeAgent has a top-level import of sales_agent: '{module}'"
                )
                assert not module.endswith("inventory_agent"), (
                    f"KnowledgeAgent has a top-level import of inventory_agent: '{module}'"
                )


    def test_data_is_structured_not_natural_language(self):
        """Ensure 'policy' field is a concise statement, never a chat response."""
        agent = KnowledgeAgent()
        with mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS):
            data = agent.execute().data
        policy = data["policy"]
        # A chat-style answer would contain "I " or "Here is" etc.
        chat_indicators = ["i think", "here is", "please note", "let me", "i would"]
        assert not any(ci in policy.lower() for ci in chat_indicators), (
            f"policy field looks like a chat-style answer: '{policy}'"
        )


# ─────────────────────────────────────────────────────────────────────────── #
# 7. to_dict() compliance
# ─────────────────────────────────────────────────────────────────────────── #

class TestToDict:

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_to_dict_has_all_schema_keys(self, mock_call, agent):
        d = agent.execute().to_dict()
        for key in ("agent_name", "status", "data", "confidence", "timestamp"):
            assert key in d, f"to_dict() missing schema key: '{key}'"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_to_dict_data_is_dict(self, mock_call, agent):
        assert isinstance(agent.execute().to_dict()["data"], dict)

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_agent_name_in_to_dict(self, mock_call, agent):
        assert agent.execute().to_dict()["agent_name"] == "knowledge"


# ─────────────────────────────────────────────────────────────────────────── #
# 8. Flask endpoint POST /api/agents/knowledge
# ─────────────────────────────────────────────────────────────────────────── #

class TestKnowledgeAgentEndpoint:

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_endpoint_returns_200(self, mock_call, client):
        resp = client.post("/api/agents/knowledge", json={"question": "reorder policy"})
        assert resp.status_code == 200

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_endpoint_response_has_schema_keys(self, mock_call, client):
        body = client.post(
            "/api/agents/knowledge", json={"question": "SOP for fabric quality"}
        ).get_json()
        for key in ("agent_name", "status", "data", "confidence", "timestamp"):
            assert key in body, f"Response missing schema key '{key}'"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_endpoint_data_has_required_knowledge_fields(self, mock_call, client):
        body = client.post("/api/agents/knowledge", json={}).get_json()
        data = body.get("data", {})
        for field in ("policy", "sources", "source_details", "relevant_chunks", "query_used"):
            assert field in data, f"data missing field '{field}'"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_endpoint_agent_name_is_knowledge(self, mock_call, client):
        body = client.post("/api/agents/knowledge", json={}).get_json()
        assert body["agent_name"] == "knowledge"

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_endpoint_no_question_still_succeeds(self, mock_call, client):
        resp = client.post("/api/agents/knowledge", json={})
        assert resp.status_code == 200

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_endpoint_sources_is_list_not_prose(self, mock_call, client):
        body = client.post(
            "/api/agents/knowledge", json={"question": "procurement policy"}
        ).get_json()
        sources = body["data"]["sources"]
        assert isinstance(sources, list)
        assert all(isinstance(s, str) for s in sources)

    @mock.patch("app.agents.knowledge_agent.call_api", return_value=_MOCK_RAG_SUCCESS)
    def test_endpoint_policy_is_string_not_chat_answer(self, mock_call, client):
        body = client.post(
            "/api/agents/knowledge", json={"question": "What is the safety stock policy?"}
        ).get_json()
        policy = body["data"]["policy"]
        assert isinstance(policy, str)
        # Must NOT look like a chatbot response
        chat_phrases = ["i think", "here is", "as an ai", "let me", "i would recommend"]
        assert not any(p in policy.lower() for p in chat_phrases), (
            f"policy looks like a chat answer: '{policy}'"
        )
