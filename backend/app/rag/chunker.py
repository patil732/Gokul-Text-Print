"""
app/rag/chunker.py
------------------
Sprint 4 Step 2 — RAG Knowledge Engine

Token-aware text chunking with overlap.

Algorithm
---------
Given a list of page dicts (output of ``loader.extract_pages()``), the chunker
concatenates page text in order and produces chunks of approximately
``target_tokens`` words, each overlapping the previous chunk by ``overlap_tokens``
words.

Token approximation
-------------------
We use ``len(text.split())`` as a word count and treat 1 word ≈ 1 token.
For typical English business text, words average ~1.3 sub-word tokens (BPE),
so a 500-word chunk maps to ~650 actual LLM tokens — well within the 1 024-token
embedding windows of most models.  A heavy tokenizer (tiktoken, sentencepiece)
can replace this function if exact token counts become important.

Public API
----------
    from app.rag.chunker import chunk_pages

    chunks = chunk_pages(pages, target_tokens=500, overlap_tokens=50)
    # [
    #   {"chunk_index": 0, "page_number": 1, "chunk_text": "..."},
    #   {"chunk_index": 1, "page_number": 1, "chunk_text": "..."},
    #   ...
    # ]
"""

from __future__ import annotations

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

from utils.logger import logger  # noqa: E402


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def chunk_pages(
    pages: list[dict[str, Any]],
    target_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[dict[str, Any]]:
    """
    Split a list of page texts into overlapping token-sized chunks.

    Parameters
    ----------
    pages : list[dict]
        Output of ``loader.extract_pages()``.  Each element must have keys
        ``"page_number"`` (int, 1-based) and ``"text"`` (str).
    target_tokens : int
        Approximate number of words per chunk.  Default 500.
    overlap_tokens : int
        Number of words from the end of a chunk to prepend to the next chunk.
        Default 50.  Must be less than ``target_tokens``.

    Returns
    -------
    list[dict]
        Each element is::

            {
                "chunk_index":  <int>,  # 0-based position in the document
                "page_number":  <int>,  # 1-based page the chunk starts on
                "chunk_text":   <str>,  # text content of the chunk
            }

        Returns an empty list if *pages* is empty or contains no text.

    Raises
    ------
    ValueError
        If ``overlap_tokens >= target_tokens``.
    """
    if not pages:
        logger.warning("[chunker] No pages provided — returning empty chunk list.")
        return []

    if overlap_tokens >= target_tokens:
        raise ValueError(
            f"[chunker] overlap_tokens ({overlap_tokens}) must be less than "
            f"target_tokens ({target_tokens})."
        )

    # ── Build a flat token list with page-number annotations ─────────────── #
    # Each element: (word_string, page_number)
    annotated_tokens: list[tuple[str, int]] = []
    for page in pages:
        words = page["text"].split()
        page_num = page["page_number"]
        annotated_tokens.extend((w, page_num) for w in words)

    if not annotated_tokens:
        logger.warning("[chunker] All pages were empty — no chunks produced.")
        return []

    # ── Sliding-window chunking ───────────────────────────────────────────── #
    chunks: list[dict[str, Any]] = []
    pos    = 0
    total  = len(annotated_tokens)

    while pos < total:
        end = min(pos + target_tokens, total)

        window       = annotated_tokens[pos:end]
        chunk_text   = " ".join(w for w, _ in window)
        # page_number is the page where this chunk *starts*
        page_number  = window[0][1]

        chunks.append(
            {
                "chunk_index": len(chunks),
                "page_number": page_number,
                "chunk_text":  chunk_text,
            }
        )

        # Advance by (target - overlap) so the next chunk reuses the last
        # overlap_tokens words of the current chunk.
        step = target_tokens - overlap_tokens
        pos += step

    logger.info(
        f"[chunker] Produced {len(chunks)} chunks "
        f"(target={target_tokens}, overlap={overlap_tokens}) "
        f"from {len(annotated_tokens)} tokens across {len(pages)} pages."
    )
    return chunks
