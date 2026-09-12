"""
app/ml/inventory/inventory_training.py
--------------------------------------
Inventory reorder model training pipeline.

  1. Loads preprocessed features via inventory_feature_engineering.py
  2. Reads algorithm choice & hyperparams from config/model_config.yaml via model_loader
  3. Fits model + scaler
  4. Saves inventory_model.pkl and inventory_scaler.pkl to models/inventory/
  5. Computes metrics using inventory_metrics.py
  6. Registers trained model via model_registry.py
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

from sklearn.model_selection import train_test_split

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_loader import (
    create_model_from_config,
    create_scaler_from_config,
    save_model_and_scaler,
    load_config,
)
from app.ml.common.model_registry import register_model
from app.ml.inventory.inventory_feature_engineering import load_and_preprocess_inventory_data
from app.ml.inventory.inventory_metrics import evaluate_inventory_model

log = get_ml_logger("inventory_training")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
INVENTORY_MODELS_DIR = os.path.join(_PROJECT_ROOT, "models", "inventory")


def train_inventory_model(
    data_path: str = None,
    models_dir: str = INVENTORY_MODELS_DIR,
    version: str = None,
) -> Dict[str, Any]:
    """
    Train, save, and register the Inventory model.

    Parameters
    ----------
    data_path  : str, optional
    models_dir : str (target directory, defaults to models/inventory/)
    version    : str, optional (defaults to YYYYMMDD_HHMM timestamp)

    Returns
    -------
    dict
        Training summary dictionary.
    """
    log.info("Starting Inventory Model Training Pipeline ...")

    # 1. Load configuration and feature contract
    cfg = load_config().get("inventory", {})
    algo_name = cfg.get("algorithm", "xgboost")
    feature_cols = cfg.get("features", [
        "total_stock", "warehouse_count", "avg_stock_per_wh", "max_stock_in_wh",
        "stock_concentration", "total_qty_planned", "total_produced", "production_gap",
        "fulfillment_rate", "has_open_orders", "available_qty", "safety_stock",
        "stock_turnover", "days_in_inventory", "fast_moving", "slow_moving",
        "dead_stock", "reorder_level"
    ])
    target_col = cfg.get("target", "reorder_flag")

    version = version or datetime.now().strftime("%Y%m%d_%H%M%S")

    # 2. Feature engineering
    df = load_and_preprocess_inventory_data(data_path)
    if df.empty:
        raise ValueError("[inventory_training] Feature engineering yielded empty dataset.")

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
    model = create_model_from_config("inventory")
    scaler = create_scaler_from_config("inventory")

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

    metrics = evaluate_inventory_model(y_test, y_pred, y_prob)

    # 6. Save model and scaler artefacts
    model_path, scaler_path = save_model_and_scaler(
        model, scaler, models_dir, model_name="inventory_model.pkl", scaler_name="inventory_scaler.pkl"
    )

    # Also sync with default root models/ path if configured
    try:
        from app.inventory.model import MODEL_PATH
        save_model_and_scaler(model, scaler, os.path.dirname(MODEL_PATH), model_name="inventory_rf.pkl", scaler_name="inventory_scaler.pkl")
    except Exception as exc:
        log.warning(f"Could not sync with legacy model path: {exc}")

    # 7. Register model in registry
    reg_entry = register_model(
        model_name="inventory",
        model_type=algo_name,
        version=version,
        accuracy=metrics.get("accuracy", 0.0),
        metrics=metrics,
        filepath=model_path,
    )

    log.info(f"Inventory Training Complete -> Version {version} | Accuracy: {metrics.get('accuracy', 0.0):.4f}")

    return {
        "status": "success",
        "model_name": "inventory",
        "model_type": algo_name,
        "version": version,
        "accuracy": metrics.get("accuracy", 0.0),
        "metrics": metrics,
        "model_path": model_path,
        "scaler_path": scaler_path,
        "registered_entry": reg_entry,
    }


if __name__ == "__main__":
    result = train_inventory_model()
    print("Inventory Training Summary:", result)
