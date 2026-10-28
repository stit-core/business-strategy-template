// modules-code.js · общий код 3D «Звена» (_shared/code3d) · процедурные модули (v2 + деталь v3) и их материалы,
// скан (плоскость отсечения + светящаяся кромка). Гибрид подменяет модули на GLB (glb-modules.js), материалы и скан — общие.
import {
  Group, Mesh, LatheGeometry, CylinderGeometry, BoxGeometry, TorusGeometry, ExtrudeGeometry, Shape, Vector2, Vector3, Color, Plane, Box3,
  MeshStandardMaterial, MeshPhysicalMaterial, DoubleSide, BufferAttribute,
} from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { withHF, hfPatch } from './world.js';
import { L1, L2 } from './rig.js';
import { SCREWS, addScrew, ringTicks, seamX, seamY, decalCylY, decalCapX, CABLE_AZ } from './detail.js';

// ---------- светодиодная полоса кольца-замка (фаза 2): лак кольца светится слабо (ниже сжатия Neutral — цвет бренда не розовеет),
// яркость вспышки несёт узкая полоса посередине пояска (атрибут band = uv.y открытого цилиндра: 0…1 поперёк пояска) — как LED у ассета Blender
export function ledPatch(m) {
  const U = { uLedK: { value: 0 }, uLedColor: { value: new Color('#ff6a2a') } };
  m.userData.led = U;
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float band; varying float vBand;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvBand = band;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vBand; uniform float uLedK; uniform vec3 uLedColor;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n' +
        '{ float led = smoothstep(0.36, 0.45, vBand) * (1.0 - smoothstep(0.55, 0.64, vBand)); totalEmissiveRadiance += uLedColor * uLedK * led; }');
  };
  m.customProgramCacheKey = () => 'led';
  return m;
}

// ---------- материалы (по ролям: shell, dark, cap, alu, copper, steel, pcb, rubber, screw, decal, ring)
const PHYS_ONLY = ['clearcoat', 'clearcoatRoughness', 'anisotropy', 'anisotropyRotation'];
export function makeMaterials(hq, F, LK = {}) {
  const P = (o) => (hq ? new MeshPhysicalMaterial(o)
    : new MeshStandardMaterial(Object.fromEntries(Object.entries(o).filter(([k]) => !PHYS_ONLY.includes(k)))));
  const M = {
    shell: P({ color: '#f2f2f0', roughness: hq ? 0.36 : 0.3, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.08 }),
    dark: P({ color: '#3a3e45', roughness: 0.48, metalness: 0.08, clearcoat: 0.5, clearcoatRoughness: 0.22 }),
    // приём 7 (texture): точёный графит — металл с круговой анизотропией: UV токарного профиля идут по окружности, направление 0 даёт
    // радиальную полосу-блик, как на задней крышке часов (zveno/art-direction.md §4 «графит точёный»); 0 байт карт. Без флага — матовый v2
    cap: F.texture ? new MeshPhysicalMaterial({ color: '#50555e', roughness: 0.3, metalness: 0.9, anisotropy: 0.8, anisotropyRotation: 0 })
      : P({ color: '#4b5058', roughness: 0.62, metalness: 0.05, clearcoat: 0.2, clearcoatRoughness: 0.45 }),
    alu: P({ color: '#b7bdc5', roughness: hq ? 0.4 : 0.36, metalness: 1, anisotropy: 0.35, anisotropyRotation: Math.PI / 2 }),
    copper: new MeshStandardMaterial({ color: '#c9824c', roughness: 0.3, metalness: 1 }),
    steel: new MeshStandardMaterial({ color: '#c6cad0', roughness: 0.2, metalness: 1 }),
    pcb: P({ color: '#16251d', roughness: 0.5, metalness: 0.1, clearcoat: 0.6, clearcoatRoughness: 0.3 }),
    rubber: new MeshStandardMaterial({ color: '#1b1d20', roughness: 0.72, metalness: 0 }),
    screw: new MeshStandardMaterial({ color: '#d4d7dc', roughness: 0.5, metalness: 1, vertexColors: true }),   // матовая сталь: при 0,32 головка давала «искру»
    decal: null,
    ringNew: () => { const m = P({ color: '#ff5a1f', roughness: 0.38, metalness: 0.02, clearcoat: 0.5, clearcoatRoughness: 0.2,
      emissive: '#ff4d14', emissiveIntensity: 0 }); if (LK.ledStrip) ledPatch(m); return __CD_WORLD__ && F.world ? withHF(m) : m; },
  };
  if (__CD_WORLD__ && F.world) for (const k of ['shell', 'dark', 'cap', 'alu', 'copper', 'steel', 'pcb', 'rubber', 'screw']) withHF(M[k]);
  return M;
}

