#!/usr/bin/env python3
"""VD3/09-page — числа фаз 2–3 в 15-showcase/velmora/numbers.json → ключ "phase2" (его читает make_page.py).

    python3 numbers_phase2.py [--agent-stop HH:MM]

Источники: 07-orbit/<режим>/<tag>_stats_*.json (время каждого кадра, спп), 07-orbit/<режим>/_batches.jsonl (пачки: Blender,
очередь, пик памяти), 08-enc/results_{arc,full}.json (веса, SSIM, время кодирования), 06-look/i3/metrics_f030.json (числа i3),
velmora/judge/metrics.json (судья), журнал очереди .locks/slot_run.log (метки VD3-…: все запуски и ожидание)."""
import glob
import json
import os
import sys
import time

R = "/home/mm/Документы/app-design/blender-research"
VD = f"{R}/99-raw/experiments/VD"
V = f"{R}/15-showcase/velmora"
LOG = "/home/mm/Документы/app-design/.locks/slot_run.log"


def frames_stats(d, tag):
    """Время каждого кадра: журнал пачек (names/render_s) + статистика отдельных запусков. Ловушка: velmora.py называет
    статистику пачки по всему списку облёта (<tag>_stats_000-060.json) — каждая пачка перезаписывает файл прежней."""
    per, spp = {}, set()
    for f in sorted(glob.glob(f"{d}/{tag}_stats*.json")):
        st = json.load(open(f))
        for name, v in (st.get("views") or {}).items():
            per[name] = v["render_s"]
            spp.add(st.get("samples"))
    for b in batches(d):
        for name, t in zip(b.get("names", []), b.get("render_s", [])):
            per[name] = t
    return per, sorted(x for x in spp if x)


def batches(d):
    out = []
    try:
        for ln in open(f"{d}/_batches.jsonl"):
            if ln.startswith('{"batch"'):
                out.append(json.loads(ln))
    except OSError:
        pass
    return out


def mode_block(mode, tag, n_expected):
    d = f"{VD}/07-orbit/{mode}"
    per, spp = frames_stats(d, tag)
    bs = batches(d)
    rs = list(per.values())
    blender_s = sum(b.get("blender_s") or 0 for b in bs)
    blk = {"frames_done": len(per), "frames_expected": n_expected, "spp": spp[0] if len(spp) == 1 else spp,
           "render_s_sum": round(sum(rs), 1), "s_per_frame_mean": round(sum(rs) / len(rs), 1) if rs else None,
           "s_per_frame_min_max": [min(rs), max(rs)] if rs else None,
           "batches": len(bs), "blender_wall_s": round(blender_s, 1), "queue_wait_s": round(sum(b.get("queue_s") or 0 for b in bs), 1),
           "peak_rss_mb_max": max((b.get("peak_rss_mb") or 0) for b in bs) if bs else None,
           "first_batch_t": bs[0]["t"] if bs else None, "last_batch_t": bs[-1]["t"] if bs else None}
    return blk


def queue_log():
    """Все запуски VD3 по журналу очереди: число, сумма времени, ожидание."""
    runs, wait, busy = 0, 0.0, 0.0
    try:
        for ln in open(LOG, errors="replace"):
            if "label=VD3-" not in ln:
                continue
            if " START " in ln and "waited=" in ln:
                runs += 1
                wait += float(ln.split("waited=")[1].split("s")[0])
            elif " END " in ln and "time=" in ln:
                busy += float(ln.split("time=")[1].split("s")[0])
    except OSError:
        pass
    return {"runs": runs, "wait_s": round(wait), "busy_s": round(busy)}


