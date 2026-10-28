#!/usr/bin/env python3
"""mockup_checks.py — проверки макета по отрисованной HTML-копии: приметы «дефолтного вида», честность содержимого,
формы, телефон, наложения, ресайз. Модель не вызывается; браузер — Chromium Playwright, один за раз.

Место в цикле — слой скриптов проверок макета (claude-design/06-design-process/04-checks.md §2–§4; протокол холста
`references/claude-design.md § Проверки по постоянной просьбе`): на статичных копиях артбордов, только по просьбе
заказчика; все ширины приёмки — артборды холста. Проверки холста — слой ниже ворот страницы и их не заменяют: вылет на
320, ресайз и зум проверяются на собранной странице в репозитории кода (`page --acceptance` и `resize` берут её адрес).

Подкоманды:
  page <url|file.html|dir> [--views 1440x900,390x844 | --acceptance] [--surface page|app] [--preset A|B|C|D]
       [--tokens ТОКЕНЫ_ДС] [--facts facts.md|facts.yaml] [--copy copy.md|copy-deck.yaml [--page ID]]
       [--demo demo-data.json] [--assets assets.md|план.yaml [--uploads ARTIFACTS.md]] [--forms ID|план.yaml …]
       [--src DIR] [--allow warm,serif,…] [--ignore-selector CSS] [--block-external | --allow-external]
       [--shots DIR] [--json OUT.json] [--md OUT.md] [--min-free-gb 2]
       exit 0 — нет critical и кластера примет, 2 — есть, 1 — ошибка, 3 — мало свободной памяти (браузер не
       запускался)
  resize <url|file> [--desktop 1440x900] [--mobile 390x844] [--wait-ms 1000] [--shots DIR] [--min-free-gb 2]
       ресайз без перезагрузки на собранной странице: широкий → узкий → широкий (пункт H5 приёмки, место «после
       сборки»): вылет, навигация, медиа первого экрана за --wait-ms, кадр после возврата совпадает с исходным
       (--max-diff — порог cd 06/04 §3 B); окна по умолчанию — самая широкая ширина приёмки и самая широкая ниже
       первого брейкпоинта эталона ui. JSON в stdout (его читает код-репо): tool, skill_version (файл VERSION
       скилла), command, target, verdict pass · fail · error, problems, steps; error — проверка не шла (мало
       свободной памяти), причина — поле error. exit 0 pass / 1 fail / 3 — мало свободной памяти
  selftest [--browser] [--min-free-gb 2]
       офлайн-проверки: цвет, контраст, числа с единицей и объектом, факты и копия таблицами и YAML, демо-набор,
       список ассетов и реестр загрузок, части артборда, формы, пороги владельцев, id примет, поверхность примет,
       вердикт кластера, токены ДС, сводка по доменам. С --browser — ещё код страницы в Chromium на синтетической
       копии артборда в двух частях (`fixtures/artboard-parts/`): hero, тело, заглушки, служебные пометки артборда,
       навигация частей, медиа против списка ассетов; exit 0 — всё сошлось, 1 — нет, 3 — мало свободной памяти (браузер не
       запускался)

Ширины. У статичной копии артборда окно — её рамка. У другой цели (собранная страница) без --views окна — ширины
артбордов `kb/common/acceptance-widths.yaml` (`artboards` — все ширины приёмки), с --acceptance — ещё отдельный прогон
вылета на `overflow_only`. Высота окна — параметр прогона: 900 у широких окон, 844 у окон уже первого брейкпоинта ДС
(окна первого экрана site). Первый брейкпоинт — из токенов ДС (--tokens: CSS, DTCG или tokens.json артефакта), без них
— эталонные токены ui.
Части артборда. Страница, которая длиннее предела высоты артборда, лежит на холсте частями `<Имя>-<ширина>-<N>`
(`Home-390-1`, `Home-390-2`; ширина в имени — ширина рамки). Шапка с навигацией и H1 — у первой части, поэтому у
следующих навигация не проверяется (M-NAV — справкой), а кадр --shots назван по копии артборда: части одной ширины
друг друга не затирают.
Служебные пометки артборда — элементы с атрибутом `data-wf` (подпись заглушки медиа, ярлык роли секции): не
содержимое страницы. В проверки они не входят — как элементы --ignore-selector.
Поверхность. Ключ --surface: страница сайта (`page`) или экран приложения (`app`). Без ключа у статичной копии из
`design/<surface>/canvas/html/` поверхность называет манифест входа холста (`route` передней части
`design/<surface>/input/INPUT.md`: `app` — экран приложения, `site` и `landing` — страница сайта); манифеста нет —
страница сайта. От поверхности зависят приметы и запреты формы заявки: согласие на обработку персональных данных
требуется у форм сайта и лендинга, у служебной формы кабинета (сотрудник вводит данные клиента) — нет.
Снятие находки. Ключ --allow переводит находку своей проверки в info и помечает её: `allowed`, ключ `allow`, тяжесть
без ключа `base_severity` и причина `reason`; сводка перечисляет снятые находки (`summary.allowed`), отчёт --md —
строкой «Снято решением» с тяжестью без ключа. `no-nav` снимает M-NAV у страницы без меню по плану страницы.

Проверки и id примет. id проверок — ключи раздела `checks` реестра `kb/common/tells.yaml`: там у ключа группа (look —
приметы вида, honesty — честность, acceptance — проверки приёмки), id приметы `tell` и ключ `--allow`. Находка несёт
`tell` и `group` своей строки; сводка называет примету один раз, сколько бы проверок её ни нашли, и считает приметы
по доменам реестра в единице домена-владельца (экран, страница, сцена), не складывая домены (`domains`, `clusters`
реестра и кластеры реестра клише creative).
  Поверхность: примета срабатывает только на поверхности своей записи реестра (`surface`: страничные приметы — ряд
  чисел, hero, пилюля, тёплая бумага, отзывы — на экране приложения не ищутся); проверка без приметы — везде.
  Вердикт (шапка реестра): одиночная примета вида — вопрос заказчику «было ли это решением», minor; примета в
  сложившемся кластере — major. Кластер складывается в единице прогона (страница или экран): кластер реестра — от
  порога владельца (шаблонный хром — ui 11/04 §1.3), без числа у владельца — от двух примет («несколько примет»
  шапки реестра), кандидат `proposed` в вердикт не входит; на странице — кластер реестра клише creative по
  `cluster_rule`; на экране приложения — ещё число маркеров домена app-visual (ui 11/04 §1.3). Приметы вида без ключа
  `--allow` (контраст тёплой палитры, шкала кеглей, высота шапки) — нормы с уровнем своей проверки. Код 1 — critical
  или сложившийся кластер; 2 — ошибка вызова или окружения (файл не читается, неизвестный ключ); 3 — мало свободной
  памяти, браузер не запускался.
  Приметы вида: тёплая тонированная бумага, выделенное слово заголовка, антиква в заголовках, капс-надзаголовки (частота
  — число владельца COPY-C-18: не чаще одного на N секций с заголовком H1, H2), доля капса, пилюля над H1, градиентный
  текст, hero на высоту окна по центру без продолжения (порог высоты — AIL-06 site; hero — блок верхнего уровня с
  H1, а когда этот блок — обёртка вроде рамки копии артборда — секция разметки с H1: `<section>` или `data-section`),
  фото-hero под вуалью, ряд крупных чисел, три одинаковые карточки (вариация длины текстов — AIL-07 site; ряд с
  заглушками `[PLACEHOLDER…]` не мерится: текстов ещё нет), бенто из однотипных плиток и орбита иконок
  (пороги — реестр клише creative), мета-строки «·», стрелки в кнопках и ссылках («»» — кавычка, «↗» у внешней ссылки —
  законна), моно-подписи, нумерация 01/02/03, стекло, бегущая строка, нарисованный хром, шкала кеглей и высота шапки
  (пороги — `scripts/ui/data/thresholds.yaml`: кегли — одни для всех поверхностей, шапка — по поверхности: страница
  сайта — телефон или десктоп, экран приложения — пресет), контраст тёплых палитр.
  Честность: сток и хотлинк картинок; подписи и alt против списка ассетов; числа против фактов и текстов — число
  совпадает с фактом значением, единицей и объектом, а строка факта без источника число не легализует; текст против
  copy deck; «рыба»; отзывы без источника.
  Картинка и список ассетов. Картинка с именем файла ищется в списке по имени. Загрузка холста `/_blob/<id>` — по
  реестру загрузок: колонка «id загрузки» списка, затем таблица «Загрузки» ARTIFACTS.md продукта (--uploads; без
  ключа — ARTIFACTS.md в папках выше списка ассетов) — её файл или слот есть в списке. Файл общих ассетов продукта
  (`design/_assets/`: знак, иконки) в список страницы не входит и находкой не считается. Находка — загрузка вне
  реестра и загрузка, чьих файла и слота в списке нет; без реестра сверка не идёт — одна находка на прогон.
  Формы — по `kb/site/05-conversion-funnels/lead-forms.yaml`: запреты раздела `forbidden`, которые видны в DOM, у любой
  формы; с --forms — поля и видимые подписи против набора формы плана.
  Приёмка: навигация, тело 16 px и вылет на телефоне, строки H1, наложение текста, слепая зона разметки (canvas и видео).
  Тело 16 px считается по абзацам внутри `main` (без `main` — вне шапки, подвала и навигации): строка реквизитов
  подвала — не основной текст.
  Навигация на телефоне — major, как пункт D2 приёмки (S): страница без меню по плану (посадочная, одноэкранная) —
  законна, такую находку отбрасывают с причиной.
Входы. Факты — facts.md входа холста (таблица «Факты»: id · дословно · источник · где можно) или facts.yaml продукта;
тексты — copy.md входа (строки слотов страницы или таблица «ключ · роль · текст …» кабинета; `{имя}` в тексте —
подстановка, её значение любое) или copy deck (YAML: выбранные варианты страницы --page); демо-набор кабинета —
demo-data.json входа (--demo): тексты и числа записей, даты и телефоны, объёмы коллекций — не выдумка; ассеты —
assets.md входа (колонки «Файл», «Подпись», «Alt»; «Слот» и «id загрузки» — для загрузок холста) или YAML плана
ассетов и манифеста (записи с file или id слота и caption или alt); реестр загрузок — ARTIFACTS.md продукта, таблица
«Загрузки» (колонки id, файл, слот); формы —
id наборов lead-forms.yaml или YAML плана страницы (`form.ref: lead-forms.yaml#<id>`). Токены ДС (--tokens) — первый
брейкпоинт, гарнитуры и цвета: антиква в заголовках и тёплый фон, которые называет ДС, — решение, а не примета.
`--allow` снимает примету, если бриф или арт-дирекция записали решение; ключи — `allow` реестра примет.
Приватность: статический обход только внутри указанной папки; `/`, домашняя папка и её служебные подпапки отклоняются.
Для локальных целей внешние запросы по умолчанию блокируются (детерминизм, ничего не уходит в сеть).
"""
import argparse, colorsys, json, math, os, re, statistics, sys, time, unicodedata
from datetime import datetime, timezone
from functools import lru_cache
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import kbpaths  # noqa: E402

VERSION = '2.0'

# ---------------------------------------------------------------- данные владельцев (числа и id — не в коде)
TELLS_FILE = kbpaths.kb(None, 'common', 'tells.yaml')                 # проверки → id приметы, группа, ключ --allow
WIDTHS_FILE = kbpaths.kb(None, 'common', 'acceptance-widths.yaml')    # ширины приёмки
UI_THRESHOLDS = kbpaths.data('ui', 'thresholds.yaml')                 # кегли и высота шапки
REF_TOKENS = kbpaths.kb('ui', '14-recipes', 'examples', 'tokens.css')  # первый брейкпоинт без токенов ДС
AIL_FILE = kbpaths.kb('site', '09-ai-generation-evaluation', 'ai-landing-markers.yaml')
LEAD_FORMS = kbpaths.kb('site', '05-conversion-funnels', 'lead-forms.yaml')
COPY_CHECKLIST = kbpaths.kb('text', '09-ai-generation-evaluation', 'copy-checklist.yaml')
ANALYZERS = kbpaths.kb('text', '06-anti-slop', 'lexicon', 'analyzers.yaml')
CLICHE = kbpaths.kb('creative', '08-uniqueness-anti-slop', 'cliche-registry.yaml')
UI_ANTISLOP = kbpaths.kb('ui', '11-styles-trends', '04-anti-slop-ui.md')   # §1.3: диагноз по числу маркеров и хрома
# Высота окна — параметр прогона, а не норма приёмки: широкие окна 900, окна уже первого брейкпоинта 844 (окна первого
# экрана site 1440×900 и 390×844).
VIEW_H_WIDE, VIEW_H_NARROW = 900, 844
INPUT_MANIFEST = 'INPUT.md'                                           # манифест входа холста (project/canvas_input.py)
FIXTURE_PARTS = kbpaths.scripts('claude-design', 'fixtures', 'artboard-parts')   # копия артборда в двух частях


def _yaml(path):
    import yaml
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=None)
def registry():
    """Реестр примет: checks {id проверки: {group, tell, allow, norm}}, tells {id: запись}, domains, clusters."""
    d = _yaml(TELLS_FILE)
    return {'checks': {k: v for k, v in (d.get('checks') or {}).items() if isinstance(v, dict)},
            'tells': {t['id']: t for t in d.get('tells') or [] if isinstance(t, dict) and t.get('id')},
            'domains': d.get('domains') or {}, 'clusters': d.get('clusters') or []}


def allow_keys():
    """Ключи --allow проверок этой утилиты (без префикса `<утилита>:` у ключа строки реестра)."""
    return {v['allow'] for k, v in registry()['checks'].items() if ':' not in k and v.get('allow')}


@lru_cache(maxsize=None)
def acceptance_widths():
    d = _yaml(WIDTHS_FILE)
    return {'widths': [int(w) for w in d.get('widths') or []], 'artboards': [int(w) for w in d.get('artboards') or []],
            'overflow_only': int(d['overflow_only']) if d.get('overflow_only') else None}


@lru_cache(maxsize=None)
def ui_thresholds():
    return _yaml(UI_THRESHOLDS)


def first_breakpoint(tokens=None):
    """Первый брейкпоинт ДС (--tokens), иначе эталонный ui (`--bp-*` эталонных токенов)."""
    if tokens:
        kbpaths.use('claude-design')
        import literal_tokens
        bps = literal_tokens.load_tokens([tokens]).breakpoints
        if bps:
            return min(bps)
    with open(REF_TOKENS, encoding='utf-8') as f:
        return min(float(v) for v in re.findall(r'--bp-[a-z-]+:\s*(\d+(?:\.\d+)?)px', f.read()))


def ds_look(tokens):
    """Гарнитуры и цвета токенов ДС (--tokens) → {'families': {первая гарнитура}, 'colors': [(r, g, b)]}; без токенов —
    None. Облик, который называет ДС, — решение, а не примета."""
    if not tokens:
        return None
    kbpaths.use('claude-design')
    import literal_tokens
    ts = literal_tokens.load_tokens([tokens])
    return {'families': set(ts.families),
            'colors': [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in ts.colors if len(c) == 7]}


def ds_color(rgb, ds):
    """Цвет отрисовки — значение токена ДС (допуск 2 на канал — округление перевода цвета в sRGB)."""
    return bool(ds) and any(max(abs(a - b) for a, b in zip(rgb[:3], c)) <= 2 for c in ds['colors'])


def header_limit(surface, preset, vw, first_bp):
    """Порог высоты шапки поверхности: страница сайта — телефон (окно уже первого брейкпоинта) или десктоп, экран
    приложения — пресет (A, B, C, D)."""
    hh = ui_thresholds()['header_height']
    if surface == 'app':
        return hh['app'][preset]
    return hh['page']['phone' if vw < first_bp else 'desktop']


def num_in(text, pattern):
    m = re.search(pattern, str(text or ''))
    return float(m.group(1).replace(',', '.')) if m else None


@lru_cache(maxsize=None)
def ail(marker_id):
    d = _yaml(AIL_FILE)
    return next((m for m in d.get('markers') or [] if isinstance(m, dict) and m.get('id') == marker_id), {})


def hero_height_share():
    """Порог высоты hero без продолжения — AIL-06 site («hero ≥ 95 % высоты окна»)."""
    v = num_in(ail('AIL-06').get('threshold'), r'hero\s*≥\s*(\d+(?:[.,]\d+)?)\s*%')
    return v / 100.0 if v else None


def cards_cv_max():
    """Вариация длины текстов карточек ниже порога — примета AIL-07 site («CV длины текстов карточек < 0,2»)."""
    return num_in(ail('AIL-07').get('threshold'), r'CV длины текстов карточек\s*<\s*(\d+(?:[.,]\d+)?)')


@lru_cache(maxsize=None)
def eyebrow_per_sections():
    """Надзаголовок — не чаще одного на N секций с заголовком (H1, H2): число владельца COPY-C-18 (text) — поле
    per_sections анализатора an-eyebrow-rate или формулировка pass_when пункта COPY-C-18."""
    for a in (_yaml(ANALYZERS).get('rules') or []):
        if isinstance(a, dict) and a.get('id') == 'an-eyebrow-rate' and a.get('per_sections'):
            return int(a['per_sections'])
    for item in (_yaml(COPY_CHECKLIST).get('items') or []):
        if isinstance(item, dict) and item.get('id') == 'COPY-C-18':
            n = num_in(item.get('pass_when'), r'не чаще 1 на (\d+) секци')
            return int(n) if n else None
    return None


@lru_cache(maxsize=None)
def cliche_entry(cid):
    return next((e for e in _yaml(CLICHE).get('entries') or [] if isinstance(e, dict) and e.get('id') == cid), {})


def bento_min_tiles():
    """Бенто — от N однотипных плиток с одним радиусом (порог записи реестра клише bento-uniform-tiles)."""
    v = num_in(cliche_entry('bento-uniform-tiles').get('threshold'), r'≥\s*(\d+)\s*однотипн')
    return int(v) if v else None


def orbit_min_icons():
    """Орбита — от N иконок на окружностях (метрика записи реестра клише logo-orbit-hero)."""
    v = num_in(((cliche_entry('logo-orbit-hero').get('signals') or {}).get('metric')), r'≥\s*(\d+)\s*икон')
    return int(v) if v else None


NUM_WORDS = {'два': 2, 'две': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6}


def _count(word):
    w = str(word or '').strip('*').lower()
    return int(w) if w.isdigit() else NUM_WORDS.get(w)


@lru_cache(maxsize=None)
def ui_diagnosis():
    """Диагноз ui 11/04 §1.3: markers — с какого числа маркеров на экране интерфейс «усреднён», chrome — с какого
    числа приёмов шаблонного хрома; числа нет у владельца — None."""
    try:
        text = open(UI_ANTISLOP, encoding='utf-8').read()
    except OSError:
        return {'markers': None, 'chrome': None}
    sec = re.search(r'^###\s*1\.3\..*?(?=^###\s)', text, re.S | re.M)
    body = sec.group(0) if sec else ''
    m = re.search(r'\|\s*\*\*(\S+)\s+и\s+больше\*\*\s*\|', body)
    c = re.search(r'\((\S+)\s+и\s+больше\s+«хрома»\)', body)
    return {'markers': _count(m.group(1)) if m else None, 'chrome': _count(c.group(1)) if c else None}


@lru_cache(maxsize=None)
def cliche_cluster_min():
    """Кластер реестра клише creative на одной сцене — от N записей одного кластера (`cluster_rule`)."""
    m = re.search(r'(\S+)\s+и\s+больше\s+записей\s+одного\s+кластера', str(_yaml(CLICHE).get('cluster_rule') or ''))
    return _count(m.group(1)) if m else None


@lru_cache(maxsize=None)
def lead_forms():
    d = _yaml(LEAD_FORMS)
    return {'sets': {f['id']: f for f in d.get('form_sets') or [] if isinstance(f, dict) and f.get('id')},
            'fields': d.get('fields') or {}, 'defaults': d.get('defaults') or {},
            'forbidden': {f['id']: f for f in d.get('forbidden') or [] if isinstance(f, dict) and f.get('id')}}


# ---------------------------------------------------------------- справочники
SERIF_FAMILIES = {  # display-антиквы, частые у сгенерированных лендингов 2025–2026 (замеры cd 06/05, impeccable, taste)
    'fraunces', 'instrument serif', 'playfair display', 'playfair', 'cormorant', 'cormorant garamond', 'dm serif display',
    'dm serif text', 'newsreader', 'eb garamond', 'garamond', 'libre caslon', 'libre caslon display', 'libre baskerville',
    'lora', 'merriweather', 'crimson pro', 'crimson text', 'source serif', 'source serif 4', 'source serif pro', 'pt serif',
    'noto serif', 'georgia', 'times new roman', 'times', 'bodoni moda', 'bodoni', 'didot', 'spectral', 'literata',
    'young serif', 'gloock', 'bitter', 'roboto serif', 'ibm plex serif', 'tinos', 'liberation serif', 'dejavu serif',
    'gelasio', 'petrona', 'besley', 'rufina', 'marcellus', 'cinzel', 'prata', 'yeseva one', 'abril fatface', 'alice',
    'lusitana', 'sorts mill goudy', 'goudy', 'baskerville', 'caslon', 'canela', 'tiempos', 'gt sectra', 'editorial new',
    'pp editorial new', 'ogg', 'recoleta', 'zodiak', 'erode', 'sentient', 'gambetta', 'boska', 'amiri', 'playfair display sc',
}
SANS_DEFAULTS = {'inter', 'geist', 'roboto', 'sora', 'space grotesk', 'plus jakarta sans', 'manrope', 'dm sans', 'poppins',
                 'outfit', 'urbanist', 'montserrat', 'open sans', 'helvetica', 'arial', 'system-ui', '-apple-system',
                 'segoe ui', 'lato', 'nunito', 'work sans'}
MONO_FAMILIES = {'jetbrains mono', 'ibm plex mono', 'geist mono', 'space mono', 'dm mono', 'fira code', 'fira mono',
                 'roboto mono', 'source code pro', 'ubuntu mono', 'courier new', 'courier', 'menlo', 'monaco', 'consolas',
                 'sf mono', 'dejavu sans mono', 'liberation mono', 'monospace', 'ui-monospace', 'berkeley mono',
                 'commit mono', 'martian mono', 'azeret mono', 'overpass mono', 'red hat mono'}
STOCK_PATTERNS = [  # (id, regex) — хотлинк стоковых фото и сервисов-заглушек; ID фото модель берёт «по памяти»
    ('unsplash', r'(?:images|plus)\.unsplash\.com/(?:photo|premium_photo)-[0-9]+-[0-9a-f]{6,}|source\.unsplash\.com/[^\s"\')]+'
                 r'|unsplash\.com/photos/[\w-]+|unsplash\.it/[^\s"\')]+'),
    ('pexels', r'images\.pexels\.com/photos/\d+|pexels\.com/photo/[\w-]+'),
    ('pixabay', r'cdn\.pixabay\.com/[^\s"\')]+|pixabay\.com/get/[^\s"\')]+'),
    ('picsum', r'picsum\.photos/[^\s"\')]*'),
    ('placeholder', r'(?:via\.)?placeholder\.com/[^\s"\')]*|placehold\.(?:co|it)/[^\s"\')]*|dummyimage\.com/[^\s"\')]*'
                    r'|fakeimg\.pl/[^\s"\')]*|placekitten\.com/[^\s"\')]*|loremflickr\.com/[^\s"\')]*|lorempixel\.com/[^\s"\')]*'),
    ('avatar-service', r'i\.pravatar\.cc/[^\s"\')]*|pravatar\.cc/[^\s"\')]*|randomuser\.me/api/portraits/[^\s"\')]+'
                       r'|ui-avatars\.com/api[^\s"\')]*|api\.dicebear\.com/[^\s"\')]+|thispersondoesnotexist\.com'),
    ('stock-site', r'(?:media\.)?istockphoto\.com/[^\s"\')]+|(?:image\.)?shutterstock\.com/[^\s"\')]+'
                   r'|media\.gettyimages\.com/[^\s"\')]+|(?:img\.|image\.)?freepik\.com/[^\s"\')]+|stock\.adobe\.com/[^\s"\')]+'
                   r'|burst\.shopifycdn\.com/[^\s"\')]+|cdn\.stocksnap\.io/[^\s"\')]+'),
]
FILLER_PATTERNS = [r'\blorem ipsum\b', r'\bdolor sit amet\b', r'\bFeature [1-9]\b', r'\bJohn Doe\b', r'\bJane Doe\b',
                   r'\bexample@(?:example|email|mail)\.com\b', r'\bAcme (?:Inc|Corp)\b', r'\bYour Company\b', r'\bCompany Name\b',
                   r'\bTrusted by\b', r'\bComing soon\b', r'\bTODO\b', r'Название компании', r'Текст-заглушка', r'Иван Иванов',
                   r'\$1,234\.56', r'\b123 Main St']
TEXT_EXT = ('.html', '.htm', '.css', '.scss', '.sass', '.less', '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.vue',
            '.svelte', '.astro', '.md', '.mdx', '.json', '.txt')
SKIP_DIRS = {'node_modules', '.git', '.next', '.nuxt', '.svelte-kit', '.venv', 'venv', '__pycache__', '.cache',
             'screenshots', '.turbo', 'coverage'}
SEV_ORDER = {'critical': 0, 'major': 1, 'minor': 2, 'info': 3}


