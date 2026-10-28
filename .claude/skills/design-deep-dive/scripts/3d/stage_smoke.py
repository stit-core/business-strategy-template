#!/usr/bin/env python3
"""stage_smoke.py — живая проверка рантайма сцен и шаблонов набора на `demo.html` в Chromium: GPU, «уменьшить
движение», программный рендер.

    python3 stage_smoke.py [--root DIR] [--page demo.html] [--shots] [--json ОТЧЁТ]
    python3 stage_smoke.py --selftest

Страница — `kb/3d/16-js-scenes/examples/demo.html` (`--root`, `--page` — своя копия с теми же местами `#s-beats`,
`#s-play`, `#s-glide`, `#s-world`). Прогоны и что считается годным:
  gpu      — сцены оживают на подлёте, живых не больше двух; колесо по 120 px переключает такты шагов и длинной сцены
             по одному (0→1→2→3 и 0→…→4); `play` живёт на экране; `glide` догоняет прогресс; ошибок консоли нет;
  reduced  — «уменьшить движение»: ни одной живой сцены, раскадровка видна, ошибок нет;
  soft     — программный рендер SwiftShader: то же, что reduced.
Вердикт — поле `ok` у каждого прогона и общее; код 0 — всё годно, 1 — нет. `--shots` — кадры тактов в
`$DDD_HOME/out/3d/stage-smoke/`. Замок браузера утилита берёт сама (kbpaths.lock("browser")). Прогон — около
полутора минут на машине с GPU.
"""
from __future__ import annotations

import functools
import http.server
import json
import os
import socketserver
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

