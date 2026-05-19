"""Tipos compartilhados para entrada de viagem e resultados do pipeline de agentes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TripInput:
    """Dados vindos da tela (ou da CLI) para montar os prompts."""

    city: str
    days: int
    dates_note: str = ""
    complementary_info: str = ""


@dataclass
class TripContext:
    """Contexto mutável: transcrições + saída acumulada de cada agente."""

    trip: TripInput
    transcripts_block: str
    agent_outputs: dict[str, str] = field(default_factory=dict)

    def copy_for_parallel(self) -> TripContext:
        """Cópia superficial para leitura em threads (outputs ainda vazios no batch inicial)."""
        return TripContext(
            trip=self.trip,
            transcripts_block=self.transcripts_block,
            agent_outputs=dict(self.agent_outputs),
        )


@dataclass
class PipelineResult:
    """Retorno do router: texto por agente e resultado final escolhido pelo pipeline."""

    agent_outputs: dict[str, str]
    final_text: str
    meta: dict[str, Any] = field(default_factory=dict)
