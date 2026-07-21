"""
app/ml/common/prediction_service.py
------------------------------------
Generic prediction service interface used by both sales and inventory prediction modules.

Provides predict(model, scaler, input_data, feature_names=None) handling scaling,
single-row dict, and multi-row DataFrame inference seamlessly.
"""

from typing import Any, Optional, Union, Dict, List
import pandas as pd
import numpy as np

from app.ml.common.feature_validator import validate_feature_dataframe, validate_feature_dict
from app.ml.common.logger import get_ml_logger

log = get_ml_logger("prediction_service")


def predict(
    model: Any,
    scaler: Optional[Any] = None,
    input_data: Union[Dict[str, Any], pd.DataFrame] = None,
    feature_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generic prediction function for model inference with optional feature scaling.

    Parameters
    ----------
    model         : Fitted sklearn/ML model object
    scaler        : Optional fitted scaler object (e.g. StandardScaler)
    input_data    : Feature dictionary OR pandas DataFrame
    feature_names : List of expected feature column names (optional)

    Returns
    -------
    dict
        Structured prediction output::
            {
                "predictions": np.ndarray | list,
                "probabilities": np.ndarray | None,
                "is_batch": bool,
                "count": int,
            }
    """
    if input_data is None:
        raise ValueError("input_data cannot be None")

    is_dict = isinstance(input_data, dict)

    if is_dict:
        if feature_names:
            sanitized_dict = validate_feature_dict(input_data, feature_names)
            X = pd.DataFrame([sanitized_dict])
        else:
            X = pd.DataFrame([input_data])
    elif isinstance(input_data, pd.DataFrame):
        if feature_names:
            X, _ = validate_feature_dataframe(input_data, feature_names)
        else:
            X = input_data.copy()
    else:
        raise TypeError(f"Unsupported input_data type: {type(input_data)}. Expected dict or pd.DataFrame.")

    # Apply scaling if a scaler is provided
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X

    # Generate predictions
    predictions = model.predict(X_scaled)

    # Generate probabilities if supported by the model
    probabilities = None
    if hasattr(model, "predict_proba"):
        try:
            probabilities = model.predict_proba(X_scaled)
        except Exception as exc:
            log.warning(f"Could not compute predict_proba: {exc}")

    log.info(f"Generated predictions for {len(X)} row(s). Scaler applied: {scaler is not None}")

    return {
        "predictions": predictions,
        "probabilities": probabilities,
        "is_batch": not is_dict and len(X) > 1,
        "count": len(X),
    }


class GenericPredictionService:
    """
    Object-oriented wrapper around predict().
    """

    def __init__(self, model: Any, scaler: Optional[Any] = None, feature_names: Optional[List[str]] = None):
        self.model = model
        self.scaler = scaler
        self.feature_names = feature_names

    def predict(self, input_data: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
        return predict(self.model, self.scaler, input_data, self.feature_names)
