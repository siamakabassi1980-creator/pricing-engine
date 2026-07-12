"""Unit tests for the catalog Pydantic schemas (T0.2).

Validates Category 1 hard rules at the input boundary: non-negative
price, <= 2 decimal places, non-empty name, lowercase-slug id.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.catalog.schemas import ProductCreate, ProductUpdate

# --- helpers -----------------------------------------------------------------


def _create(**overrides: object) -> None:
    """Build a ProductCreate from valid defaults + overrides, assert no error."""
    base: dict[str, object] = {
        "id": "headphone-x",
        "name_fa": "هدفون مدل X",
        "unit_price": Decimal("150000"),
    }
    base.update(overrides)
    ProductCreate(**base)


def _expect_create_error(field: str, **overrides: object) -> None:
    base: dict[str, object] = {
        "id": "headphone-x",
        "name_fa": "هدفون مدل X",
        "unit_price": Decimal("150000"),
    }
    base.update(overrides)
    with pytest.raises(ValidationError) as exc:
        ProductCreate(**base)
    assert field in str(exc.value)


# --- valid inputs ------------------------------------------------------------


@pytest.mark.parametrize(
    "price",
    [
        Decimal("150000"),
        Decimal("150000.99"),
        Decimal("150000.9"),
        Decimal("0"),
        Decimal("0.00"),
    ],
)
def test_create_accepts_valid_prices(price: Decimal) -> None:
    _create(unit_price=price)


@pytest.mark.parametrize(
    "product_id",
    ["headphone-x", "a", "a-b-c", "x1", "abc-123-def"],
)
def test_create_accepts_valid_slugs(product_id: str) -> None:
    _create(id=product_id)


# --- price validation --------------------------------------------------------


def test_create_rejects_negative_price() -> None:
    _expect_create_error("unit_price", unit_price=Decimal("-1"))


def test_create_rejects_more_than_two_decimal_places() -> None:
    _expect_create_error("unit_price", unit_price=Decimal("150000.999"))


def test_create_rejects_three_decimal_places() -> None:
    _expect_create_error("unit_price", unit_price=Decimal("0.001"))


# --- name validation ---------------------------------------------------------


def test_create_rejects_empty_name() -> None:
    _expect_create_error("name_fa", name_fa="")


def test_create_rejects_whitespace_only_name() -> None:
    _expect_create_error("name_fa", name_fa="   ")


# --- id / slug validation ----------------------------------------------------


@pytest.mark.parametrize(
    "product_id",
    [
        "Headphone",  # uppercase
        "-x",  # leading hyphen
        "x-",  # trailing hyphen
        "a--b",  # consecutive hyphens
        "",  # empty
        "headphone_x",  # underscore not allowed
        "headphone x",  # space not allowed
        "هدفون",  # non-ascii
    ],
)
def test_create_rejects_invalid_slugs(product_id: str) -> None:
    _expect_create_error("id", id=product_id)


# --- ProductUpdate -----------------------------------------------------------


def test_update_accepts_valid_fields() -> None:
    ProductUpdate(
        id="headphone-x",
        name_fa="هدفون جدید",
        unit_price=Decimal("200000"),
    )


def test_update_rejects_negative_price() -> None:
    with pytest.raises(ValidationError) as exc:
        ProductUpdate(
            id="headphone-x",
            name_fa="نام",
            unit_price=Decimal("-5"),
        )
    assert "unit_price" in str(exc.value)


def test_update_rejects_more_than_two_decimals() -> None:
    with pytest.raises(ValidationError) as exc:
        ProductUpdate(
            id="headphone-x",
            name_fa="نام",
            unit_price=Decimal("1.234"),
        )
    assert "unit_price" in str(exc.value)


def test_update_rejects_empty_name() -> None:
    with pytest.raises(ValidationError) as exc:
        ProductUpdate(
            id="headphone-x",
            name_fa="",
            unit_price=Decimal("1"),
        )
    assert "name_fa" in str(exc.value)
