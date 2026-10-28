"""build_pages.py — страницы B и C фазы 2 из A (l0-sdano как есть): меняется только визуал — фигура первого экрана
(изометрия Blender крупно, номера-выноски и подписи комнат HTML, связь «пункт ↔ булавка» на :has()), полоса приборов в
«Что проверяет инженер», штамп «СДАНО» на «Образце акта». Тексты, форма, структура — как в A.
    python3 build_pages.py [--only b|c]"""
import json, os, re, shutil, sys
R = "/home/mm/Документы/app-design/blender-research"; X = f"{R}/99-raw/experiments/SD"; S = f"{R}/15-showcase/sdano"
PB = f"{X}/pagebuild"
A_HTML = open(f"{S}/a-code/index.html", encoding="utf-8").read()
A_CSS = open(f"{S}/a-code/style.css", encoding="utf-8").read()
meta = json.load(open(f"{PB}/assets/assets_b.json"))
ROOMS_FIX = {"Гостиная": (3.0, 5.85, 0.0)}      # якорь подписи с учётом проекции головки 1 (фаза 2)


def rooms_html():
    import math
    FR = meta["desk"]["frame_uw"]; W = meta["desk"]["w"]; ppm = W / (FR["u1"] - FR["u0"]); H = meta["desk"]["h"]
    out = []
    for nm, r in meta["rooms"].items():
        x, y = r["x"], r["y"]
        if nm in ROOMS_FIX:
            px_, py_, pz_ = ROOMS_FIX[nm]
            u = (px_ - py_) / math.sqrt(2); w = (px_ + py_) * 0.408248 + pz_ * 0.816497
            x, y = round((u - FR["u0"]) * ppm / W * 100, 2), round((FR["w1"] - w) * ppm / H * 100, 2)
        out.append(f'          <li style="--x:{x}%;--y:{y}%">{nm}<span>{r["area"]}</span></li>')
    return "\n".join(out)


TIPS = {"1": "Трещина в стяжке", "2": "Продувает окно", "3": "Уклон пола 9 мм", "4": "Розетка без заземления"}


def pins_html():
    out = []
    for k, p in sorted(meta["pins"].items(), key=lambda kv: int(kv[0])):
        out.append(f'          <li class="pin" data-d="{k}" style="--x:{p["x"]}%;--y:{p["y"]}%;--xm:{p["xm"]}%;--ym:{p["ym"]}%;--i:{int(k) - 1}">'
                   f'<b>{k}</b><span class="pin__tip">{TIPS[k]}</span></li>')
    return "\n".join(out)


def srcset(base, widths, ext):
    return ", ".join(f"assets/{base}-{w}.{ext} {w}w" for w in widths)


ALT = ("Изометрический разрез той же квартиры: стены срезаны на высоте 1,1 м; инженер в каске с планшетом у лазерного "
       "нивелира, красная линия лазера на стенах гостиной; красными булавками отмечены четыре дефекта первой страницы акта — "
       "1 трещина в стяжке гостиной, 2 продувает окно, 3 уклон пола 9 мм на 2 м, 4 розетка без заземления")


def figure_html(variant):
    mw, mh = meta["mob"]["w"], meta["mob"]["h"]; dw, dh = meta["desk"]["w"], meta["desk"]["h"]
    canvas = '\n        <canvas class="plan__fx" aria-hidden="true"></canvas>' if variant == "c" else ""
    hint = ('\n        <p class="plan__hint" aria-hidden="true">Наведите курсор на план — фонарь инженера найдёт дефекты</p>' if variant == "c" else "")
    return f'''    <figure class="plan plan--iso" data-slot="hero-visual" aria-labelledby="plan-cap">
      <div class="plan__stage">
        <picture>
          <source media="(max-width: 60rem)" type="image/avif" srcset="{srcset('iso-mob', (390, 780, 1170), 'avif')}" sizes="calc(100vw - 32px)" width="{mw}" height="{mh}">
          <source media="(max-width: 60rem)" type="image/webp" srcset="{srcset('iso-mob', (390, 780, 1170), 'webp')}" sizes="calc(100vw - 32px)" width="{mw}" height="{mh}">
          <source type="image/avif" srcset="{srcset('iso-desk', (720, 1080, 1440, 1800), 'avif')}" sizes="56vw">
          <source type="image/webp" srcset="{srcset('iso-desk', (720, 1080, 1440, 1800), 'webp')}" sizes="56vw">
          <img class="plan__img" src="assets/iso-desk-1080.webp" width="{dw}" height="{dh}" alt="{ALT}" fetchpriority="high" decoding="async">
        </picture>{canvas}
        <ul class="plan__rooms" aria-hidden="true">
{rooms_html()}
        </ul>
        <ol class="plan__pins" aria-hidden="true" data-moment="hero-marks">
{pins_html()}
        </ol>{hint}
      </div>
      <figcaption id="plan-cap" class="plan__cap">
        <span class="plan__cap-lead">Так выглядит первая страница акта:</span>
        <ol class="plan__list">
          <li data-d="1"><b>1</b> Трещина в&nbsp;стяжке гостиной</li>
          <li data-d="2"><b>2</b> Продувает окно: нет пароизоляции шва</li>
          <li data-d="3"><b>3</b> Уклон пола 9&nbsp;мм на&nbsp;2&nbsp;м</li>
          <li data-d="4"><b>4</b> Розетка без заземления</li>
        </ol>
      </figcaption>
    </figure>'''


