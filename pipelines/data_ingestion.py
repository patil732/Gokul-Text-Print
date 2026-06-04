import os
import sys
from datetime import datetime, timedelta

# Fallback for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.frappe_client import FrappeClient
from config.settings import settings
from utils.logger import logger

def run_data_ingestion():
    """
    Optimized ERP ingestion pipeline with 5-year history and 100k row limit.
    Uses absolute paths from settings.
    """
    try:
        os.makedirs(settings.RAW_DATA_DIR, exist_ok=True)
        client = FrappeClient()
        
        # Calculate 5 years ago date
        five_years_ago = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
        logger.info(f"Applying 5-year date filter: >= {five_years_ago}")
        
        # 1. Sales Order
        sales_fields = ["name", "transaction_date", "customer", "grand_total", "status"]
        sales_filters = [["transaction_date", ">=", five_years_ago]]
        df_sales = client.fetch_data("Sales Order", fields=sales_fields, filters=sales_filters, max_records=100000)
        
        sales_out = os.path.join(settings.RAW_DATA_DIR, "sales.csv")
        df_sales.to_csv(sales_out, index=False)
        
        # 2. Stock (Bin) - No date filter if not available
        stock_fields = ["name", "item_code", "actual_qty", "warehouse"]
        df_stock = client.fetch_data("Bin", fields=stock_fields, max_records=100000)
        
        stock_out = os.path.join(settings.RAW_DATA_DIR, "stock.csv")
        df_stock.to_csv(stock_out, index=False)
        
        # 3. Work Order (Production) - Apply date filter
        prod_fields = ["name", "item", "qty", "produced_qty", "status"]
        prod_filters = [["creation", ">=", five_years_ago]]
        df_prod = client.fetch_data("Work Order", fields=prod_fields, filters=prod_filters, max_records=100000)
        
        prod_out = os.path.join(settings.RAW_DATA_DIR, "production.csv")
        df_prod.to_csv(prod_out, index=False)
        
        logger.info("--- Ingestion Summary ---")
        logger.info(f"Sales Records: {len(df_sales)}")
        logger.info(f"Stock Records: {len(df_stock)}")
        logger.info(f"Production Records: {len(df_prod)}")
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Ingestion Pipeline failed: {str(e)}")

if __name__ == "__main__":
    run_data_ingestion()
