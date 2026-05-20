"""Agente de atrações e pontos turísticos."""

from __future__ import annotations

from source.agents.base_agent import SimpleTranscriptAgent


class AttractionsAgent(SimpleTranscriptAgent):
    AGENT_ID = "attractions"

    USER_PROMPT_TEMPLATE = """\
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


AGENT_ID = AttractionsAgent.AGENT_ID
USER_PROMPT_TEMPLATE = AttractionsAgent.USER_PROMPT_TEMPLATE
run = AttractionsAgent.run
build_user_prompt = AttractionsAgent.build_user_prompt
