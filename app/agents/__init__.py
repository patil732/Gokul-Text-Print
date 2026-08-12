"""
app/agents
----------
Multi-Agent AI Orchestration Layer for Gokul Tex Print.

Exports:
  - BaseAgent
  - SalesAgent
  - InventoryAgent
  - KnowledgeAgent
  - ManagerAgent
  - build_copilot_prompt
"""

from app.agents.base import BaseAgent, call_api
from app.agents.sales_agent import SalesAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.manager_agent import ManagerAgent
from app.agents.prompt_builder import build_copilot_prompt

__all__ = [
    "BaseAgent",
    "call_api",
    "SalesAgent",
    "InventoryAgent",
    "KnowledgeAgent",
    "ManagerAgent",
    "build_copilot_prompt",
]
