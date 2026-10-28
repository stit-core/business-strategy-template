// adapter_b.js — вариант B: только кадры Blender (Cycles), 0 КБ three. «Докуда доходит предрендер»:
// • набор — кадр «все вверх» + 4 кадра «нажато» (соседи в разных кадрах); нажатие открывает кадр своей группы в обводе
//   клавиши (clip-path по выпуклой оболочке, спроецированной из Blender — cams/T_keys.json) + лёгкая подсветка верха;
// • расцветки — оборот 360° кадрами на каждую расцветку (десктоп 36 × 10°, телефон 24 × 15°), грузится только выбранная
//   и только при подходе к разделу (или по нажатию чипа);
// • разборка — 4 станции по прокрутке; reduce — все станции списком.
import { whenNear, isPhone, logTiming } from './page.js';

const inPoly = (x, y, poly) => {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
};
const area = (poly) => Math.abs(poly.reduce((s, [x, y], i) => { const [x2, y2] = poly[(i + 1) % poly.length]; return s + x * y2 - x2 * y; }, 0) / 2);

export function createAdapterB({ pressFrames = true, turnFrames = true, lazyOnly = false } = {}) {
  // pressFrames — кадры «нажато» (B, C-static); иначе только подсветка верха (A-static: кадров нажатия у кода нет);
  // turnFrames — секвенция 360°; иначе один кадр на расцветку (статичный режим A/C); lazyOnly — запасной слой до 3D
  const T0 = performance.now();
  const nodes = new Map();
  let keymap = null;
  // ---------------------------------------------------------------- набор
  const stT = document.getElementById('stage-type');
  const layer = stT.querySelector('.keylayer');
  whenNear(stT, '900px', async () => {
    const j = await fetch('assets/data/T_keys.json').then((r) => r.json());
    const [W, H] = j.res;
    const pc = (pts) => `polygon(${pts.map(([x, y]) => `${(x / W * 100).toFixed(2)}% ${(y / H * 100).toFixed(2)}%`).join(',')})`;
    const suf = '';                    // телефон: кадр набора показан крупнее экрана (окно левой половины) — полные кадры 1600 px
    const frag = document.createDocumentFragment();
    for (const [id, k] of Object.entries(j.keys)) {
      const d = document.createElement('div');
      d.className = 'k';
      if (pressFrames) {
        d.style.clipPath = pc(k.hull);
        d.style.backgroundImage = `url(assets/img/type/p${k.group}${suf}.avif)`;
      }
      const h = document.createElement('div');
      h.className = id === 'yo' ? 'hl yo' : 'hl';
      h.style.clipPath = pc(k.hull_up);
      frag.append(d, h);
      nodes.set(id, { d, h, k, a: area(k.hull_up) });
    }
    layer.append(frag);
    keymap = { W, H, keys: j.keys };
    // кадры «нажато» — заранее в кэш, чтобы первое нажатие не мигало
    if (pressFrames) for (let g = 0; g < 4; g++) { const im = new Image(); im.decoding = 'async'; im.src = `assets/img/type/p${g}${suf}.avif`; }
    logTiming({ b_type_ready_ms: Math.round(performance.now() - T0) });
  });

  // ---------------------------------------------------------------- оборот по расцветкам
  const stR = document.getElementById('stage-turn');
  const img = stR.querySelector('.st-img');
  const N = !turnFrames ? 1 : isPhone ? 24 : 36, STEP = 360 / Math.max(N, 1);
  const url = (cw, i) => (isPhone ? `assets/img/turn/${cw}/m_${String(i * 15).padStart(3, '0')}.avif`
    : `assets/img/turn/${cw}/d_${String(i * 10).padStart(3, '0')}.avif`);
  const cache = {};
  let cw = 'snow', angle = 0;
  const load = (c) => {
    if (cache[c]) return;
    const t = performance.now();
    cache[c] = Array.from({ length: N }, (_, i) => { const im = new Image(); im.decoding = 'async'; im.src = url(c, i); return im; });
    Promise.all(cache[c].map((im) => im.decode().catch(() => null))).then(() => logTiming({ [`b_turn_${c}_ms`]: Math.round(performance.now() - t) }));
  };
  const show = () => {
    const i = ((Math.round(angle / STEP) % N) + N) % N;
    const src = url(cw, i);
    if (!img.src.endsWith(src)) img.src = src;
  };
  if (isPhone) img.src = url('snow', 0);
  if (turnFrames && !lazyOnly) whenNear(stR, '700px', () => load('snow'));

  // ---------------------------------------------------------------- разборка: станции
  const stX = document.getElementById('stage-x');
  const frames = [...stX.querySelectorAll('.st-frame')];
  let station = 0;

  return {
    press(id, down) {
      const n = nodes.get(id);
      if (!n) return;
      n.d.classList.toggle('on', down);
      n.h.classList.toggle('on', down);
    },
    yo() {},
    hitTest(stage, x, y) {
      if (!keymap) return null;
      const r = (stage.querySelector('.frame') || stage).getBoundingClientRect();   // весь кадр T (на телефоне шире сцены)
      const px = (x - r.left) / r.width * keymap.W, py = (y - r.top) / r.height * keymap.H;
      let best = null;
      for (const [id, n] of nodes) if (inPoly(px, py, n.k.hull_up) && (!best || n.a < best.a)) best = { id, a: n.a };
      return best && best.id;
    },
    setColorway(c) { cw = c; if (turnFrames) load(c); show(); },
    setTurn(a) { if (turnFrames) { angle = a; show(); } },
    setExplode(p) {
      if (p === null) { frames.forEach((f) => f.classList.add('on')); return; }
      const st = Math.max(0, Math.min(3, Math.round(p * 3)));      // станции 0; 0,35; 0,65; 1 — ближайшая к прогрессу
      if (st === station && frames[st].classList.contains('on')) return;
      station = st;
      frames.forEach((f, i) => f.classList.toggle('on', i === st));
    },
    onStage() {},
  };
}
