"""
tests/test_rag_pipeline.py
---------------------------
Sprint 4 Step 2 — RAG Knowledge Engine

Unit and integration tests for the PDF extraction & chunking pipeline.

Coverage
--------
1. DB Schema          — document_chunks table exists with all 6 required columns.
2. PDF Loader         — extract_pages() returns per-page dicts; empty pages skipped;
                        clean_text() normalises whitespace correctly.
3. Chunker            — chunks produced; chunk_index sequential; overlap preserved;
                        short text produces exactly 1 chunk.
4. Chunk Persistence  — insert_chunks() writes to DB; get_chunks() retrieves in order;
                        update_document_status() transitions status correctly.
5. Upload Pipeline    — upload via Flask client → document status = 'processed';
                        document_chunks rows created with correct metadata fields.

Test PDF generation
-------------------
``_make_real_pdf()`` builds a valid multi-page PDF in memory using
``pypdf.PdfWriter`` so no binary fixture needs to be committed to the repo.
"""

from __future__ import annotations

import importlib.util
import io
import os
import sys
import uuid

import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_db_connection, init_db

# ── Load Flask app factory (same pattern as test_sales_history.py) ─────────── #
_SPEC    = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


# --------------------------------------------------------------------------- #
# Helpers — in-memory PDF generation
# --------------------------------------------------------------------------- #

def _make_real_pdf(pages: list[str]) -> bytes:
    """
    Build a genuine (non-stub) PDF with one text page per entry in *pages*.

    Uses ``pypdf.PdfWriter`` with a blank page and overlaid text annotations
    so that ``pypdf.PdfReader.extract_text()`` can read the content back.

    For simplicity we embed text via the content stream directly — this
    produces text that ``pypdf`` can extract reliably.
    """
    from pypdf import PdfWriter
    from pypdf.generic import (
        ArrayObject, ContentStream, DecodedStreamObject,
        DictionaryObject, NameObject, NumberObject, RectangleObject,
    )

    writer = PdfWriter()

    for page_text in pages:
        # Add a blank A4 page
        page = writer.add_blank_page(width=595, height=842)

        # Build a minimal content stream that draws text
        # BT = begin text, /F1 = font, Tf = set font+size,
        # Td = move cursor, Tj = show string, ET = end text
        safe_text = page_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content = f"BT /F1 12 Tf 50 750 Td ({safe_text}) Tj ET".encode()

        stream = DecodedStreamObject()
        stream.set_data(content)
        page[NameObject("/Contents")] = writer._add_object(stream)

        # Register a minimal font so pypdf does not error
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


def _make_pdf_file(tmp_path, pages: list[str], filename: str = "test.pdf") -> str:
    """Write a real PDF to *tmp_path* and return its absolute path."""
    pdf_bytes = _make_real_pdf(pages)
    path = str(tmp_path / filename)
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path


def _make_werkzeug_file(filename: str, content: bytes):
    """Build a Werkzeug FileStorage from raw bytes."""
    from werkzeug.datastructures import FileStorage
    return FileStorage(
        stream=io.BytesIO(content),
        filename=filename,
        content_type="application/pdf",
    )


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module", autouse=True)
def ensure_db_schema():
    """Ensure all tables are present before any test runs."""
    init_db()


@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """
    Remove any document + chunk rows created by tests (uploaded_by='__test__')
    and delete saved files after each test.
    """
    yield
    from app.documents.storage_service import delete_file
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT document_id, file_path FROM documents WHERE uploaded_by = '__test__'"
    ).fetchall()
    doc_ids = [r["document_id"] for r in rows]
    if doc_ids:
        placeholders = ",".join("?" * len(doc_ids))
        conn.execute(
            f"DELETE FROM document_chunks WHERE document_id IN ({placeholders})", doc_ids
        )
    conn.execute("DELETE FROM documents WHERE uploaded_by = '__test__'")
    conn.commit()
    conn.close()
    for row in rows:
        delete_file(row["file_path"])


# ============================================================================ #
# 1. DB Schema
# ============================================================================ #

