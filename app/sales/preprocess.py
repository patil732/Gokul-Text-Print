"""
app/sales/preprocess.py
-----------------------
Feature engineering for the Sales forecasting module.

Derives all temporal and rolling features that the Random Forest model
expects.  The feature list here MUST stay in sync with FEATURE_COLS in
app/sales/model.py — that constant is the single source of truth.

This module has NO dependency on app/inventory; changes here do not
affect inventory preprocessing.
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config  import cfg
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Output path for the sales-specific processed dataset
# --------------------------------------------------------------------------- #
PROCESSED_CSV = os.path.join(cfg.PROCESSED_DATA_DIR, "sales_training_data.csv")


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and engineer features from the raw sales DataFrame.

    Steps
    -----
    1. Parse & coerce dates; drop unparseable rows.
    2. Deduplicate on the ERP order name.
    3. Standardise column names (transaction_date→date, customer→product,
       grand_total→sales).
    4. Aggregate to (date, product) grain.
    5. Compute lag features (1, 2, 3 days).
    6. Compute rolling averages (3, 7, 14 days) and rolling std (7 days).
    7. Compute momentum, growth_rate, trend.
    8. Compute target variable: next-period sales > current  →  1 else 0.
    9. Drop rows with NaNs introduced by shifts/rolling.

    Parameters
    ----------
    df : pd.DataFrame
        Raw sales DataFrame from data_loader.load_raw_sales().

    Returns
    -------
    pd.DataFrame
        Feature-engineered DataFrame ready for model training or inference.
        Returns an empty DataFrame if the input is empty or malformed.
    """
    if df.empty:
        logger.warning("[sales.preprocess] Received empty DataFrame — skipping.")
        return pd.DataFrame()

    try:
        # --- 1. Date parsing & coercion ---
        df = df.copy()
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
        df = df.dropna(subset=["transaction_date", "grand_total"])

        # --- 2. Deduplication ---
        df = df.drop_duplicates(subset=["name"])

        # --- 3. Standardise column names ---
        df = df.rename(columns={
            "transaction_date": "date",
            "customer":         "product",
            "grand_total":      "sales",
        })

        # --- 4. Aggregate to daily-product grain ---
        df = (
            df.groupby(["date", "product"])["sales"]
            .sum()
            .reset_index()
        )
        df = df.sort_values(["product", "date"])

        # --- 5. Lag features ---
        grp = df.groupby("product")["sales"]
        df["sales_lag_1"] = grp.shift(1)
        df["sales_lag_2"] = grp.shift(2)
        df["sales_lag_3"] = grp.shift(3)

        # --- 6. Rolling statistics ---
        df["sales_ma_3"]  = grp.transform(lambda x: x.rolling(window=3,  min_periods=1).mean())
        df["sales_ma_7"]  = grp.transform(lambda x: x.rolling(window=7,  min_periods=1).mean())
        df["sales_ma_14"] = grp.transform(lambda x: x.rolling(window=14, min_periods=1).mean())
        df["sales_std_7"] = grp.transform(lambda x: x.rolling(window=7,  min_periods=1).std())

        # --- 7. Momentum & trend & stock_ratio ---
        df["momentum"]   = df["sales"] - df["sales_lag_3"]
        df["prev_sales"] = grp.shift(1)
        df["growth_rate"] = (df["sales"] - df["prev_sales"]) / (df["prev_sales"] + 1)
        df["trend"] = df["growth_rate"].apply(
            lambda x: 1 if x > 0.05 else (-1 if x < -0.05 else 0)
        )
        df["stock_ratio"] = (df["stock"] / (df["sales"] + 1)) if "stock" in df.columns else 0.0

        # --- 8. Target variable: will next period sales increase? ---
        df["next_sales"]       = grp.shift(-1)
        df["target_decision"]  = (df["next_sales"] > df["sales"]).astype(int)

        # --- 9. Drop NaNs (from shifts and future-target) ---
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()

        logger.info(
            f"[sales.preprocess] Feature engineering complete: {len(df):,} rows, "
            f"{len(df.columns)} columns."
        )
        return df

    except Exception as exc:
        logger.error(f"[sales.preprocess] Preprocessing failed: {exc}")
        raise


def run_and_save(df: pd.DataFrame, output_path: str = PROCESSED_CSV) -> pd.DataFrame:
    """
    Preprocess raw data and persist the result to disk.

    Parameters
    ----------
    df : pd.DataFrame
        Output of data_loader.load_raw_sales().
    output_path : str
        Where to write the processed CSV.

    Returns
    -------
    pd.DataFrame
        The processed DataFrame (same as what was saved).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    processed = preprocess(df)
    if not processed.empty:
        processed.to_csv(output_path, index=False)
        logger.info(f"[sales.preprocess] Saved {len(processed):,} rows -> {output_path}")
    return processed


if __name__ == "__main__":
    from app.sales.data_loader import load_raw_sales
    raw = load_raw_sales()
    out = run_and_save(raw)
    print(f"Processed rows: {len(out)}")
    print(out.head())
