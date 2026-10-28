#!/usr/bin/env python3
"""Z2 · копия CD/lp.py (дорожка CD, только чтение) — стенд preview.html в папке Z, бандл cz = страница c-hybrid.
CD · «Звено» код v3: кадры состояний по флагам, постеры, кадры страницы, цена кадра, листы (дорожка CD, 15-showcase, 25.09.2026).

Копия J/04 `lp.py` (creative-research/99-raw/experiments/J/04-light-pass/lp.py, агент J2), пути — на 3d-research:
раздача — корень 3d-research/ (стенды CD и страница 15-showcase/zveno/a-code видны одним сервером).
Браузер — только через очередь:  python3 $R/99-raw/tools/slot_run.py --kind browser --label CD-… -- python3 lp.py <команда> …
Команды:
  frames --b v2|v3 [--f all|none|studio,world|-ao] --out DIR [--mobile] [--states hero,…] [--size 960x600] [--dpr 1]
         кадры состояний через preview.html + DIR/sheet.jpg + frames.log (вызовы, треугольники, init)
  posters --out DIR                  постеры страницы своим рендером v3 (hero-d/-m, 5 станций, WebP q80)
  shots  --out DIR [--rm] [--page a-code] настоящая страница: первый экран + станции, десктоп 1440×900 и телефон 390×844
  bench  --out FILE.json --sets "v2:all;v3:none;v3:studio;…" [--ms 3000] [--repeat 2] [--modes desk,mob]
         цена кадра без vsync (--disable-gpu-vsync --disable-frame-rate-limit): десктоп 1440×900 DPR 1,5, телефон 412×915 DPR 1,25
  sheet  --pairs DIR_A DIR_B --out FILE [--states …] [--la до --lb после] [--title …]   (без браузера)
"""
import argparse
import functools
import http.server
import io
import json
import os
import socketserver
import sys
import threading
import time

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))                 # 3d-research/
REL = os.path.relpath(HERE, ROOT)                                            # 99-raw/experiments/CD
PAGE = os.path.join(ROOT, '15-showcase', 'zveno')
GPU_ARGS = ['--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist', '--enable-gpu']
NOVSYNC = ['--disable-gpu-vsync', '--disable-frame-rate-limit']
STATES = {  # имя → (фаза, t, указатель или None)
    'hero': ('story', 0.0, None), 'hero-ik': ('story', 0.0, (-0.62, -0.28)), 'hero-ik2': ('story', 0.0, (0.55, 0.35)),
    'straight': ('story', 1.15, None), 'exploded': ('story', 1.42, None), 'approach': ('story', 1.64, None),
    'locking': ('story', 1.8, None), 'lock-flash': ('story', 1.79, None), 'first-move': ('story', 2.0, None),
    'first-move-ik': ('story', 2.0, (-0.5, -0.1)),
    # фаза 2: указатель над частями первого экрана (доли окна −1…1, y вниз), как на странице 1440×900
    'ik-head': ('story', 0.0, (-0.47, -0.29)), 'ik-lead': ('story', 0.0, (-0.45, 0.22)), 'ik-cta': ('story', 0.0, (-0.6, 0.55)),
    'ik-top': ('story', 0.0, (0.25, -0.65)), 'ik-right': ('story', 0.0, (0.8, 0.1)), 'ik-low': ('story', 0.0, (0.1, 0.7)),
    'scan': ('scan', 0.3, None), 'scan-half': ('scan', 0.5, None), 'inside': ('scan', 1.0, None),
}
POSTERS = [('hero-d', 'hero', 1600, 1000, False), ('hero-m', 'hero', 600, 1300, True),
           ('st-exploded', 'exploded', 1200, 750, False), ('st-locking', 'locking', 1200, 750, False),
           ('st-first-move', 'first-move', 1200, 750, False), ('st-scan', 'scan-half', 1200, 750, False), ('st-inside', 'inside', 1200, 750, False)]


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def guess_type(self, path):
        if str(path).endswith(('.js', '.mjs')):
            return 'text/javascript'
        return super().guess_type(path)


