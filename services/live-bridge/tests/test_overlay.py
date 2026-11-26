"""Tes renderer overlay Clean Lab (unittest, stdlib saja)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alkaff_live.config import Config, load_config  # noqa: E402
from alkaff_live.overlay import (  # noqa: E402
    build_overlay_state,
    render_html,
    render_json,
    write_overlay,
)


def snapshot(status: str, **context: str):
    return {"status": status, "context": context, "eventCount": 1}


class OverlayTest(unittest.TestCase):
    def test_status_memetakan_ke_lima_scene(self) -> None:
        diharapkan = {
            "LIVE": "boot",
            "COLLECTING": "scan",
            "PROCESSING": "mix",
            "READY": "result",
        }
        untuk_status, hasil = zip(*diharapkan.items())
        states = [build_overlay_state(snapshot(s)) for s in untuk_status]
        self.assertEqual(tuple(st.scene for st in states), hasil)

    def test_processing_memutar_mix_lalu_analyze(self) -> None:
        state = build_overlay_state(snapshot("PROCESSING", sku="ALK-01"))
        self.assertEqual(state.sequence, ("mix", "analyze"))
        self.assertIn("ALK-01", state.narrations["mix"])
        self.assertIn("ALK-01", state.narrations["analyze"])

    def test_idle_dan_ended_disembunyikan(self) -> None:
        for status in ("IDLE", "ENDED"):
            state = build_overlay_state(snapshot(status))
            self.assertFalse(state.visible)
            self.assertEqual(state.scene, "boot")

    def test_error_tetap_terlihat_dengan_narasi_gangguan(self) -> None:
        state = build_overlay_state(snapshot("ERROR"))
        self.assertTrue(state.visible)
        self.assertIn("terganggu", state.narrations["boot"])

    def test_json_memuat_sequence_dan_narasi(self) -> None:
        state = build_overlay_state(snapshot("READY", sku="ALK-01", variant="EDT"))
        data = json.loads(render_json(state))
        self.assertEqual(data["sequence"], ["result"])
        self.assertIn("ALK-01", data["narrations"]["result"])
        self.assertIn("QUOTE", data["narrations"]["result"])

    def test_html_memakai_template_clean_lab(self) -> None:
        state = build_overlay_state(snapshot("COLLECTING"))
        html = render_html(state)
        for scene in ("boot", "scan", "mix", "analyze", "result"):
            self.assertIn('data-key="' + scene + '"', html)
        self.assertIn("alkaff-overlay-state", html)
        self.assertIn("postMessage", html)
        self.assertNotIn("https://", html.replace("https://contoh.invalid", ""))

    def test_write_overlay_menyalin_audio(self) -> None:
        state = build_overlay_state(snapshot("READY"))
        with tempfile.TemporaryDirectory() as tmp:
            jalur_json, jalur_html = write_overlay(state, tmp)
            self.assertTrue(jalur_json.is_file())
            self.assertTrue(jalur_html.is_file())
            self.assertTrue((Path(tmp) / "audio" / "boot.mp3").is_file())
            self.assertTrue((Path(tmp) / "audio" / "result.mp3").is_file())

    def test_konfigurasi_voice(self) -> None:
        self.assertTrue(Config().overlay.voice)
        cfg = load_config({"overlay": {"voice": False}})
        self.assertFalse(cfg.overlay.voice)
        self.assertFalse(cfg.to_dict()["overlay"]["voice"])


if __name__ == "__main__":
    unittest.main()
