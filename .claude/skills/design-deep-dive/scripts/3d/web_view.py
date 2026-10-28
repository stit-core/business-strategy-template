#!/usr/bin/env python3
"""Проверка 3D в браузере: GLB в three.js или готовая страница — через headless Chromium на реальной видеокарте.

САМОПРОВЕРКА
    python3 web_view.py --selftest     # пути web_stats.json от папки модели (без браузера); режим страницы на локальной
                                       # папке: GSAP по рантайму

РЕЖИМ МОДЕЛИ
    python3 web_view.py model.glb OUT_DIR [--three 0.186.0] [--views 4|turntable:8] [--size 1200x800]
        [--tone agx|neutral|aces|none] [--exposure 1.0] [--env room|none|file.hdr] [--bg #RRGGBB|transparent]
        [--anim] [--frames 120] [--gpu gl|vulkan|swiftshader] [--no-lock]
    Грузит модель через GLTFLoader (+ DRACOLoader, KTX2Loader, MeshoptDecoder с jsDelivr той же версии three),
    кадрирует по Box3, снимает ракурсы (та же конвенция, что render_views.py: азимут 0 — вид спереди; Blender −Y
    становится +Z в glTF), собирает web_stats.json: время загрузки, ревизия three, строка GPU, draw calls и
    треугольники из renderer.info, число мешей/материалов/текстур, максимальный размер текстуры, extensionsUsed,
    анимации (имя, длительность, число треков), габариты; среднее и p95 время кадра (render + gl.finish) за --frames.
    --anim: проигрывает все клипы и снимает кадры на 0/25/50/75 % самого длинного.
    Скриншоты: OUT_DIR/web_view_<n>.png, контактный лист OUT_DIR/web_sheet.png. Пути в web_stats.json (model,
    views[].file, anim_frames[].file, sheet) — от папки модели (у рецептов базы — папка примера), а не путь машины.

РЕЖИМ СТРАНИЦЫ
    python3 web_view.py --page path/to/index.html OUT_DIR [--size 1440x900] [--mobile] [--scroll 0,0.33,0.66,1]
        [--wait 2000] [--frames 120] [--gpu gl]
    Раздаёт папку страницы локальным сервером (свободный порт), открывает, ждёт window.__ready === true (если страница
    его выставляет) или --wait мс, снимает экран на каждой доле прокрутки, считает draw calls за кадр (перехват
    drawElements/drawArrays/…Instanced в WebGL и WebGL2 — работает для three, R3F, Babylon, PlayCanvas), FPS
    по requestAnimationFrame во время плавной прокрутки, ошибки консоли, число <canvas>, JS heap.
    --mobile: 390×844, deviceScaleFactor 3, touch.

РЕЖИМ ЖИВОГО САЙТА
    python3 web_view.py --url https://example.com OUT_DIR [--size 1440x900] [--mobile] [--scroll 0,0.5,1]
        [--wait 6000] [--throttle] [--gpu gl]
    То же, что режим страницы, плюс: журнал сети (вес по категориям: 3D-модели .glb/.gltf/.bin/.drc,
    текстуры .ktx2/.basis/.hdr/.exr, картинки, видео, JS, WASM, шрифты; топ-20 самых тяжёлых ответов),
    определение движков и библиотек (window.__THREE__ → ревизия three.js, BABYLON, PlayCanvas, Spline, model-viewer,
    Needle Engine, Lenis, Unicorn Studio, Webflow, Framer; GSAP и ScrollTrigger — по рантайму: window.gsapVersions,
    свойство _gsap у элементов, .pin-spacer — бандл глобал gsap не ставит), LCP/CLS/долгие задачи через PerformanceObserver.
    --throttle: CPU и сеть телефона лаборатории (budgets.yaml site conditions.lab_mobile: CPU ×4, 150 мс RTT, 1,6 Мбит/с)
    через CDP — ориентир для мобильного первого экрана. Сайт открывается как есть: куки-баннеры и заглушки видны на
    скриншотах.

Замер кадров — на тихой машине: утилита сама берёт общий тяжёлый замок и замок браузера на время работы браузера
(page_gates.heavy_lock через kbpaths.lock, реентерабельно по дереву процессов: утилита, запущенная из утилиты с теми же
замками, их не ждёт); --no-lock — без замков: ни тишины машины, ни очереди браузера. Код репозитория запускает утилиту
соседним чекаутом ../strategy/.claude/skills/design-deep-dive/scripts/3d/web_view.py.

GPU: по умолчанию --use-angle=gl (видеокарта машины через ANGLE и OpenGL). swiftshader — программный, для сравнения.
Время кадра в режиме модели — CPU-время render() + gl.finish(); ANGLE в headless может не ждать GPU, поэтому
это ориентир для сравнения вариантов между собой, а не бенчмарк устройства. FPS в режиме страницы — по
requestAnimationFrame (упирается в 60 при vsync).
"""
import contextlib, functools, http.server, json, os, shutil, socketserver, sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import kbpaths  # noqa: E402
kbpaths.use("site")
import page_gates as PG  # noqa: E402  условия замера и тишина машины (budgets.yaml site)

