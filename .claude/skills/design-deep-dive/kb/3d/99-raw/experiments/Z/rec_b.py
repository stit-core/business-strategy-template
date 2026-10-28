#!/usr/bin/env python3
"""rec_b — запись 10 с страницы B (секвенции Blender по прокрутке): сюжет «модули» (hero → разнос → сборка → первое движение),
затем «внутри» (скан J3, слои). Дорожка Z3, 26.09.2026.

    python3 slot_run.py --kind browser --label Z3-rec -- python3 rec_b.py OUT.webm [--page b-blender] [--sec 10]
Сервер — корень 3d-research (как lpz.py), Chromium с GPU (ANGLE GL), 1440×900. Перед записью страница один раз медленно
прокручивается до конца (кадры попадают в Blob-кэш секвенций — как у посетителя, который уже прокрутил), потом возврат наверх;
записывается ровная прокрутка по времени: 0–6 с сюжет (t 0 → 2), 6–6,8 с «цифры», 6,8–10 с скан (t 0 → 1). Ролик обрезается до
последних N секунд (ffmpeg, VP9 crf 34)."""
import functools
import http.server
import math
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time

ROOT = "/home/mm/Документы/app-design/blender-research"
GPU_ARGS = ['--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist', '--enable-gpu']

GEOM_JS = """() => { const y = (s) => { const e = document.querySelector(s); const r = e.getBoundingClientRect();
  return { top: Math.round(r.top + scrollY), h: Math.round(e.offsetHeight) }; };
  return { vh: innerHeight, hero: y('[data-section="hero"]'), story: y('[data-scene="story"]'), scan: y('[data-scene="scan"]'),
           max: document.documentElement.scrollHeight - innerHeight }; }"""


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


def ease(x):
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def main():
    a = sys.argv[1:]
    out = a[0]
    page = a[a.index('--page') + 1] if '--page' in a else 'b-blender'
    sec = float(a[a.index('--sec') + 1]) if '--sec' in a else 10.0
    from playwright.sync_api import sync_playwright
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(H, directory=ROOT))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/15-showcase/zveno/{page}/index.html"
    vd = tempfile.mkdtemp(prefix='zrecb_')
    W, Hh = 1440, 900
    with sync_playwright() as p:
        br = p.chromium.launch(args=GPU_ARGS)
        ctx = br.new_context(viewport={'width': W, 'height': Hh}, record_video_dir=vd, record_video_size={'width': W, 'height': Hh})
        pg = ctx.new_page()
        logs = []
        pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}'))
        pg.on('pageerror', lambda e: logs.append(f'pageerror: {e}'))
        pg.goto(url, wait_until='load')
        pg.wait_for_function("document.documentElement.classList.contains('gl-on')", timeout=60000)
        g = pg.evaluate(GEOM_JS)
        y_story_end = g['story']['top'] + g['story']['h'] - g['vh']
        y_scan0 = g['scan']['top']
        y_scan_end = g['scan']['top'] + g['scan']['h'] - g['vh']
        for y in range(0, int(y_scan_end) + 1, 120):              # прогрев: байты кадров в Blob-кэш (как после первой прокрутки)
            pg.evaluate(f"window.scrollTo(0, {y})"); pg.wait_for_timeout(60)
        pg.wait_for_timeout(1500)
        pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(2500)
        t_start = time.time()
        fps, n = 30, int(sec * 30)
        seg = [(0.0, 6.0, 0, y_story_end), (6.0, 6.8, y_story_end, y_scan0), (6.8, sec - 0.2, y_scan0, y_scan_end)]
        for i in range(n + 6):
            u = i / fps
            y = y_scan_end
            for t0, t1, a0, a1 in seg:
                if u < t1:
                    y = a0 + (a1 - a0) * (ease((u - t0) / (t1 - t0)) if t0 < t1 else 1.0)
                    break
            pg.evaluate(f"window.scrollTo(0, {int(y)})")
            pg.wait_for_timeout(1000 / fps)
        pg.wait_for_timeout(500)
        rec = time.time() - t_start
        vpath = pg.video.path()
        ctx.close(); br.close()
    httpd.shutdown()
    total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', vpath],
                                 capture_output=True, text=True).stdout.strip() or 0)
    start = max(0.0, total - rec + 0.1)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{start:.2f}', '-i', vpath, '-t', f'{sec:.2f}', '-c:v', 'libvpx-vp9',
                    '-b:v', '0', '-crf', '34', '-an', out], check=True)
    shutil.rmtree(vd, ignore_errors=True)
    print('REC', out, round(os.path.getsize(out) / 1024, 1), 'KB', 'geom', g, 'console:',
          [l for l in logs if 'error' in l.lower()][:5], [l for l in logs if 'timing' in l][:2])


if __name__ == '__main__':
    main()
