"""
app/documents/document_metadata.py
------------------------------------
Sprint 4 — RAG Knowledge Engine

Database operations for the ``documents`` and ``document_chunks`` tables:
  documents table:
    - Insert a new document record.
    - Check for duplicates by (document_name, file_hash).
    - List all non-deleted documents.
    - Fetch a single document by its ID.
    - Soft-delete a document (sets status = 'deleted').
    - Update document status (pending → processing → processed / failed).
  document_chunks table:
    - Bulk-insert extracted text chunks.
    - Retrieve chunks for a document ordered by chunk_index.

All DB access uses ``database.db.get_db_connection()`` — the same pattern
used throughout the rest of the project.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.db  import get_db_connection  # noqa: E402
from utils.logger import logger             # noqa: E402


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _row_to_dict(row) -> dict[str, Any]:
    """Convert a ``sqlite3.Row`` to a plain ``dict``."""
    return dict(row)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def document_exists(document_name: str, file_hash: str) -> bool:
    """
    Return ``True`` if a document with the same name **and** file hash already
    exists in the database (regardless of status).

    Parameters
    ----------
    document_name : str
        Original filename of the uploaded document.
    file_hash : str
        SHA-256 hex digest of the file content.

    Returns
    -------
    bool
    """
    conn = get_db_connection()
    row  = conn.execute(
        "SELECT document_id FROM documents WHERE document_name = ? AND file_hash = ?",
        (document_name, file_hash),
    ).fetchone()
    conn.close()
    return row is not None


def insert_document(meta: dict[str, Any]) -> dict[str, Any]:
    """
    Insert a new row into the ``documents`` table.

    Parameters
    ----------
    meta : dict
        Must contain keys: ``document_name``, ``document_type``,
        ``uploaded_by``, ``file_path``, ``file_hash``.
        Optional key: ``document_id`` (generated if absent).

    Returns
    -------
    dict
        The fully-populated document record as stored in the DB.

    Raises
    ------
    ValueError
        If required keys are missing.
    """
    required = {"document_name", "document_type", "uploaded_by", "file_path", "file_hash"}
    missing  = required - meta.keys()
    if missing:
        raise ValueError(f"[document_metadata] Missing required fields: {missing}")

    document_id = meta.get("document_id") or str(uuid.uuid4())
    upload_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO documents
            (document_id, document_name, document_type, upload_date,
             uploaded_by, file_path, status, file_hash)
        VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
        """,
        (
            document_id,
            meta["document_name"],
            meta["document_type"],
            upload_date,
            meta["uploaded_by"],
            meta["file_path"],
            meta["file_hash"],
        ),
    )
    conn.commit()
    conn.close()

    logger.info(f"[document_metadata] Inserted document: {document_id} ({meta['document_name']})")

    return {
        "document_id":   document_id,
        "document_name": meta["document_name"],
        "document_type": meta["document_type"],
        "upload_date":   upload_date,
        "uploaded_by":   meta["uploaded_by"],
        "file_path":     meta["file_path"],
        "status":        "active",
        "file_hash":     meta["file_hash"],
    }


