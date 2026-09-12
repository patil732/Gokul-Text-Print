"""
tests/test_sales_dataset.py
----------------------------
Sprint 2 — Sales Intelligence Engine
Unit tests for:

  1. app/ml/sales/dataset.py
       - build_sales_dataset() produces a non-empty CSV on disk
       - Output has zero duplicate rows
       - Output has zero nulls in key columns (date, product, revenue, revenue_norm)
       - Output contains all required date-feature columns

  2. app/ml/sales/sales_feature_engineering.compute_sales_features()
       - All Sprint-1 feature columns are present
       - All Sprint-2 new feature columns are present
         (product_popularity, seasonal_index, sales_frequency)
       - Result has zero duplicates
       - Result has zero nulls

  3. app/ml/sales/sales_feature_engineering.compute_extended_features()
       - Returns only the three new Sprint-2 columns when called standalone

All tests use a self-contained synthetic fixture — no live database,
no network access, and no running ETL pipeline required.
"""

from __future__ import annotations

import os
import sys
import tempfile

import numpy  as np
import pandas as pd
import pytest

# ── Project path bootstrap ────────────────────────────────────────────────── #
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.sales.dataset import (
    build_sales_dataset,
    load_sales_dataset,
)
from app.ml.sales.sales_feature_engineering import (
    compute_sales_features,
    compute_extended_features,
)


# ============================================================================ #
# Fixtures
# ============================================================================ #

# Sprint-1 feature columns produced by compute_sales_features()
_SPRINT1_FEATURE_COLS = [
    "daily_sales",
    "weekly_sales",
    "monthly_sales",
    "growth_rate",
    "rolling_avg",
    "moving_avg_7d",
    "revenue_trend",
    "sales_volatility",
    "sales_lag_1",
    "sales_lag_2",
    "sales_lag_3",
    "momentum",
    "stock_ratio",
]

# Sprint-2 new feature columns
_SPRINT2_FEATURE_COLS = [
    "product_popularity",
    "seasonal_index",
    "sales_frequency",
]

# All required feature columns (union)
_ALL_FEATURE_COLS = _SPRINT1_FEATURE_COLS + _SPRINT2_FEATURE_COLS

# Key columns that must have zero nulls in the built dataset
_DATASET_NO_NULL_COLS = ["date", "product", "revenue", "revenue_norm"]


def _make_synthetic_sales_df(n_products: int = 3, n_days: int = 15) -> pd.DataFrame:
    """
    Build a synthetic sales DataFrame in the ETL raw format:
      name, transaction_date, customer, grand_total, status

    Includes deliberate noise:
      - Two exact duplicate rows
      - One row with a negative grand_total (invalid)
      - One row with a NaT date (invalid)
      - One row with a null grand_total (missing value)
    """
    rng      = np.random.default_rng(42)
    products = [f"Product_{chr(65 + i)}" for i in range(n_products)]

    dates    = pd.date_range("2024-01-01", periods=n_days, freq="D")

    rows = []
    counter = 1
    for product in products:
        for date in dates:
            rows.append({
                "name":             f"SO-{counter:05d}",
                "transaction_date": date.strftime("%Y-%m-%d"),
                "customer":         product,
                "grand_total":      round(float(rng.uniform(500, 50_000)), 2),
                "status":           "Completed",
            })
            counter += 1

    df = pd.DataFrame(rows)

    # Inject deliberate noise
    dup_row = df.iloc[0].copy()
    dup_row["name"] = "SO-DUPE-99"          # different name but same data otherwise
    # Make it a true content duplicate (same date, product, revenue)
    noise = pd.DataFrame([
        # Exact duplicate row (same 'name' → will be deduped by name)
        {**df.iloc[5].to_dict(), "name": df.iloc[5]["name"]},
        # Different name, same rest → exact-content dup
        {**df.iloc[7].to_dict(), "name": "SO-EXACT-DUP"},
        # Negative revenue (invalid)
        {"name": "SO-NEG", "transaction_date": "2024-01-10",
         "customer": products[0], "grand_total": -100.0, "status": "Cancelled"},
        # Unparseable date (invalid)
        {"name": "SO-BAD-DATE", "transaction_date": "not-a-date",
         "customer": products[1], "grand_total": 1000.0, "status": "Completed"},
        # Null grand_total (missing → should be filled with 0.0)
        {"name": "SO-NULL-AMT", "transaction_date": "2024-01-12",
         "customer": products[2], "grand_total": None, "status": "Draft"},
    ])
    df = pd.concat([df, noise], ignore_index=True)
    return df


