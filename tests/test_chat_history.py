"""
tests/test_chat_history.py
----------------------------
Sprint 4 Step 6 — Chat History Table, Persistence & GET /api/chat/history

Tests:
  - Database schema & persistence: save_chat_turn, get_chat_history
  - Chat service integration: chat() records turns into chat_history
  - REST endpoint: GET /api/chat/history with pagination, ordering, user filters
"""

from __future__ import annotations

import importlib.util
import io
import math
import os
import sys
import uuid

import pytest

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_db_connection, init_db

# --------------------------------------------------------------------------- #
# Flask app factory
# --------------------------------------------------------------------------- #
_SPEC = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


class MockChatProvider:
    """Mock LLM provider returning a deterministic response."""

    def __init__(self, answer: str = "Mock answer for history testing.") -> None:
        self.answer = answer

    def complete(self, system_prompt: str, user_message: str) -> str:
        return self.answer


class MockEmbeddingProvider:
    """Mock embedding provider."""

    def embed(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0, 0.0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]


@pytest.fixture(scope="module", autouse=True)
def ensure_db():
    init_db()


@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_chat_history():
    """Clean up chat history rows created by tests."""
    yield
    conn = get_db_connection()
    conn.execute("DELETE FROM chat_history WHERE user LIKE '__test_%'")
    conn.commit()
    conn.close()


# ============================================================================ #
# 1. Database Persistence Layer
# ============================================================================ #

class TestChatHistoryDB:

    def test_save_chat_turn_inserts_row(self):
        from app.rag.chat_history import save_chat_turn

        q = "What is the policy?"
        a = "The policy requires X."
        srcs = [{"document": "Policy.pdf", "page": 2}]
        user = "__test_user_1__"

        chat_id = save_chat_turn(question=q, answer=a, sources=srcs, user=user)
        assert chat_id is not None
        assert len(chat_id) > 10

        conn = get_db_connection()
        row = conn.execute(
            "SELECT * FROM chat_history WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["user"] == user
        assert row["question"] == q
        assert row["answer"] == a
        assert '"Policy.pdf"' in row["retrieved_documents"]

    def test_get_chat_history_returns_paginated_data(self):
        from app.rag.chat_history import save_chat_turn, get_chat_history

        user = "__test_user_pag__"
        for i in range(5):
            save_chat_turn(
                question=f"Q{i}",
                answer=f"A{i}",
                sources=[{"document": f"Doc{i}.pdf", "page": i + 1}],
                user=user,
            )

        res = get_chat_history(page=1, limit=3, user=user)
        assert res["total"] == 5
        assert res["page"] == 1
        assert res["limit"] == 3
        assert res["pages"] == 2
        assert len(res["history"]) == 3
        # Ensure retrieved_documents is parsed as list of dicts
        assert isinstance(res["history"][0]["retrieved_documents"], list)

        # Page 2
        res2 = get_chat_history(page=2, limit=3, user=user)
        assert len(res2["history"]) == 2

    def test_get_chat_history_ordered_descending(self):
        from app.rag.chat_history import save_chat_turn, get_chat_history

        user = "__test_user_order__"
        id1 = save_chat_turn(question="First question", answer="First ans", sources=[], user=user)
        id2 = save_chat_turn(question="Second question", answer="Second ans", sources=[], user=user)

        res = get_chat_history(page=1, limit=10, user=user)
        history = res["history"]
        assert len(history) >= 2
        # Most recent turn should be first
        assert history[0]["chat_id"] == id2
        assert history[1]["chat_id"] == id1


# ============================================================================ #
# 2. Chat Service Integration
# ============================================================================ #

class TestChatServicePersistence:

    def test_chat_call_persists_turn(self):
        from app.rag import embeddings as emb_mod
        from app.rag import chat_service as chat_mod
        from unittest.mock import patch

        emb_mod.set_provider(MockEmbeddingProvider())
        chat_mod.set_chat_provider(MockChatProvider("Grounded test answer."))

        user = "__test_service_user__"
        with patch("app.rag.chat_service.retrieve") as mock_ret:
            mock_ret.return_value = [
                {"chunk_text": "Sample chunk", "source_document": "Manual.pdf", "page_number": 1, "score": 0.9}
            ]
            res = chat_mod.chat("How to operate machine?", user=user)

            assert "chat_id" in res
            assert res["answer"] == "Grounded test answer."

            # Verify persisted in database
            conn = get_db_connection()
            row = conn.execute(
                "SELECT * FROM chat_history WHERE chat_id = ?",
                (res["chat_id"],),
            ).fetchone()
            conn.close()

            assert row is not None
            assert row["user"] == user
            assert row["question"] == "How to operate machine?"
            assert row["answer"] == "Grounded test answer."


# ============================================================================ #
# 3. GET /api/chat/history Endpoint
# ============================================================================ #

class TestChatHistoryEndpoint:

    def test_get_history_empty_returns_200(self, flask_client):
        resp = flask_client.get("/api/chat/history?user=__test_nonexistent__")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["total"] == 0
        assert data["history"] == []

    def test_get_history_returns_populated_list(self, flask_client):
        from app.rag.chat_history import save_chat_turn

        user = "__test_api_user__"
        save_chat_turn(question="Q1", answer="A1", sources=[{"document": "Doc1.pdf", "page": 1}], user=user)
        save_chat_turn(question="Q2", answer="A2", sources=[{"document": "Doc2.pdf", "page": 2}], user=user)

        resp = flask_client.get(f"/api/chat/history?user={user}&page=1&limit=10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["total"] == 2
        assert len(data["history"]) == 2
        assert data["history"][0]["question"] == "Q2"
        assert data["history"][0]["retrieved_documents"] == [{"document": "Doc2.pdf", "page": 2}]

    def test_post_chat_then_get_history(self, flask_client):
        from app.rag import embeddings as emb_mod
        from app.rag import chat_service as chat_mod
        from unittest.mock import patch

        emb_mod.set_provider(MockEmbeddingProvider())
        chat_mod.set_chat_provider(MockChatProvider("Answer from API chat."))

        user = "__test_post_get_user__"
        with patch("app.rag.chat_service.retrieve") as mock_ret:
            mock_ret.return_value = [
                {"chunk_text": "Chunk info", "source_document": "Policy_Doc.pdf", "page_number": 4, "score": 0.88}
            ]
            post_resp = flask_client.post(
                "/api/chat",
                json={"question": "What is the safety rule?", "user": user},
            )
            assert post_resp.status_code == 200
            post_data = post_resp.get_json()
            assert "chat_id" in post_data

            # Query history
            hist_resp = flask_client.get(f"/api/chat/history?user={user}")
            assert hist_resp.status_code == 200
            hist_data = hist_resp.get_json()
            assert hist_data["total"] >= 1
            entry = hist_data["history"][0]
            assert entry["chat_id"] == post_data["chat_id"]
            assert entry["question"] == "What is the safety rule?"
            assert entry["answer"] == "Answer from API chat."
            assert entry["retrieved_documents"] == [{"document": "Policy_Doc.pdf", "page": 4}]
