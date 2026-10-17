# DEPLOYMENT.md — Enterprise AI Sales & Inventory Copilot
## Gokul Text Print — Production Deployment Guide

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Variables](#2-environment-variables)
3. [Local Development Setup](#3-local-development-setup)
4. [Production Server (Gunicorn)](#4-production-server-gunicorn)
5. [Render Deployment](#5-render-deployment)
6. [Persistence & Storage](#6-persistence--storage)
7. [Memory & Instance Sizing](#7-memory--instance-sizing)
8. [Security Checklist](#8-security-checklist)
9. [Post-Deploy Smoke Test Checklist](#9-post-deploy-smoke-test-checklist)

---

## 1. Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| pip | latest |
| npm | latest |
| Git | 2.x |

---

## 2. Environment Variables

Copy `.env.example` to `.env` (backend) and `frontend/.env.local.example` to `frontend/.env.local`.

### Backend (`backend/.env` or Render env vars)

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Flask session key — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_ENV` | ✅ | `production` in prod, `development` locally |
| `FLASK_DEBUG` | ✅ | `False` in production |
| `PORT` | auto | Render injects this automatically |
| `DATABASE_URL` | ✅ | SQLite: `sqlite:////var/data/platform.db` · PostgreSQL: `postgresql://user:pass@host:5432/db` |
| `ERP_BASE_URL` | ✅ | Frappe/ERPNext base URL |
| `ERP_API_KEY` | ✅ | ERP API key |
| `ERP_API_SECRET` | ✅ | ERP API secret |
| `LLM_PROVIDER` | ✅ | `gemini` or `openai` |
| `GEMINI_API_KEY` | cond. | Required if LLM_PROVIDER=gemini |
| `OPENAI_API_KEY` | cond. | Required if LLM_PROVIDER=openai |
| `FRONTEND_ORIGIN` | ✅ | Deployed frontend URL for CORS (e.g. `https://gtp-frontend.onrender.com`) |
| `SALES_MODEL_VERSION` | opt. | Default: `sales_rf` |
| `INVENTORY_MODEL_VERSION` | opt. | Default: `inventory_rf` |
| `DOCUMENTS_DIR` | prod | Path for uploaded PDFs (e.g. `/var/data/documents`) |
| `FAISS_INDEX_PATH` | prod | Path for FAISS vector index (e.g. `/var/data/faiss_index`) |
| `MODELS_DIR` | prod | Path for model `.pkl` files (e.g. `/var/data/models`) |
| `REPORTS_DIR` | prod | Path for generated PDF reports (e.g. `/var/data/reports`) |
| `LOGS_DIR` | prod | Path for application logs (e.g. `/var/data/logs`) |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend URL — e.g. `https://gtp-backend.onrender.com` |

> **Never commit `.env`, `backend/.env`, or `frontend/.env.local` to version control.**

---

## 3. Local Development Setup

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example ../.env   # fill in values
python app.py                # starts on http://localhost:5001
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_BASE_URL=http://localhost:5001
npm install
npm run dev                         # starts on http://localhost:3000
```

---

## 4. Production Server (Gunicorn)

The app uses the **factory pattern** (`create_app()`). The verified start command:

```bash
gunicorn "app:create_app()" \
  --bind 0.0.0.0:$PORT \
  --workers 2 \
  --timeout 120 \
  --log-level info
```

> **Why 2 workers?** The sentence-transformers embedding model loads ~1 GB into memory per worker. With SHAP (~23 MB) and XGBoost/LightGBM models, use 2 workers on a **Standard plan** (2 GB RAM). Scale workers only after upgrading the instance.

To verify locally:
```bash
cd backend
FLASK_ENV=production SECRET_KEY=test gunicorn "app:create_app()" --bind 0.0.0.0:5001 --workers 1 --timeout 120
curl http://localhost:5001/health   # should return {"status": "ok"}
```

---

## 5. Render Deployment

### Option A — Blueprint (recommended)

1. Push `render.yaml` to the `main` branch.
2. In Render Dashboard → **New** → **Blueprint** → select the GitHub repo.
3. Render creates `gtp-backend` and `gtp-frontend` services automatically.
4. Fill in all **`sync: false`** environment variables in each service's dashboard.
5. Attach a **Persistent Disk** to `gtp-backend`:
   - Mount path: `/var/data`
   - Size: 10 GB
6. Set disk env vars (`DOCUMENTS_DIR=/var/data/documents`, etc.)
7. Trigger a manual deploy (or push to `main` for auto-deploy).

### Option B — Manual Dashboard

**Backend service:**
- Type: **Web Service**
- Runtime: **Python 3**
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- Health check path: `/health`
- Plan: **Standard** (minimum)
- Auto-deploy: from `main` branch

**Frontend service:**
- Type: **Web Service**
- Runtime: **Node**
- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Start command: `npm start`
- Env var: `NEXT_PUBLIC_API_BASE_URL=https://gtp-backend.onrender.com`

---

## 6. Persistence & Storage

Everything written to local disk at runtime — and the decision for each:

| Artefact | Path | Decision | Notes |
|---|---|---|---|
| Uploaded PDFs | `backend/documents/` | **Persistent disk** `/var/data/documents` | Set `DOCUMENTS_DIR` env var |
| FAISS index | `backend/app/rag/` | **Persistent disk** `/var/data/faiss_index` | Set `FAISS_INDEX_PATH` env var; index is rebuilt from DB on first run |
| Model `.pkl` files (sales_rf, inventory_rf, SHAP) | `backend/models/` | **Commit to repo OR persistent disk** `/var/data/models` | Existing `sales_rf.pkl` (174 KB), `inventory_rf.pkl` (232 KB) are small enough to commit. `sales_shap.pkl` (23 MB) should go on the disk. |
| Scaler `.pkl` files | `backend/models/` | Same as model files | Small (< 2 KB) — safe to commit |
| SHAP images | `backend/static/` | **Persistent disk** or regenerate on demand | Currently regenerated per request — no change needed |
| Generated PDF reports | `backend/static/reports/` | **Persistent disk** `/var/data/reports` | Set `REPORTS_DIR` env var |
| SQLite database | `backend/ai_decision.db` | **Persistent disk** `/var/data/platform.db` | Use `DATABASE_URL=sqlite:////var/data/platform.db` OR migrate to PostgreSQL |
| Application logs | `backend/logs/` | **Persistent disk** `/var/data/logs` | Set `LOGS_DIR` env var; Render also captures stdout |

> **Recommendation:** For production, migrate from SQLite to **PostgreSQL** (available as a Render managed database). SQLite on the persistent disk works for small teams but does not support concurrent writes.

---

## 7. Memory & Instance Sizing

| Component | Estimated RAM |
|---|---|
| Flask + Gunicorn base | ~80 MB |
| sentence-transformers (all-MiniLM-L6-v2) | ~90–150 MB |
| XGBoost inventory model | ~50 MB |
| LightGBM / RandomForest sales model | ~30 MB |
| SHAP explainer (sales_shap.pkl = 23 MB) | ~50–100 MB peak |
| **Total (1 worker)** | **~350–500 MB** |
| **Total (2 workers)** | **~700 MB–1 GB** |

**Minimum Render plan: Standard (2 GB RAM)**

Use 2 workers. If you add more LLM context or increase FAISS index size, upgrade to Pro (4 GB).

---

## 8. Security Checklist

- [x] `SECRET_KEY` is a 64-char hex string from `secrets.token_hex(32)` — never the dev default
- [x] `FLASK_ENV=production` and `FLASK_DEBUG=False` in Render env vars
- [x] No stack traces or internal errors exposed in production responses (`app.py` errorhandler)
- [x] Session cookies: `HTTPONLY=True`, `SAMESITE=Lax`, `SECURE=True` (production)
- [x] CORS restricted to `FRONTEND_ORIGIN` only
- [x] No API keys in frontend bundles — `NEXT_PUBLIC_*` only holds the backend URL
- [x] `.env`, `backend/.env`, `frontend/.env.local` are gitignored
- [x] `sync: false` for all secrets in `render.yaml` — secrets entered via dashboard only
- [x] Database passwords not logged

---

## 9. Post-Deploy Smoke Test Checklist

Run these after every production deployment.

> ⚠️ `/health` returning OK **does NOT** prove AI features work. Complete all checks below.

### Infrastructure
- [ ] `GET https://gtp-backend.onrender.com/health` → `{"status": "ok"}` with HTTP 200
- [ ] Response time < 500 ms

### Authentication
- [ ] Login page loads at frontend URL
- [ ] CEO login succeeds and redirects to CEO dashboard
- [ ] Admin login succeeds and redirects to Admin dashboard
- [ ] Logout clears session; accessing protected route returns 401

### Sales Intelligence
- [ ] Sales dashboard loads with data (no blank charts)
- [ ] `POST /api/sales/forecast` with `{"forecast_period": "30_days"}` returns `status: success`
- [ ] SHAP explanation chart renders on forecast page

### Inventory Intelligence
- [ ] Inventory dashboard loads with stock data
- [ ] `POST /api/ml/inventory/predict` returns `status: success` with decision
- [ ] SHAP chart renders on inventory page

### RAG Knowledge Engine
- [ ] Upload a PDF document → status shows "Processed"
- [ ] `POST /api/rag/search` with a query returns relevant chunks
- [ ] Chat Q&A returns answers citing uploaded document

### AI Copilot (Multi-Agent)
- [ ] `GET /api/agent/status` → `status: online`
- [ ] Ask "Should we increase inventory?" → receives a structured answer with `agents_used`
- [ ] `POST /api/agents/manager` orchestration returns `status: success`

### Reports
- [ ] Generate a PDF report → download link works
- [ ] Downloaded PDF opens correctly

### Security Spot-Checks
- [ ] `GET /api/auth/me` without login → HTTP 401
- [ ] No `SECRET_KEY`, API keys, or DB passwords visible in response bodies
- [ ] No Python tracebacks in any error response body
- [ ] Browser DevTools → Application → Cookies: `HttpOnly` flag set on session cookie

---

*Last updated: 2026-10-17*
*Branch: feature/final-release-deployment*
