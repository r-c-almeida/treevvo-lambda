"""
Configuração central de logging.

Variáveis de ambiente:
- LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (padrão: INFO)
- LOG_MAX_CHARS: tamanho máximo de texto de prompt/resposta nos logs (padrão: 15000)
"""

from __future__ import annotations

import logging
import os


def setup_logging() -> None:
    """Configura o root logger uma vez (ignora se já houver handlers)."""
    root = logging.getLogger()
    if root.handlers:
        return
    level_name = (os.environ.get("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def log_text_limit() -> int:
    raw = os.environ.get("LOG_MAX_CHARS", "15000")
    try:
        return max(0, int(raw))
    except ValueError:
        return 15000
