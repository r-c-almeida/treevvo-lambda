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
Dias de viagem: {days}
Datas / período: {dates_note}
Informações complementares: {complementary_info}

Quero que você liste as atrações e pontos turísticos relevantes e importantes para viajantes.
Informe se o ponto turístico é um museu, monumento, parque, etc.
Se for monumento, construção histórica, etc, traga informações sobre a história do local.
Informe se o ponto turístico é pago ou gratuito.
Informe o horário de funcionamento.
Se for um passeio, traga informações sobre o preço e se faz parte de algum plano de desconto (citypass, go city, etc).
Se for um local de risco, não sugira visita à noite.
Se for um restaurante (Ex Hard Rock Cafe, etc), traga informações sobre o cardápio e o preço.

Com base nas transcrições (se houver), liste atrações e pontos turísticos relevantes, com prioridades para o tempo disponível.
Responda em português.

--- Transcrições ---
{transcripts}
"""
