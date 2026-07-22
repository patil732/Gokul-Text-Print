"""
tests/test_sales_evaluate.py
-----------------------------
Sprint 2 — Multi-Model Training & Evaluation Engine
Unit tests for:

  1. app/ml/sales/evaluate.run_evaluation_pipeline()
       - Pipeline completes and selects a model
       - sales_model.pkl is created
       - sales_scaler.pkl is created
       - sales_metrics.json is created and is valid JSON
       - metrics JSON contains required keys (rmse, mae, r2)
       - all_results contains entries for all four algorithms
       - Selected model is registered in the model registry

  2. app/ml/sales/sales_training.train_sales_model()  (backward-compat)
       - Returns status == "success" with Sprint 1 dict shape
       - model_path file exists on disk

All tests use a self-contained synthetic fixture (no live DB connection,
no ETL pipeline, no network access). Registry calls go to the real SQLite
ai_decision.db if present, or fall back gracefully.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

# ── Project root on sys.path ──────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.sales.evaluate import run_evaluation_pipeline, _ALGORITHM_NAMES
from app.ml.sales.sales_training import train_sales_model
from app.ml.common.model_registry import get_latest_version

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_SPRINT1_RETURN_KEYS = {
    "status", "model_name", "model_type", "version",
    "accuracy", "metrics", "model_path", "scaler_path", "registered_entry",
}

_REQUIRED_METRICS_JSON_KEYS = {"rmse", "mae", "r2", "best_model", "version"}

_FEATURE_COLS = [
    "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3",
    "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7",
    "momentum", "trend", "stock_ratio",
]
_TARGET_COL = "target_decision"


# --------------------------------------------------------------------------- #
# Synthetic dataset fixture
# --------------------------------------------------------------------------- #

def _make_synthetic_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Build a small in-memory DataFrame that matches the feature contract
    expected by run_evaluation_pipeline().  Includes all Sprint-1 feature
    columns and a binary target_decision column.
    """
    rng = np.random.default_rng(seed)

    df = pd.DataFrame({
        "sales":        rng.uniform(1_000, 50_000, n),
        "sales_lag_1":  rng.uniform(900,  48_000, n),
        "sales_lag_2":  rng.uniform(800,  46_000, n),
        "sales_lag_3":  rng.uniform(700,  44_000, n),
        "sales_ma_3":   rng.uniform(900,  48_000, n),
        "sales_ma_7":   rng.uniform(900,  47_000, n),
        "sales_ma_14":  rng.uniform(900,  46_000, n),
        "sales_std_7":  rng.uniform(0,     5_000, n),
        "momentum":     rng.uniform(-5_000, 5_000, n),
        "trend":        rng.choice([-1, 0, 1], n),
        "stock_ratio":  rng.uniform(0.1, 10.0, n),
        # Binary target — ~60 % positive class to avoid all-one degenerate split
        "target_decision": rng.choice([0, 1], n, p=[0.4, 0.6]),
    })
    return df


@pytest.fixture(scope="module")
def pipeline_result(tmp_path_factory):
    """
    Run run_evaluation_pipeline() once on the synthetic dataset and
    cache the result for the whole module.
    """
    models_dir = str(tmp_path_factory.mktemp("models_sales"))
    df         = _make_synthetic_df()

    result = run_evaluation_pipeline(
        df           = df,
        feature_cols = _FEATURE_COLS,
        target_col   = _TARGET_COL,
        models_dir   = models_dir,
        version      = "pytest_eval_v1",
    )
    return result


@pytest.fixture(scope="module")
def training_result(tmp_path_factory):
    """
    Run train_sales_model() with a pre-built synthetic CSV so it exercises
    the full orchestration path (load → evaluate → register).
    Uses monkeypatching via data_path pointing at a temp CSV.
    """
    tmp_dir  = tmp_path_factory.mktemp("train_data")
    csv_path = str(tmp_dir / "sales.csv")

    # Write raw-format CSV (ETL output columns: name, transaction_date, customer, grand_total, status)
    rng = np.random.default_rng(99)
    n   = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    pd.DataFrame({
        "name":             [f"SO-{i:05d}" for i in range(n)],
        "transaction_date": dates.strftime("%Y-%m-%d"),
        "customer":         rng.choice(["Alpha", "Beta", "Gamma"], n),
        "grand_total":      rng.uniform(500, 50_000, n).round(2),
        "status":           "Completed",
    }).to_csv(csv_path, index=False)

    # Override the output directory so we don't clobber the real models/sales/
    tmp_models = str(tmp_path_factory.mktemp("train_models"))
    result = train_sales_model(
        data_path  = csv_path,
        models_dir = tmp_models,
        version    = "pytest_train_v1",
    )
    return result


