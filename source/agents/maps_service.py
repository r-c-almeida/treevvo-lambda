"""Agente de mapas: usa o roteiro consolidado para sugerir organização espacial / mapas."""

from __future__ import annotations

from typing import ClassVar

from source.agents.base_agent import BaseTripAgent
from source.agents.routization_service import RoutizationAgent
from source.agents.trip_types import TripContext


class MapsAgent(BaseTripAgent):
    AGENT_ID = "maps"

    USER_PROMPT_TEMPLATE: ClassVar[str] = """\
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

    @classmethod
    def build_user_prompt(cls, ctx: TripContext) -> str:
        t = ctx.trip
        route_plan = ctx.agent_outputs.get(RoutizationAgent.AGENT_ID, "").strip()
        return cls.USER_PROMPT_TEMPLATE.format(
            city=t.city.strip(),
            days=t.days,
            complementary_info=(t.complementary_info or "").strip() or "(não informado)",
            route_plan=route_plan or "(vazio — execute a roteirização antes)",
        )


AGENT_ID = MapsAgent.AGENT_ID
USER_PROMPT_TEMPLATE = MapsAgent.USER_PROMPT_TEMPLATE
run = MapsAgent.run
build_user_prompt = MapsAgent.build_user_prompt
