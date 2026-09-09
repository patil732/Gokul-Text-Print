"""
app/ml/sales/sales_pipeline.py
-------------------------------
End-to-end sales forecasting pipeline orchestrator.
"""

from typing import Dict, Any, Union
import pandas as pd

from app.ml.sales.sales_feature_engineering import load_and_preprocess_sales_data
from app.ml.sales.sales_training import train_sales_model
from app.ml.sales.sales_prediction import predict_sales
from app.ml.common.logger import get_ml_logger

log = get_ml_logger("sales_pipeline")


def run_sales_pipeline(data_path: str = None, force_reprocess: bool = True) -> Dict[str, Any]:
    """
    Run the end-to-end sales feature engineering, model training, and validation pipeline.
    """
    log.info("Executing full Sales ML pipeline ...")

    # 1. Feature Engineering
    df_features = load_and_preprocess_sales_data(data_path)

    # 2. Training & Registration
    train_summary = train_sales_model(data_path=data_path)

    log.info("Sales ML pipeline execution completed successfully.")
    return train_summary
