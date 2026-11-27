"""Pemuat konfigurasi lokal.

Konfigurasi dibaca dari ``dict`` atau file JSON dengan ``json`` bawaan Python.
Tidak ada PyYAML, tidak ada environment secret, dan tidak ada akses jaringan.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Pengaman sederhana: skeleton ini tidak boleh menyimpan kredensial apa pun.
_POLA_KREDENSIAL = re.compile(
    r"token|secret|password|passwd|api[_-]?key|authorization|credential",
    re.IGNORECASE,
)


class ConfigError(ValueError):
    """Konfigurasi tidak valid atau mengandung field yang dilarang."""


_SCENES = frozenset({"boot", "scan", "mix", "analyze", "result"})
_STAGES = frozenset({"full", "split"})


@dataclass(frozen=True)
class OverlayConfig:
    """Kanvas dan timing Browser Source OBS."""

    width: int = 1920
    height: int = 1080
    transparent: bool = True
    voice: bool = True
    sfx: bool = True
    stage: str = "full"
    durations: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Config:
    """Konfigurasi ringan untuk demo pipeline lokal."""

    app_name: str = "alkaff-live-bridge"
    session_ttl_seconds: int = 60
    session_extension_seconds: int = 15
    max_quotes_per_minute: int = 20
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    gift_tiers: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    easter_eggs: Mapping[str, str] = field(default_factory=dict)
    recap_every: int = 5
    quote_keyword: str = "QUOTE"
    quote_base_url: str = "https://contoh.invalid/quote"
    themes_csv: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Config":
        """Buat Config dari ``dict``/mapping dengan kunci camelCase maupun snake_case."""
        if not isinstance(data, Mapping):
            raise ConfigError("konfigurasi harus berupa mapping/dict")
        _tolak_kredensial(data)

        overlay_raw = _ambil(data, "overlay", default={})
        if not isinstance(overlay_raw, Mapping):
            raise ConfigError("field 'overlay' harus berupa objek")

        demo_raw = _ambil(data, "demo", default={})
        if not isinstance(demo_raw, Mapping):
            raise ConfigError("field 'demo' harus berupa objek")

        tiers_raw = _ambil(data, "giftTiers", "gift_tiers", default={})
        if not isinstance(tiers_raw, Mapping):
            raise ConfigError("field 'giftTiers' harus berupa objek")

        tiers: dict[str, tuple[str, ...]] = {}
        for tier, nama in tiers_raw.items():
            if not isinstance(nama, (list, tuple)):
                raise ConfigError(f"giftTiers.{tier} harus berupa daftar nama gift")
            bersih = tuple(str(item).strip().lower() for item in nama if str(item).strip())
            tiers[str(tier).strip().lower()] = bersih

        eggs_raw = _ambil(data, "easterEggs", "easter_eggs", default={})
        if not isinstance(eggs_raw, Mapping):
            raise ConfigError("field 'easterEggs' harus berupa objek")
        eggs: dict[str, str] = {}
        for kata, merek in eggs_raw.items():
            kunci = re.sub(r"\s+", " ", str(kata).strip().lower())
            nama = re.sub(r"\s+", " ", str(merek).strip().upper())
            if kunci and nama:
                eggs[kunci] = nama

        durasi_raw = _ambil(overlay_raw, "durations", default={})
        if not isinstance(durasi_raw, Mapping):
            raise ConfigError("field 'overlay.durations' harus berupa objek")
        durasi: dict[str, int] = {}
        for scene, ms in durasi_raw.items():
            kunci = str(scene).strip().lower()
            if kunci not in _SCENES:
                raise ConfigError(f"overlay.durations.{scene} bukan scene yang dikenal")
            if isinstance(ms, bool) or not isinstance(ms, int) or ms <= 0:
                raise ConfigError(f"overlay.durations.{scene} harus bilangan bulat positif (ms)")
            durasi[kunci] = ms

        stage = str(_ambil(overlay_raw, "stage", default="full")).strip().lower()
        if stage not in _STAGES:
            raise ConfigError("overlay.stage harus 'full' atau 'split'")

        return cls(
            app_name=str(_ambil(data, "appName", "app_name", default="alkaff-live-bridge")),
            session_ttl_seconds=_bilangan(
                data, "sessionTtlSeconds", "session_ttl_seconds", default=60
            ),
            session_extension_seconds=_bilangan(
                data,
                "sessionExtensionSeconds",
                "session_extension_seconds",
                default=15,
            ),
            max_quotes_per_minute=_bilangan(
                data, "maxQuotesPerMinute", "max_quotes_per_minute", default=20
            ),
            overlay=OverlayConfig(
                width=_bilangan(overlay_raw, "width", default=1920),
                height=_bilangan(overlay_raw, "height", default=1080),
                transparent=bool(_ambil(overlay_raw, "transparent", default=True)),
                voice=bool(_ambil(overlay_raw, "voice", default=True)),
                sfx=bool(_ambil(overlay_raw, "sfx", default=True)),
                stage=stage,
                durations=durasi,
            ),
            gift_tiers=tiers,
            easter_eggs=eggs,
            recap_every=_bilangan(data, "recapEvery", "recap_every", default=5),
            quote_keyword=str(
                _ambil(demo_raw, "quoteKeyword", "quote_keyword", default="QUOTE")
            ).strip().upper(),
            quote_base_url=str(
                _ambil(
                    demo_raw,
                    "quoteBaseUrl",
                    "quote_base_url",
                    default="https://contoh.invalid/quote",
                )
            ).strip(),
            themes_csv=str(
                _ambil(data, "themesCsv", "themes_csv", default="")
            ).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Kembalikan bentuk JSON (camelCase) agar bisa ditulis ulang."""
        return {
            "appName": self.app_name,
            "sessionTtlSeconds": self.session_ttl_seconds,
            "sessionExtensionSeconds": self.session_extension_seconds,
            "maxQuotesPerMinute": self.max_quotes_per_minute,
            "overlay": {
                "width": self.overlay.width,
                "height": self.overlay.height,
                "transparent": self.overlay.transparent,
                "voice": self.overlay.voice,
                "sfx": self.overlay.sfx,
                "stage": self.overlay.stage,
                "durations": dict(self.overlay.durations),
            },
            "giftTiers": {k: list(v) for k, v in self.gift_tiers.items()},
            "easterEggs": dict(self.easter_eggs),
            "recapEvery": self.recap_every,
            "demo": {
                "quoteKeyword": self.quote_keyword,
                "quoteBaseUrl": self.quote_base_url,
            },
            "themesCsv": self.themes_csv,
        }