// ---------- скан: плоскость отсечения + светящаяся кромка на срезе (работает на любом Standard/Physical — и на материалах GLB)
export const scanPlane = new Plane(new Vector3(0, -1, 0), 10);
export const scanLocal = new Plane(new Vector3(0, -1, 0), 10);
export const scanUniforms = { uScanN: { value: new Vector3(0, -1, 0) }, uScanC: { value: 10 }, uScanColor: { value: new Color('#ff6a2a') },
  uScanK: { value: 2.6 }, uScanCore: { value: 0 }, uScanCoreW: { value: 0.004 } };
export function scanify(mat) {
  const m = mat.clone();
  m.side = DoubleSide;
  m.clippingPlanes = [scanPlane];
  m.clipShadows = true;
  const hf = !!mat.userData.hf;
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, scanUniforms);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vScanW;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvScanW = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vScanW; uniform vec3 uScanN; uniform float uScanC; uniform vec3 uScanColor; uniform float uScanK, uScanCore, uScanCoreW;')
      .replace('#include <emissivemap_fragment>',
        '#include <emissivemap_fragment>\nfloat sd = dot(uScanN, vScanW) + uScanC;\n' +
        'float band = 1.0 - smoothstep(0.0, 0.018, sd);\n' +
        'float core = 1.0 - smoothstep(0.0, uScanCoreW, sd);\n' +      // фаза 2: тонкое горячее ядро (bloom) поверх оранжевой полосы
        'totalEmissiveRadiance += uScanColor * (band * uScanK + core * uScanCore);\n' +
        'if (!gl_FrontFacing) { diffuseColor.rgb *= 0.42; }');
    if (hf) hfPatch(sh);
  };
  m.customProgramCacheKey = () => (hf ? 'scan-hf' : 'scan');
  return m;
}

// ---------- геометрия (v2)
function lathe(points, segs = 64) { return new LatheGeometry(points.map(([r, y]) => new Vector2(r, y)), segs); }
function rodX(r, len, cham = 0.012, segs = 64) {
  const h = len / 2;
  const g = lathe([[0, -h], [r - cham, -h], [r, -h + cham], [r, h - cham], [r - cham, h], [0, h]], segs);
  g.rotateZ(Math.PI / 2);
  return g;
}
function ringX(r, w, x, segs = 64) { const g = new CylinderGeometry(r, r, w, segs, 1, true); g.rotateZ(Math.PI / 2); g.translate(x, 0, 0); return g; }
function discX(r, t, x, segs = 64) { const g = new CylinderGeometry(r, r, t, segs); g.rotateZ(Math.PI / 2); g.translate(x, 0, 0); return g; }
function tubeY(r, y0, y1, segs = 48) { const g = new CylinderGeometry(r, r, y1 - y0, segs); g.translate(0, (y0 + y1) / 2, 0); return g; }
function capX(r, x, dir, segs = 64) {
  const g = lathe([[0, -0.022], [r, -0.022], [r, -0.012], [0.96 * r, -0.003], [0.9 * r, 0.002], [0.8 * r, 0.002], [0.78 * r, -0.001],
    [0.76 * r, 0.002], [0.42 * r, 0.003], [0.3 * r, 0.008], [0.15 * r, 0.011], [0, 0.012]], segs);
  g.rotateZ(dir > 0 ? -Math.PI / 2 : Math.PI / 2);
  g.translate(x, 0, 0);
  return g;
}

