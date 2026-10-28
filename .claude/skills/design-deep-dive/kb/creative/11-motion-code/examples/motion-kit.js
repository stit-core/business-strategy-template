/* motion-kit.js — движение страницы своим кодом: появления, разбиение текста, счётчики, петли, эффекты прокрутки,
   DOM-сцены прокрутки с пружиной рантайма 3D, указатель, микродвижение, переходы и переключатель движения.
   Без библиотек и сети. Набор не создаёт, не переносит и не переписывает узлы DOM: он ставит атрибуты, классы и
   CSS-переменные на существующие элементы; облик, начальные и конечные состояния — motion-kit.css. Классический
   скрипт с одним глобальным именем MotionKit: годится файлом поддержки холста Claude Design (project/lib/motion-kit.js)
   и модулем острова сайта.

   Подключение:
     <link rel="stylesheet" href="motion-kit.css">
     <script src="motion-kit.js" data-motion-toggle></script>
     <script>var mk = MotionKit.mount(document, { remember: 'local', level: 'L1' });</script>
   mount(root, opts) → { destroy, pause, resume, refresh, info, transition }.

   Разметка — data-mk="<примитив> …" (словарь — ../01-kit.md §3, ../primitives.yaml). Набор ставит: корню
   data-mk-on="full | reduced | still"; элементу появления data-mk-in ("" — с движением, "instant" — сразу);
   счётчику --mk-to, --mk-dec, --mk-group, data-mk-fmt, data-mk-done; петле --mk-period и data-mk-idle (вне экрана);
   сцене --mk-p, --mk-len, data-beat, подписям data-on и --mk-fill; указателю --mk-mx/--mk-my, --mk-rx/--mk-ry,
   --mk-x/--mk-y; носителю выбора (по умолчанию <html>) — data-motion: нет — как в системе, reduced, full, paused. */
