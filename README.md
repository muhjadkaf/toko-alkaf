# Toko Alkaff — fondasi software, katalog Odoo, dan rencana operasional

Repo publik `muhjadkaf/toko-alkaf` ini mengumpulkan tiga hal:

1. **Fondasi software** untuk operasional Toko Alkaff: addon Odoo dan layanan pendukung (direktori `odoo/` dan `services/`).
2. **Katalog parfum Odoo** hasil olahan nota toko dan riset parfum lokal Indonesia, beserta skrip pembuatnya.
3. **Rencana operasional dan teknis**, terutama dokumentasi interaksi TikTok LIVE dan rencana perbaikan Suite Odoo Namlah.

Seluruh tulisan menggunakan bahasa Indonesia. Dokumen, data, addon Odoo, skeleton layanan LIVE, dan web app Flutter sudah tersedia. Modul `alkaff_catalog` serta 164 produk katalog sudah terpasang di database **`nml`**, dan web app theater sudah dipublish di `https://alkaff.lokal.or.id` untuk OBS screen-share. **Belum ada integrasi ke API TikTok** dan tidak ada auto-DM. Rencana bertahapnya ada di [`ROADMAP.md`](ROADMAP.md).

## Status fondasi

| Bagian | Status |
|---|---|
| `docs/` | Empat dokumen sumber sudah disalin, ditambah [`docs/ARSITEKTUR.md`](docs/ARSITEKTUR.md) |
| `data/katalog-alkaff-odoo/` | XLSX, CSV siap import Odoo, README katalog, dan `tambah_parfum_lokal.py` sudah disalin |
| `data/pengetahuan-parfum/` | Basis pengetahuan turunan: 14 keluarga, 135 notes, 78 deskriptor, 56 accord, 40 tema, 70 frasa sensorik, 18 pagar klaim |
| `odoo/addons/alkaff_catalog/` | Addon Odoo 20: kategori, field aroma/notes, log, wizard import CSV, dan API baca-saja; sudah di-install di `nml` |
| `odoo/addons/alkaff_custom_request/` | Addon Odoo 20 terpisah untuk draft custom/rebrand; tanpa harga/supplier/publish otomatis; sudah di-install hanya di `nml` |
| `webapp/alkaff_scent_lab/` | Flutter Web Clean Lab dengan dunia pabrik maklon “Alkaff Maklon Hall”, narasi audio, bus kontrol, botol reward, dan QR 3 detik; dipublish di `alkaf.lokal.or.id` / `alkaff.lokal.or.id` |
| `services/live-bridge/` | Skeleton Python stdlib: normalisasi event, state machine, dedupe, dan overlay lokal (34 tes lulus) |
| Interaksi TikTok LIVE | Punya rencana teknis + skeleton lokal; **belum terhubung ke API TikTok**, tanpa auto-DM |
| Katalog parfum | 164 produk di sheet `IMPORT_odoo`; 42 `Sales Price` terisi dan 122 sengaja dikosongkan |

Angka di atas bersumber dari [`data/katalog-alkaff-odoo/README.md`](data/katalog-alkaff-odoo/README.md). Harga pada katalog adalah harga pembelian historis dari nota atau harga eceran referensi, **bukan harga jual final Toko Alkaff**.

## Struktur direktori

| Path | Isi |
|---|---|
| `README.md` | Penjelasan repo, struktur, quickstart, status, dan peringatan privasi (file ini) |
| `ROADMAP.md` | Rencana Fase 0–5: fondasi, katalog, event ingest, orchestrator/overlay, integrasi Odoo/DM, hardening |
| `docs/` | Dokumentasi LIVE TikTok, arsitektur, rencana perbaikan Odoo Namlah, dan catatan riset Biharul Anwar |
| `data/` | Data katalog parfum untuk Odoo, termasuk file XLSX/CSV dan skrip pembuatnya; lihat [`data/pengetahuan-parfum/README.md`](data/pengetahuan-parfum/README.md) untuk kosakata, resep, dan tema layanan |
| `odoo/` | Addon Odoo untuk operasional toko; lihat [`odoo/addons/alkaff_catalog/README.md`](odoo/addons/alkaff_catalog/README.md) |
| `webapp/` | Aplikasi Flutter Web untuk OBS screen-share; lihat [`webapp/alkaff_scent_lab/README.md`](webapp/alkaff_scent_lab/README.md) |
| `services/` | Layanan pendukung; lihat [`services/live-bridge/README.md`](services/live-bridge/README.md). Quotation/DM gateway masih rencana, bukan kode |

