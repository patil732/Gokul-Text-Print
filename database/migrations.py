"""
database/migrations.py
----------------------
Database schema migrations script creating:
  1. model_registry(model_id UUID PK, ...)
  2. prediction_history(prediction_id UUID PK, ...)
  3. documents(document_id UUID PK, ...) [Sprint 4 Step 1]
  4. document_chunks(chunk_id UUID PK, document_id FK, chunk_index INT,
                     page_number INT, source_document VARCHAR, chunk_text TEXT)
     [Sprint 4 Step 2 — RAG Extraction Pipeline]
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

-- Sprint 4: RAG Knowledge Engine — document upload & management
CREATE TABLE IF NOT EXISTS documents (
    document_id   UUID         PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50)  NOT NULL,
    upload_date   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    uploaded_by   VARCHAR(100) NOT NULL,
    file_path     VARCHAR(512) NOT NULL,
    status        VARCHAR(50)  NOT NULL DEFAULT 'active',
    file_hash     VARCHAR(64)  NOT NULL,
    UNIQUE (document_name, file_hash)
);

-- Sprint 4 Step 2: RAG extraction pipeline — text chunks
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id        UUID         PRIMARY KEY,
    document_id     UUID         NOT NULL REFERENCES documents(document_id),
    chunk_index     INTEGER      NOT NULL,
    page_number     INTEGER      NOT NULL,
    source_document VARCHAR(255) NOT NULL,
    chunk_text      TEXT         NOT NULL
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
