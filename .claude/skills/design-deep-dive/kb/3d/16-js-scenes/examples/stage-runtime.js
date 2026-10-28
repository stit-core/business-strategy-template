/* stage-runtime.js — рантайм живых сцен страницы: видимость, прогресс прокрутки с пружиной, режимы шагов, пути и проигрыша,
   предел живых сцен, постер и раскадровка, «уменьшить движение», программный рендер. Без библиотек, прокрутку не перехватывает.

   Подключение:
     <script src="scenes/<имя>.js"></script>             регистрирует window.STAGE_SCENES['<имя>'] (scene-template.js)
     <script src="stage-runtime.js"></script>
     <script>new StageRuntime(window.STAGE_SCENES, { header: 72 }).mount(document);</script>

   Разметка сцены (атрибуты читает рантайм; облик — CSS страницы):
     <section data-stage="<имя>" data-mode="beats|glide|play|scrub" data-beats="0,0.25,0.5,0.75,1" data-tempo="3"
              data-pin="3400" data-exit="340" data-dur="9" data-range="0,1" data-variant="hero" data-bg="#16181D"
              data-tex="img/a.webp,img/b.webp" data-rtl>
       <div data-window>                                   окно сцены; beats и glide — position: sticky; top: <шапка>px
         <img data-poster src="poster.jpg" alt="">         кадр покоя той же камеры (p = poster_p), он же запасной
         <canvas data-canvas aria-hidden="true" hidden></canvas>
         <p class="visually-hidden">что на сцене — для экранного диктора</p>
         <div data-caps aria-live="polite"><div data-cap data-k="1">…<i data-fill></i></div>…</div>   подписи тактов
         <p data-from="0.2" data-to="0.45">…</p>           надпись на отрезке прогресса (scrub, glide, play): [data-on] на отрезке
         <nav data-rail><button data-dot>…</button>…</nav>  рельс тактов
         <button data-skip>Пропустить</button> <button data-pause aria-pressed="false" aria-label="…">…</button>
         <div data-veil aria-hidden="true"></div>          выход: окно гаснет в фон места на последних data-exit px
       </div>
       <div data-steps><div data-beat></div>…</div>        beats: блоки задают длину прокрутки до тактов: первый — заставка
                                                           (0,78 H), шаг ≈ 480 px ПК / 420 телефон, последний — шаг + хвост
                                                           0,45 H + выход 0,45 H (data-exit); у data-steps margin-top: −H
       <div data-story hidden>…кадры тактов с подписями…</div>   раскадровка: обзор, reduce, программный рендер
     </section>

   Состояния на разметке: section[data-live] — сцена ожила (холст поверх постера, переход прозрачности — CSS);
   [data-stage-story] — раскадровка вместо закрепления (CSS: шаги скрыты, data-story виден, высота поля — auto);
   [data-cap][data-on] и --fill — подпись такта и доля пути до следующего; [data-dot][aria-current="step"] — текущий такт.

   Режимы:
     scrub — прогресс = доля прокрутки (полоса через окно или поле data-pin), сцена догоняет пружиной ω 6,5 (95 % за ≈ 0,73 с);
     beats — текст идёт карточками обычной прокруткой; такт — последний блок data-beat, чей центр прошёл линию 60 % окна;
             сцена сама доводит прогресс до точки покоя такта пружиной ω data-tempo (3 → 95 % за ≈ 1,6 с);
     glide — путь с инерцией: прогресс = доля прокрутки поля data-pin, пружина ω data-tempo (по умолчанию 2);
     play  — сама играет: когда видно ≥ 40 % полосы, 0 → 1 за data-dur секунд по синусоиде, один раз, финал держится. */
