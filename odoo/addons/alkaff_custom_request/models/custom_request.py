"""Draft custom/rebrand untuk penonton LIVE Alkaff.

Model ini TIDAK membuat product.template, tidak menyimpan harga/supplier, dan
tidak publish ke e-commerce. `label_name` hanya boleh diisi setelah opt-in dan
hanya dipakai sebagai label produk nyata setelah admin approve.
"""
import re
import time

from odoo import api, fields, models
from odoo.exceptions import UserError

_ALIAS_RE = re.compile(r"^[A-Za-z0-9._-]{1,32}$")
_BOTTLE_TYPES = [("rollon", "Roll-on"), ("spray", "Spray"), ("usap", "Usap")]
_STATUS = [
    ("draft", "Draft"),
    ("review", "Menunggu Review"),
    ("approved", "Disetujui"),
    ("rejected", "Ditolak"),
]
_CLAIM_BLOCKLIST = (
    "24 jam", "bebas alergi", "afrodisiak", "menghangatkan tubuh",
    "formula produksi", "komposisi resmi", "gratis", "diskon",
    "auto-dm", "auto dm", "obat", "menyembuhkan", "dijamin",
    "halal tanpa bukti", "halal",
)


def _claim_guard(*values):
    combined = " ".join(str(value or "") for value in values).lower()
    for phrase in _CLAIM_BLOCKLIST:
        if phrase in combined:
            return phrase
    return ""


class AlkaffCustomRequest(models.Model):
    _name = "alkaff.custom.request"
    _description = "Draft Custom/Rebrand Alkaff"
    _order = "id desc"

    name = fields.Char(string="Judul Draft", required=True, default="Draft Custom Rebrand Alkaff")
    draft_ref = fields.Char(string="Ref Draft", copy=False, readonly=True, index=True)
    alias = fields.Char(string="Alias Penonton", size=32, required=True,
                        help="Alias/nama tampilan, BUKAN userId TikTok.")
    label_name = fields.Char(string="Label Nama (opt-in)", size=32,
                             help="Kosong bila penonton tidak memberi opt-in.")
    consent_opt_in = fields.Boolean(string="Opt-in nama dipakai", default=False)
    consent_at = fields.Datetime(string="Waktu Opt-in", readonly=True)
    theme_ref = fields.Char(string="Ref Tema", size=80, required=True)
    notes_aman = fields.Text(string="Notes Aman",
                             help="Keluarga aroma/edukasi, bukan formula produksi.")
    bottle_type = fields.Selection(_BOTTLE_TYPES, string="Format", default="spray", required=True)
    product_ref = fields.Many2one("product.template", string="Produk existing (opsional)")
    intent = fields.Char(string="Intent", size=24, default="custom")
    reason = fields.Text(string="Alasan Keputusan")
    status = fields.Selection(_STATUS, string="Status", default="draft", readonly=True)
    review_note = fields.Text(string="Catatan Review")
    reviewed_by = fields.Many2one("res.users", string="Ditinjau Oleh", readonly=True)
    reviewed_at = fields.Datetime(string="Waktu Review", readonly=True)
    odoo_sync = fields.Selection(
        [("pending", "Menunggu input admin"), ("linked", "Ditautkan manual")],
        string="Sinkronisasi", default="pending",
        help="Draft tidak otomatis membuat/mengubah produk.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        cleaned = []
        for raw in vals_list:
            vals = dict(raw)
            alias = str(vals.get("alias") or "").strip()
            if not _ALIAS_RE.fullmatch(alias):
                raise UserError("Alias harus 1-32 karakter A-Z, a-z, 0-9, titik, underscore, atau dash.")
            vals["alias"] = alias
            if vals.get("consent_opt_in") is True:
                vals["consent_at"] = fields.Datetime.now()
                label = str(vals.get("label_name") or alias).strip()[:32]
                vals["label_name"] = label
            else:
                vals["consent_opt_in"] = False
                vals["label_name"] = False
                vals["consent_at"] = False
            blocked = _claim_guard(
                vals.get("theme_ref"), vals.get("notes_aman"), vals.get("label_name")
            )
            if blocked:
                raise UserError('Klaim tidak diizinkan: "%s".' % blocked)
            cleaned.append(vals)
        records = super().create(cleaned)
        for record in records:
            if not record.draft_ref:
                ref = "CD-%s-%05d" % (time.strftime("%Y%m%d", time.gmtime()), record.id)
                record.sudo().write({"draft_ref": ref, "name": ref})
        return records

    def write(self, vals):
        vals = dict(vals)
        if "status" in vals and not self.env.user.has_group("base.group_system"):
            raise UserError("Status draft hanya dapat diubah admin.")
        if vals.get("label_name"):
            consent = vals.get("consent_opt_in")
            if consent is None:
                consent = any(record.consent_opt_in for record in self)
            if not consent:
                raise UserError("Label nama penonton memerlukan opt-in.")
        if vals.get("consent_opt_in") is True and "consent_at" not in vals:
            vals["consent_at"] = fields.Datetime.now()
        return super().write(vals)

    def action_submit_review(self):
        if not self.env.user.has_group("base.group_user"):
            raise UserError("Hanya operator yang dapat mengirim draft ke review.")
        for record in self:
            if record.status != "draft":
                raise UserError("Hanya draft berstatus Draft yang bisa dikirim ke review.")
        self.sudo().write({"status": "review"})
        return True

    def action_approve(self):
        if not self.env.user.has_group("base.group_system"):
            raise UserError("Hanya admin yang dapat menyetujui draft.")
        for record in self:
            if record.status not in ("draft", "review"):
                raise UserError("Draft ini tidak bisa disetujui dari status saat ini.")
            if record.label_name and not (record.consent_opt_in and record.consent_at):
                raise UserError("Nama label tanpa opt-in tidak boleh disetujui.")
        self.sudo().write({
            "status": "approved",
            "reviewed_by": self.env.user.id,
            "reviewed_at": fields.Datetime.now(),
        })
        return True

    def action_reject(self):
        if not self.env.user.has_group("base.group_system"):
            raise UserError("Hanya admin yang dapat menolak draft.")
        self.sudo().write({
            "status": "rejected",
            "reviewed_by": self.env.user.id,
            "reviewed_at": fields.Datetime.now(),
        })
        return True
