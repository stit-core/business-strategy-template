#!/usr/bin/env python3
"""Постер из того же GLB и той же пары тонмаппинга: открывает index.html?poster (десктопная модель, DPR 1, без анимации),
снимает блок #hero 1024×1024 с прозрачным фоном и кодирует AVIF (q60) и WebP (q85) через Pillow.
    python3 make_poster.py            # требует dist/ (esbuild) и Playwright; пишет assets/poster.avif, assets/poster.webp
"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../../../scripts/3d"))  # перенос: serve_br.py — scripts/3d
from serve_br import start  # noqa: E402
from PIL import Image
from playwright.sync_api import sync_playwright

httpd = start(HERE, 0)
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"])
        p = b.new_page(viewport={"width": 1100, "height": 1400}, device_scale_factor=1)
        p.goto(f"http://127.0.0.1:{httpd.server_address[1]}/index.html?poster")
        p.add_style_tag(content="html,body{background:transparent!important} .hero{width:1024px!important} "
                                ".hero img{visibility:hidden} .hero canvas{opacity:1!important}")   # постер с альфой: без шва на любом фоне
        p.wait_for_function("window.__ready === true", timeout=120000)
        p.evaluate("window.dispatchEvent(new Event('resize'))")
        p.wait_for_timeout(500)
        png = p.locator("#hero canvas").screenshot(omit_background=True)
        b.close()
finally:
    httpd.shutdown()
im = Image.open(io.BytesIO(png)).convert("RGBA")
im.save(os.path.join(HERE, "assets", "poster.avif"), quality=60)
im.save(os.path.join(HERE, "assets", "poster.webp"), quality=85, method=6)
for f in ("poster.avif", "poster.webp"):
    print(f, im.size, os.path.getsize(os.path.join(HERE, "assets", f)), "байт")
