// page.js — общее поведение страницы «Ё» для A (код), B (кадры Blender), C (гибрид). Отличается только «адаптер» 3D:
// adapter.press(id, down, opts), hitTest(stage, x, y) → id, setColorway(cw), setTurn(deg), setExplode(p), onStage(name, on).
// Ввод: настоящая клавиатура посетителя (event.code → клавиша, event.key → буква в его раскладке RU/EN), мышь и касание по
// клавишам на картинке. Движение — только в ответ на действие (0 кадров в покое); reduce → станции, без закрепления.
import { KEYS, RANGES } from './keys.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
export const reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
export const isTouch = matchMedia('(hover: none) and (pointer: coarse)').matches;
export const isPhone = matchMedia('(max-width: 700px)').matches || isTouch;
const T0 = performance.now();
export const timing = { variant: window.KB_CFG?.variant, phone: isPhone, reduce: reduceMQ.matches };
export function logTiming(extra) {
  Object.assign(timing, extra || {});
  console.warn('KB timing', JSON.stringify(timing));
  window.__kb = timing;
}

const BY_CODE = new Map(KEYS.map((k) => [k.code, k]));
const BY_ID = new Map(KEYS.map((k) => [k.id, k]));

// «когда рядом»: колбэк один раз, когда элемент подошёл ближе margin к экрану
export function whenNear(el, margin, fn) {
  const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); fn(); } }, { rootMargin: margin });
  io.observe(el);
}
export function afterLoadIdle(fn) {
  const go = () => ('requestIdleCallback' in window ? requestIdleCallback(fn, { timeout: 2000 }) : setTimeout(fn, 200));
  if (document.readyState === 'complete') go(); else addEventListener('load', go, { once: true });
}

