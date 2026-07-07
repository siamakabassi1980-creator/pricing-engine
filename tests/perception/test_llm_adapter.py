"""Tests for LLM adapter (T2.1)."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.perception.llm_adapter import (
    DeepSeekAdapter,
    DummyLLM,
    build_llm_adapter,
    parse_json_response,
)

# --- DummyLLM ---


def test_dummy_llm_returns_scripted_response_on_match() -> None:
    """DummyLLM returns the response whose key is a substring of prompt."""
    dummy = DummyLLM(
        responses={
            "parse request": '{"items": []}',
            "generate invoice": "متن فاکتور",
        }
    )
    assert dummy.complete("Please parse request now") == '{"items": []}'
    assert dummy.complete("generate invoice please") == "متن فاکتور"


def test_dummy_llm_returns_first_response_on_no_match() -> None:
    """If no key matches, DummyLLM returns the first scripted response."""
    dummy = DummyLLM(responses={"key1": "response1", "key2": "response2"})
    assert dummy.complete("totally unrelated prompt") == "response1"


def test_dummy_llm_empty_responses_returns_empty_string() -> None:
    """Empty DummyLLM returns empty string, not an error."""
    dummy = DummyLLM(responses={})
    assert dummy.complete("anything") == ""


# --- DeepSeekAdapter (construction only; no real API call) ---


def test_deepseek_adapter_stores_config() -> None:
    """DeepSeekAdapter can be constructed without making an API call."""
    adapter = DeepSeekAdapter(api_key="fake-key", model="deepseek-chat")
    assert adapter._api_key == "fake-key"
    assert adapter._model == "deepseek-chat"


# --- build_llm_adapter factory ---


def test_build_llm_adapter_returns_deepseek_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Factory returns DeepSeekAdapter when DEEPSEEK_API_KEY is set."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]  # pydantic private
    adapter = build_llm_adapter(settings)
    assert isinstance(adapter, DeepSeekAdapter)


def test_build_llm_adapter_falls_back_to_dummy_when_key_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Factory returns DummyLLM (with warning) when key is missing.

    This is the done-with-caveat pattern: app never crashes on missing config.
    """
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]  # pydantic private
    adapter = build_llm_adapter(settings)
    assert isinstance(adapter, DummyLLM)


# --- parse_json_response ---


def test_parse_json_response_plain() -> None:
    """Plain JSON object parses correctly."""
    result = parse_json_response('{"a": 1, "b": 2}')
    assert result == {"a": 1, "b": 2}


def test_parse_json_response_with_code_fence() -> None:
    """JSON wrapped in ```json fences parses correctly."""
    raw = '```json\n{"items": [{"id": "x", "qty": 5}]}\n```'
    result = parse_json_response(raw)
    assert result == {"items": [{"id": "x", "qty": 5}]}


def test_parse_json_response_with_prose_around() -> None:
    """JSON embedded in prose is extracted."""
    raw = 'Here is the result: {"total": 100} hope it helps'
    result = parse_json_response(raw)
    assert result == {"total": 100}


def test_parse_json_response_raises_on_no_json() -> None:
    """No JSON object -> ValueError."""
    with pytest.raises(ValueError, match="No JSON object found"):
        parse_json_response("just prose, no json here")
