"""AnomalyResult — separate from PriceResult (per AC1).

Three states (per AC5, Claude's correction):
- checked_clean: LLM checked, not suspicious.
- checked_flagged: LLM checked, suspicious — flagged for human review.
- check_skipped: LLM unavailable — NOT checked (done-with-caveat pattern).

This trinary preserves the distinction between "checked and clean" vs
"not checked at all" — a bool (True/False) would lose this.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AnomalyStatus = Literal["checked_clean", "checked_flagged", "check_skipped"]


@dataclass(frozen=True)
class AnomalyResult:
    """Result of anomaly assessment — separate from PriceResult."""

    anomaly_status: AnomalyStatus
    anomaly_reason: str | None = None  # only set when checked_flagged
    deterministic_signals: list[str] | None = None  # signals that triggered

    @staticmethod
    def clean() -> AnomalyResult:
        """Build a checked_clean result."""
        return AnomalyResult(anomaly_status="checked_clean")

    @staticmethod
    def flagged(reason: str, signals: list[str] | None = None) -> AnomalyResult:
        """Build a checked_flagged result with reason."""
        return AnomalyResult(
            anomaly_status="checked_flagged",
            anomaly_reason=reason,
            deterministic_signals=signals,
        )

    @staticmethod
    def skipped() -> AnomalyResult:
        """Build a check_skipped result (LLM unavailable)."""
        return AnomalyResult(anomaly_status="check_skipped")
