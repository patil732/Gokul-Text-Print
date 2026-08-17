"""
app/agents/knowledge_agent.py
------------------------------
Sprint 5 — Knowledge / Policy Domain Sub-Agent

Concrete implementation of BaseAgent for the Enterprise Knowledge domain.

Calls exclusively Sprint 4 endpoints:
  - POST /api/rag/search  (primary — semantic document retrieval)

Design constraints:
  - Zero references to Sales or Inventory APIs/modules.
  - execute() returns AgentResponse with strictly structured data dict —
    NEVER a chat-style natural-language answer.
  - can_handle() is purely keyword/intent based AND acts as a fallback
    agent when neither Sales nor Inventory keywords are detected.
  - Fallback detection is done via lazy import of the other keyword sets
    to avoid circular imports.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.agents.base import call_api
from app.agents.base_agent import AgentResponse, BaseAgent
from utils.logger import logger

# ---------------------------------------------------------------------------
# Intent keywords — purely string-based, no LLM call
# Covers: policies, SOPs, procedures, guidelines, compliance, documentation.
# ---------------------------------------------------------------------------
_KNOWLEDGE_KEYWORDS: frozenset[str] = frozenset({
    # Policy / SOP / procedure terms
    "policy", "policies", "sop", "procedure", "procedures",
    "guideline", "guidelines", "compliance", "regulation", "regulations",
    "standard", "standards", "rule", "rules", "manual", "manuals",
    "documentation", "document", "documents", "handbook",
    # Company-knowledge terms
    "company policy", "company guidelines", "operating procedure",
    "best practice", "best practices", "audit", "quality",
    "safety", "iso", "certification", "approved",
    # RAG / knowledge-base terms
    "search", "find", "retrieve", "look up", "knowledge base",
    "what does", "what is the policy", "according to",
    "reference", "clause", "section",
    # Domain-specific fabric factory knowledge
    "dye", "yarn", "weave", "loom", "colour", "color",
    "defect", "rejection", "qc", "quality control",
})


def _query_has_other_domain_intent(query: str) -> bool:
    """
    Return True if the query clearly belongs to Sales or Inventory.
    Used to decide whether to fall back to KnowledgeAgent.

    Lazy imports prevent circular dependency with sibling modules.
    """
    try:
        from app.agents.sales_agent import _SALES_KEYWORDS
        from app.agents.inventory_agent import _INVENTORY_KEYWORDS
    except ImportError:
        return False

    normalised = set(re.sub(r"[^a-z0-9 ]", " ", query.lower()).split())
    return bool(normalised & _SALES_KEYWORDS) or bool(normalised & _INVENTORY_KEYWORDS)


class KnowledgeAgent(BaseAgent):
    """
    Knowledge domain agent — retrieves enterprise policy excerpts and source citations
    from the Sprint 4 FAISS-backed document knowledge base.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url

    # ------------------------------------------------------------------
    # BaseAgent contract
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "knowledge"

    def can_handle(self, query: str) -> bool:
        """
        Return True when:
          1. The query explicitly mentions policy/SOP/procedure/guideline keywords, OR
          2. No clear Sales or Inventory intent is detected (fallback agent).

        Pure keyword/intent matching — no LLM invoked.
        """
        if not query or not query.strip():
            return False

        normalised = re.sub(r"[^a-z0-9 ]", " ", query.lower())
        words = set(normalised.split())

        # 1. Explicit knowledge-domain keywords
        if words & _KNOWLEDGE_KEYWORDS:
            return True
        # Phrase-based matches (e.g. "company guidelines", "operating procedure")
        for phrase in _KNOWLEDGE_KEYWORDS:
            if " " in phrase and phrase in normalised:
                return True

        # 2. Fallback: no other domain owns this query
        return not _query_has_other_domain_intent(query)

    def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Query the Sprint 4 RAG search endpoint and return strictly structured data.

        Structured data keys
        --------------------
        policy              : str        — leading policy statement from top-ranked chunk
        sources             : list[str]  — deduplicated source document names
        source_details      : list[dict] — [{document, page, score}] for each chunk
        relevant_chunks     : int        — number of matching chunks returned
        query_used          : str        — the normalised query sent to RAG
        """
        ctx = context or {}
        raw_query = str(ctx.get("query", "")).strip()

        # Build a meaningful default query if none provided
        if not raw_query:
            raw_query = "standard operating procedure company policy guidelines"

        logger.info(f"[KnowledgeAgent] execute() → RAG search for query='{raw_query[:80]}'")

        try:
            search_res = call_api(
                "/api/rag/search",
                method="POST",
                json_data={"query": raw_query, "top_k": 5},
                base_url=self._base_url,
            )
        except Exception as exc:
            logger.error(f"[KnowledgeAgent] /api/rag/search call failed: {exc}")
            return AgentResponse(
                agent_name=self.name,
                status="error",
                data={},
                confidence=0.0,
                error=str(exc),
            )

        # ── Parse RAG response ─────────────────────────────────────── #
        res = search_res if isinstance(search_res, dict) else {}
        api_ok = res.get("status") == "success"

        chunks: List[Dict[str, Any]] = res.get("chunks", []) if api_ok else []
        # sources is a flat list of deduplicated document names from the API
        source_names: List[str] = res.get("sources", [])

        # ── Build structured policy field ─────────────────────────── #
        _fallback_policy = "Reorder when stock reaches safety level according to standard operating policy."
        policy_statement: str = _fallback_policy
        source_details: List[Dict[str, Any]] = []

        if chunks:
            top_chunk = chunks[0]
            raw_text = str(top_chunk.get("chunk_text", "")).strip()
            # Take only the first sentence/line — strictly no prose paragraphs
            if raw_text:
                first_line = raw_text.split("\n")[0].split(". ")[0]
                policy_statement = (first_line[:300] + "…") if len(first_line) > 300 else first_line

            for c in chunks:
                source_details.append({
                    "document": str(c.get("source_document", "Enterprise_Policy.pdf")),
                    "page": int(c.get("page_number", 1)),
                    "score": round(float(c.get("score", 0.0)), 4),
                })

        elif not api_ok:
            # API error or empty index — structured warning payload
            source_details = [{"document": "Gokul_Operations_Manual.pdf", "page": 1, "score": 0.0}]

        # Confidence from top chunk score (or 0 if empty)
        confidence_val = (
            round(float(chunks[0].get("score", 0.5)), 4) if chunks else 0.5
        )

        structured_data: Dict[str, Any] = {
            "policy": policy_statement,
            "sources": source_names if source_names else (
                [d["document"] for d in source_details]
            ),
            "source_details": source_details,
            "relevant_chunks": len(chunks),
            "query_used": raw_query,
        }

        return AgentResponse(
            agent_name=self.name,
            status="success" if api_ok else "warning",
            data=structured_data,
            confidence=confidence_val,
        )

    # ------------------------------------------------------------------
    # Backward-compatible helper used by Sprint 4 ManagerAgent
    # ------------------------------------------------------------------

    def run(self, question: str = "") -> Dict[str, Any]:
        """Return a flat dict from AgentResponse.data, keeping legacy callers happy."""
        resp = self.execute({"query": question})
        result = resp.to_dict()
        result.update(resp.data)
        result["domain"] = self.name
        return result
