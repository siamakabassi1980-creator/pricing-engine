"""Tests for Category 2 discounts (T1.3).

Critical rule: non-stacking. If both VIP and seasonal apply, the MAX is
taken, not the sum. This keeps discount <= base trivially.
"""

from __future__ import annotations

from decimal import Decimal

from app.decision.discounts import (
    applicable_discounts,
    compute_discount,
)

VIP_RATE = Decimal("0.15")  # 15% — agreed Category 2 default
SEASONAL_RATE = Decimal("0.10")  # 10% — agreed Category 2 default


def test_no_discount_for_regular_customer_normal_season() -> None:
    """Regular customer, normal season: no discount applies."""
    amount, reason = compute_discount(
        base=Decimal("1000"),
        customer_tier="regular",
        season="normal",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    assert amount == Decimal("0")
    assert reason == ""


def test_vip_discount_applies_for_special_tier() -> None:
    """Special tier applies VIP discount (15%) regardless of season."""
    amount, reason = compute_discount(
        base=Decimal("1000"),
        customer_tier="special",
        season="normal",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    assert amount == Decimal("150")  # 1000 * 0.15
    assert "مشتری ویژه" in reason


def test_seasonal_discount_applies_in_sale_season() -> None:
    """Sale season applies seasonal discount (10%) for regular customer."""
    amount, reason = compute_discount(
        base=Decimal("1000"),
        customer_tier="regular",
        season="sale",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    assert amount == Decimal("100")  # 1000 * 0.10
    assert "فصلی" in reason


def test_non_stacking_takes_max_when_both_apply() -> None:
    """Both VIP (15%) and seasonal (10%) apply -> take MAX (15%), not sum.

    This is the critical non-stacking rule. Sum would be 250; max is 150.
    """
    amount, reason = compute_discount(
        base=Decimal("1000"),
        customer_tier="special",
        season="sale",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    assert amount == Decimal("150")  # max(150, 100), NOT 250
    assert "بالاتر از" in reason  # mentions the non-stacking choice


def test_non_stacking_takes_max_when_seasonal_higher() -> None:
    """If seasonal > VIP (configurable), max picks seasonal."""
    amount, _ = compute_discount(
        base=Decimal("1000"),
        customer_tier="special",
        season="sale",
        vip_rate=Decimal("0.05"),  # 5%
        seasonal_rate=Decimal("0.20"),  # 20%
    )
    assert amount == Decimal("200")  # max(50, 200)


def test_rate_to_amount_conversion_happens_here() -> None:
    """Conversion rate -> amount is a Decision responsibility.

    The formula in spec.md uses an absolute amount; we must not leak rates
    out of this layer. Verify the output is a money amount, not a fraction.
    """
    amount, _ = compute_discount(
        base=Decimal("1000000"),
        customer_tier="special",
        season="normal",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    # 1000000 * 0.15 = 150000 (a money amount, not 0.15)
    assert amount == Decimal("150000")


def test_applicable_discounts_returns_empty_when_none_match() -> None:
    """No discount matches -> empty list, compute_discount returns zero."""
    candidates = applicable_discounts(
        base=Decimal("1000"),
        customer_tier="regular",
        season="normal",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    assert candidates == []


def test_applicable_discounts_lists_both_when_both_match() -> None:
    """Both conditions met -> two candidates listed (max picked later)."""
    candidates = applicable_discounts(
        base=Decimal("1000"),
        customer_tier="special",
        season="sale",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    assert len(candidates) == 2


def test_zero_base_produces_zero_discount() -> None:
    """Edge case: empty cart (base=0) -> zero discount, no division issues."""
    amount, reason = compute_discount(
        base=Decimal("0"),
        customer_tier="special",
        season="sale",
        vip_rate=VIP_RATE,
        seasonal_rate=SEASONAL_RATE,
    )
    assert amount == Decimal("0")