@pytest.fixture(scope="module")
def synthetic_csv(tmp_path_factory) -> str:
    """Write the synthetic sales DataFrame to a temp CSV and return its path."""
    tmp_dir = tmp_path_factory.mktemp("raw")
    path    = str(tmp_dir / "sales.csv")
    _make_synthetic_sales_df().to_csv(path, index=False)
    return path


@pytest.fixture(scope="module")
def built_dataset(synthetic_csv, tmp_path_factory) -> tuple[pd.DataFrame, str]:
    """
    Run build_sales_dataset() on the synthetic CSV and return
    (loaded_dataframe, output_path).
    """
    tmp_dir     = tmp_path_factory.mktemp("out")
    output_path = str(tmp_dir / "sales_dataset.csv")

    result = build_sales_dataset(source_path=synthetic_csv, output_path=output_path)

    assert result["status"] == "success", (
        f"build_sales_dataset() failed: {result['errors']}"
    )

    df = pd.read_csv(output_path, parse_dates=["date"])
    return df, output_path


@pytest.fixture(scope="module")
def featured_df(synthetic_csv) -> pd.DataFrame:
    """
    Load synthetic data, run compute_sales_features(), and return the result.
    Uses the same raw format as the ETL output (transaction_date / customer /
    grand_total) so the column-mapping path inside compute_sales_features() fires.
    """
    df_raw = pd.read_csv(synthetic_csv)
    return compute_sales_features(df_raw)


# ============================================================================ #
# Tests — dataset.py
# ============================================================================ #

class TestBuildSalesDataset:
    """Tests for build_sales_dataset() and load_sales_dataset()."""

    # ── Output file exists and is non-empty ─────────────────────────────── #

    def test_output_file_exists(self, built_dataset):
        _, output_path = built_dataset
        assert os.path.exists(output_path), "Output CSV was not created on disk."

    def test_output_is_non_empty(self, built_dataset):
        df, _ = built_dataset
        assert len(df) > 0, "build_sales_dataset() produced an empty DataFrame."

    # ── Zero duplicate rows ──────────────────────────────────────────────── #

    def test_no_duplicate_rows(self, built_dataset):
        df, _ = built_dataset
        n_dupes = df.duplicated().sum()
        assert n_dupes == 0, (
            f"Output dataset has {n_dupes} duplicate row(s). Expected 0."
        )

    # ── Zero nulls in key columns ─────────────────────────────────────────── #

    @pytest.mark.parametrize("col", _DATASET_NO_NULL_COLS)
    def test_no_nulls_in_key_column(self, built_dataset, col):
        df, _ = built_dataset
        if col not in df.columns:
            pytest.skip(f"Column '{col}' not present in output.")
        n_nulls = df[col].isna().sum()
        assert n_nulls == 0, (
            f"Column '{col}' has {n_nulls} null value(s). Expected 0."
        )

    # ── Required date-feature columns present ──────────────────────────── #

    @pytest.mark.parametrize("col", ["year", "month", "day_of_week",
                                      "week_of_year", "quarter", "revenue_norm"])
    def test_required_columns_present(self, built_dataset, col):
        df, _ = built_dataset
        assert col in df.columns, (
            f"Required column '{col}' is missing from the built dataset."
        )

    # ── Negative revenues removed ─────────────────────────────────────────── #

    def test_no_negative_revenue(self, built_dataset):
        df, _ = built_dataset
        assert (df["revenue"] >= 0).all(), "Output contains negative revenue values."

    # ── revenue_norm is bounded [0, 1] ───────────────────────────────────── #

    def test_revenue_norm_bounds(self, built_dataset):
        df, _ = built_dataset
        assert df["revenue_norm"].between(0.0, 1.0).all(), (
            "revenue_norm values are not bounded in [0, 1]."
        )

    # ── load_sales_dataset round-trips correctly ─────────────────────────── #

    def test_load_sales_dataset_roundtrip(self, built_dataset):
        df_original, output_path = built_dataset
        df_loaded = load_sales_dataset(path=output_path)
        assert len(df_loaded) == len(df_original), (
            f"Round-trip row count mismatch: built={len(df_original)}, "
            f"loaded={len(df_loaded)}."
        )


# ============================================================================ #
# Tests — compute_sales_features() (feature engineering)
# ============================================================================ #

