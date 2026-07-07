"""Domain dataclasses for the Decision layer.

These are pure data containers that flow through the pricing pipeline:
- LineItemRequest: output of Perception, input to Decision.
- PurchaseRequest: the full parsed request.
- LineItemResult / PriceResult: output of Decision, input to Generation.

These are NOT SQLAlchemy models — they are plain domain types. The ORM
models live in app/db/models.py.

Design rule (security, from data-model.md): unit_price NEVER comes from the
LLM. It is injected from the catalog. Perception only extracts product_id
and qty; the Decision layer (or the orchestration above it) looks up the
price from the DB.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Tier = Literal["regular", "special"]
Season = Literal["normal", "sale"]
PricingStatus = Literal["priced", "rejected"]


@dataclass(frozen=True)
class LineItemRequest:
    """A single line item parsed from the natural-language request.

    unit_price is injected from the catalog, NOT from the LLM output.
    """

    product_id: str
    qty: int
    unit_price: Decimal


@dataclass(frozen=True)
class PurchaseRequest:
    """The full parsed request handed to the Decision layer."""

    items: list[LineItemRequest]
    customer_tier: Tier
    season: Season


@dataclass(frozen=True)
class LineItemResult:
    """A priced line item in the result."""

    product_id: str
    product_name: str
    qty: int
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class PriceResult:
    """The final pricing result.

    If status == "rejected", line_items is empty and rejection_reason holds
    the human-readable (Farsi) reason. The Decision layer NEVER raises — it
    always returns a PriceResult.
    """

    line_items: list[LineItemResult]
    base: Decimal
    discount: Decimal
    discount_reason: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    status: PricingStatus
    rejection_reason: str | None = None

    @staticmethod
    def rejected(reason: str) -> PriceResult:
        """Build a rejected result with zeroed amounts."""
        return PriceResult(
            line_items=[],
            base=Decimal("0"),
            discount=Decimal("0"),
            discount_reason="",
            subtotal=Decimal("0"),
            tax=Decimal("0"),
            total=Decimal("0"),
            status="rejected",
            rejection_reason=reason,
        )
