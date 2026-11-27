"""Endpoint baca-saja untuk web app theater Alkaff.

Bukan koneksi TikTok dan bukan auto-DM. Endpoint ini hanya membaca katalog
product.template dan bundle basis pengetahuan yang dibungkus dengan modul.
Harga mentah, supplier, dan data sensitif lain sengaja tidak dikembalikan.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from odoo import http
from odoo.http import request

_ALLOWED_ORIGIN = "https://alkaff.lokal.or.id"
_BUNDLE_PATH = Path(__file__).resolve().parent.parent / "data" / "pengetahuan-parfum.json"
_TOKEN_RE = re.compile(r"[^\w]+", re.UNICODE)
_ALIASES = {
    "kopi": ("kopi", "coffee"),
    "coffee": ("coffee", "kopi"),
    "dingin": ("dingin", "cold", "fresh"),
    "manis": ("manis", "sweet", "vanilla"),
    "vanila": ("vanila", "vanilla"),
    "bunga": ("bunga", "floral", "flower"),
    "kayu": ("kayu", "woody", "wood"),
}


def _tokens(value):
    """Tokenisasi keyword + sinonim Indonesia/Inggris untuk pencarian katalog."""
    result = []
    for token in _TOKEN_RE.split(str(value or "").lower()):
        if not token:
            continue
        for candidate in _ALIASES.get(token, (token,)):
            if candidate not in result:
                result.append(candidate)
    return result


def _load_bundle():
    with _BUNDLE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _pick_theme(bundle, keyword):
    """Pilih tema skor tertinggi dari token keyword. Fallback: CTA QUOTE."""
    tokens = _tokens(keyword)
    best, best_score = None, 0
    if tokens:
        for theme in bundle.get("tema", []):
            weighted_fields = (
                (theme.get("Tema"), 4),
                (theme.get("Notes Kunci"), 3),
                (theme.get("CTA"), 3),
                (theme.get("Keluarga"), 2),
                (theme.get("Trigger"), 1),
                (theme.get("Format"), 1),
                (theme.get("Persona"), 1),
                (theme.get("Momen"), 1),
            )
            score = 0
            for token in tokens:
                for value, weight in weighted_fields:
                    if token in str(value or "").lower():
                        score += weight
                        break
            if score > best_score:
                best, best_score = theme, score
    if best:
        return best
    return next(
        (t for t in bundle.get("tema", []) if t.get("CTA") == "QUOTE"),
        bundle.get("tema", [None])[0] if bundle.get("tema") else None,
    )


def _product_domain(theme, keyword):
    """Domain OR dari token keyword + notes tema, tanpa harga/supplier."""
    terms = []
    for value in (
        keyword or "",
        theme.get("Notes Kunci", "") if theme else "",
        theme.get("Keluarga", "") if theme else "",
    ):
        for token in _tokens(value):
            if token not in terms:
                terms.append(token)
    clauses = []
    for term in terms[:8]:
        clauses.extend([
            ("aroma_family", "ilike", term),
            ("notes_top", "ilike", term),
            ("notes_heart", "ilike", term),
            ("notes_base", "ilike", term),
            ("name", "ilike", term),
            ("default_code", "ilike", term),
        ])
    if not clauses:
        return []
    return ["|"] * (len(clauses) - 1) + clauses


def _score_product(product, primary_tokens, secondary_tokens):
    """Ranking sederhana: keyword lebih penting daripada notes tema."""
    fields = (
        (product.name, 6),
        (product.default_code, 4),
        (product.aroma_family, 3),
        (product.notes_top, 2),
        (product.notes_heart, 2),
        (product.notes_base, 2),
    )
    score = 0
    for token in primary_tokens:
        for value, weight in fields:
            if token in str(value or "").lower():
                score += weight
    for token in secondary_tokens:
        if token in primary_tokens:
            continue
        for value, _weight in fields:
            if token in str(value or "").lower():
                score += 1
                break
    return score


class AlkaffCatalogApi(http.Controller):
    @http.route(
        "/alkaff/api/health",
        auth="public",
        type="http",
        methods=["GET"],
        csrf=False,
        cors=_ALLOWED_ORIGIN,
    )
    def health(self, **kw):
        return request.make_json_response({
            "ok": True,
            "module": "alkaff_catalog",
            "database": request.env.cr.dbname,
        })

    @http.route(
        "/alkaff/api/themes",
        auth="public",
        type="http",
        methods=["GET"],
        csrf=False,
        cors=_ALLOWED_ORIGIN,
    )
    def themes(self, **kw):
        bundle = _load_bundle()
        rows = [
            {
                "tema": t.get("Tema"),
                "persona": t.get("Persona"),
                "notesKunci": t.get("Notes Kunci"),
                "ctaKeyword": t.get("CTA"),
                "format": t.get("Format"),
                "momen": t.get("Momen"),
                "risiko": t.get("Risiko"),
            }
            for t in bundle.get("tema", [])
        ]
        return request.make_json_response({"ok": True, "themes": rows})

    @http.route(
        "/alkaff/api/recommendations",
        auth="public",
        type="http",
        methods=["GET"],
        csrf=False,
        cors=_ALLOWED_ORIGIN,
    )
    def recommendations(self, keyword="", limit="6", **kw):
        try:
            limit = max(1, min(int(limit), 12))
        except (TypeError, ValueError):
            limit = 6
        bundle = _load_bundle()
        theme = _pick_theme(bundle, keyword)
        domain = _product_domain(theme, keyword)
        # Baca-saja untuk katalog publik; tidak mengembalikan harga/supplier.
        candidates = request.env["product.template"].sudo().search(domain, limit=200) if domain else []
        primary_tokens = _tokens(keyword)
        secondary_tokens = []
        for value in (
            theme.get("Notes Kunci", "") if theme else "",
            theme.get("Keluarga", "") if theme else "",
        ):
            for token in _tokens(value):
                if token not in secondary_tokens:
                    secondary_tokens.append(token)
        scored = [
            (_score_product(product, primary_tokens, secondary_tokens), product)
            for product in candidates
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        products = [product for _score, product in scored[:limit]]
        rows = [
            {
                "ref": p.default_code or "",
                "name": p.name or "",
                "family": p.aroma_family or "",
                "notesTop": p.notes_top or "",
                "notesHeart": p.notes_heart or "",
                "notesBase": p.notes_base or "",
            }
            for p in products
        ]
        return request.make_json_response({
            "ok": True,
            "keyword": keyword or "",
            "theme": {
                "tema": theme.get("Tema") if theme else "",
                "ctaKeyword": theme.get("CTA") if theme else "QUOTE",
                "notesKunci": theme.get("Notes Kunci") if theme else "",
                "risiko": theme.get("Risiko") if theme else "",
            } if theme else None,
            "products": rows,
            "batasan": "Notes adalah gambaran keluarga, bukan komposisi resmi pabrik. Harga/stok dicek di katalog saat LIVE.",
        })
