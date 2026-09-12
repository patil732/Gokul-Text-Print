"""
app/ml/sales/dataset.py
-----------------------
ML-layer sales dataset builder.

Reads the ETL output (data/raw/sales.csv or data/processed/training_data.csv)
and applies ML-specific cleaning, normalization, and column enrichment to
produce data/sales_dataset.csv.

This module is intentionally decoupled from the ETL pipeline:
  - It does NOT import or call any code in app/etl/
  - It reads the ETL's CSV output via plain pandas
  - The ETL pipeline remains completely unchanged

Cleaning steps
--------------
1. Deduplication    — drop exact-duplicate rows; then deduplicate on Sales
                      Order 'name' field (ETL primary key).
2. Invalid removal  — drop rows with unparseable dates or negative revenue.
3. Missing values   — impute revenue nulls with 0.0; drop rows missing the
                      date or product identifier.
4. Date normalization — parse to datetime64; extract year, month,
                       day_of_week, week_of_year, quarter.
5. Column normalization — map ETL column names to ML canonical names:
                           date, product, revenue.
6. Quantity derivation  — no explicit qty in ETL output; derive as order-count
                           per (product, date) aggregation.
7. Revenue normalization — min-max scale 'revenue' → 'revenue_norm' ∈ [0, 1].
8. Output           — write to data/sales_dataset.csv (default).

Public API
----------
build_sales_dataset(source_path=None, output_path=None) -> dict
    Build the dataset and return a summary dict.

load_sales_dataset(path=None) -> pd.DataFrame
    Load the pre-built dataset CSV.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

_MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ML_DIR       = os.path.dirname(_MODULE_DIR)
_APP_DIR      = os.path.dirname(_ML_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import numpy  as np
import pandas as pd

from app.config            import cfg
from app.ml.common.logger  import get_ml_logger

log = get_ml_logger("sales_dataset")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_DEFAULT_OUTPUT_FILENAME = "sales_dataset.csv"

# ETL column → ML canonical column mapping
_ETL_COL_MAP = {
    "transaction_date": "date",
    "customer":         "product",
    "grand_total":      "revenue",
}

# Columns that must be present (with canonical names) after normalization
_REQUIRED_COLS = ["date", "product", "revenue"]


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def build_sales_dataset(
    source_path: str | None = None,
    output_path: str | None = None,
) -> dict:
    """
    Build a cleaned, feature-rich ML sales dataset from the ETL CSV output.

    Parameters
    ----------
    source_path : str, optional
        Path to the input CSV.  Defaults to data/raw/sales.csv;
        falls back to data/processed/training_data.csv.
    output_path : str, optional
        Path for the output CSV.  Defaults to data/sales_dataset.csv.

    Returns
    -------
    dict
        Summary::
            {
              "status":      "success" | "failed",
              "source":      str,
              "output":      str,
              "input_rows":  int,
              "output_rows": int,
              "dropped":     int,
              "columns":     list[str],
              "errors":      list[str],
            }
    """
    started = datetime.now()
    errors: list[str] = []

    source_path = _resolve_source(source_path)
    output_path = output_path or os.path.join(cfg.DATA_DIR, _DEFAULT_OUTPUT_FILENAME)

    log.info(f"[dataset] Building sales dataset from: {source_path}")

    # ------------------------------------------------------------------ #
    # Step 1 — Load
    # ------------------------------------------------------------------ #
    df, load_err = _load_csv(source_path)
    if load_err:
        errors.append(load_err)
        return _failure_summary(source_path, output_path, errors)

    input_rows = len(df)
    log.info(f"[dataset] Loaded {input_rows:,} rows × {len(df.columns)} cols from ETL output.")

    # ------------------------------------------------------------------ #
    # Step 2 — Column normalization (rename before any other step)
    # ------------------------------------------------------------------ #
    df = df.rename(columns={k: v for k, v in _ETL_COL_MAP.items() if k in df.columns})

    # ------------------------------------------------------------------ #
    # Step 3 — Date normalization
    # ------------------------------------------------------------------ #
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    else:
        errors.append("'date' column not found after column mapping.")
        return _failure_summary(source_path, output_path, errors)

    # ------------------------------------------------------------------ #
    # Step 4 — Remove invalid records (must happen before dedup on 'name')
    # ------------------------------------------------------------------ #
    pre_invalid = len(df)
    df = df.dropna(subset=["date"])                                            # unparseable dates
    df["revenue"] = pd.to_numeric(df.get("revenue", pd.Series(dtype=float)), errors="coerce")
    df = df[df["revenue"].fillna(0.0) >= 0]                                    # negative revenue
    df = df.dropna(subset=["product"])                                         # missing product
    post_invalid = len(df)
    _log_drop("invalid records", pre_invalid, post_invalid)

    # ------------------------------------------------------------------ #
    # Step 5 — Handle missing values
    # ------------------------------------------------------------------ #
    df["revenue"] = df["revenue"].fillna(0.0)

    # ------------------------------------------------------------------ #
    # Step 6 — Deduplication
    # ------------------------------------------------------------------ #
    pre_dup = len(df)
    df = df.drop_duplicates()                                                  # exact-duplicate rows
    if "name" in df.columns:
        df = df.drop_duplicates(subset=["name"])                               # duplicate Sales Orders
    post_dup = len(df)
    _log_drop("duplicate rows", pre_dup, post_dup)

    # ------------------------------------------------------------------ #
    # Step 7 — Quantity derivation
    # ------------------------------------------------------------------ #
    # ETL raw sales.csv has no 'quantity' column; derive as order-count
    # per (product, date) group — how many orders per product per day.
    if "quantity" not in df.columns:
        qty_map = df.groupby(["product", "date"]).size().rename("quantity")
        df = df.join(qty_map, on=["product", "date"])
        log.info("[dataset] Derived 'quantity' as order-count per (product, date).")

    # ------------------------------------------------------------------ #
    # Step 8 — Date feature extraction
    # ------------------------------------------------------------------ #
    df["year"]         = df["date"].dt.year
    df["month"]        = df["date"].dt.month
    df["day_of_week"]  = df["date"].dt.dayofweek          # 0=Monday … 6=Sunday
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["quarter"]      = df["date"].dt.quarter

    # ------------------------------------------------------------------ #
    # Step 9 — Revenue normalization (min-max → [0, 1])
    # ------------------------------------------------------------------ #
    rev_min = df["revenue"].min()
    rev_max = df["revenue"].max()
    if rev_max > rev_min:
        df["revenue_norm"] = (df["revenue"] - rev_min) / (rev_max - rev_min)
    else:
        df["revenue_norm"] = 0.0
    log.info(f"[dataset] revenue_norm: min={rev_min:.2f}  max={rev_max:.2f}")

    # ------------------------------------------------------------------ #
    # Step 10 — Final guard: drop any remaining rows missing required cols
    # ------------------------------------------------------------------ #
    pre_final = len(df)
    df = df.dropna(subset=_REQUIRED_COLS)
    post_final = len(df)
    _log_drop("final null-guard", pre_final, post_final)

    total_dropped = input_rows - post_final

    # ------------------------------------------------------------------ #
    # Step 11 — Sort and save
    # ------------------------------------------------------------------ #
    df = df.sort_values(["product", "date"]).reset_index(drop=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    elapsed = (datetime.now() - started).total_seconds()
    log.info(
        f"[dataset] Done in {elapsed:.2f}s — "
        f"{post_final:,} rows × {len(df.columns)} cols → {output_path}"
    )

    return {
        "status":      "success",
        "source":      source_path,
        "output":      output_path,
        "input_rows":  input_rows,
        "output_rows": post_final,
        "dropped":     total_dropped,
        "columns":     list(df.columns),
        "errors":      [],
    }


def load_sales_dataset(path: str | None = None) -> pd.DataFrame:
    """
    Load the pre-built ML sales dataset CSV.

    Parameters
    ----------
    path : str, optional
        Explicit path to the CSV.  Defaults to data/sales_dataset.csv.

    Returns
    -------
    pd.DataFrame
        Loaded dataset with 'date' parsed as datetime, or empty DataFrame
        if the file is missing.
    """
    path = path or os.path.join(cfg.DATA_DIR, _DEFAULT_OUTPUT_FILENAME)

    if not os.path.exists(path):
        log.warning(f"[dataset] Sales dataset not found at {path}. Run build_sales_dataset() first.")
        return pd.DataFrame()

    df = pd.read_csv(path, parse_dates=["date"])
    log.info(f"[dataset] Loaded sales dataset: {len(df):,} rows from {path}")
    return df


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _resolve_source(source_path: str | None) -> str:
    """Resolve the input CSV path with fallback chain."""
    if source_path and os.path.exists(source_path):
        return source_path

    # Primary: ETL raw output
    raw_path = os.path.join(cfg.RAW_DATA_DIR, "sales.csv")
    if os.path.exists(raw_path):
        return raw_path

    # Fallback: ETL processed output
    processed_path = os.path.join(cfg.PROCESSED_DATA_DIR, "training_data.csv")
    if os.path.exists(processed_path):
        log.warning("[dataset] Raw sales.csv not found — falling back to training_data.csv.")
        return processed_path

    return raw_path   # will produce a clear error in _load_csv


def _load_csv(path: str) -> tuple[pd.DataFrame, str | None]:
    """Safely load a CSV; return (df, error_message_or_None)."""
    if not os.path.exists(path):
        return pd.DataFrame(), f"Source file not found: {path}"

    if os.path.getsize(path) == 0:
        return pd.DataFrame(), f"Source file is empty (0 bytes): {path}"

    try:
        df = pd.read_csv(path)
        if df.empty:
            return pd.DataFrame(), f"Source CSV parsed to empty DataFrame: {path}"
        return df, None
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        return pd.DataFrame(), f"Cannot parse CSV at {path}: {exc}"
    except Exception as exc:
        return pd.DataFrame(), f"Unexpected error reading {path}: {exc}"


def _log_drop(label: str, before: int, after: int) -> None:
    dropped = before - after
    if dropped > 0:
        log.info(f"[dataset] {label}: dropped {dropped:,} rows  ({after:,} remain).")


def _failure_summary(source: str, output: str, errors: list[str]) -> dict:
    log.error(f"[dataset] Build FAILED: {errors}")
    return {
        "status":      "failed",
        "source":      source,
        "output":      output,
        "input_rows":  0,
        "output_rows": 0,
        "dropped":     0,
        "columns":     [],
        "errors":      errors,
    }


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    result = build_sales_dataset()
    print(f"\nStatus      : {result['status']}")
    print(f"Source      : {result['source']}")
    print(f"Output      : {result['output']}")
    print(f"Input rows  : {result['input_rows']:,}")
    print(f"Output rows : {result['output_rows']:,}")
    print(f"Dropped     : {result['dropped']:,}")
    print(f"Columns     : {result['columns']}")
    if result["errors"]:
        print(f"Errors      : {result['errors']}")
        sys.exit(1)
