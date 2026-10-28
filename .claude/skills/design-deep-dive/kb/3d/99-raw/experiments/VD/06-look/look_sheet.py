#!/usr/bin/env python3
"""VD2/06-look — лист итерации «эталон против нас» по f030 (ровно 2 кадра, sheet.py) + числа img_metrics (маски флакона и
этикетки — как у судьи фазы 1: 04-judge/judge.py, функции metrics/bg_noise/mask_share) + сравнение с v5.

    python3 look_sheet.py DIR [--tag hero] [--name i2] [--frame 030]   → DIR/sheet_f030.jpg, DIR/metrics_f030.json (+ строка таблицы)
    --frame NNN — имя кадра облёта (DIR/<tag>_NNN.png вместо DIR/<tag>_f030.png; VD3: кадр 030 дуги = ракурс f030)"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VD = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(VD, "04-judge"))
import judge as J  # noqa: E402

KEYS = [("obj_L", "p50"), ("label_L", "p50"), ("bg_L", "p50"), ("clip_obj_pct", None), ("hi_obj_pct", None),
        ("bg_vs_page_dE", None), ("weight_on_obj", None), ("weight_in_text", None), ("bg_noise_e3", None),
        ("chroma_hi_pct_frame", None)]


def row(m):
    out = {}
    for k, sub in KEYS:
        v = m.get(k)
        out[k + ("." + sub if sub else "")] = round(v[sub], 2) if (sub and v) else (round(v, 3) if isinstance(v, float) else v)
    return out


def main():
    a = sys.argv[1:]
    d = a[0]
    tag = a[a.index("--tag") + 1] if "--tag" in a else "hero"
    name = a[a.index("--name") + 1] if "--name" in a else os.path.basename(d.rstrip("/"))
    v = "f030"
    fr = a[a.index("--frame") + 1] if "--frame" in a else v
    ai, ai_m, ai_l = (f"{VD}/00-ref/ai_{v}.png", f"{VD}/00-ref/ai_{v}_mask.png", f"{VD}/00-ref/ai_{v}_mask_label.png")
    bl, bl_m, bl_l = (f"{d}/{tag}_{fr}.png", f"{d}/{tag}_{fr}_mask.png", f"{d}/{tag}_{fr}_mask_label.png")
    v5, v5_m, v5_l = (f"{VD}/03-hero-v5/hero_{v}.png", f"{VD}/03-hero-v5/hero_{v}_mask.png", f"{VD}/03-hero-v5/hero_{v}_mask_label.png")
    res = {}
    for key, img, m, lm in (("ai", ai, ai_m, ai_l), ("v5", v5, v5_m, v5_l), (name, bl, bl_m, bl_l)):
        mm = J.metrics(img, m, lm)
        mm["mask_share"] = J.mask_share(m)
        mm["bg_noise_e3"] = J.bg_noise(img)
        res[key] = mm
    json.dump(res, open(f"{d}/metrics_{v}.json", "w"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, f"{J.SH}/sheet.py", "--out", f"{d}/sheet_{v}.jpg", "--cols", "2", "--tile", "960",
                    "--title", f"Velmora · {v} · слева нейросеть (Kling 3), справа Blender {name}",
                    f"{ai}:ai · Kling 3 std 720p · 57 ₽", f"{bl}:b-blender {name} · Cycles 128 спп + OIDN · 0 ₽"],
                   check=True, capture_output=True)
    for k, m in res.items():
        print(k, json.dumps(row(m), ensure_ascii=False))
    print("→", f"{d}/sheet_{v}.jpg")


if __name__ == "__main__":
    main()
