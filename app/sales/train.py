"""
app/sales/train.py
------------------
Training entry point for the Sales demand-forecasting module.

Run this file directly to retrain the sales model without touching
any inventory code:

    python -m app.sales.train
    # or
    python app/sales/train.py

Pipeline
--------
1. Load raw sales data          (data_loader.load_raw_sales)
2. Feature-engineer             (preprocess.run_and_save)
3. Split into train / test
4. Train RandomForest           (model.build / model.save)
5. Evaluate and print metrics

Nothing here imports from app/inventory — the two modules are fully
decoupled and can be retrained independently.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

from app.sales.data_loader import load_raw_sales
from app.sales.preprocess  import run_and_save, PROCESSED_CSV
from app.sales.model       import build, save, load, FEATURE_COLS, TARGET_COL, MODEL_PATH
from utils.logger          import logger


def train(processed_csv: str = PROCESSED_CSV) -> None:
    """
    Full training pipeline for the sales module.

    Parameters
    ----------
    processed_csv : str
        Path to the preprocessed CSV.  If the file already exists it is
        reused; otherwise raw data is loaded and processed first.
    """
    # ------------------------------------------------------------------ #
    # 1. Load + preprocess
    # ------------------------------------------------------------------ #
    if not os.path.exists(processed_csv):
        logger.info("[sales.train] Processed CSV missing — running preprocessing.")
        raw = load_raw_sales()
        df  = run_and_save(raw, output_path=processed_csv)
    else:
        logger.info(f"[sales.train] Loading preprocessed data from {processed_csv}")
        df = pd.read_csv(processed_csv)

    if df.empty:
        logger.error("[sales.train] No data available for training. Aborting.")
        return

    # ------------------------------------------------------------------ #
    # 2. Validate required columns
    # ------------------------------------------------------------------ #
    missing = (set(FEATURE_COLS) | {TARGET_COL}) - set(df.columns)
    if missing:
        logger.error(f"[sales.train] Missing columns: {missing}. Re-run preprocessing.")
        return

    # ------------------------------------------------------------------ #
    # 3. Build X / y
    # ------------------------------------------------------------------ #
    # stock_ratio is in FEATURE_COLS but may not be in the processed CSV
    # (stock data was optional during ingestion).  Fill with 0 if absent.
    if "stock_ratio" not in df.columns:
        logger.warning("[sales.train] 'stock_ratio' not found — defaulting to 0.")
        df["stock_ratio"] = 0.0

    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    logger.info(f"[sales.train] Dataset: {len(X):,} rows | {len(FEATURE_COLS)} features")

    # Display sample of target variable (mirrors original train_model.py output)
    print("\n" + "=" * 50)
    print("  SAMPLE — TARGET VARIABLE (sales module)  ")
    print("=" * 50)
    print(df[[TARGET_COL]].head(10).to_string(index=False))
    print("=" * 50 + "\n")

    # ------------------------------------------------------------------ #
    # 4. Train / test split
    # ------------------------------------------------------------------ #
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ------------------------------------------------------------------ #
    # 5. Train
    # ------------------------------------------------------------------ #
    logger.info(
        f"[sales.train] Training RandomForest with {len(X_train):,} samples …"
    )
    clf = build()
    clf.fit(X_train, y_train)

    # ------------------------------------------------------------------ #
    # 6. Evaluate
    # ------------------------------------------------------------------ #
    y_pred = clf.predict(X_test)

    accuracy  = accuracy_score(y_test,  y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall    = recall_score(y_test,    y_pred, zero_division=0)
    f1        = f1_score(y_test,        y_pred, zero_division=0)
    cm        = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    print("\n" + "=" * 50)
    print("  SALES MODEL — TRAINING RESULTS  ")
    print("=" * 50)
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("-" * 50)
    print("CONFUSION MATRIX:")
    print(f"  True Negatives  (TN): {tn}")
    print(f"  False Positives (FP): {fp}")
    print(f"  False Negatives (FN): {fn}")
    print(f"  True Positives  (TP): {tp}")
    print("-" * 50)
    print("CLASSIFICATION REPORT:")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("=" * 50 + "\n")

    # ------------------------------------------------------------------ #
    # 7. Persist
    # ------------------------------------------------------------------ #
    save(clf, path=MODEL_PATH)
    logger.info(f"[sales.train] Training complete. Model → {MODEL_PATH}")


if __name__ == "__main__":
    train()
