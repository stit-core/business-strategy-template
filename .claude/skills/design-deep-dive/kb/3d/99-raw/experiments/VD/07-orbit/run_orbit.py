#!/usr/bin/env python3
"""VD/07-orbit — облёт пачками через общую очередь (KIT §2): каждый запуск — `slot_run.py --heavy`, внутри velmora.py с
`--budget` из budget.txt (сам останавливается до конца бюджета) и `--skip-existing` (продолжает с первого недостающего кадра).

VD3 (26.09.2026): очередь slot_run v2 — честная (FIFO), соседи встают между пачками сами → пауза между пачками 5 с (была 45);
метки VD3-…; каждый запуск обёрнут в tools/peak.py — реальный пик памяти Blender в журнале пачек (порог --min-mem по нему:
кадр 1280 × 720 — пик 1 606 МБ → порог 3000; 2560 × 1440 — 3500); режимы можно цепочкой: `run_orbit.py arc poster2k full`.
Сэмплы круга — из файла 07-orbit/full_spp.txt (решение по пробе 64 против 96 спп; нет файла — 96, безопасное умолчание).
Бюджет пачки — из 07-orbit/budget.txt перед каждой пачкой (умолчание 480 с ≈ 8 мин: оркестратор 26.09 00:40 — соседи ждали за
14-минутной пачкой до 15–18 мин; суммарное время то же, накладные ≈ 15 с на пачку). Нумерация пачек продолжается по журналу.

    python3 run_orbit.py arc  [--script velmora_v6_final.py]   # 61 кадр, 0 → 25°, наезд 1 → 0,89, 128 спп → 07-orbit/arc/o25_NNN.png
    python3 run_orbit.py full [--script …]                     # 72 кадра, 0 → 360° (шаг 5°), 64/96 спп → 07-orbit/full/o360_NNN.png
    python3 run_orbit.py poster2k [--script …]                 # один кадр 2560 × 1440 (f000 дуги), 128 спп → 07-orbit/poster2k/
    python3 run_orbit.py arc poster2k full                     # всё по очереди (ночь 26.09)
Журнал пачек — 07-orbit/<режим>/_batches.jsonl (время очереди и рендера, кадры, пик памяти)."""
import json
import os
import subprocess
import sys
import time

R = "/home/mm/Документы/app-design/blender-research"
VD = f"{R}/99-raw/experiments/VD"
MODES = {
    "arc": dict(orbit="61,0,25", dist="1,0.89", spp=128, res="1280x720", tag="o25", n=61, masks="000,030,060", mem=3000),
    "full": dict(orbit="72,0,360", dist="1,1", spp=96, res="1280x720", tag="o360", n=72, masks="000,018,036,054", mem=3000),
    "poster2k": dict(orbit="61,0,25", dist="1,0.89", spp=128, res="2560x1440", tag="o25_2k", n=1, masks="000", frames="0-0",
                     mem=3500),
}
PAUSE = 5
BUDGET_FILE = f"{VD}/07-orbit/budget.txt"


def budget():
    try:
        return int(open(BUDGET_FILE).read().split()[0])
    except (OSError, ValueError, IndexError):
        return 480


