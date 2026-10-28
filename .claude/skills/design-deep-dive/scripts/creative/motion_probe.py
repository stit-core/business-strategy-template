#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motion_probe.py — замер движения референса: длительности, кривые, задержки, стаггер, скраб, закрепления и станции
понравившегося сайта (Awwwards, Codrops и т. п.) → паспорт движения (passport.json по схеме, passport.md по-русски).

Числа движения на этапах арт-дирекции и движения берутся с измеренных референсов, а не на глаз: строки паспорта идут в
запись референса (values.measured), моменты motion-spec ссылаются на моменты паспорта (source.ref, source.moment), а
прототип сверяют с референсом и со спецификацией тем же замером (compare). Описание —
kb/creative/03-live-sites-measured/03-reference-motion-probe.md; схема паспорта —
kb/creative/09-ai-execution-evaluation/motion-passport.schema.json.

Что снимается (Playwright, Chromium, CDP):
  1. CDP Animation: CSS-анимации, переходы, WAAPI, в том числе на шкалах прокрутки (viewOrScrollTimeline — диапазон
     шкалы в px); цель — DOM.describeNode и DOM.resolveNode; ключевые кадры, тайминг и диапазон view() —
     Animation.resolveAnimation → effect.getKeyframes(), getTiming(), rangeStart/rangeEnd.
  2. Библиотеки: GSAP (версия; твины gsap.globalTimeline.getChildren — опрос каждые 4 кадра: доигравшие твины корень
     удаляет; ScrollTrigger.getAll — триггер, start/end в px, scrub, pin, snap), Lenis (экземпляр среди глобалов, класс
     lenis на <html>, опции), ScrollSmoother, Locomotive, anime.js, Motion и другие — по глобалам и сниффером по
     содержимому файлов (сигнатуры из кода самих библиотек); CSS scroll-driven, @view-transition, scroll-snap — в
     таблицах стилей.
  3. Движение скриптом через инлайн-стили (так двигает GSAP без глобала, Motion, свой rAF): MutationObserver на атрибут
     style и выборка в requestAnimationFrame (takeRecords) — вычисленные opacity, transform, clip-path, filter,
     translate/scale/rotate и CSS-переменные элемента; траектории → моменты (старт, конец, от → до, длительность,
     задержка), стаггер соседей, кривая: прогресс → ближайшая именованная (linear, ease, power1–4, expo, sine, circ,
     back — in/out/inOut) и лучший cubic-bezier методом наименьших квадратов (numpy) с ошибкой подбора.
  4. Прокрутка колесом шагами --scroll-step доли окна и пауза --settle-ms после успокоения: значение против прокрутки →
     диапазон, линейность скраба (R²), догон сглаживания; хвост плавной прокрутки и оценка lerp; закрепления — элементы,
     чей верх в окне стоит ≥ 2 шагов, пока документ едет (начало, конец, длина в vh, механизм); станции — точки snap и
     плато прогресса скраба.
  5. --clock: шаг времени через Playwright page.clock (поддельные Date, таймеры, rAF, performance.now) — анимации
     скриптом идут кадрами ровно по 16 мс и снимаются без дрожи; CSS-анимации, переходы, WAAPI, видео и воркеры часам не
     подчиняются (их числа — объявленные, из CDP).

Использование:
  motion_probe.py probe ЦЕЛЬ [--out DIR] [--viewport 1440x900] [--mobile] [--scroll-step 0.33] [--settle-ms 1200]
                  [--max-s 60] [--frames] [--clock] [--no-lock] [--json]
  motion_probe.py compare A B [--json] [--out DIR]   # паспорт против паспорта или против motion-spec (YAML/JSON)
  motion_probe.py --selftest [--no-browser]           # тестовые страницы без сети и чистые тесты
ЦЕЛЬ — адрес или локальный HTML (раздаётся встроенным сервером motion_check.py; корень — по ссылкам ../ или --root).
Выход DIR (по умолчанию $DDD_HOME/out/creative/motion-probe/<хост>-<хеш адреса>/, с --mobile —
<хост>-mobile-<хеш>/): passport.json, passport.md; с
--frames — frames_NN.jpg (контактный лист кадров станций и закреплений; только в выходе, не в git).
Коды выхода probe: 0 — паспорт снят; 3 — закрыто защитой, входом или robots.txt (паспорт со статусом, сайт смотрит
человек); 2 — сбой замера. compare: 0 — далёких расхождений нет; 1 — есть «далеко» или моменты без пары; 2 — ошибка входа.

Правила (kb/creative/02-references-moodboards/02-refs-client-and-library.md §8): автоматизация не маскируется — UA как
есть (HeadlessChrome), без AutomationControlled, stealth и подмен; вход, капча, антибот (Cloudflare «Just a moment»,
hCaptcha, reCAPTCHA, ответы 401/403/429) — отсев со статусом, без ожидания и без повтора; robots.txt — по RFC 9309
(разбор refs_client.py); согласие cookie не нажимается; одна страница за запуск; браузер — под замком
kbpaths.lock('browser') и при свободной памяти. Числа и кадры — только в выходе; картинки площадок не выкачиваются.
Пределы: WebGL и canvas внутри, видео, Lottie, SVG SMIL не видны (паспорт считает их в unseen); анимации без глобала и
без инлайн-стилей (смена класса без перехода, правка таблицы стилей) не видны; движение через CSS-переменную видно
дорожкой переменной у того элемента, где она меняется; наведение и клики не выполняются; кривая скраба — по точкам
шагов (точнее — меньший --scroll-step); headless: rAF ≤ 60 кадров/с, телефон — эмуляция без замедления CPU.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import unquote, urlparse

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lib"))  # scripts/lib
import kbpaths  # noqa: E402
import motion_check as MC  # noqa: E402  сервер локальных файлов, сеть по CDP, сигнатуры, память, аргументы GPU
import scroll_record as SR  # noqa: E402  контактные листы
PG = MC.PG                    # дескриптор телефона, условия лаборатории

VERSION = "motion_probe.py 0.1"
PASSPORT_VERSION = "1.0"
SCHEMA = str(kbpaths.kb("creative", "09-ai-execution-evaluation", "motion-passport.schema.json"))
TOKENS = str(kbpaths.kb("creative", "04-visual-language", "marketing-tokens.json"))
FIXTURES = os.path.join(HERE, "tests", "fixtures", "motion-probe")
EXIT_CLOSED = 3
GAP_MS = 150                  # пауза без изменений, после которой начинается новый отрезок движения элемента
LOOP_MS = 3000                # непрерывное движение дольше — петля (если есть развороты или сбросы)
WHEEL_WINDOW = (-30, 700)     # отрезок «вызван шагом прокрутки», мс от шага колеса
STATUS_WORDS = {"ok": "снято", "static": "движения не найдено", "partial": "снято частично",
                "blocked": "закрыто защитой — не снимаем, сайт смотрит человек",
                "login": "закрыто входом — не снимаем, сайт смотрит человек",
                "robots": "robots.txt не разрешает — не снимаем, сайт смотрит человек", "error": "сбой замера"}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def _rc():
    """refs_client — разбор robots.txt (RFC 9309) и признаки капчи и страницы блокировки; импорт по месту: модуль
    при импорте заводит папку кэша клиента."""
    import refs_client
    return refs_client


# =====================================================================================================================
# 1. Кривые: именованные (формулы GSAP 3.15 и ключевые слова CSS), cubic-bezier, подбор
# =====================================================================================================================
def _pow_in(n):
    return lambda u: u ** n


def _out_of(fin):
    return lambda u: 1.0 - fin(1.0 - u)


def _inout_of(fin):
    return lambda u: np.where(u < 0.5, fin(u * 2.0) / 2.0, 1.0 - fin((1.0 - u) * 2.0) / 2.0)


def _inout_from_out(fout):
    return lambda u: np.where(u < 0.5, (1.0 - fout(1.0 - u * 2.0)) / 2.0, 0.5 + fout((u - 0.5) * 2.0) / 2.0)


def _expo_in(u):
    return 2.0 ** (10.0 * (u - 1.0)) * u + u ** 6 * (1.0 - u)


def _circ_in(u):
    return -(np.sqrt(np.clip(1.0 - u * u, 0.0, 1.0)) - 1.0)


def _sine_in(u):
    return np.where(u >= 1.0, 1.0, 1.0 - np.cos(u * np.pi / 2.0))


def _back_out(s=1.70158):
    def f(u):
        q = u - 1.0
        return np.where(u > 0, q * q * ((s + 1.0) * q + s) + 1.0, 0.0)
    return f


def bezier_y(u, x1, y1, x2, y2):
    """cubic-bezier(x1, y1, x2, y2) в точках u ∈ [0, 1]: параметр s из x(s) = u (Ньютон, где он не сошёлся — деление
    пополам), затем y(s)."""
    u = np.minimum(np.maximum(np.asarray(u, dtype=float), 0.0), 1.0)
    cx = 3.0 * x1
    bx = 3.0 * (x2 - x1) - cx
    ax = 1.0 - cx - bx
    cy = 3.0 * y1
    by = 3.0 * (y2 - y1) - cy
    ay = 1.0 - cy - by
    s = u.copy()
    for _ in range(6):
        xs = ((ax * s + bx) * s + cx) * s - u
        d = (3.0 * ax * s + 2.0 * bx) * s + cx
        d = np.where(np.abs(d) > 1e-6, d, 1e-6)
        s = np.minimum(np.maximum(s - xs / d, 0.0), 1.0)
    bad = np.abs(((ax * s + bx) * s + cx) * s - u) > 1e-6
    if np.any(bad):
        lo, hi = np.zeros_like(u), np.ones_like(u)
        for _ in range(32):
            mid = (lo + hi) / 2.0
            below = ((ax * mid + bx) * mid + cx) * mid < u
            lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        s = np.where(bad, (lo + hi) / 2.0, s)
    return ((ay * s + by) * s + cy) * s


def _bz(p):
    return lambda u: bezier_y(u, *p)


CSS_KEYWORDS = {"linear": (0.0, 0.0, 1.0, 1.0), "ease": (0.25, 0.1, 0.25, 1.0), "ease-in": (0.42, 0.0, 1.0, 1.0),
                "ease-out": (0.0, 0.0, 0.58, 1.0), "ease-in-out": (0.42, 0.0, 0.58, 1.0)}
NAMED = {"linear": lambda u: np.asarray(u, dtype=float)}
for _k in ("ease", "ease-in", "ease-out", "ease-in-out"):
    NAMED[_k] = _bz(CSS_KEYWORDS[_k])
for _n in (1, 2, 3, 4):                         # GSAP: power1 = quad, power2 = cubic, power3 = quart, power4 = quint
    _f = _pow_in(_n + 1)
    NAMED[f"power{_n}.in"], NAMED[f"power{_n}.out"], NAMED[f"power{_n}.inOut"] = _f, _out_of(_f), _inout_of(_f)
for _nm, _f in (("expo", _expo_in), ("sine", _sine_in), ("circ", _circ_in)):
    NAMED[f"{_nm}.in"], NAMED[f"{_nm}.out"], NAMED[f"{_nm}.inOut"] = _f, _out_of(_f), _inout_of(_f)
_bo = _back_out()
NAMED["back.out"], NAMED["back.in"], NAMED["back.inOut"] = _bo, _out_of(_bo), _inout_from_out(_bo)

# приближения именованных кривых через cubic-bezier (easings.net) — CSS-строка паспорта и старт подбора
BEZIER_OF = {
    "power1.in": (0.11, 0, 0.5, 0), "power1.out": (0.5, 1, 0.89, 1), "power1.inOut": (0.45, 0, 0.55, 1),
    "power2.in": (0.32, 0, 0.67, 0), "power2.out": (0.33, 1, 0.68, 1), "power2.inOut": (0.65, 0, 0.35, 1),
    "power3.in": (0.5, 0, 0.75, 0), "power3.out": (0.25, 1, 0.5, 1), "power3.inOut": (0.76, 0, 0.24, 1),
    "power4.in": (0.64, 0, 0.78, 0), "power4.out": (0.22, 1, 0.36, 1), "power4.inOut": (0.83, 0, 0.17, 1),
    "sine.in": (0.12, 0, 0.39, 0), "sine.out": (0.61, 1, 0.88, 1), "sine.inOut": (0.37, 0, 0.63, 1),
    "expo.in": (0.7, 0, 0.84, 0), "expo.out": (0.16, 1, 0.3, 1), "expo.inOut": (0.87, 0, 0.13, 1),
    "circ.in": (0.55, 0, 1, 0.45), "circ.out": (0, 0.55, 0.45, 1), "circ.inOut": (0.85, 0, 0.15, 1),
    "back.in": (0.36, 0, 0.66, -0.56), "back.out": (0.34, 1.56, 0.64, 1), "back.inOut": (0.68, -0.6, 0.32, 1.6),
    **CSS_KEYWORDS}
GSAP_ALIAS = {"none": "linear", "linear": "linear", "power0": "linear", "quad": "power1", "cubic": "power2",
              "quart": "power3", "quint": "power4", "strong": "power4"}
U41 = np.linspace(0.0, 1.0, 41)


def css_bezier(p, nd=3):
    return "cubic-bezier(" + ", ".join(f"{round(float(x), nd):g}" for x in p) + ")"


def ease_fn(spec):
    """Кривая по имени GSAP («power3.out», «expo», «back.out(2)», «none») или строке CSS (ключевое слово,
    cubic-bezier(…), linear(…)) → функция прогресса; None — неизвестно (steps, elastic, функция)."""
    if spec is None:
        return None
    if isinstance(spec, (list, tuple)) and len(spec) == 4:
        p = tuple(float(x) for x in spec)
        return _bz(p)
    s = str(spec).strip()
    if s in NAMED:
        return NAMED[s]
    m = re.match(r"cubic-bezier\(\s*([-\d.e]+)\s*,\s*([-\d.e]+)\s*,\s*([-\d.e]+)\s*,\s*([-\d.e]+)\s*\)$", s)
    if m:
        return _bz(tuple(float(x) for x in m.groups()))
    m = re.match(r"linear\((.+)\)$", s)
    if m:                                   # CSS linear(0, 0.25 40%, 1): точки с необязательными позициями
        pts = []
        for part in m.group(1).split(","):
            nums = re.findall(r"-?[\d.]+%?", part)
            if not nums:
                return None
            v = float(nums[0])
            pos = [float(x[:-1]) / 100 for x in nums[1:] if x.endswith("%")]
            pts.append((v, pos[0] if pos else None))
        n = len(pts)
        xs = [p[1] if p[1] is not None else (i / (n - 1) if n > 1 else 0.0) for i, p in enumerate(pts)]
        ys = [p[0] for p in pts]
        return lambda u: np.interp(np.asarray(u, dtype=float), xs, ys)
    m = re.match(r"([a-z]+\d?)(?:\.(in|out|inOut))?(?:\(([-\d.]+)\))?$", s, re.I)
    if m:
        base, kind, arg = m.group(1).lower(), m.group(2) or "out", m.group(3)
        base = GSAP_ALIAS.get(base, base)
        if base == "linear":
            return NAMED["linear"]
        if base == "back" and arg:
            bo = _back_out(float(arg))
            return {"out": bo, "in": _out_of(bo), "inOut": _inout_from_out(bo)}[kind]
        key = f"{base}.{kind}"
        if key in NAMED:
            return NAMED[key]
    return None


def curve_distance(fa, fb):
    """Расстояние кривых — среднеквадратичная разница прогресса в 41 точке [0, 1] (доли прогресса)."""
    return float(np.sqrt(np.mean((np.asarray(fa(U41), float) - np.asarray(fb(U41), float)) ** 2)))


def nearest_named(f, names=None):
    best = None
    for nm in names or NAMED:
        d = curve_distance(f, NAMED[nm])
        if best is None or d < best[1]:
            best = (nm, d)
    return best


def _err_rows(F, vs, v0, v1):
    """Ошибка подбора по строкам F (вариант × отсчёт) в долях прогресса; v0 None — исходное значение подбирается
    наименьшими квадратами (v = v0·(1 − f) + v1·f)."""
    if v0 is None:
        g = 1.0 - F
        den = np.sum(g * g, axis=1)
        num = np.sum(g * (vs[None, :] - v1 * F), axis=1)
        v0r = np.where(den > 1e-12, num / np.where(den > 1e-12, den, 1.0), vs[0])
    else:
        v0r = np.full(F.shape[0], float(v0))
    span = np.abs(v1 - v0r)
    span = np.where(span > 1e-9, span, 1e-9)
    pred = v0r[:, None] + (v1 - v0r)[:, None] * F
    return np.sqrt(np.mean(((pred - vs[None, :]) / span[:, None]) ** 2, axis=1)), v0r


_TU = np.linspace(0.0, 1.0, 4001)
_INV = {}


def _inverse_table(nm):
    """Таблица кривой для обратной функции: возрастающая часть (у back.out — до пика перелёта) и производная."""
    if nm not in _INV:
        F = np.asarray(NAMED[nm](_TU), dtype=float)
        k = int(np.argmax(F)) if float(np.max(F)) > 1.0 + 1e-6 else len(F) - 1
        F1, U1 = F[: k + 1], _TU[: k + 1]
        ok = bool(np.all(np.diff(F1) >= -1e-12)) and abs(float(F1[0])) < 1e-9 and k > 10
        _INV[nm] = (F1, U1, np.gradient(F, _TU)[: k + 1]) if ok else None
    return _INV[nm]


def _closed_form(nm, xs, vs, v0, v1):
    """Начало и конец отрезка при известных исходном и конечном значениях: прогресс → нормированная координата через
    обратную функцию кривой, затем взвешенная регрессия x = s + (e − s)·u (вес — квадрат производной кривой: плоский
    хвост кривых out почти не меняет прогресс и не должен решать). None — кривая не обращается или мало точек."""
    tab = _inverse_table(nm)
    if tab is None or abs(v1 - v0) < 1e-12:
        return None
    F, U, dF = tab
    p = (vs - v0) / (v1 - v0)
    m = (p > 1e-4) & (p < min(1.0, float(F[-1])) - 1e-4)
    if float(F[-1]) > 1.0 + 1e-6:                  # перелёт: только до максимума прогресса
        m &= np.arange(len(p)) <= int(np.argmax(p))
    if int(m.sum()) < 2:
        return None
    u = np.interp(p[m], F, U)
    w = np.sqrt(np.interp(u, U, dF) ** 2 + 1e-6)
    A = np.vstack([np.ones_like(u), u]).T * w[:, None]
    sol, *_ = np.linalg.lstsq(A, xs[m] * w, rcond=None)
    s0, D = float(sol[0]), float(sol[1])
    return (s0, s0 + D) if D > 0 else None


def fit_axis(xs, vs, s_lo, s_hi, e_lo, e_hi, v0=None, names=None):
    """Начало, конец и кривая отрезка по отсчётам (x — время в мс или прокрутка в px), для каждой именованной кривой:
    при известном исходном значении — решение через обратную функцию и уточнение сеткой вокруг него, иначе (и у кривых
    без обратной функции) — сетка 25 × 13 по окнам начала и конца и три уровня уточнения. → dict: named, error, s, e,
    v0, v1, ranking."""
    xs, vs = np.asarray(xs, dtype=float), np.asarray(vs, dtype=float)
    v1 = float(vs[-1])
    names = list(names or NAMED)

    def grid(lo, hi, n=9):
        return np.linspace(lo, hi, n) if hi > lo + 1e-9 else np.array([lo])

    def search(nm, S, E):
        A0, A1 = np.meshgrid(S, E, indexing="ij")
        A0, A1 = A0.ravel(), A1.ravel()
        ok = A1 - A0 > 1e-6
        if not np.any(ok):
            return None
        A0, A1 = A0[ok], A1[ok]
        U = np.clip((xs[None, :] - A0[:, None]) / (A1 - A0)[:, None], 0.0, 1.0)
        err, v0r = _err_rows(np.asarray(NAMED[nm](U), dtype=float), vs, v0, v1)
        if v0 is None and s_hi > s_lo:
            # без отсчёта покоя у кривых out (v0·(1 − u)ⁿ) старт и исходное значение меняются друг на друга без роста
            # ошибки: при равной ошибке берётся середина окна старта
            err = err + 1e-4 * np.abs(A0 - (s_lo + s_hi) / 2.0) / (s_hi - s_lo)
        j = int(np.nanargmin(err))
        return float(err[j]), float(A0[j]), float(A1[j]), float(v0r[j])

    def clip_s(x):
        return min(max(x, s_lo), s_hi)

    def clip_e(x):
        return min(max(x, e_lo), e_hi)

    def refine(nm, cur, hs, he):
        for _ in range(3):                           # окно ± шаг, затем ÷ 4
            r = search(nm, grid(clip_s(cur[2] - hs), clip_s(cur[2] + hs)), grid(clip_e(cur[3] - he), clip_e(cur[3] + he)))
            if r and r[0] <= cur[0]:
                cur = (r[0], nm, r[1], r[2], r[3])
            hs, he = hs / 4, he / 4
        return cur
    res = []
    span = max(1e-6, float(xs[-1] - xs[0]))
    for nm in names:
        cf = _closed_form(nm, xs, vs, v0, v1) if v0 is not None else None
        if cf is not None:
            h = 0.02 * span
            r = search(nm, grid(clip_s(cf[0] - h), clip_s(cf[0] + h)), grid(clip_e(cf[1] - h), clip_e(cf[1] + h)))
            if r:
                res.append(refine(nm, (r[0], nm, r[1], r[2], r[3]), h / 4, h / 4))
                continue
        r = search(nm, grid(s_lo, s_hi, 25), grid(e_lo, e_hi, 13))
        if r:
            res.append(refine(nm, (r[0], nm, r[1], r[2], r[3]), (s_hi - s_lo) / 24, (e_hi - e_lo) / 12))
    if not res:
        return None
    res.sort()
    err, nm, s0, e0, v0r = res[0]
    return {"named": nm, "error": err, "s": s0, "e": e0, "v0": v0r, "v1": v1,
            "ranking": [[n, round(e_, 4)] for e_, n, *_ in res[:4]]}


def fit_bezier(u, p, init=None):
    """Лучший cubic-bezier(x1, y1, x2, y2) к точкам (u, прогресс) — Левенберг — Марквардт на numpy; x1, x2 ∈ [0, 1],
    y1, y2 ∈ [−1,5; 2,5]. → ([x1, y1, x2, y2], ошибка в долях прогресса)."""
    u, p = np.asarray(u, dtype=float), np.asarray(p, dtype=float)
    lo = np.array([0.0, -1.5, 0.0, -1.5])
    hi = np.array([1.0, 2.5, 1.0, 2.5])
    starts = ([tuple(init)] if init else []) + [(0.33, 1.0, 0.68, 1.0), (0.65, 0.0, 0.35, 1.0)]

    def res(q):
        return bezier_y(u, *q) - p

    best = None
    for st in starts:
        q = np.clip(np.array(st, dtype=float), lo, hi)
        r = res(q)
        c = float(r @ r)
        lam = 1e-3
        for _ in range(40):
            J = np.empty((len(u), 4))
            for k in range(4):
                h = 1e-5 if q[k] + 1e-5 <= hi[k] else -1e-5
                dq = q.copy()
                dq[k] += h
                J[:, k] = (res(dq) - r) / h
            A, g = J.T @ J, J.T @ r
            try:
                step = -np.linalg.solve(A + lam * (np.diag(np.diag(A)) + 1e-9 * np.eye(4)), g)
            except np.linalg.LinAlgError:
                break
            qn = np.clip(q + step, lo, hi)
            rn = res(qn)
            cn = float(rn @ rn)
            if cn < c - 1e-14:
                q, r, c, lam = qn, rn, cn, max(lam / 3.0, 1e-9)
                if float(np.max(np.abs(step))) < 1e-6:
                    break
            else:
                lam *= 8.0
                if lam > 1e7:
                    break
        if best is None or c < best[1]:
            best = (q, c)
    q, c = best
    return [round(float(x), 3) for x in q], float(math.sqrt(c / max(1, len(u))))


def fit_curve(xs, vs, s_lo, s_hi, e_lo, e_hi, v0=None):
    """Именованная кривая и cubic-bezier одного отрезка: начало и конец — из подбора именованной, затем bezier,
    затем уточнение начала и конца под bezier. → dict или None (меньше 3 отсчётов или нет изменения)."""
    xs, vs = np.asarray(xs, dtype=float), np.asarray(vs, dtype=float)
    if len(xs) < 3 or float(np.ptp(vs)) <= 0 and v0 is None:
        return None
    nf = fit_axis(xs, vs, s_lo, s_hi, e_lo, e_hi, v0=v0)
    if not nf:
        return None
    s0, e0, v0f, v1 = nf["s"], nf["e"], nf["v0"], nf["v1"]
    if abs(v1 - v0f) < 1e-9 or e0 - s0 <= 1e-6:
        return None

    def up(s_, e_):
        return np.clip((xs - s_) / (e_ - s_), 0.0, 1.0), (vs - v0f) / (v1 - v0f)

    u, p = up(s0, e0)
    bz, bz_err = fit_bezier(u, p, init=BEZIER_OF.get(nf["named"]))
    ds, de = max(1e-6, (s_hi - s_lo) / 6), max(1e-6, (e_hi - e_lo) / 6)
    best = (bz_err, s0, e0)
    for s_ in np.linspace(max(s_lo, s0 - ds), min(s_hi, s0 + ds), 5):
        for e_ in np.linspace(max(e_lo, e0 - de), min(e_hi, e0 + de), 5):
            if e_ - s_ <= 1e-6:
                continue
            uu, pp = up(s_, e_)
            er = float(np.sqrt(np.mean((bezier_y(uu, *bz) - pp) ** 2)))
            if er < best[0] - 1e-6:
                best = (er, s_, e_)
    if best[1:] != (s0, e0):
        u, p = up(best[1], best[2])
        bz2, er2 = fit_bezier(u, p, init=bz)
        if er2 < bz_err:
            bz, bz_err = bz2, er2
    return {"named": nf["named"], "named_error": round(nf["error"], 4), "bezier": bz, "bezier_error": round(bz_err, 4),
            "s": nf["s"], "e": nf["e"], "v0": v0f, "v1": v1, "ranking": nf["ranking"], "n": int(len(xs))}


# =====================================================================================================================
# 2. Токены motion.marketing: ближайшая длительность и кривая (для моментов motion-spec)
# =====================================================================================================================
_TOK = {}


