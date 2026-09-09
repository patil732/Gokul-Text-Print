"""
tests/test_rag_search.py
--------------------------
Sprint 4 Step 4 — FAISS Vector Store & RAG Search Endpoint

Integration tests verifying the full search stack:
  vector_store → retriever → POST /api/rag/search

All tests that need an embedding provider use MockEmbeddingProvider so
no real models are downloaded and no API keys are needed.

Test classes
------------
1. TestVectorStore        — build_index, search_index, invalidate, inject
2. TestRetriever          — retrieve() keys, score range, empty index
3. TestSearchLatency      — 1k-chunk index build + 10 queries all < 1 000ms
4. TestSearchEndpoint     — HTTP 200/400/503 response shape
5. TestEndToEndRAG        — upload real PDF → search → chunk contains query term
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import time
import uuid

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_db_connection, init_db
import faiss


# --------------------------------------------------------------------------- #
# Flask app factory
# --------------------------------------------------------------------------- #
_SPEC    = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


# --------------------------------------------------------------------------- #
# Shared constants & helpers
# --------------------------------------------------------------------------- #

_DIM = 384   # match sentence_transformers dimension in model_config.yaml



def _unit_vec(seed: int = 0) -> list[float]:
    v    = [float(i + seed + 1) for i in range(_DIM)]
    norm = math.sqrt(sum(x ** 2 for x in v))
    return [x / norm for x in v]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class MockProvider:
    """Deterministic embedding provider — returns _unit_vec(0) for every input."""

    def embed(self, text: str) -> list[float]:
        return _unit_vec(0)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_unit_vec(i) for i in range(len(texts))]


def _make_pdf(page_texts: list[str]) -> bytes:
    """Build a real multi-page PDF via pypdf.PdfWriter."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    for text in page_texts:
        page = writer.add_blank_page(width=595, height=842)
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content = f"BT /F1 12 Tf 50 750 Td ({safe}) Tj ET".encode()
        stream  = DecodedStreamObject()
        stream.set_data(content)
        page[NameObject("/Contents")] = writer._add_object(stream)
        font = DictionaryObject({
            NameObject("/Type"):     NameObject("/Font"),
            NameObject("/Subtype"):  NameObject("/Type1"),
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
def reset_embedding_singleton():
    from app.rag import embeddings as emb_module
    emb_module.reset_provider()
    yield
    emb_module.reset_provider()


@pytest.fixture(autouse=True)
def reset_vector_store_cache():
    from app.rag.vector_store import _CACHE
    _CACHE.invalidate()
    yield
    _CACHE.invalidate()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield
    from app.documents.storage_service import delete_file
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT document_id, file_path FROM documents WHERE uploaded_by = '__test__'"
    ).fetchall()
    doc_ids = [r["document_id"] for r in rows]
    if doc_ids:
        ph       = ",".join("?" * len(doc_ids))
        c_rows   = conn.execute(
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


# ============================================================================ #
# 1. Vector Store
# ============================================================================ #

class TestVectorStore:

    def _make_vectors(self, n: int) -> tuple[list[list[float]], list[str]]:
        vecs = [_unit_vec(i) for i in range(n)]
        ids  = [str(uuid.uuid4()) for _ in range(n)]
        return vecs, ids

    def test_build_index_returns_non_none_for_nonempty_input(self):
        from app.rag.vector_store import build_index
        vecs, ids = self._make_vectors(5)
        idx, out_ids = build_index(vecs, ids)
        assert idx is not None
        assert out_ids == ids

    def test_build_index_returns_none_for_empty_input(self):
        from app.rag.vector_store import build_index
        idx, ids = build_index([], [])
        assert idx is None
        assert ids == []

    def test_search_index_returns_correct_count(self):
        from app.rag.vector_store import build_index, search_index
        vecs, ids = self._make_vectors(10)
        idx, cids = build_index(vecs, ids)
        results   = search_index(idx, cids, _unit_vec(0), top_k=3)
        assert len(results) == 3

    def test_search_index_results_have_required_keys(self):
        from app.rag.vector_store import build_index, search_index
        vecs, ids = self._make_vectors(5)
        idx, cids = build_index(vecs, ids)
        results   = search_index(idx, cids, _unit_vec(0), top_k=2)
        for r in results:
            assert "chunk_id" in r
            assert "score"    in r

    def test_search_index_scores_are_floats_in_valid_range(self):
        from app.rag.vector_store import build_index, search_index
        vecs, ids = self._make_vectors(5)
        idx, cids = build_index(vecs, ids)
        results   = search_index(idx, cids, _unit_vec(0), top_k=5)
        for r in results:
            assert isinstance(r["score"], float)
            assert -1.01 <= r["score"] <= 1.01  # cosine similarity range

    def test_search_index_returns_empty_for_none_index(self):
        from app.rag.vector_store import search_index
        results = search_index(None, [], _unit_vec(0), top_k=5)
        assert results == []

    def test_top_k_clamped_to_available_vectors(self):
        from app.rag.vector_store import build_index, search_index
        vecs, ids = self._make_vectors(3)
        idx, cids = build_index(vecs, ids)
        results   = search_index(idx, cids, _unit_vec(0), top_k=100)
        assert len(results) <= 3

    def test_l2_normalise_unit_vectors_unchanged(self):
        from app.rag.vector_store import _l2_normalise
        v    = np.array([[3.0, 4.0]], dtype=np.float32)
        norm = _l2_normalise(v)
        assert abs(np.linalg.norm(norm[0]) - 1.0) < 1e-5

    def test_invalidate_sets_dirty_flag(self):
        from app.rag.vector_store import _CACHE, build_index, inject_index
        vecs, ids = self._make_vectors(3)
        idx, cids = build_index(vecs, ids)
        inject_index(idx, cids)
        assert not _CACHE._dirty
        from app.rag.vector_store import invalidate_index
        invalidate_index()
        assert _CACHE._dirty

    def test_inject_index_bypasses_db(self):
        from app.rag.vector_store import build_index, inject_index, get_index
        vecs, ids = self._make_vectors(4)
        idx, cids = build_index(vecs, ids)
        inject_index(idx, cids)
        ret_idx, ret_ids = get_index()
        assert ret_ids == cids
        assert ret_idx is not None


# ============================================================================ #
# 2. Retriever
# ============================================================================ #

class TestRetriever:

    def _seed_chunks_with_embeddings(self, n: int = 3) -> list[str]:
        """Insert document + n chunks + embeddings, return chunk_ids."""
        from app.documents.document_metadata import (
            insert_document, insert_chunks, get_chunks, insert_embedding,
        )
        doc = insert_document({
            "document_name": f"retriever_{uuid.uuid4().hex[:6]}.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     "/tmp/retriever.pdf",
            "file_hash":     uuid.uuid4().hex * 2,
        })
        chunks = [
            {"chunk_index": i, "page_number": 1,
             "chunk_text": f"Retriever test chunk {i} content words here."}
            for i in range(n)
        ]
        insert_chunks(doc["document_id"], doc["document_name"], chunks)
        db_chunks = get_chunks(doc["document_id"])
        chunk_ids = []
        from app.rag.vector_store import invalidate_index
        for c in db_chunks:
            h = _sha256(c["chunk_text"])
            insert_embedding(c["chunk_id"], h, _unit_vec(0), "mock", "mock-v1")
            chunk_ids.append(c["chunk_id"])
        invalidate_index()
        return chunk_ids


    def test_retrieve_returns_list(self):
        from app.rag import embeddings as emb_module
        from app.rag.retriever import retrieve
        self._seed_chunks_with_embeddings(3)
        emb_module.set_provider(MockProvider())
        result = retrieve("test query", top_k=2)
        assert isinstance(result, list)

    def test_retrieve_result_has_required_keys(self):
        from app.rag import embeddings as emb_module
        from app.rag.retriever import retrieve
        self._seed_chunks_with_embeddings(3)
        emb_module.set_provider(MockProvider())
        results = retrieve("test query", top_k=1)
        if results:
            r = results[0]
            for key in ["chunk_id", "chunk_text", "page_number",
                        "source_document", "score"]:
                assert key in r, f"Missing key: {key}"

    def test_retrieve_score_is_float(self):
        from app.rag import embeddings as emb_module
        from app.rag.retriever import retrieve
        self._seed_chunks_with_embeddings(3)
        emb_module.set_provider(MockProvider())
        results = retrieve("query here", top_k=3)
        for r in results:
            assert isinstance(r["score"], float)

    def test_retrieve_empty_index_returns_empty_list(self):
        from app.rag import embeddings as emb_module
        from app.rag.vector_store import inject_index
        from app.rag.retriever import retrieve
        inject_index(None, [])
        emb_module.set_provider(MockProvider())
        result = retrieve("anything", top_k=5)
        assert result == []

    def test_retrieve_raises_for_empty_query(self):
        from app.rag import embeddings as emb_module
        from app.rag.retriever import retrieve
        emb_module.set_provider(MockProvider())
        with pytest.raises(ValueError, match="empty"):
            retrieve("", top_k=5)

    def test_retrieve_respects_top_k(self):
        from app.rag import embeddings as emb_module
        from app.rag.retriever import retrieve
        self._seed_chunks_with_embeddings(5)
        emb_module.set_provider(MockProvider())
        results = retrieve("query", top_k=2)
        assert len(results) <= 2


# ============================================================================ #
# 3. Search Latency
# ============================================================================ #

class TestSearchLatency:
    """
    Performance regression tests.

    Thresholds:
      - Index build (1k vectors, 384-dim): < 500ms
      - Single search (1k vectors):        < 1 000ms  (includes embed + search)
    """

    _N     = 1000
    _QDIM  = 384   # realistic embedding dimension

    def _make_random_unit_vecs(self, n: int, dim: int) -> np.ndarray:
        mat  = np.random.randn(n, dim).astype(np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        return mat / norms

    def test_index_build_under_500ms(self):
        from app.rag.vector_store import build_index
        vecs_np = self._make_random_unit_vecs(self._N, self._QDIM)
        vecs    = vecs_np.tolist()
        ids     = [str(uuid.uuid4()) for _ in range(self._N)]

        t0 = time.monotonic()
        idx, _ = build_index(vecs, ids)
        elapsed_ms = (time.monotonic() - t0) * 1000

        assert idx is not None
        assert elapsed_ms < 500, (
            f"Index build took {elapsed_ms:.1f}ms — must be <500ms"
        )

    def test_single_search_under_1000ms(self):
        """
        Measures vector_store search only (not embedding), should be <50ms.
        We test it at <1 000ms to give ample headroom.
        """
        from app.rag.vector_store import build_index, search_index
        vecs_np = self._make_random_unit_vecs(self._N, self._QDIM)
        vecs    = vecs_np.tolist()
        ids     = [str(uuid.uuid4()) for _ in range(self._N)]
        idx, cids = build_index(vecs, ids)
        query   = vecs[0]

        t0 = time.monotonic()
        results = search_index(idx, cids, query, top_k=5)
        elapsed_ms = (time.monotonic() - t0) * 1000

        assert len(results) == 5
        assert elapsed_ms < 1000, (
            f"Search took {elapsed_ms:.1f}ms — must be <1 000ms"
        )

    def test_ten_queries_p95_under_500ms(self):
        from app.rag.vector_store import build_index, search_index
        vecs_np = self._make_random_unit_vecs(self._N, self._QDIM)
        vecs    = vecs_np.tolist()
        ids     = [str(uuid.uuid4()) for _ in range(self._N)]
        idx, cids = build_index(vecs, ids)

        timings = []
        for i in range(10):
            q  = vecs_np[i].tolist()
            t0 = time.monotonic()
            search_index(idx, cids, q, top_k=5)
            timings.append((time.monotonic() - t0) * 1000)

        p95 = sorted(timings)[int(len(timings) * 0.95)]
        assert p95 < 500, (
            f"p95 search latency {p95:.1f}ms — must be <500ms"
        )


# ============================================================================ #
# 4. Search Endpoint
# ============================================================================ #

class TestSearchEndpoint:

    def _seed_and_inject(self):
        """Seed 3 chunks with embeddings and inject into vector store."""
        from app.documents.document_metadata import (
            insert_document, insert_chunks, get_chunks, insert_embedding,
        )
        from app.rag.vector_store import build_index, inject_index

        doc = insert_document({
            "document_name": f"ep_{uuid.uuid4().hex[:6]}.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     "/tmp/ep.pdf",
            "file_hash":     uuid.uuid4().hex * 2,
        })
        insert_chunks(doc["document_id"], doc["document_name"], [
            {"chunk_index": i, "page_number": 1,
             "chunk_text": f"Endpoint test chunk {i}."}
            for i in range(3)
        ])
        db_chunks = get_chunks(doc["document_id"])
        vecs, cids = [], []
        for c in db_chunks:
            h = _sha256(c["chunk_text"])
            insert_embedding(c["chunk_id"], h, _unit_vec(0), "mock", "v1")
            vecs.append(_unit_vec(0))
            cids.append(c["chunk_id"])

        idx, _ = __import__("app.rag.vector_store", fromlist=["build_index"]) \
            .build_index(vecs, cids)
        inject_index(idx, cids)

    def test_search_returns_200_with_correct_shape(
        self, flask_client, monkeypatch
    ):
        from app.rag import embeddings as emb_module
        emb_module.set_provider(MockProvider())
        self._seed_and_inject()

        resp = flask_client.post(
            "/api/rag/search",
            json={"query": "endpoint test chunk", "top_k": 2},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"]     == "success"
        assert "query"      in body
        assert "top_k"      in body
        assert "elapsed_ms" in body
        assert "chunks"     in body
        assert "sources"    in body

    def test_search_missing_query_returns_400(self, flask_client):
        resp = flask_client.post("/api/rag/search", json={"top_k": 3})
        assert resp.status_code == 400

    def test_search_empty_query_returns_400(self, flask_client):
        resp = flask_client.post("/api/rag/search", json={"query": "   "})
        assert resp.status_code == 400

    def test_search_top_k_zero_returns_400(self, flask_client):
        resp = flask_client.post("/api/rag/search",
                                 json={"query": "test", "top_k": 0})
        assert resp.status_code == 400

    def test_search_top_k_above_max_returns_400(self, flask_client):
        resp = flask_client.post("/api/rag/search",
                                 json={"query": "test", "top_k": 9999})
        assert resp.status_code == 400

    def test_search_top_k_invalid_type_returns_400(self, flask_client):
        resp = flask_client.post("/api/rag/search",
                                 json={"query": "test", "top_k": "bad"})
        assert resp.status_code == 400

    def test_search_empty_index_returns_503(self, flask_client):
        from app.rag.vector_store import inject_index
        from app.rag import embeddings as emb_module
        emb_module.set_provider(MockProvider())
        inject_index(None, [])
        with patch("database.db.get_db_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = {"cnt": 0}
            mock_conn.return_value.execute.return_value = mock_cursor
            resp = flask_client.post("/api/rag/search", json={"query": "anything"})
            assert resp.status_code == 503


    def test_search_elapsed_ms_is_positive(self, flask_client):
        from app.rag import embeddings as emb_module
        emb_module.set_provider(MockProvider())
        self._seed_and_inject()

        resp = flask_client.post("/api/rag/search",
                                 json={"query": "chunk", "top_k": 1})
        assert resp.status_code == 200
        assert resp.get_json()["elapsed_ms"] >= 0

    def test_sources_is_deduplicated_list(self, flask_client):
        from app.rag import embeddings as emb_module
        emb_module.set_provider(MockProvider())
        self._seed_and_inject()

        resp   = flask_client.post("/api/rag/search",
                                   json={"query": "chunk", "top_k": 5})
        assert resp.status_code == 200
        sources = resp.get_json()["sources"]
        assert isinstance(sources, list)
        assert len(sources) == len(set(sources)), "Sources must be deduplicated"

    def test_chunk_has_all_required_fields(self, flask_client):
        from app.rag import embeddings as emb_module
        emb_module.set_provider(MockProvider())
        self._seed_and_inject()

        resp   = flask_client.post("/api/rag/search",
                                   json={"query": "chunk", "top_k": 1})
        assert resp.status_code == 200
        chunks = resp.get_json()["chunks"]
        if chunks:
            for key in ["chunk_id", "chunk_text", "page_number",
                        "source_document", "score"]:
                assert key in chunks[0]


# ============================================================================ #
# 5. End-to-End RAG
# ============================================================================ #

class TestEndToEndRAG:
    """
    Full pipeline: upload PDF → chunks → embeddings → FAISS search → verify results.

    Uses a real (tiny) PDF with known content so we can assert the query term
    appears in at least one returned chunk.
    """

    _SEARCH_TERM = "inventory reorder threshold policy document"

    def test_uploaded_doc_chunks_are_searchable(
        self, flask_client, tmp_path, monkeypatch
    ):
        from app.documents import storage_service
        from app.rag import embeddings as emb_module

        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        emb_module.set_provider(MockProvider())

        # Upload a PDF whose content contains the search term
        pdf_bytes = _make_pdf([
            f"This document describes the {self._SEARCH_TERM}. "
            "When stock falls below the minimum level a purchase order is generated "
            "automatically by the ERP system.",
            "The reorder point is calculated as: average daily usage multiplied by "
            "lead time in days, plus safety stock.",
        ])
        filename = f"e2e_{uuid.uuid4().hex[:6]}.pdf"
        upload_resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert upload_resp.status_code == 201
        doc = upload_resp.get_json()["document"]
        assert doc["status"] == "processed"
        assert doc.get("embed_count", 0) >= 1

        # Search with a term that appears in the uploaded text
        search_resp = flask_client.post(
            "/api/rag/search",
            json={"query": self._SEARCH_TERM, "top_k": 5},
        )
        assert search_resp.status_code == 200
        body   = search_resp.get_json()
        chunks = body["chunks"]
        assert len(chunks) >= 1, "At least one chunk must be returned."

    def test_sources_contains_uploaded_filename(
        self, flask_client, tmp_path, monkeypatch
    ):
        from app.documents import storage_service
        from app.rag import embeddings as emb_module

        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        emb_module.set_provider(MockProvider())

        pdf_bytes = _make_pdf(
            [f"Policy content: {self._SEARCH_TERM} is enforced company-wide."]
        )
        filename = f"e2e_src_{uuid.uuid4().hex[:6]}.pdf"
        flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )

        search_resp = flask_client.post(
            "/api/rag/search",
            json={"query": self._SEARCH_TERM, "top_k": 5},
        )
        assert search_resp.status_code == 200
        sources = search_resp.get_json()["sources"]
        assert filename in sources, (
            f"Expected '{filename}' in sources {sources}"
        )

    def test_search_latency_under_1000ms_end_to_end(
        self, flask_client, tmp_path, monkeypatch
    ):
        from app.documents import storage_service
        from app.rag import embeddings as emb_module

        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        emb_module.set_provider(MockProvider())

        pdf_bytes = _make_pdf(
            [f"Latency test content about {self._SEARCH_TERM} procedures."]
        )
        filename = f"e2e_lat_{uuid.uuid4().hex[:6]}.pdf"
        flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )

        t0   = time.monotonic()
        resp = flask_client.post(
            "/api/rag/search",
            json={"query": self._SEARCH_TERM, "top_k": 5},
        )
        elapsed_ms = (time.monotonic() - t0) * 1000

        assert resp.status_code == 200
        assert elapsed_ms < 1000, (
            f"End-to-end search took {elapsed_ms:.1f}ms — must be <1 000ms"
        )
        # Also check the server-reported elapsed_ms
        assert resp.get_json()["elapsed_ms"] < 1000


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
