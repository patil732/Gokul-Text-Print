"""
app/ml/common/feature_validator.py
-----------------------------------
Feature schema validation helper for ML input data.
"""

from typing import List
import pandas as pd


def validate_feature_schema(df: pd.DataFrame, expected_features: List[str]) -> pd.DataFrame:
    """
    Ensure all expected features are present in the DataFrame.
    Fills missing features with 0.0.
    """
    df = df.copy()
    missing = set(expected_features) - set(df.columns)
    for col in missing:
        df[col] = 0.0
    return df[expected_features]
