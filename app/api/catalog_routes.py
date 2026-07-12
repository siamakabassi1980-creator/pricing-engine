"""Catalog CRUD HTTP endpoints (feature 003, T2.1).

Thin dispatch layer: each endpoint validates the request shape (Pydantic
does this automatically), delegates to catalog/service.py, and maps the
service's conceptual exceptions to HTTP status codes. The route knows
nothing about pricing — it is a separate concern from routes.py.

Error mapping:
- ProductNotFound      -> 404
- ProductAlreadyExists -> 409
- id mismatch (body vs path) -> 422
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.routes import get_db_session
from app.catalog.schemas import ProductCreate, ProductOut, ProductUpdate
from app.catalog.service import (
    ProductAlreadyExists,
    ProductNotFound,
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)

router = APIRouter(prefix="/products", tags=["catalog"])


def _to_out(product: object) -> ProductOut:
    """Map an ORM Product row to the ProductOut response schema."""
    return ProductOut.model_validate(product)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_endpoint(
    data: ProductCreate,
    session: Session = Depends(get_db_session),
) -> ProductOut:
    """Create a new product."""
    try:
        product = create_product(session, data)
    except ProductAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"product already exists: {exc.product_id}",
        ) from exc
    return _to_out(product)


@router.get("", response_model=list[ProductOut])
def list_endpoint(
    session: Session = Depends(get_db_session),
) -> list[ProductOut]:
    """List all products, ordered by id."""
    return [_to_out(p) for p in list_products(session)]


@router.get("/{product_id}", response_model=ProductOut)
def get_endpoint(
    product_id: str,
    session: Session = Depends(get_db_session),
) -> ProductOut:
    """Fetch one product by id."""
    try:
        product = get_product(session, product_id)
    except ProductNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"product not found: {exc.product_id}",
        ) from exc
    return _to_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_endpoint(
    product_id: str,
    data: ProductUpdate,
    session: Session = Depends(get_db_session),
) -> ProductOut:
    """Replace a product's name_fa and unit_price. id is immutable."""
    if data.id != product_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="id in body must match id in path",
        )
    try:
        product = update_product(session, product_id, data)
    except ProductNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"product not found: {exc.product_id}",
        ) from exc
    return _to_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endpoint(
    product_id: str,
    session: Session = Depends(get_db_session),
) -> Response:
    """Delete a product (see ADR-0003 restore-on-reseed caveat)."""
    try:
        delete_product(session, product_id)
    except ProductNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"product not found: {exc.product_id}",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
