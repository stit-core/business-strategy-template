#!/usr/bin/env python3
"""encode_seq — кадры Blender → поставка страницы B (дорожка Z2): секвенции AVIF, постеры AVIF + WebP, станции WebP 1200×750.

    python3 encode_seq.py test  PNG [PNG…]            # AVIF q 45/55/65 и WebP q80: вес и ΔE к исходнику (выбор качества)
    python3 encode_seq.py seq   story-d|story-m|scan-d|scan-m [--q 55]   # out/seq/<набор>/f*.png → b-blender/seq/<набор>/f*.avif
    python3 encode_seq.py posters [--q 60]            # out/judge/hero.png, hero-m.png → b-blender/img/hero-{d,m}.{avif,webp} + кадр 0 сюжета
    python3 encode_seq.py stations                    # out/judge/{exploded,locking,first-move,scan-half,inside}.png → img/st-*.webp
    python3 encode_seq.py report                      # вес наборов и сессии (десктоп / телефон) → out/seq/weights.json
Кодирование — Pillow 11.3 (libavif 1.3, aom), 8 бит, 4:2:0, speed 6. Качество кадра не снижаем ради веса (решение задания):
если сессия не влезает — меньше кадров, а не хуже кадр.
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
B = R + "/15-showcase/zveno/b-blender"
sys.path.insert(0, R + "/15-showcase/_shared")
import img_metrics as IM  # noqa: E402


def de_mean(a, b):
    la = IM.rgb_to_lab(np.asarray(a.convert("RGB")).astype(np.float64) / 255)
    lb = IM.rgb_to_lab(np.asarray(b.convert("RGB")).astype(np.float64) / 255)
    d = np.sqrt(((la - lb) ** 2).sum(-1))                      # ΔE76 — для сравнения кодеков достаточно
    return round(float(d.mean()), 3), round(float(np.percentile(d, 99)), 2)


def avif(im, path, q, speed=6):
    im.convert("RGB").save(path, "AVIF", quality=q, speed=speed, subsampling="4:2:0")
    return os.path.getsize(path)


def cmd_test(files):
    rows = []
    tmp = os.path.join(Z, "out", "enc_test"); os.makedirs(tmp, exist_ok=True)
    for f in files:
        im = Image.open(f).convert("RGB")
        for q in (45, 55, 65):
            p = os.path.join(tmp, f"{os.path.basename(f)[:-4]}_q{q}.avif")
            t = time.time(); n = avif(im, p, q); dt = time.time() - t
            rows.append({"file": os.path.basename(f), "fmt": f"avif q{q}", "kb": round(n / 1024, 1), "enc_s": round(dt, 2),
                         "dE_mean_p99": de_mean(im, Image.open(p))})
        p = os.path.join(tmp, f"{os.path.basename(f)[:-4]}_q80.webp")
        im.save(p, "WEBP", quality=80, method=6)
        rows.append({"file": os.path.basename(f), "fmt": "webp q80", "kb": round(os.path.getsize(p) / 1024, 1),
                     "dE_mean_p99": de_mean(im, Image.open(p))})
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))


def cmd_seq(name, q):
    src = os.path.join(Z, "out", "seq", name)
    dst = os.path.join(B, "seq", name); os.makedirs(dst, exist_ok=True)
    tot, n, t0 = 0, 0, time.time()
    for f in sorted(os.listdir(src)):
        if not (f.startswith("f") and f.endswith(".png")) or "_mask" in f:
            continue
        tot += avif(Image.open(os.path.join(src, f)), os.path.join(dst, f[:-4] + ".avif"), q)
        n += 1
    print(json.dumps({"set": name, "frames": n, "kb": round(tot / 1024, 1), "kb_per_frame": round(tot / 1024 / max(1, n), 1),
                      "enc_s": round(time.time() - t0, 1)}, ensure_ascii=False))


def cmd_posters(q):
    J = os.path.join(Z, "out", "judge")
    os.makedirs(os.path.join(B, "img"), exist_ok=True)
    out = {}
    for tag, src, seqdir in (("hero-d", "hero.png", "story-d"), ("hero-m", "hero-m.png", "story-m")):
        im = Image.open(os.path.join(J, src)).convert("RGB")
        out[tag + ".avif"] = avif(im, os.path.join(B, "img", tag + ".avif"), q)
        im.save(os.path.join(B, "img", tag + ".webp"), "WEBP", quality=85, method=6)
        out[tag + ".webp"] = os.path.getsize(os.path.join(B, "img", tag + ".webp"))
        d = os.path.join(B, "seq", seqdir); os.makedirs(d, exist_ok=True)
        avif(im, os.path.join(d, "f000.avif"), q)                  # кадр 0 сюжета = постер (тот же рендер, свой размер)
    print(json.dumps({k: round(v / 1024, 1) for k, v in out.items()}, ensure_ascii=False))


def cmd_stations():
    J = os.path.join(Z, "out", "judge")
    out = {}
    for st, src in (("st-exploded", "exploded"), ("st-locking", "locking"), ("st-first-move", "first-move"),
                    ("st-scan", "scan-half"), ("st-inside", "inside")):
        im = Image.open(os.path.join(J, src + ".png")).convert("RGB").resize((1200, 750), Image.LANCZOS)
        p = os.path.join(B, "img", st + ".webp")
        im.save(p, "WEBP", quality=80, method=6)
        out[st] = round(os.path.getsize(p) / 1024, 1)
    print(json.dumps(out, ensure_ascii=False))


def cmd_report():
    def kb(d):
        return sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)) / 1024 if os.path.isdir(d) else 0
    s = {n: round(kb(os.path.join(B, "seq", n)), 1) for n in ("story-d", "scan-d", "story-m", "scan-m")}
    img = {f: round(os.path.getsize(os.path.join(B, "img", f)) / 1024, 1) for f in sorted(os.listdir(os.path.join(B, "img")))}
    rep = {"seq_kb": s, "img_kb": img,
           "session_3d_desktop_kb": round(s["story-d"] + s["scan-d"] + img.get("hero-d.avif", 0), 1),
           "session_3d_phone_kb": round(s["story-m"] + s["scan-m"] + img.get("hero-m.avif", 0), 1),
           "budget_kb": {"desktop": 8192, "phone": 3072}}
    json.dump(rep, open(os.path.join(Z, "out", "seq", "weights.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))


def main():
    a = sys.argv[1:]

    def opt(n, d):
        return type(d)(a[a.index(n) + 1]) if n in a else d
    if a[0] == "test":
        cmd_test([x for x in a[1:] if x.endswith(".png")])
    elif a[0] == "seq":
        cmd_seq(a[1], opt("--q", 70))
    elif a[0] == "posters":
        cmd_posters(opt("--q", 75))
    elif a[0] == "stations":
        cmd_stations()
    elif a[0] == "report":
        cmd_report()


if __name__ == "__main__":
    main()
