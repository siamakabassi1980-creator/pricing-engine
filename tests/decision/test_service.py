"""Tests for the Decision orchestration service (T1.4)."""

from __future__ import annotations

from decimal import Decimal

from app.config import Settings
from app.decision.models import LineItemRequest, PurchaseRequest
from app.decision.service import price

CATALOG = {
    "headphone-x": "هدفون مدل X",
    "keyboard-y": "کیبورد مدل Y",
}


def _settings() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]  # pydantic private


def test_service_priced_full_pipeline() -> None:
    """Service produces a priced result for a valid request."""
    request = PurchaseRequest(
        items=[
            LineItemRequest("headphone-x", 20, Decimal("150000")),
            LineItemRequest("keyboard-y", 5, Decimal("800000")),
        ],
        customer_tier="special",
        season="sale",
    )
    result = price(request, CATALOG, _settings())
    assert result.status == "priced"
    assert result.base == Decimal("7000000")
    assert result.discount == Decimal("1050000")  # max(15%, 10%)
    assert result.subtotal == Decimal("5950000")
    assert result.tax == Decimal("535500")
    assert result.total == Decimal("6485500")


def test_service_rejects_bad_qty_no_exception() -> None:
    """Service returns a rejected result, never raises."""
    request = PurchaseRequest(
        items=[LineItemRequest("headphone-x", -3, Decimal("150000"))],
        customer_tier="regular",
        season="normal",
    )
    result = price(request, CATALOG, _settings())
    assert result.status == "rejected"
    assert result.rejection_reason is not None
    assert result.line_items == []


def test_service_rejects_negative_price() -> None:
    """Negative unit_price is rejected defensively."""
    request = PurchaseRequest(
        items=[LineItemRequest("headphone-x", 1, Decimal("-100"))],
        customer_tier="regular",
        season="normal",
    )
    result = price(request, CATALOG, _settings())
    assert result.status == "rejected"


def test_service_enriches_line_item_names_from_catalog() -> None:
    """Line item results carry the Farsi name from the catalog."""
    request = PurchaseRequest(
        items=[LineItemRequest("headphone-x", 1, Decimal("150000"))],
        customer_tier="regular",
        season="normal",
    )
    result = price(request, CATALOG, _settings())
    assert result.status == "priced"
    assert result.line_items[0].product_name == "هدفون مدل X"


def test_service_falls_back_to_id_when_product_not_in_catalog() -> None:
    """If catalog lacks a name, fall back to the product_id."""
    request = PurchaseRequest(
        items=[LineItemRequest("unknown-product", 1, Decimal("100"))],
        customer_tier="regular",
        season="normal",
    )
    result = price(request, {}, _settings())
    assert result.status == "priced"
    assert result.line_items[0].product_name == "unknown-product"


def test_service_zero_discount_for_regular_normal() -> None:
    """Regular customer, normal season: zero discount, reason empty."""
    request = PurchaseRequest(
        items=[LineItemRequest("headphone-x", 1, Decimal("150000"))],
        customer_tier="regular",
        season="normal",
    )
    result = price(request, CATALOG, _settings())
    assert result.status == "priced"
    assert result.discount == Decimal("0")
    assert result.discount_reason == ""
