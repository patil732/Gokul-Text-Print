"""
routes/agent.py
---------------
Flask Blueprint exposing Multi-Agent Copilot API endpoints:

  - POST /api/agent/ask          : Orchestrated multi-agent answer (legacy).
  - GET  /api/agent/status       : Health check and registered sub-agent list.
  - POST /api/agents/sales       : Run SalesAgent independently (testing / direct use).
  - POST /api/agents/inventory   : Run InventoryAgent independently (testing / direct use).
  - POST /api/agents/knowledge   : Run KnowledgeAgent independently (testing / direct use).
  - POST /api/agents/manager     : Full orchestration pipeline with confidence + agent_details.
"""

from collections import deque
from datetime import datetime
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request
from app.agents.manager_agent import ManagerAgent
from app.agents.sales_agent import SalesAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.knowledge_agent import KnowledgeAgent
from utils.logger import logger

agent_bp = Blueprint("agent_bp", __name__)
_manager = ManagerAgent()
_sales_agent = SalesAgent()
_inventory_agent = InventoryAgent()
_knowledge_agent = KnowledgeAgent()

# Thread-safe ring buffer storing the last 10 manager orchestration outputs
_manager_history: deque[Dict[str, Any]] = deque(maxlen=10)


def record_manager_output(output: Dict[str, Any]) -> None:
    """Record a manager orchestration output into the recent memory buffer."""
    if output and output.get("status") == "success":
        entry = {
            "question": output.get("question", ""),
            "answer": output.get("answer", ""),
            "confidence": output.get("confidence", 0.8),
            "agents_used": output.get("agents_used", []),
            "timestamp": datetime.now().isoformat(),
        }
        _manager_history.appendleft(entry)


