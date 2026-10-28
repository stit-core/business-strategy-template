"""judge_shots.py (SD3) — кадры судьи одного варианта «Сдано» (KIT §7): одинаковые состояния у A, B, C.
  first-screen-desk — 1440 × 900, DPR 1, прокрутка 0, через 1,5 с после load (вход первого экрана закончен);
  first-screen-mob  — 390 × 844, DPR 3 (телефон с касанием), план в кадре: верх фигуры плана на 56 px; у C кадр снимается
                      через 0,2 с после прокрутки — до однократного показа фонаря (он начинается через 0,35 с);
  icons             — десктоп, раздел «Что проверяет инженер» (заголовок на 64 px);
  act-stamp         — десктоп, «Образец акта» по центру окна, конечное состояние: клип штампа доиграл (браузер БЕЗ GPU-флагов —
                      с ними декодер видео headless-shell падает, shots/sd3_video/video_probe.json);
  C: beam-off (полумрак, луч в пустом углу кадра — бумага), beam-on (луч на трещине, пункт 1 найден), tour-mob (телефон,
     середина однократного показа) — браузер с GPU-флагами (WebGL2 на видеокарте).
    python3 judge_shots.py PAGE_DIR NAME OUT_DIR [--states a,b,…]"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_shots import serve, GPU  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

a = sys.argv[1:]
root, name, out = os.path.abspath(a[0]), a[1], os.path.abspath(a[2])
states = a[a.index("--states") + 1].split(",") if "--states" in a else \
    ["first-screen-desk", "first-screen-mob", "icons", "act-stamp"] + (["beam-off", "beam-on", "tour-mob"] if name == "c-hybrid" else [])
os.makedirs(out, exist_ok=True)
srv, port = serve(root)
URL = f"http://127.0.0.1:{port}/index.html"
res = {"name": name, "states": {}}
logs = []
PIXEL = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True,
         "user_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Mobile Safari/537.36"}


def shot(p, st, extra=None):
    f = f"{out}/{name}__{st}.png"
    p.screenshot(path=f)
    res["states"][st] = {"file": os.path.basename(f), "scrollY": p.evaluate("scrollY"), **(extra or {})}
    print(st, res["states"][st], flush=True)


def ready(p):
    if name == "c-hybrid":
        p.wait_for_function("window.__ready === true", timeout=20000)


with sync_playwright() as pw:
    gpu = pw.chromium.launch(headless=True, args=GPU)
    soft = pw.chromium.launch(headless=True, args=[])
    # ---- десктоп: первый экран, приборы
    if {"first-screen-desk", "icons"} & set(states):
        c = gpu.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        p = c.new_page(); p.on("console", lambda m: logs.append(f"{m.type}: {m.text[:200]}"))
        p.goto(URL, wait_until="load"); ready(p); p.wait_for_timeout(1500)
        if "first-screen-desk" in states:
            shot(p, "first-screen-desk")
        if "icons" in states:
            p.evaluate("(() => { const h = document.querySelector('#offer-h'); scrollTo(0, scrollY + h.getBoundingClientRect().top - 64); })()")
            p.wait_for_timeout(900)
            shot(p, "icons")
        c.close()
    # ---- C: луч (десктоп, WebGL на видеокарте)
    if {"beam-off", "beam-on"} & set(states):
        c = gpu.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        p = c.new_page(); p.on("console", lambda m: logs.append(f"{m.type}: {m.text[:200]}"))
        p.goto(URL, wait_until="load"); ready(p); p.wait_for_timeout(800)
        st = p.evaluate("(() => { const r = document.querySelector('.plan__stage').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        FR = dict(u0=-4.9, u1=3.7, w0=-0.6, w1=8.5)

        def frac(x, y, z):
            u = (x - y) / math.sqrt(2); w = (x + y) * 0.40824829 + z * 0.81649658
            return (u - FR["u0"]) / (FR["u1"] - FR["u0"]), (FR["w1"] - w) / (FR["w1"] - FR["w0"])
        p.mouse.move(st[0] - 40, st[1] + st[3] * 0.9)
        if "beam-off" in states:
            p.mouse.move(st[0] + 0.12 * st[2], st[1] + 0.93 * st[3], steps=10); p.wait_for_timeout(1400)
            shot(p, "beam-off", {"fx": p.evaluate("window.__fonarik.state()")})
        if "beam-on" in states:
            fx, fy = frac(2.5, 4.25, 0.0)
            p.mouse.move(st[0] + fx * st[2], st[1] + fy * st[3], steps=14); p.wait_for_timeout(1400)
            shot(p, "beam-on", {"fx": p.evaluate("window.__fonarik.state()")})
        c.close()
    # ---- телефон: план в кадре (+ у C — середина однократного показа фонаря)
    if {"first-screen-mob", "tour-mob"} & set(states):
        c = gpu.new_context(**PIXEL)
        p = c.new_page(); p.on("console", lambda m: logs.append(f"{m.type}: {m.text[:200]}"))
        p.goto(URL, wait_until="load"); ready(p); p.wait_for_timeout(1200)
        p.evaluate("(() => { const f = document.querySelector('figure.plan'); scrollTo(0, scrollY + f.getBoundingClientRect().top - 56); })()")
        p.wait_for_timeout(200)
        if "first-screen-mob" in states:
            shot(p, "first-screen-mob")
        if "tour-mob" in states:
            try:
                p.wait_for_function("window.__fonarik && window.__fonarik.state().tour", timeout=3000, polling=20)
                p.wait_for_timeout(1000)
                shot(p, "tour-mob", {"fx": p.evaluate("window.__fonarik.state()")})
            except Exception as e:
                res["tour_err"] = str(e)[:160]
        c.close()
    # ---- «Образец акта»: клип штампа доиграл (браузер без GPU-флагов)
    if "act-stamp" in states:
        c = soft.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        p = c.new_page(); p.on("console", lambda m: logs.append(f"{m.type}: {m.text[:200]}"))
        p.goto(URL, wait_until="load"); p.wait_for_timeout(600)
        y = p.evaluate("(() => { const d = document.querySelector('.doc'); const r = d.getBoundingClientRect(); return Math.round(scrollY + r.top + r.height / 2 - innerHeight / 2); })()")
        for k in range(1, 9):
            p.evaluate(f"window.scrollTo(0, {y * k / 8})"); p.wait_for_timeout(60)
        t0 = time.time()
        has = p.evaluate("!!document.querySelector('.stamp3d__clip')")
        if has:
            try:
                p.wait_for_function("(() => { const v = document.querySelector('.stamp3d__clip'); return v.ended || !document.querySelector('.doc__stamp3d').classList.contains('is-armed') && v.currentTime > 1; })()",
                                   timeout=8000, polling=50)
            except Exception as e:
                res["stamp_err"] = str(e)[:120]
        p.wait_for_timeout(700 if has else 1200)
        extra = {"stamp_wait_s": round(time.time() - t0, 2)}
        if has:
            extra["stamp"] = p.evaluate("(() => { const v = document.querySelector('.stamp3d__clip'); return {ended: v.ended, t: v.currentTime, cls: document.querySelector('.doc__stamp3d').className}; })()")
        shot(p, "act-stamp", extra)
        c.close()
    gpu.close(); soft.close()
srv.shutdown()
res["console"] = logs[:20]
res["console_errors"] = len([x for x in logs if x.startswith(("error", "pageerror"))])
json.dump(res, open(f"{out}/{name}__judge.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "states"}, ensure_ascii=False))
