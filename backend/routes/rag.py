"""
routes/rag.py
--------------
Sprint 4 Step 4 — RAG Knowledge Engine

REST Blueprint exposing the semantic search endpoint:

    POST /api/rag/search
        Request  { "query": "...", "top_k": 5 }
        Response { "status", "query", "top_k", "elapsed_ms",
                   "chunks": [...], "sources": [...] }

Error responses
---------------
400 — missing / empty query, or top_k out of range
503 — FAISS index is empty (no embeddings have been generated yet)
500 — unexpected server error
"""

from __future__ import annotations

import os
import sys
import time

from flask import Blueprint, jsonify, request

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.rag.retriever    import retrieve                 # noqa: E402
from app.ml.common.model_loader import load_config        # noqa: E402
from utils.logger         import logger                   # noqa: E402

_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")


# --------------------------------------------------------------------------- #
# Blueprint
# --------------------------------------------------------------------------- #

rag_bp = Blueprint("rag", __name__, url_prefix="/api/rag")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _search_limits() -> dict:
    raw = load_config(_CONFIG_PATH)
    return raw.get("rag", {}).get("search", {})


# --------------------------------------------------------------------------- #
# POST /api/rag/search
# --------------------------------------------------------------------------- #

@rag_bp.route("/search", methods=["POST"])
def search():
    """
    Semantic similarity search over all uploaded documents.

    Request body (JSON)
    -------------------
    query   : str  — the natural-language question (required)
    top_k   : int  — number of chunks to return (optional, default from config)

    Response 200
    ------------
    {
      "status":     "success",
      "query":      "...",
      "top_k":      5,
      "elapsed_ms": 12.4,
      "chunks": [
        {
          "chunk_id":        "...",
          "chunk_text":      "...",
          "page_number":     3,
          "source_document": "Inventory Policy.pdf",
          "score":           0.94
        },
        ...
      ],
      "sources": ["Inventory Policy.pdf", "SOP.pdf"]
    }
    """
    t_start = time.monotonic()

    # ── Parse request ──────────────────────────────────────────────────────── #
    body = request.get_json(silent=True) or {}

    query = body.get("query", "").strip()
    if not query:
        return jsonify({
            "status":  "error",
            "message": "Request body must include a non-empty 'query' field.",
        }), 400

    cfg     = _search_limits()
    default_k = int(cfg.get("default_top_k", 5))
    max_k     = int(cfg.get("max_top_k",     50))

    raw_k = body.get("top_k", default_k)
    try:
        top_k = int(raw_k)
    except (TypeError, ValueError):
        return jsonify({
            "status":  "error",
            "message": f"'top_k' must be an integer (got {raw_k!r}).",
        }), 400

    if top_k < 1 or top_k > max_k:
        return jsonify({
            "status":  "error",
            "message": f"'top_k' must be between 1 and {max_k} (got {top_k}).",
        }), 400

    # ── Retrieve ───────────────────────────────────────────────────────────── #
    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception as exc:
        logger.error(f"[rag.search] retrieval error: {exc}")
        return jsonify({
            "status":  "error",
            "message": "Internal server error during retrieval.",
        }), 500

    # ── Handle empty index ─────────────────────────────────────────────────── #
    if chunks is None:
        chunks = []

    # Detect empty-index case (retriever returns [] when index has no vectors)
    # We only return 503 when the DB also has zero embeddings; if the query
    # simply matched nothing that's a normal empty result.
    if not chunks:
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

    # Deduplicated, ordered list of source filenames
    seen:    list[str] = []
    sources: list[str] = []
    for c in chunks:
        src = c.get("source_document", "")
        if src and src not in seen:
            seen.append(src)
            sources.append(src)

    logger.info(
        f"[rag.search] query='{query[:60]}' top_k={top_k} "
        f"results={len(chunks)} elapsed={elapsed_ms}ms"
    )

    return jsonify({
        "status":     "success",
        "query":      query,
        "top_k":      top_k,
        "elapsed_ms": elapsed_ms,
        "chunks":     chunks,
        "sources":    sources,
    }), 200
