"""
app/dashboard/alerts/alert_engine.py
------------------------------------
Sprint 6 — Threshold-Based Operational Alert Engine.

Monitors business operations, ETL ingestion, and AI model health across 6 categories:
  1. Sales Drop / Spike (Growth beyond configurable % threshold)
  2. Low Stock / Overstock (From Sprint 3 inventory safety rules)
  3. ETL Failure (From Sprint 1 ETL pipeline logs)
  4. Model Failure (Training / inference runtime errors)
  5. AI Confidence Drop (Recommendation confidence below threshold)
  6. Missing Data (ETL row-count and schema sanity check failures)

Persists alerts to the SQLite ``alerts`` table and returns active alerts
sorted by priority (CRITICAL > HIGH > MEDIUM > LOW) then recency.
"""

from __future__ import annotations

from datetime import datetime
import os
import sys
from typing import Any, Dict, List, Optional
import uuid

# Ensure project root is on sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_DIR)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.db import get_db_connection
from utils.logger import logger

_PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


class AlertEngine:
    """
    Threshold-based monitoring and alert dispatch engine.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        sales_drop_threshold: float = -15.0,
        sales_spike_threshold: float = 25.0,
        low_stock_threshold: int = 50,
        confidence_min_threshold: float = 0.60,
        min_expected_etl_rows: int = 100,
    ) -> None:
        self._db_path = db_path
        self.sales_drop_threshold = sales_drop_threshold
        self.sales_spike_threshold = sales_spike_threshold
        self.low_stock_threshold = low_stock_threshold
        self.confidence_min_threshold = confidence_min_threshold
        self.min_expected_etl_rows = min_expected_etl_rows

    # ---------------------------------------------------------------------- #
    # 1. Anomaly Checkers (Pure Evaluation Logic)
    # ---------------------------------------------------------------------- #

    def check_sales_anomaly(self, growth_rate: float) -> Optional[Dict[str, Any]]:
        """
        Check for sales drop or surge beyond configured thresholds.
        """
        if growth_rate <= -25.0:
            return {
                "alert_type": "SALES_DROP",
                "priority": "CRITICAL",
                "message": f"Severe sales contraction detected: projected growth plummeted to {growth_rate:+.1f}%.",
            }
        elif growth_rate <= self.sales_drop_threshold:
            return {
                "alert_type": "SALES_DROP",
                "priority": "HIGH",
                "message": f"Significant sales drop detected: projected growth fell to {growth_rate:+.1f}%.",
            }
        elif growth_rate >= self.sales_spike_threshold:
            return {
                "alert_type": "SALES_SPIKE",
                "priority": "MEDIUM",
                "message": f"Notable sales spike detected: projected growth surged to {growth_rate:+.1f}%. Capacity adjustments recommended.",
            }
        return None

    def check_inventory_levels(
        self,
        low_stock_count: int = 0,
        overstock_count: int = 0,
        stock_health: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Check for low stock risks and overstock / dead stock accumulation.
        """
        alerts = []
        health_cap = (stock_health or "").strip().capitalize()

        # Low Stock / Stockout Risk
        if health_cap == "Critical" or low_stock_count >= 10:
            alerts.append({
                "alert_type": "LOW_STOCK",
                "priority": "CRITICAL",
                "message": f"Critical stockout risk: {low_stock_count} products have breached safety thresholds (< {self.low_stock_threshold} units).",
            })
        elif low_stock_count > 0 or health_cap == "Warning":
            alerts.append({
                "alert_type": "LOW_STOCK",
                "priority": "HIGH",
                "message": f"Low stock warning: {low_stock_count} products approaching reorder threshold.",
            })

        # Overstock / Dead Stock
        if overstock_count > 0:
            alerts.append({
                "alert_type": "OVERSTOCK",
                "priority": "MEDIUM",
                "message": f"Overstock alert: {overstock_count} items identified as dead stock with zero production velocity.",
            })

        return alerts

    def check_etl_status(
        self,
        etl_success: bool,
        error_msg: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for ETL ingestion pipeline failures.
        """
        if not etl_success:
            err_detail = f": {error_msg}" if error_msg else ""
            return {
                "alert_type": "ETL_FAILURE",
                "priority": "CRITICAL",
                "message": f"ETL ingestion pipeline failed{err_detail}. Operational datasets may be stale.",
            }
        return None

    def check_model_health(
        self,
        model_error: Optional[str] = None,
        accuracy: Optional[float] = None,
        model_name: str = "Forecast Model",
    ) -> Optional[Dict[str, Any]]:
        """
        Check for ML training or inference runtime/validation failures.
        """
        if model_error:
            return {
                "alert_type": "MODEL_FAILURE",
                "priority": "HIGH",
                "message": f"Model runtime failure for '{model_name}': {model_error}.",
            }
        if accuracy is not None and accuracy < 0.50:
            return {
                "alert_type": "MODEL_FAILURE",
                "priority": "HIGH",
                "message": f"Model performance degraded: '{model_name}' accuracy fell to {accuracy:.1%}.",
            }
        return None

    def check_ai_confidence(
        self,
        confidence: float,
        source: str = "recommendation",
    ) -> Optional[Dict[str, Any]]:
        """
        Check for AI recommendation or prediction confidence drops below threshold.
        """
        if confidence < 0.40:
            return {
                "alert_type": "AI_CONFIDENCE_DROP",
                "priority": "HIGH",
                "message": f"Severe AI confidence degradation: '{source}' confidence fell to {confidence:.1%} (below critical 40% threshold).",
            }
        elif confidence < self.confidence_min_threshold:
            return {
                "alert_type": "AI_CONFIDENCE_DROP",
                "priority": "MEDIUM",
                "message": f"AI confidence drop: '{source}' confidence is {confidence:.1%} (below {self.confidence_min_threshold:.1%} threshold).",
            }
        return None

    def check_missing_data(
        self,
        current_row_count: int,
        expected_min_rows: Optional[int] = None,
        missing_columns: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for row-count sanity check failures or missing required schema columns.
        """
        min_rows = expected_min_rows if expected_min_rows is not None else self.min_expected_etl_rows

        if current_row_count == 0:
            return {
                "alert_type": "MISSING_DATA",
                "priority": "CRITICAL",
                "message": "Data completeness failure: 0 records ingested during ETL run.",
            }
        if missing_columns and len(missing_columns) > 0:
            cols_str = ", ".join(missing_columns)
            return {
                "alert_type": "MISSING_DATA",
                "priority": "CRITICAL",
                "message": f"Schema sanity check failed: Missing required columns: {cols_str}.",
            }
        if current_row_count < min_rows:
            return {
                "alert_type": "MISSING_DATA",
                "priority": "HIGH",
                "message": f"Row count sanity check failed: Ingested {current_row_count} rows, below expected minimum of {min_rows} rows.",
            }
        return None

    # ---------------------------------------------------------------------- #
    # 2. Database Persistence & Querying
    # ---------------------------------------------------------------------- #

    def create_alert(
        self,
        alert_type: str,
        priority: str,
        message: str,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """
        Insert a new alert into the alerts table.
        """
        alert_id = str(uuid.uuid4())
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        p_upper = priority.strip().upper()

        conn = get_db_connection(self._db_path)
        try:
            conn.execute(
                """
                INSERT INTO alerts (alert_id, alert_type, priority, message, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (alert_id, alert_type.strip().upper(), p_upper, message, status.strip().upper(), created_at),
            )
            conn.commit()
        finally:
            conn.close()

        logger.info(f"[alert_engine] Generated alert [{p_upper}] {alert_type}: {message[:60]}")

        return {
            "alert_id": alert_id,
            "alert_type": alert_type.strip().upper(),
            "priority": p_upper,
            "message": message,
            "status": status.strip().upper(),
            "created_at": created_at,
        }

    def get_active_alerts(
        self,
        priority_filter: Optional[str] = None,
        status: str = "ACTIVE",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve alerts sorted by priority (CRITICAL > HIGH > MEDIUM > LOW)
        then recency (created_at DESC).
        """
        conn = get_db_connection(self._db_path)
        try:
            query = """
                SELECT alert_id, alert_type, priority, message, status, created_at
                FROM alerts
            """
            conditions = []
            params: List[Any] = []

            if status != "ALL":
                conditions.append("status = ?")
                params.append(status.strip().upper())

            if priority_filter:
                conditions.append("priority = ?")
                params.append(priority_filter.strip().upper())

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += """
                ORDER BY
                    CASE priority
                        WHEN 'CRITICAL' THEN 0
                        WHEN 'HIGH'     THEN 1
                        WHEN 'MEDIUM'   THEN 2
                        WHEN 'LOW'      THEN 3
                        ELSE 4
                    END,
                    created_at DESC
                LIMIT ?
            """
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as RESOLVED."""
        conn = get_db_connection(self._db_path)
        try:
            cur = conn.execute("UPDATE alerts SET status = 'RESOLVED' WHERE alert_id = ?", (alert_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def clear_alerts(self) -> None:
        """Clear all alerts (utility for testing)."""
        conn = get_db_connection(self._db_path)
        try:
            conn.execute("DELETE FROM alerts")
            conn.commit()
        finally:
            conn.close()

    # ---------------------------------------------------------------------- #
    # 3. Comprehensive Evaluation Runner
    # ---------------------------------------------------------------------- #

    def evaluate_all(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evaluate full operational posture against provided context or live system metrics.
        Persists and returns newly triggered alerts.
        """
        ctx = context or {}
        new_alerts: List[Dict[str, Any]] = []

        # 1. Sales Anomaly
        if "sales_growth" in ctx:
            alt = self.check_sales_anomaly(float(ctx["sales_growth"]))
            if alt:
                new_alerts.append(self.create_alert(**alt))

        # 2. Inventory Levels
        if "low_stock_count" in ctx or "overstock_count" in ctx or "stock_health" in ctx:
            alts = self.check_inventory_levels(
                low_stock_count=int(ctx.get("low_stock_count", 0)),
                overstock_count=int(ctx.get("overstock_count", 0)),
                stock_health=ctx.get("stock_health"),
            )
            for a in alts:
                new_alerts.append(self.create_alert(**a))

        # 3. ETL Status
        if "etl_success" in ctx:
            alt = self.check_etl_status(
                etl_success=bool(ctx["etl_success"]),
                error_msg=ctx.get("etl_error"),
            )
            if alt:
                new_alerts.append(self.create_alert(**alt))

        # 4. Model Health
        if "model_error" in ctx or "model_accuracy" in ctx:
            alt = self.check_model_health(
                model_error=ctx.get("model_error"),
                accuracy=ctx.get("model_accuracy"),
                model_name=ctx.get("model_name", "Forecast Model"),
            )
            if alt:
                new_alerts.append(self.create_alert(**alt))

        # 5. AI Confidence
        if "ai_confidence" in ctx:
            alt = self.check_ai_confidence(
                confidence=float(ctx["ai_confidence"]),
                source=ctx.get("confidence_source", "recommendation"),
            )
            if alt:
                new_alerts.append(self.create_alert(**alt))

        # 6. Missing Data
        if "row_count" in ctx:
            alt = self.check_missing_data(
                current_row_count=int(ctx["row_count"]),
                expected_min_rows=ctx.get("expected_min_rows"),
                missing_columns=ctx.get("missing_columns"),
            )
            if alt:
                new_alerts.append(self.create_alert(**alt))

        return new_alerts


def get_active_alerts(priority: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Convenience helper to retrieve active alerts."""
    engine = AlertEngine()
    return engine.get_active_alerts(priority_filter=priority, limit=limit)
