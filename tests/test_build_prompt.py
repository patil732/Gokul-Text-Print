"""
tests/test_build_prompt.py
---------------------------
Sprint 5 — build_prompt() Unit Tests

Validates:
  1. All-three-agent output produces all sections in order.
  2. Sales-only output contains only the Sales section.
  3. Inventory-only output contains only the Inventory section.
  4. Knowledge-only output contains only the Knowledge section.
  5. Sales + Inventory (no knowledge) omits the Policy section.
  6. Inventory + Knowledge (no sales) omits the Sales section.
  7. Empty agent_outputs produces the fallback notice.
  8. Question and directive always appear at the end.
  9. AgentResponse.to_dict() wrapper is automatically unwrapped.
  10. Numeric formatting: sales_growth shown as %, forecast with ₹ symbol.
  11. Sources are rendered as a comma-separated string (not a list literal).
  12. Missing optional fields inside a section are gracefully omitted.
"""

from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.agents.prompt_builder import build_prompt

# ─────────────────────────────────────────────────────────────────────────── #
# Fixtures — sample agent output payloads
# ─────────────────────────────────────────────────────────────────────────── #

SALES_DATA = {
    "sales_growth": -12.4,
    "forecast": 15000.0,
    "market_trend": "Declining",
    "top_product": "Cotton Fabric (Grade A)",
    "recommendation": "Increase marketing",
    "forecast_period": "30_days",
    "confidence": 0.82,
}

INVENTORY_DATA = {
    "stock_health": "Critical",
    "remaining_days": 4,
    "decision": "Reorder Required",
    "recommendation": "Restock Immediately",
    "confidence": 0.92,
    "confidence_level": "High",
}

KNOWLEDGE_DATA = {
    "policy": "Reorder when stock reaches safety level of 200 units.",
    "sources": ["Inventory Policy.pdf", "Procurement_SOP.pdf"],
    "source_details": [{"document": "Inventory Policy.pdf", "page": 3, "score": 0.94}],
    "relevant_chunks": 3,
    "query_used": "reorder policy",
}

QUESTION_FULL = "Should inventory be increased?"
QUESTION_SALES = "What is our 30-day sales outlook?"
QUESTION_KNOWLEDGE = "What does company policy say about reordering?"


# ─────────────────────────────────────────────────────────────────────────── #
# 1. All-three-agent combination
# ─────────────────────────────────────────────────────────────────────────── #

class TestAllThreeAgents:

    @pytest.fixture(autouse=True)
    def _prompt(self):
        self.prompt = build_prompt(
            {"sales": SALES_DATA, "inventory": INVENTORY_DATA, "knowledge": KNOWLEDGE_DATA},
            QUESTION_FULL,
        )

    def test_returns_string(self):
        assert isinstance(self.prompt, str)

    def test_contains_sales_header(self):
        assert "=== Sales Intelligence ===" in self.prompt

    def test_contains_inventory_header(self):
        assert "=== Inventory Intelligence ===" in self.prompt

    def test_contains_policy_header(self):
        assert "=== Company Policy ===" in self.prompt

    def test_sections_appear_in_order(self):
        sales_pos = self.prompt.index("=== Sales Intelligence ===")
        inv_pos = self.prompt.index("=== Inventory Intelligence ===")
        policy_pos = self.prompt.index("=== Company Policy ===")
        assert sales_pos < inv_pos < policy_pos

    def test_question_appears_at_end(self):
        q_pos = self.prompt.index(f"Question: {QUESTION_FULL}")
        directive_pos = self.prompt.index("Provide a business recommendation with justification.")
        assert q_pos < directive_pos
        # Nothing comes after the directive
        assert self.prompt.endswith("Provide a business recommendation with justification.")

    def test_sales_growth_formatted_as_percentage(self):
        assert "-12.4%" in self.prompt

    def test_forecast_formatted_with_rupee(self):
        assert "₹" in self.prompt
        assert "15,000" in self.prompt

    def test_inventory_health_present(self):
        assert "Critical" in self.prompt

    def test_remaining_days_present(self):
        assert "4" in self.prompt

    def test_policy_text_present(self):
        assert "Reorder when stock reaches safety level" in self.prompt

    def test_sources_as_comma_string(self):
        assert "Inventory Policy.pdf" in self.prompt
        # Must NOT be rendered as Python list literal
        assert "[" not in self.prompt or "Source" not in self.prompt.split("[")[0]


