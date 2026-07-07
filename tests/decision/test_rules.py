"""Tests for Category 1 hard rules (T1.2)."""

from __future__ import annotations

from decimal import Decimal

from app.decision.models import LineItemRequest
from app.decision.rules import (
    TAX_RATE,
    compute_base,
    compute_tax,
    compute_totals,
    validate_items_nonempty,
    validate_prices,
    validate_qty,
)


def _item(product_id: str, qty: int, price: int | Decimal = 100) -> LineItemRequest:
    """Helper to build a LineItemRequest."""
    return LineItemRequest(
        product_id=product_id,
        qty=qty,
        unit_price=Decimal(str(price)),
    )


# --- validate_items_nonempty ---


def test_validate_items_nonempty_accepts_nonempty() -> None:
    """A list with at least one item passes."""
    items = [_item("a", 1)]
    assert validate_items_nonempty(items) is None


def test_validate_items_nonempty_rejects_empty() -> None:
    """An empty items list is rejected with a clear Farsi reason.

    This closes the silent-drop gap where unparseable LLM output (empty
    items from Perception) would otherwise produce a 'priced' 0-toman order.
    """
    reason = validate_items_nonempty([])
    assert reason is not None
    assert "آیتم" in reason


# --- validate_qty ---


def test_validate_qty_accepts_positive() -> None:
    """qty > 0 passes validation."""
    items = [_item("a", 1), _item("b", 10)]
    assert validate_qty(items) is None
    """qty > 0 passes validation."""
    items = [_item("a", 1), _item("b", 10)]
    assert validate_qty(items) is None


def test_validate_qty_rejects_zero() -> None:
    """qty == 0 is rejected with a Farsi reason naming the product."""
    items = [_item("headphone-x", 0)]
    reason = validate_qty(items)
    assert reason is not None
    assert "headphone-x" in reason
    assert "qty=0" in reason


def test_validate_qty_rejects_negative() -> None:
    """qty < 0 is rejected."""
    items = [_item("a", -5)]
    reason = validate_qty(items)
    assert reason is not None
    assert "-5" in reason


def test_validate_qty_rejects_whole_request_on_one_bad_item() -> None:
    """One bad item rejects the WHOLE request, not just that item.

    This is the critical AC #2 rule: no silent filtering.
    """
    items = [_item("good", 5), _item("bad", -1), _item("also-good", 3)]
    reason = validate_qty(items)
    assert reason is not None
    assert "bad" in reason


# --- validate_prices ---


def test_validate_prices_accepts_non_negative() -> None:
    """unit_price >= 0 passes."""
    items = [_item("a", 1, 0), _item("b", 1, 150000)]
    assert validate_prices(items) is None


def test_validate_prices_rejects_negative() -> None:
    """unit_price < 0 is rejected with the product named."""
    items = [_item("mouse-z", 1, -100)]
    reason = validate_prices(items)
    assert reason is not None
    assert "mouse-z" in reason


# --- compute_base ---


def test_compute_base_sums_price_times_qty() -> None:
    """base = Σ(unit_price * qty)."""
    items = [_item("a", 2, 150000), _item("b", 3, 800000)]
    base = compute_base(items)
    assert base == Decimal("2700000")  # 2*150000 + 3*800000


def test_compute_base_empty_items_is_zero() -> None:
    """Empty cart has base = 0."""
    assert compute_base([]) == Decimal("0")


# --- compute_tax ---


def test_compute_tax_default_rate() -> None:
    """Default tax rate is 0.09 (Category 1 VAT)."""
    assert compute_tax(Decimal("1000")) == Decimal("90")


def test_compute_tax_custom_rate() -> None:
    """Custom rate can be passed (for testing only)."""
    assert compute_tax(Decimal("1000"), Decimal("0.20")) == Decimal("200")


def test_tax_rate_is_category_1_fixed() -> None:
    """TAX_RATE constant is exactly 0.09 — a hard non-negotiable rule."""
    assert Decimal("0.09") == TAX_RATE


# --- compute_totals ---


def test_compute_totals_contract_example() -> None:
    """The contract example: base=7000000, discount=1050000.

    subtotal = 5950000, tax = 535500, total = 6485500.
    """
    subtotal, tax, total = compute_totals(
        base=Decimal("7000000"),
        discount=Decimal("1050000"),
    )
    assert subtotal == Decimal("5950000")
    assert tax == Decimal("535500")
    assert total == Decimal("6485500")


def test_compute_totals_zero_discount() -> None:
    """Zero discount: subtotal == base, tax = base * rate."""
    subtotal, tax, total = compute_totals(
        base=Decimal("1000"),
        discount=Decimal("0"),
    )
    assert subtotal == Decimal("1000")
    assert tax == Decimal("90")
    assert total == Decimal("1090")
