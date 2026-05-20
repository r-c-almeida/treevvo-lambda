"""Agente de busca / sugestão de hospedagem."""

from __future__ import annotations

from source.agents.base_agent import SimpleTranscriptAgent


class HotelAgent(SimpleTranscriptAgent):
    AGENT_ID = "hotels"

    USER_PROMPT_TEMPLATE = """\
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


AGENT_ID = HotelAgent.AGENT_ID
USER_PROMPT_TEMPLATE = HotelAgent.USER_PROMPT_TEMPLATE
run = HotelAgent.run
build_user_prompt = HotelAgent.build_user_prompt
