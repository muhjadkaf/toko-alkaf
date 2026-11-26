"""Normalisasi event LIVE menjadi envelope internal yang tunggal.

Bentuk input mengikuti payload dokumentasi TikTok LIVE (camelCase), tetapi ini
hanya transformer data lokal: tidak ada WebSocket, HTTP, atau klien TikTok.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Event publik (dokumentasi) + event kontrol internal untuk state machine.
JENIS_EVENT = frozenset(
    {
        "streamStart",
        "streamEnd",
        "chat",
        "gift",
        "member",
        "like",
        "share",
        "follow",
        "questionNew",
        "control.submit",
        "control.result",
        "control.error",
        "control.retry",
        "control.reset",
    }
)

_ALIAS_JENIS = {
    "comment": "chat",
    "chat_message": "chat",
    "stream_start": "streamStart",
    "stream_started": "streamStart",
    "stream_end": "streamEnd",
    "stream_ended": "streamEnd",
}

_KUNCI_ENVELOP = {
    "eventId",
    "event_id",
    "type",
    "occurredAt",
    "occurred_at",
    "user",
    "userInfo",
    "payload",
}
_KUNCI_USER = {"id", "userId", "user_id", "uniqueId", "unique_id", "nickname", "nickName"}
_CALON_USER = frozenset(_KUNCI_USER | {"user", "userInfo"})


class EventValidationError(ValueError):
    """Payload event tidak memenuhi kontrak minimal."""


@dataclass(frozen=True)
class LiveUser:
    """Identitas viewer yang sudah dinormalisasi."""

    id: str = ""
    unique_id: str = ""
    nickname: str = ""

    def to_dict(self) -> dict[str, str]:
        hasil: dict[str, str] = {}
        if self.id:
            hasil["id"] = self.id
        if self.unique_id:
            hasil["uniqueId"] = self.unique_id
        if self.nickname:
            hasil["nickname"] = self.nickname
        return hasil


@dataclass(frozen=True)
class LiveEvent:
    """Envelope event internal.

    ``event_id`` dipakai untuk idempotency: event yang sama tidak boleh memicu
    dua transisi/animasi.
    """

    event_id: str
    type: str
    occurred_at: str
    user: LiveUser | None = None
    payload: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise EventValidationError("eventId wajib berupa string non-kosong")
        if self.type not in JENIS_EVENT:
            raise EventValidationError(f"jenis event '{self.type}' tidak dikenal")
        if not isinstance(self.occurred_at, str) or not self.occurred_at.strip():
            raise EventValidationError("occurredAt wajib berupa string ISO-8601")
        if self.payload is not None and not isinstance(self.payload, dict):
            raise EventValidationError("payload harus berupa objek")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LiveEvent":
        return normalize_event(data)

    def to_dict(self) -> dict[str, Any]:
        hasil: dict[str, Any] = {
            "eventId": self.event_id,
            "type": self.type,
            "occurredAt": self.occurred_at,
        }
        if self.user is not None:
            hasil["user"] = self.user.to_dict()
        hasil["payload"] = copy.deepcopy(self.payload or {})
        return hasil


def utc_now() -> str:
    """Waktu UTC sekarang dalam bentuk ISO-8601 berakhiran ``Z``."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def normalize_event(raw: Mapping[str, Any]) -> LiveEvent:
    """Ubah payload mentah menjadi ``LiveEvent`` dan hitung ``eventId`` bila perlu."""
    if not isinstance(raw, Mapping):
        raise EventValidationError("event harus berupa objek/JSON mapping")

    jenis_mentah = _ambil(raw, "type", "eventType")
    if jenis_mentah is None or not str(jenis_mentah).strip():
        raise EventValidationError("field 'type' wajib ada")
    jenis = str(jenis_mentah).strip()
    jenis = _ALIAS_JENIS.get(jenis, jenis)
    if jenis not in JENIS_EVENT:
        raise EventValidationError(f"jenis event '{jenis}' tidak dikenal")

    occurred_at = _normalisasi_waktu(
        _ambil(raw, "occurredAt", "occurred_at", default=utc_now())
    )
    user = _normalisasi_user(raw)
    payload = _normalisasi_payload(raw)

    if jenis == "chat" and "comment" in payload:
        payload["comment"] = str(payload["comment"]).strip()
    if "gift" in payload and isinstance(payload["gift"], Mapping):
        payload["gift"] = dict(payload["gift"])

    event_id_mentah = _ambil(raw, "eventId", "event_id")
    if event_id_mentah is not None:
        event_id = str(event_id_mentah).strip()
        if not event_id:
            raise EventValidationError("eventId tidak boleh kosong")
    else:
        event_id = _hitung_event_id(jenis, occurred_at, user, payload)

    return LiveEvent(
        event_id=event_id,
        type=jenis,
        occurred_at=occurred_at,
        user=user,
        payload=payload,
    )