def list_documents() -> list[dict[str, Any]]:
    """
    Return all non-deleted documents, ordered newest first.

    After Sprint 4 Step 2, documents progress through:
      active → processing → processed / failed
    This query includes all live statuses so callers always see documents
    regardless of whether chunking has completed.

    Returns
    -------
    list[dict]
        Each element is a fully-populated document record dict.
    """
    conn  = get_db_connection()
    rows  = conn.execute(
        "SELECT * FROM documents WHERE status != 'deleted' ORDER BY upload_date DESC"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_document(document_id: str) -> dict[str, Any] | None:
    """
    Fetch a single document record by its primary key.

    Parameters
    ----------
    document_id : str
        UUID string of the target document.

    Returns
    -------
    dict | None
        The document record, or ``None`` if not found.
    """
    conn = get_db_connection()
    row  = conn.execute(
        "SELECT * FROM documents WHERE document_id = ?", (document_id,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def soft_delete_document(document_id: str) -> bool:
    """
    Mark a document as ``'deleted'`` without removing its DB row.

    Parameters
    ----------
    document_id : str
        UUID string of the target document.

    Returns
    -------
    bool
        ``True`` if the record was found and updated, ``False`` otherwise.
    """
    conn    = get_db_connection()
    cursor  = conn.execute(
        "UPDATE documents SET status = 'deleted' WHERE document_id = ? AND status != 'deleted'",
        (document_id,),
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if updated:
        logger.info(f"[document_metadata] Soft-deleted document: {document_id}")
    else:
        logger.warning(f"[document_metadata] Document not found or already deleted: {document_id}")

    return updated


# --------------------------------------------------------------------------- #
# Status management (Sprint 4 Step 2)
# --------------------------------------------------------------------------- #

def update_document_status(document_id: str, status: str) -> bool:
    """
    Update the ``status`` field of a document record.

    Valid status values in the RAG pipeline lifecycle:
      ``'active'``      — initial state after upload (Step 1)
      ``'processing'``  — extraction pipeline started
      ``'processed'``   — chunks successfully extracted and stored
      ``'failed'``      — extraction pipeline encountered an error
      ``'deleted'``     — soft-deleted (use soft_delete_document() instead)

    Parameters
    ----------
    document_id : str
        UUID string of the target document.
    status : str
        The new status value.

    Returns
    -------
    bool
        ``True`` if the record was found and updated.
    """
    conn    = get_db_connection()
    cursor  = conn.execute(
        "UPDATE documents SET status = ? WHERE document_id = ?",
        (status, document_id),
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if updated:
        logger.info(
            f"[document_metadata] Status updated: {document_id} → '{status}'"
        )
    else:
        logger.warning(
            f"[document_metadata] update_document_status: document not found: {document_id}"
        )
    return updated


# --------------------------------------------------------------------------- #
# Chunk persistence (Sprint 4 Step 2)
# --------------------------------------------------------------------------- #

def insert_chunks(
    document_id: str,
    source_document: str,
    chunks: list[dict],
) -> int:
    """
    Bulk-insert extracted text chunks into the ``document_chunks`` table.

    Parameters
    ----------
    document_id : str
        UUID of the parent document (FK).
    source_document : str
        The ``document_name`` value (denormalised for query convenience).
    chunks : list[dict]
        Output of ``chunker.chunk_pages()``.  Each element must have keys:
        ``chunk_index`` (int), ``page_number`` (int), ``chunk_text`` (str).

    Returns
    -------
    int
        Number of chunk rows inserted.
    """
    import uuid as _uuid  # local import to avoid polluting module namespace

    if not chunks:
        logger.warning(
            f"[document_metadata] insert_chunks called with empty list for {document_id}"
        )
        return 0

    rows = [
        (
            str(_uuid.uuid4()),
            document_id,
            c["chunk_index"],
            c["page_number"],
            source_document,
            c["chunk_text"],
        )
        for c in chunks
    ]

    conn = get_db_connection()
    conn.executemany(
        """
        INSERT INTO document_chunks
            (chunk_id, document_id, chunk_index, page_number,
             source_document, chunk_text)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()

    logger.info(
        f"[document_metadata] Inserted {len(rows)} chunks for document {document_id}"
    )
    return len(rows)


def get_chunks(document_id: str) -> list[dict[str, Any]]:
    """
    Retrieve all chunks for a document, ordered by ``chunk_index``.

    Parameters
    ----------
    document_id : str
        UUID of the parent document.

    Returns
    -------
    list[dict]
        Each element is a fully-populated chunk record dict.
        Empty list if the document has no chunks.
    """
    conn  = get_db_connection()
    rows  = conn.execute(
        """
        SELECT * FROM document_chunks
        WHERE document_id = ?
        ORDER BY chunk_index ASC
        """,
        (document_id,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]
