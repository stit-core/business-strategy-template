"""stamp_tex.py — текстуры штампа «СДАНО» (системный Python + Pillow; в Blender Pillow нет).
  stamp_label.png — этикетка-индекс на передней полосе верхней грани колодки (70 × 14 мм, 12 px/мм): бумага #efede6, двойная рамка и «СДАНО»
                    шрифтом страницы (Golos Text 800, OFL — копия из creative-research/_shared/fonts, лицензия рядом);
  stamp_ink.png   — оттиск (90 × 40 мм, 12 px/мм, RGBA): двойная рамка + «СДАНО», чернила #141414 с неровной плотностью
                    (зерно бумаги, лёгкие «недоливы» у края) — кладётся в дообработке по плоскости листа (stamp_comp.py).
    python3 stamp_tex.py OUT_DIR"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/home/mm/Документы/app-design/creative-research/10-recipes/examples/_shared/fonts/golos-text/golos-text-cyrillic-wght-normal.woff2"
PPM = 12            # px на мм


def golos(size_px, weight=800):
    f = ImageFont.truetype(FONT, size_px)
    try:
        f.set_variation_by_axes([weight])
    except OSError:
        pass
    return f


def frame_and_text(w_mm, h_mm, stroke_out, gap, stroke_in, radius, text_h_mm, tracking=0.10, pad_mm=0.0):
    """Маска (L, 0..255): двойная рамка со скруглением + текст по центру, разрядка tracking (em)."""
    W, H = round(w_mm * PPM), round(h_mm * PPM)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    p = pad_mm * PPM
    so, g, si, r = stroke_out * PPM, gap * PPM, stroke_in * PPM, radius * PPM
    d.rounded_rectangle([p, p, W - 1 - p, H - 1 - p], radius=r, outline=255, width=max(1, round(so)))
    q = p + so + g
    d.rounded_rectangle([q, q, W - 1 - q, H - 1 - q], radius=max(1, r - so - g), outline=255, width=max(1, round(si)))
    # текст: кегль по высоте прописной, но не шире внутренней рамки минус поля 3,5 мм
    letters = list("СДАНО")
    max_w = W - 2 * (q + si + 3.5 * PPM)

    def measure(sz):
        f_ = golos(sz)
        ws = [f_.getlength(ch) for ch in letters]
        return f_, ws, sum(ws) + tracking * sz * (len(letters) - 1)
    size = round(text_h_mm * PPM / 0.72)
    f, widths, total = measure(size)
    if total > max_w:
        size = int(size * max_w / total)
        f, widths, total = measure(size)
    tr = tracking * size
    x = (W - total) / 2
    bb = f.getbbox("СДАНО")
    cap_h = bb[3] - bb[1]
    y = (H - cap_h) / 2 - bb[1]
    for ch, cw in zip(letters, widths):
        d.text((x, y), ch, fill=255, font=f)
        x += cw + tr
    return m


def label_png(path):
    """Этикетка — передняя полоса верхней грани колодки 70 × 14 мм (перед шейкой: сверху-спереди её не заслоняет ручка)."""
    w, h = 70.0, 14.0
    m = frame_and_text(w, h, 0.5, 0.6, 0.3, 1.5, 7.0, tracking=0.12, pad_mm=1.2)
    base = np.full((m.height, m.width, 3), (239, 237, 230), np.float64)
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float64)[..., None] / 255.0
    ink = np.array([24, 24, 26], np.float64)
    out = base * (1 - a * 0.92) + ink * a * 0.92
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(path)
    return path


def ink_png(path, seed=7):
    """Оттиск: маска → лёгкое размытие края (впитывание) → плотность с зерном и «недоливом» → RGBA чернил #141414."""
    w, h = 90.0, 40.0
    m = frame_and_text(w, h, 1.6, 1.0, 0.6, 2.5, 17.0, tracking=0.10, pad_mm=0.0)
    rng = np.random.default_rng(seed)
    H, W = m.height, m.width
    base = np.asarray(m.filter(ImageFilter.GaussianBlur(0.9))).astype(np.float64) / 255.0
    # края чуть «шершавые»: порог по размытому полю + мелкий шум
    fine = rng.random((H, W))
    fine = np.asarray(Image.fromarray((fine * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float64) / 255.0
    edge = np.clip((base - 0.5 + (fine - 0.5) * 0.35) * 6.0 + 0.5, 0, 1)
    # плотность: крупные пятна (неравномерный нажим) + зерно бумаги
    coarse = rng.random((H // 24 + 2, W // 24 + 2))
    coarse = np.asarray(Image.fromarray((coarse * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float64) / 255.0
    grain = rng.random((H, W))
    grain = np.asarray(Image.fromarray((grain * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))).astype(np.float64) / 255.0
    # нажим слабее к правому нижнему углу (штамп покачнули) — «недолив» ≤ 14 %
    yy, xx = np.mgrid[0:H, 0:W]
    press = 1.0 - 0.14 * np.clip((xx / W - 0.55) * 1.6, 0, 1) * np.clip((yy / H - 0.35) * 1.8, 0, 1)
    dens = 0.87 + 0.06 * coarse + 0.05 * grain
    alpha = np.clip(edge * dens * press, 0, 1)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = (20, 20, 20)
    rgba[..., 3] = (alpha * 255 + 0.5).astype(np.uint8)
    Image.fromarray(rgba).save(path)
    return path


if __name__ == "__main__":
    out = os.path.abspath(sys.argv[1])
    os.makedirs(out, exist_ok=True)
    print(label_png(f"{out}/stamp_label.png"), ink_png(f"{out}/stamp_ink.png"))
