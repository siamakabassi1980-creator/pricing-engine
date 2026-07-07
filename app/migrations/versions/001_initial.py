"""initial schema: products and customer_tiers

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-07

This migration creates the two MVP tables. The downgrade path drops them
in reverse order of creation (customer_tiers first, then products) so that
no foreign-key constraints are violated if any are added later.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create products and customer_tiers tables."""
    op.create_table(
        "products",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name_fa", sa.String(128), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
    )
    op.create_table(
        "customer_tiers",
        sa.Column("tier", sa.String(32), primary_key=True),
        sa.Column("discount_rate", sa.Numeric(3, 2), nullable=False),
    )


def downgrade() -> None:
    """Drop tables in reverse order of creation."""
    op.drop_table("customer_tiers")
    op.drop_table("products")
