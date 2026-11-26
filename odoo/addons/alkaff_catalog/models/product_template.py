from odoo import fields, models


class ProductTemplate(models.Model):
    """Field tambahan untuk katalog parfum Alkaff.

    Nama field di bawah sengaja tidak memakai prefiks ``x_`` karena tidak ada
    field bawaan Odoo 17/20 dengan nama yang sama; ini menjaga mapping CSV
    tetap mudah dibaca. Field ``description_ecommerce`` (bila tersedia di
    versi Odoo yang dipakai) tetap memakai field bawaan — wizard menyalin
    HTML ke field itu dan ke ``x_description_ecommerce`` sebagai cadangan.
    """

    _inherit = 'product.template'

    supplier_info_text = fields.Text(
        string='Info Supplier (Teks)',
        help=(
            'Catatan supplier berupa teks bebas. Tidak diisi otomatis oleh '
            'import CSV; sumber data supplier tetap sheet Supplier_Lokal.'
        ),
    )
    aroma_family = fields.Char(
        string='Keluarga Aroma',
        help='Keluarga wewangian, mis. Floral Bouquet / Spicy Woody (dari deskripsi CSV).',
    )
    notes_top = fields.Char(string='Top Notes')
    notes_heart = fields.Char(string='Heart Notes')
    notes_base = fields.Char(string='Base Notes')
    x_description_ecommerce = fields.Html(
        string='Deskripsi E-commerce (Alkaff)',
        help='Salinan HTML kolom "Description for E-commerce" dari CSV katalog.',
    )
