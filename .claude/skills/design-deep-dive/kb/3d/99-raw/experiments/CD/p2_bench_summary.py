#!/usr/bin/env python3
"""CD2 · сводка бенча: python3 p2_bench_summary.py FILE.json [FILE.json …] [--out summary.json]
Медиана по повторам от медианы длительности кадров (frame_med), p90, зависания > 50 мс, CPU, вызовы, первый кадр, load average."""
import json, statistics as st, sys
files = [a for a in sys.argv[1:] if a.endswith('.json') and not a.startswith('--')]
out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
rows = {}
for fn in files:
    if out and fn == out: continue
    for r in json.load(open(fn)):
        rows.setdefault((r['mode'], r['set']), []).append(r)
res = {}
for (mode, s), rs in rows.items():
    fm = [r.get('frame_med') for r in rs if r.get('frame_med') is not None] or [r['frame_ms'] for r in rs]
    res[f'{mode}|{s}'] = {'n': len(rs), 'frame_med': round(st.median(fm), 3), 'frame_med_min': round(min(fm), 3), 'frame_med_max': round(max(fm), 3),
        'frame_p90': round(st.median([r.get('frame_p90') or 0 for r in rs]), 3), 'mean_el_n': round(st.median([r['frame_ms'] for r in rs]), 2),
        'cpu_med': round(st.median([r.get('cpu_med') or r['cpu_ms'] for r in rs]), 3), 'stalls50': sum(r.get('stalls50') or 0 for r in rs),
        'stall_max': max(r.get('stall_max') or 0 for r in rs), 'calls_story': rs[0].get('calls_story'), 'calls_scan': rs[0].get('calls_scan'),
        'tris_story': rs[0].get('tris_story'), 'programs': rs[0].get('programs'), 'first_frame_ms': round(st.median([r['first_frame_ms'] for r in rs])),
        'ready_ms': round(st.median([r['ready_ms'] for r in rs])), 'load': round(st.median([r['loadavg'] for r in rs]), 1),
        'console': sorted({c for r in rs for c in r.get('console', [])})[:3]}
for k, v in res.items():
    print(f"{k:22s} кадр {v['frame_med']:6.3f} [{v['frame_med_min']}–{v['frame_med_max']}] p90 {v['frame_p90']:6.3f} (el/n {v['mean_el_n']}) cpu {v['cpu_med']:5.3f} "
          f"зав. {v['stalls50']} (max {v['stall_max']}) вызовы {v['calls_story']}/{v['calls_scan']} 1-й кадр {v['first_frame_ms']} load {v['load']} {v['console'] or ''}")
if out: json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
