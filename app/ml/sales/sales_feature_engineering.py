"""
app/ml/sales/sales_feature_engineering.py
------------------------------------------
Feature engineering for the Sales ML domain module.

Computes:
  - Daily Sales, Weekly Sales, Monthly Sales
  - Growth Rate, Rolling Average, 7-Day Moving Average
  - Revenue Trend, Sales Volatility
Reuses existing ETL output / sales dataset without modifying ETL logic.
"""

import os
import sys
import pandas as pd
import numpy as np

from app.config import cfg
from app.ml.common.logger import get_ml_logger

log = get_ml_logger("sales_feature_engineering")


def compute_sales_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform sales data to compute advanced temporal and volatility features.

    Calculates:
      - daily_sales        : daily total sales per product
      - weekly_sales       : 7-day rolling sales sum
      - monthly_sales      : 30-day rolling sales sum
      - growth_rate        : period-over-period percentage change
      - rolling_avg        : 3-period rolling mean
      - moving_avg_7d      : 7-period rolling mean
      - revenue_trend      : trend direction indicator (1, 0, -1)
      - sales_volatility   : 7-period rolling standard deviation
      - lag and momentum   : sales_lag_1/2/3, momentum, stock_ratio
    """
    if df.empty:
        log.warning("Received empty DataFrame for sales feature engineering.")
        return pd.DataFrame()

    df = df.copy()

    # Standardize column names if raw
    col_mapping = {
        "transaction_date": "date",
        "customer": "product",
        "grand_total": "sales",
    }
    df = df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns})

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

    # Ensure product and sales columns exist
    if "product" not in df.columns:
        df["product"] = "default_product"
    if "sales" not in df.columns:
        df["sales"] = 0.0

    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0.0)

    # Sort data for time series calculation
    sort_cols = ["product", "date"] if "date" in df.columns else ["product"]
    df = df.sort_values(by=sort_cols)

    # Group by product
    grp = df.groupby("product")["sales"]

    # 1. Daily, Weekly, Monthly Sales
    df["daily_sales"] = df["sales"]
    df["weekly_sales"] = grp.transform(lambda x: x.rolling(window=7, min_periods=1).sum())
    df["monthly_sales"] = grp.transform(lambda x: x.rolling(window=30, min_periods=1).sum())

    # 2. Rolling Average & 7-Day Moving Average
    df["rolling_avg"] = grp.transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    df["moving_avg_7d"] = grp.transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    df["sales_ma_3"] = df["rolling_avg"]
    df["sales_ma_7"] = df["moving_avg_7d"]
    df["sales_ma_14"] = grp.transform(lambda x: x.rolling(window=14, min_periods=1).mean())

    # 3. Lags
    df["sales_lag_1"] = grp.shift(1).fillna(0.0)
    df["sales_lag_2"] = grp.shift(2).fillna(0.0)
    df["sales_lag_3"] = grp.shift(3).fillna(0.0)

    # 4. Growth Rate, Momentum & Revenue Trend
    df["prev_sales"] = df["sales_lag_1"]
    df["growth_rate"] = (df["sales"] - df["prev_sales"]) / (df["prev_sales"].replace(0, np.nan))
    df["growth_rate"] = df["growth_rate"].fillna(0.0)

    df["momentum"] = df["sales"] - df["sales_lag_3"]
    df["revenue_trend"] = df["growth_rate"].apply(
        lambda x: 1 if x > 0.05 else (-1 if x < -0.05 else 0)
    )
    df["trend"] = df["revenue_trend"]

    # 5. Sales Volatility
    df["sales_volatility"] = grp.transform(lambda x: x.rolling(window=7, min_periods=1).std()).fillna(0.0)
    df["sales_std_7"] = df["sales_volatility"]

    # 6. Stock ratio (if stock available)
    if "stock" in df.columns:
        df["stock_ratio"] = df["stock"] / (df["sales"] + 1)
    else:
        df["stock_ratio"] = 0.0

    # 7. Target decision variable for classification/training
    df["next_sales"] = grp.shift(-1)
    df["target_decision"] = (df["next_sales"] > df["sales"]).astype(int)

    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    log.info(f"Sales feature engineering complete: {len(df):,} rows x {len(df.columns)} columns.")
    return df


def load_and_preprocess_sales_data(filepath: str = None) -> pd.DataFrame:
    """
    Load data from processed CSV or raw sales CSV and compute features.
    """
    filepath = filepath or os.path.join(cfg.PROCESSED_DATA_DIR, "training_data.csv")
    if not os.path.exists(filepath):
        filepath = os.path.join(cfg.RAW_DATA_DIR, "sales.csv")

    if not os.path.exists(filepath):
        log.warning(f"Sales input dataset not found at {filepath}")
        return pd.DataFrame()

    df_raw = pd.read_csv(filepath)
    return compute_sales_features(df_raw)
