"""Generation service — produce a Farsi invoice text from a PriceResult.

BOUNDARY RULE (per T3.1, agreed with developer):
    Generation is ONLY called for PriceResult with status="priced".
    For status="rejected", the API layer returns rejection_reason directly
    (HTTP 422) without calling the LLM — this avoids a wasteful, slow LLM
    round-trip just to paraphrase an already-human-readable rejection.

This module enforces the rule defensively: generate_invoice() returns the
rejection_reason unchanged if given a rejected result, so misuse at the
call site cannot trigger an LLM call. But callers SHOULD branch on status
before calling, to keep the contract explicit.
"""

from __future__ import annotations

import json
import logging

from app.decision.models import PriceResult
from app.generation.prompts import build_invoice_prompt
from app.perception.llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)


def generate_invoice(result: PriceResult, llm: LLMAdapter) -> str:
    """Generate a Farsi invoice text for a PriceResult.

    Args:
        result: The pricing result. MUST have status="priced" in normal use.
        llm: The LLM adapter (shared with Perception — same provider).

    Returns:
        Farsi invoice text. If result.status == "rejected", returns the
        rejection_reason unchanged WITHOUT calling the LLM (defensive).
    """
    # Boundary rule enforced defensively: never call LLM for a rejection.
    if result.status == "rejected":
        logger.debug("Skipping LLM for rejected result (boundary rule)")
        return result.rejection_reason or "درخواست رد شد"

    # Build a compact JSON description of the pricing for the LLM.
    pricing_payload = {
        "line_items": [
            {
                "product_name": item.product_name,
                "qty": item.qty,
                "line_total": str(item.line_total),
            }
            for item in result.line_items
        ],
        "base": str(result.base),
        "discount": str(result.discount),
        "discount_reason": result.discount_reason,
        "subtotal": str(result.subtotal),
        "tax": str(result.tax),
        "total": str(result.total),
    }
    prompt = build_invoice_prompt(json.dumps(pricing_payload, ensure_ascii=False))
    return llm.complete(prompt)
