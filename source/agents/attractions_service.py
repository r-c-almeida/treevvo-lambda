"""Agente de atrações e pontos turísticos."""

from __future__ import annotations

from pathlib import Path

from source.agents.service_base import ServiceBase, instructions_path


class AttractionsAgent(ServiceBase):
    @property
    def instruction_file_path(self) -> Path:
        return instructions_path("attractions.txt")

    def run(
        self,
        city: str,
        days: int,
        dates_note: str,
        complementary_info: str,
        transcripts: str,
    ) -> str:
        return self._chat.chat(
            self._build_prompt(
                city=city,
                days=days,
                dates_note=dates_note,
                complementary_info=complementary_info,
                transcripts=transcripts,
            )
        )

    def _build_prompt(
        self,
        city: str,
        days: int,
        dates_note: str,
        complementary_info: str,
        transcripts: str,
    ) -> str:
        return f"""\
Cidade: {city}
Período: {dates_note}
Perfil e preferências do viajante: {complementary_info}
"""
