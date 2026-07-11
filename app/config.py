"""Application configuration loaded from environment variables.

All settings are read from .env via pydantic-settings. No secret is ever
hardcoded (per constitution: no-secret rule). Tax rate and discount rates
default to the values agreed in spec.md Clarify answers.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM provider.
    deepseek_api_key: str = ""

    # Database URLs.
    database_url: str = "postgresql+psycopg://pricing:pricing@localhost:5432/pricing_engine"
    test_database_url: str = "sqlite:///:memory:"

    # Category 1 hard rule — fixed tax rate (VAT, applied post-discount).
    tax_rate: Decimal = Decimal("0.09")

    # Category 2 tunable defaults.
    default_seasonal_discount_rate: Decimal = Decimal("0.10")
    vip_customer_discount_rate: Decimal = Decimal("0.15")

    # Category 2 — anomaly deterministic signal thresholds (feature 002).
    anomaly_qty_threshold: int = 100
    anomaly_base_threshold: Decimal = Decimal("10000000")

    @field_validator(
        "tax_rate",
        "default_seasonal_discount_rate",
        "vip_customer_discount_rate",
        mode="before",
    )
    @classmethod
    def to_decimal(cls, v: object) -> Decimal:
        """Coerce string env values into Decimal."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))


def get_settings() -> Settings:
    """Factory used as a FastAPI dependency and in tests."""
    return Settings()
