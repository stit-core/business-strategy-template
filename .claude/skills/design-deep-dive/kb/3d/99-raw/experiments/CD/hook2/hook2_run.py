#!/usr/bin/env python3
"""CD3 · крюк v2 (_shared/code3d): замер KTX2 против WebP и начинки отдельным GLB (innerUrl) на GLB дорожки Z.

  python3 hook2_run.py prep                       # копия стенда в scratchpad/h2serve (бандлы c3g/c3k, GLB) + brotli q11 (без браузера)
  python3 slot_run.py --kind browser --heavy --label CD3-hook2 -- python3 hook2_run.py run OUT_DIR [--repeat 3]
Раздача — serve_br.py «как хостинг» (br, no-store: каждый прогон холодный) на порту 8782 (порт CD); Chromium headless, ANGLE GL.
Выход: OUT_DIR/runs.json (все прогоны), OUT_DIR/summary.json (медианы по варианту), кадры «внутри» (scan) для глаз.
"""
import json, os, shutil, statistics, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.dirname(HERE)
R = os.path.abspath(os.path.join(CD, '..', '..', '..'))
C3 = os.path.join(R, '15-showcase', '_shared', 'code3d')
Z = os.path.join(R, '99-raw', 'experiments', 'Z')
SERVE = '/tmp/claude-1000/-home-mm-----------app-design/d8f53347-66a5-40ec-a709-75f4623c7b47/scratchpad/h2serve'
sys.path.insert(0, os.path.join(R, '99-raw', 'experiments', 'F1', '02-hero-variants'))
PORT = 8782
GPU_ARGS = ['--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist', '--enable-gpu']
GLBS = {
    'zveno.glb': os.path.join(R, '15-showcase/zveno/c-hybrid/assets/zveno.glb'),
    'zveno-low.glb': os.path.join(R, '15-showcase/zveno/c-hybrid/assets/zveno-low.glb'),
    'zveno_ktx2.glb': os.path.join(Z, 'out/c_web/zveno_ktx2.glb'),
    'zveno_main.glb': os.path.join(CD, 'out/hook2/glb/zveno_main.glb'),
    'zveno_inner.glb': os.path.join(CD, 'out/hook2/glb/zveno_inner.glb'),
    'zveno_inner_noao.glb': os.path.join(CD, 'out/hook2/glb/zveno_inner_noao.glb'),
    'zveno-low_main.glb': os.path.join(CD, 'out/hook2/glb/zveno-low_main.glb'),
    'zveno-low_inner_noao.glb': os.path.join(CD, 'out/hook2/glb/zveno-low_inner_noao.glb'),
    'zveno_inner_noao_scenenamed.glb': os.path.join(CD, 'out/hook2/glb/zveno_inner_noao_scenenamed.glb'),   # сцена «inner» — ловушка поиска начинки
}
# вариант → (бандл, режим, запрос)
VARIANTS = [
    ('webp', 'c3g', 'desk', 'glb=glb/zveno.glb'),
    ('ktx2', 'c3k', 'desk', 'glb=glb/zveno_ktx2.glb'),
    ('ktx2-pre', 'c3k', 'desk', 'glb=glb/zveno_ktx2.glb&ktx2=1'),
    ('split', 'c3g', 'desk', 'glb=glb/zveno_main.glb&inner=glb/zveno_inner_noao.glb'),
    ('split-ao', 'c3g', 'desk', 'glb=glb/zveno_main.glb&inner=glb/zveno_inner.glb'),
    ('webp-low', 'c3g', 'mob', 'glb=glb/zveno-low.glb'),
    ('split-low', 'c3g', 'mob', 'glb=glb/zveno-low_main.glb&inner=glb/zveno-low_inner_noao.glb'),
]


def prep():
    if os.path.isdir(SERVE):
        shutil.rmtree(SERVE)
    os.makedirs(os.path.join(SERVE, 'glb'))
    shutil.copy(os.path.join(HERE, 'hook2.html'), SERVE); shutil.copy(os.path.join(HERE, 'dbg_inner.html'), SERVE)
    for b, flag in (('c3g', '--glb'), ('c3k', '--ktx2')):
        subprocess.run([os.path.join(C3, 'build.sh'), os.path.join(SERVE, 'b', b), flag], check=True, stdout=subprocess.DEVNULL)
    for n, p in GLBS.items():
        shutil.copy(p, os.path.join(SERVE, 'glb', n))
    from serve_br import precompress
    t = time.time(); n = precompress(SERVE)
    print(f'prep: {SERVE}, сжато {n} файлов за {time.time() - t:.1f} с')


def cat(n):
    if '/basis/' in n:
        return 'basis'
    if n.endswith('.glb'):
        return 'inner_glb' if 'inner' in n else 'glb'
    if 'ktx2-' in n:
        return 'ktx2_chunk'
    if 'glb-modules' in n:
        return 'glb_chunk'
    if n.endswith('.js'):
        return 'js'
    return 'other'


