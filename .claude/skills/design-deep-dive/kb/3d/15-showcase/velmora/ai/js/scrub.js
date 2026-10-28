/* scrub.js — «мышь ведёт видео»: горизонталь указателя (касание — протяжкой) → кадр ролика с плавным догоном (lerp) и холостым
   дрейфом, когда указатель стоит. Две доставки: видео с коротким GOP (перемотка currentTime, задержка `seeked`) и секвенция
   кадров на <canvas> (точный кадр + перекрёстное смешение соседних кадров — «под-кадровая» плавность).
   Обычный скрипт (не модуль) — работает и с file://, и с http.server.

   Разметка: <section data-scrub data-default="orbit-av1-g4" data-rest="0.5"> … .stage__media (img постера) … </section>
             <script type="application/json" id="scrub-manifest">{…}</script>   (веса и пути ассетов)
   Доступность: reduce → 0 байт медиа, только постер и кнопка «Показать облёт»; Save-Data/2G → кнопка с весом; холостой дрейф
   дольше 5 с — кнопка паузы 44 px (WCAG 2.2.2); клавиатура — ползунок (input range) с именем; пауза вне экрана и во вкладке.
   Замер: ?bench=1 — сценарий движения 8 с, итог в window.__scrubBench и <html data-bench="done">; ?v=<вариант> — выбрать доставку. */
