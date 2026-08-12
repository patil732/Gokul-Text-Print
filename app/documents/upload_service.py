"""
app/documents/upload_service.py
---------------------------------
Sprint 4 — RAG Knowledge Engine

Orchestrates the end-to-end PDF upload workflow:
  1. Validate that the file extension is ``.pdf``.
  2. Compute a SHA-256 hash of the file bytes.
  3. Reject duplicates (same ``document_name`` + ``file_hash``).
  4. Persist the file to the local documents/ directory.
  5. Write metadata to the ``documents`` table (status: 'active').
  6. Trigger the RAG extraction pipeline (Step 2):
       a. Update status → 'processing'.
       b. Extract text pages via ``app.rag.loader``.
       c. Chunk the text via ``app.rag.chunker``.
       d. Persist chunks to ``document_chunks``.
       e. Generate embeddings for each chunk (Step 3 — non-fatal).
       f. Update status → 'processed'.
       g. On extraction error: update status → 'failed', log, re-raise.

Usage
-----
    from app.documents.upload_service import process_upload, DuplicateDocumentError

    try:
        record = process_upload(request.files["file"], uploaded_by="admin")
    except DuplicateDocumentError as exc:
        return jsonify({"error": str(exc)}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
"""

from __future__ import annotations

import os
import sys

from werkzeug.datastructures import FileStorage

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.documents.storage_service   import compute_file_hash, save_file  # noqa: E402
from app.documents.document_metadata import (                               # noqa: E402
    document_exists,
    insert_document,
    update_document_status,
    insert_chunks,
)
from app.rag.loader            import extract_pages              # noqa: E402
from app.rag.chunker           import chunk_pages                # noqa: E402
from app.rag.embedding_pipeline import embed_document_chunks     # noqa: E402
from utils.logger              import logger                     # noqa: E402


# --------------------------------------------------------------------------- #
# Custom exception
# --------------------------------------------------------------------------- #

class DuplicateDocumentError(Exception):
    """
    Raised when an uploaded PDF is already present in the documents table.

    The duplicate is determined by matching both ``document_name`` and the
    SHA-256 ``file_hash`` — so a rename of an existing file is not treated as
    a duplicate, and a same-name file with different content is accepted.
    """


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"pdf"})


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def _allowed_file(filename: str) -> bool:
    """Return True if *filename* has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def process_upload(
    file_storage: FileStorage,
    uploaded_by: str = "system",
) -> dict:
    """
    Validate, de-duplicate, store, and record an uploaded PDF.

    Parameters
    ----------
    file_storage : FileStorage
        The ``FileStorage`` object from ``request.files["file"]``.
    uploaded_by : str
        Identity of the uploader (e.g. session username).  Defaults to
        ``"system"`` when called outside an authenticated request.

    Returns
    -------
    dict
        The fully-populated document metadata record as stored in the DB.

    Raises
    ------
    ValueError
        If no file is provided, the filename is empty, or the extension is
        not ``.pdf``.
    DuplicateDocumentError
        If a document with the same name and file hash already exists.
    OSError
        If the file cannot be written to the storage directory.
    """
    # ── 1. Validate presence ──────────────────────────────────────────────── #
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided or filename is empty.")

    filename = file_storage.filename

    # ── 2. Validate extension ─────────────────────────────────────────────── #
    if not _allowed_file(filename):
        raise ValueError(
            f"Unsupported file type '{filename}'. Only PDF files are accepted."
        )

    # ── 3. Compute SHA-256 hash ───────────────────────────────────────────── #
    file_hash = compute_file_hash(file_storage)
    logger.info(f"[upload_service] Hash computed for '{filename}': {file_hash[:12]}…")

    # ── 4. Duplicate check ────────────────────────────────────────────────── #
    if document_exists(filename, file_hash):
        raise DuplicateDocumentError(
            f"Document '{filename}' with identical content already exists."
        )

    # ── 5. Persist to disk ────────────────────────────────────────────────── #
    file_path = save_file(file_storage, filename)

    # ── 6. Write metadata to DB ───────────────────────────────────────────── #
    record = insert_document(
        {
            "document_name": filename,
            "document_type": "pdf",
            "uploaded_by":   uploaded_by,
            "file_path":     file_path,
            "file_hash":     file_hash,
        }
    )
    document_id = record["document_id"]

    # ── 7. RAG extraction pipeline (Sprint 4 Step 2) ─────────────────────── #
    try:
        # a. Mark as processing
        update_document_status(document_id, "processing")
        record["status"] = "processing"

        # b. Extract text pages from the saved PDF
        pages = extract_pages(file_path)

        # c. Split into overlapping chunks
        chunks = chunk_pages(pages)

        # d. Persist chunks to document_chunks table
        chunk_count = insert_chunks(document_id, filename, chunks)

        # e. Generate embeddings (Step 3) — non-fatal: failure logs but
        #    does not prevent the document from being marked 'processed'.
        try:
            embed_count = embed_document_chunks(document_id, filename)
            record["embed_count"] = embed_count
            logger.info(
                f"[upload_service] Embedded {embed_count} chunks "
                f"for {document_id}"
            )
        except Exception as emb_exc:
            logger.warning(
                f"[upload_service] Embedding skipped for {document_id}: {emb_exc}"
            )
            record["embed_count"] = 0

        # f. Mark as processed
        update_document_status(document_id, "processed")
        record["status"]      = "processed"
        record["chunk_count"] = chunk_count

        logger.info(
            f"[upload_service] Pipeline complete: {document_id} — "
            f"{chunk_count} chunks from '{filename}'"
        )

    except Exception as exc:
        # g. Mark as failed — upload record is preserved for audit/retry
        logger.error(
            f"[upload_service] RAG pipeline failed for {document_id} "
            f"('{filename}'): {exc}"
        )
        update_document_status(document_id, "failed")
        record["status"] = "failed"
        # Re-raise so the route can return an appropriate HTTP error
        raise

    return record
