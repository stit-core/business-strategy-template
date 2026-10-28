// main.js · L2 «Звено» · вариант B — предрендер Blender · Chromium 153
// Страница — копия a-code (разметка, тексты, стили, motion.js, станции), 3D — не WebGL, а секвенции кадров Blender (Cycles), которые
// ведёт прокрутка (как у Apple): Canvas 2D, createImageBitmap, окно памяти (09-web-runtime/06 §1.1 ImageSequence, доработан):
//   • сжатые кадры (AVIF) держатся в памяти как Blob, декодированы — только соседние с текущим (окно 12, телефон 10);
//   • кадр рисуется только при смене номера (0 кадров в покое); номер сглаживается (τ 90 мс), хвост ≤ 0,45 с после ввода;
//   • кадр 0 сюжета = постер hero (тот же рендер) — постер гаснет без «прыжка»;
//   • сцена «внутри» грузится, когда до неё ≤ 1,5 экрана; телефон — свой портретный набор 720×1560.
// Reduce (ОС или кнопка «Меньше движения») — секвенции не грузятся: страница — стопка станций-картинок. Без JS и без createImageBitmap — то же.
const root = document.documentElement;
const canvas = document.querySelector('.stage');
const hero = document.querySelector('[data-section="hero"]');
const modules = document.querySelector('[data-scene="story"]');
const inside = document.querySelector('[data-scene="scan"]');
const btn = document.querySelector('[data-motion-toggle]');
const mqMobile = matchMedia('(max-width: 40rem), (pointer: coarse)');
const clamp = (x) => Math.min(1, Math.max(0, x));
const reduced = () => (window.Motion ? window.Motion.reduced() : matchMedia('(prefers-reduced-motion: reduce)').matches);

// наборы кадров (Blender 5.2.2 Cycles + OIDN, Khronos PBR Neutral): сюжет «модули» = отрезок hero (уход первого экрана, t 0…1:
// кран от камеры постера к камере кода) + сцена (t 1…2: выпрямление, разнос, сборка с кольцом-замком, первое движение); «внутри» —
// скан J3 (t 0…1: срез корпуса и начинки, слои расходятся). Кадр 0 сюжета — постер hero в своём размере.
const SETS = {
  d: { story: { n: 90, hero: 18, dir: 'seq/story-d/' }, scan: { n: 60, dir: 'seq/scan-d/' }, win: 12, posY: 0.4 },
  m: { story: { n: 60, hero: 12, dir: 'seq/story-m/' }, scan: { n: 60, dir: 'seq/scan-m/' }, win: 10, posY: 0.3 },
};
const EXT = '.avif';

class Seq {
  constructor(spec, win) {
    Object.assign(this, spec, { win, blobs: new Map(), bmps: new Map(), jobs: new Map(), want: 0, cur: 0, dirn: 1, dead: false });
  }
  url(i) { return this.dir + 'f' + String(i).padStart(3, '0') + EXT; }
  blob(i) {
    if (this.blobs.has(i)) return Promise.resolve(this.blobs.get(i));
    return fetch(this.url(i)).then((r) => { if (!r.ok) throw new Error(this.url(i) + ' ' + r.status); return r.blob(); })
      .then((b) => { this.blobs.set(i, b); return b; });
  }
  decode(i) {                                                      // один раз на кадр; вне окна к моменту готовности — сразу close()
    if (this.bmps.has(i) || this.jobs.has(i)) return this.jobs.get(i) || Promise.resolve(this.bmps.get(i));
    const p = this.blob(i).then((b) => createImageBitmap(b)).then((bmp) => {
      this.jobs.delete(i);
      if (this.dead || !this.inWin(i)) { bmp.close(); return null; }
      this.bmps.set(i, bmp);
      if (i === this.want || !this.bmps.has(this.want)) paint();
      return bmp;
    }).catch((e) => { this.jobs.delete(i); fail(e); return null; });
    this.jobs.set(i, p);
    return p;
  }
  bounds(i) {
    const ahead = Math.ceil(this.win * 0.75), behind = this.win - ahead;
    return this.dirn > 0 ? [i - behind, i + ahead] : [i - ahead, i + behind];
  }
  inWin(i) { const [lo, hi] = this.bounds(this.cur); return i >= lo && i <= hi; }
  move(i) {
    if (i !== this.cur) this.dirn = Math.sign(i - this.cur);
    this.cur = i; this.want = i;
    const [lo, hi] = this.bounds(i);
    this.decode(i);
    for (let k = Math.max(0, lo); k <= Math.min(this.n - 1, hi); k++) if (k !== i) this.decode(k);
    for (const [k, b] of this.bmps) if (k < lo || k > hi) { b.close(); this.bmps.delete(k); }
  }
  nearest(i) {
    for (let d = 0; d < this.n; d++) { const b = this.bmps.get(i - d) || this.bmps.get(i + d); if (b) return b; }
    return null;
  }
  prefetch(i, count) {                                             // только байты вперёд по ходу прокрутки (без декодирования)
    const out = [];
    for (let d = 1; d <= count; d++) { const k = i + d * this.dirn; if (k >= 0 && k < this.n && !this.blobs.has(k)) out.push(k); }
    return out.reduce((p, k) => p.then(() => (this.dead ? null : this.blob(k).catch(() => null))), Promise.resolve());
  }
  dispose() { this.dead = true; for (const b of this.bmps.values()) b.close(); this.bmps.clear(); this.blobs.clear(); }
}

