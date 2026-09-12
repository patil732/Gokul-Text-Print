"""
app/rag/embedding_pipeline.py
------------------------------
Sprint 4 Step 3 — RAG Knowledge Engine

Orchestrates batch embedding of all chunks belonging to a document.

Workflow
--------
1. Fetch all ``document_chunks`` rows for ``document_id``.
2. For each chunk, compute SHA-256(chunk_text) → ``chunk_hash``.
3. Call ``embedding_exists(chunk_id, chunk_hash)`` — skip if already embedded
   with the same content (idempotent re-runs, zero duplicate API calls).
4. Collect unseen chunks and call ``embed_batch()`` in one provider call.
5. Persist each vector with ``insert_embedding()``.
6. Return the count of newly generated embeddings.

Public API
----------
    from app.rag.embedding_pipeline import embed_document_chunks

    embed_count = embed_document_chunks(document_id, source_document)
"""

from __future__ import annotations

import hashlib
import os
import sys
from typing import Any

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.documents.document_metadata import (  # noqa: E402
    get_chunks,
    embedding_exists,
    insert_embedding,
)
from app.rag.embeddings import embed_batch, get_provider  # noqa: E402
from utils.logger        import logger                    # noqa: E402


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _sha256(text: str) -> str:
    """Return the SHA-256 hex digest of *text* (UTF-8 encoded)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def embed_document_chunks(
    document_id: str,
    source_document: str,
) -> int:
    """
    Generate and persist embeddings for all chunks of a document.

    Chunks whose ``(chunk_id, chunk_hash)`` pair is already present in
    ``chunk_embeddings`` are skipped, making this function safe to call
    multiple times on the same document (e.g. on retry after a partial
    failure).

    Parameters
    ----------
    document_id : str
        UUID of the parent document.
    source_document : str
        Human-readable document name (used only for log messages).

    Returns
    -------
    int
        Number of embeddings newly generated and persisted.
        Returns 0 if all chunks were already embedded or the document has
        no chunks.
    """
    chunks = get_chunks(document_id)
    if not chunks:
        logger.warning(
            f"[embedding_pipeline] No chunks found for document {document_id} "
            f"('{source_document}') — nothing to embed."
        )
        return 0

    # ── Identify unseen chunks ────────────────────────────────────────────── #
    unseen: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_hash = _sha256(chunk["chunk_text"])
        if not embedding_exists(chunk["chunk_id"], chunk_hash):
            unseen.append({**chunk, "chunk_hash": chunk_hash})

    if not unseen:
        logger.info(
            f"[embedding_pipeline] All {len(chunks)} chunks already embedded "
            f"for document {document_id} — skipping."
        )
        return 0

    logger.info(
        f"[embedding_pipeline] Embedding {len(unseen)}/{len(chunks)} chunks "
        f"for '{source_document}' ({document_id})"
    )

    # ── Embed unseen chunks in one batch call ─────────────────────────────── #
    texts   = [c["chunk_text"] for c in unseen]
    vectors = embed_batch(texts)

    # ── Resolve provider metadata for storage ────────────────────────────── #
    provider = get_provider()
    # Derive provider name and model from the class + its config if available
    provider_name = type(provider).__name__.replace("Provider", "").lower()
    provider_model = getattr(getattr(provider, "_cfg", None), "model", "unknown")

    # ── Persist embeddings ────────────────────────────────────────────────── #
    for chunk_meta, vector in zip(unseen, vectors):
        insert_embedding(
            chunk_id=chunk_meta["chunk_id"],
            chunk_hash=chunk_meta["chunk_hash"],
            vector=vector,
            provider=provider_name,
            model=provider_model,
        )

    logger.info(
        f"[embedding_pipeline] Persisted {len(unseen)} embeddings "
        f"for document {document_id}."
    )
    return len(unseen)
