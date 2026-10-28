#!/usr/bin/env python3
"""write_numbers3 — фаза 2 (дорожки Z2 → Z3) в 15-showcase/zveno/numbers.json: «b-blender.phase2», «c-hybrid», «z_machine_phase2».
Чужие разделы не трогает (A ведёт CD в a-code/numbers.json). Источники: журнал очереди (.locks/slot_run.log, метки Z2-*/Z3-*),
логи zseq (время кадра, VmHWM), вес поставки B (encode_seq.py report → out/seq/weights.json), метрики кадров судьи (out/judge/metrics.json),
проверка страницы B (out/check_b/*.json), GLB C (assets, out/c_web*_bake.json, gltf_diff), ворота (out/gates/<страница>/…),
motion_check L2 и marketing_audit (out/motion_*.log, out/mkt_*/).
"""
import glob
import json
import os
import re
import time

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
ZV = R + "/15-showcase/zveno"
F = ZV + "/numbers.json"
LOG = "/home/mm/Документы/app-design/.locks/slot_run.log"


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def kb(p):
    return round(os.path.getsize(p) / 1024, 1) if os.path.exists(p) else None


def machine(prefix):
    runs, wait = {}, 0
    for line in open(LOG, errors="replace"):
        m = re.search(r"END\s+label=(" + prefix + r"-[\w-]+) exit=(\d+) time=(\d+)s", line)
        if m:
            k = m.group(1)
            runs.setdefault(k, {"runs": 0, "sec": 0}); runs[k]["runs"] += 1; runs[k]["sec"] += int(m.group(3))
        m = re.search(r"START\s+label=" + prefix + r"-[\w-]+.*waited=(\d+)s", line)
        if m:
            wait += int(m.group(1))
    return {"runs": runs, "machine_total_s": sum(v["sec"] for v in runs.values()), "queue_wait_s": wait}


def seq_frames():
    out = {}
    for p in glob.glob(Z + "/out/seq/*/log_*.json") + glob.glob(Z + "/out/judge/log_*.json"):
        d = load(p) or {}
        key = os.path.basename(os.path.dirname(p))
        fr = d.get("frames", [])
        if fr:
            e = out.setdefault(key, {"frames": 0, "sec": 0.0, "vmhwm_mb": 0, "samples": d.get("samples")})
            e["frames"] += len(fr); e["sec"] += sum(f["sec"] for f in fr); e["vmhwm_mb"] = max(e["vmhwm_mb"], d.get("vmhwm_mb") or 0)
    for e in out.values():
        e["sec_per_frame"] = round(e["sec"] / max(1, e["frames"]), 1); e["sec"] = round(e["sec"], 1)
    return out


def gates(tag):
    out = {}
    for g in ("desk", "mob", "rm"):
        p = f"{Z}/out/gates/{tag}/gate_{g}.txt"
        if os.path.exists(p):
            rows = [l.strip() for l in open(p) if l.strip()]
            out[g] = {"fail": sum(r.startswith("FAIL") for r in rows), "rows": rows}
    lt = f"{Z}/out/gates/{tag}/load.txt"
    if os.path.exists(lt):
        out["load"] = [l.strip() for l in open(lt) if l.startswith(("load", "start", "motion", "mkt"))]
    return out


def motion(tag):
    p = f"{Z}/out/motion_{tag}.log"
    res = {}
    if os.path.exists(p):
        for line in open(p, errors="replace"):
            if line.startswith("{") and '"fail_B"' in line:
                res = json.loads(line)
    g = load(f"{Z}/out/motion_{tag}/gates.json")
    if isinstance(g, list):
        res["fails"] = [{k: r.get(k) for k in ("moment", "mode", "verdict", "severity", "found")} for r in g if r.get("verdict") == "FAIL"][:12]
    return res


def mkt(tag, name):
    d = load(f"{Z}/out/mkt_{tag}/{name}.marketing.json") or {}
    if not d:
        return None
    fm = d.get("findings_marketing") or []
    fails = [f for f in fm if f.get("verdict") == "FAIL"]
    return {"compare": {k: (d.get("compare") or {}).get(k) for k in ("consumer_serious_fail", "removed_by_profile", "kept", "marketing_new_serious")},
            "marketing_fail": len(fails), "severities": sorted({f.get("severity") for f in fails}),
            "ids": sorted({f.get("id") for f in fails}), "note": "все FAIL — «полировка» общего style.css A (шкала отступов/кеглей)"}


cur = load(F) or {}
b = cur.get("b-blender", {})
jm = load(Z + "/out/judge/metrics.json") or {}
judge = {}
for k, v in jm.items():
    o, s = v.get("obj", {}), v.get("shell_L", {})
    judge[os.path.basename(k)[:-4]] = {"shell_p50_p75_p90": [s.get("p50"), s.get("p75"), s.get("p90")],
                                       "clip_obj_pct": round(o.get("clip_obj_pct", 0), 2), "obj_minus_bg_L": round(o.get("obj_minus_bg_L", 0), 1),
                                       "bg_vs_page_dE": round(o.get("bg_vs_page_dE", 0), 2), "edge_bottom_dE": v.get("edge_bottom_dE_L", [None])[0],
                                       "noise_flat_shell_e3": v.get("noise_flat_shell_e3"), "noise_bg_e3": v.get("noise_bg_e3")}
