"""
app/ml/common/logger.py
------------------------
Configured Python logging for ML modules with rotating file handlers per module.
Logs are written to logs/{module_name}.log.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_LOGS_DIR = os.path.join(_PROJECT_ROOT, "logs")


def get_ml_logger(module_name: str = "ml_common") -> logging.Logger:
    """
    Returns a configured logger instance that logs to console and to logs/{module_name}.log with rotation.
    """
    logger_name = f"ml.{module_name}"
    log = logging.getLogger(logger_name)

    if log.handlers:
        return log

    log.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    # File handler with rotation
    os.makedirs(_LOGS_DIR, exist_ok=True)
    log_path = os.path.join(_LOGS_DIR, f"{module_name}.log")
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    log.propagate = False
    return log


# Default logger for common ML tools
ml_logger = get_ml_logger("ml_common")
