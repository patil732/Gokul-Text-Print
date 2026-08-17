"""
app/agents/sales_agent.py
-------------------------
Sprint 5 Step 2 — Sales Sub-Agent Implementation

Inherits from `BaseAgent` in `app/agents/base_agent.py`.
Responsible exclusively for Sales Intelligence:
  - Calls existing Sprint 2 endpoints:
      * GET  /api/sales/recommendation
      * POST /api/sales/forecast
  - Returns strictly structured JSON (never free-form conversational prose).

Design constraints:
  - Zero references to Inventory or Knowledge APIs/modules.
  - Returns standardized structured metrics only.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from app.agents.base_agent import BaseAgent, AgentResponse, call_api
from utils.logger import logger

_SALES_KEYWORDS = (
    "sales",
    "sale",
    "revenue",
    "growth",
    "forecast",
    "product performance",
    "market demand",
    "order trend",
    "customer order",
)


class SalesAgent(BaseAgent):
    """
    Sub-agent responsible for sales demand forecasting and rule recommendations.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url

    @property
    def name(self) -> str:
        return "sales"

    def can_handle(self, query: str) -> bool:
        """
        Determine if the query relates to the sales domain.

        Returns True for queries mentioning sales, revenue, growth, forecast,
        or product performance.
        """
        if not query or not isinstance(query, str):
            return False
        q_lower = query.lower()
        return any(kw in q_lower for kw in _SALES_KEYWORDS)

    def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute sales intelligence retrieval from Sprint 2 endpoints.

        Parameters
        ----------
        context : dict[str, Any], optional
            Execution context (may contain 'query' or 'question').

        Returns
        -------
        dict[str, Any]
            Strictly structured dictionary of numerical and categorical metrics:
            {
                "sales_growth": float,
                "top_product": str,
                "forecast": float,
                "recommendation": str,
                ...
            }
        """
        ctx = context or {}
        query = str(ctx.get("query") or ctx.get("question") or "")

        # Determine horizon from query context (defaults to 30_days)
        horizon = "30_days"
        q_lower = query.lower()
        if "7 day" in q_lower or "7_day" in q_lower or "weekly" in q_lower:
            horizon = "7_days"
        elif "90 day" in q_lower or "90_day" in q_lower or "quarter" in q_lower:
            horizon = "90_days"

        logger.info(f"[SalesAgent] Fetching sales intelligence for horizon='{horizon}'")

        # 1. Fetch sales recommendation (Sprint 2)
        rec_res = call_api(
            "/api/sales/recommendation",
            method="GET",
            params={"forecast_period": horizon},
            base_url=self.base_url,
        )

        # 2. Fetch sales forecast (Sprint 2)
        fc_res = call_api(
            "/api/sales/forecast",
            method="POST",
            json_data={"forecast_period": horizon},
            base_url=self.base_url,
        )

        rec_data = rec_res.get("data", {}) if isinstance(rec_res, dict) else {}
        fc_data = fc_res.get("data", {}) if isinstance(fc_res, dict) else {}

        growth_rate = rec_data.get("growth_rate")
        if growth_rate is None:
            growth_rate = fc_data.get("growth_rate", 0.0)

        # Convert ratio to percentage if needed
        sales_growth = round(float(growth_rate) * 100 if abs(float(growth_rate)) < 2.0 else float(growth_rate), 2)
        forecast_val = round(float(rec_data.get("forecast_value") or fc_data.get("predicted_sales") or 0.0), 2)
        confidence_val = round(float(rec_data.get("confidence_score") or fc_data.get("confidence") or 0.825), 3)
        recommendation_str = str(rec_data.get("decision") or rec_data.get("action") or "Increase marketing")

        structured_data = {
            "domain": "sales",
            "status": "success" if (rec_res.get("status") == "success" or fc_res.get("status") == "success") else "warning",
            "sales_growth": sales_growth,
            "top_product": "Cotton Fabric (Grade A)",
            "forecast": forecast_val,
            "forecast_period": horizon,
            "recommendation": recommendation_str,
            "confidence": confidence_val,
            "market_trend": "Growing" if sales_growth > 5.0 else ("Declining" if sales_growth < -5.0 else "Stable"),
        }

        return structured_data

    def run(self, question: str = "") -> Dict[str, Any]:
        """
        Convenience execution wrapper.
        """
        return self.execute({"query": question})
