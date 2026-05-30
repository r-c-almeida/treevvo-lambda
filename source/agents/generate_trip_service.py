"""Agente final: consolida roteiro preservando links e mapas.

``hotel``: vazio no pipeline atual (HotelAgent desativado). Ver ``trip_pipeline`` / ``hotel_service``.
"""

from __future__ import annotations

import re
from pathlib import Path

from source.agents.service_base import ServiceBase, instructions_path


def _extract_json(text: str) -> str:
    """Remove markdown code fences (```json ... ```) que o modelo pode incluir."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


class GenerateTripAgent(ServiceBase):
    @property
    def instruction_file_path(self) -> Path:
        return instructions_path("generate_trip.txt")

    def run(
        self,
        city: str,
        days: int,
        dates_note: str,
        complementary_info: str,
        transcripts: str,
        *,
        hotel: str = "",
        tips: str,
        attractions: str,
        routization: str,
        maps: str,
    ) -> str:
        raw = self._timed_chat(
            self._build_prompt(
                city=city,
                days=days,
                dates_note=dates_note,
                complementary_info=complementary_info,
                transcripts=transcripts,
                hotel=self._nz(hotel),
                tips=self._nz(tips),
                attractions=self._nz(attractions),
                routization=self._nz(routization),
                maps=self._nz(maps),
            )
        )
        return _extract_json(raw)

    @staticmethod
    def _nz(s: str) -> str:
        t = (s or "").strip()
        return t if t else "(vazio)"

    def _build_prompt(
        self,
        city: str,
        days: int,
        dates_note: str,
        complementary_info: str,
        transcripts: str,
        hotel: str,
        tips: str,
        attractions: str,
        routization: str,
        maps: str,
    ) -> str:
        return f"""\
Cidade: {city}
Dias de viagem: {days}
Datas / período: {dates_note}
Atrações: {attractions}
Perfil e preferências: {complementary_info}

--- Hospedagem ---
{hotel}

--- Dicas da cidade ---
{tips}

--- Roteiro dia a dia ---
{routization}

--- Mapas ---
{maps}
"""
