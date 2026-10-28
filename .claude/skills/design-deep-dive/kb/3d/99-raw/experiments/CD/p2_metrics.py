#!/usr/bin/env python3
"""CD фаза 2 · цвет по роли материала и «пятно» вспышки (без браузера).

  python3 p2_metrics.py role FRAME.png ROLE_MASK.png [--hex ff5a1f]   → медианы L*, C*, h° пикселей роли (маска сужена на 1 px), ΔE00 к hex
  python3 p2_metrics.py blob FLASH.png NOFLASH.png [--thr 3]           → площадь (% кадра) и «энергия» (сумма ΔL*) прибавки света вспышки
"""
import argparse, json, math
import numpy as np
from PIL import Image, ImageFilter


def srgb_to_lab(a):
    a = a / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    L = 116 * f[..., 1] - 16; A = 500 * (f[..., 0] - f[..., 1]); B = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, A, B], -1)


def de2000(l1, l2):
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1 = math.hypot(a1, b1); C2 = math.hypot(a2, b2); Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360; h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp = L2 - L1; dCp = C2p - C1p
    dh = h2p - h1p
    if C1p * C2p == 0: dh = 0
    elif dh > 180: dh -= 360
    elif dh < -180: dh += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lpm = (L1 + L2) / 2; Cpm = (C1p + C2p) / 2
    if C1p * C2p == 0: hpm = h1p + h2p
    elif abs(h1p - h2p) <= 180: hpm = (h1p + h2p) / 2
    else: hpm = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = 1 - 0.17 * math.cos(math.radians(hpm - 30)) + 0.24 * math.cos(math.radians(2 * hpm)) + 0.32 * math.cos(math.radians(3 * hpm + 6)) - 0.2 * math.cos(math.radians(4 * hpm - 63))
    dth = 30 * math.exp(-(((hpm - 275) / 25) ** 2)); Rc = 2 * math.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lpm - 50) ** 2 / math.sqrt(20 + (Lpm - 50) ** 2); Sc = 1 + 0.045 * Cpm; Sh = 1 + 0.015 * Cpm * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def role(a):
    im = np.asarray(Image.open(a.frame).convert('RGB')).astype(float)
    mk = Image.open(a.mask).convert('L').filter(ImageFilter.MinFilter(3))
    m = np.asarray(mk) > 128
    if m.sum() < 20:
        print(json.dumps({'frame': a.frame, 'n': int(m.sum())})); return
    lab = srgb_to_lab(im[m])
    L, A, B = lab[:, 0], lab[:, 1], lab[:, 2]
    C = np.hypot(A, B); H = np.degrees(np.arctan2(B, A)) % 360
    hexc = np.array([[int(a.hex[i:i + 2], 16) for i in (0, 2, 4)]], float)
    ref = srgb_to_lab(hexc)[0]
    med = [float(np.median(L)), float(np.median(A)), float(np.median(B))]
    # «розовое» — пиксели роли, у которых оттенок ушёл на 10°+ к красному/пурпурному при светлоте выше медианы бренда
    pinkish = float(((H < math.degrees(math.atan2(ref[2], ref[1])) - 10) & (L > 55)).mean() * 100)
    top = lab[L >= np.percentile(L, 90)]
    out = {'frame': a.frame, 'n': int(m.sum()), 'L50': round(med[0], 1), 'C50': round(float(np.median(C)), 1), 'h50': round(float(np.median(H)), 1),
           'L90': round(float(np.percentile(L, 90)), 1), 'top10_h': round(float(np.median(np.degrees(np.arctan2(top[:, 2], top[:, 1])) % 360)), 1),
           'top10_C': round(float(np.median(np.hypot(top[:, 1], top[:, 2]))), 1),
           'dE00_median_to_hex': round(de2000(ref, med), 1), 'hex_Lch': [round(ref[0], 1), round(math.hypot(ref[1], ref[2]), 1), round(math.degrees(math.atan2(ref[2], ref[1])) % 360, 1)],
           'pinkish_pct': round(pinkish, 2), 'a50': round(med[1], 1), 'b50': round(med[2], 1)}
    print(json.dumps(out, ensure_ascii=False))


def blob(a):
    f = srgb_to_lab(np.asarray(Image.open(a.flash).convert('RGB')).astype(float))[..., 0]
    n = srgb_to_lab(np.asarray(Image.open(a.noflash).convert('RGB')).astype(float))[..., 0]
    d = f - n
    m = d > a.thr
    ys, xs = np.where(m)
    out = {'flash': a.flash, 'area_pct': round(float(m.mean() * 100), 2), 'energy_dL_sum_k': round(float(d[d > 0].sum() / 1000), 1),
           'dL_p99': round(float(np.percentile(d, 99.9)), 1),
           'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('role'); r.add_argument('frame'); r.add_argument('mask'); r.add_argument('--hex', default='ff5a1f')
    b = sub.add_parser('blob'); b.add_argument('flash'); b.add_argument('noflash'); b.add_argument('--thr', type=float, default=3)
    a = ap.parse_args(); {'role': role, 'blob': blob}[a.cmd](a)