Isi `docs/`:

- [`DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md`](docs/DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md) — rencana teknis interaktif TikTok LIVE: event LIVE, state machine, overlay OBS, quotation, dan batasan DM.
- [`ARSITEKTUR.md`](docs/ARSITEKTUR.md) — ringkasan arsitektur tiga layer dan alur import katalog.
- [`RENCANA-PERBAIKAN-NAMLAH.md`](docs/RENCANA-PERBAIKAN-NAMLAH.md) — rencana perbaikan multi-agen untuk Suite Odoo Namlah (keamanan, tes/CI, isolasi tenant, dokumentasi).
- [`biharul-anwar-daftar-jilid.md`](docs/biharul-anwar-daftar-jilid.md) dan [`biharul-anwar-tema-penciptaan.md`](docs/biharul-anwar-tema-penciptaan.md) — daftar jilid dan indeks tema dari Ahlulbayt Library.

## Quickstart

### 1. Membaca dokumentasi LIVE

Mulai dari [`docs/DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md`](docs/DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md) untuk requirement, batasan platform, skema event, state machine, dan runbook go-live. Ringkasannya ada di [`docs/ARSITEKTUR.md`](docs/ARSITEKTUR.md). Keduanya adalah **rencana**, bukan kode yang bisa dijalankan.

### 2. Mengimport katalog ke Odoo

1. Baca dulu [`data/katalog-alkaff-odoo/README.md`](data/katalog-alkaff-odoo/README.md).
2. Pastikan kategori produk sudah ada, atau saat import centang **Create missing values** untuk *Product Category* (termasuk `Parfum / Lokal Indonesia` dan `Bahan Baku / Bibit Parfum`).
3. Buka **Sales → Products → Products → Import** dan unggah `data/katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv` (UTF-8 BOM) atau file XLSX-nya.
4. Tinjau ulang `Sales Price` sebelum produk dijual; isi manual bila masih kosong. `Description` juga perlu ditinjau sebelum dipakai sebagai klaim penjualan.
5. Jangan mencampur `Cost Price` per gram dan per kemasan; basisnya ada di kolom `Basis Harga` pada sheet `Detail_Harga_Sumber`. Untuk produk lokal, `Cost Price` sengaja kosong sampai harga supplier dikonfirmasi.

Detail validasi supplier ada pada sheet `Supplier_Lokal` di XLSX; baca catatan verifikasinya sebelum melakukan order.

### 3. Memakai basis pengetahuan parfum

Baca [`data/pengetahuan-parfum/README.md`](data/pengetahuan-parfum/README.md).
Data ini memakai `Internal Reference` katalog sebagai kunci gabung, jadi bisa
dipakai untuk rekomendasi tema, copywriting, dan konten edukasi tanpa mengubah
CSV import Odoo. Perbarui data dengan:

```bash
python3 data/pengetahuan-parfum/build_kb.py
```

Resep accord dan angka ketahanan bersifat edukatif, bukan formula produksi atau
klaim produk. Riset lanjutan (perbendaharaan aroma, merek/karakter, kosakata
marketing, dan audit katalog) ada di
[`data/pengetahuan-parfum/research/`](data/pengetahuan-parfum/research/);
semuanya memakai URL sumber, tanggal akses `2026-11-27`, dan status verifikasi.
Setelah ditinjau, hanya frasa sensorik dan pagar klaim yang dipromosikan menjadi
CSV/JSON; keputusan lengkapnya ada di
[`research/05_keputusan_tinjauan.md`](data/pengetahuan-parfum/research/05_keputusan_tinjauan.md).
Arketipe, ide positioning, usulan tema, dan perbaikan katalog tetap usulan.

