// Проверка KHR_materials_variants в three r186: загрузка, переключение как в webgl_loader_gltf_variants,
// имена материалов и цвет пикселя в центре каждого колпачка — для каждого файла постобработки.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const FILES = ['variants_raw.glb', 'v_opt_keep.glb', 'v_pack_kn.glb', 'variants12_raw.glb', 'v12_opt_default.glb',
  'v12_opt_keep.glb', 'v12_joinoff.glb', 'v12_pack_kn.glb', 'v12_pack_cc.glb'];
const W = 360, H = 200;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.toneMapping = THREE.NeutralToneMapping;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#7a7d80');
scene.add(new THREE.HemisphereLight(0xffffff, 0x303030, 2.2));
const dl = new THREE.DirectionalLight(0xffffff, 1.6); dl.position.set(0.2, 1, 0.6); scene.add(dl);
const cam = new THREE.PerspectiveCamera(28, W / H, 0.001, 20);
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const grid = document.getElementById('grid');

async function selectVariant(root, parser, ext, name) {
  const idx = ext.variants.findIndex((v) => v.name === name);
  const jobs = [];
  root.traverse((o) => {
    if (!o.isMesh || !o.userData.gltfExtensions) return;
    const def = o.userData.gltfExtensions.KHR_materials_variants;
    if (!def) return;
    if (!o.userData.originalMaterial) o.userData.originalMaterial = o.material;
    const m = def.mappings.find((mp) => mp.variants.includes(idx));
    jobs.push((async () => {
      if (m) { o.material = await parser.getDependency('material', m.material); parser.assignFinalMaterial(o); }
      else o.material = o.userData.originalMaterial;
    })());
  });
  await Promise.all(jobs);
}

function pixelAt(v3) {
  const p = v3.clone().project(cam);
  const x = Math.round((p.x * 0.5 + 0.5) * W), y = Math.round((1 - (p.y * 0.5 + 0.5)) * H);
  const gl = renderer.getContext(); const px = new Uint8Array(4);
  gl.readPixels(x, H - y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  return '#' + [px[0], px[1], px[2]].map((c) => c.toString(16).padStart(2, '0')).join('');
}

async function main() {
  const out = {};
  for (const f of FILES) {
    const t0 = performance.now();
    const gltf = await loader.loadAsync('assets/' + f);
    const ext = gltf.userData.gltfExtensions && gltf.userData.gltfExtensions.KHR_materials_variants;
    const root = gltf.scene; scene.add(root);
    const box = new THREE.Box3().setFromObject(root); const c = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3()).length();
    cam.position.set(c.x, c.y + size * 0.9, c.z + size * 1.25); cam.lookAt(c);
    const meshes = []; root.traverse((o) => { if (o.isMesh) meshes.push(o); });
    const rec = { load_ms: Math.round(performance.now() - t0), variants: ext ? ext.variants.map((v) => v.name) : null,
      meshes: meshes.length, with_mapping: meshes.filter((o) => o.userData.gltfExtensions && o.userData.gltfExtensions.KHR_materials_variants).length,
      per_variant: {} };
    for (const vn of (rec.variants || [])) {
      await selectVariant(root, gltf.parser, ext, vn);
      renderer.render(scene, cam);
      rec.per_variant[vn] = meshes.map((o) => {
        const b = new THREE.Box3().setFromObject(o); const top = b.getCenter(new THREE.Vector3()); top.y = b.max.y;
        return { node: o.name || (o.parent && o.parent.name) || '?', material: o.material.name, color: '#' + o.material.color.getHexString(), map: !!o.material.map, pixel: pixelAt(top) };
      });
      const img = new Image(); img.src = renderer.domElement.toDataURL(); img.title = f + ' · ' + vn;
      const fig = document.createElement('figure'); fig.append(img); const cap = document.createElement('figcaption');
      cap.textContent = f + ' · ' + vn; fig.append(cap); grid.append(fig);
    }
    out[f] = rec; scene.remove(root);
  }
  window.__result = out; window.__done = true;
}
main().catch((e) => { window.__result = { error: String(e) }; window.__done = true; console.error(e); });
