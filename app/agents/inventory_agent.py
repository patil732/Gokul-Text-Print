"""
app/agents/inventory_agent.py
------------------------------
Sprint 5 — Inventory Domain Sub-Agent

Concrete implementation of BaseAgent for the Inventory domain.

Calls exclusively Sprint 3 endpoints:
  - GET  /api/ml/inventory/predict
  - POST /api/ml/inventory/predict  (with feature payload when available)
  - GET  /api/ml/inventory/metrics  (for model metadata)

Design constraints:
  - Zero references to Sales or Knowledge modules/APIs.
  - execute() returns AgentResponse with strictly structured data dict —
    NEVER natural-language prose.
  - can_handle() is purely keyword/intent based; makes no LLM call.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.agents.base import call_api
from app.agents.base_agent import AgentResponse, BaseAgent
from utils.logger import logger

# ---------------------------------------------------------------------------
# Intent keywords — purely string-based, no LLM call
# ---------------------------------------------------------------------------
_INVENTORY_KEYWORDS: frozenset[str] = frozenset({
    "stock", "stocks", "inventory", "inventories", "reorder", "restock", "restocking",
    "warehouse", "storage", "stockout", "out of stock", "supply", "supplies",
    "replenish", "replenishment", "safety stock", "buffer", "shelf",
    "remaining", "days left", "fulfillment", "fulfil", "fulfill",
    "procurement", "purchase", "raw material", "materials", "thread",
    "dye", "fabric level", "available", "availability", "production gap",
    "turnover", "dead stock", "fast moving", "slow moving",
})

# Decision labels returned by the inventory ML model
_CRITICAL_DECISIONS: frozenset[str] = frozenset({
    "reorder required", "stockout risk",
})


class InventoryAgent(BaseAgent):
    """
    Inventory domain agent that retrieves and structures Sprint 3 inventory intelligence.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url

    # ------------------------------------------------------------------
    # BaseAgent contract
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "inventory"

    def can_handle(self, query: str) -> bool:
        """
        Return True if the query mentions any inventory-domain keyword.

        Pure keyword/intent matching — no LLM invoked.
        """
        if not query or not query.strip():
            return False
        normalised = re.sub(r"[^a-z0-9 ]", " ", query.lower())
        words = set(normalised.split())
        # Single-word and phrase matches
        if words & _INVENTORY_KEYWORDS:
            return True
        # Multi-word phrase check (e.g. "out of stock", "safety stock")
        for phrase in _INVENTORY_KEYWORDS:
            if " " in phrase and phrase in normalised:
                return True
        return False

    def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Query Sprint 3 inventory endpoints and return a strictly structured AgentResponse.

        Structured data keys
        --------------------
        stock_health       : str   — "Critical" | "Warning" | "Healthy"
        remaining_days     : int   — estimated days before stockout (−1 = unknown)
        recommendation     : str   — categorical action (≤ 5 words)
        decision           : str   — raw ML model decision label
        confidence         : float — model probability score 0–1
        confidence_level   : str   — "High" | "Medium" | "Low"
        model_version      : str   — registered model version tag
        model_type         : str   — e.g. "xgboost"
        model_accuracy     : float — training accuracy
        """
        ctx = context or {}
        logger.info("[InventoryAgent] execute() → querying inventory prediction endpoint")

        try:
            # Primary: GET prediction (no user features available from context)
            inv_res = call_api(
                "/api/ml/inventory/predict",
                method="GET",
                base_url=self._base_url,
            )

            # Secondary: GET model metrics for metadata enrichment
            metrics_res = call_api(
                "/api/ml/inventory/metrics",
                method="GET",
                base_url=self._base_url,
            )
        except Exception as exc:
            logger.error(f"[InventoryAgent] API call failed: {exc}")
            return AgentResponse(
                agent_name=self.name,
                status="error",
                data={},
                confidence=0.0,
                error=str(exc),
            )

        # ── Parse prediction response ────────────────────────────────── #
        pred = inv_res if isinstance(inv_res, dict) else {}
        metrics = metrics_res.get("metrics", {}) if isinstance(metrics_res, dict) else {}

        decision: str = str(pred.get("decision") or "Stock Sufficient")
        prob: float = round(float(pred.get("probability") or 0.5), 4)
        confidence_str: str = str(pred.get("confidence") or "Medium")
        model_version: str = str(
            pred.get("version")
            or (metrics_res.get("version") if isinstance(metrics_res, dict) else "v1.0")
            or "v1.0"
        )
        model_type: str = str(
            (metrics_res.get("model_type") if isinstance(metrics_res, dict) else None)
            or pred.get("model_status", {}).get("model_type", "xgboost")
            or "xgboost"
        )
        model_accuracy: float = round(
            float(
                (metrics_res.get("accuracy") if isinstance(metrics_res, dict) else None)
                or pred.get("model_status", {}).get("accuracy", 0.0)
                or 0.0
            ),
            4,
        )

        # ── Derive structured business metrics from ML decision ───────── #
        decision_lower = decision.lower()
        if decision_lower in _CRITICAL_DECISIONS:
            stock_health = "Critical"
            remaining_days = 4
            recommendation = "Restock Immediately"
        elif "warning" in decision_lower or "low" in decision_lower:
            stock_health = "Warning"
            remaining_days = 10
            recommendation = "Schedule Reorder"
        else:
            stock_health = "Healthy"
            remaining_days = 28
            recommendation = "Maintain Replenishment Cycle"

        api_ok = pred.get("status") == "success"

        structured_data: Dict[str, Any] = {
            "stock_health": stock_health,
            "remaining_days": remaining_days,
            "recommendation": recommendation,
            "decision": decision,
            "confidence_level": confidence_str,
            "model_version": model_version,
            "model_type": model_type,
            "model_accuracy": model_accuracy,
        }

        return AgentResponse(
            agent_name=self.name,
            status="success" if api_ok else "warning",
            data=structured_data,
            confidence=prob,
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
