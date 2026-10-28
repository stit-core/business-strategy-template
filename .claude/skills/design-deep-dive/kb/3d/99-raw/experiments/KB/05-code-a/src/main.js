// main.js — вариант A (код на максимуме): один кадр hero «Ё» в той же камере, что H1 Blender (camera_H1.json).
// Свет — схема S2 кодом: ключ низко слева (RectAreaLight + направленный с мягкой тенью), два контровых-полосы, верхний
// «кикер», лампа фона; окружение — PMREM студии из светящихся панелей в тех же направлениях (отражения металла);
// пост: N8AO (щели между колпачками), Bokeh (ГРИП на Ё), OutputPass (Neutral, 2^−0,35 как в Blender).
import {
  WebGLRenderer, Scene, PerspectiveCamera, Color, Vector3, Quaternion, Matrix4, Mesh, PlaneGeometry, MeshStandardMaterial,
  MeshBasicMaterial, RectAreaLight, DirectionalLight, PMREMGenerator, NeutralToneMapping, SRGBColorSpace, PCFShadowMap,
  HalfFloatType, WebGLRenderTarget, Group, DoubleSide, SphereGeometry, BackSide, MeshPhysicalMaterial,
} from 'three';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { N8AOPass } from 'n8ao';
import { buildKeyboard } from './kb3.js';

const Q = new URLSearchParams(location.search);
const OPT = { cam: Q.get('cam') || 'H1', ao: Q.get('ao') !== '0', dof: Q.get('dof') !== '0', k: +(Q.get('k') || 1),
  env: +(Q.get('env') || 0.12), exp: +(Q.get('exp') || -0.35), aperture: +(Q.get('ap') || 0.03), cw: Q.get('cw') || 'snow' };
const t0 = performance.now();

async function fonts() {
  const faces = [
    new FontFace('Onest', 'url(assets/fonts/onest-cyrillic-wght-normal.woff2)', { weight: '100 900', unicodeRange: 'U+0400-045F, U+2116' }),
    new FontFace('Onest', 'url(assets/fonts/onest-latin-wght-normal.woff2)', { weight: '100 900', unicodeRange: 'U+0000-00FF, U+2000-206F, U+2191, U+2193, U+2212' }),
  ];
  for (const f of faces) { await f.load(); document.fonts.add(f); }
  await document.fonts.ready;
}

const sph = (c, az, el, d) => {
  const a = az * Math.PI / 180, e = el * Math.PI / 180;
  return new Vector3(Math.sin(a) * Math.cos(e), -Math.cos(a) * Math.cos(e), Math.sin(e)).multiplyScalar(d).add(c);
};
// ориентация как kbr.orient: −Z на цель, локальная X — по xdir (координаты Blender внутри повёрнутой группы)
function orient(obj, pos, target, xdir) {
  const z = pos.clone().sub(target).normalize();
  let x = xdir ? xdir.clone().addScaledVector(z, -xdir.dot(z)) : new Vector3(0, 0, 1).cross(z);
  if (x.lengthSq() < 1e-8) x = new Vector3(1, 0, 0);
  x.normalize();
  const y = z.clone().cross(x);
  const m = new Matrix4().makeBasis(x, y, z); m.setPosition(pos);
  m.decompose(obj.position, obj.quaternion, obj.scale);
}

