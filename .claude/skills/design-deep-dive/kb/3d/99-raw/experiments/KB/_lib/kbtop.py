#!/usr/bin/env python3
"""kbtop.py — «главная грань» белого товара: L* верха колпачков в точках, спроецированных из Blender (keytops_<H>.json).
    python3 kbtop.py КАДР.png keytops.json [роль=KC_alpha]  → медиана/мин/доля ≥ 85 по окнам 5×5 px в центрах верха."""
import json, sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, "/home/mm/Документы/app-design/blender-research/15-showcase/_shared")
import img_metrics as IM
img, pts = sys.argv[1], json.load(open(sys.argv[2]))
role = sys.argv[3] if len(sys.argv) > 3 else "KC_alpha"
rgb = np.asarray(Image.open(img).convert("RGB")).astype(np.float64) / 255
L = IM.rgb_to_lab(rgb)[..., 0]
h, w = L.shape
vals = {}
for kid, (x, y, mat) in pts.items():
    if not mat.startswith(role):
        continue
    xi, yi = int(round(x)), int(round(y))
    if 2 <= xi < w - 2 and 2 <= yi < h - 2:
        vals[kid] = float(np.median(L[yi - 2:yi + 3, xi - 2:xi + 3]))
v = np.array(list(vals.values()))
out = {"frame": os.path.basename(img), "role": role, "n": int(v.size), "top_L_median": round(float(np.median(v)), 1) if v.size else None,
       "top_L_min": round(float(v.min()), 1) if v.size else None, "share_ge_85": round(float((v >= 85).mean()), 2) if v.size else None,
       "yo": None}
if "yo" in pts:
    x, y, _ = pts["yo"]; out["yo_L"] = round(float(np.median(L[int(y) - 2:int(y) + 3, int(x) - 2:int(x) + 3])), 1)
print(json.dumps(out, ensure_ascii=False))
