"""Tests for Decision layer domain dataclasses (T1.1)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.decision.models import (
    LineItemRequest,
    LineItemResult,
    PriceResult,
    PurchaseRequest,
)


def test_line_item_request_holds_catalog_price() -> None:
    """LineItemRequest carries the catalog unit_price (not LLM-derived)."""
    item = LineItemRequest(
        product_id="headphone-x",
        qty=5,
        unit_price=Decimal("150000"),
    )
    assert item.product_id == "headphone-x"
    assert item.qty == 5
    assert item.unit_price == Decimal("150000")


def test_purchase_request_groups_items_and_context() -> None:
    """PurchaseRequest holds items + customer_tier + season."""
    items = [
        LineItemRequest(product_id="headphone-x", qty=2, unit_price=Decimal("150000")),
    ]
    request = PurchaseRequest(items=items, customer_tier="special", season="sale")
    assert request.customer_tier == "special"
    assert request.season == "sale"
    assert len(request.items) == 1


def test_price_result_priced_holds_all_amounts() -> None:
    """A 'priced' result carries base, discount, tax, total."""
    result = PriceResult(
        line_items=[
            LineItemResult(
                product_id="headphone-x",
                product_name="هدفون مدل X",
                qty=2,
                unit_price=Decimal("150000"),
                line_total=Decimal("300000"),
            )
        ],
        base=Decimal("300000"),
        discount=Decimal("45000"),
        discount_reason="تخفیف مشتری ویژه",
        subtotal=Decimal("255000"),
        tax=Decimal("22950"),
        total=Decimal("277950"),
        status="priced",
    )
    assert result.status == "priced"
    assert result.rejection_reason is None
    assert result.total == Decimal("277950")


def test_price_result_rejected_factory_zeroes_amounts() -> None:
    """PriceResult.rejected() builds a rejected result with zero amounts."""
    result = PriceResult.rejected("qty نامعتبر")
    assert result.status == "rejected"
    assert result.rejection_reason == "qty نامعتبر"
    assert result.line_items == []
    assert result.base == Decimal("0")
    assert result.total == Decimal("0")


def test_price_result_is_frozen() -> None:
    """Domain dataclasses are immutable — prevents accidental mutation."""
    result = PriceResult.rejected("test")

    with pytest.raises(FrozenInstanceError):
        result.status = "priced"  # type: ignore[misc]
