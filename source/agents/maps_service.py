"""Agente de mapas a partir do roteiro já montado."""

from __future__ import annotations

from pathlib import Path

from source.agents.service_base import ServiceBase, instructions_path


class MapsAgent(ServiceBase):
    @property
    def instruction_file_path(self) -> Path:
        return instructions_path("maps.txt")

    def run(
        self,
        city: str,
        days: int,
        complementary_info: str,
        route_plan: str,
    ) -> str:
        prompt = self._build_prompt(
            city=city,
            days=days,
            complementary_info=complementary_info,
            route_plan=(route_plan or "").strip()
            or "(vazio — execute a roteirização antes)",
        )
        return self._chat.chat(prompt)

    def _build_prompt(
        self,
        city: str,
        days: int,
        complementary_info: str,
        route_plan: str,
    ) -> str:
        return f"""\
Cidade: {city}
Dias de viagem: {days}
Informações complementares: {complementary_info}

Com base no roteiro já montado abaixo, sugira como organizar visitas no mapa (regiões por dia, deslocamentos, ordem lógica).
Otimize ao máximo a distância percorrida e o tempo de viagem entre os pontos turísticos.
Agrupar pontos turísticos que estejam próximos, evitando longas viagens.
Não coloque visitações em horários considerado de risco ou perigosos.
Se a distância entre os pontos turisticos for longa, verifique se há histórico de transito.
Se houver lista de pontos turísticos, foque na roteirização entre eles.
Se não houver roteiro, indique que faltou a etapa anterior.
SEMPRE retorne a rota do google maps com o link indicando o ponto de partida e o ponto de destino.
Se a distância for longa, indique meios de transporte alternativos como ônibus, táxi, trem, metrô, etc.
Se a distância for curta, indique a melhor forma de deslocar-se a pé.
Você deve criar a rota entre todos os pontos turísticos do roteiro, traçando a rota do ponto de partida até o ponto de destino.
Faça isso para cada ponto de interesse.
Ex.:
  - **Excalibur**
  - **Luxor**
  - **MGM Grand**
  - **New York-New-York**
  - **The Park / T-Mobile Arena**
Crie o link do mapa entre Hotel -> Excalibur
Crie o link do mapa entre Excalibur -> Luxor
Crie o link do mapa entre Luxor -> MGM Grand
Crie o link do mapa entre MGM Grand -> New York-New-York
Crie o link do mapa entre New York-New-York -> The Park / T-Mobile Arena
Responda em português.

--- Roteiro (etapa anterior) ---
{route_plan}
"""
