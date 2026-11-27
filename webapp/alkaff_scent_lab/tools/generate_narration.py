#!/usr/bin/env python3
"""Buat narasi bahasa Indonesia untuk kelima adegan (gTTS).

Tidak ada klaim medis/kosmetik/formula produksi, halal, bebas alergi, dan
sejenisnya. Teks ini hanya narasi visualisasi proses maklon.
"""
from __future__ import annotations

import os

from gtts import gTTS

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "audio"))
os.makedirs(OUT, exist_ok=True)

NARRATION = {
    "boot": (
        "Selamat datang di Alkaff Scent Lab. Visualisasi ini menunjukkan alur "
        "maklon parfum dari penerimaan bahan hingga pengemasan."
    ),
    "scan": (
        "Penerimaan bahan dimulai dari pemeriksaan kode dan kondisi kemasan. "
        "Setiap batch dicatat agar dapat ditelusuri."
    ),
    "mix": (
        "Di ruang pencampuran, tangki berjaket dan pengaduk bekerja dengan "
        "kendali suhu. Skala ini menggambarkan kapasitas produksi."
    ),
    "analyze": (
        "Pemeriksaan mutu dilakukan sebelum proses lanjut. Fokusnya adalah "
        "konsistensi keluarga aroma dan kesesuaian dokumen."
    ),
    "result": (
        "Botol diberi label, lalu dikemas. Rekomendasi yang Anda lihat berasal "
        "dari katalog Alkaff. CTA dimulai dari penonton."
    ),
}


def main():
    for scene, text in NARRATION.items():
        path = os.path.join(OUT, "narasi_%s.mp3" % scene)
        gTTS(text=text, lang="id", slow=False).save(path)
        print("WROTE", path)


if __name__ == "__main__":
    main()
