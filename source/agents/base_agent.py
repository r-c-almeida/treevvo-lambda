"""
Classe base para agentes de viagem: imports comuns, ``run`` padrão e contrato para o prompt.

- Agentes “simples”: herde ``SimpleTranscriptAgent`` e defina só ``AGENT_ID`` e
  ``USER_PROMPT_TEMPLATE`` (placeholders: city, days, dates_note, complementary_info, transcripts).
- Agentes com prompt composto: herde ``BaseTripAgent`` e implemente ``build_user_prompt``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from source.agents.trip_types import TripContext
from source.llms.chatgpt_chat import ChatGPTChat


class BaseTripAgent(ABC):
    """
    Identificador único do agente no pipeline e construção do prompt de usuário.

    ``run`` envia o prompt ao modelo; em geral não precisa ser sobrescrito.
    """

    AGENT_ID: ClassVar[str]

    @classmethod
    @abstractmethod
    def build_user_prompt(cls, ctx: TripContext) -> str:
        """Monta o texto do usuário enviado ao ChatGPT."""

    @classmethod
    def run(cls, chat: ChatGPTChat, ctx: TripContext) -> str:
        caller = f"{cls.__module__}.{cls.__qualname__}"
        return chat.send_prompt(cls.build_user_prompt(ctx), caller=caller)


class SimpleTranscriptAgent(BaseTripAgent):
    """
    Template único com cidade, duração, datas e transcrições.

    Sobrescreva apenas ``AGENT_ID`` e ``USER_PROMPT_TEMPLATE``.
    """

    USER_PROMPT_TEMPLATE: ClassVar[str]

    @classmethod
    def build_user_prompt(cls, ctx: TripContext) -> str:
        t = ctx.trip
        return cls.USER_PROMPT_TEMPLATE.format(
            city=t.city.strip(),
            days=t.days,
            dates_note=(t.dates_note or "").strip() or "(não informado)",
            complementary_info=(t.complementary_info or "").strip() or "(não informado)",
            transcripts=ctx.transcripts_block.strip() or "(nenhuma transcrição)",
        )