# ─────────────────────────────────────────────────────────────────────────── #
# 2. Single-agent combinations
# ─────────────────────────────────────────────────────────────────────────── #

class TestSalesOnly:

    @pytest.fixture(autouse=True)
    def _prompt(self):
        self.prompt = build_prompt({"sales": SALES_DATA}, QUESTION_SALES)

    def test_contains_sales_section(self):
        assert "=== Sales Intelligence ===" in self.prompt

    def test_no_inventory_section(self):
        assert "=== Inventory Intelligence ===" not in self.prompt

    def test_no_policy_section(self):
        assert "=== Company Policy ===" not in self.prompt

    def test_question_appended(self):
        assert f"Question: {QUESTION_SALES}" in self.prompt

    def test_directive_present(self):
        assert "Provide a business recommendation with justification." in self.prompt


class TestInventoryOnly:

    @pytest.fixture(autouse=True)
    def _prompt(self):
        self.prompt = build_prompt({"inventory": INVENTORY_DATA}, "How critical is our stock situation?")

    def test_contains_inventory_section(self):
        assert "=== Inventory Intelligence ===" in self.prompt

    def test_no_sales_section(self):
        assert "=== Sales Intelligence ===" not in self.prompt

    def test_no_policy_section(self):
        assert "=== Company Policy ===" not in self.prompt

    def test_stock_health_present(self):
        assert "Critical" in self.prompt

    def test_remaining_days_present(self):
        assert "4" in self.prompt


class TestKnowledgeOnly:

    @pytest.fixture(autouse=True)
    def _prompt(self):
        self.prompt = build_prompt({"knowledge": KNOWLEDGE_DATA}, QUESTION_KNOWLEDGE)

    def test_contains_policy_section(self):
        assert "=== Company Policy ===" in self.prompt

    def test_no_sales_section(self):
        assert "=== Sales Intelligence ===" not in self.prompt

    def test_no_inventory_section(self):
        assert "=== Inventory Intelligence ===" not in self.prompt

    def test_policy_text_present(self):
        assert "200 units" in self.prompt

    def test_sources_listed(self):
        assert "Inventory Policy.pdf" in self.prompt


# ─────────────────────────────────────────────────────────────────────────── #
# 3. Two-agent combinations
# ─────────────────────────────────────────────────────────────────────────── #

class TestSalesAndInventoryNoKnowledge:

    @pytest.fixture(autouse=True)
    def _prompt(self):
        self.prompt = build_prompt(
            {"sales": SALES_DATA, "inventory": INVENTORY_DATA},
            QUESTION_FULL,
        )

    def test_has_both_sections(self):
        assert "=== Sales Intelligence ===" in self.prompt
        assert "=== Inventory Intelligence ===" in self.prompt

    def test_no_policy_section(self):
        assert "=== Company Policy ===" not in self.prompt

    def test_question_present(self):
        assert f"Question: {QUESTION_FULL}" in self.prompt


class TestInventoryAndKnowledgeNoSales:

    @pytest.fixture(autouse=True)
    def _prompt(self):
        self.prompt = build_prompt(
            {"inventory": INVENTORY_DATA, "knowledge": KNOWLEDGE_DATA},
            "Should we trigger an emergency restock?",
        )

    def test_has_inventory_and_policy(self):
        assert "=== Inventory Intelligence ===" in self.prompt
        assert "=== Company Policy ===" in self.prompt

    def test_no_sales_section(self):
        assert "=== Sales Intelligence ===" not in self.prompt


