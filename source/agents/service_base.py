"""Base para agentes: lê instrução de ``docs/instructions`` e cria o cliente LLM via factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from source.llms.llm_factory import create_llm_chat

_REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INSTRUCTIONS_DIR = _REPO_ROOT / "docs" / "instructions"


def instructions_path(filename: str) -> Path:
    """Caminho absoluto para um nome de arquivo apenas (ex.: ``attractions.txt``)."""
    return (DOCS_INSTRUCTIONS_DIR / Path(filename).name).resolve()


class ServiceBase(ABC):
    def __init__(self, *, model: str | None = None) -> None:
        instructions = self.load_instructions()
        self._chat = create_llm_chat(instructions, model=model)

    @property
    @abstractmethod
    def instruction_file_path(self) -> Path:
        """Arquivo UTF-8 com a instrução de sistema."""

    def load_instructions(self) -> str:
        return self._load_instruction()

    def _load_instruction(self) -> str:
        path = self.instruction_file_path
        if not path.is_file():
            raise FileNotFoundError(f"Instruction file not found: {path}")
        return path.read_text(encoding="utf-8").strip()


__all__ = ["DOCS_INSTRUCTIONS_DIR", "ServiceBase", "instructions_path"]
