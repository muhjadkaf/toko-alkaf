import base64
import binascii
import csv
import io
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Header yang dipakai katalog_parfum_alkaff_odoo.csv. Urutan tidak dianggap
# fixed; yang penting nama kolomnya ada.
REQUIRED_HEADERS = (
    'Name',
    'Internal Reference',
    'Product Category',
    'Product Type',
    'Sales Price',
    'Cost Price',
    'Can be Sold',
    'Can be Purchased',
    'Active',
    'Description',
    'Description for E-commerce',
)

# Label di CSV → XML ID kategori yang dibuat di data/product_category.xml.
CATEGORY_XMLIDS = {
    'Parfum': 'alkaff_catalog.category_parfum',
    'Parfum / Attar & Oud': 'alkaff_catalog.category_parfum_attar_oud',
    'Parfum / Gourmand': 'alkaff_catalog.category_parfum_gourmand',
    'Parfum / Laundry': 'alkaff_catalog.category_parfum_laundry',
    'Parfum / Lokal Indonesia': 'alkaff_catalog.category_parfum_lokal_indonesia',
    'Bahan Baku / Bibit Parfum': 'alkaff_catalog.category_bahan_baku_bibit_parfum',
}

PRODUCT_TYPE_MAP = {
    'consumable': 'consu',
    'consu': 'consu',
    'product': 'product',
    'stock': 'product',
    'service': 'service',
}

TRUE_VALUES = {'true', '1', 'yes', 'y', 't'}
FALSE_VALUES = {'false', '0', 'no', 'n', 'f'}

# Contoh deskripsi: "... — Floral Bouquet. Notes: Top Bergamot, Spices;
# Heart Mixed Flowers; Base Amber, Musk, Woody. Karakter: ..."
NOTES_RE = re.compile(
    r'Notes:\s*Top\s+(?P<top>.*?)\s*;\s*Heart\s+(?P<heart>.*?)\s*;\s*Base\s+(?P<base>.*?)(?:\.|$)',
    re.IGNORECASE | re.DOTALL,
)
FAMILY_RE = re.compile(r'[—–-]\s*(?P<family>[^.]+?)\s*\.', re.DOTALL)