class TestSalesAndKnowledgeNoInventory:

    @pytest.fixture(autouse=True)
    def _prompt(self):
        self.prompt = build_prompt(
            {"sales": SALES_DATA, "knowledge": KNOWLEDGE_DATA},
            "What does policy say about our declining sales?",
        )

    def test_has_sales_and_policy(self):
        assert "=== Sales Intelligence ===" in self.prompt
        assert "=== Company Policy ===" in self.prompt

    def test_no_inventory_section(self):
        assert "=== Inventory Intelligence ===" not in self.prompt


# ─────────────────────────────────────────────────────────────────────────── #
# 4. Empty / fallback
# ─────────────────────────────────────────────────────────────────────────── #

class TestEmptyAgentOutputs:

    def test_empty_dict_shows_fallback(self):
        prompt = build_prompt({}, "What should we do?")
        assert "No domain intelligence was retrieved" in prompt

    def test_empty_dict_still_has_question(self):
        prompt = build_prompt({}, "What should we do?")
        assert "Question: What should we do?" in prompt

    def test_empty_dict_still_has_directive(self):
        prompt = build_prompt({}, "What should we do?")
        assert "Provide a business recommendation with justification." in prompt

    def test_unknown_agent_key_ignored(self):
        # Keys that are not 'sales', 'inventory', 'knowledge' are silently ignored
        prompt = build_prompt({"finance": {"profit": 100}}, "What happened?")
        assert "=== Sales Intelligence ===" not in prompt
        assert "No domain intelligence was retrieved" in prompt


# ─────────────────────────────────────────────────────────────────────────── #
# 5. AgentResponse.to_dict() wrapper auto-unwrap
# ─────────────────────────────────────────────────────────────────────────── #

class TestAgentResponseWrapperUnwrap:

    def test_full_agent_response_dict_is_unwrapped(self):
        """build_prompt must work when passed AgentResponse.to_dict() directly."""
        wrapped = {
            "agent_name": "sales",
            "status": "success",
            "confidence": 0.82,
            "timestamp": "2026-09-09T13:00:00",
            "error": None,
            "data": SALES_DATA,
        }
        prompt = build_prompt({"sales": wrapped}, QUESTION_SALES)
        assert "Sales Growth:" in prompt
        assert "₹15,000" in prompt

    def test_inventory_full_response_dict_unwrapped(self):
        wrapped = {
            "agent_name": "inventory",
            "status": "success",
            "confidence": 0.92,
            "timestamp": "2026-09-09T13:00:00",
            "error": None,
            "data": INVENTORY_DATA,
        }
        prompt = build_prompt({"inventory": wrapped}, "Inventory check?")
        assert "Inventory:       Critical" in prompt


# ─────────────────────────────────────────────────────────────────────────── #
# 6. Graceful handling of missing optional fields within a section
# ─────────────────────────────────────────────────────────────────────────── #

class TestMissingOptionalFields:

    def test_sales_section_with_only_growth(self):
        """Partial sales data should not raise and should render what is present."""
        prompt = build_prompt({"sales": {"sales_growth": 5.2}}, "Sales update?")
        assert "=== Sales Intelligence ===" in prompt
        assert "Sales Growth:" in prompt
        # Fields not provided should simply be absent — no 'N/A' clutter
        assert "Forecast:" not in prompt
        assert "Market Trend:" not in prompt

    def test_inventory_section_with_only_health(self):
        prompt = build_prompt({"inventory": {"stock_health": "Healthy"}}, "Status?")
        assert "Inventory:       Healthy" in prompt
        assert "Remaining Days:" not in prompt

    def test_knowledge_section_with_no_sources(self):
        prompt = build_prompt(
            {"knowledge": {"policy": "Order weekly."}},
            "Policy check?",
        )
        assert "Company Policy:  Order weekly." in prompt
        assert "Sources:" not in prompt

    def test_positive_growth_formatted_with_plus_sign(self):
        prompt = build_prompt({"sales": {"sales_growth": 8.5}}, "Good news?")
        assert "+8.5%" in prompt
