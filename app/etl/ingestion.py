"""
app/etl/ingestion.py
--------------------
Validated ERP data ingestion for the ETL pipeline.

Fetches Sales Orders, Stock (Bin), and Work Orders from Frappe,
validates each dataset immediately after fetch, and writes raw CSVs
to data/raw/.

Differences from the legacy pipelines/data_ingestion.py
---------------------------------------------------------
- Uses the dedicated ETL logger (logs/etl.log) instead of the generic
  ai_platform logger, so nightly run failures are traceable.
- Validates each fetched dataset via app/etl/validators before saving,
  emitting structured WARNING / ERROR lines for any anomaly.
- Raises ETLIngestionError on sales data failures (blocking).
  Stock and production failures are logged as warnings; the run continues.
- Uses app/config.cfg paths instead of settings.RAW_DATA_DIR.
- Structured run header / footer so log entries for one run are bookended.

CLI
---
    python -m app.etl.ingestion
    python app/etl/ingestion.py
"""

import os
import sys
import time
from datetime import datetime, timedelta

_ETL_DIR      = os.path.dirname(os.path.abspath(__file__))
_APP_DIR      = os.path.dirname(_ETL_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.etl.logger     import etl_logger as log
from app.etl.validators import (
    validate_sales,
    validate_stock,
    validate_production,
    log_validation_result,
)
from app.config          import cfg
from services.frappe_client import FrappeClient


# --------------------------------------------------------------------------- #
# Custom exception
# --------------------------------------------------------------------------- #

class ETLIngestionError(RuntimeError):
    """Raised when a blocking validation failure prevents ETL from continuing."""


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_MODULE = "ingestion"

# Look back 5 years for sales and production history
_HISTORY_DAYS = 5 * 365


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def run_ingestion() -> dict:
    """
    Fetch, validate, and persist raw ERP data.

    Returns
    -------
    dict
        Summary of the run::
            {
              "status":  "success" | "failed",
              "started": ISO timestamp,
              "elapsed": seconds (float),
              "counts":  {"sales": int, "stock": int, "production": int},
              "errors":  list[str],
              "warnings": list[str],
            }

    Raises
    ------
    ETLIngestionError
        When sales data fails validation — the pipeline cannot proceed
        without sales records.
    """
    started    = datetime.now()
    run_errors: list[str] = []
    run_warns:  list[str] = []
    counts = {"sales": 0, "stock": 0, "production": 0}

    log.info("=" * 60, extra={"etl_module": _MODULE})
    log.info(
        f"ETL INGESTION RUN STARTED — {started.strftime('%Y-%m-%d %H:%M:%S')}",
        extra={"etl_module": _MODULE},
    )
    log.info("=" * 60, extra={"etl_module": _MODULE})

    try:
        os.makedirs(cfg.RAW_DATA_DIR, exist_ok=True)
        client         = FrappeClient()
        cutoff_date    = (datetime.now() - timedelta(days=_HISTORY_DAYS)).strftime("%Y-%m-%d")

        log.info(
            f"History window: >= {cutoff_date}  ({_HISTORY_DAYS} days)",
            extra={"etl_module": _MODULE},
        )

        # ------------------------------------------------------------------ #
        # 1. Sales Orders (MANDATORY)
        # ------------------------------------------------------------------ #
        log.info("Fetching Sales Orders …", extra={"etl_module": _MODULE})
        df_sales = client.fetch_data(
            "Sales Order",
            fields=["name", "transaction_date", "customer", "grand_total", "status"],
            filters=[["transaction_date", ">=", cutoff_date]],
            max_records=100_000,
        )

        result_sales = validate_sales(df_sales)
        log_validation_result(result_sales, log, "sales")
        run_errors.extend(result_sales.errors)
        run_warns.extend(result_sales.warnings)

        if not result_sales.passed:
            msg = (
                f"Sales validation FAILED with {len(result_sales.errors)} error(s). "
                "ETL run aborted — no data written."
            )
            log.critical(msg, extra={"etl_module": _MODULE})
            raise ETLIngestionError(msg)

        _write_csv(df_sales, "sales.csv", "Sales Orders")
        counts["sales"] = len(df_sales)

        # ------------------------------------------------------------------ #
        # 2. Stock / Bin (OPTIONAL)
        # ------------------------------------------------------------------ #
        log.info("Fetching Stock (Bin) …", extra={"etl_module": _MODULE})
        df_stock = client.fetch_data(
            "Bin",
            fields=["name", "item_code", "actual_qty", "warehouse"],
            max_records=100_000,
        )

        result_stock = validate_stock(df_stock)
        log_validation_result(result_stock, log, "stock")
        run_warns.extend(result_stock.warnings)
        # Stock warnings never abort the run

        if not df_stock.empty:
            _write_csv(df_stock, "stock.csv", "Stock")
        else:
            log.warning(
                "Stock CSV not written — dataset was empty.",
                extra={"etl_module": _MODULE},
            )
        counts["stock"] = len(df_stock)

        # ------------------------------------------------------------------ #
        # 3. Work Orders / Production (OPTIONAL)
        # ------------------------------------------------------------------ #
        log.info("Fetching Work Orders …", extra={"etl_module": _MODULE})
        df_prod = client.fetch_data(
            "Work Order",
            fields=["name", "item", "qty", "produced_qty", "status"],
            filters=[["creation", ">=", cutoff_date]],
            max_records=100_000,
        )

        result_prod = validate_production(df_prod)
        log_validation_result(result_prod, log, "production")
        run_warns.extend(result_prod.warnings)

        if not df_prod.empty:
            _write_csv(df_prod, "production.csv", "Work Orders")
        else:
            log.warning(
                "Production CSV not written — dataset was empty.",
                extra={"etl_module": _MODULE},
            )
        counts["production"] = len(df_prod)

    except ETLIngestionError:
        raise   # already logged — let caller handle
    except Exception as exc:
        msg = f"Unexpected error during ingestion: {exc}"
        log.error(msg, exc_info=True, extra={"etl_module": _MODULE})
        run_errors.append(msg)

    # ---------------------------------------------------------------------- #
    # Run footer
    # ---------------------------------------------------------------------- #
    elapsed = (datetime.now() - started).total_seconds()
    status  = "failed" if run_errors else "success"

    log.info("=" * 60, extra={"etl_module": _MODULE})
    log.info(
        f"ETL INGESTION RUN {status.upper()} | "
        f"elapsed={elapsed:.1f}s | "
        f"sales={counts['sales']:,}  stock={counts['stock']:,}  "
        f"production={counts['production']:,}",
        extra={"etl_module": _MODULE},
    )
    if run_errors:
        for e in run_errors:
            log.error(f"  [ERROR] {e}", extra={"etl_module": _MODULE})
    if run_warns:
        log.info(
            f"  {len(run_warns)} warning(s) — see log for details.",
            extra={"etl_module": _MODULE},
        )
    log.info("=" * 60, extra={"etl_module": _MODULE})

    return {
        "status":   status,
        "started":  started.isoformat(),
        "elapsed":  elapsed,
        "counts":   counts,
        "errors":   run_errors,
        "warnings": run_warns,
    }


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _write_csv(df, filename: str, label: str) -> None:
    """Write DataFrame to data/raw/<filename> with structured logging."""
    path = os.path.join(cfg.RAW_DATA_DIR, filename)
    df.to_csv(path, index=False)
    log.info(
        f"Written: {label} -> {path}  ({len(df):,} rows)",
        extra={"etl_module": _MODULE},
    )


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    try:
        summary = run_ingestion()
        print(f"\nIngestion {summary['status'].upper()} in {summary['elapsed']:.1f}s")
        print(f"  Sales:      {summary['counts']['sales']:,}")
        print(f"  Stock:      {summary['counts']['stock']:,}")
        print(f"  Production: {summary['counts']['production']:,}")
        if summary["errors"]:
            sys.exit(1)
    except ETLIngestionError as exc:
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)
