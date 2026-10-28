// CD2 · опыт «цена AO трёх видов на одной сцене» (14-code-3d/05): N8AO (pmndrs — как на странице A; и в EffectComposer three),
// GTAOPass и SSAOPass (three/addons). Сцена — общий код «Звена» (_shared/code3d), поза hero, без фона-шейдера (иначе проход
// нормалей GTAO/SSAO рисует его треугольник), без bloom/LUT. Один экземпляр three на всё (бандл esbuild).
import { createScene } from '../../../../15-showcase/_shared/code3d/src/scene.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { SSAOPass } from 'three/examples/jsm/postprocessing/SSAOPass.js';
import { N8AOPass } from 'n8ao';

const q = new URLSearchParams(location.search);
const mode = q.get('ao') || 'none';                                 // none | n8pm | n8 | gtao | ssao
const W = +q.get('w') || 1440, H = +q.get('h') || 900, dur = +q.get('ms') || 2500;
const c = document.getElementById('c'); c.style.width = W + 'px'; c.style.height = H + 'px';
let composer = null;
const s = createScene(c, { dprMax: +q.get('dpr') || 1.5, quality: 'high', preserve: true,
  flags: { ao: mode === 'n8pm', fx: false }, onDraw: (r, scene, camera) => { if (composer) composer.render(); else r.render(scene, camera); } });
await s.ready;
s.__dbg.bg.visible = false;                                         // фон-шейдер — вне опыта (в проходе нормалей он ломает AO)
s.resize(W, H, false);
const { scene, camera } = s.__dbg, r = s.renderer;
if (mode === 'n8' || mode === 'gtao' || mode === 'ssao') {
  composer = new EffectComposer(r); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  if (mode === 'n8') {
    const p = new N8AOPass(scene, camera, W, H); const k = p.configuration;
    Object.assign(k, { halfRes: true, depthAwareUpsampling: true, aoRadius: 0.32, distanceFalloff: 0.6, intensity: 2.4, aoSamples: 12,
      denoiseSamples: 6, denoiseRadius: 10, transparencyAware: false, accumulate: false, gammaCorrection: false });
    composer.addPass(p);
  } else if (mode === 'gtao') {
    const p = new GTAOPass(scene, camera, W, H);
    p.output = GTAOPass.OUTPUT.Default; p.blendIntensity = 1;
    p.updateGtaoMaterial({ radius: 0.32, distanceExponent: 1, thickness: 1, scale: 1, samples: 16 });
    p.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 4, rings: 2, samples: 16 });
    composer.addPass(p);
  } else {
    const p = new SSAOPass(scene, camera, W, H, 32);
    p.kernelRadius = 0.32; p.minDistance = 0.00002; p.maxDistance = 0.0015;   // min/max — в нормированной глубине (near 0,1 … far 260)
    composer.addPass(p);
  }
  composer.addPass(new OutputPass());                               // тон (Neutral рендерера) + sRGB — как прямой рендер
}
const gl = r.getContext(), px = new Uint8Array(4), sync = () => gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
const t0 = performance.now(); s.set('story', 0, true); s.renderNow(); sync(); const first = performance.now() - t0;
for (let i = 0; i < 5; i++) { s.set('story', 0.001 * i, true); s.renderNow(); } sync();
await new Promise((res) => (window.requestIdleCallback ? requestIdleCallback(() => res(), { timeout: 3000 }) : setTimeout(res, 500)));
const dts = []; let prev = 0, n = 0; const start = performance.now();
await new Promise((done) => {
  function loop() {
    const now = performance.now(); if (prev) dts.push(now - prev); prev = now;
    if (now - start > dur) return done();
    s.set('story', (n++ % 2) * 0.0005, true); s.renderNow(); requestAnimationFrame(loop);   // поза та же, кадр каждый раз новый
  }
  requestAnimationFrame(loop);
});
s.set('story', 0, true); s.renderNow(); sync();
const med = (a) => { const b = [...a].sort((x, y) => x - y); return b[Math.floor(b.length / 2)]; };
window.__res = { mode, w: W, h: H, dpr: r.getPixelRatio(), frames: dts.length, frame_med: +med(dts).toFixed(3),
  frame_p90: +[...dts].sort((x, y) => x - y)[Math.floor(dts.length * 0.9)].toFixed(3), stalls50: dts.filter((x) => x > 50).length,
  first_ms: Math.round(first), calls: r.info.render.calls, programs: r.info.programs.length };
window.__done = true;
