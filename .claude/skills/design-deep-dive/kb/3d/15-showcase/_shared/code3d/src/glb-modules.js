// glb-modules.js · общий код 3D «Звена» (_shared/code3d) — ГИБРИДНЫЙ КРЮК: модули из GLB вместо процедурных.
// Грузится отдельным чанком только при opts.glb (страница A его не качает). GLTFLoader + MeshoptDecoder (three 0.186.0).
//
// Контракт GLB (подробно — _shared/code3d/README.md):
//   • модуль = узел-ПУСТЫШКА с именем из ORDER (base, j1, j2, l1, j3, l2, wrist, grip) или extras {zveno_module: '<имя>'};
//     точка пустышки — шарнир, оси = оси three (Y вверх), метры scene.js; свой TRS пустышки код отбрасывает (позу ставит кинематика),
//     поэтому GLB можно выгружать в любой позе: геометрия берётся в системе пустышки. Дети (меши, их TRS, квантование) — как есть;
//   • роль материала — по extras {role} (Blender: свойство материала) или по имени: led, decal, ring, shell, cap, alu, steel, rubber,
//     copper, pcb, dark; роль нужна коду: led/ring — свет по сюжету (вспышка фиксации), decal — не в зеркале и без тени;
//   • начинка сустава — узел j3_inner (или extras {zveno_inner: true}) с детьми по ролям; extras детей {spread, spin} — разведение
//     слоёв по оси X (м при полном разведении) и вращение (доля угла ротора); без узла остаётся процедурная начинка кода;
//   • реквизит — узел cable (или extras {zveno_prop: 'cable'}) ставится как в GLB (мировая матрица), процедурный кабель тогда выключен.
// v2: KTX2 — если в GLB есть KHR_texture_basisu, чанк ktx2.js (KTX2Loader) догружается сам; транскодер basis — со своего
//   домена (js/basis/, кладёт build.sh --ktx2); без --ktx2 такой GLB — ошибка → модули кода. Начинка отдельным GLB — adaptInner().
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { MeshStandardMaterial, FrontSide, Box3, Vector3, Group } from 'three';
// ORDER и withHF приходят параметрами (o.order, o.withHF): чанк загрузчика зависит только от three — у сцены нет лишнего общего чанка
const ORDER0 = ['base', 'j1', 'j2', 'l1', 'j3', 'l2', 'wrist', 'grip'];

const ROLE_RULES = [
  [/led|emit|glow/i, 'led'], [/decal|print|etch|label|mark|lbl/i, 'decal'], [/ring|lock/i, 'ring'], [/shell|lacq|body|paint_white/i, 'shell'],
  [/cap/i, 'cap'], [/alu|tube/i, 'alu'], [/steel|screw|bolt|shaft/i, 'steel'], [/rubber|seal|cable/i, 'rubber'], [/copper|coil|winding/i, 'copper'],
  [/pcb|board/i, 'pcb'], [/graph|dark|black|base|collar|powder/i, 'dark'],
];
export const ROLES = ['led', 'decal', 'ring', 'shell', 'cap', 'alu', 'steel', 'rubber', 'copper', 'pcb', 'dark', 'other'];
export function roleOf(mat, obj) {
  const ex = (mat && mat.userData && (mat.userData.role || mat.userData.zveno_role)) || (obj && obj.userData && obj.userData.role);
  if (ex && ROLES.includes(ex)) return ex;
  const name = (mat && mat.name) || '';
  for (const [re, r] of ROLE_RULES) if (re.test(name)) return r;
  return 'other';
}
// роли начинки (как у процедурной): разведение слоёв по X и вращение (доля угла генератора волн)
export const INNER_SPREAD = { copper: 0.07, steel: 0, dark: -0.03, pcb: -0.07, ring: -0.07 };
export const INNER_SPIN = { dark: 1, steel: -1 / 12, ring: -1 / 12 };

// KTX2: один KTX2Loader на страницу (чанк ktx2.js — только сборка --ktx2 и только когда он нужен GLB)
let ktxMod = null;
function ktx2For(o) {
  if (__CD_KTX2__) {                                               // именно блок под define: ранний return не вырезает import() из сборки
    if (!o.renderer) return Promise.reject(new Error('KTX2: нет renderer (detectSupport)'));
    if (!ktxMod) ktxMod = import('./ktx2.js');
    return ktxMod.then((K) => K.ktx2Loader(o.renderer, typeof o.ktx2 === 'string' ? o.ktx2 : undefined, o.ktx2Workers));
  }
  return Promise.reject(new Error('GLB с KTX2 (KHR_texture_basisu), а сборка без --ktx2'));
}
// после последнего GLB страницы: закрыть воркеры транскодера (и освободить wasm-память в них)
export function releaseLoaders() { if (__CD_KTX2__ && ktxMod) { ktxMod.then((K) => K.ktx2Release()); ktxMod = null; } }