export function startPage(adapter) {
  const reduce = reduceMQ.matches;
  document.documentElement.classList.toggle('is-reduce', reduce);
  // ---------------------------------------------------------------- постер первого экрана = LCP
  const heroImg = $('.hero__poster img');
  const markHero = () => { performance.mark('hero-first-frame'); logTiming({ hero_poster_ms: Math.round(performance.now() - T0) }); };
  if (heroImg.complete && heroImg.naturalWidth) markHero(); else heroImg.addEventListener('load', markHero, { once: true });

  // ---------------------------------------------------------------- набор
  const typedEl = $('#typed-text'), yoNote = $('#yo-note'), layoutEl = $('#layout');
  const langBtn = $('#lang'), shiftBtn = $('#shift');
  let text = [], lang = 'ru', shift = false, typeVisible = false;
  const held = new Map();
  const esc = (c) => (c === '<' ? '&lt;' : c === '>' ? '&gt;' : c === '&' ? '&amp;' : c);
  const draw = () => {
    text = text.slice(-64);
    typedEl.innerHTML = text.map((c) => (c === 'ё' || c === 'Ё' ? `<span class="yo">${c}</span>` : esc(c))).join('');
  };
  const note = (html) => { yoNote.innerHTML = html; };
  const detect = (c) => {
    if (/[а-яё]/i.test(c)) layoutEl.textContent = 'Раскладка: RU';
    else if (/[a-z]/i.test(c)) layoutEl.textContent = 'Раскладка: EN';
  };
  const addChar = (c, k) => {
    text.push(c); draw(); detect(c);
    if (c === 'ё' || c === 'Ё') {
      note('<b>Ё</b> набрана одной клавишей&nbsp;— без Fn и&nbsp;без поиска по&nbsp;раскладке.');
      adapter.yo?.();
    } else if (k && k.id === 'yo') {
      note('В&nbsp;английской раскладке здесь&nbsp;«`», в&nbsp;русской&nbsp;— <b>Ё</b>. Esc&nbsp;— это Fn&nbsp;+&nbsp;Ё.');
    }
  };
  const act = (k) => {
    if (k.id === 'bksp') { text.pop(); draw(); return; }
    if (k.id === 'enter') { text = []; draw(); note(''); return; }
  };
  const ioType = new IntersectionObserver((es) => { for (const e of es) typeVisible = e.isIntersecting; }, { threshold: 0.25 });
  ioType.observe($('#type'));
  addEventListener('keydown', (e) => {
    if (!typeVisible || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.target.closest?.('input, textarea, select, [contenteditable]')) return;
    const k = BY_CODE.get(e.code);
    if (!k) return;
    const ae = document.activeElement;
    const onControl = ae && ae !== document.body && ae.matches('button, a, [role="radio"], [tabindex]');
    if (onControl && (e.code === 'Space' || e.code === 'Enter' || e.code === 'NumpadEnter' || e.code.startsWith('Arrow'))) return;
    const passThrough = e.code === 'Tab' || e.code === 'Escape';
    if (!passThrough) e.preventDefault();
    if (!e.repeat) { adapter.press(k.id, true); held.set(e.code, k.id); }
    if (passThrough) return;
    if (e.key && e.key.length === 1) addChar(e.key, k);
    else act(k);
  });
  addEventListener('keyup', (e) => { const id = held.get(e.code); if (id) { adapter.press(id, false); held.delete(e.code); } });
  addEventListener('blur', () => { for (const id of held.values()) adapter.press(id, false); held.clear(); });
  // касание и мышь по клавишам на картинке
  const stageType = $('#stage-type');
  const touchChar = (k) => {
    if (k.id === 'space') return ' ';
    if (k.role === 'mod') return null;
    if (k.id === 'yo') return lang === 'ru' ? (shift ? 'Ё' : 'ё') : '`';
    let c = lang === 'ru' ? k.l1 : (k.l2 || k.l1);
    if (!c) return null;
    if (c === '−') c = '-';
    if (k.row === 0 && shift && k.l2) c = lang === 'ru' && k.l3 ? k.l3 : k.l2;
    return shift ? c.toUpperCase() : c.toLowerCase();
  };
  const ptrKeys = new Map();
  const commit = (k) => {
    if (k.id === 'lshift' || k.id === 'rshift') { shift = !shift; shiftBtn.setAttribute('aria-pressed', String(shift)); return; }
    const c = touchChar(k);
    if (c) { addChar(c, k); if (shift) { shift = false; shiftBtn.setAttribute('aria-pressed', 'false'); } } else act(k);
  };
  // мышь — буква сразу; касание — клавиша вниз сразу, буква на отпускании (на телефоне сцена листается вбок: свайп не печатает)
  stageType.addEventListener('pointerdown', (e) => {
    const id = adapter.hitTest?.(stageType, e.clientX, e.clientY);
    if (!id) return;
    const mouse = e.pointerType === 'mouse';
    if (mouse) e.preventDefault();
    adapter.press(id, true);
    ptrKeys.set(e.pointerId, { id, x: e.clientX, y: e.clientY, mouse });
    if (mouse) commit(BY_ID.get(id));
  });
  const up = (e, ok) => {
    const p = ptrKeys.get(e.pointerId);
    if (!p) return;
    adapter.press(p.id, false); ptrKeys.delete(e.pointerId);
    if (ok && !p.mouse && Math.hypot(e.clientX - p.x, e.clientY - p.y) < 14) commit(BY_ID.get(p.id));
  };
  stageType.addEventListener('pointerup', (e) => up(e, true));
  stageType.addEventListener('pointercancel', (e) => up(e, false));
  stageType.addEventListener('pointerleave', (e) => up(e, false));
  // телефон: половины раскладки — кнопка и прокрутка сцены (прилипание к краям)
  const halfBtn = $('#half');
  const syncHalf = () => {
    const max = stageType.scrollWidth - stageType.clientWidth;
    const right = max > 0 && stageType.scrollLeft > max / 2;
    halfBtn.innerHTML = right ? '←&nbsp;Левая половина' : 'Правая половина&nbsp;→';
  };
  halfBtn.addEventListener('click', () => {
    const max = stageType.scrollWidth - stageType.clientWidth;
    stageType.scrollTo({ left: stageType.scrollLeft > max / 2 ? 0 : max, behavior: reduceMQ.matches ? 'auto' : 'smooth' });
  });
  stageType.addEventListener('scroll', () => { requestAnimationFrame(syncHalf); }, { passive: true });
  langBtn.addEventListener('click', () => {
    lang = lang === 'ru' ? 'en' : 'ru';
    langBtn.textContent = `Касание печатает: ${lang.toUpperCase()}`;
    langBtn.setAttribute('aria-pressed', String(lang === 'en'));
  });
  shiftBtn.addEventListener('click', () => { shift = !shift; shiftBtn.setAttribute('aria-pressed', String(shift)); });
  $('#clear').addEventListener('click', () => { text = []; draw(); note(''); });

  // ---------------------------------------------------------------- расцветки
  const colors = $('#colors'), stageTurn = $('#stage-turn');
  const chips = $$('.chips [role="radio"]');
  const NAMES = { snow: 'Снег', graphite: 'Графит', linen: 'Лён' };
  const setCw = (cw, focus) => {
    colors.dataset.cw = cw;
    for (const c of chips) {
      const on = c.dataset.cw === cw;
      c.setAttribute('aria-checked', String(on)); c.tabIndex = on ? 0 : -1;
      if (on && focus) c.focus();
    }
    stageTurn.setAttribute('aria-label', `Клавиатура в расцветке «${NAMES[cw]}». Потяните или нажмите стрелки, чтобы повернуть.`);
    adapter.setColorway(cw);
  };
  chips.forEach((c, i) => {
    c.tabIndex = i === 0 ? 0 : -1;
    c.addEventListener('click', () => setCw(c.dataset.cw));
    c.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      const j = (i + (e.key === 'ArrowRight' ? 1 : chips.length - 1)) % chips.length;
      setCw(chips[j].dataset.cw, true);
    });
  });
  // поворот: перетаскивание, кнопки, стрелки в фокусе
  let angle = 0, drag = null;
  const turnTo = (a, smooth) => { angle = a; adapter.setTurn(angle, smooth); };
  stageTurn.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, a: angle, id: e.pointerId }; stageTurn.setPointerCapture(e.pointerId); });
  stageTurn.addEventListener('pointermove', (e) => {
    if (!drag || e.pointerId !== drag.id) return;
    const w = stageTurn.clientWidth || 1;
    turnTo(drag.a + (e.clientX - drag.x) / w * 300, false);
  });
  const endDrag = (e) => { if (drag && e.pointerId === drag.id) drag = null; };
  stageTurn.addEventListener('pointerup', endDrag);
  stageTurn.addEventListener('pointercancel', endDrag);
  $$('[data-turn]').forEach((b) => b.addEventListener('click', () => turnTo(Math.round((angle + 30 * +b.dataset.turn) / 30) * 30, true)));
  stageTurn.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); turnTo(angle + (e.key === 'ArrowRight' ? 15 : -15), true); }
  });

  // ---------------------------------------------------------------- разборка: одна сцена ≤ 150vh
  const inside = $('#inside'), stageX = $('#stage-x');
  const layerLis = $$('#layers li');
  const lit = (p) => {
    let cur = 'keycaps';
    for (const [L, [a]] of Object.entries(RANGES)) if (L !== 'case_top' && p >= a + 0.02) cur = L === 'stabs' ? 'switches' : L;
    if (p >= 0.95) cur = 'case';
    for (const li of layerLis) li.classList.toggle('on', li.dataset.layer === cur);
  };
  if (reduce) {
    stageX.classList.add('stations');
    adapter.setExplode(null);
  } else {
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        ticking = false;
        const r = inside.getBoundingClientRect();
        const span = Math.max(1, r.height - innerHeight);
        const p = Math.min(1, Math.max(0, -r.top / span));
        adapter.setExplode(p);
        lit(p);
      });
    };
    addEventListener('scroll', onScroll, { passive: true });
    addEventListener('resize', onScroll, { passive: true });
    onScroll();
  }

  // ---------------------------------------------------------------- видимость сцен (адаптер решает, куда ставить canvas)
  const ioStage = new IntersectionObserver((es) => {
    for (const e of es) adapter.onStage?.(e.target.dataset.stage, e.isIntersecting, e.intersectionRatio);
  }, { threshold: [0, 0.15, 0.35, 0.6, 0.9] });
  for (const s of $$('[data-stage]')) ioStage.observe(s);

  // ---------------------------------------------------------------- призыв
  const nb = $('#notify'), nm = $('#notify-msg');
  nb.addEventListener('click', () => { const open = nm.hidden; nm.hidden = !open; nb.setAttribute('aria-expanded', String(open)); });
  return { setCw, BY_ID };
}
