"""Cliente e operações SQS (interface AWS)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from source.dtos.generate_script import GenerateScriptPayload

logger = logging.getLogger(__name__)

DEFAULT_GENERATE_TRIP_QUEUE_URL = (
    "https://sqs.us-east-2.amazonaws.com/255615880605/generate-trip"
)

_QUEUE_URL_REGION = re.compile(
    r"^https://sqs\.([a-z0-9-]+)\.amazonaws\.com/", re.IGNORECASE
)


def _resolve_sqs_region(queue_url: str) -> str | None:
    """
    Região do cliente boto3: Lambda define ``AWS_REGION``; local costuma usar
    ``AWS_DEFAULT_REGION`` ou a região embutida na URL da fila.
    """
    for key in ("AWS_REGION", "AWS_DEFAULT_REGION"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    m = _QUEUE_URL_REGION.match((queue_url or "").strip())
    return m.group(1).lower() if m else None


def _make_sqs_client(queue_url: str) -> Any:
    region = _resolve_sqs_region(queue_url)
    if region:
        return boto3.client("sqs", region_name=region)
    return boto3.client("sqs")


class GenerateTripQueueService:
    """Publica o payload na fila; o consumidor processa de forma assíncrona."""

    def __init__(
        self,
        queue_url: str,
        *,
        sqs_client: Any | None = None,
    ) -> None:
        self._queue_url = queue_url.strip()
        if not self._queue_url:
            raise ValueError("URL da fila SQS não pode ser vazia.")
        self._sqs = sqs_client if sqs_client is not None else _make_sqs_client(self._queue_url)

    @property
    def queue_url(self) -> str:
        return self._queue_url

    @classmethod
    def from_env(cls, *, sqs_client: Any | None = None) -> GenerateTripQueueService:
        """Mesma URL que o produtor usa: ``SQS_GENERATE_TRIP_QUEUE_URL`` ou default do projeto."""
        url = (
            os.environ.get("SQS_GENERATE_TRIP_QUEUE_URL") or DEFAULT_GENERATE_TRIP_QUEUE_URL
        ).strip()
        return cls(url, sqs_client=sqs_client)

    def receive_messages(
        self,
        *,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: int | None = None,
    ) -> list[dict[str, Any]]:
        """Long poll SQS (útil para testar consumo local contra a fila real)."""
        kwargs: dict[str, Any] = {
            "QueueUrl": self._queue_url,
            "MaxNumberOfMessages": max(1, min(max_messages, 10)),
            "WaitTimeSeconds": max(0, min(wait_time_seconds, 20)),
            "AttributeNames": ["All"],
        }
        if visibility_timeout is not None:
            kwargs["VisibilityTimeout"] = int(visibility_timeout)
        resp = self._sqs.receive_message(**kwargs)
        return resp.get("Messages") or []

    def delete_message(self, receipt_handle: str) -> None:
        self._sqs.delete_message(QueueUrl=self._queue_url, ReceiptHandle=receipt_handle)

    def enqueue(self, payload: GenerateScriptPayload) -> str:
        body = json.dumps(payload.as_json_dict(), ensure_ascii=False)
        region = _resolve_sqs_region(self._queue_url)
        logger.info(
            "[SQS] Enviando mensagem | regiao=%s | user=%r | folder=%r | city=%r | corpo_chars=%d | fila=%s",
            region or "(default boto)",
            payload.user,
            payload.folder,
            payload.city,
            len(body),
            self._queue_url,
        )
        try:
            resp = self._sqs.send_message(QueueUrl=self._queue_url, MessageBody=body)
        except (ClientError, BotoCoreError):
            logger.exception("[SQS] Falha ao enviar mensagem para a fila")
            raise
        mid = resp.get("MessageId") or ""
        logger.info(
            "[SQS] Mensagem aceita pela fila | message_id=%s | md5_corpo=%s",
            mid,
            resp.get("MD5OfMessageBody", ""),
        )
        return mid