# ---------------------------------------------------------------- цвет: sRGB → OKLab/OKLCH, контраст WCAG 2
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def oklch(rgb):
    r, g, b = (_lin(x) for x in rgb[:3])
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    C = math.hypot(A, B)
    H = math.degrees(math.atan2(B, A)) % 360
    return round(L, 4), round(C, 4), round(H, 1)


def hexs(rgb):
    return '#%02x%02x%02x' % tuple(int(round(x)) for x in rgb[:3])


def luminance(rgb):
    r, g, b = (_lin(x) for x in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    """WCAG 2 contrast; fg может быть RGBA — альфа компонуется поверх bg (ui 13: контраст после композитинга)."""
    if len(fg) > 3 and fg[3] < 1:
        a = fg[3]
        fg = [fg[i] * a + bg[i] * (1 - a) for i in range(3)]
    l1, l2 = luminance(fg), luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def warm_class(rgb):
    """'light' (крем, беж, тёплый off-white), 'dark' (коричнево-чёрный) или None. Пороги — метрика записи warm-paper
    реестра клише creative (OKLCH h 45–115°, C 0,006–0,08, L ≥ 0,88 или ≤ 0,30); насыщенный брендовый цвет (C > 0,08) —
    не «тонировка»."""
    L, C, H = oklch(rgb)
    if not (45 <= H <= 115 and 0.006 <= C <= 0.08):
        return None
    if L >= 0.88:
        return 'light'
    if L <= 0.30:
        return 'dark'
    return None


def warm_hue_text(rgb):
    """Тёплый «латунный/терракотовый» цвет текста или акцента: h 25–95°, C ≥ 0.05."""
    L, C, H = oklch(rgb)
    return 25 <= H <= 95 and C >= 0.05


# ---------------------------------------------------------------- текст и числа
QUOTES = str.maketrans({'«': '"', '»': '"', '“': '"', '”': '"', '„': '"', '’': "'", '‘': "'", '—': '-', '–': '-',
                        '‑': '-', ' ': ' ', ' ': ' ', ' ': ' ', ' ': ' '})


def norm_text(s):
    s = unicodedata.normalize('NFKC', s or '').translate(QUOTES).lower()
    s = re.sub(r'[*_`#>|]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


NUM_RX = re.compile(r'(?<![\w.,])([$€£₽]?\s?\d[\d\s   ]*(?:[.,]\d+)?)(\s?(?:%|\+|k\b|K\b|M\b|млн|тыс|млрд|x\b|×|₽|\$|€|£))?')


def extract_numbers(text):
    """[(исходная строка, нормализованное значение)] — '12 000+' → '12000', '4,9' → '4.9', '98 %' → '98'."""
    out = []
    for m in NUM_RX.finditer(text or ''):
        raw = (m.group(1) + (m.group(2) or '')).strip()
        core = re.sub(r'[$€£₽\s   ]', '', m.group(1))
        if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', core) and not re.fullmatch(r'\d+[.,]\d{1,2}', core):
            core = re.sub(r'[.,]', '', core)          # 12.000 / 12,000 → 12000
        core = core.replace(',', '.')
        try:
            val = float(core)
        except ValueError:
            continue
        v = ('%f' % val).rstrip('0').rstrip('.')
        out.append((raw, v))
    return out


def md_plain(text):
    text = re.sub(r'\{#.*?#\}', ' ', text, flags=re.S)           # комментарии шаблонов {# … #}
    text = re.sub(r'^\s*\|?\s*-{3,}.*$', ' ', text, flags=re.M)   # разделители таблиц
    return text


# Число как утверждение: значение, единица и объект («1 146 квартир», «гарантия 3 года», «4,8 из 5»). Число на странице
# легально, только если факт (или текст copy deck) говорит то же значение с той же единицей о том же объекте.
UNITS = [(r'%|процент\w*', '%'), (r'₽|руб\w*|р\.', '₽'), (r'\$|долл\w*', '$'), (r'€|евро', '€'), (r'£', '£'),
         (r'×|x|раз(?:а)?', '×'), (r'лет|год\w*|г\.', 'год'), (r'мес\w*', 'мес'), (r'недел\w*|нед\.', 'нед'),
         (r'дн\w*|день|сут\w*', 'день'), (r'час\w*|ч\.?', 'ч'), (r'мин\w*', 'мин'), (r'сек\w*', 'с'),
         (r'м²|м2|кв\.\s?м', 'м²'), (r'км', 'км'), (r'см', 'см'), (r'мм', 'мм'), (r'кг', 'кг'), (r'м', 'м'),
         (r'шт\w*', 'шт')]
UNIT_RX = re.compile(r'\s?(' + '|'.join(u for u, _ in UNITS) + r')(?![\wА-Яа-яЁё])', re.I)
MULT = {'k': 1e3, 'тыс': 1e3, 'm': 1e6, 'млн': 1e6, 'млрд': 1e9}
STOP = {'и', 'в', 'во', 'на', 'за', 'до', 'от', 'по', 'с', 'со', 'к', 'о', 'об', 'из', 'у', 'не', 'а', 'но', 'под', 'над',
        'при', 'около', 'более', 'менее', 'чем', 'для', 'же', 'уже', 'всего', 'лишь', 'the', 'of', 'and', 'for', 'in', 'to',
        'on', 'at', 'by', 'with', 'from', 'over', 'than', 'up', 'our', 'your', 'наших', 'наш', 'наша', 'ваш', 'ваших'}
PHONE_RX = re.compile(r'(?:\+7|8)[\s(-]*\d{3}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}')
DATE_RX = re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b')
TIME_RX = re.compile(r'\b\d{1,2}:\d{2}\b')
WORD_RX = re.compile(r'[A-Za-zА-Яа-яЁё]{3,}')


def _stem(w):
    return w.lower().replace('ё', 'е')[:5]


def number_claims(text):
    """Утверждения с числами: [{raw, value, unit, objs}] — телефон и дата целиком, число с единицей и словами рядом
    (первое значимое слово после числа и последнее до него в той же части фразы). Время «10:00» — не утверждение."""
    text = str(text or '')
    out = []
    for m in PHONE_RX.finditer(text):
        out.append({'raw': m.group(0), 'value': 'tel:' + re.sub(r'\D', '', m.group(0))[-10:], 'unit': 'tel', 'objs': set()})
    for m in DATE_RX.finditer(text):
        d, mo, y = m.group(0).split('.')
        out.append({'raw': m.group(0), 'value': f"date:{int(d):02d}.{int(mo):02d}.{y[-2:]}", 'unit': 'date', 'objs': set()})
    rest = TIME_RX.sub(' ', DATE_RX.sub(' ', PHONE_RX.sub(' ', text)))
    for m in NUM_RX.finditer(rest):
        raw = (m.group(1) + (m.group(2) or '')).strip()
        core = re.sub(r'[$€£₽\s\u00a0\u202f\u2009]', '', m.group(1))
        if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', core) and not re.fullmatch(r'\d+[.,]\d{1,2}', core):
            core = re.sub(r'[.,]', '', core)
        try:
            val = float(core.replace(',', '.'))
        except ValueError:
            continue
        suf = (m.group(2) or '').strip().lower()
        unit = None
        if suf in MULT:
            val *= MULT[suf]
        elif suf in ('%', '₽', '$', '€', '£', '×', 'x'):
            unit = '×' if suf in ('x', '×') else suf
        cur = re.match(r'\s*[$€£₽]', m.group(1))
        if cur:
            unit = cur.group(0).strip()
        tail = rest[m.end():m.end() + 40]
        if unit is None:
            um = UNIT_RX.match(tail)
            if um:
                unit = next(n for u, n in UNITS if re.fullmatch(u, um.group(1), re.I))
                tail = tail[um.end():]
        clause_after = re.split(r'[.;:!?()«»"—–]|\d', tail)[0]
        clause_before = re.split(r'[.;:!?()«»"—–]|\d', rest[max(0, m.start() - 40):m.start()][::-1])[0][::-1]
        after = next((w for w in WORD_RX.findall(clause_after) if w.lower() not in STOP), None)
        before = next((w for w in reversed(WORD_RX.findall(clause_before)) if w.lower() not in STOP), None)
        v = ('%f' % val).rstrip('0').rstrip('.')
        out.append({'raw': raw, 'value': v, 'unit': unit, 'objs': {_stem(w) for w in (after, before) if w}})
    return out


def claim_known(c, known):
    """Число страницы совпадает с утверждением фактов или текстов: значение, единица и хотя бы одно общее слово-объект
    (если объект есть у обоих)."""
    for k in known:
        if k['value'] != c['value'] or k['unit'] != c['unit']:
            continue
        if not c['objs'] or not k['objs'] or c['objs'] & k['objs']:
            return True
    return False


SUBST_RX = re.compile(r'\{[^{}]{1,40}\}')
LETTERS_RX = re.compile(r'[a-zа-яё]+')


def copy_matcher(copy_text, demo=None):
    """Текст блока → из copy deck ли он: дословно внутри текстов (кавычки, тире и пробелы нормализуются); строка с
    подстановкой `{имя}` — шаблон, значение подстановки любое. С демо-набором — ещё тексты его записей, а блок, собранный
    из полей записи (строка таблицы, карточка), проходит, если каждое его слово есть в текстах copy deck и демо-набора
    (блок без слов — число, дата, телефон — сверяет HON-NUMBERS)."""
    pool = copy_text + ('\n' + '\n'.join(demo['texts']) if demo else '')
    cn = norm_text(pool)
    tmpl = []
    for line in pool.splitlines():
        if SUBST_RX.search(line):
            parts = SUBST_RX.split(norm_text(line))
            if LETTERS_RX.search(''.join(parts)):
                tmpl.append(re.compile('.+?'.join(re.escape(p) for p in parts)))
    vocab = set(LETTERS_RX.findall(cn)) if demo else None

    def known(text):
        t = norm_text(text)
        if t in cn or any(rx.fullmatch(t) for rx in tmpl):
            return True
        return vocab is not None and all(w in vocab for w in LETTERS_RX.findall(t))
    return known


def _cells(line):
    return [x.strip() for x in line.strip().strip('|').split('|')]


def load_facts(path):
    """Факты для сверки чисел → {'known': [утверждения], 'rows': n, 'no_source': [id]}. facts.md входа холста: таблица
    раздела «Факты» (id · дословно · источник · где можно; колонка «Факт…» или «Текст на странице» — тоже текст факта);
    строки раздела «Нет» и строки без источника число не легализуют. facts.yaml продукта: verbatim и canonical каждого
    факта с источником (source: who или where)."""
    if not path:
        return None
    try:
        raw = open(path, encoding='utf-8').read()
    except OSError as e:
        raise SystemExit(f'не читается {path}: {e}')
    known, rows, nosrc = [], 0, []
    if path.lower().endswith(('.yaml', '.yml', '.json')):
        import yaml
        d = yaml.safe_load(raw) or {}
        for f in d.get('facts') or []:
            if not isinstance(f, dict):
                continue
            rows += 1
            src = f.get('source') or {}
            if not (isinstance(src, dict) and (src.get('who') or src.get('where') or src.get('url'))):
                nosrc.append(str(f.get('id')))
                continue
            for t in list(f.get('verbatim') or []) + [f.get('canonical') or '']:
                known += number_claims(t)
        return {'known': known, 'rows': rows, 'no_source': nosrc}
    section, header = '', None
    for line in re.sub(r'\{#.*?#\}', ' ', raw, flags=re.S).splitlines():
        st = line.strip()
        if re.fullmatch(r'\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-*:?\s*\|?', st):
            continue                                       # разделитель шапки таблицы
        if st.startswith('#'):
            section, header = st.lstrip('#').strip().lower(), None
            continue
        if not st.startswith('|'):
            header = None
            continue
        cells = _cells(st)
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if section and not section.startswith('факт') and not section.startswith('fact'):
            continue
        rec = dict(zip(header, cells))
        text_cols = [h for h in header if h in ('дословно', 'verbatim') or h.startswith(('факт', 'fact'))
                     or 'текст на странице' in h or 'text on the page' in h]
        if not text_cols:
            continue
        fid = rec.get('id') or rec.get(text_cols[0], '')[:30]
        if fid in ('—', '-', ''):
            continue
        rows += 1
        src = next((rec[h] for h in header if h.startswith(('источник', 'source'))), None)
        if not src or src.strip() in ('—', '-'):
            nosrc.append(fid)
            continue
        for h in text_cols:
            known += number_claims(rec.get(h, ''))
    return {'known': known, 'rows': rows, 'no_source': nosrc}


def load_copy(path, page=None):
    """Тексты copy deck: copy.md входа (строки слотов страницы; у кабинета — таблица «ключ · роль · текст …», колонка
    «текст») или copy deck YAML/JSON (выбранные варианты страницы --page; без --page — все страницы)."""
    if not path:
        return None
    try:
        raw = open(path, encoding='utf-8').read()
    except OSError as e:
        raise SystemExit(f'не читается {path}: {e}')
    if not path.lower().endswith(('.yaml', '.yml', '.json')):
        out, header = [], None
        for line in raw.splitlines():
            st = line.strip()
            if st.startswith('|'):
                cells = _cells(st)
                if header is None:
                    header = [c.lower() for c in cells]             # первая строка таблицы — шапка
                elif not all(re.fullmatch(r':?-{3,}:?', c) for c in cells if c):
                    col = next((i for i, h in enumerate(header) if h in ('текст', 'text')), None)
                    if col is not None and col < len(cells) and cells[col]:
                        out.append(cells[col])
                continue
            header = None
            m = re.match(r'^\[[^\]]*\](?:\s+[a-z]+)?:\s?(.*)$', st)
            if m:
                out.append(m.group(1))
            elif line.startswith('  ') and out:
                out[-1] += '\n' + st
        return '\n'.join(out) if out else md_plain(raw)
    import yaml
    d = yaml.safe_load(raw) or {}
    deck = d.get('copy_deck') if isinstance(d.get('copy_deck'), dict) else d
    out = []
    for pg in deck.get('pages') or []:
        if page and str(pg.get('page_id')) != str(page):
            continue
        for sec in pg.get('sections') or []:
            for sl in sec.get('slots') or []:
                vs = [v for v in sl.get('variants') or [] if isinstance(v, dict)]
                ch = next((v for v in vs if str(v.get('id')) == str(sl.get('chosen'))), vs[0] if len(vs) == 1 else None)
                if ch and ch.get('text'):
                    out.append(str(ch['text']))
    return '\n'.join(out)


ISO_DATE_RX = re.compile(r'^(\d{4})-(\d{2})-(\d{2})(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$')


def _num_value(x):
    return ('%f' % float(x)).rstrip('0').rstrip('.')


def load_demo(path):
    """Демо-набор кабинета (demo-data.json входа холста) → {'texts': [строки], 'values': {значения}}: макет кабинета
    рисует записи демо-набора, и их тексты и числа — не выдумка. Тексты — строки записей, названия статусов объектов,
    строки локализации; значения — числа записей (без единицы: единицу и формат задаёт вёрстка), числа внутри строк,
    телефоны, даты ISO (дата целиком, день, месяц, год), объёмы коллекций и размеры наборов."""
    if not path:
        return None
    try:
        d = json.load(open(path, encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f'не читается демо-набор {path}: {e}')
    texts, values = [], set()

    def scalar(v):
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float)):
            values.add(_num_value(v))
        elif isinstance(v, str) and v.strip():
            s = v.strip()
            m = ISO_DATE_RX.match(s)
            if m:
                y, mo, dd = m.groups()
                values.update({f'date:{dd}.{mo}.{y[-2:]}', str(int(dd)), str(int(mo)), y})
                return
            texts.append(s)
            values.update(c['value'] for c in number_claims(s))
        elif isinstance(v, list):
            for x in v:
                scalar(x)
        elif isinstance(v, dict):
            for k, x in v.items():
                if not str(k).startswith('_') and k != 'example':
                    scalar(x)

    for obj in (d.get('objects') or {}).values():
        if not isinstance(obj, dict):
            continue
        for rec in obj.get('records') or []:
            scalar(rec)
        texts += [str(s['name']) for s in obj.get('statuses') or [] if isinstance(s, dict) and s.get('name')]
    for col in (d.get('collections') or {}).values():
        if not isinstance(col, dict):
            continue
        scalar(list((col.get('volume') or {}).values()))
        scalar([s.get('count') for s in (col.get('sets') or {}).values() if isinstance(s, dict)])
    texts += [str(x['text']) for x in d.get('localization') or [] if isinstance(x, dict) and x.get('text')]
    return {'texts': texts, 'values': values}


def _md_rows(text, is_header):
    """Строки таблиц markdown, чья шапка проходит is_header(ячейки шапки в нижнем регистре) → [{колонка: ячейка}]."""
    out, header = [], None
    for line in text.splitlines():
        st = line.strip()
        if not st.startswith('|'):
            header = None if not st else header
            continue
        cells = _cells(st)
        if all(re.fullmatch(r':?-{3,}:?', c) for c in cells if c):
            continue
        low = [c.lower() for c in cells]
        if is_header(low):
            header = low
            continue
        if header:
            out.append(dict(zip(header, cells)))
    return out


def _code(cell):
    """Значение ячейки формы: текст первых обратных кавычек, без них — ячейка целиком; прочерк — пусто."""
    cell = str(cell or '').strip()
    m = re.search(r'`([^`]+)`', cell)
    val = (m.group(1) if m else cell).strip()
    return '' if val in ('—', '–', '-') else val


def _file_stem(path):
    return os.path.splitext(os.path.basename(path))[0].lower()


def asset_index(rows):
    """Строки списка ассетов [{file, slot, caption, alt, uploads}] → поиск строки по имени файла без расширения, id
    слота и id загрузки. Строка пустого слота (заглушка placeholder без файла) находится по слоту и по имени
    «placeholder»: так картинка-заглушка страницы остаётся картинкой из списка."""
    idx = {'rows': rows, 'by_stem': {}, 'by_slot': {}, 'by_upload': {}}
    for r in rows:
        if r['file']:
            idx['by_stem'].setdefault(_file_stem(r['file']), r)
        elif r.get('placeholder'):
            idx['by_stem'].setdefault('placeholder', r)
        if r['slot']:
            idx['by_slot'].setdefault(r['slot'], r)
        for u in r['uploads']:
            idx['by_upload'].setdefault(u, r)
    return idx


def parse_assets_readme(path):
    """Список ассетов → индекс asset_index: assets.md входа холста (колонки «Файл», «Подпись», «Alt»; «Слот» и «id
    загрузки» — если есть) или YAML плана ассетов и манифеста (записи с file или id слота и caption или alt на любой
    глубине). Прочерк в ячейке — пусто: сверять не с чем; alt декоративной картинки `alt=""` — тоже."""
    if not path:
        return None
    text = open(path, encoding='utf-8').read()
    rows = []

    def row(f, slot, cap, alt, uploads=(), placeholder=False):
        rows.append({'file': f, 'slot': slot, 'caption': cap, 'alt': alt, 'uploads': list(uploads),
                     'placeholder': placeholder})

    if path.lower().endswith(('.yaml', '.yml', '.json')):
        import yaml

        def walk(x):
            if isinstance(x, dict):
                f = x.get('file') or x.get('path') or x.get('src')
                f = f if isinstance(f, str) else ''
                # id слота: у плана ассетов — `id` (там `slot` — тип слота блока), у манифеста — `slot`
                slot = next((x[k] for k in ('id', 'slot') if isinstance(x.get(k), str)), '')
                if (f or slot) and (x.get('caption') is not None or x.get('alt') is not None):
                    row(f, slot, str(x.get('caption') or '').strip('"« »'), str(x.get('alt') or '').strip('"« »'))
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(yaml.safe_load(text))
        return asset_index(rows)
    for rec in _md_rows(text, lambda low: any(h.startswith(('file', 'файл')) for h in low)
                        and any(('caption' in h or 'подпис' in h) for h in low)):
        col = lambda test: next((rec[h] for h in rec if test(h)), '')   # noqa: E731
        f_cell = col(lambda h: h.startswith(('file', 'файл')))
        placeholder = '`' not in f_cell and f_cell.strip().lower().startswith('placeholder')
        f = '' if placeholder else _code(f_cell)
        slot = _code(col(lambda h: h.startswith(('slot', 'слот')))).split(' ')[0]
        cap = _code(col(lambda h: 'caption' in h or 'подпис' in h)).strip('"« »')
        alt = _code(col(lambda h: h.startswith('alt'))).strip('"« »')
        ups = re.findall(r'[0-9A-Za-z_-]{6,}', col(lambda h: 'id загрузки' in h or 'upload' in h))
        if f or slot or placeholder:
            row(f, slot, cap, '' if alt == 'alt=' else alt, ups, placeholder)
    return asset_index(rows)


def load_uploads(path):
    """Реестр загрузок холста — таблица «Загрузки» ARTIFACTS.md продукта (колонки id, файл, слот, артефакт; другие
    колонки не мешают) → {id: {file, slot, artifact}}. Загрузка живёт в claude.ai, на артборде она — `/_blob/<id>`."""
    if not path:
        return None
    try:
        text = open(path, encoding='utf-8').read()
    except OSError as e:
        raise SystemExit(f'не читается реестр загрузок {path}: {e}')
    reg = {}
    for rec in _md_rows(text, lambda low: 'id' in low and any(h.startswith(('файл', 'file')) for h in low)):
        fid = _code(rec.get('id'))
        if fid:
            reg[fid] = {'file': _code(next((rec[h] for h in rec if h.startswith(('файл', 'file'))), '')),
                        'slot': _code(rec.get('слот') or rec.get('slot')).split(' ')[0],
                        'artifact': _code(rec.get('артефакт') or rec.get('artifact'))}
    return reg


def find_uploads(assets_path, depth=6):
    """ARTIFACTS.md продукта для списка ассетов: первая папка вверх от списка (не дальше depth уровней), где он лежит
    — у входа холста это `design/` продукта; нет — None."""
    d = os.path.dirname(os.path.abspath(assets_path))
    for _ in range(depth):
        p = os.path.join(d, 'ARTIFACTS.md')
        if os.path.isfile(p):
            return p
        if os.path.dirname(d) == d:
            break
        d = os.path.dirname(d)
    return None


def blob_id(src):
    """id загрузки холста в адресе картинки `/_blob/<id>`; другой адрес — None."""
    m = re.search(r'/_blob/([^/?#]+)', urlparse(src or '').path)
    return m.group(1) if m else None


def asset_for(img, assets, uploads):
    """Картинка страницы {file — имя без расширения, src, blob — id загрузки} → (строка списка ассетов или None,
    статус, запись реестра). Статусы: row — строка найдена; shared — файл общих ассетов продукта (`_assets/`), в
    список страницы не входит; off-list — загрузка есть в реестре, а её файла и слота в списке нет; unregistered —
    загрузки нет в реестре; no-registry — реестра нет вовсе (ни id в списке, ни таблицы «Загрузки»); missing — файла
    нет в списке."""
    blob = img['blob'] if 'blob' in img else blob_id(img.get('src'))
    if not blob:
        f = img['file']
        r = assets['by_stem'].get(f) or next((r for k, r in assets['by_stem'].items()
                                              if f.startswith(k) or k.startswith(f)), None)
        return (r, 'row', None) if r else (None, 'missing', None)
    r = assets['by_upload'].get(blob)
    if r:
        return r, 'row', None
    up = (uploads or {}).get(blob)
    if not up:
        return None, ('unregistered' if uploads is not None or assets['by_upload'] else 'no-registry'), None
    r = assets['by_stem'].get(_file_stem(up['file'])) or assets['by_slot'].get(up['slot'])
    if r:
        return r, 'row', up
    return None, ('shared' if re.search(r'(?:^|/)_assets/', up['file']) else 'off-list'), up


# медиа страницы, которое сверяется со списком ассетов наравне с <img>: (кто, кого)
MEDIA_RU = {'poster': ('постер видео', 'постера видео'), 'video': ('видео', 'видео'),
            'source': ('источник медиа', 'источника медиа'), 'background': ('фон', 'фоновой картинки')}


def load_form_sets(items):
    """--forms: id наборов lead-forms.yaml и YAML-файлы (план страницы, вход холста) со ссылками
    `lead-forms.yaml#<id>` → [id]."""
    out = []
    for it in items or []:
        for part in [x.strip() for x in str(it).split(',') if x.strip()]:
            if os.path.isfile(part):
                txt = open(part, encoding='utf-8').read()
                out += re.findall(r'lead-forms\.yaml#([a-z0-9]+(?:-[a-z0-9]+)*)', txt)
            else:
                out.append(part.split('#')[-1])
    sets = lead_forms()['sets']
    bad = [x for x in out if x not in sets]
    if bad:
        raise SystemExit(f'нет наборов форм в lead-forms.yaml: {sorted(set(bad))}; есть: {sorted(sets)}')
    return list(dict.fromkeys(out))


def family_first(ff):
    return (ff or '').split(',')[0].strip().strip('"\'').lower()


def family_kind(ff):
    """serif | sans | mono | unknown по объявленному стеку (намерение исполнителя важнее запасного шрифта)."""
    stack = [x.strip().strip('"\'').lower() for x in (ff or '').split(',') if x.strip()]
    if not stack:
        return 'unknown'
    first = stack[0]
    if first in MONO_FAMILIES or 'mono' in first:
        return 'mono'
    if first in SERIF_FAMILIES or re.search(r'\bserif\b', first) and 'sans' not in first:
        return 'serif'
    if first in SANS_DEFAULTS or 'sans' in first or 'grotesk' in first or 'grotesque' in first:
        return 'sans'
    generic = stack[-1]
    if generic == 'serif':
        return 'serif'
    if generic in ('sans-serif', 'system-ui'):
        return 'sans'
    if generic == 'monospace':
        return 'mono'
    return 'unknown'


# ---------------------------------------------------------------- статический обход исходников (без выхода за папку)
def safe_root(path):
    real = os.path.realpath(path)
    home = os.path.realpath(os.path.expanduser('~'))
    if real in ('/', home, os.path.dirname(home)):
        raise SystemExit(f'отказ: {real} — корень или домашняя папка; укажите папку проекта (--src)')
    for bad in ('.ssh', '.claude', '.config', '.gnupg', '.local'):
        if real == os.path.join(home, bad) or real.startswith(os.path.join(home, bad) + os.sep):
            raise SystemExit(f'отказ: {real} внутри ~/{bad}')
    return real


def scan_sources(root, max_bytes=20_000_000, max_files=5000):
    root = safe_root(root)
    hits, fonts, trans_all, files, total = [], {}, 0, 0, 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith('.')]
        for fn in fns:
            if not fn.lower().endswith(TEXT_EXT):
                continue
            p = os.path.join(dp, fn)
            try:
                size = os.path.getsize(p)
                if size > 3_000_000:
                    continue
                txt = open(p, encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            files += 1
            total += size
            rel = os.path.relpath(p, root)
            for kind, rx in STOCK_PATTERNS:
                for m in re.finditer(rx, txt, re.I):
                    hits.append({'kind': kind, 'url': m.group(0)[:160], 'file': rel,
                                 'line': txt.count('\n', 0, m.start()) + 1})
            for m in re.finditer(r'family=([A-Za-z0-9+ %]+?)(?::|&|"|\'|\))', txt):
                fam = m.group(1).replace('+', ' ').replace('%20', ' ').strip().lower()
                fonts[fam] = fonts.get(fam, 0) + 1
            for m in re.finditer(r'font-family\s*:\s*([^;}{]+)', txt, re.I):
                fam = family_first(m.group(1))
                if fam and not fam.startswith('var('):
                    fonts[fam] = fonts.get(fam, 0) + 1
            trans_all += len(re.findall(r'transition\s*:\s*all\b', txt, re.I))
            if files >= max_files or total >= max_bytes:
                break
        if files >= max_files or total >= max_bytes:
            break
    return {'root': root, 'files': files, 'bytes': total, 'stock_hits': hits[:200], 'declared_fonts': fonts,
            'transition_all': trans_all}


# ---------------------------------------------------------------- сбор с отрисованной страницы
COLLECT_JS = r"""
(conf) => {
  const vw = conf.vw, vh = conf.vh, LIM = 6000;
  const out = {vw, vh, url: location.href, lang: document.documentElement.getAttribute('lang') || ''};
  // служебные пометки артборда [data-wf] — не содержимое страницы: вне проверок, как --ignore-selector
  const ign = Array.from(document.querySelectorAll(conf.ignore ? '[data-wf], ' + conf.ignore : '[data-wf]'));
  const isIgn = (el) => ign.some(g => g === el || g.contains(el));
  const cv = document.createElement('canvas'); cv.width = cv.height = 1;
  const cx = cv.getContext('2d', {willReadFrequently: true});
  const cache = new Map();
  const rgba = (c) => {
    if (!c) return [0, 0, 0, 0];
    if (cache.has(c)) return cache.get(c);
    let v = [0, 0, 0, 0];
    if (c !== 'transparent' && c !== 'rgba(0, 0, 0, 0)') {
      cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1);
      const d = cx.getImageData(0, 0, 1, 1).data; v = [d[0], d[1], d[2], +(d[3] / 255).toFixed(3)];
    }
    cache.set(c, v); return v;
  };
  const desc = (el) => {
    let s = el.tagName.toLowerCase(); if (el.id) s += '#' + el.id;
    const cl = (typeof el.className === 'string') ? el.className.trim().split(/\s+/).filter(Boolean).slice(0, 2) : [];
    if (cl.length) s += '.' + cl.join('.'); return s;
  };
  const visible = (el) => {
    const r = el.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return false;
    let o = 1;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden') return false;
      o *= parseFloat(s.opacity || '1');
    }
    return o >= 0.1;
  };
  const effBg = (el) => {
    const layers = []; let img = false;
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const s = getComputedStyle(e);
      if (s.backgroundImage && s.backgroundImage !== 'none') img = true;
      const c = rgba(s.backgroundColor);
      if (c[3] > 0.02) { layers.push(c); if (c[3] >= 0.99) break; }
    }
    let r = 255, g = 255, b = 255;
    for (let i = layers.length - 1; i >= 0; i--) { const [lr, lg, lb, la] = layers[i];
      r = lr * la + r * (1 - la); g = lg * la + g * (1 - la); b = lb * la + b * (1 - la); }
    return {rgb: [Math.round(r), Math.round(g), Math.round(b)], img};
  };
  const fam1 = (ff) => (ff || '').split(',')[0].trim().replace(/^["']|["']$/g, '').toLowerCase();
  const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();
  const main = document.querySelector('main');

  // --- заголовки: акцентное слово, надзаголовок, пилюля
  const heads = Array.from(document.querySelectorAll('h1, h2, h3')).filter(h => !isIgn(h) && visible(h));
  out.headings = heads.slice(0, 80).map(h => {
    const cs = getComputedStyle(h); const r = h.getBoundingClientRect(); const txt = clean(h.innerText);
    const hc = rgba(cs.color);
    let accent = null;
    for (const d of h.querySelectorAll('em, i, span, strong, b, mark, u, sup, a')) {
      if (!visible(d)) continue;
      const dt = clean(d.innerText); if (!dt || dt.length >= txt.length * 0.6) continue;
      const ds = getComputedStyle(d); const dc = rgba(ds.color); const reasons = [];
      if (ds.fontStyle !== cs.fontStyle && ds.fontStyle !== 'normal') reasons.push('italic');
      if (Math.hypot(dc[0] - hc[0], dc[1] - hc[1], dc[2] - hc[2]) > 40) reasons.push('colour');
      const clip = ds.webkitBackgroundClip || ds.backgroundClip;
      if (clip === 'text' && /gradient/.test(ds.backgroundImage)) reasons.push('gradient');
      if (fam1(ds.fontFamily) !== fam1(cs.fontFamily)) reasons.push('font');
      if (/underline/.test(ds.textDecorationLine) && !/underline/.test(cs.textDecorationLine) && d.tagName !== 'A') reasons.push('underline');
      if (rgba(ds.backgroundColor)[3] > 0.2) reasons.push('highlight');
      if (reasons.length) { accent = {text: dt.slice(0, 40), el: desc(d), reasons}; break; }
    }
    const clipH = cs.webkitBackgroundClip || cs.backgroundClip;
    let eyebrow = null, pill = null;
    const prev = h.previousElementSibling;
    if (prev && !isIgn(prev) && visible(prev)) {
      const ps = getComputedStyle(prev); const pt = clean(prev.innerText);
      const fs = parseFloat(ps.fontSize), hfs = parseFloat(cs.fontSize);
      const ls = ps.letterSpacing === 'normal' ? 0 : parseFloat(ps.letterSpacing);
      const letters = pt.replace(/[^A-Za-zА-Яа-яЁё]/g, '');
      const caps = ps.textTransform === 'uppercase' || (letters.length >= 3 && letters === letters.toUpperCase());
      if (pt && pt.length <= 70 && caps && fs <= Math.min(15, hfs * 0.7) && ls / fs >= 0.04)
        eyebrow = {text: pt.slice(0, 40), fs, ls_em: +(ls / fs).toFixed(3), el: desc(prev)};
      const pr = prev.getBoundingClientRect(); const rad = parseFloat(ps.borderTopLeftRadius) || 0;
      const box = rgba(ps.backgroundColor)[3] > 0.05 || parseFloat(ps.borderTopWidth) > 0;
      if (h.tagName === 'H1' && pt && pt.length <= 70 && pr.height <= 48 && rad >= pr.height * 0.45 && box && pr.width < vw * 0.7)
        pill = {text: pt.slice(0, 50), el: desc(prev)};
    }
    const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2;
    return {tag: h.tagName.toLowerCase(), el: desc(h), text: txt.slice(0, 120), ff: cs.fontFamily,
            fs: parseFloat(cs.fontSize), fw: cs.fontWeight, style: cs.fontStyle, align: cs.textAlign,
            x: r.left, w: r.width, top: r.top + scrollY, h: r.height, lines: Math.max(1, Math.round(r.height / lh)),
            color: hc, accent, grad: clipH === 'text' && /gradient/.test(cs.backgroundImage), eyebrow, pill};
  });

  // --- текстовые узлы: шрифты, капс, моно, «·», стрелки, контраст
  const leaves = []; const seen = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode() && leaves.length < 3000) {
    const t = walker.currentNode; if (!clean(t.textContent)) continue;
    const el = t.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
    if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(el.tagName) || el.closest('svg')) continue;
    if (isIgn(el) || !visible(el)) continue;
    const cs = getComputedStyle(el); const bg = effBg(el);
    const own = clean(Array.from(el.childNodes).filter(c => c.nodeType === 3).map(c => c.textContent).join(' '));
    const link = el.closest('a[href]');
    let ext = false;
    if (link && /^https?:/i.test(link.getAttribute('href') || '')) { try { ext = new URL(link.href).host !== location.host; } catch (e) {} }
    leaves.push({el: desc(el), tag: el.tagName.toLowerCase(), text: own.slice(0, 160), fs: parseFloat(cs.fontSize),
                 fw: parseInt(cs.fontWeight) || 400, ff: cs.fontFamily, tt: cs.textTransform,
                 ls: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing), color: rgba(cs.color), bg: bg.rgb,
                 bg_img: bg.img, in_btn: !!el.closest('button, a, [role=button]'), ext,
                 body: main ? main.contains(el) : !el.closest('header, footer, nav')});
  }
  out.leaves = leaves;

  // --- наложение текста: прямоугольники строк текстовых узлов (Range.getClientRects), не контейнеров
  const rects = []; const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let tn = 0;
  while (tw.nextNode() && rects.length < 1500) {
    const t = tw.currentNode; const txt = clean(t.textContent); if (txt.length < 2) continue;
    const el = t.parentElement; if (!el || isIgn(el) || el.closest('svg') || ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName)) continue;
    if (!visible(el)) continue;
    tn++;
    const rg = document.createRange(); rg.selectNodeContents(t);
    const cr = Array.from(rg.getClientRects()).filter(r => r.width >= 3 && r.height >= 3).slice(0, 6);
    for (const r of cr) rects.push({n: tn, x: r.left, y: r.top + scrollY, w: r.width, h: r.height, text: txt.slice(0, 30), el: desc(el)});
  }
  const overlaps = [];
  for (let i = 0; i < rects.length && overlaps.length < 12; i++) {
    const a = rects[i];
    for (let j = i + 1; j < rects.length; j++) {
      const b = rects[j]; if (a.n === b.n) continue;
      const ix = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x); if (ix <= 0) continue;
      const iy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y); if (iy <= 0) continue;
      const inter = ix * iy, small = Math.min(a.w * a.h, b.w * b.h);
      if (inter >= 0.3 * small) { overlaps.push({a: a.text, a_el: a.el, b: b.text, b_el: b.el, y: Math.round(Math.min(a.y, b.y)), share: +(inter / small).toFixed(2)}); break; }
    }
  }
  out.text_overlaps = overlaps;

  // --- блоки текста для сверки с copy.md и facts.md
  const blocks = []; const BLK = 'h1,h2,h3,h4,h5,h6,p,li,button,figcaption,blockquote,td,th,dt,dd,label';
  for (const el of document.querySelectorAll(BLK + ',a,small,strong,span,q,cite')) {
    if (blocks.length >= 1500) break;
    if (isIgn(el) || !visible(el)) continue;
    if (el.querySelector('h1,h2,h3,h4,h5,h6,p,li,figcaption,blockquote,td,dd')) continue;
    if (['A', 'SMALL', 'STRONG', 'SPAN', 'Q', 'CITE'].includes(el.tagName) && el.parentElement && el.parentElement.closest(BLK)) continue;
    const t = clean(el.innerText); if (!t) continue;
    blocks.push({el: desc(el), tag: el.tagName.toLowerCase(), text: t.slice(0, 400),
                 quote: !!el.closest('blockquote, q, [class*=testimonial i], [class*=review i], [class*=quote i]')});
  }
  out.blocks = blocks;

  // --- картинки, фоны, источники
  out.images = Array.from(document.querySelectorAll('img')).filter(im => !isIgn(im)).slice(0, 200).map(im => {
    const r = im.getBoundingClientRect(); const fig = im.closest('figure');
    const cap = fig && fig.querySelector('figcaption') ? clean(fig.querySelector('figcaption').innerText) : null;
    return {el: desc(im), src: im.currentSrc || im.src || '', srcset: im.getAttribute('srcset') || '', alt: im.getAttribute('alt'),
            w: r.width, h: r.height, visible: visible(im), caption: cap};
  });
  const bgs = []; let k = 0;
  for (const el of document.querySelectorAll('body *')) {
    if (++k > LIM || bgs.length >= 120) break; if (isIgn(el)) continue;
    for (const ps of [null, '::before', '::after']) {
      const s = getComputedStyle(el, ps);
      if (s.backgroundImage && s.backgroundImage.includes('url(')) bgs.push({el: desc(el) + (ps || ''), value: s.backgroundImage.slice(0, 500), visible: visible(el)});
    }
  }
  out.bg_images = bgs;
  out.media_src = Array.from(document.querySelectorAll('source[srcset], source[src], video[poster], video[src]')).slice(0, 60)
      .flatMap(s => ['srcset', 'src', 'poster'].map(a => s.getAttribute(a) || '')).filter(Boolean);
  // постер и источники видео, источники <picture>: файлы страницы наравне с <img> — сверяются со списком ассетов
  const media = [];
  for (const v of Array.from(document.querySelectorAll('video')).filter(v => !isIgn(v)).slice(0, 40)) {
    const vis = visible(v);
    if (v.getAttribute('poster')) media.push({el: desc(v), kind: 'poster', src: v.poster || v.getAttribute('poster'), visible: vis});
    if (v.getAttribute('src')) media.push({el: desc(v), kind: 'video', src: v.src || v.getAttribute('src'), visible: vis});
    for (const s of v.querySelectorAll('source[src]')) media.push({el: desc(v), kind: 'source', src: s.src || s.getAttribute('src'), visible: vis});
  }
  for (const s of Array.from(document.querySelectorAll('picture source[srcset]')).filter(s => !isIgn(s)).slice(0, 60)) {
    const im = s.parentElement.querySelector('img');
    media.push({el: desc(s.parentElement), kind: 'source', src: s.getAttribute('srcset') || '', visible: im ? visible(im) : true});
  }
  out.media = media;

  // --- фон страницы и секций
  const cands = [...document.body.children, ...(main ? main.children : [])];
  out.sections = cands.filter(el => !isIgn(el) && visible(el)).map(el => {
    const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return {el: desc(el), top: r.top + scrollY, h: r.height, w: r.width, bg: effBg(el).rgb, bg_img: s.backgroundImage !== 'none'};
  }).filter(s => s.h >= 120).slice(0, 60);
  let cvArea = 0;
  for (const c of document.querySelectorAll('canvas, video')) {
    if (isIgn(c) || !visible(c)) continue; const r = c.getBoundingClientRect();
    const w = Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0)), hh = Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0));
    cvArea += w * hh;
  }
  out.canvas_share = Math.min(1, cvArea / (vw * vh));
  out.page_bg = effBg(document.body).rgb;
  out.page_h = document.documentElement.scrollHeight;
  out.scroll_w = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);

  // --- hero: высота, центрирование, фото под вуалью
  const h1 = heads.find(h => h.tagName === 'H1') || null;
  out.hero = null;
  if (h1) {
    // hero — блок верхнего уровня с H1 (ребёнок body или main). Когда этот блок — обёртка, а не секция (рамка копии
    // артборда без <main>, корень приложения), hero — самая внешняя секция разметки между обёрткой и H1
    let hero = h1;
    while (hero.parentElement && hero.parentElement !== document.body && hero.parentElement !== main) hero = hero.parentElement;
    if (hero !== h1 && !hero.matches('section, [data-section], header')) {
      let sec = null;
      for (let e = h1.parentElement; e && e !== hero; e = e.parentElement) if (e.matches('section, [data-section]')) sec = e;
      if (sec) hero = sec;
    }
    const hr = hero.getBoundingClientRect(); const hs = getComputedStyle(hero); const h1s = getComputedStyle(h1); const h1r = h1.getBoundingClientRect();
    const area = Math.max(1, hr.width * Math.min(hr.height, Math.max(vh, 1)));
    const media = [], bgUrl = [], overlays = [];
    const all = [hero, ...hero.querySelectorAll('*')].filter(m => !isIgn(m)).slice(0, 500);
    for (const m of all) {
      const r = m.getBoundingClientRect(); const s = getComputedStyle(m);
      const big = r.width >= hr.width * 0.85 && r.height >= Math.min(hr.height, vh) * 0.5;
      if (big && ['IMG', 'VIDEO', 'PICTURE', 'CANVAS'].includes(m.tagName)) media.push({el: desc(m), tag: m.tagName.toLowerCase()});
      if (big && s.backgroundImage.includes('url(')) bgUrl.push({el: desc(m), veil_in_same: /gradient/.test(s.backgroundImage)});
      for (const ps of [null, '::before', '::after']) {
        const q = getComputedStyle(m, ps);
        if (ps && (q.content === 'none' || q.content === 'normal')) continue;
        if (!ps && !(q.position === 'absolute' || q.position === 'fixed')) continue;
        if (ps && !(q.position === 'absolute' || q.position === 'fixed')) continue;
        const cover = (r.width * r.height) / area;
        const c = rgba(q.backgroundColor);
        const lum = (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255;
        const darkFill = c[3] >= 0.15 && c[3] <= 0.95 && lum < 0.45;
        const gradDark = /gradient/.test(q.backgroundImage) && /rgba?\(\s*\d{1,2},\s*\d{1,2},\s*\d{1,2}|#000|black|rgba\(0, 0, 0/.test(q.backgroundImage);
        if ((darkFill || gradDark) && cover >= 0.6) overlays.push({el: desc(m) + (ps || ''), alpha: c[3], grad: gradDark});
      }
    }
    // продолжение: край следующего блока в окне или знак прокрутки в нижней четверти hero
    let next = hero.nextElementSibling;
    while (next && (!visible(next) || ['SCRIPT', 'STYLE', 'TEMPLATE'].includes(next.tagName))) next = next.nextElementSibling;
    const nextTop = next ? next.getBoundingClientRect().top : null;
    const cueRx = /[↓⌄⬇]|листа|прокрут|scroll|ниже|вниз/i;
    const cue = all.some(m => { const r = m.getBoundingClientRect();
      return r.top >= hr.top + hr.height * 0.75 && r.bottom <= hr.bottom + 2 && visible(m) &&
             cueRx.test((m.getAttribute && (m.getAttribute('aria-label') || '')) + ' ' + (m.children.length ? '' : clean(m.textContent))); });
    out.hero = {el: desc(hero), h: hr.height, w: hr.width, top: hr.top + scrollY, h1_align: h1s.textAlign, hero_align: hs.textAlign,
                h1_cx: (h1r.left + h1r.width / 2) / vw, h1_w: h1r.width / vw, min_height: hs.minHeight,
                h1_lines: Math.max(1, Math.round(h1r.height / (parseFloat(h1s.lineHeight) || parseFloat(h1s.fontSize) * 1.2))),
                media: media.slice(0, 5), bg_url: bgUrl.slice(0, 5), overlays: overlays.slice(0, 5),
                next_top: nextTop, cue};
  }

  // --- ряды: ряд цифр, три одинаковые карточки
  const rows = []; k = 0;
  for (const p of document.querySelectorAll('body *')) {
    if (++k > LIM || rows.length > 200) break; if (isIgn(p)) continue;
    const kids = Array.from(p.children).filter(c => visible(c) && !isIgn(c));
    if (kids.length < 3 || kids.length > 6) continue;
    const rs = kids.map(c => c.getBoundingClientRect()); const t0 = rs[0].top;
    if (!rs.every(r => Math.abs(r.top - t0) < 10)) continue;
    const pr = p.getBoundingClientRect(); if (pr.width < vw * 0.5) continue;
    const ws = rs.map(r => r.width), hs2 = rs.map(r => r.height);
    const sig = kids.map(c => c.tagName + ':' + c.children.length);
    const nums = kids.map(c => {
      let best = null;
      for (const e of [c, ...c.querySelectorAll('*')]) {
        if (e.children.length) continue; const t = clean(e.innerText); const fs = parseFloat(getComputedStyle(e).fontSize);
        if (t && t.length <= 14 && /\d/.test(t) && /^[~≈<>]?\s*[$€£₽]?\s*[\d\s.,]+\s*(%|\+|k|K|M|x|×|млн|тыс|₽|\$|€|£|ч|h|min|мин|\/\s*\d+)?\s*\+?$/.test(t) && fs >= 28)
          if (!best || fs > best.fs) best = {t, fs};
      }
      return best;
    }).filter(Boolean);
    const lens = kids.map(c => clean(c.innerText).length);
    const mean = lens.reduce((a, b) => a + b, 0) / lens.length;
    const cv = mean ? Math.sqrt(lens.reduce((a, b) => a + (b - mean) * (b - mean), 0) / lens.length) / mean : 0;
    rows.push({el: desc(p), n: kids.length, top: t0 + scrollY, w_ratio: Math.max(...ws) / Math.max(1, Math.min(...ws)), cv: +cv.toFixed(3),
               h_ratio: Math.max(...hs2) / Math.max(1, Math.min(...hs2)), min_w: Math.min(...ws) / pr.width, min_h: Math.min(...hs2),
               same: sig.every(s => s === sig[0]), content: kids.every(c => !!c.querySelector('h2,h3,h4,h5,p,strong')),
               ph: kids.filter(c => /\[PLACEHOLDER/i.test(c.innerText || '')).length,
               nums: nums.length, num_texts: nums.map(x => x.t), in_chrome: !!p.closest('nav, header, footer')});
  }
  out.rows = rows;

  // --- бенто: сетка из однотипных плиток с одним радиусом и одним отступом
  const bento = []; k = 0;
  for (const g of document.querySelectorAll('body *')) {
    if (++k > LIM || bento.length > 20) break; if (isIgn(g) || !visible(g)) continue;
    const gs = getComputedStyle(g);
    if (!(gs.display.includes('grid') || (gs.display.includes('flex') && gs.flexWrap === 'wrap'))) continue;
    const tiles = Array.from(g.children).filter(c => visible(c) && !isIgn(c));
    if (tiles.length < 4) continue;
    const st = tiles.map(c => getComputedStyle(c));
    const rad = st.map(x => x.borderTopLeftRadius), pad = st.map(x => x.paddingTop + ' ' + x.paddingLeft);
    const sig = tiles.map(c => c.tagName + ':' + c.children.length);
    const areas = tiles.map(c => { const r = c.getBoundingClientRect(); return Math.round(r.width) + 'x' + Math.round(r.height); });
    const tops = new Set(tiles.map(c => Math.round(c.getBoundingClientRect().top)));
    bento.push({el: desc(g), n: tiles.length, one_radius: new Set(rad).size === 1 && parseFloat(rad[0]) > 0, radius: rad[0],
                one_padding: new Set(pad).size === 1, same: new Set(sig).size === 1, sizes: new Set(areas).size, rows: tops.size,
                in_chrome: !!g.closest('nav, header, footer')});
  }
  out.bento = bento;

  // --- орбита: иконки на окружности вокруг общего центра в контейнере с бесконечной анимацией
  const orbit = []; k = 0;
  for (const c of document.querySelectorAll('body *')) {
    if (++k > LIM || orbit.length > 10) break; if (isIgn(c) || !visible(c)) continue;
    const spinning = (el) => { const s = getComputedStyle(el); return s.animationName && s.animationName !== 'none' && s.animationIterationCount === 'infinite'; };
    if (!spinning(c) && !Array.from(c.children).some(spinning)) continue;
    const icons = Array.from(c.querySelectorAll('img, svg, picture, i, [class*=icon i], [class*=logo i]')).filter(x => {
      if (!visible(x) || (x.tagName.toLowerCase() !== 'svg' && x.closest('svg'))) return false;
      const r = x.getBoundingClientRect(); return r.width <= 120 && r.height <= 120 && r.width >= 8; });
    if (icons.length < 3) continue;
    const cr = c.getBoundingClientRect(), cx0 = cr.left + cr.width / 2, cy0 = cr.top + cr.height / 2;
    const dist = icons.map(x => { const r = x.getBoundingClientRect(); return Math.hypot(r.left + r.width / 2 - cx0, r.top + r.height / 2 - cy0); });
    const m = dist.reduce((a, b) => a + b, 0) / dist.length;
    const sd = Math.sqrt(dist.reduce((a, b) => a + (b - m) * (b - m), 0) / dist.length);
    orbit.push({el: desc(c), icons: icons.length, radius: Math.round(m), ring_cv: m ? +(sd / m).toFixed(3) : 1, top: cr.top + scrollY});
  }
  out.orbit = orbit;

  // --- шапка: первый видимый header или role=banner у верха страницы
  const hdr = Array.from(document.querySelectorAll('header, [role=banner]')).find(h => visible(h) && h.getBoundingClientRect().top + scrollY < 60);
  out.header = hdr ? {el: desc(hdr), h: +hdr.getBoundingClientRect().height.toFixed(1)} : null;

  // --- формы: поля, подписи, согласия, кнопка отправки
  const labelOf = (f) => {
    let t = '';
    if (f.id) { const l = document.querySelector('label[for="' + CSS.escape(f.id) + '"]'); if (l) t = clean(l.innerText); }
    if (!t && f.closest('label')) t = clean(f.closest('label').innerText);
    return t || clean(f.getAttribute('aria-label') || '');
  };
  const forms = [];
  const roots = Array.from(document.querySelectorAll('form'));
  for (const fm of roots.slice(0, 10)) {
    if (isIgn(fm)) continue;
    const fields = Array.from(fm.querySelectorAll('input, select, textarea')).filter(f => !['hidden', 'submit', 'button', 'reset', 'image'].includes((f.type || '').toLowerCase()));
    const submit = fm.querySelector('button[type=submit], input[type=submit], button:not([type])');
    forms.push({el: desc(fm), in_dialog: !!fm.closest('dialog, [role=dialog], [aria-modal=true]'), text: clean(fm.innerText).slice(0, 1500),
                submit: submit ? {text: clean(submit.innerText || submit.value || ''), disabled: !!submit.disabled} : null,
                fields: fields.slice(0, 30).map(f => ({tag: f.tagName.toLowerCase(), type: (f.type || '').toLowerCase(), name: f.getAttribute('name') || '',
                  id: f.id || '', autocomplete: (f.getAttribute('autocomplete') || '').toLowerCase(), required: !!f.required,
                  checked: !!f.checked, label: labelOf(f), placeholder: f.getAttribute('placeholder') || '', visible: visible(f),
                  hidden_trap: !visible(f) || f.getAttribute('tabindex') === '-1' || f.getAttribute('aria-hidden') === 'true'}))});
  }
  out.forms = forms;

  // --- стекло, градиентный текст, бегущая строка, нарисованный хром
  const glass = [], gradText = [], marquee = [], dots = []; k = 0;
  for (const e of document.querySelectorAll('body *')) {
    if (++k > LIM) break; if (isIgn(e)) continue;
    const s = getComputedStyle(e);
    if (/blur/.test(s.backdropFilter || s.webkitBackdropFilter || '') && visible(e)) glass.push(desc(e));
    const clip = s.webkitBackgroundClip || s.backgroundClip;
    if (clip === 'text' && /gradient/.test(s.backgroundImage) && visible(e)) gradText.push({el: desc(e), text: clean(e.innerText).slice(0, 40)});
    if (e.tagName === 'MARQUEE') marquee.push(desc(e));
    else if (s.animationName && s.animationName !== 'none' && s.animationIterationCount === 'infinite' && e.parentElement &&
             e.scrollWidth > e.parentElement.clientWidth * 1.5) marquee.push(desc(e));
    const kids = e.children;
    if (kids.length >= 3 && kids.length <= 4) {
      let small = 0;
      for (const c of kids) { const r = c.getBoundingClientRect(); const cs2 = getComputedStyle(c);
        if (r.width > 4 && r.width <= 16 && Math.abs(r.width - r.height) <= 2 && parseFloat(cs2.borderTopLeftRadius) >= r.width * 0.45 && rgba(cs2.backgroundColor)[3] > 0.3) small++; }
      if (small >= 3) dots.push(desc(e));
    }
  }
  out.glass = glass.slice(0, 20); out.grad_text = gradText.slice(0, 20); out.marquee = marquee.slice(0, 10); out.drawn_dots = dots.slice(0, 10);

  // --- навигация
  const navs = [];
  for (const n of document.querySelectorAll('nav, header')) {
    if (isIgn(n) || !visible(n)) continue;
    navs.push({el: desc(n), links: Array.from(n.querySelectorAll('a[href], button')).filter(a => visible(a)).length});
  }
  const toggles = [];
  for (const b of document.querySelectorAll('button, [role=button], a, label, [aria-expanded], [aria-controls], [class*=menu i], [class*=burger i], [id*=menu i], [class*=toggle i]')) {
    if (toggles.length >= 10) break; if (isIgn(b) || !visible(b)) continue;
    const idc = ((b.id || '') + ' ' + (typeof b.className === 'string' ? b.className : '') + ' ' + (b.getAttribute('aria-label') || '')).toLowerCase();
    if (b.hasAttribute('aria-expanded') || b.hasAttribute('aria-controls') || /(menu|burger|hamburger|nav-?toggle|navbar-toggler|меню)/.test(idc)) {
      const r = b.getBoundingClientRect(); toggles.push({el: desc(b), top: r.top, w: r.width, h: r.height});
    }
  }
  out.nav = {navs: navs.slice(0, 10), toggles};

  if (conf.full) {
    let css = '';
    for (const sh of Array.from(document.styleSheets)) { try { for (const r of Array.from(sh.cssRules)) { css += r.cssText + '\n'; if (css.length > 2e6) break; } } catch (e) {} }
    out.html = document.documentElement.outerHTML.slice(0, 3e6); out.css = css.slice(0, 2e6);
  }
  return out;
}
"""


def free_gb():
    try:
        for line in open('/proc/meminfo'):
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) / 1024 / 1024
    except OSError:
        pass
    return None


