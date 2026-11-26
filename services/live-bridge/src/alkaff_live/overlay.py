"""Renderer overlay Browser Source OBS.

Dua keluaran tanpa jaringan:
- ``overlay.json``: snapshot state untuk konsumen lain (SSE/Socket.IO di masa depan).
- ``overlay.html``: halaman transparan mandiri dengan data yang disematkan.

Renderer memakai template ``overlay-demo-clean-lab/index.html`` bila tersedia,
sehingga status orchestrator ditampilkan sebagai lima scene sinematik:
boot → scan → mix → analyze → result. Jika template tidak ada (misalnya paket
dipasang tanpa folder demo), renderer jatuh ke panel HTML sederhana.

Renderer ini sengaja "dumb": tidak mengambil keputusan bisnis dan tidak
mengirim pesan/DM.
"""

from __future__ import annotations

import html
import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config
from .events import utc_now

# Template Clean Lab hidup di sibling ``src/`` pada repo ini.
_SCENE_ROOT = Path(__file__).resolve().parents[2] / "overlay-demo-clean-lab"
_TEMPLATE = _SCENE_ROOT / "index.html"
_AUDIO = _SCENE_ROOT / "audio"

# Status orchestrator → scene pertama yang harus tampil.
_SCENE = {
    "IDLE": "boot",
    "LIVE": "boot",
    "COLLECTING": "scan",
    "PROCESSING": "mix",
    "READY": "result",
    "ERROR": "boot",
    "ENDED": "boot",
}

# Urutan scene yang diputar otomatis untuk tiap status. PROCESSING menampilkan
# mixing lalu analisis sebelum quotation siap.
_SEQUENCE = {
    "IDLE": ("boot",),
    "LIVE": ("boot",),
    "COLLECTING": ("scan",),
    "PROCESSING": ("mix", "analyze"),
    "READY": ("result",),
    "ERROR": ("boot",),
    "ENDED": ("boot",),
}

_PESAN = {
    "IDLE": "Menunggu LIVE dimulai.",
    "LIVE": "LIVE sekarang — ketik nama parfum di komentar.",
    "COLLECTING": "Pilih varian lewat komentar: 1 / 2 / 3.",
    "PROCESSING": "Meracik formula pilihan dan menganalisis profil aroma...",
    "READY": "Quotation siap. Silakan DM keyword bila ingin dikirim.",
    "ERROR": "Sambungan event terganggu; lab menampilkan ulang pemindaian.",
    "ENDED": "Selesai. Overlay disembunyikan.",
}


