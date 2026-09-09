"""
app/ml/inventory/inventory_feature_engineering.py
--------------------------------------------------
Feature engineering for the Inventory ML domain module.

Computes:
  - Available Quantity (available_qty)
  - Safety Stock (safety_stock)
  - Stock Turnover (stock_turnover)
  - Days in Inventory (days_in_inventory)
  - Fast Moving Items Indicator (fast_moving)
  - Slow Moving Items Indicator (slow_moving)
  - Dead Stock Indicator (dead_stock)
  - Reorder Level (reorder_level)
  - Stock & Production aggregations (total_stock, warehouse_count, etc.)
  - Target variable (reorder_flag)
"""

import os
import sys
import pandas as pd
import numpy as np

from app.config import cfg
from app.ml.common.logger import get_ml_logger
from app.inventory.data_loader import load_raw_stock, load_raw_production
from app.inventory.preprocess import preprocess as inventory_preprocess

log = get_ml_logger("inventory_feature_engineering")


def compute_inventory_features(stock_df: pd.DataFrame = None, prod_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Transform stock and production data to compute inventory health and reorder features.
    """
    if stock_df is None or stock_df.empty:
        stock_df = load_raw_stock()
        prod_df = load_raw_production()

    if stock_df.empty:
        log.warning("Received empty stock DataFrame for inventory feature engineering.")
        return pd.DataFrame()

    # 1. Base aggregations from app/inventory/preprocess
    df = inventory_preprocess(stock_df, prod_df)

    if df.empty:
        log.warning("Base inventory preprocessing yielded empty DataFrame.")
        return pd.DataFrame()

    df = df.copy()

    # 2. Available Quantity
    df["available_qty"] = df["total_stock"].clip(lower=0.0)

    # 3. Safety Stock (Buffer estimate based on mean stock and variance)
    df["safety_stock"] = (df["total_stock"] * 0.15 + 10.0).round(2)

    # 4. Stock Turnover Rate
    planned = df["total_qty_planned"].replace(0, np.nan)
    df["stock_turnover"] = (df["total_produced"] / (df["total_stock"] + 1)).fillna(0.0).round(4)

    # 5. Days in Inventory
    daily_consumption = (df["total_produced"] / 30.0).replace(0, np.nan)
    df["days_in_inventory"] = (df["total_stock"] / daily_consumption).fillna(180.0).clip(upper=365.0).round(1)

    # 6. Fast Moving & Slow Moving Flags
    df["fast_moving"] = (df["stock_turnover"] > 2.0).astype(int)
    df["slow_moving"] = ((df["stock_turnover"] < 0.5) & (df["total_stock"] > 0)).astype(int)

    # 7. Dead Stock Indicator
    df["dead_stock"] = ((df["total_produced"] == 0) & (df["total_stock"] > 50)).astype(int)

    # 8. Reorder Level
    lead_time_days = 7.0
    avg_daily_demand = (df["total_qty_planned"] / 30.0).fillna(1.0)
    df["reorder_level"] = (df["safety_stock"] + (avg_daily_demand * lead_time_days)).round(2)

    # Target variable: reorder_flag (1 if total_stock < reorder_level, else 0)
    if "reorder_flag" not in df.columns:
        df["reorder_flag"] = (df["total_stock"] < df["reorder_level"]).astype(int)

    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    log.info(f"Inventory feature engineering complete: {len(df):,} items x {len(df.columns)} columns.")
    return df


def load_and_preprocess_inventory_data(filepath: str = None) -> pd.DataFrame:
    """
    Load inventory data from processed CSV or raw stock/production datasets and compute features.
    """
    stock_df = load_raw_stock()
    prod_df = load_raw_production()
    return compute_inventory_features(stock_df, prod_df)