// загрузка: fetch → заглянуть в JSON-чанк (нужен ли KTX2) → разбор. o: { renderer, ktx2?: true | 'путь/к/basis/', ktx2Workers? }
//   o.ktx2 задан явно — чанк и транскодер (≈ 212 КБ br) качаются параллельно с GLB; не задан — по требованию, если GLB с KTX2.
//   gltf.load = { url, bytes, fetch_ms, parse_ms, ktx2 } — для отчёта крюка (stats().glb).
export async function loadGLB(url, o = {}) {
  const t0 = performance.now();
  if (__CD_KTX2__ && o.ktx2 && o.renderer) ktx2For(o).then((k) => k.init()).catch(() => {});
  const res = await fetch(url, { credentials: 'same-origin' });
  if (!res.ok) throw new Error(`GLB ${url}: HTTP ${res.status}`);
  const buf = await res.arrayBuffer();
  const t1 = performance.now();
  const loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  const dv = new DataView(buf);
  const isGLB = buf.byteLength > 20 && dv.getUint32(0, true) === 0x46546c67;          // 'glTF'
  const head = isGLB ? new TextDecoder().decode(new Uint8Array(buf, 20, Math.min(dv.getUint32(12, true), buf.byteLength - 20)))
    : new TextDecoder().decode(new Uint8Array(buf, 0, Math.min(buf.byteLength, 1 << 20)));
  const ktx2 = head.includes('KHR_texture_basisu');
  if (ktx2 || (__CD_KTX2__ && o.ktx2)) loader.setKTX2Loader(await ktx2For(o));
  const gltf = await loader.parseAsync(buf, url.slice(0, url.lastIndexOf('/') + 1));
  gltf.load = { url, bytes: buf.byteLength, fetch_ms: Math.round(t1 - t0), parse_ms: Math.round(performance.now() - t1), ktx2 };
  return gltf;
}

const TEX_KEYS = ['map', 'aoMap', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'alphaMap', 'clearcoatMap', 'clearcoatNormalMap',
  'clearcoatRoughnessMap', 'sheenColorMap', 'sheenRoughnessMap', 'specularIntensityMap', 'specularColorMap', 'anisotropyMap', 'iridescenceMap'];
function toStandard(m) {                                           // телефон: Physical → Standard (как у кода: без лака и анизотропии)
  if (!m.isMeshPhysicalMaterial) return m;
  const s = new MeshStandardMaterial();
  MeshStandardMaterial.prototype.copy.call(s, m);
  s.name = m.name; s.userData = { ...m.userData };
  return s;
}

