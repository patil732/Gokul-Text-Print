"""
app/ml/sales/sales_prediction.py
---------------------------------
Sales inference module.
"""

from app.sales.predict import predict_row, predict_batch

__all__ = ["predict_row", "predict_batch"]
