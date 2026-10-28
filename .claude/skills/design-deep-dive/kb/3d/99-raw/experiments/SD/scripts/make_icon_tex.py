"""make_icon_tex.py — текстуры экранов серии приборов (системный Python + Pillow; в Blender Pillow нет)."""
import sys
import numpy as np

def heatmap_png(path, w=240, h=180):
    """Тепловая карта окна (палитра «железо»): холодный откос, тёплое продувание по шву — одно цветное пятно."""
    from PIL import Image
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    t = 0.30 + 0.25 * np.exp(-((xx - 0.5) ** 2 / 0.08 + (yy - 0.55) ** 2 / 0.12))
    t += 0.45 * np.exp(-((xx - 0.22) ** 2 / 0.004 + (yy - 0.5) ** 2 / 0.09))      # полоса по шву окна
    t = np.clip(t, 0, 1)
    stops = [(0.0, (10, 8, 40)), (0.3, (80, 10, 110)), (0.55, (190, 30, 60)), (0.75, (240, 110, 20)), (0.9, (250, 200, 60)),
             (1.0, (255, 250, 210))]
    rgb = np.zeros((h, w, 3))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (t >= a) & (t <= b)
        k = ((t - a) / (b - a))[..., None]
        rgb = np.where(m[..., None], np.array(ca) * (1 - k) + np.array(cb) * k, rgb)
    im = Image.fromarray(rgb.astype(np.uint8), "RGB")
    im.save(path)
    return path


def lcd_png(path, text="18,4", w=200, h=90):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (w, h), (46, 50, 46))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 58)
    d.text((w - 12, h // 2 + 2), text, fill=(214, 222, 206), font=f, anchor="rm")
    d.text((10, 10), "%", fill=(170, 180, 160), font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18))
    im.save(path)
    return path


def tape_png(path, w=600, h=60):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (238, 236, 230))
    d = ImageDraw.Draw(im)
    for i in range(0, w, 6):
        L = h * (0.55 if i % 60 == 0 else 0.35 if i % 30 == 0 else 0.2)
        d.line([(i, 0), (i, L)], fill=(28, 29, 32), width=2 if i % 60 == 0 else 1)
    im.save(path)
    return path



if __name__ == "__main__":
    out = sys.argv[1]
    # SD2: полотно рулетки — tape_tex.png (tape.png — имя рендера рулетки: в v2 текстуру затирал рендер, полотно выходило чёрным)
    print(heatmap_png(f"{out}/heatmap.png"), lcd_png(f"{out}/lcd.png"), tape_png(f"{out}/tape_tex.png"))
