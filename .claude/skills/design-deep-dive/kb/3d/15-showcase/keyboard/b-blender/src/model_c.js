// model_c.js — гибрид C: GLB из Blender (export_web.py рецепта 17 → gltfpack). Десктоп — WebP атлас 2048 (ETC1S сдвигал
// почти-серые PBT в сиреневый, а с транскодером Basis KTX2 ещё и тяжелее на 229 КБ br), телефон — WebP 512.
// • 67 колпачков — 13 общих мешей на узлах glTF (инстансы) → InstancedMesh по мешу, UV ячейки атласа — атрибут экземпляра
//   iUV из extras узла kb_uv4 (в «чужом» просмотрщике колпачки просто без надписей); Ё — свой меш и своя текстура;
// • расцветки — KHR_materials_variants: parser.getDependency('material', i) для отображения варианта (как
//   webgl_loader_gltf_variants), у InstancedMesh — тот же список отображений, что у исходного меша;
// • разборка — узлы слоёв L_keycaps / L_switches / L_stabs / Plate / PCB (дети деки: +Y локально) и Weight (по нормали деки);
// • тень пола — запечена в Blender (Cycles, ловец теней) → прозрачная плоскость с alphaMap.
import {
  InstancedMesh, InstancedBufferAttribute, Matrix4, Vector3, TextureLoader, Mesh, PlaneGeometry, MeshBasicMaterial,
  Color,
} from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

const CWS = ['snow', 'graphite', 'linen'];
const ACCENT = { snow: '#E05A2A', graphite: '#7BD3B4', linen: '#8A5234' };
const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };

function patchUV(mat) {
  if (mat.userData.kbPatched) return mat;
  mat.userData.kbPatched = true;
  // верх нажатой клавиши чуть светлее (как подсветка обвода у B) — атрибут экземпляра iPress 0…1 (глубина нажатия)
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec4 iUV;\nattribute float iPress;\nvarying float vPress;')
      .replace('#include <uv_vertex>', '#include <uv_vertex>\n#ifdef USE_MAP\n\tvMapUv = iUV.xy + iUV.zw * vMapUv;\n#endif\nvPress = iPress;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vPress;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(0.09) * vPress;');
  };
  mat.customProgramCacheKey = () => 'kb-iuv-press';
  mat.needsUpdate = true;
  return mat;
}

