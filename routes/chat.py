"""
routes/chat.py
---------------
Sprint 4 Step 5 — RAG Chat Service

Flask Blueprint for the single-turn Q&A endpoint:

    POST /api/chat
        Request  { "question": "..." }
        Response { "status", "question", "answer", "sources", "elapsed_ms" }

Error responses
---------------
400 — missing / empty question
503 — no documents indexed yet (chat() returned empty sources + fallback answer)
500 — LLM or retrieval error
"""

from __future__ import annotations

import os
import sys
import time

from flask import Blueprint, jsonify, request, session

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.rag.chat_service import chat               # noqa: E402
from app.rag.chat_history import get_chat_history   # noqa: E402
from utils.logger         import logger             # noqa: E402

# --------------------------------------------------------------------------- #
# Blueprint
# --------------------------------------------------------------------------- #

chat_bp = Blueprint("chat", __name__, url_prefix="/api")


# --------------------------------------------------------------------------- #
# POST /api/chat
# --------------------------------------------------------------------------- #

@chat_bp.route("/chat", methods=["POST"])
def ask():
    """
    Single-turn RAG question-answering endpoint.

    Request body (JSON)
    -------------------
    question : str  — the natural-language question (required)
    user     : str  — identity of user asking (optional, default session/system)

    Response 200
    ------------
    {
      "status":     "success",
      "question":   "What triggers a purchase order?",
      "answer":     "A purchase order is triggered when stock falls below...",
      "sources": [
        {"document": "Inventory Policy.pdf", "page": 3},
        {"document": "SOP.pdf",              "page": 1}
      ],
      "elapsed_ms": 1240
    }
    """
    t_start = time.monotonic()

    # ── Parse request ──────────────────────────────────────────────────────── #
    body     = request.get_json(silent=True) or {}
    question = body.get("question", "").strip()
    user     = body.get("user") or session.get("user") or "system"

    if not question:
        return jsonify({
            "status":  "error",
            "message": "Request body must include a non-empty 'question' field.",
        }), 400

    # ── Call chat service ──────────────────────────────────────────────────── #
    try:
        result = chat(question, user=user)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except RuntimeError as exc:
        logger.error(f"[chat.ask] LLM error: {exc}")
        return jsonify({
            "status":  "error",
            "message": "The language model returned an error. Please try again.",
        }), 500
    except Exception as exc:
        logger.error(f"[chat.ask] Unexpected error: {exc}")
        return jsonify({
            "status":  "error",
            "message": "Internal server error.",
        }), 500

    # ── Detect empty-index situation ───────────────────────────────────────── #
    # chat() returns [] sources when no chunks were retrieved.
    # Check whether the DB actually has embeddings to distinguish
    # "no results for query" (200) from "nothing uploaded yet" (503).
    if not result["sources"]:
        from database.db import get_db_connection
        conn    = get_db_connection()
        has_emb = conn.execute(
            "SELECT COUNT(*) as cnt FROM chunk_embeddings"
        ).fetchone()["cnt"]
        conn.close()

        if has_emb == 0:
            return jsonify({
                "status":  "error",
                "message": "No documents have been indexed yet. "
                           "Upload and process at least one PDF first.",
            }), 503

    # ── Build response ─────────────────────────────────────────────────────── #
    elapsed_ms = round((time.monotonic() - t_start) * 1000, 2)

    logger.info(
        f"[chat.ask] question='{question[:60]}' user='{user}' "
        f"sources={len(result['sources'])} elapsed={elapsed_ms}ms"
    )

    return jsonify({
        "status":     "success",
        "chat_id":    result.get("chat_id"),
        "question":   question,
        "answer":     result["answer"],
        "sources":    result["sources"],
        "elapsed_ms": elapsed_ms,
    }), 200


# --------------------------------------------------------------------------- #
# GET /api/chat/history
# --------------------------------------------------------------------------- #

@chat_bp.route("/chat/history", methods=["GET"])
def history():
    """
    Retrieve paginated chat history ordered by timestamp descending.

    Query parameters
    ----------------
    page  : int (optional, default 1)
    limit : int (optional, default 20, max 100)
    user  : str (optional, filter by user)

    Response 200
    ------------
    {
      "status":  "success",
      "page":    1,
      "limit":   20,
      "total":   45,
      "pages":   3,
      "history": [
        {
          "chat_id": "...",
          "user": "...",
          "question": "...",
          "answer": "...",
          "retrieved_documents": [...],
          "timestamp": "..."
        }
      ]
    }
    """
    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    try:
        limit = int(request.args.get("limit", 20))
    except (ValueError, TypeError):
        limit = 20

    user = request.args.get("user")

    data = get_chat_history(page=page, limit=limit, user=user)

    return jsonify({
        "status":  "success",
        "page":    data["page"],
        "limit":   data["limit"],
        "total":   data["total"],
        "pages":   data["pages"],
        "history": data["history"],
    }), 200

