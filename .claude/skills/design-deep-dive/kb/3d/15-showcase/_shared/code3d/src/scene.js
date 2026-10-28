// scene.js · общий код 3D «Звена» (_shared/code3d) · сцена «код v3» + гибридный крюк (модули из GLB)
// three 0.186.0 · сборка — _shared/code3d/build.sh (esbuild, define __CD_*__) → <страница>/js/three-scene.js + chunks/.
// Сцена разложена по модулям без изменения поведения однофайлового исходника фазы 1
// (look 'p1' = кадры фазы 1), правки фазы 2 — таблица LOOKS.p2.
// API для main.js (как v2/v3): createScene(canvas, {context, dprMax, quality, flags?, look?, glb?, …}) → {ready, resize, set, pointer,
// intro, renderNow, stop, dispose, stats, tap, ikBounds, flags, mask}. Имена модулей и шарниров — rig.js (base, j1, j2, l1, j3, l2, wrist, grip).
// Приёмы — каждый под своим флагом (opts.flags / ?f= в стендах) и своим define сборки (вес в КБ br):
//   studio — студия PMREM по сценам;  ik — рука тянется к указателю, телефон — касание;  world — пол-отражение, туман по высоте, горизонт;
//   ao — N8AO (пост);  fx — свет по сюжету + bloom/LUT/зерно (пост);  detail — винты, кабель, маркировка, риски, швы;  texture — точёные крышки.
// Гибрид: opts.glb = 'url.glb' | { url, lowUrl?, only?: ['j2'], map?: {j3: 'j2'}, materials: 'glb'|'code', ao?: bool,
//   innerUrl?, innerLowUrl?, ktx2?: true | 'путь/basis/', ktx2Workers? } — модули с этими именами берутся из GLB (glb-modules.js, отдельный
//   чанк), всё живое (кинематика, IK, студия, свет по сюжету, пол, туман, пост) — код. Крюк v2: KTX2 в GLB (сборка --ktx2) и
//   начинка J3 отдельным GLB (innerUrl) — догружается в простое после первого кадра и подставляется вместо начинки-заглушки кода.
// Правила ворот не меняются: 0 кадров в покое, один контекст, DPR ≤ 1,5 (телефон 1,25), текст — только в HTML.
import {
  WebGLRenderer, Scene, PerspectiveCamera, Group, Mesh, Vector2, Vector3, Matrix4, Quaternion, Euler, Color, MeshStandardMaterial,
  MeshBasicMaterial, Plane, PMREMGenerator, AgXToneMapping, NeutralToneMapping, ACESFilmicToneMapping, NoToneMapping, SRGBColorSpace,
  DirectionalLight, PointLight, PCFShadowMap, InstancedMesh, Raycaster,
} from 'three';
import { clamp, seg, ease, lerp, bump, snap, preTone } from './util.js';
import { HF, HALO_BASE, withHF, backdrop, floorV2, floorV3, contactShadow, createMirror } from './world.js';
import { studioV2, studioStory, studioScan } from './studio.js';
import { SCREWS, screwGeometry, makeAtlas, buildCable } from './detail.js';
import { makeMaterials, scanify, scanPlane, scanLocal, scanUniforms, buildModules, buildInternals } from './modules-code.js';
import { ORDER, EXPLODE, POSE_WORK, POSE_REST, POSE_FIRST, blendPose, createPivots, applyPose as poseRig } from './rig.js';
import { solveIK, wrapNear, SH_Y as SH_Y0 } from './ik.js';
import { createTrail } from './trail.js';

export const version = 'zveno-scene v3 (CD, _shared/code3d) 2026-09-25';
const TONE = { agx: AgXToneMapping, neutral: NeutralToneMapping, aces: ACESFilmicToneMapping };

