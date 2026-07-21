"""
app/ml/inventory/inventory_prediction.py
-----------------------------------------
Inventory inference module.
"""

from app.inventory.predict import predict_row, predict_batch

__all__ = ["predict_row", "predict_batch"]
