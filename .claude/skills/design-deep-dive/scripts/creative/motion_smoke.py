#!/usr/bin/env python3
"""motion_smoke.py — живая проверка набора движения страницы (kb/creative/11-motion-code/examples) в Chromium и
статическая проверка его кода.

    python3 motion_smoke.py [--root DIR] [--page demo.html] [--modes static,desk,rm,reduced,paused,nojs,phone,demos]
                            [--shots] [--json ОТЧЁТ]
    python3 motion_smoke.py --selftest

Страница — `examples/demo.html` (`--root`, `--page` — своя страница с тем же DOM-контрактом). Прогоны и что годно:
  static   — без браузера: motion-kit.js не строит DOM (innerHTML, appendChild, cloneNode, createElement, textContent =
             и т. п.), не ходит в сеть (fetch, XMLHttpRequest, import(), WebSocket, sendBeacon), не модуль (без export и
             import), одно глобальное имя MotionKit; пружина дословно та же, что у рантайма сцен 3D; переменные токенов в
             motion-kit.css есть в marketing-tokens.json; нет общего reduce «* { animation-duration: .01ms }»; пример
             артборда — по формату холста (строка support.js, <helmet>, корень, class Component extends DCLogic, destroy в
             componentWillUnmount, без построения DOM);
  desk     — 1440×900: проход прокруткой — все появления в конечном состоянии (непрозрачность 1, без смещения, маска
             открыта), невидимого текста 0; порядок стаггера по --i / sibling-index(), шаг 40–80 мс, сумма ≤ 600 мс;
             счётчики дошли до чисел; бегущая строка 30–60 px/с, стоит при наведении, вне экрана и по паузе; пауза
             останавливает все петли и возвращает выбор; переключатель «Меньше» / «Полное» / «Как в системе»; такты сцены
             beats по одному, пружина без перелёта садится на точку покоя; скраб монотонен; магнит ≤ 8 px, наклон ≤ 7°;
             долгие кадры прокрутки ≤ 2 % окна; ни одного запроса наружу, ошибок и предупреждений консоли нет;
  rm       — prefers-reduced-motion: reduce: режим reduced, до прокрутки ничего не скрыто, ни одной бегущей бесконечной
             анимации, сцены без закрепления и в конечном кадре, дубль строки скрыт;
  reduced  — выбор «Меньше» (data-motion="reduced" из localStorage) при системном «без предпочтений»: то же, что rm;
  paused   — пауза из sessionStorage: петли стоят, появления и сцены работают;
  nojs     — JavaScript выключен: корня набора нет, весь текст видим, счётчики — итоговые числа, сцены без закрепления;
  phone    — 390×844, тач: указатель не двигает ничего, горизонталь — родная лента, нет горизонтального переполнения,
             петель в окне ≤ 1, все появления сработали;
  demos    — страницы examples/demos/*.html: якоря эффектов из primitives.yaml на месте, ошибок и сети наружу нет,
             появления сработали, предупреждений бюджета нет.
Вердикт — `ok` и `findings` у каждого прогона и общее `ok`; код 0 — всё годно, 1 — нет. `--shots` — кадры в
`$DDD_HOME/out/creative/motion-smoke/`. Замок браузера утилита берёт сама (kbpaths.lock("browser")). Прогон всех
режимов — около четырёх минут.
"""
from __future__ import annotations

import functools
import http.server
import json
import math
import os
import re
import socketserver
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

FOLDER = kbpaths.kb("creative", "11-motion-code")
ROOT = FOLDER / "examples"
TOKENS = kbpaths.kb("creative", "04-visual-language", "marketing-tokens.json")
STAGE_RUNTIME = kbpaths.kb("3d", "16-js-scenes", "examples", "stage-runtime.js")
MODES = ("static", "desk", "rm", "reduced", "paused", "nojs", "phone", "demos")
REVEAL = ("rise", "unmask", "split", "sweep", "scale-in", "draw", "count")
# Запрещённое в коде набора: построение и перенос узлов, запись текста, сеть, модули, исполнение строк.
FORBIDDEN = [
    (r"\.innerHTML\b|\.outerHTML\b|insertAdjacentHTML|document\.write", "строит разметку строкой"),
    (r"\.(appendChild|insertBefore|replaceChild|removeChild|replaceChildren)\s*\(", "переносит узлы"),
    (r"\.(append|prepend|before|after|replaceWith)\s*\(", "переносит узлы"),
    (r"\bcreateElement(NS)?\s*\(|createTextNode|createDocumentFragment|\.cloneNode\s*\(|\.importNode\s*\(", "создаёт узлы"),
    (r"\.(textContent|innerText|nodeValue)\s*=(?!=)", "переписывает текст"),
    (r"\bfetch\s*\(|XMLHttpRequest|\bWebSocket\b|EventSource|sendBeacon|\bimport\s*\(|importScripts|new\s+Worker", "ходит в сеть"),
    (r"^\s*(export|import)\s", "модуль, а не классический скрипт"),
    (r"\beval\s*\(|new\s+Function\s*\(", "исполняет строку"),
]
SEL = "(el) => { if (!el || !el.tagName) return ''; const m = el.getAttribute('data-moment'); return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (m ? '[' + m + ']' : (el.getAttribute('data-mk') ? '{' + el.getAttribute('data-mk') + '}' : '')); }"
INIT = """(() => { window.__ms = {loaf: []};
  try { new PerformanceObserver(l => l.getEntries().forEach(e => __ms.loaf.push([e.startTime, e.duration])))
    .observe({type: 'long-animation-frame', buffered: true}); } catch (e) {} })();"""
HIDDEN_JS = """() => { const sel = """ + SEL + """;
  const OK = '[data-mk-k]:not([data-on]), [data-mk-seg]:not([data-on]), dialog:not([open]), details:not([open]) > :not(summary), [data-mk-story], [hidden], [data-mk~="text-mask"], script, style, noscript, template';
  const op = (el) => { let o = 1; for (let n = el; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity); return o; };
  const out = [];
  for (const el of document.body.querySelectorAll('*')) {
    if (el.closest(OK)) continue;
    if (!Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 1)) continue;
    const cs = getComputedStyle(el); if (cs.display === 'none') continue;
    const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
    const fill = cs.webkitTextFillColor || '';
    if (op(el) < 0.05 || cs.visibility === 'hidden' || /rgba\\(\\d+, \\d+, \\d+, 0\\)/.test(fill)) out.push(sel(el));
  }
  return out; }"""
