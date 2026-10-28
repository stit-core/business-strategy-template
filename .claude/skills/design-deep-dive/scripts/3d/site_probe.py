#!/usr/bin/env python3
"""site_probe.py — замер страницы с 3D (живой сайт или собранная страница): сеть, контексты, вызовы отрисовки, кадры, LCP, TBT.

Что меряет:
  * вес сети — по фактически переданным байтам (Playwright request.sizes().responseBodySize), а не по content-length: у
    сжатых на лету ответов (br/zstd, HTTP/2) content-length нет;
  * категория файла — по расширению, content-type, пути и сигнатуре первых байт (glTF, KTX2, Draco, Basis, EXR, HDR, PLY,
    WASM, OGG…): собственные бинарные форматы студий (.buf, .bin без расширения) иначе уходят в other;
  * контексты: перехват getContext (webgl/webgl2/webgpu/2d), transferControlToOffscreen (рендер в воркере — вызовы
    отрисовки главного потока тогда 0), navigator.gpu.requestAdapter;
  * вызовы отрисовки: WebGL/WebGL2 + WebGPU (GPURenderPassEncoder.draw*); время до первого 3D-кадра (первый кадр rAF с
    ≥ 1 вызовом) и таймлайн вызовов по секундам;
  * прокрутка колесом мыши (mouse.wheel) — работает и на сайтах с виртуальной прокруткой (Lenis, свой скролл);
  * LCP с элементом (тег, url), TBT до прокрутки и во время неё отдельно;
  * библиотеки: глобальные объекты, DOM, баннеры в консоли (Babylon, PlayCanvas, Pixi), сигнатуры в тексте JS; GSAP и
    ScrollTrigger — по рантайму (window.gsapVersions, свойство _gsap у элементов, .pin-spacer): бандл глобал gsap не ставит;
  * --no-3d — прогон «постер без 3D» для вклада 3D в TBT (gate_check.py --baseline): WebGL и WebGPU недоступны странице,
    3D-ассеты и декодеры (glTF, KTX2, Draco, Basis, HDR…) не грузятся; JS 3D-библиотеки, которую страница грузит без проверки
    возможностей, остаётся в обоих прогонах — ключ --block ШАБЛОН (регулярное выражение по URL, повтором) снимает и его;
  * WebGPU включён флагами (--enable-unsafe-webgpu --enable-features=Vulkan): без них requestAdapter() в headless
    возвращает null;
  * --mobile: дескриптор телефона и CPU — budgets.yaml site conditions.lab_mobile (Pixel 7, CPU ×4), UA — HeadlessChrome;
    --throttle — сеть того же условия (1,6 Мбит/с, RTT 150 мс); --reduced-motion: контекст с prefers-reduced-motion: reduce.
Замер времени — на тихой машине: зонд сам берёт общий тяжёлый замок и замок браузера на время работы браузера
(page_gates.heavy_lock через kbpaths.lock, реентерабельно по дереву процессов: зонд, запущенный из утилиты с теми же
замками, их не ждёт); --no-lock — без замков: ни тишины машины, ни очереди браузера. Автоматизация не маскируется.

Использование (код-репо — соседним чекаутом ../strategy/.claude/skills/design-deep-dive/scripts/3d/site_probe.py):
  site_probe.py --selftest            # локальная страница: GSAP по рантайму, WebGL, прогон --no-3d
  site_probe.py URL OUT_DIR [--mobile] [--throttle] [--wait 8000] [--steps 24] [--reduced-motion] [--quick]
                [--no-3d [--block ШАБЛОН …]] [--gpu gl|vulkan|swiftshader] [--no-webgpu] [--click SELECTOR [--click-timeout 30]]
                [--click-xy 0.5,0.5 [--click-delay 8000]] [--wait-until load|domcontentloaded|commit] [--timeout 180] [--no-lock]
Результат: OUT_DIR/probe[_mobile][_thr][_rm][_no3d][_quick].json, network[…].json, shot_*.png, sheet*.png; краткая сводка
в stdout. Ворота 3D по отчёту — gate_check.py.
"""
import contextlib, json, os, re, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402
kbpaths.use("site")
import page_gates as PG  # noqa: E402  условия замера и тишина машины (budgets.yaml site)

GPU_ARGS = {
    "gl": ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"],
    "vulkan": ["--use-angle=vulkan", "--enable-features=Vulkan", "--ignore-gpu-blocklist"],
    "swiftshader": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
}
WEBGPU_ARGS = ["--enable-unsafe-webgpu", "--enable-features=Vulkan"]
# «постер без 3D»: WebGL и WebGPU странице недоступны (страница уходит в запасной путь — постер), 3D-ассеты не грузятся
NO3D_INIT = r"""(() => { const gc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, ...a) { if (/webgl|webgpu/i.test(String(type))) return null; return gc.call(this, type, ...a); };
  try { if (HTMLCanvasElement.prototype.transferControlToOffscreen) HTMLCanvasElement.prototype.transferControlToOffscreen = undefined; } catch (e) {}
  try { Object.defineProperty(navigator, 'gpu', {get: () => undefined}); } catch (e) {} })();"""
