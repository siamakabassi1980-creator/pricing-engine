"""Pydantic schemas for the pricing API (request/response models).

These are the wire-level contracts documented in
specs/001-pricing/contracts/price-api.md.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PriceContext(BaseModel):
    """Context for a pricing request."""

    customer_tier: str = Field(..., description='"regular" یا "special"')
    season: str = Field(..., description='"normal" یا "sale"')


class PriceRequest(BaseModel):
    """POST /price request body."""

    request_text: str = Field(..., description="درخواست به زبان طبیعی فارسی")
    context: PriceContext


class LineItemOut(BaseModel):
    """A line item in the pricing response."""

    product_id: str
    product_name: str
    qty: int
    unit_price: str  # string to preserve Decimal precision on the wire
    line_total: str


class PriceResponse(BaseModel):
    """POST /price success response (HTTP 200)."""

    line_items: list[LineItemOut]
    base: str
    discount: str
    discount_reason: str
    subtotal: str
    tax: str
    total: str
    invoice_text: str
    status: str
    rejection_reason: str | None = None


class RejectionDetail(BaseModel):
    """POST /price rejection body (HTTP 422)."""

    status: str = "rejected"
    rejection_reason: str
    line_items: list[LineItemOut] = Field(default_factory=list)
