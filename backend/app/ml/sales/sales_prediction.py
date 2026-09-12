"""
app/ml/sales/sales_prediction.py
---------------------------------
Sales inference module.

Loads the latest registered sales model and scaler from models/sales/, runs inference
via prediction_service, and logs prediction entries to prediction_history in database.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Union
import pandas as pd

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_loader import load_model_and_scaler, load_config
from app.ml.common.model_registry import get_latest_version
from app.ml.common.prediction_service import predict
from database.db import get_db_connection

log = get_ml_logger("sales_prediction")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SALES_MODELS_DIR = os.path.join(_PROJECT_ROOT, "models", "sales")

_LABEL_MAP = {1: "Increase Production", 0: "Reduce Production"}


def get_latest_sales_model_and_scaler(models_dir: str = SALES_MODELS_DIR):
    """
    Load the latest sales model and scaler from models_dir or model_registry.
    """
    model_path = os.path.join(models_dir, "sales_model.pkl")
    scaler_path = os.path.join(models_dir, "sales_scaler.pkl")

    if not os.path.exists(model_path):
        # Fallback to legacy path if present
        from app.config import cfg
        model_path = cfg.SALES_MODEL_PATH

    model, scaler = load_model_and_scaler(os.path.dirname(model_path), model_name=os.path.basename(model_path))
    return model, scaler


from app.ml.common.prediction_service import predict, log_prediction_record

def log_prediction_to_db(model_name: str, version: str, input_data: Any, prediction: Any, confidence: float) -> None:
    """
    Log a prediction record to the prediction_history table.
    """
    log_prediction_record(
        model_name=model_name,
        prediction=prediction,
        input_data=input_data,
        confidence=confidence,
        version=version,
    )


def predict_sales(input_data: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
    """
    Run sales demand forecasting on single feature dictionary or batch DataFrame.

    Parameters
    ----------
    input_data : dict or pd.DataFrame

    Returns
    -------
    dict
        Structured output containing decision, prediction, confidence, probability, and domain.
    """
    # 2. Get latest version info & load model + scaler
    reg_entry = get_latest_version("sales")
    version = reg_entry.get("version", "v1.0") if reg_entry else "v1.0"

    model, scaler = get_latest_sales_model_and_scaler()

    # 1. Fetch feature names from config or model introspection
    cfg = load_config().get("sales", {})
    feature_names = cfg.get("features", [
        "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
        "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
        "momentum", "trend", "stock_ratio"
    ])

    if hasattr(model, "feature_names_in_"):
        feature_names = list(model.feature_names_in_)
    elif hasattr(model, "n_features_in_") and model.n_features_in_ == 14:
        feature_names = [
            "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
            "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
            "momentum", "trend", "stock_ratio", "month", "day", "dayofweek"
        ]

    # 3. Run prediction via common service
    pred_res = predict(model, scaler, input_data, feature_names=feature_names)


    predictions = pred_res["predictions"]
    probabilities = pred_res.get("probabilities")

    raw_pred = int(predictions[0]) if len(predictions) > 0 else 0
    decision = _LABEL_MAP.get(raw_pred, "Reduce Production")

    confidence_v = 0.5
    if probabilities is not None and len(probabilities) > 0:
        confidence_v = float(probabilities[0][raw_pred]) if raw_pred < probabilities.shape[1] else float(probabilities[0].max())

    confidence_str = "High" if confidence_v > 0.70 else "Medium"
    trained_at = reg_entry.get("trained_at", "") if reg_entry else ""
    model_type = reg_entry.get("model_type", "xgboost") if reg_entry else "xgboost"
    accuracy = reg_entry.get("accuracy", 0.0) if reg_entry else 0.0

    output = {
        "status": "success",
        "domain": "sales",
        "model_name": "sales",
        "version": version,
        "decision": decision,
        "prediction": raw_pred,
        "confidence": confidence_str,
        "probability": round(confidence_v, 4),
        "is_batch": pred_res.get("is_batch", False),
        "count": pred_res.get("count", 1),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_status": {
            "model_type": model_type,
            "version": version,
            "accuracy": round(accuracy, 4),
            "trained_at": trained_at,
        },
    }

    # 4. Log to database
    log_prediction_to_db(
        model_name="sales",
        version=version,
        input_data=input_data if isinstance(input_data, dict) else input_data.to_dict(orient="records")[:5],
        prediction=decision,
        confidence=confidence_v,
    )

    return output


def predict_row(row_df_or_dict: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
    return predict_sales(row_df_or_dict)


def predict_batch(df: pd.DataFrame) -> Dict[str, Any]:
    return predict_sales(df)
