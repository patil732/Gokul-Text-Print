"""
app/dashboard/analytics/sales_analytics.py
-------------------------------------------
Sprint 6 — Executive BI Dashboard: Sales Analytics Engine

Provides chart-ready historical, grouped, and predictive sales analytics:
  - Daily, weekly, and monthly trend aggregation (revenue & volume)
  - Date-range filtering (start_date, end_date)
  - Product performance rankings and revenue share
  - Recent prediction history integration from Sprint 2 (sales_prediction_history)
  - Formatted Chart.js compatible series and raw point arrays
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

# Ensure project root is available on sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DASH_DIR = os.path.dirname(_THIS_DIR)
_APP_DIR = os.path.dirname(_DASH_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.db import get_db_connection
from utils.logger import logger


def _fetch_sales_prediction_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch recent sales forecast and recommendation records from the
    Sprint 2 sales_prediction_history SQLite table.
    """
    history: List[Dict[str, Any]] = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT prediction_id, prediction_date, forecast_period,
                   forecast_value, recommendation, confidence, model_version
            FROM sales_prediction_history
            ORDER BY prediction_date DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        for row in rows:
            history.append({
                "prediction_id": row["prediction_id"],
                "prediction_date": str(row["prediction_date"]),
                "forecast_period": row["forecast_period"],
                "forecast_value": round(float(row["forecast_value"] or 0.0), 2),
                "recommendation": row["recommendation"],
                "confidence": round(float(row["confidence"] or 0.0), 4),
                "model_version": row["model_version"],
            })
        conn.close()
    except Exception as exc:
        logger.warning(f"[sales_analytics] Could not query sales_prediction_history: {exc}")

    return history


