#!/usr/bin/env python3
"""capture.py — кадры варианта A со СВОЕЙ страницы (три кода, без Blender): постер первого экрана H2v2 (десктоп/портрет) и
запасные кадры (reduce и «до загрузки 3D»): набор, кадр 0 оборота в трёх расцветках, 4 станции разборки.

    python3 capture.py [hero-desk hero-mob type turn-snow turn-graphite turn-linen x-0 x-1 x-2 x-3]
→ out/*.png и web/assets/img/… (те же имена, что у кадров B: build_pages.py раскладывает их в a-code/).
"""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time

from PIL import Image
from playwright.sync_api import sync_playwright

R = "/home/mm/Документы/app-design/blender-research"
HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = f"{R}/15-showcase/keyboard/" + os.environ.get("KB_CAP_PAGE", "a-code")
SCR = "/tmp/claude-1000/-home-mm-----------app-design/2e530199-ecfd-48ab-994b-f3dd1c91c010/scratchpad"
OUT = os.path.join(HERE, os.environ.get("KB_CAP_OUT", "out"))
WEB = os.path.join(HERE, os.environ.get("KB_CAP_WEB", "web"), "assets", "img")
GPU = ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"]
SIZES = {"hero-desk": (1920, 1200), "hero-mob": (780, 1688), "type": (1600, 900), "turn-snow": (1280, 800),
         "turn-graphite": (1280, 800), "turn-linen": (1280, 800), "x-0": (1600, 1000), "x-1": (1600, 1000),
         "x-2": (1600, 1000), "x-3": (1600, 1000)}
WHAT = sys.argv[1:] or list(SIZES)
os.makedirs(OUT, exist_ok=True)
PORT = int(os.environ.get("KB_CAP_PORT", "8783"))


def save(im, rel, q=62, webp=False):
    p = os.path.join(WEB, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p + ".avif", quality=q, speed=6)
    if webp:
        im.save(p + ".webp", quality=84, method=6)


copy = os.path.join(SCR, "kb_serve_cap_a")
if os.path.isdir(copy):
    shutil.rmtree(copy)
shutil.copytree(PAGE, copy)
srv = subprocess.Popen([sys.executable, f"{R}/99-raw/experiments/F1/02-hero-variants/serve_br.py", copy, str(PORT)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(240):
    try:
        socket.create_connection(("127.0.0.1", PORT), timeout=0.2).close()
        break
    except OSError:
        time.sleep(0.25)
log = {"load": os.getloadavg(), "shots": {}}
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=GPU)
        for w in WHAT:
            W, H = SIZES[w]
            ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
            t0 = time.time()
            pg.goto(f"http://127.0.0.1:{PORT}/index.html?capture={w}", wait_until="load")
            pg.wait_for_function("window.__capReady === true", timeout=60000)
            path = os.path.join(OUT, f"{w}.png")
            pg.screenshot(path=path)
            log["shots"][w] = {"sec": round(time.time() - t0, 2), "errors": errs, "kb": pg.evaluate("window.__kb || null")}
            ctx.close()
        b.close()
finally:
    srv.send_signal(signal.SIGTERM)
    srv.wait(timeout=5)
for w in WHAT:
    im = Image.open(os.path.join(OUT, f"{w}.png")).convert("RGB")
    if w.startswith("hero"):
        save(im, f"hero_{w.split('-')[1]}", q=62, webp=True)
    elif w == "type":
        save(im, "type/base", q=64, webp=True)
        save(im.resize((800, 450), Image.LANCZOS), "type/base_m")
    elif w.startswith("turn"):
        cw = w.split("-")[1]
        save(im, f"turn/{cw}/d_000", q=56, webp=True)
        save(im.resize((720, 450), Image.LANCZOS), f"turn/{cw}/m_000", q=56)
    elif w.startswith("x"):
        i = w.split("-")[1]
        save(im, f"x/s{i}", q=62, webp=i == "0")
        save(im.resize((800, 500), Image.LANCZOS), f"x/s{i}_m", q=60)
json.dump(log, open(os.path.join(HERE, "capture_log.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: [v["sec"], v["errors"][:1]] for k, v in log["shots"].items()}, ensure_ascii=False))
