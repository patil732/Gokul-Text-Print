"""
app/ml/common/model_registry.py
--------------------------------
Model registry database persistence and metadata tracking.

Reads/writes directly to the model_registry database table:
  model_registry(model_id UUID PK, model_name VARCHAR, model_type VARCHAR,
                 version VARCHAR, trained_at TIMESTAMP, accuracy FLOAT,
                 metrics TEXT, filepath TEXT)
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.ml.common.logger import get_ml_logger
from database.db import get_db_connection

log = get_ml_logger("model_registry")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGISTRY_JSON_PATH = os.path.join(_PROJECT_ROOT, "models", "registry.json")


def register_model(
    model_name: str,
    model_type: str,
    version: str,
    accuracy: float,
    metrics: Optional[Dict[str, Any]] = None,
    filepath: Optional[str] = None,
    registry_path: str = REGISTRY_JSON_PATH,
) -> Dict[str, Any]:
    """
    Register a trained model entry in the model_registry database table (and sync file backup).

    Parameters
    ----------
    model_name : str   (e.g., 'sales', 'inventory')
    model_type : str   (e.g., 'random_forest', 'xgboost')
    version    : str   (e.g., 'v1.0', '20260721_2230')
    accuracy   : float
    metrics    : dict, optional
    filepath   : str, optional (path to saved model artefact)

    Returns
    -------
    dict
        The newly registered metadata entry containing UUID model_id.
    """
    model_id = str(uuid.uuid4())
    trained_at = datetime.now().isoformat()

    entry = {
        "model_id": model_id,
        "model_name": model_name,
        "model_type": model_type,
        "version": version,
        "trained_at": trained_at,
        "accuracy": float(accuracy),
        "metrics": metrics or {},
        "filepath": filepath or "",
    }

    # 1. Write to database table model_registry
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO model_registry (model_id, model_name, model_type, version, trained_at, accuracy, metrics, filepath)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                model_id,
                model_name,
                model_type,
                version,
                trained_at,
                float(accuracy),
                json.dumps(metrics or {}),
                filepath or "",
            ),
        )
        conn.commit()
        conn.close()
        log.info(f"Registered model '{model_name}' v{version} (id={model_id}) in database table 'model_registry'")
    except Exception as exc:
        log.error(f"Failed to register model in database: {exc}")

    # 2. Sync file backup (registry.json)
    try:
        data = {}
        if os.path.exists(registry_path):
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        if model_name not in data:
            data[model_name] = []
        data[model_name].append(entry)
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as exc:
        log.warning(f"Could not sync JSON backup registry: {exc}")

    return entry


def get_latest_version(model_name: str, registry_path: str = REGISTRY_JSON_PATH) -> Optional[Dict[str, Any]]:
    """
    Fetch the latest registered model version entry for model_name from database model_registry table.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT model_id, model_name, model_type, version, trained_at, accuracy, metrics, filepath
            FROM model_registry
            WHERE model_name = ?
            ORDER BY trained_at DESC
            LIMIT 1
            """,
            (model_name,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            row_dict = dict(row)
            if isinstance(row_dict.get("metrics"), str):
                try:
                    row_dict["metrics"] = json.loads(row_dict["metrics"])
                except Exception:
                    pass
            log.info(f"Retrieved latest version from DB for '{model_name}': v{row_dict.get('version')}")
            return row_dict
    except Exception as exc:
        log.warning(f"Database query failed for model_registry: {exc}. Falling back to JSON file.")

    # Fallback to JSON file if DB query fails or table empty
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = data.get(model_name, [])
            if entries:
                return entries[-1]
        except Exception:
            pass

    log.warning(f"No registered models found for '{model_name}'")
    return None


def list_registered_models(registry_path: str = REGISTRY_JSON_PATH) -> Dict[str, List[Dict[str, Any]]]:
    """List all registered models from database model_registry table."""
    result = {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT model_id, model_name, model_type, version, trained_at, accuracy, metrics, filepath
            FROM model_registry
            ORDER BY trained_at ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            row_dict = dict(row)
            name = row_dict["model_name"]
            if name not in result:
                result[name] = []
            if isinstance(row_dict.get("metrics"), str):
                try:
                    row_dict["metrics"] = json.loads(row_dict["metrics"])
                except Exception:
                    pass
            result[name].append(row_dict)
        return result
    except Exception as exc:
        log.warning(f"Database list failed for model_registry ({exc}). Using JSON file.")

    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}
