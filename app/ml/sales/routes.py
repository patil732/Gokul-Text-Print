"""
app/ml/sales/routes.py
----------------------
Flask Blueprint exposing API endpoints for Sales ML model management:

  - POST /api/ml/sales/train      : Trigger sales model training pipeline
  - GET  /api/ml/sales/predict    : Run inference on query parameters
  - POST /api/ml/sales/predict    : Run inference on JSON body features
  - GET  /api/ml/sales/metrics    : Latest registered model evaluation metrics
  - POST /api/sales/forecast      : Generate 7 / 30 / 90-day sales forecast
"""

import time
from flask import Blueprint, jsonify, request
from app.ml.sales.sales_training import train_sales_model
from app.ml.sales.sales_prediction import predict_sales
from app.ml.sales.forecast import generate_forecast, reload_model
from app.ml.common.model_registry import get_latest_version
from utils.logger import logger

sales_ml_bp = Blueprint("sales_ml", __name__)

_VALID_PERIODS = {"7_days", "30_days", "90_days"}


@sales_ml_bp.route("/api/ml/sales/train", methods=["POST"])
def train_endpoint():
    """
    Trigger Sales ML model training.
    After training succeeds the forecast engine singleton is reloaded
    so the /api/sales/forecast endpoint immediately uses the new model.
    """
    try:
        data = request.get_json(silent=True) or {}
        version = data.get("version")
        result = train_sales_model(version=version)
        # Reload forecast engine so new weights are served immediately
        try:
            reload_model()
        except Exception as reload_exc:
            logger.warning(f"[sales_ml_bp] Could not reload forecast engine: {reload_exc}")
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


# --------------------------------------------------------------------------- #
# POST /api/sales/forecast
# --------------------------------------------------------------------------- #

@sales_ml_bp.route("/api/sales/forecast", methods=["POST"])
def forecast_endpoint():
    """
    Generate a sales forecast for 7, 30, or 90 calendar days.

    Request JSON
    ------------
    {
      "forecast_period": "7_days" | "30_days" | "90_days"
    }

    Optional additional keys are passed as baseline feature overrides
    (e.g. ``"sales": 25000.0``) and merged with the model defaults.

    Response JSON
    -------------
    {
      "status":           "success",
      "forecast_period":  str,
      "predicted_sales":  float,
      "growth_rate":      float,
      "confidence":       float,
      "model_type":       str,
      "version":          str,
      "elapsed_ms":       float
    }
    """
    t_request = time.perf_counter()
    try:
        payload = request.get_json(silent=True) or {}

        # ── Validate forecast_period ────────────────────────────────── #
        forecast_period = payload.get("forecast_period")
        if not forecast_period:
            return jsonify({
                "status":  "error",
                "message": "'forecast_period' is required.",
                "valid_values": sorted(_VALID_PERIODS),
            }), 400

        if forecast_period not in _VALID_PERIODS:
            return jsonify({
                "status":  "error",
                "message": (
                    f"Invalid forecast_period '{forecast_period}'. "
                    f"Must be one of: {sorted(_VALID_PERIODS)}"
                ),
                "valid_values": sorted(_VALID_PERIODS),
            }), 400

        # ── Optional baseline feature overrides ─────────────────────── #
        baseline_features = {
            k: float(v)
            for k, v in payload.items()
            if k != "forecast_period"
            and isinstance(v, (int, float))
        }

        # ── Run forecast ────────────────────────────────────────────── #
        result = generate_forecast(
            forecast_period   = forecast_period,
            baseline_features = baseline_features or None,
        )

        # ── Performance assertion (log warn if > 1 000 ms) ──────────── #
        total_ms = (time.perf_counter() - t_request) * 1000
        if total_ms > 1_000:
            logger.warning(
                f"[forecast_endpoint] Response time {total_ms:.1f}ms exceeds 1000ms SLA."
            )

        return jsonify({
            "status":          "success",
            "forecast_period": result["forecast_period"],
            "predicted_sales": result["predicted_sales"],
            "growth_rate":     result["growth_rate"],
            "confidence":      result["confidence"],
            "model_type":      result["model_type"],
            "version":         result["version"],
            "elapsed_ms":      result["elapsed_ms"],
        }), 200

    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except FileNotFoundError as exc:
        return jsonify({
            "status":  "error",
            "message": str(exc),
            "hint":    "Train a sales model first via POST /api/ml/sales/train",
        }), 503
    except Exception as exc:
        logger.error(f"[sales_ml_bp] Forecast endpoint failed: {exc}", exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500
