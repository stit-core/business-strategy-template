// main.js · L2 «Звено» · Chromium 153 / WebKit 26.6 · ≈ 1,6 КБ br
// «Код v3»: сцена v3 (three 0.186.0), касание на телефоне ставит цель руке (IK), метка
// hero-first-frame и строка «CD timing» в консоль.
// Порядок: HTML со смыслом и постер (LCP) → после load + простоя — import('./three-scene.js') (three 0.186.1, ≈ 123 КБ br) → первый кадр →
// постер гаснет. В reduce (ОС или кнопка «Меньше движения») сцена не грузится: страница — стопка станций-картинок (reduce: stations).
// Без WebGL и без JS — то же. Холст рисует только при прокрутке, указателе и одноразовом «пробуждении» (0 кадров в покое).
// Телефон получает quality 'low' (Standard, без карты теней).
const root = document.documentElement;
let canvas = document.querySelector('.stage');
const hero = document.querySelector('[data-section="hero"]');
const modules = document.querySelector('[data-scene="story"]');
const inside = document.querySelector('[data-scene="scan"]');
const btn = document.querySelector('[data-motion-toggle]');
const mqMobile = matchMedia('(max-width: 40rem), (pointer: coarse)');
const clamp = (x) => Math.min(1, Math.max(0, x));
let S = null, loading = null, lastW = 0, lastH = 0, introDone = false;

const reduced = () => (window.Motion ? window.Motion.reduced() : matchMedia('(prefers-reduced-motion: reduce)').matches);

function state() {
  const vh = innerHeight;
  const hr = hero.getBoundingClientRect(), mr = modules.getBoundingClientRect(), ir = inside.getBoundingClientRect();
  if (hr.bottom > 0) return ['story', clamp(-hr.top / hr.height)];
  if (mr.top < vh && mr.bottom > 0) return ['story', 1 + clamp(-mr.top / Math.max(1, mr.height - vh))];
  if (ir.top < vh && ir.bottom > 0) return ['scan', clamp(-ir.top / Math.max(1, ir.height - vh))];
  return [null, 0];
}

function update(instant) {
  if (!S) return;
  const [phase, t] = state();
  canvas.classList.toggle('is-hidden', !phase);
  if (!phase) { S.stop(); return; }
  S.set(phase, t, instant);
}

function size(force) {
  if (!S) return;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (!force && w === lastW && Math.abs(h - lastH) < 80) return;   // панель адреса телефона: высоту не дёргать
  lastW = w; lastH = h;
  S.resize(w, h, mqMobile.matches);
  // v3: рука тянется к указателю, но не заходит в колонку текста первого экрана (десктоп — правее текста, телефон — выше H1)
  if (S.ikBounds) {
    // правый край — по СОДЕРЖИМОМУ (строки текста, кнопки), а не по блоку: .hero__actions — флекс-строка во всю ширину
    // контейнера (край ≈ 1312 px из 1440) → minX упирался в 0,6, правее оси руки, и рука не тянулась к тексту вовсе
    const els = [...document.querySelectorAll('.hero__title, .hero__lead, .hero__actions, .hero__facts, .scene--modules .step')].filter((e) => e.offsetParent);
    const rg = document.createRange();
    const edge = (e) => { if (e.classList.contains('step')) return e.getBoundingClientRect().right; rg.selectNodeContents(e); return rg.getBoundingClientRect().right; };
    const right = Math.max(0, ...els.filter((e) => !e.classList.contains('step') || !mqMobile.matches).map(edge));
    const top = document.querySelector('.hero__title').getBoundingClientRect().top;
    S.ikBounds(Math.min(0.6, (right / innerWidth) * 2 - 1 + 0.08), 1 - (top / innerHeight) * 2 + 0.06);
  }
}