NO3D_URL = (r"\.(glb|gltf|drc|ktx2|ktx|basis|hdr|exr|splat|ksplat|spz|sog|ply|usdz|splinecode|vrm|fbx|obj|buf)(\?|$)|"
            r"draco_(decoder|wasm)|basis_transcoder|meshopt_decoder|/(models?|meshes|geometr|gltf|glb|3d)/")

INIT = r"""(() => {
  if (window.__probe) return;
  const P = window.__probe = {cur: 0, frames: 0, dcFrames: [], rafT: [], firstDraw: null, perSec: {},
    ctx: [], offscreen: 0, gpuAdapterCalls: 0, gpuAdapterOk: 0, lcp: null, cls: 0, lt: [], console: []};
  const bump = () => { P.cur++; };
  const wrap = (proto, names) => { if (!proto) return; for (const n of names) { const f = proto[n]; if (typeof f !== 'function') continue;
    proto[n] = function (...a) { bump(); return f.apply(this, a); }; } };
  const gl = ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced', 'drawRangeElements', 'multiDrawElementsWEBGL', 'multiDrawArraysWEBGL'];
  wrap(window.WebGLRenderingContext && WebGLRenderingContext.prototype, gl);
  wrap(window.WebGL2RenderingContext && WebGL2RenderingContext.prototype, gl);
  wrap(window.GPURenderPassEncoder && GPURenderPassEncoder.prototype, ['draw', 'drawIndexed', 'drawIndirect', 'drawIndexedIndirect']);
  wrap(window.GPURenderBundleEncoder && GPURenderBundleEncoder.prototype, ['draw', 'drawIndexed']);
  const gc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, attrs) {
    const r = gc.call(this, type, attrs);
    try { if (!this.__ctxType && r) { this.__ctxType = type; P.ctx.push({type, w: this.width, h: this.height, t: Math.round(performance.now()),
      aa: attrs && attrs.antialias, alpha: attrs && attrs.alpha, pp: attrs && attrs.powerPreference}); } } catch (e) {}
    return r; };
  if (HTMLCanvasElement.prototype.transferControlToOffscreen) { const tc = HTMLCanvasElement.prototype.transferControlToOffscreen;
    HTMLCanvasElement.prototype.transferControlToOffscreen = function () { P.offscreen++; this.__ctxType = 'offscreen'; return tc.call(this); }; }
  if (navigator.gpu && navigator.gpu.requestAdapter) { const ra = navigator.gpu.requestAdapter.bind(navigator.gpu);
    navigator.gpu.requestAdapter = async (...a) => { P.gpuAdapterCalls++; const ad = await ra(...a); if (ad) P.gpuAdapterOk++; return ad; }; }
  const raf = window.requestAnimationFrame.bind(window);
  const loop = (t) => { const dc = P.cur; P.cur = 0; P.frames++; P.rafT.push(t); P.dcFrames.push(dc);
    if (dc > 0 && P.firstDraw === null) P.firstDraw = Math.round(t);
    const s = Math.floor(t / 1000); if (dc > (P.perSec[s] || 0)) P.perSec[s] = dc;
    if (P.rafT.length > 20000) { P.rafT.splice(0, 10000); P.dcFrames.splice(0, 10000); }
    raf(loop); };
  raf(loop);
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) { const el = e.element;
    P.lcp = {t: Math.round(e.startTime), size: e.size, tag: el ? el.tagName : null, url: (e.url || '').slice(0, 200),
      id: el && el.id ? el.id : null, cls: el && el.className && typeof el.className === 'string' ? el.className.slice(0, 80) : null}; } })
    .observe({type: 'largest-contentful-paint', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) P.cls += e.value; }).observe({type: 'layout-shift', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) P.lt.push([Math.round(e.startTime), Math.round(e.duration)]); }).observe({type: 'longtask', buffered: true}); } catch (e) {}
})();"""

