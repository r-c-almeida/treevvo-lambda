"""
Orquestração central do fluxo de agentes.

A ordem de execução fica em ``RouterService.execute_sequence``: chamadas explícitas,
uma por vez, com retornos em variáveis distintas para inspeção e debug.
O miolo pode ser repensado depois; ``run`` apenas prepara o contexto e monta o resultado.
"""

from __future__ import annotations

import logging
from typing import Callable, ClassVar

from source.agents import (
    attractions_service,
    hotel_service,
    maps_service,
    routization_service,
    generate_trip_service,
    tips_service,
)
from source.agents.trip_types import PipelineResult, TripContext, TripInput
from source.llms.chatgpt_chat import ChatGPTChat
from source.logging_setup import setup_logging

# Chamado após cada agente com o texto produzido.
OnAgentComplete = Callable[[str, str, TripContext], None]

logger = logging.getLogger(__name__)


AGENT_RUNNERS: dict[str, Callable[[ChatGPTChat, TripContext], str]] = {
    #hotel_service.AGENT_ID: hotel_service.run,
    tips_service.AGENT_ID: tips_service.run,
    attractions_service.AGENT_ID: attractions_service.run,
    routization_service.AGENT_ID: routization_service.run,
    maps_service.AGENT_ID: maps_service.run,
    generate_trip_service.AGENT_ID: generate_trip_service.run,
}


class RouterService:
    """
    Define o fluxo em ``execute_sequence`` (variáveis explícitas por etapa).
    """

    #: Ordem lógica usada só em meta/logs; edite ``execute_sequence`` para mudar o fluxo real.
    DEFAULT_SEQUENCE_ORDER: ClassVar[list[str]] = [
        #hotel_service.AGENT_ID,
        tips_service.AGENT_ID,
        attractions_service.AGENT_ID,
        routization_service.AGENT_ID,
        maps_service.AGENT_ID,
        generate_trip_service.AGENT_ID,
    ]

    def _invoke_agent(
        self,
        ctx: TripContext,
        agent_id: str,
        instruction_file: str,
        on_agent_complete: OnAgentComplete | None,
    ) -> str:
        """Executa um agente, grava em ``ctx.agent_outputs`` e dispara callback opcional."""
        if agent_id not in AGENT_RUNNERS:
            raise ValueError(f"Agente desconhecido: {agent_id!r}")
        logger.info(
            "Router agente: agent_id=%s instruction_file=%s",
            agent_id,
            instruction_file,
        )
        chat = ChatGPTChat.from_instruction_file(instruction_file)
        try:
            text = AGENT_RUNNERS[agent_id](chat, ctx)
        except Exception:
            logger.exception(
                "Router falha no agente agent_id=%s instruction_file=%s",
                agent_id,
                instruction_file,
            )
            raise
        ctx.agent_outputs[agent_id] = text
        if on_agent_complete:
            on_agent_complete(agent_id, text, ctx)
        return text

    def execute_sequence(
        self,
        ctx: TripContext,
        *,
        on_agent_complete: OnAgentComplete | None = None,
    ) -> str:
        """
        **Edite aqui a ordem e o uso dos retornos.** Cada etapa fica em uma variável própria.

        O valor de retorno deste método vira ``PipelineResult.final_text`` (normalmente o último passo).
        """
        response_attractions = self._invoke_agent(
            ctx, attractions_service.AGENT_ID, "attractions.txt", on_agent_complete
        )
       # response_hotels = self._invoke_agent(
       #     ctx, hotel_service.AGENT_ID, "hotel.txt", on_agent_complete
        #)
        response_tips = self._invoke_agent(
            ctx, tips_service.AGENT_ID, "tips.txt", on_agent_complete
        )
        response_routization = self._invoke_agent(
            ctx, routization_service.AGENT_ID, "routization.txt", on_agent_complete
        )
        response_maps = self._invoke_agent(
            ctx, maps_service.AGENT_ID, "maps.txt", on_agent_complete
        )
        response_generate_trip = self._invoke_agent(
            ctx, generate_trip_service.AGENT_ID, "generate_trip.txt", on_agent_complete
        )

        logger.debug(
            "execute_sequence tamanhos (chars) hotels=%d tips=%d attractions=%d routization=%d maps=%d",
            #len(response_hotels),
            len(response_tips),
            len(response_attractions),
            len(response_routization),
            len(response_maps),
        )


        return response_generate_trip

    def run(
        self,
        trip: TripInput,
        transcripts_block: str,
        *,
        on_agent_complete: OnAgentComplete | None = None,
    ) -> PipelineResult:
        setup_logging()
        logger.info(
            "RouterService.run início city=%r days=%s dates_note=%r complementary_info_len=%d transcript_chars=%d",
            trip.city,
            trip.days,
            trip.dates_note,
            len(trip.complementary_info or ""),
            len(transcripts_block),
        )
        ctx = TripContext(trip=trip, transcripts_block=transcripts_block)

        try:
            final_text = self.execute_sequence(ctx, on_agent_complete=on_agent_complete)
        except Exception:
            logger.exception("RouterService.run interrompido em execute_sequence")
            raise

        meta = {
            "sequence_order_hint": list(type(self).DEFAULT_SEQUENCE_ORDER),
            "agent_outputs_keys": list(ctx.agent_outputs.keys()),
        }
        logger.info(
            "RouterService.run sucesso final_chars=%d agents=%s",
            len(final_text or ""),
            list(ctx.agent_outputs.keys()),
        )
        return PipelineResult(
            agent_outputs=dict(ctx.agent_outputs),
            final_text=final_text,
            meta=meta,
        )
