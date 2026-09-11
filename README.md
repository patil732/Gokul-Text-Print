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

### Prerequisites
- Python 3.10+
- Node.js 20+

### 1. Clone and install backend
`
git clone <repo-url>
cd "Gokul Text Print"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
`

### 2. Configure environment
`
copy .env.example .env
# Edit .env and set SECRET_KEY and GEMINI_API_KEY
`

### 3. Start Flask API server
`
python app.py
# API available at http://localhost:5001
`

### 4. Install and start frontend
`
cd frontend
npm install
npm run dev
# App available at http://localhost:3000
`

---

## User Roles and Credentials

| Role  | Username | Password | Default Landing       |
|-------|----------|----------|-----------------------|
| Admin | admin    | admin123 | /admin                |
| CEO   | ceo      | ceo123   | /dashboard            |

---

## Key Pages

| Page                  | Path       | Available To |
|-----------------------|------------|-------------|
| Executive Dashboard   | /dashboard | CEO         |
| Sales Intelligence    | /sales     | CEO         |
| Inventory Intelligence| /inventory | CEO         |
| AI Copilot            | /copilot   | CEO         |
| Knowledge Center      | /knowledge | CEO         |
| Reports Center        | /reports   | CEO         |
| Alert Center          | /alerts    | Both        |
| Settings              | /settings  | Both        |
| Admin Operations      | /admin     | Admin only  |

---

## Running Tests

Backend:
  .\venv\Scripts\python.exe -m pytest tests/ -v --tb=short

Frontend E2E (requires both servers running):
  cd frontend
  npx playwright test

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