DETECT = r"""(() => { const r = {};
  if (window.__THREE__) r.three = window.__THREE__;
  if (window.BABYLON) r.babylon = (window.BABYLON.Engine && BABYLON.Engine.Version) || true;
  if (window.pc && (window.pc.version || window.pc.Application)) r.playcanvas = window.pc.version || true;
  if (window.PIXI) r.pixi = window.PIXI.VERSION || true;
  if (customElements.get('model-viewer')) r.model_viewer = true;
  if (customElements.get('needle-engine')) r.needle = true;
  if (customElements.get('spline-viewer') || document.querySelector('spline-viewer')) r.spline_viewer = true;
  // GSAP — по рантайму: бандл глобал window.gsap не ставит; признаки — gsapVersions, _gsap у элементов, .pin-spacer
  const gv = Array.isArray(window.gsapVersions) ? window.gsapVersions.slice(0, 4).map(String) : [];
  let gt = 0; try { for (const el of document.querySelectorAll('body *')) { if (el._gsap) gt++; if (gt >= 500) break; } } catch (e) {}
  const pins = document.querySelectorAll('.pin-spacer').length;
  if (window.gsap || gv.length || gt || pins) { r.gsap = (window.gsap && window.gsap.version) || gv[0] || true; r.gsap_targets = gt; r.pin_spacers = pins; }
  if (window.ScrollTrigger || pins) r.scrolltrigger = true;
  if (window.lenis || document.documentElement.classList.contains('lenis') || document.querySelector('.lenis')) r.lenis = true;
  if (window.UnicornStudio) r.unicorn_studio = true;
  if (window.Webflow) r.webflow = true;
  if (document.querySelector('[data-framer-hydrate-v2], #__framer-badge-container, [data-framer-name]')) r.framer = true;
  if (window.__NEXT_DATA__ || self.__next_f) r.nextjs = true;
  if (window.__NUXT__ || window.useNuxtApp) r.nuxt = true;
  if (document.querySelector('astro-island')) r.astro = true;
  if (Object.keys(window).some(k => k.startsWith('__sveltekit'))) r.sveltekit = true;
  if (window.__VUE__) r.vue = true;
  if (window.__TheatreJS_CoreBundle) r.theatre = true;
  if (document.querySelector('lottie-player, dotlottie-player, dotlottie-wc')) r.lottie_el = true;
  if (document.querySelector('rive-canvas') ) r.rive_el = true;
  const P = window.__probe || {};
  r.canvases = [...document.querySelectorAll('canvas')].slice(0, 12).map(c => { const b = c.getBoundingClientRect(); const cs = getComputedStyle(c);
    return {w: c.width, h: c.height, css: [Math.round(b.width), Math.round(b.height)], ctx: c.__ctxType || null, pos: cs.position,
            vis: cs.visibility !== 'hidden' && cs.display !== 'none' && b.width > 0 && b.height > 0, z: cs.zIndex}; });
  r.ctx_created = (P.ctx || []).slice(0, 20); r.offscreen = P.offscreen || 0;
  r.gpu_adapter_calls = P.gpuAdapterCalls || 0; r.gpu_adapter_ok = P.gpuAdapterOk || 0;
  r.videos = [...document.querySelectorAll('video')].slice(0, 10).map(v => ({src: (v.currentSrc || v.src || '').slice(0, 160), w: v.videoWidth, h: v.videoHeight,
    autoplay: v.autoplay, loop: v.loop, muted: v.muted, poster: !!v.poster}));
  r.iframes = [...document.querySelectorAll('iframe')].slice(0, 10).map(f => (f.src || '').slice(0, 160));
  r.dom_text_chars = (document.body && document.body.innerText || '').length;
  r.h1 = [...document.querySelectorAll('h1')].slice(0, 3).map(h => h.innerText.slice(0, 100));
  r.title = document.title;
  r.meta_viewport = (document.querySelector('meta[name=viewport]') || {}).content || null;
  return r; })()"""

SIGS = {  # сигнатуры в тексте JS (переживают минификацию: строки ошибок, баннеры, URL)
    "three": [r"Multiple instances of Three\.js being imported", r"THREE\.WebGLRenderer", r"__THREE__"],
    "three_webgpu": [r"THREE\.WebGPURenderer", r"WebGPURenderer", r"WebGPUBackend", r"THREE\.TSL"],
    "r3f": [r"R3F: Hooks can only be used within the Canvas component", r"R3F: "],
    "drei": [r"@react-three/drei", r"MeshTransmissionMaterial", r"useGLTF"],
    "babylon": [r"Babylon\.js v", r"BABYLON\."],
    "playcanvas": [r"Powered by PlayCanvas", r"playcanvas"],
    "pixi": [r"PixiJS", r"pixi\.js"],
    "ogl": [r"\bogl\b"],
    "spline": [r"@splinetool", r"splinecode", r"prod\.spline\.design"],
    "gsap": [r"https://gsap\.com", r"greensock", r"GreenSock", r"gsap\.registerPlugin"],
    "scrolltrigger": [r"ScrollTrigger"],
    "lenis": [r"lenis-smooth", r"lenis-stopped", r"\blenis\b"],
    "theatre": [r"@theatre/core", r"TheatreJS", r"__TheatreJS"],
    "postprocessing": [r"EffectComposer", r"postprocessing"],
    "draco": [r"DRACOLoader", r"draco_decoder"],
    "meshopt": [r"MeshoptDecoder", r"meshopt_decoder", r"EXT_meshopt_compression"],
    "ktx2": [r"KTX2Loader", r"basis_transcoder", r"KHR_texture_basisu"],
    "gltf": [r"GLTFLoader", r"KHR_materials_", r"glTF"],
    "unicorn": [r"unicornstudio", r"UnicornStudio"],
    "rive": [r"@rive-app", r"rive\.wasm"],
    "lottie": [r"bodymovin", r"lottie"],
    "barba": [r"barba"],
    "swup": [r"swup"],
    "curtains": [r"curtainsjs", r"Curtains"],
    "vanta": [r"VANTA"],
    "shadergradient": [r"shadergradient"],
    "cobe": [r"cobe"],
    "globe_gl": [r"globe\.gl", r"three-globe"],
}