GPU_ARGS = {
    "gl": ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"],
    "vulkan": ["--use-angle=vulkan", "--enable-features=Vulkan", "--ignore-gpu-blocklist"],
    "swiftshader": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
}

VIEWER = r"""<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;height:100%;background:__BGCSS__;overflow:hidden}canvas{display:block}</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@__VER__/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@__VER__/examples/jsm/"}}</script></head><body>
<script type="module">
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {KTX2Loader} from 'three/addons/loaders/KTX2Loader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const CFG = __CFG__;
const W = CFG.w, H = CFG.h;
const renderer = new THREE.WebGLRenderer({antialias: true, alpha: CFG.bg === 'transparent', preserveDrawingBuffer: true});
renderer.setPixelRatio(1); renderer.setSize(W, H); document.body.appendChild(renderer.domElement);
renderer.toneMapping = {agx: THREE.AgXToneMapping, neutral: THREE.NeutralToneMapping, aces: THREE.ACESFilmicToneMapping, none: THREE.NoToneMapping}[CFG.tone] ?? THREE.AgXToneMapping;
renderer.toneMappingExposure = CFG.exposure;
const scene = new THREE.Scene();
if (CFG.bg !== 'transparent') scene.background = new THREE.Color(CFG.bg); else renderer.setClearColor(0x000000, 0);
const pmrem = new THREE.PMREMGenerator(renderer);
async function setupEnv() {
  if (CFG.env === 'room') scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  else if (CFG.env && CFG.env !== 'none') {
    let Loader;
    try { Loader = (await import('three/addons/loaders/HDRLoader.js')).HDRLoader; }
    catch (e) { Loader = (await import('three/addons/loaders/RGBELoader.js')).RGBELoader; }
    const tex = await new Loader().loadAsync(CFG.env); tex.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = tex;
  } else {
    scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.5));
    const d = new THREE.DirectionalLight(0xffffff, 2.5); d.position.set(3, 5, 4); scene.add(d);
  }
}
const gl = renderer.getContext(); const dbg = gl.getExtension('WEBGL_debug_renderer_info');
const info = {three: THREE.REVISION, gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'n/a', webgl2: renderer.capabilities.isWebGL2};
const draco = new DRACOLoader().setDecoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/draco/gltf/`);
const ktx2 = new KTX2Loader().setTranscoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/basis/`).detectSupport(renderer);
const loader = new GLTFLoader().setDRACOLoader(draco).setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
const camera = new THREE.PerspectiveCamera(CFG.fov, W / H, 0.01, 1000);
let mixer = null, clips = [], center = new THREE.Vector3(), radius = 1;
window.__api = {
  view(az, el) {
    const a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el);
    const d = radius / Math.sin(THREE.MathUtils.degToRad(CFG.fov) / 2) * 1.08;
    camera.position.set(center.x + d * Math.sin(a) * Math.cos(e), center.y + d * Math.sin(e), center.z + d * Math.cos(a) * Math.cos(e));
    camera.near = Math.max(d - radius * 3, radius * 0.01); camera.far = d + radius * 4; camera.updateProjectionMatrix();
    camera.lookAt(center); renderer.render(scene, camera);
    return {calls: renderer.info.render.calls, triangles: renderer.info.render.triangles};
  },
  animAt(frac) {
    if (!mixer) return null; const dur = Math.max(...clips.map(c => c.duration));
    mixer.setTime(dur * frac); renderer.render(scene, camera); return dur * frac;
  },
  frameTimes(n) {
    const ts = []; let az = 0;
    for (let i = 0; i < n; i++) { const t0 = performance.now(); az += 360 / n; this.view(az, 20); gl.finish(); ts.push(performance.now() - t0); }
    ts.sort((a, b) => a - b);
    return {avg_ms: +(ts.reduce((s, x) => s + x, 0) / n).toFixed(2), p95_ms: +ts[Math.floor(n * 0.95)].toFixed(2), frames: n};
  }
};
(async () => {
  try {
    await setupEnv();
    const t0 = performance.now();
    const gltf = await loader.loadAsync(CFG.model);
    info.load_ms = +(performance.now() - t0).toFixed(0);
    scene.add(gltf.scene);
    const box = new THREE.Box3().setFromObject(gltf.scene); box.getCenter(center);
    const size = box.getSize(new THREE.Vector3()); radius = Math.max(size.length() / 2, 1e-4);
    info.bbox_size = size.toArray().map(v => +v.toFixed(4));
    let meshes = 0; const mats = new Set(), texs = new Set(); let maxTex = 0;
    gltf.scene.traverse(o => { if (o.isMesh) { meshes++; (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => { mats.add(m);
      for (const k in m) { const v = m[k]; if (v && v.isTexture) { texs.add(v); const im = v.image; if (im && im.width) maxTex = Math.max(maxTex, im.width, im.height); } } }); } });
    Object.assign(info, {meshes, materials: mats.size, textures: texs.size, max_texture_px: maxTex,
      material_types: [...new Set([...mats].map(m => m.type))],
      extensionsUsed: gltf.parser.json.extensionsUsed || [],
      animations: gltf.animations.map(c => ({name: c.name, duration: +c.duration.toFixed(3), tracks: c.tracks.length}))});
    clips = gltf.animations;
    if (CFG.anim && clips.length) { mixer = new THREE.AnimationMixer(gltf.scene); clips.forEach(c => mixer.clipAction(c).play()); }
    renderer.compile(scene, camera);
    window.__info = info; window.__done = true;
  } catch (e) { window.__err = String(e && e.stack || e); window.__done = true; }
})();
</script></body></html>"""

