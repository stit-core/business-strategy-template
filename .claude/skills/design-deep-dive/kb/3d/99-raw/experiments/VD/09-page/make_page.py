#!/usr/bin/env python3
"""VD/09-page — страница 15-showcase/velmora/b-blender/: копия разметки и движка эталона нейросети (velmora/ai/01-mouse-scrub,
js/scrub.js без правок), свои assets/ и манифесты. Отличается только источник кадров (Blender Cycles) + кнопка «полный круг
360°» (второй встроенный манифест; кадры грузятся по нажатию — подменяем s.m у экземпляра движка stage.__scrub и зовём
s.load, scrub.js не меняется), подписи «Blender · Cycles · 0 ₽ · время машины», отметка первого кадра (KIT §5).

    python3 make_page.py [--no-full] [--out DIR]   # читает b-blender/assets/manifest.json, [assets/full360/manifest.json], velmora/numbers.json
VD3 (26.09.2026): без assets/full360/manifest.json (или с --no-full) страница собирается только с дугой — кнопки «Полный круг»
нет, столбца круга в таблице нет, тексты про круг убраны. Включение круга: пока не пришёл кадр фаса (середина секвенции),
холст скрыт и виден постер (фас) — без прыжка на спину флакона; затем точка покоя 0,5 (фас) без вступления, дальше — дрейф.
Общие файлы (css, js, fonts, favicon, noise) копируются из velmora/ai/ как есть (самодостаточная папка)."""
import json
import os
import shutil
import sys

R = "/home/mm/Документы/app-design/blender-research"
V = f"{R}/15-showcase/velmora"
OUT = f"{V}/b-blender"
AI = f"{V}/ai"


def kb(n):
    return f"{n / 1024:,.0f}".replace(",", " ") + " КБ"


def mb(n):
    return f"{n / 1048576:.1f}".replace(".", ",") + " МБ"


