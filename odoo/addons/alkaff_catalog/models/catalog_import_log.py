from odoo import _, fields, models


class AlkaffCatalogImportLog(models.Model):
    """Ringkasan tiap kali wizard import dijalankan."""

    _name = 'alkaff.catalog.import.log'
    _description = 'Log Import Katalog Alkaff'
    _order = 'id desc'

    name = fields.Char(
        string='Nama',
        required=True,
        default=lambda self: _('Import Katalog Parfum Alkaff'),
    )
    filename = fields.Char(string='Nama File CSV')
    rows_total = fields.Integer(string='Jumlah Baris')
    rows_created = fields.Integer(string='Produk Baru')
    rows_updated = fields.Integer(string='Produk Diperbarui')
    rows_skipped = fields.Integer(string='Baris Dilewati')
    notes = fields.Text(string='Catatan Import')
