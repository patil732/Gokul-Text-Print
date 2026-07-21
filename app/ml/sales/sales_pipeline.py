"""
app/ml/sales/sales_pipeline.py
-------------------------------
End-to-end sales forecasting pipeline orchestrator.
"""

from app.sales.data_loader import load_raw_sales
from app.sales.preprocess import run_and_save
from app.sales.train import train


def run_sales_pipeline(force_reprocess: bool = False):
    """
    Run the end-to-end sales data loading, feature engineering, and training pipeline.
    """
    if force_reprocess:
        raw_df = load_raw_sales()
        run_and_save(raw_df)
    train(force_reprocess=force_reprocess)
