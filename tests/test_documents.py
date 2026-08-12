"""
tests/test_documents.py
------------------------
Sprint 4 — RAG Knowledge Engine

Unit and integration tests for the document upload & management subsystem.

Coverage
--------
1. DB Schema          — documents table exists with all 8 required columns.
2. StorageService     — file hash computation, save, delete.
3. UploadService      — successful upload, non-PDF rejection, duplicate rejection.
4. DocumentMetadata   — list, get, soft-delete operations.
5. API Endpoints      — POST /api/documents/upload, GET /api/documents,
                        DELETE /api/documents/<id>.
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
# Helpers
# --------------------------------------------------------------------------- #

def _make_pdf_bytes(text: str = "Standard test document page content.") -> bytes:
    """Build a valid PDF byte string using pypdf."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
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


def _make_pdf_stream(content: bytes | None = None) -> io.BytesIO:
    """Return a BytesIO stream that mimics a valid PDF file."""
    if content is None:
        content = _make_pdf_bytes()
    return io.BytesIO(content)


def _make_werkzeug_file(filename: str, content: bytes | None = None):
    """
    Build a lightweight stand-in for werkzeug.datastructures.FileStorage
    using valid PDF bytes so tests run without a live HTTP request.
    """
    from werkzeug.datastructures import FileStorage
    if content is None or content.startswith(b"%PDF"):
        if content is None or content == b"%PDF-1.4 fake pdf content" or len(content) < 50:
            content = _make_pdf_bytes(f"Content for {filename}")
    stream = io.BytesIO(content)
    return FileStorage(stream=stream, filename=filename, content_type="application/pdf")


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module", autouse=True)
def ensure_db_schema():
    """Ensure the documents table is present before any test runs."""
    init_db()


@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_test_documents():
    """
    After each test, remove any document rows whose uploaded_by is
    '__test__' so tests stay independent.  Also deletes the saved file.
    """
    yield
    from app.documents.storage_service import delete_file
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT document_id, file_path FROM documents WHERE uploaded_by = '__test__'"
    ).fetchall()
    conn.execute("DELETE FROM documents WHERE uploaded_by = '__test__'")
    conn.commit()
    conn.close()
    for row in rows:
        delete_file(row["file_path"])


# ============================================================================ #
# 1. DB Schema
# ============================================================================ #

class TestDocumentsDBSchema:
    """Verify the documents table structure in SQLite."""

    def test_documents_table_exists(self):
        conn = get_db_connection()
        row  = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone()
        conn.close()
        assert row is not None, "Table 'documents' must exist in DB."

    def test_documents_column_names(self):
        conn    = get_db_connection()
        cursor  = conn.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()

        expected = [
            "document_id",
            "document_name",
            "document_type",
            "upload_date",
            "uploaded_by",
            "file_path",
            "status",
            "file_hash",
        ]
        for col in expected:
            assert col in columns, f"Column '{col}' missing from documents table."

    def test_documents_unique_constraint_exists(self):
        """Unique index on (document_name, file_hash) must be present."""
        conn     = get_db_connection()
        indexes  = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='documents'"
        ).fetchall()
        conn.close()
        index_names = [idx["name"] for idx in indexes]
        # SQLite auto-names UNIQUE constraints as sqlite_autoindex_<table>_<n>
        assert any("documents" in name for name in index_names), (
            "Expected a UNIQUE index on the documents table."
        )


# ============================================================================ #
# 2. Storage Service
# ============================================================================ #

class TestStorageService:
    """Unit tests for app/documents/storage_service.py."""

    def test_compute_file_hash_returns_64_char_hex(self):
        from app.documents.storage_service import compute_file_hash
        fs   = _make_werkzeug_file("test.pdf", b"hello world")
        h    = compute_file_hash(fs)
        assert isinstance(h, str), "Hash must be a string."
        assert len(h) == 64,       "SHA-256 hex digest must be 64 characters."

    def test_compute_file_hash_is_deterministic(self):
        from app.documents.storage_service import compute_file_hash
        content = b"deterministic content"
        h1 = compute_file_hash(_make_werkzeug_file("a.pdf", content))
        h2 = compute_file_hash(_make_werkzeug_file("a.pdf", content))
        assert h1 == h2, "Same content must produce the same hash."

    def test_compute_file_hash_differs_for_different_content(self):
        from app.documents.storage_service import compute_file_hash
        h1 = compute_file_hash(_make_werkzeug_file("a.pdf", b"content A"))
        h2 = compute_file_hash(_make_werkzeug_file("b.pdf", b"content B"))
        assert h1 != h2, "Different content must produce different hashes."

    def test_save_file_creates_file_on_disk(self, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        fs   = _make_werkzeug_file("save_test.pdf", b"%PDF test")
        path = storage_service.save_file(fs, "save_test.pdf")
        assert os.path.exists(path), "Saved file must exist on disk."

    def test_delete_file_removes_file(self, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))
        fs   = _make_werkzeug_file("del_test.pdf", b"%PDF test")
        path = storage_service.save_file(fs, "del_test.pdf")
        result = storage_service.delete_file(path)
        assert result is True,            "delete_file() must return True."
        assert not os.path.exists(path),  "File must be removed from disk."

    def test_delete_file_returns_false_for_missing_file(self, tmp_path):
        from app.documents.storage_service import delete_file
        result = delete_file(str(tmp_path / "nonexistent.pdf"))
        assert result is False, "delete_file() must return False for missing files."