PAGE_INIT = r"""(() => {
  const st = window.__perf = {frames: 0, drawCallsFrame: [], cur: 0, t0: 0, rafTimes: []};
  const wrap = (proto, names) => { if (!proto) return; for (const n of names) { const f = proto[n]; if (!f) continue;
    proto[n] = function (...a) { st.cur++; return f.apply(this, a); }; } };
  const names = ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced', 'drawRangeElements'];
  wrap(window.WebGLRenderingContext && WebGLRenderingContext.prototype, names);
  wrap(window.WebGL2RenderingContext && WebGL2RenderingContext.prototype, names);
  const raf = window.requestAnimationFrame.bind(window);
  const loop = (t) => { if (st.cur) st.drawCallsFrame.push(st.cur); st.cur = 0; st.frames++; st.rafTimes.push(t); raf(loop); };
  raf(loop);
  st.lcp = 0; st.cls = 0; st.longtasks = 0; st.tbt = 0;
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) st.lcp = e.startTime; }).observe({type: 'largest-contentful-paint', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) st.cls += e.value; }).observe({type: 'layout-shift', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) { st.longtasks++; st.tbt += Math.max(0, e.duration - 50); } }).observe({type: 'longtask', buffered: true}); } catch (e) {}
})();"""

DETECT = r"""(() => { const r = {};
  if (window.__THREE__) r.three = window.__THREE__;
  if (window.BABYLON && BABYLON.Engine) r.babylon = BABYLON.Engine.Version || true;
  if (window.pc && window.pc.version) r.playcanvas = window.pc.version;
  if (customElements.get('model-viewer')) r.model_viewer = true;
  if (customElements.get('needle-engine')) r.needle = true;
  // GSAP — по рантайму: бандл глобал window.gsap не ставит; признаки — gsapVersions, _gsap у элементов, .pin-spacer
  const gv = Array.isArray(window.gsapVersions) ? window.gsapVersions.slice(0, 4).map(String) : [];
  let gt = 0; try { for (const el of document.querySelectorAll('body *')) { if (el._gsap) gt++; if (gt >= 500) break; } } catch (e) {}
  const pins = document.querySelectorAll('.pin-spacer').length;
  if (window.gsap || gv.length || gt || pins) { r.gsap = (window.gsap && window.gsap.version) || gv[0] || true; r.gsap_targets = gt; r.pin_spacers = pins; }
  if (window.ScrollTrigger || pins) r.scrolltrigger = true;
  if (window.lenis || document.documentElement.classList.contains('lenis')) r.lenis = true;
  if (window.UnicornStudio) r.unicorn_studio = true;
  if (window.Webflow) r.webflow = true;
  if (document.querySelector('[data-framer-hydrate-v2], #__framer-badge-container') || window.__framer_importFromPackage) r.framer = true;
  const srcs = [...document.scripts].map(s => s.src).filter(Boolean);
  if (srcs.some(u => /spline/.test(u)) || document.querySelector('spline-viewer')) r.spline = true;
  r.canvases = [...document.querySelectorAll('canvas')].map(c => ({w: c.width, h: c.height,
    ctx: c.__ctxType || null})).slice(0, 10);
  return r; })()"""

