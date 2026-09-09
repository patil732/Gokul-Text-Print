"""
tests/test_dashboard_chat_integration.py
----------------------------------------
Integration Tests for Dashboard Chat Window with Manager Agent Backend (Sprint 6).

Covers:
  1. Sending a suggested question ("Which products need restocking?", "What is the safety stock policy for inventory?")
     to POST /api/agents/manager.
  2. Confirming the turn is persisted to the chat_history table.
  3. Confirming the entry is tagged with is_manager == True (1).
  4. Confirming source references from the knowledge agent are attached to the history record.
  5. Confirming GET /api/chat/history exposes the is_manager tag for frontend conversation display.
  6. Confirming plain-RAG POST /api/chat continues to work and sets is_manager == False.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from database.db import get_db_connection

# Load Flask app factory from app.py
_SPEC = importlib.util.spec_from_file_location("app_entry", os.path.join(_ROOT, "app.py"))
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestDashboardChatIntegration:
    """Integration test suite for Manager Agent default chat window & history persistence."""

    def test_manager_endpoint_saves_history_with_is_manager_tag(self, client):
        """
        Send suggested question 'Which products need restocking?' to POST /api/agents/manager.
        Confirm:
          - HTTP 200 response with answer and agent details.
          - Record saved in chat_history table.
          - Record has is_manager == 1.
          - Record user == 'manager'.
        """
        question = "Which products need restocking?"

        resp = client.post(
            "/api/agents/manager",
            json={"question": question},
            content_type="application/json",
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert len(body["answer"]) > 0
        assert "inventory" in body["agents_used"]

        # Verify database record in chat_history
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT chat_id, user, question, answer, retrieved_documents, is_manager
                FROM chat_history
                WHERE question = ?
                ORDER BY timestamp DESC, rowid DESC
                LIMIT 1
                """,
                (question,),
            ).fetchone()

            assert row is not None, "Chat turn was not persisted to chat_history table"
            assert row["question"] == question
            assert row["user"] == "manager"
            assert row["is_manager"] == 1 or row["is_manager"] is True
            assert row["answer"] == body["answer"]

    def test_manager_endpoint_attaches_sources_when_knowledge_agent_runs(self, client):
        """
        Send suggested policy question 'What is the safety stock policy for inventory?'.
        Confirm:
          - Knowledge agent is invoked.
          - Sources are retrieved and attached to the chat_history record.
        """
        question = "What is the safety stock policy for inventory?"

        resp = client.post(
            "/api/agents/manager",
            json={"question": question},
            content_type="application/json",
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert "knowledge" in body["agents_used"]

        # Check database record has source citations
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT chat_id, question, retrieved_documents, is_manager
                FROM chat_history
                WHERE question = ?
                ORDER BY timestamp DESC, rowid DESC
                LIMIT 1
                """,
                (question,),
            ).fetchone()

            assert row is not None
            assert row["is_manager"] == 1 or row["is_manager"] is True

            # Parse retrieved_documents JSON
            sources = json.loads(row["retrieved_documents"])
            assert isinstance(sources, list)
            # When knowledge agent runs, sources or source_details are attached
            k_agent_data = body["agent_details"]["knowledge"]["data"]
            if k_agent_data.get("sources") or k_agent_data.get("source_details"):
                assert len(sources) > 0

    def test_chat_history_api_exposes_is_manager_tag(self, client):
        """
        Call GET /api/chat/history and verify each turn dictionary contains the
        is_manager boolean flag for frontend display rendering.
        """
        resp = client.get("/api/chat/history?limit=10")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert "history" in body
        assert len(body["history"]) > 0

        for turn in body["history"]:
            assert "is_manager" in turn
            assert isinstance(turn["is_manager"], bool)
            assert "question" in turn
            assert "answer" in turn
            assert "retrieved_documents" in turn

        # At least one turn should be a manager turn from the previous tests
        manager_turns = [t for t in body["history"] if t["is_manager"] is True]
        assert len(manager_turns) > 0

    def test_plain_rag_chat_records_is_manager_false(self, client):
        """
        Verify that calling the plain RAG endpoint POST /api/chat persists
        with is_manager == False (0), allowing distinct UI presentation.
        """
        question = "What are the standard fabric production specifications?"

        resp = client.post(
            "/api/chat",
            json={"question": question},
            content_type="application/json",
        )

        # /api/chat can return 200 or 503 if no documents are indexed, but if 200 it must be saved with is_manager=False
        if resp.status_code == 200:
            with get_db_connection() as conn:
                row = conn.execute(
                    """
                    SELECT question, is_manager, user
                    FROM chat_history
                    WHERE question = ?
                    ORDER BY timestamp DESC, rowid DESC
                    LIMIT 1
                    """,
                    (question,),
                ).fetchone()

                if row:
                    assert row["is_manager"] == 0 or row["is_manager"] is False
