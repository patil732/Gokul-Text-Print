"""
tests/test_sales_explain.py
----------------------------
Sprint 2 — Sales Model Explainability & SHAP Integration Tests

Coverage
--------
1. Feature importance ranking (sorted descending by importance score).
2. SHAP summary plot saved to static/sales_explanations/shap_summary.png.
3. SHAP waterfall plot saved to static/sales_explanations/shap_waterfall.png.
4. Feature importance plot saved to static/sales_explanations/feature_importance.png.
5. Per-prediction explanation: explain_prediction() returns top 3 features with values & SHAP scores.
6. API Integration: POST /api/sales/forecast includes explanation payload (top 3 features).
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.sales.explain import (
    compute_shap_values,
    explain_prediction,
    generate_and_save_plots,
    generate_sales_explanations,
    get_explainer,
    get_feature_importance,
    STATIC_EXPLANATIONS_DIR,
)
from app.ml.sales.forecast import generate_forecast, _get_engine

# ── Load Flask app factory ───────────────────────────────────────────────── #
_SPEC    = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app

_FEATURE_COLS = [
    "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
    "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
    "momentum", "trend", "stock_ratio",
]


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def loaded_engine():
    """Ensure process-level forecast engine model is loaded."""
    engine = _get_engine()
    engine.load()
    return engine


@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================================ #
# 1. Explainability core function tests
# ============================================================================ #

class TestExplainabilityFunctions:
    """Unit tests for compute_shap_values, get_feature_importance, explain_prediction."""

    def test_get_explainer_returns_valid_object(self, loaded_engine):
        explainer = get_explainer(loaded_engine.model)
        assert explainer is not None

    def test_compute_shap_values_matrix_shape(self, loaded_engine):
        feature_cols = loaded_engine.feature_cols
        X = np.random.default_rng(42).uniform(10, 1000, (10, len(feature_cols)))
        shap_mat = compute_shap_values(loaded_engine.model, X, feature_names=feature_cols)
        assert isinstance(shap_mat, np.ndarray)
        assert shap_mat.shape == (10, len(feature_cols))

    def test_get_feature_importance_ranking_structure(self, loaded_engine):
        feature_cols = loaded_engine.feature_cols
        X = np.random.default_rng(42).uniform(10, 1000, (15, len(feature_cols)))
        rankings = get_feature_importance(loaded_engine.model, X, feature_names=feature_cols)

        assert isinstance(rankings, list)
        assert len(rankings) == len(feature_cols)

        for item in rankings:
            assert "feature" in item
            assert "importance" in item
            assert isinstance(item["feature"], str)
            assert isinstance(item["importance"], float)

    def test_get_feature_importance_is_sorted_descending(self, loaded_engine):
        feature_cols = loaded_engine.feature_cols
        X = np.random.default_rng(42).uniform(10, 1000, (15, len(feature_cols)))
        rankings = get_feature_importance(loaded_engine.model, X, feature_names=feature_cols)

        scores = [item["importance"] for item in rankings]
        assert scores == sorted(scores, reverse=True), "Feature importances must be sorted descending."

    def test_explain_prediction_returns_top_3_features(self, loaded_engine):
        feature_cols = loaded_engine.feature_cols
        sample_dict = {f: 100.0 for f in feature_cols}
        exp = explain_prediction(
            model=loaded_engine.model,
            scaler=loaded_engine.scaler,
            input_data=sample_dict,
            feature_names=feature_cols,
            top_n=3,
        )

        assert isinstance(exp, list)
        assert len(exp) == 3

        for item in exp:
            assert "feature" in item
            assert "value" in item
            assert "shap_value" in item
            assert isinstance(item["feature"], str)
            assert isinstance(item["value"], float)
            assert isinstance(item["shap_value"], float)

    def test_explain_prediction_sorted_by_abs_shap_value(self, loaded_engine):
        feature_cols = loaded_engine.feature_cols
        sample_dict = {f: 100.0 for f in feature_cols}
        exp = explain_prediction(
            model=loaded_engine.model,
            scaler=loaded_engine.scaler,
            input_data=sample_dict,
            feature_names=feature_cols,
            top_n=3,
        )

        abs_shaps = [abs(item["shap_value"]) for item in exp]
        assert abs_shaps == sorted(abs_shaps, reverse=True), (
            "Top feature explanations must be ordered by absolute SHAP contribution."
        )


# ============================================================================ #
# 2. Plot generation tests (static/sales_explanations/)
# ============================================================================ #

class TestPlotGeneration:
    """Test generating and saving SHAP summary, waterfall, and feature importance plots."""

    def test_plots_saved_to_static_explanations_folder(self, loaded_engine, tmp_path):
        out_dir = str(tmp_path / "sales_explanations")
        feat_cols = getattr(loaded_engine.scaler, "feature_names_in_", None)
        if feat_cols is None:
            feat_cols = getattr(loaded_engine.model, "feature_names_in_", None)
        if feat_cols is None:
            feat_cols = getattr(loaded_engine, "feature_names", None)
        if feat_cols is None:
            feat_cols = _FEATURE_COLS

        if hasattr(feat_cols, "tolist"):
            feat_cols = feat_cols.tolist()
        else:
            feat_cols = list(feat_cols)

        X = np.random.default_rng(99).uniform(100, 5000, (20, len(feat_cols)))
        df_sample = pd.DataFrame(X, columns=feat_cols)

        plots = generate_and_save_plots(
            model=loaded_engine.model,
            scaler=loaded_engine.scaler,
            X_sample=df_sample,
            feature_names=feat_cols,
            output_dir=out_dir,
        )


        assert "summary_plot" in plots
        assert "waterfall_plot" in plots
        assert "importance_plot" in plots

        for name, path in plots.items():
            assert os.path.exists(path), f"Plot image '{name}' missing at '{path}'."
            assert os.path.getsize(path) > 1000, f"Plot image '{name}' is suspiciously small (< 1KB)."

    def test_generate_sales_explanations_workflow(self):
        result = generate_sales_explanations(output_dir=STATIC_EXPLANATIONS_DIR)
        assert result["status"] == "success"
        assert "version" in result
        assert "feature_importance" in result
        assert "plots" in result

        summary_file = os.path.join(STATIC_EXPLANATIONS_DIR, "shap_summary.png")
        waterfall_file = os.path.join(STATIC_EXPLANATIONS_DIR, "shap_waterfall.png")
        importance_file = os.path.join(STATIC_EXPLANATIONS_DIR, "feature_importance.png")

        assert os.path.exists(summary_file)
        assert os.path.exists(waterfall_file)
        assert os.path.exists(importance_file)


# ============================================================================ #
# 3. Forecast endpoint explanation integration tests
# ============================================================================ #

class TestForecastExplanationIntegration:
    """Ensure generate_forecast and POST /api/sales/forecast include explanation payload."""

    @pytest.mark.parametrize("period", ["7_days", "30_days", "90_days"])
    def test_generate_forecast_contains_explanation(self, period):
        res = generate_forecast(period)
        assert "explanation" in res
        exp = res["explanation"]

        assert isinstance(exp, list)
        assert len(exp) == 3

        for item in exp:
            assert "feature" in item
            assert "value" in item
            assert "shap_value" in item

    @pytest.mark.parametrize("period", ["7_days", "30_days", "90_days"])
    def test_forecast_api_endpoint_returns_explanation_payload(self, flask_client, period):
        resp = flask_client.post(
            "/api/sales/forecast",
            data=json.dumps({"forecast_period": period}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        body = resp.get_json()

        assert body["status"] == "success"
        assert "explanation" in body
        exp = body["explanation"]

        assert isinstance(exp, list)
        assert len(exp) == 3

        for item in exp:
            assert "feature" in item
            assert "value" in item
            assert "shap_value" in item
            assert isinstance(item["feature"], str)
            assert isinstance(item["value"], (int, float))
            assert isinstance(item["shap_value"], (int, float))


# ============================================================================ #
# CLI runner
# ============================================================================ #

if __name__ == "__main__":
    import subprocess, sys as _sys
    ret = subprocess.run(
        [_sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    _sys.exit(ret.returncode)