def tokens(path=None):
    """Шкала motion.marketing: длительности и стаггер (мс), кривые (cubic-bezier) — из marketing-tokens.json."""
    path = path or TOKENS
    if path in _TOK:
        return _TOK[path]
    out = {"duration": {}, "stagger": {}, "easing": {}}
    try:
        d = json.load(open(path, encoding="utf-8"))
        m = (d.get("motion") or {}).get("marketing") or d.get("motion") or {}
        for grp in ("duration", "stagger"):
            for k, v in (m.get(grp) or {}).items():
                val = v.get("$value") if isinstance(v, dict) else None
                if isinstance(val, dict) and isinstance(val.get("value"), (int, float)):
                    out[grp][k] = float(val["value"]) * (1000.0 if val.get("unit") == "s" else 1.0)
        for k, v in (m.get("easing") or {}).items():
            val = v.get("$value") if isinstance(v, dict) else None
            if isinstance(val, list) and len(val) == 4:
                out["easing"][k] = tuple(float(x) for x in val)
    except Exception:
        pass
    _TOK[path] = out
    return out


def nearest_token_duration(ms, grp="duration"):
    tk = tokens()[grp]
    if not ms or not tk:
        return None
    k, v = min(tk.items(), key=lambda kv: abs(kv[1] - ms))
    return {"token": f"motion.marketing.{grp}.{k}", "ms": v, "delta_pct": round(100.0 * (ms - v) / v, 1) if v else None}


def nearest_token_easing(f):
    tk = tokens()["easing"]
    if f is None or not tk:
        return None
    k, d = min(((k, curve_distance(f, _bz(p))) for k, p in tk.items()), key=lambda x: x[1])
    return {"token": f"motion.marketing.easing.{k}", "distance": round(d, 4)}


# =====================================================================================================================
# 3. Инструментирование страницы (до любых скриптов)
# =====================================================================================================================
INIT = r"""
(() => {
  if (window.__mp) return;
  const M = window.__mp = {list: [], els: new Map(), scroll: [], sentScroll: 0, frames: 0, dropped: 0, over: 0, lastChange: 0,
    gtw: [], gseen: new WeakMap(), gid: 0, gpolls: 0, gmap: [], gl: 0, cands: []};
  const LIM_ELS = 1200, LIM_S = 4000, LIM_BATCH = 300;
  const R1 = (x) => Math.round(x * 10) / 10;
  const esc = (s) => (window.CSS && CSS.escape) ? CSS.escape(s) : s;
  const selOf = (el) => { if (!el || !el.tagName) return '';
    const id = el.id ? '#' + el.id : '';
    const c = (typeof el.className === 'string' && el.className.trim()) ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.') : '';
    return (el.tagName.toLowerCase() + id + c).slice(0, 90); };
  const cssPath = (el) => { const parts = []; let n = el, d = 0;
    while (n && n.nodeType === 1 && n !== document.documentElement && d < 40) {
      if (n.id && /^[A-Za-z][\w-]*$/.test(n.id)) { let u = false; try { u = document.querySelectorAll('#' + esc(n.id)).length === 1; } catch (e) {}
        if (u) { parts.unshift('#' + esc(n.id)); return parts.join(' > '); } }
      let i = 1, s = n; while ((s = s.previousElementSibling)) if (s.tagName === n.tagName) i++;
      parts.unshift(n.tagName.toLowerCase() + ':nth-of-type(' + i + ')'); n = n.parentElement; d++; }
    return parts.join(' > '); };
  // классы-состояния (is-visible, active, aos-animate …) не входят в подпись группы: соседи узнаются и после смены класса
  const STATE_CLS = /^(is-|has-|active$|visible$|show$|shown$|in-view|inview|animated?$|done$|loaded$|ready$|aos-|revealed?$)/;
  M.describe = (el) => { if (!el || el.nodeType !== 1) return null;
    let r = null; try { r = el.getBoundingClientRect(); } catch (e) {}
    const ds = el.dataset || {}; const up = (s) => { try { return el.closest(s); } catch (e) { return null; } };
    const sec = up('[data-section]'), grp = up('[data-group]'), par = el.parentElement;
    let depth = 0; for (let n = el; n && n !== document.documentElement && depth < 80; n = n.parentElement) depth++;
    const cls = (typeof el.className === 'string') ? el.className.trim().split(/\s+/).filter(c => c && !STATE_CLS.test(c)).sort().slice(0, 3) : [];
    return {sel: selOf(el), path: cssPath(el), tag: el.tagName.toLowerCase(), sig: el.tagName.toLowerCase() + (cls.length ? '.' + cls.join('.') : ''),
      text: ((el.textContent || '') + '').replace(/\s+/g, ' ').trim().slice(0, 32),
      rect: r ? [R1(r.left + scrollX), R1(r.top + scrollY), R1(r.width), R1(r.height)] : null,
      parent: par ? cssPath(par) : '', idx: par ? Array.prototype.indexOf.call(par.children, el) : 0, depth,
      data: {moment: ds.moment || null, slot: ds.slot || null, fx: ds.fx || null, group: grp ? grp.getAttribute('data-group') : null,
             section: sec ? sec.getAttribute('data-section') : null}}; };
  const read = (el) => { let cs; try { cs = getComputedStyle(el); } catch (e) { return null; }
    let cust = ''; const st = el.style;
    if (st && st.length) { const a = []; for (let i = 0; i < st.length && a.length < 6; i++) { const p = st[i];
        if (p.charCodeAt(0) === 45 && p.charCodeAt(1) === 45) a.push(p + ':' + st.getPropertyValue(p).trim().slice(0, 40)); } cust = a.join(';'); }
    const tr = cs.translate, sc = cs.scale, ro = cs.rotate;
    const ind = ((tr && tr !== 'none') || (sc && sc !== 'none') || (ro && ro !== 'none')) ? [tr, sc, ro].join('|') : '';
    return [cs.opacity, cs.transform, cs.clipPath, cs.filter, cust, ind]; };
  const add = (rec, s) => { if (rec.tot < LIM_S) { rec.s.push(s); rec.tot++; } else M.over++; };
  // отсчёт пишется при смене значения; повтор того же значения продлевает «удержание» (отсчёт удержания — перед сменой)
  M.ingest = (recs, t) => { if (!recs || !recs.length) return; const dirty = new Set();
    for (const r of recs) { const el = r.target; if (el && el.nodeType === 1 && el.id !== '__mp_flash') dirty.add(el); }
    const y = R1(scrollY); let k = 0;
    for (const el of dirty) { if (++k > LIM_BATCH) { M.over++; break; }
      let rec = M.els.get(el);
      if (!rec) { if (M.list.length >= LIM_ELS) { M.dropped++; continue; }
        rec = {i: M.list.length, s: [], tot: 0, key: null, v: null, kt: t, kt1: t, ky1: y, n: 0, first: t, d: M.describe(el), sent: false};
        M.els.set(el, rec); M.list.push(rec); }
      const v = read(el); if (!v) continue; const key = v.join('\u0001');
      if (key !== rec.key) {
        if (rec.key !== null && rec.kt1 > rec.kt + 0.5) add(rec, [R1(rec.kt1), rec.ky1].concat(rec.v));
        add(rec, [R1(t), y].concat(v)); if (rec.key !== null) M.lastChange = t;
        rec.key = key; rec.v = v; rec.kt = t; rec.kt1 = t; rec.ky1 = y; rec.n++;
      } else { rec.kt1 = t; rec.ky1 = y; } } };
  let mo = null;
  try { mo = new MutationObserver((r) => M.ingest(r, performance.now()));
        mo.observe(document, {subtree: true, attributes: true, attributeFilter: ['style']}); } catch (e) {}
  M.busy = (ms) => { const t = performance.now(); let n = 0;
    for (const r of M.list) if (r.n > 1 && t - r.kt < ms && !(r.kt - r.first > 2500 && r.n > 90)) n++;
    try { for (const x of document.getAnimations()) { if (x.playState !== 'running' || x.timeline !== document.timeline) continue;
        const c = x.effect && x.effect.getComputedTiming ? x.effect.getComputedTiming() : null; if (c && isFinite(c.endTime)) n++; } } catch (e) {}
    return n; };
  M.drain = (fin) => { const els = [], s = [];
    for (const r of M.list) { if (!r.sent) { els.push([r.i, r.d]); r.sent = true; }
      if (fin && r.key !== null && r.kt1 > r.kt + 0.5) { add(r, [R1(r.kt1), r.ky1].concat(r.v)); r.kt = r.kt1; }
      if (r.s.length) { s.push([r.i, r.s]); r.s = []; } }
    const sc = M.scroll.slice(M.sentScroll); M.sentScroll = M.scroll.length;
    return {els, s, scroll: sc, dropped: M.dropped, over: M.over, frames: M.frames, now: R1(performance.now())}; };
  // кадр: записи наблюдателя (под page.clock микрозадачи ждут конца прогона — takeRecords здесь же), прокрутка, GSAP
  // забор записей наблюдателя: под page.clock кадры идут подряд в одной задаче и микрозадачи ждут конца прогона —
  // setTimeout(0) из кадра срабатывает в том же кадре после остальных обработчиков rAF (время кадра то же)
  const late = () => { if (mo) { try { const r = mo.takeRecords(); if (r.length) M.ingest(r, performance.now()); } catch (e) {} } };
  const tick = () => { const t = performance.now();
    late(); setTimeout(late, 0);
    const y = R1(scrollY), L = M.scroll; if (!L.length || L[L.length - 1][1] !== y) L.push([R1(t), y]);
    M.frames++; if ((M.frames & 3) === 0) { try { M.gpoll(t); } catch (e) {} }
    requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  try { const orig = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, ...a) { const c = orig.call(this, type, ...a);
      try { if (c && /webgl|webgpu/i.test(String(type)) && !this.__mpgl) { this.__mpgl = 1; M.gl++; } } catch (e) {} return c; }; } catch (e) {}
  // GSAP: корневая шкала удаляет доигравшие твины — опрос копит их по мере появления
  const call = (o, k, a) => { try { return typeof o[k] === 'function' ? (a === undefined ? o[k]() : o[k](a)) : undefined; } catch (e) { return undefined; } };
  M.gpoll = (t) => { const g = window.gsap; const tl = g && g.globalTimeline;
    if (!tl || typeof tl.getChildren !== 'function') return;
    let kids; try { kids = tl.getChildren(true, true, true); } catch (e) { return; }
    const gt = call(tl, 'time'); if (typeof gt === 'number' && M.gmap.length < 600) M.gmap.push([R1(t), gt]);
    M.gpolls++;
    for (const tw of kids || []) { if (!tw || typeof tw !== 'object' || M.gseen.has(tw)) continue; if (M.gtw.length >= 4000) break;
      M.gseen.set(tw, ++M.gid); M.gtw.push({id: M.gid, tw, seen: R1(t), gt: typeof gt === 'number' ? gt : null}); } };
  const RESERVED = new Set(('onComplete onUpdate onStart onRepeat onReverseComplete onInterrupt onCompleteParams onUpdateParams onStartParams ' +
    'onRepeatParams onReverseCompleteParams onInterruptParams parent duration ease delay overwrite runBackwards startAt yoyo immediateRender ' +
    'repeat repeatDelay data paused reversed lazy callbackScope stringFilter id yoyoEase stagger inherit repeatRefresh keyframes autoRevert ' +
    'scrollTrigger easeReverse defaults smoothChildTiming autoRemoveChildren onToggle force3D modifiers snap fastScrollEnd preventOverlaps').split(' '));
  const val = (v, d) => { d = d || 0; if (v === null) return null; if (v === undefined) return undefined; const ty = typeof v;
    if (ty === 'number') return isFinite(v) ? v : String(v); if (ty === 'boolean') return v; if (ty === 'string') return v.slice(0, 80);
    if (ty === 'function') return 'fn'; if (v.nodeType === 1) return {el: selOf(v)};
    if (Array.isArray(v)) return d > 2 ? '[...]' : v.slice(0, 12).map(x => val(x, d + 1));
    if (ty === 'object') { if (d > 2) return '{...}'; const o = {}; let k = 0;
      for (const key of Object.keys(v)) { if (++k > 16) break; o[key] = val(v[key], d + 1); } return o; }
    return String(v).slice(0, 40); };
  const stIds = new WeakMap(); let stN = 0; const stId = (s) => { if (!stIds.has(s)) stIds.set(s, ++stN); return stIds.get(s); };
  M.gdump = () => { const g = window.gsap; const out = {version: g ? (g.version || null) : null, versions: window.gsapVersions || null,
      defaults: g ? val(call(g, 'defaults')) : null, gmap: M.gmap, polls: M.gpolls, tweens: [], timelines: [], truncated: M.gtw.length >= 4000};
    for (const {id, tw, seen, gt} of M.gtw) {
      const isTween = typeof tw.targets === 'function';
      const r = {id, seen, gt, duration: call(tw, 'duration'), delay: call(tw, 'delay'), start: call(tw, 'startTime'), repeat: call(tw, 'repeat'),
        yoyo: call(tw, 'yoyo'), global_start: call(tw, 'globalTime', 0), progress: call(tw, 'progress'), active: call(tw, 'isActive'),
        parent: (tw.parent && M.gseen.has(tw.parent)) ? M.gseen.get(tw.parent) : null, st: tw.scrollTrigger ? stId(tw.scrollTrigger) : null};
      const vars = tw.vars || {}; r.ease = typeof vars.ease === 'string' ? vars.ease : (vars.ease ? 'fn' : null);
      r.vars = {}; for (const k of Object.keys(vars).slice(0, 40)) { if (k === 'scrollTrigger' || k === 'parent') continue; r.vars[k] = val(vars[k]); }
      r.props = Object.keys(vars).filter(k => !RESERVED.has(k)).slice(0, 20);
      if (isTween) { const tg = call(tw, 'targets') || [];
        r.n_targets = tg.length; r.targets = tg.slice(0, 16).map(el => (el && el.nodeType === 1) ? {i: M.els.has(el) ? M.els.get(el).i : null, d: M.describe(el)} : {obj: String(el).slice(0, 30)}); }
      (isTween ? out.tweens : out.timelines).push(r); }
    return out; };
  M.stdump = () => { const S = window.ScrollTrigger; if (!S || typeof S.getAll !== 'function') return null;
    let all = []; try { all = S.getAll() || []; } catch (e) { return {error: String(e).slice(0, 80)}; }
    const str = (x) => typeof x === 'string' ? x.slice(0, 60) : (typeof x === 'function' ? 'fn' : (x == null ? null : (typeof x === 'number' ? x : String(x).slice(0, 60))));
    const list = all.slice(0, 300).map(s => { const v = s.vars || {}; const sn = v.snap; let snap = null;
      if (sn != null && sn !== false) { if (typeof sn === 'number') snap = {kind: 'increment', value: sn};
        else if (Array.isArray(sn)) snap = {kind: 'points', values: sn.slice(0, 24).filter(x => typeof x === 'number')};
        else if (typeof sn === 'string') snap = {kind: sn};
        else if (typeof sn === 'function') snap = {kind: 'fn'};
        else if (typeof sn === 'object') { const to = sn.snapTo; snap = {kind: 'object', snapTo: typeof to === 'number' ? to : (Array.isArray(to) ? to.slice(0, 24) : str(to)),
          duration: val(sn.duration, 1), delay: typeof sn.delay === 'number' ? sn.delay : null, ease: typeof sn.ease === 'string' ? sn.ease : null}; } }
      const an = s.animation; let labels = null;
      try { if (an && an.labels && Object.keys(an.labels).length) { const d = an.duration(); labels = Object.entries(an.labels).slice(0, 24).map(([k, t]) => [k, d ? t / d : null]); } } catch (e) {}
      if (an && typeof an === 'object' && !M.gseen.has(an)) { M.gseen.set(an, ++M.gid); M.gtw.push({id: M.gid, tw: an, seen: R1(performance.now()), gt: null}); }
      return {id: stId(s), trigger: s.trigger && s.trigger.nodeType === 1 ? M.describe(s.trigger) : null, start: typeof s.start === 'number' ? s.start : null,
        end: typeof s.end === 'number' ? s.end : null, start_str: str(v.start), end_str: str(v.end), scrub: v.scrub === undefined ? null : val(v.scrub, 1),
        pin: (s.pin && s.pin.nodeType === 1) ? M.describe(s.pin) : null, pin_spacing: v.pinSpacing === undefined ? null : val(v.pinSpacing, 1),
        pin_type: typeof v.pinType === 'string' ? v.pinType : null, snap, labels, toggle_actions: typeof v.toggleActions === 'string' ? v.toggleActions : null,
        once: !!v.once, horizontal: !!v.horizontal, container: !!v.containerAnimation, anim: (an && M.gseen.has(an)) ? M.gseen.get(an) : null,
        progress: typeof s.progress === 'number' ? s.progress : null}; });
    return {version: S.version || null, list}; };
  M.libs = () => { const H = document.documentElement, o = {};
    const g = window.gsap; o.gsap = g ? (g.version || true) : null; o.gsap_versions = window.gsapVersions || null;
    o.scrolltrigger = window.ScrollTrigger ? (window.ScrollTrigger.version || true) : null;
    o.scrollsmoother = window.ScrollSmoother ? (window.ScrollSmoother.version || true) : null;
    try { const sm = window.ScrollSmoother && window.ScrollSmoother.get && window.ScrollSmoother.get();
      if (sm) o.smoother = {smooth: call(sm, 'smooth'), effects: !!(sm.vars && sm.vars.effects), speed: sm.vars ? val(sm.vars.speed, 1) : null}; } catch (e) {}
    o.splittext = !!window.SplitText;
    o.lenis_version = window.lenisVersion || ((window.lenis && typeof window.lenis.version === 'string') ? window.lenis.version : null);
    o.lenis_class = H.classList.contains('lenis'); o.lenis_smooth = H.classList.contains('lenis-smooth');
    o.locomotive = H.classList.contains('has-scroll-smooth') || !!document.querySelector('[data-scroll-container]') || !!window.LocomotiveScroll;
    const isLenis = (v) => { try { return !!(v && typeof v === 'object' && ('animatedScroll' in v) && ('targetScroll' in v) && v.options && typeof v.options === 'object'); } catch (e) { return false; } };
    let inst = null, name = null;
    for (const k of ['lenis', '__lenis', 'smoothScroll', 'scroller', 'scroll']) { try { if (isLenis(window[k])) { inst = window[k]; name = k; break; } } catch (e) {} }
    if (!inst) { let n = 0;
      for (const k of Object.keys(window)) { if (++n > 3000) break; let v; try { v = window[k]; } catch (e) { continue; }
        if (isLenis(v)) { inst = v; name = k; break; }
        try { if (v && typeof v === 'object' && !Array.isArray(v) && v !== window && !(v instanceof Node)) {
            for (const kk of Object.keys(v).slice(0, 40)) { let w; try { w = v[kk]; } catch (e) { continue; } if (isLenis(w)) { inst = w; name = k + '.' + kk; break; } } } } catch (e) {}
        if (inst) break; } }
    if (inst) { const op = {}; for (const [k, v] of Object.entries(inst.options || {})) { if (['number', 'boolean', 'string'].includes(typeof v)) op[k] = v; else if (typeof v === 'function') op[k] = 'fn'; }
      o.lenis = {global: name, options: op}; }
    const an = window.anime; o.anime = an ? {version: an.version || null, running: Array.isArray(an.running) ? an.running.length : null} : null;
    o.motion = !!(window.Motion || window.MotionGlobalConfig); o.three = !!(window.THREE || window.__THREE__); o.barba = !!window.barba;
    o.swup = !!window.swup; o.lottie = !!(window.lottie || window.bodymovin); o.scroll_behavior = getComputedStyle(H).scrollBehavior;
    let snapType = null; for (const e of [H, document.body]) { if (!e) continue; const v = getComputedStyle(e).scrollSnapType; if (v && v !== 'none') { snapType = v; break; } }
    if (snapType) { const pts = []; const all = document.body ? document.body.getElementsByTagName('*') : [];
      for (let i = 0; i < all.length && i < 8000 && pts.length < 40; i++) { const al = getComputedStyle(all[i]).scrollSnapAlign;
        if (al && al !== 'none') { const r = all[i].getBoundingClientRect(); pts.push([al.split(' ')[0], R1(r.top + scrollY), R1(r.height)]); } }
      o.snap = {type: snapType, points: pts}; }
    return o; };
  M.cssScan = () => { const re = {animation_timeline: /animation-timeline\s*:/g, view_timeline: /view-timeline(-name)?\s*:/g,
      scroll_timeline: /scroll-timeline(-name)?\s*:/g, animation_range: /animation-range(-start|-end)?\s*:/g, timeline_scope: /timeline-scope\s*:/g,
      view_transition_at: /@view-transition/g, view_transition_name: /view-transition-name\s*:/g, scroll_snap_type: /scroll-snap-type\s*:/g};
    const counts = {}; for (const k in re) counts[k] = 0; const blocked = []; let sheets = 0, chars = 0;
    for (const sh of Array.from(document.styleSheets)) { sheets++; let rules = null; try { rules = sh.cssRules; } catch (e) { if (sh.href) blocked.push(sh.href); continue; }
      let txt = ''; try { for (const r of Array.from(rules || [])) txt += r.cssText + '\n'; } catch (e) {}
      chars += txt.length; for (const k in re) { const m = txt.match(re[k]); if (m) counts[k] += m.length; } }
    return {counts, blocked: blocked.slice(0, 40), sheets, chars}; };
  M.unseen = () => { const IW = innerWidth, IH = innerHeight;
    const big = (e) => { try { const r = e.getBoundingClientRect(); return r.width * r.height >= 0.04 * IW * IH; } catch (x) { return false; } };
    const vids = Array.from(document.querySelectorAll('video'));
    return {webgl_contexts: M.gl, canvas: Array.from(document.querySelectorAll('canvas')).filter(big).length, video: vids.length,
      video_playing: vids.filter(v => !v.paused && !v.ended).length, svg_smil: document.querySelectorAll('animate, animateTransform, animateMotion').length,
      iframes: document.querySelectorAll('iframe').length, lottie: !!document.querySelector('lottie-player, dotlottie-player, [data-animation-path], [data-lottie]')}; };
  const POS = {sticky: 'k', fixed: 'f', absolute: 'a', relative: 'r', static: 's'};
  M.pinInit = () => { const IH = innerHeight, IW = innerWidth, c = [], seen = new Set();
    const addc = (e) => { if (!seen.has(e) && c.length < 260) { seen.add(e); c.push(e); } };
    const all = document.body ? Array.from(document.body.getElementsByTagName('*')).slice(0, 15000) : [];
    for (const e of all) { let cs; try { cs = getComputedStyle(e); } catch (x) { continue; }
      if (cs.position === 'sticky' || cs.position === 'fixed') { const r = e.getBoundingClientRect(); if (r.height >= 24 && r.width >= 24) addc(e); }
      else if (e.parentElement && e.parentElement.classList.contains('pin-spacer')) addc(e); }
    for (const e of all) { const r = e.getBoundingClientRect(); if (r.height >= 0.5 * IH && r.width >= 0.5 * IW) addc(e); }
    M.cands = c; return c.map(e => M.describe(e)); };
  M.pinSnap = () => { const v = []; for (const e of M.cands) { let r, p = 's';
      try { r = e.getBoundingClientRect(); p = POS[getComputedStyle(e).position] || '?'; } catch (x) { v.push(null); continue; }
      v.push([Math.round(r.top * 2) / 2, Math.round(r.height), p]); }
    return {t: R1(performance.now()), y: R1(scrollY), v, docH: Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)}; };
  M.nav = () => { let n = null; try { n = performance.getEntriesByType('navigation')[0]; } catch (e) {}
    let fcp = null; try { const p = performance.getEntriesByName('first-contentful-paint')[0]; fcp = p ? p.startTime : null; } catch (e) {}
    return {title: document.title, href: location.href, IW: innerWidth, IH: innerHeight, dpr: devicePixelRatio,
      docH: Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0),
      dcl: n ? R1(n.domContentLoadedEventEnd) : null, load: n ? R1(n.loadEventEnd) : null, fcp: fcp ? R1(fcp) : null,
      ua: navigator.userAgent, webdriver: navigator.webdriver}; };
  M.closedSignals = () => { const b = document.body; const t = b ? (b.innerText || '') : '';
    const fr = Array.from(document.querySelectorAll('iframe')).map(f => f.src || '').join(' ');
    const pw = Array.from(document.querySelectorAll('input[type=password]')).filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length;
    return {title: document.title || '', n: t.length, text: t.slice(0, 3000).toLowerCase(), fr, pw, href: location.href,
      cf: !!document.querySelector('#challenge-running, #challenge-form, #cf-challenge-running, .cf-browser-verification, #challenge-stage')}; };
})();
"""

# ключевые кадры, тайминг, шкала и диапазон анимации (вызывается на объекте Animation из Animation.resolveAnimation)
RESOLVE_ANIM_JS = r"""
function () {
  const a = this, ef = a.effect, M = window.__mp;
  const ser = (v) => { if (v == null) return null; if (typeof v === 'string') return {name: v};
    try { if (v.rangeName !== undefined) return {name: v.rangeName, unit: v.offset ? v.offset.unit : null, value: v.offset ? v.offset.value : null}; } catch (e) {}
    try { if (v.unit !== undefined) return {name: null, unit: v.unit, value: v.value}; } catch (e) {}
    return {name: String(v)}; };
  let kf = [];
  try { kf = ef.getKeyframes().map(k => { const o = {}; for (const [p, x] of Object.entries(k)) { if (p === 'composite' || p === 'computedOffset') continue;
      o[p] = (typeof x === 'number' || x === null) ? x : String(x).slice(0, 160); } o.offset = k.computedOffset; return o; }); } catch (e) {}
  let tm = {};
  try { const t = ef.getTiming(); tm = {duration: typeof t.duration === 'number' ? t.duration : String(t.duration), delay: t.delay, end_delay: t.endDelay,
    iterations: t.iterations === Infinity ? 'Infinity' : t.iterations, direction: t.direction, easing: t.easing, fill: t.fill}; } catch (e) {}
  const tl = a.timeline;
  let st = null; try { st = a.startTime == null ? null : (typeof a.startTime === 'number' ? a.startTime : (a.startTime.value !== undefined ? a.startTime.value : String(a.startTime))); } catch (e) {}
  return {kind: a.constructor ? a.constructor.name : null, name: a.animationName || a.transitionProperty || a.id || '', play: a.playState, start: st,
    kf, tm, tl: tl ? (tl.constructor ? tl.constructor.name : 'timeline') : null, axis: (tl && tl.axis) || null, rs: ser(a.rangeStart), re: ser(a.rangeEnd),
    pseudo: (ef && ef.pseudoElement) || null, target: (M && ef && ef.target) ? M.describe(ef.target) : null};
}
"""
DESCRIBE_JS = "function () { return window.__mp ? window.__mp.describe(this) : null; }"


