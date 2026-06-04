import os
import pandas as pd
from config.settings import settings
from utils.logger import logger

def run_analytics():
    """
    Analyzes processed ERP data to extract key business insights.
    
    Returns:
        dict: A dictionary containing core metrics, trends, and product summaries.
    """
    # 1. Load Data
    data_path = os.path.join(settings.PROCESSED_DATA_DIR, "training_data.csv")
    
    # Default values for empty/missing data
    default_results = {
        "total_sales": 0.0,
        "avg_sales": 0.0,
        "total_products": 0,
        "growth_trend": "stable",
        "top_product": "N/A",
        "low_stock_products": [],
        "product_summary": []
    }

    if not os.path.exists(data_path):
        logger.warning(f"Analytics source file missing at {data_path}. Returning defaults.")
        return default_results

    try:
        df = pd.read_csv(data_path)
        
        if df.empty:
            logger.warning("Processed dataset is empty. Returning default metrics.")
            return default_results

        logger.info(f"Running analytics on dataset with {len(df)} rows.")

        # 2. Core Metrics
        total_sales = float(df['sales'].sum())
        avg_sales = float(df['sales'].mean())
        total_products = int(df['product'].nunique())

        # 3. Growth Trend
        avg_growth = df['growth_rate'].mean()
        if avg_growth > 0:
            growth_trend = "increasing"
        elif avg_growth < 0:
            growth_trend = "decreasing"
        else:
            growth_trend = "stable"

        # 4. Top Product
        product_totals = df.groupby('product')['sales'].sum()
        top_product = str(product_totals.idxmax()) if not product_totals.empty else "N/A"

        # 5. Low Stock Detection (Threshold = 50)
        # Note: Stock might be duplicated per row, so we take the last known stock per product
        last_stock = df.groupby('product')['stock'].last()
        low_stock_mask = last_stock < 50
        low_stock_products = last_stock[low_stock_mask].index.tolist()

        # 6. Product Summary
        summary_df = df.groupby('product').agg({
            'sales': 'sum',
            'growth_rate': 'mean'
        }).reset_index()
        
        product_summary = summary_df.rename(columns={
            'sales': 'total_sales',
            'growth_rate': 'avg_growth_rate'
        }).to_dict(orient='records')

        # 7. Final Results
        results = {
            "total_sales": total_sales,
            "avg_sales": avg_sales,
            "total_products": total_products,
            "growth_trend": growth_trend,
            "top_product": top_product,
            "low_stock_products": low_stock_products,
            "product_summary": product_summary
        }

        logger.info(f"Analytics complete: Total Sales={total_sales:.2f}, Top Product={top_product}")
        return results

    except Exception as e:
        logger.error(f"Error during analytics computation: {str(e)}")
        return default_results

if __name__ == "__main__":
    # Test execution
    analytics = run_analytics()
    print(f"Analytics Result Summary:")
    print(f"Total Sales: {analytics['total_sales']}")
    print(f"Total Products: {analytics['total_products']}")
    print(f"Growth Trend: {analytics['growth_trend']}")
    print(f"Top Product: {analytics['top_product']}")
    print(f"Low Stock Count: {len(analytics['low_stock_products'])}")
