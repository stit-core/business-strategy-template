#!/usr/bin/env python3
"""gltf_web_inspect.py — что three.js (r186 по умолчанию) реально создаёт из glTF/GLB: дамп сцены в JSON.

    python3 gltf_web_inspect.py model.glb [--out report.json] [--three 0.186.0] [--anim-sample 0.5] [--gpu gl]

Печатает/пишет JSON:
  objects  — обход gltf.scene: тип (Mesh/SkinnedMesh/InstancedMesh/Points/LineSegments/Group/Bone/Object3D/…Light/…Camera),
             name (санитизированное three) и userData.name (исходное имя glTF), userData (extras), position/quaternion/scale,
             для мешей: geometry.attributes {имя: itemSize, тип массива, normalized, count}, morphAttributes, index,
             morphTargetDictionary, morphTargetInfluences, count у InstancedMesh, instanceColor;
             для света: intensity, color, distance, decay, angle, penumbra; для камер: fov/aspect/near/far или left/right/…
  materials — тип, name, side (0 Front/1 Back/2 Double), transparent, depthWrite, alphaTest, opacity, vertexColors, flatShading,
             color/emissive/emissiveIntensity/metalness/roughness и физические параметры, карты: имя слота → колор-спейс,
             channel (набор UV), offset/repeat/rotation, размер изображения, формат (сжатая ли).
  animations — клипы: имя, длительность, треки (имя, тип, число ключей, интерполяция); --anim-sample T — значения
             анимируемых свойств после mixer.setTime(T·длительность).
  renderer — WebGL2, GPU, число draw calls и треугольников первого кадра, info.memory (геометрии, текстуры), ошибки консоли.
Нужен для матрицы «Blender → glTF → three»: какие атрибуты дошли, какие UV-каналы у карт, как назначено цветовое
пространство, какие имена у узлов (sanitizeNodeName: «Cube.001» → «Cube001»).
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
const r4 = x => typeof x === 'number' ? +x.toFixed(4) : x;
const arr = a => Array.from(a).map(r4);
(async () => {
 try {
  const renderer = new THREE.WebGLRenderer({antialias: true});
  renderer.setSize(256, 256); document.body.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const draco = new DRACOLoader().setDecoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/draco/gltf/`);
  const ktx2 = new KTX2Loader().setTranscoderPath(`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/basis/`).detectSupport(renderer);
  const loader = new GLTFLoader().setDRACOLoader(draco).setKTX2Loader(ktx2).setMeshoptDecoder(MeshoptDecoder);
  const t0 = performance.now();
  const gltf = await loader.loadAsync(CFG.model);
  const load_ms = +(performance.now() - t0).toFixed(1);
  scene.add(gltf.scene);
  const mats = new Map();
  const texInfo = t => ({colorSpace: t.colorSpace, channel: t.channel, offset: arr(t.offset.toArray()), repeat: arr(t.repeat.toArray()),
    rotation: r4(t.rotation), wrapS: t.wrapS, wrapT: t.wrapT, minFilter: t.minFilter, magFilter: t.magFilter, flipY: t.flipY,
    compressed: !!t.isCompressedTexture, format: t.format, mimeType: t.userData && t.userData.mimeType,
    size: t.image ? [t.image.width, t.image.height] : (t.mipmaps && t.mipmaps[0] ? [t.mipmaps[0].width, t.mipmaps[0].height] : null),
    mipmaps: t.mipmaps ? t.mipmaps.length : 0, name: t.name});
  const matInfo = m => {
    if (mats.has(m.uuid)) return mats.get(m.uuid).id;
    const id = mats.size;
    const d = {id, name: m.name, type: m.type, side: m.side, transparent: m.transparent, depthWrite: m.depthWrite, alphaTest: m.alphaTest,
      opacity: m.opacity, vertexColors: m.vertexColors, flatShading: m.flatShading, userData: m.userData, maps: {}};
    for (const k of ['color','emissive','sheenColor','specularColor','attenuationColor']) if (m[k] && m[k].isColor) d[k] = arr(m[k].toArray());
    for (const k of ['emissiveIntensity','metalness','roughness','transmission','thickness','ior','sheen','sheenRoughness','clearcoat',
      'clearcoatRoughness','iridescence','iridescenceIOR','anisotropy','anisotropyRotation','dispersion','specularIntensity',
      'attenuationDistance','aoMapIntensity','bumpScale','lightMapIntensity','envMapIntensity']) if (m[k] !== undefined) d[k] = r4(m[k]);
    if (m.normalScale) d.normalScale = arr(m.normalScale.toArray());
    if (m.iridescenceThicknessRange) d.iridescenceThicknessRange = m.iridescenceThicknessRange;
    for (const k in m) { const v = m[k]; if (v && v.isTexture) d.maps[k] = texInfo(v); }
    mats.set(m.uuid, d); return id;
  };
  const objects = [];
  gltf.scene.traverse(o => {
    const d = {type: o.isInstancedMesh ? 'InstancedMesh' : (o.isSkinnedMesh ? 'SkinnedMesh' : o.type), name: o.name, gltfName: o.userData && o.userData.name, parent: o.parent ? o.parent.name : null,
      userData: Object.fromEntries(Object.entries(o.userData || {}).filter(([k]) => k !== 'name')),
      position: arr(o.position.toArray()), quaternion: arr(o.quaternion.toArray()), scale: arr(o.scale.toArray()), visible: o.visible};
    if (o.geometry) {
      const g = o.geometry; d.geometry = {attributes: {}, index: g.index ? {count: g.index.count, type: g.index.array.constructor.name} : null,
        morphAttributes: Object.fromEntries(Object.entries(g.morphAttributes).map(([k, v]) => [k, v.length])), morphTargetsRelative: g.morphTargetsRelative,
        groups: g.groups.length, bbox: g.boundingBox ? [arr(g.boundingBox.min.toArray()), arr(g.boundingBox.max.toArray())] : null};
      for (const [k, a] of Object.entries(g.attributes)) {
        const src = a.isInterleavedBufferAttribute ? a.data.array : a.array;
        d.geometry.attributes[k] = {itemSize: a.itemSize, array: src.constructor.name, normalized: a.normalized, count: a.count,
          interleaved: !!a.isInterleavedBufferAttribute, first: Array.from({length: a.itemSize}, (_, i) => r4(a.getComponent ? a.getComponent(0, i) : src[i]))};
      }
    }
    if (o.material) d.material = Array.isArray(o.material) ? o.material.map(matInfo) : matInfo(o.material);
    if (o.morphTargetDictionary) d.morphTargetDictionary = o.morphTargetDictionary;
    if (o.morphTargetInfluences) d.morphTargetInfluences = arr(o.morphTargetInfluences);
    if (o.isInstancedMesh) { d.instanceCount = o.count; d.instanceColor = !!o.instanceColor; }
    if (o.isSkinnedMesh) d.skeleton = {bones: o.skeleton.bones.length, boneNames: o.skeleton.bones.slice(0, 20).map(b => b.name)};
    if (o.isLight) Object.assign(d, {intensity: r4(o.intensity), color: arr(o.color.toArray()), distance: r4(o.distance), decay: r4(o.decay),
      angle: r4(o.angle), penumbra: r4(o.penumbra), castShadow: o.castShadow});
    if (o.isPerspectiveCamera) Object.assign(d, {fov: r4(o.fov), aspect: r4(o.aspect), near: r4(o.near), far: r4(o.far)});
    if (o.isOrthographicCamera) Object.assign(d, {left: r4(o.left), right: r4(o.right), top: r4(o.top), bottom: r4(o.bottom), near: r4(o.near), far: r4(o.far)});
    objects.push(d);
  });
  const animations = gltf.animations.map(c => ({name: c.name, duration: r4(c.duration), userData: c.userData,
    tracks: c.tracks.map(t => ({name: t.name, type: t.ValueTypeName, keys: t.times.length, interpolation: t.getInterpolation ? t.getInterpolation() : null,
      custom: !!(t.createInterpolant && t.createInterpolant.isInterpolantFactoryMethodGLTFCubicSpline)}))}));
  let sample = null;
  if (CFG.animSample !== null && gltf.animations.length) {
    const mixer = new THREE.AnimationMixer(gltf.scene);
    gltf.animations.forEach(c => mixer.clipAction(c).play());
    const dur = Math.max(...gltf.animations.map(c => c.duration)); mixer.setTime(dur * CFG.animSample);
    sample = {t: r4(dur * CFG.animSample), objects: []};
    gltf.scene.traverse(o => sample.objects.push({name: o.name, position: arr(o.position.toArray()), quaternion: arr(o.quaternion.toArray()),
      scale: arr(o.scale.toArray()), morph: o.morphTargetInfluences ? arr(o.morphTargetInfluences) : undefined}));
  }
  const cam = new THREE.PerspectiveCamera(40, 1, 0.01, 1000);
  const box = new THREE.Box3().setFromObject(gltf.scene); const c = box.getCenter(new THREE.Vector3()); const s = box.getSize(new THREE.Vector3()).length() || 1;
  cam.position.copy(c).add(new THREE.Vector3(0.4, 0.3, 1).normalize().multiplyScalar(s * 1.6)); cam.lookAt(c);
  renderer.render(scene, cam);
  const gl = renderer.getContext(); const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  window.__out = {three: THREE.REVISION, load_ms, extensionsUsed: gltf.parser.json.extensionsUsed || [], asset: gltf.asset,
    userData: gltf.userData, sceneName: gltf.scene.name, cameras: gltf.cameras.length,
    objects, materials: [...mats.values()], animations, animSample: sample,
    renderer: {webgl2: renderer.capabilities.isWebGL2, gpu: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'n/a',
      calls: renderer.info.render.calls, triangles: renderer.info.render.triangles, memory: {...renderer.info.memory},
      bbox_size: arr(box.getSize(new THREE.Vector3()).toArray())}};
 } catch (e) { window.__err = String(e && e.stack || e); }
 window.__done = true;
})();
</script></body></html>"""

