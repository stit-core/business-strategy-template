#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motion_check.py — цикл проверки сборки: запись → кадры → метрики → сверка с motion-spec → ворота эффектов → отчёт.

Playwright (Chromium), ffmpeg, numpy, Pillow, PyYAML. VLM движения не видит: скриншот — конечное состояние. Здесь движение
проверяется поведением страницы во времени. Код репозитория запускает утилиту соседним чекаутом:
../strategy/.claude/skills/design-deep-dive/scripts/creative/motion_check.py.

Режимы (каждый — отдельный браузер на тихой машине, партия ≤ 5 мин; анализ видео — после снятия замков):
  desk  Chromium 1440×900, DPR 1, запись 960×600: сеть по фазам (первый экран = load + окно первого экрана budgets.yaml site,
        сессия = после прокрутки), LCP (элемент, H1 выпал из LCP), CLS загрузки и прокрутки, TBT, LoAF и rAF при
        прокрутке, хвост прокрутки, перехват прокрутки (путь колеса), движение на 6-й секунде, прелоадер или входной экран
        (заставка на весь экран в первые секунды: «Пропустить», длительность), петли в видимой зоне по паузам, петли под
        читаемым текстом, бегущая строка (px/с), колебания крупных и мелких объектов, петли через 6 с после показа, кнопка
        паузы (нажать → стоит ли), переключатель «меньше движения» (атрибут data-motion: reduced | full | paused), WebGL
        (контексты, вызовы отрисовки в покое), CDN, Tab-проход (кольцо, фокус на экране и видим), вспышки WCAG 2.3.1 покадрово
        25 к/с, «вау»-переходы, контактные листы.
  mob   телефон (дескриптор и CPU — budgets.yaml conditions.lab_mobile; UA — HeadlessChrome): то же без Tab; ширина документа.
  rm    desk с prefers-reduced-motion: reduce: байты видео, движение первого экрана и по всей записи, бесконечные анимации,
        вызовы WebGL в покое, скрытое до прокрутки, загружены ли библиотеки эффектов.
  nojs  JavaScript выключен: H1, текст и призыв видны, кадр не пуст.
  nogl  --disable-webgl --disable-webgl2: первый экран не пуст, H1 виден, ошибки консоли.

Пороги ворот (effect-gates.yaml): число строки, поле limits строки или threshold_ref — ссылка на данные владельца величины:
путь в уровне ambition-levels.yaml (budgets.effects.*, motion_hints.*), `profile.<путь>` — профиль страницы site
(budgets.yaml через page_gates.py; с --page-type — профиль <page_type>@<уровень> с исключениями, иначе уровень), метка
<device> — устройство режима; `effects.yaml#<id>.<путь>` — запись каталога эффектов. Метрики страницы (LCP, TBT, вес,
шрифты) в воротах эффектов — зеркало D: вердикт им ставят ворота страницы site.
Отчёт: слой подачи по режимам (JS эффектов, JS и wasm 3D — EG-WEIGHT-02, wasm-рантаймы подачи 2D — EG-WEIGHT-11, видео
первого экрана) против одного порога уровня (EG-WEIGHT-01), картинка первого экрана — ссылкой на бюджет ассета ai-media.
Подписи механизма паузы (кнопка, переключатель, выбор) — общий список page_gates.PAUSE_LABELS.

Использование:
  motion_check.py ЦЕЛЬ --level L0|L1|L2 [--page-type landing-saas] [--out DIR] [--modes desk,mob,rm,nojs,nogl]
          [--spec motion-spec.yaml] [--gates effect-gates.yaml] [--steps 12] [--dwell 1.8] [--wait МС] [--no-lock]
          [--keep-video] [--no-video] [--effects-js REGEX] [--f83 "h1" ".lead"] [--contrast SEL …] [--root DIR]
  motion_check.py report --in DIR [--level L1] [--gates FILE]   # пересчёт ворот по сохранённому results.json
  motion_check.py --selftest                                     # без браузера
ЦЕЛЬ — URL или локальный файл/папка (раздаётся встроенным сервером с Range; вес текста — brotli q11 по файлу).
--wait — окно первого экрана после load, мс (по умолчанию — budgets.yaml conditions.first_screen.window_after_load_s).
Выход DIR (по умолчанию $DDD_HOME/out/creative/motion/<цель>): results.json (все метрики по режимам), gates.md (ворота:
правило → найдено → порог → где; слой подачи), gates.json (строки ворот, слой подачи), fix.txt (блок для промта правки),
spec.md (сверка с motion-spec, если --spec), sheet_<режим>_NN.jpg.
Код выхода: 0 — нет FAIL уровня B; 1 — есть B (или --fail-on serious и есть S); 2 — ошибка запуска.

Контракт DOM для целей motion-spec: секция — data-section="<id>" или id="<id>", слот — data-slot, экземпляр группы —
data-group, элемент момента — data-moment="<id момента>"; иначе selector_hint.
Станции скраба: край цели минус линия окна, округление до целого (половина — от нуля), допуск ±tolerance_px включительно
(motion-spec.schema.json $defs.station).
Ограничения: headless (rAF ≤ 60 кадров/с, эмуляция ≠ телефон), колесо мыши, а не тач; INP не мерится (сценарий site);
скринкаст Playwright ≤ 25 к/с — вспышки чаще 12 Гц не видны; GSAP без глобала не виден в getAnimations (длительность
моментов меряется выборкой стилей цели); WebKit не поддержан.
"""
from __future__ import annotations

import argparse
import base64
import functools
import http.server
import io
import json
import math
import mimetypes
import os
import re
import shutil
import socketserver
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlparse, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lib"))  # scripts/lib
import kbpaths  # noqa: E402
kbpaths.use("site")
import page_gates as PG  # noqa: E402  профиль страницы, условия замера, тишина машины
ROOT = str(kbpaths.kb("creative"))
GATES_DEFAULT = os.path.join(ROOT, "09-ai-execution-evaluation", "effect-gates.yaml")
LEVELS_YAML = os.path.join(ROOT, "01-creative-direction", "ambition-levels.yaml")
EFFECTS_YAML = os.path.join(ROOT, "06-effects-catalog", "effects.yaml")
AI_THRESHOLDS = str(kbpaths.kb("ai-media", "11-evaluation-qa", "thresholds.yaml"))
VERSION = "motion_check.py 0.2"
GPU_ARGS = ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"]
NOGL_ARGS = ["--disable-webgl", "--disable-webgl2"]
TEXT_EXT = {".html", ".htm", ".css", ".js", ".mjs", ".json", ".svg", ".txt", ".vtt", ".glsl", ".xml", ".map"}
CDN_HOSTS = ("cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com", "esm.sh", "cdn.skypack.dev", "ga.jspm.io", "jspm.dev",
             "unicorn.studio", "cdn.unicorn.studio", "prod.spline.design", "unpkg.co", "cdn.jsdelivr.com")
EFFECT_JS_RE = (r"gsap|greensock|ScrollTrigger|SplitText|ScrollSmoother|lenis|locomotive|motion(\.|-|/)|framer|three|\bogl\b|pixi|"
                r"lottie|rive|spline|unicorn|barba|swup|theatre|curtains|anime(js)?|split-?type|splitting|/effects?/|/fx/|effect[-_]")
THREE_D_RE = r"three|\bogl\b|pixi|babylon|spline|unicorn|playcanvas|@react-three|drei|model-viewer"
WASM_3D_RE = THREE_D_RE + r"|draco|basis|meshopt|ktx"   # wasm 3D-рантаймов и декодеров; прочий wasm — рантаймы подачи (dotLottie, Rive)
# библиотеки по содержимому файла (бандл с «немым» именем — scene.js с three) — строки из кода самих библиотек, а не из
# кода, который их зовёт (загрузчик с путём «lenis.min.js» библиотекой не считается)
SNIFF_3D = re.compile(rb"__THREE__|@splinetool|UnicornStudio|BABYLON\.Engine|pixi\.js - v|PIXI\.Application|@react-three/fiber")
SNIFF_FX = re.compile(rb"GreenSock|pin-spacer|lenis-smooth|data-lenis-prevent|bodymovin|@rive-app|rive\.wasm|has-scroll-smooth|@barba/core|anime\.js v")
MOTION_VALUES = ("reduced", "full", "paused")   # значения data-motion на корне (creative 05-motion/01 §4.4)
for _e, _t in {".woff2": "font/woff2", ".avif": "image/avif", ".webm": "video/webm", ".mp4": "video/mp4", ".mjs": "text/javascript",
               ".js": "text/javascript", ".json": "application/json", ".webp": "image/webp", ".svg": "image/svg+xml", ".glb": "model/gltf-binary",
               ".wasm": "application/wasm", ".lottie": "application/zip", ".riv": "application/octet-stream"}.items():
    mimetypes.add_type(_t, _e)

try:
    import scroll_record as SR   # read_frames, diff_regions, find_flash, sheet
except Exception:  # pragma: no cover
    SR = None

# =====================================================================================================================
# 1. Инструментирование страницы (до любых скриптов)
# =====================================================================================================================
INIT = r"""
(() => {
  if (window.__mc) return;
  const M = window.__mc = {lcp: [], cls: [], lt: [], loaf: [], raf: [], rafOn: false, gl: {ctx: 0, calls: 0, canv: []}, h1op: [], err: [], phase: 'load', samp: {}};
  const po = (type, fn) => { try { new PerformanceObserver(l => l.getEntries().forEach(fn)).observe({type, buffered: true}); } catch (e) {} };
  const selOf = (el) => { if (!el || !el.tagName) return ''; const id = el.id ? '#' + el.id : '';
    const c = (typeof el.className === 'string' && el.className.trim()) ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
    return (el.tagName.toLowerCase() + id + c).slice(0, 70); };
  M.selOf = selOf;
  po('largest-contentful-paint', e => { const el = e.element;
    M.lcp.push({t: Math.round(e.startTime), size: e.size, tag: el ? el.tagName : null, sel: selOf(el), url: (e.url || '').slice(-80),
                isH1: !!(el && (el.tagName === 'H1' || (el.closest && el.closest('h1'))))}); });
  const R4 = (x) => x ? [Math.round(x.x), Math.round(x.y), Math.round(x.width), Math.round(x.height)] : null;
  const nodeOf = (n) => !n ? null : (n.nodeType === 1 ? selOf(n) : '#text:' + (n.textContent || '').trim().slice(0, 24));
  po('layout-shift', e => { if (!e.hadRecentInput) M.cls.push({t: Math.round(e.startTime), v: e.value, ph: M.phase,
      src: (e.sources || []).slice(0, 2).map(s => selOf(s.node)),
      mv: (e.sources || []).slice(0, 3).map(s => ({n: nodeOf(s.node), f: R4(s.previousRect), c: R4(s.currentRect)}))}); });
  po('longtask', e => M.lt.push({t: Math.round(e.startTime), d: Math.round(e.duration), ph: M.phase}));
  po('long-animation-frame', e => M.loaf.push({t: Math.round(e.startTime), d: Math.round(e.duration), b: Math.round(e.blockingDuration || 0), ph: M.phase}));
  po('paint', e => { if (e.name === 'first-contentful-paint') M.fcp = Math.round(e.startTime); });
  const tick = (t) => { if (M.rafOn) M.raf.push(t); requestAnimationFrame(tick); }; requestAnimationFrame(tick);
  try {
    const orig = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, ...a) {
      const ctx = orig.call(this, type, ...a);
      if (ctx && /webgl/i.test(String(type)) && !ctx.__mc) { ctx.__mc = 1; M.gl.ctx++; M.gl.canv.push(this);
        for (const fn of ['drawArrays', 'drawElements', 'drawArraysInstanced', 'drawElementsInstanced', 'drawRangeElements']) {
          const o = ctx[fn]; if (typeof o === 'function') ctx[fn] = function (...x) { M.gl.calls++; this.canvas.__mcCalls = (this.canvas.__mcCalls || 0) + 1; return o.apply(this, x); }; } }
      return ctx; };
  } catch (e) {}
  const h1s = () => { const h = document.querySelector('h1'); if (!h) return; let o = 1, n = h; while (n && n.nodeType === 1) { o *= parseFloat(getComputedStyle(n).opacity); n = n.parentElement; }
    const r = h.getBoundingClientRect(); M.h1op.push({t: Math.round(performance.now()), o: Math.round(o * 1000) / 1000, top: Math.round(r.top), h: Math.round(r.height)}); };
  document.addEventListener('DOMContentLoaded', () => { let k = 0; const f = () => { h1s(); if (++k < 60) requestAnimationFrame(f); }; requestAnimationFrame(f); });
  // прелоадер или входной экран: слой position: fixed на ≥ 90 % окна в первые 8 с после DOMContentLoaded (не баннер
  // cookie); время показа и видимая «Пропустить» внутри слоя
  M.intro = null;
  const introEl = () => { try { const IW = innerWidth, IH = innerHeight; let el = document.elementFromPoint(IW / 2, IH / 2);
      while (el && el !== document.body && el !== document.documentElement) { const cs = getComputedStyle(el);
        if (cs.position === 'fixed') { const r = el.getBoundingClientRect();
          if (r.width >= 0.9 * IW && r.height >= 0.9 * IH && parseFloat(cs.opacity) >= 0.5 && cs.visibility !== 'hidden'
              && !/cookie|куки|consent|соглас/i.test(el.innerText || '')) return el; }
        el = el.parentElement; } } catch (e) {} return null; };
  document.addEventListener('DOMContentLoaded', () => { const t0 = performance.now(); const f = () => { const el = introEl();
      const t = Math.round(performance.now());
      if (el) { const s = selOf(el); if (!M.intro) M.intro = {sel: s, t_first: t, t_last: t, skip: false, skip_t: null};
        if (M.intro.sel === s) { M.intro.t_last = t;
          if (!M.intro.skip) { const b = [...el.querySelectorAll('button, a, [role=button]')].find(x => { const r = x.getBoundingClientRect();
              const cs = getComputedStyle(x); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.5
                && /пропуст|skip|далее|войти|enter/i.test((x.innerText || x.getAttribute('aria-label') || '').trim()); });
            if (b) { M.intro.skip = true; M.intro.skip_t = t; } } } }
      if (performance.now() - t0 < 8000) requestAnimationFrame(f); }; requestAnimationFrame(f); });
  window.addEventListener('error', e => M.err.push(String(e.message || e).slice(0, 140)));
  // выборка стилей целей моментов (сверка с motion-spec): M.watch(key, selector, ms)
  M.watch = (key, sel, ms) => { const el = document.querySelector(sel); if (!el) { M.samp[key] = {missing: true}; return false; }
    const rec = M.samp[key] = {t0: performance.now(), s: []};
    const f = (t) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
      rec.s.push([Math.round(t - rec.t0), parseFloat(cs.opacity), cs.transform, cs.clipPath, cs.filter, Math.round(r.top), Math.round(r.left)]);
      if (t - rec.t0 < ms) requestAnimationFrame(f); }; requestAnimationFrame(f); return true; };
})();
"""

SNAP_JS = r"""
(opts) => {
  const M = window.__mc || {}; const IH = innerHeight, IW = innerWidth; const sel = M.selOf || (e => e.tagName);
  const inV = (r) => r.bottom > 0 && r.top < IH && r.right > 0 && r.left < IW && r.width >= 24 && r.height >= 24;
  const out = {y: Math.round(scrollY), docH: Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0), IH, IW};
  const loops = []; let running = 0, infinite = 0;
  try { for (const a of document.getAnimations()) { if (a.playState === 'running') running++; let t = {}; try { t = a.effect.getTiming(); } catch (e) {}
      if (t.iterations !== Infinity || a.playState !== 'running') continue; infinite++;
      const tg = a.effect && a.effect.target; if (!tg || !tg.getBoundingClientRect) continue; const r = tg.getBoundingClientRect();
      let props = []; try { const s = new Set(); a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if (!['offset','easing','composite','computedOffset'].includes(p)) s.add(p); })); props = [...s]; } catch (e) {}
      loops.push({k: 'anim', sel: sel(tg), name: a.animationName || '', r: [r.left, r.top, r.width, r.height], dur: t.duration, dir: t.direction, props, vis: inV(r),
                  cta: !!(tg.closest && tg.closest('a, button')), el: tg}); } } catch (e) {}
  document.querySelectorAll('video').forEach(v => { const r = v.getBoundingClientRect(); if (!v.paused && !v.ended && v.readyState > 2)
    loops.push({k: 'video', sel: sel(v), r: [r.left, r.top, r.width, r.height], vis: inV(r), dur: isFinite(v.duration) ? v.duration * 1000 : null, loop: v.loop, el: v}); });
  (M.gl && M.gl.canv || []).forEach(c => { const r = c.getBoundingClientRect(); const calls = c.__mcCalls || 0; const d = calls - (c.__mcPrev || 0); c.__mcPrev = calls;
    if (d > 0) loops.push({k: 'webgl', sel: sel(c), r: [r.left, r.top, r.width, r.height], vis: inV(r), dc: d, el: c}); });
  const vis = loops.filter(l => l.vis);
  // объекты, а не области: слить пересекающиеся и соседние в одной полосе (две дорожки бегущей строки — один объект)
  const objs = [];
  for (const l of vis) { const [x, y, w, h] = l.r; let m = null;
    for (const o of objs) { const [ox, oy, ow, oh] = o.r; const vov = Math.max(0, Math.min(y + h, oy + oh) - Math.max(y, oy)) / Math.min(h, oh);
      const gap = Math.max(ox - (x + w), x - (ox + ow)); const inside = x >= ox - 2 && y >= oy - 2 && x + w <= ox + ow + 2 && y + h <= oy + oh + 2;
      if (inside || (vov >= 0.6 && gap <= 40)) { m = o; break; } }
    if (m) { const [ox, oy, ow, oh] = m.r; const nx = Math.min(ox, x), ny = Math.min(oy, y); m.r = [nx, ny, Math.max(ox + ow, x + w) - nx, Math.max(oy + oh, y + h) - ny]; m.parts.push(l.sel); m.els.push(l.el); }
    else objs.push({r: [x, y, w, h], parts: [l.sel], k: l.k, els: [l.el]}); }
  // текст на скриме (свой фон с альфой ≥ 0,6 или backdrop-filter у текста или предка, не содержащего петлю) — петля его не
  // «читает» (E 05/01 §5.3: лид под заголовком — на скриме)
  const scrimmed = (el, loopEls) => { let n = el;
    for (let d = 0; n && n !== document.body && d < 8; d++, n = n.parentElement) {
      if (loopEls.some(le => le && n.contains(le))) break;
      const cs = getComputedStyle(n); const m = (cs.backgroundColor || '').match(/[\d.]+/g); const al = !m ? 0 : (m.length > 3 ? parseFloat(m[3]) : 1);
      if (al >= 0.6 || (cs.backdropFilter && cs.backdropFilter !== 'none')) return true; }
    return false; };
  const texts = Array.from(document.querySelectorAll('p, li, blockquote, figcaption, dd, label')).filter(el => {
      const t = (el.innerText || '').trim(); if (t.length < 60) return false; const cs = getComputedStyle(el);
      if (parseFloat(cs.fontSize) > 24 || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.5) return false; return inV(el.getBoundingClientRect()); }).slice(0, 80);
  const under = [];
  for (const o of objs) { const [x, y, w, h] = o.r; if (w * h > IW * IH * 0.98 && o.k !== 'video' && o.k !== 'webgl') continue;
    for (const el of texts) { if (scrimmed(el, o.els || [])) continue;
      const r = el.getBoundingClientRect(); const ix = Math.max(0, Math.min(x + w, r.right + 24) - Math.max(x, r.left - 24));
      const iy = Math.max(0, Math.min(y + h, r.bottom + 24) - Math.max(y, r.top - 24));
      if (ix * iy >= 0.10 * r.width * r.height) { under.push(o.parts[0] + ' под «' + (el.innerText || '').trim().slice(0, 30) + '»'); break; } } }
  out.loops = objs.length; out.loopList = objs.slice(0, 8).map(o => o.k + ':' + o.parts.slice(0, 2).join('+')); out.under = under.slice(0, 4);
  out.loopsAll = loops.map(l => ({k: l.k, sel: l.sel, vis: l.vis, dur: l.dur, dir: l.dir, props: l.props, cta: l.cta, w: Math.round(l.r[2]), h: Math.round(l.r[3]), name: l.name, dc: l.dc}));
  out.running = running; out.infinite = infinite;
  return out;
}
"""

# сброс счётчиков WebGL перед окном покоя — кадры, нарисованные при прокрутке и в хвосте сглаживания скраба, не петля
PRIME_JS = "() => { const M = window.__mc || {}; (M.gl && M.gl.canv || []).forEach(c => { c.__mcPrev = c.__mcCalls || 0; }); return true; }"

# замер движения для теста переключателя: 'prime' — отметка; иначе — вызовы WebGL с отметки, бесконечные, видео, атрибут
MEASURE_JS = r"""
(a) => { const M = window.__mc || {}; const now = performance.now();
  if (a === 'prime') { (M.gl && M.gl.canv || []).forEach(c => { c.__mcT = c.__mcCalls || 0; }); window.__mcTT = now; return null; }
  let calls = 0; (M.gl && M.gl.canv || []).forEach(c => { calls += (c.__mcCalls || 0) - (c.__mcT || 0); });
  let inf = 0; try { inf = document.getAnimations().filter(x => x.playState === 'running' && x.effect && x.effect.getTiming().iterations === Infinity).length; } catch (e) {}
  const vids = [...document.querySelectorAll('video')].filter(v => !v.paused && !v.ended).length;
  let lab = null; try { lab = (window.LAB && window.LAB.info) ? JSON.parse(JSON.stringify(window.LAB.info)) : null; } catch (e) {}
  return {webgl_calls: calls, window_ms: Math.round(now - (window.__mcTT || now)), infinite: inf, videos_playing: vids,
          motion_attr: document.documentElement.getAttribute('data-motion'), lab}; }
