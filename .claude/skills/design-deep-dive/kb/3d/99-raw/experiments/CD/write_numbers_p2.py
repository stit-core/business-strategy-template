#!/usr/bin/env python3
"""CD2 · a-code/numbers.json фазы 2 из файлов прогонов (без браузера): python3 write_numbers_p2.py"""
import glob, json, os, re, subprocess, sys
CD = os.path.dirname(os.path.abspath(__file__)); R = os.path.abspath(os.path.join(CD, '..', '..', '..'))
A = os.path.join(R, '15-showcase', 'zveno', 'a-code'); O = os.path.join(CD, 'out', 'p2')
J = lambda p: json.load(open(p)) if os.path.exists(p) else None
old = J(os.path.join(A, 'numbers.json')) or {}
phase1 = old.get('phase1') or {k: v for k, v in old.items() if k not in ('phase1',)}
# время машины: журнал очереди, метки CD2-*
runs, t_run, t_wait = 0, 0, 0
for line in open('/home/mm/Документы/app-design/.locks/slot_run.log', encoding='utf-8', errors='replace'):
    m = re.search(r'START label=(CD2-\S+) .* waited=(\d+)s', line)
    if m: runs += 1; t_wait += int(m.group(2))
    m = re.search(r'END   label=(CD2-\S+) exit=\d+ time=(\d+)s', line)
    if m: t_run += int(m.group(2))
kb = J(os.path.join(CD, 'out', 'kb.json')) or {}
full = kb.get('full', {})
per = {k.replace('no-', ''): round(full.get('desktop_kb_br', 0) - v.get('desktop_kb_br', 0), 1) for k, v in kb.items() if k.startswith('no-')}
def frames_log(d):
    out = {}
    p = os.path.join(O, d, 'frames.log')
    if os.path.exists(p):
        for l in open(p):
            if l.startswith('{'):
                r = json.loads(l); out[r['state']] = {k: r.get(k) for k in ('calls', 'tris', 'programs')}
    return out
def metr(p):
    j = J(p); return None if not j else {k: (round(j[k], 3) if isinstance(j[k], float) else j[k]) for k in ('bg_vs_page_dE', 'hi_obj_pct', 'clip_obj_pct', 'crush_obj_pct', 'obj_minus_bg_L', 'weight_in_text', 'weight_on_obj') if k in j}
def sub(cmd):
    try: return json.loads(subprocess.check_output(cmd, text=True).strip().splitlines()[-1])
    except Exception as e: return {'error': str(e)[:100]}
L = os.path.join(O, 'look'); pm = os.path.join(CD, 'p2_metrics.py')
look = {'flash_blob_p1': sub(['python3', pm, 'blob', f'{L}/p1/lock-flash.png', f'{L}/p1-noflash/lock-flash.png']),
        'flash_blob_p2': sub(['python3', pm, 'blob', f'{L}/p2b/lock-flash.png', f'{L}/p2b-noflash/lock-flash.png']),
        'ring_hero_p1': sub(['python3', pm, 'role', f'{L}/p1-roles/hero.png', f'{L}/p1-roles/hero_ring.png']),
        'ring_hero_p2': sub(['python3', pm, 'role', f'{L}/p2b-roles/hero.png', f'{L}/p2b-roles/hero_ring.png']),
        'cap_hero_p1': sub(['python3', pm, 'role', f'{L}/p1-roles/hero.png', f'{L}/p1-roles/hero_cap.png', '--hex', '4b5058']),
        'cap_hero_p2': sub(['python3', pm, 'role', f'{L}/p2b-roles/hero.png', f'{L}/p2b-roles/hero_cap.png', '--hex', '4b5058'])}
for k, v in look.items():
    if isinstance(v, dict): v.pop('frame', None); v.pop('flash', None)
bench = J(os.path.join(O, 'q', 'summary.json')); bench_p1 = J(os.path.join(O, 'bench-q-summary.json'))
gates = {}
for d in sorted(glob.glob(os.path.join(O, 'gates', '*'))):
    if not os.path.isdir(d): continue
    f = (glob.glob(os.path.join(d, 'probe*.json')) or [None])[0]
    if not f: continue
    j = J(f); v = j.get('vitals_pre_scroll', {}); n = j.get('network', {})
    prof = 'mobile' if j.get('mobile') else 'desktop'
    gc = subprocess.run(['python3', os.path.join(R, '99-raw', 'tools', 'gate_check.py'), f, prof] + (['--reduced'] if j.get('reduced_motion') else []), capture_output=True, text=True).stdout
    gates[os.path.basename(d)] = {'lcp_ms': (v.get('lcp') or {}).get('t'), 'lcp_el': (v.get('lcp') or {}).get('tag'), 'first_frame_3d_ms': (re.findall(r'firstFrame[^0-9]*(\d+)', json.dumps(j.get('console', []))) or [None])[0], 'tbt_ms': v.get('tbt_ms'), 'longest_task_ms': v.get('longest_task_ms'),
        'cls': v.get('cls'), 'transfer_kb': n.get('transfer_kb'), 'console_errors': j.get('console_errors'), 'idle_dc_max': j.get('idle', {}).get('dc_max'),
        'idle_motion_pct': j.get('idle_motion_pct'), 'fail': gc.count('FAIL'), 'gate_lines': [l for l in gc.splitlines() if l.startswith(('FAIL', 'WARN'))][:6]}