def make_router(host, blocked):
    """Обработчик page.route с одним параметром (Playwright передаёт (route, request), если параметров два)."""
    def handler(route):
        u = urlparse(route.request.url)
        if u.scheme in ('data', 'blob') or u.netloc == host:
            return route.continue_()
        blocked.append(route.request.url[:200])
        return route.abort()
    return handler


def shot_name(w, h, copy=None):
    """Файл кадра первого экрана в --shots: у статичной копии артборда — по имени копии (части одного артборда и
    артборды разных страниц одной ширины кладутся в одну папку и друг друга не затирают), у другой цели — по классу
    окна (`desktop-1440x900-00.jpg` — имена видов страницы слепого выбора `stand_page.py`)."""
    kind = 'desktop' if w >= 1024 else ('tablet' if w >= 768 else 'mobile')
    return f'{copy or kind}-{w}x{h}-00.jpg'


def collect(target, views, ignore, block_external, shots_dir, copy=None):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    import functools, http.server, socketserver, threading
    httpd, url, local_host = None, target, None
    if not target.startswith(('http://', 'https://', 'file://')):
        path = os.path.abspath(target)
        if not os.path.exists(path):
            raise SystemExit(f'нет файла или папки: {path}')
        root, name = (path, '') if os.path.isdir(path) else (os.path.dirname(path), os.path.basename(path))
        safe_root(root)

        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a):
                pass
        httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=root))
        httpd.daemon_threads = True
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{httpd.server_address[1]}/{name}'
        local_host = f'127.0.0.1:{httpd.server_address[1]}'
    results, blocked = [], []
    try:
        with kbpaths.lock('browser'), sync_playwright() as p:     # браузер один за раз на машину
            browser = p.chromium.launch()
            try:
                for i, spec in enumerate(views):
                    w, h = (int(x) for x in spec.lower().split('x'))
                    ctx = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1,
                                              is_mobile=w < 768, has_touch=w < 1024, reduced_motion='reduce')
                    page = ctx.new_page()
                    if block_external:
                        page.route('**/*', make_router(local_host or urlparse(url).netloc, blocked))
                    try:
                        page.goto(url, wait_until='networkidle', timeout=60000)
                    except PWTimeout:
                        pass
                    page.wait_for_timeout(400)
                    total = page.evaluate('document.documentElement.scrollHeight')
                    y = 0
                    while y < total and y < 40000:           # догрузить lazy и отыграть reveal-анимации
                        page.evaluate(f'window.scrollTo(0, {y})'); page.wait_for_timeout(100); y += h
                    page.evaluate('window.scrollTo(0, 0)'); page.wait_for_timeout(300)
                    data = page.evaluate(COLLECT_JS, {'vw': w, 'vh': h, 'ignore': ignore or '', 'full': i == 0})
                    data['viewport'] = spec
                    if shots_dir:
                        os.makedirs(shots_dir, exist_ok=True)
                        fn = os.path.join(shots_dir, shot_name(w, h, copy))
                        try:                              # WebGL-страницы бывают «нестабильны» для скриншота — не ронять прогон
                            page.screenshot(path=fn, type='jpeg', quality=80, animations='disabled', timeout=15000)
                            data['shot'] = os.path.abspath(fn)
                        except Exception as e:  # noqa: BLE001
                            data['shot_error'] = f'{type(e).__name__}: {str(e)[:120]}'
                    results.append(data)
                    ctx.close()
            finally:
                browser.close()
    finally:
        if httpd:
            httpd.shutdown(); httpd.server_close()
    return url, results, sorted(set(blocked))[:50]


