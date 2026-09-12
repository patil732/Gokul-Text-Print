"""
app/inventory/predict.py
------------------------
Inference entry point for the Inventory reorder-prediction module.

Exposes two public functions:
  predict_row(row_df)   — classify a single feature row.
  predict_batch(df)     — classify a batch DataFrame.

Both functions load the trained artefacts (model + SHAP explainer) on
every call, suitable for low-frequency API / scheduled use.

This module has NO dependency on app/sales.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
import shap

from app.inventory.model import load, load_shap, FEATURE_COLS, SHAP_PATH
from utils.logger import logger

# Human-readable decision labels
_LABEL_MAP = {1: "Reorder Required", 0: "Stock Sufficient"}

# SHAP feature-name aliases for explainability
_FEATURE_ALIASES = {
    "total_stock":          "Total current stock",
    "warehouse_count":      "Warehouse distribution",
    "avg_stock_per_wh":     "Average warehouse stock",
    "max_stock_in_wh":      "Max warehouse stock",
    "stock_concentration":  "Stock concentration ratio",
    "total_qty_planned":    "Planned production volume",
    "total_produced":       "Completed production volume",
    "production_gap":       "Unfulfilled production gap",
    "fulfillment_rate":     "Fulfillment rate",
    "has_open_orders":      "Open work orders flag",
}


def predict_row(row_df: pd.DataFrame) -> dict:
    """
    Run inference on a single feature row for inventory reorder prediction.

    Parameters
    ----------
    row_df : pd.DataFrame
        A single-row DataFrame containing columns in FEATURE_COLS.

    Returns
    -------
    dict with keys:
        decision    (str)  — "Reorder Required" | "Stock Sufficient"
        prediction  (int)  — raw label (1 or 0)
        confidence  (str)  — "High" | "Medium"
        probability (float)— probability of the predicted class
        reasons     (list) — top-3 SHAP explanations
    """
    clf = load()
    return _infer(clf, row_df)


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run inference on a DataFrame of feature rows.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain all columns in FEATURE_COLS.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with 'prediction' (int) and 'decision' (str) appended.
    """
    clf = load()
    X = _validate_features(df)
    df = df.copy()
    df["prediction"] = clf.predict(X)
    df["decision"]   = df["prediction"].map(_LABEL_MAP)
    logger.info(f"[inventory.predict] Batch inference on {len(df):,} rows complete.")
    return df


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

def _validate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all required feature columns are present; fill missing with 0."""
    missing = set(FEATURE_COLS) - set(df.columns)
    if missing:
        logger.warning(
            f"[inventory.predict] Missing feature columns filled with 0: {missing}"
        )
        for col in missing:
            df[col] = 0.0
    return df[FEATURE_COLS]


def _infer(clf, row_df: pd.DataFrame) -> dict:
    """Core inference logic shared by predict_row and predict_batch."""
    X = _validate_features(row_df.copy())

    prediction   = int(clf.predict(X)[0])
    proba        = clf.predict_proba(X)[0]
    confidence_v = float(proba[prediction])
    confidence   = "High" if confidence_v > 0.70 else "Medium"
    decision     = _LABEL_MAP[prediction]

    reasons = _shap_reasons(clf, X)

    logger.info(
        f"[inventory.predict] Decision={decision} | Confidence={confidence} "
        f"({confidence_v:.2%})"
    )

    return {
        "decision":    decision,
        "prediction":  prediction,
        "confidence":  confidence,
        "probability": round(confidence_v, 4),
        "reasons":     reasons,
    }


def _shap_reasons(clf, X: pd.DataFrame, top_n: int = 3) -> list[str]:
    """
    Return top-N SHAP-driven plain-English explanations.

    Loads the pre-saved shap.TreeExplainer from models/inventory_shap.pkl.
    Falls back gracefully if shap values cannot be calculated.
    """
    try:
        try:
            explainer = load_shap(SHAP_PATH)
        except FileNotFoundError:
            logger.warning(
                "[inventory.predict] SHAP artefact not found - building inline explainer."
            )
            explainer = shap.TreeExplainer(clf)

        if hasattr(explainer, "shap_values"):
            shap_values = explainer.shap_values(X)
        else:
            shap_values = explainer(X).values

        if isinstance(shap_values, list):
            # List of arrays [class_0, class_1]
            vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 3:
                # Shape (n_samples, n_features, n_classes)
                vals = shap_values[0, :, 1] if shap_values.shape[2] > 1 else shap_values[0, :, 0]
            elif shap_values.ndim == 2:
                # Shape (n_samples, n_features)
                vals = shap_values[0]
            else:
                vals = shap_values.flatten()
        else:
            vals = np.array(shap_values).flatten()

        top_indices = np.argsort(np.abs(vals))[-top_n:][::-1]
        return [
            (
                f"{_FEATURE_ALIASES.get(FEATURE_COLS[i], FEATURE_COLS[i].replace('_', ' ')).capitalize()} "
                f"is {'positively' if vals[i] > 0 else 'negatively'} impacting the reorder requirement."
            )
            for i in top_indices
        ]
    except Exception as exc:
        logger.warning(f"[inventory.predict] SHAP explanation failed: {exc}")
        return ["Current stock level relative to reorder threshold is the primary driver."]


if __name__ == "__main__":
    sample_row = pd.DataFrame([{col: 0.0 for col in FEATURE_COLS}])
    result = predict_row(sample_row)
    print("Sample inventory prediction result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
