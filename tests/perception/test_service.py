"""Tests for Perception service (T2.2).

Includes the critical adversarial security test: when the LLM returns a
fake/negative unit_price in its response, the system MUST ignore it and
use the catalog price. This is a regression test for the security decision
documented in data-model.md.
"""

from __future__ import annotations

from decimal import Decimal

from app.perception.llm_adapter import DummyLLM
from app.perception.service import parse_request

CATALOG = {
    "headphone-x": "هدفون مدل X",
    "keyboard-y": "کیبورد مدل Y",
}
CATALOG_PRICES = {
    "headphone-x": Decimal("150000"),
    "keyboard-y": Decimal("800000"),
}


def test_parse_request_extracts_items() -> None:
    """A valid LLM response produces a PurchaseRequest with correct items."""
    llm = DummyLLM(
        responses={
            "parse": '{"items": [{"product_id": "headphone-x", "qty": 20}, '
            '{"product_id": "keyboard-y", "qty": 5}]}',
        }
    )
    result = parse_request(
        request_text="۲۰ هدفون و ۵ کیبورد",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert len(result.items) == 2
    assert result.items[0].product_id == "headphone-x"
    assert result.items[0].qty == 20
    assert result.items[1].product_id == "keyboard-y"
    assert result.items[1].qty == 5


def test_parse_request_injects_catalog_price_not_llm_price() -> None:
    """Prices come from catalog, not from LLM output.

    This is the standard behavior: LLM provides product_id + qty, price is
    looked up server-side.
    """
    llm = DummyLLM(
        responses={
            "parse": '{"items": [{"product_id": "headphone-x", "qty": 2}]}',
        }
    )
    result = parse_request(
        request_text="۲ هدفون",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert result.items[0].unit_price == Decimal("150000")


def test_adversarial_llm_returns_fake_price_is_ignored() -> None:
    """SECURITY TEST: LLM returns a fake/negative price -> MUST be ignored.

    The LLM might hallucinate or be manipulated into returning a 'price'
    field. The system MUST ignore any LLM-supplied price and use the
    catalog price. This is a regression test for the security decision
    in data-model.md: "unit_price NEVER comes from the LLM."

    Here the LLM returns price=-999 (negative, absurd). The catalog price
    (150000) must be used regardless.
    """
    malicious_llm_response = '{"items": [{"product_id": "headphone-x", "qty": 2, "price": -999}]}'
    llm = DummyLLM(responses={"parse": malicious_llm_response})
    result = parse_request(
        request_text="۲ هدفون",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert len(result.items) == 1
    # The catalog price is used, NOT -999.
    assert result.items[0].unit_price == Decimal("150000")
    assert result.items[0].unit_price != Decimal("-999")


def test_adversarial_llm_returns_zero_price_is_ignored() -> None:
    """SECURITY TEST: LLM returns price=0 (free exploit) -> MUST be ignored.

    A malicious LLM response claiming the product is free must not result
    in a zero price. Catalog price must win.
    """
    malicious_llm_response = '{"items": [{"product_id": "keyboard-y", "qty": 1, "price": 0}]}'
    llm = DummyLLM(responses={"parse": malicious_llm_response})
    result = parse_request(
        request_text="۱ کیبورد",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert result.items[0].unit_price == Decimal("800000")  # catalog, not 0


def test_parse_request_unknown_product_is_skipped() -> None:
    """Products not in the catalog are skipped, not included with no price."""
    llm = DummyLLM(
        responses={
            "parse": '{"items": [{"product_id": "headphone-x", "qty": 1}, '
            '{"product_id": "unknown-thing", "qty": 1}]}',
        }
    )
    result = parse_request(
        request_text="۱ هدفون و یه چیز ناشناخته",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert len(result.items) == 1  # only the known product
    assert result.items[0].product_id == "headphone-x"


def test_parse_request_unparseable_response_returns_empty() -> None:
    """If the LLM returns garbage, return empty items (safe default)."""
    llm = DummyLLM(responses={"parse": "this is not json at all"})
    result = parse_request(
        request_text="هرچی",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert result.items == []


def test_parse_request_no_items_key_returns_empty() -> None:
    """If the JSON has no 'items' key, return empty."""
    llm = DummyLLM(responses={"parse": '{"something_else": true}'})
    result = parse_request(
        request_text="هرچی",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert result.items == []


def test_parse_request_qty_not_int_skipped() -> None:
    """If qty is not an integer (e.g. a string), the item is skipped."""
    llm = DummyLLM(
        responses={
            "parse": '{"items": [{"product_id": "headphone-x", "qty": "twenty"}]}',
        }
    )
    result = parse_request(
        request_text="بیست هدفون",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=llm,
    )
    assert result.items == []
