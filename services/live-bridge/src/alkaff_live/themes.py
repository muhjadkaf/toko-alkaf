"""Pemuat tema layanan dari CSV basis pengetahuan parfum.

Modul ini hanya membaca data. Tema dipakai untuk memilih kosakata narasi dan
keyword CTA yang sudah ada di ``05_tema_layanan.csv``, sehingga overlay tidak
mengarang notes, harga, atau klaim. File ini tidak mengubah CSV sumber.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

# services/live-bridge/src/alkaff_live/themes.py -> akar repo.
_AKAR = Path(__file__).resolve().parents[4]
_CSV_DEFAULT = _AKAR / "data" / "pengetahuan-parfum" / "05_tema_layanan.csv"
_STOP = frozenset({"parfum", "aroma", "wangi", "produk", "pilihan", "dong", "kak"})


@dataclass(frozen=True)
class Theme:
    """Satu baris tema layanan yang sudah dinormalisasi."""

    nama: str
    persona: str
    trigger: str
    keluarga: str
    notes: str
    referensi: tuple[str, ...]
    cta_keyword: str
    format_konten: str
    momen: str
    caveat: str
    catatan_live: str

    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            "nama": self.nama,
            "persona": self.persona,
            "trigger": self.trigger,
            "keluarga": self.keluarga,
            "notes": self.notes,
            "referensi": list(self.referensi),
            "ctaKeyword": self.cta_keyword,
            "formatKonten": self.format_konten,
            "momen": self.momen,
            "caveat": self.caveat,
            "catatanLive": self.catatan_live,
        }


def _bersih(nilai: object) -> str:
    return re.sub(r"\s+", " ", str(nilai or "").strip())


def _normal(nilai: object) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(nilai).lower())).strip()


def _jalur_csv(path: str | Path | None) -> Path:
    if path is None or not str(path).strip():
        return _CSV_DEFAULT
    calon = Path(path).expanduser()
    if not calon.is_absolute():
        calon = _CSV_DEFAULT.parent / calon
    return calon


def muat_tema(path: str | Path | None = None) -> tuple[Theme, ...]:
    """Baca CSV tema. Mengembalikan tuple kosong bila berkas tidak tersedia."""
    jalur = _jalur_csv(path)
    try:
        dengan = jalur.open("r", encoding="utf-8-sig", newline="")
    except OSError:
        return ()

    hasil: list[Theme] = []
    with dengan:
        for baris in csv.DictReader(dengan):
            nama = _bersih(baris.get("Tema"))
            if not nama:
                continue
            referensi = tuple(
                bagian
                for bagian in (
                    _bersih(item)
                    for item in re.split(r"[·|,]", str(baris.get("Contoh Internal Reference") or ""))
                )
                if bagian
            )
            hasil.append(
                Theme(
                    nama=nama,
                    persona=_bersih(baris.get("Persona")),
                    trigger=_bersih(baris.get("Trigger")),
                    keluarga=_bersih(baris.get("Keluarga")),
                    notes=_bersih(baris.get("Notes Kunci")),
                    referensi=referensi,
                    cta_keyword=_bersih(baris.get("CTA Keyword")).upper() or "QUOTE",
                    format_konten=_bersih(baris.get("Format Konten")),
                    momen=_bersih(baris.get("Momen")),
                    caveat=_bersih(baris.get("Risiko / Caveat")),
                    catatan_live=_bersih(baris.get("Catatan LIVE")),
                )
            )
    return tuple(hasil)


def _skor(
    tema: Theme,
    keyword: str,
    sku: str,
    cta_keyword: str,
) -> int:
    kata = _normal(keyword)
    cta = _normal(cta_keyword)
    nama = _normal(tema.nama)
    cta_tema = _normal(tema.cta_keyword)
    sku_norm = _normal(sku)

    kata_token = {bit for bit in kata.split() if len(bit) >= 3 and bit not in _STOP}
    nama_token = set(nama.split())
    cta_token = set(cta_tema.split())

    skor = 0
    if cta and cta == cta_tema:
        skor += 120
    if sku_norm and any(_normal(ref) == sku_norm for ref in tema.referensi):
        skor += 100
    if kata and kata == cta_tema:
        skor += 90
    if kata and len(kata) >= 3 and (kata in nama or nama in kata):
        skor += 70
    if kata_token & nama_token:
        skor += 45
    if kata and len(kata) >= 3 and (kata in cta_tema or cta_tema in kata):
        skor += 50
    if kata_token & cta_token:
        skor += 30
    for saku in (tema.keluarga, tema.notes, tema.momen, tema.trigger):
        for potong in re.split(r"[,/;]+", saku):
            bersih = _normal(potong)
            if kata_token & set(bersih.split()):
                skor += 20
                break
    return skor


def pilih_tema(
    daftar: tuple[Theme, ...],
    *,
    keyword: str = "",
    sku: str = "",
    variant: str = "",
    tema: str = "",
    cta_keyword: str = "",
) -> Theme | None:
    """Pilih satu tema dengan prioritas: eksplisit → SKU → keyword → default QUOTE.

    Tidak ada tebakan harga atau komposisi; hanya pencocokan tekstual terhadap
    field yang memang ada di CSV.
    """
    if not daftar:
        return None

    diminta = _normal(tema)
    if diminta:
        for item in daftar:
            if _normal(item.nama) == diminta:
                return item
        for item in daftar:
            if diminta in _normal(item.nama):
                return item

    cta_diminta = _normal(cta_keyword)
    if cta_diminta:
        for item in daftar:
            if _normal(item.cta_keyword) == cta_diminta:
                return item

    gabungan_sku = " ".join(bit for bit in (sku, variant) if bit)
    kandidat: list[tuple[int, int, Theme]] = []
    for indeks, item in enumerate(daftar):
        nilai = _skor(item, keyword, gabungan_sku, cta_keyword)
        if nilai:
            kandidat.append((-nilai, indeks, item))
    if kandidat:
        kandidat.sort(key=lambda row: (row[0], row[1]))
        return kandidat[0][2]

    for item in daftar:
        if item.cta_keyword == "QUOTE":
            return item
    return daftar[0]
