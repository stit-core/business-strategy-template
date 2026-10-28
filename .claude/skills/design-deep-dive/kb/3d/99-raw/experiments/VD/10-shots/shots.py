#!/usr/bin/env python3
"""VD3/10-shots — кадры страницы для судьи и слепого голосования: ОДИН И ТОТ ЖЕ сценарий на странице нейросети (копия
velmora/ai/01-mouse-scrub) и на странице Blender (velmora/b-blender) — движок scrub.js у обеих один.

    python3 shots.py first  URL OUT.png [--mobile] [--after 2200]   # первый экран: 1440 × 900 (или 390 × 844 телефон)
    python3 shots.py record URL OUT.webm [--secs 10]                # 10 с одного сценария мыши, 1440 × 900, webm (VP9)

first: ждёт, пока сцена «live» и все кадры секвенции загружены, затем снимает ровно через --after мс после готовности
сцены (stats.readyAt движка): вступление (1,8 с, кадр 0 → точка покоя 0,5) кончилось, дрейф едва начался — у обеих
страниц один и тот же момент облёта (≈ середина дуги).
record: после загрузки и вступления (+2,6 с) — сценарий мыши 10 с (слежение → быстрый бросок → медленно → дрожь →
рука замерла, начинается дрейф), указатель двигается 60 раз в секунду; видео Playwright обрезается ffmpeg ровно по началу
сценария и перекодируется в VP9 (CRF 30, 30 к/с). Запускать под `slot_run --kind browser --heavy` (замер — в тишине).
Сценарий x(t) — доля ширины окна (сцена во всю ширину; движок берёт (x − 0,08) / 0,84)."""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

GPU = ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu", "--autoplay-policy=no-user-gesture-required"]
LIVE = """() => { const st = document.querySelector('[data-scrub]'); const s = st && st.__scrub;
  return !!(s && st.dataset.state === 'live' && s.stats.readyAt != null && s.stats.framesLoaded >= s.stats.framesTotal); }"""


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


# (t0, t1, x0, x1, форма): сценарий 10 с, x — доля ширины окна
SCENARIO = [
    (0.0, 0.5, 0.50, 0.50, "hold"),      # рука входит в кадр по центру
    (0.5, 3.5, 0.50, 0.92, "ease"),      # медленное слежение к концу дуги
    (3.5, 4.4, 0.92, 0.08, "ease"),      # быстрый бросок к началу
    (4.4, 6.4, 0.08, 0.62, "ease"),      # медленно к середине
    (6.4, 7.4, 0.62, 0.62, "jitter"),    # дрожь руки ± 3 %
    (7.4, 10.0, 0.62, 0.62, "hold"),     # рука замерла: через 1,4 с начинается дрейф
]


def x_at(t):
    for t0, t1, x0, x1, kind in SCENARIO:
        if t0 <= t < t1 or (t >= t1 and (t0, t1) == SCENARIO[-1][:2]):
            u = (t - t0) / (t1 - t0)
            if kind == "ease":
                return x0 + (x1 - x0) * ease(u)
            if kind == "jitter":
                return x0 + 0.03 * math.sin(2 * math.pi * 5 * (t - t0))
            return x0
    return SCENARIO[-1][3]


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def first(url, out, mobile, after):
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=GPU)
        vw, vh = (390, 844) if mobile else (1440, 900)
        ctx = b.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=1, is_mobile=mobile, has_touch=mobile)
        p = ctx.new_page()
        logs = []
        p.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        p.goto(url, wait_until="load", timeout=120000)
        p.wait_for_function(LIVE, timeout=60000, polling=50)
        p.wait_for_function(f"() => performance.now() >= document.querySelector('[data-scrub]').__scrub.stats.readyAt + {after}",
                            timeout=60000, polling=16)
        p.screenshot(path=out)
        info = p.evaluate("""() => { const s = document.querySelector('[data-scrub]').__scrub;
            return {variant: s.variant, kind: s.kind, p: +s.p.toFixed(4), frames: s.stats.framesLoaded + '/' + s.stats.framesTotal,
                    readyAt: s.stats.readyAt, now: Math.round(performance.now())}; }""")
        b.close()
    info.update({"out": out, "url": url, "viewport": [vw, vh], "after_ms": after, "console": logs[:10]})
    print(json.dumps(info, ensure_ascii=False))
    return info


def record(url, out, secs):
    tmp = tempfile.mkdtemp(prefix="vd3rec_")
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=GPU)
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1,
                            record_video_dir=tmp, record_video_size={"width": 1440, "height": 900})
        t_page = time.time()
        p = ctx.new_page()
        p.goto(url, wait_until="load", timeout=120000)
        p.wait_for_function(LIVE, timeout=60000, polling=50)
        p.wait_for_function("() => performance.now() >= document.querySelector('[data-scrub]').__scrub.stats.readyAt + 2600",
                            timeout=60000, polling=16)
        y = 900 * 0.55
        p.mouse.move(1440 * x_at(0.0), y)
        t_start = time.time()
        trace = []
        while True:
            t = time.time() - t_start
            if t >= secs:
                break
            x = 1440 * x_at(t)
            p.mouse.move(x, y)
            if len(trace) % 6 == 0:
                trace.append((round(t, 3), round(x / 1440, 4), p.evaluate("() => +document.querySelector('[data-scrub]').__scrub.p.toFixed(4)")))
            else:
                trace.append((round(t, 3), round(x / 1440, 4), None))
            nxt = t_start + (len(trace)) / 60.0
            dt = nxt - time.time()
            if dt > 0:
                time.sleep(dt)
        t_end = time.time()
        stats = p.evaluate("() => { const s = document.querySelector('[data-scrub]').__scrub; return {variant: s.variant, draws: s.stats.draws}; }")
        vpath = p.video.path()
        t_close = time.time()
        ctx.close()
        b.close()
    # видео Playwright начинается не с создания страницы (первый кадр — позже), а кончается закрытием контекста:
    # начало сценария на шкале видео = длительность видео − (t_close − t_start)
    pts = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time", "-of", "csv=p=0",
                          vpath], capture_output=True, text=True).stdout.split()
    raw_dur = max(float(x) for x in pts if x.replace(".", "", 1).isdigit()) if pts else (t_close - t_page)
    off = max(0.0, raw_dur - (t_close - t_start))
    enc = ["ffmpeg", "-v", "error", "-y", "-ss", f"{off:.3f}", "-i", vpath, "-t", f"{secs:.3f}", "-an", "-vf", "fps=30",
           "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", out]
    subprocess.run(enc, check=True)
    raw_kb = round(os.path.getsize(vpath) / 1024)
    shutil.rmtree(tmp, ignore_errors=True)
    info = {"out": out, "url": url, "secs": secs, "offset_s": round(off, 3), "raw_dur_s": round(raw_dur, 3),
            "offset_from_page_s": round(t_start - t_page, 3), "moves": len(trace),
            "move_hz": round(len(trace) / (t_end - t_start), 1), "kb": round(os.path.getsize(out) / 1024), "raw_kb": raw_kb,
            "variant": stats["variant"], "draws": stats["draws"],
            "trace_sample": [tr for tr in trace if tr[2] is not None][::10]}
    json.dump(info, open(os.path.splitext(out)[0] + "_rec.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: info[k] for k in ("out", "offset_s", "moves", "move_hz", "kb", "variant", "draws")}, ensure_ascii=False))
    return info


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        return 2
    mode, url, out = a[:3]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if mode == "first":
        first(url, out, "--mobile" in a, int(opt(a, "--after", "2200")))
    elif mode == "record":
        record(url, out, float(opt(a, "--secs", "10")))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
