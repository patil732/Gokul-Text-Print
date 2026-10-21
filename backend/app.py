import os
import sys

# Ensure backend root directory is on sys.path
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from flask import Flask, jsonify, redirect, url_for, session, make_response
from flask_cors import CORS
from config.settings import Config
from utils.logger import logger
from routes.ceo import ceo_bp
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.documents import documents_bp
from database.db import init_db
from services.automation import start_scheduler

def create_app():
    """
    Application factory with Auth, RBAC, and Automated Background Tasks.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    # Sprint 8: secret key from environment (falls back to dev key only in local dev)
    app.secret_key = os.environ.get("SECRET_KEY", "gtp-dev-secret-change-in-production")

    # Sprint 8: Session security hardening
    _is_prod = os.environ.get("FLASK_ENV", "development") == "production"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    # In production (HTTPS), default to None so cross-site frontends (Vercel/Render/localhost) can send session cookies
    app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "None" if _is_prod else "Lax")
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "true" if _is_prod else "false").lower() == "true"
    # Optional: restrict session cookie to a custom domain (e.g. ".myapp.com")
    _cookie_domain = os.environ.get("SESSION_COOKIE_DOMAIN")
    if _cookie_domain:
        app.config["SESSION_COOKIE_DOMAIN"] = _cookie_domain

    # ── Sprint 7: CORS — allow Next.js frontend (dev + prod) ────────────── #
    # Only the allowed origins are configured here; no route logic is changed.
    _frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
    _cors_origins = [
        "http://localhost:3000",   # Next.js dev default
        "http://localhost:3001",   # alternate dev port
        _frontend_origin,          # env-override for prod
    ]
    CORS(
        app,
        origins=list(dict.fromkeys(_cors_origins)),  # deduplicate
        supports_credentials=True,
    )
    logger.info(f"[CORS] Allowed origins: {list(dict.fromkeys(_cors_origins))}")

    # ── Cross-site Set-Cookie hardening ────────────────────────────────────── #
    # Modern Chrome (≥ v127) blocks third-party cookies unless Partitioned is
    # present alongside SameSite=None; Secure.  Flask does not natively add
    # the Partitioned attribute, so we patch it in via after_request.
    if _is_prod:
        @app.after_request
        def _harden_set_cookie(response):
            """Append Partitioned attribute to session cookies for cross-site compat."""
            cookies = response.headers.getlist("Set-Cookie")
            if cookies:
                patched = []
                for cookie in cookies:
                    if "SameSite=None" in cookie and "Partitioned" not in cookie:
                        cookie += "; Partitioned"
                    patched.append(cookie)
                # Replace all Set-Cookie headers
                response.headers.pop("Set-Cookie")
                for c in patched:
                    response.headers.add("Set-Cookie", c)
            return response
    # ──────────────────────────────────────────────────────────────────────── #

    # Initialize Database
    init_db()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(ceo_bp)
    app.register_blueprint(admin_blueprint:=admin_bp)

    from app.ml.sales.routes import sales_ml_bp
    app.register_blueprint(sales_ml_bp)

    from app.ml.inventory.routes import inventory_ml_bp
    app.register_blueprint(inventory_ml_bp)

    # Sprint 4 — RAG Knowledge Engine: document management
    app.register_blueprint(documents_bp)

    # Sprint 4 Step 4 — RAG Knowledge Engine: semantic search
    from routes.rag import rag_bp
    app.register_blueprint(rag_bp)

    # Sprint 4 Step 5 — RAG Knowledge Engine: chat / Q&A
    from routes.chat import chat_bp
    app.register_blueprint(chat_bp)

    # Multi-Agent Executive Copilot
    from routes.agent import agent_bp
    app.register_blueprint(agent_bp)

    # Sprint 6 — Executive BI Dashboard: KPI Aggregation & Business Health
    from routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)


    # ── Health check ─────────────────────────────────────────────────── #
    # No auth, no DB, no LLM — always fast and reliable.
    @app.route('/health', methods=['GET'])
    def health():
        return make_response(jsonify({"status": "ok"}), 200)

    # ── Production error handling ────────────────────────────────────── #
    _is_prod = os.environ.get("FLASK_ENV", "development") == "production"

    @app.errorhandler(500)
    def internal_error(error):
        if _is_prod:
            return jsonify({"error": "Internal server error"}), 500
        return jsonify({"error": str(error)}), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.route('/')
    def index():
        if 'user' in session:
            # Sprint 8: use normalized role strings ('CEO', 'Admin') from ROLE_MAP
            if session.get('role', '').upper() == 'CEO':
                return redirect(url_for('ceo.ceo_view'))
            return redirect(url_for('admin.admin_view'))
        return redirect(url_for('auth.login'))

    # Start Automation Layer (Background Scheduler)
    if not app.config.get("TESTING") and not os.environ.get("PYTEST_CURRENT_TEST"):
        try:
            start_scheduler()
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")


    logger.info("Flask Application initialized with Automation Layer.")
    return app

app = create_app()

if __name__ == "__main__":
    _port = int(os.environ.get("PORT", 5001))
    _debug = os.environ.get("FLASK_DEBUG", "True").lower() not in ("false", "0", "no") \
             and os.environ.get("FLASK_ENV", "development") != "production"
    app.run(host="0.0.0.0", port=_port, debug=_debug)
