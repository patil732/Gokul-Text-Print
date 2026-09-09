"""
app/dashboard/recommendations/aggregator.py
-------------------------------------------
Sprint 6 — Executive Recommendation Aggregator.

Consolidates real-time business recommendations across four intelligence layers:
  1. Sales Engine       (/api/sales/recommendation, Sprint 2)
  2. Inventory Engine   (Sprint 3's inventory prediction and health)
  3. Knowledge Engine   (Sprint 4's policy hits and citations)
  4. Manager Agent      (Sprint 5's multi-agent orchestrated outputs)

Normalizes all outputs into a common schema:
  {
    "recommendation": str,
    "reason": str,
    "confidence": float,
    "priority": "HIGH" | "MEDIUM" | "LOW",
    "source": str,
    "timestamp": str
  }

Derives priority from confidence and source-specific thresholds
(e.g., inventory "Critical" health = HIGH regardless of confidence value).
"""

from __future__ import annotations

from datetime import datetime
import os
import re
import sys
from typing import Any, Dict, List, Optional, Union

# Ensure project root is on sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_THIS_DIR)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from database.db import get_db_connection
from utils.logger import logger

_PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


class RecommendationAggregator:
    """
    Consolidates, normalizes, and ranks recommendations from Sales, Inventory,
    Knowledge, and Manager Agent engines.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path

    # ---------------------------------------------------------------------- #
    # 1. Source Pullers
    # ---------------------------------------------------------------------- #

    def fetch_sales_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Pull latest recommendation from Sales Engine (Sprint 2).
        Falls back to sales_prediction_history table if needed.
        """
        try:
            from app.ml.sales.recommendation import get_recommendation
            result = get_recommendation(forecast_period="30_days")
            if isinstance(result, dict) and result.get("status") != "error":
                return {
                    "raw_decision": result.get("decision", "Maintain Current Production"),
                    "reason": result.get("reason", "Based on 30-day sales forecast."),
                    "confidence": float(result.get("confidence", 0.75)),
                    "growth_rate": float(result.get("growth_rate", 0.0)),
                    "forecast_period": result.get("forecast_period", "30_days"),
                    "source": "sales",
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as exc:
            logger.warning(f"[aggregator] Sales engine direct call failed: {exc}")

        # Fallback to database
        try:
            with get_db_connection(self._db_path) as conn:
                row = conn.execute(
                    """
                    SELECT recommendation, confidence, forecast_period, prediction_date, created_at
                    FROM sales_prediction_history
                    ORDER BY id DESC LIMIT 1
                    """
                ).fetchone()
                if row:
                    return {
                        "raw_decision": row["recommendation"] or "Maintain Production",
                        "reason": f"Historical sales forecast ({row['forecast_period']}).",
                        "confidence": float(row["confidence"] or 0.70),
                        "growth_rate": 0.0,
                        "forecast_period": row["forecast_period"],
                        "source": "sales",
                        "timestamp": row["created_at"] or row["prediction_date"] or datetime.now().isoformat(),
                    }
        except Exception as exc:
            logger.warning(f"[aggregator] Sales database fallback failed: {exc}")

        return None

    def fetch_inventory_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Pull latest recommendation from Inventory Engine (Sprint 3).
        Falls back to prediction_history table if needed.
        """
        try:
            from app.ml.inventory.inventory_prediction import predict_inventory
            inv_res = predict_inventory({})
            if isinstance(inv_res, dict) and inv_res.get("status") == "success":
                raw_decision = str(inv_res.get("decision", "Stock Sufficient"))
                confidence_val = float(inv_res.get("probability", 0.75))

                decision_lower = raw_decision.lower()
                if "reorder" in decision_lower or "critical" in decision_lower or "stockout" in decision_lower:
                    stock_health = "Critical"
                    recommendation = "Restock Immediately"
                    reason = f"Inventory health is Critical ({raw_decision}). Immediate replenishment recommended to avoid stockout."
                elif "warning" in decision_lower or "low" in decision_lower:
                    stock_health = "Warning"
                    recommendation = "Schedule Reorder"
                    reason = f"Inventory health is Warning ({raw_decision}). Reorder cycle should be scheduled."
                else:
                    stock_health = "Healthy"
                    recommendation = "Maintain Replenishment Cycle"
                    reason = "Inventory levels are healthy across warehouse facilities."

                return {
                    "raw_decision": raw_decision,
                    "recommendation": recommendation,
                    "reason": reason,
                    "confidence": confidence_val,
                    "stock_health": stock_health,
                    "source": "inventory",
                    "timestamp": inv_res.get("timestamp", datetime.now().isoformat()),
                }
        except Exception as exc:
            logger.warning(f"[aggregator] Inventory engine direct call failed: {exc}")

        # Fallback to database
        try:
            with get_db_connection(self._db_path) as conn:
                row = conn.execute(
                    """
                    SELECT prediction, confidence, timestamp
                    FROM prediction_history
                    WHERE model_name = 'inventory'
                    ORDER BY id DESC LIMIT 1
                    """
                ).fetchone()
                if row:
                    raw_dec = str(row["prediction"] or "Stock Sufficient")
                    is_crit = "reorder" in raw_dec.lower() or "critical" in raw_dec.lower()
                    return {
                        "raw_decision": raw_dec,
                        "recommendation": "Restock Immediately" if is_crit else "Maintain Inventory",
                        "reason": f"Inventory status indicates {raw_dec}.",
                        "confidence": float(row["confidence"] or 0.70),
                        "stock_health": "Critical" if is_crit else "Healthy",
                        "source": "inventory",
                        "timestamp": row["timestamp"] or datetime.now().isoformat(),
                    }
        except Exception as exc:
            logger.warning(f"[aggregator] Inventory database fallback failed: {exc}")

        return None

    def fetch_knowledge_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Pull relevant policy recommendation from Knowledge Engine (Sprint 4).
        """
        try:
            from app.agents.knowledge_agent import KnowledgeAgent
            k_agent = KnowledgeAgent()
            resp = k_agent.execute({"query": "inventory replenishment safety stock company policy guidelines"})
            if resp.status == "success" and resp.data:
                policy_text = resp.data.get("policy", "")
                sources = resp.data.get("sources", [])
                source_str = ", ".join(sources) if sources else "Enterprise Policies"
                return {
                    "policy": policy_text,
                    "sources": sources,
                    "reason": f"Governed by standard operating policy ({source_str}).",
                    "confidence": float(resp.confidence or 0.85),
                    "source": "knowledge",
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as exc:
            logger.warning(f"[aggregator] Knowledge agent direct call failed: {exc}")

        return None

    def fetch_manager_recommendations(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Pull the last few outputs from Manager Agent (Sprint 5).
        First checks in-memory manager outputs buffer, then chat_history table.
        """
        results: List[Dict[str, Any]] = []

        # 1. Check in-memory buffer in routes/agent.py
        try:
            from routes.agent import get_recent_manager_outputs
            recent = get_recent_manager_outputs(limit=limit)
            for item in recent:
                results.append({
                    "answer": item.get("answer", ""),
                    "question": item.get("question", ""),
                    "confidence": float(item.get("confidence", 0.80)),
                    "agents_used": item.get("agents_used", []),
                    "source": "manager",
                    "timestamp": item.get("timestamp", datetime.now().isoformat()),
                })
        except Exception as exc:
            logger.debug(f"[aggregator] Could not fetch from manager in-memory buffer: {exc}")

        if results:
            return results[:limit]

        # 2. Check chat_history database table
        try:
            with get_db_connection(self._db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT question, answer, retrieved_documents, timestamp
                    FROM chat_history
                    ORDER BY id DESC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
                for row in rows:
                    results.append({
                        "answer": row["answer"] or "",
                        "question": row["question"] or "",
                        "confidence": 0.82,
                        "agents_used": ["manager", "rag"],
                        "source": "manager",
                        "timestamp": row["timestamp"] or datetime.now().isoformat(),
                    })
        except Exception as exc:
            logger.warning(f"[aggregator] chat_history fallback failed: {exc}")

        return results[:limit]

    # ---------------------------------------------------------------------- #
    # 2. Normalization & Priority Derivation
    # ---------------------------------------------------------------------- #

    @staticmethod
    def derive_priority(
        confidence: float,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Derive priority (HIGH / MEDIUM / LOW) from confidence and source-specific rules.

        Rules:
          - Inventory: "Critical" health = HIGH regardless of confidence value.
                       "Warning" health = MEDIUM (or HIGH if confidence >= 0.85).
          - Sales:     Abs(growth_rate) >= 15.0 or confidence >= 0.80 = HIGH;
                       confidence >= 0.60 = MEDIUM; else LOW.
          - Knowledge: confidence >= 0.85 = HIGH; confidence >= 0.65 = MEDIUM; else LOW.
          - Manager:   confidence >= 0.80 = HIGH; confidence >= 0.60 = MEDIUM; else LOW.
        """
        meta = metadata or {}
        source_norm = (source or "").strip().lower()
        conf = max(0.0, min(1.0, float(confidence)))

        # ── Source 1: Inventory Overrides ───────────────────────────────── #
        if source_norm in ("inventory", "inventory engine"):
            health = str(meta.get("stock_health") or meta.get("health", "")).strip().capitalize()
            raw_decision = str(meta.get("raw_decision") or meta.get("decision", "")).lower()
            rec = str(meta.get("recommendation", "")).lower()

            # "Critical" health, reorder required, or stockout risk => HIGH regardless of confidence
            if (
                health == "Critical"
                or "critical" in raw_decision
                or "reorder required" in raw_decision
                or "stockout risk" in raw_decision
                or "restock immediately" in rec
            ):
                return "HIGH"

            if health == "Warning" or "warning" in raw_decision:
                return "HIGH" if conf >= 0.85 else "MEDIUM"

            # Default confidence scale for inventory
            if conf >= 0.80:
                return "HIGH"
            elif conf >= 0.60:
                return "MEDIUM"
            return "LOW"

        # ── Source 2: Sales Overrides ───────────────────────────────────── #
        if source_norm in ("sales", "sales engine"):
            growth_rate = meta.get("growth_rate")
            if growth_rate is not None:
                try:
                    if abs(float(growth_rate)) >= 15.0:
                        return "HIGH"
                except (ValueError, TypeError):
                    pass

            if conf >= 0.80:
                return "HIGH"
            elif conf >= 0.60:
                return "MEDIUM"
            return "LOW"

        # ── Source 3: Knowledge Engine ──────────────────────────────────── #
        if source_norm in ("knowledge", "knowledge engine", "rag"):
            if conf >= 0.85:
                return "HIGH"
            elif conf >= 0.65:
                return "MEDIUM"
            return "LOW"

        # ── Source 4: Manager Agent / Default ───────────────────────────── #
        if conf >= 0.80:
            return "HIGH"
        elif conf >= 0.60:
            return "MEDIUM"
        return "LOW"

    def normalize_item(
        self,
        item: Dict[str, Any],
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Normalize an arbitrary raw source item into standard schema:
        {
          "recommendation": str,
          "reason": str,
          "confidence": float,
          "priority": "HIGH" | "MEDIUM" | "LOW",
          "source": str,
          "timestamp": str
        }
        """
        src = (source or item.get("source") or "unknown").strip().lower()
        conf = round(max(0.0, min(1.0, float(item.get("confidence", 0.5)))), 4)

        # 1. Recommendation text extraction
        recommendation = ""
        if "recommendation" in item and item["recommendation"]:
            recommendation = str(item["recommendation"]).strip()
        elif "decision" in item and item["decision"]:
            recommendation = str(item["decision"]).strip()
        elif "raw_decision" in item and item["raw_decision"]:
            recommendation = str(item["raw_decision"]).strip()
        elif "policy" in item and item["policy"]:
            policy_line = str(item["policy"]).strip().split("\n")[0]
            recommendation = policy_line if len(policy_line) <= 200 else policy_line[:197] + "..."
        elif "answer" in item and item["answer"]:
            # Extract recommendation sentence from manager answer if present
            ans = str(item["answer"]).strip()
            rec_match = re.search(r"(?:Recommendation|Recommended Action)[:\s]+([^\n\.]+[\.]?)", ans, re.IGNORECASE)
            if rec_match:
                recommendation = rec_match.group(1).strip()
            else:
                first_sentence = ans.split(". ")[0].strip()
                recommendation = first_sentence if len(first_sentence) <= 150 else first_sentence[:147] + "..."
        else:
            recommendation = "Action pending further evaluation"

        # 2. Reason extraction
        reason = ""
        if "reason" in item and item["reason"]:
            reason = str(item["reason"]).strip()
        elif "question" in item and item["question"]:
            agents = ", ".join(item.get("agents_used", [])) or "orchestration"
            reason = f"Derived from multi-agent synthesis ({agents}) for query: '{item['question']}'"
        elif "sources" in item and item["sources"]:
            src_names = ", ".join(str(s) for s in item["sources"])
            reason = f"Based on knowledge documentation: {src_names}"
        else:
            reason = f"Identified by {src.capitalize()} analytical model."

        # 3. Priority calculation
        priority = self.derive_priority(conf, src, metadata=item)

        # 4. Timestamp
        raw_ts = item.get("timestamp")
        if raw_ts:
            timestamp = str(raw_ts)
        else:
            timestamp = datetime.now().isoformat()

        return {
            "recommendation": recommendation,
            "reason": reason,
            "confidence": conf,
            "priority": priority,
            "source": src,
            "timestamp": timestamp,
        }

    # ---------------------------------------------------------------------- #
    # 3. Consolidation and Priority Sorting
    # ---------------------------------------------------------------------- #

    def aggregate(
        self,
        sales_raw: Optional[Dict[str, Any]] = None,
        inventory_raw: Optional[Dict[str, Any]] = None,
        knowledge_raw: Optional[Dict[str, Any]] = None,
        manager_raws: Optional[List[Dict[str, Any]]] = None,
        priority_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pull from all four sources (or use provided raw dictionaries), normalize,
        filter by optional priority, and sort:
          Primary:   priority (HIGH -> MEDIUM -> LOW)
          Secondary: confidence (descending)
          Tertiary:  timestamp (descending)
        """
        normalized_list: List[Dict[str, Any]] = []

        # ── 1. Sales Engine ────────────────────────────────────────────── #
        s_data = sales_raw if sales_raw is not None else self.fetch_sales_recommendation()
        if s_data:
            normalized_list.append(self.normalize_item(s_data, source="sales"))

        # ── 2. Inventory Engine ────────────────────────────────────────── #
        i_data = inventory_raw if inventory_raw is not None else self.fetch_inventory_recommendation()
        if i_data:
            normalized_list.append(self.normalize_item(i_data, source="inventory"))

        # ── 3. Knowledge Engine ────────────────────────────────────────── #
        k_data = knowledge_raw if knowledge_raw is not None else self.fetch_knowledge_recommendation()
        if k_data:
            normalized_list.append(self.normalize_item(k_data, source="knowledge"))

        # ── 4. Manager Agent ───────────────────────────────────────────── #
        m_list = manager_raws if manager_raws is not None else self.fetch_manager_recommendations()
        if m_list:
            for m_item in m_list:
                normalized_list.append(self.normalize_item(m_item, source="manager"))

        # ── Optional Priority Filtering ────────────────────────────────── #
        if priority_filter:
            target_p = priority_filter.strip().upper()
            normalized_list = [item for item in normalized_list if item.get("priority") == target_p]

        # ── Sort Order ─────────────────────────────────────────────────── #
        # HIGH (0) -> MEDIUM (1) -> LOW (2), then confidence desc, then timestamp desc
        def sort_key(item: Dict[str, Any]):
            p_val = _PRIORITY_ORDER.get(item.get("priority", "LOW"), 2)
            c_val = -float(item.get("confidence", 0.0))
            t_val = str(item.get("timestamp", ""))
            return (p_val, c_val, t_val)

        normalized_list.sort(key=sort_key)

        if limit is not None and limit > 0:
            return normalized_list[:limit]

        return normalized_list


def aggregate_recommendations(
    priority_filter: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function returning aggregated, priority-sorted recommendations.
    """
    aggregator = RecommendationAggregator()
    return aggregator.aggregate(priority_filter=priority_filter, limit=limit)