MAGIC = [(b"glTF", "model3d"), (b"\xabKTX 20\xbb", "texture3d"), (b"\xabKTX 11\xbb", "texture3d"), (b"DRACO", "model3d"),
         (b"sB", None), (b"\x76\x2f\x31\x01", "texture3d"), (b"#?RADIANCE", "texture3d"), (b"#?RGBE", "texture3d"),
         (b"ply\n", "model3d"), (b"\x00asm", "wasm"), (b"OggS", "audio"), (b"ID3", "audio"), (b"RIFF", None),
         (b"\x89PNG", "image"), (b"\xff\xd8\xff", "image"), (b"\x1a\x45\xdf\xa3", "video"), (b"GIF8", "image")]

EXT = [("model3d", (".glb", ".gltf", ".drc", ".splat", ".ksplat", ".spz", ".sog", ".ply", ".usdz", ".fbx", ".obj", ".buf", ".splinecode", ".riv", ".vrm", ".fbx")),
       ("texture3d", (".ktx2", ".basis", ".hdr", ".exr", ".ktx", ".dds")),
       ("image", (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg", ".ico")),
       ("video", (".mp4", ".webm", ".mov", ".m3u8", ".ts", ".m4s")),
       ("audio", (".mp3", ".ogg", ".wav", ".m4a", ".aac", ".opus", ".flac")),
       ("wasm", (".wasm",)), ("js", (".js", ".mjs", ".cjs")), ("css", (".css",)), ("font", (".woff2", ".woff", ".ttf", ".otf")),
       ("json", (".json",)), ("bin", (".bin", ".dat", ".data", ".raw", ".bytes", ".gz", ".br"))]


def categorize(url, ctype, rtype, head):
    u = url.split("?")[0].split("#")[0].lower()
    if head:
        for m, cat in MAGIC:
            if head.startswith(m):
                if m == b"RIFF":
                    return "image" if head[8:12] == b"WEBP" else ("audio" if head[8:12] == b"WAVE" else "bin")
                if m == b"sB":
                    if u.endswith(".basis"):
                        return "texture3d"
                    continue
                if cat:
                    return cat
        if len(head) >= 12 and head[4:8] == b"ftyp":
            brand = head[8:12]
            return "image" if brand in (b"avif", b"avis", b"heic", b"mif1") else "video"
    for cat, exts in EXT:
        if u.endswith(exts):
            if cat == "bin":
                return "model3d" if re.search(r"/(models?|meshes|geometr|gltf|glb|3d)/", u) else "bin"
            return cat
    ct = (ctype or "").lower()
    if "model/gltf" in ct: return "model3d"
    if ct.startswith("image/"): return "image"
    if ct.startswith("video/"): return "video"
    if ct.startswith("audio/"): return "audio"
    if "javascript" in ct or "ecmascript" in ct: return "js"
    if "wasm" in ct: return "wasm"
    if "font" in ct: return "font"
    if "css" in ct: return "css"
    if "json" in ct: return "json"
    if "html" in ct: return "html"
    if rtype in ("fetch", "xhr") and re.search(r"/(models?|meshes|geometr|gltf|glb|3d)/", u): return "model3d"
    if rtype == "media": return "video"
    return "other"


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def sheet(paths, out, maxw=720):
    try:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in paths]
        ims = [im.resize((maxw, int(im.height * maxw / im.width))) if im.width > maxw else im for im in ims]
        w = max(i.width for i in ims); h = max(i.height for i in ims)
        s = Image.new("RGB", (w * len(ims), h), (255, 255, 255))
        for i, im in enumerate(ims):
            s.paste(im, (i * w, 0))
        s.save(out)
        return out
    except Exception as e:
        return f"не собран: {e}"


def frame_diff(a_path, b_path, thr=8):
    """Доля пикселей (0..100 %), изменившихся больше чем на thr/255 хотя бы в одном канале — есть ли движение в покое."""
    try:
        from PIL import Image, ImageChops
        a = Image.open(a_path).convert("RGB"); b = Image.open(b_path).convert("RGB")
        if a.size != b.size:
            return None
        d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > thr else 0)
        hist = d.histogram()
        return round(100.0 * hist[255] / (a.size[0] * a.size[1]), 2)
    except Exception:
        return None


