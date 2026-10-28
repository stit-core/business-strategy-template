#!/usr/bin/env python3
"""three_probe.py — загрузить GLB в three r186 (Chromium, GPU) и выполнить JS-проверку; вывести JSON.

    python3 three_probe.py MODEL.glb CHECK.js [--three 0.186.0] [--out result.json]

CHECK.js — тело async-функции с доступом к THREE, gltf, scene, renderer, camera, render(); возвращает объект (JSON).
Пример: `const m = new THREE.AnimationMixer(gltf.scene); ...; return {...}`.
Замок браузера утилита берёт сама на время работы браузера: kbpaths.lock("browser"), реентерабельный по дереву
процессов — утилита, запущенная из утилиты с тем же замком, его не ждёт.
"""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # gltf_diff.py — рядом
import gltf_diff as GD

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@__VER__/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@__VER__/examples/jsm/"}}</script></head><body>
<script type="module">
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
window.THREE = THREE;
(async () => {
  try {
    const renderer = new THREE.WebGLRenderer({antialias: true}); renderer.setSize(256, 256); document.body.appendChild(renderer.domElement);
    const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(40, 1, 0.01, 100); camera.position.set(0, 1, 4);
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync('__MODEL__');
    scene.add(gltf.scene);
    const render = () => renderer.render(scene, camera);
    const check = async (THREE, gltf, scene, renderer, camera, render) => { __CHECK__ };
    window.__res = await check(THREE, gltf, scene, renderer, camera, render);
  } catch (e) { window.__res = {error: String(e && e.stack || e)}; }
  window.__done = true;
})();
</script></body></html>"""


def run(glb, check_js, ver="0.186.0"):
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="threeprobe_")
    shutil.copy(glb, os.path.join(tmp, os.path.basename(glb)))
    open(os.path.join(tmp, "index.html"), "w").write(PAGE.replace("__VER__", ver).replace("__MODEL__", os.path.basename(glb)).replace("__CHECK__", check_js))
    httpd, port = GD.serve(tmp)
    logs = []
    try:
        with GD.kbpaths.lock("browser"), sync_playwright() as pw:
            b = pw.chromium.launch(headless=True, args=GD.GPU_ARGS["gl"])
            p = b.new_page()
            p.on("console", lambda m: logs.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
            p.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))
            p.goto(f"http://127.0.0.1:{port}/index.html")
            p.wait_for_function("window.__done === true", timeout=120000)
            res = p.evaluate("window.__res")
            b.close()
    finally:
        httpd.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
    if isinstance(res, dict):
        res["_console"] = logs[:20]
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    js = open(a[1]).read() if os.path.exists(a[1]) else a[1]
    ver = a[a.index("--three") + 1] if "--three" in a else "0.186.0"
    r = run(os.path.abspath(a[0]), js, ver)
    s = json.dumps(r, ensure_ascii=False, indent=1)
    if "--out" in a:
        open(a[a.index("--out") + 1], "w").write(s)
    print(s)
