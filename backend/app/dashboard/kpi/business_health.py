"""
app/dashboard/kpi/business_health.py
------------------------------------
Sprint 6 — Executive BI Dashboard: Business Health Score Engine

Calculates a single composite "Business Health Score" (0 to 100) using a
transparent, deterministic weighted formula combining:
  1. Sales Growth Metric (weight: 40%)
  2. Inventory Health Metric & Low-Stock Risk (weight: 40%)
  3. Actionable Alert / Recommendation Load (weight: 20%)

Formula
-------
  Business Health Score = (0.40 * sales_score) + (0.40 * inventory_score) + (0.20 * alert_score)

Status Grades
-------------
  - >= 80.0 : "Excellent"
  - >= 65.0 : "Good"
  - >= 50.0 : "Fair"
  - <  50.0 : "Needs Attention"
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class HealthScoreBreakdown:
    score: float
    status: str
    sales_score: float
    inventory_score: float
    alert_score: float
    formula: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_sales_score(sales_growth: float) -> float:
    """
    Map sales growth percentage to a 0–100 scale.
    0.0% growth is neutral (50.0).
    +20% or above reaches 100.0.
    -20% or below drops to 0.0.
    """
    try:
        growth = float(sales_growth)
    except (ValueError, TypeError):
        growth = 0.0

    # 50 + (growth * 2.5): e.g. +10% -> 75, -10% -> 25
    score = 50.0 + (growth * 2.5)
    return round(max(0.0, min(100.0, score)), 2)


def calculate_inventory_score(
    inventory_health: str,
    low_stock_count: int = 0,
) -> float:
    """
    Map inventory health and low-stock product count to a 0–100 scale.

    Base values:
      - "Healthy" / "Stock Sufficient": 95.0
      - "Warning": 60.0
      - "Critical" / "Reorder Required": 35.0
      - Other / Unknown: 70.0

    Each low stock product applies a small risk penalty of 2.0 points.
    """
    health_norm = str(inventory_health).strip().lower()
    if health_norm in ("healthy", "stock sufficient", "optimal"):
        base = 95.0
    elif health_norm in ("warning", "caution"):
        base = 60.0
    elif health_norm in ("critical", "reorder required", "high risk", "stockout risk"):
        base = 35.0
    else:
        base = 70.0

    penalty = max(0, int(low_stock_count)) * 2.0
    score = max(0.0, base - penalty)
    return round(min(100.0, score), 2)


def calculate_alert_score(recommendations_count: int = 0) -> float:
    """
    Map the number of active warning alerts and urgent recommendations to a 0–100 scale.
    Fewer alerts indicate smooth, unhindered operations.
    """
    try:
        count = max(0, int(recommendations_count))
    except (ValueError, TypeError):
        count = 0

    if count == 0:
        return 100.0
    elif count == 1:
        return 85.0
    elif count == 2:
        return 75.0
    elif count == 3:
        return 60.0
    elif count == 4:
        return 45.0
    else:
        return round(max(10.0, 45.0 - (count - 4) * 5.0), 2)


def compute_business_health(
    sales_growth: float = 0.0,
    inventory_health: Optional[str] = None,
    low_stock_count: int = 0,
    recommendations_count: int = 0,
    **kwargs: Any,
) -> HealthScoreBreakdown:
    """
    Compute composite Business Health Score and categorical status.
    """
    resolved_inv_health = inventory_health or kwargs.get("stock_health") or "Healthy"
    resolved_recs_count = recommendations_count or kwargs.get("alerts_count") or 0

    sales_score = calculate_sales_score(sales_growth)
    inv_score = calculate_inventory_score(resolved_inv_health, low_stock_count)
    alert_score = calculate_alert_score(resolved_recs_count)

    # Transparent weighted formula
    composite = (0.40 * sales_score) + (0.40 * inv_score) + (0.20 * alert_score)
    composite = round(max(0.0, min(100.0, composite)), 1)

    if composite >= 80.0:
        status = "Excellent"
    elif composite >= 65.0:
        status = "Good"
    elif composite >= 50.0:
        status = "Fair"
    else:
        status = "Needs Attention"

    formula_str = (
        f"0.40 * sales_score ({sales_score}) + "
        f"0.40 * inventory_score ({inv_score}) + "
        f"0.20 * alert_score ({alert_score}) = {composite}"
    )

    return HealthScoreBreakdown(
        score=composite,
        status=status,
        sales_score=sales_score,
        inventory_score=inv_score,
        alert_score=alert_score,
        formula=formula_str,
    )