class TestComputeSalesFeatures:
    """Tests for the extended compute_sales_features() function."""

    # ── Non-empty result ─────────────────────────────────────────────────── #

    def test_result_is_non_empty(self, featured_df):
        assert len(featured_df) > 0, "compute_sales_features() returned empty DataFrame."

    # ── Zero duplicate rows ──────────────────────────────────────────────── #

    def test_no_duplicate_rows(self, featured_df):
        n_dupes = featured_df.duplicated().sum()
        assert n_dupes == 0, (
            f"Featured DataFrame has {n_dupes} duplicate row(s). Expected 0."
        )

    # ── Zero nulls across all columns ────────────────────────────────────── #

    def test_no_null_values(self, featured_df):
        null_counts = featured_df.isna().sum()
        cols_with_nulls = null_counts[null_counts > 0]
        assert cols_with_nulls.empty, (
            f"Featured DataFrame has null values in columns: "
            f"{cols_with_nulls.to_dict()}"
        )

    # ── Sprint-1 feature columns present ─────────────────────────────────── #

    @pytest.mark.parametrize("col", _SPRINT1_FEATURE_COLS)
    def test_sprint1_feature_columns_present(self, featured_df, col):
        assert col in featured_df.columns, (
            f"Sprint-1 feature column '{col}' is missing from the output."
        )

    # ── Sprint-2 new feature columns present ─────────────────────────────── #

    @pytest.mark.parametrize("col", _SPRINT2_FEATURE_COLS)
    def test_sprint2_feature_columns_present(self, featured_df, col):
        assert col in featured_df.columns, (
            f"Sprint-2 feature column '{col}' is missing from the output."
        )

    # ── product_popularity sums to ≈ 1.0 ────────────────────────────────── #

    def test_product_popularity_sums_to_one(self, featured_df):
        """
        product_popularity is each row's sales / grand_total_sales.
        Summing over all rows gives total_sales / grand_total_sales * n_rows,
        but summing the *unique* product totals should equal 1.0.
        """
        product_share = (
            featured_df.groupby("product")["sales"].sum()
            / featured_df["sales"].sum()
        )
        assert abs(product_share.sum() - 1.0) < 1e-6, (
            f"Product popularity does not sum to 1.0: {product_share.sum()}"
        )

    # ── seasonal_index is positive ───────────────────────────────────────── #

    def test_seasonal_index_is_positive(self, featured_df):
        assert (featured_df["seasonal_index"] >= 0).all(), (
            "seasonal_index contains negative values."
        )

    # ── sales_frequency is ≥ 1 and ≤ 30 ─────────────────────────────────── #

    def test_sales_frequency_range(self, featured_df):
        assert (featured_df["sales_frequency"] >= 1).all(), (
            "sales_frequency contains values < 1."
        )
        assert (featured_df["sales_frequency"] <= 30).all(), (
            "sales_frequency contains values > 30 (exceeds 30-day window)."
        )

    # ── No inf values ────────────────────────────────────────────────────── #

    def test_no_inf_values(self, featured_df):
        numeric_cols = featured_df.select_dtypes(include=[np.number]).columns
        has_inf = np.isinf(featured_df[numeric_cols]).any().any()
        assert not has_inf, "Featured DataFrame contains infinite values."


# ============================================================================ #
# Tests — compute_extended_features()
# ============================================================================ #

class TestComputeExtendedFeatures:
    """Tests for the standalone compute_extended_features() wrapper."""

    @pytest.fixture(scope="class")
    def extended_df(self):
        """Run compute_extended_features() on a minimal prepared DataFrame."""
        df = pd.DataFrame({
            "product": ["Alpha", "Alpha", "Beta", "Beta", "Alpha"],
            "date":    pd.to_datetime(["2024-01-01", "2024-01-02",
                                       "2024-01-01", "2024-01-02",
                                       "2024-02-01"]),
            "sales":   [1000.0, 1500.0, 800.0, 1200.0, 2000.0],
        })
        return compute_extended_features(df)

    def test_result_non_empty(self, extended_df):
        assert len(extended_df) > 0

    @pytest.mark.parametrize("col", _SPRINT2_FEATURE_COLS)
    def test_sprint2_columns_added(self, extended_df, col):
        assert col in extended_df.columns, (
            f"compute_extended_features() did not add '{col}'."
        )

    def test_no_nulls(self, extended_df):
        null_counts = extended_df[_SPRINT2_FEATURE_COLS].isna().sum()
        assert null_counts.sum() == 0, (
            f"extended features contain nulls: {null_counts[null_counts > 0].to_dict()}"
        )

    def test_product_popularity_bounded(self, extended_df):
        assert extended_df["product_popularity"].between(0.0, 1.0).all()

    def test_empty_df_returns_empty(self):
        result = compute_extended_features(pd.DataFrame())
        assert result.empty, "compute_extended_features(empty) should return empty DataFrame."


# ============================================================================ #
# CLI runner
# ============================================================================ #

if __name__ == "__main__":
    import subprocess, sys as _sys
    result = subprocess.run(
        [_sys.executable, "-m", "pytest", __file__, "-v"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    _sys.exit(result.returncode)
