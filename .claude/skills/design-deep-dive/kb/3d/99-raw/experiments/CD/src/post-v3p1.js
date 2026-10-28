// ЗАМОРОЖЕНО 25.09 20:30: исходник фазы 1 (= бандл v3p1-ref). С фазы 2 сцена живёт в 15-showcase/_shared/code3d/src/.
// post.js · «Звено» код v3 · дорожка CD · 2026-09-25 — постобработка отдельным чанком (десктоп, quality high)
// pmndrs postprocessing 6.39.5 (peer three < 0.187) + n8ao 2.0.1 · WebGLRenderer
// Цепочка: RenderPass (HDR, HalfFloat, MSAA) → N8AO (AO на стыках, ½ разрешения, нормали из глубины, без накопления — кадры
// только по вводу) → EffectPass [Bloom (по яркости: горят кольца и кромка скана) → Neutral (тон — здесь, у рендерера NoToneMapping)
// → LUT (процедурная, 32³) → зерно] + дизеринг. Каждый эффект включается флагом: ao, fx.
import { HalfFloatType, Scene, Mesh, BufferGeometry, Float32BufferAttribute, OrthographicCamera } from 'three';
import { EffectComposer, RenderPass, EffectPass, BloomEffect, ToneMappingEffect, ToneMappingMode, LUT3DEffect, LookupTexture,
  NoiseEffect, BlendFunction, VignetteEffect, FXAAEffect } from 'postprocessing';
import { N8AOPostPass } from 'n8ao';

// LUT «Звена»: мягкая S-кривая в средних тонах, тени чуть холоднее (к цвету страницы #101215), фирменный оранжевый + 4 %
// насыщенности, остальное −5 % (промышленный нейтральный вид). Тёмные ≤ 0,08 (sRGB) почти не трогаем: фон страницы — ΔE ≤ 1.
function makeLUT(size = 32) {
  const lut = LookupTexture.createNeutral(size);
  const d = lut.image.data;
  const sm = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  for (let i = 0; i < d.length; i += 4) {
    let r = d[i], g = d[i + 1], b = d[i + 2];
    const L = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    const w = sm(0.08, 0.3, L) * (1 - sm(0.66, 0.92, L));           // средние тона; светлые не трогаем — иначе блики уходят в 255
    const k = 0.3 * w * (L - 0.45) * (1 - L);                       // S-кривая по яркости
    r += k; g += k; b += k;
    const sh = (1 - sm(0.05, 0.4, L)) * sm(0.03, 0.1, L);           // только глубокие полутени
    r -= 0.004 * sh; b += 0.006 * sh;
    const L2 = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    const orange = sm(0.18, 0.45, r - b) * (g < 0.75 * r ? 1 : 0);
    const sat = 0.95 + 0.09 * orange;
    r = L2 + (r - L2) * sat; g = L2 + (g - L2) * sat; b = L2 + (b - L2) * sat;
    d[i] = Math.min(1, Math.max(0, r)); d[i + 1] = Math.min(1, Math.max(0, g)); d[i + 2] = Math.min(1, Math.max(0, b));
  }
  lut.needsUpdate = true;
  return lut;
}

