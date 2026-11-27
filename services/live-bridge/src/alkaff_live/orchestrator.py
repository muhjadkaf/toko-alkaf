"""State machine pipeline: event masuk -> status -> snapshot untuk overlay.

Modul ini adalah satu-satunya pemilik state. Tidak ada IO jaringan, tidak ada
antrean DM, dan tidak ada kode yang memulai percakapan dengan viewer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .config import Config
from .events import JENIS_EVENT, LiveEvent, normalize_event


class State(str, Enum):
    """Status global pipeline."""

    IDLE = "IDLE"
    LIVE = "LIVE"
    COLLECTING = "COLLECTING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    ERROR = "ERROR"
    ENDED = "ENDED"


# Matriks transisi yang diizinkan. Selain pasangan di bawah, transisi ditolak.
ALLOWED_TRANSITIONS: dict[State, frozenset[State]] = {
    State.IDLE: frozenset({State.LIVE, State.ENDED}),
    State.LIVE: frozenset({State.LIVE, State.COLLECTING, State.ENDED, State.ERROR}),
    State.COLLECTING: frozenset(
        {State.COLLECTING, State.PROCESSING, State.ENDED, State.ERROR}
    ),
    State.PROCESSING: frozenset({State.READY, State.ERROR, State.ENDED}),
    State.READY: frozenset({State.COLLECTING, State.ENDED, State.ERROR}),
    State.ERROR: frozenset({State.COLLECTING, State.LIVE, State.ENDED}),
    State.ENDED: frozenset({State.IDLE}),
}


class InvalidTransitionError(ValueError):
    """Transisi status tidak diizinkan oleh state machine."""


class UnknownEventTypeError(ValueError):
    """Jenis event tidak dikenal."""


@dataclass(frozen=True)
class Transition:
    """Hasil pemrosesan satu event (termasuk no-op untuk duplikat/streak)."""

    event_id: str
    event_type: str
    previous: State
    current: State
    reason: str
    changed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "previous": self.previous.value,
            "current": self.current.value,
            "reason": self.reason,
            "changed": self.changed,
        }


def _bangun_aturan() -> dict[tuple[State, str], State]:
    aturan: dict[tuple[State, str], State] = {
        (State.IDLE, "streamStart"): State.LIVE,
        (State.LIVE, "streamStart"): State.LIVE,
        (State.LIVE, "chat"): State.COLLECTING,
        (State.LIVE, "questionNew"): State.COLLECTING,
        (State.LIVE, "gift"): State.COLLECTING,
        (State.LIVE, "member"): State.LIVE,
        (State.LIVE, "like"): State.LIVE,
        (State.LIVE, "share"): State.LIVE,
        (State.LIVE, "follow"): State.LIVE,
        (State.COLLECTING, "chat"): State.COLLECTING,
        (State.COLLECTING, "questionNew"): State.COLLECTING,
        (State.COLLECTING, "gift"): State.COLLECTING,
        (State.COLLECTING, "member"): State.LIVE,
        (State.COLLECTING, "like"): State.COLLECTING,
        (State.COLLECTING, "share"): State.COLLECTING,
        (State.COLLECTING, "follow"): State.COLLECTING,
        (State.COLLECTING, "control.submit"): State.PROCESSING,
        (State.PROCESSING, "control.result"): State.READY,
        (State.PROCESSING, "control.error"): State.ERROR,
        (State.PROCESSING, "chat"): State.COLLECTING,
        (State.PROCESSING, "streamEnd"): State.ENDED,
        (State.READY, "chat"): State.COLLECTING,
        (State.READY, "gift"): State.COLLECTING,
        (State.READY, "control.submit"): State.PROCESSING,
        (State.ERROR, "control.retry"): State.COLLECTING,
        (State.ERROR, "chat"): State.COLLECTING,
        (State.ENDED, "control.reset"): State.IDLE,
    }
    for status in (State.IDLE, State.LIVE, State.COLLECTING, State.READY, State.ERROR):
        aturan[(status, "streamEnd")] = State.ENDED
    return aturan


ATURAN_TRANSISI: dict[tuple[State, str], State] = _bangun_aturan()


class Orchestrator:
    """Pemilik state dengan dedupe ``eventId`` dan filter streak gift."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._state = State.IDLE
        self._history: list[Transition] = []
        self._seen: set[str] = set()
        self._context: dict[str, Any] = {}
        self._event_count = 0
        self._last_event_id = ""

    @property
    def state(self) -> State:
        return self._state

    @property
    def history(self) -> tuple[Transition, ...]:
        return tuple(self._history)

    def can_transition(self, source: State, target: State) -> bool:
        """Periksa pasangan status terhadap matrik yang diizinkan."""
        sumber = State(source)
        tujuan = State(target)
        return tujuan in ALLOWED_TRANSITIONS[sumber]

    def transition_to(self, target: State, reason: str = "transisi manual") -> Transition:
        """Paksa transisi valid; lempar error bila tidak diizinkan."""
        tujuan = State(target)
        if not self.can_transition(self._state, tujuan):
            raise InvalidTransitionError(
                f"transisi {self._state.value} -> {tujuan.value} tidak diizinkan"
            )
        return self._simpan(tujuan, "", "manual", reason)

    def apply(self, event: LiveEvent | Mapping[str, Any]) -> Transition:
        """Proses satu event dan kembalikan transisi hasilnya."""
        if isinstance(event, Mapping):
            event = normalize_event(event)
        if not isinstance(event, LiveEvent):
            raise TypeError("event harus LiveEvent atau mapping")
        if event.type not in JENIS_EVENT:
            raise UnknownEventTypeError(f"jenis event '{event.type}' tidak dikenal")

        if event.event_id in self._seen:
            return self._no_op(event, "duplikat eventId, diabaikan")

        if self._streak_gift_belum_selesai(event):
            return self._no_op(event, "streak gift belum berakhir (repeatEnd != 1)")

        kunci = (self._state, event.type)
        target = ATURAN_TRANSISI.get(kunci)
        if target is None:
            raise InvalidTransitionError(
                f"event '{event.type}' tidak valid pada status {self._state.value}"
            )
        if not self.can_transition(self._state, target):
            raise InvalidTransitionError(
                f"transisi {self._state.value} -> {target.value} tidak diizinkan"
            )

        self._seen.add(event.event_id)
        self._event_count += 1
        self._last_event_id = event.event_id
        hasil = self._simpan(target, event.event_id, event.type, self._alasan(event, target))
        self._perbarui_konteks(event)
        return hasil

    def snapshot(self) -> dict[str, Any]:
        """Ambil state untuk renderer overlay (tanpa objek mutable mentah)."""
        return {
            "status": self._state.value,
            "eventCount": self._event_count,
            "lastEventId": self._last_event_id,
            "context": dict(self._context),
            "history": [item.to_dict() for item in self._history[-10:]],
        }

    def _simpan(
        self, target: State, event_id: str, event_type: str, reason: str
    ) -> Transition:
        hasil = Transition(
            event_id=event_id,
            event_type=event_type,
            previous=self._state,
            current=target,
            reason=reason,
            changed=target is not self._state,
        )
        self._state = target
        self._history.append(hasil)
        return hasil

    def _no_op(self, event: LiveEvent, reason: str) -> Transition:
        """Catat no-op untuk audit, tanpa mengubah status maupun jumlah event."""
        hasil = Transition(
            event_id=event.event_id,
            event_type=event.type,
            previous=self._state,
            current=self._state,
            reason=reason,
            changed=False,
        )
        self._history.append(hasil)
        return hasil

    @staticmethod
    def _streak_gift_belum_selesai(event: LiveEvent) -> bool:
        gift = (event.payload or {}).get("gift")
        if not isinstance(gift, Mapping):
            return False
        if gift.get("giftType") not in (1, "1", True):
            return False
        return str(gift.get("repeatEnd")) not in ("1", "True", "true")

    def _perbarui_konteks(self, event: LiveEvent) -> None:
        """Simpan konteks teater: klien, kata kunci, kasta botol, dan recap."""
        payload = event.payload or {}
        if event.type in ("streamStart", "streamEnd"):
            self._context.clear()
            return

        viewer = self._viewer(event)
        if viewer:
            sebelumnya = str(self._context.get("viewer", "")).strip()
            if sebelumnya and sebelumnya.lower() != viewer.lower():
                # Klien baru: kasta dan kata kunci lama tidak terbawa.
                for kunci in ("keyword", "shared", "giftTier", "giftName", "priority"):
                    self._context.pop(kunci, None)
            self._context["viewer"] = viewer

        if event.type in ("chat", "questionNew"):
            teks = self._teks_chat(payload)
            if teks:
                self._context["keyword"] = teks[:120]
        elif event.type == "share":
            self._context["shared"] = True
            if self._context.get("giftTier") != "founder":
                self._context["giftTier"] = "emerald"
        elif event.type == "gift":
            gift = payload.get("gift")
            nama = "gift"
            if isinstance(gift, Mapping) and gift.get("name"):
                nama = str(gift["name"])
            self._context["giftName"] = nama
            self._context["giftTier"] = "founder"
            self._context["priority"] = True
        elif event.type in ("control.submit", "control.result"):
            if payload.get("keyword"):
                self._context["keyword"] = str(payload["keyword"]).strip()[:120]
            if event.type == "control.submit":
                if payload.get("sku"):
                    self._context["sku"] = str(payload["sku"])
                if payload.get("variant"):
                    self._context["variant"] = str(payload["variant"])
                self._context.pop("quoteId", None)
                self._context.pop("quoteUrl", None)
                self._ingat_klien()
            else:
                if payload.get("quoteId"):
                    self._context["quoteId"] = str(payload["quoteId"])
                if payload.get("quoteUrl"):
                    self._context["quoteUrl"] = str(payload["quoteUrl"])

    @staticmethod
    def _viewer(event: LiveEvent) -> str:
        if event.user is None:
            return ""
        for nilai in (event.user.unique_id, event.user.nickname, event.user.id):
            bersih = str(nilai or "").strip().lstrip("@")
            if bersih:
                return bersih[:64]
        return ""

    @staticmethod
    def _teks_chat(payload: Mapping[str, Any]) -> str:
        for kunci in ("comment", "question", "text", "message"):
            nilai = payload.get(kunci)
            if nilai:
                return str(nilai).strip()
        return ""

    def _ingat_klien(self) -> None:
        """Simpan resep klien untuk papan recap lima merek terakhir."""
        klien = {
            "viewer": str(self._context.get("viewer", "")),
            "keyword": str(self._context.get("keyword", "")),
            "sku": str(self._context.get("sku", "")),
            "variant": str(self._context.get("variant", "")),
            "tier": str(self._context.get("giftTier", "classic")),
            "shared": bool(self._context.get("shared", False)),
            "priority": bool(self._context.get("priority", False)),
        }
        daftar = list(self._context.get("clients", []))
        daftar.append(klien)
        self._context["clients"] = daftar[-10:]
        self._context["clientCount"] = int(self._context.get("clientCount", 0)) + 1

    @staticmethod
    def _alasan(event: LiveEvent, target: State) -> str:
        if event.type == "control.submit":
            return "permintaan masuk, mulai proses racikan/quotation"
        if event.type == "control.result":
            return "quotation siap ditampilkan (CTA DM bersifat viewer-initiated)"
        if event.type == "control.error":
            return "proses gagal, pindah ke ERROR"
        if event.type == "streamEnd":
            return "stream berakhir, state dibersihkan"
        return f"event {event.type} diterima"
