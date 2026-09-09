"""
tests/test_sales_ml.py
-----------------------
Unit test suite for app/ml/sales/ module and Flask endpoints.
Verifies that:
  1. train_sales_model() produces saved model & scaler files in models/sales/ and registers entry.
  2. predict_sales() returns a valid structured response shape.
  3. Flask API endpoints (/api/ml/sales/train, /api/ml/sales/predict, /api/ml/sales/metrics) function as expected.
"""

import os
import sys
import pytest

sys.path.insert(0, ".")

from app.ml.sales.sales_training import train_sales_model
from app.ml.sales.sales_prediction import predict_sales
from app.ml.common.model_registry import get_latest_version
import importlib.util

spec = importlib.util.spec_from_file_location("app_entry", os.path.join(os.path.dirname(__file__), "..", "app.py"))
app_entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_entry)
create_app = app_entry.create_app


def test_sales_model_training_and_prediction():
    # 1. Run training pipeline
    res = train_sales_model(version="unittest_v1")

    assert res["status"] == "success"
    assert res["model_name"] == "sales"
    assert res["version"] == "unittest_v1"
    assert os.path.exists(res["model_path"]), f"Model file missing at {res['model_path']}"

    # 2. Check registry entry
    latest = get_latest_version("sales")
    assert latest is not None
    assert latest["version"] == "unittest_v1"

    # 3. Test prediction response shape
    sample_input = {
        "sales": 5000.0,
        "sales_lag_1": 4800.0,
        "sales_lag_2": 4600.0,
        "sales_lag_3": 4500.0,
        "sales_ma_3": 4800.0,
        "sales_ma_7": 4700.0,
        "sales_ma_14": 4500.0,
        "sales_std_7": 200.0,
        "momentum": 500.0,
        "trend": 1,
        "stock_ratio": 2.5,
    }

    pred_res = predict_sales(sample_input)

    assert pred_res["status"] == "success"
    assert pred_res["domain"] == "sales"
    assert pred_res["model_name"] == "sales"
    assert "decision" in pred_res
    assert "prediction" in pred_res
    assert "confidence" in pred_res
    assert "probability" in pred_res
    assert isinstance(pred_res["prediction"], int)
    assert isinstance(pred_res["probability"], float)


def test_sales_flask_endpoints():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Test POST /api/ml/sales/train
    resp_train = client.post("/api/ml/sales/train", json={"version": "unittest_api_v1"})
    assert resp_train.status_code == 200
    json_train = resp_train.get_json()
    assert json_train["status"] == "success"

    # 2. Test GET /api/ml/sales/metrics
    resp_metrics = client.get("/api/ml/sales/metrics")
    assert resp_metrics.status_code == 200
    json_metrics = resp_metrics.get_json()
    assert json_metrics["status"] == "success"
    assert "accuracy" in json_metrics

    # 3. Test POST /api/ml/sales/predict
    resp_pred = client.post("/api/ml/sales/predict", json={"sales": 6000.0, "sales_lag_1": 5500.0})
    assert resp_pred.status_code == 200
    json_pred = resp_pred.get_json()
    assert json_pred["status"] == "success"
    assert "decision" in json_pred


if __name__ == "__main__":
    print("Running sales ML unit tests ...")
    test_sales_model_training_and_prediction()
    print("PASS: test_sales_model_training_and_prediction")
    test_sales_flask_endpoints()
    print("PASS: test_sales_flask_endpoints")
    print("\nALL SALES ML UNIT TESTS PASSED SUCCESSFULLY!")
