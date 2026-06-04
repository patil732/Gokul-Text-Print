import os
import sys
import pandas as pd
import numpy as np

# Fallback for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from utils.logger import logger

def safe_read_csv(path):
    """
    Safely reads a CSV file, returning an empty DataFrame if the file 
    is missing, empty, or unparseable.
    """
    if not os.path.exists(path):
        return pd.DataFrame()
    
    try:
        # Check if file size is 0
        if os.path.getsize(path) == 0:
            return pd.DataFrame()
            
        df = pd.read_csv(path)
        return df
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()
    except Exception as e:
        logger.warning(f"Unexpected error reading {path}: {e}")
        return pd.DataFrame()

def run_data_processing():
    """
    Transforms raw ERP data into a cleaned dataset, resilient to empty or missing files.
    """
    try:
        # 1. Setup Directories
        os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True)

        # 2. Define File Paths
        sales_path = os.path.join(settings.RAW_DATA_DIR, "sales.csv")
        stock_path = os.path.join(settings.RAW_DATA_DIR, "stock.csv")
        prod_path = os.path.join(settings.RAW_DATA_DIR, "production.csv")
        output_path = os.path.join(settings.PROCESSED_DATA_DIR, "training_data.csv")

        # 3. Load Data Safely
        logger.info("Loading raw data datasets...")
        df_sales = safe_read_csv(sales_path)
        df_stock = safe_read_csv(stock_path)
        df_prod = safe_read_csv(prod_path)

        # 4. Critical Validation
        if df_sales.empty:
            logger.error("Sales data is empty or missing. Critical failure.")
            raise ValueError("Sales data is mandatory for processing.")

        # Log status of optional datasets
        if df_stock.empty:
            logger.warning("Stock data (stock.csv) is empty or missing.")
        if df_prod.empty:
            logger.warning("Production data (production.csv) is empty or missing.")

        # 5. Clean Sales Data
        logger.info("Cleaning sales data...")
        df_sales['transaction_date'] = pd.to_datetime(df_sales['transaction_date'], errors='coerce')
        df_sales = df_sales.dropna(subset=['transaction_date', 'grand_total'])
        df_sales = df_sales.drop_duplicates(subset=['name'])
        df_sales = df_sales.sort_values(by='transaction_date')

        # Standardize columns
        df_sales = df_sales.rename(columns={
            'transaction_date': 'date',
            'customer': 'product',
            'grand_total': 'sales'
        })

        # 6. Engineering Core Features
        logger.info("Processing features (Aggregations, Rolling Mean, Growth Rate)...")
        
        # Group by product and date
        df_main = df_sales.groupby(['date', 'product'])['sales'].sum().reset_index()
        df_main = df_main.sort_values(['product', 'date'])

        # sales_ma_3
        df_main['sales_ma_3'] = df_main.groupby('product')['sales'].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )

        # prev_sales (Lag 1)
        df_main['prev_sales'] = df_main.groupby('product')['sales'].shift(1)

        # growth_rate
        df_main['growth_rate'] = (df_main['sales'] - df_main['prev_sales']) / df_main['prev_sales']

        # Trend Feature
        df_main['trend'] = df_main['growth_rate'].apply(
            lambda x: 1 if x > 0.05 else (-1 if x < -0.05 else 0)
        )

        # 7. Integration with Stock and Production
        # Aggregate and join as features (filled with 0 if empty)
        if not df_stock.empty and 'actual_qty' in df_stock.columns:
            total_stock = df_stock['actual_qty'].sum()
            df_main['stock'] = total_stock
        else:
            logger.info("Setting stock to 0 (data empty).")
            df_main['stock'] = 0

        if not df_prod.empty and 'produced_qty' in df_prod.columns:
            total_prod = df_prod['produced_qty'].sum()
            df_main['production'] = total_prod
        else:
            logger.info("Setting production to 0 (data empty).")
            df_main['production'] = 0

        # 8. Final Cleaning (Infinity and NaNs)
        df_main = df_main.replace([np.inf, -np.inf], np.nan)
        df_main = df_main.fillna(0)

        # 9. Save Dataset
        df_main.to_csv(output_path, index=False)
        
        logger.info(f"Processing Complete: {len(df_main)} rows saved to {output_path}")

    except Exception as e:
        logger.error(f"Critical error in data processing pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    run_data_processing()
