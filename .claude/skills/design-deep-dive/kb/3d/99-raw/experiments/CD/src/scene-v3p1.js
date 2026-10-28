// ЗАМОРОЖЕНО 25.09 20:30: исходник фазы 1 (= бандл v3p1-ref). С фазы 2 сцена живёт в 15-showcase/_shared/code3d/src/.
// scene.js v3 · L2 «Звено» — «код v3» · дорожка CD испытания 15-showcase · 2026-09-25
// three 0.186.0 (npm-trial) · esbuild 0.28.2 → 15-showcase/zveno/a-code/js/three-scene.js (+ чанк post-*.js только для десктопа)
// Исходник v2 (J2, creative-research J/04) — src/scene-v2.js: геометрия, кинематика, скан, рендер по требованию, API — оттуда.
// API для main.js не менялся: createScene(canvas, {context, dprMax, quality}) → {ready, resize, set, pointer, intro, renderNow,
// stop, dispose, stats}; добавлено: tap(x, y) (касание на телефоне), flags. Имена модулей и шарниров — как в v2
// (base, j1, j2, l1, j3, l2, wrist, grip) — дорожка Z подменит геометрию модулей на GLB из Blender.
// Приёмы v3 — каждый под своим флагом (opts.flags / ?f= в стендах) и своим define сборки (вес в КБ br):
//   studio — студия PMREM по сценам: «сборка» (длинные полосы-блики вдоль корпусов, тёплый отражатель) и «скан» (холодная,
//            контрастная — для меди и стали начинки); окружение меняется со сценой.
//   ik     — рука тянется к курсору: аналитическая IK на 2 звена + поворот основания + наклон кисти; телефон — касание;
//            кадры только по вводу, хвост ≤ 0,9 с после последнего движения указателя.
//   world  — мир вокруг: тёмный пол с отражением (зеркальный проход в ½ разрешения, размытие по высоте над полом),
//            туман по высоте в каждом материале, горизонт и дальние световые полосы цеха.
//   ao     — AO на стыках: N8AO (половина разрешения, нормали из глубины) в цепочке pmndrs postprocessing.
//   fx     — свет по сюжету (вспышка кольца светит на соседние корпуса, плоскость скана светит на начинку) +
//            bloom по яркости (горят только кольца и кромка скана) + LUT (своя, процедурная) + зерно.
//   detail — процедурная микродеталь: винты (один InstancedMesh на всю руку), кабель у основания (TubeGeometry с провисом),
//            маркировка canvas-текстурой («ЗВЕНО», J1…J4, шильдик), риски на кольцах-замках, швы 0,3 мм.
// Правила ворот не меняются: 0 кадров в покое, один контекст, DPR ≤ 1,5 (телефон 1,25), текст — только в HTML.
import {
  WebGLRenderer, Scene, PerspectiveCamera, OrthographicCamera, Group, Mesh, Object3D, LatheGeometry, CylinderGeometry, BoxGeometry,
  TorusGeometry, ExtrudeGeometry, Shape, Vector2, Vector3, Vector4, Matrix4, Quaternion, Euler, Color, MeshStandardMaterial,
  MeshPhysicalMaterial, MeshBasicMaterial, MeshLambertMaterial, ShaderMaterial, PlaneGeometry, SphereGeometry, BufferGeometry,
  Float32BufferAttribute, CanvasTexture, Plane, PMREMGenerator, AgXToneMapping, NeutralToneMapping, ACESFilmicToneMapping,
  NoToneMapping, SRGBColorSpace, DirectionalLight, PointLight, DoubleSide, BackSide, PCFShadowMap, Box3, InstancedMesh,
  WebGLRenderTarget, HalfFloatType, LinearFilter, Raycaster, CatmullRomCurve3, TubeGeometry, CustomBlending, AddEquation, SrcAlphaFactor,
  OneFactor, ZeroFactor,
} from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

export const version = 'zveno-scene v3 (CD code v3) 2026-09-25';

// сборочные выключатели (esbuild --define): вес каждого приёма в КБ br меряется сборкой без него (build.sh)
// (условия ниже пишут __CD_*__ прямо — esbuild сворачивает `false && …` и выбрасывает код приёма и его функции)

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const lerp = (a, b, t) => a + (b - a) * t;
const bump = (x, a, b, c) => (x <= a || x >= c ? 0 : x < b ? ease(seg(x, a, b)) : 1 - ease(seg(x, b, c)));
const snap = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : 1 - Math.exp(-6 * u) * Math.cos(9 * u));
const TONE = { agx: AgXToneMapping, neutral: NeutralToneMapping, aces: ACESFilmicToneMapping };

// Khronos PBR Neutral: обратная функция для тёмных цветов (фон, туман, горизонт). v3 пропускает фон через тот же тон-маппинг,
// что и сцену (иначе туман на полу и фон расходятся ступенькой на горизонте), поэтому цвет страницы задаётся «до тона»:
// Neutral(exp·x) = hex. Для x < 0.08 у Neutral «носок» x − 6,25x² снимается со всех каналов — тёмный серый темнеет в 5–10 раз.
function preTone(hex, exposure) {
  const c = new Color(hex);                                       // линейные значения
  const ym = Math.min(c.r, c.g, c.b);
  let off;
  if (ym < 0.04) { const xm = Math.sqrt(ym / 6.25); off = xm - ym; } else off = 0.04;
  return new Color((c.r + off) / exposure, (c.g + off) / exposure, (c.b + off) / exposure);
}

// ---------- туман по высоте + зеркальный проход: общие uniform всех материалов (onBeforeCompile, один кэш-ключ на тип)
const HF = {
  uHF: { value: new Vector4(0.0, 0.5, 6, 0) },                   // x — плотность 1/м (0 — нет тумана), y — спад по высоте 1/м, z — старт, м
  uHFColor: { value: new Color(0, 0, 0) },                       // цвет тумана «до тона» (preTone)
  uMirrorPass: { value: 0 },                                     // 1 — рисуем отражение: в альфу пишем «близость к полу»
  uHalo: { value: new Vector4(0, 0, -1, 0) },                    // ореол в дымке за объектом: xyz — направление из камеры, w — сила
  uHaloColor: { value: new Color(0.007, 0.008, 0.011) },          // ореол тихий: фон кадра ≈ фон страницы (ΔE ≤ 3, img_metrics)
};
const HF_VERT_PARS = 'varying vec3 vHFW;';
const HF_VERT = '{ vec4 hw = vec4(transformed, 1.0);\n#ifdef USE_INSTANCING\nhw = instanceMatrix * hw;\n#endif\nhw = modelMatrix * hw; vHFW = hw.xyz; }';
const HF_FRAG_PARS = 'varying vec3 vHFW; uniform vec4 uHF; uniform vec3 uHFColor; uniform float uMirrorPass; uniform vec4 uHalo; uniform vec3 uHaloColor;';
const HF_FRAG = `
{ float hd = distance(vHFW, cameraPosition);
  float hf = (1.0 - exp(-uHF.x * max(hd - uHF.z, 0.0))) * exp(-uHF.y * max(vHFW.y, 0.0));
  vec3 vd = normalize(vHFW - cameraPosition);
  vec3 fc = uHFColor + uHaloColor * uHalo.w * exp(-(1.0 - dot(vd, uHalo.xyz)) * 36.0);   // та же формула, что у фона: шва на горизонте нет
  outgoingLight = mix(outgoingLight, fc, clamp(hf, 0.0, 1.0)); }
`;
const HF_MIRROR = 'if (uMirrorPass > 0.5) gl_FragColor.a = 1.0 - clamp(vHFW.y * 0.6, 0.0, 1.0);\n';
function hfPatch(sh, extra) {
  Object.assign(sh.uniforms, HF, extra ? extra.uniforms : null);
  sh.vertexShader = sh.vertexShader
    .replace('#include <common>', `#include <common>\n${HF_VERT_PARS}\n${extra ? extra.vertPars || '' : ''}`)
    .replace('#include <fog_vertex>', `#include <fog_vertex>\n${HF_VERT}\n${extra ? extra.vert || '' : ''}`);
  sh.fragmentShader = sh.fragmentShader
    .replace('#include <common>', `#include <common>\n${HF_FRAG_PARS}\n${extra ? extra.fragPars || '' : ''}`)
    .replace('#include <opaque_fragment>', `${extra ? extra.frag || '' : ''}\n${HF_FRAG}\n#include <opaque_fragment>\n${HF_MIRROR}`);
}
function withHF(mat, key = 'hf') {                                 // материал сцены «Звена» получает туман и зеркальную альфу
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => { if (prev && prev !== withHF.noop) prev(sh, r); hfPatch(sh); };
  const prevKey = mat.customProgramCacheKey.bind(mat);
  mat.customProgramCacheKey = () => key + prevKey();
  return mat;
}
withHF.noop = MeshStandardMaterial.prototype.onBeforeCompile;