class TestDocumentChunksSchema:
    """Verify the document_chunks table structure in SQLite."""

    def test_document_chunks_table_exists(self):
        conn = get_db_connection()
        row  = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks'"
        ).fetchone()
        conn.close()
        assert row is not None, "Table 'document_chunks' must exist in DB."

    def test_document_chunks_column_names(self):
        conn    = get_db_connection()
        cursor  = conn.execute("PRAGMA table_info(document_chunks)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()

        expected = [
            "chunk_id",
            "document_id",
            "chunk_index",
            "page_number",
            "source_document",
            "chunk_text",
        ]
        for col in expected:
            assert col in columns, f"Column '{col}' missing from document_chunks."


# ============================================================================ #
# 2. PDF Loader
# ============================================================================ #

class TestPDFLoader:
    """Unit tests for app/rag/loader.py."""

    def test_extract_pages_returns_list(self, tmp_path):
        from app.rag.loader import extract_pages
        path   = _make_pdf_file(tmp_path, ["Hello world this is page one content."])
        result = extract_pages(path)
        assert isinstance(result, list)
        assert len(result) >= 1, "Should extract at least one non-empty page."

    def test_extract_pages_contains_expected_keys(self, tmp_path):
        from app.rag.loader import extract_pages
        path   = _make_pdf_file(tmp_path, ["Sample document text for key test."])
        pages  = extract_pages(path)
        assert len(pages) >= 1
        page = pages[0]
        assert "page_number" in page, "'page_number' key must be present."
        assert "text"        in page, "'text' key must be present."

    def test_extract_pages_page_numbers_are_one_based(self, tmp_path):
        from app.rag.loader import extract_pages
        path  = _make_pdf_file(
            tmp_path,
            [
                "First page content with enough text to pass min char filter.",
                "Second page content with enough text to pass min char filter.",
            ],
        )
        pages = extract_pages(path)
        # Page numbers must start from 1, not 0
        page_nums = [p["page_number"] for p in pages]
        assert 1 in page_nums, "First non-empty page must have page_number = 1."

    def test_extract_pages_raises_for_missing_file(self):
        from app.rag.loader import extract_pages
        with pytest.raises(FileNotFoundError):
            extract_pages("/nonexistent/path/to/file.pdf")

    def test_extract_pages_raises_for_invalid_pdf(self, tmp_path):
        from app.rag.loader import extract_pages
        bad_path = str(tmp_path / "bad.pdf")
        with open(bad_path, "wb") as f:
            f.write(b"not a valid pdf at all")
        with pytest.raises(ValueError):
            extract_pages(bad_path)

    def test_clean_text_normalises_multiple_spaces(self):
        from app.rag.loader import clean_text
        result = clean_text("hello   world    foo")
        assert result == "hello world foo", "Multiple spaces must be collapsed."

    def test_clean_text_collapses_excess_newlines(self):
        from app.rag.loader import clean_text
        result = clean_text("line1\n\n\n\n\nline2")
        assert "\n\n\n" not in result, "3+ consecutive newlines must be collapsed."

    def test_clean_text_strips_leading_trailing_whitespace(self):
        from app.rag.loader import clean_text
        result = clean_text("   hello world   ")
        assert result == "hello world"

    def test_clean_text_handles_empty_string(self):
        from app.rag.loader import clean_text
        assert clean_text("") == ""
        assert clean_text(None) == ""  # type: ignore[arg-type]

    def test_clean_text_removes_control_characters(self):
        from app.rag.loader import clean_text
        # \x01 is a control char; \t and \n are kept
        result = clean_text("hello\x01world")
        assert "\x01" not in result


# ============================================================================ #
# 3. Chunker
# ============================================================================ #

class TestChunker:
    """Unit tests for app/rag/chunker.py."""

    def _make_pages(self, word_count: int, page_number: int = 1) -> list[dict]:
        text = " ".join(f"word{i}" for i in range(word_count))
        return [{"page_number": page_number, "text": text}]

    def test_chunk_pages_returns_list(self):
        from app.rag.chunker import chunk_pages
        pages  = self._make_pages(100)
        chunks = chunk_pages(pages, target_tokens=50, overlap_tokens=5)
        assert isinstance(chunks, list)

    def test_chunk_pages_nonempty_for_nonempty_pages(self):
        from app.rag.chunker import chunk_pages
        pages  = self._make_pages(200)
        chunks = chunk_pages(pages, target_tokens=50, overlap_tokens=5)
        assert len(chunks) > 0, "Non-empty pages must produce at least one chunk."

    def test_chunk_indices_are_sequential(self):
        from app.rag.chunker import chunk_pages
        pages  = self._make_pages(600)
        chunks = chunk_pages(pages, target_tokens=100, overlap_tokens=10)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks))), "chunk_index must be 0-based sequential."

    def test_each_chunk_has_required_keys(self):
        from app.rag.chunker import chunk_pages
        pages  = self._make_pages(300)
        chunks = chunk_pages(pages, target_tokens=100, overlap_tokens=10)
        for chunk in chunks:
            assert "chunk_index"  in chunk
            assert "page_number"  in chunk
            assert "chunk_text"   in chunk

    def test_short_text_produces_single_chunk(self):
        from app.rag.chunker import chunk_pages
        pages  = self._make_pages(50)
        chunks = chunk_pages(pages, target_tokens=500, overlap_tokens=50)
        assert len(chunks) == 1, "Text shorter than target_tokens must produce 1 chunk."

    def test_overlap_words_appear_in_consecutive_chunks(self):
        from app.rag.chunker import chunk_pages
        # 600 words, chunk size 100, overlap 20
        pages  = self._make_pages(600)
        chunks = chunk_pages(pages, target_tokens=100, overlap_tokens=20)
        if len(chunks) >= 2:
            tail_words = set(chunks[0]["chunk_text"].split()[-20:])
            head_words = set(chunks[1]["chunk_text"].split()[:20])
            overlap    = tail_words & head_words
            assert len(overlap) > 0, "Overlap words must appear in consecutive chunks."

    def test_chunk_pages_empty_input_returns_empty(self):
        from app.rag.chunker import chunk_pages
        assert chunk_pages([]) == []

    def test_chunk_pages_raises_if_overlap_gte_target(self):
        from app.rag.chunker import chunk_pages
        pages = self._make_pages(100)
        with pytest.raises(ValueError, match="overlap_tokens"):
            chunk_pages(pages, target_tokens=50, overlap_tokens=50)

    def test_page_number_tracked_across_pages(self):
        from app.rag.chunker import chunk_pages
        # Two pages, each with 60 words; target 50 words → at least 2 chunks
        pages = [
            {"page_number": 1, "text": " ".join(f"p1w{i}" for i in range(60))},
            {"page_number": 2, "text": " ".join(f"p2w{i}" for i in range(60))},
        ]
        chunks = chunk_pages(pages, target_tokens=50, overlap_tokens=5)
        page_nums = {c["page_number"] for c in chunks}
        # Should reference at least one of the two source pages
        assert page_nums.issubset({1, 2})


