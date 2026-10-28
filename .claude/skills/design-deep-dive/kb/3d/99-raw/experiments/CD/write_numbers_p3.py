#!/usr/bin/env python3
"""CD3 · a-code/numbers.json фазы 3 из файлов прогонов (без браузера): python3 write_numbers_p3.py [--agent-end ЧЧ:ММ]
Фазы 1–2 сохраняются вложенными блоками (phase1, phase2); верхний уровень — фаза 3 (вид p3, крюк v2, приёмы 8/10, ворота в тишине)."""
import glob, json, os, re, subprocess, sys
import brotli
CD = os.path.dirname(os.path.abspath(__file__)); R = os.path.abspath(os.path.join(CD, '..', '..', '..'))
A = os.path.join(R, '15-showcase', 'zveno', 'a-code'); O = os.path.join(CD, 'out', 'cd3')
J = lambda p: json.load(open(p)) if os.path.exists(p) else None
end = sys.argv[sys.argv.index('--agent-end') + 1] if '--agent-end' in sys.argv else None
old = J(os.path.join(A, 'numbers.json')) or {}
phase1 = old.get('phase1')
phase2 = old.get('phase2') or {k: v for k, v in old.items() if k not in ('phase1',)}
if old.get('phase') == 3:                                            # повторный запуск: блоки фаз 1–2 уже вложены
    phase2 = old.get('phase2')
# время машины: журнал очереди, метки CD3-*
runs, t_run, t_wait, heavy = 0, 0, 0, 0
for line in open('/home/mm/Документы/app-design/.locks/slot_run.log', encoding='utf-8', errors='replace'):
    m = re.search(r'START label=(CD3-\S+) .*heavy=(\d) waited=(\d+)s', line)
    if m: runs += 1; t_wait += int(m.group(3)); heavy += int(m.group(2))
    m = re.search(r'END   label=(CD3-\S+) exit=\d+ time=(\d+)s', line)
    if m: t_run += int(m.group(2))
# вес страницы A (сборка фазы 3): по файлам js/ (brotli q11)
files = {}
for f in sorted(glob.glob(os.path.join(A, 'js', '**', '*.js'), recursive=True)):
    b = open(f, 'rb').read(); files[os.path.relpath(f, os.path.join(A, 'js'))] = round(len(brotli.compress(b, quality=11)) / 1024, 2)
scene = sum(v for k, v in files.items() if k == 'three-scene.js' or k.startswith('chunks/'))
post = sum(v for k, v in files.items() if 'post-' in k)
def frames_log(p):
    out = {}
    if os.path.exists(p):
        for l in open(p):
            if l.startswith('{'):
                r = json.loads(l); out[r['state']] = {k: r.get(k) for k in ('calls', 'tris', 'programs')}
    return out
def metr(p):
    j = J(p); return None if not j else {k: (round(j[k], 3) if isinstance(j[k], float) else j[k]) for k in ('bg_vs_page_dE', 'hi_obj_pct', 'clip_obj_pct', 'obj_minus_bg_L', 'weight_in_text', 'weight_on_obj') if k in j}
gates = {}
GD = 'gates2' if os.path.isdir(os.path.join(O, 'gates2')) else 'gates'      # gates2 — перепрогон после итерации №2 (телефонный ореол)
for d in sorted(glob.glob(os.path.join(O, GD, '*'))):
    if not os.path.isdir(d) or os.path.basename(d) == 'motion-l2': continue
    f = (glob.glob(os.path.join(d, 'probe*.json')) or [None])[0]
    if not f: continue
    j = J(f); v = j.get('vitals_pre_scroll', {}); n = j.get('network', {})
    gt = os.path.join(O, GD, os.path.basename(d) + '.gate.txt'); gc = open(gt).read() if os.path.exists(gt) else ''
    gates[os.path.basename(d)] = {'lcp_ms': (v.get('lcp') or {}).get('t'), 'lcp_el': (v.get('lcp') or {}).get('tag'), 'tbt_ms': v.get('tbt_ms'),
        'longest_task_ms': v.get('longest_task_ms'), 'cls': v.get('cls'), 'transfer_kb': n.get('transfer_kb'), 'console_errors': j.get('console_errors'),
        'first_frame_3d_ms': (re.findall(r'firstFrame[^0-9]*(\d+)', json.dumps(j.get('console', []))) or [None])[0],
        'idle_dc_max': j.get('idle', {}).get('dc_max'), 'idle_motion_pct': j.get('idle_motion_pct'), 'fail': gc.count('FAIL')}