(function () {
  'use strict';
  var RM = matchMedia('(prefers-reduced-motion: reduce)');
  var FINE = matchMedia('(hover: hover) and (pointer: fine)');
  var conn = navigator.connection || {};
  var LOW_DATA = conn.saveData === true || /(^|-)2g$/.test(conn.effectiveType || '');
  var Q = new URLSearchParams(location.search);
  var HTTP = /^https?:$/.test(location.protocol);

  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function median(a) { if (!a.length) return null; var s = a.slice().sort(function (x, y) { return x - y; }); return s[Math.floor(s.length / 2)]; }
  function pct(a, p) { if (!a.length) return null; var s = a.slice().sort(function (x, y) { return x - y; }); return s[Math.min(s.length - 1, Math.floor(s.length * p))]; }
  function kb(n) { return (n / 1024).toLocaleString('ru-RU', {maximumFractionDigits: 0}) + ' КБ'; }

  function Scrub(root, manifest) {
    this.root = root; this.m = manifest;
    this.media = root.querySelector('.stage__media');
    this.poster = this.media.querySelector('img');
    this.range = root.querySelector('input[type=range][data-scrub-range]');
    this.pauseBtn = root.querySelector('.motion-toggle');
    this.optIn = root.querySelector('[data-scrub-optin]');
    this.rest = Number(root.dataset.rest || 0.5);
    this.mode = root.dataset.input || 'pointer';     // 'pointer' — мышь и касание; 'scroll' — прогресс прокрутки сцены
    this.p = 0; this.target = 0;            // положение 0…1 (текущее и цель)
    this.lastInput = -1e9; this.userPaused = false; this.visible = true;
    this.variant = null; this.kind = null; this.ready = false; this.raf = 0; this.tPrev = 0;
    this.introUntil = 0; this.driftT0 = 0;
    this.stats = this.freshStats();
    root.__scrub = this;
    try { this.userPaused = sessionStorage.getItem('scrub-paused') === '1'; } catch (e) {}
    this.bind();
  }

  Scrub.prototype.freshStats = function () {
    return {variant: null, kind: null, bytes: 0, loadMs: null, readyAt: null, seeks: 0, coalesced: 0, seekMs: [], decodeMs: [],
            framesLoaded: 0, framesTotal: 0, draws: 0, lag: [], memMB: null, error: null};
  };

  Scrub.prototype.scrollProgress = function () {
    var r = this.root.getBoundingClientRect(), total = r.height - innerHeight;
    return clamp(-r.top / (total > 0 ? total : 1), 0, 1);
  };

  Scrub.prototype.bind = function () {
    var s = this, stage = this.root;
    if (this.mode === 'scroll') {                  // прокрутка ведёт видео: цель = доля пройденной липкой сцены
      addEventListener('scroll', function () { s.input(s.scrollProgress()); }, {passive: true});
      addEventListener('resize', function () { s.input(s.scrollProgress()); });
    }
    // мышь: горизонталь указателя над сценой → цель (края 8 % — «мёртвые»: до них не надо тянуться)
    stage.addEventListener('pointermove', function (e) {
      if (s.mode === 'pointer' && e.pointerType === 'mouse' && FINE.matches) { s.input(clamp(((e.clientX - stage.getBoundingClientRect().left) / stage.clientWidth - 0.08) / 0.84, 0, 1)); }
    });
    // касание и перо: протяжка; вертикальная прокрутка страницы не блокируется (touch-action: pan-y в CSS)
    var drag = null;
    stage.addEventListener('pointerdown', function (e) { if (s.mode === 'pointer' && e.pointerType !== 'mouse') drag = {x: e.clientX, t: s.target}; });
    stage.addEventListener('pointermove', function (e) {
      if (drag && e.pointerType !== 'mouse') s.input(clamp(drag.t + (e.clientX - drag.x) / stage.clientWidth * 1.25, 0, 1));
    });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (ev) { stage.addEventListener(ev, function () { drag = null; }); });
    if (this.range) this.range.addEventListener('input', function () { s.input(Number(s.range.value) / 1000, true); });
    if (this.pauseBtn) this.pauseBtn.addEventListener('click', function () {
      s.userPaused = !s.userPaused;
      try { sessionStorage.setItem('scrub-paused', s.userPaused ? '1' : '0'); } catch (e) {}
      s.syncButton(); s.kick();
    });
    if (this.optIn) this.optIn.addEventListener('click', function () { s.optIn.hidden = true; s.load(s.pickDefault(), true); });
    new IntersectionObserver(function (en) { s.visible = en[0].isIntersecting; s.kick(); }, {threshold: 0}).observe(stage);
    document.addEventListener('visibilitychange', function () { s.kick(); });
    RM.addEventListener('change', function () { s.syncButton(); s.kick(); });
  };

  Scrub.prototype.input = function (v, fromKeyboard) {
    this.target = v; this.lastInput = performance.now(); this.introUntil = 0;
    if (fromKeyboard && RM.matches) this.p = v;     // reduce: без догона — кадр сразу
    // вкладка не на экране (фоновая вкладка, скрытая панель): requestAnimationFrame не идёт — рисуем кадр сразу, без догона
    if (document.visibilityState !== 'visible' && this.ready) { this.p = v; this.drawAt(v, false); return; }
    this.kick();
  };

  Scrub.prototype.pickDefault = function () {
    // по умолчанию: точный указатель — секвенция кадров (0 отставания, смешение соседних кадров), касание — видео AV1 GOP 4
    // (1 файл, 1 кадр в памяти, аппаратный декодер); замер — README галереи
    var want = Q.get('v') || (FINE.matches ? this.root.dataset.default : (this.root.dataset.defaultTouch || this.root.dataset.default));
    if (this.m.video[want] || this.m.frames[want]) {
      if (this.m.video[want] && !document.createElement('video').canPlayType(this.m.video[want].type)) {
        return this.root.dataset.fallback || 'orbit-h264-g4';                    // AV1 не играет → H.264 того же GOP
      }
      return want;
    }
    return Object.keys(this.m.video)[0];
  };

  Scrub.prototype.start = function () {
    if (RM.matches || LOW_DATA) {                    // 0 байт медиа без явного согласия
      if (this.optIn) { this.optIn.hidden = false; var d = this.pickDefault(); var b = (this.m.video[d] || this.m.frames[d]).bytes;
        this.optIn.querySelector('[data-size]').textContent = kb(b); }
      this.root.dataset.state = RM.matches ? 'reduce' : 'save-data';
      return;
    }
    var s = this;
    if (this.root.hasAttribute('data-lazy')) {
      var io = new IntersectionObserver(function (en) { if (en[0].isIntersecting) { io.disconnect(); s.load(s.pickDefault(), false); } },
                                        {rootMargin: this.root.dataset.lazyMargin || '100% 0px'});   // data-lazy-margin: сцену сразу под hero — только когда начали листать
      io.observe(this.root); this.root.dataset.state = 'waiting';
      return;
    }
    this.load(this.pickDefault(), false);
  };

  Scrub.prototype.teardown = function () {
    cancelAnimationFrame(this.raf); this.raf = 0; this.ready = false;
    if (this.video) { this.video.pause(); this.video.removeAttribute('src'); this.video.load(); this.video.remove(); this.video = null; }
    if (this.canvas) { this.canvas.remove(); this.canvas = null; }
    if (this.objectURL) { URL.revokeObjectURL(this.objectURL); this.objectURL = null; }
    (this.bitmaps || []).forEach(function (b) { if (b && b.close) b.close(); });
    this.bitmaps = null; this.poster.style.opacity = '';
    this.seekT0 = null; this.seekingTo = null; this.shownFrame = null; this.wantFrame = null; this.lastFi = null; this.benchOn = false;
  };

  Scrub.prototype.load = function (name, userAsked) {
    var s = this; this.teardown();
    this.variant = name; this.stats = this.freshStats(); this.stats.variant = name;
    this.loadToken = {};
    var token = this.loadToken, t0 = performance.now();
    this.root.dataset.state = 'loading';
    if (this.m.video[name]) {
      var v = this.m.video[name]; this.kind = 'video'; this.stats.kind = 'video';
      var video = document.createElement('video');
      video.muted = true; video.playsInline = true; video.preload = 'auto'; video.setAttribute('aria-hidden', 'true'); video.tabIndex = -1;
      video.className = 'scrub-layer'; this.video = video; this.media.appendChild(video);
      var go = function (src) {
        video.src = src;
        video.addEventListener('loadeddata', function () {
          if (token !== s.loadToken) return;
          s.stats.loadMs = Math.round(performance.now() - t0);
          s.duration = video.duration; s.fps = s.m.fps; s.nFrames = Math.round(video.duration * s.m.fps);
          s.shownFrame = 0; s.ready = true; s.onReady(userAsked);
        }, {once: true});
        video.addEventListener('seeked', function () {
          if (token !== s.loadToken || s.seekT0 == null) return;
          s.stats.seekMs.push(performance.now() - s.seekT0); s.seekT0 = null;
          s.shownFrame = s.seekingTo;
          if (!video.classList.contains('is-on')) { video.classList.add('is-on'); s.poster.style.opacity = '0'; }
          s.kick();
        });
        video.addEventListener('error', function () { s.stats.error = 'media-error'; s.root.dataset.state = 'error'; }, {once: true});
      };
      if (HTTP && window.fetch) {                    // весь файл в память: точная перемотка без сети и без Range у http.server
        fetch(v.src).then(function (r) { return r.blob(); }).then(function (b) {
          if (token !== s.loadToken) return;
          s.stats.bytes = b.size; s.objectURL = URL.createObjectURL(b); go(s.objectURL);
        }).catch(function () { s.stats.bytes = v.bytes; go(v.src); });
      } else { this.stats.bytes = v.bytes; go(v.src); }
      return;
    }
    // ---- секвенция кадров на canvas
    var f = this.m.frames[name]; this.kind = 'frames'; this.stats.kind = 'frames';
    var canvas = document.createElement('canvas'); canvas.width = f.width; canvas.height = f.height; canvas.className = 'scrub-layer';
    canvas.setAttribute('aria-hidden', 'true'); this.canvas = canvas; this.ctx = canvas.getContext('2d', {alpha: false});
    this.media.appendChild(canvas);
    var n = f.count; this.nFrames = n; this.bitmaps = new Array(n); this.stats.framesTotal = n;
    this.stats.memMB = Math.round(n * f.width * f.height * 4 / 1048576);
    // порядок загрузки «грубо → точно»: 0, n-1, середина, четверти… — перемотка работает до полной загрузки
    var order = [], seen = {}, step = n;
    while (step >= 1) { for (var i = 0; i < n; i += step) if (!seen[i]) { seen[i] = 1; order.push(i); } if (!seen[n - 1]) { seen[n - 1] = 1; order.push(n - 1); } step = Math.floor(step / 2); }
    var url = function (i) { return f.pattern.replace('{i}', String(i).padStart(3, '0')); };
    var loadOne = function (i) {
      var td = performance.now();
      var done = function (bmp, bytes) {
        if (token !== s.loadToken) { if (bmp && bmp.close) bmp.close(); return; }
        s.stats.decodeMs.push(performance.now() - td); s.bitmaps[i] = bmp; s.stats.framesLoaded++; s.stats.bytes += bytes || 0;
        if (!s.ready && s.bitmaps[0]) { s.ready = true; s.stats.loadMs = Math.round(performance.now() - t0); s.onReady(userAsked); }
        if (s.stats.framesLoaded === n) s.stats.allMs = Math.round(performance.now() - t0);
        s.kick();
      };
      if (HTTP && window.fetch && window.createImageBitmap) {
        return fetch(url(i)).then(function (r) { return r.blob(); }).then(function (b) {
          td = performance.now(); return createImageBitmap(b).then(function (bmp) { done(bmp, b.size); });
        }).catch(function () { s.stats.error = 'frame ' + i; });
      }
      return new Promise(function (res) {
        var im = new Image(); im.decoding = 'async'; im.src = url(i);
        im.decode().then(function () { done(im, 0); res(); }).catch(function () { s.stats.error = 'frame ' + i; res(); });
      });
    };
    var k = 0, next = function () { if (k >= order.length || token !== s.loadToken) return; loadOne(order[k++]).then(next); };
    for (var c = 0; c < 4; c++) next();          // 4 запроса параллельно
    if (!HTTP) this.stats.bytes = f.bytes;
  };

  Scrub.prototype.onReady = function (userAsked) {
    var s = this;
    this.root.dataset.state = 'live'; this.stats.readyAt = Math.round(performance.now());
    this.p = 0; this.target = 0; this.drawAt(0, true);
    if (this.kind === 'frames') { this.canvas.classList.add('is-on'); this.poster.style.opacity = '0'; }
    // вступление: плавный облёт от кадра 0 к точке покоя — показать, что сцена «живая» (без reduce и без паузы)
    if (this.mode === 'scroll') { this.p = this.target = this.scrollProgress(); this.drawAt(this.p, true); }
    else if (!RM.matches && !this.userPaused && !Q.has('bench')) this.introUntil = performance.now() + 1800;
    this.syncButton(); this.kick();
    if (Q.has('bench')) setTimeout(function () { s.bench(); }, 600);
  };

  // ---------------------------------------------------------------- цикл
  Scrub.prototype.kick = function () {
    var s = this;
    if (!this.raf && this.ready && this.visible && document.visibilityState === 'visible') {
      this.tPrev = performance.now(); this.raf = requestAnimationFrame(function (t) { s.tick(t); });
    }
  };

  Scrub.prototype.drifting = function (now) {
    return this.mode === 'pointer' && !RM.matches && !this.userPaused && now - this.lastInput > 1400 && this.introUntil === 0 && !this.benchOn;
  };

  Scrub.prototype.tick = function (now) {
    var s = this; this.raf = 0;
    var dt = Math.min(0.05, (now - this.tPrev) / 1000); this.tPrev = now;
    if (this.introUntil) {                            // вступление: цель едет от 0 к точке покоя по плавной кривой
      var k0 = clamp(1 - (this.introUntil - now) / 1800, 0, 1);
      this.target = this.rest * (1 - Math.pow(1 - k0, 3));
      if (k0 >= 1) { this.introUntil = 0; this.lastInput = now - 1400; this.driftT0 = now; }
    } else if (this.drifting(now)) {                 // холостой дрейф: медленное «дыхание» вокруг точки покоя
      if (!this.driftT0) this.driftT0 = now;
      var ramp = clamp((now - this.driftT0) / 1500, 0, 1);
      var w = Math.sin((now - this.driftT0) / 1000 * 2 * Math.PI / 11) * 0.26 + Math.sin((now - this.driftT0) / 1000 * 2 * Math.PI / 4.7) * 0.04;
      this.target = clamp(this.rest + w * ramp, 0, 1);
    } else { this.driftT0 = 0; }
    var tau = RM.matches ? 0.02 : 0.16;              // постоянная догона, с: 160 мс — «вязко», но без запаздывания
    this.p += (this.target - this.p) * (1 - Math.exp(-dt / tau));
    if (Math.abs(this.target - this.p) < 1e-4) this.p = this.target;
    this.drawAt(this.p, false);
    this.root.style.setProperty('--p', this.p.toFixed(4));
    if (this.onProgress) this.onProgress(this.p);
    if (this.range && document.activeElement !== this.range) this.range.value = String(Math.round(this.p * 1000));
    if (this.benchOn) this.benchSample();
    var moving = Math.abs(this.target - this.p) > 1e-4 || this.introUntil || this.drifting(now) || this.benchOn || this.seekT0 != null;
    this.syncButton();
    if (moving && this.visible && document.visibilityState === 'visible') this.raf = requestAnimationFrame(function (t) { s.tick(t); });
  };

  Scrub.prototype.drawAt = function (p, force) {
    if (this.kind === 'video') {
      var idx = Math.round(p * (this.nFrames - 1));
      this.wantFrame = idx;
      if (this.seekT0 != null) {                     // перемотка ещё идёт — новую не начинаем, цель запоминаем («слито»)
        if (idx !== this.seekingTo && idx !== this.lastCoalesced) { this.stats.coalesced++; this.lastCoalesced = idx; }
        return;
      }
      if (idx === this.shownFrame && !force) return;
      this.seekT0 = performance.now(); this.seekingTo = idx; this.lastCoalesced = null; this.stats.seeks++;
      this.video.currentTime = (idx + 0.5) / this.fps;   // середина кадра: без «соседнего» кадра из-за округления
      return;
    }
    if (this.kind === 'frames') {
      var fi = p * (this.nFrames - 1), i0 = Math.floor(fi), a = fi - i0;
      if (!force && Math.abs(fi - (this.lastFi == null ? -9 : this.lastFi)) < 0.004) return;
      var j0 = this.nearest(i0), j1 = a > 0.001 ? this.nearest(Math.min(i0 + 1, this.nFrames - 1)) : -1;
      if (j0 < 0) return;
      this.ctx.globalAlpha = 1; this.ctx.drawImage(this.bitmaps[j0], 0, 0, this.canvas.width, this.canvas.height);
      var mixed = j1 >= 0 && j1 !== j0;
      if (mixed) { this.ctx.globalAlpha = a; this.ctx.drawImage(this.bitmaps[j1], 0, 0, this.canvas.width, this.canvas.height); this.ctx.globalAlpha = 1; }
      this.lastFi = fi; this.shownFrame = mixed ? j0 + a * (j1 - j0) : j0; this.stats.draws++;
    }
  };

  Scrub.prototype.nearest = function (i) {       // индекс ближайшего загруженного кадра (пока секвенция догружается)
    var b = this.bitmaps; if (b[i]) return i;
    for (var d = 1; d < b.length; d++) { if (b[i - d]) return i - d; if (b[i + d]) return i + d; }
    return -1;
  };

  Scrub.prototype.syncButton = function () {
    if (!this.pauseBtn) return;
    var show = this.ready && !RM.matches && this.mode === 'pointer';
    this.pauseBtn.hidden = !show;
    if (!show) return;
    var playing = !this.userPaused;
    this.pauseBtn.setAttribute('aria-pressed', String(!playing));
    this.pauseBtn.querySelector('.sr-only').textContent = playing ? 'Остановить движение сцены' : 'Запустить движение сцены';
    this.pauseBtn.querySelector('.i-pause').style.display = playing ? '' : 'none';
    this.pauseBtn.querySelector('.i-play').style.display = playing ? 'none' : '';
  };

  // ---------------------------------------------------------------- замер (?bench=1)
  Scrub.prototype.bench = function () {
    var s = this, t0 = performance.now(), rnd = 17;
    var r = function () { rnd = (rnd * 16807) % 2147483647; return rnd / 2147483647; };
    var jumps = []; for (var k = 0; k < 8; k++) jumps.push(r());
    // 8 с: медленно (слежение) → быстро → дрожь → прыжки (время «догнать») → медленно
    this.benchPath = function (t) {
      if (t < 2) return {seg: 'slow', v: t / 2};
      if (t < 2.6) return {seg: 'fast', v: 1 - (t - 2) / 0.6};
      if (t < 4.1) return {seg: 'jitter', v: 0.5 + 0.06 * Math.sin((t - 2.6) * 40)};
      if (t < 6) { var j = Math.min(7, Math.floor((t - 4.1) / 0.24)); return {seg: 'jump', v: jumps[j], j: j}; }
      return {seg: 'slow', v: Math.min(1, (t - 6) / 2)};
    };
    this.bs = {lag: {slow: [], fast: [], jitter: [], jump: []}, jumpT: {}, settle: []};
    this.stats.seekMs = []; this.stats.seeks = 0; this.stats.coalesced = 0; this.stats.draws = 0;
    this.benchOn = true; this.benchT0 = t0; this.kick();
    setTimeout(function () {
      s.benchOn = false;
      var st = s.stats, L = s.bs.lag, mean = function (a) { return a.length ? +(a.reduce(function (x, y) { return x + y; }, 0) / a.length).toFixed(2) : null; };
      window.__scrubBench = {variant: st.variant, kind: st.kind, bytes: st.bytes, loadMs: st.loadMs, allMs: st.allMs || null,
        seeks: st.seeks, coalesced: st.coalesced, seek_ms_median: median(st.seekMs), seek_ms_p95: pct(st.seekMs, 0.95),
        seek_ms_max: st.seekMs.length ? Math.max.apply(null, st.seekMs) : null,
        decode_ms_median: median(st.decodeMs), decode_ms_p95: pct(st.decodeMs, 0.95),
        lag_slow_mean: mean(L.slow), lag_slow_p95: pct(L.slow, 0.95), lag_fast_mean: mean(L.fast), lag_fast_p95: pct(L.fast, 0.95),
        lag_jitter_mean: mean(L.jitter), jump_settle_ms_median: median(s.bs.settle), jump_settle_ms_max: s.bs.settle.length ? Math.max.apply(null, s.bs.settle) : null,
        jumps_settled: s.bs.settle.length, samples: L.slow.length + L.fast.length + L.jitter.length + L.jump.length,
        frames_loaded: st.framesLoaded, frames_total: st.framesTotal, mem_mb_decoded: st.memMB, error: st.error,
        ua: navigator.userAgent.slice(0, 80)};
      document.documentElement.dataset.bench = 'done';
    }, 8200);
  };

  Scrub.prototype.benchSample = function () {
    var now = performance.now(), t = (now - this.benchT0) / 1000, b = this.bs;
    // сначала — отставание того, что показано сейчас, от цели, выставленной на прошлом кадре экрана
    if (this.benchPrev && this.shownFrame != null) {
      var lag = Math.abs(this.benchPrev.v * (this.nFrames - 1) - this.shownFrame);
      b.lag[this.benchPrev.seg].push(lag);
      if (this.benchPrev.seg === 'jump' && b.jumpT[this.benchPrev.j] && !b.jumpT[this.benchPrev.j].done && lag < 0.51) {
        b.settle.push(now - b.jumpT[this.benchPrev.j].t); b.jumpT[this.benchPrev.j].done = true;
      }
    }
    var cur = this.benchPath(t);
    if (cur.seg === 'jump' && !b.jumpT[cur.j]) b.jumpT[cur.j] = {t: now, done: false};
    this.target = cur.v; this.p = cur.v; this.benchPrev = cur;      // в замере цель = положение: меряем доставку, а не догон
  };

  // ---------------------------------------------------------------- витрина замеров (лаборатория на странице)
  function hud(s, box) {
    if (!box) return;
    var set = function (k, v) { var el = box.querySelector('[data-k="' + k + '"]'); if (el) el.textContent = v; };
    setInterval(function () {
      var st = s.stats;
      set('bytes', st.bytes ? kb(st.bytes) : '—');
      set('load', st.loadMs != null ? st.loadMs + ' мс' : '—');
      if (st.kind === 'video') {
        set('seek', st.seekMs.length ? Math.round(median(st.seekMs)) + ' / ' + Math.round(pct(st.seekMs, 0.95)) + ' мс' : '—');
        set('extra', st.seeks + ' перемоток, ' + st.coalesced + ' слито');
      } else if (st.kind === 'frames') {
        set('seek', st.decodeMs.length ? Math.round(median(st.decodeMs)) + ' / ' + Math.round(pct(st.decodeMs, 0.95)) + ' мс' : '—');
        set('extra', st.framesLoaded + ' из ' + st.framesTotal + ' кадров, ≈ ' + st.memMB + ' МБ в памяти');
      }
      set('state', s.root.dataset.state || '—');
    }, 400);
  }

  window.VelmoraScrub = {
    init: function (root) {
      var man = JSON.parse(document.getElementById(root.dataset.manifest || 'scrub-manifest').textContent);
      var s = new Scrub(root, man);
      hud(s, document.querySelector('[data-scrub-hud]'));
      document.querySelectorAll('input[name="scrub-variant"]').forEach(function (r) {
        if (r.value === s.pickDefault()) r.checked = true;
        r.addEventListener('change', function () { if (r.checked) s.load(r.value, true); });
      });
      var go = function () { (window.requestIdleCallback || function (f) { setTimeout(f, 120); })(function () { s.start(); }, {timeout: 800}); };
      if (document.readyState === 'complete') go(); else addEventListener('load', go, {once: true});
      return s;
    }
  };
  document.querySelectorAll('[data-scrub]').forEach(function (el) { window.VelmoraScrub.init(el); });
})();
