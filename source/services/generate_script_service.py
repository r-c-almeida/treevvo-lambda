"""
Caso de uso: gerar roteiro a partir de uma pasta de transcrições (Lambda SQS / CLI).

Encapsula regras de entrada (cidade default), chamada a ``Application`` e uso do texto gerado em memória.
Se a subpasta de transcrições não existir, segue mesmo assim (só aviso no log).
Opcionalmente persiste perfil + JSON da viagem no S3 (``TripProfileS3Service``); não grava arquivos locais.
"""

from __future__ import annotations

import logging
from pathlib import Path

from application import Application, safe_folder_name
from source.dtos.generate_script import GenerateScriptPayload, GenerateScriptResult
from source.cloud.aws import TripProfileS3Service

logger = logging.getLogger(__name__)


class GenerateScriptService:
    """Orquestra geração de roteiro em relação à raiz onde ficam subpastas com ``transcricao*.txt``."""

    def __init__(
        self,
        transcripts_root: Path,
        *,
        trip_profile_s3: TripProfileS3Service | None = None,
    ) -> None:
        self._transcripts_root = transcripts_root.resolve()
        self._trip_profile_s3 = trip_profile_s3

    def generate(self, payload: GenerateScriptPayload) -> GenerateScriptResult:
        name = safe_folder_name(payload.folder)
        target = self._transcripts_root / name

        logger.info(
            "GenerateScriptService folder=%r name=%s target=%s user=%r",
            payload.folder,
            name,
            target,
            payload.user,
        )

        if not target.is_dir():
            logger.warning(
                'Pasta de transcrições ausente ou não é diretório: "%s" em %s. '
                "Prosseguindo sem arquivos transcricao*.txt (recomendado criar a pasta e os .txt).",
                name,
                self._transcripts_root,
            )

        city = payload.city or name.replace("_", " ").strip()

        logger.info(
            "GenerateScriptService parâmetros id=%r city=%r days=%s dates_note=%r complementary_info_len=%d",
            payload.id,
            city,
            payload.days,
            payload.dates_note,
            len(payload.complementary_info),
        )

        if self._trip_profile_s3 is not None:
            self._trip_profile_s3.mark_trip_creation_started(payload)

        app_job = Application(base_dir=target)
        s3_keys: dict[str, str] | None = None
        try:
            pipeline_result = app_job.run(
                city=city,
                days=payload.days,
                dates_note=payload.dates_note,
                complementary_info=payload.complementary_info,
            )
            text = pipeline_result.final_text

            logger.info(
                "GenerateScriptService sucesso response_chars=%d stages=%s",
                len(text),
                list(pipeline_result.agent_outputs.keys()),
            )

            if self._trip_profile_s3 is not None:
                logger.info(
                    "[Worker] Gravando resultado no S3 após pipeline OK | user=%r",
                    payload.user,
                )
                try:
                    s3_keys = self._trip_profile_s3.persist_after_generation(
                        payload,
                        destination=city,
                        success=True,
                        trip_text=text,
                    )
                    logger.info("[Worker] S3 concluído com sucesso | s3=%s", s3_keys)
                except Exception:
                    logger.exception(
                        "[Worker] Falha ao gravar no S3 (user=%r); resultado só em memória.",
                        payload.user,
                    )
            else:
                logger.info(
                    "[Worker] S3 desligado (S3_TRIP_PROFILE_BUCKET vazio); roteiro só em memória."
                )

            return GenerateScriptResult(
                response_text=text,
                stages=pipeline_result.agent_outputs,
                pipeline_meta=pipeline_result.meta,
                s3_persisted=s3_keys,
            )
        except Exception as e:
            if self._trip_profile_s3 is not None:
                logger.info(
                    "[Worker] Registrando falha no S3 | user=%r | erro=%s",
                    payload.user,
                    str(e)[:200],
                )
                try:
                    self._trip_profile_s3.persist_after_generation(
                        payload,
                        destination=city,
                        success=False,
                        trip_text="",
                        error_message=str(e)[:4000],
                    )
                    logger.info("[Worker] Entrada ERROR gravada no profile S3 | user=%r", payload.user)
                except Exception:
                    logger.exception(
                        "[Worker] Falha ao gravar estado ERROR no S3 (user=%r)",
                        payload.user,
                    )
            raise
