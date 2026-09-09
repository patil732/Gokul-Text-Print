"""
app/rag/chat_history.py
------------------------
Sprint 4 — RAG Knowledge Engine

Database persistence and retrieval for the ``chat_history`` table:
  - Save single-turn question/answer interactions with cited sources.
  - Paginated retrieval of chat logs ordered by timestamp descending.
"""

from __future__ import annotations

import json
import math
import os
import sys
import uuid
from typing import Any

# --------------------------------------------------------------------------- #
# Project root on sys.path
# --------------------------------------------------------------------------- #
_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.db  import get_db_connection  # noqa: E402
from utils.logger import logger             # noqa: E402


def _row_to_dict(row) -> dict[str, Any]:
    """Convert an sqlite3.Row or mapping to a standard dict and parse JSON."""
    d = dict(row)
    if "retrieved_documents" in d and isinstance(d["retrieved_documents"], str):
        try:
            d["retrieved_documents"] = json.loads(d["retrieved_documents"])
        except (json.JSONDecodeError, TypeError):
            d["retrieved_documents"] = []
    if "is_manager" in d:
        d["is_manager"] = bool(d["is_manager"])
    else:
        d["is_manager"] = (d.get("user") == "manager")
    return d


def save_chat_turn(
    question: str,
    answer: str,
    sources: list[dict[str, Any]],
    user: str = "system",
    is_manager: bool = False,
) -> str:
    """
    Persist a Q&A interaction to ``chat_history``.

    Parameters
    ----------
    question : str
        The user's question.
    answer : str
        The generated answer text.
    sources : list[dict]
        List of source citations, e.g. ``[{"document": "...", "page": ...}]``.
    user : str
        Identity of the user / session.
    is_manager : bool
        Whether this turn went through the Manager Agent orchestrator.

    Returns
    -------
    str
        The assigned ``chat_id`` (UUID string).
    """
    chat_id = str(uuid.uuid4())
    retrieved_json = json.dumps(sources or [])
    is_mgr_int = 1 if is_manager else 0

    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE chat_history ADD COLUMN is_manager INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass

    conn.execute(
        """
        INSERT INTO chat_history (chat_id, user, question, answer, retrieved_documents, is_manager)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (chat_id, user or "system", question, answer, retrieved_json, is_mgr_int),
    )
    conn.commit()
    conn.close()

    logger.info(f"[chat_history] Saved chat turn {chat_id} (user='{user}', is_manager={is_manager})")
    return chat_id


def get_chat_history(
    page: int = 1,
    limit: int = 20,
    user: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve paginated chat history ordered by timestamp descending.

    Parameters
    ----------
    page : int
        1-based page index (defaults to 1).
    limit : int
        Number of entries per page (clamped between 1 and 100, default 20).
    user : str | None
        Optional filter by user name.

    Returns
    -------
    dict
        ``{"total": int, "page": int, "limit": int, "pages": int, "history": list[dict]}``
    """
    page_num = max(1, page)
    limit_num = max(1, min(100, limit))
    offset = (page_num - 1) * limit_num

    conn = get_db_connection()

    if user:
        total = conn.execute(
            "SELECT COUNT(*) as count FROM chat_history WHERE user = ?",
            (user,),
        ).fetchone()["count"]

        rows = conn.execute(
            """
            SELECT chat_id, user, question, answer, retrieved_documents, timestamp, is_manager
            FROM chat_history
            WHERE user = ?
            ORDER BY timestamp DESC, rowid DESC
            LIMIT ? OFFSET ?
            """,
            (user, limit_num, offset),
        ).fetchall()
    else:
        total = conn.execute(
            "SELECT COUNT(*) as count FROM chat_history"
        ).fetchone()["count"]

        rows = conn.execute(
            """
            SELECT chat_id, user, question, answer, retrieved_documents, timestamp, is_manager
            FROM chat_history
            ORDER BY timestamp DESC, rowid DESC
            LIMIT ? OFFSET ?
            """,
            (limit_num, offset),
        ).fetchall()

    conn.close()

    pages = math.ceil(total / limit_num) if total > 0 else 0
    history = [_row_to_dict(r) for r in rows]

    return {
        "total": total,
        "page": page_num,
        "limit": limit_num,
        "pages": pages,
        "history": history,
    }
