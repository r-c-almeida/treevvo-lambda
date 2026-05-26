from __future__ import annotations

import json
import re
from typing import Any, Literal

from openai import APIError, APITimeoutError, OpenAI, RateLimitError


class OpenAIChatError(Exception):
    """Base error for OpenAIChat failures."""

class OpenAIChatApiError(OpenAIChatError):
    """API communication failure."""

class OpenAIChatParseError(OpenAIChatError):
    """Response could not be parsed as JSON."""


_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL | re.IGNORECASE)

def _strip_json_fence(raw: str) -> str:
    m = _JSON_FENCE.match((raw or "").strip())
    return m.group(1).strip() if m else (raw or "").strip()


DEFAULT_MODEL = "gpt-5.4-mini"

class OpenAIChat:
    def __init__(self, instruction: str, api_key: str, *, model: str = DEFAULT_MODEL) -> None:
        if not api_key:
            raise ValueError("api_key cannot be empty.")
        self._instruction = instruction.strip()
        self._client = OpenAI(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    def chat(
        self,
        user_message: str,
        *,
        response_format: Literal["text", "json"] = "text",
    ) -> str | Any:
        if not user_message.strip():
            raise ValueError("user_message cannot be empty.")

        messages = []
        if self._instruction:
            messages.append({"role": "system", "content": self._instruction})
        messages.append({"role": "user", "content": user_message.strip()})

        kwargs: dict[str, Any] = {"model": self._model, "messages": messages}
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self._client.chat.completions.create(**kwargs)
        except (APIError, APITimeoutError, RateLimitError) as e:
            raise OpenAIChatApiError(f"OpenAI API error: {e}") from e

        content = response.choices[0].message.content or ""

        if response_format == "text":
            return content

        try:
            return json.loads(_strip_json_fence(content) or "{}")
        except json.JSONDecodeError as e:
            raise OpenAIChatParseError(
                f"Model response is not valid JSON. Preview: {content[:200]!r}"
            ) from e