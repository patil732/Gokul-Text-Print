"""
routes/ceo.py
-------------
CEO Dashboard Flask Blueprint.

ML insight calls are routed through BusinessAILayer rather than importing
services.decision_pipeline directly.  This keeps the route layer thin and
ensures all AI calls go through the single orchestration point.

The legacy run_pipeline() / simulate_scenario() calls are preserved for
backward compatibility during the sprint-1 → sprint-2 transition:
  - /ceo/dashboard     uses BusinessAILayer.get_sales_insight() (new path)
  - /ceo/simulate      delegates to BusinessAILayer as well
  - /ceo/analytics-data keeps its direct ERP fetch (not an ML call)
"""

from flask import Blueprint, jsonify, render_template, session, redirect, url_for, request

from app.business_ai_layer import BusinessAILayer
from utils.logger           import logger

ceo_bp = Blueprint('ceo', __name__)

# One shared layer instance per process — lightweight, stateless
_ai = BusinessAILayer()


# --------------------------------------------------------------------------- #
# Page renders
# --------------------------------------------------------------------------- #

@ceo_bp.route('/ceo', methods=['GET'])
def ceo_view():
    """Render the CEO Dashboard HTML template (auth-gated)."""
    if 'user' not in session or session.get('role') != 'ceo':
        return redirect(url_for('auth.login'))
    return render_template("ceo_dashboard.html")


@ceo_bp.route('/ceo/analytics', methods=['GET'])
def analytics_view():
    """Render the Data Visualisation page (auth-gated)."""
    if 'user' not in session or session.get('role') != 'ceo':
        return redirect(url_for('auth.login'))
    return render_template("data_analytics.html")


# --------------------------------------------------------------------------- #
# API endpoints
# --------------------------------------------------------------------------- #

