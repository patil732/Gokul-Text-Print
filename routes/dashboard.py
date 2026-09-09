"""
routes/dashboard.py
-------------------
Sprint 6 — Executive BI Dashboard API Blueprint.

Exposes high-level KPI aggregation and Business Health endpoints for the
executive decision layer:
  - GET /api/dashboard/kpis : Returns all 7 aggregated KPIs + Business Health Score,
                              cached in-memory for 30–60s to avoid hammering
                              underlying model and database services.
                              Strict response latency SLA: < 2.0 seconds.
"""

from __future__ import annotations

import io
import json
import time
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file, Response, session

from app.dashboard.kpi.kpi_service import aggregate_kpis
from utils.logger import logger

dashboard_bp = Blueprint("dashboard", __name__)

_LATENCY_SLA_MS = 2000.0


@dashboard_bp.route("/api/dashboard/kpis", methods=["GET"])
def get_dashboard_kpis():
    """
    Fetch comprehensive KPI metrics and composite Business Health Score.

    Query Parameters
    ----------------
    refresh : str, optional
        Set to 'true' or '1' to bypass in-memory cache and re-aggregate immediately.

    Response JSON
    -------------
    {
      "status": "success",
      "data": {
        "total_sales":              int,
        "revenue":                  float,
        "sales_growth":             float,
        "inventory_value":          float,
        "inventory_health":         str,
        "low_stock_products_count": int,
        "ai_recommendations_count": int,
        "business_health": {
          "score":           float,
          "status":          str,
          "sales_score":     float,
          "inventory_score": float,
          "alert_score":     float,
          "formula":         str
        },
        "timestamp":  str,
        "elapsed_ms": float,
        "cached":     bool
      }
    }
    """
    t_start = time.perf_counter()
    force_refresh = request.args.get("refresh", "").lower() in ("true", "1", "yes")

    try:
        data = aggregate_kpis(force_refresh=force_refresh)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # Record high-resolution request timing
        logger.info(
            f"[dashboard_bp] GET /api/dashboard/kpis responded in {elapsed_ms}ms "
            f"(cached={data.get('cached', False)})"
        )

        if elapsed_ms > _LATENCY_SLA_MS:
            logger.warning(
                f"[dashboard_bp] SLA breach warning: {elapsed_ms}ms exceeded {_LATENCY_SLA_MS}ms SLA ceiling."
            )

        # Attach request-level elapsed time
        data["elapsed_ms"] = elapsed_ms

        return jsonify({
            "status": "success",
            "data": data,
        }), 200

    except Exception as exc:
        logger.error(f"[dashboard_bp] Failed to aggregate KPIs: {exc}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve dashboard KPIs: {str(exc)}",
        }), 500


