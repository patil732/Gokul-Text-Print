"""
routes/admin.py
---------------
Admin Monitoring Flask Blueprint.

Model-artefact paths are sourced from app/config.cfg rather than being
hardcoded.  The admin monitor endpoint now reports the status of the new
sales and inventory artefacts (managed by BusinessAILayer) instead of
the legacy decision_model.pkl.
"""

import os
import pandas as pd
from flask import Blueprint, jsonify, render_template, session, redirect, url_for, request

from app.config   import cfg
from database.db  import get_db_connection
from services.automation import automated_job
from utils.logger import logger

admin_bp = Blueprint('admin', __name__)


# --------------------------------------------------------------------------- #
# Page render
# --------------------------------------------------------------------------- #

@admin_bp.route('/admin', methods=['GET'])
def admin_view():
    """Render the Admin Monitoring HTML template (auth-gated)."""
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template("admin_dashboard.html")


# --------------------------------------------------------------------------- #
# API endpoints
# --------------------------------------------------------------------------- #

@admin_bp.route('/admin/monitor', methods=['GET'])
def admin_monitor():
    """
    System health check for the admin dashboard.

    Reports the status of both ML artefacts managed by BusinessAILayer:
      - Sales model      (cfg.SALES_MODEL_PATH)
      - Inventory model  (cfg.INVENTORY_MODEL_PATH)
    And the status of the processed data files for each domain.
    """
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    # Model artefact presence — sourced from app/config.cfg (no hardcoded paths)
    sales_model_loaded     = os.path.exists(cfg.SALES_MODEL_PATH)
    inventory_model_loaded = os.path.exists(cfg.INVENTORY_MODEL_PATH)
    sales_shap_loaded      = os.path.exists(cfg.SALES_SHAP_PATH)
    inventory_shap_loaded  = os.path.exists(cfg.INVENTORY_SHAP_PATH)

    # Processed data status
    sales_data_path     = os.path.join(cfg.PROCESSED_DATA_DIR, "sales_training_data.csv")
    inventory_data_path = os.path.join(cfg.PROCESSED_DATA_DIR, "inventory_training_data.csv")

    sales_rows,     sales_last_updated     = _csv_stats(sales_data_path)
    inventory_rows, inventory_last_updated = _csv_stats(inventory_data_path)

    return jsonify({
        "status": "success",
        "system": {
            "api_status": "running",
            "models": {
                "sales": {
                    "model_loaded": sales_model_loaded,
                    "shap_loaded":  sales_shap_loaded,
                    "model_path":   cfg.SALES_MODEL_PATH,
                    "shap_path":    cfg.SALES_SHAP_PATH,
                },
                "inventory": {
                    "model_loaded": inventory_model_loaded,
                    "shap_loaded":  inventory_shap_loaded,
                    "model_path":   cfg.INVENTORY_MODEL_PATH,
                    "shap_path":    cfg.INVENTORY_SHAP_PATH,
                },
            },
            "data": {
                "sales": {
                    "rows":         sales_rows,
                    "last_updated": sales_last_updated,
                },
                "inventory": {
                    "rows":         inventory_rows,
                    "last_updated": inventory_last_updated,
                },
            },
        }
    })


@admin_bp.route('/admin/users', methods=['GET'])
def list_users():
    """Return a list of all registered users (admin only)."""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    conn  = get_db_connection()
    users = conn.execute('SELECT id, username, role FROM users').fetchall()
    conn.close()

    return jsonify({
        "status": "success",
        "users":  [dict(u) for u in users],
    })


@admin_bp.route('/admin/sync-now', methods=['POST'])
def sync_now():
    """Manually trigger the background ERP data ingestion job."""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        automated_job()
        return jsonify({
            "status":  "success",
            "message": "Data synchronization triggered successfully.",
        })
    except Exception as exc:
        logger.error(f"[admin.sync_now] Job failed: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _csv_stats(path: str) -> tuple[int, str]:
    """
    Return (row_count, last_updated_date) for a processed CSV.
    Returns (0, "N/A") if the file is absent or unreadable.
    """
    if not os.path.exists(path):
        return 0, "N/A"
    try:
        df = pd.read_csv(path)
        rows         = len(df)
        last_updated = (
            str(df['date'].max())
            if not df.empty and 'date' in df.columns
            else "N/A"
        )
        return rows, last_updated
    except Exception:
        return 0, "N/A"
