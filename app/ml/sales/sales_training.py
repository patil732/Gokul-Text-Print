"""
app/ml/sales/sales_training.py
-------------------------------
Sales model training pipeline.

  1. Loads preprocessed features via sales_feature_engineering.py
  2. Reads algorithm choice & hyperparams from config/model_config.yaml via model_loader
  3. Fits model + scaler
  4. Saves sales_model.pkl and sales_scaler.pkl to models/sales/
  5. Computes metrics using sales_metrics.py
  6. Registers trained model via model_registry.py
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_loader import (
    create_model_from_config,
    create_scaler_from_config,
    save_model_and_scaler,
    load_config,
)
from app.ml.common.model_registry import register_model
from app.ml.sales.sales_feature_engineering import load_and_preprocess_sales_data
from app.ml.sales.sales_metrics import evaluate_sales_model

log = get_ml_logger("sales_training")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SALES_MODELS_DIR = os.path.join(_PROJECT_ROOT, "models", "sales")


def train_sales_model(
    data_path: str = None,
    models_dir: str = SALES_MODELS_DIR,
    version: str = None,
) -> Dict[str, Any]:
    """
    Train, save, and register the Sales model.

    Parameters
    ----------
    data_path  : str, optional (path to input dataset)
    models_dir : str (target directory, defaults to models/sales/)
    version    : str, optional (defaults to YYYYMMDD_HHMM timestamp)

    Returns
    -------
    dict
        Training summary dictionary containing status, model_type, version, accuracy, metrics, and artefact paths.
    """
    log.info("Starting Sales Model Training Pipeline ...")

    # 1. Load configuration and feature contract
    cfg = load_config().get("sales", {})
    algo_name = cfg.get("algorithm", "xgboost")
    feature_cols = cfg.get("features", [
        "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
        "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
        "momentum", "trend", "stock_ratio"
    ])
    target_col = cfg.get("target", "target_decision")

    version = version or datetime.now().strftime("%Y%m%d_%H%M%S")

    # 2. Feature engineering
    df = load_and_preprocess_sales_data(data_path)
    if df.empty:
        raise ValueError("[sales_training] Feature engineering yielded empty dataset.")

    # Ensure required columns
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
    if target_col not in df.columns:
        df[target_col] = 0

    X = df[feature_cols]
    y = df[target_col]

    # 3. Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) > 1 else None
    )

    # 4. Instantiate Model & Scaler from config
    model = create_model_from_config("sales")
    scaler = create_scaler_from_config("sales")

    # Fit Scaler if enabled
    if scaler is not None:
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
    else:
        X_train_scaled = X_train
        X_test_scaled = X_test

    # Fit Model
    log.info(f"Fitting '{algo_name}' model on {len(X_train):,} training rows ...")
    model.fit(X_train_scaled, y_train)

    # 5. Evaluate predictions & compute metrics
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled) if hasattr(model, "predict_proba") else None

    metrics = evaluate_sales_model(y_test, y_pred, y_prob)

    # 6. Save model and scaler artefacts
    model_path, scaler_path = save_model_and_scaler(
        model, scaler, models_dir, model_name="sales_model.pkl", scaler_name="sales_scaler.pkl"
    )

    # Also sync with default root models/ path if configured
    try:
        from app.sales.model import MODEL_PATH
        save_model_and_scaler(model, scaler, os.path.dirname(MODEL_PATH), model_name="sales_rf.pkl", scaler_name="sales_scaler.pkl")
    except Exception as exc:
        log.warning(f"Could not sync with legacy model path: {exc}")

    # 7. Register model in registry
    reg_entry = register_model(
        model_name="sales",
        model_type=algo_name,
        version=version,
        accuracy=metrics.get("accuracy", 0.0),
        metrics=metrics,
        filepath=model_path,
    )

    log.info(f"Sales Training Complete -> Version {version} | Accuracy: {metrics.get('accuracy', 0.0):.4f}")

    return {
        "status": "success",
        "model_name": "sales",
        "model_type": algo_name,
        "version": version,
        "accuracy": metrics.get("accuracy", 0.0),
        "metrics": metrics,
        "model_path": model_path,
        "scaler_path": scaler_path,
        "registered_entry": reg_entry,
    }


if __name__ == "__main__":
    result = train_sales_model()
    print("Sales Training Summary:", result)
