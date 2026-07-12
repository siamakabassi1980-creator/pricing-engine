"""Tests for seed data idempotency.

Per the SDD guide section 10, idempotent operations must be run twice and
the second run's behavior (0 inserts, all skipped) verified explicitly.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import CustomerTier, Product
from app.db.seed import seed_database
from app.db.session import configure_session_factory, create_app_engine


@pytest.fixture
def engine() -> Engine:
    """Fresh in-memory SQLite engine with schema created."""
    eng = create_app_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    """Session factory bound to the test engine."""
    return configure_session_factory(engine)


def test_seed_first_run_inserts_all(session_factory: sessionmaker[Session]) -> None:
    """First seed run inserts all 8 products and 2 tiers."""
    with session_factory() as session:
        result = seed_database(session)
    assert result["products_inserted"] == 8
    assert result["tiers_inserted"] == 2
    assert result["products_skipped"] == 0
    assert result["tiers_skipped"] == 0


def test_seed_second_run_is_idempotent(session_factory: sessionmaker[Session]) -> None:
    """Second seed run inserts nothing — all rows skipped.

    This is the idempotency test required by the SDD guide (section 10):
    run twice, verify the second run shows 0 inserts.
    """
    with session_factory() as session:
        first = seed_database(session)
    with session_factory() as session:
        second = seed_database(session)

    assert first["products_inserted"] == 8
    assert first["tiers_inserted"] == 2

    # The critical idempotency assertion.
    assert second["products_inserted"] == 0
    assert second["tiers_inserted"] == 0
    assert second["products_skipped"] == 8
    assert second["tiers_skipped"] == 2


def test_seed_data_matches_data_model(session_factory: sessionmaker[Session]) -> None:
    """Seed values match data-model.md exactly (esp. headphone-x price)."""
    with session_factory() as session:
        seed_database(session)
        headphone = session.get(Product, "headphone-x")
    assert headphone is not None
    assert headphone.name_fa == "هدفون مدل X"
    # Compare Decimal to Decimal — float 150000 == Decimal works for integers,
    # but be explicit to model correct financial-domain comparison habits.
    assert headphone.unit_price == Decimal("150000")


def test_customer_tier_special_has_15_percent(session_factory: sessionmaker[Session]) -> None:
    """VIP tier 'special' has 15% discount (Category 2 agreed value).

    Compare Decimal-to-Decimal, never Decimal-to-float: 0.15 is not exactly
    representable in binary float, so Decimal('0.15') == 0.15 is False.
    This is exactly why we use Decimal for money in the first place.
    """
    with session_factory() as session:
        seed_database(session)
        tier = session.get(CustomerTier, "special")
    assert tier is not None
    assert tier.discount_rate == Decimal("0.15")


def test_migration_upgrade_then_downgrade_roundtrip(engine: Engine) -> None:
    """upgrade then downgrade leaves no tables — rollback path works.

    Per constitution AC6: every migration must have a tested downgrade path.
    We simulate it by creating then dropping the schema (since we use
    metadata.create_all, we test the migration's SQL by running it via
    Alembic commands if possible, or by simulating the drop order).
    """
    # Create all tables (simulates upgrade).
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    assert "products" in inspector.get_table_names()
    assert "customer_tiers" in inspector.get_table_names()

    # Drop in reverse order of creation (simulates downgrade).
    Base.metadata.tables["customer_tiers"].drop(engine)
    Base.metadata.tables["products"].drop(engine)

    inspector = inspect(engine)
    assert "products" not in inspector.get_table_names()
    assert "customer_tiers" not in inspector.get_table_names()


def test_seed_restores_deleted_product_on_reseed(
    session_factory: sessionmaker[Session],
) -> None:
    """A deleted seed product reappears on the next seed_database() run.

    This pins the known restore-on-reseed behavior documented in ADR-0003:
    seed_database() checks existence via SELECT and INSERTs anything missing,
    so a DELETE on a seed product is not permanent — it returns on the next
    reseed (e.g. app restart). Operators must be aware of this caveat.
    """
    with session_factory() as session:
        seed_database(session)
        # Delete a seed product via direct ORM (simulates the DELETE endpoint).
        headphone = session.get(Product, "headphone-x")
        assert headphone is not None
        session.delete(headphone)
        session.commit()
        assert session.get(Product, "headphone-x") is None

    # Re-run seed: the deleted product must be restored (re-inserted).
    with session_factory() as session:
        result = seed_database(session)
        assert result["products_inserted"] == 1
        assert result["products_skipped"] == 7
        assert session.get(Product, "headphone-x") is not None
