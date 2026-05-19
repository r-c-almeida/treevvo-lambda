"""Agente de dicas gerais da cidade."""

from __future__ import annotations

from source.agents.base_agent import SimpleTranscriptAgent


class TipsAgent(SimpleTranscriptAgent):
    AGENT_ID = "tips"

    USER_PROMPT_TEMPLATE = """\
Cidade: {city}
Dias de viagem: {days}
Datas / período: {dates_note}
Informações complementares: {complementary_info}

Com base nas transcrições, extraia e organize dicas práticas (segurança, transporte, costumes, etc.).
Responda em português.

--- Transcrições ---
{transcripts}
"""


AGENT_ID = TipsAgent.AGENT_ID
USER_PROMPT_TEMPLATE = TipsAgent.USER_PROMPT_TEMPLATE
run = TipsAgent.run
build_user_prompt = TipsAgent.build_user_prompt
