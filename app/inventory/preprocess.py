"""
app/inventory/preprocess.py
---------------------------
Feature engineering for the Inventory reorder-prediction module.

This module will transform raw stock and production data into a feature
DataFrame suitable for training the inventory model.  It has NO dependency
on app/sales.

Planned features (sprint 2+)
-----------------------------
  - stock_level       : actual_qty per item / warehouse
  - days_of_cover     : stock_level / avg_daily_consumption
  - reorder_flag      : binary target (1 = reorder needed, 0 = sufficient)
  - production_gap    : qty - produced_qty (unfulfilled production)
  - warehouse_turnover: how fast stock moves per warehouse

Output file
-----------
  data/processed/inventory_training_data.csv
  (separate from sales_training_data.csv — never share artefacts)

TODO (sprint 2+)
----------------
  - Implement preprocess(df_stock, df_prod) function.
  - Implement run_and_save() to write PROCESSED_CSV.
  - Define FEATURE_COLS to keep in sync with inventory/model.py.
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import settings
from utils.logger    import logger

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
PROCESSED_CSV = os.path.join(
    settings.PROCESSED_DATA_DIR, "inventory_training_data.csv"
)

# Will be populated in sprint 2 once the feature set is finalised
FEATURE_COLS: list[str] = []   # TODO: define inventory feature columns
TARGET_COL = "reorder_flag"    # planned binary target


def preprocess(df_stock: pd.DataFrame, df_prod: pd.DataFrame) -> pd.DataFrame:
    """
    [STUB] Clean and engineer features from raw inventory DataFrames.

    Parameters
    ----------
    df_stock : pd.DataFrame  — output of data_loader.load_raw_stock()
    df_prod  : pd.DataFrame  — output of data_loader.load_raw_production()

    Returns
    -------
    pd.DataFrame
        Empty DataFrame — implement in sprint 2.
    """
    # TODO: implement feature engineering for inventory reorder prediction
    logger.warning(
        "[inventory.preprocess] preprocess() is a stub — returns empty DataFrame."
    )
    return pd.DataFrame()


def run_and_save(
    df_stock: pd.DataFrame,
    df_prod: pd.DataFrame,
    output_path: str = PROCESSED_CSV,
) -> pd.DataFrame:
    """
    [STUB] Preprocess and persist inventory features to disk.

    Returns
    -------
    pd.DataFrame
        Empty DataFrame — implement in sprint 2.
    """
    # TODO: call preprocess() and save result to output_path
    logger.warning(
        "[inventory.preprocess] run_and_save() is a stub — no file written."
    )
    return pd.DataFrame()


if __name__ == "__main__":
    from app.inventory.data_loader import load_raw_stock, load_raw_production
    stock = load_raw_stock()
    prod  = load_raw_production()
    out   = run_and_save(stock, prod)
    print(f"Processed rows: {len(out)}")
