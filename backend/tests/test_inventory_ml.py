"""
tests/test_inventory_ml.py
---------------------------
Unit test suite for app/ml/inventory/ module and Flask endpoints.
Verifies that:
  1. train_inventory_model() produces saved model & scaler files in models/inventory/ and registers entry.
  2. predict_inventory() returns a valid structured response shape.
  3. Flask API endpoints (/api/ml/inventory/train, /api/ml/inventory/predict, /api/ml/inventory/metrics) function as expected.
"""

import os
import sys
import pytest

sys.path.insert(0, ".")

from app.ml.inventory.inventory_training import train_inventory_model
from app.ml.inventory.inventory_prediction import predict_inventory
from app.ml.common.model_registry import get_latest_version
import importlib.util

spec = importlib.util.spec_from_file_location("app_entry", os.path.join(os.path.dirname(__file__), "..", "app.py"))
app_entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_entry)
create_app = app_entry.create_app


def test_inventory_model_training_and_prediction():
    # 1. Run training pipeline
    res = train_inventory_model(version="unittest_inv_v1")

    assert res["status"] == "success"
    assert res["model_name"] == "inventory"
    assert res["version"] == "unittest_inv_v1"
    assert os.path.exists(res["model_path"]), f"Model file missing at {res['model_path']}"

    # 2. Check registry entry
    latest = get_latest_version("inventory")
    assert latest is not None
    assert latest["version"] == "unittest_inv_v1"

    # 3. Test prediction response shape
    sample_input = {
        "total_stock": 1500.0,
        "warehouse_count": 3,
        "avg_stock_per_wh": 500.0,
        "max_stock_in_wh": 800.0,
        "stock_concentration": 0.53,
        "total_qty_planned": 1000.0,
        "total_produced": 900.0,
        "production_gap": 100.0,
        "fulfillment_rate": 0.9,
        "has_open_orders": 1,
        "available_qty": 1500.0,
        "safety_stock": 235.0,
        "stock_turnover": 0.6,
        "days_in_inventory": 50.0,
        "fast_moving": 0,
        "slow_moving": 0,
        "dead_stock": 0,
        "reorder_level": 468.33,
    }

    pred_res = predict_inventory(sample_input)

    assert pred_res["status"] == "success"
    assert pred_res["domain"] == "inventory"
    assert pred_res["model_name"] == "inventory"
    assert "decision" in pred_res
    assert "prediction" in pred_res
    assert "confidence" in pred_res
    assert "probability" in pred_res
    assert isinstance(pred_res["prediction"], int)
    assert isinstance(pred_res["probability"], float)


def test_inventory_flask_endpoints():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Test POST /api/ml/inventory/train
    resp_train = client.post("/api/ml/inventory/train", json={"version": "unittest_inv_api_v1"})
    assert resp_train.status_code == 200
    json_train = resp_train.get_json()
    assert json_train["status"] == "success"

    # 2. Test GET /api/ml/inventory/metrics
    resp_metrics = client.get("/api/ml/inventory/metrics")
    assert resp_metrics.status_code == 200
    json_metrics = resp_metrics.get_json()
    assert json_metrics["status"] == "success"
    assert "accuracy" in json_metrics

    # 3. Test POST /api/ml/inventory/predict
    resp_pred = client.post("/api/ml/inventory/predict", json={"total_stock": 100.0, "reorder_level": 500.0})
    assert resp_pred.status_code == 200
    json_pred = resp_pred.get_json()
    assert json_pred["status"] == "success"
    assert "decision" in json_pred


if __name__ == "__main__":
    print("Running inventory ML unit tests ...")
    test_inventory_model_training_and_prediction()
    print("PASS: test_inventory_model_training_and_prediction")
    test_inventory_flask_endpoints()
    print("PASS: test_inventory_flask_endpoints")
    print("\nALL INVENTORY ML UNIT TESTS PASSED SUCCESSFULLY!")