// MSAA композитора и N8AO вместе — первый кадр 0,5–1,35 с (перекомпиляция/резолв глубины), без MSAA — 65–150 мс (CD dbg-programs):
// с AO берём multisampling 0 и FXAA в том же EffectPass (свёртка — одна на проход, её место — FXAA)
export function createPost(renderer, scene, camera, { ao = true, fx = true, msaa } = {}) {
  if (msaa === undefined) msaa = ao ? 0 : 4;
  const composer = new EffectComposer(renderer, { frameBufferType: HalfFloatType, multisampling: msaa });
  composer.addPass(new RenderPass(scene, camera));
  let n8 = null;
  if (ao) {
    n8 = new N8AOPostPass(scene, camera, 256, 256);
    const c = n8.configuration;
    c.transparencyAware = false;                                   // иначе при прозрачных объектах сцены — ещё 2 прохода сцены
    c.accumulate = false;                                          // накопление по кадрам противоречит «0 кадров в покое»
    c.halfRes = true; c.depthAwareUpsampling = true;
    c.aoRadius = 0.32; c.distanceFalloff = 0.6; c.intensity = 2.4; c.aoSamples = 12; c.denoiseSamples = 6; c.denoiseRadius = 10;
    c.gammaCorrection = false;                                      // дальше — EffectPass в линейном
    composer.addPass(n8);
  }
  const effects = [];
  let bloom = null;
  if (fx) {
    // порог по яркости 3,4 (HDR, до тона; 2,6 ловил искру на анизотропном алюминии): блики лака (≤ ≈ 2) не горят, вспышка кольца (яркость ≈ 4) и кромка скана — горят
    bloom = new BloomEffect({ luminanceThreshold: 3.4, luminanceSmoothing: 0.3, intensity: 0.9, mipmapBlur: true, radius: 0.6, levels: 5 });
    effects.push(bloom);
  }
  effects.push(new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }));
  if (fx) {
    effects.push(new LUT3DEffect(makeLUT(32), { tetrahedralInterpolation: true }));
    const noise = new NoiseEffect({ blendFunction: BlendFunction.SOFT_LIGHT, premultiply: false });   // OVERLAY выбивал блики в 255 (клиппинг 3,9 %)
    noise.blendMode.opacity.value = 0.05;                            // 0,12 в мягком свете давала «крапинку» на графите (+5/255 в тёмных)
    effects.push(noise);
    effects.push(new VignetteEffect({ offset: 0.42, darkness: 0.42 }));   // виньетка v2 ушла из фона (мир): теперь общая для пола и неба
  }
  const pass = new EffectPass(camera, ...effects);
  pass.dithering = true;
  composer.addPass(pass);
  // FXAA — отдельным проходом ПОСЛЕ тона: свёрточный эффект в общем EffectPass читает сырой входной буфер (HDR до bloom, тона и LUT)
  // и выбрасывает результат предыдущих эффектов (кадр без тона: пересвет 11,5 %, шум AO на крышках — CD f-v3 19:37)
  if (msaa === 0) composer.addPass(new EffectPass(camera, new FXAAEffect()));
  let last = performance.now();
  // прогрев программ поста без длинной задачи: EffectPass собирает общий материал, все ShaderMaterial цепочки (N8AO, bloom,
  // эффекты) компилируются через compileAsync (KHR_parallel_shader_compile) с тем же целевым буфером, что при рендере:
  // three различает программы по цветовому пространству выхода (буфер — линейный, экран — sRGB)
  async function warm() {
    for (const p of composer.passes) if (typeof p.recompile === 'function') p.recompile();
    const mats = new Set(), seen = new Set();
    const walk = (o, d) => {
      if (!o || typeof o !== 'object' || seen.has(o) || d > 5) return; seen.add(o);
      if (o.isMaterial) { mats.add(o); return; }
      if (o.isScene || o.isCamera || o.isTexture || o.isBufferGeometry || o.isWebGLRenderTarget || ArrayBuffer.isView(o) || o === renderer) return;
      if (o instanceof Map) { o.forEach((v) => walk(v, d + 1)); return; }
      for (const k of Object.keys(o)) { try { walk(o[k], d + 1); } catch (e) { /* геттеры */ } }
    };
    composer.passes.forEach((p) => walk(p, 0));
    const last = composer.passes[composer.passes.length - 1].fullscreenMaterial;
    const g = new BufferGeometry();
    g.setAttribute('position', new Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
    g.setAttribute('uv', new Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
    const toRT = new Scene(), toScreen = new Scene(), cam = new OrthographicCamera(-1, 1, 1, -1, 0, 1);
    mats.forEach((m) => { const mesh = new Mesh(g, m); mesh.frustumCulled = false; (m === last ? toScreen : toRT).add(mesh); });
    const cur = renderer.getRenderTarget();
    renderer.setRenderTarget(composer.inputBuffer); const p1 = renderer.compileAsync(toRT, cam);
    renderer.setRenderTarget(null); const p2 = renderer.compileAsync(toScreen, cam);
    renderer.setRenderTarget(cur);
    await Promise.all([p1, p2]);
    g.dispose();
    return mats.size;
  }
  return {
    composer, n8, bloom, warm, target: () => composer.inputBuffer,
    render() { const now = performance.now(); composer.render(Math.min(0.1, (now - last) / 1000)); last = now; },
    setSize(w, h) { composer.setSize(w, h, false); },
    dispose() { composer.dispose(); },
  };
}
