"""
app/ml/sales/evaluate.py
-------------------------
Sprint 2 — Multi-Model Training & Evaluation Engine.

Trains four algorithms (Random Forest, XGBoost, LightGBM, Gradient Boosting),
tunes each via RandomizedSearchCV or GridSearchCV using grids defined in
config/model_config.yaml, evaluates on RMSE / MAE / R² (and accuracy / F1 when
the target is binary classification), selects the best-performing model, saves
artefacts, and registers the winner in the model registry.

Public API
----------
run_evaluation_pipeline(
    df, feature_cols, target_col,
    models_dir, version, config_path=None
) -> dict

    Returns a summary dict::
        {
          "status":          "success" | "failed",
          "best_model_name": str,
          "best_metrics":    dict,          # rmse, mae, r2, accuracy (opt.)
          "all_results":     list[dict],    # one entry per algorithm
          "model_path":      str,
          "scaler_path":     str,
          "metrics_path":    str,
          "version":         str,
          "registered_entry": dict,
        }

Design notes
------------
- ETL pipeline is never imported or called.
- XGBoost / LightGBM are imported lazily; missing libs fall back to RF.
- Best-model criterion: lowest RMSE on the held-out test set (primary),
  then lowest MAE (tiebreaker). RMSE is well-defined for both regression
  and binary-classification tasks (treating predictions as numeric).
- Tuning is skipped per-algorithm when its param grid is absent or
  strategy == "none".
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

_MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ML_DIR       = os.path.dirname(_MODULE_DIR)
_APP_DIR      = os.path.dirname(_ML_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import joblib
import numpy as np
import yaml
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    train_test_split,
)
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_registry import register_model

log = get_ml_logger("sales_evaluate")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_DEFAULT_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")

# Canonical artefact filenames (relative to models_dir)
_MODEL_FILENAME   = "sales_model.pkl"
_SCALER_FILENAME  = "sales_scaler.pkl"
_METRICS_FILENAME = "sales_metrics.json"

# Algorithms trained in every evaluation run (in this order)
_ALGORITHM_NAMES = ["random_forest", "xgboost", "lightgbm", "gradient_boosting"]


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def run_evaluation_pipeline(
    df,
    feature_cols: List[str],
    target_col: str,
    models_dir: str,
    version: str,
    config_path: str = _DEFAULT_CONFIG_PATH,
) -> Dict[str, Any]:
    """
    Train, tune, evaluate, select, and save the best sales model.

    Parameters
    ----------
    df          : pd.DataFrame   Input feature-engineered dataset.
    feature_cols: list[str]      Feature column names.
    target_col  : str            Target column name.
    models_dir  : str            Directory where artefacts will be saved.
    version     : str            Version tag (e.g. "20260722_214400").
    config_path : str, optional  Path to model_config.yaml.

    Returns
    -------
    dict   Evaluation summary (see module docstring).
    """
    started = datetime.now()
    log.info("=" * 60)
    log.info(f"[evaluate] Multi-model training pipeline started — v{version}")
    log.info("=" * 60)

    # ------------------------------------------------------------------ #
    # 0. Load config
    # ------------------------------------------------------------------ #
    sales_cfg   = _load_sales_config(config_path)
    tuning_cfg  = sales_cfg.get("tuning", {})
    scaler_cfg  = sales_cfg.get("scaler", {})
    algo_defs   = sales_cfg.get("algorithms", {})

    strategy = tuning_cfg.get("strategy", "random").lower()
    n_iter   = int(tuning_cfg.get("n_iter", 8))
    cv       = int(tuning_cfg.get("cv", 3))
    scoring  = tuning_cfg.get("scoring", "neg_root_mean_squared_error")

    log.info(f"[evaluate] Tuning: strategy={strategy}  n_iter={n_iter}  cv={cv}  scoring={scoring}")

    # ------------------------------------------------------------------ #
    # 1. Build feature matrix and target vector
    # ------------------------------------------------------------------ #
    # Guarantee all requested columns exist
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
    if target_col not in df.columns:
        df[target_col] = 0

    if df.empty or len(df) < 5:
        return _failure(
            f"[evaluate] Input DataFrame is empty or too small "
            f"({len(df)} rows). Need at least 5 rows."
        )

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Detect task type
    is_classification = _is_binary_target(y)
    log.info(
        f"[evaluate] Task type: {'classification (binary 0/1)' if is_classification else 'regression'} "
        f"| {len(X):,} rows | {len(feature_cols)} features"
    )

    # ------------------------------------------------------------------ #
    # 2. Train / test split (80/20)
    # ------------------------------------------------------------------ #
    try:
        stratify = y if (is_classification and len(y.unique()) > 1) else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
    except ValueError as exc:
        return _failure(f"[evaluate] Train/test split failed: {exc}")

    log.info(f"[evaluate] Split: train={len(X_train):,}  test={len(X_test):,}")

    # ------------------------------------------------------------------ #
    # 3. Feature scaling
    # ------------------------------------------------------------------ #
    scaler = _build_scaler(scaler_cfg)
    if scaler is not None:
        X_train_s = scaler.fit_transform(X_train)
        X_test_s  = scaler.transform(X_test)
        log.info(f"[evaluate] Scaler: {type(scaler).__name__} applied.")
    else:
        X_train_s, X_test_s = X_train.values, X_test.values
        log.info("[evaluate] Scaler: disabled (passthrough).")

    # ------------------------------------------------------------------ #
    # 4. Build, tune, and evaluate each algorithm candidate
    # ------------------------------------------------------------------ #
    all_results: List[Dict[str, Any]] = []

    for algo_name in _ALGORITHM_NAMES:
        log.info(f"[evaluate] ── Algorithm: {algo_name} ──")
        result = _train_and_evaluate_one(
            algo_name      = algo_name,
            base_params    = algo_defs.get(algo_name, {}),
            tuning_cfg     = tuning_cfg,
            strategy       = strategy,
            n_iter         = n_iter,
            cv             = cv,
            scoring        = scoring,
            X_train        = X_train_s,
            X_test         = X_test_s,
            y_train        = y_train,
            y_test         = y_test,
            is_classification = is_classification,
        )
        all_results.append(result)
        log.info(
            f"[evaluate] {algo_name}: RMSE={result['rmse']:.4f}  "
            f"MAE={result['mae']:.4f}  R²={result['r2']:.4f}"
            + (f"  Acc={result.get('accuracy', 'n/a'):.4f}" if is_classification else "")
        )

    # ------------------------------------------------------------------ #
    # 5. Select best model (lowest RMSE → lowest MAE)
    # ------------------------------------------------------------------ #
    successful = [r for r in all_results if r.get("status") == "ok"]
    if not successful:
        msg = "[evaluate] All algorithms failed. Cannot select best model."
        log.error(msg)
        return _failure(msg)

    best_result = min(successful, key=lambda r: (r["rmse"], r["mae"]))
    best_model  = best_result["model"]
    best_name   = best_result["name"]
    best_metrics = {k: best_result[k] for k in ("rmse", "mae", "r2") if k in best_result}
    if is_classification and "accuracy" in best_result:
        best_metrics["accuracy"] = best_result["accuracy"]
        best_metrics["f1_score"] = best_result.get("f1_score", 0.0)

    log.info(f"[evaluate] ★ Best model: {best_name}  RMSE={best_result['rmse']:.4f}")

    # ------------------------------------------------------------------ #
    # 6. Save artefacts
    # ------------------------------------------------------------------ #
    os.makedirs(models_dir, exist_ok=True)

    model_path  = os.path.join(models_dir, _MODEL_FILENAME)
    scaler_path = os.path.join(models_dir, _SCALER_FILENAME)
    metrics_path = os.path.join(models_dir, _METRICS_FILENAME)

    joblib.dump(best_model, model_path)
    log.info(f"[evaluate] Model saved  → {model_path}")

    if scaler is not None:
        joblib.dump(scaler, scaler_path)
        log.info(f"[evaluate] Scaler saved → {scaler_path}")

    # Build the full metrics payload for JSON
    metrics_payload = {
        "version":         version,
        "best_model":      best_name,
        "trained_at":      started.isoformat(),
        **best_metrics,
        "all_results":     _serialisable_results(all_results),
        "feature_cols":    feature_cols,
        "target_col":      target_col,
        "train_rows":      int(len(X_train)),
        "test_rows":       int(len(X_test)),
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2, default=str)
    log.info(f"[evaluate] Metrics saved → {metrics_path}")

    # ------------------------------------------------------------------ #
    # 7. Register model in registry
    # ------------------------------------------------------------------ #
    reg_entry = register_model(
        model_name = "sales",
        model_type = best_name,
        version    = version,
        accuracy   = float(best_metrics.get("accuracy", best_metrics.get("r2", 0.0))),
        metrics    = best_metrics,
        filepath   = model_path,
    )

    elapsed = (datetime.now() - started).total_seconds()
    log.info(f"[evaluate] Pipeline complete in {elapsed:.1f}s")
    log.info("=" * 60)

    return {
        "status":           "success",
        "best_model_name":  best_name,
        "best_metrics":     best_metrics,
        "all_results":      _serialisable_results(all_results),
        "model_path":       model_path,
        "scaler_path":      scaler_path if scaler is not None else None,
        "metrics_path":     metrics_path,
        "version":          version,
        "registered_entry": reg_entry,
    }


# --------------------------------------------------------------------------- #
# Private: per-algorithm training + evaluation
# --------------------------------------------------------------------------- #

def _train_and_evaluate_one(
    algo_name: str,
    base_params: dict,
    tuning_cfg: dict,
    strategy: str,
    n_iter: int,
    cv: int,
    scoring: str,
    X_train,
    X_test,
    y_train,
    y_test,
    is_classification: bool,
) -> Dict[str, Any]:
    """Instantiate, tune, fit, and evaluate a single algorithm candidate."""
    result: Dict[str, Any] = {"name": algo_name}

    try:
        # ── Build estimator ──────────────────────────────────────────── #
        estimator = _build_estimator(algo_name, base_params, is_classification)
        if estimator is None:
            result["status"] = "skipped"
            result["error"]  = "Could not build estimator"
            _zero_metrics(result)
            return result

        # ── Hyperparameter tuning ────────────────────────────────────── #
        param_grid = tuning_cfg.get(algo_name, {})

        if strategy != "none" and param_grid:
            # Convert None placeholders (from YAML) to Python None
            param_grid = _sanitise_grid(param_grid)

            searcher = (
                RandomizedSearchCV(
                    estimator,
                    param_distributions=param_grid,
                    n_iter=min(n_iter, _grid_size(param_grid)),
                    cv=cv,
                    scoring=scoring,
                    random_state=42,
                    n_jobs=-1,
                    refit=True,
                )
                if strategy == "random"
                else GridSearchCV(
                    estimator,
                    param_grid=param_grid,
                    cv=cv,
                    scoring=scoring,
                    n_jobs=-1,
                    refit=True,
                )
            )
            log.info(
                f"[evaluate]   {algo_name}: tuning ({strategy} search, "
                f"grid_params={list(param_grid.keys())})"
            )
            searcher.fit(X_train, y_train)
            best_estimator = searcher.best_estimator_
            log.info(f"[evaluate]   {algo_name}: best_params={searcher.best_params_}")
        else:
            log.info(f"[evaluate]   {algo_name}: no tuning grid — fitting with base params.")
            estimator.fit(X_train, y_train)
            best_estimator = estimator

        # ── Evaluate ─────────────────────────────────────────────────── #
        y_pred = best_estimator.predict(X_test)

        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae  = float(mean_absolute_error(y_test, y_pred))
        r2   = float(r2_score(y_test, y_pred))

        result.update({"rmse": round(rmse, 6), "mae": round(mae, 6), "r2": round(r2, 6)})

        if is_classification:
            acc = float(accuracy_score(y_test, y_pred))
            f1  = float(f1_score(y_test, y_pred, zero_division=0))
            result.update({"accuracy": round(acc, 6), "f1_score": round(f1, 6)})

        result["model"]  = best_estimator
        result["status"] = "ok"

    except Exception as exc:
        log.warning(f"[evaluate]   {algo_name} failed: {exc}", exc_info=False)
        result["status"] = "error"
        result["error"]  = str(exc)
        _zero_metrics(result)

    return result


# --------------------------------------------------------------------------- #
# Private: model factory
# --------------------------------------------------------------------------- #

def _build_estimator(algo_name: str, params: dict, is_classification: bool) -> Optional[Any]:
    """Instantiate the correct estimator class for algo_name."""
    # Strip keys that sklearn doesn't recognise for specific algos
    p = dict(params)

    if algo_name == "random_forest":
        _drop_keys(p, ["eval_metric", "verbose", "num_leaves",
                        "colsample_bytree", "subsample", "learning_rate"])
        return RandomForestClassifier(**p)

    elif algo_name == "xgboost":
        try:
            from xgboost import XGBClassifier
            _drop_keys(p, ["num_leaves"])
            return XGBClassifier(**p)
        except ImportError:
            log.warning("[evaluate] XGBoost not installed — using RandomForest fallback.")
            safe = {k: v for k, v in p.items()
                    if k in ("n_estimators", "max_depth", "random_state", "n_jobs")}
            return RandomForestClassifier(**safe)

    elif algo_name == "lightgbm":
        try:
            from lightgbm import LGBMClassifier
            _drop_keys(p, ["eval_metric", "colsample_bytree"])
            return LGBMClassifier(**p)
        except ImportError:
            log.warning("[evaluate] LightGBM not installed — using RandomForest fallback.")
            safe = {k: v for k, v in p.items()
                    if k in ("n_estimators", "max_depth", "random_state", "n_jobs")}
            return RandomForestClassifier(**safe)

    elif algo_name == "gradient_boosting":
        _drop_keys(p, ["eval_metric", "verbose", "num_leaves",
                        "colsample_bytree", "n_jobs"])
        return GradientBoostingClassifier(**p)

    else:
        log.warning(f"[evaluate] Unknown algorithm '{algo_name}' — skipping.")
        return None


# --------------------------------------------------------------------------- #
# Private: scaler factory
# --------------------------------------------------------------------------- #

def _build_scaler(scaler_cfg: dict) -> Optional[Any]:
    if not scaler_cfg.get("enabled", False):
        return None
    t = scaler_cfg.get("type", "standard").lower()
    if t == "minmax":
        return MinMaxScaler()
    if t == "robust":
        return RobustScaler()
    return StandardScaler()


# --------------------------------------------------------------------------- #
# Private: config helpers
# --------------------------------------------------------------------------- #

def _load_sales_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        log.warning(f"[evaluate] Config not found at {config_path}. Using defaults.")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("sales", {})


def _is_binary_target(y) -> bool:
    unique = set(y.dropna().unique())
    return unique.issubset({0, 1, 0.0, 1.0, True, False})


def _sanitise_grid(grid: dict) -> dict:
    """Replace YAML null → Python None in param grid values."""
    return {
        k: [None if v is None else v for v in vals]
        for k, vals in grid.items()
        if isinstance(vals, list)
    }


def _grid_size(grid: dict) -> int:
    """Total number of combinations in a param grid."""
    size = 1
    for vals in grid.values():
        if isinstance(vals, list):
            size *= len(vals)
    return max(size, 1)


def _drop_keys(d: dict, keys: list) -> None:
    """Remove keys from dict in-place (silently)."""
    for k in keys:
        d.pop(k, None)


# --------------------------------------------------------------------------- #
# Private: result serialisation helpers
# --------------------------------------------------------------------------- #

def _serialisable_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return results list with non-serialisable 'model' object removed."""
    out = []
    for r in results:
        entry = {k: v for k, v in r.items() if k != "model"}
        out.append(entry)
    return out