@ceo_bp.route('/ceo/dashboard', methods=['GET'])
def ceo_dashboard():
    """
    CEO intelligence feed.

    Fetches live ERP data, prepares features, runs the sales demand model
    via BusinessAILayer, and returns the full pipeline result as JSON.

    The response shape is kept identical to the previous run_pipeline()
    contract so the front-end needs no changes.
    """
    if 'user' not in session or session.get('role') != 'ceo':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        # Fetch live features from ERP (unchanged — this is data plumbing,
        # not model logic, so it stays in the pipeline service for now)
        from services.decision_pipeline import (
            fetch_live_data,
            prepare_live_features,
            get_explainable_reasons,
            generate_recommendations,
            generate_early_warnings,
        )
        from app.sales.model import load as load_sales_model, FEATURE_COLS
        import pandas as pd

        df_sales, df_stock = fetch_live_data()
        df = prepare_live_features(df_sales, df_stock)

        if df.empty:
            return jsonify({"status": "error", "message": "Insufficient data."}), 500

        # Build representative feature row (highest-sales product on latest date)
        last_date      = df['date'].max()
        daily_summary  = df[df['date'] == last_date]
        rep_idx        = daily_summary['sales'].idxmax()
        latest_row     = daily_summary.loc[[rep_idx]]
        latest_data    = latest_row.iloc[0]

        # ------------------------------------------------------------------ #
        # Route through BusinessAILayer
        # ------------------------------------------------------------------ #
        input_data = latest_row[FEATURE_COLS].iloc[0].to_dict()
        insight    = _ai.get_sales_insight(input_data)

        if insight["status"] == "error":
            return jsonify({"status": "error", "message": insight["message"]}), 500

        # Preserve the weighted-probability aggregation from run_pipeline()
        # for multi-product confidence (BusinessAILayer gives single-row proba;
        # the weighted version is computed here from the full daily batch).
        try:
            clf          = load_sales_model()
            predictions  = clf.predict(daily_summary[FEATURE_COLS])
            probs        = clf.predict_proba(daily_summary[FEATURE_COLS])
            sales_weights = daily_summary['sales'].values
            total_w       = sales_weights.sum()

            if total_w > 0:
                weighted_p1  = sum(
                    probs[i][1] * sales_weights[i]
                    for i in range(len(daily_summary))
                ) / total_w
                prediction   = 1 if weighted_p1 >= 0.5 else 0
                confidence_v = weighted_p1 if prediction == 1 else (1 - weighted_p1)
            else:
                prediction   = int(round(predictions.mean()))
                confidence_v = float(probs[:, prediction].mean())

            decision   = "Increase Production" if prediction == 1 else "Reduce Production"
            confidence = "High" if confidence_v > 0.7 else "Medium"
        except Exception:
            # Fall back to single-row result from BusinessAILayer
            decision   = insight["decision"]
            confidence = insight["confidence"]

        # Supplementary context (rules + SHAP — not model logic)
        reasons         = insight.get("reasons", [])
        recommendations = generate_recommendations(decision, latest_data)
        warnings        = generate_early_warnings(latest_data)

        # Date-range aggregates for dashboard cards
        available_dates = sorted(df['date'].unique())
        total_sales     = daily_summary['sales'].sum()
        total_stock     = daily_summary['stock'].mean()
        prev_sales      = (
            df[df['date'] == available_dates[-2]]['sales'].sum()
            if len(available_dates) > 1 else 0
        )
        company_growth = (
            (total_sales - prev_sales) / (prev_sales + 1)
            if prev_sales > 0 else 0
        )

        return jsonify({
            "status":       "success",
            "data": {
                "date":         str(latest_data['date']),
                "decision":     decision,
                "confidence":   confidence,
                "reasons":      reasons,
                "recommendations": recommendations,
                "warnings":     warnings,
                "total_records": len(df_sales),
                "history": {
                    "dates": df.groupby('date')['sales'].sum().tail(30)
                               .index.strftime('%Y-%m-%d').tolist(),
                    "sales": df.groupby('date')['sales'].sum().tail(30).tolist(),
                },
                "data": {
                    "sales":      float(total_sales),
                    "stock":      float(total_stock),
                    "trend":      int(latest_data['trend']),
                    "growth_rate": float(company_growth),
                    "sales_ma_3": float(daily_summary['sales_ma_3'].mean()),
                },
                # BusinessAILayer fields (additional — front-end can use these)
                "ai_layer": {
                    "domain":      insight["domain"],
                    "probability": insight["probability"],
                },
            }
        })

    except Exception as exc:
        logger.error(f"[ceo.dashboard] Unhandled error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@ceo_bp.route('/ceo/simulate', methods=['POST'])
def simulate():
    """
    What-if scenario simulation.

    Accepts JSON ``{sales_change: int, stock_change: int}`` (percentage values).
    Routes through BusinessAILayer with the adjusted feature values.
    """
    if 'user' not in session or session.get('role') != 'ceo':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.json or {}
    sales_pct = float(data.get('sales_change', 0)) / 100
    stock_pct = float(data.get('stock_change', 0)) / 100

    try:
        from services.decision_pipeline import (
            fetch_live_data,
            prepare_live_features,
        )
        from app.sales.model import FEATURE_COLS

        df_sales, df_stock = fetch_live_data()
        df = prepare_live_features(df_sales, df_stock)

        if df.empty:
            return jsonify({"status": "error", "message": "Insufficient data."}), 500

        last_date      = df['date'].max()
        daily_summary  = df[df['date'] == last_date]
        rep_idx        = daily_summary['sales'].idxmax()
        latest_row     = daily_summary.loc[[rep_idx]].copy()

        # Apply what-if adjustments
        latest_row['sales'] *= (1 + sales_pct)
        latest_row['stock'] *= (1 + stock_pct)
        latest_row['momentum']    = latest_row['sales'] - latest_row['sales_lag_3']
        latest_row['stock_ratio'] = latest_row['stock'] / (latest_row['sales'] + 1)

        # Route through BusinessAILayer
        input_data = latest_row[FEATURE_COLS].iloc[0].to_dict()
        insight    = _ai.get_sales_insight(input_data)

        if insight["status"] == "error":
            return jsonify({"status": "error", "message": insight["message"]}), 500

        # Determine change impact label
        impact = "Significant" if abs(sales_pct) > 0.2 else "Moderate"

        return jsonify({
            "status": "success",
            "simulation": {
                "decision":       insight["decision"],
                "confidence":     insight["confidence"],
                "probability":    insight["probability"],
                "impact":         impact,
                "risk_level":     "HIGH" if insight["prediction"] == 0 else "LOW",
                "recommendation": (
                    "Strategic shift detected"
                    if insight["prediction"] != _baseline_prediction(df, daily_summary, rep_idx, FEATURE_COLS)
                    else "Current strategy remains optimal"
                ),
                "reasons": insight.get("reasons", []),
                # BusinessAILayer meta
                "ai_layer": {"domain": insight["domain"]},
            }
        })

    except Exception as exc:
        logger.error(f"[ceo.simulate] Unhandled error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@ceo_bp.route('/ceo/analytics-data', methods=['GET'])
def analytics_data():
    """
    Rich chart data for the analytics page.

    This endpoint fetches ERP data for visualisation (not an ML call),
    so it does not go through BusinessAILayer.
    """
    if 'user' not in session or session.get('role') != 'ceo':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        from services.decision_pipeline import fetch_live_data, prepare_live_features

        df_sales, df_stock = fetch_live_data()
        df_processed       = prepare_live_features(df_sales, df_stock)

        product_sales = (
            df_sales.groupby('customer')['grand_total']
            .sum().sort_values(ascending=False).head(10).to_dict()
            if 'customer' in df_sales.columns else {}
        )
        stock_status  = df_stock.head(15).fillna(0).to_dict('records')
        recent_txs    = df_sales.head(20).fillna(0).to_dict('records')

        return jsonify({
            "status":               "success",
            "sales_by_product":     product_sales,
            "stock_inventory":      stock_status,
            "recent_transactions":  recent_txs,
            "processed_metrics":    df_processed.tail(30).fillna(0).to_dict('records'),
        })

    except Exception as exc:
        logger.error(f"[ceo.analytics_data] Unhandled error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _baseline_prediction(df, daily_summary, rep_idx, feature_cols) -> int:
    """
    Run a baseline prediction on the unmodified representative row.
    Used by /ceo/simulate to detect whether the scenario changes the decision.
    Returns 1 (Increase) or 0 (Reduce), defaulting to 0 on any error.
    """
    try:
        base_row     = daily_summary.loc[[rep_idx]]
        base_input   = base_row[feature_cols].iloc[0].to_dict()
        base_insight = _ai.get_sales_insight(base_input)
        return base_insight.get("prediction", 0)
    except Exception:
        return 0
