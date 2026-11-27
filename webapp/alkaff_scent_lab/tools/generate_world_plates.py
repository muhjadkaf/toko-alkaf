#!/usr/bin/env python3
"""Render ulang plate Alkaff Maklon Hall dengan tekstur industri + butik.

Plate TIDAK menyalin foto internet. Foto dipakai hanya sebagai referensi nuansa
(rak hangat, botol amber, stainless, pencahayaan butik); seluruh piksel dibuat
ulang secara prosedural dengan numpy + PIL.

Sengaja TANPA teks, logo, atau manusia. Semua teks diegetik ditambahkan Flutter
sebagai benda fisik (papan, monitor QC, kertas batch).

Jalankan:
    python3 tools/generate_world_plates.py
"""
from __future__ import annotations

import math
import os
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from texture_utils import (
    brushed_steel,
    concrete,
    epoxy,
    fbm,
    grain,
    radial_light,
    warm_wood,
)

W, H = 1920, 1080
VX, VY = 960, 500

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "world")
os.makedirs(OUT, exist_ok=True)

AMBER = (184, 116, 46)
BRASS = (176, 138, 70)
CREAM = (224, 202, 166)
STEEL = (126, 138, 133)
STEEL_DARK = (48, 57, 54)
INK = (11, 14, 12)


# ---------------------------------------------------------------------------
# Tekstur dasar (dibuat sekali, dipakai ulang oleh kelima scene)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=None)
def wall_texture():
    return concrete(W, H, 101, (63, 57, 49))


@lru_cache(maxsize=None)
def floor_texture():
    return epoxy(W, H, 202, (52, 53, 48))


@lru_cache(maxsize=None)
def steel_texture():
    return brushed_steel(W, H, 303, (127, 139, 134))


@lru_cache(maxsize=None)
def wood_texture():
    return warm_wood(W, H, 404, (113, 74, 43))


def paste_patch(img, texture, box, opacity=255):
    """Tempel potongan tekstur ke area tertentu tanpa garis kotak polos."""
    x0, y0, x1, y1 = (int(v) for v in box)
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)
    patch = texture.crop((0, 0, w, h)).convert("RGBA")
    if opacity != 255:
        patch.putalpha(opacity)
    img.alpha_composite(patch, (x0, y0))


def soft_light(img, center, radius, color, alpha):
    img.alpha_composite(radial_light(W, H, center, radius, color, alpha))


def vignette(img, strength=78):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = np.clip((d - 0.52) / 0.48, 0, 1) * strength
    layer = np.zeros((H, W, 4), dtype=np.uint8)
    layer[:, :, 0], layer[:, :, 1], layer[:, :, 2] = 8, 11, 9
    layer[:, :, 3] = a.astype(np.uint8)
    img.alpha_composite(Image.fromarray(layer, mode="RGBA"))


def grade(img, seed):
    """Warm grade + grain halus + vignette."""
    soft_light(img, (1460, 360), 900, (224, 166, 92), 26)
    soft_light(img, (380, 820), 620, (196, 122, 52), 18)
    g = grain(W, H, seed, 6).convert("RGBA")
    g.putalpha(9)
    img.alpha_composite(g)
    vignette(img)