let ctx = null, set = null, seqs = {}, active = null, phaseNow = null, lastBmp = null, dirty = true, booted = false, failed = false;
let target = 0, curK = 0, raf = 0, lastInput = 0, lastFrame = 0, firstMarked = false;

function state() {                                                 // как у a-code: сюжет — от hero до конца «модулей», скан — «внутри»
  const vh = innerHeight;
  const hr = hero.getBoundingClientRect(), mr = modules.getBoundingClientRect(), ir = inside.getBoundingClientRect();
  if (hr.bottom > 0) return ['story', clamp(-hr.top / hr.height)];
  if (mr.top < vh && mr.bottom > 0) return ['story', 1 + clamp(-mr.top / Math.max(1, mr.height - vh))];
  if (ir.top < vh && ir.bottom > 0) return ['scan', clamp(-ir.top / Math.max(1, ir.height - vh))];
  return [null, 0];
}
function kOf(phase, t) {                                           // дробный номер кадра
  const s = seqs[phase];
  if (phase === 'story') return t <= 1 ? t * (s.hero - 1) : (s.hero - 1) + (t - 1) * (s.n - s.hero);
  return t * (s.n - 1);
}

function size() {
  if (!ctx) return;
  const dpr = Math.min(window.devicePixelRatio || 1, mqMobile.matches ? 1.5 : 2);   // ворота KIT §5: DPR ≤ 1,5 телефон / 2 десктоп
  const w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
  if (w && h && (w !== canvas.width || h !== canvas.height)) { canvas.width = w; canvas.height = h; dirty = true; }
}
function paint() {
  if (!ctx || !active) return;
  const bmp = active.bmps.get(active.want) || active.nearest(active.want);
  if (!bmp || (bmp === lastBmp && !dirty)) return;
  const cw = canvas.width, ch = canvas.height, bw = bmp.width, bh = bmp.height;
  const sc = Math.max(cw / bw, ch / bh), dw = bw * sc, dh = bh * sc;
  ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(bmp, (cw - dw) * 0.5, (ch - dh) * set.posY, dw, dh);   // как object-fit: cover постера (50 % 40 %, телефон 50 % 30 %)
  lastBmp = bmp; dirty = false;
  if (!firstMarked && active === seqs.story) {
    firstMarked = true;
    try { performance.mark('hero-first-frame'); const m = performance.getEntriesByName('hero-first-frame')[0];
      console.warn('Z timing ' + JSON.stringify({ firstFrame: Math.round(m.startTime), set: mqMobile.matches ? 'm' : 'd', engine: 'canvas2d-seq' })); } catch (e) { /* без меток */ }
    requestAnimationFrame(() => { root.classList.replace('gl-pending', 'gl-on') || root.classList.add('gl-on'); });
  }
}

function step(now) {
  raf = 0;
  if (!active) return;
  const dt = Math.min(0.05, Math.max(0.001, (now - (lastFrame || now - 16)) / 1000)); lastFrame = now;
  const since = now - lastInput;
  curK += (target - curK) * (1 - Math.exp(-dt / (since > 280 ? 0.035 : 0.09)));
  if (Math.abs(target - curK) < 0.02 || since > 450) curK = target;   // хвост ≤ 0,45 с (как сцена кода)
  const i = Math.max(0, Math.min(active.n - 1, Math.round(curK)));
  if (i !== active.want || dirty) { active.move(i); paint(); }
  if (curK !== target) raf = requestAnimationFrame(step); else lastFrame = 0;
}
function update(instant) {
  if (!booted || failed) return;
  const [phase, t] = state();
  canvas.classList.toggle('is-hidden', !phase);
  if (!phase) { if (raf) cancelAnimationFrame(raf); raf = 0; return; }
  if (phase === 'scan' && !seqs.scan) return;
  if (phase !== phaseNow) {                                          // смена сцены — без сглаживания
    phaseNow = phase; active = seqs[phase]; target = curK = kOf(phase, t); dirty = true;
    active.move(Math.round(curK)); paint(); return;
  }
  target = kOf(phase, t); lastInput = performance.now();
  if (instant) { curK = target; active.move(Math.round(curK)); paint(); return; }
  if (!raf) raf = requestAnimationFrame(step);
}
function nearInside() { const r = inside.getBoundingClientRect(); return r.top < innerHeight * 2.5 && r.bottom > -innerHeight; }
function ensureScan() {
  if (seqs.scan || !set) return;
  seqs.scan = new Seq(set.scan, set.win);
  seqs.scan.move(0);
}