def serve():
    h = functools.partial(Handler, directory=ROOT)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), h)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def font(sz=14):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def label(im, text, sz=14, fill=(255, 190, 120)):
    d = ImageDraw.Draw(im)
    f = font(sz)
    x0, y0, x1, y1 = d.textbbox((10, 8), text, font=f)
    d.rectangle((x0 - 6, y0 - 4, x1 + 6, y1 + 4), fill=(0, 0, 0))
    d.text((10, 8), text, font=f, fill=fill)
    return im


def launch(p, extra=()):
    return p.chromium.launch(args=GPU_ARGS + list(extra))


EXTRA = ''                                                                    # --extra: сырой хвост запроса (look=p1&glbMap=j3:j2 …)


def preview_url(base, b, state, w, h, mobile, f=None, q=None, dpr=None, mask=False, glb=None):
    phase, t, ptr = STATES[state]
    u = f"{base}/{REL}/preview.html?b={b}&phase={phase}&t={t}&w={w}&h={h}&mobile={1 if mobile else 0}"
    if glb:
        u += f"&glb={glb}"
    if EXTRA:
        u += '&' + EXTRA
    if f:
        u += f"&f={f}"
    if q:
        u += f"&q={q}"
    if dpr:
        u += f"&dpr={dpr}"
    if ptr:
        u += f"&px={ptr[0]}&py={ptr[1]}"
    if mask:
        u += '&mask=1'
    return u


def shoot_preview(page, url, w, h):
    page.set_viewport_size({'width': w, 'height': h})
    page.goto(url, wait_until='load')
    page.wait_for_function('window.__done === true', timeout=90000)
    st = page.evaluate('window.__stats')
    return Image.open(io.BytesIO(page.screenshot(type='png'))).convert('RGB'), st


def cmd_frames(a):
    from playwright.sync_api import sync_playwright
    os.makedirs(a.out, exist_ok=True)
    httpd, base = serve()
    w, h = map(int, a.size.split('x'))
    if a.mobile and a.size == '960x600':
        w, h = 390, 844
    names = [s for s in a.states.split(',') if s]
    log, tiles = [], []
    with sync_playwright() as p:
        br = launch(p)
        page = br.new_page()
        page.on('pageerror', lambda e: log.append(f'pageerror: {e}'))
        page.on('console', lambda m: log.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        for n in names:
            u = preview_url(base, a.b, n, w, h, a.mobile, a.f, a.q, a.dpr, False, a.glb)
            im, st = shoot_preview(page, u, w, h)
            im.save(os.path.join(a.out, f'{n}.png'))
            if a.masks and a.b != 'v2':
                mk, _ = shoot_preview(page, preview_url(base, a.b, n, w, h, a.mobile, a.masks, a.q, a.dpr, True, a.glb), w, h)
                mk.save(os.path.join(a.out, f'{n}_mask.png'))
            for role in [r for r in (a.rolemask or '').split(',') if r]:  # маска одной роли материала (ring, cap…) — замер цвета по роли
                mk, _ = shoot_preview(page, preview_url(base, a.b, n, w, h, a.mobile, a.f, a.q, a.dpr, False, a.glb) + f'&mask={role}', w, h)
                mk.save(os.path.join(a.out, f'{n}_{role}.png'))
            log.append(json.dumps({'state': n, 'url': u.split('?', 1)[1], **st}, ensure_ascii=False))
            tiles.append((n, im, st))
        br.close()
    httpd.shutdown()
    tw = 480 if not a.mobile else 240
    th = int(tw * h / w)
    cols = 4 if not a.mobile else 5
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * th), (0, 0, 0))
    for i, (n, im, st) in enumerate(tiles):
        t = label(im.resize((tw, th), Image.LANCZOS), f"{a.b} {a.f or 'all'} {n} calls={st.get('calls')} tris={st.get('tris')}", 11)
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    sheet.save(os.path.join(a.out, 'sheet.jpg'), quality=84)
    open(os.path.join(a.out, 'frames.log'), 'w').write('\n'.join(log) + '\n')
    print('\n'.join(log[-(len(names) + 6):]))
    return 0


