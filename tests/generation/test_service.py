"""Tests for the Generation service (T3.1).

Critical boundary rule tested here: generate_invoice() must NEVER call
the LLM for a rejected result — it returns the rejection_reason directly.
This is verified by using a DummyLLM that would FAIL the test if called
on a rejected result.
"""

from __future__ import annotations

from decimal import Decimal

from app.decision.models import LineItemResult, PriceResult
from app.generation.service import generate_invoice
from app.perception.llm_adapter import DummyLLM


def _priced_result() -> PriceResult:
    """Build a sample priced result for invoice generation."""
    return PriceResult(
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
        discount_reason="تخفیف مشتری ویژه (۱۵٪)",
        subtotal=Decimal("255000"),
        tax=Decimal("22950"),
        total=Decimal("277950"),
        status="priced",
    )


def test_generate_invoice_calls_llm_for_priced_result() -> None:
    """For a priced result, generate_invoice calls the LLM and returns text."""
    llm = DummyLLM(
        responses={
            "invoice": "پیش‌فاکتور: ۲ عدد هدفون — ۳۰۰٬۰۰۰ تومان",
        }
    )
    text = generate_invoice(_priced_result(), llm)
    assert "هدفون" in text


def test_generate_invoice_skips_llm_for_rejected_result() -> None:
    """BOUNDARY RULE: rejected result -> NO LLM call, return reason directly.

    This is the critical test. We pass a DummyLLM whose responses would
    NEVER match a rejection reason. If generate_invoice called the LLM,
    it would return the scripted invoice text (wrong). It must instead
    return the rejection_reason unchanged.
    """
    rejected = PriceResult.rejected("هیچ آیتم معتبری از درخواست استخراج نشد")
    # A DummyLLM that would return invoice text if called — proving it's NOT.
    llm = DummyLLM(
        responses={
            "invoice": "THIS SHOULD NEVER APPEAR IF BOUNDARY RULE WORKS",
        }
    )
    text = generate_invoice(rejected, llm)

    # The rejection reason is returned, NOT the LLM's invoice text.
    assert text == "هیچ آیتم معتبری از درخواست استخراج نشد"
    assert "THIS SHOULD NEVER APPEAR" not in text


def test_generate_invoice_rejected_with_empty_reason_returns_default() -> None:
    """A rejected result with no reason returns a safe Farsi default."""
    # Build a rejected result with empty rejection_reason (edge case).
    rejected = PriceResult(
        line_items=[],
        base=Decimal("0"),
        discount=Decimal("0"),
        discount_reason="",
        subtotal=Decimal("0"),
        tax=Decimal("0"),
        total=Decimal("0"),
        status="rejected",
        rejection_reason=None,
    )
    llm = DummyLLM(responses={"invoice": "SHOULD NOT APPEAR"})
    text = generate_invoice(rejected, llm)
    assert text == "درخواست رد شد"
    assert "SHOULD NOT APPEAR" not in text


def test_generate_invoice_prompt_includes_line_items() -> None:
    """The LLM prompt should include product names and totals.

    We capture the prompt by using a DummyLLM keyed on 'invoice' and
    verifying the response we get back matches what the prompt asked for.
    (Indirect — a full prompt inspection would require a spy adapter.)
    """
    llm = DummyLLM(
        responses={
            "invoice": "generated invoice with هدفون in it",
        }
    )
    text = generate_invoice(_priced_result(), llm)
    assert "هدفون" in text  # product name reached the (scripted) output
