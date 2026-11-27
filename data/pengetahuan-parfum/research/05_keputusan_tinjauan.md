# Keputusan Tinjauan Laporan `02`–`04` — Basis Pengetahuan Alkaff

**Disusun:** 2026-11-27  
**Ruang lingkup:** `02_merek_karakter.md`, `03_karakter_marketing.md`, `04_audit_katalog_gap.md`.  
**Sifat:** catatan keputusan internal. Bukan data impor Odoo, bukan dokumen resmi pabrik, bukan nasihat hukum, dan bukan pengumuman positioning publik. Semua URL pada laporan yang ditinjau diakses pada **2026-11-27**; status verifikasi mengikuti laporan asalnya.

## 1. Ringkasan keputusan

| Kelompok | Keputusan | Alasan singkat | Dampak ke generator |
|---|---|---|---|
| 70 frasa sensorik (`03` §3) | **Dipromosikan** | Kalimat 2–8 kata, berupa gambaran indrawi/suasana; tidak berisi komposisi, angka performa, atau efek tubuh. | CSV baru `06_frasa_sensorik.csv` + kunci `frasa` pada bundle JSON. |
| 18 alternatif klaim aman (`03` §4) | **Dipromosikan** | Berfungsi sebagai pagar sebelum tayang, bukan janji produk. Sumber regulasi/platform tercantum dengan status verifikasi. | CSV baru `07_pagar_klaim.csv` + kunci `pagarKlaim` pada bundle JSON. |
| 10 arketipe (`03` §2) | **Dipakai terbatas** | Hanya sebagai label pengelompokan frasa; laporan sendiri menyatakan ini interpretasi internal, bukan taksonomi resmi atau segmen demografi. | Kolom `Arketipe (alat bercerita)` pada `06_frasa_sensorik.csv`, dengan kolom `Batasan`. |
| 24 merek + 8 pola positioning (`02` §1–2) | **Tetap riset** | Observasi publik atas merek lain; bukan afiliasi, endorse, atau resep identitas Alkaff. | Tidak diubah menjadi tema/klaim. |
| 10 ide pembeda (`02` §3) | **Tetap usulan**, kecuali prinsip kejujuran deskripsi | Sebagian besar bergantung pada stok, `Sales Price`, sertifikat, atau keputusan redaksi. | Prinsip kejujuran masuk `07_pagar_klaim.csv`; sisanya tidak menambah tema. |
| 12 usulan tema pengaya (`03` §5) | **Ditolak untuk tayang saat ini** | Masih usulan; sebagian berisiko menjadi klaim efek/psikologis bila dibingkai keliru. Tidak ada verifikasi stok/harga. | `05_tema_layanan.csv` tetap 40 tema; tidak ada CTA baru. |
| Temuan audit (`04` §4–5) | **Ditunda / backlog data** | Katalog Odoo tidak diubah. Mengisi celah dengan notes karangan justru melanggar pagar klaim. | Tidak ada perbaikan otomatis pada CSV katalog. |

## 2. Keputusan per laporan

### 2.1 `02_merek_karakter.md` — merek, pola, ide pembeda

- **24 merek:** tetap sebagai referensi bahasa. Tiga berstatus `Perlu verifikasi` (Tom Ford, Kilian Paris, Parfums de Marly) **tidak** boleh dibaca sebagai afiliasi, distributorship, atau endorse Alkaff. Kosakata seperti *premium/luxury* adalah kutipan merek lain, bukan janji harga atau mutu produk Alkaff.
- **8 pola positioning:** tetap observasi. Pola proyeksi (`dekat kulit → seimbang → menyapa ruang`) boleh dipakai sebagai cara membaca deskriptor, tetapi **tidak** boleh diubah menjadi label konsentrasi EDT/EDP/extrait atau bukti ketahanan.
- **10 ide pembeda:**

| # | Ide | Keputusan | Catatan pagar |
|---:|---|---|---|
| 1 | Satu botol, tiga momen | Tetap usulan | Sudah diwakili tema `Signature Scent`/`Bundle 3 Momen`; jangan klaim aroma unik. |
| 2 | Peta proyeksi | Tetap usulan | Pakai deskriptor; tanpa angka jam/meter; proyeksi ≠ ketahanan. |
| 3 | Kamus aroma Nusantara | Tetap usulan | Klaim asal-usul butuh data; teh tidak boleh diklaim detoks. |
| 4 | Attar sebagai warisan, bukan suci | Tetap usulan | Halal hanya dengan sertifikat yang bisa ditunjuk. |
| 5 | Ritual hujan–kopi–vanila | Tetap usulan | Tema `HUJAN`, `COFFEE`, `VANILLA` sudah ada; tanpa klaim energi/menghangatkan tubuh. |
| 6 | Laundry vs parfum kulit | Dipertahankan sebagai aturan | Tema `Parfum Laundry Wangi` sudah membawa caveat kategori. |
| 7 | Live 15 detik + CTA viewer-initiated | Dipertahankan | Sudah ada di kontrak LIVE dan overlay; tidak ada auto-DM. |
| 8 | Workshop racik sebagai edukasi | Dipertahankan pada batas existing | Accord tetap inspirasi, bukan formula/standar IFRA. |
| 9 | Kartu hadiah berpersona | Tetap usulan | Cek stok dan harga; hindari janji romantis/afrodisiak. |
| 10 | Label kejujuran deskripsi | **Dipromosikan** | Masuk pagar klaim: notes = gambaran keluarga; harga hanya bila terverifikasi. |

