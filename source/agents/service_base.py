"""Base para agentes que usam ``OpenAIChat`` + um arquivo ``docs/instructions/*.txt``."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

from source.llms.open_ai_chat import DEFAULT_MODEL, OpenAIChat

# service_base.py -> agents -> source -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INSTRUCTIONS_DIR = _REPO_ROOT / "docs" / "instructions"


def instructions_path(filename: str) -> Path:
    """Caminho absoluto para um nome de arquivo apenas (ex.: ``attractions.txt``)."""
    return (DOCS_INSTRUCTIONS_DIR / Path(filename).name).resolve()


class ServiceBase(ABC):
    def __init__(self, *, model: str = DEFAULT_MODEL) -> None:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise OSError("OPENAI_API_KEY is not set")

        instructions = self.load_instructions()
        self._chat = OpenAIChat(instruction=instructions, api_key=api_key, model=model)

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
