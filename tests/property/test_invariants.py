"""Property-based tests for Decision layer invariants (T1.4).

These are the core of the whole experiment: proving that Category 1 hard
rules hold for ANY input Hypothesis can generate, not just hand-picked cases.

The five properties mandated by spec.md AC #3:
  (الف)   total >= 0 for any valid input.
  (الف')  unit_price >= 0 directly on every line item.
  (ب)    discount <= base for any combination of discounts.
  (ج)    tax = subtotal * TAX_RATE exactly.
  (د)    invalid qty (<=0) -> status="rejected", not exception or computation.
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from app.config import Settings
from app.decision.models import LineItemRequest, PurchaseRequest
from app.decision.rules import TAX_RATE
from app.decision.service import price

# --- Strategies: how Hypothesis generates inputs ---

# Quantities: positive integers (the valid case).
qty_strategy = st.integers(min_value=1, max_value=1000)

# Prices: non-negative decimals with 2 decimal places (money).
price_strategy = st.decimals(
    min_value=0,
    max_value=10_000_000,
    places=2,
    allow_nan=False,
    allow_infinity=False,
)

# Tiers and seasons.
tier_strategy = st.sampled_from(["regular", "special"])
season_strategy = st.sampled_from(["normal", "sale"])

# Discount rates (Category 2 tunable values).
rate_strategy = st.decimals(
    min_value=0,
    max_value=0.50,
    places=2,
    allow_nan=False,
    allow_infinity=False,
)


def _line_item_strategy() -> st.SearchStrategy[LineItemRequest]:
    """Generate a valid LineItemRequest."""
    return st.builds(
        LineItemRequest,
        product_id=st.sampled_from(["headphone-x", "keyboard-y", "mouse-z", "monitor-m"]),
        qty=qty_strategy,
        unit_price=price_strategy,
    )


def _purchase_request_strategy() -> st.SearchStrategy[PurchaseRequest]:
    """Generate a valid PurchaseRequest with 1-5 line items."""
    return st.builds(
        PurchaseRequest,
        items=st.lists(_line_item_strategy(), min_size=1, max_size=5),
        customer_tier=tier_strategy,
        season=season_strategy,
    )


def _make_settings(vip_rate: Decimal, seasonal_rate: Decimal) -> Settings:
    """Build a Settings instance with custom Category 2 rates.

    We cannot use st.builds(Settings, ...) because pydantic-settings has
    private model config that Hypothesis tries to treat as a field.
    Instead, generate the rates as strategies and construct via a function.
    """
    return Settings(
        _env_file=None,  # type: ignore[call-arg]  # pydantic-settings private init
        vip_customer_discount_rate=vip_rate,
        default_seasonal_discount_rate=seasonal_rate,
    )


def _settings_strategy() -> st.SearchStrategy[Settings]:
    """Generate Settings with tunable Category 2 rates."""
    return st.builds(_make_settings, vip_rate=rate_strategy, seasonal_rate=rate_strategy)


CATALOG = {
    "headphone-x": "هدفون مدل X",
    "keyboard-y": "کیبورد مدل Y",
    "mouse-z": "ماوس مدل Z",
    "monitor-m": "مانیتور مدل M",
}


# --- The five property tests ---


class TestDecisionInvariants:
    """The five invariant properties mandated by spec.md AC #3."""

    @given(req=_purchase_request_strategy(), settings=_settings_strategy())
    @hyp_settings(max_examples=100)
    def test_alf_total_non_negative(self, req: PurchaseRequest, settings: Settings) -> None:
        """(الف) For any valid input, total >= 0."""
        result = price(req, CATALOG, settings)
        assert result.status == "priced"
        assert result.total >= 0

    @given(req=_purchase_request_strategy(), settings=_settings_strategy())
    @hyp_settings(max_examples=100)
    def test_alf_prime_unit_price_non_negative_directly(
        self, req: PurchaseRequest, settings: Settings
    ) -> None:
        """(الف') unit_price >= 0 on every line item, directly.

        Not just inferred from total — checked per-item so a broken
        computation points to the exact failing location.
        """
        result = price(req, CATALOG, settings)
        assert result.status == "priced"
        for item in result.line_items:
            assert item.unit_price >= 0

    @given(req=_purchase_request_strategy(), settings=_settings_strategy())
    @hyp_settings(max_examples=100)
    def test_be_discount_le_base(self, req: PurchaseRequest, settings: Settings) -> None:
        """(ب) discount <= base for any combination of discounts.

        Non-stacking max() keeps this trivially true: a single rate applied
        to base can never exceed base (assuming rate <= 1).
        """
        result = price(req, CATALOG, settings)
        assert result.status == "priced"
        assert result.discount <= result.base

    @given(req=_purchase_request_strategy(), settings=_settings_strategy())
    @hyp_settings(max_examples=100)
    def test_jim_tax_exact(self, req: PurchaseRequest, settings: Settings) -> None:
        """(ج) tax = subtotal * TAX_RATE exactly (0.09)."""
        result = price(req, CATALOG, settings)
        assert result.status == "priced"
        expected_tax = result.subtotal * TAX_RATE
        assert result.tax == expected_tax

    @given(
        product_id=st.sampled_from(["headphone-x", "keyboard-y"]),
        bad_qty=st.integers(min_value=-100, max_value=0),
        unit_price=price_strategy,
        customer_tier=tier_strategy,
        season=season_strategy,
    )
    @hyp_settings(max_examples=50)
    def test_dal_invalid_qty_rejected(
        self,
        product_id: str,
        bad_qty: int,
        unit_price: Decimal,
        customer_tier: object,
        season: object,
    ) -> None:
        """(د) Invalid qty (<=0) -> status='rejected', never exception.

        The Decision layer must return a rejected PriceResult, not raise
        and not silently compute a (wrong) price.
        """
        request = PurchaseRequest(
            items=[
                LineItemRequest(
                    product_id=product_id,
                    qty=bad_qty,
                    unit_price=unit_price,
                )
            ],
            customer_tier=customer_tier,  # type: ignore[arg-type]
            season=season,  # type: ignore[arg-type]
        )
        settings = Settings(_env_file=None)  # type: ignore[call-arg]  # pydantic private
        result = price(request, CATALOG, settings)

        assert result.status == "rejected"
        assert result.rejection_reason is not None
        assert "qty" in result.rejection_reason
