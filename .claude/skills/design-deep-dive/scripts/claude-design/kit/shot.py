#!/usr/bin/env python3
"""kit/shot.py — «глаза» холста для работы из чата: PNG каждого кадра HTML-копий (с метками #N и без), весь холст,
marks.json. Модель не вызывается; сеть — только к шрифтам и ресурсам самих копий. Фоновых процессов не оставляет:
сервер — поток этого процесса, браузер закрывается в finally.

Кадры — список `artboards` манифеста (file, w, h, theme, title). Манифест HTML-копий холста — `kit.json`: в git он не
хранится, съёмка считает его сама сборкой `kit/kit_manifest.py` из статичных копий артбордов (кадр — копия на ширине и
высоте своей рамки; подписи и порядок — из `canvas.json` исходников холста, ключ --canvas, без ключа — папка `project`
рядом с папкой копий; ряды холста — набор ширин входа холста или проекта, без них — набор базы). Все ширины приёмки —
артборды холста, поэтому своих ширин у съёмки нет; вылет на 320, ресайз и зум проверяются на собранной странице в
репозитории кода. `--manifest` — имя файла в папке копий или путь к манифесту, собранному вне её (от рабочей папки
или абсолютный): копии при этом остаются нетронутыми; `--manifest kit.json` без такого файла — манифест считается.

Использование:
  python3 shot.py <папка копий> <outdir> [--manifest kit.json | ПУТЬ/kit.json] [--canvas ПАПКА] [--only landing.html]
          [--themes light,dark] [--scale 1] [--tiles] [--no-plain] [--no-marks] [--no-canvas] [--canvas-dpr 0.5]
          [--set "radius-md=16px;color-accent=#0a7d4f"] [--prev review/iter-01/marks.json] [--iteration iter-02]
          [--lock ФАЙЛ] [--min-free-gb 2] [--strict]
  python3 shot.py serve <папка проекта> [--port 8765]
      → http://127.0.0.1:8765/ перенаправляет на /_kit/canvas.html?m=/canvas.json&marks=1 (холст для встроенного браузера
        приложения через .claude/launch.json или для своего браузера)
  python3 shot.py --selftest      офлайн: шрифты и их метрические двойники, H1 у частей артборда, путь манифеста,
                                  манифест копий при съёмке, служебные пометки артборда вне проверок кадра, замок браузера

Что пишет в <outdir>:
  <файл>-<W>-<тема>.png            артборд целиком (full page) без меток
  <файл>-<W>-<тема>-marks.png      то же с метками #N; при --tiles ещё …-marks-tNN.png по высоте кадра (удобно читать)
  canvas.png, canvas-marks.png     весь холст (рамки рядами по ширинам, подписи), DPR --canvas-dpr
  marks.json                       номер → файл, вид, тег, селектор, текст, родитель; по кадрам: видимость, прямоугольник, бейдж
  marks.md                         та же карта короткой таблицей (для чата)
  shots.json                       кадры, проверки, предупреждения, согласованность меток холста и кадров
Номера: блоки по файлам (base из manifest.marks или 100 × порядок файла); один номер = один элемент на всех ширинах и темах
этого файла; --prev переносит номера прошлой итерации (совпадение: селектор+тег+текст → тег+текст → селектор+тег).
Проверки кадра (`failed_checks`). H1 на странице один: у артборда целиком — ровно один; страница длиннее предела высоты
артборда лежит частями `<Имя>-<ширина>-<N>` — H1 в первой части, у следующих его нет. Шрифт: объявлен веб-шрифт, а
рисуется системный с другим именем — `fonts_missing`; метрический двойник системного шрифта (Arimo на месте Arial) —
не пропажа: объявленного системного шрифта на машине нет, раскладка та же. Служебные пометки артборда — элементы с
атрибутом `data-wf` и их поддерево — не текст страницы: в счёт мелкого текста, наименьший кегль и невидимый текст они не
входят.
Замок браузера съёмка берёт сама на время работы браузера: браузер один за раз на машину. Умолчание --lock — общий
замок окружения, его берёт `kbpaths.lock("browser")`: замок реентерабелен по дереву процессов, поэтому съёмка, запущенная
из утилиты, которая держит тот же замок, его не ждёт, а чужого держателя ждёт до 15 минут. `--lock ФАЙЛ` (или переменная
KIT_BROWSER_LOCK) — другой файл замка, его съёмка держит своим flock без повторного входа; `--lock ""` — без замка.
Коды выхода: 0 — готово; 2 — страница или браузер не открылись, замок браузера не дождался или мало памяти
(--min-free-gb); 3 — нет кадров (манифест не читается, в нём нет рамок или --only мимо); 4 — --strict и есть непройденные
проверки, наложения меток или расхождение номеров холста и кадров.
"""
import argparse, contextlib, fcntl, functools, http.server, json, os, re, socketserver, sys, threading, time
from datetime import datetime, timezone
from urllib.parse import quote, unquote, urlparse

KIT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(KIT_DIR, '..', '..', 'lib'))
import kbpaths  # noqa: E402

kbpaths.use('claude-design')
from mockup_checks import artboard_part  # noqa: E402  (имя части артборда — одно правило с проверками макета)

GENERIC = {'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui', 'ui-sans-serif', 'ui-serif',
           'ui-monospace', 'ui-rounded', '-apple-system', 'blinkmacsystemfont', 'emoji', 'math', 'fangsong'}
# Метрические двойники системных шрифтов: на машине без Arial, Times New Roman или Courier New fontconfig рисует шрифт
# с теми же метриками — раскладка не меняется, и веб-шрифт тут не терялся.
_SANS, _SERIF, _MONO = ('arimo', 'liberation sans', 'nimbus sans'), ('tinos', 'liberation serif', 'nimbus roman'), \
    ('cousine', 'liberation mono', 'nimbus mono')
