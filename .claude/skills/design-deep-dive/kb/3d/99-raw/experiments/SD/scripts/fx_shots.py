"""fx_shots.py — снимки и числа «фонарика» (C, SD2) в Chromium на реальной видеокарте (как fx_probe: ANGLE → GL).
  1) постер (до шейдера), 2) первый кадр шейдера при полумраке 0 (canvas поверх постера) → ΔE к постеру по области кадра,
  3) луч на дефекте (булавка 1, 3 …) и без луча (полумрак, луч в пустом углу), 4) список «найдено», ошибки консоли,
  5) --video: запись 10 с движения фонаря (webm) по сценарию курсора; 6) --mobile: Pixel 7 (касание).
    python3 fx_shots.py PAGE_DIR OUT_DIR [--mobile] [--video] [--size 1440x900] [--prefix c]"""
import http.server
import json
import math
import os
import socketserver
import sys
import threading
import time

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

GPU = ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"]


def serve(root):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=root, **k)

        def log_message(self, *a):
            pass
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def lab(rgb):
    c = rgb.astype(np.float64) / 255
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def de(a, b):
    return np.sqrt(((lab(a) - lab(b)) ** 2).sum(-1))


def main():
    a = sys.argv[1:]
    root, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    mobile, video = "--mobile" in a, "--video" in a
    prefix = a[a.index("--prefix") + 1] if "--prefix" in a else "c"
    W, H = map(int, (a[a.index("--size") + 1] if "--size" in a else "1440x900").split("x"))
    os.makedirs(out, exist_ok=True)
    srv, port = serve(root)
    url = f"http://127.0.0.1:{port}/index.html"
    res = {"url": url, "mobile": mobile}
    logs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=GPU)
        kw = dict(pw.devices["Pixel 7"]) if mobile else dict(viewport={"width": W, "height": H}, device_scale_factor=1)
        if video:
            kw["record_video_dir"] = out
            kw["record_video_size"] = {"width": kw.get("viewport", {"width": W})["width"], "height": kw.get("viewport", {"height": H})["height"]}
        ctx = b.new_context(**kw)
        p = ctx.new_page()
        p.on("console", lambda m: logs.append(f"{m.type}: {m.text[:300]}"))
        p.on("pageerror", lambda e: logs.append(f"pageerror: {str(e)[:300]}"))
        t0 = time.time()
        p.goto(url, wait_until="load")
        p.wait_for_function("window.__ready === true", timeout=20000)
        res["ready_s"] = round(time.time() - t0, 2)
        res["info"] = p.evaluate("window.__info")
        stage = p.evaluate("(() => { const s = document.querySelector('.plan__stage'); s.scrollIntoView({block: 'center'}); const r = s.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()") if mobile else \
            p.evaluate("(() => { const r = document.querySelector('.plan__stage').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        p.wait_for_timeout(700)
        if mobile:
            # SD3: однократный проход фонаря при появлении плана (≥ 70 % в кадре) — кадр середины и конца, время
            try:
                p.wait_for_function("window.__fonarik && window.__fonarik.state().tour", timeout=3000, polling=20)
                t_tour = time.time()
                p.wait_for_timeout(1150)
                p.screenshot(path=f"{out}/{prefix}_tour-mid.png")
                res["tour_mid"] = p.evaluate("window.__fonarik.state()")
                p.wait_for_function("(() => { const s = window.__fonarik.state(); return !s.tour && s.dark === 0; })()", timeout=8000, polling=20)
                res["tour_s"] = round(time.time() - t_tour + 1.15 * 0, 2)
                p.wait_for_timeout(300)
                p.screenshot(path=f"{out}/{prefix}_tour-end.png")
                res["tour_end_hint"] = p.evaluate("(document.querySelector('.plan__hint') || {}).textContent")
            except Exception as e:
                res["tour_err"] = str(e)[:160]
        res["stage"] = stage
        clip = {"x": max(0, stage[0]), "y": max(0, stage[1]), "width": min(stage[2], (kw.get("viewport") or {"width": W})["width"] - max(0, stage[0])),
                "height": min(stage[3], (kw.get("viewport") or {"height": H})["height"] - max(0, stage[1]))}
        p.screenshot(path=f"{out}/{prefix}_poster.png")
        s_poster = np.asarray(Image.open(f"{out}/{prefix}_poster.png").convert("RGB"))
        # первый кадр шейдера при полумраке 0: показать canvas без затемнения
        p.evaluate("(() => { window.__fonarik.frame(); document.querySelector('.plan--iso').classList.add('fx-on'); })()")
        p.wait_for_timeout(300)
        p.screenshot(path=f"{out}/{prefix}_frame0.png")
        s_f0 = np.asarray(Image.open(f"{out}/{prefix}_frame0.png").convert("RGB"))
        x0, y0 = int(clip["x"]), int(clip["y"])
        x1, y1 = int(clip["x"] + clip["width"]), int(clip["y"] + clip["height"])
        d = de(s_poster[y0:y1, x0:x1], s_f0[y0:y1, x0:x1])
        res["dE_poster_vs_frame0"] = {"mean": round(float(d.mean()), 3), "p95": round(float(np.percentile(d, 95)), 3),
                                      "p99": round(float(np.percentile(d, 99)), 3), "max": round(float(d.max()), 2)}
        p.evaluate("document.querySelector('.plan--iso').classList.remove('fx-on')")
        # сценарий: луч в пустой угол (без дефекта), потом на булавки
        pins = p.evaluate("""[...document.querySelectorAll('.plan__pins .pin')].map(e => { const r = e.getBoundingClientRect();
            const s = document.querySelector('.plan__stage').getBoundingClientRect(); return [e.dataset.d, (r.left + r.width / 2 - s.left) / s.width, (r.top + r.height / 2 - s.top) / s.height]; })""")
        res["pins_frac"] = pins
        shots = {}

        def aim(fx, fy, wait=900, name=None):
            if mobile:
                p.touchscreen.tap(stage[0] + fx * stage[2], stage[1] + fy * stage[3])
            else:
                p.mouse.move(stage[0] + fx * stage[2], stage[1] + fy * stage[3], steps=12)
            p.wait_for_timeout(wait)
            if name:
                p.screenshot(path=f"{out}/{prefix}_{name}.png")
                shots[name] = p.evaluate("window.__fonarik.state()")
        # экранные доли stage для точек дефектов (та же проекция, что в fonarik.js)
        FR = dict(u0=-4.9, u1=3.7, w0=-0.6, w1=8.5)
        DEF = {"1": (2.5, 4.25, 0.0), "2": (2.0, 6.42, 0.87), "3": (3.25, 3.4167, 0.0), "4": (9.233, 4.6667, 0.5)}
        crop = [335 / 1800, 105 / 1905, 1402 / 1800, 1758 / 1905] if mobile else [0, 0, 1, 1]

        def frac(pt):
            x, y, z = pt
            u = (x - y) / math.sqrt(2); w = (x + y) * 0.40824829 + z * 0.81649658
            uf = ((u - FR["u0"]) / (FR["u1"] - FR["u0"]), (FR["w1"] - w) / (FR["w1"] - FR["w0"]))
            return (uf[0] - crop[0]) / crop[2], (uf[1] - crop[1]) / crop[3]
        res["def_frac"] = {k: frac(v) for k, v in DEF.items()}
        # «без луча»: полумрак, луч в пустом углу кадра (бумага за квартирой)
        aim(0.12, 0.93, 1200, "beam-off")
        for k in ("1", "2", "3", "4"):
            fx, fy = res["def_frac"][k]
            aim(fx, fy, 900, f"beam-pin{k}")
        res["states"] = shots
        res["found_list"] = p.evaluate("[...document.querySelectorAll('.plan__list li.is-found')].map(e => e.dataset.d)")
        res["hint"] = p.evaluate("(document.querySelector('.plan__hint') || {}).textContent")
        # покой: 1,5 с без движения — число кадров rAF с отрисовкой
        p.evaluate("""(() => { window.__dc = 0; const gl = document.querySelector('.plan__fx').getContext('webgl2');
            const o = gl.drawArrays.bind(gl); gl.drawArrays = (...x) => { window.__dc++; return o(...x); }; })()""")
        p.wait_for_timeout(1500)
        res["idle_draws_1500ms"] = p.evaluate("window.__dc")
        if video:
            # 10 с: вход курсора, медленный обход, дефекты по очереди, уход — свет возвращается
            t_start = time.time()
            path = [(0.95, 0.95)] + [(0.2 + 0.25 * math.cos(i / 40 * 2 * math.pi), 0.55 + 0.18 * math.sin(i / 40 * 2 * math.pi)) for i in range(40)]
            for fx, fy in path:
                aim(fx, fy, 60)
            for k in ("1", "2", "3", "4"):
                fx, fy = res["def_frac"][k]
                aim(fx, fy, 700)
            if not mobile:
                p.mouse.move(stage[0] - 60, stage[1] + stage[3] * 0.5, steps=10)
            p.wait_for_timeout(max(0, int((10.5 - (time.time() - t_start)) * 1000)))
        res["console"] = logs[:30]
        res["console_errors"] = len([x for x in logs if x.startswith(("error", "pageerror"))])
        vid = p.video.path() if video else None
        ctx.close()
        b.close()
        if vid:
            res["video"] = vid
    srv.shutdown()
    json.dump(res, open(f"{out}/{prefix}_fx.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("states",)}, ensure_ascii=False)[:2500])


if __name__ == "__main__":
    main()
