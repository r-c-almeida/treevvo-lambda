"""DTOs para geração de roteiro: parse do corpo da requisição e resposta da API."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


def _format_br_date(d: date) -> str:
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _parse_roteiro_uuid(raw: str) -> str:
    """Valida UUID e normaliza para string canônica (RFC 4122)."""
    s = (raw or "").strip()
    if not s:
        raise ValueError("Informe o identificador do roteiro (campo id).")
    try:
        return str(uuid.UUID(s))
    except ValueError:
        raise ValueError(
            "O campo id deve ser um UUID válido (ex.: 550e8400-e29b-41d4-a716-446655440000)."
        ) from None

@dataclass(frozen=True)
class GenerateScriptPayload:
    """Entrada já validada a partir do corpo JSON da requisição.

    O campo ``id`` identifica o roteiro em ``profile.json`` e deve ser um **UUID** (RFC 4122).
    """

    user: str
    id: str
    folder: str
    city: str
    date_start: date
    date_end: date
    complementary_info: str

    @property
    def days(self) -> int:
        return (self.date_end - self.date_start).days + 1

    @property
    def dates_note(self) -> str:
        return f"{_format_br_date(self.date_start)} a {_format_br_date(self.date_end)}"

    @classmethod
    def from_request_data(cls, data: dict[str, Any]) -> GenerateScriptPayload:
        user = (data.get("user") or "").strip()
        if not user:
            raise ValueError("Informe o identificador do usuário (campo user).")
        rid = _parse_roteiro_uuid(data.get("id") or "")
        folder = (data.get("folder") or "").strip()
        city = (data.get("city") or "").strip()
        complementary_info = (data.get("complementary_info") or "").strip()

        date_start_s = (data.get("date_start") or "").strip()
        date_end_s = (data.get("date_end") or "").strip()
        if not date_start_s or not date_end_s:
            raise ValueError("Informe a data inicial e a data final do intervalo.")
        try:
            d0 = datetime.strptime(date_start_s, "%Y-%m-%d").date()
            d1 = datetime.strptime(date_end_s, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                "Datas inválidas. Use o seletor de intervalo (formato AAAA-MM-DD)."
            ) from None
        if d1 < d0:
            raise ValueError("A data final não pode ser anterior à data inicial.")

        return cls(
            user=user,
            id=rid,
            folder=folder,
            city=city,
            date_start=d0,
            date_end=d1,
            complementary_info=complementary_info,
        )

    def as_json_dict(self) -> dict[str, Any]:
        """Mesmo formato do corpo JSON da API (para fila / workers)."""
        return {
            "user": self.user,
            "id": self.id,
            "folder": self.folder,
            "city": self.city,
            "date_start": self.date_start.isoformat(),
            "date_end": self.date_end.isoformat(),
            "complementary_info": self.complementary_info,
        }


@dataclass(frozen=True)
class GenerateScriptResult:
    """Saída do caso de uso pronta para serializar em JSON."""

    response_text: str
    stages: dict[str, str]
    pipeline_meta: dict[str, Any]
    s3_persisted: dict[str, str] | None = None

    def as_api_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "ok": True,
            "message": "Roteiro gerado com sucesso.",
            "response": self.response_text,
            "stages": self.stages,
            "pipeline_meta": self.pipeline_meta,
        }
        if self.s3_persisted:
            out["s3"] = self.s3_persisted
        return out
