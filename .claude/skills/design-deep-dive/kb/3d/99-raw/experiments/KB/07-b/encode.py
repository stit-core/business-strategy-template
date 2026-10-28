#!/usr/bin/env python3
"""encode.py — кадры B → веб (Pillow 11: AVIF, WebP). Прозрачные кадры сводятся на цвет своего раздела страницы:
фон кадра = CSS-фон раздела (ΔE 0). Выход — web/assets/img/… (build_pages.py раскладывает по страницам).

    python3 encode.py [hero] [type] [x] [turn] [shadow]      (без аргументов — всё, что уже отрендерено)
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
WEB = os.path.join(HERE, "web", "assets", "img")
STUDIO = (0x1C, 0x1D, 0x20)          # --studio (раздел «Напечатайте»)
PAPER = (0xED, 0xEF, 0xF0)           # --paper (раздел «Как устроена»)
CW_BG = {"snow": (0xED, 0xEF, 0xF0), "graphite": (0x14, 0x16, 0x19), "linen": (0xEF, 0xE8, 0xDC)}
stats = {}


def comp(path, bg, feather=0.05, fade=None):
    """Свести прозрачный кадр на цвет раздела. Ловец теней Cycles при светлом мире слегка темнит весь пол (альфа 0,05–0,1
    по краю) → прямоугольник кадра виден на странице. Лечение: из альфы полупрозрачных пикселей (тень) вычитается медиана
    альфы по краю кадра, тень растушёвывается к краям — фон кадра = фон раздела.
    fade=(r0, r1) (KB3, разборка): тень гаснет по расстоянию от предмета — полная ближе r0, ноль дальше r1 (доли меньшей
    стороны кадра); иначе мягкая тень слоёв доходила до нижнего края кадра и растушёвка 5 % давала прямую кромку плашки."""
    im = np.asarray(Image.open(path).convert("RGBA")).astype(np.float64) / 255
    rgb, a = im[..., :3], im[..., 3]
    H, W = a.shape
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    a0 = float(np.median(edge))
    sh = a < 0.995
    a2 = a.copy()
    a2[sh] = np.clip((a[sh] - a0) / max(1e-6, 1 - a0), 0, 1)
    f = feather * min(W, H)
    yy, xx = np.mgrid[0:H, 0:W]
    ramp = np.clip(np.minimum.reduce([xx, W - 1 - xx, yy, H - 1 - yy]) / f, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)
    a2[sh] *= ramp[sh]
    if fade:
        from scipy.ndimage import distance_transform_edt
        dist = distance_transform_edt(a < 0.5)            # px до ближайшего пикселя предмета
        r0, r1 = fade[0] * min(W, H), fade[1] * min(W, H)
        t = np.clip((dist - r0) / (r1 - r0), 0, 1)
        a2[sh] *= (1 - t * t * (3 - 2 * t))[sh]
        stats.setdefault("fade", {})[os.path.basename(path)] = [round(r0), round(r1)]
    bgc = np.array(bg, dtype=np.float64) / 255
    out = rgb * a2[..., None] + bgc * (1 - a2[..., None])
    stats.setdefault("edge_alpha", {})[os.path.basename(path)] = round(a0, 4)
    return Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8))


def save(im, rel, q_avif=60, webp=False, q_webp=82):
    p = os.path.join(WEB, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    # KB3: 4:4:4 — ровный цвет раздела точнее (фон #EDEFF0: ΔE 1,26 → 0,64; «Графит» 1,78 → 0,91 при 4:2:0)
    im.save(p + ".avif", quality=q_avif, speed=6, subsampling="4:4:4")
    stats[rel + ".avif"] = os.path.getsize(p + ".avif")
    if webp:
        im.save(p + ".webp", quality=q_webp, method=6)
        stats[rel + ".webp"] = os.path.getsize(p + ".webp")


def half(im):
    return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)


def main():
    what = set(sys.argv[1:]) or {"hero", "type", "x", "turn", "shadow"}
    t0 = time.time()
    if "hero" in what:
        for tag in ("desk", "mob"):
            f = os.path.join(OUT, f"hero2_{tag}.png")
            if os.path.exists(f):
                save(Image.open(f).convert("RGB"), f"hero_{tag}", q_avif=62, webp=True, q_webp=84)
    if "type" in what and os.path.exists(os.path.join(OUT, "typing_snow.png")):
        for src, dst in [("typing_snow", "type/base")] + [(f"typing_snow_p{g}", f"type/p{g}") for g in range(4)]:
            im = comp(os.path.join(OUT, src + ".png"), STUDIO)
            save(im, dst, q_avif=64, webp=dst == "type/base")
            save(half(im), dst + "_m", q_avif=62)
    if "x" in what:
        for i in range(4):
            f = os.path.join(OUT, f"explode_{i}.png")
            if os.path.exists(f):
                im = comp(f, PAPER, feather=0.12, fade=(0.04, 0.2))
                save(im, f"x/s{i}", q_avif=62, webp=i == 0)
                save(half(im), f"x/s{i}_m", q_avif=60)
    if "turn" in what:
        for cw, bg in CW_BG.items():
            d = os.path.join(OUT, f"turn_{cw}")
            if not os.path.isdir(d):
                continue
            n = 0
            for a in range(0, 360, 10):
                f = os.path.join(d, f"d_{a:03d}.png")
                if not os.path.exists(f):
                    continue
                im = comp(f, bg)
                save(im, f"turn/{cw}/d_{a:03d}", q_avif=56, webp=a == 0)
                if a % 30 == 0:
                    save(im.resize((720, 450), Image.LANCZOS), f"turn/{cw}/m_{a:03d}", q_avif=56)
                n += 1
            for a in range(15, 360, 30):
                f = os.path.join(d, f"m_{a:03d}.png")
                if os.path.exists(f):
                    save(comp(f, bg), f"turn/{cw}/m_{a:03d}", q_avif=56)
                else:                         # телефонный кадр не отрендерен — ближайший десктопный (−5°), уменьшенный
                    fd = os.path.join(d, f"d_{a - 5:03d}.png")
                    if os.path.exists(fd):
                        save(comp(fd, bg).resize((720, 450), Image.LANCZOS), f"turn/{cw}/m_{a:03d}", q_avif=56)
                        stats.setdefault("m_fallback", []).append(f"{cw}/m_{a:03d}←d_{a - 5:03d}")
            stats[f"turn_{cw}_frames_d"] = n
    if "shadow" in what and os.path.exists(os.path.join(OUT, "shadow_floor.png")):
        a = Image.open(os.path.join(OUT, "shadow_floor.png")).convert("RGBA").split()[3]
        p = os.path.join(WEB, "shadow_floor.webp")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        a.save(p, quality=90, method=6)
        stats["shadow_floor.webp"] = os.path.getsize(p)
    tot = {}
    for k, v in list(stats.items()):
        if isinstance(v, int) and "." in k and not isinstance(v, dict):
            grp = k.split("/")[0] + ("/" + k.split("/")[1] if k.startswith("turn/") else "")
            if k.startswith("turn/"):
                grp += "/" + ("d" if "/d_" in k else "m")
            tot[grp] = tot.get(grp, 0) + v
    rep = {"sec": round(time.time() - t0, 1), "totals_kb": {k: round(v / 1024, 1) for k, v in tot.items()},
           "files": {k: (round(v / 1024, 1) if "." in k else v) for k, v in stats.items() if not k.startswith("turn/") or k.endswith("000.avif")}}
    old = {}
    rp = os.path.join(HERE, "web", "encode_report.json")
    if os.path.exists(rp):
        old = json.load(open(rp))
    old.setdefault("runs", []).append(rep)
    json.dump(old, open(rp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep["totals_kb"], ensure_ascii=False), rep["sec"], "s")


if __name__ == "__main__":
    main()