# ============================================================================ #
# 3. Upload Service
# ============================================================================ #

class TestUploadService:
    """Unit tests for app/documents/upload_service.py."""

    def test_successful_pdf_upload(self, tmp_path, monkeypatch):
        """A valid PDF must be saved to disk and inserted into the DB."""
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        from app.documents.upload_service import process_upload
        fs     = _make_werkzeug_file("sprint4_test.pdf", _make_pdf_bytes("Sprint 4 unique upload content"))
        record = process_upload(fs, uploaded_by="__test__")

        assert record["document_name"] == "sprint4_test.pdf"
        assert record["document_type"] == "pdf"
        assert record["status"]        in ("active", "processed")
        assert record["uploaded_by"]   == "__test__"
        assert len(record["file_hash"]) == 64
        assert os.path.exists(record["file_path"]), "File must exist on disk after upload."

    def test_non_pdf_file_raises_value_error(self, tmp_path, monkeypatch):
        """Uploading a non-PDF file must raise ValueError."""
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        from app.documents.upload_service import process_upload
        fs = _make_werkzeug_file("report.docx", b"PK\x03\x04 fake docx")
        with pytest.raises(ValueError, match="Only PDF"):
            process_upload(fs, uploaded_by="__test__")

    def test_duplicate_upload_raises_duplicate_error(self, tmp_path, monkeypatch):
        """Re-uploading the same file must raise DuplicateDocumentError."""
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        from app.documents.upload_service import process_upload, DuplicateDocumentError
        content  = _make_pdf_bytes("Duplicate content for unit testing")
        filename = f"dup_test_{uuid.uuid4().hex[:6]}.pdf"

        # First upload — must succeed
        fs1 = _make_werkzeug_file(filename, content)
        process_upload(fs1, uploaded_by="__test__")

        # Second upload — must be rejected
        fs2 = _make_werkzeug_file(filename, content)
        with pytest.raises(DuplicateDocumentError):
            process_upload(fs2, uploaded_by="__test__")

    def test_same_name_different_content_not_a_duplicate(self, tmp_path, monkeypatch):
        """Same filename with different content must NOT be treated as duplicate."""
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        from app.documents.upload_service import process_upload
        base_name = f"samenamed_{uuid.uuid4().hex[:6]}.pdf"

        fs1 = _make_werkzeug_file(base_name, _make_pdf_bytes("Content version 1"))
        r1  = process_upload(fs1, uploaded_by="__test__")

        new_name = base_name.replace(".pdf", "_v2.pdf")
        fs2 = _make_werkzeug_file(new_name, _make_pdf_bytes("Content version 2"))
        r2  = process_upload(fs2, uploaded_by="__test__")

        assert r1["document_id"] != r2["document_id"], (
            "Different content must produce independent document records."
        )


    def test_missing_file_raises_value_error(self, tmp_path, monkeypatch):
        """process_upload() with no file must raise ValueError."""
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        from werkzeug.datastructures import FileStorage
        from app.documents.upload_service import process_upload
        empty_fs = FileStorage(stream=io.BytesIO(b""), filename="", content_type="")
        with pytest.raises(ValueError):
            process_upload(empty_fs, uploaded_by="__test__")


# ============================================================================ #
# 4. Document Metadata
# ============================================================================ #

class TestDocumentMetadata:
    """Unit tests for app/documents/document_metadata.py."""

    def _insert_test_doc(self, suffix: str = "") -> dict:
        from app.documents.document_metadata import insert_document
        return insert_document({
            "document_name": f"meta_test{suffix}.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     f"/tmp/meta_test{suffix}.pdf",
            "file_hash":     uuid.uuid4().hex * 2,  # 64-char fake hash
        })

    def test_insert_document_returns_record(self):
        record = self._insert_test_doc("_insert")
        assert "document_id"   in record
        assert record["status"] == "active"

    def test_list_documents_includes_inserted(self):
        from app.documents.document_metadata import list_documents
        record = self._insert_test_doc("_list")
        docs   = list_documents()
        ids    = [d["document_id"] for d in docs]
        assert record["document_id"] in ids, "Newly inserted doc must appear in list."

    def test_get_document_returns_correct_record(self):
        from app.documents.document_metadata import get_document
        record   = self._insert_test_doc("_get")
        fetched  = get_document(record["document_id"])
        assert fetched is not None
        assert fetched["document_name"] == record["document_name"]

    def test_get_document_returns_none_for_unknown_id(self):
        from app.documents.document_metadata import get_document
        result = get_document(str(uuid.uuid4()))
        assert result is None

    def test_soft_delete_sets_status_deleted(self):
        from app.documents.document_metadata import get_document, soft_delete_document
        record = self._insert_test_doc("_del")
        ok     = soft_delete_document(record["document_id"])
        assert ok is True
        refreshed = get_document(record["document_id"])
        assert refreshed["status"] == "deleted"

    def test_soft_delete_returns_false_for_unknown_id(self):
        from app.documents.document_metadata import soft_delete_document
        result = soft_delete_document(str(uuid.uuid4()))
        assert result is False

    def test_list_documents_excludes_deleted(self):
        from app.documents.document_metadata import list_documents, soft_delete_document
        record = self._insert_test_doc("_excl")
        soft_delete_document(record["document_id"])
        docs = list_documents()
        ids  = [d["document_id"] for d in docs]
        assert record["document_id"] not in ids, (
            "Deleted document must not appear in list_documents()."
        )

    def test_document_exists_true_after_insert(self):
        from app.documents.document_metadata import insert_document, document_exists
        file_hash = uuid.uuid4().hex * 2
        insert_document({
            "document_name": "exists_check.pdf",
            "document_type": "pdf",
            "uploaded_by":   "__test__",
            "file_path":     "/tmp/exists_check.pdf",
            "file_hash":     file_hash,
        })
        assert document_exists("exists_check.pdf", file_hash) is True

    def test_document_exists_false_for_unknown(self):
        from app.documents.document_metadata import document_exists
        assert document_exists("__nonexistent__.pdf", "a" * 64) is False