def run(out, repeat):
    from playwright.sync_api import sync_playwright
    from serve_br import start
    os.makedirs(out, exist_ok=True)
    httpd = start(SERVE, PORT)
    base = f'http://127.0.0.1:{PORT}'
    runs = []
    with sync_playwright() as p:
        br = p.chromium.launch(args=GPU_ARGS)
        w = br.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1.5).new_page()   # прогрев браузера и GPU-процесса
        w.goto(f'{base}/hook2.html?b=c3g&glb=glb/zveno.glb&w=1440&h=900&mobile=0&dpr=1.5', wait_until='load'); w.wait_for_function('window.__done === true', timeout=60000); w.context.close()
        for rep in range(repeat):
            for name, b, mode, qs in VARIANTS:
                if mode == 'desk':
                    ctx = br.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1.5)
                    tail = 'w=1440&h=900&mobile=0&dpr=1.5'
                else:
                    ctx = br.new_context(viewport={'width': 412, 'height': 915}, device_scale_factor=2.625, is_mobile=True, has_touch=True)
                    tail = 'w=412&h=915&mobile=1&dpr=1.25'
                pg = ctx.new_page()
                log = []
                pg.on('console', lambda m: log.append(f'{m.type}: {m.text}'))
                pg.on('pageerror', lambda e: log.append(f'pageerror: {e}'))
                t0 = time.time()
                pg.goto(f'{base}/hook2.html?b={b}&{qs}&{tail}&scan=1', wait_until='load')
                pg.wait_for_function('window.__done === true', timeout=60000)
                r = pg.evaluate('window.__res')
                if rep == 0:
                    pg.screenshot(path=os.path.join(out, f'{name}_inside.png'))
                by = {}
                for e in r['res']:
                    c = cat(e['n']); d = by.setdefault(c, {'tr': 0, 'dec': 0, 'end': 0})
                    d['tr'] += e['tr'] or 0; d['dec'] += e['dec'] or 0; d['end'] = max(d['end'], e['end'])
                r.update({'variant': name, 'rep': rep, 'mode': mode, 'by': by, 'console': log[:12], 'wall_s': round(time.time() - t0, 2),
                          'loadavg': os.getloadavg()[0]})
                del r['res']
                runs.append(r)
                g = r['stats'].get('glb') or {}
                gi = r['stats'].get('glbInner') or {}
                print(json.dumps({'v': name, 'rep': rep, 'ready': r['T']['ready'], 'first_gpu': r['T']['first_gpu'], 'inner': r['T'].get('inner'),
                                  'scan_ms': r['T'].get('scan_frame_ms'), 'tex_MB': round(r['tex_bytes'] / 1048576, 2), 'tbt': r['tbt'], 'lt_max': r['lt_max'],
                                  'glb_kb': round(by.get('glb', {}).get('tr', 0) / 1024, 1), 'inner_kb': round(by.get('inner_glb', {}).get('tr', 0) / 1024, 1),
                                  'basis_kb': round(by.get('basis', {}).get('tr', 0) / 1024, 1), 'load': g.get('load'), 'innerInfo': {k: gi.get(k) for k in ('bytes', 'fetch_ms', 'parse_ms', 'total_ms', 'tris', 'error')},
                                  'err': [l for l in log if 'error' in l.lower()][:3], 'la': round(r['loadavg'], 1)}, ensure_ascii=False))
                ctx.close()
        br.close()
    httpd.shutdown()
    json.dump(runs, open(os.path.join(out, 'runs.json'), 'w'), ensure_ascii=False, indent=1)
    summ = {}
    for name, *_ in VARIANTS:
        rs = [r for r in runs if r['variant'] == name]
        med = lambda f: statistics.median([f(r) for r in rs]) if rs else None
        summ[name] = {
            'n': len(rs), 'ready_ms': med(lambda r: r['T']['ready']), 'first_frame_gpu_ms': med(lambda r: r['T']['first_gpu']),
            'inner_ms': med(lambda r: r['T'].get('inner') or 0), 'scan_frame_ms': med(lambda r: r['T'].get('scan_frame_ms') or 0),
            'tbt_ms': med(lambda r: r['tbt']), 'longtask_max_ms': med(lambda r: r['lt_max']),
            'tex_gpu_MB': round(med(lambda r: r['tex_bytes']) / 1048576, 2),
            'transfer_kb': {c: round(med(lambda r, c=c: r['by'].get(c, {}).get('tr', 0)) / 1024, 1) for c in ('glb', 'inner_glb', 'basis', 'ktx2_chunk', 'glb_chunk', 'js')},
            'glb_parse_ms': med(lambda r: ((r['stats'].get('glb') or {}).get('load') or {}).get('parse_ms') or 0),
            'glb_fetch_ms': med(lambda r: ((r['stats'].get('glb') or {}).get('load') or {}).get('fetch_ms') or 0),
            'heap_MB': med(lambda r: r['heap'] or 0), 'calls': rs[0]['first_stats']['calls'] if rs else None, 'tris': rs[0]['first_stats']['tris'] if rs else None,
            'tex': rs[0]['tex'] if rs else None, 'ext': rs[0]['ext'] if rs else None, 'gpu': rs[0]['gpu'] if rs else None,
            'loadavg': [round(r['loadavg'], 1) for r in rs],
        }
    json.dump(summ, open(os.path.join(out, 'summary.json'), 'w'), ensure_ascii=False, indent=1)
    for k, v in summ.items():
        print(k, {kk: v[kk] for kk in ('ready_ms', 'first_frame_gpu_ms', 'inner_ms', 'scan_frame_ms', 'tbt_ms', 'longtask_max_ms', 'tex_gpu_MB', 'transfer_kb', 'glb_parse_ms')})


if __name__ == '__main__':
    if sys.argv[1] == 'prep':
        prep()
    else:
        rep = int(sys.argv[sys.argv.index('--repeat') + 1]) if '--repeat' in sys.argv else 3
        run(sys.argv[2], rep)
