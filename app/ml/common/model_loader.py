"""
app/ml/common/model_loader.py
------------------------------
Common model loading and serialization utility for multi-model architecture.
"""

import os
import joblib
from utils.logger import logger


def load_model(model_path: str):
    """
    Load a serialized model artefact from *model_path*.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"[model_loader] Model file not found: {model_path}")
    model = joblib.load(model_path)
    logger.info(f"[model_loader] Model loaded from {model_path}")
    return model


def save_model(model, model_path: str) -> None:
    """
    Persist a fitted model to *model_path*.
    """
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"[model_loader] Model saved to {model_path}")