# =====================================================================================================================
# 4. Отсев: защита, вход, robots.txt (признаки — списки refs_client.py)
# =====================================================================================================================
CHALLENGE_TITLE = re.compile(r"just a moment|attention required|access denied|verify(ing)? you are human|are you a robot|"
                             r"ddos-guard|security check|checking your browser|проверка браузера|доступ ограничен|один момент", re.I)
LOGIN_PATH = re.compile(r"/(login|log-in|signin|sign-in|sign_in|auth|sso|account/login|users/sign_in)(/|$)", re.I)
KEEP_HEADERS = ("cf-mitigated", "x-amzn-waf-action", "x-vercel-mitigated", "server", "retry-after")   # cookie не читаются


def closed_status(http, headers, sig, url):
    """Закрыто ли защитой или входом: (статус, пояснение) или None. sig — window.__mp.closedSignals()."""
    h = {str(k).lower(): str(v).lower() for k, v in (headers or {}).items()}
    sig = sig or {}
    for k in ("cf-mitigated", "x-amzn-waf-action", "x-vercel-mitigated"):
        if h.get(k) == "challenge":
            return "blocked", f"челлендж антибота ({k}, HTTP {http})"
    if http in (401, 403):
        return "blocked", f"HTTP {http}"
    if http == 429:
        return "blocked", "HTTP 429 — слишком много запросов"
    title, text, fr = str(sig.get("title") or ""), str(sig.get("text") or ""), str(sig.get("fr") or "")
    thin = (sig.get("n") or 0) < 1500
    if CHALLENGE_TITLE.search(title) and (thin or sig.get("cf")):
        return "blocked", f"страница проверки «{title[:48]}»"
    if sig.get("cf") and thin:
        return "blocked", "страница проверки Cloudflare"
    rc = _rc()
    for src in fr.split(" "):
        for hst in rc.CAPTCHA_HOSTS:
            if hst in src and (thin or hst in rc.CAPTCHA_ALWAYS or "bframe" in src):
                return "blocked", f"капча ({hst})"
    if thin:
        for m in rc.BLOCK_TEXT:
            if m in text or m in title.lower():
                return "blocked", f"страница блокировки («{m}»)"
        if (sig.get("pw") or 0) > 0:
            return "login", "форма входа вместо страницы"
    href = str(sig.get("href") or "")
    if href and LOGIN_PATH.search(urlparse(href).path or "") and not LOGIN_PATH.search(urlparse(url).path or ""):
        return "login", "переадресация на вход"
    return None


# =====================================================================================================================
# 5. Сеть и файлы: библиотеки по содержимому, CSS из закрытых таблиц
# =====================================================================================================================
# строки из кода самих библиотек (а не из кода, который их зовёт); третий элемент — версия в том же файле
LIB_SIGS = (
    ("gsap", rb"gsapVersions", rb'\.version\s*=\s*"(3\.\d+\.\d+)"'),
    ("ScrollTrigger", rb"pin-spacer", None),
    ("ScrollSmoother", rb"ScrollSmoother|smooth-content", None),
    ("SplitText", rb"SplitText", None),
    ("lenis", rb"lenis-smooth|lenisVersion|lenis-scrolling", None),
    ("locomotive-scroll", rb"has-scroll-smooth|LocomotiveScroll", None),
    ("anime.js", rb"anime\.js v|animejs", rb"anime\.js v(\d+\.\d+\.\d+)"),
    ("motion", rb"framerAppearId|data-framer-appear-id|MotionGlobalConfig", None),
    ("three", rb"__THREE__", None),
    ("barba", rb"@barba/core", None),
    ("swup", rb"swup-transition|data-swup", None),
    ("lottie", rb"bodymovin", None),
    ("rive", rb"@rive-app|rive\.wasm", None),
    ("theatre", rb"@theatre/core", None),
    ("split-type", rb"split-type|SplitType", None),
    ("swiper", rb"swiper-wrapper", None),
)
CSS_SIGS = {"animation_timeline": rb"animation-timeline\s*:", "view_timeline": rb"view-timeline(?:-name)?\s*:",
            "scroll_timeline": rb"scroll-timeline(?:-name)?\s*:", "animation_range": rb"animation-range(?:-start|-end)?\s*:",
            "timeline_scope": rb"timeline-scope\s*:", "view_transition_at": rb"@view-transition",
            "view_transition_name": rb"view-transition-name\s*:", "scroll_snap_type": rb"scroll-snap-type\s*:"}


def body_of(net, cdp, rid, r, cap=8 * 1024 * 1024):
    """Тело ответа: локальный — с диска (сервер motion_check), удалённый — Network.getResponseBody по CDP."""
    u = r["url"]
    if net.local_base and u.startswith(net.local_base):
        p = os.path.join(net.local_root, unquote(urlparse(u).path).lstrip("/"))
        try:
            with open(p, "rb") as f:
                return f.read(cap)
        except OSError:
            return None
    try:
        b = cdp.send("Network.getResponseBody", {"requestId": rid})
        body = b.get("body") or ""
        data = base64.b64decode(body) if b.get("base64Encoded") else body.encode("utf-8", "ignore")
        return data[:cap]
    except Exception:
        return None


def sniff_bodies(net, cdp, css_blocked):
    """Библиотеки по содержимому JS (≤ 80 файлов) и счёт CSS scroll-driven, view transitions, snap в таблицах, которые
    страница не отдала через CSSOM (чужой источник)."""
    libs, css = {}, {k: 0 for k in CSS_SIGS}
    blocked = set(css_blocked or [])
    n_js = n_css = 0
    for rid, r in list(net.req.items()):
        u = r.get("url") or ""
        if u.startswith("data:"):
            continue
        c = net.cat(r)
        if c == "js" and n_js < 80:
            n_js += 1
            data = body_of(net, cdp, rid, r)
            if not data:
                continue
            name = u.split("?")[0].rstrip("/").split("/")[-1][:60] or u[:60]
            for lib, rx, vrx in LIB_SIGS:
                if re.search(rx, data):
                    rec = libs.setdefault(lib, {"files": [], "version": None})
                    if len(rec["files"]) < 4:
                        rec["files"].append(name)
                    if vrx and not rec["version"]:
                        m = re.search(vrx, data)
                        if m:
                            rec["version"] = m.group(1).decode("ascii", "ignore")
        elif c == "css" and u in blocked and n_css < 40:
            n_css += 1
            data = body_of(net, cdp, rid, r)
            if data:
                for k, rx in CSS_SIGS.items():
                    css[k] += len(re.findall(rx, data))
    return {"libs": libs, "css_blocked_counts": css, "js_files": n_js, "css_files": n_css}


# =====================================================================================================================
# 6. CDP Animation: события, ключевые кадры, цели
# =====================================================================================================================
class AnimEvents:
    """События домена Animation (CSS-анимации, переходы, WAAPI, шкалы прокрутки); ключевые кадры и цель — после
    фазы: Animation.resolveAnimation (агент держит объекты анимаций и после конца), DOM.describeNode и DOM.resolveNode."""

    def __init__(self, cdp, limit=600):
        self.cdp, self.limit = cdp, limit
        self.anims, self.order = {}, []
        cdp.on("Animation.animationStarted", self.on_start)
        cdp.on("Animation.animationUpdated", self.on_update)
        cdp.on("Animation.animationCanceled", self.on_cancel)

    def on_start(self, e):
        an = e.get("animation") or {}
        aid = an.get("id")
        if aid is None:
            return
        if aid not in self.anims:
            if len(self.order) >= self.limit:
                return
            self.order.append(aid)
            self.anims[aid] = {"id": aid, "cdp": an}
        else:
            self.anims[aid]["cdp"] = an

    def on_update(self, e):
        an = e.get("animation") or {}
        rec = self.anims.get(an.get("id"))
        if rec is not None:
            rec["play_last"] = an.get("playState")

    def on_cancel(self, e):
        rec = self.anims.get(e.get("id"))
        if rec is not None:
            rec["canceled"] = True

    def resolve(self):
        for aid in self.order:
            rec = self.anims[aid]
            if rec.get("resolved"):
                continue
            rec["resolved"] = True
            try:
                ra = self.cdp.send("Animation.resolveAnimation", {"animationId": aid})
                oid = ra["remoteObject"]["objectId"]
                rec["page"] = self.cdp.send("Runtime.callFunctionOn", {"objectId": oid, "functionDeclaration": RESOLVE_ANIM_JS,
                                                                       "returnByValue": True})["result"].get("value")
            except Exception as ex:
                rec["resolve_error"] = str(ex)[:80]
            bid = ((rec["cdp"].get("source") or {}).get("backendNodeId"))
            if bid:
                try:
                    node = self.cdp.send("DOM.describeNode", {"backendNodeId": bid})["node"]
                    rec["node"] = {"name": node.get("nodeName"), "attrs": (node.get("attributes") or [])[:12]}
                except Exception:
                    pass
                if not ((rec.get("page") or {}).get("target")):
                    try:
                        oid = self.cdp.send("DOM.resolveNode", {"backendNodeId": bid})["object"]["objectId"]
                        rec["target"] = self.cdp.send("Runtime.callFunctionOn", {"objectId": oid, "functionDeclaration": DESCRIBE_JS,
                                                                                 "returnByValue": True})["result"].get("value")
                    except Exception:
                        pass

    def export(self):
        return [self.anims[a] for a in self.order]


# =====================================================================================================================
# 7. Замер в браузере
# =====================================================================================================================
def wait_ms(page, ms, clock=False):
    """Пауза: обычное время или шаги поддельных часов (под page.clock rAF и таймеры идут только во время run_for)."""
    if ms <= 0:
        return
    if clock:
        left = int(ms)
        while left > 0:
            d = min(100, left)
            page.clock.run_for(d)
            left -= d
    else:
        page.wait_for_timeout(int(ms))


def merge_drain(raw, d):
    for i, desc in d.get("els") or []:
        raw["els"][str(i)] = desc
    for i, ss in d.get("s") or []:
        raw["samples"].setdefault(str(i), []).extend(ss)
    raw["scroll"].extend(d.get("scroll") or [])
    raw["dropped"], raw["over"], raw["frames"] = d.get("dropped", 0), d.get("over", 0), d.get("frames", 0)


def measure(url, a, net_ctx):
    """Один прогон: загрузка → покой первого экрана → шаги колесом с паузами → сводки страницы. → сырьё (dict)."""
    from playwright.sync_api import sync_playwright
    raw = {"url": url, "wheels": [], "snaps": [], "shots": [], "els": {}, "samples": {}, "scroll": [], "log": [], "hdr": {}}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=list(MC.GPU_ARGS))
        raw["browser"] = b.version
        ctx = None
        try:
            kw = dict(locale=a.locale, reduced_motion="no-preference")
            if a.mobile:
                dev = PG.mobile_device(pw)                     # дескриптор budgets.yaml, UA — HeadlessChrome
                raw["device"] = PG.conditions()["mobile"]["descriptor"]
                ctx = b.new_context(**dev, **kw)
            else:
                ctx = b.new_context(viewport={"width": a.vw, "height": a.vh}, device_scale_factor=1, **kw)
            ctx.add_init_script(INIT)
            page = ctx.new_page()
            cdp = ctx.new_cdp_session(page)
            net = MC.Net(*net_ctx)
            net.attach(cdp)
            try:
                cdp.send("Network.enable", {"maxTotalBufferSize": 100 * 1024 * 1024, "maxResourceBufferSize": 16 * 1024 * 1024})
            except Exception:
                pass
            anim = AnimEvents(cdp)
            cdp.send("Animation.enable")
            if a.clock:
                page.clock.install()
            T0 = time.time()
            deadline = T0 + a.max_s
            resp = None
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                raw["error"] = f"страница не открылась: {str(e)[:160]}"
                return raw
            raw["http"] = resp.status if resp else None
            if resp:
                hd = resp.headers
                raw["hdr"] = {k: hd[k] for k in KEEP_HEADERS if k in hd}
            vw = page.viewport_size or {"width": a.vw, "height": a.vh}
            page.mouse.move(vw["width"] - 3, vw["height"] / 2)   # указатель у правого края: наведение не запускается
            try:
                page.wait_for_load_state("load", timeout=15000)
            except Exception:
                raw["log"].append("событие load не наступило за 15 с")
            wait_ms(page, 500, a.clock)
            raw["nav"] = page.evaluate("window.__mp ? window.__mp.nav() : null") or {}
            sig = page.evaluate("window.__mp ? window.__mp.closedSignals() : null") or {}
            closed = closed_status(raw.get("http"), raw["hdr"], sig, url)
            if closed:
                raw["closed"] = list(closed)
                return raw
            if raw.get("http") and raw["http"] >= 400:
                raw["error"] = f"HTTP {raw['http']}"
                return raw

            def ev(js, arg=None, default=None):
                """Вызов инструментирования: страница могла пересоздать документ — снятое до этого не теряется."""
                try:
                    r = page.evaluate(js, arg) if arg is not None else page.evaluate(js)
                    return default if r is None else r
                except Exception as e:
                    raw["log"].append(f"evaluate: {str(e)[:120]}")
                    return default

            def drain(fin=False):
                merge_drain(raw, ev("(f) => window.__mp ? window.__mp.drain(f) : null", fin, {}))

            # покой первого экрана: ждём, пока не доиграет сцена загрузки (петли не в счёт), не дольше 9 с
            spent, quiet = 900, 0
            wait_ms(page, 900, a.clock)
            while spent < 9000 and time.time() < deadline - 10:
                busy = ev("window.__mp ? window.__mp.busy(700) : 0", default=0)
                quiet = quiet + 1 if not busy else 0
                if quiet >= 2:
                    break
                wait_ms(page, 300, a.clock)
                spent += 300
            raw["load_phase_ms"] = spent
            drain()
            raw["pin_cands"] = ev("window.__mp ? window.__mp.pinInit() : []", default=[])

            def snap(k):
                s = ev("window.__mp ? window.__mp.pinSnap() : null")
                if not s or len(s.get("v") or []) != len(raw["pin_cands"]):
                    return                               # документ пересоздан — снимок не сравним с кандидатами
                s["k"] = k
                raw["snaps"].append(s)
                if a.frames:
                    try:
                        raw["shots"].append({"k": k, "y": s["y"], "jpg": page.screenshot(type="jpeg", quality=72)})
                    except Exception:
                        pass
            snap(0)
            H = vw["height"]
            step_px = max(40, int(round(a.scroll_step * H)))
            k, still = 0, 0
            while True:
                g = page.evaluate("({y: scrollY, max: Math.max(document.documentElement.scrollHeight, document.body ? "
                                  "document.body.scrollHeight : 0) - innerHeight})")
                scrollable = g["max"] > 2
                if scrollable and g["y"] >= g["max"] - 2:
                    break
                if not scrollable and k >= getattr(a, "virtual_steps", 8):   # не прокручивается: шаги на виртуальную прокрутку
                    break
                if time.time() > deadline - 2 or k >= 400:
                    raw["truncated"] = True
                    break
                tw = page.evaluate("[performance.now(), document.timeline.currentTime]")
                page.mouse.wheel(0, step_px)
                k += 1
                last, stable, waited = None, 0, 0
                while waited < 3000:                           # успокоение: scrollY не меняется 250 мс (хвост Lenis ≤ 1,4 с)
                    wait_ms(page, 50, a.clock)
                    waited += 50
                    y = page.evaluate("scrollY")
                    stable = stable + 50 if y == last else 0
                    last = y
                    if stable >= 250:
                        break
                wait_ms(page, a.settle_ms, a.clock)
                y1 = page.evaluate("scrollY")
                raw["wheels"].append({"k": k, "t": tw[0], "t_doc": tw[1], "dy": step_px, "y0": g["y"], "y1": y1, "max": g["max"]})
                snap(k)
                drain()
                still = still + 1 if abs(y1 - g["y"]) < 1 else 0
                if scrollable and still >= 3:
                    raw["log"].append("прокрутка стоит три шага подряд — замер остановлен")
                    break
            wait_ms(page, 300, a.clock)
            drain(True)
            raw["st"] = ev("window.__mp ? window.__mp.stdump() : null")
            raw["gsap"] = ev("window.__mp ? window.__mp.gdump() : null")
            raw["libs"] = ev("window.__mp ? window.__mp.libs() : null", default={})
            raw["css"] = ev("window.__mp ? window.__mp.cssScan() : null", default={})
            raw["unseen"] = ev("window.__mp ? window.__mp.unseen() : null", default={})
            raw["nav_end"] = ev("window.__mp ? window.__mp.nav() : null", default=raw.get("nav") or {})
            anim.resolve()
            raw["anims"] = anim.export()
            raw["sniff"] = sniff_bodies(net, cdp, (raw.get("css") or {}).get("blocked"))
            raw["seconds"] = round(time.time() - T0, 1)
        finally:
            try:
                if ctx:
                    ctx.close()
            finally:
                b.close()
    return raw


# =====================================================================================================================
# 8. Траектории инлайн-стилей → моменты
# =====================================================================================================================
_NUM = re.compile(r"-?\d*\.?\d+(?:e[-+]?\d+)?", re.I)
EPS = {"opacity": 0.003, "translateX": 0.25, "translateY": 0.25, "scale": 0.002, "scaleX": 0.002, "scaleY": 0.002,
       "rotate": 0.1, "clip-path": 0.15, "blur": 0.05}
PRIORITY = ("translateY", "translateX", "scale", "scaleX", "scaleY", "rotate", "clip-path", "opacity", "blur")
SCALE = {"translateX": 100.0, "translateY": 100.0, "scale": 0.2, "scaleX": 0.2, "scaleY": 0.2, "rotate": 45.0, "opacity": 1.0,
         "clip-path": 100.0, "blur": 10.0}            # «заметный» размах свойства — для выбора главного у скраба
UNITS = {"translateX": "px", "translateY": "px", "rotate": "deg", "blur": "px", "clip-path": "", "opacity": "", "scale": ""}


def parse_transform(s):
    """Вычисленный transform → (tx, ty, sx, sy, поворот в градусах); 3D — по столбцам matrix3d, перспектива не учитывается."""
    if not s or s == "none":
        return 0.0, 0.0, 1.0, 1.0, 0.0
    m = re.match(r"matrix3d\(([^)]+)\)", s)
    if m:
        v = [float(x) for x in m.group(1).split(",")]
        if len(v) == 16:
            return v[12], v[13], math.hypot(v[0], v[1], v[2]), math.hypot(v[4], v[5], v[6]), math.degrees(math.atan2(v[1], v[0]))
    m = re.match(r"matrix\(([^)]+)\)", s)
    if m:
        v = [float(x) for x in m.group(1).split(",")]
        if len(v) == 6:
            a_, b_, c_, d_, e_, f_ = v
            sx = math.hypot(a_, b_)
            sy = (a_ * d_ - b_ * c_) / sx if sx > 1e-9 else math.hypot(c_, d_)
            return e_, f_, sx, sy, math.degrees(math.atan2(b_, a_))
    return 0.0, 0.0, 1.0, 1.0, 0.0


def parse_individual(s):
    """Свойства translate | scale | rotate (вычисленные) → (tx, ty, s, поворот); проценты translate не учитываются."""
    tx = ty = rot = 0.0
    sc = 1.0
    try:
        tr, scl, ro = (s.split("|") + ["", "", ""])[:3]
        if tr and tr != "none":
            px = [float(x) for x in re.findall(r"(-?[\d.]+)px", tr)]
            tx = px[0] if px else 0.0
            ty = px[1] if len(px) > 1 else 0.0
        if scl and scl != "none":
            sc = float(_NUM.findall(scl)[0])
        if ro and ro != "none":
            d = re.findall(r"(-?[\d.]+)deg", ro)
            rot = float(d[-1]) if d else 0.0
    except (ValueError, IndexError):
        pass
    return tx, ty, sc, rot


def sample_props(s):
    """Отсчёт [t, y, opacity, transform, clip-path, filter, переменные, translate|scale|rotate] → {свойство: число}."""
    out = {}
    try:
        out["opacity"] = float(s[2])
    except (TypeError, ValueError):
        out["opacity"] = 1.0
    tx, ty, sx, sy, rot = parse_transform(s[3])
    if len(s) > 7 and s[7]:
        dtx, dty, dsc, drot = parse_individual(s[7])
        tx, ty, sx, sy, rot = tx + dtx, ty + dty, sx * dsc, sy * dsc, rot + drot
    out["translateX"], out["translateY"], out["rotate"] = tx, ty, rot
    if abs(sx - sy) < 1e-3:
        out["scale"] = sx
    else:
        out["scaleX"], out["scaleY"] = sx, sy
    clip = s[4] if len(s) > 4 else "none"
    if clip and clip != "none":
        out["_clip"] = tuple(float(x) for x in _NUM.findall(clip.split("(", 1)[-1]))
        out["_clip_css"] = clip
    flt = s[5] if len(s) > 5 else "none"
    if flt and flt != "none":
        m = re.search(r"blur\((-?[\d.]+)px\)", flt)
        if m:
            out["blur"] = float(m.group(1))
        out["_filter_css"] = flt
    if len(s) > 6 and s[6]:
        for part in str(s[6]).split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                n = _NUM.findall(v)
                if n:
                    out[k.strip()] = float(n[0])
    return out


def element_series(samples):
    """Отсчёты элемента → время, прокрутка и ряды свойств (без пропусков: недостающее значение — предыдущее)."""
    ss = sorted(samples, key=lambda s: s[0])
    T = np.array([float(s[0]) for s in ss])
    Y = np.array([float(s[1]) for s in ss])
    props = [sample_props(s) for s in ss]
    keys = sorted({k for p in props for k in p if not k.startswith("_")})
    series = {}
    for k in keys:
        last = next((p[k] for p in props if k in p), 0.0)
        col = []
        for p in props:
            last = p.get(k, last)
            col.append(last)
        series[k] = np.array(col, dtype=float)
    clips = [p.get("_clip") for p in props]
    if any(clips):
        n = max(len(c) for c in clips if c)
        mat = np.array([(list(c) + [0.0] * n)[:n] if c else [0.0] * n for c in clips], dtype=float)
        j = int(np.argmax(np.ptp(mat, axis=0))) if len(mat) else 0
        series["clip-path"] = mat[:, j]
    css = {"clip-path": [p.get("_clip_css") for p in props], "filter": [p.get("_filter_css") for p in props]}
    return T, Y, series, css


def _eps(k, col):
    if k in EPS:
        return EPS[k]
    rng = float(np.ptp(col)) if len(col) else 0.0
    return max(1e-4, 0.002 * rng)


def change_mask(series):
    """Изменился ли элемент между соседними отсчётами. Отсчёт пишется только при смене вычисленного значения, поэтому
    граница — любое изменение, а не порог: у кривых out хвост меняется на тысячные доли, и порог срезал бы конец."""
    n = len(next(iter(series.values()))) if series else 0
    m = np.zeros(max(0, n - 1), dtype=bool)
    for col in series.values():
        if len(col) > 1:
            m |= np.abs(np.diff(col)) > 1e-9
    return m


def runs_of(T, mask, gap=GAP_MS):
    """Отрезки движения: индексы отсчётов-изменений (i — отсчёт после изменения), соседние — ближе gap мс."""
    idx = [i + 1 for i, ch in enumerate(mask) if ch]
    runs, cur = [], []
    for i in idx:
        if cur and T[i] - T[cur[-1]] > gap:
            runs.append(cur)
            cur = []
        cur.append(i)
    if cur:
        runs.append(cur)
    return runs


def main_props(series, i0, i1):
    """Свойства, изменившиеся на отрезке [i0−1, i1], в порядке приоритета (сдвиг и масштаб — раньше прозрачности)."""
    out = []
    for k in list(PRIORITY) + sorted(x for x in series if x.startswith("--")):
        col = series.get(k)
        if col is None:
            continue
        seg = col[max(0, i0 - 1): i1 + 1]
        if len(seg) > 1 and float(np.ptp(seg)) > 4 * _eps(k, col):
            out.append(k)
    return out


def wheel_of(t, wheels, window=WHEEL_WINDOW):
    """Ближайший предшествующий шаг колеса, после которого отрезок начался в окне window (мс), или None."""
    best = None
    for w in wheels:
        dt = t - w["t"]
        if window[0] <= dt <= window[1] and (best is None or dt < t - best["t"]):
            best = w
    return best


def scroll_at(t, scroll):
    """Прокрутка в момент t по записи кадров [(t, y)]."""
    if not scroll:
        return 0.0
    ts = [s[0] for s in scroll]
    i = int(np.searchsorted(ts, t, side="right")) - 1
    return float(scroll[max(0, i)][1])


FIRST_FRAME = 1.25            # первый кадр аниматора на rAF пишется не позже следующего кадра после старта (в кадрах)


def time_fit(T, col, i0, i1, base_known, frame):
    """Кривая и тайминг отрезка по времени. Исходное значение известно, если перед отрезком был отсчёт покоя; иначе
    первый отсчёт — первый кадр движения, старт — не раньше FIRST_FRAME кадра до него, исходное подбирается."""
    if base_known:
        xs, vs, v0 = T[i0: i1 + 1], col[i0: i1 + 1], float(col[i0 - 1])
        s_lo, s_hi = float(T[i0 - 1]), float(T[i0])
    else:
        xs, vs, v0 = T[i0 - 1: i1 + 1], col[i0 - 1: i1 + 1], None
        s_lo, s_hi = float(T[i0 - 1] - FIRST_FRAME * frame), float(T[i0 - 1])
    e_lo, e_hi = (float(T[i1 - 1]), float(T[i1])) if i1 - 1 >= i0 else (float(T[i1] - frame), float(T[i1]))
    # отсчёт удержания сразу за последним изменением: аниматор ещё писал то же (округлённое) значение — конец мог быть
    # позже последнего видимого изменения, но не позже удержания и не дальше двух кадров
    if i1 + 1 < len(T) and abs(float(col[i1 + 1]) - float(col[i1])) <= 1e-9:
        e_hi = float(min(T[i1 + 1], T[i1] + 2.0 * frame))
    if len(xs) < 3:
        return None
    return fit_curve(xs, vs, s_lo, s_hi, e_lo, e_hi, v0=v0)