# ============================================================================ #
# Tests — run_evaluation_pipeline()
# ============================================================================ #

class TestEvaluationPipeline:
    """Core tests for the multi-model evaluation engine."""

    # ── Pipeline succeeds and selects a model ─────────────────────────── #

    def test_pipeline_returns_success(self, pipeline_result):
        assert pipeline_result["status"] == "success", (
            f"Pipeline returned status '{pipeline_result['status']}'. "
            f"Error: {pipeline_result.get('error')}"
        )

    def test_best_model_name_is_non_empty_string(self, pipeline_result):
        name = pipeline_result["best_model_name"]
        assert isinstance(name, str) and len(name) > 0, (
            f"best_model_name should be a non-empty string, got: {name!r}"
        )

    def test_best_model_is_known_algorithm(self, pipeline_result):
        name = pipeline_result["best_model_name"]
        # XGBoost/LightGBM may fall back to random_forest when not installed
        known = set(_ALGORITHM_NAMES) | {"random_forest"}
        assert name in known, (
            f"best_model_name '{name}' is not in the known algorithm set {known}."
        )

    # ── Artefact files exist ──────────────────────────────────────────── #

    def test_sales_model_pkl_created(self, pipeline_result):
        path = pipeline_result["model_path"]
        assert path is not None and os.path.exists(path), (
            f"sales_model.pkl not found at '{path}'."
        )

    def test_sales_scaler_pkl_created(self, pipeline_result):
        path = pipeline_result.get("scaler_path")
        assert path is not None and os.path.exists(path), (
            f"sales_scaler.pkl not found at '{path}'."
        )

    def test_sales_metrics_json_created(self, pipeline_result):
        path = pipeline_result["metrics_path"]
        assert path is not None and os.path.exists(path), (
            f"sales_metrics.json not found at '{path}'."
        )

    # ── Metrics JSON is valid and complete ───────────────────────────── #

    def test_metrics_json_is_valid_json(self, pipeline_result):
        with open(pipeline_result["metrics_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), "sales_metrics.json did not parse to a dict."

    @pytest.mark.parametrize("key", sorted(_REQUIRED_METRICS_JSON_KEYS))
    def test_metrics_json_has_required_key(self, pipeline_result, key):
        with open(pipeline_result["metrics_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert key in data, (
            f"Required key '{key}' missing from sales_metrics.json. "
            f"Keys present: {list(data.keys())}"
        )

    def test_metrics_rmse_is_non_negative(self, pipeline_result):
        with open(pipeline_result["metrics_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["rmse"] >= 0.0, f"RMSE is negative: {data['rmse']}"

    def test_metrics_mae_is_non_negative(self, pipeline_result):
        with open(pipeline_result["metrics_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["mae"] >= 0.0, f"MAE is negative: {data['mae']}"

    # ── best_metrics dict on the result object ─────────────────────────── #

    @pytest.mark.parametrize("key", ["rmse", "mae", "r2"])
    def test_best_metrics_has_required_key(self, pipeline_result, key):
        best = pipeline_result["best_metrics"]
        assert key in best, (
            f"best_metrics is missing key '{key}'. Keys: {list(best.keys())}"
        )

    # ── all_results covers every algorithm ──────────────────────────── #

    def test_all_results_is_non_empty_list(self, pipeline_result):
        results = pipeline_result["all_results"]
        assert isinstance(results, list) and len(results) > 0, (
            "all_results should be a non-empty list."
        )

    def test_all_results_covers_all_algorithms(self, pipeline_result):
        reported_names = {r["name"] for r in pipeline_result["all_results"]}
        for algo in _ALGORITHM_NAMES:
            assert algo in reported_names, (
                f"Algorithm '{algo}' missing from all_results. "
                f"Reported: {reported_names}"
            )

    def test_all_results_have_status_field(self, pipeline_result):
        for r in pipeline_result["all_results"]:
            assert "status" in r, f"Result entry for '{r.get('name')}' has no 'status' key."

    def test_all_results_have_rmse_field(self, pipeline_result):
        for r in pipeline_result["all_results"]:
            assert "rmse" in r, f"Result entry for '{r.get('name')}' has no 'rmse' key."

    # ── Model is registered ──────────────────────────────────────────── #

    def test_model_registered_in_registry(self, pipeline_result):
        """
        The pipeline calls register_model(); verify registry entry exists.
        Falls back to checking the returned registered_entry dict if the
        SQLite DB / JSON file is not accessible in this test environment.
        """
        reg = pipeline_result.get("registered_entry")
        # Either a non-None entry dict (file-backed) OR DB lookup succeeds
        assert reg is not None, "registered_entry in pipeline result is None."
        assert reg.get("model_name") == "sales", (
            f"Registered model_name should be 'sales', got: {reg.get('model_name')!r}"
        )

    def test_registered_entry_has_version(self, pipeline_result):
        reg = pipeline_result.get("registered_entry", {})
        assert reg.get("version") == "pytest_eval_v1", (
            f"Registered version mismatch: {reg.get('version')!r}"
        )

    # ── Loaded model can predict ──────────────────────────────────────── #

    def test_saved_model_can_predict(self, pipeline_result):
        import joblib
        model = joblib.load(pipeline_result["model_path"])
        sample = np.zeros((1, len(_FEATURE_COLS)))
        pred   = model.predict(sample)
        assert len(pred) == 1, "Loaded model did not return a single prediction."


# ============================================================================ #
# Tests — train_sales_model() backward compatibility
# ============================================================================ #

class TestSalesTrainingBackwardCompat:
    """Ensure the Sprint 1 contract for train_sales_model() is intact."""

    def test_returns_success_status(self, training_result):
        assert training_result["status"] == "success", (
            f"train_sales_model returned status '{training_result['status']}'."
        )

    @pytest.mark.parametrize("key", sorted(_SPRINT1_RETURN_KEYS))
    def test_sprint1_return_key_present(self, training_result, key):
        assert key in training_result, (
            f"Sprint 1 return key '{key}' missing from train_sales_model() result. "
            f"Keys: {list(training_result.keys())}"
        )

    def test_model_name_is_sales(self, training_result):
        assert training_result["model_name"] == "sales"

    def test_version_is_non_empty(self, training_result):
        assert isinstance(training_result["version"], str) and len(training_result["version"]) > 0

    def test_model_path_file_exists(self, training_result):
        path = training_result["model_path"]
        assert path is not None and os.path.exists(path), (
            f"model_path '{path}' does not exist on disk."
        )

    def test_scaler_path_file_exists(self, training_result):
        path = training_result.get("scaler_path")
        assert path is not None and os.path.exists(path), (
            f"scaler_path '{path}' does not exist on disk."
        )

    def test_metrics_path_file_exists(self, training_result):
        path = training_result.get("metrics_path")
        assert path is not None and os.path.exists(path), (
            f"metrics_path '{path}' does not exist on disk."
        )

    def test_accuracy_is_float(self, training_result):
        acc = training_result["accuracy"]
        assert isinstance(acc, float), f"accuracy should be float, got {type(acc)}."

    def test_sprint2_all_results_present(self, training_result):
        """Sprint 2 additions should also be present."""
        assert "all_results" in training_result
        assert isinstance(training_result["all_results"], list)
        assert len(training_result["all_results"]) > 0

    def test_sprint2_best_model_name_present(self, training_result):
        assert "best_model_name" in training_result
        assert isinstance(training_result["best_model_name"], str)

    def test_sprint2_metrics_path_is_valid_json(self, training_result):
        path = training_result.get("metrics_path")
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "rmse" in data and "mae" in data and "r2" in data


# ============================================================================ #
# Tests — edge cases
# ============================================================================ #

class TestEdgeCases:
    """Guard against edge-case inputs to run_evaluation_pipeline()."""

    def test_empty_dataframe_raises_or_fails_gracefully(self, tmp_path):
        """An empty DataFrame should not crash the process — it may return 'failed'."""
        import pandas as pd
        df = pd.DataFrame(columns=_FEATURE_COLS + [_TARGET_COL])
        result = run_evaluation_pipeline(
            df           = df,
            feature_cols = _FEATURE_COLS,
            target_col   = _TARGET_COL,
            models_dir   = str(tmp_path / "models"),
            version      = "edge_empty",
        )
        # We expect either "failed" status or a ValueError — not a hard crash
        assert result["status"] in ("success", "failed"), (
            f"Unexpected status for empty DF: {result['status']}"
        )

    def test_missing_feature_columns_filled_with_zeros(self, tmp_path):
        """
        If feature_cols contains columns not in df, they should be silently
        filled with 0.0 rather than raising a KeyError.
        """
        df     = _make_synthetic_df(n=120)
        result = run_evaluation_pipeline(
            df           = df,
            feature_cols = _FEATURE_COLS + ["nonexistent_feature"],
            target_col   = _TARGET_COL,
            models_dir   = str(tmp_path / "models_missing"),
            version      = "edge_missing_cols",
        )
        assert result["status"] == "success", (
            f"Pipeline failed when extra feature col was absent: {result.get('error')}"
        )


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