FINAL_JS = """() => { const sel = """ + SEL + """, R = """ + json.dumps(list(REVEAL)) + """;
  const id = (t) => t === 'none' || /^matrix\\(1, 0, 0, 1, 0, 0\\)$/.test(t);
  const full = (document.documentElement.getAttribute('data-mk-on') || '') === 'full'; const bad = []; let n = 0;
  for (const el of document.querySelectorAll('[data-mk]')) {
    const w = (el.getAttribute('data-mk') || '').split(/\\s+/); if (!w.some(x => R.includes(x))) continue;
    const cs = getComputedStyle(el); if (cs.display === 'none') continue; n++;
    const s = sel(el);
    if (full && !el.hasAttribute('data-mk-in')) bad.push(s + ': не появился');
    if (parseFloat(cs.opacity) < 0.99) bad.push(s + ': opacity ' + cs.opacity);
    if (!id(cs.transform)) bad.push(s + ': transform ' + cs.transform.slice(0, 40));
    if (/100%/.test(cs.clipPath)) bad.push(s + ': маска закрыта ' + cs.clipPath.slice(0, 40));
    if (w.includes('split')) for (const p of el.children) { const c = getComputedStyle(p); if (!id(c.transform) || /100%/.test(c.clipPath)) { bad.push(s + ': кусок не на месте'); break; } }
    if (w.includes('sweep')) { const i = el.querySelector('[data-mk-inner]'); if (i && !id(getComputedStyle(i).transform)) bad.push(s + ': внутренний масштаб'); }
    if (w.includes('draw')) for (const p of el.querySelectorAll('[pathLength]')) { const o = parseFloat(getComputedStyle(p).strokeDashoffset); if (o > 0.01) { bad.push(s + ': линия не дорисована ' + o); break; } }
    if (w.includes('count') && full) { const v = getComputedStyle(el).getPropertyValue('--mk-num').trim(), to = getComputedStyle(el).getPropertyValue('--mk-to').trim();
      if (v !== to || !el.hasAttribute('data-mk-done')) bad.push(s + ': счёт ' + v + ' из ' + to + (el.hasAttribute('data-mk-done') ? '' : ', не дошёл')); }
  }
  return {n, bad}; }"""
STAGGER_JS = """() => { const sel = """ + SEL + """, out = [];
  const ms = (v) => { const x = String(v).split(',')[0].trim(); return x.endsWith('ms') ? parseFloat(x) : parseFloat(x) * 1000; };
  for (const g of document.querySelectorAll('[data-mk-stagger]')) {
    const it = Array.from(g.children).filter(c => c.hasAttribute('data-mk'));
    if (it.length < 2 || it.some(c => c.getAttribute('data-mk-in') === 'instant')) continue;
    out.push({group: sel(g), k: it.map(c => +getComputedStyle(c).getPropertyValue('--mk-k')), idx: it.map(c => Array.from(c.parentElement.children).indexOf(c)),
      d: it.map(c => ms(getComputedStyle(c).transitionDelay)), kind: 'group'}); }
  for (const g of document.querySelectorAll('[data-mk~="split"]')) {
    if (g.getAttribute('data-mk-in') === 'instant') continue; const it = Array.from(g.children); if (it.length < 2) continue;
    out.push({group: sel(g), k: it.map(c => +getComputedStyle(c).getPropertyValue('--mk-k')), idx: it.map((c, i) => i),
      d: it.map(c => ms(getComputedStyle(c).transitionDelay)), dur: ms(getComputedStyle(it[0]).transitionDuration), kind: 'split'}); }
  return out; }"""
