"""Catalog CRUD service (feature 003, T1.1).

Pure deterministic logic over the existing products table. Maps DB
errors to conceptual exceptions (ProductNotFound, ProductAlreadyExists)
that the HTTP layer translates to 404 / 409. The service itself knows
nothing about HTTP.

Audit log (AC9): when a PUT changes unit_price, the old/new values and
a UTC ISO-8601 timestamp are emitted via the logging module. This is a
retrospective trail, not a preventive barrier — see spec.md AC9 and
ADR-0003.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalog.schemas import ProductCreate, ProductUpdate
from app.db.models import Product

logger = logging.getLogger(__name__)


class ProductNotFound(Exception):
    """Raised when get/update/delete targets a missing product id."""

    def __init__(self, product_id: str) -> None:
        super().__init__(f"product not found: {product_id}")
        self.product_id = product_id


class ProductAlreadyExists(Exception):
    """Raised when create hits a duplicate primary key."""

    def __init__(self, product_id: str) -> None:
        super().__init__(f"product already exists: {product_id}")
        self.product_id = product_id


def _get_or_raise(session: Session, product_id: str) -> Product:
    """Fetch a product by id or raise ProductNotFound."""
    product = session.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise ProductNotFound(product_id)
    return product


def create_product(session: Session, data: ProductCreate) -> Product:
    """Insert a new product. Raises ProductAlreadyExists on duplicate id."""
    product = Product(
        id=data.id,
        name_fa=data.name_fa,
        unit_price=data.unit_price,
    )
    session.add(product)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ProductAlreadyExists(data.id) from exc
    session.refresh(product)
    return product


def list_products(session: Session) -> list[Product]:
    """Return all products (order is unspecified, like feature 001)."""
    return list(session.scalars(select(Product)).all())


def get_product(session: Session, product_id: str) -> Product:
    """Fetch one product or raise ProductNotFound."""
    return _get_or_raise(session, product_id)


def update_product(session: Session, product_id: str, data: ProductUpdate) -> Product:
    """Replace a product's name_fa and unit_price. id is immutable.

    Emits an audit-log line (AC9) only when unit_price actually changes.
    """
    product = _get_or_raise(session, product_id)
    old_price = product.unit_price
    product.name_fa = data.name_fa
    product.unit_price = data.unit_price
    session.commit()
    session.refresh(product)

    if product.unit_price != old_price:
        logger.info(
            "unit_price_changed product_id=%s old=%s new=%s at=%s",
            product.id,
            old_price,
            product.unit_price,
            datetime.now(UTC).isoformat(),
        )
    return product


def delete_product(session: Session, product_id: str) -> None:
    """Remove a product. Raises ProductNotFound if it does not exist.

    Note (ADR-0003, restore-on-reseed): if the deleted product is a
    seed entry, seed_database() will recreate it on the next run.
    """
    product = _get_or_raise(session, product_id)
    session.delete(product)
    session.commit()
