# Audit Katalog & Celah Narasi — 164 Produk Alkaff

**Disusun:** 2026-11-27  
**Lingkup:** `data/katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv` (164 baris) dan basis pengetahuan `data/pengetahuan-parfum/02_taksonomi_notes.csv`, `03_kosakata_deskriptor.csv`, `04_resep_accord.csv`, `05_tema_layanan.csv`.  
**Sifat dokumen:** riset pendukung untuk narasi LIVE/theater. Bukan data import Odoo, bukan dokumen resmi pabrik.

> **Batasan mutlak:** Seluruh `Description` di CSV adalah **gambaran keluarga wewangian**, **bukan komposisi resmi pabrik**, bukan daftar bahan baku terverifikasi, bukan formula produksi, dan bukan klaim medis/kosmetik. Angka ketahanan/sillage di basis pengetahuan bersifat perkiraan edukatif. Harga, supplier, sertifikasi, dan stok **tidak** diambil dari sumber di luar CSV dan tidak ditebak di dokumen ini; bila disebut dalam `Description`, tetap berstatus **perlu verifikasi**.

---

## 1. Ringkasan eksekutif (angka hasil hitungan)

| Indikator | Hasil | Catatan |
|---|---:|---|
| Produk dianalisis | **164** | `Internal Reference` 164/164 unik; `Name` 164/164 unik |
| `Description` berisi label keluarga | **164/164 (100%)** | Pola `— <keluarga>. Notes:` |
| `Description` berisi Notes Top/Heart/Base | **164/164 (100%)** | Ketiga layer hadir pada semua baris |
| `Description` berisi `Karakter:` | **164/164 (100%)** | — |
| `Description` berisi `Cocok untuk:` (audiens) | **164/164 (100%)** | — |
| `Description` berisi `Cocok dipakai:` (padanan momen) | **164/164 (100%)** | Label literal `Momen:` **0/164** di `Description`; namun **164/164** di `Description for E-commerce` |
| Deskripsi dengan catatan disclaimer "notes adalah gambaran keluarga…" | **118/164 (72,0%)** | **46/164 (28,0%)** tidak memuatnya; semuanya ber-`Internal Reference` awalan `ALK-L-` |
| Deskripsi dengan frasa "Terinspirasi aroma …" | **73/164 (44,5%)** | Sisanya tidak punya atribusi inspirasi eksplisit |
| Deskripsi menyebut "live" / "konten live" | **46/164 (28,0%)** | 39 di antaranya adalah blok generik `Aromatic Blend`; hanya **7** di luar blok itu |
| Kombinasi deskripsi identik (keluarga + notes + karakter + audiens + momen) | **39 produk (23,8%)** | Semua ber-label keluarga `Aromatic Blend` dengan teks yang sama persis |
| Label keluarga berbeda | **95** | Dominan: `Aromatic Blend` 39, `Floral Fruity` 6, `Gourmand Vanilla` 5 |
| `Sales Price` terisi | **42/164 (25,6%)** | **122/164 (74,4%)** kosong → tidak boleh ditampilkan sebagai harga jual |
| `Cost Price` terisi | **117/164** | Tidak dipakai untuk narasi konsumen |
| Kategori produk | 6 | `Parfum` 96, `Parfum / Lokal Indonesia` 45, `Parfum / Attar & Oud` 10, `Parfum / Gourmand` 8, `Parfum / Laundry` 4, `Bahan Baku / Bibit Parfum` 1 |

**Temuan utama:** secara struktural katalog sudah lengkap (100% punya notes, karakter, audiens, momen), tetapi **kualitas narasinya tidak merata**: 39 produk identik, 46 produk tanpa disclaimer, 76 produk tidak pernah dipakai sebagai contoh tema, dan 27 dari 78 deskriptor tidak muncul secara literal di deskripsi. Celah terbesar bukan "field kosong", melainkan **duplikasi teks dan miskinnya variasi kosakata**.

---

## 2. Metode hitung (dapat diaudit ulang)

1. CSV dibaca dengan `utf-8-sig`; jumlah baris dihitung dari `csv.DictReader` → 164.
2. Kelengkapan field diukur dengan pencarian pola regex pada `Description`:
   `— (.+?)\. Notes:`, `Notes: (.+?)\. Karakter:`, `Karakter: (.+?)\. Cocok untuk:`, `Cocok untuk: (.+?)\. Cocok dipakai:`, `Cocok dipakai: (.+?)(?=\.|$)`.
