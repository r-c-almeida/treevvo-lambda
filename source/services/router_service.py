"""
Encadeamento do fluxo: instancia os agentes e chama ``run(...)`` um após o outro.

Sem registro por id nem dicionários de runners; o fluxo está explícito em ``TripPipeline.run``.
"""

from __future__ import annotations

import logging
from typing import Callable

from source.agents.attractions_service import AttractionsAgent
from source.agents.generate_trip_service import GenerateTripAgent
from source.agents.maps_service import MapsAgent
from source.agents.routization_service import RoutizationAgent
from source.agents.tips_service import TipsAgent
from source.agents.trip_types import PipelineResult, TripContext, TripInput
from source.logging_setup import setup_logging

logger = logging.getLogger(__name__)

# (nome do passo, texto produzido, contexto atual)
OnStepComplete = Callable[[str, str, TripContext], None]

# Nome histórico usado antes da refatoração
OnAgentComplete = OnStepComplete


class TripPipeline:
    """Único ponto de entrada: monta agentes uma vez e expõe ``run`` até o texto final."""

    def __init__(self) -> None:
        self.attractions = AttractionsAgent()
        self.tips = TipsAgent()
        self.routization = RoutizationAgent()
        self.maps = MapsAgent()
        self.generate_trip = GenerateTripAgent()

    def run(
        self,
        trip: TripInput,
        transcripts_block: str,
        *,
        on_step_complete: OnStepComplete | None = None,
        on_agent_complete: OnStepComplete | None = None,
    ) -> PipelineResult:
        """
        Executa cada passo em sequência. ``on_agent_complete`` é alias de ``on_step_complete``.
        """
        cb = on_step_complete or on_agent_complete

        setup_logging()
        transcripts = transcripts_block.strip() or "(nenhuma transcrição)"
        city = trip.city.strip()
        days = trip.days
        dates_note = (trip.dates_note or "").strip() or "(não informado)"
        complementary_info = (trip.complementary_info or "").strip() or "(não informado)"
        ctx = TripContext(trip=trip, transcripts_block=transcripts_block)
        outputs: dict[str, str] = {}

        logger.info(
            "TripPipeline.run city=%r days=%s dates_note=%r complementary_chars=%d transcript_chars=%d",
            city,
            days,
            dates_note,
            len(complementary_info),
            len(transcripts_block),
        )

        def after(step: str, text: str) -> None:
            outputs[step] = text
            ctx.agent_outputs[step] = text
            if cb:
                cb(step, text, ctx)

        try:
            attractions_text = self.attractions.run(
                city=city,
                days=days,
                dates_note=dates_note,
                complementary_info=complementary_info,
                transcripts=transcripts,
            )
            after("attractions", attractions_text)

            tips_text = self.tips.run(
                city=city,
                days=days,
                dates_note=dates_note,
                complementary_info=complementary_info,
                transcripts=transcripts,
            )
            after("tips", tips_text)

            routization_text = self.routization.run(
                city=city,
                days=days,
                dates_note=dates_note,
                complementary_info=complementary_info,
                transcripts=transcripts,
                hotel="",
                tips=tips_text,
                attractions=attractions_text,
            )
            after("routization", routization_text)

            maps_text = self.maps.run(
                city=city,
                days=days,
                complementary_info=complementary_info,
                route_plan=routization_text,
            )
            after("maps", maps_text)

            final_text = self.generate_trip.run(
                city=city,
                days=days,
                dates_note=dates_note,
                complementary_info=complementary_info,
                transcripts=transcripts,
                hotel="",
                tips=tips_text,
                attractions=attractions_text,
                maps=maps_text,
            )
            after("generate_trip", final_text)
        except Exception:
            logger.exception("TripPipeline.run interrompido")
            raise

        meta = {"steps": list(outputs.keys())}
        logger.info(
            "TripPipeline.run ok final_chars=%d steps=%s",
            len(final_text),
            meta["steps"],
        )
        return PipelineResult(
            agent_outputs=dict(outputs),
            final_text=final_text,
            meta=meta,
        )


RouterService = TripPipeline

__all__ = [
    "OnAgentComplete",
    "OnStepComplete",
    "RouterService",
    "TripPipeline",
]
