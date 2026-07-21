"""
app/ml/sales/routes.py
----------------------
Flask Blueprint exposing API endpoints for Sales ML model management:

  - POST /api/ml/sales/train   : Trigger sales model training pipeline
  - GET  /api/ml/sales/predict : Run inference on query parameters or default features
  - POST /api/ml/sales/predict : Run inference on JSON body features
  - GET  /api/ml/sales/metrics : Fetch latest registered sales model evaluation metrics
"""

from flask import Blueprint, jsonify, request
from app.ml.sales.sales_training import train_sales_model
from app.ml.sales.sales_prediction import predict_sales
from app.ml.common.model_registry import get_latest_version
from utils.logger import logger

sales_ml_bp = Blueprint("sales_ml", __name__)


@sales_ml_bp.route("/api/ml/sales/train", methods=["POST"])
def train_endpoint():
    """
    Trigger Sales ML model training.
    """
    try:
        data = request.get_json(silent=True) or {}
        version = data.get("version")
        result = train_sales_model(version=version)
        return jsonify({
            "status": "success",
            "message": "Sales model training complete.",
            "data": result,
        }), 200
    except Exception as exc:
        logger.error(f"[sales_ml_bp] Training endpoint failed: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@sales_ml_bp.route("/api/ml/sales/predict", methods=["GET", "POST"])
def predict_endpoint():
    """
    Run prediction using the latest registered Sales ML model.
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

        result = predict_sales(input_data)
        return jsonify(result), 200

    except Exception as exc:
        logger.error(f"[sales_ml_bp] Prediction endpoint failed: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@sales_ml_bp.route("/api/ml/sales/metrics", methods=["GET"])
def metrics_endpoint():
    """
    Retrieve evaluation metrics for the latest registered Sales model.
    """
    try:
        latest = get_latest_version("sales")
        if not latest:
            return jsonify({
                "status": "error",
                "message": "No registered sales model found. Please train a model first.",
            }), 4404 if False else 404

        return jsonify({
            "status": "success",
            "model_name": "sales",
            "version": latest.get("version"),
            "model_type": latest.get("model_type"),
            "accuracy": latest.get("accuracy"),
            "trained_at": latest.get("trained_at"),
            "metrics": latest.get("metrics"),
        }), 200

    except Exception as exc:
        logger.error(f"[sales_ml_bp] Metrics endpoint failed: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500