def loop_info(T, col):
    """Петля: период (развороты или сбросы), скорость дорожки (px/с), размах."""
    if len(col) < 8:
        return None
    d = np.diff(col)
    dt = np.diff(T)
    med = float(np.median(np.abs(d))) or 1e-9
    rng = float(np.ptp(col))
    jumps = np.where((np.abs(d) > 5 * med) & (np.abs(d) > 0.2 * rng))[0]
    out = {"amplitude": round(rng, 2)}
    if len(jumps) >= 2:                              # равномерно со сбросом: бегущая строка, вращение по кругу
        per = np.diff(T[jumps])
        out["period_ms"] = round(float(np.median(per)), 1)
        keep = np.ones(len(d), dtype=bool)
        keep[jumps] = False
        v = d[keep] / np.where(dt[keep] > 0, dt[keep], 1.0) * 1000.0
        out["speed_px_s"] = round(abs(float(np.median(v))), 1) if len(v) else None
        out["kind"] = "cycle"
        return out
    c = col - float(np.mean(col))
    zc = np.where(np.diff(np.signbit(c)))[0]
    if len(zc) >= 2:
        out["period_ms"] = round(2.0 * float(np.median(np.diff(T[zc]))), 1)
        out["kind"] = "oscillation"
        return out
    v = d / np.where(dt > 0, dt, 1.0) * 1000.0               # ровное движение в одну сторону (вращение, дрейф)
    out["kind"] = "drift"
    out["speed_px_s"] = round(abs(float(np.median(v))), 2)
    return out


def settled_steps(T, series, runs, wheels):
    """На скольких шагах колеса значение в конце паузы отличается от предыдущего: у скраба со сглаживанием догон
    длиннее паузы, отрезки сливаются, но значения в конце пауз идут за прокруткой."""
    if len(wheels) < 2 or not runs:
        return 0
    props = main_props(series, runs[0][0], runs[-1][-1])
    if not props:
        return 0
    col = series[props[0]]
    eps = 4 * _eps(props[0], col)
    vals = []
    for t_end in [w["t"] for w in wheels] + [float(T[-1]) + 1.0]:
        j = int(np.searchsorted(T, t_end, side="right")) - 1
        vals.append(float(col[j]) if j >= 0 else float(col[0]))
    return int(np.sum(np.abs(np.diff(vals)) > eps))


def idle_windows(wheels, scroll, t_end):
    """Окна покоя прокрутки: последние 1,2 с до первого шага и от успокоения каждого шага (+200 мс) до следующего."""
    out = []
    if wheels:
        out.append((wheels[0]["t"] - 1200.0, wheels[0]["t"] - 30.0))
    for i, w in enumerate(wheels):
        nxt = wheels[i + 1]["t"] if i + 1 < len(wheels) else t_end
        ts = [x[0] for x in scroll if w["t"] <= x[0] < nxt]
        out.append(((max(ts) if ts else w["t"]) + 200.0, nxt - 30.0))
    return [(a, b) for a, b in out if b - a >= 800]


def keeps_moving(T, col, windows):
    """В скольких окнах покоя значение меняется и в конце окна не медленнее, чем в начале (суммарное изменение за
    400 мс): петля по времени идёт ровно, догон скраба после остановки прокрутки затухает."""
    n = 0
    for a, b in windows:
        def tv(lo, hi):
            m = (T >= lo) & (T <= hi)
            seg = col[m]
            return float(np.sum(np.abs(np.diff(seg)))) if len(seg) > 1 else 0.0
        early, late = tv(a, a + 400.0), tv(b - 400.0, b)
        if late > 1e-6 and late >= 0.5 * early:
            n += 1
    return n


def _direction_changes(col, eps):
    d = np.diff(col)
    d = d[np.abs(d) > eps]
    return int(np.sum(np.diff(np.sign(d)) != 0)) if len(d) > 1 else 0


def analyze_elements(raw, frame):
    """Инлайн-стили по элементам → наблюдаемые моменты: one-shot (с кривой), scroll-linked (диапазон, линейность,
    догон), loop (период, скорость), set (мгновенная установка, в паспорт не идёт)."""
    wheels, scroll = raw.get("wheels") or [], raw.get("scroll") or []
    t_first_wheel = wheels[0]["t"] if wheels else float("inf")
    out = []
    for key, ss in (raw.get("samples") or {}).items():
        desc = (raw.get("els") or {}).get(key) or {}
        if len(ss) < 2:
            continue
        T, Y, series, css = element_series(ss)
        if not series:
            continue
        mask = change_mask(series)
        runs = runs_of(T, mask)
        if not runs:
            continue
        el = {"i": int(key), "desc": desc}
        # петля: непрерывное движение дольше LOOP_MS с разворотами или сбросами — или ровное движение в паузах прокрутки
        longest = max(runs, key=lambda r: T[r[-1]] - T[r[0]])
        span = T[longest[-1]] - T[longest[0]]
        props_all = main_props(series, runs[0][0], runs[-1][-1])
        if span >= LOOP_MS and props_all:
            props_all.sort(key=lambda q: -float(np.ptp(series[q])) / SCALE.get(q, max(1e-9, float(np.ptp(series[q])))))
            q0 = props_all[0]
            col = series[q0][longest[0] - 1: longest[-1] + 1]
            tt = T[longest[0] - 1: longest[-1] + 1]
            if _direction_changes(col, _eps(q0, series[q0])) >= 2 or keeps_moving(T, series[q0], idle_windows(wheels, scroll, float(T[-1]))) >= 2:
                li = loop_info(tt, col) or {}
                out.append({**el, "class": "loop", "kind": "inline-style", "props": props_all, "t0": float(tt[0]), "t1": float(tt[-1]),
                            "loop": li, "tracks": _tracks(series, css, longest[0], longest[-1], props_all), "n": len(longest)})
                continue
        aligned = [(r, wheel_of(T[r[0]], wheels)) for r in runs]
        steps = {w["k"] for r, w in aligned if w is not None and len(main_props(series, r[0], r[-1])) > 0}
        if len(steps) >= 2 or settled_steps(T, series, runs, wheels) >= 3:
            sl = scroll_linked(T, Y, series, css, runs, aligned, wheels, scroll, desc)
            if sl:
                out.append({**el, **sl})
                # отрезки до первого шага (появление на загрузке) — отдельные моменты
                runs = [r for r in runs if T[r[0]] < t_first_wheel + WHEEL_WINDOW[0]]
            else:
                runs = runs
        for r in runs:
            i0, i1 = r[0], r[-1]
            props = main_props(series, i0, i1)
            if not props:
                continue
            if len(r) < 2 or T[i1] - T[i0] < 1.5 * frame:
                out.append({**el, "class": "set", "props": props, "t0": float(T[i0])})
                continue
            base_known = i0 >= 2 or (i0 == 1 and T[1] - T[0] > GAP_MS)
            fits = {}
            for p in props:
                f = time_fit(T, series[p], i0, i1, base_known, frame)
                if f:
                    fits[p] = f
            if not fits:
                continue
            mainp = next((p for p in props if p in fits), None)
            f = fits[mainp]
            # разовый момент после первого шага — от последнего шага (появление по IntersectionObserver, ScrollTrigger),
            # дальше 3 с от шага — смена состояния по таймеру (слайдер, отложенный показ)
            w = wheel_of(T[i0], wheels, (WHEEL_WINDOW[0], 3000)) if T[i0] >= t_first_wheel + WHEEL_WINDOW[0] else None
            trig = "load" if T[i0] < t_first_wheel + WHEEL_WINDOW[0] else ("in-view" if w else "state")
            out.append({**el, "class": "one-shot", "kind": "inline-style", "props": props, "main": mainp, "fit": f, "fits": fits,
                        "t0": f["s"], "t1": f["e"], "trigger": trig, "wheel": w["k"] if w else None,
                        "wheel_t": w["t"] if w else None, "scroll_y": float(Y[i0]),
                        "tracks": _tracks(series, css, i0, i1, props, fits, base_known), "n": len(r)})
    return out


def _tracks(series, css, i0, i1, props, fits=None, base_known=True):
    tr = []
    for p in props:
        col = series[p]
        f = (fits or {}).get(p)
        v0 = f["v0"] if f else float(col[max(0, i0 - 1)])
        v1 = f["v1"] if f else float(col[i1])
        rec = {"property": p, "from": _r(v0, p), "to": _r(v1, p)}
        if UNITS.get(p):
            rec["unit"] = UNITS[p]
        if p == "clip-path" and css.get("clip-path"):
            a_, b_ = css["clip-path"][max(0, i0 - 1)], css["clip-path"][i1]
            rec.update({"css_from": a_ or "none", "css_to": b_ or "none"})
        if f:
            rec["fit"] = f
        tr.append(rec)
    return tr


def _r(v, p):
    if v is None:
        return None
    if p in ("opacity", "scale", "scaleX", "scaleY"):
        return round(float(v), 3)
    return round(float(v), 1)


def scroll_linked(T, Y, series, css, runs, aligned, wheels, scroll, desc):
    """Скраб или параллакс: значения в конце пауз против прокрутки → диапазон, линейность, догон сглаживания."""
    props = main_props(series, runs[0][0], runs[-1][-1])
    if not props:
        return None
    props.sort(key=lambda q: -float(np.ptp(series[q][max(0, runs[0][0] - 1): runs[-1][-1] + 1])) / SCALE.get(q, max(1e-9, float(np.ptp(series[q])))))
    p = props[0]
    col = series[p]
    # значение и прокрутка в конце каждой паузы (перед следующим шагом) и до первого шага
    marks = [w["t"] for w in wheels] + [float(T[-1]) + 1.0]
    pts = []
    for t_end in marks:
        j = int(np.searchsorted(T, t_end, side="right")) - 1
        if j >= 0:
            pts.append((scroll_at(t_end - 1, scroll), float(col[j])))
    if len(pts) < 3:
        return None
    ys = np.array([q[0] for q in pts])
    vs = np.array([q[1] for q in pts])
    order = np.argsort(ys, kind="stable")
    ys, vs = ys[order], vs[order]
    eps = 4 * _eps(p, col)
    ch = np.where(np.abs(np.diff(vs)) > eps)[0]
    if len(ch) < 2:
        return None
    a0, a1 = int(ch[0]), int(ch[-1]) + 1                # изменения между точками a0 и a1
    # линейность — по внутренним точкам: в крайних значение уже обрезано (до начала и после конца диапазона)
    seg_y, seg_v = (ys[a0 + 1: a1], vs[a0 + 1: a1]) if a1 - a0 >= 3 else (ys[a0: a1 + 1], vs[a0: a1 + 1])
    lin = None
    if len(seg_y) >= 2 and float(np.ptp(seg_y)) > 0:
        A = np.vstack([seg_y, np.ones_like(seg_y)]).T
        coef, *_ = np.linalg.lstsq(A, seg_v, rcond=None)
        pred = A @ coef
        ss_tot = float(np.sum((seg_v - seg_v.mean()) ** 2)) or 1e-12
        r2 = 1.0 - float(np.sum((seg_v - pred) ** 2)) / ss_tot if len(seg_y) >= 3 else None
        lin = {"r2": round(r2, 4) if r2 is not None else None, "slope": float(coef[0]), "b": float(coef[1])}
    start_open, end_open = a0 == 0 and abs(vs[0] - vs[1]) > eps, a1 == len(vs) - 1
    s_lo, s_hi = float(ys[max(0, a0)]), float(ys[min(len(ys) - 1, a0 + 1)])
    e_lo, e_hi = float(ys[max(0, a1 - 1)]), float(ys[a1])
    start, end = s_lo, e_hi
    if lin and abs(lin["slope"]) > 1e-12:
        start = min(max((vs[a0] - lin["b"]) / lin["slope"], s_lo), s_hi)
        end = min(max((vs[a1] - lin["b"]) / lin["slope"], e_lo), e_hi)
    curve = None
    xs_fit, vs_fit = ys[a0 + 1: a1 + 1], vs[a0 + 1: a1 + 1]
    if len(xs_fit) >= 4:
        curve = fit_curve(xs_fit, vs_fit, s_lo, s_hi, e_lo, e_hi, v0=float(vs[a0]))
    # плато внутри диапазона: соседние точки с изменением ≤ 2 % размаха при прокрутке — кадр, где можно остановиться
    total = abs(float(vs[a1] - vs[a0])) or 1e-9
    plats, i = [], a0 + 1
    while i < a1:
        j = i
        while j < a1 and abs(float(vs[j + 1] - vs[j])) <= 0.02 * total and ys[j + 1] - ys[j] > 1:
            j += 1
        if j > i:
            plats.append(float((ys[i] + ys[j]) / 2))
        i = j + 1
    # догон: от успокоения прокрутки после шага до успокоения значения (2 % изменения шага)
    lags = []
    for r, w in aligned:
        if w is None:
            continue
        nxt = next((x["t"] for x in wheels if x["t"] > w["t"]), float(T[-1]) + 1)
        ts_scroll = [s[0] for s in scroll if w["t"] <= s[0] < nxt]
        if not ts_scroll:
            continue
        t_stop = max(ts_scroll)
        seg = [i for i in r if T[i] < nxt]
        if len(seg) < 2:
            continue
        v_end = col[seg[-1]]
        dv = abs(v_end - col[max(0, seg[0] - 1)])
        if dv <= eps:
            continue
        t_set = next((T[i] for i in seg if all(abs(col[j] - v_end) <= 0.02 * dv for j in seg if T[j] >= T[i])), T[seg[-1]])
        lags.append(max(0.0, float(t_set - t_stop)))
    smooth = round(float(np.median(lags)), 0) if lags else None
    w0 = aligned[0][1] if aligned and aligned[0][1] else None
    changes = [(float(ys[i]), float(ys[i + 1])) for i in range(len(ys) - 1) if abs(float(vs[i + 1] - vs[i])) > eps]
    i_a, i_b = max(0, runs[0][0] - 1), runs[-1][-1]

    def track(q):
        seg = series[q][i_a: i_b + 1]
        rec = {"property": q, "from": _r(seg[0], q), "to": _r(seg[-1], q), **({"unit": UNITS[q]} if UNITS.get(q) else {})}
        if float(np.ptp(seg)) > 4 * _eps(q, series[q]) and abs(float(seg[-1] - seg[0])) < 0.5 * float(np.ptp(seg)):
            rec.update({"min": _r(float(np.min(seg)), q), "max": _r(float(np.max(seg)), q)})   # туда и обратно
        return rec
    return {"class": "scroll-linked", "kind": "inline-style", "props": props, "main": p, "trigger": "scroll-scrub",
            "scroll": {"start_px": round(float(start), 1), "end_px": round(float(end), 1), "start_open": bool(start_open), "end_open": bool(end_open),
                       "linearity_r2": lin["r2"] if lin else None, "smoothing_ms": smooth, "points": int(a1 - a0 + 1),
                       "curve": curve},
            "t0": float(T[runs[0][0]]), "wheel": w0["k"] if w0 else None, "plateaus": plats, "changes": changes,
            "tracks": [track(q) for q in props], "n": int(sum(len(r) for r in runs))}


# =====================================================================================================================
# 9. CDP-анимации → моменты
# =====================================================================================================================
def _num_or(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _segment_easing(cdp_src, page_kf):
    """Кривая анимации: у эффекта (переход, WAAPI) или у ключевых кадров (CSS-анимация — одна на все отрезки)."""
    eff = (cdp_src or {}).get("easing") or "linear"
    kfe = [k.get("easing") for k in ((cdp_src or {}).get("keyframesRule") or {}).get("keyframes") or []]
    if not kfe:
        kfe = [k.get("easing") for k in page_kf or [] if k.get("easing")]
    seg = [e for e in kfe[:-1] if e] if len(kfe) > 1 else kfe
    if eff != "linear":
        return eff, False
    if seg and len(set(seg)) == 1:
        return seg[0], False
    if seg:
        return seg[0], True                          # разные кривые по ключевым кадрам — первая, с пометкой
    return eff, False


def view_range(cdp_tl, page, IH):
    """Диапазон анимации на шкале прокрутки в px прокрутки. CDP даёт диапазон шкалы (у view() — cover: от входа
    снизу до выхода сверху); rangeStart/rangeEnd анимации (entry, exit, contain, cover, …, % или px) — из страницы."""
    s0, s1 = _num_or((cdp_tl or {}).get("startOffset")), _num_or((cdp_tl or {}).get("endOffset"))
    if s0 is None or s1 is None:
        return None
    tl = (page or {}).get("tl") or ""
    if "View" in tl or (cdp_tl or {}).get("subjectNodeId"):
        T_ = s0 + IH
        h = max(0.0, s1 - s0 - IH)
        if h <= IH:
            contain = (T_ + h - IH, T_)
        else:
            contain = (T_, T_ + h - IH)
        ranges = {"cover": (s0, s1), "contain": contain, "entry": (s0, contain[0]), "exit": (contain[1], s1),
                  "entry-crossing": (s0, s0 + h), "exit-crossing": (T_, T_ + h)}
    else:
        ranges = {"cover": (s0, s1), "contain": (s0, s1), "entry": (s0, s1), "exit": (s0, s1)}

    def at(rv, default_pct):
        nm, unit, val = "cover", "percent", default_pct
        if isinstance(rv, dict):
            if rv.get("name") and rv["name"] != "normal":
                nm = rv["name"]
            if rv.get("unit") is not None and rv.get("value") is not None:
                unit, val = rv["unit"], float(rv["value"])
        a_, b_ = ranges.get(nm, ranges["cover"])
        if unit == "percent":
            return a_ + val / 100.0 * (b_ - a_)
        if unit == "px":
            return a_ + val
        return a_ + default_pct / 100.0 * (b_ - a_)
    return at((page or {}).get("rs"), 0.0), at((page or {}).get("re"), 100.0)


def _kf_tracks(kf):
    """Свойства ключевых кадров: от первого к последнему значению; числа — где их можно разобрать."""
    if not kf:
        return []
    props = [p for p in kf[0] if p not in ("offset", "easing", "composite", "computedOffset")]
    out = []
    for p in props:
        a_, b_ = kf[0].get(p), kf[-1].get(p)
        css_name = p if p.startswith("--") else re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), p)   # clipPath → clip-path
        rec = {"property": css_name, "from": a_, "to": b_}
        if p == "transform":
            ta, tb = _css_transform_nums(a_), _css_transform_nums(b_)
            if ta is not None and tb is not None and (ta or tb):
                for k in sorted(set(ta) | set(tb)):
                    va, vb = ta.get(k, 1.0 if k.startswith("scale") else 0.0), tb.get(k, 1.0 if k.startswith("scale") else 0.0)
                    if abs(va - vb) > 1e-6:
                        out.append({"property": k, "from": round(va, 3), "to": round(vb, 3), **({"unit": UNITS[k]} if UNITS.get(k) else {})})
                continue
        if p == "opacity":
            rec = {"property": "opacity", "from": _num_or(a_), "to": _num_or(b_)}
        if len(kf) > 2:
            rec["keyframes"] = len(kf)
        out.append(rec)
    return out


def _css_transform_nums(s):
    """transform CSS-функциями (translateY(40px), scale(.9), rotate(10deg), none) → {свойство: число}; matrix — разбором."""
    if s is None:
        return None
    s = str(s).strip()
    if s in ("none", ""):
        return {}
    if s.startswith("matrix"):
        tx, ty, sx, sy, rot = parse_transform(s)
        return {"translateX": tx, "translateY": ty, "scale": sx, "rotate": rot}
    out = {}
    for fn, args in re.findall(r"([a-zA-Z0-9]+)\(([^)]*)\)", s):
        nums = [float(x) for x in _NUM.findall(args)]
        fl = fn.lower()
        if not nums:
            continue
        if fl in ("translatey",):
            out["translateY"] = out.get("translateY", 0.0) + nums[0]
        elif fl in ("translatex",):
            out["translateX"] = out.get("translateX", 0.0) + nums[0]
        elif fl in ("translate", "translate3d"):
            out["translateX"] = out.get("translateX", 0.0) + nums[0]
            if len(nums) > 1:
                out["translateY"] = out.get("translateY", 0.0) + nums[1]
        elif fl in ("scale", "scale3d"):
            out["scale"] = nums[0] if len(nums) == 1 or abs(nums[0] - nums[1]) < 1e-6 else nums[0]
            if len(nums) > 1 and abs(nums[0] - nums[1]) >= 1e-6:
                out["scaleX"], out["scaleY"] = nums[0], nums[1]
                out.pop("scale", None)
        elif fl == "scalex":
            out["scaleX"] = nums[0]
        elif fl == "scaley":
            out["scaleY"] = nums[0]
        elif fl in ("rotate", "rotatez"):
            out["rotate"] = nums[0] * (57.29578 if "rad" in args else 1.0)
        else:
            return None
    return out


def moments_from_cdp(anims, wheels, IH, pointer):
    """События CDP → моменты (до группировки): класс, триггер, дорожки, длительность, задержка, кривая, повторы,
    диапазон прокрутки."""
    out = []
    t_first = min((w["t_doc"] for w in wheels if w.get("t_doc") is not None), default=float("inf"))
    for rec in anims:
        c = rec.get("cdp") or {}
        src = c.get("source") or {}
        pg = rec.get("page") or {}
        desc = pg.get("target") or rec.get("target") or {}
        kind = {"CSSAnimation": "css-animation", "CSSTransition": "css-transition", "WebAnimation": "waapi"}.get(c.get("type"), "waapi")
        if (desc.get("sel") or "").startswith("div#__mp"):
            continue
        dur = _num_or(src.get("duration"))
        delay = _num_or(src.get("delay")) or 0.0
        iters = src.get("iterations")
        tm = pg.get("tm") or {}
        if tm.get("iterations") == "Infinity" or (isinstance(iters, (int, float)) and iters > 1e6) or iters is None and tm.get("iterations") == "Infinity":
            iters = "infinite"
        easing, mixed = _segment_easing(src, pg.get("kf"))
        tracks = _kf_tracks(pg.get("kf"))
        if not tracks and c.get("name"):             # объект анимации уже собран: свойство — из имени перехода
            tracks = [{"property": c["name"] if c.get("type") == "CSSTransition" else f"@keyframes {c['name']}"}]
        tl = c.get("viewOrScrollTimeline")
        m = {"source": "cdp", "kind": kind, "name": c.get("name") or pg.get("name") or "", "desc": desc,
             "tracks": tracks, "easing_css": easing, "easing_mixed": mixed, "cdp_id": rec.get("id"), "pseudo": pg.get("pseudo")}
        if tl:
            rng = view_range(tl, pg, IH)
            m.update({"class": "scroll-linked", "trigger": "scroll-scrub",
                      "scroll": {"start_px": round(rng[0], 1), "end_px": round(rng[1], 1), "timeline": pg.get("tl") or "ScrollTimeline",
                                 "range": [pg.get("rs"), pg.get("re")], "axis": tl.get("axis")} if rng else None})
            out.append(m)
            continue
        if not dur or dur <= 16:
            continue
        st = _num_or(c.get("startTime"))
        t_vis = (st or 0.0) + delay
        if iters == "infinite":
            m.update({"class": "loop", "trigger": "idle-loop", "t0": t_vis, "duration_ms": dur, "delay_declared": delay,
                      "repeat": {"iterations": "infinite", "direction": src.get("direction") or "normal",
                                 "period_ms": round(dur * (2 if str(src.get("direction", "")).startswith("alternate") else 1), 1)}})
            out.append(m)
            continue
        w = None
        if st is not None and st >= t_first + WHEEL_WINDOW[0]:
            cands = [x for x in wheels if x.get("t_doc") is not None and x["t_doc"] - 30 <= st]
            w = cands[-1] if cands else None
        rect = desc.get("rect") or [0, 0, 0, 0]
        x, y = pointer
        if kind == "css-transition" and rect and rect[2] and rect[0] <= x <= rect[0] + rect[2]:
            # переход у элемента под указателем — вероятно наведение; не момент подачи
            top_vp = rect[1] - (w["y1"] if w else 0.0)
            if top_vp <= y <= top_vp + rect[3]:
                continue
        m.update({"class": "one-shot", "trigger": "in-view" if w else "load", "t0": t_vis, "t1": t_vis + dur * (iters if isinstance(iters, (int, float)) and iters >= 1 else 1),
                  "duration_ms": dur, "delay_declared": delay, "wheel": w["k"] if w else None, "wheel_t": w["t_doc"] if w else None,
                  "repeat": {"iterations": iters if isinstance(iters, (int, float)) else 1, "direction": src.get("direction") or "normal"}})
        out.append(m)
    # одна цель, один старт (±20 мс): переходы transform и opacity — один момент с дорожками
    merged, used = [], set()
    for i, m in enumerate(out):
        if i in used:
            continue
        if m["class"] == "one-shot":
            for j in range(i + 1, len(out)):
                n = out[j]
                if j in used or n["class"] != "one-shot" or (n["desc"] or {}).get("path") != (m["desc"] or {}).get("path"):
                    continue
                if abs(n["t0"] - m["t0"]) <= 20 and n["kind"] == m["kind"]:
                    for t in n["tracks"]:
                        t.setdefault("duration_ms", n["duration_ms"])
                        t.setdefault("easing_css", n["easing_css"])
                    for t in m["tracks"]:
                        t.setdefault("duration_ms", m["duration_ms"])
                        t.setdefault("easing_css", m["easing_css"])
                    m["tracks"] += n["tracks"]
                    if n["duration_ms"] > m["duration_ms"]:
                        m["duration_ms"], m["easing_css"], m["t1"] = n["duration_ms"], n["easing_css"], n["t1"]
                    m["name"] = (m["name"] + "+" + n["name"]).strip("+")
                    used.add(j)
        merged.append(m)
    return merged


# =====================================================================================================================
# 10. GSAP, ScrollTrigger, Lenis → моменты, закрепления, станции
# =====================================================================================================================
def _gsap_time_map(g):
    """Связь времени корневой шкалы GSAP (с) со временем страницы (мс): среднее по опросам."""
    gm = [x for x in (g or {}).get("gmap") or [] if isinstance(x, list) and len(x) == 2 and isinstance(x[1], (int, float))]
    if not gm:
        return None
    return float(np.median([t - gt * 1000.0 for t, gt in gm]))


def _ease_of(tw, by_id, defaults):
    e = tw.get("ease")
    p = by_id.get(tw.get("parent"))
    while not e and p:
        e = (((p.get("vars") or {}).get("defaults") or {}) if isinstance((p.get("vars") or {}).get("defaults"), dict) else {}).get("ease")
        p = by_id.get(p.get("parent"))
    if not e and isinstance(defaults, dict):
        e = defaults.get("ease")
    return e if isinstance(e, str) else ("power1.out" if not e else "fn")


