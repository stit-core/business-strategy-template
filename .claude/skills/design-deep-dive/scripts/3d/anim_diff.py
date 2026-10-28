#!/usr/bin/env python3
"""anim_diff.py — анимация «как в Blender» против «как в three r186» в ОДНИ И ТЕ ЖЕ моменты.

    python3 anim_diff.py SCENE.blend OUT_DIR --glb MODEL.glb --frames 1,31,61,91 [--fps 30] [--start 1]
        [--clip NAME] [--scene-camera] [--size 512] [--tone standard|neutral|agx] [--hdri FILE|none] [--strength 1]
        [--keep-lights] [--samples 16] [--az 35 --el 20] [--three 0.186.0] [--mute-nla]

Blender (фон): кадр f → frame_set(f) → рендер EEVEE (камера: общая по объединённым габаритам всех кадров, FOV 40°, или
камера сцены при --scene-camera), мир = HDRI, свет сцены выключен (кроме --keep-lights), view transform по --tone.
three (Chromium): тот же HDRI, та же камера (или экспортированная камера glTF с тем же именем, анимированная клипом),
mixer.clipAction(clip).play(); action.time = (f − start)/fps; mixer.update(0) — клип экспортирован с export_anim_slide_to_zero=True.
Метрики на кадр (gltf_diff.compare): IoU силуэтов, ΔE2000 среднее/p95, SSIM L*. Лист: Blender | three | ΔE.
Замок браузера утилита берёт сама на время работы браузера: kbpaths.lock("browser"), реентерабельный по дереву
процессов — утилита, запущенная из утилиты с тем же замком, его не ждёт.
"""
import json, os, shutil, subprocess, sys, tempfile, time

TOOLS = os.path.dirname(os.path.abspath(__file__))  # gltf_diff.py — рядом
sys.path.insert(0, TOOLS)
import gltf_diff as GD  # compare, sheet, serve, b2t, GPU_ARGS, DEFAULT_HDRI

