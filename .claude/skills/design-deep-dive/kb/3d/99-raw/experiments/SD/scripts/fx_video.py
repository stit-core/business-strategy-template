"""fx_video.py (SD3) — запись 10 с «фонарика инженера» (C) для судьи: десктоп 1440 × 900, WebGL2 на видеокарте (GPU-флаги
fx_probe), курсор по расписанию: день (C = B) → вход на план, полумрак → трещина (1) → окно (2) → прихожая (3) → розетка (4)
→ уход с плана, свет возвращается. Playwright пишет всю сессию; ffmpeg вырезает ровно 10 с от начала сценария (VP9).
    python3 fx_video.py PAGE_DIR OUT.webm [--mobile]"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_shots import serve, GPU  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

root, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
tmp = tempfile.mkdtemp(prefix="fxvid_", dir=os.path.dirname(out))
srv, port = serve(root)
FR = dict(u0=-4.9, u1=3.7, w0=-0.6, w1=8.5)


def frac(x, y, z):
    u = (x - y) / math.sqrt(2); w = (x + y) * 0.40824829 + z * 0.81649658
    return (u - FR["u0"]) / (FR["u1"] - FR["u0"]), (FR["w1"] - w) / (FR["w1"] - FR["w0"])


D = {k: frac(*v) for k, v in {"1": (2.5, 4.25, 0.0), "2": (2.0, 6.42, 0.87), "3": (3.25, 3.4167, 0.0), "4": (9.233, 4.6667, 0.5)}.items()}
info = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=GPU)
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1, record_video_dir=tmp,
                        record_video_size={"width": 1440, "height": 900})
    t_page = time.time()
    p = ctx.new_page()
    p.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load")
    p.wait_for_function("window.__ready === true", timeout=20000)
    p.wait_for_timeout(900)
    st = p.evaluate("(() => { const r = document.querySelector('.plan__stage').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    P = lambda fx, fy: (st[0] + fx * st[2], st[1] + fy * st[3])  # noqa: E731
    # точки сценария (доли stage) и время прихода, с; между точками — плавное ведение (smoothstep), 30 шагов/с
    outside = (st[0] - 260, st[1] + st[3] * 0.62)
    plan = [(0.0, outside), (0.9, outside), (1.2, P(0.05, 0.62)), (2.2, P(0.30, 0.66)), (2.8, P(*D["1"])), (3.8, P(*D["1"])),
            (4.6, P(*D["2"])), (5.4, P(*D["2"])), (6.3, P(0.58, 0.72)), (6.8, P(*D["3"])), (7.7, P(*D["4"])), (8.6, P(*D["4"])),
            (9.1, (st[0] + st[2] * 0.7, st[1] - 30)), (10.0, (st[0] + st[2] * 0.7, st[1] - 30))]
    p.mouse.move(*outside)
    t0 = time.time()
    k = 0
    while True:
        e = time.time() - t0
        if e >= plan[-1][0]:
            break
        while k < len(plan) - 2 and e >= plan[k + 1][0]:
            k += 1
        (ta, a), (tb, bb) = plan[k], plan[k + 1]
        s = min(1.0, max(0.0, (e - ta) / max(1e-6, tb - ta)))
        s = s * s * (3 - 2 * s)
        p.mouse.move(a[0] + (bb[0] - a[0]) * s, a[1] + (bb[1] - a[1]) * s)
        p.wait_for_timeout(33)
    p.wait_for_timeout(400)
    info["state_end"] = p.evaluate("window.__fonarik.state()")
    info["found"] = p.evaluate("[...document.querySelectorAll('.plan__list li.is-found')].map(e => e.dataset.d)")
    vid = p.video.path()
    ctx.close()
    b.close()
srv.shutdown()
off = max(0.0, t0 - t_page)
info.update({"offset_s": round(off, 2), "raw": vid})
subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{off:.2f}", "-i", vid, "-t", "10", "-an", "-c:v", "libvpx-vp9",
                "-b:v", "0", "-crf", "36", "-row-mt", "1", "-cpu-used", "4", "-pix_fmt", "yuv420p", out], check=True)
pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=width,height,r_frame_rate", "-of", "json", out],
                    capture_output=True, text=True)
info["probe"] = json.loads(pr.stdout)
shutil.rmtree(tmp, ignore_errors=True)
json.dump(info, open(out.rsplit(".", 1)[0] + ".json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(info, ensure_ascii=False))
