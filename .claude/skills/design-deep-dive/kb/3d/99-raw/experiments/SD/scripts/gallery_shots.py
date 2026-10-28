"""gallery_shots.py (SD4) — исходники картинок галереи приёмов «Сдано» в DPR 2 (резче кадров судьи 1440 × 900 DPR 1):
  c_beam2x.png   — C, луч на трещине (как judge beam-on), вырезка stage;
  c_window2x.png — C, луч на окне (дефект 2), вырезка stage;
  b_stage2x.png  — B без ввода, вырезка stage (номера HTML поверх кадра Blender).
Браузер с GPU-флагами (WebGL2 на видеокарте), как у fx_shots / judge_shots.
    python3 gallery_shots.py S_DIR OUT_DIR"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_shots import serve, GPU  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

S, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(out, exist_ok=True)
FR = dict(u0=-4.9, u1=3.7, w0=-0.6, w1=8.5)


def frac(x, y, z):
    u = (x - y) / math.sqrt(2); w = (x + y) * 0.40824829 + z * 0.81649658
    return (u - FR["u0"]) / (FR["u1"] - FR["u0"]), (FR["w1"] - w) / (FR["w1"] - FR["w0"])


STAGE = "(() => { const r = document.querySelector('.plan__stage').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()"
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=GPU)
    for v in ("b-blender", "c-hybrid"):
        srv, port = serve(f"{S}/{v}")
        c = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        p = c.new_page()
        p.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load")
        if v == "c-hybrid":
            p.wait_for_function("window.__ready === true", timeout=20000)
        p.wait_for_timeout(1200)
        st = p.evaluate(STAGE)
        clip = {"x": st[0], "y": st[1], "width": min(st[2], 1440 - st[0]), "height": min(st[3], 900 - st[1])}
        if v == "b-blender":
            p.screenshot(path=f"{out}/b_stage2x.png", clip=clip)
        else:
            p.mouse.move(st[0] - 40, st[1] + st[3] * 0.9)
            for name, pt in (("c_beam2x", (2.5, 4.25, 0.0)), ("c_window2x", (2.0, 6.42, 0.87))):
                fx, fy = frac(*pt)
                p.mouse.move(st[0] + fx * st[2], st[1] + fy * st[3], steps=14); p.wait_for_timeout(1400)
                p.screenshot(path=f"{out}/{name}.png", clip=clip)
                res[name] = p.evaluate("window.__fonarik.state()")
        res[v] = {"stage": st}
        c.close(); srv.shutdown()
    b.close()
json.dump(res, open(f"{out}/gallery_shots.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False)[:600])
