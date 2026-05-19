"""
Entrada AWS Lambda com trigger SQS.

Configure o handler como ``lambda_function.lambda_handler`` e habilite
``ReportBatchItemFailures`` no event source mapping da fila.

Variáveis úteis: ``TRANSCRIPTS_ROOT``, ``SQS_*``, ``S3_*``, ``OPENAI_API_KEY``
(ver ``.env.example``).
"""

from __future__ import annotations

from source.logging_setup import setup_logging

setup_logging()

from source.sqs_generate_worker import handle_sqs_lambda_event


def lambda_handler(event, context):
    return handle_sqs_lambda_event(event, context)
