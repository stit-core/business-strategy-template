#!/usr/bin/env python3
"""drive.py — прогон страницы «Ё» в Chromium (Playwright): снимки состояний и запись набора (webm).

    python3 drive.py PAGE_DIR OUT_DIR [--mobile] [--reduce] [--steps first,type,colors,explode] [--video SEC] [--port 8783]
PAGE_DIR копируется в скретчпад (serve_br пишет *.br внутрь), раздаётся serve_br.py на порту 8783, сервер гасится по PID.
Набор по-русски: KeyboardEvent с настоящим code (из паспорта) и key = буква — так посетитель в раскладке RU (у headless — US).
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

R = "/home/mm/Документы/app-design/blender-research"
SCR = "/tmp/claude-1000/-home-mm-----------app-design/2e530199-ecfd-48ab-994b-f3dd1c91c010/scratchpad"
GPU = ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"]
a = sys.argv[1:]
PAGE, OUT = os.path.abspath(a[0]), os.path.abspath(a[1])


def opt(n, d=None):
    return a[a.index(n) + 1] if n in a else d


MOBILE = "--mobile" in a
REDUCE = "--reduce" in a
STEPS = opt("--steps", "first,type,colors,explode").split(",")
VIDEO = float(opt("--video", "0"))
PORT = int(opt("--port", "8783"))
TEXT = opt("--text", "ёлка и ёж. Всё на месте")
os.makedirs(OUT, exist_ok=True)
P = json.load(open(f"{R}/15-showcase/keyboard/passport.json"))
CODE = {}
for k in P["layout"]:
    for ch in (k["l1"], k["l2"]):
        if ch and len(ch) == 1:
            CODE.setdefault(ch.lower(), k["code"])
CODE.update({"ё": "Backquote", " ": "Space", ".": "Slash", ",": "Slash"})

copy = os.path.join(SCR, "kb_serve_" + os.path.basename(PAGE.rstrip("/")))
if os.path.isdir(copy):
    shutil.rmtree(copy)
shutil.copytree(PAGE, copy)
srv = subprocess.Popen([sys.executable, f"{R}/99-raw/experiments/F1/02-hero-variants/serve_br.py", copy, str(PORT)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
import socket
for _ in range(240):                                   # serve_br сначала сжимает файлы (brotli q11) — ждём порт
    try:
        socket.create_connection(("127.0.0.1", PORT), timeout=0.2).close()
        break
    except OSError:
        time.sleep(0.25)
URL = f"http://127.0.0.1:{PORT}/index.html"
log = {"url": URL, "mobile": MOBILE, "reduce": REDUCE, "console": [], "errors": [], "shots": [], "load": os.getloadavg()}
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=GPU)
        kw = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True) if MOBILE \
            else dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        if REDUCE:
            kw["reduced_motion"] = "reduce"
        if VIDEO:
            kw["record_video_dir"] = OUT
            kw["record_video_size"] = kw["viewport"]
        ctx = b.new_context(**kw)
        t_ctx = time.time()
        pg = ctx.new_page()
        pg.on("console", lambda m: log["console"].append(f"{m.type}: {m.text}"[:600]))
        pg.on("pageerror", lambda e: log["errors"].append(str(e)[:600]))
        pg.goto(URL, wait_until="load")
        pg.wait_for_timeout(900)

        def shot(name, full=False):
            p = os.path.join(OUT, name + ".png")
            pg.screenshot(path=p, full_page=full)
            log["shots"].append(p)

        def goto_sel(sel, extra=0):
            pg.evaluate(f"(()=>{{const el=document.querySelector('{sel}'); window.scrollTo(0, el.getBoundingClientRect().top + scrollY + {extra});}})()")

        def wait3d(extra=700):
            """A/C: снимать живое 3D, а не запасной кадр (three грузится по намерению — остановка ≥ 2,5 с или нажатие)."""
            v = pg.evaluate("document.querySelector('meta[name=kb-variant]')?.content || ''")
            if v in ("a", "c") and not REDUCE:
                try:
                    pg.wait_for_function("window.__kb3d && window.__kb3d.frames > 2", timeout=15000)
                    if not MOBILE:        # десктоп: пост (N8AO) — отдельным чанком после первого кадра; снимать с ним
                        pg.wait_for_function("!!window.__kbPost", timeout=15000)
                except Exception:
                    log.setdefault("warn", []).append("3D не готово за 15 с")
                pg.wait_for_timeout(extra)

        def key(ch, down=True):
            c = CODE.get(ch.lower())
            if not c:
                return
            pg.evaluate("([t,c,k])=>window.dispatchEvent(new KeyboardEvent(t,{code:c,key:k,bubbles:true}))",
                        ["keydown" if down else "keyup", c, ch])

        def type_text(s, gap=150):
            for ch in s:
                key(ch, True)
                pg.wait_for_timeout(70)
                key(ch, False)
                pg.wait_for_timeout(gap)

        if "first" in STEPS:
            shot("first")
        if "type" in STEPS:
            goto_sel("#typed", -24 if not MOBILE else -60)
            pg.wait_for_timeout(3000)
            wait3d(900)
            if VIDEO:
                t0 = time.time()
                log["video_type_start_s"] = round(t0 - t_ctx, 2)
                type_text(TEXT, 260)
                while time.time() - t0 < VIDEO - 1:
                    type_text("ё", 400)
            else:
                type_text("ёлка и ёж", 120)
            key("ф", True)
            pg.wait_for_timeout(120)
            shot("type")
            key("ф", False)
        if "colors" in STEPS:
            goto_sel("#colors", 0)
            pg.wait_for_timeout(3000)
            wait3d()
            shot("colors_snow")
            pg.click('.chips [data-cw="graphite"]')
            pg.wait_for_timeout(2500)
            shot("colors_graphite")
            box = pg.locator("#stage-turn").bounding_box()
            if box:
                pg.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
                pg.mouse.down()
                pg.mouse.move(box["x"] + box["width"] * 0.62, box["y"] + box["height"] * 0.5, steps=8)
                pg.mouse.up()
                pg.wait_for_timeout(1500)
                shot("colors_graphite_turned")
            pg.click('.chips [data-cw="linen"]')
            pg.wait_for_timeout(2500)
            shot("colors_linen")
            pg.click('.chips [data-cw="snow"]')
            pg.wait_for_timeout(800)
        if "explode" in STEPS:
            goto_sel("#inside", 0)
            pg.wait_for_timeout(2800)
            wait3d()
            for frac in (0.0, 0.35, 0.7, 1.0):
                pg.evaluate(f"(()=>{{const el=document.querySelector('#inside'); const r=el.getBoundingClientRect(); window.scrollTo(0, r.top+scrollY+(r.height-innerHeight)*{frac});}})()")
                pg.wait_for_timeout(1800)
                shot(f"explode_{int(frac * 100):03d}")
        log["kb"] = pg.evaluate("window.__kb || null")
        log["frames3d"] = pg.evaluate("window.__kb3d ? window.__kb3d.frames : null")
        vid = pg.video.path() if VIDEO else None
        ctx.close()
        b.close()
        if vid:
            # обрезка: 10 с набора с начала печати → VP9
            out_v = os.path.join(OUT, "typing.webm")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(max(0, log["video_type_start_s"] - 0.3)), "-i", vid,
                            "-t", str(VIDEO), "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34", "-an", out_v], check=False)
            log["video"] = out_v if os.path.exists(out_v) else None
finally:
    srv.send_signal(signal.SIGTERM)
    srv.wait(timeout=5)
json.dump(log, open(os.path.join(OUT, "drive_log.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({"errors": log["errors"], "kb": log.get("kb"), "frames3d": log.get("frames3d"),
                  "console_errors": [c for c in log["console"] if c.startswith("error")][:5]}, ensure_ascii=False)[:2500])
