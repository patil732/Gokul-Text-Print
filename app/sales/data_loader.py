"""
app/sales/data_loader.py
------------------------
Loads raw sales data for the Sales forecasting module.

Data source: data/raw/sales.csv  (ingested by pipelines/data_ingestion.py)

This module is intentionally isolated from app/inventory — it reads only
the sales CSV and returns a clean DataFrame. No stock or production data
is loaded here; those belong to app/inventory/data_loader.py.
"""

import os
import sys
import pandas as pd

# Allow direct script execution from any working directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import settings
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
_SALES_CSV = os.path.join(settings.RAW_DATA_DIR, "sales.csv")

REQUIRED_COLUMNS = {"name", "transaction_date", "customer", "grand_total"}


def load_raw_sales(path: str = _SALES_CSV) -> pd.DataFrame:
    """
    Read the raw sales CSV produced by the ERP ingestion pipeline.

    Parameters
    ----------
    path : str
        Absolute path to the sales CSV. Defaults to data/raw/sales.csv.

    Returns
    -------
    pd.DataFrame
        Raw sales DataFrame with at least the columns listed in
        REQUIRED_COLUMNS.  Returns an empty DataFrame on any error so
        callers can detect the failure without crashing.
    """
    if not os.path.exists(path):
        logger.warning(f"[sales.data_loader] File not found: {path}")
        return pd.DataFrame()

    if os.path.getsize(path) == 0:
        logger.warning(f"[sales.data_loader] File is empty: {path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        logger.error(f"[sales.data_loader] Could not parse {path}: {exc}")
        return pd.DataFrame()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        logger.error(
            f"[sales.data_loader] Missing columns in {path}: {missing}"
        )
        return pd.DataFrame()

    logger.info(f"[sales.data_loader] Loaded {len(df):,} rows from {path}")
    return df


if __name__ == "__main__":
    df = load_raw_sales()
    print(f"Rows loaded: {len(df)}")
    print(df.head())
