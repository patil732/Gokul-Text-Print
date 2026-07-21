"""
app/inventory/data_loader.py
----------------------------
Loads raw inventory (stock + production) data for the Inventory
reorder-prediction module.

Data sources
------------
  data/raw/stock.csv      — ERP Bin records (item_code, actual_qty, warehouse)
  data/raw/production.csv — ERP Work Order records (item, qty, produced_qty)

This module is intentionally isolated from app/sales — it does NOT read
sales.csv.  If a combined feature is needed in the future, it should be
built here from the already-loaded DataFrames rather than importing from
app/sales.

TODO (sprint 2+)
----------------
  - Implement load_raw_stock() by reading data/raw/stock.csv.
  - Implement load_raw_production() by reading data/raw/production.csv.
  - Add column validation (REQUIRED_STOCK_COLUMNS, REQUIRED_PROD_COLUMNS).
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
_STOCK_CSV = os.path.join(settings.RAW_DATA_DIR, "stock.csv")
_PROD_CSV  = os.path.join(settings.RAW_DATA_DIR, "production.csv")

REQUIRED_STOCK_COLUMNS = {"name", "item_code", "actual_qty", "warehouse"}
REQUIRED_PROD_COLUMNS  = {"name", "item", "qty", "produced_qty", "status"}


def load_raw_stock(path: str = _STOCK_CSV) -> pd.DataFrame:
    """
    [STUB] Read the raw stock/bin CSV.

    Returns
    -------
    pd.DataFrame
        Empty DataFrame — implement in sprint 2.
    """
    # TODO: implement full loading logic (see sales/data_loader.py as reference)
    logger.warning(
        "[inventory.data_loader] load_raw_stock() is a stub — returns empty DataFrame."
    )
    return pd.DataFrame()


def load_raw_production(path: str = _PROD_CSV) -> pd.DataFrame:
    """
    [STUB] Read the raw production/work-order CSV.

    Returns
    -------
    pd.DataFrame
        Empty DataFrame — implement in sprint 2.
    """
    # TODO: implement full loading logic (see sales/data_loader.py as reference)
    logger.warning(
        "[inventory.data_loader] load_raw_production() is a stub — returns empty DataFrame."
    )
    return pd.DataFrame()


if __name__ == "__main__":
    stock = load_raw_stock()
    prod  = load_raw_production()
    print(f"Stock rows:      {len(stock)}")
    print(f"Production rows: {len(prod)}")
