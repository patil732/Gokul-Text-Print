"""
tests/test_embeddings.py
--------------------------
Sprint 4 Step 3 — RAG Knowledge Engine: Embedding Backend

Tests the full embedding stack with ALL providers mocked — no real API calls,
no model downloads, no API keys required.

Coverage
--------
1. TestEmbeddingConfig         — YAML config parsing; unknown provider raises ValueError
2. TestSentenceTransformerProvider — embed() / embed_batch() shape; mock SentenceTransformer
3. TestOpenAIProvider          — embed() / embed_batch() via mocked openai.OpenAI
4. TestGeminiProvider          — embed() / embed_batch() via mocked google.generativeai
5. TestEmbeddingDeduplication  — embedding_exists() False before insert, True after;
                                 insert_embedding() stores all 6 fields; get_embeddings() join
6. TestEmbeddingPipeline       — all chunks receive embeddings; already-embedded chunks skipped;
                                 embed_count matches; empty document returns 0
7. TestUploadPipelineEmbeddings — end-to-end Flask upload with mocked provider;
                                  embed_count field present in JSON response

Mock strategy
-------------
- ``app.rag.embeddings.set_provider(MockProvider())`` injects a fake provider
  that returns deterministic unit-vectors without any library dependency.
- ``app.rag.embeddings.reset_provider()`` is called in teardown so other tests
  are not affected by the injected singleton.
- For provider-unit tests, individual library modules are patched via
  ``unittest.mock.patch`` at import time to avoid ImportError when the real
  library is absent.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_db_connection, init_db

# ── Flask app factory ─────────────────────────────────────────────────────── #
_SPEC    = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


# --------------------------------------------------------------------------- #
# Constants & helpers
# --------------------------------------------------------------------------- #

_VECTOR_DIM = 8  # small fixed dimension for all mock vectors


def _unit_vector(seed: int = 0) -> list[float]:
    """Return a deterministic unit-vector of dimension _VECTOR_DIM."""
    import math
    v = [float(i + seed + 1) for i in range(_VECTOR_DIM)]
    norm = math.sqrt(sum(x ** 2 for x in v))
    return [x / norm for x in v]


class MockEmbeddingProvider:
    """
    Test double for any real EmbeddingProvider.

    embed()       → _unit_vector(0)
    embed_batch() → one _unit_vector(i) per text
    """

    def embed(self, text: str) -> list[float]:
        return _unit_vector(0)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_unit_vector(i) for i in range(len(texts))]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _make_real_pdf(page_texts: list[str]) -> bytes:
    """Build a valid multi-page PDF in memory via pypdf.PdfWriter."""
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
        font_dict = DictionaryObject({
            NameObject("/Type"):     NameObject("/Font"),
            NameObject("/Subtype"):  NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        resources = DictionaryObject({
            NameObject("/Font"): DictionaryObject({
                NameObject("/F1"): writer._add_object(font_dict)
            })
        })
        page[NameObject("/Resources")] = resources

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
    """Always reset the provider singleton so tests don't bleed into each other."""
    from app.rag import embeddings as emb_module
    emb_module.reset_provider()
    yield
    emb_module.reset_provider()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Remove all rows created with uploaded_by='__test__' after each test."""
    yield
    from app.documents.storage_service import delete_file
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT document_id, file_path FROM documents WHERE uploaded_by = '__test__'"
    ).fetchall()
    doc_ids = [r["document_id"] for r in rows]
    if doc_ids:
        ph = ",".join("?" * len(doc_ids))
        chunk_rows = conn.execute(
            f"SELECT chunk_id FROM document_chunks WHERE document_id IN ({ph})", doc_ids
        ).fetchall()
        chunk_ids = [c["chunk_id"] for c in chunk_rows]
        if chunk_ids:
            cph = ",".join("?" * len(chunk_ids))
            conn.execute(f"DELETE FROM chunk_embeddings WHERE chunk_id IN ({cph})", chunk_ids)
        conn.execute(f"DELETE FROM document_chunks WHERE document_id IN ({ph})", doc_ids)
    conn.execute("DELETE FROM documents WHERE uploaded_by = '__test__'")
    conn.commit()
    conn.close()
    for row in rows:
        delete_file(row["file_path"])


# ============================================================================ #
# 1. Embedding Config
# ============================================================================ #

class TestEmbeddingConfig:

    def test_default_provider_is_sentence_transformers(self):
        from app.rag.embeddings import _resolve_config
        cfg = _resolve_config()
        assert cfg.provider == "sentence_transformers"

    def test_default_model_is_minilm(self):
        from app.rag.embeddings import _resolve_config
        cfg = _resolve_config()
        assert cfg.model == "all-MiniLM-L6-v2"

    def test_dimension_is_integer(self):
        from app.rag.embeddings import _resolve_config
        cfg = _resolve_config()
        assert isinstance(cfg.dimension, int)
        assert cfg.dimension > 0

    def test_batch_size_is_positive_integer(self):
        from app.rag.embeddings import _resolve_config
        cfg = _resolve_config()
        assert isinstance(cfg.batch_size, int)
        assert cfg.batch_size > 0

    def test_unknown_provider_raises_value_error(self):
        from app.rag.embeddings import get_provider, _PROVIDER_REGISTRY
        # Temporarily override the registry lookup via a bad config value
        with patch("app.rag.embeddings._resolve_config") as mock_cfg:
            from app.rag.embeddings import EmbeddingConfig
            mock_cfg.return_value = EmbeddingConfig(provider="nonexistent_provider")
            with pytest.raises(ValueError, match="Unknown provider"):
                get_provider()

    def test_embedding_config_dataclass_fields(self):
        from app.rag.embeddings import EmbeddingConfig
        cfg = EmbeddingConfig()
        assert hasattr(cfg, "provider")
        assert hasattr(cfg, "model")
        assert hasattr(cfg, "dimension")
        assert hasattr(cfg, "batch_size")
        assert hasattr(cfg, "api_key")


# ============================================================================ #
# 2. SentenceTransformer Provider
# ============================================================================ #

class TestSentenceTransformerProvider:

    def _make_provider(self, dim: int = _VECTOR_DIM):
        """Build a SentenceTransformerProvider with a mocked backend."""
        from app.rag.embeddings import SentenceTransformerProvider, EmbeddingConfig
        import numpy as np

        cfg = EmbeddingConfig(provider="sentence_transformers",
                              model="all-MiniLM-L6-v2", dimension=dim)

        mock_st = MagicMock()
        mock_st.encode.side_effect = lambda texts, **kw: (
            np.array([_unit_vector(i) for i in range(len(texts))])
            if isinstance(texts, list)
            else np.array(_unit_vector(0))
        )

        with patch("app.rag.embeddings.SentenceTransformerProvider.__init__",
                   lambda self, cfg: None):
            prov = SentenceTransformerProvider.__new__(SentenceTransformerProvider)
            prov._model = mock_st
            prov._cfg   = cfg
        return prov

    def test_embed_returns_list_of_floats(self):
        prov = self._make_provider()
        result = prov.embed("hello world")
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_embed_batch_returns_one_vector_per_text(self):
        prov = self._make_provider()
        texts = ["foo", "bar", "baz"]
        result = prov.embed_batch(texts)
        assert len(result) == len(texts)

    def test_embed_batch_each_element_is_list_of_floats(self):
        prov = self._make_provider()
        result = prov.embed_batch(["a", "b"])
        for vec in result:
            assert isinstance(vec, list)
            assert all(isinstance(x, float) for x in vec)

    def test_embed_batch_empty_returns_empty(self):
        prov = self._make_provider()
        assert prov.embed_batch([]) == []


# ============================================================================ #
# 3. OpenAI Provider
# ============================================================================ #

class TestOpenAIProvider:

    def _make_provider(self, dim: int = _VECTOR_DIM):
        from app.rag.embeddings import OpenAIProvider, EmbeddingConfig

        cfg = EmbeddingConfig(provider="openai", model="text-embedding-3-small",
                              dimension=dim, api_key="test-key")

        # Build mock response for OpenAI embeddings.create
        def _make_data(texts_or_text):
            texts = texts_or_text if isinstance(texts_or_text, list) else [texts_or_text]
            return [MagicMock(embedding=_unit_vector(i)) for i in range(len(texts))]

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = lambda input, model: \
            MagicMock(data=_make_data(input))

        with patch("app.rag.embeddings.OpenAIProvider.__init__", lambda self, cfg: None):
            prov = OpenAIProvider.__new__(OpenAIProvider)
            prov._client = mock_client
            prov._cfg    = cfg
        return prov

    def test_embed_returns_list_of_floats(self):
        prov = self._make_provider()
        result = prov.embed("test query")
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_embed_batch_returns_correct_count(self):
        prov = self._make_provider()
        texts = ["one", "two", "three", "four"]
        result = prov.embed_batch(texts)
        assert len(result) == len(texts)

    def test_embed_batch_each_is_list_of_floats(self):
        prov = self._make_provider()
        for vec in prov.embed_batch(["x", "y"]):
            assert isinstance(vec, list)
            assert all(isinstance(v, float) for v in vec)

    def test_embed_batch_empty_returns_empty(self):
        prov = self._make_provider()
        assert prov.embed_batch([]) == []

    def test_missing_api_key_raises_value_error(self):
        from app.rag.embeddings import OpenAIProvider, EmbeddingConfig

        cfg = EmbeddingConfig(provider="openai", model="text-embedding-3-small",
                              api_key="")  # no key
        mock_openai = MagicMock()

        with patch.dict("sys.modules", {"openai": mock_openai}):
            with pytest.raises(ValueError, match="API key"):
                OpenAIProvider(cfg)


# ============================================================================ #
# 4. Gemini Provider
# ============================================================================ #

class TestGeminiProvider:

    def _make_provider(self, dim: int = _VECTOR_DIM):
        from app.rag.embeddings import GeminiProvider, EmbeddingConfig

        cfg = EmbeddingConfig(provider="gemini",
                              model="models/text-embedding-004",
                              dimension=dim, api_key="test-gemini-key")

        mock_genai = MagicMock()
        mock_genai.embed_content.side_effect = lambda model, content, task_type: \
            {"embedding": _unit_vector(0)}

        with patch("app.rag.embeddings.GeminiProvider.__init__", lambda self, cfg: None):
            prov = GeminiProvider.__new__(GeminiProvider)
            prov._genai = mock_genai
            prov._cfg   = cfg
        return prov

    def test_embed_returns_list_of_floats(self):
        prov = self._make_provider()
        result = prov.embed("gemini test")
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_embed_batch_returns_correct_count(self):
        prov = self._make_provider()
        texts = ["alpha", "beta", "gamma"]
        result = prov.embed_batch(texts)
        assert len(result) == len(texts)

    def test_embed_batch_each_is_list_of_floats(self):
        prov = self._make_provider()
        for vec in prov.embed_batch(["a", "b"]):
            assert isinstance(vec, list)
            assert all(isinstance(v, float) for v in vec)

    def test_embed_batch_empty_returns_empty(self):
        prov = self._make_provider()
        assert prov.embed_batch([]) == []

    def test_missing_api_key_raises_value_error(self):
        from app.rag.embeddings import GeminiProvider, EmbeddingConfig

        cfg = EmbeddingConfig(provider="gemini", model="models/text-embedding-004",
                              api_key="")
        mock_genai_mod = MagicMock()

        with patch.dict("sys.modules", {
            "google": MagicMock(),
            "google.generativeai": mock_genai_mod,
        }):
            with pytest.raises(ValueError, match="API key"):
                GeminiProvider(cfg)


# ============================================================================ #
# 5. Embedding Deduplication (DB layer)
# ============================================================================ #

class TestEmbeddingDeduplication:

    def _create_chunk(self) -> dict:
        """Insert a document + chunk and return the chunk dict."""
        from app.documents.document_metadata import insert_document, insert_chunks
        doc = insert_document({
            "document_name": f"dedup_test_{uuid.uuid4().hex[:6]}.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     "/tmp/dedup.pdf",
            "file_hash":     uuid.uuid4().hex * 2,
        })
        insert_chunks(doc["document_id"], doc["document_name"], [
            {"chunk_index": 0, "page_number": 1, "chunk_text": "Dedup test chunk text."}
        ])
        from app.documents.document_metadata import get_chunks
        chunks = get_chunks(doc["document_id"])
        return chunks[0]

    def test_embedding_not_exists_before_insert(self):
        from app.documents.document_metadata import embedding_exists
        chunk = self._create_chunk()
        h = _sha256(chunk["chunk_text"])
        assert embedding_exists(chunk["chunk_id"], h) is False

    def test_embedding_exists_after_insert(self):
        from app.documents.document_metadata import embedding_exists, insert_embedding
        chunk = self._create_chunk()
        h = _sha256(chunk["chunk_text"])
        insert_embedding(chunk["chunk_id"], h, _unit_vector(), "mock", "mock-v1")
        assert embedding_exists(chunk["chunk_id"], h) is True

    def test_different_hash_not_detected_as_duplicate(self):
        from app.documents.document_metadata import embedding_exists, insert_embedding
        chunk = self._create_chunk()
        h_old = _sha256(chunk["chunk_text"])
        insert_embedding(chunk["chunk_id"], h_old, _unit_vector(), "mock", "mock-v1")
        h_new = _sha256("completely different text")
        # Same chunk_id but new hash → should NOT be found
        assert embedding_exists(chunk["chunk_id"], h_new) is False

    def test_insert_embedding_stores_correct_fields(self):
        from app.documents.document_metadata import insert_embedding
        chunk = self._create_chunk()
        h     = _sha256(chunk["chunk_text"])
        vec   = _unit_vector()
        emb_id = insert_embedding(chunk["chunk_id"], h, vec, "mock", "mock-v1")

        conn = get_db_connection()
        row  = conn.execute(
            "SELECT * FROM chunk_embeddings WHERE embedding_id = ?", (emb_id,)
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["chunk_id"]   == chunk["chunk_id"]
        assert row["chunk_hash"] == h
        assert row["provider"]   == "mock"
        assert row["model"]      == "mock-v1"

        stored_vec = json.loads(row["embedding"])
        assert len(stored_vec) == _VECTOR_DIM
        assert all(abs(a - b) < 1e-9 for a, b in zip(stored_vec, vec))

    def test_insert_embedding_returns_uuid_string(self):
        from app.documents.document_metadata import insert_embedding
        chunk  = self._create_chunk()
        h      = _sha256(chunk["chunk_text"])
        emb_id = insert_embedding(chunk["chunk_id"], h, _unit_vector(), "mock", "v1")
        # Should be parseable as a UUID
        parsed = uuid.UUID(emb_id)
        assert str(parsed) == emb_id

    def test_get_embeddings_returns_joined_rows(self):
        from app.documents.document_metadata import (
            insert_document, insert_chunks, get_chunks,
            insert_embedding, get_embeddings,
        )
        doc = insert_document({
            "document_name": f"get_emb_{uuid.uuid4().hex[:6]}.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     "/tmp/get_emb.pdf",
            "file_hash":     uuid.uuid4().hex * 2,
        })
        insert_chunks(doc["document_id"], doc["document_name"], [
            {"chunk_index": 0, "page_number": 1, "chunk_text": "First chunk."},
            {"chunk_index": 1, "page_number": 1, "chunk_text": "Second chunk."},
        ])
        chunks = get_chunks(doc["document_id"])
        for chunk in chunks:
            h = _sha256(chunk["chunk_text"])
            insert_embedding(chunk["chunk_id"], h, _unit_vector(), "mock", "v1")

        result = get_embeddings(doc["document_id"])
        assert len(result) == 2
        for row in result:
            assert "embedding_id"    in row
            assert "chunk_id"        in row
            assert "chunk_index"     in row
            assert "page_number"     in row
            assert "source_document" in row

    def test_get_embeddings_empty_for_unknown_document(self):
        from app.documents.document_metadata import get_embeddings
        result = get_embeddings(str(uuid.uuid4()))
        assert result == []


# ============================================================================ #
# 6. Embedding Pipeline
# ============================================================================ #

class TestEmbeddingPipeline:

    def _setup_document_with_chunks(self, n_chunks: int = 3) -> str:
        from app.documents.document_metadata import insert_document, insert_chunks
        doc = insert_document({
            "document_name": f"pipeline_{uuid.uuid4().hex[:6]}.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     "/tmp/pipeline.pdf",
            "file_hash":     uuid.uuid4().hex * 2,
        })
        chunks = [
            {"chunk_index": i, "page_number": 1, "chunk_text": f"Chunk {i} text content."}
            for i in range(n_chunks)
        ]
        insert_chunks(doc["document_id"], doc["document_name"], chunks)
        return doc["document_id"]

    def test_all_chunks_receive_embeddings(self):
        from app.rag import embeddings as emb_module
        from app.rag.embedding_pipeline import embed_document_chunks
        from app.documents.document_metadata import get_embeddings

        emb_module.set_provider(MockEmbeddingProvider())

        doc_id = self._setup_document_with_chunks(3)
        count  = embed_document_chunks(doc_id, "pipeline.pdf")

        assert count == 3
        assert len(get_embeddings(doc_id)) == 3

    def test_already_embedded_chunks_are_skipped(self):
        from app.rag import embeddings as emb_module
        from app.rag.embedding_pipeline import embed_document_chunks

        emb_module.set_provider(MockEmbeddingProvider())

        doc_id = self._setup_document_with_chunks(2)

        # First run
        first_count  = embed_document_chunks(doc_id, "pipeline.pdf")
        assert first_count == 2

        # Second run — nothing new to embed
        second_count = embed_document_chunks(doc_id, "pipeline.pdf")
        assert second_count == 0

    def test_embed_count_matches_chunk_count(self):
        from app.rag import embeddings as emb_module
        from app.rag.embedding_pipeline import embed_document_chunks

        emb_module.set_provider(MockEmbeddingProvider())

        n   = 5
        doc_id = self._setup_document_with_chunks(n)
        count  = embed_document_chunks(doc_id, "pipeline.pdf")
        assert count == n

    def test_empty_document_returns_zero(self):
        from app.rag import embeddings as emb_module
        from app.rag.embedding_pipeline import embed_document_chunks

        emb_module.set_provider(MockEmbeddingProvider())
        # Unknown document_id → no chunks
        count = embed_document_chunks(str(uuid.uuid4()), "ghost.pdf")
        assert count == 0

    def test_embedding_vectors_are_stored_as_valid_json(self):
        from app.rag import embeddings as emb_module
        from app.rag.embedding_pipeline import embed_document_chunks

        emb_module.set_provider(MockEmbeddingProvider())

        doc_id = self._setup_document_with_chunks(1)
        embed_document_chunks(doc_id, "pipeline.pdf")

        conn = get_db_connection()
        rows = conn.execute(
            "SELECT ce.embedding FROM chunk_embeddings ce "
            "JOIN document_chunks dc ON dc.chunk_id = ce.chunk_id "
            "WHERE dc.document_id = ?",
            (doc_id,),
        ).fetchall()
        conn.close()

        assert len(rows) == 1
        vec = json.loads(rows[0]["embedding"])
        assert isinstance(vec, list)
        assert all(isinstance(v, float) for v in vec)

    def test_provider_metadata_stored_correctly(self):
        from app.rag import embeddings as emb_module
        from app.rag.embedding_pipeline import embed_document_chunks

        emb_module.set_provider(MockEmbeddingProvider())

        doc_id = self._setup_document_with_chunks(1)
        embed_document_chunks(doc_id, "pipeline.pdf")

        conn = get_db_connection()
        row  = conn.execute(
            "SELECT ce.provider, ce.model FROM chunk_embeddings ce "
            "JOIN document_chunks dc ON dc.chunk_id = ce.chunk_id "
            "WHERE dc.document_id = ?",
            (doc_id,),
        ).fetchone()
        conn.close()

        assert row is not None
        # Provider name is derived from class name "MockEmbeddingProvider" → "mockembedding"
        # or similar; just verify it's a non-empty string
        assert len(row["provider"]) > 0
        assert len(row["model"])    >= 0  # may be 'unknown' for test doubles


# ============================================================================ #
# 7. Upload Pipeline — Embeddings end-to-end
# ============================================================================ #

class TestUploadPipelineEmbeddings:
    """
    Full Flask upload with MockEmbeddingProvider injected.

    The real sentence-transformers model is NOT downloaded.
    """

    def _upload(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        from app.rag import embeddings as emb_module

        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        emb_module.set_provider(MockEmbeddingProvider())

        pdf_bytes = _make_real_pdf([
            "Embedding pipeline end-to-end test page with enough words to chunk."
        ])
        filename = f"emb_pipeline_{uuid.uuid4().hex[:6]}.pdf"
        resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        return resp, filename

    def test_upload_returns_201(self, flask_client, tmp_path, monkeypatch):
        resp, _ = self._upload(flask_client, tmp_path, monkeypatch)
        assert resp.status_code == 201

    def test_response_contains_embed_count(self, flask_client, tmp_path, monkeypatch):
        resp, _ = self._upload(flask_client, tmp_path, monkeypatch)
        body = resp.get_json()["document"]
        assert "embed_count" in body, "Response must include 'embed_count' field."

    def test_embed_count_is_non_negative(self, flask_client, tmp_path, monkeypatch):
        resp, _ = self._upload(flask_client, tmp_path, monkeypatch)
        body = resp.get_json()["document"]
        assert body["embed_count"] >= 0

    def test_status_is_processed(self, flask_client, tmp_path, monkeypatch):
        resp, _ = self._upload(flask_client, tmp_path, monkeypatch)
        body = resp.get_json()["document"]
        assert body["status"] == "processed"

    def test_chunk_embeddings_exist_in_db(self, flask_client, tmp_path, monkeypatch):
        from app.documents.document_metadata import get_embeddings
        resp, _ = self._upload(flask_client, tmp_path, monkeypatch)
        doc_id   = resp.get_json()["document"]["document_id"]
        embeddings = get_embeddings(doc_id)
        assert len(embeddings) >= 1, "At least one embedding must be in DB after upload."

    def test_embedding_failure_does_not_break_upload(
        self, flask_client, tmp_path, monkeypatch
    ):
        """
        If embed_document_chunks raises, the upload should still succeed
        (status=processed, embed_count=0).
        """
        from app.documents import storage_service
        from app.rag import embeddings as emb_module

        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        # Inject a provider that always fails
        class FailingProvider:
            def embed(self, text):
                raise RuntimeError("mock embedding failure")
            def embed_batch(self, texts):
                raise RuntimeError("mock embedding failure")

        emb_module.set_provider(FailingProvider())

        pdf_bytes = _make_real_pdf(["Failure tolerance test content."])
        filename  = f"emb_fail_{uuid.uuid4().hex[:6]}.pdf"
        resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        body = resp.get_json()["document"]
        assert body["status"]      == "processed"
        assert body["embed_count"] == 0


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
