"""Unit tests for the catalog CRUD service (T1.1).

Uses an in-memory SQLite session. Covers happy paths plus the three
conceptual exceptions (ProductNotFound, ProductAlreadyExists) and the
audit-log behavior (AC9) via caplog.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.catalog.schemas import ProductCreate, ProductUpdate
from app.catalog.service import (
    ProductAlreadyExists,
    ProductNotFound,
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)
from app.db.base import Base


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Fresh in-memory SQLite session with schema created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sess = Session(engine)
    yield sess
    sess.close()


# --- helpers -----------------------------------------------------------------


def _make(session: Session, id_: str = "x", price: Decimal = Decimal("100")) -> None:
    create_product(
        session,
        ProductCreate(id=id_, name_fa="نام", unit_price=price),
    )


# --- create ------------------------------------------------------------------


def test_create_returns_product_with_fields(session: Session) -> None:
    p = create_product(
        session,
        ProductCreate(id="abc", name_fa="هدفون", unit_price=Decimal("150000")),
    )
    assert p.id == "abc"
    assert p.name_fa == "هدفون"
    assert p.unit_price == Decimal("150000")


def test_create_duplicate_raises_already_exists(session: Session) -> None:
    _make(session, id_="dup")
    with pytest.raises(ProductAlreadyExists) as exc:
        _make(session, id_="dup")
    assert exc.value.product_id == "dup"
    # session must be usable after a failed create
    _make(session, id_="other")


# --- list / get --------------------------------------------------------------


def test_list_returns_all(session: Session) -> None:
    _make(session, id_="a")
    _make(session, id_="b")
    ids = {p.id for p in list_products(session)}
    assert ids == {"a", "b"}


def test_list_empty_returns_empty_list(session: Session) -> None:
    assert list_products(session) == []


def test_get_returns_product(session: Session) -> None:
    _make(session, id_="findme", price=Decimal("999"))
    p = get_product(session, "findme")
    assert p.unit_price == Decimal("999")


def test_get_missing_raises_not_found(session: Session) -> None:
    with pytest.raises(ProductNotFound) as exc:
        get_product(session, "ghost")
    assert exc.value.product_id == "ghost"


# --- update + audit log (AC9) ------------------------------------------------


def test_update_changes_name_and_price(session: Session) -> None:
    _make(session, id_="u", price=Decimal("100"))
    updated = update_product(
        session,
        "u",
        ProductUpdate(id="u", name_fa="نام جدید", unit_price=Decimal("200")),
    )
    assert updated.name_fa == "نام جدید"
    assert updated.unit_price == Decimal("200")


def test_update_missing_raises_not_found(session: Session) -> None:
    with pytest.raises(ProductNotFound):
        update_product(
            session,
            "ghost",
            ProductUpdate(id="ghost", name_fa="x", unit_price=Decimal("1")),
        )


def test_update_price_change_logs_audit(session: Session, caplog: pytest.LogCaptureFixture) -> None:
    _make(session, id_="p", price=Decimal("100"))
    caplog.set_level(logging.INFO, logger="app.catalog.service")
    update_product(
        session,
        "p",
        ProductUpdate(id="p", name_fa="نام", unit_price=Decimal("200")),
    )
    audit_records = [r for r in caplog.records if "unit_price_changed" in r.message]
    assert len(audit_records) == 1
    msg = audit_records[0].getMessage()
    assert "product_id=p" in msg
    assert "old=100" in msg
    assert "new=200" in msg
    # ISO-8601 UTC timestamp present
    assert "at=" in msg


def test_update_no_price_change_does_not_log(
    session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    _make(session, id_="p", price=Decimal("100"))
    caplog.set_level(logging.INFO, logger="app.catalog.service")
    # Only the name changes; price stays 100.
    update_product(
        session,
        "p",
        ProductUpdate(id="p", name_fa="نام دیگر", unit_price=Decimal("100")),
    )
    audit_records = [r for r in caplog.records if "unit_price_changed" in r.message]
    assert audit_records == []


def test_update_price_to_same_value_does_not_log(
    session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    """Decimal equality (not string equality) gates the log."""
    _make(session, id_="p", price=Decimal("100"))
    caplog.set_level(logging.INFO, logger="app.catalog.service")
    update_product(
        session,
        "p",
        ProductUpdate(id="p", name_fa="نام", unit_price=Decimal("100.00")),
    )
    audit_records = [r for r in caplog.records if "unit_price_changed" in r.message]
    assert audit_records == []


# --- delete ------------------------------------------------------------------


def test_delete_removes_product(session: Session) -> None:
    _make(session, id_="del")
    delete_product(session, "del")
    with pytest.raises(ProductNotFound):
        get_product(session, "del")


def test_delete_missing_raises_not_found(session: Session) -> None:
    with pytest.raises(ProductNotFound):
        delete_product(session, "ghost")
