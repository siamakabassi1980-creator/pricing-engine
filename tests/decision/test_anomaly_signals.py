"""Tests for deterministic anomaly signals (T0.1, feature 002).

These are Category 2 signals with tunable thresholds. They are property-tested
because they are deterministic — unlike the qualitative LLM-based detection
which is exempt from PBT (ADR-0002).
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from app.decision.models import LineItemRequest
from app.decision.rules import check_deterministic_signals


def _item(product_id: str, qty: int, price: Decimal = Decimal("100")) -> LineItemRequest:
    return LineItemRequest(product_id=product_id, qty=qty, unit_price=price)


# --- Unit tests ---


def test_no_signals_for_normal_order() -> None:
    """Normal quantities and amounts produce no signals."""
    items = [_item("a", 5), _item("b", 10)]
    signals = check_deterministic_signals(items, base=Decimal("5000"))
    assert signals == []


def test_large_quantity_signal() -> None:
    """qty > threshold produces a signal naming the product."""
    items = [_item("headphone-x", 150)]
    signals = check_deterministic_signals(items, base=Decimal("1000"))
    assert len(signals) == 1
    assert "headphone-x" in signals[0]
    assert "150" in signals[0]


def test_large_base_signal() -> None:
    """base > threshold produces a signal."""
    items = [_item("a", 1, Decimal("11000000"))]
    signals = check_deterministic_signals(items, base=Decimal("11000000"))
    assert len(signals) == 1
    assert "مبلغ کل" in signals[0]


def test_both_signals_when_both_trigger() -> None:
    """Both large qty and large base can trigger simultaneously."""
    items = [_item("a", 200, Decimal("100000"))]
    signals = check_deterministic_signals(items, base=Decimal("20000000"))
    assert len(signals) == 2


def test_custom_thresholds() -> None:
    """Thresholds are configurable (Category 2)."""
    items = [_item("a", 50)]  # qty=50, below default 100
    # With custom threshold 40, this should flag.
    signals = check_deterministic_signals(items, base=Decimal("100"), qty_threshold=40)
    assert len(signals) == 1
    assert "50" in signals[0]


def test_boundary_qty_equals_threshold_no_signal() -> None:
    """qty == threshold does NOT signal (strictly greater than)."""
    items = [_item("a", 100)]
    signals = check_deterministic_signals(items, base=Decimal("1000"), qty_threshold=100)
    assert signals == []


def test_boundary_base_equals_threshold_no_signal() -> None:
    """base == threshold does NOT signal (strictly greater than)."""
    items = [_item("a", 1)]
    threshold = Decimal("10000000")
    signals = check_deterministic_signals(items, base=threshold, base_threshold=threshold)
    assert signals == []


# --- Property tests (Hypothesis) ---


qty_strategy = st.integers(min_value=1, max_value=1000)
price_strategy = st.decimals(
    min_value=Decimal("1"),
    max_value=Decimal("20000000"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)


class TestDeterministicSignalProperties:
    """Property tests for Category 2 deterministic anomaly signals."""

    @given(qty=qty_strategy)
    @hyp_settings(max_examples=100)
    def test_qty_above_threshold_always_signals(self, qty: int) -> None:
        """For any qty > threshold, a signal is produced (guaranteed)."""
        threshold = 100
        items = [_item("test-product", qty)]
        base = Decimal("1000")  # small base, no base signal
        signals = check_deterministic_signals(items, base=base, qty_threshold=threshold)
        if qty > threshold:
            assert len(signals) >= 1
            assert any("test-product" in s for s in signals)
        else:
            assert all("test-product" not in s for s in signals)

    @given(base=price_strategy)
    @hyp_settings(max_examples=100)
    def test_base_above_threshold_always_signals(self, base: Decimal) -> None:
        """For any base > threshold, a signal is produced (guaranteed)."""
        threshold = Decimal("10000000")
        items = [_item("a", 1)]  # small qty, no qty signal
        signals = check_deterministic_signals(items, base=base, base_threshold=threshold)
        if base > threshold:
            assert any("مبلغ کل" in s for s in signals)
        else:
            assert all("مبلغ کل" not in s for s in signals)

    @given(qty=st.integers(min_value=1, max_value=50))
    @hyp_settings(max_examples=50)
    def test_normal_qty_never_signals(self, qty: int) -> None:
        """For any qty <= 50 (well below threshold 100), no qty signal."""
        items = [_item("a", qty)]
        signals = check_deterministic_signals(items, base=Decimal("1000"), qty_threshold=100)
        # Only base signal might appear if base is large, but we set it small.
        assert all("a" not in s for s in signals)
