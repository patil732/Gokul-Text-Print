"""
app/ml/inventory/inventory_pipeline.py
---------------------------------------
End-to-end inventory reorder prediction pipeline orchestrator.
"""

from typing import Dict, Any
from app.ml.inventory.inventory_feature_engineering import load_and_preprocess_inventory_data
from app.ml.inventory.inventory_training import train_inventory_model
from app.ml.inventory.inventory_prediction import predict_inventory
from app.ml.common.logger import get_ml_logger

log = get_ml_logger("inventory_pipeline")


def run_inventory_pipeline(data_path: str = None, force_reprocess: bool = True) -> Dict[str, Any]:
    """
    Run the end-to-end inventory feature engineering, model training, and validation pipeline.
    """
    log.info("Executing full Inventory ML pipeline ...")

    # 1. Feature Engineering
    df_features = load_and_preprocess_inventory_data(data_path)

    # 2. Training & Registration
    train_summary = train_inventory_model(data_path=data_path)

    log.info("Inventory ML pipeline execution completed successfully.")
    return train_summary