(function () {
  'use strict';
  var VERSION = '0.5.0';
  var D = {
    level: 'L1',                          // уровень страницы: бюджет внимания — петель в окне 1 / 2 / 3 (телефон — на 1 меньше)
    remember: 'session',                  // где помнить выбор движения: 'local' (L2), 'session', false
    key: 'motion',                        // ключ хранилища — как у острова предпочтений кода сайта
    toggle: true,                         // обслуживать кнопки [data-motion-set] и [data-mk~="pause"]; на сайте их ведёт остров — false
    host: null,                           // носитель data-motion; по умолчанию <html>, на холсте — корень артборда
    scroller: null,                       // контейнер прокрутки; по умолчанию — ближайший прокручиваемый (на холсте — внутреннее окно)
    header: null,                         // высота липкой шапки, px; по умолчанию — CSS-переменная --mk-header
    isLive: null,                         // () => bool: показан ли документ вживую (обзор холста — нет); по умолчанию — да
    phone: '(max-width: 40rem), (pointer: coarse)',
    fine: '(hover: hover) and (pointer: fine)',
    onState: null                         // (info) => void — строка состояния адаптера холста
  };
  var REVEAL = { rise: 1, unmask: 1, split: 1, sweep: 1, 'scale-in': 1, count: 1, draw: 1 };
  var KNOWN = ('entrance rise unmask split sweep scale-in count draw progress parallax scroll-draw highlight scroll-mask ' +
    'frame-expand text-mask stack horizontal header text-path scene marquee drift magnet tilt spotlight dialog accordion ' +
    'button-label flip shine columns state page-transition toggle pause').split(' ');
  var BUDGET = { L0: 1, L1: 2, L2: 3 };
  var EPS = 4e-4;                         // стоп пружины: |x − цель| < EPS и |v| < 4·EPS (02-stage-runtime.md §4)

  function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
  function num(v, d) { var x = parseFloat(v); return isFinite(x) ? x : d; }
  function list(v) { return String(v || '').split(',').map(function (x) { return x.trim(); }).filter(Boolean); }
  function words(el) { return String(el.getAttribute('data-mk') || '').split(/\s+/).filter(Boolean); }
  function has(el, w) { return words(el).indexOf(w) >= 0; }
  function arr(x) { return Array.prototype.slice.call(x || []); }
  function mq(q) { return window.matchMedia ? window.matchMedia(q) : { matches: false }; }
  function listen(m, fn) { if (m.addEventListener) { m.addEventListener('change', fn); } else if (m.addListener) { m.addListener(fn); } }
  function unlisten(m, fn) { if (m.removeEventListener) { m.removeEventListener('change', fn); } else if (m.removeListener) { m.removeListener(fn); } }
  function store(kind) { try { return kind === 'local' ? window.localStorage : (kind === 'session' ? window.sessionStorage : null); } catch (e) { return null; } }
  function sda() { try { return !!(window.CSS && CSS.supports('(animation-timeline: scroll()) and (animation-range: 0% 100%)')); } catch (e) { return false; } }

  // Пружина рантайма сцен 3D — дословно kb/3d/16-js-scenes/02-stage-runtime.md §4: критически демпфированная, точное
  // решение за шаг dt — без рывка и без перелёта, устойчива на любой частоте экрана; 95 % пути — за 4,74/ω с.
  function spring(x, v, target, w, dt) {
    var d = x - target, e = Math.exp(-w * dt), c = v + w * d;
    return [target + (d + c * dt) * e, (v - w * c * dt) * e];
  }
  // Сглаживание указателя по времени (creative 05/03 §4.5): одинаково на 60 и 144 Гц.
  function damp(x, y, lambda, dt) { return x + (y - x) * (1 - Math.exp(-lambda * dt)); }

  // «Вживую» (Play холста) — эвристика рантайма 3D (02-stage-runtime.md §10): окно не выше 1700 px и страница или окно-предок
  // прокручивается дальше окна на 40 px. Холст режим не сообщает.
  function viewMode(root) {
    var vh = window.innerHeight || 0, doc = document.scrollingElement || document.documentElement, el = root;
    if (vh > 1700) { return false; }
    if (doc.scrollHeight > vh + 40) { return true; }
    for (; el && el.nodeType === 1 && el !== document.body; el = el.parentElement) {
      var oy = getComputedStyle(el).overflowY;
      if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight + 40) { return true; }
    }
    return false;
  }
  // Ближайший прокручиваемый контейнер: на холсте прокрутка идёт во внутреннем окне, а не у документа; null — документ.
  function scrollerOf(el) {
    for (var n = el; n && n.nodeType === 1 && n !== document.body && n !== document.documentElement; n = n.parentElement) {
      var oy = getComputedStyle(n).overflowY;
      if ((oy === 'auto' || oy === 'scroll' || oy === 'overlay') && n.scrollHeight > n.clientHeight + 1) { return n; }
    }
    return null;
  }

  function Kit(root, opts) {
    var k;
    this.o = {};
    for (k in D) { if (Object.prototype.hasOwnProperty.call(D, k)) { this.o[k] = D[k]; } }
    for (k in (opts || {})) { if (Object.prototype.hasOwnProperty.call(opts, k)) { this.o[k] = opts[k]; } }
    this.doc = root && root.nodeType === 9 ? root : document;
    this.root = root && root.nodeType === 1 ? root : this.doc.documentElement;
    this.host = this.o.host || this.doc.documentElement;
  }
  var P = Kit.prototype;

  // ---------- запись атрибутов и переменных: всё, что ставит набор, снимает destroy ----------
  P.mark = function (el) { if (!el.__mk) { el.__mk = { a: {}, v: {} }; this.touched.push(el); } return el.__mk; };
  P.attr = function (el, name, val) {
    var m = this.mark(el);
    if (!(name in m.a)) { m.a[name] = el.hasAttribute(name) ? el.getAttribute(name) : null; }
    if (val === null || val === undefined) { if (el.hasAttribute(name)) { el.removeAttribute(name); } }
    else if (el.getAttribute(name) !== String(val)) { el.setAttribute(name, String(val)); }
  };
  P.css = function (el, name, val) {
    var m = this.mark(el);
    m.v[name] = 1;
    if (val === null || val === undefined) { el.style.removeProperty(name); }
    else if (el.style.getPropertyValue(name) !== String(val)) { el.style.setProperty(name, String(val)); }
  };
  P.warn = function (msg) {
    if (this.warns.indexOf(msg) >= 0) { return; }
    this.warns.push(msg);
    try { console.warn('MotionKit: ' + msg); } catch (e) { /* консоли нет */ }
  };

  P.mount = function () {
    var self = this;
    this.alive = true;
    this.touched = []; this.warns = [];
    this.groups = new Map(); this.loops = []; this.paths = []; this.scenes = []; this.ptr = []; this.headers = [];
    this.counts = {}; this.mode = null; this.paused = false; this.raf = 0; this.prafId = 0; this.tick = false;
    this.mqR = mq('(prefers-reduced-motion: reduce)'); this.mqP = mq(this.o.phone); this.mqF = mq(this.o.fine);
    this.sda = sda();
    this.sc = this.o.scroller || scrollerOf(this.root);
    this.lastY = this.scrollY(); this.lastT = 0; this.vel = 0;
    this.restore();
    this.ioR = new IntersectionObserver(function (es) { es.forEach(function (e) { self.onReveal(e); }); },
      { rootMargin: '0px 0px -4% 0px', threshold: 0.01 });          // зона без обрезки снизу: появление и у дна (06/01 §4.2)
    this.ioV = new IntersectionObserver(function (es) { es.forEach(function (e) { self.onVisible(e); }); self.budget(); },
      { threshold: 0 });
    this.mo = new MutationObserver(function () { self.syncChoice(); self.apply(); });
    this.mo.observe(this.host, { attributes: true, attributeFilter: ['data-motion'] });
    this.onScroll = function () {
      if (self.tick) { return; }
      self.tick = true;
      requestAnimationFrame(function () { self.tick = false; self.frame(); });
    };
    this.onResize = function () { self.layout(); self.frame(); };
    this.onMedia = function () { self.apply(); };
    this.onClick = function (e) { self.click(e); };
    this.onMove = function (e) { self.pmove(e); };
    this.onOut = function (e) { if (!e.relatedTarget) { self.pin = false; self.kickPtr(); } };
    this.doc.addEventListener('scroll', this.onScroll, { passive: true, capture: true });   // и прокрутка внутренних окон
    window.addEventListener('resize', this.onResize);
    [this.mqR, this.mqP, this.mqF].forEach(function (m) { listen(m, self.onMedia); });
    this.doc.addEventListener('click', this.onClick);
    this.doc.addEventListener('pointermove', this.onMove, { passive: true });
    this.doc.addEventListener('pointerout', this.onOut, { passive: true });
    this.scan();
    this.apply();
    if (this.doc.fonts && this.doc.fonts.ready) { this.doc.fonts.ready.then(function () { if (self.alive) { self.layout(); } }); }
    return this;
  };

  // ---------- выбор движения: data-motion на носителе, хранилище, кнопки ----------
  P.restore = function () {
    var st = store(this.o.remember), v = null, ss = store('session'), pz = null;
    if (st) { try { v = st.getItem(this.o.key); } catch (e) { v = null; } }
    if ((v === 'reduced' || v === 'full') && !this.host.hasAttribute('data-motion')) { this.host.setAttribute('data-motion', v); }
    this.syncChoice();
    if (ss) { try { pz = ss.getItem(this.o.key + '-paused'); } catch (e) { pz = null; } }
    if (pz === '1') { this.setPaused(true, true); }
  };
  P.syncChoice = function () {
    var v = this.host.getAttribute('data-motion');
    if (v !== 'paused') { this.prev = v === 'reduced' || v === 'full' ? v : ''; }
  };
  P.choice = function () { return this.prev || ''; };
  P.save = function () {
    var st = store(this.o.remember), ss = store('session'), v = this.choice();
    try { if (st) { if (v) { st.setItem(this.o.key, v); } else { st.removeItem(this.o.key); } } } catch (e) { /* хранилище закрыто */ }
    try { if (ss) { if (this.paused) { ss.setItem(this.o.key + '-paused', '1'); } else { ss.removeItem(this.o.key + '-paused'); } } } catch (e) { /* хранилище закрыто */ }
  };
  P.choose = function (v) {
    this.prev = v === 'reduced' || v === 'full' ? v : '';
    if (this.prev) { this.host.setAttribute('data-motion', this.prev); } else { this.host.removeAttribute('data-motion'); }
    this.paused = false;
    this.save(); this.apply();
  };
  P.setPaused = function (on, quiet) {
    var cur = this.host.getAttribute('data-motion');
    if (on && cur !== 'paused') { this.syncChoice(); this.host.setAttribute('data-motion', 'paused'); }
    if (!on && cur === 'paused') { if (this.prev) { this.host.setAttribute('data-motion', this.prev); } else { this.host.removeAttribute('data-motion'); } }
    this.paused = !!on;
    if (!quiet) { this.save(); this.apply(); }
  };
  P.isReduced = function () {
    var v = this.host.getAttribute('data-motion');
    if (v === 'paused') { v = this.prev; }
    if (v === 'reduced') { return true; }
    if (v === 'full') { return false; }
    return !!this.mqR.matches;
  };
  P.modeNow = function () {
    var live = this.o.isLive ? !!this.o.isLive() : true;
    return !live ? 'still' : (this.isReduced() ? 'reduced' : 'full');
  };

  // Режим целиком: в full до смены атрибута всё видимое и пройденное встаёт в конечное состояние — без мелькания.
  P.apply = function () {
    if (!this.alive) { return; }
    var m = this.modeNow(), was = this.mode;
    this.paused = this.host.getAttribute('data-motion') === 'paused';
    this.phone = !!this.mqP.matches; this.fine = !!this.mqF.matches;
    if (m === 'full' && was !== 'full') { this.premark(); }
    this.mode = m;
    if (m !== was) { this.scenes.forEach(function (s) { s.snap = true; }); }     // refresh() холста доигрыш не обрывает
    this.layout();
    this.frame();
    this.attr(this.root, 'data-mk-on', m);
    if (m !== 'full') { this.scenesStatic(); }
    this.syncButtons();
    this.syncPaths();
    this.ptrSync();
    this.budget();
    this.notify();
  };
  P.syncButtons = function () {
    var self = this, c = this.choice();
    if (!this.o.toggle) { return; }
    arr(this.doc.querySelectorAll('[data-motion-set]')).forEach(function (b) {
      self.attr(b, 'aria-pressed', (b.getAttribute('data-motion-set') || '') === c ? 'true' : 'false');
    });
    arr(this.doc.querySelectorAll('[data-mk~="pause"]')).forEach(function (b) { self.attr(b, 'aria-pressed', self.paused ? 'true' : 'false'); });
  };

  // ---------- разметка: поиск примитивов и привязка ----------
  P.scan = function () {
    var self = this, els = arr(this.root.querySelectorAll('[data-mk]'));
    if (this.root.hasAttribute('data-mk')) { els.unshift(this.root); }
    els.forEach(function (el) { if (!el.__mkW) { el.__mkW = 1; self.wire(el); } });
  };
  P.wire = function (el) {
    var self = this, w = words(el);
    w.forEach(function (x) {
      if (KNOWN.indexOf(x) < 0) { self.warn('неизвестный примитив data-mk="' + x + '"'); }
      self.counts[x] = (self.counts[x] || 0) + 1;
    });
    if (w.some(function (x) { return REVEAL[x]; })) { this.addReveal(el); }
    if (has(el, 'count')) { this.wireCount(el); }
    if (has(el, 'marquee') || has(el, 'drift')) {
      this.loops.push({ el: el, kind: has(el, 'marquee') ? 'marquee' : 'drift', vis: false, rate: 1, boost: num(el.getAttribute('data-mk-boost'), 0) });
      this.ioV.observe(el);
      if (has(el, 'marquee') && !el.querySelector('[data-mk-track]')) { this.warn('бегущая строка без [data-mk-track]'); }
    }
    if (has(el, 'parallax') && el.hasAttribute('data-mk-depth')) { this.css(el, '--mk-depth', String(num(el.getAttribute('data-mk-depth'), 0.2))); }
    if (has(el, 'text-path')) {
      this.paths.push({ el: el, from: el.getAttribute('data-mk-from') || '0%', to: el.getAttribute('data-mk-to') || '40%', vis: false,
        box: el.ownerSVGElement || el.closest('svg') || el });
      this.ioV.observe(el.ownerSVGElement || el.closest('svg') || el);
    }
    if (has(el, 'scene')) { this.scenes.push(this.readScene(el)); }
    if (has(el, 'horizontal')) {
      var n = el.querySelectorAll('[data-mk-track] > *').length;
      this.css(el, '--mk-panels', String(Math.max(1, n)));
      if (n > 5) { this.warn('горизонталь: панелей ' + n + ' > 5 (creative 05/02 §5)'); }
    }
    if (has(el, 'header')) { this.headers.push(el); }
    ['magnet', 'tilt', 'spotlight'].forEach(function (k) {
      if (has(el, k)) { self.ptr.push({ el: el, kind: k, x: 0, y: 0, tx: 0, ty: 0, a: 0, ta: 0, label: el.querySelector('[data-mk-label]'), on: false }); }
    });
    if (has(el, 'page-transition') && getComputedStyle(el).viewTransitionName === 'none') {
      this.warn('page-transition без view-transition-name у ' + el.tagName.toLowerCase());
    }
  };

  // ---------- появление: один раз, по IO; группа [data-mk-stagger] — один триггер на всех ----------
  P.addReveal = function (el) {
    var g = el.parentElement && el.parentElement.closest('[data-mk-stagger]');
    var key = g && this.root.contains(g) ? g : el;
    var rec = this.groups.get(key);
    if (!rec) { rec = { el: key, items: [], done: false }; this.groups.set(key, rec); this.ioR.observe(key); }
    rec.items.push(el);
  };
  P.onReveal = function (e) {
    var rec = this.groups.get(e.target);
    if (!rec || rec.done || this.mode !== 'full') { return; }
    if (e.isIntersecting) { this.show(rec, false); }
    else if (e.boundingClientRect.bottom <= (e.rootBounds ? e.rootBounds.top : 0)) { this.show(rec, true); }   // пролетели — сразу
  };
  P.show = function (rec, instant) {
    var self = this;
    rec.done = true;
    this.ioR.unobserve(rec.el);
    rec.items.forEach(function (el) {
      self.attr(el, 'data-mk-in', instant ? 'instant' : '');
      if (has(el, 'count')) { self.countEnd(el, instant); }
    });
  };
  P.premark = function () {
    var self = this, v = this.view();
    this.groups.forEach(function (rec) {
      if (rec.done) { return; }
      var r = rec.el.getBoundingClientRect();
      if ((r.top < v.top + v.h && r.bottom > v.top) || r.bottom <= v.top) { self.show(rec, true); }
    });
  };
  // Проверка по коробке в кадре прокрутки — основной триггер: IO в Chromium учитывает clip-path самой цели (маска и
  // шторка скрыты обрезкой — пересечения нет) и не сообщает о том, что пролетели прыжком (якорь, «Пропустить»).
  // Сначала чтения, потом записи: кадр без принудительной раскладки.
  P.revealScan = function (v) {
    var self = this, hit = [];
    this.groups.forEach(function (rec) {
      if (rec.done) { return; }
      var r = rec.el.getBoundingClientRect();
      if (!r.width && !r.height) { return; }                                   // display: none — не трогаем
      if (r.bottom <= v.top) { hit.push([rec, true]); }                        // пролетели — сразу
      else if (r.top < v.top + v.h * 0.96 && r.bottom > v.top) { hit.push([rec, false]); }   // зона: окно без нижних 4 %
    });
    hit.forEach(function (x) { self.show(x[0], x[1]); });
  };
  // Добор у дна: что в окне на последних 4 px прокрутки, появляется, даже если IO не сработал (06/01 §4.2).
  P.atEnd = function (v) {
    var self = this, s = this.sc || this.doc.scrollingElement || this.doc.documentElement;
    if (s.scrollTop + s.clientHeight < s.scrollHeight - 4) { return; }
    this.groups.forEach(function (rec) { if (!rec.done && rec.el.getBoundingClientRect().top < v.top + v.h) { self.show(rec, false); } });
  };

  // ---------- счётчик: число в HTML; набор ставит только переменные — цифры рисует CSS-счётчик (motion-kit.css §5) ----------
  P.wireCount = function (el) {
    var t = String(el.textContent || '').replace(/[\s   ]+/g, ' ').trim();
    var m = t.match(/^(\d{1,3}(?: \d{3})+|\d+)(?:[,.](\d{1,2}))?$/);
    if (!m) { this.warn('счётчик без числа: «' + t.slice(0, 24) + '»'); return; }
    var ip = m[1].replace(/ /g, ''), fp = m[2] || '';
    if (ip.length > 6) { this.warn('счётчик: целая часть больше 999 999 — ' + t); return; }
    this.css(el, '--mk-to', String(parseInt(ip + fp, 10)));
    this.css(el, '--mk-dec', String(fp.length));
    this.css(el, '--mk-group', / /.test(m[1]) ? '1' : '0');
    this.attr(el, 'data-mk-fmt', 'd' + fp.length);
  };
  P.countEnd = function (el, instant) {
    var self = this, done = function () { if (self.alive && el.isConnected) { self.attr(el, 'data-mk-done', ''); } };
    if (instant) { done(); return; }
    var fn = function (e) { if (e.target === el && e.propertyName === '--mk-num') { el.removeEventListener('transitionend', fn); done(); } };
    el.addEventListener('transitionend', fn);
    setTimeout(function () { el.removeEventListener('transitionend', fn); done(); }, 1700);   // ≤ 1,5 с + запас
  };

  // ---------- петли: бегущая строка и дыхание; вне экрана стоят, пауза — общая ----------
  P.onVisible = function (e) {
    var t = e.target, i;
    for (i = 0; i < this.loops.length; i++) {
      if (this.loops[i].el === t) { this.loops[i].vis = e.isIntersecting; this.attr(t, 'data-mk-idle', e.isIntersecting ? null : ''); }
    }
    for (i = 0; i < this.paths.length; i++) { if (this.paths[i].box === t) { this.paths[i].vis = e.isIntersecting; } }
    for (i = 0; i < this.scenes.length; i++) { if (this.scenes[i].el === t) { this.scenes[i].vis = e.isIntersecting; } }
    if (e.isIntersecting) { this.frame(); }
  };
  P.measure = function () {
    var self = this;
    this.loops.forEach(function (L) {
      if (L.kind !== 'marquee') { return; }
      var tr = L.el.querySelector('[data-mk-track]'), w = tr ? tr.getBoundingClientRect().width : 0;
      if (!w) { return; }
      var sp = num(L.el.getAttribute('data-mk-speed'), num(getComputedStyle(L.el).getPropertyValue('--mk-marquee-speed'), 40));
      var c = Math.max(30, Math.min(60, sp));
      if (c !== sp) { self.warn('скорость бегущей строки ' + sp + ' px/с вне 30–60 (effects.yaml, marquee-logos)'); }
      L.speed = c;
      self.css(L.el, '--mk-period', (w / c).toFixed(2) + 's');     // период = ширина дорожки / скорость
    });
  };
  // Ускорение строки от скорости прокрутки (marquee-text): вход ≤ 900 px/с, k = data-mk-boost, затухание λ 4.
  P.boost = function (dt) {
    var self = this, busy = false;
    this.loops.forEach(function (L) {
      if (!L.boost || L.kind !== 'marquee') { return; }
      var goal = self.mode === 'full' && !self.paused && L.vis ? 1 + L.boost * Math.min(900, Math.abs(self.vel)) / (L.speed || 40) : 1;
      L.rate = damp(L.rate, goal, 4, dt);
      if (Math.abs(L.rate - goal) > 0.01) { busy = true; } else { L.rate = goal; }
      arr(L.el.querySelectorAll('[data-mk-track]')).forEach(function (tr) {
        (tr.getAnimations ? tr.getAnimations() : []).forEach(function (a) { a.playbackRate = L.rate; });
      });
    });
    return busy;
  };
  P.budget = function () {
    var on = this.mode === 'full' && !this.paused, n = 0, b;
    if (!on) { this.inView = 0; return; }
    var seen = [];                                                        // объекты, а не пятна (05/01 §5.1): слои дыхания
    this.loops.forEach(function (L) {                                     // одного родителя — одна композиция
      var key = L.kind === 'drift' ? L.el.parentElement : L.el;
      if (L.vis && seen.indexOf(key) < 0) { seen.push(key); n += 1; }
    });
    this.scenes.forEach(function (s) { if (s.mode === 'play' && s.vis && s.playing) { n += 1; } });
    this.inView = n;
    b = Math.max(1, (BUDGET[this.o.level] || 2) - (this.phone ? 1 : 0));
    if (n > b) { this.warn('петель в окне ' + n + ' > ' + b + ' для ' + this.o.level + (this.phone ? ' на телефоне' : '') + ' (creative 05/01 §5.2)'); }
  };

  // ---------- геометрия окна прокрутки ----------
  P.scrollY = function () { var s = this.sc || document.scrollingElement || document.documentElement; return s.scrollTop; };
  P.view = function () {
    if (!this.sc) { return { top: 0, h: window.innerHeight || 800 }; }
    var r = this.sc.getBoundingClientRect();
    return { top: r.top + this.sc.clientTop, h: this.sc.clientHeight };
  };
  P.headerPx = function () {
    if (typeof this.o.header === 'function') { return num(this.o.header(), 0); }
    if (this.o.header !== null && this.o.header !== undefined) { return num(this.o.header, 0); }
    return num(getComputedStyle(this.root).getPropertyValue('--mk-header'), 0);
  };
  P.layout = function () {
    var self = this, v = this.view();
    this.hdr = this.headerPx();
    if (this.sc) { this.css(this.root, '--mk-vh', v.h + 'px'); }      // внутреннее окно: высота сцены — по нему, а не по 100vh
    this.measure();
    this.scenes.forEach(function (s) { self.sceneLayout(s, v); });
  };

  // ---------- кадр прокрутки: сцены, подпись по кривой, шапка без SDA, добор у дна, скорость прокрутки ----------
  P.frame = function () {
    if (!this.alive) { return; }
    var self = this, v = this.view(), now = performance.now(), y = this.scrollY();
    if (this.lastT) { var dt = Math.max(0.008, (now - this.lastT) / 1000); this.vel = (y - this.lastY) / dt; }
    this.lastY = y; this.lastT = now;
    if (this.mode === 'full') {
      this.revealScan(v);
      this.atEnd(v);
      this.scenes.forEach(function (s) { self.sceneRead(s, v); });
      this.scenes.forEach(function (s) { self.sceneWrite(s); });
      this.paths.forEach(function (p) { if (p.vis) { self.pathFrame(p, v); } });
    }
    if (!this.sda) {
      this.headers.forEach(function (h) { self.attr(h, 'data-mk-shrunk', y > 40 || self.mode !== 'full' ? '' : null); });
    }
    this.kick();
  };
  P.pathFrame = function (p, v) {
    var r = p.box.getBoundingClientRect(), t = clamp01((v.top + v.h - r.top) / (v.h + r.height));
    var a = parseFloat(p.from), b = parseFloat(p.to), unit = String(p.to).replace(/^[-\d.]+/, '') || '%';
    this.attr(p.el, 'startOffset', (a + (b - a) * t).toFixed(2) + unit);
  };
  P.syncPaths = function () {
    var self = this;
    if (this.mode !== 'full') { this.paths.forEach(function (p) { var m = p.el.__mk; self.attr(p.el, 'startOffset', m && m.a.startOffset !== undefined ? m.a.startOffset : null); }); }
  };

  // ---------- DOM-сцена прокрутки: scrub · beats · glide · play; прогресс → --mk-p, такт → data-beat ----------
  P.readScene = function (el) {
    var self = this, a = function (k) { return el.getAttribute(k); };
    var q = function (s) { return el.querySelector(s); }, qa = function (s) { return arr(el.querySelectorAll(s)); };
    var mode = a('data-mk-mode') || 'scrub';
    var s = {
      el: el, mode: mode, beats: list(a('data-mk-beats')).map(Number),
      tempo: num(a('data-mk-tempo'), mode === 'beats' ? 3 : (mode === 'glide' ? 2 : 6.5)),
      length: num(a('data-mk-length'), 150), exitAttr: a('data-mk-exit'), dur: num(a('data-mk-dur'), 9),
      range: list(a('data-mk-range')).map(Number),
      stage: q('[data-mk-stage]') || el, cards: qa('[data-mk-beat]'), caps: qa('[data-mk-k]'), dots: qa('[data-mk-dot]'),
      rail: q('[data-mk-rail]'), skip: q('[data-mk-skip]'), veil: q('[data-mk-veil]'),
      segs: qa('[data-mk-seg]').map(function (n) { var r = list(n.getAttribute('data-mk-seg')).map(Number); return { el: n, a: r[0] || 0, b: r.length > 1 ? r[1] : 1, on: null }; }),
      p: 0, cur: 0, v: 0, target: 0, beat: -1, played: false, playing: false, tp: 0, sent: null, vis: false, snap: true, exitPx: 0
    };
    if (s.range.length !== 2) { s.range = [0, 1]; }
    if (mode === 'beats' && !s.beats.length) { s.mode = 'scrub'; this.warn('сцена beats без data-mk-beats — идёт как scrub'); }
    s.segs.forEach(function (g) { self.css(g.el, '--mk-a', String(g.a)); self.css(g.el, '--mk-b', String(g.b)); });
    this.ioV.observe(el);
    return s;
  };
  P.pinned = function (s) { return s.mode !== 'play'; };
  P.sceneLayout = function (s, v) {
    var H = s.stage.getBoundingClientRect().height || v.h;
    s.H = H;
    s.exitPx = s.exitAttr !== null ? num(s.exitAttr, 0) : (s.veil ? Math.round(0.45 * H) : 0);
    if (s.mode === 'scrub' || s.mode === 'glide') { this.css(s.el, '--mk-len', Math.round(s.length / 100 * v.h) + 'px'); }
    var showRail = this.mode === 'full' && !this.phone && s.cards.length >= 3;
    if (s.rail) { this.attr(s.rail, 'hidden', showRail ? null : ''); }
    if (s.skip) { this.attr(s.skip, 'hidden', this.mode === 'full' && this.pinned(s) ? null : ''); }
  };
  P.sceneRead = function (s, v) {
    var r = s.el.getBoundingClientRect(), H = s.H || v.h, top = v.top + this.hdr, p;
    if (this.pinned(s)) { p = (top - r.top) / Math.max(1, r.height - H - (s.mode === 'glide' ? s.exitPx : 0)); }
    else { p = (v.top + v.h - r.top) / (v.h + r.height); }
    s.p = clamp01(p);
    s.r = r;
    var q = clamp01((s.p - s.range[0]) / Math.max(1e-3, s.range[1] - s.range[0]));
    if (s.mode === 'scrub' || s.mode === 'glide') { s.target = q; }
    if (s.mode === 'beats') { this.beatOf(s, v); }
    if (s.mode === 'play' && !s.played) {
      var vis = (Math.min(r.bottom, v.top + v.h) - Math.max(r.top, v.top)) / Math.max(1, r.height);
      if (vis >= 0.4) { s.played = true; s.playing = true; s.tp = 0; s.target = 1; }   // старт при видимости ≥ 40 %, один раз
    }
    s.xo = s.veil && s.exitPx > 0 ? clamp01(1 - (r.bottom - (top + H)) / s.exitPx) : 0;
  };
  // Такт — последняя карточка [data-mk-beat], чей центр прошёл линию 60 % окна (02-stage-runtime.md §5).
  P.beatOf = function (s, v) {
    var line = v.top + v.h * 0.6, k = 0, bt = s.beats;
    s.cards.forEach(function (b, i) { var r = b.getBoundingClientRect(); if (r.height && r.top + r.height * 0.5 < line) { k = i; } });
    k = Math.min(k, bt.length - 1);
    s.nextBeat = k;
    s.target = bt[k];
    s.fill = 1;
    if (k + 1 < s.cards.length) {
      var a = s.cards[k].getBoundingClientRect(), b = s.cards[k + 1].getBoundingClientRect();
      var ca = a.top + a.height * 0.5, cb = b.top + b.height * 0.5;
      s.fill = clamp01((line - ca) / Math.max(1, cb - ca));
    }
  };
  P.sceneWrite = function (s) {
    var self = this;
    if (s.snap) { s.cur = s.mode === 'play' && !s.played ? 0 : s.target; s.v = 0; s.snap = false; this.paint(s); }
    if (s.mode === 'beats' && s.beat !== s.nextBeat) {
      s.beat = s.nextBeat;
      this.attr(s.el, 'data-beat', String(s.beat));
      s.caps.forEach(function (c) { self.attr(c, 'data-on', +c.getAttribute('data-mk-k') === s.beat ? '' : null); });
      s.dots.forEach(function (d, i) { self.attr(d, 'aria-current', i === s.beat ? 'step' : 'false'); });
    }
    if (s.mode === 'beats') {
      var cur = s.caps.filter(function (c) { return +c.getAttribute('data-mk-k') === s.beat; })[0];
      if (cur) { this.css(cur, '--mk-fill', s.fill.toFixed(3)); }
    }
    if (s.veil) { this.css(s.veil, '--mk-veil', (s.xo * s.xo * 0.94).toFixed(3)); }   // выход: окно гаснет в фон места
  };
  P.paint = function (s) {
    var self = this;
    if (s.sent === s.cur) { return; }
    s.sent = s.cur;
    this.css(s.el, '--mk-p', s.cur.toFixed(4));
    s.segs.forEach(function (g) {
      var on = s.cur >= g.a - EPS && s.cur <= g.b + EPS;
      if (g.on !== on) { g.on = on; self.attr(g.el, 'data-on', on ? '' : null); }
    });
  };
  P.scenesStatic = function () {
    var self = this;
    this.scenes.forEach(function (s) {
      self.css(s.el, '--mk-p', null); self.css(s.el, '--mk-len', null); self.attr(s.el, 'data-beat', null);
      s.caps.forEach(function (c) { self.attr(c, 'data-on', null); self.css(c, '--mk-fill', null); });
      s.segs.forEach(function (g) { g.on = null; self.attr(g.el, 'data-on', null); });
      s.dots.forEach(function (d) { self.attr(d, 'aria-current', null); });
      if (s.veil) { self.css(s.veil, '--mk-veil', null); }
      s.sent = null; s.beat = -1; s.snap = true;
    });
  };
  // Цикл пружины: одна запись --mk-p на изменение; без движения — 0 кадров.
  P.kick = function () {
    var self = this;
    if (this.raf || !this.alive) { return; }
    var last = 0;
    this.raf = requestAnimationFrame(function step(now) {
      self.raf = 0;
      var dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60, busy = false;
      last = now;
      if (self.mode === 'full') {
        self.scenes.forEach(function (s) {
          if (s.mode === 'play') {
            if (!s.playing || self.paused) { return; }                 // пауза сдвигает время проигрыша на свою длину
            s.tp += dt;
            var t = Math.min(1, s.tp / s.dur);
            s.cur = 0.5 - 0.5 * Math.cos(Math.PI * t);
            self.paint(s);
            if (t < 1) { busy = true; } else { s.playing = false; }
            return;
          }
          if (Math.abs(s.cur - s.target) < EPS && Math.abs(s.v) < EPS * 4) {
            if (s.cur !== s.target) { s.cur = s.target; s.v = 0; self.paint(s); }
            return;
          }
          var r = spring(s.cur, s.v, s.target, s.tempo, dt);
          s.cur = r[0]; s.v = r[1];
          self.paint(s); busy = true;
        });
      }
      if (self.boost(dt)) { busy = true; }
      if (busy && self.alive) { self.raf = requestAnimationFrame(step); }
    });
  };

  // ---------- указатель: магнит, наклон, прожектор — только мышь и перо, раз в кадр, rAF по требованию ----------
  P.ptrSync = function () {
    var self = this;
    if (this.mode === 'full' && this.fine) { this.kickPtr(); return; }
    this.ptr.forEach(function (p) {
      p.x = p.y = p.tx = p.ty = 0; p.on = false;
      ['--mk-mx', '--mk-my', '--mk-rx', '--mk-ry', '--mk-gx', '--mk-gy', '--mk-glare', '--mk-x', '--mk-y'].forEach(function (n) { self.css(p.el, n, null); });
      if (p.label) { self.css(p.label, '--mk-mx', null); self.css(p.label, '--mk-my', null); }
    });
  };
  P.pmove = function (e) {
    if (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen') { return; }
    this.px = e.clientX; this.py = e.clientY; this.pin = true;
    this.kickPtr();
  };
  P.kickPtr = function () {
    var self = this;
    if (this.prafId || !this.alive || !this.ptr.length || !this.fine || this.mode === 'still') { return; }
    var last = 0;
    this.prafId = requestAnimationFrame(function step(now) {
      self.prafId = 0;
      var dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60, busy = false;
      last = now;
      self.ptr.forEach(function (p) { if (self.ptrStep(p, dt)) { busy = true; } });
      if (busy && self.alive) { self.prafId = requestAnimationFrame(step); }
    });
  };
  P.ptrStep = function (p, dt) {
    var r = p.el.getBoundingClientRect(), full = this.mode === 'full', x = this.px, y = this.py, cs, mx, lam;
    if (p.kind === 'magnet') {
      if (!full) { return false; }
      cs = getComputedStyle(p.el);
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2, R = 0.8 * Math.max(r.width, r.height);   // радиус 1,6 размера
      mx = Math.min(num(cs.getPropertyValue('--mk-magnet'), 8), 0.25 * r.height);                       // ≤ токена и ≤ 25 % высоты
      var dx = x - cx, dy = y - cy, d = Math.sqrt(dx * dx + dy * dy);
      p.tx = 0; p.ty = 0;
      if (this.pin && d < R && d > 0) { var f = Math.min(1, d / (0.5 * R)) * mx / d; p.tx = dx * f; p.ty = dy * f; }
      lam = 8;
    } else if (p.kind === 'tilt') {
      if (!full) { return false; }
      var inside = this.pin && x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
      var deg = Math.min(7, num(p.el.getAttribute('data-mk-deg'), 6));                                    // ≤ 7° (effects.yaml)
      p.tx = inside ? (0.5 - (y - r.top) / r.height) * 2 * deg : 0;     // rotateX
      p.ty = inside ? ((x - r.left) / r.width - 0.5) * 2 * deg : 0;     // rotateY
      p.ta = inside ? 1 : 0;
      lam = 7;
    } else {
      var area = p.el.closest('[data-mk-area]') || p.el.parentElement || p.el, ar = area.getBoundingClientRect();
      var hit = this.pin && x >= ar.left && x <= ar.right && y >= ar.top && y <= ar.bottom;
      p.tx = hit ? x - r.left : 0.7 * r.width; p.ty = hit ? y - r.top : 0.3 * r.height;                  // покой — 70 % / 30 %
      lam = full ? 10 : 1e3;                                                                              // reduce: без хвоста
    }
    p.x = damp(p.x, p.tx, lam, dt); p.y = damp(p.y, p.ty, lam, dt); p.a = damp(p.a, p.ta, lam, dt);
    var settled = Math.abs(p.x - p.tx) < 0.05 && Math.abs(p.y - p.ty) < 0.05 && Math.abs(p.a - p.ta) < 0.01;
    if (settled) { p.x = p.tx; p.y = p.ty; p.a = p.ta; }
    if (p.kind === 'magnet') {
      this.css(p.el, '--mk-mx', p.x.toFixed(2) + 'px'); this.css(p.el, '--mk-my', p.y.toFixed(2) + 'px');
      if (p.label) { this.css(p.label, '--mk-mx', (p.x * 0.4).toFixed(2) + 'px'); this.css(p.label, '--mk-my', (p.y * 0.4).toFixed(2) + 'px'); }
    } else if (p.kind === 'tilt') {
      this.css(p.el, '--mk-rx', p.x.toFixed(2) + 'deg'); this.css(p.el, '--mk-ry', p.y.toFixed(2) + 'deg');
      this.css(p.el, '--mk-gx', (50 + p.y / 7 * 50).toFixed(1) + '%'); this.css(p.el, '--mk-gy', (50 - p.x / 7 * 50).toFixed(1) + '%');
      this.css(p.el, '--mk-glare', p.a.toFixed(3));
    } else {
      this.css(p.el, '--mk-x', p.x.toFixed(1) + 'px'); this.css(p.el, '--mk-y', p.y.toFixed(1) + 'px');
    }
    return !settled;
  };

  // ---------- кнопки: выбор движения, пауза, окно, переворот, смена состояния, рельс, «Пропустить» ----------
  P.click = function (e) {
    var t = e.target && e.target.closest ? e.target : null, b;
    if (!t || !this.root.contains(t) && !(this.o.toggle && t.closest('[data-motion-set], [data-mk~="pause"]'))) { return; }
    if (this.o.toggle && (b = t.closest('[data-motion-set]'))) { this.choose(b.getAttribute('data-motion-set') || ''); return; }
    if (this.o.toggle && (b = t.closest('[data-mk~="pause"]'))) { this.setPaused(!this.paused); return; }
    if ((b = t.closest('[commandfor]')) && !('commandForElement' in HTMLButtonElement.prototype)) { this.command(b); return; }
    if ((b = t.closest('[data-mk-flip-toggle]'))) { this.flip(b); return; }
    if ((b = t.closest('[data-mk~="state"]'))) { this.state(b); return; }
    if ((b = t.closest('[data-mk-dot]'))) { this.goBeat(b); return; }
    if ((b = t.closest('[data-mk-skip]'))) { this.skipScene(b); return; }
    if ((b = t.closest('dialog[data-mk~="dialog"][closedby="any"]')) && t === b && !('closedBy' in HTMLDialogElement.prototype)) { this.dismiss(b, e); }
  };
  // Окно без JS открывают команды кнопок (command / commandfor); где их нет — то же действие набором.
  P.command = function (b) {
    var d = this.doc.getElementById(b.getAttribute('commandfor')), c = b.getAttribute('command');
    if (!d || !d.showModal) { return; }
    if (c === 'show-modal' && !d.open) { d.showModal(); } else if ((c === 'close' || c === 'request-close') && d.open) { d.close(); }
  };
  P.dismiss = function (d, e) {
    var r = d.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) { d.close(); }
  };
  P.flip = function (b) {
    var card = b.closest('[data-mk~="flip"]'), on;
    if (!card) { return; }
    on = !card.hasAttribute('data-mk-flipped');
    this.attr(card, 'data-mk-flipped', on ? '' : null);
    arr(card.querySelectorAll('[data-mk-flip-toggle]')).forEach(function (x) { x.setAttribute('aria-expanded', on ? 'true' : 'false'); });
    var back = card.querySelector('[data-mk-back] a, [data-mk-back] button');
    if (on && back) { setTimeout(function () { back.focus({ preventScroll: true }); }, 0); }     // фокус — на ссылку оборота
  };
  // Смена состояния блока в View Transition (effect view-transition): атрибут цели меняет набор, морфинг — браузер.
  P.state = function (b) {
    var target = this.doc.querySelector(b.getAttribute('data-mk-target') || ''), name = b.getAttribute('data-mk-attr') || 'data-state';
    var val = b.getAttribute('data-mk-value') || '', grp = arr(this.doc.querySelectorAll('[data-mk~="state"]')).filter(function (x) {
      return x.getAttribute('data-mk-target') === b.getAttribute('data-mk-target') && (x.getAttribute('data-mk-attr') || 'data-state') === name;
    });
    if (!target) { this.warn('state: цель ' + b.getAttribute('data-mk-target') + ' не найдена'); return; }
    this.transition(function () {
      target.setAttribute(name, val);
      grp.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    }, 'mk-state');
  };
  P.transition = function (fn, type) {
    var d = this.doc;
    if (this.mode !== 'full' || !d.startViewTransition) { fn(); return null; }
    try { return d.startViewTransition({ update: fn, types: [type || 'mk-state'] }); }
    catch (e) { return d.startViewTransition(fn); }                    // движок без types
  };
  P.scrollByY = function (dy) {
    var s = this.sc || this.doc.scrollingElement || this.doc.documentElement;
    try { s.scrollBy({ top: dy, behavior: this.mode === 'full' ? 'smooth' : 'auto' }); } catch (e) { s.scrollTop += dy; }
  };
  P.sceneOf = function (el) { for (var i = 0; i < this.scenes.length; i++) { if (this.scenes[i].el.contains(el)) { return this.scenes[i]; } } return null; };
  P.goBeat = function (b) {
    var s = this.sceneOf(b), k = s ? s.dots.indexOf(b) : -1, c = s && s.cards[k], v = this.view();
    if (!c) { return; }
    var r = c.getBoundingClientRect();
    this.scrollByY(r.top + r.height * 0.5 - (v.top + v.h * 0.6) + 2);
  };
  P.skipScene = function (b) {
    var s = this.sceneOf(b), v = this.view();
    if (s) { this.scrollByY(s.el.getBoundingClientRect().bottom - (v.top + this.hdr)); }
  };

  // ---------- состояние, обновление, снятие ----------
  P.info = function () {
    var shown = 0, total = 0;
    this.groups.forEach(function (rec) { total += rec.items.length; if (rec.done) { shown += rec.items.length; } });
    return {
      version: VERSION, mode: this.mode, paused: this.paused, choice: this.choice(), phone: this.phone, fine: this.fine,
      sda: this.sda, scroller: this.sc ? 'element' : 'document', counts: this.counts, reveals: { shown: shown, total: total },
      loopsInView: this.inView || 0, budget: Math.max(1, (BUDGET[this.o.level] || 2) - (this.phone ? 1 : 0)),
      scenes: this.scenes.map(function (s) {
        return { mode: s.mode, p: +s.p.toFixed(4), cur: +s.cur.toFixed(4), target: s.target, beat: s.beat, tempo: s.tempo, playing: s.playing };
      }),
      warnings: this.warns.slice()
    };
  };
  P.notify = function () {
    var i = this.info();
    if (this.o.onState) { try { this.o.onState(i); } catch (e) { /* обвязка места */ } }
    try { this.root.dispatchEvent(new CustomEvent('mk:state', { detail: i })); } catch (e) { /* старый движок */ }
  };
  P.refresh = function () {
    if (!this.alive) { return; }
    var sc = this.o.scroller || scrollerOf(this.root);
    this.sc = sc;
    this.scan();
    this.apply();
  };
  P.destroy = function () {
    var self = this;
    if (!this.alive) { return; }
    this.alive = false;
    this.doc.removeEventListener('scroll', this.onScroll, { capture: true });
    window.removeEventListener('resize', this.onResize);
    [this.mqR, this.mqP, this.mqF].forEach(function (m) { unlisten(m, self.onMedia); });
    this.doc.removeEventListener('click', this.onClick);
    this.doc.removeEventListener('pointermove', this.onMove);
    this.doc.removeEventListener('pointerout', this.onOut);
    this.ioR.disconnect(); this.ioV.disconnect(); this.mo.disconnect();
    if (this.raf) { cancelAnimationFrame(this.raf); this.raf = 0; }
    if (this.prafId) { cancelAnimationFrame(this.prafId); this.prafId = 0; }
    this.loops.forEach(function (L) { arr(L.el.querySelectorAll('[data-mk-track]')).forEach(function (tr) { (tr.getAnimations ? tr.getAnimations() : []).forEach(function (a) { a.playbackRate = 1; }); }); });
    this.touched.forEach(function (el) {
      var m = el.__mk, k;
      for (k in m.a) { if (m.a[k] === null) { el.removeAttribute(k); } else { el.setAttribute(k, m.a[k]); } }
      for (k in m.v) { el.style.removeProperty(k); }
      delete el.__mk;
    });
    arr(this.root.querySelectorAll('[data-mk]')).concat([this.root]).forEach(function (el) { delete el.__mkW; });
    this.touched = [];
  };

  function mount(root, opts) {
    var k = new Kit(root || document, opts).mount();
    return {
      destroy: function () { k.destroy(); },
      pause: function () { k.setPaused(true); },
      resume: function () { k.setPaused(false); },
      refresh: function () { k.refresh(); },
      info: function () { return k.info(); },
      transition: function (fn, type) { return k.transition(fn, type); }
    };
  }

  window.MotionKit = { version: VERSION, mount: mount, spring: spring, damp: damp, viewMode: viewMode };
})();
