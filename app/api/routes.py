"""POST /price endpoint — thin dispatch to the three layers.

This is the ONLY place where the three layers (Perception, Decision,
Generation) are wired together at the HTTP boundary. The route itself is
deliberately thin: it delegates to the layers and only handles the
HTTP-shaped concerns (mapping PriceResult -> HTTP status).

Boundary rule (per T3.1): Generation is called ONLY for status="priced".
For status="rejected", rejection_reason is returned directly as HTTP 422
without calling the LLM.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import (
    LineItemOut,
    PriceRequest,
    PriceResponse,
    RejectionDetail,
)
from app.config import Settings, get_settings
from app.db.models import Product
from app.decision.service import price as decision_price
from app.generation.service import generate_invoice
from app.perception.llm_adapter import build_llm_adapter
from app.perception.service import parse_request

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session() -> Generator[Session, None, None]:
    """Default session dependency. Overridden in tests via app.dependency_overrides."""
    from app.db.session import configure_session_factory, create_app_engine

    settings = get_settings()
    engine = create_app_engine(settings.database_url)
    factory = configure_session_factory(engine)
    with factory() as session:
        yield session


def _build_catalog_and_prices(
    session: Session,
) -> tuple[dict[str, str], dict[str, Decimal], dict[str, str]]:
    """Load the catalog from the DB.

    Returns three dicts keyed by product_id:
    - name lookup (for Perception matching)
    - price lookup (for Decision — NEVER from LLM)
    - name for display in results (same as name lookup; kept separate for clarity)
    """
    products = session.scalars(select(Product)).all()
    catalog: dict[str, str] = {p.id: p.name_fa for p in products}
    prices: dict[str, Decimal] = {p.id: p.unit_price for p in products}
    display_names: dict[str, str] = {p.id: p.name_fa for p in products}
    return catalog, prices, display_names


@router.post("/price", response_model=PriceResponse)
def price_endpoint(
    payload: PriceRequest,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> PriceResponse:
    """Price a natural-language purchase request."""
    # --- Layer 1: Perception (parse Farsi -> PurchaseRequest) ---
    catalog, catalog_prices, display_names = _build_catalog_and_prices(session)
    llm = build_llm_adapter(settings)
    purchase_request = parse_request(
        request_text=payload.request_text,
        catalog=catalog,
        catalog_prices=catalog_prices,
        llm=llm,
        customer_tier=payload.context.customer_tier,  # type: ignore[arg-type]
        season=payload.context.season,  # type: ignore[arg-type]
    )

    # --- Layer 2: Decision (deterministic pricing) ---
    result = decision_price(purchase_request, display_names, settings)

    # --- Boundary rule: rejected -> HTTP 422, NO LLM call ---
    if result.status == "rejected":
        raise HTTPException(
            status_code=422,
            detail=RejectionDetail(
                rejection_reason=result.rejection_reason or "درخواست رد شد",
            ).model_dump(),
        )

    # --- Layer 3: Generation (only for priced results) ---
    invoice_text = generate_invoice(result, llm)

    # --- Shape the success response ---
    line_items_out = [
        LineItemOut(
            product_id=item.product_id,
            product_name=item.product_name,
            qty=item.qty,
            unit_price=str(item.unit_price),
            line_total=str(item.line_total),
        )
        for item in result.line_items
    ]
    return PriceResponse(
        line_items=line_items_out,
        base=str(result.base),
        discount=str(result.discount),
        discount_reason=result.discount_reason,
        subtotal=str(result.subtotal),
        tax=str(result.tax),
        total=str(result.total),
        invoice_text=invoice_text,
        status="priced",
        rejection_reason=None,
    )
