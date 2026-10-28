#!/usr/bin/env python3
"""make_sheets — листы дорожки Z в 15-showcase/zveno/judge/ (общий _shared/sheet.py) и кадры для судьи.

    python3 make_sheets.py hero BEST.png            # v2 ↔ B (ровно 2 кадра) + варианты hero с числами
    python3 make_sheets.py xray                     # рентген B ↔ скан v2
    python3 make_sheets.py web [out/web_lean]       # модуль J2: Blender ↔ three (по умолчанию облегчённый прогон)
    python3 make_sheets.py pairs [A_BEST.png]       # решение оркестратора 25.09: две пары для судьи
        · «та же камера»: v2 ↔ B H1c (контролируемое сравнение ремесла)
        · «лучший против лучшего»: A код v3 (по умолчанию judge/a-code__hero.png) ↔ B H4m (сравнение на вау)
"""
import json
import os
import shutil
import subprocess
import sys

from PIL import Image

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
J = R + "/15-showcase/zveno/judge"
CR = "/home/mm/Документы/app-design/creative-research"
SHEET = R + "/15-showcase/_shared/sheet.py"
os.makedirs(J, exist_ok=True)


def sheet(out, items, title, cols=2, tile=960):
    r = subprocess.run([sys.executable, SHEET, "--out", out, "--cols", str(cols), "--tile", str(tile), "--title", title]
                       + [f"{p}:{c}" for p, c in items], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr[-400:])


def v2_hero_png():
    dst = os.path.join(J, "v2-base__hero.png")
    Image.open(f"{CR}/10-recipes/examples/l2-zveno/img/hero-d.webp").convert("RGB").save(dst)
    return dst


def cap(m, name):
    r = m[name]
    s = r["shell_L"]
    p75 = f"{s['p75']:.0f}" if s.get("p75") else "—"
    return (f"лак {s['p50']:.0f}/{p75}/{s['p90']:.0f} · блик {r['obj']['hi_obj_pct']:.1f}% · фон ΔE {r['obj']['bg_vs_page_dE']:.1f}"
            f" · низ {r['edge_bottom_dE_L'][0]:.1f}")