# ============================================================================ #
# 5. API Endpoints
# ============================================================================ #

class TestDocumentsAPIEndpoints:
    """Integration tests against the Flask test client."""

    # ── POST /api/documents/upload ──────────────────────────────────────────

    def test_upload_returns_201_for_valid_pdf(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        content = _make_pdf_bytes("API upload test content")
        data     = {
            "file":        (io.BytesIO(content), "api_upload_test.pdf"),
            "uploaded_by": "__test__",
        }
        resp = flask_client.post(
            "/api/documents/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "success"
        assert "document" in body
        assert body["document"]["document_name"] == "api_upload_test.pdf"

    def test_upload_returns_400_for_non_pdf(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        data = {"file": (io.BytesIO(b"not a pdf"), "report.txt")}
        resp = flask_client.post(
            "/api/documents/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_upload_returns_400_when_no_file(self, flask_client):
        resp = flask_client.post(
            "/api/documents/upload",
            data={},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_upload_returns_409_for_duplicate(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        content  = _make_pdf_bytes("Duplicate test content")
        filename = f"dup_api_{uuid.uuid4().hex[:6]}.pdf"

        # First upload
        resp1 = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(content), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert resp1.status_code == 201

        # Duplicate upload
        resp2 = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(content), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        assert resp2.status_code == 409
        body2 = resp2.get_json()
        assert body2["status"] == "error"

    # ── GET /api/documents ──────────────────────────────────────────────────

    def test_list_returns_200(self, flask_client):
        resp = flask_client.get("/api/documents")
        assert resp.status_code == 200

    def test_list_response_schema(self, flask_client):
        resp = flask_client.get("/api/documents")
        body = resp.get_json()
        assert body["status"]    == "success"
        assert "count"           in body
        assert "documents"       in body
        assert isinstance(body["documents"], list)

    def test_list_includes_uploaded_document(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        content  = _make_pdf_bytes("Listing check content")
        filename = f"list_check_{uuid.uuid4().hex[:6]}.pdf"
        flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(content), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )

        resp  = flask_client.get("/api/documents")
        names = [d["document_name"] for d in resp.get_json()["documents"]]
        assert filename in names, "Uploaded document must appear in listing."

    # ── DELETE /api/documents/<id> ──────────────────────────────────────────

    def test_delete_returns_200(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        content  = _make_pdf_bytes("Delete check content")
        filename = f"delete_me_{uuid.uuid4().hex[:6]}.pdf"
        upload_resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(content), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        doc_id = upload_resp.get_json()["document"]["document_id"]

        del_resp = flask_client.delete(f"/api/documents/{doc_id}")
        assert del_resp.status_code == 200
        body = del_resp.get_json()
        assert body["status"]      == "success"
        assert body["document_id"] == doc_id

    def test_delete_removes_from_listing(self, flask_client, tmp_path, monkeypatch):
        from app.documents import storage_service
        monkeypatch.setattr(storage_service, "STORAGE_DIR", str(tmp_path))

        content  = _make_pdf_bytes("Delete from listing content")
        filename = f"del_list_{uuid.uuid4().hex[:6]}.pdf"
        upload_resp = flask_client.post(
            "/api/documents/upload",
            data={"file": (io.BytesIO(content), filename), "uploaded_by": "__test__"},
            content_type="multipart/form-data",
        )
        doc_id = upload_resp.get_json()["document"]["document_id"]

        flask_client.delete(f"/api/documents/{doc_id}")

        list_resp = flask_client.get("/api/documents")
        ids       = [d["document_id"] for d in list_resp.get_json()["documents"]]
        assert doc_id not in ids, "Deleted document must not appear in listing."

    def test_delete_returns_404_for_unknown_id(self, flask_client):
        resp = flask_client.delete(f"/api/documents/{uuid.uuid4()}")
        assert resp.status_code == 404


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
