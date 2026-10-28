#!/usr/bin/env python3
"""kbm.py — обёртка над общим img_metrics.py (дорожка KB): маска из альфы, метрики кадра, плюс шум на ровном фоне.

    python3 kbm.py КАДР.png МАСКА_RGBA.png PAGE_HEX OUT.json [text_zone]
Шум img_metrics считается по объекту и завышается мелкими деталями (надписи, щели между колпачками — это не шум).
Здесь добавлен noise_bg_e3 — то же СКО (L/100 − гаусс σ 2 px), но по фону дальше 12 px от объекта (ровная циклорама).
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

IMG_METRICS = "/home/mm/Документы/app-design/blender-research/15-showcase/_shared/img_metrics.py"
sys.path.insert(0, os.path.dirname(IMG_METRICS))
import img_metrics as IM  # noqa: E402


def bw_mask(mask_rgba, out):
    a = np.asarray(Image.open(mask_rgba).convert("RGBA"))[..., 3]
    Image.fromarray(((a > 127) * 255).astype(np.uint8)).save(out)
    return out


def main():
    frame, mask_rgba, page, out = sys.argv[1:5]
    tz = sys.argv[5] if len(sys.argv) > 5 else "0,0,0.33,1"
    bw = bw_mask(mask_rgba, os.path.splitext(mask_rgba)[0] + "_bw.png")
    r = subprocess.run([sys.executable, IMG_METRICS, frame, "--mask", bw, "--bg-hex", page, "--text-zone", tz],
                       capture_output=True, text=True, check=True)
    m = json.loads(r.stdout)
    rgb = np.asarray(Image.open(frame).convert("RGB")).astype(np.float64) / 255
    L = IM.rgb_to_lab(rgb)[..., 0] / 100
    hp = L - IM.gauss(L, 2.0)
    far = Image.open(bw).filter(ImageFilter.MaxFilter(25))
    bg = np.asarray(far) < 128
    m["noise_bg_e3"] = float(hp[bg].std() * 1000) if bg.any() else None
    m["obj_share"] = float((np.asarray(Image.open(bw)) > 127).mean())
    json.dump(m, open(out, "w"), ensure_ascii=False, indent=1)
    keys = ("obj_L", "clip_obj_pct", "hi_obj_pct", "bg_L", "obj_minus_bg_L", "bg_vs_page_dE", "noise_e3", "noise_bg_e3",
            "weight_center", "weight_on_obj", "weight_in_text", "obj_share", "chroma_hi_pct_obj")
    short = {}
    for k in keys:
        v = m.get(k)
        if isinstance(v, dict):
            v = {kk: round(vv, 1) for kk, vv in v.items() if vv is not None}
        elif isinstance(v, list):
            v = [round(x, 3) for x in v]
        elif isinstance(v, float):
            v = round(v, 2)
        short[k] = v
    print(os.path.basename(frame), json.dumps(short, ensure_ascii=False))


if __name__ == "__main__":
    main()
