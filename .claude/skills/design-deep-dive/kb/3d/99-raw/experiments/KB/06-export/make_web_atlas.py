#!/usr/bin/env python3
"""make_web_atlas.py — полноцветные атласы колпачков для веба (гибрид C): одна текстура на расцветку.

    python3 make_web_atlas.py      → tex/kc_<cw>.png (2048×1536), tex/yo_<cw>.png (512×544), tex/kc_<cw>_m.png (512×384),
                                     tex/yo_<cw>_m.png (128×136), tex/atlas_web.json (ячейки + пустая ячейка для «чужого»
                                     просмотрщика)
Источник — маски Blender-атласа (01-build/out_web: R — основная надпись, G — вторая, 8 px/мм) и маска Ё (yo_top.png,
24 px/мм, «Ё» + «esc» 60 %). Ячейка заливается цветом роли (буквы / модификаторы), поверх — цвета надписей расцветки:
в glTF это обычный baseColorTexture, варианты KHR_materials_variants меняют материал (= текстуру) целиком.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbp  # noqa: E402

SRC = os.path.join(HERE, "..", "01-build", "out_web")
OUT = os.path.join(HERE, "tex")
os.makedirs(OUT, exist_ok=True)


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float64)


def main():
    meta = json.load(open(os.path.join(SRC, "atlas_legends.json")))
    W, H = meta["size"]
    m = np.asarray(Image.open(os.path.join(SRC, "atlas_legends.png")).convert("RGB")).astype(np.float64) / 255
    R, G = m[..., 0:1], m[..., 1:2]
    yo = np.asarray(Image.open(os.path.join(SRC, "yo_top.png")).convert("L")).astype(np.float64)[..., None] / 255
    keys = {k["id"]: k for k in kbp.keys()}
    out = {"size": [W, H], "cells": {}, "blank": "space"}
    for cw_name, cw in kbp.COLORWAYS.items():
        base = np.zeros((H, W, 3))
        base[:] = rgb(cw["alpha"])
        for kid, cell in meta["keys"].items():
            x0, y0, cwid, ch = cell["px"]
            base[y0:y0 + ch, x0:x0 + cwid] = rgb(cw["mod"] if keys[kid]["role"] == "mod" else cw["alpha"])
        img = base * (1 - R) + rgb(cw["legend1"]) * R
        img = img * (1 - G) + rgb(cw["legend2"]) * G
        im = Image.fromarray(np.clip(img, 0, 255).round().astype(np.uint8))
        im.save(os.path.join(OUT, f"kc_{cw_name}.png"), optimize=True)
        im.resize((W // 4, H // 4), Image.LANCZOS).save(os.path.join(OUT, f"kc_{cw_name}_m.png"), optimize=True)
        # Ё: своя текстура (крупная надпись «Ё» и «esc» — в общем атласе 8 px/мм «esc» не читается)
        y = rgb(cw["accent"]) * (1 - yo) + rgb(cw["legend_accent"]) * yo
        yi = Image.fromarray(np.clip(y, 0, 255).round().astype(np.uint8))
        yi.resize((512, 544), Image.LANCZOS).save(os.path.join(OUT, f"yo_{cw_name}.png"), optimize=True)
        yi.resize((128, 136), Image.LANCZOS).save(os.path.join(OUT, f"yo_{cw_name}_m.png"), optimize=True)
    for kid, cell in meta["keys"].items():
        out["cells"][kid] = {"off": cell["off"], "scl": cell["scl"]}
    # ячейка Ё в yo_*.png: верх колпачка (0..1 UV) → внутренняя часть с полем 4,5 мм (как kbb.keycap_material)
    kd = kbp.keycap_dims(1, "R1")
    mg = meta["margin_mm"] * 1e-3
    out["yo"] = {"scl": [kd["wt"] / (kd["wt"] + 2 * mg), kd["dt"] / (kd["dt"] + 2 * mg)],
                 "off": [mg / (kd["wt"] + 2 * mg), mg / (kd["dt"] + 2 * mg)]}
    json.dump(out, open(os.path.join(OUT, "atlas_web.json"), "w"), indent=1)
    sizes = {f: os.path.getsize(os.path.join(OUT, f)) for f in sorted(os.listdir(OUT)) if f.endswith(".png")}
    print(json.dumps({"atlas": [W, H], "files": sizes}, ensure_ascii=False))


if __name__ == "__main__":
    main()
