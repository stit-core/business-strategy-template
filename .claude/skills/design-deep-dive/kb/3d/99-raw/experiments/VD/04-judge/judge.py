#!/usr/bin/env python3
"""VD/04-judge — кадры судьи, листы «нейросеть против Blender» и числа img_metrics по ракурсам (фаза 1 дуэли Velmora).

    python3 judge.py [--hero ../03-hero] [--tag hero]

Кладёт в 15-showcase/velmora/judge/: ai__fNNN.png, b-blender__fNNN.png (одинаковые 1280×720), листы sheet_fNNN.jpg (ровно
2 кадра: слева нейросеть, справа Blender), sheet_f180.jpg (Blender f000 | f180 — ракурс, которого у нейросети нет),
metrics.json (img_metrics по объекту — маска флакона, по этикетке и фону; зона текста 0…0,45 ширины; фон страницы #050607).
Маски нейросети — ручная разметка 00-ref/ai_masks.py; маски Blender — силуэт Workbench тем же кадром."""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VD = os.path.dirname(HERE)
R = "/home/mm/Документы/app-design/blender-research"
SH = f"{R}/15-showcase/_shared"
OUT = f"{R}/15-showcase/velmora/judge"
BG = "#050607"          # фон сцены страницы ai-media (.stage__media)
ZONE = "0,0,0.45,1"     # левая треть+ под заголовок (как на странице нейросети)


def metrics(img, mask, label_mask):
    def run(args):
        r = subprocess.run([sys.executable, f"{SH}/img_metrics.py", img] + args, capture_output=True, text=True, check=True)
        return json.loads(r.stdout)
    m = run(["--mask", mask, "--bg-hex", BG, "--text-zone", ZONE])
    try:
        lab = run(["--mask", label_mask])
    except subprocess.CalledProcessError:           # f180: этикетка на обороте — маска пустая
        lab = {"obj_L": {"p5": None, "p50": None, "p95": None, "max": None}, "noise_e3": None}
    keep = {k: m[k] for k in ("obj_L", "bg_L", "obj_minus_bg_L", "clip_obj_pct", "hi_obj_pct", "crush_obj_pct", "noise_e3",
                              "chroma_hi_pct_frame", "chroma_hi_pct_obj", "weight_center", "weight_on_obj", "weight_in_text",
                              "bg_vs_page_dE") if k in m}
    keep["label_L"] = lab["obj_L"]
    keep["label_noise_e3"] = lab["noise_e3"]        # шум по плоской бумаге — честнее, чем по рифлёному стеклу
    keep["mask_share"] = None
    return keep


def bg_noise(img):
    """Зерно рендера/сжатия на ровном тёмном фоне (0…0,25 ширины × 0,30…0,70 высоты — во всех ракурсах там только фон):
    СКО (L/100 − гаусс σ 2) ×10⁻³ — тем же методом, что img_metrics, но по плоскому месту."""
    sys.path.insert(0, SH)
    import numpy as np
    from PIL import Image
    import img_metrics as IM
    rgb = np.asarray(Image.open(img).convert("RGB")).astype(np.float64) / 255
    h, w = rgb.shape[:2]
    L = IM.rgb_to_lab(rgb[int(h * 0.30): int(h * 0.70), : int(w * 0.25)])[..., 0]
    hp = L / 100 - IM.gauss(L / 100, 2.0)
    return round(float(hp.std() * 1000), 3)


def mask_share(mask):
    from PIL import Image
    im = Image.open(mask).convert("L")
    px = im.getdata()
    return round(sum(1 for p in px if p > 127) / (im.width * im.height), 4)