# ---------------------------------------------------------------- анализ
def add(findings, fid, sev, view, msg, evidence=None, fix=None, allowed=()):
    """Находка: id проверки, примета и группа — из реестра примет (`checks`). Ключ --allow снимает находку до info и
    помечает её: `allowed`, ключ `allow`, тяжесть без ключа `base_severity`, причина `reason` — решение о примете вида
    или, у проверки приёмки, решение плана страницы."""
    row = registry()['checks'].get(fid, {})
    key = row.get('allow')
    lifted = bool(key and key in allowed)
    f = {'id': fid, 'tell': row.get('tell'), 'group': row.get('group'), 'severity': sev, 'view': view,
         'message': msg, 'evidence': evidence or {}, 'fix': fix or '', 'allowed': lifted}
    if lifted:
        why = 'решение плана страницы' if row.get('group') == 'acceptance' else 'решение записано'
        f.update(severity='info', allow=key, base_severity=sev, reason=f'{why}: --allow {key}',
                 message=f'{msg} ({why}: --allow {key}; без ключа — {sev})')
    findings.append(f)


def urls_in(text):
    return re.findall(r'url\(["\']?([^"\')]+)["\']?\)', text or '')


def stock_kind(u):
    for kind, rx in STOCK_PATTERNS:
        if re.search(rx, u or '', re.I):
            return kind
    return None


def sequence(texts):
    """1, 2, 3 или 01, 02, 03 — номера шагов, а не ряд чисел-доказательств."""
    try:
        vals = [int(t.strip().rstrip('.)')) for t in texts]
    except ValueError:
        return False
    return len(vals) >= 2 and all(0 < v < 100 for v in vals) and vals == list(range(vals[0], vals[0] + len(vals)))


def view_w(v):
    return int(v['viewport'].split('x')[0])


def form_field_id(f, fields_lib):
    """Поле DOM → id поля библиотеки lead-forms.yaml: name, autocomplete, тип, подпись."""
    name = (f['name'] or f['id'] or '').lower()
    if name in fields_lib:
        return name
    ac = {'name': 'name', 'tel': 'phone', 'email': 'email', 'organization': 'company', 'organization-title': 'role',
          'street-address': 'address', 'address-level2': 'city'}
    if f['autocomplete'] in ac:
        return ac[f['autocomplete']]
    if f['type'] in ('tel', 'email'):
        return {'tel': 'phone', 'email': 'email'}[f['type']]
    lab = norm_text(f['label'])
    for fid, spec in fields_lib.items():
        if isinstance(spec, dict) and spec.get('label') and norm_text(spec['label']) == lab:
            return fid
    return None


CONSENT_RX = re.compile(r'персональн|обработк\w* (?:моих |своих )?(?:данн|имени|телефон)|\bпд\b|согласи', re.I)
BUNDLE_RX = re.compile(r'оферт|рассылк|реклам|маркетинг', re.I)
BY_BUTTON_RX = re.compile(r'нажима\w+\s+(?:на\s+)?кнопк\w*[^.]{0,80}соглаша', re.I)


# Запреты формы заявки сайта: согласие на обработку ПД и обязательный комментарий первичной заявки. У экрана
# приложения формы служебные (заявка менеджера, настройки) — эти запреты к ним не относятся.
LEAD_ONLY = {'prechecked-consent', 'no-separate-consent', 'consent-by-button', 'bundled-consent', 'required-comment'}


def check_forms(F, desk, form_sets, allowed, surface='page'):
    """Формы по lead-forms.yaml: запреты `forbidden`, видимые в DOM, — у любой формы, запреты формы заявки (LEAD_ONLY) —
    только у страницы сайта; поля и подписи — против наборов --forms (форма страницы ↔ набор по наибольшему совпадению
    полей)."""
    lf = lead_forms()
    lib, forb = lf['fields'], lf['forbidden']
    modal_max = (lf['defaults'] or {}).get('modal_max_fields')
    view = desk['viewport']
    for fm in desk.get('forms') or []:
        fields = [f for f in fm['fields'] if not f['hidden_trap'] or f['type'] not in ('text', '')]
        people = [f for f in fields if f['type'] not in ('checkbox', 'radio')]
        boxes = [f for f in fields if f['type'] == 'checkbox']
        ids = [form_field_id(f, lib) for f in people]
        consent = [b for b in boxes if CONSENT_RX.search(b['label'] or '')]
        pd = [i for i in ids if i in ('name', 'phone', 'email')] or [f for f in people if f['type'] in ('tel', 'email')]
        bad = []
        for b in boxes:
            if b['checked'] and (CONSENT_RX.search(b['label'] or '') or BUNDLE_RX.search(b['label'] or '')):
                bad.append(('prechecked-consent', 'critical', f"галочка «{b['label'][:50]}» отмечена заранее"))
        if pd and not consent:
            bad.append(('consent-by-button' if BY_BUTTON_RX.search(fm['text']) else 'no-separate-consent', 'critical',
                        'согласие «нажимая кнопку…» вместо отдельной галочки' if BY_BUTTON_RX.search(fm['text'])
                        else 'нет отдельной неотмеченной галочки согласия на обработку ПД'))
        for b in consent:
            if BUNDLE_RX.search(b['label'] or ''):
                bad.append(('bundled-consent', 'critical', f"одно согласие на ПД и рассылку или оферту: «{b['label'][:60]}»"))
        if fm['submit'] and fm['submit']['disabled']:
            bad.append(('disabled-submit', 'major', 'кнопка отправки неактивна до нажатия'))
        if sum(1 for i in ids if i == 'email') > 1 or any(re.search(r'повтор', f['label'] or '', re.I) for f in people):
            bad.append(('repeat-email', 'major', 'поле «повторите почту»'))
        for f, i in zip(people, ids):
            if f['required'] and (i in ('task', 'address') or f['tag'] == 'textarea'):
                bad.append(('required-comment', 'major', f"обязательное поле «{f['label'] or f['name']}» в первичной заявке"))
            if f['autocomplete'] == 'off' and i in ('name', 'phone', 'email'):
                bad.append(('autocomplete-off', 'major', f"autocomplete=off у поля «{f['label'] or f['name']}»"))
        if fm['in_dialog'] and modal_max and len(people) > modal_max:
            bad.append(('modal-long-form', 'major', f'форма в окне из {len(people)} полей (> {modal_max})'))
        for fid, sev, msg in bad:
            if surface != 'page' and fid in LEAD_ONLY:
                continue
            rule = (forb.get(fid) or {}).get('rule') or ''
            add(F, 'FORM-FORBIDDEN', sev, view, f"форма {fm['el']}: {msg}",
                {'form': fm['el'], 'forbidden': fid, 'rule': rule}, 'снять запрещённый приём формы (lead-forms.yaml, '
                'раздел forbidden): согласие — отдельной неотмеченной галочкой, поля — по набору формы', allowed)
    if not form_sets:
        return
    sets = lf['sets']
    forms = desk.get('forms') or []
    for sid in form_sets:
        spec = sets[sid]
        want = [x['field'] for x in spec.get('fields') or [] if isinstance(x, dict)]
        if not want:
            continue
        best, got_best = None, []
        for fm in forms:
            got = [form_field_id(f, lib) for f in fm['fields'] if f['type'] not in ('checkbox', 'hidden')
                   and not f['hidden_trap']]
            if best is None or len(set(got) & set(want)) > len(set(got_best) & set(want)):
                best, got_best = fm, got
        if best is None:
            add(F, 'FORM-FIELDS', 'major', view, f'формы набора {sid} на странице нет',
                {'set': sid, 'fields': want}, f'форма по набору {sid} lead-forms.yaml: поля {", ".join(want)}', allowed)
            continue
        req = {x['field']: bool(x.get('required')) for x in spec.get('fields') or [] if isinstance(x, dict)}
        miss = [w for w in want if w not in got_best]
        people = [f for f in best['fields'] if f['type'] not in ('checkbox', 'hidden') and not f['hidden_trap']]
        extra = [g or (f['label'] or f['name'] or f['tag']) for f, g in zip(people, got_best) if g not in want]
        nolabel = [f['name'] or f['placeholder'] or f['tag'] for f in people if not f['label']]
        wrong_req = [g for f, g in zip(people, got_best) if g in req and f['required'] and not req[g]]
        problems = ([f'нет полей набора: {", ".join(miss)}'] if miss else []) + \
                   ([f'поля вне набора: {", ".join(extra)}'] if extra else []) + \
                   ([f'поля без видимой подписи (подсказка вместо подписи): {", ".join(nolabel)}'] if nolabel else []) + \
                   ([f'обязательны, хотя в наборе нет: {", ".join(wrong_req)}'] if wrong_req else [])
        if problems:
            add(F, 'FORM-FIELDS', 'major', view, f"форма {best['el']} против набора {sid}: " + '; '.join(problems),
                {'set': sid, 'want': want, 'got': got_best, 'missing': miss, 'extra': extra, 'no_label': nolabel},
                f'поля, порядок, обязательность и видимые подписи — по набору {sid} lead-forms.yaml', allowed)