KIT = [("laser", "Лазерный уровень"), ("thermal", "Тепловизор"), ("moisture", "Влагомер"), ("tape", "Рулетка"), ("flashlight", "Фонарь")]


def kit_html():
    have = [k for k, _ in KIT if os.path.exists(f"{PB}/assets/icon-{k}-128.avif")]
    if not have:
        return ""
    lis = []
    for k, cap in KIT:
        if k not in have:
            continue
        lis.append(f'''      <li><picture><source type="image/avif" srcset="assets/icon-{k}-128.avif 1x, assets/icon-{k}-256.avif 2x">
        <img src="assets/icon-{k}-128.webp" srcset="assets/icon-{k}-256.webp 2x" width="128" height="128" alt="" loading="lazy" decoding="async"></picture><span>{cap}</span></li>''')
    return '\n    <ul class="kit" aria-label="Приборы инженера">\n' + "\n".join(lis) + "\n    </ul>"


def stamp_html():
    """Штамп «СДАНО» (SD2): клип Blender 38 кадров @24 — VP9 webm + H.264 mp4, кадр начала (штамп на месте) и конца
    (штамп на месте + оттиск). Без JS и в reduce — кадр конца; с JS — кадр начала, при 60 % в кадре клип играет один раз."""
    if os.path.exists(f"{PB}/assets/stamp.webm"):
        return '''
      <div class="doc__stamp3d" aria-hidden="true" data-moment="act-stamp">
        <img class="stamp3d__end" src="assets/stamp-end.webp" width="800" height="392" alt="" loading="lazy" decoding="async">
        <img class="stamp3d__start" data-src="assets/stamp-start.webp" width="800" height="392" alt="" decoding="async">
        <video class="stamp3d__clip" width="800" height="392" muted playsinline preload="none" disablepictureinpicture disableremoteplayback data-webm="assets/stamp.webm" data-mp4="assets/stamp.mp4"></video>
      </div>'''
    return ""


STAMP_JS = """  /* штамп «СДАНО» (SD2/SD3, ≈ 0,45 КБ): рядом с актом — кадр начала, при 60 % в кадре клип играет один раз; reduce и без JS —
     кадр конца; ошибка декодера или клип не доиграл за 4,5 с — тоже кадр конца (зона штампа не остаётся пустой) */
  var sb = document.querySelector('.doc__stamp3d');
  if (sb && 'IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var sv = sb.querySelector('video'), s0 = sb.querySelector('.stamp3d__start');
    var sOff = function () { sb.classList.remove('is-armed', 'is-play'); };
    var arm = function () { if (!s0.src) { s0.src = s0.dataset.src; sb.classList.add('is-armed'); } };
    var sa = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { sa.disconnect(); arm(); } }, {rootMargin: '0px 0px 60% 0px'});
    var so = new IntersectionObserver(function (es) { if (!es[0].isIntersecting) return; so.disconnect(); arm();
      var e;
      [['webm', 'video/webm; codecs="vp9"'], ['mp4', 'video/mp4']].forEach(function (t) {
        e = document.createElement('source'); e.src = sv.dataset[t[0]]; e.type = t[1]; sv.appendChild(e); });
      e.addEventListener('error', sOff); sv.addEventListener('error', sOff);
      sv.addEventListener('playing', function () { sb.classList.add('is-play'); });
      sv.addEventListener('ended', sOff); setTimeout(sOff, 4500);
      sv.load(); var pp = sv.play(); if (pp && pp.catch) pp.catch(function (x) { console.warn('SD stamp', x && x.name); sOff(); }); }, {threshold: 0.6});
    sa.observe(sb); so.observe(sb);
  }
"""


