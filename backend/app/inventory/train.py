"""
app/inventory/train.py
----------------------
Training entry point for the Inventory reorder-prediction module.

CLI usage
---------
    python -m app.inventory.train                        # default paths
    python -m app.inventory.train --force-reprocess      # re-run preprocessing
    python -m app.inventory.train --processed-csv /path/to/custom.csv
    python -m app.inventory.train --help

Outputs (written to models/)
-----------------------------
    models/inventory_rf.pkl      — fitted RandomForestClassifier
    models/inventory_shap.pkl    — fitted shap.TreeExplainer (built on training set)

Pipeline
--------
1. Load raw stock CSV                  (data_loader.load_raw_stock)
2. Load raw production CSV             (data_loader.load_raw_production)
3. Feature-engineer & persist CSV      (preprocess.run_and_save)
4. Train / test split (80 / 20, stratified on reorder_flag)
5. Fit RandomForestClassifier          (model.build  — class_weight=balanced)
6. Evaluate: accuracy, precision, recall, F1, confusion matrix
7. Save model artefact                 (model.save  → models/inventory_rf.pkl)
8. Fit SHAP TreeExplainer on X_train   (shap.TreeExplainer)
9. Save SHAP explainer                 (model.save_shap → models/inventory_shap.pkl)

No imports from app.sales — fully decoupled.
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

from app.inventory.data_loader import load_raw_stock, load_raw_production
from app.inventory.preprocess  import run_and_save, PROCESSED_CSV, FEATURE_COLS, TARGET_COL
from app.inventory.model       import (
    build, save, save_shap,
    FEATURE_COLS as MODEL_FEATURE_COLS,
    MODEL_PATH, SHAP_PATH,
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
    Full training pipeline for the inventory module.

    Parameters
    ----------
    processed_csv : str
        Path to the preprocessed feature CSV.  Reused if it already exists
        unless *force_reprocess* is True.
    force_reprocess : bool
        When True, raw data is re-loaded and preprocessing is re-run even
        if *processed_csv* already exists on disk.
    """
    # ------------------------------------------------------------------ #
    # 1-3. Load or (re-)generate preprocessed data
    # ------------------------------------------------------------------ #
    needs_preprocess = force_reprocess or not os.path.exists(processed_csv)

    if needs_preprocess:
        logger.info("[inventory.train] Running preprocessing pipeline …")
        df_stock = load_raw_stock()
        df_prod  = load_raw_production()
        df = run_and_save(df_stock, df_prod, output_path=processed_csv)
    else:
        logger.info(f"[inventory.train] Loading preprocessed data from {processed_csv}")
        df = pd.read_csv(processed_csv)

    if df.empty:
        logger.error("[inventory.train] No data available for training. Aborting.")
        return

    # ------------------------------------------------------------------ #
    # 4. Validate feature columns
    # ------------------------------------------------------------------ #
    required = set(FEATURE_COLS) | {TARGET_COL}
    missing  = required - set(df.columns)
    if missing:
        logger.error(f"[inventory.train] Missing columns: {missing}. Re-run preprocessing.")
        return

    # ------------------------------------------------------------------ #
    # 5. Build feature matrix and target vector
    # ------------------------------------------------------------------ #
    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    logger.info(f"[inventory.train] Dataset: {len(X):,} items × {len(FEATURE_COLS)} features")
    logger.info(f"[inventory.train] Class balance — reorder_flag=1: {y.mean():.1%}")

    print("\n" + "=" * 54)
    print("   INVENTORY MODULE — CLASS DISTRIBUTION")
    print("=" * 54)
    vc = y.value_counts().sort_index()
    print(f"  reorder_flag=0 (Sufficient stock) : {vc.get(0, 0):>8,}")
    print(f"  reorder_flag=1 (Reorder needed)   : {vc.get(1, 0):>8,}")
    print("=" * 54 + "\n")

    # ------------------------------------------------------------------ #
    # 6. Train / test split (stratified to preserve class ratio)
    # ------------------------------------------------------------------ #
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(
        f"[inventory.train] Split — train: {len(X_train):,}  test: {len(X_test):,}"
    )

    # ------------------------------------------------------------------ #
    # 7. Fit model (class_weight=balanced handles class imbalance)
    # ------------------------------------------------------------------ #
    logger.info("[inventory.train] Fitting RandomForestClassifier (balanced) …")
    clf = build()
    clf.fit(X_train, y_train)

    # ------------------------------------------------------------------ #
    # 8. Evaluate
    # ------------------------------------------------------------------ #
    y_pred = clf.predict(X_test)

    accuracy  = accuracy_score(y_test,  y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall    = recall_score(y_test,    y_pred, zero_division=0)
    f1        = f1_score(y_test,        y_pred, zero_division=0)
    cm        = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    print("\n" + "=" * 54)
    print("   INVENTORY MODEL — TRAINING RESULTS")
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
    # 9. Save model artefact  →  models/inventory_rf.pkl
    # ------------------------------------------------------------------ #
    save(clf, path=MODEL_PATH)

    # ------------------------------------------------------------------ #
    # 10. Build and save SHAP explainer  →  models/inventory_shap.pkl
    #
    # Subsample X_train for background (≤500 rows) to keep fitting fast.
    # class_weight does not affect shap.TreeExplainer construction.
    # ------------------------------------------------------------------ #
    logger.info("[inventory.train] Building SHAP TreeExplainer on training set …")
    shap_background = (
        X_train.sample(n=min(500, len(X_train)), random_state=42)
        if len(X_train) > 500
        else X_train
    )
    try:
        explainer = shap.TreeExplainer(clf, data=shap_background)
    except Exception as exc:
        logger.warning(f"[inventory.train] TreeExplainer failed ({exc}) — using fallback Explainer.")
        try:
            explainer = shap.Explainer(clf.predict_proba, shap_background)
        except Exception:
            explainer = shap.Explainer(clf, shap_background)
    save_shap(explainer, path=SHAP_PATH)

    print(f"  Model     -> {MODEL_PATH}")
    print(f"  Explainer -> {SHAP_PATH}")
    logger.info("[inventory.train] Training pipeline complete.")


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.inventory.train",
        description="Train the Inventory reorder-prediction RandomForest model.",
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