def analyze(url, views, static, facts, copy_text, assets, allowed, blocked, opts):
    """opts: surface (page | app), preset (A–D), first_bp, form_sets; ds — гарнитуры и цвета токенов ДС (ds_look),
    demo — демо-набор кабинета (load_demo), uploads — реестр загрузок (load_uploads), part — номер части артборда
    (artboard_part). Кадр с overflow_only — только вылет. Находки — после фильтра поверхности и вердикта кластера
    (verdict)."""
    F = []
    over = [v for v in views if v.get('overflow_only')]
    views = [v for v in views if not v.get('overflow_only')]
    desk = next((v for v in views if view_w(v) >= opts['first_bp']), views[0])
    target_host = urlparse(url).netloc
    ds = opts.get('ds')

    # ---------- тёплая бумага: фон страницы и секций; тёплая нейтраль из токенов ДС — решение, не примета
    for v in views[:1] if len(views) else []:
        page_w = warm_class(v['page_bg'])
        page_ds = bool(page_w) and ds_color(v['page_bg'], ds)
        page_w = page_w and not page_ds
        secs = v['sections']
        total_h = max(1, v['page_h'])
        warm_all = [s for s in secs if warm_class(s['bg'])]
        warm_secs = [s for s in warm_all if not ds_color(s['bg'], ds)]
        share = min(1.0, sum(s['h'] for s in warm_secs) / total_h)
        ev = {'page_bg': hexs(v['page_bg']), 'page_bg_oklch': oklch(v['page_bg']), 'warm_share_of_page': round(share, 2),
              'warm_sections': [{'el': s['el'], 'bg': hexs(s['bg']), 'oklch': oklch(s['bg'])} for s in warm_secs[:6]]}
        if page_w or share >= 0.25:
            add(F, 'LOOK-BG-WARM', 'major', v['viewport'],
                f"тёплый тонированный фон ({'страница ' + hexs(v['page_bg']) if page_w else 'секции'}; доля {share:.0%})",
                ev, 'фон страницы и секций — нейтраль из токенов ДС (без крема, беж и коричнево-чёрного)', allowed)
        elif warm_secs:
            add(F, 'LOOK-BG-WARM', 'minor', v['viewport'], f'тёплая тонированная секция ({len(warm_secs)} шт., доля {share:.0%})',
                ev, 'фон секции — поверхность из токенов ДС', allowed)
        elif page_ds or warm_all:
            ds_bg = sorted(({hexs(v['page_bg'])} if page_ds else set()) | {hexs(s['bg']) for s in warm_all})
            add(F, 'LOOK-BG-WARM', 'info', v['viewport'],
                f"тёплый фон — значения токенов ДС ({', '.join(ds_bg[:4])}): решение ДС, не примета", {'ds_colors': ds_bg})

    # ---------- заголовки: акцентное слово, антиква, надзаголовки, пилюля, градиент
    heads = desk['headings']
    h1s = [h for h in heads if h['tag'] == 'h1']
    acc_h1 = [h for h in h1s if h['accent']]
    acc_h2 = [h for h in heads if h['tag'] != 'h1' and h['accent']]
    if acc_h1:
        a = acc_h1[0]['accent']
        add(F, 'LOOK-ACCENT-WORD', 'major', desk['viewport'],
            f"в h1 выделено слово «{a['text']}» ({', '.join(a['reasons'])})",
            {'h1': acc_h1[0]['text'], 'accent': a, 'h2_with_accent': len(acc_h2)},
            f"H1 {acc_h1[0]['el']}: «{a['text']}» — как весь заголовок (та же гарнитура, начертание, цвет); иерархия — "
            'кеглем, насыщенностью и местом', allowed)
    elif len(acc_h2) >= 2:
        add(F, 'LOOK-ACCENT-WORD', 'minor', desk['viewport'], f'выделенное слово в {len(acc_h2)} подзаголовках',
            {'examples': [h['accent'] for h in acc_h2[:3]]}, 'снять выделенные слова в заголовках секций', allowed)
    # антиква, которую называют токены ДС (--tokens), — решение ДС, не примета
    ds_fam = (ds or {}).get('families') or set()
    serif_all = [h for h in heads if family_kind(h['ff']) == 'serif']
    serif_heads = [h for h in serif_all if family_first(h['ff']) not in ds_fam]
    h2s = [h for h in heads if h['tag'] == 'h2']
    serif_h1 = any(h in serif_heads for h in h1s)
    serif_h2 = h2s and sum(h in serif_heads for h in h2s) / len(h2s) >= 0.5
    body_leaves = [l for l in desk['leaves'] if l['tag'] in ('p', 'li') and len(l['text'].split()) >= 6]
    body_fam = statistics.mode([family_first(l['ff']) for l in body_leaves]) if body_leaves else ''
    if serif_h1 or serif_h2:
        disp = family_first(([h for h in h1s if h in serif_heads] or serif_heads)[0]['ff'])
        pair = body_fam in SANS_DEFAULTS
        italic = any(h['style'] == 'italic' for h in serif_heads if h['tag'] == 'h1')
        add(F, 'LOOK-SERIF-DISPLAY', 'major', desk['viewport'],
            f"антиква в заголовках: {disp or '?'}" + (f" + {body_fam} в тексте (пара «антиква + дефолтный гротеск»)" if pair else '')
            + (' курсивом' if italic else ''),
            {'display': disp, 'body': body_fam, 'serif_headings': len(serif_heads), 'headings': len(heads)},
            'гарнитуры — только из ДС; антиква в заголовках — только если её называет ДС', allowed)
    elif len(serif_heads) < len(serif_all):
        fams = sorted({family_first(h['ff']) for h in serif_all if h not in serif_heads})
        add(F, 'LOOK-SERIF-DISPLAY', 'info', desk['viewport'],
            f"антиква в заголовках — гарнитура токенов ДС ({', '.join(fams)}): решение ДС, не примета", {'ds_families': fams})
    per = eyebrow_per_sections()
    heads12 = [h for h in heads if h['tag'] in ('h1', 'h2')]
    eyebrowed = [h for h in heads12 if h['eyebrow']]
    limit = math.ceil(len(heads12) / per) if per and heads12 else None
    if eyebrowed and limit is not None and len(eyebrowed) > limit:
        add(F, 'LOOK-EYEBROW', 'major', desk['viewport'],
            f'капс-надзаголовки над {len(eyebrowed)} из {len(heads12)} заголовков H1, H2 (> ceil({len(heads12)}/{per}) '
            f'= {limit}; число — COPY-C-18)',
            {'examples': [h['eyebrow'] for h in eyebrowed[:4]], 'per_sections': per, 'limit': limit},
            f'надзаголовок — не чаще одного на {per} секции с заголовком, обычным регистром', allowed)
    elif eyebrowed:
        add(F, 'LOOK-EYEBROW', 'info', desk['viewport'],
            f'капс-надзаголовков {len(eyebrowed)} из {len(heads12)} заголовков H1, H2'
            + (f' (в пределах ceil(N/{per}))' if per else ' (порог COPY-C-18 не найден у владельца)'),
            {'examples': [h['eyebrow'] for h in eyebrowed[:3]], 'per_sections': per})
    pills = [h['pill'] for h in h1s if h['pill']]
    if pills:
        add(F, 'LOOK-PILL', 'minor', desk['viewport'], f"пилюля над h1: «{pills[0]['text']}»", {'pill': pills[0]},
            'снять пилюлю над H1', allowed)
    grad = desk['grad_text']
    if grad:
        in_head = any(h['grad'] or (h['accent'] and 'gradient' in h['accent']['reasons']) for h in heads)
        add(F, 'LOOK-GRADIENT-TEXT', 'major' if in_head else 'minor', desk['viewport'],
            f'градиентный текст: {len(grad)} эл.', {'examples': grad[:3]},
            'снять background-clip: text с градиентом; цвет текста — сплошной токен', allowed)

    # ---------- hero
    hero = desk.get('hero')
    share = hero_height_share()
    if hero and share:
        vh = desk['vh']
        centered = hero['h1_align'] == 'center' or (abs(hero['h1_cx'] - 0.5) < 0.05 and hero['h1_w'] < 0.9 and hero['hero_align'] == 'center')
        cont = hero.get('cue') or (hero.get('next_top') is not None and hero['next_top'] < vh - 1)
        if hero['h'] >= share * vh and centered and not cont:
            add(F, 'LOOK-HERO-CENTER', 'major', desk['viewport'],
                f"hero {hero['h']:.0f} px при окне {vh} (≥ {share:.0%}, AIL-06), всё по центру, продолжения не видно",
                {'hero': hero['el'], 'h': round(hero['h']), 'vh': vh, 'h1_align': hero['h1_align'],
                 'next_top': hero.get('next_top'), 'cue': hero.get('cue')},
                f"hero {hero['el']}: высота по политике первого экрана плана, край следующей секции виден в окне "
                f"{desk['viewport']}; центр — не больше четырёх элементов", allowed)
    if hero and (hero['media'] or hero['bg_url']) and (hero['overlays'] or any(b['veil_in_same'] for b in hero['bg_url'])):
        add(F, 'LOOK-HERO-OVERLAY', 'major', desk['viewport'], 'фото или видео на весь hero под тёмной вуалью',
            {'media': hero['media'][:2] + hero['bg_url'][:2], 'overlays': hero['overlays'][:2]},
            'снять вуаль: ассет героя из списка ассетов в естественном контрасте или сплошная поверхность', allowed)

    # ---------- ряды: цифры, три карточки, бенто, орбита
    rows = desk['rows']
    stats = [r for r in rows if r['nums'] >= 3 and not r['in_chrome'] and not sequence(r['num_texts'])]
    if stats:
        add(F, 'LOOK-STATS-ROW', 'major', desk['viewport'], f"ряд крупных чисел: {', '.join(stats[0]['num_texts'][:5])}",
            {'rows': [{'el': r['el'], 'numbers': r['num_texts']} for r in stats[:3]]},
            'снять ряд чисел, если каждое число не из фактов и бриф его не заказывал', allowed)
    cv_max = cards_cv_max()
    # ряд с заглушками [PLACEHOLDER…] не мерится: одинаковая длина заглушек — не одинаковые тексты карточек
    cards = [r for r in rows if r['n'] == 3 and r['w_ratio'] <= 1.06 and r['h_ratio'] <= 1.25 and r['same'] and
             r['min_w'] >= 0.2 and r['min_h'] >= 120 and r['content'] and not r['in_chrome'] and not r.get('ph') and
             (cv_max is None or r.get('cv', 0) < cv_max)]
    if cards:
        add(F, 'LOOK-THREE-CARDS', 'major', desk['viewport'],
            f'три одинаковые карточки в ряд: {len(cards)} ряд(а)' + (f', вариация длины текстов < {cv_max:g} (AIL-07)'
                                                                   if cv_max else ''),
            {'rows': [{'el': c['el'], 'cv': c.get('cv')} for c in cards[:3]]},
            f"секция {cards[0]['el']}: продукт настоящим интерфейсом или асимметрия (ведущий элемент шире), не три "
            'одинаковые карточки', allowed)
    nb = bento_min_tiles()
    bento = [b for b in desk.get('bento') or [] if nb and b['n'] >= nb and b['one_radius'] and b['one_padding']
             and b['same'] and b['rows'] >= 2 and not b['in_chrome']]
    if bento:
        add(F, 'LOOK-BENTO', 'minor', desk['viewport'],
            f"бенто из однотипных плиток: {bento[0]['n']} плиток с одним радиусом {bento[0]['radius']} и одним отступом",
            {'grids': bento[:3], 'min_tiles': nb}, 'список или чередование «текст ↔ кадр»; бенто — только плитки разного '
            'содержания и веса, главный блок крупнее', allowed)
    no = orbit_min_icons()
    orbit = [o for o in desk.get('orbit') or [] if no and o['icons'] >= no and o['ring_cv'] <= 0.15
             and o['top'] < desk['vh'] * 1.2]
    if orbit:
        add(F, 'LOOK-ORBIT', 'minor', desk['viewport'],
            f"орбита: {orbit[0]['icons']} иконок по кольцу радиуса {orbit[0]['radius']} px с бесконечной анимацией в первом экране",
            {'orbits': orbit[:3], 'min_icons': no}, 'сетка логотипов интеграций с подписями или схема потока данных '
            'кодом — только реальные интеграции', allowed)

    # ---------- шаблонный хром по текстовым узлам
    leaves = desk['leaves']
    n_leaves = max(1, len(leaves))
    caps = [l for l in leaves if l['tt'] == 'uppercase' and re.search(r'[A-Za-zА-Яа-яЁё]{2,}', l['text'])]
    if len(caps) / n_leaves > 0.02 and len(caps) >= 3:
        add(F, 'LOOK-CAPS', 'minor', desk['viewport'], f'капс у {len(caps)} из {n_leaves} текстовых узлов ({len(caps) / n_leaves:.1%} > 2 %, m8)',
            {'examples': [l['text'][:30] for l in caps[:5]]}, 'обычный регистр; капс — не больше одной малой роли', allowed)
    dots = [l for l in leaves if re.search(r'[·•]', l['text']) and len(l['text']) <= 90]
    if len(dots) > 5:
        add(F, 'LOOK-META-DOTS', 'minor', desk['viewport'], f'мета-строки через «·»: {len(dots)} (> 5, m32)',
            {'examples': [l['text'][:50] for l in dots[:4]]}, 'подписи с ролями вместо строк «A · B · C», разделять '
            'пространством', allowed)
    arrows = [l for l in leaves if l['in_btn'] and (re.search(r'[→⟶➝➜⇢↘]', l['text'])
                                                    or ('↗' in l['text'] and not l.get('ext')))]
    if arrows:
        add(F, 'LOOK-ARROWS', 'minor', desk['viewport'], f'стрелки в подписях кнопок и ссылок: {len(arrows)} (m34)',
            {'examples': [l['text'][:30] for l in arrows[:4]]}, 'стрелку — из текста подписи; иконка рядом — решение '
            'облика («↗» у ссылки на внешний сайт законна)', allowed)
    mono = [l for l in leaves if l['fs'] < 14 and family_kind(l['ff']) == 'mono' and not re.search(r'\d', l['text'])]
    if len(mono) >= 3:
        add(F, 'LOOK-MONO-LABELS', 'minor', desk['viewport'], f'моноширинные подписи без данных: {len(mono)} (m33)',
            {'examples': [l['text'][:30] for l in mono[:4]]}, 'малые подписи — гарнитурой текста; моно — только код и '
            'данные', allowed)
    numbered = [l for l in leaves if re.match(r'^\s*0[1-9](?:\b|[.·/—-])', l['text']) and len(l['text']) <= 24]
    if len(numbered) >= 3:
        add(F, 'LOOK-NUMBERED', 'minor', desk['viewport'], f'нумерация 01/02/03: {len(numbered)} (m31 — только для настоящей последовательности)',
            {'examples': [l['text'] for l in numbered[:4]]}, 'снять 01/02/03, если содержимое — не последовательность',
            allowed)
    if len(desk['glass']) > 2:
        add(F, 'LOOK-GLASS', 'minor', desk['viewport'], f"стекло (backdrop-filter): {len(desk['glass'])} эл. (> 2, m15)",
            {'examples': desk['glass'][:4]}, 'размытие фона — не больше одного слоя оверлея; поверхности сплошные', allowed)
    elif desk['glass']:
        add(F, 'LOOK-GLASS', 'info', desk['viewport'], f"стекло: {len(desk['glass'])} эл.", {'examples': desk['glass'][:2]})
    if desk['marquee']:
        add(F, 'LOOK-MARQUEE', 'minor', desk['viewport'], f"бегущая строка: {len(desk['marquee'])}", {'examples': desk['marquee'][:3]},
            'снять бегущую строку или сделать статичной; если остаётся — кнопка паузы (WCAG 2.2.2)', allowed)
    if desk['drawn_dots']:
        add(F, 'LOOK-DRAWN-CHROME', 'minor', desk['viewport'], f"нарисованный браузерный хром (три точки): {len(desk['drawn_dots'])}",
            {'examples': desk['drawn_dots'][:3]}, 'снять нарисованные рамки браузера и телефона; только настоящий кадр '
            'из ассетов', allowed)

    # ---------- шкала кеглей и шапка — пороги ui по поверхности, на каждой ширине
    fs_th = ui_thresholds().get('font_sizes') or {}
    for v in views:
        sizes = sorted({round(l['fs'] * 2) / 2 for l in v['leaves'] if l['text']})
        if fs_th.get('tell_above') and len(sizes) > fs_th['tell_above']:
            add(F, 'LOOK-TYPE-SCALE', 'minor', v['viewport'],
                f"кеглей на странице {len(sizes)} (> {fs_th['tell_above']}; норма {fs_th.get('norm')})",
                {'sizes': sizes, 'norm': fs_th.get('norm')}, 'шкала кеглей ДС: 6–8 кеглей, три несущих', allowed)
        hdr = v.get('header')
        if hdr:
            lim = header_limit(opts['surface'], opts['preset'], view_w(v), opts['first_bp'])
            if hdr['h'] > lim:
                add(F, 'LOOK-HEADER', 'minor', v['viewport'], f"шапка {hdr['h']:.0f} px (> {lim} px для "
                    + ('экрана приложения, пресет ' + opts['preset'] if opts['surface'] == 'app' else
                       'телефона' if view_w(v) < opts['first_bp'] else 'десктопа') + ')',
                    {'header': hdr['el'], 'h': hdr['h'], 'limit': lim, 'surface': opts['surface']},
                    f'высота шапки — не больше {lim} px (токен высоты шапки)', allowed)

    # ---------- контраст тёплых палитр
    bad = []
    for v in views:
        for l in v['leaves']:
            if l['bg_img'] or not l['text'] or l['color'][3] == 0:
                continue
            large = l['fs'] >= 24 or (l['fs'] >= 18.66 and l['fw'] >= 700)
            cr = contrast(l['color'], l['bg'])
            need = 3.0 if large else 4.5
            if cr < need and (warm_class(l['bg']) or warm_hue_text(l['color'])):
                bad.append({'view': v['viewport'], 'el': l['el'], 'text': l['text'][:30], 'ratio': cr, 'need': need,
                            'fg': hexs(l['color']), 'bg': hexs(l['bg'])})
    if bad:
        uniq_bad = {}
        for b in bad:
            uniq_bad.setdefault((b['el'], b['text'], b['ratio']), b)
        bad = sorted(uniq_bad.values(), key=lambda x: x['ratio'])
        add(F, 'LOOK-WARM-CONTRAST', 'major', bad[0]['view'],
            f"текст тёплой палитры ниже порога: {len(bad)} узл., худший {bad[0]['ratio']}:1 ({bad[0]['fg']} на {bad[0]['bg']})",
            {'worst': bad[:6]}, f"поднять контраст {bad[0]['el']} до ≥ {bad[0]['need']}:1 более тёмным токеном текста")

    # ---------- честность: сток и хотлинк
    stock, hot = [], []
    for v in views:
        srcs = [(im['src'], im['el']) for im in v['images']] + [(s, 'srcset') for im in v['images'] for s in re.split(r',\s*', im['srcset']) if s]
        srcs += [(u, b['el']) for b in v['bg_images'] for u in urls_in(b['value'])] + [(s, 'source') for s in v['media_src'] if s]
        for s, el in srcs:
            s = s.strip().split(' ')[0]
            if not s or s.startswith(('data:', 'blob:')):
                continue
            kind = stock_kind(s)
            host = urlparse(s).netloc
            if kind:
                stock.append({'kind': kind, 'url': s[:160], 'el': el, 'view': v['viewport']})
            elif host and host != target_host and not host.startswith('127.0.0.1'):
                hot.append({'url': s[:160], 'el': el})
    raw = (desk.get('html') or '') + '\n' + (desk.get('css') or '')
    for kind, rx in STOCK_PATTERNS:
        for m in re.finditer(rx, raw, re.I):
            stock.append({'kind': kind, 'url': m.group(0)[:160], 'el': 'html/css', 'view': desk['viewport']})
    for h in (static or {}).get('stock_hits', []):
        stock.append({'kind': h['kind'], 'url': h['url'], 'el': f"{h['file']}:{h['line']}", 'view': 'source'})
    uniq = {}
    for s in stock:
        uniq.setdefault(s['url'], s)
    unsplash = [s for s in uniq.values() if s['kind'] == 'unsplash']
    other = [s for s in uniq.values() if s['kind'] != 'unsplash']
    if unsplash:
        ids = sorted({re.sub(r'^.*?(photo-[0-9]+-[0-9a-f]+).*$', r'\1', s['url']) for s in unsplash})
        add(F, 'HON-UNSPLASH', 'critical', 'all', f'фото Unsplash по памяти (хотлинк): {len(unsplash)} адрес(ов)',
            {'ids': ids[:10], 'where': [s['el'] for s in unsplash[:6]]},
            'снять адреса Unsplash: только файлы из списка ассетов с подписями оттуда; пустой слот — заглушка «placeholder»')
    if other:
        add(F, 'HON-STOCK', 'critical', 'all', f"стоковые и заглушечные сервисы: {', '.join(sorted({s['kind'] for s in other}))}",
            {'urls': [s['url'] for s in other[:8]], 'where': [s['el'] for s in other[:6]]},
            'снять хотлинк стока и сервисов-заглушек: файлы из ассетов или локальная заглушка')
    hot_u = sorted({h['url'] for h in hot})
    if hot_u:
        add(F, 'HON-HOTLINK', 'major', 'all', f'внешние картинки (не сток): {len(hot_u)}', {'urls': hot_u[:8]},
            'утверждённые ассеты — локальными файлами (загрузки холста), без внешних адресов картинок', allowed)

    # ---------- подписи и alt против списка ассетов
    caps_all = []
    for im in desk['images']:
        if not im['visible']:
            continue
        stem = os.path.splitext(os.path.basename(urlparse(im['src']).path))[0].lower()
        if im['src'].startswith('data:'):
            continue
        caps_all.append({'el': im['el'], 'file': stem, 'src': im['src'][:160], 'blob': blob_id(im['src']),
                         'alt': im['alt'], 'caption': im['caption']})
    # постер и источники видео, источники <picture>, фоновые загрузки холста — те же файлы списка ассетов, без подписей
    media_all, seen = [], {c['src'] for c in caps_all}
    cand = [(m['el'], s, m['kind']) for m in desk.get('media') or [] if m.get('visible', True)
            for s in re.split(r',\s*', m.get('src') or '')]
    cand += [(b['el'], u, 'background') for b in desk['bg_images'] if b.get('visible', True)
             for u in urls_in(b['value']) if blob_id(u)]
    for el, s, kind in cand:
        s = s.strip().split(' ')[0]
        if not s or s.startswith(('data:', 'blob:')) or s[:160] in seen:
            continue
        seen.add(s[:160])
        media_all.append({'el': el, 'file': os.path.splitext(os.path.basename(urlparse(s).path))[0].lower(),
                          'src': s[:160], 'blob': blob_id(s), 'alt': None, 'caption': None, 'kind': kind})
    if assets is not None:
        shared, unverified = [], []
        for c in caps_all + media_all:
            if not c['file'] or stock_kind(c.get('src') or ''):
                continue
            row, status, up = asset_for(c, assets, opts.get('uploads'))
            if status == 'shared':
                shared.append(up['file'])
                continue
            if status == 'no-registry':
                unverified.append(c)
                continue
            if not row:
                blob = c['blob']
                what, of = MEDIA_RU.get(c.get('kind'), ('картинка', 'картинки'))
                msg, fix = {
                    'missing': (f"{of} «{c['file']}» нет в списке ассетов",
                                f"{what} {c['el']}: только файлы из списка ассетов"),
                    'unregistered': (f'загрузки {blob} нет в реестре загрузок',
                                     f"{what} {c['el']}: только загрузки из списка ассетов — строка «Загрузок» "
                                     'ARTIFACTS.md (id, файл, слот) или id загрузки в списке'),
                    'off-list': (f"загрузка {blob} — файл {(up or {}).get('file') or '?'}, слот "
                                 f"{(up or {}).get('slot') or '?'}: ни файла, ни слота нет в списке ассетов страницы",
                                 f"{what} {c['el']}: только файлы слотов плана ассетов страницы; общий ассет "
                                 'продукта — файл из design/_assets/'),
                }[status]
                add(F, 'HON-CAPTION', 'major', desk['viewport'], msg, {'img': c, 'upload': up}, fix)
                continue
            name = row['file'] or row['slot'] or c['file']
            if c['caption'] is not None and row['caption'] and norm_text(c['caption']) != norm_text(row['caption']):
                add(F, 'HON-CAPTION', 'critical', desk['viewport'], f"подпись не из списка ассетов: «{c['caption'][:60]}»",
                    {'expected': row['caption'], 'found': c['caption'], 'file': name},
                    f"подпись к {name} — дословно «{row['caption']}» (список ассетов)")
            if c['alt'] is not None and row['alt'] and norm_text(c['alt']) != norm_text(row['alt']):
                add(F, 'HON-CAPTION', 'major', desk['viewport'], f"alt не из списка ассетов: «{(c['alt'] or '')[:60]}»",
                    {'expected': row['alt'], 'found': c['alt'], 'file': name},
                    f"alt у {name} — дословно «{row['alt']}» (список ассетов)")
        if unverified:
            add(F, 'HON-CAPTION', 'minor', desk['viewport'],
                f'загрузок холста без реестра загрузок: {len(unverified)} — со списком ассетов не сверены',
                {'images': unverified[:8]}, 'реестр загрузок — ARTIFACTS.md продукта (--uploads, таблица «Загрузки») '
                'или колонка «id загрузки» списка ассетов')
        if shared:
            add(F, 'HON-CAPTION', 'info', desk['viewport'],
                f'общих ассетов продукта на странице: {len(shared)} (в список ассетов страницы не входят)',
                {'files': sorted(set(shared))[:12]})
    elif caps_all:
        sus = [c for c in caps_all if c['caption'] and re.search(r'\b(1[89]|20)\d{2}\b|[A-ZА-Я][a-zа-я]+,\s*[A-ZА-Я]', c['caption'])]
        add(F, 'HON-CAPTION', 'info', desk['viewport'], f'подписей и alt без списка ассетов для сверки: {len(caps_all)}'
            + (f'; с местом или датой (проверить глазами): {len(sus)}' if sus else ''), {'captions': caps_all[:8]})

    # ---------- числа против фактов и текстов: значение, единица и объект; строка факта без источника не легализует
    seen_nums, page_nums = set(), []
    for v in views:
        for l in v['leaves']:
            if '[PLACEHOLDER' in l['text'].upper() or re.fullmatch(r'\s*\d{1,2}\s*[.)]?\s*', l['text']):
                continue                           # заглушка; номер пункта или шага — не утверждение
            for c in number_claims(l['text']):
                if re.fullmatch(r'0\d', c['raw'].strip()):
                    continue                       # 01/02/03 — нумерация (LOOK-NUMBERED), не факт
                key = (c['value'], c['unit'], c['raw'])
                if key in seen_nums:
                    continue
                seen_nums.add(key)
                page_nums.append(dict(c, objs=sorted(c['objs']), el=l['el'], context=l['text'][:80]))
    copy_claims = number_claims(copy_text) if copy_text is not None else None
    demo = opts.get('demo')
    if facts is not None or copy_claims is not None or demo is not None:
        known = (facts or {}).get('known', []) + (copy_claims or [])
        demo_values = (demo or {}).get('values') or set()      # число записи демо-набора — с любой единицей и объектом
        unknown = [n for n in page_nums if not claim_known(dict(n, objs=set(n['objs'])), known)
                   and n['value'] not in demo_values]
        nosrc = (facts or {}).get('no_source') or []
        if unknown:
            add(F, 'HON-NUMBERS', 'critical', desk['viewport'],
                f"чисел нет в фактах и текстах{' и демо-наборе' if demo is not None else ''} (значение, единица, "
                f'объект): {len(unknown)}' + (f'; строк фактов без источника: {len(nosrc)}' if nosrc else ''),
                {'numbers': unknown[:12], 'facts_without_source': nosrc[:12]},
                'каждое число — из фактов с источником (та же единица, тот же объект)'
                + (' или из записей демо-набора' if demo is not None else '')
                + '; выдуманное — [PLACEHOLDER: что] и строка «Нет»: ' + ', '.join(n['raw'] for n in unknown[:6]))
        elif nosrc:
            add(F, 'HON-NUMBERS', 'info', desk['viewport'], f'строк фактов без источника: {len(nosrc)} (число они не легализуют)',
                {'facts_without_source': nosrc[:12]})
    elif page_nums:
        big = [n for n in page_nums if not re.fullmatch(r'\d', n['raw'])]
        if big:
            add(F, 'HON-NUMBERS', 'info', desk['viewport'], f'чисел на странице (нет фактов для сверки): {len(big)}',
                {'numbers': big[:12]})

    # ---------- текст против copy deck, заглушки, отзывы
    if copy_text is not None:
        from_copy = copy_matcher(copy_text, demo)
        cand = [b for b in desk['blocks'] if len(b['text'].split()) >= 3 and '[PLACEHOLDER' not in b['text'].upper()]
        miss = [b for b in cand if not from_copy(b['text'])]
        if cand and len(miss) / len(cand) > 0.10:
            add(F, 'HON-COPY', 'major', desk['viewport'],
                f"текст не из copy deck{' и демо-набора' if demo is not None else ''}: {len(miss)} из {len(cand)} блоков "
                f'({len(miss) / len(cand):.0%} > 10 %)',
                {'examples': [{'el': b['el'], 'text': b['text'][:90]} for b in miss[:10]]},
                'тексты — дословно из copy.md входа: не переписывать, не сокращать, не дописывать; пробел — '
                '[PLACEHOLDER: что]')
    filler = []
    alltext = ' \n'.join(b['text'] for b in desk['blocks'])
    for rx in FILLER_PATTERNS:
        for m in re.finditer(rx, alltext, re.I):
            filler.append(m.group(0))
    if filler:
        add(F, 'HON-FILLER', 'critical', desk['viewport'], f"текст-заглушка: {', '.join(sorted(set(filler))[:6])}",
            {'hits': sorted(set(filler))[:10]}, 'заменить «рыбу» текстом copy deck или [PLACEHOLDER: что]')
    quotes = [b for b in desk['blocks'] if b['quote'] and len(b['text'].split()) >= 5]
    if quotes:
        if copy_text is not None or facts is not None:
            src = norm_text(copy_text or '')
            unsourced = [q for q in quotes if norm_text(q['text']) not in src]
            if unsourced:
                add(F, 'HON-QUOTE', 'critical', desk['viewport'], f'отзыв или цитата без источника: {len(unsourced)}',
                    {'examples': [q['text'][:90] for q in unsourced[:4]]},
                    'снять отзывы, которых нет в copy deck и фактах')
        else:
            add(F, 'HON-QUOTE', 'info', desk['viewport'], f'отзывы и цитаты — проверить источник: {len(quotes)}',
                {'examples': [q['text'][:90] for q in quotes[:4]]})

    # ---------- формы по lead-forms.yaml
    check_forms(F, desk, opts.get('form_sets'), allowed, opts.get('surface', 'page'))

    # ---------- наложение текста
    ov = [dict(o, view=v['viewport']) for v in views for o in v.get('text_overlaps', [])]
    if ov:
        add(F, 'V-OVERLAP', 'major', ov[0]['view'], f"текст накладывается на текст: {len(ov)} пар(ы), напр. «{ov[0]['a']}» × «{ov[0]['b']}»",
            {'pairs': ov[:8]}, f"на {ov[0]['view']}: «{ov[0]['a']}» ({ov[0]['a_el']}) наезжает на «{ov[0]['b']}» "
            f"({ov[0]['b_el']}) около y={ov[0]['y']} px — развести (≥ 8 px), размеры не менять")

    # ---------- телефон: окна уже первого брейкпоинта
    for v in views:
        w = view_w(v)
        if w >= opts['first_bp']:
            continue
        nav_ok = any(n['links'] >= 2 for n in v['nav']['navs']) or any(t['top'] < v['vh'] * 0.3 for t in v['nav']['toggles'])
        part = opts.get('part') or 1
        if part > 1:
            add(F, 'M-NAV', 'info', v['viewport'], f'часть {part} артборда: шапка с навигацией — у первой части, '
                'здесь навигация не проверяется', {'part': part})
        elif not nav_ok:
            add(F, 'M-NAV', 'major', v['viewport'], 'навигация не видна (нет кнопки меню и нет ≥ 2 ссылок в nav или header)',
                {'navs': v['nav']['navs'][:3], 'toggles': v['nav']['toggles'][:3]},
                f"на {v['viewport']}: кнопка меню в шапке (≥ 44 × 44 px), открывающая разделы, или видимые ссылки; "
                'страница без меню по плану (посадочная, вход, «не найдено») — законна: ключ --allow no-nav', allowed)
        # тело — абзацы основного содержимого: строка реквизитов подвала или подпись шапки — не основной текст
        paras = [l for l in v['leaves'] if l.get('body', True) and l['tag'] in ('p', 'li', 'dd', 'blockquote')
                 and len(l['text'].split()) >= 8]
        if paras:
            small = [l for l in paras if l['fs'] < 16]
            med = statistics.median(l['fs'] for l in paras)
            if len(small) / len(paras) > 0.25:
                add(F, 'M-BODY-16', 'major', v['viewport'], f'тело текста < 16 px: {len(small)} из {len(paras)} абзацев, медиана {med:.1f} px',
                    {'examples': [{'el': l['el'], 'fs': l['fs']} for l in small[:5]]},
                    f"на {v['viewport']}: основной текст ≥ 16 px (интерлиньяж 1,4–1,6), десктоп не менять")
        if v['scroll_w'] > w + 1:
            add(F, 'M-OVERFLOW', 'critical', v['viewport'], f"горизонтальная прокрутка: {v['scroll_w'] - w} px",
                {'scroll_width': v['scroll_w']}, f"на {v['viewport']}: убрать горизонтальный вылет (элемент шире окна — "
                'overflow_elements кадров kit/shot.py)')
        hero_m = v.get('hero')
        if hero_m and hero_m['h1_lines'] > 4:
            add(F, 'M-H1-LINES', 'minor', v['viewport'], f"h1 занимает {hero_m['h1_lines']} строк (> 4)",
                {'lines': hero_m['h1_lines']}, f"на {v['viewport']}: H1 — не больше четырёх строк (кегль узкой ширины ДС)")

    for v in over:
        w = view_w(v)
        if v['scroll_w'] > w + 1:
            add(F, 'M-OVERFLOW', 'critical', v['viewport'], f"горизонтальная прокрутка на ширине вылета: {v['scroll_w'] - w} px",
                {'scroll_width': v['scroll_w']}, f"на {v['viewport']}: страница читается без прокрутки в двух измерениях "
                '(таблицы и карты — прокрутка в своём контейнере)')

    # ---------- слепая зона разметки: canvas и видео или почти пустой DOM
    if len(desk['leaves']) < 12 or desk.get('canvas_share', 0) > 0.5:
        add(F, 'E-LOW-DOM', 'minor', desk['viewport'],
            f"мало текста в DOM ({len(desk['leaves'])} узл.) или canvas и видео {desk.get('canvas_share', 0):.0%} первого экрана — "
            'проверки по разметке неполны, смотреть кадры глазами', {'leaves': len(desk['leaves']), 'canvas_share': desk.get('canvas_share')})

    # ---------- справочно: шрифты
    fam = {}
    for l in desk['leaves']:
        f = family_first(l['ff'])
        fam[f] = fam.get(f, 0) + 1
    add(F, 'I-FONTS', 'info', desk['viewport'], 'шрифты по числу текстовых узлов',
        {'families': dict(sorted(fam.items(), key=lambda x: -x[1])[:8]),
         'declared_in_source': dict(sorted(((static or {}).get('declared_fonts') or {}).items(), key=lambda x: -x[1])[:10])})
    if blocked:
        add(F, 'I-BLOCKED', 'info', 'all', f'внешних запросов заблокировано: {len(blocked)}', {'urls': blocked[:10]})
    return verdict(F, opts['surface'])


