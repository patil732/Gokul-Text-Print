"""
routes/agent.py
---------------
Flask Blueprint exposing Multi-Agent Copilot API endpoints:

  - POST /api/agent/ask : Parse question, dispatch sub-agents in parallel, merge JSON, and return synthesized answer.
  - GET  /api/agent/status : Health check and list registered sub-agents.
"""

from flask import Blueprint, jsonify, request
from app.agents.manager_agent import ManagerAgent
from utils.logger import logger

agent_bp = Blueprint("agent_bp", __name__)
_manager = ManagerAgent()


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


@agent_bp.route("/api/agents/sales", methods=["POST", "GET"])
@agent_bp.route("/api/agent/sales", methods=["POST", "GET"])
def sales_agent_direct_endpoint():
    """
    Direct endpoint for SalesAgent execution (for testing and independent use).
    """
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
        else:
            data = request.args.to_dict()

        from app.agents.sales_agent import SalesAgent
        agent = SalesAgent()
        result = agent.execute(data)
        if hasattr(result, "to_dict"):
            result = result.to_dict()

        return jsonify(result), 200
    except Exception as exc:
        logger.error(f"[agent_bp] /api/agents/sales error: {exc}")
        return jsonify({
            "status": "error",
            "message": str(exc),
        }), 500

