"""fx_bench2.py (SD4) — цена кадра «фонарика» C точнее, чем window.__bench: у __bench каждый кадр меряется отдельно, и при
performance.now() с шагом 0,1 мс (страница без cross-origin isolation) быстрый кадр даёт 0. Здесь — сумма N кадров:
  sync  — N × (draw + readPixels 1 px): мс/кадр с ожиданием GPU (задержка кадра);
  flush — N × draw, один readPixels в конце: пропускная способность (мс/кадр).
Режимы: desk1 (1440 × 900, DPR 1), desk2 (DPR 2 — худший десктоп), mob (412 × 915, DPR 2,625 → холст ≤ 1,5, CPU×4).
Луч на трещине, полумрак 1 (как в кадре судьи beam-on). Браузер с GPU-флагами fx_probe.
    python3 fx_bench2.py PAGE_DIR OUT.json [--n 400]"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_shots import serve, GPU  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

root, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
N = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 400
srv, port = serve(root)
URL = f"http://127.0.0.1:{port}/index.html"
JS = """async (N) => {
  const F = window.__fonarik; F.aim(0.4259, 0.6312);
  await new Promise(r => setTimeout(r, 1600));
  const c = document.querySelector('canvas.plan__fx'), gl = c.getContext('webgl2'), px = new Uint8Array(4);
  for (let i = 0; i < 30; i++) F.frame();
  gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  let t0 = performance.now();
  for (let i = 0; i < N; i++) { F.frame(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); }
  const sync = (performance.now() - t0) / N;
  t0 = performance.now();
  for (let i = 0; i < N; i++) F.frame();
  gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  const flush = (performance.now() - t0) / N;
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  return { sync_ms: +sync.toFixed(4), flush_ms: +flush.toFixed(4), canvas: [c.width, c.height], dpr: devicePixelRatio,
           state: F.state(), gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : null };
}"""
MODES = {
    "desk1": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1),
    "desk2": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=2),
    "mob": dict(viewport={"width": 412, "height": 915}, device_scale_factor=2.625, is_mobile=True, has_touch=True,
                user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Mobile Safari/537.36"),
}
res = {"n": N, "loadavg": open("/proc/loadavg").read().split()[:3]}
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=GPU)
    for m, kw in MODES.items():
        c = b.new_context(**kw)
        p = c.new_page()
        if m == "mob":
            cdp = c.new_cdp_session(p); cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        p.goto(URL, wait_until="load")
        p.wait_for_function("window.__ready === true", timeout=20000)
        if m == "mob":  # план в кадр (как у кадра судьи), до показа — касание не нужно: aim() включает фонарь сам
            p.evaluate("(() => { const f = document.querySelector('figure.plan'); scrollTo(0, scrollY + f.getBoundingClientRect().top - 56); })()")
        p.wait_for_timeout(600)
        try:
            res[m] = p.evaluate(JS, N)
        except Exception as e:
            res[m] = {"error": str(e)[:200]}
        print(m, res[m], flush=True)
        c.close()
    b.close()
srv.shutdown()
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