@dashboard_bp.route("/api/dashboard/analytics", methods=["GET"])
def get_dashboard_analytics():
    """
    Fetch chart-ready analytics data for Sales or Inventory domains.

    Query Parameters
    ----------------
    type : "sales" | "inventory"
        Analytics domain (default: "sales").
    range : "daily" | "weekly" | "monthly"
        Grouping cadence (default: "daily").
    start : str, optional
        Start date filter in YYYY-MM-DD format.
    end : str, optional
        End date filter in YYYY-MM-DD format.

    Response JSON
    -------------
    {
      "status": "success",
      "analytics_type": "sales" | "inventory",
      "range": "daily" | "weekly" | "monthly",
      "start_date": str | null,
      "end_date": str | null,
      "data": { ... chart-ready data ... },
      "elapsed_ms": float
    }
    """
    t_start = time.perf_counter()
    analytics_type = request.args.get("type", "sales").strip().lower()
    range_type = request.args.get("range", "daily").strip().lower()
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if analytics_type not in ("sales", "inventory"):
        return jsonify({
            "status": "error",
            "message": f"Invalid analytics type '{analytics_type}'. Must be 'sales' or 'inventory'.",
            "valid_types": ["sales", "inventory"],
        }), 400

    if range_type not in ("daily", "weekly", "monthly"):
        return jsonify({
            "status": "error",
            "message": f"Invalid range '{range_type}'. Must be 'daily', 'weekly', or 'monthly'.",
            "valid_ranges": ["daily", "weekly", "monthly"],
        }), 400

    try:
        if analytics_type == "sales":
            from app.dashboard.analytics.sales_analytics import get_sales_analytics
            analytics_data = get_sales_analytics(
                range_type=range_type,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            from app.dashboard.analytics.inventory_analytics import get_inventory_analytics
            analytics_data = get_inventory_analytics(
                range_type=range_type,
                start_date=start_date,
                end_date=end_date,
            )

        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[dashboard_bp] GET /api/dashboard/analytics (type={analytics_type}, "
            f"range={range_type}) completed in {elapsed_ms}ms"
        )

        return jsonify({
            "status": "success",
            "analytics_type": analytics_type,
            "range": range_type,
            "start_date": start_date,
            "end_date": end_date,
            "data": analytics_data,
            "elapsed_ms": elapsed_ms,
        }), 200

    except Exception as exc:
        logger.error(
            f"[dashboard_bp] Analytics retrieval failed for type='{analytics_type}': {exc}",
            exc_info=True,
        )
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve analytics data: {str(exc)}",
        }), 500


@dashboard_bp.route("/api/dashboard/recommendations", methods=["GET"])
def get_dashboard_recommendations():
    """
    Fetch aggregated, priority-sorted business recommendations across all
    intelligence domains (Sales, Inventory, Knowledge, Manager Agent).

    Query Parameters
    ----------------
    priority : "high" | "medium" | "low", optional
        Filter results by priority level.
    limit : int, optional
        Maximum number of recommendations to return (default: 10).

    Response JSON
    -------------
    {
      "status": "success",
      "count": int,
      "data": [
        {
          "recommendation": str,
          "reason": str,
          "confidence": float,
          "priority": "HIGH" | "MEDIUM" | "LOW",
          "source": "sales" | "inventory" | "knowledge" | "manager",
          "timestamp": str
        }
      ],
      "elapsed_ms": float
    }
    """
    t_start = time.perf_counter()
    priority_param = request.args.get("priority")
    limit_param = request.args.get("limit")

    limit_val = None
    if limit_param:
        try:
            limit_val = max(1, int(limit_param))
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": f"Invalid limit parameter '{limit_param}'. Must be a positive integer.",
            }), 400

    if priority_param and priority_param.lower() not in ("high", "medium", "low"):
        return jsonify({
            "status": "error",
            "message": f"Invalid priority '{priority_param}'. Must be 'high', 'medium', or 'low'.",
            "valid_priorities": ["high", "medium", "low"],
        }), 400

    try:
        from app.dashboard.recommendations.aggregator import aggregate_recommendations
        recs = aggregate_recommendations(priority_filter=priority_param, limit=limit_val)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

        logger.info(
            f"[dashboard_bp] GET /api/dashboard/recommendations returned {len(recs)} "
            f"items in {elapsed_ms}ms (filter={priority_param}, limit={limit_val})"
        )

        return jsonify({
            "status": "success",
            "count": len(recs),
            "data": recs,
            "elapsed_ms": elapsed_ms,
        }), 200

    except Exception as exc:
        logger.error(f"[dashboard_bp] Recommendation aggregation failed: {exc}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve recommendations: {str(exc)}",
        }), 500