// «вид»: параметры, которые меняет доводка (фаза 2). p1 — ровно фаза 1 (сверка рефакторинга кадрами), p2 — по умолчанию.
//   warm — тёплый отражатель студии «сборка» (p1 0,9 → бронза на точёных крышках; p2 0 — нейтральный низкий отражатель);
//   ring* — излучение лака кольца (lit — под питанием, flash — вспышка фиксации, intro — пробуждение); p2 держит лак ниже сжатия Neutral
//   (пик R·exp < 0,76…1 — цвет бренда не уходит в розовый); led* — узкая LED-полоса пояска (несёт яркость вспышки и bloom, только p2);
//   scanBand/scanCore — кромка скана: оранжевая полоса ниже сжатия + тонкое горячее ядро (p1: одна полоса ×13 — розово-белая);
//   bloom — порог/сила/радиус/уровни; ik — плоскость цели (м перед осью руки, к камере), наклон инструмента, мин. радиус, доля вылета.
export const LOOKS = {
  p1: { warm: 0.9, ledStrip: false, ringLit: 0.8, ringFlash: 16, ringIntro: 1.8, scanRing: 1.6, storyK: 2.6, storyOff: 0, storyDist: 1.6,
    ledLit: 0, ledFlash: 0, ledIntro: 0, glbLedFlash: 6, glbLedIntro: 1.2, glbRingFlash: 0.35,
    scanBand: 13, scanCore: 0, scanCoreW: 0.004,
    bloom: { threshold: 3.4, intensity: 0.9, radius: 0.6, levels: 5 },
    ik: { tilt: 0.55, reach: 1, minR: 1.0, plane: 0.8, aim: false, minD: 0 } },
  p2: { warm: 0, ledStrip: true, ringLit: 0.5, ringFlash: 0.55, ringIntro: 0.35, scanRing: 0.7, storyK: 3.2, storyOff: 0.7, storyDist: 2.6,
    ledLit: 0.8, ledFlash: 30, ledIntro: 3, glbLedFlash: 6, glbLedIntro: 1.2, glbRingFlash: 0.02,
    scanBand: 1.1, scanCore: 14, scanCoreW: 0.004,
    bloom: { threshold: 3.4, intensity: 0.9, radius: 0.45, levels: 4 },
    ik: { tilt: 0.4, reach: 0.94, minR: 1.35, plane: 0.0, aim: true, minD: 1.2, yMax: 1.95, comfort: 'lift' } },
};
// фаза 3: p3 = p2 + приём 8 «лучи в дымке» (контровой диск за рукой, рука режет лучи) + приём 10 «след инструмента»
// луч: диск 1,9 м (эллипс 0,65) в 2,5 м за целью камеры — нижний край не уходит под пол (иначе граница свечения по горизонту);
// свёртка 48 отсчётов, спад 0,9, плотность 0,5 — лучи короткие: дальний фон не поднимается (при 0,8 каждый пиксель «дотягивался» до
// диска и фон кадра к странице уходил в ΔE 3,4; при 0,5 — 3,0, края кадра и зона текста как у p2), колонка текста остаётся тёмной
LOOKS.p3 = { ...LOOKS.p2, beam: true, trail: true, beamK: 1.0, beamColor: '#8d98ad', beamDist: 2.5, beamR: 1.9, beamRx: 1.2, beamY: 0.35, beamAsp: 0.65,
  beamExp: 0.12, beamW: 0.3, beamDecay: 0.9, beamDensity: 0.5, beamScanK: 0.75, trailK: 2.2, trailSize: 0.075, trailStep: 0.035,
  haloLowK: 5, haloLowW: 22 };                                        // телефон (low): ореол фона ×5 и шире (36 → 22) вместо лучей — только в «модулях»
function mergeLook(base, over) {                                   // ?lk=ringFlash:0.5,ik.plane:0 → глубокое слияние (стенды, подбор)
  const out = JSON.parse(JSON.stringify(base));
  for (const [k, v] of Object.entries(over || {})) {
    if (v && typeof v === 'object' && !Array.isArray(v)) out[k] = { ...(out[k] || {}), ...v }; else out[k] = v;
  }
  return out;
}