// модуль = группа мешей по материалам (слитые геометрии) → ≤ 3–4 вызова на модуль; userData.key — роль материала
export function moduleGroup(parts, MAT) {
  const grp = new Group();
  for (const [key, geos] of Object.entries(parts)) {
    if (!geos || !geos.length) continue;
    if (key === 'ring') for (const g of geos) {                      // band: 0…1 поперёк пояска (для LED-полосы); у брусков — 0 (без полосы)
      const n = g.attributes.position.count, b = new Float32Array(n);
      if (g.type === 'CylinderGeometry' && g.attributes.uv) for (let i = 0; i < n; i++) b[i] = g.attributes.uv.getY(i);
      g.setAttribute('band', new BufferAttribute(b, 1));
    }
    const g = geos.length > 1 ? mergeGeometries(geos.map((x) => (x.index ? x.toNonIndexed() : x))) : geos[0];
    const mesh = new Mesh(g, key === 'ring' ? MAT.ringNew() : MAT[key]);
    mesh.userData.key = key;
    grp.add(mesh);
  }
  const box = new Box3().setFromObject(grp);
  grp.userData.c = box.getCenter(new Vector3());
  return grp;
}

export function buildModules(MAT, D) {                              // D — микродеталь включена
  const M = {};
  const sc = (k, x, y, z, ax, ay, az, s) => addScrew(k, new Vector3(x, y, z), new Vector3(ax, ay, az), s);
  const ring = (n, r, y, k, s = 1) => { for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2 + 0.3; sc(k, Math.cos(a) * r, y, Math.sin(a) * r, 0, 1, 0, s); } };
  const ringSide = (n, r, y, k) => { for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2 + 0.2; sc(k, Math.cos(a) * r, y, Math.sin(a) * r, Math.cos(a), 0, Math.sin(a), 0.8); } };
  const capScrews = (n, r, x, dir, k) => { for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2 + Math.PI / n; sc(k, x, Math.cos(a) * r, Math.sin(a) * r, dir, 0, 0, 0.8); } };
  SCREWS.length = 0;
  // 0 · основание
  const baseDark = [lathe([[0, 0], [0.44, 0], [0.44, 0.05], [0.34, 0.075], [0.3, 0.1], [0.3, 0.3], [0.27, 0.34], [0, 0.34]])];
  if (D) {
    ring(8, 0.39, 0.05, 'base', 1.3);                               // анкерные болты фланца
    baseDark.push((() => { const g = new BoxGeometry(0.1, 0.07, 0.09); g.translate(0, 0.14, 0.3); g.rotateY(CABLE_AZ); return g; })());   // разъём кабеля сзади-справа
    baseDark.push(seamY(0.3, 0.2));
  } else {
    baseDark.push(...[0, 1, 2, 3].map((i) => { const g = new CylinderGeometry(0.03, 0.03, 0.03, 16); const a = Math.PI / 4 + i * Math.PI / 2; g.translate(Math.cos(a) * 0.37, 0.06, Math.sin(a) * 0.37); return g; }));
  }
  M.base = moduleGroup({
    dark: baseDark,
    ring: [(() => { const g = new CylinderGeometry(0.305, 0.305, 0.04, 64, 1, true); g.translate(0, 0.3, 0); return g; })()],
    decal: D ? [decalCylY(0.3025, 0.14, 0.19, 0.55, 1.12, 'plate')] : [],          // 1024×152 → 0,05 м × 0,337 м
  }, MAT);
  // 1 · J1
  const j1Shell = [lathe([[0, 0], [0.235, 0], [0.25, 0.02], [0.25, 0.33], [0.23, 0.36], [0, 0.36]])];
  const j1Dark = [(() => { const g = new CylinderGeometry(0.2, 0.2, 0.012, 48); g.translate(0, 0.366, 0); return g; })()];
  if (D) { j1Dark.push(seamY(0.25, 0.3)); ring(6, 0.17, 0.372, 'j1', 0.9); }
  M.j1 = moduleGroup({
    shell: j1Shell,
    ring: [(() => { const g = new CylinderGeometry(0.255, 0.255, 0.035, 64, 1, true); g.translate(0, 0.035, 0); return g; })()],
    dark: j1Dark,
    decal: D ? [decalCylY(0.2512, 0.17, 0.245, 1.2, 1.53, 'logo'), decalCylY(0.2512, 0.09, 0.14, 1.2, 0.34, 'J1')] : [],   // азимут 1,2 — к камере в рабочей позе
  }, MAT);
  // 2 · J2 (плечо)
  const capDecal = (r, x, name) => [decalCapX(x + 0.0032, 0.0, 0.58 * r, 0.3 * r, 0.18 * r, 1, name), decalCapX(-x - 0.0032, 0.0, -0.58 * r, 0.3 * r, 0.18 * r, -1, name)];
  M.j2 = moduleGroup({ shell: [rodX(0.235, 0.46)], cap: [capX(0.2, 0.246, 1), capX(0.2, -0.246, -1)], ring: [ringX(0.24, 0.035, -0.19)],
    dark: D ? [...ringTicks(0.24, -0.19), seamX(0.235, 0.12)] : [], decal: D ? capDecal(0.2, 0.246, 'J2') : [] }, MAT);
  if (D) { capScrews(8, 0.172, 0.248, 1, 'j2'); capScrews(8, 0.172, -0.248, -1, 'j2'); }
  // 3 · L1
  M.l1 = moduleGroup({
    alu: [tubeY(0.1, 0.2, 0.2 + L1)],
    dark: [lathe([[0, 0.17], [0.145, 0.17], [0.145, 0.22], [0.1, 0.24], [0, 0.24]]), lathe([[0, 0.16 + L1], [0.1, 0.16 + L1], [0.14, 0.18 + L1], [0.14, 0.23 + L1], [0, 0.23 + L1]])],
    ring: [(() => { const g = new CylinderGeometry(0.15, 0.15, 0.03, 48, 1, true); g.translate(0, 0.205, 0); return g; })()],
  }, MAT);
  if (D) { ringSide(8, 0.145, 0.185, 'l1'); ringSide(8, 0.14, 0.205 + L1, 'l1'); }
  // 4 · J3 (локоть)
  M.j3 = moduleGroup({ shell: [rodX(0.2, 0.4)], cap: [capX(0.17, 0.216, 1), capX(0.17, -0.216, -1)], ring: [ringX(0.205, 0.03, 0.16)],
    dark: D ? [...ringTicks(0.205, 0.16), seamX(0.2, -0.1)] : [], decal: D ? capDecal(0.17, 0.216, 'J3') : [] }, MAT);
  if (D) { capScrews(6, 0.146, 0.218, 1, 'j3'); capScrews(6, 0.146, -0.218, -1, 'j3'); }
  // 5 · L2
  M.l2 = moduleGroup({
    alu: [tubeY(0.085, 0.17, 0.17 + L2)],
    dark: [lathe([[0, 0.15], [0.125, 0.15], [0.125, 0.19], [0.085, 0.21], [0, 0.21]]), lathe([[0, 0.13 + L2], [0.085, 0.13 + L2], [0.12, 0.15 + L2], [0.12, 0.2 + L2], [0, 0.2 + L2]])],
    ring: [(() => { const g = new CylinderGeometry(0.13, 0.13, 0.026, 48, 1, true); g.translate(0, 0.18, 0); return g; })()],
  }, MAT);
  if (D) { ringSide(6, 0.125, 0.165, 'l2'); ringSide(6, 0.12, 0.175 + L2, 'l2'); }
  // 6 · запястье
  M.wrist = moduleGroup({
    shell: [rodX(0.14, 0.28), (() => { const g = lathe([[0, 0.12], [0.11, 0.12], [0.11, 0.27], [0.1, 0.285], [0, 0.285]], 48); return g; })()],
    cap: [capX(0.12, 0.156, 1, 48), capX(0.12, -0.156, -1, 48)],
    ring: [ringX(0.145, 0.024, -0.1)],
    dark: D ? [...ringTicks(0.145, -0.1)] : [], decal: D ? capDecal(0.12, 0.156, 'J4') : [],
  }, MAT);
  if (D) { capScrews(6, 0.1, 0.158, 1, 'wrist'); capScrews(6, 0.1, -0.158, -1, 'wrist'); }
  // 7 · захват
  M.grip = moduleGroup({
    dark: [(() => { const g = new BoxGeometry(0.26, 0.07, 0.14); g.translate(0, 0.035, 0); return g; })(),
      ...[-1, 1].map((s) => { const g = new BoxGeometry(0.034, 0.17, 0.08); g.translate(s * 0.09, 0.155, 0); return g; })],
    ring: [...[-1, 1].map((s) => { const g = new BoxGeometry(0.012, 0.09, 0.066); g.translate(s * 0.07, 0.19, 0); return g; })],
    alu: [(() => { const g = new CylinderGeometry(0.1, 0.1, 0.02, 40); g.translate(0, -0.005, 0); return g; })()],
  }, MAT);
  if (D) { sc('grip', 0.105, 0.07, 0.05, 0, 1, 0, 0.7); sc('grip', -0.105, 0.07, 0.05, 0, 1, 0, 0.7); sc('grip', 0.105, 0.07, -0.05, 0, 1, 0, 0.7); sc('grip', -0.105, 0.07, -0.05, 0, 1, 0, 0.7); }
  return M;
}