3. Duplikasi dihitung dari tupel lima field di atas, bukan dari keseluruhan baris.
4. Cakupan kosakata dihitung dengan **pencocokan kata utuh, case-insensitive** terhadap gabungan 164 `Description`, memakai kolom `Note`, `Kunci`, `Alias` (`02`) serta `Deskriptor` dan `English` (`03`). Ini adalah ukuran **kemunculan literal**, bukan ukuran makna/semantik; sinonim yang tidak persis sama tidak terhitung.
5. Cakupan tema dihitung dari `Contoh Internal Reference` pada `05_tema_layanan.csv` (pemisah ` · `), lalu dibandingkan dengan 164 reference katalog.
6. Klaster pada Bagian 6 adalah **aturan editorial deterministik** berdasarkan label keluarga pada `Description` (prioritas: generik → gourmand → musk → spicy → woody/amber/oud → fresh → aromatic → floral/fruity). Bukan taksonomi resmi, bukan klasifikasi IFRA, bukan klaim komposisi.

---

## 3. Pola keluarga yang dominan

### 3.1 Notes paling sering muncul di bagian `Notes:` (hitungan per deskripsi)

| Note | Jumlah deskripsi | Catatan |
|---|---:|---|
| Musk | 150 | Termasuk kemunculan pada "White Musk" |
| Jasmine | 125 | Bersama variasi ejaan "Melati" pada 5 deskripsi |
| Bergamot | 115 | Pembuka paling dominan |
| Amber | 105 | Fondasi hangat paling dominan |
| Rose | 84 | — |
| Vanilla | 45 | — |
| Cedar | 29 | — |
| Sandalwood | 29 | — |
| Pear | 21 | — |
| Lemon | 20 | — |
| Oud | 14 | — |

**Interpretasi naratif:** katalog sangat bertumpu pada rumus *Bergamot → Jasmine/Rose → Musk/Amber*. Ini mudah dikenal penonton, tetapi menyebabkan banyak produk terasa "mirip" meski nama mereknya berbeda.

### 3.2 Ketimpangan label keluarga

| Fenomena | Angka | Dampak |
|---|---:|---|
| `Aromatic Blend` identik | 39 produk | Tidak bisa dibedakan di LIVE tanpa data baru |
| Label `Floral Fruity` | 6 produk | Family bunga-buah paling padat setelah blok generik |
| Label `Gourmand Vanilla` | 5 produk | Gourmand kuat, tetapi didominasi vanila |
| 95 label unik secara keseluruhan | 95 | Banyak label unik hanya dipakai 1× → perpustakaan keluarga terlalu fragmenter |
| 14 keluarga di `01_keluarga_aroma.csv` | 14 | Jumlah `Jumlah Produk` di file itu berjumlah **164**, cocok dengan katalog, tetapi 14 keluarga ini menyederhanakan 95 label mentah |

### 3.3 Fragmentasi data tambahan di deskripsi

| Jenis teks tambahan | Jumlah | Contoh reference | Status |
|---|---:|---|---|
| Teks "Harga referensi …" tertanam di `Description` | 13 | `ALK-L-025`, `ALK-L-026`, `ALK-L-038`, `ALK-L-041` | **Perlu verifikasi**; tidak boleh dipakai sebagai harga jual |
| Teks "Harga resmi …" tertanam di `Description` | 11 | `ALK-L-001`, `ALK-L-006`, `ALK-L-015`, `ALK-L-018` | **Perlu verifikasi**; angka sengaja tidak disalin ke dokumen ini |
| Teks BPOM / halal | 5 | `ALK-L-023`, `ALK-L-024`, `ALK-L-038`, `ALK-L-040` | **Perlu verifikasi** ke dokumen resmi; bukan klaim audit ini |
| Teks stok / "sold out" / "cek stok" | 6 | `ALK-L-003`, `ALK-L-030` s.d. `ALK-L-034` | **Perlu verifikasi** saat LIVE |
| Ejaan tidak konsisten | — | `ESEN0009` & `PG003` memakai "Safron" (di tempat lain "Saffron"); `ESEN0009` memakai "Melati"/"Gula"; `ALK-P-033` memakai "maskalin" | Perlu normalisasi kosakata |
| Kata berpotensi klaim kuat | — | `ALK-P-063` "membersihkan"; `ESEN0054` "adiktif" | Pakai sebagai majas, jangan sebagai klaim fungsi/medik |

