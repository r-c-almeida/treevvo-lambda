"""Cliente e operações S3 (interface AWS) — perfil e roteiros por usuário."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date, datetime, time, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

from application import safe_folder_name
from source.domain.trip_record_status import TripRecordStatus
from source.dtos.generate_script import GenerateScriptPayload

logger = logging.getLogger(__name__)


def _resolve_s3_region() -> str | None:
    for key in ("AWS_REGION", "AWS_DEFAULT_REGION"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return None


def _utc_day_start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _utc_day_end(d: date) -> datetime:
    return datetime.combine(d, time.max.replace(microsecond=999999), tzinfo=timezone.utc)


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _make_s3_client() -> Any:
    kwargs: dict[str, Any] = {}
    region = _resolve_s3_region()
    if region:
        kwargs["region_name"] = region
    endpoint = (os.environ.get("AWS_ENDPOINT_URL") or "").strip()
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    return boto3.client("s3", **kwargs)


class TripProfileS3Service:
    """Grava ``profile.json`` e arquivos em ``trips/`` por usuário."""

    def __init__(self, bucket: str, *, s3_client: Any | None = None) -> None:
        self._bucket = bucket.strip()
        if not self._bucket:
            raise ValueError("Bucket S3 não pode ser vazio.")
        self._s3 = s3_client if s3_client is not None else _make_s3_client()

    @classmethod
    def from_env(cls) -> TripProfileS3Service | None:
        bucket = (os.environ.get("S3_TRIP_PROFILE_BUCKET") or "").strip()
        if not bucket:
            logger.info(
                "[S3] Persistência desligada: defina S3_TRIP_PROFILE_BUCKET no ambiente para gravar perfil e viagens."
            )
            return None
        logger.info("[S3] Cliente ativo para bucket=%s", bucket)
        return cls(bucket)

    def _user_prefix(self, payload: GenerateScriptPayload) -> str:
        """Prefixo seguro das chaves S3 (derivado de ``user``)."""
        return safe_folder_name(payload.user)

    def _ensure_user_prefix(self, user_prefix: str) -> None:
        prefix = f"{user_prefix}/"
        resp = self._s3.list_objects_v2(Bucket=self._bucket, Prefix=prefix, MaxKeys=1)
        if resp.get("KeyCount", 0):
            logger.info(
                "[S3] Prefixo do usuário já existia | bucket=%s prefix=%s keys_encontradas=%s",
                self._bucket,
                prefix,
                resp.get("KeyCount", 0),
            )
            return
        self._s3.put_object(Bucket=self._bucket, Key=prefix, Body=b"")
        logger.info(
            "[S3] Criado prefixo (pasta) do usuário | bucket=%s key=%s",
            self._bucket,
            prefix,
        )

    def _load_profile(self, profile_key: str) -> dict[str, Any]:
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=profile_key)
            raw = obj["Body"].read().decode("utf-8")
            data = json.loads(raw)
        except ClientError as e:
            code = (e.response.get("Error") or {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                logger.info(
                    "[S3] profile.json ainda não existe (novo usuário) | key=%s",
                    profile_key,
                )
                return {}
            raise
        except json.JSONDecodeError:
            logger.warning("S3 profile.json inválido em %s; recriando estrutura.", profile_key)
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def _save_profile(self, profile_key: str, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2)
        raw = body.encode("utf-8")
        self._s3.put_object(
            Bucket=self._bucket,
            Key=profile_key,
            Body=raw,
            ContentType="application/json; charset=utf-8",
        )
        logger.info(
            "[S3] profile.json gravado | bucket=%s key=%s bytes=%d viagens_no_array=%d",
            self._bucket,
            profile_key,
            len(raw),
            len(data.get("trips") or []),
        )

    def persist_after_generation(
        self,
        payload: GenerateScriptPayload,
        *,
        destination: str,
        success: bool,
        trip_text: str,
        error_message: str | None = None,
    ) -> dict[str, str] | None:
        """
        Ao final do processamento: atualiza ``profile.json`` e, se sucesso, grava TXT em ``trips/``.

        Retorna chaves S3 gravadas (profile + trip) ou ``None`` se nada foi feito.
        """
        user_prefix = self._user_prefix(payload)
        profile_key = f"{user_prefix}/profile.json"
        region = _resolve_s3_region()
        logger.info(
            "[S3] Iniciando persistência | bucket=%s | regiao=%s | user_id=%r | prefixo_s3=%s | destino=%r | sucesso=%s",
            self._bucket,
            region or "(default boto)",
            (payload.user or "").strip(),
            user_prefix,
            (destination or "").strip(),
            success,
        )

        self._ensure_user_prefix(user_prefix)

        profile = self._load_profile(profile_key)
        trips = profile.get("trips")
        if not isinstance(trips, list):
            trips = []
        logger.info(
            "[S3] profile.json carregado | key=%s | viagens_existentes=%d",
            profile_key,
            len(trips),
        )

        start_at = _iso_z(_utc_day_start(payload.date_start))
        end_at = _iso_z(_utc_day_end(payload.date_end))

        file_generated: str | None = None
        status = TripRecordStatus.OK if success else TripRecordStatus.ERROR
        err_msg: str | None = None if success else (error_message or "Erro desconhecido")

        if success and trip_text is not None:
            fname = f"trip_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.txt"
            trip_key = f"{user_prefix}/trips/{fname}"
            self._s3.put_object(
                Bucket=self._bucket,
                Key=trip_key,
                Body=trip_text.encode("utf-8"),
                ContentType="text/plain; charset=utf-8",
            )
            file_generated = f"trips/{fname}"
            logger.info(
                "[S3] Roteiro .txt gravado | bucket=%s key=%s bytes=%d",
                self._bucket,
                trip_key,
                len(trip_text.encode("utf-8")),
            )

        entry: dict[str, Any] = {
            "destination": (destination or "").strip(),
            "start_at": start_at,
            "end_at": end_at,
            "status": status.value,
            "error_message": err_msg,
            "file_generated": file_generated,
        }
        trips.append(entry)

        out_profile: dict[str, Any] = {
            "user_id": (payload.user or "").strip(),
            "trips": trips,
        }
        self._save_profile(profile_key, out_profile)

        out_keys = {
            "profile": profile_key,
            "trip_txt": file_generated and f"{user_prefix}/{file_generated}" or "",
        }
        logger.info(
            "[S3] Persistência concluída | status_viagem=%s | chaves=%s",
            status.value,
            out_keys,
        )
        return out_keys
