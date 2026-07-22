"""
app/ml/sales/sales_training.py
-------------------------------
Sales model training pipeline (Sprint 2 rewrite).

Orchestrates the multi-model evaluation engine in evaluate.py:

  1. Load & feature-engineer sales data
  2. Delegate to run_evaluation_pipeline() which:
       - trains RF, XGBoost, LightGBM, and Gradient Boosting
       - tunes hyperparameters (RandomizedSearchCV / GridSearchCV)
       - evaluates each on RMSE, MAE, R² (+ accuracy when binary target)
       - selects the best model by lowest RMSE
       - saves sales_model.pkl, sales_scaler.pkl, sales_metrics.json
       - registers the winner in model_registry
  3. Return a summary dict that is a strict superset of the Sprint 1 shape
     so all existing callers (test_sales_ml.py, routes.py, …) continue
     to work without modification.

Sprint 1 return-dict keys preserved
------------------------------------
    status, model_name, model_type, version, accuracy,
    metrics, model_path, scaler_path, registered_entry

Sprint 2 additions
------------------
    all_results, metrics_path, best_model_name
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

_MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ML_DIR       = os.path.dirname(_MODULE_DIR)
_APP_DIR      = os.path.dirname(_ML_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_loader import load_config
from app.ml.sales.sales_feature_engineering import load_and_preprocess_sales_data
from app.ml.sales.evaluate import run_evaluation_pipeline

log = get_ml_logger("sales_training")

SALES_MODELS_DIR = os.path.join(_PROJECT_ROOT, "models", "sales")
_CONFIG_PATH     = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def train_sales_model(
    data_path:  Optional[str] = None,
    models_dir: str           = SALES_MODELS_DIR,
    version:    Optional[str] = None,
) -> Dict[str, Any]:
    """
    Train, evaluate, and register the best Sales model.

    Parameters
    ----------
    data_path  : str, optional
        Path to the input CSV.  Defaults to the ETL processed output.
    models_dir : str
        Directory where artefacts are saved.  Defaults to models/sales/.
    version    : str, optional
        Version tag.  Defaults to a YYYYMMDD_HHMMSS timestamp.

    Returns
    -------
    dict
        {
          # --- Sprint 1 keys (unchanged) ---
          "status":           "success" | "failed",
          "model_name":       "sales",
          "model_type":       <best algorithm name>,
          "version":          str,
          "accuracy":         float,
          "metrics":          dict,          # rmse, mae, r2, accuracy (opt.)
          "model_path":       str,
          "scaler_path":      str | None,
          "registered_entry": dict,
          # --- Sprint 2 additions ---
          "best_model_name":  str,
          "all_results":      list[dict],
          "metrics_path":     str,
        }
    """
    log.info("=" * 60)
    log.info("Sales Training Pipeline — starting (Sprint 2 multi-model mode)")
    log.info("=" * 60)

    version = version or datetime.now().strftime("%Y%m%d_%H%M%S")

    # ------------------------------------------------------------------ #
    # 1. Load configuration
    # ------------------------------------------------------------------ #
    cfg_yaml     = load_config(_CONFIG_PATH)
    sales_cfg    = cfg_yaml.get("sales", {})
    feature_cols = sales_cfg.get("features", [
        "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
        "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
        "momentum", "trend", "stock_ratio",
    ])
    target_col = sales_cfg.get("target", "target_decision")

    log.info(f"[sales_training] Features ({len(feature_cols)}): {feature_cols}")
    log.info(f"[sales_training] Target: {target_col}")

    # ------------------------------------------------------------------ #
    # 2. Feature engineering
    # ------------------------------------------------------------------ #
    df = load_and_preprocess_sales_data(data_path)
    if df.empty:
        raise ValueError(
            "[sales_training] Feature engineering yielded an empty dataset. "
            "Check that the input CSV exists and contains valid sales records."
        )
    log.info(f"[sales_training] Dataset: {len(df):,} rows × {len(df.columns)} cols")

    # ------------------------------------------------------------------ #
    # 3. Delegate to multi-model evaluation engine
    # ------------------------------------------------------------------ #
    result = run_evaluation_pipeline(
        df           = df,
        feature_cols = feature_cols,
        target_col   = target_col,
        models_dir   = models_dir,
        version      = version,
        config_path  = _CONFIG_PATH,
    )

    if result["status"] != "success":
        raise RuntimeError(
            f"[sales_training] Evaluation pipeline failed: {result.get('error')}"
        )

    # ------------------------------------------------------------------ #
    # 4. Optional: sync with legacy root models/ path (best-effort)
    # ------------------------------------------------------------------ #
    _sync_legacy_artefacts(result["model_path"], result.get("scaler_path"))

    # ------------------------------------------------------------------ #
    # 5. Build backward-compatible return dict
    # ------------------------------------------------------------------ #
    best_metrics   = result["best_metrics"]
    best_algo_name = result["best_model_name"]

    # 'accuracy' key: use accuracy if present (classification), else r2
    summary_accuracy = float(
        best_metrics.get("accuracy", best_metrics.get("r2", 0.0))
    )

    log.info(
        f"[sales_training] Complete — best={best_algo_name}  "
        f"RMSE={best_metrics.get('rmse', 0.0):.4f}  "
        f"v={version}"
    )

    return {
        # Sprint 1 keys
        "status":           "success",
        "model_name":       "sales",
        "model_type":       best_algo_name,
        "version":          version,
        "accuracy":         summary_accuracy,
        "metrics":          best_metrics,
        "model_path":       result["model_path"],
        "scaler_path":      result.get("scaler_path"),
        "registered_entry": result["registered_entry"],
        # Sprint 2 additions
        "best_model_name":  best_algo_name,
        "all_results":      result["all_results"],
        "metrics_path":     result["metrics_path"],
    }


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _sync_legacy_artefacts(model_path: str, scaler_path: Optional[str]) -> None:
    """
    Best-effort copy of the winner to the root models/ legacy path
    (models/sales_rf.pkl, models/sales_scaler.pkl) so older prediction
    code that hard-codes those filenames continues to work.
    """
    try:
        import shutil
        legacy_dir = os.path.join(_PROJECT_ROOT, "models")
        os.makedirs(legacy_dir, exist_ok=True)

        if model_path and os.path.exists(model_path):
            dest = os.path.join(legacy_dir, "sales_rf.pkl")
            shutil.copy2(model_path, dest)
            log.info(f"[sales_training] Synced to legacy path: {dest}")

        if scaler_path and os.path.exists(scaler_path):
            dest = os.path.join(legacy_dir, "sales_scaler.pkl")
            shutil.copy2(scaler_path, dest)
    except Exception as exc:
        log.warning(f"[sales_training] Could not sync legacy artefacts: {exc}")


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    res = train_sales_model()
    print(f"\nStatus      : {res['status']}")
    print(f"Best model  : {res['best_model_name']}")
    print(f"Version     : {res['version']}")
    print(f"Accuracy    : {res['accuracy']:.4f}")
    print(f"Metrics     : {res['metrics']}")
    print(f"Model path  : {res['model_path']}")
    print(f"Metrics path: {res['metrics_path']}")
    print("\nAll results:")
    for r in res["all_results"]:
        print(f"  {r['name']:20s}  RMSE={r.get('rmse', 'n/a'):.4f}  MAE={r.get('mae', 'n/a'):.4f}  R²={r.get('r2', 'n/a'):.4f}")
