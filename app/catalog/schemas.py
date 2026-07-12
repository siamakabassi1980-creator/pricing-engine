"""Pydantic schemas for the catalog CRUD API (feature 003).

Category 1 hard validation lives here at the input boundary so invalid
data is rejected with 422 *before* it reaches the DB. See plan.md for
the rationale behind the >2-decimal-place rejection (explicit Fail Fast
over silent rounding).
"""

from __future__ import annotations

import re
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

# Slug pattern for product ids: lowercase ascii letters/digits separated
# by single hyphens. No leading/trailing hyphen, no consecutive hyphens.
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"

# NOTE (PUT race condition): concurrent PUTs to the same product are
# out of scope for the MVP. We assume a single operator on a trusted
# internal network (ADR-0003), so last-write-wins at the DB row-lock
# level (SQLite/PostgreSQL) is acceptable and deterministic. If
# multi-operator support is needed later, optimistic locking (e.g. a
# version column) must be added in a separate feature — that is a
# schema change requiring its own ADR.


def _validate_slug(v: str) -> str:
    """Ensure id matches the lowercase slug pattern."""
    if not re.match(SLUG_PATTERN, v):
        raise ValueError("id must be a lowercase slug (letters/digits separated by single hyphens)")
    return v


def _validate_name(v: str) -> str:
    """Ensure name_fa is non-empty (after stripping whitespace)."""
    if not v.strip():
        raise ValueError("name_fa must be non-empty")
    return v


def _validate_price(v: Decimal) -> Decimal:
    """Ensure unit_price is non-negative and has <= 2 decimal places."""
    if v < 0:
        raise ValueError("unit_price must be >= 0")
    sign, digits, exponent = v.as_tuple()
    if isinstance(exponent, int) and exponent < 0 and abs(exponent) > 2:
        raise ValueError("unit_price must have <= 2 decimal places")
    return v


class _ProductFields(BaseModel):
    """Shared fields + validators for create and update payloads.

    The `id` validation differs between create (must be a valid slug)
    and update (must match the path id — validated in the route), so
    `id` is declared on each subclass rather than here.
    """

    model_config = ConfigDict(str_strip_whitespace=False)

    name_fa: str
    unit_price: Decimal

    _validate_name = field_validator("name_fa")(_validate_name)
    _validate_price = field_validator("unit_price")(_validate_price)


class ProductCreate(_ProductFields):
    """Body for POST /products (create)."""

    id: str

    _validate_id = field_validator("id")(_validate_slug)


class ProductUpdate(_ProductFields):
    """Body for PUT /products/{id} (full replacement).

    `id` is immutable — the route enforces that body.id == path id and
    rejects mismatches with 422. No per-field slug validation here to
    avoid masking that distinct check.
    """

    id: str


class ProductOut(BaseModel):
    """Response schema for all read/create/update operations."""

    id: str
    name_fa: str
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)
