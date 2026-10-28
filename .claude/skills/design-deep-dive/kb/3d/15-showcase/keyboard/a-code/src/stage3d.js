// stage3d.js — общий 3D для A (код) и C (гибрид), three r186. Отличается только модель (model_a.js / model_c.js).
// Один WebGLRenderer и один canvas на страницу: canvas переезжает в ту сцену, которая сейчас на экране (набор T, расцветки R,
// разборка X). Камеры — из JSON Blender (те же, что у кадров B): позиция (x, z, −y), поворот Rx(−90°)·q, FOV по sensor fit,
// сдвиг — setViewOffset. Рендер только по требованию: пружины нажатий, поворот и разборка догоняют цель и засыпают.
import {
  WebGLRenderer, Scene, PerspectiveCamera, Vector3, Vector2, Quaternion, Color, NeutralToneMapping, SRGBColorSpace,
  PMREMGenerator, Mesh, MeshBasicMaterial, SphereGeometry, BackSide, PlaneGeometry, DirectionalLight, DoubleSide,
  Raycaster, PCFShadowMap,
} from 'three';
import { logTiming } from './page.js';

const DEG = Math.PI / 180;
const sph3 = (az, el, d) => new Vector3(Math.sin(az * DEG) * Math.cos(el * DEG), Math.sin(el * DEG), Math.cos(az * DEG) * Math.cos(el * DEG)).multiplyScalar(d);
const damp = (x, y, l, dt) => x + (y - x) * (1 - Math.exp(-l * dt));

function camFromBlender(J) {
  const cam = new PerspectiveCamera(30, J.res[0] / J.res[1], 0.02, 10);
  const [bx, by, bz] = J.location;
  cam.position.set(bx, bz, -by);
  const [qw, qx, qy, qz] = J.quaternion_wxyz;
  cam.quaternion.copy(new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2).multiply(new Quaternion(qx, qy, qz, qw)));
  cam.userData.J = J;
  return cam;
}
// w × h — весь кадр Blender в CSS px; sub — видимое окно этого кадра (телефонная полоса набора), иначе кадр целиком
function fitCam(cam, w, h, sub = null) {
  const J = cam.userData.J, horiz = J.sensor_fit !== 'VERTICAL', aspect = w / h;
  if (horiz) cam.fov = 2 * Math.atan(Math.tan(Math.atan(J.sensor_width_mm / 2 / J.lens_mm)) / aspect) / DEG;
  else cam.fov = 2 * Math.atan((J.sensor_height_mm || J.sensor_width_mm) / 2 / J.lens_mm) / DEG;
  cam.aspect = aspect;
  const big = horiz ? w : h;
  const sx = (J.shift_x || 0) * big, sy = -(J.shift_y || 0) * big;
  if (sub) cam.setViewOffset(w, h, sub.x + sx, sub.y + sy, sub.w, sub.h);
  else if (sx || sy) cam.setViewOffset(w, h, sx, sy, w, h); else cam.clearViewOffset();
  cam.updateProjectionMatrix();
}
const phoneBand = matchMedia('(max-width: 700px)');

// студия для отражений (PMREM): тёмно-серая сфера и светящиеся панели там же, где лампы схемы S1 у Blender (азимут камеры R −20°)
function studioEnv(renderer) {
  const s = new Scene();
  s.add(new Mesh(new SphereGeometry(8, 48, 24), new MeshBasicMaterial({ color: new Color(0.16, 0.165, 0.17), side: BackSide })));
  const r = 0.175, d = 3.5 * r;
  const panel = (az, el, w, h, I) => {
    const m = new Mesh(new PlaneGeometry(w, h), new MeshBasicMaterial({ color: new Color(I, I, I), side: DoubleSide }));
    m.position.copy(sph3(az, el, d)); m.lookAt(0, 0, 0); s.add(m);
  };
  panel(18, 48, 2.4 * r, 1.8 * r, 7.0);        // ключ-софтбокс
  panel(-90, 18, 3.0 * r, 3.0 * r, 1.6);       // заливка
  panel(58, 57, 5.0 * r, 0.18 * r, 9.0);       // полоса под переднюю фаску
  panel(-140, 25, 5.0 * r, 0.18 * r, 9.0);     // полоса под левую фаску
  panel(140, 30, 1.5 * r, 1.5 * r, 5.0);       // контровой
  panel(180, 62, 2.5 * r, 2.5 * r, 3.0);       // верх
  const floor = new Mesh(new PlaneGeometry(20, 20), new MeshBasicMaterial({ color: new Color(0.35, 0.355, 0.36) }));
  floor.rotation.x = -Math.PI / 2; floor.position.y = -0.002; s.add(floor);
  const pm = new PMREMGenerator(renderer);
  const rt = pm.fromScene(s, 0.015, 0.05, 20);
  pm.dispose();
  return rt.texture;
}

