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

    def test_koleksi_then_processing_membentuk_episode_lima_babak(self) -> None:
        live = build_overlay_state(snapshot("LIVE"))
        koleksi = build_overlay_state(snapshot("COLLECTING", sku="ALK-01"))
        proses = build_overlay_state(snapshot("PROCESSING", sku="ALK-01"))
        hasil = build_overlay_state(snapshot("READY", sku="ALK-01"))
        self.assertEqual(koleksi.sequence, ("scan",))
        self.assertEqual(proses.sequence, ("mix", "analyze"))
        self.assertEqual(hasil.sequence, ("result",))
        self.assertEqual(
            tuple(live.sequence + koleksi.sequence + proses.sequence + hasil.sequence),
            ("boot", "scan", "mix", "analyze", "result"),
        )
        self.assertIn("ALK-01", proses.narrations["mix"])
        self.assertIn("ALK-01", proses.narrations["analyze"])

    def test_easter_egg_menjadi_merek_jenaka(self) -> None:
        cfg = load_config({"easterEggs": {"hujan mantan": "EAU DE KENANGAN"}})
        state = build_overlay_state(
            snapshot("COLLECTING", viewer="hujan_aja", keyword="!racik hujan mantan"), cfg
        )
        self.assertEqual(state.keyword, "hujan mantan")
        self.assertEqual(state.egg, "hujan mantan")
        self.assertEqual(state.brand, "EAU DE KENANGAN")
        self.assertIn("pusing", state.narrations["boot"])

    def test_kasta_gift_menjadi_founder(self) -> None:
        state = build_overlay_state(
            snapshot(
                "READY",
                viewer="alkaff_fan",
                keyword="oud",
                sku="ALK-01",
                giftTier="founder",
                priority=True,
            )
        )
        self.assertEqual(state.tier, "founder")
        self.assertIn("Founder Edition", state.tier_label)
        self.assertTrue(state.priority)
        self.assertIn("VIP MAKLON UNLOCKED!", render_html(state))

    def test_recap_lima_merek_terakhir(self) -> None:
        klien = [
            {
                "viewer": f"klien{i}",
                "keyword": "oud",
                "sku": f"ALK-0{i}",
                "tier": "classic",
            }
            for i in range(1, 6)
        ]
        state = build_overlay_state(
            {
                "status": "READY",
                "eventCount": 20,
                "context": {"clientCount": 5, "clients": klien},
            }
        )
        self.assertEqual(len(state.recap), 5)
        self.assertTrue(all(item["code"].startswith("ALK-") for item in state.recap))
        self.assertEqual(state.recap[-1]["brand"], "KLIEN5")

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

    def test_mode_split_dan_durasi_episode(self) -> None:
        cfg = load_config(
            {
                "overlay": {
                    "stage": "split",
                    "voice": False,
                    "sfx": True,
                    "durations": {"boot": 1000},
                }
            }
        )
        state = build_overlay_state(snapshot("LIVE"), cfg)
        self.assertEqual(state.stage, "split")
        self.assertTrue(state.sfx)
        self.assertEqual(state.durations["boot"], 1000)
        self.assertEqual(state.durations["result"], 6000)
        self.assertIn("split-stage", render_html(state, cfg))

    def test_mode_split_tidak_valid_ditolak(self) -> None:
        from alkaff_live.config import ConfigError

        with self.assertRaises(ConfigError):
            load_config({"overlay": {"stage": "teater"}})

    def test_tema_csv_mengubah_narasi_dan_cta(self) -> None:
        state = build_overlay_state(
            snapshot("READY", viewer="rani", keyword="!racik office", sku="ALK-L-001")
        )
        self.assertEqual(state.theme, "Parfum Kantor Ringan")
        self.assertEqual(state.theme_keyword, "OFFICE")
        self.assertIn("white musk, iris, lavender", state.narrations["scan"])
        self.assertIn("Gambaran keluarga", state.narrations["scan"])
        self.assertIn("DM OFFICE", state.cta)
        self.assertIn('"themeKeyword": "OFFICE"', render_html(state))

    def test_tema_eksplisit_mengalahkan_keyword(self) -> None:
        state = build_overlay_state(
            snapshot("COLLECTING", keyword="oud", tema="Wangi Malam Formal")
        )
        self.assertEqual(state.theme, "Wangi Malam Formal")
        self.assertEqual(state.theme_keyword, "NIGHT")

    def test_tema_fallback_quote_bila_csv_tidak_ada(self) -> None:
        cfg = load_config({"themesCsv": "tidak-ada.csv"})
        state = build_overlay_state(snapshot("READY"), cfg)
        self.assertEqual(state.theme, "")
        self.assertEqual(state.theme_keyword, "QUOTE")
        self.assertIn("DM QUOTE", state.cta)


if __name__ == "__main__":
    unittest.main()