def gsap_moments(g, st, IH):
    """Твины GSAP (объявленные числа): один момент на твин; со ScrollTrigger — scroll-linked с диапазоном в px;
    закрепления и станции (snap) — из ScrollTrigger."""
    if not g:
        return [], [], []
    by_id = {t["id"]: t for t in (g.get("tweens") or []) + (g.get("timelines") or [])}
    sts = {s["id"]: s for s in ((st or {}).get("list") or [])}
    off = _gsap_time_map(g)
    defaults = g.get("defaults") if isinstance(g.get("defaults"), dict) else {}
    moments, pins, stations = [], [], []
    st_of_anim = {s.get("anim"): s for s in sts.values() if s.get("anim")}
    for tw in g.get("tweens") or []:
        vars_ = tw.get("vars") or {}
        props = [p for p in tw.get("props") or [] if p not in ("css",)]
        if not props or not tw.get("targets"):
            continue
        if float(tw.get("duration") or 0.0) * 1000.0 <= 16.0:
            continue                                     # gsap.set и твины нулевой длительности — установки, не движение
        n = int(tw.get("n_targets") or len(tw["targets"]))
        stg = vars_.get("stagger")
        each = None
        if isinstance(stg, (int, float)):
            each = float(stg) * 1000.0
        elif isinstance(stg, dict):
            if isinstance(stg.get("each"), (int, float)):
                each = float(stg["each"]) * 1000.0
            elif isinstance(stg.get("amount"), (int, float)) and n > 1:
                each = float(stg["amount"]) * 1000.0 / (n - 1)
        dur_v = vars_.get("duration")
        if isinstance(dur_v, (int, float)):
            dur = float(dur_v) * 1000.0
        else:
            tot = float(tw.get("duration") or 0.0) * 1000.0
            dur = tot - (each or 0.0) * max(0, n - 1) if each else tot
            if dur <= 0:
                dur = float(defaults.get("duration") or 0.5) * 1000.0
        delay = float(vars_["delay"]) * 1000.0 if isinstance(vars_.get("delay"), (int, float)) else float(tw.get("delay") or 0.0) * 1000.0
        ease = _ease_of(tw, by_id, defaults)
        frm = bool(vars_.get("runBackwards"))
        start_at = vars_.get("startAt") if isinstance(vars_.get("startAt"), dict) else None
        tracks = []
        for p in props:
            v = vars_.get(p)
            if start_at is not None:
                tracks.append({"property": p, "from": start_at.get(p), "to": v})
            elif frm:
                tracks.append({"property": p, "from": v, "to": "текущее"})
            else:
                tracks.append({"property": p, "from": "текущее", "to": v})
        stt = sts.get(tw.get("st")) or st_of_anim.get(tw["id"])
        par = by_id.get(tw.get("parent"))
        while not stt and par:
            stt = sts.get(par.get("st")) or st_of_anim.get(par.get("id"))
            par = by_id.get(par.get("parent"))
        loop_parent = None                               # шкала-родитель с repeat: -1 — твин крутится вместе с ней
        par = by_id.get(tw.get("parent"))
        while par:
            if par.get("repeat") == -1:
                loop_parent = par
                break
            par = by_id.get(par.get("parent"))
        desc0 = (tw["targets"][0] or {}).get("d") or {}
        m = {"source": "gsap", "kind": "gsap", "desc": desc0, "targets": tw["targets"], "count": n, "tracks": tracks,
             "duration_ms": round(dur, 1), "delay_declared": round(delay, 1), "ease_declared": ease, "gsap_id": tw["id"],
             "repeat": {"iterations": "infinite" if tw.get("repeat") == -1 else int(tw.get("repeat") or 0) + 1, "yoyo": bool(tw.get("yoyo"))},
             "stagger_declared": ({"each_ms": round(each, 1), "count": n, "from": (stg.get("from") if isinstance(stg, dict) else "start")} if each else None)}
        if stt:
            sc = stt.get("scrub")
            rng = (stt.get("start"), stt.get("end"))
            if stt.get("container"):                     # start/end — в шкале горизонтальной дорожки, не в px прокрутки
                rng = (None, None)
            m.update({"class": "scroll-linked" if sc not in (None, False) else "one-shot",
                      "trigger": ("pin-scrub" if stt.get("pin") else "scroll-scrub") if sc not in (None, False) else "in-view",
                      "scroll": {"start_px": rng[0], "end_px": rng[1], "scrub": sc, "start_text": stt.get("start_str"), "end_text": stt.get("end_str"),
                                 "container": bool(stt.get("container"))},
                      "st_id": stt["id"]})
        elif tw.get("repeat") == -1 or loop_parent:
            per = float(loop_parent.get("duration") or 0.0) * 1000.0 if loop_parent else None
            m.update({"class": "loop", "trigger": "idle-loop"})
            m["repeat"] = {"iterations": "infinite", "yoyo": bool(tw.get("yoyo") or (loop_parent or {}).get("yoyo")),
                           **({"period_ms": round(per, 1)} if per else {})}
        else:
            gs = tw.get("global_start")
            t0 = off + float(gs) * 1000.0 if (off is not None and isinstance(gs, (int, float))) else None
            m.update({"class": "one-shot", "trigger": "load", "t0": t0})
        moments.append(m)
    for s in sts.values():
        if s.get("pin") and not s.get("container") and isinstance(s.get("start"), (int, float)) and isinstance(s.get("end"), (int, float)):
            pins.append({"desc": s["pin"], "start_px": float(s["start"]), "end_px": float(s["end"]), "evidence": "scrolltrigger",
                         "pin_spacing": s.get("pin_spacing"), "pin_type": s.get("pin_type"), "st_id": s["id"]})
        pts = snap_points(s) if not s.get("container") else []
        for p in pts:
            stations.append({"kind": "snap", "progress": round(p, 4),
                             "scroll_px": round(float(s["start"]) + p * (float(s["end"]) - float(s["start"])), 1) if isinstance(s.get("start"), (int, float)) else None,
                             "st_id": s["id"]})
    return moments, pins, stations


def snap_points(s):
    """Точки snap ScrollTrigger в долях прогресса: шаг, список, метки шкалы; функция — не известна до прокрутки."""
    sn = s.get("snap") or {}
    k = sn.get("kind")
    val = sn.get("value") if k == "increment" else (sn.get("snapTo") if k == "object" else None)
    if k == "points":
        val = sn.get("values")
    if isinstance(val, (int, float)) and 0 < val <= 1:
        n = int(round(1.0 / val))
        return [min(1.0, i * val) for i in range(n + 1)]
    if isinstance(val, list):
        return sorted(float(x) for x in val if isinstance(x, (int, float)) and 0 <= x <= 1)
    if (k in ("labels", "labelsDirectional") or val in ("labels", "labelsDirectional")) and s.get("labels"):
        return sorted(float(p) for _, p in s["labels"] if isinstance(p, (int, float)))
    return []


# =====================================================================================================================
# 11. Закрепления по геометрии, станции, плавная прокрутка
# =====================================================================================================================
def detect_pins(cands, snaps, IH):
    """Элементы, чей верх в окне стоит на месте ≥ 2 шагов, пока документ едет: начало и конец — продолжением движения
    вместе с документом до и после стоянки. Стоят все шаги — постоянный слой (шапка, фон), не закрепление."""
    if not cands or len(snaps) < 3:
        return [], []
    ys = np.array([float(s["y"]) for s in snaps])
    K = len(snaps)
    pins, fixed = [], []
    for ci, desc in enumerate(cands):
        vals = [(s["v"][ci] if ci < len(s["v"]) else None) for s in snaps]
        if any(v is None for v in vals):
            continue
        tops = np.array([float(v[0]) for v in vals])
        hs = np.array([float(v[1]) for v in vals])
        pos = [v[2] for v in vals]
        vis = (tops < IH) & (tops + hs > 0) & (hs > 0)
        stuck = []
        for k in range(K - 1):
            dy = ys[k + 1] - ys[k]
            stuck.append(bool(dy >= 8 and abs(tops[k + 1] - tops[k]) <= 1.5 and vis[k] and vis[k + 1]))
        k = 0
        while k < K - 1:
            if not stuck[k]:
                k += 1
                continue
            j = k
            while j < K - 1 and stuck[j]:
                j += 1
            ka, kb = k, j                               # стоит со снимка ka по снимок kb
            if kb - ka >= 2:
                # fixed на всех снимках — постоянный слой (шапка, фон): верх у него двигает разве что своя анимация
                if (ka == 0 and kb == K - 1) or all(x == "f" for x in pos):
                    fixed.append({"desc": desc, "height_vh": round(float(np.median(hs)) / IH * 100, 1), "position": pos[ka]})
                else:
                    top = float(tops[ka])
                    start = float(ys[ka])
                    if ka > 0:
                        moved, dy0 = float(tops[ka - 1] - top), float(ys[ka] - ys[ka - 1])
                        if 0 <= moved <= dy0 + 1:
                            start = float(ys[ka - 1]) + moved
                    end = float(ys[kb])
                    end_open = kb == K - 1
                    if not end_open:
                        moved, dy1 = float(top - tops[kb + 1]), float(ys[kb + 1] - ys[kb])
                        if 0 <= moved <= dy1 + 1:
                            end = float(ys[kb + 1]) - moved
                    mid = (ka + kb) // 2
                    mech = {"k": "sticky", "f": "fixed"}.get(pos[mid], "transform")
                    pins.append({"desc": desc, "start_px": round(start, 1), "end_px": round(end, 1), "top_px": round(top, 1),
                                 "end_open": end_open, "start_open": ka == 0, "mechanism": mech,
                                 "height_vh": round(float(hs[mid]) / IH * 100, 1), "evidence": "geometry", "ci": ci})
            k = j
    # вложенные элементы одной стоянки — одно закрепление (внешний элемент)
    pins.sort(key=lambda p: (p["start_px"], (p["desc"] or {}).get("depth") or 0))
    keep = []
    for p in pins:
        dup = None
        for q in keep:
            inter = min(p["end_px"], q["end_px"]) - max(p["start_px"], q["start_px"])
            union = max(p["end_px"], q["end_px"]) - min(p["start_px"], q["start_px"])
            if union > 0 and inter / union >= 0.8:
                dup = q
                break
        if dup is None:
            p["inner"] = 0
            keep.append(p)
        else:
            dup["inner"] = dup.get("inner", 0) + 1
            if ((p["desc"] or {}).get("depth") or 99) < ((dup["desc"] or {}).get("depth") or 99):
                p["inner"] = dup["inner"]
                keep[keep.index(dup)] = p
    fx, seen = [], set()
    for f in fixed:
        s = (f["desc"] or {}).get("sel")
        if s not in seen:
            seen.add(s)
            fx.append(f)
    return keep, fx[:12]


def merge_pins(geo, stp, IH):
    out = []
    used = set()
    for p in stp:
        best, bj = 0.0, None
        for j, q in enumerate(geo):
            inter = min(p["end_px"], q["end_px"]) - max(p["start_px"], q["start_px"])
            union = max(p["end_px"], q["end_px"]) - min(p["start_px"], q["start_px"])
            if union > 0 and inter / union > best:
                best, bj = inter / union, j
        rec = dict(p)
        if bj is not None and best >= 0.5:
            used.add(bj)
            q = geo[bj]
            rec.update({"evidence": "geometry+scrolltrigger", "mechanism": q["mechanism"], "top_px": q["top_px"], "height_vh": q["height_vh"],
                        "geometry": {"start_px": q["start_px"], "end_px": q["end_px"]}})
        else:
            rec.setdefault("mechanism", "transform" if p.get("pin_type") == "transform" else "fixed")
        out.append(rec)
    out += [q for j, q in enumerate(geo) if j not in used]
    for p in out:
        p["length_px"] = round(p["end_px"] - p["start_px"], 1)
        p["length_vh"] = round(p["length_px"] / IH * 100.0, 1)
    out.sort(key=lambda p: p["start_px"])
    return out


def smooth_scroll(libs, wheels, scroll, IH):
    """Плавная прокрутка: что за механизм, опции, хвост после шага колеса (мс), оценка lerp по затуханию хвоста."""
    libs = libs or {}
    kind = "native"
    if libs.get("lenis") or libs.get("lenis_smooth"):
        kind = "lenis"
    elif libs.get("smoother"):
        kind = "scrollsmoother"
    elif libs.get("locomotive"):
        kind = "locomotive"
    tails, lerps = [], []
    sc = [(float(t), float(y)) for t, y in scroll]
    for i, w in enumerate(wheels):
        nxt = wheels[i + 1]["t"] if i + 1 < len(wheels) else float("inf")
        seg = [(t, y) for t, y in sc if w["t"] <= t < nxt]
        if not seg:
            continue
        t_last = seg[-1][0]
        tails.append(t_last - w["t"])
        y_end = seg[-1][1]
        d = [(t, abs(y_end - y)) for t, y in seg[:-1] if abs(y_end - y) > 0.5]
        if len(d) >= 8:
            tt = np.array([x[0] for x in d]) / 1000.0
            ll = np.log(np.array([x[1] for x in d]))
            k_, _b = np.polyfit(tt, ll, 1)
            if k_ < 0:
                lerps.append(-k_ / 60.0)
    out = {"kind": kind}
    if libs.get("lenis"):
        out["options"] = (libs["lenis"] or {}).get("options")
        out["global"] = (libs["lenis"] or {}).get("global")
    if libs.get("smoother"):
        out["options"] = libs["smoother"]
    if libs.get("scroll_behavior") == "smooth":
        out["css_scroll_behavior"] = "smooth"
    if tails:
        out["tail_ms"] = {"median": round(float(np.median(tails)), 0), "max": round(float(np.max(tails)), 0), "steps": len(tails)}
        if kind == "native" and np.median(tails) >= 300:
            out["kind"] = "smooth-unknown"
    if lerps and out["kind"] in ("lenis", "smooth-unknown"):
        out["lerp_est"] = round(float(np.median(lerps)), 3)
    return out


# =====================================================================================================================
# 12. Сборка паспорта
# =====================================================================================================================
def _slug(s, n=28):
    s = re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")
    return (s[:n].strip("-") or "el")


def _el_slug(desc, fallback="anim", n=24):
    """Часть id момента или закрепления: тег и id элемента или первый класс подписи («h1-hero-title»)."""
    d = desc or {}
    if not d.get("tag"):
        return _slug(fallback, n)
    sel = d.get("sel") or ""
    ident = sel.split("#", 1)[1].split(".")[0] if "#" in sel else ""
    sig = d.get("sig") or ""
    cls = sig.split(".")[1] if "." in sig else ""
    return _slug(d["tag"] + "-" + (ident or cls), n)


def _logical(desc):
    d = (desc or {}).get("data") or {}
    sec = d.get("section")
    x = d.get("slot") or d.get("group") or (("fx-" + d["fx"]) if d.get("fx") else None)
    return f"{sec}.{x}" if sec and x else (sec or None)


def _target(desc, count=1, members=None):
    d = desc or {}
    out = {"selector": d.get("sel") or "", "path": d.get("path") or "", "tag": d.get("tag") or "", "text": d.get("text") or "",
           "rect": d.get("rect"), "count": int(count)}
    data = {k: v for k, v in (d.get("data") or {}).items() if v}
    if data:
        out["data"] = data
    lg = _logical(d)
    if lg:
        out["logical"] = lg
    if members:
        out["members"] = members[:12]
    return out


def _easing_block(fit=None, css=None, declared=None):
    """Кривая момента: подбор (именованная, bezier, ошибки), CSS-строка, объявленная, ближайший токен."""
    e = {}
    f = None
    if fit:
        e.update({"named": fit["named"], "named_error": fit["named_error"], "bezier": fit["bezier"], "bezier_error": fit["bezier_error"]})
        e["css"] = css_bezier(fit["bezier"])
        f = _bz(fit["bezier"])
        if fit["named"] in CSS_KEYWORDS and fit["named_error"] <= fit["bezier_error"] + 0.002:
            # ключевое слово CSS объясняет движение не хуже подбора — пишется словом (у линейного скраба bezier вырожден)
            e.update({"css": fit["named"], "bezier": list(CSS_KEYWORDS[fit["named"]])})
            f = NAMED[fit["named"]]
    if css:
        e["css"] = css
        f = ease_fn(css) or f
        if f is not None and "named" not in e:
            nn = nearest_named(f)
            e.update({"named": nn[0], "named_error": round(nn[1], 4)})
    if declared:
        e["declared"] = declared
        fd = ease_fn(declared)
        if fd is not None:
            f = fd if not fit else f
            if "css" not in e:
                bz = BEZIER_OF.get(declared) or BEZIER_OF.get(_canon_ease(declared))
                if bz:
                    e["css"] = css_bezier(bz)
            if "named" not in e:
                nn = nearest_named(fd)
                e.update({"named": nn[0], "named_error": round(nn[1], 4)})
    tok = nearest_token_easing(f)
    if tok:
        e["token"] = tok
    return e or None


def _canon_ease(s):
    m = re.match(r"([a-z]+\d?)(?:\.(in|out|inOut))?", str(s), re.I)
    if not m:
        return s
    base = GSAP_ALIAS.get(m.group(1).lower(), m.group(1).lower())
    return "linear" if base == "linear" else f"{base}.{m.group(2) or 'out'}"


def group_stagger(ms):
    """Соседи с одним триггером, одним набором свойств, близкой длительностью и кривой → один момент со стаггером."""
    groups, used = [], set()
    for i, m in enumerate(ms):
        if i in used or m.get("class") != "one-shot" or m.get("count", 1) > 1 or m.get("kind") == "gsap":
            continue
        g = [i]
        for j in range(i + 1, len(ms)):
            n = ms[j]
            if j in used or n.get("class") != "one-shot" or n.get("count", 1) > 1 or n.get("kind") != m.get("kind"):
                continue
            if n.get("trigger") != m.get("trigger") or n.get("wheel") != m.get("wheel"):
                continue
            if sorted(t["property"] for t in n["tracks"]) != sorted(t["property"] for t in m["tracks"]):
                continue
            da, db = m.get("duration_ms") or 0, n.get("duration_ms") or 0
            if not da or not db or abs(da - db) / max(da, db) > 0.15:
                continue
            ma, mb = m.get("desc") or {}, n.get("desc") or {}
            if ma.get("parent") != mb.get("parent") and ma.get("sig") != mb.get("sig"):
                continue
            fa, fb = _curve_of_moment(m), _curve_of_moment(n)
            if fa is not None and fb is not None and curve_distance(fa, fb) > 0.06:
                continue
            g.append(j)
        if len(g) >= 2:
            used.update(g)
            groups.append(g)
    out = []
    grouped = {j for g in groups for j in g}
    for g in groups:
        mem = sorted((ms[j] for j in g), key=lambda m: m.get("t0") or 0)
        starts = [m.get("t0") or 0 for m in mem]
        steps = np.diff(starts)
        each = float(np.median(steps)) if len(steps) else 0.0
        if len(steps) and 5 < each <= 400 and (np.max(np.abs(steps - each)) <= max(14.0, 0.3 * each)):
            pass
        elif len(steps) and each <= 5:
            each = 0.0
        else:
            out.extend(mem)                          # шаг неровный — не стаггер, моменты по отдельности
            continue
        dom = [((m.get("desc") or {}).get("rect") or [0, 0])[:2] for m in mem]
        order = "dom"
        if len(dom) > 1:
            ys_ = [(r[1], r[0]) for r in dom]
            if ys_ == sorted(ys_):
                order = "dom"
            elif ys_ == sorted(ys_, reverse=True):
                order = "reverse"
            else:
                order = "random"
        head = dict(mem[0])
        head["count"] = len(mem)
        head["members"] = [(m.get("desc") or {}).get("sel") for m in mem]
        if each > 0:
            head["stagger"] = {"each_ms": round(each, 1), "count": len(mem), "order": order, "total_ms": round(each * (len(mem) - 1), 1)}
        durs = [m.get("duration_ms") for m in mem if m.get("duration_ms")]
        head["duration_ms"] = round(float(np.median(durs)), 1) if durs else head.get("duration_ms")
        out.append(head)
    out.extend(m for i, m in enumerate(ms) if i not in grouped)
    return out


def group_scroll(ms):
    """Одинаковые скрабы соседей (те же свойства, длина ±15 %, тот же догон, одна подпись или родитель) → один момент: число
    элементов и шаг начала диапазонов в px (карточки сетки с view() — ряд за рядом)."""
    out, used = [], set()
    for i, m in enumerate(ms):
        if i in used or m.get("class") != "scroll-linked" or m.get("kind") == "gsap":
            continue
        sc = m.get("scroll") or {}
        if not isinstance(sc.get("start_px"), (int, float)) or not isinstance(sc.get("end_px"), (int, float)):
            continue
        L = sc["end_px"] - sc["start_px"]
        g = [i]
        for j in range(i + 1, len(ms)):
            n = ms[j]
            sn = n.get("scroll") or {}
            if j in used or n.get("class") != "scroll-linked" or n.get("kind") != m.get("kind"):
                continue
            if not isinstance(sn.get("start_px"), (int, float)) or not isinstance(sn.get("end_px"), (int, float)):
                continue
            if sorted(t["property"] for t in n["tracks"]) != sorted(t["property"] for t in m["tracks"]):
                continue
            Ln = sn["end_px"] - sn["start_px"]
            if max(L, Ln) <= 0 or abs(L - Ln) / max(L, Ln) > 0.15:
                continue
            sa, sb = float(sc.get("smoothing_ms") or 0.0), float(sn.get("smoothing_ms") or 0.0)
            if abs(sa - sb) > max(60.0, 0.3 * max(sa, sb)):
                continue                                 # разный догон — разные скрабы, хоть и соседи
            ma, mb = m.get("desc") or {}, n.get("desc") or {}
            if ma.get("parent") != mb.get("parent") and ma.get("sig") != mb.get("sig"):
                continue
            g.append(j)
        if len(g) >= 2:
            used.update(g)
            mem = sorted((ms[j] for j in g), key=lambda x: x["scroll"]["start_px"])
            starts = sorted({round(x["scroll"]["start_px"], 1) for x in mem})
            head = dict(mem[0])
            head["count"] = len(mem)
            head["members"] = [(x.get("desc") or {}).get("sel") for x in mem]
            st = np.diff(starts)
            head["stagger"] = {"count": len(mem), "order": "dom", **({"each_px": round(float(np.median(st)), 1)} if len(st) else {}),
                               "rows": len(starts)}
            out.append(head)
    return out + [m for i, m in enumerate(ms) if i not in used]


def _curve_of_moment(m):
    if m.get("fit"):
        return _bz(m["fit"]["bezier"])
    if m.get("easing_css"):
        return ease_fn(m["easing_css"])
    if m.get("ease_declared"):
        return ease_fn(m["ease_declared"])
    return None


def _merge_gsap_observed(gm, obs):
    """Твин GSAP и наблюдённые траектории его целей: подтверждение длительности и кривой, одна запись на твин."""
    by_el = {}
    for o in obs:
        by_el.setdefault(o["i"], []).append(o)
    used = set()
    for m in gm:
        idx = [t.get("i") for t in m.get("targets") or [] if isinstance(t, dict) and t.get("i") is not None]
        cand = [o for i in idx for o in by_el.get(i, []) if o.get("class") == m.get("class")]
        if m.get("class") == "one-shot":
            # у цели бывает несколько твинов подряд (шкала карусели): отрезок — свой, если начался у начала твина
            # (±150 мс), а при неизвестном начале — если длительность в пределах ±35 %
            d0 = float(m.get("duration_ms") or 0.0)

            def mine(o):
                if m.get("t0") is not None and o.get("t0") is not None:
                    return abs(float(o["t0"]) - float(m["t0"]) - float(m.get("delay_declared") or 0.0)) <= 150.0 or \
                        abs(float(o["t0"]) - float(m["t0"])) <= 150.0
                return d0 > 0 and 0.65 <= (float(o.get("t1", 0.0)) - float(o.get("t0", 0.0))) / d0 <= 1.35
            cand = [o for o in cand if mine(o)]
        if not cand:
            continue
        first = min(cand, key=lambda o: o.get("t0") or 0)
        if first.get("class") == "one-shot" and first.get("fit"):
            m["observed"] = {"duration_ms": round(first["t1"] - first["t0"], 1), "easing": first["fit"]["named"],
                             "bezier": first["fit"]["bezier"], "bezier_error": first["fit"]["bezier_error"]}
            if m.get("t0") is None:
                m["t0"] = first.get("t0")
            if m.get("trigger") == "load" and first.get("trigger") == "in-view":
                m["trigger"], m["wheel"], m["wheel_t"] = "in-view", first.get("wheel"), first.get("wheel_t")
            obs_starts = sorted(o.get("t0") or 0 for o in cand if o.get("class") == "one-shot")
            if len(obs_starts) >= 2:
                m["observed"]["stagger_each_ms"] = round(float(np.median(np.diff(obs_starts))), 1)
        elif first.get("class") == "scroll-linked":
            m["observed"] = {"scroll": first.get("scroll")}
        for o in cand:
            used.add(id(o))
    return [o for o in obs if id(o) not in used]


def build_moments(raw, frame, IH):
    obs = analyze_elements(raw, frame)
    cdp = moments_from_cdp(raw.get("anims") or [], raw.get("wheels") or [], IH,
                           ((raw.get("nav") or {}).get("IW", 1440) - 3, IH / 2))
    gm, st_pins, st_stations = gsap_moments(raw.get("gsap"), raw.get("st"), IH)
    wheels = raw.get("wheels") or []
    for m in gm:                                      # твин, запущенный после первого шага (код сайта без ScrollTrigger), — от шага
        if m.get("trigger") == "load" and m.get("t0") is not None and wheels and m["t0"] >= wheels[0]["t"] - 30:
            w = max((x for x in wheels if x["t"] <= m["t0"] + 30), key=lambda x: x["t"], default=None)
            if w:
                m.update({"trigger": "in-view" if m["t0"] - w["t"] <= 3000 else "state", "wheel": w["k"], "wheel_t": w["t"]})
    obs = _merge_gsap_observed(gm, obs)
    sets = [o for o in obs if o.get("class") == "set"]
    obs = [o for o in obs if o.get("class") != "set"]
    for o in obs:
        if o.get("class") == "one-shot":
            o["duration_ms"] = round(o["t1"] - o["t0"], 1)
    allm = obs + cdp + gm
    allm = group_scroll(group_stagger(allm))
    return allm, st_pins, st_stations, len(sets)


