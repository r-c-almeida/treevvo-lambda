"""Agente de dicas gerais da cidade."""

from __future__ import annotations

from pathlib import Path

from source.agents.service_base import ServiceBase, instructions_path


class TipsAgent(ServiceBase):
    @property
    def instruction_file_path(self) -> Path:
        return instructions_path("tips.txt")

    def run(
        self,
        city: str,
        days: int,
        dates_note: str,
        complementary_info: str,
        transcripts: str,
    ) -> str:
        return self._timed_chat(
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
Dias de viagem: {days}
Período: {dates_note}
Perfil e preferências do viajante: {complementary_info}
"""
