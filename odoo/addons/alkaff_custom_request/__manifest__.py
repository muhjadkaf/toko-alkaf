{
    'name': 'Alkaff Custom Request — Draft Rebrand LIVE',
    'version': '20.0.1.0.0',
    'category': 'Sales/Catalog',
    'summary': 'Draft permintaan custom/rebrand parfum dari konsol LIVE Alkaff.',
    'description': """
Draft custom/rebrand penonton LIVE Alkaff.

Model ini sengaja terpisah dari product.template: tidak ada harga, supplier,
Cost Price, atau publish otomatis. Nama penonton dipakai sebagai label hanya
bila consent_opt_in benar dan admin menyetujui draft. Tidak ada userId TikTok.
""",
    'depends': ['base', 'sale', 'alkaff_catalog'],
    'data': [
        'security/ir.access.csv',
        'views/custom_request_views.xml',
    ],
    'license': 'LGPL-3',
    'author': 'Toko Alkaff',
    'application': False,
    'installable': True,
}
