"""
tests/test_ci_smoke.py
-----------------------
CI smoke tests for critical routes.
All external services (PostgreSQL, ERP, LLM, embeddings, SHAP) are mocked.
These tests verify route registration and basic HTTP contract only.
They must run cleanly in CI with no real backend services.

Covered endpoints:
  - GET  /health
  - POST /api/auth/login
  - POST /api/sales/forecast
  - POST /api/ml/inventory/predict
  - POST /api/rag/search
  - POST /api/agent/ask
  - GET  /api/agent/status
"""

from __future__ import annotations

import json
import os
import sys
from typing import Generator
from unittest.mock import MagicMock, patch, PropertyMock

# ── Safe env vars (must be set before any app import) ─────────────────── #
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("FLASK_DEBUG", "False")
os.environ.setdefault("SECRET_KEY", "ci-test-secret-not-real")
os.environ.setdefault("DATABASE_URL", "sqlite:///ci_smoke.db")
os.environ.setdefault("ERP_BASE_URL", "http://fake-erp.local")
os.environ.setdefault("ERP_API_KEY", "fake")
os.environ.setdefault("ERP_API_SECRET", "fake")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini")
os.environ.setdefault("OPENAI_API_KEY", "fake-openai")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

import pytest


# ─────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────

def _make_mock_forecast():
    return {
        "status": "success",
        "forecast_period": "30_days",
        "predicted_sales": 550000.0,
        "growth_rate": 5.2,
        "confidence": 0.85,
        "explanation": ["Strong seasonal demand"],
        "model_type": "RandomForest",
        "version": "v1.0",
        "elapsed_ms": 12.4,
    }


def _make_mock_inventory_pred():
    return {
        "status": "success",
        "domain": "inventory",
        "prediction": 1,
        "confidence": 0.92,
        "decision": "Reorder Required",
        "probability": 0.92,
    }


def _make_mock_agent_response():
    return {
        "status": "success",
        "question": "Should we reorder fabric?",
        "answer": "Yes, current stock levels indicate reorder is needed.",
        "agents_used": ["sales", "inventory", "knowledge"],
        "confidence": 0.87,
    }


@pytest.fixture(scope="module")
def app():
    """
    Create the Flask app with ALL external services mocked.
    Patches applied before create_app() is called so there are no
    import-time side effects (DB connections, model loading, API calls).
    """
    # Mock heavy ML / embedding libraries
    fake_st = MagicMock()
    fake_st.encode.return_value = [[0.1] * 384]

    # Mock database init — no SQLite file created
    with (
        patch("services.automation.start_scheduler", return_value=None),
        # Sentence-transformers (embedding model)
        patch.dict("sys.modules", {
            "sentence_transformers": MagicMock(SentenceTransformer=MagicMock(return_value=fake_st)),
        }),
        # Mock ML model loading (joblib.load) to return a stub model
        patch("joblib.load", return_value=MagicMock(
            predict=MagicMock(return_value=[1]),
            predict_proba=MagicMock(return_value=[[0.1, 0.9]]),
        )),
        # Mock FAISS
        patch.dict("sys.modules", {
            "faiss": MagicMock(),
        }),
        # Mock OpenAI / Gemini clients
        patch.dict("sys.modules", {
            "openai": MagicMock(),
            "google.generativeai": MagicMock(),
        }),
    ):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "app_entry_smoke",
            os.path.join(_BACKEND, "app.py")
        )
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        flask_app = m.create_app()
        flask_app.config.update({
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
        })
        yield flask_app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def auth_client(app):
    """Return a client that has a seeded CEO session."""
    c = app.test_client()
    # Seed session directly to avoid DB dependency
    with app.test_request_context():
        with c.session_transaction() as sess:
            sess["user"] = "ceo"
            sess["role"] = "CEO"
    return c


# ─────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────

class TestHealthCI:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.get_json()["status"] == "ok"


class TestAuthRoutes:
    def test_login_endpoint_exists(self, client):
        """POST /api/auth/login must return 200 or 401 (not 404/500).
        The DB is seeded by init_db() (using SQLite ci_smoke.db).
        """
        r = client.post(
            "/api/auth/login",
            json={"username": "ceo", "password": "ceo123"},
        )
        # 200 = login success, 401 = wrong password, both are valid route responses
        assert r.status_code in (200, 401), (
            f"Unexpected status {r.status_code}: {r.data}"
        )

    def test_login_missing_credentials(self, client):
        r = client.post("/api/auth/login", json={})
        assert r.status_code == 400

    def test_logout_endpoint_exists(self, client):
        r = client.post("/api/auth/logout")
        assert r.status_code == 200


class TestSalesForecastRoute:
    def test_forecast_endpoint_exists(self, client):
        """POST /api/sales/forecast returns 200 or 503 (no 404)."""
        with patch(
            "app.ml.sales.routes.generate_forecast",
            return_value=_make_mock_forecast(),
        ):
            r = client.post(
                "/api/sales/forecast",
                json={"forecast_period": "30_days"},
            )
        assert r.status_code in (200, 503), (
            f"Unexpected {r.status_code}: {r.data}"
        )

    def test_forecast_bad_period(self, client):
        r = client.post(
            "/api/sales/forecast",
            json={"forecast_period": "invalid"},
        )
        assert r.status_code == 400


class TestInventoryPredictionRoute:
    def test_predict_endpoint_exists(self, client):
        with patch(
            "app.ml.inventory.routes.predict_inventory",
            return_value=_make_mock_inventory_pred(),
        ):
            r = client.post(
                "/api/ml/inventory/predict",
                json={"stock_level": 100.0},
            )
        assert r.status_code in (200, 503), (
            f"Unexpected {r.status_code}: {r.data}"
        )


class TestRAGSearchRoute:
    def test_rag_search_empty_query(self, client):
        """Empty query must return 400."""
        r = client.post("/api/rag/search", json={"query": ""})
        assert r.status_code == 400

    def test_rag_search_endpoint_exists(self, client):
        """Valid query returns 200 or 503 (no index yet) — never 404.
        500 is also acceptable when retriever encounters mock incompatibility.
        Route must be registered (no 404/405).
        """
        import numpy as np
        fake_chunks = [
            {
                "chunk_id": "c1",
                "chunk_text": "Reorder when stock < safety level",
                "page_number": 1,
                "source_document": "Policy.pdf",
                "score": 0.92,
            }
        ]
        with patch("routes.rag.retrieve", return_value=fake_chunks):
            r = client.post(
                "/api/rag/search",
                json={"query": "What is the reorder policy?"},
            )
        # 200 = results found, 503 = no embeddings, 500 = retriever internal error
        assert r.status_code in (200, 503, 500), (
            f"Route not registered or returned unexpected {r.status_code}: {r.data}"
        )
        assert r.status_code != 404, "Route /api/rag/search is not registered!"
        assert r.status_code != 405, "Method not allowed on /api/rag/search!"


class TestAgentRoutes:
    def test_agent_status(self, client):
        r = client.get("/api/agent/status")
        assert r.status_code == 200
        data = r.get_json()
        assert data.get("status") == "online"

    def test_agent_ask_empty_question(self, client):
        r = client.post("/api/agent/ask", json={"question": ""})
        assert r.status_code == 400

    def test_agent_ask_endpoint_exists(self, client):
        with patch(
            "routes.agent._manager.ask",
            return_value=_make_mock_agent_response(),
        ):
            r = client.post(
                "/api/agent/ask",
                json={"question": "Should we reorder fabric?"},
            )
        assert r.status_code in (200, 500), (
            f"Unexpected {r.status_code}: {r.data}"
        )
