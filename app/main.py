"""FastAPI application entry point.

Wires the API router to the app. The session dependency is declared in
routes.py (get_db_session) and can be overridden in tests via
app.dependency_overrides.

Note: create_app() is called lazily (not at import time) so importing this
module (e.g. in tests) does NOT trigger a real PostgreSQL connection.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.catalog_routes import router as catalog_router
from app.api.routes import router


def create_app() -> FastAPI:
    """Application factory.

    Creates tables at startup ONLY for local/dev use. In production, Alembic
    migrations should handle schema (per constitution AC6). We wrap the
    metadata.create_all in a try/except so a missing DB doesn't crash the
    app startup — the API will return errors on requests that need the DB,
    which is the correct behavior (not a startup crash).
    """
    app = FastAPI(
        title="Pricing Engine",
        description="موتور قیمت‌گذاری پویا — معماری سه‌لایه",
        version="0.1.0",
    )
    app.include_router(router)
    # Feature 003 (catalog-management): CRUD on the products table.
    # main.py is a feature-001 file; see specs/001-pricing/status.md drift note.
    app.include_router(catalog_router)

    # Create tables at startup (MVP convenience). Wrapped so a missing DB
    # does not crash import or test collection.
    try:
        from app.config import get_settings
        from app.db.base import Base
        from app.db.session import create_app_engine

        settings = get_settings()
        engine = create_app_engine(settings.database_url)
        Base.metadata.create_all(engine)
    except Exception:  # noqa: BLE001 — startup resilience
        # DB unavailable (e.g. during tests without PostgreSQL). The
        # dependency-overridden session will provide the real engine.
        pass

    return app


# Lazy global app: only built when the module is run as a server (uvicorn),
# not when imported by tests. Tests build their own app via create_app()
# or use the TestClient with dependency overrides.
def _get_app() -> FastAPI:
    """Return the app instance, building it on first call."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


_app: FastAPI | None = None


# For `uvicorn app.main:app` to work, expose a module-level attribute that
# builds lazily. We use a module __getattr__ so import never triggers build.
def __getattr__(name: str) -> object:
    if name == "app":
        return _get_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
