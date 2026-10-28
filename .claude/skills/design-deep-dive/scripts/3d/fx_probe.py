#!/usr/bin/env python3
"""fx_probe.py — замер своей демо-страницы с 3D/шейдерным эффектом.

Отличия от web_view.py --page (его тоже прогоняют для каждого демо):
  * режимы одним запуском: desktop (1440×900, DPR 1), mobile (Pixel 7: 412×915 CSS, DPR 2.625, touch, UA Android)
    с CPU×4, reduce (prefers-reduced-motion: reduce) и uncapped (без vsync: --disable-gpu-vsync
    --disable-frame-rate-limit → rAF не упирается в 60 и FPS показывает цену кадра);
  * покой отдельно от прокрутки: draw calls и FPS за 2 с простоя; доля пикселей, изменившихся за 1 с (есть ли движение);
  * прокрутка колесом мыши (как site_probe.py: работает и с Lenis), движение курсора по кругу (hover/tilt);
  * время до первого кадра с draw call (rAF), window.__ready, window.__info (что страница сама сообщает);
  * bench: если страница выставляет window.__bench(n) — N кадров с синхронизацией GPU (readPixels 1 px), мс/кадр;
  * сеть: переданные байты по категориям (request.sizes), как у site_probe.py; JS heap; ошибки и предупреждения консоли.

Использование:
  python3 fx_probe.py ROOT_DIR PAGE_REL_PATH OUT_DIR [--modes desktop,mobile,reduce,uncapped] [--wait 15000]
                      [--scroll-steps 16] [--pointer] [--bench 120] [--webgpu] [--query "?v=a"] [--label name]
  ROOT_DIR раздаётся локальным сервером (страница может ссылаться на ../assets внутри ROOT_DIR).
Результат: OUT_DIR/fx_<label>.json и скриншоты OUT_DIR/<label>_<mode>_*.png; сводка в stdout.
Замок браузера утилита берёт сама на время работы браузера: kbpaths.lock("browser"), реентерабельный по дереву
процессов — утилита, запущенная из утилиты с тем же замком, его не ждёт.
"""
import functools, http.server, json, os, socketserver, sys, threading, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

GPU = ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"]
UNCAPPED = ["--disable-gpu-vsync", "--disable-frame-rate-limit"]
WEBGPU = ["--enable-unsafe-webgpu", "--enable-features=Vulkan"]

INIT = r"""(() => {
  if (window.__fx) return;
  const P = window.__fx = {cur: 0, dc: [], t: [], firstDraw: null, ctx: [], lt: []};
  const bump = () => { P.cur++; };
  const wrap = (proto, names) => { if (!proto) return; for (const n of names) { const f = proto[n]; if (typeof f !== 'function') continue;
    proto[n] = function (...a) { bump(); return f.apply(this, a); }; } };
  const gl = ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced', 'drawRangeElements', 'multiDrawElementsWEBGL', 'multiDrawArraysWEBGL'];
  wrap(window.WebGLRenderingContext && WebGLRenderingContext.prototype, gl);
  wrap(window.WebGL2RenderingContext && WebGL2RenderingContext.prototype, gl);
  wrap(window.GPURenderPassEncoder && GPURenderPassEncoder.prototype, ['draw', 'drawIndexed', 'drawIndirect', 'drawIndexedIndirect']);
  const gc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, attrs) { const r = gc.call(this, type, attrs);
    try { if (r && !this.__ctxType) { this.__ctxType = type; P.ctx.push({type, t: Math.round(performance.now())}); } } catch (e) {}
    return r; };
  const raf = window.requestAnimationFrame.bind(window);
  const loop = (t) => { const d = P.cur; P.cur = 0; P.dc.push(d); P.t.push(t); if (d > 0 && P.firstDraw === null) P.firstDraw = Math.round(t);
    if (P.t.length > 60000) { P.t.splice(0, 30000); P.dc.splice(0, 30000); } raf(loop); };
  raf(loop);
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) P.lt.push([Math.round(e.startTime), Math.round(e.duration)]); }).observe({type: 'longtask', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) { const el = e.element; P.lcp = {t: Math.round(e.startTime), tag: el ? el.tagName : null}; } }).observe({type: 'largest-contentful-paint', buffered: true}); } catch (e) {}
})();"""

STATS = r"""((from) => { const P = window.__fx; const dc = P.dc.slice(from.dc); const t = P.t.slice(from.t);
  const d = []; for (let i = 1; i < t.length; i++) d.push(t[i] - t[i - 1]); const ds = d.slice().sort((a, b) => a - b);
  const s = dc.slice().sort((a, b) => a - b);
  return {frames: t.length, fps: d.length ? +(1000 / (d.reduce((a, b) => a + b, 0) / d.length)).toFixed(1) : null,
          frame_ms_avg: d.length ? +(d.reduce((a, b) => a + b, 0) / d.length).toFixed(2) : null,
          frame_ms_p95: ds.length ? +ds[Math.floor(ds.length * 0.95)].toFixed(1) : null,
          dc_median: s.length ? s[Math.floor(s.length / 2)] : 0, dc_max: s.length ? s[s.length - 1] : 0,
          frames_with_draws: dc.filter(x => x > 0).length}; })"""

