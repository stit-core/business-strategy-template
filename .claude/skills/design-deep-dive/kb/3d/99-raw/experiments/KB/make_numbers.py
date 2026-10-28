#!/usr/bin/env python3
"""make_numbers.py — собрать 15-showcase/keyboard/numbers.json из отчётов опытов KB (время агента и машины, метрики, веса)."""
import json
import os
import re
import time
from collections import defaultdict

K = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(K, "../../../15-showcase/keyboard/numbers.json"))
LOG = "/home/mm/Документы/app-design/.locks/slot_run.log"


def jl(p):
    p = os.path.join(K, p)
    return json.load(open(p)) if os.path.exists(p) else None


def pick(m):
    if not m:
        return None
    keys = ("obj_L", "clip_obj_pct", "hi_obj_pct", "bg_L", "obj_minus_bg_L", "bg_vs_page_dE", "noise_e3", "noise_bg_e3",
            "weight_center", "weight_on_obj", "weight_in_text", "obj_share")
    out = {}
    for k in keys:
        v = m.get(k)
        if isinstance(v, dict):
            v = {kk: round(vv, 1) for kk, vv in v.items() if vv is not None}
        elif isinstance(v, list):
            v = [round(x, 3) for x in v]
        elif isinstance(v, float):
            v = round(v, 2)
        out[k] = v
    return out


def queue():
    st, tot, wait, n = {}, defaultdict(float), 0, 0
    for line in open(LOG, encoding="utf-8"):
        m = re.search(r"pid=(\d+) (START|END)\s+label=(\S+)", line)
        if not m or not m.group(3).startswith("KB"):
            continue
        pid, ev, lab = m.groups()
        if ev == "START":
            w = re.search(r"waited=(\d+)s", line)
            wait += int(w.group(1)) if w else 0
            n += 1
            st[pid] = ("heavy" if "heavy=1" in line else re.search(r"kind=(\S+)", line).group(1))
        else:
            t = re.search(r"time=(\d+)s", line)
            if pid in st and t:
                tot[st[pid]] += int(t.group(1))
    return {"runs": n, "queue_wait_s": wait, "machine_s": dict(tot), "machine_total_s": sum(tot.values())}


