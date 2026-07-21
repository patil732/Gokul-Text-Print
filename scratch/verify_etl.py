"""
Smoke test for app/etl/ — runs without a live ERP connection.
Tests: logger, validators (all datasets), and module imports.
"""
import sys, os
sys.path.insert(0, '.')

import pandas as pd

# ------------------------------------------------------------------ #
# 1. Logger
# ------------------------------------------------------------------ #
from app.etl.logger import etl_logger as log, ETL_LOG_PATH
log.info("Smoke test started", extra={"etl_module": "test"})
log.warning("Test warning", extra={"etl_module": "test"})
log.error("Test error", extra={"etl_module": "test"})
assert os.path.exists(ETL_LOG_PATH), f"Log file not created at {ETL_LOG_PATH}"
with open(ETL_LOG_PATH, encoding="utf-8") as f:
    lines = f.readlines()
assert any("Smoke test started" in l for l in lines), "INFO not in log file"
assert any("Test warning"       in l for l in lines), "WARNING not in log file"
assert any("Test error"         in l for l in lines), "ERROR not in log file"
print(f"PASS: logger -> {ETL_LOG_PATH}")

# ------------------------------------------------------------------ #
# 2. Sales validator — good data
# ------------------------------------------------------------------ #
from app.etl.validators import validate_sales, validate_stock, validate_production, log_validation_result

good_sales = pd.DataFrame({
    "name":             [f"SO-{i:04}" for i in range(200)],
    "transaction_date": pd.date_range("2024-01-01", periods=200, freq="D"),
    "customer":         ["Customer A"] * 200,
    "grand_total":      [1000.0 + i for i in range(200)],
    "status":           ["Submitted"] * 200,
})
r = validate_sales(good_sales)
assert r.passed, f"Good sales should pass: {r.errors}"
assert r.stats["rows"] == 200
print(f"PASS: validate_sales (good data) | stats={r.stats}")

# ------------------------------------------------------------------ #
# 3. Sales validator — missing required column
# ------------------------------------------------------------------ #
bad_schema = good_sales.drop(columns=["grand_total"])
r2 = validate_sales(bad_schema)
assert not r2.passed, "Missing grand_total should fail"
assert any("grand_total" in e for e in r2.errors), f"Expected column error, got: {r2.errors}"
print(f"PASS: validate_sales (missing column)")

# ------------------------------------------------------------------ #
# 4. Sales validator — empty DataFrame
# ------------------------------------------------------------------ #
r3 = validate_sales(pd.DataFrame())
assert not r3.passed, "Empty sales should fail"
print(f"PASS: validate_sales (empty DataFrame)")

# ------------------------------------------------------------------ #
# 5. Sales validator — too many nulls in grand_total
# ------------------------------------------------------------------ #
high_null = good_sales.copy()
high_null.loc[:110, "grand_total"] = None   # 55% null
r4 = validate_sales(high_null, max_null_frac=0.50)
assert not r4.passed, "55% nulls in grand_total should fail"
print(f"PASS: validate_sales (high null fraction)")

# ------------------------------------------------------------------ #
# 6. Sales validator — below row-count warn threshold
# ------------------------------------------------------------------ #
small = good_sales.head(50)
r5 = validate_sales(small, min_rows_warn=100)
assert r5.passed, "50-row sales should still pass"
assert any("only 50 rows" in w or "50 rows" in w for w in r5.warnings), \
    f"Expected row-count warning, got: {r5.warnings}"
print(f"PASS: validate_sales (row-count warning)")

# ------------------------------------------------------------------ #
# 7. Stock validator — optional, never blocks
# ------------------------------------------------------------------ #
good_stock = pd.DataFrame({
    "name":       [f"BIN-{i}" for i in range(100)],
    "item_code":  [f"ITEM-{i}" for i in range(100)],
    "actual_qty": [float(i * 5) for i in range(100)],
    "warehouse":  ["Main WH"] * 100,
})
r6 = validate_stock(good_stock)
assert r6.passed, f"Good stock should pass: {r6.errors}"
print(f"PASS: validate_stock (good data)")

# Empty stock should warn but pass
r7 = validate_stock(pd.DataFrame())
assert r7.passed, "Empty stock should still pass (optional)"
assert any("empty" in w.lower() for w in r7.warnings)
print(f"PASS: validate_stock (empty, passes with warning)")

# ------------------------------------------------------------------ #
# 8. Production validator — optional, never blocks
# ------------------------------------------------------------------ #
good_prod = pd.DataFrame({
    "name":         [f"WO-{i}" for i in range(30)],
    "item":         [f"ITEM-{i}" for i in range(30)],
    "qty":          [10.0] * 30,
    "produced_qty": [8.0] * 30,
    "status":       ["Submitted"] * 30,
})
r8 = validate_production(good_prod)
assert r8.passed, f"Good production should pass: {r8.errors}"
print(f"PASS: validate_production (good data)")

# ------------------------------------------------------------------ #
# 9. log_validation_result helper
# ------------------------------------------------------------------ #
log_validation_result(r, log, "sales_test")
log_validation_result(r2, log, "sales_bad_schema")
print("PASS: log_validation_result")

# ------------------------------------------------------------------ #
# 10. Module imports
# ------------------------------------------------------------------ #
from app.etl.ingestion  import run_ingestion, ETLIngestionError
from app.etl.processing import run_processing, ETLProcessingError
from pipelines.data_ingestion  import run_data_ingestion
from pipelines.data_processing import run_data_processing
print("PASS: all module imports OK")

print()
print("All smoke tests passed.")
print(f"ETL log: {ETL_LOG_PATH}")
