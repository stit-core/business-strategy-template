#!/usr/bin/env python3
"""sheet.py — лист сравнения кадров с подписями, одинаковый вид для всех вариантов сцены.

    python3 sheet.py --out лист.jpg [--cols 2] [--tile 960] [--title "Заголовок листа"] кадр1.png:подпись1 кадр2.png:подпись2 …

Кадры приводятся к ширине --tile (высота по пропорции первого), прозрачное кладётся на тёмно-серый; подпись — полосой над
кадром. JPEG q90. Для судьи — не больше 2 кадров на лист (правило 11/02 §4): --cols 2 и ровно два кадра.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
         "/usr/share/fonts/opentype/noto/NotoSans-Regular.otf"]


def font(size):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    a = sys.argv[1:]
    if not a or "--out" not in a:
        print(__doc__)
        return 2

    def opt(n, d=None):
        if n in a:
            i = a.index(n)
            v = a[i + 1]
            del a[i:i + 2]
            return v
        return d

    out = opt("--out")
    cols = int(opt("--cols", 2))
    tile = int(opt("--tile", 960))
    title = opt("--title")
    items = []
    for s in a:
        p, _, lab = s.partition(":")
        items.append((p, lab or p.rsplit("/", 1)[-1]))
    ims = []
    for p, lab in items:
        im = Image.open(p).convert("RGBA")
        bg = Image.new("RGBA", im.size, (34, 36, 40, 255))
        bg.alpha_composite(im)
        ims.append((bg.convert("RGB"), lab))
    r = ims[0][0].height / ims[0][0].width
    th = int(tile * r)
    lab_h = 40
    rows = (len(ims) + cols - 1) // cols
    top = 56 if title else 0
    sheet = Image.new("RGB", (cols * tile + (cols + 1) * 12, top + rows * (th + lab_h) + (rows + 1) * 12), (18, 19, 22))
    d = ImageDraw.Draw(sheet)
    f = font(22)
    if title:
        d.text((14, 14), title, fill=(236, 235, 230), font=font(26))
    for i, (im, lab) in enumerate(ims):
        x = 12 + (i % cols) * (tile + 12)
        y = top + 12 + (i // cols) * (th + lab_h + 12)
        d.rectangle([x, y, x + tile, y + lab_h], fill=(40, 42, 48))
        d.text((x + 10, y + 8), lab, fill=(236, 235, 230), font=f)
        sheet.paste(im.resize((tile, th), Image.LANCZOS), (x, y + lab_h))
    sheet.save(out, quality=90)
    print(out, sheet.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
