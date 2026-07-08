"""Prompt templates for the Generation layer.

Generation's job: take a PriceResult (status='priced') and produce a
readable Farsi invoice text. It is ONLY called for priced results —
rejected results bypass Generation entirely (their rejection_reason is
returned directly by the API layer, no LLM call needed).
"""

from __future__ import annotations

INVOICE_PROMPT_TEMPLATE = """\
You are an invoice generator. Given pricing details in JSON, produce a
clear, polite Farsi invoice text for the customer.

Pricing details:
{pricing_json}

Produce ONLY the invoice text in Farsi (no code fences, no JSON). Format:
- List each line item: "<qty> عدد <product_name> — <line_total> تومان"
- Show: جمع کل، تخفیف اعمال‌شده (if any) با دلیل، مالیات بر ارزش افزوده،
  مبلغ نهایی قابل پرداخت.
- Use Persian digits where natural.
- Keep it concise and professional.
"""


def build_invoice_prompt(pricing_json: str) -> str:
    """Build the prompt for generating a Farsi invoice from pricing JSON."""
    return INVOICE_PROMPT_TEMPLATE.format(pricing_json=pricing_json)
