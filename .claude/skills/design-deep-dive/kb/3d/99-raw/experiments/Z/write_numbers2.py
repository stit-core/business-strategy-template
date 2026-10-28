#!/usr/bin/env python3
"""write_numbers2 — фаза 2 дорожки Z2 в 15-showcase/zveno/numbers.json: разделы «b-blender» (дополняет фазу 1 ключом phase2) и
«c-hybrid». Чужие разделы не трогает. Источники: журнал очереди (.locks/slot_run.log, метки Z2-*), логи zseq (время кадра, VmHWM),
вес поставки B (out/seq/weights.json), GLB C (zweb_all *_bake.json, gltf_check), ворота (out/gates/<страница>/…), motion_check."""
import glob
import json
import os
import re
import time

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
F = R + "/15-showcase/zveno/numbers.json"
LOG = "/home/mm/Документы/app-design/.locks/slot_run.log"


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


runs, wait = {}, 0
for line in open(LOG):
    m = re.search(r"END\s+label=(Z2-[\w-]+) exit=(\d+) time=(\d+)s", line)
    if m:
        k = m.group(1)
        runs.setdefault(k, {"runs": 0, "sec": 0}); runs[k]["runs"] += 1; runs[k]["sec"] += int(m.group(3))
    m = re.search(r"START\s+label=Z2-[\w-]+.*waited=(\d+)s", line)
    if m:
        wait += int(m.group(1))

frames = {}
for p in glob.glob(Z + "/out/seq/*/log_*.json") + glob.glob(Z + "/out/judge/log_*.json"):
    d = load(p) or {}
    key = os.path.basename(os.path.dirname(p))
    fr = d.get("frames", [])
    if fr:
        e = frames.setdefault(key, {"frames": 0, "sec": 0.0, "vmhwm_mb": 0})
        e["frames"] += len(fr); e["sec"] += sum(f["sec"] for f in fr); e["vmhwm_mb"] = max(e["vmhwm_mb"], d.get("vmhwm_mb") or 0)
for e in frames.values():
    e["sec_per_frame"] = round(e["sec"] / max(1, e["frames"]), 1); e["sec"] = round(e["sec"], 1)


def gates(tag):
    out = {}
    for g in ("desk", "mob", "rm"):
        p = f"{Z}/out/gates/{tag}/gate_{g}.txt"
        if os.path.exists(p):
            rows = [l.strip() for l in open(p) if l.strip()]
            out[g] = {"fail": sum(r.startswith("FAIL") for r in rows), "rows": rows}
    lt = f"{Z}/out/gates/{tag}/load.txt"
    if os.path.exists(lt):
        out["load"] = [l.strip() for l in open(lt) if l.startswith("load")]
    return out


def glb_stats(d, name):
    b = load(f"{Z}/out/{d}/{name}_bake.json") or {}
    return {k: b.get(k) for k in ("tris_total", "tris_inner", "draw_calls_est", "size", "bake_ao_s", "glb_raw_kb")}


cur = load(F) or {}
b = cur.get("b-blender", {})
b["phase2"] = {
    "track": "Z2", "updated": time.strftime("%Y-%m-%d %H:%M"),
    "agent_time": {"start": "2026-09-25 20:17", "end": time.strftime("%Y-%m-%d %H:%M")},
    "engine": "Cycles CPU (20 потоков) + OIDN; секвенции 40 спп --fast, кадры судьи 128 спп; EEVEE отклонён (out/engine)",
    "frames": frames, "weights": load(Z + "/out/seq/weights.json"),
    "gates": gates("b-blender"), "motion_check": load(Z + "/out/motion_b/summary.json"),
}
cur["b-blender"] = b
cur["c-hybrid"] = {
    "track": "Z2 (ассет) + CD2 (крюк _shared/code3d)", "updated": time.strftime("%Y-%m-%d %H:%M"),
    "glb": {"desktop": {**glb_stats("c_web", "zveno"), "kb": round(os.path.getsize(R + "/15-showcase/zveno/c-hybrid/assets/zveno.glb") / 1024, 1)
                        if os.path.exists(R + "/15-showcase/zveno/c-hybrid/assets/zveno.glb") else None},
            "phone": {**glb_stats("c_webl", "zveno-low"), "kb": round(os.path.getsize(R + "/15-showcase/zveno/c-hybrid/assets/zveno-low.glb") / 1024, 1)
                      if os.path.exists(R + "/15-showcase/zveno/c-hybrid/assets/zveno-low.glb") else None},
            "ktx2_desktop_kb": round(os.path.getsize(Z + "/out/c_web/zveno_ktx2.glb") / 1024, 1) if os.path.exists(Z + "/out/c_web/zveno_ktx2.glb") else None},
    "diff": (load(Z + "/out/c_web/diff/diff_metrics.json") or {}).get("mean"),
    "gates": gates("c-hybrid"), "motion_check": load(Z + "/out/motion_c/summary.json"),
}
cur["z2_machine"] = {"runs": runs, "machine_total_s": sum(v["sec"] for v in runs.values()), "queue_wait_s": wait}
json.dump(cur, open(F, "w"), ensure_ascii=False, indent=1)
print(json.dumps({"machine_total_s": cur["z2_machine"]["machine_total_s"], "queue_wait_s": wait, "frames": frames}, ensure_ascii=False)[:1500])