"""

# нажать элемент по пути (radio, button, switch, checkbox) или выбрать значение select
CLICK_JS = r"""
(o) => { let el = null; try { el = document.querySelector(o.path); } catch (e) {} if (!el) return false;
  if (o.kind === 'select') { el.value = o.value; el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); return true; }
  el.click(); return true; }
"""

PAGE_JS = r"""
(opts) => {
  const M = window.__mc || {}; const IH = innerHeight, IW = innerWidth; const sel = M.selOf || (e => e.tagName);
  const effOp = (el) => { let o = 1, n = el, d = 0; while (n && n.nodeType === 1 && d < 40) { o *= parseFloat(getComputedStyle(n).opacity); n = n.parentElement; d++; } return o; };
  const ownText = (el) => Array.from(el.childNodes).filter(n => n.nodeType === 3 && n.textContent.trim()).map(n => n.textContent.trim()).join(' ');
  const all = Array.from(document.body ? document.body.getElementsByTagName('*') : []).slice(0, 8000);
  let textBelow = 0, hiddenBelow = 0; const hidEx = []; let textAll = 0, hiddenAll = 0;
  for (const el of all) { const t = ownText(el); if (t.length < 3) continue; const cs = getComputedStyle(el); if (cs.display === 'none') continue;
    const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue; textAll++;
    const hid = effOp(el) < 0.05 || cs.visibility === 'hidden';
    if (hid) hiddenAll++;
    if (r.top + scrollY >= IH) { textBelow++; if (hid) { hiddenBelow++; if (hidEx.length < 5) hidEx.push(sel(el)); } } }
  const h1 = document.querySelector('h1'); let h1i = null;
  if (h1) { const r = h1.getBoundingClientRect(); h1i = {sel: sel(h1), text: (h1.innerText || '').trim().slice(0, 80), top: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height),
    area: Math.round(r.width * r.height), op: Math.round(effOp(h1) * 100) / 100, first: r.top + scrollY < IH}; }
  const cta = Array.from(document.querySelectorAll('a, button')).filter(el => { const r = el.getBoundingClientRect(); const t = (el.innerText || '').trim();
      return t.length >= 2 && r.top + scrollY < IH && r.width >= 40 && r.height >= 20 && effOp(el) > 0.5 && getComputedStyle(el).visibility !== 'hidden'; }).length;
  const ctrlRe = __PAUSE_RE__; const txt = (el) => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
  const cssPath = (el) => { const esc = (s) => (window.CSS && CSS.escape) ? CSS.escape(s) : s; const parts = []; let n = el;
    while (n && n.nodeType === 1 && n !== document.documentElement) {
      if (n.id && document.querySelectorAll('#' + esc(n.id)).length === 1) { parts.unshift('#' + esc(n.id)); return parts.join(' > '); }
      let i = 1, s = n; while ((s = s.previousElementSibling)) if (s.tagName === n.tagName) i++;
      parts.unshift(n.tagName.toLowerCase() + ':nth-of-type(' + i + ')'); n = n.parentElement; }
    return parts.join(' > '); };
  const labText = (el) => { const labs = el.labels ? Array.from(el.labels).map(txt).join(' ') : ''; const wrap = el.closest('label') ? txt(el.closest('label')) : '';
    const lb = (el.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean).map(id => { const x = document.getElementById(id); return x ? txt(x) : ''; }).join(' ');
    return [el.getAttribute('aria-label') || '', txt(el), el.title || '', labs, wrap, lb].join(' '); };
  const shownC = (el) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect(); return !(cs.display === 'none' || cs.visibility === 'hidden' || r.width < 1); };
  const shownOrLabel = (el) => shownC(el) || !!(el.labels && Array.from(el.labels).some(shownC));
  const box = (el) => { const r = el.getBoundingClientRect(); return {w: Math.round(r.width), h: Math.round(r.height)}; };
  const pause = Array.from(document.querySelectorAll('button, [role=button], [role=switch], input[type=checkbox], [aria-pressed], [data-motion-toggle]')).filter(el => {
      if (!shownOrLabel(el)) return false;
      return el.hasAttribute('data-motion-toggle') || ctrlRe.test(labText(el)); }).map(el => ({sel: sel(el), ...box(el), kind: 'button', path: cssPath(el)}));
  // переключатель «Движение» — радиогруппа, select или кнопки [data-motion-set]; варианты «меньше» / «полное» / «как в системе»
  // (кириллица и \b в JS без флага u не дружат — границы слов только у латиницы)
  const RED = /(меньш|пауз|останов|стоп|выкл|без движ|reduc|less|\boff\b|pause|stop|\bnone\b|minimal)/i,
        FULL = /(полн|больш|вкл|full|more|\bon\b|\ball\b|max)/i, SYS = /(систем|system|auto|авто|умолч|default)/i;
  let mctrl = null;
  const uw = (s) => Array.from(new Set(String(s || '').split(/\s+/).filter(Boolean))).join(' ');   // «Остановить Остановить» → одно слово
  const opt = (el, kind, lab, value) => ({path: cssPath(el), label: uw(lab).slice(0, 40), value: value || '', kind});
  const groups = new Map();
  document.querySelectorAll('input[type=radio], [role=radio], [role=menuitemradio]').forEach(el => {
    const g = el.closest('[role=radiogroup], fieldset'); const key = el.name ? 'n:' + el.name : (g ? 'g:' + cssPath(g) : 'x:' + cssPath(el));
    if (!groups.has(key)) groups.set(key, {g, name: el.name || '', els: []}); groups.get(key).els.push(el); });
  for (const G of groups.values()) { const g = G.g;
    const ctx = [g && g.querySelector('legend') ? txt(g.querySelector('legend')) : '', g ? (g.getAttribute('aria-label') || '') : '', G.name].join(' ');
    if (!ctrlRe.test(ctx) && !G.els.some(e => e.hasAttribute('data-motion-set'))) continue;
    const opts = G.els.filter(shownOrLabel).map(el => ({el, lab: labText(el) + ' ' + (el.value || '') + ' ' + (el.getAttribute('data-motion-set') || '')}));
    // вариант с data-motion-set узнаётся по значению контракта (reduced | full; «как в системе» — пусто или system), без
    // него — по подписи
    const pick = (re, v) => { const o = opts.find(x => x.el.hasAttribute('data-motion-set') ? v.includes((x.el.getAttribute('data-motion-set') || '').trim()) : re.test(x.lab));
      return o ? opt(o.el, 'radio', labText(o.el), o.el.value) : null; };
    const red = pick(RED, ['reduced']); if (!red) continue;
    mctrl = {kind: 'radio', reduce: red, full: pick(FULL, ['full']), system: pick(SYS, ['', 'system']), group: ctx.trim().slice(0, 40)}; break; }
  if (!mctrl) for (const s of document.querySelectorAll('select')) { if (!shownOrLabel(s) || !ctrlRe.test(labText(s) + ' ' + (s.name || ''))) continue;
    const os = Array.from(s.options).map(o => ({o, lab: (o.text || '') + ' ' + (o.value || '')}));
    const pick = (re) => { const x = os.find(y => re.test(y.lab)); return x ? opt(s, 'select', x.o.text, x.o.value) : null; };
    const red = pick(RED); if (!red) continue; mctrl = {kind: 'select', reduce: red, full: pick(FULL), system: pick(SYS), group: labText(s).trim().slice(0, 40)}; break; }
  if (!mctrl) { const sets = Array.from(document.querySelectorAll('[data-motion-set]')).filter(shownC);
    const pick = (v) => { const b = sets.find(x => v.includes((x.getAttribute('data-motion-set') || '').trim())); return b ? opt(b, 'button', labText(b), b.getAttribute('data-motion-set')) : null; };
    const red = pick(['reduced']); if (red) mctrl = {kind: 'button-set', reduce: red, full: pick(['full']), system: pick(['', 'system']), group: ''}; }
  if (!mctrl) { const b = pause.find(p => { let el = null; try { el = document.querySelector(p.path); } catch (e) {} return el && (el.hasAttribute('data-motion-toggle') || RED.test(labText(el)) || /движени|motion/i.test(labText(el))); });
    if (b) mctrl = {kind: 'button', reduce: {path: b.path, label: uw(labText(document.querySelector(b.path))).slice(0, 40), value: '', kind: 'button'}, full: null, system: null, group: ''}; }
  if (mctrl && mctrl.kind !== 'button' && !pause.some(p => p.path === mctrl.reduce.path)) { let el = null; try { el = document.querySelector(mctrl.reduce.path); } catch (e) {}
    if (el) pause.push({sel: sel(el), ...box(el), kind: mctrl.reduce.kind, path: mctrl.reduce.path, value: mctrl.reduce.value}); }
  const html = document.documentElement;
  const toggle = html.hasAttribute('data-motion') || !!document.querySelector('[data-motion-toggle], [data-motion], [data-motion-set]') || !!mctrl;
  const toggleScripts = Array.from(document.querySelectorAll('script[data-motion-toggle][src]')).map(s => (s.src || '').split('/').pop().split('?')[0]);
  const libs = {gsap: !!(window.gsap || window.gsapVersions), st: !!(window.ScrollTrigger), three: !!window.__THREE__, lenis: html.classList.contains('lenis') || !!window.lenis,
                pins: document.querySelectorAll('.pin-spacer').length, fx: !!(window.__fx), fxDestroy: !!(window.__fx && window.__fx.destroyAll)};
  const vids = Array.from(document.querySelectorAll('video')).map(v => ({src: (v.currentSrc || v.src || '').split('/').pop().slice(0, 60), paused: v.paused, autoplay: v.autoplay,
      poster: !!v.poster, loop: v.loop, muted: v.muted, first: v.getBoundingClientRect().top + scrollY < IH}));
  const canv = (M.gl && M.gl.canv || []).map(c => { const r = c.getBoundingClientRect(); return {sel: sel(c), w: c.width, cssw: Math.round(r.width), top: Math.round(r.top + scrollY),
      area: Math.round(r.width * r.height), first: r.top + scrollY < IH}; });
  return {textAll, hiddenAll, textBelow, hiddenBelow, hidEx, h1: h1i, cta, pause, toggle, libs, vids, canv, glCtx: M.gl ? M.gl.ctx : 0, glCalls: M.gl ? M.gl.calls : 0,
          scrollW: html.scrollWidth, innerW: IW, title: document.title, motion_ctrl: mctrl, toggle_scripts: toggleScripts};
}
""".replace("__PAUSE_RE__", PG.pause_label_re_js())   # подписи механизма паузы — page_gates.PAUSE_LABELS

MARQUEE_JS = r"""
async () => { const IW = innerWidth, IH = innerHeight; const cands = [];
  for (const el of Array.from(document.body.getElementsByTagName('*')).slice(0, 8000)) { const r = el.getBoundingClientRect();
    if (r.width > IW * 1.2 && r.height <= 320 && r.height >= 16 && r.bottom > 0 && r.top < IH) cands.push(el); if (cands.length > 40) break; }
  try { for (const a of document.getAnimations()) { const t = a.effect && a.effect.getTiming ? a.effect.getTiming() : {}; const tg = a.effect && a.effect.target;
      if (t.iterations === Infinity && tg && !cands.includes(tg)) { const r = tg.getBoundingClientRect(); if (r.bottom > 0 && r.top < IH && r.height <= 320) cands.push(tg); } } } catch (e) {}
  const x0 = cands.map(el => el.getBoundingClientRect().left);
  await new Promise(r => setTimeout(r, 700));
  const res = cands.map((el, i) => ({sel: (window.__mc && window.__mc.selOf ? window.__mc.selOf(el) : el.tagName), v: Math.abs(el.getBoundingClientRect().left - x0[i]) / 0.7}))
    .filter(x => x.v >= 3);
  return res.sort((a, b) => b.v - a.v).slice(0, 5); }
"""

FOCUS_JS = r"""
() => { let el = document.activeElement; if (!el || el === document.body) return null; const M = window.__mc || {}; const sel = M.selOf || (e => e.tagName);
  const opOf = (x) => { let o = 1, n = x; while (n && n.nodeType === 1) { o *= parseFloat(getComputedStyle(n).opacity); n = n.parentElement; } return o; };
  let r = el.getBoundingClientRect(); let o = opOf(el); let via = null;
  // скрытый radio/checkbox с видимой подписью (кольцо — на label через :focus-visible + label, F2 motion-toggle) — судим по подписи
  if ((o < 0.1 || (r.width <= 2 && r.height <= 2)) && el.labels && el.labels.length) {
    const lb = Array.from(el.labels).find(l => { const rr = l.getBoundingClientRect(); return rr.width > 2 && rr.height > 2 && opOf(l) >= 0.1; });
    if (lb) { via = sel(el); el = lb; r = lb.getBoundingClientRect(); o = opOf(lb); } }
  const cs = getComputedStyle(el);
  const cx = r.left + r.width / 2, cy = r.top + Math.min(r.height / 2, 12); const top = (cx >= 0 && cy >= 0 && cx < innerWidth && cy < innerHeight) ? document.elementFromPoint(cx, cy) : null;
  return {sel: via ? via + ' → ' + sel(el) : sel(el), via_label: !!via, ow: parseFloat(cs.outlineWidth) || 0, ost: cs.outlineStyle, sh: cs.boxShadow, bg: cs.backgroundColor,
          bc: cs.borderTopColor, td: cs.textDecorationLine, y: Math.round(r.top + scrollY), top: Math.round(r.top), h: Math.round(r.height),
          onScreen: r.bottom > 0 && r.top < innerHeight, op: Math.round(o * 100) / 100, covered: !!(top && top !== el && !el.contains(top) && !top.contains(el))}; }
"""


# =====================================================================================================================
# 2. Сервер для локальных файлов (Range, учёт байт, br по файлу) и блокировки
# =====================================================================================================================
class Served:
    def __init__(self):
        self.lock = threading.Lock()
        self.items = []   # (путь относительно корня, отдано байт, время)

    def add(self, rel, n):
        with self.lock:
            self.items.append((rel, n, time.time()))


def make_server(root, served):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=root, **k)

        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("Accept-Ranges", "bytes")
            super().end_headers()

        def do_GET(self):
            path = self.translate_path(self.path)
            if os.path.isdir(path):
                path = os.path.join(path, "index.html")
            if not os.path.isfile(path):
                self.send_error(404)
                return
            size = os.path.getsize(path)
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            rng = self.headers.get("Range")
            start, end, status = 0, size - 1, 200
            if rng:
                m = re.match(r"bytes=(\d*)-(\d*)", rng)
                if m:
                    s, e = m.group(1), m.group(2)
                    if s == "" and e:
                        start = max(0, size - int(e))
                    else:
                        start = int(s or 0)
                        end = min(size - 1, int(e)) if e else size - 1
                    if start >= size:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.end_headers()
                        return
                    status = 206
            length = end - start + 1
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            sent = 0
            try:
                with open(path, "rb") as f:
                    f.seek(start)
                    left = length
                    while left > 0:
                        chunk = f.read(min(65536, left))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        sent += len(chunk)
                        left -= len(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
            served.add(os.path.relpath(path, root), sent)

    class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True
    srv = S(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


_BR = {}


def br_size(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = (path, st.st_mtime, st.st_size)
    if key not in _BR:
        raw = open(path, "rb").read()
        if os.path.splitext(path)[1].lower() in TEXT_EXT:
            try:
                import brotli
                _BR[key] = len(brotli.compress(raw, quality=11))
            except Exception:
                import gzip
                _BR[key] = len(gzip.compress(raw, 9))
        else:
            _BR[key] = len(raw)
    return _BR[key]


class Locks:
    """Тихая машина на время режима (budgets.yaml conditions.quiet): общий тяжёлый замок, замок браузера и замок creative
    (page_gates.heavy_lock — kbpaths.lock; замок, который уже держит этот процесс или его предок, повторно не берётся и не
    ждётся), затем — свободная память."""
    def __init__(self, enabled=True, timeout=900):
        self.enabled, self.timeout, self._cm = enabled, timeout, None

    def __enter__(self):
        if not self.enabled:
            return self
        t0 = time.time()
        self._cm = PG.heavy_lock(domains=("creative",), timeout=self.timeout)
        self._cm.__enter__()
        if time.time() - t0 > 5:
            log(f"  замки тишины: ждали {time.time() - t0:.0f} с")
        wait_memory()
        return self

    def __exit__(self, *a):
        if self._cm is not None:
            self._cm.__exit__(*a)
            self._cm = None


def mem_available_gb():
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 1024 / 1024
    except Exception:
        pass
    return 99.0


def wait_memory(min_gb=3.0, max_wait=1800):
    t0 = time.time()
    while mem_available_gb() < min_gb:
        if time.time() - t0 > max_wait:
            raise SystemExit(f"память < {min_gb} ГБ дольше {max_wait} с — прогон отложен")
        log(f"  ждём память: {mem_available_gb():.1f} ГБ")
        time.sleep(20)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# =====================================================================================================================
# 3. Сеть по CDP: байты по фазам и типам
# =====================================================================================================================
class Net:
    def __init__(self, local_base=None, local_root=None, effects_re=EFFECT_JS_RE):
        self.req = {}
        self.phase = "first"
        self.local_base, self.local_root = local_base, local_root
        self.effects_re = re.compile(effects_re, re.I)
        self.cdp = None
        self._sniff = {}
        self._remote_sniffs = 0

    def sniff(self, rid, r):
        """Библиотека по содержимому файла: локальный — с диска; удалённый — тело ответа по CDP (≤ 30 файлов ≥ 20 КБ).
        Возвращает множество {'fx', '3d'}. Сигнатуры — строки из кода самих библиотек (SNIFF_FX, SNIFF_3D)."""
        key = r["url"]
        if key in self._sniff:
            return self._sniff[key]
        data = None
        if self.local_base and r["url"].startswith(self.local_base):
            p = os.path.join(self.local_root, unquote(urlparse(r["url"]).path).lstrip("/"))
            try:
                with open(p, "rb") as f:
                    data = f.read(8 * 1024 * 1024)
            except OSError:
                data = None
        elif self.cdp is not None and self._remote_sniffs < 30 and sum(r["by"].values()) >= 20 * 1024:
            self._remote_sniffs += 1
            try:
                b = self.cdp.send("Network.getResponseBody", {"requestId": rid})
                body = b.get("body") or ""
                data = base64.b64decode(body) if b.get("base64Encoded") else body.encode("utf-8", "ignore")
            except Exception:
                data = None
        kind = set()
        if data:
            if SNIFF_3D.search(data):
                kind.add("3d")
            if SNIFF_FX.search(data):
                kind.add("fx")
        self._sniff[key] = kind
        return kind

    def attach(self, cdp):
        self.cdp = cdp
        cdp.send("Network.enable")
        cdp.on("Network.requestWillBeSent", self.on_req)
        cdp.on("Network.responseReceived", self.on_resp)
        cdp.on("Network.dataReceived", self.on_data)
        cdp.on("Network.loadingFinished", self.on_fin)
        cdp.on("Network.loadingFailed", self.on_fail)

    def on_req(self, e):
        rid = e["requestId"]
        r = self.req.setdefault(rid, {"url": e["request"]["url"], "type": e.get("type") or "Other", "phase0": self.phase, "by": {}, "chunks": 0, "mime": ""})
        r["url"] = e["request"]["url"]

    def on_resp(self, e):
        r = self.req.get(e["requestId"])
        if r:
            r["mime"] = (e["response"].get("mimeType") or "")
            r["status"] = e["response"].get("status")
            r["type"] = e.get("type") or r["type"]

    def on_data(self, e):
        r = self.req.get(e["requestId"])
        if r:
            n = e.get("encodedDataLength") or 0
            r["by"][self.phase] = r["by"].get(self.phase, 0) + n
            r["chunks"] += n

    def on_fin(self, e):
        r = self.req.get(e["requestId"])
        if r:
            tot = e.get("encodedDataLength") or 0
            if tot > r["chunks"]:
                r["by"][self.phase] = r["by"].get(self.phase, 0) + (tot - r["chunks"])
                r["chunks"] = tot
            r["done"] = True

    def on_fail(self, e):
        r = self.req.get(e["requestId"])
        if r:
            r["failed"] = True

    def cat(self, r):
        t, u, m = r["type"], r["url"].lower(), r["mime"]
        if t == "Media" or m.startswith("video/") or re.search(r"\.(mp4|webm|m3u8|mov)(\?|$)", u):
            return "video"
        if t == "Script" or "javascript" in m or re.search(r"\.m?js(\?|$)", u):
            return "js"
        if t == "Font" or m.startswith("font/") or re.search(r"\.(woff2?|ttf|otf)(\?|$)", u):
            return "font"
        if t == "Image" or m.startswith("image/"):
            return "image"
        if t == "Stylesheet" or m == "text/css":
            return "css"
        if t == "Document":
            return "html"
        if re.search(r"\.(glb|gltf|ktx2|drc|splat|spz|bin|hdr|exr|usdz|splinecode)(\?|$)", u):
            return "3d"
        if re.search(r"\.wasm(\?|$)", u) or "wasm" in m:
            return "wasm"
        return "other"

    def wire_bytes(self, r, n):
        """Байты «на проводе»: у локального сервера текст идёт без сжатия → пересчёт в br q11 по файлу пропорционально."""
        if self.local_base and r["url"].startswith(self.local_base):
            rel = unquote(urlparse(r["url"]).path).lstrip("/")
            p = os.path.join(self.local_root, rel)
            if os.path.isdir(p):
                p = os.path.join(p, "index.html")
            if os.path.splitext(p)[1].lower() in TEXT_EXT and os.path.isfile(p):
                raw = os.path.getsize(p) or 1
                b = br_size(p) or raw
                return n * b / raw
        return n

    def summary(self):
        out = {"first_kb": 0.0, "session_kb": 0.0, "first_by": {}, "session_by": {}, "requests": len(self.req), "cdn": [], "hosts": {},
               "js_effects_first_kb": 0.0, "js_effects_session_kb": 0.0, "js_3d_first_kb": 0.0, "js_3d_session_kb": 0.0, "effects_js": [],
               "video_first_kb": 0.0, "video_session_kb": 0.0, "font_kb": 0.0, "js_first_kb": 0.0, "failed": 0, "sniffed": [],
               "wasm_presentation_kb": 0.0, "wasm_presentation": []}
        three_re = re.compile(THREE_D_RE, re.I)
        wasm3d_re = re.compile(WASM_3D_RE, re.I)
        for rid, r in list(self.req.items()):   # список: getResponseBody может принести события сети во время обхода
            if r["url"].startswith("data:"):
                continue
            c = self.cat(r)
            host = urlparse(r["url"]).hostname or ""
            first = self.wire_bytes(r, r["by"].get("first", 0)) / 1024
            tot = self.wire_bytes(r, sum(r["by"].values())) / 1024
            out["first_kb"] += first
            out["session_kb"] += tot
            out["first_by"][c] = out["first_by"].get(c, 0) + first
            out["session_by"][c] = out["session_by"].get(c, 0) + tot
            out["hosts"][host] = out["hosts"].get(host, 0) + tot
            if r.get("failed"):
                out["failed"] += 1
            if any(host == h or host.endswith("." + h) for h in CDN_HOSTS) and c in ("js", "wasm", "3d", "other"):
                out["cdn"].append(r["url"][:120])
            if c == "js":
                out["js_first_kb"] += first
                name_fx, name_3d = bool(self.effects_re.search(r["url"])), bool(three_re.search(r["url"]))
                sn = set() if (name_fx and name_3d) else self.sniff(rid, r)
                is_fx = name_fx or bool(sn)          # 3D-библиотека — тоже «эффекты», как и по имени (EFFECT_JS_RE содержит three)
                is_3d = name_3d or "3d" in sn
                if sn and not (name_fx and (name_3d or "3d" not in sn)):
                    out["sniffed"].append(f"{r['url'].split('/')[-1][:50]}: {'+'.join(sorted(sn))}")
                if is_fx:
                    out["js_effects_first_kb"] += first
                    out["js_effects_session_kb"] += tot
                    out["effects_js"].append(f"{r['url'].split('/')[-1][:50]} {tot:.1f}")
                if is_3d:
                    out["js_3d_first_kb"] += first
                    out["js_3d_session_kb"] += tot
            if c == "wasm" and wasm3d_re.search(r["url"]):
                out["js_3d_session_kb"] += tot
            elif c == "wasm":
                out["wasm_presentation_kb"] += tot
                out["wasm_presentation"].append(f"{r['url'].split('/')[-1][:50]} {tot:.1f}")
            if c == "video":
                out["video_first_kb"] += first
                out["video_session_kb"] += tot
            if c == "font":
                out["font_kb"] += tot
        for k in list(out):
            if isinstance(out[k], float):
                out[k] = round(out[k], 1)
        out["first_by"] = {k: round(v, 1) for k, v in out["first_by"].items()}
        out["session_by"] = {k: round(v, 1) for k, v in out["session_by"].items()}
        out["hosts"] = dict(sorted(((k, round(v, 1)) for k, v in out["hosts"].items()), key=lambda x: -x[1])[:10])
        out["effects_js"] = out["effects_js"][:12]
        out["sniffed"] = out["sniffed"][:8]
        out["first_mb"] = round(out["first_kb"] / 1024, 3)
        out["session_mb"] = round(out["session_kb"] / 1024, 3)
        out["video_session_mb"] = round(out["video_session_kb"] / 1024, 3)
        return out


# =====================================================================================================================
# 4. Сценарий режима (браузер под блокировками)
# =====================================================================================================================
def resolve_target_sel(target, hint=None, moment_id=None):
    """Логическая цель motion-spec → CSS-селекторы по x-dom-contract I (motion-spec.schema.json v1):
    [data-moment] → [data-section] [data-slot | data-group | data-fx] → #секция [data-slot] → selector_hint."""
    cands = [f'[data-moment="{moment_id}"]'] if moment_id else []
    if not target or target == "page":
        return cands + ["html"]
    parts = target.split(".")
    sec = parts[0]
    if len(parts) == 1:
        cands += [f'[data-section="{sec}"]', f"#{sec}"]
    elif len(parts) == 2:
        x = parts[1]
        if x.startswith("fx-"):
            cands += [f'[data-section="{sec}"] [data-fx="{x[3:]}"]', f'#{sec} [data-fx="{x[3:]}"]']
        cands += [f'[data-section="{sec}"] [data-slot="{x}"]', f'[data-section="{sec}"] [data-group="{x}"]', f'#{sec} [data-slot="{x}"]',
                  f'#{sec} [data-group="{x}"]']
    else:
        g, x = parts[1], parts[2]
        cands += [f'[data-section="{sec}"] [data-group="{g}"] [data-slot="{x}"]', f'[data-section="{sec}"] [data-group="{g}"] [data-fx="{x}"]',
                  f'#{sec} [data-group="{g}"] [data-slot="{x}"]']
    if hint:
        cands.append(hint)
    return cands


