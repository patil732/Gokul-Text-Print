"""
app/documents/document_metadata.py
------------------------------------
Sprint 4 — RAG Knowledge Engine

Database operations for the ``documents`` table:
  - Insert a new document record.
  - Check for duplicates by (document_name, file_hash).
  - List all active documents.
  - Fetch a single document by its ID.
  - Soft-delete a document (sets status = 'deleted').

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
    Return all documents whose status is ``'active'``, ordered newest first.

    Returns
    -------
    list[dict]
        Each element is a fully-populated document record dict.
    """
    conn  = get_db_connection()
    rows  = conn.execute(
        "SELECT * FROM documents WHERE status = 'active' ORDER BY upload_date DESC"
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
        "UPDATE documents SET status = 'deleted' WHERE document_id = ? AND status = 'active'",
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