// материалы и меши GLB → роли, клоны, туман, тени (один адаптер на GLB: материалы общие у мешей — адаптируются один раз)
function adapter(o) {
  const withHF = o.withHF || null;
  const matDone = new Map(), textures = new Set();
  const adaptMat = (m, role, owner) => {
    // исходный материал GLB не трогаем: адаптируется копия (одна на материал и роль; кольцо и светодиод — своя на модуль:
    // вспышка фиксации горит у одного модуля, а в GLB всей руки материал кольца обычно общий)
    const per = role === 'ring' || role === 'led';
    const key = m.uuid + '|' + role + (per ? '|' + owner : '');
    if (matDone.has(key)) return matDone.get(key);
    let r = m.clone(); r.name = m.name; r.userData = { ...m.userData };
    if (o.materials === 'code' && o.codeMat && role !== 'decal' && role !== 'other') {
      const c = per ? o.codeMat.ringNew() : (o.codeMat[role] || null);
      if (c) { const src = r; r = c.clone(); r.name = src.name + '→code:' + role; r.userData = { ...src.userData }; if (src.aoMap) { r.aoMap = src.aoMap; r.aoMapIntensity = src.aoMapIntensity; } }
    }
    if (!o.hq) r = toStandard(r);
    if (o.sides !== 'keep' && role !== 'decal') r.side = FrontSide;   // doubleSided Blender (по умолчанию) — тыльные грани закрытых тел не нужны
    r.userData.role = role; delete r.userData.hf;
    r.userData.e0 = r.emissive && r.emissiveIntensity > 0 && (r.emissive.r + r.emissive.g + r.emissive.b) > 0 ? r.emissiveIntensity : 0;
    if (o.world && withHF) withHF(r);
    for (const t of TEX_KEYS) if (r[t] && r[t].isTexture) textures.add(r[t]);
    matDone.set(key, r);
    return r;
  };
  const prep = (obj, isInner, owner) => {
    const rep = { meshes: 0, tris: 0, roles: {}, ao: false };
    obj.traverse((ch) => {
      if (!ch.isMesh) return;
      const mats = Array.isArray(ch.material) ? ch.material : [ch.material];
      const roles = mats.map((m) => roleOf(m, ch));
      const out = mats.map((m, i) => adaptMat(m, roles[i], owner));
      ch.material = Array.isArray(ch.material) ? out : out[0];
      const role = roles[0];
      ch.userData.role = role; ch.userData.key = role;             // key — как у процедурных мешей (скан, зеркало, тени)
      ch.castShadow = !!o.hq && role !== 'decal' && role !== 'led'; ch.receiveShadow = !!o.hq;
      rep.meshes += mats.length;
      const g = ch.geometry; rep.tris += Math.round((g.index ? g.index.count : g.attributes.position.count) / 3) * (ch.isInstancedMesh ? ch.count : 1);
      for (const r of roles) rep.roles[r] = (rep.roles[r] || 0) + 1;
      if (out.some((m) => m.aoMap)) rep.ao = true;
      if (isInner) {
        ch.userData.spread = ch.userData.spread ?? INNER_SPREAD[role] ?? 0;
        ch.userData.spin = ch.userData.spin ?? INNER_SPIN[role] ?? 0;
      }
    });
    return rep;
  };
  return { prep, textures };
}
// начинка: узел в системе J3 — TRS узла сбрасывается; верхний уровень — «слои» (база положения и поворота; смещение и вращение — поверх)
function prepInner(innerNode, A) {
  const inner = innerNode;
  inner.position.set(0, 0, 0); inner.quaternion.identity(); inner.scale.set(1, 1, 1);
  const rep = A.prep(inner, true, 'inner');
  inner.children.forEach((ch) => {
    ch.userData.p0x = ch.position.x; ch.userData.r0x = ch.rotation.x;
    if (ch.userData.spread === undefined) { let r = null; ch.traverse((m) => { if (!r && m.isMesh) r = m.userData; }); ch.userData.spread = r ? r.spread : 0; ch.userData.spin = r ? r.spin : 0; }
  });
  inner.userData.source = 'glb';
  return rep;
}
// узел начинки: по приоритету extras zveno_inner → имя j3_inner → имя inner; корень сцены glTF (gltf.scene) не узел —
// (ловушка: сцена с именем «inner» целиком принималась за начинку, слои не разводились)
function findInner(root) {
  let best = null, rank = 9;
  root.traverse((n) => {
    if (n === root) return;
    const ex = n.userData || {};
    const r = ex.zveno_inner ? 0 : n.name === 'j3_inner' ? 1 : n.name === 'inner' ? 2 : 9;
    if (r < rank) { best = n; rank = r; }
  });
  return best;
}

