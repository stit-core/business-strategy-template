"""bench_check.py (SD4) — почему window.__bench из fx_probe вернул 0 мс: тот же __bench(120) при плане в кадре и после
прокрутки к концу страницы (как делает fx_probe), десктоп 1440 × 900 DPR 1, GPU-флаги fx_probe.
    python3 bench_check.py PAGE_DIR OUT.json"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_shots import serve, GPU  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

root, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
srv, port = serve(root)
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=GPU)
    p = b.new_page(viewport={"width": 1440, "height": 900})
    p.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load")
    p.wait_for_function("window.__ready === true", timeout=20000)
    p.wait_for_timeout(800)
    res["in_view"] = p.evaluate("window.__bench(120)")
    p.evaluate("scrollTo(0, document.documentElement.scrollHeight)"); p.wait_for_timeout(900)
    res["scrolled_end"] = p.evaluate("window.__bench(120)")
    p.evaluate("scrollTo(0, 0)"); p.wait_for_timeout(900)
    res["back_in_view"] = p.evaluate("window.__bench(120)")
    b.close()
srv.shutdown()
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
