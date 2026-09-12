"""
pipelines/data_ingestion.py
---------------------------
Thin backward-compatibility shim.

All ingestion logic has moved to app/etl/ingestion.py which adds:
  - Validation (schema / null / row-count checks via app/etl/validators)
  - Structured logging to logs/etl.log (RotatingFileHandler)
  - ETLIngestionError for blocking failures

This module delegates immediately to the new implementation so that
existing callers (services/automation.py, etc.) continue to work
without modification.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.etl.ingestion import run_ingestion, ETLIngestionError   # noqa: F401
from utils.logger import logger


def run_data_ingestion():
    """
    Backward-compatible wrapper around app.etl.ingestion.run_ingestion().

    Callers that previously imported run_data_ingestion() from this module
    will continue to work unchanged.  On blocking failure, logs the error
    and re-raises ETLIngestionError.
    """
    try:
        summary = run_ingestion()
        if summary["status"] != "success":
            logger.error(
                f"[pipelines.data_ingestion] ETL run finished with status="
                f"{summary['status']}. Errors: {summary['errors']}"
            )
    except ETLIngestionError as exc:
        logger.error(f"[pipelines.data_ingestion] Blocking failure: {exc}")
        raise


if __name__ == "__main__":
    run_data_ingestion()
