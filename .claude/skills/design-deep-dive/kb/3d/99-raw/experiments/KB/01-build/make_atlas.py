#!/usr/bin/env python3
"""make_atlas.py — атлас надписей колпачков «Ё» (Pillow + Onest woff2, OFL). Каналы — маски: R — основная надпись
(кириллица, цифры, подписи модификаторов, RU-символы), G — вторая (латиница, EN-символы). Цвет надписей подставляет
материал расцветки (один атлас на три расцветки).

    python3 make_atlas.py [--ppm 24] [--out DIR]      → atlas_legends.png, atlas_legends.json, yo_top.png, yo_side.png,
                                                        brass_mark.png, atlas_preview.png
Ячейка = верх колпачка (Wt × Dt из паспорта) + поле 4,5 мм с каждой стороны: стенки при проекции на верх попадают в своё
пустое поле, соседние надписи не протекают. UV верха колпачка 0..1 → внутренняя часть ячейки.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbp  # noqa: E402

FONTS = "/home/mm/Документы/app-design/creative-research/10-recipes/examples/_shared/fonts/onest"
F_CYR = f"{FONTS}/onest-cyrillic-wght-normal.woff2"
F_LAT = f"{FONTS}/onest-latin-wght-normal.woff2"
F_SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"      # стрелки ← → (в подмножестве Onest их нет)
MARGIN_MM = 4.5


def arg(name, default):
    a = sys.argv
    return type(default)(a[a.index(name) + 1]) if name in a else default


PPM = arg("--ppm", 24)
OUT = arg("--out", os.path.join(HERE, "out"))
os.makedirs(OUT, exist_ok=True)
_cache = {}


def font_for(ch, px, wght):
    if "Ѐ" <= ch <= "ӿ" or ch == "№":
        path = F_CYR
    elif ch in "←→↑↓":
        path = F_SYM
    else:
        path = F_LAT
    key = (path, px, wght)
    if key not in _cache:
        f = ImageFont.truetype(path, px)
        if path != F_SYM:
            f.set_variation_by_axes([wght])
        _cache[key] = f
    return _cache[key]


def cap_ratio():
    """Доля кегля, которую занимает высота прописной «Н» у Onest (для надписей в миллиметрах)."""
    f = font_for("Н", 400, 500)
    b = f.getbbox("Н", anchor="ls")
    return (b[3] - b[1]) / 400


CAP = cap_ratio()


def draw_text(img, text, x_mm, y_mm, cap_mm, wght, anchor, ox, oy):
    """Надпись по базовой линии: x_mm, y_mm — от левого верхнего угла верха колпачка (мм); anchor — l/r/m + s (baseline)."""
    if not text:
        return
    px = max(6, round(cap_mm / CAP * PPM))
    d = ImageDraw.Draw(img)
    # по символу: разные файлы шрифтов для кириллицы и латиницы
    widths = []
    for ch in text:
        f = font_for(ch, px, wght)
        widths.append(f.getlength(ch))
    total = sum(widths)
    x = ox + x_mm * PPM
    if anchor[0] == "r":
        x -= total
    elif anchor[0] == "m":
        x -= total / 2
    y = oy + y_mm * PPM
    for ch, w in zip(text, widths):
        d.text((x, y), ch, fill=255, font=font_for(ch, px, wght), anchor="ls")
        x += w


def key_cell_mm(k):
    kd = kbp.keycap_dims(k["w"], k["profile"])
    return kd["wt"] * 1000, kd["dt"] * 1000


def draw_key(R, G, k, ox, oy):
    """ox, oy — пиксель левого верхнего угла ВЕРХА колпачка (внутри поля ячейки)."""
    wt, dt = key_cell_mm(k)
    ins_x, ins_top, ins_bot = 1.7, 1.55, 1.65
    role, l1, l2, l3 = k["role"], k["l1"], k["l2"], k["l3"]
    if k["id"] == "yo" or k["id"] == "space":
        return
    if role == "mod":
        if l1 in "←→↑↓":
            draw_text(R, l1, wt / 2, dt / 2 + 1.5, 3.0, 500, "ms", ox, oy)
        else:
            draw_text(R, l1, ins_x, ins_top + 2.1, 2.1, 480, "ls", ox, oy)     # строчные: высота «x» ≈ 2,1 × 0,73
        return
    if k["row"] == 0 or k["id"] in ("bsl",):
        # ряд цифр: цифра снизу слева; символ Shift сверху слева (общий — основной цвет, EN — второй); RU-символ сверху справа
        draw_text(R, l1, ins_x, dt - ins_bot, 3.1, 520, "ls", ox, oy)
        if l3:
            draw_text(G, l2, ins_x, ins_top + 2.4, 2.4, 480, "ls", ox, oy)
            draw_text(R, l3, wt - ins_x, ins_top + 2.4, 2.4, 480, "rs", ox, oy)
        else:
            draw_text(R, l2, ins_x, ins_top + 2.4, 2.4, 480, "ls", ox, oy)
        return
    if k["id"] == "slash":
        draw_text(R, f"{l1} {l3}", ins_x, ins_top + 3.3, 3.3, 520, "ls", ox, oy)
        draw_text(G, l2, wt - ins_x, dt - ins_bot, 2.5, 470, "rs", ox, oy)
        return
    # буквы: кириллица — основная сверху слева, латиница/символ — вторая снизу справа
    draw_text(R, l1, ins_x, ins_top + 3.4, 3.4, 540, "ls", ox, oy)
    draw_text(G, l2, wt - ins_x, dt - ins_bot, 2.5, 470, "rs", ox, oy)


def main():
    global PPM
    keys = kbp.keys()
    m = MARGIN_MM
    cells = []
    for k in keys:
        wt, dt = key_cell_mm(k)
        cells.append((k, round((wt + 2 * m) * PPM), round((dt + 2 * m) * PPM)))
    W = 6144 if PPM >= 20 else 2048
    x = y = row_h = 0
    place = {}
    for k, cw, ch in sorted(cells, key=lambda c: -c[1]):      # широкие первыми, полками
        if x + cw > W:
            x, y = 0, y + row_h
            row_h = 0
        place[k["id"]] = (x, y, cw, ch)
        x += cw
        row_h = max(row_h, ch)
    H = y + row_h
    H = ((H + 255) // 256) * 256
    R = Image.new("L", (W, H), 0)
    G = Image.new("L", (W, H), 0)
    meta = {"ppm": PPM, "margin_mm": m, "size": [W, H], "keys": {}}
    for k in keys:
        x0, y0, cw, ch = place[k["id"]]
        wt, dt = key_cell_mm(k)
        ox, oy = x0 + m * PPM, y0 + m * PPM
        draw_key(R, G, k, ox, oy)
        # UV верха 0..1 → атлас (Blender: v снизу): off = (ox/W, (H − oy − dt·ppm)/H), scl = (wt·ppm/W, dt·ppm/H)
        meta["keys"][k["id"]] = {"px": [x0, y0, cw, ch], "off": [ox / W, (H - oy - dt * PPM) / H],
                                 "scl": [wt * PPM / W, dt * PPM / H]}
    B = Image.new("L", (W, H), 0)
    atlas = Image.merge("RGB", (R, G, B))
    atlas.save(os.path.join(OUT, "atlas_legends.png"), optimize=True)
    json.dump(meta, open(os.path.join(OUT, "atlas_legends.json"), "w"), ensure_ascii=False, indent=1)

    # Ё — своя текстура крупнее (герой макро): верх и лицевая грань («esc» = Fn + Ё)
    ppm_yo = PPM * 3
    k = next(k for k in keys if k["id"] == "yo")
    wt, dt = key_cell_mm(k)
    yw, yh = round((wt + 2 * m) * ppm_yo), round((dt + 2 * m) * ppm_yo)
    Y = Image.new("L", (yw, yh), 0)
    keep = PPM
    PPM = ppm_yo
    _cache.clear()
    draw_text(Y, "Ё", wt / 2, dt / 2 + 2.9, 6.2, 640, "ms", m * ppm_yo, m * ppm_yo)
    Y2 = Image.new("L", Y.size, 0)                                  # «esc» — вторая надпись (Fn + Ё): 60 % маски
    draw_text(Y2, "esc", wt - 1.7, dt - 1.65, 1.75, 520, "rs", m * ppm_yo, m * ppm_yo)
    Y = Image.fromarray(__import__("numpy").maximum(__import__("numpy").asarray(Y), (__import__("numpy").asarray(Y2) * 0.6).astype("uint8")))
    Y.save(os.path.join(OUT, "yo_top.png"))
    kd = kbp.keycap_dims(1, "R1")
    sw_mm, sh_mm = kd["wb"] * 1000, 10.0                         # лицевая грань: ширина низа × 10 мм высоты (проекция XZ)
    S = Image.new("L", (round(sw_mm * ppm_yo), round(sh_mm * ppm_yo)), 0)
    draw_text(S, "esc", sw_mm / 2, sh_mm - 3.3, 1.35, 520, "ms", 0, 0)
    S.save(os.path.join(OUT, "yo_side.png"))
    # марка на латунной полосе сзади: «Ё» и «65» — маска для рельефа гравировки
    Mk = Image.new("L", (round(60 * ppm_yo), round(7 * ppm_yo)), 0)
    draw_text(Mk, "Ё · 65", 30, 4.9, 3.2, 560, "ms", 0, 0)
    Mk.save(os.path.join(OUT, "brass_mark.png"))
    Pm = Image.new("L", (round(80 * ppm_yo), round(26 * ppm_yo)), 0)          # гравировка на плите-грузике
    draw_text(Pm, "Ё", 40, 15.5, 11.0, 640, "ms", 0, 0)
    draw_text(Pm, "шестьдесят пять · 408 г · латунь", 40, 22.5, 2.3, 520, "ms", 0, 0)
    Pm.save(os.path.join(OUT, "brass_plate_mark.png"))
    PPM = keep
    _cache.clear()

    # превью: надписи «Снега» на цвете колпачков
    cw_ = kbp.COLORWAYS["snow"]
    def hexrgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    prev = Image.new("RGB", (W, H), hexrgb(cw_["alpha"]))
    prev.paste(Image.new("RGB", (W, H), hexrgb(cw_["legend1"])), mask=R)
    prev.paste(Image.new("RGB", (W, H), hexrgb(cw_["legend2"])), mask=G)
    d = ImageDraw.Draw(prev)
    for kid, (x0, y0, cw, ch) in place.items():
        d.rectangle([x0, y0, x0 + cw - 1, y0 + ch - 1], outline=(200, 90, 60))
    prev.resize((W // 4, H // 4), Image.LANCZOS).save(os.path.join(OUT, "atlas_preview.png"))
    print(json.dumps({"atlas": [W, H], "ppm": PPM, "cap_ratio": round(CAP, 3), "yo": [yw, yh], "keys": len(keys)}))


if __name__ == "__main__":
    main()
