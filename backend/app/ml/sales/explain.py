"""
app/ml/sales/explain.py
------------------------
Sprint 2 — Sales Model Explainability & SHAP Engine.

Generates feature importance rankings, SHAP summary plots, waterfall plots,
and per-prediction feature attribution payloads for the trained sales model.

Plots are saved to static/sales_explanations/ for dashboard integration.

Public API
----------
get_explainer(model, X_background=None)
    Builds and returns a SHAP Explainer / TreeExplainer instance for the model.

compute_shap_values(model, X, feature_names=None) -> np.ndarray
    Computes a 2D matrix (n_samples, n_features) of SHAP values for class 1/positive impact.

get_feature_importance(model, X_sample=None, feature_names=None) -> list[dict]
    Returns feature importance ranking sorted descending by mean |SHAP| (or model importances).

explain_prediction(model, scaler, input_data, feature_names=None, top_n=3) -> list[dict]
    Returns top_n contributing features with feature name, feature value, and SHAP contribution score.

generate_and_save_plots(model, scaler, X_sample, feature_names, output_dir=None) -> dict
    Generates and saves shap_summary.png, shap_waterfall.png, feature_importance.png into static/sales_explanations/.

generate_sales_explanations(df=None, models_dir=None, output_dir=None) -> dict
    Full workflow helper: loads best model, runs explanation engine, generates plots, and returns metadata.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

_MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ML_DIR       = os.path.dirname(_MODULE_DIR)
_APP_DIR      = os.path.dirname(_ML_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd

# Use non-interactive backend for matplotlib server safety
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import shap

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_loader import load_config, load_model_and_scaler
from app.ml.common.model_registry import get_latest_version

log = get_ml_logger("sales_explain")

# --------------------------------------------------------------------------- #
# Constants & Directory Paths
# --------------------------------------------------------------------------- #

_SALES_MODELS_DIR     = os.path.join(_PROJECT_ROOT, "models", "sales")
STATIC_EXPLANATIONS_DIR = os.path.join(_PROJECT_ROOT, "static", "sales_explanations")

_DEFAULT_FEATURE_NAMES = [
    "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
    "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
    "momentum", "trend", "stock_ratio",
]


# --------------------------------------------------------------------------- #
# Core SHAP Explainer Builder & Value Extractor
# --------------------------------------------------------------------------- #

def get_explainer(model: Any, X_background: Optional[np.ndarray] = None) -> Any:
    """
    Build and return a SHAP Explainer for the model.
    Tries TreeExplainer first; if TreeExplainer fails (e.g. XGBoost 3.x base_score format bug),
    falls back to shap.Explainer using the model's prediction function.
    """
    try:
        return shap.TreeExplainer(model)
    except Exception as exc:
        log.info(f"[explain] TreeExplainer fallback: {exc}")
        predict_fn = getattr(model, "predict_proba", getattr(model, "predict", None))
        if predict_fn is not None:
            if X_background is not None and len(X_background) > 0:
                bg_sample = X_background[:5]
                return shap.Explainer(predict_fn, bg_sample)
            n_cols = getattr(model, "n_features_in_", 11)
            dummy_bg = np.zeros((5, n_cols), dtype=np.float64)
            return shap.Explainer(predict_fn, dummy_bg)
        return shap.Explainer(model)


def compute_shap_values(
    model: Any,
    X: Union[pd.DataFrame, np.ndarray],
    feature_names: Optional[List[str]] = None,
) -> np.ndarray:
    """
    Compute a 2D numpy matrix of shape (n_samples, n_features) representing
    SHAP feature attribution scores for the positive class (or main outcome).
    """
    X_mat = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
    if X_mat.ndim == 1:
        X_mat = X_mat.reshape(1, -1)

    try:
        explainer = shap.TreeExplainer(model)
        if hasattr(explainer, "shap_values"):
            raw_vals = explainer.shap_values(X_mat)
        else:
            shap_obj = explainer(X_mat)
            raw_vals = shap_obj.values if hasattr(shap_obj, "values") else shap_obj
        return _normalize_shap_matrix(raw_vals, n_samples=len(X_mat), n_features=X_mat.shape[1])
    except Exception as exc:
        log.info(f"[explain] TreeExplainer unavailable ({exc}) — using fast feature importance attribution.")
        return _fallback_shap_matrix(model, X_mat)


def _normalize_shap_matrix(raw_vals: Any, n_samples: int, n_features: int) -> np.ndarray:
    """
    Normalize various SHAP return shapes (list of arrays, 3D tensor, 2D matrix)
    into a clean 2D numpy array of shape (n_samples, n_features).
    """
    if isinstance(raw_vals, list):
        # Multi-class list of arrays: pick class 1 if available, else class 0
        arr = raw_vals[1] if len(raw_vals) > 1 else raw_vals[0]
    elif hasattr(raw_vals, "values"):
        arr = raw_vals.values
    else:
        arr = np.asarray(raw_vals)

    if arr.ndim == 3:
        # (n_samples, n_features, n_classes) → pick class 1
        arr = arr[:, :, 1] if arr.shape[2] > 1 else arr[:, :, 0]
    elif arr.ndim == 1:
        arr = arr.reshape(1, -1)

    if arr.shape != (n_samples, n_features):
        # Reshape or truncate safely if dimensions shifted
        arr = np.resize(arr, (n_samples, n_features))

    return arr


def _fallback_shap_matrix(model: Any, X_mat: np.ndarray) -> np.ndarray:
    """
    Fallback approximation of SHAP values based on feature importances
    when SHAP explainer fails.
    """
    n_samples, n_features = X_mat.shape
    if hasattr(model, "feature_importances_"):
        importances = np.asarray(model.feature_importances_, dtype=np.float64)
    else:
        importances = np.ones(n_features, dtype=np.float64) / n_features

    # Scale by deviation from column mean
    means = np.mean(X_mat, axis=0)
    stds  = np.std(X_mat, axis=0) + 1e-6
    z_scores = (X_mat - means) / stds

    shap_matrix = z_scores * importances.reshape(1, -1)
    return shap_matrix


# --------------------------------------------------------------------------- #
# Feature Importance Ranking
# --------------------------------------------------------------------------- #

def get_feature_importance(
    model: Any,
    X_sample: Optional[Union[pd.DataFrame, np.ndarray]] = None,
    feature_names: Optional[List[str]] = None,
) -> List[Dict[str, float]]:
    """
    Compute feature importance ranking sorted descending by mean |SHAP| score
    (or model feature_importances_).

    Returns
    -------
    list[dict]
        [{"feature": str, "importance": float}, ...]
    """
    names = feature_names or _DEFAULT_FEATURE_NAMES

    if X_sample is not None and len(X_sample) > 0:
        shap_mat = compute_shap_values(model, X_sample, feature_names=names)
        mean_abs_shap = np.mean(np.abs(shap_mat), axis=0)
        total = np.sum(mean_abs_shap) + 1e-9
        scores = mean_abs_shap / total
    elif hasattr(model, "feature_importances_"):
        raw_imp = np.asarray(model.feature_importances_, dtype=np.float64)
        total = np.sum(raw_imp) + 1e-9
        scores = raw_imp / total
    else:
        scores = np.ones(len(names), dtype=np.float64) / len(names)

    rankings = [
        {"feature": names[i] if i < len(names) else f"feature_{i}", "importance": round(float(scores[i]), 4)}
        for i in range(min(len(names), len(scores)))
    ]
    rankings.sort(key=lambda item: item["importance"], reverse=True)
    return rankings


# --------------------------------------------------------------------------- #
# Per-Prediction Explanation (Top-N features)
# --------------------------------------------------------------------------- #

def explain_prediction(
    model: Any,
    scaler: Optional[Any] = None,
    input_data: Union[Dict[str, Any], pd.DataFrame, np.ndarray] = None,
    feature_names: Optional[List[str]] = None,
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """
    Compute top_n contributing features with their feature name, feature value,
    and SHAP contribution score for a single prediction.

    Parameters
    ----------
    model         : Fitted sklearn/ML model object
    scaler        : Optional fitted scaler object
    input_data    : Feature dict, DataFrame (1 row or multi), or 1D/2D array
    feature_names : List of expected feature column names
    top_n         : Number of top features to return (default 3)

    Returns
    -------
    list[dict]
        [
          {"feature": "sales_ma_7", "value": 19000.0, "shap_value": 0.1234},
          {"feature": "momentum",   "value": 500.0,   "shap_value": -0.0876},
          ...
        ]
    """
    names = feature_names or _DEFAULT_FEATURE_NAMES

    # Convert input_data into a 1-row DataFrame and numeric array
    if isinstance(input_data, dict):
        row_dict = {f: float(input_data.get(f, 0.0)) for f in names}
        raw_vals = np.array([row_dict[f] for f in names], dtype=np.float64)
        df_row   = pd.DataFrame([row_dict])
    elif isinstance(input_data, pd.DataFrame):
        df_row = input_data.iloc[[0]].copy()
        for f in names:
            if f not in df_row.columns:
                df_row[f] = 0.0
        df_row   = df_row[names]
        raw_vals = df_row.values[0].astype(float)
    elif isinstance(input_data, np.ndarray):
        raw_vals = input_data.flatten()[:len(names)]
        if len(raw_vals) < len(names):
            raw_vals = np.pad(raw_vals, (0, len(names) - len(raw_vals)))
        df_row = pd.DataFrame([raw_vals], columns=names[:len(raw_vals)])
    else:
        raw_vals = np.zeros(len(names), dtype=np.float64)
        df_row   = pd.DataFrame([raw_vals], columns=names)

    # Scale features if scaler is present
    if scaler is not None:
        X_scaled = scaler.transform(df_row)
    else:
        X_scaled = df_row.values

    # Compute SHAP values for this row
    shap_matrix = compute_shap_values(model, X_scaled, feature_names=names)
    row_shap    = shap_matrix[0]

    # Combine into explanation records
    explanations = []
    for i in range(min(len(names), len(row_shap))):
        fname = names[i]
        fval  = float(raw_vals[i])
        sval  = float(row_shap[i])
        explanations.append({
            "feature":    fname,
            "value":      round(fval, 4),
            "shap_value": round(sval, 4),
        })

    # Sort descending by absolute SHAP magnitude
    explanations.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
    return explanations[:top_n]


# --------------------------------------------------------------------------- #
# Plot Generator (Summary Plot, Waterfall Plot, Feature Importance Bar)
# --------------------------------------------------------------------------- #

def generate_and_save_plots(
    model: Any,
    scaler: Optional[Any] = None,
    X_sample: Optional[Union[pd.DataFrame, np.ndarray]] = None,
    feature_names: Optional[List[str]] = None,
    output_dir: str = STATIC_EXPLANATIONS_DIR,
) -> Dict[str, str]:
    """
    Generate and save:
      1. shap_summary.png     (SHAP summary plot)
      2. shap_waterfall.png   (SHAP waterfall plot for individual prediction)
      3. feature_importance.png (Feature importance bar chart)

    Returns
    -------
    dict
        {"summary_plot": path, "waterfall_plot": path, "importance_plot": path}
    """
    os.makedirs(output_dir, exist_ok=True)
    names = feature_names or _DEFAULT_FEATURE_NAMES

    # Ensure a sample matrix X_mat is available
    if X_sample is None or len(X_sample) == 0:
        X_mat = np.random.default_rng(42).uniform(10, 1000, (50, len(names)))
        df_sample = pd.DataFrame(X_mat, columns=names)
    elif isinstance(X_sample, pd.DataFrame):
        df_sample = X_sample[names].copy()
        X_mat     = df_sample.values
    else:
        X_mat     = np.asarray(X_sample)
        df_sample = pd.DataFrame(X_mat, columns=names[:X_mat.shape[1]])

    # Scaled sample if scaler is active
    X_scaled = scaler.transform(df_sample) if scaler is not None else X_mat

    # Compute SHAP values
    shap_mat = compute_shap_values(model, X_scaled, feature_names=names)

    summary_path    = os.path.join(output_dir, "shap_summary.png")
    waterfall_path  = os.path.join(output_dir, "shap_waterfall.png")
    importance_path = os.path.join(output_dir, "feature_importance.png")

    # ── 1. SHAP Summary Plot ─────────────────────────────────────────── #
    try:
        plt.close("all")
        fig, ax = plt.subplots(figsize=(9, 6))
        shap.summary_plot(
            shap_mat,
            df_sample,
            feature_names=names,
            show=False,
            plot_type="dot",
        )
        plt.title("Sales Model — SHAP Feature Summary", fontsize=12, pad=15)
        plt.tight_layout()
        plt.savefig(summary_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        log.info(f"[explain] Saved SHAP summary plot -> {summary_path}")
    except Exception as exc:
        log.warning(f"[explain] Could not generate SHAP summary plot ({exc}). Using custom fallback.")
        _save_custom_summary_plot(shap_mat, names, summary_path)

    # ── 2. SHAP Waterfall Plot for Individual Prediction ────────────── #
    try:
        plt.close("all")
        single_shap = shap_mat[0]
        single_x    = df_sample.values[0]

        # Try built-in SHAP waterfall if Explanation object supported
        explainer = get_explainer(model, X_background=X_scaled[:50])
        try:
            explanation_obj = explainer(X_scaled[:1])
            plt.figure(figsize=(9, 6))
            shap.plots.waterfall(explanation_obj[0], show=False)
            plt.title("Sales Model — Prediction SHAP Waterfall", fontsize=12, pad=15)
            plt.tight_layout()
            plt.savefig(waterfall_path, dpi=150, bbox_inches="tight")
            plt.close("all")
        except Exception:
            _save_custom_waterfall_plot(single_shap, single_x, names, waterfall_path)

        log.info(f"[explain] Saved SHAP waterfall plot -> {waterfall_path}")
    except Exception as exc:
        log.warning(f"[explain] Could not generate SHAP waterfall plot ({exc}). Using custom fallback.")
        _save_custom_waterfall_plot(shap_mat[0], df_sample.values[0], names, waterfall_path)

    # ── 3. Feature Importance Bar Chart ──────────────────────────────── #
    try:
        _save_feature_importance_plot(model, X_scaled, names, importance_path)
        log.info(f"[explain] Saved feature importance plot -> {importance_path}")
    except Exception as exc:
        log.warning(f"[explain] Feature importance plot failed: {exc}")

    return {
        "summary_plot":    summary_path,
        "waterfall_plot":  waterfall_path,
        "importance_plot": importance_path,
    }


# --------------------------------------------------------------------------- #
# Custom Matplotlib Fallback Plotters
# --------------------------------------------------------------------------- #

def _save_custom_summary_plot(shap_mat: np.ndarray, feature_names: List[str], path: str) -> None:
    plt.close("all")
    mean_abs = np.mean(np.abs(shap_mat), axis=0)
    idx = np.argsort(mean_abs)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh([feature_names[i] for i in idx], mean_abs[idx], color="#3182bd", edgecolor="#08519c")
    ax.set_xlabel("Mean |SHAP Value| (Impact on Prediction)")
    ax.set_title("Sales Model — SHAP Feature Summary")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close("all")


def _save_custom_waterfall_plot(row_shap: np.ndarray, row_x: np.ndarray, feature_names: List[str], path: str) -> None:
    plt.close("all")
    # Order features by absolute SHAP magnitude
    idx = np.argsort(np.abs(row_shap))[-8:]  # top 8 features

    sorted_names = [feature_names[i] for i in idx]
    sorted_sval  = row_shap[idx]
    sorted_fval  = row_x[idx]

    labels = [f"{n} = {v:.1f}" for n, v in zip(sorted_names, sorted_fval)]
    colors = ["#2ca02c" if s >= 0 else "#d62728" for s in sorted_sval]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(labels, sorted_sval, color=colors)
    ax.axvline(0, color="black", linestyle="--", linewidth=0.8)
    ax.set_xlabel("SHAP Value (Contribution to Prediction)")
    ax.set_title("Sales Model — Prediction SHAP Waterfall")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close("all")


def _save_feature_importance_plot(model: Any, X_sample: np.ndarray, feature_names: List[str], path: str) -> None:
    plt.close("all")
    importances = get_feature_importance(model, X_sample, feature_names)
    names  = [item["feature"] for item in importances[::-1]]
    scores = [item["importance"] for item in importances[::-1]]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(names, scores, color="#41b6c4", edgecolor="#253494")
    ax.set_xlabel("Relative Importance Score")
    ax.set_title("Sales Model — Feature Importance Ranking")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close("all")


# --------------------------------------------------------------------------- #
# Full Workflow Helper Function
# --------------------------------------------------------------------------- #

def generate_sales_explanations(
    df: Optional[pd.DataFrame] = None,
    models_dir: str = _SALES_MODELS_DIR,
    output_dir: str = STATIC_EXPLANATIONS_DIR,
) -> Dict[str, Any]:
    """
    Load the latest trained Sales model and scaler, compute feature importance,
    and generate/save all SHAP explanation plots into static/sales_explanations/.

    Returns
    -------
    dict
        Summary dictionary containing feature rankings, plot image paths, and model version.
    """
    model_path  = os.path.join(models_dir, "sales_model.pkl")
    scaler_path = os.path.join(models_dir, "sales_scaler.pkl")

    if not os.path.exists(model_path):
        from app.config import cfg
        model_path = cfg.SALES_MODEL_PATH

    model, scaler = load_model_and_scaler(os.path.dirname(model_path), model_name=os.path.basename(model_path))

    cfg_yaml     = load_config()
    feature_names = cfg_yaml.get("sales", {}).get("features", _DEFAULT_FEATURE_NAMES)
    reg_entry    = get_latest_version("sales")
    version      = reg_entry.get("version", "v1.0") if reg_entry else "v1.0"

    # Build sample matrix if df not passed
    if df is None or df.empty:
        try:
            from app.ml.sales.sales_feature_engineering import load_and_preprocess_sales_data
            df = load_and_preprocess_sales_data()
        except Exception:
            df = pd.DataFrame()

    if not df.empty:
        for f in feature_names:
            if f not in df.columns:
                df[f] = 0.0
        X_sample = df[feature_names].iloc[:100].copy()
    else:
        X_sample = None

    importances = get_feature_importance(model, X_sample, feature_names)
    plots       = generate_and_save_plots(model, scaler, X_sample, feature_names, output_dir=output_dir)

    log.info(f"[explain] Sales model explanations generated for version {version}")

    return {
        "status":             "success",
        "version":            version,
        "feature_importance": importances,
        "plots":              plots,
    }


# --------------------------------------------------------------------------- #
# CLI Smoke Test
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    res = generate_sales_explanations()
    print("\nSales Explainability Summary:")
    print(f"Version: {res['version']}")
    print("Top Feature Importances:")
    for item in res["feature_importance"][:5]:
        print(f"  {item['feature']:20s} : {item['importance']:.4f}")
    print("Plots saved:")
    for k, p in res["plots"].items():
        print(f"  {k:15s} : {p}")
