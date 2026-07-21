"""
app/ml/inventory/routes.py
--------------------------
Flask Blueprint exposing API endpoints for Inventory ML model management:

  - POST /api/ml/inventory/train   : Trigger inventory model training pipeline
  - GET  /api/ml/inventory/predict : Run inference on query parameters or default features
  - POST /api/ml/inventory/predict : Run inference on JSON body features
  - GET  /api/ml/inventory/metrics : Fetch latest registered inventory model evaluation metrics
"""

from flask import Blueprint, jsonify, request
from app.ml.inventory.inventory_training import train_inventory_model
from app.ml.inventory.inventory_prediction import predict_inventory
from app.ml.common.model_registry import get_latest_version
from utils.logger import logger

inventory_ml_bp = Blueprint("inventory_ml", __name__)


@inventory_ml_bp.route("/api/ml/inventory/train", methods=["POST"])
def train_endpoint():
    """
    Trigger Inventory ML model training.
    """
    try:
        data = request.get_json(silent=True) or {}
        version = data.get("version")
        result = train_inventory_model(version=version)
        return jsonify({
            "status": "success",
            "message": "Inventory model training complete.",
            "data": result,
        }), 200
    except Exception as exc:
        logger.error(f"[inventory_ml_bp] Training endpoint failed: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@inventory_ml_bp.route("/api/ml/inventory/predict", methods=["GET", "POST"])
def predict_endpoint():
    """
    Run prediction using the latest registered Inventory ML model.
    Accepts query parameters (GET) or JSON payload (POST).
    """
    try:
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
        else:
            payload = request.args.to_dict()

        # Convert numeric string parameters to float
        input_data = {}
        for k, v in payload.items():
            try:
                input_data[k] = float(v)
            except (ValueError, TypeError):
                input_data[k] = v

        result = predict_inventory(input_data)
        return jsonify(result), 200

    except Exception as exc:
        logger.error(f"[inventory_ml_bp] Prediction endpoint failed: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@inventory_ml_bp.route("/api/ml/inventory/metrics", methods=["GET"])
def metrics_endpoint():
    """
    Retrieve evaluation metrics for the latest registered Inventory model.
    """
    try:
        latest = get_latest_version("inventory")
        if not latest:
            return jsonify({
                "status": "error",
                "message": "No registered inventory model found. Please train a model first.",
            }), 404

        return jsonify({
            "status": "success",
            "model_name": "inventory",
            "version": latest.get("version"),
            "model_type": latest.get("model_type"),
            "accuracy": latest.get("accuracy"),
            "trained_at": latest.get("trained_at"),
            "metrics": latest.get("metrics"),
        }), 200

    except Exception as exc:
        logger.error(f"[inventory_ml_bp] Metrics endpoint failed: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500
