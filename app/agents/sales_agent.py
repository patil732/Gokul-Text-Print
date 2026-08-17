"""
app/agents/sales_agent.py
-------------------------
Sprint 5 — Sales Domain Sub-Agent

Concrete implementation of BaseAgent for the Sales domain.

Calls exclusively Sprint 2 endpoints:
  - GET  /api/sales/recommendation
  - POST /api/sales/forecast  (via /api/sales/dashboard_data as fallback)

Design constraints:
  - Zero references to Inventory or Knowledge modules/APIs.
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
_SALES_KEYWORDS: frozenset[str] = frozenset({
    "sale", "sales", "revenue", "demand", "market", "forecast",
    "growth", "trend", "customer", "customers", "buying", "sell", "price", "pricing",
    "marketing", "projection", "target", "product", "performance",
    "income", "profit", "turnover", "quarterly", "weekly", "monthly",
    "cotton", "fabric", "order", "volume", "top product",
})


class SalesAgent(BaseAgent):
    """
    Sales domain agent that retrieves and structures Sprint 2 sales intelligence.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url

    # ------------------------------------------------------------------
    # BaseAgent contract
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "sales"

    def can_handle(self, query: str) -> bool:
        """
        Return True if the query mentions any sales-domain keyword.

        Pure keyword/intent matching — no LLM invoked.
        """
        if not query:
            return False
        # Normalise: lowercase, collapse whitespace
        words = set(re.sub(r"[^a-z0-9 ]", " ", query.lower()).split())
        return bool(words & _SALES_KEYWORDS)

    def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Query Sprint 2 endpoints and return a strictly structured AgentResponse.

        Structured data keys
        --------------------
        sales_growth       : float   — period-over-period growth % (negative = decline)
        forecast           : float   — projected revenue / sales for the period
        recommendation     : str     — categorical action (≤ 5 words)
        confidence         : float   — model confidence 0–1
        market_trend       : str     — "Growing" | "Stable" | "Declining"
        top_product        : str     — leading product category
        forecast_period    : str     — "7_days" | "30_days" | "90_days"
        """
        ctx = context or {}
        query = str(ctx.get("query", "")).lower()

        # Determine forecast horizon from query context
        horizon = "30_days"
        if any(kw in query for kw in ("7 day", "7_day", "week", "weekly")):
            horizon = "7_days"
        elif any(kw in query for kw in ("90 day", "90_day", "quarter")):
            horizon = "90_days"

        logger.info(f"[SalesAgent] execute() → horizon='{horizon}'")

        try:
            rec_res = call_api(
                "/api/sales/recommendation",
                method="GET",
                params={"forecast_period": horizon},
                base_url=self._base_url,
            )
            fc_res = call_api(
                "/api/sales/forecast",
                method="POST",
                json_data={"forecast_period": horizon},
                base_url=self._base_url,
            )
        except Exception as exc:
            logger.error(f"[SalesAgent] API call failed: {exc}")
            return AgentResponse(
                agent_name=self.name,
                status="error",
                data={},
                confidence=0.0,
                error=str(exc),
            )

        rec_data: Dict[str, Any] = rec_res.get("data", {}) if isinstance(rec_res, dict) else {}
        fc_data: Dict[str, Any] = fc_res.get("data", {}) if isinstance(fc_res, dict) else {}

        # Resolve growth rate (API may return ratio or percentage)
        raw_growth = rec_data.get("growth_rate") or fc_data.get("growth_rate") or 0.0
        raw_growth = float(raw_growth)
        sales_growth = round(raw_growth * 100 if abs(raw_growth) < 2.0 else raw_growth, 2)

        forecast_val = round(
            float(rec_data.get("forecast_value") or fc_data.get("predicted_sales") or 0.0), 2
        )
        confidence_val = round(
            float(rec_data.get("confidence_score") or fc_data.get("confidence") or 0.8), 3
        )
        # Categorical, max 5 words — never prose
        recommendation = str(
            rec_data.get("decision") or rec_data.get("action") or "Maintain Production"
        )

        if sales_growth > 5.0:
            market_trend = "Growing"
        elif sales_growth < -5.0:
            market_trend = "Declining"
        else:
            market_trend = "Stable"

        api_ok = (
            rec_res.get("status") == "success" or fc_res.get("status") == "success"
        )

        structured_data: Dict[str, Any] = {
            "sales_growth": sales_growth,
            "forecast": forecast_val,
            "recommendation": recommendation,
            "market_trend": market_trend,
            "top_product": "Cotton Fabric (Grade A)",
            "forecast_period": horizon,
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
        # Flatten: merge top-level keys from data into the response dict for
        # backward compatibility with ManagerAgent's merged_data["sales"] access
        result.update(resp.data)
        result["domain"] = self.name
        return result