def _zero_metrics(result: dict) -> None:
    """Fill metric keys with 0.0 for failed / skipped runs."""
    for key in ("rmse", "mae", "r2", "accuracy", "f1_score"):
        result.setdefault(key, 0.0)


def _failure(message: str) -> Dict[str, Any]:
    return {
        "status":           "failed",
        "error":            message,
        "best_model_name":  None,
        "best_metrics":     {},
        "all_results":      [],
        "model_path":       None,
        "scaler_path":      None,
        "metrics_path":     None,
        "version":          None,
        "registered_entry": None,
    }


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    from app.ml.sales.sales_feature_engineering import load_and_preprocess_sales_data
    from app.ml.common.model_loader import load_config

    cfg_yaml     = load_config()
    sales_cfg    = cfg_yaml.get("sales", {})
    feature_cols = sales_cfg.get("features", [])
    target_col   = sales_cfg.get("target", "target_decision")
    version      = datetime.now().strftime("%Y%m%d_%H%M%S")
    models_dir   = os.path.join(_PROJECT_ROOT, "models", "sales")

    df = load_and_preprocess_sales_data()
    result = run_evaluation_pipeline(df, feature_cols, target_col, models_dir, version)

    print(f"\nStatus     : {result['status']}")
    print(f"Best model : {result['best_model_name']}")
    print(f"Metrics    : {result['best_metrics']}")
    print(f"Artefacts  : {result['model_path']}")
    print(f"            {result['scaler_path']}")
    print(f"            {result['metrics_path']}")