# ============================================================================ #
# 4. Chunk Persistence
# ============================================================================ #

class TestChunkPersistence:
    """Unit tests for the chunk-related functions in document_metadata.py."""

    def _create_test_document(self) -> str:
        """Insert a minimal document row and return its document_id."""
        from app.documents.document_metadata import insert_document
        record = insert_document({
            "document_name": f"persist_test_{uuid.uuid4().hex[:6]}.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     "/tmp/persist_test.pdf",
            "file_hash":     uuid.uuid4().hex * 2,
        })
        return record["document_id"]

    def test_insert_chunks_returns_correct_count(self):
        from app.documents.document_metadata import insert_chunks
        doc_id = self._create_test_document()
        chunks = [
            {"chunk_index": 0, "page_number": 1, "chunk_text": "First chunk text."},
            {"chunk_index": 1, "page_number": 1, "chunk_text": "Second chunk text."},
            {"chunk_index": 2, "page_number": 2, "chunk_text": "Third chunk text."},
        ]
        count = insert_chunks(doc_id, "persist_test.pdf", chunks)
        assert count == 3

    def test_get_chunks_returns_all_inserted(self):
        from app.documents.document_metadata import insert_chunks, get_chunks
        doc_id = self._create_test_document()
        chunks = [
            {"chunk_index": 0, "page_number": 1, "chunk_text": "Alpha text."},
            {"chunk_index": 1, "page_number": 2, "chunk_text": "Beta text."},
        ]
        insert_chunks(doc_id, "alpha_beta.pdf", chunks)
        fetched = get_chunks(doc_id)
        assert len(fetched) == 2

    def test_get_chunks_ordered_by_chunk_index(self):
        from app.documents.document_metadata import insert_chunks, get_chunks
        doc_id = self._create_test_document()
        chunks = [{"chunk_index": i, "page_number": 1, "chunk_text": f"Text {i}."} for i in range(5)]
        insert_chunks(doc_id, "order_test.pdf", chunks)
        fetched = get_chunks(doc_id)
        indices = [c["chunk_index"] for c in fetched]
        assert indices == sorted(indices), "Chunks must be ordered by chunk_index ASC."

    def test_get_chunks_record_has_all_fields(self):
        from app.documents.document_metadata import insert_chunks, get_chunks
        doc_id = self._create_test_document()
        insert_chunks(doc_id, "fields_test.pdf", [
            {"chunk_index": 0, "page_number": 3, "chunk_text": "Some content."}
        ])
        fetched = get_chunks(doc_id)
        assert len(fetched) == 1
        chunk = fetched[0]
        for field in ["chunk_id", "document_id", "chunk_index", "page_number",
                      "source_document", "chunk_text"]:
            assert field in chunk, f"Field '{field}' missing from chunk record."

    def test_get_chunks_source_document_matches(self):
        from app.documents.document_metadata import insert_chunks, get_chunks
        doc_id      = self._create_test_document()
        source_name = "exact_source.pdf"
        insert_chunks(doc_id, source_name, [
            {"chunk_index": 0, "page_number": 1, "chunk_text": "Content."}
        ])
        fetched = get_chunks(doc_id)
        assert fetched[0]["source_document"] == source_name

    def test_get_chunks_returns_empty_for_unknown_document(self):
        from app.documents.document_metadata import get_chunks
        result = get_chunks(str(uuid.uuid4()))
        assert result == []

    def test_update_document_status_transitions_correctly(self):
        from app.documents.document_metadata import update_document_status, get_document
        doc_id = self._create_test_document()

        for new_status in ("processing", "processed", "failed", "active"):
            ok = update_document_status(doc_id, new_status)
            assert ok is True
            doc = get_document(doc_id)
            assert doc["status"] == new_status, (
                f"Status should be '{new_status}', got '{doc['status']}'"
            )

    def test_update_document_status_returns_false_for_unknown(self):
        from app.documents.document_metadata import update_document_status
        result = update_document_status(str(uuid.uuid4()), "processed")
        assert result is False

    def test_insert_chunks_empty_list_returns_zero(self):
        from app.documents.document_metadata import insert_chunks
        doc_id = self._create_test_document()
        count  = insert_chunks(doc_id, "empty.pdf", [])
        assert count == 0