@dashboard_bp.route("/api/reports/generate", methods=["GET"])
def generate_report_endpoint():
    """
    Generate downloadable executive BI report in PDF or CSV format.

    Query Parameters
    ----------------
    type : "daily" | "weekly" | "monthly" | "custom", optional (default: "daily")
        Report cadence and aggregation scope.
    format : "pdf" | "csv", optional (default: "pdf")
        Export document format.
    start : str, optional (YYYY-MM-DD)
        Custom range start date.
    end : str, optional (YYYY-MM-DD)
        Custom range end date.

    Returns
    -------
    Downloadable attachment file (application/pdf or text/csv).
    """
    t_start = time.perf_counter()
    report_type = request.args.get("type", "daily").strip().lower()
    export_format = request.args.get("format", "pdf").strip().lower()
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    valid_types = ["daily", "weekly", "monthly", "custom"]
    if report_type not in valid_types:
        return jsonify({
            "status": "error",
            "message": f"Invalid report type '{report_type}'. Must be one of: {valid_types}",
            "valid_types": valid_types,
        }), 400

    valid_formats = ["pdf", "csv"]
    if export_format not in valid_formats:
        return jsonify({
            "status": "error",
            "message": f"Invalid export format '{export_format}'. Must be one of: {valid_formats}",
            "valid_formats": valid_formats,
        }), 400

    try:
        from app.dashboard.reports import (
            build_daily_report,
            build_weekly_report,
            build_monthly_report,
            build_custom_report,
            export_pdf,
            export_csv,
        )

        if report_type == "daily":
            report_data = build_daily_report(target_date=end_date or start_date)
        elif report_type == "weekly":
            report_data = build_weekly_report(end_date=end_date)
        elif report_type == "monthly":
            report_data = build_monthly_report()
        else:
            report_data = build_custom_report(start_date=start_date, end_date=end_date)

        date_tag = datetime.now().strftime("%Y%m%d")
        filename_base = f"executive_report_{report_type}_{date_tag}"

        if export_format == "pdf":
            pdf_bytes = export_pdf(report_data)
            elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
            logger.info(
                f"[dashboard_bp] Generated {report_type} PDF ({len(pdf_bytes)} bytes) in {elapsed_ms}ms"
            )
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"{filename_base}.pdf",
            )
        else:
            csv_content = export_csv(report_data)
            elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
            logger.info(
                f"[dashboard_bp] Generated {report_type} CSV ({len(csv_content)} chars) in {elapsed_ms}ms"
            )
            return Response(
                csv_content,
                mimetype="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename_base}.csv"',
                    "Content-Type": "text/csv; charset=utf-8",
                },
            )

    except Exception as exc:
        logger.error(f"[dashboard_bp] Report generation failed for type='{report_type}': {exc}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to generate report: {str(exc)}",
        }), 500


@dashboard_bp.route("/api/dashboard/alerts", methods=["GET"])
def get_dashboard_alerts():
    """
    Fetch active operational alerts sorted by priority (CRITICAL > HIGH > MEDIUM > LOW)
    then recency (created_at DESC).

    Query Parameters
    ----------------
    status : "ACTIVE" | "RESOLVED" | "ALL", optional (default: "ACTIVE")
    priority : "CRITICAL" | "HIGH" | "MEDIUM" | "LOW", optional
    limit : int, optional (default: 20)

    Response JSON
    -------------
    {
      "status": "success",
      "count": int,
      "data": [
        {
          "alert_id": str,
          "alert_type": str,
          "priority": str,
          "message": str,
          "status": str,
          "created_at": str
        }
      ],
      "elapsed_ms": float
    }
    """
    t_start = time.perf_counter()
    status_param = request.args.get("status", "ACTIVE").strip().upper()
    priority_param = request.args.get("priority")
    limit_param = request.args.get("limit")

    limit_val = 20
    if limit_param:
        try:
            limit_val = max(1, int(limit_param))
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": f"Invalid limit '{limit_param}'. Must be a positive integer.",
            }), 400

    valid_priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    if priority_param and priority_param.strip().upper() not in valid_priorities:
        return jsonify({
            "status": "error",
            "message": f"Invalid priority '{priority_param}'. Must be one of: {valid_priorities}",
            "valid_priorities": valid_priorities,
        }), 400

    try:
        from app.dashboard.alerts import AlertEngine
        engine = AlertEngine()
        alerts = engine.get_active_alerts(
            priority_filter=priority_param,
            status=status_param,
            limit=limit_val,
        )

        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        logger.info(
            f"[dashboard_bp] GET /api/dashboard/alerts returned {len(alerts)} alerts "
            f"in {elapsed_ms}ms (status={status_param}, priority={priority_param})"
        )

        return jsonify({
            "status": "success",
            "count": len(alerts),
            "data": alerts,
            "elapsed_ms": elapsed_ms,
        }), 200

    except Exception as exc:
        logger.error(f"[dashboard_bp] Failed to retrieve alerts: {exc}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve alerts: {str(exc)}",
        }), 500


