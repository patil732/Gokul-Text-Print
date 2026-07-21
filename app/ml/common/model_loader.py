"""
app/ml/common/model_loader.py
------------------------------
Load & save sklearn/ML models + scalers, and build model/scaler instances
dynamically from config settings.
"""

import os
import joblib
import yaml
from typing import Tuple, Optional, Any, Dict

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

from app.ml.common.logger import get_ml_logger

log = get_ml_logger("model_loader")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "model_config.yaml")


def load_config(config_path: str = _CONFIG_PATH) -> Dict[str, Any]:
    """
    Load pipeline model configuration from YAML file.
    """
    if not os.path.exists(config_path):
        log.warning(f"Config file not found at {config_path}. Using empty configuration.")
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def create_model_from_config(pipeline_name: str, config_path: str = _CONFIG_PATH) -> Any:
    """
    Instantiate an untrained model (RandomForest, XGBoost, or LightGBM) based on config/model_config.yaml.
    """
    cfg = load_config(config_path).get(pipeline_name, {})
    algo = cfg.get("algorithm", "random_forest").lower()
    params = cfg.get("hyperparameters", {})

    log.info(f"Instantiating model algorithm '{algo}' for pipeline '{pipeline_name}' with params: {params}")

    if algo == "random_forest":
        return RandomForestClassifier(**params)

    elif algo == "xgboost":
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(**params)
        except ImportError:
            log.warning("XGBoost not installed. Falling back to RandomForestClassifier.")
            # Remove non-RF parameters if any
            rf_params = {k: v for k, v in params.items() if k in ["n_estimators", "max_depth", "random_state", "n_jobs", "class_weight"]}
            return RandomForestClassifier(**rf_params)

    elif algo == "lightgbm":
        try:
            from lightgbm import LGBMClassifier
            return LGBMClassifier(**params)
        except ImportError:
            log.warning("LightGBM not installed. Falling back to RandomForestClassifier.")
            rf_params = {k: v for k, v in params.items() if k in ["n_estimators", "max_depth", "random_state", "n_jobs", "class_weight"]}
            return RandomForestClassifier(**rf_params)

    else:
        log.warning(f"Unknown algorithm '{algo}'. Defaulting to RandomForestClassifier.")
        return RandomForestClassifier(**params)


def create_scaler_from_config(pipeline_name: str, config_path: str = _CONFIG_PATH) -> Optional[Any]:
    """
    Instantiate a scaler (StandardScaler, MinMaxScaler, or RobustScaler) based on config.
    """
    cfg = load_config(config_path).get(pipeline_name, {}).get("scaler", {})
    if not cfg.get("enabled", False):
        return None

    scaler_type = cfg.get("type", "standard").lower()
    if scaler_type == "minmax":
        return MinMaxScaler()
    elif scaler_type == "robust":
        return RobustScaler()
    else:
        return StandardScaler()


def save_model(model: Any, filepath: str) -> None:
    """Save a fitted model to filepath."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(model, filepath)
    log.info(f"Model saved -> {filepath}")


def load_model(filepath: str) -> Any:
    """Load a fitted model from filepath."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found at {filepath}")
    model = joblib.load(filepath)
    log.info(f"Model loaded <- {filepath}")
    return model


def save_scaler(scaler: Any, filepath: str) -> None:
    """Save a fitted scaler to filepath."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(scaler, filepath)
    log.info(f"Scaler saved -> {filepath}")


def load_scaler(filepath: str) -> Optional[Any]:
    """Load a fitted scaler from filepath."""
    if not os.path.exists(filepath):
        log.warning(f"Scaler file not found at {filepath}")
        return None
    scaler = joblib.load(filepath)
    log.info(f"Scaler loaded <- {filepath}")
    return scaler


def save_model_and_scaler(model: Any, scaler: Optional[Any], target_dir: str, model_name: str = "model.pkl", scaler_name: str = "scaler.pkl") -> Tuple[str, Optional[str]]:
    """
    Save both model and optional scaler inside target_dir.
    """
    os.makedirs(target_dir, exist_ok=True)
    model_path = os.path.join(target_dir, model_name)
    save_model(model, model_path)

    scaler_path = None
    if scaler is not None:
        scaler_path = os.path.join(target_dir, scaler_name)
        save_scaler(scaler, scaler_path)

    return model_path, scaler_path


def load_model_and_scaler(target_dir: str, model_name: str = "model.pkl", scaler_name: str = "scaler.pkl") -> Tuple[Any, Optional[Any]]:
    """
    Load model and optional scaler from target_dir.
    """
    model_path = os.path.join(target_dir, model_name)
    scaler_path = os.path.join(target_dir, scaler_name)

    model = load_model(model_path)
    scaler = load_scaler(scaler_path) if os.path.exists(scaler_path) else None

    return model, scaler
