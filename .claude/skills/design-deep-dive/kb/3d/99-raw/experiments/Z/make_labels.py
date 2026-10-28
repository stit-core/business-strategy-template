#!/usr/bin/env python3
"""Картинки-маски маркировки «Звена»: белый текст на прозрачном (печать поверх лака — цвет задаёт материал, гравировка крышек)
и двухцветная печать J1 «знак страницы + ЗВЕНО» (`zveno_mark`: кольца #ff5a1f, буквы #2b2e33, цвет из картинки — материал
kind="color"). Шрифт OFL Liberation Sans Narrow Bold (кириллица). Пишет tex/lbl_*.png и tex/labels.json (пропорции наклеек).
Запускать ДО zbuild.py: build берёт размеры наклеек из labels.json."""
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf"
out = {}
def label(name, text, px, track=0.08, pad=0.18, font=FONT, lines=None):
    f = ImageFont.truetype(font, px)
    rows = lines or [(text, f, track)]
    ws, hs = [], []
    for t, ff, tr in rows:
        w = sum(ff.getlength(ch) for ch in t) + tr * ff.size * (len(t) - 1)
        asc, desc = ff.getmetrics(); ws.append(w); hs.append(asc + desc)
    W = int(max(ws) * (1 + pad)); H = int(sum(hs) * (1 + pad * 1.6))
    im = Image.new("RGBA", (W, H), (255, 255, 255, 0)); d = ImageDraw.Draw(im)
    y = (H - sum(hs)) / 2
    for (t, ff, tr), w, h in zip(rows, ws, hs):
        x = (W - w) / 2
        for ch in t:
            d.text((x, y), ch, font=ff, fill=(255, 255, 255, 255)); x += ff.getlength(ch) + tr * ff.size
        y += h
    bb = im.getbbox()
    p = os.path.join(HERE, "tex", f"lbl_{name}.png"); im.save(p)
    out[name] = {"path": p, "w": W, "h": H, "aspect": W / H, "ink_bbox": bb}
label("zveno", "ЗВЕНО", 360, track=0.14)
for j in ("J1", "J2", "J3"):
    label(j.lower(), j, 300, track=0.04)
fs = ImageFont.truetype(FONT_R, 120)
label("spec", "", 120, lines=[("ЗВЕНО · МОДУЛЬ СУСТАВА · 48 V DC", fs, 0.06)])


def label_mark(name="zveno_mark", text="ЗВЕНО", px=360, track=0.14):
    """Знак страницы (logo__mark: две окружности r 5 в поле 24, обводка 2,4 — в акценте) перед словом «ЗВЕНО»."""
    f = ImageFont.truetype(FONT, px)
    INK = (0x2b, 0x2e, 0x33, 255); ACC = (0xff, 0x5a, 0x1f, 255)
    w_text = sum(f.getlength(ch) for ch in text) + track * px * (len(text) - 1)
    asc, desc = f.getmetrics(); by = f.getbbox("Н"); cap_h = by[3] - by[1]
    mark_w = cap_h * 2.0; gap = cap_h * 0.5
    W = int((mark_w + gap + w_text) * 1.18); H = int((asc + desc) * 1.29)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0 = (W - (mark_w + gap + w_text)) / 2; ytop = (H - (asc + desc)) / 2; cy = ytop + (by[1] + by[3]) / 2
    r = cap_h * 0.5; lw = max(3, int(cap_h * 0.24))
    for cx in (x0 + r, x0 + r + cap_h):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ACC, width=lw)
    x = x0 + mark_w + gap
    for ch in text:
        d.text((x, ytop), ch, font=f, fill=INK); x += f.getlength(ch) + track * px
    p = os.path.join(HERE, "tex", f"lbl_{name}.png"); im.save(p)
    out[name] = {"path": p, "w": W, "h": H, "aspect": W / H, "ink_bbox": im.getbbox(), "colored": True}


label_mark()
json.dump(out, open(os.path.join(HERE, "tex", "labels.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v["w"], v["h"], round(v["aspect"], 3)) for k, v in out.items()}, ensure_ascii=False))
