"""
app/agents/manager_agent.py
---------------------------
Manager / Orchestrator Agent — Sprint 5

The ONLY component that touches the LLM.
Responsibilities (in strict order):
  1. Accept the CEO's natural-language question.
  2. Call can_handle(query) on every registered agent to route intent.
  3. Execute each selected agent's execute() in parallel (ThreadPoolExecutor).
  4. Merge the structured AgentResponse objects.
  5. Build a grounded prompt via prompt_builder.build_prompt().
  6. Send the prompt to the config-driven LLM provider and return the answer.

Design constraints:
  - NEVER queries database tables directly.
  - NEVER hard-codes domain logic — it only calls the BaseAgent interface.
  - Registry is a plain list; adding a FinanceAgent requires ZERO changes here:
        mgr.register_agent(FinanceAgent())
"""

from __future__ import annotations

import concurrent.futures
from typing import Any, Dict, List, Optional

from app.agents.base_agent import AgentResponse, BaseAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.prompt_builder import build_prompt, build_copilot_prompt
from app.agents.sales_agent import SalesAgent
from app.rag.chat_service import get_chat_provider
from utils.logger import logger


class ManagerAgent:
    """
    Central Multi-Agent Orchestrator for the Executive Business Copilot.

    The registry is a plain list of BaseAgent instances — the Manager never
    references concrete agent types after __init__, so adding a FinanceAgent,
    ProductionAgent, etc. only requires calling register_agent().
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        self._base_url = base_url
        # Registry: ordered list of BaseAgent instances
        self._registry: List[BaseAgent] = []
        # Register default sub-agents (the only place concrete classes appear)
        self.register_agent(SalesAgent(base_url=base_url))
        self.register_agent(InventoryAgent(base_url=base_url))
        self.register_agent(KnowledgeAgent(base_url=base_url))

    # ── Registry ──────────────────────────────────────────────────────────── #

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Add an agent to the registry.

        Enables open-closed extensibility:
            mgr.register_agent(FinanceAgent())
        No other change to ManagerAgent is needed.
        """
        self._registry.append(agent)
        logger.info(
            f"[ManagerAgent] Registered sub-agent: '{agent.name}' ({agent.__class__.__name__})"
        )

    @property
    def registered_agents(self) -> List[str]:
        """Names of all registered agents, in registration order."""
        return [a.name for a in self._registry]

    # ── Routing (delegates to agent.can_handle) ────────────────────────────── #

    def _select_agents(self, query: str) -> List[BaseAgent]:
        """
        Ask every registered agent whether it can handle the query.

        Uses each agent's own can_handle() so the Manager has no domain
        routing knowledge of its own.  Additionally, if any two or more
        specialist agents claim the query, the knowledge agent is always
        also included (cross-domain synthesis benefit), as long as it is
        registered.  KnowledgeAgent's own can_handle() already acts as
        a fallback for truly unrecognised queries.
        """
        selected = [agent for agent in self._registry if agent.can_handle(query)]

        # Cross-domain boost: if ≥2 specialists are selected, ensure the
        # knowledge agent is also included for policy context
        if len(selected) >= 2:
            selected_names = {a.name for a in selected}
            for agent in self._registry:
                if agent.name == "knowledge" and agent.name not in selected_names:
                    selected.append(agent)
                    break

        return selected

    # ── Main orchestration entry point ─────────────────────────────────────── #

    def orchestrate(self, question: str) -> Dict[str, Any]:
        """
        Full multi-agent pipeline returning a rich response dict.

        Parameters
        ----------
        question : str
            CEO's natural-language question.

        Returns
        -------
        dict with keys:
            status        : "success" | "error"
            question      : echoed input
            answer        : LLM-generated natural-language recommendation
            agents_used   : list[str] of agent names that were triggered
            confidence    : float — mean confidence across active agents
            agent_details : dict[str, AgentResponse.to_dict()] per agent
        """
        clean_question = (question or "").strip()
        if not clean_question:
            return {
                "status": "error",
                "question": question,
                "answer": "Please ask a specific business question.",
                "agents_used": [],
                "confidence": 0.0,
                "agent_details": {},
            }

        # Step 2 — route via can_handle()
        selected = self._select_agents(clean_question)
        agents_used = [a.name for a in selected]
        logger.info(
            f"[ManagerAgent] Routing query='{clean_question}' -> "
            f"Selected agents={agents_used}"
        )

        # Step 3 — parallel execute()
        agent_responses: Dict[str, AgentResponse] = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(len(selected), 1)
        ) as pool:
            future_to_agent = {
                pool.submit(agent.execute, {"query": clean_question}): agent
                for agent in selected
            }
            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    resp: AgentResponse = future.result()
                    agent_responses[agent.name] = resp
                except Exception as exc:
                    logger.error(
                        f"[ManagerAgent] Agent '{agent.name}' execute() failed: {exc}"
                    )
                    agent_responses[agent.name] = AgentResponse(
                        agent_name=agent.name,
                        status="error",
                        data={},
                        confidence=0.0,
                        error=str(exc),
                    )

        # Step 4 — merge structured outputs for prompt builder
        # build_prompt() receives {agent_name: AgentResponse.data} dicts
        merged_for_prompt: Dict[str, Any] = {
            name: resp.data for name, resp in agent_responses.items()
        }

        # Step 5 — build prompt using the new flat formatter
        prompt_text = build_prompt(merged_for_prompt, clean_question)

        # Confidence = mean of all agent confidences (error agents score 0)
        confidence = (
            round(
                sum(r.confidence for r in agent_responses.values()) /
                len(agent_responses),
                4,
            )
            if agent_responses else 0.0
        )

        # Step 6 — call LLM
        answer = self._call_llm(prompt_text, merged_for_prompt, clean_question)

        return {
            "status": "success",
            "question": clean_question,
            "answer": answer,
            "agents_used": agents_used,
            "confidence": confidence,
            "agent_details": {
                name: resp.to_dict() for name, resp in agent_responses.items()
            },
        }

    # ── LLM call with deterministic fallback ───────────────────────────────── #

    def _call_llm(
        self,
        prompt_text: str,
        merged_data: Dict[str, Any],
        question: str,
    ) -> str:
        """
        Send prompt_text to the configured LLM; fall back to a deterministic
        structured summary if the LLM is offline or unconfigured.
        """
        try:
            provider = get_chat_provider()
            # Use the flat prompt as the user message; system prompt is implicit
            answer = provider.complete(
                system_prompt=(
                    "You are the Gokul Tex Print Executive Business Copilot. "
                    "Synthesize the structured data below into a concise, "
                    "actionable recommendation. Base your answer strictly on "
                    "the provided facts — do not invent data."
                ),
                user_message=prompt_text,
            )
            if answer and answer.strip():
                return answer.strip()
        except Exception as exc:
            logger.warning(
                f"[ManagerAgent] LLM call failed: {exc}. Using structured fallback."
            )

        # Deterministic fallback — grounded only in returned data
        s = merged_data.get("sales", {})
        inv = merged_data.get("inventory", {})
        k = merged_data.get("knowledge", {})

        parts: List[str] = []
        if s:
            growth = s.get("sales_growth", 0)
            forecast = s.get("forecast", 0)
            trend = s.get("market_trend", "Stable")
            rec = s.get("recommendation", "Maintain")
            try:
                parts.append(
                    f"• **Sales Outlook**: Sales growth is projected at "
                    f"**{growth:+.1f}%** with a forecast of **₹{float(forecast):,.0f}** "
                    f"({trend} trend). Strategy: *{rec}*."
                )
            except (TypeError, ValueError):
                parts.append(f"• **Sales Outlook**: Growth={growth}, Forecast={forecast}.")

        if inv:
            health = inv.get("stock_health", "Normal")
            days = inv.get("remaining_days", "N/A")
            decision = inv.get("decision", "N/A")
            rec = inv.get("recommendation", "N/A")
            parts.append(
                f"• **Inventory Status**: Stock health is **{health}** with "
                f"**{days} days** of stock remaining. "
                f"Decision: *{decision}* — {rec}."
            )
        if k:
            policy = k.get("policy", "Follow standard replenishment rules.")
            parts.append(f"• **Enterprise Policy**: {policy}")

        body = "\n".join(parts) if parts else "No real-time domain data was retrieved."
        return (
            "### Business Copilot Strategic Assessment\n\n"
            f"{body}\n\n"
            "**Recommendation**: Weigh replenishment needs against projected "
            "market growth to maintain safety buffers without over-stocking."
        )

    # ── Backward-compatible ask() (used by /api/agent/ask + existing tests) ── #

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Backward-compatible wrapper around orchestrate().

        Returns the same schema as before (raw_data instead of agent_details)
        so existing routes and tests remain unbroken.
        """
        result = self.orchestrate(question)
        # Map new field names -> legacy field names
        result["raw_data"] = {
            name: detail.get("data", detail)
            for name, detail in result.get("agent_details", {}).items()
        }
        return result

    # ── Legacy registry dict API (for backward compat with old register_agent calls) #

    def _get_agents_dict(self) -> Dict[str, BaseAgent]:
        return {a.name: a for a in self._registry}

    # Keep the old route_intent for backward compat with any callers
    def route_intent(self, question: str) -> List[str]:
        return [a.name for a in self._select_agents(question)]
