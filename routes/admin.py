import os
import pandas as pd
from flask import Blueprint, jsonify, render_template, session, redirect, url_for, request
from config.settings import settings
from database.db import get_db_connection
from services.automation import automated_job

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', methods=['GET'])
def admin_view():
    """Renders the Admin Monitoring HTML template if authorized."""
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template("admin_dashboard.html")

@admin_bp.route('/admin/monitor', methods=['GET'])
def admin_monitor():
    """Role-based API for Admin to monitor system health. Requires admin role."""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    model_path = os.path.join(settings.BASE_DIR, "models", "decision_model.pkl")
    data_path = os.path.join(settings.PROCESSED_DATA_DIR, "training_data.csv")
    
    # 1. Check Model Status
    model_loaded = os.path.exists(model_path)
    
    # 2. Check Data Status
    data_rows = 0
    last_updated = "N/A"
    
    if os.path.exists(data_path):
        try:
            df = pd.read_csv(data_path)
            data_rows = len(df)
            if not df.empty and 'date' in df.columns:
                last_updated = str(df['date'].max())
        except Exception:
            pass
            
    return jsonify({
        "status": "success",
        "system": {
            "model_loaded": model_loaded,
            "data_rows": data_rows,
            "last_updated": last_updated,
            "api_status": "running"
        }
    })

@admin_bp.route('/admin/users', methods=['GET'])
def list_users():
    """Returns a list of all registered users."""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, role FROM users').fetchall()
    conn.close()
    
    return jsonify({
        "status": "success",
        "users": [dict(u) for u in users]
    })

@admin_bp.route('/admin/sync-now', methods=['POST'])
def sync_now():
    """Manually triggers the background data ingestion job."""
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    try:
        automated_job()
        return jsonify({"status": "success", "message": "Data synchronization triggered successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
