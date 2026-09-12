"""
app/ml/sales/recommendation.py
--------------------------------
Sprint 2 — Sales Recommendation Rules Engine.

Calls forecast.generate_forecast() to obtain the latest growth_rate, then
applies a deterministic rules engine to map growth_rate → business decision.

Rules (in priority order)
--------------------------
  growth_rate >  15.0 %  →  "Increase Production"
  growth_rate < -10.0 %  →  "Reduce Inventory"
  otherwise              →  "Maintain Current Production"

Each recommendation includes:
  - decision   : str    — one of the three labels above
  - reason     : str    — human-readable explanation citing the growth_rate
  - confidence : float  — model confidence score [0.0 – 1.0] from the forecast

The recommendation AND its triggering forecast are persisted to the
``decision_history`` SQLite table (id, timestamp, decision, confidence, reason).

Public API
----------
get_recommendation(
    forecast_period: str = "30_days",
    baseline_features: dict = None,
) -> dict

    Returns::
        {
          "decision":        str,
          "reason":          str,
          "confidence":      float,
          "growth_rate":     float,
          "forecast_period": str,
          "predicted_sales": float,
          "model_type":      str,
          "version":         str,
          "stored_id":       int | None,   # decision_history row-id
        }

Thresholds can be overridden via config/model_config.yaml::

    sales:
      recommendation:
        increase_threshold:  15.0   # growth_rate % above which → Increase Production
        reduce_threshold:   -10.0   # growth_rate % below which → Reduce Inventory
        default_period:     30_days # forecast horizon used by GET /api/sales/recommendation
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

_MODULE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ML_DIR       = os.path.dirname(_MODULE_DIR)
_APP_DIR      = os.path.dirname(_ML_DIR)
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.ml.common.logger import get_ml_logger
from app.ml.common.model_loader import load_config
from app.ml.sales.forecast import generate_forecast

log = get_ml_logger("sales_recommendation")

# --------------------------------------------------------------------------- #
# Default thresholds (overridable via model_config.yaml)
# --------------------------------------------------------------------------- #

_DEFAULT_INCREASE_THRESHOLD: float =  15.0   # growth_rate % → Increase Production
_DEFAULT_REDUCE_THRESHOLD:   float = -10.0   # growth_rate % → Reduce Inventory
_DEFAULT_FORECAST_PERIOD:    str   = "30_days"

# Decision labels — kept as module constants so tests can import them
DECISION_INCREASE  = "Increase Production"
DECISION_REDUCE    = "Reduce Inventory"
DECISION_MAINTAIN  = "Maintain Current Production"


# --------------------------------------------------------------------------- #
# Threshold loader (cached per process; reads YAML once)
# --------------------------------------------------------------------------- #

_THRESHOLDS: Optional[Dict[str, Any]] = None


def _get_thresholds() -> Dict[str, Any]:
    """Read recommendation thresholds from model_config.yaml (cached)."""
    global _THRESHOLDS
    if _THRESHOLDS is not None:
        return _THRESHOLDS

    try:
        cfg = load_config()
        rec_cfg = cfg.get("sales", {}).get("recommendation", {})
        _THRESHOLDS = {
            "increase": float(rec_cfg.get("increase_threshold", _DEFAULT_INCREASE_THRESHOLD)),
            "reduce":   float(rec_cfg.get("reduce_threshold",   _DEFAULT_REDUCE_THRESHOLD)),
            "period":   str(rec_cfg.get("default_period",       _DEFAULT_FORECAST_PERIOD)),
        }
    except Exception:
        _THRESHOLDS = {
            "increase": _DEFAULT_INCREASE_THRESHOLD,
            "reduce":   _DEFAULT_REDUCE_THRESHOLD,
            "period":   _DEFAULT_FORECAST_PERIOD,
        }

    log.info(
        f"[recommendation] Thresholds loaded — "
        f"increase>{_THRESHOLDS['increase']}%  reduce<{_THRESHOLDS['reduce']}%  "
        f"default_period={_THRESHOLDS['period']}"
    )
    return _THRESHOLDS


# --------------------------------------------------------------------------- #
# Core rules engine
# --------------------------------------------------------------------------- #

def apply_rules(
    growth_rate: float,
    confidence:  float,
    increase_threshold: float = _DEFAULT_INCREASE_THRESHOLD,
    reduce_threshold:   float = _DEFAULT_REDUCE_THRESHOLD,
) -> Dict[str, Any]:
    """
    Apply the business rules to a growth_rate and return (decision, reason).

    Parameters
    ----------
    growth_rate         : float — period-over-period growth rate in %
    confidence          : float — model confidence [0.0 – 1.0] (from forecast)
    increase_threshold  : float — growth_rate % above which → Increase Production
    reduce_threshold    : float — growth_rate % below which → Reduce Inventory

    Returns
    -------
    dict  { "decision": str, "reason": str, "confidence": float }
    """
    gr = round(float(growth_rate), 4)
    cf = round(float(confidence),  4)

    if gr > increase_threshold:
        decision = DECISION_INCREASE
        reason = (
            f"Sales growth rate of {gr:+.2f}% exceeds the {increase_threshold:.1f}% "
            f"threshold. Increasing production capacity is recommended to meet "
            f"projected demand (model confidence: {cf:.0%})."
        )
    elif gr < reduce_threshold:
        decision = DECISION_REDUCE
        reason = (
            f"Sales growth rate of {gr:+.2f}% is below the {reduce_threshold:.1f}% "
            f"threshold, indicating a demand contraction. Reducing inventory levels "
            f"is recommended to avoid overstock (model confidence: {cf:.0%})."
        )
    else:
        decision = DECISION_MAINTAIN
        reason = (
            f"Sales growth rate of {gr:+.2f}% is within the normal operating range "
            f"({reduce_threshold:.1f}% – {increase_threshold:.1f}%). Maintaining "
            f"current production and inventory levels is recommended "
            f"(model confidence: {cf:.0%})."
        )

    log.info(
        f"[recommendation] growth_rate={gr:+.2f}%  "
        f"confidence={cf:.4f}  decision='{decision}'"
    )
    return {"decision": decision, "reason": reason, "confidence": cf}


# --------------------------------------------------------------------------- #
# Persistence — decision_history table
# --------------------------------------------------------------------------- #

def _store_recommendation(
    decision:        str,
    reason:          str,
    confidence:      float,
    forecast_payload: Dict[str, Any],
) -> Optional[int]:
    """
    Persist the recommendation and its triggering forecast to decision_history.

    The ``reason`` column stores the human-readable explanation; the full
    forecast snapshot is JSON-serialised and appended after a separator so
    it can be parsed later without a schema change.

    Returns the new row-id, or None if the write fails.
    """
    full_reason = (
        f"{reason}\n\n"
        f"[forecast_snapshot] {json.dumps(forecast_payload, default=str)}"
    )
    try:
        from database.db import get_db_connection
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO decision_history (timestamp, decision, confidence, reason)
            VALUES (?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                decision,
                float(confidence),
                full_reason,
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        log.info(
            f"[recommendation] Stored to decision_history — "
            f"id={row_id}  decision='{decision}'"
        )
        return row_id
    except Exception as exc:
        log.warning(f"[recommendation] Could not write to decision_history: {exc}")
        return None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def get_recommendation(
    forecast_period:   str                     = _DEFAULT_FORECAST_PERIOD,
    baseline_features: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Obtain a forecast, apply the rules engine, persist the result, and return
    a unified recommendation dict.

    Parameters
    ----------
    forecast_period   : "7_days" | "30_days" | "90_days"
    baseline_features : Optional feature overrides passed to generate_forecast().

    Returns
    -------
    dict::
        {
          "decision":        str,
          "reason":          str,
          "confidence":      float,
          "growth_rate":     float,
          "forecast_period": str,
          "predicted_sales": float,
          "model_type":      str,
          "version":         str,
          "stored_id":       int | None,
        }
    """
    thresholds = _get_thresholds()

    # Resolve period — accept None or empty string → use configured default
    period = forecast_period or thresholds["period"]

    # ── 1. Fetch forecast ────────────────────────────────────────────── #
    log.info(f"[recommendation] Requesting forecast for period='{period}'")
    forecast = generate_forecast(
        forecast_period   = period,
        baseline_features = baseline_features,
    )

    growth_rate  = float(forecast["growth_rate"])
    confidence   = float(forecast["confidence"])
    model_type   = str(forecast["model_type"])
    version      = str(forecast["version"])
    predicted_sales = float(forecast["predicted_sales"])

    # ── 2. Apply rules ───────────────────────────────────────────────── #
    rule_result = apply_rules(
        growth_rate        = growth_rate,
        confidence         = confidence,
        increase_threshold = thresholds["increase"],
        reduce_threshold   = thresholds["reduce"],
    )

    # ── 3. Persist ───────────────────────────────────────────────────── #
    forecast_snapshot = {
        "forecast_period":  period,
        "predicted_sales":  predicted_sales,
        "growth_rate":      growth_rate,
        "confidence":       confidence,
        "model_type":       model_type,
        "version":          version,
        "generated_at":     datetime.now().isoformat(),
    }
    try:
        stored_id = _store_recommendation(
            decision         = rule_result["decision"],
            reason           = rule_result["reason"],
            confidence       = confidence,
            forecast_payload = forecast_snapshot,
        )
    except Exception as exc:
        log.warning(f"[recommendation] Storage call raised unexpectedly: {exc}")
        stored_id = None

    try:
        from app.ml.common.prediction_service import log_sales_prediction_history
        log_sales_prediction_history(
            forecast_period=period,
            forecast_value=predicted_sales,
            recommendation=rule_result["decision"],
            confidence=confidence,
            model_version=version,
        )
    except Exception as exc:
        log.warning(f"[recommendation] Failed to write sales_prediction_history: {exc}")

    return {
        "decision":        rule_result["decision"],
        "reason":          rule_result["reason"],
        "confidence":      rule_result["confidence"],
        "growth_rate":     growth_rate,
        "forecast_period": period,
        "predicted_sales": predicted_sales,
        "model_type":      model_type,
        "version":         version,
        "stored_id":       stored_id,
    }


# --------------------------------------------------------------------------- #
# CLI smoke test
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    for period in ("7_days", "30_days", "90_days"):
        r = get_recommendation(forecast_period=period)
        print(
            f"{period:10s}  growth={r['growth_rate']:+.2f}%  "
            f"decision='{r['decision']}'  confidence={r['confidence']:.4f}"
        )
        print(f"           reason: {r['reason'][:80]}...")
        print()