def get_sales_analytics(
    range_type: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_products_limit: int = 10,
) -> Dict[str, Any]:
    """
    Generate comprehensive, chart-ready sales analytics.

    Parameters
    ----------
    range_type : str
        Aggregation cadence: 'daily', 'weekly', or 'monthly'.
    start_date : str, optional
        Filter records on or after YYYY-MM-DD.
    end_date : str, optional
        Filter records on or before YYYY-MM-DD.
    top_products_limit : int
        Number of top-performing products to include in rankings.

    Returns
    -------
    dict
        Chart-ready dictionary with:
          - trend: list of {date, revenue, volume}
          - labels: list of date strings for X-axis
          - datasets: Chart.js standard dataset objects
          - product_performance: top product rankings
          - prediction_history: recent model forecasts
          - summary: high-level totals
    """
    from app.ml.sales.dataset import load_sales_dataset

    df = load_sales_dataset()
    if df.empty:
        return {
            "trend": [],
            "labels": [],
            "datasets": [],
            "product_performance": [],
            "prediction_history": [],
            "summary": {
                "total_revenue": 0.0,
                "total_volume": 0,
                "records_count": 0,
            },
        }

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # 1. Apply date filtering if provided
    has_custom_filter = bool(start_date or end_date)
    if start_date:
        try:
            dt_start = pd.to_datetime(start_date)
            df = df[df["date"] >= dt_start]
        except Exception:
            logger.warning(f"[sales_analytics] Invalid start_date '{start_date}' ignored.")

    if end_date:
        try:
            dt_end = pd.to_datetime(end_date)
            df = df[df["date"] <= dt_end]
        except Exception:
            logger.warning(f"[sales_analytics] Invalid end_date '{end_date}' ignored.")

    if df.empty:
        return {
            "trend": [],
            "labels": [],
            "datasets": [],
            "product_performance": [],
            "prediction_history": _fetch_sales_prediction_history(),
            "summary": {
                "total_revenue": 0.0,
                "total_volume": 0,
                "records_count": 0,
            },
        }

    # Ensure quantity column exists
    if "quantity" not in df.columns:
        df["quantity"] = 1

    # 2. Aggregation by cadence (daily, weekly, monthly)
    range_norm = str(range_type).strip().lower()
    if range_norm == "weekly":
        # Group by Monday start of week
        df["group_date"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%Y-%m-%d"))
        grouped = df.groupby("group_date").agg({
            "revenue": "sum",
            "quantity": "sum",
        }).reset_index()
        # Default to last 16 weeks if no explicit date filter
        if not has_custom_filter and len(grouped) > 16:
            grouped = grouped.tail(16)
    elif range_norm == "monthly":
        df["group_date"] = df["date"].dt.strftime("%Y-%m")
        grouped = df.groupby("group_date").agg({
            "revenue": "sum",
            "quantity": "sum",
        }).reset_index()
        # Default to last 12 months if no explicit date filter
        if not has_custom_filter and len(grouped) > 12:
            grouped = grouped.tail(12)
    else:
        # Default: daily
        range_norm = "daily"
        df["group_date"] = df["date"].dt.strftime("%Y-%m-%d")
        grouped = df.groupby("group_date").agg({
            "revenue": "sum",
            "quantity": "sum",
        }).reset_index()
        # Default to last 30 daily points if no explicit date filter
        if not has_custom_filter and len(grouped) > 30:
            grouped = grouped.tail(30)

    grouped = grouped.sort_values("group_date")

    # 3. Chart-ready points array {date, revenue, volume}
    trend_points: List[Dict[str, Any]] = []
    labels: List[str] = []
    rev_series: List[float] = []
    vol_series: List[int] = []

    for _, row in grouped.iterrows():
        d_str = str(row["group_date"])
        rev = round(float(row["revenue"]), 2)
        vol = int(row["quantity"])
        trend_points.append({
            "date": d_str,
            "revenue": rev,
            "volume": vol,
        })
        labels.append(d_str)
        rev_series.append(rev)
        vol_series.append(vol)

    # 4. Product performance breakdown
    product_performance: List[Dict[str, Any]] = []
    total_period_revenue = float(df["revenue"].sum())

    prod_grp = df.groupby("product").agg({
        "revenue": "sum",
        "quantity": "sum",
    }).reset_index()

    top_prods = prod_grp.nlargest(top_products_limit, "revenue")
    for _, row in top_prods.iterrows():
        p_rev = round(float(row["revenue"]), 2)
        p_vol = int(row["quantity"])
        share = round((p_rev / (total_period_revenue + 1e-6)) * 100, 2)
        product_performance.append({
            "product": str(row["product"]),
            "revenue": p_rev,
            "volume": p_vol,
            "share_pct": share,
        })

    # 5. Prediction history integration
    prediction_history = _fetch_sales_prediction_history()

    # 6. Assemble Chart.js standard datasets
    datasets = [
        {
            "label": "Revenue (INR)",
            "data": rev_series,
            "borderColor": "#6366f1",
            "backgroundColor": "rgba(99, 102, 241, 0.15)",
            "yAxisID": "yRevenue",
            "fill": True,
            "tension": 0.3,
        },
        {
            "label": "Volume (Units)",
            "data": vol_series,
            "borderColor": "#10b981",
            "backgroundColor": "rgba(16, 185, 129, 0.15)",
            "yAxisID": "yVolume",
            "fill": False,
            "tension": 0.3,
        },
    ]

    total_volume_sum = int(df["quantity"].sum())
    summary = {
        "total_revenue": round(total_period_revenue, 2),
        "total_volume": total_volume_sum,
        "avg_order_value": round(total_period_revenue / max(1, len(df)), 2),
        "records_count": len(df),
        "range_type": range_norm,
        "data_points": len(trend_points),
        "min_date": df["date"].min().strftime("%Y-%m-%d"),
        "max_date": df["date"].max().strftime("%Y-%m-%d"),
    }

    return {
        "trend": trend_points,
        "labels": labels,
        "datasets": datasets,
        "product_performance": product_performance,
        "prediction_history": prediction_history,
        "summary": summary,
    }