function fail(e) {
  if (failed) return;
  failed = true;
  console.info('секвенция недоступна — страница остаётся на станциях-картинках', e && e.message);
  root.classList.remove('gl-pending', 'gl-on');
  Object.values(seqs).forEach((s) => s.dispose()); seqs = {}; active = null;
}

function boot() {
  if (booted || failed) return;
  if (!('createImageBitmap' in window) || !canvas.getContext) { fail(new Error('нет createImageBitmap')); return; }
  booted = true;
  ctx = canvas.getContext('2d', { alpha: false });
  window.__zseq = () => Object.fromEntries(Object.entries(seqs).map(([k, s]) =>   // проверка окна памяти (check_b.py)
    [k, { blobs: s.blobs.size, bmps: s.bmps.size, cur: s.cur, win: s.win }]));
  window.__fx = { destroyAll: () => {                               // EG-CODE-01: чистое разрушение (как у a-code)
    Object.values(seqs).forEach((s) => s.dispose()); seqs = {}; active = null; booted = false; phaseNow = null;
    if (raf) cancelAnimationFrame(raf); raf = 0; if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    root.classList.remove('gl-on', 'gl-pending'); } };
  set = SETS[mqMobile.matches ? 'm' : 'd'];
  seqs.story = new Seq(set.story, set.win);
  size();
  const [phase, t] = state();
  phaseNow = phase === 'scan' ? null : 'story'; active = seqs.story;
  target = curK = kOf('story', phase === 'story' ? t : 0);
  active.move(Math.round(curK));
  if (phase === 'scan' || nearInside()) { ensureScan(); update(true); }
  const idle = window.requestIdleCallback || ((f) => setTimeout(f, 300));
  idle(() => { if (seqs.story) seqs.story.prefetch(seqs.story.cur, 24); }, { timeout: 3000 });
}
function start() {
  if (reduced()) return;
  const idle = window.requestIdleCallback || ((f) => setTimeout(f, 200));
  const go = () => idle(boot, { timeout: 1500 });
  if (document.readyState === 'complete') go(); else addEventListener('load', go, { once: true });
}

function apply() {
  if (reduced()) {                                                   // reduce, not remove: станции вместо секвенций, смысл на месте
    root.classList.remove('gl-pending', 'gl-on');
    Object.values(seqs).forEach((s) => s.dispose()); seqs = {}; active = null; booted = false; phaseNow = null; firstMarked = false; lastBmp = null;
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }
  if (!booted) { root.classList.add('gl-pending'); start(); } else { root.classList.add('gl-on'); size(); dirty = true; update(true); }
}

addEventListener('scroll', () => {
  if (!booted) return;
  if (!seqs.scan && nearInside()) ensureScan();
  if (seqs.story && phaseNow === 'story' && !raf) { const s = seqs.story; const idle = window.requestIdleCallback || ((f) => setTimeout(f, 300)); idle(() => s.prefetch(s.cur, 16)); }
  update(false);
}, { passive: true });
addEventListener('resize', () => { size(); dirty = true; update(true); }, { passive: true });

function bindToggle() {
  if (!window.Motion) { btn.hidden = true; apply(); return; }
  btn.addEventListener('click', () => window.Motion.set(window.Motion.reduced() ? 'full' : 'reduced'));
  window.Motion.on((r) => { btn.setAttribute('aria-pressed', String(r)); apply(); });
}
if (window.Motion) bindToggle(); else addEventListener('DOMContentLoaded', bindToggle, { once: true });

// интерфейс программы: одноразовая сборка при входе в вид (reduce и без JS — конечное состояние в CSS) — как у a-code
const app = document.querySelector('.app');
if (app && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { app.classList.add('is-in'); io.disconnect(); } }),
    { rootMargin: '0px 0px -20% 0px' });
  io.observe(app);
} else if (app) app.classList.add('is-in');

// демо-форма без отправки
document.querySelector('.form').addEventListener('submit', (e) => { e.preventDefault(); e.target.querySelector('.form__done').hidden = false; });
