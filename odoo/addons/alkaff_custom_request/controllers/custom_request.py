"""JSON-RPC internal untuk draft custom LIVE Alkaff.

Memakai auth='user' (bukan public): konsol harus berada di sesi Odoo yang
sudah login. Tidak ada auto-publish, tidak ada QR, tidak ada harga/supplier.
"""
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

_NOTICE = (
    "Permintaan dicatat. Bukan produk jadi; belum bisa dipesan atau dibayar; "
    "menunggu tinjauan admin."
)


def _public(record):
    return {
        "draftRef": record.draft_ref or "",
        "status": record.status,
        "alias": record.alias,
        "labelName": record.label_name or "",
        "consentOptIn": bool(record.consent_opt_in),
        "consentAt": record.consent_at and record.consent_at.isoformat() or "",
        "themeRef": record.theme_ref or "",
        "notesAman": record.notes_aman or "",
        "bottleType": record.bottle_type or "",
        "intent": record.intent or "",
        "reason": record.reason or "",
        "qrEligible": False,
        "notice": _NOTICE,
    }


class AlkaffCustomRequestApi(http.Controller):
    @http.route(
        "/alkaff/api/custom-request",
        auth="user",
        type="jsonrpc",
        methods=["POST"],
        csrf=False,
    )
    def create_custom_request(self, alias=None, labelName=None, consentOptIn=False,
                              themeRef=None, notesAman=None, bottleType="spray",
                              productRef=None, intent="custom", reason="", **kw):
        try:
            product_id = False
            if productRef:
                ref = str(productRef).strip()
                if ref.isdigit():
                    product_id = int(ref)
                else:
                    product = request.env["product.template"].sudo().search(
                        [("default_code", "=", ref)], limit=1
                    )
                    product_id = product.id if product else False
            record = request.env["alkaff.custom.request"].create({
                "alias": str(alias or "").strip(),
                "label_name": str(labelName or "").strip(),
                "consent_opt_in": consentOptIn is True,
                "theme_ref": str(themeRef or "").strip()[:80],
                "notes_aman": str(notesAman or "")[:1000],
                "bottle_type": bottleType if bottleType in ("rollon", "spray", "usap") else "spray",
                "product_ref": product_id or False,
                "intent": str(intent or "custom").strip()[:24],
                "reason": str(reason or "")[:1000],
            })
            return {"ok": True, "draft": _public(record)}
        except UserError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:  # pragma: no cover - dependensi DB
            return {"ok": False, "error": "GAGAL_MEMBUAT_DRAFT", "detail": str(exc)[:200]}

    @http.route(
        "/alkaff/api/custom-request/list",
        auth="user",
        type="jsonrpc",
        methods=["POST"],
        csrf=False,
    )
    def list_custom_requests(self, **kw):
        records = request.env["alkaff.custom.request"].search([], limit=50)
        return {"ok": True, "drafts": [_public(record) for record in records]}

    @http.route(
        "/alkaff/api/custom-request/review",
        auth="user",
        type="jsonrpc",
        methods=["POST"],
        csrf=False,
    )
    def review_custom_request(self, draftRef=None, action=None, reviewNote="", **kw):
        if action not in ("approve", "reject"):
            return {"ok": False, "error": "INVALID_ACTION"}
        record = request.env["alkaff.custom.request"].search(
            [("draft_ref", "=", str(draftRef or "").strip())], limit=1
        )
        if not record:
            return {"ok": False, "error": "DRAFT_NOT_FOUND"}
        try:
            if action == "approve":
                record.action_approve()
            else:
                if reviewNote:
                    record.write({"review_note": str(reviewNote)[:1000]})
                record.action_reject()
            return {"ok": True, "draft": _public(record)}
        except UserError as exc:
            return {"ok": False, "error": str(exc)}
