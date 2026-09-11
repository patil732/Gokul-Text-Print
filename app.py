import os
from flask import Flask, jsonify, redirect, url_for, session
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
    app.secret_key = "super_secret_key"

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


    @app.route('/')
    def index():
        if 'user' in session:
            if session['role'] == 'ceo':
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
    app.run(host="0.0.0.0", port=5001, debug=True)
