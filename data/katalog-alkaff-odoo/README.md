# Katalog Parfum Alkaff — Siap Import Odoo

Dibuat 2026-11-26 dari workbook `daftar parfum di toko.sync-conflict-20261026-144315-ICWAE6O.xlsx`, lalu diperluas dengan riset parfum lokal Indonesia terlaris pada 2026-11-26.

## File

| File | Isi |
|---|---|
| `katalog_parfum_alkaff_odoo.xlsx` | 6 sheet: `IMPORT_odoo`, `Detail_Harga_Sumber`, `Tanpa_Harga`, `Panduan_Import`, `Supplier_Lokal`, `Referensi_Ranking` |
| `katalog_parfum_alkaff_odoo.csv` | Sama dengan sheet `IMPORT_odoo` (UTF-8 BOM, siap diimpor Odoo) |

## Sheet yang dibaca dari workbook toko

- `nota nota hal dila`
- `nota depo`
- `NOTA NOTA JAF`
- `shopee` (hanya baris parfum/bibit/attar; botol, madu, alat, dll. tidak dimasukkan)
- `parfum yang ada di toko` — dipakai sebagai master tambahan untuk **harga ecer** dan pabrik

## Hasil

- **164 produk** di sheet `IMPORT_odoo` (118 dari workbook toko + 46 produk lokal hasil riset).
- Reference lokal memakai prefix `ALK-L-001 … ALK-L-046` agar mudah dibedakan. Semua reference unik.
- **10 nama tanpa harga dari workbook** tidak diimpor, tetapi dicatat di sheet `Tanpa_Harga`:
  `Apel, Arabian Rose, Garuda, Hajar Aswad, Hugo Boss Orange, Lacoste Sport, Musk Amber, Rose Seroja, Roudhoh, Victory`.
- Nama dari beberapa sheet sudah digabung menjadi satu produk. Variasi nama asli ada di kolom `Nama Alternatif` pada sheet `Detail_Harga_Sumber`.
- Kategori: `Parfum` (96), `Parfum / Attar & Oud` (10), `Parfum / Gourmand` (8), `Parfum / Laundry` (4), `Parfum / Lokal Indonesia` (45), `Bahan Baku / Bibit Parfum` (1).

### Tambahan parfum lokal Indonesia

46 produk dari 10 brand lokal terlaris Shopee Indonesia Q2 2026 + 1 pelengkap B2B:

| Brand | Peringkat (Databoks/Compas) | Pangsa | Produk dimasukkan |
|---|---|---|---|
| MyKonos | 1 | 6,75% | 5 |
| Scarlett | 2 | 5,43% | 4 |
| HMNS | 3 | 5,06% | 4 |
| Saff & Co | 4 | 3,52% | 4 |
| Octarine | 5 | 2,98% | 6 |
| Macbrame | 6 | 1,57% | 1 (bibit/konsentrat B2B) |
| Morris | 7 | 1,49% | 5 |
| Velixir | 8 (`Velixlr` di Databoks) | 1,36% | 5 |
| Fres & Natural | 9 | 1,26% | 5 |
| Evangeline | 10 | 0,93% | 7 |

Parfarome masuk dalam daftar GoodStats (posisi 9, 1,49%) tetapi tidak ditambahkan sebagai produk baru karena sudah dipakai sebagai *factory* di nota toko Alkaff. Data distributor Parfarome tetap dicatat di sheet `Supplier_Lokal`.

## Field penting

- `Cost Price` — harga modal terakhir yang **berbasis gram**. Jika tidak tersedia, dipakai harga kemasan (misalnya bibit 100 ml). Basisnya ada di kolom `Basis Harga` pada sheet detail. **Jangan mencampur harga per gram dan per kemasan.**
- `Sales Price` — diisi bila ada harga ecer terverifikasi. Dari 164 produk, 42 terisi (13 dari workbook + 29 produk lokal dari situs resmi/retailer resmi); 122 sengaja dikosongkan, bukan diarang.
- Untuk produk lokal, `Cost Price` sengaja **kosong** karena harga beli/negosiasi supplier belum tersedia. Harga di `Sales Price` adalah **harga eceran referensi**, bukan harga jual final Alkaff.
- `Description` — teks biasa berisi **Notes (Top/Heart/Base), Karakter, Cocok untuk, dan Momen**.
- `Description for E-commerce` — versi HTML untuk website/e-commerce Odoo.

## Supplier lokal (sheet `Supplier_Lokal`)

