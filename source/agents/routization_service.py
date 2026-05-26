"""Agente que monta roteiro dia a dia usando dicas, atrações e (opcional) hotéis."""

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
        hotel: str = "",
        tips: str,
        attractions: str,
    ) -> str:
        prompt = self._build_prompt(
            city=city,
            days=days,
            dates_note=dates_note,
            complementary_info=complementary_info,
            transcripts=transcripts,
            hotel=self._nz(hotel),
            tips=self._nz(tips),
            attractions=self._nz(attractions),
        )
        return self._chat.chat(prompt)

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
        return f"""\
Cidade: {city}
Dias de viagem: {days}
Datas / período: {dates_note}
Informações complementares: {complementary_info}

Use as seções abaixo (geradas por outros agentes) e as transcrições para montar um roteiro dia a dia coerente.
Responda em português.

Faça a divisão do roteiro por dias, considerando o horário de check-in e check-out do hotel, o horário de funcionamento dos pontos turísticos e o horário de deslocamento entre os pontos turísticos.
Faça a divisão do dia em manhã, tarde e noite, considerando o horário de funcionamento dos pontos turísticos e o horário de deslocamento entre os pontos turísticos.
Não sugira visitação de roteiro em horário ou dia que ele não estará aberto.
Otimize as distâncias entre os pontos turísticos, considerando a menor distância e o tempo de viagem entre eles.
Agrupe a maior quantidade possível de pontos turísticos em um unico período do dia desde que estejam próximos.
Agrupar pontos turísticos que estejam próximos, evitando longas viagens.
Não coloque visitações em horários considerado de risco ou perigosos.
Se a distância entre os pontos turisticos for longa, verifique se há histórico de transito.
Se houver lista de pontos turísticos, foque na roteirização entre eles.
Se houver informação de hotel, considere o ponto de partida inicial e final como o hotel.
Se houver mais de um hotel, considere o tempo de deslocamento entre eles durante a data de troca de hoteis.
Se for informado uma lista de pontos turísticos, você deve priorizar a roteirização entre eles garantindo que sejam visitados. Caso não seja possível visitar todos eles, priorize os que estão próximos um do outro.
Esta lista estará em informações complementares.

Responda em português.

--- Transcrições ---
{transcripts}

--- Sugestões de hospedagem (agente hotéis) ---
{hotel}

--- Dicas da cidade (agente dicas) ---
{tips}

--- Atrações (agente atrações) ---
{attractions}
"""
