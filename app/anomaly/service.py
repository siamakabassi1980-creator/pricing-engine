"""Anomaly assessment service — orchestration + fail-open.

This is the orchestration layer that combines:
1. Deterministic signals (from decision/rules.py — pure, property-tested).
2. Qualitative analysis (from LLM — exempt from PBT per ADR-0002).

Boundary rule: PriceResult is NEVER modified. This service reads it and
produces a separate AnomalyResult.

Fail-open policy (AC5): if the LLM is unavailable, returns check_skipped
(NOT checked_flagged). Rationale: prefer to miss a suspicious request
rather than block all requests.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from app.anomaly.models import AnomalyResult
from app.anomaly.prompts import build_anomaly_prompt
from app.decision.models import LineItemRequest, PriceResult
from app.decision.rules import check_deterministic_signals
from app.perception.llm_adapter import LLMAdapter, parse_json_response

logger = logging.getLogger(__name__)


def assess_anomaly(
    price_result: PriceResult,
    request_text: str,
    items: list[LineItemRequest],
    llm: LLMAdapter,
    qty_threshold: int = 100,
    base_threshold: Decimal = Decimal("10000000"),
) -> AnomalyResult:
    """Assess whether a priced request is anomalous.

    Combines deterministic signals (qty, base thresholds) with qualitative
    LLM analysis. Returns a three-state AnomalyResult.

    Args:
        price_result: The priced result (read-only, never modified).
        request_text: Original request text for qualitative analysis.
        items: Line items for deterministic signal check.
        llm: LLM adapter (DummyLLM in tests, DeepSeek in prod).
        qty_threshold: Category 2 threshold for large quantity (default 100).
        base_threshold: Category 2 threshold for large base (default 10M).

    Returns:
        AnomalyResult with anomaly_status in {checked_clean, checked_flagged, check_skipped}.
    """
    # Step 1: deterministic signals (Category 2, property-tested in rules.py).
    det_signals = check_deterministic_signals(
        items=items,
        base=price_result.base,
        qty_threshold=qty_threshold,
        base_threshold=base_threshold,
    )

    # Step 2: qualitative LLM analysis (exempt from PBT per ADR-0002).
    prompt = build_anomaly_prompt(
        request_text=request_text,
        base=str(price_result.base),
        total=str(price_result.total),
        item_count=len(price_result.line_items),
        deterministic_signals=det_signals,
    )

    try:
        raw = llm.complete(prompt)
        parsed = parse_json_response(raw)
    except Exception as e:  # noqa: BLE001 — fail-open: any LLM/parse failure
        logger.warning("Anomaly LLM unavailable or unparseable: %s. Fail-open.", e)
        return AnomalyResult.skipped()

    # Parse LLM response.
    if not isinstance(parsed, dict):
        logger.warning("Anomaly LLM returned non-dict: %s. Fail-open.", type(parsed))
        return AnomalyResult.skipped()

    suspicious = parsed.get("suspicious")
    reason = parsed.get("reason", "")

    if suspicious is not True:
        # LLM says not suspicious. But deterministic signals may still flag.
        if det_signals:
            return AnomalyResult.flagged(
                reason="سیگنال‌های دترمینیستیک: " + "; ".join(det_signals),
                signals=det_signals,
            )
        return AnomalyResult.clean()

    # LLM says suspicious. Combine with deterministic signals for the reason.
    all_reasons: list[str] = []
    if reason:
        all_reasons.append(reason)
    if det_signals:
        all_reasons.append("سیگنال‌های دترمینیستیک: " + "; ".join(det_signals))

    return AnomalyResult.flagged(
        reason=" | ".join(all_reasons) if all_reasons else "مشکوک",
        signals=det_signals if det_signals else None,
    )
