"""
Fachada sobre ``ChatGPTChat``: ``instruction`` (string), ``api_key`` e método ``chat`` para o texto do usuário.
"""

from __future__ import annotations

from typing import Any, Literal

from source.llms.chatgpt_chat import DEFAULT_MODEL, ChatGPTChat


class OpenAIChatApiError(RuntimeError):
    """Falhas na comunicação/API ao enviar prompts."""


class OpenAIChat:
    def __init__(
        self,
        instruction: str,
        api_key: str,
        *,
        model: str | None = None,
    ) -> None:
        self._gpt = ChatGPTChat(
            api_key=api_key,
            model=model or DEFAULT_MODEL,
            system_instructions=(instruction or "").strip(),
            log_label="OpenAIChat",
        )

    def chat(
        self,
        user_message: str,
        *,
        response_format: Literal["text", "json"] = "text",
    ) -> str | Any:
        if response_format != "text":
            raise NotImplementedError(
                "Este projeto usa apenas response_format=\"text\" no pipeline atual."
            )
        text = (user_message or "").strip()
        if not text:
            raise ValueError("user_message cannot be empty.")
        try:
            return self._gpt.send_prompt(text, caller="OpenAIChat.chat")
        except Exception as e:
            raise OpenAIChatApiError(str(e)) from e


__all__ = ["DEFAULT_MODEL", "OpenAIChat", "OpenAIChatApiError"]
