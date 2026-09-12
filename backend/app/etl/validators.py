"""
app/etl/validators.py
---------------------
Reusable data validation functions for the ETL pipeline.

All validators follow a single contract:

    validate_*(df, ...) -> ValidationResult

where ``ValidationResult`` is a named tuple::

    ValidationResult(
        passed   : bool,           # True if all checks pass
        errors   : list[str],      # blocking errors — abort ETL on any
        warnings : list[str],      # non-blocking — log and continue
        stats    : dict,           # counts / metrics for audit logging
    )

Validators are pure functions; they never mutate the DataFrame.

Available validators
--------------------
validate_sales(df)       — Sales Order dataset (mandatory)
validate_stock(df)       — Stock / Bin dataset (optional)
validate_production(df)  — Work Order dataset (optional)

Each validator runs three tiers of checks in order:
  Tier 1 — Schema:     required columns present
  Tier 2 — Null:       critical columns are not entirely null
  Tier 3 — Row count:  row totals are within expected bounds

Thresholds
----------
Configurable via module-level constants below.  Override them in tests
without patching by passing keyword arguments to each validator.
"""

from __future__ import annotations

import os
import sys
from typing import NamedTuple

import pandas as pd

_ETL_DIR      = os.path.dirname(os.path.abspath(__file__))
_APP_DIR      = os.path.dirname(_ETL_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# --------------------------------------------------------------------------- #
# Result type
# --------------------------------------------------------------------------- #

class ValidationResult(NamedTuple):
    passed:   bool
    errors:   list[str]
    warnings: list[str]
    stats:    dict


# --------------------------------------------------------------------------- #
# Default thresholds
# --------------------------------------------------------------------------- #

# Sales: warn if fewer than this many rows; error if completely empty
SALES_MIN_ROWS_WARN  = 100      # warn: suspiciously low for a live ERP
SALES_MIN_ROWS_ERROR = 1        # error: truly empty → abort

# Stock: optional dataset — only warn
STOCK_MIN_ROWS_WARN  = 50

# Production: optional dataset — only warn
PROD_MIN_ROWS_WARN   = 1

# Null tolerance: max fraction of nulls in a critical column before erroring
MAX_NULL_FRACTION_CRITICAL  = 0.50    # 50% nulls in a critical column → error
MAX_NULL_FRACTION_WARN      = 0.10    # 10% nulls in any column → warning

# Negative-value columns that should never be negative
SALES_NON_NEGATIVE_COLS = ["grand_total"]
STOCK_NON_NEGATIVE_COLS = ["actual_qty"]


# --------------------------------------------------------------------------- #
# Sales validator
# --------------------------------------------------------------------------- #

SALES_REQUIRED_COLS  = ["name", "transaction_date", "customer", "grand_total"]
SALES_CRITICAL_COLS  = ["transaction_date", "grand_total"]


def validate_sales(
    df: pd.DataFrame,
    min_rows_warn:  int   = SALES_MIN_ROWS_WARN,
    min_rows_error: int   = SALES_MIN_ROWS_ERROR,
    max_null_frac:  float = MAX_NULL_FRACTION_CRITICAL,
) -> ValidationResult:
    """
    Validate the raw Sales Order DataFrame fetched from Frappe.

    Parameters
    ----------
    df             : Raw sales DataFrame (from FrappeClient or CSV).
    min_rows_warn  : Row count below which a WARNING is emitted.
    min_rows_error : Row count below which an ERROR is emitted (abort).
    max_null_frac  : Maximum fraction of nulls in a critical column.

    Returns
    -------
    ValidationResult
    """
    errors:   list[str] = []
    warnings: list[str] = []
    stats:    dict      = {"dataset": "sales", "rows": len(df)}

    # ------------------------------------------------------------------ #
    # Tier 1 — Schema check
    # ------------------------------------------------------------------ #
    missing_cols = [c for c in SALES_REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        errors.append(
            f"Schema: missing required columns: {missing_cols}. "
            f"Found: {list(df.columns)}"
        )
        # Can't proceed with null or range checks without the columns
        return ValidationResult(False, errors, warnings, stats)

    # ------------------------------------------------------------------ #
    # Tier 2 — Row count sanity
    # ------------------------------------------------------------------ #
    row_count = len(df)
    stats["rows"] = row_count

    if row_count < min_rows_error:
        errors.append(
            f"Row count: Sales dataset has {row_count} rows — "
            f"minimum required is {min_rows_error}. ETL cannot continue."
        )
    elif row_count < min_rows_warn:
        warnings.append(
            f"Row count: Sales dataset has only {row_count} rows "
            f"(warn threshold: {min_rows_warn}). "
            "This may indicate an incomplete ERP sync."
        )

    # ------------------------------------------------------------------ #
    # Tier 3 — Null checks on critical columns
    # ------------------------------------------------------------------ #
    for col in SALES_CRITICAL_COLS:
        if col not in df.columns:
            continue
        null_count = int(df[col].isna().sum())
        null_frac  = null_count / max(row_count, 1)
        stats[f"null_{col}"] = null_count

        if null_frac > max_null_frac:
            errors.append(
                f"Nulls: '{col}' has {null_count:,} nulls "
                f"({null_frac:.1%} of rows) — exceeds critical threshold "
                f"of {max_null_frac:.0%}."
            )
        elif null_frac > MAX_NULL_FRACTION_WARN:
            warnings.append(
                f"Nulls: '{col}' has {null_count:,} nulls ({null_frac:.1%})."
            )

    # ------------------------------------------------------------------ #
    # Tier 4 — Value-range checks (non-negative grand_total)
    # ------------------------------------------------------------------ #
    for col in SALES_NON_NEGATIVE_COLS:
        if col not in df.columns:
            continue
        neg_count = int((pd.to_numeric(df[col], errors="coerce") < 0).sum())
        stats[f"negative_{col}"] = neg_count
        if neg_count > 0:
            warnings.append(
                f"Values: '{col}' contains {neg_count:,} negative values. "
                "These rows will be dropped during processing."
            )

    # ------------------------------------------------------------------ #
    # Tier 5 — Duplicate check
    # ------------------------------------------------------------------ #
    dup_count = int(df.duplicated(subset=["name"]).sum())
    stats["duplicates"] = dup_count
    if dup_count > 0:
        warnings.append(
            f"Duplicates: {dup_count:,} duplicate 'name' values found — "
            "they will be deduplicated during processing."
        )

    passed = len(errors) == 0
    return ValidationResult(passed, errors, warnings, stats)


# --------------------------------------------------------------------------- #
# Stock validator
# --------------------------------------------------------------------------- #

STOCK_REQUIRED_COLS = ["name", "item_code", "actual_qty", "warehouse"]
STOCK_CRITICAL_COLS = ["actual_qty"]


def validate_stock(
    df: pd.DataFrame,
    min_rows_warn: int   = STOCK_MIN_ROWS_WARN,
    max_null_frac: float = MAX_NULL_FRACTION_CRITICAL,
) -> ValidationResult:
    """
    Validate the raw Stock (Bin) DataFrame fetched from Frappe.

    Stock is an optional dataset — errors here are demoted to warnings
    so the ETL can proceed with stock = 0 fallback.

    Parameters
    ----------
    df            : Raw stock DataFrame.
    min_rows_warn : Warn threshold for row count.
    max_null_frac : Max null fraction in critical columns.

    Returns
    -------
    ValidationResult  (passed is always True — stock is optional)
    """
    errors:   list[str] = []
    warnings: list[str] = []
    stats:    dict      = {"dataset": "stock", "rows": len(df)}

    if df.empty:
        warnings.append(
            "Stock dataset is empty — stock features will default to 0."
        )
        return ValidationResult(True, errors, warnings, stats)

    # Tier 1 — Schema
    missing_cols = [c for c in STOCK_REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        warnings.append(
            f"Schema: missing expected columns: {missing_cols}. "
            "Stock features may be incomplete."
        )

    row_count     = len(df)
    stats["rows"] = row_count

    # Tier 2 — Row count
    if row_count < min_rows_warn:
        warnings.append(
            f"Row count: Stock dataset has only {row_count} rows "
            f"(warn threshold: {min_rows_warn})."
        )

    # Tier 3 — Nulls in actual_qty
    if "actual_qty" in df.columns:
        null_count = int(df["actual_qty"].isna().sum())
        null_frac  = null_count / max(row_count, 1)
        stats["null_actual_qty"] = null_count

        if null_frac > max_null_frac:
            warnings.append(
                f"Nulls: 'actual_qty' has {null_count:,} nulls "
                f"({null_frac:.1%}) — will be filled with 0 during processing."
            )

    # Tier 4 — Negative actual_qty
    if "actual_qty" in df.columns:
        neg_count = int(
            (pd.to_numeric(df["actual_qty"], errors="coerce") < 0).sum()
        )
        stats["negative_actual_qty"] = neg_count
        if neg_count > 0:
            warnings.append(
                f"Values: 'actual_qty' has {neg_count:,} negative values — "
                "this may indicate return/adjustment entries."
            )

    # Stock is optional — never block the pipeline
    return ValidationResult(True, errors, warnings, stats)


# --------------------------------------------------------------------------- #
# Production validator
# --------------------------------------------------------------------------- #

PROD_REQUIRED_COLS = ["name", "item", "qty", "produced_qty", "status"]
PROD_CRITICAL_COLS = ["qty", "produced_qty"]


def validate_production(
    df: pd.DataFrame,
    min_rows_warn: int   = PROD_MIN_ROWS_WARN,
    max_null_frac: float = MAX_NULL_FRACTION_CRITICAL,
) -> ValidationResult:
    """
    Validate the raw Production (Work Order) DataFrame fetched from Frappe.

    Production is an optional dataset — errors are demoted to warnings.

    Returns
    -------
    ValidationResult  (passed is always True — production is optional)
    """
    errors:   list[str] = []
    warnings: list[str] = []
    stats:    dict      = {"dataset": "production", "rows": len(df)}

    if df.empty:
        warnings.append(
            "Production dataset is empty — production features will default to 0."
        )
        return ValidationResult(True, errors, warnings, stats)

    # Tier 1 — Schema
    missing_cols = [c for c in PROD_REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        warnings.append(
            f"Schema: missing expected columns: {missing_cols}."
        )

    row_count     = len(df)
    stats["rows"] = row_count

    # Tier 2 — Row count
    if row_count < min_rows_warn:
        warnings.append(
            f"Row count: Production dataset has only {row_count} rows."
        )

    # Tier 3 — Nulls
    for col in PROD_CRITICAL_COLS:
        if col not in df.columns:
            continue
        null_count = int(df[col].isna().sum())
        null_frac  = null_count / max(row_count, 1)
        stats[f"null_{col}"] = null_count

        if null_frac > max_null_frac:
            warnings.append(
                f"Nulls: '{col}' has {null_count:,} nulls ({null_frac:.1%})."
            )

    return ValidationResult(True, errors, warnings, stats)


# --------------------------------------------------------------------------- #
# Reporting helper
# --------------------------------------------------------------------------- #

def log_validation_result(
    result: ValidationResult,
    logger,
    dataset_name: str,
) -> None:
    """
    Emit structured log lines for a ValidationResult.

    Parameters
    ----------
    result       : Output of validate_*().
    logger       : Any logger with .info / .warning / .error methods.
    dataset_name : Human-readable label for the dataset (e.g. "sales").
    """
    stats_line = "  ".join(f"{k}={v}" for k, v in result.stats.items())
    logger.info(
        f"Validation [{dataset_name}] {'PASSED' if result.passed else 'FAILED'} | "
        f"{stats_line}",
        extra={"etl_module": "validators"},
    )
    for w in result.warnings:
        logger.warning(
            f"Validation [{dataset_name}] WARNING: {w}",
            extra={"etl_module": "validators"},
        )
    for e in result.errors:
        logger.error(
            f"Validation [{dataset_name}] ERROR: {e}",
            extra={"etl_module": "validators"},
        )