// gltf → { modules: {имя: Object3D}, inner, cable, textures: Set, report }
// o: { only?: [имена], map?: {имя кода: имя в GLB}, materials: 'glb'|'code', codeMat?: MAT сцены, hq, world, sides: 'front'|'keep' }
export function adaptModules(gltf, o = {}) {
  const ORDER = o.order || ORDER0;
  const root = gltf.scene || gltf.scenes[0];
  root.updateMatrixWorld(true);
  const byName = {}, warnings = [];
  let cableNode = null;
  const innerNode = findInner(root);
  root.traverse((n) => {
    if (n === root) return;                                        // корень сцены glTF — не модуль
    const ex = n.userData || {};
    const nm = ex.zveno_module || (ORDER.includes(n.name) ? n.name : null);
    if (nm && !byName[nm]) byName[nm] = n;
    if (!cableNode && (ex.zveno_prop === 'cable' || n.name === 'cable')) cableNode = n;
  });
  const want = (o.only && o.only.length ? o.only : ORDER).filter((k) => ORDER.includes(k));
  const pick = {};
  for (const k of want) { const src = (o.map && o.map[k]) || k; if (byName[src]) pick[k] = byName[src]; }
  // узлы открепляются от GLB-иерархии (вложенные модули, начинка, кабель) до того, как модули станут корнями сцены
  let cableWorld = null;
  if (cableNode) { cableWorld = cableNode.matrixWorld.clone(); cableNode.removeFromParent(); }
  if (innerNode) innerNode.removeFromParent();
  const used = new Set();
  const modules = {};
  const json = gltf.parser && gltf.parser.json, assoc = gltf.parser && gltf.parser.associations;
  const isMeshNode = (n) => { const a = assoc && assoc.get(n); return !!(json && a && a.nodes !== undefined && json.nodes[a.nodes].mesh !== undefined); };
  for (const k of Object.keys(pick)) {
    let n = pick[k];
    const meshNode = isMeshNode(n);
    if (used.has(n)) n = n.clone(true);                            // один узел на два модуля (проба map) — копия
    used.add(pick[k]);
    let h;
    if (!meshNode) {                                               // контракт: пустышка — её TRS = шарнир, код его отбрасывает
      n.removeFromParent();
      n.position.set(0, 0, 0); n.quaternion.identity(); n.scale.set(1, 1, 1);
      n.updateMatrix(); h = n;
    } else {
      // узел модуля сам несёт меш: в его TRS может сидеть квантование (gltf-transform) — сбросить нельзя; геометрия берётся в
      // мировых координатах GLB (ждём выгрузку модуля в начале координат)
      warnings.push(`${k}: узел «${n.name}» — меш, а не пустышка: мировой TRS узла сохранён (модуль должен лежать в начале координат)`);
      const mw = n.matrixWorld.clone();
      n.removeFromParent(); n.matrixAutoUpdate = false; n.matrix.copy(mw); n.matrix.decompose(n.position, n.quaternion, n.scale);
      h = new Group(); h.add(n);
    }
    h.matrixAutoUpdate = false; h.name = k; h.userData.source = 'glb'; h.userData.glbNode = n.name;
    modules[k] = h;
  }
  const A = adapter(o), prep = A.prep, textures = A.textures;
  const report = { modules: {}, inner: null, cable: null, warnings, found: Object.keys(byName) };
  const box = new Box3();
  for (const [k, n] of Object.entries(modules)) {
    const rep = prep(n, false, k);
    n.updateMatrixWorld(true);
    box.setFromObject(n); n.userData.c = box.getCenter(new Vector3());
    rep.bbox = [box.min.toArray().map((x) => +x.toFixed(3)), box.max.toArray().map((x) => +x.toFixed(3))];
    report.modules[k] = rep;
  }
  let inner = null;
  if (innerNode) { inner = innerNode; report.inner = prepInner(inner, A); }
  let cable = null;
  if (cableNode) {
    cable = cableNode; report.cable = prep(cable, false, 'cable');
    cable.matrixAutoUpdate = false; cable.matrix.copy(cableWorld); cable.matrixWorldNeedsUpdate = true;
  }
  return { modules, inner, cable, textures, report };
}

// начинка отдельным GLB (glb.innerUrl): из него берётся только узел j3_inner (или extras zveno_inner; слои j3in_* — его дети) в системе J3;
// остальные узлы файла не используются (предупреждение в отчёте). o — как у adaptModules (materials, codeMat, hq, world, sides, withHF).
export function adaptInner(gltf, o = {}) {
  const root = gltf.scene || gltf.scenes[0];
  root.updateMatrixWorld(true);
  const node = findInner(root), other = [];
  root.children.forEach((n) => { if (n !== node && !(node && n.getObjectById(node.id))) other.push(n.name || n.type); });
  if (!node) return { inner: null, textures: new Set(), report: { error: 'нет узла j3_inner (extras zveno_inner)', found: other } };
  node.removeFromParent();
  const A = adapter(o);
  const rep = prepInner(node, A);
  rep.layers = node.children.map((c) => c.name);
  rep.warnings = [];
  if (other.length) rep.warnings.push(`узлы вне начинки не используются: ${other.join(', ')}`);
  if (node.children.length < 2) rep.warnings.push(`у начинки ${node.children.length} слой(ёв) — слои j3in_* должны быть прямыми детьми узла начинки`);
  return { inner: node, textures: A.textures, report: rep };
}
