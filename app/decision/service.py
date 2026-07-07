"""Decision layer orchestration service.

This is the single entry point to the Decision layer. It NEVER raises —
any invalid input produces a PriceResult with status="rejected". This is
the trust boundary: Perception (LLM) can produce garbage, but Decision
turns it into either a correct price or an explicit rejection.

Pure deterministic: no LLM, no IO, no time-dependent behavior. Given the
same inputs, always the same output.
"""

from __future__ import annotations

from app.config import Settings
from app.decision.discounts import compute_discount
from app.decision.models import (
    LineItemResult,
    PriceResult,
    PurchaseRequest,
)
from app.decision.rules import (
    compute_base,
    compute_totals,
    validate_items_nonempty,
    validate_prices,
    validate_qty,
)


def price(
    request: PurchaseRequest,
    catalog: dict[str, str],
    settings: Settings,
) -> PriceResult:
    """Price a purchase request deterministically.

    Args:
        request: The parsed request (from Perception).
        catalog: A mapping of product_id -> product_name (Farsi). Used only
            to enrich line item names in the result; prices come from the
            request's LineItemRequest.unit_price (which was injected from DB).
        settings: App settings (carries the tunable Category 2 rates).

    Returns:
        PriceResult — always. Either status="priced" with full amounts, or
        status="rejected" with a Farsi rejection_reason. Never raises.
    """
    # Category 1 validation — reject the WHOLE request on any violation.
    # Order matters: empty-items check first (cheapest, short-circuits).
    if (reason := validate_items_nonempty(request.items)) is not None:
        return PriceResult.rejected(reason)
    if (reason := validate_qty(request.items)) is not None:
        return PriceResult.rejected(reason)
    if (reason := validate_prices(request.items)) is not None:
        return PriceResult.rejected(reason)

    # Compute base (only reached if all items validated).
    base = compute_base(request.items)

    # Category 2 discount (non-stacking max).
    discount, discount_reason = compute_discount(
        base=base,
        customer_tier=request.customer_tier,
        season=request.season,
        vip_rate=settings.vip_customer_discount_rate,
        seasonal_rate=settings.default_seasonal_discount_rate,
    )

    # Totals pipeline.
    subtotal, tax, total = compute_totals(base, discount)

    # Build line item results (enrich with product names from catalog).
    line_items = [
        LineItemResult(
            product_id=item.product_id,
            product_name=catalog.get(item.product_id, item.product_id),
            qty=item.qty,
            unit_price=item.unit_price,
            line_total=item.unit_price * item.qty,
        )
        for item in request.items
    ]

    return PriceResult(
        line_items=line_items,
        base=base,
        discount=discount,
        discount_reason=discount_reason,
        subtotal=subtotal,
        tax=tax,
        total=total,
        status="priced",
    )