async function main() {
  const [P, CAM] = await Promise.all([fetch('assets/passport.json').then((r) => r.json()), fetch(`assets/camera_${OPT.cam}.json`).then((r) => r.json())]);
  await fonts();
  const W = CAM.res[0], H = CAM.res[1];
  const canvas = document.getElementById('c');
  const renderer = new WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.toneMapping = NeutralToneMapping;
  renderer.toneMappingExposure = 2 ** OPT.exp;
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFShadowMap;
  RectAreaLightUniformsLib.init();

  const scene = new Scene();
  const kb = buildKeyboard(P, OPT.cw);
  scene.add(kb.root);
  const root = kb.root;                                   // всё ниже — в координатах Blender внутри root
  const C = P.case;
  const c = new Vector3(0, 0, (C.foot_h + C.h_back) / 2);
  const r = new Vector3(C.W, C.D, C.h_back - C.foot_h).length() / 2;
  const d = 3.5 * r, az = CAM.az;
  // пол-циклорама S2: тёмный, шероховатый
  const floor = new Mesh(new PlaneGeometry(6, 6), new MeshPhysicalMaterial({ color: Q.get('floor') || '#0D0E10', roughness: 0.7, metalness: 0, specularIntensity: +(Q.get('fspec') || 0.6) }));  // блик пола подобран под пол B (L* ≈ 14)
  floor.receiveShadow = true; root.add(floor);
  // свет S2 (E — освещённость Blender, Вт/м²; RectAreaLight — яркость I = E·d²/A)
  const K = OPT.k;
  const lights = [
    { name: 'Key', az: az - 55, el: 16, w: 1.4 * r, h: 3.5 * r, E: 4.0 * 0.62 * K },
    { name: 'RimL', az: -150, el: 22, w: 5.0 * r, h: 0.2 * r, E: 4.8 * K, x: new Vector3(0, 1, 0) },
    { name: 'RimR', az: 140, el: 22, w: 5.0 * r, h: 0.2 * r, E: 4.8 * K, x: new Vector3(0, 1, 0) },
    { name: 'Top', az: 180, el: 62, w: 2.5 * r, h: 2.5 * r, E: 1.0 * K },
  ];
  const studio = new Scene();
  studio.add(new Mesh(new SphereGeometry(20, 32, 16), new MeshBasicMaterial({ color: '#060607', side: BackSide })));
  const sfloor = new Mesh(new PlaneGeometry(40, 40), new MeshBasicMaterial({ color: '#0D0E10' }));
  sfloor.rotation.x = -Math.PI / 2; sfloor.position.y = -0.03; studio.add(sfloor);
  const sroot = new Group(); sroot.rotation.x = -Math.PI / 2; studio.add(sroot);
  for (const L of lights) {
    const pos = sph(c, L.az, L.el, d);
    const I = L.E * d * d / (L.w * L.h);
    const ra = new RectAreaLight('#ffffff', I, L.w, L.h);
    orient(ra, pos, c, L.x); root.add(ra);
    const panel = new Mesh(new PlaneGeometry(L.w, L.h), new MeshBasicMaterial({ color: new Color(1, 1, 1).multiplyScalar(I), side: DoubleSide }));
    orient(panel, pos.clone().sub(c), new Vector3(), L.x); sroot.add(panel);
    L.pos = pos; L.I = I;
  }
  // тень ключа: направленный из той же точки (доля 0,38 от E ключа — остальное даёт RectAreaLight)
  const sun = new DirectionalLight('#ffffff', 4.0 * 0.38 * K);
  sun.position.copy(lights[0].pos); sun.target.position.copy(c); root.add(sun, sun.target);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 6; sun.shadow.bias = -0.0002; sun.shadow.normalBias = 0.0006;
  const sc = sun.shadow.camera; sc.left = -0.3; sc.right = 0.3; sc.top = 0.3; sc.bottom = -0.3; sc.near = 0.1; sc.far = 2.0; sc.updateProjectionMatrix();
  // лампа фона (пол за клавиатурой)
  {
    const th = az * Math.PI / 180; const back = new Vector3(-Math.sin(th), Math.cos(th), 0);
    const tgt = new Vector3(c.x, c.y, 0).addScaledVector(back, 0.45);
    const pos = new Vector3(c.x, c.y, 0).addScaledVector(back, 0.75).add(new Vector3(0, 0, 0.9));
    const dd = pos.distanceTo(tgt); const bg = new RectAreaLight('#ffffff', 0.6 * dd * dd / 1.44 * K, 1.2, 1.2);
    orient(bg, pos, tgt); root.add(bg);
  }
  // окружение PMREM из той же «студии» (отражения на металле и фасках)
  const pmrem = new PMREMGenerator(renderer);
  const envRT = pmrem.fromScene(studio, 0.02, 0.05, 30);
  scene.environment = envRT.texture;
  scene.environmentIntensity = OPT.env;
  scene.background = new Color('#0D0E10');
  // камера Blender → three: позиция (x, z, −y), поворот = Rx(−90°) · q_blender; сдвиг — setViewOffset
  const cam = new PerspectiveCamera(30, W / H, 0.01, 20);
  const [bx, by, bz] = CAM.location;
  cam.position.set(bx, bz, -by);
  const [qw, qx, qy, qz] = CAM.quaternion_wxyz;
  cam.quaternion.copy(new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2).multiply(new Quaternion(qx, qy, qz, qw)));
  const hfov = 2 * Math.atan(CAM.sensor_width_mm / 2 / CAM.lens_mm);
  cam.fov = 2 * Math.atan(Math.tan(hfov / 2) / (W / H)) * 180 / Math.PI;
  cam.setViewOffset(W, H, CAM.shift_x * W, -CAM.shift_y * W, W, H);
  cam.updateProjectionMatrix();
  // пост
  const rt = new WebGLRenderTarget(W, H, { type: HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, cam));
  if (OPT.ao) {
    const ao = new N8AOPass(scene, cam, W, H);
    Object.assign(ao.configuration, { aoRadius: 0.006, distanceFalloff: 0.004, intensity: 2.2, halfRes: false, screenSpaceRadius: false,
      color: new Color('#000000'), aoSamples: 24, denoiseSamples: 8, denoiseRadius: 6, gammaCorrection: false });
    composer.addPass(ao);
  }
  if (OPT.dof) composer.addPass(new BokehPass(scene, cam, { focus: CAM.focus_distance_m, aperture: OPT.aperture, maxblur: 0.008 }));
  composer.addPass(new OutputPass());
  await renderer.compileAsync(scene, cam);
  renderer.info.autoReset = false;
  renderer.info.reset();
  composer.render();
  performance.mark('hero-first-frame');
  const info = { ms_to_first_frame: Math.round(performance.now() - t0), calls: renderer.info.render.calls, tris: renderer.info.render.triangles,
    programs: renderer.info.programs.length, atlas: kb.atlas.size, opt: OPT, light_I: lights.map((L) => [L.name, +L.I.toFixed(2)]) };
  console.warn('KB timing', JSON.stringify(info));
  window.__info = info; window.__ready = true;
}
main().catch((e) => { console.error(e); window.__info = { error: String(e) }; window.__ready = true; });
