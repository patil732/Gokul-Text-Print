"""
app/sales/train.py
------------------
Training entry point for the Sales demand-forecasting module.

CLI usage
---------
    python -m app.sales.train                        # default paths
    python -m app.sales.train --force-reprocess      # re-run preprocessing even if CSV exists
    python -m app.sales.train --processed-csv /path/to/custom.csv
    python -m app.sales.train --help

Outputs (written to models/)
-----------------------------
    models/sales_rf.pkl      — fitted RandomForestClassifier
    models/sales_shap.pkl    — fitted shap.TreeExplainer (built on training set)

Pipeline
--------
1. Load raw sales CSV                  (data_loader.load_raw_sales)
2. Feature-engineer & persist CSV      (preprocess.run_and_save)
3. Train / test split (80 / 20)
4. Fit RandomForestClassifier          (model.build)
5. Evaluate: accuracy, precision, recall, F1, confusion matrix
6. Save model artefact                 (model.save  → models/sales_rf.pkl)
7. Fit SHAP TreeExplainer on X_train   (shap.TreeExplainer)
8. Save SHAP explainer                 (model.save_shap → models/sales_shap.pkl)

No imports from app.inventory — fully decoupled.
"""

import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import shap
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
from app.sales.model       import (
    build, save, load_shap,
    save_shap, FEATURE_COLS, TARGET_COL, MODEL_PATH, SHAP_PATH,
)
from utils.logger import logger


# --------------------------------------------------------------------------- #
# Core training function
# --------------------------------------------------------------------------- #
def train(
    processed_csv: str = PROCESSED_CSV,
    force_reprocess: bool = False,
) -> None:
    """
    Full training pipeline for the sales module.

    Parameters
    ----------
    processed_csv : str
        Path to the preprocessed feature CSV.  If the file already exists
        it is reused unless *force_reprocess* is True.
    force_reprocess : bool
        When True, raw data is re-loaded and preprocessing is re-run even
        if *processed_csv* already exists on disk.
    """
    # ------------------------------------------------------------------ #
    # 1. Load or (re-)generate preprocessed data
    # ------------------------------------------------------------------ #
    needs_preprocess = force_reprocess or not os.path.exists(processed_csv)

    if needs_preprocess:
        logger.info("[sales.train] Running preprocessing pipeline …")
        raw = load_raw_sales()
        df  = run_and_save(raw, output_path=processed_csv)
    else:
        logger.info(f"[sales.train] Loading preprocessed data from {processed_csv}")
        df = pd.read_csv(processed_csv)

    if df.empty:
        logger.error("[sales.train] No data available for training. Aborting.")
        return

    # ------------------------------------------------------------------ #
    # 2. Validate feature columns
    # ------------------------------------------------------------------ #
    required = set(FEATURE_COLS) | {TARGET_COL}
    missing  = required - set(df.columns)
    if missing:
        logger.error(f"[sales.train] Missing columns: {missing}. Re-run preprocessing.")
        return

    # stock_ratio is engineered from ERP stock data which is optional
    if "stock_ratio" not in df.columns:
        logger.warning("[sales.train] 'stock_ratio' absent — filling with 0.")
        df["stock_ratio"] = 0.0

    # ------------------------------------------------------------------ #
    # 3. Build feature matrix and target vector
    # ------------------------------------------------------------------ #
    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    logger.info(f"[sales.train] Dataset: {len(X):,} rows × {len(FEATURE_COLS)} features")

    print("\n" + "=" * 54)
    print("   SAMPLE — TARGET VARIABLE  (sales module)")
    print("=" * 54)
    print(df[[TARGET_COL]].head(10).to_string(index=False))
    print("=" * 54 + "\n")

    # ------------------------------------------------------------------ #
    # 4. Train / test split
    # ------------------------------------------------------------------ #
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(
        f"[sales.train] Split — train: {len(X_train):,}  test: {len(X_test):,}"
    )

    # ------------------------------------------------------------------ #
    # 5. Fit model
    # ------------------------------------------------------------------ #
    logger.info("[sales.train] Fitting RandomForestClassifier …")
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

    print("\n" + "=" * 54)
    print("   SALES MODEL — TRAINING RESULTS")
    print("=" * 54)
    print(f"  Accuracy  : {accuracy:.4f}")
    print(f"  Precision : {precision:.4f}")
    print(f"  Recall    : {recall:.4f}")
    print(f"  F1 Score  : {f1:.4f}")
    print("-" * 54)
    print("  CONFUSION MATRIX")
    print(f"    True Negatives  (TN) : {tn}")
    print(f"    False Positives (FP) : {fp}")
    print(f"    False Negatives (FN) : {fn}")
    print(f"    True Positives  (TP) : {tp}")
    print("-" * 54)
    print("  CLASSIFICATION REPORT")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("=" * 54 + "\n")

    # ------------------------------------------------------------------ #
    # 7. Save model artefact  →  models/sales_rf.pkl
    # ------------------------------------------------------------------ #
    save(clf, path=MODEL_PATH)

    # ------------------------------------------------------------------ #
    # 8. Build and save SHAP explainer  →  models/sales_shap.pkl
    #
    # We fit the explainer on the training set so SHAP background
    # statistics match the data distribution seen during training.
    # A random subsample (≤500 rows) is used to keep fitting fast while
    # still providing a representative background dataset.
    # ------------------------------------------------------------------ #
    logger.info("[sales.train] Building SHAP TreeExplainer on training set …")
    shap_background = (
        X_train.sample(n=min(500, len(X_train)), random_state=42)
        if len(X_train) > 500
        else X_train
    )
    try:
        explainer = shap.TreeExplainer(clf, data=shap_background)
    except Exception as exc:
        logger.warning(f"[sales.train] TreeExplainer failed ({exc}) — using fallback Explainer.")
        try:
            explainer = shap.Explainer(clf.predict_proba, shap_background)
        except Exception:
            explainer = shap.Explainer(clf, shap_background)
    save_shap(explainer, path=SHAP_PATH)

    print(f"  Model    -> {MODEL_PATH}")
    print(f"  Explainer-> {SHAP_PATH}")
    logger.info("[sales.train] Training pipeline complete.")


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.sales.train",
        description="Train the Sales demand-forecasting RandomForest model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Outputs\n"
            "-------\n"
            f"  {MODEL_PATH}\n"
            f"  {SHAP_PATH}\n"
        ),
    )
    parser.add_argument(
        "--processed-csv",
        default=PROCESSED_CSV,
        metavar="PATH",
        help=(
            "Path to the preprocessed feature CSV. "
            f"Default: {PROCESSED_CSV}"
        ),
    )
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        default=False,
        help=(
            "Re-run data loading and preprocessing even if the processed "
            "CSV already exists on disk."
        ),
    )
    return parser


def main() -> None:
    """Parse CLI args and run the training pipeline."""
    parser = _build_parser()
    args   = parser.parse_args()
    train(
        processed_csv=args.processed_csv,
        force_reprocess=args.force_reprocess,
    )


if __name__ == "__main__":
    main()
