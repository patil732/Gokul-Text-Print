"""
app/inventory/data_loader.py
----------------------------
Loads raw inventory data (stock levels + production orders) for the
Inventory reorder-prediction module.

Data sources (written by pipelines/data_ingestion.py)
------------------------------------------------------
  data/raw/stock.csv      — ERP Bin records
                            columns: name, item_code, actual_qty, warehouse
  data/raw/production.csv — ERP Work Order records
                            columns: name, item, qty, produced_qty, status

This module is intentionally isolated from app/sales — it does NOT read
sales.csv and has no dependency on app/sales.data_loader.
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config  import cfg
from utils.logger import logger

# --------------------------------------------------------------------------- #
# File paths
# --------------------------------------------------------------------------- #
_STOCK_CSV = os.path.join(cfg.RAW_DATA_DIR, "stock.csv")
_PROD_CSV  = os.path.join(cfg.RAW_DATA_DIR, "production.csv")

REQUIRED_STOCK_COLUMNS = {"name", "item_code", "actual_qty", "warehouse"}
REQUIRED_PROD_COLUMNS  = {"name", "item", "qty", "produced_qty", "status"}


# --------------------------------------------------------------------------- #
# Internal helper
# --------------------------------------------------------------------------- #
def _safe_read(path: str, required_cols: set, label: str) -> pd.DataFrame:
    """Read a CSV, validate required columns, and return an empty DataFrame on any error."""
    if not os.path.exists(path):
        logger.warning(f"[inventory.data_loader] {label} file not found: {path}")
        return pd.DataFrame()

    if os.path.getsize(path) == 0:
        logger.warning(f"[inventory.data_loader] {label} file is empty: {path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        logger.error(f"[inventory.data_loader] Cannot parse {path}: {exc}")
        return pd.DataFrame()

    missing = required_cols - set(df.columns)
    if missing:
        logger.error(
            f"[inventory.data_loader] {label} missing columns: {missing}"
        )
        return pd.DataFrame()

    logger.info(f"[inventory.data_loader] {label}: loaded {len(df):,} rows from {path}")
    return df


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def load_raw_stock(path: str = _STOCK_CSV) -> pd.DataFrame:
    """
    Read the raw ERP stock/bin CSV.

    Expected columns: name, item_code, actual_qty, warehouse

    Returns
    -------
    pd.DataFrame
        Raw stock records, or an empty DataFrame on error.
    """
    return _safe_read(path, REQUIRED_STOCK_COLUMNS, "stock.csv")


def load_raw_production(path: str = _PROD_CSV) -> pd.DataFrame:
    """
    Read the raw ERP production/work-order CSV.

    Expected columns: name, item, qty, produced_qty, status

    Returns
    -------
    pd.DataFrame
        Raw production records, or an empty DataFrame on error.
    """
    return _safe_read(path, REQUIRED_PROD_COLUMNS, "production.csv")


if __name__ == "__main__":
    stock = load_raw_stock()
    prod  = load_raw_production()
    print(f"Stock rows      : {len(stock):,}")
    print(f"Production rows : {len(prod):,}")
    if not stock.empty:
        print(stock.head(3).to_string())
    if not prod.empty:
        print(prod.head(3).to_string())