METRIC_TWINS = {'arial': _SANS, 'helvetica': _SANS, 'arial narrow': ('liberation sans narrow',),
                'times new roman': _SERIF, 'times': _SERIF, 'courier new': _MONO, 'courier': _MONO,
                'calibri': ('carlito',), 'cambria': ('caladea',), 'georgia': ('gelasio',)}
MANIFEST_URL = '/_kit-manifest.json'       # манифест вне папки копий: холст берёт его из памяти сервера, кадры — из папки
KIT_NAME = 'kit.json'                      # манифест статичных копий: файла нет — считается при съёмке

# --- проверки страницы (плейсхолдеры — любые [КАПС-МЕТКИ]) ---------------------------------------------------------------
CHECKS_JS = r"""
(conf) => {
  const vw = conf.vw || document.documentElement.clientWidth;
  const touch = conf.touch;
  const sw = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
  const desc = (el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
      ((el.className && typeof el.className === 'string' && el.className.trim()) ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
  const off = [];
  if (sw > vw + 1) {
    for (const el of document.querySelectorAll('body *')) {
      if (el.id === 'kit-marks-host') continue;
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.right > vw + 1) {
        const inner = [...el.children].some(c => c.getBoundingClientRect().right > vw + 1);
        if (!inner) off.push({el: desc(el), right: Math.round(r.right), width: Math.round(r.width)});
      }
      if (off.length >= 5) break;
    }
  }
  const host = location.host;
  const imgs = [...document.images];
  const broken = imgs.filter(i => i.complete && i.naturalWidth === 0).slice(0, 10).map(i => i.getAttribute('src'));
  const external = imgs.map(i => i.currentSrc || i.src).filter(s => {
      if (!s || s.startsWith('data:') || s.startsWith('blob:')) return false;
      try { return new URL(s, location.href).host !== host; } catch (e) { return false; } }).slice(0, 10);
  const noAlt = imgs.filter(i => !i.hasAttribute('alt')).length;
  const opacityChain = (el) => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const cs = getComputedStyle(e); o *= parseFloat(cs.opacity); if (cs.visibility === 'hidden') return 0; } return o; };
  let small = 0, minFont = 999; const fonts = {}; const invisible = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const t = walker.currentNode; if (!t.textContent.trim()) continue;
    const el = t.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
    if (el.closest('[data-wf]')) continue;                 // служебная пометка артборда и её поддерево — не текст страницы
    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    if (cs.display === 'none' || r.width === 0 || r.height === 0) continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'TITLE'].includes(el.tagName)) continue;
    if (opacityChain(el) < 0.1) { if (invisible.length < 8) invisible.push({el: desc(el), text: t.textContent.trim().slice(0, 40)}); continue; }
    const fs = parseFloat(cs.fontSize); if (fs < minFont) minFont = fs; if (fs < 12) small++;
    const fam = cs.fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, '');
    fonts[fam] = (fonts[fam] || 0) + 1;
  }
  const targets24 = [], targets44 = [];
  if (touch) {
    const sel = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=link]';
    for (const el of document.querySelectorAll(sel)) {
      const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
      if (r.width === 0 || r.height === 0 || cs.visibility === 'hidden') continue;
      const p = el.parentElement;
      const inlineText = el.tagName === 'A' && cs.display.startsWith('inline') && p &&
          (p.textContent || '').trim().length > (el.textContent || '').trim().length + 20;
      const m = Math.min(r.width, r.height);
      const item = {el: desc(el), w: Math.round(r.width), h: Math.round(r.height), inline_text_link: inlineText};
      if (m < 24 && !inlineText) { if (targets24.length < 8) targets24.push(item); }
      else if (m < 44 && !inlineText) { if (targets44.length < 8) targets44.push(item); }
    }
  }
  const text = document.body ? document.body.innerText : '';
  const ph = text.match(/\[[A-ZА-ЯЁ][A-ZА-ЯЁ0-9 _-]{1,40}\]/g) || [];
  return {viewport_width: vw, scroll_width: sw, overflow_px: Math.max(0, sw - vw), overflow_elements: off,
          page_height: document.documentElement.scrollHeight, lang: document.documentElement.getAttribute('lang') || '',
          h1_count: document.querySelectorAll('h1').length, broken_images: broken, external_images: external,
          images_without_alt: noAlt, invisible_text: invisible, small_text_elements: small,
          min_font_px: minFont === 999 ? null : minFont, small_targets_24: targets24, small_targets_44: targets44,
          placeholders: ph.length, placeholder_list: [...new Set(ph)].slice(0, 12), fonts_used: fonts};
}
"""

SAMPLE_JS = r"""
(sels) => sels.map(s => { const el = [...document.querySelectorAll(s)].find(e => {
    const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && e.textContent.trim(); });
  if (!el) return null; el.setAttribute('data-shot-sample', s);
  return {selector: s, declared: getComputedStyle(el).fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, '')}; })
"""


def platform_fonts(ctx, page):
    """Какие шрифты реально отрисованы у образцов (CDP CSS.getPlatformFontsForNode)."""
    try:
        samples = [s for s in page.evaluate(SAMPLE_JS, ['h1', 'h2', 'h3', 'p', 'button', 'label', 'a']) if s]
        cdp = ctx.new_cdp_session(page)
        cdp.send('DOM.enable'); cdp.send('CSS.enable')
        root = cdp.send('DOM.getDocument', {'depth': -1})['root']['nodeId']
        out = []
        for s in samples:
            nid = cdp.send('DOM.querySelector', {'nodeId': root, 'selector': f'[data-shot-sample="{s["selector"]}"]'})['nodeId']
            if not nid:
                continue
            fonts = cdp.send('CSS.getPlatformFontsForNode', {'nodeId': nid}).get('fonts', [])
            fonts = sorted(fonts, key=lambda f: -f.get('glyphCount', 0))
            out.append({**s, 'rendered': [{'family': f.get('familyName'), 'custom': f.get('isCustomFont'),
                                           'glyphs': f.get('glyphCount')} for f in fonts[:3]]})
        cdp.detach()
        page.evaluate("() => document.querySelectorAll('[data-shot-sample]').forEach(e => e.removeAttribute('data-shot-sample'))")
        return out
    except Exception as e:  # noqa: BLE001 — проверка шрифтов не должна ронять съёмку
        return [{'error': f'{type(e).__name__}: {str(e)[:120]}'}]