def finalize_moments(allm, wheels, IH):
    """Порядок, id, триггер и задержка от триггера, поля паспорта."""
    load = [m for m in allm if m.get("class") == "one-shot" and m.get("trigger") == "load" and m.get("t0") is not None]
    t_scene = min((m["t0"] for m in load), default=None)
    rank = {"load": 0, "in-view": 1, "scroll-scrub": 2, "pin-scrub": 2, "idle-loop": 3}

    def key(m):
        sc = (m.get("scroll") or {}).get("start_px")
        return (rank.get(m.get("trigger"), 4), m.get("t0") if m.get("t0") is not None else 1e12,
                sc if isinstance(sc, (int, float)) else 1e12)
    allm.sort(key=key)
    out = []
    for n, m in enumerate(allm, 1):
        desc = m.get("desc") or {}
        mid = f"m{n:02d}-" + _el_slug(desc, m.get("name") or "anim")
        trig = {"type": m.get("trigger") or "unknown"}
        if m.get("wheel"):
            trig["step"] = m["wheel"]
        delay = None
        if m.get("class") == "one-shot" and m.get("t0") is not None:
            if m.get("trigger") == "load" and t_scene is not None:
                delay = m["t0"] - t_scene
            elif m.get("trigger") == "in-view" and m.get("wheel_t") is not None:
                delay = m["t0"] - m["wheel_t"]
        if m.get("scroll_y") is not None:
            trig["scroll_y"] = round(m["scroll_y"], 1)
        sc = m.get("scroll")
        if sc and isinstance(sc.get("start_text"), str):
            trig["start"] = sc.get("start_text")
            trig["end"] = sc.get("end_text")
        rec = {"id": mid, "class": m.get("class"), "kind": m.get("kind"),
               "evidence": "declared+measured" if (m.get("source") in ("gsap", "cdp") and m.get("observed")) else
                           ("declared" if m.get("source") in ("gsap", "cdp") else "measured"),
               "trigger": trig, "target": _target(desc, m.get("count", 1), m.get("members"))}
        tr = []
        for t in m.get("tracks") or []:
            x = {k: v for k, v in t.items() if k not in ("fit", "easing_css")}
            if t.get("fit"):
                f = t["fit"]
                x["duration_ms"] = round(f["e"] - f["s"], 1)
                if m.get("t0") is not None:
                    x["delay_ms"] = round(max(0.0, f["s"] - m["t0"]), 1)
                x["easing"] = _easing_block(fit=f)
            elif t.get("easing_css"):
                x["easing"] = _easing_block(css=t["easing_css"])
            tr.append(x)
        rec["tracks"] = tr
        if m.get("t0") is not None:
            rec["t_ms"] = round(float(m["t0"]), 1)
        if m.get("duration_ms") is not None and m.get("class") in ("one-shot", "loop"):
            rec["duration_ms"] = round(float(m["duration_ms"]), 1)
            tk = nearest_token_duration(rec["duration_ms"])
            if tk and m.get("class") == "one-shot":
                rec["duration_token"] = tk
        if delay is not None:
            rec["delay_ms"] = round(max(0.0, float(delay)), 1)
        decl = {}
        if m.get("delay_declared") is not None:
            decl["delay_ms"] = m["delay_declared"]
        if m.get("source") in ("gsap", "cdp") and m.get("duration_ms") is not None:
            decl["duration_ms"] = m["duration_ms"]
        if m.get("ease_declared"):
            decl["easing"] = m["ease_declared"]
        if m.get("stagger_declared"):
            decl["stagger"] = m["stagger_declared"]
        if decl:
            rec["declared"] = decl
        if m.get("fit"):
            rec["easing"] = _easing_block(fit=m["fit"])
        elif m.get("easing_css"):
            rec["easing"] = _easing_block(css=m["easing_css"])
            if m.get("easing_mixed"):
                rec["easing"]["mixed"] = True
        elif m.get("ease_declared"):
            rec["easing"] = _easing_block(declared=m["ease_declared"])
        elif m.get("class") == "scroll-linked" and (sc or {}).get("curve"):
            rec["easing"] = _easing_block(fit=sc["curve"])
        if rec.get("easing") is None:
            rec.pop("easing", None)
        stg = m.get("stagger") or ({"each_ms": m["stagger_declared"]["each_ms"], "count": m["stagger_declared"]["count"],
                                    "order": "dom" if m["stagger_declared"].get("from") in (None, "start", 0) else str(m["stagger_declared"].get("from"))}
                                   if m.get("stagger_declared") else None)
        if stg:
            stg = dict(stg)
            if stg.get("each_px") is not None:            # скрабы соседей: шаг начала диапазонов
                stg["each_vh"] = round(float(stg.pop("each_px")) / IH * 100.0, 1)
            rec["stagger"] = stg
            tk = nearest_token_duration(stg.get("each_ms"), "stagger") if stg.get("each_ms") else None
            if tk:
                rec["stagger"]["token"] = tk
        if m.get("repeat"):
            rp = dict(m["repeat"])
            if m.get("loop"):
                rp.update({k: v for k, v in m["loop"].items() if k in ("period_ms", "speed_px_s", "kind", "amplitude")})
            rec["repeat"] = rp
        elif m.get("class") == "loop":
            rec["repeat"] = {"iterations": "infinite", **{k: v for k, v in (m.get("loop") or {}).items()}}
        if sc:
            s2 = {k: v for k, v in sc.items() if k not in ("curve", "start_text", "end_text", "range", "timeline", "axis")}
            if isinstance(s2.get("start_px"), (int, float)) and isinstance(s2.get("end_px"), (int, float)):
                s2["length_px"] = round(float(s2["end_px"]) - float(s2["start_px"]), 1)
                s2["length_vh"] = round(s2["length_px"] / IH * 100.0, 1)
                s2["start_vh"] = round(float(s2["start_px"]) / IH * 100.0, 1)
            if sc.get("timeline"):
                s2["timeline"] = sc["timeline"]
            if sc.get("range"):
                s2["range"] = [_range_text(r) for r in sc["range"]]
            rec["scroll"] = {k: v for k, v in s2.items() if v is not None}
        if m.get("observed"):
            rec["observed"] = m["observed"]
        if m.get("n"):
            rec["samples"] = int(m["n"])
        rec["_m"] = m
        out.append(rec)
    return out


def _range_text(r):
    if not isinstance(r, dict):
        return "normal"
    nm = r.get("name") or "normal"
    if r.get("value") is None:
        return nm
    unit = "%" if r.get("unit") == "percent" else (r.get("unit") or "")
    return f"{nm} {r['value']:g}{unit}"


def stations_of(moments, pins, st_stations, libs, IH, step_px=0.0):
    """Станции: точки snap ScrollTrigger и CSS scroll-snap, плато прогресса скраба."""
    out = []
    by_st = {m["_m"].get("st_id"): m["id"] for m in moments if m["_m"].get("st_id")}
    for s in st_stations:
        out.append({"kind": "snap", "scroll_px": s["scroll_px"], "progress": s["progress"], "moment": by_st.get(s.get("st_id"))})
    for p in ((libs or {}).get("snap") or {}).get("points") or []:
        al, top, h = p
        y = top if al == "start" else (top + h / 2 - IH / 2 if al == "center" else top + h - IH)
        out.append({"kind": "css-snap", "scroll_px": round(max(0.0, y), 1), "align": al})
    for p in pins:                                    # плато сцены: шаги, на которых не меняется ни один её скраб
        ch = [iv for m in moments if (m["trigger"].get("pin") == p["id"]) and m["_m"].get("changes")
              for iv in m["_m"]["changes"]]
        if not ch:
            continue
        ch.sort()
        merged = []
        for a_, b_ in ch:
            if merged and a_ <= merged[-1][1] + 1:
                merged[-1][1] = max(merged[-1][1], b_)
            else:
                merged.append([a_, b_])
        for (a1, b1), (a2, b2) in zip(merged, merged[1:]):
            if a2 - b1 >= step_px * 0.9 and p["start_px"] <= b1 and a2 <= p["end_px"]:
                out.append({"kind": "plateau", "scroll_px": round((b1 + a2) / 2, 1), "moment": None})
    for s in out:
        if s.get("scroll_px") is None:
            continue
        for p in pins:
            if p["start_px"] - 2 <= s["scroll_px"] <= p["end_px"] + 2:
                s["pin"] = p["id"]
                if p["length_px"] > 0:
                    s.setdefault("progress", round((s["scroll_px"] - p["start_px"]) / p["length_px"], 3))
                break
    out.sort(key=lambda s: s.get("scroll_px") if isinstance(s.get("scroll_px"), (int, float)) else 1e12)
    for i, s in enumerate(out, 1):
        s["id"] = f"s{i:02d}"
    return out


def libraries(raw, cdp_moments):
    """Библиотеки: глобалы рантайма, содержимое файлов, CSS; версия — из рантайма, иначе из файла."""
    L = raw.get("libs") or {}
    sn = ((raw.get("sniff") or {}).get("libs")) or {}
    out = {}

    def put(name, version=None, how=None, files=None):
        r = out.setdefault(name, {"name": name, "version": None, "evidence": []})
        if version and not r["version"] and isinstance(version, str):
            r["version"] = version
        if how and how not in r["evidence"]:
            r["evidence"].append(how)
        if files:
            r["files"] = (r.get("files") or []) + [f for f in files if f not in (r.get("files") or [])][:4]
    if L.get("gsap"):
        put("gsap", L["gsap"] if isinstance(L["gsap"], str) else None, "global")
    elif L.get("gsap_versions"):
        put("gsap", (L["gsap_versions"] or [None])[0], "gsapVersions")
    if L.get("scrolltrigger"):
        put("ScrollTrigger", L["scrolltrigger"] if isinstance(L["scrolltrigger"], str) else None, "global")
    if L.get("scrollsmoother"):
        put("ScrollSmoother", L["scrollsmoother"] if isinstance(L["scrollsmoother"], str) else None, "global")
    if L.get("splittext"):
        put("SplitText", None, "global")
    if L.get("lenis") or L.get("lenis_class") or L.get("lenis_version"):
        put("lenis", L.get("lenis_version"), "instance" if L.get("lenis") else ("class" if L.get("lenis_class") else "lenisVersion"))
    if L.get("locomotive"):
        put("locomotive-scroll", None, "dom")
    if L.get("anime"):
        put("anime.js", (L["anime"] or {}).get("version"), "global")
    for k, nm in (("motion", "motion"), ("three", "three"), ("barba", "barba"), ("swup", "swup"), ("lottie", "lottie")):
        if L.get(k):
            put(nm, None, "global")
    for nm, rec in sn.items():
        put(nm, rec.get("version"), "file", rec.get("files"))
    kinds = {}
    for rec in raw.get("anims") or []:               # по анимациям CDP, а не по сгруппированным моментам
        c = rec.get("cdp") or {}
        kinds[c.get("type") or "?"] = kinds.get(c.get("type") or "?", 0) + 1
        if c.get("viewOrScrollTimeline"):
            kinds["scroll-timeline"] = kinds.get("scroll-timeline", 0) + 1
    return list(out.values()), kinds


def css_block(raw, kinds):
    c = ((raw.get("css") or {}).get("counts")) or {}
    cb = ((raw.get("sniff") or {}).get("css_blocked_counts")) or {}
    tot = {k: int(c.get(k, 0)) + int(cb.get(k, 0)) for k in set(c) | set(cb)}
    snap = (raw.get("libs") or {}).get("snap")
    return {"scroll_driven": {"declared": tot.get("animation_timeline", 0) + tot.get("view_timeline", 0) + tot.get("scroll_timeline", 0),
                              "running": int(kinds.get("scroll-timeline", 0))},
            "view_transitions": {"at_rule": tot.get("view_transition_at", 0) > 0, "names": tot.get("view_transition_name", 0)},
            "scroll_snap": {"type": snap.get("type"), "points": len(snap.get("points") or [])} if snap else None,
            "counts": tot}


OBJ = {"div": "блок", "h1": "заголовок h1", "h2": "заголовок h2", "h3": "заголовок h3", "p": "текст", "img": "картинка", "picture": "картинка",
       "video": "видео", "a": "ссылка", "button": "кнопка", "li": "элемент списка", "svg": "графика svg", "path": "линия svg",
       "span": "фрагмент текста", "section": "секция", "header": "шапка", "nav": "меню", "footer": "подвал", "canvas": "холст",
       "figure": "медиа"}
PROP_RU = {"opacity": "прозрачность", "translateX": "сдвиг X", "translateY": "сдвиг Y", "scale": "масштаб", "scaleX": "масштаб X",
           "scaleY": "масштаб Y", "rotate": "поворот", "clip-path": "маска clip-path", "blur": "размытие", "transform": "transform",
           "x": "сдвиг X", "y": "сдвиг Y", "autoAlpha": "прозрачность", "xPercent": "сдвиг X %", "yPercent": "сдвиг Y %"}


def _fmt(v):
    if isinstance(v, float):
        return f"{v:g}".replace(".", ",")
    return str(v)


def _obj_name(m, IH):
    """Объект строки «что взять»: роль по тегу, экран по положению на странице, селектор — для поиска."""
    t = m["target"]
    base = OBJ.get(t.get("tag"), t.get("tag") or "элемент")
    if t.get("count", 1) > 1:
        base = f"{base} × {t['count']}"
    r = t.get("rect") or [0, 0, 0, 0]
    y = float(r[1]) if len(r) > 1 and isinstance(r[1], (int, float)) else 0.0
    where = "первого экрана" if y < IH else f"{int(y // IH) + 1}-го экрана"
    return f"{base} {where} ({t.get('selector', '')[:40]})"


def _salience(m, IH):
    """Заметность момента для «что взять»: площадь цели (доля окна) × число элементов, скраб — ещё и длина в vh."""
    r = (m.get("target") or {}).get("rect") or [0, 0, 0, 0]
    area = (float(r[2]) * float(r[3])) if len(r) == 4 else 0.0
    k = area / max(1.0, IH * IH * 1.6) * (m.get("target") or {}).get("count", 1)
    if m["class"] == "scroll-linked":
        k *= 1.0 + float((m.get("scroll") or {}).get("length_vh") or 0) / 100.0
    if m["class"] == "one-shot" and (m.get("duration_ms") or 0) < 120:
        k *= 0.1                                     # отклик короче 120 мс — не подача
    return k


def _track_text(t):
    if t.get("from") is None and t.get("to") is None:   # переход без ключевых кадров — известно только свойство
        return PROP_RU.get(t["property"], t["property"])
    s = f"{PROP_RU.get(t['property'], t['property'])} {_fmt(t.get('from'))} → {_fmt(t.get('to'))}{(' ' + t['unit']) if t.get('unit') else ''}"
    if t.get("min") is not None and t.get("max") is not None:
        s += f" (размах {_fmt(t['min'])}…{_fmt(t['max'])})"
    return s


def take_lines(moments, pins, smooth, IH, limit=30):
    """«Что взять» — объект + свойство + число: строки для values.measured записи референса; при многих моментах —
    самые заметные (площадь цели, число элементов, длина скраба), в порядке страницы."""
    out = []
    keep = {m["id"] for m in sorted((m for m in moments if m["class"] in ("one-shot", "scroll-linked", "loop")),
                                    key=lambda m: -_salience(m, IH))[:max(0, limit - len(pins) - 1)]}
    for m in moments:
        if m["class"] not in ("one-shot", "scroll-linked", "loop") or m["id"] not in keep:
            continue
        props = ", ".join(_track_text(t) for t in m["tracks"][:3])
        e = m.get("easing") or {}
        curve = ""
        if e.get("css"):
            curve = f", кривая {e['css']}"
            if e.get("named"):
                curve += f" ≈ {e['named']}"
        if m["class"] == "one-shot":
            s = f"{_obj_name(m, IH)} — {props} — {_fmt(m.get('duration_ms'))} мс"
            if m.get("delay_ms"):
                s += f", задержка {_fmt(m['delay_ms'])} мс"
            s += curve
            if (m.get("stagger") or {}).get("each_ms") is not None:
                s += f", стаггер {_fmt(m['stagger']['each_ms'])} мс × {m['stagger']['count']}"
        elif m["class"] == "scroll-linked":
            sc = m.get("scroll") or {}
            s = f"скраб: {_obj_name(m, IH)} — {props} — на {_fmt(sc.get('length_vh'))} vh прокрутки"
            if sc.get("linearity_r2") is not None:
                s += f", линейность R² {_fmt(sc['linearity_r2'])}"
            if sc.get("smoothing_ms"):
                s += f", догон {_fmt(sc['smoothing_ms'])} мс"
            if sc.get("scrub") not in (None, True, False):
                s += f", scrub {_fmt(sc['scrub'])}"
            if (m.get("stagger") or {}).get("each_vh") is not None:
                s += f", соседи со сдвигом {_fmt(m['stagger']['each_vh'])} vh × {m['stagger']['count']}"
        else:
            rp = m.get("repeat") or {}
            s = f"петля: {_obj_name(m, IH)} — {props}"
            if rp.get("period_ms"):
                s += f" — период {_fmt(rp['period_ms'])} мс"
            if rp.get("speed_px_s"):
                s += f", {_fmt(rp['speed_px_s'])} px/с"
        out.append(s + f" [{m['id']}]")
    for p in pins:
        out.append(f"закрепление {p['target'].get('selector', '')[:40]} — {_fmt(p['length_vh'])} vh, механизм {p['mechanism']} [{p['id']}]")
    if smooth and smooth.get("kind") not in (None, "native"):
        s = f"плавная прокрутка {smooth['kind']}"
        if (smooth.get("tail_ms") or {}).get("median"):
            s += f" — хвост {_fmt(smooth['tail_ms']['median'])} мс на шаг колеса"
        if (smooth.get("options") or {}).get("lerp") is not None:
            s += f", lerp {_fmt(smooth['options']['lerp'])}"
        elif smooth.get("lerp_est"):
            s += f", lerp ≈ {_fmt(smooth['lerp_est'])}"
        out.append(s)
    return out[:40]


def limits_of(raw, passport):
    u = raw.get("unseen") or {}
    out = []
    if u.get("webgl_contexts"):
        out.append(f"WebGL: {u['webgl_contexts']} контекст(ов) — движение внутри холста не видно")
    elif u.get("canvas"):
        out.append(f"canvas: {u['canvas']} крупных холстов — движение внутри не видно")
    if u.get("video_playing"):
        out.append(f"видео: играет {u['video_playing']} — кадры видео не разбираются")
    if u.get("svg_smil"):
        out.append(f"SVG SMIL: {u['svg_smil']} анимаций — не снимаются")
    if u.get("lottie"):
        out.append("Lottie: движение внутри не видно")
    if u.get("iframes"):
        out.append(f"iframe: {u['iframes']} — содержимое не снимается")
    if raw.get("truncated"):
        out.append(f"прокрутка остановлена по --max-s: пройдено {passport['probe']['coverage'] * 100:.0f} % страницы")
    if passport["probe"].get("scroll_mode") == "virtual":
        out.append("виртуальная прокрутка: scrollY не меняется, ось скраба — сумма шагов колеса, закрепления не ищутся")
    if raw.get("dropped"):
        out.append(f"элементов с инлайн-стилями больше предела: {raw['dropped']} не отслежены")
    if raw.get("over"):
        out.append(f"отсчётов больше предела: {raw['over']} не записаны")
    if (raw.get("gsap") or {}).get("truncated"):
        out.append("твинов GSAP больше 4000 — записаны первые")
    gl = (raw.get("gsap") or {}).get("version")
    lone = [m for m in passport["moments"] if m["kind"] == "inline-style"]
    if gl and lone:
        out.append(f"GSAP {gl} с глобалом, но {len(lone)} траекторий инлайн-стилей без своего твина (плагины MotionPath, "
                   "morphSVG, вложенные шкалы, свой код) — их числа по замеру")
    if any((m.get("scroll") or {}).get("container") for m in passport["moments"]):
        out.append("ScrollTrigger внутри containerAnimation: диапазон — в шкале горизонтальной дорожки, px прокрутки не указаны")
    if passport["probe"].get("clock"):
        out.append("--clock: CSS-анимации, переходы и WAAPI идут в реальном времени — их числа объявленные (CDP)")
    out.append("наведение, клики и ввод не выполняются: моменты pointer и state не сняты")
    out.append(f"кривые скраба — по точкам шагов {passport['probe']['scroll_step_vh']:g} vh (точнее — меньший --scroll-step)")
    return out


def frames_sheet(raw, passport, out_dir):
    """Контактный лист кадров: первый экран, станции, начало, середина и конец закреплений (только в выходе)."""
    shots = raw.get("shots") or []
    if not shots:
        return []
    from PIL import Image
    # подписи латиницей: шрифт Pillow по умолчанию кириллицы не рисует
    want = [(0.0, "start")]
    for p in passport["pins"]:
        want += [(p["start_px"], f"{p['id'][:3]} pin start"), ((p["start_px"] + p["end_px"]) / 2, f"{p['id'][:3]} pin mid"),
                 (p["end_px"], f"{p['id'][:3]} pin end")]
    for s in passport["stations"]:
        if isinstance(s.get("scroll_px"), (int, float)):
            want.append((s["scroll_px"], f"{s['id']} {s['kind']}"))
    for m in passport["moments"]:
        sc = m.get("scroll") or {}
        if isinstance(sc.get("end_px"), (int, float)):
            want.append((sc["end_px"], f"{m['id'][:3]} scrub end"))
    picked, labels = [], []
    for y, lab in want[:32]:
        sh = min(shots, key=lambda s: abs(s["y"] - y))
        if any(sh is x for x in picked) and len(picked) > 1:
            continue
        picked.append(sh)
        labels.append(f"{lab} y={int(sh['y'])}")
    arrs = []
    for sh in picked:
        im = Image.open(io.BytesIO(sh["jpg"])).convert("RGB")
        arrs.append(np.asarray(im))
    files = []
    for k in range(0, min(len(arrs), 32), 16):
        p = os.path.join(out_dir, f"frames_{k // 16 + 1:02d}.jpg")
        SR.sheet(arrs[k:k + 16], p, labels[k:k + 16], quality=70)
        files.append(os.path.basename(p))
    return files


def assemble(raw, a, target, url, local):
    """Сырьё → паспорт (dict по motion-passport.schema.json)."""
    nav = raw.get("nav_end") or raw.get("nav") or {}
    IH = float(nav.get("IH") or a.vh)
    IW = float(nav.get("IW") or a.vw)
    host = (urlparse(url).hostname or "local") if not local else "local"
    pid = passport_id(target, url, local, bool(a.mobile))
    passport = {"passport_version": PASSPORT_VERSION, "id": pid, "tool": VERSION, "skill_version": kbpaths.skill_version(),
                "target": {"url": url if not local else target, "final_url": nav.get("href") or url, "host": host, "local": bool(local),
                           "title": (nav.get("title") or "")[:120]},
                "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "status": {"code": "ok", "words": STATUS_WORDS["ok"], "http": raw.get("http")},
                "viewport": {"width": int(IW), "height": int(IH), "dpr": nav.get("dpr") or 1, "mobile": bool(a.mobile),
                             "device": raw.get("device")},
                "browser": {"name": "chromium", "version": raw.get("browser"), "headless": True, "user_agent": nav.get("ua"),
                            "webdriver": nav.get("webdriver")},
                "probe": {"clock": bool(a.clock), "scroll_step_vh": round(a.scroll_step * 100, 1), "settle_ms": a.settle_ms, "max_s": a.max_s,
                          "steps": len(raw.get("wheels") or []), "seconds": raw.get("seconds"), "locks": not a.no_lock}}
    if raw.get("closed") or raw.get("error"):
        code, note = (raw["closed"] if raw.get("closed") else ("error", raw.get("error")))
        passport["status"] = {"code": code, "words": STATUS_WORDS.get(code, code), "note": note, "http": raw.get("http")}
        passport.update({"libraries": [], "moments": [], "pins": [], "stations": [], "take": [], "limits": [], "files": {}})
        return passport
    frame = 16.0 if a.clock else 16.7
    allm, st_pins, st_stations, n_sets = build_moments(raw, frame, IH)
    moments = finalize_moments(allm, raw.get("wheels") or [], IH)
    geo, fixed = detect_pins(raw.get("pin_cands") or [], raw.get("snaps") or [], IH)
    pins = merge_pins(geo, st_pins, IH)
    for n, p in enumerate(pins, 1):
        p["id"] = f"p{n:02d}-" + _el_slug(p["desc"], "pin", 20)
        p["target"] = _target(p.pop("desc"))
        for k in ("ci", "st_id", "pin_spacing", "pin_type"):
            v = p.pop(k, None)
            if k in ("pin_spacing", "pin_type") and v is not None:
                p.setdefault("scrolltrigger", {})[k] = v
        p["moments"] = [m["id"] for m in moments if m["class"] == "scroll-linked" and isinstance((m.get("scroll") or {}).get("start_px"), (int, float))
                        and p["start_px"] - 2 <= m["scroll"]["start_px"] <= p["end_px"] + 2]
    by_id = {m["id"]: m for m in moments}
    for p in pins:                                    # скраб, начатый в закреплении, — скраб в закреплении
        for mid in p["moments"]:
            tr = by_id[mid]["trigger"]
            tr["pin"] = p["id"]
            if tr["type"] == "scroll-scrub":
                tr["type"] = "pin-scrub"
    step_px = float(np.median([w["dy"] for w in raw.get("wheels") or []])) if raw.get("wheels") else a.scroll_step * IH
    stations = stations_of(moments, pins, st_stations, raw.get("libs"), IH, step_px)
    for p in pins:
        p["stations"] = [s["id"] for s in stations if s.get("pin") == p["id"]]
    libs, kinds = libraries(raw, allm)
    wheels = raw.get("wheels") or []
    doc_h = float(nav.get("docH") or 0)
    smax = max([float(w.get("max") or 0) for w in wheels] + [max(0.0, doc_h - IH)])
    reached = max([float(w.get("y1") or 0) for w in wheels] + [0.0])
    virtual = smax <= 2 and len(wheels) > 0
    passport["probe"].update({"scroll_mode": "virtual" if virtual else "native", "doc_height_px": doc_h, "scroll_max_px": smax,
                              "scroll_reached_px": reached, "coverage": round(reached / smax, 3) if smax > 2 else 1.0,
                              "truncated": bool(raw.get("truncated")), "load_phase_ms": raw.get("load_phase_ms"),
                              "observed_elements": len(raw.get("els") or {}), "sets": n_sets, "cdp_animations": len(raw.get("anims") or [])})
    nav0 = raw.get("nav") or {}
    timing = {f"{k}_ms": nav0[k] for k in ("dcl", "load", "fcp") if isinstance(nav0.get(k), (int, float))}
    if timing:
        passport["timing"] = timing
    smooth = smooth_scroll(raw.get("libs"), wheels, raw.get("scroll") or [], IH)
    gsap_ok = bool((raw.get("gsap") or {}).get("version") or (raw.get("libs") or {}).get("gsap"))
    passport.update({"libraries": libs, "smooth_scroll": smooth, "css": css_block(raw, kinds), "moments": moments, "pins": pins,
                     "stations": stations, "fixed_layers": [{"target": _target(f["desc"]), "height_vh": f["height_vh"]} for f in fixed],
                     "unseen": raw.get("unseen") or {}})
    passport["gsap"] = {"global": gsap_ok, "tweens": len((raw.get("gsap") or {}).get("tweens") or []),
                        "scrolltriggers": len(((raw.get("st") or {}).get("list")) or [])} if (gsap_ok or raw.get("st")) else None
    if passport["gsap"] is None:
        passport.pop("gsap")
    if not moments and not pins:
        passport["status"].update({"code": "static", "words": STATUS_WORDS["static"]})
    elif raw.get("truncated"):
        passport["status"].update({"code": "partial", "words": STATUS_WORDS["partial"]})
    passport["take"] = take_lines(moments, pins, smooth, IH)
    passport["limits"] = limits_of(raw, passport)
    for m in moments:
        m.pop("_m", None)
    return passport


