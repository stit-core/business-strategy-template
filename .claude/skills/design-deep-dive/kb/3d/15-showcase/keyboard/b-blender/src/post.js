// post.js — десктопный уровень качества A и C: N8AO (щели между колпачками, стыки корпуса) + OutputPass (Neutral).
// Грузится отдельным чанком после первого кадра; телефону не грузится вовсе. Альфа кадра сохраняется (фон — CSS раздела).
// Постер A (только ?capture=hero-…): ГРИП «разброс как сбор» по буферу глубины BokehPass — радиус кружка нерезкости по
// тонкой линзе из камеры Blender (f, N, фокус, сенсор), выборка с учётом порядка по глубине (резкий передний план не
// «течёт» ореолом на размытый фон). Скорость не важна — кадр снимается один раз.
import { HalfFloatType, WebGLRenderTarget, Vector2, Color } from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { N8AOPass } from 'n8ao';

// Gustafsson (2018) «Bokeh depth of field in a single pass»: спираль золотого угла, радиус растёт как r += s/r
const DOF_FRAG = /* glsl */`
#include <common>
#include <packing>
varying vec2 vUv;
uniform sampler2D tColor;
uniform sampler2D tDepth;
uniform float nearClip;
uniform float farClip;
uniform float focus;
uniform float uCoc;
uniform float uMax;
uniform float uStep;
uniform vec2 uRes;
float dist(vec2 uv) { return -perspectiveDepthToViewZ(unpackRGBAToDepth(texture2D(tDepth, uv)), nearClip, farClip); }
float blurSize(float d) { return clamp(uCoc * abs(d - focus) / max(d, 1e-4), 0.0, uMax); }
void main() {
  float cd = dist(vUv);
  float cs = blurSize(cd);
  vec4 c0 = texture2D(tColor, vUv);
  vec3 col = c0.rgb;
  float tot = 1.0;
  float rad = uStep;
  float ang = 0.0;
  for (int i = 0; i < 6000; i++) {
    if (rad >= uMax) break;
    vec2 tc = vUv + vec2(cos(ang), sin(ang)) * rad / uRes;
    vec3 sc = texture2D(tColor, tc).rgb;
    float sd = dist(tc);
    float ss = blurSize(sd);
    if (sd > cd) ss = clamp(ss, 0.0, cs * 2.0);
    float m = smoothstep(rad - 0.5, rad + 0.5, ss);
    col += mix(col / tot, sc, m);
    tot += 1.0;
    rad += uStep / rad;
    ang += 2.39996323;
  }
  gl_FragColor = vec4(col / tot, c0.a);
}`;

function makeDOF(scene, cam, dof, w, h) {
  const bp = new BokehPass(scene, cam, { focus: dof.focus, aperture: 1, maxblur: 1 });
  const m = bp.materialBokeh;
  // радиус (px) = ½ · px_на_метр_сенсора · f² / (N (s − f)) · |d − s| / d
  const f = dof.lens, N = dof.fstop, s = dof.focus;
  const k = 0.5 * dof.pxPerSensorM * (f * f) / (N * (s - f));
  Object.assign(m.uniforms, { uCoc: { value: k }, uMax: { value: dof.maxR || 48 }, uStep: { value: dof.step || 0.5 }, uRes: { value: new Vector2(w, h) } });
  m.fragmentShader = DOF_FRAG;
  m.needsUpdate = true;
  // фон сцены (текстура) рисуется своим материалом (allowOverride = false) и портит буфер глубины → на время прохода глубины фона нет
  const r0 = bp.render.bind(bp);
  bp.render = (renderer, wb, rb, dt, mask) => { const bg = scene.background; scene.background = null; r0(renderer, wb, rb, dt, mask); scene.background = bg; };
  bp.kbDof = { k, maxR: m.uniforms.uMax.value };
  return bp;
}

export function createPost({ renderer, scene, cam, dof = null }) {
  const s = renderer.getSize(new Vector2());
  const rt = new WebGLRenderTarget(s.x, s.y, { type: HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, rt);
  const rp = new RenderPass(scene, cam);
  rp.clearAlpha = 0;
  let ao = null;
  const makeAO = (c, w, h) => {
    const p = new N8AOPass(scene, c, w, h);
    Object.assign(p.configuration, { aoRadius: 0.006, distanceFalloff: 0.004, intensity: 2.0, halfRes: false, screenSpaceRadius: false,
      color: new Color('#000000'), aoSamples: 16, denoiseSamples: 8, denoiseRadius: 6, gammaCorrection: false });
    return p;
  };
  ao = makeAO(cam, s.x, s.y);
  const out = new OutputPass();
  composer.addPass(rp); composer.addPass(ao);
  const pr = renderer.getPixelRatio();
  const dofPass = dof ? makeDOF(scene, cam, dof, s.x * pr, s.y * pr) : null;   // только кадр-постер A (ГРИП на Ё)
  if (dofPass) composer.addPass(dofPass);
  composer.addPass(out);
  let size = [s.x, s.y];
  window.__kbPost = { composer, dof: dofPass ? dofPass.kbDof : null };
  return {
    render() { composer.render(); },
    setSize(w, h) {
      size = [w, h]; composer.setPixelRatio(renderer.getPixelRatio()); composer.setSize(w, h);
      if (dofPass) dofPass.materialBokeh.uniforms.uRes.value.set(w * renderer.getPixelRatio(), h * renderer.getPixelRatio());
    },
    setCamera(c) {
      rp.camera = c;
      const i = composer.passes.indexOf(ao);
      ao.dispose?.();
      ao = makeAO(c, size[0] * renderer.getPixelRatio(), size[1] * renderer.getPixelRatio());
      composer.passes[i] = ao;
      composer.setSize(size[0], size[1]);
    },
  };
}
