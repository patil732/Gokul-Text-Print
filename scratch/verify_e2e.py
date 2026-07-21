"""
End-to-End Pipeline Verification Script
---------------------------------------
1. ETL: Ingestion + Processing
2. Sales Training: python -m app.sales.train
3. Inventory Training: python -m app.inventory.train
4. BusinessAILayer Prediction: get_sales_insight & get_inventory_insight
5. Flask Routes: /ceo/dashboard, /ceo/simulate, /admin/monitor
"""

import os
import sys

sys.path.insert(0, ".")

import pandas as pd
from app.etl.processing import run_processing
from app.sales.train import train as train_sales
from app.inventory.train import train as train_inventory
from app.business_ai_layer import business_ai
from app.config import cfg
import importlib.util
spec = importlib.util.spec_from_file_location("app_entry", os.path.join(os.path.dirname(__file__), "..", "app.py"))
app_entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_entry)
create_app = app_entry.create_app

def run_e2e():
    print("==================================================")
    print("STEP 1: ETL Processing")
    print("==================================================")
    # Check if raw data exists or process existing raw data
    proc_summary = run_processing()
    print("ETL processing summary:", proc_summary)
    assert proc_summary["status"] == "success", "ETL processing failed"

    print("\n==================================================")
    print("STEP 2: Sales Training")
    print("==================================================")
    train_sales(force_reprocess=True)
    assert os.path.exists(cfg.SALES_MODEL_PATH), "Sales model file missing"
    assert os.path.exists(cfg.SALES_SHAP_PATH), "Sales SHAP file missing"
    print("Sales training completed & artefacts verified.")

    print("\n==================================================")
    print("STEP 3: Inventory Training")
    print("==================================================")
    train_inventory(force_reprocess=True)
    assert os.path.exists(cfg.INVENTORY_MODEL_PATH), "Inventory model file missing"
    assert os.path.exists(cfg.INVENTORY_SHAP_PATH), "Inventory SHAP file missing"
    print("Inventory training completed & artefacts verified.")

    print("\n==================================================")
    print("STEP 4: BusinessAILayer Predictions")
    print("==================================================")
    # Test Sales Prediction
    from app.sales.model import FEATURE_COLS as SALES_FEATS
    sales_input = {col: 10.0 for col in SALES_FEATS}
    sales_res = business_ai.get_sales_insight(sales_input)
    print("Sales Insight Result:", sales_res)
    assert sales_res["status"] == "success", f"Sales insight failed: {sales_res}"

    # Test Inventory Prediction
    from app.inventory.model import FEATURE_COLS as INV_FEATS
    inv_input = {col: 5.0 for col in INV_FEATS}
    inv_res = business_ai.get_inventory_insight(inv_input)
    print("Inventory Insight Result:", inv_res)
    assert inv_res["status"] == "success", f"Inventory insight failed: {inv_res}"

    print("\n==================================================")
    print("STEP 5: Flask Dashboard Routes Render Check")
    print("==================================================")
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["user"] = "test_ceo"
        sess["role"] = "ceo"

    resp_ceo = client.get("/ceo/dashboard")
    print("GET /ceo/dashboard -> status:", resp_ceo.status_code)
    print("Data:", resp_ceo.get_json())
    assert resp_ceo.status_code == 200, f"CEO dashboard failed: {resp_ceo.data}"
    assert resp_ceo.get_json()["status"] == "success"

    resp_sim = client.post("/ceo/simulate", json={"sales_change": 10, "stock_change": -5})
    print("POST /ceo/simulate -> status:", resp_sim.status_code)
    print("Data:", resp_sim.get_json())
    assert resp_sim.status_code == 200, f"CEO simulate failed: {resp_sim.data}"
    assert resp_sim.get_json()["status"] == "success"

    with client.session_transaction() as sess:
        sess["user"] = "test_admin"
        sess["role"] = "admin"

    resp_admin = client.get("/admin/monitor")
    print("GET /admin/monitor -> status:", resp_admin.status_code)
    print("Data:", resp_admin.get_json())
    assert resp_admin.status_code == 200, f"Admin monitor failed: {resp_admin.data}"
    assert resp_admin.get_json()["status"] == "success"

    print("\n==================================================")
    print("ALL END-TO-END VERIFICATION CHECKS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_e2e()
