"""Grava falhas de geração em ``error_trace/{data_hora}_generation.json``."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from application import BASE_DIR

logger = logging.getLogger(__name__)

ERROR_TRACE_DIRNAME = "error_trace"
# Limite para não explodir disco se o corpo SQS for gigante
_MAX_BODY_PREVIEW_CHARS = 50_000


def _utc_timestamp_for_filename(now: datetime) -> str:
    """``YYYYMMDD_HHMMSS_microseconds`` (UTC), único por mensagem na prática."""
    return now.strftime("%Y%m%d_%H%M%S") + f"_{now.microsecond:06d}"


def write_generation_error_trace(
    roteiro_solicitado: dict[str, Any],
    erro: str,
    *,
    root_dir: Path | None = None,
) -> Path:
    """
    Cria ``error_trace/<data_hora>_generation.json`` com o pedido e a mensagem de erro.

    ``roteiro_solicitado`` deve refletir o que foi possível extrair (payload completo,
    JSON parcial ou trecho do corpo da mensagem).

    Pasta pai do diretório ``error_trace``: ``root_dir`` se informado; senão
    ``ERROR_TRACE_ROOT`` no ambiente (na Lambda use ``/tmp`` — em ``/var/task`` não há escrita);
    se vazio, usa ``BASE_DIR`` do projeto.
    """
    if root_dir is not None:
        base_parent = root_dir.resolve()
    else:
        env_root = (os.environ.get("ERROR_TRACE_ROOT") or "").strip()
        base_parent = (
            Path(env_root).expanduser().resolve()
            if env_root
            else BASE_DIR.resolve()
        )
    out_dir = base_parent / ERROR_TRACE_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    path = out_dir / f"{_utc_timestamp_for_filename(now)}_generation.json"
    doc = {
        "gravado_em_utc": now.isoformat(),
        "roteiro_solicitado": roteiro_solicitado,
        "erro": erro,
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.warning("Erro de geração registrado em %s", path)
    return path


def body_preview_for_error_log(body: str) -> dict[str, Any]:
    """Snapshot seguro quando o JSON não pôde ser interpretado."""
    b = body or ""
    if len(b) > _MAX_BODY_PREVIEW_CHARS:
        b = b[:_MAX_BODY_PREVIEW_CHARS] + "\n…(truncado)"
    return {"corpo_mensagem_nao_json_ou_invalido": b}
