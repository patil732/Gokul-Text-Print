"""
app/sales/predict.py
--------------------
Inference entry point for the Sales demand-forecasting module.

Exposes two public functions:

  predict_row(row_df)   — classify a single feature row.
  predict_batch(df)     — classify a batch DataFrame.

Both functions load the trained sales model on every call (suitable for
low-frequency API / scheduled use).  For high-frequency usage, call
model.load() once and reuse the returned object.

This module has NO dependency on app/inventory.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
import shap

from app.sales.model import load, FEATURE_COLS
from utils.logger    import logger

# Human-readable decision labels
_LABEL_MAP = {1: "Increase Production", 0: "Reduce Production"}

# SHAP feature-name aliases for explainability
_FEATURE_ALIASES = {
    "sales":        "Current sales",
    "sales_ma_7":   "7-day sales trend",
    "momentum":     "Demand momentum",
    "stock_ratio":  "Inventory efficiency",
}


def predict_row(row_df: pd.DataFrame) -> dict:
    """
    Run inference on a single feature row.

    Parameters
    ----------
    row_df : pd.DataFrame
        A single-row DataFrame containing all columns in FEATURE_COLS.

    Returns
    -------
    dict with keys:
        decision    (str)  — "Increase Production" | "Reduce Production"
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
        Input DataFrame with two new columns appended:
        'prediction' (int) and 'decision' (str).
    """
    clf = load()
    X = _validate_features(df)
    df = df.copy()
    df["prediction"] = clf.predict(X)
    df["decision"]   = df["prediction"].map(_LABEL_MAP)
    logger.info(f"[sales.predict] Batch inference on {len(df):,} rows complete.")
    return df


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

def _validate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all required feature columns are present; fill missing with 0."""
    missing = set(FEATURE_COLS) - set(df.columns)
    if missing:
        logger.warning(
            f"[sales.predict] Missing feature columns filled with 0: {missing}"
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
        f"[sales.predict] Decision={decision} | Confidence={confidence} "
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
    """Return top-N SHAP-driven plain-English explanations."""
    try:
        explainer   = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X)
        vals = (
            shap_values[1] if isinstance(shap_values, list) else shap_values
        ).flatten()
        top_indices = np.argsort(np.abs(vals))[-top_n:][::-1]
        return [
            (
                f"{_FEATURE_ALIASES.get(FEATURE_COLS[i], FEATURE_COLS[i].replace('_', ' ')).capitalize()} "
                f"is {'positively' if vals[i] > 0 else 'negatively'} impacting the forecast."
            )
            for i in top_indices
        ]
    except Exception as exc:
        logger.warning(f"[sales.predict] SHAP explanation failed: {exc}")
        return ["Historical sales trajectory is the primary driver."]


if __name__ == "__main__":
    # Quick smoke-test: build a zero-vector row and run inference
    sample_row = pd.DataFrame([{col: 0.0 for col in FEATURE_COLS}])
    result = predict_row(sample_row)
    print("Sample prediction result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
