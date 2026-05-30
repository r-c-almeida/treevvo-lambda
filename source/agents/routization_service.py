"""Agente que monta roteiro dia a dia com dicas, atrações e (opcional) hotéis.

Parâmetro ``hotel``: hoje sempre vazio porque o passo ``HotelAgent`` está desativado no pipeline.
Quando ligar hotéis, passe o texto do agente aqui nas chamadas desde ``trip_pipeline``.
"""

from __future__ import annotations

from pathlib import Path

from source.agents.service_base import ServiceBase, instructions_path


class RoutizationAgent(ServiceBase):
    @property
    def instruction_file_path(self) -> Path:
        return instructions_path("routization.txt")

    def run(
        self,
        city: str,
        days: int,
        dates_note: str,
        complementary_info: str,
        transcripts: str,
        *,
        # hotel_desativado: ver comentários em ``trip_pipeline`` / ``hotel_service``.
        hotel: str = "",
        tips: str,
        attractions: str,
    ) -> str:
        return self._timed_chat(
            self._build_prompt(
                city=city,
                days=days,
                dates_note=dates_note,
                complementary_info=complementary_info,
                transcripts=transcripts,
                hotel=self._nz(hotel),
                tips=self._nz(tips),
                attractions=self._nz(attractions),
            )
        )

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
    ) -> str:
        # Mantém placeholder de hotel para quando o HotelAgent voltar ao pipeline.
        return f"""\
Cidade: {city}
Dias de viagem: {days}
Período: {dates_note}
Perfil e preferências do viajante: {complementary_info}

--- Hospedagem ---
{hotel}

--- Dicas da cidade ---
{tips}

--- Atrações ---
{attractions}
"""
