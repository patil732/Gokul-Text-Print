"""
app/agents/prompt_builder.py
----------------------------
Prompt builder for the Multi-Agent Executive Business Copilot.
Formats merged JSON intelligence from specialized domain agents
into a structured, grounded prompt for the Manager Agent's LLM.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

_COPILOT_SYSTEM_PROMPT = """You are the Gokul Tex Print Executive Business Copilot.
Your job is to synthesize multi-domain intelligence (Sales Forecasting, Inventory Intelligence, Enterprise SOPs/Policies) to provide clear, actionable, executive-level recommendations.

Core Guidelines:
1. Grounding: Base your analysis and recommendations STRICTLY on the provided domain intelligence facts below.
2. Cross-Domain Synthesis: When conflicting signals exist (e.g. declining sales growth vs. critical low stock), explicitly weigh both aspects and propose a balanced business solution.
3. Clarity & Conciseness: Provide a direct, professional answer in 2-4 structured paragraphs or bullet points. Avoid filler text.
4. Transparency: Reference specific facts, numbers, and cited document sources provided in the context.
"""


# ─────────────────────────────────────────────────────────────────────────── #
# Public API — primary lightweight formatter
# ─────────────────────────────────────────────────────────────────────────── #

def build_prompt(
    agent_outputs: Dict[str, Any],
    original_question: str,
) -> str:
    """
    Merge whichever agents' JSON responses were collected (any subset of
    'sales', 'inventory', 'knowledge') into a clearly labelled, flat
    key-value structured prompt block and append the original question.

    Each domain section is included only when its key is present in
    ``agent_outputs``; missing sections are silently omitted.

    Parameters
    ----------
    agent_outputs : dict[str, Any]
        Keyed by agent name.  Each value may be either:
        - An ``AgentResponse.data`` dict (preferred), or
        - A full ``AgentResponse.to_dict()`` dict (the ``data`` sub-key is
          automatically unwrapped).
    original_question : str
        The executive's original natural-language question.

    Returns
    -------
    str
        A ready-to-send prompt string.

    Examples
    --------
    >>> prompt = build_prompt(
    ...     {"sales": {"sales_growth": -12, "forecast": 15000,
    ...                "recommendation": "Increase marketing",
    ...                "market_trend": "Declining"},
    ...      "inventory": {"stock_health": "Critical", "remaining_days": 4,
    ...                    "recommendation": "Restock"}},
    ...     "Should inventory be increased?"
    ... )
    """
    lines: List[str] = []

    # ── Helper: unwrap AgentResponse.to_dict() if needed ──────────────────── #
    def _data(raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
            return raw["data"]
        return raw if isinstance(raw, dict) else {}

    # ── 1. Sales section ──────────────────────────────────────────────────── #
    if "sales" in agent_outputs:
        s = _data(agent_outputs["sales"])
        lines.append("=== Sales Intelligence ===")

        growth = s.get("sales_growth")
        if growth is not None:
            lines.append(f"Sales Growth:    {growth:+.1f}%" if isinstance(growth, (int, float))
                         else f"Sales Growth:    {growth}")

        forecast = s.get("forecast")
        if forecast is not None:
            lines.append(f"Forecast:        ₹{forecast:,.0f}" if isinstance(forecast, (int, float))
                         else f"Forecast:        {forecast}")

        trend = s.get("market_trend")
        if trend:
            lines.append(f"Market Trend:    {trend}")

        top_product = s.get("top_product")
        if top_product:
            lines.append(f"Top Product:     {top_product}")

        rec = s.get("recommendation")
        if rec:
            lines.append(f"Recommendation:  {rec}")

        lines.append("")  # blank separator

    # ── 2. Inventory section ──────────────────────────────────────────────── #
    if "inventory" in agent_outputs:
        inv = _data(agent_outputs["inventory"])
        lines.append("=== Inventory Intelligence ===")

        health = inv.get("stock_health")
        if health:
            lines.append(f"Inventory:       {health}")

        days = inv.get("remaining_days")
        if days is not None:
            lines.append(f"Remaining Days:  {days}")

        decision = inv.get("decision")
        if decision:
            lines.append(f"ML Decision:     {decision}")

        rec = inv.get("recommendation")
        if rec:
            lines.append(f"Recommendation:  {rec}")

        lines.append("")

    # ── 3. Knowledge / Policy section ─────────────────────────────────────── #
    if "knowledge" in agent_outputs:
        k = _data(agent_outputs["knowledge"])
        lines.append("=== Company Policy ===")

        policy = k.get("policy")
        if policy:
            lines.append(f"Company Policy:  {policy}")

        # sources may be list[str] or list[dict]
        raw_sources = k.get("sources") or []
        src_names: List[str] = []
        for s in raw_sources:
            src_names.append(s.get("document", str(s)) if isinstance(s, dict) else str(s))
        if src_names:
            lines.append(f"Sources:         {', '.join(src_names)}")

        lines.append("")

    # ── Fallback when no agents contributed ───────────────────────────────── #
    if not any(k in agent_outputs for k in ("sales", "inventory", "knowledge")):
        lines.append("(No domain intelligence was retrieved.)")
        lines.append("")

    # ── Question + directive ──────────────────────────────────────────────── #
    lines.append(f"Question: {original_question.strip()}")
    lines.append("Provide a business recommendation with justification.")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────── #
# Legacy / LLM-facing detailed formatter (kept intact)
# ─────────────────────────────────────────────────────────────────────────── #

def build_copilot_prompt(
    question: str,
    merged_data: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Format merged domain data into a grounded context prompt.

    Parameters
    ----------
    question : str
        The executive's original question.
    merged_data : dict[str, Any]
        Dictionary of sub-agent responses keyed by agent name:
        {'sales': {...}, 'inventory': {...}, 'knowledge': {...}}

    Returns
    -------
    tuple[str, str]
        (system_prompt, user_message)
    """
    context_blocks: List[str] = []

    # 1. Sales domain block
    if "sales" in merged_data and isinstance(merged_data["sales"], dict):
        s = merged_data["sales"]
        s_lines = [
            f"- Sales Growth Rate: {s.get('sales_growth', 'N/A')}% (Period: {s.get('forecast_period', '30_days')})",
            f"- Projected Forecast Revenue: ₹{s.get('forecast', 0):,.2f}" if isinstance(s.get('forecast'), (int, float)) else f"- Forecast: {s.get('forecast', 'N/A')}",
            f"- Sales Strategy Recommendation: {s.get('recommendation', 'N/A')}",
            f"- Market Demand Trend: {s.get('market_trend', 'N/A')}",
            f"- Primary Product Focus: {s.get('top_product', 'N/A')}",
            f"- Prediction Confidence: {round(float(s.get('confidence', 0.8)) * 100, 1)}%",
        ]
        context_blocks.append("[SALES INTELLIGENCE]\n" + "\n".join(s_lines))

    # 2. Inventory domain block
    if "inventory" in merged_data and isinstance(merged_data["inventory"], dict):
        inv = merged_data["inventory"]
        inv_lines = [
            f"- Stock Health Status: {inv.get('stock_health', 'N/A')}",
            f"- Decision Classifier: {inv.get('decision', 'N/A')}",
            f"- Estimated Stock Remaining: {inv.get('remaining_days', 'N/A')} days",
            f"- Inventory Action Recommended: {inv.get('recommendation', 'N/A')}",
            f"- Evaluation Confidence: {round(float(inv.get('confidence', 0.85)) * 100, 1)}% ({inv.get('confidence_level', 'High')})",
        ]
        context_blocks.append("[INVENTORY INTELLIGENCE]\n" + "\n".join(inv_lines))

    # 3. Knowledge / Policy domain block
    if "knowledge" in merged_data and isinstance(merged_data["knowledge"], dict):
        k = merged_data["knowledge"]
        sources = k.get("sources", [])
        # sources may be list[str] (new shape) or list[dict] (legacy shape)
        src_parts = []
        for s in sources:
            if isinstance(s, dict):
                src_parts.append(f"{s.get('document', 'Doc')} (Page {s.get('page', 1)})")
            else:
                src_parts.append(str(s))
        src_formatted = ", ".join(src_parts) if src_parts else "Standard Operating Policy"
        k_lines = [
            f"- Enterprise Policy Statement: {k.get('policy', 'N/A')}",
            f"- Verified Sources / Documents: {src_formatted}",
        ]
        context_blocks.append("[ENTERPRISE POLICIES & SOPs]\n" + "\n".join(k_lines))

    # Fallback if no specific sub-agent returned data
    if not context_blocks:
        formatted_context = "No specific domain intelligence was retrieved."
    else:
        formatted_context = "\n\n".join(context_blocks)

    user_message = f"""Executive Question:
{question}

=== REAL-TIME DOMAIN INTELLIGENCE ===
{formatted_context}

Please provide an objective, data-grounded strategic recommendation for the executive based on the intelligence above."""

    return _COPILOT_SYSTEM_PROMPT, user_message
