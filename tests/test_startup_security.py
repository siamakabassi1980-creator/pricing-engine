"""Security tests for create_app() startup validation (ADR-0001 addendum).

These test the REAL production path: create_app() with default settings
(no overrides, no injected DummyLLM). This is the exact code path that
runs when `uvicorn app.main:app` starts in production.
"""

from __future__ import annotations

import pytest

from app.main import create_app


def test_create_app_raises_when_no_key_and_fallback_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_app() must raise RuntimeError at startup when no API key
    is present and allow_dummy_fallback is False (the safe default).

    This is the production path. A misconfigured production deployment
    must fail to start, NOT silently serve DummyLLM output on the first
    request. The error must surface at create_app() time.
    """
    # Simulate production: no key in env, flag at default (False).
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("ALLOW_DUMMY_FALLBACK", raising=False)

    with pytest.raises(RuntimeError, match="refusing to start"):
        create_app()
