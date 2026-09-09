# System Architecture — Decoupled AI Platform

This document describes the refactored architecture of the AI platform, establishing decoupled domain modules (`app/sales/`, `app/inventory/`), a central orchestration layer (`app/business_ai_layer.py`), unified configuration management (`app/config.py`), and a validated ETL engine (`app/etl/`).

---

## 1. Directory Structure

```
app/
├── config.py                 # Centralised configuration loader (.env driven)
├── business_ai_layer.py      # Domain orchestrator & API routing layer
├── etl/
│   ├── __init__.py
│   ├── logger.py             # Dedicated ETL logger (logs/etl.log, rotating)
│   ├── validators.py         # Multi-tier schema, null & sanity checks
│   ├── ingestion.py          # Validated ERP data ingestion
│   └── processing.py         # Validated feature engineering pipeline
├── sales/
│   ├── data_loader.py        # Raw sales dataset loader
│   ├── preprocess.py         # Sales feature engineering & target creation
│   ├── model.py              # Sales Random Forest model & SHAP persistence
│   ├── train.py              # Sales training pipeline & CLI entry point
│   └── predict.py            # Sales inference engine & SHAP explanation
└── inventory/
    ├── data_loader.py        # Raw stock & production dataset loader
    ├── preprocess.py         # Inventory feature engineering & target creation
    ├── model.py              # Inventory Random Forest model & SHAP persistence
    ├── train.py              # Inventory training pipeline & CLI entry point
    └── predict.py            # Inventory inference engine & SHAP explanation
```

---

## 2. Component Architecture

### A. Central Configuration (`app/config.py`)
- Sourced entirely from `.env` with fallback defaults.
- Manages paths for raw data (`data/raw`), processed data (`data/processed`), and model artefacts (`models/`).
- Supports dynamic model versioning via `SALES_MODEL_VERSION` and `INVENTORY_MODEL_VERSION` environment variables.
- Exposes DB paths (`DATABASE_URL`, `DB_PATH`) and placeholders for `LLM_PROVIDER` and `LLM_API_KEY`.

### B. Business AI Orchestration (`app/business_ai_layer.py`)
- **Role**: Pure orchestration/routing layer between web routes (Flask dashboard) and domain ML modules.
- **Stateless & Decoupled**: Contains zero ML model logic.
- **Lazy Imports**: Loads domain prediction engines (`app.sales.predict`, `app.inventory.predict`) on demand to keep web server startup instant.
- **Resilient**: Wraps predictions in a unified error contract (`{status, domain, decision, prediction, confidence, probability, reasons}`).

```
   Flask Dashboard Routes (/ceo/*, /admin/*)
                      │
                      ▼
         ┌─────────────────────────┐
         │   BusinessAILayer       │
         └────────────┬────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌──────────────────┐     ┌──────────────────────┐
│ app.sales.predict│     │ app.inventory.predict│
└────────┬─────────┘     └──────────┬───────────┘
         │                          │
         ▼                          ▼
  sales_rf.pkl               inventory_rf.pkl
  sales_shap.pkl             inventory_shap.pkl
```

### C. Domain Modules (`app/sales/` and `app/inventory/`)
- **Strict Decoupling**: `app/sales` and `app/inventory` operate completely independently. Neither imports from the other.
- **Model Artefacts**:
  - Sales: `models/sales_rf.pkl` & `models/sales_shap.pkl`
  - Inventory: `models/inventory_rf.pkl` & `models/inventory_shap.pkl`
- **CLI Entry Points**:
  - `python -m app.sales.train [--force-reprocess]`
  - `python -m app.inventory.train [--force-reprocess]`

### D. Validated ETL Layer (`app/etl/`)
- **Validation Rules** (`validators.py`):
  - Tier 1: Schema validation (column presence)
  - Tier 2: Row-count sanity checks
  - Tier 3: Critical column null fraction checks
  - Tier 4: Value bounds (non-negative constraints)
  - Tier 5: Deduplication checks
- **Logging** (`logger.py`): Rotates `logs/etl.log` up to 50 MB with structured module tags (`ingestion`, `processing`, `validators`).

---

## 3. Preparation for Sprint 2 (Sales Intelligence Engine)

With Sprint 1 complete, the codebase is modular and ready for Sprint 2 enhancements:
1. **Sales Intelligence Extension**: Deepen `app/sales/` feature engineering and time-series models without affecting inventory or dashboard routing.
2. **Inventory Model Tuning**: Advance `app/inventory/` model algorithms independently.
3. **LLM Integration**: Plug LLM reasoning into `BusinessAILayer` using `LLM_PROVIDER` and `LLM_API_KEY` configured in `app/config.py`.
