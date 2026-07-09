"""Integration tests for the POST /price endpoint (T4.1).

Uses the FastAPI TestClient with:
- A DummyLLM injected via build_llm_adapter override (no real DeepSeek call).
- In-memory SQLite + seeded catalog via get_db_session override.
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
from app.config import Settings, get_settings
from app.db.base import Base
from app.db.models import CustomerTier, Product
from app.db.seed import CUSTOMER_TIERS_SEED, PRODUCTS_SEED
from app.db.session import configure_session_factory
from app.main import create_app
from app.perception.llm_adapter import DummyLLM


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Test client with in-memory SQLite + seeded catalog + DummyLLM.

    The DummyLLM returns a scripted parse response so Perception produces
    a valid PurchaseRequest without calling the real DeepSeek API.
    """
    app = create_app()

    # StaticPool so the in-memory SQLite DB persists across the multiple
    # connections that FastAPI's session dependency will open. Without it,
    # each new connection sees an empty database.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = configure_session_factory(engine)

    # Seed the catalog + tiers.
    with factory() as session:
        for pid, name, price in PRODUCTS_SEED:
            session.add(Product(id=pid, name_fa=name, unit_price=price))
        for tier, rate in CUSTOMER_TIERS_SEED:
            session.add(CustomerTier(tier=tier, discount_rate=rate))
        session.commit()

    # Override DB session dependency.
    def _get_test_session() -> Generator[Session, None, None]:
        with factory() as session:
            yield session

    # Override settings (no real API key needed).
    def _get_test_settings() -> Settings:
        return Settings(_env_file=None)  # type: ignore[call-arg]  # pydantic private

    app.dependency_overrides[get_db_session] = _get_test_session
    app.dependency_overrides[get_settings] = _get_test_settings

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_price_endpoint_priced_success(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid request -> 200 with full pricing.

    We monkeypatch build_llm_adapter to return a DummyLLM with a scripted
    valid response, so Perception extracts items without a real API call.
    """
    from app.api import routes

    dummy = DummyLLM(
        responses={
            "parse": '{"items": [{"product_id": "headphone-x", "qty": 20}]}',
            "invoice": "پیش‌فاکتور: ۲۰ عدد هدفون مدل X — ۳٬۰۰۰٬۰۰۰ تومان",
        }
    )
    monkeypatch.setattr(routes, "build_llm_adapter", lambda settings: dummy)

    response = test_client.post(
        "/price",
        json={
            "request_text": "۲۰ عدد هدفون مدل X",
            "context": {"customer_tier": "regular", "season": "normal"},
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "priced"
    assert len(data["line_items"]) == 1
    assert data["line_items"][0]["product_id"] == "headphone-x"
    assert data["line_items"][0]["qty"] == 20
    # Compare as Decimal (not string) — Decimal scale varies by computation history.
    assert Decimal(data["base"]) == Decimal("3000000")
    assert Decimal(data["discount"]) == Decimal("0")
    assert Decimal(data["tax"]) == Decimal("270000")
    assert Decimal(data["total"]) == Decimal("3270000")


def test_price_endpoint_rejected_returns_422(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unparseable LLM response -> empty items -> rejected -> HTTP 422."""
    from app.api import routes

    # DummyLLM returns garbage -> parse_request -> empty items -> rejected.
    garbage_llm = DummyLLM(responses={"parse": "this is totally not json!!!"})
    monkeypatch.setattr(routes, "build_llm_adapter", lambda settings: garbage_llm)

    response = test_client.post(
        "/price",
        json={
            "request_text": "نامفهوم",
            "context": {"customer_tier": "regular", "season": "normal"},
        },
    )
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["status"] == "rejected"
    assert "آیتم" in detail["rejection_reason"]


def test_price_endpoint_missing_field_returns_422_validation(test_client: TestClient) -> None:
    """Missing required field -> HTTP 422 (Pydantic validation, not pricing)."""
    response = test_client.post(
        "/price",
        json={"request_text": "فقط متن، بدون context"},
    )
    assert response.status_code == 422
    # This is a Pydantic validation error, not a pricing rejection.
    assert "detail" in response.json()


def test_price_endpoint_with_discount_special_tier(
    test_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Special tier customer gets VIP discount (15%)."""
    from app.api import routes

    dummy = DummyLLM(
        responses={
            "parse": '{"items": [{"product_id": "headphone-x", "qty": 2}]}',
            "invoice": "پیش‌فاکتور با تخفیف مشتری ویژه",
        }
    )
    monkeypatch.setattr(routes, "build_llm_adapter", lambda settings: dummy)

    response = test_client.post(
        "/price",
        json={
            "request_text": "۲ هدفون",
            "context": {"customer_tier": "special", "season": "normal"},
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert Decimal(data["base"]) == Decimal("300000")
    assert Decimal(data["discount"]) == Decimal("45000")
    assert Decimal(data["subtotal"]) == Decimal("255000")
    assert Decimal(data["tax"]) == Decimal("22950")
    assert Decimal(data["total"]) == Decimal("277950")