---

## 4. Celah kosakata dan tema

### 4.1 Taksonomi notes (`02_taksonomi_notes.csv`, 98 note)

- **96/98 (98,0%)** note memiliki kemunculan literal di deskripsi.
- **2 note tidak muncul sama sekali:** `Woody Accord`, `Floral Accord`. Keduanya adalah konsep abstrak, bukan note tunggal; cocok dipakai sebagai label edukatif, bukan sebagai "note yang tercantum di katalog".
- Karena pencocokan bersifat literal, kemunculan "Melati" tidak dihitung sebagai "Jasmine". Ini bukan kekurangan data, melainkan **inkonsistensi pelabelan** yang harus dinormalisasi.

### 4.2 Kosakata deskriptor (`03_kosakata_deskriptor.csv`, 78 deskriptor)

- **51/78 (65,4%)** muncul literal di deskripsi; **27/78 (34,6%)** tidak muncul.

| Dimensi | Tersedia | Muncul literal | Cakupan |
|---|---:|---:|---:|
| karakter | 28 | 18 | 64,3% |
| tekstur | 11 | 6 | 54,5% |
| audiens | 8 | 7 | 87,5% |
| momen | 13 | 10 | 76,9% |
| suasana | 6 | 4 | 66,7% |
| proyeksi | 4 | 2 | 50,0% |
| ketahanan | 2 | 1 | 50,0% |
| musim | 4 | 2 | 50,0% |
| tema | 2 | 1 | 50,0% |

**27 deskriptor yang tidak muncul literal:**  
Kulit, Asap, Tanah, Energetik, Dramatis, Segar-Manis, Dekat Kulit, Menyebar, Cepat Hilang, Setelah Mandi, Workshop, Ramah Anggaran, Maduan, Balsamik, Herbal, Pinus, Kayu Krim, Kayu Kering, Kulit Halus, Bunga Krim, Bunga Powdery, Buah Berry, Susu, Musim Semi, Musim Gugur, Fotogenik, Restock.

Catatan penting: sebagian dari daftar itu **sebenarnya sudah memiliki padanan Inggris/sinonim di deskripsi** (mis. "after-shower" untuk "Setelah Mandi", "skin-scent" untuk "Dekat Kulit", "Milk" untuk "Susu", "creamy" untuk kesan "Krim"). Jadi ini terutama **celah bahasa Indonesia terpakai**, bukan selalu celah konsep.

### 4.3 Tema layanan (`05_tema_layanan.csv`, 40 tema)

| Indikator | Hasil | Artinya |
|---|---:|---|
| Jumlah tema | 40 | Sudah mencakup 12 keluarga naratif |
| Reference unik dipakai sebagai contoh | **88/164 (53,7%)** | — |
| Produk **tidak pernah** jadi contoh tema | **76/164 (46,3%)** | Hampir setengah katalog belum punya jalur narasi siap pakai |
| Produk `Aromatic Blend` generik yang dipakai tema | **1/39 (2,6%)**, yaitu `ALK-P-022` | 38 produk generik tidak memiliki hook tema sama sekali |
| Keluarga pada tema | 12 | `Amber / Oriental`, `Aquatik / Laut`, `Aromatic Herbal`, `Attar & Oud`, `Bibit / Konsentrat`, `Citrus Segar`, `Floral Putih & Bouquet`, `Fruity`, `Gourmand`, `Laundry & Clean`, `Musk & Powdery`, `Spicy Leather`, `Woody` |

### 4.4 Resep accord (`04_resep_accord.csv`, 40 accord)

- **40/40** berstatus identik: *"Edukasi/inspirasi konten; bukan formula produksi."*
- Tidak ada celah status: semua sudah diberi label aman. Risikonya bukan pada file ini, melainkan pada kemungkinan pembicara LIVE menyebut rasio sebagai resep nyata. **Rasio accord tidak boleh disajikan sebagai formula produksi atau standar IFRA.**

