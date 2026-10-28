#!/usr/bin/env python3
"""VD3/11-gallery — галерея приёмов дуэли Velmora: 15-showcase/velmora/gallery.json + gallery/<id>.webp (1200 × 750, WebP q80).

    python3 gallery.py [--dry]      # --dry: только проверить источники

Картинки — вырезы из кадров без повторного рендера: 2560 × 1440 (07-orbit/poster2k/o25_2k_000.png; нет — кадр 000 дуги
1280, увеличенный), кадры дуги и круга, кадры эталона (00-ref, из AVIF нейросети). Тексты приёмов — в ITEMS ниже (цена, вес,
ворота, итог — по журналам VD: NOTES.md, rules.md, 07-orbit/*/_batches.jsonl, 08-enc/results_*.json)."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

R = "/home/mm/Документы/app-design/blender-research"
VD = f"{R}/99-raw/experiments/VD"
V = f"{R}/15-showcase/velmora"
W, H = 1200, 750
P2K = f"{VD}/07-orbit/poster2k/o25_2k_000.png"
ARC = f"{VD}/07-orbit/arc"
FULL = f"{VD}/07-orbit/full"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def src2k():
    if os.path.exists(P2K) and Image.open(P2K).width >= 2560:      # не заглушка 8 × 8 (VD3: poster2k после круга)
        return Image.open(P2K).convert("RGB")
    return Image.open(f"{ARC}/o25_000.png").convert("RGB").resize((2560, 1440), Image.LANCZOS)


def crop_frac(im, x0, y0, wf):
    """Вырез с левым верхом (x0, y0) в долях и шириной wf (доля ширины), пропорция 1,6 → 1200 × 750."""
    w = round(im.width * wf)
    h = round(w * H / W)
    x = round(im.width * x0)
    y = min(round(im.height * y0), im.height - h)
    return im.crop((x, y, x + w, y + h)).resize((W, H), Image.LANCZOS)


def label(im, text, xy=(18, 14)):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 22)
    x, y = xy
    tw = d.textlength(text, font=f)
    d.rectangle((x - 8, y - 5, x + tw + 8, y + 29), fill=(10, 12, 15))
    d.text((x, y), text, font=f, fill=(236, 235, 230))
    return im


def tiles(paths_labels, cols, rows, box=None):
    """Сетка cols × rows из кадров 1280 × 720: каждый — вырез box (доли x0, y0, x1, y1) под пропорцию клетки."""
    tw, th = W // cols, H // rows
    out = Image.new("RGB", (W, H), (5, 6, 7))
    for k, (p, lab) in enumerate(paths_labels):
        im = Image.open(p).convert("RGB")
        x0, y0, x1, y1 = box or (0, 0, 1, 1)
        cw, ch = (x1 - x0) * im.width, (y1 - y0) * im.height
        # подогнать вырез под пропорцию клетки (по центру заданного окна)
        if cw / ch > tw / th:
            nw = ch * tw / th
            cx = (x0 * im.width + x1 * im.width) / 2
            bx = (cx - nw / 2, y0 * im.height, cx + nw / 2, y1 * im.height)
        else:
            nh = cw * th / tw
            cy = (y0 * im.height + y1 * im.height) / 2
            bx = (x0 * im.width, cy - nh / 2, x1 * im.width, cy + nh / 2)
        t = im.crop(tuple(round(v) for v in bx)).resize((tw, th), Image.LANCZOS)
        if lab:
            label(t, lab, (12, 10))
        out.paste(t, ((k % cols) * tw, (k // cols) * th))
    d = ImageDraw.Draw(out)
    for c in range(1, cols):
        d.line((c * tw, 0, c * tw, H), fill=(5, 6, 7), width=4)
    for r in range(1, rows):
        d.line((0, r * th, W, r * th), fill=(5, 6, 7), width=4)
    return out


def img_ribbon():
    return crop_frac(src2k(), *CROPS["ribbon-dome"])


def img_dispersion():
    return crop_frac(src2k(), *CROPS["dispersion-3glass"])


def img_air():
    return tiles([(f"{VD}/03-hero-v5/hero_f030.png", "v5 (фаза 1): чёрная пустота"),
                  (f"{VD}/06-look/i3/hero_f030.png", "i3: свет по складкам за лентой")], 2, 1, (0.40, 0.0, 0.95, 1.0))


def img_granite():
    return crop_frac(src2k(), *CROPS["granite-mica"])


def img_sway():
    # только кадры круга (без запасных кадров дуги — подписи 90° / 270° должны быть правдой)
    return tiles([(f"{FULL}/o360_018.png", "стол 90°: фаза закрута 82°"),
                  (f"{FULL}/o360_054.png", "стол 270°: фаза закрута 58°")], 2, 1, (0.30, 0.0, 1.0, 1.0))


def img_full():
    fs = [("000", "0° · фас"), ("018", "90°"), ("036", "180° · спина"), ("054", "270°")]
    return tiles([(f"{FULL}/o360_{n}.png", lab) for n, lab in fs], 2, 2, (0.30, 0.0, 1.0, 1.0))


def img_label():
    return crop_frac(src2k(), *CROPS["label-exact"])


def img_ai_ribbon():
    return tiles([(f"{VD}/00-ref/ai_f000.png", "ai f000"), (f"{VD}/00-ref/ai_f060.png", "ai f060: лента другая, справа панель")],
                 2, 1, (0.30, 0.0, 1.0, 1.0))


def img_ai_rays():
    im = Image.open(f"{VD}/00-ref/ai_f000.png").convert("RGB")
    return crop_frac(im, *CROPS["ai-caustic-rays"])


# вырезы (x0, y0, доля ширины) — по кадру 2560 × 1440 (кадр 000 дуги) и кадрам эталона
CROPS = {
    "ribbon-dome": (0.27, 0.0, 0.47),
    "dispersion-3glass": (0.77, 0.30, 0.23),
    "granite-mica": (0.40, 0.55, 0.47),
    "label-exact": (0.52, 0.30, 0.42),
    "ai-caustic-rays": (0.40, 0.58, 0.45),
}

ITEMS = [
    dict(id="ribbon-dome", variant="b-blender", title="Лента светится «средой», а не лампами", make=img_ribbon),
    dict(id="dispersion-3glass", variant="b-blender", title="Дисперсия тремя стёклами на клиновидной кромке", make=img_dispersion),
    dict(id="air-folds", variant="b-blender", title="«Воздух» — светом по складкам за лентой, а не дымкой", make=img_air),
    dict(id="granite-mica", variant="b-blender", title="Гранит со слюдой под лаком", make=img_granite),
    dict(id="secondary-motion", variant="b-blender", title="Вторичное движение ленты", make=img_sway),
    dict(id="full-360", variant="b-blender", title="Полный круг 360° по кнопке", make=img_full),
    dict(id="label-exact", variant="b-blender", title="Точная этикетка: антиква, вторая строка, краска в бумаге", make=img_label),
    dict(id="ai-ribbon-flow", variant="ai", title="Нейросеть: лента — светящаяся полоса, но мир плывёт", make=img_ai_ribbon),
    dict(id="ai-caustic-rays", variant="ai", title="Нейросеть: лучи «от дна» на камне — вероятно, вымысел", make=img_ai_rays),
]


def main():
    dry = "--dry" in sys.argv
    texts = json.load(open(f"{VD}/11-gallery/texts.json"))
    os.makedirs(f"{V}/gallery", exist_ok=True)
    out = []
    for it in ITEMS:
        t = texts[it["id"]]
        rec = {"id": it["id"], "variant": it["variant"], "title": it["title"], "how": t["how"], "cost": t["cost"],
               "weight": t["weight"], "gates": t["gates"], "helped": t["helped"], "img": f"gallery/{it['id']}.webp"}
        if not dry:
            try:
                im = it["make"]()
                im.save(f"{V}/gallery/{it['id']}.webp", quality=80, method=6)
                rec["img_kb"] = round(os.path.getsize(f"{V}/gallery/{it['id']}.webp") / 1024, 1)
            except FileNotFoundError as e:
                print("нет источника:", it["id"], e)
                continue
        out.append(rec)
        print(it["id"], rec.get("img_kb"))
    if not dry:
        json.dump(out, open(f"{V}/gallery.json", "w"), ensure_ascii=False, indent=1)
        print("→", f"{V}/gallery.json", len(out), "приёмов")


if __name__ == "__main__":
    main()
