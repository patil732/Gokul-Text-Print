"""
tests/test_chat_service.py
----------------------------
Sprint 4 Step 5 — RAG Chat Service & Single-Turn Q&A Endpoint

Tests the full RAG chat flow:
  question -> retriever -> prompt_builder -> LLM -> {answer, sources}

All LLM calls are mocked using MockChatProvider and MockEmbeddingProvider.
Zero external API calls are made.

Test classes
------------
1. TestPromptBuilder   — build_prompt() formatting, extract_sources() deduplication
2. TestChatProvider    — Gemini/OpenAI provider wrappers, missing keys, unknown provider
3. TestChatService     — chat() flow, empty index fallback, LLM failure exception
4. TestChatEndpoint    — POST /api/chat contract (200, 400, 503)
5. TestEndToEndChat    — Upload SOP PDF -> wait for processing -> chat -> verify source citations
"""

from __future__ import annotations

import importlib.util
import io
import math
import os
import sys
import uuid
from unittest.mock import MagicMock, patch

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


# --------------------------------------------------------------------------- #
# Test doubles & helpers
# --------------------------------------------------------------------------- #

_DIM = 384



def _unit_vec(seed: int = 0) -> list[float]:
    v = [float(i + seed + 1) for i in range(_DIM)]
    norm = math.sqrt(sum(x ** 2 for x in v))
    return [x / norm for x in v]


class MockEmbeddingProvider:
    """Mock embedding provider returning deterministic unit vectors."""

    def embed(self, text: str) -> list[float]:
        return _unit_vec(0)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_unit_vec(i) for i in range(len(texts))]


