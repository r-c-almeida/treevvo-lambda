"""Carrega arquivo ``.env`` apenas se ``python-dotenv`` estiver instalado.

Na AWS Lambda as variáveis vêm do console/Layers; normalmente não há ``python-dotenv``
no deployment — este módulo evita ``ImportError`` e segue só com ``os.environ``.
"""

from __future__ import annotations

from pathlib import Path


def try_load_dotenv(path: Path | str) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(Path(path))
