"""
app/rag/vector_store.py
------------------------
Sprint 4 Step 4 — RAG Knowledge Engine

FAISS-backed vector index for chunk similarity search.

Architecture
------------
- Vectors from ``chunk_embeddings`` are L2-normalised before insertion so that
  FAISS inner-product (FlatIP) equals cosine similarity.
- A module-level singleton (``_INDEX_CACHE``) holds the built index and a
  monotonic timestamp.  On each ``get_index()`` call the cache age is checked
  against ``cache_ttl_seconds``; if expired OR the dirty flag is set, the index
  is rebuilt from the database.
- ``invalidate_index()`` sets the dirty flag instantly so a new upload is
  visible on the very next search request without a server restart.

Public API
----------
    from app.rag.vector_store import get_index, search_index, invalidate_index

    index, chunk_ids = get_index()
    results = search_index(index, chunk_ids, query_vector, top_k=5)
    # results = [{"chunk_id": "...", "score": 0.94}, ...]

Performance targets
-------------------
- FlatIP index build: <100ms for 10k 384-dim vectors.
- FlatIP search:      <5ms   for 10k 384-dim vectors.
- Full rebuild is only triggered once after startup and once per upload.
"""

from __future__ import annotations

import json
import os
import sys
import threading
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

try:
    import faiss
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "faiss-cpu is required for vector search. "
        "Install it with: pip install faiss-cpu"
    ) from exc

_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")


# --------------------------------------------------------------------------- #
# Config helper
# --------------------------------------------------------------------------- #

def _load_search_config() -> dict[str, Any]:
    raw = load_config(_CONFIG_PATH)
    return raw.get("rag", {}).get("search", {})


# --------------------------------------------------------------------------- #
# Index singleton cache
# --------------------------------------------------------------------------- #

class _IndexCache:
    """Thread-safe container for the FAISS index singleton."""

    def __init__(self) -> None:
        self._lock      = threading.Lock()
        self._index     = None          # faiss.Index | None
        self._chunk_ids: list[str] = []  # positional map: FAISS row → chunk_id
        self._built_at  = 0.0           # monotonic timestamp of last build
        self._dirty     = True          # True → rebuild on next access

    # ── Invalidation ────────────────────────────────────────────────────────── #

    def invalidate(self) -> None:
        """Mark the cache dirty so the next get() rebuilds the index."""
        with self._lock:
            self._dirty = True
        logger.debug("[vector_store] Index cache invalidated.")

    # ── Access ──────────────────────────────────────────────────────────────── #

    def get(self, ttl: float) -> tuple:
        """
        Return ``(index, chunk_ids)``, rebuilding if needed.

        Parameters
        ----------
        ttl : float
            Cache lifetime in seconds.  0 means never expire (rely on dirty flag).
        """
        with self._lock:
            age     = time.monotonic() - self._built_at
            expired = (ttl > 0) and (age > ttl)

            if self._dirty or expired:
                self._rebuild()

        return self._index, self._chunk_ids

    # ── Internal rebuild ────────────────────────────────────────────────────── #

    def _rebuild(self) -> None:
        """Build a fresh FAISS index from ``chunk_embeddings``.  Caller holds lock."""
        t0 = time.monotonic()
        vectors, chunk_ids = _load_all_embeddings()

        if not chunk_ids:
            logger.warning("[vector_store] No embeddings in DB — index is empty.")
            self._index     = None
            self._chunk_ids = []
        else:
            dim   = len(vectors[0])
            mat   = _l2_normalise(np.array(vectors, dtype=np.float32))
            index = faiss.IndexFlatIP(dim)
            index.add(mat)

            self._index     = index
            self._chunk_ids = chunk_ids
            logger.info(
                f"[vector_store] Index built: {len(chunk_ids)} vectors, "
                f"dim={dim}, elapsed={1000*(time.monotonic()-t0):.1f}ms"
            )

        self._built_at = time.monotonic()
        self._dirty    = False

    def inject(self, index, chunk_ids: list[str]) -> None:
        """
        Directly set the index (used in tests to bypass DB loading).
        """
        with self._lock:
            self._index     = index
            self._chunk_ids = chunk_ids
            self._built_at  = time.monotonic()
            self._dirty     = False


_CACHE = _IndexCache()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _l2_normalise(mat: np.ndarray) -> np.ndarray:
    """
    L2-normalise each row of *mat* in place.

    After normalisation, FAISS inner-product = cosine similarity.
    Zero-norm rows are left as-is (avoid division by zero).
    """
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return (mat / norms).astype(np.float32)


