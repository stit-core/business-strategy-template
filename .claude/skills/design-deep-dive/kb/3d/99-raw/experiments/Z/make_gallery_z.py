#!/usr/bin/env python3
"""make_gallery_z — галерея приёмов вариантов B и C «Звена» (дорожка Z3, 26.09.2026): картинки 1200×750 WebP q80 в
15-showcase/zveno/gallery/z-*.webp и список 15-showcase/zveno/gallery-Z.json (поля — по заданию оркестратора).

    python3 make_gallery_z.py            # собрать всё, что есть на диске (нет исходника — приём пропускается с предупреждением)
Картинка приёма — 1–4 кадра-доказательства с подписями (DejaVu Sans), тёмный фон страницы #101215.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
ZV = R + "/15-showcase/zveno"
G = ZV + "/gallery"
W, H = 1200, 750
BG = (16, 18, 21)


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def fit(im, w, h):
    """cover-обрезка по центру до w×h"""
    im = im.convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def contain(im, w, h):
    im = im.convert("RGB")
    s = min(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    c = Image.new("RGB", (w, h), BG); c.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return c


def tile(panels, title, mode="cover"):
    """panels: [(путь | Image, подпись, crop (x0,y0,x1,y1 в долях) | None)]; 1 → весь кадр, 2 → рядом, 3–4 → сетка 2×2"""
    n = len(panels)
    can = Image.new("RGB", (W, H), BG)
    top = 44
    if n == 1:
        cells = [(0, top, W, H - top)]
    elif n == 2:
        cells = [(0, top, W // 2 - 3, H - top), (W // 2 + 3, top, W // 2 - 3, H - top)]
    else:
        hh = (H - top - 6) // 2
        cells = [(0, top, W // 2 - 3, hh), (W // 2 + 3, top, W // 2 - 3, hh), (0, top + hh + 6, W // 2 - 3, hh), (W // 2 + 3, top + hh + 6, W // 2 - 3, hh)]
    d = ImageDraw.Draw(can)
    d.text((14, 11), title, font=font(20), fill=(236, 235, 230))
    for (src, cap, crop), (x, y, w, h) in zip(panels, cells):
        im = src if isinstance(src, Image.Image) else Image.open(src)
        if crop:
            a, b, c, e = crop
            im = im.crop((int(a * im.width), int(b * im.height), int(c * im.width), int(e * im.height)))
        im = fit(im, w, h) if mode == "cover" else contain(im, w, h)
        can.paste(im, (x, y))
        f = font(15)
        bb = d.textbbox((0, 0), cap, font=f)
        d.rectangle((x, y + h - (bb[3] - bb[1]) - 14, x + (bb[2] - bb[0]) + 16, y + h), fill=(0, 0, 0))
        d.text((x + 8, y + h - (bb[3] - bb[1]) - 9), cap, font=f, fill=(255, 190, 120))
    return can


def main():
    spec = json.load(open(os.path.join(Z, "gallery_spec.json")))
    os.makedirs(G, exist_ok=True)
    out = []
    for it in spec:
        panels = []
        for p in it["panels"]:
            path = p[0] if os.path.isabs(p[0]) else os.path.join(R, p[0])
            if not os.path.exists(path):
                print("нет исходника", it["id"], path, file=sys.stderr); panels = None; break
            panels.append((path, p[1], p[2] if len(p) > 2 else None))
        if not panels:
            continue
        im = tile(panels, it["title"], it.get("mode", "cover"))
        fp = os.path.join(G, it["id"] + ".webp")
        im.save(fp, "WEBP", quality=80, method=6)
        rec = {k: it[k] for k in ("id", "variant", "title", "how", "cost", "weight", "gates", "helped")}
        rec["img"] = f"gallery/{it['id']}.webp"
        out.append(rec)
        print(it["id"], round(os.path.getsize(fp) / 1024, 1), "КБ")
    json.dump(out, open(os.path.join(ZV, "gallery-Z.json"), "w"), ensure_ascii=False, indent=1)
    print("gallery-Z.json:", len(out), "приёмов")


if __name__ == "__main__":
    main()
