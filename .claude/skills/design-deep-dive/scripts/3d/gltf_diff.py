#!/usr/bin/env python3
"""gltf_diff.py — сравнение «как выглядит в Blender» и «как выглядит в three.js» при ОДИНАКОВЫХ камере, свете и тонмаппинге.

Использование (системный python3):
    python3 gltf_diff.py SOURCE OUT_DIR --glb MODEL.glb [--size 512] [--views 3|4|az:el,az:el]
        [--hdri FILE.hdr|none] [--strength 1.0] [--tone standard|neutral|agx] [--exposure 0]
        [--engine eevee|cycles] [--samples 32] [--keep-lights] [--keep-world] [--three 0.186.0]
        [--gpu gl|vulkan|swiftshader] [--label TEXT] [--cam OUT_OLD/cam.json] [--three-tone standard|neutral|agx]
    python3 gltf_diff.py --compare A.png B.png OUT_PREFIX      # только метрики для двух готовых PNG (RGBA)

SOURCE — .blend (рендерится как есть: исходные материалы, модификаторы) или .glb/.gltf (импорт в пустую сцену).
MODEL.glb — экспортированный файл, который грузится в three (GLTFLoader + Draco + KTX2 + Meshopt той же версии three).

Что делает:
  1. Blender (через blender_run.py, фон, --factory-startup): открывает SOURCE, считает габариты видимой геометрии (после
     модификаторов), ставит камеру (вертикальный FOV 40°, квадратный кадр) на N ракурсах, мир = HDRI (--strength), свет сцены
     выключается (кроме --keep-lights), EEVEE (или Cycles), view transform: standard → «Standard», neutral →
     «Khronos PBR Neutral», agx → «AgX»; плёнка прозрачная. Пишет OUT_DIR/blender_<i>.png и cam.json.
  2. three r186 в headless Chromium на GPU: тот же HDRI как scene.environment (PMREM), environmentIntensity = strength,
     камера в тех же координатах (Blender (x,y,z) → glTF/three (x, z, −y)), toneMapping: None / Neutral / AgX, фон прозрачный.
     Пишет OUT_DIR/three_<i>.png и three_info.json (draw calls, треугольники, материалы, extensionsUsed, ошибки консоли).
  3. Метрики на каждую пару: IoU силуэтов (альфа > 0.5), средняя |ΔRGB| (0–255), ΔE2000 среднее и p95, доля пикселей
     с ΔE2000 > 5, SSIM по L* — внутри общей маски (обе альфы > 0.95). OUT_DIR/diff_metrics.json, OUT_DIR/diff_sheet.png
     (строки — ракурсы; столбцы: Blender | three | тепловая карта ΔE2000, 0…20).
Ориентиры (калибровка: тот же файл в EEVEE «Standard» и three NoToneMapping даёт ΔE2000 3.1, IoU 0.996): ΔE2000 среднее
≤ 3.5 и IoU ≥ 0.99 — «совпадает»; металлы и блики — до ≈ 5; > 6 или IoU < 0.95 — поломка (потеря текстуры, цветовое
пространство, нормали, масштаб). Стекло/анизотропия/плёнка — сравнивать с --engine cycles.
EEVEE даёт затенение (AO/horizon scan) и тени от мира, которых нет у чистого IBL в three: вогнутые места темнее в Blender.
Замок браузера утилита берёт сама на время работы браузера: kbpaths.lock("browser"), реентерабельный по дереву
процессов — утилита, запущенная из утилиты с тем же замком, его не ждёт.
"""
import json, math, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import kbpaths  # noqa: E402
DEFAULT_HDRI = str(kbpaths.data("3d", "studio_small_09_1k.hdr"))
FOV = 40.0

