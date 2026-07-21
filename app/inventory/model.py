"""
app/inventory/model.py
----------------------
[STUB] Model definition for the Inventory reorder-prediction module.

This file is the authoritative definition of the inventory model architecture.
It is intentionally kept separate from app/sales/model.py — the two modules
use independent artefacts and may use entirely different algorithms.

Planned model (sprint 2+)
--------------------------
  - Algorithm TBD: RandomForest, GradientBoosting, or LightGBM depending on
    the feature distribution of the inventory dataset.
  - Binary classification: predict whether an item needs reordering (1) or
    has sufficient stock (0).

Artefact path
-------------
  models/inventory_reorder_model.pkl
  (deliberately separate from models/sales_decision_model.pkl)

TODO (sprint 2+)
----------------
  - Define FEATURE_COLS (must stay in sync with inventory/preprocess.py).
  - Implement build() to return an untrained model instance.
  - Implement save() and load() using joblib (same pattern as sales/model.py).
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import settings
from utils.logger    import logger

# --------------------------------------------------------------------------- #
# Feature contract — MUST stay in sync with app/inventory/preprocess.py
# --------------------------------------------------------------------------- #
FEATURE_COLS: list[str] = []   # TODO: define in sprint 2
TARGET_COL = "reorder_flag"

# Inventory model has its own artefact path — never overwritten by sales/train.py
MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "inventory_reorder_model.pkl")


def build():
    """
    [STUB] Return a freshly configured, untrained model instance.

    Returns
    -------
    None — implement in sprint 2.
    """
    # TODO: choose and instantiate the algorithm
    raise NotImplementedError(
        "[inventory.model] build() not implemented yet. "
        "Will be completed in sprint 2."
    )


def save(model, path: str = MODEL_PATH) -> None:
    """
    [STUB] Persist a trained model to disk.

    Returns
    -------
    None — implement in sprint 2.
    """
    raise NotImplementedError(
        "[inventory.model] save() not implemented yet."
    )


def load(path: str = MODEL_PATH):
    """
    [STUB] Load the trained inventory model from disk.

    Returns
    -------
    None — implement in sprint 2.
    """
    raise NotImplementedError(
        "[inventory.model] load() not implemented yet. "
        f"Expected artefact path: {path}"
    )
