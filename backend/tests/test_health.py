"""
tests/test_health.py
--------------------
CI smoke test for the /health endpoint.
No DB, ERP, LLM, or embedding calls are made.
All external services are mocked at import time via PYTEST_CURRENT_TEST + env vars.
"""

import os
import sys

# ── Set safe env vars before any app import ────────────────────────────── #
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("FLASK_DEBUG", "False")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///ci_test.db")
os.environ.setdefault("ERP_BASE_URL", "http://fake-erp.example.com")
os.environ.setdefault("ERP_API_KEY", "fake-erp-key")
os.environ.setdefault("ERP_API_SECRET", "fake-erp-secret")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini-key")
os.environ.setdefault("OPENAI_API_KEY", "fake-openai-key")

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from unittest.mock import MagicMock, patch
import pytest


# ── Patch heavy services before create_app is called ──────────────────── #
@pytest.fixture(scope="module")
def app():
    with (
        patch("services.automation.start_scheduler", return_value=None),
        patch("database.db.init_db", return_value=None),
        patch("sentence_transformers.SentenceTransformer", MagicMock()),
    ):
        import importlib.util, os as _os
        spec = importlib.util.spec_from_file_location(
            "app_entry",
            _os.path.join(_BACKEND, "app.py")
        )
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        flask_app = m.create_app()
        flask_app.config["TESTING"] = True
        yield flask_app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

    def test_health_returns_ok_json(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert data is not None, "Response is not JSON"
        assert data.get("status") == "ok", f"Expected status=ok, got {data}"

    def test_health_content_type(self, client):
        response = client.get("/health")
        assert "application/json" in response.content_type

    def test_health_does_not_require_auth(self, client):
        """Health endpoint must work without any session/cookie."""
        response = client.get("/health", headers={})
        assert response.status_code == 200