### 4. Menjalankan skeleton yang sudah ada

**Addon Odoo** (Odoo 20, lisensi LGPL-3):

1. Arahkan `addons_path` ke `odoo/addons/`, restart Odoo, lalu *Update Modules List*.
2. Install **Alkaff Catalog — Fondasi Import Parfum** pada **database uji**.
3. Buka **Alkaff → Import Katalog Parfum**, unggah `data/katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv`.
4. Import idempoten berdasarkan `Internal Reference`; lihat [`odoo/addons/alkaff_catalog/docs/IMPORT_MAPPING.md`](odoo/addons/alkaff_catalog/docs/IMPORT_MAPPING.md).

**Skeleton LIVE** (Python 3.10+, stdlib saja):

```bash
cd services/live-bridge
python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m alkaff_live.main \
  --config config/example.json --events examples/events-theater.jsonl --out build
```

Demo menghasilkan `build/overlay.json` dan `build/overlay.html` (transparan, bisa dibuka sebagai OBS Browser Source lokal). `events-theater.jsonl` memperlihatkan lima klien, kasta botol, easter egg, dan papan recap; `events.jsonl` berisi alur singkat. Narasi dan CTA kini memakai tema dari `05_tema_layanan.csv` (misalnya keyword `kopi` → `DM COFFEE`), bukan notes statis. Ini **bukan** koneksi TikTok: tidak ada WebSocket, HTTP, auto-DM, atau kredensial. Rincian kontrak ada di [`services/live-bridge/docs/EVENT_CONTRACT.md`](services/live-bridge/docs/EVENT_CONTRACT.md).

Dua demo visual mandiri juga tersedia:

- [`services/live-bridge/overlay-demo/`](services/live-bridge/overlay-demo/) — Dark Emerald Atelier.
- [`services/live-bridge/overlay-demo-clean-lab/`](services/live-bridge/overlay-demo-clean-lab/) — **Virtual Clean Lab / Interactive Scent Theater**: lima babak sinematik 20 detik per klien, mode `full` atau `split` (40% atas untuk kamera host), kabut, lens flare, SFX sintesis, kasta botol, easter egg, dan recap lima merek. Teks hanya menempel pada objek fisik (layar monitor, label botol/vial, plakat meja, panel mesin); tidak ada teks mengambang. Buka `preview.html` untuk pratinjau, atau `index.html?obs=1` untuk OBS.

### 5. Memakai web app Flutter untuk OBS

Buka `https://alkaff.lokal.or.id/?controls=1&keyword=kopi%20dingin` saat menyiapkan host, lalu
`https://alkaff.lokal.or.id/?keyword=kopi%20dingin` saat LIVE. Aplikasi mengambil tema dan produk
langsung dari `/alkaff/api/recommendations` di Odoo `nml`; hasil build Flutter tidak di-commit.
Theater menampilkan **Alkaff Maklon Hall**, visualisasi pabrik maklon skala besar berupa lima plate
CG + parallax: penerimaan bahan, pencampuran, QC, dan finishing. Ruangnya memakai tekstur nyata
(dinding beton, lantai epoksi, stainless brushed, kayu hangat), rak botol kaca amber, tangki
berjaket, drum, pipa/gauge, meja QC dengan vial/pipet/suntikan realistik, dan conveyor—bukan garis
atau kotak generik. Teks hanya menempel pada benda fisik, tanpa sosok manusia, dan narasi disiarkan
sebagai audio bahasa Indonesia tanpa subtitle. Konsol Sarang Semut bisa memilih tiga mode presenter:
`host` (CG jadi latar, mic host dari OBS), `robot` (operator menyuruh robot bicara/bergerak), atau
`autopilot` (robot mengikuti script lima adegan). Rujukan visual multi-agen (butik parfum, peralatan
maklon, lisensi foto) tercatat di
[`webapp/alkaff_scent_lab/docs/REFERENSI-VISUAL.md`](webapp/alkaff_scent_lab/docs/REFERENSI-VISUAL.md);
foto internet hanya dipakai sebagai referensi, bukan disalin ke repo.

