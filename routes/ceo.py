from flask import Blueprint, jsonify, render_template, session, redirect, url_for, request
from services.decision_pipeline import run_pipeline, simulate_scenario

ceo_bp = Blueprint('ceo', __name__)

@ceo_bp.route('/ceo', methods=['GET'])
def ceo_view():
    """Renders the CEO Dashboard HTML template if authorized."""
    if 'user' not in session or session.get('role') != 'ceo':
        return redirect(url_for('auth.login'))
    return render_template("ceo_dashboard.html")

@ceo_bp.route('/ceo/analytics', methods=['GET'])
def analytics_view():
    """Renders the Data Visualization page."""
    if 'user' not in session or session.get('role') != 'ceo':
        return redirect(url_for('auth.login'))
    return render_template("data_analytics.html")

@ceo_bp.route('/ceo/dashboard', methods=['GET'])
def ceo_dashboard():
    """API for the CEO providing enhanced intelligence insights."""
    if 'user' not in session or session.get('role') != 'ceo':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    result = run_pipeline()
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 500
        
    return jsonify({
        "status": "success",
        "data": result
    })

@ceo_bp.route('/ceo/simulate', methods=['POST'])
def simulate():
    """API to run What-if simulations for sales and stock changes."""
    if 'user' not in session or session.get('role') != 'ceo':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
    data = request.json
    changes = {
        "sales": float(data.get('sales_change', 0)) / 100,
        "stock": float(data.get('stock_change', 0)) / 100
    }
    
    result = simulate_scenario(changes)
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 500
        
    return jsonify({
        "status": "success",
        "simulation": result
    })

@ceo_bp.route('/ceo/analytics-data', methods=['GET'])
def analytics_data():
    """Fetches comprehensive data for visualization."""
    if 'user' not in session or session.get('role') != 'ceo':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    # Re-use parts of the pipeline logic to get rich data
    from services.decision_pipeline import fetch_live_data, prepare_live_features
    df_sales, df_stock = fetch_live_data()
    df_processed = prepare_live_features(df_sales, df_stock)
    
    # Prepare charts data
    print(f"DEBUG: df_sales columns: {df_sales.columns}")
    if not df_sales.empty:
        print(f"DEBUG: first row: {df_sales.iloc[0].to_dict()}")
    
    product_sales = df_sales.groupby('customer')['grand_total'].sum().sort_values(ascending=False).head(10).to_dict() if 'customer' in df_sales.columns else {}
    stock_status = df_stock.head(15).fillna(0).to_dict('records') 
    recent_txs = df_sales.head(20).fillna(0).to_dict('records')
    
    return jsonify({
        "status": "success",
        "sales_by_product": product_sales,
        "stock_inventory": stock_status,
        "recent_transactions": recent_txs,
        "processed_metrics": df_processed.tail(30).fillna(0).to_dict('records')
    })