def _load_all_embeddings() -> tuple[list[list[float]], list[str]]:
    """
    Fetch all rows from ``chunk_embeddings`` and return parallel lists.

    Returns
    -------
    vectors : list[list[float]]
    chunk_ids : list[str]
        Positional map: ``vectors[i]`` belongs to ``chunk_ids[i]``.
    """
    from database.db import get_db_connection  # local import — avoids circular deps

    conn = get_db_connection()
    rows = conn.execute(
        "SELECT chunk_id, embedding FROM chunk_embeddings ORDER BY rowid ASC"
    ).fetchall()
    conn.close()

    vectors:   list[list[float]] = []
    chunk_ids: list[str]         = []
    target_dim: int | None       = None

    for row in rows:
        try:
            vec = json.loads(row["embedding"])
            if not isinstance(vec, list) or not vec:
                continue
            if target_dim is not None and len(vec) != target_dim:
                logger.warning(
                    f"[vector_store] Skipping embedding with mismatched dimension "
                    f"({len(vec)} != {target_dim}) for chunk {row['chunk_id']}"
                )
                continue
            vectors.append(vec)
            chunk_ids.append(row["chunk_id"])
            if target_dim is None:
                target_dim = len(vec)
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                f"[vector_store] Skipping malformed embedding for "
                f"chunk {row['chunk_id']}: {exc}"
            )

    return vectors, chunk_ids



# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def build_index(
    vectors:   list[list[float]],
    chunk_ids: list[str],
) -> tuple:
    """
    Build a FAISS FlatIP index from *vectors* and return ``(index, chunk_ids)``.

    Vectors are L2-normalised before insertion so inner-product = cosine similarity.
    This function is *stateless* — it does **not** update the module-level cache.
    Use ``get_index()`` for the cached singleton.

    Parameters
    ----------
    vectors : list[list[float]]
        Raw embedding vectors (any L2 norm — will be normalised internally).
    chunk_ids : list[str]
        One chunk UUID per vector, in the same order.

    Returns
    -------
    (faiss.Index, list[str])
        The populated index and the chunk_id positional map.
    """
    if not vectors:
        return None, []

    dim = len(vectors[0])
    mat = _l2_normalise(np.array(vectors, dtype=np.float32))
    idx = faiss.IndexFlatIP(dim)
    idx.add(mat)
    return idx, chunk_ids


def get_index() -> tuple:
    """
    Return the cached ``(index, chunk_ids)`` singleton, rebuilding if stale.

    Returns
    -------
    (faiss.Index | None, list[str])
        ``index`` is ``None`` when no embeddings exist in the database yet.
    """
    cfg = _load_search_config()
    ttl = float(cfg.get("cache_ttl_seconds", 300))
    return _CACHE.get(ttl)


def invalidate_index() -> None:
    """
    Mark the index cache as dirty.

    Call this after a successful upload so the newly added chunks are visible
    on the next ``get_index()`` call without a server restart.
    """
    _CACHE.invalidate()


def inject_index(index, chunk_ids: list[str]) -> None:
    """
    Directly inject a pre-built index into the cache (for tests).

    Bypasses DB loading and TTL expiry.
    """
    _CACHE.inject(index, chunk_ids)


def search_index(
    index,
    chunk_ids: list[str],
    query_vector: list[float],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Search *index* for the *top_k* nearest neighbours of *query_vector*.

    Parameters
    ----------
    index : faiss.Index
        Populated FAISS index (from ``get_index()`` or ``build_index()``).
    chunk_ids : list[str]
        Positional chunk-ID map matching the index rows.
    query_vector : list[float]
        Raw query embedding (will be L2-normalised internally).
    top_k : int
        Number of results to return.

    Returns
    -------
    list[dict]
        Each element: ``{"chunk_id": str, "score": float}``
        Ordered by descending score (most similar first).
        Returns ``[]`` if *index* is ``None`` or *chunk_ids* is empty.
    """
    if index is None or not chunk_ids:
        return []

    k_actual = min(top_k, len(chunk_ids))

    q = _l2_normalise(
        np.array([query_vector], dtype=np.float32)
    )

    scores, indices = index.search(q, k_actual)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(chunk_ids):  # FAISS returns -1 for padded slots
            continue
        results.append({
            "chunk_id": chunk_ids[idx],
            "score":    float(score),
        })

    return results
