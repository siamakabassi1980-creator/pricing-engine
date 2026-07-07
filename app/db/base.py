"""SQLAlchemy declarative base.

All ORM models inherit from Base. Kept in its own module to avoid circular
imports between models.py and session.py.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
