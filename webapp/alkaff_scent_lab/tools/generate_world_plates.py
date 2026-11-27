#!/usr/bin/env python3
"""Render plate CG dunia pabrik maklon Alkaff tanpa asset eksternal.

Lima plate (boot, scan, mix, analyze, result) dirender 1920x1080 dengan PIL.
Sengaja TANPA teks, logo, atau manusia: semua teks diegetik ditambahkan Flutter
sebagai benda fisik (papan, nameplate, monitor, kertas batch).

Jalankan:
    python3 tools/generate_world_plates.py
"""
from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
VX, VY = 960, 470

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "world")
os.makedirs(OUT, exist_ok=True)

STEEL_DARK = (52, 62, 60)
STEEL_MID = (126, 140, 136)
STEEL_LIGHT = (206, 216, 212)
STEEL_HI = (242, 247, 244)
WALL = (34, 41, 39)
FLOOR = (42, 48, 46)
AMBER = (184, 123, 50)
YELLOW = (216, 169, 60)
INK = (12, 16, 15)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def hgrad(draw, box, left, right):
    x0, y0, x1, y1 = (int(v) for v in box)
    span = max(1, x1 - x0 - 1)
    for x in range(x0, x1):
        draw.line([(x, y0), (x, y1)], fill=mix(left, right, (x - x0) / span))


def vgrad(draw, box, top, bottom):
    x0, y0, x1, y1 = (int(v) for v in box)
    span = max(1, y1 - y0 - 1)
    for y in range(y0, y1):
        draw.line([(x0, y), (x1, y)], fill=mix(top, bottom, (y - y0) / span))


def glow(img, center, radius, color, alpha=90):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 22
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(alpha * (1 - i / steps) ** 1.6)
        d.ellipse(
            [center[0] - r, center[1] - r * 0.75, center[0] + r, center[1] + r * 0.75],
            fill=color[:3] + (a,),
        )
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(18)))


def ceiling_and_floor(img, floor_top=VY):
    d = ImageDraw.Draw(img, "RGBA")
    vgrad(d, (0, 0, W, floor_top), (20, 26, 24, 255), (58, 67, 63, 255))
    vgrad(d, (0, floor_top, W, H), (56, 64, 61, 255), (20, 25, 23, 255))

    # Perspektif lantai: garis menuju titik hilang.
    for x in range(-800, W + 800, 150):
        d.line([(x, H), (VX + (x - VX) * 0.16, floor_top)], fill=(255, 255, 255, 16), width=2)
    for i in range(1, 10):
        t = i / 10
        y = floor_top + (H - floor_top) * (t ** 1.7)
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 12), width=2)

    # Garis keselamatan kuning.
    d.line([(W * 0.06, H), (VX - 230, floor_top + 40)], fill=YELLOW + (120,), width=14)
    d.line([(W * 0.94, H), (VX + 230, floor_top + 40)], fill=YELLOW + (120,), width=14)