mo = J(os.path.join(O, 'motion-l2', 'gates.json')); mk = J(os.path.join(O, 'mkt', 'zveno-a-code.marketing.json'))
fv = frames_log('f-v3'); fm = frames_log('f-v3-mob')
new = {
 'variant': 'a-code', 'title': '«Звено» A — код v3 (дорожка CD)', 'phase': 2, 'date': '2026-09-25', 'look': 'p2',
 'stack': phase1.get('stack'), 'source': '15-showcase/_shared/code3d/src/ (общий код A и C); фаза 1 — 99-raw/experiments/CD/src/scene-v3p1.js',
 'time': {'agent_clock_phase2': '20:15–(см. NOTES)', 'machine_browser_runs_phase2': runs, 'machine_browser_s_phase2': t_run, 'queue_wait_s_phase2': t_wait,
          'machine_blender_s': 0, 'phase1': phase1.get('time')},
 'weight_kb_br': {'method': 'brotli q11 по файлам сборки (out/kb.json)', 'desktop_total': full.get('desktop_kb_br'), 'mobile_total': full.get('mobile_kb_br'),
                  'files': full.get('files'), 'per_technique_desktop': per, 'hybrid_build': (J(os.path.join(O, 'kb-hook.json')) or {}).get('c3-glb'),
                  'phase1_same_method': (J(os.path.join(O, 'kb-hook.json')) or {}).get('v3p1-ref'), 'assets_3d_kb': 0},
 'frame_ms_quiet_phase2': bench, 'frame_ms_quiet_phase1_code': bench_p1,
 'draw_calls_desktop': fv, 'draw_calls_mobile': fm,
 'img_metrics_hero': {'p1': metr(os.path.join(O, 'metrics-hero-p1.json')), 'p2': metr(os.path.join(O, 'metrics-hero-p2.json'))},
 'look_p2_vs_p1': look,
 'gates_site_probe_quiet': gates,
 'motion_check_L2': mo if not isinstance(mo, dict) else {k: mo.get(k) for k in list(mo)[:12]},
 'marketing_audit': None if not mk else {k: mk.get(k) for k in ('level', 'summary', 'counts', 'verdict') if k in mk},
 'hybrid_hook': {'path': '15-showcase/_shared/code3d/', 'test_glb': '99-raw/experiments/Z/out/web_lean/j2.glb', 'frames': 'out/p2/hy2-*',
                 'sheet': '99-raw/experiments/CD/sheet-hook-glb.jpg', 'hero_calls_tris_programs': frames_log('hy2-1600').get('hero')},
 'experiments': {'ao': J(os.path.join(O, 'ao', 'summary.json')), 'ao_weights_kb_br': J(os.path.join(CD, 'ao', 'weights.json')),
                 'tsl': J(os.path.join(O, 'tsl', 'summary.json')), 'tsl_weights': open(os.path.join(CD, 'tsl', 'weights.txt')).read().strip() if os.path.exists(os.path.join(CD, 'tsl', 'weights.txt')) else None},
 'files': {'sheets': ['99-raw/experiments/CD/pairs-p1-p2-desk.jpg', '99-raw/experiments/CD/sheet-hook-glb.jpg', '99-raw/experiments/CD/judge-pair-hero.jpg',
                      '99-raw/experiments/CD/judge-pair-hero-ik.jpg', '99-raw/experiments/CD/out/p2/look/sheet-ik5.jpg', '99-raw/experiments/CD/out/p2/page-ik-p1-p2.jpg'],
           'judge': ['15-showcase/zveno/judge/a-code__' + s + '.png' for s in ('hero', 'hero-ik', 'exploded', 'locking', 'first-move', 'scan-half', 'inside')]},
 'phase1': phase1,
}
json.dump(new, open(os.path.join(A, 'numbers.json'), 'w'), ensure_ascii=False, indent=1)
print('numbers.json:', os.path.getsize(os.path.join(A, 'numbers.json')), 'байт; прогонов CD2', runs, 'время', t_run, 'с, ожидание', t_wait, 'с; ворота', {k: v['fail'] for k, v in gates.items()})