Plate dan narasi bisa dibuat ulang dengan `tools/generate_world_plates.py`,
`tools/texture_utils.py`, dan `tools/generate_narration.py` di folder webapp. Build memakai
`build_web.sh` dengan nomor build unik; aset dan loader diberi query `?v=<build>` sehingga
tablet Opera maupun PC otomatis mengambil versi baru tanpa hard refresh.

Di OBS cukup pakai **Window Capture** pada jendela browser. Opsi `?mode=split` menyediakan zona
kamera host di 40% atas. Menu **Alkaff Live Console** di superapp `https://app.lokal.or.id`
menyediakan chat simulasi dan tombol sutradara adegan lewat bus kontrol bersama,
tanpa iframe; theater dibuka terpisah di `https://alkaf.lokal.or.id` (alias
`https://alkaff.lokal.or.id`) dengan channel yang sama. Perintah manual menghentikan
auto-sequence sampai host menekan `Auto` atau mengubah keyword.
Detail build, query string, generator aset, protokol pesan, dan pagar klaim ada di
[`webapp/alkaff_scent_lab/README.md`](webapp/alkaff_scent_lab/README.md).

Reward poin → QR `/a/<token>` → produk allowlist dan jalur custom → draft admin
dijelaskan di
[`docs/ALKAFF-REWARD-QR-DRAFT.md`](docs/ALKAFF-REWARD-QR-DRAFT.md). QR memakai
token opaque TTL 24 jam, replay maksimal 2, bisa dicabut, dan tidak memakai
`/q/<kode>`. `custom_draft` tidak punya QR, harga, atau janji produk jadi; nama
penonton hanya dipakai sebagai label setelah opt-in dan approval admin.
Token admin hanya dari environment `NAMLAH_WEB_ADMIN_TOKEN`, bukan repo.

Sebelum produksi, tetap ikuti dokumentasi LIVE: endpoint `/internal/*` wajib dilindungi, token disimpan di secret manager, dan uji memakai akun TikTok uji dengan moderator manual.

## Peringatan: repo ini publik

`data/` mengandung informasi sensitif:

- Sheet `Supplier_Lokal` memuat 12 baris data brand owner/produsen atau distributor, badan hukum, alamat, kota, telepon/WhatsApp, email, website, kanal pembelian, sertifikasi, dan catatan untuk Alkaff.
- Sheet detail dan CSV memuat **harga pembelian historis** dari nota toko serta catatan sumber harga.

Data tersebut berasal dari sumber publik/historis dan perlu **ditinjau ulang sebelum dipublikasikan lebih luas** atau dipakai untuk transaksi. Verifikasi ulang alamat, kontak, MOQ, stok, sertifikasi, dan harga per SKU sebelum kerja sama. Jangan menyimpan token, kata sandi, atau kredensial lain di repo; gunakan variabel lingkungan/secret manager.

## Sumber

- [`docs/DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md`](docs/DOKUMENTASI-LIVE-TIKTOK-ALKAFF.md) — versi 1.0, 2026-11-26.
- [`docs/RENCANA-PERBAIKAN-NAMLAH.md`](docs/RENCANA-PERBAIKAN-NAMLAH.md) — baseline dan rencana perbaikan, 2026-11-26.
- [`data/katalog-alkaff-odoo/README.md`](data/katalog-alkaff-odoo/README.md) — ringkasan katalog, 2026-11-26.