# ============================================================================ #
# 5. Upload Pipeline (end-to-end)
# ============================================================================ #

class TestUploadPipeline:
    """
    Integration tests verifying that a complete upload via the Flask endpoint
    triggers the RAG pipeline and produces chunk records.
    """

    def test_upload_sets_status_processed(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        pdf_bytes = _make_real_pdf(
            ["This is the first page of a test document with some meaningful text content."]
        )
        filename  = f"pipeline_status_{uuid.uuid4().hex[:6]}.pdf"
        resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        doc = resp.get_json()["document"]
        assert doc["status"] == "processed", (
            f"Expected 'processed', got '{doc['status']}'"
        )

    def test_upload_creates_chunk_rows(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        from app.documents.document_metadata import get_chunks
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        pdf_bytes = _make_real_pdf([
            "Page one has plenty of text content so that the chunker can process it.",
            "Page two also has meaningful content for the chunker to work with properly.",
        ])
        filename  = f"pipeline_chunks_{uuid.uuid4().hex[:6]}.pdf"
        resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        doc_id = resp.get_json()["document"]["document_id"]

        chunks = get_chunks(doc_id)
        assert len(chunks) >= 1, "At least one chunk must be created after upload."

    def test_upload_chunk_fields_populated(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        from app.documents.document_metadata import get_chunks
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        pdf_bytes = _make_real_pdf(
            ["Document content for field validation. It contains several words."]
        )
        filename  = f"pipeline_fields_{uuid.uuid4().hex[:6]}.pdf"
        resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        doc_id = resp.get_json()["document"]["document_id"]

        chunks = get_chunks(doc_id)
        assert len(chunks) >= 1
        chunk = chunks[0]

        assert chunk["chunk_id"]        != ""
        assert chunk["document_id"]     == doc_id
        assert chunk["chunk_index"]     == 0
        assert isinstance(chunk["page_number"], int)
        assert chunk["source_document"] == filename
        assert len(chunk["chunk_text"])  > 0

    def test_upload_response_contains_chunk_count(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        pdf_bytes = _make_real_pdf(
            ["Response schema test content. This PDF should produce a chunk count field."]
        )
        filename  = f"pipeline_count_{uuid.uuid4().hex[:6]}.pdf"
        resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        body = resp.get_json()["document"]
        assert "chunk_count" in body, "Response must include 'chunk_count' field."
        assert body["chunk_count"] >= 1

    def test_processed_document_appears_in_listing(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        pdf_bytes = _make_real_pdf(["Listing test content for processed document."])
        filename  = f"pipeline_list_{uuid.uuid4().hex[:6]}.pdf"
        flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(pdf_bytes), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )

        list_resp = flask_client.get("/api/documents")
        assert list_resp.status_code == 200
        names = [d["document_name"] for d in list_resp.get_json()["documents"]]
        assert filename in names, "Processed document must appear in GET /api/documents."


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
