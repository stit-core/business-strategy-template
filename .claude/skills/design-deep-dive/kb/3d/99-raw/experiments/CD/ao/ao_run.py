#!/usr/bin/env python3
"""CD2 · цена AO трёх видов: python3 ao_run.py OUT_DIR [--repeat 3] [--ms 2500] — через slot_run --kind browser --heavy (тишина)."""
import argparse, io, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import lp
from PIL import Image
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--repeat', type=int, default=3); ap.add_argument('--ms', type=int, default=2500)
ap.add_argument('--modes', default='none,n8pm,n8,gtao,ssao'); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
httpd, base = lp.serve()
res = []
with sync_playwright() as p:
    br = lp.launch(p, lp.NOVSYNC)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    for rep in range(a.repeat):
        for m in a.modes.split(','):
            pg = ctx.new_page(); errs = []
            pg.on('console', lambda msg: errs.append(f'{msg.type}: {msg.text}') if msg.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
            pg.goto(f"{base}/99-raw/experiments/CD/ao/ao.html?ao={m}&ms={a.ms}", wait_until='load')
            pg.wait_for_function('window.__done === true', timeout=a.ms + 120000)
            r = pg.evaluate('window.__res'); r.update({'rep': rep, 'console': errs[:4], 'loadavg': round(os.getloadavg()[0], 1)})
            if rep == 0:
                Image.open(io.BytesIO(pg.screenshot(type='png'))).convert('RGB').save(os.path.join(a.out, f'{m}.png'))
            print(json.dumps(r, ensure_ascii=False)); res.append(r); pg.close()
    br.close()
httpd.shutdown()
json.dump(res, open(os.path.join(a.out, 'ao.json'), 'w'), ensure_ascii=False, indent=1)
