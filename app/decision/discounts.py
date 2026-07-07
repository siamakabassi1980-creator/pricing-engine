"""Category 2 tunable discounts — non-stacking.

Unlike Category 1 (hard rules), Category 2 rates are tunable via config.
But the COMBINATION logic is still deterministic: when multiple discounts
apply, we take the MAXIMUM, not the sum. This keeps the invariant
`discount <= base` trivially true (no compounding beyond 100%).

Rate-to-amount conversion happens HERE, inside the Decision layer, not
outside it. This is per spec.md AC #2: discount in the formula is an
absolute money amount, and the conversion is a Decision responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.decision.models import Season, Tier


@dataclass(frozen=True)
class DiscountRate:
    """A named discount rate (fraction, e.g. 0.15 for 15%)."""

    rate: Decimal
    reason: str


def vip_discount_rate(rate: Decimal) -> DiscountRate:
    """The VIP customer discount (Category 2, tier='special' only)."""
    return DiscountRate(rate=rate, reason="تخفیف مشتری ویژه")


def seasonal_discount_rate(rate: Decimal) -> DiscountRate:
    """The seasonal sale discount (Category 2, season='sale' only)."""
    return DiscountRate(rate=rate, reason="تخفیف فصلی")


def applicable_discounts(
    base: Decimal,
    customer_tier: Tier,
    season: Season,
    vip_rate: Decimal,
    seasonal_rate: Decimal,
) -> list[tuple[DiscountRate, Decimal]]:
    """List the discounts that apply, each as (rate, amount).

    A discount applies only when its condition is met:
    - VIP discount: customer_tier == 'special'.
    - Seasonal discount: season == 'sale'.

    Each amount is base * rate (the rate-to-amount conversion happens here).
    Returns an empty list if no discount applies.
    """
    result: list[tuple[DiscountRate, Decimal]] = []

    if customer_tier == "special":
        vip = vip_discount_rate(vip_rate)
        result.append((vip, base * vip.rate))

    if season == "sale":
        seasonal = seasonal_discount_rate(seasonal_rate)
        result.append((seasonal, base * seasonal.rate))

    return result


def compute_discount(
    base: Decimal,
    customer_tier: Tier,
    season: Season,
    vip_rate: Decimal,
    seasonal_rate: Decimal,
) -> tuple[Decimal, str]:
    """Compute the non-stacking discount for a request.

    Returns (discount_amount, reason) where amount is an absolute money
    value (not a rate) and reason is a Farsi explanation.

    Non-stacking rule: if multiple discounts apply, we take the one with
    the MAXIMUM amount, not the sum. This keeps discount <= base trivially.
    """
    candidates = applicable_discounts(base, customer_tier, season, vip_rate, seasonal_rate)

    if not candidates:
        return Decimal("0"), ""

    # Pick the discount with the maximum amount (non-stacking).
    best_rate, best_amount = max(candidates, key=lambda pair: pair[1])

    # Build a Farsi reason. If both applied, mention the non-stacking choice.
    if len(candidates) > 1:
        other_rate, other_amount = min(candidates, key=lambda pair: pair[1])
        reason = (
            f"{best_rate.reason} ({_percent(best_rate.rate)}) — "
            f"بالاتر از {other_rate.reason} ({_percent(other_rate.rate)})"
        )
    else:
        reason = f"{best_rate.reason} ({_percent(best_rate.rate)})"

    return best_amount, reason


def _percent(rate: Decimal) -> str:
    """Format a rate as a Farsi percentage string, e.g. 0.15 -> '۱۵٪'."""
    # Use Decimal arithmetic to avoid float artifacts.
    pct = (rate * 100).quantize(Decimal("1"))
    return f"{pct}٪"