(function () {
  'use strict';
  var D = {
    maxLive: 2, maxLivePhone: 1,          // живых сцен одновременно: ПК / телефон
    wakeAhead: 0.5,                       // оживить, когда до окна ≤ 0,5 его высоты
    dropFar: 1.5,                         // уничтожить сцену дальше 1,5 высоты окна (контекст освобождается)
    line: 0.6,                            // линия такта — 60 % высоты окна
    header: 72, headerPhone: 64,          // липкая шапка: под ней закрепление, к ней — «Пропустить»
    tempo: 6.5, tempoBeats: 3, tempoGlide: 2, eps: 4e-4,
    dur: 9, playAt: 0.4,
    exitK: 0.94,                          // предел затемнения выхода
    phone: '(max-width: 40rem), (pointer: coarse)',
    force3d: false,                       // стенд: живые сцены и на программном рендере
    isLive: null,                         // () => bool: показан ли документ вживую (обзор холста — нет); по умолчанию — да
    retryLost: 1                          // сколько раз оживлять сцену заново после потери контекста
  };
  function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
  function num(v, d) { var x = parseFloat(v); return isFinite(x) ? x : d; }
  function list(v) { return String(v || '').split(',').map(function (x) { return x.trim(); }).filter(Boolean); }
  // Критически демпфированная пружина, точное решение за шаг dt: без рывка в начале, без перелёта; 95 % пути — за 4,74/ω с.
  function spring(x, v, target, w, dt) {
    var d = x - target, e = Math.exp(-w * dt), c = v + w * d;
    return [target + (d + c * dt) * e, (v - w * c * dt) * e];
  }
  // Программный рендер (SwiftShader, llvmpipe, softpipe, «Microsoft Basic Render»): живых сцен нет — постеры и раскадровка.
  function isSoftware() {
    try {
      var free = function (g) { var x = g && g.getExtension('WEBGL_lose_context'); if (x) { x.loseContext(); } };
      var gl = document.createElement('canvas').getContext('webgl2', { failIfMajorPerformanceCaveat: true });
      if (!gl) {
        // контекст есть только «с оговоркой о скорости» — значит, рисует процессор
        var any = document.createElement('canvas').getContext('webgl2'); free(any);
        return !!any;
      }
      var r = String(gl.getParameter(gl.RENDERER) || '');
      var ext = gl.getExtension('WEBGL_debug_renderer_info');
      if (ext) { r += ' ' + String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) || ''); }
      free(gl);
      return /swiftshader|llvmpipe|softpipe|software|basic render/i.test(r);
    } catch (e) { return false; }
  }

  function StageRuntime(scenes, o) {
    this.scenes = scenes || {};
    this.o = {};
    var k;
    for (k in D) { if (Object.prototype.hasOwnProperty.call(D, k)) { this.o[k] = D[k]; } }
    for (k in (o || {})) { if (Object.prototype.hasOwnProperty.call(o, k)) { this.o[k] = o[k]; } }
    this.st = [];
    this.raf = 0;
    this.tick = false;
  }
  var P = StageRuntime.prototype;

  P.mount = function (root) {
    var self = this;
    root = root || document;
    this.alive = true;
    this.soft = !this.o.force3d && isSoftware();
    this.mqR = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    this.mqP = window.matchMedia ? window.matchMedia(this.o.phone) : null;
    this.rm = !!(this.mqR && this.mqR.matches);
    this.phone = !!(this.mqP && this.mqP.matches);
    this.st = Array.prototype.slice.call(root.querySelectorAll('[data-stage]')).map(function (el) { return self.read(el); });
    this.onScroll = function () {
      if (self.tick) { return; }
      self.tick = true;
      requestAnimationFrame(function () { self.tick = false; self.frame(); });
    };
    this.onResize = function () { self.phone = !!(self.mqP && self.mqP.matches); self.layout(); self.frame(); };
    this.onVis = function () { if (!document.hidden) { self.st.forEach(function (s) { if (s.eng && s.eng.wake) { s.eng.wake(); } }); } };
    this.onRm = function () { self.rm = !!self.mqR.matches; self.layout(); self.frame(); };
    document.addEventListener('scroll', this.onScroll, { passive: true, capture: true });   // и прокрутка внутренних окон
    window.addEventListener('resize', this.onResize);
    document.addEventListener('visibilitychange', this.onVis);
    if (this.mqR && this.mqR.addEventListener) { this.mqR.addEventListener('change', this.onRm); }
    this.st.forEach(function (s) { self.wire(s); });
    this.layout();
    this.frame();
    return this;
  };

  P.destroy = function () {
    var self = this;
    this.alive = false;
    document.removeEventListener('scroll', this.onScroll, { capture: true });
    window.removeEventListener('resize', this.onResize);
    document.removeEventListener('visibilitychange', this.onVis);
    if (this.mqR && this.mqR.removeEventListener) { this.mqR.removeEventListener('change', this.onRm); }
    if (this.raf) { cancelAnimationFrame(this.raf); this.raf = 0; }
    this.st.forEach(function (s) { self.drop(s); });
  };

  // ---------- конфигурация сцены из атрибутов ----------
  P.read = function (el) {
    var a = function (k) { return el.getAttribute(k); };
    var mode = a('data-mode') || 'scrub';
    var c = {
      el: el, scene: a('data-stage'), mode: mode, beats: list(a('data-beats')).map(Number),
      tempo: num(a('data-tempo'), mode === 'beats' ? this.o.tempoBeats : (mode === 'glide' ? this.o.tempoGlide : this.o.tempo)),
      pin: num(a('data-pin'), 0), exit: num(a('data-exit'), 0), dur: num(a('data-dur'), this.o.dur),
      range: list(a('data-range')).map(Number), variant: a('data-variant') || '', bg: a('data-bg') || '', rtl: el.hasAttribute('data-rtl'),
      tex: list(a('data-tex'))
    };
    if (c.range.length !== 2) { c.range = [0, 1]; }
    if (mode === 'beats' && !c.beats.length) { c.mode = 'scrub'; }
    var q = function (s) { return el.querySelector(s); }, qa = function (s) { return Array.prototype.slice.call(el.querySelectorAll(s)); };
    return {
      c: c, state: 'poster', eng: null, pend: null, failed: false, lost: 0, cool: 0, frozen: false,
      d: 1e9, dc: 0, p: 0, cur: 0, v: 0, target: 0, beat: -1, played: false, playing: false, t0: 0, tp: 0,
      win: q('[data-window]') || el, canvas: q('[data-canvas]'), poster: q('[data-poster]'), story: q('[data-story]'),
      blocks: qa('[data-beat]'), caps: qa('[data-cap][data-k]'), steps: qa('[data-from]'), dots: qa('[data-dot]'),
      skip: q('[data-skip]'), pause: q('[data-pause]'), exitEl: q('[data-veil]'), rail: q('[data-rail]'), imgs: null
    };
  };

  P.wire = function (s) {
    var self = this;
    if (s.pause) { s.pause.addEventListener('click', function () { self.toggle(s); }); }
    if (s.skip) { s.skip.addEventListener('click', function () { self.skipTo(s); }); }
    s.dots.forEach(function (b, k) { b.addEventListener('click', function () { self.goBeat(s, k); }); });
  };

  // ---------- вживую или раскадровка ----------
  P.liveMode = function () { return (this.o.isLive ? !!this.o.isLive() : true) && !this.rm && !this.soft; };
  P.layout = function () {
    var self = this, live = this.liveMode();
    this.st.forEach(function (s) {
      var el = s.c.el, pinned = s.c.mode === 'glide' || (s.c.mode === 'scrub' && s.c.pin > 0);
      if (live) { el.removeAttribute('data-stage-story'); } else { el.setAttribute('data-stage-story', ''); }
      if (s.story) { s.story.hidden = live; }
      // поле закрепления держит длинную прокрутку только вживую; в раскадровке — окно с заставкой и кадры тактов
      if (pinned) { el.style.height = live ? (s.c.pin + s.c.exit) + 'px' : 'auto'; }
      [s.skip, s.rail].forEach(function (x) { if (x) { x.hidden = !live || (x === s.rail && self.phone); } });
      if (!live) { self.drop(s); }
    });
  };

  // ---------- кадр прокрутки: дистанции, прогресс, такты, надписи ----------
  P.frame = function () {
    if (!this.alive) { return; }
    var self = this, vh = window.innerHeight || 800, top = this.phone ? this.o.headerPhone : this.o.header, live = this.liveMode();
    this.st.forEach(function (s) {
      var c = s.c, r = c.el.getBoundingClientRect();
      s.d = r.bottom < 0 ? -r.bottom : (r.top > vh ? r.top - vh : 0);                   // насколько полоса за окном
      s.dc = Math.abs((r.top + r.bottom) / 2 - vh / 2);                                     // из видимых живёт ближняя к центру
      var H = s.win.getBoundingClientRect().height || vh, p;
      var pinned = c.mode === 'glide' || c.mode === 'beats' || (c.mode === 'scrub' && c.pin > 0);
      if (pinned && live) { p = (top - r.top) / Math.max(1, r.height - H - (c.mode === 'glide' ? c.exit : 0)); }
      else { p = (vh - r.top) / (vh + r.height); }
      s.p = clamp01(p);
      var q = clamp01((s.p - c.range[0]) / Math.max(1e-3, c.range[1] - c.range[0]));
      if (c.mode === 'scrub' || c.mode === 'glide') { s.target = q; }
      if (c.mode === 'beats') { self.beatOf(s, vh); }
      if (c.mode === 'play') { self.playOf(s, r, vh); }
      // выход закреплённой сцены: на последних exit px окно гаснет в фон места, и только потом поле уезжает
      if (s.exitEl && c.exit > 0) {
        var xo = live ? clamp01(1 - (r.bottom - (top + H)) / c.exit) : 0, xs = (xo * xo * self.o.exitK).toFixed(3);
        if (s.exitEl._o !== xs) { s.exitEl._o = xs; s.exitEl.style.opacity = xs; }
      }
      if (!s.eng) { self.texts(s, c.mode === 'play' ? (s.played ? 1 : 0) : s.target); }
      if (s.eng) { s.eng.setVisible(s.d === 0); }                                           // за экраном — сон, 0 кадров
    });
    this.reconcile();
    this.kick();
  };

  // такт — последний блок, чей центр прошёл линию; подпись такта включается, --fill — путь до следующего такта
  P.beatOf = function (s, vh) {
    var line = vh * this.o.line, k = 0, bt = s.c.beats;
    s.blocks.forEach(function (b, i) { var r = b.getBoundingClientRect(); if (r.height && r.top + r.height * 0.5 < line) { k = i; } });
    k = Math.min(k, bt.length - 1);
    if (s.beat !== k) {
      s.beat = k; s.target = bt[k];
      s.caps.forEach(function (c) { if (+c.getAttribute('data-k') === k) { c.setAttribute('data-on', ''); } else { c.removeAttribute('data-on'); } });
      s.dots.forEach(function (d, i) { d.setAttribute('aria-current', i === k ? 'step' : 'false'); });
    }
    var cur = s.caps.filter(function (c) { return +c.getAttribute('data-k') === k; })[0];
    if (!cur) { return; }
    var fl = 1;
    if (k + 1 < s.blocks.length) {
      var a = s.blocks[k].getBoundingClientRect(), b = s.blocks[k + 1].getBoundingClientRect();
      var ca = a.top + a.height * 0.5, cb = b.top + b.height * 0.5;
      fl = clamp01((line - ca) / Math.max(1, cb - ca));
    }
    if (Math.abs((cur._fl || 0) - fl) > 0.004) { cur._fl = fl; cur.style.setProperty('--fill', fl.toFixed(3)); }
  };

  // сама играет: старт, когда полоса видна на 40 % своей высоты; один раз за просмотр страницы
  P.playOf = function (s, r, vh) {
    if (s.played) { return; }
    var vis = (Math.min(r.bottom, vh) - Math.max(r.top, 0)) / Math.max(1, r.height);
    if (vis >= this.o.playAt) { s.played = true; s.playing = true; s.t0 = 0; s.target = 1; }
  };

  // надписи на отрезках прогресса: видна только на своём отрезке
  P.texts = function (s, p) {
    s.steps.forEach(function (el) {
      var a = num(el.getAttribute('data-from'), 0), b = num(el.getAttribute('data-to'), 1), on = p >= a && p <= b;
      if (el._on === on) { return; }
      el._on = on;
      if (on) { el.setAttribute('data-on', ''); } else { el.removeAttribute('data-on'); }
    });
  };

  // ---------- сколько сцен живёт: ближние к окну, не больше предела ----------
  P.reconcile = function () {
    var self = this, vh = window.innerHeight || 800, now = performance.now(), live = this.liveMode();
    var max = this.phone ? this.o.maxLivePhone : this.o.maxLive;
    this.st.forEach(function (s) { if (s.state !== 'poster' && (!live || s.d > self.o.dropFar * vh)) { self.drop(s); } });
    if (!live) { return; }
    var count = function () { return self.st.filter(function (s) { return s.state !== 'poster'; }).length; };
    this.st.filter(function (s) { return s.state === 'poster' && !s.failed && now >= s.cool && s.d <= self.o.wakeAhead * vh; })
      .sort(function (a, b) { return a.d - b.d || a.dc - b.dc; })
      .forEach(function (c) {
        if (count() >= max) {
          var far = self.st.filter(function (s) { return s.state !== 'poster' && (s.d > c.d || (s.d === c.d && s.dc > c.dc + 80)); })
            .sort(function (a, b) { return b.d - a.d || b.dc - a.dc; })[0];
          if (!far) { return; }
          self.drop(far);
        }
        self.start(c);
      });
  };

  // ---------- жизнь сцены ----------
  P.start = function (s) {
    var self = this, c = s.c, make = this.scenes[c.scene], cv = s.canvas;
    if (!make || !cv) { this.fail(s, make ? 'нет холста' : 'нет сцены ' + c.scene); return; }
    s.state = 'loading';
    cv.hidden = false; cv.style.opacity = '0';
    var o = {
      mobile: this.phone, rtl: c.rtl, variant: c.variant, background: c.bg || undefined, pin: (c.mode === 'beats' || c.mode === 'glide') || c.pin > 0,
      driven: true, idle: !s.frozen,
      onReady: function (eng) { self.ready(s, eng, cv); },
      onStatus: function (code, log) {
        if (code === 'context-lost' && s.canvas === cv) { self.lose(s); }
        else if (code === 'shader-error' && s.canvas === cv) { self.fail(s, code + (log ? ': ' + String(log).slice(0, 160) : '')); }
      }
    };
    s.canvas = cv;
    var h = null;
    try { h = make(cv, o); } catch (err) { h = null; s.err = String(err && err.message || err); }
    if (!h) { this.fail(s, s.err || 'нет WebGL2'); return; }
    if (h.pending) { s.pend = h; } else { this.ready(s, h, cv); }
  };
  P.ready = function (s, eng, cv) {
    if (s.state !== 'loading' || s.canvas !== cv) { if (eng) { try { eng.destroy(); } catch (e) { /* уже снята */ } } return; }
    s.pend = null;
    if (!eng) { this.fail(s, 'шейдер не собрался'); return; }
    s.eng = eng; s.state = 'live';
    if (s.c.tex.length && eng.setTexture) {
      if (!s.imgs) { s.imgs = s.c.tex.map(function (u) { var im = new Image(); im.crossOrigin = 'anonymous'; im.decoding = 'async'; im.src = u; return im; }); }
      s.imgs.forEach(function (im, i) {
        var put = function () { if (s.eng === eng) { try { eng.setTexture(i, im); } catch (e) { /* без текстуры */ } } };
        if (im.complete && im.naturalWidth) { put(); } else { im.addEventListener('load', put, { once: true }); }
      });
    }
    if (s.frozen) { eng.setIdle(false); if (eng.setPlaying) { eng.setPlaying(false); } }
    s.cur = s.c.mode === 'play' && s.playing ? 0 : s.target; s.v = 0;
    this.apply(s);
    s.c.el.setAttribute('data-live', '');
    s.canvas.style.opacity = '1';                                                           // постер под холстом, переход — CSS
    if (s.pause) { s.pause.hidden = false; }
    this.kick();
  };
  P.fail = function (s, why) {
    this.drop(s); s.failed = true;
    try { console.warn('сцена ' + s.c.scene + ' осталась постером: ' + (why || 'движок не запустился')); } catch (e) { /* консоли нет */ }
  };
  // потеря контекста: постер сразу; на следующем подлёте — ещё попытка (не больше retryLost), потом — постер насовсем
  P.lose = function (s) {
    this.drop(s); s.lost += 1; s.cool = performance.now() + 3000;
    if (s.lost > this.o.retryLost) { s.failed = true; }
  };
  P.drop = function (s) {
    if (s.eng) { try { s.eng.destroy(); } catch (e) { /* контекст уже потерян */ } }
    if (s.pend) { try { s.pend.destroy(); } catch (e) { /* контекст уже потерян */ } }
    s.eng = null; s.pend = null;
    if (s.state !== 'poster') {
      s.state = 'poster';
      s.c.el.removeAttribute('data-live');
      if (s.canvas && s.canvas.parentNode) {
        // свежий холст: у потерянного или снятого контекста холст не переиспользуется (getContext вернёт тот же потерянный)
        var fresh = s.canvas.cloneNode(false); fresh.hidden = true; fresh.style.opacity = '0';
        s.canvas.parentNode.replaceChild(fresh, s.canvas); s.canvas = fresh;
      }
      if (s.pause) { s.pause.hidden = true; }
    }
  };

  // ---------- прогресс в сцену: пружина и проигрыш, одна отрисовка на изменение ----------
  P.apply = function (s) {
    if (!s.eng) { return; }
    if (s.sent !== s.cur) { s.sent = s.cur; s.eng.scrub(s.cur); }
    this.texts(s, s.cur);
  };
  P.kick = function () {
    var self = this;
    if (this.raf || !this.alive) { return; }
    var last = 0;
    this.raf = requestAnimationFrame(function step(now) {
      self.raf = 0;
      var dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60, busy = false;
      last = now;
      self.st.forEach(function (s) {
        if (s.state !== 'live' || s.frozen) { return; }
        if (s.c.mode === 'play') {
          if (!s.playing) { return; }
          s.tp += dt;
          var t = Math.min(1, s.tp / s.c.dur);
          s.cur = 0.5 - 0.5 * Math.cos(Math.PI * t);                                       // разгон и торможение
          self.apply(s);
          if (t < 1) { busy = true; } else { s.playing = false; }
          return;
        }
        var eps = self.o.eps;
        if (Math.abs(s.cur - s.target) < eps && Math.abs(s.v) < eps * 4) {
          if (s.cur !== s.target) { s.cur = s.target; s.v = 0; self.apply(s); }
          return;
        }
        var r = spring(s.cur, s.v, s.target, s.c.tempo, dt);
        s.cur = r[0]; s.v = r[1];
        self.apply(s); busy = true;
      });
      if (busy && self.alive) { self.raf = requestAnimationFrame(step); }
    });
  };

  // ---------- кнопки: пауза, «Пропустить», рельс ----------
  P.toggle = function (s) {
    s.frozen = !s.frozen;
    if (s.eng) { s.eng.setIdle(!s.frozen); if (s.eng.setPlaying) { s.eng.setPlaying(!s.frozen); } }
    if (s.pause) { s.pause.setAttribute('aria-pressed', s.frozen ? 'true' : 'false'); }
    if (!s.frozen) { this.kick(); }
  };
  P.scrollByY = function (dy) {
    var sc = document.scrollingElement || document.documentElement;
    try { sc.scrollBy({ top: dy, behavior: this.rm ? 'auto' : 'smooth' }); } catch (e) { sc.scrollTop += dy; }
  };
  P.skipTo = function (s) {
    var top = this.phone ? this.o.headerPhone : this.o.header;
    this.scrollByY(s.c.el.getBoundingClientRect().bottom - top);
  };
  P.goBeat = function (s, k) {
    var b = s.blocks[k];
    if (!b) { return; }
    var r = b.getBoundingClientRect(), vh = window.innerHeight || 800;
    this.scrollByY(r.top + r.height * 0.5 - vh * this.o.line + 2);
  };
  P.info = function () {
    return this.st.map(function (s) {
      return { scene: s.c.scene, mode: s.c.mode, state: s.state, p: +s.p.toFixed(3), cur: +s.cur.toFixed(3), beat: s.beat, failed: s.failed,
        eng: s.eng && s.eng.info ? s.eng.info() : null };
    });
  };

  StageRuntime.spring = spring;
  StageRuntime.isSoftware = isSoftware;
  window.StageRuntime = StageRuntime;
})();
