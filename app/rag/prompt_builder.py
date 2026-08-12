"""
app/rag/prompt_builder.py
--------------------------
Sprint 4 Step 5 — RAG Chat Service

Pure-function prompt assembly — no state, no DB access, no LLM calls.

This module takes a question and a list of retrieved chunks (from retriever.py)
and produces the (system_prompt, user_message) pair that is sent to the LLM.

Design
------
- The system prompt instructs the LLM to:
    * Answer *only* from the provided context.
    * Cite every claim as [Source: <filename>, p.<page>].
    * Reply "I don't have enough information in the provided documents"
      when the context doesn't contain the answer.
- The user message contains a numbered context block so the model can
  reference [1], [2], … inline, followed by the question.
- Sources are derived from the chunk list by the caller (chat_service.py),
  NOT parsed from the LLM text — citation accuracy is deterministic.

Public API
----------
    from app.rag.prompt_builder import build_prompt

    system, user = build_prompt(question, chunks)
    # chunks: list of dicts with keys chunk_text, source_document, page_number
"""

from __future__ import annotations

_SYSTEM_TEMPLATE = """\
You are a helpful document assistant for a print and stationery business.
Your task is to answer the user's question using ONLY the context excerpts provided below.

Rules:
1. Base your answer exclusively on the provided context. Do not use external knowledge.
2. When you use information from a context excerpt, cite it inline as:
   [Source: <document name>, p.<page number>]
3. If the context does not contain enough information to answer the question,
   respond with exactly:
   "I don't have enough information in the provided documents to answer that question."
4. Be concise and factual. Do not speculate or invent details.
5. If multiple excerpts support the same point, cite all of them.\
"""

_CONTEXT_HEADER = "Context excerpts (use only these to answer):"
_QUESTION_LABEL = "Question:"
_SEPARATOR      = "-" * 60


def build_prompt(
    question: str,
    chunks:   list[dict],
) -> tuple[str, str]:
    """
    Assemble a (system_prompt, user_message) pair for the LLM.

    Parameters
    ----------
    question : str
        The user's natural-language question.
    chunks : list[dict]
        Retrieved chunks from ``retriever.retrieve()``.  Each dict must have:
        - ``chunk_text``      : str
        - ``source_document`` : str  (PDF filename)
        - ``page_number``     : int

    Returns
    -------
    (system_prompt, user_message) : tuple[str, str]

    Notes
    -----
    When *chunks* is empty the user message still contains the question,
    so the LLM can return the "not enough information" response gracefully.
    """
    context_lines: list[str] = [_CONTEXT_HEADER]

    for i, chunk in enumerate(chunks, start=1):
        source = chunk.get("source_document", "Unknown")
        page   = chunk.get("page_number",     0)
        text   = chunk.get("chunk_text",      "").strip()

        context_lines.append(
            f"\n[{i}] Source: {source}, p.{page}\n"
            f"    \"{text}\""
        )

    if not chunks:
        context_lines.append(
            "\n[No context excerpts available — the document index may be empty.]"
        )

    context_block = "\n".join(context_lines)
    user_message  = (
        f"{context_block}\n\n"
        f"{_SEPARATOR}\n\n"
        f"{_QUESTION_LABEL} {question}"
    )

    return _SYSTEM_TEMPLATE, user_message


def extract_sources(chunks: list[dict]) -> list[dict]:
    """
    Derive the unique, ordered source list from retrieved chunks.

    Deduplication key is ``(source_document, page_number)``.
    Order matches the chunk ranking from the retriever (highest score first).

    Parameters
    ----------
    chunks : list[dict]
        Same list passed to ``build_prompt()``.

    Returns
    -------
    list[dict]
        ``[{"document": str, "page": int}, ...]``
    """
    seen:    set[tuple]  = set()
    sources: list[dict]  = []

    for chunk in chunks:
        doc  = chunk.get("source_document", "")
        page = chunk.get("page_number",     0)
        key  = (doc, page)
        if key not in seen:
            seen.add(key)
            sources.append({"document": doc, "page": page})

    return sources