// ---------- материалы
const PHYS_ONLY = ['clearcoat', 'clearcoatRoughness', 'anisotropy', 'anisotropyRotation'];
function makeMaterials(hq, F) {
  const P = (o) => (hq ? new MeshPhysicalMaterial(o)
    : new MeshStandardMaterial(Object.fromEntries(Object.entries(o).filter(([k]) => !PHYS_ONLY.includes(k)))));
  const M = {
    shell: P({ color: '#f2f2f0', roughness: hq ? 0.36 : 0.3, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.08 }),
    dark: P({ color: '#3a3e45', roughness: 0.48, metalness: 0.08, clearcoat: 0.5, clearcoatRoughness: 0.22 }),
    // приём 7 (texture): точёный графит — металл с круговой анизотропией: UV токарного профиля идут по окружности, направление 0 даёт
    // радиальную полосу-блик, как на задней крышке часов (паспорт Z §4 «графит точёный»); 0 байт карт. Без флага — матовый v2
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
      emissive: '#ff4d14', emissiveIntensity: 0 }); return __CD_WORLD__ && F.world ? withHF(m) : m; },
  };
  if (__CD_WORLD__ && F.world) for (const k of ['shell', 'dark', 'cap', 'alu', 'copper', 'steel', 'pcb', 'rubber', 'screw']) withHF(M[k]);
  return M;
}

// ---------- скан: плоскость отсечения + светящаяся кромка на срезе
const scanPlane = new Plane(new Vector3(0, -1, 0), 10);
const scanLocal = new Plane(new Vector3(0, -1, 0), 10);
const scanUniforms = { uScanN: { value: new Vector3(0, -1, 0) }, uScanC: { value: 10 }, uScanColor: { value: new Color('#ff6a2a') },
  uScanK: { value: 2.6 } };
function scanify(mat) {
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
      .replace('#include <common>', '#include <common>\nvarying vec3 vScanW; uniform vec3 uScanN; uniform float uScanC; uniform vec3 uScanColor; uniform float uScanK;')
      .replace('#include <emissivemap_fragment>',
        '#include <emissivemap_fragment>\nfloat sd = dot(uScanN, vScanW) + uScanC;\n' +
        'float band = 1.0 - smoothstep(0.0, 0.018, sd);\n' +
        'totalEmissiveRadiance += uScanColor * band * uScanK;\n' +
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

// ---------- микродеталь (detail): винты (локальные матрицы в системе модуля), риски колец, швы, наклейки
const SCREWS = [];                                                 // {k: модуль, m: Matrix4 в системе модуля}
function addScrew(k, pos, axis, s = 1) {                           // axis — направление «из детали» (нормаль к площадке)
  const q = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), axis.clone().normalize());
  SCREWS.push({ k, m: new Matrix4().compose(pos, q, new Vector3(s, s, s)) });
}
function screwGeometry() {                                          // головка винта с внутренним шестигранником: сталь + тёмное гнездо
  const r = 0.0085, h = 0.006;
  const g = lathe([[0, 0.0035], [0.45 * r, 0.0035], [0.45 * r, h], [0.86 * r, h], [r, 0.82 * h], [r, -0.002], [0, -0.002]], 12);
  const pos = g.attributes.position, col = [];
  for (let i = 0; i < pos.count; i++) { const rr = Math.hypot(pos.getX(i), pos.getZ(i)); const dk = rr < 0.5 * r && pos.getY(i) < h - 1e-4 ? 0.12 : 1; col.push(dk, dk, dk); }
  g.setAttribute('color', new Float32BufferAttribute(col, 3));
  return g;
}
function ringTicks(r, x, n = 4, axisX = true) {                    // риски кольца-замка: видно, что кольцо повернулось на 90°
  const out = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + Math.PI / 4;
    const g = new BoxGeometry(axisX ? 0.02 : 0.008, axisX ? 0.008 : 0.02, 0.006);
    if (axisX) g.translate(x, Math.cos(a) * (r + 0.002), Math.sin(a) * (r + 0.002));
    out.push(g);
  }
  return out;
}
function seamX(r, x) { const g = new CylinderGeometry(r + 0.0004, r + 0.0004, 0.0028, 64, 1, true); g.rotateZ(Math.PI / 2); g.translate(x, 0, 0); return g; }
function seamY(r, y) { const g = new CylinderGeometry(r + 0.0004, r + 0.0004, 0.0028, 64, 1, true); g.translate(0, y, 0); return g; }

// атлас маркировки 1024×512: логотип, J1…J4, шильдик основания (цвет «напечатан» в текстуре)
const ATLAS = { logo: [0, 0, 1024, 200], J1: [0, 200, 256, 150], J2: [256, 200, 256, 150], J3: [512, 200, 256, 150], J4: [768, 200, 256, 150],
  plate: [0, 360, 1024, 152] };
function makeAtlas(fontFamily) {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 512;
  const x = c.getContext('2d');
  x.clearRect(0, 0, 1024, 512);
  const fam = fontFamily || '"Science Gothic", "Arial Narrow", "DejaVu Sans Condensed", sans-serif';
  // логотип: знак (два кольца) + слово — графит на белом лаке
  x.strokeStyle = '#ff5a1f'; x.lineWidth = 14;
  x.beginPath(); x.arc(90, 100, 46, 0, Math.PI * 2); x.stroke(); x.beginPath(); x.arc(172, 100, 46, 0, Math.PI * 2); x.stroke();
  x.fillStyle = '#2b2e33'; x.textBaseline = 'middle';
  x.font = `800 128px ${fam}`; try { x.fontStretch = 'extra-condensed'; } catch (e) { /* старые движки */ }
  x.fillText('ЗВЕНО', 250, 106);
  // метки суставов — светло-серые на графитовых крышках
  x.font = `700 104px ${fam}`; x.fillStyle = '#c9ccd1'; x.textAlign = 'center';
  ['J1', 'J2', 'J3', 'J4'].forEach((t, i) => x.fillText(t, 128 + i * 256, 278));
  // шильдик основания: светлый текст на тёмном
  x.textAlign = 'left'; x.font = `600 56px ${fam}`; x.fillStyle = '#b9bdc4';
  x.fillText('ЗВЕНО · 24 В · IP54 · 5 кг', 24, 436);
  const t = new CanvasTexture(c); t.colorSpace = SRGBColorSpace; t.anisotropy = 4;
  return t;
}
function uvRect(name) { const [x, y, w, h] = ATLAS[name]; return [x / 1024, 1 - (y + h) / 512, (x + w) / 1024, 1 - y / 512]; }
// наклейка на цилиндр оси Y: радиус r, высоты y0..y1, центр по азимуту a (рад от +Z к +X), угловая ширина span
function decalCylY(r, y0, y1, a, span, name, n = 18) {
  const [u0, v0, u1, v1] = uvRect(name); const p = [], uv = [], nr = [], idx = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, ang = a - span / 2 + span * t, sx = Math.sin(ang), sz = Math.cos(ang);
    for (let j = 0; j <= 1; j++) { const y = j ? y1 : y0; p.push(sx * r, y, sz * r); nr.push(sx, 0, sz); uv.push(lerp(u0, u1, t), j ? v1 : v0); }
  }
  for (let i = 0; i < n; i++) { const a0 = i * 2; idx.push(a0, a0 + 2, a0 + 1, a0 + 1, a0 + 2, a0 + 3); }
  const g = new BufferGeometry(); g.setAttribute('position', new Float32BufferAttribute(p, 3)); g.setAttribute('normal', new Float32BufferAttribute(nr, 3));
  g.setAttribute('uv', new Float32BufferAttribute(uv, 2)); g.setIndex(idx); return g;
}
// наклейка на торец крышки (плоскость ⊥ X): центр (x, cy, cz), размер w×h, лицом в +X (dir 1) или −X
function decalCapX(x, cy, cz, w, h, dir, name) {
  const g = new PlaneGeometry(w, h); const [u0, v0, u1, v1] = uvRect(name);
  const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, lerp(u0, u1, uv.getX(i)), lerp(v0, v1, uv.getY(i)));
  g.rotateY(dir > 0 ? Math.PI / 2 : -Math.PI / 2); g.translate(x, cy, cz); return g;
}

// модуль = группа мешей по материалам (слитые геометрии) → ≤ 3–4 вызова на модуль
function moduleGroup(parts, MAT) {
  const grp = new Group();
  for (const [key, geos] of Object.entries(parts)) {
    if (!geos || !geos.length) continue;
    const g = geos.length > 1 ? mergeGeometries(geos.map((x) => (x.index ? x.toNonIndexed() : x))) : geos[0];
    const mesh = new Mesh(g, key === 'ring' ? MAT.ringNew() : MAT[key]);
    mesh.userData.key = key;
    grp.add(mesh);
  }
  const box = new Box3().setFromObject(grp);
  grp.userData.c = box.getCenter(new Vector3());
  return grp;
}