class CatalogImportWizard(models.TransientModel):
    """Import CSV katalog parfum menjadi/mengubah product.template."""

    _name = 'alkaff.catalog.import.wizard'
    _description = 'Wizard Import Katalog Parfum Alkaff'

    csv_file = fields.Binary(string='File CSV', required=True)
    csv_filename = fields.Char(string='Nama File')
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Selesai')],
        string='Status',
        default='draft',
        readonly=True,
    )
    result_text = fields.Text(string='Hasil Import', readonly=True)
    log_id = fields.Many2one(
        'alkaff.catalog.import.log',
        string='Log Import',
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Aksi utama
    # ------------------------------------------------------------------
    def action_import(self):
        self.ensure_one()
        rows = self._read_csv(self.csv_file)
        reader = csv.DictReader(rows)
        headers = reader.fieldnames or []
        missing = [name for name in REQUIRED_HEADERS if name not in headers]
        if missing:
            raise UserError(
                _('Header CSV tidak lengkap. Kolom kurang: %s')
                % ', '.join(missing)
            )

        Product = self.env['product.template'].sudo()
        notes = []
        seen_refs = set()
        created = updated = skipped = 0

        for row in reader:
            ref = (row.get('Internal Reference') or '').strip()
            if not ref:
                skipped += 1
                notes.append(_('Baris tanpa Internal Reference dilewati.'))
                continue
            # Duplikat reference di dalam satu file: baris pertama yang menang.
            if ref in seen_refs:
                skipped += 1
                notes.append(
                    _('%s: duplikat Internal Reference dalam file, dilewati.') % ref
                )
                continue
            seen_refs.add(ref)

            vals = self._prepare_product_vals(row, notes)
            if not vals:
                skipped += 1
                continue

            # active_test=False agar produk yang pernah dinonaktifkan tetap
            # ditemukan dan diperbarui, bukan dibuat duplikat.
            product = Product.with_context(active_test=False).search(
                [('default_code', '=', ref)], limit=1
            )
            if product:
                product.write(vals)
                updated += 1
            else:
                Product.create(dict(vals, default_code=ref))
                created += 1

        log = self.env['alkaff.catalog.import.log'].sudo().create({
            'name': _('Import Katalog Parfum Alkaff'),
            'filename': self.csv_filename or _('katalog.csv'),
            'rows_total': created + updated + skipped,
            'rows_created': created,
            'rows_updated': updated,
            'rows_skipped': skipped,
            'notes': '\n'.join(notes),
        })
        summary = _(
            'Selesai: %(created)s produk dibuat, %(updated)s diperbarui, '
            '%(skipped)s baris dilewati. Log: #%(log)s'
        ) % {
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'log': log.id,
        }
        self.write({
            'state': 'done',
            'result_text': summary + '\n\n' + '\n'.join(notes),
            'log_id': log.id,
        })
        return self._reopen_action()

    # ------------------------------------------------------------------
    # Helper parsing
    # ------------------------------------------------------------------
    @api.model
    def _read_csv(self, binary_value):
        """Terima nilai field Binary Odoo (bytes) maupun string base64 mentah."""
        value = binary_value or b''
        # Odoo 20 menyimpan field Binary sebagai BinaryValue (bukan bytes biasa).
        if hasattr(value, 'content'):
            value = bytes(value)
        if isinstance(value, bytes):
            # Odoo mengembalikan bytes file yang sudah didekode dari base64.
            try:
                value.decode('utf-8-sig')
                raw = value
            except UnicodeDecodeError:
                try:
                    raw = base64.b64decode(value, validate=True)
                except (binascii.Error, ValueError):
                    raise UserError(_('Isi file CSV tidak valid (base64 rusak).'))
        else:
            try:
                raw = base64.b64decode(value, validate=True)
            except (binascii.Error, ValueError):
                raise UserError(_('Isi file CSV tidak valid (base64 rusak).'))
        try:
            # utf-8-sig membuang BOM yang sering dibawa spreadsheet.
            return raw.decode('utf-8-sig').splitlines()
        except UnicodeDecodeError:
            raise UserError(_('File CSV harus ber-encoding UTF-8.'))

    @api.model
    def _parse_bool(self, value):
        raw = (value or '').strip().lower()
        if raw in TRUE_VALUES:
            return True
        if raw in FALSE_VALUES:
            return False
        return None

    @api.model
    def _parse_price(self, value):
        """Kembalikan float, atau None bila kosong; raising ValueError bila rusak."""
        raw = (value or '').strip()
        if not raw:
            return None
        return float(raw.replace(',', '.'))

    @api.model
    def _resolve_category(self, label, notes, ref):
        xmlid = CATEGORY_XMLIDS.get((label or '').strip())
        if not xmlid:
            notes.append(
                _('%s: kategori "%s" belum dikenal, kategori tidak diubah.')
                % (ref, label or '-')
            )
            return None
        category = self.env.ref(xmlid, raise_if_not_found=False)
        if not category:
            notes.append(
                _('%s: kategori %s belum terpasang, kategori tidak diubah.')
                % (ref, xmlid)
            )
        return category

    @api.model
    def _prepare_product_vals(self, row, notes):
        """Petakan satu baris CSV ke vals product.template.

        Catatan sengaja dikosongkan:
        * Cost Price kosong → standard_price tidak ditulis (tidak mengarang
          harga modal, terutama untuk Parfum / Lokal Indonesia).
        * Sales Price kosong → list_price tidak ditulis (tidak mengarang harga
          jual). Produk tetap dibuat dengan harga bawaan Odoo (0).
        * supplier_info_text tidak pernah diisi dari CSV ini; data supplier
          berada di sheet Supplier_Lokal dan belum ada sinkronisasi otomatis.
        """
        ref = (row.get('Internal Reference') or '').strip()
        name = (row.get('Name') or '').strip()
        if not name:
            notes.append(
                _('%s: Name kosong, baris dilewati.') % (ref or '-')
            )
            return None

        vals = {'name': name, 'default_code': ref}

        category = self._resolve_category(row.get('Product Category'), notes, ref)
        if category:
            vals['categ_id'] = category.id

        raw_type = (row.get('Product Type') or '').strip().lower()
        vals['type'] = PRODUCT_TYPE_MAP.get(raw_type, 'consu')
        if raw_type not in PRODUCT_TYPE_MAP:
            notes.append(
                _('%s: Product Type "%s" tidak dikenal, dipakai Consumable.')
                % (ref, raw_type or '-')
            )

        for header, field in (
            ('Can be Sold', 'sale_ok'),
            ('Can be Purchased', 'purchase_ok'),
            ('Active', 'active'),
        ):
            flag = self._parse_bool(row.get(header))
            if flag is None:
                notes.append(
                    _('%s: %s tidak dikenal, field %s tidak diubah.')
                    % (ref, header, field)
                )
            else:
                vals[field] = flag

        try:
            sales_price = self._parse_price(row.get('Sales Price'))
        except ValueError:
            notes.append(_('%s: Sales Price bukan angka, tidak ditulis.') % ref)
        else:
            if sales_price is None:
                notes.append(
                    _('%s: Sales Price kosong, list_price sengaja tidak ditulis.') % ref
                )
            else:
                vals['list_price'] = sales_price

        try:
            cost_price = self._parse_price(row.get('Cost Price'))
        except ValueError:
            notes.append(_('%s: Cost Price bukan angka, tidak ditulis.') % ref)
        else:
            if cost_price is None:
                notes.append(
                    _('%s: Cost Price kosong, standard_price sengaja dikosongkan.') % ref
                )
            else:
                vals['standard_price'] = cost_price

        description = (row.get('Description') or '').strip()
        vals['description'] = description
        ecommerce_html = (row.get('Description for E-commerce') or '').strip()
        vals['x_description_ecommerce'] = ecommerce_html
        # Field bawaan berbeda antar versi Odoo; isi bila memang tersedia.
        if 'description_ecommerce' in self.env['product.template']._fields:
            vals['description_ecommerce'] = ecommerce_html

        notes_match = NOTES_RE.search(description)
        if notes_match:
            vals['notes_top'] = notes_match.group('top').strip()
            vals['notes_heart'] = notes_match.group('heart').strip()
            vals['notes_base'] = notes_match.group('base').strip()
        else:
            notes.append(
                _('%s: pola "Notes: Top ...; Heart ...; Base ..." tidak ditemukan.') % ref
            )

        family_match = FAMILY_RE.search(description)
        if family_match:
            vals['aroma_family'] = family_match.group('family').strip()

        notes.append(
            _('%s: supplier_info_text tidak diisi (sumber: sheet Supplier_Lokal).') % ref
        )
        return vals

    def _reopen_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hasil Import Katalog Parfum Alkaff'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }
