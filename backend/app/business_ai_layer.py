"""
app/business_ai_layer.py
------------------------
Thin orchestration layer that routes business insight requests to the
correct domain-specific prediction module.

This class owns ZERO model logic.  It does only three things per method:
  1. Accept a dict of input data from the caller.
  2. Convert it to the DataFrame shape expected by the predict module.
  3. Return the structured dict produced by that module.

Public API
----------
    from app.business_ai_layer import BusinessAILayer

    ai = BusinessAILayer()

    # Sales demand forecast
    result = ai.get_sales_insight(input_data)
    # → {domain, decision, prediction, confidence, probability, reasons, status}

    # Inventory reorder prediction
    result = ai.get_inventory_insight(input_data)
    # → {domain, decision, prediction, confidence, probability, reasons, status}

    # Convenience: run both in one call
    results = ai.get_all_insights(sales_data, inventory_data)
    # → {sales: {...}, inventory: {...}}

Input contract
--------------
``input_data`` is a plain dict whose keys map 1-to-1 with the feature
columns defined in:
  - app/sales/model.py    FEATURE_COLS   (for sales)
  - app/inventory/model.py FEATURE_COLS  (for inventory)

Missing keys are filled with 0.0 by the predict modules themselves.

Error handling
--------------
Both methods catch ALL exceptions so that a failure in one domain never
crashes the other.  On error, the returned dict has::

    {"status": "error", "domain": "sales"|"inventory", "message": "<reason>"}

This contract lets Flask routes return a meaningful JSON response rather
than an unhandled 500.
"""

import os
import sys

_APP_DIR      = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pandas as pd

from utils.logger import logger

# Lazy imports — the predict modules load model artefacts from disk on
# first call, so we defer the import until the method is actually invoked.
# This keeps Flask startup fast even if a model file is temporarily absent.


class BusinessAILayer:
    """
    Thin orchestration layer between Flask routes and ML predict modules.

    Design constraints
    ------------------
    - Contains NO model logic (no sklearn, no joblib, no SHAP).
    - Does NOT import app.sales.predict or app.inventory.predict at class
      definition time — imports happen inside each method to keep startup
      fast and failures isolated.
    - Returns a consistent dict contract regardless of domain so callers
      can handle both responses with identical code.
    """

    # ---------------------------------------------------------------------- #
    # Public methods
    # ---------------------------------------------------------------------- #

    def get_sales_insight(self, input_data: dict) -> dict:
        """
        Route input data to the Sales prediction module and return its result.

        Parameters
        ----------
        input_data : dict
            Feature values keyed by the column names in
            app/sales/model.FEATURE_COLS.  Missing keys are filled with 0.0.

        Returns
        -------
        dict
            On success::
                {
                  "status":      "success",
                  "domain":      "sales",
                  "decision":    str,    # "Increase Production" | "Reduce Production"
                  "prediction":  int,    # 1 | 0
                  "confidence":  str,    # "High" | "Medium"
                  "probability": float,
                  "reasons":     list[str],
                }

            On error::
                {
                  "status":  "error",
                  "domain":  "sales",
                  "message": str,
                }
        """
        try:
            from app.sales.predict import predict_row  # lazy import

            row_df = self._to_dataframe(input_data)
            result = predict_row(row_df)
            result["domain"] = "sales"
            result["status"] = "success"

            logger.info(
                f"[BusinessAILayer] sales insight: "
                f"decision={result.get('decision')} "
                f"confidence={result.get('confidence')}"
            )
            return result

        except NotImplementedError as exc:
            return self._error("sales", f"Module not yet implemented: {exc}")
        except FileNotFoundError as exc:
            return self._error("sales", f"Model artefact missing: {exc}")
        except Exception as exc:
            logger.error(f"[BusinessAILayer] sales insight failed: {exc}")
            return self._error("sales", str(exc))

    def get_inventory_insight(self, input_data: dict) -> dict:
        """
        Route input data to the Inventory prediction module and return its result.

        Parameters
        ----------
        input_data : dict
            Feature values keyed by the column names in
            app/inventory/model.FEATURE_COLS.  Missing keys are filled with 0.0.

        Returns
        -------
        dict
            On success::
                {
                  "status":      "success",
                  "domain":      "inventory",
                  "decision":    str,    # "Reorder Required" | "Stock Sufficient"
                  "prediction":  int,    # 1 | 0
                  "confidence":  str,    # "High" | "Medium"
                  "probability": float,
                  "reasons":     list[str],
                }

            On error::
                {
                  "status":  "error",
                  "domain":  "inventory",
                  "message": str,
                }

        Note
        ----
        The inventory predict module is currently a stub (sprint 1).
        Until sprint 2 implements it, this method returns an error dict
        with ``"message": "Module not yet implemented: …"`` rather than
        raising an exception.
        """
        try:
            from app.inventory.predict import predict_row  # lazy import

            row_df = self._to_dataframe(input_data)
            result = predict_row(row_df)
            result["domain"] = "inventory"
            result["status"] = "success"

            logger.info(
                f"[BusinessAILayer] inventory insight: "
                f"decision={result.get('decision')} "
                f"confidence={result.get('confidence')}"
            )
            return result

        except NotImplementedError as exc:
            # Expected during sprint 1 — inventory model not trained yet
            logger.info(
                f"[BusinessAILayer] inventory predict not yet implemented: {exc}"
            )
            return self._error("inventory", f"Module not yet implemented: {exc}")
        except FileNotFoundError as exc:
            return self._error("inventory", f"Model artefact missing: {exc}")
        except Exception as exc:
            logger.error(f"[BusinessAILayer] inventory insight failed: {exc}")
            return self._error("inventory", str(exc))

    def get_all_insights(
        self,
        sales_input: dict,
        inventory_input: dict,
    ) -> dict:
        """
        Run both domain insights and return them under a single dict.

        Both calls are made sequentially; a failure in one domain does NOT
        prevent the other from running.

        Parameters
        ----------
        sales_input     : dict  Feature values for the sales module.
        inventory_input : dict  Feature values for the inventory module.

        Returns
        -------
        dict::
            {
              "sales":     { ...sales insight dict... },
              "inventory": { ...inventory insight dict... },
            }
        """
        return {
            "sales":     self.get_sales_insight(sales_input),
            "inventory": self.get_inventory_insight(inventory_input),
        }

    # ---------------------------------------------------------------------- #
    # Private helpers
    # ---------------------------------------------------------------------- #

    @staticmethod
    def _to_dataframe(input_data: dict) -> pd.DataFrame:
        """
        Wrap a flat dict in a single-row DataFrame.

        The predict modules handle missing column filling internally, so
        this method only needs to produce a valid DataFrame.
        """
        return pd.DataFrame([input_data])

    @staticmethod
    def _error(domain: str, message: str) -> dict:
        """Return a standard error dict."""
        return {
            "status":  "error",
            "domain":  domain,
            "message": message,
        }


# --------------------------------------------------------------------------- #
# Module-level convenience instance
# --------------------------------------------------------------------------- #
# Import this directly for simple one-off calls:
#   from app.business_ai_layer import business_ai
#   result = business_ai.get_sales_insight(data)
business_ai = BusinessAILayer()
