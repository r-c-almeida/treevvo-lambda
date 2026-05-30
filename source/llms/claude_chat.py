"""
Cliente para a API de mensagens da Anthropic (Claude).

Mesma interface de fachada de ``OpenAIChat``: construtor recebe ``instruction``,
``api_key`` e ``model``; método ``chat`` recebe a mensagem do usuário e devolve texto.
"""

from __future__ import annotations

import logging
from typing import Literal

from source.logging_setup import log_text_limit, setup_logging

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"


def _truncate_for_log(text: str) -> str:
    lim = log_text_limit()
    if lim <= 0 or len(text) <= lim:
        return text
    return text[:lim] + f"\n...[truncado no log, total_chars={len(text)}]"


class ClaudeChatApiError(RuntimeError):
    """Falhas na comunicação/API ao enviar prompts para o Claude."""


class ClaudeChat:
    """Envia prompts ao Claude via API Anthropic; configuração isolada por instância."""

    def __init__(
        self,
        instruction: str,
        api_key: str,
        *,
        model: str | None = None,
    ) -> None:
        setup_logging()
        self._model = (model or DEFAULT_MODEL).strip()
        self._system = (instruction or "").strip()

        from anthropic import Anthropic

        self._client = Anthropic(api_key=api_key)

        logger.info(
            "ClaudeChat criado model=%s system_instruction_chars=%d",
            self._model,
            len(self._system),
        )

    def chat(
        self,
        user_message: str,
        *,
        response_format: Literal["text", "json"] = "text",
    ) -> str:
        if response_format != "text":
            raise NotImplementedError(
                'Este projeto usa apenas response_format="text" no pipeline atual.'
            )
        text = (user_message or "").strip()
        if not text:
            raise ValueError("user_message cannot be empty.")

        logger.info(
            "Claude envio model=%s user_prompt_chars=%d prompt=%s",
            self._model,
            len(text),
            _truncate_for_log(text),
        )

        kwargs: dict = {
            "model": self._model,
            "max_tokens": 16_000,
            "messages": [{"role": "user", "content": text}],
        }
        if self._system:
            kwargs["system"] = self._system

        try:
            response = self._client.messages.create(**kwargs)
        except Exception as e:
            logger.exception("Claude erro na API model=%s", self._model)
            raise ClaudeChatApiError(str(e)) from e

        if response.stop_reason == "max_tokens":
            logger.error(
                "Claude resposta truncada model=%s — aumente max_tokens ou reduza o prompt",
                self._model,
            )
            raise ClaudeChatApiError(
                "Resposta do modelo truncada (stop_reason=max_tokens). "
                "Reduza o número de dias ou aumente max_tokens."
            )
        out = response.content[0].text if response.content else ""
        logger.info(
            "Claude retorno model=%s response_chars=%d response=%s",
            self._model,
            len(out),
            _truncate_for_log(out),
        )
        return out


__all__ = ["DEFAULT_MODEL", "ClaudeChat", "ClaudeChatApiError"]
