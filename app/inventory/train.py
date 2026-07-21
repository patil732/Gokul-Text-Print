"""
app/inventory/train.py
----------------------
[STUB] Training entry point for the Inventory reorder-prediction module.

Run this file directly to retrain the inventory model without touching
any sales code:

    python -m app.inventory.train
    # or
    python app/inventory/train.py

This file has NO dependency on app/sales — the two training pipelines are
fully decoupled and safe to run independently or in parallel.

TODO (sprint 2+)
----------------
  1. Load raw stock & production data via data_loader.
  2. Feature-engineer via preprocess.run_and_save().
  3. Split into train / test.
  4. Train the chosen model via model.build() / model.save().
  5. Evaluate and print metrics.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logger import logger


def train() -> None:
    """
    [STUB] Full training pipeline for the inventory module.

    Raises
    ------
    NotImplementedError
        Always — until sprint 2 implements this function.
    """
    # TODO: implement training pipeline (see app/sales/train.py as reference)
    raise NotImplementedError(
        "[inventory.train] train() is not implemented yet. "
        "This will be completed in sprint 2 once the inventory feature set "
        "and model architecture are finalised."
    )


if __name__ == "__main__":
    logger.info("[inventory.train] Starting inventory model training …")
    train()
