/* hero-video.js — видео-слой hero поверх картинки-постера (канон — ai-media `10-web-integration/pages/js/hero-video.js`, переписан
   обычным скриптом, чтобы работал и с file://).
   1) LCP — <picture> (кадр 0 финального видео); видео грузится только после load + простоя;
   2) reduce, Save-Data, 2G → видео не запрашивается (0 байт), остаётся постер;
   3) источники — по data-media (телефону 4:5, десктопу 16:9) и canPlayType (AV1 первым, H.264 запасом);
   4) подмена постера видео — по первому показанному кадру (requestVideoFrameCallback), без мигания;
   5) кнопка паузы (WCAG 2.2.2, петля дольше 5 с), выбор помнится в sessionStorage; пауза вне экрана и в скрытой вкладке. */
(function () {
  'use strict';
  var RM = matchMedia('(prefers-reduced-motion: reduce)');
  var conn = navigator.connection || {};
  var LOW_DATA = conn.saveData === true || /(^|-)2g$/.test(conn.effectiveType || '');

  function pickSources(video) {
    var out = [];
    video.querySelectorAll('source[data-src]').forEach(function (s) {
      var m = s.dataset.media;
      if (m && !matchMedia(m).matches) return;
      if (s.type && !video.canPlayType(s.type)) return;
      out.push(s);
    });
    return out;
  }

  function heroVideo(root) {
    var video = root.querySelector('video[data-video]'), btn = root.querySelector('.motion-toggle, .media-toggle');
    if (!video) return;
    var key = 'hero-video-paused:' + (root.id || 'hero');
    var userPaused = false, visible = true, started = false;
    try { userPaused = sessionStorage.getItem(key) === '1'; } catch (e) {}
    var setBtn = function (playing) {
      if (!btn) return;
      btn.hidden = !started || RM.matches;
      btn.setAttribute('aria-pressed', String(!playing));
      var sr = btn.querySelector('.sr-only'); if (sr) sr.textContent = playing ? 'Остановить фоновое видео' : 'Запустить фоновое видео';
      var ip = btn.querySelector('.i-pause'), pl = btn.querySelector('.i-play');
      if (ip) ip.style.display = playing ? '' : 'none'; if (pl) pl.style.display = playing ? 'none' : '';
    };
    var shouldPlay = function () { return started && !userPaused && visible && !RM.matches && document.visibilityState === 'visible'; };
    var sync = function () {
      if (!started) return;
      if (shouldPlay()) { var p = video.play(); if (p && p.catch) p.catch(function () {}); } else video.pause();
      root.classList.toggle('is-video', !RM.matches && root.dataset.shown === '1');
      setBtn(shouldPlay());
    };
    var start = function () {
      if (started || RM.matches || LOW_DATA) { if (RM.matches || LOW_DATA) root.dataset.videoState = RM.matches ? 'reduce' : 'save-data'; return; }
      var chosen = pickSources(video);
      if (!chosen.length) { root.dataset.videoState = 'no-codec'; return; }
      video.querySelectorAll('source').forEach(function (s) { s.remove(); });
      chosen.forEach(function (s) { var n = document.createElement('source'); n.src = s.dataset.src; if (s.type) n.type = s.type; video.appendChild(n); });
      video.preload = 'auto'; video.load(); started = true; root.dataset.videoState = 'loading';
      var reveal = function () { root.dataset.shown = '1'; root.dataset.videoState = 'playing'; sync(); };
      if ('requestVideoFrameCallback' in video) video.requestVideoFrameCallback(reveal);
      else video.addEventListener('playing', reveal, {once: true});
      sync();
    };
    if (btn) btn.addEventListener('click', function () {
      userPaused = !userPaused;
      try { sessionStorage.setItem(key, userPaused ? '1' : '0'); } catch (e) {}
      sync();
    });
    new IntersectionObserver(function (en) { visible = en[0].isIntersecting; sync(); }, {threshold: 0}).observe(root);
    document.addEventListener('visibilitychange', sync);
    RM.addEventListener('change', function () { if (!RM.matches) start(); sync(); });
    var idle = window.requestIdleCallback || function (f) { return setTimeout(f, 200); };
    var go = function () { idle(start, {timeout: 1500}); };
    if (document.readyState === 'complete') go(); else addEventListener('load', go, {once: true});
    root.__heroVideo = {video: video, sync: sync};
  }

  window.VelmoraHeroVideo = heroVideo;
  document.querySelectorAll('[data-hero-video]').forEach(heroVideo);
})();
