"""
Processamento de mensagens SQS: mesmo payload JSON que ``GenerateTripQueueService.enqueue``.

Suporta invocação Lambda (evento SQS) e reuso pelo script local ``scripts/poll_sqs_local.py``.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from source.dtos.generate_script import GenerateScriptPayload
from source.generation_error_trace import body_preview_for_error_log, write_generation_error_trace
from source.service_factory import create_generate_script_service
from source.services.generate_script_service import GenerateScriptService

logger = logging.getLogger(__name__)


def process_message_body(body: str, *, service: GenerateScriptService | None = None) -> None:
    """Parseia o corpo da mensagem, valida e executa a geração do roteiro."""
    try:
        raw = json.loads(body)
    except json.JSONDecodeError as e:
        msg = f"JSON inválido no corpo da mensagem: {e}"
        write_generation_error_trace(body_preview_for_error_log(body), msg)
        raise ValueError(msg) from e
    if not isinstance(raw, dict):
        msg = "Corpo da mensagem deve ser um objeto JSON."
        write_generation_error_trace({"valor_recebido": raw}, msg)
        raise ValueError(msg)

    try:
        payload = GenerateScriptPayload.from_request_data(raw)
    except ValueError as e:
        write_generation_error_trace(dict(raw), str(e))
        raise

    roteiro_solicitado = payload.as_json_dict()
    svc = service if service is not None else create_generate_script_service()
    try:
        svc.generate(payload)
    except Exception as e:
        write_generation_error_trace(roteiro_solicitado, str(e))
        raise


def handle_sqs_lambda_event(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handler para Lambda com trigger SQS.

    Retorna ``batchItemFailures`` para mensagens que falharam, permitindo retry
    parcial sem reprocesar o lote inteiro (requer ``ReportBatchItemFailures`` no mapping).
    """
    _ = context
    records = event.get("Records") or []
    if not records:
        logger.warning("Evento SQS sem Records")
        return {"batchItemFailures": []}

    service = create_generate_script_service()
    failures: list[dict[str, str]] = []

    for record in records:
        mid = (record.get("messageId") or "").strip()
        body = record.get("body") or ""
        try:
            process_message_body(body, service=service)
            logger.info("Mensagem processada com sucesso messageId=%s", mid or "(sem id)")
        except Exception:
            logger.exception("Falha ao processar mensagem SQS messageId=%s", mid or "(sem id)")
            if mid:
                failures.append({"itemIdentifier": mid})

    return {"batchItemFailures": failures}