def local_root_for(page_path, root=None):
    """Корень раздачи: --root или подъём на глубину самых длинных ссылок «../» в HTML (общие папки вида ../_shared, ../_vendor)."""
    d = os.path.dirname(page_path)
    if root:
        return os.path.abspath(root)
    try:
        html = open(page_path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return d
    depth = max([len(m.group(1)) // 3 for m in re.finditer(r"""(?:src|href|url)\s*[=(]\s*["']?((?:\.\./)+)""", html)] + [0])
    for _ in range(min(depth, 6)):
        d = os.path.dirname(d)
    return d


def load_spec(path):
    if not path:
        return None
    import yaml
    txt = open(path, encoding="utf-8").read()
    return yaml.safe_load(txt) if path.endswith((".yaml", ".yml")) else json.loads(txt)


def spec_moments(spec):
    out = []
    for s in (spec or {}).get("sections", []) or []:
        for m in s.get("moments", []) or []:
            out.append({"section": s.get("id"), "role": s.get("role"), **m})
    return out


def run_mode(pw, mode, url, a, net_ctx, tmpdir, spec_ms):
    """Один режим: браузер → сценарий → сырьё. Видео сохраняется во временный файл (анализ — вне блокировок)."""
    args = list(GPU_ARGS) + (NOGL_ARGS if mode == "nogl" else [])
    b = pw.chromium.launch(headless=True, args=args)
    res = {"mode": mode, "browser": b.version, "log": []}
    rm = "reduce" if mode == "rm" else "no-preference"
    record = mode in ("desk", "mob", "rm") and not a.no_video
    vdir = os.path.join(tmpdir, mode)
    kw = dict(reduced_motion=rm, locale=a.locale)
    if record:
        kw["record_video_dir"] = vdir
    if mode == "mob":
        dev = PG.mobile_device(pw)                     # дескриптор budgets.yaml, UA — HeadlessChrome
        if record:
            kw["record_video_size"] = {"width": dev["viewport"]["width"], "height": dev["viewport"]["height"]}
        ctx = b.new_context(**dev, **kw)
    else:
        if record:
            kw["record_video_size"] = {"width": 960, "height": 600}
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1, java_script_enabled=(mode != "nojs"), **kw)
    ctx.add_init_script(INIT)
    page = ctx.new_page()
    errors = []
    def _con(m):
        if m.type != "error":
            return
        loc = (m.location or {}).get("url", "") if isinstance(m.location, dict) else ""
        if "favicon" in loc or "favicon" in m.text:
            return
        errors.append((m.text[:120] + (f" [{loc.split('/')[-1][:60]}]" if loc else "")))
    page.on("console", _con)
    page.on("pageerror", lambda e: errors.append(("pageerror: " + str(e))[:160]))
    cdp = ctx.new_cdp_session(page)
    net = Net(*net_ctx, effects_re=a.effects_js)
    net.attach(cdp)
    if mode == "mob":
        try:
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": PG.conditions()["mobile"]["cpu_slowdown"]})
        except Exception as e:
            res["log"].append(f"cpu: {e}")
    T0 = time.time()
    rel = lambda: round(time.time() - T0, 3)
    try:
        resp = page.goto(url, wait_until="load", timeout=a.timeout * 1000)
        res["status"] = resp.status if resp else None
    except Exception as e:
        res["log"].append(f"goto: {str(e)[:160]}")
    res["t_load"] = rel()
    if mode in ("nojs", "nogl"):
        page.wait_for_timeout(2500 if mode == "nogl" else 1200)
        res["page"] = page.evaluate(PAGE_JS, {}) if mode != "nojs" else page_nojs(page)
        png = page.screenshot(type="png")
        res["blank_std"] = blank_std(png)
        res["hero_std"] = blank_std(png, top_frac=0.6)
        res["console_errors"] = len(errors)
        res["errors"] = errors[:8]
        res["net"] = net.summary()
        if a.keep_shots:
            open(os.path.join(a.out, f"shot_{mode}.png"), "wb").write(png)
        thumb(png, os.path.join(a.out, f"shot_{mode}.jpg"))
        ctx.close()
        b.close()
        return res
    page.wait_for_timeout(max(0, a.wait - 400))
    # синхровспышка для видео (внутри окна первого экрана)
    try:
        page.evaluate("""(() => { const d = document.createElement('div'); d.id = '__mc_flash';
          d.style.cssText = 'position:fixed;inset:0;background:#ff00ff;z-index:2147483647;pointer-events:none';
          document.documentElement.appendChild(d); })()""")
        res["t_flash"] = rel()
        page.wait_for_timeout(400)
        page.evaluate("(() => { const d = document.getElementById('__mc_flash'); if (d) d.remove(); })()")
    except Exception as e:
        res["log"].append(f"flash: {e}")
    net.phase = "idle"          # первый экран = load + окно budgets.yaml (conditions.first_screen)
    page.wait_for_timeout(500)
    # движение на 6-й секунде после load (2.2.2) и в покое
    t_idle = rel()
    try:
        page.evaluate(PRIME_JS)          # вызовы WebGL первого снимка — только за эту секунду покоя
        s1 = page.screenshot(type="png")
        page.wait_for_timeout(1000)
        s2 = page.screenshot(type="png")
        res["idle_6s"] = {"t_after_load_s": round(t_idle - res["t_load"], 2), "pct": motion_pct(s1, s2), "blank_std": blank_std(s2)}
        thumb(s2, os.path.join(a.out, f"shot_{mode}.jpg"))
    except Exception as e:
        res["log"].append(f"idle: {e}")
    snap0 = page.evaluate(SNAP_JS, {})
    res["snap_first"] = snap0
    res["page_first"] = page.evaluate(PAGE_JS, {})
    try:
        res["marquee"] = page.evaluate(MARQUEE_JS)
    except Exception:
        res["marquee"] = []
    mc = page.evaluate("() => { const M = window.__mc || {}; return {lcp: M.lcp || [], cls: M.cls || [], lt: M.lt || [], fcp: M.fcp || null, h1op: (M.h1op || []).slice(0, 12), err: M.err || [], gl: M.gl ? {ctx: M.gl.ctx, calls: M.gl.calls} : null, intro: M.intro || null}; }")
    res["vitals"] = vitals(mc, res["page_first"])
    res["intro"] = mc.get("intro")
    net_first = net.summary()
    # выборка моментов motion-spec: load — уже прошли; in-view — ниже, при прокрутке
    # --- прокрутка
    net.phase = "session"
    page.evaluate("() => { const M = window.__mc; if (M) { M.phase = 'scroll'; M.raf = []; M.rafOn = true; M.tScroll = performance.now(); } }")
    W = page.viewport_size["width"]
    H = page.viewport_size["height"]
    total = page.evaluate("Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0) - innerHeight")
    delta = max(200, int(H * 0.8))
    steps = max(3, min(a.steps, math.ceil(max(total, 1) / delta) + 1)) if total > H * 0.3 else 3
    page.mouse.move(W / 2, H / 2)
    windows, wheel, snaps = [], [], []
    # два снимка в паузе — сброс счётчика WebGL на +0,5 с (после хвоста сглаживания скраба), снимок на +1,2 с
    # (при --dwell 1,8; при меньшей паузе — пропорционально); петля WebGL — только если вызовы выросли между ними («Звено»)
    t_prime = min(0.5, 0.28 * a.dwell)
    t_snap = max(t_prime + 0.35, min(1.2, 0.67 * a.dwell))

    mq_tries = [0]                 # бегущая строка меряется на шагах с петлёй, пока не попадёт в окно (до 6 попыток)

    def dwell(step):
        y = page.evaluate("Math.round(scrollY)")
        t0 = rel()
        page.wait_for_timeout(int(t_prime * 1000))
        page.evaluate(PRIME_JS)
        page.wait_for_timeout(int((t_snap - t_prime) * 1000))
        s = page.evaluate(SNAP_JS, {})
        s["step"] = step
        s["idle_window_s"] = round(t_snap - t_prime, 2)
        snaps.append(s)
        if (s.get("loops") or 0) > 0 and not res.get("marquee_measured") and mq_tries[0] < 6:
            mq_tries[0] += 1
            try:
                mq = page.evaluate(MARQUEE_JS)
                allm = {}
                for x in (res.get("marquee") or []) + (mq or []):
                    allm[x["sel"]] = max(allm.get(x["sel"], 0), x["v"])
                res["marquee"] = [{"sel": k, "v": round(v, 1)} for k, v in sorted(allm.items(), key=lambda kv: -kv[1])[:5]]
                if mq:
                    res["marquee_measured"] = step
            except Exception:
                pass
        else:
            page.wait_for_timeout(int(max(0.0, a.dwell - t_snap) * 1000))
        windows.append({"step": step, "y": y, "t0": t0, "t1": rel()})
    dwell(0)
    for s in range(1, steps + 1):
        y0 = page.evaluate("Math.round(scrollY)")
        remain = page.evaluate("Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0) - innerHeight - scrollY")
        tw = rel()
        page.mouse.wheel(0, delta)
        last, stable, settle = None, None, None
        for _ in range(60):
            page.wait_for_timeout(50)
            y = page.evaluate("Math.round(scrollY)")
            if y == last:
                if stable is None:
                    stable = rel()
                elif rel() - stable >= 0.25:
                    settle = round((stable - tw) * 1000)
                    break
            else:
                stable = None
            last = y
        y1 = page.evaluate("Math.round(scrollY)")
        exp = min(delta, max(remain, 0))
        wheel.append({"step": s, "t": tw, "settle_ms": settle, "dist": y1 - y0, "expected": exp, "ratio": round((y1 - y0) / exp, 2) if exp >= 80 else None})
        dwell(s)
        if remain <= 2:
            break
        if time.time() - T0 > a.budget - 40:
            res["log"].append("бюджет времени режима: прокрутка остановлена")
            break
    page.evaluate("() => { const M = window.__mc; if (M) M.rafOn = false; }")
    mc2 = page.evaluate("() => { const M = window.__mc || {}; return {cls: M.cls || [], loaf: M.loaf || [], raf: M.raf || [], tScroll: M.tScroll || 0, now: performance.now(), lt: M.lt || [], err: M.err || [], gl: M.gl ? {ctx: M.gl.ctx, calls: M.gl.calls} : null}; }")
    res["scroll"] = scroll_metrics(mc2, wheel)
    res["cls"] = cls_block(mc2.get("cls") or [])      # сумма, окно сессии, атрибуция источников сдвига
    res["windows"] = windows
    res["wheel"] = wheel
    res["snaps"] = [{k: v for k, v in s_.items() if k != "loopsAll"} for s_ in snaps]
    res["loops"] = loop_metrics(snaps, res.get("marquee") or [], H, W)
    res["page_end"] = page.evaluate(PAGE_JS, {})
    # петли: через 6 с после показа (2.2.2 «остановка ≤ 5 с»)
    res["loops_6s"] = loops_after_6s(page, snaps) if mode != "rm" else None
    # моменты motion-spec
    if spec_ms:
        res["spec"] = sample_moments(page, spec_ms, mode)
    if a.spec_doc and mode in ("desk", "mob", "rm"):
        res["stations"] = station_probe(page, a.spec_doc, mode, a.out)
    if getattr(a, "contrast", None) and mode in ("desk", "mob"):
        try:                               # контраст над живым фоном (EG-A11Y-27)
            res["contrast_live"] = contrast_live(page, a.contrast, mode)
        except Exception as e:
            res["contrast_live"] = [{"error": str(e)[:160]}]
    # Tab-проход и пауза — только десктоп
    if mode == "desk":
        res["keyboard"] = tab_walk(page, 25)
        res["toggle_test"] = toggle_test(page, res["page_end"], mode, a.out)   # «Меньше» → стоит ли (EG-A11Y-24)
        res["pause_test"] = pause_test(page, res["page_end"])
        if res["page_end"]["libs"].get("fxDestroy"):
            try:
                res["destroy"] = page.evaluate("() => { const b = document.querySelectorAll('.pin-spacer').length; try { window.__fx.destroyAll(); } catch (e) { return {error: String(e)}; } return {pins_before: b, pins_after: document.querySelectorAll('.pin-spacer').length, st_after: window.ScrollTrigger ? window.ScrollTrigger.getAll().length : null}; }")
            except Exception as e:
                res["destroy"] = {"error": str(e)[:120]}
    res["net"] = net.summary()
    res["net"]["first_only"] = {k: net_first[k] for k in ("first_kb", "first_mb", "first_by", "js_first_kb", "js_effects_first_kb", "js_3d_first_kb", "video_first_kb")}
    res["console_errors"] = len(errors)
    res["errors"] = errors[:8]
    res["gl"] = mc2.get("gl")
    if mode == "rm":
        # выбор посетителя сильнее ОС — «Полное» в reduce включает движение (EG-A11Y-25); после сводки сети, чтобы
        # библиотеки, загруженные по выбору «Полное», не попали в ворота reduce (EG-A11Y-05, EG-A11Y-11)
        res["toggle_test"] = toggle_test(page, res["page_end"], mode, a.out)
    video = page.video if record else None
    ctx.close()
    res["video_tmp"] = video.path() if video else None
    b.close()
    return res


def page_nojs(page):
    """Без JS нельзя исполнить PAGE_JS через evaluate? — можно: evaluate работает и при java_script_enabled=False (исполняет CDP)."""
    try:
        return page.evaluate(PAGE_JS, {})
    except Exception as e:
        return {"error": str(e)[:160]}


def blank_std(png, top_frac=1.0):
    import numpy as np
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("L")
    if top_frac < 1.0:
        im = im.crop((0, 0, im.width, int(im.height * top_frac)))
    return round(float(np.asarray(im, dtype=np.float32).std()), 2)


def motion_pct(a, b, thr=12):
    import numpy as np
    from PIL import Image
    x = np.asarray(Image.open(io.BytesIO(a)).convert("RGB"), dtype=np.int16)
    y = np.asarray(Image.open(io.BytesIO(b)).convert("RGB"), dtype=np.int16)
    if x.shape != y.shape:
        return None
    return round(100.0 * float((np.abs(x - y).max(axis=2) > thr).mean()), 3)


def thumb(png, path, w=480):
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(path, "JPEG", quality=72, optimize=True)


def vitals(mc, pg):
    lcp = mc["lcp"][-1] if mc.get("lcp") else None
    fcp = mc.get("fcp") or 0
    tbt = sum(max(0, x["d"] - 50) for x in mc.get("lt", []) if x["t"] >= fcp and x.get("ph", "load") == "load")
    cls_load = round(sum(x["v"] for x in mc.get("cls", []) if x.get("ph") == "load"), 4)
    h1 = (pg or {}).get("h1")
    dropped = False
    if lcp and h1 and h1.get("first") and not lcp.get("isH1") and lcp.get("tag") not in ("IMG", "VIDEO", "image", "CANVAS"):
        dropped = (h1.get("area") or 0) > 1.2 * (lcp.get("size") or 0)
    h1op = mc.get("h1op") or []
    first_invisible = bool(h1op) and h1op[0]["o"] < 0.05
    return {"lcp_ms": lcp["t"] if lcp else None, "lcp_tag": lcp["tag"] if lcp else None, "lcp_sel": lcp["sel"] if lcp else None,
            "lcp_size": lcp["size"] if lcp else None, "lcp_is_h1": bool(lcp and lcp.get("isH1")), "lcp_entries": len(mc.get("lcp") or []),
            "h1_lcp_dropped": dropped, "h1_first_frame_invisible": first_invisible, "h1_first_op": h1op[0]["o"] if h1op else None,
            "fcp_ms": fcp or None, "tbt_ms": round(tbt), "cls_load": cls_load, "lcp_canvas": bool(lcp and lcp.get("tag") == "CANVAS"),
            "lcp_video_no_poster": bool(lcp and lcp.get("tag") == "VIDEO")}


def scroll_metrics(mc, wheel):
    t0 = mc.get("tScroll") or 0
    span = max(1.0, (mc.get("now") or 0) - t0)
    loaf = [x for x in mc.get("loaf", []) if x.get("ph") == "scroll"]
    cls_s = round(sum(x["v"] for x in mc.get("cls", []) if x.get("ph") == "scroll"), 4)
    raf = mc.get("raf") or []
    d = [b - a for a, b in zip(raf, raf[1:]) if 0 < b - a < 250]
    ds = sorted(d)
    settles = [w["settle_ms"] for w in wheel if w.get("settle_ms") is not None]
    ratios = [w["ratio"] for w in wheel if w.get("ratio") is not None]
    return {"loaf_n": len(loaf), "loaf_ms": sum(x["d"] for x in loaf), "loaf_pct": round(100.0 * sum(x["d"] for x in loaf) / span, 2),
            "loaf_blocking_ms": sum(x["b"] for x in loaf), "cls": cls_s,
            "cls_sources": sorted({s for x in mc.get("cls", []) if x.get("ph") == "scroll" for s in (x.get("src") or []) if s})[:6],
            "raf_p95_ms": round(ds[int(0.95 * (len(ds) - 1))], 1) if ds else None, "fps": round(1000 * len(d) / sum(d), 1) if d else None,
            "tail_ms_median": statistics.median(settles) if settles else None, "tail_ms_max": max(settles) if settles else None,
            "dist_ratio_min": min(ratios) if ratios else None, "dist_ratio_max": max(ratios) if ratios else None,
            "steps": len(wheel), "span_s": round(span / 1000, 1)}


def cls_block(entries):
    """CLS загрузки и прокрутки (сдвиги без недавнего ввода), наибольшее окно сессии как у web-vitals (разрыв < 1 с,
    окно ≤ 5 с) и атрибуция по узлам (метод F2 cls_sources.py): вклад сдвига делится поровну между его источниками,
    пример — прямоугольник «откуда → куда» [x, y, w, h]."""
    es = sorted((e for e in (entries or []) if isinstance(e, dict) and isinstance(e.get("v"), (int, float))), key=lambda e: e.get("t") or 0)
    load = sum(e["v"] for e in es if e.get("ph") == "load")
    total = sum(e["v"] for e in es)
    wins, cur, start, prev = [], 0.0, None, None
    for e in es:
        t = e.get("t") or 0
        if start is None or t - prev >= 1000 or t - start >= 5000:
            if start is not None:
                wins.append(cur)
            cur, start = 0.0, t
        cur += e["v"]
        prev = t
    if start is not None:
        wins.append(cur)
    by = {}
    for e in es:
        srcs = [s for s in (e.get("mv") or [{"n": x} for x in (e.get("src") or [])]) if isinstance(s, dict) and s.get("n")] or [{"n": "?"}]
        for s in srcs:
            rec = by.setdefault(s["n"], {"v": 0.0, "ph": set(), "ex": None})
            rec["v"] += e["v"] / len(srcs)
            rec["ph"].add(e.get("ph") or "?")
            if rec["ex"] is None and s.get("f") and s.get("c"):
                rec["ex"] = f"{s['f']}→{s['c']}"
    top = sorted(by.items(), key=lambda kv: -kv[1]["v"])[:5]
    return {"load": round(load, 4), "scroll": round(total - load, 4), "total": round(total, 4),
            "window_max": round(max(wins), 4) if wins else 0.0, "n": len(es),
            "top_sources": [f"{k} {v['v']:.3f} ({'+'.join(sorted(v['ph']))}){(' ' + v['ex']) if v['ex'] else ''}" for k, v in top]}


def loop_metrics(snaps, marquee, H, W):
    """Петли по паузам: число в зоне, под текстом, колебания (EG-A11Y-18: крупный объект — меньшая сторона ≥ доли
    large_min_side_share меньшей стороны окна, период ≥ period_min_s; мелкий — ≥ small_period_min_s; быстрее полосы band_s
    — пульсация, не колебание), пульсация призыва, бегущая строка."""
    loops_max = max((s.get("loops") or 0) for s in snaps) if snaps else 0
    under = sorted({u for s in snaps for u in (s.get("under") or [])})
    band, pmin, psmall, share = (LIM("EG-A11Y-18", k) for k in ("band_s", "period_min_s", "small_period_min_s", "large_min_side_share"))
    osc, pulse = [], []
    for s in snaps:
        for l in s.get("loopsAll") or []:
            if l.get("k") != "anim" or not l.get("vis"):
                continue
            props = [re.sub(r"[^a-z]", "", p.lower()) for p in (l.get("props") or [])]
            period = (l.get("dur") or 0) * (2 if (l.get("dir") or "").startswith("alternate") else 1) / 1000
            big = min(l.get("w") or 0, l.get("h") or 0) >= share * min(W, H)
            moving = any(p in ("transform", "translate", "rotate", "scale") for p in props)
            if moving and big and band[0] <= period < pmin:
                osc.append(f"{l['sel']} крупный, период {period:.1f} с < {pmin} с" + (f" (полоса {band[0]}–{band[1]} с)" if period <= band[1] else ""))
            elif moving and not big and band[0] <= period < psmall:
                osc.append(f"{l['sel']} мелкий, период {period:.1f} с < {psmall} с")
            if l.get("cta") and any(p in ("transform", "scale", "boxshadow", "opacity") for p in props):
                pulse.append(f"{l['sel']} {l.get('name', '')}")
    return {"loops_in_view_max": loops_max, "under_text": under[:6], "oscillation": sorted(set(osc))[:6], "pulsing_cta": sorted(set(pulse))[:4],
            "marquee_speed_max": round(max((m["v"] for m in marquee), default=0), 1), "marquee": marquee[:4],
            "loops_by_step": [s.get("loops") for s in snaps]}


def loops_after_6s(page, snaps, limit=3):
    """Каждую найденную петлю (до 3) — в экран, 6 с ожидания: движется ли ещё (2.2.2: пауза или стоп ≤ 5 с)."""
    seen, out = [], []
    for s in snaps:
        for l in s.get("loopsAll") or []:
            if l["sel"] in seen or not l.get("vis"):
                continue
            seen.append(l["sel"])
            if len(seen) > limit:
                break
    for sel in seen[:limit]:
        try:
            r = page.evaluate("""async (sel) => { const M = window.__mc || {}; const el = [...document.querySelectorAll('*')].find(e => (M.selOf ? M.selOf(e) : '') === sel);
                if (!el) return {sel, found: false}; el.scrollIntoView({block: 'center'}); await new Promise(r => setTimeout(r, 6000));
                const an = el.getAnimations ? el.getAnimations({subtree: true}).filter(a => a.playState === 'running').length : 0;
                const vid = el.tagName === 'VIDEO' ? !el.paused : false; const c0 = el.__mcCalls || 0; await new Promise(r => setTimeout(r, 500));
                return {sel, found: true, running_anims: an, video_playing: vid, webgl_calls_0_5s: (el.__mcCalls || 0) - c0}; }""", sel)
        except Exception as e:
            r = {"sel": sel, "error": str(e)[:100]}
        r["moving"] = bool(r.get("running_anims") or r.get("video_playing") or (r.get("webgl_calls_0_5s") or 0) > 0)
        out.append(r)
    return out


def tab_walk(page, n):
    page.evaluate("() => { window.scrollTo(0, 0); if (document.activeElement) document.activeElement.blur(); }")
    page.wait_for_timeout(300)
    stops, no_ring, off, hidden, covered, back = [], [], [], [], [], 0
    prev_y = None
    for _ in range(n):
        page.keyboard.press("Tab")
        page.wait_for_timeout(350)
        f = page.evaluate(FOCUS_JS)
        if not f:
            continue
        if f["sel"] in [s["sel"] for s in stops]:
            continue
        stops.append(f)
        ring = (f["ost"] not in ("none", "") and f["ow"] > 0) or (f["sh"] not in ("none", "")) or ("underline" in (f.get("td") or ""))
        if not ring:
            no_ring.append(f["sel"])
        if not f["onScreen"]:
            off.append(f["sel"])
        if f["op"] < 0.1:
            hidden.append(f["sel"])
        if f["covered"]:
            covered.append(f["sel"])
        if prev_y is not None and f["y"] < prev_y - 40:
            back += 1
        prev_y = f["y"]
    return {"stops": len(stops), "no_ring_guess": no_ring[:6], "off_screen": off[:6], "invisible": hidden[:6], "covered": covered[:6], "order_back": back}


def pause_test(page, pg):
    """Есть кнопка паузы → нажать → через 0,8 с два кадра по 1 с: стоит ли первый экран и бесконечные анимации."""
    if not pg.get("pause"):
        return {"control": False}
    p0 = pg["pause"][0]
    sel = p0["sel"]
    try:
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        before = page.evaluate("() => document.getAnimations().filter(a => a.playState === 'running' && a.effect && a.effect.getTiming().iterations === Infinity).length")
        if p0.get("path"):     # по пути элемента (радиогруппа «Движение», select, кнопка)
            ok = page.evaluate(CLICK_JS, {"path": p0["path"], "kind": p0.get("kind", "button"), "value": p0.get("value", "")})
        else:
            ok = page.evaluate("""(sel) => { const M = window.__mc || {}; const el = [...document.querySelectorAll('button, [role=button], [role=switch], input[type=checkbox], [aria-pressed]')]
              .find(e => (M.selOf ? M.selOf(e) : '') === sel); if (!el) return false; el.click(); return true; }""", sel)
        page.wait_for_timeout(800)
        s1 = page.screenshot(type="png")
        page.wait_for_timeout(1000)
        s2 = page.screenshot(type="png")
        after = page.evaluate("() => document.getAnimations().filter(a => a.playState === 'running' && a.effect && a.effect.getTiming().iterations === Infinity).length")
        vids = page.evaluate("() => [...document.querySelectorAll('video')].filter(v => !v.paused).length")
        return {"control": True, "sel": sel, "kind": p0.get("kind", "button"), "clicked": ok, "infinite_before": before, "infinite_after": after,
                "videos_playing_after": vids, "pct_after": motion_pct(s1, s2)}
    except Exception as e:
        return {"control": True, "sel": sel, "error": str(e)[:120]}


def motion_sample(page):
    """Движение первого экрана за 1 с — % пикселей (порог 12/255 по каналу), вызовы WebGL за эту секунду, бегущие
    бесконечные анимации, играющие видео, html[data-motion], объект LAB.info страницы, если он есть."""
    page.evaluate(MEASURE_JS, "prime")
    s1 = page.screenshot(type="png")
    page.wait_for_timeout(1000)
    s2 = page.screenshot(type="png")
    m = page.evaluate(MEASURE_JS, "read") or {}
    m["pct_1s"] = motion_pct(s1, s2)
    return m, s2


def toggle_test(page, pg, mode, out_dir=None):
    """Переключатель «меньше движения» поведением (CRV-AL-12, E 05/01 §4.4). desk: нажать «Меньше» → первый экран
    ≤ 0,3 %/с, 0 вызовов WebGL, 0 бесконечных анимаций, видео стоит (эталон F2/12: 3,94 → 0 %/с). rm: нажать «Полное» →
    движение есть (выбор посетителя сильнее ОС). Затем вернуть исходное состояние («как в системе» или повторное нажатие)."""
    ctrl = (pg or {}).get("motion_ctrl") or {}
    want = "full" if mode == "rm" else "reduce"
    o = ctrl.get(want)
    if not o:
        return {"control": bool(ctrl), "kind": ctrl.get("kind"), "option": None}
    out = {"control": True, "kind": ctrl.get("kind"), "option": o.get("label"), "path": o.get("path")}
    try:
        page.evaluate("() => window.scrollTo({top: 0, behavior: 'instant'})")
        page.wait_for_timeout(700)
        out["before"], _ = motion_sample(page)
        out["clicked"] = page.evaluate(CLICK_JS, o)
        page.wait_for_timeout(1000)
        out["after"], png = motion_sample(page)
        if out_dir:
            thumb(png, os.path.join(out_dir, f"toggle_{mode}_after.jpg"))
        if ctrl.get("kind") == "button":
            back = o                                  # одна кнопка — повторное нажатие возвращает
        else:
            back = ctrl.get("system") or ctrl.get("full" if want == "reduce" else "reduce")
        out["restored"] = bool(back and page.evaluate(CLICK_JS, back))
        page.wait_for_timeout(700)
    except Exception as e:
        out["error"] = str(e)[:160]
    return out


# контраст текста над живым фоном: текст выбранных элементов
# прозрачен, фон снимается в нескольких кадрах (время и положения указателя), под рамкой строк (Range) — перцентиль яркости
CONTRAST_PREP_JS = r"""
(sels) => { const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', {willReadFrequently: true});
  const rgba = (c) => { try { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); return Array.from(cx.getImageData(0, 0, 1, 1).data); } catch (e) { return null; } };
  const out = [];
  for (const s of sels) { let els = []; try { els = Array.from(document.querySelectorAll(s)); } catch (e) {}
    const el = els.find(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight; });
    if (!el) { out.push({sel: s, found: false}); continue; }
    const cs = getComputedStyle(el); const g = document.createRange(); g.selectNodeContents(el); const r = g.getBoundingClientRect();
    const fs = parseFloat(cs.fontSize), fw = parseInt(cs.fontWeight, 10) || 400;
    out.push({sel: s, found: true, color: cs.color, rgba: rgba(cs.color), box: [r.left, r.top, r.width, r.height], fs, fw,
              large: fs >= 24 || (fs >= 18.66 && fw >= 700), gradient_text: (cs.webkitBackgroundClip || cs.backgroundClip || '') === 'text'}); }
  const st = document.createElement('style'); st.id = '__mc_contrast';
  st.textContent = sels.map(s => s + ', ' + s + ' * { color: transparent !important; text-shadow: none !important; -webkit-text-stroke: 0 !important; text-decoration-color: transparent !important; }').join('\n');
  document.head.appendChild(st); return out; }
"""


def contrast_eval(Ls, items, scale):
    """Худший контраст по кадрам. Ls — массивы относительной яркости кадров (текст прозрачен); под рамкой строк — 95-й
    перцентиль яркости фона для светлого текста (самая светлая точка) или 5-й для тёмного; цвет текста с альфой смешивается с фоном.
    Порог — 4,5:1, крупный текст (≥ 24 px или ≥ 18,66 px жирный) — 3:1 (WCAG 1.4.3). Градиентный текст — N/A (F83 по буквам)."""
    import numpy as np
    out = []
    for it in items or []:
        if not it.get("found"):
            out.append({"sel": it.get("sel"), "found": False})
            continue
        rgba = it.get("rgba") or [0, 0, 0, 255]
        c = np.array(rgba[:3], dtype=np.float64) / 255.0
        cl = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        lt = float(0.2126 * cl[0] + 0.7152 * cl[1] + 0.0722 * cl[2])
        alpha = (rgba[3] if len(rgba) > 3 else 255) / 255.0
        x, y, w, h = it["box"]
        worst, bg_w = None, None
        for L in Ls:
            x0, y0 = max(0, int(x * scale)), max(0, int(y * scale))
            x1, y1 = min(L.shape[1], int((x + w) * scale)), min(L.shape[0], int((y + h) * scale))
            crop = L[y0:y1, x0:x1]
            if crop.size < 16:
                continue
            light = lt >= float(np.median(crop))
            bg = float(np.percentile(crop, 95 if light else 5))
            t = alpha * lt + (1 - alpha) * bg
            ratio = (max(t, bg) + 0.05) / (min(t, bg) + 0.05)
            if worst is None or ratio < worst:
                worst, bg_w = ratio, bg
        rec = {"sel": it["sel"], "found": True, "ratio_min": round(worst, 2) if worst is not None else None, "threshold": 3.0 if it.get("large") else 4.5,
               "large": bool(it.get("large")), "text_rgba": rgba, "frames": len(Ls), "box": [round(v) for v in it["box"]],
               "bg_lum_worst": round(bg_w, 4) if bg_w is not None else None}
        if it.get("gradient_text"):
            rec.update({"ratio_min": None, "note": "градиентный текст (background-clip: text) — F83 по буквам (page_accept.py)"})
        out.append(rec)
    return out


def contrast_live(page, sels, mode):
    """Худший контраст текста над живым фоном первого экрана: 4 кадра через 0,45 с (видео, шейдер, петли) и на
    десктопе ещё 5 положений указателя по диагонали (фон, который следует за мышью); рамка — границы строк (Range), а не блока."""
    import numpy as np
    from PIL import Image
    page.evaluate("() => window.scrollTo({top: 0, behavior: 'instant'})")
    page.wait_for_timeout(600)
    items = page.evaluate(CONTRAST_PREP_JS, list(sels))
    vw, vh = page.viewport_size["width"], page.viewport_size["height"]
    shots = []
    try:
        for _ in range(4):
            page.wait_for_timeout(450)
            shots.append(page.screenshot(type="png"))
        if mode != "mob":
            for fx, fy in ((0.12, 0.15), (0.35, 0.35), (0.62, 0.55), (0.88, 0.8), (0.88, 0.2)):
                page.mouse.move(vw * fx, vh * fy, steps=10)
                page.wait_for_timeout(550)
                shots.append(page.screenshot(type="png"))
    finally:
        page.evaluate("() => { const s = document.getElementById('__mc_contrast'); if (s) s.remove(); }")
    Ls = []
    for png in shots:
        im = np.asarray(Image.open(io.BytesIO(png)).convert("RGB"), dtype=np.float64) / 255.0
        lin = np.where(im <= 0.04045, im / 12.92, ((im + 0.055) / 1.055) ** 2.4)
        Ls.append(0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2])
    return contrast_eval(Ls, items, (Ls[0].shape[1] / vw) if Ls else 1.0)


def sample_moments(page, moments, mode):
    """Выборка стилей целей моментов: load — сразу (уже доиграли → конечное состояние), in-view — прокрутка к цели и 3 с выборки."""
    out = []
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(600)
    for m in moments[:12]:
        trig = (m.get("trigger") or {}).get("type")
        cands = resolve_target_sel(m.get("target"), m.get("selector_hint"), m.get("id"))
        sel = None
        for c in cands:
            try:
                if page.evaluate("(s) => !!document.querySelector(s)", c):
                    sel = c
                    break
            except Exception:
                continue
        rec = {"id": m.get("id"), "section": m.get("section"), "class": m.get("class"), "trigger": trig, "target": m.get("target"), "sel": sel}
        if not sel:
            rec["missing"] = True
            out.append(rec)
            continue
        try:   # canvas/video — выборка стилей их содержимого не видит
            rec["tag"] = page.evaluate("(s) => { const e = document.querySelector(s); return e ? e.tagName : null; }", sel)
        except Exception:
            rec["tag"] = None
        if trig in ("in-view", "scroll-scrub", "pin-scrub"):
            try:
                page.evaluate("""(s) => { const el = document.querySelector(s); if (!el) return; const r = el.getBoundingClientRect();
                    window.scrollTo(0, Math.max(0, scrollY + r.top - innerHeight * 1.2)); }""", sel)
                page.wait_for_timeout(400)
                page.evaluate("(a) => window.__mc && window.__mc.watch(a[0], a[1], 2200)", [m.get("id") or sel, sel])
                page.mouse.wheel(0, int(page.viewport_size["height"] * 0.6))
                page.wait_for_timeout(2400)
            except Exception as e:
                rec["error"] = str(e)[:100]
        else:
            page.evaluate("(a) => window.__mc && window.__mc.watch(a[0], a[1], 1200)", [m.get("id") or sel, sel])
            page.wait_for_timeout(1400)
        samp = page.evaluate("(k) => (window.__mc && window.__mc.samp[k]) || null", m.get("id") or sel)
        rec.update(analyze_samples(samp))
        rec["spec_ms"] = spec_duration_ms(m)
        rec["spec_props"] = [t.get("property") for t in (m.get("tracks") or [])]
        rec["reduce"] = (m.get("reduce") or {}).get("strategy")
        out.append(rec)
    return out


STATION_JS = r"""
async (a) => { const [place, line, targets] = a; const IH = innerHeight, IW = innerWidth;
  const lineY = line === 'viewport-top' ? 0 : (line === 'viewport-bottom' ? IH : IH / 2);
  const q = (sels) => { for (const s of sels || []) { let e = null; try { e = document.querySelector(s); } catch (x) {} if (e) return e; } return null; };
  let group = null, anchor = null, sec = null;
  if (place.kind === 'anchor') { group = q(place.sels); if (!group) return {found: false};
    anchor = group.matches('[data-anchor-point]') ? group : (group.querySelector('[data-anchor-point]') || group);   // точка якоря в группе (маркер шага)
    const r0 = anchor.getBoundingClientRect(); window.scrollTo({top: Math.max(0, scrollY + r0.top + r0.height / 2 - lineY), behavior: 'instant'});
  } else { sec = q(place.secSels); if (!sec) return {found: false, reason: 'section'};
    const r = sec.getBoundingClientRect(); const top = r.top + scrollY, h = r.height;
    // доля at: сцена выше окна (sticky/pin) — 0 = верх секции у верха окна, 1 = низ секции у низа окна; иначе — диапазон cover
    const y = h > IH * 1.05 ? top + place.at * (h - IH) : top - IH + place.at * (h + IH);
    window.scrollTo({top: Math.max(0, y), behavior: 'instant'}); }
  await new Promise(r => setTimeout(r, 900));
  const out = {found: true, y: Math.round(scrollY), line_y: Math.round(lineY), targets: []};
  if (anchor) { const r1 = anchor.getBoundingClientRect(); out.anchor_center_offset = Math.round(r1.top + r1.height / 2 - lineY); out.anchor_point = anchor !== group; }
  if (sec) { const r = sec.getBoundingClientRect(); out.progress = place.at; out.section_top = Math.round(r.top); out.section_h = Math.round(r.height); }
  const shown = (e) => { const cs = getComputedStyle(e); const r = e.getBoundingClientRect(); return cs.display !== 'none' && cs.visibility !== 'hidden' && (r.width > 0 || r.height > 0); };
  const big = (r) => r.width * r.height >= 0.5 * IW * IH;
  for (const t of targets) { let els = [];
    for (const s of t.sels || []) { try { els = Array.from(document.querySelectorAll(s)); } catch (x) { els = []; } if (els.length) break; }
    if (!els.length) { out.targets.push({moment: t.moment, found: false}); continue; }
    const vis = els.filter(shown);
    if (!vis.length) { out.targets.push({moment: t.moment, found: true, hidden: true, n: els.length, reduce: t.reduce}); continue; }
    const e0 = vis[0], r0 = e0.getBoundingClientRect(), p0 = getComputedStyle(e0).position;
    if (e0.tagName === 'CANVAS' || e0.tagName === 'VIDEO' || (big(r0) && (p0 === 'fixed' || p0 === 'sticky' || !!e0.querySelector('canvas, video')))) {
      out.targets.push({moment: t.moment, found: true, kind: 'frame', n: els.length, tag: e0.tagName.toLowerCase(), position: p0, reduce: t.reduce}); continue; }
    let el = null;
    if (group && vis.length > 1) el = vis.find(e => group.contains(e) || e.contains(group)) || null;   // экземпляр в группе якоря
    if (!el) { let bd = 1e9; for (const e of vis) { const rr = e.getBoundingClientRect(); const d = Math.abs(rr.top + rr.height / 2 - lineY); if (d < bd) { bd = d; el = e; } } }
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    const rec = {moment: t.moment, found: true, n: els.length, kind: t.geo ? 'geometry' : (t.state ? 'state' : 'geometry'), reduce: t.reduce,
      edge_bottom_offset: Math.round(r.bottom - lineY), edge_top_offset: Math.round(r.top - lineY), center_offset: Math.round(r.top + r.height / 2 - lineY),
      height: Math.round(r.height), width: Math.round(r.width), transform: cs.transform.slice(0, 60), opacity: parseFloat(cs.opacity)};
    if (rec.kind === 'geometry') { let edge = 'bottom';
      if (t.scale) { const oy = parseFloat(String(cs.transformOrigin || '0 0').split(' ')[1]); const lh = el.offsetHeight || r.height;
        if (!isNaN(oy) && lh > 0 && oy >= 0.9 * lh) edge = 'top';      // scale от низа — растёт вверх, конец — верхний край
        const m = cs.transform.match(/^matrix\(([^)]+)\)/);
        if (m) { const v = m[1].split(',').map(Number); rec.scale_x = Math.round(Math.hypot(v[0], v[1]) * 1000) / 1000; rec.scale_y = Math.round(Math.hypot(v[2], v[3]) * 1000) / 1000; }
        else if (cs.transform === 'none') { rec.scale_x = 1; rec.scale_y = 1; } }
      else if (r.height <= 24) edge = 'center';                           // маленькая цель (точка, ромб) — центр
      rec.edge = edge; rec.edge_offset = edge === 'top' ? rec.edge_top_offset : (edge === 'center' ? rec.center_offset : rec.edge_bottom_offset); }
    if (t.state && t.state.prop && window.CSS && CSS.supports(t.state.prop, t.state.from)) {   // изменено от from ↔ центр прошёл линию
      let fromV = null; try { const pr = document.createElement('span'); pr.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none';
        pr.style.setProperty(t.state.prop, t.state.from); (el.parentNode || document.body).appendChild(pr); fromV = getComputedStyle(pr).getPropertyValue(t.state.prop); pr.remove(); } catch (x) {}
      if (fromV !== null) { let changed = 0, passed = 0, mismatch = 0;
        for (const e of vis) { const rr = e.getBoundingClientRect(); const v = getComputedStyle(e).getPropertyValue(t.state.prop);
          const ch = t.state.prop === 'opacity' ? Math.abs(parseFloat(v) - parseFloat(fromV)) > 0.02 : v !== fromV; const ps = rr.top + rr.height / 2 <= lineY + 2;
          changed += ch ? 1 : 0; passed += ps ? 1 : 0; if (ch !== ps) mismatch++; }
        Object.assign(rec, {state_prop: t.state.prop, state_from: fromV, changed, passed, mismatch, n_visible: vis.length}); } }
    out.targets.push(rec); }
  return out; }
"""


GEO_PROPS = ("transform", "translate", "scale", "rotate", "clip-path", "clip", "top", "bottom", "left", "right", "height", "width", "inset")


def station_targets(sec):
    """Цели scroll-linked моментов секции для зонда станций: селекторы по контракту, геометрия (transform и раскладка)
    или состояние (первый трек не из геометрии с from: цвет, opacity), трек scale, стратегия reduce."""
    out = []
    for m in sec.get("moments", []) or []:
        if m.get("class") != "scroll-linked":
            continue
        tr = [t for t in (m.get("tracks") or []) if isinstance(t, dict)]
        props = [str(t.get("property") or "") for t in tr]
        geo = any(p in GEO_PROPS for p in props)
        scale = any(str(t.get("property")) == "scale" or "scale" in (str(t.get("from", "")) + " " + str(t.get("to", ""))).lower() for t in tr)
        st = next(({"prop": str(t["property"]), "from": str(t["from"])} for t in tr
                   if t.get("property") and str(t["property"]) not in GEO_PROPS and not str(t["property"]).startswith(("uniform", "--"))
                   and t.get("from") is not None), None)
        out.append({"moment": m.get("id"), "sels": resolve_target_sel(m.get("target"), m.get("selector_hint"), m.get("id")), "geo": geo,
                    "scale": scale, "state": st, "reduce": (m.get("reduce") or {}).get("strategy")})
    return out


def station_probe(page, spec, mode, out_dir):
    """Станции motion-spec v1 (scene.stations[]): anchor — «якорь на линии окна» (anchor_line), at — доля сцены; замер целей
    scroll-linked моментов секции и кадр станции. Допуск по умолчанию ±24 px (motion-spec.schema.json $defs.station) или threshold
    проверки со словом «станц»/station. Группы целей, скрытые цели, холст и fixed-слой — кадр, трек состояния, край по
    треку, станции долей at."""
    rows = []
    for sec in (spec or {}).get("sections", []) or []:
        stations = ((sec.get("scene") or {}).get("stations")) or []
        if not stations:
            continue
        targets = station_targets(sec)
        tol = 24
        for acc in sec.get("acceptance", []) or []:
            if isinstance(acc.get("threshold"), (int, float)) and ("станц" in str(acc.get("check", "")) or "station" in str(acc.get("check", ""))):
                tol = acc["threshold"]
        for st in stations:
            if st.get("anchor"):
                place, label = {"kind": "anchor", "sels": resolve_target_sel(st["anchor"])}, st["anchor"]
            elif isinstance(st.get("at"), (int, float)):
                place, label = {"kind": "at", "secSels": resolve_target_sel(sec.get("id")), "at": float(st["at"])}, f"at {st['at']}"
            else:
                rows.append({"section": sec.get("id"), "station": st.get("id"), "note": "у станции нет ни anchor, ни at"})
                continue
            try:
                r = page.evaluate(STATION_JS, [place, st.get("anchor_line", "viewport-center"), targets])
            except Exception as e:
                r = {"found": False, "error": str(e)[:100]}
            shot = None
            if r.get("found"):
                try:
                    shot = f"station_{mode}_{sec.get('id')}_{st.get('id')}.jpg"
                    thumb(page.screenshot(type="png"), os.path.join(out_dir, shot), w=640)
                except Exception:
                    shot = None
            rows.append({"section": sec.get("id"), "station": st.get("id"), "anchor": label, "place": place["kind"], "tolerance_px": tol,
                         "shot": shot, **r})
    return rows


def analyze_samples(samp):
    if not samp or samp.get("missing"):
        return {"sampled": False}
    s = samp.get("s") or []
    if len(s) < 3:
        return {"sampled": True, "frames": len(s)}

    def num_t(tr):
        if not tr or tr == "none":
            return (0.0, 0.0, 1.0)
        m = re.match(r"matrix\(([^)]+)\)", tr)
        if m:
            v = [float(x) for x in m.group(1).split(",")]
            return (v[4], v[5], math.hypot(v[0], v[1]))
        m = re.match(r"matrix3d\(([^)]+)\)", tr)
        if m:
            v = [float(x) for x in m.group(1).split(",")]
            return (v[12], v[13], math.hypot(v[0], v[1]))
        return (0.0, 0.0, 1.0)
    ch = []
    for i in range(1, len(s)):
        a, b = s[i - 1], s[i]
        ta, tb = num_t(a[2]), num_t(b[2])
        changed = abs(a[1] - b[1]) > 0.004 or abs(ta[0] - tb[0]) > 0.3 or abs(ta[1] - tb[1]) > 0.3 or abs(ta[2] - tb[2]) > 0.002 or a[3] != b[3] or a[4] != b[4]
        if changed:
            ch.append(b[0])
    props = set()
    t_first, t_last = s[0], s[-1]
    if abs(t_first[1] - t_last[1]) > 0.02 or any(abs(x[1] - t_first[1]) > 0.02 for x in s):
        props.add("opacity")
    if any(num_t(x[2]) != num_t(t_first[2]) for x in s):
        props.add("transform")
    if any(x[3] != t_first[3] for x in s):
        props.add("clip-path")
    if any(x[4] != t_first[4] for x in s):
        props.add("filter")
    return {"sampled": True, "frames": len(s), "moved": bool(ch), "t_start_ms": ch[0] if ch else None, "t_end_ms": ch[-1] if ch else None,
            "duration_ms": (ch[-1] - ch[0]) if len(ch) >= 2 else 0, "props_changed": sorted(props), "opacity_end": round(t_last[1], 2),
            "transform_end": t_last[2][:40]}


def spec_duration_ms(m):
    d = m.get("duration") or {}
    if isinstance(d, dict) and d.get("ms"):
        return float(d["ms"])
    tok = (d or {}).get("token") if isinstance(d, dict) else None
    TOK = {"feedback": 120, "hover": 200, "reveal": 560, "split-line": 800, "hero-scene": 900, "hero-scene-max": 1200, "state": 320, "page": 400,
           "counter": 1200, "cta-pulse": 500, "crossfade-reduce": 180}
    if tok:
        key = str(tok).split(".")[-1].strip("{}")
        return float(TOK.get(key, 0)) or None
    return None


# =====================================================================================================================
# 5. Анализ видео: паузы, «вау»-переходы, листы, вспышки (WCAG 2.3.1)
# =====================================================================================================================
def analyze_video(res, out_dir, mode, keep=False):
    vpath = res.get("video_tmp")
    if not vpath or not os.path.exists(vpath) or SR is None:
        return {"error": "нет видео"}
    import numpy as np
    info = {"video_mb": round(os.path.getsize(vpath) / 1e6, 2)}
    frames, (fw, fh) = SR.read_frames(vpath)
    info["frames"] = len(frames)
    vf = SR.find_flash(frames, vpath)
    tf = res.get("t_flash")
    off = round(vf - tf, 3) if (vf is not None and tf is not None) else 0.0
    info["sync_offset_s"] = off
    fps = SR.FPS
    wins = []
    for w in res.get("windows", []):
        i0 = int(math.ceil((w["t0"] + off + 0.25) * fps))
        i1 = int(math.floor((w["t1"] + off - 0.2) * fps))
        ie = int(math.floor((w["t0"] + off) * fps))
        early = [SR.diff_regions(frames[i - 1], frames[i])[0] for i in range(max(1, ie + 1), min(len(frames), ie + fps + 1))] if ie > 0 else []
        pcts, regs, p1s = [], [], []
        for i in range(max(1, i0 + 1), min(len(frames), i1 + 1)):
            pc, rg = SR.diff_regions(frames[i - 1], frames[i])
            pcts.append(pc)
            regs.append(rg if pc >= SR.NOISE else 0)
            if i - fps >= i0 and i - fps >= 0:
                p1s.append(float((np.abs(frames[i].astype(np.int16) - frames[i - fps].astype(np.int16)).max(axis=2) > SR.THR).mean() * 100))
        moving = [p for p in pcts if p >= SR.NOISE]
        wins.append({"step": w["step"], "y": w["y"], "pairs": len(pcts), "pct_mean": round(sum(pcts) / len(pcts), 2) if pcts else None,
                     "early_max": round(max(early), 1) if early else None,
                     "pct_1s": round(max(p1s), 2) if p1s else None, "regions_max": max(regs) if regs else 0,
                     "continuous": bool(pcts) and len(moving) >= 0.6 * len(pcts)})
    # «вау»-переход (C 03/02): ≥ 10 % пикселей меняется за 0,25 с сразу после успокоения прокрутки (появление сцены)
    ws = [w for w in wins if w["pairs"]]
    info["wow_transitions"] = sum(1 for w in ws if (w.get("early_max") or 0) >= 10 and w["step"] > 0)
    first = ws[0] if ws else {}
    info.update({"windows": wins, "idle_first_pct_1s": first.get("pct_1s"), "idle_first_pct": first.get("pct_mean"),
                 "continuous_windows": sum(1 for w in ws if w["continuous"]), "windows_n": len(ws),
                 "loud_windows": sum(1 for w in ws if (w.get("pct_1s") or 0) > 5), "pct_1s_max": max((w.get("pct_1s") or 0) for w in ws) if ws else None,
                 "regions_max": max((w["regions_max"] for w in ws), default=0)})
    # листы: середина каждой паузы + смена сцены, ≤ 32 кадров
    keep_f, labels = [], []
    for w in res.get("windows", []):
        i = int(((w["t0"] + w["t1"]) / 2 + off) * fps)
        if 0 <= i < len(frames):
            keep_f.append(frames[i])
            labels.append(f"{mode} s{w['step']} y={w['y']}")
    sheets = []
    for k in range(0, min(len(keep_f), 32), 16):
        p = os.path.join(out_dir, f"sheet_{mode}_{k // 16 + 1:02d}.jpg")
        SR.sheet(keep_f[k:k + 16], p, labels[k:k + 16], quality=68)
        sheets.append(os.path.basename(p))
    info["sheets"] = sheets
    del frames
    info["flash"] = flash_scan(vpath, res, off)
    if keep:
        shutil.copy(vpath, os.path.join(out_dir, f"video_{mode}.webm"))
    return info


def flash_scan(vpath, res, off, fps=25, width=256):
    """WCAG 2.3.1 по кадрам 25 к/с: пара противоположных изменений относительной яркости ≥ 0,1 при тёмном < 0,8 — вспышка;
    > 3 вспышек в любую секунду на площади ≥ 25 % прямоугольника 341×256 CSS px (10° при 1024×768) — провал.
    Красная — упрощённо: переход, где в одном из состояний R/(R+G+B) ≥ 0,8 и насыщенность высокая."""
    import numpy as np
    try:
        w0, h0 = SR.ffprobe_size(vpath)
    except Exception as e:
        return {"error": str(e)[:80]}
    h = int(round(h0 * width / w0 / 2)) * 2
    vp_w = (res.get("page_first") or {}).get("innerW") or 1440
    css_per_px = vp_w / width
    win_w = max(2, int(round(341 / css_per_px)))
    win_h = max(2, int(round(256 / css_per_px)))
    cmd = [kbpaths.ffmpeg(), "-hide_banner", "-loglevel", "error", "-threads", "4", "-i", vpath, "-vf", f"fps={fps},scale={width}:{h}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    fsz = width * h * 3
    ring = []
    ref = dirn = None
    ring_red = []
    t_flash0 = (res.get("t_flash") or 0) + off
    max_general = max_red = 0.0
    worst_t = None
    n = 0
    while True:
        buf = p.stdout.read(fsz)
        if len(buf) < fsz:
            break
        t = n / fps
        n += 1
        f = np.frombuffer(buf, dtype=np.uint8).reshape(h, width, 3).astype(np.float32) / 255.0
        lin = np.where(f <= 0.04045, f / 12.92, ((f + 0.055) / 1.055) ** 2.4)
        L = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
        s = f.sum(axis=2) + 1e-6
        red = (f[..., 0] / s >= 0.8) & (f[..., 0] > 0.3)
        if ref is None:
            ref = L.copy()
            dirn = np.zeros(L.shape, dtype=np.int8)
            prev_red = red
            tr = np.zeros(L.shape, dtype=np.int8)
            trr = np.zeros(L.shape, dtype=np.int8)
        else:
            up = (L - ref >= 0.1) & (np.minimum(L, ref) < 0.8) & (dirn <= 0)
            down = (ref - L >= 0.1) & (np.minimum(L, ref) < 0.8) & (dirn >= 0)
            tr = (up | down).astype(np.int8)
            ext_up = (dirn >= 0) & (L > ref)
            ext_down = (dirn <= 0) & (L < ref)
            ref = np.where(up | down | ext_up | ext_down, L, ref)
            dirn = np.where(up, 1, np.where(down, -1, dirn)).astype(np.int8)
            trr = (tr.astype(bool) & (red | prev_red)).astype(np.int8)
            prev_red = red
        in_sync = t_flash0 - 0.1 <= t <= t_flash0 + 0.6
        if in_sync:
            tr = np.zeros_like(tr)
            trr = np.zeros_like(trr)
        ring.append(tr)
        ring_red.append(trr)
        if len(ring) > fps:
            ring.pop(0)
            ring_red.pop(0)
        if len(ring) == fps and n % 5 == 0:
            cnt = np.sum(ring, axis=0)
            cnt_r = np.sum(ring_red, axis=0)
            for arr, kind in ((cnt, "g"), (cnt_r, "r")):
                mask = (arr >= 7).astype(np.float32)          # > 3 вспышек = ≥ 7 переходов за 1 с
                if mask.sum() == 0:
                    continue
                ii = mask.cumsum(0).cumsum(1)
                ii = np.pad(ii, ((1, 0), (1, 0)))
                ww, hh = min(win_w, width), min(win_h, h)
                area = ii[hh:, ww:] - ii[:-hh, ww:] - ii[hh:, :-ww] + ii[:-hh, :-ww]
                frac = float(area.max()) / (ww * hh)
                if kind == "g" and frac > max_general:
                    max_general, worst_t = frac, round(t - off, 2)
                if kind == "r" and frac > max_red:
                    max_red = frac
    p.stdout.close()
    p.wait()
    return {"frames": n, "fps": fps, "window_px": [win_w, win_h], "max_area_frac_general": round(max_general, 3),
            "max_area_frac_red": round(max_red, 3), "fail": max_general >= 0.25 or max_red >= 0.25, "worst_t_s": worst_t}


# =====================================================================================================================
# 6. Ворота: чтение effect-gates.yaml, пороги уровня, оценка
# =====================================================================================================================
def load_levels(path=LEVELS_YAML):
    try:
        import yaml
        d = yaml.safe_load(open(path, encoding="utf-8"))
        return {L["id"]: L for L in d.get("levels", [])}, d
    except Exception:
        return {}, {}


def dig(d, path):
    cur = d
    for k in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(k)
        elif isinstance(cur, list) and k.isdigit() and int(k) < len(cur):
            cur = cur[int(k)]
        else:
            return None
    return cur


_PROFILES, _EFFECTS, _GL = {}, None, {}


def page_profile(level, page_type=None):
    """Профиль страницы site для ссылок «profile.*»: <page_type>@<уровень> с исключениями overrides (page_gates.py), без
    типа — числа уровня budgets.yaml."""
    key = (level, page_type)
    if key not in _PROFILES:
        prof = None
        if page_type:
            try:
                prof = PG.resolve_profile(f"{page_type}@{level}")
            except ValueError as e:
                log(f"  профиль {page_type}@{level}: {e} — берутся числа уровня")
        if prof is None:
            lv = PG.load_budgets()["levels"][level]
            prof = {"id": f"@{level}", "level": level, "outcome": lv["outcome"], "weight": lv["weight"]}
        _PROFILES[key] = prof
    return _PROFILES[key]


def effects_catalog():
    global _EFFECTS
    if _EFFECTS is None:
        import yaml
        d = yaml.safe_load(open(EFFECTS_YAML, encoding="utf-8"))
        _EFFECTS = {e["id"]: e for e in d.get("effects") or [] if isinstance(e, dict) and e.get("id")}
    return _EFFECTS


def resolve_ref(ref, level, device, levels, page_type=None):
    """threshold_ref → (найдено ли поле, число или None): путь в уровне ambition-levels.yaml; «profile.<путь>» — профиль
    страницы site; «effects.yaml#<id>.<путь>» — запись каталога эффектов. <device> — устройство режима; узел {mobile,
    desktop} — значение устройства, узел {goal, poor} — goal. Поле есть, а числа нет (null) — (True, None): порог открыт."""
    ref = str(ref).replace("<device>", device)
    if ref.startswith("profile."):
        node, path = page_profile(level, page_type), ref[len("profile."):]
    elif ref.startswith("effects.yaml#"):
        eid, _, path = ref[len("effects.yaml#"):].partition(".")
        node = effects_catalog().get(eid)
        if node is None:
            return False, None
    else:
        node, path = levels.get(level) or {}, ref
    cur = node
    for k in path.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        elif isinstance(cur, list) and k.isdigit() and int(k) < len(cur):
            cur = cur[int(k)]
        else:
            return False, None
    if isinstance(cur, dict) and device in cur:
        cur = cur[device]
    elif isinstance(cur, dict) and "all" in cur:
        cur = cur["all"]
    if isinstance(cur, dict) and "goal" in cur:
        cur = cur["goal"]
    return True, (cur if isinstance(cur, (int, float)) and not isinstance(cur, bool) else None)


def threshold_for(g, level, device, levels, page_type=None):
    if g.get("threshold_ref"):
        _, v = resolve_ref(g["threshold_ref"], level, device, levels, page_type)
        if v is None:
            return None
        return v * float(g.get("scale", 1))
    thr = g.get("threshold")
    if isinstance(thr, dict):
        v = thr.get(level, thr.get("all"))
        if isinstance(v, dict):
            v = v.get(device, v.get("all"))
        return v
    return thr


def use_gate_limits(gates_doc):
    """Поля limits и число threshold строк ворот — для производных метрик (derive), которые считают по ним находки."""
    _GL.clear()
    for g in (gates_doc or {}).get("gates") or []:
        if isinstance(g, dict) and g.get("id"):
            _GL[g["id"]] = dict(g.get("limits") or {}, threshold=g.get("threshold"))


def LIM(gid, key):
    """Число строки ворот: limits.<key> или threshold (key='threshold'); нет строки или поля — ошибка с адресом."""
    if not _GL:
        import yaml
        use_gate_limits(yaml.safe_load(open(GATES_DEFAULT, encoding="utf-8")))
    v = (_GL.get(gid) or {}).get(key)
    if v is None:
        raise KeyError(f"нет {'threshold' if key == 'threshold' else 'limits.' + key} у строки {gid} (effect-gates.yaml)")
    return v


def sev_for(g, level):
    s = g.get("severity", "S")
    if isinstance(s, dict):
        s = s.get(level, s.get("all", "S"))
    return s


def compare_op(val, op, thr):
    if op == "false":
        return not val
    if op == "true":
        return bool(val)
    if op == "empty":
        return not val
    if thr is None:
        return None
    if op in ("<=", "≤"):
        return val <= thr
    if op in ("<", ):
        return val < thr
    if op in (">=", "≥"):
        return val >= thr
    if op in (">", ):
        return val > thr
    if op in ("==", "="):
        return val == thr
    if op == "!=":
        return val != thr
    if op == "false":
        return not val
    if op == "true":
        return bool(val)
    if op == "empty":
        return not val
    return None


DEVICE = {"desk": "desktop", "rm": "desktop", "nojs": "desktop", "nogl": "desktop", "mob": "mobile"}


def evaluate_gates(gates_doc, results, level, levels, spec=None, page_type=None):
    rows = []
    for g in gates_doc.get("gates", []):
        if g.get("auto") is False:
            rows.append({"id": g["id"], "name": g.get("name"), "mode": "—", "found": "вручную", "threshold": g.get("threshold_text", "—"),
                         "verdict": "MANUAL", "severity": sev_for(g, level), "where": g.get("method", ""), "site": g.get("site", "")})
            continue
        lv = g.get("levels")
        if lv and level not in lv:
            continue
        modes = g.get("modes") or [g.get("mode", "desk")]
        for mode in modes:
            r = results.get(mode)
            if not r:
                continue
            dev = DEVICE.get(mode, "desktop")
            val = dig(r, g["metric"])
            if isinstance(val, list) and g.get("op") not in ("empty",):
                val_cmp = len(val)
            else:
                val_cmp = val
            thr = threshold_for(g, level, dev, levels, page_type)
            if spec and g.get("spec_override"):
                sv = dig(spec, g["spec_override"])
                if isinstance(sv, (int, float)) and (thr is None or sv < thr):
                    thr = sv
            if val_cmp is None:
                ok = None
            else:
                try:
                    ok = compare_op(val_cmp, g.get("op", "<="), thr)
                except TypeError:
                    ok = None
            where = ""
            if g.get("where"):
                w = dig(r, g["where"])
                where = (", ".join(str(x) for x in w[:4]) if isinstance(w, list) else str(w))[:160] if w not in (None, [], "") else ""
            rows.append({"id": g["id"], "name": g.get("name"), "mode": mode, "found": val if not isinstance(val, list) else (f"{len(val)}: " + ", ".join(str(x) for x in val[:3])),
                         "threshold": ({"empty": "пусто", "false": "нет", "true": "да"}.get(g.get("op")) or (f"{g.get('op', '<=')} {thr}" if thr is not None else
                                       ("числа нет — " + (g.get("label") or "открыто") if g.get("threshold_ref") else g.get("threshold_text", "—")))),
                         "verdict": "PASS" if ok is True else ("FAIL" if ok is False else "N/A"), "severity": sev_for(g, level), "where": where,
                         "site": g.get("site", ""), "label": g.get("label", "")})
    return rows


def round_half_away(x):
    """Целое по схеме станции: половина — от нуля (−24,5 → −25, −24,2 → −24)."""
    return int(math.copysign(math.floor(abs(x) + 0.5), x))


def station_rows(st_res, mode):
    """Строки сверки станций. Геометрия — |край цели − линия окна| после округления ≤ допуска; состояние — «изменено» = «прошли линию»
    у всех экземпляров; кадр (холст, видео, fixed-слой) и скрытая цель — без вердикта; reduce — конечное состояние (final-state:
    все экземпляры изменены, scale ≈ 1), иначе кадры для глаза. Цель без поля kind — геометрия."""
    rows = []
    for r in st_res or []:
        name = f"{r.get('section')}:{r.get('station')}"
        if not r.get("found"):
            rows.append({"moment": name, "mode": mode, "verdict": "N/A" if r.get("note") else "FAIL",
                         "found": r.get("note") or ("секция станции не найдена в DOM" if r.get("reason") == "section" else "якорь станции не найден в DOM"),
                         "spec": r.get("anchor", "—"), "where": "x-dom-contract: data-section / data-group", "note": ""})
            continue
        tol = r.get("tolerance_px", 24)
        tg = [t for t in r.get("targets", []) if t.get("found")]
        if not tg:
            rows.append({"moment": name, "mode": mode, "verdict": "N/A", "found": "целей scroll-linked нет или не найдены",
                         "spec": f"±{tol} px", "where": r.get("shot") or "", "note": "кадр станции — сверить глазами с раскадровкой"})
            continue

        def off(t):
            return t["edge_offset"] if t.get("edge_offset") is not None else t["edge_bottom_offset"]
        geo = [t for t in tg if not t.get("hidden") and t.get("kind", "geometry") == "geometry"
               and (t.get("edge_offset") is not None or t.get("edge_bottom_offset") is not None)]
        state = [t for t in tg if not t.get("hidden") and t.get("mismatch") is not None]
        frames = [t for t in tg if t.get("kind") == "frame"]
        hidden = [t for t in tg if t.get("hidden")]
        # край минус линия окна — целое, округление половины от нуля (motion-spec.schema.json $defs.station); -0.0 из JS → 0
        parts = [f"{t['moment']}: край{('-' + t['edge']) if t.get('edge') else ''} {round_half_away(off(t)):+d} px" for t in geo]
        parts += [f"{t['moment']}: изменено {t['changed']} из {t.get('n_visible', t.get('n'))}, прошли линию {t['passed']}" for t in state]
        parts += [f"{t['moment']}: {t.get('tag') or 'слой'} — кадр" for t in frames]
        parts += [f"{t['moment']}: скрыт" for t in hidden]
        note = ""
        if mode == "rm":
            fin_state = [t for t in state if t.get("reduce") in ("final-state", None)]
            fin_geo = [t for t in geo if t.get("reduce") in ("final-state", None) and t.get("scale_y") is not None]
            bad = [t for t in fin_state if t.get("changed") != t.get("n_visible", t.get("n"))]
            bad += [t for t in fin_geo if min(t.get("scale_y") or 0, t.get("scale_x") or 0) < 0.98]
            ok = (not bad) if (fin_state or fin_geo) else None
            note = "reduce: конечное состояние (всё изменено, scale ≈ 1)" if ok is not None else "reduce: станции — кадры для глаза"
        else:
            bad = [t for t in geo if abs(round_half_away(off(t))) > tol] + [t for t in state if t.get("mismatch")]
            ok = (not bad) if (geo or state) else None
            if ok is None and frames:
                note = "холст, видео или fixed-слой — сверить кадр станции глазами или судьёй по раскадровке"
        at_place = r.get("place") == "at"
        rows.append({"moment": name, "mode": mode, "verdict": "PASS" if ok is True else ("FAIL" if ok is False else "N/A"),
                     "found": ("; ".join(parts) or "целей scroll-linked нет")[:160],
                     "spec": (f"доля сцены {r.get('anchor')}, край цели ±{tol} px" if at_place else f"якорь {r.get('anchor')} на линии окна, край цели ±{tol} px"),
                     "where": r.get("shot") or "", "note": note})
    return rows


def spec_rows(spec_res, mode):
    rows = []
    for r in spec_res or []:
        if r.get("missing") or not r.get("sel"):
            rows.append({"moment": r.get("id"), "mode": mode, "verdict": "FAIL", "found": "цель не найдена в DOM", "spec": r.get("target"),
                         "where": "контракт DOM: data-section / data-slot / data-moment"})
            continue
        exp = r.get("spec_ms")
        dur = r.get("duration_ms")
        notes = []
        ok = True
        # uniform шейдера, содержимое canvas/video и custom properties выборка стилей не видит — не PASS, а N/A («Звено»)
        props = [str(p) for p in (r.get("spec_props") or []) if p]
        seen = [p for p in props if p.split(":")[0].split("-")[0] in ("opacity", "transform", "translate", "scale", "rotate", "clip", "filter")]
        blind = str(r.get("tag") or "").upper() in ("CANVAS", "VIDEO") or bool(props and not seen)
        if blind:
            ok = None
            notes.append("свойство вне стилей элемента (uniform, canvas, video, custom) — выборка не видит; сверка кадрами станций и глазами")
        elif mode != "rm" and r.get("class") == "scroll-linked" and not r.get("moved"):
            ok = None
            notes.append("скраб не замечен при прокрутке выборки — сверить станциями")
        if blind:
            pass
        elif mode == "rm":
            if r.get("moved") and r.get("reduce") in ("final-state", "static-poster", "stop-loop", "stations"):
                ok = False
                notes.append("в reduce цель движется")
            if (r.get("opacity_end") or 1) < 0.95 and r.get("reduce") == "final-state":
                ok = False
                notes.append(f"конечное состояние не видно (opacity {r.get('opacity_end')})")
        else:
            if r.get("class") == "one-shot" and not r.get("moved") and r.get("trigger") in ("in-view",):
                notes.append("движение не замечено (доиграло до выборки или не запущено)")
                ok = None
            if exp and dur and r.get("class") == "one-shot":
                if abs(dur - exp) > max(0.25 * exp, 120):
                    ok = False
                    notes.append(f"длительность {dur} мс против {exp:.0f}")
            miss = [p for p in (r.get("spec_props") or []) if p and p.split("-")[0] in ("opacity", "transform", "translate", "scale", "rotate", "clip")
                    and not any(p.startswith(x.split("-")[0]) or (x == "transform" and p in ("translate", "scale", "rotate")) for x in (r.get("props_changed") or []))]
            if r.get("moved") and miss:
                notes.append("не меняются: " + ", ".join(miss))
                ok = False if ok else ok
        rows.append({"moment": r.get("id"), "mode": mode, "verdict": "PASS" if ok is True else ("FAIL" if ok is False else "N/A"),
                     "found": f"{'движется' if r.get('moved') else 'стоит'}; {dur} мс; {', '.join(r.get('props_changed') or [])}",
                     "spec": f"{r.get('class')} {r.get('trigger')} {exp or '—'} мс {', '.join(p for p in (r.get('spec_props') or []) if p)}",
                     "where": r.get("sel"), "note": "; ".join(notes)})
    return rows


# =====================================================================================================================
# 7. Отчёт
# =====================================================================================================================
def presentation_layer(results, level, levels, gates_doc):
    """Слой подачи по режимам (десктоп, телефон, reduce): JS эффектов и движения в первом экране и за сессию, JS и wasm 3D
    (EG-WEIGHT-02), wasm-рантаймы подачи 2D (EG-WEIGHT-11), видео первого экрана. Порог один — EG-WEIGHT-01 уровня (reduce —
    с порогом десктопа); вес страницы целиком — ворота страницы site. Картинка первого экрана — бюджет ассета ai-media,
    здесь ссылкой."""
    row = next((g for g in (gates_doc or {}).get("gates") or [] if g.get("id") == "EG-WEIGHT-01"), None)
    out = {"modes": {}, "threshold_row": "EG-WEIGHT-01" if row else None}
    for mode in ("desk", "mob", "rm"):
        r = results.get(mode)
        if not isinstance(r, dict) or r.get("error"):
            continue
        net, dev = r.get("net") or {}, DEVICE[mode]
        fo = net.get("first_only") or {}
        thr = threshold_for(row, level, dev, levels) if row else None
        js = fo.get("js_effects_first_kb")
        out["modes"][mode] = {"device": dev, "js_effects_first_kb": js, "js_effects_session_kb": net.get("js_effects_session_kb"),
                              "js_3d_session_kb": net.get("js_3d_session_kb"), "wasm_presentation_kb": net.get("wasm_presentation_kb"),
                              "video_first_kb": fo.get("video_first_kb"), "threshold_js_effects_kb": thr,
                              "over": (js > thr) if (js is not None and thr is not None) else None}
    try:
        import yaml
        img = ((yaml.safe_load(open(AI_THRESHOLDS, encoding="utf-8")).get("thresholds") or {}).get("budget") or {}).get("image") or {}
        out["hero_image"] = {"ref": "ai-media/11-evaluation-qa/thresholds.yaml#thresholds.budget.image",
                             "hero_kb": (img.get("hero_kb") or {}).get("value"), "hero_mobile_kb": (img.get("hero_mobile_kb") or {}).get("value"),
                             "check": "asset_audit.py audit --stage web --slot hero [--mobile]"}
    except Exception as e:  # noqa: BLE001
        out["hero_image"] = {"error": str(e)[:120]}
    return out


def render(target, level, results, rows, srows, gates_doc, pres=None):
    fails = [r for r in rows if r["verdict"] == "FAIL"]
    by = {s: len([r for r in fails if r["severity"] == s]) for s in ("B", "S", "D")}
    L = [f"# Ворота эффектов: {target}", "",
         f"`{VERSION}` · уровень **{level}** · ворота `{os.path.relpath(gates_doc.get('_path', GATES_DEFAULT), ROOT)}` v{gates_doc.get('version', '?')} · "
         f"режимы: {', '.join(k for k in results if not k.startswith('_'))} · {time.strftime('%Y-%m-%d %H:%M')}", "",
         f"**Итог: FAIL {len(fails)} — B {by['B']}, S {by['S']}, D {by['D']}; N/A {len([r for r in rows if r['verdict'] == 'N/A'])}; вручную "
         f"{len([r for r in rows if r['verdict'] == 'MANUAL'])}.** Иерархия: ворота страницы site выше этих; ворота ассетов (ai-media, blender) "
         f"страницу не блокируют.", ""]
    if fails:
        L += ["## Что править (правило → найдено → порог → где)", "", "```text"]
        for s in ("B", "S", "D"):
            for r in [x for x in fails if x["severity"] == s]:
                L.append(f"[{s}] {r['id']:<12} {r['mode']:<5} → {str(r['found'])[:50]} → {r['threshold']} → {r['where'] or r['name'][:60]}")
        L += ["```", ""]
    L += ["## Все ворота", "", "| ID | Правило | Режим | Найдено | Порог | Вердикт | Сер. | Сверка с site | Где |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['id']} | {r['name']} | {r['mode']} | {str(r['found'])[:60]} | {r['threshold']} | {r['verdict']} | {r['severity']} | {r.get('site', '')} | {str(r.get('where', ''))[:80]} |")
    if srows:
        L += ["", "## Сверка с motion-spec", "", "| Момент | Режим | Найдено | По спецификации | Вердикт | Цель | Примечание |", "|---|---|---|---|---|---|---|"]
        for r in srows:
            L.append(f"| {r['moment']} | {r['mode']} | {r['found']} | {r['spec']} | {r['verdict']} | `{r['where']}` | {r.get('note', '')} |")
    st_sum = [(m, s) for m in ("desk", "mob", "rm") if isinstance(results.get(m), dict) for s in ((results[m].get("derived") or {}).get("stations") or [])]
    if st_sum:   # метрика зонда станций: tip_offset_px, filled
        dash = lambda v: "—" if v is None else v
        L += ["", "## Станции (метрика зонда I: tip_offset_px, filled)", "", "| Станция | Режим | tip_offset_px | Цель | filled / ожидалось |", "|---|---|---|---|---|"]
        for m, s in st_sum:
            L.append(f"| {s['section']}:{s['station']} | {m} | {dash(s['tip_offset_px'])} | {dash(s.get('tip_moment'))} | {dash(s['filled'])} / {dash(s['filled_expected'])} |")
    if pres and pres.get("modes"):
        L += ["", "## Слой подачи по режимам (порог — EG-WEIGHT-01 уровня; вес страницы — ворота site)", "",
              "| Режим | JS эффектов, первый экран, КБ | JS эффектов, сессия | JS и wasm 3D, сессия (EG-WEIGHT-02) | wasm-рантаймы подачи (EG-WEIGHT-11) | видео первого экрана | порог JS эффектов |",
              "|---|---|---|---|---|---|---|"]
        for m, x in pres["modes"].items():
            L.append(f"| {m} ({x['device']}) | {x['js_effects_first_kb']} | {x['js_effects_session_kb']} | {x['js_3d_session_kb']} | "
                     f"{x['wasm_presentation_kb']} | {x['video_first_kb']} | {x['threshold_js_effects_kb']}{' — выше' if x.get('over') else ''} |")
        hi = pres.get("hero_image") or {}
        if hi.get("ref"):
            L += ["", f"Картинка первого экрана — бюджет ассета ai-media `{hi['ref']}`: десктоп {hi.get('hero_kb')} КБ, телефон "
                  f"{hi.get('hero_mobile_kb')} КБ; проверка — `{hi.get('check')}`."]
    sheets = [s for k, v in results.items() if isinstance(v, dict) for s in ((v.get("video") or {}).get("sheets") or [])]
    if sheets:
        L += ["", "## Кадры", ""] + [f"- `{s}`" for s in sheets]
    return "\n".join(L) + "\n"


def fix_text(target, rows, srows):
    out = [f"ОТЧЁТ ПРОВЕРОК ДВИЖЕНИЯ (правило → найдено → порог → где) · {target} · {time.strftime('%Y-%m-%d %H:%M')}"]
    for s in ("B", "S", "D"):
        for r in [x for x in rows if x["verdict"] == "FAIL" and x["severity"] == s]:
            out.append(f"  [{s}] {r['id']} {r['name']} ({r['mode']}) → {str(r['found'])[:60]} → {r['threshold']} → {r['where'] or '—'}")
    for r in srows or []:
        if r["verdict"] == "FAIL":
            out.append(f"  [S] motion-spec {r['moment']} ({r['mode']}) → {r['found']} → {r['spec']} → {r['where']} {r.get('note', '')}")
    if len(out) == 1:
        out.append("  нарушений нет")
    return "\n".join(out) + "\n"


# =====================================================================================================================
# 8. Самопроверка
# =====================================================================================================================
SELFTEST_GATES = """
version: "test"
gates:
  - {id: T-01, name: "LoAF", modes: [desk, mob], metric: scroll.loaf_pct, op: "<=", threshold: {all: {desktop: 2, mobile: 10}}, severity: S}
  - {id: T-02, name: "первый экран", modes: [mob], metric: net.first_kb, op: "<=", threshold_ref: "profile.weight.first_screen_kb.<device>", severity: D}
  - {id: T-03, name: "видео в reduce", modes: [rm], metric: net.video_session_kb, op: "<=", threshold: 0, severity: S}
  - {id: T-04, name: "петли", modes: [desk], metric: loops.loops_in_view_max, op: "<=", threshold: {L0: 1, L1: 2, L2: 3}, severity: S}
  - {id: T-05, name: "вручную", auto: false, severity: S, method: "глазами"}
  - {id: T-06, name: "под текстом", modes: [desk], metric: loops.under_text, op: "empty", severity: S}
"""


def selftest():
    ok = True

    def check(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {name}: {got!r}" + ("" if good else f" (ожидалось {want!r})"))
    import yaml
    import numpy as np
    check("scroll_record импортирован", SR is not None, True)
    levels, _doc = load_levels()
    check("ambition-levels.yaml: L0, L1, L2", sorted(levels), ["L0", "L1", "L2"])
    gd = yaml.safe_load(SELFTEST_GATES)
    res = {"desk": {"scroll": {"loaf_pct": 3.1}, "loops": {"loops_in_view_max": 2, "under_text": []}, "net": {"first_kb": 1000.0}},
           "mob": {"scroll": {"loaf_pct": 8.0}, "net": {"first_kb": 2200.0}},
           "rm": {"net": {"video_session_kb": 350.0}}}
    rows = {(r["id"], r["mode"]): r for r in evaluate_gates(gd, res, "L1", levels)}
    check("T-01 desk 3,1 > 2 → FAIL", rows[("T-01", "desk")]["verdict"], "FAIL")
    check("T-01 mob 8 ≤ 10 → PASS", rows[("T-01", "mob")]["verdict"], "PASS")
    check("T-02 порог — профиль site L1, телефон 2 000 КБ → FAIL 2 200", (rows[("T-02", "mob")]["verdict"], rows[("T-02", "mob")]["threshold"]), ("FAIL", "<= 2000.0"))
    rows_lead = {(r["id"], r["mode"]): r for r in evaluate_gates(gd, res, "L1", levels, page_type="landing-lead-services")}
    check("T-02 с --page-type landing-lead-services: исключение профиля, телефон 1 500", rows_lead[("T-02", "mob")]["threshold"], "<= 1500.0")
    check("T-03 reduce видео 350 КБ → FAIL", rows[("T-03", "rm")]["verdict"], "FAIL")
    check("T-04 петли 2 ≤ 2 (L1) → PASS", rows[("T-04", "desk")]["verdict"], "PASS")
    check("T-05 вручную", rows[("T-05", "—")]["verdict"], "MANUAL")
    check("T-06 под текстом пусто → PASS", rows[("T-06", "desk")]["verdict"], "PASS")
    check("цель motion-spec → селекторы", resolve_target_sel("hero.headline")[0], '[data-section="hero"] [data-slot="headline"]')
    check("цель с моментом и fx → data-moment первым, data-fx", resolve_target_sel("hero.fx-glow", None, "m-hero-glow")[:2],
          ['[data-moment="m-hero-glow"]', '[data-section="hero"] [data-fx="glow"]'])
    check("длительность из токена", spec_duration_ms({"duration": {"token": "motion.marketing.duration.reveal"}}), 560.0)
    s = {"s": [[0, 0.0, "matrix(1, 0, 0, 1, 0, 24)", "none", "none", 100, 0], [16, 0.2, "matrix(1, 0, 0, 1, 0, 20)", "none", "none", 100, 0],
               [300, 0.8, "matrix(1, 0, 0, 1, 0, 5)", "none", "none", 100, 0], [560, 1.0, "none", "none", "none", 100, 0], [700, 1.0, "none", "none", "none", 100, 0]]}
    an = analyze_samples(s)
    check("выборка: движение 16→560 мс, opacity и transform", (an["moved"], an["duration_ms"], an["props_changed"]), (True, 544, ["opacity", "transform"]))
    sr = spec_rows([{"id": "m1", "sel": "h1", "class": "one-shot", "trigger": "load", "spec_ms": 560.0, "spec_props": ["opacity", "transform"], **an}], "desk")
    check("сверка с motion-spec: 544 против 560 → PASS", sr[0]["verdict"], "PASS")
    st = station_rows([{"section": "hiw", "station": "s2", "anchor": "hiw.step-2", "tolerance_px": 24, "found": True, "shot": "x.jpg",
                        "targets": [{"moment": "m-line", "found": True, "edge_bottom_offset": -97}]}], "desk")
    check("станция: край −97 px при допуске ±24 → FAIL", st[0]["verdict"], "FAIL")
    edge = lambda v: station_rows([{"section": "hiw", "station": "s2", "anchor": "hiw.step-2", "tolerance_px": 24, "found": True, "shot": "x.jpg",  # noqa: E731
                                    "targets": [{"moment": "m-line", "found": True, "edge_offset": v, "edge_bottom_offset": v}]}], "desk")[0]["verdict"]
    check("станция по схеме: −24,2 → −24 PASS; −24,5 → −25 FAIL; 24,49 → 24 PASS", (edge(-24.2), edge(-24.5), edge(24.49)), ("PASS", "FAIL", "PASS"))
    # станции — группа целей, состояние, скрытая цель, кадр холста, reduce
    base = {"section": "hiw", "station": "s2", "anchor": "hiw.step-2", "place": "anchor", "tolerance_px": 24, "found": True, "shot": "x.jpg"}
    line0 = {"moment": "line", "found": True, "kind": "geometry", "edge": "bottom", "edge_offset": 0, "edge_bottom_offset": 0, "reduce": "final-state"}
    mark_ok = {"moment": "marker", "found": True, "kind": "state", "changed": 2, "passed": 2, "mismatch": 0, "n_visible": 4, "n": 4, "reduce": "final-state"}
    st2 = station_rows([{**base, "targets": [line0, mark_ok, {"moment": "bob", "found": True, "hidden": True, "n": 1}]}], "desk")
    check("станция: линия 0 px, маркеры 2 = 2, грузик скрыт → PASS", st2[0]["verdict"], "PASS")
    st2b = station_rows([{**base, "targets": [{**line0, "edge_offset": -0.0, "edge_bottom_offset": -0.0}]}], "desk")
    check("станция: край −0.0 (float из JS) не ломает формат → PASS", st2b[0]["verdict"], "PASS")
    st3 = station_rows([{**base, "targets": [{**line0, "edge_offset": -28}, mark_ok]}], "desk")
    check("станция: конец линии −28 px → FAIL", st3[0]["verdict"], "FAIL")
    st4 = station_rows([{**base, "targets": [{**mark_ok, "passed": 3, "mismatch": 1}]}], "desk")
    check("станция: маркер залит не там, где линия → FAIL", st4[0]["verdict"], "FAIL")
    st5 = station_rows([{**base, "place": "at", "anchor": "at 0.5", "targets": [{"moment": "scene", "found": True, "kind": "frame", "tag": "canvas", "n": 1}]}], "desk")
    check("станция: fixed-холст — кадр, без вердикта («Звено»)", (st5[0]["verdict"], "кадр" in st5[0]["found"]), ("N/A", True))
    st6 = station_rows([{**base, "targets": [{**line0, "scale_y": 1.0, "scale_x": 1.0}, {**mark_ok, "changed": 4, "passed": 2, "mismatch": 2}]}], "rm")
    check("станция reduce: линия целиком, 4 из 4 залиты → PASS", st6[0]["verdict"], "PASS")
    st7 = station_rows([{**base, "targets": [{**mark_ok, "changed": 1}]}], "rm")
    check("станция reduce: залит 1 из 4 → FAIL", st7[0]["verdict"], "FAIL")
    sec = {"moments": [{"id": "line", "class": "scroll-linked", "target": "hiw.fx-line", "reduce": {"strategy": "final-state"},
                        "tracks": [{"property": "transform", "from": "scaleY(0)", "to": "scaleY(1)"}]},
                       {"id": "mark", "class": "scroll-linked", "target": "hiw.fx-mark", "tracks": [{"property": "background-color", "from": "transparent", "to": "var(--a)"}]},
                       {"id": "scene", "class": "scroll-linked", "target": "hiw.fx-gl", "tracks": [{"property": "uniform:uStory", "from": 0, "to": 1}]}]}
    check("цели станций: линия — геометрия и scale; маркер — состояние; uniform — ни то ни другое",
          [(t["geo"], t["scale"], bool(t["state"])) for t in station_targets(sec)], [(True, True, False), (False, False, True), (False, False, False)])
    sr2 = spec_rows([{"id": "wake", "sel": "canvas.stage", "tag": "CANVAS", "class": "one-shot", "trigger": "load", "spec_ms": 1200.0,
                      "spec_props": ["uniform:uWake"], "sampled": True, "moved": False, "duration_ms": 0}], "desk")
    check("сверка: uniform на canvas → N/A, не PASS («Звено»)", sr2[0]["verdict"], "N/A")
    sr3 = spec_rows([{"id": "line", "sel": ".l", "tag": "DIV", "class": "scroll-linked", "trigger": "scroll-scrub", "spec_ms": None,
                      "spec_props": ["transform"], "sampled": True, "moved": False, "duration_ms": 0}], "desk")
    check("сверка: скраб не замечен при прокрутке → N/A", sr3[0]["verdict"], "N/A")
    dr = derive({"net": {"effects_js": ["motion.js 1.1", "gsap.min.js 27.3", "fx-toggle.js 4.2"]}, "page_end": {"toggle_scripts": ["fx-toggle.js"]}}, "rm")
    check("EG-A11Y-11: 1,1 КБ и script[data-motion-toggle] — исключения, GSAP — нет («Звено»)",
          (dr["derived"]["effects_libs_loaded"], len(dr["derived"]["effects_libs_exempt"])), (["gsap.min.js 27.3"], 2))
    tt_ok = {"control": True, "option": "Меньше", "before": {"pct_1s": 3.94}, "after": {"pct_1s": 0.0, "webgl_calls": 0, "infinite": 0, "videos_playing": 0}}
    check("переключатель: 3,94 → 0 %/с, 0 WebGL → работает (эталон F2/12)", derive({"toggle_test": tt_ok}, "desk")["derived"]["toggle_works"], True)
    check("переключатель: после «Меньше» WebGL рисует → не работает",
          derive({"toggle_test": {**tt_ok, "after": {**tt_ok["after"], "webgl_calls": 58}}}, "desk")["derived"]["toggle_works"], False)
    check("переключатель в reduce: «Полное» → движение есть (F2/12 ?start=full 3,6 %/с)",
          derive({"toggle_test": {"control": True, "option": "Полное", "before": {"pct_1s": 0.0}, "after": {"pct_1s": 3.6, "webgl_calls": 60}}}, "rm")["derived"]["toggle_full_in_reduce"], True)
    check("переключателя нет → N/A", derive({"toggle_test": {"control": False}}, "desk")["derived"]["toggle_works"], None)
    cb = cls_block([{"t": 100, "v": 0.05, "ph": "load", "mv": [{"n": "div.hero", "f": [0, 0, 10, 10], "c": [0, 50, 10, 10]}]},
                    {"t": 600, "v": 0.04, "ph": "load", "src": ["p.lead"]}, {"t": 9000, "v": 0.2, "ph": "scroll", "mv": [{"n": "section.pin"}]}])
    check("CLS: окна 0,09 и 0,2 → наибольшее 0,2; сумма 0,29; первый источник section.pin",
          (cb["window_max"], cb["total"], cb["top_sources"][0].split(" ")[0]), (0.2, 0.29, "section.pin"))
    # контраст над живым фоном на синтетике: белый текст над тёмным фоном с ярким пятном в одном кадре → худший кадр
    L_dark = np.full((100, 200), 0.02)
    L_blob = L_dark.copy()
    L_blob[40:60, 40:120] = 0.8
    item = {"sel": "h1", "found": True, "rgba": [255, 255, 255, 255], "box": [30, 30, 100, 40], "large": False}
    ce = contrast_eval([L_dark, L_blob], [item], 1.0)
    check("контраст над живым фоном: тёмный кадр ≈ 15:1, кадр с пятном 0,8 → худший < 4,5 → FAIL", (ce[0]["ratio_min"] < 4.5, ce[0]["frames"]), (True, 2))
    ce2 = contrast_eval([L_dark], [{**item, "rgba": [255, 255, 255, 255]}], 1.0)
    check("контраст над тёмным фоном 0,02: белый текст (1 + 0,05) / (0,02 + 0,05) = 15:1", round(ce2[0]["ratio_min"], 1), 15.0)
    dcl = derive({"contrast_live": ce}, "desk")["derived"]
    check("EG-A11Y-27: список провалов контраста не пуст", bool(dcl["contrast_live_fail"]), True)
    check("контраст не мерили → N/A", derive({}, "desk")["derived"]["contrast_live_fail"], None)
    rs = {"desk": {"derived": {}, "page_first": {"cta": 1, "h1": {"op": 1}}},
          "_f83": {"contrast": [{"selector": ".hero__title", "f83_min": 1.44, "need": 3.0, "pass_f83": False},
                                {"selector": ".hero__lede", "f83_min": 7.2, "need": 4.5, "pass_f83": True}]}}
    cross_derive(rs)
    check("F83 (page_accept, ключ no_preference): провал H1 → EG-A11Y-26", rs["desk"]["derived"]["f83_fail"], [".hero__title 1.44:1 < 3.0"])
    tmp2 = tempfile.mkdtemp(prefix="mc_sniff_")
    try:
        open(os.path.join(tmp2, "scene.js"), "w").write('/* bundle */ window.__THREE__ = "183"; class WebGLRenderer {}')
        open(os.path.join(tmp2, "loader.js"), "w").write("LAB.load(['../_vendor/lenis-1.3.26/lenis.min.js']); // gsap ScrollTrigger")
        n2 = Net("http://127.0.0.1:1", tmp2)
        n2.req = {"a": {"url": "http://127.0.0.1:1/scene.js", "type": "Script", "mime": "text/javascript", "by": {"first": 60}, "chunks": 60},
                  "b": {"url": "http://127.0.0.1:1/loader.js", "type": "Script", "mime": "text/javascript", "by": {"first": 80}, "chunks": 80}}
        s2 = n2.summary()
        check("JS по содержимому: scene.js с __THREE__ → 3D; загрузчик с путём «lenis» — не библиотека («Звено»)",
              (s2["js_3d_session_kb"] > 0, any("loader.js" in x for x in s2["effects_js"]), s2["sniffed"][:1]), (True, False, ["scene.js: 3d"]))
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)
    # вспышки: синтетическое видео 25 к/с, 2 с мигания 10 Гц на весь кадр → провал; 1 Гц → норма
    if kbpaths.find("ffmpeg"):
        tmp = tempfile.mkdtemp(prefix="mc_selftest_")
        try:
            for hz, want in ((10, True), (1, False)):
                path = os.path.join(tmp, f"f{hz}.webm")
                expr = f"if(lt(mod(T*{hz}*2,2),1),255,20)"
                subprocess.run([kbpaths.ffmpeg(), "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x200:r=25:d=3",
                                "-vf", f"geq=lum='{expr}':cb=128:cr=128", "-c:v", "libvpx", "-b:v", "1M", "-threads", "2", path], check=True, timeout=120)
                fr = flash_scan(path, {"page_first": {"innerW": 1440}, "t_flash": -10}, 0.0)
                check(f"вспышки {hz} Гц на весь кадр → fail={want}", fr.get("fail"), want)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    net = Net()
    net.req = {"1": {"url": "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js", "type": "Script", "mime": "text/javascript", "by": {"first": 26000}, "chunks": 26000},
               "2": {"url": "https://x.test/v.mp4", "type": "Media", "mime": "video/mp4", "by": {"first": 500000, "session": 300000}, "chunks": 800000}}
    sm = net.summary()
    check("сеть: CDN найден, js эффектов 25,4 КБ, видео первого экрана 488,3 КБ", (len(sm["cdn"]), sm["js_effects_first_kb"], sm["video_first_kb"]), (1, 25.4, 488.3))
    # ссылки порогов: уровень, профиль site, каталог эффектов; поле без числа — N/A
    import copy
    import yaml as _y
    gdoc = _y.safe_load(open(GATES_DEFAULT, encoding="utf-8"))
    use_gate_limits(gdoc)
    G = {g["id"]: g for g in gdoc["gates"]}
    check("EG-PERF-06 → профиль site: LCP L1 телефон 2 500, L0 десктоп 2 000",
          (threshold_for(G["EG-PERF-06"], "L1", "mobile", levels), threshold_for(G["EG-PERF-06"], "L0", "desktop", levels)), (2500, 2000))
    check("EG-WEIGHT-08 → профиль landing-lead-services@L1 телефон 1 500 (исключение)",
          threshold_for(G["EG-WEIGHT-08"], "L1", "mobile", levels, "landing-lead-services"), 1500)
    check("EG-A11Y-19 → effects.yaml marquee-logos 60 px/с", threshold_for(G["EG-A11Y-19"], "L1", "desktop", levels), 60)
    check("EG-A11Y-17 → motion_hints L1: десктоп 2, телефон 1",
          (threshold_for(G["EG-A11Y-17"], "L1", "desktop", levels), threshold_for(G["EG-A11Y-17"], "L1", "mobile", levels)), (2, 1))
    check("EG-WEIGHT-04 → budgets.effects.video_first_screen_kb L2 десктоп 2 500", threshold_for(G["EG-WEIGHT-04"], "L2", "desktop", levels), 2500)
    check("EG-WEIGHT-02 → JS и wasm 3D: budgets.effects.js_3d_kb_br L1 телефон 200, десктоп 300; 320 КБ на десктопе → FAIL",
          (threshold_for(G["EG-WEIGHT-02"], "L1", "mobile", levels), threshold_for(G["EG-WEIGHT-02"], "L1", "desktop", levels),
           evaluate_gates({"gates": [G["EG-WEIGHT-02"]]}, {"desk": {"net": {"js_3d_session_kb": 320.0}}}, "L1", levels)[0]["verdict"]),
          (200, 300, "FAIL"))
    check("EG-WEIGHT-11 → wasm-рантаймы подачи: поле есть, числа нет → N/A",
          (resolve_ref(G["EG-WEIGHT-11"]["threshold_ref"], "L1", "mobile", levels), evaluate_gates({"gates": [G["EG-WEIGHT-11"]]},
           {"desk": {"net": {"wasm_presentation_kb": 400.0}}}, "L1", levels)[0]["verdict"]), ((True, None), "N/A"))
    n3 = Net()
    n3.req = {"1": {"url": "https://x.test/draco_decoder.wasm", "type": "Other", "mime": "application/wasm", "by": {"first": 2048}, "chunks": 2048},
              "2": {"url": "https://x.test/rive.wasm", "type": "Other", "mime": "application/wasm", "by": {"session": 4096}, "chunks": 4096}}
    s3 = n3.summary()
    check("wasm: декодер 3D (draco) — в метрику EG-WEIGHT-02, рантайм подачи (rive.wasm) — в метрику EG-WEIGHT-11",
          (s3["js_3d_session_kb"], s3["wasm_presentation_kb"]), (2.0, 4.0))
    g11 = copy.deepcopy(gdoc)
    next(x for x in g11["gates"] if x["id"] == "EG-A11Y-11")["limits"]["exempt_js_kb_br_max"] = 1
    use_gate_limits(g11)
    try:
        dr1 = derive({"net": {"effects_js": ["motion.js 1.1", "gsap.min.js 27.3"]}}, "rm")["derived"]["effects_libs_loaded"]
    finally:
        use_gate_limits(gdoc)
    check("EG-A11Y-11: предел маленького JS — limits строки (1 КБ в копии → motion.js 1,1 КБ — библиотека)",
          dr1, ["motion.js 1.1", "gsap.min.js 27.3"])
    check("подписи механизма паузы — page_gates.PAUSE_LABELS: выражение подставлено в PAGE_JS",
          (PG.pause_label_re_js() in PAGE_JS, "__PAUSE_RE__" in PAGE_JS), (True, False))
    # NU-31: атрибут data-motion — только reduced | full | paused
    tt_ok2 = {"control": True, "option": "Меньше", "before": {"pct_1s": 3.9}, "after": {"pct_1s": 0.0, "webgl_calls": 0, "infinite": 0, "videos_playing": 0}}
    check("переключатель: data-motion=reduced → работает; data-motion=reduce → вне контракта",
          (derive({"toggle_test": {**tt_ok2, "after": {**tt_ok2["after"], "motion_attr": "reduced"}}}, "desk")["derived"]["toggle_works"],
           derive({"toggle_test": {**tt_ok2, "after": {**tt_ok2["after"], "motion_attr": "reduce"}}}, "desk")["derived"]["toggle_works"]), (True, False))
    # EG-A11Y-18: полоса и минимум периода — поля строки
    snap = lambda w, h, dur, dr="alternate": {"loops": 1, "loopsAll": [{"k": "anim", "vis": True, "sel": f"div.o{w}-{dur}", "w": w, "h": h, "dur": dur,  # noqa: E731
                                                                         "dir": dr, "props": ["transform"]}]}
    osc = loop_metrics([snap(500, 500, 4000), snap(120, 120, 2000), snap(500, 500, 6000), snap(120, 120, 4000, "normal")], [], 900, 1440)["oscillation"]
    check("колебания (поля EG-A11Y-18): крупный 8 с, мелкий 4 с и мелкий 4 с без alternate — находки, крупный 12 с — нет",
          (any("div.o500-4000" in x for x in osc), any("div.o120-2000" in x for x in osc), any("div.o500-6000" in x for x in osc),
           any("div.o120-4000" in x for x in osc)), (True, True, False, True))
    # EG-A11Y-28: заставка дольше 3 с и без «Пропустить»
    di = derive({"intro": {"sel": "div.loader", "t_first": 120, "t_last": 4300, "skip": False, "skip_t": None}}, "desk")["derived"]
    check("прелоадер 4,2 с без «Пропустить» → две находки", len(di["intro_fail"]), 2)
    di = derive({"intro": {"sel": "div.loader", "t_first": 120, "t_last": 2100, "skip": True, "skip_t": 400}}, "desk")["derived"]
    check("прелоадер 2 с, «Пропустить» с 0,3 с → чисто", di["intro_fail"], [])
    # слой подачи по режимам: порог один — EG-WEIGHT-01 уровня
    pres = presentation_layer({"desk": {"net": {"first_only": {"js_effects_first_kb": 120.0, "video_first_kb": 0.0}, "js_3d_session_kb": 0.0}},
                               "mob": {"net": {"first_only": {"js_effects_first_kb": 40.0}}}, "rm": {"net": {"first_only": {"js_effects_first_kb": 3.0}}}},
                              "L1", levels, gdoc)
    check("слой подачи: десктоп 120 > 100 (L1), телефон 40 ≤ 100, reduce — порог десктопа; бюджет картинки героя — ссылкой",
          (pres["modes"]["desk"]["over"], pres["modes"]["mob"]["over"], pres["modes"]["rm"]["threshold_js_effects_kb"],
           (pres.get("hero_image") or {}).get("hero_mobile_kb")), (True, False, 100, 80))
    check("окно первого экрана по умолчанию — budgets.yaml (5 000 мс)", PG.window_ms(), 5000)
    gpath = GATES_DEFAULT
    if os.path.exists(gpath):
        g = yaml.safe_load(open(gpath, encoding="utf-8"))
        ids = [x["id"] for x in g.get("gates", [])]
        check("effect-gates.yaml: id уникальны", len(ids) == len(set(ids)), True)
        bad = [x["id"] for x in g.get("gates", []) if x.get("auto") is not False and not x.get("metric")]
        check("effect-gates.yaml: у автоматических есть metric", bad, [])
        for lv in ("L0", "L1", "L2"):
            miss = [x["id"] for x in g["gates"] if x.get("threshold_ref") and (not x.get("levels") or lv in x["levels"])
                    and not all(resolve_ref(x["threshold_ref"], lv, dv, levels)[0] for dv in ("desktop", "mobile"))]
            check(f"effect-gates.yaml: threshold_ref разрешается для {lv} (поле есть у владельца)", miss, [])
    print(f"\n{VERSION}")
    return 0 if ok else 1


# =====================================================================================================================
# 9. CLI
# =====================================================================================================================
def run(a):
    os.makedirs(a.out, exist_ok=True)
    import yaml
    gates_doc = yaml.safe_load(open(a.gates, encoding="utf-8")) if os.path.exists(a.gates) else {"gates": []}
    gates_doc["_path"] = a.gates
    use_gate_limits(gates_doc)
    levels, _ = load_levels()
    spec = load_spec(a.spec)
    a.spec_doc = spec
    spec_ms = spec_moments(spec) if spec else None
    target = a.target
    srv, local_base, local_root, url = None, None, None, target
    served = Served()
    if not re.match(r"^https?://", target):
        p = os.path.abspath(target)
        if os.path.isdir(p):
            p = os.path.join(p, "index.html")
        if not os.path.isfile(p):
            raise SystemExit(f"нет файла {p}")
        local_root = local_root_for(p, a.root)
        srv = make_server(local_root, served)
        local_base = f"http://127.0.0.1:{srv.server_address[1]}"
        url = f"{local_base}/{os.path.relpath(p, local_root)}"
    results = {"_meta": {"tool": VERSION, "target": target, "url": url, "level": a.level, "date": time.strftime("%Y-%m-%d %H:%M"),
                         "load_avg": os.getloadavg()[0], "modes": a.modes, "page_type": a.page_type, "window_after_load_ms": a.wait}}
    tmp = tempfile.mkdtemp(prefix="motion_check_")
    from playwright.sync_api import sync_playwright
    try:
        for mode in a.modes:
            t0 = time.time()
            log(f"[{mode}] {url}")
            try:
                with Locks(not a.no_lock):
                    with sync_playwright() as pw:
                        r = run_mode(pw, mode, url, a, (local_base, local_root), tmp, spec_ms)
            except Exception as e:
                r = {"mode": mode, "error": str(e)[:300]}
                log(f"  ошибка режима {mode}: {e}")
            r["seconds_browser"] = round(time.time() - t0, 1)
            if r.get("video_tmp"):
                try:
                    r["video"] = analyze_video(r, a.out, mode, a.keep_video)
                except Exception as e:
                    r["video"] = {"error": str(e)[:200]}
            r.pop("video_tmp", None)
            results[mode] = derive(r, mode)
            log(f"  [{mode}] {r['seconds_browser']} с браузера")
        if a.f83:
            # page_accept получает адрес нашего сервера (корень раздачи — по ссылкам ../ или --root), а не файл: так стили
            # из соседних папок (../_shared/…) находятся
            results["_f83"] = f83_run(url, a)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if srv:
            srv.shutdown()
    cross_derive(results)
    json.dump(results, open(os.path.join(a.out, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    return finish(results, a, gates_doc, levels, spec)


def derive(r, mode):
    """Производные метрики для ворот (плоские имена)."""
    if r.get("error"):
        return r
    v = r.get("video") or {}
    d = r.setdefault("derived", {})
    pf = r.get("page_first") or {}
    pe = r.get("page_end") or {}
    d["hidden_below_before_scroll"] = pf.get("hiddenBelow")
    d["hidden_after_scroll"] = pe.get("hiddenAll")
    d["text_hidden_share_nojs"] = round((pf.get("hiddenAll") or 0) / max(1, pf.get("textAll") or 1), 3) if mode == "nojs" else None
    if mode in ("nojs", "nogl"):
        pg = r.get("page") or {}
        d["h1_visible"] = bool(pg.get("h1") and (pg["h1"].get("op") or 0) >= 0.9)
        d["cta_visible"] = (pg.get("cta") or 0) > 0
        d["text_hidden_share"] = round((pg.get("hiddenAll") or 0) / max(1, pg.get("textAll") or 1), 3)
        d["blank"] = (r.get("blank_std") or 0) < 2.0
        d["hero_blank"] = (r.get("hero_std") or 0) < 2.0
        return r
    loops6 = r.get("loops_6s") or []
    pt = r.get("pause_test") or {}
    d["loops_moving_after_6s"] = [x["sel"] for x in loops6 if x.get("moving")]
    has_ctrl = bool((r.get("page_end") or {}).get("pause")) or bool((r.get("page_end") or {}).get("toggle"))
    d["loops_without_pause"] = d["loops_moving_after_6s"] if not has_ctrl else []
    d["pause_control"] = has_ctrl
    moving_min = LIM("EG-A11Y-01", "moving_pct_min")          # «движется»: доля пикселей за 1 с (строка ворот 2.2.2)
    d["pause_works"] = None if not pt.get("control") else ((pt.get("infinite_after") or 0) == 0 and (pt.get("videos_playing_after") or 0) == 0 and (pt.get("pct_after") or 0) < moving_min)
    idle = r.get("idle_6s") or {}
    snapf = r.get("snap_first") or {}
    moving6 = (idle.get("pct") or 0) >= moving_min or any(l.get("k") == "video" and l.get("vis") for l in (snapf.get("loopsAll") or []))
    d["moving_6s_without_pause"] = bool(moving6 and not has_ctrl)
    d["idle_first_pct_1s"] = idle.get("pct")
    d["continuous_windows"] = v.get("continuous_windows")
    d["loud_windows"] = v.get("loud_windows")
    d["flash_fail"] = (v.get("flash") or {}).get("fail")
    d["flash_area_frac"] = (v.get("flash") or {}).get("max_area_frac_general")
    d["webgl_contexts"] = (r.get("gl") or {}).get("ctx") or 0
    d["webgl_idle_calls"] = sum(1 for s in (r.get("snaps") or []) for x in (s.get("loopList") or []) if x.startswith("webgl"))
    snaps0 = (r.get("snap_first") or {}).get("loopsAll") or []
    d["infinite_running"] = len([x for x in snaps0 if x.get("k") == "anim"])
    kb = r.get("keyboard") or {}
    d["focus_off_screen"] = kb.get("off_screen")
    d["focus_invisible"] = kb.get("invisible")
    d["focus_no_ring"] = kb.get("no_ring_guess")
    net = r.get("net") or {}
    # переключатель и загрузчик обязаны грузиться и в reduce — JS не больше limits.exempt_js_kb_br_max строки
    # EG-A11Y-11 и script[data-motion-toggle] не «библиотека эффектов»; список исключённых — effects_libs_exempt
    tscripts = set((pe.get("toggle_scripts") or []) + (pf.get("toggle_scripts") or []))
    small_kb = float(LIM("EG-A11Y-11", "exempt_js_kb_br_max"))
    libs, exempt = [], []
    for x in net.get("effects_js") or []:
        nm, _, kb = str(x).rpartition(" ")
        try:
            kbv = float(kb)
        except ValueError:
            nm, kbv = str(x), None
        (exempt if ((kbv is not None and kbv <= small_kb) or nm in tscripts) else libs).append(x)
    d["effects_libs_loaded"] = libs
    d["effects_libs_exempt"] = exempt
    # тест переключателя (desk — «Меньше» стоит; rm — «Полное» движется)
    tt = r.get("toggle_test") or {}
    aft, bef = tt.get("after") or {}, tt.get("before") or {}
    key = "toggle_full_in_reduce" if mode == "rm" else "toggle_works"
    if tt.get("control") and aft:
        still = LIM("EG-A11Y-06", "threshold")                  # «стоит»: не больше порога reduce первого экрана
        moving_after = ((aft.get("pct_1s") or 0) > still or (aft.get("webgl_calls") or 0) > 0 or (aft.get("infinite") or 0) > 0
                        or (aft.get("videos_playing") or 0) > 0)
        attr = aft.get("motion_attr")
        attr_ok = attr is None or attr in MOTION_VALUES          # атрибут на корне — только reduced | full | paused
        d[key] = (bool(moving_after) if mode == "rm" else (not moving_after)) and attr_ok
        d["toggle_summary"] = (f"«{tt.get('option')}»: до {bef.get('pct_1s')} %/с → после {aft.get('pct_1s')} %/с; WebGL {aft.get('webgl_calls')}; "
                               f"бесконечных {aft.get('infinite')}; видео {aft.get('videos_playing')}; data-motion={attr}"
                               + ("" if attr_ok else f" — вне контракта ({' | '.join(MOTION_VALUES)})"))
    else:
        d[key] = None
        d["toggle_summary"] = None
    # сводка станций: tip_offset_px — край цели со scale-треком (линия)
    # или первой геометрической цели от линии окна; filled / filled_expected — «изменено» / «прошли линию» у цели-состояния
    sts = []
    for s in r.get("stations") or []:
        if not s.get("found"):
            continue
        tg = [t for t in (s.get("targets") or []) if t.get("found") and not t.get("hidden")]
        geo = [t for t in tg if t.get("kind", "geometry") == "geometry" and (t.get("edge_offset") is not None or t.get("edge_bottom_offset") is not None)]
        tip = next((t for t in geo if t.get("scale_y") is not None), geo[0] if geo else None)
        stt = next((t for t in tg if t.get("mismatch") is not None), None)
        tv = None if tip is None else (tip["edge_offset"] if tip.get("edge_offset") is not None else tip["edge_bottom_offset"])
        sts.append({"section": s.get("section"), "station": s.get("station"), "tip_offset_px": None if tv is None else round_half_away(tv),
                    "tip_moment": tip.get("moment") if tip else None, "filled": stt.get("changed") if stt else None,
                    "filled_expected": (stt.get("n_visible") if mode == "rm" else stt.get("passed")) if stt else None})
    d["stations"] = sts
    # контраст над живым фоном (EG-A11Y-27): None — не мерили или ошибка; [] — все выше порога
    cl = r.get("contrast_live")
    if isinstance(cl, list) and cl and not any(x.get("error") for x in cl):
        d["contrast_live_fail"] = [f"{x['sel']} {x['ratio_min']}:1 < {x['threshold']}" for x in cl
                                   if x.get("found") and x.get("ratio_min") is not None and x["ratio_min"] < x["threshold"]]
        d["contrast_live_min"] = "; ".join(f"{x['sel']} {x.get('ratio_min')}:1" for x in cl if x.get("found"))
    else:
        d["contrast_live_fail"] = None
        d["contrast_live_min"] = None
    jr_min, jr_max = LIM("EG-A11Y-21", "ratio_min"), LIM("EG-A11Y-21", "ratio_max")
    d["scroll_jacking"] = bool((r.get("scroll") or {}).get("dist_ratio_min") is not None and ((r["scroll"]["dist_ratio_min"] < jr_min) or (r["scroll"].get("dist_ratio_max") or 1) > jr_max))
    # прелоадер или входной экран (EG-A11Y-28): дольше intro_max_ms или без видимой «Пропустить» к skip_visible_by_ms
    it = r.get("intro")
    if isinstance(it, dict) and it.get("t_first") is not None:
        dur, fails = (it.get("t_last") or it["t_first"]) - it["t_first"], []
        if dur > LIM("EG-A11Y-28", "intro_max_ms"):
            fails.append(f"{it.get('sel')}: заставка {dur} мс > {LIM('EG-A11Y-28', 'intro_max_ms')}")
        if not it.get("skip") or (it.get("skip_t") or 0) - it["t_first"] > LIM("EG-A11Y-28", "skip_visible_by_ms"):
            fails.append(f"{it.get('sel')}: нет видимой «Пропустить» в первые {LIM('EG-A11Y-28', 'skip_visible_by_ms')} мс")
        d["intro_fail"], d["intro_ms"] = fails, dur
    else:
        d["intro_fail"], d["intro_ms"] = [], None
    d["h_overflow_px"] = max(0, (pe.get("scrollW") or 0) - (pe.get("innerW") or 0))
    d["toggle"] = bool(pe.get("toggle"))
    d["heavy_3d_first_kb"] = (net.get("first_only") or {}).get("js_3d_first_kb")
    return r


def cross_derive(results):
    """Сравнение режимов: без JS / без WebGL пропало то, что было в desk (призыв, H1)."""
    base = results.get("desk") or {}
    pf = base.get("page_first") or {}
    for m in ("nojs", "nogl"):
        r = results.get(m)
        if not isinstance(r, dict) or r.get("error"):
            continue
        pg = r.get("page") or {}
        d = r.setdefault("derived", {})
        d["cta_lost"] = bool((pf.get("cta") or 0) > 0 and (pg.get("cta") or 0) == 0) if pf else None
        d["h1_lost"] = bool(pf.get("h1") and (pf["h1"].get("op") or 0) >= 0.9 and not d.get("h1_visible")) if pf else None
    # F83 по буквам (page_accept.py, --f83) → ворота EG-A11Y-26 в режиме desk; None — не запускали или нет данных
    f83 = results.get("_f83") or {}
    if isinstance(base, dict) and not base.get("error") and base:
        dd = base.setdefault("derived", {})
        c = f83.get("contrast") if isinstance(f83, dict) else None
        dd["f83_fail"] = None if not isinstance(c, list) or not c else [
            f"{x.get('selector')} {x.get('f83_min')}:1 < {x.get('need')}" for x in c if x.get("pass_f83") is False]
        dd["f83_min"] = None if not isinstance(c, list) else "; ".join(f"{x.get('selector')} {x.get('f83_min')}:1" for x in c)


def f83_run(target, a):
    """Контраст на медиа по F83 — делегируется page_accept.py (ai-media): только первый экран, без reduce; замки тишины он
    берёт сам (удержанные обёрткой — нет)."""
    out = os.path.join(a.out, "f83")
    cmd = [sys.executable, str(kbpaths.scripts("ai-media", "page_accept.py")), target, "--out", out, "--no-rm", "--first-screen-only",
           "--contrast", *a.f83]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
        js = sorted(f for f in os.listdir(out) if f.startswith("accept_") and f.endswith(".json")) if os.path.isdir(out) else []
        data = json.load(open(os.path.join(out, js[0]), encoding="utf-8")) if js else {}
        c = (data.get("no_preference") or {}).get("contrast") if isinstance(data, dict) else None
        return {"code": p.returncode, "contrast": c, "verdict": data.get("verdict") if isinstance(data, dict) else None, "stderr": p.stderr[-300:]}
    except Exception as e:
        return {"error": str(e)[:200]}


def finish(results, a, gates_doc, levels, spec):
    rows = evaluate_gates(gates_doc, {k: v for k, v in results.items() if not k.startswith("_")}, a.level, levels,
                          spec=(spec or {}).get("page") if spec else None, page_type=getattr(a, "page_type", None))
    pres = presentation_layer(results, a.level, levels, gates_doc)
    srows = []
    for mode in ("desk", "mob", "rm"):
        if isinstance(results.get(mode), dict) and results[mode].get("spec") and mode != "mob":
            srows += spec_rows(results[mode]["spec"], mode)
        if isinstance(results.get(mode), dict) and results[mode].get("stations"):
            srows += station_rows(results[mode]["stations"], mode)
    md = render(results["_meta"]["target"], a.level, results, rows, srows, gates_doc, pres)
    open(os.path.join(a.out, "gates.md"), "w", encoding="utf-8").write(md)
    open(os.path.join(a.out, "fix.txt"), "w", encoding="utf-8").write(fix_text(results["_meta"]["target"], rows, srows))
    stations = {m: (results[m].get("derived") or {}).get("stations") for m in ("desk", "mob", "rm")
                if isinstance(results.get(m), dict) and (results[m].get("derived") or {}).get("stations")}
    json.dump({"rows": rows, "spec": srows, "level": a.level, "page_type": getattr(a, "page_type", None), "gates_version": gates_doc.get("version"),
               "tool": VERSION, "stations": stations, "presentation": pres},
              open(os.path.join(a.out, "gates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    fails = [r for r in rows if r["verdict"] == "FAIL"]
    summ = {"target": results["_meta"]["target"], "level": a.level, "fail_B": len([r for r in fails if r["severity"] == "B"]),
            "fail_S": len([r for r in fails if r["severity"] == "S"]), "fail_D": len([r for r in fails if r["severity"] == "D"]),
            "na": len([r for r in rows if r["verdict"] == "N/A"]), "spec_fail": len([r for r in srows if r["verdict"] == "FAIL"]), "out": a.out}
    print(json.dumps(summ, ensure_ascii=False))
    worst_b = summ["fail_B"] > 0
    if a.fail_on == "serious":
        return 1 if (summ["fail_B"] or summ["fail_S"]) else 0
    return 1 if worst_b else 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        p = argparse.ArgumentParser(prog="motion_check.py report")
        p.add_argument("cmd")
        p.add_argument("--in", dest="inp", required=True)
        p.add_argument("--level")
        p.add_argument("--gates", default=GATES_DEFAULT)
        p.add_argument("--spec")
        p.add_argument("--fail-on", default="blocker", choices=["blocker", "serious"])
        a = p.parse_args()
        import yaml
        results = json.load(open(os.path.join(a.inp, "results.json"), encoding="utf-8"))
        a.level = a.level or results["_meta"]["level"]
        a.page_type = results["_meta"].get("page_type")
        a.out = a.inp
        a.spec_doc = None
        gd = yaml.safe_load(open(a.gates, encoding="utf-8"))
        gd["_path"] = a.gates
        use_gate_limits(gd)
        levels, _ = load_levels()
        for k, v in list(results.items()):
            if not k.startswith("_") and isinstance(v, dict):
                results[k] = derive(v, k)
        cross_derive(results)
        return finish(results, a, gd, levels, load_spec(a.spec))
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("target", nargs="?")
    p.add_argument("--level", default="L1", choices=["L0", "L1", "L2"])
    p.add_argument("--out")
    p.add_argument("--modes", default="desk,mob,rm,nojs,nogl")
    p.add_argument("--spec")
    p.add_argument("--gates", default=GATES_DEFAULT)
    p.add_argument("--steps", type=int, default=12)
    p.add_argument("--dwell", type=float, default=1.8)
    p.add_argument("--wait", type=int, help="окно первого экрана после load, мс (по умолчанию — budgets.yaml site)")
    p.add_argument("--timeout", type=int, default=90)
    p.add_argument("--budget", type=int, default=240, help="секунд на режим (≤ 300: партия под блокировкой)")
    p.add_argument("--locale", default="ru-RU")
    p.add_argument("--no-lock", action="store_true")
    p.add_argument("--keep-video", action="store_true")
    p.add_argument("--keep-shots", action="store_true")
    p.add_argument("--no-video", action="store_true")
    p.add_argument("--page-type", help="тип страницы: зеркала страницы (profile.*) — профиль <тип>@<уровень> с исключениями")
    p.add_argument("--root", help="корень раздачи локальной страницы (по умолчанию — по ссылкам ../ в HTML)")
    p.add_argument("--effects-js", default=EFFECT_JS_RE)
    p.add_argument("--f83", nargs="*")
    p.add_argument("--contrast", nargs="*", help="худший контраст текста над живым фоном (селекторы; без значений — h1)")
    p.add_argument("--fail-on", default="blocker", choices=["blocker", "serious"])
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--version", action="store_true")
    p.add_argument("-h", "--help", action="store_true")
    a = p.parse_args()
    if a.version:
        print(VERSION)
        return 0
    if a.help or (not a.target and not a.selftest):
        print(__doc__)
        return 0
    if a.selftest:
        return selftest()
    if a.contrast is not None and not a.contrast:
        a.contrast = ["h1"]
    a.modes = [m.strip() for m in a.modes.split(",") if m.strip()]
    bad = [m for m in a.modes if m not in DEVICE]
    if bad:
        raise SystemExit(f"неизвестные режимы: {bad}")
    a.budget = min(a.budget, 300)
    a.wait = a.wait if a.wait is not None else PG.window_ms()
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", re.sub(r"^https?://", "", a.target).strip("/"))[:60] or "page"
    a.out = os.path.abspath(a.out or os.path.join(str(kbpaths.out("creative", "motion")), slug))
    try:
        return run(a)
    except SystemExit:
        raise
    except Exception as e:
        log(f"ошибка: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
