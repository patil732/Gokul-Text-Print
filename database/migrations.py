"""
database/migrations.py
----------------------
Database schema migrations script creating:
  1. model_registry(model_id UUID PK, model_name VARCHAR, model_type VARCHAR, version VARCHAR, trained_at TIMESTAMP, accuracy FLOAT)
  2. prediction_history(prediction_id UUID PK, model_name VARCHAR, prediction JSON, created_at TIMESTAMP)
"""

import os
import sys
from database.db import get_db_connection, init_db
from utils.logger import logger


POSTGRES_MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS model_registry (
    model_id    UUID PRIMARY KEY,
    model_name  VARCHAR(100) NOT NULL,
    model_type  VARCHAR(100) NOT NULL,
    version     VARCHAR(50)  NOT NULL,
    trained_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accuracy    FLOAT,
    metrics     JSONB,
    filepath    VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS prediction_history (
    prediction_id UUID PRIMARY KEY,
    model_name    VARCHAR(100) NOT NULL,
    version       VARCHAR(50),
    prediction    JSONB NOT NULL,
    input_data    JSONB,
    confidence    FLOAT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales_prediction_history (
    prediction_id   UUID PRIMARY KEY,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    forecast_period VARCHAR(50) NOT NULL,
    forecast_value  FLOAT NOT NULL,
    recommendation  VARCHAR(100),
    confidence      FLOAT,
    model_version   VARCHAR(50)
);
"""


def run_migrations():
    """
    Execute migrations to create model_registry and prediction_history tables.
    """
    logger.info("Executing database schema migrations ...")
    init_db()
    logger.info("Schema migrations executed successfully.")


if __name__ == "__main__":
    run_migrations()