def get_recent_manager_outputs(limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieve up to `limit` recent manager orchestration outputs."""
    return list(_manager_history)[:limit]


@agent_bp.route("/api/agent/status", methods=["GET"])
def agent_status():
    """
    Return status and list of registered domain sub-agents.
    """
    return jsonify({
        "status": "online",
        "registered_agents": _manager.registered_agents,
        "description": "Multi-Agent AI Executive Business Copilot",
    }), 200


@agent_bp.route("/api/agent/ask", methods=["POST"])
def agent_ask():
    """
    Ask the Multi-Agent Business Copilot an executive question.

    Request JSON:
      {
        "question": "Should we increase inventory?"
      }

    Response JSON:
      {
        "status": "success",
        "question": "Should we increase inventory?",
        "answer": "...",
        "agents_used": ["sales", "inventory", "knowledge"],
        "raw_data": {
          "sales": {...},
          "inventory": {...},
          "knowledge": {...}
        }
      }
    """
    try:
        body = request.get_json(silent=True) or {}
        question = body.get("question", "")

        if not question or not str(question).strip():
            return jsonify({
                "status": "error",
                "message": "Field 'question' is required and cannot be empty.",
            }), 400

        result = _manager.ask(str(question).strip())
        return jsonify(result), 200

    except Exception as exc:
        logger.error(f"[agent_bp] /api/agent/ask error: {exc}")
        return jsonify({
            "status": "error",
            "message": str(exc),
        }), 500


@agent_bp.route("/api/agents/sales", methods=["POST"])
def sales_agent_direct():
    """
    Run the SalesAgent independently for testing and direct use.

    Request JSON (optional):
      { "question": "What is our 30-day sales forecast?" }

    Response JSON:
      {
        "status": "success",
        "agent_name": "sales",
        "data": {
          "sales_growth": -12.4,
          "forecast": 480000.0,
          "recommendation": "Reduce Inventory",
          "market_trend": "Declining",
          "top_product": "Cotton Fabric (Grade A)",
          "forecast_period": "30_days"
        },
        "confidence": 0.825,
        "timestamp": "2026-08-17T..."
      }
    """
    try:
        body = request.get_json(silent=True) or {}
        question = str(body.get("question", "")).strip()

        context = {"query": question} if question else {}
        resp = _sales_agent.execute(context)
        return jsonify(resp.to_dict()), 200 if resp.status in ("success", "warning") else 500

    except Exception as exc:
        logger.error(f"[agent_bp] /api/agents/sales error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@agent_bp.route("/api/agents/inventory", methods=["POST"])
def inventory_agent_direct():
    """
    Run the InventoryAgent independently for testing and direct use.

    Request JSON (optional):
      { "question": "How much stock do we have remaining?" }

    Response JSON:
      {
        "status": "success",
        "agent_name": "inventory",
        "data": {
          "stock_health": "Critical",
          "remaining_days": 4,
          "recommendation": "Restock Immediately",
          "decision": "Reorder Required",
          "confidence_level": "High",
          "model_version": "v1.0",
          "model_type": "xgboost",
          "model_accuracy": 0.9231
        },
        "confidence": 0.92,
        "timestamp": "2026-08-17T..."
      }
    """
    try:
        body = request.get_json(silent=True) or {}
        question = str(body.get("question", "")).strip()

        context = {"query": question} if question else {}
        resp = _inventory_agent.execute(context)
        return jsonify(resp.to_dict()), 200 if resp.status in ("success", "warning") else 500

    except Exception as exc:
        logger.error(f"[agent_bp] /api/agents/inventory error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@agent_bp.route("/api/agents/knowledge", methods=["POST"])
def knowledge_agent_direct():
    """
    Run the KnowledgeAgent independently for testing and direct use.

    Request JSON (optional):
      { "question": "What is the reorder policy for raw materials?" }

    Response JSON:
      {
        "status": "success",
        "agent_name": "knowledge",
        "data": {
          "policy": "Reorder when stock reaches safety level...",
          "sources": ["Inventory Policy.pdf"],
          "source_details": [{"document": "Inventory Policy.pdf", "page": 3, "score": 0.94}],
          "relevant_chunks": 3,
          "query_used": "What is the reorder policy for raw materials?"
        },
        "confidence": 0.94,
        "timestamp": "2026-08-17T..."
      }
    """
    try:
        body = request.get_json(silent=True) or {}
        question = str(body.get("question", "")).strip()

        context = {"query": question} if question else {}
        resp = _knowledge_agent.execute(context)
        return jsonify(resp.to_dict()), 200 if resp.status in ("success", "warning") else 500

    except Exception as exc:
        logger.error(f"[agent_bp] /api/agents/knowledge error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


@agent_bp.route("/api/agents/manager", methods=["POST"])
def manager_orchestrate():
    """
    Full multi-agent orchestration pipeline.

    Request JSON:
      { "question": "Should we increase inventory next week?" }

    Response JSON:
      {
        "status": "success",
        "question": "Should we increase inventory next week?",
        "answer": "...",
        "agents_used": ["sales", "inventory", "knowledge"],
        "confidence": 0.87,
        "agent_details": {
          "sales":     { ...AgentResponse.to_dict()... },
          "inventory": { ...AgentResponse.to_dict()... },
          "knowledge": { ...AgentResponse.to_dict()... }
        }
      }
    """
    try:
        body = request.get_json(silent=True) or {}
        question = str(body.get("question", "")).strip()

        if not question:
            return jsonify({
                "status": "error",
                "message": "Field 'question' is required and cannot be empty.",
            }), 400

        result = _manager.orchestrate(question)
        if result.get("status") == "success":
            record_manager_output(result)

            # Extract source citations from knowledge agent output if present
            knowledge_sources = []
            try:
                agent_details = result.get("agent_details", {})
                k_info = agent_details.get("knowledge", {})
                k_data = k_info.get("data", {}) if isinstance(k_info, dict) else {}
                if isinstance(k_data, dict):
                    if k_data.get("source_details"):
                        knowledge_sources = k_data["source_details"]
                    elif k_data.get("sources"):
                        knowledge_sources = [
                            {"document": str(s), "page": 1, "score": 0.90}
                            for s in k_data["sources"]
                        ]
            except Exception as exc:
                logger.debug(f"[agent_bp] Failed to extract knowledge sources for chat history: {exc}")

            try:
                from app.rag.chat_history import save_chat_turn
                chat_id = save_chat_turn(
                    question=question,
                    answer=result.get("answer", ""),
                    sources=knowledge_sources,
                    user="manager",
                    is_manager=True,
                )
                result["chat_id"] = chat_id
            except Exception as exc:
                logger.warning(f"[agent_bp] Could not save manager turn to chat_history: {exc}")

        http_code = 200 if result.get("status") == "success" else 500
        return jsonify(result), http_code

    except Exception as exc:
        logger.error(f"[agent_bp] /api/agents/manager error: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500
