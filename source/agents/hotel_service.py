"""Agente de busca / sugestão de hospedagem.

Este módulo fica disponível porém **fora do pipeline** em ``trip_pipeline`` / ``RouterService``.
Quando incluir Hotéis, instanciar ``HotelAgent`` após Tips e antes da Roteirização e passar ``hotel`` nas chamadas.
"""

from __future__ import annotations

from pathlib import Path

from source.agents.service_base import ServiceBase, instructions_path


class HotelAgent(ServiceBase):
    @property
    def instruction_file_path(self) -> Path:
        return instructions_path("hotel.txt")

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
Quantidade de dias de viagem: {days}
Datas / período (se informado): {dates_note}
Informações complementares: {complementary_info}

Quero que você sugira hoteis otimizando as distâncias e considerando as melhores regiões da cidade. Evite regiões consideradas perigosas ou zonas de risco.
Traga informações sobre o preço do hotel
Traga informações sobre a avaliação do hotel (tripadvisor, booking, etc)

Se houver transcrição abaixo, sugira opções de hospedagem e critérios de busca.
Se houver informação complementar contendo nome de hotel e hospedagem, sugira apenas hoteis da mesma categoria e preço como comparativo para acomodação futura.
Responda em português.

--- Transcrições ---
{transcripts}
"""
