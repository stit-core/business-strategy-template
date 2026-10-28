// world.js · общий код 3D «Звена» (_shared/code3d) · приём «world»: туман по высоте во всех материалах,
// фон (v2 — экранный, v3 — мировой: горизонт + ореол в дымке), пол (v2 — циклорама, v3 — тёмный пол с отражением), зеркальный проход.
import {
  Mesh, Scene, PerspectiveCamera, OrthographicCamera, PlaneGeometry, BufferGeometry, Float32BufferAttribute, CanvasTexture,
  ShaderMaterial, MeshStandardMaterial, MeshPhysicalMaterial, MeshBasicMaterial, Color, Vector2, Vector3, Vector4, Matrix4, Plane,
  WebGLRenderTarget, HalfFloatType, LinearFilter,
} from 'three';
import { preTone } from './util.js';

// ---------- туман по высоте + зеркальный проход: общие uniform всех материалов (onBeforeCompile, один кэш-ключ на тип)
export const HF = {
  uHF: { value: new Vector4(0.0, 0.5, 6, 0) },                   // x — плотность 1/м (0 — нет тумана), y — спад по высоте 1/м, z — старт, м
  uHFColor: { value: new Color(0, 0, 0) },                       // цвет тумана «до тона» (preTone)
  uMirrorPass: { value: 0 },                                     // 1 — рисуем отражение: в альфу пишем «близость к полу»
  uHalo: { value: new Vector4(0, 0, -1, 0) },                    // ореол в дымке за объектом: xyz — направление из камеры, w — сила
  uHaloColor: { value: new Color(0.007, 0.008, 0.011) },          // ореол тихий: фон кадра ≈ фон страницы (ΔE ≤ 3, img_metrics)
  uHaloWidth: { value: 36 },                                     // ширина ореола (36 — как в фазах 1–2; телефон p3 — шире и ярче)
};
export const HALO_BASE = [0.007, 0.008, 0.011];
const HF_VERT_PARS = 'varying vec3 vHFW;';
const HF_VERT = '{ vec4 hw = vec4(transformed, 1.0);\n#ifdef USE_INSTANCING\nhw = instanceMatrix * hw;\n#endif\nhw = modelMatrix * hw; vHFW = hw.xyz; }';
const HF_FRAG_PARS = 'varying vec3 vHFW; uniform vec4 uHF; uniform vec3 uHFColor; uniform float uMirrorPass; uniform vec4 uHalo; uniform vec3 uHaloColor; uniform float uHaloWidth;';
const HF_FRAG = `
{ float hd = distance(vHFW, cameraPosition);
  float hf = (1.0 - exp(-uHF.x * max(hd - uHF.z, 0.0))) * exp(-uHF.y * max(vHFW.y, 0.0));
  vec3 vd = normalize(vHFW - cameraPosition);
  vec3 fc = uHFColor + uHaloColor * uHalo.w * exp(-(1.0 - dot(vd, uHalo.xyz)) * uHaloWidth);   // та же формула, что у фона: шва на горизонте нет
  outgoingLight = mix(outgoingLight, fc, clamp(hf, 0.0, 1.0)); }
`;
const HF_MIRROR = 'if (uMirrorPass > 0.5) gl_FragColor.a = 1.0 - clamp(vHFW.y * 0.6, 0.0, 1.0);\n';
export function hfPatch(sh, extra) {
  Object.assign(sh.uniforms, HF, extra ? extra.uniforms : null);
  sh.vertexShader = sh.vertexShader
    .replace('#include <common>', `#include <common>\n${HF_VERT_PARS}\n${extra ? extra.vertPars || '' : ''}`)
    .replace('#include <fog_vertex>', `#include <fog_vertex>\n${HF_VERT}\n${extra ? extra.vert || '' : ''}`);
  sh.fragmentShader = sh.fragmentShader
    .replace('#include <common>', `#include <common>\n${HF_FRAG_PARS}\n${extra ? extra.fragPars || '' : ''}`)
    .replace('#include <opaque_fragment>', `${extra ? extra.frag || '' : ''}\n${HF_FRAG}\n#include <opaque_fragment>\n${HF_MIRROR}`);
}
export function withHF(mat, key = 'hf') {                          // материал сцены получает туман и зеркальную альфу
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => { if (prev && prev !== withHF.noop) prev(sh, r); hfPatch(sh); };
  const prevKey = mat.customProgramCacheKey.bind(mat);
  mat.customProgramCacheKey = () => key + prevKey();
  mat.userData.hf = true;
  return mat;
}
withHF.noop = MeshStandardMaterial.prototype.onBeforeCompile;

// ---------- фон: v2 (экранный) и v3 (мировой: горизонт + ореол за объектом); фон идёт через тот же тон-маппинг
export function backdrop(worldMode, exposure, usePost) {
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
      uHaloW: HF.uHalo, uHaloColor: HF.uHaloColor, uHaloWidth: HF.uHaloWidth,
    },
    vertexShader: 'varying vec2 vUv; void main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 1.0, 1.0); }',
    fragmentShader: `
      uniform vec2 uGlow; uniform float uAspect, uR, uDither, uHalo2, uHaloWidth; uniform vec3 uTop, uBot, uHor, uHalo, uWarm, uCam, uHaloColor; uniform vec4 uHaloW; uniform mat4 uInvVP; varying vec2 vUv;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      void main() {
        vec2 d = (vUv - uGlow) * vec2(uAspect, 1.0);
        ${worldMode ? `
        vec4 wp = uInvVP * vec4(vUv * 2.0 - 1.0, 1.0, 1.0); vec3 dir = normalize(wp.xyz / wp.w - uCam);
        float el = dir.y;
        vec3 c = el < 0.0 ? uHor : mix(uHor, uTop, smoothstep(0.0, 0.42, el));   // ниже горизонта — цвет тумана: край пола не виден
        c += uHaloColor * uHaloW.w * exp(-(1.0 - dot(dir, uHaloW.xyz)) * uHaloWidth);  // ореол в дымке — та же формула в тумане пола
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
export function floorV2(hq) {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const x = c.getContext('2d'); const gr = x.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.3, '#b4b4b4'); gr.addColorStop(0.62, '#383838'); gr.addColorStop(1, '#000000');
  x.fillStyle = gr; x.fillRect(0, 0, 256, 256);
  const m = new Mesh(new PlaneGeometry(7, 7), new MeshStandardMaterial({ color: '#101215', roughness: 0.86, metalness: 0,
    transparent: true, alphaMap: new CanvasTexture(c), depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.position.y = -0.001; m.receiveShadow = hq; m.renderOrder = -6;
  return m;
}
export function floorV3(hq, mirror) {
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
export function contactShadow() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d'); const gr = x.createRadialGradient(64, 64, 4, 64, 64, 64);
  gr.addColorStop(0, 'rgba(0,0,0,0.6)'); gr.addColorStop(0.5, 'rgba(0,0,0,0.22)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
  const m = new Mesh(new PlaneGeometry(1.7, 1.7), new MeshBasicMaterial({ map: new CanvasTexture(c), transparent: true, depthWrite: false }));
  m.rotation.x = -Math.PI / 2; m.position.y = 0.002; m.renderOrder = -5;
  return m;
}

// ---------- зеркальный проход (world, десктоп): отражение пола y = 0 в ½ разрешения + размытие в ¼ (Reflector three — логика)
export function createMirror(renderer) {
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
