#!/usr/bin/env python3
"""VD2/06-look — расшифровка «карты направлений» (dirdebug.py): пиксель ленты c (sRGB 16 бит → линейный) → d = 2c − 1,
годен, если |d| ≈ 1 (лента отражает купол, а не предмет сцены). Азимут — как у area() в velmora.py: 0° — к камере (−Y),
180° — за сцену (+Y), + вправо; угол места — вверх. Печатает гистограмму по клеткам 30° × 15° (доля годных пикселей
ленты) и долю «отражает сцену» (|d| далеко от 1: стена, пол, флакон). Рисует dir_hist.png.

    python3 dir_analyze.py dir/dir_f000.png dir/dir_f030.png …"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def analyze(path):
    im = np.asarray(Image.open(path)).astype(np.float64)
    im = im[..., :3] / (65535.0 if im.max() > 255 else 255.0)
    lin = srgb_to_lin(im)
    d = 2 * lin - 1
    n = np.linalg.norm(d, axis=-1)
    chroma = lin.max(axis=-1) - lin.min(axis=-1)
    valid = (np.abs(n - 1) < 0.08) & (lin.max(axis=-1) > 0.02)
    mk = path.replace(".png", "_mask.png")
    import os
    if os.path.exists(mk):
        m = np.asarray(Image.open(mk).convert("L").resize((im.shape[1], im.shape[0]))) > 127
        valid &= m
    dn = d[valid] / n[valid][:, None]
    az = np.degrees(np.arctan2(dn[:, 0], -dn[:, 1]))
    el = np.degrees(np.arcsin(np.clip(dn[:, 2], -1, 1)))
    return valid, az, el, lin


def main():
    paths = sys.argv[1:]
    H = np.zeros((12, 12))
    rows = []
    for p in paths:
        valid, az, el, lin = analyze(p)
        h, _, _ = np.histogram2d(el, az, bins=[12, 12], range=[[-90, 90], [-180, 180]])
        H += h
        tot = valid.sum()
        rows.append((p.rsplit("/", 1)[-1], tot, h))
        print(f"\n{p.rsplit('/', 1)[-1]}: годных пикселей ленты {tot}")
        print("угол места \\ азимут  " + " ".join(f"{a:>5}" for a in range(-165, 180, 30)))
        for i in range(11, -1, -1):
            e0 = -90 + 15 * i
            line = " ".join(f"{(h[i, j] / tot * 100 if tot else 0):5.1f}" for j in range(12))
            print(f"  {e0:+4d}…{e0 + 15:+4d}°          {line}")
    # рисунок суммарной гистограммы
    W, Hh, cell = 12, 12, 40
    img = Image.new("RGB", (W * cell + 80, Hh * cell + 60), (20, 20, 24))
    dr = ImageDraw.Draw(img)
    mx = H.max() or 1
    for i in range(12):
        for j in range(12):
            v = H[i, j] / mx
            c = int(255 * v ** 0.5)
            x0, y0 = 60 + j * cell, 20 + (11 - i) * cell
            dr.rectangle([x0, y0, x0 + cell - 2, y0 + cell - 2], fill=(c, int(c * 0.8), int(c * 0.5)))
    for j in range(0, 13, 2):
        dr.text((60 + j * cell - 10, 20 + 12 * cell + 4), f"{-180 + 30 * j}", fill=(200, 200, 200))
    for i in range(0, 13, 2):
        dr.text((10, 20 + (12 - i) * cell - 6), f"{-90 + 15 * i}", fill=(200, 200, 200))
    out = paths[0].rsplit("/", 1)[0] + "/dir_hist.png"
    img.save(out)
    print("\n→", out)


if __name__ == "__main__":
    main()
