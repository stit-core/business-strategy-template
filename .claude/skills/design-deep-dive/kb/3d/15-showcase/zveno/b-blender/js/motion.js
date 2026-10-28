/* effect:motion-toggle · motion.js ≈ 1 КБ br с комментариями · Chromium 153 / WebKit 26.6
   Переключатель «меньше движения» (L2 — CRV-AL-12) и единая пауза всех петель (WCAG 2.2.2), по creative 05/01 §4.4:
   <html data-motion>: нет атрибута — как в системе; "reduced" — меньше; "full" — полное вопреки ОС (выбор побеждает ОС в обе стороны).
   Выбор — localStorage("motion"), ставится строкой в <head> до первой отрисовки; меняется без перезагрузки.
   CSS слушает атрибут (токены --mm-* и [data-loop]); JS-движение подписывается: Motion.on(function (reduced, pref) {…}). */
(function () {
  var root = document.documentElement, KEY = 'motion', mq = matchMedia('(prefers-reduced-motion: reduce)'), subs = [], box, now;
  function pref() { var m = root.dataset.motion; return m === 'reduced' || m === 'full' ? m : 'system'; }
  function reduced() { var p = pref(); return p === 'reduced' || (p === 'system' && mq.matches); }
  function render() {
    if (!box) return;
    var p = pref(), r = reduced(), inp = box.querySelector('input[value="' + p + '"]');
    if (inp) inp.checked = true;
    if (now) now.textContent = (r ? 'меньше' : 'полное') + (p === 'system' ? ' · как в системе' : ' · ваш выбор');
  }
  function emit() { var r = reduced(), p = pref(); render(); for (var i = 0; i < subs.length; i++) { try { subs[i](r, p); } catch (e) { console.error(e); } } }
  function set(p) {
    if (p === 'reduced' || p === 'full') root.dataset.motion = p; else delete root.dataset.motion;
    try { if (p === 'reduced' || p === 'full') localStorage.setItem(KEY, p); else localStorage.removeItem(KEY); } catch (e) {}
    emit();
  }
  function bind() {
    box = document.querySelector('.mt'); if (!box) return;
    now = box.querySelector('.mt__now');
    box.addEventListener('change', function (e) { if (e.target && e.target.name === 'motion') set(e.target.value); });
    render();
  }
  mq.addEventListener('change', emit);                       // смена настройки ОС на лету — тоже без перезагрузки
  window.Motion = { reduced: reduced, pref: pref, set: set,
    on: function (fn) { subs.push(fn); try { fn(reduced(), pref()); } catch (e) { console.error(e); } } };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind); else bind();
})();
