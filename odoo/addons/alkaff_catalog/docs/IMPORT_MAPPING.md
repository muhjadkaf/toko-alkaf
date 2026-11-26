# Pemetaan Import Katalog Parfum Alkaff

Dokumen ini menjelaskan bagaimana wizard **Import Katalog Parfum Alkaff**
membaca `katalog_parfum_alkaff_odoo.csv` dan menulis `product.template`.

Sumber CSV yang dibaca saat pengembangan:
`data/katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv` di root repo `toko-alkaf`.
Folder `data/` hanya dibaca oleh modul ini, tidak diubah.

## Asumsi versi

Modul mengikuti konvensi repo `namlah-odoo-addons`: versi **`20.0.1.0.0`**,
lisensi **`LGPL-3`**, dan ACL memakai format **`ir.access.csv`** (Odoo 20 hanya
memiliki model `ir.access`). Berkas `security/ir.model.access.csv` juga
disiapkan sebagai format ACL Odoo 17 untuk kompatibilitas, tetapi **tidak
dirujuk di manifest** agar tidak mengganggu instalasi Odoo 20.

## Header yang diwajibkan

```text
Name, Internal Reference, Product Category, Product Type, Sales Price, Cost Price,
Can be Sold, Can be Purchased, Active, Description, Description for E-commerce
```

Wizard menolak import bila ada header di atas yang hilang. Urutan kolom tidak
penting. File dibaca sebagai UTF-8 (BOM otomatis dibuang).

## Tabel pemetaan

| Kolom CSV | Field Odoo | Catatan |
|---|---|---|
| `Name` | `product.template.name` | Wajib; baris tanpa nama dilewati. |
| `Internal Reference` | `product.template.default_code` | Kunci pencarian create/update. Baris tanpa reference dilewati. |
| `Product Category` | `product.template.categ_id` | Dicocokkan persis dengan label kategori di bawah. Kategori asing tidak dibuat otomatis. |
| `Product Type` | `product.template.type` | `Consumable` → `consu`; `Service` → `service`; `Stock/Product` → `product`. Nilai lain fallback ke `consu` + catatan log. |
| `Sales Price` | `product.template.list_price` | Diisi hanya bila tidak kosong dan berupa angka. **Kosong = sengaja tidak ditulis** (harga jual tidak dikarang); produk memakai harga bawaan Odoo. |
| `Cost Price` | `product.template.standard_price` | Diisi hanya bila tidak kosong dan berupa angka. **Kosong = sengaja dikosongkan**, terutama untuk `Parfum / Lokal Indonesia` (45 baris di CSV sumber). |
| `Can be Sold` | `product.template.sale_ok` | `TRUE` → True, `FALSE` → False. |
| `Can be Purchased` | `product.template.purchase_ok` | `TRUE` → True, `FALSE` → False. |
| `Active` | `product.template.active` | `TRUE` → True, `FALSE` → False. Pencarian memakai `active_test=False`. |
| `Description` | `product.template.description` | Teks deskripsi utama. |
| `Description` (pola `Notes: Top …; Heart …; Base …`) | `notes_top`, `notes_heart`, `notes_base` | Diekstrak dengan regex dari deskripsi. Bila pola tidak cocok, field tidak disentuh dan dicatat di log. |
| `Description` (fragmen setelah tanda `—` sampai titik pertama) | `aroma_family` | Heuristik, mis. `Floral Bouquet`, `Spicy Woody`. Bukan komposisi resmi pabrik. |
| `Description for E-commerce` | `x_description_ecommerce`, dan `description_ecommerce` bila field bawaan tersedia | HTML disalin apa adanya. |
| — | `supplier_info_text` | **Sengaja tidak diisi.** CSV ini tidak memuat supplier; sumber tetap sheet `Supplier_Lokal`. Belum ada sinkronisasi supplier otomatis. |

## Kategori yang dibuat modul

Struktur hierarki di `data/product_category.xml` — `Parfum` menjadi induk:

```text
Parfum
├── Parfum / Attar & Oud
├── Parfum / Gourmand
├── Parfum / Laundry
├── Parfum / Lokal Indonesia
└── Bahan Baku / Bibit Parfum
```

Nama dengan slash dipertahankan persis seperti label CSV, bukan dipecah menjadi
beberapa level, agar mapping `Product Category` bersifat 1:1.

## Duplikat `Internal Reference`

- Wizard mencari `product.template` dengan `default_code` persis sama dengan
  `Internal Reference`.
- Sudah ada → **update** produk tersebut (tidak membuat duplikat).
- Belum ada → **create** produk baru.
- Duplikat reference **di dalam satu file CSV**: baris pertama dipakai, baris
  berikutnya dilewati dan dicatat di log.
- Reference kosong → baris dilewati dan dicatat di log.
- Contoh dari CSV sumber: 164 baris, 0 duplikat reference; 122 baris tanpa
  `Sales Price`, 47 baris tanpa `Cost Price`.

## Langkah uji (tanpa menyentuh produksi)

1. Pasang modul di database uji:
   `-i alkaff_catalog -u alkaff_catalog` atau lewat Apps → *Alkaff Catalog*.
2. Pastikan 6 kategori di atas muncul di *Sales → Configuration → Product Categories*.
3. Buka menu **Alkaff → Import Katalog Parfum**, unggah
   `katalog_parfum_alkaff_odoo.csv`, klik **Import CSV**.
4. Periksa ringkasan hasil pada wizard dan record **Log Import Katalog Alkaff**
   (menu Technical bila perlu): jumlah create/update/skip serta catatan harga kosong.
5. Cek contoh produk:
   - `MCB0001` → kategori `Parfum`, `list_price` tetap 0 (Sales Price kosong),
     `standard_price = 863`, notes terisi, `aroma_family = Floral Bouquet`.
   - `ALK-L-024` → kategori `Bahan Baku / Bibit Parfum`, harga jual dan modal
     kosong, `supplier_info_text` tetap kosong.
6. Ulangi import file yang sama: angka **produk baru harus 0**, semua barcode
   menjadi **diperbarui** (idempoten).
7. Uji negatif: hapus satu header → wizard harus menampilkan pesan error;
   masukkan dua baris dengan reference sama → yang kedua dilewati.

> Modul ini belum dijalankan dengan Odoo saat dibuat. Validasi yang dilakukan
> hanya `python3 -m py_compile` untuk Python dan pengecekan well-formed XML.