# ---------------------------------------------------------------- Blender-часть -------------------------------------------
BLENDER_SIDE = r'''
import bpy, json, math, os, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
src, out, cfg_path = argv[0], argv[1], argv[2]
cfg = json.load(open(cfg_path))
ext = os.path.splitext(src)[1].lower()
if ext == ".blend":
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
if cfg.get("frame") is not None:
    scene.frame_set(int(cfg["frame"]))
dg = bpy.context.evaluated_depsgraph_get()
GEOM = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "POINTCLOUD"}
objs = [o for o in scene.objects if o.type in GEOM and o.visible_get() and not o.hide_render]
mn = Vector((1e18,) * 3); mx = Vector((-1e18,) * 3)
names = {o.name for o in objs}
for inst in dg.object_instances:   # включает GN-инстансы и инстансы коллекций (bound_box объекта с одними инстансами = 0)
    ob = inst.object
    if ob.type not in GEOM:
        continue
    if not inst.is_instance and ob.original.name not in names:
        continue
    if inst.is_instance and inst.parent and inst.parent.original.hide_render:
        continue
    # у вычисленных FONT/CURVE/SURFACE bound_box не учитывает extrude/bevel — брать у оригинала
    bb = ob.original.bound_box if (ob.type in ("FONT", "CURVE", "SURFACE") and not inst.is_instance) else ob.bound_box
    for c in bb:
        w = inst.matrix_world @ Vector(c)
        mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
if mn.x > mx.x:
    raise SystemExit("пустые габариты")
center = (mn + mx) / 2; radius = max((mx - mn).length / 2, 1e-4)
fov = math.radians(cfg["fov"])
dist = radius / math.sin(fov / 2) * 1.1
near = max(dist - radius * 3, radius * 0.01); far = dist + radius * 4
if not cfg.get("keep_lights"):
    for o in scene.objects:
        if o.type == "LIGHT":
            o.hide_render = True
for o in scene.objects:
    if o.type == "CAMERA":
        o.hide_render = True
if not cfg.get("keep_world"):
    world = bpy.data.worlds.new("_diff_world"); scene.world = world
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    if cfg["hdri"] == "none":   # только свет сцены: чёрный мир
        bg.inputs["Color"].default_value = (0, 0, 0, 1); bg.inputs["Strength"].default_value = 0.0
    else:
        env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(cfg["hdri"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = cfg["strength"]
    try:
        world.sun_threshold = 0.0      # D2: 0 = не извлекать «солнце» из ярких пятен HDRI (умолчание 10 — иначе
                                        # EEVEE превращает превышение в отдельный направленный свет, +13 L* на
                                        # верхних гранях; у чистого IBL в three такого источника нет)
        world.use_sun_shadow = False   # на случай извлечения при иных настройках — хотя бы без теней (в three их нет)
    except Exception:
        pass
cd = bpy.data.cameras.new("_diff_cam"); cd.sensor_fit = "AUTO"; cd.angle = fov
cd.clip_start = near; cd.clip_end = far
cam = bpy.data.objects.new("_diff_cam", cd); scene.collection.objects.link(cam); scene.camera = cam
r = scene.render
r.resolution_x = r.resolution_y = cfg["size"]; r.resolution_percentage = 100; r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"
eng = {"eevee": "BLENDER_EEVEE", "cycles": "CYCLES"}[cfg["engine"]]
try:
    r.engine = eng
except TypeError as e:
    raise SystemExit(str(e))
if eng == "CYCLES":
    scene.cycles.device = "CPU"; scene.cycles.samples = cfg["samples"]
    try:
        scene.cycles.use_denoising = True
    except Exception:
        pass
else:
    scene.eevee.taa_render_samples = cfg["samples"]
vt = {"standard": "Standard", "neutral": "Khronos PBR Neutral", "agx": "AgX"}[cfg["tone"]]
vs = scene.view_settings
vs.view_transform = vt; vs.look = "None"; vs.exposure = cfg["exposure"]; vs.gamma = 1.0
scene.display_settings.display_device = "sRGB"
views_out = []
for i, (az, el) in enumerate(cfg["views"]):
    a, e = math.radians(az), math.radians(el)
    pos = center + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.location = pos
    cam.rotation_euler = (center - pos).to_track_quat("-Z", "Y").to_euler()
    fp = os.path.join(out, "blender_%d.png" % i); r.filepath = fp
    bpy.ops.render.render(write_still=True)
    views_out.append({"az": az, "el": el, "pos_blender": list(pos), "file": fp})
json.dump({"center_blender": list(center), "radius": radius, "dist": dist, "near": near, "far": far,
           "fov": cfg["fov"], "views": views_out, "view_transform": vs.view_transform,
           "engine": r.engine, "blender": bpy.app.version_string},
          open(os.path.join(out, "cam.json"), "w"), indent=1)
print("BLENDER_SIDE_OK", len(views_out))
'''

