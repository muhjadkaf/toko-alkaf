# Alkaff Catalog

Fondasi modul Odoo untuk katalog parfum Toko Alkaff. Modul ini menyiapkan
kategori produk, field pendukung aroma/notes, log import, dan wizard untuk
mengimpor `katalog_parfum_alkaff_odoo.csv`.

## Versi dan konvensi

Mengikuti konvensi proyek `namlah-odoo-addons`: Odoo **20.0** (`20.0.2.1.0`),
lisensi **LGPL-3**, dependensi minimal `base` dan `sale`. File ACL utama
memakai format Odoo 20 `security/ir.access.csv`. File
`security/ir.model.access.csv` disertakan hanya sebagai format kompatibilitas
Odoo 17 dan sengaja tidak dimuat oleh manifest.

## Cara install

1. Letakkan folder `odoo/addons/alkaff_catalog/` di dalam `addons_path` Odoo.
2. Restart Odoo, lalu perbarui daftar modul (*Apps → Update Modules List*).
3. Cari **Alkaff Catalog — Fondasi Import Parfum** dan klik *Install*.
   Via CLI: `odoo -d <database_uji> -i alkaff_catalog --stop-after-init`
   (jalankan hanya di database uji).

Modul ini akan membuat enam kategori di bawah `Parfum`, field tambahan pada
`product.template`, model log import, dan menu backend **Alkaff**.

## Cara pakai wizard

1. Buka menu **Alkaff → Import Katalog Parfum** (hanya administrator).
2. Pilih file CSV dengan header:
   `Name, Internal Reference, Product Category, Product Type, Sales Price,
   Cost Price, Can be Sold, Can be Purchased, Active, Description,
   Description for E-commerce`.
3. Klik **Import CSV**. Wizard akan menutup/membuka kembali dengan ringkasan
   jumlah produk baru, diperbarui, dan dilewati.
4. Detail per baris ada pada record **Log Import Katalog Alkaff**.

Import bersifat idempoten berdasarkan `Internal Reference` (`default_code`):
reference yang sudah ada diperbarui, bukan dibuat ulang. Lihat
[`docs/IMPORT_MAPPING.md`](docs/IMPORT_MAPPING.md) untuk pemetaan lengkap dan
langkah uji.

Pada instalasi produksi lokal, modul ini di-install hanya di database **`nml`**
(port `8071`) dan CSV katalog diimpor lewat wizard yang sama. Instance `8069`
dan `8070` tidak disentuh.

## Endpoint API untuk web app

Tiga endpoint `auth="public"` bersifat baca-saja dan membatasi CORS ke
`https://alkaff.lokal.or.id`:

| Endpoint | Fungsi |
|---|---|
| `GET /alkaff/api/health` | Status modul + nama database |
| `GET /alkaff/api/themes` | 40 tema dari bundle basis pengetahuan |
| `GET /alkaff/api/recommendations?keyword=...&limit=...` | Tema + hingga 12 produk dari `product.template` |

Field yang dikembalikan hanya `ref`, `name`, `family`, dan `notes_top/heart/base`.
Harga, supplier, `supplier_info_text`, dan data sensitif lain **tidak** dikirim.
Pencarian memakai token keyword dan sinonim Indonesia/Inggris (mis. `kopi` ↔
`coffee`), lalu mengurutkan produk berdasarkan kecocokan nama/kode/notes.

Contoh:

```bash
curl 'https://nml.lokal.or.id/alkaff/api/recommendations?keyword=kopi%20dingin&limit=3'
```

## Batasan

- **Belum ada sinkronisasi supplier otomatis.** Data supplier tetap berada di
  sheet `Supplier_Lokal`; field `supplier_info_text` sengaja tidak diisi wizard.
- Harga tidak dikarang: `Sales Price` kosong → `list_price` tidak ditulis;
  `Cost Price` kosong → `standard_price` tidak ditulis (kasus umum pada
  `Parfum / Lokal Indonesia`).
- Kategori yang belum dikenal tidak dibuat otomatis; tambahkan dulu ke
  `data/product_category.xml` bila ada label baru.
- `aroma_family`, `notes_top`, `notes_heart`, dan `notes_base` diekstrak dengan
  heuristik dari `Description`; field ini adalah gambaran keluarga wewangian,
  bukan komposisi resmi pabrik.
- Modul ini baru berupa fondasi: belum ada sinkronisasi gambar, varian,
  website/e-commerce publish, atau penjualan supplier otomatis.
