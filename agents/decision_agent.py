import os
import joblib
import pandas as pd
import numpy as np
from config.settings import settings
from utils.logger import logger

class DecisionAgent:
    def __init__(self):
        """Initialize the Decision Agent and load the enhanced model."""
        self.model_path = os.path.join(settings.BASE_DIR, "models", "decision_model.pkl")
        self.data_path = os.path.join(settings.PROCESSED_DATA_DIR, "training_data.csv")
        self.model = None
        
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info("Decision Agent: Enhanced ML Model loaded.")
        else:
            logger.error(f"Decision Agent: Model file not found at {self.model_path}")

    def prepare_features(self, df):
        """
        Ensures temporal order and applies feature engineering used during model training.
        """
        # Convert date to datetime and sort to ensure we pick the actual latest record
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by="date", ascending=True)
        
        # Features calculation (Lags, Rolling, etc.)
        # Groupby 'product' ensures we don't mix time-series data between different items/customers
        df['sales_lag_1'] = df.groupby('product')['sales'].shift(1)
        df['sales_lag_2'] = df.groupby('product')['sales'].shift(2)
        df['sales_lag_3'] = df.groupby('product')['sales'].shift(3)

        df['sales_ma_7'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=7).mean())
        df['sales_ma_14'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=14).mean())
        df['sales_std_7'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=7).std())

        df['momentum'] = df['sales'] - df['sales_lag_3']
        df['stock_ratio'] = df['stock'] / (df['sales'] + 1)
        
        return df

    def get_latest_decision(self):
        """
        Fetches latest data row after sorting and returns prediction.
        """
        if self.model is None:
            return "Error: Model not loaded"

        if not os.path.exists(self.data_path):
            return "Error: Processed data missing"

        try:
            # 1. Load data
            df = pd.read_csv(self.data_path)
            
            # 2. Sort and prepare features
            df = self.prepare_features(df)
            
            # 3. Get the absolute latest row
            latest_row = df.iloc[-1:].fillna(0)
            latest_date = latest_row['date'].iloc[0]
            
            # 4. Input mapping
            feature_cols = [
                "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3", 
                "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7", 
                "momentum", "trend", "stock_ratio"
            ]
            
            # Convert to DataFrame with feature names to suppress sklearn warnings
            input_df = latest_row[feature_cols]
            
            # 5. Predict
            prediction = self.model.predict(input_df)[0]
            decision_msg = "Increase Production" if prediction == 1 else "Reduce Production"
            
            logger.info(f"Decision Agent Result: {decision_msg} | Date: {latest_date}")
            
            return decision_msg

        except Exception as e:
            logger.error(f"Decision Agent Prediction Failed: {str(e)}")
            return "Error: Prediction failed"

def get_decision():
    """Entry point for the decision engine."""
    agent = DecisionAgent()
    return agent.get_latest_decision()

if __name__ == "__main__":
    print(f"Latest System Decision: {get_decision()}")
