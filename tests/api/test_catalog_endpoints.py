"""Integration tests for the catalog CRUD endpoints (T2.2).

Uses the FastAPI TestClient with in-memory SQLite + the real catalog
router. Mirrors the fixture pattern from tests/api/test_price_endpoint.py.
"""

from __future__ import annotations

from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes import get_db_session
from app.db.base import Base
from app.main import create_app


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Test client with an empty in-memory SQLite DB."""
    # allow_dummy_fallback=True so create_app()'s startup LLM gate passes,
    # even though catalog endpoints never call the LLM (the gate runs for
    # the whole app at startup). See ADR-0001 security addendum.
    from app.config import Settings

    def _test_settings() -> Settings:
        return Settings(_env_file=None, allow_dummy_fallback=True)  # type: ignore[call-arg]

    monkeypatch.setattr("app.main.get_settings", _test_settings)
    app = create_app()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def _get_test_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = _get_test_session
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def _create(client: TestClient, id_: str = "x", price: str = "100") -> dict[str, object]:
    """Helper: POST a product and return the response JSON (assumes success)."""
    resp = client.post(
        "/products",
        json={"id": id_, "name_fa": "نام", "unit_price": price},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- POST /products ----------------------------------------------------------


def test_create_returns_201(client: TestClient) -> None:
    data = _create(client, id_="headphone-x", price="150000")
    assert data["id"] == "headphone-x"
    assert data["name_fa"] == "نام"
    # Compare as Decimal, never as string: the Numeric(12,2) column returns
    # "150000.00" for input "150000". Same family of bug as the
    # Decimal('0.15')==0.15 trap caught in feature 001 — Decimal scale varies
    # with storage/computation history, so string comparison is flaky.
    assert Decimal(str(data["unit_price"])) == Decimal("150000")


def test_create_duplicate_returns_409(client: TestClient) -> None:
    _create(client, id_="dup")
    resp = client.post(
        "/products",
        json={"id": "dup", "name_fa": "نام", "unit_price": "100"},
    )
    assert resp.status_code == 409


def test_create_negative_price_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/products",
        json={"id": "x", "name_fa": "نام", "unit_price": "-1"},
    )
    assert resp.status_code == 422


def test_create_three_decimal_places_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/products",
        json={"id": "x", "name_fa": "نام", "unit_price": "150000.999"},
    )
    assert resp.status_code == 422


def test_create_empty_name_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/products",
        json={"id": "x", "name_fa": "", "unit_price": "100"},
    )
    assert resp.status_code == 422


def test_create_invalid_slug_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/products",
        json={"id": "Headphone_X", "name_fa": "نام", "unit_price": "100"},
    )
    assert resp.status_code == 422


# --- GET /products and /products/{id} ----------------------------------------


def test_list_returns_all_ordered_by_id(client: TestClient) -> None:
    _create(client, id_="c-item")
    _create(client, id_="a-item")
    _create(client, id_="b-item")
    resp = client.get("/products")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert ids == ["a-item", "b-item", "c-item"]


def test_list_empty_returns_empty_array(client: TestClient) -> None:
    resp = client.get("/products")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_one_returns_product(client: TestClient) -> None:
    _create(client, id_="findme", price="999")
    resp = client.get("/products/findme")
    assert resp.status_code == 200
    assert Decimal(resp.json()["unit_price"]) == Decimal("999")


def test_get_one_missing_returns_404(client: TestClient) -> None:
    resp = client.get("/products/ghost")
    assert resp.status_code == 404


# --- PUT /products/{id} ------------------------------------------------------


def test_update_changes_fields(client: TestClient) -> None:
    _create(client, id_="u", price="100")
    resp = client.put(
        "/products/u",
        json={"id": "u", "name_fa": "نام جدید", "unit_price": "200"},
    )
    assert resp.status_code == 200
    assert resp.json()["name_fa"] == "نام جدید"
    assert Decimal(resp.json()["unit_price"]) == Decimal("200")


def test_update_missing_returns_404(client: TestClient) -> None:
    resp = client.put(
        "/products/ghost",
        json={"id": "ghost", "name_fa": "نام", "unit_price": "1"},
    )
    assert resp.status_code == 404


def test_update_id_mismatch_returns_422(client: TestClient) -> None:
    _create(client, id_="real")
    resp = client.put(
        "/products/real",
        json={"id": "different", "name_fa": "نام", "unit_price": "1"},
    )
    assert resp.status_code == 422


def test_update_negative_price_returns_422(client: TestClient) -> None:
    _create(client, id_="u")
    resp = client.put(
        "/products/u",
        json={"id": "u", "name_fa": "نام", "unit_price": "-5"},
    )
    assert resp.status_code == 422


def test_update_price_change_emits_audit_log(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    _create(client, id_="p", price="100")
    caplog.set_level(logging.INFO, logger="app.catalog.service")
    client.put(
        "/products/p",
        json={"id": "p", "name_fa": "نام", "unit_price": "200"},
    )
    records = [r for r in caplog.records if "unit_price_changed" in r.message]
    assert len(records) == 1
    assert "product_id=p" in records[0].getMessage()


def test_update_no_price_change_no_audit_log(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    _create(client, id_="p", price="100")
    caplog.set_level(logging.INFO, logger="app.catalog.service")
    client.put(
        "/products/p",
        json={"id": "p", "name_fa": "نام دیگر", "unit_price": "100"},
    )
    records = [r for r in caplog.records if "unit_price_changed" in r.message]
    assert records == []


# --- DELETE /products/{id} ---------------------------------------------------


def test_delete_returns_204(client: TestClient) -> None:
    _create(client, id_="del")
    resp = client.delete("/products/del")
    assert resp.status_code == 204
    # gone for real
    assert client.get("/products/del").status_code == 404


def test_delete_missing_returns_404(client: TestClient) -> None:
    resp = client.delete("/products/ghost")
    assert resp.status_code == 404