Berisi 12 baris: brand owner/produsen (atau distributor, untuk Parfarome dan Ashar), badan hukum, alamat, kota, telepon/WhatsApp, email, website, kanal pembelian, sertifikasi, catatan untuk Alkaff, dan sumber data.

Catatan penting sebelum order:

- **Macbrame** sudah terdaftar sebagai *factory* di nota toko untuk banyak aroma. Pricelist/sampel melalui `maharum.group/sample-request`. Jangan duplikasi aroma spesifik yang sudah ada di `IMPORT_odoo`.
- **Scarlett** punya program *Reseller Resmi/Official Partner*; **Saff & Co** menyediakan `partnership@saffnco.com` — keduanya jalur yang cocok untuk toko.
- **Parfarome**: data yang tercantum adalah **distributor Bandung**, bukan pabrik/brand owner. Konfirmasi dulu sebelum order besar.
- **Ashar Grosir Parfum**: situs mengembalikan HTTP 403 saat divalidasi; alamat/kontak lengkap **wajib dikonfirmasi** sebelum transaksi.
- **Velixir**: harga di situs resmi masih dalam USD dan berbeda menurut region, jadi tidak dikonversi ke IDR.
- **Morris**: email yang tercantum adalah email rekrutmen; kontak CS perlu dikonfirmasi. Tahun berdiri juga berbeda antar sumber (2004/2007/2009).
- Semua kontak berasal dari situs resmi/publik pada 2026-11-26, **bukan kontrak resmi**. Verifikasi ulang alamat, kontak, MOQ, stok, dan sertifikasi per SKU sebelum kerja sama.

## Sumber ranking

- **Databoks/Katadata**, 12/11/2026 — *10 Best-Selling Local Perfume Brands on Shopee Indonesia in Q2 2026*. Metode: Compas, online crawling 1 April–30 Juni 2026, toko resmi & nonresmi, rating > 4 bintang.
  `https://databoks.katadata.co.id/en/consumer-durables-apparel/statistics/6af55e3e43df0/10-best-selling-local-perfume-brands-on-shopee-indonesia-in-q2-2026`
- **GoodStats Data**, 05/10/2026 — *10 Brand Parfum & Wewangian Terlaris di Shopee Q2 2026* (mencampur brand lokal & global).
  `https://data.goodstats.id/statistic/10-brand-parfum-wewangian-terlaris-di-shopee-pada-q2-2026-peringkat-atas-kebal-YAF3P`

Lima besar identik di kedua sumber; selisih persentase kecil (mis. 6,75% vs 6,78%) kemungkinan perbedaan pembulatan/waktu tarik data. Detail ada di sheet `Referensi_Ranking`. Peringkat adalah pangsa nilai penjualan Shopee Q2 2026, **bukan jaminan kualitas atau ketersediaan stok**.

## Cara import

1. Pastikan kategori produk sudah ada, atau saat import centang **Create missing values** untuk *Product Category* (termasuk `Parfum / Lokal Indonesia` dan `Bahan Baku / Bibit Parfum`).
2. Buka **Sales → Products → Products → Import**, unggah CSV/XLSX.
3. Cek ulang `Sales Price`; isi manual untuk produk yang masih kosong sebelum dijual. Untuk produk lokal, tentukan `Cost Price` setelah harga supplier dikonfirmasi.
4. Tinjau ulang `Description` sebelum dipakai sebagai klaim penjualan.

## Catatan keakuratan

- Notes parfum disusun berdasarkan **nama produk / inspired-by** dan keluarga aroma umum. Ini **bukan komposisi resmi pabrik** dan bukan klaim identik dengan brand asli. Kalau dipakai untuk konten penjualan, sebaiknya diverifikasi oleh admin toko.
- Produk alternatif/inspired-by dari workbook toko **bukan barang resmi** brand yang disebut dalam nama.
- Untuk produk lokal, deskripsi aroma sebagian berasal dari situs resmi brand (MyKonos Marbella, Octarine Vanilla Laice, Fres & Natural Ocean Secrets, Evangeline Baby Powder); sisanya adalah gambaran keluarga aroma, bukan klaim resmi.
- Harga sumber adalah harga pembelian historis dari nota (workbook) atau harga eceran referensi dari situs resmi/retailer resmi (produk lokal). Harga jual final tetap keputusan toko.
- Data supplier dan ranking dapat berubah; lakukan verifikasi ulang sebelum transaksi atau publikasi konten.