def main():
    global OUT
    if "--out" in sys.argv:                  # проба конвейера — во временную папку (там же assets/manifest.json)
        OUT = sys.argv[sys.argv.index("--out") + 1]
    for d in ("css", "js", "fonts"):
        os.makedirs(f"{OUT}/{d}", exist_ok=True)
        for f in os.listdir(f"{AI}/{d}"):
            if d == "js" and f != "scrub.js":
                continue
            shutil.copy(f"{AI}/{d}/{f}", f"{OUT}/{d}/{f}")
    os.makedirs(f"{OUT}/assets", exist_ok=True)
    for f in ("favicon.svg", "noise.svg"):
        shutil.copy(f"{AI}/assets/{f}", f"{OUT}/assets/{f}")
    arc = json.load(open(f"{OUT}/assets/manifest.json"))
    full_p = f"{OUT}/assets/full360/manifest.json"
    full = json.load(open(full_p)) if (os.path.exists(full_p) and "--no-full" not in sys.argv) else None
    ai = json.load(open(f"{AI}/01-mouse-scrub/assets/manifest.json"))
    nums = json.load(open(f"{V}/numbers.json"))
    ph2 = nums.get("phase2", {})
    mach = ph2.get("machine", {})
    arc_h = mach.get("orbit25_render_h", 0)
    full_h = mach.get("orbit360_render_h", 0)
    poster_kb = os.path.getsize(f"{OUT}/assets/poster.avif")

    def size(m, k):
        if not m:
            return 0
        e = m["video"].get(k) or m["frames"].get(k)
        return e["bytes"] if e else 0

    variants = [("orbit-av1-g4", "AV1 · ключ каждые 4 кадра"), ("orbit-av1-g1", "AV1 · каждый кадр ключевой"),
                ("orbit-av1-g8", "AV1 · ключ каждые 8 кадров"), ("orbit-h264-g4", "H.264 · ключ каждые 4 кадра"),
                ("orbit-h264-g1", "H.264 · каждый кадр ключевой"), ("orbit-h264-g8", "H.264 · ключ каждые 8 кадров"),
                ("seq-avif-1280", "Кадры AVIF 1280 · 61 шт."), ("seq-webp-1280", "Кадры WebP 1280 · 61 шт."),
                ("seq-avif-960", "Кадры AVIF 960 · 61 шт.")]
    n_arc = arc["frames"]["seq-avif-1280"]["count"]
    radios = "\n".join(f'      <label><input type="radio" name="scrub-variant" value="{k}"><span>'
                       + t.replace("61 шт.", f"<span data-n>{n_arc}</span> шт.") + '</span>'
                       f'<small data-size-of="{k}">{kb(size(arc, k))}</small></label>' for k, t in variants)
    rows = "".join(f'<tr data-v="{k}"><td>{t.replace(" · 61 шт.", "")}</td><td class="num">{kb(size(arc, k))}</td>'
                   + (f'<td class="num">{kb(size(full, k))}</td>' if full else "")
                   + f'<td class="num">{kb(size(ai, k))}</td></tr>' for k, t in variants)
    fmt = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
    html = TEMPLATE
    jdump = lambda m: json.dumps(m, ensure_ascii=False).replace("</", "<\\/")  # noqa: E731
    nf = (full["frames"]["seq-avif-1280"]["count"] - 1) if full else 72
    nfw = "кадра" if nf % 10 in (2, 3, 4) and nf % 100 not in (12, 13, 14) else "кадров"
    para_full = (f"      <p>Кнопка «полный круг 360°» грузит вторую секвенцию: {nf} {nfw} через {360 / nf:g}° — спина флакона, лента перед ним, этикетка\n"
                 "        уходит за стекло. У видео нейросети этого ракурса нет вовсе: пять секунд, дуга 25°.</p>")
    para_arc = ("      <p>Облёт отрендерен, а не сгенерирован, поэтому его можно продолжить до полного круга — тот же стол, та же студия,\n"
                "        спина флакона и лента перед ним. У видео нейросети этого ракурса нет вовсе: пять секунд, дуга 25°.</p>")
    spf = fmt(ph2.get("orbit25_s_per_frame", 0))
    repl = {
        "{{ARC_JSON}}": jdump(arc),
        "{{FULL_SCRIPT}}": (f'<script type="application/json" id="scrub-manifest-360">{jdump(full)}</script>' if full else ""),
        "{{FULL_BTN}}": ('\n      <button class="btn" type="button" data-full-circle aria-pressed="false"><span data-label>Полный круг 360°</span>'
                         f' <small data-full-size>{mb(size(full, "seq-avif-1280"))}</small></button>' if full else ""),
        "{{LEAD_TAIL}}": "Мир не плывёт, этикетка читается, круг можно замкнуть." if full else "Мир не плывёт, этикетка читается.",
        "{{PRICE}}": (f"0 ₽ · машина: дуга {fmt(arc_h)} ч ({spf} с на кадр), круг 360° — {fmt(full_h)} ч "
                      f"({ph2.get('orbit360_spp', 96)} спп)" if full else f"0 ₽ · машина: дуга {fmt(arc_h)} ч ({spf} с на кадр)"),
        "{{WIRE_FULL}}": f" · круг 360°: {mb(size(full, 'seq-avif-1280'))} по кнопке" if full else "",
        "{{FULL_PARA}}": para_full if full else para_arc,
        "{{SWAY_TAIL}}": ", в круге 360° — петля без шва" if full else "",
        "{{FULL_TH}}": "<th>Blender · круг 360°</th>" if full else "",
        "{{RADIOS}}": radios, "{{ROWS}}": rows,
        "{{POSTER_KB}}": kb(poster_kb), "{{ARC_AVIF}}": kb(size(arc, "seq-avif-1280")), "{{ARC_AV1G4}}": kb(size(arc, "orbit-av1-g4")),
        "{{ARC_H264G4}}": kb(size(arc, "orbit-h264-g4")), "{{FULL_AVIF}}": mb(size(full, "seq-avif-1280")) if full else "",
        "{{FULL_AV1G4}}": kb(size(full, "orbit-av1-g4")), "{{AI_AVIF}}": kb(size(ai, "seq-avif-1280")),
        "{{ARC_H}}": fmt(arc_h), "{{FULL_H}}": fmt(full_h), "{{SPP}}": str(ph2.get("orbit25_spp", 128)),
        "{{SPP360}}": str(ph2.get("orbit360_spp", 96)), "{{SEC_FRAME}}": fmt(ph2.get("orbit25_s_per_frame", 0)),
        "{{SEC_FRAME360}}": fmt(ph2.get("orbit360_s_per_frame", 0)),
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    assert "{{" not in html, [ln for ln in html.splitlines() if "{{" in ln][:3]
    open(f"{OUT}/index.html", "w").write(html)
    print("→", f"{OUT}/index.html", len(html), "байт")


TEMPLATE = r'''<!doctype html>
<!-- Дуэль Velmora · Blender: тот же приём «мышь ведёт видео», та же разметка и тот же движок scrub.js, что у страницы нейросети
     (velmora/ai/01-mouse-scrub/) — отличается только источник кадров: облёт флакона отрендерен в Blender 5.2.2 (Cycles),
     61 кадр дуги 25° + наезд (как у Kling 3), плюс «полный круг 360°» по кнопке (36 кадров через 10°, 64 спп). Постер = кадр 0 (LCP).
     reduce / Save-Data — 0 байт медиа, облёт по кнопке. Дорожка VD, фазы 2–3, 25–26.09.2026. Сборка — 99-raw/experiments/VD/
     (01-build/velmora.py → 08-enc/build_seq.py → 09-page/make_page.py). -->
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blender ведёт камеру — облёт флакона Velmora · дуэль с нейросетью</title>
<meta name="description" content="Горизонталь курсора управляет облётом камеры вокруг флакона: 61 кадр Blender Cycles на том же движке, что у видео нейросети, и полный круг 360° по кнопке.">
<meta name="theme-color" content="#050607">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="fonts/noto-serif-display-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="css/demos.css">
<style>
  .stage { touch-action: pan-y; }
  @media (hover: hover) and (pointer: fine) { .stage { cursor: ew-resize; } }
  .stage__media { background: #050607; }
  /* VD3 (26.09, ворота телефона): постер на 1 px шире сцены (под overflow:hidden не видно) — площадь LCP постера 207 648 px²
     вместо 207 236: кандидат-видео движка (207 648) уже не бывает строго крупнее, LCP остаётся постером (lcp_exp: bbC) */
  .stage__media > picture { inset: -1px; width: auto; height: auto; }
  .stage__media > picture > img, .stage__media > img { transition: opacity .6s var(--ease); object-position: 60% 50%; }
  .scrub-layer { opacity: 0; transition: opacity .6s var(--ease); object-position: 60% 50%; }
  .scrub-layer.is-on { opacity: 1; }
  .stage__scrim { background:
      linear-gradient(180deg, rgb(5 6 8 / .55) 0, rgb(5 6 8 / 0) 120px),
      linear-gradient(90deg, rgb(5 6 8 / .74) 0%, rgb(5 6 8 / .5) 36%, rgb(5 6 8 / 0) 60%),
      linear-gradient(0deg, var(--bg) 0, rgb(5 6 8 / 0) 140px); }
  .scrub-range { position: absolute; z-index: 4; left: var(--gutter); right: calc(var(--gutter) + 64px); bottom: 38px; display: block; }
  .scrub-range input { width: 100%; margin: 0; -webkit-appearance: none; appearance: none; background: transparent; height: 22px; cursor: pointer; }
  .scrub-range input::-webkit-slider-runnable-track { height: 1px; background: rgb(255 255 255 / .28); }
  .scrub-range input::-moz-range-track { height: 1px; background: rgb(255 255 255 / .28); }
  .scrub-range input::-webkit-slider-thumb { -webkit-appearance: none; width: 12px; height: 12px; margin-top: -6px; border-radius: 50%;
    background: var(--pearl); box-shadow: 0 0 0 6px rgb(239 230 220 / .12); }
  .scrub-range input::-moz-range-thumb { width: 12px; height: 12px; border: 0; border-radius: 50%; background: var(--pearl); }
  .scrub-range .ticks { position: absolute; left: 0; right: 0; top: 17px; display: flex; justify-content: space-between; font-size: 11px;
    letter-spacing: .12em; text-transform: uppercase; color: var(--faint); pointer-events: none; }
  .stage[data-state="reduce"] .hint, .stage[data-state="save-data"] .hint { display: none; }
  .optin { margin-top: 26px; display: flex; flex-wrap: wrap; gap: 10px; }
  .btn[aria-pressed="true"] { border-color: var(--champagne); background: rgb(217 195 166 / .14); }
  .btn small { color: var(--muted); font-weight: 400; }
  /* кольцо-курсор: только точный указатель и без reduce; мягко догоняет (CSS-переменные ставит скрипт ниже) */
  .ring { position: fixed; z-index: 6; left: 0; top: 0; width: 64px; height: 64px; margin: -32px 0 0 -32px; border-radius: 50%;
    border: 1px solid rgb(239 230 220 / .55); pointer-events: none; opacity: 0; transition: opacity .3s, width .3s, height .3s;
    transform: translate3d(var(--cx, -100px), var(--cy, -100px), 0); display: grid; place-items: center; color: var(--pearl); }
  .ring svg { width: 30px; height: 12px; }
  .stage:hover ~ .ring { opacity: 1; }
  @media (hover: none), (prefers-reduced-motion: reduce) { .ring { display: none; } }
  .lab-note { margin-top: 14px; }
  .stage__copy { padding-top: clamp(96px, 16vh, 150px); padding-bottom: 110px; }
  .only-touch { display: none; }
  @media (hover: none) { .only-fine { display: none; } .only-touch { display: inline; } }
  @media (max-width: 700px) {
    /* телефон: текст сверху на тёмном, кадр — нижние 60 % сцены, флакон целиком (фокус x ≈ 0,74) */
    .stage { min-height: 100svh; }
    .stage__media { inset: 40% 0 0 0; }
    .stage__media > picture > img, .scrub-layer { object-position: 74% 45%; }
    .stage__scrim { background: linear-gradient(180deg, #050607 0%, #050607 40%, rgb(5 6 8 / .0) 56%),
                                linear-gradient(0deg, var(--bg) 0, rgb(5 6 8 / 0) 90px); }
    .stage__copy { padding-top: 76px; padding-bottom: 0; }
    .display { font-size: clamp(32px, 9vw, 40px); }
    .lead { font-size: 15px; margin-top: 14px; }
    .hint { margin-top: 16px; }
    .optin { margin-top: 16px; }
  }
</style>
</head>
<body>
<header class="topbar">
  <a class="crumb" href="../ai/01-mouse-scrub/index.html"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M10 3 5 8l5 5"/></svg>Нейросеть · Kling 3</a>
  <span class="spacer"></span><span>Дуэль · Blender</span>
</header>

<section class="stage grain" data-scrub data-default="seq-avif-1280" data-default-touch="orbit-av1-g4" data-fallback="orbit-h264-g4" data-rest="0.5" aria-labelledby="h1">
  <div class="stage__media">
    <picture>
      <source type="image/avif" srcset="assets/poster.avif">
      <img src="assets/poster.webp" width="1280" height="720" fetchpriority="high"
           alt="Флакон крема VELMORA из рифлёного стекла с шампань-золотой крышкой на полированном чёрном граните, за ним — прозрачная стеклянная лента с радужной каймой">
    </picture>
  </div>
  <div class="stage__scrim" aria-hidden="true"></div>
  <div class="stage__copy">
    <p class="kicker">Blender · Cycles · 0 ₽ · {{ARC_H}} ч машины</p>
    <h1 class="display" id="h1">Курсор ведёт <em>камеру</em> вокруг флакона</h1>
    <p class="lead">Тот же облёт 25°, что у нейросети, — но отрендеренный: горизонталь указателя выбирает кадр, сцена догоняет мягко,
      а когда рука замирает — медленно дышит сама. {{LEAD_TAIL}}</p>
    <p class="hint"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><rect x="7" y="3" width="10" height="16" rx="5"/><path d="M12 6.5v3M3 12h2M19 12h2M3.8 12l1.4-1.2M3.8 12l1.4 1.2M20.2 12l-1.4-1.2M20.2 12l-1.4 1.2"/></svg>
      <span class="only-fine">Ведите мышь влево и вправо</span><span class="only-touch">Проведите пальцем по кадру</span></p>
    <p class="optin"><button class="btn btn--solid" type="button" data-scrub-optin hidden>Показать облёт · <span data-size>≈ 1 МБ</span></button>{{FULL_BTN}}</p>
  </div>
  <label class="scrub-range"><span class="sr-only">Положение камеры вокруг флакона</span>
    <input type="range" min="0" max="1000" value="0" step="1" data-scrub-range>
    <span class="ticks" aria-hidden="true"><span>фас</span><span>облёт 25°</span></span></label>
  <button class="motion-toggle" type="button" aria-pressed="false" hidden>
    <span class="sr-only">Остановить движение сцены</span>
    <svg class="i-pause" viewBox="0 0 18 18" fill="currentColor" aria-hidden="true"><rect x="4" y="3" width="3.4" height="12" rx="1"/><rect x="10.6" y="3" width="3.4" height="12" rx="1"/></svg>
    <svg class="i-play" viewBox="0 0 18 18" fill="currentColor" aria-hidden="true" style="display:none"><path d="M5 3.2v11.6c0 .6.7 1 1.2.7l9-5.8c.5-.3.5-1.1 0-1.4l-9-5.8C5.7 2.2 5 2.6 5 3.2z"/></svg>
  </button>
</section>
<div class="ring" aria-hidden="true"><svg viewBox="0 0 30 12" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M6 1 1 6l5 5M24 1l5 5-5 5"/></svg></div>

<section class="section" aria-labelledby="how">
  <h2 id="how">Как сделано</h2>
  <ul class="credits" aria-label="Паспорт приёма">
    <li><b>Движок</b><span>Blender 5.2.2 · Cycles CPU, {{SPP}} спп + OIDN, 1280 × 720, вид Khronos PBR Neutral</span></li>
    <li><b>Цена</b><span>{{PRICE}}</span></li>
    <li><b>Вес на проводе</b><span>постер {{POSTER_KB}} · мышь: 61 кадр AVIF {{ARC_AVIF}} (у нейросети {{AI_AVIF}}) · касание: AV1 GOP 4 — {{ARC_AV1G4}} (запас H.264 — {{ARC_H264G4}}){{WIRE_FULL}}</span></li>
    <li><b>Как сделано</b><span>сцена в метрах одним скриптом → поворотный стол (камера и свет стоят) → PNG без потерь → AVIF q55 / AV1 CRF 32 / H.264 CRF 22 → тот же <code>scrub.js</code></span></li>
  </ul>
  <p class="note lab-note">Сравнить: <a href="../ai/01-mouse-scrub/index.html">тот же приём на видео Kling 3</a> (57 ₽). Флакон, этикетка VELMORA и
    лента повторяют бриф нейросети; разметка и движок страницы — копия её страницы, отличаются только кадры.</p>

  <div class="cols" style="margin-top:40px">
    <div>
      <h3>Что даёт рендер вместо генерации</h3>
      <p>Мир облёта жёсткий: флакон, камень и лента стоят на поворотном столе, камера и студия неподвижны — свет остаётся
        «фотографическим» в любом ракурсе, лента не плывёт от кадра к кадру и не появляется панель, которой не было.
        Этикетка — настоящая типографика (антиква с разрядкой и вторая строка мелким кеглем, краска вдавлена в бумагу),
        рифление — 32 грани с острыми канавками, дно — толстое стекло с преломлением крема.</p>
{{FULL_PARA}}
    </div>
    <div>
      <h3>Свет, лента, камень</h3>
      <p>У ленты своя «студия»: большой купол с мягкими долями и полосами-стрип-боксами, видимый только ей (light linking; для флакона
        он прозрачен) — перелив течёт по закруту, а не пятнами-лампами. Плёнка — стекло 1,1 мм с тонкой плёнкой и честной
        дисперсией на клиновидной кромке (три стекла R/G/B), кромки светятся, концы растворяются. Камень — полированный гранит:
        зерно, облака и чешуйки слюды под лаком. За лентой — свет по складкам ткани и мягкое свечение Glare.</p>
      <p>Вторичное движение: фаза закрута ленты медленно следует за поворотом стола (± несколько градусов){{SWAY_TAIL}}.</p>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="lab" style="padding-top:0">
  <h2 id="lab">Лаборатория доставки</h2>
  <div class="lab">
    <fieldset>
      <legend>Вариант</legend>
{{RADIOS}}
    </fieldset>
    <div>
      <div class="stats" data-scrub-hud aria-live="off">
        <div><b data-k="bytes">—</b><span>получено</span></div>
        <div><b data-k="load">—</b><span>до первого кадра</span></div>
        <div><b data-k="seek">—</b><span>перемотка / декод: медиана · p95</span></div>
        <div><b data-k="state">—</b><span>состояние</span></div>
      </div>
      <p class="note" data-k-wrap>Счётчик: <span data-scrub-hud-extra></span></p>
      <div class="table-wrap" style="margin-top:22px">
        <table class="data" id="weights-table">
          <caption class="sr-only">Вес вариантов доставки: Blender (дуга и круг) и нейросеть</caption>
          <thead><tr><th>Вариант</th><th>Blender · дуга 25°</th>{{FULL_TH}}<th>Нейросеть · дуга 25°</th></tr></thead>
          <tbody>{{ROWS}}</tbody>
        </table>
      </div>
    </div>
  </div>
</section>

<footer class="foot">Дуэль Velmora · 15-showcase, дорожка VD, фазы 2–3 (25–26.09.2026) · <a href="../ai/01-mouse-scrub/index.html">страница нейросети</a> ·
  кадры отрендерены в Blender Cycles на своей машине, 0 ₽; шрифт Noto Serif Display (OFL).</footer>

<script type="application/json" id="scrub-manifest">{{ARC_JSON}}</script>
{{FULL_SCRIPT}}
<script>
  // кольцо-курсор: мягко догоняет указатель (только точный указатель и без reduce)
  (function () {
    var ring = document.querySelector('.ring');
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var x = -100, y = -100, cx = -100, cy = -100, raf = 0;
    var step = function () { cx += (x - cx) * 0.22; cy += (y - cy) * 0.22; ring.style.setProperty('--cx', cx.toFixed(1) + 'px');
      ring.style.setProperty('--cy', cy.toFixed(1) + 'px'); raf = Math.abs(x - cx) + Math.abs(y - cy) > 0.3 ? requestAnimationFrame(step) : 0; };
    addEventListener('pointermove', function (e) { if (e.pointerType !== 'mouse') return; x = e.clientX; y = e.clientY; if (!raf) raf = requestAnimationFrame(step); }, {passive: true});
  })();
  // счётчик «extra» из HUD-а скрипта
  (function () { var el = document.querySelector('[data-scrub-hud-extra]'); var hud = document.querySelector('[data-scrub-hud]');
    var b = document.createElement('b'); b.dataset.k = 'extra'; b.hidden = true; hud.appendChild(b);
    setInterval(function () { el.textContent = b.textContent || '—'; }, 400); })();
  // отметка первого кадра сцены (KIT §5): состояние сцены стало live — кадр облёта на экране
  (function () { var st = document.querySelector('[data-scrub]'), done = false;
    new MutationObserver(function () { if (!done && st.dataset.state === 'live') { done = true; performance.mark('hero-first-frame');
      console.warn('VD timing hero-first-frame ' + Math.round(performance.now()) + ' ms · ' + ((st.__scrub || {}).variant || '')); } })
      .observe(st, {attributes: true, attributeFilter: ['data-state']}); })();
  // «полный круг 360°»: вторая секвенция по нажатию — тот же движок, другой манифест (порядок −180°…+180°, фас в середине)
  (function () {
    var st = document.querySelector('[data-scrub]'), btn = document.querySelector('[data-full-circle]');
    if (!btn || !document.getElementById('scrub-manifest-360')) return;
    var ticks = st.querySelector('.scrub-range .ticks'), kbf = function (n) { return Math.round(n / 1024).toLocaleString('ru-RU') + ' КБ'; };
    var mbf = function (n) { return (n / 1048576).toLocaleString('ru-RU', {maximumFractionDigits: 1}) + ' МБ'; };
    var mans = {arc: JSON.parse(document.getElementById('scrub-manifest').textContent),
                full: JSON.parse(document.getElementById('scrub-manifest-360').textContent)};
    // круг: первым приходит кадр 0 (спина, −180°) — холст держим скрытым (виден постер-фас), пока не придёт кадр фаса
    // (середина), потом точка покоя 0,5 без вступления: переключение без прыжка на спину (scrub.js не меняется)
    var settle = function (s) {
      var t0 = performance.now();
      var go = function () {
        if (s.m !== mans.full || !s.bitmaps) return;
        var mid = Math.round((s.nFrames - 1) * s.rest);
        s.introUntil = 0; s.p = s.target = s.rest;
        if (!s.bitmaps[mid] && performance.now() - t0 < 5000) {
          if (s.canvas) s.canvas.classList.remove('is-on'); s.poster.style.opacity = ''; requestAnimationFrame(go); return;
        }
        s.lastInput = performance.now() - 1400; s.driftT0 = 0; s.drawAt(s.p, true);   // как в конце вступления движка: дрейф с разгоном 1,5 с
        if (s.canvas) s.canvas.classList.add('is-on'); if (s.kind === 'frames') s.poster.style.opacity = '0'; s.kick();
      };
      go();
    };
    new MutationObserver(function () { var s = st.__scrub; if (s && st.dataset.state === 'live' && s.m === mans.full && s.kind === 'frames') settle(s); })
      .observe(st, {attributes: true, attributeFilter: ['data-state']});
    btn.addEventListener('click', function () {
      var s = st.__scrub; if (!s) return;
      var full = btn.getAttribute('aria-pressed') !== 'true', m = full ? mans.full : mans.arc;
      s.m = m; btn.setAttribute('aria-pressed', String(full));
      btn.querySelector('[data-label]').textContent = full ? 'Дуга 25° · как у нейросети' : 'Полный круг 360°';
      btn.querySelector('[data-full-size]').textContent = full ? '' : mbf(mans.full.frames['seq-avif-1280'].bytes);
      document.querySelectorAll('[data-n]').forEach(function (el) { el.textContent = m.frames['seq-avif-1280'].count; });
      ticks.innerHTML = full ? '<span>спина</span><span>фас</span><span>спина</span>' : '<span>фас</span><span>облёт 25°</span>';
      st.querySelector('.scrub-range .sr-only').textContent = full ? 'Положение камеры на полном круге вокруг флакона' : 'Положение камеры вокруг флакона';
      document.querySelectorAll('[data-size-of]').forEach(function (el) { var k = el.dataset.sizeOf, e = m.video[k] || m.frames[k];
        if (e) el.textContent = kbf(e.bytes); });
      if (s.optIn) s.optIn.hidden = true;
      var cur = document.querySelector('input[name="scrub-variant"]:checked');
      s.load(cur && (m.video[cur.value] || m.frames[cur.value]) ? cur.value : s.pickDefault(), true);
    });
  })();
</script>
<script src="js/scrub.js"></script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
