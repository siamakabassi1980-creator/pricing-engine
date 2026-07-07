"""Tests for config loading from environment."""

from __future__ import annotations

from decimal import Decimal

from app.config import Settings


def test_settings_load_defaults(monkeypatch: object) -> None:
    """Settings load with agreed defaults when env vars are absent.

    Uses monkeypatch to clear env vars so defaults apply.
    """
    # Clear the env vars that Settings reads, so defaults are used.
    for key in (
        "TAX_RATE",
        "DEFAULT_SEASONAL_DISCOUNT_RATE",
        "VIP_CUSTOMER_DISCOUNT_RATE",
    ):
        monkeypatch.delenv(key, raising=False)  # type: ignore[attr-defined]

    settings = Settings()
    assert settings.tax_rate == Decimal("0.09")
    assert settings.default_seasonal_discount_rate == Decimal("0.10")
    assert settings.vip_customer_discount_rate == Decimal("0.15")


def test_settings_coerce_decimal_from_string(monkeypatch: object) -> None:
    """String env values are coerced to Decimal (env vars are always str)."""
    monkeypatch.setenv("TAX_RATE", "0.20")  # type: ignore[attr-defined]
    settings = Settings()
    assert settings.tax_rate == Decimal("0.20")


def test_database_urls_have_non_empty_defaults() -> None:
    """Database URLs have sensible defaults so config never crashes."""
    settings = Settings()
    assert settings.database_url.startswith("postgresql")
    assert settings.test_database_url.startswith("sqlite")