### 4.5 Prioritas celah

1. **39 deskripsi identik** → belum bisa dijual lewat cerita; perlu data pembeda dari sumber resmi/verifikasi staf.
2. **46 deskripsi tanpa disclaimer** (semua `ALK-L-`) → perlu diseragamkan agar pembicara tidak mengira notes adalah komposisi resmi.
3. **76 produk tanpa contoh tema** → perlu dipetakan ke 40 tema atau dibuatkan tema baru.
4. **27 deskriptor tak terpakai literal** → peluang memperkaya copy bahasa Indonesia.
5. **Teks harga/sertifikat/stok tertanam** → harus dipisahkan dari narasi aroma dan diverifikasi.

---

## 5. 20 kandidat produk dengan potensi storytelling kaya

Semua alasan di bawah **hanya berasal dari teks `Description` di CSV**. Detail di luar itu diberi status **Perlu verifikasi**. Ini bukan komposisi resmi pabrik, bukan klaim khasiat, dan bukan rekomendasi harga.

| # | Internal Reference | Nama | Alasan berbasis `Description` | Status detail di luar `Description` |
|---:|---|---|---|---|
| 1 | `MCB0001` | 1000 Bunga | Label `Floral Bouquet`; notes merangkai Bergamot/Spices → Mixed Flowers → Amber/Musk/Woody; karakter "bunga campuran kaya, oriental"; momen malam/acara; ada atribusi inspirasi. | **Perlu verifikasi:** ejaan/daftar notes resmi dan ketersediaan stok. |
| 2 | `MCB0067` | 212 VIP Rose Carolina Herrera | Kontras buah (Peach, Raspberry) dengan Rose/Jasmine; karakter feminin-elegan-manis; momen malam, pesta, kencan; ada atribusi inspirasi. | **Perlu verifikasi:** posisi merek/usia audiens bila dipakai sebagai klaim. |
| 3 | `ALK-P-012` | Alkaff Zam Zam | Salah satu dari sedikit produk dengan narasi lokal kuat: "Aroma khas Zam Zam, lembut"; momen "sehari-hari, setelah wudhu" memberi ritual harian. | **Perlu verifikasi:** konteks penggunaan dan sensitivitas klaim keagamaan; jangan diubah jadi klaim syariah/fungsi. |
| 4 | `PG002` | Melati Keraton | Notes Green Notes → Jasmine/Tuberose → Sandalwood/Musk; karakter "Melati autentik, feminin, klasik"; momen siang/acara tradisional. | **Perlu verifikasi:** apakah "autentik" dimaksudkan sebagai deskripsi aroma atau klaim bahan; pakai sebagai kesan saja. |
| 5 | `ALK-L-013` | HMNS Unrosed Eau de Parfum | Deskripsi menyebut "Mawar modern, feminin, bersih" dan "Teknik Soliflore khas HMNS" → hook edukatif langka di katalog. | **Perlu verifikasi:** istilah teknik dan atribusi merek ke sumber resmi. |
| 6 | `IBC0079` | 3 L'Imperatrice D&G | Notes buah tropis (Kiwi, Strawberry, Watermelon) + Cyclamen/Jasmine; karakter segar-manis; momen siang, pantai, liburan; ada atribusi inspirasi. | **Perlu verifikasi:** daftar notes resmi; jangan menyebut replika atau tiruan. |
| 7 | `ALK-L-001` | Mykonos Marbella Extrait de Parfum | Karakter sangat visual: "seperti laundry di angin laut"; deskripsi menyatakan gambaran aroma berasal dari situs resmi; momen pantai/kantor/after-shower. | **Perlu verifikasi:** konsentrasi, ukuran, stok, dan angka apa pun yang tertanam di deskripsi. |
| 8 | `ALK-L-046` | Evangeline Premium EDP Sea Salt | notes Sea Salt/Water Lily/Driftwood; karakter "Asin segar, bersih, menenangkan"; momen siang/pantai — cocok untuk adegan laut. | **Perlu verifikasi:** klaim "menenangkan" harus dibingkai sebagai kesan aroma, bukan efek psikologis/medik. |
| 9 | `ALK-P-063` | Jeruk Nipis / Lemongrass | Notes Lime/Lemongrass/Citronella; karakter "Segar sitrus, membersihkan"; momen "setelah Aktivitas" → mudah dibuat skenario harian. | **Perlu verifikasi:** kata "membersihkan" jangan dijadikan klaim fungsi; ubah ke "kesan segar". |
| 10 | `ALK-P-086` | Ombre Nomade Louis Vuitton | Saffron/Raspberry → Rose/Oud → Benzoin/Amber/Leather; karakter "Gelap, mewah, oud berani"; momen malam/formal. | **Perlu verifikasi:** daftar notes resmi; hindari klaim originalitas atau kepemilikan merek. |
| 11 | `SRT009` | Ameer Al Oud | Notes Saffron → Oud/Rose → Amber/Musk/Sandalwood; karakter "Oud elegan, hangat, berwibawa"; momen malam/acara spesial. | **Perlu verifikasi:** konsentrasi, stok, dan apakah "Attar & Oud" adalah kategori atau jenis formula. |
| 12 | `ESEN0009` | Baccarat Rouge 540 | Karakter sangat spesifik: "Manis transparan, hangat, mewah, khas amber-safron"; momen malam/formal/sesi foto → kaya visual. | **Perlu verifikasi:** ejaan Safron/Melati/Gula dan daftar notes resmi; jangan memakai angka model sebagai klaim. |
| 13 | `ALK-P-018` | Angels Share Kilian | Cognac/Cinnamon → Tonka/Oak/Prairie Oud → Vanilla/Sandalwood; karakter "boozy, mewah"; momen malam/musim dingin. | **Perlu verifikasi:** daftar notes resmi; hindari narasi konsumsi alkohol yang ditujukan ke minors. |
| 14 | `IBC0027` | Bubble Gum | Strawberry/Pear → Sugar/Jasmine → Musk/Vanilla; karakter "Permen karet, manis playful"; audiens remaja dan "konten live" eksplisit. | **Perlu verifikasi:** batasan usia audiens dan aturan platform bila menyasar remaja. |
| 15 | `ESEN0054` | Black Opium YSL | Pear/Pink Pepper/Orange Blossom → Kopi/Melati/Almond pahit → Vanilla/Patchouli/Cedar; karakter kopi-vanila "berani, adiktif"; momen night out/kencan. | **Perlu verifikasi:** kata "adiktif" hanya majas; jangan dijadikan klaim ketergantungan. |
| 16 | `ALK-L-004` | Mykonos Matcha Latte Extrait de Parfum | Matcha/Bergamot → Vanilla/Milk → Musk/Amber; karakter "creamy dengan twist teh hijau, viral"; momen hangout/konten live. | **Perlu verifikasi:** klaim "viral"/"andalan" dan angka/stok; jangan menyebut angka penjualan. |
| 17 | `ALK-L-038` | Fres & Natural BT21 Yellow In Luv 100ml | Edisi kolaborasi; karakter "Manis buah ceria"; audiens penggemar BT21; deskripsi memuat referensi registrasi/sertifikasi. | **Perlu verifikasi:** lisensi kolaborasi, nomor registrasi, dan sertifikat — audit ini tidak menyatakan keduanya valid. |
| 18 | `ALK-P-089` | One Million Paco Rabanne | Blood Orange/Mint → Cinnamon/Spices → Leather/Amber/Tonka; karakter "maskulin, hangat, manis pedas, percaya diri"; momen malam/klub. | **Perlu verifikasi:** daftar notes resmi; hindari klaim kepercayaan diri sebagai efek nyata. |
| 19 | `ALK-P-103` | Sakura | Sakura/Pear → Cherry Blossom/Jasmine → Musk/White Wood; karakter "Bunga sakura lembut"; momen siang/konten live; kategori `Parfum / Laundry`. | **Perlu verifikasi:** apakah diposisikan sebagai parfum tubuh atau pewangi laundry; jangan dicampur dalam satu klaim. |
| 20 | `ALK-L-024` | Macbrame Bibit Parfum Konsentrat (900+ aroma, B2B) | Satu-satunya kategori `Bahan Baku / Bibit Parfum`; deskripsi menyebut stabil antar batch, segmen B2B, dan catatan bahwa aroma tertentu sudah ada di sheet impor → narasi workshop/racik. | **Perlu verifikasi:** spesifikasi teknis, klaim halal, pricelist, dan status harga per gram; bukan untuk narasi konsumen LIVE. |

