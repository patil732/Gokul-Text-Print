"""
app/ml/sales/sales_feature_engineering.py
------------------------------------------
Feature engineering for the Sales ML domain module.

Sprint 1 features
-----------------
  - Daily Sales, Weekly Sales, Monthly Sales
  - Growth Rate, Rolling Average, 7-Day Moving Average
  - Revenue Trend, Sales Volatility
  - Lag features (lag_1 / lag_2 / lag_3), Momentum, Stock Ratio

Sprint 2 additions
------------------
  - Product Popularity  : product's share of total revenue across the dataset
  - Seasonal Index      : per-(product, month) mean sales divided by the
                          product's overall mean — captures seasonal uplift/drag
  - Sales Frequency     : rolling 30-day count of distinct sale days per product

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

    # ------------------------------------------------------------------ #
    # Sprint 2 — New features
    # ------------------------------------------------------------------ #

    # 8. Product Popularity
    #    Each product's cumulative revenue as a fraction of grand-total revenue
    #    across the entire dataset (global popularity score ∈ [0, 1]).
    total_revenue = df["sales"].sum()
    if total_revenue > 0:
        product_totals = df.groupby("product")["sales"].transform("sum")
        df["product_popularity"] = product_totals / total_revenue
    else:
        df["product_popularity"] = 0.0

    # 9. Seasonal Index
    #    Ratio of the (product, month) mean to the product's overall mean.
    #    Values > 1 indicate above-average demand for that month;
    #    values < 1 indicate below-average demand.
    if "date" in df.columns:
        df["_month"] = df["date"].dt.month
        product_mean       = df.groupby("product")["sales"].transform("mean").replace(0, np.nan)
        product_month_mean = df.groupby(["product", "_month"])["sales"].transform("mean")
        df["seasonal_index"] = (product_month_mean / product_mean).fillna(1.0)
        df = df.drop(columns=["_month"])
    else:
        df["seasonal_index"] = 1.0

    # 10. Sales Frequency
    #     Within a 30-day rolling window, count the number of distinct
    #     calendar days on which the product recorded a sale.
    #     Reflects how consistently (frequently) a product moves.
    if "date" in df.columns:
        # Convert date to integer ordinal for rolling arithmetic
        df["_date_ord"] = df["date"].map(lambda d: d.toordinal() if pd.notna(d) else np.nan)

        def _rolling_distinct_days(group: pd.Series) -> pd.Series:
            """Count distinct sale days in a 30-day trailing window."""
            result = np.zeros(len(group), dtype=float)
            values = group.values
            for i in range(len(values)):
                current = values[i]
                if np.isnan(current):
                    continue
                window_vals = values[max(0, i - 29): i + 1]   # up to 30 observations
                result[i] = len(set(v for v in window_vals if not np.isnan(v)))
            return pd.Series(result, index=group.index)

        df["sales_frequency"] = (
            df.groupby("product")["_date_ord"]
            .transform(_rolling_distinct_days)
        )
        df = df.drop(columns=["_date_ord"])
    else:
        df["sales_frequency"] = 1.0

    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    log.info(
        f"Sales feature engineering complete: {len(df):,} rows x {len(df.columns)} columns "
        f"(includes Sprint-2 features: product_popularity, seasonal_index, sales_frequency)."
    )
    return df


def compute_extended_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute only the three Sprint-2 feature additions on an already-prepared
    DataFrame (must contain 'product', 'sales', and optionally 'date').

    This is a lightweight wrapper for cases where the Sprint-1 features have
    already been computed and only the new features are needed.

    Returns
    -------
    pd.DataFrame
        Input DataFrame extended with:
          - product_popularity
          - seasonal_index
          - sales_frequency
    """
    if df.empty:
        log.warning("compute_extended_features(): received empty DataFrame.")
        return pd.DataFrame()

    df = df.copy()

    if "product" not in df.columns:
        df["product"] = "default_product"
    if "sales" not in df.columns:
        df["sales"] = 0.0

    # Product Popularity
    total_revenue = df["sales"].sum()
    if total_revenue > 0:
        product_totals = df.groupby("product")["sales"].transform("sum")
        df["product_popularity"] = product_totals / total_revenue
    else:
        df["product_popularity"] = 0.0

    # Seasonal Index
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["_month"] = df["date"].dt.month
        product_mean       = df.groupby("product")["sales"].transform("mean").replace(0, np.nan)
        product_month_mean = df.groupby(["product", "_month"])["sales"].transform("mean")
        df["seasonal_index"] = (product_month_mean / product_mean).fillna(1.0)
        df = df.drop(columns=["_month"])
    else:
        df["seasonal_index"] = 1.0

    # Sales Frequency
    if "date" in df.columns:
        df["_date_ord"] = df["date"].map(lambda d: d.toordinal() if pd.notna(d) else np.nan)

        def _rolling_distinct_days(group: pd.Series) -> pd.Series:
            result = np.zeros(len(group), dtype=float)
            values = group.values
            for i in range(len(values)):
                current = values[i]
                if np.isnan(current):
                    continue
                window_vals = values[max(0, i - 29): i + 1]
                result[i] = len(set(v for v in window_vals if not np.isnan(v)))
            return pd.Series(result, index=group.index)

        df["sales_frequency"] = (
            df.groupby("product")["_date_ord"]
            .transform(_rolling_distinct_days)
        )
        df = df.drop(columns=["_date_ord"])
    else:
        df["sales_frequency"] = 1.0

    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    log.info(f"compute_extended_features(): added 3 Sprint-2 features to {len(df):,} rows.")
    return df


def load_and_preprocess_sales_data(filepath: str = None) -> pd.DataFrame:
    """
    Load data from processed CSV or raw sales CSV and compute features
    (Sprint-1 + Sprint-2).
    """
    filepath = filepath or os.path.join(cfg.PROCESSED_DATA_DIR, "training_data.csv")
    if not os.path.exists(filepath):
        filepath = os.path.join(cfg.RAW_DATA_DIR, "sales.csv")

    if not os.path.exists(filepath):
        log.warning(f"Sales input dataset not found at {filepath}")
        return pd.DataFrame()

    df_raw = pd.read_csv(filepath)
    return compute_sales_features(df_raw)
