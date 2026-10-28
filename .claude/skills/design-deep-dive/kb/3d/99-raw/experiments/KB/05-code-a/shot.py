"""shot.py — кадр варианта A: index.html?QUERY в Chromium (ANGLE/GL, Iris Xe), 1600×1000 DPR 1 → PNG + info.
    python3 shot.py OUT.png [query]"""
import functools, http.server, json, os, socketserver, sys, threading, time
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
out = os.path.abspath(sys.argv[1]); query = sys.argv[2] if len(sys.argv) > 2 else "cam=H1"
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
Q.extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript", ".woff2": "font/woff2", ".json": "application/json"}
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", 8783), functools.partial(Q, directory=HERE))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
logs = []
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"])
        p = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
        p.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
        p.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))
        t0 = time.time()
        p.goto(f"http://127.0.0.1:8783/index.html?{query}", wait_until="load")
        p.wait_for_function("window.__ready === true", timeout=120000)
        info = p.evaluate("window.__info")
        p.locator("#c").screenshot(path=out)
        info["wall_s"] = round(time.time() - t0, 2)
        b.close()
finally:
    httpd.shutdown(); httpd.server_close()
info["console"] = logs[:20]
json.dump(info, open(os.path.splitext(out)[0] + ".json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(info, ensure_ascii=False)[:1500])