def passport_id(target, url, local, mobile=False):
    """Id паспорта: хост (у локальной страницы — local-<имя файла>) и хеш адреса; замер с телефона — с «-mobile» и своим
    хешем, чтобы не перезаписывать паспорт той же страницы с компьютера."""
    key = (os.path.abspath(target) if local else url) + ("#mobile" if mobile else "")
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    host = "local-" + _slug(os.path.splitext(os.path.basename(target))[0], 24) if local else (urlparse(url).hostname or "site")
    return re.sub(r"[^a-z0-9.-]+", "-", host.lower()).strip("-") + ("-mobile" if mobile else "") + "-" + h


# =====================================================================================================================
# 13. Сводка для человека (passport.md)
# =====================================================================================================================
TRIG_RU = {"load": "загрузка", "in-view": "в зоне видимости", "scroll-scrub": "скраб", "pin-scrub": "скраб в закреплении",
           "idle-loop": "петля", "state": "по таймеру", "unknown": "—"}
CLASS_RU = {"one-shot": "разовое", "scroll-linked": "по прокрутке", "loop": "петля"}


def render_md(p):
    L = [f"# Паспорт движения: {p['target'].get('host')}", ""]
    st = p["status"]
    L.append(f"- Адрес: {p['target'].get('url')}" + (f" (заголовок «{p['target'].get('title')}»)" if p["target"].get("title") else ""))
    L.append(f"- Снято: {p['measured_at']}, окно {p['viewport']['width']}×{p['viewport']['height']}"
             + (" (телефон, эмуляция)" if p["viewport"].get("mobile") else "") + f", {p['browser'].get('version') or ''}, "
             f"шаг прокрутки {p['probe']['scroll_step_vh']:g} vh, пауза {p['probe']['settle_ms']} мс"
             + (", часы page.clock" if p["probe"].get("clock") else ""))
    L.append(f"- Статус: {st['words']}" + (f" — {st['note']}" if st.get("note") else "") + f" (`{st['code']}`)")
    if st["code"] in ("blocked", "login", "robots", "error"):
        L += ["", "Страницу не снимаем: защиту и вход утилита не обходит. Сайт смотрит человек; числа — с его слов или с "
              "другой страницы этого сайта.", ""]
        return "\n".join(L) + "\n"
    pr = p["probe"]
    L.append(f"- Прокрутка: {pr['steps']} шагов, пройдено {pr.get('coverage', 1) * 100:.0f} % страницы ({pr.get('scroll_mode')})"
             + ("; остановлено по времени" if pr.get("truncated") else ""))
    libs = ", ".join(f"{x['name']}{(' ' + x['version']) if x.get('version') else ''}" for x in p.get("libraries") or [])
    L.append(f"- Библиотеки: {libs or 'не найдены'}")
    sm = p.get("smooth_scroll") or {}
    s = sm.get("kind", "native")
    if (sm.get("tail_ms") or {}).get("median") is not None:
        s += f", хвост шага {sm['tail_ms']['median']:.0f} мс"
    if (sm.get("options") or {}).get("lerp") is not None:
        s += f", lerp {sm['options']['lerp']}"
    elif sm.get("lerp_est"):
        s += f", lerp ≈ {sm['lerp_est']}"
    L.append(f"- Прокрутка страницы: {s}")
    css = p.get("css") or {}
    sd = css.get("scroll_driven") or {}
    L.append(f"- CSS scroll-driven: объявлено {sd.get('declared', 0)}, работает {sd.get('running', 0)}; View Transitions: "
             f"{'@view-transition есть' if (css.get('view_transitions') or {}).get('at_rule') else '@view-transition нет'}, имён "
             f"{(css.get('view_transitions') or {}).get('names', 0)}")
    L += ["", "## Что двигается", ""]
    if p["moments"]:
        L.append("| id | что | когда | свойства | длит., мс | задержка, мс | кривая | стаггер |")
        L.append("|---|---|---|---|---|---|---|---|")
        for m in p["moments"][:60]:
            t = m["target"]
            what = f"{OBJ.get(t.get('tag'), t.get('tag'))} `{t.get('selector', '')[:36]}`" + (f" × {t['count']}" if t.get("count", 1) > 1 else "")
            when = TRIG_RU.get(m["trigger"]["type"], m["trigger"]["type"])
            if m["trigger"].get("step"):
                when += f", шаг {m['trigger']['step']}"
            props = "; ".join(_track_text(x) for x in m["tracks"][:3])
            sc = m.get("scroll") or {}
            dur = _fmt(m["duration_ms"]) if m.get("duration_ms") is not None else (f"{_fmt(sc.get('length_vh'))} vh" if sc.get("length_vh") is not None else "—")
            e = m.get("easing") or {}
            curve = (e.get("named") or "") + (f" ({e['css']})" if e.get("css") else "")
            if e.get("bezier_error") is not None:
                curve += f", ошибка {e['bezier_error']:g}"
            stg = m.get("stagger") or {}
            stx = (_fmt(stg["each_ms"]) + " мс × " + str(stg["count"])) if stg.get("each_ms") is not None else (
                (_fmt(stg["each_vh"]) + " vh × " + str(stg["count"])) if stg.get("each_vh") is not None else "—")
            L.append(f"| {m['id']} | {what} | {when} | {props} | {dur} | {_fmt(m['delay_ms']) if m.get('delay_ms') is not None else '—'} | "
                     f"{curve or '—'} | {stx} |")
        if len(p["moments"]) > 60:
            L.append(f"\nЕщё {len(p['moments']) - 60} моментов — в `passport.json`.")
    else:
        L.append("Движения не найдено: ни анимаций CSS и WAAPI, ни движения скриптом через стили (см. «Чего замер не видит»).")
    L += ["", "## Закрепления и станции", ""]
    if p["pins"]:
        for pn in p["pins"]:
            L.append(f"- {pn['id']}: `{pn['target'].get('selector', '')[:48]}` — {_fmt(pn['length_vh'])} vh ({_fmt(pn['start_px'])}–"
                     f"{_fmt(pn['end_px'])} px), {pn['mechanism']}, {pn['evidence']}" + (f"; моменты {', '.join(pn['moments'])}" if pn.get("moments") else "")
                     + (f"; станции {', '.join(pn['stations'])}" if pn.get("stations") else ""))
    else:
        L.append("- Закреплений не найдено.")
    if p["stations"]:
        L.append("- Станции: " + "; ".join(f"{s['id']} {s['kind']} {_fmt(s.get('scroll_px'))} px" + (f" (доля {_fmt(s['progress'])})" if s.get("progress") is not None else "")
                                         for s in p["stations"][:16]))
    L += ["", "## Что взять", ""]
    L += [f"- {x}" for x in p["take"]] or ["- —"]
    L += ["", "## Чего замер не видит", ""]
    L += [f"- {x}" for x in p["limits"]]
    if (p.get("files") or {}).get("frames"):
        L += ["", "## Кадры", "", "Контактный лист станций и закреплений (только в выходе): " + ", ".join(p["files"]["frames"])]
    L += ["", f"Паспорт: `passport.json` (схема `motion-passport.schema.json`), утилита {p['tool']}."]
    return "\n".join(L) + "\n"


# =====================================================================================================================
# 14. probe: запуск
# =====================================================================================================================
def default_out(target, url, local, mobile=False):
    return str(kbpaths.out("creative", "motion-probe", passport_id(target, url, local, mobile)))


def probe_core(a):
    """Замер и запись паспорта без печати: → (код выхода, паспорт)."""
    target = a.target
    local = not re.match(r"^https?://", target)
    srv, net_ctx, url = None, (None, None), target
    if local:
        p = os.path.abspath(target)
        if os.path.isdir(p):
            p = os.path.join(p, "index.html")
        if not os.path.isfile(p):
            raise SystemExit(f"нет файла {p}")
        root = MC.local_root_for(p, getattr(a, "root", None))
        srv = MC.make_server(root, MC.Served())
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        url = f"{base}/{os.path.relpath(p, root)}"
        net_ctx = (base, root)
        target = p
    a.out = os.path.abspath(a.out or default_out(target, url, local, bool(a.mobile)))
    os.makedirs(a.out, exist_ok=True)
    for f in os.listdir(a.out):                       # листы кадров прошлого замера этой страницы
        if re.fullmatch(r"frames_\d{2}\.jpg", f):
            os.remove(os.path.join(a.out, f))
    raw = None
    try:
        if not local:
            try:
                allowed = _rc().robots_allows(url)
            except Exception:
                allowed = False
            if not allowed:
                raw = {"closed": ["robots", "robots.txt не разрешает этот адрес или недоступен"], "url": url}
        if raw is None:
            if a.no_lock:
                raw = measure(url, a, net_ctx)
            else:
                MC.wait_memory()                         # память — до замка: ожидание не держит браузер других
                with kbpaths.lock("browser"):
                    raw = measure(url, a, net_ctx)
    finally:
        if srv:
            srv.shutdown()
    passport = assemble(raw, a, target, url, local)
    files = {"json": "passport.json", "md": "passport.md"}
    if a.frames and passport["status"]["code"] in ("ok", "partial", "static"):
        try:
            fr = frames_sheet(raw, passport, a.out)
            if fr:
                files["frames"] = fr
        except Exception as e:
            log(f"кадры: {e}")
    passport["files"] = files
    with open(os.path.join(a.out, "passport.json"), "w", encoding="utf-8") as f:
        json.dump(passport, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(a.out, "passport.md"), "w", encoding="utf-8") as f:
        f.write(render_md(passport))
    code = passport["status"]["code"]
    return (EXIT_CLOSED if code in ("blocked", "login", "robots") else (2 if code == "error" else 0)), passport


def run_probe(a):
    code, passport = probe_core(a)
    if a.json:
        print(json.dumps(passport, ensure_ascii=False, indent=1, default=str))
    else:
        print(json.dumps({"status": passport["status"]["code"], "words": passport["status"]["words"], "moments": len(passport["moments"]),
                          "pins": len(passport["pins"]), "stations": len(passport["stations"]),
                          "libraries": [x["name"] for x in passport.get("libraries") or []], "out": a.out}, ensure_ascii=False))
    return code


# =====================================================================================================================
# 15. compare: паспорт против паспорта (референс против прототипа) или против motion-spec
# =====================================================================================================================
FAMILY = {"load": "time", "in-view": "time", "state": "time", "scroll-scrub": "scroll", "pin-scrub": "scroll", "idle-loop": "loop"}
RANK = {None: 0, "близко": 1, "заметно": 2, "далеко": 3}


def compare_thresholds():
    """Пороги «близко / заметно / далеко» — x-compare схемы паспорта (мнение базы; калибровка — по проектам)."""
    with open(SCHEMA, encoding="utf-8") as f:
        th = (json.load(f).get("x-compare") or {})
    return {k: v for k, v in th.items() if isinstance(v, dict) and "close" in v and "far" in v}


def load_doc(path):
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    if path.endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(txt)
    return json.loads(txt)


def norm_passport(p):
    ms = []
    for i, m in enumerate(p.get("moments") or []):
        e = m.get("easing") or {}
        f = _bz(e["bezier"]) if e.get("bezier") else (ease_fn(e.get("css")) or ease_fn(e.get("declared")) or ease_fn(e.get("named")))
        sc, t = m.get("scroll") or {}, m.get("target") or {}
        ms.append({"id": m.get("id"), "class": m.get("class"), "family": FAMILY.get((m.get("trigger") or {}).get("type"), "time"),
                   "duration_ms": m.get("duration_ms"), "delay_ms": m.get("delay_ms"), "curve": f,
                   "curve_text": e.get("named") or e.get("css") or e.get("declared"), "stagger_ms": (m.get("stagger") or {}).get("each_ms"),
                   "count": t.get("count", 1), "length_vh": sc.get("length_vh"), "logical": t.get("logical"),
                   "data_moment": (t.get("data") or {}).get("moment"), "selector": t.get("selector"), "path": t.get("path"),
                   "kind": m.get("kind"), "t": m.get("t_ms"), "order": i, "source_moment": None,
                   "period_ms": (m.get("repeat") or {}).get("period_ms")})
    pins = [{"id": x.get("id"), "length_vh": x.get("length_vh")} for x in p.get("pins") or []]
    return {"kind": "passport", "id": p.get("id"), "title": (p.get("target") or {}).get("url"), "moments": ms, "pins": pins}


def norm_spec(s, path):
    """motion-spec v1 → моменты для сравнения: длительность (мс, доля базы или токен motion.marketing), кривая (css,
    токен, скраб — linear), задержка триггера, стаггер, длина скраба в vh, закрепления сцен."""
    tk = tokens()
    page = s.get("page") or {}
    base = page.get("base") or {}
    base_ms = base.get("duration_ms") if isinstance(base.get("duration_ms"), (int, float)) else None

    def dur(d):
        if not isinstance(d, dict):
            return None
        if isinstance(d.get("ms"), (int, float)):
            return float(d["ms"])
        if isinstance(d.get("share"), (int, float)) and base_ms:
            return float(d["share"]) * base_ms
        if isinstance(d.get("token"), str):
            parts = d["token"].split(".")
            if len(parts) >= 2:
                return tk.get(parts[-2], {}).get(parts[-1])
        return None

    def eas(e):
        e = e if isinstance(e, dict) and e else (base.get("easing") if isinstance(base.get("easing"), dict) else None)
        if not e:
            return None, None
        if e.get("none"):
            return NAMED["linear"], "linear (скраб)"
        if e.get("css"):
            return ease_fn(e["css"]), e["css"]
        if isinstance(e.get("token"), str):
            p = tk["easing"].get(e["token"].split(".")[-1])
            return (_bz(p) if p else None), e["token"]
        return None, None
    ms, pins, i = [], [], 0
    for sec in s.get("sections") or []:
        scene = sec.get("scene") or {}
        if scene.get("pin") in ("sticky", "pin-transform", "pin-padding") and isinstance(scene.get("length_vh"), (int, float)):
            pins.append({"id": str(sec.get("id")), "length_vh": float(scene["length_vh"])})
        for m in sec.get("moments") or []:
            trig = m.get("trigger") or {}
            f, ftxt = eas(m.get("easing"))
            stg = m.get("stagger") or {}
            each = dur(stg.get("each")) if isinstance(stg.get("each"), dict) else None
            count = 1 + len(m.get("stagger_targets") or [])
            if stg.get("max_items") and count <= 1:
                count = int(stg["max_items"])
            length = None
            rv = trig.get("range_vh") or {}
            if isinstance(rv.get("length"), (int, float)):
                length = float(rv["length"])
            elif isinstance(trig.get("progress"), dict) and isinstance(scene.get("length_vh"), (int, float)):
                pr = trig["progress"]
                length = float(scene["length_vh"]) * (float(pr.get("end", 1)) - float(pr.get("start", 0)))
            elif trig.get("type") == "pin-scrub" and isinstance(scene.get("length_vh"), (int, float)):
                length = float(scene["length_vh"])
            src = m.get("source") or {}
            ms.append({"id": m.get("id"), "class": m.get("class") if m.get("class") in ("one-shot", "scroll-linked", "loop") else "one-shot",
                       "family": FAMILY.get(trig.get("type"), "time"), "duration_ms": dur(m.get("duration")), "delay_ms": trig.get("delay_ms"),
                       "curve": f, "curve_text": ftxt, "stagger_ms": each, "count": count, "length_vh": length, "logical": m.get("target"),
                       "data_moment": m.get("id"), "selector": m.get("selector_hint"), "order": i, "source_moment": src.get("moment"),
                       "source_ref": src.get("ref"), "period_ms": (m.get("loop") or {}).get("period_ms")})
            i += 1
    return {"kind": "motion-spec", "id": s.get("id"), "title": path, "moments": ms, "pins": pins}


def normalize(path):
    d = load_doc(path)
    if isinstance(d, dict) and d.get("passport_version"):
        return norm_passport(d)
    if isinstance(d, dict) and d.get("motion_spec_version"):
        return norm_spec(d, path)
    raise ValueError(f"{path}: не паспорт движения и не motion-spec")


def _band(v, th):
    if v is None or not th:
        return None
    x = abs(float(v))
    return "близко" if x <= th["close"] else ("заметно" if x <= th["far"] else "далеко")


def match_moments(A, B):
    """Пары моментов: ссылка source.moment (спецификация → паспорт референса), data-moment (прототип → спецификация),
    логическая цель, тот же элемент (путь, вид и класс момента — повторный замер того же сайта), затем порядок внутри
    класса; из нескольких кандидатов — ближайший по времени начала."""
    am, bm = A["moments"], B["moments"]
    pairs, ua, ub = [], set(), set()

    def link(a, b):
        if (b.get("source_moment") and b["source_moment"] == a.get("id")) or (a.get("source_moment") and a["source_moment"] == b.get("id")):
            return "source.moment"
        if A["kind"] == "passport" and B["kind"] == "motion-spec" and a.get("data_moment") and a["data_moment"] == b.get("id"):
            return "data-moment"
        if B["kind"] == "passport" and A["kind"] == "motion-spec" and b.get("data_moment") and b["data_moment"] == a.get("id"):
            return "data-moment"
        if A["kind"] == B["kind"] == "passport" and a.get("data_moment") and a["data_moment"] == b.get("data_moment"):
            return "data-moment"
        if a.get("logical") and a["logical"] == b.get("logical"):
            return "цель"
        if A["kind"] == B["kind"] == "passport" and (a.get("path") or a.get("selector")) and \
                (a.get("path") or a.get("selector")) == (b.get("path") or b.get("selector")) and \
                a.get("kind") == b.get("kind") and a.get("class") == b.get("class") and a.get("family") == b.get("family"):
            return "элемент"                             # тот же сайт: уникальный путь элемента, вид и класс момента
        return None
    for prio in ("source.moment", "data-moment", "цель", "элемент"):
        for i, a in enumerate(am):
            if i in ua:
                continue
            cands = [j for j, b in enumerate(bm) if j not in ub and link(a, b) == prio]
            if not cands:
                continue
            # у одного элемента бывает несколько моментов (твины шкалы подряд) — ближайший по времени начала
            j = min(cands, key=lambda j: abs(float(bm[j].get("t") or 0.0) - float(a.get("t") or 0.0)))
            pairs.append((i, j, prio))
            ua.add(i)
            ub.add(j)
    for cls in ("one-shot", "scroll-linked", "loop"):
        ra = [i for i, a in enumerate(am) if i not in ua and a["class"] == cls]
        rb = [j for j, b in enumerate(bm) if j not in ub and b["class"] == cls]
        for i, j in zip(ra, rb):
            pairs.append((i, j, "порядок"))
            ua.add(i)
            ub.add(j)
    pairs.sort(key=lambda x: x[0])
    return pairs, [i for i in range(len(am)) if i not in ua], [j for j in range(len(bm)) if j not in ub]


def pair_metrics(a, b, th):
    r = {}
    if a.get("duration_ms") and b.get("duration_ms"):
        r["duration_pct"] = round(100.0 * (float(b["duration_ms"]) - float(a["duration_ms"])) / float(a["duration_ms"]), 1)
    if a.get("delay_ms") is not None and b.get("delay_ms") is not None:
        r["delay_ms"] = round(float(b["delay_ms"]) - float(a["delay_ms"]), 1)
    if a.get("curve") is not None and b.get("curve") is not None:
        r["curve_rmse"] = round(curve_distance(a["curve"], b["curve"]), 4)
    if a.get("stagger_ms") is not None and b.get("stagger_ms") is not None:
        r["stagger_ms"] = round(float(b["stagger_ms"]) - float(a["stagger_ms"]), 1)
    if a.get("length_vh") is not None and b.get("length_vh") is not None:
        r["length_vh"] = round(float(b["length_vh"]) - float(a["length_vh"]), 1)
    if a.get("period_ms") and b.get("period_ms"):
        r["period_pct"] = round(100.0 * (float(b["period_ms"]) - float(a["period_ms"])) / float(a["period_ms"]), 1)
    bands = {k: _band(v, th.get("duration_pct" if k == "period_pct" else k)) for k, v in r.items()}
    verdict = max(bands.values(), key=lambda x: RANK[x]) if bands else None
    return r, bands, verdict


def compare_docs(pa, pb):
    th = compare_thresholds()
    A, B = normalize(pa), normalize(pb)
    pairs, ua, ub = match_moments(A, B)
    rows = []
    for i, j, how in pairs:
        a, b = A["moments"][i], B["moments"][j]
        met, bands, verdict = pair_metrics(a, b, th)
        rows.append({"a": a["id"], "b": b["id"], "how": how, "class": a["class"], "metrics": met, "bands": bands, "verdict": verdict,
                     "a_values": {k: a.get(k) for k in ("duration_ms", "delay_ms", "curve_text", "stagger_ms", "count", "length_vh")},
                     "b_values": {k: b.get(k) for k in ("duration_ms", "delay_ms", "curve_text", "stagger_ms", "count", "length_vh")}})
    pins = []
    for k, (x, y) in enumerate(zip(A["pins"], B["pins"])):
        d = None if x.get("length_vh") is None or y.get("length_vh") is None else round(float(y["length_vh"]) - float(x["length_vh"]), 1)
        pins.append({"a": x["id"], "b": y["id"], "length_vh": [x.get("length_vh"), y.get("length_vh")], "delta_vh": d,
                     "band": _band(d, th.get("length_vh"))})
    na, nb = len(A["moments"]), len(B["moments"])
    counts = {"a": na, "b": nb, "delta": nb - na, "band": _band(nb - na, th.get("count")),
              "pins": [len(A["pins"]), len(B["pins"])]}
    worst = max([r["verdict"] for r in rows] + [p["band"] for p in pins] + [None], key=lambda x: RANK[x])
    spec_missing = ([A["moments"][i]["id"] for i in ua] if A["kind"] == "motion-spec" else []) + \
                   ([B["moments"][j]["id"] for j in ub] if B["kind"] == "motion-spec" else [])
    return {"a": {"kind": A["kind"], "id": A["id"], "file": pa}, "b": {"kind": B["kind"], "id": B["id"], "file": pb},
            "pairs": rows, "unmatched_a": [A["moments"][i]["id"] for i in ua], "unmatched_b": [B["moments"][j]["id"] for j in ub],
            "spec_unmatched": spec_missing, "pins": pins, "counts": counts, "verdict": worst, "thresholds": th,
            "thresholds_status": "[мнение] калибровка — по проектам"}


def render_compare(r):
    def f(v, unit=""):
        return "—" if v is None else f"{_fmt(v)}{unit}"
    L = [f"# Сравнение движения: {r['a']['kind']} `{r['a']['id']}` → {r['b']['kind']} `{r['b']['id']}`", "",
         f"Итог: **{r['verdict'] or 'нет пар'}**. Моментов {r['counts']['a']} → {r['counts']['b']} ({r['counts']['band'] or '—'}), "
         f"закреплений {r['counts']['pins'][0]} → {r['counts']['pins'][1]}. Пороги — `x-compare` схемы паспорта "
         f"{r['thresholds_status']}.", "",
         "| A | B | связь | длительность, мс (Δ %) | задержка, мс (Δ) | кривая (расстояние) | стаггер, мс (Δ) | длина, vh (Δ) | итог |",
         "|---|---|---|---|---|---|---|---|---|"]
    for x in r["pairs"]:
        av, bv, m = x["a_values"], x["b_values"], x["metrics"]
        L.append(f"| {x['a']} | {x['b']} | {x['how']} | {f(av['duration_ms'])} → {f(bv['duration_ms'])} ({f(m.get('duration_pct'), ' %')}) | "
                 f"{f(av['delay_ms'])} → {f(bv['delay_ms'])} ({f(m.get('delay_ms'))}) | {av['curve_text'] or '—'} → {bv['curve_text'] or '—'} "
                 f"({f(m.get('curve_rmse'))}) | {f(av['stagger_ms'])} → {f(bv['stagger_ms'])} ({f(m.get('stagger_ms'))}) | "
                 f"{f(av['length_vh'])} → {f(bv['length_vh'])} ({f(m.get('length_vh'))}) | {x['verdict'] or '—'} |")
    if r["pins"]:
        L += ["", "Закрепления: " + "; ".join(f"{p['a']} → {p['b']}: {f(p['length_vh'][0])} → {f(p['length_vh'][1])} vh ({p['band'] or '—'})" for p in r["pins"])]
    if r["unmatched_a"]:
        L.append(f"\nБез пары в A: {', '.join(r['unmatched_a'][:20])}")
    if r["unmatched_b"]:
        L.append(f"\nБез пары в B: {', '.join(r['unmatched_b'][:20])}")
    if r["spec_unmatched"]:
        L.append(f"\nМоменты спецификации без замера: {', '.join(r['spec_unmatched'])} — в прототипе их нет или замер их не видит.")
    return "\n".join(L) + "\n"


def run_compare(a):
    try:
        r = compare_docs(a.a, a.b)
    except Exception as e:
        log(f"compare: {e}")
        return 2
    md = render_compare(r)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, "compare.md"), "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(os.path.join(a.out, "compare.json"), "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str) if a.json else md)
    return 1 if (r["verdict"] == "далеко" or r["spec_unmatched"]) else 0


# =====================================================================================================================
# 16. Самопроверка
# =====================================================================================================================
def _ns(**kw):
    d = dict(target=None, out=None, vw=1440, vh=900, mobile=False, scroll_step=0.33, settle_ms=1200, max_s=60.0, frames=False,
             clock=False, no_lock=True, json=False, locale="ru-RU", root=None, virtual_steps=8)
    d.update(kw)
    return argparse.Namespace(**d)