def fonts_missing(samples):
    """Объявлен не-generic шрифт, а рисуется системный с другим именем (веб-шрифт не загрузился). Метрический двойник
    объявленного системного шрифта (METRIC_TWINS) — не пропажа."""
    missing = []
    for s in samples:
        if 'error' in s or not s.get('rendered'):
            continue
        dec = (s.get('declared') or '').lower()
        if not dec or dec in GENERIC:
            continue
        top = s['rendered'][0]
        fam = (top.get('family') or '').lower()
        if top.get('custom') or fam.startswith(dec) or dec in fam or fam.startswith(METRIC_TWINS.get(dec, ())):
            continue
        missing.append({'selector': s['selector'], 'declared': s['declared'], 'rendered': top.get('family')})
    return missing


def failed_checks(v):
    f = []
    if v['overflow_px'] > 0: f.append('overflow_px')
    for k in ('console_errors', 'broken_images', 'external_images', 'invisible_text', 'small_targets_24', 'fonts_missing'):
        if v.get(k): f.append(k)
    if v['small_text_elements'] > 0: f.append('small_text_elements')
    if v['images_without_alt'] > 0: f.append('images_without_alt')
    # H1 на странице один: у частей артборда он в первой части, у следующих его нет
    if v['h1_count'] != (0 if (v.get('part') or 1) > 1 else 1): f.append('h1_count')
    if not v['lang']: f.append('lang')
    return f


# --- ресурсы: блокировка браузера и память ------------------------------------------------------------------------------
def mem_available_gb():
    try:
        for line in open('/proc/meminfo', encoding='ascii'):
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) / 1024 / 1024
    except OSError:
        pass
    return None


def browser_lock(path):
    """Замок браузера на время его работы. Общий замок окружения (`kbpaths.lock_path("browser")`) — через
    `kbpaths.lock("browser")`: реентерабелен по дереву процессов, чужого держателя ждёт до 15 минут (TimeoutError).
    Другой файл (--lock ФАЙЛ, переменная KIT_BROWSER_LOCK) — свой flock без повторного входа; пустой путь — без замка."""
    if not path:
        return contextlib.nullcontext()
    if os.path.abspath(path) == os.path.abspath(kbpaths.lock_path('browser')):
        return kbpaths.lock('browser')
    return _file_lock(path)


@contextlib.contextmanager
def _file_lock(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'a') as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield path
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


# --- сервер: проект + /_kit/ + /_virtual/ -------------------------------------------------------------------------------
class Handler(http.server.SimpleHTTPRequestHandler):
    virtual = {}
    root_redirect = None          # в режиме serve «/» ведёт сразу на холст

    def __init__(self, *a, project=None, **kw):
        self.project = project
        super().__init__(*a, directory=project, **kw)

    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def translate_path(self, path):
        p = unquote(urlparse(path).path)
        if p.startswith('/_kit/'):
            name = os.path.basename(p[len('/_kit/'):])
            return os.path.join(KIT_DIR, name)
        return super().translate_path(path)

    def do_GET(self):
        p = unquote(urlparse(self.path).path)
        if p == '/' and Handler.root_redirect:
            self.send_response(302)
            self.send_header('Location', Handler.root_redirect)
            self.end_headers()
            return
        if p in Handler.virtual:
            body = Handler.virtual[p]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()


def serve(project, port=0):
    handler = functools.partial(Handler, project=os.path.abspath(project))
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', port), handler)
    httpd.daemon_threads = True
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f'http://127.0.0.1:{httpd.server_address[1]}'


# --- нумерация ------------------------------------------------------------------------------------------------------------
def assign_numbers(cands, base, prev):
    """cands — кандидаты канонического кадра в порядке DOM; prev — метки этого файла из прошлого marks.json.
    Возвращает (pin {селектор: номер}, отчёт о переносе)."""
    pin, used, report = {}, set(), {'kept': 0, 'moved': [], 'new': [], 'removed': []}
    if prev:
        def take(c, p, how):
            pin[c['selector']] = p['n']; used.add(p['n'])
            if how != 'same':
                report['moved'].append({'n': p['n'], 'how': how, 'from': p['selector'], 'to': c['selector']})
            else:
                report['kept'] += 1
        for c in cands:                                   # 1) тот же элемент: селектор + тег + текст
            for p in prev:
                if p['n'] not in used and p['selector'] == c['selector'] and p['tag'] == c['tag'] and p.get('text') == c['text']:
                    take(c, p, 'same'); break
        for c in cands:                                   # 2) элемент переехал: уникальная пара тег + текст
            if c['selector'] in pin or not c['text']:
                continue
            hits = [p for p in prev if p['n'] not in used and p['tag'] == c['tag'] and p.get('text') == c['text']]
            if len(hits) == 1:
                take(c, hits[0], 'text')
        for c in cands:                                   # 3) текст поменяли на том же месте: селектор + тег
            if c['selector'] in pin:
                continue
            for p in prev:
                if p['n'] not in used and p['selector'] == c['selector'] and p['tag'] == c['tag']:
                    take(c, p, 'selector'); break
        top = max([base] + [p['n'] for p in prev])
        report['removed'] = sorted(p['n'] for p in prev if p['n'] not in used)
    else:
        top = base
    nxt = top
    for c in cands:
        if c['selector'] in pin:
            continue
        nxt += 1
        while nxt in used:
            nxt += 1
        pin[c['selector']] = nxt; used.add(nxt)
        if prev:
            report['new'].append(nxt)
    return pin, report