def load_config(source: Mapping[str, Any] | str | Path | None = None) -> Config:
    """Muat Config dari mapping, path file JSON, atau ``None`` untuk default."""
    if source is None:
        return Config()
    if isinstance(source, Mapping):
        return Config.from_mapping(source)

    path = Path(source).expanduser()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"tidak dapat membaca konfigurasi {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"JSON konfigurasi {path} tidak valid: {exc}") from exc
    return Config.from_mapping(data)


def _ambil(data: Mapping[str, Any], *kunci: str, default: Any = None) -> Any:
    for kunci_item in kunci:
        if kunci_item in data:
            return data[kunci_item]
    return default


def _bilangan(data: Mapping[str, Any], *kunci: str, default: int) -> int:
    nilai = _ambil(data, *kunci, default=default)
    if isinstance(nilai, bool) or not isinstance(nilai, int) or nilai <= 0:
        raise ConfigError(f"{kunci[0]} harus berupa bilangan bulat positif")
    return nilai


def _tolak_kredensial(data: Mapping[str, Any], jalur: str = "") -> None:
    """Tolak field yang menyerupai kredensial, termasuk di dalam nested object."""
    for kunci, nilai in data.items():
        nama = str(kunci)
        lokasi = f"{jalur}.{nama}" if jalur else nama
        if _POLA_KREDENSIAL.search(nama):
            raise ConfigError(
                f"field '{lokasi}' dilarang: kerangka ini tidak menyimpan kredensial/token"
            )
        if isinstance(nilai, Mapping):
            _tolak_kredensial(nilai, lokasi)
