"""
app/ml/inventory/inventory_pipeline.py
---------------------------------------
End-to-end inventory reorder prediction pipeline orchestrator.
"""

from app.inventory.data_loader import load_raw_stock, load_raw_production
from app.inventory.preprocess import run_and_save
from app.inventory.train import train


def run_inventory_pipeline(force_reprocess: bool = False):
    """
    Run the end-to-end inventory data loading, feature engineering, and training pipeline.
    """
    if force_reprocess:
        stock_df = load_raw_stock()
        prod_df  = load_raw_production()
        run_and_save(stock_df, prod_df)
    train(force_reprocess=force_reprocess)
