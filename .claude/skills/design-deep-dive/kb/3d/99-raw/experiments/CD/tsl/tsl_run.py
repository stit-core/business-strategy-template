#!/usr/bin/env python3
"""CD2 · TSL на WebGPU / тот же TSL на откате WebGL2 / GLSL на WebGLRenderer: python3 tsl_run.py OUT [--repeat 3] (slot_run --heavy)."""
import argparse, io, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import lp
from PIL import Image
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--repeat', type=int, default=3); ap.add_argument('--ms', type=int, default=2500); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
httpd, base = lp.serve()
WEBGPU = ['--enable-unsafe-webgpu', '--enable-features=Vulkan']
res = []
with sync_playwright() as p:
    for rep in range(a.repeat):
        for name, page in (('gl', 'gl.html'), ('webgpu', 'tsl.html'), ('fallback', 'tsl.html?gl=1')):
            br = p.chromium.launch(args=lp.GPU_ARGS + lp.NOVSYNC + WEBGPU)          # новый процесс — холодный кэш шейдеров
            pg = br.new_page(viewport={'width': 960, 'height': 600}); errs = []
            pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
            sep = '&' if '?' in page else '?'
            pg.goto(f"{base}/99-raw/experiments/CD/tsl/{page}{sep}ms={a.ms}", wait_until='load')
            try:
                pg.wait_for_function('window.__done === true', timeout=a.ms + 120000); r = pg.evaluate('window.__res')
            except Exception as e:
                r = {'error': str(e)[:200]}
            r.update({'name': name, 'rep': rep, 'console': errs[:4], 'loadavg': round(os.getloadavg()[0], 1)})
            if rep == 0 and 'error' not in r:
                Image.open(io.BytesIO(pg.screenshot(type='png'))).convert('RGB').save(os.path.join(a.out, f'{name}.png'))
            print(json.dumps(r, ensure_ascii=False)); res.append(r); br.close()
httpd.shutdown()
json.dump(res, open(os.path.join(a.out, 'tsl.json'), 'w'), ensure_ascii=False, indent=1)
