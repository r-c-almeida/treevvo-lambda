"""Status de um registro de viagem no perfil S3 (JSON)."""

from __future__ import annotations

from enum import Enum


class TripRecordStatus(str, Enum):
    """Ciclo: PENDING (criado pelo produtor) → CREATING (Lambda iniciou) → FINISHED ou ERROR."""

    PENDING = "PENDING"
    CREATING = "CREATING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"