### 2.2 `03_karakter_marketing.md` — arketipe, frasa, pagar klaim, usulan tema

- **10 arketipe:** dipakai hanya sebagai pengelompokan pada `06_frasa_sensorik.csv`. Tidak dijadikan persona komersial resmi, klaim demografi, atau janji hasil.
- **70 frasa:** seluruhnya dipromosikan. Status `BARU` dan kolom `Mirip Deskriptor` disalin apa adanya; kolom `Batasan` ditambahkan generator.
- **18 alternatif klaim aman:** dipromosikan sebagai `07_pagar_klaim.csv` dengan URL, tanggal akses, dan status verifikasi. Ini daftar larangan/pengganti kata, **bukan** daftar klaim yang boleh dikatakan tanpa bukti.
- **12 usulan tema pengaya:** **tidak dipromosikan.** Termasuk yang terdengar aman (`Jarak Dekat Kulit`, `Jeda Ritual`, `Uji Kecil di Kulit Sendiri`) tetap menunggu keputusan redaksi dan pagar klaim. Khususnya `Warisan Keluarga` (asal-usul/halal), `Hadiah untuk Diri Sendiri` (klaim efek psikologis), dan `Layering Dua Aroma` (bisa disalahartikan sebagai komposisi resmi) berisiko bila dipadatkan jadi CTA publik.
- **Sumber regulasi (S6–S15):** dipakai untuk menolak klaim, bukan untuk membenarkan mutu produk. Platform (S10, S11) menguatkan aturan viewer-initiated.

### 2.3 `04_audit_katalog_gap.md` — audit dan celah

| Temuan | Keputusan |
|---|---|
| 39 deskripsi `Aromatic Blend` identik | **Ditolak untuk storytelling.** Jangan mengarang notes pengganti; tunggu data dari sumber resmi/staf. |
| 46 deskripsi `ALK-L-` tanpa disclaimer | Backlog katalog. Generator tidak menyunting CSV Odoo; overlay sudah memakai disclaimer keluarga. |
| 76/164 produk belum jadi contoh tema | Backlog pemetaan. Tidak menambah tema otomatis, karena sebagian besar berada pada klaster generik H. |
| 27/78 deskriptor tak muncul literal | Sebagian terbantu oleh frasa baru (mis. `Dekat Kulit`, `Kayu Krim`, `Teh`, `Restock`); sisanya tetap kosakata cadangan. |
| 8 klaster naratif | Alat baca audit, bukan klasifikasi produk baru di basis pengetahuan. |
| 20 kandidat storytelling | Daftar awal internal saja. Tidak dipindah ke CSV karena bergantung pada verifikasi notes resmi, stok, harga, lisensi/sertifikat, dan sensitivitas nama merek pihak ketiga. |
| 122/164 `Sales Price` kosong | Harga kosong tetap kosong; tidak ada angka yang ditambahkan ke basis pengetahuan maupun CTA. |

## 3. Batas yang tidak berubah

- Tidak ada klaim tahan 24 jam, bebas alergi, afrodisiak, menghangatkan tubuh, detoks, halal tanpa sertifikat, BPOM/IFRA tanpa nomor, atau cocok untuk semua kulit.
- Tidak ada harga, supplier, komposisi resmi, formula produksi, status stok, atau sertifikasi yang dikarang.
- Tidak ada auto-DM: undangan tetap diketik penonton (`CTA Keyword` dari `05_tema_layanan.csv`).
- `build/` hasil demo tetap tidak di-commit.
- Perubahan apa pun pada data hasil generator harus melalui `build_kb.py`, bukan penyuntingan CSV langsung.

## 4. Validasi setelah promosi

1. `python3 data/pengetahuan-parfum/build_kb.py` → 164 produk, 14 keluarga, 135 notes, 78 deskriptor, 56 accord, 40 tema, 70 frasa, 18 pagar klaim; referensi tervalidasi tetap 105.
2. `python3 -m unittest discover -s services/live-bridge/tests` → 34 tes lulus.
3. Demo `services/live-bridge/config/example.json` dengan `events-theater.jsonl` → tema `Parfum Kopi`, CTA `DM COFFEE` tidak berubah.
4. Cek Chromium headless → `COFFEE NOIR`, `ALK-658`, `TEMA · PARFUM KOPI · DM COFFEE` tetap tampil.
