"""Tests for database session infrastructure."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.session import configure_session_factory, create_app_engine


def test_create_sqlite_in_memory_engine() -> None:
    """SQLite in-memory engine can be created and queried."""
    engine = create_app_engine("sqlite:///:memory:")
    assert isinstance(engine, Engine)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_session_factory_yields_working_session() -> None:
    """A session from the factory can execute a simple query."""
    engine = create_app_engine("sqlite:///:memory:")
    factory = configure_session_factory(engine)
    with factory() as session:
        result = session.execute(text("SELECT 42")).scalar()
        assert result == 42