ROOT = kbpaths.kb("3d", "16-js-scenes", "examples")
GPU = ["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=vulkan", "--enable-features=Vulkan"]
SOFT = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
PLACES = ("s-beats", "s-play", "s-glide", "s-world")
STATE = """() => ({ info: window.__rt.info(), live: document.querySelectorAll('[data-stage][data-live]').length,
  story: document.querySelectorAll('[data-stage][data-stage-story]').length, y: window.scrollY,
  dots: Array.from(document.querySelectorAll('#s-beats [data-dot]')).findIndex(d => d.getAttribute('aria-current') === 'step'),
  caps: Array.from(document.querySelectorAll('#s-beats [data-cap][data-on]')).map(c => c.getAttribute('data-k')) })"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(root):
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(root)))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def launch(pw, args):
    try:
        return pw.chromium.launch(channel="chromium", args=args)
    except Exception:  # noqa: BLE001 — сборка Playwright без канала chromium
        return pw.chromium.launch(args=args)


def top_of(pg, sel):
    return pg.evaluate(f"document.querySelector('#{sel}').getBoundingClientRect().top + scrollY")


def run(pw, url, args, reduced=False, shots=None, tag="gpu"):
    b = launch(pw, args)
    try:
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2,
                            reduced_motion="reduce" if reduced else "no-preference")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
        pg.goto(url, wait_until="load")
        time.sleep(0.6)
        out = {"start": pg.evaluate(STATE)}
        pg.evaluate(f"window.scrollTo(0, {top_of(pg, 's-beats')} - 72)")
        time.sleep(1.2)
        out["at_beats"] = pg.evaluate(STATE)
        seq = []
        pg.mouse.move(1000, 450)
        for _ in range(26):
            pg.mouse.wheel(0, 120)
            time.sleep(0.15)
            s = pg.evaluate(STATE)
            if not seq or seq[-1] != s["dots"]:
                seq.append(s["dots"])
                if shots and s["dots"] >= 0:
                    time.sleep(1.8)
                    pg.screenshot(path=str(shots / f"{tag}-beat-{s['dots']}.png"))
        out["beat_seq"] = seq
        time.sleep(2.0)
        pg.evaluate(f"window.scrollTo(0, {top_of(pg, 's-play')} - 200)")
        time.sleep(10.5)
        out["play_end"] = pg.evaluate(STATE)
        glide, top = [], top_of(pg, "s-glide")
        for k in range(0, 2800, 400):
            pg.evaluate(f"window.scrollTo(0, {top} - 72 + {k})")
            time.sleep(0.9)
            g = [x for x in pg.evaluate(STATE)["info"] if x["mode"] == "glide"][0]
            glide.append([k, g["state"], g["p"], g["cur"]])
        out["glide"] = glide
        pg.evaluate(f"window.scrollTo(0, {top_of(pg, 's-world')} - 72)")
        time.sleep(1.5)
        wseq, wlive = [], 0
        for _ in range(34):
            pg.mouse.wheel(0, 120)
            time.sleep(0.15)
            st = pg.evaluate(STATE)
            wlive = max(wlive, st["live"])
            beat = [x for x in st["info"] if x["mode"] == "beats"][-1]["beat"]
            if not wseq or wseq[-1] != beat:
                wseq.append(beat)
                if shots and beat >= 0:
                    time.sleep(2.0)
                    pg.screenshot(path=str(shots / f"{tag}-world-{beat}.png"))
        out["world_seq"] = wseq
        out["world_max_live"] = wlive
        pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        time.sleep(1.0)
        out["bottom"] = pg.evaluate(STATE)
        out["errors"] = errs
    finally:
        b.close()
    return out


def steps_ok(seq, last):
    """Такты идут по одному: соседние значения отличаются на 1, последний не меньше last."""
    s = [x for x in seq if x is not None and x >= 0]
    return bool(s) and all(b - a == 1 for a, b in zip(s, s[1:])) and s[-1] >= last


def judge(tag, r):
    """Прогон → список непройденных условий (пусто — годен)."""
    bad = []
    if r.get("errors"):
        bad.append(f"ошибки страницы: {r['errors'][:3]}")
    if tag == "gpu":
        if not steps_ok(r.get("beat_seq", []), 3):
            bad.append(f"такты шагов не по одному: {r.get('beat_seq')}")
        if not steps_ok(r.get("world_seq", []), 4):
            bad.append(f"такты длинной сцены не по одному: {r.get('world_seq')}")
        if r.get("world_max_live", 0) > 2:
            bad.append(f"живых сцен больше двух: {r['world_max_live']}")
        play = [x for x in r.get("play_end", {}).get("info", []) if x.get("mode") == "play"]
        if not play or play[0].get("state") != "live":
            bad.append("сцена play не ожила на экране")
        curs = [g[3] for g in r.get("glide", [])]
        if not curs or any(b < a for a, b in zip(curs, curs[1:])) or curs[-1] < 0.9:
            bad.append(f"glide не догоняет прогресс: {curs}")
    else:
        if r.get("world_max_live", 0) or r.get("play_end", {}).get("live", 0) or r.get("bottom", {}).get("live", 0):
            bad.append("есть живая сцена — ждали только раскадровку")
        if r.get("bottom", {}).get("story", 0) < 1:
            bad.append("раскадровки не видно")
    return bad


def opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return default


def selftest():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(("OK   " if cond else "FAIL ") + name)

    check("steps_ok: 0→1→2→3", steps_ok([-1, 0, 1, 2, 3], 3))
    check("steps_ok: перескок 1→3 — не годен", not steps_ok([0, 1, 3], 3))
    check("steps_ok: не дошли до конца — не годен", not steps_ok([0, 1, 2], 3))
    good = {"errors": [], "beat_seq": [0, 1, 2, 3], "world_seq": [0, 1, 2, 3, 4], "world_max_live": 2,
            "play_end": {"info": [{"mode": "play", "state": "live"}]}, "glide": [[0, "live", 0, 0], [400, "live", 1, 0.95]]}
    check("judge gpu: годный прогон", judge("gpu", good) == [])
    check("judge gpu: три живых — находка", judge("gpu", dict(good, world_max_live=3)) != [])
    soft = {"errors": [], "world_max_live": 0, "play_end": {"live": 0}, "bottom": {"live": 0, "story": 4}}
    check("judge soft: только раскадровка — годен", judge("soft", soft) == [])
    check("judge reduced: живая сцена — находка", judge("reduced", dict(soft, world_max_live=1)) != [])
    page = ROOT / "demo.html"
    html = page.read_text(encoding="utf-8") if page.is_file() else ""
    check("demo.html на месте и несёт четыре места", all(f'id="{p}"' in html for p in PLACES))
    print("stage_smoke selftest: " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv):
    argv = list(argv)
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if "--selftest" in argv:
        return selftest()
    root = Path(opt(argv, "--root", str(ROOT))).resolve()
    page = opt(argv, "--page", "demo.html")
    report = opt(argv, "--json")
    shots = None
    if "--shots" in argv:
        shots = kbpaths.out("3d", "stage-smoke")
    from playwright.sync_api import sync_playwright
    httpd, base = serve(root)
    res = {}
    try:
        with kbpaths.lock("browser"), sync_playwright() as pw:
            url = f"{base}/{page}"
            res["gpu"] = run(pw, url, GPU, shots=shots, tag="gpu")
            res["reduced"] = run(pw, url, GPU, reduced=True, tag="reduced")
            res["soft"] = run(pw, url, SOFT, tag="soft")
    finally:
        httpd.shutdown()
    for tag in ("gpu", "reduced", "soft"):
        bad = judge(tag, res[tag])
        res[tag]["ok"], res[tag]["findings"] = not bad, bad
    res["ok"] = all(res[t]["ok"] for t in ("gpu", "reduced", "soft"))
    text = json.dumps(res, ensure_ascii=False, indent=1)
    if report:
        Path(report).write_text(text, encoding="utf-8")
    print(text if not report else json.dumps({t: {"ok": res[t]["ok"], "findings": res[t]["findings"]}
                                              for t in ("gpu", "reduced", "soft")} | {"ok": res["ok"]},
                                             ensure_ascii=False, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