CATS = [("model3d", (".glb", ".gltf", ".bin", ".drc", ".splat", ".ply", ".spz", ".usdz", ".fbx", ".obj")),
        ("texture3d", (".ktx2", ".basis", ".hdr", ".exr", ".ktx")),
        ("image", (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg")),
        ("video", (".mp4", ".webm", ".mov", ".m3u8", ".ts")),
        ("wasm", (".wasm",)), ("js", (".js", ".mjs")), ("font", (".woff2", ".woff", ".ttf", ".otf")),
        ("json", (".json",))]


def categorize(url, ctype):
    u = url.split("?")[0].split("#")[0].lower()
    for cat, exts in CATS:
        if u.endswith(exts):
            return cat
    ct = (ctype or "").lower()
    if "model/gltf" in ct: return "model3d"
    if ct.startswith("image/"): return "image"
    if ct.startswith("video/"): return "video"
    if "javascript" in ct: return "js"
    if "wasm" in ct: return "wasm"
    if "font" in ct: return "font"
    return "other"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve(directory):
    handler = functools.partial(QuietHandler, directory=directory)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def portable_stats(stats, base):
    """Пути отчёта режима модели — от папки модели base (у рецептов базы — папка примера), а не путь машины: model,
    views[].file, anim_frames[].file, sheet. Строка без абсолютного пути (сообщение «не собран: …») — как есть."""
    def rel(p):
        return os.path.relpath(p, base).replace(os.sep, "/") if isinstance(p, str) and os.path.isabs(p) else p
    out = dict(stats, model=rel(stats.get("model")))
    for key in ("views", "anim_frames"):
        if key in stats:
            out[key] = [dict(v, file=rel(v.get("file"))) for v in stats[key]]
    if "sheet" in stats:
        out["sheet"] = rel(stats["sheet"])
    return out


def sheet(paths, out):
    try:
        from PIL import Image
        ims = [Image.open(p).convert("RGBA") for p in paths]
        cols = min(len(ims), 4); rows = (len(ims) + cols - 1) // cols
        w, h = ims[0].size
        s = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
        for i, im in enumerate(ims):
            s.paste(im, ((i % cols) * w, (i // cols) * h))
        s.save(out)
        return out
    except Exception as e:
        return f"не собран: {e}"


def model_mode(a):
    from playwright.sync_api import sync_playwright
    model, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    os.makedirs(out, exist_ok=True)
    ver = opt(a, "--three", "0.186.0")
    w, h = map(int, opt(a, "--size", "1200x800").split("x"))
    views = opt(a, "--views", "4")
    if views.startswith("turntable"):
        n = int(views.split(":")[1]) if ":" in views else 8
        vlist = [(i * 360.0 / n, 20.0) for i in range(n)]
    elif views == "6":
        vlist = [(35, 20), (0, 5), (90, 5), (200, 35), (0, 85), (300, -25)]
    else:
        vlist = [(35, 20), (0, 5), (90, 5), (200, 35)]
    env = opt(a, "--env", "room")
    tmp = tempfile.mkdtemp(prefix="webview_")
    shutil.copy(model, os.path.join(tmp, os.path.basename(model)))
    if model.lower().endswith(".gltf"):  # внешние .bin и текстуры рядом
        src = os.path.dirname(model)
        for fn in os.listdir(src):
            if fn != os.path.basename(model) and os.path.isfile(os.path.join(src, fn)):
                shutil.copy(os.path.join(src, fn), os.path.join(tmp, fn))
    if env not in ("room", "none"):
        shutil.copy(os.path.abspath(env), os.path.join(tmp, os.path.basename(env))); env = os.path.basename(env)
    bg = opt(a, "--bg", "#d4d4d8")
    cfg = {"ver": ver, "w": w, "h": h, "model": os.path.basename(model), "tone": opt(a, "--tone", "agx"),
           "exposure": float(opt(a, "--exposure", 1.0)), "env": env, "bg": bg, "fov": 40, "anim": "--anim" in a}
    html = VIEWER.replace("__VER__", ver).replace("__CFG__", json.dumps(cfg)).replace(
        "__BGCSS__", "transparent" if bg == "transparent" else bg)
    open(os.path.join(tmp, "index.html"), "w", encoding="utf-8").write(html)
    httpd, port = serve(tmp)
    stats = {"model": model, "file_kb": round(os.path.getsize(model) / 1024, 1), "config": cfg}
    shots = []
    lock = contextlib.nullcontext() if "--no-lock" in a else PG.heavy_lock(domains=("3d",))
    try:
        with lock, sync_playwright() as pw:
            b = pw.chromium.launch(headless=True, args=GPU_ARGS[opt(a, "--gpu", "gl")])
            p = b.new_page(viewport={"width": w, "height": h})
            logs = []
            p.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            p.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))
            p.goto(f"http://127.0.0.1:{port}/index.html")
            p.wait_for_function("window.__done === true", timeout=120000)
            err = p.evaluate("window.__err || null")
            if err:
                stats["error"] = err
            else:
                stats["info"] = p.evaluate("window.__info")
                stats["views"] = []
                for i, (az, el) in enumerate(vlist):
                    r = p.evaluate(f"window.__api.view({az}, {el})")
                    fp = os.path.join(out, f"web_view_{i}_az{int(az)}_el{int(el)}.png")
                    p.screenshot(path=fp, omit_background=(bg == "transparent")); shots.append(fp)
                    stats["views"].append({"az": az, "el": el, **r, "file": fp})
                if cfg["anim"] and stats["info"].get("animations"):
                    p.evaluate(f"window.__api.view({vlist[0][0]}, {vlist[0][1]})")
                    stats["anim_frames"] = []
                    for frac in (0, 0.25, 0.5, 0.75):
                        t = p.evaluate(f"window.__api.animAt({frac})")
                        fp = os.path.join(out, f"web_anim_{int(frac * 100):03d}.png")
                        p.screenshot(path=fp, omit_background=(bg == "transparent")); shots.append(fp)
                        stats["anim_frames"].append({"t": t, "file": fp})
                stats["frame_time"] = p.evaluate(f"window.__api.frameTimes({int(opt(a, '--frames', 120))})")
            stats["console"] = logs[:50]
            b.close()
    finally:
        httpd.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
    if shots:
        stats["sheet"] = sheet(shots, os.path.join(out, "web_sheet.png"))
    stats = portable_stats(stats, os.path.dirname(model))
    json.dump(stats, open(os.path.join(out, "web_stats.json"), "w"), ensure_ascii=False, indent=1)
    summary = {k: stats.get(k) for k in ("file_kb", "error", "frame_time", "sheet")}
    summary["info"] = stats.get("info"); summary["console_errors"] = [l for l in stats.get("console", []) if l.startswith(("error", "pageerror"))][:10]
    print(json.dumps(summary, ensure_ascii=False, indent=1)); print("STATS", os.path.join(out, "web_stats.json"))


def page_mode(a):
    from playwright.sync_api import sync_playwright
    url_mode = "--url" in a
    target = opt(a, "--url") if url_mode else os.path.abspath(opt(a, "--page"))
    valued = ("--size", "--scroll", "--wait", "--frames", "--gpu", "--page", "--url")
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in valued)]
    out = os.path.abspath(pos[0])
    os.makedirs(out, exist_ok=True)
    mobile = "--mobile" in a
    w, h = (390, 844) if mobile else tuple(map(int, opt(a, "--size", "1440x900").split("x")))
    fracs = [float(x) for x in opt(a, "--scroll", "0,0.33,0.66,1").split(",")]
    wait = int(opt(a, "--wait", 6000 if url_mode else 2000))
    httpd, port = (None, None) if url_mode else serve(os.path.dirname(target))
    stats = {"target": target, "viewport": [w, h], "mobile": mobile, "throttle": "--throttle" in a, "shots": []}
    net = []
    lock = contextlib.nullcontext() if "--no-lock" in a else PG.heavy_lock(domains=("3d",))
    try:
        with lock, sync_playwright() as pw:
            b = pw.chromium.launch(headless=True, args=GPU_ARGS[opt(a, "--gpu", "gl")])
            ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=3 if mobile else 1,
                                is_mobile=mobile, has_touch=mobile)
            p = ctx.new_page(); p.add_init_script(PAGE_INIT)
            logs = []
            p.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            p.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))

            def on_resp(r):
                try:
                    hdr = r.headers
                    ln = int(hdr.get("content-length") or 0)
                    ct = hdr.get("content-type", "")
                    cat = categorize(r.url, ct)
                    if not ln and cat in ("model3d", "texture3d", "wasm"):
                        try:
                            ln = len(r.body())
                        except Exception:
                            pass
                    net.append({"url": r.url[:300], "status": r.status, "type": ct[:60], "bytes": ln, "cat": cat,
                                "encoding": hdr.get("content-encoding")})
                except Exception:
                    pass
            p.on("response", on_resp)
            if "--throttle" in a:
                cdp = ctx.new_cdp_session(p)
                cdp.send("Network.enable")
                cond = PG.conditions()
                cdp.send("Network.emulateNetworkConditions", PG.cdp_network(cond))
                cdp.send("Emulation.setCPUThrottlingRate", {"rate": cond["mobile"]["cpu_slowdown"]})
            t0 = time.time()
            dest = target if url_mode else f"http://127.0.0.1:{port}/{os.path.basename(target)}"
            try:
                p.goto(dest, wait_until="load", timeout=180000)
            except Exception as e:
                logs.append(f"goto: {e}")
            try:
                p.wait_for_function("window.__ready === true", timeout=wait)
                stats["ready_flag"] = True
            except Exception:
                p.wait_for_timeout(wait); stats["ready_flag"] = False
            stats["load_sec"] = round(time.time() - t0, 2)
            stats["canvases"] = p.evaluate("document.querySelectorAll('canvas').length")
            try:
                stats["detected"] = p.evaluate(DETECT)
            except Exception as e:
                stats["detected"] = {"error": str(e)}
            stats["web_vitals_like"] = p.evaluate("({lcp_ms: Math.round(window.__perf.lcp), cls: +window.__perf.cls.toFixed(3), longtasks: window.__perf.longtasks, tbt_ms: Math.round(window.__perf.tbt)})")
            stats["gpu"] = p.evaluate("""(() => { const c = document.createElement('canvas'); const g = c.getContext('webgl2') || c.getContext('webgl');
                if (!g) return 'no webgl'; const d = g.getExtension('WEBGL_debug_renderer_info'); return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'n/a'; })()""")
            total_h = p.evaluate("document.documentElement.scrollHeight - innerHeight")
            p.evaluate("window.__perf.drawCallsFrame = []; window.__perf.rafTimes = []")
            for i, f in enumerate(fracs):
                p.evaluate(f"window.scrollTo(0, {int(total_h * f)})"); p.wait_for_timeout(700)
                fp = os.path.join(out, f"page_{i}_scroll{int(f * 100):03d}.png"); p.screenshot(path=fp)
                stats["shots"].append(fp)
            # плавная прокрутка для FPS
            p.evaluate("window.scrollTo(0, 0)"); p.wait_for_timeout(300)
            p.evaluate("window.__perf.drawCallsFrame = []; window.__perf.rafTimes = []")
            steps = 60
            for s in range(steps + 1):
                p.evaluate(f"window.scrollTo(0, {int(total_h * s / steps)})"); p.wait_for_timeout(16)
            perf = p.evaluate("""(() => { const s = window.__perf; const t = s.rafTimes; const d = [];
                for (let i = 1; i < t.length; i++) d.push(t[i] - t[i - 1]); d.sort((a, b) => a - b);
                const dc = s.drawCallsFrame.slice().sort((a, b) => a - b);
                return {frames: t.length, fps_avg: d.length ? +(1000 / (d.reduce((x, y) => x + y, 0) / d.length)).toFixed(1) : null,
                        frame_ms_p95: d.length ? +d[Math.floor(d.length * 0.95)].toFixed(1) : null,
                        drawcalls_per_frame_median: dc.length ? dc[Math.floor(dc.length / 2)] : 0,
                        drawcalls_per_frame_max: dc.length ? dc[dc.length - 1] : 0}; })()""")
            stats["scroll_perf"] = perf
            try:
                stats["js_heap_mb"] = round(p.evaluate("performance.memory ? performance.memory.usedJSHeapSize : 0") / 1e6, 1)
            except Exception:
                pass
            stats["console"] = logs[:80]
            b.close()
    finally:
        if httpd:
            httpd.shutdown()
    if net:
        by = {}
        for n in net:
            by.setdefault(n["cat"], [0, 0]); by[n["cat"]][0] += 1; by[n["cat"]][1] += n["bytes"]
        stats["network"] = {"requests": len(net), "total_kb": round(sum(n["bytes"] for n in net) / 1024, 1),
                            "by_category_kb": {k: {"n": v[0], "kb": round(v[1] / 1024, 1)} for k, v in
                                               sorted(by.items(), key=lambda kv: -kv[1][1])},
                            "heaviest": sorted(net, key=lambda n: -n["bytes"])[:20],
                            "note": "bytes = content-length (часто сжатый размер) или длина тела для 3D/wasm"}
        json.dump(net, open(os.path.join(out, "network.json"), "w"), ensure_ascii=False, indent=1)
    stats["sheet"] = sheet(stats["shots"], os.path.join(out, "page_sheet.png")) if stats["shots"] else None
    json.dump(stats, open(os.path.join(out, "page_stats.json"), "w"), ensure_ascii=False, indent=1)
    short = {k: stats[k] for k in stats if k not in ("shots", "network")}
    if "network" in stats:
        short["network"] = {k: stats["network"][k] for k in ("requests", "total_kb", "by_category_kb")}
        short["network"]["heaviest_top5"] = [(n["cat"], round(n["bytes"] / 1024), n["url"][:120]) for n in stats["network"]["heaviest"][:5]]
    print(json.dumps(short, ensure_ascii=False, indent=1))


