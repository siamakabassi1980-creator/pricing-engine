"""Perception service — parse Farsi natural-language request.

Takes request_text + catalog (product_id -> name) + catalog_prices
(product_id -> price), returns a PurchaseRequest. The LLM extracts
product_id and qty ONLY — prices are injected from the catalog, never
trusted from LLM output (security decision, data-model.md).

If the LLM returns garbage (unparseable JSON, missing fields), returns
a PurchaseRequest with an empty items list — the Decision layer will
then price it as base=0, which is safe. But we never let LLM-supplied
prices through.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from app.decision.models import LineItemRequest, PurchaseRequest
from app.perception.llm_adapter import LLMAdapter, parse_json_response
from app.perception.prompts import build_parse_prompt

logger = logging.getLogger(__name__)


def parse_request(
    request_text: str,
    catalog: dict[str, str],
    catalog_prices: dict[str, Decimal],
    llm: LLMAdapter,
) -> PurchaseRequest:
    """Parse a Farsi request into a PurchaseRequest.

    Args:
        request_text: The user's natural-language request (Farsi).
        catalog: product_id -> product_name (Farsi).
        catalog_prices: product_id -> unit_price. The PRICE IS ALWAYS TAKEN
            FROM HERE, never from the LLM. This is a security-critical rule.
        llm: The LLM adapter (DeepSeek in prod, DummyLLM in tests).

    Returns:
        PurchaseRequest with items. If parsing fails, items may be empty.
    """
    # Build catalog id -> name for prompt.
    prompt = build_parse_prompt(catalog, request_text)
    raw = llm.complete(prompt)

    try:
        parsed = parse_json_response(raw)
    except ValueError:
        logger.warning("LLM returned unparseable response: %s", raw[:200])
        return PurchaseRequest(items=[], customer_tier="regular", season="normal")

    # Extract items. The LLM provides product_id and qty ONLY.
    raw_items = parsed.get("items", []) if isinstance(parsed, dict) else []
    items: list[LineItemRequest] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        product_id = raw_item.get("product_id")
        qty = raw_item.get("qty")
        if not isinstance(product_id, str) or not isinstance(qty, int):
            continue
        # SECURITY: price comes from catalog, NEVER from LLM output.
        # Even if the LLM returned a 'price' field, we ignore it entirely.
        if product_id not in catalog_prices:
            logger.warning("LLM returned unknown product_id: %s", product_id)
            continue
        items.append(
            LineItemRequest(
                product_id=product_id,
                qty=qty,
                unit_price=catalog_prices[product_id],
            )
        )

    # customer_tier and season are NOT parsed from the request text in MVP;
    # they come from the request context (passed separately). Default here.
    return PurchaseRequest(items=items, customer_tier="regular", season="normal")
