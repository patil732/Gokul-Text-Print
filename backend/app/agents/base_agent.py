"""
app/agents/base_agent.py
------------------------
Sprint 5 Step 1 — Base Agent Contract & Shared Response Schema

Defines the abstract base class `BaseAgent` and the standard `AgentResponse`
data model that every domain sub-agent must implement and return.

Contract requirements:
  1. `can_handle(query: str) -> bool`: Keyword/intent evaluation without LLM invocation.
  2. `execute(context: dict) -> AgentResponse | dict`: Returns strictly structured JSON data only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AgentResponse:
    """
    Standard response schema returned by all domain sub-agents.

    Attributes
    ----------
    agent_name : str
        Unique identifier for the domain agent (e.g. 'sales', 'inventory', 'knowledge').
    status : str
        Execution status ('success', 'warning', 'error').
    data : dict[str, Any]
        Domain-specific structured key-value payload (strictly metrics/facts, no conversational prose).
    confidence : float
        Confidence score for the returned intelligence (0.0 to 1.0).
    timestamp : str
        ISO 8601 timestamp of execution.
    error : str, optional
        Error message if status == 'error'.
    """

    agent_name: str
    status: str = "success"
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to a standard JSON-serializable dictionary."""
        return asdict(self)


class BaseAgent(ABC):
    """
    Abstract contract for all Sprint 5 domain sub-agents.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent."""
        pass

    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """
        Determine if this agent is relevant to the given user query.

        Parameters
        ----------
        query : str
            Executive or user question.

        Returns
        -------
        bool
            True if the query relates to this agent's domain, False otherwise.
        """
        pass

    @abstractmethod
    def execute(self, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Perform domain-specific analysis and data retrieval.

        Parameters
        ----------
        context : dict[str, Any], optional
            Execution context (e.g. parsed query, horizon, parameters).

        Returns
        -------
        AgentResponse
            Structured response object conforming to the shared AgentResponse schema.
            MUST contain structured facts/metrics only — NEVER natural-language prose.
        """
        pass

    def run(self, question: str = "") -> Dict[str, Any]:
        """
        Convenience wrapper executing the agent with the query in context.
        """
        ctx = {"query": question} if question else {}
        resp = self.execute(ctx)
        if isinstance(resp, AgentResponse):
            return resp.to_dict()
        return resp
