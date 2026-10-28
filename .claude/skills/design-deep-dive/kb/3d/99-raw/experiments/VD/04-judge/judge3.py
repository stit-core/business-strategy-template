#!/usr/bin/env python3
"""VD3/04-judge — судья фазы 3 дуэли Velmora: кадры облёта вместо чистовых фазы 1 (метрики — функции judge.py фазы 1).

    python3 judge3.py [--part pairs|f180|360|first|all] [--out DIR]

pairs — ai / b-blender f000 / f030 / f060: нейросеть — кадры 00-ref (из AVIF эталона), Blender — кадры дуги
        07-orbit/arc/o25_000 / 030 / 060 (i3, 128 спп + OIDN, вторичное движение ленты) → velmora/judge/{ai,b-blender}__fNNN.png,
        листы sheet_fNNN.jpg (ровно 2 кадра), числа в metrics.json;
f180  — Blender: фас (дуга 000) и спина (круг 360°, кадр 036 = 180°) → b-blender__f180.png, sheet_f180.jpg;
360   — лист круга 0° / 90° / 180° / 270° (кадры 000 / 018 / 036 / 054) → sheet_360.jpg (+ числа по маскам);
first — лист «первый экран» 1440 × 900: ai__first-screen-desk.png против b-blender__first-screen-desk.png → sheet_first-screen.jpg
        (снимки делает 10-shots/shots.py first; здесь только лист).
metrics.json дополняется по частям (что уже посчитано — сохраняется)."""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VD = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import judge as J  # noqa: E402

OUT = f"{J.R}/15-showcase/velmora/judge"
ARC = f"{VD}/07-orbit/arc"
FULL = f"{VD}/07-orbit/full"
VIEWS = {"f000": "000", "f030": "030", "f060": "060"}


def meta_spp(d, tag):
    try:
        return J_spp_cache[(d, tag)]
    except KeyError:
        pass
    spp = set()
    for f in os.listdir(d):
        if f.startswith(tag + "_stats") and f.endswith(".json"):
            st = json.load(open(os.path.join(d, f)))
            if st.get("views"):
                spp.add(st.get("samples"))
    J_spp_cache[(d, tag)] = "/".join(str(x) for x in sorted(spp)) or "?"
    return J_spp_cache[(d, tag)]


J_spp_cache = {}


def full_metrics(img, m, lm):
    mm = J.metrics(img, m, lm)
    mm["mask_share"] = J.mask_share(m)
    mm["bg_noise_e3"] = J.bg_noise(img)
    return mm


def sheet(out, title, *items):
    subprocess.run([sys.executable, f"{J.SH}/sheet.py", "--out", out, "--cols", "2", "--tile", "960", "--title", title,
                    *[f"{p}:{lab}" for p, lab in items]], check=True, capture_output=True)


def part_pairs(res):
    spp = meta_spp(ARC, "o25")
    for v, n in VIEWS.items():
        ai, ai_m, ai_l = (f"{VD}/00-ref/ai_{v}.png", f"{VD}/00-ref/ai_{v}_mask.png", f"{VD}/00-ref/ai_{v}_mask_label.png")
        bl, bl_m, bl_l = (f"{ARC}/o25_{n}.png", f"{ARC}/o25_{n}_mask.png", f"{ARC}/o25_{n}_mask_label.png")
        if not os.path.exists(bl):
            print("нет кадра", bl)
            continue
        shutil.copy(ai, f"{OUT}/ai__{v}.png")
        shutil.copy(bl, f"{OUT}/b-blender__{v}.png")
        res["views"][v] = {"ai": full_metrics(ai, ai_m, ai_l), "b-blender": full_metrics(bl, bl_m, bl_l),
                           "b-blender_src": os.path.relpath(bl, VD)}
        sheet(f"{OUT}/sheet_{v}.jpg", f"Velmora · ракурс {v} · слева нейросеть (Kling 3), справа Blender (Cycles, облёт)",
              (f"{OUT}/ai__{v}.png", "ai · Kling 3 std 720p · 57 ₽"),
              (f"{OUT}/b-blender__{v}.png", f"b-blender · Cycles {spp} спп + OIDN · кадр {n} облёта · 0 ₽"))
        print("пара", v, "→", f"{OUT}/sheet_{v}.jpg")


