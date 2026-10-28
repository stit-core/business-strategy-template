#!/usr/bin/env python3
"""VD/01-build — растр бумажной этикетки VELMORA (Pillow): цвет (sRGB) + маска краски (Non-Color, для шероховатости и
тиснения). Физический размер этикетки 54 × 16,4 мм (дуга × высота) → 4096 × 1244 px (≈ 76 px/мм): буквы не мельче 4 px
даже в кадре 2560 px. Шрифт — Noto Serif Display Regular из галереи ai-media (OFL-1.1, копия с лицензией в ../fonts/).

    python3 make_label.py [--out tex/]"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "noto-serif-display-400.woff2")
W_MM, H_MM = 54.0, 16.4
W, H = 4096, round(4096 * H_MM / W_MM)
PX_MM = W / W_MM
PAPER = (236, 231, 222)       # #ECE7DE — тёплая бумага (sRGB)
INK = (36, 34, 30)            # #24221E — почти чёрная краска
INK2 = (104, 99, 91)          # #68635B — вторая строка, тише
LINES = [  # текст, высота прописной (мм), разрядка (доля кегля), центр строки от верха (доля высоты), цвет
    ("VELMORA", 4.3, 0.20, 0.445, INK),
    ("LAIT DE CORPS  ·  100 ML", 1.05, 0.34, 0.775, INK2),
]


def cap_font(cap_mm):
    """Кегль, при котором высота прописной «H» = cap_mm."""
    probe = ImageFont.truetype(FONT, 1000)
    b = probe.getbbox("H")
    cap_px_per_pt = (b[3] - b[1]) / 1000
    return ImageFont.truetype(FONT, round(cap_mm * PX_MM / cap_px_per_pt))


def draw_spaced(d, text, font, tracking, cy, fill):
    """Строка с разрядкой: ширина = Σ(ширина буквы) + tracking·кегль·(n−1); по центру W, прописные по центру cy."""
    size = font.size
    widths = [font.getlength(ch) for ch in text]
    total = sum(widths) + tracking * size * (len(text) - 1)
    x = (W - total) / 2
    hb = font.getbbox("H")
    y = cy - (hb[1] + hb[3]) / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += w + tracking * size
    return total


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(HERE, "tex")
    os.makedirs(out, exist_ok=True)
    col = Image.new("RGB", (W, H), PAPER)
    ink = Image.new("L", (W, H), 0)
    dc, di = ImageDraw.Draw(col), ImageDraw.Draw(ink)
    info = []
    for text, cap_mm, tr, cy, fill in LINES:
        f = cap_font(cap_mm)
        wpx = draw_spaced(dc, text, f, tr, cy * H, fill)
        draw_spaced(di, text, f, tr, cy * H, 255)
        info.append({"text": text, "cap_mm": cap_mm, "font_px": f.size, "width_mm": round(wpx / PX_MM, 2)})
    # тонкая «печатная» мягкость края краски (≈ 0,02 мм) — без лесенки при сильном сжатии
    ink = ink.filter(ImageFilter.GaussianBlur(1.2))
    col.save(os.path.join(out, "label_color.png"))
    ink.save(os.path.join(out, "label_ink.png"))
    meta = {"size_px": [W, H], "size_mm": [W_MM, H_MM], "px_per_mm": round(PX_MM, 2), "font": os.path.basename(FONT),
            "lines": info}
    json.dump(meta, open(os.path.join(out, "label.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
