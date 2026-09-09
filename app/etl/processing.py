"""
app/etl/processing.py
---------------------
Validated data processing / feature-engineering pipeline for the ETL layer.

Reads raw CSVs written by app/etl/ingestion, re-validates them before
processing (guards against stale / corrupted CSVs on disk), transforms
them into a feature-enriched training dataset, and writes it to
data/processed/training_data.csv.

Differences from legacy pipelines/data_processing.py
------------------------------------------------------
- Uses the dedicated ETL logger (logs/etl.log).
- Validates raw CSVs before any transformation using app/etl/validators.
- Emits structured per-step log lines (schema, row counts, NaN stats).
- Uses app/config.cfg paths instead of settings.*_DATA_DIR.
- Returns a summary dict (compatible with automation.py / Celery tasks).

CLI
---
    python -m app.etl.processing
    python app/etl/processing.py
"""

import os
import sys
from datetime import datetime

_ETL_DIR      = os.path.dirname(os.path.abspath(__file__))
_APP_DIR      = os.path.dirname(_ETL_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import numpy as np
import pandas as pd

from app.etl.logger     import etl_logger as log
from app.etl.validators import (
    validate_sales,
    validate_stock,
    validate_production,
    log_validation_result,
)
from app.config import cfg

_MODULE      = "processing"
_OUTPUT_FILE = "training_data.csv"


# --------------------------------------------------------------------------- #
# Custom exception
# --------------------------------------------------------------------------- #

class ETLProcessingError(RuntimeError):
    """Raised when a blocking error prevents the processing step from completing."""


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def run_processing() -> dict:
    """
    Read raw CSVs, validate, transform, and write the processed dataset.

    Returns
    -------
    dict
        Summary of the run::
            {
              "status":       "success" | "failed",
              "started":      ISO timestamp,
              "elapsed":      float,
              "output_rows":  int,
              "output_path":  str,
              "errors":       list[str],
              "warnings":     list[str],
            }

    Raises
    ------
    ETLProcessingError
        When sales data is missing or invalid — processing cannot continue.
    """
    started     = datetime.now()
    run_errors: list[str] = []
    run_warns:  list[str] = []
    output_rows = 0

    output_path = os.path.join(cfg.PROCESSED_DATA_DIR, _OUTPUT_FILE)

    log.info("=" * 60, extra={"etl_module": _MODULE})
    log.info(
        f"ETL PROCESSING RUN STARTED — {started.strftime('%Y-%m-%d %H:%M:%S')}",
        extra={"etl_module": _MODULE},
    )
    log.info("=" * 60, extra={"etl_module": _MODULE})

    try:
        os.makedirs(cfg.PROCESSED_DATA_DIR, exist_ok=True)

        # ------------------------------------------------------------------ #
        # Step 1 — Load raw CSVs
        # ------------------------------------------------------------------ #
        log.info("Loading raw CSVs …", extra={"etl_module": _MODULE})

        df_sales = _safe_read(os.path.join(cfg.RAW_DATA_DIR, "sales.csv"),     "sales.csv")
        df_stock = _safe_read(os.path.join(cfg.RAW_DATA_DIR, "stock.csv"),     "stock.csv")
        df_prod  = _safe_read(os.path.join(cfg.RAW_DATA_DIR, "production.csv"),"production.csv")

        _log_load_stats(df_sales, "sales")
        _log_load_stats(df_stock, "stock")
        _log_load_stats(df_prod,  "production")

        # ------------------------------------------------------------------ #
        # Step 2 — Re-validate raw data before any transformation
        # ------------------------------------------------------------------ #
        log.info("Validating raw datasets …", extra={"etl_module": _MODULE})

        result_sales = validate_sales(df_sales)
        log_validation_result(result_sales, log, "sales")
        run_errors.extend(result_sales.errors)
        run_warns.extend(result_sales.warnings)

        if not result_sales.passed:
            msg = (
                f"Sales validation FAILED ({len(result_sales.errors)} error(s)). "
                "Processing aborted."
            )
            log.critical(msg, extra={"etl_module": _MODULE})
            raise ETLProcessingError(msg)

        result_stock = validate_stock(df_stock)
        log_validation_result(result_stock, log, "stock")
        run_warns.extend(result_stock.warnings)

        result_prod = validate_production(df_prod)
        log_validation_result(result_prod, log, "production")
        run_warns.extend(result_prod.warnings)

        # ------------------------------------------------------------------ #
        # Step 3 — Clean sales data
        # ------------------------------------------------------------------ #
        log.info("Cleaning sales data …", extra={"etl_module": _MODULE})

        df_sales = df_sales.copy()
        df_sales["transaction_date"] = pd.to_datetime(
            df_sales["transaction_date"], errors="coerce"
        )

        pre_drop = len(df_sales)
        df_sales = df_sales.dropna(subset=["transaction_date", "grand_total"])
        df_sales = df_sales[pd.to_numeric(df_sales["grand_total"], errors="coerce") >= 0]
        df_sales = df_sales.drop_duplicates(subset=["name"])
        df_sales = df_sales.sort_values("transaction_date")
        post_drop = len(df_sales)

        dropped = pre_drop - post_drop
        if dropped > 0:
            log.info(
                f"Cleaning: dropped {dropped:,} rows "
                f"(nulls / negatives / duplicates). {post_drop:,} remain.",
                extra={"etl_module": _MODULE},
            )

        df_sales = df_sales.rename(columns={
            "transaction_date": "date",
            "customer":         "product",
            "grand_total":      "sales",
        })

        # ------------------------------------------------------------------ #
        # Step 4 — Feature engineering
        # ------------------------------------------------------------------ #
        log.info("Engineering features …", extra={"etl_module": _MODULE})

        df_main = df_sales.groupby(["date", "product"])["sales"].sum().reset_index()
        df_main = df_main.sort_values(["product", "date"])

        # Rolling averages
        df_main["sales_ma_3"] = df_main.groupby("product")["sales"].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )
        df_main["sales_ma_7"] = df_main.groupby("product")["sales"].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        df_main["sales_ma_14"] = df_main.groupby("product")["sales"].transform(
            lambda x: x.rolling(window=14, min_periods=1).mean()
        )
        df_main["sales_std_7"] = df_main.groupby("product")["sales"].transform(
            lambda x: x.rolling(window=7, min_periods=1).std().fillna(0)
        )

        # Lag features
        df_main["sales_lag_1"] = df_main.groupby("product")["sales"].shift(1)
        df_main["sales_lag_2"] = df_main.groupby("product")["sales"].shift(2)
        df_main["sales_lag_3"] = df_main.groupby("product")["sales"].shift(3)

        # Growth rate and trend
        df_main["prev_sales"]  = df_main["sales_lag_1"]
        df_main["growth_rate"] = (
            (df_main["sales"] - df_main["prev_sales"])
            / df_main["prev_sales"].replace(0, np.nan)
        )
        df_main["trend"]    = df_main["growth_rate"].apply(
            lambda x: 1 if x > 0.05 else (-1 if x < -0.05 else 0)
        )
        df_main["momentum"] = df_main["sales"] - df_main["sales_lag_3"].fillna(0)

        log.info(
            f"Features: {len(df_main):,} product×date rows with "
            f"{len(df_main.columns)} columns.",
            extra={"etl_module": _MODULE},
        )

        # ------------------------------------------------------------------ #
        # Step 5 — Integrate stock and production
        # ------------------------------------------------------------------ #
        if not df_stock.empty and "actual_qty" in df_stock.columns:
            total_stock = pd.to_numeric(
                df_stock["actual_qty"], errors="coerce"
            ).fillna(0).sum()
            df_main["stock"] = total_stock
            log.info(
                f"Stock: integrated total_actual_qty={total_stock:,.0f}",
                extra={"etl_module": _MODULE},
            )
        else:
            df_main["stock"] = 0
            log.info(
                "Stock: defaulting to 0 (empty or missing data).",
                extra={"etl_module": _MODULE},
            )

        if not df_prod.empty and "produced_qty" in df_prod.columns:
            total_prod = pd.to_numeric(
                df_prod["produced_qty"], errors="coerce"
            ).fillna(0).sum()
            df_main["production"] = total_prod
            log.info(
                f"Production: integrated total_produced_qty={total_prod:,.0f}",
                extra={"etl_module": _MODULE},
            )
        else:
            df_main["production"] = 0
            log.info(
                "Production: defaulting to 0 (empty or missing data).",
                extra={"etl_module": _MODULE},
            )

        # stock_ratio feature
        df_main["stock_ratio"] = df_main["stock"] / (df_main["sales"] + 1)

        # ------------------------------------------------------------------ #
        # Step 6 — Final cleanup
        # ------------------------------------------------------------------ #
        df_main = df_main.replace([np.inf, -np.inf], np.nan)
        df_main = df_main.fillna(0)

        pre_final = len(df_main)
        df_main = df_main[df_main["sales"] >= 0]     # guard against any remnant negatives
        if len(df_main) < pre_final:
            log.warning(
                f"Final cleanup: dropped {pre_final - len(df_main)} rows with negative sales.",
                extra={"etl_module": _MODULE},
            )

        # ------------------------------------------------------------------ #
        # Step 7 — Validate output before writing
        # ------------------------------------------------------------------ #
        nan_cols = df_main.columns[df_main.isna().any()].tolist()
        if nan_cols:
            run_warns.append(
                f"Output still has NaN values in: {nan_cols}. "
                "Check feature engineering logic."
            )
            log.warning(
                f"NaN columns in output: {nan_cols}",
                extra={"etl_module": _MODULE},
            )

        if df_main.empty:
            msg = "Processing produced an empty output DataFrame. Aborting write."
            log.critical(msg, extra={"etl_module": _MODULE})
            raise ETLProcessingError(msg)

        # ------------------------------------------------------------------ #
        # Step 8 — Write output
        # ------------------------------------------------------------------ #
        df_main.to_csv(output_path, index=False)
        output_rows = len(df_main)
        log.info(
            f"Output: {output_rows:,} rows written -> {output_path}",
            extra={"etl_module": _MODULE},
        )

    except ETLProcessingError:
        raise   # already logged
    except Exception as exc:
        msg = f"Unexpected error during processing: {exc}"
        log.error(msg, exc_info=True, extra={"etl_module": _MODULE})
        run_errors.append(msg)
        raise ETLProcessingError(msg) from exc

    # ---------------------------------------------------------------------- #
    # Run footer
    # ---------------------------------------------------------------------- #
    elapsed = (datetime.now() - started).total_seconds()
    status  = "failed" if run_errors else "success"

    log.info("=" * 60, extra={"etl_module": _MODULE})
    log.info(
        f"ETL PROCESSING RUN {status.upper()} | "
        f"elapsed={elapsed:.1f}s | "
        f"output_rows={output_rows:,} | output={output_path}",
        extra={"etl_module": _MODULE},
    )
    if run_warns:
        log.info(
            f"  {len(run_warns)} warning(s) emitted — check etl.log for details.",
            extra={"etl_module": _MODULE},
        )
    log.info("=" * 60, extra={"etl_module": _MODULE})

    return {
        "status":      status,
        "started":     started.isoformat(),
        "elapsed":     elapsed,
        "output_rows": output_rows,
        "output_path": output_path,
        "errors":      run_errors,
        "warnings":    run_warns,
    }


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _safe_read(path: str, label: str) -> pd.DataFrame:
    """Read a CSV safely; return empty DataFrame on any error."""
    if not os.path.exists(path):
        log.warning(
            f"Raw file not found: {path}",
            extra={"etl_module": _MODULE},
        )
        return pd.DataFrame()

    if os.path.getsize(path) == 0:
        log.warning(
            f"Raw file is empty (0 bytes): {path}",
            extra={"etl_module": _MODULE},
        )
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        return df
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        log.error(
            f"Cannot parse {label}: {exc}",
            extra={"etl_module": _MODULE},
        )
        return pd.DataFrame()
    except Exception as exc:
        log.error(
            f"Unexpected error reading {label}: {exc}",
            extra={"etl_module": _MODULE},
        )
        return pd.DataFrame()


def _log_load_stats(df: pd.DataFrame, name: str) -> None:
    """Emit a one-line load summary for a dataset."""
    if df.empty:
        log.warning(
            f"Load [{name}]: empty DataFrame",
            extra={"etl_module": _MODULE},
        )
    else:
        log.info(
            f"Load [{name}]: {len(df):,} rows × {len(df.columns)} columns | "
            f"cols={list(df.columns)}",
            extra={"etl_module": _MODULE},
        )


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    try:
        summary = run_processing()
        print(f"\nProcessing {summary['status'].upper()} in {summary['elapsed']:.1f}s")
        print(f"  Output rows : {summary['output_rows']:,}")
        print(f"  Output path : {summary['output_path']}")
        if summary["warnings"]:
            print(f"  Warnings    : {len(summary['warnings'])}")
        if summary["errors"]:
            sys.exit(1)
    except ETLProcessingError as exc:
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)