def domain_of(tell_id, surface):
    """Домен приметы для поверхности: владелец приметы (по поверхности, если их несколько) → домен реестра с тем же
    файлом-владельцем, иначе первый домен той же базы."""
    reg = registry()
    t = reg['tells'].get(tell_id) or {}
    own = t.get('owner')
    if isinstance(own, dict):
        own = own.get(surface) or next(iter(own.values()), '')
    path = re.split(r'[#\s]', str(own or ''))[0]
    for did, d in reg['domains'].items():
        if path and path == re.split(r'[#\s]', str(d.get('owner') or ''))[0]:
            return did
    base = path.split('/')[0]
    return next((did for did, d in reg['domains'].items() if str(d.get('owner') or '').split('/')[0] == base), None)


def ui_markers(tell_id):
    """Номера маркеров ui 11/04 приметы (владелец и соседи: «04-anti-slop-ui.md §… (маркер N)»)."""
    t = registry()['tells'].get(tell_id) or {}
    own = t.get('owner')
    refs = (list(own.values()) if isinstance(own, dict) else [own]) + list(t.get('also') or [])
    out = set()
    for r in refs:
        m = re.search(r'04-anti-slop-ui\.md[^()]*\(маркер(?:ы)?\s+([\d,\s]+)\)', str(r or ''))
        if m:
            out |= {int(x) for x in re.findall(r'\d+', m.group(1))}
    return out


def on_surface(f, surface):
    """Примета срабатывает только на поверхности своей записи реестра (`surface`); проверка без приметы — везде."""
    t = registry()['tells'].get(f.get('tell') or '') or {}
    return not t.get('surface') or surface in t['surface']


def off_surface(surface):
    """Проверки утилиты, чья примета на этой поверхности не ищется (поле отчёта off_surface)."""
    return sorted(k for k, v in registry()['checks'].items() if ':' not in k and not on_surface(v, surface))


def clusters_of(hit, surface):
    """Кластеры с приметами прогона (hit — приметы находок не info): [{id, name, unit, members_hit, members, min,
    formed, rule}]. Кластер реестра примет — от порога владельца (шаблонный хром — ui 11/04 §1.3), без числа у
    владельца — от двух («несколько примет» шапки реестра); кандидат `proposed` в вердикт не входит (min — None). На
    странице — кластеры реестра клише creative (`cluster_rule`); на экране приложения — маркеры домена app-visual
    (ui 11/04 §1.3)."""
    reg = registry()
    diag = ui_diagnosis()
    out = []

    def row(cid, name, unit, mem, members, n, rule):
        out.append({'id': cid, 'name': name, 'unit': unit, 'members_hit': mem, 'members': members, 'min': n,
                    'formed': bool(n) and len(mem) >= n, 'rule': rule})

    for c in reg['clusters']:
        mem = [m for m in c.get('members') or [] if m in hit]
        if mem:
            n = None if 'proposed' in str(c.get('rule') or '') else (diag['chrome'] if c['id'] == 'template-chrome' else 2)
            row(c['id'], c.get('name'), c.get('unit'), mem, len(c.get('members') or []), n, c.get('rule') or c.get('owner'))
    if surface == 'page':
        for c in _yaml(CLICHE).get('clusters') or []:
            mem = [m for m in c.get('members') or [] if m in hit]
            if mem:
                row(f"cliche:{c['id']}", c.get('name_ru'), 'сцена страницы', mem, len(c.get('members') or []),
                    cliche_cluster_min(), 'creative/08-uniqueness-anti-slop/cliche-registry.yaml#cluster_rule')
    if surface == 'app':
        dom = [t for t in reg['tells'] if domain_of(t, 'app') == 'app-visual']
        mem = sorted(t for t in hit if t in dom)
        if mem:
            row('domain:app-visual', 'маркеры экрана приложения', 'экран', mem, len(dom), diag['markers'],
                'ui/11-styles-trends/04-anti-slop-ui.md §1.3')
    return out


def verdict(F, surface):
    """Находки прогона → находки на поверхности с вердиктом шапки реестра: примета вида с ключом --allow — minor
    (одиночная: вопрос заказчику, было ли это решением) или major (член сложившегося кластера); примета без ключа
    (контраст, шкала кеглей, шапка) — уровень своей проверки."""
    F = [f for f in F if on_surface(f, surface)]
    hit = {f['tell'] for f in F if f.get('tell') and f['severity'] != 'info'}
    formed = {}
    for c in clusters_of(hit, surface):
        if c['formed']:
            for t in c['members_hit']:
                formed.setdefault(t, c)
    checks = registry()['checks']
    for f in F:
        if f.get('group') != 'look' or f['severity'] not in ('major', 'minor') or not checks.get(f['id'], {}).get('allow'):
            continue
        c = formed.get(f['tell'])
        if c:
            f['severity'], f['cluster'] = 'major', c['id']
            f['message'] += f" — кластер {c['id']} ({len(c['members_hit'])} примет: {', '.join(c['members_hit'][:6])})"
        else:
            f['severity'] = 'minor'
            f['message'] += ' — одиночная примета: вопрос заказчику, было ли это решением'
    return F


def summarize(F, allowed, surface='page'):
    """Сводка без дублей: примета — один раз, сколько бы проверок её ни нашли; счёт — по доменам реестра в единице
    домена (страница или экран одного прогона), домены не складываются; кластеры реестра и реестра клише — членами,
    порогом владельца и признаком «сложился» (clusters_of); clusters_formed — сложившиеся кластеры (код 1)."""
    reg = registry()
    counts = {s_: 0 for s_ in SEV_ORDER}
    for f in F:
        counts[f['severity']] += 1
    hit = {}
    for f in F:
        if not f.get('tell') or f['severity'] == 'info':
            continue
        h = hit.setdefault(f['tell'], {'tell': f['tell'], 'checks': [], 'severity': f['severity'], 'group': f.get('group')})
        if f['id'] not in h['checks']:
            h['checks'].append(f['id'])
        if SEV_ORDER[f['severity']] < SEV_ORDER[h['severity']]:
            h['severity'] = f['severity']
    tells = []
    for t, h in sorted(hit.items()):
        tells.append(dict(h, domain=domain_of(t, surface)))
    domains = {}
    for row in tells:
        did = row['domain'] or '—'
        d = reg['domains'].get(did) or {}
        dom = domains.setdefault(did, {'unit': d.get('unit'), 'owner': d.get('owner'), 'diagnosis': d.get('diagnosis'),
                                       'tells': []})
        dom['tells'].append(row['tell'])
    for did, dom in domains.items():
        dom['count'] = len(dom['tells'])
        if did == 'app-visual':
            dom['ui_markers'] = sorted(set().union(*(ui_markers(t) for t in dom['tells'])))
    clusters = clusters_of(set(hit), surface)
    groups = {}
    for f in F:
        if f['severity'] in ('critical', 'major') and f.get('group'):
            groups.setdefault(f['group'], [])
            if f['id'] not in groups[f['group']]:
                groups[f['group']].append(f['id'])
    return {'counts': counts, 'tells': tells, 'domains': domains, 'clusters': clusters,
            'clusters_formed': [c['id'] for c in clusters if c['formed']],
            'groups': {g: sorted(v) for g, v in sorted(groups.items())},
            'acceptance_hint': {g: not groups.get(g) for g in ('look', 'honesty', 'acceptance')},
            'allowed_by_brief': sorted(allowed),
            'allowed': [{k: f.get(k) for k in ('id', 'allow', 'base_severity', 'view', 'reason')}
                        for f in F if f.get('allowed')]}


def exit_code(summary):
    """Код прогона: 1 — есть critical или сложился кластер примет, иначе 0."""
    return 1 if summary['counts']['critical'] or summary['clusters_formed'] else 0


def to_md(res):
    s = res['summary']
    doms = '; '.join(f"{d} ({v.get('unit') or '—'}): {', '.join(v['tells'])}" for d, v in s['domains'].items()) or '—'
    cl = '; '.join(f"{c['id']} {len(c['members_hit'])} из {c['members']}"
                   + (f" (порог {c['min']}{' — сложился' if c['formed'] else ''})" if c.get('min') else ' (вне вердикта)')
                   for c in s['clusters']) or '—'
    L = [f"# mockup_checks · {res['target']} · {res['created']}", '',
         f"Итог: critical {s['counts']['critical']} · major {s['counts']['major']} · minor {s['counts']['minor']} · "
         f"info {s['counts']['info']}. Приметы по доменам (единица домена; домены не складываются): {doms}. "
         f"Кластеры (члены; порог — владелец; одиночная примета — вопрос заказчику): {cl}.", '',
         '| Проверка | Примета | Тяжесть | Вид | Найдено | Правка |', '|---|---|---|---|---|---|']
    for f in sorted(res['findings'], key=lambda x: (SEV_ORDER[x['severity']], x['id'])):
        if f['severity'] == 'info':
            continue
        L.append(f"| {f['id']} | {f.get('tell') or '—'} | {f['severity']} | {f['view']} | {f['message'].replace('|', '/')} | "
                 f"{f['fix'].replace('|', '/')} |")
    lifted = [f for f in res['findings'] if f.get('allowed')]
    if lifted:
        L += ['', 'Снято решением (тяжесть без ключа): '
              + '; '.join(f"{f['id']} — {f['base_severity']}, {f['view']}, {f['reason']}" for f in lifted) + '.']
    return '\n'.join(L) + '\n'


def static_copy(target):
    """Статичная копия артборда (строка происхождения dc_to_html) → {artboard — имя исходника, w, h — рамка}; другая
    цель — None."""
    if target.startswith(('http://', 'https://')) or not os.path.isfile(target):
        return None
    head = open(target, encoding='utf-8', errors='replace').read(4000)
    m = re.search(r'<!--\s*dc_to_html:\s*статичная копия артборда ([^;]+);.*?рамка (\d+)×(\d+)', head)
    return {'artboard': m.group(1).strip(), 'w': int(m.group(2)), 'h': int(m.group(3))} if m else None


def input_surface(target):
    """Поверхность проверки по манифесту входа холста: статичная копия лежит в `design/<surface>/canvas/html/`, манифест
    — `design/<surface>/input/INPUT.md`; `route: app` его передней части — экран приложения (`app`), другой маршрут —
    страница сайта (`page`). Цель вне папки копий или манифеста с маршрутом нет — None."""
    if target.startswith(('http://', 'https://', 'file://')):
        return None
    import docpaths
    d = os.path.abspath(target if os.path.isdir(target) else os.path.dirname(os.path.abspath(target)))
    html = docpaths.DESIGN_SURFACE['canvas-html'].split('/')
    if d.split(os.sep)[-len(html):] != html:
        return None
    man = os.path.join(d, *['..'] * len(html), docpaths.DESIGN_SURFACE['input'], INPUT_MANIFEST)
    try:
        head = open(man, encoding='utf-8').read(4000)
    except OSError:
        return None
    fm = re.match(r'---\r?\n(.*?)\r?\n---', head, re.S)
    m = re.search(r'^route:\s*["\']?([\w-]+)', fm.group(1), re.M) if fm else None
    return None if not m else ('app' if m.group(1) == 'app' else 'page')


def static_frame(target):
    """Ширина рамки, если цель — статичная копия артборда: такая копия — страница фиксированной ширины и проверяется
    окном своей рамки; другие ширины — свои артборды холста и их копии."""
    c = static_copy(target)
    return c['w'] if c else None


def artboard_part(name, width):
    """Имя артборда или его копии → (имя без номера части, номер части). Страница длиннее предела высоты артборда
    лежит на холсте частями `<Имя>-<ширина>-<N>`, N с единицы; ширина в имени равна ширине рамки — так номер части не
    путается с числом в имени страницы (`Flat-204-1440` — артборд целиком). Артборд целиком — (имя, None)."""
    stem = re.sub(r'(?:\.dc)?\.html?$', '', os.path.basename(str(name or '')))
    m = re.fullmatch(r'(.+-(\d+))-(\d+)', stem)
    if m and width and int(m.group(2)) == int(width) and int(m.group(3)) >= 1:
        return m.group(1), int(m.group(3))
    return stem, None


def cmd_page(a):
    allowed = {x.strip() for x in (a.allow or '').split(',') if x.strip()}
    keys = allow_keys()
    unknown = allowed - keys
    if unknown:
        raise SystemExit(f'неизвестные ключи --allow: {sorted(unknown)}; допустимые: {sorted(keys)}')
    fg = free_gb()
    if fg is not None and fg < a.min_free_gb:
        print(json.dumps({'error': f'свободно {fg:.1f} ГБ < {a.min_free_gb} ГБ — браузер не запускаю'}, ensure_ascii=False))
        return 3
    first_bp = first_breakpoint(a.tokens)
    aw = acceptance_widths()
    by_input = None if a.surface else input_surface(a.target)
    surface = a.surface or by_input or 'page'
    copy = static_copy(a.target)
    frame = copy['w'] if copy else None
    part = artboard_part(copy['artboard'], frame)[1] if copy else None
    if a.views:
        specs = [v.strip() for v in a.views.split(',') if v.strip()]
    elif frame:
        specs = [f'{frame}x{VIEW_H_WIDE if frame >= first_bp else VIEW_H_NARROW}']
    else:
        specs = [f'{w}x{VIEW_H_WIDE if w >= first_bp else VIEW_H_NARROW}'
                 for w in (aw['widths'] if a.acceptance else aw['artboards'])]
    over = f"{aw['overflow_only']}x{VIEW_H_NARROW}" if a.acceptance and aw['overflow_only'] and not frame else None
    local = not a.target.startswith(('http://', 'https://'))
    block = a.block_external or (local and not a.allow_external)
    src = a.src or (os.path.dirname(os.path.abspath(a.target)) if local and os.path.isfile(a.target)
                    else (os.path.abspath(a.target) if local else None))
    static = scan_sources(src) if src else None
    facts = load_facts(a.facts)
    copy_text = load_copy(a.copy, a.page)
    demo = load_demo(a.demo)
    assets = parse_assets_readme(a.assets)
    uploads_file = a.uploads or (find_uploads(a.assets) if a.assets else None)
    uploads = load_uploads(uploads_file)
    form_sets = load_form_sets(a.forms)
    t0 = time.time()
    url, views, blocked = collect(a.target, specs + ([over] if over else []), a.ignore_selector, block, a.shots,
                                  os.path.splitext(os.path.basename(a.target))[0] if copy else None)
    if over:
        views[-1]['overflow_only'] = True
    opts = {'surface': surface, 'preset': a.preset, 'first_bp': first_bp, 'form_sets': form_sets,
            'ds': ds_look(a.tokens), 'demo': demo, 'uploads': uploads, 'part': part}
    F = analyze(url, views, static, facts, copy_text, assets, allowed, blocked, opts)
    res = {'tool': 'mockup_checks.py', 'version': VERSION, 'target': a.target, 'url': url, 'static_frame': frame,
           'artboard': copy and copy['artboard'], 'part': part,
           'created': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'seconds': round(time.time() - t0, 1),
           'surface': surface, 'first_breakpoint': first_bp,
           'surface_source': '--surface' if a.surface else ('манифест входа холста' if by_input else 'умолчание'),
           'views': [v['viewport'] for v in views],
           'widths': '--views' if a.views else ('рамка статичной копии' if frame else 'kb/common/acceptance-widths.yaml'),
           'off_surface': off_surface(surface),
           'inputs': {'facts': a.facts, 'copy': a.copy, 'demo': a.demo, 'assets': a.assets, 'uploads': uploads_file,
                      'forms': form_sets, 'tokens': a.tokens, 'src': (static or {}).get('root'),
                      'block_external': block},
           'static': {k: v for k, v in (static or {}).items() if k != 'stock_hits'} if static else None,
           'shots': [v.get('shot') for v in views if v.get('shot')],
           'summary': summarize(F, allowed, surface),
           'findings': sorted(F, key=lambda x: (SEV_ORDER[x['severity']], x['id']))}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        open(a.json, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
    if a.md:
        os.makedirs(os.path.dirname(os.path.abspath(a.md)), exist_ok=True)
        open(a.md, 'w', encoding='utf-8').write(to_md(res))
    s = res['summary']
    print(json.dumps({'target': a.target, 'seconds': res['seconds'], 'summary': {k: s[k] for k in ('counts', 'groups',
                      'clusters_formed', 'acceptance_hint')}, 'tells': [t['tell'] for t in s['tells']],
                      'top': [f"{f['severity']} {f['id']}: {f['message']}" for f in res['findings'] if f['severity'] != 'info'][:14]},
                     ensure_ascii=False, indent=1))
    return exit_code(s)


# ---------------------------------------------------------------- ресайз без перезагрузки (пункт H5 приёмки)
def resize_windows():
    """Окна ресайза по умолчанию: широкое — самая широкая ширина приёмки, узкое — самая широкая ниже первого брейкпоинта
    эталона ui (окна первого экрана site 1440×900 и 390×844)."""
    aw = acceptance_widths()
    bp = first_breakpoint()
    narrow = [w for w in aw['widths'] if w < bp]
    return f"{aw['widths'][0]}x{VIEW_H_WIDE}", f"{max(narrow) if narrow else aw['widths'][-1]}x{VIEW_H_NARROW}"


RESIZE_JS = r"""
() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity || '1') > 0.1; };
  const vw = document.documentElement.clientWidth;
  const media = Array.from(document.querySelectorAll('video, img, canvas')).filter(m => { const r = m.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0 && r.width * r.height > vw * innerHeight * 0.15; });
  const mstate = media.slice(0, 4).map(m => ({tag: m.tagName.toLowerCase(), visible: vis(m),
    ready: m.tagName === 'VIDEO' ? m.readyState >= 2 : (m.tagName === 'IMG' ? (m.complete && m.naturalWidth > 0) : true),
    src: (m.currentSrc || m.src || '').slice(-60)}));
  const navLinks = Array.from(document.querySelectorAll('nav a[href], header a[href], nav button, header button')).filter(vis).length;
  const sw = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0);
  return {vw, overflow_px: Math.max(0, sw - vw), nav_controls: navLinks, media: mstate};
}
"""


def cmd_resize(a):
    fg = free_gb()
    if fg is not None and fg < a.min_free_gb:
        print(json.dumps(resize_report(a.target, verdict='error', error=f'свободно {fg:.1f} ГБ < {a.min_free_gb} ГБ — '
                                       'браузер не запускаю'), ensure_ascii=False, indent=1))
        return 3
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageChops, ImageStat
    import io
    target = a.target
    httpd = None
    if not target.startswith(('http://', 'https://')):
        import functools, http.server, socketserver, threading
        path = os.path.abspath(target)
        root, name = (path, '') if os.path.isdir(path) else (os.path.dirname(path), os.path.basename(path))
        safe_root(root)

        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *x):
                pass
        httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=root))
        httpd.daemon_threads = True
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        target = f'http://127.0.0.1:{httpd.server_address[1]}/{name}'
    big = [int(x) for x in a.desktop.split('x')]
    small = [int(x) for x in a.mobile.split('x')]
    steps, shots = [], []
    try:
        with kbpaths.lock('browser'), sync_playwright() as p:
            b = p.chromium.launch()
            try:
                page = b.new_page(viewport={'width': big[0], 'height': big[1]})
                try:
                    page.goto(target, wait_until='networkidle', timeout=60000)
                except Exception:  # noqa: BLE001
                    pass
                page.wait_for_timeout(800)
                for label, (w, h) in (('desktop-before', big), ('mobile-after-resize', small), ('desktop-after-resize', big)):
                    if label != 'desktop-before':
                        page.set_viewport_size({'width': w, 'height': h})
                        page.wait_for_timeout(a.wait_ms)
                    st = page.evaluate(RESIZE_JS)
                    st['step'] = label
                    try:
                        png = page.screenshot(type='png', animations='disabled', timeout=15000)
                        shots.append(Image.open(io.BytesIO(png)).convert('RGB'))
                        if a.shots:
                            os.makedirs(a.shots, exist_ok=True)
                            shots[-1].save(os.path.join(a.shots, f'resize-{label}.jpg'), 'JPEG', quality=80)
                    except Exception as e:  # noqa: BLE001
                        st['shot_error'] = str(e)[:120]
                        shots.append(None)
                    steps.append(st)
            finally:
                b.close()
    finally:
        if httpd:
            httpd.shutdown(); httpd.server_close()
    problems = []
    for st in steps:
        if st['overflow_px'] > 0:
            problems.append(f"{st['step']}: горизонтальный вылет {st['overflow_px']} px")
        for m in st['media']:
            if not m['visible'] or not m['ready']:
                problems.append(f"{st['step']}: медиа первого экрана не показано через {a.wait_ms} мс ({m['tag']} {m['src']})")
    if steps and steps[1]['nav_controls'] == 0:
        problems.append('mobile-after-resize: навигация не видна после ресайза')
    diff = None
    if shots and shots[0] is not None and shots[-1] is not None and shots[0].size == shots[-1].size:
        diff = round(sum(ImageStat.Stat(ImageChops.difference(shots[0], shots[-1])).mean) / 3 / 255, 4)
        if diff > a.max_diff:
            problems.append(f'после возврата на {a.desktop} кадр отличается от исходного (средняя разница {diff} > {a.max_diff})')
    res = resize_report(a.target, wait_ms=a.wait_ms, steps=steps, desktop_restore_diff=diff, problems=problems,
                        verdict='fail' if problems else 'pass')
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 1 if problems else 0


def resize_report(target, **fields):
    """JSON подкоманды resize: какая утилита ответила и версия контракта скилла (tool, skill_version, command), цель и
    поля прогона; verdict — pass · fail, error — проверка не шла (причина — поле error)."""
    return {'tool': 'mockup_checks.py', 'skill_version': kbpaths.skill_version(), 'command': 'resize', 'target': target,
            **fields}


# ---------------------------------------------------------------- самопроверка
def _view(w=1440, vh=900, **kw):
    """Кадр COLLECT_JS для синтетики самопроверки."""
    base = {'viewport': f'{w}x{vh}', 'vw': w, 'vh': vh, 'headings': [], 'leaves': [], 'text_overlaps': [], 'blocks': [],
            'images': [], 'bg_images': [], 'media_src': [], 'sections': [], 'canvas_share': 0, 'page_bg': [255, 255, 255],
            'page_h': 3000, 'scroll_w': w, 'hero': None, 'rows': [], 'bento': [], 'orbit': [], 'header': None, 'forms': [],
            'glass': [], 'grad_text': [], 'marquee': [], 'drawn_dots': [], 'nav': {'navs': [{'el': 'nav', 'links': 4}], 'toggles': []}}
    base.update(kw)
    return base


