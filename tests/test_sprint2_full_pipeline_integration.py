"""
tests/test_sprint2_full_pipeline_integration.py
-------------------------------------------------
End-to-End Integration Test for Sprint 2 — Sales Intelligence Engine

Execution Flow
--------------
1. Raw Data Extraction & Cleaning  → dataset.py: build_sales_dataset()
2. Feature Engineering Extensions  → sales_feature_engineering.py: load_and_prepare_sales_data()
3. Model Training & Selection      → evaluate.py: train_and_evaluate_sales_pipeline()
4. Forecasting Engine Inference    → forecast.py: generate_forecast() & POST /api/sales/forecast
5. Business Recommendation Engine  → recommendation.py: get_recommendation() & GET /api/sales/recommendation
6. Dashboard Analytics Endpoint    → routes.py: GET /api/sales/dashboard_data
7. Prediction History Endpoint     → routes.py: GET /api/sales/history

All stages assert zero errors, valid schemas, and expected state progression.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.sales.dataset import build_sales_dataset, load_sales_dataset
from app.ml.sales.sales_feature_engineering import compute_sales_features
from app.ml.sales.evaluate import run_evaluation_pipeline
from app.ml.sales.forecast import generate_forecast
from app.ml.sales.recommendation import get_recommendation

# ── Load Flask app factory ───────────────────────────────────────────────── #
_SPEC    = importlib.util.spec_from_file_location(
    "app_entry",
    os.path.join(os.path.dirname(__file__), "..", "app.py"),
)
_APP_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APP_MOD)
create_app = _APP_MOD.create_app


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def flask_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Authenticate session
        with client.session_transaction() as sess:
            sess["user"] = "ceo_integration_user"
            sess["role"] = "ceo"
        yield client


# ============================================================================ #
# Full End-to-End Pipeline Integration Test
# ============================================================================ #

class TestFullSalesPipelineIntegration:
    """Executes the complete Sprint 2 pipeline from raw data to API endpoints."""

    def test_stage_1_raw_data_cleaning_and_dataset_building(self):
        """Stage 1: Raw ERP data extraction, cleaning, and dataset creation."""
        output_csv = os.path.join(
            os.path.dirname(__file__), "..", "data", "sales_dataset.csv"
        )
        res = build_sales_dataset(output_path=output_csv)

        assert res["status"] == "success"
        assert os.path.exists(output_csv)

        df_cleaned = load_sales_dataset(output_csv)
        assert df_cleaned is not None
        assert not df_cleaned.empty
        assert df_cleaned.duplicated().sum() == 0
        assert df_cleaned[["date", "product", "revenue"]].isnull().sum().sum() == 0

        # Assert cleaned dataset columns present
        for col in ["date", "product", "revenue", "quantity", "revenue_norm", "year", "month", "quarter"]:
            assert col in df_cleaned.columns

    def test_stage_2_feature_engineering_extension(self):
        """Stage 2: Feature engineering pipeline preparing feature-rich dataset."""
        df_raw = load_sales_dataset()
        df_features = compute_sales_features(df_raw)

        assert df_features is not None
        assert not df_features.empty
        assert df_features.isnull().sum().sum() == 0

        required_features = [
            "daily_sales", "weekly_sales", "monthly_sales", "growth_rate",
            "rolling_avg", "moving_avg_7d", "revenue_trend", "sales_volatility",
            "sales_lag_1", "sales_lag_2", "sales_lag_3", "momentum", "stock_ratio",
            "product_popularity", "seasonal_index", "sales_frequency",
        ]
        for feat in required_features:
            assert feat in df_features.columns, f"Missing feature: {feat}"

    def test_stage_3_multi_model_training_and_selection(self):
        """Stage 3: Training 4 candidates, selecting best model, saving artifacts."""
        df_raw = load_sales_dataset()
        df_features = compute_sales_features(df_raw)

        feature_cols = [
            "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
            "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
            "momentum", "trend", "stock_ratio", "product_popularity",
            "seasonal_index", "sales_frequency",
        ]
        feature_cols = [c for c in feature_cols if c in df_features.columns]
        target_col = "target_decision"

        models_dir = os.path.join(os.path.dirname(__file__), "..", "models", "sales")

        results = run_evaluation_pipeline(
            df=df_features,
            feature_cols=feature_cols,
            target_col=target_col,
            models_dir=models_dir,
            version="20260722_integration",
        )

        assert results["status"] == "success"
        assert "best_model_name" in results
        assert "best_metrics" in results
        assert os.path.exists(results["model_path"])
        assert os.path.exists(results["scaler_path"])
        assert os.path.exists(results["metrics_path"])

        # Reload engine so forecast uses the updated model and scaler
        from app.ml.sales.forecast import _get_engine
        _get_engine().reload()

    def test_stage_4_forecasting_engine_and_api(self, flask_client):
        """Stage 4: Forecast engine inference and API endpoint call."""
        # 1. Direct Python function call
        forecast_res = generate_forecast(forecast_period="30_days")
        assert forecast_res["forecast_period"] == "30_days"
        assert forecast_res["predicted_sales"] > 0.0
        assert "explanation" in forecast_res
        assert len(forecast_res["explanation"]) == 3

        # 2. HTTP POST API call
        resp = flask_client.post(
            "/api/sales/forecast",
            json={"forecast_period": "30_days"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["forecast_period"] == "30_days"
        assert body["predicted_sales"] > 0.0
        assert body["elapsed_ms"] < 1000.0, "Forecast response time must be < 1s."

    def test_stage_5_recommendation_rules_engine_and_api(self, flask_client):
        """Stage 5: Recommendation rules engine and API endpoint call."""
        # 1. Direct Python call
        rec_res = get_recommendation(forecast_period="30_days")
        assert rec_res["decision"] in [
            "Increase Production",
            "Reduce Inventory",
            "Maintain Current Production",
        ]
        assert len(rec_res["reason"]) > 0
        assert 0.0 <= rec_res["confidence"] <= 1.0

        # 2. HTTP GET API call
        resp = flask_client.get("/api/sales/recommendation?forecast_period=30_days")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["decision"] == rec_res["decision"]
        assert "reason" in body
        assert "confidence" in body

    def test_stage_6_dashboard_data_analytics_api(self, flask_client):
        """Stage 6: GET /api/sales/dashboard_data endpoint serving dashboard visual series."""
        resp = flask_client.get("/api/sales/dashboard_data")
        assert resp.status_code == 200

        body = resp.get_json()
        assert body["status"] == "success"
        assert "kpis" in body
        assert "sales_trend" in body
        assert "revenue_trend" in body
        assert "product_performance" in body
        assert "monthly_comparison" in body

        # Assert visual series are populated
        assert len(body["sales_trend"]["dates"]) > 0
        assert len(body["revenue_trend"]["revenue"]) > 0
        assert len(body["product_performance"]["products"]) > 0
        assert len(body["monthly_comparison"]["months"]) > 0

    def test_stage_7_prediction_history_api(self, flask_client):
        """Stage 7: GET /api/sales/history endpoint retrieving stored predictions."""
        resp = flask_client.get("/api/sales/history?page=1&limit=10")
        assert resp.status_code == 200

        body = resp.get_json()
        assert body["status"] == "success"
        assert body["total_records"] > 0
        assert len(body["data"]) > 0

        latest = body["data"][0]
        assert "prediction_id" in latest
        assert "forecast_period" in latest
        assert "forecast_value" in latest
        assert "recommendation" in latest
        assert "confidence" in latest
        assert "model_version" in latest


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
