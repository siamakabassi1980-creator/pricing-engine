"""Prompt template for qualitative anomaly analysis (LLM-only).

This is the part EXEMPT from PBT (ADR-0002). The LLM judges whether a
request is suspicious based on qualitative factors: unusual item combos,
suspicious tone, patterns inconsistent with normal customer behavior.
"""

from __future__ import annotations

ANOMALY_PROMPT_TEMPLATE = """\
You are an anomaly detector for a pricing system. Given a purchase request
and its pricing result, determine if it is suspicious or anomalous.

Request text: "{request_text}"
Pricing summary: base={base}, total={total}, item_count={item_count}
Deterministic signals already flagged: {deterministic_signals}

Consider ONLY qualitative factors that the deterministic signals might miss:
- Unusual combination of items (e.g., only the most expensive product in bulk)
- Tone suggesting testing or probing the system
- Patterns inconsistent with normal purchasing behavior

Return ONLY a JSON object (no prose, no fences):
{{"suspicious": true/false, "reason": "<brief Farsi explanation if suspicious>"}}

If not suspicious, return: {{"suspicious": false, "reason": ""}}
"""


def build_anomaly_prompt(
    request_text: str,
    base: str,
    total: str,
    item_count: int,
    deterministic_signals: list[str],
) -> str:
    """Build the prompt for qualitative anomaly analysis."""
    return ANOMALY_PROMPT_TEMPLATE.format(
        request_text=request_text,
        base=base,
        total=total,
        item_count=item_count,
        deterministic_signals=deterministic_signals if deterministic_signals else "[]",
    )