def skylights(img):
    d = ImageDraw.Draw(img, "RGBA")
    for x in (260, 700, 1220, 1660):
        w = 210
        d.polygon(
            [(x - w // 2, 0), (x + w // 2, 0), (x + w // 2 - 26, 150), (x - w // 2 + 26, 150)],
            fill=(196, 214, 205, 42),
        )
        d.line([(x - w // 2, 0), (x - w // 2 + 26, 150)], fill=(230, 240, 235, 60), width=3)
        d.line([(x + w // 2, 0), (x + w // 2 - 26, 150)], fill=(230, 240, 235, 60), width=3)
    glow(img, (960, 60), 900, (190, 220, 205), 34)


def high_bay(img, x, y, scale=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    w = int(150 * scale)
    d.polygon([(x - w, y - 14), (x + w, y - 14), (x + w // 2, y + 10), (x - w // 2, y + 10)], fill=(70, 78, 75, 255))
    d.ellipse([x - w // 3, y + 4, x + w // 3, y + 18], fill=(245, 242, 220, 210))
    glow(img, (x, y + 16), int(230 * scale), (235, 230, 200), 42)


def column(img, x, top, bottom, width=54):
    d = ImageDraw.Draw(img, "RGBA")
    hgrad(d, (x - width // 2, top, x + width // 2, bottom), STEEL_DARK, STEEL_MID)
    d.line([(x - width // 2, top), (x - width // 2, bottom)], fill=STEEL_HI + (70,), width=2)
    d.line([(x + width // 2, top), (x + width // 2, bottom)], fill=(0, 0, 0, 90), width=3)


def tank(img, cx, base_y, w, h, detail=True):
    """Tangki stainless berjaket dengan elips atas, badan gradasi, kaki, katup."""
    d = ImageDraw.Draw(img, "RGBA")
    top = base_y - h
    body = (cx - w // 2, top + w // 5, cx + w // 2, base_y)
    hgrad(d, body, STEEL_DARK, STEEL_MID)
    # highlight vertikal
    hx = cx - w // 5
    d.rectangle([hx - 10, body[1], hx + 14, body[3]], fill=STEEL_HI + (48,))
    d.rectangle([cx + w // 4, body[1], cx + w // 4 + 16, body[3]], fill=(12, 18, 16, 70))
    # elips atas
    d.ellipse([cx - w // 2, top, cx + w // 2, top + w // 2], fill=STEEL_MID + (255,))
    d.ellipse([cx - w // 2 + 12, top + 10, cx + w // 2 - 12, top + w // 2 - 10], fill=STEEL_LIGHT + (180,))
    d.ellipse([cx - w // 2 + 30, top + 18, cx + w // 2 - 30, top + w // 2 - 18], fill=STEEL_DARK + (200,))
    # elips bawah
    d.ellipse([cx - w // 2, base_y - w // 6, cx + w // 2, base_y + w // 6], fill=STEEL_DARK + (255,))
    # jaket/banding
    for yy in (top + w // 2 + 30, body[3] - 70):
        d.rectangle([body[0], yy, body[2], yy + 14], fill=(30, 38, 36, 180))
        d.line([(body[0], yy), (body[2], yy)], fill=STEEL_HI + (60,), width=2)
    # kaki
    for dx in (-w // 3, w // 3):
        d.rectangle([cx + dx - 12, base_y, cx + dx + 12, base_y + 54], fill=STEEL_DARK + (255,))
    if detail:
        # nameplate kosong untuk teks Flutter
        d.rounded_rectangle([body[0] + 22, body[1] + 70, body[0] + 150, body[1] + 126], radius=6, fill=(216, 222, 214, 190))
        d.rectangle([body[0] + 34, body[1] + 88, body[0] + 132, body[1] + 94], fill=(90, 98, 94, 140))
        d.rectangle([body[0] + 34, body[1] + 104, body[0] + 110, body[1] + 109], fill=(90, 98, 94, 120))
        # gauge
        gx, gy = cx + w // 3, body[1] + 120
        d.ellipse([gx - 26, gy - 26, gx + 26, gy + 26], fill=(226, 232, 224, 240), outline=(40, 48, 45, 255), width=4)
        d.line([(gx, gy), (gx + 16, gy - 12)], fill=(30, 36, 34, 255), width=3)
        # katup
        d.line([(cx, top + 10), (cx, top - 46)], fill=STEEL_MID + (255,), width=10)
        d.ellipse([cx - 30, top - 66, cx + 30, top - 26], fill=(174, 138, 56, 255))


def pipe(img, points, width=18, color=STEEL_MID):
    d = ImageDraw.Draw(img, "RGBA")
    d.line(points, fill=(18, 24, 22, 220), width=width + 6, joint="curve")
    d.line(points, fill=color + (255,), width=width, joint="curve")
    off = [(x, y - max(2, width // 4)) for x, y in points]
    d.line(off, fill=STEEL_HI + (55,), width=max(2, width // 4), joint="curve")


def catwalk(img, y, x0, x1, scale=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    h = int(16 * scale)
    d.rectangle([x0, y, x1, y + h], fill=STEEL_DARK + (255,))
    d.line([(x0, y), (x1, y)], fill=STEEL_HI + (80,), width=2)
    rail_y = y - int(70 * scale)
    d.line([(x0, rail_y), (x1, rail_y)], fill=STEEL_LIGHT + (220,), width=max(3, int(6 * scale)))
    for x in range(x0, x1 + 1, int(120 * scale)):
        d.line([(x, y), (x, rail_y)], fill=STEEL_MID + (220,), width=max(2, int(4 * scale)))


def pallet_drums(img, x, y, scale=1.0, count=2):
    d = ImageDraw.Draw(img, "RGBA")
    pw = int(180 * scale)
    d.polygon([(x - pw // 2, y), (x + pw // 2, y), (x + pw // 2, y + 26 * scale), (x - pw // 2, y + 26 * scale)], fill=(92, 72, 46, 255))
    for i in range(count):
        cx = x + (i - (count - 1) / 2) * 78 * scale
        w, h = int(64 * scale), int(150 * scale)
        hgrad(d, (cx - w // 2, y - h, cx + w // 2, y), (66, 76, 73, 255), (158, 168, 164, 255))
        d.ellipse([cx - w // 2, y - h - 10 * scale, cx + w // 2, y - h + 12 * scale], fill=STEEL_LIGHT + (230,))
        d.rectangle([cx - w // 2, y - h + 40 * scale, cx + w // 2, y - h + 52 * scale], fill=(30, 36, 34, 150))


def bottle(img, cx, base, scale=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    w, h = int(46 * scale), int(120 * scale)
    body = (cx - w // 2, base - h, cx + w // 2, base)
    hgrad(d, body, (78, 44, 18, 240), AMBER + (245,))
    d.rectangle([cx - 8 * scale, base - h - 26 * scale, cx + 8 * scale, base - h], fill=(52, 32, 16, 255))
    d.rectangle([cx - 11 * scale, base - h - 34 * scale, cx + 11 * scale, base - h - 24 * scale], fill=STEEL_MID + (255,))
    d.rounded_rectangle([cx - w // 2 + 5, base - h + 34 * scale, cx + w // 2 - 5, base - h + 76 * scale], radius=4, fill=(226, 220, 202, 235))
    d.line([(cx - w // 2 + 5, base - h + 52 * scale), (cx + w // 2 - 12, base - h + 52 * scale)], fill=(120, 110, 92, 160), width=2)


def grade(img, seed):
    random.seed(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    # vignette
    steps = 26
    for i in range(steps):
        a = int(3 + 9 * (i / steps) ** 2)
        inset = int(i * 12)
        d.rectangle([inset, inset, W - inset, H - inset], outline=(6, 10, 8, a), width=12)
    img.alpha_composite(layer)
    # haze hangat tipis
    glow(img, (1500, 520), 620, (190, 140, 70), 16)
    # grain
    noise = Image.new("L", (W, H))
    noise.putdata([random.randrange(116, 140) for _ in range(W * H)])
    noise = noise.filter(ImageFilter.GaussianBlur(0.4)).convert("RGBA")
    noise.putalpha(12)
    img.alpha_composite(noise)


def new_canvas():
    return Image.new("RGBA", (W, H), INK + (255,))


def scene_boot():
    img = new_canvas()
    ceiling_and_floor(img)
    skylights(img)
    high_bay(img, 420, 210, 1.1)
    high_bay(img, 1500, 210, 1.1)
    for x in (300, 1620):
        column(img, x, 0, 720, 62)
    # pintu geser
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([690, 210, 1230, 700], fill=(46, 56, 53, 255), outline=STEEL_MID + (255,), width=8)
    d.line([(960, 210), (960, 700)], fill=STEEL_HI + (120,), width=5)
    d.rectangle([730, 520, 1190, 560], fill=YELLOW + (110,))
    # deretan tangki perspektif
    for i, (cx, base, w, h) in enumerate([
        (210, 820, 210, 430), (420, 700, 150, 320), (570, 620, 104, 240),
        (1710, 820, 210, 430), (1500, 700, 150, 320), (1350, 620, 104, 240),
    ]):
        tank(img, cx, base, w, h, detail=(i in (0, 3)))
    catwalk(img, 430, 120, 1800, 1.0)
    pipe(img, [(120, 360), (520, 360), (520, 300), (1400, 300)], 14)
    pipe(img, [(1800, 470), (1480, 470), (1480, 520), (520, 520)], 12)
    glow(img, (960, 620), 520, (120, 170, 150), 24)
    grade(img, 11)
    return img


def scene_scan():
    img = new_canvas()
    ceiling_and_floor(img)
    skylights(img)
    high_bay(img, 560, 230)
    high_bay(img, 1420, 230)
    d = ImageDraw.Draw(img, "RGBA")
    # rack gudang
    for x0, x1, y in ((90, 620, 540), (1300, 1830, 540)):
        d.rectangle([x0, y - 320, x1, y], fill=(28, 34, 32, 220), outline=STEEL_DARK + (255,), width=8)
        for yy in (y - 230, y - 120):
            d.line([(x0, yy), (x1, yy)], fill=STEEL_MID + (180,), width=8)
    for x, y, s in ((260, 720, 1.05), (520, 660, 0.8), (1660, 720, 1.05), (1400, 660, 0.8)):
        pallet_drums(img, x, y, s)
    # meja QC foreground kanan (area monitor kosong disiapkan Flutter)
    d.rounded_rectangle([1030, 700, 1820, 900], radius=18, fill=STEEL_DARK + (255,))
    hgrad(d, (1030, 690, 1820, 716), STEEL_LIGHT, STEEL_MID)
    for cx in (1120, 1210, 1300, 1390):
        d.rectangle([cx - 7, 620, cx + 7, 690], fill=(120, 150, 140, 230))
        d.ellipse([cx - 9, 610, cx + 9, 626], fill=(220, 232, 226, 220))
    pipe(img, [(120, 380), (900, 380), (900, 330)], 14)
    glow(img, (1360, 700), 430, (180, 190, 165), 26)
    grade(img, 22)
    return img


def scene_mix():
    img = new_canvas()
    ceiling_and_floor(img)
    skylights(img)
    high_bay(img, 500, 190, 1.15)
    high_bay(img, 1440, 190, 1.15)
    for i, (cx, base, w, h) in enumerate([
        (250, 900, 300, 560), (650, 760, 210, 420), (930, 680, 150, 330),
        (1220, 680, 150, 330), (1600, 900, 300, 560),
    ]):
        tank(img, cx, base, w, h, detail=(i in (0, 1, 4)))
    catwalk(img, 470, 100, 1820, 1.1)
    pipe(img, [(80, 360), (520, 360), (520, 300), (1420, 300), (1420, 390), (1840, 390)], 18)
    pipe(img, [(250, 520), (250, 600), (650, 600), (650, 540)], 14)
    pipe(img, [(1600, 520), (1600, 610), (1220, 610)], 14)
    # panel kontrol kosong
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([1470, 690, 1810, 880], radius=12, fill=(28, 36, 33, 255), outline=STEEL_MID + (255,), width=4)
    for x in range(1510, 1790, 70):
        d.ellipse([x, 730, x + 34, 764], fill=STEEL_LIGHT + (220,))
        d.line([(x + 17, 747), (x + 28, 736)], fill=(40, 50, 46, 255), width=3)
    glow(img, (960, 500), 560, (110, 160, 145), 22)
    grade(img, 33)
    return img


def scene_analyze():
    img = new_canvas()
    ceiling_and_floor(img)
    skylights(img)
    # jendela ke production hall
    d = ImageDraw.Draw(img, "RGBA")
    for x0, x1 in ((120, 520), (620, 1020), (1120, 1520)):
        d.rectangle([x0, 140, x1, 520], fill=(70, 86, 80, 230), outline=STEEL_MID + (220,), width=8)
        for i in range(3):
            tank(img, x0 + 120 + i * 130, 500, 90, 210, detail=False)
        d.line([((x0 + x1) // 2, 140), ((x0 + x1) // 2, 520)], fill=STEEL_MID + (180,), width=6)
    # meja QC
    d.rounded_rectangle([90, 720, 1830, 940], radius=16, fill=STEEL_DARK + (255,))
    hgrad(d, (90, 705, 1830, 735), STEEL_LIGHT, STEEL_MID)
    for cx in (260, 360, 460, 560):
        d.rectangle([cx - 8, 640, cx + 8, 710], fill=(120, 150, 140, 230))
        d.ellipse([cx - 10, 628, cx + 10, 646], fill=(220, 232, 226, 220))
    # monitor kosong untuk chat diegetik (kanan)
    d.rounded_rectangle([1180, 430, 1740, 690], radius=18, fill=(18, 24, 22, 255), outline=STEEL_MID + (255,), width=10)
    d.rectangle([1210, 460, 1710, 660], fill=(10, 20, 17, 255))
    d.rectangle([1440, 690, 1480, 730], fill=STEEL_DARK + (255,))
    d.rectangle([1380, 730, 1540, 744], fill=STEEL_MID + (255,))
    glow(img, (1450, 560), 420, (90, 150, 130), 30)
    glow(img, (420, 760), 300, (210, 150, 70), 20)
    grade(img, 44)
    return img


def scene_result():
    img = new_canvas()
    ceiling_and_floor(img)
    skylights(img)
    high_bay(img, 500, 200)
    high_bay(img, 1420, 200)
    d = ImageDraw.Draw(img, "RGBA")
    # rak gudang belakang
    for x0, x1 in ((120, 700), (1220, 1800)):
        d.rectangle([x0, 250, x1, 640], fill=(30, 36, 34, 230), outline=STEEL_DARK + (255,), width=8)
        for yy in (360, 470, 575):
            d.line([(x0, yy), (x1, yy)], fill=STEEL_MID + (160,), width=7)
            for bx in range(x0 + 30, x1 - 30, 110):
                d.rectangle([bx, yy - 80, bx + 90, yy - 6], fill=(128, 106, 72, 220))
    # conveyor
    d.polygon([(180, 700), (1740, 700), (1600, 900), (320, 900)], fill=STEEL_DARK + (255,))
    d.line([(180, 700), (1740, 700)], fill=STEEL_HI + (90,), width=5)
    for x in range(260, 1700, 120):
        d.line([(x, 710), (x + 40, 890)], fill=(12, 18, 16, 120), width=6)
    # mesin cap/label
    for cx in (620, 1180):
        d.rounded_rectangle([cx - 130, 470, cx + 130, 710], radius=16, fill=STEEL_MID + (230,), outline=STEEL_HI + (120,), width=4)
        d.rectangle([cx - 80, 520, cx + 80, 600], fill=(28, 36, 33, 220))
    for cx in (420, 700, 980, 1260, 1540):
        bottle(img, cx, 780, 1.0)
    # area kertas batch kosong di tengah bawah
    d.rounded_rectangle([760, 820, 1160, 1010], radius=10, fill=(226, 220, 202, 235))
    glow(img, (960, 640), 540, (120, 160, 145), 22)
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
        fn().convert("RGB").save(path, quality=88, optimize=True)
        print("WROTE", path)


if __name__ == "__main__":
    main()
