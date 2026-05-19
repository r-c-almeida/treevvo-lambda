"""Agente de roteirização: consolida saídas anteriores e monta o roteiro da viagem."""

from __future__ import annotations

from typing import ClassVar

from source.agents.attractions_service import AttractionsAgent
from source.agents.base_agent import BaseTripAgent
from source.agents.hotel_service import HotelAgent
from source.agents.tips_service import TipsAgent
from source.agents.maps_service import MapsAgent
from source.agents.trip_types import TripContext


class GenerateTripAgent(BaseTripAgent):
    AGENT_ID = "generate_trip"

    USER_PROMPT_TEMPLATE: ClassVar[str] = """\
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
Agrupar pontos turísticos que estejam próximos, evitando longas viagens.
Não coloque visitações em horários considerado de risco ou perigosos.
Se a distância entre os pontos turisticos for longa, verifique se há histórico de transito.
Se houver lista de pontos turísticos, foque na roteirização entre eles.
Não remova nenhum link do google maps. Mantenha EXATAMENTE a mesma estrutura de links.
Mantenha EXATAMENTE a mesma rota. Não troque a ordem ou dias da semana.
Seja rigoroso com estas regras.

Responda em português.

--- Transcrições ---
{transcripts}

--- Sugestões de hospedagem (agente hotéis) ---
{hotel}

--- Dicas da cidade (agente dicas) ---
{tips}

--- Atrações (agente atrações) ---
{attractions}

--- Mapas (agente maps) ---
{maps}
"""

    @classmethod
    def build_user_prompt(cls, ctx: TripContext) -> str:
        t = ctx.trip
        return cls.USER_PROMPT_TEMPLATE.format(
            city=t.city.strip(),
            days=t.days,
            dates_note=(t.dates_note or "").strip() or "(não informado)",
            complementary_info=(t.complementary_info or "").strip() or "(não informado)",
            transcripts=ctx.transcripts_block.strip() or "(nenhuma transcrição)",
            hotel=ctx.agent_outputs.get(HotelAgent.AGENT_ID, "").strip() or "(vazio)",
            tips=ctx.agent_outputs.get(TipsAgent.AGENT_ID, "").strip() or "(vazio)",
            attractions=ctx.agent_outputs.get(AttractionsAgent.AGENT_ID, "").strip() or "(vazio)",
            maps=ctx.agent_outputs.get(MapsAgent.AGENT_ID, "").strip() or "(vazio)"
        )


AGENT_ID = GenerateTripAgent.AGENT_ID
USER_PROMPT_TEMPLATE = GenerateTripAgent.USER_PROMPT_TEMPLATE
run = GenerateTripAgent.run
build_user_prompt = GenerateTripAgent.build_user_prompt