SELFTEST_HTML = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>web_view selftest</title></head><body>
<h1>Проверка страницы</h1><div class="pin-spacer"><div id="pinned">закреплённый блок</div></div><div style="height:1200px"></div>
<script>window.gsapVersions = ["3.12.5"]; document.getElementById("pinned")._gsap = {id: 1}; window.__ready = true;</script></body></html>"""


def selftest():
    """Пути web_stats.json режима модели — от папки модели (без браузера, временная папка); режим страницы на локальной
    папке: GSAP и ScrollTrigger — по рантайму (gsapVersions, _gsap, .pin-spacer без window.gsap); отчёт page_stats.json."""
    import subprocess
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)
    with tempfile.TemporaryDirectory() as td:
        ex = os.path.join(td, "01-sample")
        model, out = os.path.join(ex, "part.glb"), os.path.join(ex, "web", "part")
        stats = {"model": model, "file_kb": 1.0, "views": [{"az": 35, "el": 20, "file": os.path.join(out, "web_view_0_az35_el20.png")}],
                 "anim_frames": [{"t": 0, "file": os.path.join(out, "web_anim_000.png")}], "sheet": os.path.join(out, "web_sheet.png"),
                 "console": ["error: x"]}
        os.makedirs(out)
        fp = os.path.join(out, "web_stats.json")
        json.dump(portable_stats(stats, os.path.dirname(model)), open(fp, "w"), ensure_ascii=False, indent=1)
        back = json.load(open(fp, encoding="utf-8"))
        text = open(fp, encoding="utf-8").read()
    check("web_stats.json: model, views[].file, anim_frames[].file, sheet — от папки модели, абсолютных путей нет",
          (back["model"], back["views"][0]["file"], back["anim_frames"][0]["file"], back["sheet"]) ==
          ("part.glb", "web/part/web_view_0_az35_el20.png", "web/part/web_anim_000.png", "web/part/web_sheet.png")
          and td not in text and back["console"] == ["error: x"])
    check("сообщение «не собран: …» на месте листа — как есть",
          portable_stats({"model": "/m/a.glb", "sheet": "не собран: x"}, "/m")["sheet"] == "не собран: x")
    with tempfile.TemporaryDirectory() as td:
        page = os.path.join(td, "index.html")
        with open(page, "w", encoding="utf-8") as f:
            f.write(SELFTEST_HTML)
        out = os.path.join(td, "out")
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--page", page, out, "--scroll", "0", "--wait", "800", "--frames", "10",
                            "--gpu", "swiftshader"], capture_output=True, text=True, timeout=240, env=kbpaths.playwright_env())
        fp = os.path.join(out, "page_stats.json")
        st = json.load(open(fp, encoding="utf-8")) if os.path.exists(fp) else {}
        check(f"режим страницы: отчёт page_stats.json (код {r.returncode}) {r.stderr[-200:] if not st else ''}", bool(st))
        det = st.get("detected") or {}
        check("GSAP по рантайму: gsapVersions, _gsap, .pin-spacer без window.gsap",
              det.get("gsap") == "3.12.5" and det.get("gsap_targets", 0) >= 1 and det.get("pin_spacers") == 1 and det.get("scrolltrigger"))
    print("web_view selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        sys.exit(selftest())
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if "--page" in a or "--url" in a:
        page_mode(a)
    else:
        model_mode(a)


if __name__ == "__main__":
    main()