BLENDER_SIDE = r'''
import bpy, json, math, os, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
src, out, cfg_path = argv
cfg = json.load(open(cfg_path))
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
if cfg.get("mute_nla"):          # клип в three играет один; в Blender отключить NLA-дорожки (Idle и т. п.)
    for ob in bpy.data.objects:
        if ob.animation_data:
            for tr in ob.animation_data.nla_tracks:
                tr.mute = True
GEOM = {"MESH", "CURVE", "SURFACE", "META", "FONT"}
mn = Vector((1e18,) * 3); mx = Vector((-1e18,) * 3)
for f in cfg["frames"]:
    sc.frame_set(int(f))
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in sc.objects:
        if ob.type not in GEOM or not ob.visible_get() or ob.hide_render:
            continue
        oe = ob.evaluated_get(dg)
        me = oe.to_mesh()
        if me is None:
            continue
        mw = oe.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
        oe.to_mesh_clear()
center = (mn + mx) / 2; radius = max((mx - mn).length / 2, 1e-4)
fov = math.radians(cfg["fov"])
if not cfg.get("keep_lights"):
    for o in sc.objects:
        if o.type == "LIGHT":
            o.hide_render = True
world = bpy.data.worlds.new("_ad_world"); sc.world = world
nt = world.node_tree; bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
if cfg["hdri"] == "none":
    bg.inputs["Color"].default_value = (0, 0, 0, 1); bg.inputs["Strength"].default_value = 0.0
else:
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(cfg["hdri"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = cfg["strength"]
try:
    world.use_sun_shadow = False
except Exception:
    pass
cam_info = {}
if cfg.get("scene_camera"):
    cam = sc.camera
    cam.data.sensor_fit = "AUTO"
    cam_info = {"mode": "scene", "name": cam.name, "lens": cam.data.lens, "angle_deg": math.degrees(cam.data.angle)}
else:
    for o in sc.objects:
        if o.type == "CAMERA":
            o.hide_render = True
    dist = radius / math.sin(fov / 2) * 1.1
    cd = bpy.data.cameras.new("_ad_cam"); cd.sensor_fit = "AUTO"; cd.angle = fov
    cd.clip_start = max(dist - radius * 3, radius * 0.01); cd.clip_end = dist + radius * 4
    cam = bpy.data.objects.new("_ad_cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    a, e = math.radians(cfg["az"]), math.radians(cfg["el"])
    pos = center + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.location = pos; cam.rotation_euler = (center - pos).to_track_quat("-Z", "Y").to_euler()
    cam_info = {"mode": "fixed", "pos_blender": list(pos), "center_blender": list(center), "fov": cfg["fov"],
                "near": cd.clip_start, "far": cd.clip_end}
r = sc.render
r.resolution_x = r.resolution_y = cfg["size"]; r.resolution_percentage = 100; r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"
r.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = cfg["samples"]
vs = sc.view_settings
vs.view_transform = {"standard": "Standard", "neutral": "Khronos PBR Neutral", "agx": "AgX"}[cfg["tone"]]
vs.look = "None"; vs.exposure = 0; vs.gamma = 1
sc.display_settings.display_device = "sRGB"
files = []
for f in cfg["frames"]:
    sc.frame_set(int(f))
    p = os.path.join(out, "blender_f%04d.png" % int(f)); r.filepath = p
    bpy.ops.render.render(write_still=True); files.append(p)
json.dump({"cam": cam_info, "radius": radius, "center": list(center), "files": files, "fps": sc.render.fps,
           "blender": bpy.app.version_string}, open(os.path.join(out, "cam.json"), "w"), indent=1)
print("AD_BLENDER_OK", len(files))
'''

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:transparent;overflow:hidden}canvas{display:block}</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@__VER__/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@__VER__/examples/jsm/"}}</script></head><body>
<script type="module">
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {HDRLoader} from 'three/addons/loaders/HDRLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
const CFG = __CFG__;
const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(1); renderer.setSize(CFG.size, CFG.size); renderer.setClearColor(0x000000, 0);
document.body.appendChild(renderer.domElement);
renderer.toneMapping = {standard: THREE.NoToneMapping, neutral: THREE.NeutralToneMapping, agx: THREE.AgXToneMapping}[CFG.tone];
const scene = new THREE.Scene();
let camera = new THREE.PerspectiveCamera(CFG.fov, 1, CFG.near || 0.01, CFG.far || 1000);
let mixer = null; let actions = [];
const info = {three: THREE.REVISION};
window.__api = {
  at(t) {
    if (mixer) { for (const a of actions) a.time = Math.min(t, a.getClip().duration); mixer.update(0); }   // не setTime: он заворачивает t = duration в 0
    scene.updateMatrixWorld(true);
    if (CFG.camMode === 'fixed') { camera.position.set(...CFG.pos); camera.up.set(0, 1, 0); camera.lookAt(...CFG.center); camera.updateProjectionMatrix(); }
    renderer.render(scene, camera);
    return {calls: renderer.info.render.calls, triangles: renderer.info.render.triangles};
  }
};
(async () => {
  try {
    if (CFG.hdri !== 'none') { const hdr = await new HDRLoader().loadAsync(CFG.hdri); hdr.mapping = THREE.EquirectangularReflectionMapping; scene.environment = hdr; scene.environmentIntensity = CFG.strength; }
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(CFG.model);
    scene.add(gltf.scene);
    info.clips = gltf.animations.map(c => ({name: c.name, duration: +c.duration.toFixed(4), tracks: c.tracks.length,
       track_names: c.tracks.slice(0, 12).map(t => t.name)}));
    if (gltf.animations.length) {
      mixer = new THREE.AnimationMixer(gltf.scene);
      const clips = CFG.clip ? [THREE.AnimationClip.findByName(gltf.animations, CFG.clip)] : gltf.animations;
      if (!clips[0]) throw new Error('clip not found: ' + CFG.clip);
      actions = clips.map(c => { const a = mixer.clipAction(c); a.play(); return a; });
    }
    if (CFG.camMode === 'scene') {
      const cams = []; gltf.scene.traverse(o => { if (o.isCamera) cams.push(o); });
      info.cameras = cams.map(c => c.name);
      camera = cams.find(c => c.name === CFG.camName || (c.parent && c.parent.name === CFG.camName)) || cams[0];
      if (!camera) throw new Error('no camera in glTF');
      camera.aspect = 1; camera.updateProjectionMatrix();
      info.cam_fov = camera.fov;
    }
    renderer.compile(scene, camera);
    window.__info = info; window.__done = true;
  } catch (e) { window.__err = String(e && e.stack || e); window.__done = true; }
})();
</script></body></html>"""


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return

    def opt(n, d=None):
        return a[a.index(n) + 1] if n in a else d
    src, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    glb = os.path.abspath(opt("--glb"))
    os.makedirs(out, exist_ok=True)
    frames = [int(x) for x in opt("--frames").split(",")]
    hd = opt("--hdri", GD.DEFAULT_HDRI)
    cfg = {"frames": frames, "fps": float(opt("--fps", 30)), "start": float(opt("--start", 1)), "size": int(opt("--size", 512)),
           "tone": opt("--tone", "standard"), "hdri": hd if hd == "none" else os.path.abspath(hd), "strength": float(opt("--strength", 1.0)),
           "keep_lights": "--keep-lights" in a, "samples": int(opt("--samples", 16)), "fov": 40.0,
           "az": float(opt("--az", 35)), "el": float(opt("--el", 20)), "scene_camera": "--scene-camera" in a,
           "clip": opt("--clip"), "three": opt("--three", "0.186.0"), "mute_nla": "--mute-nla" in a}
    cfgp = os.path.join(out, "ad_cfg.json"); json.dump(cfg, open(cfgp, "w"), indent=1)
    t0 = time.time()
    side = os.path.join(out, "_ad_blender.py"); open(side, "w").write(BLENDER_SIDE)
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "blender_run.py"), side, "--timeout", "600", "--", src, out, cfgp],
                       capture_output=True, text=True)
    os.remove(side)
    if r.returncode != 0 or "AD_BLENDER_OK" not in r.stdout:
        print(r.stdout[-3000:], r.stderr[-1500:]); sys.exit(1)
    cam = json.load(open(os.path.join(out, "cam.json")))
    tb = time.time() - t0
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="animdiff_")
    shutil.copy(glb, os.path.join(tmp, os.path.basename(glb)))
    if cfg["hdri"] != "none":
        shutil.copy(cfg["hdri"], os.path.join(tmp, "env.hdr"))
    ci = cam["cam"]
    pcfg = {"ver": cfg["three"], "size": cfg["size"], "tone": cfg["tone"], "strength": cfg["strength"], "fov": 40.0,
            "model": os.path.basename(glb), "hdri": "env.hdr" if cfg["hdri"] != "none" else "none", "clip": cfg["clip"],
            "camMode": ci["mode"]}
    if ci["mode"] == "fixed":
        pcfg.update(pos=GD.b2t(ci["pos_blender"]), center=GD.b2t(ci["center_blender"]), near=ci["near"], far=ci["far"])
    else:
        pcfg.update(camName=ci["name"])
    open(os.path.join(tmp, "index.html"), "w").write(PAGE.replace("__VER__", cfg["three"]).replace("__CFG__", json.dumps(pcfg)))
    httpd, port = GD.serve(tmp)
    res = {"frames": [], "console": []}
    try:
        with GD.kbpaths.lock("browser"), sync_playwright() as pw:
            b = pw.chromium.launch(headless=True, args=GD.GPU_ARGS["gl"])
            p = b.new_page(viewport={"width": cfg["size"], "height": cfg["size"]})
            p.on("console", lambda m: res["console"].append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            p.on("pageerror", lambda e: res["console"].append(f"pageerror: {e}"))
            p.goto(f"http://127.0.0.1:{port}/index.html")
            p.wait_for_function("window.__done === true", timeout=120000)
            err = p.evaluate("window.__err || null")
            if err:
                print(json.dumps({"three_error": err[:1500], "console": res["console"][:10]}, ensure_ascii=False, indent=1)); sys.exit(1)
            res["info"] = p.evaluate("window.__info")
            for f in frames:
                t = (f - cfg["start"]) / cfg["fps"]
                rr = p.evaluate(f"window.__api.at({t})")
                fp = os.path.join(out, "three_f%04d.png" % f)
                p.screenshot(path=fp, omit_background=True)
                res["frames"].append({"frame": f, "t": round(t, 4), **rr, "file": fp})
            b.close()
    finally:
        httpd.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
    metrics, rows = [], []
    for fr in res["frames"]:
        f = fr["frame"]
        pa, pb = os.path.join(out, "blender_f%04d.png" % f), os.path.join(out, "three_f%04d.png" % f)
        heat = os.path.join(out, "heat_f%04d.png" % f)
        m = GD.compare(pa, pb, heat); m["frame"] = f; m["t"] = fr["t"]; metrics.append(m); rows.append([pa, pb, heat])
    sh = GD.sheet(rows, os.path.join(out, "anim_diff_sheet.png"))
    summ = {"glb": glb, "glb_kb": round(os.path.getsize(glb) / 1024, 1), "clips": res["info"].get("clips"),
            "per_frame": [{k: m.get(k) for k in ("frame", "t", "iou", "de2000_mean", "de2000_p95", "ssim_L")} for m in metrics],
            "worst": {"iou_min": min(m["iou"] for m in metrics), "de_max": max(m.get("de2000_mean", 0) for m in metrics)},
            "console": res["console"][:10], "sheet": sh, "sec": {"blender": round(tb, 1)}, "cam": ci}
    json.dump(summ, open(os.path.join(out, "anim_diff.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: summ[k] for k in ("glb_kb", "per_frame", "worst", "console", "sheet")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
