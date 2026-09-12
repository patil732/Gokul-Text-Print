"""
app/sales/model.py
------------------
Random Forest classifier for sales demand forecasting.

Authoritative definition of:
  - FEATURE_COLS  — exact feature list expected at training and inference time.
  - TARGET_COL    — binary classification target.
  - MODEL_PATH    — serialised RandomForest artefact (models/sales_rf.pkl).
  - SHAP_PATH     — serialised SHAP TreeExplainer (models/sales_shap.pkl).
  - build()       — factory for a fresh, untrained model.
  - save()        — persist a fitted model to MODEL_PATH.
  - load()        — load the fitted model from MODEL_PATH.
  - save_shap()   — persist a fitted SHAP explainer to SHAP_PATH.
  - load_shap()   — load the SHAP explainer from SHAP_PATH.

The inventory module has its own parallel model.py and completely
separate artefact paths; the two never overwrite each other.
"""

import os
import sys
import joblib
from sklearn.ensemble import RandomForestClassifier

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config  import cfg
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Feature contract — keep in sync with app/sales/preprocess.py
# --------------------------------------------------------------------------- #
FEATURE_COLS = [
    "sales",
    "sales_lag_1",
    "sales_lag_2",
    "sales_lag_3",
    "sales_ma_3",
    "sales_ma_7",
    "sales_ma_14",
    "sales_std_7",
    "momentum",
    "trend",
    "stock_ratio",
]

TARGET_COL = "target_decision"

# --------------------------------------------------------------------------- #
# Artefact paths — sourced from app/config.py (env: SALES_MODEL_VERSION)
# Never shared with inventory module
# --------------------------------------------------------------------------- #
MODEL_PATH = cfg.SALES_MODEL_PATH
SHAP_PATH  = cfg.SALES_SHAP_PATH


from app.ml.common.model_loader import create_model_from_config
from typing import Any

# --------------------------------------------------------------------------- #
# Model factory
# --------------------------------------------------------------------------- #
def build() -> Any:
    """
    Return a freshly configured, **untrained** model object based on config/model_config.yaml.
    """
    return create_model_from_config("sales")


# --------------------------------------------------------------------------- #
# Model persistence
# --------------------------------------------------------------------------- #
def save(model: Any, path: str = MODEL_PATH) -> None:
    """
    Persist a fitted model to *path* using joblib.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logger.info(f"[sales.model] Model saved -> {path}")


def load(path: str = MODEL_PATH) -> Any:
    """
    Load the trained sales model from *path*.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[sales.model] No trained model at {path}. "
            "Run: python -m app.sales.train"
        )
    model = joblib.load(path)
    logger.info(f"[sales.model] Model loaded <- {path}")
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
    logger.info(f"[sales.model] SHAP explainer saved -> {path}")


def load_shap(path: str = SHAP_PATH):
    """
    Load the SHAP TreeExplainer from *path*.

    Raises
    ------
    FileNotFoundError  If the explainer artefact does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[sales.model] No SHAP explainer at {path}. "
            "Run: python -m app.sales.train"
        )
    explainer = joblib.load(path)
    logger.info(f"[sales.model] SHAP explainer loaded <- {path}")
    return explainer