def main():
    what = sys.argv[1]
    if what == "hero":
        best = sys.argv[2]
        dst = os.path.join(J, "b-blender__hero.png")
        shutil.copy(best, dst)
        v2 = v2_hero_png()
        sheet(os.path.join(J, "sheet_z_hero_v2-vs-b.jpg"), [(v2, "v2 — код (база, J/04 hero-d)"), (dst, "B — Blender (Cycles 128 спп)")],
              "«Звено» · hero · v2 кодом против B (Blender) · 1600×1000", cols=2, tile=960)
        m = {}
        for f in ("metrics_m.json", "metrics_c.json", "metrics_b.json", "metrics.json"):
            p = os.path.join(Z, "out/hero", f)
            if os.path.exists(p):
                m.update(json.load(open(p)))
        items = []
        for n, label in (("H1c_S1.png", "H1c кам. v2, S1"), ("H2b_S1H.png", "H2b кам. v2, S1+ореол"),
                         ("H3b_S1.png", "H3b 50 мм, S1"), ("H4m_S1H.png", "H4m 50 мм, S1+ореол")):
            p = os.path.join(Z, "out/hero", n)
            if os.path.exists(p) and n in m:
                items.append((p, f"{label} · {cap(m, n)}"))
        sheet(os.path.join(J, "sheet_z_hero-variants.jpg"), items, "«Звено» B · варианты hero (Cycles 128 спп + OIDN, 1600×1000) · лак p50/p75/p90 L* · блик ≥ 97 L* · фон и низ кадра — ΔE к #101215",
              cols=2, tile=960)
    elif what == "xray":
        src = os.path.join(Z, "out/xray2/xray_j3.png")
        dst = os.path.join(J, "b-blender__xray.png")
        shutil.copy(src, dst)
        v2 = os.path.join(J, "v2-base__inside.png")
        Image.open(f"{CR}/99-raw/experiments/J/04-light-pass/out/f-after/scan-half.png").convert("RGB").resize((1600, 1000), Image.LANCZOS).save(v2)
        sheet(os.path.join(J, "sheet_z_xray.jpg"), [(v2, "v2 — скан кодом (J/04 scan-half, 960×600 → 1600×1000)"),
                                                     (dst, "B — рентген Blender (Cycles 128 спп)")],
              "«Звено» · сустав внутри · скан кодом против рентгена Blender", cols=2, tile=960)
    elif what == "pairs":
        # Z3 (26.09): кадры B — рендеры фазы 2 (zseq, текущая модель): «та же камера» = камера кода t 0 (= v2 и A; сдвиг кадра
        # исправлен — у H1c фазы 1 было 0,125 ширины вместо 0,2); «лучший» — judge/b-blender__hero-best.png (камера постера H4m).
        # Прежняя ветка (H1c/H4m фазы 1, копия рентгена в scan-half) — make_sheets_z2.py.
        same = os.path.join(J, "b-blender__hero-v2cam.png")
        v2 = v2_hero_png()
        sheet(os.path.join(J, "sheet_z_pair_same-cam.jpg"), [(v2, "v2 — код (база, J/04 hero-d)"),
                                                            (same, "B — Blender, та же камера (камера кода t 0, Cycles 128 спп)")],
              "«Звено» · hero · пара «та же камера»: v2 ↔ B", cols=2, tile=960)
        a_best = sys.argv[2] if len(sys.argv) > 2 else os.path.join(J, "a-code__hero.png")
        best = os.path.join(J, "b-blender__hero-best.png")
        blab = sys.argv[3] if len(sys.argv) > 3 else "B — Blender, лучший (постер страницы B, камера H4m, Cycles 128 спп)"
        sheet(os.path.join(J, "sheet_z_pair_best.jpg"), [(a_best, f"A — код v3 ({os.path.basename(a_best)})"), (best, blab)],
              "«Звено» · hero · пара «лучший против лучшего»: A ↔ B", cols=2, tile=960)
    elif what == "web":
        if len(sys.argv) > 2 and sys.argv[2].lstrip().startswith("["):
            items = [(p, c) for p, c in json.loads(sys.argv[2])]
        else:                                   # по умолчанию — облегчённый прогон out/web_lean (или папка аргументом)
            W = os.path.join(Z, sys.argv[2] if len(sys.argv) > 2 else "out/web_lean")
            m = json.load(open(f"{W}/diff/diff_metrics.json")); b = json.load(open(f"{W}/bake.json"))
            im = Image.open(f"{W}/view/web_view_0_az35_el20.png"); w, h = im.size
            im.crop(((w - h) // 2, 0, (w - h) // 2 + h, h)).save(f"{W}/view/web_view_0_sq.png")
            m0 = m["metrics"][0]
            items = [(f"{W}/diff/blender_0.png", "Blender Cycles · веб-режим J2 · HDRI studio_small_09"),
                     (f"{W}/diff/three_0.png", f"three 0.186 · Neutral · тот же HDRI · {m['draw_calls'][0]} вызовов · {b['tris']} треуг."),
                     (f"{W}/diff/heat_0.png", f"ΔE2000 0…20 · средн. {m0['de2000_mean']} (по 3 видам {m['mean']['de2000_mean']}) · IoU {m['mean']['iou']}"),
                     (f"{W}/view/web_view_0_sq.png", f"three на фоне страницы · RoomEnvironment · {m['glb_kb']} КБ (meshopt + WebP)")]
        sheet(os.path.join(J, "sheet_z_web-j2.jpg"), items, "«Звено» B · модуль J2: Blender → GLB (AO запечён) → three 0.186 Neutral",
              cols=2, tile=800)


if __name__ == "__main__":
    main()
