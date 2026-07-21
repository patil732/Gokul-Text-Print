"""
app/ml/common/model_registry.py
--------------------------------
Model registry persistence and metadata tracking.

Saves registration entries to models/registry.json.
Allows registering trained models (name, type, version, trained_at, accuracy)
and fetching the latest version for a given model_name.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.ml.common.logger import get_ml_logger

log = get_ml_logger("model_registry")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGISTRY_JSON_PATH = os.path.join(_PROJECT_ROOT, "models", "registry.json")


def _load_registry_data(filepath: str = REGISTRY_JSON_PATH) -> Dict[str, List[Dict[str, Any]]]:
    """Load registry file content or return empty dictionary if file missing."""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.error(f"Failed to read model registry at {filepath}: {exc}")
        return {}


def _save_registry_data(data: Dict[str, List[Dict[str, Any]]], filepath: str = REGISTRY_JSON_PATH) -> None:
    """Save registry data dictionary to filepath."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


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
    Register a trained model entry in the model registry.

    Parameters
    ----------
    model_name : str   (e.g., 'sales', 'inventory')
    model_type : str   (e.g., 'random_forest', 'xgboost')
    version    : str   (e.g., 'v1.0', '1.0.0', '20260721_2230')
    accuracy   : float
    metrics    : dict, optional
    filepath   : str, optional (path to saved model artefact)

    Returns
    -------
    dict
        The newly registered metadata entry.
    """
    data = _load_registry_data(registry_path)

    entry = {
        "model_name": model_name,
        "model_type": model_type,
        "version": version,
        "trained_at": datetime.now().isoformat(),
        "accuracy": float(accuracy),
        "metrics": metrics or {},
        "filepath": filepath or "",
    }

    if model_name not in data:
        data[model_name] = []

    data[model_name].append(entry)
    _save_registry_data(data, registry_path)

    log.info(
        f"Registered model '{model_name}' v{version} ({model_type}) "
        f"with accuracy={accuracy:.4f} -> {registry_path}"
    )
    return entry


def get_latest_version(model_name: str, registry_path: str = REGISTRY_JSON_PATH) -> Optional[Dict[str, Any]]:
    """
    Fetch the latest registered model version entry for a given model_name.

    Returns None if no entries exist for model_name.
    """
    data = _load_registry_data(registry_path)
    entries = data.get(model_name, [])

    if not entries:
        log.warning(f"No registered models found for '{model_name}' in {registry_path}")
        return None

    # Return the last added entry (chronologically latest)
    latest_entry = entries[-1]
    log.info(f"Retrieved latest version for '{model_name}': v{latest_entry.get('version')} ({latest_entry.get('model_type')})")
    return latest_entry


def list_registered_models(registry_path: str = REGISTRY_JSON_PATH) -> Dict[str, List[Dict[str, Any]]]:
    """List all registered models grouped by model_name."""
    return _load_registry_data(registry_path)
