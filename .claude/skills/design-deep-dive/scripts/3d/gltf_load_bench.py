#!/usr/bin/env python3
"""gltf_load_bench.py — замер загрузки GLB в three.js (r186) в headless Chromium на GPU: холодная загрузка (с докачкой
декодеров с jsDelivr), тёплые загрузки (декодеры готовы; медиана N), первый кадр (компиляция шейдеров + загрузка текстур в GPU),
оценка памяти GPU (геометрия + текстуры с учётом формата и мипмапов), draw calls, треугольники, ошибки консоли.

    python3 gltf_load_bench.py a.glb [b.glb ...] [--runs 3] [--three 0.186.0] [--gpu gl] [--throttle 4] [--json out.json]

--throttle N: замедление CPU в N раз через CDP (ориентир для телефона; сеть не ограничивается — файлы раздаются локально).
Время тёплой загрузки включает: чтение файла с локального сервера, разбор JSON, декодирование Draco/Meshopt в воркерах,
транскодирование KTX2, декодирование PNG/JPEG/WebP (ImageBitmap), сборку сцены. Первый кадр: renderer.compile + render + gl.finish.
Память GPU — оценка: атрибуты и индексы (байты массивов), текстуры: w×h×Bpp×(4/3 при мипмапах); Bpp: RGBA8 = 4,
BC7/BC3/ASTC4x4/ETC2-RGBA = 1, BC1/ETC1/ETC2-RGB = 0.5.
Замок браузера утилита берёт сама на время работы браузера: kbpaths.lock("browser"), реентерабельный по дереву
процессов — утилита, запущенная из утилиты с тем же замком, его не ждёт.
"""
import functools, http.server, json, os, shutil, socketserver, sys, tempfile, threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
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
const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setPixelRatio(1); renderer.setSize(800, 600); document.body.appendChild(renderer.domElement);
const gl = renderer.getContext();
const draco = new DRACOLoader().setDecoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/draco/gltf/`);
const ktx2 = new KTX2Loader().setTranscoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/basis/`).detectSupport(renderer);
const loader = new GLTFLoader().setDRACOLoader(draco).setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
const BPP = {}; // заполняется по формату
function texBytes(t) {
  let w = 0, h = 0, levels = 1, bpp = 4;
  if (t.isCompressedTexture) {
    const m = t.mipmaps || []; if (m[0]) { w = m[0].width; h = m[0].height; }
    levels = m.length || 1;
    let total = 0; for (const lv of m) total += lv.data ? lv.data.byteLength : 0;
    return {w, h, bytes: total, format: t.format, compressed: true, mips: levels};
  }
  const im = t.image; if (!im) return {w: 0, h: 0, bytes: 0};
  w = im.width; h = im.height;
  const mip = t.generateMipmaps && t.minFilter !== THREE.LinearFilter && t.minFilter !== THREE.NearestFilter;
  return {w, h, bytes: Math.round(w * h * 4 * (mip ? 4 / 3 : 1)), compressed: false, mips: mip ? 'auto' : 1};
}
async function once(url) {
  const t0 = performance.now();
  const gltf = await loader.loadAsync(url);
  const t1 = performance.now();
  return {gltf, ms: t1 - t0};
}
(async () => {
  try {
    const res = {three: THREE.REVISION, gpu: (() => { const d = gl.getExtension('WEBGL_debug_renderer_info'); return d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'n/a'; })(),
      ktx2Support: ktx2.workerConfig, files: []};
    { // прогрев: компиляция стандартного PBR-шейдера и PMREM, чтобы «первый кадр» мерил загрузку в GPU, а не первую компиляцию
      const ws = new THREE.Scene(); ws.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
      ws.add(new THREE.Mesh(new THREE.SphereGeometry(1, 16, 8), new THREE.MeshStandardMaterial()));
      const wc = new THREE.PerspectiveCamera(40, 800 / 600, 0.1, 100); wc.position.set(0, 0, 4);
      renderer.render(ws, wc); gl.finish();
    }
    for (const f of CFG.files) {
      const r = {file: f};
      const cold = await once(f); r.cold_ms = +cold.ms.toFixed(1);
      const warm = [];
      for (let i = 0; i < CFG.runs; i++) warm.push((await once(f)).ms);
      warm.sort((a, b) => a - b); r.warm_ms = +warm[Math.floor(warm.length / 2)].toFixed(1); r.warm_all = warm.map(x => +x.toFixed(1));
      const gltf = cold.gltf;
      const scene = new THREE.Scene();
      scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
      scene.add(gltf.scene);
      const box = new THREE.Box3().setFromObject(gltf.scene); const c = box.getCenter(new THREE.Vector3()); const s = box.getSize(new THREE.Vector3()).length() || 1;
      const cam = new THREE.PerspectiveCamera(40, 800 / 600, s * 0.01, s * 10); cam.position.copy(c).add(new THREE.Vector3(0.5, 0.35, 1).normalize().multiplyScalar(s * 1.4)); cam.lookAt(c);
      const t2 = performance.now(); renderer.compile(scene, cam); renderer.render(scene, cam); gl.finish(); r.first_frame_ms = +(performance.now() - t2).toFixed(1);
      const t3 = performance.now(); for (let i = 0; i < 10; i++) renderer.render(scene, cam); gl.finish(); r.frame_ms = +((performance.now() - t3) / 10).toFixed(2);
      r.calls = renderer.info.render.calls; r.triangles = renderer.info.render.triangles;
      let geo = 0; const geos = new Set(), texs = new Set(), arrays = new Set();
      const addArr = arr => { if (!arrays.has(arr)) { arrays.add(arr); geo += arr.byteLength; } };
      gltf.scene.traverse(o => { if (o.geometry && !geos.has(o.geometry)) { geos.add(o.geometry);
        for (const a of Object.values(o.geometry.attributes)) addArr(a.isInterleavedBufferAttribute ? a.data.array : a.array);
        for (const arr of Object.values(o.geometry.morphAttributes)) for (const a of arr) addArr(a.isInterleavedBufferAttribute ? a.data.array : a.array);
        if (o.geometry.index) addArr(o.geometry.index.array); }
        if (o.isInstancedMesh) geo += o.instanceMatrix.array.byteLength;
        const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
        for (const m of ms) for (const k in m) { const v = m[k]; if (v && v.isTexture) texs.add(v.source ? v.source : v); } });
      let tb = 0; const tl = [];
      const seen = new Set();
      gltf.scene.traverse(o => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
        for (const m of ms) for (const k in m) { const v = m[k]; if (v && v.isTexture) { const key = v.source ? v.source.uuid : v.uuid; if (seen.has(key)) continue; seen.add(key);
          const b = texBytes(v); tb += b.bytes; tl.push({slot: k, ...b}); } } });
      r.gpu_geometry_kb = +(geo / 1024).toFixed(1); r.gpu_textures_kb = +(tb / 1024).toFixed(1); r.textures = tl;
      r.extensionsUsed = gltf.parser.json.extensionsUsed || [];
      scene.remove(gltf.scene); renderer.renderLists.dispose();
      gltf.scene.traverse(o => { if (o.geometry) o.geometry.dispose(); const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
        for (const m of ms) { for (const k in m) { const v = m[k]; if (v && v.isTexture) v.dispose(); } m.dispose(); } });
      res.files.push(r);
    }
    window.__out = res;
  } catch (e) { window.__err = String(e && e.stack || e); }
  window.__done = true;
})();
</script></body></html>"""

GPU_ARGS = {"gl": ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"],
            "vulkan": ["--use-angle=vulkan", "--enable-features=Vulkan", "--ignore-gpu-blocklist"],
            "swiftshader": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]}


def bench(files, runs=3, ver="0.186.0", gpu="gl", throttle=None):
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="loadbench_")
    names = []
    for i, f in enumerate(files):
        n = f"m{i}_" + os.path.basename(f); shutil.copy(f, os.path.join(tmp, n)); names.append(n)
    cfg = {"ver": ver, "files": names, "runs": runs}
    open(os.path.join(tmp, "index.html"), "w").write(PAGE.replace("__VER__", ver).replace("__CFG__", json.dumps(cfg)))

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store"); super().end_headers()
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Q, directory=tmp)); httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    logs = []
    try:
        with kbpaths.lock("browser"), sync_playwright() as pw:
            b = pw.chromium.launch(headless=True, args=GPU_ARGS[gpu])
            ctx = b.new_context(viewport={"width": 800, "height": 600}); p = ctx.new_page()
            if throttle:
                cdp = ctx.new_cdp_session(p); cdp.send("Emulation.setCPUThrottlingRate", {"rate": float(throttle)})
            p.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            p.goto(f"http://127.0.0.1:{httpd.server_address[1]}/index.html")
            p.wait_for_function("window.__done === true", timeout=600000)
            err = p.evaluate("window.__err || null")
            out = {"error": err} if err else p.evaluate("window.__out")
            b.close()
    finally:
        httpd.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
    for r, f in zip(out.get("files", []), files):
        r["file"] = f; r["file_kb"] = round(os.path.getsize(f) / 1024, 1)
    out["console"] = logs[:30]; out["throttle"] = throttle
    return out


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    vals = {opt(k) for k in ("--runs", "--three", "--gpu", "--throttle", "--json")}
    files = [os.path.abspath(x) for x in a if x.endswith((".glb", ".gltf")) and x not in vals]
    res = bench(files, int(opt("--runs", 3)), opt("--three", "0.186.0"), opt("--gpu", "gl"), opt("--throttle"))
    if opt("--json"):
        json.dump(res, open(opt("--json"), "w"), ensure_ascii=False, indent=1)
    for r in res.get("files", []):
        print(f"{os.path.basename(r['file']):48s} {r['file_kb']:>9} КБ  cold {r['cold_ms']:>8} мс  warm {r['warm_ms']:>8} мс  1st frame {r['first_frame_ms']:>7} мс  "
              f"calls {r['calls']:>4}  tris {r['triangles']:>8}  GPU geo {r['gpu_geometry_kb']:>8} КБ  tex {r['gpu_textures_kb']:>9} КБ")
    if res.get("error"):
        print("ERROR", res["error"][:1000])
    if res.get("console"):
        print("console:", res["console"][:5])


if __name__ == "__main__":
    main()
