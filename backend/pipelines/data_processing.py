"""
pipelines/data_processing.py
-----------------------------
Thin backward-compatibility shim.

All processing logic has moved to app/etl/processing.py which adds:
  - Re-validation of raw CSVs before any transformation
  - Structured per-step logging to logs/etl.log
  - ETLProcessingError for blocking failures
  - Additional lag / rolling features aligned with app/sales/model.FEATURE_COLS

This module delegates immediately to the new implementation so that
existing callers (services/automation.py, etc.) continue to work
without modification.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.etl.processing import run_processing, ETLProcessingError   # noqa: F401
from utils.logger import logger


def run_data_processing():
    """
    Backward-compatible wrapper around app.etl.processing.run_processing().

    Callers that previously imported run_data_processing() from this module
    will continue to work unchanged.  On blocking failure, logs the error
    and re-raises ETLProcessingError.
    """
    try:
        summary = run_processing()
        if summary["status"] != "success":
            logger.error(
                f"[pipelines.data_processing] ETL run finished with status="
                f"{summary['status']}. Errors: {summary['errors']}"
            )
    except ETLProcessingError as exc:
        logger.error(f"[pipelines.data_processing] Blocking failure: {exc}")
        raise


if __name__ == "__main__":
    run_data_processing()