def selftest(no_browser=False):
    ok = True

    def check(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {name}: {got!r}" + ("" if good else f" (ожидалось {want!r})"))

    def near(name, got, want, tol):
        nonlocal ok
        good = got is not None and abs(float(got) - float(want)) <= tol
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {name}: {got!r}" + ("" if good else f" (ожидалось {want} ± {tol})"))

    one = lambda f, x: float(np.asarray(f(np.array([x])), dtype=float)[0])  # noqa: E731
    # кривые
    check("power2.out(0,5) = 0,875 (easeOutCubic)", round(one(NAMED["power2.out"], 0.5), 4), 0.875)
    check("power3.inOut(0,5) = 0,5; sine.inOut(0,5) = 0,5", (round(one(NAMED["power3.inOut"], 0.5), 4), round(one(NAMED["sine.inOut"], 0.5), 4)), (0.5, 0.5))
    check("expo.in(0) = 0, expo.out(1) = 1", (round(one(NAMED["expo.in"], 0.0), 6), round(one(NAMED["expo.out"], 1.0), 6)), (0.0, 1.0))
    check("back.out перелетает за 1", float(np.max(NAMED["back.out"](U41))) > 1.0, True)
    check("cubic-bezier(.42, 0, .58, 1) в 0,5 = 0,5; cubic-bezier(0, 0, 1, 1) — прямая",
          (round(float(bezier_y(np.array([0.5]), 0.42, 0, 0.58, 1)[0]), 4), float(np.max(np.abs(bezier_y(U41, 0, 0, 1, 1) - U41))) < 1e-6), (0.5, True))
    check("разбор кривых: power3.out, expo → expo.out, none → linear, steps — неизвестна",
          (ease_fn("power3.out") is NAMED["power3.out"], ease_fn("expo") is NAMED["expo.out"], ease_fn("none") is NAMED["linear"], ease_fn("steps(4)")),
          (True, True, True, None))
    near("back.out(2): своё перелетание сильнее стандартного", float(np.max(ease_fn("back.out(2)")(U41))) - float(np.max(NAMED["back.out"](U41))), 0.04, 0.04)
    near("CSS linear(0, 0.5 30%, 1) в 0,3 = 0,5", one(ease_fn("linear(0, 0.5 30%, 1)"), 0.3), 0.5, 1e-9)
    nm = nearest_named(ease_fn("cubic-bezier(0.33, 1, 0.68, 1)"))
    check("cubic-bezier(0.33, 1, 0.68, 1) ближе всего к power2.out", nm[0], "power2.out")
    # подбор: easeOutCubic 600 мс со старта 100 мс, кадры по 1000/60 мс, отсчёт покоя 50 мс
    fr = 1000.0 / 60.0
    t0, D = 100.0, 600.0
    ts = [t0 + fr * k for k in range(1, 60) if t0 + fr * (k - 1) < t0 + D]
    vs = [40.0 * (1.0 - one(NAMED["power2.out"], min(1.0, (t - t0) / D))) for t in ts]
    f = fit_curve(ts, vs, 50.0, ts[0], ts[-2], ts[-1], v0=40.0)
    check("подбор easeOutCubic: именованная power2.out", f["named"], "power2.out")
    near("подбор easeOutCubic: старт 100 мс", f["s"], 100.0, 3.0)
    near("подбор easeOutCubic: длительность 600 мс", f["e"] - f["s"], 600.0, 6.0)
    check("подбор easeOutCubic: bezier с ошибкой < 0,01 и ≈ power2.out (расстояние < 0,01)",
          (f["bezier_error"] < 0.01, curve_distance(_bz(f["bezier"]), NAMED["power2.out"]) < 0.01), (True, True))
    f2 = fit_curve([t0 + fr] + ts[1:], [40.0 * (1.0 - one(NAMED["power2.out"], fr / D))] + vs[1:], t0 + fr - FIRST_FRAME * fr, t0 + fr, ts[-2], ts[-1], v0=None)
    check("подбор без исходного значения (to-твин с CSS-состояния): power2.out", f2["named"], "power2.out")
    near("подбор без исходного значения: исходное 40 px — с точностью до кадра старта", f2["v0"], 40.0, 2.5)
    near("подбор без исходного значения: длительность 600 мс — с точностью до кадра", f2["e"] - f2["s"], 600.0, FIRST_FRAME * fr)
    vb = [100.0 * one(NAMED["back.out"], min(1.0, (t - t0) / D)) for t in ts]
    check("подбор с перелётом: back.out", fit_curve(ts, vb, 50.0, ts[0], ts[-2], ts[-1], v0=0.0)["named"], "back.out")
    # transform и токены
    tx, ty, sx, sy, rot = parse_transform("matrix(1.03923, 0.6, -0.6, 1.03923, 12, 40)")
    check("matrix → сдвиг 12/40, масштаб 1,2, поворот 30°", (round(tx, 1), round(ty, 1), round(sx, 2), round(rot, 1)), (12.0, 40.0, 1.2, 30.0))
    check("transform CSS-функциями: translateY(40px) scale(.9)", _css_transform_nums("translateY(40px) scale(.9)"), {"translateY": 40.0, "scale": 0.9})
    te = nearest_token_easing(_bz((0.16, 1, 0.3, 1)))
    check("ближайший токен кривой (0.16, 1, 0.3, 1) — out-expo, расстояние 0",
          (te or {}).get("token"), "motion.marketing.easing.out-expo")
    check("ближайший токен длительности 560 мс — reveal", (nearest_token_duration(560.0) or {}).get("token"), "motion.marketing.duration.reveal")
    # диапазон view(): шкала cover 1350–2350 при окне 900 → entry 0 % … cover 50 % = 1350–1850
    vr = view_range({"startOffset": 1350, "endOffset": 2350, "subjectNodeId": 3},
                    {"tl": "ViewTimeline", "rs": {"name": "entry", "unit": "percent", "value": 0}, "re": {"name": "cover", "unit": "percent", "value": 50}}, 900)
    check("view(): entry 0 % … cover 50 % → 1350–1850 px", tuple(round(x) for x in vr), (1350, 1850))
    vr2 = view_range({"startOffset": 1350, "endOffset": 2350, "subjectNodeId": 3},
                     {"tl": "ViewTimeline", "rs": {"name": "contain", "unit": "percent", "value": 0}, "re": {"name": "contain", "unit": "percent", "value": 100}}, 900)
    check("view(): contain 0 % … 100 % у элемента 100 px → 1450–2250 px", tuple(round(x) for x in vr2), (1450, 2250))
    # стаггер
    base = {"class": "one-shot", "kind": "inline-style", "trigger": "load", "wheel": None, "duration_ms": 500.0,
            "tracks": [{"property": "translateY"}, {"property": "opacity"}], "fit": {"bezier": [0.33, 1, 0.68, 1]}}
    grp = group_stagger([dict(base, t0=100.0 + 80 * k, desc={"parent": "ul", "sig": "li.card", "sel": f"li{k}", "rect": [0, 100 + 10 * k]}) for k in range(5)]
                        + [dict(base, t0=900.0, kind="css-animation", desc={"parent": "x", "sig": "h1", "sel": "h1"})])
    g0 = next(m for m in grp if m.get("count", 1) > 1)
    check("стаггер: 5 соседей с шагом 80 мс → один момент, 80 мс, порядок dom", (len(grp), g0["count"], g0["stagger"]["each_ms"], g0["stagger"]["order"]),
          (2, 5, 80.0, "dom"))
    # закрепление по геометрии: верх 0 при прокрутке 2600–4400 (окно 900)
    ys = [0, 450, 900, 1350, 1800, 2250, 2700, 3150, 3600, 4050, 4500, 4950]
    snaps = [{"y": y, "v": [[(2600 - y) if y <= 2600 else (0 if y <= 4400 else 4400 - y), 900, "k" if 2600 < y < 4400 else "r"],
                            [0.0, 80, "f"]]} for y in ys]
    pins, fixed = detect_pins([{"sel": "div.sticky", "depth": 4}, {"sel": "header", "depth": 2}], snaps, 900)
    check("закрепление 2600–4400 px = 200 vh, sticky; шапка — постоянный слой",
          ([(p["start_px"], p["end_px"], p["mechanism"]) for p in pins], len(fixed)), ([(2600.0, 4400.0, "sticky")], 1))
    # отсев: защита и вход
    cases = [(403, {}, {"title": "", "n": 4000}), (200, {"cf-mitigated": "challenge"}, {"title": "x", "n": 4000}),
             (200, {}, {"title": "Just a moment...", "n": 120, "cf": True}), (429, {}, {}),
             (200, {}, {"title": "", "n": 300, "fr": "https://newassets.hcaptcha.com/captcha/v1/x"}),
             (200, {}, {"title": "Войти", "n": 400, "pw": 1}), (200, {}, {"title": "Студия", "n": 5000, "fr": "https://www.google.com/recaptcha/api2/anchor"})]
    check("отсев: 403, cf-mitigated, «Just a moment», 429, hCaptcha, вход, обычная страница с reCAPTCHA формы",
          [(closed_status(h, hd, s, "https://x.test/") or ["—"])[0] for h, hd, s in cases], ["blocked", "blocked", "blocked", "blocked", "blocked", "login", "—"])
    # библиотеки по содержимому файла
    libs = {}
    blob = b'/* x */ (h.gsapVersions||(h.gsapVersions=[])).push(Fe.version); te.version=Gt.version=Fe.version="3.15.0"; G.classList.add("pin-spacer")'
    for lib, rx, vrx in LIB_SIGS:
        if re.search(rx, blob):
            m_ = re.search(vrx, blob) if vrx else None
            libs[lib] = m_.group(1).decode() if m_ else None
    check("сниффер: gsap 3.15.0 и ScrollTrigger по строкам из кода библиотек", libs, {"gsap": "3.15.0", "ScrollTrigger": None})
    # схема и сравнение
    try:
        import jsonschema
        sch = json.load(open(SCHEMA, encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(sch)
        check("motion-passport.schema.json — JSON Schema 2020-12", True, True)
        V = jsonschema.Draft202012Validator(sch)
    except Exception as e:
        check(f"motion-passport.schema.json — JSON Schema 2020-12 ({e})", False, True)
        V = None
    th = compare_thresholds()
    check("пороги сравнения — x-compare схемы", sorted(th), ["count", "curve_rmse", "delay_ms", "duration_pct", "length_vh", "stagger_ms"])
    closed = assemble({"closed": ["blocked", "HTTP 403"], "http": 403}, _ns(), "https://x.test/", "https://x.test/", False)
    closed["files"] = {}
    if V:
        errs = [e.message for e in V.iter_errors(closed)]
        check("паспорт «закрыто защитой» проходит схему", errs, [])
    tmp = kbpaths.out("creative", "motion-probe", "_selftest")
    pa = {"passport_version": "1.0", "id": "ref-1", "viewport": {"height": 900},
          "moments": [{"id": "m01-h1", "class": "one-shot", "trigger": {"type": "load"}, "duration_ms": 800, "delay_ms": 0,
                       "easing": {"bezier": [0.17, 1, 0.31, 1]}, "target": {"count": 1}},
                      {"id": "m02-li", "class": "one-shot", "trigger": {"type": "in-view"}, "duration_ms": 600, "delay_ms": 40,
                       "easing": {"named": "power2.out"}, "stagger": {"each_ms": 80}, "target": {"count": 5}},
                      {"id": "m03-img", "class": "scroll-linked", "trigger": {"type": "scroll-scrub"}, "scroll": {"length_vh": 100},
                       "easing": {"named": "linear"}, "target": {}}],
          "pins": [{"id": "p01", "length_vh": 200}]}
    pb = json.loads(json.dumps(pa))
    pb["id"] = "proto-1"
    pb["moments"][0]["duration_ms"] = 1100                      # +37,5 % — далеко
    pb["moments"][1]["stagger"]["each_ms"] = 90                 # +10 мс — близко
    pb["pins"][0]["length_vh"] = 230                            # +30 vh — заметно
    fa, fb = os.path.join(str(tmp), "a.json"), os.path.join(str(tmp), "b.json")
    json.dump(pa, open(fa, "w", encoding="utf-8"))
    json.dump(pb, open(fb, "w", encoding="utf-8"))
    r = compare_docs(fa, fb)
    check("сравнение паспортов: длительность +37,5 % — далеко, стаггер +10 мс — близко, закрепление +30 vh — заметно",
          (r["pairs"][0]["metrics"]["duration_pct"], r["pairs"][0]["verdict"], r["pairs"][1]["bands"].get("stagger_ms"), r["pins"][0]["band"], r["verdict"]),
          (37.5, "далеко", "близко", "заметно", "далеко"))
    spec = {"motion_spec_version": "1.0", "id": "demo", "page": {"base": {"duration_ms": 400, "easing": {"token": "motion.marketing.easing.out-expo"}}},
            "sections": [{"id": "hero", "moments": [{"id": "hero-title", "class": "one-shot", "target": "hero.headline", "trigger": {"type": "load"},
                                                     "duration": {"share": 2}, "source": {"ref": "ref-1", "moment": "m01-h1", "take": ["duration"]}},
                                                    {"id": "hero-cta", "class": "one-shot", "target": "hero.cta", "trigger": {"type": "load", "delay_ms": 80},
                                                     "duration": {"token": "motion.marketing.duration.reveal"}}]}]}
    fs = os.path.join(str(tmp), "s.yaml")
    import yaml
    yaml.safe_dump(spec, open(fs, "w", encoding="utf-8"), allow_unicode=True)
    r2 = compare_docs(fa, fs)
    p0 = next(x for x in r2["pairs"] if x["b"] == "hero-title")
    check("паспорт против motion-spec: пара по source.moment, 800 мс = 0,4 с × 2, кривая ≈ токен out-expo — близко",
          (p0["a"], p0["how"], p0["metrics"]["duration_pct"], p0["bands"]["curve_rmse"]), ("m01-h1", "source.moment", 0.0, "близко"))
    p1 = next(x for x in r2["pairs"] if x["b"] == "hero-cta")
    check("паспорт против motion-spec: второй момент — по порядку, 600 → 560 мс (токен reveal) −6,7 % — близко",
          (p1["a"], p1["how"], p1["metrics"]["duration_pct"], p1["bands"]["duration_pct"]), ("m02-li", "порядок", -6.7, "близко"))
    pd, pm = passport_id("", "https://gsap.com/", False), passport_id("", "https://gsap.com/", False, True)
    check("id паспорта: с телефона — «-mobile» и свой хеш, оба по шаблону схемы",
          (pd != pm, pm.startswith("gsap.com-mobile-"), all(re.fullmatch(r"[a-z0-9][a-z0-9.-]*-[0-9a-f]{8}", x) for x in (pd, pm))),
          (True, True, True))
    if no_browser:
        print(f"\n{VERSION} (без браузера)")
        return 0 if ok else 1
    # тестовые страницы в браузере (без сети): сервер motion_check раздаёт папку фикстур
    with kbpaths.lock("browser"):
        browser_tests(check, near, V)
    print(f"\n{VERSION}")
    return 0 if ok else 1


def browser_tests(check, near, V):
    out = str(kbpaths.out("creative", "motion-probe", "_selftest"))

    def run(name, **kw):
        a = _ns(target=os.path.join(FIXTURES, name), out=os.path.join(out, os.path.splitext(name)[0] + ("-clock" if kw.get("clock") else "")), **kw)
        code, p = probe_core(a)
        if V:
            errs = [f"{'/'.join(str(x) for x in e.absolute_path)}: {e.message}"[:160] for e in V.iter_errors(p)]
            check(f"{name}{' --clock' if kw.get('clock') else ''}: паспорт проходит схему", errs[:3], [])
        return code, p

    def by_kind(p, kind, **f):
        return [m for m in p["moments"] if m["kind"] == kind and all(m.get(k) == v for k, v in f.items())]
    # 1. время: CSS-анимация, переход, WAAPI, аниматор на rAF через инлайн-стили
    for clock in (False, True):
        tag = " --clock" if clock else ""
        code, p = run("time.html", settle_ms=400, scroll_step=0.5, max_s=30, clock=clock, virtual_steps=1)
        check(f"time.html{tag}: код 0, статус снято", (code, p["status"]["code"]), (0, "ok"))
        ca = by_kind(p, "css-animation")
        check(f"time.html{tag}: CSS-анимация h1 — 700 мс, задержка 100, cubic-bezier(0.16, 1, 0.3, 1), загрузка",
              [(m["target"]["tag"], m["duration_ms"], m["declared"]["delay_ms"], m["easing"]["css"], m["trigger"]["type"]) for m in ca],
              [("h1", 700.0, 100.0, "cubic-bezier(0.16, 1, 0.3, 1)", "load")])
        tr = by_kind(p, "css-transition")
        check(f"time.html{tag}: переход — один момент, transform 400 мс ease-out и opacity 300 мс linear",
              [(m["duration_ms"], sorted((t["property"], t.get("duration_ms"), (t.get("easing") or {}).get("css")) for t in m["tracks"])) for m in tr],
              [(400.0, [("opacity", 300.0, "linear"), ("translateX", 400.0, "ease-out")])])
        wa = by_kind(p, "waapi")
        check(f"time.html{tag}: WAAPI — 900 мс, задержка 200, ease-in-out, 2 итерации alternate",
              [(m["duration_ms"], m["declared"]["delay_ms"], m["easing"]["css"], m["repeat"]["iterations"], m["repeat"]["direction"]) for m in wa],
              [(900.0, 200.0, "ease-in-out", 2, "alternate")])
        il = [m for m in by_kind(p, "inline-style") if m["class"] == "one-shot"]
        g = next((m for m in il if (m.get("stagger") or {}).get("count") == 5), None)
        check(f"time.html{tag}: инлайн-стили — одна группа из 5 карточек", (len(il), bool(g)), (1, True))
        if g:
            tol = 4.0 if clock else 12.0     # конец кривой out виден до последнего изменения значения в записи
            near(f"time.html{tag}: стаггер 80 мс", g["stagger"]["each_ms"], 80.0, 1.5 if clock else 8.0)
            near(f"time.html{tag}: длительность 600 мс", g["duration_ms"], 600.0, tol)
            check(f"time.html{tag}: кривая power2.out (easeOutCubic), ошибка bezier < 0,02",
                  (g["easing"]["named"], g["easing"]["bezier_error"] < 0.02), ("power2.out", True))
            check(f"time.html{tag}: дорожки сдвиг Y 40 → 0 px и прозрачность 0 → 1",
                  sorted((t["property"], round(t["from"]), round(t["to"])) for t in g["tracks"]), [("opacity", 0, 1), ("translateY", 40, 0)])
    # 2. прокрутка: scroll-driven, закрепление sticky, скраб инлайн-стилями (сразу и со сглаживанием), появление в зоне видимости
    code, p = run("scroll.html", settle_ms=800, scroll_step=0.5, max_s=60)
    check("scroll.html: код 0", code, 0)
    spin = [m for m in by_kind(p, "inline-style") if m["target"]["selector"] == "div#badge.badge"]
    check("scroll.html: значок, который вращается без остановки, — петля по кругу, а не скраб",
          [(m["class"], (m.get("repeat") or {}).get("kind")) for m in spin], [("loop", "cycle")])
    if spin:
        near("scroll.html: скорость вращения значка 90°/с", (spin[0].get("repeat") or {}).get("speed_px_s"), 90.0, 3.0)
    sd = [m for m in by_kind(p, "css-animation") if m["class"] == "scroll-linked"]
    check("scroll.html: CSS scroll-driven view() — entry 0 % … cover 50 % = 1350–1850 px",
          [(m["scroll"]["start_px"], m["scroll"]["end_px"]) for m in sd], [(1350.0, 1850.0)])
    pins = p["pins"]
    check("scroll.html: одно закрепление sticky", [(x["mechanism"], x["evidence"]) for x in pins], [("sticky", "geometry")])
    if pins:
        near("scroll.html: начало закрепления 2600 px", pins[0]["start_px"], 2600.0, 3.0)
        near("scroll.html: длина закрепления 200 vh", pins[0]["length_vh"], 200.0, 1.0)
    sc = {m["target"]["selector"]: m for m in by_kind(p, "inline-style") if m["class"] == "scroll-linked"}
    bar, bar2 = sc.get("div#bar.bar"), sc.get("div#bar2.bar.bar2")
    check("scroll.html: два скраба инлайн-стилями", (bool(bar), bool(bar2)), (True, True))
    if bar:
        near("scroll.html: скраб — начало 2600 px", bar["scroll"]["start_px"], 2600.0, 6.0)
        near("scroll.html: скраб — конец 4400 px", bar["scroll"]["end_px"], 4400.0, 6.0)
        check("scroll.html: скраб линеен (R² ≥ 0,999), догон ≤ 40 мс",
              (bar["scroll"]["linearity_r2"] >= 0.999, (bar["scroll"].get("smoothing_ms") or 0) <= 40), (True, True))
    if bar2:
        check("scroll.html: скраб со сглаживанием — догон 300–800 мс", 300 <= (bar2["scroll"].get("smoothing_ms") or 0) <= 800, True)
    rv = [m for m in by_kind(p, "inline-style") if m["class"] == "one-shot" and m["trigger"]["type"] == "in-view"]
    g = next((m for m in rv if (m.get("stagger") or {}).get("count") == 4), None)
    check("scroll.html: появление в зоне видимости — 4 карточки со стаггером", bool(g), True)
    if g:
        near("scroll.html: появление — стаггер 80 мс", g["stagger"]["each_ms"], 80.0, 8.0)
        near("scroll.html: появление — 500 мс", g["duration_ms"], 500.0, 12.0)
        check("scroll.html: появление — power2.out", g["easing"]["named"], "power2.out")
    # 3. подложные GSAP, ScrollTrigger и Lenis с известными числами
    code, p = run("gsap-fake.html", settle_ms=300, scroll_step=0.66, max_s=30)
    lib = {x["name"]: x.get("version") for x in p["libraries"]}
    check("gsap-fake.html: gsap 3.12.5, ScrollTrigger 3.12.5, lenis 1.3.27",
          (lib.get("gsap"), lib.get("ScrollTrigger"), lib.get("lenis")), ("3.12.5", "3.12.5", "1.3.27"))
    sm = p["smooth_scroll"]
    check("gsap-fake.html: плавная прокрутка lenis, экземпляр app.smooth, lerp 0,1",
          (sm.get("kind"), sm.get("global"), (sm.get("options") or {}).get("lerp")), ("lenis", "app.smooth", 0.1))
    gs = by_kind(p, "gsap")
    rev = next((m for m in gs if m["class"] == "one-shot"), None)
    scr = next((m for m in gs if m["class"] == "scroll-linked"), None)
    check("gsap-fake.html: твин появления — 3 цели, 1200 мс, задержка 300, power3.out, стаггер 80 мс",
          None if not rev else (rev["target"]["count"], rev["duration_ms"], rev["declared"]["delay_ms"], rev["easing"]["declared"], rev["stagger"]["each_ms"]),
          (3, 1200.0, 300.0, "power3.out", 80.0))
    check("gsap-fake.html: скраб ScrollTrigger — 1000–2800 px = 200 vh, scrub 1, в закреплении",
          None if not scr else (scr["scroll"]["start_px"], scr["scroll"]["end_px"], scr["scroll"]["length_vh"], scr["scroll"]["scrub"], scr["trigger"]["type"]),
          (1000, 2800, 200.0, 1, "pin-scrub"))
    check("gsap-fake.html: закрепление из ScrollTrigger 200 vh, станции snap 1000/1600/2200/2800",
          ([(x["evidence"], x["length_vh"]) for x in p["pins"]], [s["scroll_px"] for s in p["stations"] if s["kind"] == "snap"]),
          ([("scrolltrigger", 200.0)], [1000.0, 1600.0, 2200.0, 2800.0]))
    # 4. страница проверки антибота — отсев, код 3
    code, p = run("challenge.html", settle_ms=200, max_s=20)
    check("challenge.html: «Just a moment» → закрыто защитой, код 3", (code, p["status"]["code"]), (EXIT_CLOSED, "blocked"))


# =====================================================================================================================
# 17. CLI
# =====================================================================================================================
def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if argv[0] == "--version":
        print(VERSION)
        return 0
    if argv[0] == "--selftest":
        return selftest(no_browser="--no-browser" in argv[1:])
    if argv[0] == "probe":
        p = argparse.ArgumentParser(prog="motion_probe.py probe", description="замер движения референса → паспорт движения")
        p.add_argument("target", help="адрес или локальный HTML")
        p.add_argument("--out", help="папка паспорта (по умолчанию $DDD_HOME/out/creative/motion-probe/<хост>-<хеш>/)")
        p.add_argument("--viewport", default="1440x900", help="окно ШxВ (по умолчанию 1440x900)")
        p.add_argument("--mobile", action="store_true", help="телефон: дескриптор budgets.yaml site, UA — HeadlessChrome")
        p.add_argument("--scroll-step", type=float, default=0.33, help="шаг колеса — доля высоты окна (0,33)")
        p.add_argument("--settle-ms", type=int, default=1200, help="пауза после успокоения прокрутки, мс (1200)")
        p.add_argument("--max-s", type=float, default=60.0, help="предел замера, с (60)")
        p.add_argument("--frames", action="store_true", help="контактный лист кадров станций и закреплений")
        p.add_argument("--clock", action="store_true", help="поддельные часы page.clock: анимации скриптом кадрами по 16 мс")
        p.add_argument("--no-lock", action="store_true", help="без замка браузера")
        p.add_argument("--json", action="store_true", help="напечатать паспорт целиком")
        p.add_argument("--locale", default="ru-RU")
        p.add_argument("--root", help="корень раздачи локальной страницы")
        a = p.parse_args(argv[1:])
        m = re.match(r"^(\d{3,4})[x×](\d{3,4})$", a.viewport)
        if not m:
            p.error("--viewport ШxВ, например 1440x900")
        a.vw, a.vh = int(m.group(1)), int(m.group(2))
        a.virtual_steps = 8
        if not 0.05 <= a.scroll_step <= 1.5:
            p.error("--scroll-step — доля окна от 0,05 до 1,5")
        try:
            return run_probe(a)
        except SystemExit:
            raise
        except Exception as e:
            log(f"ошибка замера: {e}")
            return 2
    if argv[0] == "compare":
        p = argparse.ArgumentParser(prog="motion_probe.py compare", description="паспорт движения против паспорта или motion-spec")
        p.add_argument("a", help="паспорт (passport.json) или motion-spec (YAML/JSON) — база сравнения")
        p.add_argument("b", help="паспорт или motion-spec — что сверяем")
        p.add_argument("--json", action="store_true")
        p.add_argument("--out", help="папка для compare.md и compare.json")
        return run_compare(p.parse_args(argv[1:]))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