// начинка сустава J3 (v2): статор-медь, сталь (колесо 72 зуба, вал, подшипник), генератор волн (dark), плата, метки энкодера (ring)
export function buildInternals(MAT) {
  const gear = new Shape();
  const teeth = 72, rOut = 0.155, rIn = 0.147;
  for (let i = 0; i <= teeth * 2; i++) {
    const a = (i / (teeth * 2)) * Math.PI * 2; const r = i % 2 ? rIn : rOut;
    if (i === 0) gear.moveTo(Math.cos(a) * r, Math.sin(a) * r); else gear.lineTo(Math.cos(a) * r, Math.sin(a) * r);
  }
  const hole = new Shape(); hole.absarc(0, 0, 0.118, 0, Math.PI * 2, true); gear.holes.push(hole);
  const gearG = new ExtrudeGeometry(gear, { depth: 0.05, bevelEnabled: false, curveSegments: 4 });
  gearG.rotateY(Math.PI / 2); gearG.translate(-0.02, 0, 0);
  const coil = [];
  for (let i = 0; i < 18; i++) { const g = new BoxGeometry(0.12, 0.022, 0.03); const a = (i / 18) * Math.PI * 2; g.translate(0.07, Math.cos(a) * 0.1, Math.sin(a) * 0.1); coil.push(g); }
  const slots = [];
  for (let i = 0; i < 64; i++) { const g = new BoxGeometry(0.006, 0.018, 0.006); const a = (i / 64) * Math.PI * 2; g.translate(-0.115, Math.cos(a) * 0.118, Math.sin(a) * 0.118); slots.push(g); }
  return moduleGroup({
    copper: [discX(0.118, 0.13, 0.07, 48), ...coil],
    steel: [gearG, discX(0.028, 0.44, 0, 24), (() => { const g = new TorusGeometry(0.168, 0.012, 12, 64); g.rotateY(Math.PI / 2); g.translate(-0.075, 0, 0); return g; })()],
    dark: [(() => { const g = new CylinderGeometry(0.11, 0.11, 0.028, 64); g.scale(1, 1, 0.82); g.rotateZ(Math.PI / 2); g.translate(-0.005, 0, 0); return g; })()],
    pcb: [discX(0.13, 0.012, -0.13, 64)],
    ring: [...slots],
  }, MAT);
}
