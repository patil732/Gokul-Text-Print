"""
database/db.py
--------------
SQLite database initialisation and connection helper.

DB_PATH is sourced from app/config.cfg.DB_PATH, which is derived from
the DATABASE_URL environment variable (set in .env).  The default value
is `sqlite:///ai_decision.db`, which maps to <project_root>/ai_decision.db.

Sprint 4 — RAG Knowledge Engine
    documents table:       PDF document tracking and duplicate detection.
    document_chunks table: extracted text chunks for RAG retrieval.
    chunk_embeddings table: dense vectors per chunk (Step 3).

To point at a different database, set DATABASE_URL in .env:

    # SQLite (default)
    DATABASE_URL=sqlite:///ai_decision.db

    # SQLite at an explicit absolute path
    DATABASE_URL=sqlite:////var/data/platform.db

    # PostgreSQL (DB_PATH will be empty; use DATABASE_URL directly)
    DATABASE_URL=postgresql://user:pass@host:5432/dbname
"""

import os
import sys
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config  import cfg
from utils.logger import logger

# Resolved at import time from DATABASE_URL env var via app/config.py
DB_PATH = cfg.DB_PATH


def init_db() -> None:
    """
    Initialise the SQLite database and create core tables if absent.

    Tables created
    --------------
    users            — login credentials and RBAC role.
    decision_history — audit log of ML decisions surfaced to the dashboard.
    """
    if not DB_PATH:
        logger.warning(
            "[db] DATABASE_URL is not a SQLite URL — skipping SQLite init. "
            "Use a migration tool (e.g. Alembic) for your configured backend."
        )
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT           NOT NULL,
            role     TEXT           NOT NULL CHECK(role IN ('ceo', 'admin'))
        )
    """)

    # Decision history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_history (
            id         INTEGER  PRIMARY KEY AUTOINCREMENT,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP,
            decision   TEXT     NOT NULL,
            confidence TEXT,
            reason     TEXT
        )
    """)

    # Model registry table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_registry (
            model_id   TEXT     PRIMARY KEY,
            model_name TEXT     NOT NULL,
            model_type TEXT     NOT NULL,
            version    TEXT     NOT NULL,
            trained_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            accuracy   REAL,
            metrics    TEXT,
            filepath   TEXT
        )
    """)

    # Prediction history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            prediction_id TEXT     PRIMARY KEY,
            model_name    TEXT     NOT NULL,
            version       TEXT,
            prediction    TEXT     NOT NULL,
            input_data    TEXT,
            confidence    REAL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sales prediction history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_prediction_history (
            prediction_id   TEXT     PRIMARY KEY,
            prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            forecast_period TEXT     NOT NULL,
            forecast_value  REAL     NOT NULL,
            recommendation  TEXT,
            confidence      REAL,
            model_version   TEXT
        )
    """)

    # Documents table (Sprint 4 — RAG Knowledge Engine)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id   TEXT PRIMARY KEY,
            document_name TEXT NOT NULL,
            document_type TEXT NOT NULL,
            upload_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
            uploaded_by   TEXT NOT NULL,
            file_path     TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'active',
            file_hash     TEXT NOT NULL,
            UNIQUE (document_name, file_hash)
        )
    """)

    # Document chunks table (Sprint 4 Step 2 — RAG extraction pipeline)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            chunk_id        TEXT    PRIMARY KEY,
            document_id     TEXT    NOT NULL,
            chunk_index     INTEGER NOT NULL,
            page_number     INTEGER NOT NULL,
            source_document TEXT    NOT NULL,
            chunk_text      TEXT    NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        )
    """)

    # Chunk embeddings table (Sprint 4 Step 3 — embedding backend)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            embedding_id TEXT     PRIMARY KEY,
            chunk_id     TEXT     NOT NULL UNIQUE,
            chunk_hash   TEXT     NOT NULL,
            embedding    TEXT     NOT NULL,
            provider     TEXT     NOT NULL,
            model        TEXT     NOT NULL,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chunk_id) REFERENCES document_chunks(chunk_id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"[db] Database initialised at {DB_PATH}")


def get_db_connection() -> sqlite3.Connection:
    """
    Return an open connection to the SQLite database.

    The connection uses ``sqlite3.Row`` as the row_factory so rows can be
    accessed by column name as well as by index.

    Raises
    ------
    RuntimeError
        If DATABASE_URL is not a SQLite URL (DB_PATH is empty).
    """
    if not DB_PATH:
        raise RuntimeError(
            "[db] get_db_connection() called but DATABASE_URL is not SQLite. "
            f"Current DATABASE_URL: {cfg.DATABASE_URL}"
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    init_db()
    print(f"Database initialised at: {DB_PATH}")
