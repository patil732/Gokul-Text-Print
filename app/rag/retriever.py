"""
app/rag/retriever.py
---------------------
Sprint 4 Step 4 — RAG Knowledge Engine

Top-K similarity retrieval: embed a query → search the FAISS index →
fetch chunk metadata → return ranked results with provenance.

Public API
----------
    from app.rag.retriever import retrieve

    results = retrieve("What is the reorder policy?", top_k=5)
    # [
    #   {
    #     "chunk_id":        "...",
    #     "chunk_text":      "Reorder when stock falls below ...",
    #     "page_number":     3,
    #     "source_document": "Inventory Policy.pdf",
    #     "score":           0.94,
    #   },
    #   ...
    # ]

Design
------
- Query text is embedded via the active provider (``app.rag.embeddings.embed()``).
- The embedding is L2-normalised then passed to ``vector_store.search_index()``.
- Chunk metadata (text, page, source) is fetched from ``document_chunks`` by
  chunk_id, preserving the score-ranked order from FAISS.
- ``top_k`` is clamped to ``rag.search.max_top_k`` from model_config.yaml.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

import numpy as np

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from utils.logger import logger  # noqa: E402
from app.ml.common.model_loader import load_config  # noqa: E402
from app.rag.embeddings   import embed as _embed     # noqa: E402
from app.rag.vector_store import (                   # noqa: E402
    get_index,
    search_index,
)

_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

def _search_cfg() -> dict[str, Any]:
    return load_config(_CONFIG_PATH).get("rag", {}).get("search", {})


# --------------------------------------------------------------------------- #
# Metadata fetch helper
# --------------------------------------------------------------------------- #

def _fetch_chunk_metadata(chunk_ids: list[str]) -> dict[str, dict]:
    """
    Return a map of ``{chunk_id: {chunk_text, page_number, source_document}}``.

    Uses a single SQL query with an IN clause for efficiency.
    """
    if not chunk_ids:
        return {}

    from database.db import get_db_connection  # local import

    placeholders = ",".join("?" * len(chunk_ids))
    conn = get_db_connection()
    rows = conn.execute(
        f"SELECT chunk_id, chunk_text, page_number, source_document "
        f"FROM document_chunks WHERE chunk_id IN ({placeholders})",
        chunk_ids,
    ).fetchall()
    conn.close()

    return {
        row["chunk_id"]: {
            "chunk_text":      row["chunk_text"],
            "page_number":     row["page_number"],
            "source_document": row["source_document"],
        }
        for row in rows
    }


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def retrieve(
    query_text: str,
    top_k:      int | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve the top-K most semantically similar chunks for *query_text*.

    Parameters
    ----------
    query_text : str
        Natural-language query string.
    top_k : int | None
        Number of results to return.  Defaults to ``rag.search.default_top_k``
        from model_config.yaml.  Clamped to ``max_top_k``.

    Returns
    -------
    list[dict]
        Ranked list of results::

            {
                "chunk_id":        str,
                "chunk_text":      str,
                "page_number":     int,
                "source_document": str,   # filename of the source PDF
                "score":           float, # cosine similarity (0 – 1)
            }

        Returns ``[]`` when the index is empty (no documents uploaded yet).

    Raises
    ------
    ValueError
        If *query_text* is empty.
    """
    if not query_text or not query_text.strip():
        raise ValueError("[retriever] query_text must not be empty.")

    cfg      = _search_cfg()
    default_k = int(cfg.get("default_top_k", 5))
    max_k     = int(cfg.get("max_top_k", 50))
    k         = min(top_k if top_k is not None else default_k, max_k)

    t0 = time.monotonic()

    # ── 1. Embed the query ─────────────────────────────────────────────────── #
    query_vector = _embed(query_text)

    # ── 2. Search the FAISS index ──────────────────────────────────────────── #
    index, chunk_ids = get_index()

    if index is None or not chunk_ids:
        logger.info("[retriever] Index is empty — returning no results.")
        return []

    hits = search_index(index, chunk_ids, query_vector, top_k=k)

    # ── 3. Fetch chunk text + provenance ───────────────────────────────────── #
    hit_ids  = [h["chunk_id"] for h in hits]
    meta_map = _fetch_chunk_metadata(hit_ids)

    results: list[dict[str, Any]] = []
    for hit in hits:
        cid  = hit["chunk_id"]
        meta = meta_map.get(cid, {})
        results.append(
            {
                "chunk_id":        cid,
                "chunk_text":      meta.get("chunk_text",      ""),
                "page_number":     meta.get("page_number",     0),
                "source_document": meta.get("source_document", ""),
                "score":           hit["score"],
            }
        )

    elapsed_ms = (time.monotonic() - t0) * 1000
    logger.info(
        f"[retriever] Retrieved {len(results)}/{k} chunks "
        f"for query='{query_text[:40]}' in {elapsed_ms:.1f}ms"
    )
    return results