const L1 = 0.78, L2 = 0.62;
const CABLE_AZ = 2.86;                                              // азимут разъёма: от камеры и вправо — кабель уходит в туман справа
function buildModules(MAT, D) {                                     // D — микродеталь включена
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

// начинка сустава J3 (v2)
function buildInternals(MAT) {
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

// ---------- студия для PMREM: v2 (одна) и v3 (по сценам)
function studioBase(floor = [0.05, 0.05, 0.055], hor = [0.06, 0.062, 0.07], top = [0.018, 0.019, 0.023]) {
  const s = new Scene();
  const v3 = (a) => `vec3(${a.map((x) => x.toFixed(4)).join(',')})`;
  s.add(new Mesh(new SphereGeometry(40, 32, 16), new ShaderMaterial({
    side: BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vD; void main() { vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `varying vec3 vD; void main() { float y = vD.y;
      vec3 c = y < 0.0 ? mix(${v3(floor)}, vec3(0.006), smoothstep(0.0, 0.25, -y)) : mix(${v3(hor)}, ${v3(top)}, smoothstep(0.0, 0.6, y));
      gl_FragColor = vec4(c, 1.0); }`,
  })));
  const quad = new PlaneGeometry(1, 1);
  const lamp = (w, h, x, y, z, color, k, look = [0, 1.2, 0]) => {
    const m = new Mesh(quad, new MeshLambertMaterial({ color: 0x000000, emissive: new Color(color), emissiveIntensity: k, side: DoubleSide }));
    m.scale.set(w, h, 1); m.position.set(x, y, z); m.lookAt(...look); s.add(m); return m;
  };
  return { s, lamp };
}
function studioV2() {
  const { s, lamp } = studioBase();
  lamp(8, 8, -2.5, 12, 3, '#fdfdff', 5); lamp(1.1, 9, -9, 4, 2, '#ffffff', 8); lamp(1.1, 9, 8.5, 4, -3.5, '#dce6ff', 6);
  lamp(12, 5, 1, 2.5, 13, '#ffffff', 1.6); lamp(7, 6, 8, 3.5, 8, '#ffffff', 2.4); lamp(4, 1.4, 6, 0.4, 6, '#ff6d2e', 0.6);
  return s;
}
// v3 «сборка»: к v2 — две длинные горизонтальные полосы (блик-линия вдоль корпусов суставов, оси которых горизонтальны),
// широкий верхний софтбокс шире и мягче, слабый отскок от пола, отражатель в фирменном цвете чуть сильнее (металл «тёплый»)
function studioStory() {
  const { s, lamp } = studioBase([0.035, 0.036, 0.04]);
  lamp(10, 7, -2, 12, 2, '#fdfdff', 4.2);                         // верх: шире, мягче
  lamp(1.1, 9, -9, 4, 2, '#ffffff', 7);                           // полоса слева (вертикальная)
  lamp(14, 0.7, 0, 6.5, 9, '#ffffff', 6.5);                       // длинная горизонтальная полоса спереди-сверху → линия блика на лаке
  lamp(14, 0.45, 2, 2.2, 10, '#ffffff', 3.8);                     // вторая, ниже — двойная линия на цилиндрах (9 и 5 давали пересвет 2–4 %)
  lamp(1.0, 9, 8.5, 4, -3.5, '#dce6ff', 6.5);                     // контровой справа-сзади (холодный)
  lamp(1.0, 7, -7, 3.5, -6, '#e8eeff', 4.5);                      // контровой слева-сзади — силуэт с двух сторон (±135°)
  lamp(12, 5, 1, 2.5, 13, '#ffffff', 1.3);                        // заливка
  lamp(4, 1.4, 6, 0.4, 6, '#ff6d2e', 0.9);                        // отражатель в фирменном цвете
  lamp(16, 16, 0, -3, 0, '#1a1b1e', 1.0, [0, 1, 0]);              // отскок пола
  return s;
}
// v3 «скан»: холоднее и контрастнее — медь и сталь начинки ловят полосы, белый корпус не «плывёт»
function studioScan() {
  const { s, lamp } = studioBase([0.02, 0.022, 0.028], [0.03, 0.034, 0.045], [0.01, 0.011, 0.016]);
  lamp(8, 6, -1, 11, 2, '#f4f7ff', 4.5);
  lamp(0.8, 10, -8.5, 4, 3, '#ffffff', 9);
  lamp(0.8, 10, 7.5, 4, -5, '#cfe0ff', 8);
  lamp(0.6, 8, -4, 4, -8, '#bcd3ff', 7);
  lamp(14, 0.6, 0, 5.5, 10, '#ffffff', 7);
  lamp(10, 4, 1, 2.0, 12, '#ffffff', 0.9);
  lamp(3, 1.2, 5, 0.3, 5, '#ff6d2e', 1.2);
  return s;
}

// ---------- фон: v2 (экранный) и v3 (мировой: горизонт + ореол за объектом); фон идёт через тот же тон-маппинг
function backdrop(worldMode, exposure, usePost) {
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  // мир: фон проходит тот же тон, что и сцена (цвета «до тона»); v2: как в v2 — без тона и в hex, но с постом — «до тона»
  const pt = (h) => (worldMode || usePost ? preTone(h, exposure) : new Color(h));
  const m = new Mesh(g, new ShaderMaterial({
    depthTest: false, depthWrite: false, toneMapped: !!worldMode,
    uniforms: {
      uGlow: { value: new Vector2(0.64, 0.55) }, uAspect: { value: 1.6 }, uR: { value: 0.5 },
      uTop: { value: pt(worldMode ? '#0a0b0d' : '#111317') }, uBot: { value: pt('#08090b') }, uHor: { value: pt('#111317') },
      uHalo: { value: pt('#1d2129') }, uWarm: { value: pt('#22160f') },
      uInvVP: { value: new Matrix4() }, uCam: { value: new Vector3() }, uDither: { value: 1 }, uHalo2: { value: 1 },
      uHaloW: HF.uHalo, uHaloColor: HF.uHaloColor,
    },
    vertexShader: 'varying vec2 vUv; void main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 1.0, 1.0); }',
    fragmentShader: `
      uniform vec2 uGlow; uniform float uAspect, uR, uDither, uHalo2; uniform vec3 uTop, uBot, uHor, uHalo, uWarm, uCam, uHaloColor; uniform vec4 uHaloW; uniform mat4 uInvVP; varying vec2 vUv;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      void main() {
        vec2 d = (vUv - uGlow) * vec2(uAspect, 1.0);
        ${worldMode ? `
        vec4 wp = uInvVP * vec4(vUv * 2.0 - 1.0, 1.0, 1.0); vec3 dir = normalize(wp.xyz / wp.w - uCam);
        float el = dir.y;
        vec3 c = el < 0.0 ? uHor : mix(uHor, uTop, smoothstep(0.0, 0.42, el));   // ниже горизонта — цвет тумана: край пола не виден
        c += uHaloColor * uHaloW.w * exp(-(1.0 - dot(dir, uHaloW.xyz)) * 36.0);  // ореол в дымке — та же формула в тумане пола
        ` : `
        vec3 c = mix(uBot, uTop, smoothstep(0.0, 1.0, vUv.y));
        c += uHalo * exp(-dot(d, d) / (uR * uR));
        vec2 w = d + vec2(0.0, 0.42);
        c += uWarm * exp(-dot(w, w) / (0.35 * uR * uR));
        `}
        ${worldMode ? '' : 'vec2 v = vUv - 0.5; c *= 1.0 - 0.7 * dot(v, v);'}
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        gl_FragColor.rgb += uDither * (hash(gl_FragCoord.xy) - 0.5) / 255.0;
      }`,
  }));
  m.frustumCulled = false; m.renderOrder = -10;
  return m;
}

// ---------- пол: v2 (циклорама с альфой) и v3 (большой тёмный пол с отражением и туманом)
function floorV2(hq, MAT) {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const x = c.getContext('2d'); const gr = x.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.3, '#b4b4b4'); gr.addColorStop(0.62, '#383838'); gr.addColorStop(1, '#000000');
  x.fillStyle = gr; x.fillRect(0, 0, 256, 256);
  const m = new Mesh(new PlaneGeometry(7, 7), new MeshStandardMaterial({ color: '#101215', roughness: 0.86, metalness: 0,
    transparent: true, alphaMap: new CanvasTexture(c), depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.position.y = -0.001; m.receiveShadow = hq; m.renderOrder = -6;
  return m;
}
function floorV3(hq, mirror) {
  // тёмный пол: студию PMREM (лампы-полосы для бликов на лаке) пол почти не отражает — иначе на скользящих углах он серый (L* 50+);
  // отражает он зеркальный проход (предметы) — это и есть «мир»
  // и прямой блик ключа тоже почти не берёт: при шероховатости 0,62 и F0 0,04 широкий лепесток GGX ложился серой вуалью под текстом
  const mat = new MeshPhysicalMaterial({ color: '#0c0d0f', roughness: 0.78, metalness: 0, envMapIntensity: 0.06, specularIntensity: 0.18 });
  const U = { uMir: { value: mirror ? mirror.sharp.texture : null }, uMirB: { value: mirror ? mirror.blur.texture : null },
    uTexMat: { value: mirror ? mirror.texMat : new Matrix4() }, uReflK: { value: mirror ? 0.5 : 0 } };
  mat.onBeforeCompile = (sh) => hfPatch(sh, mirror ? {
    uniforms: U,
    vertPars: 'varying vec4 vMirUv; uniform mat4 uTexMat;',
    vert: 'vMirUv = uTexMat * vec4(vHFW, 1.0);',
    fragPars: 'varying vec4 vMirUv; uniform sampler2D uMir; uniform sampler2D uMirB; uniform float uReflK;',
    frag: `{ vec2 muv = vMirUv.xy / vMirUv.w;
      vec4 rs = texture2D(uMir, muv); vec4 rb = texture2D(uMirB, muv);
      float nearF = rs.a;                                                   // 1 у самого пола → резкое, выше — размытое
      vec3 refl = mix(rb.rgb, rs.rgb, nearF * nearF);
      float nv = clamp(dot(normalize(vViewPosition), normal), 0.0, 1.0);
      float fres = 0.1 + 0.9 * pow(1.0 - nv, 4.0);
      outgoingLight += refl * uReflK * fres; }`,
  } : null);
  mat.customProgramCacheKey = () => (mirror ? 'floor-mirror' : 'floor-hf');
  const m = new Mesh(new PlaneGeometry(400, 400), mat);
  m.rotation.x = -Math.PI / 2; m.position.y = -0.001; m.receiveShadow = hq; m.renderOrder = -6;
  m.userData.U = U;
  return m;
}
function contactShadow() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d'); const gr = x.createRadialGradient(64, 64, 4, 64, 64, 64);
  gr.addColorStop(0, 'rgba(0,0,0,0.6)'); gr.addColorStop(0.5, 'rgba(0,0,0,0.22)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
  const m = new Mesh(new PlaneGeometry(1.7, 1.7), new MeshBasicMaterial({ map: new CanvasTexture(c), transparent: true, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.position.y = 0.002; m.renderOrder = -5;
  return m;
}
// дальние полосы света цеха (world): белые, мягкие, в тумане; их же видно в отражении пола — мир, который отражают корпуса
function farBars() {
  const c = document.createElement('canvas'); c.width = 16; c.height = 256;
  const x = c.getContext('2d'); const gr = x.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(0.18, 'rgba(255,255,255,1)'); gr.addColorStop(0.82, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 16, 256);
  const hx = x.createLinearGradient(0, 0, 16, 0); hx.addColorStop(0, 'rgba(0,0,0,1)'); hx.addColorStop(0.5, 'rgba(0,0,0,0)'); hx.addColorStop(1, 'rgba(0,0,0,1)');
  x.globalCompositeOperation = 'destination-out'; x.fillStyle = hx; x.fillRect(0, 0, 16, 256);
  const tex = new CanvasTexture(c);
  // сложение цвета без записи альфы: в зеркальном проходе альфа = «близость к полу», полосы её не трогают (отражение — размытое)
  const mat = new MeshBasicMaterial({ color: new Color(0.55, 0.57, 0.62), map: tex, transparent: true, depthWrite: false, fog: false,
    blending: CustomBlending, blendEquation: AddEquation, blendSrc: SrcAlphaFactor, blendDst: OneFactor, blendSrcAlpha: ZeroFactor, blendDstAlpha: OneFactor });
  const g = new Group();
  [[-7.5, -16], [-3.5, -19], [1.5, -21], [6.5, -19.5], [11, -16.5]].forEach(([px, pz], i) => {
    const m = new Mesh(new PlaneGeometry(0.34, 5.2), mat); m.position.set(px, 2.9, pz); m.lookAt(0, 2.9, 0); m.renderOrder = -8; g.add(m);
  });
  return g;
}

// ---------- зеркальный проход (world, десктоп): отражение пола y = 0 в ½ разрешения + размытие в ¼ (Reflector three — логика)
function createMirror(renderer) {
  const opt = { type: HalfFloatType, minFilter: LinearFilter, magFilter: LinearFilter, depthBuffer: true };
  const sharp = new WebGLRenderTarget(2, 2, opt), blurA = new WebGLRenderTarget(2, 2, { ...opt, depthBuffer: false }),
    blur = new WebGLRenderTarget(2, 2, { ...opt, depthBuffer: false });
  const vcam = new PerspectiveCamera(), texMat = new Matrix4();
  const N = new Vector3(0, 1, 0), P0 = new Vector3(0, 0, 0), camP = new Vector3(), look = new Vector3(), tgt = new Vector3(), rot = new Matrix4();
  const clipPlane = new Vector4(), q = new Vector4(), pl = new Plane();
  const fsGeo = new BufferGeometry(); fsGeo.setAttribute('position', new Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  const blurMat = new ShaderMaterial({
    depthTest: false, depthWrite: false, uniforms: { tMap: { value: null }, uDir: { value: new Vector2() } },
    vertexShader: 'varying vec2 vUv; void main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: `uniform sampler2D tMap; uniform vec2 uDir; varying vec2 vUv;
      void main() { vec4 s = texture2D(tMap, vUv) * 0.227027;
        s += (texture2D(tMap, vUv + uDir * 1.3846) + texture2D(tMap, vUv - uDir * 1.3846)) * 0.3162162;
        s += (texture2D(tMap, vUv + uDir * 3.2308) + texture2D(tMap, vUv - uDir * 3.2308)) * 0.0702703;
        gl_FragColor = s; }`,
  });
  const fs = new Mesh(fsGeo, blurMat); fs.frustumCulled = false;
  const fsScene = new Scene(); fsScene.add(fs); const ocam = new OrthographicCamera(-1, 1, 1, -1, 0, 1);
  let w = 2, h = 2;
  function setSize(W, H) { w = Math.max(2, Math.round(W * 0.5)); h = Math.max(2, Math.round(H * 0.5)); sharp.setSize(w, h); blurA.setSize(w >> 1, h >> 1); blur.setSize(w >> 1, h >> 1); }
  function blurPass(src, dst, dx, dy) { blurMat.uniforms.tMap.value = src.texture; blurMat.uniforms.uDir.value.set(dx, dy); renderer.setRenderTarget(dst); renderer.render(fsScene, ocam); }
  function render(scene, camera, hide) {
    camP.setFromMatrixPosition(camera.matrixWorld);
    if (camP.y <= 0.01) return false;
    const view = P0.clone().sub(camP).reflect(N).negate().add(P0);
    rot.extractRotation(camera.matrixWorld);
    look.set(0, 0, -1).applyMatrix4(rot).add(camP);
    tgt.subVectors(P0, look).reflect(N).negate().add(P0);
    vcam.position.copy(view); vcam.up.set(0, 1, 0).applyMatrix4(rot).reflect(N); vcam.lookAt(tgt);
    vcam.far = camera.far; vcam.near = camera.near; vcam.updateMatrixWorld();
    vcam.projectionMatrix.copy(camera.projectionMatrix);
    texMat.set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1).multiply(vcam.projectionMatrix).multiply(vcam.matrixWorldInverse);
    pl.setFromNormalAndCoplanarPoint(N, P0).applyMatrix4(vcam.matrixWorldInverse);
    clipPlane.set(pl.normal.x, pl.normal.y, pl.normal.z, pl.constant);
    const e = vcam.projectionMatrix.elements;
    q.x = (Math.sign(clipPlane.x) + e[8]) / e[0]; q.y = (Math.sign(clipPlane.y) + e[9]) / e[5]; q.z = -1; q.w = (1 + e[10]) / e[14];
    clipPlane.multiplyScalar(2 / clipPlane.dot(q));
    e[2] = clipPlane.x; e[6] = clipPlane.y; e[10] = clipPlane.z + 1 - 0.003; e[14] = clipPlane.w;
    vcam.projectionMatrixInverse.copy(vcam.projectionMatrix).invert();
    const vis = hide.map((o) => o.visible); hide.forEach((o) => { o.visible = false; });
    HF.uMirrorPass.value = 1;
    const cur = renderer.getRenderTarget(), ac = renderer.autoClear;
    renderer.setRenderTarget(sharp); renderer.setClearColor(0x000000, 0); renderer.clear(true, true, false);
    renderer.render(scene, vcam);
    HF.uMirrorPass.value = 0;
    hide.forEach((o, i) => { o.visible = vis[i]; });
    renderer.autoClear = false;
    blurPass(sharp, blurA, 1.6 / (w >> 1), 0); blurPass(blurA, blur, 0, 1.6 / (h >> 1));
    blurPass(blur, blurA, 3.4 / (w >> 1), 0); blurPass(blurA, blur, 0, 3.4 / (h >> 1));
    renderer.autoClear = ac; renderer.setRenderTarget(cur);
    return true;
  }
  return { sharp, blur, texMat, setSize, render, dispose() { sharp.dispose(); blurA.dispose(); blur.dispose(); blurMat.dispose(); fsGeo.dispose(); } };
}

// ---------- позы (v2)
const POSE_WORK = { j1: -0.62, j2: 0.42, j3: -1.95, wr: -0.72, roll: 0.35 };
const POSE_REST = { j1: 0, j2: 0, j3: 0, wr: 0, roll: 0 };
const POSE_FIRST = { j1: -1.15, j2: 0.5, j3: -1.85, wr: -0.85, roll: 0.3 };
const blendPose = (a, b, t) => Object.fromEntries(Object.keys(a).map((k) => [k, lerp(a[k], b[k], t)]));
const ORDER = ['base', 'j1', 'j2', 'l1', 'j3', 'l2', 'wrist', 'grip'];
const EXPLODE = {
  base: [0, 0, 0, 0], j1: [-0.55, 0.06, 0.12, 0.12], j2: [0.62, 0.16, 0.08, -0.16], l1: [-0.7, 0.26, -0.06, 0.1],
  j3: [0.72, 0.36, 0.12, -0.14], l2: [-0.64, 0.46, 0.08, 0.12], wrist: [0.6, 0.56, -0.08, -0.18], grip: [-0.26, 0.7, 0.14, 0.14],
};

// ---------- IK: плечо на оси основания; звенья J2→J3 1,21 м, J3→кисть 0,97 м, кисть→точка захвата 0,42 м
const SH_Y = 0.34 + 0.36 + 0.235, LA = 0.2 + L1 + 0.23, LB = 0.17 + L2 + 0.18, LC = 0.42;
const wrapNear = (a, ref) => ref + ((((a - ref + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI;
function solveIK(T, prevJ1, out) {
  const r = Math.max(0.45, Math.hypot(T.x, T.z));
  const up = clamp(T.y, 0.35, 2.5) - SH_Y;
  // рука тянется «от себя»: ось f звена смотрит от цели (как в рабочей позе v2), углы — зеркально
  out.j1 = wrapNear(Math.atan2(T.x, T.z) + Math.PI, prevJ1);
  const ang = Math.atan2(up, r) - 0.55;                            // инструмент смотрит на цель с наклоном вниз ≈ 31°
  const tu = Math.cos(ang), tv = Math.sin(ang);
  let wu = r - LC * tu, wv = up - LC * tv, d = Math.hypot(wu, wv);
  const dmax = LA + LB - 0.03, dmin = Math.abs(LA - LB) + 0.08;
  if (d > dmax) { wu *= dmax / d; wv *= dmax / d; d = dmax; } else if (d < dmin) { wu *= dmin / d; wv *= dmin / d; d = dmin; }
  const g = Math.acos(clamp((LA * LA + d * d - LB * LB) / (2 * LA * d), -1, 1));
  const e1 = Math.atan2(wv, wu) + g;                               // локоть вверх
  const eu = LA * Math.cos(e1), ev = LA * Math.sin(e1);
  const t2 = Math.atan2(eu, ev), a2 = Math.atan2(wu - eu, wv - ev), a3 = Math.atan2(tu, tv);
  out.j2 = clamp(-t2, -1.3, 1.3); out.j3 = clamp(-(a2 - t2), -2.75, 2.75); out.wr = clamp(-(a3 - a2), -2.1, 2.1); out.roll = 0.35;
  return out;
}

export function createScene(canvas, opts = {}) {
  const dprMax = opts.dprMax || 1.5;
  const hq = opts.quality !== 'low';
  // флаги приёмов: по умолчанию всё, что влезает в уровень качества; ?f= в стендах переопределяет
  const def = { studio: true, ik: true, world: true, ao: hq, fx: hq, detail: true, texture: hq };
  const F = Object.assign({}, def, opts.flags || {});
  F.studio = __CD_STUDIO__ && F.studio; F.ik = __CD_IK__ && F.ik; F.world = __CD_WORLD__ && F.world; F.detail = __CD_DETAIL__ && F.detail;
  F.ao = __CD_POST__ && F.ao && hq; F.fx = __CD_POST__ && F.fx; F.texture = !!F.texture && hq;
  const usePost = __CD_POST__ && hq && (F.ao || F.fx);
  const mirrorOn = __CD_WORLD__ && F.world && hq && opts.mirror !== false;

  const renderer = new WebGLRenderer({ canvas, context: opts.context || undefined, antialias: !usePost, alpha: true, powerPreference: 'high-performance', preserveDrawingBuffer: !!opts.preserve });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, dprMax));
  const exposure = opts.exposure || 1.22;
  renderer.toneMapping = usePost ? NoToneMapping : (TONE[opts.tone] || NeutralToneMapping);   // с постом тон — эффектом в конце цепочки
  renderer.toneMappingExposure = exposure;
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.localClippingEnabled = true;
  renderer.shadowMap.enabled = hq;
  renderer.shadowMap.type = PCFShadowMap;
  renderer.shadowMap.autoUpdate = false;                           // карта теней — один раз за кадр (зеркальный проход её не пересчитывает)
  renderer.info.autoReset = false;                                 // счёт вызовов — за весь кадр (зеркало, размытие, пост), сброс в draw()

  const scene = new Scene();
  let envStory = null, envScan = null, envCur = null, rtStory = null, rtScan = null;   // env* — текстуры PMREM, rt* — их цели
  scene.environmentIntensity = opts.env || 1.8;

  const key = new DirectionalLight('#fffaf4', opts.key || (hq ? 2.3 : 2.1));
  key.position.set(-3.2, 6.8, 4.4); key.target.position.set(0, 1.1, 0);
  scene.add(key, key.target);
  if (hq) {
    key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
    const sc = key.shadow.camera; sc.left = -3.2; sc.right = 3.2; sc.top = 3.2; sc.bottom = -3.2; sc.near = 2; sc.far = 16; sc.updateProjectionMatrix();
    key.shadow.bias = -0.0004; key.shadow.normalBias = 0.025; key.shadow.radius = 4;
  }
  const rim = new DirectionalLight('#b9c9ff', opts.rim || 2.0); rim.position.set(4.5, 3.2, -5); scene.add(rim);
  const KEY0 = key.intensity, RIM0 = rim.intensity;
  // fx: свет по сюжету — точечный оранжевый: вспышка фиксации кольца и «свет скана» (всегда в сцене, 0 — выключен: без перекомпиляции)
  const story = new PointLight('#ff6a2a', 0, 1.6, 2); if (F.fx) scene.add(story);

  const camera = new PerspectiveCamera(30, 1, 0.1, 260);
  const MAT = makeMaterials(hq, F);
  let atlas = null;
  if (__CD_DETAIL__ && F.detail) {
    atlas = makeAtlas(opts.font);
    MAT.decal = new MeshStandardMaterial({ map: atlas, transparent: true, depthWrite: false, roughness: 0.5, metalness: 0,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    if (__CD_WORLD__ && F.world) withHF(MAT.decal);
  }
  const M = buildModules(MAT, __CD_DETAIL__ && F.detail);
  const inner = buildInternals(MAT);
  const bg = backdrop(__CD_WORLD__ && F.world, exposure, usePost);
  if (usePost) bg.material.uniforms.uDither.value = 0;              // в посте дизеринг делает EffectPass
  const mirror = __CD_WORLD__ && mirrorOn ? createMirror(renderer) : null;
  const floor = __CD_WORLD__ && F.world ? floorV3(hq, mirror) : floorV2(hq);
  const blob = contactShadow();
  const bars = null;                                               // дальние полосы света — сняты: читались как сбой кадра (dbg1)
  scene.add(bg, floor, blob); if (bars) scene.add(bars);
  if (F.world) {
    HF.uHF.value.set(0.07, 0.42, 6, 0);                            // к 60 м туман ≈ 98 %: край пола растворяется в горизонте
    HF.uHFColor.value.copy(preTone('#111317', exposure));
  } else HF.uHF.value.set(0, 0.5, 6, 0);

  // кабель у основания (detail): из разъёма сзади, провисает до пола и уходит в туман
  let cable = null;
  if (__CD_DETAIL__ && F.detail) {
    const dirX = Math.sin(CABLE_AZ), dirZ = Math.cos(CABLE_AZ), sx = dirZ, sz = -dirX;    // вдоль и поперёк
    const pts = [[0.34, 0.14, 0], [0.46, 0.13, 0], [0.62, 0.06, 0.02], [0.85, 0.016, 0.07], [1.25, 0.014, 0.2], [1.75, 0.014, 0.16], [2.2, 0.03, -0.02], [2.36, 0.045, -0.08]]
      .map(([d, y, l]) => new Vector3(dirX * d + sx * l, y, dirZ * d + sz * l));
    const port = new CylinderGeometry(0.075, 0.085, 0.03, 32); port.translate(pts[7].x, 0.015, pts[7].z);   // напольный разъём: кабель не тянется к горизонту
    cable = new Mesh(mergeGeometries([new TubeGeometry(new CatmullRomCurve3(pts, false, 'catmullrom', 0.5), 90, 0.014, 10, false).toNonIndexed(), port.toNonIndexed()]), MAT.rubber);
    cable.castShadow = hq; cable.receiveShadow = hq; scene.add(cable);
  }

  // кинематика (v2): пустые шарниры; видимые модули лежат в корне и получают матрицу шарнир × разнос
  const piv = { base: new Object3D(), j1: new Object3D(), j2: new Object3D(), l1: new Object3D(), j3: new Object3D(), l2: new Object3D(), wrist: new Object3D(), grip: new Object3D() };
  piv.j1.position.set(0, 0.34, 0); piv.base.add(piv.j1);
  piv.j2.position.set(0, 0.36 + 0.235, 0); piv.j1.add(piv.j2);
  piv.l1.position.set(0, 0, 0); piv.j2.add(piv.l1);
  piv.j3.position.set(0, 0.2 + L1 + 0.23, 0); piv.l1.add(piv.j3);
  piv.l2.position.set(0, 0, 0); piv.j3.add(piv.l2);
  piv.wrist.position.set(0, 0.17 + L2 + 0.18, 0); piv.l2.add(piv.wrist);
  piv.grip.position.set(0, 0.3, 0); piv.wrist.add(piv.grip);
  const rig = new Group(); rig.add(piv.base); scene.add(rig);
  const RING = {};
  const decals = [];
  for (const k of ORDER) {
    M[k].matrixAutoUpdate = false; scene.add(M[k]);
    M[k].children.forEach((ch) => {
      const dec = ch.userData.key === 'decal';
      ch.castShadow = hq && !dec; ch.receiveShadow = hq;
      if (ch.userData.key === 'ring') RING[k] = ch.material;
      if (dec) { decals.push(ch); ch.renderOrder = 2; }
    });
  }
  // винты (detail): один InstancedMesh на всю руку; матрица экземпляра = модуль × локальная, считается только в кадре
  let screws = null;
  // винты — только десктоп: на телефоне ≈ 4 px, а матрицы 86 экземпляров грузятся в каждом кадре (LoAF прокрутки 4,4 % против 1,3 % у v2)
  const sGeo = __CD_DETAIL__ && F.detail && hq ? screwGeometry() : null;
  if (sGeo) {
    screws = new InstancedMesh(sGeo, MAT.screw, SCREWS.length);
    screws.castShadow = hq; screws.receiveShadow = hq; screws.frustumCulled = false; scene.add(screws);
  }

  // сустав крупно для «Внутри» (v2) + винты крышек J3 копией (свой материал со срезом)
  const big = new Group();
  const j3scan = new Group();
  M.j3.children.forEach((ch) => {
    const mm = ch.material; if (mm && mm.onBeforeCompile !== withHF.noop) mm.userData.hf = !!F.world;
    const m = new Mesh(ch.geometry, scanify(ch.material)); m.castShadow = hq && ch.userData.key !== 'decal'; m.receiveShadow = hq; m.renderOrder = ch.renderOrder; j3scan.add(m);
    if (ch.userData.key === 'ring') m.material.emissiveIntensity = F.fx ? 1.6 : 0.85;
  });
  if (sGeo) {
    MAT.screw.userData.hf = !!F.world;
    const loc = SCREWS.filter((s) => s.k === 'j3');
    const s3 = new InstancedMesh(sGeo, scanify(MAT.screw), loc.length); loc.forEach((s, i) => s3.setMatrixAt(i, s.m));
    s3.castShadow = hq; j3scan.add(s3);
  }
  inner.children.forEach((ch) => { ch.castShadow = hq; ch.receiveShadow = hq; });
  const IN = Object.fromEntries(inner.children.map((ch) => [ch.userData.key, ch]));
  big.add(j3scan, inner); big.visible = false; scene.add(big);

  const tmpM = new Matrix4(), tmpM2 = new Matrix4(), tmpR = new Matrix4(), tmpQ = new Quaternion(), tmpE = new Euler(), tmpV = new Vector3(), tmpC = new Vector3(), one = new Vector3(1, 1, 1);
  const noRot = new Quaternion();
  const state = { phase: 'story', t: 0, px: 0, py: 0, w: 1, h: 1, mobile: false, instant: false };
  const cur = { t: 0, px: 0, py: 0 };
  const SP = Object.fromEntries(ORDER.map((k) => [k, { x: 0, v: 0, prev: null }]));
  const SPW = 14, SPZ = 0.8;
  let raf = 0, alive = true, introStart = 0, introMs = 1200, introBump = 0;
  // IK: цель — точка на вертикальной плоскости перед рукой (лицом к камере), луч из камеры через указатель
  const ik = { has: false, nx: 0, ny: 0, T: new Vector3(0, 1.4, 1.2), sol: { ...POSE_WORK }, cur: { ...POSE_WORK }, w: 0, wCur: 0, last: 0,
    minX: opts.ikMinX ?? 0.02, minY: opts.ikMinY ?? -1 };        // цель — не в колонке текста (EG-A11Y-27: белый корпус под белым H1)
  const ray = new Raycaster(), ikPlane = new Plane(), camH = new Vector3(), ndc = new Vector2();
  let post = null, postPromise = null;

  function applyPose(p) {
    piv.j1.rotation.y = p.j1; piv.j2.rotation.x = p.j2; piv.j3.rotation.x = p.j3; piv.wrist.rotation.x = p.wr; piv.grip.rotation.y = p.roll;
    rig.updateMatrixWorld(true);
  }
  function setGlow(x, y, z, r) {
    tmpV.set(x, y, z).project(camera);
    bg.material.uniforms.uGlow.value.set(tmpV.x * 0.5 + 0.5, tmpV.y * 0.5 + 0.5);
    bg.material.uniforms.uR.value = r;
  }
  function ikTarget() {                                             // луч из камеры через указатель → плоскость перед рукой
    camH.set(camera.position.x, 0, camera.position.z).normalize();
    ikPlane.setFromNormalAndCoplanarPoint(camH, tmpV.copy(camH).multiplyScalar(0.8));
    ndc.set(Math.max(ik.nx, state.mobile ? -1 : ik.minX), Math.max(ik.ny, state.mobile ? ik.minY : -1)); ray.setFromCamera(ndc, camera);
    if (ray.ray.intersectPlane(ikPlane, tmpC)) {
      const lat = tmpC.clone().sub(tmpV); const L = lat.length(); if (L > 2.3) lat.multiplyScalar(2.3 / L);
      ik.T.copy(tmpV).add(lat); ik.T.y = clamp(ik.T.y, 0.55, 2.4);
      const rr = Math.hypot(ik.T.x, ik.T.z); if (rr < 1.0) { ik.T.x *= 1.0 / rr; ik.T.z *= 1.0 / rr; }   // не ближе 1 м к оси: иначе предплечье складывается
    }
  }

  function storyFrame(t, dt, still, ikDt) {
    const a = clamp(t - 1, 0, 1);
    const straighten = ease(seg(a, 0.06, 0.2));
    const explode = ease(seg(a, 0.16, 0.34));
    const firstMove = ease(seg(a, 0.88, 1.0));
    let pose = blendPose(POSE_WORK, POSE_REST, straighten);
    if (firstMove > 0) pose = blendPose(POSE_REST, POSE_FIRST, firstMove);
    if (introBump > 0 && a === 0) pose = { ...pose, j1: pose.j1 + 0.22 * introBump, wr: pose.wr - 0.3 * introBump, roll: pose.roll + 0.9 * introBump };
    // IK: вес — на первом экране (гаснет до выпрямления) и после сборки («первое движение» — рука снова ваша)
    let ikQuiet = 0;
    if (__CD_IK__ && F.ik) {
      const zone = Math.max(1 - ease(seg(t, 0.5, 1.04)), ease(seg(a, 0.93, 1.0)));
      ik.w = ik.has ? zone : 0;
      if (ik.has) { ikTarget(); solveIK(ik.T, ik.cur.j1, ik.sol); }
      const kk = still ? 1 : 1 - Math.exp(-ikDt.dt / ikDt.tau);
      for (const j of ['j1', 'j2', 'j3', 'wr', 'roll']) { const tv = ik.has ? ik.sol[j] : pose[j]; ik.cur[j] += (tv - ik.cur[j]) * kk; ikQuiet = Math.max(ikQuiet, Math.abs(tv - ik.cur[j])); }
      ik.wCur += (ik.w - ik.wCur) * kk; ikQuiet = Math.max(ikQuiet, Math.abs(ik.w - ik.wCur));
      if (ik.wCur > 1e-4) { const pj = pose.j1; ik.cur.j1 = wrapNear(ik.cur.j1, pj); pose = blendPose(pose, ik.cur, ik.wCur); }
    }
    applyPose(pose);
    const power = 1 - explode;
    let quiet = 0, lockAt = null, lockK = 0;
    ORDER.forEach((k, i) => {
      const s0 = 0.52 + i * 0.04;
      const u = a >= 0.52 ? seg(a, s0, s0 + 0.12) : 0;
      const back = ease(u);
      const out = a < 0.52 ? explode : explode * (1 - back);
      const hover = a >= 0.52 && i > 0 ? 0.07 * bump(u, 0.2, 0.62, 0.86) : 0;
      const twist = a >= 0.52 && i > 0 ? seg(u, 0, 0.3) * (1 - snap(seg(u, 0.72, 1))) : 0;
      const [ex, ey, ez, er] = EXPLODE[k];
      const sp = SP[k];
      if (still || sp.prev === null) { sp.x = 0; sp.v = 0; }
      else {
        const vOut = (out - sp.prev) / dt;
        const target = clamp(-0.035 * vOut * Math.sign(ex || 1) * (1 + 0.6 * ey), -0.1, 0.1);
        sp.v += (SPW * SPW * (target - sp.x) - 2 * SPZ * SPW * sp.v) * dt;
        sp.x += sp.v * dt;
      }
      sp.prev = out;
      quiet = Math.max(quiet, Math.abs(sp.x), Math.abs(sp.v) * 0.1);
      tmpE.set(er * out * 0.5, er * out + twist * Math.PI / 2, er * out * 0.3);
      tmpQ.setFromEuler(tmpE);
      tmpM.compose(tmpV.set(ex * out, ey * out + hover, ez * out), noRot, one);
      M[k].matrix.copy(tmpM).multiply(piv[k].matrixWorld).multiply(tmpR.makeRotationFromQuaternion(tmpQ));
      if (Math.abs(sp.x) > 1e-4) {
        tmpC.copy(M[k].userData.c).applyMatrix4(M[k].matrix);
        tmpM.makeTranslation(tmpC.x, tmpC.y, tmpC.z).multiply(tmpR.makeRotationZ(sp.x)).multiply(tmpM2.makeTranslation(-tmpC.x, -tmpC.y, -tmpC.z));
        M[k].matrix.premultiply(tmpM);
      }
      M[k].matrixWorldNeedsUpdate = true;
      M[k].visible = true;
      const lock = i === 0 ? seg(a, 0.52, 0.56) : seg(u, 0.86, 0.94);
      const lit = a < 0.52 ? power : lock;
      const flash = a >= 0.52 ? bump(u, 0.84, 0.92, 1.0) : 0;
      // fx: «горит» ярче (bloom только выше порога яркости), вспышка фиксации — сильнее и светит на соседние корпуса
      RING[k].emissiveIntensity = F.fx ? 0.8 * lit + 16 * flash + 1.8 * introBump : 0.85 * lit + 1.6 * flash + 0.9 * introBump;   // fx: ровный свет как v2 (цвет бренда), горит только вспышка
      if (flash > lockK) { lockK = flash; lockAt = k; }
    });
    if (F.fx) {                                                      // свет по сюжету: точечный у фиксируемого кольца
      if (lockAt) { M[lockAt].updateMatrixWorld(); tmpC.copy(M[lockAt].userData.c).applyMatrix4(M[lockAt].matrix); story.position.copy(tmpC); story.position.z += 0.25; }
      story.intensity = 2.6 * lockK;
      key.intensity = KEY0 * (1 - 0.12 * bump(a, 0.14, 0.34, 0.56));  // разнос — «чертёж»: ключ тише, контровой сильнее
      rim.intensity = RIM0 * (1 + 0.45 * bump(a, 0.14, 0.34, 0.56));
    }
    if (screws) {
      SCREWS.forEach((s, i) => { screws.setMatrixAt(i, tmpM.multiplyMatrices(M[s.k].matrix, s.m)); });
      screws.instanceMatrix.needsUpdate = true; screws.visible = true;
    }
    floor.visible = true; blob.visible = true; big.visible = false; if (bars) bars.visible = true; if (cable) cable.visible = true;
    const hTo = ease(clamp(t, 0, 1));
    const far = Math.max(explode * (1 - ease(seg(a, 0.52, 0.9))), straighten * 0.55 * (1 - firstMove));
    const arc = 0.24 * bump(a, 0.16, 0.42, 0.66) - 0.1 * bump(a, 0.6, 0.8, 0.96);
    const low = bump(a, 0.58, 0.8, 0.98);
    const push = ease(seg(a, 0.9, 1.0));
    const dist = lerp(5.9, 10.2, far) * (1 - 0.08 * push) * (state.mobile ? 1.3 : 1);
    const nudge = F.ik ? 0.03 : 0.06;
    const yaw = lerp(0.62, 0.38, hTo) + lerp(0, -0.18, a) + arc + cur.px * nudge;
    const tgtY = lerp(1.28, 2.3, far);
    camera.position.set(Math.sin(yaw) * dist, tgtY + lerp(0.85, 0.45, far) - 0.5 * low + cur.py * (F.ik ? 0.06 : 0.12), Math.cos(yaw) * dist);
    camera.lookAt(0.05, tgtY, 0);
    const shift = state.mobile ? 0 : lerp(-0.2, -0.12, hTo);
    const shiftY = state.mobile ? lerp(0.18, 0.1, hTo) : 0;
    camera.setViewOffset(state.w, state.h, shift * state.w, shiftY * state.h, state.w, state.h);
    camera.updateMatrixWorld();
    setGlow(0.05, tgtY * 0.95, 0, lerp(0.5, 0.62, far));
    if (F.world) {
      HF.uHF.value.z = dist - 0.8;                                  // туман начинается за рукой: сам предмет чистый, дальний план — в дымке
      tmpV.set(0.05, tgtY * 0.95 + 0.25, 0).sub(camera.position).normalize(); HF.uHalo.value.set(tmpV.x, tmpV.y, tmpV.z, lerp(1.0, 1.25, far));
    }
    if (F.studio && envStory && envCur !== envStory) { scene.environment = envCur = envStory; scene.environmentIntensity = 1.8; }
    return Math.max(quiet, ikQuiet * 10);
  }

  function scanFrame(t) {
    ORDER.forEach((k) => { M[k].visible = false; });
    floor.visible = false; blob.visible = false; big.visible = true; if (bars) bars.visible = false; if (cable) cable.visible = false; if (screws) screws.visible = false;
    const sweep = ease(seg(t, 0.06, 0.52));
    const spread = ease(seg(t, 0.6, 0.92));
    const c = lerp(0.26, -0.015, sweep);
    inner.children.forEach((m) => { const k = m.userData.key; const d = { copper: 0.07, steel: 0, dark: -0.03, pcb: -0.07, ring: -0.07 }[k] || 0; m.position.x = d * spread * 0.9; });
    const spin = t * Math.PI * 6;
    IN.dark.rotation.x = spin; IN.steel.rotation.x = -spin / 12; IN.ring.rotation.x = -spin / 12;
    big.scale.setScalar(state.mobile ? 1.9 : 2.45);
    big.rotation.set(0.42, lerp(-0.2, -0.42, t) + cur.px * 0.05, 0.04);
    big.position.set(0, 1.2, 0);
    big.updateMatrixWorld(true);
    scanLocal.constant = c;
    scanPlane.copy(scanLocal).applyMatrix4(big.matrixWorld);
    scanUniforms.uScanN.value.copy(scanPlane.normal); scanUniforms.uScanC.value = scanPlane.constant;
    scanUniforms.uScanK.value = F.fx ? 13.0 : 2.6;               // fx: кромка скана выше порога bloom (3,4)
    if (F.fx) {                                                       // свет скана: плоскость «светит» на начинку, пока идёт по корпусу
      tmpC.set(0, c * 0.6, 0).applyMatrix4(big.matrixWorld); story.position.copy(tmpC);
      story.intensity = 3.2 * bump(t, 0.02, 0.3, 0.6) + 0.6;
      key.intensity = KEY0; rim.intensity = RIM0 * 1.15;
    }
    const dist = (state.mobile ? 5.0 : 4.3) * (1 - 0.05 * bump(t, 0.5, 0.8, 1.01));
    const yaw = 0.18 + 0.1 * bump(t, 0.1, 0.45, 0.8);
    camera.position.set(Math.sin(yaw) * dist, 1.62 + cur.py * 0.08, Math.cos(yaw) * dist);
    camera.lookAt(0, 1.2, 0);
    const shift = state.mobile ? 0 : 0.13;
    camera.setViewOffset(state.w, state.h, shift * state.w, state.mobile ? 0.12 * state.h : 0, state.w, state.h);
    camera.updateMatrixWorld();
    setGlow(0, 1.2, 0, 0.55);
    if (F.world) {
      HF.uHF.value.z = dist + 0.5;
      tmpV.set(0, 1.35, 0).sub(camera.position).normalize(); HF.uHalo.value.set(tmpV.x, tmpV.y, tmpV.z, 1.1);
    }
    if (F.studio && envScan && envCur !== envScan) { scene.environment = envCur = envScan; scene.environmentIntensity = 1.5; }
  }

  const hideInMirror = [bg, floor, blob, ...decals];
  const maskMat = new MeshBasicMaterial({ color: '#ffffff', toneMapped: false });
  function drawMask() {                                             // маска объекта для img_metrics.py --mask (тот же кадр)
    const vis = [bg, floor, blob].map((o) => o.visible); [bg, floor, blob].forEach((o) => { o.visible = false; });
    const tm = renderer.toneMapping; renderer.toneMapping = NoToneMapping; scene.overrideMaterial = maskMat;
    renderer.setRenderTarget(null); renderer.setClearColor(0x000000, 1); renderer.clear(); renderer.render(scene, camera);
    scene.overrideMaterial = null; renderer.toneMapping = tm; [bg, floor, blob].forEach((o, i) => { o.visible = vis[i]; });
  }
  function draw() {
    const u = bg.material.uniforms;
    u.uInvVP.value.multiplyMatrices(camera.matrixWorld, camera.projectionMatrixInverse); u.uCam.value.setFromMatrixPosition(camera.matrixWorld);
    renderer.info.reset();
    renderer.shadowMap.needsUpdate = true;
    if (mirror && state.phase === 'story') { mirror.render(scene, camera, hideInMirror); floor.userData.U.uReflK.value = 0.5; }
    else if (mirror) floor.userData.U.uReflK.value = 0;
    if (post) post.render(); else renderer.render(scene, camera);
  }

  let lastFrame = 0, lastInput = 0, lastPointer = 0;
  function frame(now) {
    raf = 0;
    if (!alive || !isReady) return;
    now = now || performance.now();
    const dt = Math.min(0.05, Math.max(0.001, (now - (lastFrame || now - 16)) / 1000)); lastFrame = now;
    const since = now - lastInput, sinceP = now - lastPointer;
    const late = since > 280;
    const k = state.instant ? 1 : 1 - Math.exp(-dt / (late ? 0.03 : 0.09));
    const kp = state.instant ? 1 : 1 - Math.exp(-dt / (late ? 0.04 : 0.16));
    cur.t += (state.t - cur.t) * k; cur.px += (state.px - cur.px) * kp; cur.py += (state.py - cur.py) * kp;
    const cut = since > 450;
    let settled = (Math.abs(state.t - cur.t) < 0.002 && Math.abs(state.px - cur.px) < 0.004 && Math.abs(state.py - cur.py) < 0.004) || cut;
    if (settled) { cur.t = state.t; cur.px = state.px; cur.py = state.py; }
    if (introStart) {
      const u = (performance.now() - introStart) / introMs;
      if (u >= 1) { introStart = 0; introBump = 0; } else { introBump = Math.sin(Math.PI * ease(u)); settled = false; }
    }
    // IK: суставы догоняют решение по времени (τ 110 мс, после 0,28 с без указателя — 35 мс); отсечка 0,45 с после указателя —
    // как у прокрутки: motion_check снимает счётчик на +0,5 с паузы, а колесо у него идёт с движением мыши (0,9 с давали EG-A11Y-16/17)
    const ikCut = sinceP > 450;
    const ikDt = { dt, tau: sinceP > 280 ? 0.035 : 0.11 };
    if (state.phase === 'scan') { scanFrame(cur.t); }
    else {
      scanPlane.constant = 10;
      const quiet = storyFrame(cur.t, dt, state.instant || (cut && ikCut), ikDt);
      if (quiet > 0.002 && !(cut && ikCut)) settled = false;
    }
    draw();
    state.instant = false;
    if (settled) lastFrame = 0; else raf = requestAnimationFrame(frame);
  }
  const kick = () => { if (!raf && alive) raf = requestAnimationFrame(frame); };

  let lastW = 1, lastH = 1;
  function resize(w, h, mobile) {
    state.w = w; state.h = h; state.mobile = !!mobile; lastW = w; lastH = h;
    renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
    bg.material.uniforms.uAspect.value = w / h;
    const pr = renderer.getPixelRatio();
    if (mirror) mirror.setSize(w * pr, h * pr);
    if (post) post.setSize(w, h);
    state.instant = true; kick();
  }

  const nextTask = () => new Promise((r) => setTimeout(r, 0));
  const par = renderer.extensions.has('KHR_parallel_shader_compile');
  let isReady = false;
  const ready = (async () => {
    await nextTask();
    if (!alive) return false;
    const pmrem = new PMREMGenerator(renderer);
    const mk = (fn) => { const st = fn(); const rt = pmrem.fromScene(st, 0.02); st.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); } }); return rt; };
    if (__CD_STUDIO__ && F.studio) { rtStory = mk(studioStory); await nextTask(); rtScan = mk(studioScan); envScan = rtScan.texture; }
    else rtStory = mk(studioV2);
    envStory = rtStory.texture;
    pmrem.dispose();
    scene.environment = envCur = envStory;
    await nextTask();
    if (!alive) return false;
    if (__CD_POST__ && usePost) {                                   // пост — отдельным чанком (телефон его не качает)
      try {
        const P = await import('./post.js');
        if (!alive) return false;
        post = P.createPost(renderer, scene, camera, { ao: F.ao, fx: F.fx, exposure, msaa: opts.msaa });
        post.setSize(lastW, lastH);
      } catch (e) { console.info('пост недоступен — кадр без AO и bloom', e); renderer.toneMapping = NeutralToneMapping; bg.material.uniforms.uDither.value = 1; }
    }
    if (document.fonts && F.detail && document.fonts.status !== 'loaded') {   // маркировка — шрифтом страницы, если он уже есть
      try { await Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 400))]); atlas.image = makeAtlas(opts.font).image; atlas.needsUpdate = true; } catch (e) { /* без шрифта — запасной */ }
    }
    // программы сцены — в тех вариантах, в которых они будут рисоваться: в буфер (пост, зеркало — линейный выход) и на экран;
    // иначе первый настоящий кадр перекомпилирует всё синхронно (замер: длинная задача 2,2 с на десктопе, CD shots-v3)
    const compileFor = async (rt) => {
      renderer.setRenderTarget(rt);
      const pr = par ? renderer.compileAsync(scene, camera) : (renderer.compile(scene, camera), null);
      renderer.setRenderTarget(null);
      if (pr) await pr; else await nextTask();
    };
    if (post) await compileFor(post.target());
    else { await compileFor(null); if (mirror) { await nextTask(); await compileFor(mirror.sharp); } }
    if (!alive) return false;
    if (post) { await nextTask(); try { await post.warm(); } catch (e) { /* прогрев — не обязателен */ } }
    if (!alive) return false;
    isReady = true;
    const idle = window.requestIdleCallback || ((f) => setTimeout(f, 300));
    idle(() => {                                                    // программы скана — в простое, тем же целевым буфером
      if (!alive) return; big.visible = true;
      renderer.setRenderTarget(post ? post.target() : null);
      if (par) renderer.compileAsync(scene, camera); else renderer.compile(scene, camera);
      renderer.setRenderTarget(null);
      big.visible = false;
    }, { timeout: 2000 });
    return true;
  })();

  return {
    renderer, ready, flags: F, version,
    isReady: () => isReady,
    resize,
    set(phase, t, instant) {
      if (phase !== state.phase) { state.phase = phase; cur.t = t; state.instant = true; }
      state.t = t; if (instant) state.instant = true; lastInput = performance.now(); kick();
    },
    pointer(x, y) {                                                 // x, y — доли окна −1…1 (y вниз), как в v2
      if (x === state.px && y === state.py && ik.has) return;       // тот же пиксель (синтетические события) — без кадров
      state.px = x; state.py = y; lastInput = performance.now();
      if (F.ik) { ik.has = true; ik.nx = x; ik.ny = -y; lastPointer = lastInput; }
      kick();
    },
    ikBounds(minX, minY) { if (minX !== undefined) ik.minX = minX; if (minY !== undefined) ik.minY = minY; },
    tap(x, y) { if (!F.ik) return; ik.has = true; ik.nx = x; ik.ny = -y; lastPointer = lastInput = performance.now(); kick(); },
    intro(ms = 1200) { introMs = ms; introStart = performance.now(); kick(); },
    renderNow() {
      cur.t = state.t; cur.px = state.px; cur.py = state.py; state.instant = true;
      if (F.ik && ik.has) { lastPointer = -1e9; }                   // стенд: IK сразу в решении
      if (raf) { cancelAnimationFrame(raf); raf = 0; } frame();
    },
    stop() { if (raf) cancelAnimationFrame(raf); raf = 0; },
    mask: drawMask,
    dispose() {
      alive = false; if (raf) cancelAnimationFrame(raf);
      const mats = new Set();
      scene.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) mats.add(o.material); });
      mats.forEach((m) => { if (m.map) m.map.dispose(); if (m.alphaMap) m.alphaMap.dispose(); m.dispose(); });
      [rtStory, rtScan].forEach((e) => e && e.dispose());
      if (mirror) mirror.dispose(); if (post) post.dispose();
      renderer.dispose(); renderer.forceContextLoss();
    },
    stats: () => ({ calls: renderer.info.render.calls, tris: renderer.info.render.triangles, programs: renderer.info.programs ? renderer.info.programs.length : null,
      screws: SCREWS.length, post: !!post, mirror: !!mirror }),
  };
}