class MockChatProvider:
    """Mock LLM provider returning a canned context-grounded response."""

    def __init__(self, canned_answer: str = "According to the SOP, operators must wear safety goggles.") -> None:
        self.canned_answer = canned_answer
        self.last_system_prompt = ""
        self.last_user_message = ""

    def complete(self, system_prompt: str, user_message: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_message = user_message
        return self.canned_answer


def _make_pdf(page_texts: list[str]) -> bytes:
    """Build a valid PDF via pypdf."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    for text in page_texts:
        page = writer.add_blank_page(width=595, height=842)
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content = f"BT /F1 12 Tf 50 750 Td ({safe}) Tj ET".encode()
        stream = DecodedStreamObject()
        stream.set_data(content)
        page[NameObject("/Contents")] = writer._add_object(stream)
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({
                NameObject("/F1"): writer._add_object(font)
            })
        })
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

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
def reset_providers_and_cache():
    from app.rag import embeddings as emb_mod
    from app.rag import chat_service as chat_mod
    from app.rag.vector_store import _CACHE

    emb_mod.reset_provider()
    chat_mod.reset_chat_provider()
    _CACHE.invalidate()
    yield
    emb_mod.reset_provider()
    chat_mod.reset_chat_provider()
    _CACHE.invalidate()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    from app.documents.storage_service import delete_file
    def _clean():
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT document_id, file_path FROM documents WHERE uploaded_by = '__test__'"
        ).fetchall()
        doc_ids = [r["document_id"] for r in rows]
        if doc_ids:
            ph = ",".join("?" * len(doc_ids))
            c_rows = conn.execute(
                f"SELECT chunk_id FROM document_chunks WHERE document_id IN ({ph})", doc_ids
            ).fetchall()
            cids = [c["chunk_id"] for c in c_rows]
            if cids:
                cph = ",".join("?" * len(cids))
                conn.execute(f"DELETE FROM chunk_embeddings WHERE chunk_id IN ({cph})", cids)
            conn.execute(f"DELETE FROM document_chunks WHERE document_id IN ({ph})", doc_ids)
        conn.execute("DELETE FROM documents WHERE uploaded_by = '__test__'")
        conn.commit()
        conn.close()
        for r in rows:
            delete_file(r["file_path"])

    _clean()
    yield
    _clean()



# ============================================================================ #
# 1. Prompt Builder
# ============================================================================ #

class TestPromptBuilder:

    def test_build_prompt_returns_tuple_of_strings(self):
        from app.rag.prompt_builder import build_prompt
        chunks = [
            {"chunk_text": "Sample text chunk", "source_document": "Policy.pdf", "page_number": 1}
        ]
        sys_p, user_p = build_prompt("What is the policy?", chunks)
        assert isinstance(sys_p, str)
        assert isinstance(user_p, str)

    def test_system_prompt_contains_grounding_rules(self):
        from app.rag.prompt_builder import build_prompt
        sys_p, _ = build_prompt("Question", [])
        assert "exclusively on the provided context" in sys_p
        assert "Source:" in sys_p

    def test_user_message_formats_numbered_chunks(self):
        from app.rag.prompt_builder import build_prompt
        chunks = [
            {"chunk_text": "First excerpt text", "source_document": "DocA.pdf", "page_number": 2},
            {"chunk_text": "Second excerpt text", "source_document": "DocB.pdf", "page_number": 5},
        ]
        _, user_p = build_prompt("How to operate machine?", chunks)
        assert "[1] Source: DocA.pdf, p.2" in user_p
        assert "First excerpt text" in user_p
        assert "[2] Source: DocB.pdf, p.5" in user_p
        assert "Second excerpt text" in user_p
        assert "Question: How to operate machine?" in user_p

    def test_build_prompt_handles_empty_chunks_gracefully(self):
        from app.rag.prompt_builder import build_prompt
        sys_p, user_p = build_prompt("Where is the file?", [])
        assert "Question: Where is the file?" in user_p
        assert "No context excerpts available" in user_p

    def test_extract_sources_deduplicates_by_doc_and_page(self):
        from app.rag.prompt_builder import extract_sources
        chunks = [
            {"source_document": "SOP.pdf", "page_number": 1},
            {"source_document": "SOP.pdf", "page_number": 1},  # duplicate
            {"source_document": "SOP.pdf", "page_number": 2},
            {"source_document": "Manual.pdf", "page_number": 1},
        ]
        sources = extract_sources(chunks)
        assert len(sources) == 3
        assert sources[0] == {"document": "SOP.pdf", "page": 1}
        assert sources[1] == {"document": "SOP.pdf", "page": 2}
        assert sources[2] == {"document": "Manual.pdf", "page": 1}


# ============================================================================ #
# 2. Chat Provider
# ============================================================================ #

class TestChatProvider:

    def test_gemini_provider_wrapper(self):
        from app.rag.chat_service import GeminiChatProvider, ChatConfig

        cfg = ChatConfig(provider="gemini", model="gemini-1.5-flash", api_key="fake-gemini-key")
        mock_response = MagicMock(text="Gemini generated response")
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel", return_value=mock_model):
            provider = GeminiChatProvider(cfg)
            res = provider.complete("System prompt", "User message")
            assert res == "Gemini generated response"

    def test_openai_provider_wrapper(self):
        from app.rag.chat_service import OpenAIChatProvider, ChatConfig

        cfg = ChatConfig(provider="openai", model="gpt-4o-mini", api_key="fake-openai-key")
        mock_choice = MagicMock()
        mock_choice.message.content = "OpenAI generated response"
        mock_completion = MagicMock(choices=[mock_choice])

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        with patch("openai.OpenAI", return_value=mock_client):
            provider = OpenAIChatProvider(cfg)
            res = provider.complete("System prompt", "User message")
            assert res == "OpenAI generated response"

    def test_missing_api_keys_raise_value_error(self):
        from app.rag.chat_service import GeminiChatProvider, OpenAIChatProvider, ChatConfig

        with pytest.raises(ValueError, match="API key"):
            GeminiChatProvider(ChatConfig(provider="gemini", api_key=""))

        with pytest.raises(ValueError, match="API key"):
            OpenAIChatProvider(ChatConfig(provider="openai", api_key=""))

    def test_unknown_provider_raises_value_error(self):
        from app.rag.chat_service import get_chat_provider, ChatConfig
        with patch("app.rag.chat_service._resolve_chat_config", return_value=ChatConfig(provider="anthropic")):
            with pytest.raises(ValueError, match="Unknown chat provider"):
                get_chat_provider()


# ============================================================================ #
# 3. Chat Service
# ============================================================================ #

class TestChatService:

    def test_chat_returns_answer_and_sources(self):
        from app.rag import embeddings as emb_mod
        from app.rag import chat_service as chat_mod

        emb_mod.set_provider(MockEmbeddingProvider())
        mock_chat = MockChatProvider("Specific answer text from SOP.")
        chat_mod.set_chat_provider(mock_chat)

        with patch("app.rag.chat_service.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                {"chunk_text": "Section 1 text", "source_document": "Standard_SOP.pdf", "page_number": 3, "score": 0.95}
            ]
            result = chat_mod.chat("What is Section 1?")

            assert result["answer"] == "Specific answer text from SOP."
            assert result["sources"] == [{"document": "Standard_SOP.pdf", "page": 3}]

    def test_chat_empty_index_returns_fallback(self):
        from app.rag import chat_service as chat_mod

        with patch("app.rag.chat_service.retrieve", return_value=[]):
            result = chat_mod.chat("Any question?")
            assert "I don't have enough information" in result["answer"]
            assert result["sources"] == []

    def test_chat_empty_question_raises_value_error(self):
        from app.rag.chat_service import chat
        with pytest.raises(ValueError, match="empty"):
            chat("   ")

    def test_chat_llm_failure_raises_runtime_error(self):
        from app.rag import embeddings as emb_mod
        from app.rag import chat_service as chat_mod

        emb_mod.set_provider(MockEmbeddingProvider())

        class FailingChatProvider:
            def complete(self, sys, user):
                raise ConnectionError("LLM API timeout")

        chat_mod.set_chat_provider(FailingChatProvider())

        with patch("app.rag.chat_service.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                {"chunk_text": "Text", "source_document": "Doc.pdf", "page_number": 1, "score": 0.9}
            ]
            with pytest.raises(RuntimeError, match="LLM provider error"):
                chat_mod.chat("Sample query?")


# ============================================================================ #
# 4. Chat Endpoint
# ============================================================================ #

class TestChatEndpoint:

    def test_post_chat_success(self, flask_client):
        from app.rag import embeddings as emb_mod
        from app.rag import chat_service as chat_mod

        emb_mod.set_provider(MockEmbeddingProvider())
        chat_mod.set_chat_provider(MockChatProvider("Goggles are required."))

        with patch("app.rag.chat_service.retrieve") as mock_retrieve:
            mock_retrieve.return_value = [
                {"chunk_text": "PPE section", "source_document": "Safety_SOP.pdf", "page_number": 2, "score": 0.91}
            ]
            resp = flask_client.post("/api/chat", json={"question": "What PPE is required?"})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["status"] == "success"
            assert data["question"] == "What PPE is required?"
            assert data["answer"] == "Goggles are required."
            assert data["sources"] == [{"document": "Safety_SOP.pdf", "page": 2}]
            assert "elapsed_ms" in data

    def test_post_chat_missing_question_returns_400(self, flask_client):
        resp = flask_client.post("/api/chat", json={})
        assert resp.status_code == 400

    def test_post_chat_empty_question_returns_400(self, flask_client):
        resp = flask_client.post("/api/chat", json={"question": "   "})
        assert resp.status_code == 400

    def test_post_chat_empty_index_returns_503_when_no_embeddings(self, flask_client):
        from app.rag import chat_service as chat_mod
        chat_mod.set_chat_provider(MockChatProvider())

        with patch("app.rag.chat_service.retrieve", return_value=[]), \
             patch("database.db.get_db_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"cnt": 0}
            mock_conn.return_value.execute.return_value = mock_cursor
            resp = flask_client.post("/api/chat", json={"question": "What is the policy?"})
            assert resp.status_code == 503
            assert "No documents have been indexed yet" in resp.get_json()["message"]



# ============================================================================ #
# 5. End-to-End Chat Integration
# ============================================================================ #

class TestEndToEndChat:

    def test_upload_sop_and_chat_cites_source(self, flask_client, tmp_path, monkeypatch):
        """
        Integration test:
        1. Upload sample SOP PDF via /api/documents/upload
        2. Wait for / confirm processing
        3. Query /api/chat
        4. Confirm the answer cites the uploaded document and page number.
        """
        from app.documents import storage_service
        from app.rag import embeddings as emb_mod
        from app.rag import chat_service as chat_mod

        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        emb_mod.set_provider(MockEmbeddingProvider())
        chat_mod.set_chat_provider(MockChatProvider("The cutting machine requires daily blade alignment."))

        # 1. Create and upload a sample SOP PDF
        sop_text = (
            "Standard Operating Procedure for Industrial Cutting Machine. "
            "Operators must calibrate the alignment guide before initiating any batch run. "
            "Emergency stop buttons are located on both sides of the console."
        )
        pdf_bytes = _make_pdf([sop_text])
        filename = f"Cutting_Machine_SOP_{uuid.uuid4().hex[:6]}.pdf"

        upload_resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert upload_resp.status_code == 201
        doc_record = upload_resp.get_json()["document"]
        assert doc_record["status"] == "processed"
        assert doc_record["chunk_count"] >= 1

        # 2. Query the chat endpoint
        chat_resp = flask_client.post(
            "/api/chat",
            json={"question": "What is the procedure for the cutting machine?"},
        )
        assert chat_resp.status_code == 200
        body = chat_resp.get_json()

        assert body["status"] == "success"
        assert body["answer"] == "The cutting machine requires daily blade alignment."
        assert len(body["sources"]) >= 1

        # Confirm the source contains the uploaded document name and valid page number
        source_docs = [s["document"] for s in body["sources"]]
        assert filename in source_docs
        assert all(isinstance(s["page"], int) and s["page"] >= 1 for s in body["sources"])


# ============================================================================ #
# CLI runner
# ============================================================================ #

if __name__ == "__main__":
    import subprocess, sys as _sys
    ret = subprocess.run(
        [_sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    _sys.exit(ret.returncode)
