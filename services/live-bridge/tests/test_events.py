"""Tes normalisasi event (unittest, stdlib saja)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alkaff_live.events import (  # noqa: E402
    EventValidationError,
    LiveEvent,
    normalize_event,
)

CHAT_MENTAH = {
    "type": "chat",
    "occurredAt": "2026-11-26T09:31:12Z",
    "user": {
        "id": "6776663624629974021",
        "uniqueId": "alkaff_fan",
        "nickname": "Fan Alkaff",
    },
    "payload": {"comment": "oud dong kak"},
}


class NormalisasiEventTest(unittest.TestCase):
    def test_chat_mentah_dinormalisasi(self) -> None:
        event = normalize_event(CHAT_MENTAH)
        self.assertEqual(event.type, "chat")
        self.assertEqual(event.occurred_at, "2026-11-26T09:31:12Z")
        self.assertIsNotNone(event.user)
        assert event.user is not None
        self.assertEqual(event.user.id, "6776663624629974021")
        self.assertEqual(event.user.unique_id, "alkaff_fan")
        self.assertEqual(event.payload or {}, {"comment": "oud dong kak"})
        self.assertEqual(len(event.event_id), 64)

    def test_event_id_deterministik_dan_sensitif_payload(self) -> None:
        pertama = normalize_event(CHAT_MENTAH)
        kedua = normalize_event(dict(CHAT_MENTAH))
        self.assertEqual(pertama.event_id, kedua.event_id)

        diubah = dict(CHAT_MENTAH)
        diubah["payload"] = {"comment": "oud lain"}
        self.assertNotEqual(pertama.event_id, normalize_event(diubah).event_id)

    def test_event_id_eksplisit_dipakai(self) -> None:
        mentah = dict(CHAT_MENTAH)
        mentah["eventId"] = "evt-demo-001"
        self.assertEqual(normalize_event(mentah).event_id, "evt-demo-001")

    def test_roundtrip_dict(self) -> None:
        asli = normalize_event(CHAT_MENTAH)
        hasil = LiveEvent.from_dict(asli.to_dict())
        self.assertEqual(hasil, asli)
        self.assertEqual(hasil.to_dict(), asli.to_dict())

    def test_payload_flat_dan_alias_jenis(self) -> None:
        mentah = {
            "type": "comment",
            "occurredAt": "2026-11-26T09:31:12+00:00",
            "userId": "123",
            "nickname": "Pembeli",
            "comment": "  parfum apa  ",
        }
        event = normalize_event(mentah)
        self.assertEqual(event.type, "chat")
        self.assertEqual(event.occurred_at, "2026-11-26T09:31:12Z")
        assert event.user is not None
        self.assertEqual(event.user.id, "123")
        self.assertEqual(event.payload or {}, {"comment": "parfum apa"})

    def test_gift_mentah_tetap_bersarang(self) -> None:
        mentah = {
            "type": "gift",
            "occurredAt": "2026-11-26T09:31:20Z",
            "uniqueId": "alkaff_fan",
            "gift": {"giftId": 5655, "name": "Universe", "repeatEnd": 1},
        }
        event = normalize_event(mentah)
        gift = (event.payload or {}).get("gift")
        self.assertIsInstance(gift, dict)
        self.assertEqual(gift["name"], "Universe")
        assert event.user is not None
        self.assertEqual(event.user.unique_id, "alkaff_fan")

    def test_event_tanpa_user_diperbolehkan(self) -> None:
        event = normalize_event(
            {"type": "streamStart", "occurredAt": "2026-11-26T09:30:00Z", "payload": {}}
        )
        self.assertIsNone(event.user)

    def test_input_tidak_valid_ditolak(self) -> None:
        kasus = [
            {"occurredAt": "2026-11-26T09:30:00Z", "payload": {}},
            {"type": "unknown", "occurredAt": "2026-11-26T09:30:00Z", "payload": {}},
            {"type": "chat", "occurredAt": "kemarin", "payload": {}},
            {"type": "chat", "occurredAt": "2026-11-26T09:30:00", "payload": {}},
            {"type": "chat", "occurredAt": "2026-11-26T09:30:00Z", "payload": "teks"},
            {
                "type": "chat",
                "occurredAt": "2026-11-26T09:30:00Z",
                "user": "bukan objek",
                "payload": {},
            },
        ]
        for mentah in kasus:
            with self.subTest(mentah=mentah):
                with self.assertRaises(EventValidationError):
                    normalize_event(mentah)


if __name__ == "__main__":
    unittest.main()
