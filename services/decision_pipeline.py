import os
import joblib
import pandas as pd
import numpy as np
import shap
from datetime import datetime, timedelta
from config.settings import settings
from services.frappe_client import FrappeClient
from agents.monitoring_agent import get_alerts
from utils.logger import logger

def fetch_live_data():
    """Fetches real-time data from ERP API for Sales and Stock."""
    client = FrappeClient()
    date_threshold = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
    sales_filters = [["transaction_date", ">=", date_threshold]]
    sales_fields = ["name", "transaction_date", "customer", "grand_total"]
    
    df_sales = client.fetch_data("Sales Order", fields=sales_fields, filters=sales_filters)
    stock_fields = ["item_code", "actual_qty", "warehouse"]
    df_stock = client.fetch_data("Bin", fields=stock_fields, max_records=2000)
    
    return df_sales, df_stock

def prepare_live_features(df_sales, df_stock):
    """Applies identical feature engineering used in ML training."""
    if df_sales.empty:
        return pd.DataFrame()

    df_sales['date'] = pd.to_datetime(df_sales['transaction_date'])
    df_sales = df_sales.rename(columns={'customer': 'product', 'grand_total': 'sales'})
    df = df_sales.groupby(['date', 'product'])['sales'].sum().reset_index()
    df = df.sort_values(by=['product', 'date'])

    df['sales_lag_1'] = df.groupby('product')['sales'].shift(1)
    df['sales_lag_2'] = df.groupby('product')['sales'].shift(2)
    df['sales_lag_3'] = df.groupby('product')['sales'].shift(3)
    df['sales_ma_3'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=3).mean())
    df['sales_ma_7'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=7).mean())
    df['sales_ma_14'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=14).mean())
    df['sales_std_7'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=7).std())
    df['momentum'] = df['sales'] - df['sales_lag_3']
    df['prev_sales'] = df.groupby('product')['sales'].shift(1)
    df['growth_rate'] = (df['sales'] - df['prev_sales']) / (df['prev_sales'] + 1)
    df['trend'] = df['growth_rate'].apply(lambda x: 1 if x > 0.05 else (-1 if x < -0.05 else 0))

    total_stock = df_stock['actual_qty'].sum() if not df_stock.empty else 0
    df['stock'] = total_stock
    df['stock_ratio'] = df['stock'] / (df['sales'] + 1)
    
    return df.fillna(0)

def generate_recommendations(decision, row):
    """Rule-based smart recommendations for executive action."""
    recs = []
    if decision == "Increase Production":
        recs.append("Scale up manufacturing by 15-20% immediately.")
        recs.append("Procure additional raw materials to prevent shortages.")
    else:
        recs.append("Optimize current inventory levels and pause non-critical production.")
        recs.append("Focus on high-margin products during this slowdown.")
        
    if row['stock'] < 500:
        recs.append("CRITICAL: Restock inventory urgently to avoid stockouts.")
    if row['growth_rate'] > 0.15:
        recs.append("Strategy: Prepare for a significant demand surge.")
    
    return recs

def generate_early_warnings(row):
    """Predictive warnings based on time-series indicators."""
    warnings = []
    if row['momentum'] < 0:
        warnings.append("Sales Momentum: Recent indicators suggest a potential decline soon.")
    if row['stock_ratio'] < 0.15:
        warnings.append("Supply Chain Risk: Inventory levels are critically low relative to sales.")
    if row['sales_ma_7'] < row['sales_ma_14']:
        warnings.append("Market Sentiment: Demand trend is weakening compared to the bi-weekly average.")
    
    return warnings

