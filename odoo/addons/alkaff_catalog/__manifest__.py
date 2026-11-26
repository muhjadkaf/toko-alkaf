{
    'name': 'Alkaff Catalog — Fondasi Import Parfum',
    'version': '20.0.1.0.0',
    'category': 'Sales/Catalog',
    'summary': 'Fondasi katalog parfum Toko Alkaff: kategori, field aroma, dan wizard import CSV.',
    'description': """
Fondasi modul katalog Toko Alkaff.

Isi awal:
* Kategori produk Parfum dan subkategorinya (termasuk Bahan Baku / Bibit Parfum).
* Field tambahan pada product.template untuk keluarga aroma, notes, dan deskripsi e-commerce.
* Model log hasil import.
* Wizard Import Katalog Parfum yang membaca CSV dengan header:
  Name, Internal Reference, Product Category, Product Type, Sales Price,
  Cost Price, Can be Sold, Can be Purchased, Active, Description,
  Description for E-commerce.

Harga kosong tidak diarang-ang, dan data supplier tidak disentuh oleh import ini.
""",
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.access.csv',
        'data/product_category.xml',
        'wizards/catalog_import_wizard_views.xml',
    ],
    'license': 'LGPL-3',
    'author': 'Toko Alkaff',
    'application': False,
    'installable': True,
}
