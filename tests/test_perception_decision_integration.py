"""True integration test: Perception -> Decision pipeline (T1.5).

Unlike the unit test in tests/decision/test_service.py which constructs a
PurchaseRequest(items=[]) by hand, THIS test starts from the real entry
point of Perception (parse_request with a DummyLLM returning garbage) and
feeds its output to Decision (price). This proves the two layers are
actually wired together — not just that each works in isolation.
"""

from __future__ import annotations

from decimal import Decimal

from app.config import Settings
from app.decision.service import price
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


def test_pipeline_unparseable_llm_rejected_not_silent_zero_order() -> None:
    """Real Perception->Decision path: LLM returns garbage -> rejected.

    This is the TRUE integration test for the T1.5 gap:
    1. DummyLLM returns an unparseable response (not JSON).
    2. parse_request() processes it -> PurchaseRequest with empty items.
    3. price() processes THAT -> PriceResult with status='rejected'.

    If we only hand-built PurchaseRequest(items=[]) we'd be testing Decision
    alone; this test proves the whole pipeline rejects correctly.
    """
    # Step 1: LLM returns garbage.
    garbage_llm = DummyLLM(responses={"parse": "this is totally not json!!!"})

    # Step 2: Perception processes it.
    purchase_request = parse_request(
        request_text="هرچی",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=garbage_llm,
    )
    # The intermediate state: Perception produced empty items (safe default).
    assert purchase_request.items == []

    # Step 3: Decision processes THAT — must reject, not price a 0-toman order.
    result = price(purchase_request, CATALOG, Settings(_env_file=None))  # type: ignore[call-arg]
    assert result.status == "rejected"
    assert result.rejection_reason is not None
    assert "آیتم" in result.rejection_reason


def test_pipeline_valid_llm_produces_priced_result() -> None:
    """Happy path integration: valid LLM response -> priced result.

    Proves the pipeline works end-to-end for the GOOD case too, not just
    the rejection case. This guards against over-aggressive rejection.
    """
    valid_llm = DummyLLM(
        responses={
            "parse": '{"items": [{"product_id": "headphone-x", "qty": 2}]}',
        }
    )
    purchase_request = parse_request(
        request_text="۲ هدفون",
        catalog=CATALOG,
        catalog_prices=CATALOG_PRICES,
        llm=valid_llm,
    )
    result = price(purchase_request, CATALOG, Settings(_env_file=None))  # type: ignore[call-arg]
    assert result.status == "priced"
    assert len(result.line_items) == 1
    assert result.base == Decimal("300000")  # 2 * 150000
