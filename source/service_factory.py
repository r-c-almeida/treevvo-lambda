"""Instancia ``GenerateScriptService`` para Lambda e workers locais (sem HTTP)."""

from __future__ import annotations

import os
from pathlib import Path

from application import BASE_DIR
from source.cloud.aws import TripProfileS3Service
from source.services.generate_script_service import GenerateScriptService


def create_generate_script_service(
    *,
    transcripts_root: Path | None = None,
) -> GenerateScriptService:
    """
    Raiz onde existem subpastas com ``transcricao*.txt``.

    Ordem de precedência: argumento ``transcripts_root`` → ``TRANSCRIPTS_ROOT``
    (env) → ``application.BASE_DIR`` (raiz do projeto / pacote deployado).
    """
    env_root = (os.environ.get("TRANSCRIPTS_ROOT") or "").strip()
    if transcripts_root is not None:
        base = transcripts_root
    elif env_root:
        base = Path(env_root)
    else:
        base = BASE_DIR
    base = base.resolve()
    trip_s3 = TripProfileS3Service.from_env()
    return GenerateScriptService(transcripts_root=base, trip_profile_s3=trip_s3)
