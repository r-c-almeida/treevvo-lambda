"""
Factory de LLM: seleciona o provider ativo via variável de ambiente ``LLM_PROVIDER``.

Valores aceitos (case-insensitive):
  openai  — ChatGPT / OpenAI (padrão)
  claude  — Anthropic Claude

Chaves de API lidas automaticamente conforme o provider:
  openai → OPENAI_API_KEY
  claude → ANTHROPIC_API_KEY
"""

from __future__ import annotations

import logging
import os
from typing import Union

logger = logging.getLogger(__name__)

LLM_PROVIDER_ENV = "LLM_PROVIDER"
_PROVIDER_OPENAI = "openai"
_PROVIDER_CLAUDE = "claude"
_VALID_PROVIDERS = (_PROVIDER_OPENAI, _PROVIDER_CLAUDE)


def _active_provider() -> str:
    raw = (os.environ.get(LLM_PROVIDER_ENV) or _PROVIDER_OPENAI).strip().lower()
    if raw not in _VALID_PROVIDERS:
        raise ValueError(
            f"LLM_PROVIDER={raw!r} inválido. Valores aceitos: {_VALID_PROVIDERS}"
        )
    return raw


def create_llm_chat(
    instruction: str,
    *,
    model: str | None = None,
):
    """
    Instancia o cliente de LLM ativo.

    Retorna um objeto com o método ``chat(user_message, *, response_format="text") -> str``,
    compatível tanto com ``OpenAIChat`` quanto com ``ClaudeChat``.
    """
    provider = _active_provider()
    logger.info("LLM factory provider=%s model_override=%s", provider, model)

    if provider == _PROVIDER_CLAUDE:
        from source.llms.claude_chat import ClaudeChat, DEFAULT_MODEL as CLAUDE_DEFAULT

        api_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not api_key:
            raise OSError("ANTHROPIC_API_KEY is not set (necessário para LLM_PROVIDER=claude)")
        return ClaudeChat(
            instruction=instruction,
            api_key=api_key,
            model=model or CLAUDE_DEFAULT,
        )

    # padrão: openai
    from source.llms.open_ai_chat import OpenAIChat, DEFAULT_MODEL as OPENAI_DEFAULT

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise OSError("OPENAI_API_KEY is not set (necessário para LLM_PROVIDER=openai)")
    return OpenAIChat(
        instruction=instruction,
        api_key=api_key,
        model=model or OPENAI_DEFAULT,
    )


__all__ = ["LLM_PROVIDER_ENV", "create_llm_chat"]