// свет сцен: ключ и контровой — направленные, по схемам Blender (T — S2 низкий ключ слева, R/X — S1 студия)
// азимуты — относительно азимута камеры сцены (как kbr: S2 ключ −55°, S1 ключ +38°, заливка −70°, контровой ±160°)
const TURN_EXP = { snow: 0.10, graphite: 0.0, linen: 0.15 };   // как у кадров B (brender.TURN_LOOK)
const RIGS = {
  type: { env: 0.55, key: [-55, 16, 2.6], rim: [-144, 22, 1.4], fill: [10, 40, 0.5], dE: 0 },
  turn: { env: 1.0, key: [38, 48, 1.7], rim: [160, 30, 0.8], fill: [-70, 18, 0.35], dE: -0.6 },   // −0,6 EV: белые 97,8 → B 91,5 L*
  x: { env: 1.0, key: [38, 48, 1.7], rim: [-160, 26, 0.9], fill: [-70, 18, 0.35], dE: -0.9 },     // −0,9 EV: объект +12 L* к B
  hero: { env: 0.35, key: [-55, 16, 3.2], rim: [-128, 22, 2.2], fill: [10, 40, 0.25] },
};

export async function createStage3D({ buildModel, cams, phone, variant, quality, idle = async () => {} }) {
  const T0 = performance.now();
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true');
  const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, phone ? 1.5 : 2));
  renderer.toneMapping = NeutralToneMapping;
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.setClearColor(0x000000, 0);
  if (quality.shadows) { renderer.shadowMap.enabled = true; renderer.shadowMap.type = PCFShadowMap; }   // r186: PCFSoft удалён, PCF берёт radius
  const scene = new Scene();
  scene.environment = studioEnv(renderer);
  await idle();
  const model = await buildModel({ renderer, scene, phone, quality, idle });
  scene.add(model.root);
  await idle();
  const L = { key: new DirectionalLight('#ffffff', 1), rim: new DirectionalLight('#ffffff', 1), fill: new DirectionalLight('#ffffff', 1) };
  for (const l of Object.values(L)) scene.add(l, l.target);
  if (quality.shadows) {
    const k = L.key; k.castShadow = true; k.shadow.mapSize.set(2048, 2048); k.shadow.radius = 5; k.shadow.bias = -0.0003; k.shadow.normalBias = 0.0008;
    const sc = k.shadow.camera; sc.left = -0.26; sc.right = 0.26; sc.top = 0.26; sc.bottom = -0.26; sc.near = 0.05; sc.far = 2; sc.updateProjectionMatrix();
  }
  const stages = {};
  for (const [name, J] of Object.entries(cams)) {
    const el = document.getElementById(`stage-${name}`);
    // набор: canvas — в .zoom (видимая полоса кадра); на телефоне полоса = окно кадра T из CSS-переменных сцены (--bx…--bh)
    const crop = () => {
      if (name !== 'type' || !phoneBand.matches) return null;
      const cs = getComputedStyle(el), v = (n) => parseFloat(cs.getPropertyValue(n));
      const c = { x: v('--bx'), y: v('--by'), w: v('--bw'), h: v('--bh') };
      return c.w > 0 && c.h > 0 ? c : null;
    };
    stages[name] = { name, el, mountEl: el.querySelector('.zoom') || el, crop, cam: camFromBlender(J), J };
  }
  // шейдеры — заранее и параллельно (KHR_parallel_shader_compile), чтобы первый кадр не был длинным
  try { const c0 = Object.values(stages)[0].cam; await renderer.compileAsync(scene, c0); } catch (e) { void e; }
  await idle();
  let cur = null, needs = false, last = 0, frames = 0, first = true;
  const vis = {};
  const st = { cw: 'snow', turn: 0, turnT: 0, p: 0, pT: 0, yo: 0 };
  const springs = new Map();
  const TRAVEL = 0.0038;
  let post = null;

  const setRig = (name) => {
    const R = RIGS[name], J = stages[name].J;
    const az = (J.az ?? -20);
    scene.environmentIntensity = R.env;
    for (const k of ['key', 'rim', 'fill']) {
      const [a, e, I] = R[k], l = L[k];
      l.intensity = I;
      l.position.copy(sph3(az + a, e, 1.2));
      l.target.position.set(0, 0.012, 0);
    }
    const ex = name === 'turn' ? TURN_EXP[st.cw] : (J.exposure ?? 0);
    renderer.toneMappingExposure = 2 ** (ex + (R.dE || 0));
  };
  const size = () => {
    if (!cur) return;
    const S = stages[cur], el = S.mountEl, J = S.J;
    const W = el.clientWidth, H = el.clientHeight, a = J.res[0] / J.res[1];
    const crop = S.crop();
    if (crop) {                                       // телефон: canvas = полоса, камера — её окно в кадре T
      const w = Math.max(1, Math.round(W)), h = Math.max(1, Math.round(H)), k = w / crop.w;
      canvas.style.cssText = `position:absolute;left:0;top:0;width:${w}px;height:${h}px`;
      renderer.setSize(w, h, false);
      fitCam(S.cam, J.res[0] * k, J.res[1] * k, { x: crop.x * k, y: crop.y * k, w, h });
      post?.setSize(w, h);
      return;
    }
    let w = W, h = W / a;
    if (h > H) { h = H; w = H * a; }
    w = Math.max(1, Math.round(w)); h = Math.max(1, Math.round(h));
    canvas.style.cssText = `position:absolute;left:${(W - w) / 2}px;top:${(H - h) / 2}px;width:${w}px;height:${h}px`;
    renderer.setSize(w, h, false);
    fitCam(S.cam, w, h);
    post?.setSize(w, h);
  };
  const ro = new ResizeObserver(() => { size(); invalidate(); });
  phoneBand.addEventListener?.('change', () => { size(); invalidate(); });
  const mount = (name) => {
    if (cur === name) return;
    if (cur) { stages[cur].el.classList.remove('is-live'); ro.unobserve(stages[cur].mountEl); }
    cur = name;
    const S = stages[name];
    S.mountEl.appendChild(canvas);
    ro.observe(S.mountEl);
    setRig(name);
    model.setStage?.(name);
    size();
    post?.setCamera(S.cam);
    invalidate();
  };
  const render = () => {
    const S = stages[cur];
    model.root.rotation.y = cur === 'turn' ? st.turn * DEG : 0;
    model.setExplode(cur === 'x' ? st.p : 0);
    if (post) post.render(); else renderer.render(scene, S.cam);
    frames++;
    if (first) {
      first = false;
      S.el.classList.add('is-live');
      performance.mark('3d-first-frame');
      const info = renderer.info.render;
      logTiming({ first3d_ms: Math.round(performance.now()), first3d_after_import_ms: Math.round(performance.now() - T0),
        calls: info.calls, tris: info.triangles, dpr: renderer.getPixelRatio(), stage: cur, post: !!post });
    } else S.el.classList.add('is-live');
  };
  const frame = (t) => {
    needs = false;
    const dt = Math.min(0.05, last ? (t - last) / 1000 : 1 / 60); last = t;
    let active = false;
    for (const [id, s] of springs) {
      const w = s.down ? (2 * Math.PI) / 0.07 : (2 * Math.PI) / 0.2, z = s.down ? 1.0 : 0.62;
      for (let k = 0; k < 4; k++) { const h = dt / 4; const acc = w * w * (s.target - s.x) - 2 * z * w * s.v; s.v += acc * h; s.x += s.v * h; }
      if (Math.abs(s.target - s.x) < 2e-5 && Math.abs(s.v) < 2e-4) { s.x = s.target; s.v = 0; if (!s.down) springs.delete(id); } else active = true;
      model.setKeyOffset(id, s.x);
    }
    if (Math.abs(st.turnT - st.turn) > 0.05) { st.turn = st.snap ? st.turnT : damp(st.turn, st.turnT, 10, dt); active = active || !st.snap; } else st.turn = st.turnT;
    if (Math.abs(st.pT - st.p) > 1e-4) { st.p = damp(st.p, st.pT, 9, dt); active = true; } else st.p = st.pT;
    if (st.yo > 0) { st.yo = Math.max(0, st.yo - dt / 0.7); model.setYoGlow(st.yo); active = true; }
    if (cur) render();
    if (active) invalidate();
    else last = 0;
  };
  function invalidate() { if (!needs && cur) { needs = true; requestAnimationFrame(frame); } }
  const pickStage = () => {
    let best = null, br = 0;
    for (const [n, r] of Object.entries(vis)) if (r > br) { br = r; best = n; }
    if (best) mount(best);
  };
  canvas.addEventListener('webglcontextlost', (e) => { e.preventDefault(); for (const S of Object.values(stages)) S.el.classList.remove('is-live'); cur = null; });
  const ray = new Raycaster(), ndc = new Vector2();
  const api = {
    renderer, scene, model, invalidate,
    press(id, down) {
      const s = springs.get(id) || { x: 0, v: 0, target: 0, down };
      s.target = down ? TRAVEL : 0; s.down = down; springs.set(id, s); invalidate();
    },
    yo() { st.yo = 1; invalidate(); },
    hitTest(stage, x, y) {
      if (!cur || stages[cur].el !== stage) return null;
      const r = canvas.getBoundingClientRect();
      ndc.set(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(ndc, stages[cur].cam);
      return model.pick(ray);
    },
    async setColorway(cw) { st.cw = cw; await model.setColorway(cw); if (cur) setRig(cur); invalidate(); },
    setTurn(a, smooth) { st.turnT = a; st.snap = !smooth; invalidate(); },
    setExplode(p) { st.pT = p === null ? 0 : p; if (cur === 'x') invalidate(); },
    onStage(name, on, ratio) { vis[name] = on ? ratio : 0; pickStage(); },
    async enablePost(mod, opts = {}) {
      post = await mod.createPost({ renderer, scene, cam: cur ? stages[cur].cam : stages.type.cam, phone, ...opts });
      size(); invalidate();
    },
    mount, stages, st, L,
    get frames() { return frames; },
  };
  window.__kb3d = api;
  return api;
}