def build(variant):
    dst = f"{S}/{'b-blender' if variant == 'b' else 'c-hybrid'}"
    os.makedirs(f"{dst}/assets", exist_ok=True)
    shutil.copytree(f"{S}/a-code/_shared", f"{dst}/_shared", dirs_exist_ok=True)
    for f in os.listdir(f"{dst}/assets"):
        os.remove(f"{dst}/assets/{f}")
    for f in os.listdir(f"{PB}/assets"):
        if f.endswith((".avif", ".webp", ".webm", ".mp4")) and not (variant == "b" and f.startswith("fx-")):
            shutil.copy2(f"{PB}/assets/{f}", f"{dst}/assets/{f}")
    h = A_HTML
    a = h.index('    <figure class="plan"'); b = h.index("</figure>", a) + len("</figure>")
    h = h[:a] + figure_html(variant) + h[b:]
    h = h.replace('<section class="hero" data-section="hero"', '<section class="hero hero--iso" data-section="hero"')
    title = "B (Blender)" if variant == "b" else "C (Blender + фонарик)"
    h = h.replace("<title>Сдано — приёмка квартиры в новостройке с инженером · демо L0</title>",
                  f"<title>Сдано — приёмка квартиры в новостройке с инженером · {title}</title>")
    h = h.replace("<!-- Рабочий пример L0 ·", f"<!-- 15-showcase «Сдано» · вариант {title} · фаза 2 · дорожка SD · 2026-09-25. Визуал — Blender 5.2 (Cycles),"
                  " номера и подписи — HTML; тексты, форма и структура — как в A.\n     Исходник — рабочий пример L0 ·", 1)
    h = h.replace('<link rel="stylesheet" href="style.css">',
                  '<link rel="preload" as="image" type="image/avif" media="(min-width: 60.01rem)" imagesrcset="'
                  + srcset("iso-desk", (720, 1080, 1440, 1800), "avif") + '" imagesizes="56vw" fetchpriority="high">\n'
                  '<link rel="stylesheet" href="style.css">')
    k = kit_html()
    if k:
        h = h.replace('<h2 id="offer-h" class="h2">Что проверяет инженер</h2>', '<h2 id="offer-h" class="h2">Что проверяет инженер</h2>' + k)
    st = stamp_html()
    if st:
        h = h.replace('<div class="doc" role="group" aria-label="Образец акта осмотра">', '<div class="doc doc--stamp" role="group" aria-label="Образец акта осмотра">')
        h = h.replace('<p class="doc__stamp" aria-hidden="true">Образец</p>', '<p class="doc__stamp" aria-hidden="true">Образец</p>' + st)
        h = h.replace("  document.querySelector('.form').addEventListener('submit', function (e) {",
                      STAMP_JS + "  document.querySelector('.form').addEventListener('submit', function (e) {")
    if variant == "c":
        h = h.replace("</body>", '<script type="module" src="dist/fonarik.js"></script>\n</body>')
    open(f"{dst}/index.html", "w", encoding="utf-8").write(h)
    css = A_CSS + open(f"{PB}/iso.css", encoding="utf-8").read()
    if variant == "c":
        css += open(f"{PB}/fx.css", encoding="utf-8").read()
    open(f"{dst}/style.css", "w", encoding="utf-8").write(css)
    ms = open(f"{PB}/motion-spec-{variant}.yaml", encoding="utf-8").read() if os.path.exists(f"{PB}/motion-spec-{variant}.yaml") else open(f"{S}/a-code/motion-spec.yaml", encoding="utf-8").read()
    open(f"{dst}/motion-spec.yaml", "w", encoding="utf-8").write(ms)
    if variant == "c" and os.path.isdir(f"{PB}/dist"):
        shutil.copytree(f"{PB}/dist", f"{dst}/dist", dirs_exist_ok=True)
    print("built", dst)


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else "bc"
    for v in only:
        build(v)
