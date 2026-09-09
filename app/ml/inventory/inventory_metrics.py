"""
app/ml/inventory/inventory_metrics.py
-------------------------------------
Inventory metrics evaluation module.
Uses app/ml/common/metrics_service.py to compute classification metrics.
"""

from typing import Dict, Any, Optional
from app.ml.common.metrics_service import compute_classification_metrics
from app.ml.common.logger import get_ml_logger

log = get_ml_logger("inventory_metrics")


def evaluate_inventory_model(y_true, y_pred, y_prob: Optional[Any] = None) -> Dict[str, Any]:
    """
    Compute and return full evaluation metrics for the inventory reorder model.
    """
    metrics = compute_classification_metrics(y_true, y_pred, y_prob)
    log.info(f"Inventory model evaluation metrics: {metrics}")
    return metrics
