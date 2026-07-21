"""
app/ml/common/prediction_service.py
------------------------------------
Base prediction service interface for model inference.
"""

import pandas as pd


class BasePredictionService:
    """
    Abstract/base prediction service for ML domain models.
    """

    def predict_row(self, row_df: pd.DataFrame) -> dict:
        raise NotImplementedError

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError
