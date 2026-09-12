"""
tests/test_sprint4_e2e_integration.py
-------------------------------------
Sprint 4 — End-to-End RAG Knowledge Engine Integration Test Suite

Covers the full knowledge pipeline from end to end:
  1. PDF Upload (POST /api/documents/upload)
  2. PDF Extraction & Token Chunking (app/rag/loader.py, app/rag/chunker.py)
  3. Embedding Generation & Deduplication (app/rag/embeddings.py, chunk_embeddings table)
  4. FAISS Vector Store Indexing (app/rag/vector_store.py)
  5. Top-K Semantic Search (POST /api/rag/search -> app/rag/retriever.py)
  6. Context-Grounded AI Chat with Source Citations (POST /api/chat -> app/rag/chat_service.py)
  7. Chat History Persistence & Pagination (GET /api/chat/history -> app/rag/chat_history.py)
  8. Document Deletion & Lifecycle Management (DELETE /api/documents/{id})
"""

from __future__ import annotations

import io
import json
import os
import sys
import uuid
import pytest
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.db import get_db_connection, init_db
import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(_PROJECT_ROOT, "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app

from app.rag import embeddings as emb_mod
from app.rag import chat_service as chat_mod
from app.rag.vector_store import _CACHE, invalidate_index
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

_DIM = 384


# --------------------------------------------------------------------------- #
# Synthetic PDF generator
# --------------------------------------------------------------------------- #

def _create_synthetic_pdf(text_lines: list[str]) -> bytes:
    """Generate a genuine valid PDF with extractable text."""
    writer = PdfWriter()
    page   = writer.add_blank_page(width=612, height=792)

    stream_content = "BT\n/F1 12 Tf\n50 750 Td\n"
    for line in text_lines:
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({safe_line}) Tj\nT*\n"
    stream_content += "ET"

    content_bytes = stream_content.encode("latin-1")
    stream = DecodedStreamObject()
    stream.set_data(content_bytes)
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
# Test doubles
# --------------------------------------------------------------------------- #

class MockE2EEmbeddingProvider:
    """Deterministic 384-dimensional embedding provider for E2E tests."""

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * _DIM
        val = (len(text) % 100) / 100.0 + 0.1
        vec[0] = val
        vec[1] = 1.0 - val
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class MockE2EChatProvider:
    """Mock grounded chat provider returning answer with verified context."""

    def __init__(self, answer: str = "According to Section 4.2 of the Cutting Machine SOP, always wear protective eyewear and engage the safety guard before power-on.") -> None:
        self.answer = answer

    def complete(self, system_prompt: str, user_message: str) -> str:
        return self.answer


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def setup_mocks_and_cleanup():
    emb_mod.set_provider(MockE2EEmbeddingProvider())
    chat_mod.set_chat_provider(MockE2EChatProvider())
    invalidate_index()

    from app.documents.storage_service import delete_file

    def _clean():
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT document_id, file_path FROM documents WHERE uploaded_by = '__e2e_test__'"
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
        conn.execute("DELETE FROM documents WHERE uploaded_by = '__e2e_test__'")
        conn.execute("DELETE FROM chat_history WHERE user = '__e2e_user__'")
        conn.commit()
        conn.close()
        for r in rows:
            delete_file(r["file_path"])

    _clean()
    yield
    _clean()
    emb_mod.reset_provider()
    chat_mod.reset_chat_provider()
    invalidate_index()


# --------------------------------------------------------------------------- #
# End-to-End Test Case
# --------------------------------------------------------------------------- #

class TestSprint4EndToEndPipeline:
    """
    Complete end-to-end integration test validating the entire Sprint 4 RAG workflow.
    """

    def test_full_rag_knowledge_lifecycle(self, flask_client, tmp_path, monkeypatch):
        # Point document storage to test tmp_path
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        doc_name = f"Gokul_Cutting_SOP_{uuid.uuid4().hex[:6]}.pdf"
        pdf_bytes = _create_synthetic_pdf([
            "GOKUL TEX PRINT - STANDARD OPERATING PROCEDURE",
            "DOCUMENT: Cutting Machine Operation & Safety SOP",
            "SECTION 4.2: Machine Startup Procedures and Safety Interlocks",
            "1. Operators must verify the hydraulic pressure reaches 120 PSI before cycling.",
            "2. Always ensure the protective laser guard is unobstructed and active.",
            "3. Emergency stop button must be tested at the beginning of each 8-hour shift.",
            "4. For fabric thickness exceeding 15mm, adjust blade feed rate to 45 mm/sec.",
        ])

        # ------------------------------------------------------------------- #
        # Step 1: Upload PDF -> Automatic Extraction, Chunking & Embeddings
        # ------------------------------------------------------------------- #
        upload_data = {
            "file": (io.BytesIO(pdf_bytes), doc_name),
            "uploaded_by": "__e2e_test__",
        }
        upload_resp = flask_client.post(
            "/api/documents/upload",
            data=upload_data,
            content_type="multipart/form-data",
        )
        assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.get_json()}"
        upload_json = upload_resp.get_json()
        assert upload_json["status"] == "success"
        doc_record = upload_json["document"]
        doc_id = doc_record["document_id"]
        assert doc_record["status"] == "processed"
        assert doc_record["chunk_count"] >= 1

        # ------------------------------------------------------------------- #
        # Step 2: Verify Metadata, Chunks, and Embeddings in DB
        # ------------------------------------------------------------------- #
        conn = get_db_connection()
        db_doc = conn.execute(
            "SELECT * FROM documents WHERE document_id = ?", (doc_id,)
        ).fetchone()
        assert db_doc is not None
        assert db_doc["document_name"] == doc_name
        assert db_doc["status"] == "processed"

        db_chunks = conn.execute(
            "SELECT * FROM document_chunks WHERE document_id = ?", (doc_id,)
        ).fetchall()
        assert len(db_chunks) >= 1
        assert "SECTION 4.2" in db_chunks[0]["chunk_text"]

        chunk_id = db_chunks[0]["chunk_id"]
        db_emb = conn.execute(
            "SELECT * FROM chunk_embeddings WHERE chunk_id = ?", (chunk_id,)
        ).fetchone()
        assert db_emb is not None
        emb_vector = json.loads(db_emb["embedding"])
        assert len(emb_vector) == _DIM
        conn.close()

        # ------------------------------------------------------------------- #
        # Step 3: Semantic Search Endpoint (/api/rag/search)
        # ------------------------------------------------------------------- #
        search_resp = flask_client.post(
            "/api/rag/search",
            json={"query": "What is the required hydraulic pressure for the cutting machine?", "top_k": 3},
        )
        assert search_resp.status_code == 200
        search_json = search_resp.get_json()
        assert search_json["status"] == "success"
        assert len(search_json["chunks"]) >= 1
        assert doc_name in search_json["sources"]
        assert search_json["elapsed_ms"] >= 0

        first_match = search_json["chunks"][0]
        assert first_match["source_document"] == doc_name
        assert first_match["page_number"] == 1
        assert isinstance(first_match["score"], float)

        # ------------------------------------------------------------------- #
        # Step 4: AI Chat Endpoint (/api/chat) Grounded with Source Citations
        # ------------------------------------------------------------------- #
        question_text = "What is the procedure before cycling the cutting machine?"
        chat_resp = flask_client.post(
            "/api/chat",
            json={"question": question_text, "user": "__e2e_user__"},
        )
        assert chat_resp.status_code == 200
        chat_json = chat_resp.get_json()
        assert chat_json["status"] == "success"
        assert "Section 4.2" in chat_json["answer"]
        assert len(chat_json["sources"]) >= 1

        source_citation = chat_json["sources"][0]
        assert source_citation["document"] == doc_name
        assert source_citation["page"] == 1

        # ------------------------------------------------------------------- #
        # Step 5: Chat History Persistence & Retrieval (/api/chat/history)
        # ------------------------------------------------------------------- #
        hist_resp = flask_client.post("/api/chat", json={"question": "What is the blade feed rate for 15mm?", "user": "__e2e_user__"})
        assert hist_resp.status_code == 200

        history_resp = flask_client.get("/api/chat/history?user=__e2e_user__&page=1&limit=10")
        assert history_resp.status_code == 200
        hist_json = history_resp.get_json()
        assert hist_json["status"] == "success"
        assert hist_json["total"] >= 2
        assert len(hist_json["history"]) >= 2

        latest_turn = hist_json["history"][0]
        assert latest_turn["user"] == "__e2e_user__"
        assert "feed rate" in latest_turn["question"]
        assert latest_turn["retrieved_documents"][0]["document"] == doc_name

        # ------------------------------------------------------------------- #
        # Step 6: Delete Document Endpoint (/api/documents/{id})
        # ------------------------------------------------------------------- #
        del_resp = flask_client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200
        assert del_resp.get_json()["status"] == "success"

        # Verify soft deletion in DB
        conn = get_db_connection()
        del_doc = conn.execute(
            "SELECT status FROM documents WHERE document_id = ?", (doc_id,)
        ).fetchone()
        assert del_doc["status"] == "deleted"
        conn.close()
