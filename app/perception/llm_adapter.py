"""LLM adapter — swappable interface to any LLM provider.

Per ADR-0001, Perception and Generation never call a provider directly.
They depend on the LLMAdapter Protocol, and a concrete adapter is injected.

Two implementations ship:
- DeepSeekAdapter: real API call via httpx.
- DummyLLM: scripted responses for deterministic tests.

To add a provider, add a new class implementing LLMAdapter. No changes
to Perception/Generation are needed.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMAdapter(Protocol):
    """Abstract interface for any LLM provider.

    A single method: take a prompt, return a completion string. The caller
    (Perception or Generation) is responsible for parsing the string into
    structured form if needed.
    """

    def complete(self, prompt: str) -> str:
        """Return the LLM completion for the given prompt."""
        ...


class DeepSeekAdapter:
    """LLM adapter calling the DeepSeek chat completion API."""

    def __init__(self, api_key: str, model: str = "deepseek-chat") -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = "https://api.deepseek.com/v1"

    def complete(self, prompt: str) -> str:
        """Call DeepSeek and return the assistant message content.

        Raises httpx.HTTPStatusError on non-2xx. Callers should catch and
        fall back to a safe default or propagate per their error policy.
        """
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,  # deterministic for parsing
                },
            )
            response.raise_for_status()
            data = response.json()
            content: str = data["choices"][0]["message"]["content"]
            return content


class DummyLLM:
    """Scripted LLM for deterministic tests.

    Holds a dict of prompt-substring -> response. If a prompt matches a
    known key (substring match), the scripted response is returned. If no
    match, returns the first scripted response or a default. This lets
    tests drive Perception/Generation through their prompts without needing
    the real DeepSeek API.
    """

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or {}

    def complete(self, prompt: str) -> str:
        for key, response in self._responses.items():
            if key in prompt:
                return response
        # Default: return the first scripted response, or empty string.
        if self._responses:
            first_key = next(iter(self._responses))
            return self._responses[first_key]
        return ""


def build_llm_adapter(settings: Settings) -> LLMAdapter:
    """Factory: return DeepSeekAdapter if API key present, else DummyLLM.

    This is the single point where the provider choice is made. If the key
    is missing, we log a warning and fall back to DummyLLM — so the app
    never crashes on missing config (done-with-caveat pattern).
    """
    if settings.deepseek_api_key:
        return DeepSeekAdapter(api_key=settings.deepseek_api_key)
    logger.warning("DEEPSEEK_API_KEY not set — falling back to DummyLLM")
    return DummyLLM()


def parse_json_response(raw: str) -> object:
    """Parse a JSON object from an LLM response.

    LLMs sometimes wrap JSON in ```json fences or prose. This extracts the
    first {...} block and parses it. Returns the parsed object.

    Raises ValueError if no valid JSON is found.
    """
    # Strip markdown code fences if present.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Remove first line (```json or ```) and last line (```).
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1])

    # Find the first {...} span (LLMs may add prose around it).
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM response")

    return json.loads(cleaned[start : end + 1])
