# Gokul Text Print — Enterprise AI Platform

> **Executive Intelligence Platform** for textile printing mill operations.  
> AI-powered sales forecasting, inventory intelligence, multi-agent copilot, and automated reporting.

---

## Architecture

`
+-------------------------------------------------------------+
|  Next.js 15 (App Router)  — http://localhost:3000           |
|  Frontend: TypeScript, Tailwind CSS v4, Recharts            |
+----------------------+--------------------------------------+
                       | REST API (JSON + file downloads)
+----------------------v--------------------------------------+
|  Flask 3.x — http://localhost:5001                          |
|  Blueprints: auth, ceo, admin, dashboard,                   |
|              documents, rag, chat, agent                    |
+----------------------+--------------------------------------+
                       |
+----------------------v--------------------------------------+
|  SQLite  — ai_decision.db                                  |
|  Tables: users, sales_data, inventory, alerts,              |
|          chunk_embeddings, documents, chat_history          |
+-------------------------------------------------------------+
`

---

## Quick Start

### 1. Terminal 1 — Start Backend (Flask API Server)
```powershell
cd backend
..\venv\Scripts\python.exe app.py
```
> 🌐 Runs on: **`http://localhost:5001`**

### 2. Terminal 2 — Start Frontend (Next.js Application)
```powershell
cd frontend
npm run dev
```
> 🌐 Runs on: **`http://localhost:3000`**

---

## Environment Variables

Copy the templates and fill in your values:

```bash
# Backend
cp .env.example .env

# Frontend
cp frontend/.env.local.example frontend/.env.local
```

See [DEPLOYMENT.md](DEPLOYMENT.md#2-environment-variables) for a full variable reference.  
**Never commit `.env` or `.env.local` files.**

---

## User Roles and Credentials

| Role | Username | Password | Direct Landing Page |
| :--- | :--- | :--- | :--- |
| **CEO / Executive** | `ceo` | `ceo123` | `/dashboard` *(Executive Strategic Dashboard)* |
| **System Admin** | `admin` | `admin123` | `/admin` *(Admin Operations & Telemetry)* |

---

## Running Tests

### Backend — CI Smoke Suite (no external services):
```powershell
cd backend
..\venv\Scripts\pytest.exe tests/test_health.py tests/test_ci_smoke.py -v
```

### Backend — Full Pytest Suite:
```powershell
cd backend
..\venv\Scripts\pytest.exe tests/
```

### Frontend E2E Playwright Suite:
```powershell
cd frontend
npx playwright test
```

---

## CI/CD

GitHub Actions runs on every push and pull request to `main`/`develop`:
- **Backend job**: installs Python 3.11, runs `pytest tests/test_health.py tests/test_ci_smoke.py`
- **Frontend job**: installs Node 20, runs `npm ci && npm run build`

No real secrets are used in CI. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Production Deployment (Render)

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the complete guide, including:
- Gunicorn start command
- Render Blueprint setup
- Persistent disk configuration
- Memory & instance sizing
- Post-deploy smoke test checklist

**Quick reference — start command:**
```bash
gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Health check:** `GET /health` → `{"status": "ok"}`

---

## Tech Stack

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4, Recharts
- Backend: Flask 3, Werkzeug, Gunicorn, Flask-CORS
- Database: SQLite (dev) / PostgreSQL (production)
- ML: LightGBM, XGBoost, RandomForest, SHAP
- AI: Google Gemini API (config-switchable to OpenAI)
- RAG: FAISS, sentence-transformers
- Reports: ReportLab PDF, built-in CSV
- Testing: Pytest, Playwright

