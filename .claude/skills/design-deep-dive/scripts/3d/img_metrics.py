#!/usr/bin/env python3
"""img_metrics.py — числа кадра до глаз и до судьи, одинаковые для всех вариантов сцены.

    python3 img_metrics.py КАДР.png [--mask МАСКА.png | --alpha] [--bg-hex '#101215'] [--text-zone x0,y0,x1,y1] [--out m.json]

  --mask      PNG той же величины: белое (> 127) — объект. Удобно рендерить из Blender тем же кадром (объект белым emission,
              остальное чёрным) или брать альфу рендера на прозрачном фоне (--alpha).
  --alpha     маска объекта = альфа кадра (> 0.5); цвет считается по кадру, наложенному на --bg-hex (или на серый).
  --bg-hex    цвет фона страницы: насколько фон кадра совпадает со страницей (ΔE2000 медианы фона к hex).
  --text-zone доли кадра под заголовок, например 0,0,0.45,1 — какая доля «визуального веса» в зоне текста (должна быть малой).

Что считает (sRGB → Lab D65):
  obj/bg L* — перцентили 5/50/95 и максимум; obj_minus_bg_L — разность медиан (цель ≥ 10–15);
  clip_obj — доля пикселей объекта с каналом ≥ 254 (цель ≤ 1 %); hi_obj — доля L* ≥ 97 (блик: 0,1–1 %); crush — доля L* ≤ 3;
  noise — СКО (L/100 − гаусс σ 2 px) по объекту, ×10⁻³ (цель ≤ 2,5 для hero);
  chroma — доля насыщенных пикселей C* > 60 в кадре и на объекте (правило «одно насыщенное пятно»);
  weight_center — центр «визуального веса» (локальный контраст σ 8 + насыщенность), доли кадра; weight_in_text — доля веса
  в зоне текста; weight_on_obj — доля веса на объекте (фокус должен быть на герое);
  bg_vs_page_dE — ΔE2000 медианы фона к --bg-hex (цель ≤ 3 — постер не «ступенькой» на странице).
Печатает JSON (и пишет в --out). Пороги — стартовые, из таблицы плана; на людях не откалиброваны.
"""
import json
import math
import sys

import numpy as np
from PIL import Image


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def rgb_to_lab(rgb):  # rgb 0..1 sRGB, (..., 3)
    lin = srgb_to_lin(rgb)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ m.T
    white = np.array([0.95047, 1.0, 1.08883])
    t = xyz / white
    d = 6 / 29
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4 / 29)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def de2000(l1, l2):
    L1, a1, b1 = l1
    L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    if C1p * C2p == 0:
        dh = 0
    elif dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lm, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    if C1p * C2p == 0:
        hm = hs
    elif abs(h1p - h2p) <= 180:
        hm = hs / 2
    else:
        hm = (hs + 360) / 2 if hs < 360 else (hs - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hm - 30)) + 0.24 * math.cos(math.radians(2 * hm))
         + 0.32 * math.cos(math.radians(3 * hm + 6)) - 0.20 * math.cos(math.radians(4 * hm - 63)))
    dth = 30 * math.exp(-((hm - 275) / 25) ** 2)
    Rc = 2 * math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    Sc = 1 + 0.045 * Cmp
    Sh = 1 + 0.015 * Cmp * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def gauss(img, sigma):
    r = max(1, int(3 * sigma))
    x = np.arange(-r, r + 1)
    k = np.exp(-x * x / (2 * sigma * sigma))
    k /= k.sum()
    pad = np.pad(img, ((r, r), (r, r)), mode="reflect")
    tmp = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 1, pad)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 0, tmp)


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def pct(v, q):
    return float(np.percentile(v, q)) if v.size else None


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    def opt(n, d=None):
        return a[a.index(n) + 1] if n in a else d

    path = a[0]
    im = Image.open(path)
    has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    rgba = np.asarray(im.convert("RGBA")).astype(np.float64) / 255
    bg_hex = opt("--bg-hex")
    bg_rgb = hex_rgb(bg_hex) if bg_hex else np.array([0.5, 0.5, 0.5])
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    if has_alpha:  # кадр на прозрачном фоне — смотрим так, как его увидит страница
        rgb = rgb * alpha[..., None] + bg_rgb * (1 - alpha[..., None])
    h, w = rgb.shape[:2]
    if opt("--mask"):
        mask = np.asarray(Image.open(opt("--mask")).convert("L").resize((w, h))) > 127
    elif "--alpha" in a and has_alpha:
        mask = alpha > 0.5
    else:
        mask = None
    lab = rgb_to_lab(rgb)
    L = lab[..., 0]
    C = np.hypot(lab[..., 1], lab[..., 2])
    rgb8 = np.round(rgb * 255)
    out = {"file": path, "size": [w, h], "mask": bool(mask is not None)}
    obj = mask if mask is not None else np.ones_like(L, dtype=bool)
    bg = ~mask if mask is not None else None
    Lo = L[obj]
    out["obj_L"] = {"p5": pct(Lo, 5), "p50": pct(Lo, 50), "p95": pct(Lo, 95), "max": float(Lo.max()) if Lo.size else None}
    out["clip_obj_pct"] = float((rgb8[obj] >= 254).any(axis=-1).mean() * 100) if Lo.size else None
    out["hi_obj_pct"] = float((Lo >= 97).mean() * 100) if Lo.size else None
    out["crush_obj_pct"] = float((Lo <= 3).mean() * 100) if Lo.size else None
    if bg is not None and bg.any():
        Lb = L[bg]
        out["bg_L"] = {"p5": pct(Lb, 5), "p50": pct(Lb, 50), "p95": pct(Lb, 95)}
        out["obj_minus_bg_L"] = pct(Lo, 50) - pct(Lb, 50)
        if bg_hex:
            med = [float(np.median(lab[..., i][bg])) for i in range(3)]
            out["bg_vs_page_dE"] = de2000(med, rgb_to_lab(hex_rgb(bg_hex)[None, None, :])[0, 0].tolist())
    hp = L / 100 - gauss(L / 100, 2.0)
    out["noise_e3"] = float(hp[obj].std() * 1000)
    out["chroma_hi_pct_frame"] = float((C > 60).mean() * 100)
    out["chroma_hi_pct_obj"] = float((C[obj] > 60).mean() * 100) if Lo.size else None
    wmap = np.abs(L - gauss(L, 8.0)) + 0.35 * C
    wsum = wmap.sum() + 1e-9
    ys, xs = np.mgrid[0:h, 0:w]
    out["weight_center"] = [float((wmap * xs).sum() / wsum / w), float((wmap * ys).sum() / wsum / h)]
    if mask is not None:
        out["weight_on_obj"] = float(wmap[mask].sum() / wsum)
    tz = opt("--text-zone")
    if tz:
        x0, y0, x1, y1 = [float(v) for v in tz.split(",")]
        zone = (xs >= x0 * w) & (xs < x1 * w) & (ys >= y0 * h) & (ys < y1 * h)
        out["weight_in_text"] = float(wmap[zone].sum() / wsum)
    js = json.dumps(out, ensure_ascii=False, indent=1)
    if opt("--out"):
        with open(opt("--out"), "w") as f:
            f.write(js)
    print(js)
    return 0


if __name__ == "__main__":
    sys.exit(main())
