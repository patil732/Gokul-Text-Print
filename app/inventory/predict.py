"""
app/inventory/predict.py
------------------------
[STUB] Inference entry point for the Inventory reorder-prediction module.

Will expose:
  predict_row(row_df)   — classify a single feature row.
  predict_batch(df)     — classify a batch DataFrame.

This module has NO dependency on app/sales.

TODO (sprint 2+)
----------------
  - Implement predict_row() and predict_batch() once model.load() is ready.
  - Add SHAP or feature-importance explanations for interpretability.
  - Return structured dict: {decision, prediction, confidence, probability, reasons}
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd

from utils.logger import logger

# Human-readable labels (to be used once the model is trained)
_LABEL_MAP = {1: "Reorder Required", 0: "Stock Sufficient"}


def predict_row(row_df: pd.DataFrame) -> dict:
    """
    [STUB] Run inference on a single feature row.

    Parameters
    ----------
    row_df : pd.DataFrame
        A single-row DataFrame containing inventory feature columns.

    Returns
    -------
    dict — implement in sprint 2.

    Raises
    ------
    NotImplementedError
        Always — until sprint 2 implements this function.
    """
    raise NotImplementedError(
        "[inventory.predict] predict_row() is not implemented yet."
    )


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    [STUB] Run inference on a DataFrame of feature rows.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain all columns in app/inventory/model.FEATURE_COLS.

    Returns
    -------
    pd.DataFrame — implement in sprint 2.

    Raises
    ------
    NotImplementedError
        Always — until sprint 2 implements this function.
    """
    raise NotImplementedError(
        "[inventory.predict] predict_batch() is not implemented yet."
    )


if __name__ == "__main__":
    logger.info("[inventory.predict] Inventory prediction module — stub only.")
    print("Inventory predict module is not yet implemented (sprint 2).")