def main():
    a = sys.argv[1:]
    hero = a[a.index("--hero") + 1] if "--hero" in a else os.path.join(VD, "03-hero")
    tag = a[a.index("--tag") + 1] if "--tag" in a else "hero"
    global OUT
    OUT = a[a.index("--out") + 1] if "--out" in a else OUT
    os.makedirs(OUT, exist_ok=True)
    res = {"bg_page_hex": BG, "text_zone": ZONE, "views": {}}
    for v in ("f000", "f030", "f060"):
        ai, ai_m, ai_l = (f"{VD}/00-ref/ai_{v}.png", f"{VD}/00-ref/ai_{v}_mask.png", f"{VD}/00-ref/ai_{v}_mask_label.png")
        bl, bl_m, bl_l = (f"{hero}/{tag}_{v}.png", f"{hero}/{tag}_{v}_mask.png", f"{hero}/{tag}_{v}_mask_label.png")
        shutil.copy(ai, f"{OUT}/ai__{v}.png")
        shutil.copy(bl, f"{OUT}/b-blender__{v}.png")
        row = {}
        for name, img, m, lm in (("ai", ai, ai_m, ai_l), ("b-blender", bl, bl_m, bl_l)):
            row[name] = metrics(img, m, lm)
            row[name]["mask_share"] = mask_share(m)
            row[name]["bg_noise_e3"] = bg_noise(img)
        res["views"][v] = row
        subprocess.run([sys.executable, f"{SH}/sheet.py", "--out", f"{OUT}/sheet_{v}.jpg", "--cols", "2", "--tile", "960",
                        "--title", f"Velmora · ракурс {v} · слева нейросеть (Kling 3), справа Blender (Cycles)",
                        f"{OUT}/ai__{v}.png:ai · Kling 3 std 720p · 57 ₽",
                        f"{OUT}/b-blender__{v}.png:b-blender · Cycles 128 спп + OIDN · 0 ₽"], check=True, capture_output=True)
    if os.path.exists(f"{hero}/{tag}_f180.png"):
        shutil.copy(f"{hero}/{tag}_f180.png", f"{OUT}/b-blender__f180.png")
        row = {"b-blender": metrics(f"{hero}/{tag}_f180.png", f"{hero}/{tag}_f180_mask.png", f"{hero}/{tag}_f180_mask_label.png")}
        row["b-blender"]["mask_share"] = mask_share(f"{hero}/{tag}_f180_mask.png")
        row["b-blender"]["bg_noise_e3"] = bg_noise(f"{hero}/{tag}_f180.png")
        res["views"]["f180"] = row
        subprocess.run([sys.executable, f"{SH}/sheet.py", "--out", f"{OUT}/sheet_f180.jpg", "--cols", "2", "--tile", "960",
                        "--title", "Velmora · Blender: фас f000 и обратная сторона f180 (у нейросети облёт только 25°)",
                        f"{OUT}/b-blender__f000.png:b-blender · f000 (фас)",
                        f"{OUT}/b-blender__f180.png:b-blender · f180 (180°, спина флакона)"], check=True, capture_output=True)
    json.dump(res, open(f"{OUT}/metrics.json", "w"), ensure_ascii=False, indent=1)
    # короткая таблица в консоль
    r2 = lambda x: "—" if x is None else (f"{x:.2f}" if isinstance(x, float) else str(x))  # noqa: E731
    print("| ракурс | вариант | L* объекта p50/p95 | этикетка p50/p95 | фон p50 | объект−фон | пересвет % | блик ≥97 % | шум ×10⁻³ | шум фона ×10⁻³ | ΔE фона к #050607 | вес на объекте | вес в зоне текста | доля кадра |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for v, row in res["views"].items():
        for name, m in row.items():
            print(f"| {v} | {name} | {r2(m['obj_L']['p50'])}/{r2(m['obj_L']['p95'])} | {r2(m['label_L']['p50'])}/{r2(m['label_L']['p95'])} | "
                  f"{r2(m['bg_L']['p50'])} | {r2(m['obj_minus_bg_L'])} | {r2(m['clip_obj_pct'])} | {r2(m['hi_obj_pct'])} | {r2(m['noise_e3'])} | {r2(m.get('bg_noise_e3'))} | "
                  f"{r2(m.get('bg_vs_page_dE'))} | {r2(m.get('weight_on_obj'))} | {r2(m.get('weight_in_text'))} | {m['mask_share']} |")


if __name__ == "__main__":
    main()