def run_mode(mode, script):
    cfg = dict(MODES[mode])
    if mode == "full" and os.path.exists(f"{VD}/07-orbit/full_spp.txt"):
        cfg["spp"] = int(open(f"{VD}/07-orbit/full_spp.txt").read().split()[0])
    if mode == "full" and os.path.exists(f"{VD}/07-orbit/full_n.txt"):     # VD3 02:55: круг 36 кадров через 10° (чётные)
        cfg["n"] = int(open(f"{VD}/07-orbit/full_n.txt").read().split()[0])
    out = f"{VD}/07-orbit/{mode}"
    os.makedirs(out, exist_ok=True)
    journal = open(f"{out}/_batches.jsonl", "a")
    journal.write(json.dumps({"mode": mode, "start": time.strftime("%Y-%m-%d %H:%M:%S"), "spp": cfg["spp"], "script": script},
                             ensure_ascii=False) + "\n")
    print(f"== {mode}: {cfg['n']} кадров, {cfg['spp']} спп, {cfg['res']} → {out}", flush=True)
    k = 0
    try:
        k = sum(1 for ln in open(f"{out}/_batches.jsonl") if ln.startswith('{"batch"'))
    except OSError:
        pass
    fails = 0
    while True:
        have = [f for f in os.listdir(out) if f.startswith(cfg["tag"] + "_") and f.endswith(".png") and "_mask" not in f
                and f[len(cfg["tag"]) + 1:len(cfg["tag"]) + 4].isdigit()]
        if len(have) >= cfg["n"]:
            print(f"готово: {len(have)} кадров в {out}", flush=True)
            journal.write(json.dumps({"mode": mode, "done": time.strftime("%Y-%m-%d %H:%M:%S"), "frames": len(have)}) + "\n")
            break
        k += 1
        label = f"VD3-{mode}-{k:02d}"
        cmd = ["python3", f"{R}/99-raw/tools/slot_run.py", "--heavy", "--min-mem", str(cfg["mem"]), "--label", label, "--",
               "python3", f"{VD}/tools/peak.py",
               "python3", f"{R}/99-raw/tools/blender_run.py", f"{VD}/01-build/{script}", "--timeout", "960", "--",
               "--scheme", "S1", "--orbit", cfg["orbit"], "--dist", cfg["dist"], "--res", cfg["res"],
               "--samples", str(cfg["spp"]), "--out", out, "--tag", cfg["tag"], "--skip-existing", "--budget", str(budget()),
               "--mask", "--mask-frames", cfg["masks"]]
        if "frames" in cfg:
            cmd += ["--frames", cfg["frames"]]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        dt = time.time() - t0
        lines = [ln for ln in (r.stdout + r.stderr).splitlines()
                 if ln.startswith(("VD_RENDER", "VD_BUDGET", "[blender_run]", "VD_PEAK"))]
        rendered = [ln for ln in lines if ln.startswith("VD_RENDER")]
        peak = [ln.split()[1] for ln in lines if ln.startswith("VD_PEAK")]
        bl = [ln for ln in lines if ln.startswith("[blender_run]")]
        bl_s = None
        if bl and "time=" in bl[-1]:
            try:
                bl_s = float(bl[-1].split("time=")[1].split("s")[0])
            except ValueError:
                bl_s = None
        rec = {"batch": k, "label": label, "exit": r.returncode, "wall_s": round(dt, 1), "blender_s": bl_s,
               "queue_s": round(dt - bl_s, 1) if bl_s else None, "frames": len(rendered),
               "names": [ln.split()[1] for ln in rendered], "render_s": [float(ln.split()[2]) for ln in rendered],
               "peak_rss_mb": int(peak[-1]) if peak else None, "tail": lines[-3:], "t": time.strftime("%H:%M:%S")}
        journal.write(json.dumps(rec, ensure_ascii=False) + "\n")
        journal.flush()
        print(json.dumps({x: rec[x] for x in ("batch", "exit", "wall_s", "queue_s", "frames", "peak_rss_mb", "t")},
                         ensure_ascii=False), flush=True)
        if r.returncode == 75:
            time.sleep(60)
            continue
        if r.returncode != 0 and not rendered:
            fails += 1
            print("пачка упала без кадров", (r.stdout + r.stderr).splitlines()[-8:], flush=True)
            if fails >= 2:
                print("две пачки подряд без кадров — стоп", flush=True)
                return 1
            time.sleep(60)
            continue
        fails = 0
        time.sleep(PAUSE)
    return 0


def main():
    a = sys.argv[1:]
    script = a[a.index("--script") + 1] if "--script" in a else "velmora_v6_final.py"
    modes = [m for m in a if m in MODES]
    for mode in modes:
        code = run_mode(mode, script)
        if code:
            return code
    print("цепочка готова:", " → ".join(modes), time.strftime("%H:%M:%S"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