def motion(p):
    j = J(p)
    if not j: return None
    res = j.get('summary') or {k: j.get(k) for k in ('fail_B', 'fail_S', 'fail_D', 'na', 'spec_fail') if k in j}
    return res or {k: j[k] for k in list(j)[:8]}
def motion_sum(logp):
    if not os.path.exists(logp): return None
    for l in reversed(open(logp).read().splitlines()):
        if l.startswith('{'): return json.loads(l)
    return None
fin = os.path.join(O, 'final', 'f-v3')
new = {
 'variant': 'a-code', 'title': '«Звено» A — код v3 (дорожка CD)', 'phase': 3, 'date': '2026-09-26', 'look': 'p3',
 'look_note': 'p3 = p2 + приём 8 «контровой свет в дымке» (десктоп, пост) + приём 10 «след инструмента» (IK, первое движение); main.js: look: "p3"',
 'stack': (phase1 or {}).get('stack'), 'source': '15-showcase/_shared/code3d/src/ (общий код A и C)',
 'time': {'agent_clock_phase3': '00:05–' + (end or '…'), 'machine_browser_runs_phase3': runs, 'heavy_runs_phase3': heavy,
          'machine_browser_s_phase3': t_run, 'queue_wait_s_phase3': t_wait, 'machine_blender_s': 0,
          'phase2': (phase2 or {}).get('time'), 'phase1': (phase1 or {}).get('time')},
 'weight_kb_br': {'method': 'brotli q11 по файлам a-code/js (сборка 26.09 01:36)', 'files': files, 'desktop_3d': round(scene, 2), 'mobile_3d': round(scene - post, 2),
                  'techniques_8_10': 2.3, 'assets_3d_kb': 0, 'phase2_same_method': [231.2, 134.3]},
 'frame_ms_quiet_phase3': {k: J(os.path.join(O, 'q', f'summary-{k}.json')) for k in ('q-desk', 'q-desk-ik', 'q-mob')},
 'draw_calls_desktop_p3': frames_log(os.path.join(fin, 'frames.log')), 'draw_calls_mobile_p3': frames_log(os.path.join(O, 'final', 'f-v3-mob', 'frames.log')),
 'img_metrics_p3': {s: metr(os.path.join(fin, f'{s}_m.json')) for s in ('hero', 'hero-ik', 'exploded', 'locking', 'first-move', 'scan-half', 'inside')},
 'img_metrics_p2_same_run': {s: metr(os.path.join(O, 'f-p2c', f'{s}_m.json')) for s in ('hero', 'exploded', 'first-move')},
 'gates_site_probe_quiet_p3': gates,
 'gates_dir': GD,
 'motion_check_L2': {'p3_final': motion_sum(os.path.join(O, GD, 'motion-l2.log')), 'p3_01_52': motion_sum(os.path.join(O, 'gates', 'motion-l2.log')), 'p2_00_54': motion_sum(os.path.join(O, 'motion-l2-a.log'))},
 'marketing_audit_L2_00_54': {'blockers': 0, 'serious': 0, 'polish': 65, 'report': '99-raw/experiments/CD/out/cd3/mkt-a/zveno-a-code.marketing.md'},
 'experiments_phase3': {'ao_tsl': J(os.path.join(O, 'ao_tsl_summary.json')), 'hook_v2': J(os.path.join(CD, 'out', 'hook2', 'q', 'summary.json'))},
 'files': {'sheets': ['99-raw/experiments/CD/out/cd3/pairs-judge-p2-p3.jpg', '99-raw/experiments/CD/out/cd3/pairs-p2-p3b.jpg', '99-raw/experiments/CD/out/cd3/abc_judge.jpg',
                      '99-raw/experiments/CD/out/cd3/ao_sheet.jpg', '99-raw/experiments/CD/out/cd3/tsl_sheet.jpg', '99-raw/experiments/CD/out/cd3/sweep/sheet3.jpg',
                      '99-raw/experiments/CD/out/cd3/final/trail-1600/hero.png'],
           'judge': ['15-showcase/zveno/judge/a-code__' + s + '.png' for s in ('hero', 'hero-ik', 'exploded', 'locking', 'first-move', 'scan-half', 'inside')]},
 'phase2': phase2, 'phase1': phase1,
}
json.dump(new, open(os.path.join(A, 'numbers.json'), 'w'), ensure_ascii=False, indent=1)
print('numbers.json:', os.path.getsize(os.path.join(A, 'numbers.json')), 'байт; прогонов CD3', runs, '(тяжёлых', heavy, ') время', t_run, 'с, ожидание', t_wait,
      'с; вес', round(scene, 1), '/', round(scene - post, 1), 'КБ br; ворота', {k: v['fail'] for k, v in gates.items()})
