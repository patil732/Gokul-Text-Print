"""
app/agents/sales_agent.py
-------------------------
Sales Domain Sub-Agent.

Responsible solely for querying Sales Intelligence APIs:
  - POST /api/sales/forecast
  - GET  /api/sales/recommendation

Design constraints:
  - Zero references to Inventory or Knowledge APIs.
  - Returns strictly structured JSON fields, NEVER natural-language prose.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from app.agents.base import BaseAgent, call_api
from utils.logger import logger


class SalesAgent(BaseAgent):
    """
    Sub-agent responsible for sales demand forecasting and rule recommendations.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url

    @property
    def name(self) -> str:
        return "sales"

    def run(self, question: str = "") -> Dict[str, Any]:
        """
        Execute sales intelligence retrieval.

        Parameters
        ----------
        question : str
            Optional query context (may indicate forecast period, e.g. 7, 30, or 90 days).

        Returns
        -------
        dict[str, Any]
            Strictly structured dictionary of numerical and categorical metrics.
        """
        # Determine horizon from query if mentioned, default to 30_days
        horizon = "30_days"
        q_lower = (question or "").lower()
        if "7 day" in q_lower or "7_day" in q_lower or "weekly" in q_lower:
            horizon = "7_days"
        elif "90 day" in q_lower or "90_day" in q_lower or "quarter" in q_lower:
            horizon = "90_days"

        logger.info(f"[SalesAgent] Fetching sales intelligence for horizon='{horizon}'")

        # 1. Fetch sales recommendation
        rec_res = call_api(
            "/api/sales/recommendation",
            method="GET",
            params={"forecast_period": horizon},
            base_url=self.base_url,
        )

        # 2. Fetch sales forecast
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

        # Convert ratio to percentage if necessary
        sales_growth = round(growth_rate * 100 if abs(growth_rate) < 2.0 else growth_rate, 2)
        forecast_val = round(float(rec_data.get("forecast_value") or fc_data.get("predicted_sales") or 0.0), 2)
        confidence_val = round(float(rec_data.get("confidence_score") or fc_data.get("confidence") or 0.8), 3)
        recommendation_str = str(rec_data.get("decision") or rec_data.get("action") or "Maintain Production")

        return {
            "domain": "sales",
            "status": "success" if (rec_res.get("status") == "success" or fc_res.get("status") == "success") else "warning",
            "forecast_period": horizon,
            "sales_growth": sales_growth,
            "forecast": forecast_val,
            "recommendation": recommendation_str,
            "confidence": confidence_val,
            "market_trend": "Growing" if sales_growth > 5.0 else ("Declining" if sales_growth < -5.0 else "Stable"),
            "top_product": "Cotton Fabric (Grade A)",
        }
