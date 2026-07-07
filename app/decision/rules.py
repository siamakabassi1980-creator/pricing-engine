"""Category 1 hard rules — deterministic pricing arithmetic.

These functions are pure: no IO, no LLM, no exceptions. They either compute
a value or return a rejection reason. The Decision layer's job is to be a
trusted guard between the unreliable LLM (Perception) and the final price.

Invariants enforced here (per spec.md AC #2):
- qty > 0 for every line item (else reject the WHOLE request, not filter).
- unit_price >= 0 for every line item.
- discount <= base (discounts are absolute money amounts, converted from
  rate to amount inside the Decision layer, not outside).
- tax = subtotal * TAX_RATE, applied post-discount (VAT on final amount).
"""

from __future__ import annotations

from decimal import Decimal

from app.decision.models import LineItemRequest

# Category 1 — fixed rate. Changing this requires a code change, not a
# config tweak, because it is a hard non-negotiable rule (VAT in Iran).
TAX_RATE = Decimal("0.09")


def validate_items_nonempty(items: list[LineItemRequest]) -> str | None:
    """Return a Farsi rejection reason if items is empty, else None.

    An empty items list means Perception failed to parse anything usable
    from the LLM (or the request genuinely contained nothing). Either way,
    pricing an empty cart as a 'successful 0-toman order' is a silent-drop
    anti-pattern — the same class of bug we closed for qty in AC #2.

    This check runs FIRST in the validation chain: it's the cheapest and
    short-circuits the others.
    """
    if not items:
        return "هیچ آیتم معتبری از درخواست استخراج نشد"
    return None


def validate_qty(items: list[LineItemRequest]) -> str | None:
    """Return a Farsi rejection reason if any qty is invalid, else None.

    If ANY item has qty <= 0, the WHOLE request is rejected — we do not
    silently filter out the bad item. This is per spec.md AC #2.
    """
    for item in items:
        if item.qty <= 0:
            return f"qty نامعتبر برای محصول {item.product_id}: qty={item.qty} باید > 0 باشد"
    return None


def validate_prices(items: list[LineItemRequest]) -> str | None:
    """Return a Farsi rejection reason if any unit_price < 0, else None.

    unit_price comes from the catalog (not LLM), so a negative value would
    indicate a catalog corruption bug — still rejected defensively.
    """
    for item in items:
        if item.unit_price < 0:
            return (
                f"قیمت نامعتبر برای محصول {item.product_id}: "
                f"unit_price={item.unit_price} باید >= 0 باشد"
            )
    return None


def compute_base(items: list[LineItemRequest]) -> Decimal:
    """Compute base = Σ(unit_price * qty).

    Assumes items are already validated (qty > 0, price >= 0). Do not call
    this on unvalidated input — the orchestrator (service.py) validates
    first, then computes.
    """
    return sum(
        (item.unit_price * item.qty for item in items),
        start=Decimal("0"),
    )


def compute_tax(subtotal: Decimal, rate: Decimal = TAX_RATE) -> Decimal:
    """Compute tax = subtotal * rate.

    Pure and deterministic. The rate defaults to the Category 1 fixed VAT
    rate; passing a different rate is only for testing.
    """
    return subtotal * rate


def compute_totals(
    base: Decimal,
    discount: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Compute (subtotal, tax, total) from base and discount.

    Returns (subtotal, tax, total) where:
        subtotal = base - discount
        tax      = subtotal * TAX_RATE
        total    = subtotal + tax

    This is the single source of truth for the arithmetic pipeline.
    """
    subtotal = base - discount
    tax = compute_tax(subtotal)
    total = subtotal + tax
    return subtotal, tax, total
