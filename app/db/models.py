"""SQLAlchemy ORM models for the pricing engine.

Only two tables in MVP: products (the catalog seed) and customer_tiers
(discount rates per tier). No order/invoice persistence — pricing is stateless.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    """A product in the seed catalog.

    unit_price is the ONLY source of truth for price — never trust LLM output
    for price (security decision documented in data-model.md).
    """

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_fa: Mapped[str] = mapped_column(String(128), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class CustomerTier(Base):
    """A customer tier with its discount rate (Category 2 tunable).

    The discount_rate here is the per-tier VIP discount. Seasonal discount
    is a config value, not a DB row, because it is global (not per-tier).
    """

    __tablename__ = "customer_tiers"

    tier: Mapped[str] = mapped_column(String(32), primary_key=True)
    discount_rate: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
