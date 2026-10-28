"""icons_web.py — веб-иконки серии приборов по паспорту (дорожка SD, итерация SD2).

Правка оркестратора: «у иконок видны светло-серые квадраты фона; рулетка и фонарь мелкие». Причина квадратов — мягкая тень
свода (мир 0,78) на ловце теней доходила до края кадра 1024² и обрезалась им: у лазера низ кадра 242/255 (ΔE ≈ 5 к #fff).
Здесь:
  1) кадр — по маске предмета: высота предмета H_T = 56 % стороны кадра (паспорт 44–63 %), ширина ≤ W_MAX = 72 %;
     центр кадра = центр габарита предмета + 2 % стороны к тени (тень солнца уходит вправо) — одно правило на серию;
  2) тень (альфа ловца теней вне маски) сохраняется у предмета, а дальше гаснет по расстоянию от маски:
     F(d) = 1 при d < 0,08·S, затем exp(−(d − 0,08·S)/(0,12·S)); плюс окно у края кадра (0,80 → 0,96 полуширины, дальше 0) —
     у края кадра фон ровно #ffffff (ΔE ≤ 1 проверяется после кодирования AVIF/WebP);
  3) «запекание» на бумагу страницы #ffffff (правило журнала: альфа AVIF с потерями даёт ореол, фон страницы ровный).
    python3 icons_web.py RENDER_DIR OUT_ASSETS_DIR [--h 0.56] [--wmax 0.72]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

KIT = ["laser", "thermal", "moisture", "tape", "flashlight"]


def srgb_to_lab(rgb8):
    c = rgb8.astype(np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def de76_to_white(rgb8):
    lab = srgb_to_lab(rgb8)
    return np.sqrt((lab[..., 0] - 100.0) ** 2 + lab[..., 1] ** 2 + lab[..., 2] ** 2)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def process(rdir, out, name, H_T, W_MAX, sizes=(128, 256)):
    im = np.asarray(Image.open(f"{rdir}/{name}.png").convert("RGBA")).astype(np.float64) / 255.0
    mk = np.asarray(Image.open(f"{rdir}/{name}_mask.png").convert("RGBA")).astype(np.float64)[..., 3] / 255.0
    ys, xs = np.nonzero(mk > 0.5)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    ow, oh = x1 - x0, y1 - y0
    S = max(oh / H_T, ow / W_MAX)
    cx, cy = (x0 + x1) / 2 + 0.02 * S, (y0 + y1) / 2          # центр габарита + 2 % к стороне тени (солнце слева)
    # тень: гашение по расстоянию от предмета + окно у края будущего кадра
    d = ndimage.distance_transform_edt(mk < 0.5)
    F = np.where(d < 0.08 * S, 1.0, np.exp(-(d - 0.08 * S) / (0.12 * S)))
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    q = np.maximum(np.abs(xx + 0.5 - cx), np.abs(yy + 0.5 - cy)) / (S / 2)
    F = F * (1.0 - smoothstep(0.80, 0.96, q))
    A = im[..., 3] * (mk + (1 - mk) * F)
    rgb = im[..., :3] * A[..., None] + (1.0 - A[..., None])            # на бумагу #ffffff
    flat = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    box = (cx - S / 2, cy - S / 2, cx + S / 2, cy + S / 2)
    inside = box[0] >= 0 and box[1] >= 0 and box[2] <= im.shape[1] and box[3] <= im.shape[0]
    # кадр может выйти за рендер (если предмет крупнее запаса): добиваем белым
    pad = int(math.ceil(max(0, -box[0], -box[1], box[2] - im.shape[1], box[3] - im.shape[0]))) + 2
    if pad > 2:
        big = Image.new("RGB", (im.shape[1] + 2 * pad, im.shape[0] + 2 * pad), (255, 255, 255))
        big.paste(flat, (pad, pad))
        flat, box = big, tuple(v + pad for v in box)
    res = {"obj_px": [int(ow), int(oh)], "crop_px": round(S, 1), "h_pct": round(oh / S * 100, 1), "w_pct": round(ow / S * 100, 1),
           "crop_inside_render": bool(inside)}
    for sz in sizes:
        fr = flat.resize((sz, sz), Image.LANCZOS, box=box)
        for ext, kw in (("avif", {"quality": 62}), ("webp", {"quality": 82, "method": 6})):
            p = f"{out}/icon-{name}-{sz}.{ext}"
            fr.save(p, ext.upper(), **kw)
            dec = np.asarray(Image.open(p).convert("RGB"))
            ring = np.concatenate([dec[:3].reshape(-1, 3), dec[-3:].reshape(-1, 3), dec[:, :3].reshape(-1, 3), dec[:, -3:].reshape(-1, 3)])
            res[f"{sz}_{ext}"] = {"kb": round(os.path.getsize(p) / 1024, 2), "edge_dE_max": round(float(de76_to_white(ring).max()), 2),
                                  "edge_dE_mean": round(float(de76_to_white(ring).mean()), 3)}
        fr.save(f"{rdir}/web_{name}_{sz}.png")
    return res


def main():
    a = sys.argv[1:]
    rdir, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    H_T = float(a[a.index("--h") + 1]) if "--h" in a else 0.56
    W_MAX = float(a[a.index("--wmax") + 1]) if "--wmax" in a else 0.72
    os.makedirs(out, exist_ok=True)
    rep = {"passport": {"h_target": H_T, "w_max": W_MAX, "bg": "#ffffff", "shadow_fade": "F(d)=1 при d<0,08S, далее exp(−(d−0,08S)/0,12S); окно 0,80–0,96 полуширины"}}
    for k in KIT:
        if os.path.exists(f"{rdir}/{k}.png"):
            rep[k] = process(rdir, out, k, H_T, W_MAX)
            print(k, json.dumps(rep[k], ensure_ascii=False))
    # лист серии на бумаге (200 px) — для глаз
    row = Image.new("RGB", (len(KIT) * 220 + 20, 240), (255, 255, 255))
    for i, k in enumerate(KIT):
        p = f"{rdir}/web_{k}_256.png"
        if os.path.exists(p):
            row.paste(Image.open(p).resize((200, 200), Image.LANCZOS), (20 + i * 220, 20))
    row.save(f"{rdir}/row200_web.png")
    json.dump(rep, open(f"{rdir}/icons_web.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
