import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score, 
    confusion_matrix, 
    classification_report
)

# Fallback for direct script execution to find project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from utils.logger import logger

def train_decision_model():
    """
    Trains an enhanced predictive model with advanced feature engineering.
    """
    try:
        data_path = os.path.join(settings.PROCESSED_DATA_DIR, "training_data.csv")
        model_dir = os.path.join(settings.BASE_DIR, "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "decision_model.pkl")

        if not os.path.exists(data_path):
            logger.error("Training data not found. Run processing first.")
            return

        df = pd.read_csv(data_path)
        if df.empty:
            logger.error("Training dataset is empty.")
            return

        # 1. Temporal Sort
        df = df.sort_values(by=['product', 'date'])

        # 2. Advanced Feature Engineering
        logger.info("Applying advanced feature engineering...")
        
        # Target: Predicting the future
        df['next_sales'] = df.groupby('product')['sales'].shift(-1)
        df['target_decision'] = (df['next_sales'] > df['sales']).astype(int)

        # Lags
        df['sales_lag_1'] = df.groupby('product')['sales'].shift(1)
        df['sales_lag_2'] = df.groupby('product')['sales'].shift(2)
        df['sales_lag_3'] = df.groupby('product')['sales'].shift(3)

        # Rolling Windows
        df['sales_ma_7'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=7).mean())
        df['sales_ma_14'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=14).mean())
        df['sales_std_7'] = df.groupby('product')['sales'].transform(lambda x: x.rolling(window=7).std())

        # Momentum
        df['momentum'] = df['sales'] - df['sales_lag_3']

        # Stock Efficiency Ratio
        df['stock_ratio'] = df['stock'] / (df['sales'] + 1)

        # 3. Cleanup NaNs from shifts/rolling and drops last row (target NaN)
        df = df.dropna()

        # 4. Feature Selection
        feature_cols = [
            "sales", "sales_lag_1", "sales_lag_2", "sales_lag_3", 
            "sales_ma_3", "sales_ma_7", "sales_ma_14", "sales_std_7", 
            "momentum", "trend", "stock_ratio"
        ]
        
        X = df[feature_cols]
        y = df['target_decision']

        # 5. Train-Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        logger.info(f"Training tuned model with {len(X_train)} samples and {len(feature_cols)} features...")
        
        # 6. Optimized Model Training
        model = RandomForestClassifier(
            n_estimators=200, 
            max_depth=10, 
            random_state=42,
            n_jobs=-1 # Speed up training
        )
        model.fit(X_train, y_train)

        # 7. Predictions & Evaluation
        y_pred = model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        # 8. Display Results
        print("\n" + "="*50)
        print(" ENHANCED MODEL PERFORMANCE (ADVANCED FEATURES) ")
        print("="*50)
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1 Score:  {f1:.4f}")
        print("-" * 50)
        print("CONFUSION MATRIX:")
        print(f"True Negatives  (TN): {tn}")
        print(f"False Positives (FP): {fp}")
        print(f"False Negatives (FN): {fn}")
        print(f"True Positives  (TP): {tp}")
        print("-" * 50)
        print("CLASSIFICATION REPORT:")
        print(classification_report(y_test, y_pred))
        print("="*50 + "\n")

        # 9. Save Model
        joblib.dump(model, model_path)
        logger.info(f"Enhanced predictive model saved to {model_path}")

    except Exception as e:
        logger.error(f"Enhanced model training failed: {str(e)}")
        raise

if __name__ == "__main__":
    train_decision_model()
