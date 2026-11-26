"""Entrypoint demo: baca event JSONL lokal, jalankan pipeline, cetak overlay.

Contoh::

    python3 -m alkaff_live.main --config config/example.json \
        --events examples/events.jsonl --out build

Tidak ada server, tidak ada koneksi TikTok, dan tidak ada pengiriman DM.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterator

if __package__ in (None, ""):
    # Mendukung: python3 src/alkaff_live/main.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alkaff_live.config import ConfigError, load_config
from alkaff_live.events import EventValidationError, normalize_event
from alkaff_live.orchestrator import InvalidTransitionError, Orchestrator, UnknownEventTypeError
from alkaff_live.overlay import OverlayState, build_overlay_state, write_overlay

_AKAR = Path(__file__).resolve().parents[2]


def _baca_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as berkas:
        for nomor, baris in enumerate(berkas, start=1):
            if not baris.strip():
                continue
            try:
                isi = json.loads(baris)
            except json.JSONDecodeError as exc:
                raise ValueError(f"baris {nomor} bukan JSON valid: {exc}") from exc
            if not isinstance(isi, dict):
                raise ValueError(f"baris {nomor} harus berupa objek JSON")
            yield nomor, isi


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Demo lokal pipeline event -> orchestrator -> overlay (tanpa jaringan)."
    )
    parser.add_argument("--config", type=Path, default=_AKAR / "config" / "example.json")
    parser.add_argument("--events", type=Path, default=_AKAR / "examples" / "events.jsonl")
    parser.add_argument("--out", type=Path, default=_AKAR / "build")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Konfigurasi ditolak: {exc}", file=sys.stderr)
        return 2

    orchestrator = Orchestrator(config)
    try:
        for nomor, mentah in _baca_jsonl(args.events):
            event = normalize_event(mentah)
            transisi = orchestrator.apply(event)
            print(
                f"[{nomor:02d}] {event.type:<15} "
                f"{transisi.previous.value} -> {transisi.current.value} "
                f"({transisi.reason})",
                file=sys.stderr,
            )
    except (
        EventValidationError,
        InvalidTransitionError,
        UnknownEventTypeError,
        OSError,
        ValueError,
    ) as exc:
        print(f"Gagal memproses event: {exc}", file=sys.stderr)
        return 2

    state = build_overlay_state(orchestrator.snapshot(), config)
    try:
        jalur_json, jalur_html = write_overlay(state, args.out, config)
    except OSError as exc:
        print(f"Gagal menulis overlay: {exc}", file=sys.stderr)
        return 2

    print(render_state(state))
    print(f"Overlay lokal: {jalur_json} | {jalur_html}", file=sys.stderr)
    return 0


def render_state(state: OverlayState) -> str:
    """Cetak state overlay sebagai JSON; dipisahkan agar mudah dipakai ulang."""
    return json.dumps(state.to_dict(), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
