#!/usr/bin/env python3
"""zmetrics — числа кадра «Звена» до глаз: общий img_metrics.py (маска руки и маска белого лака) + свои добавки дорожки Z:
края кадра к странице (низ и левый край — где постер встречает страницу), шум на гладком лаке (без рёбер и печати).

    python3 zmetrics.py КАДР.png [КАДР2.png …] --out table.json [--page '#101215'] [--text 0,0,0.45,1]
Маска — КАДР_mask.png рядом (альфа — рука, R — видимый белый лак), её пишет zrender.py.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

SH = "/home/mm/Документы/app-design/blender-research/15-showcase/_shared"
sys.path.insert(0, SH)
import img_metrics as IM  # noqa: E402


def split_masks(mask_path, tmp_dir):
    m = np.asarray(Image.open(mask_path).convert("RGBA")).astype(np.float64) / 255
    obj = (m[..., 3] > 0.5)
    shell = obj & (m[..., 0] > 0.5)
    po, ps = os.path.join(tmp_dir, "m_obj.png"), os.path.join(tmp_dir, "m_shell.png")
    Image.fromarray((obj * 255).astype(np.uint8)).save(po)
    Image.fromarray((shell * 255).astype(np.uint8)).save(ps)
    return po, ps, obj, shell


def run_im(img, mask, page, text):
    r = subprocess.run([sys.executable, os.path.join(SH, "img_metrics.py"), img, "--mask", mask, "--bg-hex", page,
                        "--text-zone", text], capture_output=True, text=True)
    return json.loads(r.stdout)


def extra(img, obj, shell, page):
    rgb = np.asarray(Image.open(img).convert("RGB")).astype(np.float64) / 255
    lab = IM.rgb_to_lab(rgb)
    h, w = obj.shape
    pl = IM.rgb_to_lab(IM.hex_rgb(page)[None, None, :])[0, 0].tolist()

    def strip_de(sl):
        reg = lab[sl]; msk = ~obj[sl]
        med = [float(np.median(reg[..., i][msk])) for i in range(3)]
        return round(IM.de2000(med, pl), 2), round(med[0], 1)
    out = {"edge_bottom_dE_L": strip_de((slice(int(h * 0.94), h), slice(0, w))),
           "edge_left_dE_L": strip_de((slice(0, h), slice(0, int(w * 0.05)))),
           "edge_top_dE_L": strip_de((slice(0, int(h * 0.05)), slice(0, w)))}
    L = lab[..., 0]
    # гладкий лак: маска лака, эрозия 3 px, без сильного градиента (рёбра, печать, швы)
    from scipy import ndimage  # noqa
    er = ndimage.binary_erosion(shell, iterations=5)
    gy, gx = np.gradient(ndimage.gaussian_filter(L, 1.5))
    edges = ndimage.binary_dilation(np.hypot(gx, gy) > 1.0, iterations=4)     # любые рёбра, печать, швы — ±4 px
    flat = er & ~edges
    hp = L / 100 - IM.gauss(L / 100, 2.0)
    v = hp[flat]
    out["noise_flat_shell_e3"] = round(float(1.4826 * np.median(np.abs(v - np.median(v))) * 1000), 2) if v.size > 200 else None
    bgf = ndimage.binary_erosion(~obj, iterations=6) & ~edges
    vb = hp[bgf]
    out["noise_bg_e3"] = round(float(1.4826 * np.median(np.abs(vb - np.median(vb))) * 1000), 2) if vb.size > 200 else None
    out["flat_shell_px"] = int(flat.sum())
    Ls = L[shell]
    out["shell_L"] = {"p50": round(float(np.percentile(Ls, 50)), 1), "p75": round(float(np.percentile(Ls, 75)), 1), "p90": round(float(np.percentile(Ls, 90)), 1),
                      "p95": round(float(np.percentile(Ls, 95)), 1), "p99": round(float(np.percentile(Ls, 99)), 1)} if Ls.size else None
    out["obj_area_pct"] = round(float(obj.mean() * 100), 1)
    ys, xs = np.nonzero(obj)
    out["obj_bbox_frac"] = [round(xs.min() / w, 3), round(ys.min() / h, 3), round(xs.max() / w, 3), round(ys.max() / h, 3)]
    return out


def main():
    a = sys.argv[1:]

    def opt(n, d=None):
        if n in a:
            i = a.index(n); v = a[i + 1]; del a[i:i + 2]; return v
        return d
    out = opt("--out"); page = opt("--page", "#101215"); text = opt("--text", "0,0,0.45,1")
    rows = {}
    for img in a:
        mpath = img[:-4] + "_mask.png"
        tmp = os.path.dirname(os.path.abspath(img))
        po, ps, obj, shell = split_masks(mpath, tmp)
        m_obj = run_im(img, po, page, text)
        m_sh = run_im(img, ps, page, text)
        row = {"obj": {k: m_obj.get(k) for k in ("obj_L", "clip_obj_pct", "hi_obj_pct", "crush_obj_pct", "bg_L", "obj_minus_bg_L",
                                                  "bg_vs_page_dE", "noise_e3", "chroma_hi_pct_frame", "chroma_hi_pct_obj",
                                                  "weight_center", "weight_on_obj", "weight_in_text")},
               "shell": {k: m_sh.get(k) for k in ("obj_L", "clip_obj_pct", "hi_obj_pct")}}
        row.update(extra(img, obj, shell, page))
        rows[os.path.basename(img)] = row
        for p in (po, ps):
            os.remove(p)
    js = json.dumps(rows, ensure_ascii=False, indent=1)
    if out:
        open(out, "w").write(js)
    # короткая таблица
    for k, r in rows.items():
        o, s = r["obj"], r["shell"]
        print(f"{k:22s} shell L p50/p90/p95 {r['shell_L']['p50'] if r['shell_L'] else '-'}/{r['shell_L']['p90'] if r['shell_L'] else '-'}/"
              f"{r['shell_L']['p95'] if r['shell_L'] else '-'} | hi≥97 obj {o['hi_obj_pct']:.2f}% clip {o['clip_obj_pct']:.2f}% | "
              f"obj−bg {o['obj_minus_bg_L']:.1f} | bgΔE {o['bg_vs_page_dE']:.2f} | edges b/l/t ΔE {r['edge_bottom_dE_L'][0]}/"
              f"{r['edge_left_dE_L'][0]}/{r['edge_top_dE_L'][0]} | noise obj {o['noise_e3']:.1f} flat {r['noise_flat_shell_e3']} bg {r['noise_bg_e3']} | "
              f"w_center {[round(x, 2) for x in o['weight_center']]} on_obj {o['weight_on_obj']:.2f} in_text {o['weight_in_text']:.2f} | "
              f"area {r['obj_area_pct']}%")


if __name__ == "__main__":
    main()
