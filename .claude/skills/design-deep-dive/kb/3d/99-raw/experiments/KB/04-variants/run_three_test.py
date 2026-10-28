"""run_three_test.py — открыть web/index.html в Chromium (Playwright, GPU через ANGLE), дождаться __done, сохранить отчёт и снимок."""
import functools, http.server, json, os, socketserver, threading, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
PORT = 8783
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); super().end_headers()
Q.extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".glb": "model/gltf-binary", ".js": "text/javascript"}
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(Q, directory=WEB))
threading.Thread(target=httpd.serve_forever, daemon=True).start()
logs = []
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"])
        p = b.new_page(viewport={"width": 1110, "height": 800})
        p.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
        p.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load")
        p.wait_for_function("window.__done === true", timeout=120000)
        res = p.evaluate("window.__result")
        p.screenshot(path=os.path.join(HERE, "three_variants_sheet.png"), full_page=True)
        b.close()
finally:
    httpd.shutdown(); httpd.server_close()
json.dump({"result": res, "console": logs[:40]}, open(os.path.join(HERE, "three_variants_report.json"), "w"), ensure_ascii=False, indent=1)
for f, r in res.items():
    if not isinstance(r, dict):
        print(f, r); continue
    pv = r.get("per_variant", {})
    summ = {vn: sorted({m["material"] for m in ms}) for vn, ms in pv.items()}
    pix = {vn: [m["pixel"] for m in ms][:3] for vn, ms in pv.items()}
    print(f, "| meshes", r["meshes"], "with_mapping", r["with_mapping"], "| load", r["load_ms"], "мс |", json.dumps(summ, ensure_ascii=False), "| px", json.dumps(pix))
print("console:", logs[:6])