export function createScene(canvas, opts = {}) {
  const dprMax = opts.dprMax || 1.5;
  const hq = opts.quality !== 'low';
  const LK = mergeLook(LOOKS[opts.look] || LOOKS.p2, opts.lk);
  // гибрид: спецификация GLB-модулей
  const glbSpec = opts.glb ? (typeof opts.glb === 'string' ? { url: opts.glb } : { ...opts.glb }) : null;
  // флаги приёмов: по умолчанию всё, что влезает в уровень качества; ?f= в стендах переопределяет.
  // Гибрид: AO по умолчанию выключен — в GLB свой запечённый (aoMap); вернуть — glb.ao: true или flags.ao
  const def = { studio: true, ik: true, world: true, ao: hq && !(__CD_GLB__ && glbSpec && !glbSpec.ao), fx: hq, detail: true, texture: hq,
    beam: !!LK.beam, trail: !!LK.trail };
  const F = Object.assign({}, def, opts.flags || {});
  F.studio = __CD_STUDIO__ && F.studio; F.ik = __CD_IK__ && F.ik; F.world = __CD_WORLD__ && F.world; F.detail = __CD_DETAIL__ && F.detail;
  F.ao = __CD_POST__ && F.ao && hq; F.fx = __CD_POST__ && F.fx; F.texture = !!F.texture && hq;
  F.beam = __CD_BEAM__ && __CD_POST__ && !!F.beam && F.fx && hq; F.trail = __CD_TRAIL__ && !!F.trail;
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

  // GLB — сразу в сеть (параллельно с PMREM и компиляцией); чанк загрузчика — только при opts.glb
  let glbPromise = null;
  if (glbSpec && !__CD_GLB__) console.info('эта сборка без гибридного крюка (build.sh --glb) — модули кода');
  // v2: начинка J3 отдельным GLB (innerUrl) — не в бюджете первого экрана: качается в простое после первого кадра (или сразу при «скане»)
  let innerUrl = __CD_GLB__ && glbSpec ? ((!hq && glbSpec.innerLowUrl) || glbSpec.innerUrl || null) : null;
  const glbLoadOpts = __CD_GLB__ && glbSpec ? { renderer, ktx2: glbSpec.ktx2, ktx2Workers: glbSpec.ktx2Workers } : null;
  if (__CD_GLB__ && glbSpec) {
    const url = (!hq && glbSpec.lowUrl) || glbSpec.url;
    glbPromise = import('./glb-modules.js').then((G) => G.loadGLB(url, glbLoadOpts).then((gltf) => ({ G, gltf })));
    glbPromise.catch(() => {});                                    // ошибка разбирается в ready (модули кода), без unhandledrejection
  }

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
  const trail = __CD_TRAIL__ && F.trail ? createTrail({ k: LK.trailK || 2.2, size: LK.trailSize || 0.075, step: LK.trailStep || 0.035 }) : null;   // приём 10: след точки захвата
  if (trail) scene.add(trail.mesh);
  const TIP = new Vector3(0, 0.21, 0), tipW = new Vector3();          // точка захвата в системе модуля grip (между пальцами)
  const MAT = makeMaterials(hq, F, LK);
  let atlas = null;
  if (__CD_DETAIL__ && F.detail) {
    atlas = makeAtlas(opts.font);
    MAT.decal = new MeshStandardMaterial({ map: atlas, transparent: true, depthWrite: false, roughness: 0.5, metalness: 0,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    if (__CD_WORLD__ && F.world) withHF(MAT.decal);
  }
  const bg = backdrop(__CD_WORLD__ && F.world, exposure, usePost);
  if (usePost) bg.material.uniforms.uDither.value = 0;              // в посте дизеринг делает EffectPass
  const mirror = __CD_WORLD__ && mirrorOn ? createMirror(renderer) : null;
  const floor = __CD_WORLD__ && F.world ? floorV3(hq, mirror) : floorV2(hq);
  const blob = contactShadow();
  scene.add(bg, floor, blob);
  // ореол в дымке: умолчание — тихий (фазы 1–2); телефон p3 (без поста и лучей) — шире и ярче: то же «студийное» свечение за рукой, 0 мс
  const haloLow = !hq && LK.haloLowK ? LK.haloLowK : 1, haloLowW = !hq && LK.haloLowW ? LK.haloLowW : 36;
  const setHalo = (k, w) => { HF.uHaloColor.value.setRGB(HALO_BASE[0] * k, HALO_BASE[1] * k, HALO_BASE[2] * k); HF.uHaloWidth.value = w; };   // абсолютно: сцена может пересоздаваться
  setHalo(1, 36);
  if (F.world) {
    HF.uHF.value.set(0.07, 0.42, 6, 0);                            // к 60 м туман ≈ 98 %: край пола растворяется в горизонте
    HF.uHFColor.value.copy(preTone('#111317', exposure));
  } else HF.uHF.value.set(0, 0.5, 6, 0);

  // кинематика: пустые шарниры; видимые модули лежат в корне и получают матрицу T(разнос) · шарнир · R (rig.js)
  const { piv, rig } = createPivots();
  scene.add(rig);
  // модули, начинка, винты, кабель — собираются в ready (assemble), когда известно, какие модули пришли из GLB
  let M = {}, inner = null, cable = null, screws = null, big = null, IN = null;
  const GLOW = {};                                                 // модуль → {ring: [материалы], led: [материалы]} — свет по сюжету
  const decals = [];
  let glbReport = null, innerInfo = null, innerP = null, innerKick = null;

  function glowOf(obj) {                                           // материалы кольца и светодиода модуля (роли — glb-modules / key процедурных)
    const g = { ring: [], led: [] };
    obj.traverse((ch) => {
      if (!ch.isMesh) return;
      const r = ch.userData.key;
      const mats = Array.isArray(ch.material) ? ch.material : [ch.material];
      if (r === 'ring') mats.forEach((m) => { if (!g.ring.includes(m)) g.ring.push(m); });
      if (r === 'led') mats.forEach((m) => { if (!g.led.includes(m)) g.led.push(m); });
    });
    for (const m of g.ring) if (g.led.length && m.emissive) { m.emissive.set('#ff4d14'); m.emissiveIntensity = 0; }   // лак GLB-кольца: свет только на вспышке
    return g;
  }
  // кольцо «горит» по сюжету: lit — под питанием (собрано), flash — вспышка фиксации, intro — «пробуждение» первого экрана
  function setGlow(k, lit, flash, intro) {
    const g = GLOW[k]; if (!g) return;
    if (!g.led.length) {                                           // процедурное кольцо (или GLB без светодиода): лак пояска + LED-полоса (p2)
      const e = F.fx ? LK.ringLit * lit + LK.ringFlash * flash + LK.ringIntro * intro : 0.85 * lit + 1.6 * flash + 0.9 * intro;
      const le = F.fx ? LK.ledLit * lit + LK.ledFlash * flash + LK.ledIntro * intro : LK.ledLit * lit + 0.1 * LK.ledFlash * flash;
      for (const m of g.ring) { m.emissiveIntensity = e; if (m.userData.led) m.userData.led.uLedK.value = le; }
      return;
    }
    // GLB: светодиод ассета — «под питанием» базовой силой из GLB, вспышка — кратно; лак кольца — едва (цвет бренда не розовеет)
    const kf = F.fx ? LK.glbLedFlash : 0.6, ki = F.fx ? LK.glbLedIntro : 0.5;
    for (const m of g.led) m.emissiveIntensity = (m.userData.e0 || 1) * (lit + kf * flash + ki * intro);
    for (const m of g.ring) m.emissiveIntensity = F.fx ? LK.ringFlash * LK.glbRingFlash * flash : 0;
  }

  function assemble(res) {
    const glbMods = res ? res.modules : {};
    const code = buildModules(MAT, __CD_DETAIL__ && F.detail);     // процедурные — все (≈ 10–30 мс), лишние освобождаются ниже
    for (const k of ORDER) {
      if (glbMods[k]) {
        code[k].traverse((o) => { if (o.geometry) o.geometry.dispose(); });
        M[k] = glbMods[k];
      } else M[k] = code[k];
    }
    for (let i = SCREWS.length - 1; i >= 0; i--) if (glbMods[SCREWS[i].k]) SCREWS.splice(i, 1);   // крепёж GLB-модулей — свой, в GLB
    for (const k of ORDER) {
      M[k].matrixAutoUpdate = false; scene.add(M[k]);
      M[k].traverse((ch) => {
        if (!ch.isMesh) return;
        const dec = ch.userData.key === 'decal';
        if (M[k].userData.source !== 'glb') { ch.castShadow = hq && !dec; ch.receiveShadow = hq; }
        if (dec) { decals.push(ch); if (M[k].userData.source !== 'glb') ch.renderOrder = 2; }
      });
      GLOW[k] = glowOf(M[k]);
    }
    // винты (detail): один InstancedMesh на всю руку; матрица экземпляра = модуль × локальная, считается только в кадре
    // винты — только десктоп: на телефоне ≈ 4 px, а матрицы 86 экземпляров грузятся в каждом кадре (LoAF прокрутки 4,4 % против 1,3 % у v2)
    const sGeo = __CD_DETAIL__ && F.detail && hq && SCREWS.length ? screwGeometry() : null;
    if (sGeo) {
      screws = new InstancedMesh(sGeo, MAT.screw, SCREWS.length);
      screws.castShadow = hq; screws.receiveShadow = hq; screws.frustumCulled = false; scene.add(screws);
    }
    // кабель у основания: из GLB (реквизит) или процедурный (detail)
    if (res && res.cable) { cable = res.cable; scene.add(cable); }
    else if (__CD_DETAIL__ && F.detail) { cable = buildCable(MAT.rubber, hq); scene.add(cable); }
    // сустав крупно для «Внутри»: копия J3 со срезом (материалы — scanify: и процедурные, и GLB) + начинка
    big = new Group();
    const j3scan = M.j3.userData.source === 'glb' ? M.j3.clone(true) : new Group();
    if (M.j3.userData.source === 'glb') {
      j3scan.matrixAutoUpdate = true; j3scan.position.set(0, 0, 0); j3scan.quaternion.identity(); j3scan.scale.set(1, 1, 1);
      const sm = new Map();
      j3scan.traverse((ch) => {
        if (!ch.isMesh) return;
        const src = ch.material;
        if (!sm.has(src)) {
          const m = scanify(src);
          if (ch.userData.key === 'led') m.emissiveIntensity = (src.userData.e0 || 1) * (F.fx ? 1.0 : 0.8);
          else if (ch.userData.key === 'ring' && GLOW.j3.led.length) m.emissiveIntensity = 0;
          sm.set(src, m);
        }
        ch.material = sm.get(src);
      });
    } else {
      M.j3.children.forEach((ch) => {
        const m = new Mesh(ch.geometry, scanify(ch.material)); m.castShadow = hq && ch.userData.key !== 'decal'; m.receiveShadow = hq; m.renderOrder = ch.renderOrder;
        m.userData.key = ch.userData.key; j3scan.add(m);
        if (ch.userData.key === 'ring') m.material.emissiveIntensity = F.fx ? LK.scanRing : 0.85;
      });
      if (sGeo) {
        const loc = SCREWS.filter((s) => s.k === 'j3');
        if (loc.length) { MAT.screw.userData.hf = !!F.world; const s3 = new InstancedMesh(sGeo, scanify(MAT.screw), loc.length); loc.forEach((s, i) => s3.setMatrixAt(i, s.m)); s3.castShadow = hq; j3scan.add(s3); }
      }
    }
    if (res && res.inner) inner = res.inner;
    else {
      inner = buildInternals(MAT);
      inner.children.forEach((ch) => {
        const r = ch.userData.key;
        ch.userData.spread = { copper: 0.07, steel: 0, dark: -0.03, pcb: -0.07, ring: -0.07 }[r] || 0;
        ch.userData.spin = { dark: 1, steel: -1 / 12, ring: -1 / 12 }[r] || 0;
        ch.userData.p0x = 0; ch.userData.r0x = 0;
        ch.castShadow = hq; ch.receiveShadow = hq;
      });
    }
    IN = inner.children;
    big.add(j3scan, inner); big.visible = false; scene.add(big);
    hideInMirror.push(...decals);
  }
  // v2: начинка из innerUrl заменяет заглушку (начинку кода); геометрия заглушки освобождается (материалы MAT — общие, остаются).
  // Обе функции — выражения под define: в сборке без --glb (страница A) их нет вовсе.
  const swapInner = __CD_GLB__ ? (n) => {
    const old = inner;
    big.remove(old);
    if (old.userData.source !== 'glb') old.traverse((o) => { if (o.geometry) o.geometry.dispose(); });
    inner = n; IN = inner.children; big.add(inner);
    if (state.phase === 'scan') kick();
  } : null;
  const loadInner = __CD_GLB__ ? () => {
    if (!innerUrl) return Promise.resolve();
    if (innerP) return innerP;
    const t0 = performance.now();
    innerP = (async () => {
      let G = null;
      try {
        G = await import('./glb-modules.js');
        const gltf = await G.loadGLB(innerUrl, glbLoadOpts);
        if (!alive) return;
        const r = G.adaptInner(gltf, { materials: glbSpec.materials || 'glb', codeMat: MAT, hq, world: !!F.world, sides: glbSpec.sides, withHF });
        if (!r.inner) throw new Error(r.report.error);
        for (const tx of r.textures) renderer.initTexture(tx);
        swapInner(r.inner);
        innerInfo = { url: innerUrl, ...gltf.load, total_ms: Math.round(performance.now() - t0), ...r.report };
      } catch (e) {
        console.info('начинка GLB недоступна — начинка кода', e && e.message);
        innerInfo = { url: innerUrl, error: String(e && e.message) };
      } finally { if (G) G.releaseLoaders(); }
    })();
    return innerP;
  } : null;

  const tmpM = new Matrix4(), tmpM2 = new Matrix4(), tmpR = new Matrix4(), tmpQ = new Quaternion(), tmpE = new Euler(), tmpV = new Vector3(), tmpC = new Vector3(), one = new Vector3(1, 1, 1);
  const noRot = new Quaternion(), tmpV2 = new Vector2();
  const state = { phase: 'story', t: 0, px: 0, py: 0, w: 1, h: 1, mobile: false, instant: false };
  const cur = { t: 0, px: 0, py: 0 };
  const SP = Object.fromEntries(ORDER.map((k) => [k, { x: 0, v: 0, prev: null }]));
  const SPW = 14, SPZ = 0.8;
  let raf = 0, alive = true, introStart = 0, introMs = 1200, introBump = 0;
  // IK: цель — точка на вертикальной плоскости перед рукой (лицом к камере), луч из камеры через указатель
  const ik = { has: false, nx: 0, ny: 0, T: new Vector3(0, 1.4, 1.2), A: new Vector3(), aim: null, sol: { ...POSE_WORK }, cur: { ...POSE_WORK }, w: 0, wCur: 0, last: 0,
    minX: opts.ikMinX ?? 0.02, minY: opts.ikMinY ?? -1 };        // цель — не в колонке текста (EG-A11Y-27: белый корпус под белым H1)
  const ray = new Raycaster(), ikPlane = new Plane(), camH = new Vector3(), ndc = new Vector2();
  let post = null;

  const applyPose = (p) => poseRig(piv, rig, p);
  function setBgGlow(x, y, z, r) {
    tmpV.set(x, y, z).project(camera);
    bg.material.uniforms.uGlow.value.set(tmpV.x * 0.5 + 0.5, tmpV.y * 0.5 + 0.5);
    bg.material.uniforms.uR.value = r;
  }
  function planeHit(nx, ny, out) {                                  // луч из камеры через точку экрана → плоскость цели (лицом к камере)
    ndc.set(nx, ny); ray.setFromCamera(ndc, camera);
    if (!ray.ray.intersectPlane(ikPlane, out)) return false;
    const lat = out.sub(tmpV); const L = lat.length(); if (L > 2.3) lat.multiplyScalar(2.3 / L);
    out.add(tmpV); out.y = clamp(out.y, 0.55, 2.4);
    return true;
  }
  function ikTarget() {                                             // цель досягания и точка прицела
    camH.set(camera.position.x, 0, camera.position.z).normalize();
    ikPlane.setFromNormalAndCoplanarPoint(camH, tmpV.copy(camH).multiplyScalar(LK.ik.plane));
    const cx = Math.max(ik.nx, state.mobile ? -1 : ik.minX), cy = Math.max(ik.ny, state.mobile ? ik.minY : -1);   // граница колонки текста (DOM)
    if (!planeHit(cx, cy, ik.T)) return;
    if (!LK.ik.aim) {                                               // фаза 1: цель не ближе minR к оси (сдвиг вбок — мог уводить в текст)
      const rr = Math.hypot(ik.T.x, ik.T.z), mr = LK.ik.minR; if (rr < mr) { ik.T.x *= mr / rr; ik.T.z *= mr / rr; }
      ik.aim = null; return;
    }
    // фаза 2: цель на луче через границу (экранная граница текста держится при любой глубине); если цель ближе minD к плечу —
    // поднять её (рука не складывается), а инструмент нацелить на настоящую точку указателя — рука указывает на курсор
    const r = Math.hypot(ik.T.x, ik.T.z), md = LK.ik.minD;
    const du = ik.T.y - SH_Y0;
    if (r * r + du * du < md * md) {
      const mode = LK.ik.comfort || 'lift';
      if (mode === 'lift' || (mode === 'mix' && du > 0)) ik.T.y = Math.min(LK.ik.yMax ?? 2.4, SH_Y0 + Math.sqrt(Math.max(0, md * md - r * r)));
      else {                                                        // 'ray': к зрителю вдоль луча камеры — экранная точка схвата та же
        const O = camera.position, d = ray.ray.direction;           // луч последнего planeHit — через границу (cx, cy)
        ndc.set(cx, cy); ray.setFromCamera(ndc, camera);
        tmpC.set(O.x, O.y - SH_Y0, O.z);                            // O − S (плечо на оси, высота SH_Y)
        const b = d.dot(tmpC), c = tmpC.lengthSq() - md * md, disc = b * b - c;
        const far = mode === 'back';                                // 'back' — дальняя точка луча: за осью руки (от зрителя)
        if (disc > 0) { const t = Math.max(0.8, -b + (far ? 1 : -1) * Math.sqrt(disc)); ik.T.copy(O).addScaledVector(d, t); ik.T.y = clamp(ik.T.y, 0.55, 2.4); }
      }
    }
    const clamped = cx !== ik.nx || cy !== ik.ny;
    if (clamped && planeHit(ik.nx, ik.ny, ik.A)) ik.aim = ik.A; else ik.aim = null;
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
      if (ik.has) { ikTarget(); solveIK(ik.T, ik.cur.j1, ik.sol, LK.ik, ik.aim); }
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
      setGlow(k, lit, flash, introBump);
      if (flash > lockK) { lockK = flash; lockAt = k; }
    });
    if (F.fx) {                                                      // свет по сюжету: точечный у фиксируемого кольца
      if (lockAt) {
        M[lockAt].updateMatrixWorld(); tmpC.copy(M[lockAt].userData.c).applyMatrix4(M[lockAt].matrix); story.position.copy(tmpC);
        if (LK.storyOff) story.position.add(tmpV.copy(camera.position).sub(tmpC).normalize().multiplyScalar(LK.storyOff));   // p2: к камере, над лаком
        else story.position.z += 0.25;                              // p1: +0,25 м по z — в 1,5 см от лака J2: выжигал свой корпус
      }
      story.intensity = LK.storyK * lockK; story.distance = LK.storyDist;
      key.intensity = KEY0 * (1 - 0.12 * bump(a, 0.14, 0.34, 0.56));  // разнос — «чертёж»: ключ тише, контровой сильнее
      rim.intensity = RIM0 * (1 + 0.45 * bump(a, 0.14, 0.34, 0.56));
    }
    if (screws) {
      SCREWS.forEach((s, i) => { screws.setMatrixAt(i, tmpM.multiplyMatrices(M[s.k].matrix, s.m)); });
      screws.instanceMatrix.needsUpdate = true; screws.visible = true;
    }
    floor.visible = true; blob.visible = true; big.visible = false; if (cable) cable.visible = true;
    if (trail) {                                                    // след — когда руку ведёт указатель (IK) или «первое движение»
      tipW.copy(TIP).applyMatrix4(M.grip.matrix);
      trail.push(tipW, performance.now() / 1000, !still && (ik.wCur > 0.3 || a > 0.86));
    }
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
    setBgGlow(0.05, tgtY * 0.95, 0, lerp(0.5, 0.62, far));
    if (__CD_BEAM__ && post && post.beam) {                         // приём 8: диск в дымке за рукой, на разносе — сильнее (лучи сквозь промежутки)
      tmpC.set(0.05, tgtY * 0.95 + LK.beamY, 0); tmpV.copy(tmpC).sub(camera.position).normalize();
      post.beam.set(tmpC.addScaledVector(tmpV, LK.beamDist), LK.beamR * lerp(1, LK.beamRx, far), LK.beamK, LK.beamAsp ?? 1);
    }
    if (haloLow !== 1) setHalo(haloLow, haloLowW);                  // телефон p3: «студийное» свечение за рукой только в сюжете «модули»
    if (F.world) {
      HF.uHF.value.z = dist - 0.8;                                  // туман начинается за рукой: сам предмет чистый, дальний план — в дымке
      tmpV.set(0.05, tgtY * 0.95 + 0.25, 0).sub(camera.position).normalize(); HF.uHalo.value.set(tmpV.x, tmpV.y, tmpV.z, lerp(1.0, 1.25, far));
    }
    if (F.studio && envStory && envCur !== envStory) { scene.environment = envCur = envStory; scene.environmentIntensity = 1.8; }
    return Math.max(quiet, ikQuiet * 10);
  }

  function scanFrame(t) {
    ORDER.forEach((k) => { M[k].visible = false; });
    floor.visible = false; blob.visible = false; big.visible = true; if (cable) cable.visible = false; if (screws) screws.visible = false;
    const sweep = ease(seg(t, 0.06, 0.52));
    const spread = ease(seg(t, 0.6, 0.92));
    const c = lerp(0.26, -0.015, sweep);
    const spin = t * Math.PI * 6;
    for (const m of IN) {                                           // слои начинки: разведение по оси и вращение (роли — как у процедурной)
      m.position.x = m.userData.p0x + m.userData.spread * spread * 0.9;
      if (m.userData.spin) m.rotation.x = m.userData.r0x + spin * m.userData.spin;
    }
    big.scale.setScalar(state.mobile ? 1.9 : 2.45);
    big.rotation.set(0.42, lerp(-0.2, -0.42, t) + cur.px * 0.05, 0.04);
    big.position.set(0, 1.2, 0);
    big.updateMatrixWorld(true);
    scanLocal.constant = c;
    scanPlane.copy(scanLocal).applyMatrix4(big.matrixWorld);
    scanUniforms.uScanN.value.copy(scanPlane.normal); scanUniforms.uScanC.value = scanPlane.constant;
    scanUniforms.uScanK.value = F.fx ? LK.scanBand : 2.6;        // fx: кромка скана выше порога bloom (3,4): p1 — вся полоса, p2 — ядро
    scanUniforms.uScanCore.value = F.fx ? LK.scanCore : 0; scanUniforms.uScanCoreW.value = LK.scanCoreW;
    if (F.fx) {                                                       // свет скана: плоскость «светит» на начинку, пока идёт по корпусу
      tmpC.set(0, c * 0.6, 0).applyMatrix4(big.matrixWorld); story.position.copy(tmpC);
      story.intensity = 3.2 * bump(t, 0.02, 0.3, 0.6) + 0.6; story.distance = 1.6;
      key.intensity = KEY0; rim.intensity = RIM0 * 1.15;
    }
    const dist = (state.mobile ? 5.0 : 4.3) * (1 - 0.05 * bump(t, 0.5, 0.8, 1.01));
    const yaw = 0.18 + 0.1 * bump(t, 0.1, 0.45, 0.8);
    camera.position.set(Math.sin(yaw) * dist, 1.62 + cur.py * 0.08, Math.cos(yaw) * dist);
    camera.lookAt(0, 1.2, 0);
    const shift = state.mobile ? 0 : 0.13;
    camera.setViewOffset(state.w, state.h, shift * state.w, state.mobile ? 0.12 * state.h : 0, state.w, state.h);
    camera.updateMatrixWorld();
    setBgGlow(0, 1.2, 0, 0.55);
    if (trail) trail.push(tipW.set(0, -100, 0), performance.now() / 1000, false);   // в «скане» следа нет (новые точки не рождаются)
    if (__CD_BEAM__ && post && post.beam) {                         // луч за разрезом сустава: сквозь зубья колеса и пазы статора
      tmpC.set(0, 1.25, 0); tmpV.copy(tmpC).sub(camera.position).normalize();
      post.beam.set(tmpC.addScaledVector(tmpV, 2.8), LK.beamR * 0.62, LK.beamK * LK.beamScanK * ease(seg(t, 0.02, 0.2)));
    }
    if (haloLow !== 1) setHalo(1, 36);                              // «скан» — тёмный фон: оранжевый разрез контрастнее
    if (F.world) {
      HF.uHF.value.z = dist + 0.5;
      tmpV.set(0, 1.35, 0).sub(camera.position).normalize(); HF.uHalo.value.set(tmpV.x, tmpV.y, tmpV.z, 1.1);
    }
    if (F.studio && envScan && envCur !== envScan) { scene.environment = envCur = envScan; scene.environmentIntensity = 1.5; }
  }

  const hideInMirror = [bg, floor, blob];                           // + наклейки (assemble)
  const maskMat = new MeshBasicMaterial({ color: '#ffffff', toneMapped: false });
  const blackMat = new MeshBasicMaterial({ color: '#000000', toneMapped: false });
  function drawMask(role) {                                         // маска объекта для img_metrics.py --mask (тот же кадр); role — только эта роль
    if (trail) trail.mesh.visible = false;                          // след — не объект
    const vis = [bg, floor, blob].map((o) => o.visible); [bg, floor, blob].forEach((o) => { o.visible = false; });
    if (role) {                                                     // белое — меши роли (ring, cap, shell…), остальное чёрным: заслонение честное
      const saved = [];
      scene.traverse((o) => { if (o.isMesh && o !== bg) { saved.push([o, o.material]); o.material = o.userData.key === role ? maskMat : blackMat; } });
      const tm = renderer.toneMapping; renderer.toneMapping = NoToneMapping;
      renderer.setRenderTarget(null); renderer.setClearColor(0x000000, 1); renderer.clear(); renderer.render(scene, camera);
      renderer.toneMapping = tm; saved.forEach(([o, m]) => { o.material = m; }); [bg, floor, blob].forEach((o, i) => { o.visible = vis[i]; });
      return;
    }
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
    if (post) post.render(); else if (opts.onDraw) opts.onDraw(renderer, scene, camera); else renderer.render(scene, camera);   // onDraw — стенды (AO трёх видов)
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
    if (trail && trail.update(now / 1000, renderer.getDrawingBufferSize(tmpV2).y * 0.5) && !(cut && ikCut)) settled = false;   // след гаснет ≤ 0,4 с (хвост 0,45)
    draw();
    if (__CD_GLB__ && innerKick) { const f = innerKick; innerKick = null; f(); }   // начинка — только после первого кадра
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
    if (__CD_STUDIO__ && F.studio) { rtStory = mk(() => studioStory({ warm: LK.warm })); await nextTask(); rtScan = mk(studioScan); envScan = rtScan.texture; }
    else rtStory = mk(studioV2);
    envStory = rtStory.texture;
    pmrem.dispose();
    scene.environment = envCur = envStory;
    await nextTask();
    if (!alive) return false;
    // гибрид: модули GLB (сеть шла параллельно с PMREM); при ошибке — модули кода, без ошибки в консоли (ворота EG-FB-06)
    let res = null;
    if (__CD_GLB__ && glbPromise) {
      try {
        const { G, gltf } = await glbPromise;
        if (!alive) return false;
        res = G.adaptModules(gltf, { only: glbSpec.only, map: glbSpec.map, materials: glbSpec.materials || 'glb', codeMat: MAT, hq, world: !!F.world,
          sides: glbSpec.sides, order: ORDER, withHF });
        glbReport = res.report; glbReport.load = gltf.load;
        for (const tx of res.textures) renderer.initTexture(tx);   // загрузка текстур в GPU — здесь, а не в первом кадре
        if (innerUrl && res.inner) { glbReport.warnings.push(`innerUrl ${innerUrl} не нужен: начинка уже в основном GLB`); innerUrl = null; }
        if (!innerUrl) G.releaseLoaders();                        // KTX2: воркеры транскодера больше не нужны
      } catch (e) { console.info('GLB модулей недоступен — модули кода', e && e.message); glbReport = { error: String(e && e.message) }; innerUrl = null; }
      await nextTask();
      if (!alive) return false;
    }
    assemble(res);
    await nextTask();
    if (!alive) return false;
    if (__CD_POST__ && usePost) {                                   // пост — отдельным чанком (телефон его не качает)
      try {
        const P = await import('./post.js');
        if (!alive) return false;
        post = P.createPost(renderer, scene, camera, { ao: F.ao, fx: F.fx, exposure, msaa: opts.msaa, bloom: LK.bloom,
          beam: __CD_BEAM__ && F.beam ? { color: LK.beamColor, exposure: LK.beamExp, weight: LK.beamW, decay: LK.beamDecay, density: LK.beamDensity } : null });
        post.setSize(lastW, lastH);
      } catch (e) { console.info('пост недоступен — кадр без AO и bloom', e); renderer.toneMapping = NeutralToneMapping; bg.material.uniforms.uDither.value = 1; }
    }
    if (document.fonts && F.detail && atlas && document.fonts.status !== 'loaded') {   // маркировка — шрифтом страницы, если он уже есть
      try { await Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 400))]); atlas.image = makeAtlas(opts.font).image; atlas.needsUpdate = true; } catch (e) { /* без шрифта — запасной */ }
    }
    // программы сцены — в тех вариантах, в которых они будут рисоваться: в буфер (пост, зеркало — линейный выход) и на экран;
    // иначе первый настоящий кадр перекомпилирует всё синхронно (замер: длинная задача 2,2 с на десктопе)
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
    if (__CD_GLB__ && innerUrl && state.phase === 'scan') await loadInner();   // страница открыта сразу на «скане» — без подмены на глазах
    if (!alive) return false;
    isReady = true;
    const idle = window.requestIdleCallback || ((f) => setTimeout(f, 300));
    const compileScan = () => {                                     // программы скана — в простое, тем же целевым буфером
      if (!alive) return; big.visible = true;
      renderer.setRenderTarget(post ? post.target() : null);
      if (par) renderer.compileAsync(scene, camera); else renderer.compile(scene, camera);
      renderer.setRenderTarget(null);
      big.visible = false;
    };
    if (__CD_GLB__ && innerUrl) innerKick = () => idle(() => { loadInner().then(() => { if (alive) idle(compileScan, { timeout: 2000 }); }); }, { timeout: 2000 });
    else idle(compileScan, { timeout: 2000 });
    return true;
  })();

  return {
    renderer, ready, flags: F, version, look: opts.look || 'p2',
    __dbg: { scene, camera, bg, floor },                            // стенды: доступ к сцене (замеры AO, WebGPU) — не для страницы
    isReady: () => isReady,
    resize,
    set(phase, t, instant) {
      if (phase !== state.phase) { state.phase = phase; cur.t = t; state.instant = true; }
      if (__CD_GLB__ && phase === 'scan' && innerUrl && isReady && !innerP) loadInner();   // «скан» раньше простоя — начинку сразу
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
      scene.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => mats.add(m)); });
      mats.forEach((m) => { for (const t of ['map', 'alphaMap', 'aoMap', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap']) if (m[t]) m[t].dispose(); m.dispose(); });
      [rtStory, rtScan].forEach((e) => e && e.dispose());
      if (mirror) mirror.dispose(); if (post) post.dispose();
      renderer.dispose(); renderer.forceContextLoss();
    },
    stats: () => ({ calls: renderer.info.render.calls, tris: renderer.info.render.triangles, programs: renderer.info.programs ? renderer.info.programs.length : null,
      screws: SCREWS.length, post: !!post, mirror: !!mirror, look: opts.look || 'p2',
      glb: glbReport, glbInner: innerInfo, modules: Object.fromEntries(ORDER.map((k) => [k, M[k] && M[k].userData.source === 'glb' ? 'glb' : 'code'])) }),
  };
}
