#!/usr/bin/env python3
"""check_b — проверка страницы B (секвенции Blender по прокрутке) в headless Chromium. Дорожка Z3, 26.09.2026.

    python3 slot_run.py --kind browser --label Z3-checkb -- python3 check_b.py OUT_DIR [--page b-blender]
Проверки (итог — OUT_DIR/check_b.json + снимки):
  1. стык «постер → кадр 0»: снимок первого экрана до подмены (класс gl-pending, виден <picture>) и после (gl-on, холст) —
     средняя разница и p99 по пикселям (цель: «без прыжка» — сдвиг не виден, разница — только перекодирование);
  2. окно памяти: после прокрутки через весь сюжет и скан декодированных кадров (ImageBitmap) в памяти ≤ окна (12 / 10);
  3. 0 кадров в покое: счётчик drawImage холста за 2 с покоя после прокрутки (цель 0) и за время прокрутки (> 0);
  4. reduce (prefers-reduced-motion): ни одного запроса seq/*.avif, станции видимы, холст скрыт;
  5. телефон 390×844 (DPR 3 → холст ≤ 1,5): набор m (seq/*-m/), размер холста / CSS-размер.
"""
import functools
import http.server
import json
import os
import socketserver
import sys
import threading

import numpy as np
from PIL import Image

ROOT = "/home/mm/Документы/app-design/blender-research"
GPU_ARGS = ['--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist', '--enable-gpu']
COUNT_JS = """(() => { window.__draws = 0; const d = CanvasRenderingContext2D.prototype.drawImage;
  CanvasRenderingContext2D.prototype.drawImage = function (...a) { window.__draws++; return d.apply(this, a); }; })();"""
GEOM_JS = """() => { const y = (s) => { const e = document.querySelector(s); const r = e.getBoundingClientRect();
  return { top: Math.round(r.top + scrollY), h: Math.round(e.offsetHeight) }; };
  return { vh: innerHeight, story: y('[data-scene="story"]'), scan: y('[data-scene="scan"]') }; }"""


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()

    def guess_type(self, path):
        p = str(path)
        if p.endswith(('.js', '.mjs')):
            return 'text/javascript'
        if p.endswith('.avif'):
            return 'image/avif'
        return super().guess_type(path)


def diff(a, b):
    x = np.asarray(Image.open(a).convert('RGB')).astype(np.int16)
    y = np.asarray(Image.open(b).convert('RGB')).astype(np.int16)
    d = np.abs(x - y).max(-1)
    return {"mean": round(float(d.mean()), 2), "p99": float(np.percentile(d, 99)), "gt24_pct": round(float((d > 24).mean() * 100), 2)}


def scroll_through(pg, y0, y1, step=90, wait=45):
    for y in range(int(y0), int(y1) + 1, step):
        pg.evaluate(f"window.scrollTo(0, {y})"); pg.wait_for_timeout(wait)


def main():
    a = sys.argv[1:]
    out = a[0]; os.makedirs(out, exist_ok=True)
    page = a[a.index('--page') + 1] if '--page' in a else 'b-blender'
    only = a[a.index('--only') + 1] if '--only' in a else None      # desk | mob | reduce — часть проверок (пока нет телефонных наборов)
    from playwright.sync_api import sync_playwright
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(H, directory=ROOT))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/15-showcase/zveno/{page}/index.html"
    res = {"url": url}
    with sync_playwright() as p:
        br = p.chromium.launch(args=GPU_ARGS)
        for name, kw in (("desk", dict(viewport={'width': 1440, 'height': 900})),
                         ("mob", dict(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True))):
            if only and only != name:
                continue
            ctx = br.new_context(**kw)
            pg = ctx.new_page()
            logs, reqs = [], []
            pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}'))
            pg.on('pageerror', lambda e: logs.append(f'pageerror: {e}'))
            pg.on('request', lambda r: reqs.append(r.url))
            pg.add_init_script(COUNT_JS)
            # 1. постер до подмены: блокируем main.js на время первого снимка — виден только <picture>
            pg.route('**/js/main.js', lambda r: r.abort())
            pg.goto(url, wait_until='load'); pg.wait_for_timeout(700)
            f_poster = os.path.join(out, f'{name}_poster.png'); pg.screenshot(path=f_poster)
            pg.unroute('**/js/main.js')
            pg.goto(url, wait_until='load')
            pg.wait_for_function("document.documentElement.classList.contains('gl-on')", timeout=60000)
            pg.wait_for_timeout(1500)                     # постер гаснет 600 мс + 150 мс задержки
            f_canvas = os.path.join(out, f'{name}_frame0.png'); pg.screenshot(path=f_canvas)
            r = {"seam_poster_vs_frame0": diff(f_poster, f_canvas)}
            r["canvas"] = pg.evaluate("(() => { const c = document.querySelector('.stage'); return {w: c.width, h: c.height, cssW: c.clientWidth, cssH: c.clientHeight, dpr: devicePixelRatio}; })()")
            r["canvas"]["ratio"] = round(r["canvas"]["w"] / max(1, r["canvas"]["cssW"]), 3)
            g = pg.evaluate(GEOM_JS)
            d0 = pg.evaluate("window.__draws")
            scroll_through(pg, 0, g['story']['top'] + g['story']['h'] - g['vh'])
            scroll_through(pg, g['scan']['top'] - g['vh'], g['scan']['top'] + g['scan']['h'] - g['vh'])
            pg.wait_for_timeout(1200)
            d1 = pg.evaluate("window.__draws")
            pg.wait_for_timeout(2000)
            d2 = pg.evaluate("window.__draws")
            r["draws_scroll"] = d1 - d0
            r["draws_idle_2s"] = d2 - d1
            r["seq_state"] = pg.evaluate("window.__zseq ? window.__zseq() : null")
            f_scan = os.path.join(out, f'{name}_scan_end.png'); pg.screenshot(path=f_scan)
            r["seq_requests"] = sum('/seq/' in u for u in reqs)
            r["seq_sets"] = sorted({u.split('/seq/')[1].split('/')[0] for u in reqs if '/seq/' in u})
            r["console"] = [l for l in logs if 'error' in l.lower() or 'timing' in l.lower()][:6]
            res[name] = r
            ctx.close()
        # 4. reduce
        if only and only != 'reduce':
            br.close(); httpd.shutdown()
            json.dump(res, open(os.path.join(out, f'check_b_{only}.json'), 'w'), ensure_ascii=False, indent=1)
            print(json.dumps(res, ensure_ascii=False)[:3000]); return
        ctx = br.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        pg = ctx.new_page(); reqs = []
        pg.on('request', lambda r: reqs.append(r.url))
        pg.goto(url, wait_until='load'); pg.wait_for_timeout(1500)
        g = pg.evaluate(GEOM_JS)
        scroll_through(pg, 0, g['scan']['top'] + g['scan']['h'], step=300, wait=60)
        res["reduce"] = {"seq_requests": sum('/seq/' in u for u in reqs),
                         "stations_visible": pg.evaluate("[...document.querySelectorAll('.station')].filter((e) => e.offsetParent).length"),
                         "html_class": pg.evaluate("document.documentElement.className"),
                         "stage_opacity": pg.evaluate("getComputedStyle(document.querySelector('.stage')).opacity")}
        pg.evaluate(f"window.scrollTo(0, {g['story']['top'] + 200})"); pg.wait_for_timeout(500)
        pg.screenshot(path=os.path.join(out, 'reduce_story.png'))
        ctx.close(); br.close()
    httpd.shutdown()
    json.dump(res, open(os.path.join(out, 'check_b.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False)[:3000])


if __name__ == '__main__':
    main()
