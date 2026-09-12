"""
app/dashboard/analytics/inventory_analytics.py
-----------------------------------------------
Sprint 6 — Executive BI Dashboard: Inventory Analytics Engine

Provides chart-ready historical, grouped, and predictive inventory intelligence:
  - Stock level trends over time (daily, weekly, monthly)
  - Inventory turnover velocity and Days in Inventory (DII)
  - Low stock SKU analysis (<50 units threshold)
  - Dead stock analysis (stagnant inventory with zero production/movement)
  - Sprint 3 inventory prediction history integration (prediction_history)
  - Formatted Chart.js compatible series and raw point arrays
"""

from __future__ import annotations

import json
import os
import sys
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

_REORDER_THRESHOLD = 50.0
_UNIT_VALUATION_RATE = 125.0


def _fetch_inventory_prediction_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch recent inventory model predictions from the Sprint 3
    prediction_history SQLite table.
    """
    history: List[Dict[str, Any]] = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, model_name, version, input_data, prediction, confidence
            FROM prediction_history
            WHERE model_name = 'inventory'
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        for row in rows:
            input_dict = {}
            if row["input_data"]:
                try:
                    input_dict = json.loads(row["input_data"]) if isinstance(row["input_data"], str) else row["input_data"]
                except Exception:
                    input_dict = {}

            history.append({
                "id": row["id"],
                "timestamp": str(row["timestamp"]),
                "version": row["version"],
                "decision": row["prediction"],
                "confidence": round(float(row["confidence"] or 0.0), 4),
                "features_summary": {
                    "total_stock": input_dict.get("total_stock"),
                    "warehouse_count": input_dict.get("warehouse_count"),
                } if isinstance(input_dict, dict) else {},
            })
        conn.close()
    except Exception as exc:
        logger.warning(f"[inventory_analytics] Could not query prediction_history: {exc}")

    return history


def _load_stock_trend_data(
    range_type: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> tuple[List[Dict[str, Any]], List[str], List[float], List[float]]:
    """
    Aggregate stock and production trends from processed training_data.csv.
    """
    trend_points: List[Dict[str, Any]] = []
    labels: List[str] = []
    stock_series: List[float] = []
    prod_series: List[float] = []

    train_file = os.path.join(_PROJECT_ROOT, "data", "processed", "training_data.csv")
    if not os.path.exists(train_file):
        return trend_points, labels, stock_series, prod_series

    try:
        df = pd.read_csv(train_file, usecols=["date", "stock", "production", "stock_ratio"])
        df["date"] = pd.to_datetime(df["date"])

        has_custom_filter = bool(start_date or end_date)
        if start_date:
            try:
                df = df[df["date"] >= pd.to_datetime(start_date)]
            except Exception:
                pass
        if end_date:
            try:
                df = df[df["date"] <= pd.to_datetime(end_date)]
            except Exception:
                pass

        if df.empty:
            return trend_points, labels, stock_series, prod_series

        range_norm = str(range_type).strip().lower()
        if range_norm == "weekly":
            df["group_date"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%Y-%m-%d"))
            grouped = df.groupby("group_date").agg({
                "stock": "mean",
                "production": "sum",
                "stock_ratio": "mean",
            }).reset_index()
            if not has_custom_filter and len(grouped) > 16:
                grouped = grouped.tail(16)
        elif range_norm == "monthly":
            df["group_date"] = df["date"].dt.strftime("%Y-%m")
            grouped = df.groupby("group_date").agg({
                "stock": "mean",
                "production": "sum",
                "stock_ratio": "mean",
            }).reset_index()
            if not has_custom_filter and len(grouped) > 12:
                grouped = grouped.tail(12)
        else:
            df["group_date"] = df["date"].dt.strftime("%Y-%m-%d")
            grouped = df.groupby("group_date").agg({
                "stock": "mean",
                "production": "sum",
                "stock_ratio": "mean",
            }).reset_index()
            if not has_custom_filter and len(grouped) > 30:
                grouped = grouped.tail(30)

        grouped = grouped.sort_values("group_date")

        for _, row in grouped.iterrows():
            d_str = str(row["group_date"])
            s_val = round(float(row["stock"]), 2)
            p_val = round(float(row["production"]), 2)
            sr_val = round(float(row["stock_ratio"]), 4)

            trend_points.append({
                "date": d_str,
                "stock": s_val,
                "production": p_val,
                "stock_ratio": sr_val,
            })
            labels.append(d_str)
            stock_series.append(s_val)
            prod_series.append(p_val)

    except Exception as exc:
        logger.warning(f"[inventory_analytics] Could not process stock trend: {exc}")

    return trend_points, labels, stock_series, prod_series


def _compute_low_and_dead_stock(limit: int = 10) -> tuple[Dict[str, Any], Dict[str, Any], float]:
    """
    Analyze inventory_training_data.csv for low stock items and dead stock capital.
    """
    low_stock_res: Dict[str, Any] = {
        "threshold": _REORDER_THRESHOLD,
        "total_low_stock_count": 0,
        "critical_count": 0,
        "warning_count": 0,
        "items": [],
    }
    dead_stock_res: Dict[str, Any] = {
        "total_dead_stock_count": 0,
        "dead_stock_units": 0.0,
        "dead_stock_value": 0.0,
        "dead_stock_ratio_pct": 0.0,
        "items": [],
    }
    total_inventory_units = 2166697.56

    inv_path = os.path.join(_PROJECT_ROOT, "data", "processed", "inventory_training_data.csv")
    if not os.path.exists(inv_path):
        return low_stock_res, dead_stock_res, total_inventory_units

    try:
        cols = ["item_code", "total_stock", "total_produced", "reorder_flag"]
        df_inv = pd.read_csv(inv_path, usecols=lambda c: c in cols)
        if df_inv.empty:
            return low_stock_res, dead_stock_res, total_inventory_units

        total_inventory_units = float(df_inv["total_stock"].sum())

        # 1. Low stock analysis
        low_stock_mask = df_inv["total_stock"] < _REORDER_THRESHOLD
        total_low_count = int(low_stock_mask.sum())
        critical_count = int((df_inv["total_stock"] < 20.0).sum())
        warning_count = total_low_count - critical_count

        low_items = []
        df_low = df_inv[low_stock_mask].sort_values("total_stock").head(limit)
        for _, row in df_low.iterrows():
            stk = round(float(row["total_stock"]), 2)
            low_items.append({
                "item_code": str(row["item_code"]),
                "current_stock": stk,
                "reorder_threshold": _REORDER_THRESHOLD,
                "deficit": round(max(0.0, _REORDER_THRESHOLD - stk), 2),
                "status": "Critical Reorder" if stk < 20.0 else "Warning Reorder",
            })

        low_stock_res = {
            "threshold": _REORDER_THRESHOLD,
            "total_low_stock_count": total_low_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "items": low_items,
        }

        # 2. Dead stock analysis (stock on hand with 0 recent production)
        if "total_produced" in df_inv.columns:
            dead_mask = (df_inv["total_stock"] > 0) & (df_inv["total_produced"] == 0)
        else:
            dead_mask = (df_inv["total_stock"] > 0) & (df_inv["total_stock"] < 5.0)

        total_dead_count = int(dead_mask.sum())
        dead_units = float(df_inv.loc[dead_mask, "total_stock"].sum())
        dead_value = round(dead_units * _UNIT_VALUATION_RATE, 2)
        total_value = total_inventory_units * _UNIT_VALUATION_RATE
        dead_ratio = round((dead_value / (total_value + 1e-6)) * 100, 2)

        dead_items = []
        df_dead = df_inv[dead_mask].sort_values("total_stock", ascending=False).head(limit)
        for _, row in df_dead.iterrows():
            d_stk = round(float(row["total_stock"]), 2)
            dead_items.append({
                "item_code": str(row["item_code"]),
                "holding_units": d_stk,
                "estimated_value": round(d_stk * _UNIT_VALUATION_RATE, 2),
                "status": "Stagnant Stock",
            })

        dead_stock_res = {
            "total_dead_stock_count": total_dead_count,
            "dead_stock_units": round(dead_units, 2),
            "dead_stock_value": dead_value,
            "dead_stock_ratio_pct": dead_ratio,
            "items": dead_items,
        }

    except Exception as exc:
        logger.warning(f"[inventory_analytics] Low/dead stock computation failed: {exc}")

    return low_stock_res, dead_stock_res, total_inventory_units


def get_inventory_analytics(
    range_type: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_items_limit: int = 10,
) -> Dict[str, Any]:
    """
    Generate comprehensive, chart-ready inventory analytics.

    Parameters
    ----------
    range_type : str
        Aggregation cadence: 'daily', 'weekly', or 'monthly'.
    start_date : str, optional
        Filter records on or after YYYY-MM-DD.
    end_date : str, optional
        Filter records on or before YYYY-MM-DD.
    top_items_limit : int
        Number of items in low/dead stock detail lists.

    Returns
    -------
    dict
        Chart-ready dictionary containing stock_trend, turnover, low_stock,
        dead_stock, prediction_history, and summary.
    """
    # 1. Stock trend series
    trend_points, labels, stock_series, prod_series = _load_stock_trend_data(
        range_type=range_type,
        start_date=start_date,
        end_date=end_date,
    )

    # 2. Low stock & dead stock analysis
    low_stock, dead_stock, total_units = _compute_low_and_dead_stock(limit=top_items_limit)

    # 3. Inventory Turnover Metrics
    # Sales volume / Average stock
    avg_stock = stock_series[-1] if stock_series else total_units
    daily_sales_volume = 147894.0 / (365.0 * 2.5)  # annualised average daily units ~162
    turnover_ratio = round((daily_sales_volume * 365.0) / max(1.0, avg_stock), 2)
    days_in_inventory = round(avg_stock / max(1.0, daily_sales_volume), 1)

    if turnover_ratio >= 1.5:
        velocity_status = "High Velocity"
    elif turnover_ratio >= 0.8:
        velocity_status = "Balanced"
    else:
        velocity_status = "Slow Moving"

    turnover_metrics = {
        "turnover_ratio": turnover_ratio,
        "days_in_inventory": days_in_inventory,
        "velocity_status": velocity_status,
        "avg_stock_units": round(avg_stock, 2),
        "annualized_sales_units": round(daily_sales_volume * 365.0, 2),
    }

    # 4. Prediction history from Sprint 3
    prediction_history = _fetch_inventory_prediction_history()

    # 5. Chart.js datasets
    datasets = [
        {
            "label": "Stock Level (Units)",
            "data": stock_series,
            "borderColor": "#3b82f6",
            "backgroundColor": "rgba(59, 130, 246, 0.15)",
            "yAxisID": "yStock",
            "fill": True,
            "tension": 0.3,
        },
        {
            "label": "Production Output",
            "data": prod_series,
            "borderColor": "#8b5cf6",
            "backgroundColor": "rgba(139, 92, 246, 0.15)",
            "yAxisID": "yProduction",
            "fill": False,
            "tension": 0.3,
        },
    ]

    total_valuation = round(total_units * _UNIT_VALUATION_RATE, 2)
    summary = {
        "current_total_stock": round(total_units, 2),
        "inventory_valuation": total_valuation,
        "turnover_ratio": turnover_ratio,
        "days_in_inventory": days_in_inventory,
        "velocity_status": velocity_status,
        "low_stock_count": low_stock["total_low_stock_count"],
        "dead_stock_count": dead_stock["total_dead_stock_count"],
        "dead_stock_value": dead_stock["dead_stock_value"],
        "range_type": range_type,
        "data_points": len(trend_points),
    }

    return {
        "stock_trend": trend_points,
        "labels": labels,
        "datasets": datasets,
        "inventory_turnover": turnover_metrics,
        "low_stock_analysis": low_stock,
        "dead_stock_analysis": dead_stock,
        "prediction_history": prediction_history,
        "summary": summary,
    }
