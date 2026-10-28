#!/usr/bin/env python3
"""make_judge2 — кадры и листы судьи фазы 2 (дорожка Z2) в 15-showcase/zveno/judge/.

    python3 make_judge2.py b            # out/judge/<состояние>.png → judge/b-blender__<состояние>.png
    python3 make_judge2.py c DIR        # DIR/<состояние>.png (lpz.py frames --b cz, 1600×1000) → judge/c-hybrid__<состояние>.png
    python3 make_judge2.py sheets       # по состоянию: пары A↔B и A↔C (ровно 2 кадра на лист, KIT §7) + обзор A/B/C
    python3 make_judge2.py pages DIR V  # снимки страницы (lpz.py shots) → judge/<V>__page-desk.jpg, __page-mob.jpg
"""
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
J = R + "/15-showcase/zveno/judge"
SHEET = R + "/15-showcase/_shared/sheet.py"
STATES = ["hero", "exploded", "locking", "first-move", "scan-half", "inside"]
NAMES = {"hero": "hero", "exploded": "разнос (станция 1)", "locking": "сборка (станция 2)", "first-move": "первое движение (станция 3)",
         "scan-half": "скан наполовину (станция 4)", "inside": "слои привода (станция 5)"}


def sheet(out, items, title, cols=2, tile=960):
    r = subprocess.run([sys.executable, SHEET, "--out", out, "--cols", str(cols), "--tile", str(tile), "--title", title]
                       + [f"{p}:{c}" for p, c in items], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr[-300:])


def main():
    what = sys.argv[1]
    if what == "b":
        # Z3 (оркестратор 26.09): состояния судьи — та же камера, что у a-code__*: hero B = камера кода t 0 (рендер hero-v2cam);
        # кадр камеры постера H4m — b-blender__hero-best.png (пара «лучший против лучшего», make_sheets.py pairs)
        mapping = {"hero-v2cam": ["hero", "hero-v2cam"], "hero": ["hero-best"]}
        for s in STATES + ["hero-v2cam"]:
            src = os.path.join(Z, "out", "judge", s + ".png")
            if os.path.exists(src):
                for dst in mapping.get(s, [s]):
                    shutil.copy(src, os.path.join(J, f"b-blender__{dst}.png")); print("B", s, "→", dst)
    elif what == "c":
        d = sys.argv[2]
        for s in STATES + ["hero-ik"]:
            src = os.path.join(d, s + ".png")
            if os.path.exists(src):
                shutil.copy(src, os.path.join(J, f"c-hybrid__{s}.png")); print("C", s)
    elif what == "sheets":
        for s in STATES:
            a, b, c = (os.path.join(J, f"{v}__{s}.png") for v in ("a-code", "b-blender", "c-hybrid"))
            if os.path.exists(a) and os.path.exists(b):
                sheet(os.path.join(J, f"sheet_z2_{s}_a-b.jpg"), [(a, "A — код v3"), (b, "B — Blender (предрендер, Cycles)")],
                      f"«Звено» · {NAMES[s]} · A ↔ B (та же камера)")
            if os.path.exists(a) and os.path.exists(c):
                sheet(os.path.join(J, f"sheet_z2_{s}_a-c.jpg"), [(a, "A — код v3"), (c, "C — гибрид (модули Blender в сцене кода)")],
                      f"«Звено» · {NAMES[s]} · A ↔ C (та же камера)")
        items = []
        for s in STATES:
            for v, lab in (("a-code", "A"), ("b-blender", "B"), ("c-hybrid", "C")):
                p = os.path.join(J, f"{v}__{s}.png")
                if os.path.exists(p):
                    items.append((p, f"{lab} · {NAMES[s]}"))
        sheet(os.path.join(J, "sheet_z2_overview.jpg"), items, "«Звено» · состояния судьи · A код v3 / B Blender / C гибрид (1600×1000)",
              cols=3, tile=640)
    elif what == "pages":
        d, v = sys.argv[2], sys.argv[3]
        for src, dst in (("desk_first.jpg", "page-desk"), ("mob_first.jpg", "page-mob")):
            p = os.path.join(d, src)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(J, f"{v}__{dst}.jpg")); print(v, dst, Image.open(p).size)


if __name__ == "__main__":
    main()
