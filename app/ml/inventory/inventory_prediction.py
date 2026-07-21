"""
app/ml/inventory/inventory_prediction.py
----------------------------------------
Inventory inference module.

Loads the latest registered inventory model and scaler from models/inventory/, runs inference
via prediction_service, and logs prediction entries to prediction_history in database.
"""

import os
import json
from typing import Dict, Any, Union
import pandas as pd

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_loader import load_model_and_scaler, load_config
from app.ml.common.model_registry import get_latest_version
from app.ml.common.prediction_service import predict
from database.db import get_db_connection

log = get_ml_logger("inventory_prediction")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
INVENTORY_MODELS_DIR = os.path.join(_PROJECT_ROOT, "models", "inventory")

_LABEL_MAP = {1: "Reorder Required", 0: "Stock Sufficient"}


def get_latest_inventory_model_and_scaler(models_dir: str = INVENTORY_MODELS_DIR):
    """
    Load the latest inventory model and scaler from models_dir or model_registry.
    """
    model_path = os.path.join(models_dir, "inventory_model.pkl")
    scaler_path = os.path.join(models_dir, "inventory_scaler.pkl")

    if not os.path.exists(model_path):
        # Fallback to legacy path if present
        from app.config import cfg
        model_path = cfg.INVENTORY_MODEL_PATH

    model, scaler = load_model_and_scaler(os.path.dirname(model_path), model_name=os.path.basename(model_path))
    return model, scaler


def log_prediction_to_db(model_name: str, version: str, input_data: Any, prediction: Any, confidence: float) -> None:
    """
    Log a prediction record to the prediction_history table in the SQLite database.
    """
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO prediction_history (model_name, version, input_data, prediction, confidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                model_name,
                version,
                json.dumps(input_data, default=str),
                str(prediction),
                float(confidence) if confidence is not None else 0.0,
            ),
        )
        conn.commit()
        conn.close()
        log.info(f"Logged inventory prediction to DB: model={model_name}, version={version}, prediction={prediction}")
    except Exception as exc:
        log.warning(f"Could not log prediction to DB: {exc}")


def predict_inventory(input_data: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
    """
    Run inventory reorder prediction on single feature dictionary or batch DataFrame.

    Parameters
    ----------
    input_data : dict or pd.DataFrame

    Returns
    -------
    dict
        Structured output containing decision, prediction, confidence, probability, and domain.
    """
    # 1. Fetch feature names from config
    cfg = load_config().get("inventory", {})
    feature_names = cfg.get("features", [
        "total_stock", "warehouse_count", "avg_stock_per_wh", "max_stock_in_wh",
        "stock_concentration", "total_qty_planned", "total_produced", "production_gap",
        "fulfillment_rate", "has_open_orders", "available_qty", "safety_stock",
        "stock_turnover", "days_in_inventory", "fast_moving", "slow_moving",
        "dead_stock", "reorder_level"
    ])

    # 2. Get latest version info & load model + scaler
    reg_entry = get_latest_version("inventory")
    version = reg_entry.get("version", "v1.0") if reg_entry else "v1.0"

    model, scaler = get_latest_inventory_model_and_scaler()

    # 3. Run prediction via common service
    pred_res = predict(model, scaler, input_data, feature_names=feature_names)

    predictions = pred_res["predictions"]
    probabilities = pred_res.get("probabilities")

    raw_pred = int(predictions[0]) if len(predictions) > 0 else 0
    decision = _LABEL_MAP.get(raw_pred, "Stock Sufficient")

    confidence_v = 0.5
    if probabilities is not None and len(probabilities) > 0:
        confidence_v = float(probabilities[0][raw_pred]) if raw_pred < probabilities.shape[1] else float(probabilities[0].max())

    confidence_str = "High" if confidence_v > 0.70 else "Medium"

    output = {
        "status": "success",
        "domain": "inventory",
        "model_name": "inventory",
        "version": version,
        "decision": decision,
        "prediction": raw_pred,
        "confidence": confidence_str,
        "probability": round(confidence_v, 4),
        "is_batch": pred_res.get("is_batch", False),
        "count": pred_res.get("count", 1),
    }

    # 4. Log to database
    log_prediction_to_db(
        model_name="inventory",
        version=version,
        input_data=input_data if isinstance(input_data, dict) else input_data.to_dict(orient="records")[:5],
        prediction=decision,
        confidence=confidence_v,
    )

    return output


def predict_row(row_df_or_dict: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
    return predict_inventory(row_df_or_dict)


def predict_batch(df: pd.DataFrame) -> Dict[str, Any]:
    return predict_inventory(df)
