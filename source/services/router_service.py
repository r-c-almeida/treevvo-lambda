"""
Encadeia os agentes: instancia um passo por vez e devolve ``PipelineResult``.

``RouterService`` é alias de ``TripPipeline`` (compatível com código que ainda usa o nome antigo).

O passo de **hotel** está comentado propositalmente; quando for reativar, inclua chamada antes da
roteirização no método ``TripPipeline.run`` e passe ``hotel=texto`` aos agentes seguintes.

Importação apenas para referência (não usar no pipeline atual):
  # from source.agents.hotel_service import HotelAgent
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from source.agents.attractions_service import AttractionsAgent
from source.agents.generate_trip_service import GenerateTripAgent
from source.agents.maps_service import MapsAgent
from source.agents.routization_service import RoutizationAgent
from source.agents.tips_service import TipsAgent

# from source.agents.hotel_service import HotelAgent  # desativado no pipeline atual

from source.agents.trip_types import PipelineResult, TripContext, TripInput
from source.logging_setup import setup_logging

logger = logging.getLogger(__name__)

OnStepComplete = Callable[[str, str, TripContext], None]

# Nome anterior usado em ``application.py``
OnAgentComplete = OnStepComplete


class TripPipeline:
    """Constrói os agentes uma vez e expõe ``run`` até produzir o texto final."""

    def __init__(self) -> None:
        self.attractions = AttractionsAgent()
        self.tips = TipsAgent()
        # self.hotels = HotelAgent()  # desativado: ver docstring deste módulo
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
        """``on_agent_complete`` é apenas outro nome para ``on_step_complete``."""
        cb = on_step_complete or on_agent_complete

        setup_logging()
        transcripts_safe = transcripts_block.strip() or "(nenhuma transcrição)"
        city = trip.city.strip()
        days = trip.days
        dates_note = (trip.dates_note or "").strip() or "(não informado)"
        complementary_info = (trip.complementary_info or "").strip() or "(não informado)"
        ctx = TripContext(trip=trip, transcripts_block=transcripts_block)
        outputs: dict[str, str] = {}

        logger.info(
            "TripPipeline.run city=%r days=%s complementary_chars=%d transcript_chars=%d",
            city,
            days,
            len(complementary_info),
            len(transcripts_block),
        )

        timings: dict[str, float] = {}
        pipeline_start = time.perf_counter()

        def notify(step: str, text: str, agent) -> None:
            outputs[step] = text
            ctx.agent_outputs[step] = text
            timings[step] = agent.last_duration_s
            if cb:
                cb(step, text, ctx)

        try:
            attractions_text = self.attractions.run(
                city=city, days=days, dates_note=dates_note,
                complementary_info=complementary_info, transcripts=transcripts_safe,
            )
            notify("attractions", attractions_text, self.attractions)

            tips_text = self.tips.run(
                city=city, days=days, dates_note=dates_note,
                complementary_info=complementary_info, transcripts=transcripts_safe,
            )
            notify("tips", tips_text, self.tips)

            # --- Hotel (DESATIVADO) ---
            # hotel_text = self.hotels.run(...)
            # notify("hotels", hotel_text, self.hotels)
            hotel_text = ""

            routization_text = self.routization.run(
                city=city, days=days, dates_note=dates_note,
                complementary_info=complementary_info, transcripts=transcripts_safe,
                hotel=hotel_text, tips=tips_text, attractions=attractions_text,
            )
            notify("routization", routization_text, self.routization)

            maps_text = self.maps.run(
                city=city, days=days,
                complementary_info=complementary_info, route_plan=routization_text,
            )
            notify("maps", maps_text, self.maps)

            final_text = self.generate_trip.run(
                city=city, days=days, dates_note=dates_note,
                complementary_info=complementary_info, transcripts=transcripts_safe,
                hotel=hotel_text, tips=tips_text, attractions=attractions_text,
                routization=routization_text, maps=maps_text,
            )
            notify("generate_trip", final_text, self.generate_trip)
        except Exception:
            logger.exception("TripPipeline.run interrompido")
            raise

        total_s = round(time.perf_counter() - pipeline_start, 3)
        timings["total"] = total_s
        logger.info("pipeline_total_s=%.3f timings=%s", total_s, timings)

        meta = {"steps": list(outputs.keys()), "timings_s": timings}
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