def parse_set(s):
    pairs = []
    for part in (s or '').split(';'):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition('=')
        k = k.strip()
        if not k.startswith('--'):
            k = '--' + k
        if len(k) < 3 or not v.strip():
            raise SystemExit(f'--set: ожидается "имя=значение" (имя CSS-переменной, можно без --), получено "{part}"')
        pairs.append((k, v.strip()))
    return pairs


def slug(s):
    return re.sub(r'[^\w.-]+', '-', s, flags=re.UNICODE).strip('-_.') or 'design'


def manifest_path(project, name):
    """Файл манифеста: имя в папке копий, а когда такого файла там нет — путь как передан (от рабочей папки или
    абсолютный): манифест, собранный вне папки копий."""
    inside = os.path.join(project, name)
    return inside if os.path.isfile(inside) or not os.path.isfile(name) else os.path.abspath(name)


def copies_manifest(project, canvas=None):
    """Манифест статичных копий папки — сборка `kit_manifest.build_manifest`: исходники холста — canvas или папка
    `project` рядом с папкой копий (раскладка `design/<surface>/canvas/`), без них кадры идут по имени файла."""
    if KIT_DIR not in sys.path:
        sys.path.insert(0, KIT_DIR)
    import kit_manifest
    side = os.path.join(os.path.dirname(os.path.abspath(project)), 'project')
    return kit_manifest.build_manifest(project, canvas or (side if os.path.isdir(side) else None))


def read_manifest(project, name, canvas=None):
    """Манифест кадров → (манифест, путь файла, посчитан ли): файл папки копий или путь как передан; `kit.json`,
    которого нет ни там, ни там, — сборка из статичных копий папки (copies_manifest). Файл не читается — OSError или
    ValueError."""
    path = manifest_path(project, name)
    computed = os.path.basename(name) == KIT_NAME and not os.path.isfile(path) and os.path.isdir(project)
    return (copies_manifest(project, canvas) if computed else json.load(open(path, encoding='utf-8'))), path, computed


