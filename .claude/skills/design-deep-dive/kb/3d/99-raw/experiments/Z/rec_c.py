#!/usr/bin/env python3
"""rec_c — запись 10 с страницы C (гибрид): рука тянется за курсором (IK кода на модулях Blender). Дорожка Z2.

    python3 slot_run.py --kind browser --label Z2-rec -- python3 rec_c.py OUT.webm [--page c-hybrid] [--sec 10]
Сервер — корень 3d-research (как lpz.py), Chromium с GPU (ANGLE GL), 1440×900; курсор идёт плавной фигурой Лиссажу по правой
половине окна (граница IK — колонка текста), затем ролик обрезается до последних N секунд (ffmpeg, VP9 без перекодирования нет —
перекодируем crf 34)."""
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


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()

    def guess_type(self, path):
        p = str(path)
        if p.endswith(('.js', '.mjs')):
            return 'text/javascript'
        if p.endswith('.glb'):
            return 'model/gltf-binary'
        return super().guess_type(path)


def main():
    a = sys.argv[1:]
    out = a[0]
    page = a[a.index('--page') + 1] if '--page' in a else 'c-hybrid'
    sec = float(a[a.index('--sec') + 1]) if '--sec' in a else 10.0
    from playwright.sync_api import sync_playwright
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(H, directory=ROOT))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/15-showcase/zveno/{page}/index.html"
    vd = tempfile.mkdtemp(prefix='zrec_')
    W, Hh = 1440, 900
    with sync_playwright() as p:
        br = p.chromium.launch(args=GPU_ARGS)
        ctx = br.new_context(viewport={'width': W, 'height': Hh}, record_video_dir=vd, record_video_size={'width': W, 'height': Hh})
        pg = ctx.new_page()
        logs = []
        pg.on('console', lambda m: logs.append(f'{m.type}: {m.text}'))
        pg.goto(url, wait_until='load')
        pg.wait_for_function("document.documentElement.classList.contains('gl-on')", timeout=60000)
        pg.wait_for_timeout(2500)                                  # пробуждение руки и постер погас
        t_start = time.time()
        n = int((sec + 1.5) * 30)
        for i in range(n):                                         # Лиссажу по правой половине окна: рука «следит» за курсором
            u = i / 30.0
            x = W * (0.72 + 0.2 * math.sin(u * 0.9))
            y = Hh * (0.46 + 0.3 * math.sin(u * 1.4 + 0.6))
            pg.mouse.move(x, y)
            pg.wait_for_timeout(33)
        pg.wait_for_timeout(600)
        rec = time.time() - t_start
        vpath = pg.video.path()
        ctx.close(); br.close()
    httpd.shutdown()
    total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', vpath],
                                 capture_output=True, text=True).stdout.strip() or 0)
    start = max(0.0, total - rec + 0.3)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{start:.2f}', '-i', vpath, '-t', f'{sec:.2f}', '-c:v', 'libvpx-vp9',
                    '-b:v', '0', '-crf', '34', '-an', out], check=True)
    shutil.rmtree(vd, ignore_errors=True)
    print('REC', out, round(os.path.getsize(out) / 1024, 1), 'KB', 'console:', [l for l in logs if 'error' in l.lower()][:5],
          [l for l in logs if 'timing' in l][:2])


if __name__ == '__main__':
    main()
