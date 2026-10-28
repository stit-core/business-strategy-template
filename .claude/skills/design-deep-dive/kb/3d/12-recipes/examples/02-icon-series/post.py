# Сгенерировано run_recipes.py из 12-recipes/02-icon-series.md — блоки «run: system» в напечатанном виде.

# ---- блок со строки 164
# run: system — Python 3 + Pillow — [проверено] PNG 512² → AVIF/WebP 1×/2× + страница-сетка
import os
from PIL import Image
EX = os.path.dirname(os.path.abspath(__file__))  # перенос: папка примера


def encode_web(png_path, out_dir, css_px, avif_q=60, webp_q=80):
    """PNG RGBA (рендер 2× CSS) → AVIF и WebP для 2× и 1×; возвращает {имя: КБ} и HTML <picture> (D2 06/04 §1.3)."""
    im = Image.open(png_path).convert("RGBA"); base = os.path.splitext(os.path.basename(png_path))[0]
    os.makedirs(out_dir, exist_ok=True); sizes = {}
    for scale in (2, 1):
        px = css_px * scale
        frame = im if im.width == px else im.resize((px, round(im.height * px / im.width)), Image.LANCZOS)
        for ext, kw in (("avif", {"quality": avif_q}), ("webp", {"quality": webp_q, "method": 6})):
            p = os.path.join(out_dir, f"{base}@{scale}x.{ext}"); frame.save(p, ext.upper(), **kw)
            sizes[os.path.basename(p)] = round(os.path.getsize(p) / 1024, 1)
    html = (f'<picture><source type="image/avif" srcset="{base}@1x.avif 1x, {base}@2x.avif 2x">'
            f'<source type="image/webp" srcset="{base}@1x.webp 1x, {base}@2x.webp 2x">'
            f'<img src="{base}@1x.webp" width="{css_px}" height="{css_px}" alt="" loading="lazy" decoding="async"></picture>')
    return sizes, html


cards, total = [], {}
for name, label in (("chat", "Сообщения"), ("bell", "Уведомления"), ("folder", "Файлы")):
    sizes, pic = encode_web(f"{EX}/icon-{name}-3d.png", f"{EX}/web", css_px=256)
    total.update(sizes)
    pic = pic.replace(f"icon-{name}-3d@", f"web/icon-{name}-3d@")          # страница лежит на уровень выше web/
    cards.append(f'<li><div class="ic">{pic}</div><h3>{label}</h3></li>')
html = ("<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Иконки — рецепт 02</title><style>body{margin:0;font:18px/1.5 system-ui;background:#F4F4F6;color:#16181d}"
        "ul{list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px;padding:6vh 6vw;margin:0}"
        "li{background:#fff;border-radius:24px;padding:24px;text-align:center}.ic img{width:min(100%,256px);height:auto}"
        "h3{margin:.4em 0 0}</style></head><body><ul>" + "".join(cards) + "</ul></body></html>")
open(f"{EX}/index.html", "w", encoding="utf-8").write(html)
print(total)