---

## 6. Pemetaan 164 produk ke 8 klaster naratif

Aturan: satu produk hanya masuk satu klaster; penentuan berdasarkan label keluarga pada `Description` dengan prioritas seperti di Bagian 2. Urutan prioritas sengaja menempatkan `Aromatic Blend` lebih dulu agar duplikasi tidak menyamar sebagai fresh/woody.

| Klaster | Fokus narasi LIVE/theater | Jumlah | Contoh `Internal Reference` | Catatan |
|---|---|---:|---|---|
| A. Floral & Fruity Playful | Bunga, bouquet, mawar, melati, buah remaja; adegan kencan siang/hangout | **17** | `MCB0001`, `MCB0067`, `ALK-P-035`, `PG002`, `ALK-L-013` | Cukup kaya, tetapi mudah tumpang tindih dengan klaster B/C |
| B. Citrus & Aquatic Segar | Sitris, laut, air, after-shower; adegan pagi/pantai/kampus | **20** | `IBC0079`, `ALK-P-005`, `ALK-P-063`, `ALK-L-001`, `ALK-L-046` | Notes bergamot laut dominan; bedakan lewat momen, bukan klaim durasi |
| C. Woody Oud / Amber / Attar | Oud, amber, attar, kulit, kayu gelap; adegan malam/formal/premium | **31** | `EXPS0018`, `SRT009`, `ALK-P-086`, `ALK-L-019`, `ALK-L-031` | Klaster paling "berwibawa"; waspadai klaim originalitas merek |
| D. Gourmand Manis | Vanila, kopi, karamel, cokelat, dessert, whipped cream | **31** | `ALK-P-006`, `ESEN0009`, `ESEN0054`, `ALK-L-004`, `ALK-L-042` | Kuat untuk theater indrawi; hindari klaim "bikin ketagihan" sebagai fakta |
| E. Clean Musk & Powdery | Skin-scent, white musk, baby powder, setelah mandi | **8** | `ALK-P-012`, `ORI0088`, `PG012`, `ALK-L-003`, `ALK-L-040` | Klaster kecil tetapi sangat spesifik; cocok untuk narasi ritual |
| F. Spicy Oriental & Woody Hangat | Rempah, saffron, cinnamon, pepper, leather; adegan malam kota | **9** | `LZ0037`, `KV0002`, `ALK-P-089`, `PG003`, `ALK-L-021` | Mirip C, tapi pitch-nya "pedas/urban", bukan "gelap/attar" |
| G. Green Aromatic & Sporty | Teh hijau, bamboo, lavender, rosemary, gym/olahraga | **8** | `LZ0019`, `ALK-P-009`, `ALK-P-048`, `ALK-P-060`, `GCF013` | Klaster kecil; deskripsi hijau/aromatik masih kurang variasi |
| H. Aromatic Blend Generik & Non-LIVE | 39 deskripsi identik + 1 bibit B2B; bukan klaster penjualan | **40** | `ORI00150`, `PG004`, `ALK-P-022`, `ALK-L-024` | **Jangan dipakai untuk storytelling sebelum diperbaiki.** Hanya 1 dari 39 generik dipakai tema (`ALK-P-022`) |

