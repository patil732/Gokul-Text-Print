"""
routes/documents.py
--------------------
Sprint 4 — RAG Knowledge Engine

Flask Blueprint exposing three document-management endpoints:

    POST   /api/documents/upload      — upload a PDF (multipart/form-data)
    GET    /api/documents             — list all active documents
    DELETE /api/documents/<id>        — soft-delete document + remove from disk

Authentication note
-------------------
Endpoints currently trust ``session["user"]`` for ``uploaded_by``.
When no session is present (e.g. in tests) they fall back to ``"system"``.
Role-level guards can be added here once RBAC requirements are finalised.
"""

from __future__ import annotations

import os
import sys

from flask import Blueprint, jsonify, request, session

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.documents.upload_service   import process_upload, DuplicateDocumentError  # noqa: E402
from app.documents.document_metadata import (                                       # noqa: E402
    list_documents,
    get_document,
    soft_delete_document,
)
from app.documents.storage_service  import delete_file                              # noqa: E402
from utils.logger                   import logger                                   # noqa: E402


# --------------------------------------------------------------------------- #
# Blueprint
# --------------------------------------------------------------------------- #

documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")


# --------------------------------------------------------------------------- #
# POST /api/documents/upload
# --------------------------------------------------------------------------- #

@documents_bp.route("/upload", methods=["POST"])
def upload_document():
    """
    Upload a PDF document.

    Request
    -------
    Content-Type: multipart/form-data
    Fields:
        file        (required) — the PDF file
        uploaded_by (optional) — uploader identity; falls back to session user

    Responses
    ---------
    201 — document accepted and stored
        { "status": "success", "document": { ... } }
    400 — missing file / bad extension
        { "status": "error", "message": "..." }
    409 — duplicate document
        { "status": "error", "message": "..." }
    500 — unexpected server error
        { "status": "error", "message": "..." }
    """
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request."}), 400

    file_storage = request.files["file"]

    if not file_storage or file_storage.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    # Resolve uploader identity
    uploaded_by = (
        request.form.get("uploaded_by")
        or session.get("user")
        or "system"
    )

    try:
        record = process_upload(file_storage, uploaded_by=uploaded_by)
        return jsonify({"status": "success", "document": record}), 201

    except DuplicateDocumentError as exc:
        logger.warning(f"[documents.upload] Duplicate rejected: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 409

    except ValueError as exc:
        logger.warning(f"[documents.upload] Validation error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 400

    except Exception as exc:  # pragma: no cover
        logger.error(f"[documents.upload] Unexpected error: {exc}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


# --------------------------------------------------------------------------- #
# GET /api/documents
# --------------------------------------------------------------------------- #

@documents_bp.route("", methods=["GET"])
def get_documents():
    """
    List all active documents.

    Responses
    ---------
    200 — success
        {
          "status": "success",
          "count":  <int>,
          "documents": [ { ... }, ... ]
        }
    500 — unexpected error
        { "status": "error", "message": "..." }
    """
    try:
        docs = list_documents()
        return jsonify({
            "status":    "success",
            "count":     len(docs),
            "documents": docs,
        }), 200

    except Exception as exc:  # pragma: no cover
        logger.error(f"[documents.list] Unexpected error: {exc}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500


# --------------------------------------------------------------------------- #
# DELETE /api/documents/<document_id>
# --------------------------------------------------------------------------- #

@documents_bp.route("/<string:document_id>", methods=["DELETE"])
def delete_document(document_id: str):
    """
    Soft-delete a document record and remove its file from disk.

    Path parameter
    --------------
    document_id : str
        UUID of the document to delete.

    Responses
    ---------
    200 — document deleted
        { "status": "success", "message": "...", "document_id": "..." }
    404 — document not found or already deleted
        { "status": "error", "message": "..." }
    500 — unexpected error
        { "status": "error", "message": "..." }
    """
    try:
        # Fetch the record first so we can get the file path
        doc = get_document(document_id)
        if not doc or doc.get("status") == "deleted":
            return jsonify({
                "status":  "error",
                "message": f"Document '{document_id}' not found or already deleted.",
            }), 404

        # Soft-delete the DB record
        deleted = soft_delete_document(document_id)
        if not deleted:
            return jsonify({
                "status":  "error",
                "message": f"Document '{document_id}' not found or already deleted.",
            }), 404

        # Remove physical file (best-effort; log warning if missing)
        delete_file(doc["file_path"])

        return jsonify({
            "status":      "success",
            "message":     f"Document '{doc['document_name']}' deleted successfully.",
            "document_id": document_id,
        }), 200

    except Exception as exc:  # pragma: no cover
        logger.error(f"[documents.delete] Unexpected error: {exc}")
        return jsonify({"status": "error", "message": "Internal server error."}), 500
