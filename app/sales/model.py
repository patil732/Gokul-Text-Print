"""
app/sales/model.py
------------------
Random Forest classifier for sales demand forecasting.

This is the authoritative definition of the sales model architecture.
It owns:
  - FEATURE_COLS  — the exact feature list the model expects at inference time.
  - MODEL_PATH    — where the trained artefact is persisted on disk.
  - build()       — factory that returns a freshly configured, untrained model.
  - load()        — loads the trained artefact from MODEL_PATH.
  - save()        — persists a trained model to MODEL_PATH.

The inventory module has its own parallel model.py and a separate MODEL_PATH;
the two artefacts never share a file.
"""

import os
import sys
import joblib
from sklearn.ensemble import RandomForestClassifier

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import settings
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Single source of truth for the feature contract
# Keep this list in sync with app/sales/preprocess.py
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

# Sales model artefact is stored separately from any future inventory model
MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "sales_decision_model.pkl")


def build() -> RandomForestClassifier:
    """
    Return a freshly configured, **untrained** RandomForestClassifier.

    Hyperparameters are kept identical to the original models/train_model.py
    implementation so existing training results remain reproducible.

    Returns
    -------
    RandomForestClassifier
        Untrained model instance.
    """
    return RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1,          # use all available CPU cores during training
    )


def save(model: RandomForestClassifier, path: str = MODEL_PATH) -> None:
    """
    Persist a trained model to disk using joblib.

    Parameters
    ----------
    model : RandomForestClassifier
        A fitted model instance.
    path : str
        Destination file path.  Parent directory is created if absent.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logger.info(f"[sales.model] Model saved → {path}")


def load(path: str = MODEL_PATH) -> RandomForestClassifier:
    """
    Load the trained sales model from disk.

    Parameters
    ----------
    path : str
        Path to the serialised model file.

    Returns
    -------
    RandomForestClassifier
        The loaded, fitted model.

    Raises
    ------
    FileNotFoundError
        If the model artefact does not exist at *path*.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[sales.model] No trained model found at {path}. "
            "Run app/sales/train.py first."
        )
    model = joblib.load(path)
    logger.info(f"[sales.model] Model loaded from {path}")
    return model