SELFTEST_HTML = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>site_probe selftest</title>
<style>body{margin:0;font:16px sans-serif} canvas{display:block}</style></head><body>
<h1>Проверка зонда</h1><canvas id="c" width="400" height="300"></canvas>
<div class="pin-spacer"><div id="pinned">закреплённый блок</div></div>
<script>window.gsapVersions = ["3.12.5"]; document.getElementById("pinned")._gsap = {id: 1};
fetch("model.glb").then(r => r.arrayBuffer()).catch(() => {});
const gl = document.getElementById("c").getContext("webgl");
if (gl) { const f = () => { gl.clearColor(0.2, 0.3, 0.4, 1); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.POINTS, 0, 1); requestAnimationFrame(f); };
  requestAnimationFrame(f); }</script></body></html>"""


def selftest():
    """Локальная страница через свой HTTP-сервер: GSAP по рантайму (gsapVersions, _gsap, .pin-spacer без window.gsap),
    контекст WebGL и вызовы отрисовки; прогон --no-3d — WebGL недоступен, 3D-ассет не грузится, файл отчёта _no3d."""
    import functools
    import http.server
    import socketserver
    import subprocess
    import tempfile
    import threading
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)
    src = open(os.path.abspath(__file__), encoding="utf-8").read().split("\ndef selftest")[0]
    check("в коде нет --disable-blink-features и своей строки UA", "--disable-blink-" not in src and "user_agent=" not in src)
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "index.html"), "w", encoding="utf-8") as f:
            f.write(SELFTEST_HTML)
        with open(os.path.join(td, "model.glb"), "wb") as f:
            f.write(b"glTF" + bytes(20000))
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *x):
                pass
        h = functools.partial(Quiet, directory=td)
        srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), h)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
        try:
            for extra, name in (([], "probe_quick.json"), (["--no-3d"], "probe_no3d_quick.json")):
                out = os.path.join(td, "out")
                r = subprocess.run([sys.executable, os.path.abspath(__file__), url, out, "--quick", "--wait", "600", "--gpu", "swiftshader",
                                    "--no-webgpu", *extra], capture_output=True, text=True, timeout=240, env=kbpaths.playwright_env())
                fp = os.path.join(out, name)
                st = json.load(open(fp, encoding="utf-8")) if os.path.exists(fp) else {}
                check(f"прогон {' '.join(extra) or 'с 3D'}: отчёт {name} (код {r.returncode}) {r.stderr[-200:] if not st else ''}", bool(st))
                if not st:
                    continue
                det = st.get("detected") or {}
                cat = (st.get("network") or {}).get("by_category") or {}
                ctx = [c.get("type") for c in det.get("ctx_created") or []]
                if not extra:
                    check("GSAP по рантайму: gsapVersions, _gsap и .pin-spacer без window.gsap",
                          det.get("gsap") == "3.12.5" and det.get("gsap_targets", 0) >= 1 and det.get("pin_spacers") == 1 and det.get("scrolltrigger"))
                    check("с 3D: контекст webgl и вызовы отрисовки, 3D-ассет загружен",
                          "webgl" in ctx and (st.get("idle") or {}).get("frames_with_draws", 0) > 0 and "model3d" in cat)
                else:
                    check("--no-3d: WebGL недоступен, 3D-ассет не загружен (запрос прерван)",
                          "webgl" not in ctx and "model3d" not in cat and (st.get("no_3d") or {}).get("aborted", 0) >= 1)
        finally:
            srv.shutdown()
    print("site_probe selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        sys.exit(selftest())
    if len(a) < 2 or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    url, out = a[0], os.path.abspath(a[1])
    os.makedirs(out, exist_ok=True)
    mobile, throttle, rm, no3d = "--mobile" in a, "--throttle" in a, "--reduced-motion" in a, "--no-3d" in a
    blocks = [a[i + 1] for i, x in enumerate(a) if x == "--block" and i + 1 < len(a)]
    wait = int(opt(a, "--wait", 8000)); steps = int(opt(a, "--steps", 24)); click = opt(a, "--click")
    nav_timeout = int(opt(a, "--timeout", 180)) * 1000
    suffix = ("_mobile" if mobile else "") + ("_thr" if throttle else "") + ("_rm" if rm else "") + ("_no3d" if no3d else "") \
        + ("_quick" if "--quick" in a and not rm else "")
    args = GPU_ARGS[opt(a, "--gpu", "gl")] + ([] if "--no-webgpu" in a else WEBGPU_ARGS)
    cond = PG.conditions()
    from playwright.sync_api import sync_playwright
    net, logs, sigs_found, js_seen = {}, [], {}, 0
    st = {"url": url, "mobile": mobile, "throttle": throttle, "reduced_motion": rm, "date": time.strftime("%Y-%m-%d %H:%M"),
          "chromium_args": args}
    if no3d:
        st["no_3d"] = {"webgl": "недоступен", "blocked_pattern": NO3D_URL + "".join("|" + x for x in blocks), "aborted": 0}
    lock = contextlib.nullcontext() if "--no-lock" in a else PG.heavy_lock(domains=("3d",))
    with lock, sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=args)
        st["browser"] = b.version
        if mobile:
            dev = PG.mobile_device(pw, cond)            # дескриптор budgets.yaml, UA — HeadlessChrome
            ctx = b.new_context(**dev, reduced_motion="reduce" if rm else "no-preference", locale="en-US")
        else:
            ctx = b.new_context(viewport={"width": cond["desktop"]["width"], "height": cond["desktop"]["height"]},
                                device_scale_factor=cond["desktop"]["dpr"], reduced_motion="reduce" if rm else "no-preference", locale="en-US")
        if no3d:
            ctx.add_init_script(NO3D_INIT)

            def _abort(route):
                st["no_3d"]["aborted"] += 1
                route.abort()
            ctx.route(re.compile(st["no_3d"]["blocked_pattern"], re.I), _abort)
        ctx.add_init_script(INIT)
        p = ctx.new_page()
        W, H = p.viewport_size["width"], p.viewport_size["height"]
        st["viewport"] = [W, H]

        def on_console(m):
            try:
                if m.type in ("error", "warning") or re.search(r"Babylon\.js v|PlayCanvas|PixiJS|three\.js|Needle Engine|THREE\.", m.text):
                    logs.append(f"{m.type}: {m.text[:300]}")
            except Exception:
                pass
        p.on("console", on_console)
        p.on("pageerror", lambda e: logs.append(f"pageerror: {str(e)[:300]}"))

        def on_finished(req):
            nonlocal js_seen
            try:
                resp = req.response()
                if resp is None:
                    return
                sz = req.sizes()
                enc = sz.get("responseBodySize", 0) or 0
                hdr = resp.headers
                ct = hdr.get("content-type", "")
                rtype = req.resource_type
                head, body_len = None, None
                need_body = rtype in ("fetch", "xhr", "other", "media") or re.search(r"\.(glb|gltf|bin|buf|drc|ktx2|basis|hdr|exr|splat|ply|spz|sog|wasm|splinecode|riv)(\?|$)", req.url.lower())
                if need_body and resp.status < 300 and enc < 60_000_000:
                    try:
                        body = resp.body(); head = body[:16]; body_len = len(body)
                    except Exception:
                        pass
                cat = categorize(req.url, ct, rtype, head)
                if cat == "js" and resp.status < 300 and js_seen < 120:
                    try:
                        txt = resp.text(); js_seen += 1
                        for k, pats in SIGS.items():
                            if k in sigs_found:
                                continue
                            for pat in pats:
                                if re.search(pat, txt):
                                    sigs_found[k] = pat; break
                    except Exception:
                        pass
                t = req.timing or {}
                key = f"{len(net)}"
                net[key] = {"url": req.url[:300], "status": resp.status, "type": ct[:60], "rtype": rtype, "cat": cat,
                            "enc_bytes": enc, "body_bytes": body_len, "encoding": hdr.get("content-encoding"),
                            "t_abs_end": (t.get("startTime", 0) + max(t.get("responseEnd", 0), 0)) if t else None}
            except Exception as e:
                logs.append(f"probe-net: {e}")
        p.on("requestfinished", on_finished)

        if throttle:
            cdp = ctx.new_cdp_session(p)
            cdp.send("Network.enable")
            cdp.send("Network.emulateNetworkConditions", PG.cdp_network(cond))
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": cond["mobile"]["cpu_slowdown"]})
        t0 = time.time()
        try:
            p.goto(url, wait_until=opt(a, "--wait-until", "load"), timeout=nav_timeout)
        except Exception as e:
            logs.append(f"goto: {str(e)[:200]}")
        st["load_event_sec"] = round(time.time() - t0, 2)
        if click:
            try:
                p.wait_for_selector(click, state="visible", timeout=int(opt(a, "--click-timeout", 30)) * 1000)
                p.wait_for_timeout(1500)
                p.click(click, timeout=5000); st["clicked"] = click
                st["clicked_at_sec"] = round(time.time() - t0, 2)
            except Exception as e:
                st["clicked"] = f"fail: {str(e)[:120]}"
        click_xy = opt(a, "--click-xy")
        if click_xy:
            try:
                p.wait_for_timeout(int(opt(a, "--click-delay", 8000)))
                x, y = (float(v) for v in click_xy.split(","))
                p.mouse.click(x * W, y * H); st["clicked_xy"] = click_xy
                st["clicked_at_sec"] = round(time.time() - t0, 2)
            except Exception as e:
                st["clicked_xy"] = f"fail: {str(e)[:120]}"
        p.wait_for_timeout(wait)
        st["settled_sec"] = round(time.time() - t0, 2)
        try:
            st["time_origin"] = p.evaluate("performance.timeOrigin")
        except Exception:
            st["time_origin"] = None
        try:
            st["nav"] = p.evaluate("""(() => { const n = performance.getEntriesByType('navigation')[0]; if (!n) return null;
              return {ttfb: Math.round(n.responseStart), dcl: Math.round(n.domContentLoadedEventEnd), load: Math.round(n.loadEventEnd),
                      transfer_kb: Math.round(n.transferSize / 1024)}; })()""")
        except Exception:
            st["nav"] = None
        # до прокрутки: простой 2 с
        try:
            p.evaluate("(() => { const P = window.__probe; P.idleFrom = P.dcFrames.length; P.idleT = P.rafT.length; })()")
            p.wait_for_timeout(2000)
            st["idle"] = p.evaluate("""(() => { const P = window.__probe; const dc = P.dcFrames.slice(P.idleFrom); const t = P.rafT.slice(P.idleT);
              const d = []; for (let i = 1; i < t.length; i++) d.push(t[i] - t[i - 1]); d.sort((x, y) => x - y); const s = dc.slice().sort((x, y) => x - y);
              return {frames: t.length, fps: d.length ? +(1000 / (d.reduce((x, y) => x + y, 0) / d.length)).toFixed(1) : null,
                      frame_ms_p95: d.length ? +d[Math.floor(d.length * 0.95)].toFixed(1) : null,
                      dc_median: s.length ? s[Math.floor(s.length / 2)] : 0, dc_max: s.length ? s[s.length - 1] : 0,
                      frames_with_draws: dc.filter(x => x > 0).length}; })()""")
        except Exception as e:
            st["idle"] = {"error": str(e)[:200]}
        try:
            st["detected"] = p.evaluate(DETECT)
        except Exception as e:
            st["detected"] = {"error": str(e)[:200]}
        try:
            st["vitals_pre_scroll"] = p.evaluate("""(() => { const P = window.__probe; let tbt = 0; for (const [s, d] of P.lt) tbt += Math.max(0, d - 50);
              return {lcp: P.lcp, cls: +P.cls.toFixed(3), longtasks: P.lt.length, tbt_ms: tbt, longest_task_ms: P.lt.reduce((m, x) => Math.max(m, x[1]), 0),
                      first_draw_ms: P.firstDraw}; })()""")
        except Exception as e:
            st["vitals_pre_scroll"] = {"error": str(e)[:200]}
        shots = []
        fp = os.path.join(out, f"shot{suffix}_0.png")
        try:
            p.screenshot(path=fp); shots.append(fp)
            p.wait_for_timeout(1000)
            fp2 = os.path.join(out, f"shot{suffix}_idle1s.png"); p.screenshot(path=fp2)
            st["idle_motion_pct"] = frame_diff(fp, fp2)
        except Exception as e:
            logs.append(f"shot: {e}")
        if not rm and "--quick" not in a:
            # прокрутка колесом
            try:
                total_h = p.evaluate("Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0) - innerHeight")
            except Exception:
                total_h = 0
            st["doc_scrollable_px"] = total_h
            native = total_h > H * 0.5
            delta = max(200, int(total_h / steps)) if native else 450
            st["scroll_mode"] = "native" if native else "virtual/none"
            try:
                p.mouse.move(W / 2, H / 2)
                p.evaluate("(() => { const P = window.__probe; P.scFrom = P.dcFrames.length; P.scT = P.rafT.length; P.ltFrom = P.lt.length; })()")
                marks = {round(steps / 3), round(2 * steps / 3), steps}
                ys = []
                for s in range(1, steps + 1):
                    p.mouse.wheel(0, delta); p.wait_for_timeout(120)
                    if s in marks:
                        p.wait_for_timeout(500)
                        fp = os.path.join(out, f"shot{suffix}_{len(shots)}.png")
                        p.screenshot(path=fp); shots.append(fp)
                    ys.append(p.evaluate("Math.round(scrollY)"))
                st["scroll_y_trace"] = ys[:: max(1, len(ys) // 8)]
                st["scroll"] = p.evaluate("""(() => { const P = window.__probe; const dc = P.dcFrames.slice(P.scFrom); const t = P.rafT.slice(P.scT);
                  const d = []; for (let i = 1; i < t.length; i++) d.push(t[i] - t[i - 1]); const ds = d.slice().sort((x, y) => x - y);
                  const s = dc.slice().sort((x, y) => x - y); let tbt = 0; const lt = P.lt.slice(P.ltFrom); for (const [a, b] of lt) tbt += Math.max(0, b - 50);
                  return {frames: t.length, fps: d.length ? +(1000 / (d.reduce((x, y) => x + y, 0) / d.length)).toFixed(1) : null,
                          frame_ms_p95: ds.length ? +ds[Math.floor(ds.length * 0.95)].toFixed(1) : null, frame_ms_max: ds.length ? +ds[ds.length - 1].toFixed(1) : null,
                          jank_frames_over_50ms: d.filter(x => x > 50).length,
                          dc_median: s.length ? s[Math.floor(s.length / 2)] : 0, dc_p90: s.length ? s[Math.floor(s.length * 0.9)] : 0, dc_max: s.length ? s[s.length - 1] : 0,
                          longtasks: lt.length, tbt_ms: tbt}; })()""")
            except Exception as e:
                st["scroll"] = {"error": str(e)[:200]}
        try:
            st["draws_per_sec_max"] = p.evaluate("window.__probe.perSec")
            st["js_heap_mb"] = round(p.evaluate("performance.memory ? performance.memory.usedJSHeapSize : 0") / 1e6, 1)
            st["detected_after"] = p.evaluate("({ctx: (window.__probe.ctx || []).length, offscreen: window.__probe.offscreen, three: window.__THREE__ || null})")
        except Exception:
            pass
        st["console"] = logs[:60]
        st["console_errors"] = len([l for l in logs if l.startswith(("error", "pageerror"))])
        b.close()
    items = list(net.values())
    by = {}
    for n in items:
        by.setdefault(n["cat"], [0, 0, 0])
        by[n["cat"]][0] += 1; by[n["cat"]][1] += n["enc_bytes"]; by[n["cat"]][2] += (n["body_bytes"] or 0)
    st["network"] = {"requests": len(items), "transfer_kb": round(sum(n["enc_bytes"] for n in items) / 1024, 1),
                     "by_category": {k: {"n": v[0], "transfer_kb": round(v[1] / 1024, 1), "decoded_kb_known": round(v[2] / 1024, 1)}
                                     for k, v in sorted(by.items(), key=lambda kv: -kv[1][1])},
                     "heaviest": sorted(items, key=lambda n: -n["enc_bytes"])[:15],
                     "last_3d_response_ms": (round(max([n["t_abs_end"] or 0 for n in items if n["cat"] in ("model3d", "texture3d")] or [0]) - st["time_origin"])
                                             if st.get("time_origin") and any(n["cat"] in ("model3d", "texture3d") for n in items) else None)}
    st["js_signatures"] = sigs_found
    st["sheet"] = sheet(shots, os.path.join(out, f"sheet{suffix}.png")) if shots else None
    st["shots"] = shots
    json.dump(items, open(os.path.join(out, f"network{suffix}.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(st, open(os.path.join(out, f"probe{suffix}.json"), "w"), ensure_ascii=False, indent=1)
    d = st.get("detected", {}) or {}
    short = {"url": url, "mode": suffix or "desktop", "load_event_sec": st.get("load_event_sec"), "nav": st.get("nav"),
             "three": d.get("three"), "libs": {k: v for k, v in d.items() if k not in ("canvases", "ctx_created", "videos", "iframes", "h1", "title", "meta_viewport", "dom_text_chars") and v},
             "js_signatures": list(sigs_found), "canvases": d.get("canvases"), "ctx_created": d.get("ctx_created"),
             "idle": st.get("idle"), "vitals_pre_scroll": st.get("vitals_pre_scroll"), "scroll_mode": st.get("scroll_mode"),
             "scroll": st.get("scroll"), "network": {k: st["network"][k] for k in ("requests", "transfer_kb", "by_category", "last_3d_response_ms")},
             "top5": [(n["cat"], round(n["enc_bytes"] / 1024), n["url"][:110]) for n in st["network"]["heaviest"][:5]],
             "console_errors": st["console_errors"], "js_heap_mb": st.get("js_heap_mb"), "sheet": st["sheet"]}
    print(json.dumps(short, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