def simulate_scenario(changes):
    """
    Predicts the impact of 'What-if' changes on the AI decision.
    changes = {'sales': float, 'stock': float} where float is % change (e.g., 0.1 for +10%)
    """
    try:
        df_sales, df_stock = fetch_live_data()
        df = prepare_live_features(df_sales, df_stock)
        if df.empty: return {"error": "Insufficient data."}
        
        latest_row = df.iloc[-1:].copy()
        
        # Apply Simulations
        latest_row['sales'] *= (1 + changes.get('sales', 0))
        latest_row['stock'] *= (1 + changes.get('stock', 0))
        
        # Recalculate derived features
        latest_row['momentum'] = latest_row['sales'] - latest_row['sales_lag_3']
        latest_row['stock_ratio'] = latest_row['stock'] / (latest_row['sales'] + 1)
        
        model_path = os.path.join(settings.BASE_DIR, "models", "decision_model.pkl")
        model = joblib.load(model_path)
        features = ["sales", "sales_lag_1", "sales_lag_2", "sales_lag_3", "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7", "momentum", "trend", "stock_ratio"]
        
        prediction = model.predict(latest_row[features])[0]
        decision = "Increase Production" if prediction == 1 else "Reduce Production"
        
        return {
            "decision": decision,
            "impact": "Significant" if abs(changes.get('sales', 0)) > 0.2 else "Moderate",
            "risk_level": "HIGH" if decision == "Reduce Production" else "LOW",
            "recommendation": "Strategic shift detected" if prediction != model.predict(df.iloc[-1:][features])[0] else "Current strategy remains optimal"
        }
    except Exception as e:
        return {"error": str(e)}

def get_explainable_reasons(model, row, features):
    """Uses SHAP to identify top 3 drivers."""
    mapping = {"sales": "current sales", "sales_ma_7": "7-day trend", "momentum": "demand momentum", "stock_ratio": "inventory efficiency"}
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(row[features])
        vals = (shap_values[1] if isinstance(shap_values, list) else shap_values).flatten()
        top_indices = np.argsort(np.abs(vals))[-3:][::-1]
        return [f"{mapping.get(features[i], features[i].replace('_', ' ')).capitalize()} is {'positively' if vals[i] > 0 else 'negatively'} impacting the forecast." for i in top_indices]
    except: return ["Historical sales trajectory is the primary driver."]

def run_pipeline():
    """Unified CEO Intelligence Pipeline."""
    try:
        df_sales, df_stock = fetch_live_data()
        df = prepare_live_features(df_sales, df_stock)
        if df.empty: return {"error": "Insufficient data."}

        model_path = os.path.join(settings.BASE_DIR, "models", "decision_model.pkl")
        model = joblib.load(model_path)
        
        latest_row = df.iloc[-1:]
        last_date = latest_row.iloc[0]['date']
        
        # Find the actual previous date in the dataset
        available_dates = sorted(df['date'].unique())
        if len(available_dates) > 1:
            prev_date = available_dates[-2]
            prev_summary = df[df['date'] == prev_date]
            total_prev_sales = prev_summary['sales'].sum()
        else:
            total_prev_sales = 0
            
        # Aggregates for the dashboard cards
        daily_summary = df[df['date'] == last_date]
        total_sales = daily_summary['sales'].sum()
        
        # Company-wide Growth Rate
        company_growth = (total_sales - total_prev_sales) / (total_prev_sales + 1) if total_prev_sales > 0 else 0
        total_stock = daily_summary['stock'].mean()
        
        features = ["sales", "sales_lag_1", "sales_lag_2", "sales_lag_3", "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7", "momentum", "trend", "stock_ratio"]
        
        # Prediction on the specific latest record
        prediction = model.predict(latest_row[features])[0]
        probs = model.predict_proba(latest_row[features])[0]
        decision = "Increase Production" if prediction == 1 else "Reduce Production"
        
        latest_data = latest_row.iloc[0]
        reasons = get_explainable_reasons(model, latest_row, features)
        recommendations = generate_recommendations(decision, latest_data)
        warnings = generate_early_warnings(latest_data)
        
        return {
            "date": str(latest_data['date']),
            "decision": decision,
            "confidence": "High" if probs[prediction] > 0.7 else "Medium",
            "reasons": reasons,
            "recommendations": recommendations,
            "warnings": warnings,
            "total_records": len(df_sales),
            "history": {"dates": df.groupby('date')['sales'].sum().tail(30).index.strftime('%Y-%m-%d').tolist(), 
                        "sales": df.groupby('date')['sales'].sum().tail(30).tolist()},
            "data": {
                "sales": float(total_sales), 
                "stock": float(total_stock),
                "trend": int(latest_data['trend']), 
                "growth_rate": float(company_growth),
                "sales_ma_3": float(daily_summary['sales_ma_3'].mean())
            }
        }
    except Exception as e:
        logger.error(f"Pipeline Failed: {str(e)}")
        return {"error": str(e)}