chk = {}
for p in glob.glob(Z + "/out/check_b/check_b*.json"):
    d = load(p) or {}
    for k in ("desk", "mob", "reduce"):
        if k in d:
            chk[k] = d[k]
b["phase2"] = {
    "tracks": "Z2 (25.09 20:17–21:36) → Z3 (26.09 00:05–" + time.strftime("%H:%M") + ")", "updated": time.strftime("%Y-%m-%d %H:%M"),
    "agent_time_h": {"Z2": 1.3, "Z3": round((time.time() - time.mktime(time.strptime("2026-09-26 00:05", "%Y-%m-%d %H:%M"))) / 3600, 1)},
    "engine": "Cycles CPU (20 потоков) + OIDN; секвенции 40 спп --fast (телефон 28), кадры судьи 128 спп 1600×1000; EEVEE отклонён (out/engine)",
    "sets": {"story-d": "90 кадров 1280×800 (0 = постер, 1–17 кран, 18–89 сцена)", "scan-d": "60 кадров 1280×800",
             "story-m": "60 кадров 720×1560 (0 = постер)", "scan-m": "60 кадров 720×1560"},
    "frames": seq_frames(), "weights": load(Z + "/out/seq/weights.json"),
    "posters_kb": {f: kb(f"{ZV}/b-blender/img/{f}") for f in ("hero-d.avif", "hero-d.webp", "hero-m.avif", "hero-m.webp")},
    "judge_metrics": judge,
    "halo_ring_L_p50_p90_peak": {"H4m_phase1_volume": [37.0, 48.8, 50.0], "k3_r0.55": [28.4, 31.5, 31.9], "k5_r0.5": [35.7, 39.9, 40.3],
                                 "k6.5_r0.45": [39.1, 44.4, 45.1], "k8_r0.42": [42.1, 48.5, 49.2], "chosen": "k 6,5 / r 0,42"},
    "scan_frame_s": {"before_hide_above_plane": [16.8, 17.4], "after": [13.5, 13.9]},
    "page_check": chk,
    "gates": gates("b-blender"), "motion_check_L2": motion("b"), "marketing_audit": mkt("b", "zveno-b-blender"),
}
cur["b-blender"] = b
A = ZV + "/c-hybrid/assets"
cur["c-hybrid"] = {
    "tracks": "Z2 (ассет, 25.09) + Z3 (крюк v2, касательные, 26.09) + CD2/CD3 (крюк _shared/code3d)", "updated": time.strftime("%Y-%m-%d %H:%M"),
    "page": "копия a-code (main.js CD3 01:36, вид p3) + строка glb {url, lowUrl, innerUrl, innerLowUrl}; сборка build.sh --glb (крюк v2)",
    "glb_kb": {f: kb(f"{A}/{f}") for f in ("zveno-main.glb", "zveno-inner.glb", "zveno-low-main.glb", "zveno-low-inner.glb")},
    "glb_full_kb": {"zveno.glb (без касательных)": 1272.8, "zveno-low.glb": 704.6, "zveno.glb с касательными": kb(Z + "/out/c_full/zveno.glb")},
    "tris": {"desktop": 87903, "desktop_main": 63831, "inner": 24072, "phone": 47883, "phone_main": 36439, "phone_inner": 11444},
    "draw_calls_glb": {"desktop": 66, "phone": 57}, "materials": {"desktop": 23, "phone": 22},
    "ao_atlas": {"desktop": "2048² (24 с запекания)", "phone": "1024² (5 с)"},
    "tangents": {"main_kb_with": 1255.5, "main_kb_without": 1008.8, "main_kb_br_with": 759, "main_kb_br_without_cd3": 679,
                 "why": "без TANGENT анизотропия крышек в three — «веер» 48 граней; optimize нужен --prune-attributes false"},
    "hook_v2": {"innerUrl": "взят: −119 КБ br первого экрана десктопа, −62 телефона, первый кадр 309 против 323 мс (замер CD3)",
                "ktx2": "не взят: сеть +301 КБ br (+38 %), первый кадр +25 мс; выигрыш только память GPU текстур 7,5 против 28,8 МБ"},
    "checks": {"validator": "0 ошибок / 0 предупреждений (все файлы)", "glb_lint": "0 предупреждений",
               "three_inspect": "0 ошибок консоли, 66 вызовов, 87 903 треуг.",
               "gltf_diff": (load(Z + "/out/c_web/diff/diff_metrics.json") or {}).get("mean"),
               "qa_scene": "review: hidden_inside 8 (начинка, задумано), nonmanifold 1, big_textures, many_materials, no_camera"},
    "stand": {"hero_calls": 122, "hero_tris": 137290, "scan_calls": 61, "scan_tris": 73655},
    "gates": gates("c-hybrid"), "motion_check_L2": motion("c"), "marketing_audit": mkt("c", "zveno-c-hybrid"),
}
cur["z_machine_phase2"] = {"Z2": machine("Z2"), "Z3": machine("Z3")}
json.dump(cur, open(F, "w"), ensure_ascii=False, indent=1)
print(json.dumps({"Z3_machine_s": cur["z_machine_phase2"]["Z3"]["machine_total_s"], "Z3_wait_s": cur["z_machine_phase2"]["Z3"]["queue_wait_s"],
                  "frames": b["phase2"]["frames"]}, ensure_ascii=False)[:1500])