def _leaf(text, fs=16, tag='p', **kw):
    base = {'el': tag, 'tag': tag, 'text': text, 'fs': fs, 'fw': 400, 'ff': 'Inter', 'tt': 'none', 'ls': 0,
            'color': [17, 21, 28, 1], 'bg': [255, 255, 255], 'bg_img': False, 'in_btn': False, 'ext': False, 'body': True}
    base.update(kw)
    return base


def _img(src, alt=None, caption=None):
    return {'el': 'img', 'src': src, 'srcset': '', 'alt': alt, 'w': 320, 'h': 240, 'visible': True, 'caption': caption}


def _field(label, type_='text', **kw):
    base = {'tag': 'input', 'type': type_, 'name': '', 'id': '', 'autocomplete': '', 'required': False, 'checked': False,
            'label': label, 'placeholder': '', 'visible': True, 'hidden_trap': False}
    base.update(kw)
    return base


def cmd_selftest(_a):
    import tempfile
    ok = True

    def check(name, cond, got=None):
        nonlocal ok
        ok &= bool(cond)
        print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else f' → {got}'))

    def ids(F, sev=None):
        return sorted({f['id'] for f in F if sev is None or f['severity'] in sev})

    opts = {'surface': 'page', 'preset': 'A', 'first_bp': 640.0, 'form_sets': []}
    L, C, H = oklch((0xF4, 0xF1, 0xEA))
    check('oklch #F4F1EA ≈ (0.957, 0.010, 84)', abs(L - 0.957) < 0.01 and abs(C - 0.010) < 0.004 and 70 < H < 95, (L, C, H))
    check('warm light #F4F1EA', warm_class((0xF4, 0xF1, 0xEA)) == 'light')
    check('warm light #f4f4ec', warm_class((0xf4, 0xf4, 0xec)) == 'light', oklch((0xf4, 0xf4, 0xec)))
    check('warm dark #14140c', warm_class((0x14, 0x14, 0x0c)) == 'dark', oklch((0x14, 0x14, 0x0c)))
    check('neutral #fafafa not warm', warm_class((0xfa, 0xfa, 0xfa)) is None)
    check('cool #f4f6fb not warm', warm_class((0xf4, 0xf6, 0xfb)) is None, oklch((0xf4, 0xf6, 0xfb)))
    check('brand orange #e4002b not tint', warm_class((0xe4, 0x00, 0x2b)) is None)
    check('contrast #9ca3af/#fff = 2.54', contrast((0x9c, 0xa3, 0xaf), (255, 255, 255)) == 2.54, contrast((0x9c, 0xa3, 0xaf), (255, 255, 255)))
    check('contrast white on #6366f1 = 4.47', contrast((255, 255, 255), (0x63, 0x66, 0xf1)) == 4.47)
    nums = dict((r, v) for r, v in extract_numbers('Более 12 000+ клиентов, рейтинг 4,9 и 98 % довольных; с 2014 года; $1,250'))
    check('numbers 12 000+ → 12000', nums.get('12 000+') == '12000', nums)
    check('numbers 4,9 → 4.9', nums.get('4,9') == '4.9', nums)
    check('norm_text quotes/dashes', norm_text('«Смена — за 5 минут»') == norm_text('"смена - за 5 минут"'))
    check('family_kind Fraunces serif', family_kind('"Fraunces", Georgia, serif') == 'serif')
    check('family_kind JetBrains mono', family_kind('"JetBrains Mono", monospace') == 'mono')
    check('stock unsplash id', stock_kind('https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1600') == 'unsplash')

    # реестр примет, ширины и пороги владельцев
    reg = registry()
    check('реестр: LOOK-EYEBROW → примета caps-eyebrow', reg['checks'].get('LOOK-EYEBROW', {}).get('tell') == 'caps-eyebrow')
    check('ключи --allow — из реестра', {'warm', 'eyebrow', 'cards', 'arrows', 'external'} <= allow_keys(), sorted(allow_keys()))
    aw = acceptance_widths()
    check('ширины приёмки из файла: артборды — все ширины приёмки, вылет 320',
          (aw['artboards'], aw['overflow_only']) == (aw['widths'], 320) and len(aw['widths']) == 6, aw)
    check('ресайз по умолчанию: 1440x900 → 390x844', resize_windows() == ('1440x900', '390x844'), resize_windows())
    import contextlib
    import io
    real_free, buf = free_gb, io.StringIO()
    globals()['free_gb'] = lambda: 0.0
    try:
        with contextlib.redirect_stdout(buf):
            rc = cmd_resize(argparse.Namespace(target='https://example.test/', min_free_gb=2.0))
    finally:
        globals()['free_gb'] = real_free
    rr, ok_rep = json.loads(buf.getvalue()), resize_report('https://example.test/', verdict='pass', problems=[])
    check('resize, JSON для кода: tool, skill_version — версия скилла, command; мало памяти — код 3, verdict error с '
          'причиной в error',
          rc == 3 and rr['tool'] == ok_rep['tool'] == 'mockup_checks.py' and rr['command'] == 'resize'
          and rr['skill_version'] == ok_rep['skill_version'] == kbpaths.skill_version() and rr['verdict'] == 'error'
          and 'ГБ' in rr['error'] and ok_rep['verdict'] == 'pass' and 'error' not in ok_rep, rr)
    check('первый брейкпоинт без токенов ДС — эталон ui 640', first_breakpoint() == 640.0, first_breakpoint())
    check('шапка страницы: телефон 64, десктоп 80', (header_limit('page', 'A', 390, 640), header_limit('page', 'A', 1440, 640)) == (64, 80))
    check('шапка приложения по пресету: A 48, B 64', (header_limit('app', 'A', 1440, 640), header_limit('app', 'B', 390, 640)) == (48, 64))
    check('надзаголовок: N у владельца COPY-C-18 = 3', eyebrow_per_sections() == 3, eyebrow_per_sections())
    check('порог высоты hero — AIL-06: 0.95', hero_height_share() == 0.95, hero_height_share())
    check('вариация длины карточек — AIL-07: 0.2', cards_cv_max() == 0.2, cards_cv_max())
    check('бенто и орбита — пороги реестра клише: 5 и 6', (bento_min_tiles(), orbit_min_icons()) == (5, 6), (bento_min_tiles(), orbit_min_icons()))

    # числа: значение, единица, объект
    fact = number_claims('1 146 квартир сдали с 2014 года; гарантия 3 года по договору; перезвоним: +7 (831) 555-12-34')
    check('телефон — одно утверждение', any(c['unit'] == 'tel' and c['value'] == 'tel:8315551234' for c in fact), fact)
    check('«3 года» — единица «год», объект «гарантия»', any(c['value'] == '3' and c['unit'] == 'год' and 'гаран' in c['objs'] for c in fact), fact)
    known = fact
    same = number_claims('Гарантия 3 года')[0]
    other_unit = number_claims('Гарантия 3 дня')[0]
    other_obj = number_claims('3 года на рынке')[0]
    check('число, единица и объект совпали — легально', claim_known(same, known))
    check('та же цифра с другой единицей — выдумка', not claim_known(other_unit, known))
    check('та же цифра и единица о другом объекте — выдумка', not claim_known(other_obj, known), other_obj)
    check('время 10:00 — не утверждение', number_claims('Запись на 10:00') == [], number_claims('Запись на 10:00'))

    with tempfile.TemporaryDirectory() as td:
        fmd = os.path.join(td, 'facts.md')
        open(fmd, 'w', encoding='utf-8').write(
            '# Факты — пример\n\n## Факты\n\n| id | дословно | источник | где можно |\n|---|---|---|---|\n'
            '| guarantee | Гарантия 3 года на работы | договор, п. 7.2 / 2026-09-01 | везде |\n'
            '| flats | 1 146 квартир | — | hero |\n\n## Нет\n\n| id | чего нет | на странице до ответа | кто даст |\n'
            '|---|---|---|---|\n| price | цена 3 500 ₽ | [PLACEHOLDER: цена] | заказчик |\n')
        fx = load_facts(fmd)
        check('facts.md входа: строка без источника не легализует', fx['no_source'] == ['flats'] and fx['rows'] == 2, fx)
        check('facts.md: строки «Нет» — не факты', not any(c['value'] == '3500' for c in fx['known']), fx['known'])
        fy = load_facts(str(kbpaths.kb('text', '02-strategy-messaging', 'examples', 'facts-service-renovation.yaml')))
        check('facts.yaml: числа фактов с источником', any(c['value'] == '1146' for c in fy['known']) and fy['rows'] > 5, fy['rows'])
        cmd = os.path.join(td, 'copy.md')
        open(cmd, 'w', encoding='utf-8').write('# Тексты\n\n## hero\n[h1] approved: Ремонт под ключ с 2014 года\n'
                                               '[text]: Первая строка\n  Вторая строка\n')
        check('copy.md: строки слотов и продолжения', load_copy(cmd) == 'Ремонт под ключ с 2014 года\nПервая строка\nВторая строка',
              load_copy(cmd))
        tp = os.path.join(td, 'copy-app.md')
        open(tp, 'w', encoding='utf-8').write('# Тексты интерфейса\n\n| ключ | роль | текст | maxlen | статус |\n'
                                              '|---|---|---|---|---|\n'
                                              '| `a.list.empty` | empty | По запросу «{query}» заявок нет | 80 | approved |\n'
                                              '| `a.list.create` | action | Создать заявку | 24 | approved |\n')
        check('copy.md кабинета: таблица — тексты колонки «текст»',
              load_copy(tp) == 'По запросу «{query}» заявок нет\nСоздать заявку', load_copy(tp))
        mt = copy_matcher(load_copy(tp))
        check('подстановка {query} — шаблон: «По запросу «кухня» заявок нет» из copy deck, «Заявок нет вообще» — нет',
              mt('По запросу «кухня» заявок нет') and not mt('Заявок нет вообще'))
        deck = str(kbpaths.kb('text', '10-templates-recipes', 'examples', 'ru-otves-lead.yaml'))
        check('copy deck YAML: выбранные тексты страницы', 'Позвать замерщика' in (load_copy(deck, 'otves-product-aware') or ''))
        ay = os.path.join(td, 'plan.yaml')
        open(ay, 'w', encoding='utf-8').write('slots:\n  - {slot: hero, file: assets/hero-01.avif, alt: Прихожая после ремонта}\n')
        ya = parse_assets_readme(ay)
        check('ассеты из YAML: file, слот и alt', {k: ya['by_stem'].get('hero-01', {}).get(k) for k in ('file', 'slot', 'caption', 'alt')}
              == {'file': 'assets/hero-01.avif', 'slot': 'hero', 'caption': '', 'alt': 'Прихожая после ремонта'}, ya)
        F = analyze('http://x/', [_view(images=[_img('http://x/assets/hero-01.avif', 'Прихожая после ремонта'),
                                                _img('http://x/assets/sofa.jpg', 'Диван')])], None, None, None, ya, set(), [], opts)
        check('картинка с именем файла: из списка — молчит, вне списка — HON-CAPTION major',
              [(f['severity'], f['message']) for f in F if f['id'] == 'HON-CAPTION'] == [('major', 'картинки «sofa» нет в списке ассетов')],
              [(f['severity'], f['message']) for f in F if f['id'] == 'HON-CAPTION'])

        # загрузка холста /_blob/<id>: id загрузки списка ассетов, затем «Загрузки» ARTIFACTS.md — файл или слот
        bid = {k: (k * 4 + k.upper() * 4) * 4 for k in 'abcdef'}
        am = os.path.join(td, 'design', 'web', 'input', 'pages', 'home', 'assets.md')
        os.makedirs(os.path.dirname(am))
        open(am, 'w', encoding='utf-8').write(
            '# Ассеты страницы home, этап mockup\n\n'
            '| файл | слот | роль | подпись | alt | фокус | варианты | источник и лицензия | id загрузки |\n'
            '|---|---|---|---|---|---|---|---|---|\n'
            '| `hero-01.avif` | `hero-visual` (hero · hero-visual) | informational | — | Прихожая после ремонта | — | desktop 16:9 | real | — |\n'
            f'| `icon-ruler.svg` | `steps-1-icon` (steps · icon) | decorative | — | alt="" | — | default 1:1 | code | {bid["a"]} |\n'
            '| placeholder · TODO | `team-1-photo` (team · photo) | informational | Прораб на объекте | — | — | desktop 4:5 | real | — |\n')
        art = os.path.join(td, 'design', 'ARTIFACTS.md')
        open(art, 'w', encoding='utf-8').write(
            '# ARTIFACTS\n\n## Загрузки\n\n| id | файл | sha256 | слот | артефакт |\n|---|---|---|---|---|\n'
            f'| `{bid["b"]}` | `design/web/assets/hero-01.avif` | | `hero-visual` | `canvas:web` |\n'
            f'| `{bid["c"]}` | `$DDD_HOME/out/demo/team-1-demo.webp` | | `team-1-photo` | `canvas:web` |\n'
            f'| `{bid["d"]}` | `design/_assets/brand/logo.svg` | | `logo` | `canvas:web` |\n'
            f'| `{bid["e"]}` | `design/web/assets/cases-1-cover.avif` | | `cases-1-cover` | `canvas:web` |\n')
        A, U = parse_assets_readme(am), load_uploads(find_uploads(am))
        check('assets.md входа: строки по файлу, слоту и id загрузки; пустой слот — по слоту; прочерк и alt="" — пусто',
              (sorted(A['by_stem']), sorted(A['by_slot']), list(A['by_upload']), A['by_slot']['steps-1-icon']['alt'],
               A['by_slot']['hero-visual']['caption'], A['by_slot']['team-1-photo']['file']) ==
              (['hero-01', 'icon-ruler', 'placeholder'], ['hero-visual', 'steps-1-icon', 'team-1-photo'], [bid['a']], '', '', ''),
              A)
        check('реестр загрузок — «Загрузки» ARTIFACTS.md в папке выше списка: id → файл, слот, артефакт',
              (find_uploads(am), len(U), U[bid['e']]) == (art, 4, {'file': 'design/web/assets/cases-1-cover.avif',
                                                                   'slot': 'cases-1-cover', 'artifact': 'canvas:web'}), U)
        blob = lambda k: f'http://127.0.0.1:8000/_blob/{bid[k]}'   # noqa: E731
        st = [asset_for({'file': bid[k], 'src': blob(k)}, A, U)[1] for k in 'abcdef']
        check('кадр /_blob/<id>: по id списка, по файлу и по слоту реестра — строка; _assets/ — общий ассет; файл и '
              'слот вне списка; id вне реестра', st == ['row', 'row', 'row', 'shared', 'off-list', 'unregistered'], st)
        imgs = [_img(blob('a'), ''), _img(blob('b'), 'Прихожая после ремонта'), _img(blob('c'), '', 'Прораб на объекте'),
                _img(blob('d'), 'Логотип')]
        F = analyze('http://x/', [_view(images=imgs)], None, None, None, A, set(), [], dict(opts, uploads=U))
        hc = [(f['severity'], f['message']) for f in F if f['id'] == 'HON-CAPTION']
        check('кадры из реестра загрузок с alt и подписью списка — HON-CAPTION молчит, общий ассет — справкой',
              [s_ for s_, _ in hc] == ['info'], hc)
        imgs = [_img(blob('b'), 'Кухня'), _img(blob('c'), '', 'Мастер'), _img(blob('e'), ''), _img(blob('f'), '')]
        F = analyze('http://x/', [_view(images=imgs)], None, None, None, A, set(), [], dict(opts, uploads=U))
        hc = sorted((f['severity'], f['message'].split(':')[0].split(' — ')[0]) for f in F if f['id'] == 'HON-CAPTION')
        check('чужой alt — major, чужая подпись — critical, загрузка вне списка и вне реестра — major',
              hc == [('critical', 'подпись не из списка ассетов'), ('major', 'alt не из списка ассетов'),
                     ('major', f'загрузка {bid["e"]}'), ('major', f'загрузки {bid["f"]} нет в реестре загрузок')], hc)
        F = analyze('http://x/', [_view(images=[_img(blob('b'), 'Кухня'), _img(blob('c'), '')])], None, None, None, ya,
                    set(), [], opts)
        hc = [(f['severity'], f['evidence'].get('images') and len(f['evidence']['images'])) for f in F if f['id'] == 'HON-CAPTION']
        check('без реестра загрузок — одна находка minor на прогон, не major на каждый кадр', hc == [('minor', 2)], hc)
        pl = os.path.join(td, 'home.yaml')
        open(pl, 'w', encoding='utf-8').write('form:\n  ref: lead-forms.yaml#callback\n')
        check('--forms: id из плана страницы', load_form_sets([pl, 'quote-request']) == ['callback', 'quote-request'])

    # приметы на синтетических кадрах
    heads = [{'tag': t, 'el': t, 'text': 'З', 'ff': 'Inter', 'fs': 30, 'fw': '700', 'style': 'normal', 'align': 'left', 'x': 0,
              'w': 600, 'top': 0, 'h': 40, 'lines': 1, 'color': [0, 0, 0, 1], 'accent': None, 'grad': False,
              'eyebrow': {'text': 'НАДЗАГОЛОВОК'} if e else None, 'pill': None} for t, e in
             [('h1', True), ('h2', False), ('h2', True), ('h2', False), ('h2', False), ('h2', False)]]
    F = analyze('http://x/', [_view(headings=heads)], None, None, None, None, set(), [], opts)
    check('надзаголовки 2 из 6 при ceil(6/3) = 2 — не примета', 'LOOK-EYEBROW' not in ids(F, ('major',)), F)
    heads[3]['eyebrow'] = {'text': 'ЕЩЁ'}
    F = analyze('http://x/', [_view(headings=heads)], None, None, None, None, set(), [], opts)
    check('надзаголовки 3 из 6 — примета caps-eyebrow; одиночная — minor, вопрос заказчику',
          any(f['id'] == 'LOOK-EYEBROW' and f['severity'] == 'minor' and f['tell'] == 'caps-eyebrow'
              and 'вопрос заказчику' in f['message'] for f in F), F)
    F = analyze('http://x/', [_view(headings=heads)], None, None, None, None, {'eyebrow'}, [], opts)
    check('--allow eyebrow снимает примету до info', all(f['severity'] == 'info' for f in F if f['id'] == 'LOOK-EYEBROW'))
    arrows = [_leaf('Записаться →', in_btn=True), _leaf('«Отвес»', in_btn=True), _leaf('Мы на Яндекс Картах ↗', in_btn=True, ext=True)]
    F = analyze('http://x/', [_view(leaves=arrows)], None, None, None, None, set(), [], opts)
    ar = [f for f in F if f['id'] == 'LOOK-ARROWS']
    check('стрелки: «→» — примета, «»» и «↗» у внешней ссылки — нет', len(ar) == 1 and ar[0]['evidence']['examples'] == ['Записаться →'], ar)
    row = {'el': 'div.cards', 'n': 3, 'top': 800, 'w_ratio': 1.0, 'h_ratio': 1.0, 'min_w': 0.3, 'min_h': 200, 'same': True,
           'content': True, 'nums': 0, 'num_texts': [], 'in_chrome': False}
    steps = dict(row, n=3, nums=3, num_texts=['1', '2', '3'], cv=0.5)
    F = analyze('http://x/', [_view(rows=[steps])], None, None, None, None, set(), [], opts)
    check('номера шагов 1, 2, 3 — не ряд чисел', 'LOOK-STATS-ROW' not in ids(F))
    F = analyze('http://x/', [_view(rows=[dict(steps, num_texts=['1 146', '4,8', '12 лет'])])], None, None, None, None, set(), [], opts)
    check('ряд 1 146, 4,8, 12 лет — ряд чисел', 'LOOK-STATS-ROW' in ids(F))
    F = analyze('http://x/', [_view(rows=[dict(row, cv=0.1)])], None, None, None, None, set(), [], opts)
    check('три карточки одной длины (CV 0.1) — примета', 'LOOK-THREE-CARDS' in ids(F))
    check('одиночная LOOK-THREE-CARDS — minor, код 0',
          ([f['severity'] for f in F if f['id'] == 'LOOK-THREE-CARDS'], exit_code(summarize(F, set(), 'page'))) == (['minor'], 0),
          [(f['id'], f['severity']) for f in F])
    tiles = dict(row, n=4, nums=4, num_texts=['12', '4', '3', '87 %'], cv=0.5)
    F = analyze('http://x/', [_view(rows=[tiles])], None, None, None, None, set(), [], dict(opts, surface='app', preset='C'))
    check('кабинет: ряд плиток «12 · 4 · 3 · 87 %» — без LOOK-STATS-ROW (примета страницы сайта)',
          'LOOK-STATS-ROW' not in ids(F), ids(F))
    F = analyze('http://x/', [_view(rows=[tiles])], None, None, None, None, set(), [], opts)
    check('тот же ряд на странице сайта — LOOK-STATS-ROW', 'LOOK-STATS-ROW' in ids(F), ids(F))
    check('вне поверхности app — ряд чисел, hero, пилюля, тёплая бумага, отзывы; у страницы — ничего',
          {'LOOK-STATS-ROW', 'LOOK-HERO-CENTER', 'LOOK-PILL', 'LOOK-BG-WARM', 'HON-QUOTE'} <= set(off_surface('app'))
          and off_surface('page') == [], off_surface('app'))
    F = analyze('http://x/', [_view(rows=[dict(row, cv=0.45)])], None, None, None, None, set(), [], opts)
    check('три карточки разного содержания (CV 0.45) — не примета', 'LOOK-THREE-CARDS' not in ids(F))
    F = analyze('http://x/', [_view(rows=[dict(row, cv=0.0, ph=3)])], None, None, None, None, set(), [], opts)
    check('три карточки с одинаковыми заглушками [PLACEHOLDER…] — вариация не мерится, не примета',
          'LOOK-THREE-CARDS' not in ids(F), ids(F))
    hero = {'el': 'section', 'h': 880, 'w': 1440, 'top': 0, 'h1_align': 'center', 'hero_align': 'center', 'h1_cx': 0.5, 'h1_w': 0.5,
            'min_height': '100vh', 'h1_lines': 2, 'media': [], 'bg_url': [], 'overlays': [], 'next_top': 900, 'cue': False}
    F = analyze('http://x/', [_view(hero=hero)], None, None, None, None, set(), [], opts)
    check('hero 98 % по центру без продолжения — примета AIL-06', 'LOOK-HERO-CENTER' in ids(F))
    F = analyze('http://x/', [_view(hero=dict(hero, next_top=860))], None, None, None, None, set(), [], opts)
    check('край следующей секции виден — не примета', 'LOOK-HERO-CENTER' not in ids(F))
    F = analyze('http://x/', [_view(hero=dict(hero, h=820))], None, None, None, None, set(), [], opts)
    check('hero 91 % окна (< 95 %) — не примета', 'LOOK-HERO-CENTER' not in ids(F))
    bento = {'el': 'div.grid', 'n': 6, 'one_radius': True, 'radius': '20px', 'one_padding': True, 'same': True, 'sizes': 2, 'rows': 2,
             'in_chrome': False}
    orbit = {'el': 'div.orbit', 'icons': 8, 'radius': 220, 'ring_cv': 0.04, 'top': 200}
    F = analyze('http://x/', [_view(bento=[bento], orbit=[orbit])], None, None, None, None, set(), [], opts)
    check('бенто 6 однотипных плиток и орбита 8 иконок — приметы',
          {f['tell'] for f in F if f['id'] in ('LOOK-BENTO', 'LOOK-ORBIT')} == {'bento-uniform-tiles', 'logo-orbit-hero'}
          or {f['id'] for f in F} >= {'LOOK-BENTO', 'LOOK-ORBIT'}, [(f['id'], f['tell']) for f in F])
    F = analyze('http://x/', [_view(bento=[dict(bento, n=4)], orbit=[dict(orbit, icons=4)])], None, None, None, None, set(), [], opts)
    check('4 плитки и 4 иконки — ниже порогов владельца', not {'LOOK-BENTO', 'LOOK-ORBIT'} & set(ids(F)))

    # вердикт кластера: пороги владельцев, одиночная примета — вопрос, кластер — major и код 1
    check('пороги кластеров у владельцев: ui 11/04 §1.3 — маркеров 4, хрома 3; реестр клише — 3',
          (ui_diagnosis(), cliche_cluster_min()) == ({'markers': 4, 'chrome': 3}, 3), (ui_diagnosis(), cliche_cluster_min()))
    F = analyze('http://x/', [_view(rows=[dict(row, cv=0.1)], bento=[bento])], None, None, None, None, set(), [], opts)
    kit = sorted((f['id'], f['severity'], f.get('cluster')) for f in F if f['id'] in ('LOOK-THREE-CARDS', 'LOOK-BENTO'))
    check('три карточки и бенто — кластер saas-card-kit: обе major, код 1',
          (kit, exit_code(summarize(F, set(), 'page'))) == ([('LOOK-BENTO', 'major', 'saas-card-kit'),
                                                             ('LOOK-THREE-CARDS', 'major', 'saas-card-kit')], 1), kit)
    chrome_leaves = [_leaf('Записаться →', in_btn=True), _leaf('01 Замер'), _leaf('02 Смета'), _leaf('03 Ремонт')]
    F = analyze('http://x/', [_view(headings=heads, leaves=chrome_leaves)], None, None, None, None, set(), [], opts)
    ch = sorted((f['id'], f['severity']) for f in F if f.get('cluster') == 'template-chrome')
    check('надзаголовки, стрелка и нумерация — кластер шаблонного хрома (3 из порога 3): major, код 1',
          (ch, exit_code(summarize(F, set(), 'page'))) == ([('LOOK-ARROWS', 'major'), ('LOOK-EYEBROW', 'major'),
                                                           ('LOOK-NUMBERED', 'major')], 1), ch)
    F = analyze('http://x/', [_view(headings=heads, leaves=chrome_leaves)], None, None, None, None, {'eyebrow'}, [], opts)
    check('снятая ключом примета в кластер не входит: хром 2 из 3 — minor, код 0',
          (sorted((f['id'], f['severity']) for f in F if f['id'] in ('LOOK-ARROWS', 'LOOK-NUMBERED')),
           exit_code(summarize(F, {'eyebrow'}, 'page'))) == ([('LOOK-ARROWS', 'minor'), ('LOOK-NUMBERED', 'minor')], 0),
          [(f['id'], f['severity']) for f in F])

    # токены ДС: антиква и тёплый фон, которые называет ДС, — решение, а не примета
    serif = [dict(heads[1], tag='h1', el='h1', ff='"Playfair Display", Georgia, serif', fs=56, eyebrow=None)]
    cream = _view(headings=serif, page_bg=[0xF4, 0xF1, 0xEA])
    F = analyze('http://x/', [cream], None, None, None, None, set(), [], opts)
    cs = sorted((f['id'], f['severity'], f.get('cluster')) for f in F if f['id'] in ('LOOK-SERIF-DISPLAY', 'LOOK-BG-WARM'))
    check('антиква и тёплая бумага без токенов ДС — кластер cream-serif: обе major',
          cs == [('LOOK-BG-WARM', 'major', 'cream-serif'), ('LOOK-SERIF-DISPLAY', 'major', 'cream-serif')], cs)
    ds_cream = {'families': {'playfair display'}, 'colors': [(0xF4, 0xF1, 0xEA)]}
    F = analyze('http://x/', [cream], None, None, None, None, set(), [], dict(opts, ds=ds_cream))
    check('антиква и тёплый фон — значения токенов ДС: LOOK-SERIF-DISPLAY и LOOK-BG-WARM молчат (info), код 0',
          ({(f['id'], f['severity']) for f in F if f['id'] in ('LOOK-SERIF-DISPLAY', 'LOOK-BG-WARM')},
           exit_code(summarize(F, set(), 'page'))) == ({('LOOK-SERIF-DISPLAY', 'info'), ('LOOK-BG-WARM', 'info')}, 0),
          [(f['id'], f['severity']) for f in F])
    check('цвет токена — с допуском округления 2 на канал', ds_color((0xF5, 0xF0, 0xEA), ds_cream)
          and not ds_color((0xF8, 0xF1, 0xEA), ds_cream))
    dl = ds_look(str(kbpaths.kb('claude-design', '05-design-artifacts', 'example', 'design-system', 'project', 'tokens.json')))
    check('--tokens: гарнитуры и цвета артефакта ДС', {'golos text', 'unbounded'} <= dl['families'] and (12, 15, 20) in dl['colors'],
          dl['families'])
    many = [_leaf('т', fs=f) for f in (12, 13, 14, 15, 16, 18, 20, 24, 28, 32, 40)]
    F = analyze('http://x/', [_view(leaves=many, header={'el': 'header', 'h': 96})], None, None, None, None, set(), [], opts)
    check('11 кеглей (> 9) — шкала без ролей; шапка 96 > 80 на десктопе страницы',
          {'LOOK-TYPE-SCALE', 'LOOK-HEADER'} <= set(ids(F)), ids(F))
    F = analyze('http://x/', [_view(header={'el': 'header', 'h': 56})], None, None, None, None, set(), [],
                dict(opts, surface='app', preset='A'))
    check('кабинет, пресет A: шапка 56 > 48 — примета', 'LOOK-HEADER' in ids(F))
    leaves = [_leaf('Гарантия 3 года на работы'), _leaf('Ремонт за 3 дня'), _leaf('Более 500 проектов'), _leaf('2'),
              _leaf('Звоните: +7 (831) 555-12-34')]
    facts = {'known': number_claims('Гарантия 3 года на работы; телефон +7 (831) 555-12-34'), 'no_source': [], 'rows': 2}
    F = analyze('http://x/', [_view(leaves=leaves)], None, facts, None, None, set(), [], opts)
    nf = next((f for f in F if f['id'] == 'HON-NUMBERS'), None)
    check('HON-NUMBERS: «3 дня» и «500 проектов» — выдумки, гарантия и телефон — факты, номер шага «2» — не число',
          nf and sorted(n['raw'] for n in nf['evidence']['numbers']) == ['3', '500'], nf and nf['evidence'])
    check('находка честности несёт примету invented-numbers', nf and nf['tell'] == 'invented-numbers' and nf['group'] == 'honesty')

    # кабинет: табличный copy.md входа и демо-набор (--demo) — запись демо-набора на экране не выдумка
    fxin = kbpaths.scripts('tests', 'fixtures', 'package-cabinet-defects', 'files', 'design', 'office', 'input')
    app_copy = load_copy(str(fxin / 'copy.md'))
    demo = load_demo(str(fxin / 'demo-data.json'))
    rec = next(r for o in json.load(open(fxin / 'demo-data.json', encoding='utf-8'))['objects'].values()
               for r in o.get('records') or [])
    shown = []
    for k, v in rec.items():
        if k.startswith('_') or isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            shown.append(f'{v:,}'.replace(',', ' ') + ' ₽')
        elif isinstance(v, list):
            shown.append(', '.join(str(x) for x in v))
        else:
            dm = ISO_DATE_RX.match(str(v))
            shown.append(f'{dm.group(3)}.{dm.group(2)}.{dm.group(1)}' if dm else str(v))
    cells = [_leaf(t, tag='td') for t in shown]
    blocks = [{'el': 'td', 'tag': 'td', 'text': t, 'quote': False} for t in shown] + \
             [{'el': 'li', 'tag': 'li', 'text': ' · '.join(shown), 'quote': False}]
    app = dict(opts, surface='app', preset='C')
    F = analyze('http://x/', [_view(leaves=cells, blocks=blocks)], None, None, app_copy, None, set(), [], app)
    check('кабинет без --demo: числа и тексты записи — HON-NUMBERS и HON-COPY', {'HON-NUMBERS', 'HON-COPY'} <= set(ids(F)),
          ids(F))
    F = analyze('http://x/', [_view(leaves=cells, blocks=blocks)], None, None, app_copy, None, set(), [], dict(app, demo=demo))
    check('copy.md кабинета с --demo: числа и записи демо-набора — без HON-NUMBERS и HON-COPY',
          not {'HON-NUMBERS', 'HON-COPY'} & set(ids(F)), [(f['id'], f['message']) for f in F if f['id'].startswith('HON')])
    fake = next(n for n in range(987654, 999999) if str(n) not in demo['values'])
    F = analyze('http://x/', [_view(leaves=cells + [_leaf(f'Экономия {fake:,} ₽ в год'.replace(',', ' '))], blocks=blocks)],
                None, None, app_copy, None, set(), [], dict(app, demo=demo))
    nf = next((f for f in F if f['id'] == 'HON-NUMBERS'), None)
    check('с --demo число вне демо-набора — HON-NUMBERS', nf and [n['value'] for n in nf['evidence']['numbers']] == [str(fake)],
          nf and nf['evidence'])
    form = {'el': 'form', 'in_dialog': False, 'text': 'Имя Телефон Нажимая кнопку, вы соглашаетесь с политикой',
            'submit': {'text': 'Отправить', 'disabled': True},
            'fields': [_field('Имя', name='name'), _field('Телефон', 'tel', required=True), _field('', 'email', placeholder='Почта'),
                       _field('Что нужно сделать', required=True, tag='textarea', name='task')]}
    F = analyze('http://x/', [_view(forms=[form])], None, None, None, None, set(), [], dict(opts, form_sets=['callback']))
    fb = sorted(f['evidence'].get('forbidden') for f in F if f['id'] == 'FORM-FORBIDDEN')
    check('запреты форм: согласие кнопкой, неактивная кнопка, обязательный комментарий',
          fb == ['consent-by-button', 'disabled-submit', 'required-comment'], fb)
    Fa = analyze('http://x/', [_view(forms=[form])], None, None, None, None, set(), [], dict(opts, surface='app', preset='C'))
    fa = sorted(f['evidence'].get('forbidden') for f in Fa if f['id'] == 'FORM-FORBIDDEN')
    check('служебная форма экрана приложения: без запретов формы заявки, неактивная кнопка — находка',
          fa == ['disabled-submit'], fa)
    ff = next((f for f in F if f['id'] == 'FORM-FIELDS'), None)
    check('поля против набора callback: нет preferred-time, лишние email и task, у почты нет подписи',
          ff and ff['evidence']['missing'] == ['preferred-time'] and sorted(ff['evidence']['extra']) == ['email', 'task']
          and ff['evidence']['no_label'], ff and ff['evidence'])
    good = {'el': 'form', 'in_dialog': False, 'text': 'Телефон Имя', 'submit': {'text': 'Позвать', 'disabled': False},
            'fields': [_field('Телефон', 'tel', required=True), _field('Имя', name='name'),
                       _field('Когда удобно принять звонок', name='preferred-time'),
                       _field('Согласен на обработку персональных данных', 'checkbox')]}
    F = analyze('http://x/', [_view(forms=[good])], None, None, None, None, set(), [], dict(opts, form_sets=['callback']))
    check('форма по набору с отдельной неотмеченной галочкой — 0 находок форм', not {'FORM-FIELDS', 'FORM-FORBIDDEN'} & set(ids(F)),
          [(f['id'], f['message']) for f in F if f['id'].startswith('FORM')])
    ov = _view(390, 844, scroll_w=412, overflow_only=True)
    F = analyze('http://x/', [_view(), ov], None, None, None, None, set(), [], opts)
    check('кадр вылета: только M-OVERFLOW', ids(F, ('critical',)) == ['M-OVERFLOW'], ids(F))
    F = analyze('http://x/', [_view(), _view(390, 844, nav={'navs': [], 'toggles': []})], None, None, None, None, set(), [],
                opts)
    check('M-NAV на посадочной без меню — major, как пункт D2 приёмки (S); код 0',
          ([f['severity'] for f in F if f['id'] == 'M-NAV'], exit_code(summarize(F, set(), 'page'))) == (['major'], 0),
          [(f['id'], f['severity']) for f in F])

    Fn = analyze('http://x/', [_view(), _view(390, 844, nav={'navs': [], 'toggles': []})], None, None, None, None,
                 {'no-nav'}, [], opts)
    nv = [f for f in Fn if f['id'] == 'M-NAV']
    check('--allow no-nav: M-NAV — info с пометкой allowed, ключом, причиной и тяжестью без ключа',
          [(f['severity'], f['allowed'], f.get('allow'), f.get('base_severity'), f.get('reason')) for f in nv]
          == [('info', True, 'no-nav', 'major', 'решение плана страницы: --allow no-nav')], nv)
    sn = summarize(Fn, {'no-nav'}, 'page')
    check('--allow no-nav: сводка называет снятую находку с тяжестью без ключа, отчёт md — строкой «Снято решением»',
          sn['allowed'] == [{'id': 'M-NAV', 'allow': 'no-nav', 'base_severity': 'major', 'view': '390x844',
                             'reason': 'решение плана страницы: --allow no-nav'}]
          and 'Снято решением (тяжесть без ключа): M-NAV — major' in to_md(
              {'target': 't', 'created': 'c', 'summary': sn, 'findings': Fn}), sn['allowed'])
    check('без ключа у находки нет полей снятия', all('allow' not in f and 'base_severity' not in f for f in F))

    # части артборда: шапка с навигацией и H1 — у первой части
    parts = [artboard_part(n, w) for n, w in (('Home-390-1.html', 390), ('Home-390-2.dc.html', 390), ('Home-1440.html', 1440),
                                              ('Flat-204-1440.dc.html', 1440), ('Tariff-B2-390.html', 390))]
    check('часть артборда — имя <Имя>-<ширина>-<N> при рамке этой ширины; число в имени страницы — не номер части',
          parts == [('Home-390', 1), ('Home-390', 2), ('Home-1440', None), ('Flat-204-1440', None), ('Tariff-B2-390', None)],
          parts)
    no_nav = _view(390, 844, nav={'navs': [], 'toggles': []})
    sev = [[f['severity'] for f in analyze('http://x/', [no_nav], None, None, None, None, set(), [], dict(opts, part=n))
            if f['id'] == 'M-NAV'] for n in (1, 2, 3)]
    check('копия без шапки: первая часть — M-NAV major, вторая и третья — справка', sev == [['major'], ['info'], ['info']], sev)
    check('кадр --shots: у копии артборда — по имени копии, части не затирают друг друга; у страницы — по классу окна',
          [shot_name(390, 844, 'Home-390-1'), shot_name(390, 844, 'Home-390-2'), shot_name(390, 844), shot_name(1440, 900)]
          == ['Home-390-1-390x844-00.jpg', 'Home-390-2-390x844-00.jpg', 'mobile-390x844-00.jpg', 'desktop-1440x900-00.jpg'])

    # тело 16 px — по абзацам основного содержимого, строка реквизитов подвала не в счёт
    body = _leaf('Мастерская открыта каждый день с десяти утра до восьми вечера без перерыва')
    legal = _leaf('ООО «Демо», ИНН 0000000000, адрес регистрации и реквизиты для договора', fs=14)
    F = analyze('http://x/', [_view(390, 844, leaves=[body, dict(legal, body=False)])], None, None, None, None, set(), [], opts)
    check('короткая страница: абзац тела 16 px и строка подвала 14 px — без M-BODY-16', 'M-BODY-16' not in ids(F), ids(F))
    F = analyze('http://x/', [_view(390, 844, leaves=[body, legal])], None, None, None, None, set(), [], opts)
    check('тот же абзац 14 px внутри main — M-BODY-16', 'M-BODY-16' in ids(F, ('major',)), ids(F))

    with tempfile.TemporaryDirectory() as td:
        for surf, route in (('office', 'app'), ('promo', 'landing'), ('bare', None)):
            os.makedirs(os.path.join(td, 'design', surf, 'canvas', 'html'))
            os.makedirs(os.path.join(td, 'design', surf, 'input'))
            open(os.path.join(td, 'design', surf, 'canvas', 'html', 'Main.html'), 'w', encoding='utf-8').write('<p>т</p>')
            if route:
                open(os.path.join(td, 'design', surf, 'input', INPUT_MANIFEST), 'w', encoding='utf-8').write(
                    f'---\nstage: mockup\nsurface: {surf}\nroute: {route}\n---\n# Вход холста\n')
        got = [input_surface(os.path.join(td, 'design', s, 'canvas', 'html', 'Main.html')) for s in ('office', 'promo', 'bare')]
        check('поверхность без ключа — по манифесту входа: route app — экран приложения, landing — страница, нет '
              'манифеста — None', got + [input_surface('https://example.test/'), input_surface(td)]
              == ['app', 'page', None, None, None], got)
    with tempfile.TemporaryDirectory() as td:
        cp = os.path.join(td, 'Main.html')
        open(cp, 'w', encoding='utf-8').write('<!doctype html><head><!-- dc_to_html: статичная копия артборда Main.dc.html; '
                                              'перевод исходника · рамка 1440×2700 · твики: — --></head>')
        check('статичная копия — окно своей рамки', (static_frame(cp), static_frame(__file__)) == (1440, None))
        check('статичная копия — имя артборда и рамка из строки происхождения',
              static_copy(cp) == {'artboard': 'Main.dc.html', 'w': 1440, 'h': 2700}, static_copy(cp))

    # сводка: примета один раз, домены не складываются
    F = [{'id': 'HON-UNSPLASH', 'tell': 'stock-and-hotlink', 'group': 'honesty', 'severity': 'critical'},
         {'id': 'HON-STOCK', 'tell': 'stock-and-hotlink', 'group': 'honesty', 'severity': 'critical'},
         {'id': 'LOOK-BG-WARM', 'tell': 'warm-paper', 'group': 'look', 'severity': 'major'},
         {'id': 'LOOK-EYEBROW', 'tell': 'caps-eyebrow', 'group': 'look', 'severity': 'major'},
         {'id': 'LOOK-META-DOTS', 'tell': 'meta-dots', 'group': 'look', 'severity': 'minor'},
         {'id': 'LOOK-ARROWS', 'tell': 'arrow-in-button', 'group': 'look', 'severity': 'minor'},
         {'id': 'LOOK-NUMBERED', 'tell': 'numbered-labels', 'group': 'look', 'severity': 'minor'}]
    sm = summarize(F, set(), 'page')
    check('сводка: две проверки стока — одна примета', [t['tell'] for t in sm['tells']].count('stock-and-hotlink') == 1)
    check('сводка: тёплая бумага — домен page-visual', sm['domains'].get('page-visual', {}).get('tells') == ['warm-paper'], sm['domains'])
    check('сводка: у доменов свой счёт, общего нет', 'total' not in sm and all('count' in d for d in sm['domains'].values()))
    chrome = next((c for c in sm['clusters'] if c['id'] == 'template-chrome'), None)
    check('сводка: кластер шаблонного хрома — 4 члена из 6 с правилом владельца, порог 3 — сложился',
          chrome and len(chrome['members_hit']) == 4 and chrome['members'] == 6 and chrome['rule'] and chrome['min'] == 3
          and chrome['formed'] and 'template-chrome' in sm['clusters_formed'], chrome)
    sa = summarize(F, set(), 'app')
    check('сводка кабинета: маркеры ui 11/04 домена app-visual', 'ui_markers' in sa['domains'].get('app-visual', {}), sa['domains'])
    dom = next((c for c in sa['clusters'] if c['id'] == 'domain:app-visual'), None)
    check('сводка кабинета: маркеров app-visual 3 при пороге владельца 4 — кластер не сложился',
          dom and len(dom['members_hit']) == 3 and dom['min'] == 4 and not dom['formed'], dom)
    check('подсказка приёмки по группам реестра', sm['acceptance_hint'] == {'look': False, 'honesty': False, 'acceptance': True},
          sm['acceptance_hint'])
    miss = sorted({f['id'] for f in F} - set(reg['checks']))
    check('id проверок сводки есть в реестре примет', not miss, miss)
    if getattr(_a, 'browser', False):
        fg = free_gb()
        if fg is not None and fg < _a.min_free_gb:
            print(f'selftest --browser: свободно {fg:.1f} ГБ < {_a.min_free_gb} ГБ — браузер не запускался')
            print('selftest:', 'OK' if ok else 'FAIL', '(без браузера)')
            return 3 if ok else 1
        selftest_browser(check, dict(opts, first_bp=first_breakpoint()))
    print('selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


def selftest_browser(check, opts):
    """Код страницы COLLECT_JS в Chromium на синтетической копии артборда в двух частях (`fixtures/artboard-parts/`,
    данные вымышлены): hero — секция разметки, а не рамка копии; служебные пометки артборда вне проверок; тело 16 px; ряд
    заглушек; навигация у первой части; постер, источник видео и фон-загрузка против списка ассетов."""
    fx = str(FIXTURE_PARTS)
    assets = parse_assets_readme(os.path.join(fx, 'assets.md'))
    uploads = load_uploads(os.path.join(fx, 'ARTIFACTS.md'))
    got = {}
    for n in (1, 2):
        target = os.path.join(fx, f'Stub-390-{n}.html')
        copy = static_copy(target)
        url, views, blocked = collect(target, [f"{copy['w']}x{VIEW_H_NARROW}"], '', True, None)
        part = artboard_part(copy['artboard'], copy['w'])[1]
        got[n] = (views[0], analyze(url, views, None, None, None, assets, set(), blocked,
                                    dict(opts, part=part, uploads=uploads)))
    (v1, F1), (v2, F2) = got[1], got[2]

    def ids(F, sev=None):
        return sorted({f['id'] for f in F if sev is None or f['severity'] in sev})

    texts = ' '.join(l['text'] for v in (v1, v2) for l in v['leaves']) + ' '.join(b['text'] for v in (v1, v2) for b in v['blocks'])
    check('браузер: копия — окно своей рамки, часть 1 и часть 2', [(v['vw'], g[1] is not None) for v, g in ((v1, got[1]), (v2, got[2]))]
          == [(390, True), (390, True)] and [artboard_part(f'Stub-390-{n}.html', 390)[1] for n in (1, 2)] == [1, 2])
    check('браузер: hero — секция разметки с H1, а не рамка копии', (v1['hero'] or {}).get('el', '').startswith('section'),
          v1['hero'] and v1['hero']['el'])
    check('браузер: служебные пометки артборда data-wf не попадают в текст проверок', 'служебная пометка' not in texts
          and 'Переплёт книг на заказ' in texts, texts[:200])
    check('браузер: тело 16 px у первой части — без M-BODY-16; 14 px у второй — M-BODY-16 major',
          ('M-BODY-16' in ids(F1), 'M-BODY-16' in ids(F2, ('major',))) == (False, True), (ids(F1), ids(F2)))
    check('браузер: ряд карточек-заглушек [PLACEHOLDER…] — не примета', 'LOOK-THREE-CARDS' not in ids(F1), ids(F1))
    check('браузер: навигация — кнопка меню у первой части, у второй M-NAV справкой',
          ([f['severity'] for f in F1 if f['id'] == 'M-NAV'], [f['severity'] for f in F2 if f['id'] == 'M-NAV'])
          == ([], ['info']), [(f['id'], f['severity']) for f in F1 + F2 if f['id'] == 'M-NAV'])
    kinds = sorted((m['kind'], blob_id(m['src'])) for m in v1.get('media') or [])
    check('браузер: постер и источник видео собраны', kinds == [('poster', 'up-poster-01'), ('source', 'up-clip-01')], kinds)
    hc = [(f['severity'], f['message']) for f in F1 if f['id'] == 'HON-CAPTION']
    check('браузер: картинка, постер и источник видео — из списка ассетов; фон-загрузка вне реестра — HON-CAPTION major',
          hc == [('major', 'загрузки up-ghost-99 нет в реестре загрузок')], hc)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('page', help='приметы «дефолтного вида», честность, формы, телефон по отрисованной странице')
    p.add_argument('target')
    p.add_argument('--views', help='окна через запятую (1440x900,390x844); по умолчанию — артборды acceptance-widths.yaml')
    p.add_argument('--acceptance', action='store_true', help='все ширины приёмки и прогон вылета на overflow_only')
    p.add_argument('--surface', choices=('page', 'app'), help='страница сайта или экран приложения; без ключа — по '
                                                              'манифесту входа холста копии, иначе страница сайта')
    p.add_argument('--preset', choices=('A', 'B', 'C', 'D'), default='A', help='пресет экрана приложения (порог шапки)')
    p.add_argument('--tokens', help='токены ДС (CSS, DTCG или tokens.json артефакта): первый брейкпоинт; антиква и '
                                    'тёплый фон из токенов — решение ДС, не примета')
    p.add_argument('--facts', help='facts.md входа холста или facts.yaml продукта')
    p.add_argument('--copy', help='copy.md входа холста (строки слотов или таблица кабинета) или copy deck (YAML, JSON)')
    p.add_argument('--page', help='id страницы copy deck (с --copy YAML)')
    p.add_argument('--demo', help='demo-data.json входа холста кабинета: тексты и числа записей — не выдумка')
    p.add_argument('--assets', '--assets-readme', dest='assets', help='assets.md входа холста или YAML плана ассетов')
    p.add_argument('--uploads', help='реестр загрузок холста — ARTIFACTS.md продукта (таблица «Загрузки»); без ключа — '
                                     'ARTIFACTS.md в папках выше списка --assets')
    p.add_argument('--forms', action='append', help='id набора lead-forms.yaml или YAML плана страницы; повтором')
    p.add_argument('--src', help='папка исходников для статического обхода (сток, шрифты)')
    p.add_argument('--allow', default='', help='приметы с записанным решением: ' + ','.join(sorted(allow_keys())))
    p.add_argument('--ignore-selector', default='', help='CSS-селектор чужих вставок (виджеты хостинга, чаты)')
    p.add_argument('--block-external', action='store_true'); p.add_argument('--allow-external', action='store_true')
    p.add_argument('--shots', help='папка: первый экран каждого окна JPEG q80; у копии артборда кадр назван по копии')
    p.add_argument('--json'); p.add_argument('--md'); p.add_argument('--min-free-gb', type=float, default=2.0)
    r = sub.add_parser('resize', help='ресайз широкий → узкий → широкий без перезагрузки на собранной странице '
                                      '(пункт H5 приёмки)')
    desk, mob = resize_windows()
    r.add_argument('target')
    r.add_argument('--desktop', default=desk)
    r.add_argument('--mobile', default=mob)
    r.add_argument('--wait-ms', type=int, default=1000); r.add_argument('--max-diff', type=float, default=0.02)
    r.add_argument('--shots'); r.add_argument('--min-free-gb', type=float, default=2.0)
    st = sub.add_parser('selftest', help='офлайн-проверки; с --browser — ещё код страницы на синтетической копии артборда')
    st.add_argument('--browser', action='store_true', help='прогон Chromium по fixtures/artboard-parts/ (замок браузера)')
    st.add_argument('--min-free-gb', type=float, default=2.0)
    a = ap.parse_args()
    return {'page': cmd_page, 'resize': cmd_resize, 'selftest': cmd_selftest}[a.cmd](a)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit as e:              # текст вместо кода — ошибка вызова или окружения
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            sys.exit(2)
        raise
