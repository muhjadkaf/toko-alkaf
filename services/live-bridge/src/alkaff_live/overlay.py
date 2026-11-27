"""Renderer overlay Browser Source OBS.

Dua keluaran tanpa jaringan:
- ``overlay.json``: snapshot state untuk konsumen lain (SSE/Socket.IO di masa depan).
- ``overlay.html``: halaman transparan mandiri dengan data yang disematkan.

Renderer memakai template ``overlay-demo-clean-lab/index.html`` bila tersedia,
sehingga status orchestrator ditampilkan sebagai lima babak sinematik:
boot → scan → mix → analyze → result. Jika template tidak ada, renderer jatuh
ke panel HTML sederhana.

Renderer sengaja "dumb": tidak mengambil keputusan bisnis, tidak mengirim DM,
dan tidak memesan antrean sungguhan. Semua gamifikasi hanya berupa tampilan.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
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

# Status orchestrator → babak pertama yang harus tampil.
_SCENE = {
    "IDLE": "boot",
    "LIVE": "boot",
    "COLLECTING": "scan",
    "PROCESSING": "mix",
    "READY": "result",
    "ERROR": "boot",
    "ENDED": "boot",
}

# Urutan otomatis per status. Gabungannya membentuk satu episode lima babak.
_SEQUENCE = {
    "IDLE": ("boot",),
    "LIVE": ("boot",),
    "COLLECTING": ("scan",),
    "PROCESSING": ("mix", "analyze"),
    "READY": ("result",),
    "ERROR": ("boot",),
    "ENDED": ("boot",),
}

# Profil timing. episode = 20 detik dengan SFX sintesis; narrated = mengikuti
# panjang MP3 narasi. Konfigurasi overlay.durations dapat menggantikan keduanya.
_EPISODE_DURATIONS = {
    "boot": 2000,
    "scan": 4000,
    "mix": 4000,
    "analyze": 4000,
    "result": 6000,
}
_NARRATED_DURATIONS = {
    "boot": 7000,
    "scan": 10500,
    "mix": 9500,
    "analyze": 7000,
    "result": 8000,
}

_TIER_LABEL = {
    "classic": "Classic Lab Edition",
    "emerald": "Emerald Doff · Tutup Emas",
    "founder": "Founder Edition · Kristal Hitam-Emas",
}

_PESAN = {
    "IDLE": "Menunggu LIVE dimulai.",
    "LIVE": "LIVE sekarang — ketik !racik di komentar.",
    "COLLECTING": "Bedah karakter: kata kunci penonton dipindai.",
    "PROCESSING": "Maserasi dan uji spektrum berjalan...",
    "READY": "Merek siap. Simpan kode resep di catatan pesanan.",
    "ERROR": "Sambungan event terganggu; lab menampilkan ulang pemindaian.",
    "ENDED": "Selesai. Overlay disembunyikan.",
}


@dataclass(frozen=True)
class OverlayState:
    """Kontrak data yang dikonsumsi overlay."""

    status: str
    scene: str
    visible: bool
    message: str
    detail: str
    cta: str | None
    updated_at: str
    event_count: int
    sequence: tuple[str, ...] = ("boot",)
    narrations: Mapping[str, str] | None = None
    viewer: str = ""
    keyword: str = ""
    brand: str = ""
    code: str = ""
    tier: str = "classic"
    tier_label: str = _TIER_LABEL["classic"]
    priority: bool = False
    egg: str = ""
    egg_name: str = ""
    recap: tuple[Mapping[str, str], ...] = ()
    stage: str = "full"
    sfx: bool = True
    durations: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        if self.narrations is None:
            object.__setattr__(self, "narrations", {})
        if self.durations is None:
            object.__setattr__(self, "durations", dict(_EPISODE_DURATIONS))

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
            "narrations": dict(self.narrations or {}),
            "viewer": self.viewer,
            "keyword": self.keyword,
            "brand": self.brand,
            "code": self.code,
            "tier": self.tier,
            "tierLabel": self.tier_label,
            "priority": self.priority,
            "egg": self.egg,
            "eggName": self.egg_name,
            "recap": [dict(item) for item in self.recap],
            "stage": self.stage,
            "sfx": self.sfx,
            "durations": dict(self.durations or {}),
        }


def _bersihkan_keyword(teks: str) -> str:
    """Buang awalan perintah `!racik` agar kata kunci rahasia bisa dicocokkan."""
    hasil = re.sub(r"^!\s*racik\b", "", str(teks).strip(), flags=re.IGNORECASE)
    hasil = re.sub(r"^racik\b", "", hasil, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", hasil).strip()[:120]


def _normalisasi_egg(teks: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]+", " ", str(teks).lower())).strip()


def _cocok_egg(keyword: str, config: Config) -> tuple[str, str]:
    if not config.easter_eggs or not keyword:
        return "", ""
    norm = _normalisasi_egg(keyword)
    if not norm:
        return "", ""
    for kunci in sorted(config.easter_eggs, key=len, reverse=True):
        if norm == kunci or kunci in norm:
            return kunci, config.easter_eggs[kunci]
    return "", ""


def _brand(viewer: str, detail: str, egg_name: str) -> str:
    if egg_name:
        return egg_name[:28]
    bersih = re.sub(r"[^0-9A-Za-z]+", " ", str(viewer)).strip()
    bersih = re.sub(r"\s+", " ", bersih).upper()
    if bersih:
        return bersih[:24]
    return (detail or "ALKaff").upper()[:24]


def _kode(viewer: str, keyword: str, sku: str) -> str:
    """Kode resep deterministik untuk screenshot, bukan nomor pesanan."""
    basis = f"{viewer}|{keyword}|{sku}".encode("utf-8")
    angka = int(hashlib.sha256(basis).hexdigest()[:8], 16) % 1000
    return f"ALK-{angka:03d}"


def _tier(klien: Mapping[str, Any]) -> str:
    if klien.get("giftTier") == "founder" or klien.get("priority"):
        return "founder"
    if klien.get("shared") or klien.get("giftTier") == "emerald":
        return "emerald"
    return "classic"


def _klien_aktif(konteks: Mapping[str, Any], status: str) -> dict[str, Any]:
    daftar = konteks.get("clients")
    if status in ("PROCESSING", "READY") and isinstance(daftar, (list, tuple)) and daftar:
        terakhir = daftar[-1]
        if isinstance(terakhir, Mapping):
            return dict(terakhir)
    return {
        "viewer": konteks.get("viewer", ""),
        "keyword": konteks.get("keyword", ""),
        "sku": konteks.get("sku", ""),
        "variant": konteks.get("variant", ""),
        "giftTier": konteks.get("giftTier", ""),
        "shared": konteks.get("shared", False),
        "priority": konteks.get("priority", False),
    }


def _recap(
    konteks: Mapping[str, Any], status: str, config: Config
) -> tuple[Mapping[str, str], ...]:
    daftar = konteks.get("clients")
    jumlah = int(konteks.get("clientCount", 0) or 0)
    if (
        status != "READY"
        or jumlah <= 0
        or jumlah % config.recap_every != 0
        or not isinstance(daftar, (list, tuple))
        or len(daftar) < config.recap_every
    ):
        return ()
    hasil: list[Mapping[str, str]] = []
    for klien in list(daftar)[-config.recap_every :]:
        if not isinstance(klien, Mapping):
            continue
        viewer = str(klien.get("viewer", ""))
        kata = _bersihkan_keyword(str(klien.get("keyword", "")))
        _, egg_name = _cocok_egg(kata, config)
        merek = _brand(viewer, str(klien.get("sku", "")), egg_name)
        hasil.append(
            {
                "brand": merek,
                "code": _kode(viewer, kata, str(klien.get("sku", ""))),
                "tier": _tier(klien),
            }
        )
    return tuple(hasil)


def _narrations(
    detail: str,
    keyword: str,
    viewer: str,
    brand: str,
    code: str,
    config: Config,
    egg_name: str,
) -> dict[str, str]:
    """Teks narasi per babak, mengikuti klien aktif dan merek yang lahir."""
    subjek = detail or "aroma pilihan"
    kata = keyword or "aroma pilihan"
    merek = brand or subjek
    panggil = viewer or "klien berikutnya"
    keyword_dm = config.quote_keyword

    if egg_name:
        boot = (
            f"Easter egg terdeteksi! {panggil} meminta {kata}. "
            f"Robot pusing, tapi merek jenakanya {egg_name}."
        )
    else:
        boot = f"Klien masuk ruang VIP. Selamat datang {panggil}. Buka berkas {merek}."
    return {
        "boot": boot,
        "scan": (
            f"Bedah karakter {kata} untuk {merek}. "
            "Top Bergamot, heart Lavender, base White Musk."
        ),
        "mix": f"Ruang maserasi {subjek}. Extrait 30 persen, vortex 2.400 RPM. Tahan napas.",
        "analyze": f"Uji spektrum {subjek} selesai. Sillage tajam, akhir lembut.",
        "result": (
            f"Resmi rilis: ALKAFF x {merek}. Kode resep {code}. Screenshot, lalu tulis "
            f"kode di catatan pesanan. DM {keyword_dm} bila ingin dikirim."
        ),
    }


def _durasi(config: Config) -> dict[str, int]:
    dasar = dict(_NARRATED_DURATIONS if config.overlay.voice else _EPISODE_DURATIONS)
    dasar.update(config.overlay.durations)
    return dasar


def build_overlay_state(snapshot: Mapping[str, Any], config: Config | None = None) -> OverlayState:
    """Ubah snapshot orchestrator menjadi state teater lima babak."""
    cfg = config or Config()
    status = str(snapshot.get("status", "IDLE")).upper()
    konteks = snapshot.get("context") or {}
    if not isinstance(konteks, Mapping):
        konteks = {}

    sku = str(konteks.get("sku", "")).strip()
    variant = str(konteks.get("variant", "")).strip()
    detail = " · ".join(bit for bit in (sku, variant) if bit)

    klien = _klien_aktif(konteks, status)
    viewer = str(klien.get("viewer", "")).strip()
    keyword = _bersihkan_keyword(str(klien.get("keyword", "")))
    egg, egg_name = _cocok_egg(keyword, cfg)
    merek = _brand(viewer, detail, egg_name)
    kode = _kode(viewer, keyword, sku)
    kasta = _tier(klien)

    pesan = _PESAN.get(status, "Status tidak dikenal.")
    if status == "PROCESSING" and detail:
        pesan = f"Maserasi dan uji spektrum {detail} berjalan..."
    elif status == "READY":
        pesan = f"{merek} rilis · kode resep {kode}. Simpan di catatan pesanan."

    # CTA mengarahkan viewer memulai DM; aplikasi ini tidak mengirim DM.
    cta = (
        f"Simpan kode resep {kode} di catatan pesanan — DM {cfg.quote_keyword} bila ingin dikirim"
        if status == "READY"
        else None
    )

    scene = _SCENE.get(status, "boot")
    sequence = _SEQUENCE.get(status, (scene,))
    narasi = _narrations(detail, keyword, viewer, merek, kode, cfg, egg_name)
    if status in ("ERROR", "IDLE"):
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
        viewer=viewer,
        keyword=keyword,
        brand=merek,
        code=kode,
        tier=kasta,
        tier_label=_TIER_LABEL[kasta],
        priority=bool(klien.get("priority", False)),
        egg=egg,
        egg_name=egg_name,
        recap=_recap(konteks, status, cfg),
        stage=cfg.overlay.stage,
        sfx=cfg.overlay.sfx,
        durations=_durasi(cfg),
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
    """Sematkan state ke template Clean Lab dan kirim perintah ke pemutar babak."""
    template = _TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(
        {
            "scene": state.scene,
            "auto": True,
            "sequence": list(state.sequence),
            "narrations": dict(state.narrations or {}),
            "visible": state.visible,
            "voice": cfg.overlay.voice,
            "sfx": state.sfx,
            "stage": state.stage,
            "durations": dict(state.durations or {}),
            "viewer": state.viewer,
            "keyword": state.keyword,
            "brand": state.brand,
            "code": state.code,
            "tier": state.tier,
            "tierLabel": state.tier_label,
            "priority": state.priority,
            "egg": state.egg,
            "eggName": state.egg_name,
            "recap": [dict(item) for item in state.recap],
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
