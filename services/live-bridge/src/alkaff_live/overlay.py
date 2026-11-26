"""Renderer overlay Browser Source OBS.

Dua keluaran tanpa jaringan:
- ``overlay.json``: snapshot state untuk konsumen lain (SSE/Socket.IO di masa depan).
- ``overlay.html``: halaman transparan mandiri dengan data yang disematkan.

Renderer ini sengaja "dumb": tidak mengambil keputusan bisnis dan tidak
mengirim pesan/DM.
"""

from __future__ import annotations

import html
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config
from .events import utc_now

_SCENE = {
    "IDLE": "idle",
    "LIVE": "live",
    "COLLECTING": "collect",
    "PROCESSING": "mixer",
    "READY": "quote-cta",
    "ERROR": "reconnecting",
    "ENDED": "hidden",
}

_PESAN = {
    "IDLE": "Menunggu LIVE dimulai.",
    "LIVE": "LIVE sekarang — ketik nama parfum di komentar.",
    "COLLECTING": "Pilih varian lewat komentar: 1 / 2 / 3.",
    "PROCESSING": "Meracik parfum dan menyiapkan quotation...",
    "READY": "Quotation siap. Silakan DM keyword bila ingin dikirim.",
    "ERROR": "Sambungan event terganggu; tidak menampilkan data basi.",
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
        }


def build_overlay_state(snapshot: Mapping[str, Any], config: Config | None = None) -> OverlayState:
    """Ubah snapshot orchestrator menjadi state overlay."""
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
        pesan = f"Meracik {detail}..."
    elif status == "READY" and detail:
        pesan = f"Quotation {detail} siap."

    # CTA mengarahkan viewer memulai DM; aplikasi ini tidak mengirim DM.
    cta = f"DM kata kunci {cfg.quote_keyword} ke akun Alkaff" if status == "READY" else None

    return OverlayState(
        status=status,
        scene=_SCENE.get(status, "idle"),
        visible=status not in ("IDLE", "ENDED"),
        message=pesan,
        detail=detail,
        cta=cta,
        updated_at=utc_now(),
        event_count=int(snapshot.get("eventCount", 0)),
    )


def render_json(state: OverlayState) -> str:
    """Render state sebagai JSON UTF-8 (indentasi agar mudah dibaca)."""
    return json.dumps(state.to_dict(), ensure_ascii=False, indent=2)


def render_html(state: OverlayState, config: Config | None = None) -> str:
    """Render halaman HTML transparan 1920x1080 tanpa aset/network eksternal."""
    cfg = config or Config()
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
    """Tulis ``overlay.json`` dan ``overlay.html`` ke direktori lokal."""
    cfg = config or Config()
    tujuan = Path(direktori)
    tujuan.mkdir(parents=True, exist_ok=True)
    jalur_json = tujuan / "overlay.json"
    jalur_html = tujuan / "overlay.html"
    jalur_json.write_text(render_json(state) + "\n", encoding="utf-8")
    jalur_html.write_text(render_html(state, cfg), encoding="utf-8")
    return jalur_json, jalur_html
