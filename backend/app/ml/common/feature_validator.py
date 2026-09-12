"""
app/ml/common/feature_validator.py
-----------------------------------
Feature schema validation helper for ML input data prior to inference.
"""

from typing import List, Dict, Any, Tuple, Union, Optional
import pandas as pd
import numpy as np

from app.ml.common.logger import get_ml_logger

log = get_ml_logger("feature_validator")


class FeatureValidationError(ValueError):
    """Raised when critical feature validation fails."""
    pass


def validate_feature_dict(
    input_data: Dict[str, Any],
    expected_features: List[str],
    defaults: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Validate and sanitize a single feature dictionary against expected feature names.

    Parameters
    ----------
    input_data        : dict of feature key-value pairs
    expected_features : list of required/expected feature names
    defaults          : dict of default values for missing keys (defaults to 0.0)

    Returns
    -------
    dict
        Cleaned dict with all expected_features present as numeric floats.
    """
    defaults = defaults or {}
    sanitized: Dict[str, float] = {}

    missing_cols = []
    for feat in expected_features:
        if feat in input_data and input_data[feat] is not None:
            try:
                val = float(input_data[feat])
                if np.isnan(val) or np.isinf(val):
                    val = defaults.get(feat, 0.0)
                sanitized[feat] = val
            except (ValueError, TypeError):
                sanitized[feat] = defaults.get(feat, 0.0)
        else:
            missing_cols.append(feat)
            sanitized[feat] = defaults.get(feat, 0.0)

    if missing_cols:
        log.warning(f"Missing feature keys filled with defaults (0.0): {missing_cols}")

    return sanitized


def validate_feature_dataframe(
    df: pd.DataFrame,
    expected_features: List[str],
    strict: bool = False,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate a DataFrame against an expected feature schema.

    Parameters
    ----------
    df                : input DataFrame
    expected_features : list of feature column names
    strict            : if True, raises FeatureValidationError on missing columns

    Returns
    -------
    (pd.DataFrame, list[str])
        Sanitized DataFrame containing exactly expected_features in order, and list of warnings.
    """
    warnings: List[str] = []

    if df.empty:
        msg = "Input DataFrame is empty."
        if strict:
            raise FeatureValidationError(msg)
        warnings.append(msg)
        log.warning(msg)
        return pd.DataFrame(columns=expected_features), warnings

    df_out = df.copy()
    missing_cols = [f for f in expected_features if f not in df_out.columns]

    if missing_cols:
        msg = f"Missing feature columns filled with 0.0: {missing_cols}"
        if strict:
            raise FeatureValidationError(msg)
        warnings.append(msg)
        log.warning(msg)
        for col in missing_cols:
            df_out[col] = 0.0

    # Ensure numeric types and replace NaNs / Inf
    for col in expected_features:
        df_out[col] = pd.to_numeric(df_out[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df_out[expected_features], warnings
