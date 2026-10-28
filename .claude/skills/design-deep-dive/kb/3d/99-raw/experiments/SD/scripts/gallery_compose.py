"""gallery_compose.py (SD4) — картинки галереи приёмов «Сдано»: 1200 × 750, WebP q80 → 15-showcase/sdano/gallery/<id>.webp.
Источники: кадры судьи (judge/), снимки DPR 2 (shots/sd4_gallery, gallery_shots.py), отладочные виды тени (shots/sd3_dbg5,
sd3_dbg10p3), ассеты страниц (иконки 256, клип штампа — кадры вынуты ffmpeg в SCR/stampf).
    python3 gallery_compose.py SCR_STAMPF_DIR"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

R = "/home/mm/Документы/app-design/blender-research"
X = f"{R}/99-raw/experiments/SD"
S = f"{R}/15-showcase/sdano"
G = f"{S}/gallery"
SF = sys.argv[1]
W, H = 1200, 750
os.makedirs(G, exist_ok=True)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
FS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19)


def label(im, text, xy=(14, 12), font=F):
    d = ImageDraw.Draw(im)
    x, y = xy
    l, t, r, b = d.textbbox((x, y), text, font=font)
    d.rectangle((l - 8, t - 6, r + 8, b + 6), fill=(20, 20, 20))
    d.text((x, y), text, font=font, fill=(255, 255, 255))


def cover(im, w, h, cx=0.5, cy=0.5):
    """Заполнить w × h с обрезкой (центр обрезки — доли cx, cy)."""
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = min(max(0, round(cx * im.width - w / 2)), im.width - w)
    y = min(max(0, round(cy * im.height - h / 2)), im.height - h)
    return im.crop((x, y, x + w, y + h))


def save(im, gid):
    f = f"{G}/{gid}.webp"
    im.convert("RGB").save(f, "WEBP", quality=80, method=6)
    print(gid, im.size, round(os.path.getsize(f) / 1024, 1), "КБ")


def op(p):
    return Image.open(p).convert("RGB")


# 1. фонарик по проходам — луч на трещине (DPR 2) + луч на окне
if os.path.exists(f"{X}/shots/sd4_gallery/c_beam2x.png"):
    a = op(f"{X}/shots/sd4_gallery/c_beam2x.png")
    b = op(f"{X}/shots/sd4_gallery/c_window2x.png")
    im = Image.new("RGB", (W, H), (255, 255, 255))
    im.paste(cover(a, 790, H, 0.42, 0.62), (0, 0))
    im.paste(cover(b, 400, H, 0.30, 0.45), (800, 0))
    label(im, "C · луч на трещине: полумрак, тени стен и фигуры, «найдено»")
    label(im, "луч на окне (шов 0,87 м)", (814, 12), FS)
    save(im, "fonarik-passes")

# 2. тени фонаря: марш по экранной высоте (SD2, mip-конус) → карта высот сверху (SD3); итог кадра, луч на трещине, крупно
a = op(f"{X}/shots/sd3_dbg5/dbg0.png")          # сборка SD2 (снята SD3 в 00:10 до правок)
b = op(f"{X}/shots/sd4_dbg_crack/dbg0.png")     # текущая сборка (SD3), та же точка луча
box = (80, 200, 430, 643)
im = Image.new("RGB", (W, H), (255, 255, 255))
im.paste(a.crop(box).resize((595, H), Image.LANCZOS), (0, 0))
im.paste(b.crop(box).resize((595, H), Image.LANCZOS), (605, 0))
ImageDraw.Draw(im).rectangle((595, 0, 604, H), fill=(20, 20, 20))
label(im, "SD2: марш по экранной высоте — «кольчуга»", (14, 700), FS)
label(im, "SD3: карта высот сверху из Blender", (619, 700), FS)
save(im, "topdown-shadows")

# 3. телефон: однократный проход фонаря после прокрутки
a = op(f"{S}/judge/c-hybrid__first-screen-mob.png")
b = op(f"{S}/judge/c-hybrid__tour-mob.png")
im = Image.new("RGB", (W, H), (255, 255, 255))
im.paste(cover(a.crop((0, 150, 1170, 1612)), 595, H), (0, 0))
im.paste(cover(b.crop((0, 150, 1170, 1612)), 595, H), (605, 0))
ImageDraw.Draw(im).rectangle((595, 0, 604, H), fill=(20, 20, 20))
label(im, "телефон: план в кадре — свет «дня»", (14, 12), FS)
label(im, "через 0,35 с — один проход ≈ 2,2 с", (619, 12), FS)
save(im, "phone-tour")

# 4. изометрия с сюжетом (B): инженер, лазерная линия, мел, булавки + номера HTML
if os.path.exists(f"{X}/shots/sd4_gallery/b_stage2x.png"):
    a = op(f"{X}/shots/sd4_gallery/b_stage2x.png")
    im = cover(a, W, H, 0.40, 0.58)
    label(im, "B · разрез 1,1 м: инженер с планшетом, лазерная линия, трещина в круге мела; номера — HTML")
    save(im, "iso-story")

# 5. серия приборов одним паспортом (B)
names = [("laser", "лазерный уровень"), ("thermal", "тепловизор"), ("moisture", "влагомер"), ("tape", "рулетка"),
         ("flashlight", "фонарь")]
im = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(im)
for i, (n, t) in enumerate(names):
    ic = op(f"{S}/b-blender/assets/icon-{n}-256.webp")
    x = 20 + i * 236
    im.paste(ic.resize((228, 228), Image.LANCZOS), (x, 200))
    l, tt, r, b_ = d.textbbox((0, 0), t, font=FS)
    d.text((x + 114 - (r - l) / 2, 450), t, font=FS, fill=(20, 20, 20))
label(im, "B · 5 приборов одним паспортом: изометрия и солнце квартиры, высота 56 %, тень запечена на #fff")
label(im, "AVIF 128/256 — 0,8–1,9 КБ; край кадра ΔE ≤ 0,35 к #fff", (14, 700), FS)
save(im, "icons-passport")

# 6. штамп-клип «СДАНО» (B): кадры клипа + конец на акте
im = Image.new("RGB", (W, H), (255, 255, 255))
ts = ["0.00", "0.30", "0.75", "0.95", "1.20", "end"]
for i, t in enumerate(ts):
    fr = op(f"{SF}/s_{t}.png").resize((400, 196), Image.LANCZOS)
    im.paste(fr, ((i % 3) * 400, (i // 3) * 196))
act = op(f"{S}/judge/b-blender__act-stamp.png")
im.paste(act.crop((600, 490, 1360, 717)).resize((W, H - 392), Image.LANCZOS), (0, 392))
ImageDraw.Draw(im).rectangle((0, 390, W, 393), fill=(20, 20, 20))
label(im, "B · клип Blender 1,58 с (38 кадров @24): покой → перенос → удар → оттиск; белый клип × multiply", (14, 12), FS)
save(im, "stamp-clip")