def _hitung_event_id(
    jenis: str, occurred_at: str, user: LiveUser | None, payload: dict[str, Any]
) -> str:
    basis = {
        "type": jenis,
        "occurredAt": occurred_at,
        "user": user.to_dict() if user else {},
        "payload": payload,
    }
    kanonik = json.dumps(
        basis, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )
    return hashlib.sha256(kanonik.encode("utf-8")).hexdigest()


def _normalisasi_waktu(nilai: Any) -> str:
    if not isinstance(nilai, str) or not nilai.strip():
        raise EventValidationError("occurredAt wajib berupa string ISO-8601")
    teks = nilai.strip().replace("Z", "+00:00")
    try:
        waktu = datetime.fromisoformat(teks)
    except ValueError as exc:
        raise EventValidationError(f"occurredAt '{nilai}' bukan ISO-8601 valid") from exc
    if waktu.tzinfo is None:
        raise EventValidationError("occurredAt wajib menyertakan timezone (mis. 'Z')")
    return waktu.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _normalisasi_user(raw: Mapping[str, Any]) -> LiveUser | None:
    pengguna = _ambil(raw, "user", "userInfo")
    if pengguna is None:
        if not any(kunci in raw for kunci in _CALON_USER):
            return None
        pengguna = {
            "id": _ambil(raw, "userId", "user_id"),
            "uniqueId": _ambil(raw, "uniqueId", "unique_id"),
            "nickname": _ambil(raw, "nickname", "nickName"),
        }
    if not isinstance(pengguna, Mapping):
        raise EventValidationError("field 'user' harus berupa objek")

    user_id = _ambil(pengguna, "id", "userId", "user_id")
    unique_id = _ambil(pengguna, "uniqueId", "unique_id")
    nickname = _ambil(pengguna, "nickname", "nickName")
    if not any(item not in (None, "") for item in (user_id, unique_id, nickname)):
        return None
    return LiveUser(
        id=str(user_id or ""),
        unique_id=str(unique_id or ""),
        nickname=str(nickname or ""),
    )


def _normalisasi_payload(raw: Mapping[str, Any]) -> dict[str, Any]:
    mentah = _ambil(raw, "payload", default={})
    if not isinstance(mentah, Mapping):
        raise EventValidationError("field 'payload' harus berupa objek")
    payload = copy.deepcopy(dict(mentah))

    # Field mentah yang bukan envelope/user ikut masuk payload (mis. gift, comment).
    for kunci, nilai in raw.items():
        if kunci in _KUNCI_ENVELOP or kunci in _KUNCI_USER or kunci == "eventType":
            continue
        payload.setdefault(kunci, copy.deepcopy(nilai))
    return payload


def _ambil(data: Mapping[str, Any], *kunci: str, default: Any = None) -> Any:
    for kunci_item in kunci:
        if kunci_item in data:
            return data[kunci_item]
    return default


# Dipakai README/docs untuk menjelaskan pencocokan alias tanpa fuzzy dependency.
POLA_ALIAS = re.compile(r"[^\w\s]+", re.UNICODE)
