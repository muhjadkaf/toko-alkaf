# Basis Pengetahuan Parfum Alkaff

Direktori ini berisi **data turunan** yang memperluas katalog 164 produk di
[`../katalog-alkaff-odoo/`](../katalog-alkaff-odoo/) menjadi kosakata, resep
accord edukatif, dan ide tema layanan aplikasi. Data dibuat dari deskripsi dan
`Internal Reference` katalog, **tanpa mengubah CSV import Odoo**.

Dibuat 2026-11-26. Generator: [`build_kb.py`](build_kb.py).

## Isi file

| File | Jumlah | Fungsi |
|---|---:|---|
| [`01_keluarga_aroma.csv`](01_keluarga_aroma.csv) | 14 keluarga | Pengelompokan aroma + karakter, momen, ketahanan umum, sillage, tema konten, contoh produk |
| [`02_taksonomi_notes.csv`](02_taksonomi_notes.csv) | 56 notes | Layer (top/heart/base), intensitas 1–5, ketahanan, alias Indonesia, pasangan umum, contoh produk |
| [`03_kosakata_deskriptor.csv`](03_kosakata_deskriptor.csv) | 55 deskriptor | kosakata copywriting Indonesia–English beserta dimensi dan contoh kalimat |
| [`04_resep_accord.csv`](04_resep_accord.csv) | 24 accord | Ide kombinasi notes dengan rasio bagian, karakter, momen, maturasi, dan catatan keamanan |
| [`05_tema_layanan.csv`](05_tema_layanan.csv) | 24 tema | Persona, trigger, notes kunci, keyword CTA, format konten, risiko, dan contoh produk |
| [`pengetahuan-parfum.json`](pengetahuan-parfum.json) | bundle | Semua tabel di atas dalam satu JSON untuk dikonsumsi aplikasi |

## Cara memperbarui

```bash
python3 data/pengetahuan-parfum/build_kb.py
```

Generator membaca `data/katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv`,
lalu menimpa seluruh CSV/JSON di direktori ini. Generator juga memvalidasi semua
`Internal Reference` yang dipakai sebagai contoh; jika ada referensi yang tidak
ada di katalog, proses berhenti dengan error.

## Cara menggabungkan dengan katalog

Gunakan `Internal Reference` sebagai kunci gabung (`join`):

```python
import csv

katalog = {
    r["Internal Reference"]: r
    for r in csv.DictReader(
        open("data/katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv", encoding="utf-8-sig")
    )
}
tema = list(csv.DictReader(
    open("data/pengetahuan-parfum/05_tema_layanan.csv", encoding="utf-8")
))

for t in tema:
    refs = [x.strip() for x in t["Contoh Internal Reference"].split("·") if x.strip() in katalog]
    print(t["Tema"], [(ref, katalog[ref]["Name"]) for ref in refs])
```

Kolom `Contoh Internal Reference` memakai pemisah ` · ` dan diisi dari produk
yang benar-benar ada di katalog. Produk difilter ulang berdasarkan kecocokan
notes, keluarga, dan status harga terverifikasi; referensi tidak diarang.

## Contoh pemakaian untuk tema aplikasi

- **Rekomendasi cepat:** pilih tema dari `05_tema_layanan.csv` berdasarkan
  persona/momen, lalu ambil 3–6 produk dari kolom contoh reference.
- **Copywriting:** ambil deskriptor dari `03_kosakata_deskriptor.csv` dan
  karakter keluarga dari `01_keluarga_aroma.csv`.
- **Edukasi racik:** tampilkan `04_resep_accord.csv` sebagai inspirasi, bukan
  formula produksi; sertakan `Catatan Keamanan`.
- **Filter LIVE:** tema dengan CTA harus memakai alur viewer-initiated. Jangan
  mengirim DM otomatis; lihat
  [`docs/DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md`](../../docs/DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md).

## Batasan penting

- Notes, keluarga, dan accord bersifat **edukatif/inspiratif**. Ini adalah
  gambaran aroma berdasarkan teks katalog, **bukan komposisi resmi pabrik**.
- Rasio pada `04_resep_accord.csv` adalah ide untuk konten/workshop, **bukan
  formula produksi**, standar IFRA, atau resep siap pakai.
- Angka ketahanan dan sillage adalah perkiraan umum, bukan hasil uji lab dan
  bukan klaim kosmetik/obat. Hindari klaim tahan 24 jam, bebas alergi,
  menghangatkan tubuh, afrodisiak, atau kehalalan tanpa bukti/sertifikasi.
- Harga tidak disalin ke basis pengetahuan ini. Cek `Sales Price` di katalog:
  kolom kosong berarti harga belum terverifikasi dan tidak boleh ditampilkan
  sebagai harga jual.
- Cek stok, harga, dan sertifikasi sebelum mempromosikan produk.