**Total: 17 + 20 + 31 + 31 + 8 + 9 + 8 + 40 = 164.**

Klaster H sengaja dipisah agar kelemahan data terlihat. Bila 39 deskripsi generik kelak diperkaya dari sumber terverifikasi, produk tersebut sebaiknya didistribusikan ulang ke klaster B, C, atau E sesuai notes yang benar.

---

## 7. Metodologi klasifikasi & segmentasi narasi — riset web

Semua URL di bawah diakses pada **2026-11-27**. Status verifikasi menunjukkan apakah isi halaman benar-benar dibaca saat audit.

| Sumber | URL | Diakses | Status verifikasi | Kaitan dengan audit |
|---|---|---|---|---|
| IFRA — *How is fragrance made?* | https://ifrafragrance.org/about-fragrance/how-is-fragrance-made | 2026-11-27 | **Terverifikasi** — halaman dibaca langsung | Menegaskan peran top/middle/base sebagai *peran komposisi* dan bahwa formula akhir ditentukan perfumer + skrining standar. Mendukung peringatan: daftar notes ≠ formula resmi. |
| Aesop — *A Guide to Fragrance* | https://www.aesop.co.nz/library/a-guide-to-fragrance.html | 2026-11-27 | **Terverifikasi** — halaman dibaca langsung | Memberi kerangka empat profil luas (fresh, woody, opulent, floral) dan konsep sillage/longevity; mendukung penyederhanaan 95 label menjadi 8 klaster naratif. Juga menyatakan preferensi aroma dipengaruhi suasana, memori, mood, dan momen → dasar segmentasi momen. |
| Crespo, Ferreira & Cardoso — *The influence of storytelling on the consumer–brand relationship experience*, Journal of Marketing Analytics 11, 41–56 (2023), DOI 10.1057/s41270-021-00149-0 | https://link.springer.com/article/10.1057/s41270-021-00149-0 | 2026-11-27 | **Terverifikasi** — abstrak halaman dibaca langsung; isi penuh berbayar | Storytelling memengaruhi respons kognitif, emosional, dan perilaku melalui identifikasi serta keterlibatan afektif. Menjadi alasan klaster dibuat per persona/momen, bukan per merek saja. |
| Júnior dkk. — *A story to sell: The influence of storytelling on consumers' purchasing behavior*, Psychology & Marketing (2023), DOI 10.1002/mar.21758 | https://onlinelibrary.wiley.com/doi/full/10.1002/mar.21758 | 2026-11-27 | **Terverifikasi sebagian** — cuplikan mesin telusur terbaca; akses penuh 403 | Menyebut empat alur storytelling: identifikasi, nilai emosional, engagement, dan risiko ujaran merugikan. Mengingatkan bahwa narasi perlu verifikasi agar tidak menjadi klaim menyesatkan. |
| IAO — *Basic Perfume Primer* (PDF) | https://artandolfaction.com/wp-content/uploads/2020/12/IAO_1_PRIMER_V4.pdf | 2026-11-27 | **Terverifikasi sebagian** — cuplikan mesin telusur terbaca; PDF tidak dapat di-fetch oleh alat | Menjelaskan top/middle/base sebagai ukuran volatilitas dengan batas waktu yang bersifat relatif, bukan garis tegas. Menjadi dasar larangan klaim "tahan 24 jam" tanpa uji. |

