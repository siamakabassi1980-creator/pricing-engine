"""Idempotent seed data for the pricing engine.

Running seed_database() twice must be a no-op on the second run (0 inserts,
all rows skipped). This is tested explicitly in tests/test_seed.py.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CustomerTier, Product

# Fixed seed data — matches data-model.md exactly.
PRODUCTS_SEED: list[tuple[str, str, Decimal]] = [
    ("headphone-x", "هدفون مدل X", Decimal("150000")),
    ("keyboard-y", "کیبورد مدل Y", Decimal("800000")),
    ("mouse-z", "ماوس مدل Z", Decimal("250000")),
    ("monitor-m", "مانیتور مدل M", Decimal("3500000")),
    ("cable-c", "کابل مدل C", Decimal("45000")),
    ("speaker-s", "اسپیکر مدل S", Decimal("650000")),
    ("webcam-w", "وب‌کم مدل W", Decimal("1200000")),
    ("adapter-a", "آداپتور مدل A", Decimal("95000")),
]

CUSTOMER_TIERS_SEED: list[tuple[str, Decimal]] = [
    ("regular", Decimal("0.00")),
    ("special", Decimal("0.15")),  # VIP 15% — Category 2
]


def seed_database(session: Session) -> dict[str, int]:
    """Seed products and customer_tiers idempotently.

    Returns a dict with counts of inserted vs skipped rows, so callers and
    tests can verify idempotency (second run should show 0 inserts).
    """
    inserted_products = 0
    skipped_products = 0
    for product_id, name_fa, unit_price in PRODUCTS_SEED:
        existing_product = session.scalar(select(Product).where(Product.id == product_id))
        if existing_product is not None:
            skipped_products += 1
            continue
        session.add(Product(id=product_id, name_fa=name_fa, unit_price=unit_price))
        inserted_products += 1

    inserted_tiers = 0
    skipped_tiers = 0
    for tier, discount_rate in CUSTOMER_TIERS_SEED:
        existing_tier = session.scalar(select(CustomerTier).where(CustomerTier.tier == tier))
        if existing_tier is not None:
            skipped_tiers += 1
            continue
        session.add(CustomerTier(tier=tier, discount_rate=discount_rate))
        inserted_tiers += 1

    session.commit()

    return {
        "products_inserted": inserted_products,
        "products_skipped": skipped_products,
        "tiers_inserted": inserted_tiers,
        "tiers_skipped": skipped_tiers,
    }
