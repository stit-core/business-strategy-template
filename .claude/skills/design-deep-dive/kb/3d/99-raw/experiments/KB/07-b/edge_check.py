#!/usr/bin/env python3
"""edge_check.py — край кадров B к цвету раздела: ΔE2000 по рамке кадра (внешние 3 px) и в полосе 3–40 px.
    python3 edge_check.py [web_img_dir]   → max/p95/сред. ΔE по рамке для type/*, x/*, turn/*/d_000/m_000."""
import sys, os, glob, json
import numpy as np
from PIL import Image
sys.path.insert(0, "/home/mm/Документы/app-design/blender-research/15-showcase/_shared")
import img_metrics as IM
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "assets", "img")
BG = {"type": (0x1C, 0x1D, 0x20), "x": (0xED, 0xEF, 0xF0), "snow": (0xED, 0xEF, 0xF0), "graphite": (0x14, 0x16, 0x19), "linen": (0xEF, 0xE8, 0xDC)}
def de_border(p, bg, w0=0, w1=3):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float64) / 255
    H, W, _ = a.shape
    m = np.zeros((H, W), bool)
    m[w0:w1, :] = m[H - w1:H - w0, :] = True; m[:, w0:w1] = m[:, W - w1:W - w0] = True
    lab = IM.rgb_to_lab(a[m][None, :, :])[0]
    ref = IM.rgb_to_lab((np.array(bg, float) / 255)[None, None, :])[0, 0]
    d = np.sqrt(((lab - ref) ** 2).sum(-1))          # ΔE76 (грубо, но строже к серому)
    return round(float(d.max()), 2), round(float(np.percentile(d, 95)), 2), round(float(d.mean()), 2)
out = {}
for p in sorted(glob.glob(f"{D}/type/*.avif")) + sorted(glob.glob(f"{D}/x/*.avif")) + sorted(glob.glob(f"{D}/turn/*/[dm]_000.avif")):
    rel = os.path.relpath(p, D)
    key = "type" if rel.startswith("type") else "x" if rel.startswith("x") else rel.split("/")[1]
    out[rel] = {"edge3": de_border(p, BG[key]), "band3_40": de_border(p, BG[key], 3, 40)}
print(json.dumps(out, ensure_ascii=False, indent=0))