**Catatan metodologis:** tidak ada sumber di atas yang dipakai untuk membenarkan klaim komposisi, harga, supplier, khasiat, atau sertifikasi produk Alkaff. Sumber hanya dipakai untuk metodologi klasifikasi dan batas bahaya klaim.

---

## 8. Rekomendasi singkat

1. **Perbaiki 39 blok `Aromatic Blend`** sebelum dipakai LIVE; jangan mengarang notes pengganti.
2. **Seragamkan disclaimer** pada 46 deskripsi `ALK-L-` agar semua menyatakan notes = gambaran keluarga.
3. **Petakan 76 produk tanpa contoh tema** ke 40 tema yang ada; untuk klaster H, tunda sampai ada data terverifikasi.
4. **Normalisasi ejaan** (Saffron/Safron, Jasmine/Melati, Sugar/Gula, "maskalin") dan pisahkan teks harga/stok/sertifikat dari narasi aroma.
5. **Gunakan 20 kandidat di Bagian 5 sebagai daftar awal** dengan script pendek per produk, bukan klaim komposisi atau khasiat.
6. **Tampilkan harga hanya jika `Sales Price` terisi**, dan tetap cek ulang; 122 baris kosong berarti harga belum terverifikasi.

---

## 9. Pernyataan batasan akhir

Dokumen ini tidak memuat harga jual, supplier, komposisi resmi pabrik, formula produksi, standar IFRA, atau klaim medis/kosmetik. Semua angka di Bagian 1–4 dan 6 berasal dari hitungan langsung pada CSV/CSV basis pengetahuan yang disebutkan. Semua detail di luar `Description` yang disebut di Bagian 5 dan 7 ditandai **Perlu verifikasi** atau **Terverifikasi sebagian**. `Description` tetap dibaca sebagai **gambaran keluarga wewangian**, bukan fakta laboratorium.