GPU_ARGS = {"gl": ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"],
            "vulkan": ["--use-angle=vulkan", "--enable-features=Vulkan", "--ignore-gpu-blocklist"],
            "swiftshader": ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]}


def inspect(model, ver="0.186.0", anim_sample=None, gpu="gl"):
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="webinspect_")
    shutil.copy(model, os.path.join(tmp, os.path.basename(model)))
    if model.lower().endswith(".gltf"):
        src = os.path.dirname(os.path.abspath(model))
        for fn in os.listdir(src):
            p = os.path.join(src, fn)
            if os.path.isfile(p) and fn != os.path.basename(model):
                shutil.copy(p, os.path.join(tmp, fn))
        for d in os.listdir(src):  # подпапки текстур
            p = os.path.join(src, d)
            if os.path.isdir(p):
                shutil.copytree(p, os.path.join(tmp, d), dirs_exist_ok=True)
    cfg = {"ver": ver, "model": os.path.basename(model), "animSample": anim_sample}
    open(os.path.join(tmp, "index.html"), "w").write(PAGE.replace("__VER__", ver).replace("__CFG__", json.dumps(cfg)))

    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Q, directory=tmp))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    logs = []
    try:
        with kbpaths.lock("browser"), sync_playwright() as pw:
            b = pw.chromium.launch(headless=True, args=GPU_ARGS[gpu])
            p = b.new_page()
            p.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            p.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))
            p.goto(f"http://127.0.0.1:{httpd.server_address[1]}/index.html")
            p.wait_for_function("window.__done === true", timeout=180000)
            err = p.evaluate("window.__err || null")
            out = {"error": err} if err else p.evaluate("window.__out")
            b.close()
    finally:
        httpd.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
    out["console"] = logs[:50]
    out["file_kb"] = round(os.path.getsize(model) / 1024, 1)
    return out


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return
    opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    s = opt("--anim-sample")
    res = inspect(os.path.abspath(a[0]), opt("--three", "0.186.0"), float(s) if s is not None else None, opt("--gpu", "gl"))
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if opt("--out"):
        open(opt("--out"), "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
