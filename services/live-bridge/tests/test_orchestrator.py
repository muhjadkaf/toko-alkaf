"""Tes state machine orchestrator (unittest, stdlib saja)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alkaff_live.config import Config  # noqa: E402
from alkaff_live.events import normalize_event  # noqa: E402
from alkaff_live.orchestrator import (  # noqa: E402
    InvalidTransitionError,
    Orchestrator,
    State,
)
from alkaff_live.overlay import build_overlay_state, render_json  # noqa: E402


def buat_event(jenis: str, event_id: str, payload: dict[str, Any] | None = None):
    """Buat event dengan eventId eksplisit agar dedupe mudah diuji."""
    return normalize_event(
        {
            "eventId": event_id,
            "type": jenis,
            "occurredAt": "2026-11-26T09:30:00Z",
            "payload": payload or {},
        }
    )


class OrchestratorTest(unittest.TestCase):
    def test_alur_lengkap(self) -> None:
        orchestrator = Orchestrator(Config())
        urutan = [
            ("streamStart", "e1", {}),
            ("chat", "e2", {"comment": "oud"}),
            ("control.submit", "e3", {"sku": "ALK-01", "variant": "EDT"}),
            ("control.result", "e4", {"quoteId": "Q-1", "quoteUrl": "https://contoh.invalid/q"}),
            ("streamEnd", "e5", {}),
        ]
        hasil = [orchestrator.apply(buat_event(*item)) for item in urutan]

        self.assertEqual(
            [transisi.current for transisi in hasil],
            [State.LIVE, State.COLLECTING, State.PROCESSING, State.READY, State.ENDED],
        )
        self.assertTrue(all(transisi.changed for transisi in hasil))
        snapshot = orchestrator.snapshot()
        self.assertEqual(snapshot["status"], "ENDED")
        self.assertEqual(snapshot["eventCount"], 5)
        self.assertEqual(snapshot["lastEventId"], "e5")

    def test_konteks_dan_state_overlay(self) -> None:
        orchestrator = Orchestrator()
        orchestrator.apply(buat_event("streamStart", "e1"))
        orchestrator.apply(buat_event("chat", "e2", {"comment": "oud"}))
        orchestrator.apply(
            buat_event("control.submit", "e3", {"sku": "ALK-01", "variant": "EDT"})
        )
        orchestrator.apply(buat_event("control.result", "e4", {"quoteId": "Q-1"}))

        snapshot = orchestrator.snapshot()
        self.assertEqual(snapshot["context"]["sku"], "ALK-01")
        self.assertEqual(snapshot["context"]["variant"], "EDT")
        self.assertEqual(snapshot["context"]["quoteId"], "Q-1")

        overlay = build_overlay_state(snapshot, Config())
        self.assertEqual(overlay.status, "READY")
        self.assertEqual(overlay.scene, "result")
        self.assertEqual(overlay.sequence, ("result",))
        self.assertTrue(overlay.visible)
        self.assertIn("QUOTE", overlay.cta or "")
        self.assertIn("ALK-01", render_json(overlay))

    def test_transisi_tidak_valid_ditolak(self) -> None:
        orchestrator = Orchestrator()
        with self.assertRaises(InvalidTransitionError):
            orchestrator.apply(buat_event("chat", "e1", {"comment": "oud"}))
        with self.assertRaises(InvalidTransitionError):
            orchestrator.transition_to(State.READY)
        self.assertEqual(orchestrator.state, State.IDLE)
        self.assertEqual(orchestrator.snapshot()["eventCount"], 0)

    def test_matriks_transisi(self) -> None:
        orchestrator = Orchestrator()
        self.assertTrue(orchestrator.can_transition(State.IDLE, State.LIVE))
        self.assertFalse(orchestrator.can_transition(State.IDLE, State.READY))
        self.assertTrue(orchestrator.can_transition(State.PROCESSING, State.READY))
        self.assertTrue(orchestrator.can_transition(State.ENDED, State.IDLE))

    def test_event_duplikat_diabaikan(self) -> None:
        orchestrator = Orchestrator()
        pertama = orchestrator.apply(buat_event("streamStart", "e1"))
        kedua = orchestrator.apply(buat_event("streamStart", "e1"))

        self.assertTrue(pertama.changed)
        self.assertFalse(kedua.changed)
        self.assertIn("duplikat", kedua.reason)
        self.assertEqual(orchestrator.state, State.LIVE)
        self.assertEqual(orchestrator.snapshot()["eventCount"], 1)
        self.assertEqual(len(orchestrator.history), 2)

    def test_streak_gift_hanya_diproses_saat_repeat_end(self) -> None:
        orchestrator = Orchestrator()
        orchestrator.apply(buat_event("streamStart", "e1"))
        orchestrator.apply(buat_event("chat", "e2", {"comment": "oud"}))

        belum_selesai = buat_event(
            "gift",
            "e3",
            {"gift": {"name": "Universe", "giftType": 1, "repeatEnd": 0}},
        )
        hasil = orchestrator.apply(belum_selesai)
        self.assertFalse(hasil.changed)
        self.assertEqual(orchestrator.state, State.COLLECTING)

        selesai = buat_event(
            "gift",
            "e4",
            {"gift": {"name": "Universe", "giftType": 1, "repeatEnd": 1}},
        )
        diterima = orchestrator.apply(selesai)
        self.assertNotIn("streak", diterima.reason)
        self.assertEqual(orchestrator.state, State.COLLECTING)
        self.assertEqual(orchestrator.snapshot()["eventCount"], 3)

    def test_jalur_error_dan_retry(self) -> None:
        orchestrator = Orchestrator()
        orchestrator.apply(buat_event("streamStart", "e1"))
        orchestrator.apply(buat_event("chat", "e2", {"comment": "oud"}))
        orchestrator.apply(buat_event("control.submit", "e3", {"sku": "ALK-01"}))

        self.assertEqual(orchestrator.apply(buat_event("control.error", "e4")).current, State.ERROR)
        self.assertEqual(orchestrator.apply(buat_event("control.retry", "e5")).current, State.COLLECTING)

        overlay = build_overlay_state(orchestrator.snapshot())
        self.assertEqual(overlay.status, "COLLECTING")
        self.assertTrue(overlay.visible)

    def test_reset_dari_ended_ke_idle(self) -> None:
        orchestrator = Orchestrator()
        orchestrator.apply(buat_event("streamStart", "e1"))
        orchestrator.apply(buat_event("streamEnd", "e2"))
        self.assertEqual(orchestrator.state, State.ENDED)
        overlay = build_overlay_state(orchestrator.snapshot())
        self.assertFalse(overlay.visible)

        orchestrator.apply(buat_event("control.reset", "e3"))
        self.assertEqual(orchestrator.state, State.IDLE)
        self.assertEqual(build_overlay_state(orchestrator.snapshot()).scene, "boot")
        self.assertFalse(build_overlay_state(orchestrator.snapshot()).visible)


if __name__ == "__main__":
    unittest.main()