# ---------------------------------------------------------------- three-часть ---------------------------------------------
PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:transparent;overflow:hidden}canvas{display:block}</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@__VER__/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@__VER__/examples/jsm/"}}</script></head><body>
<script type="module">
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {KTX2Loader} from 'three/addons/loaders/KTX2Loader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
const CFG = __CFG__;
const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(1); renderer.setSize(CFG.size, CFG.size); renderer.setClearColor(0x000000, 0);
document.body.appendChild(renderer.domElement);
renderer.toneMapping = {standard: THREE.NoToneMapping, neutral: THREE.NeutralToneMapping, agx: THREE.AgXToneMapping}[CFG.tone];
renderer.toneMappingExposure = Math.pow(2, CFG.exposure);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(CFG.fov, 1, CFG.near, CFG.far);
const info = {three: THREE.REVISION};
window.__api = {
  view(i) {
    const v = CFG.views[i];
    camera.position.set(...v.pos); camera.up.set(0, 1, 0); camera.lookAt(...CFG.center);
    camera.updateProjectionMatrix(); renderer.render(scene, camera);
    return {calls: renderer.info.render.calls, triangles: renderer.info.render.triangles};
  }
};
(async () => {
  try {
    let HDR;
    try { HDR = (await import('three/addons/loaders/HDRLoader.js')).HDRLoader; }
    catch (e) { HDR = (await import('three/addons/loaders/RGBELoader.js')).RGBELoader; }
    if (CFG.hdri !== 'none') {
      const hdr = await new HDR().loadAsync(CFG.hdri);
      hdr.mapping = THREE.EquirectangularReflectionMapping;
      scene.environment = hdr;
      scene.environmentIntensity = CFG.strength;
    }
    const draco = new DRACOLoader().setDecoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/draco/gltf/`);
    const ktx2 = new KTX2Loader().setTranscoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/basis/`).detectSupport(renderer);
    const loader = new GLTFLoader().setDRACOLoader(draco).setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
    const t0 = performance.now();
    const gltf = await loader.loadAsync(CFG.model);
    info.load_ms = +(performance.now() - t0).toFixed(0);
    scene.add(gltf.scene);
    const mats = new Set(); let meshes = 0;
    gltf.scene.traverse(o => { if (o.isMesh || o.isPoints || o.isLine) { meshes++; (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => mats.add(m)); } });
    info.meshes = meshes;
    info.materials = [...mats].map(m => ({name: m.name, type: m.type, side: m.side, transparent: m.transparent,
      alphaTest: m.alphaTest, depthWrite: m.depthWrite, vertexColors: m.vertexColors, flatShading: m.flatShading,
      color: m.color ? m.color.toArray().map(x => +x.toFixed(4)) : null,
      emissive: m.emissive ? m.emissive.toArray().map(x => +x.toFixed(4)) : null, emissiveIntensity: m.emissiveIntensity,
      metalness: m.metalness, roughness: m.roughness, transmission: m.transmission, thickness: m.thickness, ior: m.ior,
      sheen: m.sheen, clearcoat: m.clearcoat, iridescence: m.iridescence, anisotropy: m.anisotropy, dispersion: m.dispersion,
      specularIntensity: m.specularIntensity, attenuationDistance: m.attenuationDistance,
      maps: Object.keys(m).filter(k => m[k] && m[k].isTexture).map(k => k + ':' + (m[k].colorSpace || '') + ':ch' + m[k].channel)}));
    info.extensionsUsed = gltf.parser.json.extensionsUsed || [];
    info.animations = gltf.animations.map(c => ({name: c.name, duration: +c.duration.toFixed(3), tracks: c.tracks.length}));
    renderer.compile(scene, camera);
    window.__info = info; window.__done = true;
  } catch (e) { window.__err = String(e && e.stack || e); window.__done = true; }
})();
</script></body></html>"""

GPU_ARGS = {
    "gl": ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"],
    "vulkan": ["--use-angle=vulkan", "--enable-features=Vulkan", "--ignore-gpu-blocklist"],
    "swiftshader": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
}


def serve(directory):
    import functools, http.server, socketserver, threading

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    h = functools.partial(Q, directory=directory)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), h)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def b2t(v):
    """Blender Z-up → glTF/three Y-up."""
    return [v[0], v[2], -v[1]]


def run_three(glb, out, cam, cfg):
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="gltfdiff_")
    shutil.copy(glb, os.path.join(tmp, os.path.basename(glb)))
    if glb.lower().endswith(".gltf"):
        src = os.path.dirname(os.path.abspath(glb))
        for fn in os.listdir(src):
            p = os.path.join(src, fn)
            if os.path.isfile(p) and fn != os.path.basename(glb):
                shutil.copy(p, os.path.join(tmp, fn))
    if cfg["hdri"] != "none":
        shutil.copy(cfg["hdri"], os.path.join(tmp, "env.hdr"))
    pcfg = {"ver": cfg["three"], "size": cfg["size"], "tone": cfg.get("three_tone") or cfg["tone"], "exposure": cfg["exposure"],
            "strength": cfg["strength"], "fov": cam["fov"], "near": cam["near"], "far": cam["far"],
            "center": b2t(cam["center_blender"]), "views": [{"pos": b2t(v["pos_blender"])} for v in cam["views"]],
            "model": os.path.basename(glb), "hdri": "env.hdr" if cfg["hdri"] != "none" else "none"}
    open(os.path.join(tmp, "index.html"), "w").write(PAGE.replace("__VER__", cfg["three"]).replace("__CFG__", json.dumps(pcfg)))
    httpd, port = serve(tmp)
    res = {"views": [], "console": []}
    try:
        with kbpaths.lock("browser"), sync_playwright() as pw:
            b = pw.chromium.launch(headless=True, args=GPU_ARGS[cfg["gpu"]])
            p = b.new_page(viewport={"width": cfg["size"], "height": cfg["size"]})
            p.on("console", lambda m: res["console"].append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            p.on("pageerror", lambda e: res["console"].append(f"pageerror: {e}"))
            p.goto(f"http://127.0.0.1:{port}/index.html")
            p.wait_for_function("window.__done === true", timeout=180000)
            err = p.evaluate("window.__err || null")
            if err:
                res["error"] = err
            else:
                res["info"] = p.evaluate("window.__info")
                for i in range(len(cam["views"])):
                    r = p.evaluate(f"window.__api.view({i})")
                    fp = os.path.join(out, f"three_{i}.png")
                    p.screenshot(path=fp, omit_background=True)
                    res["views"].append({**r, "file": fp})
            b.close()
    finally:
        httpd.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
    json.dump(res, open(os.path.join(out, "three_info.json"), "w"), ensure_ascii=False, indent=1)
    return res


# ---------------------------------------------------------------- метрики -------------------------------------------------
def _load(p):
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.float64) / 255.0


def srgb_to_lab(rgb):
    import numpy as np
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ M.T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    d = 6 / 29
    f = np.where(xyz > d ** 3, np.cbrt(xyz), xyz / (3 * d * d) + 4 / 29)
    L = 116 * f[..., 1] - 16; a = 500 * (f[..., 0] - f[..., 1]); b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)


def ciede2000(lab1, lab2):
    import numpy as np
    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]
    C1 = np.hypot(a1, b1); C2 = np.hypot(a2, b2); Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p = (1 + G) * a1; a2p = (1 + G) * a2
    C1p = np.hypot(a1p, b1); C2p = np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360; h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp = L2 - L1; dCp = C2p - C1p
    dh = h2p - h1p
    dh = np.where(C1p * C2p == 0, 0, np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh)))
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lbp = (L1 + L2) / 2; Cbp = (C1p + C2p) / 2
    hs = h1p + h2p
    hbp = np.where(C1p * C2p == 0, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2, np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    T = 1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp)) + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63))
    dtheta = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2); Sc = 1 + 0.045 * Cbp; Sh = 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dtheta)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def _gauss_blur(img, sigma=1.5):
    import numpy as np
    r = int(3 * sigma + 0.5); x = np.arange(-r, r + 1); k = np.exp(-x ** 2 / (2 * sigma * sigma)); k /= k.sum()
    tmp = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, img)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, tmp)


def ssim_map(x, y, L=100.0):
    C1 = (0.01 * L) ** 2; C2 = (0.03 * L) ** 2
    mx = _gauss_blur(x); my = _gauss_blur(y)
    sxx = _gauss_blur(x * x) - mx * mx; syy = _gauss_blur(y * y) - my * my; sxy = _gauss_blur(x * y) - mx * my
    return ((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx * mx + my * my + C1) * (sxx + syy + C2))


def compare(pa, pb, heat_path=None):
    import numpy as np
    A = _load(pa); B = _load(pb)
    if A.shape != B.shape:
        from PIL import Image
        B = np.asarray(Image.open(pb).convert("RGBA").resize((A.shape[1], A.shape[0]))).astype(np.float64) / 255
    ma = A[..., 3] > 0.5; mb = B[..., 3] > 0.5
    inter = (ma & mb).sum(); union = (ma | mb).sum()
    iou = float(inter / union) if union else 1.0
    m = (A[..., 3] > 0.95) & (B[..., 3] > 0.95)
    res = {"iou": round(iou, 4), "pixels_a": int(ma.sum()), "pixels_b": int(mb.sum()), "pixels_compared": int(m.sum())}
    if m.sum() == 0:
        res["note"] = "нет общей маски (объект не отрисован в одном из рендеров)"
        res.update({"de2000_mean": 100.0, "de2000_p95": 100.0, "ssim_L": 0.0, "mean_abs_rgb_255": 255.0})
        if heat_path:
            from PIL import Image
            rgb = np.full(A.shape[:2] + (3,), 0.12); rgb[ma ^ mb] = [1, 0, 1]
            Image.fromarray((rgb * 255).astype(np.uint8)).save(heat_path)
        return res
    la = srgb_to_lab(A[..., :3]); lb = srgb_to_lab(B[..., :3])
    de = ciede2000(la, lb)
    dv = de[m]
    res.update({
        "mean_abs_rgb_255": round(float(np.abs(A[..., :3] - B[..., :3])[m].mean() * 255), 2),
        "mean_rgb_a_255": [round(float(v), 1) for v in (A[..., :3][m].mean(0) * 255)],
        "mean_rgb_b_255": [round(float(v), 1) for v in (B[..., :3][m].mean(0) * 255)],
        "de2000_mean": round(float(dv.mean()), 2), "de2000_p95": round(float(np.percentile(dv, 95)), 2),
        "de2000_gt5_share": round(float((dv > 5).mean()), 3),
        "L_mean_a": round(float(la[..., 0][m].mean()), 2), "L_mean_b": round(float(lb[..., 0][m].mean()), 2),
    })
    ys, xs = np.nonzero(ma | mb)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sm = ssim_map(la[y0:y1, x0:x1, 0], lb[y0:y1, x0:x1, 0])
    res["ssim_L"] = round(float(sm[m[y0:y1, x0:x1]].mean()), 4)
    if heat_path:
        from PIL import Image
        h = np.clip(de / 20.0, 0, 1)
        rgb = np.stack([h, 1 - np.abs(h - 0.5) * 2, 1 - h], -1) * ((ma | mb)[..., None]) + 0.12 * (~(ma | mb))[..., None]
        miss = ma ^ mb
        rgb[miss] = [1, 0, 1]
        Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(heat_path)
    return res


def sheet(rows, out, bg=(212, 212, 216)):
    from PIL import Image
    ims = [[Image.open(p).convert("RGBA") for p in r] for r in rows]
    w, h = ims[0][0].size
    S = Image.new("RGBA", (w * max(len(r) for r in ims), h * len(ims)), bg + (255,))
    for i, r in enumerate(ims):
        for j, im in enumerate(r):
            tile = Image.new("RGBA", (w, h), bg + (255,)); tile.alpha_composite(im.resize((w, h)))
            S.paste(tile, (j * w, i * h))
    S.convert("RGB").save(out)
    return out


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    if a[0] == "--compare":
        pa, pb, pref = a[1], a[2], a[3]
        r = compare(pa, pb, pref + "_heat.png"); print(json.dumps(r, ensure_ascii=False, indent=1))
        json.dump(r, open(pref + "_metrics.json", "w"), indent=1); return

    def opt(n, d=None):
        return a[a.index(n) + 1] if n in a else d

    src, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    glb = opt("--glb")
    if not glb:
        print("нужен --glb MODEL.glb"); sys.exit(2)
    glb = os.path.abspath(glb)
    os.makedirs(out, exist_ok=True)
    views = opt("--views", "3")
    if ":" in views:
        vlist = [tuple(float(x) for x in v.split(":")) for v in views.split(",")]
    elif views == "4":
        vlist = [(35, 20), (0, 5), (90, 5), (200, 35)]
    elif views == "1":
        vlist = [(35, 20)]
    else:
        vlist = [(35, 20), (0, 5), (200, 35)]
    hd = opt("--hdri", DEFAULT_HDRI)
    cfg = {"size": int(opt("--size", 512)), "views": vlist, "hdri": hd if hd == "none" else os.path.abspath(hd),
           "strength": float(opt("--strength", 1.0)), "tone": opt("--tone", "standard"), "exposure": float(opt("--exposure", 0)),
           "engine": opt("--engine", "eevee"), "samples": int(opt("--samples", 32)), "keep_lights": "--keep-lights" in a,
           "keep_world": "--keep-world" in a, "fov": FOV, "three": opt("--three", "0.186.0"), "gpu": opt("--gpu", "gl"),
           "frame": opt("--frame"), "three_tone": opt("--three-tone")}
    cfgp = os.path.join(out, "diff_cfg.json"); json.dump(cfg, open(cfgp, "w"), indent=1)
    t0 = time.time()
    if opt("--cam"):   # только three: камера и эталонные blender_<i>.png из прошлого прогона (сравнение вариантов сжатия)
        cam = json.load(open(opt("--cam")))
        ref_dir = os.path.dirname(os.path.abspath(opt("--cam")))
        for i in range(len(cam["views"])):
            shutil.copy(os.path.join(ref_dir, f"blender_{i}.png"), os.path.join(out, f"blender_{i}.png"))
        json.dump(cam, open(os.path.join(out, "cam.json"), "w"), indent=1)
        cam.setdefault("engine", "reuse"); cam.setdefault("view_transform", "reuse"); cam.setdefault("blender", "reuse")
    else:
        side = os.path.join(out, "_blender_side.py"); open(side, "w").write(BLENDER_SIDE)
        r = subprocess.run([sys.executable, os.path.join(HERE, "blender_run.py"), side, "--timeout", "600", "--", src, out, cfgp],
                           capture_output=True, text=True)
        os.remove(side)
        if r.returncode != 0 or "BLENDER_SIDE_OK" not in r.stdout:
            print(r.stdout[-3000:], r.stderr[-2000:]); sys.exit(1)
        cam = json.load(open(os.path.join(out, "cam.json")))
    t_bl = time.time() - t0
    t1 = time.time()
    tres = run_three(glb, out, cam, cfg)
    t_th = time.time() - t1
    if tres.get("error"):
        print(json.dumps({"three_error": tres["error"][:2000], "console": tres["console"][:10]}, ensure_ascii=False, indent=1)); sys.exit(1)
    metrics = []
    rows = []
    for i, v in enumerate(cam["views"]):
        pa, pb = os.path.join(out, f"blender_{i}.png"), os.path.join(out, f"three_{i}.png")
        heat = os.path.join(out, f"heat_{i}.png")
        m = compare(pa, pb, heat); m["view"] = [v["az"], v["el"]]; metrics.append(m)
        rows.append([pa, pb, heat])
    sh = sheet(rows, os.path.join(out, "diff_sheet.png"))
    summary = {"label": opt("--label", ""), "source": src, "glb": glb, "glb_kb": round(os.path.getsize(glb) / 1024, 1),
               "tone": cfg["tone"], "engine": cam["engine"], "view_transform": cam["view_transform"],
               "three": tres.get("info", {}).get("three"), "blender": cam["blender"],
               "metrics": metrics,
               "mean": {k: round(sum(m.get(k, 0) for m in metrics) / len(metrics), 3) for k in ("iou", "de2000_mean", "de2000_p95", "ssim_L", "mean_abs_rgb_255")},
               "three_info": tres.get("info"), "draw_calls": [v["calls"] for v in tres["views"]],
               "console": tres["console"][:20], "sheet": sh, "sec": {"blender": round(t_bl, 1), "three": round(t_th, 1)}}
    json.dump(summary, open(os.path.join(out, "diff_metrics.json"), "w"), ensure_ascii=False, indent=1)
    short = {k: summary[k] for k in ("label", "glb_kb", "tone", "engine", "mean", "draw_calls", "console", "sheet", "sec")}
    print(json.dumps(short, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
