"""
app/inventory/preprocess.py
---------------------------
Feature engineering for the Inventory reorder-prediction module.

Transforms raw stock and production DataFrames into a per-item feature
matrix suitable for binary classification (reorder_flag = 1/0).

This module has NO dependency on app/sales — the two preprocessing
pipelines are fully decoupled.

Features produced (per item_code)
----------------------------------
  total_stock         : sum of actual_qty across all warehouses for the item
  warehouse_count     : number of distinct warehouses holding the item
  avg_stock_per_wh    : total_stock / warehouse_count
  max_stock_in_wh     : maximum actual_qty in any single warehouse
  stock_concentration : max_stock_in_wh / (total_stock + 1)   — how "concentrated"
                        the stock is (1.0 = all in one warehouse)
  total_qty_planned   : sum of planned production qty for the item
  total_produced      : sum of produced_qty for the item
  production_gap      : total_qty_planned - total_produced (unfulfilled orders)
  fulfillment_rate    : total_produced / (total_qty_planned + 1)
  has_open_orders     : 1 if any Work Order is in "In Process" / "Submitted"

Target
------
  reorder_flag : 1 if total_stock < REORDER_THRESHOLD else 0

Output file
-----------
  data/processed/inventory_training_data.csv
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config  import cfg
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
# Items with total stock below this threshold are labelled as needing reorder.
# 50 matches the threshold used in services/analytics_engine.py (low_stock_products).
REORDER_THRESHOLD = 50.0

PROCESSED_CSV = os.path.join(
    cfg.PROCESSED_DATA_DIR, "inventory_training_data.csv"
)

# Feature columns — MUST stay in sync with app/inventory/model.FEATURE_COLS
FEATURE_COLS = [
    "total_stock",
    "warehouse_count",
    "avg_stock_per_wh",
    "max_stock_in_wh",
    "stock_concentration",
    "total_qty_planned",
    "total_produced",
    "production_gap",
    "fulfillment_rate",
    "has_open_orders",
]

TARGET_COL = "reorder_flag"

# Work Order statuses treated as "open" (not yet fulfilled)
_OPEN_STATUSES = {"In Process", "Submitted", "Not Started"}


def preprocess(df_stock: pd.DataFrame, df_prod: pd.DataFrame) -> pd.DataFrame:
    """
    Build a per-item feature matrix from raw stock and production DataFrames.

    Parameters
    ----------
    df_stock : pd.DataFrame
        Output of data_loader.load_raw_stock().
        Required columns: item_code, actual_qty, warehouse.
    df_prod : pd.DataFrame
        Output of data_loader.load_raw_production().
        Required columns: item, qty, produced_qty, status.

    Returns
    -------
    pd.DataFrame
        Processed feature DataFrame with columns FEATURE_COLS + [TARGET_COL].
        Returns an empty DataFrame if df_stock is empty.
    """
    if df_stock.empty:
        logger.warning("[inventory.preprocess] Stock data is empty — cannot preprocess.")
        return pd.DataFrame()

    try:
        df_stock = df_stock.copy()
        df_stock["actual_qty"] = pd.to_numeric(df_stock["actual_qty"], errors="coerce").fillna(0.0)

        # ---------------------------------------------------------------- #
        # Stock-side features (per item_code)
        # ---------------------------------------------------------------- #
        stock_agg = df_stock.groupby("item_code").agg(
            total_stock      =("actual_qty", "sum"),
            warehouse_count  =("warehouse",  "nunique"),
            max_stock_in_wh  =("actual_qty", "max"),
        ).reset_index()

        stock_agg["avg_stock_per_wh"] = (
            stock_agg["total_stock"] / stock_agg["warehouse_count"]
        )
        stock_agg["stock_concentration"] = (
            stock_agg["max_stock_in_wh"] / (stock_agg["total_stock"] + 1)
        )

        # ---------------------------------------------------------------- #
        # Production-side features (per item)
        # ---------------------------------------------------------------- #
        if not df_prod.empty:
            df_prod = df_prod.copy()
            df_prod["qty"]         = pd.to_numeric(df_prod["qty"],         errors="coerce").fillna(0.0)
            df_prod["produced_qty"]= pd.to_numeric(df_prod["produced_qty"],errors="coerce").fillna(0.0)

            prod_agg = df_prod.groupby("item").agg(
                total_qty_planned=("qty",          "sum"),
                total_produced   =("produced_qty", "sum"),
            ).reset_index()
            prod_agg.rename(columns={"item": "item_code"}, inplace=True)

            # Open orders flag: 1 if the item has any non-completed Work Orders
            open_orders = (
                df_prod[df_prod["status"].isin(_OPEN_STATUSES)]
                .groupby("item")
                .size()
                .reset_index(name="open_order_count")
                .rename(columns={"item": "item_code"})
            )
            open_orders["has_open_orders"] = 1

            prod_agg = prod_agg.merge(
                open_orders[["item_code", "has_open_orders"]],
                on="item_code", how="left"
            )
            prod_agg["has_open_orders"] = prod_agg["has_open_orders"].fillna(0).astype(int)
        else:
            logger.info(
                "[inventory.preprocess] No production data — filling production features with 0."
            )
            prod_agg = pd.DataFrame(
                columns=["item_code", "total_qty_planned", "total_produced", "has_open_orders"]
            )

        # ---------------------------------------------------------------- #
        # Merge stock + production on item_code
        # ---------------------------------------------------------------- #
        df = stock_agg.merge(prod_agg, on="item_code", how="left")
        df["total_qty_planned"] = df["total_qty_planned"].fillna(0.0)
        df["total_produced"]    = df["total_produced"].fillna(0.0)
        df["has_open_orders"]   = df["has_open_orders"].fillna(0).astype(int)

        # ---------------------------------------------------------------- #
        # Derived production features
        # ---------------------------------------------------------------- #
        df["production_gap"]    = df["total_qty_planned"] - df["total_produced"]
        df["fulfillment_rate"]  = df["total_produced"] / (df["total_qty_planned"] + 1)

        # ---------------------------------------------------------------- #
        # Target: reorder needed when total stock is below threshold
        # ---------------------------------------------------------------- #
        df[TARGET_COL] = (df["total_stock"] < REORDER_THRESHOLD).astype(int)

        # ---------------------------------------------------------------- #
        # Final cleanup
        # ---------------------------------------------------------------- #
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        result = df[["item_code"] + FEATURE_COLS + [TARGET_COL]].copy()

        reorder_pct = result[TARGET_COL].mean() * 100
        logger.info(
            f"[inventory.preprocess] Done: {len(result):,} items | "
            f"reorder_flag=1: {reorder_pct:.1f}%"
        )
        return result

    except Exception as exc:
        logger.error(f"[inventory.preprocess] Preprocessing failed: {exc}")
        raise


def run_and_save(
    df_stock: pd.DataFrame,
    df_prod: pd.DataFrame,
    output_path: str = PROCESSED_CSV,
) -> pd.DataFrame:
    """
    Preprocess raw inventory data and write the result to *output_path*.

    Parameters
    ----------
    df_stock    : pd.DataFrame  Output of data_loader.load_raw_stock().
    df_prod     : pd.DataFrame  Output of data_loader.load_raw_production().
    output_path : str           Destination CSV path.

    Returns
    -------
    pd.DataFrame  The processed DataFrame (same as what was saved).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    processed = preprocess(df_stock, df_prod)
    if not processed.empty:
        processed.to_csv(output_path, index=False)
        logger.info(
            f"[inventory.preprocess] Saved {len(processed):,} rows -> {output_path}"
        )
    return processed


if __name__ == "__main__":
    from app.inventory.data_loader import load_raw_stock, load_raw_production
    stock = load_raw_stock()
    prod  = load_raw_production()
    out   = run_and_save(stock, prod)
    print(f"Processed rows : {len(out):,}")
    if not out.empty:
        print(out.head(5).to_string())
        print(f"\nReorder flag distribution:\n{out[TARGET_COL].value_counts()}")
