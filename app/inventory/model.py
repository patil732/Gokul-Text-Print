"""
app/inventory/model.py
----------------------
Random Forest classifier for inventory reorder prediction.

Authoritative definition of:
  - FEATURE_COLS  — exact feature list expected at training and inference time.
  - TARGET_COL    — binary classification target ("reorder_flag").
  - MODEL_PATH    — serialised RandomForest artefact (models/inventory_rf.pkl).
  - SHAP_PATH     — serialised SHAP TreeExplainer (models/inventory_shap.pkl).
  - build()       — factory for a fresh, untrained model.
  - save()        — persist a fitted model to MODEL_PATH.
  - load()        — load the fitted model from MODEL_PATH.
  - save_shap()   — persist a fitted SHAP explainer to SHAP_PATH.
  - load_shap()   — load the SHAP explainer from SHAP_PATH.

This file is entirely independent from app/sales/model.py.
The two modules use separate artefact files and may diverge in
algorithm choice in future sprints.
"""

import os
import sys
import joblib
from sklearn.ensemble import RandomForestClassifier

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config  import cfg
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Feature contract — MUST stay in sync with app/inventory/preprocess.py
# --------------------------------------------------------------------------- #
FEATURE_COLS = [
    "total_stock",
    "warehouse_count",
    "avg_stock_per_wh",
    "max_stock_in_wh",
    "stock_concentration",
    "total_qty_planned",
    "total_produced",
    "production_gap",
    "fulfillment_rate",
    "has_open_orders",
]

TARGET_COL = "reorder_flag"

# --------------------------------------------------------------------------- #
# Artefact paths — sourced from app/config.py (env: INVENTORY_MODEL_VERSION)
# Never shared with sales module
# --------------------------------------------------------------------------- #
MODEL_PATH = cfg.INVENTORY_MODEL_PATH
SHAP_PATH  = cfg.INVENTORY_SHAP_PATH


# --------------------------------------------------------------------------- #
# Model factory
# --------------------------------------------------------------------------- #
def build() -> RandomForestClassifier:
    """
    Return a freshly configured, **untrained** RandomForestClassifier.

    Hyperparameters are tuned for a wide, sparse item-level dataset:
      - n_estimators=300 : more trees for robustness over many items
      - max_depth=8       : shallower than sales (simpler decision surface)
      - class_weight='balanced' : handles the imbalanced reorder_flag target
        (most items with actual_qty=0 → reorder_flag=1 dominates)

    Returns
    -------
    RandomForestClassifier  Untrained model instance.
    """
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",   # corrects for majority reorder_flag=1 class
    )


# --------------------------------------------------------------------------- #
# Model persistence
# --------------------------------------------------------------------------- #
def save(model: RandomForestClassifier, path: str = MODEL_PATH) -> None:
    """
    Persist a fitted RandomForest to *path* using joblib.

    Parameters
    ----------
    model : RandomForestClassifier  Fitted model.
    path  : str                     Destination (parent dir created if absent).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logger.info(f"[inventory.model] Model saved → {path}")


def load(path: str = MODEL_PATH) -> RandomForestClassifier:
    """
    Load the trained inventory model from *path*.

    Raises
    ------
    FileNotFoundError  If the artefact does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[inventory.model] No trained model at {path}. "
            "Run: python -m app.inventory.train"
        )
    model = joblib.load(path)
    logger.info(f"[inventory.model] Model loaded ← {path}")
    return model


# --------------------------------------------------------------------------- #
# SHAP explainer persistence
# --------------------------------------------------------------------------- #
def save_shap(explainer, path: str = SHAP_PATH) -> None:
    """
    Persist a fitted shap.TreeExplainer to *path* using joblib.

    Parameters
    ----------
    explainer : shap.TreeExplainer  Fitted on X_train after model training.
    path      : str                 Destination (parent dir created if absent).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(explainer, path)
    logger.info(f"[inventory.model] SHAP explainer saved → {path}")


def load_shap(path: str = SHAP_PATH):
    """
    Load the SHAP TreeExplainer from *path*.

    Raises
    ------
    FileNotFoundError  If the explainer artefact does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[inventory.model] No SHAP explainer at {path}. "
            "Run: python -m app.inventory.train"
        )
    explainer = joblib.load(path)
    logger.info(f"[inventory.model] SHAP explainer loaded ← {path}")
    return explainer
