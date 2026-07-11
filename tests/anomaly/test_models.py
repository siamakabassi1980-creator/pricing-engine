"""Tests for anomaly layer (T1.1-T1.3, feature 002).

Tests the three-state model, prompt builder, and service orchestration
including the critical fail-open behavior (AC5).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.anomaly.models import AnomalyResult
from app.anomaly.prompts import build_anomaly_prompt
from app.anomaly.service import assess_anomaly
from app.decision.models import LineItemRequest, LineItemResult, PriceResult
from app.perception.llm_adapter import DummyLLM

# --- Helpers ---


def _priced_result(items: list[LineItemRequest], base: Decimal) -> PriceResult:
    """Build a priced PriceResult for testing."""
    line_items = [
        LineItemResult(
            product_id=item.product_id,
            product_name=item.product_id,
            qty=item.qty,
            unit_price=item.unit_price,
            line_total=item.unit_price * item.qty,
        )
        for item in items
    ]
    return PriceResult(
        line_items=line_items,
        base=base,
        discount=Decimal("0"),
        discount_reason="",
        subtotal=base,
        tax=base * Decimal("0.09"),
        total=base + base * Decimal("0.09"),
        status="priced",
    )


def _items(qty: int = 5, price: Decimal = Decimal("1000")) -> list[LineItemRequest]:
    return [LineItemRequest(product_id="test-product", qty=qty, unit_price=price)]


# --- T1.1: AnomalyResult model ---


def test_anomaly_result_clean_factory() -> None:
    """clean() produces checked_clean with no reason."""
    result = AnomalyResult.clean()
    assert result.anomaly_status == "checked_clean"
    assert result.anomaly_reason is None


def test_anomaly_result_flagged_factory() -> None:
    """flagged() produces checked_flagged with reason."""
    result = AnomalyResult.flagged("مشکوک", ["qty high"])
    assert result.anomaly_status == "checked_flagged"
    assert result.anomaly_reason == "مشکوک"
    assert result.deterministic_signals == ["qty high"]


def test_anomaly_result_skipped_factory() -> None:
    """skipped() produces check_skipped (LLM unavailable)."""
    result = AnomalyResult.skipped()
    assert result.anomaly_status == "check_skipped"
    assert result.anomaly_reason is None


def test_anomaly_result_is_frozen() -> None:
    """AnomalyResult is immutable."""
    from dataclasses import FrozenInstanceError

    result = AnomalyResult.clean()
    with pytest.raises(FrozenInstanceError):
        result.anomaly_status = "checked_flagged"  # type: ignore[misc]


# --- T1.2: Prompt builder ---


def test_prompt_includes_request_text_and_signals() -> None:
    """Prompt contains request text and deterministic signals."""
    prompt = build_anomaly_prompt(
        request_text="۵۰۰ عدد هدفون",
        base="500000",
        total="545000",
        item_count=1,
        deterministic_signals=["تعداد غیرعادی"],
    )
    assert "۵۰۰ عدد هدفون" in prompt
    assert "تعداد غیرعادی" in prompt


def test_prompt_with_no_signals_shows_empty_list() -> None:
    """Empty signals list renders as [] in the prompt."""
    prompt = build_anomaly_prompt(
        request_text="نرمال",
        base="1000",
        total="1090",
        item_count=1,
        deterministic_signals=[],
    )
    assert "[]" in prompt


# --- T1.3: Service orchestration ---


def test_service_clean_when_llm_says_not_suspicious() -> None:
    """LLM says not suspicious, no deterministic signals -> checked_clean."""
    llm = DummyLLM(responses={"anomaly": '{"suspicious": false, "reason": ""}'})
    result = assess_anomaly(
        price_result=_priced_result(_items(qty=5), Decimal("5000")),
        request_text="۵ عدد",
        items=_items(qty=5),
        llm=llm,
    )
    assert result.anomaly_status == "checked_clean"


def test_service_flagged_when_llm_says_suspicious() -> None:
    """LLM says suspicious -> checked_flagged with reason."""
    llm = DummyLLM(responses={"anomaly": '{"suspicious": true, "reason": "ترکیب عجیب"}'})
    result = assess_anomaly(
        price_result=_priced_result(_items(qty=5), Decimal("5000")),
        request_text="۵ عدد",
        items=_items(qty=5),
        llm=llm,
    )
    assert result.anomaly_status == "checked_flagged"
    assert "ترکیب عجیب" in (result.anomaly_reason or "")


def test_service_flagged_when_deterministic_signal_only() -> None:
    """No LLM suspicion, but deterministic signal -> checked_flagged."""
    llm = DummyLLM(responses={"anomaly": '{"suspicious": false, "reason": ""}'})
    # qty=200 > threshold 100 -> deterministic signal
    result = assess_anomaly(
        price_result=_priced_result(_items(qty=200), Decimal("200000")),
        request_text="۲۰۰ عدد",
        items=_items(qty=200),
        llm=llm,
        qty_threshold=100,
    )
    assert result.anomaly_status == "checked_flagged"
    assert result.deterministic_signals is not None
    assert len(result.deterministic_signals) >= 1


def test_service_skipped_when_llm_returns_garbage() -> None:
    """LLM returns unparseable response -> check_skipped (fail-open)."""
    garbage_llm = DummyLLM(responses={"anomaly": "not json at all!!!"})
    result = assess_anomaly(
        price_result=_priced_result(_items(qty=5), Decimal("5000")),
        request_text="۵ عدد",
        items=_items(qty=5),
        llm=garbage_llm,
    )
    assert result.anomaly_status == "check_skipped"


def test_service_skipped_when_llm_raises_exception() -> None:
    """LLM raises exception -> check_skipped (fail-open, AC5)."""

    class ExplodingLLM:
        def complete(self, prompt: str) -> str:
            raise ConnectionError("LLM is down")

    result = assess_anomaly(
        price_result=_priced_result(_items(qty=5), Decimal("5000")),
        request_text="۵ عدد",
        items=_items(qty=5),
        llm=ExplodingLLM(),
    )
    assert result.anomaly_status == "check_skipped"


def test_service_price_result_never_modified() -> None:
    """PriceResult passed in is never mutated (AC1)."""
    price_result = _priced_result(_items(qty=5), Decimal("5000"))
    original_status = price_result.status
    original_total = price_result.total

    llm = DummyLLM(responses={"anomaly": '{"suspicious": true, "reason": "test"}'})
    assess_anomaly(
        price_result=price_result,
        request_text="test",
        items=_items(qty=5),
        llm=llm,
    )
    # PriceResult unchanged.
    assert price_result.status == original_status
    assert price_result.total == original_total


def test_service_combines_llm_and_deterministic_reasons() -> None:
    """Both LLM suspicion and deterministic signal -> combined reason."""
    llm = DummyLLM(responses={"anomaly": '{"suspicious": true, "reason": "لحن مشکوک"}'})
    result = assess_anomaly(
        price_result=_priced_result(_items(qty=200), Decimal("200000")),
        request_text="۲۰۰ عدد",
        items=_items(qty=200),
        llm=llm,
        qty_threshold=100,
    )
    assert result.anomaly_status == "checked_flagged"
    assert result.anomaly_reason is not None
    assert "لحن مشکوک" in result.anomaly_reason
    assert "دترمینیستیک" in result.anomaly_reason
