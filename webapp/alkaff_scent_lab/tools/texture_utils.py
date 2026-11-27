"""Utilitas tekstur prosedural untuk plate Alkaff Maklon Hall.

Semua tekstur dibuat dari nol memakai numpy + PIL. Tidak ada foto pihak ketiga
yang disalin; foto internet hanya dipakai sebagai referensi nuansa.
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def smooth_noise(width: int, height: int, cells_x: int, cells_y: int, rng) -> np.ndarray:
    """Noise halo halus dari grid acak, di-upsample dengan bicubic."""
    grid = rng.random((cells_y + 1, cells_x + 1)).astype(np.float32)
    small = Image.fromarray((grid * 255).astype(np.uint8), mode="L")
    big = small.resize((width, height), Image.Resampling.BICUBIC)
    return np.asarray(big, dtype=np.float32) / 255.0


def fbm(width: int, height: int, seed: int, octaves: int = 4) -> np.ndarray:
    """Fractal Brownian motion ringan untuk tekstur alami."""
    rng = np.random.default_rng(seed)
    out = np.zeros((height, width), dtype=np.float32)
    amp = 1.0
    total = 0.0
    cells = 4
    for _ in range(octaves):
        out += amp * smooth_noise(width, height, cells, max(2, cells // 2), rng)
        total += amp
        amp *= 0.52
        cells *= 2
    return out / total


def brushed_steel(width: int, height: int, seed: int, base=(126, 138, 133)) -> Image.Image:
    """Stainless brushed: gradasi tipis + goresan mikro searah horizontal."""
    rng = np.random.default_rng(seed)
    n = fbm(width, height, seed, 3)
    y = np.arange(height, dtype=np.float32)[:, None]
    streak_y = np.sin(y * 0.22) * 3.0
    streak_y += rng.normal(0, 1.4, size=(height, 1)).astype(np.float32)
    streak = np.repeat(streak_y, width, axis=1) + (n - 0.5) * 7.0
    arr = np.empty((height, width, 3), dtype=np.float32)
    for ch, value in enumerate(base):
        arr[:, :, ch] = np.clip(value + (n - 0.5) * 38 + streak, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="RGB")


def concrete(width: int, height: int, seed: int, base=(58, 62, 58)) -> Image.Image:
    """Beton cat industrial: mottling halus + bintik agregat."""
    rng = np.random.default_rng(seed)
    n = fbm(width, height, seed, 5)
    speck = rng.random((height, width)).astype(np.float32)
    speck = np.where(speck > 0.992, 22.0, 0.0)
    arr = np.empty((height, width, 3), dtype=np.float32)
    for ch, value in enumerate(base):
        arr[:, :, ch] = np.clip(value + (n - 0.5) * 46 + speck, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="RGB")


def epoxy(width: int, height: int, seed: int, base=(49, 52, 49)) -> Image.Image:
    """Lantai epoksi abu hangat dengan kilap lembut dan debu halus."""
    rng = np.random.default_rng(seed)
    n = fbm(width, height, seed + 17, 4)
    dust = rng.random((height, width)).astype(np.float32)
    arr = np.empty((height, width, 3), dtype=np.float32)
    for ch, value in enumerate(base):
        arr[:, :, ch] = np.clip(value + (n - 0.5) * 28 + (dust - 0.5) * 6, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="RGB")


def warm_wood(width: int, height: int, seed: int, base=(112, 74, 43)) -> Image.Image:
    """Kayu rak butik: serat memanjang, nada coklat hangat."""
    rng = np.random.default_rng(seed)
    n = fbm(width, height, seed + 41, 4)
    x = np.arange(width, dtype=np.float32)[None, :]
    rings = np.sin(x * 0.045 + n * 11.0) * 10.0
    arr = np.empty((height, width, 3), dtype=np.float32)
    for ch, value in enumerate(base):
        arr[:, :, ch] = np.clip(value + (n - 0.5) * 42 + rings, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="RGB")


def radial_light(width: int, height: int, center, radius: float, color, alpha: float) -> Image.Image:
    """Cahaya hangat dengan jatuhan mulus (bukan lingkaran konsentris)."""
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    cx, cy = center
    d2 = ((xx - cx) / max(radius, 1.0)) ** 2 + ((yy - cy) / max(radius * 0.78, 1.0)) ** 2
    a = np.exp(-d2 * 1.8) * alpha
    arr = np.empty((height, width, 4), dtype=np.float32)
    arr[:, :, 0], arr[:, :, 1], arr[:, :, 2] = color
    arr[:, :, 3] = np.clip(a, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="RGBA")


def multiply_shade(img: Image.Image, factor: float) -> Image.Image:
    """Pergelap/pencerah cepat untuk bayangan jatuh."""
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    return Image.fromarray(np.clip(arr * factor, 0, 255).astype(np.uint8), mode="RGB")


def grain(width: int, height: int, seed: int, strength: int = 7) -> Image.Image:
    """Film grain halus untuk mengikat tekstur."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(128, strength, size=(height, width)).clip(0, 255)
    return Image.fromarray(noise.astype(np.uint8), mode="L").convert("RGB")
