"""
app/ml/sales/sales_metrics.py
------------------------------
Sales metrics evaluation module.
Uses app/ml/common/metrics_service.py to compute classification and regression metrics.
"""

from typing import Dict, Any, Optional
from app.ml.common.metrics_service import (
    compute_classification_metrics,
    compute_regression_metrics,
)
from app.ml.common.logger import get_ml_logger

log = get_ml_logger("sales_metrics")


def evaluate_sales_model(y_true, y_pred, y_prob: Optional[Any] = None) -> Dict[str, Any]:
    """
    Compute and return full evaluation metrics for the sales model.
    """
    metrics = compute_classification_metrics(y_true, y_pred, y_prob)
    log.info(f"Sales model evaluation metrics: {metrics}")
    return metrics
