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

## User Roles and Credentials

| Role | Username | Password | Direct Landing Page |
| :--- | :--- | :--- | :--- |
| **CEO / Executive** | `ceo` | `admin123` | `/dashboard` *(Executive Strategic Dashboard)* |
| **System Admin** | `admin` | `admin123` | `/admin` *(Admin Operations & Telemetry)* |

---

## Running Tests

### Backend Pytest Suite (844 Tests):
```powershell
cd backend
..\venv\Scripts\pytest.exe tests/
```

### Frontend E2E Playwright Suite (8 Scenarios):
```powershell
cd frontend
npx playwright test
```

---

## Tech Stack

- Frontend: Next.js 15, React 19, TypeScript, Tailwind CSS v4, Recharts
- Backend: Flask 3, Werkzeug, Flask-CORS
- Database: SQLite
- ML: LightGBM, XGBoost, ARIMA, SHAP
- AI: Google Gemini API (config-switchable to OpenAI)
- RAG: ChromaDB, sentence-transformers
- Reports: ReportLab PDF, built-in CSV
- Testing: Pytest, Playwright