# --------------------------------------------------------------------------- #
# Dashboard Personalization & User Preferences (Sprint 6 V2)
# --------------------------------------------------------------------------- #

DEFAULT_PREFERENCES = {
    "theme": "light",
    "pinned_widgets": ["widget-alerts", "widget-kpis"],
    "widget_order": [
        "widget-alerts",
        "widget-kpis",
        "widget-charts",
        "widget-recommendations",
        "widget-chat",
        "widget-specialist-engines",
    ],
    "chart_filters": {
        "sales_range": "monthly",
        "inventory_range": "monthly",
        "start_date": "",
        "end_date": "",
    },
    "collapsed_sections": [],
}


@dashboard_bp.route("/api/dashboard/preferences", methods=["GET"])
def get_dashboard_preferences():
    """
    Retrieve personalized dashboard preferences for a given user.
    """
    user_id = request.args.get("user") or session.get("user") or "ceo"
    try:
        from database.db import get_db_connection
        conn = get_db_connection()
        row = conn.execute(
            "SELECT preferences, updated_at FROM dashboard_preferences WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        if row:
            try:
                prefs = json.loads(row["preferences"])
            except Exception:
                prefs = dict(DEFAULT_PREFERENCES)
            return jsonify({
                "status": "success",
                "user": user_id,
                "data": prefs,
                "updated_at": row["updated_at"]
            }), 200
        else:
            return jsonify({
                "status": "success",
                "user": user_id,
                "data": dict(DEFAULT_PREFERENCES),
                "is_default": True
            }), 200

    except Exception as exc:
        logger.error(f"[dashboard_bp] Failed to get preferences for user='{user_id}': {exc}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to get preferences: {str(exc)}"
        }), 500


@dashboard_bp.route("/api/dashboard/preferences", methods=["POST"])
def save_dashboard_preferences():
    """
    Persist personalized dashboard preferences for a user.
    """
    if request.data and request.get_json(silent=True) is None:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON payload."
        }), 400

    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user") or request.args.get("user") or session.get("user") or "ceo"

    prefs_data = payload.get("preferences") if "preferences" in payload else payload
    if isinstance(prefs_data, dict) and "user" in prefs_data and "preferences" not in payload:
        prefs_data = {k: v for k, v in prefs_data.items() if k != "user"}

    if not isinstance(prefs_data, dict):
        return jsonify({
            "status": "error",
            "message": "Preferences payload must be a JSON object."
        }), 400

    try:
        from database.db import get_db_connection
        conn = get_db_connection()

        row = conn.execute(
            "SELECT preferences FROM dashboard_preferences WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        merged_prefs = dict(DEFAULT_PREFERENCES)
        if row:
            try:
                merged_prefs.update(json.loads(row["preferences"]))
            except Exception:
                pass
        merged_prefs.update(prefs_data)

        prefs_json = json.dumps(merged_prefs)
        conn.execute(
            """
            INSERT INTO dashboard_preferences (user_id, preferences, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                preferences = excluded.preferences,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, prefs_json)
        )
        conn.commit()
        conn.close()

        logger.info(f"[dashboard_bp] Saved dashboard preferences for user='{user_id}'")
        return jsonify({
            "status": "success",
            "user": user_id,
            "data": merged_prefs
        }), 200

    except Exception as exc:
        logger.error(f"[dashboard_bp] Failed to save preferences for user='{user_id}': {exc}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Failed to save preferences: {str(exc)}"
        }), 500


