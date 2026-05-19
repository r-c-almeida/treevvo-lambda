"""Status de um registro de viagem no perfil S3 (JSON)."""

from __future__ import annotations

from enum import Enum


class TripRecordStatus(str, Enum):
    OK = "OK"
    CREATING = "CREATING"
    ERROR = "ERROR"
