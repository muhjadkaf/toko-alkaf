# Riset Pendukung Perbendaharaan Parfum

Direktori ini memuat hasil riset multi-agent yang dipakai untuk memperluas
perbendaharaan aroma, merek, dan karakter marketing parfum. File di sini adalah
**bahan baku bersumber**, bukan data import Odoo dan bukan klaim resmi pabrik.

| File | Fokus | Status |
|---|---|---|
| [`01_perbendaharaan_aroma.md`](01_perbendaharaan_aroma.md) | 45 note + 20 accord baru di luar taksonomi existing | Riset agent; 37 note + 16 accord diserap ke `build_kb.py` |
| [`02_merek_karakter.md`](02_merek_karakter.md) | 24 merek + 8 pola positioning + 10 ide pembeda | Riset agent; usulan internal |
| [`03_karakter_marketing.md`](03_karakter_marketing.md) | 10 arketipe, 70 frasa, 18 aturan klaim aman | Riset agent; 70 frasa + 18 pagar klaim diserap ke `build_kb.py` |
| [`04_audit_katalog_gap.md`](04_audit_katalog_gap.md) | Audit 164 produk, 20 kandidat, 8 klaster | Riset agent; dasar evaluasi, bukan perubahan katalog |
| [`05_keputusan_tinjauan.md`](05_keputusan_tinjauan.md) | Keputusan tinjauan `02`–`04` | Catatan internal; menentukan mana yang dipromosikan/ditunda/ditolak |

Setiap laporan memakai URL sumber dan tanggal akses `2026-11-27`. Beberapa agent
menulis draf dengan path yang sama; versi final di atas yang dipertahankan dan
menjadi rujukan konsolidasi.

## Baca sebagai

- **Edukasi/konten:** `01`, `03`, dan turunannya `06_frasa_sensorik.csv` / `07_pagar_klaim.csv`.
- **Inspirasi positioning (usulan):** `02`.
- **Keputusan produk/narasi LIVE:** baca `05` dulu, lalu `04` + CSV di direktori induk.

## Batasan

- Sumber publik dicantumkan dengan URL; bila tidak ada sumber kuat, statusnya
  ditandai **perlu verifikasi**.
- Tidak ada harga jual, supplier, atau klaim komposisi resmi.
- Rasio accord adalah ide edukatif, bukan formula produksi atau standar IFRA.
- Klaim ketahanan, sillage, kehalalan, dan keamanan tetap mengikuti batasan di
  [`../README.md`](../README.md).
- File turunan final tetap dibuat oleh `../build_kb.py`; riset ini tidak
  mengubah CSV katalog Odoo.