export async function buildModelC({ phone, idle = async () => {} }) {
  const loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  const gltf = await loader.loadAsync(phone ? 'assets/model/kb_mob.glb' : 'assets/model/kb_desk.glb');
  await idle();
  const parser = gltf.parser;
  const root = gltf.scene;
  const R = root.getObjectByName('KB_root');
  const ex = R.userData;                              // kb_explode, kb_ranges, kb_travel, kb_deck_normal_three
  const nDeck = new Vector3(...ex.kb_deck_normal_three);
  const variantNames = (gltf.userData.gltfExtensions?.KHR_materials_variants?.variants || []).map((v) => v.name);
  const layers = {
    keycaps: root.getObjectByName('L_keycaps'), switches: root.getObjectByName('L_switches'), stabs: root.getObjectByName('L_stabs'),
    plate: root.getObjectByName('Plate'), pcb: root.getObjectByName('PCB'), weight: root.getObjectByName('Weight'),
  };
  const base = {};
  for (const [k, o] of Object.entries(layers)) base[k] = o.position.clone();
  const withVariants = [];                           // [mesh, mappings]
  // ------------------------------------------------------------ колпачки → InstancedMesh по общему мешу
  const groups = new Map();
  for (const o of [...layers.keycaps.children]) {
    if (!o.isMesh) continue;
    const g = groups.get(o.geometry.uuid) || { geo: o.geometry, mat: o.material, ext: o.userData.gltfExtensions, items: [] };
    g.items.push(o);
    groups.set(o.geometry.uuid, g);
  }
  const keyRef = new Map();                          // id → [{im, i, m0}]
  const pickables = [];
  for (const g of groups.values()) {
    const n = g.items.length;
    const im = new InstancedMesh(g.geo, patchUV(g.mat), n);
    const iuv = new Float32Array(n * 4);
    g.items.forEach((o, i) => {
      o.updateMatrix();
      im.setMatrixAt(i, o.matrix);
      iuv.set(o.userData.kb_uv4 || [0, 0, 1, 1], i * 4);
      const id = o.userData.kb_id;
      keyRef.set(id, [{ im, i, m0: o.matrix.clone() }]);
      im.userData.ids = im.userData.ids || [];
      im.userData.ids[i] = id;
      layers.keycaps.remove(o);
    });
    g.geo.setAttribute('iUV', new InstancedBufferAttribute(iuv, 4));
    const ip = new InstancedBufferAttribute(new Float32Array(n), 1);
    g.geo.setAttribute('iPress', ip);
    g.items.forEach((o, i) => { keyRef.get(o.userData.kb_id)[0].press = ip; });
    im.name = `KC_inst_${g.items[0].userData.kb_id}`;
    im.userData.gltfExtensions = g.ext;
    im.userData.isKeycap = true;
    im.userData.isYo = g.items[0].userData.kb_id === 'yo';
    im.frustumCulled = false;
    layers.keycaps.add(im);
    pickables.push(im);
    if (g.ext?.KHR_materials_variants) withVariants.push(im);
  }
  // ------------------------------------------------------------ свитчи: узел = группа из 2 примитивов → 2 InstancedMesh
  const swNodes = layers.switches.children.filter((o) => o.name.startsWith('Sw_'));
  const prims = swNodes[0].isMesh ? [swNodes[0]] : swNodes[0].children.filter((c) => c.isMesh);
  const swIds = swNodes.map((o) => o.name.slice(3));
  prims.forEach((p0, pi) => {
    const im = new InstancedMesh(p0.geometry, p0.material, swNodes.length);
    swNodes.forEach((o, i) => {
      o.updateMatrix();
      const m = swNodes[0].isMesh ? o.matrix.clone() : o.matrix.clone().multiply((o.children[pi] || p0).matrix);
      im.setMatrixAt(i, m);
      const ref = keyRef.get(swIds[i]);
      if (ref) ref.push({ im, i, m0: m.clone() });
    });
    im.userData.gltfExtensions = p0.userData.gltfExtensions;
    im.frustumCulled = false;
    layers.switches.add(im);
    if (p0.userData.gltfExtensions?.KHR_materials_variants) withVariants.push(im);
  });
  for (const o of swNodes) layers.switches.remove(o);
  // ------------------------------------------------------------ остальные меши с вариантами
  root.traverse((o) => {
    if (o.isMesh && !o.isInstancedMesh && o.userData.gltfExtensions?.KHR_materials_variants) withVariants.push(o);
  });
  // Ё: материал для «особой реакции» (свечение акцентом)
  const yoIm = pickables.find((m) => m.userData.isYo);
  // ------------------------------------------------------------ тень пола (Cycles, ловец теней, ортокамера сверху)
  const sh = await fetch('assets/data/shadow_floor.json').then((r) => r.json());
  const tex = await new TextureLoader().loadAsync('assets/img/shadow_floor.webp');
  const floor = new Mesh(new PlaneGeometry(sh.extent_m[0], sh.extent_m[1]),
    new MeshBasicMaterial({ color: 0x000000, alphaMap: tex, transparent: true, depthWrite: false, toneMapped: false }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(sh.center_blender[0], 0.0002, -sh.center_blender[1]);
  floor.renderOrder = -1;
  root.add(floor);
  // ------------------------------------------------------------ API модели
  const mats = new Map();
  const getMat = async (idx, keycap) => {
    const key = `${idx}`;
    if (!mats.has(key)) mats.set(key, parser.getDependency('material', idx).then((m) => (keycap ? patchUV(m) : m)));
    return mats.get(key);
  };
  const tmp = new Matrix4();
  const off = new Vector3();
  let yoMat = null, curCw = 'snow';
  const glow = new Color();
  return {
    root,
    variants: variantNames,
    async setColorway(cw) {
      const vi = CWS.indexOf(cw);
      curCw = cw;
      await Promise.all(withVariants.map(async (m) => {
        const maps = m.userData.gltfExtensions.KHR_materials_variants.mappings;
        const mp = maps.find((x) => x.variants.includes(vi));
        if (!mp) return;
        m.material = await getMat(mp.material, !!m.userData.isKeycap);
        if (m === yoIm) yoMat = null;
      }));
    },
    setKeyOffset(id, d) {
      const refs = keyRef.get(id);
      if (!refs) return;
      for (const r of refs) {
        tmp.makeTranslation(0, -d, 0).multiply(r.m0);
        r.im.setMatrixAt(r.i, tmp);
        r.im.instanceMatrix.needsUpdate = true;
        if (r.press) { r.press.setX(r.i, Math.min(1, Math.max(0, d / 0.0038))); r.press.needsUpdate = true; }
      }
    },
    setExplode(p) {
      const E = ex.kb_explode, RG = ex.kb_ranges;
      for (const [L, o] of Object.entries(layers)) {
        const [a, b] = RG[L];
        const d = E[L] * (b > a ? smooth((p - a) / (b - a)) : 0);
        if (L === 'weight') o.position.copy(base[L]).addScaledVector(nDeck, d);
        else o.position.set(base[L].x, base[L].y + d, base[L].z);
      }
    },
    setYoGlow(t) {
      if (!yoIm) return;
      if (!yoMat) yoMat = yoIm.material;
      yoMat.emissive.copy(glow.set(ACCENT[curCw])).multiplyScalar(0.6 * t * t);
    },
    pick(ray) {
      const hit = ray.intersectObjects(pickables, false)[0];
      return hit ? hit.object.userData.ids[hit.instanceId] : null;
    },
    info: { groups: groups.size, variants: variantNames, withVariants: withVariants.length },
  };
}