# ---------------------------------------------------------------------------
# Material objects
# ---------------------------------------------------------------------------
@lru_cache(maxsize=128)
def bottle_tile(w, h, seed, family=0):
    """Botol amber: lima siluet, shading kaca silinder, label matte."""
    w, h = max(12, int(w)), max(28, int(h))
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x = xx / max(w - 1, 1)
    y = yy / max(h - 1, 1)

    bases = [(172, 96, 36), (146, 82, 34), (196, 132, 58), (158, 100, 40), (140, 88, 38)]
    base = np.array(bases[family % len(bases)], dtype=np.float32)
    inset = (0.0, 0.14, 0.06, 0.10, 0.02)[family % 5]
    nx = np.clip((x - inset) / max(1 - 2 * inset, 0.01), 0, 1)

    # Tepi gelap, pantulan specular di kiri, pantulan hangat di bawah
    shade = 0.50 + 0.55 * np.maximum(np.sin(nx * math.pi), 0.0) ** 1.3
    shade += 0.20 * np.exp(-((nx - 0.24) / 0.10) ** 2)
    shade += 0.08 * (1 - y)
    arr = np.empty((h, w, 4), dtype=np.float32)
    for ch in range(3):
        arr[:, :, ch] = np.clip(base[ch] * shade + rng.normal(0, 1.1, (h, w)), 0, 255)
    arr[:, :, 3] = 255

    # Leher kaca dan tutup logam
    neck_w = max(3, int(w * (0.24 if family % 2 else 0.32)))
    neck_h = max(5, int(h * 0.16))
    cap_h = max(4, int(h * 0.08))
    cx0, cx1 = (w - neck_w) // 2, (w + neck_w) // 2
    arr[:neck_h, cx0:cx1, :3] = np.array([104, 78, 42])
    arr[:cap_h, max(0, cx0 - 1):min(w, cx1 + 1), :3] = np.array([72, 78, 72])
    arr[cap_h:cap_h + 2, cx0:cx1, :3] += 34

    # Label matte dengan dua goresan halus (bukan teks)
    ly0, ly1 = int(h * 0.44), int(h * 0.70)
    lx0, lx1 = int(w * (0.12 + inset * 0.4)), int(w * (0.88 - inset * 0.4))
    arr[ly0:ly1, lx0:lx1, :3] = np.array([222, 212, 190])
    arr[ly0 + 4:ly0 + 7, lx0 + 5:max(lx0 + 6, lx1 - 5), :3] = np.array([142, 128, 100])
    arr[ly0 + 11:ly0 + 13, lx0 + 5:max(lx0 + 6, lx1 - 12), :3] = np.array([158, 146, 118])

    hx = int(w * (0.20 + inset * 0.3))
    arr[neck_h:h - 4, hx:hx + max(2, w // 12), :3] += 30
    arr[neck_h:h - 6, int(w * 0.86):max(int(w * 0.86) + 1, int(w * 0.94)), :3] *= 0.72

    img = Image.fromarray(arr.astype(np.uint8), mode="RGBA")
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    bx0, bx1 = int(w * inset), w - 1 - int(w * inset)
    md.rounded_rectangle([bx0, cap_h, bx1, h - 1],
                         radius=max(3, int(w * (0.10 if family % 2 else 0.20))), fill=255)
    md.rectangle([cx0, 0, cx1, cap_h], fill=255)
    img.putalpha(mask)
    return img


def place_bottle(img, cx, base, scale=1.0, seed=1, family=0):
    w = max(10, int(30 * scale))
    h = max(28, int(92 * scale))
    tile = bottle_tile(w, h, seed, family)
    shadow = Image.new("RGBA", (w + 14, 10), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([4, 1, w + 10, 9], fill=(0, 0, 0, 70))
    img.alpha_composite(shadow, (cx - w // 2 - 4, base - 4))
    img.alpha_composite(tile, (cx - w // 2, base - h))


def shelf(img, box, rows=3, cols=7, seed=1, blur=0, warm=True):
    """Rak butik dengan kayu/kuningan dan deretan botol amber."""
    x, y, w, h = (int(v) for v in box)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")

    # Backing kayu bertekstur
    backing = wood_texture().crop((0, 0, w, h)).convert("RGBA")
    if not warm:
        steel = steel_texture().crop((0, 0, w, h)).convert("RGBA")
        backing = Image.blend(backing, steel, 0.55).convert("RGBA")
    backing.putalpha(235)
    layer.alpha_composite(backing, (x, y))

    # Rak dan rel kuningan
    row_h = h / rows
    for r in range(rows + 1):
        sy = int(y + r * row_h)
        plank = wood_texture().crop((7 * r, 30 * r, 7 * r + w, 30 * r + 16)).convert("RGBA")
        plank.putalpha(245)
        layer.alpha_composite(plank, (x, sy))
        d.line([(x, sy), (x + w, sy)], fill=BRASS + (150,), width=3)
        d.line([(x, sy + 13), (x + w, sy + 13)], fill=(28, 26, 20, 120), width=3)

    # Botol-botol dengan variasi tinggi dan keluarga warna
    rng = random.Random(seed)
    for r in range(rows):
        sy = int(y + (r + 1) * row_h) - 8
        for c in range(cols):
            cx = x + int((c + 0.5) * w / cols) + rng.randint(-4, 4)
            base = sy + rng.randint(-3, 2)
            scale = rng.uniform(0.68, 1.06)
            place_bottle(layer, cx, base, scale, seed * 100 + r * 13 + c,
                         family=(r * 3 + c * 2 + seed) % 5)

    # Kilau hangat pada rak
    layer.alpha_composite(
        radial_light(W, H, (x + w // 2, y + h // 2), w * 0.7, (238, 186, 108), 22)
    )
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def drum(img, cx, base, scale=1.0, seed=1):
    """Drum stainless: silinder bergradasi, tutup berimping, bung, label."""
    w = int(100 * scale)
    h = int(200 * scale)
    top = base - h
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")

    patch = steel_texture().crop((seed * 13 % 400, seed * 7 % 400,
                                  seed * 13 % 400 + w, seed * 7 % 400 + h)).convert("RGBA")
    pa = np.asarray(patch, dtype=np.float32).copy()
    nx = np.arange(w, dtype=np.float32) / max(w - 1, 1)
    shade = 0.56 + 0.50 * np.maximum(np.sin(nx * math.pi), 0.0) ** 1.2
    shade += 0.16 * np.exp(-((nx - 0.22) / 0.10) ** 2)
    pa[:, :, :3] = np.clip(pa[:, :, :3] * shade[None, :, None], 0, 255)
    patch = Image.fromarray(pa.astype(np.uint8), "RGBA")

    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 6, w - 1, h - 1], radius=int(w * 0.12), fill=255)
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    body.paste(patch, (0, 0))
    body.putalpha(mask)
    layer.alpha_composite(body, (cx - w // 2, top))

    # Tutup dengan imping dan bung
    d.ellipse([cx - w // 2, top - 8 * scale, cx + w // 2, top + 14 * scale],
              fill=(186, 196, 190, 255), outline=(36, 44, 40, 255),
              width=max(2, int(3 * scale)))
    d.ellipse([cx - w // 2 + 8, top - 4, cx + w // 2 - 8, top + 9],
              outline=(232, 240, 234, 120), width=2)
    d.ellipse([cx + w * 0.18, top + 1, cx + w * 0.18 + 12 * scale, top + 9 * scale],
              fill=(92, 102, 96, 255), outline=(38, 46, 42, 255), width=2)

    # Rusuk dengan kilau tipis
    for k in (1, 2, 3):
        ry = top + k * h / 4
        d.line([(cx - w // 2 + 3, ry), (cx + w // 2 - 3, ry)],
               fill=(32, 40, 36, 150), width=max(3, int(6 * scale)))
        d.line([(cx - w // 2 + 3, ry - 3), (cx + w // 2 - 3, ry - 3)],
               fill=(226, 234, 228, 80), width=2)

    # Label matte melingkar, tanpa tulisan terbaca
    ly = top + int(h * 0.40)
    d.rectangle([cx - w // 2 + 1, ly, cx + w // 2 - 1, ly + int(h * 0.22)],
                fill=(176, 168, 146, 225))
    d.rectangle([cx - w // 2 + 8, ly + 8, cx + w // 2 - 22, ly + 12],
                fill=(96, 88, 68, 220))

    d.ellipse([cx - w // 2 + 8, base - 12, cx + w // 2 - 8, base + 8],
              fill=(22, 28, 25, 170))
    img.alpha_composite(layer)


def pallet(img, cx, base, seed=1):
    """Palet kayu dengan tekstur, bukan kotak polos."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    w, h = 220, 30
    patch = wood_texture().crop((seed * 17 % 500, seed * 11 % 500,
                                 seed * 17 % 500 + w, seed * 11 % 500 + h)).convert("RGBA")
    layer.alpha_composite(patch, (cx - w // 2, base - h))
    d = ImageDraw.Draw(layer, "RGBA")
    for i in range(4):
        x = cx - w // 2 + i * 58
        d.rectangle([x, base - h - 14, x + 34, base - h], fill=(70, 52, 34, 220))
    img.alpha_composite(layer)


def tank(img, cx, base_y, w, h, seed=1, detail=True):
    """Tangki berjaket: tekstur stainless, leher, gauge, katup, pipa."""
    top = base_y - h
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")

    body_top = top + int(w * 0.16)
    body_box = (cx - w // 2, body_top, cx + w // 2, base_y)
    patch = steel_texture().crop((seed * 29 % 600, seed * 19 % 600,
                                  seed * 29 % 600 + w, seed * 19 % 600 + h)).convert("RGBA")
    pa = np.asarray(patch, dtype=np.float32).copy()
    nx = np.arange(w, dtype=np.float32) / max(w - 1, 1)
    shade = 0.58 + 0.48 * np.maximum(np.sin(nx * math.pi), 0.0) ** 1.3
    shade += 0.14 * np.exp(-((nx - 0.24) / 0.09) ** 2)
    pa[:, :, :3] = np.clip(pa[:, :, :3] * shade[None, :, None], 0, 255)
    patch = Image.fromarray(pa.astype(np.uint8), "RGBA")

    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, w - 1, int(w * 0.34)], fill=255)
    md.rectangle([0, int(w * 0.17), w - 1, h - int(w * 0.12)], fill=255)
    md.ellipse([0, h - int(w * 0.24), w - 1, h - 1], fill=255)
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    body.paste(patch, (0, 0))
    body.putalpha(mask)
    layer.alpha_composite(body, (cx - w // 2, top))

    # Kilau sempit mengikuti silinder, bukan kotak terang
    sx = cx - int(w * 0.26)
    d.rounded_rectangle([
        sx - max(3, w // 20), body_top + 14,
        sx + max(3, w // 20), base_y - 28],
        radius=max(2, w // 40), fill=(244, 250, 244, 52))
    d.rectangle([cx + int(w * 0.34), body_top + 14,
                 cx + int(w * 0.44), base_y - 28], fill=(10, 16, 13, 62))
    for yy in (body_top + 48, base_y - 78):
        d.line([(cx - w // 2 + 6, yy), (cx + w // 2 - 6, yy)], fill=(38, 46, 43, 190), width=12)
        d.line([(cx - w // 2 + 6, yy - 5), (cx + w // 2 - 6, yy - 5)],
               fill=(220, 230, 224, 55), width=2)

    # Tutup elips dengan kilau
    d.ellipse([cx - w // 2, top, cx + w // 2, top + int(w * 0.34)],
              outline=(232, 240, 234, 110), width=4)

    # Kaki, katup, gauge
    for dx in (-w // 3, w // 3):
        d.rectangle([cx + dx - 10, base_y - 6, cx + dx + 10, base_y + 46],
                    fill=(42, 50, 47, 255))
    d.line([(cx, top + 6), (cx, top - 44)], fill=(156, 168, 162, 255), width=max(6, w // 18))
    d.ellipse([cx - 26, top - 62, cx + 26, top - 30], fill=BRASS + (255,),
              outline=(68, 56, 32, 255), width=3)

    if detail:
        gr = max(30, int(w * 0.16))
        gx, gy = cx + w // 3, body_top + gr + 54
        d.line([(gx, gy + gr), (gx, gy + gr + 26)],
               fill=(126, 138, 132, 255), width=max(6, gr // 3))
        d.ellipse([gx - gr - 4, gy - gr - 4, gx + gr + 4, gy + gr + 4],
                  fill=(196, 206, 198, 255), outline=(38, 46, 42, 255), width=5)
        d.ellipse([gx - gr + 3, gy - gr + 3, gx + gr - 3, gy + gr - 3],
                  fill=(238, 238, 224, 255), outline=(96, 106, 100, 255), width=2)
        for i in range(11):
            a = math.radians(-210 + i * 24)
            r0 = gr - 12
            r1 = gr - (5 if i % 2 == 0 else 9)
            d.line([(gx + math.cos(a) * r0, gy + math.sin(a) * r0),
                    (gx + math.cos(a) * r1, gy + math.sin(a) * r1)],
                   fill=(56, 64, 60, 255), width=2 if i % 2 == 0 else 1)
        a = math.radians(-58)
        d.line([(gx, gy), (gx + math.cos(a) * (gr - 12), gy + math.sin(a) * (gr - 12))],
               fill=(24, 30, 27, 255), width=max(3, gr // 10))
        d.ellipse([gx - 5, gy - 5, gx + 5, gy + 5], fill=(70, 78, 73, 255))
    img.alpha_composite(layer)


def pipe(img, points, width=18, seed=1):
    """Pipa stainless: bayangan, gradasi logam, flange, dan katup roda."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.line(points, fill=(12, 18, 15, 230), width=width + 10, joint="curve")
    d.line(points, fill=(88, 100, 94, 255), width=width + 3, joint="curve")
    d.line(points, fill=(156, 168, 162, 255), width=width, joint="curve")
    off = [(x, y - max(3, width // 4)) for x, y in points]
    d.line(off, fill=(240, 246, 240, 90), width=max(3, width // 4), joint="curve")

    joints = list(points)
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if math.hypot(x2 - x1, y2 - y1) > 220:
            joints.append(((x1 + x2) / 2, (y1 + y2) / 2))
    for x, y in joints:
        r = width * 0.82
        d.ellipse([x - r, y - r, x + r, y + r], fill=(178, 188, 182, 255),
                  outline=(44, 52, 48, 255), width=3)
        d.ellipse([x - r * 0.55, y - r * 0.55, x + r * 0.55, y + r * 0.55],
                  fill=(120, 132, 126, 255))

    if len(points) >= 2:
        (x1, y1), (x2, y2) = max(
            zip(points, points[1:]),
            key=lambda p: math.hypot(p[1][0] - p[0][0], p[1][1] - p[0][1]),
        )
        vx, vy = x1 * 0.62 + x2 * 0.38, y1 * 0.62 + y2 * 0.38
        vr = max(16, width)
        d.ellipse([vx - vr, vy - vr, vx + vr, vy + vr],
                  outline=(186, 154, 74, 255), width=5)
        for a in range(0, 180, 45):
            rad = math.radians(a)
            d.line([(vx - math.cos(rad) * vr, vy - math.sin(rad) * vr),
                    (vx + math.cos(rad) * vr, vy + math.sin(rad) * vr)],
                   fill=(176, 146, 70, 230), width=3)
        d.ellipse([vx - 6, vy - 6, vx + 6, vy + 6], fill=(72, 78, 72, 255))
    img.alpha_composite(layer)


def catwalk(img, y, x0, x1, scale=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    h = int(18 * scale)
    patch = steel_texture().crop((0, int(y), x1 - x0, int(y) + h)).convert("RGBA")
    patch.putalpha(245)
    layer.alpha_composite(patch, (x0, int(y)))
    rail_y = int(y - 72 * scale)
    d.line([(x0, rail_y), (x1, rail_y)], fill=(214, 222, 216, 235), width=6)
    for x in range(x0, x1 + 1, int(130 * scale)):
        d.line([(x, y), (x, rail_y)], fill=(148, 160, 154, 225), width=4)
    img.alpha_composite(layer)


def syringe(img, x, y, scale=1.0, angle=0):
    """Suntikan mikroliter: barrel kaca, plunger, gradasi, jarum bevel."""
    tile = Image.new("RGBA", (int(230 * scale), int(76 * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile, "RGBA")
    s = scale
    cy = 38 * s
    d.line([(176 * s, cy), (226 * s, cy)],
           fill=(196, 206, 198, 210), width=max(1, int(2 * s)))
    d.line([(226 * s, cy), (230 * s, cy - 2 * s)],
           fill=(228, 234, 228, 220), width=max(1, int(2 * s)))
    d.rounded_rectangle([62 * s, cy - 16 * s, 178 * s, cy + 16 * s], radius=6 * s,
                        fill=(206, 218, 210, 150), outline=(46, 56, 50, 255),
                        width=max(2, int(3 * s)))
    d.rectangle([66 * s, cy - 10 * s, 150 * s, cy + 10 * s], fill=(178, 108, 40, 190))
    d.line([(70 * s, cy - 11 * s), (150 * s, cy - 11 * s)],
           fill=(244, 220, 170, 180), width=max(1, int(2 * s)))
    for i in range(6):
        gx = (78 + i * 14) * s
        d.line([(gx, cy - 15 * s), (gx, cy - (7 if i % 2 else 4) * s)],
               fill=(40, 48, 44, 230), width=max(1, int(2 * s)))
    d.line([(10 * s, cy), (64 * s, cy)],
           fill=(150, 162, 156, 255), width=max(3, int(6 * s)))
    d.rectangle([6 * s, cy - 14 * s, 16 * s, cy + 14 * s], fill=(64, 72, 67, 255))
    d.rectangle([52 * s, cy - 12 * s, 64 * s, cy + 12 * s], fill=(82, 92, 86, 255))
    tile = tile.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    img.alpha_composite(tile, (int(x - tile.width / 2), int(y - tile.height / 2)))


def pipette(img, x, y, scale=1.0, angle=0):
    """Pipet kaca dengan bola karet dan ujung runcing."""
    tile = Image.new("RGBA", (int(180 * scale), int(48 * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile, "RGBA")
    s = scale
    cy = 24 * s
    d.ellipse([6 * s, cy - 14 * s, 52 * s, cy + 14 * s],
              fill=(126, 78, 40, 255), outline=(56, 44, 30, 255), width=max(2, int(3 * s)))
    d.ellipse([12 * s, cy - 10 * s, 30 * s, cy - 2 * s], fill=(172, 116, 62, 150))
    d.line([(52 * s, cy), (130 * s, cy)],
           fill=(216, 226, 218, 230), width=max(2, int(4 * s)))
    d.line([(130 * s, cy), (174 * s, cy)],
           fill=(180, 190, 184, 255), width=max(1, int(2 * s)))
    d.line([(174 * s, cy), (180 * s, cy)], fill=(236, 242, 236, 255), width=1)
    tile = tile.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    img.alpha_composite(tile, (int(x - tile.width / 2), int(y - tile.height / 2)))


def vial(img, x, base, scale=1.0, seed=1):
    w = int(24 * scale)
    h = int(70 * scale)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([x - w // 2, base - h, x + w // 2, base], radius=4 * scale,
                        fill=(206, 216, 208, 165), outline=(40, 50, 45, 255), width=2)
    d.rectangle([x - w // 2 + 3, base - int(h * 0.62), x + w // 2 - 3, base - 3],
                fill=(AMBER[0], AMBER[1], AMBER[2], 210))
    d.line([(x - w // 2 + 3, base - int(h * 0.62)), (x + w // 2 - 3, base - int(h * 0.62))],
           fill=(232, 190, 120, 220), width=2)
    d.rectangle([x - w // 2 - 2, base - h - 8 * scale, x + w // 2 + 2, base - h + 2],
                fill=(64, 72, 67, 255))
    d.line([(x - w // 3, base - h + 6), (x - w // 3, base - 8)],
           fill=(245, 248, 242, 150), width=2)


def vial_rack(img, x, y, w, h, n=6):
    """Rak logam berlubang untuk vial, bukan kotak polos."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle([x, y, x + w, y + h], radius=10,
                        fill=(48, 56, 52, 235), outline=(150, 162, 155, 255), width=3)
    for i in range(n):
        cx = x + int((i + 0.5) * w / n)
        d.ellipse([cx - 13, y + 6, cx + 13, y + 20],
                  fill=(14, 20, 17, 255), outline=(118, 130, 124, 255), width=2)
    img.alpha_composite(layer)


def qc_bench(img, box, seed=1, blur=0):
    """Meja QC: rak vial, timbangan, suntikan, dan pipet yang jelas terlihat."""
    x, y, w, h = (int(v) for v in box)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    patch = steel_texture().crop((seed * 23 % 500, seed * 17 % 500,
                                  seed * 23 % 500 + w, seed * 17 % 500 + h)).convert("RGBA")
    patch.putalpha(250)
    layer.alpha_composite(patch, (x, y))
    d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle([x, y, x + w, y + h], radius=16,
                        outline=(236, 242, 236, 90), width=4)
    d.rectangle([x + 20, y + h, x + w - 20, y + h + 26], fill=(10, 14, 12, 120))

    # Mat gelap agar siluet kaca alat QC kontras di layar LIVE
    d.rounded_rectangle([x + w * 0.38, y + h * 0.18, x + w * 0.86, y + h * 0.86],
                        radius=22, fill=(26, 34, 30, 175),
                        outline=(150, 162, 154, 150), width=3)

    # Dua rak vial berisi delapan sampel
    rack_w = min(430, int(w * 0.28))
    for r, rx in enumerate((x + 40, x + 40 + rack_w + 46)):
        vial_rack(layer, rx, y + h - 96, rack_w, 76, n=4)
        for i in range(4):
            cx = rx + int((i + 0.5) * rack_w / 4)
            vial(layer, cx, y + h - 74, 1.25, seed + r * 10 + i)

    # Timbangan digital dengan penutup kaca
    sx = x + w * 0.30
    d.rectangle([sx - 94, y + h - 206, sx + 94, y + h - 150],
                fill=(186, 200, 192, 55), outline=(150, 162, 155, 180), width=2)
    d.rounded_rectangle([sx - 90, y + h - 150, sx + 90, y + h - 96], radius=10,
                        fill=(54, 62, 58, 255), outline=(160, 172, 164, 255), width=3)
    d.rectangle([sx - 60, y + h - 138, sx + 60, y + h - 112], fill=(16, 30, 24, 255))
    d.rectangle([sx - 40, y + h - 132, sx + 30, y + h - 126], fill=(118, 206, 150, 220))

    # Alat QC utama di atas mat
    syringe(layer, x + w * 0.57, y + h * 0.44, 2.15, -12)
    syringe(layer, x + w * 0.66, y + h * 0.74, 1.65, 7)
    pipette(layer, x + w * 0.44, y + h * 0.62, 1.95, -25)

    layer.alpha_composite(
        radial_light(W, H, (x + w * 0.62, y + h * 0.24), w * 0.45, (246, 190, 108), 30)
    )
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def conveyor(img, box, seed=1):
    """Conveyor dengan sabuk bertekstur, roller elips, dan botol finished."""
    x, y, w, h = (int(v) for v in box)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.polygon([(x, y), (x + w, y), (x + w - 90, y + h), (x + 90, y + h)],
              fill=(42, 50, 46, 255))
    patch = steel_texture().crop((0, 200, w, 200 + h // 2)).convert("RGBA")
    patch.putalpha(115)
    layer.alpha_composite(patch, (x, y))
    # Rel samping yang memantulkan cahaya hangat
    d.line([(x, y + 6), (x + 90, y + h - 6)], fill=(186, 196, 188, 165), width=8)
    d.line([(x + w, y + 6), (x + w - 90, y + h - 6)], fill=(186, 196, 188, 165), width=8)
    # Roller berbentuk elips, bukan garis diagonal berulang
    for i in range(9):
        t = (i + 0.5) / 9
        rx = x + 70 + t * (w - 160)
        ry = y + h - 18 - t * 12
        d.ellipse([rx - 22, ry - 6, rx + 22, ry + 6],
                  fill=(26, 32, 29, 150), outline=(120, 132, 126, 110), width=2)
    for i, cx in enumerate(range(x + 150, x + w - 130, 200)):
        place_bottle(layer, cx, y + h - 54, 1.12, seed * 50 + i, family=i % 5)
    img.alpha_composite(layer)


def room_base(img, seed, floor_top=VY, warm=1.0):
    """Dinding beton + lantai epoksi bertekstur, bukan grid generik."""
    paste_patch(img, wall_texture(), (0, 0, W, floor_top), 245)
    paste_patch(img, floor_texture(), (0, floor_top, W, H), 250)

    # Bayangan vertikal halus pada dinding dan lantai
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade, "RGBA")
    sd.rectangle([0, floor_top - 120, W, floor_top], fill=(12, 16, 14, 90))
    sd.rectangle([0, H - 170, W, H], fill=(8, 11, 9, 110))
    img.alpha_composite(shade)

    # Silau lantai dari lampu toko
    soft_light(img, (W * 0.72, floor_top + 240), 760, (226, 168, 90), 26 * warm)
    soft_light(img, (W * 0.22, floor_top + 430), 620, (196, 132, 66), 18 * warm)

    # Jalur keselamatan yang sudah aus, bukan garis neon
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(int(W * 0.10), H), (VX - 210, floor_top + 60),
               (VX - 188, floor_top + 60), (int(W * 0.14), H)],
              fill=(198, 150, 58, 72))
    d.polygon([(int(W * 0.90), H), (VX + 210, floor_top + 60),
               (VX + 188, floor_top + 60), (int(W * 0.86), H)],
              fill=(198, 150, 58, 72))


def high_bay(img, x, y, scale=1.0, warm=True):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    w = int(140 * scale)
    d.polygon([(x - w, y - 16), (x + w, y - 16), (x + w // 2, y + 12), (x - w // 2, y + 12)],
              fill=(58, 66, 61, 255))
    color = (248, 214, 156, 230) if warm else (226, 236, 226, 210)
    d.ellipse([x - w // 3, y + 6, x + w // 3, y + 20], fill=color)
    layer.alpha_composite(
        radial_light(W, H, (x, y + 20), 280 * scale,
                     (238, 190, 116) if warm else (224, 232, 220), 38)
    )
    img.alpha_composite(layer)


def new_canvas():
    return Image.new("RGBA", (W, H), INK + (255,))


# ---------------------------------------------------------------------------
# Lima scene
# ---------------------------------------------------------------------------
def scene_boot():
    """Showroom hangat: rak parfum di kiri/kanan, pintu produksi di tengah."""
    img = new_canvas()
    room_base(img, 11, floor_top=520, warm=1.2)
    high_bay(img, 470, 190, 1.05)
    high_bay(img, 1450, 190, 1.05)

    shelf(img, (70, 220, 540, 600), rows=4, cols=6, seed=11, blur=2.2)
    shelf(img, (1330, 180, 520, 470), rows=4, cols=7, seed=12, blur=2.2)

    # Jaringan pipa di belakang pintu memberi kesan fasilitas besar
    pipe(img, [(110, 250), (630, 250), (630, 200), (1290, 200),
               (1290, 260), (1830, 260)], 14, seed=5)

    # Pintu produksi stainless di tengah, dengan bayangan dan panel
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    patch = steel_texture().crop((300, 120, 300 + 520, 120 + 470)).convert("RGBA")
    patch.putalpha(240)
    layer.alpha_composite(patch, (700, 180))
    d.rectangle([700, 180, 1220, 650], outline=(58, 66, 62, 255), width=10)
    d.line([(960, 180), (960, 650)], fill=(220, 230, 224, 90), width=5)
    d.rectangle([748, 566, 1172, 600], fill=(178, 138, 60, 110))
    d.rounded_rectangle([1150, 380, 1176, 452], radius=8,
                        fill=(196, 206, 198, 255), outline=(48, 56, 52, 255), width=3)
    img.alpha_composite(layer)

    # Tangki jauh memberi skala pabrik, ukuran tidak simetris
    tank(img, 210, 790, 170, 340, seed=3, detail=False)
    tank(img, 1710, 820, 200, 380, seed=4, detail=False)
    catwalk(img, 430, 120, 1800, 0.9)

    # Plinth butik dengan satu botol hero memecah simetri ruang
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.rounded_rectangle([250, 860, 470, 1010], radius=10,
                        fill=(38, 42, 38, 255), outline=(176, 138, 70, 200), width=4)
    d.ellipse([250, 850, 470, 880], fill=(58, 62, 55, 255),
              outline=(186, 148, 76, 180), width=3)
    place_bottle(layer, 360, 852, 2.4, 7, family=2)
    img.alpha_composite(layer)

    soft_light(img, (960, 470), 640, (222, 170, 96), 30)
    grade(img, 11)
    return img


def scene_scan():
    """Penerimaan bahan: drum, palet, rak hangat, dan meja sampel."""
    img = new_canvas()
    room_base(img, 22, floor_top=510, warm=1.1)
    high_bay(img, 520, 210, 1.0)
    high_bay(img, 1430, 210, 1.0)

    shelf(img, (60, 200, 520, 560), rows=3, cols=6, seed=21, blur=3.2, warm=False)
    shelf(img, (1400, 170, 460, 420), rows=4, cols=6, seed=22, blur=3.2)

    pallet(img, 270, 770, seed=2)
    drum(img, 220, 740, 0.95, seed=2)
    drum(img, 320, 740, 0.95, seed=5)
    pallet(img, 1630, 770, seed=7)
    drum(img, 1580, 740, 0.95, seed=8)
    drum(img, 1680, 740, 0.95, seed=9)

    # Drum di tengah mengisi area yang sebelumnya kosong
    pallet(img, 960, 680, seed=12)
    drum(img, 930, 650, 0.72, seed=13)
    drum(img, 1000, 650, 0.72, seed=14)

    qc_bench(img, (480, 690, 1260, 250), seed=22, blur=0)
    pipe(img, [(90, 340), (520, 340), (520, 280), (1380, 280),
               (1380, 360), (1840, 360)], 18, seed=6)
    pipe(img, [(230, 620), (230, 672), (740, 672)], 14, seed=7)
    soft_light(img, (1180, 690), 520, (232, 178, 104), 34)
    grade(img, 22)
    return img


def scene_mix():
    """Blending hall stainless dengan cahaya hangat high-bay."""
    img = new_canvas()
    room_base(img, 33, floor_top=520, warm=1.15)
    high_bay(img, 480, 180, 1.12)
    high_bay(img, 1440, 180, 1.12)

    tank(img, 250, 900, 300, 560, seed=31, detail=True)
    tank(img, 650, 760, 210, 420, seed=32, detail=True)
    tank(img, 930, 690, 150, 330, seed=33, detail=False)
    tank(img, 1220, 690, 150, 330, seed=34, detail=False)
    tank(img, 1600, 900, 300, 560, seed=35, detail=True)

    catwalk(img, 470, 100, 1820, 1.1)
    pipe(img, [(80, 360), (520, 360), (520, 300), (1420, 300), (1420, 390), (1840, 390)],
         18, seed=2)
    pipe(img, [(250, 520), (250, 610), (650, 610), (650, 540)], 14, seed=3)
    pipe(img, [(1600, 520), (1600, 620), (1220, 620)], 14, seed=4)

    # Etalase butik di foreground kiri memecah simetri lini stainless
    shelf(img, (-60, 610, 290, 320), rows=3, cols=4, seed=36, blur=1.4)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    patch = steel_texture().crop((700, 300, 700 + 340, 300 + 190)).convert("RGBA")
    patch.putalpha(240)
    layer.alpha_composite(patch, (1470, 690))
    d.rounded_rectangle([1470, 690, 1810, 880], radius=14,
                        outline=(232, 240, 234, 100), width=4)
    for x in range(1510, 1790, 70):
        d.ellipse([x, 730, x + 34, 764], fill=(210, 220, 214, 230),
                  outline=(50, 58, 54, 255), width=3)
        d.line([(x + 17, 747), (x + 28, 736)], fill=(44, 52, 48, 255), width=3)
    img.alpha_composite(layer)

    # Cove light hangat di dinding mengimbangi stainless yang dingin
    soft_light(img, (960, 300), 900, (222, 160, 82), 30)
    soft_light(img, (960, 520), 620, (210, 156, 92), 26)
    grade(img, 33)
    return img


def scene_analyze():
    """QC close-up: vial, pipet, dan suntikan jelas di meja stainless."""
    img = new_canvas()
    room_base(img, 44, floor_top=500, warm=1.2)

    # Hall produksi di latar tanpa bingkai kotak, ditutup haze tipis
    for i, cx in enumerate((250, 520, 1370, 1630)):
        tank(img, cx, 570, 116, 250, seed=45 + i, detail=False)
    img.alpha_composite(Image.new("RGBA", (W, H), (52, 46, 36, 42)))

    # Rak produksi blur memberi kedalaman
    shelf(img, (60, 130, 900, 510), rows=3, cols=8, seed=41, blur=4.5, warm=False)
    shelf(img, (1020, 130, 840, 380), rows=3, cols=8, seed=42, blur=4.5)

    qc_bench(img, (90, 690, 1740, 250), seed=44, blur=0)

    # Tepi meja depan dan vial blur mengisi bagian bawah frame
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.rectangle([0, 980, W, H], fill=(36, 42, 38, 240))
    d.line([(0, 980), (W, 980)], fill=(180, 190, 182, 120), width=4)
    for cx in (180, 420, 1500, 1740):
        d.rounded_rectangle([cx - 18, 900, cx + 18, 1010], radius=6,
                            fill=(150, 92, 36, 190))
        d.rectangle([cx - 20, 894, cx + 20, 908], fill=(60, 68, 63, 255))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(3)))

    # Monitor QC fisik: bezel logam, grafik abstrak, dan dudukan nyata
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(layer, "RGBA")
    md.rounded_rectangle([1200, 420, 1760, 680], radius=16,
                         fill=(46, 54, 50, 255), outline=(176, 186, 178, 255), width=8)
    md.rectangle([1230, 450, 1730, 650], fill=(10, 20, 17, 255))
    for i in range(9):
        bx = 1250 + i * 52
        by = 610 - int(28 * abs(math.sin(i * 0.9 + 0.4)))
        md.rounded_rectangle([bx, by, bx + 26, 612], radius=3, fill=(126, 168, 132, 150))
    md.line([(1250, 590), (1270, 564), (1290, 578), (1310, 540), (1330, 556),
             (1350, 520), (1370, 536), (1390, 500), (1410, 518)],
            fill=(224, 176, 96, 220), width=3)
    md.ellipse([1680, 468, 1696, 484], fill=(196, 148, 72, 255))
    md.rectangle([1440, 680, 1520, 726], fill=(52, 60, 56, 255))
    md.rounded_rectangle([1380, 726, 1580, 742], radius=6, fill=(110, 122, 116, 255))
    img.alpha_composite(layer)

    soft_light(img, (1450, 560), 430, (100, 156, 136), 16)
    soft_light(img, (420, 760), 360, (232, 176, 96), 28)
    grade(img, 44)
    return img


def scene_result():
    """Filling + rak butik: mesin isi/label dikenali, conveyor, botol jadi."""
    img = new_canvas()
    room_base(img, 55, floor_top=520, warm=1.25)
    high_bay(img, 500, 200, 1.0)
    high_bay(img, 1420, 200, 1.0)

    shelf(img, (90, 230, 650, 610), rows=3, cols=6, seed=51, blur=3.4)
    shelf(img, (1300, 200, 550, 440), rows=4, cols=7, seed=52, blur=3.4)

    # Mesin isi/label: hopper, empat nozzle, botol, panel, dan rol label
    for idx, (cx, top, scale) in enumerate(((600, 420, 1.0), (1310, 460, 0.92))):
        w = int(300 * scale)
        h = int(270 * scale)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer, "RGBA")
        patch = steel_texture().crop((100 + idx * 40, 250,
                                      100 + idx * 40 + w, 250 + h)).convert("RGBA")
        pa = np.asarray(patch, dtype=np.float32).copy()
        nx = np.arange(w, dtype=np.float32) / max(w - 1, 1)
        sh = 0.58 + 0.48 * np.maximum(np.sin(nx * math.pi), 0.0) ** 1.3
        sh += 0.14 * np.exp(-((nx - 0.24) / 0.10) ** 2)
        pa[:, :, :3] = np.clip(pa[:, :, :3] * sh[None, :, None], 0, 255)
        patch = Image.fromarray(pa.astype(np.uint8), "RGBA")
        layer.alpha_composite(patch, (cx - w // 2, top))
        d.rounded_rectangle([cx - w // 2, top, cx + w // 2, top + h], radius=12,
                            outline=(226, 234, 228, 110), width=4)
        d.polygon([(cx - 46, top), (cx + 46, top),
                   (cx + 28, top + 50), (cx - 28, top + 50)],
                  fill=(150, 162, 156, 255), outline=(48, 56, 52, 255))
        for k in range(4):
            nx_ = cx - w // 2 + 50 + k * (w - 100) // 3
            d.rectangle([nx_ - 5, top + 60, nx_ + 5, top + 126],
                        fill=(190, 200, 194, 255))
            d.ellipse([nx_ - 8, top + 120, nx_ + 8, top + 134],
                      fill=(108, 120, 114, 255))
            place_bottle(layer, nx_, top + h - 24, 0.60, 500 + idx * 10 + k,
                         family=k % 5)
        d.rectangle([cx - w // 2 + 16, top + 150, cx - w // 2 + 96, top + 206],
                    fill=(26, 34, 30, 240), outline=(150, 162, 155, 255), width=3)
        d.ellipse([cx - w // 2 + 34, top + 168, cx - w // 2 + 48, top + 182],
                  fill=(214, 164, 76, 255))
        d.ellipse([cx - w // 2 + 60, top + 168, cx - w // 2 + 74, top + 182],
                  fill=(112, 158, 122, 255))
        d.ellipse([cx + w // 2 - 86, top + 150, cx + w // 2 - 22, top + 214],
                  fill=(178, 170, 148, 255), outline=(60, 68, 64, 255), width=4)
        d.ellipse([cx + w // 2 - 70, top + 166, cx + w // 2 - 38, top + 198],
                  fill=(78, 86, 80, 255))
        img.alpha_composite(layer)

    conveyor(img, (140, 700, 1640, 220), seed=55)
    soft_light(img, (960, 640), 560, (226, 170, 96), 30)
    grade(img, 55)
    return img


SCENES = {
    "boot": scene_boot,
    "scan": scene_scan,
    "mix": scene_mix,
    "analyze": scene_analyze,
    "result": scene_result,
}


def main():
    for name, fn in SCENES.items():
        path = os.path.normpath(os.path.join(OUT, "scene_%s.jpg" % name))
        fn().convert("RGB").save(path, quality=90, optimize=True)
        print("WROTE", path)


if __name__ == "__main__":
    main()
