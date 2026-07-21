"""
app/ml/common/metrics_service.py
---------------------------------
Evaluation and metrics computation service for ML models.
"""

from typing import Dict, Any
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def compute_classification_metrics(y_true, y_pred) -> Dict[str, float]:
    """
    Compute standard classification evaluation metrics.
    """
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
    }