MARK = "(() => ({dc: window.__fx.dc.length, t: window.__fx.t.length}))()"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve(root):
    h = functools.partial(Quiet, directory=root)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), h)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def diff_pct(a_path, b_path, thr=8):
    try:
        from PIL import Image, ImageChops
        a = Image.open(a_path).convert("RGB"); b = Image.open(b_path).convert("RGB")
        d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > thr else 0)
        return round(100.0 * d.histogram()[255] / (a.size[0] * a.size[1]), 2)
    except Exception:
        return None


def cat_of(url, ctype):
    u = url.split("?")[0].lower()
    for cat, exts in (("model3d", (".glb", ".gltf", ".bin", ".drc", ".splinecode")), ("texture3d", (".ktx2", ".hdr", ".exr")),
                      ("image", (".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg")), ("video", (".mp4", ".webm")),
                      ("wasm", (".wasm",)), ("js", (".js", ".mjs")), ("json", (".json",)), ("font", (".woff2", ".woff", ".ttf"))):
        if u.endswith(exts):
            return cat
    c = (ctype or "").lower()
    if "javascript" in c: return "js"
    if "html" in c: return "html"
    if "wasm" in c: return "wasm"
    if c.startswith("image/"): return "image"
    return "other"


def run_mode(pw, mode, url, out, label, a):
    args = GPU + (UNCAPPED if mode == "uncapped" else []) + (WEBGPU if "--webgpu" in a else [])
    b = pw.chromium.launch(headless=True, args=args)
    if mode == "mobile":
        dev = dict(pw.devices["Pixel 7"])
        ctx = b.new_context(**dev, reduced_motion="no-preference")
    else:
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1,
                            reduced_motion="reduce" if mode == "reduce" else "no-preference")
    ctx.add_init_script(INIT)
    p = ctx.new_page()
    logs, net = [], []
    p.on("console", lambda m: logs.append(f"{m.type}: {m.text[:240]}") if m.type in ("error", "warning") else None)
    p.on("pageerror", lambda e: logs.append(f"pageerror: {str(e)[:240]}"))

    def fin(req):
        try:
            r = req.response()
            if r is None:
                return
            sz = req.sizes()
            net.append({"url": req.url[:200], "cat": cat_of(req.url, r.headers.get("content-type", "")),
                        "bytes": sz.get("responseBodySize", 0) or 0, "status": r.status})
        except Exception:
            pass
    p.on("requestfinished", fin)
    if mode == "mobile":
        cdp = ctx.new_cdp_session(p)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    st = {"mode": mode, "browser": b.version, "args": args}
    t0 = time.time()
    try:
        p.goto(url, wait_until="load", timeout=120000)
    except Exception as e:
        logs.append(f"goto: {e}")
    try:
        p.wait_for_function("window.__ready === true", timeout=int(opt(a, "--wait", 15000)))
        st["ready"] = True
    except Exception:
        st["ready"] = False
    st["ready_sec"] = round(time.time() - t0, 2)
    p.wait_for_timeout(800)
    st["first_draw_ms"] = p.evaluate("window.__fx.firstDraw")
    st["contexts"] = p.evaluate("window.__fx.ctx")
    st["info"] = p.evaluate("window.__info || null")
    W, H = p.viewport_size["width"], p.viewport_size["height"]
    st["canvases"] = p.evaluate("""[...document.querySelectorAll('canvas')].map(c => { const r = c.getBoundingClientRect();
        return {w: c.width, h: c.height, css: [Math.round(r.width), Math.round(r.height)], ctx: c.__ctxType || null}; })""")
    # покой
    m = p.evaluate(MARK); p.wait_for_timeout(2000)
    st["idle"] = p.evaluate(f"{STATS}({json.dumps(m)})")
    f0 = os.path.join(out, f"{label}_{mode}_0.png"); p.screenshot(path=f0)
    p.wait_for_timeout(1000)
    f1 = os.path.join(out, f"{label}_{mode}_idle1s.png"); p.screenshot(path=f1)
    st["idle_motion_pct"] = diff_pct(f0, f1)
    shots = [f0]
    # курсор
    if "--pointer" in a and mode != "mobile":
        import math
        m = p.evaluate(MARK)
        for i in range(48):
            x = W / 2 + W * 0.3 * math.cos(i / 48 * 2 * math.pi); y = H / 2 + H * 0.3 * math.sin(i / 48 * 2 * math.pi)
            p.mouse.move(x, y); p.wait_for_timeout(25)
        st["pointer"] = p.evaluate(f"{STATS}({json.dumps(m)})")
        fp = os.path.join(out, f"{label}_{mode}_pointer.png"); p.screenshot(path=fp); shots.append(fp)
    # прокрутка колесом
    steps = int(opt(a, "--scroll-steps", 16))
    total = p.evaluate("Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0) - innerHeight")
    st["scrollable_px"] = total
    if steps and total > 50:
        m = p.evaluate(MARK)
        p.mouse.move(W / 2, H / 2)
        delta = max(120, int(total / steps))
        marks = {steps // 2, steps}
        for s in range(1, steps + 1):
            p.mouse.wheel(0, delta); p.wait_for_timeout(110)
            if s in marks:
                p.wait_for_timeout(700)
                fp = os.path.join(out, f"{label}_{mode}_scroll{s}.png"); p.screenshot(path=fp); shots.append(fp)
        st["scroll"] = p.evaluate(f"{STATS}({json.dumps(m)})")
        st["scroll_y_end"] = p.evaluate("Math.round(scrollY)")
    # bench
    nb = int(opt(a, "--bench", 0) or 0)
    if nb:
        try:
            st["bench"] = p.evaluate(f"window.__bench ? window.__bench({nb}) : null")
        except Exception as e:
            st["bench"] = {"error": str(e)[:200]}
    try:
        st["js_heap_mb"] = round(p.evaluate("performance.memory ? performance.memory.usedJSHeapSize : 0") / 1e6, 1)
    except Exception:
        pass
    lt = p.evaluate("window.__fx.lt")
    st["longtasks"] = {"n": len(lt), "tbt_ms": sum(max(0, d - 50) for _, d in lt), "max_ms": max([d for _, d in lt] or [0])}
    st["lcp"] = p.evaluate("window.__fx.lcp || null")
    by = {}
    for n in net:
        by.setdefault(n["cat"], [0, 0]); by[n["cat"]][0] += 1; by[n["cat"]][1] += n["bytes"]
    st["network"] = {"requests": len(net), "transfer_kb": round(sum(n["bytes"] for n in net) / 1024, 1),
                     "by_cat_kb": {k: {"n": v[0], "kb": round(v[1] / 1024, 1)} for k, v in sorted(by.items(), key=lambda kv: -kv[1][1])},
                     "heaviest": sorted([(round(n["bytes"] / 1024, 1), n["url"][-90:]) for n in net], reverse=True)[:6]}
    st["console"] = logs[:40]
    st["console_errors"] = len([l for l in logs if l.startswith(("error", "pageerror"))])
    st["shots"] = shots
    b.close()
    return st


def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    root, page, out = os.path.abspath(a[0]), a[1], os.path.abspath(a[2])
    os.makedirs(out, exist_ok=True)
    label = opt(a, "--label", os.path.splitext(os.path.basename(page))[0])
    modes = opt(a, "--modes", "desktop,mobile,reduce,uncapped").split(",")
    httpd, port = serve(root)
    url = f"http://127.0.0.1:{port}/{page}{opt(a, '--query', '')}"
    from playwright.sync_api import sync_playwright
    res = {"page": page, "url_query": opt(a, "--query", ""), "date": time.strftime("%Y-%m-%d %H:%M"), "modes": {}}
    try:
        with kbpaths.lock("browser"), sync_playwright() as pw:
            for mode in modes:
                try:
                    res["modes"][mode] = run_mode(pw, mode, url, out, label, a)
                except Exception as e:
                    res["modes"][mode] = {"error": str(e)[:400]}
    finally:
        httpd.shutdown()
    json.dump(res, open(os.path.join(out, f"fx_{label}.json"), "w"), ensure_ascii=False, indent=1)
    short = {}
    for k, v in res["modes"].items():
        if "error" in v:
            short[k] = v; continue
        short[k] = {"ready": v.get("ready"), "first_draw_ms": v.get("first_draw_ms"), "idle": v.get("idle"),
                    "idle_motion_pct": v.get("idle_motion_pct"), "pointer": v.get("pointer"), "scroll": v.get("scroll"),
                    "bench": v.get("bench"), "net_kb": v["network"]["transfer_kb"], "by_cat": v["network"]["by_cat_kb"],
                    "heap": v.get("js_heap_mb"), "tbt": v["longtasks"]["tbt_ms"], "errors": v["console_errors"],
                    "console": v["console"][:6], "canvases": v.get("canvases"), "info": v.get("info")}
    print(json.dumps(short, ensure_ascii=False, indent=1))
    print("JSON", os.path.join(out, f"fx_{label}.json"))


if __name__ == "__main__":
    main()
