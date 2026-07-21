"""
app/ml/common/metrics_service.py
---------------------------------
Evaluation and metrics computation service for ML models.
Supports both classification and regression model evaluation.
"""

from typing import Dict, Any, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
)

from app.ml.common.logger import get_ml_logger

log = get_ml_logger("metrics_service")


def compute_classification_metrics(y_true, y_pred, y_prob: Optional[Any] = None) -> Dict[str, Any]:
    """
    Compute standard classification evaluation metrics.

    Returns
    -------
    dict
        accuracy, precision, recall, f1_score, roc_auc (if y_prob provided), confusion_matrix
    """
    acc  = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec  = float(recall_score(y_true, y_pred, zero_division=0))
    f1   = float(f1_score(y_true, y_pred, zero_division=0))
    cm   = confusion_matrix(y_true, y_pred).tolist()

    metrics: Dict[str, Any] = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": cm,
    }

    if y_prob is not None:
        try:
            # Check if binary or multi-class proba
            if isinstance(y_prob, (list, np.ndarray)) and np.ndim(y_prob) == 2 and y_prob.shape[1] == 2:
                auc = float(roc_auc_score(y_true, y_prob[:, 1]))
            else:
                auc = float(roc_auc_score(y_true, y_prob))
            metrics["roc_auc"] = round(auc, 4)
        except Exception as exc:
            log.warning(f"Could not compute ROC-AUC score: {exc}")

    log.info(f"Classification Metrics -> Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}")
    return metrics


def compute_regression_metrics(y_true, y_pred) -> Dict[str, float]:
    """
    Compute standard regression evaluation metrics.

    Returns
    -------
    dict
        mse, rmse, mae, r2_score, mape
    """
    mse  = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))

    # Calculate Mean Absolute Percentage Error (MAPE) safely
    y_true_arr = np.array(y_true, dtype=float)
    y_pred_arr = np.array(y_pred, dtype=float)
    non_zero_mask = y_true_arr != 0
    if np.any(non_zero_mask):
        mape = float(np.mean(np.abs((y_true_arr[non_zero_mask] - y_pred_arr[non_zero_mask]) / y_true_arr[non_zero_mask])) * 100)
    else:
        mape = 0.0

    metrics = {
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2_score": round(r2, 4),
        "mape": round(mape, 4),
    }

    log.info(f"Regression Metrics -> RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")
    return metrics