@dataclass(frozen=True)
class OverlayState:
    """Kontrak data minimal yang dikonsumsi overlay."""

    status: str
    scene: str
    visible: bool
    message: str
    detail: str
    cta: str | None
    updated_at: str
    event_count: int
    sequence: tuple[str, ...] = ("boot",)
    narrations: Mapping[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.narrations is None:
            object.__setattr__(self, "narrations", {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "scene": self.scene,
            "visible": self.visible,
            "message": self.message,
            "detail": self.detail,
            "cta": self.cta,
            "updatedAt": self.updated_at,
            "eventCount": self.event_count,
            "sequence": list(self.sequence),
            "narrations": dict(self.narrations),
        }


def _narrations(detail: str, keyword: str) -> dict[str, str]:
    """Teks narasi per scene, disesuaikan dengan produk yang sedang diproses."""
    subjek = detail or "aroma pilihan"
    return {
        "boot": f"Sistem lab Alkaff aktif. Saya AI perfumer. Mari kita racik {subjek}.",
        "scan": f"Memindai {subjek}. Top, heart, dan base dicocokkan dengan katalog.",
        "mix": f"Meracik {subjek}. Tetesan presisi, lalu diputar hingga homogen.",
        "analyze": f"Analisis profil {subjek} selesai. Karakter siap ditampilkan.",
        "result": f"Profil {subjek} siap. DM kata kunci {keyword} untuk detail quotation.",
    }


def build_overlay_state(snapshot: Mapping[str, Any], config: Config | None = None) -> OverlayState:
    """Ubah snapshot orchestrator menjadi state overlay Clean Lab."""
    cfg = config or Config()
    status = str(snapshot.get("status", "IDLE")).upper()
    konteks = snapshot.get("context") or {}
    if not isinstance(konteks, Mapping):
        konteks = {}

    sku = str(konteks.get("sku", "")).strip()
    variant = str(konteks.get("variant", "")).strip()
    detail = " · ".join(bit for bit in (sku, variant) if bit)

    pesan = _PESAN.get(status, "Status tidak dikenal.")
    if status == "PROCESSING" and detail:
        pesan = f"Meracik {detail} dan menganalisis profilnya..."
    elif status == "READY" and detail:
        pesan = f"Quotation {detail} siap."

    # CTA mengarahkan viewer memulai DM; aplikasi ini tidak mengirim DM.
    cta = f"DM kata kunci {cfg.quote_keyword} ke akun Alkaff" if status == "READY" else None

    scene = _SCENE.get(status, "boot")
    sequence = _SEQUENCE.get(status, (scene,))
    narasi = _narrations(detail, cfg.quote_keyword)
    if status == "ERROR":
        narasi["boot"] = pesan
    elif status == "IDLE":
        narasi["boot"] = pesan
    elif status == "LIVE" and detail:
        narasi["boot"] = f"LIVE dimulai. Katalog {detail} siap dipindai."

    return OverlayState(
        status=status,
        scene=scene,
        visible=status not in ("IDLE", "ENDED"),
        message=pesan,
        detail=detail,
        cta=cta,
        updated_at=utc_now(),
        event_count=int(snapshot.get("eventCount", 0)),
        sequence=sequence,
        narrations=narasi,
    )


def render_json(state: OverlayState) -> str:
    """Render state sebagai JSON UTF-8 (indentasi agar mudah dibaca)."""
    return json.dumps(state.to_dict(), ensure_ascii=False, indent=2)


def render_html(state: OverlayState, config: Config | None = None) -> str:
    """Render halaman HTML transparan 1920x1080 tanpa aset/network eksternal."""
    if _TEMPLATE.is_file():
        return _render_clean_lab_html(state, config or Config())
    return _render_fallback_html(state, config or Config())


def _render_clean_lab_html(state: OverlayState, cfg: Config) -> str:
    """Sematkan state ke template Clean Lab dan kirim perintah ke pemutar scene."""
    template = _TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(
        {
            "scene": state.scene,
            "auto": True,
            "sequence": list(state.sequence),
            "narrations": dict(state.narrations),
            "visible": state.visible,
            "voice": cfg.overlay.voice,
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    bootstrap = f"""<script type="application/json" id="alkaff-overlay-state">{payload}</script>
<script>
(function () {{
  var node = document.getElementById('alkaff-overlay-state');
  var data = JSON.parse(node.textContent);
  function kirim() {{ window.postMessage(data, '*'); }}
  if (document.readyState === 'loading') {{
    window.addEventListener('load', kirim);
  }} else {{
    setTimeout(kirim, 0);
  }}
}})();
</script>
"""
    return template.replace("</body>", bootstrap + "</body>")


def _render_fallback_html(state: OverlayState, config: Config | None = None) -> str:
    """Panel teks sederhana bila template Clean Lab tidak tersedia."""
    data = render_json(state).replace("</", "<\\/")
    kelas = "" if state.visible else " tersembunyi"
    badge = html.escape(state.status)
    judul = html.escape(state.message)
    detail = html.escape(state.detail)
    cta = html.escape(state.cta or "")

    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Overlay Alkaff — {badge}</title>
<style>
  html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: transparent; }}
  body {{ font-family: system-ui, sans-serif; color: #fff; overflow: hidden; }}
  .tersembunyi .panel {{ opacity: 0; }}
  .panel {{
    position: absolute; left: 5%; bottom: 12%; width: 42%;
    padding: 28px 34px; border-radius: 20px;
    background: linear-gradient(135deg, rgba(28,18,12,.88), rgba(78,44,20,.78));
    box-shadow: 0 12px 48px rgba(0,0,0,.45);
    transition: opacity .25s ease;
  }}
  .badge {{ font-size: 20px; letter-spacing: .16em; color: #e9c98b; }}
  .judul {{ font-size: 44px; font-weight: 700; margin-top: 10px; line-height: 1.15; }}
  .detail {{ font-size: 26px; color: #f4e4c8; margin-top: 8px; }}
  .cta {{ font-size: 30px; font-weight: 700; color: #ffd98a; margin-top: 16px; }}
</style>
</head>
<body class="{kelas.strip()}">
  <div class="panel">
    <div class="badge" id="badge"></div>
    <div class="judul" id="judul"></div>
    <div class="detail" id="detail"></div>
    <div class="cta" id="cta"></div>
  </div>
  <script type="application/json" id="overlay-state">{data}</script>
  <script>
    (function () {{
      var node = document.getElementById('overlay-state');
      var state = JSON.parse(node.textContent);
      document.getElementById('badge').textContent = state.status;
      document.getElementById('judul').textContent = state.message;
      document.getElementById('detail').textContent = state.detail || '';
      document.getElementById('cta').textContent = state.cta || '';
    }})();
  </script>
</body>
</html>
"""


def write_overlay(
    state: OverlayState, direktori: str | Path, config: Config | None = None
) -> tuple[Path, Path]:
    """Tulis ``overlay.json`` dan ``overlay.html`` ke direktori lokal.

    Bila template Clean Lab dipakai, folder ``audio/`` ikut disalin agar
    narasi MP3 tetap berjalan dari hasil build yang berdiri sendiri.
    """
    cfg = config or Config()
    tujuan = Path(direktori)
    tujuan.mkdir(parents=True, exist_ok=True)
    jalur_json = tujuan / "overlay.json"
    jalur_html = tujuan / "overlay.html"
    jalur_json.write_text(render_json(state) + "\n", encoding="utf-8")
    jalur_html.write_text(render_html(state, cfg), encoding="utf-8")
    if _TEMPLATE.is_file() and _AUDIO.is_dir():
        shutil.copytree(_AUDIO, tujuan / "audio", dirs_exist_ok=True)
    return jalur_json, jalur_html