def cmd_posters(a):
    from playwright.sync_api import sync_playwright
    os.makedirs(a.out, exist_ok=True)
    httpd, base = serve()
    log = []
    with sync_playwright() as p:
        br = launch(p)
        page = br.new_page()
        page.on('pageerror', lambda e: log.append(f'pageerror: {e}'))
        page.on('console', lambda m: log.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        for name, state, w, h, mobile in POSTERS:
            im, st = shoot_preview(page, preview_url(base, a.b, state, w, h, mobile, None, 'low' if mobile else 'high', None, False, a.glb), w, h)
            fp = os.path.join(a.out, f'{name}.webp')
            im.save(fp, 'WEBP', quality=80, method=6)
            if a.png:
                im.save(os.path.join(a.png, f'{name}.png'))
            log.append(f'{name}: {os.path.getsize(fp)} B · {json.dumps(st, ensure_ascii=False)}')
        br.close()
    httpd.shutdown()
    open(os.path.join(a.out, 'render.log'), 'w').write('\n'.join(log) + '\n')
    print('\n'.join(log))
    return 0


STATIONS_JS = """() => { const out = [], vh = innerHeight;
  document.querySelectorAll('[data-scene]').forEach((sec) => { const top = sec.getBoundingClientRect().top + scrollY, H = sec.offsetHeight;
    sec.querySelectorAll('.step').forEach((st, i) => { const at = parseFloat(getComputedStyle(st).getPropertyValue('--at'));
      out.push({ scene: sec.dataset.scene, i: i + 1, at, y: Math.round(top + at * Math.max(1, H - vh)) }); }); });
  return out; }"""


def cmd_shots(a):
    from playwright.sync_api import sync_playwright
    os.makedirs(a.out, exist_ok=True)
    httpd, base = serve()
    url = f"{base}/15-showcase/zveno/{a.page}/index.html"
    logs, meta = [], {'url': url, 'rm': a.rm, 'shots': []}
    with sync_playwright() as p:
        br = launch(p)
        meta['browser_version'] = br.version
        for name, vp, mob in (('desk', {'width': 1440, 'height': 900}, False), ('mob', {'width': 390, 'height': 844}, True)):
            kw = dict(viewport=vp, device_scale_factor=2 if mob else 1, reduced_motion='reduce' if a.rm else 'no-preference')
            if mob:
                kw.update(is_mobile=True, has_touch=True)
            ctx = br.new_context(**kw)
            pg = ctx.new_page()
            pg.on('console', lambda m, n=name: logs.append(f'[{n}] {m.type}: {m.text}'))
            pg.on('pageerror', lambda e, n=name: logs.append(f'[{n}] pageerror: {e}'))
            pg.add_init_script("window.__lt = []; try { new PerformanceObserver((l) => l.getEntries().forEach((e) => "
                               "__lt.push([Math.round(e.startTime), Math.round(e.duration)]))).observe({ type: 'longtask', buffered: true }); } catch (e) {}")
            pg.goto(url, wait_until='load')
            pg.wait_for_timeout(a.wait)
            meta[f'longtasks_{name}'] = pg.evaluate('window.__lt')
            suf = '_rm' if a.rm else ''
            fp = os.path.join(a.out, f'{name}{suf}_first.jpg')
            pg.screenshot(path=fp, type='jpeg', quality=88)
            meta['shots'].append({'vp': name, 'file': os.path.basename(fp), 'y': 0, 'html_class': pg.evaluate("document.documentElement.className")})
            if not mob and not a.rm:                       # IK: указатель над заголовком — рука тянется к тексту
                pg.mouse.move(360, 300); pg.wait_for_timeout(120); pg.mouse.move(380, 320); pg.wait_for_timeout(1400)
                fp = os.path.join(a.out, f'{name}_first_ik.jpg'); pg.screenshot(path=fp, type='jpeg', quality=88)
                meta['shots'].append({'vp': name, 'file': os.path.basename(fp), 'y': 0, 'ik': [380, 320]})
                pg.mouse.move(1300, 780); pg.wait_for_timeout(1400)
            if mob and not a.rm:                           # телефон: касание над рукой — цель IK (не ссылка и не кнопка)
                pg.touchscreen.tap(90, 230); pg.wait_for_timeout(1500)
                fp = os.path.join(a.out, f'{name}_first_tap.jpg'); pg.screenshot(path=fp, type='jpeg', quality=88)
                meta['shots'].append({'vp': name, 'file': os.path.basename(fp), 'y': 0, 'tap': [90, 230]})
            for s in pg.evaluate(STATIONS_JS):
                if mob and s['scene'] == 'story' and s['i'] == 2:
                    continue
                pg.evaluate(f"window.scrollTo(0, {s['y']})")
                pg.wait_for_timeout(a.settle)
                fp = os.path.join(a.out, f"{name}{suf}_{s['scene']}{s['i']}.jpg")
                pg.screenshot(path=fp, type='jpeg', quality=88)
                meta['shots'].append({'vp': name, 'file': os.path.basename(fp), **s, 'html_class': pg.evaluate("document.documentElement.className")})
            meta[f'timing_{name}'] = pg.evaluate("(() => { const m = performance.getEntriesByName('hero-first-frame')[0]; return m ? Math.round(m.startTime) : null; })()")
            ctx.close()
        br.close()
    httpd.shutdown()
    meta['console'] = logs
    json.dump(meta, open(os.path.join(a.out, 'shots.json'), 'w'), ensure_ascii=False, indent=1)
    print(url, '| кадров:', len(meta['shots']), '| консоль:', len(logs), '| first-frame:', meta.get('timing_desk'), meta.get('timing_mob'))
    for l in logs[:14]:
        print('  ', l[:220])
    return 0


def cmd_bench(a):
    from playwright.sync_api import sync_playwright
    httpd, base = serve()
    res = []
    with sync_playwright() as p:
        br = launch(p, NOVSYNC)
        for mode in a.modes.split(','):
            if mode == 'desk':
                ctx = br.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1.5)
                q = "w=1440&h=900&mobile=0&q=high&dpr=1.5"
            else:
                ctx = br.new_context(viewport={'width': 412, 'height': 915}, device_scale_factor=2.625, is_mobile=True, has_touch=True)
                q = "w=412&h=915&mobile=1&q=low&dpr=1.25"
            for rep in range(a.repeat):                      # чередуем наборы (A B C … A B C): шум общей машины ложится на всех поровну
                for item in a.sets.split(';'):
                    b, f = item.split(':')
                    pg = ctx.new_page()
                    errs = []
                    pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
                    pg.goto(f"{base}/{REL}/bench.html?b={b}&f={f}&{q}&ms={a.ms}{'&ik=1' if a.ik else ''}{('&glb=' + a.glb) if a.glb else ''}{('&' + EXTRA) if EXTRA else ''}", wait_until='load')
                    pg.wait_for_function('window.__done === true', timeout=a.ms + 90000)
                    r = pg.evaluate('window.__res')
                    r.update({'mode': mode, 'rep': rep, 'set': item, 'console': errs[:5], 'loadavg': os.getloadavg()[0]})
                    res.append(r)
                    print(json.dumps({k: r.get(k) for k in ('set', 'mode', 'rep', 'frame_med', 'frame_p90', 'frame_ms', 'cpu_med', 'stalls50', 'stall_max', 'calls_story', 'calls_scan', 'tris_story', 'ready_ms', 'first_frame_ms', 'boot_longtask_max', 'programs', 'loadavg')}, ensure_ascii=False))
                    pg.close()
            ctx.close()
        br.close()
    httpd.shutdown()
    old = json.load(open(a.out)) if os.path.exists(a.out) else []
    json.dump(old + res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    return 0


def cmd_sheet(a):
    names = [s for s in a.states.split(',') if s]
    bdir, adir = a.pairs
    tw, th = map(int, a.tile.split('x'))
    gap, head = 6, 34
    W = 2 * tw + gap
    rows = []
    for n in names:
        b = Image.open(os.path.join(bdir, f'{n}.png')).convert('RGB').resize((tw, th), Image.LANCZOS)
        f = Image.open(os.path.join(adir, f'{n}.png')).convert('RGB').resize((tw, th), Image.LANCZOS)
        label(b, f'{a.la} · {n}', 13, (200, 200, 200))
        label(f, f'{a.lb} · {n}', 13, (255, 190, 120))
        rows.append((b, f))
    sheet = Image.new('RGB', (W, head + len(rows) * (th + gap)), (12, 13, 15))
    for i, (b, f) in enumerate(rows):
        sheet.paste(b, (0, head + i * (th + gap))); sheet.paste(f, (tw + gap, head + i * (th + gap)))
    ImageDraw.Draw(sheet).text((10, 9), a.title, font=font(15), fill=(236, 235, 230))
    sheet.save(a.out, quality=88)
    print(a.out, sheet.size, os.path.getsize(a.out))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('frames'); f.add_argument('--b', default='v3'); f.add_argument('--f'); f.add_argument('--out', required=True)
    f.add_argument('--mobile', action='store_true'); f.add_argument('--q'); f.add_argument('--dpr')
    f.add_argument('--states', default='hero,exploded,locking,first-move,scan-half,inside'); f.add_argument('--size', default='960x600')
    f.add_argument('--masks', help='снять и маску объекта: флаги v3 для маски (none — геометрия v2, all — v3)')
    f.add_argument('--glb', help='URL GLB-модулей от корня сервера (гибрид, _shared/code3d), напр. /99-raw/experiments/Z/out/web_lean/j2.glb')
    f.add_argument('--rolemask', help='маски ролей материала через запятую: ring,cap,shell → <state>_<role>.png')
    po = sub.add_parser('posters'); po.add_argument('--out', required=True); po.add_argument('--png')
    po.add_argument('--b', default='v3', help='бандл стенда: v3 (страница A), c3g (общий код с крюком) …'); po.add_argument('--glb', help='URL GLB от корня (постеры C)')
    s = sub.add_parser('shots'); s.add_argument('--out', required=True); s.add_argument('--rm', action='store_true'); s.add_argument('--page', default='a-code')
    s.add_argument('--wait', type=int, default=5000); s.add_argument('--settle', type=int, default=1600)
    b = sub.add_parser('bench'); b.add_argument('--out', required=True); b.add_argument('--sets', required=True)
    b.add_argument('--ms', type=int, default=3000); b.add_argument('--modes', default='desk,mob'); b.add_argument('--repeat', type=int, default=1)
    b.add_argument('--ik', action='store_true'); b.add_argument('--glb')
    sh = sub.add_parser('sheet'); sh.add_argument('--pairs', nargs=2, required=True); sh.add_argument('--out', required=True)
    sh.add_argument('--states', default='hero,exploded,locking,first-move,scan-half,inside'); sh.add_argument('--tile', default='640x400')
    sh.add_argument('--la', default='v2'); sh.add_argument('--lb', default='v3')
    sh.add_argument('--title', default='L2 «Звено» · v2 (J2, свет кодом) → v3 (CD, код на максимуме) · three 0.186.0')
    for sp in (f, po, s, b):
        sp.add_argument('--extra', default='', help='хвост запроса стенда: look=p1&glbOnly=j2&glbMap=j3:j2&glbMat=code')
    a = ap.parse_args()
    global EXTRA
    EXTRA = getattr(a, 'extra', '') or ''
    return {'frames': cmd_frames, 'posters': cmd_posters, 'shots': cmd_shots, 'bench': cmd_bench, 'sheet': cmd_sheet}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
