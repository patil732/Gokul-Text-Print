"""
app/etl/logger.py
-----------------
Dedicated structured logger for the ETL pipeline.

Writes to TWO sinks simultaneously:
  1. logs/etl.log  — rotating file (10 MB / 5 backups), survives restarts
  2. stdout        — console output for interactive runs / container logs

Usage
-----
    from app.etl.logger import etl_logger as log

    log.info("Starting ingestion run")
    log.warning("Sales row count below threshold: 50")
    log.error("Schema validation failed: missing columns ['grand_total']")
    log.critical("Sales dataset is empty — aborting ETL run")

Log format
----------
    2026-07-21 22:05:00,123 | ETL | INFO     | ingestion | Sales: 12,450 rows fetched
    <timestamp>             | ETL | <level>  | <module>  | <message>

The module field comes from the ``extra={"etl_module": "..."}`` pattern or
falls back to ``-`` when not provided.

Rotation
--------
RotatingFileHandler:  maxBytes=10 MB,  backupCount=5
This gives ≈50 MB of ETL history before the oldest log rotates out.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# --------------------------------------------------------------------------- #
# Resolve log file path relative to project root
# --------------------------------------------------------------------------- #
_ETL_DIR      = os.path.dirname(os.path.abspath(__file__))
_APP_DIR      = os.path.dirname(_ETL_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
_LOGS_DIR     = os.path.join(_PROJECT_ROOT, "logs")
ETL_LOG_PATH  = os.path.join(_LOGS_DIR, "etl.log")


# --------------------------------------------------------------------------- #
# Custom formatter — adds ETL module field
# --------------------------------------------------------------------------- #
class _ETLFormatter(logging.Formatter):
    """
    Structured log formatter for ETL events.

    Output:
        2026-07-21 22:05:00,123 | ETL | INFO     | ingestion | message text
    """
    def format(self, record: logging.LogRecord) -> str:
        module = getattr(record, "etl_module", record.module)
        record.etl_module_field = f"{module:<12}"
        return super().format(record)


_FMT    = "%(asctime)s | ETL | %(levelname)-8s | %(etl_module_field)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


# --------------------------------------------------------------------------- #
# Logger factory
# --------------------------------------------------------------------------- #

def _build_etl_logger() -> logging.Logger:
    """Build and return the ETL logger (idempotent — safe to call multiple times)."""
    log = logging.getLogger("etl")

    if log.handlers:        # already configured — return as-is
        return log

    log.setLevel(logging.DEBUG)   # capture everything; handlers filter by level

    formatter = _ETLFormatter(fmt=_FMT, datefmt=_DATEFMT)

    # 1. Rotating file handler → logs/etl.log
    os.makedirs(_LOGS_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        ETL_LOG_PATH,
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    # 2. Stream handler → stdout (same format, INFO+ only)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    # Prevent propagation to root logger (avoids duplicate console output)
    log.propagate = False

    return log


# --------------------------------------------------------------------------- #
# Module-level singleton
# --------------------------------------------------------------------------- #
etl_logger = _build_etl_logger()
