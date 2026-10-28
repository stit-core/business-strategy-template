// main_3d.js — общий вход A и C: до 3D и при reduce — кадры (C — Blender, A — снятые с кода A) и слой подсветки нажатий;
// 3D (three) грузится только после load и по намерению: первое взаимодействие или остановка на разделе с 3D (см. ниже).
import { startPage, afterLoadIdle, isPhone, reduceMQ, logTiming } from './page.js';
import { createAdapterB } from './adapter_b.js';
import { makeProxy } from './proxy.js';

export function boot(variant, loadModel) {
  const cfg = window.KB_CFG;
  const cap = new URLSearchParams(location.search).get('capture');
  if (cap) { import('./capture.js').then((m) => m.capture(cap, variant, loadModel)); return; }
  if (reduceMQ.matches) {                        // reduce: three не грузится, 0 кадров WebGL
    startPage(createAdapterB({ pressFrames: cfg.staticPressFrames, turnFrames: cfg.staticTurnFrames }));
    logTiming({ mode: 'reduce-static' });
    return;
  }
  const proxy = makeProxy();
  const fallback = createAdapterB({ pressFrames: cfg.staticPressFrames, turnFrames: false, lazyOnly: true });
  const page = startPage({
    press: (id, d) => { proxy.press(id, d); if (!window.__kb3d) fallback.press(id, d); },
    yo: () => proxy.yo(),
    hitTest: (st, x, y) => (window.__kb3d ? proxy.hitTest(st, x, y) : fallback.hitTest(st, x, y)),
    setColorway: (cw) => { proxy.setColorway(cw); fallback.setColorway(cw); },
    setTurn: (a, s) => proxy.setTurn(a, s),
    setExplode: (p) => proxy.setExplode(p),
    onStage: (n, on, r) => proxy.onStage(n, on, r),
  });
  void page;
  const gl2 = typeof WebGL2RenderingContext !== 'undefined';   // без пробного контекста: на странице ровно один WebGL
  const idle = () => new Promise((r) => ('requestIdleCallback' in window ? requestIdleCallback(r, { timeout: 300 }) : setTimeout(r, 16)));
  const lowData = navigator.connection?.saveData || (navigator.deviceMemory && navigator.deviceMemory < 2);
  const go = async () => {
    if (!gl2 || lowData) { logTiming({ mode: gl2 ? 'save-data-static' : 'no-webgl2-static' }); console.warn('KB: 3D пропущено — кадры'); return; }
    const t = performance.now();
    try {
      const [{ createStage3D }, buildModel, cams] = await Promise.all([
        import('./stage3d.js'), loadModel(),
        Promise.all(['T', 'R', 'X'].map((n) => fetch(`assets/data/${n}.json`).then((r) => r.json()))),
      ]);
      const [T, Rr, X] = cams;
      await idle();
      const s = await createStage3D({ buildModel, cams: { type: T, turn: Rr, x: X }, phone: isPhone, variant,
        quality: { shadows: variant === 'a' && !isPhone }, idle });
      proxy.attach(s);
      document.getElementById('stage-type').querySelector('.keylayer')?.replaceChildren();
      logTiming({ three_ready_ms: Math.round(performance.now() - t) });
      if (!isPhone) {                               // пост (N8AO) — отдельным чанком в следующий простой, не посреди прокрутки
        const post = await import('./post.js');
        await idle(); await idle();
        s.enablePost(post);
      }
    } catch (e) {
      console.error('KB 3D failed', e);
    }
  };
  // three — «по намерению», не посреди прокрутки (ворота EG-PERF-01 считают длинные кадры всей фазы прокрутки): первое
  // взаимодействие (клавиша, касание, клик) или остановка ≥ 2,5 с, когда раздел с 3D (набор, цвета, разборка) на экране.
  // До этого разделы показывают кадры (C — Blender, A — свои) и уже отвечают на нажатия.
  afterLoadIdle(() => {
    let started = false, timer = 0;
    const stagesEls = ['stage-type', 'stage-turn', 'stage-x'].map((id) => document.getElementById(id));
    const start = (why) => {
      if (started) return;
      started = true;
      clearTimeout(timer);
      for (const [t, f, o] of subs) removeEventListener(t, f, o);
      logTiming({ three_trigger: why, three_trigger_ms: Math.round(performance.now()) });
      go();
    };
    const inView = () => stagesEls.some((el) => {
      const r = el.getBoundingClientRect(), h = innerHeight;
      return Math.min(r.bottom, h) - Math.max(r.top, 0) > Math.min(r.height, h) * 0.35;
    });
    const arm = () => { clearTimeout(timer); timer = setTimeout(() => { if (inView()) start('dwell'); }, 2500); };
    const subs = [['pointerdown', () => start('pointer'), { capture: true, passive: true }],
      ['keydown', () => start('key'), { capture: true }],
      ['touchstart', () => start('touch'), { capture: true, passive: true }],
      ['scroll', arm, { passive: true }]];
    for (const [t, f, o] of subs) addEventListener(t, f, o);
    arm();
  });
}