def keytop(frame, pts):
    import subprocess
    import sys
    r = subprocess.run([sys.executable, os.path.join(K, "_lib/kbtop.py"), os.path.join(K, frame), os.path.join(K, pts), "KC_alpha"],
                       capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


N = {"subject": "keyboard «Ё»", "lane": "KB", "phase": 1, "date": "2026-09-25",
     "agent_time": {"start": "18:30", "end": "19:53", "minutes": 83, "note": "по часам, фаза 1"},
     "queue": queue(),
     "B_blender": {
         "build": jl("01-build/build_snow.json"),
         "light_study_960x540_32spp": {s: {"metrics": pick(jl(f"02-light-study/m_{s}.json"))}
                                       for s in ("S1", "S2", "S3", "S4")},
         "light_study_sec": jl("02-light-study/study_log_S1_S2_S3_S4.json"),
         "hero_1600x1000_128spp": {h: {"metrics": pick(jl(f"03-hero/m_{h}.json")),
                                       "main_face": keytop(f"03-hero/hero_{h}.png", f"03-hero/keytops_{h}.json")}
                                   for h in ("H1", "H2", "H3")},
         "hero_log": jl("03-hero/hero_log_H1_H2_H3.json"),
         "colorways_log": jl("03-hero/colorways_log.json"),
         "colorways_metrics": {cw: pick(jl(f"03-hero/m_colorway_{cw}.json")) for cw in ("snow", "graphite", "linen")},
     },
     "A_code": {
         "frame": "05-code-a/a_H1_v6.png", "metrics": pick(jl("05-code-a/m_a_H1_v6.json")),
         "main_face": keytop("05-code-a/a_H1_v6.png", "03-hero/keytops_H1.json"),
         "shot": {k: v for k, v in (jl("05-code-a/a_H1_v6.json") or {}).items() if k != "console"},
         "js_min_kb": 960.0, "js_br_kb": 266.9, "note": "three r186 + N8AO + Bokeh + OutputPass; calls/tris — по всем проходам кадра",
     },
     "variants": {"export": jl("04-variants/variants_export_report.json"), "post_flags": jl("04-variants/post_flags_report.json"),
                  "verdict": "работает: экспорт при KHR_materials_variants_ui=True; optimize — только с --join false; gltfpack -cc держит (имена: -kn -ke); three переключает"},
     }

# ============================================================================ фаза 2 (KB 19:53–20:12, KB2 20:14 → конец)
import glob  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

S = os.path.normpath(os.path.join(K, "../../../15-showcase/keyboard"))


def queue2(prefix=("KB2-",), since_kb=True):
    st, tot, wait, n, lab = {}, defaultdict(float), 0, 0, defaultdict(float)
    for line in open(LOG, encoding="utf-8"):
        m = re.search(r"^(\S+ \S+) pid=(\d+) (START|END)\s+label=(\S+)", line)
        if not m:
            continue
        ts, pid, ev, lb = m.groups()
        ok = lb.startswith(prefix) or (since_kb and lb.startswith("KB-") and ts >= "2026-09-25 19:53")
        if not ok:
            continue
        if ev == "START":
            w = re.search(r"waited=(\d+)s", line)
            wait += int(w.group(1)) if w else 0
            n += 1
            st[pid] = ("heavy" if "heavy=1" in line and "kind=blender" in line else
                       "browser_heavy" if "heavy=1" in line else re.search(r"kind=(\S+)", line).group(1), lb)
        elif pid in st:
            t = re.search(r"time=(\d+)s", line)
            if t:
                tot[st[pid][0]] += int(t.group(1))
                lab[re.sub(r"-[a-z]$", "", st[pid][1])] += int(t.group(1))
    return {"runs": n, "queue_wait_s": wait, "machine_s": dict(tot), "machine_total_s": sum(tot.values()),
            "by_label_s": dict(sorted(lab.items(), key=lambda x: -x[1]))}


def br_js(d):
    import brotli
    out = {}
    for f in sorted(glob.glob(os.path.join(d, "dist", "*.js"))):
        b = open(f, "rb").read()
        out[os.path.basename(f)] = [round(len(b) / 1024, 1), round(len(brotli.compress(b, quality=11)) / 1024, 1)]
    meta = json.load(open(os.path.join(d, "dist", "meta.json")))
    roles = {}
    for o, info in meta["outputs"].items():
        ins = " ".join(info.get("inputs", {}))
        name = os.path.basename(o)
        roles[name] = ("three" if "three.core" in ins else "n8ao+post" if "n8ao" in ins else "loaders" if "GLTFLoader" in ins
                       else "page" if "page.js" in ins else "model" if "model_" in ins else "stage3d" if "stage3d" in ins
                       else "entry" if name == "main.js" else "other")
    return {k: {"kb_min": v[0], "kb_br": v[1], "role": roles.get(k)} for k, v in out.items()}


def size_tree(d):
    tot = defaultdict(int)
    for f in glob.glob(os.path.join(d, "**", "*"), recursive=True):
        if os.path.isfile(f) and not f.endswith(".br"):
            tot[os.path.relpath(f, d).split("/")[0] + "/" + (os.path.relpath(f, d).split("/")[1] if "/" in os.path.relpath(f, d) else "")] += os.path.getsize(f)
    return {k: round(v / 1024, 1) for k, v in sorted(tot.items())}


def gate_txt(p):
    if not os.path.exists(p):
        return None
    rows = [ln.split(None, 1) for ln in open(p, encoding="utf-8") if ln[:4] in ("OK  ", "FAIL", "WARN", "SKIP")]
    return {"pass": sum(1 for r in rows if r[0] == "OK"), "fail": [r[1].strip() for r in rows if r[0] == "FAIL"],
            "rows": [" ".join(r).strip() for r in rows]}


def glb_info(p):
    import brotli
    import struct
    b = open(p, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    pr = [q for m in j["meshes"] for q in m["primitives"]]
    return {"kb": round(len(b) / 1024, 1), "kb_br": round(len(brotli.compress(b, quality=11)) / 1024, 1), "nodes": len(j["nodes"]),
            "meshes": len(j["meshes"]), "prims": len(pr), "prims_variants": sum(1 for q in pr if "KHR_materials_variants" in q.get("extensions", {})),
            "materials": len(j["materials"]), "images": [i.get("mimeType") for i in j.get("images", [])][:1], "ext": j.get("extensionsUsed")}


def gates(v):
    d = os.path.join(K, "11-gates", v)
    out = {k: gate_txt(os.path.join(d, f"gate_{k}.txt")) for k in ("desktop", "mobile", "reduce")}
    mj = os.path.join(d, "motion", "gates.json")
    if os.path.exists(mj):
        rows = json.load(open(mj)).get("rows", [])
        fails = [r for r in rows if r.get("verdict") == "FAIL"]
        out["motion"] = {"FAIL_B": sum(1 for r in fails if r.get("severity") == "B"), "FAIL_S": sum(1 for r in fails if r.get("severity") == "S"),
                         "FAIL_D": sum(1 for r in fails if r.get("severity") == "D"), "PASS": sum(1 for r in rows if r.get("verdict") == "PASS"),
                         "fails": sorted({f"{r['id']} {r.get('mode')} {r.get('found')}" for r in fails})}
    mk = glob.glob(os.path.join(d, "mkt", "*.marketing.json"))
    if mk:
        fm = json.load(open(mk[0])).get("findings_marketing", [])
        fl = [x for x in fm if str(x.get("verdict", x.get("status", ""))).upper().startswith("FAIL")]
        sev = defaultdict(int)
        for x in fl:
            sev[str(x.get("severity", x.get("sev", "?")))] += 1
        out["marketing"] = {"FAIL_by_severity": dict(sev), "blockers": sorted({str(x.get("id", x.get("check", "?"))) for x in fl
                            if str(x.get("severity", "")).lower() in ("blocker", "блокер", "b")})}
    lg = os.path.join(d, "gates.log")
    if os.path.exists(lg):
        out["load_avg"] = [ln.strip() for ln in open(lg) if " load " in ln][:6]
    return out


N["phase2"] = {
    "agent_time": {"KB": {"start": "19:53", "end": "20:12", "minutes": 19},
                   "KB2": {"start": "20:14", "end": "21:40", "minutes": 86, "note": "по часам"},
                   "KB3": {"start": "00:05", "end": os.environ.get("KB3_END", time.strftime("%H:%M")), "date": "2026-09-26", "note": "по часам"}},
    "queue": queue2(("KB2-", "KB3-")),
    "queue_KB3": queue2(("KB3-",), since_kb=False),
    "B_blender": {
        "hero2": {t: {"metrics": pick(jl(f"12-metrics/m_B_hero2_{t}.json")),
                      "main_face": keytop(f"07-b/out/hero2_{t}.png", f"07-b/cams/H2v2_{t}_keytops.json")} for t in ("desk", "mob")},
        "hero2_v1_metrics": {t: pick(jl(f"12-metrics/m_B_hero2_{t}_v1.json")) for t in ("desk", "mob")},
        "hero2_v1_main_face": {t: keytop(f"07-b/out/hero2_{t}_v1.png", f"07-b/cams/H2v2_{t}_keytops.json") for t in ("desk", "mob")},
        "logs": {os.path.basename(f)[4:-5]: jl(os.path.relpath(f, K)) for f in sorted(glob.glob(os.path.join(K, "07-b/out/log_*.json")))},
        "engine_choice": jl("12-metrics/engine_choice.json"),
        "encode": (jl("07-b/web/encode_report.json") or {"runs": [None]})["runs"][-1],
        "page_assets_kb": size_tree(os.path.join(S, "b-blender/assets")),
        "js": br_js(os.path.join(S, "b-blender")),
    },
    "C_hybrid": {"export": jl("06-export/out/export_report.json"),
                 "glb": {f: glb_info(os.path.join(K, "06-export/out", f)) for f in ("kb_web_raw.glb", "kb_desk.glb", "kb_mob.glb", "kb_desk_ktx2.glb")},
                 "atlas_webp_vs_ktx2": jl("12-metrics/kb3_atlas_webp_vs_ktx2.json"),
                 "page_assets_kb": size_tree(os.path.join(S, "c-hybrid/assets")), "js": br_js(os.path.join(S, "c-hybrid"))},
    "A_code": {"capture": jl("09-capture/capture_log.json"), "hero2": {t: {"metrics": pick(jl(f"12-metrics/m_A_hero2_{t}.json")),
               "main_face": keytop(f"09-capture/out/hero-{t}.png", f"07-b/cams/H2v2_{t}_keytops.json"),
               "metrics_nodof_KB2": pick(jl(f"12-metrics/m_A_hero2_{t}_nodof.json"))} for t in ("desk", "mob")},
               "page_assets_kb": size_tree(os.path.join(S, "a-code/assets")), "js": br_js(os.path.join(S, "a-code"))},
    "same_camera": {"before_exposure_fix": jl("12-metrics/abc_same_camera.json"), "after": jl("12-metrics/abc_after_fix.json")},
    "dev_runs": {v: {k: x for k, x in (jl(f"10-check/{d}/drive_log.json") or {}).get("kb", {}).items()} if jl(f"10-check/{d}/drive_log.json") else None
                 for v, d in (("a", "judge_a/desk"), ("b", "judge_b/desk"), ("c", "judge_c/desk"), ("a_mob", "judge_a/mob"),
                              ("b_mob", "judge_b/mob"), ("c_mob", "judge_c/mob"))},
    "phone_touch": {v: {k: (jl(f"10-check/mt_{v}/mob_touch.json") or {}).get(k) for k in ("typed", "key_css_px", "scroll_after_half", "errors", "kb")}
                    for v in ("a-code", "b-blender", "c-hybrid")},
    "loaf_probe_KB3": jl("12-metrics/kb3_loaf_probe.json"),
    "gates": {v: gates(v) for v in ("a", "b", "c")},
    "gates_KB2_c_before_fixes": gates("c_kb2"),
}
json.dump(N, open(OUT, "w"), ensure_ascii=False, indent=1)
print(OUT, json.dumps(N["queue"], ensure_ascii=False), json.dumps(N["phase2"]["queue"], ensure_ascii=False)[:400])