LOOPS_JS = """() => document.getAnimations().filter(a => { let t = {}; try { t = a.effect.getTiming(); } catch (e) {} return t.iterations === Infinity && a.playState === 'running'; }).length"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(root):
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(root)))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def launch(pw):
    try:
        return pw.chromium.launch(channel="chromium")
    except Exception:  # noqa: BLE001 — сборка Playwright без канала chromium
        return pw.chromium.launch()


# ---------------------------------------------------------------------------------------------- пружина и статика
def spring(x, v, target, w, dt):
    """Та же пружина, что в motion-kit.js и stage-runtime.js: критически демпфированная, точное решение за шаг."""
    d = x - target
    e = math.exp(-w * dt)
    c = v + w * d
    return target + (d + c * dt) * e, (v - w * c * dt) * e


def spring_run(w, dt, t_end, x=0.0, target=1.0):
    v, t, out = 0.0, 0.0, []
    while t < t_end - 1e-12:
        x, v = spring(x, v, target, w, dt)
        t += dt
        out.append((t, x))
    return out


def fn_text(src, name):
    """Тело функции name без комментариев и пробелов — для сверки «дословно»."""
    m = re.search(r"function\s+" + name + r"\s*\([^)]*\)\s*\{(.*?)\n\s*\}", src, re.S)
    if not m:
        return None
    body = re.sub(r"//[^\n]*", "", m.group(0))
    return re.sub(r"\s+", "", body)


def forbidden(src):
    """Находки запрещённых API в коде без комментариев: [(строка, что)]."""
    clean = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    out = []
    for i, line in enumerate(clean.splitlines(), 1):
        code = re.sub(r"//.*$", "", line)
        code = re.sub(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", "''", code)
        for rx, what in FORBIDDEN:
            if re.search(rx, code):
                out.append((i, what))
    return out


def token_vars(css, tokens):
    """Переменные --motion-marketing-* в CSS без токена в marketing-tokens.json."""
    names = set()

    def walk(node, path):
        if isinstance(node, dict):
            if "$value" in node:
                names.add("--" + "-".join(path))
                return
            for k, v in node.items():
                if not k.startswith("$"):
                    walk(v, path + [k])
    walk(tokens.get("motion", {}), ["motion"])
    used = set(re.findall(r"--motion-marketing-[a-z0-9-]+", css))
    return sorted(used - names), sorted(used)


def artboard_findings(html, css=None):
    bad = []
    if css is not None:                                    # вырезка CSS набора в <helmet> — строки motion-kit.css без правок
        m = re.search(r"/\* motion-kit\.css: начало вырезки[^*]*\*/(.*?)/\* motion-kit\.css: конец вырезки \*/", html, re.S)
        lines = {x.strip() for x in css.splitlines()}
        drift = [x.strip() for x in (m.group(1) if m else "").splitlines() if x.strip() and x.strip() not in lines]
        if not m:
            bad.append("в <helmet> нет вырезки motion-kit.css между метками")
        elif drift:
            bad.append(f"вырезка CSS разошлась с motion-kit.css: {len(drift)} строк, первая — {drift[0][:60]}")
    if '<script src="./support.js"></script>' not in html:
        bad.append("нет строки support.js дословно")
    if '<script src="./lib/motion-kit.js"></script>' not in html:
        bad.append("набор не подключён файлом поддержки ./lib/motion-kit.js")
    elif html.index('./lib/motion-kit.js') < html.index('./support.js'):
        bad.append("файл набора раньше support.js")
    for need, what in (("<x-dc>", "<x-dc>"), ("<helmet>", "<helmet>"), ('type="text/x-dc"', "блок логики text/x-dc"),
                       ("class Component extends DCLogic", "class Component extends DCLogic"), ("renderVals()", "renderVals()"),
                       ("componentWillUnmount", "componentWillUnmount"), ("MotionKit.mount(", "MotionKit.mount"),
                       (".destroy()", "destroy() набора"), ('ref="{{', "ref корня")):
        if need not in html:
            bad.append(f"нет {what}")
    if re.search(r"innerHTML|appendChild|insertAdjacentHTML|<iframe|<object|<embed", html):
        bad.append("строит интерфейс скриптом или встраивает чужую страницу")
    return bad


def static_check(root=ROOT):
    res = {"findings": []}
    js_p, css_p = Path(root) / "motion-kit.js", Path(root) / "motion-kit.css"
    js = js_p.read_text(encoding="utf-8") if js_p.is_file() else ""
    css = css_p.read_text(encoding="utf-8") if css_p.is_file() else ""
    res["forbidden"] = [f"motion-kit.js:{i}: {w}" for i, w in forbidden(js)]
    res["globals"] = sorted(set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", js)))
    rt = STAGE_RUNTIME.read_text(encoding="utf-8") if STAGE_RUNTIME.is_file() else ""
    res["spring_same"] = bool(js) and bool(rt) and fn_text(js, "spring") == fn_text(rt, "spring")
    miss, used = token_vars(css, json.loads(TOKENS.read_text(encoding="utf-8")))
    res["token_vars"], res["token_vars_missing"] = len(used), miss
    res["global_reduce"] = bool(re.search(r"\*\s*(,[^{]*)?\{[^}]*animation-duration\s*:\s*\.?0*\.01m?s", css))
    ab = Path(root) / "artboard-adapter.dc.html"
    res["artboard"] = artboard_findings(ab.read_text(encoding="utf-8"), css) if ab.is_file() else ["нет artboard-adapter.dc.html"]
    return res


# ---------------------------------------------------------------------------------------------- живые прогоны
def wire(pg, base):
    errs, ext = [], []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:160]))
    pg.on("console", lambda m: errs.append(f"{m.type}: {m.text[:160]}") if m.type in ("error", "warning") else None)
    pg.on("request", lambda r: ext.append(r.url[:120]) if not (r.url.startswith(base) or r.url.startswith("data:")) else None)
    return errs, ext


def info(pg):
    return pg.evaluate("() => window.__mk ? window.__mk.info() : null")


def wheel_pass(pg, step=300, gap=0.11, cap=260):
    """Колесом до дна; доля долгих кадров (LoAF ≥ 50 мс) за проход; максимум петель в окне по info()."""
    t0 = pg.evaluate("performance.now()")
    pg.mouse.move(720, 450)
    loops, k = 0, 0
    while k < cap:
        pg.mouse.wheel(0, step)
        time.sleep(gap)
        k += 1
        if k % 4 == 0:
            i = info(pg)
            loops = max(loops, (i or {}).get("loopsInView") or 0)
        if pg.evaluate("innerHeight + scrollY >= document.documentElement.scrollHeight - 2"):
            break
    time.sleep(1.8)
    t1 = pg.evaluate("performance.now()")
    loaf = pg.evaluate("() => (window.__ms && window.__ms.loaf) || []")
    long_ms = sum(d for s, d in loaf if s >= t0 and d >= 50)
    return {"steps": k, "ms": round(t1 - t0), "loaf_pct": round(100 * long_ms / max(1, t1 - t0), 2), "loops_max": loops}


def js_pass(pg, step=320, gap=0.1, cap=260):
    """То же для телефона: прокрутка скриптом (колесо у тач-эмуляции не ходит)."""
    loops, k = 0, 0
    while k < cap:
        pg.evaluate(f"window.scrollBy(0, {step})")
        time.sleep(gap)
        k += 1
        if k % 4 == 0:
            loops = max(loops, (info(pg) or {}).get("loopsInView") or 0)
        if pg.evaluate("innerHeight + scrollY >= document.documentElement.scrollHeight - 2"):
            break
    time.sleep(1.8)
    return {"steps": k, "loops_max": loops}


def scroll_to(pg, sel, offset=0):
    pg.evaluate(f"(() => {{ const e = document.querySelector('{sel}'); if (e) window.scrollTo(0, e.getBoundingClientRect().top + scrollY - {offset}); }})()")
    time.sleep(1.0)


# Длительности и кривые появлений — по объектам CSSTransition сразу после срабатывания (точнее порогов выборки стилей).
TIMING = {"rise": {"opacity": 336, "transform": 560}, "unmask": {"transform": 800, "clip-path": 800},
          "sweep": {"clip-path": 800}, "scale-in": {"opacity": 400, "transform": 800, "filter": 560}, "count": {"--mk-num": 1200}}


def timing_check(pg, url):
    """Каждый примитив — на свежей загрузке: прыжок к первому экземпляру ниже первого экрана (что выше — пролетели)."""
    out = {}
    for prim in TIMING:
        pg.goto(url, wait_until="load")
        time.sleep(0.6)
        r = pg.evaluate("""async (p) => { const vh = innerHeight;
            const el = Array.from(document.querySelectorAll('[data-mk~="' + p + '"]')).find(e => !e.hasAttribute('data-mk-in') && e.getBoundingClientRect().top > vh * 1.1);
            if (!el) return null;
            el.scrollIntoView({block: 'center', behavior: 'instant'});
            for (let i = 0; i < 40 && !el.hasAttribute('data-mk-in'); i++) await new Promise(r => requestAnimationFrame(r));
            await new Promise(r => requestAnimationFrame(r));
            const tr = el.getAnimations().filter(a => a.transitionProperty);
            return {moment: el.getAttribute('data-moment') || el.tagName.toLowerCase(), t: tr.map(a => { const g = a.effect.getTiming();
              return {prop: a.transitionProperty, ms: Math.round(g.duration), delay: Math.round(g.delay), ease: g.easing}; })}; }""", prim)
        out[prim] = r
    pg.goto(url, wait_until="load")
    time.sleep(1.0)
    return out


def marquee_check(pg):
    out = {}
    if not pg.evaluate("!!document.querySelector('[data-mk~=\"marquee\"]')"):
        return {"present": False}
    scroll_to(pg, '[data-mk~="marquee"]', 300)
    time.sleep(1.6)                                                        # разгон от прокрутки гаснет
    dx = pg.evaluate("""async () => { const t = document.querySelector('[data-mk~="marquee"] [data-mk-track]'); const x0 = t.getBoundingClientRect().left;
        await new Promise(r => setTimeout(r, 1000)); return Math.abs(t.getBoundingClientRect().left - x0); }""")
    out["speed_px_s"] = round(dx, 1)
    box = pg.evaluate("(() => { const r = document.querySelector('[data-mk~=\"marquee\"]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
    pg.mouse.move(box[0], box[1])
    time.sleep(0.4)
    out["hover_paused"] = pg.evaluate("() => document.querySelector('[data-mk~=\"marquee\"] [data-mk-track]').getAnimations().every(a => a.playState === 'paused')")
    pg.mouse.move(5, 5)
    pg.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.6)
    out["offscreen_idle"] = pg.evaluate("() => { const m = document.querySelector('[data-mk~=\"marquee\"]'); return m.hasAttribute('data-mk-idle') && m.querySelector('[data-mk-track]').getAnimations().every(a => a.playState === 'paused'); }")
    return out


def pause_check(pg):
    if not pg.evaluate("!!document.querySelector('[data-mk~=\"pause\"]')"):
        return {"present": False}
    pg.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.5)
    before = pg.evaluate("document.documentElement.getAttribute('data-motion')")
    pg.click('[data-mk~="pause"]')
    time.sleep(0.5)
    st = pg.evaluate("() => ({attr: document.documentElement.getAttribute('data-motion'), pressed: document.querySelector('[data-mk~=\"pause\"]').getAttribute('aria-pressed')})")
    running = pg.evaluate(LOOPS_JS)
    pg.click('[data-mk~="pause"]')
    time.sleep(0.4)
    after = pg.evaluate("document.documentElement.getAttribute('data-motion')")
    return {"present": True, "attr": st["attr"], "pressed": st["pressed"], "running_infinite": running, "restored": after == before}


def toggle_check(pg):
    if not pg.evaluate("!!document.querySelector('[data-motion-set=\"reduced\"]')"):
        return {"present": False}
    pg.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.4)
    out = {"present": True}
    pg.click('[data-motion-set="reduced"]')
    time.sleep(0.6)
    out["reduced"] = {"on": pg.evaluate("document.documentElement.getAttribute('data-mk-on')"), "running_infinite": pg.evaluate(LOOPS_JS),
                      "final": pg.evaluate(FINAL_JS)["bad"][:4], "hidden": pg.evaluate(HIDDEN_JS)[:4]}
    pg.click('[data-motion-set="full"]')
    time.sleep(0.4)
    out["full_on"] = pg.evaluate("document.documentElement.getAttribute('data-mk-on')")
    pg.click('[data-motion-set=""]')
    time.sleep(0.4)
    out["system"] = {"attr": pg.evaluate("document.documentElement.getAttribute('data-motion')"),
                     "on": pg.evaluate("document.documentElement.getAttribute('data-mk-on')")}
    return out


def beats_check(pg, shots=None, tag="desk"):
    """Такты сцены beats колесом по 120 px: последовательность и пружина каждого такта (выборка 2,2 с)."""
    if not pg.evaluate("!!document.querySelector('[data-mk~=\"scene\"][data-mk-mode=\"beats\"]')"):
        return {"present": False}
    idx = pg.evaluate("Array.from(document.querySelectorAll('[data-mk~=\"scene\"]')).findIndex(s => s.getAttribute('data-mk-mode') === 'beats')")
    scroll_to(pg, '[data-mk~="scene"][data-mk-mode="beats"]', 72)
    pg.mouse.move(900, 450)
    seq, settle = [], []
    for _ in range(48):
        pg.mouse.wheel(0, 120)
        time.sleep(0.12)
        s = info(pg)["scenes"][idx]
        if seq and seq[-1] == s["beat"]:
            continue
        seq.append(s["beat"])
        t0, samp, cut = time.time(), [], None
        while time.time() - t0 < 2.4:
            x = info(pg)["scenes"][idx]
            samp.append((round(time.time() - t0, 3), x["cur"], x["target"]))
            if cut is None and s["beat"] == 1 and time.time() - t0 > 0.3:      # refresh() холста посреди доигрыша
                pg.evaluate("window.__mk.refresh()")
                y = info(pg)["scenes"][idx]
                cut = abs(y["cur"] - y["target"]) < 1e-3 and abs(x["cur"] - x["target"]) > 0.02
            time.sleep(0.04)
        tgt = samp[-1][2]
        start = samp[0][1]
        span = abs(tgt - start)
        t95 = next((t for t, c, _ in samp if span > 1e-3 and abs(c - start) >= 0.95 * span), None)
        mono = all((b[1] - a[1]) * (1 if tgt >= start else -1) >= -1e-4 for a, b in zip(samp, samp[1:]))
        over = max(((c - tgt) * (1 if tgt >= start else -1) for _, c, _ in samp), default=0)
        settle.append({"beat": s["beat"], "target": tgt, "end": samp[-1][1], "t95_s": t95, "monotonic": mono, "overshoot": round(over, 5),
                       "refresh_cut": cut})
        if shots:
            pg.screenshot(path=str(shots / f"{tag}-beat-{s['beat']}.png"))
        if s["beat"] >= len(info(pg)["scenes"][idx].get("beats") or []) - 1 and s["target"] == 1:
            break
    tempo = info(pg)["scenes"][idx]["tempo"]
    return {"present": True, "seq": seq, "settle": settle, "tempo": tempo}


def scrub_check(pg):
    if not pg.evaluate("!!document.querySelector('[data-mk~=\"scene\"][data-mk-mode=\"scrub\"]')"):
        return {"present": False}
    idx = pg.evaluate("Array.from(document.querySelectorAll('[data-mk~=\"scene\"]')).findIndex(s => s.getAttribute('data-mk-mode') === 'scrub')")
    scroll_to(pg, '[data-mk~="scene"][data-mk-mode="scrub"]', 72)
    pg.mouse.move(900, 450)
    samp = []
    for _ in range(8):
        pg.mouse.wheel(0, 120)
        for _ in range(3):
            time.sleep(0.04)
            x = info(pg)["scenes"][idx]
            samp.append((x["cur"], x["target"]))
    time.sleep(1.2)
    x = info(pg)["scenes"][idx]
    mono = all(b[0] - a[0] >= -1e-4 for a, b in zip(samp, samp[1:]))
    return {"present": True, "monotonic": mono, "end_gap": round(abs(x["cur"] - x["target"]), 5), "target": x["target"], "tempo": x["tempo"]}


def pointer_check(pg):
    out = {}
    if pg.evaluate("!!document.querySelector('[data-mk~=\"magnet\"]')"):
        pg.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.4)
        r = pg.evaluate("(() => { const e = document.querySelector('[data-mk~=\"magnet\"]'); e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        time.sleep(0.5)
        pg.mouse.move(r[0] + r[2] + 30, r[1] + r[3] / 2, steps=6)
        time.sleep(0.8)
        mx = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('[data-mk~=\"magnet\"]')).getPropertyValue('--mk-mx')) || 0")
        pg.mouse.move(5, 5, steps=4)
        time.sleep(0.9)
        back = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('[data-mk~=\"magnet\"]')).getPropertyValue('--mk-mx')) || 0")
        out["magnet_px"], out["magnet_back_px"] = round(mx, 2), round(back, 2)
    if pg.evaluate("!!document.querySelector('[data-mk~=\"tilt\"]')"):
        r = pg.evaluate("(() => { const e = document.querySelector('[data-mk~=\"tilt\"]'); e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
        time.sleep(0.5)
        pg.mouse.move(r[0] + r[2] * 0.95, r[1] + r[3] * 0.5, steps=6)
        time.sleep(0.9)
        out["tilt_ry_deg"] = round(pg.evaluate("parseFloat(getComputedStyle(document.querySelector('[data-mk~=\"tilt\"]')).getPropertyValue('--mk-ry')) || 0"), 2)
        pg.mouse.move(5, 5, steps=4)
    return out


def static_layout(pg):
    """Сцены и горизонталь в конечном кадре без закрепления; дубль строки скрыт."""
    return pg.evaluate("""() => ({
      sticky: Array.from(document.querySelectorAll('[data-mk~="scene"] > [data-mk-stage], [data-mk~="horizontal"] > [data-mk-stage]')).filter(s => getComputedStyle(s).position === 'sticky').length,
      p: Array.from(document.querySelectorAll('[data-mk~="scene"]')).map(s => getComputedStyle(s).getPropertyValue('--mk-p').trim()),
      dup_shown: Array.from(document.querySelectorAll('[data-mk~="marquee"] > [data-mk-track][aria-hidden="true"]')).filter(t => getComputedStyle(t).display !== 'none').length })""")


def run_mode(pw, base, page, mode, shots=None):
    b = launch(pw)
    try:
        kw = {"viewport": {"width": 1440, "height": 900}, "device_scale_factor": 1, "reduced_motion": "reduce" if mode == "rm" else "no-preference"}
        if mode == "nojs":
            kw["java_script_enabled"] = False
        if mode == "phone":
            kw = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True,
                  "user_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Mobile Safari/537.36",
                  "reduced_motion": "no-preference"}
        ctx = b.new_context(**kw)
        ctx.add_init_script(INIT)
        if mode == "reduced":
            ctx.add_init_script("try { localStorage.setItem('motion', 'reduced'); } catch (e) {}")
        if mode == "paused":
            ctx.add_init_script("try { sessionStorage.setItem('motion-paused', '1'); } catch (e) {}")
        pg = ctx.new_page()
        errs, ext = wire(pg, base)
        pg.goto(f"{base}/{page}", wait_until="load")
        time.sleep(1.4)
        r = {"mode": mode}
        if mode == "nojs":
            r["mk_on"] = pg.evaluate("document.documentElement.getAttribute('data-mk-on')")
            r["hidden"] = pg.evaluate(HIDDEN_JS)
            r["final"] = pg.evaluate(FINAL_JS)
            r["layout"] = static_layout(pg)
            r["errors"], r["external"] = errs, ext
            if shots:
                pg.screenshot(path=str(shots / f"{mode}-top.png"))
            return r
        r["start"] = info(pg)
        r["attr"] = pg.evaluate("document.documentElement.getAttribute('data-motion')")
        r["mk_on"] = pg.evaluate("document.documentElement.getAttribute('data-mk-on')")
        if mode in ("rm", "reduced"):
            r["hidden_before"] = pg.evaluate(HIDDEN_JS)
            r["final_before"] = pg.evaluate(FINAL_JS)
            r["running_infinite"] = pg.evaluate(LOOPS_JS)
            r["layout"] = static_layout(pg)
        if mode == "desk":
            r["stagger"] = pg.evaluate(STAGGER_JS)
            r["timing"] = timing_check(pg, f"{base}/{page}")
        if mode == "paused":
            time.sleep(0.4)
            r["running_infinite"] = pg.evaluate(LOOPS_JS)
        if shots:
            pg.screenshot(path=str(shots / f"{mode}-top.png"))
        r["pass"] = js_pass(pg) if mode == "phone" else wheel_pass(pg)
        r["final"] = pg.evaluate(FINAL_JS)
        r["hidden"] = pg.evaluate(HIDDEN_JS)
        if mode in ("rm", "reduced", "paused"):
            r["running_infinite_end"] = pg.evaluate(LOOPS_JS)
        if mode == "phone":
            r["overflow_px"] = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            r["horizontal"] = pg.evaluate("""() => { const s = document.querySelector('[data-mk~="horizontal"]'); if (!s) return null; const st = s.querySelector('[data-mk-stage]');
                return {overflow: getComputedStyle(st).overflowX, position: getComputedStyle(st).position, tall: s.getBoundingClientRect().height > 2 * innerHeight}; }""")
            pg.mouse.move(200, 400)
            pg.mouse.move(260, 420)
            time.sleep(0.4)
            r["pointer_vars"] = pg.evaluate("() => Array.from(document.querySelectorAll('[data-mk~=\"magnet\"], [data-mk~=\"tilt\"]')).filter(e => e.style.getPropertyValue('--mk-mx') || e.style.getPropertyValue('--mk-ry')).length")
        if mode == "desk":
            r["marquee"] = marquee_check(pg)
            r["beats"] = beats_check(pg, shots)
            r["scrub"] = scrub_check(pg)
            r["pointer"] = pointer_check(pg)
            r["toggle"] = toggle_check(pg)
            r["pause"] = pause_check(pg)
        r["end"] = info(pg)
        r["errors"], r["external"] = errs, ext
        return r
    finally:
        b.close()


def demo_targets(folder=FOLDER):
    """Страница-демо → якоря эффектов из primitives.yaml (поля demo и also)."""
    import yaml
    doc = yaml.safe_load((Path(folder) / "primitives.yaml").read_text(encoding="utf-8"))
    out = {}
    for p in doc.get("primitives") or []:
        for ref in [p.get("demo")] + list(p.get("also") or []):
            if ref and "#" in ref:
                path, anchor = ref.split("#", 1)
                out.setdefault(path.replace("examples/", "", 1), set()).add(anchor)
    return {k: sorted(v) for k, v in out.items()}


def run_demos(pw, base, root):
    b = launch(pw)
    res = {}
    try:
        for page, anchors in sorted(demo_targets().items()):
            if not (Path(root) / page).is_file():
                res[page] = {"missing_page": True}
                continue
            ctx = b.new_context(viewport={"width": 1440, "height": 900})
            ctx.add_init_script(INIT)
            pg = ctx.new_page()
            errs, ext = wire(pg, base)
            pg.goto(f"{base}/{page}", wait_until="load")
            time.sleep(1.0)
            miss = [a for a in anchors if not pg.evaluate(f"!!document.getElementById({json.dumps(a)})")]
            ps = wheel_pass(pg, step=600, gap=0.09)
            res[page] = {"anchors": anchors, "missing": miss, "final": pg.evaluate(FINAL_JS), "hidden": pg.evaluate(HIDDEN_JS),
                         "warnings": (info(pg) or {}).get("warnings"), "loops_max": ps["loops_max"], "errors": errs, "external": ext}
            ctx.close()
    finally:
        b.close()
    return res


# ---------------------------------------------------------------------------------------------- вердикт
def judge(tag, r):
    """Прогон → список непройденных условий (пусто — годен)."""
    bad = []
    if not isinstance(r, dict):
        return ["нет результата"]
    if tag == "static":
        if r.get("forbidden"):
            bad.append(f"запрещённые API: {r['forbidden'][:4]}")
        if r.get("globals") != ["MotionKit"]:
            bad.append(f"глобальные имена {r.get('globals')} — нужно одно MotionKit")
        if not r.get("spring_same"):
            bad.append("пружина набора не совпадает с пружиной рантайма сцен 3D")
        if r.get("token_vars_missing"):
            bad.append(f"переменных токенов нет в marketing-tokens.json: {r['token_vars_missing'][:4]}")
        if r.get("global_reduce"):
            bad.append("общий reduce «* { animation-duration: .01ms }»")
        if r.get("artboard"):
            bad.append(f"артборд: {r['artboard'][:3]}")
        return bad
    if tag == "demos":
        for page, x in sorted(r.items()):
            if x.get("missing_page"):
                bad.append(f"{page}: страницы нет")
                continue
            if x.get("missing"):
                bad.append(f"{page}: нет якорей {x['missing']}")
            for k in ("errors", "external"):
                if x.get(k):
                    bad.append(f"{page}: {k} {x[k][:2]}")
            if (x.get("final") or {}).get("bad"):
                bad.append(f"{page}: не в конечном состоянии {x['final']['bad'][:2]}")
            if x.get("hidden"):
                bad.append(f"{page}: невидимый текст {x['hidden'][:3]}")
            if x.get("warnings"):
                bad.append(f"{page}: предупреждения набора {x['warnings'][:2]}")
        return bad
    if r.get("errors"):
        bad.append(f"ошибки и предупреждения консоли: {r['errors'][:3]}")
    if r.get("external"):
        bad.append(f"запросы наружу: {r['external'][:3]}")
    if tag == "nojs":
        if r.get("mk_on"):
            bad.append("корень набора стоит без JS")
        if r.get("hidden"):
            bad.append(f"без JS скрыт текст: {r['hidden'][:4]}")
        if (r.get("final") or {}).get("bad"):
            bad.append(f"без JS не конечное состояние: {r['final']['bad'][:3]}")
        lay = r.get("layout") or {}
        if lay.get("sticky"):
            bad.append("без JS сцена закреплена")
        return bad
    want = {"desk": "full", "phone": "full", "paused": "full", "rm": "reduced", "reduced": "reduced"}[tag]
    if r.get("mk_on") != want:
        bad.append(f"режим {r.get('mk_on')} ≠ {want}")
    if (r.get("final") or {}).get("bad"):
        bad.append(f"после прохода не в конечном состоянии: {r['final']['bad'][:3]}")
    if r.get("hidden"):
        bad.append(f"невидимый текст после прохода: {r['hidden'][:4]}")
    if tag in ("rm", "reduced"):
        if r.get("hidden_before"):
            bad.append(f"до прокрутки скрыт текст: {r['hidden_before'][:4]}")
        if (r.get("final_before") or {}).get("bad"):
            bad.append(f"до прокрутки не конечное состояние: {r['final_before']['bad'][:3]}")
        if r.get("running_infinite") or r.get("running_infinite_end"):
            bad.append("бегут бесконечные анимации")
        lay = r.get("layout") or {}
        if lay.get("sticky"):
            bad.append("сцена закреплена")
        if any(p not in ("1", "") for p in lay.get("p") or []):
            bad.append(f"сцена не в конечном кадре: --mk-p {lay.get('p')}")
        if lay.get("dup_shown"):
            bad.append("дубль бегущей строки виден")
        if tag == "reduced" and r.get("attr") != "reduced":
            bad.append(f"data-motion {r.get('attr')} ≠ reduced")
    if tag == "paused":
        if r.get("attr") != "paused":
            bad.append(f"data-motion {r.get('attr')} ≠ paused")
        if r.get("running_infinite") or r.get("running_infinite_end"):
            bad.append("петли бегут на паузе")
    if tag == "phone":
        if (r.get("start") or {}).get("fine"):
            bad.append("тач-телефон опознан как мышь")
        if (r.get("overflow_px") or 0) > 2:
            bad.append(f"горизонтальное переполнение {r['overflow_px']} px")
        h = r.get("horizontal") or {}
        if h and (h.get("position") == "sticky" or h.get("tall") or h.get("overflow") not in ("auto", "scroll")):
            bad.append(f"горизонталь на телефоне не родная лента: {h}")
        if r.get("pointer_vars"):
            bad.append("указатель двигает элементы на тач-экране")
        if ((r.get("pass") or {}).get("loops_max") or 0) > 1:
            bad.append(f"петель в окне {r['pass']['loops_max']} > 1 на телефоне")
        if (r.get("end") or {}).get("warnings"):
            bad.append(f"предупреждения набора: {r['end']['warnings'][:2]}")
    if tag == "desk":
        p = r.get("pass") or {}
        if (p.get("loaf_pct") or 0) > 2:
            bad.append(f"долгие кадры прокрутки {p['loaf_pct']} % > 2 %")
        if (p.get("loops_max") or 0) > 2:
            bad.append(f"петель в окне {p['loops_max']} > 2 (L1)")
        if (r.get("end") or {}).get("warnings"):
            bad.append(f"предупреждения набора: {r['end']['warnings'][:2]}")
        for g in r.get("stagger") or []:
            if g["k"] != g["idx"]:
                bad.append(f"стаггер {g['group']}: --mk-k {g['k']} ≠ порядку {g['idx']}")
            d = g["d"]
            if any(b < a - 0.5 for a, b in zip(d, d[1:])):
                bad.append(f"стаггер {g['group']}: задержки не по порядку {d}")
            if g["kind"] == "group" and len(d) > 1 and not (40 - 0.5 <= d[1] - d[0] <= 80 + 0.5 and d[-1] <= 600 + 0.5):
                bad.append(f"стаггер {g['group']}: шаг {d[1] - d[0]:.0f} мс или сумма {d[-1]:.0f} мс вне 40–80 / ≤ 600")
            if g["kind"] == "split" and d[-1] + (g.get("dur") or 0) > 1000 + 1:
                bad.append(f"разбиение {g['group']}: сцена {d[-1] + g['dur']:.0f} мс > 1000")
        for prim, want in TIMING.items():
            got = (r.get("timing") or {}).get(prim)
            if got is None:
                continue
            have = {x["prop"]: x["ms"] for x in got.get("t") or []}
            for prop, ms in want.items():
                if prop not in have:
                    bad.append(f"{prim}: нет перехода {prop}")
                elif abs(have[prop] - ms) > 2:
                    bad.append(f"{prim}: {prop} {have[prop]} мс ≠ {ms}")
        m = r.get("marquee") or {}
        if m.get("present", True) and m:
            if not 30 * 0.85 <= (m.get("speed_px_s") or 0) <= 60 * 1.1:
                bad.append(f"скорость строки {m.get('speed_px_s')} px/с вне 30–60")
            if not m.get("hover_paused"):
                bad.append("строка не стоит при наведении")
            if not m.get("offscreen_idle"):
                bad.append("строка идёт вне экрана")
        pz = r.get("pause") or {}
        if pz.get("present"):
            if pz.get("attr") != "paused" or pz.get("pressed") != "true" or pz.get("running_infinite") or not pz.get("restored"):
                bad.append(f"пауза не работает: {pz}")
        tg = r.get("toggle") or {}
        if tg.get("present"):
            red = tg.get("reduced") or {}
            if red.get("on") != "reduced" or red.get("running_infinite") or red.get("final") or red.get("hidden"):
                bad.append(f"«Меньше» не останавливает движение: {red}")
            if tg.get("full_on") != "full":
                bad.append("«Полное» не включает движение")
            if (tg.get("system") or {}).get("attr") is not None:
                bad.append("«Как в системе» не снимает data-motion")
        bt = r.get("beats") or {}
        if bt.get("present"):
            s = [x for x in bt.get("seq") or [] if x is not None and x >= 0]
            if not s or any(b - a != 1 for a, b in zip(s, s[1:])):
                bad.append(f"такты не по одному: {bt.get('seq')}")
            w = bt.get("tempo") or 3
            for st in bt.get("settle") or []:
                if not st["monotonic"] or st["overshoot"] > 1e-3:
                    bad.append(f"такт {st['beat']}: пружина с перелётом или рывком ({st['overshoot']})")
                if st.get("refresh_cut"):
                    bad.append(f"такт {st['beat']}: refresh() оборвал доигрыш — сцена прыгнула к точке покоя")
                if abs(st["end"] - st["target"]) > 3e-3:
                    bad.append(f"такт {st['beat']}: не сел на точку покоя ({st['end']} из {st['target']})")
                if st["t95_s"] is not None and st["beat"] > 0 and not 0.6 * 4.74 / w <= st["t95_s"] <= 1.4 * 4.74 / w:
                    bad.append(f"такт {st['beat']}: 95 % пути за {st['t95_s']} с, ждали ≈ {4.74 / w:.2f}")
        sc = r.get("scrub") or {}
        if sc.get("present") and (not sc.get("monotonic") or (sc.get("end_gap") or 0) > 1e-3):
            bad.append(f"скраб не монотонен или не догнал: {sc}")
        pt = r.get("pointer") or {}
        if "magnet_px" in pt and not (0 < abs(pt["magnet_px"]) <= 8.05 and abs(pt.get("magnet_back_px", 0)) < 0.5):
            bad.append(f"магнит {pt['magnet_px']} px, возврат {pt.get('magnet_back_px')} px — нужно 0 < x ≤ 8 и возврат")
        if "tilt_ry_deg" in pt and not 0 < pt["tilt_ry_deg"] <= 7.05:
            bad.append(f"наклон {pt['tilt_ry_deg']}° вне (0; 7]")
    return bad


# ---------------------------------------------------------------------------------------------- запуск
def opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return default


def selftest():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(("OK   " if cond else "FAIL ") + name)

    a = spring_run(3.0, 1 / 60, 3.0)
    t95 = next(t for t, x in a if x >= 0.95)
    check("пружина ω 3: 95 % пути за 4,74/ω ≈ 1,58 с", abs(t95 - 4.74 / 3) < 0.03)
    check("пружина без перелёта: x ≤ цели на всём пути", max(x for _, x in a) <= 1 + 1e-12)
    b = spring_run(3.0, 1 / 144, 1.0)
    c = spring_run(3.0, 1 / 30, 1.0)
    check("пружина не зависит от частоты кадров: x(1 с) при 144 и 30 Гц совпадают", abs(b[-1][1] - c[-1][1]) < 1e-9)
    check("скраб ω 6,5: 95 % за ≈ 0,73 с", abs(next(t for t, x in spring_run(6.5, 1 / 240, 2) if x >= 0.95) - 0.73) < 0.02)
    check("статика: innerHTML, fetch, appendChild, export, textContent = — находки",
          len(forbidden("el.innerHTML = x;\nfetch('/a');\np.appendChild(c);\nexport default 1;\nn.textContent = 's';")) == 5)
    check("статика: classList.remove, removeAttribute, комментарий с innerHTML — не находки",
          not forbidden("el.classList.remove('a'); el.removeAttribute('x'); // innerHTML\n/* appendChild */ var s = 'fetch(';"))
    good = {"mode": "desk", "mk_on": "full", "errors": [], "external": [], "final": {"n": 9, "bad": []}, "hidden": [],
            "pass": {"loaf_pct": 0.3, "loops_max": 2}, "end": {"warnings": []},
            "stagger": [{"group": "g", "k": [0, 1, 2], "idx": [0, 1, 2], "d": [0, 60, 120], "kind": "group"}],
            "marquee": {"speed_px_s": 40, "hover_paused": True, "offscreen_idle": True},
            "pause": {"present": True, "attr": "paused", "pressed": "true", "running_infinite": 0, "restored": True},
            "toggle": {"present": True, "reduced": {"on": "reduced", "running_infinite": 0, "final": [], "hidden": []}, "full_on": "full", "system": {"attr": None, "on": "full"}},
            "beats": {"present": True, "seq": [0, 1, 2], "tempo": 3, "settle": [{"beat": 1, "target": 0.5, "end": 0.4995, "t95_s": 1.6, "monotonic": True, "overshoot": 0}]},
            "scrub": {"present": True, "monotonic": True, "end_gap": 0}, "pointer": {"magnet_px": 6.2, "magnet_back_px": 0.0, "tilt_ry_deg": 5.4},
            "timing": {"rise": {"t": [{"prop": "opacity", "ms": 336}, {"prop": "transform", "ms": 560}]}}}
    check("judge desk: годный прогон", judge("desk", good) == [])
    check("judge desk: перескок такта и перелёт пружины — находки",
          len(judge("desk", dict(good, beats={"present": True, "seq": [0, 2], "tempo": 3,
                                              "settle": [{"beat": 2, "target": 1, "end": 1, "t95_s": 1.5, "monotonic": True, "overshoot": 0.02}]}))) == 2)
    check("judge desk: запрос наружу и невидимый текст — находки", len(judge("desk", dict(good, external=["https://x"], hidden=["p"]))) == 2)
    check("judge desk: прозрачность подъёма не короче сдвига — находка",
          judge("desk", dict(good, timing={"rise": {"t": [{"prop": "opacity", "ms": 560}, {"prop": "transform", "ms": 560}]}})) != [])
    check("judge desk: стаггер не по порядку — находка",
          judge("desk", dict(good, stagger=[{"group": "g", "k": [0, 2, 1], "idx": [0, 1, 2], "d": [0, 120, 60], "kind": "group"}])) != [])
    rm = {"mode": "rm", "mk_on": "reduced", "errors": [], "external": [], "final": {"bad": []}, "hidden": [], "hidden_before": [],
          "final_before": {"bad": []}, "running_infinite": 0, "running_infinite_end": 0, "layout": {"sticky": 0, "p": ["1"], "dup_shown": 0}}
    check("judge rm: конечные состояния — годен", judge("rm", rm) == [])
    check("judge rm: закреплённая сцена и бегущая петля — находки", len(judge("rm", dict(rm, running_infinite=1, layout={"sticky": 1, "p": ["0.3"], "dup_shown": 0}))) == 3)
    check("judge nojs: скрытый текст — находка", judge("nojs", {"errors": [], "external": [], "mk_on": None, "hidden": ["p"], "final": {"bad": []}, "layout": {}}) != [])
    st = static_check()
    check("motion-kit.js: без запрещённых API, одно глобальное имя MotionKit", not st["forbidden"] and st["globals"] == ["MotionKit"])
    check("пружина motion-kit.js дословно та же, что в stage-runtime.js", st["spring_same"])
    check(f"motion-kit.css: {st['token_vars']} переменных токенов — все есть в marketing-tokens.json", not st["token_vars_missing"])
    check("motion-kit.css: нет общего reduce «* { animation-duration: .01ms }»", not st["global_reduce"])
    check("artboard-adapter.dc.html: формат артборда холста", not st["artboard"])
    check("артборд: ловит innerHTML и пропуск support.js", len(artboard_findings("<x-dc><helmet></helmet></x-dc><script>a.innerHTML=1</script>")) >= 3)
    pages = demo_targets()
    check(f"primitives.yaml → {len(pages)} страниц-демо, все на месте", pages and all((ROOT / p).is_file() for p in pages))
    html = (ROOT / "demo.html").read_text(encoding="utf-8") if (ROOT / "demo.html").is_file() else ""
    check("demo.html: DOM-контракт, пауза, переключатель, MotionKit.mount",
          all(x in html for x in ('data-section=', 'data-moment=', 'data-mk="pause"', 'data-motion-set="reduced"', 'MotionKit.mount(')))
    print("motion_smoke selftest: " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv):
    argv = list(argv)
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if "--selftest" in argv:
        return selftest()
    root = Path(opt(argv, "--root", str(ROOT))).resolve()
    page = opt(argv, "--page", "demo.html")
    report = opt(argv, "--json")
    modes = [m for m in opt(argv, "--modes", ",".join(MODES)).split(",") if m]
    bad_modes = [m for m in modes if m not in MODES]
    if bad_modes:
        print(f"неизвестные режимы: {bad_modes}", file=sys.stderr)
        return 2
    shots = kbpaths.out("creative", "motion-smoke") if "--shots" in argv else None
    res = {}
    if "static" in modes:
        res["static"] = static_check(root)
    live = [m for m in modes if m != "static"]
    if live:
        from playwright.sync_api import sync_playwright
        httpd, base = serve(root)
        try:
            with kbpaths.lock("browser"), sync_playwright() as pw:
                for m in live:
                    t0 = time.time()
                    res[m] = run_demos(pw, base, root) if m == "demos" else run_mode(pw, base, page, m, shots)
                    print(f"  [{m}] {time.time() - t0:.0f} с", file=sys.stderr)
        finally:
            httpd.shutdown()
    for m in modes:
        bad = judge(m, res[m])
        res[m] = {"ok": not bad, "findings": bad, "data": res[m]}
    res["ok"] = all(res[m]["ok"] for m in modes)
    text = json.dumps(res, ensure_ascii=False, indent=1, default=str)
    if report:
        Path(report).write_text(text, encoding="utf-8")
    print(json.dumps({m: {"ok": res[m]["ok"], "findings": res[m]["findings"]} for m in modes} | {"ok": res["ok"]},
                     ensure_ascii=False, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
