#!/usr/bin/env python3
"""write_numbers — раздел «b-blender» (дорожка Z) в 15-showcase/zveno/numbers.json: время агента и машины, кадры, числа.
Чужие разделы файла (a-code и др.) не трогает — читает, обновляет только свой ключ, пишет обратно."""
import json
import os
import re
import time

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
F = R + "/15-showcase/zveno/numbers.json"
LOG = "/home/mm/Документы/app-design/.locks/slot_run.log"

runs, wait = {}, 0
for line in open(LOG):
    m = re.search(r"END\s+label=(Z-[\w-]+) exit=(\d+) time=(\d+)s", line)
    if m:
        k = m.group(1).split("-")[1]
        runs.setdefault(k, {"runs": 0, "sec": 0}); runs[k]["runs"] += 1; runs[k]["sec"] += int(m.group(3))
    m = re.search(r"START\s+label=Z-[\w-]+.*waited=(\d+)s", line)
    if m:
        wait += int(m.group(1))


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


hero = {}
for f in ("metrics.json", "metrics_b.json", "metrics_c.json", "metrics_m.json"):
    d = load(f"{Z}/out/hero/{f}") or {}
    for k, r in d.items():
        hero[k] = {"shell_L": r["shell_L"], "hi_obj_pct": round(r["obj"]["hi_obj_pct"], 2),
                   "clip_obj_pct": round(r["obj"]["clip_obj_pct"], 2), "obj_minus_bg_L": round(r["obj"]["obj_minus_bg_L"], 1),
                   "bg_vs_page_dE": round(r["obj"]["bg_vs_page_dE"], 2), "edge_bottom_dE": r["edge_bottom_dE_L"][0],
                   "noise_flat_shell_e3": r["noise_flat_shell_e3"], "noise_bg_e3": r["noise_bg_e3"],
                   "weight_center": [round(x, 3) for x in r["obj"]["weight_center"]],
                   "weight_in_text": round(r["obj"]["weight_in_text"], 3), "obj_area_pct": r["obj_area_pct"]}
web = {}
for d in ("web", "web_lean"):
    b = load(f"{Z}/out/{d}/bake.json")
    m = load(f"{Z}/out/{d}/diff/diff_metrics.json")
    if b:
        web[d] = {"bake": b, "glb_kb": m["glb_kb"] if m else None, "diff_mean": m["mean"] if m else None,
                  "draw_calls": m["draw_calls"] if m else None}
sec = {"b-blender": {
    "track": "Z", "phase": 1, "updated": time.strftime("%Y-%m-%d %H:%M"),
    "agent_time": {"start": "2026-09-25 18:29", "end": time.strftime("%Y-%m-%d %H:%M")},
    "machine_time_s": {k: v for k, v in sorted(runs.items())}, "machine_total_s": sum(v["sec"] for v in runs.values()),
    "queue_wait_s": wait,
    "model": {"render": {"objects": 466, "unique_mesh_tris": 644157, "build_s": "1,6–4,2"},
              "note": "метры scene.js (×≈2,7 к паспорту страницы 900 мм)"},
    "light_study": load(f"{Z}/out/light/metrics.json") and {k: {"shell_L": v["shell_L"], "hi": round(v["obj"]["hi_obj_pct"], 2),
                                                                 "bg_dE": round(v["obj"]["bg_vs_page_dE"], 2)}
                                                             for k, v in load(f"{Z}/out/light/metrics.json").items()},
    "hero": hero, "web_j2": web,
    "frames": {"hero": "judge/b-blender__hero.png", "xray": "judge/b-blender__xray.png"},
}}
cur = load(F) or {}
cur.update(sec)
json.dump(cur, open(F, "w"), ensure_ascii=False, indent=1)
print(json.dumps({"machine_total_s": sec["b-blender"]["machine_total_s"], "queue_wait_s": wait, "runs": runs}, ensure_ascii=False))