def part_f180(res):
    src = f"{FULL}/o360_036.png"
    if not os.path.exists(src):
        print("нет кадра", src)
        return
    shutil.copy(src, f"{OUT}/b-blender__f180.png")
    m = full_metrics(src, f"{FULL}/o360_036_mask.png", f"{FULL}/o360_036_mask_label.png")
    m["bg_noise_e3"] = None          # в участке замера зерна на 180° — лента (как в фазе 1)
    res["views"]["f180"] = {"b-blender": m, "b-blender_src": os.path.relpath(src, VD)}
    sheet(f"{OUT}/sheet_f180.jpg", "Velmora · Blender: фас и спина флакона (180°) — у нейросети облёт только 25°",
          (f"{ARC}/o25_000.png", "b-blender · фас (кадр 000 дуги)"),
          (src, f"b-blender · 180°, спина флакона (кадр 036 круга, {meta_spp(FULL, 'o360')} спп)"))
    print("f180 →", f"{OUT}/sheet_f180.jpg")


def part_360(res):
    names = [("000", "0° · фас"), ("018", "90° · бок"), ("036", "180° · спина"), ("054", "270° · бок")]
    items = []
    res.setdefault("full360", {})
    for n, lab in names:
        p = f"{FULL}/o360_{n}.png"
        if not os.path.exists(p):
            print("нет кадра", p)
            return
        items.append((p, f"b-blender · {lab} (кадр {n})"))
        mk, ml = f"{FULL}/o360_{n}_mask.png", f"{FULL}/o360_{n}_mask_label.png"
        if os.path.exists(mk):
            m = full_metrics(p, mk, ml)
            if n == "036":
                m["bg_noise_e3"] = None
            res["full360"][n] = m
    sheet(f"{OUT}/sheet_360.jpg", f"Velmora · Blender: полный круг 360° — 0° / 90° / 180° / 270° ({meta_spp(FULL, 'o360')} спп + OIDN)",
          *items)
    print("360 →", f"{OUT}/sheet_360.jpg")


def part_first(res):
    a, b = f"{OUT}/ai__first-screen-desk.png", f"{OUT}/b-blender__first-screen-desk.png"
    if not (os.path.exists(a) and os.path.exists(b)):
        print("нет снимков первого экрана")
        return
    sheet(f"{OUT}/sheet_first-screen.jpg", "Velmora · первый экран 1440 × 900 (тот же момент после загрузки) · слева нейросеть, справа Blender",
          (a, "ai · страница нейросети (копия эталона)"), (b, "b-blender · та же разметка и scrub.js, кадры Cycles"))
    res["first_screen"] = {"ai": os.path.basename(a), "b-blender": os.path.basename(b), "size": [1440, 900]}
    print("first →", f"{OUT}/sheet_first-screen.jpg")


def main():
    a = sys.argv[1:]
    part = a[a.index("--part") + 1] if "--part" in a else "all"
    global OUT
    OUT = a[a.index("--out") + 1] if "--out" in a else OUT      # проба — во временную папку
    os.makedirs(OUT, exist_ok=True)
    mp = f"{OUT}/metrics.json"
    res = json.load(open(mp)) if os.path.exists(mp) else {}
    res.update({"bg_page_hex": J.BG, "text_zone": J.ZONE, "phase": "3 (VD3, 26.09.2026): кадры облёта i3"})
    res.setdefault("views", {})
    for name, fn in (("pairs", part_pairs), ("f180", part_f180), ("360", part_360), ("first", part_first)):
        if part in (name, "all"):
            fn(res)
    json.dump(res, open(mp, "w"), ensure_ascii=False, indent=1)
    r2 = lambda x: "—" if x is None else (f"{x:.2f}" if isinstance(x, float) else str(x))  # noqa: E731
    print("| ракурс | вариант | L* флакона p50/p95 | этикетка p50 | фон p50 | пересвет % | блик ≥97 % | зерно фона ×10⁻³ | ΔE фона | вес на объекте / в зоне текста | доля кадра |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    rows = [(v, k, m) for v, row in res["views"].items() for k, m in row.items() if isinstance(m, dict)]
    rows += [(f"360/{n}", "b-blender", m) for n, m in res.get("full360", {}).items()]
    for v, k, m in rows:
        print(f"| {v} | {k} | {r2(m['obj_L']['p50'])}/{r2(m['obj_L']['p95'])} | {r2(m['label_L']['p50'])} | {r2(m['bg_L']['p50'])} | "
              f"{r2(m['clip_obj_pct'])} | {r2(m['hi_obj_pct'])} | {r2(m.get('bg_noise_e3'))} | {r2(m.get('bg_vs_page_dE'))} | "
              f"{r2(m.get('weight_on_obj'))} / {r2(m.get('weight_in_text'))} | {m.get('mask_share')} |")


if __name__ == "__main__":
    main()
