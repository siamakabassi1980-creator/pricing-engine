"""Database session management.

Provides an engine factory and a session factory. In tests, an in-memory
SQLite engine is used; in production, PostgreSQL via DATABASE_URL.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Protocol

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


class EngineFactory(Protocol):
    """Protocol for engine providers (enables swapping in tests)."""

    def __call__(self) -> Engine: ...


def create_app_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine from a URL.

    SQLite needs connect_args={"check_same_thread": False} to work with
    FastAPI's thread pool; PostgreSQL does not.
    """
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, connect_args=connect_args)


def get_engine() -> Engine:
    """Return the application engine (PostgreSQL in prod)."""
    settings = get_settings()
    return create_app_engine(settings.database_url)


def get_test_engine() -> Engine:
    """Return an in-memory SQLite engine for tests."""
    settings = get_settings()
    return create_app_engine(settings.test_database_url)


def configure_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a session factory bound to a specific engine.

    Used both in production (bound to app engine) and in tests (bound to
    the in-memory SQLite engine).
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session_factory(engine: Engine) -> Generator[Session, None, None]:
    """FastAPI dependency that yields sessions bound to a specific engine."""
    factory = configure_session_factory(engine)
    with factory() as session:
        yield session