function boot() {
  if (loading) return loading;
  const idle = window.requestIdleCallback || ((f) => setTimeout(f, 200));
  loading = new Promise((done) => {
    // WebGL2 проверяем на том же холсте и отдаём контекст three: без второго контекста (EG-WEIGHT-03), без ошибки в консоли
    // (EG-FB-06) и без загрузки 125 КБ three.js там, где рисовать нечем
    let gl = null;
    try { gl = canvas.getContext('webgl2', { antialias: true, alpha: true, powerPreference: 'high-performance' }); } catch (e) { gl = null; }
    if (!gl) { root.classList.remove('gl-pending'); done(null); return; }
    const go = () => import('./three-scene.js').then(({ createScene }) => {
      if (reduced()) { done(null); loading = null; return; }
      // вид p3 — p2 + контровой свет в дымке за рукой (приём 8, десктоп) + след инструмента пунктиром при IK (приём 10)
      try { S = createScene(canvas, { context: gl, dprMax: mqMobile.matches ? 1.25 : 1.5, quality: mqMobile.matches ? 'low' : 'high', look: 'p3' }); }
      catch (e) { console.info('WebGL недоступен — страница остаётся на станциях-картинках'); root.classList.remove('gl-pending'); done(null); return; }
      window.__fx = { destroyAll: () => { if (S) { S.dispose(); S = null; } } };   // EG-CODE-01: чистое разрушение
      const s0 = S;
      // сцена v2 готовится несколькими задачами (PMREM, compileAsync) — первый кадр и смена постера только после готовности
      (S.ready || Promise.resolve(true)).then((ok) => {
        if (S !== s0 || ok === false) { done(null); return; }               // за время подготовки ушли в reduce — сцена разрушена
        size(true); update(true); S.renderNow();
        try { performance.mark('hero-first-frame'); const m = performance.getEntriesByName('hero-first-frame')[0];
          console.warn('CD timing ' + JSON.stringify({ firstFrame: Math.round(m.startTime), flags: S.flags || null })); } catch (e) {}
        requestAnimationFrame(() => {
          root.classList.replace('gl-pending', 'gl-on') || root.classList.add('gl-on');
          if (!introDone && state()[0] === 'story' && state()[1] < 0.05) { introDone = true; setTimeout(() => S && S.intro(1200), 650); }
        });
        done(S);
      });
    }).catch(() => { root.classList.remove('gl-pending'); done(null); });
    if (document.readyState === 'complete') idle(go, { timeout: 1500 }); else addEventListener('load', () => idle(go, { timeout: 1500 }), { once: true });
  });
  return loading;
}

function apply() {
  if (reduced()) {                                   // reduce, not remove: станции вместо сцены, смысл на месте
    root.classList.remove('gl-pending', 'gl-on');
    if (S) {                                         // контекст потерян (forceContextLoss) — для возврата к «полному» нужен новый холст
      S.dispose(); S = null; loading = null;
      const fresh = canvas.cloneNode(false); canvas.replaceWith(fresh); canvas = fresh; lastW = lastH = 0;
    }
    return;
  }
  if (!S) { root.classList.add('gl-pending'); boot(); } else { root.classList.add('gl-on'); size(true); update(true); }
}

addEventListener('scroll', () => update(false), { passive: true });
addEventListener('resize', () => { size(false); update(true); }, { passive: true });
addEventListener('pointermove', (e) => {
  if (!S || mqMobile.matches || e.pointerType !== 'mouse') return;
  S.pointer((e.clientX / innerWidth) * 2 - 1, (e.clientY / innerHeight) * 2 - 1);
}, { passive: true });
// v3: на телефоне цель руке ставит касание (не жест прокрутки и не нажатие на ссылку/кнопку); рука тянется туда и замирает
let down = null;
addEventListener('pointerdown', (e) => { if (e.pointerType !== 'mouse') down = [e.clientX, e.clientY, performance.now()]; }, { passive: true });
addEventListener('pointerup', (e) => {
  if (!S || !S.tap || !down || e.pointerType === 'mouse') return;
  const [x0, y0, t0] = down; down = null;
  if (Math.hypot(e.clientX - x0, e.clientY - y0) > 12 || performance.now() - t0 > 600) return;
  if (e.target && e.target.closest && e.target.closest('a, button, input, label, select, textarea, summary, .step')) return;
  S.tap((e.clientX / innerWidth) * 2 - 1, (e.clientY / innerHeight) * 2 - 1);
}, { passive: true });
document.addEventListener('visibilitychange', () => { if (document.hidden && S) S.stop(); });

// кнопка «Меньше движения» (aria-pressed) поверх переключателя motion.js: выбор побеждает ОС в обе стороны, помнится
function bindToggle() {
  if (!window.Motion) { btn.hidden = true; apply(); return; }
  btn.addEventListener('click', () => window.Motion.set(window.Motion.reduced() ? 'full' : 'reduced'));
  window.Motion.on((r) => { btn.setAttribute('aria-pressed', String(r)); apply(); });
}
if (window.Motion) bindToggle(); else addEventListener('DOMContentLoaded', bindToggle, { once: true });

// интерфейс программы: одноразовая сборка при входе в вид (reduce и без JS — конечное состояние в CSS)
const app = document.querySelector('.app');
if (app && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { app.classList.add('is-in'); io.disconnect(); } }),
    { rootMargin: '0px 0px -20% 0px' });
  io.observe(app);
} else if (app) app.classList.add('is-in');

// демо-форма без отправки
document.querySelector('.form').addEventListener('submit', (e) => { e.preventDefault(); e.target.querySelector('.form__done').hidden = false; });
