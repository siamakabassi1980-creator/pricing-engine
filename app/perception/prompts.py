"""Prompt templates for the Perception layer.

Perception's job: take a Farsi natural-language request and return a
JSON array of {product_id, qty} pairs. It does NOT return prices —
prices are injected from the catalog by the service, never trusted from
the LLM (security decision documented in data-model.md).
"""

from __future__ import annotations

PARSE_PROMPT_TEMPLATE = """\
You are a pricing request parser. Given a Farsi purchase request and a
product catalog, extract the requested items as JSON.

Catalog (product_id: name):
{catalog_lines}

User request (Farsi):
"{request_text}"

Return ONLY a JSON object (no prose, no code fences) of this exact shape:
{{
  "items": [
    {{"product_id": "<id from catalog>", "qty": <positive integer>}}
  ]
}}

Rules:
- Match products by their Farsi name in the catalog.
- qty must be a positive integer.
- Do NOT include prices. Prices are looked up server-side.
- If a product is not in the catalog, omit it from the response.
"""


def build_parse_prompt(catalog: dict[str, str], request_text: str) -> str:
    """Build the prompt for parsing a Farsi request against a catalog."""
    catalog_lines = "\n".join(f"{pid}: {name}" for pid, name in catalog.items())
    return PARSE_PROMPT_TEMPLATE.format(
        catalog_lines=catalog_lines,
        request_text=request_text,
    )
