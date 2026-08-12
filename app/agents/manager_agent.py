"""
app/agents/manager_agent.py
---------------------------
Manager / Orchestrator Agent.

The ONLY agent that interacts with the LLM.
Responsibilities:
  1. Parse the CEO's natural-language question.
  2. Perform intent routing to select relevant sub-agents.
  3. Execute sub-agents in parallel via ThreadPoolExecutor.
  4. Aggregate strictly structured JSON responses.
  5. Build a grounded prompt via app.agents.prompt_builder.
  6. Dispatch to the config-driven LLM provider for the final natural-language response.

Design constraints:
  - NEVER queries database tables directly.
  - Extensible agent registry: Adding new agents requires zero modifications to existing sub-agents.
"""

from __future__ import annotations

import concurrent.futures
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.prompt_builder import build_copilot_prompt
from app.agents.sales_agent import SalesAgent
from app.rag.chat_service import get_chat_provider
from utils.logger import logger

_SALES_KEYWORDS = {
    "sale", "sales", "revenue", "demand", "market", "forecast", "growth",
    "trend", "customer", "sell", "price", "marketing", "projection", "target"
}

_INVENTORY_KEYWORDS = {
    "inventory", "stock", "reorder", "restock", "warehouse", "bin", "supply",
    "material", "quantity", "safety stock", "shortage", "storage", "replenish"
}

_KNOWLEDGE_KEYWORDS = {
    "policy", "sop", "standard", "procedure", "rule", "guideline", "manual",
    "document", "regulation", "spec", "compliance", "process", "instruction"
}

_CROSS_DOMAIN_PHRASES = [
    "should we increase inventory",
    "should we decrease inventory",
    "should we restock",
    "should we reorder",
    "should we scale",
    "business overview",
    "copilot",
    "recommendation",
    "what should we do",
    "executive update",
    "strategic advice",
]


class ManagerAgent:
    """
    Central Multi-Agent Orchestrator for the Executive Business Copilot.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url
        self._agents: Dict[str, BaseAgent] = {}
        # Register default sub-agents
        self.register_agent("sales", SalesAgent(base_url=base_url))
        self.register_agent("inventory", InventoryAgent(base_url=base_url))
        self.register_agent("knowledge", KnowledgeAgent(base_url=base_url))

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register a new sub-agent in the orchestrator.
        Enables open-closed extensibility for future domains (e.g. finance, production).
        """
        self._agents[name] = agent
        logger.info(f"[ManagerAgent] Registered sub-agent: '{name}' ({agent.__class__.__name__})")

    @property
    def registered_agents(self) -> List[str]:
        return list(self._agents.keys())

    def route_intent(self, question: str) -> List[str]:
        """
        Analyze user query to decide which sub-agents to trigger.

        Parameters
        ----------
        question : str
            Executive natural-language query.

        Returns
        -------
        list[str]
            List of agent names to invoke.
        """
        q_lower = (question or "").lower()

        # 1. Check for known strategic cross-domain questions
        for phrase in _CROSS_DOMAIN_PHRASES:
            if phrase in q_lower:
                return [name for name in ["sales", "inventory", "knowledge"] if name in self._agents]

        # 2. Check keyword intersections
        words = set(q_lower.replace("?", "").replace(",", "").replace(".", "").split())
        matched: List[str] = []

        if words & _SALES_KEYWORDS:
            matched.append("sales")
        if words & _INVENTORY_KEYWORDS:
            matched.append("inventory")
        if words & _KNOWLEDGE_KEYWORDS:
            matched.append("knowledge")

        # 3. If query mentions both sales and inventory, also consult enterprise knowledge policy
        if "sales" in matched and "inventory" in matched and "knowledge" in self._agents:
            matched.append("knowledge")

        # 4. Fallback if no specific keyword matched — consult all registered agents
        if not matched:
            matched = list(self._agents.keys())

        return [name for name in matched if name in self._agents]

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Orchestrate full multi-agent Copilot pipeline.

        Parameters
        ----------
        question : str
            Executive question.

        Returns
        -------
        dict[str, Any]
            {
                "status": "success",
                "question": question,
                "answer": natural_language_answer,
                "agents_used": [...],
                "raw_data": {...}
            }
        """
        clean_question = (question or "").strip()
        if not clean_question:
            return {
                "status": "error",
                "message": "Question cannot be empty.",
                "answer": "Please ask a specific business question.",
                "agents_used": [],
                "raw_data": {},
            }

        selected_agents = self.route_intent(clean_question)
        logger.info(f"[ManagerAgent] Routing query='{clean_question}' -> Selected agents={selected_agents}")

        # Execute selected agents concurrently in parallel threads
        merged_data: Dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(len(selected_agents), 1)) as executor:
            future_to_agent = {
                executor.submit(self._agents[name].run, clean_question): name
                for name in selected_agents
                if name in self._agents
            }
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    res = future.result()
                    merged_data[agent_name] = res
                except Exception as exc:
                    logger.error(f"[ManagerAgent] Agent '{agent_name}' failed during execution: {exc}")
                    merged_data[agent_name] = {"domain": agent_name, "status": "error", "error": str(exc)}

        # Build grounded prompt
        system_prompt, user_message = build_copilot_prompt(clean_question, merged_data)

        # Send to LLM
        answer = self._generate_llm_answer(system_prompt, user_message, clean_question, merged_data)

        return {
            "status": "success",
            "question": clean_question,
            "answer": answer,
            "agents_used": selected_agents,
            "raw_data": merged_data,
        }

    def _generate_llm_answer(
        self,
        system_prompt: str,
        user_message: str,
        question: str,
        merged_data: Dict[str, Any],
    ) -> str:
        """
        Invoke LLM with fallback rule-based generation if LLM is offline or unconfigured.
        """
        try:
            provider = get_chat_provider()
            answer = provider.complete(system_prompt=system_prompt, user_message=user_message)
            if answer and answer.strip():
                return answer.strip()
        except Exception as exc:
            logger.warning(f"[ManagerAgent] LLM completion failed or not configured: {exc}. Generating structured fallback.")

        # Deterministic fallback response grounded strictly in returned data
        s = merged_data.get("sales", {})
        inv = merged_data.get("inventory", {})
        k = merged_data.get("knowledge", {})

        parts = []
        if s:
            parts.append(
                f"• **Sales Outlook**: Sales growth is projected at **{s.get('sales_growth', 0)}%** "
                f"with a forecast value of **₹{s.get('forecast', 0):,.2f}** ({s.get('market_trend', 'Stable')} trend). "
                f"Strategy: *{s.get('recommendation', 'Maintain')}*."
            )
        if inv:
            parts.append(
                f"• **Inventory Status**: Stock health is currently **{inv.get('stock_health', 'Normal')}** "
                f"with approximately **{inv.get('remaining_days', 0)} days** of stock remaining. "
                f"Decision: *{inv.get('decision', 'N/A')}* ({inv.get('recommendation', 'N/A')})."
            )
        if k:
            parts.append(
                f"• **Enterprise Policy**: {k.get('policy', 'Follow standard replenishment rules.')}"
            )

        summary_text = "\n".join(parts) if parts else "No real-time domain data was retrieved."
        return (
            f"### Business Copilot Strategic Assessment\n\n"
            f"{summary_text}\n\n"
            f"**Recommendation**: Weigh replenishment needs against projected market growth to maintain safety buffers without over-stocking."
        )