def selftest():
    import subprocess, tempfile
    ok = True

    def check(name, cond, got=None):
        nonlocal ok
        ok &= bool(cond)
        print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else f' → {got}'))

    def sample(declared, family, custom=False):
        return {'selector': 'p', 'declared': declared, 'rendered': [{'family': family, 'custom': custom, 'glyphs': 9}]}

    miss = fonts_missing([sample('Arial', 'Arimo'), sample('Times New Roman', 'Liberation Serif'),
                          sample('Golos Text', 'DejaVu Sans'), sample('Golos Text', 'Golos Text', True), sample('system-ui', 'DejaVu Sans'),
                          sample('Arial', 'DejaVu Serif')])
    check('шрифты: метрический двойник системного шрифта — не пропажа; веб-шрифт или Arial, отрисованные чужим '
          'системным, — пропажа', [(m['declared'], m['rendered']) for m in miss]
          == [('Golos Text', 'DejaVu Sans'), ('Arial', 'DejaVu Serif')], miss)
    base = {'overflow_px': 0, 'small_text_elements': 0, 'images_without_alt': 0, 'lang': 'ru'}
    got = [failed_checks(dict(base, h1_count=n, part=part)) for n, part in ((1, None), (0, None), (1, 1), (0, 1), (0, 2), (1, 2))]
    check('H1 один на страницу: артборд целиком и первая часть — ровно один, следующие части — ни одного',
          got == [[], ['h1_count'], [], ['h1_count'], [], ['h1_count']], got)
    parts = [artboard_part(n, w)[1] for n, w in (('Home-390-1.html', 390), ('Home-390-2.dc.html', 390), ('Home-1440.html', 1440))]
    check('часть артборда — по имени копии и ширине кадра манифеста', parts == [1, 2, None], parts)
    with tempfile.TemporaryDirectory() as td:
        td = os.path.realpath(td)
        proj, other = os.path.join(td, 'html'), os.path.join(td, 'out')
        os.makedirs(proj); os.makedirs(other)
        for d in (proj, other):
            open(os.path.join(d, 'kit.json'), 'w', encoding='utf-8').write('{"artboards": []}')
        open(os.path.join(other, 'side.json'), 'w', encoding='utf-8').write('{"artboards": []}')
        cwd = os.getcwd()
        os.chdir(td)
        try:
            got = [manifest_path(proj, 'kit.json'), manifest_path(proj, os.path.join(other, 'side.json')),
                   manifest_path(proj, os.path.join('out', 'side.json'))]
        finally:
            os.chdir(cwd)
        check('манифест: имя — файл папки копий; путь вне папки копий — как передан, абсолютный и от рабочей папки',
              got == [os.path.join(proj, 'kit.json'), os.path.join(other, 'side.json'), os.path.join(other, 'side.json')], got)
        run = lambda *args: subprocess.run([sys.executable, os.path.abspath(__file__), proj, os.path.join(td, 'shots'), *args],  # noqa: E731
                                           capture_output=True, text=True, cwd=td)
        r = run('--manifest', 'nope.json')
        check('манифеста нет — сообщение и код 3, без трассировки',
              r.returncode == 3 and 'манифест не читается' in r.stderr and 'Traceback' not in r.stderr, (r.returncode, r.stderr[-300:]))
        r = run('--manifest', os.path.join('out', 'side.json'))
        check('манифест вне папки копий читается: рамок в нём нет — код 3, без трассировки',
              r.returncode == 3 and 'нет рамок' in r.stderr and 'Traceback' not in r.stderr, (r.returncode, r.stderr[-300:]))
        bare = os.path.join(td, 'design', 'promo', 'canvas', 'html')
        os.makedirs(bare)
        for name, w, h in (('Page-1440.html', 1440, 2000), ('Page-390.html', 390, 3000)):
            open(os.path.join(bare, name), 'w', encoding='utf-8').write(
                f'<!doctype html><head><!-- dc_to_html: статичная копия артборда {name[:-5]}.dc.html; перевод исходника · '
                f'рамка {w}×{h} · твики: — --></head><p>т</p>')
        open(os.path.join(bare, 'note.html'), 'w', encoding='utf-8').write('<!doctype html><p>не копия</p>')
        man = copies_manifest(bare)
        check('манифест копий считается при съёмке: кадр на статичную копию на её рамке, ряды — набор базы',
              ([(f['file'], f['w'], f['h']) for f in man['artboards']], len(man['widths']) >= 2)
              == ([('Page-1440.html', 1440, 2000), ('Page-390.html', 390, 3000)], True), man)
        open(os.path.join(td, 'design', 'ARTIFACTS.md'), 'w', encoding='utf-8').write(
            '# Артефакты\n\n## Условия холста\n\nШирины приёмки: 1440, 390 — набор проекта\n')
        check('ряды манифеста — набор ширин проекта из ARTIFACTS.md', copies_manifest(bare)['widths'] == [1440, 390],
              copies_manifest(bare)['widths'])
        got = [(len(m['artboards']), c) for m, _p, c in (read_manifest(bare, 'kit.json'), read_manifest(proj, 'kit.json'))]
        check('чтение манифеста: kit.json нет — считается из копий; файл есть — читается', got == [(2, True), (0, False)], got)
        os.makedirs(os.path.join(td, 'design', 'promo', 'input'))
        open(os.path.join(td, 'design', 'promo', 'input', 'INPUT.md'), 'w', encoding='utf-8').write(
            '---\nstage: mockup\nacceptance_widths: [1440, 1024, 390]\n---\n# Вход холста\n')
        check('ряды манифеста — набор входа холста (acceptance_widths в INPUT.md) первым',
              copies_manifest(bare)['widths'] == [1440, 1024, 390], copies_manifest(bare)['widths'])
        r = subprocess.run([sys.executable, os.path.abspath(__file__), os.path.join(td, 'out'), os.path.join(td, 'shots'),
                            '--manifest', 'nope/kit.json'], capture_output=True, text=True, cwd=td)
        check('папка без статичных копий и без kit.json: манифест считается пустым — код 3, без трассировки',
              r.returncode == 3 and 'нет рамок' in r.stderr and 'Traceback' not in r.stderr, (r.returncode, r.stderr[-300:]))
    check('проверки кадра: служебная пометка артборда data-wf и её поддерево — вне счёта мелкого и невидимого текста',
          re.search(r"closest\('\[data-wf\]'\)\) continue;[^\n]*\n\s*const cs = getComputedStyle\(el\)", CHECKS_JS) is not None)
    home0 = os.environ.get('DDD_HOME')
    with tempfile.TemporaryDirectory() as td:          # замки — во временном $DDD_HOME, общий замок машины не трогается
        os.environ['DDD_HOME'] = td
        try:
            nested = "import sys; sys.path.insert(0, %r); import kbpaths\nwith kbpaths.lock('browser', timeout=5): pass" % \
                os.path.join(KIT_DIR, '..', '..', 'lib')
            with browser_lock(kbpaths.lock_path('browser')):
                held = kbpaths.lock_held('browser')
                t0 = time.monotonic()
                rc = subprocess.run([sys.executable, '-c', nested], capture_output=True, text=True, timeout=60).returncode
                quick = time.monotonic() - t0 < 5
            free = not kbpaths.lock_held('browser')
            with browser_lock(''):
                none = kbpaths.lock_held('browser')
            with browser_lock(os.path.join(td, 'other.lock')):
                other = (kbpaths.lock_held('browser'), os.path.exists(os.path.join(td, 'other.lock')))
        finally:
            if home0 is None:
                os.environ.pop('DDD_HOME', None)
            else:
                os.environ['DDD_HOME'] = home0
    got = (held, rc, quick, free, none, other)
    check('замок браузера: общий файл — kbpaths.lock (назван в DDD_LOCKS_HELD), вложенный процесс с тем же замком не ждёт, '
          'после выхода замок свободен; --lock "" — без замка; другой файл — свой flock', got == (True, 0, True, True, False,
                                                                                               (False, True)), got)
    print('selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('--selftest', 'selftest'):
        return selftest()
    if len(sys.argv) > 1 and sys.argv[1] == 'serve':
        ap = argparse.ArgumentParser(prog='shot.py serve')
        ap.add_argument('cmd'); ap.add_argument('project'); ap.add_argument('--port', type=int, default=8765)
        ap.add_argument('--manifest', default='canvas.json')
        a = ap.parse_args()
        Handler.root_redirect = f'/_kit/canvas.html?m=/{quote(a.manifest)}&marks=1'
        httpd, base = serve(a.project, a.port)
        print(f'холст:  {base}/_kit/canvas.html?m=/{a.manifest}&marks=1\nбез меток: {base}/_kit/canvas.html?m=/{a.manifest}\n'
              f'Ctrl+C — остановить', flush=True)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            httpd.shutdown()
        return 0

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project'); ap.add_argument('outdir')
    ap.add_argument('--manifest', default='canvas.json', help='манифест кадров: kit.json HTML-копий холста (файла нет — '
                                                              'считается при съёмке) или canvas.json kit')
    ap.add_argument('--canvas', default='', help='папка исходников холста с canvas.json: подписи и порядок кадров '
                                                 'манифеста копий; без ключа — папка project рядом с папкой копий')
    ap.add_argument('--only', default='', help='только рамки этого файла (через запятую)')
    ap.add_argument('--themes', default='', help='снять каждую рамку во всех темах списка, напр. light,dark')
    ap.add_argument('--scale', type=float, default=1.0, help='DPR кадров артбордов (2 — «ретина»)')
    ap.add_argument('--tiles', action='store_true', help='порезать кадры с метками на куски высотой в экран')
    ap.add_argument('--no-plain', action='store_true'); ap.add_argument('--no-marks', action='store_true')
    ap.add_argument('--no-canvas', action='store_true')
    ap.add_argument('--canvas-dpr', type=float, default=0.5)
    ap.add_argument('--set', default='', help='временная подмена CSS-переменных: "radius-md=4px;color-accent=#0B6E4F" (имена можно без --)')
    ap.add_argument('--prev', default='', help='marks.json прошлой итерации — перенести номера')
    ap.add_argument('--iteration', default='')
    ap.add_argument('--wait-ms', type=int, default=350)
    ap.add_argument('--lock', default=os.environ.get('KIT_BROWSER_LOCK') or kbpaths.lock_path('browser'),
                    help='файл замка браузера: умолчание — общий замок окружения (kbpaths.lock), другой файл — свой flock, '
                         '"" — без замка')
    ap.add_argument('--min-free-gb', type=float, default=float(os.environ.get('KIT_MIN_FREE_GB', '0') or 0))
    ap.add_argument('--strict', action='store_true')
    a = ap.parse_args()

    project = os.path.abspath(a.project)
    man_path = manifest_path(project, a.manifest)
    try:
        manifest, man_path, computed = read_manifest(project, a.manifest, a.canvas)
    except (OSError, ValueError) as e:
        print(json.dumps({'error': f'манифест не читается: {man_path} ({type(e).__name__}: {e})'}, ensure_ascii=False),
              file=sys.stderr)
        return 3
    man_rel = os.path.relpath(man_path, project)
    if computed or man_rel.startswith('..'):
        Handler.virtual[MANIFEST_URL] = json.dumps(manifest, ensure_ascii=False).encode('utf-8')
        man_url = MANIFEST_URL
    else:
        man_url = '/' + quote(man_rel.replace(os.sep, '/'))
    sets = parse_set(a.set)
    only = [x.strip() for x in a.only.split(',') if x.strip()]
    themes = [t.strip() for t in a.themes.split(',') if t.strip()]

    frames = []
    for ab in manifest.get('artboards', []):
        if only and ab['file'] not in only:
            continue
        for th in (themes or [ab.get('theme', 'light')]):
            frames.append({**ab, 'theme': th})
    if not frames:
        print(json.dumps({'error': 'нет рамок (проверьте --only и manifest)'}, ensure_ascii=False), file=sys.stderr)
        return 3
    files = []
    for fr in frames:
        if fr['file'] not in files:
            files.append(fr['file'])
    all_files = []
    for ab in manifest.get('artboards', []):
        if ab['file'] not in all_files:
            all_files.append(ab['file'])
    bases = {}
    for f in files:
        mm = (manifest.get('marks') or {}).get(f) or {}
        bases[f] = mm.get('base', all_files.index(f) * 100)

    prev_by_file = {}
    if a.prev:
        prev = json.load(open(a.prev, encoding='utf-8'))
        for m in prev.get('marks', []):
            prev_by_file.setdefault(m['file'], []).append(m)

    if a.min_free_gb:
        gb = mem_available_gb()
        if gb is not None and gb < a.min_free_gb:
            print(json.dumps({'error': f'мало памяти: доступно {gb:.1f} ГБ < {a.min_free_gb} ГБ'}, ensure_ascii=False), file=sys.stderr)
            return 2

    os.makedirs(a.outdir, exist_ok=True)
    outdir = os.path.abspath(a.outdir)
    marks_src = os.path.join(KIT_DIR, 'marks.js')
    set_css = ''.join(f'{k}:{v} !important;' for k, v in sets)
    t0 = time.time()
    shots = {'tool': 'kit/shot.py', 'version': '1', 'created': datetime.now(timezone.utc).isoformat(timespec='seconds'),
             'project': project, 'manifest': a.manifest, 'iteration': a.iteration or manifest.get('iteration', ''),
             'set': dict(sets), 'frames': [], 'warnings': [], 'canvas': {}}
    marks_out = {'tool': 'kit/shot.py + kit/marks.js', 'version': '1', 'created': shots['created'], 'iteration': shots['iteration'],
                 'project': project, 'manifest': a.manifest, 'set': dict(sets), 'files': {}, 'marks': [], 'frames': []}
    pins, cand_info = {}, {}

    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    httpd, base_url = serve(project)

    def open_frame(browser, fr, dpr):
        w, h = int(fr['w']), int(fr['h'])
        scheme = fr['theme'] if fr['theme'] in ('light', 'dark') else None
        ctx = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr, is_mobile=w < 768,
                                  has_touch=w < 1024, reduced_motion='reduce', color_scheme=scheme)
        page = ctx.new_page()
        errs, failed = [], []
        page.on('console', lambda m: errs.append(m.text[:300]) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errs.append(('pageerror: ' + str(e))[:300]))
        page.on('requestfailed', lambda r: failed.append({'url': r.url[:160], 'error': (r.failure or '')[:100]}))
        try:
            page.goto(f"{base_url}/{quote(fr['file'])}", wait_until='networkidle', timeout=60000)
        except PWTimeout:
            shots['warnings'].append(f"{fr['file']} {w}: networkidle timeout")
        try:
            page.evaluate('document.fonts ? document.fonts.ready.then(() => true) : true')
        except Exception:
            pass
        if scheme:
            page.evaluate("(t) => { document.documentElement.setAttribute('data-theme', t); document.documentElement.style.colorScheme = t; }", scheme)
        if set_css:
            page.add_style_tag(content=':root, :root[data-theme]{' + set_css + '}')
        page.wait_for_timeout(a.wait_ms)
        total = page.evaluate('document.documentElement.scrollHeight')
        y = 0
        while y < total:
            page.evaluate(f'window.scrollTo(0, {y})'); page.wait_for_timeout(60); y += h
        page.evaluate('window.scrollTo(0, 0)'); page.wait_for_timeout(a.wait_ms)
        return ctx, page, errs, failed

    try:
        with browser_lock(a.lock), sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                # 1) канонический кадр каждого файла → номера
                for f in files:
                    fr0 = next(fr for fr in frames if fr['file'] == f)
                    ctx, page, _, _ = open_frame(browser, fr0, 1)
                    page.evaluate('window.__kitMarksManual = true')
                    page.add_script_tag(path=marks_src)
                    cands = page.evaluate("() => window.__kitMarks.collect().map(c => ({selector: c.selector, kind: c.kind, tag: c.tag, text: c.text, th: c.th}))")
                    ctx.close()
                    pin, rep = assign_numbers(cands, bases[f], prev_by_file.get(f))
                    pins[f] = pin
                    cand_info[f] = {c['selector']: c for c in cands}
                    nums = sorted(pin.values())
                    marks_out['files'][f] = {'base': bases[f], 'count': len(nums), 'first': nums[0] if nums else None,
                                             'last': nums[-1] if nums else None,
                                             'overflow': any(n - bases[f] >= 100 for n in nums)}
                    if a.prev:
                        marks_out['files'][f]['from_prev'] = rep
                    if marks_out['files'][f]['overflow']:
                        shots['warnings'].append(f'{f}: номеров больше 99 — задайте manifest.marks["{f}"].base с запасом')

                by_n = {}
                for f in files:
                    for sel, n in pins[f].items():
                        c = cand_info[f][sel]
                        by_n[(f, n)] = {'n': n, 'file': f, 'kind': c['kind'], 'tag': c['tag'], 'selector': sel, 'text': c['text'],
                                        'th': c.get('th'), 'parent': None, 'frames': {}}

                # 2) кадры
                for fr in frames:
                    w, h, th = int(fr['w']), int(fr['h']), fr['theme']
                    fid = f"{fr['file']}@{w}x{h}@{th}"
                    stem = f"{slug(os.path.splitext(fr['file'])[0])}-{w}-{th}"
                    ctx, page, errs, failed = open_frame(browser, fr, a.scale)
                    checks = page.evaluate(CHECKS_JS, {'vw': w, 'touch': w < 1024})
                    samples = platform_fonts(ctx, page)
                    view = {'id': fid, 'title': fr.get('title', ''), 'file': fr['file'], 'w': w, 'h': h, 'theme': th,
                            'part': artboard_part(fr.get('artboard') or fr['file'], w)[1], **checks,
                            'fonts_missing': fonts_missing(samples), 'font_samples': samples,
                            'console_errors': errs[:10], 'failed_requests': failed[:10]}
                    view['failed_checks'] = failed_checks(view)
                    if not a.no_plain:
                        path = os.path.join(outdir, f'{stem}.png')
                        page.screenshot(path=path, full_page=True)
                        view['png'] = path
                    if not a.no_marks:
                        page.evaluate('window.__kitMarksManual = true')
                        page.add_script_tag(path=marks_src)
                        res = page.evaluate('(o) => window.__kitMarks.run(o)', {'base': bases[fr['file']], 'pin': pins[fr['file']]})
                        page.wait_for_timeout(80)
                        path = os.path.join(outdir, f'{stem}-marks.png')
                        page.screenshot(path=path, full_page=True)
                        view['png_marks'] = path
                        badges = {b['n']: b for b in res['badges']}
                        unpinned = [m['n'] for m in res['marks'] if m.get('unpinned')]
                        view['marks_visible'] = sum(1 for m in res['marks'] if m['visible'])
                        view['marks_total'] = len(res['marks'])
                        view['badge_overlaps'] = res['overlaps']
                        view['badge_text_overlaps'] = res.get('textOverlaps', [])
                        view['unpinned'] = unpinned
                        if unpinned:
                            shots['warnings'].append(f'{fid}: элементы вне канонической нумерации {unpinned[:10]}')
                        for m in res['marks']:
                            key = (fr['file'], m['n'])
                            if key not in by_n:
                                by_n[key] = {'n': m['n'], 'file': fr['file'], 'kind': m['kind'], 'tag': m['tag'],
                                             'selector': m['selector'], 'text': m['text'], 'parent': None, 'frames': {}}
                            if m.get('parent') is not None:
                                by_n[key]['parent'] = m['parent']
                            rec = {'visible': m['visible'], 'rect': m['rect'], 'sh': m.get('sh'), 'own': m.get('own'), 'th': m.get('th')}
                            if m['n'] in badges:
                                b = badges[m['n']]
                                rec['badge'] = {'x': b['x'], 'y': b['y'], 'w': b['w'], 'h': b['h'], 'pos': b['pos']}
                            by_n[key]['frames'][fid] = rec
                        if a.tiles:
                            view['tiles'] = cut_tiles(path, int(h * a.scale))
                    shots['frames'].append(view)
                    marks_out['frames'].append({'id': fid, 'title': fr.get('title', ''), 'png': view.get('png'),
                                                'png_marks': view.get('png_marks'), 'tiles': view.get('tiles', []),
                                                'overlaps': view.get('badge_overlaps', []),
                                                'text_overlaps': view.get('badge_text_overlaps', [])})
                    ctx.close()

                marks_out['marks'] = [by_n[k] for k in sorted(by_n, key=lambda k: (files.index(k[0]), k[1]))]

                # 3) весь холст (рамки рядами), номера — те же (pin через /_virtual/pin.json)
                if not a.no_canvas:
                    Handler.virtual['/_virtual/pin.json'] = json.dumps(pins, ensure_ascii=False).encode('utf-8')
                    rows = {}
                    for fr in frames:
                        rows.setdefault(fr['file'], []).append(int(fr['w']))
                    width = max(sum(ws) + 80 * (len(ws) - 1) for ws in rows.values()) + 80
                    q = f"m={man_url}&pin=/_virtual/pin.json"
                    if only:
                        q += '&only=' + quote(only[0])
                    if themes and len(themes) == 1:
                        q += '&theme=' + quote(themes[0])
                    if sets:
                        q += '&set=' + quote(';'.join(f'{k}:{v}' for k, v in sets))
                    for with_marks in ([False] if a.no_marks else [False, True]):
                        ctx = browser.new_context(viewport={'width': width, 'height': 1000}, device_scale_factor=a.canvas_dpr,
                                                  reduced_motion='reduce')
                        page = ctx.new_page()
                        url = f"{base_url}/_kit/canvas.html?{q}{'&marks=1' if with_marks else ''}"
                        page.goto(url, wait_until='networkidle', timeout=90000)
                        page.wait_for_function('window.__kitCanvasReady === true', timeout=90000)
                        page.wait_for_timeout(300)
                        err = page.evaluate('window.__kitCanvasError || null')
                        name = 'canvas-marks.png' if with_marks else 'canvas.png'
                        path = os.path.join(outdir, name)
                        page.screenshot(path=path, full_page=True)
                        shots['canvas']['png_marks' if with_marks else 'png'] = path
                        if err:
                            shots['warnings'].append('холст: ' + err)
                        if with_marks:
                            cm = page.evaluate('window.__kitCanvasMarks') or {}
                            shots['canvas']['consistency'] = canvas_consistency(cm, by_n, frames)
                        ctx.close()
            finally:
                browser.close()
    except Exception as e:  # noqa: BLE001
        shots['error'] = f'{type(e).__name__}: {e}'[:600]
        print(json.dumps(shots, ensure_ascii=False, indent=1)[:4000], file=sys.stderr)
        return 2
    finally:
        httpd.shutdown(); httpd.server_close()

    shots['seconds'] = round(time.time() - t0, 1)
    shots['failed_checks_total'] = sum(len(v['failed_checks']) for v in shots['frames'])
    shots['badge_overlaps_total'] = sum(len(v.get('badge_overlaps', [])) for v in shots['frames'])
    shots['badge_text_overlaps_total'] = sum(len(v.get('badge_text_overlaps', [])) for v in shots['frames'])
    json.dump(shots, open(os.path.join(outdir, 'shots.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if not a.no_marks:
        json.dump(marks_out, open(os.path.join(outdir, 'marks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        write_marks_md(os.path.join(outdir, 'marks.md'), marks_out, files)
    cons = shots['canvas'].get('consistency', {})
    summary = {'outdir': outdir, 'seconds': shots['seconds'], 'frames': len(shots['frames']),
               'marks': {f: marks_out['files'].get(f) for f in files} if not a.no_marks else None,
               'canvas': shots['canvas'].get('png_marks') or shots['canvas'].get('png'),
               'canvas_consistent': cons.get('ok'), 'failed_checks_total': shots['failed_checks_total'],
               'badge_overlaps_total': shots['badge_overlaps_total'],
               'badge_text_overlaps_total': shots['badge_text_overlaps_total'], 'warnings': shots['warnings']}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for v in shots['frames']:
        print(f"[shot] {v['id']}: меток {v.get('marks_visible', '—')}/{v.get('marks_total', '—')}, наложений на метки "
              f"{len(v.get('badge_overlaps', []))}, на текст {len(v.get('badge_text_overlaps', []))}, вылет {v['overflow_px']} px, "
              f"не пройдено: {', '.join(v['failed_checks']) or '—'}", file=sys.stderr)
    bad = (shots['failed_checks_total'] or shots['badge_overlaps_total'] or shots['badge_text_overlaps_total']
           or (cons and not cons.get('ok')))
    return 4 if (a.strict and bad) else 0


def cut_tiles(path, tile_h):
    from PIL import Image
    im = Image.open(path)
    out, y, i = [], 0, 0
    stem = path[:-4]
    while y < im.height:
        box = (0, y, im.width, min(im.height, y + tile_h))
        tp = f'{stem}-t{i:02d}.png'
        im.crop(box).save(tp)
        out.append(tp); y += tile_h; i += 1
    return out


def canvas_consistency(cm, by_n, frames):
    """Совпадают ли номера на холсте с номерами кадров (по каждой рамке — множество (номер, селектор) видимых меток)."""
    res = {'ok': True, 'frames': []}
    frame_sets = {}
    for (f, n), m in by_n.items():
        for fid, rec in m['frames'].items():
            if rec['visible']:
                frame_sets.setdefault(fid, set()).add((n, m['selector']))
    for f, grp in (cm or {}).items():
        for fr in grp.get('frames', []):
            r = fr.get('result') or {}
            got = {(m['n'], m['selector']) for m in r.get('marks', []) if m.get('visible')}
            match = [fid for fid in frame_sets if fid.startswith(f + '@' + str(fr['w']) + 'x') and fid.endswith('@' + fr['theme'])]
            want = frame_sets.get(match[0], set()) if match else set()
            ok = got == want
            res['frames'].append({'file': f, 'w': fr['w'], 'theme': fr['theme'], 'canvas': len(got), 'frame': len(want), 'ok': ok,
                                  'only_canvas': sorted(n for n, _ in got - want)[:10], 'only_frame': sorted(n for n, _ in want - got)[:10]})
            res['ok'] = res['ok'] and ok
    if not res['frames']:
        res['ok'] = False
    return res


def write_marks_md(path, mo, files):
    lines = [f"# Метки #N · {mo.get('iteration') or ''} · {mo['created']}", '',
             'Номер — адрес правки в чате («#7: …»). Номер един для всех ширин и тем файла; видимость — в marks.json.', '']
    for f in files:
        info = mo['files'].get(f, {})
        lines += [f"## {f} (#{info.get('first')}–#{info.get('last')}, всего {info.get('count')})", '',
                  '| # | вид | тег | текст | родитель | селектор |', '|---|---|---|---|---|---|']
        for m in mo['marks']:
            if m['file'] != f:
                continue
            t = (m['text'] or '').replace('|', '\\|')
            lines.append(f"| {m['n']} | {m['kind']} | {m['tag']} | {t} | {m['parent'] or ''} | `{m['selector']}` |")
        lines.append('')
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))


if __name__ == '__main__':
    sys.exit(main())