def main():
    a = sys.argv[1:]
    nums = json.load(open(f"{V}/numbers.json"))
    arc = mode_block("arc", "o25", 61)
    full = mode_block("full", "o360", 72)
    p2k = mode_block("poster2k", "o25_2k", 1)
    # кадр 030 дуги рендерился отдельным запуском VD3-f030 до драйвера (105 с Blender) — в сумму дуги
    arc_bl = arc["blender_wall_s"] + 105.0
    full_test_s = 53.8 + 56.3        # проба 64 спп: 000 и 036 скопированы в круг (full_t64/run.log)
    enc = {}
    for m in ("arc", "full"):
        p = f"{VD}/08-enc/results_{m}.json"
        if os.path.exists(p):
            r = json.load(open(p))
            enc[m] = {"frames": r.get("source", {}).get("frames"), "total_secs": r.get("total_secs"),
                      "kb": {k: v.get("total_kb", v.get("kb")) for k, v in {**r.get("frames", {}), **r.get("video", {})}.items()},
                      "per_frame_kb_avif1280": (r.get("frames", {}).get("seq-avif-1280") or {}).get("per_frame_kb"),
                      "poster_kb": r.get("poster"),
                      "ssim_av1_g4": (r.get("video", {}).get("orbit-av1-g4") or {}).get("ssim_all")}
    i3 = {}
    p = f"{VD}/06-look/i3/metrics_f030.json"
    if os.path.exists(p):
        m = json.load(open(p)).get("i3", {})
        i3 = {k: (round(m[k], 3) if isinstance(m.get(k), float) else m.get(k)) for k in
              ("clip_obj_pct", "hi_obj_pct", "bg_vs_page_dE", "weight_on_obj", "weight_in_text", "bg_noise_e3")}
        i3["obj_L_p50"] = round(m["obj_L"]["p50"], 1)
        i3["label_L_p50"] = round(m["label_L"]["p50"], 1)
    ph = nums.get("phase2", {})
    ph.update({
        "date": "2026-09-25/26",
        "note": "Фаза 2 (VD2, 25.09 20:13–21:36): красота i1–i3, драйверы. Фаза 3 (VD3, 26.09 ночь): облёт, страница, судья.",
        "scene": "velmora_v6_final.py (i3): лента — купол-среда + дисперсия тремя стёклами, воздух светом по складкам, гранит со слюдой, вторичное движение 12°",
        "orbit25_spp": arc["spp"] if not isinstance(arc["spp"], list) else 128,
        "orbit360_spp": full["spp"] if not isinstance(full["spp"], list) else 64,
        "orbit25_s_per_frame": arc["s_per_frame_mean"] or 0,
        "orbit360_s_per_frame": full["s_per_frame_mean"] or 0,
        "machine": {
            "orbit25_render_h": round(arc_bl / 3600, 2),
            "orbit360_render_h": round((full["blender_wall_s"] + full_test_s) / 3600, 2),
            "poster2k_s": p2k["render_s_sum"] or None,
            "arc": arc, "full": full, "poster2k": p2k,
            "full_spp_test": "64 против 96 спп на кадрах 000/036: 52,5/55,1 с против 67,4/76,8 с; зерно фона 1,11e-3 у обоих; глазами неотличимы → 64 (07-orbit/full_spp_test.json, full_t64/_zoom_64_vs_96.png)",
            "vd3_queue_log": queue_log(),
            "note": "render_h — время Blender по пачкам (сборка сцены, BVH, маски — внутри); s_per_frame — чистый рендер кадра; очередь — отдельно",
        },
        "encode": enc,
        "i3_f030": i3,
        "agent_clock_vd3": {"start": "00:06", "stop": (a[a.index("--agent-stop") + 1] if "--agent-stop" in a else time.strftime("%H:%M"))},
        "agent_clock_vd2": {"start": "20:13", "stop": "21:36", "minutes": 83},
        "machine_vd2": {"blender_runs": 34, "blender_s": 427, "queue_wait_s": 2874},
        "cost_rub": 0,
    })
    nums["phase2"] = ph
    nums["note"] = ("Дуэль «нейросеть против Blender»: облёт флакона Velmora. Фаза 1 — кадры и числа; фазы 2–3 — облёт Cycles, "
                    "страница b-blender на том же scrub.js, судья (velmora/judge/).")
    json.dump(nums, open(f"{V}/numbers.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: ph[k] for k in ("orbit25_spp", "orbit360_spp", "orbit25_s_per_frame", "orbit360_s_per_frame")}, ensure_ascii=False))
    print(json.dumps({k: v for k, v in ph["machine"].items() if k.endswith(("_h", "_s"))}, ensure_ascii=False))
    print("arc", {k: arc[k] for k in ("frames_done", "batches", "blender_wall_s", "queue_wait_s", "peak_rss_mb_max")})
    print("full", {k: full[k] for k in ("frames_done", "batches", "blender_wall_s", "queue_wait_s", "peak_rss_mb_max")})


if __name__ == "__main__":
    main()
