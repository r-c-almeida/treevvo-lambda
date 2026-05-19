#!/usr/bin/env python3
"""
Consome mensagens da fila SQS na AWS usando as mesmas credenciais do boto3 local
(perfil ~/.aws, variáveis de ambiente, etc.) e o mesmo pipeline da Lambda.

Uso (na raiz do repositório), com ``.env`` carregado pelo ``application``:

    python scripts/poll_sqs_local.py

Um lote e encerra:

    python scripts/poll_sqs_local.py --once

Encerre com Ctrl+C em modo contínuo.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from source.logging_setup import setup_logging

setup_logging()

from source.cloud.aws import GenerateTripQueueService
from source.service_factory import create_generate_script_service
from source.sqs_generate_worker import process_message_body

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Consome SQS localmente (fila AWS real).")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Recebe até um lote de mensagens, processa e sai (útil para um disparo de teste).",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=10,
        help="Máximo de mensagens por receive (1–10). Padrão: 10.",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=20,
        help="Long poll em segundos (0–20). Padrão: 20.",
    )
    parser.add_argument(
        "--visibility-timeout",
        type=int,
        default=None,
        help="Opcional: VisibilityTimeout em segundos para esta recepção.",
    )
    args = parser.parse_args()

    queue = GenerateTripQueueService.from_env()
    logger.info("Escutando fila %s (Ctrl+C para sair)", queue.queue_url)

    service = create_generate_script_service()

    while True:
        messages = queue.receive_messages(
            max_messages=args.max_messages,
            wait_time_seconds=args.wait,
            visibility_timeout=args.visibility_timeout,
        )
        if not messages:
            logger.debug("Nenhuma mensagem neste receive.")
            if args.once:
                break
            continue

        for msg in messages:
            body = msg.get("Body") or ""
            receipt = msg.get("ReceiptHandle") or ""
            mid = msg.get("MessageId") or ""
            try:
                process_message_body(body, service=service)
                queue.delete_message(receipt)
                logger.info("Processada e removida da fila messageId=%s", mid)
            except Exception:
                logger.exception(
                    "Falha ao processar messageId=%s — mensagem volta à fila após visibility timeout",
                    mid,
                )

        if args.once:
            break

        time.sleep(0.05)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
