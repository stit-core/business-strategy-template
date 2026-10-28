#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""copydeck.py — copy deck: каркас из плана страницы, проверка формата и стыка, сверка с фактами, линтер, статусы,
выбор вариантов, утверждение, выгрузка во вход холста и приём правок текста с холста.

Формат — 10-templates-recipes/copy-deck.schema.json (поля и статусы v0 на месте; статус assumed — черновик агента
«допущением»); процесс — 10-templates-recipes/01-copy-deck-workflow.md; стык с планом — x-site-map схемы, выгрузка во
вход холста — x-canvas-map (ключ copy_md: синтаксис copy.md, статусы по этапу). id типов страниц, ролей секций, слотов и
блоков — словарь site (kb/site/02-site-types/vocabulary.yaml, kb/site/04-blocks/blocks.yaml).

Подкоманды (порядок проверок: сначала факты и право, потом стиль, потом формат и статусы):
  skeleton PLAN -o DECK [--facts-ref F] [--voice-ref V] [--date ГГГГ-ММ-ДД] [--force]
        каркас copy deck из плана страницы (page-plan): секции, текстовые слоты, анатомия блока, группы, fact_ids и
        missing_ids из binds слотов данных (missing_ids — только пробел с заглушкой: fallback rewrite-without и
        omit-block заглушки не оставляют), мета из page_slots, page_plan_ref; voice_ref — из смысла, legal_category —
        из брифа (refs плана); тексты пусты, статус draft; папка выхода создаётся; слот готового сообщения
        мессенджера (текстовый слот, который называет target.prefill действия секции или page.cta_target плана)
        получает пометку, чьё это сообщение;
        иерархий в плане больше одной без вариантов и без правила сведения — заметка (см. validate)
  validate DECK [--facts F] [--plan PLAN] [--today ГГГГ-ММ-ДД] [--final] [--no-jsonschema]
        схема (jsonschema, если есть; иначе встроенная проверка того же подмножества), id и ссылки, статусы
        (x-status-rules), словарь site, block против blocks.yaml, стык с планом (page_plan_ref или --plan; на плане
        стоят страница с его id и образцы шаблона коллекции — страницы с site_page_id = id плана), иерархии плана
        (их больше одной, вариантов первого экрана first_screen.variant_map нет и правила awareness_basis.rule нет —
        warning COPY-D-HIERARCHY), факты (есть
        ли, не пробел ли, не истекли ли, публикуемы ли, демо-данные), [PLACEHOLDER], обещание и ядро первого экрана
        (секция hero, без неё — первая после шапки), строки в картинках, второй язык; правила copy-slots.yaml,
        voice.yaml, meta-rules.yaml, claims-rules.yaml: есть — проверка работает, нет — предупреждение
        «правила не загружены»; заголовок, равный имени сущности фактов (entities[].names), короче нормы длины
        copy-slots.yaml — не находка COPY-D-LEN; copy_slots_ref, который не разрешается от папки copy deck, —
        предупреждение COPY-D-RULES-REF и правила copy-slots.yaml базы; нет voice_ref — предупреждение COPY-D-VOICE
        (голос не проверяется); OG-поля мета ждутся те, что заведены слотами плана; записи claims_allow; --final —
        ворота публикации: страница approved, 0 [PLACEHOLDER], 0 демо-фактов, мета заполнена (без --final пустая
        мета — warning), обходы claims_allow — списком
  claims DECK [--facts F] [--today …] [--strict] [--all-variants] [--final]
        claims_check.py (факты и право) процессом на плоской копии: обещание, мета, OG-шаблон — тоже текст страницы;
        находки, обойдённые claims_allow, в error не идут — списком обходов
  lint DECK [--final] [--all-variants] [--no-page-pass]
        copy_lint.py через API lint_text: каждый слот со своим slot_type и жанром + проход страницы; линтер получает
        файл фактов copy deck (facts_ref): адреса и названия мест из его сущностей вида place правило о слове на
        «-ая,» не трогает
  check DECK [--facts F] [--today …] [--final] [--strict] [--all-variants] [--update OUT [--promote]]
        claims → lint → validate (линтер получает тот же файл фактов, что и сверка: --facts, без него — facts_ref);
        --update пишет копию deck с записями lint и claims (text_hash, дата, версия),
        --promote — draft и assumed → checked у текстов без error проверки (claims, lint, validate — и на статусе
        checked тоже), страница — checked, когда проверены все её выбранные тексты и error нет; --all-variants —
        альтернативы «как выбранные», только отчёт: записи --update — у выбранных текстов
  export DECK --page ID --stage directions|mockup [--out DIR] [--facts F] [--facts-scope all|used]
        выгрузка во вход холста: DIR/pages/<page-id>/copy.md (тексты статуса этапа) и DIR/facts.md («Факты», «Нет»,
        «Нельзя утверждать»); слот без текста статуса этапа — находка COPY-D-STAGE (макет — error, направления —
        warning); по умолчанию DIR — $DDD_HOME/out/text/export
  import-copy COPY.md --deck DECK --page ID -o OUT [--choose] [--date ГГГГ-ММ-ДД]
        приём правок текста с холста: изменённый текст слота — новый вариант source: customer (draft); --choose — сразу
        выбран, страница возвращается в draft; тексты холста без слота плана — вопрос «перенести в план?»
  export-assets DECK [--page ID] [-o OUT]   alt, подписи, строки в картинках, OG → фрагмент плана ассетов ai-media
  export-variants DECK -o SHEET.md --key KEY.yaml [--seed N] [--include-failed]   лист слепого выбора (метки; модели
                                             и авторы скрыты; варианты с error в своём поле checks сняты)
  apply-selection DECK --key KEY.yaml (--votes VOTES.yaml | --sheet SHEET.md) --by КТО -o OUT [--method M] [--at ДАТА]
                                             голоса слепого выбора → chosen и selection {method, by, at, compared,
                                             tally, ref}; у мета — выбранный текст в meta.<поле>
  select DECK --page ID --slot СЕКЦИЯ/СЛОТ --variant ID --by КТО -o OUT [--method M] [--at ДАТА]
                                             открытый выбор варианта человеком: chosen и selection {method, by, at,
                                             compared}; --slot — <section_id>/<slot_id>, id слота, если он один на
                                             странице, или promise; сменился выбранный текст — страница checked или
                                             approved возвращается в draft
  approve DECK --page ID --by КТО -o OUT      утверждение страницы человеком: checked (0 error, актуальный text_hash)
                                             → approved; заглушка пробела facts.yaml missing[] — warning (её держит
                                             validate --final), заглушка без пробела или о другом, чем пробел
                                             missing_ids слота, — отказ; журнал процесса (edit_log, отклонённые
                                             варианты) уходит — история в git; пустая мета — warning; обходы
                                             claims_allow страницы — списком
  before-after [--write | --check]           пустой why в 10-templates-recipes/before-after.tsv — из rule_ref (заголовок
                                             раздела нормы); без ключей — показать, что будет заполнено; --check —
                                             код 1, если есть что заполнить
  --selftest                                 офлайн-тесты
Все подкоманды проверок: --json OUT, --md OUT, --quiet.
Коды выхода: 0 — нет error; 1 — есть error (у approve, select, apply-selection, import-copy — отказ с находкой, у
before-after --check — есть что заполнить); 2 — ошибка вызова, входа или окружения (файл не читается, неверный ключ,
нет PyYAML, линтер copy_lint.py не импортируется); 3 — у claims и check: сверка фактов не отработала (claims_check.py
нет, он не уложился во время или завершился ошибкой) — находки сверки неполны, причина — находка COPY-D-TOOL.

Команды, которые пишут copy deck (check --update, approve, import-copy, apply-selection, select), ставят copy_deck.date
— дату записи — и шапку о файле: без даты и пути источника, со строкой всех утверждённых страниц. Относительные ссылки
(facts_ref, voice_ref, page_plan_ref, hierarchy_ref и остальные) остаются как в исходном файле — от его папки: файл,
записанный в другую папку, рассчитан на возврат на место исходного, об этом говорит предупреждение.

Обход эвристик сверки — claims_allow слота, мета (meta.claims_allow — тексты мета) или страницы: [{rule, reason, by
[, value | fragment]}]. rule — семейство или id находки: COPY-F-CLASS (маркер класса утверждения без факта), COPY-F-NUM
(семейство: число без факта и число, не совпавшее с фактом — COPY-F-NUM, COPY-F-NUM-MISMATCH) или COPY-F-NUM-MISMATCH
(только несовпавшее число); value — число, которое снято, fragment — фрагмент находки (слово или фраза целиком): с ними
запись снимает одну эту находку, без них — все находки правила на своём месте; reason — почему находка ложная (у числа —
fact:<id>, на котором оно стоит, или почему это не утверждение); by — кто решил: заказчик или аналитик, а не агент.
Обойдённая находка не считается в error сверки и записях claims; claims, check, approve и validate --final перечисляют
обходы отдельным списком (--json — поле allowed). Право (COPY-L-…), never_claim, «утверждение шире факта» и остальная
сверка не обходятся. Запись без reason или by, с другим правилом, с value не числом или с fact:<id>, которого нет в
facts.yaml, — не обход: находка остаётся, validate — warning COPY-D-CLAIMS-ALLOW.

Зависимости: Python 3.10+, PyYAML; jsonschema — необязательно (Python окружения скилла). Модели, сеть и браузер не
нужны. claims_check.py вызывается процессом, copy_lint.py — через lint_text.
"""
from __future__ import annotations

import argparse
import copy as _copy
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:  # pragma: no cover
    print('copydeck.py: нужен PyYAML (Python окружения скилла: $DDD_HOME/venv, scripts/install.sh)', file=sys.stderr)
    sys.exit(2)

VERSION = '1.2'
DATE = '2026-09-29'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb('text'))
SCHEMA_PATH = os.path.join(ROOT, '10-templates-recipes', 'copy-deck.schema.json')
VOCAB_PATH = str(kbpaths.kb('site', '02-site-types', 'vocabulary.yaml'))   # словарь id системы (site v1)
BLOCKS_PATH = str(kbpaths.kb('site', '04-blocks', 'blocks.yaml'))
BEFORE_AFTER_PATH = os.path.join(ROOT, '10-templates-recipes', 'before-after.tsv')
FACTS_SCHEMA_PATH = os.path.join(ROOT, '02-strategy-messaging', 'facts.schema.yaml')
COPY_SLOTS_PATH = os.path.join(ROOT, '04-copy-by-block', 'copy-slots.yaml')
VOICE_SCHEMA_PATH = os.path.join(ROOT, '05-voice-editorial', 'voice.schema.yaml')
META_RULES_PATH = os.path.join(ROOT, '07-seo-geo-copy', 'meta-rules.yaml')
CLAIMS_RULES_PATH = os.path.join(ROOT, '08-russian-legal-typography', 'claims-rules.yaml')
CLAIMS_CHECK = os.path.join(HERE, 'claims_check.py')
EXIT_NO_CLAIMS = 3   # особый исход claims и check: сверка фактов не отработала
GENRES = ('landing', 'site-page', 'article', 'meta', 'geo', 'email-form')
LEVELS = ('error', 'warning', 'info')
STATUS_RANK = {'draft': 0, 'assumed': 0, 'checked': 1, 'approved': 2, 'rejected': -1}
CHROME_TOP_ROLES = {'header', 'utility'}   # шапка и служебная строка над первым экраном: ядро считается после них
PAGE_PASS = ' (страница)'                  # хвост места (where) у находок прохода страницы линтером
PLACEHOLDER_RX = re.compile(r'\[PLACEHOLDER(?::\s*([^\]]*))?\]', re.I)
BAD_PLACEHOLDER_RX = re.compile(r'\[\s*(?:заглушка|todo|tbd|xxx|плейсхолдер|placeholder\s*[^:\]\s])|lorem ipsum|\bTODO\b|'
                                r'(?<!\[)PLACEHOLDER(?!\s*[:\]])|\[PLACEHOLDER(?![^\]]*\])', re.I)
META_FIELDS = (('title', 'meta-title'), ('description', 'meta-description'), ('og_title', 'og-title'),
               ('og_description', 'og-description'), ('og_image_alt', 'og-image-alt'))
OG_TEMPLATE_FIELDS = (('kicker', 'eyebrow'), ('title', 'og-title'))
# Прозаические типы слотов — для прохода страницы линтером.
PROSE_SLOT_TYPES = {'body', 'section-lead', 'article-paragraph', 'article-lead', 'article-summary', 'geo-answer',
                    'definition', 'faq-a', 'email-body', 'case-summary', 'guarantee-text', 'objection-answer',
                    'pricing-plan-summary'}
HEADING_LEVEL = {'headline': 1, 'article-title': 1, 'section-title': 2, 'article-heading': 2, 'form-title': 2,
                 'email-heading': 2, 'card-title': 3, 'step-title': 3, 'case-title': 3, 'pricing-plan-name': 3,
                 'faq-q': 3}
# Готовое сообщение мессенджера: текст несёт ссылка действия (target.prefill плана называет его слот), на странице он
# не виден — в проекцию страницы для прохода линтером не идёт; сам слот сверяется и линтуется как любой текст.
PREFILL_SLOT_TYPE = 'messenger-prefill'
# Набор запретов по умолчанию x-never-claim-defaults схемы фактов — английская адаптация для copy deck с lang: en.
NEVER_EN = {
    'nc-counts': 'Customer, user or order counts and growth percentages without a fact with a source and a date',
    'nc-ratings': 'Ratings and stars without a fact with the platform, scale, number of reviews and snapshot date',
    'nc-trusted-by': '"Trusted by", client and partner names and logos without a fact with the client\'s written permission',
    'nc-awards-press': 'Awards, prizes, "as seen in", media logos without a fact with a link or a document',
    'nc-testimonials': 'Testimonials, quotes, names and photos of people without a fact with written permission',
    'nc-prices-terms': 'Prices, discounts, delivery times, guarantees, certifications without a fact',
    'nc-superlatives': '"Best", "No. 1", "most", "first", "leader" without a criterion and objective proof',
    'nc-comparisons': 'Comparisons with competitors and "N times" without a method, a date and a document',
    'nc-health': 'Health or healing promises (never for non-medical goods and services)',
    'nc-income': 'Promises of income, earnings or payback',
    'nc-scarcity': '"Only N left", "last places" without a live stock source',
    'nc-deadline': 'Offer deadlines and countdown timers without a real end date',
    'nc-forecast': 'Forecasts of results without a calculation and a disclaimer',
    'nc-official-approval': 'Claims of approval by public authorities ("approved by the Ministry of Health")',
    'nc-ai-people': 'AI-generated people as clients, team or reviewers; invented names and faces',
}


# ============================================================================================ общие помощники
def today_iso(s=None):
    if s:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
            raise SystemExit('--today: ГГГГ-ММ-ДД')
        return s
    return dt.date.today().isoformat()


def norm_ws(s):
    return re.sub(r'\s+', ' ', str(s or '').replace(' ', ' ').replace(' ', ' ')).strip()


def text_hash(s):
    """sha1 нормализованного текста (пробелы, NBSP), первые 12 знаков — для записи lint/claims."""
    return hashlib.sha1(norm_ws(s).encode('utf-8')).hexdigest()[:12]


def date_end(s):
    """«2026-10» → «2026-10-31» для сравнения сроков; «2026-10-31» → как есть."""
    s = str(s)
    if re.fullmatch(r'\d{4}-\d{2}', s):
        y, m = int(s[:4]), int(s[5:7])
        nxt = dt.date(y + (m == 12), (m % 12) + 1, 1)
        return (nxt - dt.timedelta(days=1)).isoformat()
    return s


def deep_dates(x, path='', found=None):
    """datetime.date из YAML без кавычек → строка ISO; пути таких мест — в found (сигнал «дата без кавычек»)."""
    if isinstance(x, dict):
        return {k: deep_dates(v, f'{path}.{k}' if path else str(k), found) for k, v in x.items()}
    if isinstance(x, list):
        return [deep_dates(v, f'{path}[{i}]', found) for i, v in enumerate(x)]
    if isinstance(x, (dt.date, dt.datetime)):
        if found is not None:
            found.append(path)
        return x.isoformat()[:10]
    return x


def load_yaml_file(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def rel_to(base_file, ref):
    """Путь ref относительно папки файла base_file (как facts_ref в copy deck)."""
    if not ref:
        return None
    if os.path.isabs(ref):
        return ref
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(base_file)), ref))


def looks_like_path(s):
    return bool(s) and bool(re.search(r'\.(ya?ml|json)$', str(s).strip(), re.I))


def cyr_share(s):
    c = len(re.findall(r'[А-Яа-яЁё]', s or ''))
    lat = len(re.findall(r'[A-Za-z]', s or ''))
    return c / (c + lat) if (c + lat) else 0.0


def words(s):
    return re.findall(r"[0-9A-Za-zА-Яа-яЁё]+(?:[-'’][0-9A-Za-zА-Яа-яЁё]+)*", s or '')


class Report:
    """Находки одной команды: tool (validate, claims, lint), level, rule (COPY-D-…, COPY-F-…, id правила copy_lint.py), where
    (путь copy deck: page/section/slot), message, fix; allowed — обходы сверки claims_allow (решение человека, не находки)."""

    def __init__(self):
        self.findings = []
        self.notes = []
        self.tools = {}
        self.allowed = []

    def add(self, tool, level, rule, where, message, fix='', **extra):
        f = {'tool': tool, 'level': level, 'rule': rule, 'where': where or '—', 'message': message, 'fix': fix}
        f.update({k: v for k, v in extra.items() if v not in (None, '', [], {})})
        self.findings.append(f)
        return f

    def count(self, level, tool=None):
        return sum(1 for f in self.findings if f['level'] == level and (tool is None or f['tool'] == tool))

    def summary(self):
        return {lv: self.count(lv) for lv in LEVELS}


# ============================================================================================ copy deck: обход
def deck_root(data):
    if isinstance(data, dict) and isinstance(data.get('copy_deck'), dict):
        return data['copy_deck']
    return data if isinstance(data, dict) else {}


def pages_of(deck):
    return [p for p in (deck.get('pages') or []) if isinstance(p, dict)]


def sections_of(page):
    return [s for s in (page.get('sections') or []) if isinstance(s, dict)]


def slots_of(section):
    return [s for s in (section.get('slots') or []) if isinstance(s, dict)]


def iter_slots(deck):
    for p in pages_of(deck):
        for s in sections_of(p):
            for sl in slots_of(s):
                yield p, s, sl, f"{p.get('page_id')}/{s.get('section_id')}/{sl.get('slot_id')}"


def variants_of(slot):
    return [v for v in (slot.get('variants') or []) if isinstance(v, dict)]


def chosen_variant(slot):
    """Выбранный вариант: chosen; без chosen — единственный вариант; иначе None."""
    vs = variants_of(slot)
    ch = slot.get('chosen')
    if ch is not None:
        for v in vs:
            if str(v.get('id')) == str(ch):
                return v
        return None
    return vs[0] if len(vs) == 1 else None


def main_variant(slot):
    """Текст, который проверяется как текст слота: выбранный вариант; без chosen при нескольких вариантах — первый
    (так же делает claims_check.py; validate при этом предупреждает COPY-D-CHOSEN); chosen на несуществующий — None."""
    v = chosen_variant(slot)
    if v is None and slot.get('chosen') is None:
        vs = variants_of(slot)
        return vs[0] if vs else None
    return v


def variant_fact_ids(slot, v):
    """Факты текста: свои fact_ids варианта (необязательное поле v1.1 — варианты одного слота опираются на разные факты),
    иначе fact_ids слота (v0). Свой список заменяет список слота, а не дополняет его."""
    if isinstance(v, dict) and isinstance(v.get('fact_ids'), list):
        return v['fact_ids']
    return (slot or {}).get('fact_ids') or []


def find_slot(deck, path):
    parts = str(path or '').split('/')
    if len(parts) < 3:
        return None
    for p in pages_of(deck):
        if str(p.get('page_id')) != parts[0]:
            continue
        for s in sections_of(p):
            if str(s.get('section_id')) != parts[1]:
                continue
            for sl in slots_of(s):
                if str(sl.get('slot_id')) == parts[2]:
                    return p, s, sl
    return None


def promise_info(deck, page):
    """(текст, вариант или None, путь-источник, объект promise) обещания страницы; from — текст слота."""
    pr = page.get('promise')
    if not isinstance(pr, dict):
        return None, None, None, None
    if pr.get('from'):
        hit = find_slot(deck, pr['from'])
        if not hit:
            return None, None, pr['from'], pr
        v = chosen_variant(hit[2])
        return (v.get('text') if v else None), v, pr['from'], pr
    v = chosen_variant(pr)
    return (v.get('text') if v else None), v, f"{page.get('page_id')}/promise", pr


def primary_cta(deck, page):
    """(путь, текст) главной кнопки: cta_primary или первый cta-label секции hero (или страницы)."""
    if page.get('cta_primary'):
        hit = find_slot(deck, page['cta_primary'])
        if hit:
            v = chosen_variant(hit[2])
            return page['cta_primary'], (v.get('text') if v else None)
        return page['cta_primary'], None
    first = None
    for s in sections_of(page):
        for sl in slots_of(s):
            if sl.get('slot_type') == 'cta-label':
                v = chosen_variant(sl)
                path = f"{page.get('page_id')}/{s.get('section_id')}/{sl.get('slot_id')}"
                if (s.get('section_role') or s.get('block') or s.get('section_id')) == 'hero':
                    return path, (v.get('text') if v else None)
                if first is None:
                    first = (path, (v.get('text') if v else None))
    return first or (None, None)


# ============================================================================================ словарь, схема, факты
def load_vocab(path=VOCAB_PATH, copy_schema=None, blocks_path=BLOCKS_PATH):
    """Словарь site v1: типы страниц (жанр), роли секций, слоты вида text (жанры — copy-slots.yaml), блоки blocks.yaml
    и статусы id (proposed — можно с пометкой, deprecated — предупреждение, out-of-scope и measurement-only — не для
    copy deck). None — файла словаря нет."""
    if not os.path.exists(path):
        return None
    ns = (load_yaml_file(path) or {}).get('namespaces') or {}
    vals = lambda key: [x for x in (ns.get(key) or {}).get('values') or [] if isinstance(x, dict) and x.get('id')]
    out = {'page_types': {x['id']: x.get('genre') for x in vals('page_type')},
           'section_roles': {x['id'] for x in vals('section_role')},
           'slot_types': {x['id']: dict(x) for x in vals('slot') if x.get('kind') == 'text'},
           'slot_kinds': {x['id']: x.get('kind') for x in vals('slot')},
           'status': {}, 'proposals': {'section_roles': set(), 'slot_types': set()}, 'blocks': {}, 'serves': {}, 'path': path}
    for key, pool in (('page_type', 'page'), ('section_role', 'role'), ('slot', 'slot'), ('block', 'block')):
        for x in vals(key):
            out['status'][(pool, x['id'])] = x.get('status') or 'active'
    out['proposals']['section_roles'] = {x['id'] for x in vals('section_role') if x.get('status') == 'proposed'}
    out['proposals']['slot_types'] = {x['id'] for x in vals('slot') if x.get('kind') == 'text' and x.get('status') == 'proposed'}
    blocks = (load_yaml_file(blocks_path) or {}).get('blocks') if os.path.exists(blocks_path) else None
    for bid, b in (blocks or {}).items() if isinstance(blocks, dict) else []:
        out['blocks'][str(bid)] = (b or {}).get('status') or 'active'
        out['serves'][str(bid)] = list((b or {}).get('serves') or [])
    if not out['blocks']:   # запасной путь: блоки словаря
        for x in vals('block'):
            out['blocks'][x['id']] = x.get('status') or 'active'
            out['serves'][x['id']] = list(x.get('serves') or [])
    try:  # жанры типа слота — copy-slots.yaml
        if os.path.exists(COPY_SLOTS_PATH):
            for x in (load_yaml_file(COPY_SLOTS_PATH) or {}).get('slot_types') or []:
                if isinstance(x, dict) and x.get('id') in out['slot_types']:
                    g = x.get('genres') or ([x['genre']] if x.get('genre') else [])
                    out['slot_types'][x['id']]['genres'] = [str(y) for y in g]
    except Exception:  # noqa: BLE001
        pass
    return out


def vocab_status(vocab, pool, ident):
    """Статус id словаря: active | proposed | deprecated | out-of-scope | measurement-only; None — id нет."""
    return (vocab or {}).get('status', {}).get((pool, ident))


def role_of_block(vocab, block):
    """Роль секции по блоку: первая роль serves блока blocks.yaml (или None)."""
    serves = (vocab or {}).get('serves', {}).get(str(block or '')) or []
    return serves[0] if serves else None


_FACTS_SCHEMA = {}


def load_facts_schema(path=FACTS_SCHEMA_PATH):
    if path not in _FACTS_SCHEMA:
        _FACTS_SCHEMA[path] = deep_dates(load_yaml_file(path) or {}) if os.path.exists(path) else {}
    return _FACTS_SCHEMA[path]


def load_copy_schema(path=SCHEMA_PATH):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


class Facts:
    """facts.yaml: факты по id и алиасам, пробелы, запреты. Семантика поиска — как в claims_check.py."""

    def __init__(self, data, path=None):
        self.data = deep_dates(data or {})
        self.path = path
        self.facts = [f for f in self.data.get('facts') or [] if isinstance(f, dict) and f.get('id')]
        self.by_id = {}
        for f in self.facts:
            self.by_id[str(f['id'])] = f
            for a in f.get('aliases') or []:
                self.by_id.setdefault(str(a), f)
        self.missing = [m for m in self.data.get('missing') or [] if isinstance(m, dict)]
        self.missing_by_id = {}
        for m in self.missing:
            self.missing_by_id[str(m.get('id'))] = m
            for a in m.get('aliases') or []:
                self.missing_by_id.setdefault(str(a), m)
        self.never = [n for n in self.data.get('never_claim') or [] if isinstance(n, dict)]

    def resolve(self, ref):
        """(факт | None, пробел | None) по ссылке fact_ids: «x», «fact:x», алиас; «missing:x» → пробел."""
        r = str(ref).strip()
        if r.startswith('missing:'):
            return None, self.missing_by_id.get(r[8:])
        r = r[5:] if r.startswith('fact:') else r
        f = self.by_id.get(r)
        if f is not None:
            return f, None
        return None, self.missing_by_id.get(r)


def load_facts(path):
    if not path:
        return None
    data = load_yaml_file(path) or {}
    if not isinstance(data, dict) or 'facts' not in data:
        raise SystemExit(f'{path}: не facts.yaml (нет ключа facts)')
    return Facts(data, path)


def claim_class_info():
    return {c['id']: c for c in load_facts_schema().get('x-claim-classes') or [] if isinstance(c, dict)}


_CC = {}


def claims_module():
    """claims_check.py как модуль (фильтр публикации фактов при выгрузке facts.md — та же семантика, что у сверки);
    None — файла нет или он не импортируется (тогда работает свой фильтр по publish_filter карты фактов)."""
    if 'm' not in _CC:
        _CC['m'] = None
        if os.path.exists(CLAIMS_CHECK):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location('claims_check_for_copydeck', CLAIMS_CHECK)
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
                _CC['m'] = m
            except Exception as e:  # noqa: BLE001
                _CC['err'] = f'{type(e).__name__}: {e}'
    return _CC['m']


def own_publish_issues(f, today, cls_info=None):
    """Свой фильтр публикации по publish_filter карты фактов (x-canvas-map facts.schema.yaml) — запасной путь, если
    claims_check.py не импортируется."""
    cls_info = cls_info if cls_info is not None else claim_class_info()
    out = []
    ver = (f.get('verification') or {}).get('status')
    classes = [c for c in f.get('claim_class') or []]
    needs_doc = any((cls_info.get(c) or {}).get('needs_document') for c in classes)
    if ver == 'unverified' or ver is None:
        out.append('verification: unverified')
    elif ver == 'stated' and needs_doc:
        out.append('verification: stated, а класс требует документа')
    perm = f.get('permission') or {}
    if perm.get('status') not in ('granted', 'not-required'):
        out.append(f'permission: {perm.get("status") or "нет"}')
    if perm.get('withdrawn'):
        out.append('разрешение отозвано')
    if perm.get('until') and date_end(perm['until']) < today:
        out.append(f'срок разрешения истёк {perm["until"]}')
    if (f.get('source') or {}).get('derivation') == 'inferred':
        out.append('derivation: inferred (вывод агента, а не факт)')
    until = (f.get('valid') or {}).get('until')
    if until and date_end(until) < today:
        out.append(f'истёк: valid.until {until}')
    review = ((f.get('legal') or {}).get('review') or {}).get('status')
    if review in ('required', 'rejected') or (any((cls_info.get(c) or {}).get('legal') == 'required' for c in classes)
                                              and review not in ('approved', 'not-needed')):
        out.append(f'legal.review: {review or "нет"} для класса с legal: required')
    return out


def publish_issues(f, today, facts=None):
    """Почему факт нельзя выгружать в «Факты» facts.md входа холста: [] — можно. Основа — claims_check.publishable_issues
    (error и COPY-F-UNVERIFIED любого уровня: publish_filter пускает «со слов» только для классов без needs_document); без
    модуля — свой фильтр."""
    m = claims_module()
    if m is not None and facts is not None:
        try:
            cf = m.Facts(facts.data, m.load_schema(), True)
            y, mo, d = (int(x) for x in today.split('-'))
            res = m.publishable_issues(f, cf, dt.date(y, mo, d))
            return [f'{rule}: {msg}' for lvl, rule, msg, _fix in res if lvl == 'error' or rule == 'COPY-F-UNVERIFIED']
        except Exception as e:  # noqa: BLE001
            _CC['err'] = f'publishable_issues: {type(e).__name__}: {e}'
    return own_publish_issues(f, today)


# ============================================================================================ схема: проверка подмножества
class SubsetValidator:
    """Проверка JSON Schema 2020-12 на подмножестве, которым написана copy-deck.schema.json: type, required,
    properties, patternProperties, additionalProperties, enum, const, pattern, minLength, minimum, minItems, maxItems,
    uniqueItems, items, $ref (#/$defs), allOf, anyOf, oneOf, булевы схемы. Нужна, когда jsonschema не установлен
    (системный python3); --selftest сверяет её с jsonschema на тех же примерах."""

    TYPES = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}

    def __init__(self, schema):
        self.root = schema

    def _ref(self, ref):
        if not ref.startswith('#/'):
            raise ValueError(f'внешняя $ref не поддержана: {ref}')
        node = self.root
        for part in ref[2:].split('/'):
            node = node[part]
        return node

    def _type_ok(self, t, x):
        if t == 'integer':
            return isinstance(x, int) and not isinstance(x, bool)
        if t == 'number':
            return isinstance(x, (int, float)) and not isinstance(x, bool)
        return isinstance(x, self.TYPES[t])

    def errors(self, x, schema=None, path=''):
        schema = self.root if schema is None else schema
        out = []
        if schema is True:
            return out
        if schema is False:
            return [(path, 'поле не допускается схемой')]
        if '$ref' in schema:
            out += self.errors(x, self._ref(schema['$ref']), path)
        for sub in schema.get('allOf') or []:
            out += self.errors(x, sub, path)
        if 'anyOf' in schema and not any(not self.errors(x, s, path) for s in schema['anyOf']):
            out.append((path, 'не подходит ни один из вариантов anyOf: ' + '; '.join(
                json.dumps(s.get('required', s), ensure_ascii=False) for s in schema['anyOf'])))
        if 'oneOf' in schema and sum(1 for s in schema['oneOf'] if not self.errors(x, s, path)) != 1:
            out.append((path, 'должен подходить ровно один вариант oneOf'))
        t = schema.get('type')
        if t:
            ts = t if isinstance(t, list) else [t]
            if not any(self._type_ok(tt, x) for tt in ts):
                return out + [(path, f'ожидался тип {"/".join(ts)}, получено {type(x).__name__}')]
        if 'const' in schema and x != schema['const']:
            out.append((path, f'значение должно быть {schema["const"]!r}'))
        if 'enum' in schema and x not in schema['enum']:
            out.append((path, f'значение {x!r} не из списка {schema["enum"]}'))
        if isinstance(x, str):
            if 'pattern' in schema and not re.search(schema['pattern'], x):
                out.append((path, f'значение {x!r} не соответствует шаблону {schema["pattern"]}'))
            if 'minLength' in schema and len(x) < schema['minLength']:
                out.append((path, f'строка короче {schema["minLength"]}'))
        if isinstance(x, (int, float)) and not isinstance(x, bool) and 'minimum' in schema and x < schema['minimum']:
            out.append((path, f'значение меньше {schema["minimum"]}'))
        if isinstance(x, list):
            if 'minItems' in schema and len(x) < schema['minItems']:
                out.append((path, f'элементов меньше {schema["minItems"]}'))
            if 'maxItems' in schema and len(x) > schema['maxItems']:
                out.append((path, f'элементов больше {schema["maxItems"]}'))
            if schema.get('uniqueItems'):
                seen = []
                for it in x:
                    k = json.dumps(it, sort_keys=True, ensure_ascii=False, default=str)
                    if k in seen:
                        out.append((path, f'повтор элемента {it!r}'))
                    seen.append(k)
            if 'items' in schema:
                for i, it in enumerate(x):
                    out += self.errors(it, schema['items'], f'{path}[{i}]')
        if isinstance(x, dict):
            for r in schema.get('required') or []:
                if r not in x:
                    out.append((path, f'нет обязательного поля «{r}»'))
            props = schema.get('properties') or {}
            pprops = schema.get('patternProperties') or {}
            for k, v in x.items():
                sub = f'{path}.{k}' if path else str(k)
                matched = False
                if k in props:
                    matched = True
                    out += self.errors(v, props[k], sub)
                for pat, ps in pprops.items():
                    if re.search(pat, str(k)):
                        matched = True
                        out += self.errors(v, ps, sub)
                if not matched and 'additionalProperties' in schema:
                    ap = schema['additionalProperties']
                    if ap is False:
                        out.append((sub, f'неизвестное поле «{k}»'))
                    elif isinstance(ap, dict):
                        out += self.errors(v, ap, sub)
        return out


def schema_errors(data, schema, use_jsonschema=True):
    """[(путь, сообщение)] и какой проверщик работал."""
    if use_jsonschema:
        try:
            import jsonschema  # noqa: F401
            from jsonschema import Draft202012Validator
            v = Draft202012Validator(schema)
            out = []
            for e in sorted(v.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path]):
                path = ''
                for p in e.absolute_path:
                    path += f'[{p}]' if isinstance(p, int) else (f'.{p}' if path else str(p))
                out.append((path, e.message))
            return out, 'jsonschema'
        except ImportError:
            pass
    return SubsetValidator(schema).errors(data), 'встроенная (подмножество JSON Schema)'


# ============================================================================================ файлы правил текста
LEN_LANG = {'ru': 'ru', 'en': 'en'}
LEN_UNIT = {'words': 'words', 'word': 'words', 'слова': 'words', 'слов': 'words', 'w': 'words',
            'chars': 'chars', 'char': 'chars', 'characters': 'chars', 'знаки': 'chars', 'знаков': 'chars', 'symbols': 'chars'}


def _len_walk(node, lang='any', unit=None, acc=None):
    """Все границы длины из узла copy-slots.yaml: {(lang, unit): [min, max]}; вьюпорты — самые широкие границы."""
    acc = {} if acc is None else acc
    if isinstance(node, dict):
        for k, v in node.items():
            ks = str(k).lower()
            if ks in LEN_LANG:
                _len_walk(v, LEN_LANG[ks], unit, acc)
            elif ks in LEN_UNIT:
                _len_walk(v, lang, LEN_UNIT[ks], acc)
            elif re.fullmatch(r'(min|max)_(words|chars|characters|знаков|слов)', ks) or re.fullmatch(r'(words|chars)_(min|max)', ks):
                parts = ks.split('_')
                b = parts[0] if parts[0] in ('min', 'max') else parts[1]
                u = LEN_UNIT.get(parts[1] if parts[0] in ('min', 'max') else parts[0], 'chars')
                _len_put(acc, lang, u, b, v)
            elif ks in ('min', 'max') and unit:
                _len_put(acc, lang, unit, ks, v)
            elif ks in ('source', 'note', 'notes', 'target', 'why'):
                continue
            else:
                _len_walk(v, lang, unit, acc)
    elif isinstance(node, list) and unit and node and all(isinstance(x, (int, float)) for x in node):
        _len_put(acc, lang, unit, 'min', node[0])
        _len_put(acc, lang, unit, 'max', node[-1])
    return acc


def _len_put(acc, lang, unit, bound, v):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return
    cur = acc.setdefault((lang, unit), [None, None])
    if bound == 'min':
        cur[0] = v if cur[0] is None else min(cur[0], v)
    else:
        cur[1] = v if cur[1] is None else max(cur[1], v)


def load_copy_slots(path):
    """copy-slots.yaml в терпимом разборе: {id: {fact_required, section_roles, genre, len}}, renames, заметки.
    Берём slot_types | slots | types (список или словарь), длины из length(s)."""
    data = load_yaml_file(path)
    notes, renames, items = [], {}, None
    if isinstance(data, dict):
        for key in ('slot_types', 'slots', 'types'):
            if key in data:
                items = data[key]
                break
        for key in ('renames', 'renamed', 'rename', 'mapping'):
            if isinstance(data.get(key), dict):
                renames.update({str(k): str(v) for k, v in data[key].items()})
    elif isinstance(data, list):
        items = data
    if isinstance(items, dict):
        items = [dict(v, id=k) if isinstance(v, dict) else {'id': k} for k, v in items.items()]
    if not items:
        return None, {}, ['copy-slots.yaml: не найден список типов слотов (slot_types / slots)']
    out = {}
    for it in items:
        if not isinstance(it, dict) or not it.get('id'):
            continue
        lens, lang_specs = {}, {}
        for key in ('length', 'lengths', 'len', 'limits'):
            if key in it:
                lens = _len_walk(it[key])
                node = it[key] if isinstance(it[key], dict) else {}
                for lg in ('ru', 'en'):  # формат copy-slots: length.<язык>: words/chars {min, target, max}, hard_*, primary
                    sp = node.get(lg) if isinstance(node.get(lg), dict) else None
                    if not sp:
                        continue
                    ls = {'primary': sp.get('primary') or ('chars' if lg == 'ru' else 'words'),
                          'provisional': bool(sp.get('provisional')), 'n_pages': sp.get('n_pages'), 'source': sp.get('source')}
                    for u in ('words', 'chars'):
                        b = sp.get(u)
                        if isinstance(b, dict):
                            ls[u] = (b.get('min'), b.get('max'))
                        h = sp.get(f'hard_{u}')
                        if isinstance(h, list) and len(h) == 2:
                            ls[f'hard_{u}'] = (h[0], h[1])
                    lang_specs[lg] = ls
                break
        out[str(it['id'])] = {'fact_required': it.get('fact_required'), 'section_roles': it.get('section_roles') or [],
                              'genre': it.get('genre') or it.get('profile'), 'len': lens, 'lang': lang_specs,
                              'exceptions': it.get('exceptions') or [], 'proposal': bool(it.get('proposal'))}
        for old in it.get('aliases') or it.get('replaces') or it.get('renamed_from') or []:
            renames.setdefault(str(old), str(it['id']))
    if not any(v['len'] for v in out.values()):
        notes.append('copy-slots.yaml: длины не распознаны (ожидались length: {ru|en: {words|chars: {min, max}}})')
    extra = {'composites': data.get('composites') if isinstance(data, dict) else None,
             'proposals': [str(x) for x in (data.get('proposals') or [])] if isinstance(data, dict) else []}
    out['__meta__'] = extra
    return out, renames, notes


VOICE_TABOO_KEY = re.compile(r'taboo|табу|dont|не_?говорим|not_say|avoid|banned|never|запрет', re.I)
VOICE_ADDR_KEY = re.compile(r'address|обращени|pronoun', re.I)
RU_FORM = {'vy': 'вы', 'ty': 'ты', 'impersonal': None}


def words_rx(term):
    """Термин в формате words линтера (06-anti-slop/02 §2.1; vocabulary.avoid голоса): «*» — продолжение основы, «ё» = «е»,
    пробел — любые пробелы; границы слова для кириллицы."""
    out, prev_space = [], False
    for ch in term.strip().lower():
        if ch.isspace():
            if not prev_space:
                out.append(r'\s+')
            prev_space = True
            continue
        prev_space = False
        if ch == '*':
            out.append('[0-9a-zа-яё]*')
        elif ch in 'её':
            out.append('[её]')
        else:
            out.append(re.escape(ch))
    tail = '' if term.strip().endswith('*') else '(?![0-9a-zа-яё])'
    return re.compile('(?<![0-9a-zа-яё])' + ''.join(out) + tail, re.I)


def load_voice(path):
    """voice.yaml (voice.schema.yaml v1): address.ru_form (vy | ty | impersonal) и exceptions, vocabulary.avoid (термины
    в формате words линтера, уровень, slot_types, unless), projections.tone_of_voice. Иной формат — терпимый разбор:
    ключи с «обращение» / «avoid», «табу», «не говорим»."""
    data = load_yaml_file(path) or {}
    out = {'taboo': [], 'address': None, 'exceptions': [], 'tone_of_voice': None, 'format': None}
    addr = data.get('address') if isinstance(data.get('address'), dict) else None
    voc = data.get('vocabulary') if isinstance(data.get('vocabulary'), dict) else None
    if addr and 'ru_form' in addr:
        out['format'] = 'F'
        out['address'] = RU_FORM.get(str(addr.get('ru_form')))
        out['exceptions'] = [str(x.get('where')) for x in addr.get('exceptions') or [] if isinstance(x, dict) and x.get('where')]
    if voc and isinstance(voc.get('avoid'), list):
        out['format'] = 'F'
        for t in voc['avoid']:
            if isinstance(t, dict) and t.get('term'):
                out['taboo'].append({'term': str(t['term']), 'lang': t.get('lang') or 'ru', 'level': t.get('level') or 'warning',
                                     'slot_types': t.get('slot_types') or [], 'unless': t.get('unless') or '', 'use_instead': t.get('use_instead') or ''})
            elif isinstance(t, str):
                out['taboo'].append({'term': t, 'lang': 'any', 'level': 'warning', 'slot_types': [], 'unless': '', 'use_instead': ''})
    tov = (data.get('projections') or {}).get('tone_of_voice') if isinstance(data.get('projections'), dict) else None
    out['tone_of_voice'] = tov or (data.get('tone_of_voice') if isinstance(data.get('tone_of_voice'), str) else None)
    if out['format'] == 'F':
        return out
    # терпимый разбор чужой формы
    taboo = []

    def walk(node, key=''):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, str(k))
        elif isinstance(node, list):
            if VOICE_TABOO_KEY.search(key):
                for x in node:
                    if isinstance(x, str) and 0 < len(x) <= 40:
                        taboo.append(x)
                    elif isinstance(x, dict):
                        for kk in ('term', 'word', 'phrase', 'text'):
                            if isinstance(x.get(kk), str):
                                taboo.append(x[kk])
                                break
            else:
                for x in node:
                    walk(x, key)
        elif isinstance(node, str) and VOICE_ADDR_KEY.search(key) and out['address'] is None:
            low = node.lower()
            out['address'] = 'вы' if re.search(r'(^|[^а-яё])вы([^а-яё]|$)', low) else ('ты' if re.search(r'(^|[^а-яё])ты([^а-яё]|$)', low) else None)
    walk(data)
    out['taboo'] = [{'term': t, 'lang': 'any', 'level': 'warning', 'slot_types': [], 'unless': '', 'use_instead': ''} for t in sorted(set(taboo))]
    out['format'] = 'generic'
    return out


META_KEYS = {'title': 'title', 'meta-title': 'title', 'meta_title': 'title', 'description': 'description',
             'meta-description': 'description', 'meta_description': 'description', 'og-title': 'og_title',
             'og_title': 'og_title', 'og-description': 'og_description', 'og_description': 'og_description'}


def load_meta_rules(path):
    """meta-rules.yaml: limits (ориентиры длины по полям и языкам: write [min, max], info_over, warning_over,
    warning_under, words_min) и checks_outside_linter (проверки между полями и страницами: meta-x-…). Правила для
    линтера из того же файла copy_lint.py подхватывает сам (profiles.yaml → external_rules).
    → {'limits': {поле: {язык: {...}}}, 'checks': {id: {...}}, 'format': 'G' | 'generic' | None}."""
    data = load_yaml_file(path) or {}
    out = {'limits': {}, 'checks': {}, 'format': None}
    lim = data.get('limits') if isinstance(data.get('limits'), dict) else {}
    for key, node in lim.items():
        fld = META_KEYS.get(str(key).lower())
        if not fld or not isinstance(node, dict):
            continue
        for lang, spec in node.items():
            if str(lang) in ('ru', 'en') and isinstance(spec, dict):
                keep = {k: v for k, v in spec.items() if k in ('write', 'info_over', 'warning_over', 'warning_under', 'words_min')}
                if keep:
                    out['limits'].setdefault(fld, {})[str(lang)] = keep
    for c in data.get('checks_outside_linter') or []:
        if isinstance(c, dict) and c.get('id'):
            out['checks'][str(c['id'])] = c
    if out['limits'] or out['checks']:
        out['format'] = 'G'
        return out
    # запасной разбор: поле → {min, max} где угодно в файле
    def grab(node):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            fld = META_KEYS.get(str(k).lower())
            if fld and isinstance(v, dict):
                lens = _len_walk(v, unit='chars')
                for (lang, unit), (a, b) in lens.items():
                    if unit == 'chars':
                        spec = out['limits'].setdefault(fld, {}).setdefault('ru' if lang == 'any' else lang, {})
                        if b is not None:
                            spec['warning_over'] = b
                        if a is not None:
                            spec['warning_under'] = a
            elif isinstance(v, dict) and str(k) != 'rules':
                grab(v)
    grab(data)
    out['format'] = 'generic' if out['limits'] else None
    return out


def plan_og_fields(deck, ctx, page):
    """Поля OG, заведённые у страницы слотами плана (page_slots.text: og-title, og-description): {'og_title', …}. None —
    плана нет, он не читается или он о другой странице: тогда ожидаются оба поля. Страница без OG-слотов в плане
    (служебная: 404, политика) OG не ждёт."""
    pp = plan_path_of(deck, ctx) if ctx is not None else None
    if not pp:
        return None
    cache = ctx.__dict__.setdefault('_plan_docs', {})
    if pp not in cache:
        try:
            cache[pp] = deep_dates(load_yaml_file(pp) or {})
        except Exception:  # noqa: BLE001 — о нечитаемом плане говорит сверка стыка (COPY-D-PLAN)
            cache[pp] = None
    plan = cache[pp]
    if not isinstance(plan, dict) or str((plan.get('page') or {}).get('id') or '') not in (str(page.get('page_id')), str(page.get('site_page_id'))):
        return None
    return {META_SLOT_FIELD[str(t.get('slot'))] for t in ((plan.get('page_slots') or {}).get('text') or [])
            if isinstance(t, dict) and str(t.get('slot')) in ('og-title', 'og-description')}


def _meta_checks(deck, mr, rep, final, ctx=None):
    """Проверки мета между полями и страницами по checks_outside_linter (id meta-x-…) и ориентиры длины limits из meta-rules.yaml."""
    T = 'validate'
    checks = mr.get('checks') or {}
    lang = (deck.get('lang') or 'ru').split('-')[0]

    def lvl(cid, default):
        return str((checks.get(cid) or {}).get('level') or default)
    titles, descs = {}, {}
    for page in pages_of(deck):
        if (page.get('status') or 'draft') == 'rejected':
            continue
        pid = str(page.get('page_id'))
        meta = page.get('meta') or {}
        published = final or page.get('status') == 'approved'
        t, d = norm_ws(meta.get('title')), norm_ws(meta.get('description'))
        for k, val in (('title', t), ('description', d)):
            if not val:   # мета — ворота публикации (--final); у утверждённой страницы — предупреждение, у черновика — справка
                rep.add(T, lvl('meta-x-missing', 'error') if final else ('warning' if published else 'info'), 'meta-x-missing', f'{pid}/meta/{k}',
                        f'нет meta.{k}' + ('' if final else ' — заполнить до публикации (validate --final)'), 'meta-rules.yaml checks_outside_linter; шаблоны — templates.' + str(page.get('page_type') or ''))
        # OG сверяется с планом: какие OG-слоты у страницы есть, те и ждём; с checked — чтобы пропуск был виден до утверждения
        og_plan = plan_og_fields(deck, ctx, page)
        og_miss = [k for k in ('og_title', 'og_description') if (og_plan is None or k in og_plan) and not norm_ws(meta.get(k))]
        if og_miss and (final or page.get('status') in ('checked', 'approved')):
            rep.add(T, lvl('meta-x-og-missing', 'warning'), 'meta-x-og-missing', f'{pid}/meta', 'нет ' + ' и '.join(og_miss), 'Картинка OG — ai-media 10/01 §7; теги — site.')
        if t:
            titles.setdefault(t.lower(), []).append(pid)
        if d:
            descs.setdefault(d.lower(), []).append(pid)
        if t and d and (d.lower() == t.lower() or d.lower().startswith(t.lower())):
            rep.add(T, lvl('meta-x-desc-equals-title', 'warning'), 'meta-x-desc-equals-title', f'{pid}/meta/description', 'description совпадает с title или начинается с него', 'description — что внутри страницы + факт.')
        for k, _st in META_FIELDS:
            val = norm_ws(meta.get(k))
            if len(words(val)) >= 3:
                share = cyr_share(val)
                if (lang == 'ru' and share < 0.3) or (lang == 'en' and share > 0.3):
                    rep.add(T, lvl('meta-x-lang-mismatch', 'warning'), 'meta-x-lang-mismatch', f'{pid}/meta/{k}', f'язык мета не совпадает с языком страницы ({lang})', '')
        for fld, bylang in (mr.get('limits') or {}).items():
            val = norm_ws(meta.get(fld))
            spec = bylang.get(lang) or bylang.get('ru') or {}
            if not val or not spec:
                continue
            n = len(val)
            where = f'{pid}/meta/{fld}'
            if spec.get('warning_over') is not None and n > spec['warning_over']:
                rep.add(T, 'warning', 'COPY-D-META-LEN', where, f'{n} знаков > {spec["warning_over"]} (limits meta-rules.yaml)', 'Главное — в первых 55 знаках; сократите.')
            elif spec.get('info_over') is not None and n > spec['info_over']:
                rep.add(T, 'info', 'COPY-D-META-LEN', where, f'{n} знаков > {spec["info_over"]} (limits meta-rules.yaml): хвост обрежется в выдаче', '')
            if spec.get('warning_under') is not None and n < spec['warning_under']:
                rep.add(T, 'warning', 'COPY-D-META-LEN', where, f'{n} знаков < {spec["warning_under"]} (limits meta-rules.yaml)', '')
            w = spec.get('write')
            if isinstance(w, list) and len(w) == 2 and not (w[0] <= n <= w[1]):
                rep.add(T, 'info', 'COPY-D-META-LEN', where, f'{n} знаков вне ориентира генерации {w[0]}–{w[1]} (limits meta-rules.yaml)', '')
            if spec.get('words_min') and len(words(val)) < spec['words_min']:
                rep.add(T, 'info', 'COPY-D-META-LEN', where, f'слов меньше {spec["words_min"]} (limits meta-rules.yaml)', '')
    for (dups, cid, default, fld) in ((titles, 'meta-x-duplicate-title', 'error', 'title'), (descs, 'meta-x-duplicate-description', 'warning', 'description')):
        for _txt, pids in dups.items():
            for pid in pids[1:]:
                rep.add(T, lvl(cid, default), cid, f'{pid}/meta/{fld}', f'meta.{fld} совпадает со страницей {pids[0]}', 'У каждой страницы своя мета.')


def load_claims_rules_ids(path):
    data = load_yaml_file(path) or {}
    return {str(r.get('id')) for r in data.get('rules') or [] if isinstance(r, dict) and r.get('id')}


# ============================================================================================ validate
def effective_genre(deck, page, section, slot_type, lint_profile, vocab):
    """Жанр слота (x-claims-map): lint.profile-жанр → section.genre → жанр типа слота, если он единственный →
    page.genre → жанр page_type по словарю → landing. Возвращает (жанр, профиль-не-жанр или '')."""
    prof = str(lint_profile or '')
    if prof in GENRES:
        return prof, ''
    if section and section.get('genre') in GENRES:
        return section['genre'], prof
    st = (vocab or {}).get('slot_types', {}).get(slot_type or '') if vocab else None
    if slot_type and (slot_type.startswith(('meta-', 'og-'))):
        return 'meta', prof
    if slot_type and slot_type.startswith('email-'):
        return 'email-form', prof
    if st and isinstance(st.get('genres'), list) and len(st['genres']) == 1:
        return st['genres'][0], prof
    if page and page.get('genre') in GENRES:
        return page['genre'], prof
    pt = (vocab or {}).get('page_types', {}).get((page or {}).get('page_type')) if vocab else None
    if pt in GENRES:
        return pt, prof
    return 'landing', prof


def meta_variant_for(meta, key):
    """Вариант meta.variants.<поле>, совпадающий с выбранным текстом meta.<поле> (или None)."""
    mv = meta.get('variants') if isinstance(meta.get('variants'), dict) else {}
    cur = norm_ws(meta.get(key))
    return next((v for v in mv.get(key) or [] if isinstance(v, dict) and cur and norm_ws(v.get('text')) == cur), None)


def meta_alternatives(meta, key):
    """Живые альтернативы мета (2–3 варианта title): не rejected, с текстом, не равные выбранному meta.<поле>."""
    mv = meta.get('variants') if isinstance(meta.get('variants'), dict) else {}
    cur = norm_ws(meta.get(key))
    return [v for v in mv.get(key) or [] if isinstance(v, dict) and v.get('status') != 'rejected'
            and norm_ws(v.get('text')) and norm_ws(v.get('text')) != cur]


def slot_alternatives(slot):
    """Живые варианты слота, кроме проверяемого как текст слота (main_variant): для --all-variants."""
    ch = main_variant(slot)
    return [v for v in variants_of(slot) if v is not ch and v.get('status') != 'rejected' and str(v.get('text') or '').strip()]


def text_units(deck, page, include_meta=True, all_variants=False):
    """Все тексты страницы, которые идут на страницу или в пакет: слоты, обещание (своё), мета, OG-шаблон.
    → [{path, kind, slot_type, text, variant, chosen, slot, section, fact_ids}]; kind: slot | promise | meta | og;
    chosen — выбранный текст (при all_variants к нему добавляются живые альтернативы с chosen: False);
    fact_ids — свои факты варианта, иначе факты слота (variant_fact_ids)."""
    out = []
    pid = page.get('page_id')
    for s in sections_of(page):
        for sl in slots_of(s):
            ch = main_variant(sl)
            vs = ([ch] if ch else []) + (slot_alternatives(sl) if all_variants else [])
            for v in vs:
                out.append({'path': f"{pid}/{s.get('section_id')}/{sl.get('slot_id')}", 'kind': 'slot',
                            'slot_type': sl.get('slot_type'), 'text': str(v.get('text') or ''), 'variant': v.get('id'),
                            'chosen': v is ch, 'slot': sl, 'section': s, 'fact_ids': variant_fact_ids(sl, v)})
    pr = page.get('promise')
    if isinstance(pr, dict) and not pr.get('from'):
        ch = main_variant(pr)
        vs = ([ch] if ch else []) + (slot_alternatives(pr) if all_variants else [])
        for v in vs:
            out.append({'path': f'{pid}/promise', 'kind': 'promise', 'slot_type': 'subheadline',
                        'text': str(v.get('text') or ''), 'variant': v.get('id'), 'chosen': v is ch, 'slot': pr,
                        'section': None, 'fact_ids': variant_fact_ids(pr, v)})
    if include_meta:
        meta = page.get('meta') or {}
        for k, st in META_FIELDS:
            if meta.get(k):
                out.append({'path': f'{pid}/meta/{k}', 'kind': 'meta', 'slot_type': st, 'text': str(meta[k]),
                            'variant': 'meta', 'chosen': True, 'slot': None, 'section': None,
                            'fact_ids': variant_fact_ids(meta, meta_variant_for(meta, k))})
            if all_variants:  # альтернативы мета (2–3 варианта title) тоже показываются людям в тесте
                for v in meta_alternatives(meta, k):
                    out.append({'path': f'{pid}/meta/{k}', 'kind': 'meta', 'slot_type': st, 'text': str(v['text']),
                                'variant': str(v.get('id')), 'chosen': False, 'slot': None, 'section': None,
                                'fact_ids': variant_fact_ids(meta, v)})
        og = page.get('og_template') or {}
        for k, st in OG_TEMPLATE_FIELDS:
            if og.get(k):
                out.append({'path': f'{pid}/og_template/{k}', 'kind': 'og', 'slot_type': st, 'text': str(og[k]),
                            'variant': 'a', 'chosen': True, 'slot': None, 'section': None, 'fact_ids': og.get('fact_ids') or []})
    return out


class Ctx:
    """Окружение проверки: пути к файлам (переопределяются в --selftest), загруженные словари и правила."""

    def __init__(self, deck_path=None, facts=None, today=None, vocab_path=VOCAB_PATH, copy_slots_path=None,
                 voice_schema_path=VOICE_SCHEMA_PATH, meta_rules_path=META_RULES_PATH, claims_rules_path=CLAIMS_RULES_PATH,
                 schema_path=SCHEMA_PATH, plan_path=None):
        self.deck_path = deck_path
        self.plan_path = plan_path
        self.facts = facts
        self.today = today or today_iso()
        self.schema = load_copy_schema(schema_path)
        self.vocab = load_vocab(vocab_path, self.schema)
        self.copy_slots_path = copy_slots_path
        self.voice_schema_path = voice_schema_path
        self.meta_rules_path = meta_rules_path
        self.claims_rules_path = claims_rules_path
        self.final = False
        self.meta_rules = None
        if meta_rules_path and os.path.exists(meta_rules_path):
            try:
                self.meta_rules = load_meta_rules(meta_rules_path)
            except Exception as e:  # noqa: BLE001
                self.meta_rules = {'limits': {}, 'checks': {}, 'format': None, 'error': str(e)}


def validate(data, ctx, rep=None, final=False, use_jsonschema=True, fresh=None, skip_fact_checks=False):
    """Проверка формата и смысловых правил copy deck. fresh — свежие итоги claims и lint по путям (из check);
    skip_fact_checks — сверка отработала в той же команде: ссылки и публикуемость фактов и список обходов — у неё."""
    rep = rep or Report()
    T = 'validate'
    ctx.final = final
    found_dates = []
    data = deep_dates(data, found=found_dates)
    if found_dates:
        rep.add(T, 'info', 'COPY-D-DATE-UNQUOTED', found_dates[0], f'даты без кавычек ({len(found_dates)}): YAML читает их как дату',
                'Пишите даты строкой в кавычках: date: "ГГГГ-ММ-ДД".')
    if not isinstance(data, dict) or not isinstance(data.get('copy_deck'), dict):
        if isinstance(data, dict) and 'pages' in data:
            rep.add(T, 'error', 'COPY-D-ROOT', '—', 'нет корня copy_deck: страницы лежат на верхнем уровне',
                    'Оберните документ в copy_deck: {…} (формат v0 и v1).')
        else:
            rep.add(T, 'error', 'COPY-D-ROOT', '—', 'это не copy deck: нет ключа copy_deck', 'Формат — 10-templates-recipes/copy-deck.schema.json.')
        return rep
    # ---- схема
    errs, engine = schema_errors(data, ctx.schema, use_jsonschema)
    rep.tools['validate'] = {'schema_engine': engine}
    for path, msg in errs[:200]:
        rep.add(T, 'error', 'COPY-D-SCHEMA', path.replace('copy_deck.', '') or '—', msg,
                'Поля и типы — copy-deck.schema.json; поля v0 не переименовывать.')
    deck = data['copy_deck']
    vocab = ctx.vocab
    if vocab is None:
        rep.add(T, 'warning', 'COPY-D-RULES-MISSING', '—', f'словарь site не найден: {VOCAB_PATH}', 'Типы страниц, секций, слотов и блоков не проверены.')
    # ---- id, ссылки, статусы
    page_ids = set()
    for page in pages_of(deck):
        pid = str(page.get('page_id'))
        if pid in page_ids:
            rep.add(T, 'error', 'COPY-D-ID-DUP', pid, f'повтор page_id «{pid}»', 'id страницы уникален в deck.')
        page_ids.add(pid)
        _validate_page(deck, page, ctx, rep, final, fresh, vocab)
    # ---- факты
    facts = ctx.facts
    if facts is None:
        used = [p for _pg, _s, sl, p in iter_slots(deck) if sl.get('fact_ids')]
        if used:
            rep.add(T, 'error', 'COPY-D-FACTS-MISSING', used[0],
                    f'в слотах есть fact_ids ({len(used)}), а facts.yaml не найден (facts_ref: {deck.get("facts_ref")!r})',
                    'Укажите facts_ref от папки copy deck или --facts.')
        elif any(PLACEHOLDER_RX.search(u['text']) for pg in pages_of(deck) for u in text_units(deck, pg)):
            rep.add(T, 'info', 'COPY-D-FACTS-MISSING', '—', 'facts.yaml не подключён: пробелы [PLACEHOLDER] не сверены с missing[]', '')
    else:  # ссылки и публикуемость фактов check берёт у claims_check.py; пробелы (missing_ids, fallback) — всегда здесь
        _validate_facts(deck, ctx, rep, refs_and_publish=not skip_fact_checks)
        _validate_examples(deck, ctx, rep)
    # ---- обходы сверки claims_allow: неверная запись — не обход; --final перечисляет обходы публикации (у check --final
    # их перечисляет сверка — обойдённые находки с фрагментом)
    for hpath, holder, _kind in claims_allow_holders(deck):
        for e, why in claims_allow_of(holder, facts)[1]:
            rep.add(T, 'warning', 'COPY-D-CLAIMS-ALLOW', hpath, f'запись claims_allow «{e["rule"] or "—"}» — не обход: {why}',
                    'Обход — COPY-F-CLASS, COPY-F-NUM (число без факта и несовпавшее) или COPY-F-NUM-MISMATCH, с reason (у числа — '
                    'fact:<id> или почему это не утверждение) и by (заказчик или аналитик); value (число) или fragment называют, '
                    'что именно снято; иначе — правка текста или facts.yaml.')
    if final and not skip_fact_checks:
        rep.allowed += claims_allow_listed(deck, facts)
    _validate_wave2(deck, ctx, rep)
    _validate_language(deck, ctx, rep)
    _validate_plan(deck, ctx, rep)
    return rep


def _validate_examples(deck, ctx, rep):
    """Демо-данные (example: true у файла фактов или факта): на макете допустимы, в публикацию не идут — с --final
    error COPY-D-EXAMPLE, без него — info (один раз на факт)."""
    facts = ctx.facts
    lvl = 'error' if ctx.final else 'info'
    seen = set()
    for page in pages_of(deck):
        if (page.get('status') or 'draft') == 'rejected':
            continue
        for u in text_units(deck, page):
            for ref in u['fact_ids']:
                f, _m = facts.resolve(ref)
                if f is None or f['id'] in seen or not (f.get('example') or facts.data.get('example')):
                    continue
                seen.add(f['id'])
                rep.add('validate', lvl, 'COPY-D-EXAMPLE', u['path'], f"fact:{f['id']} — демо-данные (example: true" + (' у файла фактов' if facts.data.get('example') and not f.get('example') else '') + ')'
                        + (': публикация с демо-фактом запрещена' if ctx.final else ': на макете допустимо, в публикацию не идёт'),
                        'Замените факт настоящим с источником (факты заказчика) или уберите утверждение до публикации.')


def plan_path_of(deck, ctx):
    """План страницы для сверки стыка: --plan (ctx.plan_path) или page_plan_ref от папки copy deck; None — нет."""
    if getattr(ctx, 'plan_path', None):
        return ctx.plan_path
    ref = deck.get('page_plan_ref')
    if ref and looks_like_path(ref) and ctx.deck_path:
        p = rel_to(ctx.deck_path, ref)
        return p if p and os.path.exists(p) else None
    return None


def plan_text_slots(section):
    """Текстовые слоты секции плана: [{id, slot, anatomy, group, intent, variants, …}]."""
    return [x for x in ((section.get('slots') or {}).get('text') or []) if isinstance(x, dict) and x.get('id')]


def plan_binds(section_or_page):
    """fact:<id> и missing:<id> слотов данных по id текстового слота (binds): {slot_id: [ref, …]}."""
    out = {}
    for d in ((section_or_page.get('slots') or section_or_page.get('page_slots') or {}).get('data') or []):
        if isinstance(d, dict) and d.get('fact'):
            for b in d.get('binds') or []:
                out.setdefault(str(b), [])
                if d['fact'] not in out[str(b)]:
                    out[str(b)].append(d['fact'])
    return out


def plan_pages(deck, plan_id):
    """Страницы copy deck, которые стоят на плане: страница плана (page_id — id плана) и образцы шаблона коллекции
    (свой page_id, site_page_id — id плана шаблона). Страница ищется по site_page_id, затем по page_id."""
    return [p for p in pages_of(deck) if str(p.get('site_page_id') or '') == plan_id or str(p.get('page_id')) == plan_id]


def plan_hierarchy_gap(plan):
    """Иерархий сообщений у страницы больше одной (refs.hierarchy плана), а copy deck несёт одну. Вторая иерархия
    уместна у вариантной страницы — page.first_screen.variant_map плана подставляет варианты первого экрана по источнику
    трафика; у страницы без вариантов план говорит, как уровни осведомлённости сведены в один, — page.awareness_basis.rule.
    → текст находки, если нет ни вариантов, ни правила; иначе None."""
    hs = [h for h in ((plan.get('refs') or {}).get('hierarchy') or []) if isinstance(h, str) and h.strip()]
    pl = plan.get('page') if isinstance(plan.get('page'), dict) else {}
    fs = pl.get('first_screen') if isinstance(pl.get('first_screen'), dict) else {}
    vm = fs.get('variant_map') if isinstance(fs.get('variant_map'), dict) else {}
    ab = pl.get('awareness_basis') if isinstance(pl.get('awareness_basis'), dict) else {}
    if len(hs) > 1 and not vm.get('variants') and not norm_ws(ab.get('rule')):
        return (f'иерархий сообщений у страницы {len(hs)} (refs.hierarchy плана), а copy deck несёт одну: вариантов первого '
                'экрана (page.first_screen.variant_map) нет, правила сведения уровней (page.awareness_basis.rule) в плане нет')
    return None


HIERARCHY_FIX = ('Вторая иерархия — у вариантной страницы: варианты первого экрана в page.first_screen.variant_map плана; у '
                 'страницы без вариантов план называет правило сведения уровней одной строкой — page.awareness_basis.rule.')


def _validate_plan(deck, ctx, rep):
    """Стык copy deck с планом страницы (x-site-map): page_id, page_type, секции (id, роль, блок), текстовые слоты (id,
    слот словаря, анатомия, группа), порядок секций — у каждой страницы, которая стоит на плане (plan_pages: страница
    плана и образцы шаблона коллекции); слоты плана без текста — у страницы плана; иерархии плана (plan_hierarchy_gap).
    План не найден — warning, если page_plan_ref задан."""
    T = 'validate'
    pp = plan_path_of(deck, ctx)
    if not pp:
        if deck.get('page_plan_ref'):
            rep.add(T, 'warning', 'COPY-D-PLAN', '—', f"page_plan_ref «{deck.get('page_plan_ref')}» не найден: стык с планом не сверен", 'Путь от папки copy deck (или --plan).')
        return
    try:
        plan = deep_dates(load_yaml_file(pp) or {})
    except Exception as e:  # noqa: BLE001
        rep.add(T, 'error', 'COPY-D-PLAN', '—', f'план не читается: {e}', '')
        return
    pl = plan.get('page') or {}
    plan_id = str(pl.get('id') or '')
    pages = plan_pages(deck, plan_id)
    rep.tools.setdefault('validate', {})['page_plan'] = pp
    if not pages:
        rep.add(T, 'error', 'COPY-D-PLAN', '—', f'в copy deck нет страницы page.id плана «{plan_id}»',
                'page_id = page.id плана (каркас — copydeck.py skeleton); у страницы-образца шаблона коллекции id плана — в site_page_id.')
        return
    gap = plan_hierarchy_gap(plan)
    if gap:
        rep.add(T, 'warning', 'COPY-D-HIERARCHY', str(pages[0].get('page_id')), gap, HIERARCHY_FIX)
    total = {'sections': 0, 'slots': 0, 'plan_text_slots_without_text': 0}
    for page in pages:
        for k, n in zip(total, _stitch_page(page, plan, ctx, rep)):
            total[k] += n
    rep.tools['validate']['plan_stitch'] = total


def _stitch_page(page, plan, ctx, rep):
    """Стык одной страницы copy deck с планом. Образец шаблона коллекции (page_id — не id плана) несёт те слоты шаблона,
    что есть у записи: слоты плана без текста у него не находка. → (сверено секций, сверено слотов, текстовых слотов
    плана без текста)."""
    T = 'validate'
    pl = plan.get('page') or {}
    pid = str(page.get('page_id'))
    sample = pid != str(pl.get('id') or '')
    if pl.get('page_type') and page.get('page_type') != pl.get('page_type'):
        rep.add(T, 'error', 'COPY-D-PLAN', pid, f"page_type «{page.get('page_type')}» ≠ page_type плана «{pl.get('page_type')}»", '')
    if (page.get('status') or 'draft') == 'approved' and plan.get('status') != 'approved':
        rep.add(T, 'error', 'COPY-D-PLAN', pid, f"страница утверждена, а план — {plan.get('status') or 'без статуса'}", 'Закрытый файл не опирается на открытый: сначала утверждается план.')
    psecs = {str(x.get('id')): x for x in plan.get('sections') or [] if isinstance(x, dict) and x.get('id')}
    order = [str(x.get('id')) for x in plan.get('sections') or [] if isinstance(x, dict)]
    n_sec = n_slot = 0
    seen_slots = set()
    for s in sections_of(page):
        sid = str(s.get('section_id'))
        ps = psecs.get(sid)
        where = f'{pid}/{sid}'
        if ps is None:
            rep.add(T, 'error', 'COPY-D-PLAN', where, f'секции «{sid}» нет в плане', 'section_id = id секции плана; новая секция — правка плана (этап page-plan).')
            continue
        n_sec += 1
        for fld, pv in (('section_role', ps.get('role')), ('site_section_id', sid), ('block', ps.get('block'))):
            if s.get(fld) not in (None, '') and pv and str(s.get(fld)) != str(pv):
                rep.add(T, 'error', 'COPY-D-PLAN', where, f"{fld} «{s.get(fld)}» ≠ плана «{pv}»", 'Поле стыка берётся из плана (x-site-map).')
        pslots = {str(x['id']): x for x in plan_text_slots(ps)}
        for sl in slots_of(s):
            slid = str(sl.get('slot_id'))
            psl = pslots.get(slid)
            if psl is None:
                rep.add(T, 'error', 'COPY-D-PLAN', f'{where}/{slid}', f'текстового слота «{slid}» нет в секции плана', 'slot_id = id текстового слота плана; новый слот — правка плана.')
                continue
            n_slot += 1
            seen_slots.add((sid, slid))
            for fld, pv in (('slot_type', psl.get('slot')), ('site_slot_id', psl.get('anatomy') or slid), ('group', psl.get('group'))):
                if sl.get(fld) not in (None, '') and pv and str(sl.get(fld)) != str(pv):
                    rep.add(T, 'error', 'COPY-D-PLAN', f'{where}/{slid}', f"{fld} «{sl.get(fld)}» ≠ плана «{pv}»", 'Поле стыка берётся из плана (x-site-map).')
    miss = [] if sample else [(sid, str(x['id'])) for sid, ps in psecs.items() for x in plan_text_slots(ps) if (sid, str(x['id'])) not in seen_slots]
    if miss:
        rep.add(T, 'error' if ctx.final else 'warning', 'COPY-D-PLAN', pid,
                f"текстовых слотов плана без текста в copy deck: {len(miss)} ({', '.join(f'{a}/{b}' for a, b in miss[:6])}{' …' if len(miss) > 6 else ''})",
                'У каждого текстового слота утверждённого плана до передачи в дизайн есть текст (каркас — copydeck.py skeleton).')
    got = [str(s.get('section_id')) for s in sections_of(page) if str(s.get('section_id')) in psecs]
    if got != [x for x in order if x in got]:
        rep.add(T, 'warning', 'COPY-D-PLAN', pid, 'порядок секций copy deck не совпадает с планом', 'Порядок секций — порядок плана.')
    return n_sec, n_slot, len(miss)


def _status_of(v):
    return (v or {}).get('status') or 'draft'


VOCAB_POOL_NAME = {'page': 'page_type', 'role': 'section_role', 'slot': 'slot'}


def _vocab_check(rep, vocab, pool, ident, where, field):
    """id словаря site: нет — error; out-of-scope и measurement-only — error (не для copy deck); deprecated — warning;
    proposed — info (можно с пометкой)."""
    st = vocab_status(vocab, pool, ident)
    ns = VOCAB_POOL_NAME[pool]
    if st is None:
        rep.add('validate', 'error', 'COPY-D-VOCAB', where, f'{field} «{ident}» нет в словаре site ({ns})',
                'id — из kb/site/02-site-types/vocabulary.yaml; нового id в словаре нет — вопрос владельцу словаря (site).')
    elif st in ('out-of-scope', 'measurement-only'):
        rep.add('validate', 'error', 'COPY-D-VOCAB', where, f'{field} «{ident}» — статус словаря {st}: не для copy deck', '')
    elif st == 'deprecated':
        rep.add('validate', 'warning', 'COPY-D-VOCAB', where, f'{field} «{ident}» устарел в словаре site (deprecated)', 'Замена — replaced_by в словаре.')
    elif st == 'proposed':
        rep.add('validate', 'info', 'COPY-D-VOCAB', where, f'{field} «{ident}» — предложение словаря site (proposed)', '')


def _validate_block(rep, vocab, s, where):
    """block секции — id блока blocks.yaml (block плана); роль секции — в section_role; блока нет — поля нет."""
    b = s.get('block')
    if b is None or not vocab or not vocab.get('blocks'):
        return
    if not str(b).strip():
        rep.add('validate', 'warning', 'COPY-D-BLOCK', where, 'пустой block', 'Блок в плане не выбран — уберите поле.')
        return
    st = vocab['blocks'].get(str(b))
    if st is None:
        role_like = str(b) in vocab['section_roles']
        rep.add('validate', 'error', 'COPY-D-BLOCK', where, f'block «{b}» нет в blocks.yaml' + (' — это роль секции' if role_like else ''),
                ('Роль — в section_role; ' if role_like else '') + 'block — id блока каталога (block секции плана) или без поля.')
    elif st in ('measurement-only', 'out-of-scope'):
        rep.add('validate', 'error', 'COPY-D-BLOCK', where, f'block «{b}» — статус {st}: не для страницы', '')


def _validate_page(deck, page, ctx, rep, final, fresh, vocab):
    T = 'validate'
    pid = str(page.get('page_id'))
    ptype = page.get('page_type')
    if vocab and ptype:
        _vocab_check(rep, vocab, 'page', ptype, pid, 'page_type')
    pstatus = page.get('status') or 'draft'
    rules = (ctx.schema.get('x-status-rules') or {})
    prules = (rules.get('page') or {}).get(pstatus, {})
    for f in prules.get('page_requires') or []:
        if f not in page or page.get(f) in (None, '', [], {}):
            if f == 'meta' and not final:   # мета — ворота публикации (validate --final), а не утверждения текстов
                rep.add(T, 'warning', 'COPY-D-META', pid, f'страница {pstatus}: нет мета — заполнить до публикации',
                        'meta: {title, description, og_title, og_description}; ворота публикации — copydeck.py validate --final.')
                continue
            rep.add(T, 'error', 'COPY-D-STATUS', pid, f'страница {pstatus}: нет поля «{f}»', 'Требования статусов — x-status-rules схемы.')
    if pstatus == 'rejected':
        return
    sec_ids = set()
    chosen_status = []
    for s in sections_of(page):
        sid = str(s.get('section_id'))
        if sid in sec_ids:
            rep.add(T, 'error', 'COPY-D-ID-DUP', f'{pid}/{sid}', f'повтор section_id «{sid}» на странице', 'id секции уникален на странице (= id секции плана).')
        sec_ids.add(sid)
        role = s.get('section_role')
        if vocab:
            if role:
                _vocab_check(rep, vocab, 'role', role, f'{pid}/{sid}', 'section_role')
            else:
                guess = role_of_block(vocab, s.get('block')) or (sid if sid in vocab['section_roles'] else None)
                rep.add(T, 'info', 'COPY-D-ROLE', f'{pid}/{sid}', 'нет section_role' + (f' (по block/id — «{guess}»)' if guess else ''),
                        'Проставьте section_role = role секции плана (claims_check.py берёт роль секции для use.section_roles фактов).')
            _validate_block(rep, vocab, s, f'{pid}/{sid}')
        if not s.get('message') and (role or '') not in ('footer', 'contacts'):
            rep.add(T, 'info', 'COPY-D-MESSAGE', f'{pid}/{sid}', 'у секции нет message (опоры иерархии)', 'message — одна фраза из иерархии сообщений (x-copy-deck-map схемы смысла).')
        slot_ids = set()
        faq_q = faq_a = 0
        for sl in slots_of(s):
            slid = str(sl.get('slot_id'))
            path = f'{pid}/{sid}/{slid}'
            if slid in slot_ids:
                rep.add(T, 'error', 'COPY-D-ID-DUP', path, f'повтор slot_id «{slid}» в секции', 'id слота уникален в секции (ключ [slot_id] в copy.md).')
            slot_ids.add(slid)
            st = sl.get('slot_type')
            faq_q += st == 'faq-q'
            faq_a += st == 'faq-a'
            if vocab and st:
                if st not in vocab['slot_types'] and vocab_status(vocab, 'slot', st):
                    rep.add(T, 'error', 'COPY-D-VOCAB', path, f'slot_type «{st}» — слот словаря site вида {vocab["slot_kinds"].get(st)}, а не text',
                            'В copy deck — только слоты вида text; медиа, данные и действия — в плане страницы.')
                else:
                    _vocab_check(rep, vocab, 'slot', st, path, 'slot_type')
            v = _validate_slot(deck, page, s, sl, path, ctx, rep, final, fresh, pstatus)
            chosen_status.append((path, _status_of(v) if v else None))
        if faq_q != faq_a and faq_q and faq_a:
            rep.add(T, 'warning', 'COPY-D-FAQ-PAIRS', f'{pid}/{sid}', f'вопросов FAQ {faq_q}, ответов {faq_a}', 'У каждого faq-q — свой faq-a (group: q1…).')
    # ---- обещание
    ptext, pv, psrc, pr = promise_info(deck, page)
    genre = effective_genre(deck, page, None, None, None, vocab)[0]
    if pr is None:
        if genre == 'landing':
            rep.add(T, 'warning', 'COPY-D-PROMISE', pid, 'нет обещания первого экрана (promise)',
                    'Заведите promise (или promise.from: <page>/hero/<slot>): обещание первого экрана — текст страницы, его сверяют как подзаголовок hero.')
    elif pr.get('from') and ptext is None:
        rep.add(T, 'error', 'COPY-D-PROMISE', f'{pid}/promise', f'promise.from «{pr.get("from")}» не найден или у слота нет выбранного варианта', 'Ссылка — <page_id>/<section_id>/<slot_id> этой страницы.')
    elif not pr.get('from'):
        v = _validate_slot(deck, page, None, pr, f'{pid}/promise', ctx, rep, final, fresh, pstatus, is_promise=True)
        chosen_status.append((f'{pid}/promise', _status_of(v) if v else None))
    # ---- главная кнопка
    cpath, ctext = primary_cta(deck, page)
    if page.get('cta_primary') and ctext is None:
        rep.add(T, 'error', 'COPY-D-CTA', pid, f'cta_primary «{page.get("cta_primary")}» не найден', 'Ссылка — <page>/<section>/<slot> слота cta-label.')
    elif cpath is None and genre in ('landing', 'site-page'):
        rep.add(T, 'info', 'COPY-D-CTA', pid, 'на странице нет слота cta-label', 'site.cta.label брифа холста останется пустым.')
    # ---- мета (без meta-rules.yaml; с ним — meta-x-… в _meta_checks)
    meta = page.get('meta')
    need_meta = final or pstatus == 'approved'
    if isinstance(meta, dict) and ctx.meta_rules is None:
        for k in ('title', 'description'):
            if need_meta and not str(meta.get(k) or '').strip():
                rep.add(T, 'error' if final else 'warning', 'COPY-D-META', f'{pid}/meta/{k}', f'пустое meta.{k} у страницы {pstatus}'
                        + ('' if final else ' — заполнить до публикации'), 'Мета — часть copy deck (правила — meta-rules.yaml); ворота публикации — validate --final.')
        og_plan = plan_og_fields(deck, ctx, page)   # как meta-x-og-missing: ждём те OG-поля, что заведены слотами плана
        for k in ('og_title', 'og_description'):
            if (need_meta or pstatus == 'checked') and (og_plan is None or k in og_plan) and not str(meta.get(k) or '').strip():
                rep.add(T, 'warning', 'COPY-D-META', f'{pid}/meta/{k}', f'пустое meta.{k}', 'Без og:* превью ссылки соберёт площадка сама.')
    elif final and not isinstance(meta, dict):
        rep.add(T, 'error', 'COPY-D-META', pid, 'нет блока meta', 'meta: {title, description, og_title, og_description}.')
    if isinstance(meta, dict) and need_meta:
        for k, _st in META_FIELDS:
            if PLACEHOLDER_RX.search(str(meta.get(k) or '')):
                rep.add(T, 'error' if final else 'warning', 'COPY-D-PLACEHOLDER', f'{pid}/meta/{k}',
                        'заглушка в мета страницы ' + ('перед публикацией' if final else f'{pstatus} — закрыть до публикации'),
                        'Закройте пробел в facts.yaml или перепишите без факта; ворота публикации — validate --final.')
    # ---- варианты мета, пересмотр, бриф статьи
    if isinstance(meta, dict):
        mv = meta.get('variants') if isinstance(meta.get('variants'), dict) else {}
        for k, vs in mv.items():
            vs = [v for v in vs or [] if isinstance(v, dict)]
            ids = [str(v.get('id')) for v in vs]
            for d in sorted({x for x in ids if ids.count(x) > 1}):
                rep.add(T, 'error', 'COPY-D-ID-DUP', f'{pid}/meta/{k}', f'повтор id варианта мета «{d}»', '')
            if meta.get(k) and not any(v.get('text') == meta.get(k) for v in vs):
                rep.add(T, 'info', 'COPY-D-META-VARIANTS', f'{pid}/meta/{k}', f'выбранный meta.{k} не совпадает ни с одним вариантом meta.variants.{k}', 'Выбранный текст — один из вариантов (или добавьте его в variants).')
            for v in vs:
                if v.get('status') == 'rejected' and not v.get('reason'):
                    rep.add(T, 'error', 'COPY-D-REJECTED', f"{pid}/meta/{k}/{v.get('id')}", 'отклонённый вариант мета без reason', '')
        n_title = len([v for v in mv.get('title') or [] if isinstance(v, dict) and v.get('status') != 'rejected'])
        g = effective_genre(deck, page, None, None, None, vocab)[0]
        if meta.get('title') and n_title < 2 and (g == 'article' or ptype in ('service-page', 'seo-landing-page')) and pstatus in ('checked', 'approved'):
            rep.add(T, 'info', 'COPY-D-META-VARIANTS', f'{pid}/meta/title', 'один вариант title у страницы из поиска', '07-seo-geo-copy/02 §4.3: 2–3 варианта title с планом теста (meta.variants.title, meta.test_plan).')
        if n_title >= 2 and not meta.get('test_plan'):
            rep.add(T, 'info', 'COPY-D-META-VARIANTS', f'{pid}/meta/title', f'вариантов title {n_title}, а плана теста нет', 'meta.test_plan: где и сколько недель мерить (Вебмастер, Search Console).')
        rb = meta.get('review_by')
        if rb and date_end(rb) < ctx.today:
            rep.add(T, 'warning', 'COPY-D-META-REVIEW', f'{pid}/meta', f'пора пересмотреть мета (review_by {rb})', 'title и description устаревают; пересмотр раз в 12–24 месяца.')
    art = page.get('article')
    if isinstance(art, dict) and ctx.facts is not None:
        refs = [('author', art.get('author'))] + [('experts', x) for x in art.get('experts') or []] + \
               [('unique_angle', x) for x in ((art.get('unique_angle') or {}).get('fact_ids') or [])]
        for what, ref in refs:
            if not ref:
                continue
            f, m = ctx.facts.resolve(ref)
            if f is None:
                rep.add(T, 'error', 'COPY-D-FACT-REF', f'{pid}/article/{what}', f'нет факта «{ref}»' + (' (это пробел missing)' if m else ''), 'Автор и эксперты — факты вида person с разрешением (COPY-GEO-19).')
            elif what in ('author', 'experts') and f.get('kind') != 'person':
                rep.add(T, 'warning', 'COPY-D-ARTICLE', f'{pid}/article/{what}', f'fact:{f["id"]} вида {f.get("kind")}, а не person', '')
    g = effective_genre(deck, page, None, None, None, vocab)[0]
    if g == 'article' and not isinstance(art, dict) and pstatus in ('checked', 'approved'):
        rep.add(T, 'info', 'COPY-D-ARTICLE', pid, 'у статьи нет полей брифа article (интент, запрос, угол, автор)', '07-seo-geo-copy/02 §1.1.')
    # ---- статус страницы из статусов выбранных вариантов
    if pstatus in ('checked', 'approved'):
        need = 'approved' if pstatus == 'approved' else 'checked'
        low = [p for p, st in chosen_status if st is None or STATUS_RANK.get(st, 0) < STATUS_RANK[need]]
        if low:
            rep.add(T, 'error', 'COPY-D-STATUS', pid, f'страница {pstatus}, но {len(low)} выбранных текстов ниже {need}: {", ".join(low[:5])}',
                    'Статус страницы не выше статуса её слотов.')
    if final and pstatus != 'approved':
        rep.add(T, 'error', 'COPY-D-FINAL', pid, f'--final: страница в статусе {pstatus}, а не approved', 'Публикуется только утверждённая страница.')
    if pstatus == 'approved':
        logs = [p for p, sl in process_holders(page) if sl.get('edit_log') or any(v.get('status') == 'rejected' for v in variants_of(sl))]
        if logs:
            rep.add(T, 'warning', 'COPY-D-PROCESS-LOG', pid, f'в утверждённой странице журнал процесса (edit_log, отклонённые варианты): {", ".join(logs[:5])}',
                    'Журнал уходит при утверждении (copydeck.py approve); история — в git.')


def gap_stems(s):
    """Значимые слова заглушки или описания пробела основами — той же нормализацией, что у сверки фактов
    (claims_check.py); без модуля — первые пять букв слова."""
    body = PLACEHOLDER_RX.sub(lambda m: m.group(1) or '', str(s or ''))
    m = claims_module()
    if m is not None:
        return {m.stem(w) for w in m.WORD_RX.findall(m.norm(body)) if w not in m.STOP and len(w) > 2}
    return {w.lower().replace('ё', 'е')[:5] for w in words(body) if len(w) > 2}


def placeholder_links(text, facts, missing_ids=None):
    """Заглушки текста и пробелы facts.yaml missing[], к которым они привязаны. → (id пробелов, заглушки без пробела).
    Заглушка привязана, если дословно повторяет placeholder любого пробела missing[] или названа своим пробелом: он стоит
    в missing_ids держателя, и больше половины значимых слов заглушки есть в его what и placeholder (один пробел
    «бригадир — имя, стаж» закрывает слот имени и слот стажа своими заглушками; заглушка без слов — «[PLACEHOLDER]» —
    при своём пробеле тоже его). Заглушка о другом рядом с чужим missing_ids не привязана: иначе любой текст в скобках
    прошёл бы утверждение. Заглушка названного пробела — честный пропуск факта на макете; публикацию держит
    validate --final (гейт 3)."""
    found = [m.group(0) for m in PLACEHOLDER_RX.finditer(text or '')]
    if not found:
        return [], []
    if facts is None:
        return [], found
    own = []
    for ref in missing_ids or []:
        r = str(ref)[8:] if str(ref).startswith('missing:') else str(ref)
        g = facts.missing_by_id.get(r)
        if g is not None and not any(g is x for x in own):
            own.append(g)
    ids, loose = [], []
    for ph in found:
        hit = next((x for x in facts.missing if norm_ws(x.get('placeholder')).lower() == norm_ws(ph).lower()), None)
        if hit is None:
            st = gap_stems(ph)
            hit = next((g for g in own if 2 * len(st & (gap_stems(g.get('what')) | gap_stems(g.get('placeholder')))) > len(st) or not st), None)
        if hit is not None:
            ids.append(str(hit.get('id')))
        else:
            loose.append(ph)
    return sorted(set(ids)), loose


def _validate_slot(deck, page, section, sl, path, ctx, rep, final, fresh, pstatus, is_promise=False):
    T = 'validate'
    vs = variants_of(sl)
    vids = [str(v.get('id')) for v in vs]
    for d in sorted({x for x in vids if vids.count(x) > 1}):
        rep.add(T, 'error', 'COPY-D-ID-DUP', path, f'повтор id варианта «{d}»', 'id варианта уникален в слоте.')
    ch = sl.get('chosen')
    v = chosen_variant(sl)
    if ch is not None and v is None:
        rep.add(T, 'error', 'COPY-D-CHOSEN', path, f'chosen «{ch}» — такого варианта нет', 'chosen = id одного из variants.')
    live = [x for x in vs if x.get('status') != 'rejected']
    # у черновика выбор ещё впереди: слот, все живые варианты которого draft, без chosen — не находка
    if ch is None and len(vs) > 1 and not (live and all(_status_of(x) == 'draft' for x in live)):
        rep.add(T, 'warning', 'COPY-D-CHOSEN', path, f'вариантов {len(vs)}, выбор не сделан (chosen)',
                'Выберите вариант: copydeck.py select (открыто) или export-variants и apply-selection (слепой выбор); до выбора сверяется первый.')
    for x in vs:
        if x.get('status') == 'rejected':
            if not x.get('reason'):
                rep.add(T, 'error', 'COPY-D-REJECTED', f"{path}/{x.get('id')}", 'отклонённый вариант без reason', 'Причина нужна цепочке I и парам «до / после».')
            if v is x:
                rep.add(T, 'error', 'COPY-D-CHOSEN', path, 'выбран отклонённый вариант', 'Выберите другой вариант или верните статус.')
    if v is None:
        return None
    if isinstance(v.get('fact_ids'), list) and set(map(str, v['fact_ids'])) != set(map(str, sl.get('fact_ids') or [])):
        rep.add(T, 'info', 'COPY-D-VARIANT-FACTS', path, f"у выбранного варианта {v.get('id')} свои fact_ids {v['fact_ids']}, у слота — {sl.get('fact_ids') or []}",
                'copydeck сверяет по фактам варианта, а claims_check.py и copy_lint.py на copy deck читают только fact_ids слота: '
                'check --update перенесёт факты выбранного варианта в слот.')
    text = str(v.get('text') or '')
    status = _status_of(v)
    rules = ((ctx.schema.get('x-status-rules') or {}).get('slot') or {}).get(status, {})
    missing_fields = [f for f in rules.get('slot_requires') or [] if f not in sl and not (is_promise and f in ('slot_id', 'slot_type'))]
    if missing_fields:
        rep.add(T, 'error', 'COPY-D-STATUS', path, f'текст в статусе {status}: нет полей {", ".join(missing_fields)}',
                'checked и approved пишет copydeck.py check --update (записи lint и claims с text_hash).')
    fr = (fresh or {}).get(path) or {}
    h = text_hash(text)
    for key in ('lint', 'claims'):
        rec = sl.get(key) if isinstance(sl.get(key), dict) else None
        if status in ('checked', 'approved'):
            now = fr.get(key)
            errs = (now.get('errors') - now.get('final_escalated', 0)) if now else (rec or {}).get('errors')
            if errs is None:
                rep.add(T, 'error', 'COPY-D-STATUS', path, f'статус {status}: нет итога {key} (errors)', f'Запустите copydeck.py check --update.')
            elif errs > 0:
                rep.add(T, 'error', 'COPY-D-STATUS', path, f'статус {status}, а {key}: {errs} error' + (' (свежая проверка)' if now else ' (запись)'),
                        'Исправьте текст или верните статус draft.')
            if rec and rec.get('text_hash') and rec['text_hash'] != h:
                rep.add(T, 'error', 'COPY-D-HASH', path, f'текст изменён после проверки {key} (text_hash {rec["text_hash"]} ≠ {h})',
                        'Статус checked/approved недействителен: перепроверьте (check --update) или верните draft.')
            elif rec and not rec.get('text_hash'):
                rep.add(T, 'warning', 'COPY-D-HASH', path, f'в записи {key} нет text_hash: не видно, тот ли текст проверяли', 'copydeck.py check --update пишет text_hash.')
        if rec and fr.get(key) and rec.get('errors') is not None and rec.get('errors') != fr[key].get('errors'):
            rep.add(T, 'info', 'COPY-D-RECORD', path, f'запись {key} устарела: в файле {rec.get("errors")} error, сейчас {fr[key].get("errors")}', 'copydeck.py check --update OUT')
    if status == 'approved':
        rv = v.get('review') if isinstance(v.get('review'), dict) else None
        if rv and str(rv.get('by', '')).startswith('copydeck'):
            rv = None  # запись утилиты (check --promote) — не утверждение человеком
        if not (rv and rv.get('by') and rv.get('at')) and not isinstance(page.get('approval'), dict):
            rep.add(T, 'error', 'COPY-D-STATUS', path, 'approved без review (by, at) у варианта и без approval страницы', 'Утверждает человек: review: {by: …, at: …}.')
    if final and PLACEHOLDER_RX.search(text):
        rep.add(T, 'error', 'COPY-D-PLACEHOLDER', path, f'заглушка в тексте статуса {status} (--final)', 'Закройте пробел в facts.yaml или перепишите без утверждения (fallback пробела).')
    elif status == 'approved' and PLACEHOLDER_RX.search(text):
        gaps, loose = placeholder_links(text, ctx.facts, sl.get('missing_ids'))
        if loose:
            rep.add(T, 'error', 'COPY-D-PLACEHOLDER', path, f'заглушка без пробела в facts.yaml: {", ".join(loose)}',
                    'Заглушка повторяет placeholder пробела facts.yaml missing[] или названа словами своего пробела (missing_ids слота); пробела нет — заведите его '
                    '(это вопрос владельцу факта) либо перепишите без утверждения.')
        else:
            rep.add(T, 'warning', 'COPY-D-PLACEHOLDER', path, 'заглушка пробела ' + ', '.join(f'missing:{g}' for g in gaps)
                    + ' в утверждённом тексте: макету не мешает, публикацию держит validate --final', 'Закройте пробел в facts.yaml до публикации.')
    _validate_text(deck, page, section, sl, path, text, v, ctx, rep)
    return v


def _validate_text(deck, page, section, sl, path, text, v, ctx, rep):
    T = 'validate'
    st = sl.get('slot_type') or ''
    bad = BAD_PLACEHOLDER_RX.search(text)
    if bad:
        rep.add(T, 'error', 'COPY-D-PLACEHOLDER-FORM', path, f'заглушка не по формату: «{bad.group(0)}»', 'Только [PLACEHOLDER: что именно].')
    for tok in ('{{', '{#', '<UNSET'):
        if tok in text:
            rep.add(T, 'error', 'COPY-D-TEMPLATE-TOKEN', path, f'в тексте «{tok}» — проверка входа холста сочтёт это остатком шаблона', 'Уберите фигурные скобки из текста.')
    if not text.strip() and st not in ('image-alt',):
        rep.add(T, 'warning', 'COPY-D-EMPTY', path, 'пустой текст выбранного варианта', 'Пустым бывает только alt декоративной картинки.')
    if st == 'image-alt':
        if not sl.get('asset_ref'):
            rep.add(T, 'warning', 'COPY-D-ASSET', path, 'alt без asset_ref', 'asset_ref — id слота плана ассетов.')
        if not text.strip() and not re.search(r'декоратив|decorative', str(sl.get('notes') or '') + str(v.get('notes') or ''), re.I):
            rep.add(T, 'warning', 'COPY-D-ALT', path, 'пустой alt без пометки, что картинка декоративная', 'Декоративная — alt="" и notes: «декоративная»; информационная — описание сцены (ai-media 10/01 §8).')
        if re.match(r'\s*(фото|изображение|картинка|image of|picture of|photo of)\b', text, re.I):
            rep.add(T, 'info', 'COPY-D-ALT', path, 'alt начинается с «фото / изображение»', 'Скринридер и так сообщает, что это картинка: опишите сцену.')
    if st == 'image-caption' and not sl.get('asset_ref'):
        rep.add(T, 'warning', 'COPY-D-ASSET', path, 'подпись без asset_ref', 'asset_ref — к какой картинке подпись.')
    if st == 'in-image-text':
        if len(text) > 40:
            rep.add(T, 'error', 'COPY-D-IN-IMAGE', path, f'строка в картинке {len(text)} знаков > 40', 'ai-media 05/03 §7: ≤ 40 знаков, 1–4 слова; длиннее — HTML поверх картинки.')
        if len(words(text)) > 4:
            rep.add(T, 'warning', 'COPY-D-IN-IMAGE', path, f'в строке {len(words(text))} слов (надёжно 1–4)', 'Сократите или вынесите текст в HTML.')
        if cyr_share(text) > 0.5:
            rep.add(T, 'info', 'COPY-D-IN-IMAGE', path, 'кириллица в картинке: риск искажений, нужна проверка OCR', 'fallback: html_overlay (ai-media 05/03 §7).')
        if not sl.get('asset_ref'):
            rep.add(T, 'warning', 'COPY-D-ASSET', path, 'строка в картинке без asset_ref', 'asset_ref — id слота плана ассетов ai-media.')


def first_screen_section(page):
    """Секция первого экрана: роль hero (или id hero без роли); нет hero — первая секция после шапки (header, utility)."""
    secs = sections_of(page)
    hero = next((s for s in secs if (s.get('section_role') or s.get('section_id')) == 'hero'), None)
    if hero is not None:
        return hero
    return next((s for s in secs if (s.get('section_role') or '') not in CHROME_TOP_ROLES), None)


def _validate_facts(deck, ctx, rep, refs_and_publish=True):
    """Факты текстов: (1) ссылки fact_ids, срок и публикуемость — их же даёт claims_check.py, поэтому check пропускает
    эту часть, если сверка отработала (refs_and_publish=False); (2) пробелы: missing_ids и fallback — этого
    claims_check.py не делает, часть работает всегда."""
    T = 'validate'
    facts = ctx.facts
    for page in pages_of(deck):
        if (page.get('status') or 'draft') == 'rejected':
            continue
        # свои fact_ids невыбранных живых вариантов: битая ссылка — warning (этот текст пока не на странице)
        pid = str(page.get('page_id'))
        holders = [(f"{pid}/{s.get('section_id')}/{sl.get('slot_id')}", sl, slot_alternatives(sl)) for s in sections_of(page) for sl in slots_of(s)]
        if isinstance(page.get('promise'), dict) and not page['promise'].get('from'):
            holders.append((f'{pid}/promise', page['promise'], slot_alternatives(page['promise'])))
        meta = page.get('meta') or {}
        holders += [(f'{pid}/meta/{k}', meta, meta_alternatives(meta, k)) for k, _st in META_FIELDS]
        for hpath, _holder, alts in (holders if refs_and_publish else []):
            for v in alts:
                for ref in (v.get('fact_ids') if isinstance(v.get('fact_ids'), list) else []):
                    f, m = facts.resolve(ref)
                    if f is None:
                        rep.add(T, 'warning', 'COPY-D-FACT-REF', f"{hpath}/{v.get('id')}",
                                f'fact_ids варианта: «{ref}» — ' + ('это пробел missing' if m is not None else 'нет такого факта'),
                                'Станет error, если вариант выберут: исправьте id или заведите факт.')
        for u in text_units(deck, page):
            refs = list(u['fact_ids'])
            slot = u['slot']
            status = _status_of(main_variant(slot)) if slot is not None else (page.get('status') or 'draft')
            for ref in (refs if refs_and_publish else []):
                f, m = facts.resolve(ref)
                if f is None:
                    if m is not None:
                        rep.add(T, 'error', 'COPY-D-FACT-REF', u['path'], f'fact_ids: «{ref}» — это пробел missing, факта ещё нет',
                                'Пробел — в тексте [PLACEHOLDER: …] и в missing_ids, не в fact_ids.')
                    else:
                        rep.add(T, 'error', 'COPY-D-FACT-REF', u['path'], f'fact_ids: нет факта «{ref}» в {os.path.basename(facts.path or "facts.yaml")}',
                                'Исправьте id (fact:<id> или алиас) или заведите факт в facts.yaml.')
                    continue
                iss = own_publish_issues(f, ctx.today)
                exp = [i for i in iss if i.startswith('истёк')]
                if exp:
                    rep.add(T, 'error', 'COPY-D-FACT-EXPIRED', u['path'], f'fact:{f["id"]}: {exp[0]}', 'Обновите факт у заказчика или уберите утверждение.')
                other = [i for i in iss if not i.startswith('истёк')]
                if other:
                    lvl = 'error' if STATUS_RANK.get(status, 0) >= 1 else 'warning'
                    rep.add(T, lvl, 'COPY-D-FACT-UNPUBLISHABLE', u['path'], f'fact:{f["id"]} не публикуется: {"; ".join(other)}',
                            'До разрешения или проверки — [PLACEHOLDER] (claims_check.py даст то же как COPY-F-…).')
            gaps = {}
            if slot is not None:
                for ref in slot.get('missing_ids') or []:
                    r = str(ref)[8:] if str(ref).startswith('missing:') else str(ref)
                    if r not in facts.missing_by_id:
                        rep.add(T, 'error', 'COPY-D-MISSING-REF', u['path'], f'missing_ids: нет пробела «{ref}»', 'id из facts.yaml missing[].')
                    elif not PLACEHOLDER_RX.search(u['text']):
                        rep.add(T, 'info', 'COPY-D-MISSING-REF', u['path'], f'missing_ids: {ref}, а в тексте нет [PLACEHOLDER]', 'Пробел закрыт? Уберите ссылку или верните заглушку.')
                    else:
                        gaps[r] = facts.missing_by_id[r]
            for m in PLACEHOLDER_RX.finditer(u['text']):
                hit = next((x for x in facts.missing if norm_ws(x.get('placeholder')).lower() == norm_ws(m.group(0)).lower()), None)
                if hit is not None:
                    gaps.setdefault(str(hit.get('id')), hit)
            for gid, gm in gaps.items():  # fallback пробела: заглушка уместна только при fallback: placeholder
                fb = gm.get('fallback') or 'placeholder'
                if fb == 'omit-block':
                    rep.add(T, 'warning', 'COPY-D-FALLBACK', u['path'], f'missing:{gid} — fallback omit-block: до ответа блок не показывают, а в тексте заглушка',
                            'Снимите слот или секцию до ответа заказчика (facts.yaml missing[].fallback).')
                elif fb == 'rewrite-without':
                    rep.add(T, 'warning', 'COPY-D-FALLBACK', u['path'], f'missing:{gid} — fallback rewrite-without: перепишите текст без этого утверждения',
                            'Заглушка на странице здесь не нужна: скажите то, что подтверждено фактами.')


def name_key(s):
    """Имя для сравнения: один пробел, без регистра, «ё» = «е»."""
    return norm_ws(s).lower().replace('ё', 'е')


def entity_names(facts):
    """Имена сущностей facts.yaml (entities[].names) ключами name_key; фактов или сущностей нет — пусто."""
    ents = (getattr(facts, 'data', None) or {}).get('entities')
    return {name_key(n) for e in (ents if isinstance(ents, list) else []) if isinstance(e, dict)
            for n in (e.get('names') if isinstance(e.get('names'), list) else [])} - {''}


def _validate_wave2(deck, ctx, rep):
    """Файлы правил текста: есть — проверка работает; нет — предупреждение «правила не загружены», без падения."""
    T = 'validate'
    # --- copy-slots.yaml: по copy_slots_ref copy deck, иначе файл базы (ctx.copy_slots_path — его замена в --selftest);
    # ссылка в пустоту — предупреждение, правила — из базы: длины слотов и обязательность фактов проверяются всё равно
    cs_path = ctx.copy_slots_path or COPY_SLOTS_PATH
    cs_ref = deck.get('copy_slots_ref')
    if cs_ref:
        ref_path = rel_to(ctx.deck_path, cs_ref) if ctx.deck_path else cs_ref
        if ref_path and os.path.exists(ref_path):
            cs_path = ref_path
        else:
            rep.add(T, 'warning', 'COPY-D-RULES-REF', '—', f'copy_slots_ref не разрешается: {cs_ref}; правила — из базы',
                    'Путь — от папки copy deck: поправьте ссылку или уберите её (без неё правила — copy-slots.yaml базы text).')
    if cs_path and os.path.exists(cs_path):
        try:
            specs, renames, notes = load_copy_slots(cs_path)
        except Exception as e:  # noqa: BLE001
            specs, renames, notes = None, {}, [f'copy-slots.yaml не читается: {e}']
        for n in notes:
            rep.add(T, 'warning', 'COPY-D-RULES-FORMAT', '—', n, 'Формат copy-slots.yaml изменился — сверьте разбор load_copy_slots.')
        if specs:
            meta_cs = specs.pop('__meta__', {}) or {}
            rep.tools.setdefault('validate', {})['copy_slots'] = os.path.relpath(cs_path, ROOT) if cs_path.startswith(ROOT) else cs_path
            lang = (deck.get('lang') or 'ru').split('-')[0]
            names = entity_names(ctx.facts)
            for page in pages_of(deck):
                pid = str(page.get('page_id'))
                targets = [(f"{pid}/{s.get('section_id')}/{sl.get('slot_id')}", s, sl, sl.get('slot_type')) for s in sections_of(page) for sl in slots_of(s)]
                pr = page.get('promise')
                if isinstance(pr, dict) and not pr.get('from'):
                    targets.append((f'{pid}/promise', None, pr, 'promise'))
                for path, s, sl, st in targets:
                    spec = specs.get(st)
                    if spec is None:
                        if st in renames:
                            rep.add(T, 'warning', 'COPY-D-SLOT-RENAMED', path, f'slot_type «{st}» переименован в copy-slots.yaml → «{renames[st]}»', 'Смените slot_type на новое имя (renames в copy-slots.yaml).')
                        else:
                            rep.add(T, 'warning', 'COPY-D-SLOT-UNKNOWN', path, f'slot_type «{st}» нет в copy-slots.yaml', 'Правила текста для этого типа не заданы.')
                        continue
                    v = chosen_variant(sl)
                    text = str((v or {}).get('text') or '')
                    if v is None or not text:
                        continue
                    body = PLACEHOLDER_RX.sub('', text)
                    vals = {'words': len(words(body)), 'chars': len(norm_ws(body))}
                    # заголовок — имя сущности фактов (модель, услуга, марка): его длину задаёт имя, нижняя граница
                    # длины к нему не применяется; верхняя — остаётся, она о месте в макете
                    named = st in HEADING_LEVEL and name_key(body) in names
                    ls = (spec.get('lang') or {}).get(lang)
                    exc = (' Исключения copy-slots.yaml: ' + one_line(spec['exceptions'][0])[:160]) if spec.get('exceptions') else ''
                    if ls:  # формат copy-slots: основная единица (RU — знаки, EN — слова), p10–p90 → info, грубые границы замера → warning
                        prim = ls.get('primary') or 'chars'
                        prov = ' (provisional)' if ls.get('provisional') else ''
                        for unit in ('words', 'chars'):
                            val, rng, hard = vals[unit], ls.get(unit), ls.get(f'hard_{unit}')
                            un = 'слов' if unit == 'words' else 'знаков'
                            if hard and hard[1] is not None and val > hard[1]:
                                rep.add(T, 'warning', 'COPY-D-LEN', path, f'{val} {un} > {hard[1]} — за грубой границей замера корпуса ({st}, {lang}){prov}', 'Длины — copy-slots.yaml.' + exc)
                            elif unit == prim and rng and rng[1] is not None and val > rng[1]:
                                rep.add(T, 'info', 'COPY-D-LEN', path, f'{val} {un} > p90 лидеров {rng[1]} ({st}, {lang}){prov}', 'Сигнал, не ворота: у 10 % лидеров длиннее.' + exc)
                            if not PLACEHOLDER_RX.search(text) and not named:
                                if hard and hard[0] is not None and val < hard[0]:
                                    rep.add(T, 'warning', 'COPY-D-LEN', path, f'{val} {un} < {hard[0]} — за грубой границей замера D ({st}, {lang})', '')
                                elif unit == prim and rng and rng[0] is not None and val < rng[0]:
                                    rep.add(T, 'info', 'COPY-D-LEN', path, f'{val} {un} < p10 лидеров {rng[0]} ({st}, {lang}){prov}', '')
                    else:  # другой формат: границы min/max где угодно в length
                        for (lg, unit), (mn, mx) in sorted(spec['len'].items()):
                            if lg not in ('any', lang):
                                continue
                            val = vals[unit]
                            if mx is not None and val > mx:
                                rep.add(T, 'warning', 'COPY-D-LEN', path, f'{val} {"слов" if unit == "words" else "знаков"} > max {mx} ({st}, {lg})', 'Длины — copy-slots.yaml; законные исключения — notes.')
                            if mn is not None and val < mn and not PLACEHOLDER_RX.search(text) and not named:
                                rep.add(T, 'info', 'COPY-D-LEN', path, f'{val} {"слов" if unit == "words" else "знаков"} < min {mn} ({st}, {lg})', '')
                    need = spec.get('fact_required')
                    refs = variant_fact_ids(sl, v)
                    if need == 'always' and not refs and not PLACEHOLDER_RX.search(text):
                        lvl = 'error' if STATUS_RANK.get(_status_of(v), 0) >= 1 else 'warning'
                        rep.add(T, lvl, 'COPY-D-FACT-REQUIRED', path, f'{st}: факт обязателен (copy-slots.yaml), а fact_ids пуст', 'Ссылка на facts.yaml или [PLACEHOLDER: …].')
                    roles = spec.get('section_roles') or []
                    if s is not None and roles and s.get('section_role') and s['section_role'] not in roles:
                        rep.add(T, 'info', 'COPY-D-SLOT-ROLE', path, f'{st} в секции «{s["section_role"]}», а copy-slots.yaml ждёт {roles}', '')
                # составные правила copy-slots.yaml: ядро первого экрана (hero-core) — сумма слов слотов секции hero; у страницы без
                # hero (план другого типа) — первой секции после шапки
                hc = ((meta_cs.get('composites') or {}).get('hero-core') or {})
                first = first_screen_section(page)
                if hc.get('max_words') and first is not None:
                    seen_t, total = set(), 0
                    for sl in slots_of(first):
                        if sl.get('slot_type') in ('headline', 'subheadline', 'cta-label', 'cta-note', 'hero-proof') and sl.get('slot_type') not in seen_t:
                            seen_t.add(sl.get('slot_type'))
                            total += len(words(PLACEHOLDER_RX.sub('', str((chosen_variant(sl) or {}).get('text') or ''))))
                    if total > hc['max_words']:
                        rep.add(T, 'warning', 'COPY-D-HERO-CORE', f"{pid}/{first.get('section_id')}", f'ядро первого экрана {total} слов > {hc["max_words"]} (hero-core)', one_line(hc.get('rule'))[:200])
    else:
        rep.add(T, 'warning', 'COPY-D-RULES-MISSING', '—', 'правила не загружены: copy-slots.yaml нет — длины слотов и обязательность фактов не проверены',
                f'Появится {os.path.relpath(COPY_SLOTS_PATH, ROOT)} — проверка включится сама.')
    # --- голос
    vref = deck.get('voice_ref')
    if not os.path.exists(ctx.voice_schema_path):
        rep.add(T, 'warning', 'COPY-D-RULES-MISSING', '—', 'правила не загружены: voice.schema.yaml нет — голос проверен только по voice.yaml, если он есть', '')
    if vref and looks_like_path(vref):
        vp = rel_to(ctx.deck_path, vref) if ctx.deck_path else vref
        if vp and os.path.exists(vp):
            try:
                voice = load_voice(vp)
            except Exception as e:  # noqa: BLE001
                voice = None
                rep.add(T, 'warning', 'COPY-D-VOICE', '—', f'voice.yaml не читается: {e}', '')
            if voice:
                _voice_checks(deck, voice, rep)
        else:
            rep.add(T, 'warning', 'COPY-D-VOICE', '—', f'voice_ref «{vref}» не найден', 'Путь от папки copy deck.')
    elif vref:
        rep.add(T, 'info', 'COPY-D-VOICE', '—', 'voice_ref — строка-описание (до профиля голоса): голос не проверяется', '')
    else:   # без ссылки проверка голоса молчит — и «не говорим» профиля проходит незамеченным
        rep.add(T, 'warning', 'COPY-D-VOICE', '—', 'нет voice_ref: голос текстов не проверяется',
                'voice_ref — путь к voice.yaml от папки copy deck (каркас берёт его из смысла: copydeck.py skeleton).')
    # --- мета
    mr = ctx.meta_rules
    if mr is not None:
        if not mr.get('format'):
            rep.add(T, 'info', 'COPY-D-RULES-FORMAT', '—', 'meta-rules.yaml: limits и checks_outside_linter не распознаны — проверки мета пропущены (правила мета в линтере работают через copy_lint.py)', 'Формат meta-rules.yaml изменился — сверьте разбор load_meta_rules.')
        else:
            rep.tools.setdefault('validate', {})['meta_rules'] = f"{os.path.relpath(ctx.meta_rules_path, ROOT) if ctx.meta_rules_path.startswith(ROOT) else ctx.meta_rules_path} ({mr['format']})"
            _meta_checks(deck, mr, rep, ctx.final, ctx)
    else:
        rep.add(T, 'warning', 'COPY-D-RULES-MISSING', '—', 'правила не загружены: meta-rules.yaml нет — длины мета и проверки между страницами не проверены', '')
        seen = {}
        for page in pages_of(deck):
            for k in ('title', 'description'):
                t = norm_ws((page.get('meta') or {}).get(k) or '').lower()
                if t:
                    if (k, t) in seen:
                        rep.add(T, 'warning', 'COPY-D-META-DUP', f"{page.get('page_id')}/meta/{k}", f'meta.{k} совпадает со страницей {seen[(k, t)]}', 'У каждой страницы своя мета.')
                    seen.setdefault((k, t), page.get('page_id'))
    # --- флаги права
    known = set(claim_class_info())
    rule_ids = None
    if os.path.exists(ctx.claims_rules_path):
        try:
            rule_ids = load_claims_rules_ids(ctx.claims_rules_path)
        except Exception as e:  # noqa: BLE001
            rep.add(T, 'warning', 'COPY-D-RULES-FORMAT', '—', f'claims-rules.yaml не читается: {e}', '')
    else:
        rep.add(T, 'warning', 'COPY-D-RULES-MISSING', '—', 'правила не загружены: claims-rules.yaml нет — флаги права не проверены', '')
    for page in pages_of(deck):
        for u in text_units(deck, page, include_meta=False):
            slot = u['slot']
            for fl in (slot or {}).get('claim_flags') or []:
                fl = str(fl)
                if fl in known or re.fullmatch(r'\d+fz(-[0-9a-z.]+)+', fl, re.I) or re.fullmatch(r'(zozpp|gk|152fz|ftc|ucpd)[-0-9a-z.]*', fl, re.I):
                    continue
                if fl.upper().startswith('COPY-'):
                    if rule_ids is None:
                        rep.add(T, 'info', 'COPY-D-FLAGS', u['path'], f'флаг «{fl}»: правила права не загружены — не проверен', '')
                    elif fl not in rule_ids:
                        rep.add(T, 'warning', 'COPY-D-FLAGS', u['path'], f'флаг «{fl}» нет в claims-rules.yaml', 'id правил права — COPY-L-…')
                    continue
                rep.add(T, 'warning', 'COPY-D-FLAGS', u['path'], f'неизвестный claim_flags «{fl}»', 'Классы утверждений (x-claim-classes), id правил права (COPY-L-…) или флаги норм (38fz-5-3-1).')
    # подсказка: факт класса legal: required без флага в слоте
    if ctx.facts is not None:
        info = claim_class_info()
        for page in pages_of(deck):
            for u in text_units(deck, page, include_meta=False):
                slot = u['slot'] or {}
                flags = {str(x) for x in slot.get('claim_flags') or []}
                for ref in u['fact_ids']:
                    f, _m = ctx.facts.resolve(ref)
                    for c in (f or {}).get('claim_class') or []:
                        if (info.get(c) or {}).get('legal') == 'required' and c not in flags:
                            rep.add(T, 'info', 'COPY-D-FLAGS', u['path'], f'fact:{f["id"]} класса {c} (legal: required), а в claim_flags его нет', f'claim_flags: [{c}] — флаг для проверки права и человека.')


def _voice_checks(deck, voice, rep):
    T = 'validate'
    lang = (deck.get('lang') or 'ru').split('-')[0]
    rxs = []
    for t in voice['taboo']:
        try:
            rxs.append((t, words_rx(t['term'])))
        except re.error:
            continue
    for page in pages_of(deck):
        for u in text_units(deck, page, include_meta=True):
            if u['slot_type'] == 'testimonial-quote':
                continue  # голос бренда не правит цитату клиента
            low = u['text'].lower()
            for t, rx in rxs:
                if t['lang'] not in ('any', lang) or (t['slot_types'] and u['slot_type'] not in t['slot_types']):
                    continue
                m = rx.search(low)
                if m:
                    lvl = t['level'] if t['level'] in LEVELS else 'warning'
                    fix = ('Вместо: ' + t['use_instead'] + '. ' if t['use_instead'] else '') + (f"Можно, если: {t['unless']}." if t['unless'] else 'Профиль голоса (voice.yaml vocabulary.avoid).')
                    rep.add(T, lvl, 'COPY-D-VOICE', u['path'], f'«не говорим» голоса: «{m.group(0)}» (термин {t["term"]})', fix)
            if lang == 'ru' and voice['address'] and u['slot_type'] not in voice.get('exceptions', []) \
                    and (u['section'] or {}).get('section_id') not in voice.get('exceptions', []):
                if voice['address'] == 'вы' and re.search(r'(?<![а-яё])(ты|тебя|тебе|тобой|твой|твоя|твоё|твои|твоих|твоим)(?![а-яё])', low):
                    rep.add(T, 'warning', 'COPY-D-VOICE', u['path'], 'обращение на «ты», а голос — на «вы»', 'address.ru_form голоса.')
                if voice['address'] == 'ты' and re.search(r'(?<![а-яё])(вас|вам|вами|ваш|ваша|ваше|ваши|вашего|вашей)(?![а-яё])', low):
                    rep.add(T, 'warning', 'COPY-D-VOICE', u['path'], 'обращение на «вы», а голос — на «ты»', 'address.ru_form голоса.')


def _validate_language(deck, ctx, rep):
    T = 'validate'
    lang = (deck.get('lang') or '').split('-')[0]
    src = deck.get('source_lang')
    if src:
        if src.split('-')[0] == lang:
            rep.add(T, 'error', 'COPY-D-LANG', '—', f'source_lang «{src}» = lang', 'source_lang — язык исходного copy deck, если этот — адаптация.')
        if not deck.get('source_ref'):
            rep.add(T, 'warning', 'COPY-D-LANG', '—', 'адаптация без source_ref', 'Укажите исходный copy deck.')
        elif ctx.deck_path and not os.path.exists(rel_to(ctx.deck_path, deck['source_ref'])):
            rep.add(T, 'warning', 'COPY-D-LANG', '—', f'source_ref «{deck["source_ref"]}» не найден', '')
        if ((deck.get('adaptation') or {}).get('mode')) == 'translation':
            rep.add(T, 'warning', 'COPY-D-LANG', '—', 'adaptation.mode: translation', 'Второй язык — адаптация под свою аудиторию, а не дословный перевод.')
        if ctx.facts is not None:
            for page in pages_of(deck):
                for u in text_units(deck, page):
                    for ref in u['fact_ids']:
                        f, _m = ctx.facts.resolve(ref)
                        if f is not None and (f.get('lang') or 'ru').split('-')[0] != lang and lang not in (f.get('translations') or {}):
                            rep.add(T, 'warning', 'COPY-D-LANG', u['path'], f'fact:{f["id"]}: нет translations.{lang}',
                                    'Сверка сравнит текст с формулировкой на другом языке: добавьте translations в facts.yaml.')
    for page in pages_of(deck):
        for u in text_units(deck, page):
            t = PLACEHOLDER_RX.sub('', u['text'])
            if len(words(t)) < 3:
                continue
            share = cyr_share(t)
            if lang == 'en' and share > 0.3:
                rep.add(T, 'warning', 'COPY-D-LANG', u['path'], f'кириллица в английском тексте ({share:.0%} букв)', 'Второй язык — отдельный copy deck.')
            if lang == 'ru' and share < 0.3 and u['slot_type'] not in ('testimonial-quote',):
                rep.add(T, 'info', 'COPY-D-LANG', u['path'], f'латиница в русском тексте ({1 - share:.0%} букв)', '')


# ============================================================================================ claims: claims_check.py процессом
# Обход эвристик сверки — claims_allow слота, мета и страницы: [{rule, reason, by[, value | fragment]}]. rule — семейство
# или id находки: COPY-F-CLASS — маркер класса утверждения без факта; COPY-F-NUM — семейство (число без факта и число,
# не совпавшее с фактом); COPY-F-NUM-MISMATCH — только несовпавшее число. value (число) и fragment (фрагмент находки)
# сужают запись до одной находки: без них запись снимает все находки правила на своём месте. Право (COPY-L-…),
# never_claim, «утверждение шире факта» и остальная сверка не обходятся — гейт 3 держится.
CLAIMS_ALLOW_RULES = {'COPY-F-CLASS': ('COPY-F-CLASS',), 'COPY-F-NUM': ('COPY-F-NUM', 'COPY-F-NUM-MISMATCH'),
                      'COPY-F-NUM-MISMATCH': ('COPY-F-NUM-MISMATCH',)}
FACT_IN_REASON_RX = re.compile(r'\bfact:([A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)')
NUMBER_RX = re.compile(r'\d+(?:[.,]\d+)?')


def number_key(s):
    """Число для сравнения записи обхода с фрагментом находки: «7 900» = «7900», «4,9» = «4.9», «12.0» = «12»; не число —
    None."""
    t = re.sub(r'(?<=\d)[\s   ](?=\d)', '', str(s).strip()).replace(',', '.')
    if not re.fullmatch(r'\d+(?:\.\d+)?', t):
        return None
    return t.rstrip('0').rstrip('.') if '.' in t else t


def fragment_numbers(fragment):
    """Числа фрагмента находки (разряды через пробел — одно число) — ключами number_key."""
    t = re.sub(r'(?<=\d)[\s   ](?=\d{3}(?!\d))', '', str(fragment or ''))
    return {number_key(x) for x in NUMBER_RX.findall(t)}


def claims_allow_of(holder, facts=None):
    """claims_allow слота, мета или страницы → (действующие [{rule, reason, by[, value][, fragment]}], неверные
    [(запись, почему)]). Действует запись с правилом из CLAIMS_ALLOW_RULES, причиной (reason) и тем, кто решил (by —
    заказчик или аналитик, не агент); value — число и только у обхода числа; fact:<id> в причине обхода числа — факт
    facts.yaml (facts=None — не сверяется)."""
    ok, bad = [], []
    raw = holder.get('claims_allow') if isinstance(holder, dict) else None
    for a in raw if isinstance(raw, list) else ([raw] if raw else []):
        a = a if isinstance(a, dict) else {'rule': a}
        rule, reason, by = (str(a.get(k) or '').strip() for k in ('rule', 'reason', 'by'))
        value = None if a.get('value') in (None, '') or isinstance(a.get('value'), bool) else str(a['value']).strip()
        fragment = norm_ws(a.get('fragment')) or None
        entry = {'rule': rule, 'reason': reason, 'by': by, **({'value': value} if value else {}), **({'fragment': fragment} if fragment else {})}
        why = []
        if rule not in CLAIMS_ALLOW_RULES:
            why.append(f'правило «{rule or "—"}» не обходится — только {", ".join(CLAIMS_ALLOW_RULES)}')
        if not reason:
            why.append('нет reason — почему находка ложная')
        if not by:
            why.append('нет by — кто решил (заказчик или аналитик)')
        if value and rule == 'COPY-F-CLASS':
            why.append('value — у обхода числа; у маркера класса снятое называет fragment')
        elif value and number_key(value) is None:
            why.append(f'value «{value}» — не число; слово или фразу называет fragment')
        if facts is not None and rule in ('COPY-F-NUM', 'COPY-F-NUM-MISMATCH'):
            miss = [x for x in FACT_IN_REASON_RX.findall(reason) if facts.resolve(x)[0] is None]
            if miss:
                why.append('в reason ' + ', '.join(f'fact:{x}' for x in miss) + ' — такого факта нет в facts.yaml')
        if why:
            bad.append((entry, '; '.join(why)))
        else:
            ok.append(entry)
    return ok, bad


def claims_allow_holders(deck, pages=None):
    """Держатели claims_allow неотклонённых страниц: [(путь, держатель, 'page' | 'meta' | 'slot')] — страница, её мета
    (путь <page>/meta: обход текстов мета, а не всей страницы) и слоты."""
    out = []
    for page in pages_of(deck):
        pid = str(page.get('page_id'))
        if (pages and pid not in pages) or (page.get('status') or 'draft') == 'rejected':
            continue
        out.append((pid, page, 'page'))
        if isinstance(page.get('meta'), dict):
            out.append((f'{pid}/meta', page['meta'], 'meta'))
        out += [(f"{pid}/{s.get('section_id')}/{sl.get('slot_id')}", sl, 'slot') for s in sections_of(page) for sl in slots_of(s)]
    return out


def claims_allow_match(entry, fragment):
    """Называет ли запись именно эту находку: value — число фрагмента находки, fragment — слово или фраза фрагмента
    целиком (без учёта регистра, «ё» = «е»). Запись без value и fragment подходит любой находке своего правила."""
    if entry.get('value') and number_key(entry['value']) not in fragment_numbers(fragment):
        return False
    if entry.get('fragment'):
        low = lambda s: norm_ws(s).lower().replace('ё', 'е')
        if not re.search(r'(?<![0-9a-zа-я])' + re.escape(low(entry['fragment'])) + r'(?![0-9a-zа-я])', low(fragment)):
            return False
    return True


def claims_allow_covers(entries, rule, fragment=''):
    """Запись, которая покрывает находку: правило записи — семейство или id находки rule, а value и fragment записи,
    если заданы, называют фрагмент находки; None — такой нет."""
    return next((e for e in entries if rule in CLAIMS_ALLOW_RULES.get(e['rule'], ()) and claims_allow_match(e, fragment)), None)


def claims_allow_listed(deck, facts, pages=None):
    """Действующие записи claims_allow страниц — список обходов для утверждения и публикации: [{rule, where, reason, by,
    scope[, value][, fragment]}]."""
    return [{'rule': e['rule'], 'where': hpath, 'reason': e['reason'], 'by': e['by'], 'scope': kind,
             **{k: e[k] for k in ('value', 'fragment') if e.get(k)}}
            for hpath, holder, kind in claims_allow_holders(deck, pages) for e in claims_allow_of(holder, facts)[0]]


def _flat_slot(slot_id, slot_type, variants, chosen, fact_ids, claim_flags, genre):
    vs = [{'id': str(v.get('id')), 'text': str(v.get('text') or ''), 'status': v.get('status') or 'draft'}
          for v in (variants or []) if isinstance(v, dict)]
    out = {'slot_id': str(slot_id), 'slot_type': slot_type or 'body', 'variants': vs,
           'fact_ids': [str(x) for x in fact_ids or []], 'claim_flags': [str(x) for x in claim_flags or []],
           'lint': {'profile': genre}}
    if chosen is not None:
        out['chosen'] = str(chosen)
    return out


def flatten_for_claims(deck, ctx, pages=None, alternatives=False):
    """v1 → плоская копия v0 для claims_check.py: мета и OG-шаблон — псевдосекция __head (жанр meta), обещание —
    псевдосекция __promise (subheadline в hero), у каждого слота lint.profile = жанр (claims берёт жанр оттуда); в слоте —
    только текст, который проверяется как текст слота (main_variant), с его фактами (variant_fact_ids).
    alternatives (check --all-variants): каждый живой невыбранный вариант (и альтернатива мета) сверяется «как если бы
    его выбрали» — копия страницы `<page>~alt~N`, где заменён один слот; соседние варианты не считаются текстом «рядом»
    (nearby), отклонённые не сверяются.
    → (deck, {(page, section, slot): путь}, {(копия страницы, section, slot): (путь, id варианта)})."""
    vocab = ctx.vocab
    out_pages, mapping, alt_map = [], {}, {}
    for page in pages_of(deck):
        pid = str(page.get('page_id'))
        if (pages and pid not in pages) or (page.get('status') or 'draft') == 'rejected':
            continue
        secs, head, alts = [], [], []   # alts: (section_id, slot_id, путь, id варианта, текст, факты)
        meta = page.get('meta') or {}
        for k, st in META_FIELDS:
            if str(meta.get(k) or '').strip():
                # meta.fact_ids — один список на все поля: в сверку не передаём (claims_check найдёт факт по тексту поля),
                # иначе каждое поле получает чужие факты и ложные COPY-F-USE; свои fact_ids варианта мета — передаём
                mvar = meta_variant_for(meta, k)
                own = mvar['fact_ids'] if isinstance((mvar or {}).get('fact_ids'), list) else []
                head.append(_flat_slot(k, st, [{'id': 'meta', 'text': meta[k], 'status': 'draft'}], 'meta', own, [], 'meta'))
                mapping[(pid, '__head', k)] = f'{pid}/meta/{k}'
                for v in (meta_alternatives(meta, k) if alternatives else []):
                    alts.append(('__head', k, f'{pid}/meta/{k}', str(v.get('id')), str(v.get('text')),
                                 v['fact_ids'] if isinstance(v.get('fact_ids'), list) else []))
        og = page.get('og_template') or {}
        for k, st in OG_TEMPLATE_FIELDS:
            if str(og.get(k) or '').strip():
                head.append(_flat_slot(f'og_template-{k}', st, [{'id': 'a', 'text': og[k], 'status': 'draft'}], 'a', [], [], 'meta'))
                mapping[(pid, '__head', f'og_template-{k}')] = f'{pid}/og_template/{k}'
        if head:
            secs.append({'section_id': '__head', 'section_role': 'head', 'slots': head})
        pr = page.get('promise')
        if isinstance(pr, dict) and not pr.get('from') and variants_of(pr):
            genre = effective_genre(deck, page, None, 'subheadline', (pr.get('lint') or {}).get('profile'), vocab)[0]
            mv = main_variant(pr)
            secs.append({'section_id': '__promise', 'section_role': 'hero',
                         'slots': [_flat_slot('promise', 'subheadline', [mv] if mv else [], (mv or {}).get('id'),
                                              variant_fact_ids(pr, mv), pr.get('claim_flags'), genre)]})
            mapping[(pid, '__promise', 'promise')] = f'{pid}/promise'
            for v in (slot_alternatives(pr) if alternatives else []):
                alts.append(('__promise', 'promise', f'{pid}/promise', str(v.get('id')), str(v.get('text') or ''), variant_fact_ids(pr, v)))
        for s in sections_of(page):
            sid = str(s.get('section_id'))
            slots = []
            for sl in slots_of(s):
                genre = effective_genre(deck, page, s, sl.get('slot_type'), (sl.get('lint') or {}).get('profile'), vocab)[0]
                mv = main_variant(sl)
                slid = str(sl.get('slot_id'))
                slots.append(_flat_slot(slid, sl.get('slot_type'), [mv] if mv else [], (mv or {}).get('id'),
                                        variant_fact_ids(sl, mv), sl.get('claim_flags'), genre))
                mapping[(pid, sid, slid)] = f'{pid}/{sid}/{slid}'
                for v in (slot_alternatives(sl) if alternatives else []):
                    alts.append((sid, slid, f'{pid}/{sid}/{slid}', str(v.get('id')), str(v.get('text') or ''), variant_fact_ids(sl, v)))
            role = s.get('section_role') or role_of_block(vocab, s.get('block'))
            sec = {'section_id': sid, 'block': s.get('block') or '', 'slots': slots}
            if role:
                sec['section_role'] = role
            secs.append(sec)
        fp = {'page_id': pid, 'page_type': page.get('page_type'), 'meta': {}, 'sections': secs}
        out_pages.append(fp)
        for n, (sid, slid, path, vid, text, fids) in enumerate(alts, 1):
            pp = _copy.deepcopy(fp)
            pp['page_id'] = f'{pid}~alt~{n}'
            for sec in pp['sections']:
                for fs in sec['slots']:
                    if sec['section_id'] == sid and fs['slot_id'] == slid:
                        fs['variants'] = [{'id': vid, 'text': text, 'status': 'draft'}]
                        fs['chosen'] = vid
                        fs['fact_ids'] = [str(x) for x in fids or []]
            alt_map[(pp['page_id'], sid, slid)] = (path, vid)
            out_pages.append(pp)
    flat = {'version': 0, 'date': deck.get('date'), 'site': deck.get('site'), 'lang': deck.get('lang'),
            'facts_ref': deck.get('facts_ref'), 'pages': out_pages}
    for k in ('jurisdiction', 'legal_category'):
        if deck.get(k):
            flat[k] = deck[k]
    return {'copy_deck': flat}, mapping, alt_map


def _empty_counts():
    return {'errors': 0, 'warnings': 0, 'info': 0, 'rules': []}


def _bump(agg, level, rule):
    agg[{'error': 'errors', 'warning': 'warnings'}.get(level, 'info')] += 1
    if rule and rule not in agg['rules']:
        agg['rules'].append(rule)


def run_claims(deck, ctx, facts_path, rep, strict=False, all_variants=False, pages=None, timeout=240, final=False):
    """claims_check.py check на плоской копии → находки в rep и итоги по путям {путь: {errors, warnings, info, rules
    [, variants: {id: итоги}]}}: итоги пути — только текст слота (для статусов и записей); с all_variants у пути ещё
    variants — каждый живой невыбранный вариант, сверенный «как если бы выбран». None — утилита не отработала."""
    if not os.path.exists(CLAIMS_CHECK):
        rep.add('claims', 'error', 'COPY-D-TOOL', '—', f'нет {CLAIMS_CHECK}', 'Сверка с фактами — ворота; без неё статус checked не ставится.')
        return None
    flat, mapping, alt_map = flatten_for_claims(deck, ctx, pages, alternatives=all_variants)
    with tempfile.TemporaryDirectory(prefix='copydeck-') as td:
        dp, jp = os.path.join(td, 'deck-flat.yaml'), os.path.join(td, 'claims.json')
        with open(dp, 'w', encoding='utf-8') as fo:
            yaml.safe_dump(flat, fo, allow_unicode=True, sort_keys=False, width=160)
        # --all-variants claims_check не передаём: альтернативы — отдельными копиями страницы (flatten_for_claims)
        cmd = [sys.executable, CLAIMS_CHECK, 'check', dp, '--format', 'deck', '--json', jp, '--today', ctx.today, '--quiet']
        if facts_path:
            cmd += ['--facts', facts_path]
        if strict:
            cmd.append('--strict')
        if final:
            cmd.append('--final')   # демо-данные (example) — error: ворота публикации
        if deck.get('jurisdiction'):
            cmd += ['--jurisdiction', str(deck['jurisdiction'])]
        if deck.get('legal_category'):
            cats = deck['legal_category'] if isinstance(deck['legal_category'], list) else [deck['legal_category']]
            cmd += ['--legal-category', ','.join(str(c) for c in cats)]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            rep.add('claims', 'error', 'COPY-D-TOOL', '—', f'claims_check.py не уложился в {timeout} с', '')
            return None
        if p.returncode not in (0, 1) or not os.path.exists(jp):
            tail = (p.stderr or p.stdout or '').strip().splitlines()[-3:]
            rep.add('claims', 'error', 'COPY-D-TOOL', '—', f'claims_check.py не отработал (код {p.returncode}): {" | ".join(tail)}', 'Проверьте facts.yaml: claims_check.py lint-facts FACTS.')
            return None
        with open(jp, encoding='utf-8') as f:
            res = json.load(f)
        for line in (p.stderr or '').splitlines():
            if line.strip():
                rep.notes.append(f'claims_check: {line.strip()[:200]}')
    per_path = {path: _empty_counts() for path in mapping.values()}
    for (_pp, _sid, _slid), (path, vid) in alt_map.items():
        per_path.setdefault(path, _empty_counts()).setdefault('variants', {}).setdefault(vid, _empty_counts())
    kept = {lv: 0 for lv in LEVELS}
    allow = {hpath: claims_allow_of(holder, ctx.facts) for hpath, holder, _kind in claims_allow_holders(deck, pages)}
    n_allowed = 0
    # проекция смысла и иерархий (chain_inputs.py meaning-claims) — не страница: места фактов (use — на каких страницах и
    # в каких секциях факт уместен) на ней не сверяются
    projection, n_use = deck.get('projection') == 'meaning', 0
    for f in res.get('findings') or []:
        if projection and f.get('rule') == 'COPY-F-USE':
            n_use += 1
            continue
        parts = str(f.get('unit') or '').split('/')
        key = tuple(parts[:3])
        if '~alt~' in parts[0]:
            hit = alt_map.get(key)
            if hit is None:
                continue  # остальные тексты копии страницы уже сверены основным прогоном
            where, variant = hit
            agg = per_path[where]['variants'][variant]
        else:
            where = mapping.get(key, '/'.join(parts[:3]) if len(parts) >= 3 else (f.get('unit') or '—'))
            variant = parts[3] if len(parts) >= 4 else None
            agg = per_path.setdefault(where, _empty_counts())
        lvl = f.get('level', 'info')
        rule = f.get('rule', 'COPY-F-?')
        # место обхода — от ближнего к дальнему: слот, мета (тексты <page>/meta/<поле>), страница
        page_id = str(where).split('/')[0]
        places = [('slot', where)] + ([('meta', f'{page_id}/meta')] if str(where).startswith(f'{page_id}/meta/') else []) + [('page', page_id)]
        entry, scope, bad_entries = None, None, []
        for sc, hpath in places:
            ok_, bad_ = allow.get(hpath, ([], []))
            bad_entries += bad_
            if entry is None:
                entry, scope = claims_allow_covers(ok_, rule, str(f.get('fragment') or '')), sc
        if entry is not None:   # обход с причиной и тем, кто решил: не находка, в итоги пути не идёт — списком
            rep.allowed.append({'rule': rule, 'where': where, 'fragment': str(f.get('fragment') or '')[:90],
                                'message': f.get('message', ''), 'reason': entry['reason'], 'by': entry['by'], 'scope': scope,
                                **({'variant': variant} if all_variants and variant else {})})
            n_allowed += 1
            continue
        fix = f.get('fix', '')
        wrong = next((why for e, why in bad_entries if e['rule'] == rule or rule in CLAIMS_ALLOW_RULES.get(e['rule'], ())), None)
        if wrong:
            fix = (fix + ' ' if fix else '') + f'Запись claims_allow не обход: {wrong}.'
        rep.add('claims', lvl, rule, where, f.get('message', ''), fix,
                fragment=str(f.get('fragment') or '')[:90], claim_class=f.get('claim_class'),
                variant=variant if all_variants else None, fact_ids=f.get('fact_ids') or None)
        _bump(agg, lvl, f.get('rule'))
        kept[lvl if lvl in kept else 'info'] += 1
    summ = dict(res.get('summary') or {})
    if alt_map or n_allowed or n_use:
        summ.update({'error': kept['error'], 'warning': kept['warning'], 'info': kept['info']})
    if n_use:
        summ['use_skipped'] = n_use
        rep.notes.append(f'проекция смысла (projection: meaning): места фактов (use) не сверяются — находок COPY-F-USE снято {n_use}')
    if alt_map:
        summ['note'] = f'с --all-variants: {len(alt_map)} вариантов сверены копиями страницы; claims, supported, by_rule и by_class — по всем единицам копий'
    if n_allowed:
        summ['allowed'] = n_allowed   # обойдено claims_allow: error, warning и info — без них
    rep.tools['claims'] = {'tool': f"claims_check.py {res.get('version')}", 'summary': summ,
                           'facts': facts_path, 'rules_loaded': res.get('rules_loaded'), 'legal': res.get('legal'),
                           'units_checked': len(mapping), 'alternatives': len(alt_map), 'allowed': n_allowed}
    return per_path


BRIEF_TEXT_FIELDS = ('product.goal', 'product.description', 'product.primary_action', 'product.target_user', 'site.cta.label')


def brief_texts(brief):
    """Поля брифа холста, которые исполнитель читает как задание и которые могут попасть на страницу (product.goal,
    description, primary_action, target_user, site.cta.label, работа секций), — [(где, текст)]; хвост «; доказательства:
    …» у job не проверяется (это id фактов). Сверка — run_claims_text: задание исполнителю с обещанием без факта уходит на страницу."""
    out = []
    for path in BRIEF_TEXT_FIELDS:
        cur = brief
        for part in path.split('.'):
            cur = cur.get(part) if isinstance(cur, dict) else None
        if isinstance(cur, str) and cur.strip():
            out.append((f'brief:{path}', one_line(cur)))
    for i, sct in enumerate(((brief.get('site') or {}).get('sections') or [])):
        if isinstance(sct, dict) and sct.get('job'):
            job = str(sct['job']).split('; доказательства:')[0]
            # «вопрос → опора»: стрелка — граница фразы; иначе эвристика имён claims_check принимает слово после «→» за
            # имя (ложные COPY-F-NAME «Вызвать», «Один»)
            job = re.sub(r'([?!.…]?)\s*→\s*', lambda m: (m.group(1) + ' ') if m.group(1) else '. ', job)
            out.append((f"brief:site.sections[{sct.get('id') or i}].job", one_line(job)))
    return out


def run_claims_text(items, ctx, facts_path, rep, tool='brief', timeout=120):
    """claims_check.py на строках вне copy deck (поля брифа): одна строка — одна единица текста. Находки — в rep."""
    if not items or not os.path.exists(CLAIMS_CHECK):
        return None
    with tempfile.TemporaryDirectory(prefix='copydeck-') as td:
        tp, jp = os.path.join(td, 'brief-texts.txt'), os.path.join(td, 'claims.json')
        with open(tp, 'w', encoding='utf-8') as fo:
            fo.write('\n'.join(t for _w, t in items) + '\n')
        cmd = [sys.executable, CLAIMS_CHECK, 'check', tp, '--format', 'text', '--json', jp, '--today', ctx.today, '--quiet']
        if facts_path:
            cmd += ['--facts', facts_path]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        if p.returncode not in (0, 1) or not os.path.exists(jp):
            return None
        res = json.load(open(jp, encoding='utf-8'))
    n = 0
    for f in res.get('findings') or []:
        line = (f.get('location') or {}).get('line')
        where = items[line - 1][0] if isinstance(line, int) and 0 < line <= len(items) else 'brief'
        lvl = f.get('level', 'info')
        if lvl == 'error' and ('.job' in where or 'target_user' in where):
            lvl = 'warning'  # задание секции и аудитория — инструкции исполнителю, не текст страницы: сигнал, не ворота
        rep.add(tool, lvl, f.get('rule', 'COPY-F-?'), where, f.get('message', ''),
                (f.get('fix') or '') + ' Поле брифа холста — задание исполнителю и может попасть на страницу.',
                fragment=str(f.get('fragment') or '')[:90])
        n += 1
    return n


# ============================================================================================ lint: copy_lint.lint_text
_CL = {}


def lint_module():
    if 'm' not in _CL:
        _CL['m'] = None
        try:
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import copy_lint  # noqa: WPS433
            _CL['m'] = copy_lint
            if not os.environ.get('COPYDECK_NO_LINT_CACHE'):
                lint_cache(True)
        except Exception as e:  # noqa: BLE001
            _CL['err'] = f'{type(e).__name__}: {e}'
    return _CL['m']


def lint_cache(on=True):
    """Кэш загрузки правил для lint_text: API линтера перечитывает YAML и компилирует ≈ 430 правил на каждый вызов (≈ 0,5 с;
    copy deck на 35 текстов — 17 с против 0,7 с у copy_lint.py в режиме copy deck). Код линтера не меняется: в процессе
    copydeck загрузчики copy_lint.load_yaml и load_rules заменяются запоминающими обёртками (по пути и времени изменения
    файла; YAML отдаётся глубокой копией). Равенство результатов с кэшем и без — --selftest. Выключить:
    COPYDECK_NO_LINT_CACHE=1."""
    C = _CL.get('m')
    if C is None:
        return False
    if not hasattr(C, '_copydeck_orig'):
        C._copydeck_orig = (C.load_yaml, C.load_rules)
    orig_yaml, orig_rules = C._copydeck_orig
    if not on:
        C.load_yaml, C.load_rules = orig_yaml, orig_rules
        _CL['cache'] = False
        return True
    ycache, rcache = {}, {}

    def load_yaml_cached(path):
        try:
            k = (str(path), os.path.getmtime(path))
        except OSError:
            return orig_yaml(path)
        if k not in ycache:
            ycache[k] = orig_yaml(path)
        return _copy.deepcopy(ycache[k])

    def load_rules_cached(extra=None, profiles=None, log=None):
        files = sorted(str(x) for x in C.LEXICON_DIR.glob('*.yaml'))
        stamp = tuple((f, os.path.getmtime(f)) for f in files)
        ext = json.dumps((profiles or {}).get('external_rules'), sort_keys=True, default=str, ensure_ascii=False)
        key = (tuple(extra or ()), ext, stamp)
        if key not in rcache:
            lg = []
            rcache[key] = (orig_rules(extra, profiles, lg), lg)
        rules, lg = rcache[key]
        if log is not None:
            log.extend(lg)
        return rules
    C.load_yaml, C.load_rules = load_yaml_cached, load_rules_cached
    _CL['cache'] = True
    return True


def _allow_list(raw):
    out = []
    for a in raw if isinstance(raw, list) else ([raw] if raw else []):
        if isinstance(a, dict) and a.get('rule'):
            out.append((str(a['rule']), str(a.get('reason') or '')))
        elif isinstance(a, str):
            out.append((a, ''))
    return out


def _allowed(f, allow):
    """lint_allow по правилам линтера: шаблон fnmatch по id; артефакты (ART) и данные (CNT) не подавляются."""
    if f.get('group') in ('ART', 'CNT'):
        return None
    for pat, reason in allow:
        if fnmatch.fnmatch(str(f.get('id')), pat):
            return reason or '—'
    return None


def page_markdown(deck, page):
    """Markdown-проекция выбранных текстов страницы для прохода страницы: заголовки — #/##/###, проза — абзацы,
    отзывы — «>», прочие короткие слоты — пункты списка (не проза), надзаголовок — капсом перед заголовком (так
    copy_lint.parse_markdown распознаёт его как eyebrow). Мета, OG и готовое сообщение мессенджера (на странице его
    нет) сюда не входят."""
    lines = []
    for s in sections_of(page):
        pairs = [(sl, chosen_variant(sl)) for sl in slots_of(s) if sl.get('slot_type') != PREFILL_SLOT_TYPE]
        eyebrows = [norm_ws(v.get('text')).upper() for sl, v in pairs if v and sl.get('slot_type') == 'eyebrow' and str(v.get('text') or '').strip()]
        for sl, v in pairs:
            if not v or sl.get('slot_type') == 'eyebrow':
                continue
            t = str(v.get('text') or '').strip()
            if not t:
                continue
            st = sl.get('slot_type') or 'body'
            lvl = HEADING_LEVEL.get(st)
            if lvl:
                lines.append('')
                if eyebrows:
                    lines.append(eyebrows.pop(0))
                lines.append('#' * lvl + ' ' + norm_ws(t))
            elif st in PROSE_SLOT_TYPES:
                lines += ['', t]
            elif st == 'testimonial-quote':
                lines += ['', '> ' + norm_ws(t)]
            else:
                lines += ['', '- ' + norm_ws(t)]
        for e in eyebrows:
            lines += ['', '- ' + e.capitalize()]
    return '\n'.join(lines).strip() + '\n'


def run_lint(deck, ctx, rep, final=False, all_variants=False, page_pass=True, pages=None, facts_path=None):
    """copy_lint.lint_text по каждому тексту (свой slot_type и жанр) + проход страницы. Линтер получает файл фактов
    (facts_path, без него — файл фактов ctx): адреса и названия мест из его сущностей вида place правило о слове на
    «-ая,» не трогает. → {путь: итоги}; None — нет линтера."""
    C = lint_module()
    if C is None:
        rep.add('lint', 'error', 'COPY-D-TOOL', '—', f'copy_lint.py не импортируется: {_CL.get("err")}', '')
        return None
    facts_path = str(facts_path or getattr(ctx.facts, 'path', None) or '')
    vocab = ctx.vocab
    lang = (deck.get('lang') or 'auto').split('-')[0] if deck.get('lang') else 'auto'
    try:
        _rules = C.load_rules(profiles=C.load_profiles(), log=[])
        doc_scope = {r.id for r in _rules if getattr(r, 'scope', '') == 'doc'}
        no_fact = {r.id for r in _rules if getattr(r, 'requires_no_fact', False)}
    except Exception:  # noqa: BLE001
        doc_scope, no_fact = set(), set()
    cache, per_path, notes, n_calls = {}, {}, [], 0
    parity = {'meta_fact_ids': 0, 'rules': [], 'paths': []}   # что снял meta.fact_ids, а copy_lint.py на deck покажет
    for page in pages_of(deck):
        pid = str(page.get('page_id'))
        if (pages and pid not in pages) or (page.get('status') or 'draft') == 'rejected':
            continue
        for u in text_units(deck, page, include_meta=True, all_variants=all_variants):
            slot = u['slot'] or {}
            if u['kind'] in ('meta', 'og'):
                genre, prof = 'meta', ''
            else:
                genre, prof = effective_genre(deck, page, u['section'], u['slot_type'], (slot.get('lint') or {}).get('profile'), vocab)
            text = u['text']
            blank = {'profile': prof or genre, 'errors': 0, 'warnings': 0, 'info': 0, 'suppressed': 0, 'verdict': 'clean'}
            agg = per_path.setdefault(u['path'], dict(blank))
            if not u.get('chosen', True):  # альтернатива (--all-variants): свои итоги, статус слота они не трогают
                agg = agg.setdefault('variants', {}).setdefault(str(u['variant']), dict(blank))
            if not text.strip():
                continue
            key = (text, genre, u['slot_type'] or '', prof, lang)
            if key not in cache:
                try:
                    cache[key] = C.lint_text(text, genre=genre, lang=lang, slot_type=u['slot_type'] or '', profile=prof, facts=facts_path)
                    n_calls += 1
                except (Exception, SystemExit) as e:  # noqa: BLE001
                    rep.add('lint', 'error', 'COPY-D-TOOL', u['path'], f'lint_text: {type(e).__name__}: {e}', 'Проверьте жанр и профиль слота.')
                    cache[key] = None
            res = cache[key]
            if not res:
                continue
            for n in res.get('notes') or []:
                if n not in notes and not n.startswith('жанр не задан'):
                    notes.append(n)
            # обход: у слота — свой lint_allow; у мета и OG-шаблона — lint_allow страницы, как в режиме copy deck линтера
            allow = _allow_list((page if u['kind'] in ('meta', 'og') else slot).get('lint_allow'))
            # lint_text не знает fact_ids слота: повторяем режим copy deck линтера — правила requires_no_fact и
            # an-number-without-fact молчат при fact_ids; явный пустой fact_ids — warning, как у линтера для copy deck
            refs = u['fact_ids']
            explicit_empty = (u['kind'] == 'slot' and 'fact_ids' in slot and not refs)
            for f in res.get('findings') or []:
                if (f.get('position') or {}).get('unit', 0) < 0 or f.get('id') in doc_scope:
                    continue  # находки документа — в проходе страницы
                if refs and (f.get('id') in no_fact or f.get('id') == 'an-number-without-fact'):
                    if u['kind'] == 'meta' and u.get('chosen', True):
                        parity['meta_fact_ids'] += 1
                        parity['rules'] += [f.get('id')] if f.get('id') not in parity['rules'] else []
                        parity['paths'] += [u['path']] if u['path'] not in parity['paths'] else []
                    continue
                lvl = f.get('level')
                if f.get('id') == 'an-number-without-fact' and explicit_empty and lvl == 'info':
                    lvl = 'warning'
                if final and f.get('id') == 'art-placeholder-marker' and lvl != 'error':
                    lvl = 'error'
                    agg['final_escalated'] = agg.get('final_escalated', 0) + 1
                if lvl not in LEVELS:
                    continue
                why = _allowed(f, allow)
                if why:
                    agg['suppressed'] += 1
                    rep.notes.append(f"lint_allow: {f.get('id')} @ {u['path']}: {why}")
                    continue
                rep.add('lint', lvl, f.get('id'), u['path'], f.get('message', ''), f.get('replacement', ''),
                        fragment=str(f.get('fragment') or '')[:90], marker_id=f.get('marker_id'), group=f.get('group'),
                        variant=u['variant'] if all_variants else None)
                agg[{'error': 'errors', 'warning': 'warnings'}.get(lvl, 'info')] += 1
            agg['verdict'] = 'fail' if agg['errors'] else ('review' if agg['warnings'] else 'clean')
        if page_pass:
            md = page_markdown(deck, page)
            pg = effective_genre(deck, page, None, None, None, vocab)[0]
            if pg == 'meta':
                pg = 'landing'
            try:
                res = C.lint_text(md, genre=pg, lang=lang, fmt='md', facts=facts_path)
                n_calls += 1
            except (Exception, SystemExit) as e:  # noqa: BLE001
                rep.add('lint', 'error', 'COPY-D-TOOL', pid, f'lint_text (страница): {type(e).__name__}: {e}', '')
                continue
            allow = _allow_list(page.get('lint_allow'))
            agg = {'profile': pg, 'errors': 0, 'warnings': 0, 'info': 0, 'suppressed': 0}
            for f in res.get('findings') or []:
                if not ((f.get('position') or {}).get('unit', 0) < 0 or f.get('id') in doc_scope):
                    continue
                if f.get('id') == 'an-lists-of-three':
                    continue  # артефакт проекции: короткие слоты — пункты списка
                lvl = f.get('level')
                if lvl not in LEVELS:
                    continue
                why = _allowed(f, allow)
                if why:
                    agg['suppressed'] += 1
                    rep.notes.append(f"lint_allow страницы: {f.get('id')} @ {pid}: {why}")
                    continue
                rep.add('lint', lvl, f.get('id'), pid + PAGE_PASS, f.get('message', ''), f.get('replacement', ''),
                        fragment=str(f.get('fragment') or f.get('context') or '')[:90], marker_id=f.get('marker_id'), group=f.get('group'))
                agg[{'error': 'errors', 'warning': 'warnings'}.get(lvl, 'info')] += 1
            m = res.get('metrics') or {}
            agg['metrics'] = {'words': (m.get('all') or {}).get('words'), 'markers_per_100w': (m.get('markers') or {}).get('per_100w'),
                              'prose_words': (m.get('prose') or {}).get('words') if m.get('prose') else 0,
                              'dash_punct_per_100w': (m.get('prose') or {}).get('dash_punct_per_100w') if m.get('prose') else None,
                              'concreteness_per_100w': (m.get('prose') or {}).get('concreteness_per_100w') if m.get('prose') else None}
            per_path[pid + PAGE_PASS] = agg
    rep.tools['lint'] = {'tool': f'copy_lint {getattr(C, "VERSION", "?")} (lint_text)', 'calls': n_calls, 'texts': len(cache),
                         'rules_cache': bool(_CL.get('cache')), 'facts': facts_path or None, 'notes': notes}
    if parity['meta_fact_ids']:
        # два пути линтера: copy_lint.py на copy deck не читает meta.fact_ids, copydeck — читает
        rep.tools['lint']['parity_copy_lint'] = parity
        rep.notes.append(f"meta.fact_ids сняли {parity['meta_fact_ids']} находок линтера в мета ({', '.join(parity['rules'])}; "
                         f"{', '.join(parity['paths'][:4])}): copy_lint.py на этом copy deck их покажет — он не читает meta.fact_ids "
                         '; ворота — copydeck.py check')
    for n in notes:
        rep.notes.append(f'copy_lint: {n}')
    return per_path


# ============================================================================================ вывод
ORDER = {'error': 0, 'warning': 1, 'info': 2}
TOOL_ORDER = {'claims': 0, 'lint': 1, 'validate': 2, 'brief': 3, 'export': 4, 'approve': 5}


def render_text(rep, head, verbose=False, limit=80):
    L = [head]
    for tool in ('claims', 'lint', 'validate', 'brief', 'export'):
        if tool in rep.tools or any(f['tool'] == tool for f in rep.findings):
            t = rep.tools.get(tool) or {}
            name = t.get('tool') or tool
            extra = f" · схема: {t['schema_engine']}" if t.get('schema_engine') else ''
            L.append(f"  {tool:9} {name}: {rep.count('error', tool)} error, {rep.count('warning', tool)} warning, {rep.count('info', tool)} info{extra}")
    s = rep.summary()
    L.append(f"Итог: {s['error']} error · {s['warning']} warning · {s['info']} info → " + ('ворота не пройдены' if s['error'] else 'ворота пройдены'))
    shown = 0
    for f in sorted(rep.findings, key=lambda x: (ORDER[x['level']], TOOL_ORDER.get(x['tool'], 9))):
        if f['level'] == 'info' and not verbose:
            continue
        if shown >= limit:
            L.append(f'  … ещё {len([x for x in rep.findings if verbose or x["level"] != "info"]) - shown} (полный список — --json или --md)')
            break
        frag = f" «{f['fragment']}»" if f.get('fragment') else ''
        L.append(f"  {f['level'].upper():7} {f['tool']:8} {f['rule'][:28]:28} {str(f['where'])[:46]:46}{frag} — {f['message'][:150]}")
        shown += 1
    return '\n'.join(L + render_allowed(rep))


def render_allowed(rep):
    """Обходы сверки claims_allow — отдельным списком: решение человека (by) с причиной, а не находка."""
    if not rep.allowed:
        return []
    L = [f'Обходы сверки claims_allow — решение человека, не находки ({len(rep.allowed)}):']
    for x in rep.allowed:
        frag = f" «{x.get('fragment') or x.get('value')}»" if (x.get('fragment') or x.get('value')) else ''
        L.append(f"  {x['rule'][:28]:28} {str(x['where'])[:46]:46}{frag} — {x['reason'][:150]} ({x['by']})")
    return L


def render_md(rep, title, meta_line):
    s = rep.summary()
    L = [f'# {title}', '', meta_line, '',
         f"**Итог:** {s['error']} error · {s['warning']} warning · {s['info']} info — " + ('ворота не пройдены' if s['error'] else 'ворота пройдены'), '',
         '| Утилита | Версия | error | warning | info |', '|---|---|---|---|---|']
    for tool in ('claims', 'lint', 'validate'):
        if tool in rep.tools or any(f['tool'] == tool for f in rep.findings):
            t = rep.tools.get(tool) or {}
            L.append(f"| {tool} | {t.get('tool') or t.get('schema_engine') or '—'} | {rep.count('error', tool)} | {rep.count('warning', tool)} | {rep.count('info', tool)} |")
    esc = lambda x: str(x or '').replace('|', '\\|').replace('\n', ' ')
    if rep.findings:
        L += ['', '| № | Уровень | Утилита | Правило | Где | Фрагмент | Что не так | Что сделать |', '|---|---|---|---|---|---|---|---|']
        for i, f in enumerate(sorted(rep.findings, key=lambda x: (ORDER[x['level']], TOOL_ORDER.get(x['tool'], 9))), 1):
            L.append(f"| {i} | {f['level']} | {f['tool']} | {esc(f['rule'])} | {esc(f['where'])} | {esc(f.get('fragment', ''))[:60]} | {esc(f['message'])[:200]} | {esc(f.get('fix'))[:160]} |")
    if rep.allowed:
        L += ['', '**Обходы сверки claims_allow** — решение человека, не находки:', '',
              '| Правило | Где | Фрагмент | Причина | Кто решил |', '|---|---|---|---|---|']
        L += [f"| {esc(x['rule'])} | {esc(x['where'])} | {esc(x.get('fragment') or x.get('value'))[:60]} | {esc(x['reason'])[:200]} | {esc(x['by'])} |" for x in rep.allowed]
    if rep.notes:
        L += ['', '**Заметки:**'] + [f'- {n}' for n in dict.fromkeys(rep.notes)]
    return '\n'.join(L) + '\n'


def write_outputs(a, rep, command, extra=None):
    payload = {'tool': 'copydeck.py', 'skill_version': kbpaths.skill_version(), 'version': VERSION, 'date': DATE,
               'command': command, 'input': getattr(a, 'deck', None),
               'today': getattr(a, 'today', None), 'summary': rep.summary(), 'tools': rep.tools,
               'findings': sorted(rep.findings, key=lambda x: (ORDER[x['level']], TOOL_ORDER.get(x['tool'], 9))),
               'allowed': rep.allowed, 'notes': list(dict.fromkeys(rep.notes))}
    payload.update(extra or {})
    if getattr(a, 'json', None):
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=1, default=str)
    if getattr(a, 'md', None):
        with open(a.md, 'w', encoding='utf-8') as f:
            f.write(render_md(rep, f'copydeck {command} · {os.path.basename(str(getattr(a, "deck", "")))}',
                              f"copydeck.py {VERSION} · {payload['today']} · facts: `{(rep.tools.get('claims') or {}).get('facts') or getattr(a, 'facts', None) or '—'}`"))
    return payload


# ============================================================================================ команды проверок
def open_deck(path):
    try:
        with open(path, encoding='utf-8') as f:
            raw = f.read()
        data = json.loads(raw) if path.lower().endswith('.json') else yaml.safe_load(raw)
    except (OSError, yaml.YAMLError, json.JSONDecodeError) as e:
        raise SystemExit(f'copydeck: не читается {path}: {e}')
    return deep_dates(data)


def resolve_facts_path(a, deck):
    if getattr(a, 'facts', None):
        return a.facts
    ref = deck.get('facts_ref')
    if ref and looks_like_path(ref):
        p = rel_to(a.deck, ref)
        return p if p and os.path.exists(p) else None
    return None


def make_ctx(a, deck):
    fp = resolve_facts_path(a, deck)
    facts = load_facts(fp) if fp else None
    ctx = Ctx(a.deck, facts, today_iso(getattr(a, 'today', None)), plan_path=getattr(a, 'plan', None))
    return ctx, fp


def cmd_validate(a):
    data = open_deck(a.deck)
    deck = deck_root(data)
    ctx, fp = make_ctx(a, deck)
    a.today = ctx.today
    rep = validate(data, ctx, final=a.final, use_jsonschema=not a.no_jsonschema)
    write_outputs(a, rep, 'validate')
    if not a.quiet:
        print(render_text(rep, f'copydeck validate · {a.deck} · {ctx.today} · facts: {fp or "—"}', a.verbose))
    return 1 if rep.count('error') else 0


def cmd_claims(a):
    data = open_deck(a.deck)
    deck = deck_root(data)
    ctx, fp = make_ctx(a, deck)
    a.today = ctx.today
    rep = Report()
    run_claims(deck, ctx, fp, rep, a.strict, a.all_variants, final=a.final)
    write_outputs(a, rep, 'claims')
    if not a.quiet:
        print(render_text(rep, f'copydeck claims · {a.deck} · {ctx.today} · facts: {fp or "— (все числа и имена — без опоры)"}', a.verbose))
    if not rep.tools.get('claims'):
        return EXIT_NO_CLAIMS
    return 1 if rep.count('error') else 0


def cmd_lint(a):
    data = open_deck(a.deck)
    deck = deck_root(data)
    ctx = Ctx(a.deck, None, today_iso(getattr(a, 'today', None)))
    a.today = ctx.today
    rep = Report()
    per = run_lint(deck, ctx, rep, a.final, a.all_variants, not a.no_page_pass, facts_path=resolve_facts_path(a, deck))
    write_outputs(a, rep, 'lint', {'slots': per})
    if not a.quiet:
        print(render_text(rep, f'copydeck lint · {a.deck} · {ctx.today}', a.verbose))
    if per is None:
        return 2                                    # линтер не импортируется — ошибка окружения
    return 1 if rep.count('error') else 0


def _lint_rec(r, prof_default, today, h, tool):
    return {'profile': r.get('profile') or prof_default or 'landing', 'errors': r['errors'], 'warnings': r['warnings'],
            'info': r['info'], 'suppressed': r.get('suppressed', 0), 'verdict': r.get('verdict', 'clean'),
            'checked_at': today, 'text_hash': h, 'tool': tool or 'copy_lint'}


def _claims_rec(r, today, h):
    return {'errors': r['errors'], 'warnings': r['warnings'], 'info': r['info'], 'rules': list(r['rules']),
            'checked_at': today, 'text_hash': h, 'tool': 'claims_check'}


def error_paths(rep, fresh=None):
    """Места находок уровня error, которые держат повышение статуса: путь слота, варианта, мета, страницы или «—» у
    находки всего файла; находка прохода страницы линтером — место страницы. Находка невыбранного варианта (check
    --all-variants сверяет его «как если бы выбрали»; fresh — свежие итоги по путям) выбранный текст не держит."""
    out = set()
    for f in rep.findings:
        if f['level'] != 'error':
            continue
        w = str(f['where'])
        alts = (((fresh or {}).get(w) or {}).get(f['tool']) or {}).get('variants') or {}
        if f.get('variant') is not None and str(f['variant']) in alts:
            continue
        out.add(w[:-len(PAGE_PASS)] if w.endswith(PAGE_PASS) else w)
    return out


def path_held(path, held):
    """Есть ли error на пути или под ним: у слота — и на его вариантах, у страницы — и на её секциях, слотах, мета."""
    return any(w == path or w.startswith(path + '/') for w in held)


def apply_records(data, claims_pp, lint_pp, today, promote=False, held=(), log=None):
    """Копия deck с записями lint и claims (text_hash проверенного текста) у выбранных текстов — и только у них: итоги
    невыбранных вариантов (check --all-variants) остаются в отчёте, в файл не пишутся. promote — перевести
    draft и assumed → checked там, где свежие claims и lint дали 0 error (checked — статус утилиты, approved — только
    человек) и на пути текста нет error проверки (held — места находок error: error_paths). Страница draft или assumed
    становится checked, когда все её выбранные тексты не ниже checked и error нет ни на ней, ни у файла в целом: статус
    страницы — минимум статусов её текстов; страница checked или approved не меняется. log — словарь для сводки:
    promoted (пути текстов), pages (id страниц), held (пути текстов, оставленных из-за error).
    Свои fact_ids выбранного варианта переносятся в слот (прямые
    claims_check.py и copy_lint.py читают только слот); варианты без своих fact_ids при этом получают прежний список слота.
    → (копия, число записей)."""
    out = _copy.deepcopy(data)
    deck = deck_root(out)
    lint_tool = (f"copy_lint {getattr(lint_module(), 'VERSION', '?')}" if lint_module() else None)
    n = 0
    log = log if log is not None else {}
    log.update(promoted=[], pages=[], held=[])
    page_ids = [str(p.get('page_id')) for p in pages_of(deck)]
    file_held = any(not any(path_held(p, [w]) for p in page_ids) for w in held)   # error вне страниц: схема, корень, файл фактов
    for page in pages_of(deck):
        pid = page.get('page_id')
        targets = [(f"{pid}/{s.get('section_id')}/{sl.get('slot_id')}", sl) for s in sections_of(page) for sl in slots_of(s)]
        pr = page.get('promise')
        if isinstance(pr, dict) and not pr.get('from') and variants_of(pr):
            targets.append((f'{pid}/promise', pr))
        for path, sl in targets:
            v = chosen_variant(sl)
            if not v:
                continue
            h = text_hash(v.get('text') or '')
            prof_default = (sl.get('lint') or {}).get('profile')
            if lint_pp and path in lint_pp:
                sl['lint'] = _lint_rec(lint_pp[path], prof_default, today, h, lint_tool)
                n += 1
            if claims_pp and path in claims_pp:
                sl['claims'] = _claims_rec(claims_pp[path], today, h)
            if isinstance(v.get('fact_ids'), list) and list(map(str, v['fact_ids'])) != list(map(str, sl.get('fact_ids') or [])):
                old = list(sl.get('fact_ids') or [])
                for x in variants_of(sl):
                    if x is not v and not isinstance(x.get('fact_ids'), list):
                        x['fact_ids'] = old
                sl['fact_ids'] = list(v['fact_ids'])
            sl.setdefault('fact_ids', [])
            sl.setdefault('claim_flags', [])
            if promote and v.get('status', 'draft') in ('draft', 'assumed') and lint_pp and claims_pp and path in lint_pp and path in claims_pp \
                    and lint_pp[path]['errors'] == 0 and claims_pp[path]['errors'] == 0:
                if path_held(path, held):
                    log['held'].append(path)
                    continue
                v['status'] = 'checked'
                v['review'] = {'by': 'copydeck.py check --promote', 'at': today}
                log['promoted'].append(path)
        if promote and (page.get('status') or 'draft') in ('draft', 'assumed') and targets and not file_held and not path_held(str(pid), held) \
                and all(STATUS_RANK.get(_status_of(chosen_variant(sl)), 0) >= 1 for _p, sl in targets):
            page['status'] = 'checked'
            log['pages'].append(str(pid))
    return out, n


DECK_REF_FIELDS = ('facts_ref', 'voice_ref', 'copy_slots_ref', 'meaning_ref', 'source_ref', 'page_plan_ref')
PAGE_REF_FIELDS = ('hierarchy_ref',)


def refs_outside(data, src_path, out_path):
    """Относительные ссылки copy deck (facts_ref, voice_ref, copy_slots_ref, meaning_ref, source_ref, page_plan_ref,
    hierarchy_ref) считаются от папки исходного файла и при записи не меняются. Файл записан в другую папку — из неё
    ссылки не разрешаются: он рассчитан на возврат на место исходного. → предупреждение об этом или None (папка та же
    или относительных ссылок нет). Строки-описания (voice_ref без .yaml) ссылками не считаются."""
    if not src_path or not out_path:
        return None
    sd, od = os.path.dirname(os.path.abspath(src_path)), os.path.dirname(os.path.abspath(out_path))
    if sd == od:
        return None
    deck = deck_root(data)
    held = [k for k in DECK_REF_FIELDS if isinstance(deck.get(k), str) and looks_like_path(deck[k]) and not os.path.isabs(deck[k])]
    held += [k for k in PAGE_REF_FIELDS if any(isinstance(p.get(k), str) and looks_like_path(p[k]) and not os.path.isabs(p[k]) for p in pages_of(deck))]
    if not held:
        return None
    return (f"файл записан вне папки исходного copy deck: относительные ссылки ({', '.join(held)}) считаются от папки исходного "
            'файла и из новой папки не разрешаются — верните файл на место исходного')


def deck_header(data, what):
    """Шапка записанного copy deck — о файле, а не о прогоне: без даты и без пути источника (дата записи —
    copy_deck.date, кто и когда проверил и утвердил — записи lint, claims, review и approval). what — строки о том, как
    файл ведётся; утверждённые страницы называются все, одной строкой."""
    lines = list(what)
    done = [str(p.get('page_id')) for p in pages_of(deck_root(data)) if (p.get('status') or 'draft') == 'approved']
    if done:
        lines.append('утверждённые страницы: ' + ', '.join(done) + ' (copydeck.py approve; кто и когда — approval страницы)')
    return ''.join(f'# {x}\n' for x in lines)


HEAD_CHECKED = ('copy deck — записи lint и claims (text_hash проверенного текста) пишет copydeck.py check --update;',
                'checked ставит --promote при 0 error проверки, approved — только человек (copydeck.py approve)')


def dump_deck(data, path, what, src_path=None, date=None):
    """Запись copy deck (YAML) с шапкой deck_header(what). date — дата записи: ставится в copy_deck.date (дата
    последнего изменения). src_path — исходный файл: относительные ссылки остаются от его папки (refs_outside).
    Папка файла создаётся: первый copy deck поверхности пишется в ещё не заведённую copy/.
    → предупреждение о записи вне папки исходного файла или None."""
    if date:
        deck_root(data)['date'] = date
    warn = refs_outside(data, src_path, path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(deck_header(data, what))
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=140, default_flow_style=False)
    return warn


def cmd_check(a):
    data = open_deck(a.deck)
    deck = deck_root(data)
    ctx, fp = make_ctx(a, deck)
    a.today = ctx.today
    rep = Report()
    claims_pp = run_claims(deck, ctx, fp, rep, a.strict, a.all_variants, final=a.final)   # 1. факты и право
    lint_pp = run_lint(deck, ctx, rep, a.final, a.all_variants, not a.no_page_pass)  # 2. стиль
    fresh = {}
    for p, r in (claims_pp or {}).items():
        fresh.setdefault(p, {})['claims'] = r
    for p, r in (lint_pp or {}).items():
        fresh.setdefault(p, {})['lint'] = r
    validate(data, ctx, rep, final=a.final, use_jsonschema=not a.no_jsonschema, fresh=fresh,
             skip_fact_checks=claims_pp is not None)                              # 3. формат и статусы
    extra = {'slots': {p: fresh[p] for p in sorted(fresh)}}
    if a.update:
        held, log, later = (error_paths(rep, fresh) if a.promote else set()), {}, {}
        upd, n = apply_records(data, claims_pp, lint_pp, ctx.today, promote=a.promote, held=held, log=log)
        for _ in range(3 if a.promote else 0):
            # поднятый утилитой статус обязан пройти проверку нового статуса: что на checked даёт error, остаётся как было
            rv = validate(upd, ctx, Report(), final=a.final, use_jsonschema=not a.no_jsonschema, fresh=fresh, skip_fact_checks=claims_pp is not None)
            new = {str(f['where']): f for f in rv.findings if f['level'] == 'error' and str(f['where']) not in held}
            if not new:
                break
            later.update(new)
            held |= set(new)
            upd, n = apply_records(data, claims_pp, lint_pp, ctx.today, promote=True, held=held, log=log)
        warn = dump_deck(upd, a.update, HEAD_CHECKED, src_path=a.deck, date=ctx.today)
        rep.notes.append(f'--update: записи у {n} выбранных текстов' + (' (--all-variants — только отчёт: итоги невыбранных вариантов в файл не пишутся)' if a.all_variants else '') + f' → {a.update}')
        if warn:
            rep.notes.append(f'--update: {warn}')
            print(f'copydeck check: {warn}', file=sys.stderr)
        if a.promote:
            rep.notes.append(f"--promote: checked — текстов {len(log['promoted'])}" + (f", страниц {len(log['pages'])} ({', '.join(log['pages'])})" if log['pages'] else ', страницы не повышены')
                             + (f"; оставлены из-за error проверки: {', '.join(log['held'][:8])}{' …' if len(log['held']) > 8 else ''}" if log['held'] else ''))
            for w, f in list(later.items())[:8]:
                rep.notes.append(f"--promote: {w} — на статусе checked был бы error {f['rule']}: {f['message'][:120]}")
            extra['promote'] = log
        extra['updated'] = a.update
    write_outputs(a, rep, 'check', extra)
    if not a.quiet:
        print(render_text(rep, f'copydeck check · {a.deck} · {ctx.today} · facts: {fp or "—"}', a.verbose))
    if lint_pp is None:
        return 2                                    # линтер не импортируется — ошибка окружения
    if claims_pp is None:
        return EXIT_NO_CLAIMS
    return 1 if rep.count('error') else 0


# ============================================================================================ вход холста: copy.md и facts.md
# Выгрузка во вход холста (references/claude-design.md § 6): тексты страницы — pages/<page-id>/copy.md, факты поверхности —
# facts.md. Формат copy.md — ключ copy_md карты x-canvas-map схемы copy deck; его же пишет разбор исходников холста
# (scripts/claude-design/dc_texts.py), читают сборщик входа и приём правок (import-copy).
COPY_TITLE = 'Тексты страницы'
COPY_RULE = 'Тексты — дословно: не переводить, не сокращать, не дописывать. Строка слота: [<slot_id>] <статус>: текст.'
TYPO_LINE_RU = 'Типографика окончательная: кавычки «», тире (—), неразрывные пробелы и «₽» — как в тексте; тире — грамматика, а не стиль.'
FACTS_RULE = ('На странице — только факты раздела «Факты». Другое число, имя, дата, цена, рейтинг, клиент или цитата — '
              '[PLACEHOLDER: что] (раздел «Нет»).')
COPY_MD_SECTION_RX = re.compile(r'^##\s+(\?|[a-z0-9]+(?:[_-][a-z0-9]+)*)(?:\s+(.*?))?\s*$')
COPY_MD_SLOT_RX = re.compile(r'^\[(\?|[a-z0-9]+(?:[_-][a-z0-9]+)*)(?:\s+([^\]]*))?\](?:\s+([a-z]+))?:(?:\s(.*))?$')


def md_cell(s):
    return norm_ws(s).replace('|', '\\|')


def one_line(s):
    return norm_ws(str(s or '').replace('\n', ' '))


def copy_md_rules(schema=None):
    """Ключ copy_md карты x-canvas-map схемы copy deck: статусы по этапу, слоты этапа directions, невыгружаемые типы."""
    cm = (((schema or load_copy_schema()).get('x-canvas-map') or {}).get('copy_md')) or {}
    return {'stage_statuses': {k: list(v) for k, v in (cm.get('stage_statuses') or {}).items()},
            'directions_slot_types': list(cm.get('directions_slot_types') or ['headline', 'cta-label']),
            'not_exported': set(cm.get('not_exported') or ['image-alt', 'image-caption', 'in-image-text'])}


def parse_copy_md(text):
    """copy.md входа холста → ([{section_id, label, line, slots: [{slot_id, label, status, text, line}]}], заметки).
    section_id и slot_id — None у «## ?» и «[?]» (тексты холста без секции или слота плана). Строки «# …» и
    «<!-- … -->» пропускаются. Значение слота тянется до следующей строки слота, секции или «# …»: строки, начатые двумя
    пробелами, продолжают текст с новой строки, пустая строка между ними — граница абзаца внутри значения (так
    render_copy_md пишет текст в несколько абзацев); пустые строки после последней строки значения в текст не входят."""
    sections, notes, cur, last = [], [], None, None
    gap = 0   # пустые строки после текста слота: станут границей абзаца, если значение продолжится
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip():
            if last is not None:
                gap += 1
            continue
        if line.lstrip().startswith('<!--'):
            continue
        if raw.startswith('  ') and last is not None:
            last['text'] = (last['text'] + '\n' * (gap + 1) + raw[2:].rstrip()) if last['text'] else raw[2:].rstrip()
            gap = 0
            continue
        gap = 0
        st = line.strip()
        m = COPY_MD_SECTION_RX.match(st)
        if m:
            cur = {'section_id': None if m.group(1) == '?' else m.group(1), 'label': (m.group(2) or '').strip(), 'line': i, 'slots': []}
            sections.append(cur)
            last = None
            continue
        if st.startswith('#'):
            last = None
            continue
        m = COPY_MD_SLOT_RX.match(st)
        if m:
            if cur is None:
                cur = {'section_id': None, 'label': '', 'line': i, 'slots': []}
                sections.append(cur)
                notes.append(f'стр. {i}: строка слота до первой секции — секция «?»')
            status = m.group(3)
            if status and status not in STATUS_RANK:
                notes.append(f'стр. {i}: статус «{status}» не из {", ".join(STATUS_RANK)}')
            last = {'slot_id': None if m.group(1) == '?' else m.group(1), 'label': (m.group(2) or '').strip(),
                    'status': status, 'text': m.group(4) or '', 'line': i}
            cur['slots'].append(last)
            continue
        notes.append(f'стр. {i}: строка вне формата copy.md: «{st[:60]}»')
        last = None
    return sections, notes


def render_copy_md(sections, title_lines=()):
    """[{section_id, slots: [{slot_id, status, text}]}] → текст copy.md (строки текста — строками продолжения; пустая
    строка между абзацами — строкой из двух пробелов)."""
    L = [f'# {t}' for t in title_lines] + ([''] if title_lines else [])
    for sec in sections:
        L.append(f"## {sec.get('section_id') or '?'}" + (f" {sec['label']}" if sec.get('label') else ''))
        for sl in sec.get('slots') or []:
            head = f"[{sl.get('slot_id') or '?'}" + (f" {sl['label']}" if sl.get('label') else '') + ']'
            if sl.get('status'):
                head += f" {sl['status']}"
            parts = str(sl.get('text') or '').strip('\n').split('\n')
            L.append(f"{head}: {parts[0].strip()}".rstrip())
            L += ['  ' + x.strip() for x in parts[1:]]
        L.append('')
    return '\n'.join(L).rstrip() + '\n'


def export_copy_md(deck, page, stage, schema=None):
    """Тексты страницы для этапа холста. → (copy.md, строки [(секция, слот, статус)], пробелы [находка]). В copy.md —
    выбранный текст, если его статус разрешён этапом (x-canvas-map copy_md.stage_statuses); на этапе directions — только
    заголовок и кнопка первого экрана; alt, подписи и строки в картинках не выгружаются. Слот без текста статуса этапа в
    файл не пишется: пробел — находка COPY-D-STAGE (строка пробелов INPUT.md; на макете — error, на направлениях —
    warning)."""
    rules = copy_md_rules(schema)
    allowed = rules['stage_statuses'].get(stage)
    if allowed is None:
        raise SystemExit(f"этап «{stage}»: у copy.md этапы {', '.join(rules['stage_statuses'])}")
    pid = str(page.get('page_id'))
    secs = sections_of(page)
    if stage == 'directions':
        first = first_screen_section(page)
        secs = [first] if first is not None else []
    out, rows, gaps = [], [], []
    for s in secs:
        sid = str(s.get('section_id'))
        slots = []
        taken = set()
        for sl in slots_of(s):
            st = sl.get('slot_type')
            if st in rules['not_exported']:
                continue
            if stage == 'directions' and (st not in rules['directions_slot_types'] or st in taken):
                continue
            taken.add(st)
            path = f"{pid}/{sid}/{sl.get('slot_id')}"
            v = chosen_variant(sl)
            if v is None:
                gaps.append({'path': path, 'status': None, 'why': 'нет выбранного варианта (chosen)'})
                continue
            status = _status_of(v)
            text = str(v.get('text') or '')
            if status not in allowed:
                gaps.append({'path': path, 'status': status, 'why': f"текст в статусе {status}, а этап {stage} берёт {' · '.join(allowed)}"})
                continue
            if not text.strip():
                gaps.append({'path': path, 'status': status, 'why': 'пустой текст'})
                continue
            slots.append({'slot_id': str(sl.get('slot_id')), 'status': status, 'text': text.strip()})
            rows.append((sid, str(sl.get('slot_id')), status))
        if slots:
            out.append({'section_id': sid, 'slots': slots})
    lang = (deck.get('lang') or 'ru').split('-')[0]
    title = [f"{COPY_TITLE} {pid} — {deck.get('product_name') or deck.get('site') or ''} ({lang}), этап {stage}".replace(' —  (', ' (')]
    title.append(COPY_RULE)
    if lang == 'ru':
        title.append(TYPO_LINE_RU)
    return render_copy_md(out, title), rows, gaps


def fact_verbatims(f, lang):
    base = (f.get('lang') or 'ru').split('-')[0]
    if lang and lang != base:
        tr = (f.get('translations') or {}).get(lang) or {}
        vs = [x for x in tr.get('verbatim') or [] if x] or ([tr['canonical']] if tr.get('canonical') else [])
        return vs, bool(vs)
    return [x for x in f.get('verbatim') or [] if x], True


def fact_source_line(f):
    src = f.get('source') or {}
    s = ' / '.join(str(src[k]) for k in ('who', 'where', 'date') if src.get(k))
    if src.get('url'):
        s += f" ({src['url']})"
    return s or '—'


def fact_where(f, page=None, lang=None):
    """Колонка «где можно»: роли use → id секций страницы (или роли), слоты, «не в …», «рядом: …»."""
    use = f.get('use') or {}
    if not use or use.get('any'):
        return 'везде'
    roles = use.get('section_roles') or []
    secs = [str(s.get('section_id')) for s in sections_of(page or {}) if s.get('section_role') in roles or s.get('section_id') in roles]
    parts = []
    if secs:
        parts.append(', '.join(dict.fromkeys(secs)))
    elif roles:
        parts.append('роли: ' + ', '.join(roles))
    if use.get('slot_types'):
        parts.append('слоты: ' + ', '.join(use['slot_types']))
    if use.get('not_in'):
        parts.append('не в: ' + ', '.join(use['not_in']))
    near = ((f.get('translations') or {}).get(lang) or {}).get('requires_nearby') if lang and lang != (f.get('lang') or 'ru').split('-')[0] else None
    near = near or use.get('requires_nearby')
    if near:
        parts.append('рядом: ' + one_line(near))
    return '; '.join(parts) or 'везде'


def used_fact_ids(deck, page, facts):
    ids = []
    for u in text_units(deck, page):
        for ref in u['fact_ids']:
            f, _m = facts.resolve(ref) if facts else (None, None)
            if f is not None and f['id'] not in ids:
                ids.append(f['id'])
    return ids


def never_rows(facts, today, lang):
    """«Нельзя утверждать»: never_claim[] + x-never-claim-defaults без снимающего проверенного факта (never_claim_md карты
    фактов) → [(id, текст на языке страницы, lift)]."""
    rows = []
    pub = [f for f in facts.facts if not publish_issues(f, today, facts)] if facts else []
    pub_classes = {c for f in pub for c in f.get('claim_class') or []}
    legal_ok = {c for f in pub for c in f.get('claim_class') or [] if ((f.get('legal') or {}).get('review') or {}).get('status') == 'approved'}
    items = [dict(r, origin='project') for r in (facts.never if facts else [])]
    if not facts or (facts.data.get('never_claim_defaults', 'ru-default-1') != 'none'):
        items += [dict(r, origin='default') for r in load_facts_schema().get('x-never-claim-defaults') or []]
    for r in items:
        lift = r.get('lift', 'never')
        cls = set(r.get('claim_class') or [])
        if lift == 'with-fact' and cls and cls & pub_classes:
            continue
        if lift == 'legal-review' and cls and cls & legal_ok:
            continue
        text = ((r.get('translations') or {}).get(lang) or {}).get('text') or r.get('text') or ''
        if lang == 'en' and r.get('origin') == 'default' and r.get('id') in NEVER_EN:
            text = NEVER_EN[r['id']]
        rows.append((r.get('id'), text, lift))
    return rows


def export_facts_md(facts, today, lang, page=None, used=None, stage='mockup', product_name=''):
    """facts.md входа холста: «Факты» (публикуемые по publish_filter; демо-данные — с пометкой), «Нет» (пробелы и
    непубликуемые факты заглушкой), «Нельзя утверждать». → (текст, сводка {published, hidden, missing, never_rows,
    demo, status})."""
    F = ['## Факты', '', '| id | дословно | источник | где можно |', '|---|---|---|---|']
    M = ['## Нет', '', '| id | чего нет | на странице до ответа | кто даст |', '|---|---|---|---|']
    summ = {'published': 0, 'hidden': 0, 'missing': 0, 'never_rows': 0, 'demo': [], 'status': (facts.data.get('status') if facts else None),
            'lang_fallback': []}
    if facts:
        file_demo = bool(facts.data.get('example'))
        for f in facts.facts:
            if used is not None and f['id'] not in used:
                continue
            iss = publish_issues(f, today, facts)
            if iss:
                why = '; '.join(re.sub(r'^COPY-F-[A-Z-]+:\s*fact:[\w.-]+:\s*', '', x) for x in iss)
                resp = (f.get('responsible') or {}).get('role') or ((facts.data.get('owner') or {}).get('role')) or 'заказчик'
                M.append(f"| {md_cell(f['id'])} | {md_cell(f.get('canonical') or (f.get('verbatim') or [''])[0])} — пока не публикуется: {md_cell(why)} "
                         f"| [PLACEHOLDER: {md_cell(f['id'])}] | {md_cell(resp)} |")
                summ['hidden'] += 1
                continue
            vs, ok = fact_verbatims(f, lang)
            if not ok:
                summ['lang_fallback'].append(f['id'])
                vs = [x for x in f.get('verbatim') or [] if x]
            demo = file_demo or bool(f.get('example'))
            if demo:
                summ['demo'].append(f['id'])
            src = ('демо: вымышленные данные · ' if demo else '') + fact_source_line(f)
            for i, t in enumerate(vs, 1):
                rid = f['id'] if i == 1 else '%s.%d' % (f['id'], i)
                F.append(f"| {md_cell(rid)} | {md_cell(t)} | {md_cell(src)} | {md_cell(fact_where(f, page, lang))} |")
            summ['published'] += 1
        for m in facts.missing:
            M.append(f"| {md_cell(m.get('id'))} | {md_cell(m.get('what'))} | {md_cell(m.get('placeholder'))} | {md_cell(m.get('who'))} |")
            summ['missing'] += 1
    if summ['published'] == 0:
        F.append('| — | (фактов нет: любое число, имя, цена на странице — [PLACEHOLDER]) | — | — |')
    if len(M) == 4:
        M.append('| — | ничего | — | — |')
    nrows = never_rows(facts, today, lang)
    summ['never_rows'] = len(nrows)
    N = ['## Нельзя утверждать', ''] + ([f'- {one_line(t)};' for _id, t, _lift in nrows] or ['- ничего сверх фактов.'])
    head = [f"# Факты — {product_name or (facts.data.get('site') if facts else '') or ''} ({lang}), этап {stage}", f'# {FACTS_RULE}', '']
    return '\n'.join(head + F + [''] + M + [''] + N) + '\n', summ


def section_job(section, deck, page, facts, with_facts=True):
    """Работа секции для брифа холста (site.sections[].job): «<вопрос> → <сообщение>; доказательства: <id фактов>»."""
    msg = one_line(section.get('message'))
    q = one_line(section.get('question'))
    fids = []
    for sl in slots_of(section):
        for ref in variant_fact_ids(sl, chosen_variant(sl)):
            f, _m = facts.resolve(ref) if facts else (None, None)
            fid = f['id'] if f else str(ref).replace('fact:', '')
            if fid not in fids:
                fids.append(fid)
    base = f'{q} → {msg}' if q and msg else (msg or q or (section.get('section_role') or str(section.get('section_id'))))
    return base + (f'; доказательства: {", ".join(fids)}' if (fids and with_facts) else '')


def export_canvas(data, ctx, out_dir, page_id, stage, facts_scope='all'):
    """Выгрузка страницы во вход холста: out_dir/pages/<page-id>/copy.md и out_dir/facts.md. → (Report, сводка).
    Находки: validate deck (формат, статусы, стык), пробелы текстов этапа (COPY-D-STAGE: макет берёт литералы
    утверждённого copy deck — error; на направлениях — warning, пробел уходит строкой в INPUT.md), статус файла фактов
    (COPY-D-FACTS-STATUS: вход берёт факты confirmed — на направлениях warning, на макете error), демо-данные (info)."""
    rep = Report()
    deck = deck_root(data)
    validate(data, ctx, rep, final=False)
    live = [p for p in pages_of(deck) if (p.get('status') or 'draft') != 'rejected']
    page = next((p for p in live if str(p.get('page_id')) == str(page_id)), None) if page_id else (live[0] if len(live) == 1 else None)
    if page is None:
        rep.add('export', 'error', 'COPY-D-EXPORT', page_id or '—', 'нет такой страницы (или она rejected); страниц несколько — укажите --page', '')
        return rep, None
    pid = str(page.get('page_id'))
    lang = (deck.get('lang') or 'ru').split('-')[0]
    copy_md, rows, gaps = export_copy_md(deck, page, stage, ctx.schema)
    for g in gaps:
        rep.add('export', 'error' if stage == 'mockup' else 'warning', 'COPY-D-STAGE', g['path'], g['why'],
                'Текст этапа: направления — assumed · checked · approved, макет — approved (x-canvas-map copy_md).')
    facts = ctx.facts
    used = used_fact_ids(deck, page, facts) if (facts and facts_scope == 'used') else None
    facts_md, fsumm = export_facts_md(facts, ctx.today, lang, page, used, stage, deck.get('product_name') or '')
    if facts is None:
        rep.add('export', 'warning', 'COPY-D-EXPORT', '—', 'facts.yaml не подключён: в facts.md нет фактов — любое число на странице станет [PLACEHOLDER]', '')
    elif fsumm['status'] != 'confirmed':
        rep.add('export', 'error' if stage == 'mockup' else 'warning', 'COPY-D-FACTS-STATUS', '—',
                f"facts.yaml в статусе {fsumm['status'] or 'draft'}: вход холста берёт подтверждённые заказчиком факты (confirmed)",
                'Подтверждение фактов заказчиком — этап meaning (status: confirmed).')
    for fid in fsumm['demo']:
        rep.add('export', 'info', 'COPY-D-EXAMPLE', pid, f'fact:{fid} — демо-данные: на макете допустимо, в публикацию не идёт', '')
    for fid in fsumm['lang_fallback']:
        rep.add('export', 'warning', 'COPY-D-LANG', pid, f'fact:{fid}: нет translations.{lang} — в facts.md ушла формулировка оригинала', '')
    pdir = os.path.join(out_dir, 'pages', pid)
    os.makedirs(pdir, exist_ok=True)
    with open(os.path.join(pdir, 'copy.md'), 'w', encoding='utf-8') as f:
        f.write(copy_md)
    with open(os.path.join(out_dir, 'facts.md'), 'w', encoding='utf-8') as f:
        f.write(facts_md)
    summ = {'page': pid, 'stage': stage, 'rows': len(rows), 'gaps': len(gaps), 'files': [os.path.join('pages', pid, 'copy.md'), 'facts.md'],
            'facts_published': fsumm['published'], 'facts_hidden': fsumm['hidden'], 'missing': fsumm['missing'],
            'never_rows': fsumm['never_rows'], 'demo_facts': fsumm['demo'], 'facts_status': fsumm['status'], 'facts_scope': facts_scope,
            'publish_filter': 'claims_check.publishable_issues' if claims_module() is not None else 'свой (publish_filter)'}
    return rep, summ


def cmd_export(a):
    data = open_deck(a.deck)
    deck = deck_root(data)
    ctx, fp = make_ctx(a, deck)
    a.today = ctx.today
    out = a.out or str(kbpaths.out('text', 'export'))
    rep, summ = export_canvas(data, ctx, out, a.page, a.stage, a.facts_scope)
    write_outputs(a, rep, 'export', {'export': summ})
    if not a.quiet:
        print(render_text(rep, f'copydeck export · {a.deck} → {out} · этап {a.stage} · facts: {fp or "—"}', a.verbose))
        if summ:
            print('  файлы: ' + ', '.join(os.path.join(out, x) for x in summ['files']))
            print(f"  страница {summ['page']}: строк {summ['rows']}, пробелов этапа {summ['gaps']}; фактов {summ['facts_published']} "
                  f"(скрыто {summ['facts_hidden']}, демо {len(summ['demo_facts'])}), пробелов фактов {summ['missing']}, строк «Нельзя утверждать» {summ['never_rows']}")
    return 1 if rep.count('error') or not summ else 0


# ============================================================================================ приём правок текста с холста
def _next_variant_id(slot):
    used = {str(v.get('id')) for v in variants_of(slot)}
    for i in range(26 * 27):
        vid = chr(97 + i % 26) if i < 26 else chr(96 + i // 26) + chr(97 + i % 26)
        if vid not in used:
            return vid
    raise SystemExit('нет свободного id варианта')


def import_copy(data, copy_text, page_id, date=None, choose=False):
    """Правки заказчика на холсте → copy deck: изменённый текст слота — новый вариант source: customer, статус draft
    (дальше — сверка фактов и права, линтер, при 0 error — approved словом заказчика). choose — вариант сразу выбран, а
    страница checked или approved возвращается в draft. Тексты холста без секции или слота плана — находки «перенести в
    план?» (структура — этап page-plan). → (новый data | None, Report, сводка)."""
    rep = Report()
    out = _copy.deepcopy(data)
    deck = deck_root(out)
    page = next((p for p in pages_of(deck) if str(p.get('page_id')) == str(page_id)), None)
    if page is None:
        rep.add('import', 'error', 'COPY-D-IMPORT', str(page_id), 'нет такой страницы в copy deck', '')
        return None, rep, None
    sections, notes = parse_copy_md(copy_text)
    for n in notes:
        rep.add('import', 'warning', 'COPY-D-IMPORT', str(page_id), n, 'Синтаксис copy.md — x-canvas-map copy_md схемы copy deck.')
    date = date or today_iso()
    summ = {'changed': [], 'same': 0, 'unmapped': 0, 'unknown': 0, 'chosen': choose}
    seen = set()
    for sec in sections:
        s = next((x for x in sections_of(page) if sec.get('section_id') and str(x.get('section_id')) == sec['section_id']), None)
        for row in sec.get('slots') or []:
            where = f"{page_id}/{sec.get('section_id') or '?'}/{row.get('slot_id') or '?'}"
            if s is None or row.get('slot_id') is None:
                summ['unmapped'] += 1
                rep.add('import', 'warning', 'COPY-D-IMPORT-STRUCT', where, f"текст холста без {'секции' if s is None else 'слота'} плана: «{one_line(row.get('text'))[:60]}»",
                        'Вопрос заказчику «перенести в план?»: да — правка на этапе page-plan, нет — откат на холсте с его согласия.')
                continue
            sl = next((x for x in slots_of(s) if str(x.get('slot_id')) == row['slot_id']), None)
            if sl is None:
                summ['unknown'] += 1
                rep.add('import', 'warning', 'COPY-D-IMPORT-STRUCT', where, 'слота нет в copy deck', 'Новый слот — правка плана (этап page-plan).')
                continue
            seen.add((str(s.get('section_id')), str(sl.get('slot_id'))))
            cur = chosen_variant(sl)
            new = str(row.get('text') or '').strip()
            if cur is not None and norm_ws(cur.get('text')) == norm_ws(new):
                summ['same'] += 1
                continue
            same = next((v for v in variants_of(sl) if norm_ws(v.get('text')) == norm_ws(new) and v.get('source') == 'customer'), None)
            if same is None:
                vid = _next_variant_id(sl)
                sl.setdefault('variants', []).append({'id': vid, 'text': new, 'status': 'draft', 'source': 'customer',
                                                      'notes': f'правка заказчика на холсте, {date}'})
            else:
                vid = str(same.get('id'))
            summ['changed'].append({'path': where, 'variant': vid, 'was': one_line((cur or {}).get('text'))[:80]})
            if choose:
                sl['chosen'] = vid
    if choose and summ['changed'] and (page.get('status') or 'draft') in ('checked', 'approved'):
        page['status'] = 'draft'
        page.pop('approval', None)
    missing = [f"{page_id}/{s.get('section_id')}/{sl.get('slot_id')}" for s in sections_of(page) for sl in slots_of(s)
               if (str(s.get('section_id')), str(sl.get('slot_id'))) not in seen and sl.get('slot_type') not in copy_md_rules()['not_exported']
               and any(sec.get('section_id') == str(s.get('section_id')) for sec in sections)]
    for m in missing[:20]:
        rep.add('import', 'info', 'COPY-D-IMPORT', m, 'слота нет в copy.md холста: текст на холсте удалён или не выгружался этапом', 'Удаление текста — вопрос структуры: «перенести в план?».')
    return out, rep, summ


HEAD_IMPORTED = ('copy deck — правки заказчика с холста приняты вариантами source: customer (copydeck.py import-copy);',
                 'вариант заказчика — draft: сверка фактов и права, линтер, затем утверждение словом заказчика')


def cmd_import_copy(a):
    with open(a.input, encoding='utf-8') as f:
        text = f.read()
    data = open_deck(a.deck)
    day = today_iso(a.date) if a.date else today_iso()
    out, rep, summ = import_copy(data, text, a.page, day, a.choose)
    if out is None:
        print(render_text(rep, f'copydeck import-copy · {a.input} → {a.deck}: отказ', True))
        return 1
    warn = dump_deck(out, a.output, HEAD_IMPORTED, src_path=a.deck, date=day)
    print(a.output)
    if warn:
        print(f'  WARNING {warn}')
    print(f"  изменено слотов {len(summ['changed'])}, без изменений {summ['same']}, текстов без слота плана {summ['unmapped'] + summ['unknown']}"
          + (' · новые варианты выбраны (--choose)' if a.choose else ''))
    for c in summ['changed']:
        print(f"  {c['path']} → вариант {c['variant']}")
    for f in rep.findings:
        if f['level'] != 'info' or getattr(a, 'verbose', False):
            print(f"  {f['level'].upper():7} {f['rule']:22} {f['where']} — {f['message'][:120]}")
    return 0


# ============================================================================================ поля продукта брифа холста из смысла
DEVICE_RU = {'mobile': 'с телефона', 'desktop': 'с компьютера', 'mixed': 'с телефона и компьютера'}
GOAL_BASIS_OK = {'brief', 'customer', 'fact', 'voc'}


def _lcfirst(s):
    s = one_line(s)
    return s[:1].lower() + s[1:] if len(s) > 1 and s[1:2].islower() else s


def _source_names():
    """Имена источников трафика — словарь site (traffic_source)."""
    try:
        ns = (load_yaml_file(VOCAB_PATH) or {}).get('namespaces') or {}
        return {x['id']: x.get('name') or x['id'] for x in (ns.get('traffic_source') or {}).get('values') or [] if isinstance(x, dict) and x.get('id')}
    except Exception:  # noqa: BLE001
        return {}


def meaning_projection(meaning, traffic=None):
    """Поля продукта брифа холста из смысла (x-canvas-map meaning.schema.yaml): product.description («X — Y. Кому важнее
    всего: Z»), product.target_user («<сегмент>: <ситуация>. Знает: … Приходит: <источники>, <устройство>»; трафик —
    site-brief traffic [{traffic_source, share, device}]), product.goal (ядро ценностного предложения — только с
    основанием brief, customer, fact или voc и без классов boundaries.not_promised; иначе None — цель страницы из плана).
    → ({поле: текст}, заметки)."""
    m = meaning.get('meaning', meaning) if isinstance(meaning, dict) else {}
    out, notes = {}, []
    aud = [s for s in m.get('audience') or [] if isinstance(s, dict)]
    seg = next((s for s in aud if s.get('primary')), None)
    lvl = (m.get('awareness') or {}).get('level')
    srcs = sorted([x for x in traffic or [] if isinstance(x, dict)], key=lambda x: -(x.get('share') or 0))
    names = _source_names()
    if seg:
        parts = [f"{one_line(seg.get('name'))}: {_lcfirst(seg.get('situation'))}"]
        knows = one_line(seg.get('knows')).split(';')[0].strip()
        if knows:
            parts.append(knows if re.match(r'^(знает|не знает)', knows, re.I) else f'Знает: {knows}')
        elif lvl:
            parts.append(f'Уровень осведомлённости: {lvl}')
        if srcs:
            top = srcs[:2]
            where = ', '.join(_lcfirst(names.get(x.get('traffic_source') or x.get('source'), x.get('traffic_source') or x.get('source'))) for x in top)
            dev = DEVICE_RU.get(top[0].get('device'))
            parts.append(f'Приходит: {where}' + (f', {dev}' if dev else ''))
        out['product.target_user'] = '. '.join(p.rstrip('.') for p in parts)
    else:
        notes.append('meaning: нет основного сегмента — target_user не выведен')
    pos = m.get('positioning') or {}
    cat = one_line((pos.get('market_category') or {}).get('name'))
    theme = one_line(((pos.get('value_themes') or [{}])[0] or {}).get('theme'))
    fit_ids = (pos.get('best_fit') or {}).get('segment_ids') or []
    fit = next((s for s in aud if s.get('id') in fit_ids), seg)
    if cat and theme:
        desc = f'{cat[:1].upper()}{cat[1:]} — {_lcfirst(theme)}'
        if fit and fit.get('name'):
            desc += f'. Кому важнее всего: {_lcfirst(fit["name"])}'
        out['product.description'] = desc
    core = (m.get('value_proposition') or {}).get('core') or {}
    banned = {str(x.get('claim_class')) for x in (m.get('boundaries') or {}).get('not_promised') or [] if isinstance(x, dict) and x.get('claim_class')}
    if core.get('text') and ((core.get('basis') or {}).get('kind') in GOAL_BASIS_OK):
        cm = claims_module()   # маркеры класса без снятия отрицанием: «без усталости глаз» — тоже обещание здоровья
        hit = {cl for cl in banned for rx in (cm.CLASS_MARKERS.get(cl) or []) if rx.search(cm.soft(core['text']))} if cm is not None else set()
        if hit:
            notes.append(f"product.goal: ядро задевает классы boundaries.not_promised ({', '.join(sorted(hit))}) — цель страницы из плана")
        else:
            out['product.goal'] = one_line(core['text'])
    elif core.get('text'):
        notes.append(f"product.goal: основание ядра — {(core.get('basis') or {}).get('kind') or 'нет'} (нужно brief, customer, fact или voc) — цель страницы из плана")
    return out, notes


# ============================================================================================ export-assets
def export_assets(deck, page):
    lang = (deck.get('lang') or 'ru').split('-')[0]
    slots, notes = {}, []
    for s in sections_of(page):
        for sl in slots_of(s):
            st = sl.get('slot_type')
            if st not in ('image-alt', 'image-caption', 'in-image-text'):
                continue
            v = chosen_variant(sl)
            path = f"{page.get('page_id')}/{s.get('section_id')}/{sl.get('slot_id')}"
            ref = sl.get('asset_ref')
            if not ref:
                notes.append(f'{path}: нет asset_ref — пропущен')
                continue
            d = slots.setdefault(ref, {'id': ref, 'from': []})
            d['from'].append(path)
            t = one_line((v or {}).get('text'))
            if st == 'image-alt':
                d['alt'] = t
            elif st == 'image-caption':
                d['caption'] = t
            else:
                ii = sl.get('in_image') or {}
                txt = d.setdefault('text', {'mode': 'in_image', 'strings': [], 'fallback': ii.get('fallback') or 'html_overlay', 'ocr_check': True})
                script = ii.get('script') or ('Cyrillic' if cyr_share(t) > 0.5 else 'Latin')
                txt['strings'].append({'text': t, 'language': lang, 'script': script, 'role': ii.get('role') or 'label', 'position': ''})
                if len(txt['strings']) > 3:
                    notes.append(f'{ref}: строк в картинке {len(txt["strings"])} > 3 (ai-media 05/03 §7)')
    meta = page.get('meta') or {}
    og = {}
    if meta.get('og_image_alt'):
        og['alt'] = one_line(meta['og_image_alt'])
    ogt = page.get('og_template') or {}
    if ogt.get('kicker') or ogt.get('title'):
        og['template_text'] = {k: one_line(ogt[k]) for k in ('kicker', 'title') if ogt.get(k)}
    frag = {'plan_fragment_version': 1, 'source': f'copydeck.py {VERSION} export-assets', 'date': today_iso(),
            'page': {'id': page.get('page_id'), 'locale': lang}, 'slots': list(slots.values())}
    if og:
        frag['og'] = og
    if any('text' in d for d in slots.values()):
        notes.append('position, typography, color строк в картинке задаёт ai-media (asset-spec text.strings[]); здесь только текст, язык, письменность, роль')
    return frag, notes


def cmd_export_assets(a):
    data = open_deck(a.deck)
    deck = deck_root(data)
    live = [p for p in pages_of(deck) if (p.get('status') or 'draft') != 'rejected']
    page = next((p for p in live if str(p.get('page_id')) == a.page), None) if a.page else (live[0] if len(live) == 1 else None)
    if page is None:
        print('copydeck export-assets: укажите --page (страниц несколько или нет такой)', file=sys.stderr)
        return 2
    frag, notes = export_assets(deck, page)
    out = yaml.safe_dump(frag, allow_unicode=True, sort_keys=False, width=140)
    head = f'# фрагмент плана ассетов ai-media (01/01 §8; тексты — asset-spec text) из {os.path.basename(a.deck)}\n'
    if a.output:
        with open(a.output, 'w', encoding='utf-8') as f:
            f.write(head + out)
        print(a.output)
    else:
        print(head + out)
    for n in notes:
        print('  заметка:', n, file=sys.stderr)
    return 0


# ============================================================================================ export-variants (слепой выбор)
def _failed_checks(v):
    """Итоги проверок варианта с error для этого же текста — поле checks варианта, если оно у него записано (text_hash
    записи — этот текст или его нет)."""
    chk = v.get('checks') if isinstance(v.get('checks'), dict) else {}
    out = []
    for key in ('claims', 'lint'):
        rec = chk.get(key) if isinstance(chk.get(key), dict) else None
        if rec and (rec.get('errors') or 0) > 0 and (not rec.get('text_hash') or rec['text_hash'] == text_hash(v.get('text') or '')):
            out.append(f"{key}: {rec['errors']} error")
    return out


def export_variants(deck, page_ids=None, min_variants=2, seed=0, include_failed=False):
    """Листы для слепого выбора: варианты слота под метками A, B, C… в случайном, но воспроизводимом
    порядке, без source/generated (модель скрыта). Мета тоже (2–3 варианта title; выбранный сейчас текст, которого
    нет среди вариантов, идёт под id «meta»). Варианты с error в своих checks (claims или lint этого же текста) на
    лист не идут: выбирают из прошедших ворота; include_failed — показать и их.
    → (markdown, key {путь: {метка: id варианта}}, excluded {путь: [(id, почему)]})."""
    import random
    L = ['# Слепой выбор вариантов', '',
         'Для каждого слота выберите лучший вариант (или ранжируйте). Модели и авторы скрыты; ключ меток — у ведущего.', '']
    key, excluded = {}, {}
    for page in pages_of(deck):
        pid = str(page.get('page_id'))
        if (page_ids and pid not in page_ids) or (page.get('status') or 'draft') == 'rejected':
            continue
        targets = [(f"{pid}/{s.get('section_id')}/{sl.get('slot_id')}", sl.get('slot_type'), variants_of(sl), s) for s in sections_of(page) for sl in slots_of(s)]
        pr = page.get('promise')
        if isinstance(pr, dict) and not pr.get('from'):
            targets.insert(0, (f'{pid}/promise', 'promise', variants_of(pr), None))
        meta = page.get('meta') or {}
        mv = meta.get('variants') if isinstance(meta.get('variants'), dict) else {}
        for k, st in META_FIELDS:
            vs = [v for v in mv.get(k) or [] if isinstance(v, dict)]
            if not vs:
                continue
            if norm_ws(meta.get(k)) and not any(norm_ws(v.get('text')) == norm_ws(meta.get(k)) for v in vs):
                vs = [{'id': 'meta', 'text': meta[k], 'status': 'draft'}] + vs
            targets.append((f'{pid}/meta/{k}', st, vs, None))
        for path, stype, variants, sec in targets:
            vs = [v for v in variants if v.get('status') != 'rejected' and str(v.get('text') or '').strip()]
            if not include_failed:
                bad = [(str(v.get('id')), '; '.join(_failed_checks(v))) for v in vs if _failed_checks(v)]
                if bad:
                    excluded[path] = bad
                    vs = [v for v in vs if not _failed_checks(v)]
            if len(vs) < min_variants:
                continue
            rnd = random.Random(int(hashlib.sha1(f'{seed}:{path}'.encode()).hexdigest()[:8], 16))
            rnd.shuffle(vs)
            labels = [chr(65 + i) for i in range(len(vs))]
            key[path] = {lab: str(v.get('id')) for lab, v in zip(labels, vs)}
            ctx_line = one_line(sec.get('question') or sec.get('message') or '') if sec is not None else ''
            if '/meta/' in path:
                ctx_line = 'как страница выглядит в поиске и в превью ссылки' + (f" (план теста: {one_line(meta.get('test_plan')).rstrip('.')})" if meta.get('test_plan') else '')
            L += [f"## {path} · {stype or 'promise'}"] + ([f'Контекст: {ctx_line}'] if ctx_line else []) + ['']
            L += [f'- **{lab}**: {one_line(v.get("text"))}' for lab, v in zip(labels, vs)] + ['', 'Выбор: ___', '']
    return '\n'.join(L).rstrip() + '\n', key, excluded


def cmd_export_variants(a):
    data = open_deck(a.deck)
    md, key, excluded = export_variants(deck_root(data), [a.page] if a.page else None, a.min, a.seed, a.include_failed)
    with open(a.output, 'w', encoding='utf-8') as f:
        f.write(md)
    with open(a.key, 'w', encoding='utf-8') as f:
        f.write(f'# ключ меток слепого выбора (copydeck.py export-variants, seed {a.seed}) — не показывать выбирающему\n')
        for path, bad in excluded.items():
            f.write(f'# не на листе (error в checks варианта): {path} — ' + ', '.join(f'{i} ({why})' for i, why in bad) + '\n')
        yaml.safe_dump(key, f, allow_unicode=True, sort_keys=False)
    print(f'{a.output} ({len(key)} слотов); ключ — {a.key}')
    for path, bad in excluded.items():
        print(f'  не на листе (error в checks): {path} — ' + ', '.join(f'{i} ({why})' for i, why in bad))
    return 0


# ============================================================================================ approve
def approve_page(data, ctx, page_id, by, at, note=''):
    """Утверждение страницы человеком: все выбранные тексты — checked с актуальным text_hash и 0 error; заглушка
    названного пробела facts.yaml missing[] — warning (публикацию держит validate --final), заглушка без пробела — отказ;
    тогда варианты → approved (review), страница → approved (approval), журнал процесса (edit_log, отклонённые варианты)
    уходит — clean_process_log. facts_ref — путь, а файла фактов по нему нет (копия copy deck вне своей папки) — отказ. Утверждённая страница обязана пройти validate (требования статуса approved, стык с
    утверждённым планом, правила текста): error этой страницы — отказ. Пустые meta.title и meta.description — warning
    (ворота публикации — validate --final); обходы claims_allow страницы — списком rep.allowed, неверная запись —
    warning. → (новый data | None, Report)."""
    rep = Report()
    out = _copy.deepcopy(data)
    deck = deck_root(out)
    page = next((p for p in pages_of(deck) if str(p.get('page_id')) == page_id), None)
    if page is None:
        rep.add('approve', 'error', 'COPY-D-APPROVE', page_id, 'нет такой страницы', '')
        return None, rep
    if ctx.facts is None and looks_like_path(deck.get('facts_ref')):
        # относительные ссылки считаются от папки исходного файла: копия в другой папке фактов не находит
        rep.add('approve', 'error', 'COPY-D-APPROVE', page_id, f"facts.yaml не найден по facts_ref «{deck.get('facts_ref')}» от папки файла: "
                'заглушки и факты страницы не с чем сверить', 'Утверждайте файл в папке copy deck: ссылки считаются от папки исходного файла.')
        return None, rep
    targets = [(f"{page_id}/{s.get('section_id')}/{sl.get('slot_id')}", sl) for s in sections_of(page) for sl in slots_of(s)]
    pr = page.get('promise')
    if isinstance(pr, dict) and not pr.get('from') and variants_of(pr):
        targets.append((f'{page_id}/promise', pr))
    for path, sl in targets:
        v = chosen_variant(sl)
        if v is None:
            rep.add('approve', 'error', 'COPY-D-APPROVE', path, 'нет выбранного варианта', '')
            continue
        t = str(v.get('text') or '')
        if _status_of(v) not in ('checked', 'approved'):
            rep.add('approve', 'error', 'COPY-D-APPROVE', path, f'статус {_status_of(v)}: утверждается только проверенный текст', 'copydeck.py check --update OUT --promote')
        for key in ('lint', 'claims'):
            rec = sl.get(key) or {}
            if rec.get('errors', 1) != 0 or rec.get('text_hash') != text_hash(t):
                rep.add('approve', 'error', 'COPY-D-APPROVE', path, f'запись {key}: нет 0 error для этого текста (text_hash)', 'Перепроверьте: check --update.')
        gaps, loose = placeholder_links(t, ctx.facts, sl.get('missing_ids'))
        if loose:
            rep.add('approve', 'error', 'COPY-D-APPROVE', path, f'заглушка без пробела в facts.yaml: {", ".join(loose)}',
                    'Заглушка повторяет placeholder пробела facts.yaml missing[] или названа словами своего пробела (missing_ids слота); пробела нет — заведите его '
                    '(это вопрос владельцу факта) либо перепишите без утверждения.')
        elif gaps:
            rep.add('approve', 'warning', 'COPY-D-APPROVE', path, 'заглушка пробела ' + ', '.join(f'missing:{g}' for g in gaps)
                    + ': утверждению и макету не мешает, публикацию держит validate --final', 'Закройте пробел в facts.yaml до публикации.')
    meta = page.get('meta') or {}
    for k in ('title', 'description'):
        if not norm_ws(meta.get(k)):
            rep.add('approve', 'warning', 'COPY-D-APPROVE', f'{page_id}/meta/{k}', f'пустое meta.{k}: заполнить до публикации',
                    'Мета макету не нужна; ворота публикации — copydeck.py validate --final.')
    rep.allowed = claims_allow_listed(deck, ctx.facts, [page_id])
    if rep.count('error'):
        return None, rep
    for path, sl in targets:
        v = chosen_variant(sl)
        v['status'] = 'approved'
        v['review'] = {'by': by, 'at': at}
    page['status'] = 'approved'
    page['approval'] = {'by': by, 'at': at, **({'note': note} if note else {})}
    cleaned = clean_process_log(page)
    rv = validate(out, ctx, Report(), final=False)
    errs = [f for f in rv.findings if f['level'] == 'error' and (f['where'] in ('—', page_id) or str(f['where']).startswith(page_id + '/'))]
    for f in errs:
        rep.add('approve', 'error', 'COPY-D-APPROVE', f['where'], f"утверждённая страница не проходит validate: {f['rule']} — {f['message']}", f.get('fix', ''))
    for f in rv.findings:   # неверная запись claims_allow — не обход: утверждение идёт, заказчик видит
        if f['rule'] == 'COPY-D-CLAIMS-ALLOW' and (f['where'] == page_id or str(f['where']).startswith(page_id + '/')):
            rep.add('approve', f['level'], f['rule'], f['where'], f['message'], f.get('fix', ''))
    if errs:
        return None, rep
    rep.tools['approve'] = {'removed': cleaned}
    if cleaned['edit_log'] or cleaned['rejected']:
        rep.notes.append(f"журнал процесса ушёл: edit_log у {cleaned['edit_log']} текстов, отклонённых вариантов {cleaned['rejected']} (история — git)")
    return out, rep


def process_holders(page):
    """Держатели вариантов страницы: [(путь, слот)] — слоты секций и обещание со своими вариантами."""
    pid = page.get('page_id')
    out = [(f"{pid}/{s.get('section_id')}/{sl.get('slot_id')}", sl) for s in sections_of(page) for sl in slots_of(s)]
    pr = page.get('promise')
    if isinstance(pr, dict) and not pr.get('from'):
        out.append((f'{pid}/promise', pr))
    return out


def clean_process_log(page):
    """При утверждении журнал процесса уходит (.claude/rules/forward-only.md § Машинные файлы слоёв): edit_log слотов и
    обещания, отклонённые варианты (и альтернативы мета со статусом rejected). Остаются выбранные тексты с записями
    проверок, живые альтернативы, selection (compared может называть удалённые варианты — это история выбора), review,
    approval. → {'edit_log': n, 'rejected': n}."""
    n_log = n_rej = 0
    for _path, sl in process_holders(page):
        if sl.pop('edit_log', None):
            n_log += 1
        keep = [v for v in variants_of(sl) if v.get('status') != 'rejected' or v is chosen_variant(sl)]
        n_rej += len(variants_of(sl)) - len(keep)
        if isinstance(sl.get('variants'), list):
            sl['variants'] = keep
    mv = (page.get('meta') or {}).get('variants')
    if isinstance(mv, dict):
        for k, vs in mv.items():
            if isinstance(vs, list):
                keep = [v for v in vs if not (isinstance(v, dict) and v.get('status') == 'rejected')]
                n_rej += len(vs) - len(keep)
                mv[k] = keep
    return {'edit_log': n_log, 'rejected': n_rej}


def cmd_approve(a):
    data = open_deck(a.deck)
    a.facts, a.today = None, a.at
    ctx, _fp = make_ctx(a, deck_root(data))
    out, rep = approve_page(data, ctx, a.page, a.by, today_iso(a.at), a.note or '')
    if out is None:
        print(render_text(rep, f'copydeck approve · {a.deck} · страница {a.page}: отказ', True))
        return 1
    warn = dump_deck(out, a.output, HEAD_CHECKED, src_path=a.deck, date=today_iso(a.at))
    print(a.output)
    if warn:
        print(f'  WARNING {warn}')
    for f in rep.findings:   # предупреждения утверждения: пустая мета, неверная запись claims_allow
        print(f"  {f['level'].upper():7} {f['rule']} {f['where']} — {f['message']}")
    for n in rep.notes:
        print('  ' + n)
    for line in render_allowed(rep):
        print('  ' + line)
    return 0


# ============================================================================================ skeleton: каркас из плана страницы
META_SLOT_FIELD = {'meta-title': 'title', 'meta-description': 'description', 'og-title': 'og_title',
                   'og-description': 'og_description', 'og-image-alt': 'og_image_alt'}
AWARENESS_IDS = ('unaware', 'problem-aware', 'solution-aware', 'product-aware', 'most-aware')


def _plan_refs(refs_list):
    fact_ids, missing_ids = [], []
    for r in refs_list or []:
        r = str(r)
        if r.startswith('missing:'):
            missing_ids.append(r[8:])
        elif r.startswith('fact:'):
            fact_ids.append(r[5:])
    return fact_ids, missing_ids


def _ref_doc(base_dir, ref):
    """Файл по ссылке плана (путь от папки base_dir, с «#/ключ/…» — его часть: смысл внутри брифа) → (словарь, папка
    файла); нет ссылки, файла, части или файл не читается — ({}, None): каркас собирается и без соседнего файла."""
    path, _, pointer = str(ref or '').partition('#')
    if not looks_like_path(path):
        return {}, None
    p = os.path.normpath(os.path.join(base_dir, path))
    try:
        d = deep_dates(load_yaml_file(p))
    except (OSError, yaml.YAMLError):
        return {}, None
    for key in [k for k in pointer.split('/') if k]:
        d = d.get(key) if isinstance(d, dict) else None
    return (d, os.path.dirname(p)) if isinstance(d, dict) else ({}, None)


def skeleton_from_plan(plan, plan_path, deck_path, facts_ref=None, voice_ref=None, date=None):
    """Каркас copy deck из плана страницы (стык — x-site-map): страница (page.id, page_type), секции с текстовыми
    слотами (id, роль, блок, вопрос, опоры), слоты (id, слот словаря, анатомия, группа, число вариантов), fact_ids и
    missing_ids — из binds слотов данных, мета — из page_slots, главная кнопка и обещание первого экрана — из слотов
    действия и hero. Голос — voice_ref смысла (refs.meaning плана, у брифа — meaning_ref или meaning), отраслевой режим
    права — constraints.legal_category брифа (refs.brief), иначе legal_category смысла: без них проверки голоса и права
    молча идут по умолчаниям. missing_ids получает только пробел, у которого до ответа на странице стоит заглушка:
    пробел с fallback rewrite-without или omit-block заглушки не оставляет. Текстовый слот, который называет
    target.prefill действия секции (id слота) или главного призыва страницы (page.cta_target, «секция.слот»), — готовое
    сообщение мессенджера: в notes слота — чьё оно; ссылка в пустоту или на слот другого типа — заметкой. Иерархий в плане больше одной без вариантов и правила сведения — заметкой
    (plan_hierarchy_gap). Тексты пусты (статус draft): их пишет агент «допущением» (assumed). → (data, заметки)."""
    notes = []
    pl = plan.get('page') or {}
    refs = plan.get('refs') or {}
    pdir = os.path.dirname(os.path.abspath(plan_path))
    ddir = os.path.dirname(os.path.abspath(deck_path))

    def rel(p):
        return os.path.relpath(os.path.normpath(os.path.join(pdir, p)), ddir)
    lang = (pl.get('lang') or str(pl.get('locale') or 'ru')[:2] or 'ru')
    deck = {'version': 1, 'date': date or today_iso(), 'site': plan.get('site') or 'site', 'lang': lang}
    if facts_ref:
        deck['facts_ref'] = facts_ref
    elif refs.get('facts') and looks_like_path(refs['facts']):
        deck['facts_ref'] = rel(refs['facts'])
    brief, bdir = _ref_doc(pdir, refs.get('brief'))
    mean, mdir = _ref_doc(pdir, refs.get('meaning'))
    if mdir is None and bdir is not None:   # смысл без своей ссылки в плане: отдельным файлом брифа или внутри брифа
        mean, mdir = _ref_doc(bdir, brief.get('meaning_ref'))
        if mdir is None and isinstance(brief.get('meaning'), dict):
            mean, mdir = brief['meaning'], bdir
    vref = voice_ref or mean.get('voice_ref')
    if voice_ref:
        deck['voice_ref'] = voice_ref
    elif isinstance(vref, str) and vref.strip():   # путь — от папки файла смысла; строка-описание — как есть
        deck['voice_ref'] = os.path.relpath(os.path.normpath(os.path.join(mdir, vref)), ddir) if looks_like_path(vref) else vref
    else:
        notes.append('voice_ref не найден (смысл по refs плана его не называет): голос текстов проверяться не будет — задайте --voice-ref')
    meaning = str(refs.get('meaning') or '')
    if meaning and '#' not in meaning and looks_like_path(meaning):
        deck['meaning_ref'] = rel(meaning)
    deck['page_plan_ref'] = os.path.relpath(os.path.abspath(plan_path), ddir)
    jur = [j for j in pl.get('jurisdiction') or [] if j in ('ru', 'eu', 'us', 'other')]
    if jur:
        deck['jurisdiction'] = jur[0]
    cats = (brief.get('constraints') or {}).get('legal_category') if isinstance(brief.get('constraints'), dict) else None
    cats = cats or mean.get('legal_category')
    cats = [str(c) for c in ([cats] if isinstance(cats, str) else cats or []) if c]
    if cats:
        deck['legal_category'] = cats
    # пробелы, у которых до ответа на странице нет заглушки (текст пишется без утверждения или блок снят)
    gaps, _fdir = _ref_doc(ddir, deck.get('facts_ref'))
    no_stub, skipped_gaps = {}, []
    for m in gaps.get('missing') or []:
        if isinstance(m, dict) and m.get('fallback') in ('rewrite-without', 'omit-block'):
            for k in [m.get('id')] + list(m.get('aliases') or []):
                no_stub[str(k)] = m['fallback']
    pid = str(pl.get('id') or 'page')
    page = {'page_id': pid, 'page_type': pl.get('page_type'), 'status': 'draft'}
    if pl.get('awareness') in AWARENESS_IDS:
        page['awareness'] = pl['awareness']
        hs = [h for h in (refs.get('hierarchy') or []) if isinstance(h, str) and h.endswith(f"-{pl['awareness']}.yaml")]
        if len(hs) == 1:
            page['hierarchy_ref'] = rel(hs[0])
    gap = plan_hierarchy_gap(plan)
    if gap:
        notes.append(f'{gap}. {HIERARCHY_FIX}')
    ps = plan.get('page_slots') or {}
    meta = {'title': '', 'description': ''}
    for t in ps.get('text') or []:
        fld = META_SLOT_FIELD.get(str((t or {}).get('slot')))
        if fld:
            meta[fld] = ''
        elif t:
            notes.append(f"слот страницы {t.get('id')} ({t.get('slot')}) — не мета: текст в copy deck не заводится")
    mids = [x for refs_ in plan_binds({'page_slots': ps}).values() for x in _plan_refs(refs_)[0]]
    if mids:
        meta['fact_ids'] = list(dict.fromkeys(mids))
    page['meta'] = meta
    cta_target = pl.get('cta_target') if isinstance(pl.get('cta_target'), dict) else {}
    cta_prefill = str(cta_target.get('prefill') or '').partition('.')   # «секция.слот» готового сообщения главного призыва
    sections = []
    for s in plan.get('sections') or []:
        if not isinstance(s, dict) or not s.get('id'):
            continue
        texts = plan_text_slots(s)
        # готовое сообщение мессенджера — текстовый слот секции, который называет target.prefill: у действия секции — id
        # слота, у главного призыва страницы (page.cta_target) — «секция.слот»
        prefill = {str(a_['target']['prefill']): f"действия «{a_.get('id')}»" for a_ in ((s.get('slots') or {}).get('action') or [])
                   if isinstance(a_, dict) and isinstance(a_.get('target'), dict) and a_['target'].get('prefill')}
        if cta_prefill[0] == str(s['id']) and cta_prefill[2]:
            prefill.setdefault(cta_prefill[2], 'главного призыва страницы (page.cta_target)')
        for pf, owner in prefill.items():
            hit = next((t for t in texts if str(t['id']) == pf), None)
            if hit is None:
                notes.append(f"{s['id']}: target.prefill {owner} называет слот «{pf}», а такого текстового слота в секции плана нет — "
                             'слот готового сообщения не заведён (правка плана)')
            elif hit.get('slot') != PREFILL_SLOT_TYPE:
                notes.append(f"{s['id']}/{pf}: target.prefill {owner} называет слот типа {hit.get('slot')}, а готовое сообщение "
                             f'мессенджера — слот типа {PREFILL_SLOT_TYPE}')
        if not texts:
            continue
        binds = plan_binds(s)
        assets = {}   # текстовый слот alt или подписи → слот плана ассетов «<секция>-<медиа>» (page-plan: media-slot)
        for m in ((s.get('slots') or {}).get('media') or []):
            if isinstance(m, dict) and m.get('id'):
                for key in ('alt', 'caption'):
                    if m.get(key) and m[key] != 'decorative':
                        assets[str(m[key])] = f"{s['id']}-{m['id']}"
        sec = {'section_id': str(s['id']), 'site_section_id': str(s['id'])}
        if s.get('role'):
            sec['section_role'] = s['role']
        if s.get('block'):
            sec['block'] = s['block']
        if s.get('question'):
            sec['question'] = s['question']
        if s.get('carries'):
            sec['carries'] = list(s['carries'])
        slots = []
        for t in texts:
            n = int(t.get('variants') or 1)
            fids, miss = _plan_refs(binds.get(str(t['id'])))
            skipped_gaps += [f"{s['id']}/{t['id']} ← missing:{g} ({no_stub[g]})" for g in miss if g in no_stub]
            miss = [g for g in miss if g not in no_stub]
            sl = {'slot_id': str(t['id']), 'slot_type': t.get('slot'), 'site_slot_id': t.get('anatomy') or str(t['id'])}
            if t.get('group'):
                sl['group'] = t['group']
            if assets.get(str(t['id'])):
                sl['asset_ref'] = assets[str(t['id'])]
            sl['variants'] = [{'id': chr(97 + i), 'text': '', 'status': 'draft'} for i in range(max(1, min(n, 5)))]
            sl['chosen'] = 'a'
            sl['fact_ids'] = fids
            if miss:
                sl['missing_ids'] = miss
            sl['claim_flags'] = []
            lead = f"готовое сообщение мессенджера {prefill[str(t['id'])]}" if str(t['id']) in prefill else ''
            intent = '; '.join(x for x in (lead, one_line(t.get('intent')), one_line(t.get('note'))) if x)
            if intent:
                sl['notes'] = f'план: {intent}'
            slots.append(sl)
        sec['slots'] = slots
        sections.append(sec)
    page['sections'] = sections
    first = first_screen_section(page)
    if first is not None:
        lead = next((sl for sl in slots_of(first) if sl.get('slot_type') == 'subheadline'), None)
        if lead is not None:
            page['promise'] = {'from': f"{pid}/{first['section_id']}/{lead['slot_id']}"}
        ps_first = next((x for x in plan.get('sections') or [] if isinstance(x, dict) and str(x.get('id')) == first['section_id']), {})
        prim = next((a for a in ((ps_first.get('slots') or {}).get('action') or []) if isinstance(a, dict) and a.get('style') == 'primary' and a.get('label')), None)
        if prim and any(str(sl.get('slot_id')) == str(prim['label']) for sl in slots_of(first)):
            page['cta_primary'] = f"{pid}/{first['section_id']}/{prim['label']}"
    order = ['page_id', 'page_type', 'status', 'awareness', 'hierarchy_ref', 'promise', 'cta_primary', 'meta', 'sections']
    deck['pages'] = [{k: page[k] for k in order if k in page}]
    skipped = [str(s.get('id')) for s in plan.get('sections') or [] if isinstance(s, dict) and not plan_text_slots(s)]
    if skipped:
        notes.append(f"секции без текстовых слотов в плане (в copy deck не заводятся): {', '.join(skipped)}")
    if skipped_gaps:
        notes.append('пробелы без заглушки на странице в missing_ids не ставятся (до ответа текст пишется без утверждения или блок снят): '
                     + ', '.join(skipped_gaps))
    return {'copy_deck': deck}, notes


HEAD_SKELETON = ('copy deck — каркас из плана страницы (copydeck.py skeleton): секции и текстовые слоты плана, план — page_plan_ref;',
                 'тексты пусты (draft): их пишет агент «допущением» (assumed) из утверждённых смысла, фактов и голоса')


def cmd_skeleton(a):
    if os.path.exists(a.output) and not a.force:
        print(f'copydeck skeleton: {a.output} уже есть — тексты не перезаписываются (--force — заменить каркасом)', file=sys.stderr)
        return 2
    try:
        plan = deep_dates(load_yaml_file(a.plan) or {})
    except (OSError, yaml.YAMLError) as e:
        print(f'copydeck skeleton: план не читается: {a.plan}: {e}', file=sys.stderr)
        return 2
    if not isinstance(plan, dict) or 'page' not in plan or 'sections' not in plan:
        print(f'copydeck skeleton: {a.plan} — не план страницы (page-plan: page, sections)', file=sys.stderr)
        return 2
    data, notes = skeleton_from_plan(plan, a.plan, a.output, a.facts_ref, a.voice_ref, today_iso(a.date) if a.date else None)
    dump_deck(data, a.output, HEAD_SKELETON)
    page = deck_root(data)['pages'][0]
    n = sum(len(slots_of(s)) for s in sections_of(page))
    print(f"{a.output}: страница {page['page_id']}, секций {len(sections_of(page))}, текстовых слотов {n}")
    for x in notes:
        print('  заметка:', x)
    return 0


# ============================================================================================ apply-selection: голоса слепого выбора
SELECTION_METHODS = ('single', 'editor', 'customer', 'pairwise', 'judge', 'ab-test', 'human-pairwise', 'judge-pairwise')


def parse_votes_sheet(text):
    """Лист export-variants с заполненными строками «Выбор: B» (или «Выбор: B, A» — ранжирование) → {путь: метка | [метки]}."""
    votes, cur = {}, None
    for line in text.splitlines():
        m = re.match(r'^##\s+(\S+)\s+·', line.strip())
        if m:
            cur = m.group(1)
            continue
        m = re.match(r'^Выбор:\s*(.*)$', line.strip())
        if m and cur:
            labels = [x for x in re.split(r'[\s,;>]+', m.group(1).strip().strip('_')) if re.fullmatch(r'[A-Z]', x)]
            if labels:
                votes[cur] = labels[0] if len(labels) == 1 else labels
    return votes


def apply_selection(data, key, votes, method='customer', by='заказчик', at=None, ref=None):
    """Голоса слепого выбора → chosen и selection {method, by, at, compared, tally, ref}. Голос — метка («B»), ранжирование
    ([«B», «A»]) или счёт ({A: 1, B: 5}); метки — ключ export-variants. У мета выбранный текст пишется в meta.<поле>.
    Сменился выбранный текст — прежние записи lint и claims недействительны (check --update --promote); страница checked или
    approved возвращается в draft. → (новый data | None, Report, сводка)."""
    rep = Report()
    if method not in SELECTION_METHODS:
        rep.add('select', 'error', 'COPY-D-SELECT', '—', f'method «{method}» не из {", ".join(SELECTION_METHODS)}', '')
        return None, rep, None
    out = _copy.deepcopy(data)
    deck = deck_root(out)
    at = at or today_iso()
    summ = {'applied': [], 'changed_pages': set()}
    for path, vote in (votes or {}).items():
        labels = (key or {}).get(path)
        if not isinstance(labels, dict) or not labels:
            rep.add('select', 'error', 'COPY-D-SELECT', path, 'пути нет в ключе меток', 'Ключ — --key export-variants.')
            continue
        tally = None
        if isinstance(vote, dict):
            counts = {str(k): int(v) for k, v in vote.items()}
            best = max(counts.values()) if counts else 0
            top = [k for k, v in counts.items() if v == best]
            if len(top) != 1:
                rep.add('select', 'error', 'COPY-D-SELECT', path, f'ничья голосов: {", ".join(top)}', 'Решает человек: ещё один голос или выбор редактора.')
                continue
            win, tally = top[0], {labels[k]: v for k, v in counts.items() if k in labels}
        else:
            win = vote[0] if isinstance(vote, list) else str(vote)
        if win not in labels:
            rep.add('select', 'error', 'COPY-D-SELECT', path, f'метки «{win}» нет в ключе ({", ".join(labels)})', '')
            continue
        vid = labels[win]
        sel = {'method': method, 'by': by, 'at': at, 'compared': list(labels.values())}
        if tally:
            sel['tally'] = tally
        if ref:
            sel['ref'] = ref
        parts = path.split('/')
        page = next((p for p in pages_of(deck) if str(p.get('page_id')) == parts[0]), None)
        if page is None:
            rep.add('select', 'error', 'COPY-D-SELECT', path, 'нет такой страницы', '')
            continue
        if len(parts) == 3 and parts[1] == 'meta':
            meta = page.setdefault('meta', {})
            if vid != 'meta':
                v = next((x for x in (meta.get('variants') or {}).get(parts[2]) or [] if str(x.get('id')) == vid), None)
                if v is None:
                    rep.add('select', 'error', 'COPY-D-SELECT', path, f'варианта {vid} нет в meta.variants.{parts[2]}', '')
                    continue
                if norm_ws(meta.get(parts[2])) != norm_ws(v.get('text')):
                    summ['changed_pages'].add(parts[0])
                meta[parts[2]] = v.get('text')
            summ['applied'].append((path, vid))
            continue
        holder = page.get('promise') if (len(parts) == 2 and parts[1] == 'promise') else ((find_slot(deck, path) or (None, None, None))[2])
        if not isinstance(holder, dict) or not any(str(v.get('id')) == vid for v in variants_of(holder)):
            rep.add('select', 'error', 'COPY-D-SELECT', path, f'нет слота или варианта {vid}', '')
            continue
        if str(holder.get('chosen')) != vid:
            summ['changed_pages'].add(parts[0])
        holder['chosen'] = vid
        holder['selection'] = sel
        summ['applied'].append((path, vid))
    for p in pages_of(deck):
        if str(p.get('page_id')) in summ['changed_pages'] and (p.get('status') or 'draft') in ('checked', 'approved'):
            p['status'] = 'draft'
            p.pop('approval', None)
    if summ['changed_pages']:
        rep.notes.append('выбор сменил тексты: записи lint и claims этих слотов недействительны — copydeck.py check --update OUT --promote')
    summ['changed_pages'] = sorted(summ['changed_pages'])
    return out, rep, summ


def cmd_apply_selection(a):
    data = open_deck(a.deck)
    key = load_yaml_file(a.key) or {}
    if a.votes:
        votes = load_yaml_file(a.votes) or {}
    else:
        with open(a.sheet, encoding='utf-8') as f:
            votes = parse_votes_sheet(f.read())
    ref = ' · '.join(os.path.basename(x) for x in (a.sheet or a.votes, a.key) if x)
    day = today_iso(a.at) if a.at else today_iso()
    out, rep, summ = apply_selection(data, key, votes, a.method, a.by, day, ref)
    if out is None or rep.count('error'):
        print(render_text(rep, f'copydeck apply-selection · {a.deck}: отказ', True))
        return 1
    warn = dump_deck(out, a.output, HEAD_SELECTED, src_path=a.deck, date=day)
    print(a.output)
    print(f"  выбрано {len(summ['applied'])}: " + ', '.join(f'{p} → {v}' for p, v in summ['applied']))
    if warn:
        print(f'  WARNING {warn}')
    for n in rep.notes:
        print('  ' + n)
    return 0


# ============================================================================================ select: открытый выбор варианта
def select_variant(data, page_id, slot_ref, variant_id, method='customer', by='заказчик', at=None):
    """Открытый выбор варианта человеком: chosen слота или обещания и запись selection {method, by, at, compared —
    живые варианты слота}. slot_ref — «<section_id>/<slot_id>», id слота, если он один на странице, или «promise».
    Сменился текст, который проверялся как текст слота, — записи lint и claims относятся к другому тексту и
    недействительны (check --update --promote), страница checked или approved возвращается в draft; выбран тот же
    текст — статусы не меняются.
    → (новый data | None, Report, сводка {path, variant, changed})."""
    rep = Report()

    def refuse(where, msg, fix=''):
        rep.add('select', 'error', 'COPY-D-SELECT', where, msg, fix)
        return None, rep, None
    if method not in SELECTION_METHODS:
        return refuse('—', f'method «{method}» не из {", ".join(SELECTION_METHODS)}')
    out = _copy.deepcopy(data)
    page = next((p for p in pages_of(deck_root(out)) if str(p.get('page_id')) == str(page_id)), None)
    if page is None:
        return refuse(str(page_id), 'нет такой страницы')
    parts = [x for x in str(slot_ref).split('/') if x]
    if parts == ['promise'] or parts == [str(page_id), 'promise']:
        holder, path = page.get('promise'), f'{page_id}/promise'
        if not isinstance(holder, dict) or holder.get('from') or not variants_of(holder):
            return refuse(path, 'у обещания страницы нет своих вариантов', 'Обещание с promise.from выбирается в слоте, на который оно указывает.')
    else:
        hits = [(s, sl) for s in sections_of(page) for sl in slots_of(s)
                if parts and str(sl.get('slot_id')) == parts[-1] and (len(parts) == 1 or str(s.get('section_id')) == parts[-2])]
        if not hits:
            return refuse(f'{page_id}/{slot_ref}', 'нет такого слота', '--slot — <section_id>/<slot_id> страницы.')
        if len(hits) > 1:
            return refuse(f'{page_id}/{slot_ref}', 'слот с таким id есть в секциях: ' + ', '.join(str(s.get('section_id')) for s, _sl in hits),
                          'Укажите --slot <section_id>/<slot_id>.')
        holder, path = hits[0][1], f"{page_id}/{hits[0][0].get('section_id')}/{hits[0][1].get('slot_id')}"
    v = next((x for x in variants_of(holder) if str(x.get('id')) == str(variant_id)), None)
    if v is None:
        return refuse(path, f'варианта «{variant_id}» нет (есть: {", ".join(str(x.get("id")) for x in variants_of(holder))})')
    if v.get('status') == 'rejected':
        return refuse(path, f'вариант «{variant_id}» отклонён: выбранным быть не может', 'Верните статус варианта или выберите другой.')
    changed = main_variant(holder) is not v
    holder['chosen'] = v.get('id')
    holder['selection'] = {'method': method, 'by': by, 'at': at or today_iso(),
                           'compared': [x.get('id') for x in variants_of(holder) if x.get('status') != 'rejected']}
    if changed:
        rep.notes.append('выбор сменил текст слота: записи lint и claims недействительны — copydeck.py check --update OUT --promote')
        if (page.get('status') or 'draft') in ('checked', 'approved'):
            rep.notes.append(f"страница {page_id}: {page.get('status')} → draft")
            page['status'] = 'draft'
            page.pop('approval', None)
    return out, rep, {'path': path, 'variant': str(v.get('id')), 'changed': changed}


HEAD_SELECTED = ('copy deck — выбор варианта записан в selection слота (copydeck.py select, apply-selection);',
                 'сменился выбранный текст — записи lint и claims обновляет copydeck.py check --update')


def cmd_select(a):
    data = open_deck(a.deck)
    day = today_iso(a.at) if a.at else today_iso()
    out, rep, summ = select_variant(data, a.page, a.slot, a.variant, a.method, a.by, day)
    if out is None:
        print(render_text(rep, f'copydeck select · {a.deck}: отказ', True))
        return 1
    warn = dump_deck(out, a.output, HEAD_SELECTED, src_path=a.deck, date=day)
    print(a.output)
    print(f"  {summ['path']} → вариант {summ['variant']}" + ('' if summ['changed'] else ' (текст слота тот же)'))
    if warn:
        print(f'  WARNING {warn}')
    for n in rep.notes:
        print('  ' + n)
    return 0


# ============================================================================================ before-after.tsv: why из rule_ref
def _section_title(path, sec):
    """Заголовок раздела «§N» md-файла базы text: «## N. …» или «### N.M. …» → текст заголовка; None — нет."""
    if not os.path.exists(path):
        return None
    rx = re.compile(r'^#{2,4}\s+' + re.escape(sec) + r'\.?\s+(.+?)\s*$')
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = rx.match(line.rstrip())
            if m:
                return m.group(1).strip()
    return None


def before_after_fill(path=BEFORE_AFTER_PATH, root=ROOT):
    """Пустой why строк before-after.tsv — из rule_ref: «норма: <заголовок раздела> (<rule_ref>)». → (строки файла,
    [(номер строки, why)], [(номер строки, rule_ref) — раздел не найден]). Остальные колонки и байты строк не меняются."""
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    head = lines[0].split('\t')
    iw, ir = head.index('why'), head.index('rule_ref')
    filled, miss = [], []
    for i, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        cells = line.split('\t')
        if len(cells) <= max(iw, ir) or cells[iw].strip():
            continue
        m = re.match(r'^([\w./-]+\.md)\s*§\s*([\d.]+)', cells[ir].strip())
        title = _section_title(os.path.join(root, m.group(1)), m.group(2).rstrip('.')) if m else None
        if not title:
            miss.append((i, cells[ir]))
            continue
        cells[iw] = f'норма: {title} ({cells[ir].strip()})'
        lines[i - 1] = '\t'.join(cells)
        filled.append((i, cells[iw]))
    return lines, filled, miss


def cmd_before_after(a):
    lines, filled, miss = before_after_fill()
    if a.write and filled:
        with open(BEFORE_AFTER_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    for i, why in filled[:(None if a.verbose else 5)]:
        print(f'  строка {i}: {why}')
    print(f"before-after.tsv: пустой why из rule_ref — {'заполнено' if a.write else 'к заполнению'} {len(filled)}; раздел не найден — {len(miss)}")
    for i, ref in miss[:10]:
        print(f'  строка {i}: раздел не найден: {ref}')
    if a.check:
        return 1 if filled else 0
    return 0


# ============================================================================================ CLI
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--selftest' in argv:
        return selftest()
    if '--version' in argv:
        print(f'copydeck.py {VERSION} ({DATE})')
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)

    def common(p, facts=True):
        p.add_argument('deck')
        if facts:
            p.add_argument('--facts', help='facts.yaml (по умолчанию — facts_ref copy deck от его папки)')
        p.add_argument('--today', help='дата сверки ГГГГ-ММ-ДД (по умолчанию — сегодня)')
        p.add_argument('--json')
        p.add_argument('--md')
        p.add_argument('--quiet', action='store_true')
        p.add_argument('--verbose', action='store_true', help='показать и info')
    p = sp.add_parser('skeleton', help='каркас copy deck из плана страницы (page-plan)')
    p.add_argument('plan', help='план страницы site/<surface>/plans/<page-id>.yaml')
    p.add_argument('-o', '--output', required=True, help='copy deck (site/<surface>/copy/<page-id>.yaml)')
    p.add_argument('--facts-ref', help='путь к facts.yaml от папки copy deck (по умолчанию — refs.facts плана)')
    p.add_argument('--voice-ref', help='путь к voice.yaml от папки copy deck')
    p.add_argument('--date')
    p.add_argument('--force', action='store_true', help='заменить существующий файл каркасом')
    p = sp.add_parser('validate', help='формат, ссылки, статусы, словарь site, блоки, стык с планом, факты, правила текста')
    common(p)
    p.add_argument('--plan', help='план страницы для сверки стыка (по умолчанию — page_plan_ref)')
    p.add_argument('--final', action='store_true', help='перед публикацией: страница approved, 0 [PLACEHOLDER], 0 демо-фактов, мета заполнена')
    p.add_argument('--no-jsonschema', action='store_true', help='встроенная проверка схемы даже при установленном jsonschema')
    p = sp.add_parser('claims', help='claims_check.py (факты и право) по copy deck')
    common(p)
    p.add_argument('--strict', action='store_true', help='claims_check --strict: утверждения без чисел и маркеров (шумно)')
    p.add_argument('--all-variants', action='store_true')
    p.add_argument('--final', action='store_true', help='ворота публикации: демо-данные — error')
    p = sp.add_parser('lint', help='copy_lint.py (lint_text) по слотам и страницам')
    common(p, facts=False)
    p.add_argument('--final', action='store_true', help='[PLACEHOLDER] — error')
    p.add_argument('--all-variants', action='store_true')
    p.add_argument('--no-page-pass', action='store_true')
    p = sp.add_parser('check', help='claims → lint → validate')
    common(p)
    p.add_argument('--plan', help='план страницы для сверки стыка (по умолчанию — page_plan_ref)')
    p.add_argument('--final', action='store_true')
    p.add_argument('--strict', action='store_true')
    p.add_argument('--no-jsonschema', action='store_true')
    p.add_argument('--no-page-pass', action='store_true')
    p.add_argument('--update', help='записать копию deck с записями lint и claims (text_hash, дата, версия)')
    p.add_argument('--promote', action='store_true', help='с --update: draft и assumed → checked у текстов без error проверки; страница — checked, когда проверены все её тексты')
    p.add_argument('--all-variants', action='store_true', help='проверить и живые невыбранные варианты (и альтернативы мета) — каждый как если бы его выбрали; только отчёт: записи --update — у выбранных текстов')
    p = sp.add_parser('export', help='выгрузка во вход холста: pages/<page-id>/copy.md и facts.md')
    common(p)
    p.add_argument('--page', help='id страницы (у copy deck с одной страницей — необязательно)')
    p.add_argument('--stage', required=True, choices=['directions', 'mockup'], help='этап холста: статусы текстов — x-canvas-map copy_md')
    p.add_argument('--out', help='папка входа (по умолчанию — $DDD_HOME/out/text/export)')
    p.add_argument('--facts-scope', choices=['all', 'used'], default='all', help='all — все публикуемые факты; used — только из текстов страницы')
    p = sp.add_parser('import-copy', help='правки текста с холста: copy.md → варианты source: customer')
    p.add_argument('input', help='copy.md (разбор исходников холста или правленая выгрузка)')
    p.add_argument('--deck', required=True)
    p.add_argument('--page', required=True)
    p.add_argument('-o', '--output', required=True)
    p.add_argument('--choose', action='store_true', help='сразу выбрать варианты заказчика (страница возвращается в draft)')
    p.add_argument('--date')
    p.add_argument('--verbose', action='store_true')
    p = sp.add_parser('export-assets', help='alt, подписи, строки в картинках, OG → фрагмент плана ассетов ai-media')
    p.add_argument('deck')
    p.add_argument('--page')
    p.add_argument('-o', '--output')
    p = sp.add_parser('export-variants', help='лист слепого выбора вариантов (метки A, B, C; модели скрыты) и ключ меток')
    p.add_argument('deck')
    p.add_argument('--page')
    p.add_argument('--min', type=int, default=2, help='слоты с не меньшим числом живых вариантов')
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('-o', '--output', required=True, help='Markdown для выбирающего')
    p.add_argument('--key', required=True, help='YAML ключа меток (у ведущего)')
    p.add_argument('--include-failed', action='store_true', help='показать и варианты с error в variant.checks (по умолчанию — только прошедшие ворота)')
    p = sp.add_parser('apply-selection', help='голоса слепого выбора → chosen и selection')
    p.add_argument('deck')
    p.add_argument('--key', required=True, help='ключ меток export-variants')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--votes', help='YAML: {путь: метка | [метки по убыванию] | {метка: голоса}}')
    g.add_argument('--sheet', help='лист export-variants с заполненными строками «Выбор: …»')
    p.add_argument('--method', default='customer', choices=list(SELECTION_METHODS))
    p.add_argument('--by', required=True, help='кто выбирал: роль или имя')
    p.add_argument('--at', help='дата ГГГГ-ММ-ДД (по умолчанию сегодня)')
    p.add_argument('-o', '--output', required=True)
    p = sp.add_parser('select', help='открытый выбор варианта человеком → chosen и selection')
    p.add_argument('deck')
    p.add_argument('--page', required=True)
    p.add_argument('--slot', required=True, help='<section_id>/<slot_id>; id слота, если он один на странице; promise — обещание со своими вариантами')
    p.add_argument('--variant', required=True, help='id варианта')
    p.add_argument('--method', default='customer', choices=list(SELECTION_METHODS))
    p.add_argument('--by', required=True, help='кто выбрал: роль или имя (не агент)')
    p.add_argument('--at', help='дата ГГГГ-ММ-ДД (по умолчанию сегодня)')
    p.add_argument('-o', '--output', required=True)
    p = sp.add_parser('approve', help='утверждение страницы человеком: checked → approved; журнал процесса уходит')
    p.add_argument('deck')
    p.add_argument('--page', required=True)
    p.add_argument('--by', required=True, help='кто утверждает: роль или имя (не агент)')
    p.add_argument('--at', help='дата ГГГГ-ММ-ДД (по умолчанию сегодня)')
    p.add_argument('--note')
    p.add_argument('-o', '--output', required=True)
    p = sp.add_parser('before-after', help='пустой why в before-after.tsv — из rule_ref')
    p.add_argument('--write', action='store_true', help='записать заполненный why в файл базы')
    p.add_argument('--check', action='store_true', help='код 1, если есть пустой why, который заполняется из rule_ref')
    p.add_argument('--verbose', action='store_true')
    a = ap.parse_args(argv)
    try:
        return {'skeleton': cmd_skeleton, 'validate': cmd_validate, 'claims': cmd_claims, 'lint': cmd_lint, 'check': cmd_check,
                'export': cmd_export, 'import-copy': cmd_import_copy, 'export-assets': cmd_export_assets,
                'export-variants': cmd_export_variants, 'apply-selection': cmd_apply_selection, 'select': cmd_select,
                'approve': cmd_approve, 'before-after': cmd_before_after}[a.cmd](a)
    except SystemExit as e:
        if isinstance(e.code, str):                 # текст вместо кода — ошибка вызова, входа или окружения
            print(e.code, file=sys.stderr)
            return 2
        raise



# ============================================================================================ selftest
def _st_deck(**over):
    """Маленький copy deck v1 для тестов."""
    d = {'copy_deck': {
        'version': 1, 'date': '2026-09-24', 'site': 'demo-site', 'product_name': 'Демо', 'lang': 'ru',
        'voice_ref': 'черновик: на «вы», спокойно', 'facts_ref': 'facts.yaml',
        'pages': [{
            'page_id': 'home', 'page_type': 'landing-lead-services', 'status': 'draft',
            'promise': {'variants': [{'id': 'a', 'text': 'Ремонт без выездов на объект: срок и смета в договоре', 'status': 'draft'}], 'chosen': 'a'},
            'meta': {'title': 'Ремонт квартир под ключ — Демо', 'description': 'Срок и смета в договоре, гарантия 3 года на работы.',
                     'og_title': 'Ремонт под ключ', 'og_description': 'Срок и смета в договоре.'},
            'sections': [
                {'section_id': 'hero', 'section_role': 'hero', 'block': 'hero-media', 'message': 'Срок и смета — в договоре',
                 'slots': [
                     {'slot_id': 'h1', 'slot_type': 'headline', 'variants': [{'id': 'a', 'text': 'Ремонт квартир под ключ', 'status': 'draft'}], 'chosen': 'a', 'fact_ids': [], 'claim_flags': []},
                     {'slot_id': 'lead', 'slot_type': 'subheadline', 'variants': [{'id': 'a', 'text': 'Гарантия 3 года на работы — пункт 7.2 договора.', 'status': 'draft'}], 'chosen': 'a', 'fact_ids': ['guarantee-3'], 'claim_flags': ['guarantee']},
                     {'slot_id': 'cta', 'slot_type': 'cta-label', 'variants': [{'id': 'a', 'text': 'Вызвать замерщика', 'status': 'draft'}], 'chosen': 'a', 'fact_ids': [], 'claim_flags': []},
                     {'slot_id': 'alt-hero', 'slot_type': 'image-alt', 'asset_ref': 'hero', 'variants': [{'id': 'a', 'text': 'Прораб с рулеткой в пустой комнате', 'status': 'draft'}], 'chosen': 'a'},
                 ]},
                {'section_id': 'faq', 'section_role': 'faq', 'message': 'Ответы до звонка',
                 'slots': [
                     {'slot_id': 'q1', 'slot_type': 'faq-q', 'group': 'q1', 'variants': [{'id': 'a', 'text': 'Сколько стоит замер?', 'status': 'draft'}], 'chosen': 'a'},
                     {'slot_id': 'a1', 'slot_type': 'faq-a', 'group': 'q1', 'variants': [{'id': 'a', 'text': '[PLACEHOLDER: цена замера]', 'status': 'draft'}], 'chosen': 'a', 'missing_ids': ['measure-price']},
                 ]},
            ]}]}}
    d['copy_deck'].update(over)
    return d


def _st_facts():
    return {'facts_version': 1, 'date': '2026-09-24', 'site': 'demo-site', 'lang': 'ru', 'jurisdiction': 'ru',
            'facts': [
                {'id': 'guarantee-3', 'aliases': ['F1'], 'kind': 'guarantee', 'claim_class': ['guarantee'],
                 'verbatim': ['Гарантия 3 года на работы — пункт 7.2 договора'], 'canonical': 'Гарантия 3 года на работы по договору (п. 7.2).',
                 'values': [{'value': 3, 'unit': 'years', 'what': 'гарантийный срок'}],
                 'source': {'type': 'contract', 'who': 'заказчик', 'where': 'договор, п. 7.2', 'date': '2026-01-15', 'document': 'dogovor.pdf',
                            'quote': 'Гарантийный срок на выполненные работы составляет 3 (три) года', 'derivation': 'direct'},
                 'verification': {'status': 'verified'}, 'permission': {'status': 'not-required'},
                 'use': {'section_roles': ['hero', 'guarantee']}, 'legal': {'review': {'status': 'not-needed'}}, 'lang': 'ru'},
                {'id': 'promo-old', 'kind': 'promo', 'claim_class': ['price-discount', 'promo-deadline'], 'verbatim': ['Скидка 10 % до 31 августа'],
                 'canonical': 'Скидка 10 % до 31 августа 2026 года.', 'values': [{'value': 10, 'unit': '%', 'what': 'скидка'}],
                 'source': {'type': 'customer-document', 'who': 'заказчик', 'date': '2026-08-01', 'document': 'prikaz.pdf', 'quote': 'скидка 10% до 31.08.2026'},
                 'verification': {'status': 'verified'}, 'permission': {'status': 'not-required'}, 'valid': {'until': '2026-08-31'}, 'lang': 'ru'},
                {'id': 'city-inferred', 'kind': 'company', 'claim_class': ['origin'], 'verbatim': ['Сборка в Казани'], 'canonical': 'Сборка в Казани.',
                 'source': {'type': 'customer-message', 'who': 'заказчик', 'date': '2026-09-24', 'quote': 'мы стартап из Казани', 'derivation': 'inferred'},
                 'verification': {'status': 'stated'}, 'permission': {'status': 'not-required'}, 'lang': 'ru'},
                {'id': 'rating-demo', 'kind': 'rating', 'claim_class': ['rating'], 'verbatim': ['4,9 из 5 на Яндекс Картах — 120 оценок'],
                 'canonical': 'Рейтинг 4,9 из 5 по 120 оценкам.', 'values': [{'value': 4.9, 'unit': 'stars', 'scale': 5, 'count': 120, 'as_of': '2026-09-01'}],
                 'source': {'type': 'platform', 'who': 'Яндекс Карты', 'date': '2026-09-01', 'url': 'https://example.org'}, 'verification': {'status': 'verified'},
                 'permission': {'status': 'not-required'}, 'valid': {'until': '2026-12-01'}, 'lang': 'ru', 'example': True},
            ],
            'missing': [{'id': 'measure-price', 'what': 'цена замера', 'placeholder': '[PLACEHOLDER: цена замера]', 'who': 'заказчик'}],
            'never_claim': [{'id': 'nc-eyes', 'text': 'любые обещания про здоровье и зрение', 'claim_class': ['health'],
                             'patterns': ['глаз', 'зрени'], 'lift': 'never', 'voice': 'any'}]}


def _st_checked(slot, text, status='checked'):
    """Слот с записями проверок текущего текста (0 error) и статусом выбранного варианта."""
    h = text_hash(text)
    v = chosen_variant(slot)
    v['text'], v['status'] = text, status
    slot['lint'] = {'profile': 'landing', 'errors': 0, 'warnings': 0, 'text_hash': h}
    slot['claims'] = {'errors': 0, 'warnings': 0, 'text_hash': h}
    slot.setdefault('fact_ids', [])
    slot.setdefault('claim_flags', [])
    return slot


def selftest():
    import shutil
    ok, bad = [], []

    def check(name, cond, detail=''):
        (ok if cond else bad).append(name)
        if not cond:
            print(f'  FAIL {name}: {detail}')

    td = tempfile.mkdtemp(prefix='copydeck-selftest-')
    try:
        schema = load_copy_schema()
        check('schema: $id и дата', schema.get('$id') == 'urn:app-design:text:copy-deck:1' and re.fullmatch(r'\d{4}-\d{2}-\d{2}', schema.get('date') or ''))
        # --- поля v0 есть в схеме (не удалять и не переименовывать)
        defs = schema['$defs']
        owners = {'copy_deck': schema['properties'], 'page': defs['page']['properties'], 'meta': defs['meta']['properties'],
                  'section': defs['section']['properties'], 'slot': defs['slot']['properties'], 'variant': defs['variant']['properties'],
                  'lint': defs['lint-record']['properties']}
        miss = []
        for path in schema['x-v0-fields']['paths']:
            if path == 'copy_deck':
                continue
            owner, field = path.split('.', 1)
            props = defs['deck']['properties'] if owner == 'copy_deck' else owners[owner]
            if field not in props:
                miss.append(path)
        check('схема: все поля v0 на месте', not miss, miss)
        check('схема: статусы v0 на месте, assumed добавлен', set(schema['x-v0-fields']['status_values_v0']) <= set(defs['status']['enum']) and 'assumed' in defs['status']['enum'])
        check('схема: x-status-rules знают assumed (слот и страница)', 'assumed' in schema['x-status-rules']['slot'] and 'assumed' in schema['x-status-rules']['page'])
        with open(os.path.abspath(__file__), encoding='utf-8') as f:
            own_src = f.read()
        named = {rid for grp in ('slot', 'page') for st in schema['x-status-rules'][grp].values() for key in ('checks', 'signals') for rid in st.get(key) or {}}
        named |= set(schema['x-status-rules']['final']['checks'])
        check('схема: x-status-rules называют проверки id находок validate (каждый id есть в коде утилиты)',
              len(named) >= 10 and not [rid for rid in sorted(named) if f"'{rid}'" not in own_src], [rid for rid in sorted(named) if f"'{rid}'" not in own_src])
        check('схема: обход claims_allow — у слота, мета и страницы; запись называет снятое полями value и fragment',
              all('claims_allow' in defs[k]['properties'] for k in ('slot', 'meta', 'page'))
              and {'rule', 'reason', 'by', 'value', 'fragment'} <= set(defs['claims-allow']['items']['properties']))
        cmr = copy_md_rules(schema)
        check('схема: x-canvas-map copy_md — статусы этапов (направления и подача — assumed и checked, макет — approved)',
              set(cmr['stage_statuses']) == {'directions', 'treatment', 'mockup'}
              and all({'assumed', 'checked'} <= set(cmr['stage_statuses'][s]) for s in ('directions', 'treatment'))
              and cmr['stage_statuses']['mockup'] == ['approved'], cmr)
        check('схема: прежней карты проекции нет', not any(k.startswith('x-k' + 'imi') for k in schema), [k for k in schema if k.startswith('x-')])
        # --- схема: пример и отрицательные случаи; паритет с jsonschema
        sv = SubsetValidator(schema)
        check('схема: пример проходит (встроенная)', not sv.errors(schema['examples'][0]), sv.errors(schema['examples'][0])[:3])
        negs = {}
        d = _st_deck(); del d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['slot_type']; negs['нет slot_type (поле v0)'] = d
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['stauts'] = 'draft'; negs['опечатка в ключе'] = d
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['status'] = 'done'; negs['неизвестный статус'] = d
        d = _st_deck(version=2); negs['version 2'] = d
        d = _st_deck(); d['copy_deck']['pages'][0]['promise'] = {'notes': 'x'}; negs['promise без variants и from'] = d
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['lint_allow'] = [{'rule': 'ru-lex-x'}]; negs['lint_allow без reason'] = d
        d = _st_deck(); d['copy_deck']['pages'][0]['cta_primary'] = 'Home Hero CTA'; negs['cta_primary не путь'] = d
        d = _st_deck(); del d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants']; negs['нет variants (поле v0)'] = d
        for name, dd in negs.items():
            check(f'схема ловит: {name}', bool(sv.errors(dd)), 'нет ошибки')
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['status'] = 'assumed'
        check('схема: статус assumed проходит', not sv.errors(d), sv.errors(d)[:2])
        try:
            from jsonschema import Draft202012Validator
            jv = Draft202012Validator(schema)
            par = [n for n, dd in negs.items() if bool(list(jv.iter_errors(dd))) != bool(sv.errors(dd))]
            par += [] if bool(list(jv.iter_errors(_st_deck()))) == bool(sv.errors(_st_deck())) else ['позитивный']
            check('схема: встроенная = jsonschema', not par, par)
        except ImportError:
            print('  (jsonschema нет — паритет не проверен; Python окружения скилла)')
        # --- validate: позитив и смысловые ошибки
        facts = Facts(_st_facts(), os.path.join(td, 'facts.yaml'))
        ctx = Ctx(os.path.join(td, 'deck.yaml'), facts, '2026-09-24', copy_slots_path=os.path.join(td, 'нет.yaml'),
                  meta_rules_path=os.path.join(td, 'нет-meta.yaml'))
        rep = validate(_st_deck(), ctx)
        errs = [f for f in rep.findings if f['level'] == 'error']
        check('validate: чистый deck — 0 error', not errs, [(f['rule'], f['where'], f['message']) for f in errs][:4])
        check('validate: файлы правил текста нет → warning, не падение', any(f['rule'] == 'COPY-D-RULES-MISSING' and 'copy-slots' in f['message'] for f in rep.findings))
        d = _st_deck(); d['copy_deck']['copy_slots_ref'] = '../../04-copy-by-block/copy-slots.yaml'
        r = validate(d, Ctx(os.path.join(td, 'deck.yaml'), facts, '2026-09-24', meta_rules_path=os.path.join(td, 'нет-meta.yaml')))
        check('validate: copy_slots_ref не разрешается → warning COPY-D-RULES-REF, правила — copy-slots.yaml базы',
              any(f['rule'] == 'COPY-D-RULES-REF' and f['level'] == 'warning' and 'copy_slots_ref не разрешается' in f['message'] for f in r.findings)
              and not any(f['rule'] == 'COPY-D-RULES-MISSING' and 'copy-slots' in f['message'] for f in r.findings)
              and r.tools.get('validate', {}).get('copy_slots') == os.path.relpath(COPY_SLOTS_PATH, ROOT))
        r = validate(d, ctx)
        check('validate: ссылка не разрешается и файла нет в базе → COPY-D-RULES-REF и «правила не загружены»',
              {'COPY-D-RULES-REF', 'COPY-D-RULES-MISSING'} <= {f['rule'] for f in r.findings})

        def rules_of(d, **kw):
            r = validate(d, kw.pop('ctx', ctx), **kw)
            return {(f['rule'], f['level']) for f in r.findings}, r
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['slot_id'] = 'h1'
        check('validate: повтор slot_id', ('COPY-D-ID-DUP', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['chosen'] = 'z'
        check('validate: chosen без варианта', ('COPY-D-CHOSEN', 'error') in rules_of(d)[0])
        d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]
        sl['variants'].append({'id': 'b', 'text': 'Ремонт с гарантией', 'status': 'rejected'}); sl['chosen'] = 'b'
        r0 = rules_of(d)[0]
        check('validate: выбран отклонённый', ('COPY-D-CHOSEN', 'error') in r0)
        check('validate: rejected без reason (v1)', ('COPY-D-REJECTED', 'error') in r0)
        # словарь site v1 (типы страниц, роли, слоты) и блоки blocks.yaml
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['slot_type'] = 'mega-title'
        check('словарь site: неизвестный slot_type → error', ('COPY-D-VOCAB', 'error') in rules_of(d)[0])
        media = next((k for k, kind in (ctx.vocab or {}).get('slot_kinds', {}).items() if kind == 'media'), None)
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['slot_type'] = media
        check('словарь site: слот не вида text → error', media and ('COPY-D-VOCAB', 'error') in rules_of(d)[0], media)
        d = _st_deck(); d['copy_deck']['pages'][0]['page_type'] = 'landing-unknown'
        check('словарь site: неизвестный page_type → error', ('COPY-D-VOCAB', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['page_type'] = 'ecommerce-product-page'
        check('словарь site: page_type out-of-scope → error', ('COPY-D-VOCAB', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['page_type'] = 'faq-page'; d['copy_deck']['pages'][0]['sections'][0]['section_role'] = 'offer'
        d['copy_deck']['pages'][0]['sections'][1]['slots'][1]['slot_type'] = 'disclaimer'
        check('словарь site: faq-page, роль offer, слот disclaimer — законные id v1', not any(f['rule'] == 'COPY-D-VOCAB' and f['level'] == 'error' for f in rules_of(d)[1].findings),
              [(f['rule'], f['message']) for f in rules_of(d)[1].findings if f['rule'] == 'COPY-D-VOCAB'])
        d = _st_deck(); d['copy_deck']['pages'][0]['page_type'] = 'integrations-page'
        check('словарь site: proposed → info', ('COPY-D-VOCAB', 'info') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['block'] = 'hero'
        check('block: роль вместо блока → error COPY-D-BLOCK', ('COPY-D-BLOCK', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['block'] = ''
        check('block: пустое поле → warning', ('COPY-D-BLOCK', 'warning') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][1]['block'] = 'faq'
        check('block: id блока blocks.yaml — без находки', not any(f['rule'] == 'COPY-D-BLOCK' for f in rules_of(d)[1].findings))
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = ['guarantee-33']
        check('validate: нет факта', ('COPY-D-FACT-REF', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = ['missing:measure-price']
        check('validate: пробел в fact_ids', ('COPY-D-FACT-REF', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = ['fact:F1']
        check('validate: алиас и префикс fact: принимаются', not any(f['rule'] == 'COPY-D-FACT-REF' for f in rules_of(d)[1].findings))
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = ['promo-old']
        check('validate: истёкший факт', ('COPY-D-FACT-EXPIRED', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = ['city-inferred']
        check('validate: вывод вместо факта (draft → warning)', ('COPY-D-FACT-UNPUBLISHABLE', 'warning') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][1]['slots'][1]['missing_ids'] = ['measure-cost']
        check('validate: неизвестный missing_ids', ('COPY-D-MISSING-REF', 'error') in rules_of(d)[0])
        # демо-данные: --final — error, без него — info
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = ['rating-demo']
        check('демо-факт example: true — без --final info', ('COPY-D-EXAMPLE', 'info') in rules_of(d)[0])
        check('демо-факт example: true — --final error', ('COPY-D-EXAMPLE', 'error') in rules_of(d, final=True)[0])
        fx_demo = dict(_st_facts(), example=True)
        ctx_demo = Ctx(os.path.join(td, 'deck.yaml'), Facts(fx_demo, os.path.join(td, 'f.yaml')), '2026-09-24', copy_slots_path=os.path.join(td, 'нет.yaml'), meta_rules_path=os.path.join(td, 'нет-meta.yaml'))
        check('демо-файл фактов (example у файла) — --final error на любом факте', ('COPY-D-EXAMPLE', 'error') in rules_of(_st_deck(), ctx=ctx_demo, final=True)[0])
        # статусы
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['status'] = 'assumed'
        check('статус assumed: без записей проверок — не ошибка (как draft)', not any(f['rule'] == 'COPY-D-STATUS' for f in rules_of(d)[1].findings))
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['status'] = 'checked'
        check('validate: checked без записей lint и claims', ('COPY-D-STATUS', 'error') in rules_of(d)[0])
        h = text_hash('Ремонт квартир под ключ')
        d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]; sl['variants'][0]['status'] = 'checked'
        sl['lint'] = {'profile': 'landing', 'errors': 0, 'warnings': 0, 'text_hash': h}; sl['claims'] = {'errors': 0, 'warnings': 0, 'text_hash': h}
        r0 = rules_of(d)[0]
        check('validate: checked с записями — без ошибок статуса', not any(r in (('COPY-D-STATUS', 'error'), ('COPY-D-HASH', 'error')) for r in r0), r0)
        sl['variants'][0]['text'] = 'Ремонт квартир под ключ за 60 дней'
        check('validate: текст изменён после проверки (text_hash)', ('COPY-D-HASH', 'error') in rules_of(d)[0])
        d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]; sl['variants'][0]['status'] = 'approved'
        sl['lint'] = {'profile': 'landing', 'errors': 0, 'warnings': 0, 'text_hash': h}; sl['claims'] = {'errors': 0, 'warnings': 0, 'text_hash': h}
        check('validate: approved без review и approval', ('COPY-D-STATUS', 'error') in rules_of(d)[0])
        sl['variants'][0]['review'] = {'by': 'заказчик', 'at': '2026-09-24'}
        check('validate: approved с review', ('COPY-D-STATUS', 'error') not in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['status'] = 'approved'; d['copy_deck']['pages'][0]['approval'] = {'by': 'заказчик', 'at': '2026-09-24'}
        check('validate: страница approved со слотами draft', ('COPY-D-STATUS', 'error') in rules_of(d)[0])
        check('validate: --final ловит [PLACEHOLDER]', ('COPY-D-PLACEHOLDER', 'error') in rules_of(_st_deck(), final=True)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['text'] = 'Ремонт [ЗАГЛУШКА] под ключ'
        check('validate: заглушка не по формату', ('COPY-D-PLACEHOLDER-FORM', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['text'] = 'Ремонт {{product.name}}'
        check('validate: «{{» в тексте — остаток шаблона для проверки входа холста', ('COPY-D-TEMPLATE-TOKEN', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0].pop('promise')
        check('validate: нет обещания → warning', ('COPY-D-PROMISE', 'warning') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['promise'] = {'from': 'home/hero/leadd'}
        check('validate: promise.from не найден', ('COPY-D-PROMISE', 'error') in rules_of(d)[0])
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'].append(
            {'slot_id': 'img-t', 'slot_type': 'in-image-text', 'asset_ref': 'hero', 'variants': [{'id': 'a', 'text': 'Ремонт квартир под ключ за шестьдесят рабочих дней', 'status': 'draft'}], 'chosen': 'a'})
        r0 = rules_of(d)[0]
        check('validate: строка в картинке > 40 знаков', ('COPY-D-IN-IMAGE', 'error') in r0)
        check('validate: строка в картинке > 4 слов', ('COPY-D-IN-IMAGE', 'warning') in r0)
        d = _st_deck(lang='en', source_lang='ru')
        check('validate: адаптация без source_ref', ('COPY-D-LANG', 'warning') in rules_of(d)[0])
        check('validate: кириллица в EN-тексте', any(f['rule'] == 'COPY-D-LANG' and 'кириллица' in f['message'] for f in rules_of(d)[1].findings))
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['claim_flags'] = ['guarantee', 'weird-flag']
        check('validate: неизвестный claim_flags', ('COPY-D-FLAGS', 'warning') in rules_of(d)[0])
        # --- правила текста: copy-slots.yaml (E) в двух формах, голос (F), мета (G); ядро первого экрана без hero
        cs1 = os.path.join(td, 'cs1.yaml')
        with open(cs1, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'slot_types': [{'id': 'headline', 'length': {'ru': {'words': {'min': 2, 'target': 6, 'max': 3}, 'chars': {'max': 20},
                                                                               'hard_words': [1, 3], 'primary': 'chars'}}},
                                           {'id': 'subheadline', 'fact_required': 'always', 'length': {'ru': {'desktop': {'words': [5, 12, 25]}, 'mobile': {'words': [5, 10, 20]}}}}],
                            'renames': {'cta-label': 'cta-button'}, 'composites': {'hero-core': {'max_words': 6, 'rule': 'тест'}}}, f, allow_unicode=True)
        specs, ren, notes = load_copy_slots(cs1)
        check('copy-slots: список и длины (форма 1)', specs['headline']['len'][('ru', 'words')] == [2, 3] and specs['subheadline']['len'][('ru', 'words')] == [5, 25], specs)
        cs2 = os.path.join(td, 'cs2.yaml')
        with open(cs2, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'slots': {'headline': {'lengths': {'en': {'max_words': 8, 'max_chars': 50}}}}}, f)
        specs2, _r, _n = load_copy_slots(cs2)
        check('copy-slots: словарь и плоские ключи (форма 2)', specs2['headline']['len'][('en', 'words')] == [None, 8])
        ctx2 = Ctx(os.path.join(td, 'deck.yaml'), facts, '2026-09-24', copy_slots_path=cs1, meta_rules_path=os.path.join(td, 'нет-meta.yaml'))
        d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = []
        rr = validate(d, ctx2).findings
        r0 = {(f['rule'], f['level']) for f in rr}
        check('copy-slots: за грубой границей → warning', ('COPY-D-LEN', 'warning') in r0)
        check('copy-slots: основная единица > p90 → info', ('COPY-D-LEN', 'info') in r0)
        check('copy-slots: fact_required always', ('COPY-D-FACT-REQUIRED', 'warning') in r0)
        check('copy-slots: переименованный тип', ('COPY-D-SLOT-RENAMED', 'warning') in r0)
        check('ядро первого экрана: секция hero > max_words → COPY-D-HERO-CORE', any(f['rule'] == 'COPY-D-HERO-CORE' and f['where'] == 'home/hero' for f in rr))
        # заголовок — имя сущности фактов: нижняя граница длины к нему не применяется, верхняя остаётся
        f_names = Facts(dict(_st_facts(), entities=[{'id': 'lamp', 'type': 'product', 'names': ['Кварц', 'Кварц Про Макс Плюс']}]),
                        os.path.join(td, 'facts.yaml'))
        cs3 = os.path.join(td, 'cs3.yaml')
        with open(cs3, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'slots': {'headline': {'lengths': {'min_words': 2, 'max_words': 3}}}}, f)   # границы без языка
        no_meta = os.path.join(td, 'нет-meta.yaml')
        ctx_b, ctx_nb = (Ctx(os.path.join(td, 'deck.yaml'), x, '2026-09-24', meta_rules_path=no_meta) for x in (facts, f_names))   # нормы базы
        ctx_3, ctx_n3 = (Ctx(os.path.join(td, 'deck.yaml'), x, '2026-09-24', copy_slots_path=cs3, meta_rules_path=no_meta) for x in (facts, f_names))

        def h1_len(text, c, side):
            """Находки COPY-D-LEN заголовка первого экрана с текстом text: side — «<» (короче нормы) или «>» (длиннее)."""
            d_ = _st_deck(); d_['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['text'] = text
            return [f['message'] for f in validate(d_, c).findings
                    if f['rule'] == 'COPY-D-LEN' and f['where'] == 'home/hero/h1' and f' {side} ' in f['message']]
        check('COPY-D-LEN: заголовок, равный имени сущности фактов (без регистра), короче нормы — не находка; без сущностей — находка',
              not h1_len('Кварц', ctx_nb, '<') and not h1_len('КВАРЦ', ctx_nb, '<') and h1_len('Кварц', ctx_b, '<')
              and not h1_len('Кварц', ctx_n3, '<') and h1_len('Кварц', ctx_3, '<'),
              (h1_len('Кварц', ctx_nb, '<'), h1_len('Кварц', ctx_b, '<'), h1_len('Кварц', ctx_n3, '<'), h1_len('Кварц', ctx_3, '<')))
        check('COPY-D-LEN: короткий заголовок не из имён сущностей — находка, с сущностями в фактах и без них',
              h1_len('Лампа', ctx_nb, '<') == h1_len('Лампа', ctx_b, '<') != [] and h1_len('Лампа', ctx_n3, '<') == h1_len('Лампа', ctx_3, '<') != [],
              (h1_len('Лампа', ctx_nb, '<'), h1_len('Лампа', ctx_n3, '<')))
        check('COPY-D-LEN: верхняя граница длины у заголовка-имени остаётся', bool(h1_len('Кварц Про Макс Плюс', ctx_n3, '>')),
              h1_len('Кварц Про Макс Плюс', ctx_n3, '>'))
        d = _st_deck(); pg = d['copy_deck']['pages'][0]; pg['page_type'] = 'case-page'
        hero = pg['sections'][0]; hero['section_id'], hero['section_role'], hero['block'] = 'case', 'case-studies', 'case-study'
        pg['sections'].insert(0, {'section_id': 'header', 'section_role': 'header', 'block': 'header', 'slots': [
            {'slot_id': 'cta-label', 'slot_type': 'cta-label', 'variants': [{'id': 'a', 'text': 'Позвонить нам сегодня же, прямо сейчас', 'status': 'draft'}], 'chosen': 'a'}]})
        pg['promise'] = {'from': 'home/case/lead'}
        rr = validate(d, ctx2).findings
        check('ядро первого экрана без hero — по первой секции после шапки', any(f['rule'] == 'COPY-D-HERO-CORE' and f['where'] == 'home/case' for f in rr)
              and not any(f['rule'] == 'COPY-D-HERO-CORE' and f['where'] == 'home/header' for f in rr), [(f['rule'], f['where']) for f in rr if f['rule'] == 'COPY-D-HERO-CORE'])
        # роли секций в правилах слотов базы покрывают примеры copy deck базы
        ex_dir, ex_roles, n_ex = os.path.join(ROOT, '10-templates-recipes', 'examples'), [], 0
        ctx_ex = Ctx(None, None, '2026-09-24')
        for name in sorted(os.listdir(ex_dir)) if os.path.isdir(ex_dir) else []:
            if name.endswith('.yaml'):
                ctx_ex.deck_path = os.path.join(ex_dir, name)
                n_ex += 1
                ex_roles += [(name, f['where'], f['message']) for f in validate(open_deck(ctx_ex.deck_path), ctx_ex).findings if f['rule'] == 'COPY-D-SLOT-ROLE']
        check('copy-slots.yaml: роли секций слотов покрывают примеры copy deck базы — COPY-D-SLOT-ROLE нет', n_ex and not ex_roles, (n_ex, ex_roles[:5]))
        d = _st_deck(projection='meaning')
        check('схема: пометка проекции смысла (projection: meaning) проходит', not SubsetValidator(schema).errors(d), SubsetValidator(schema).errors(d)[:2])
        vy = os.path.join(td, 'voice.yaml')
        with open(vy, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'voice_version': 1, 'address': {'ru_form': 'vy', 'capital_vy': False, 'self_reference': 'we'},
                            'vocabulary': {'avoid': [{'term': 'уникальн*', 'reason': 'пустой эпитет', 'use_instead': 'факт отличия'},
                                                     {'term': 'решения под ключ', 'reason': 'штамп', 'level': 'info'}]},
                            'projections': {'tone_of_voice': 'на «вы», спокойно и по делу, без восклицаний'}}, f, allow_unicode=True)
        vo = load_voice(vy)
        check('голос: обращение, avoid, tone_of_voice', vo['format'] == 'F' and vo['address'] == 'вы' and vo['taboo'][0]['term'] == 'уникальн*' and vo['tone_of_voice'], vo)
        vg = os.path.join(td, 'voice-generic.yaml')
        with open(vg, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'обращение': 'на «ты»', 'lexicon': {'dont_say': ['уникальный']}}, f, allow_unicode=True)
        check('голос: терпимый разбор чужой формы', load_voice(vg)['address'] == 'ты' and load_voice(vg)['format'] == 'generic')
        check('words_rx: «*» и ё/е', bool(words_rx('уникальн*').search('уникальное')) and bool(words_rx('ещё').search('еще')))
        d = _st_deck(voice_ref='voice.yaml'); d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'][0]['text'] = 'Уникальный ремонт для тебя'
        r0 = [f for f in validate(d, ctx2).findings if f['rule'] == 'COPY-D-VOICE']
        check('голос: табу и «ты» при «вы»', len(r0) >= 2, r0)
        mg = os.path.join(td, 'meta-rules.yaml')
        with open(mg, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'limits': {'meta-title': {'ru': {'write': [40, 70], 'info_over': 80, 'warning_over': 110, 'words_min': 3}},
                                       'meta-description': {'ru': {'write': [110, 180], 'warning_under': 60}}},
                            'checks_outside_linter': [{'id': 'meta-x-duplicate-title', 'level': 'error'}, {'id': 'meta-x-missing', 'level': 'error'},
                                                      {'id': 'meta-x-desc-equals-title', 'level': 'warning'}]}, f, allow_unicode=True)
        ctx3 = Ctx(os.path.join(td, 'deck.yaml'), facts, '2026-09-24', copy_slots_path=cs1, meta_rules_path=mg)
        check('мета: формат распознан', ctx3.meta_rules['format'] == 'G')
        d = _st_deck(); p2 = _copy.deepcopy(d['copy_deck']['pages'][0]); p2['page_id'] = 'home-2'; d['copy_deck']['pages'].append(p2)
        r0 = {(f['rule'], f['level']) for f in validate(d, ctx3).findings}
        check('мета: дубль title между страницами', ('meta-x-duplicate-title', 'error') in r0)
        check('мета: description короче warning_under', ('COPY-D-META-LEN', 'warning') in r0)
        d = _st_deck(); m = d['copy_deck']['pages'][0]['meta']
        m['variants'] = {'title': [{'id': 'a', 'text': m['title'], 'status': 'draft'}, {'id': 'b', 'text': 'Ремонт под ключ с гарантией 3 года', 'status': 'draft'},
                                   {'id': 'c', 'text': 'Ремонт без смет', 'status': 'rejected'}]}
        m['review_by'] = '2026-01-01'
        r0 = {(f['rule'], f['level']) for f in validate(d, ctx3).findings}
        check('мета: варианты title без плана теста → info', ('COPY-D-META-VARIANTS', 'info') in r0)
        check('мета: отклонённый вариант без reason', ('COPY-D-REJECTED', 'error') in r0)
        check('мета: review_by в прошлом → warning', ('COPY-D-META-REVIEW', 'warning') in r0)
        # --- OG-поля мета ждутся те, что заведены слотами плана; с checked, до утверждения
        og_of = lambda dd, cx: [f['message'] for f in validate(dd, cx).findings if f['rule'] == 'meta-x-og-missing']
        plan_og = {}
        for name, slots in (('no-og', ['meta-title', 'meta-description']), ('og-title', ['meta-title', 'meta-description', 'og-title'])):
            plan_og[name] = os.path.join(td, f'plan-{name}.yaml')
            with open(plan_og[name], 'w', encoding='utf-8') as f:
                yaml.safe_dump({'status': 'approved', 'page': {'id': 'home', 'page_type': 'landing-lead-services'}, 'sections': [],
                                'page_slots': {'text': [{'id': x, 'slot': x} for x in slots]}}, f, allow_unicode=True)
        cx_og = lambda plan=None: Ctx(os.path.join(td, 'deck.yaml'), facts, '2026-09-24', copy_slots_path=cs1, meta_rules_path=mg, plan_path=plan)
        d_og = _st_deck(); pg_og = d_og['copy_deck']['pages'][0]; pg_og['status'] = 'checked'; pg_og['meta'].update(og_title='', og_description='')
        check('мета: OG пусты, плана нет — meta-x-og-missing уже на checked (до утверждения), у черновика — нет',
              og_of(d_og, cx_og()) == ['нет og_title и og_description']
              and not og_of(dict(copy_deck=dict(d_og['copy_deck'], pages=[dict(pg_og, status='draft')])), cx_og()), og_of(d_og, cx_og()))
        check('мета: у страницы без OG-слотов в плане (служебная) OG не ждётся; есть слот og-title — ждётся только он',
              og_of(d_og, cx_og(plan_og['no-og'])) == [] and og_of(d_og, cx_og(plan_og['og-title'])) == ['нет og_title'],
              (og_of(d_og, cx_og(plan_og['no-og'])), og_of(d_og, cx_og(plan_og['og-title']))))
        flat, _mp, _alt = flatten_for_claims(deck_root(d), ctx3)
        tslot = next(x for x in flat['copy_deck']['pages'][0]['sections'][0]['slots'] if x['slot_id'] == 'title')
        check('мета: в основной сверке — выбранный title', len(tslot['variants']) == 1 and tslot['chosen'] == 'meta' and not _alt, tslot)
        flat, _mp, alt = flatten_for_claims(deck_root(d), ctx3, alternatives=True)
        check('мета: --all-variants — живая альтернатива title копией страницы, отклонённая и равная выбранному — нет',
              sorted(alt.values()) == [('home/meta/title', 'b')] and len(flat['copy_deck']['pages']) == 2, sorted(alt.values()))
        d = _st_deck(); d['copy_deck']['pages'][0]['article'] = {'intent': 'выбор подрядчика', 'author': 'fact:lapin-nope', 'unique_angle': {'text': 'график по неделям', 'fact_ids': ['guarantee-3']}}
        r0 = {(f['rule'], f['level'], f['where']) for f in validate(d, ctx3).findings}
        check('статья: автор — несуществующий факт', ('COPY-D-FACT-REF', 'error', 'home/article/author') in r0)
        if os.path.exists(META_RULES_PATH):
            check('мета: реальный meta-rules.yaml читается', load_meta_rules(META_RULES_PATH).get('format') in ('G', 'generic'))
        # --- плоская копия для claims_check
        flat, mp, _alt = flatten_for_claims(deck_root(_st_deck()), ctx)
        secs = {s['section_id'] for s in flat['copy_deck']['pages'][0]['sections']}
        check('claims: псевдосекции мета и обещания', {'__head', '__promise', 'hero'} <= secs, secs)
        check('claims: обратная карта путей', mp[('home', '__promise', 'promise')] == 'home/promise' and mp[('home', '__head', 'title')] == 'home/meta/title')
        # --- каркас из плана страницы и стык (пример site v1)
        plan_p = str(kbpaths.kb('site', '10-playbooks-contracts', 'examples', 'lead-services-otves', 'plans', 'home.yaml'))
        if os.path.exists(plan_p):
            plan = deep_dates(load_yaml_file(plan_p))
            sk_p = os.path.join(td, 'site', 'copy', 'home.yaml')
            os.makedirs(os.path.dirname(sk_p), exist_ok=True)
            sk, sk_notes = skeleton_from_plan(plan, plan_p, sk_p, date='2026-09-29')
            dump_deck(sk, sk_p, '# каркас\n')
            pg = deck_root(sk)['pages'][0]
            n_plan = sum(len(plan_text_slots(s)) for s in plan['sections'])
            check('каркас из плана: page_id, page_type, page_plan_ref, все текстовые слоты плана',
                  pg['page_id'] == plan['page']['id'] and pg['page_type'] == plan['page']['page_type'] and deck_root(sk).get('page_plan_ref')
                  and sum(len(slots_of(s)) for s in sections_of(pg)) == n_plan, (pg['page_id'], n_plan))
            hero_sl = next(sl for s in sections_of(pg) if s['section_id'] == 'hero' for sl in slots_of(s) if sl['slot_id'] == 'headline')
            check('каркас: поля стыка слота (slot_type, site_slot_id, варианты по плану)', hero_sl['slot_type'] == 'headline' and hero_sl['site_slot_id'] == 'headline' and len(hero_sl['variants']) == 2, hero_sl)
            check('каркас: fact_ids из binds, обещание и главная кнопка первого экрана',
                  any(sl.get('fact_ids') for s in sections_of(pg) for sl in slots_of(s)) and pg.get('promise', {}).get('from') == 'home/hero/subheadline' and pg.get('cta_primary') == 'home/hero/cta-label', (pg.get('promise'), pg.get('cta_primary')))
            fp_sk = rel_to(sk_p, deck_root(sk)['facts_ref'])
            ctx_sk = Ctx(sk_p, load_facts(fp_sk), '2026-09-29')
            r_sk = validate(sk, ctx_sk)
            check('каркас из плана → validate: 0 error, стык сверен', not r_sk.count('error') and (r_sk.tools.get('validate') or {}).get('plan_stitch', {}).get('slots') == n_plan,
                  [(f['rule'], f['where'], f['message'][:60]) for f in r_sk.findings if f['level'] == 'error'][:4])
            check('каркас: голос — voice_ref смысла (у примера смысл внутри брифа), режим права — legal_category брифа',
                  str(deck_root(sk).get('voice_ref') or '').startswith('черновик') and deck_root(sk).get('legal_category') == ['general']
                  and not any('voice_ref не найден' in n for n in sk_notes), (deck_root(sk).get('voice_ref'), deck_root(sk).get('legal_category')))
            sk_miss = {f"{s['section_id']}/{sl['slot_id']}": sl.get('missing_ids') for s in sections_of(pg) for sl in slots_of(s)}
            check('каркас: missing_ids — только пробел с заглушкой; пробел rewrite-without или omit-block — заметкой, не ссылкой слота',
                  sk_miss.get('pricing/disclaimer') == ['payment-stages'] and 'guarantee/text' in sk_miss and sk_miss['guarantee/text'] is None
                  and any('guarantee/text ← missing:estimate-change-policy (rewrite-without)' in n for n in sk_notes)
                  and not any(f['rule'] == 'COPY-D-MISSING-REF' and f['where'] == 'home/guarantee/text' for f in r_sk.findings),
                  (sk_miss.get('pricing/disclaimer'), sk_miss.get('guarantee/text'), sk_notes))
            import contextlib
            import io
            new_p = os.path.join(td, 'new-surface', 'copy', 'home.yaml')
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err_:
                rc_new = main(['skeleton', plan_p, '-o', new_p, '--date', '2026-09-29'])
                rc_none = main(['skeleton', os.path.join(td, 'нет-плана.yaml'), '-o', os.path.join(td, 'x', 'home.yaml')])
            check('skeleton: папки выхода ещё нет — создаётся, каркас записан; плана нет — код 1 и строка об ошибке входа',
                  rc_new == 0 and os.path.isfile(new_p) and rc_none == 2 and 'план не читается' in err_.getvalue() and not os.path.exists(os.path.join(td, 'x')),
                  (rc_new, rc_none, err_.getvalue()[:200]))
            p_nv = _copy.deepcopy(plan)
            p_nv['refs'] = {k: v for k, v in plan['refs'].items() if k not in ('brief', 'meaning')}
            sk_nv, notes_nv = skeleton_from_plan(p_nv, plan_p, sk_p, date='2026-09-29')
            r_nv = validate(sk_nv, ctx_sk)
            check('без voice_ref: каркас говорит заметкой, validate — warning COPY-D-VOICE (голос не проверяется), а не тишина',
                  'voice_ref' not in deck_root(sk_nv) and any('voice_ref не найден' in n for n in notes_nv)
                  and any(f['rule'] == 'COPY-D-VOICE' and f['level'] == 'warning' and 'нет voice_ref' in f['message'] for f in r_nv.findings)
                  and not any(f['rule'] == 'COPY-D-VOICE' and f['level'] == 'warning' for f in r_sk.findings), notes_nv)
            bad_sk = _copy.deepcopy(sk)
            bpg = deck_root(bad_sk)['pages'][0]
            multi = [s for s in sections_of(bpg) if len(slots_of(s)) >= 2]
            slots_of(multi[0])[0]['slot_type'] = 'body' if slots_of(multi[0])[0]['slot_type'] != 'body' else 'headline'
            multi[1]['slots'] = slots_of(multi[1])[1:]
            bpg['sections'].append({'section_id': 'extra', 'section_role': 'benefits', 'slots': [{'slot_id': 'x', 'slot_type': 'body', 'variants': [{'id': 'a', 'text': '', 'status': 'draft'}], 'chosen': 'a'}]})
            r_b = validate(bad_sk, ctx_sk)
            plan_errs = [f for f in r_b.findings if f['rule'] == 'COPY-D-PLAN']
            check('стык: слот не того типа и секция вне плана → error, слот плана без текста → warning (--final — error)',
                  sum(f['level'] == 'error' for f in plan_errs) >= 2 and any(f['level'] == 'warning' and 'без текста' in f['message'] for f in plan_errs)
                  and any(f['rule'] == 'COPY-D-PLAN' and f['level'] == 'error' and 'без текста' in f['message'] for f in validate(bad_sk, ctx_sk, final=True).findings),
                  [(f['level'], f['message'][:60]) for f in plan_errs])
            # --- страница-образец шаблона коллекции стоит на плане шаблона: site_page_id — id плана
            sm = _copy.deepcopy(sk)
            spg = deck_root(sm)['pages'][0]
            spg['page_id'], spg['site_page_id'] = 'home-sample', plan['page']['id']
            spg['promise']['from'] = spg['promise']['from'].replace('home/', 'home-sample/', 1)
            spg['cta_primary'] = spg['cta_primary'].replace('home/', 'home-sample/', 1)
            r_sm = validate(sm, ctx_sk)
            check('образец шаблона коллекции (свой page_id, site_page_id — id плана): validate — 0 error, стык сверен на образце',
                  not r_sm.count('error') and (r_sm.tools.get('validate') or {}).get('plan_stitch', {}).get('slots') == n_plan,
                  [(f['rule'], f['where'], f['message'][:60]) for f in r_sm.findings if f['level'] == 'error'][:4])
            part = _copy.deepcopy(sm)
            faq_p = next(s for s in sections_of(deck_root(part)['pages'][0]) if len(slots_of(s)) >= 2)
            faq_p['slots'] = slots_of(faq_p)[:-1]
            wrong = _copy.deepcopy(part)
            slots_of(sections_of(deck_root(wrong)['pages'][0])[0])[0]['slot_id'] = 'not-in-plan'
            check('образец несёт не все слоты шаблона — не находка (и с --final); слот образца вне плана — error COPY-D-PLAN',
                  not any(f['rule'] == 'COPY-D-PLAN' for f in validate(part, ctx_sk).findings)
                  and not any(f['rule'] == 'COPY-D-PLAN' and 'без текста' in f['message'] for f in validate(part, ctx_sk, final=True).findings)
                  and any(f['rule'] == 'COPY-D-PLAN' and f['level'] == 'error' and f['where'].startswith('home-sample/') for f in validate(wrong, ctx_sk).findings),
                  [(f['level'], f['where'], f['message'][:60]) for f in validate(part, ctx_sk).findings if f['rule'] == 'COPY-D-PLAN'])
            both = _copy.deepcopy(sk)
            deck_root(both)['pages'].append(_copy.deepcopy(spg))
            r_both = validate(both, ctx_sk)
            check('страница плана и её образец в одном copy deck: стык сверен у обеих',
                  (r_both.tools.get('validate') or {}).get('plan_stitch', {}) == {'sections': 2 * len(sections_of(pg)), 'slots': 2 * n_plan, 'plan_text_slots_without_text': 0}
                  and not any(f['rule'] == 'COPY-D-PLAN' and f['level'] == 'error' for f in r_both.findings),
                  [(f['where'], f['message'][:60]) for f in r_both.findings if f['rule'] == 'COPY-D-PLAN'][:4])
            lost = _copy.deepcopy(sm)
            deck_root(lost)['pages'][0]['site_page_id'] = 'pricing'
            check('страница не стоит на плане (ни page_id, ни site_page_id) — error COPY-D-PLAN',
                  any(f['rule'] == 'COPY-D-PLAN' and f['level'] == 'error' and 'нет страницы' in f['message'] for f in validate(lost, ctx_sk).findings))
            # --- иерархии плана: вторая — у вариантной страницы, иначе правило сведения уровней в плане
            ctx_h = Ctx(sk_p, ctx_sk.facts, '2026-09-29')
            two_h = ['../hierarchy/home-solution-aware.yaml', '../hierarchy/home-problem-aware.yaml']
            got_h, plans_h = {}, {}
            for name in ('none', 'rule', 'variants', 'one'):
                pc = _copy.deepcopy(plan)
                pc['refs'] = dict(pc['refs'], hierarchy=two_h[:1] if name == 'one' else two_h)
                pc['page'] = {k: v for k, v in pc['page'].items() if k != 'awareness_basis'}
                fs_h = {k: v for k, v in (pc['page'].get('first_screen') or {}).items() if k != 'variant_map'}
                if name == 'rule':
                    pc['page']['awareness_basis'] = {'rule': 'по доле трафика: порядок секций — под основной уровень'}
                if name == 'variants':
                    fs_h['variant_map'] = {'param': 'utm_term', 'default': 'base', 'variants': [{'id': 'base', 'when': ['*']}, {'id': 'cold', 'when': ['remont']}]}
                pc['page']['first_screen'] = fs_h
                plans_h[name] = pc
                ctx_h.plan_path = os.path.join(td, f'plan-hierarchy-{name}.yaml')
                with open(ctx_h.plan_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(pc, f, allow_unicode=True, sort_keys=False)
                got_h[name] = [f['level'] for f in validate(sk, ctx_h).findings if f['rule'] == 'COPY-D-HIERARCHY']
            check('иерархии плана: две без вариантов и без правила — warning COPY-D-HIERARCHY; правило awareness_basis.rule, вариантная страница, одна иерархия — без находки',
                  got_h == {'none': ['warning'], 'rule': [], 'variants': [], 'one': []}, got_h)
            check('каркас: две иерархии без вариантов и правила — заметка; с правилом — нет',
                  any('иерархий сообщений' in n for n in skeleton_from_plan(plans_h['none'], plan_p, sk_p, date='2026-09-29')[1])
                  and not any('иерархий сообщений' in n for n in skeleton_from_plan(plans_h['rule'], plan_p, sk_p, date='2026-09-29')[1]))
            # --- готовое сообщение мессенджера: текстовый слот, который называет target.prefill действия плана
            p_pf = _copy.deepcopy(plan)
            hero_pf = next(s for s in p_pf['sections'] if s['id'] == 'hero')
            hero_pf['slots']['text'].append({'id': 'chat-prefill', 'slot': PREFILL_SLOT_TYPE, 'intent': 'запись на замер'})
            hero_pf['slots'].setdefault('action', []).append({'id': 'chat', 'slot': 'messenger-link', 'action': 'message', 'style': 'channel',
                                                             'target': {'kind': 'messenger', 'value': 'messenger:chat-channel', 'prefill': 'chat-prefill'}})
            hero_pf['slots']['text'].append({'id': 'page-prefill', 'slot': PREFILL_SLOT_TYPE})
            p_pf['page']['cta_target'] = {'kind': 'messenger', 'value': 'messenger:chat-channel', 'prefill': 'hero.page-prefill'}
            plan_pf = os.path.join(td, 'plan-prefill.yaml')
            with open(plan_pf, 'w', encoding='utf-8') as f:
                yaml.safe_dump(p_pf, f, allow_unicode=True, sort_keys=False)
            sk_pf, notes_pf = skeleton_from_plan(p_pf, plan_p, sk_p, date='2026-09-29')
            hit_pf = find_slot(deck_root(sk_pf), 'home/hero/chat-prefill')
            sl_pf = hit_pf[2] if hit_pf else {}
            pg_note = str((find_slot(deck_root(sk_pf), 'home/hero/page-prefill') or (None, None, {}))[2].get('notes'))
            check('каркас: слот готового сообщения мессенджера заведён по target.prefill плана — тип слота и пометка действия; у главного призыва страницы — «секция.слот»',
                  sl_pf.get('slot_type') == PREFILL_SLOT_TYPE and 'готовое сообщение мессенджера действия «chat»' in str(sl_pf.get('notes'))
                  and 'главного призыва страницы' in pg_note and not any('prefill' in n for n in notes_pf), (sl_pf, pg_note, notes_pf))
            ctx_pf = Ctx(sk_p, ctx_sk.facts, '2026-09-29', plan_path=plan_pf)
            if PREFILL_SLOT_TYPE not in ctx_pf.vocab['slot_types']:   # словарь site без слота — случай проверяет свою часть
                ctx_pf.vocab['slot_types'][PREFILL_SLOT_TYPE] = {'id': PREFILL_SLOT_TYPE, 'kind': 'text', 'genres': ['email-form']}
                ctx_pf.vocab['slot_kinds'][PREFILL_SLOT_TYPE] = 'text'
                ctx_pf.vocab['status'][('slot', PREFILL_SLOT_TYPE)] = 'active'
            if sl_pf:
                sl_pf['variants'][0].update(text='Здравствуйте! Хочу записаться на замер.', status='assumed')
            r_pf = validate(sk_pf, ctx_pf)
            at_pf = [(f['rule'], f['level']) for f in r_pf.findings if f['where'] == 'home/hero/chat-prefill']
            check('готовое сообщение: validate сверяет слот со стыком плана и правилами copy-slots.yaml (тип известен, error нет)',
                  not r_pf.count('error') and (r_pf.tools.get('validate') or {}).get('plan_stitch', {}).get('slots') == n_plan + 2
                  and not any(r in ('COPY-D-SLOT-UNKNOWN', 'COPY-D-VOCAB', 'COPY-D-PLAN') for r, _l in at_pf),
                  (at_pf, [(f['rule'], f['where'], f['message'][:60]) for f in r_pf.findings if f['level'] == 'error'][:4]))
            pg_pf = deck_root(sk_pf)['pages'][0]
            flat_pf, mp_pf, _a = flatten_for_claims(deck_root(sk_pf), ctx_pf)
            check('готовое сообщение: идёт в сверку фактов своим слотом (жанр email-form по правилу слота), в проекцию страницы для линтера — нет',
                  mp_pf.get(('home', 'hero', 'chat-prefill')) == 'home/hero/chat-prefill'
                  and effective_genre(deck_root(sk_pf), pg_pf, sections_of(pg_pf)[0], PREFILL_SLOT_TYPE, None, ctx_pf.vocab)[0] == 'email-form'
                  and 'Хочу записаться' not in page_markdown(deck_root(sk_pf), pg_pf), page_markdown(deck_root(sk_pf), pg_pf)[:200])
            p_dang = _copy.deepcopy(p_pf)
            del next(s for s in p_dang['sections'] if s['id'] == 'hero')['slots']['text'][-2:]
            sk_dang, notes_dang = skeleton_from_plan(p_dang, plan_p, sk_p, date='2026-09-29')
            check('каркас: target.prefill называет слот, которого нет в секции плана, — заметка, слот не заводится',
                  find_slot(deck_root(sk_dang), 'home/hero/chat-prefill') is None and any('действия «chat»' in n and 'chat-prefill' in n for n in notes_dang)
                  and any('page.cta_target' in n and 'page-prefill' in n for n in notes_dang), notes_dang)
            specs_b, _rn, _nt = load_copy_slots(COPY_SLOTS_PATH)
            check('copy-slots.yaml: правило слота готового сообщения — жанр email-form, роль user-content, факт не нужен',
                  PREFILL_SLOT_TYPE in specs_b and specs_b[PREFILL_SLOT_TYPE]['genre'] == 'email-form' and specs_b[PREFILL_SLOT_TYPE]['fact_required'] == 'never',
                  specs_b.get(PREFILL_SLOT_TYPE))
        else:
            print('  (примера плана site нет — каркас не проверен)')
        # --- выгрузка во вход холста и разбор copy.md
        d = _st_deck()
        pg = d['copy_deck']['pages'][0]
        _st_checked(pg['sections'][0]['slots'][0], 'Ремонт квартир под ключ', 'approved')
        pg['sections'][0]['slots'][1]['variants'][0]['status'] = 'assumed'
        pg['sections'][0]['slots'][2]['variants'][0]['status'] = 'checked'
        _st_checked(pg['sections'][0]['slots'][3], 'Прораб с рулеткой в пустой комнате', 'approved')
        c_md, rows, gaps = export_copy_md(deck_root(d), pg, 'mockup', schema)
        check('выгрузка mockup: в copy.md — только approved; assumed, checked и draft — пробел этапа',
              rows == [('hero', 'h1', 'approved')] and {'home/hero/lead', 'home/hero/cta', 'home/faq/q1'} <= {g['path'] for g in gaps},
              (rows, [g['path'] for g in gaps]))
        check('выгрузка: alt и строки в картинке не идут в copy.md, и утверждённые тоже',
              'alt-hero' not in c_md and 'Прораб с рулеткой' not in c_md and '[h1] approved: Ремонт квартир под ключ' in c_md, c_md[:300])
        c_md3, rows3, _g3 = export_copy_md(deck_root(d), pg, 'directions', schema)
        check('выгрузка directions: заголовок и кнопка первого экрана, статусы assumed · checked · approved',
              rows3 == [('hero', 'h1', 'approved'), ('hero', 'cta', 'checked')], rows3)
        secs_p, notes_p = parse_copy_md(c_md)
        check('copy.md: разбор выгрузки — те же секции, слоты, статусы и тексты', [(s['section_id'], sl['slot_id'], sl['status']) for s in secs_p for sl in s['slots']] == rows and not notes_p, (secs_p, notes_p))
        rt = render_copy_md([{'section_id': 'hero', 'slots': [{'slot_id': 'body', 'status': 'assumed', 'text': 'Абзац один.\nАбзац два.'}]}, {'section_id': None, 'slots': [{'slot_id': None, 'label': 'плашка', 'text': 'Новинка'}]}])
        sp_, _n = parse_copy_md(rt)
        check('copy.md: абзацы строками продолжения, «## ?» и «[? подпись]» — туда и обратно',
              sp_[0]['slots'][0]['text'] == 'Абзац один.\nАбзац два.' and sp_[1]['section_id'] is None and sp_[1]['slots'][0]['label'] == 'плашка', (rt, sp_))
        two = 'Первый абзац.\n\nВторой абзац.\nЕго вторая строка.'
        rt2 = render_copy_md([{'section_id': 'solution', 'slots': [{'slot_id': 'body', 'status': 'approved', 'text': two}, {'slot_id': 'note', 'status': 'approved', 'text': 'Сноска'}]},
                              {'section_id': 'faq', 'slots': [{'slot_id': 'q1', 'status': 'approved', 'text': 'Вопрос?'}]}])
        sp2, n2 = parse_copy_md(rt2)
        sp3, n3 = parse_copy_md('\n'.join(x.rstrip() for x in rt2.split('\n')))   # редактор срезал пробелы пустой строки абзаца
        check('copy.md: слот в два абзаца — значение тянется до следующей строки слота, пустая строка — абзац внутри значения',
              [sl['text'] for s in sp2 for sl in s['slots']] == [two, 'Сноска', 'Вопрос?'] and not n2
              and [sl['text'] for s in sp3 for sl in s['slots']] == [two, 'Сноска', 'Вопрос?'] and not n3, (rt2, sp2, n2, n3))
        fmd, fsumm = export_facts_md(facts, '2026-09-24', 'ru', pg, None, 'mockup', 'Демо')
        check('facts.md: «Факты», «Нет», «Нельзя утверждать»; публикуемый факт, вывод и истёкший — в «Нет»',
              '## Факты' in fmd and '## Нет' in fmd and '## Нельзя утверждать' in fmd and '| guarantee-3 |' in fmd.split('## Нет')[0]
              and '| city-inferred |' in fmd.split('## Нет')[1] and '| promo-old |' in fmd.split('## Нет')[1], fmd[:400])
        check('facts.md: демо-факт — в «Факты» с пометкой, в сводке', 'демо: вымышленные данные' in fmd and fsumm['demo'] == ['rating-demo'], fsumm)
        check('facts.md: «Нельзя утверждать» — строка проекта и умолчания без снимающего факта', 'здоровье и зрение' in fmd and 'Рейтинги и звёзды' not in fmd and 'Отзывы, цитаты' in fmd, fmd.split('## Нельзя утверждать')[1][:300])
        check('facts.md: нет остатков шаблона', not re.search(r'\{\{|\{#|<UNSET', fmd + c_md))
        out_dir = os.path.join(td, 'input')
        rep_e, summ_e = export_canvas(_st_deck(), ctx, out_dir, 'home', 'directions')
        check('export directions: файлы pages/<page-id>/copy.md и facts.md, пробел этапа (черновик заголовка) — COPY-D-STAGE warning, '
              'факты не confirmed — warning',
              summ_e and os.path.exists(os.path.join(out_dir, 'pages', 'home', 'copy.md')) and os.path.exists(os.path.join(out_dir, 'facts.md'))
              and any(f['rule'] == 'COPY-D-STAGE' and f['level'] == 'warning' for f in rep_e.findings)
              and any(f['rule'] == 'COPY-D-FACTS-STATUS' and f['level'] == 'warning' for f in rep_e.findings), (summ_e, [(f['rule'], f['level']) for f in rep_e.findings if f['tool'] == 'export']))
        rep_m, _s = export_canvas(d, ctx, out_dir, 'home', 'mockup')
        check('export mockup: факты не confirmed и текст не approved — error',
              any(f['rule'] == 'COPY-D-FACTS-STATUS' and f['level'] == 'error' for f in rep_m.findings)
              and any(f['rule'] == 'COPY-D-STAGE' and f['level'] == 'error' for f in rep_m.findings))
        # --- приём правок текста с холста
        edited = c_md.replace('[h1] approved: Ремонт квартир под ключ', '[h1]: Ремонт квартир под ключ в Казани') + '\n## ?\n[? плашка]: Новинка сезона\n'
        pg['status'] = 'approved'
        imp, rep_i, summ_i = import_copy(d, edited, 'home', '2026-09-29')
        sl_i = find_slot(deck_root(imp), 'home/hero/h1')[2]
        newv = next(v for v in sl_i['variants'] if v.get('source') == 'customer')
        check('import-copy: изменённый текст → вариант source: customer (draft) в том же слоте, выбор не тронут',
              newv['text'] == 'Ремонт квартир под ключ в Казани' and newv['status'] == 'draft' and sl_i['chosen'] == 'a' and len(summ_i['changed']) == 1, (sl_i, summ_i))
        check('import-copy: текст холста без секции плана → вопрос «перенести в план?»', any(f['rule'] == 'COPY-D-IMPORT-STRUCT' for f in rep_i.findings))
        imp2, _r2, _s2 = import_copy(d, edited, 'home', '2026-09-29', choose=True)
        pg2 = deck_root(imp2)['pages'][0]
        check('import-copy --choose: вариант заказчика выбран, утверждённая страница → draft', find_slot(deck_root(imp2), 'home/hero/h1')[2]['chosen'] == newv['id'] and pg2['status'] == 'draft' and 'approval' not in pg2)
        pg['status'] = 'draft'
        rsch = SubsetValidator(schema).errors(imp)
        check('import-copy: результат проходит схему', not rsch, rsch[:3])
        # --- export-assets
        d = _st_deck()
        for i in range(4):
            d['copy_deck']['pages'][0]['sections'][0]['slots'].append({'slot_id': f't{i}', 'slot_type': 'in-image-text', 'asset_ref': 'banner', 'in_image': {'role': 'label'},
                                                                       'variants': [{'id': 'a', 'text': f'Строка {i}', 'status': 'draft'}], 'chosen': 'a'})
        frag, notes = export_assets(deck_root(d), deck_root(d)['pages'][0])
        banner = next(x for x in frag['slots'] if x['id'] == 'banner')
        check('export-assets: строки in_image с языком и письменностью', banner['text']['mode'] == 'in_image' and banner['text']['strings'][0]['script'] == 'Cyrillic')
        check('export-assets: > 3 строк — заметка', any('> 3' in n for n in notes))
        check('export-assets: alt по asset_ref', next(x for x in frag['slots'] if x['id'] == 'hero')['alt'].startswith('Прораб'))
        check('text_hash: пробелы и NBSP не меняют хэш', text_hash('Смета — бесплатно ') == text_hash('Смета — бесплатно'))
        check('claims_allow: число записи против фрагмента находки — разряды, запятая, число и слово целиком',
              number_key('7 900') == '7900' and number_key('4,90') == '4.9' and number_key(12) == '12' and number_key('двенадцать') is None
              and fragment_numbers('от 7 900 ₽ за 12 лет') == {'7900', '12'}
              and claims_allow_match({'value': '12'}, '12 лет') and not claims_allow_match({'value': '12'}, '120 лет')
              and claims_allow_match({'fragment': 'зарплата'}, 'Зарплата') and not claims_allow_match({'fragment': '12 лет'}, '112 лет')
              and claims_allow_match({}, 'любой фрагмент'), (number_key('4,90'), fragment_numbers('от 7 900 ₽ за 12 лет')))
        # --- запись в другую папку: ссылки остаются от папки исходного файла, дата записи, шапка о файле
        d = _st_deck(facts_ref='../facts/f.yaml', voice_ref='черновик: на «вы»', meaning_ref='m.yaml')
        d['copy_deck']['pages'][0]['hierarchy_ref'] = '../h/h.yaml'
        src_r, out_r = os.path.join(td, 'refs', 'decks', 'deck.yaml'), os.path.join(td, 'refs', 'out', 'run1', 'deck.yaml')
        for rp in ('facts/f.yaml', 'decks/m.yaml', 'h/h.yaml'):
            os.makedirs(os.path.dirname(os.path.join(td, 'refs', rp)), exist_ok=True)
            with open(os.path.join(td, 'refs', rp), 'w', encoding='utf-8') as f:
                f.write('{}\n')
        warn_r = dump_deck(d, out_r, HEAD_CHECKED, src_path=src_r, date='2026-09-30')
        with open(out_r, encoding='utf-8') as f:
            raw_r = f.read()
        dk_r = deck_root(yaml.safe_load(raw_r))
        refs_r = [dk_r['facts_ref'], dk_r['meaning_ref'], dk_r['pages'][0]['hierarchy_ref']]
        check('запись в другую папку: ссылки остаются как в исходном файле и от его папки разрешаются; предупреждение называет ссылки; строка голоса не тронута',
              refs_r == ['../facts/f.yaml', 'm.yaml', '../h/h.yaml'] and all(os.path.exists(rel_to(src_r, r)) for r in refs_r)
              and warn_r and all(k in warn_r for k in ('facts_ref', 'meaning_ref', 'hierarchy_ref')) and 'voice_ref' not in warn_r
              and dk_r['voice_ref'].startswith('черновик'), (refs_r, warn_r))
        check('запись в ту же папку — без предупреждения; дата записи — в copy_deck.date',
              dump_deck(d, os.path.join(td, 'refs', 'decks', 'deck.out.yaml'), HEAD_CHECKED, src_path=src_r, date='2026-09-30') is None
              and dk_r['date'] == '2026-09-30', dk_r['date'])
        d_h = _st_deck(); p2_h = _copy.deepcopy(d_h['copy_deck']['pages'][0]); p2_h['page_id'] = 'about'; d_h['copy_deck']['pages'].append(p2_h)
        for pg_h in d_h['copy_deck']['pages']:
            pg_h['status'] = 'approved'
        heads = {name: deck_header(d_h, what) for name, what in (('check --update и approve', HEAD_CHECKED), ('skeleton', HEAD_SKELETON),
                                                                  ('import-copy', HEAD_IMPORTED), ('select и apply-selection', HEAD_SELECTED))}
        check('шапки записи (skeleton, check --update, approve, import-copy, select, apply-selection): без даты и без пути, утверждённые страницы — все',
              all(h.startswith('# ') and not re.search(r'\d{4}-\d{2}-\d{2}|\.ya?ml|/home|' + re.escape(td), h)
                  and 'утверждённые страницы: home, about' in h for h in heads.values())
              and 'утверждённые страницы' not in deck_header(_st_deck(), HEAD_CHECKED), heads)
        # --- слепой выбор: лист, ключ, голоса → chosen и selection
        d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]
        sl['variants'] += [{'id': 'b', 'text': 'Ремонт с договором', 'status': 'draft', 'source': 'model', 'generated': {'model': 'x'}},
                           {'id': 'c', 'text': 'Ремонт отклонён', 'status': 'rejected', 'reason': 'тест'}]
        md, key, _ex = export_variants(deck_root(d))
        check('export-variants: метки без модели, отклонённые не показываются', 'home/hero/h1' in key and set(key['home/hero/h1'].values()) == {'a', 'b'}
              and 'model' not in md and 'Ремонт отклонён' not in md, (key, md[:200]))
        check('export-variants: порядок воспроизводим', export_variants(deck_root(d))[1] == key)
        lab_b = next(k for k, v in key['home/hero/h1'].items() if v == 'b')
        sheet = md.replace('Выбор: ___', f'Выбор: {lab_b}', 1)
        votes = parse_votes_sheet(sheet)
        check('apply-selection: голос листа разобран', votes.get('home/hero/h1') == lab_b, votes)
        sel_d, rep_s, summ_s = apply_selection(d, key, votes, 'customer', 'заказчик', '2026-09-29', 'sheet.md · key.yaml')
        ssl = find_slot(deck_root(sel_d), 'home/hero/h1')[2]
        check('apply-selection: chosen и selection {method, by, at, compared, ref}', ssl['chosen'] == 'b' and ssl['selection']['method'] == 'customer'
              and sorted(ssl['selection']['compared']) == ['a', 'b'] and ssl['selection']['ref'] and not rep_s.count('error'), ssl.get('selection'))
        tally_d, _rt, _st = apply_selection(d, key, {'home/hero/h1': {lab_b: 5, next(k for k in key['home/hero/h1'] if k != lab_b): 1}}, 'human-pairwise', 'группа', '2026-09-29')
        check('apply-selection: счёт голосов → tally по id вариантов', find_slot(deck_root(tally_d), 'home/hero/h1')[2]['selection'].get('tally', {}).get('b') == 5)
        _tie, rep_t, _ = apply_selection(d, key, {'home/hero/h1': {k: 2 for k in key['home/hero/h1']}}, 'customer', 'x')
        check('apply-selection: ничья — error, выбор за человеком', rep_t.count('error') >= 1)
        # --- открытый выбор варианта: select; у черновика невыбранные варианты — не находка
        import contextlib
        import io
        d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]
        sl['variants'].append({'id': 'b', 'text': 'Ремонт с договором', 'status': 'draft'}); del sl['chosen']
        ch_w = lambda dd: [f['level'] for f in validate(dd, ctx).findings if f['rule'] == 'COPY-D-CHOSEN' and f['where'] == 'home/hero/h1']
        r_dr = ch_w(d)
        sl['variants'][1]['status'] = 'assumed'
        check('невыбранные варианты: у черновика (все живые варианты draft) — не находка, с вариантом assumed — warning COPY-D-CHOSEN',
              r_dr == [] and ch_w(d) == ['warning'], (r_dr, ch_w(d)))
        d['copy_deck']['pages'][0]['status'] = 'checked'
        s_d, rep_sv, summ_sv = select_variant(d, 'home', 'hero/h1', 'b', 'editor', 'редактор', '2026-09-30')
        s_sl = find_slot(deck_root(s_d), 'home/hero/h1')[2] if s_d else {}
        check('select: chosen и selection {method, by, at, compared}; текст слота сменился — страница checked → draft',
              s_d is not None and s_sl.get('chosen') == 'b' and s_sl.get('selection') == {'method': 'editor', 'by': 'редактор', 'at': '2026-09-30', 'compared': ['a', 'b']}
              and summ_sv == {'path': 'home/hero/h1', 'variant': 'b', 'changed': True} and deck_root(s_d)['pages'][0]['status'] == 'draft'
              and not SubsetValidator(schema).errors(s_d), (s_sl.get('selection'), summ_sv, rep_sv.notes))
        s_same, _r, summ_same = select_variant(d, 'home', 'h1', 'a', 'customer', 'заказчик', '2026-09-30')
        check('select: id слота без секции, если он один на странице; выбран тот же текст — страница остаётся checked',
              s_same is not None and summ_same['changed'] is False and deck_root(s_same)['pages'][0]['status'] == 'checked', summ_same)
        bad_sel = [select_variant(d, 'home', ref, var, 'customer', 'заказчик')[1].count('error') for ref, var in (('hero/h1', 'z'), ('hero/net', 'a'), ('promise', 'z'))]
        dup = _copy.deepcopy(d); dup['copy_deck']['pages'][0]['sections'][1]['slots'][0]['slot_id'] = 'h1'
        check('select: нет варианта или слота — отказ; id слота в двух секциях без секции — отказ, с секцией — выбор',
              bad_sel == [1, 1, 1] and select_variant(dup, 'home', 'h1', 'a', 'customer', 'заказчик')[0] is None
              and select_variant(dup, 'home', 'faq/h1', 'a', 'customer', 'заказчик')[0] is not None, bad_sel)
        src_s, out_s, no_s = (os.path.join(td, x) for x in ('select-src.yaml', 'select-out.yaml', 'select-no.yaml'))
        with open(src_s, 'w', encoding='utf-8') as f:
            yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
        with contextlib.redirect_stdout(io.StringIO()):
            rc_s = main(['select', src_s, '--page', 'home', '--slot', 'hero/h1', '--variant', 'b', '--by', 'заказчик', '--at', '2026-09-30', '-o', out_s])
            rc_no = main(['select', src_s, '--page', 'home', '--slot', 'hero/h1', '--variant', 'z', '--by', 'заказчик', '-o', no_s])
        with open(out_s, encoding='utf-8') as f:
            raw_s = f.read()
        dk_s = deck_root(yaml.safe_load(raw_s))
        check('select (команда): файл с шапкой о файле и датой записи; отказ — код 2, файл не пишется',
              rc_s == 0 and rc_no == 1 and not os.path.exists(no_s) and raw_s.startswith('# copy deck — выбор варианта')
              and dk_s['date'] == '2026-09-30' and dk_s['pages'][0]['sections'][0]['slots'][0]['chosen'] == 'b', (rc_s, rc_no, raw_s[:160]))
        # --- утверждение: журнал процесса уходит, selection остаётся
        d = _st_deck(); pg = d['copy_deck']['pages'][0]
        for s in sections_of(pg):
            for sl in slots_of(s):
                _st_checked(sl, 'Замер и смета' if sl['slot_id'] == 'a1' else chosen_variant(sl)['text'])
        pg['promise']['variants'][0]['status'] = 'checked'
        _st_checked(pg['promise'], pg['promise']['variants'][0]['text'])
        h1 = find_slot(deck_root(d), 'home/hero/h1')[2]
        h1['variants'].append({'id': 'x', 'text': 'Ремонт мечты', 'status': 'rejected', 'reason': 'правка по находкам: ru-lex-x'})
        h1['edit_log'] = [{'pass': 1, 'rules': ['ru-lex-x'], 'from_variant': 'x', 'to_variant': 'a'}]
        h1['selection'] = {'method': 'customer', 'by': 'заказчик', 'at': '2026-09-24', 'compared': ['a', 'x']}
        d_bad = _copy.deepcopy(d)
        ap, rep_a = approve_page(d, ctx, 'home', 'заказчик', '2026-09-29')
        ah1 = find_slot(deck_root(ap), 'home/hero/h1')[2] if ap else {}
        check('approve: журнал правки и отклонённые варианты удалены, selection с compared остался',
              ap is not None and 'edit_log' not in ah1 and all(v['status'] != 'rejected' for v in ah1['variants']) and ah1['selection']['compared'] == ['a', 'x']
              and rep_a.tools['approve']['removed'] == {'edit_log': 1, 'rejected': 1}, (rep_a.findings[:3], ah1))
        r_ap = validate(ap, ctx) if ap else Report()
        check('approve → validate: 0 error, удалённые варианты в selection.compared не требуются', ap is not None and not r_ap.count('error')
              and not any(f['rule'] == 'COPY-D-PROCESS-LOG' for f in r_ap.findings), [(f['rule'], f['where']) for f in r_ap.findings if f['level'] == 'error'][:4])
        find_slot(deck_root(d_bad), 'home/hero/cta')[2]['fact_ids'] = ['nope-fact']
        ap_bad, rep_b = approve_page(d_bad, ctx, 'home', 'заказчик', '2026-09-29')
        ap_nf, rep_nf = approve_page(d, Ctx(os.path.join(td, 'elsewhere', 'deck.yaml'), None, '2026-09-24', copy_slots_path=os.path.join(td, 'нет.yaml'),
                                            meta_rules_path=os.path.join(td, 'нет-meta.yaml')), 'home', 'заказчик', '2026-09-29')
        check('approve: файл фактов по facts_ref не найден (копия вне своей папки) — отказ с причиной, а не «заглушка без пробела»',
              ap_nf is None and [f['message'][:20] for f in rep_nf.findings] == ['facts.yaml не найден'], rep_nf.findings[:2])
        check('approve: утверждённая страница не проходит validate (битый fact_ids) — отказ COPY-D-APPROVE',
              ap_bad is None and any(f['rule'] == 'COPY-D-APPROVE' and 'не проходит validate' in f['message'] for f in rep_b.findings), rep_b.findings[:3])
        d2 = _copy.deepcopy(ap)
        find_slot(deck_root(d2), 'home/hero/h1')[2]['edit_log'] = [{'pass': 1}]
        check('утверждённая страница с журналом процесса → warning COPY-D-PROCESS-LOG', ('COPY-D-PROCESS-LOG', 'warning') in {(f['rule'], f['level']) for f in validate(d2, ctx).findings})
        d_nm = _copy.deepcopy(d)
        deck_root(d_nm)['pages'][0]['meta'].update(title='', description='')
        ap_nm, rep_nm = approve_page(d_nm, ctx, 'home', 'заказчик', '2026-09-29')
        got = {(f['rule'], f['level'], f['where']) for f in rep_nm.findings}
        check('approve без меты: утверждено, пустые meta.title и meta.description — warning',
              ap_nm is not None and {('COPY-D-APPROVE', 'warning', 'home/meta/title'), ('COPY-D-APPROVE', 'warning', 'home/meta/description')} <= got
              and not rep_nm.count('error'), got)
        if ap_nm is not None:
            lv = lambda r, rule: {f['level'] for f in r.findings if f['rule'] == rule and f['where'].startswith('home/meta/')}
            check('пустая мета утверждённой страницы: без --final — warning, validate --final — error (ворота публикации)',
                  lv(validate(ap_nm, ctx), 'COPY-D-META') == {'warning'} and lv(validate(ap_nm, ctx, final=True), 'COPY-D-META') == {'error'}
                  and lv(validate(ap_nm, ctx3), 'meta-x-missing') == {'warning'} and lv(validate(ap_nm, ctx3, final=True), 'meta-x-missing') == {'error'},
                  (lv(validate(ap_nm, ctx), 'COPY-D-META'), lv(validate(ap_nm, ctx3), 'meta-x-missing')))
        d_nb = _copy.deepcopy(d)
        del deck_root(d_nb)['pages'][0]['meta']
        ap_nb, rep_nb = approve_page(d_nb, ctx, 'home', 'заказчик', '2026-09-29')
        check('approve без блока meta: утверждено, warning; validate --final — error',
              ap_nb is not None and ('COPY-D-META', 'warning') in {(f['rule'], f['level']) for f in validate(ap_nb, ctx).findings}
              and ('COPY-D-META', 'error') in {(f['rule'], f['level']) for f in validate(ap_nb, ctx, final=True).findings},
              [(f['rule'], f['level'], f['message'][:60]) for f in rep_nb.findings][:4])
        # --- заглушки: пробел missing[] утверждению и макету не мешает, публикацию держит --final; без пробела — отказ
        d_ph = _copy.deepcopy(d)
        _st_checked(find_slot(deck_root(d_ph), 'home/faq/a1')[2], '[PLACEHOLDER: цена замера]')
        ap_ph, rep_ph = approve_page(d_ph, ctx, 'home', 'заказчик', '2026-09-29')
        got = {(f['rule'], f['level'], f['where']) for f in rep_ph.findings}
        lv_ph = lambda r: {f['level'] for f in r.findings if f['rule'] == 'COPY-D-PLACEHOLDER' and f['where'] == 'home/faq/a1'}
        check('approve: заглушка пробела missing[] — warning, страница утверждена; validate — warning, --final — error',
              ap_ph is not None and ('COPY-D-APPROVE', 'warning', 'home/faq/a1') in got and not rep_ph.count('error')
              and lv_ph(validate(ap_ph, ctx)) == {'warning'} and lv_ph(validate(ap_ph, ctx, final=True)) == {'error'},
              (got, rep_ph.findings[:3]))
        d_lo = _copy.deepcopy(d)
        _st_checked(find_slot(deck_root(d_lo), 'home/hero/cta')[2], 'Позвонить [PLACEHOLDER: телефон]')
        ap_lo, rep_lo = approve_page(d_lo, ctx, 'home', 'заказчик', '2026-09-29')
        check('approve: заглушка без пробела в facts.yaml — отказ COPY-D-APPROVE',
              ap_lo is None and any(f['rule'] == 'COPY-D-APPROVE' and f['level'] == 'error' and f['where'] == 'home/hero/cta'
                                    for f in rep_lo.findings), rep_lo.findings[:3])
        d_fo = _copy.deepcopy(d)
        _st_checked(find_slot(deck_root(d_fo), 'home/faq/a1')[2], '[PLACEHOLDER: что-то совсем другое]')
        ap_fo, rep_fo = approve_page(d_fo, ctx, 'home', 'заказчик', '2026-09-29')
        check('approve: заглушка о другом при missing_ids слота — отказ COPY-D-APPROVE (чужой пробел её не прикрывает)',
              find_slot(deck_root(d_fo), 'home/faq/a1')[2].get('missing_ids') == ['measure-price'] and ap_fo is None
              and any(f['rule'] == 'COPY-D-APPROVE' and f['level'] == 'error' and f['where'] == 'home/faq/a1' and 'заглушка без пробела' in f['message']
                      for f in rep_fo.findings), rep_fo.findings[:3])
        fx_g = _st_facts()
        fx_g['missing'].append({'id': 'crew', 'what': 'бригадир: имя и стаж', 'placeholder': '[PLACEHOLDER: бригадир — имя, стаж]', 'who': 'заказчик'})
        fg = Facts(fx_g, os.path.join(td, 'facts.yaml'))
        got = [placeholder_links(t, fg, ids) for t, ids in (
            ('[PLACEHOLDER: цена замера]', None), ('[PLACEHOLDER: имя бригадира]', ['crew']), ('[PLACEHOLDER: стаж бригадира]', ['missing:crew']),
            ('[PLACEHOLDER: имя бригадира]', None), ('[PLACEHOLDER: часы работы]', ['crew']), ('[PLACEHOLDER]', ['crew']), ('[PLACEHOLDER]', None))]
        check('заглушка и пробел: placeholder любого пробела дословно; часть своего пробела словами; о другом или без missing_ids — без пробела',
              got == [(['measure-price'], []), (['crew'], []), (['crew'], []), ([], ['[PLACEHOLDER: имя бригадира]']),
                      ([], ['[PLACEHOLDER: часы работы]']), (['crew'], []), ([], ['[PLACEHOLDER]'])], got)
        check('заглушка и пробел: одно общее слово из двух — мало (больше половины значимых слов заглушки)',
              placeholder_links('[PLACEHOLDER: телефон бригадира]', fg, ['crew']) == ([], ['[PLACEHOLDER: телефон бригадира]']))
        d_pa = _copy.deepcopy(d)
        a1_pa = find_slot(deck_root(d_pa), 'home/faq/a1')[2]
        _st_checked(a1_pa, '[PLACEHOLDER: имя бригадира]')
        a1_pa['missing_ids'] = ['crew']
        ctx_g = Ctx(os.path.join(td, 'deck.yaml'), fg, '2026-09-24', copy_slots_path=os.path.join(td, 'нет.yaml'), meta_rules_path=os.path.join(td, 'нет-meta.yaml'))
        ap_pa, rep_pa = approve_page(d_pa, ctx_g, 'home', 'заказчик', '2026-09-29')
        check('approve: заглушка части своего пробела (один пробел на несколько слотов) — warning, страница утверждена',
              ap_pa is not None and not rep_pa.count('error') and any(f['level'] == 'warning' and f['where'] == 'home/faq/a1' and 'missing:crew' in f['message'] for f in rep_pa.findings)
              and {f['level'] for f in validate(ap_pa, ctx_g).findings if f['rule'] == 'COPY-D-PLACEHOLDER' and f['where'] == 'home/faq/a1'} == {'warning'},
              rep_pa.findings[:3])
        # --- check --promote: draft и assumed → checked
        d = _st_deck(); pg = d['copy_deck']['pages'][0]
        pg['sections'][0]['slots'][0]['variants'][0]['status'] = 'assumed'
        rec = {'errors': 0, 'warnings': 0, 'info': 0, 'rules': []}
        lrec = {'profile': 'landing', 'errors': 0, 'warnings': 0, 'info': 0, 'suppressed': 0, 'verdict': 'clean'}
        upd, _n = apply_records(d, {'home/hero/h1': dict(rec), 'home/hero/cta': dict(rec)}, {'home/hero/h1': dict(lrec), 'home/hero/cta': dict(lrec)}, '2026-09-29', promote=True)
        uh = find_slot(deck_root(upd), 'home/hero/h1')[2]
        check('check --promote: assumed → checked (запись утилиты)', chosen_variant(uh)['status'] == 'checked' and chosen_variant(uh)['review']['by'].startswith('copydeck')
              and chosen_variant(find_slot(deck_root(upd), 'home/hero/cta')[2])['status'] == 'checked')
        check('check --promote: страница остаётся draft, пока проверены не все её тексты', deck_root(upd)['pages'][0]['status'] == 'draft')
        # --- check --promote: статус страницы — минимум статусов её текстов; error проверки статус не повышает
        d = _st_deck(); pg = d['copy_deck']['pages'][0]; pg['status'] = 'assumed'
        all_p = [p for _pg, _s, _sl, p in iter_slots(deck_root(d))] + ['home/promise']
        cpp, lpp = {p: dict(rec) for p in all_p}, {p: dict(lrec) for p in all_p}
        st_of = lambda dd, p: _status_of(chosen_variant(find_slot(deck_root(dd), p)[2]))
        lg = {}
        upd, _n = apply_records(d, cpp, lpp, '2026-09-29', promote=True, log=lg)
        check('check --promote: все выбранные тексты checked → страница assumed → checked', deck_root(upd)['pages'][0]['status'] == 'checked'
              and lg['pages'] == ['home'] and len(lg['promoted']) == len(all_p) and not lg['held'], (deck_root(upd)['pages'][0]['status'], lg))
        upd, _n = apply_records(d, cpp, lpp, '2026-09-29', promote=True, held={'home/faq/a1'}, log=lg)
        check('check --promote: error проверки на тексте (COPY-D-MISSING-REF) — текст и страница не повышаются, остальные тексты — checked',
              st_of(upd, 'home/faq/a1') == 'draft' and st_of(upd, 'home/hero/h1') == 'checked' and deck_root(upd)['pages'][0]['status'] == 'assumed'
              and lg['held'] == ['home/faq/a1'] and not lg['pages'], (st_of(upd, 'home/faq/a1'), lg))
        upd, _n = apply_records(d, cpp, lpp, '2026-09-29', promote=True, held={'—'}, log=lg)
        check('check --promote: error всего файла (схема, корень) — страница не повышается', deck_root(upd)['pages'][0]['status'] == 'assumed' and st_of(upd, 'home/hero/h1') == 'checked')
        rep_h = Report()
        rep_h.add('lint', 'error', 'ru-lex-x', 'home/hero/h1', 'штамп у альтернативы', variant='b')
        rep_h.add('claims', 'error', 'COPY-F-NUM', 'home/hero/lead', 'число без факта', variant='a')
        rep_h.add('lint', 'error', 'an-x', 'home' + PAGE_PASS, 'находка прохода страницы')
        rep_h.add('validate', 'warning', 'COPY-D-EMPTY', 'home/hero/cta', 'пусто')
        fr_h = {'home/hero/h1': {'lint': {'errors': 0, 'variants': {'b': {'errors': 1}}}}, 'home/hero/lead': {'claims': {'errors': 1}}}
        check('check --promote: error невыбранного варианта (--all-variants) выбранный текст не держит; проход страницы — место страницы',
              error_paths(rep_h, fr_h) == {'home/hero/lead', 'home'} and error_paths(rep_h) == {'home/hero/h1', 'home/hero/lead', 'home'},
              (error_paths(rep_h, fr_h), error_paths(rep_h)))
        d_ap = _copy.deepcopy(ap)
        upd, _n = apply_records(d_ap, cpp, lpp, '2026-09-29', promote=True, log=lg)
        check('check --promote: утверждённая страница и её тексты не меняются', deck_root(upd)['pages'][0]['status'] == 'approved'
              and deck_root(upd)['pages'][0].get('approval') == deck_root(ap)['pages'][0].get('approval') and st_of(upd, 'home/hero/h1') == 'approved'
              and not lg['promoted'] and not lg['pages'], lg)
        # --- варианты со своими фактами, пробелы в check
        d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][1]
        sl['variants'].append({'id': 'b', 'text': 'Смета до договора — бесплатно', 'status': 'draft', 'fact_ids': ['estimate-free']})
        sl['variants'].append({'id': 'c', 'text': 'Старый вариант', 'status': 'rejected', 'reason': 'тест', 'fact_ids': ['nope-old']})
        us = {(u['variant'], tuple(u['fact_ids'])) for u in text_units(deck_root(d), deck_root(d)['pages'][0], all_variants=True) if u['path'] == 'home/hero/lead'}
        check('variant.fact_ids: свои факты варианта заменяют факты слота; отклонённый — не в списке', us == {('a', ('guarantee-3',)), ('b', ('estimate-free',))}, us)
        r0 = validate(d, ctx)
        check('variant.fact_ids: битая ссылка невыбранного варианта — warning с id варианта',
              any(f['rule'] == 'COPY-D-FACT-REF' and f['level'] == 'warning' and f['where'] == 'home/hero/lead/b' for f in r0.findings)
              and not any(f['where'] == 'home/hero/lead/c' for f in r0.findings), [(f['rule'], f['where']) for f in r0.findings if 'FACT' in f['rule']])
        sl['chosen'] = 'b'
        r1 = validate(d, ctx)
        check('variant.fact_ids: выбран вариант со своими фактами → info COPY-D-VARIANT-FACTS', any(f['rule'] == 'COPY-D-VARIANT-FACTS' for f in r1.findings))
        flat, mp, alt = flatten_for_claims(deck_root(d), ctx, alternatives=True)
        lead = next(x for x in flat['copy_deck']['pages'][0]['sections'] if x['section_id'] == 'hero')['slots'][1]
        check('claims: в основной сверке — факты выбранного варианта', lead['fact_ids'] == ['estimate-free'] and [v['id'] for v in lead['variants']] == ['b'], lead)
        check('claims: --all-variants — альтернатива a со своими (слотовыми) фактами, отклонённая c не сверяется',
              ('home/hero/lead', 'a') in alt.values() and ('home/hero/lead', 'c') not in alt.values(), sorted(alt.values()))
        upd, n_rec = apply_records(d, {'home/hero/lead': {'errors': 0, 'warnings': 0, 'info': 0, 'rules': [], 'variants': {'a': {'errors': 2, 'warnings': 0, 'info': 0, 'rules': ['COPY-F-X']}}}},
                                   {'home/hero/lead': {'profile': 'landing', 'errors': 0, 'warnings': 0, 'info': 0, 'suppressed': 0, 'verdict': 'clean',
                                                       'variants': {'a': {'profile': 'landing', 'errors': 0, 'warnings': 1, 'info': 0, 'suppressed': 0, 'verdict': 'review'}}}},
                                   '2026-09-24')
        ul = deck_root(upd)['pages'][0]['sections'][0]['slots'][1]
        va = next(v for v in ul['variants'] if v['id'] == 'a')
        check('check --update: факты выбранного варианта → в слот, прежний список слота — варианту без своих', ul['fact_ids'] == ['estimate-free'] and va.get('fact_ids') == ['guarantee-3'], (ul['fact_ids'], va.get('fact_ids')))
        check('check --all-variants --update: записи — у выбранного текста слота (text_hash выбранного варианта), у вариантов поля checks нет',
              n_rec == 1 and ul['claims']['errors'] == 0 and ul['lint']['text_hash'] == text_hash('Смета до договора — бесплатно')
              and not any('checks' in v for v in ul['variants']), (n_rec, ul.get('lint'), [sorted(v) for v in ul['variants']]))
        rsch = SubsetValidator(schema).errors(upd)
        check('check --all-variants --update: копия проходит схему (variant.fact_ids)', not rsch, rsch[:3])
        fx = _st_facts(); fx['missing'].append({'id': 'min-job', 'what': 'минимальный объём', 'placeholder': '[PLACEHOLDER: минимальный объём]', 'who': 'заказчик', 'fallback': 'omit-block'})
        ctxg = Ctx(os.path.join(td, 'deck.yaml'), Facts(fx, os.path.join(td, 'facts.yaml')), '2026-09-24', copy_slots_path=os.path.join(td, 'нет.yaml'), meta_rules_path=os.path.join(td, 'нет-meta.yaml'))
        d = _st_deck(); a1 = d['copy_deck']['pages'][0]['sections'][1]['slots'][1]
        a1['variants'][0]['text'] = '[PLACEHOLDER: минимальный объём]'; a1['missing_ids'] = ['min-job']
        d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['fact_ids'] = ['nope-fact']
        rs = validate(d, ctxg, skip_fact_checks=True)
        check('check: пробелы и fallback проверяются и при свежей сверке', any(f['rule'] == 'COPY-D-FALLBACK' for f in rs.findings), [(f['rule'], f['where']) for f in rs.findings][:6])
        check('check: ссылки фактов при свежей сверке не дублируются (их даёт claims_check)', not any(f['rule'] == 'COPY-D-FACT-REF' for f in rs.findings))
        bt = dict(brief_texts({'site': {'sections': [{'id': 'final', 'job': 'Что сделать сейчас? → Вызвать замерщика'},
                                                     {'id': 'solution', 'job': 'Решение → Один подрядчик; доказательства: guarantee-3'}]}}))
        check('поля брифа холста: стрелка в job — граница фразы для сверки', bt.get('brief:site.sections[final].job') == 'Что сделать сейчас? Вызвать замерщика'
              and bt.get('brief:site.sections[solution].job') == 'Решение. Один подрядчик', bt)
        mp_, mnotes = meaning_projection({'audience': [{'id': 's1', 'name': 'Владельцы квартир', 'primary': True, 'situation': 'Купили вторичку', 'knows': 'сравнивают бригады'}],
                                          'awareness': {'level': 'solution-aware'},
                                          'positioning': {'market_category': {'name': 'ремонт под ключ'}, 'value_themes': [{'theme': 'Срок и смета в договоре'}], 'best_fit': {'segment_ids': ['s1']}},
                                          'value_proposition': {'core': {'text': 'Ремонт без усталости глаз', 'basis': {'kind': 'brief'}}},
                                          'boundaries': {'not_promised': [{'text': 'здоровье', 'claim_class': 'health'}]}},
                                         [{'traffic_source': 'maps-local', 'share': 0.6, 'device': 'mobile'}])
        check('поля продукта из смысла: description и target_user выведены, goal с классом not_promised не выводится',
              mp_.get('product.description', '').startswith('Ремонт под ключ — срок и смета') and 'с телефона' in mp_.get('product.target_user', '')
              and 'product.goal' not in mp_ and any('not_promised' in n for n in mnotes), (mp_, mnotes))
        # --- before-after.tsv: why из rule_ref
        md_dir = os.path.join(td, 'kbt', '04-copy-by-block')
        os.makedirs(md_dir)
        with open(os.path.join(md_dir, 'x.md'), 'w', encoding='utf-8') as f:
            f.write('# X\n\n## 1. Заголовок первого экрана\n\nтекст\n\n### 1.2. Кнопка\n')
        ba = os.path.join(td, 'ba.tsv')
        with open(ba, 'w', encoding='utf-8') as f:
            f.write('before\tafter\trule_ref\tlang\twhy\n'
                    'А\tБ\t04-copy-by-block/x.md §1\tru\t\n'
                    'В\tГ\t04-copy-by-block/x.md §1.2\tru\tуже есть\n'
                    'Д\tЕ\t04-copy-by-block/x.md §7\tru\t\n')
        lines, filled, missed = before_after_fill(ba, os.path.join(td, 'kbt'))
        check('before-after: пустой why ← заголовок раздела rule_ref, заполненный не тронут, раздел не найден — в отчёт',
              [w for _i, w in filled] == ['норма: Заголовок первого экрана (04-copy-by-block/x.md §1)'] and lines[2].endswith('уже есть') and [i for i, _r in missed] == [4], (filled, missed))
        # --- интеграция: claims_check.py (процесс) и copy_lint.lint_text
        fpath = os.path.join(td, 'facts.yaml')
        with open(fpath, 'w', encoding='utf-8') as f:
            yaml.safe_dump(_st_facts(), f, allow_unicode=True)
        d = _st_deck(); d['copy_deck']['pages'][0]['promise']['variants'][0]['text'] = 'Читайте вечером без усталости глаз'
        if os.path.exists(CLAIMS_CHECK):
            rep_c = Report()
            pp = run_claims(deck_root(d), ctx, fpath, rep_c)
            check('claims: утилита отработала', pp is not None, [f['message'] for f in rep_c.findings][:2])
            check('claims: обещание про глаза → COPY-F-NEVER в home/promise (обещание — текст страницы)',
                  any(f['rule'] == 'COPY-F-NEVER' and f['where'] == 'home/promise' for f in rep_c.findings), [(f['rule'], f['where']) for f in rep_c.findings][:6])
            d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]
            sl['variants'] += [{'id': 'b', 'text': 'Ремонт, после которого не болят глаза', 'status': 'rejected', 'reason': 'обещание здоровья'},
                               {'id': 'c', 'text': 'Ремонт, который бережёт зрение', 'status': 'draft'}]
            rep_c = Report()
            pp = run_claims(deck_root(d), ctx, fpath, rep_c, all_variants=True)
            nev = [(f['where'], f.get('variant')) for f in rep_c.findings if f['rule'] == 'COPY-F-NEVER']
            check('claims --all-variants: отклонённый вариант не сверяется, живой — сверяется «как выбранный»',
                  ('home/hero/h1', 'c') in nev and ('home/hero/h1', 'b') not in nev, nev)
            check('claims --all-variants: итоги варианта отдельно, статус выбранного не задет',
                  pp and pp['home/hero/h1']['errors'] == 0 and pp['home/hero/h1']['variants']['c']['errors'] >= 1, (pp or {}).get('home/hero/h1'))
            d = _st_deck(); d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['variants'][0]['text'] = 'Рейтинг 4,9 из 5 на Яндекс Картах — 120 оценок'
            d['copy_deck']['pages'][0]['sections'][0]['slots'][1]['fact_ids'] = ['rating-demo']
            rep_c, rep_f = Report(), Report()
            run_claims(deck_root(d), ctx, fpath, rep_c)
            run_claims(deck_root(d), ctx, fpath, rep_f, final=True)
            check('claims: демо-факт — без --final сигнал, с --final error COPY-F-EXAMPLE',
                  not any(f['rule'] == 'COPY-F-EXAMPLE' and f['level'] == 'error' for f in rep_c.findings)
                  and any(f['rule'] == 'COPY-F-EXAMPLE' and f['level'] == 'error' for f in rep_f.findings), [(f['rule'], f['level']) for f in rep_f.findings][:5])
            # --- обход эвристик сверки claims_allow: решение человека с причиной, право и never_claim не обходятся
            d = _st_deck(); pg = d['copy_deck']['pages'][0]
            h1 = find_slot(deck_root(d), 'home/hero/h1')[2]
            h1['variants'][0]['text'] = 'Зарплата и кадры'
            pp0 = run_claims(deck_root(d), ctx, fpath, Report())
            h1['claims_allow'] = [{'rule': 'COPY-F-CLASS', 'reason': 'название услуги «Зарплата и кадры», а не обещание дохода', 'by': 'заказчик'}]
            rep_a = Report()
            pp_a = run_claims(deck_root(d), ctx, fpath, rep_a)
            check('claims_allow COPY-F-CLASS: «Зарплата и кадры» — не error, обход списком с причиной и тем, кто решил',
                  pp0 and pp0['home/hero/h1']['errors'] >= 1 and pp_a and pp_a['home/hero/h1']['errors'] == 0
                  and not any(f['rule'] == 'COPY-F-CLASS' and f['where'] == 'home/hero/h1' for f in rep_a.findings)
                  and [(x['rule'], x['where'], x['by'], x['fragment']) for x in rep_a.allowed] == [('COPY-F-CLASS', 'home/hero/h1', 'заказчик', 'Зарплата')]
                  and 'Обходы сверки claims_allow' in render_text(rep_a, 'claims') and rep_a.tools['claims']['summary'].get('allowed') == 1,
                  ((pp0 or {}).get('home/hero/h1'), (pp_a or {}).get('home/hero/h1'), rep_a.allowed))
            d_ok = _copy.deepcopy(d); pg_ok = deck_root(d_ok)['pages'][0]
            for s in sections_of(pg_ok):
                for sl in slots_of(s):
                    _st_checked(sl, 'Замер и смета' if sl['slot_id'] == 'a1' else chosen_variant(sl)['text'])
            _st_checked(pg_ok['promise'], pg_ok['promise']['variants'][0]['text'])
            find_slot(deck_root(d_ok), 'home/hero/h1')[2]['claims'] = _claims_rec(pp_a['home/hero/h1'], '2026-09-24', text_hash('Зарплата и кадры'))
            ap_a, rep_ap = approve_page(d_ok, ctx, 'home', 'заказчик', '2026-09-29')
            r_fin = validate(ap_a, ctx, final=True) if ap_a else Report()
            check('claims_allow: approve проходит, обход — отдельным списком утверждения и validate --final',
                  ap_a is not None and [(x['rule'], x['where']) for x in rep_ap.allowed] == [('COPY-F-CLASS', 'home/hero/h1')]
                  and [(x['rule'], x['where'], x['by']) for x in r_fin.allowed] == [('COPY-F-CLASS', 'home/hero/h1', 'заказчик')],
                  ([(f['rule'], f['message'][:60]) for f in rep_ap.findings if f['level'] == 'error'][:3], rep_ap.allowed, r_fin.allowed))
            h1['claims_allow'] = [{'rule': 'COPY-F-CLASS', 'reason': 'название услуги'}]
            rep_b = Report()
            pp_b = run_claims(deck_root(d), ctx, fpath, rep_b)
            check('claims_allow без by — не обход: error остаётся, совет называет запись, validate — warning COPY-D-CLAIMS-ALLOW',
                  pp_b and pp_b['home/hero/h1']['errors'] >= 1 and not rep_b.allowed
                  and any(f['rule'] == 'COPY-F-CLASS' and 'claims_allow не обход' in f['fix'] for f in rep_b.findings)
                  and any(f['rule'] == 'COPY-D-CLAIMS-ALLOW' and f['level'] == 'warning' and 'нет by' in f['message'] for f in validate(d, ctx).findings),
                  ((pp_b or {}).get('home/hero/h1'), rep_b.allowed))
            h1['variants'][0]['text'] = 'Лучший ремонт в городе'
            h1['claims_allow'] = [{'rule': 'COPY-L-SUP-01', 'reason': 'слоган из брифа', 'by': 'заказчик'},
                                  {'rule': 'COPY-F-CLASS', 'reason': 'слоган из брифа', 'by': 'заказчик'}]
            rep_l = Report()
            run_claims(deck_root(d), ctx, fpath, rep_l)
            check('claims_allow на COPY-L-*: право не обходится — error права остаётся, запись — warning COPY-D-CLAIMS-ALLOW',
                  any(f['rule'] == 'COPY-L-SUP-01' and f['level'] == 'error' and f['where'] == 'home/hero/h1' for f in rep_l.findings)
                  and [x['rule'] for x in rep_l.allowed] == ['COPY-F-CLASS']
                  and any(f['rule'] == 'COPY-D-CLAIMS-ALLOW' and 'COPY-L-SUP-01' in f['message'] for f in validate(d, ctx).findings),
                  ([(f['rule'], f['level']) for f in rep_l.findings if f['where'] == 'home/hero/h1'], rep_l.allowed))
            fx_n = _st_facts()
            fx_n['facts'].append({'id': 'since-2014', 'kind': 'company', 'claim_class': ['fact-number'], 'verbatim': ['Работаем с 2014 года'],
                                  'canonical': 'Студия работает с 2014 года.', 'source': {'type': 'customer-document', 'who': 'заказчик', 'date': '2026-09-24', 'document': 'выписка ЕГРЮЛ'},
                                  'verification': {'status': 'verified'}, 'permission': {'status': 'not-required'}, 'lang': 'ru'})
            fpath_n = os.path.join(td, 'facts-num.yaml')
            with open(fpath_n, 'w', encoding='utf-8') as f:
                yaml.safe_dump(fx_n, f, allow_unicode=True)
            ctx_n = Ctx(os.path.join(td, 'deck.yaml'), Facts(fx_n, fpath_n), '2026-09-24', copy_slots_path=os.path.join(td, 'нет.yaml'), meta_rules_path=os.path.join(td, 'нет-meta.yaml'))
            h1['variants'][0]['text'] = 'Работаем 12 лет'
            h1['claims_allow'] = [{'rule': 'COPY-F-NUM', 'reason': 'fact:since-2015: 12 лет = 2026 − 2014', 'by': 'аналитик'}]
            rep_n = Report()
            run_claims(deck_root(d), ctx_n, fpath_n, rep_n)
            miss_n = [f['rule'] for f in rep_n.findings if f['where'] == 'home/hero/h1' and f['level'] == 'error']
            h1['claims_allow'][0]['reason'] = 'fact:since-2014: 12 лет = 2026 − 2014'
            rep_n2 = Report()
            run_claims(deck_root(d), ctx_n, fpath_n, rep_n2)
            check('claims_allow COPY-F-NUM: число с несовпавшим фактом обходится причиной с fact:<id>; факта нет — не обход',
                  bool(set(miss_n) & {'COPY-F-NUM', 'COPY-F-NUM-MISMATCH'}) and not rep_n.allowed
                  and not any(f['where'] == 'home/hero/h1' and f['level'] == 'error' for f in rep_n2.findings)
                  and [x['rule'] for x in rep_n2.allowed] and all(x['rule'] in CLAIMS_ALLOW_RULES['COPY-F-NUM'] for x in rep_n2.allowed),
                  (miss_n, [(x['rule'], x['fragment']) for x in rep_n2.allowed]))
            # --- обход называет, что именно снято (value, fragment), место обхода у мета, rule — id находки
            d = _st_deck()
            find_slot(deck_root(d), 'home/hero/h1')[2]['variants'][0]['text'] = 'Работаем 12 лет'
            find_slot(deck_root(d), 'home/hero/cta')[2]['variants'][0]['text'] = 'Сдали 340 квартир'
            d['copy_deck']['pages'][0]['meta']['title'] = 'Ремонт квартир: работаем 12 лет — Демо'
            num_err = lambda r: sorted(f['where'] for f in r.findings if f['level'] == 'error' and f['rule'] in CLAIMS_ALLOW_RULES['COPY-F-NUM'])
            why12 = 'fact:since-2014: 12 лет = 2026 − 2014'

            def claims_with(page_allow=None, meta_allow=None):
                dd = _copy.deepcopy(d)
                pg_ = deck_root(dd)['pages'][0]
                if page_allow:
                    pg_['claims_allow'] = page_allow
                if meta_allow:
                    pg_['meta']['claims_allow'] = meta_allow
                r = Report()
                run_claims(deck_root(dd), ctx_n, fpath_n, r)
                return r, dd
            r_0, _dd = claims_with()
            r_val, d_val = claims_with(page_allow=[{'rule': 'COPY-F-NUM', 'value': 12, 'reason': why12, 'by': 'аналитик'}])
            check('claims_allow с value: обход страницы снимает находки о числе 12, число 340 на той же странице остаётся error',
                  num_err(r_0) == ['home/hero/cta', 'home/hero/h1', 'home/meta/title'] and num_err(r_val) == ['home/hero/cta']
                  and sorted(x['where'] for x in r_val.allowed) == ['home/hero/h1', 'home/meta/title'] and not SubsetValidator(schema).errors(d_val),
                  (num_err(r_0), num_err(r_val), SubsetValidator(schema).errors(d_val)[:2]))
            r_meta, d_meta = claims_with(meta_allow=[{'rule': 'COPY-F-NUM', 'fragment': '12 лет', 'reason': why12, 'by': 'аналитик'}])
            check('claims_allow у мета (meta.claims_allow): снята находка текста мета, то же число в слоте остаётся error',
                  num_err(r_meta) == ['home/hero/cta', 'home/hero/h1'] and [(x['where'], x['scope']) for x in r_meta.allowed] == [('home/meta/title', 'meta')]
                  and not SubsetValidator(schema).errors(d_meta), (num_err(r_meta), r_meta.allowed, SubsetValidator(schema).errors(d_meta)[:2]))
            r_id, _dd = claims_with(page_allow=[{'rule': 'COPY-F-NUM-MISMATCH', 'reason': why12, 'by': 'аналитик'}])
            check('claims_allow с id находки COPY-F-NUM-MISMATCH: снято только несовпавшее число, числа без факта остаются error',
                  num_err(r_id) == ['home/hero/cta', 'home/meta/title'] and [x['rule'] for x in r_id.allowed] == ['COPY-F-NUM-MISMATCH'], (num_err(r_id), r_id.allowed))
            d_nv = _copy.deepcopy(d)
            deck_root(d_nv)['pages'][0]['claims_allow'] = [{'rule': 'COPY-F-NUM', 'value': 'двенадцать', 'reason': why12, 'by': 'аналитик'}]
            check('claims_allow: value не число — не обход, validate — warning COPY-D-CLAIMS-ALLOW',
                  any(f['rule'] == 'COPY-D-CLAIMS-ALLOW' and f['level'] == 'warning' and 'не число' in f['message'] for f in validate(d_nv, ctx_n).findings))
            if lint_module() is not None:
                # --- check --update --promote целиком: шапка файла, статус страницы, error проверки
                import contextlib
                import io
                d = _st_deck(); pg = d['copy_deck']['pages'][0]; pg['status'] = 'assumed'
                pg['promise'] = {'from': 'home/hero/lead'}
                src_p, out_p = os.path.join(td, 'deck-src.yaml'), os.path.join(td, 'checked', 'deck.yaml')
                with open(src_p, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err_u:
                    rc_u = main(['check', src_p, '--facts', fpath, '--today', '2026-09-29', '--update', out_p, '--promote', '--quiet'])
                with open(out_p, encoding='utf-8') as f:
                    raw_u = f.read()
                head_u = '\n'.join(x for x in raw_u.split('\n') if x.startswith('#'))
                pg_u = deck_root(yaml.safe_load(raw_u))['pages'][0]
                check('check --update: шапка файла — без даты и без пути источника; папка выхода создаётся',
                      rc_u == 0 and head_u and not re.search(r'\d{4}-\d{2}-\d{2}', head_u) and td not in head_u and 'deck-src' not in head_u, head_u)
                check('check --update в другую папку: facts_ref — как в исходном файле, дата записи — дата проверки, предупреждение о папке',
                      deck_root(yaml.safe_load(raw_u))['facts_ref'] == 'facts.yaml' and deck_root(yaml.safe_load(raw_u))['date'] == '2026-09-29'
                      and 'вне папки исходного' in err_u.getvalue(), (deck_root(yaml.safe_load(raw_u))['facts_ref'], err_u.getvalue()[:200]))
                check('check --update --promote: 0 error → тексты и страница checked',
                      pg_u['status'] == 'checked' and all(_status_of(chosen_variant(sl)) == 'checked' for s in sections_of(pg_u) for sl in slots_of(s)),
                      (pg_u['status'], [(sl['slot_id'], _status_of(chosen_variant(sl))) for s in sections_of(pg_u) for sl in slots_of(s)]))
                find_slot(deck_root(d), 'home/faq/a1')[2]['missing_ids'] = ['нет-такого-пробела']
                del find_slot(deck_root(d), 'home/hero/cta')[2]['chosen']
                with open(src_p, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
                jp_u = os.path.join(td, 'check-promote.json')
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    rc_e = main(['check', src_p, '--facts', fpath, '--today', '2026-09-29', '--update', out_p, '--promote', '--quiet', '--json', jp_u])
                with open(out_p, encoding='utf-8') as f:
                    dk_e = yaml.safe_load(f)
                with open(jp_u, encoding='utf-8') as f:
                    js_e = json.load(f)
                check('--json для кода: tool copydeck.py, skill_version — VERSION скилла, command, summary.error — число',
                      js_e.get('tool') == 'copydeck.py' and js_e.get('skill_version') == kbpaths.skill_version()
                      and js_e.get('command') == 'check' and isinstance((js_e.get('summary') or {}).get('error'), int),
                      {k: js_e.get(k) for k in ('tool', 'skill_version', 'command', 'summary')})
                st_e = {sl['slot_id']: _status_of(chosen_variant(sl)) for s in sections_of(deck_root(dk_e)['pages'][0]) for sl in slots_of(s)}
                check('check --update --promote при error COPY-D-MISSING-REF: текст с error и страница не повышаются, чистые тексты — checked',
                      rc_e == 1 and st_e['a1'] == 'draft' and st_e['h1'] == 'checked' and deck_root(dk_e)['pages'][0]['status'] == 'assumed'
                      and 'home/faq/a1' in js_e['promote']['held'], (rc_e, st_e, js_e.get('promote')))
                check('check --update --promote: текст, у которого статус checked дал бы error (нет chosen), остаётся draft — с заметкой',
                      st_e['cta'] == 'draft' and 'home/hero/cta' in js_e['promote']['held']
                      and any('home/hero/cta' in n and 'на статусе checked' in n for n in js_e['notes']), (st_e['cta'], js_e['notes']))
                # --- сверка фактов не отработала: claims_check.py с кодом 2 (ошибка вызова) — не итог сверки, даже с выводом
                fake_cc, jp_nc = os.path.join(td, 'claims_check_fail.py'), os.path.join(td, 'check-no-claims.json')
                with open(fake_cc, 'w', encoding='utf-8') as f:
                    f.write("import json, sys\na = sys.argv\njson.dump({'version': '0', 'summary': {'error': 0}, 'findings': []}, "
                            "open(a[a.index('--json') + 1], 'w'))\nprint('claims_check: вход не разбирается', file=sys.stderr)\nsys.exit(2)\n")
                saved_cc = globals()['CLAIMS_CHECK']
                globals()['CLAIMS_CHECK'] = fake_cc
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        rc_nc = main(['check', src_p, '--facts', fpath, '--today', '2026-09-29', '--quiet', '--json', jp_nc])
                        rc_nc2 = main(['claims', src_p, '--facts', fpath, '--today', '2026-09-29', '--quiet'])
                finally:
                    globals()['CLAIMS_CHECK'] = saved_cc
                with open(jp_nc, encoding='utf-8') as f:
                    js_nc = json.load(f)
                check('сверка фактов не отработала (claims_check.py — код 2): check и claims — особый исход 3, причина — COPY-D-TOOL',
                      rc_nc == EXIT_NO_CLAIMS and rc_nc2 == EXIT_NO_CLAIMS and any(x['rule'] == 'COPY-D-TOOL' and '(код 2)' in x['message']
                                                                                 for x in js_nc['findings']), (rc_nc, rc_nc2))
                # --- check --all-variants --update: невыбранные варианты — только в отчёте
                d = _st_deck(); d['copy_deck']['pages'][0]['promise'] = {'from': 'home/hero/lead'}
                d['copy_deck']['pages'][0]['sections'][0]['slots'][0]['variants'].append({'id': 'b', 'text': 'Ремонт квартир с договором', 'status': 'draft'})
                out_av, jp_av = os.path.join(td, 'deck-all-variants.yaml'), os.path.join(td, 'check-all-variants.json')
                with open(src_p, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
                with contextlib.redirect_stdout(io.StringIO()):
                    main(['check', src_p, '--facts', fpath, '--today', '2026-09-29', '--all-variants', '--update', out_av, '--quiet', '--json', jp_av])
                with open(out_av, encoding='utf-8') as f:
                    dk_av = deck_root(yaml.safe_load(f))
                with open(jp_av, encoding='utf-8') as f:
                    js_av = json.load(f)
                sl_av = dk_av['pages'][0]['sections'][0]['slots'][0]
                h_av = text_hash('Ремонт квартир под ключ')
                check('check --all-variants --update: итоги невыбранного варианта — в отчёте; в файле записи только у выбранных текстов, поля checks у вариантов нет',
                      'b' in ((js_av['slots'].get('home/hero/h1') or {}).get('lint') or {}).get('variants', {})
                      and not any('checks' in v for _pg, _s, s_, _w in iter_slots(dk_av) for v in variants_of(s_))
                      and sl_av['lint']['text_hash'] == h_av and sl_av['claims']['text_hash'] == h_av
                      and any('только отчёт' in n for n in js_av['notes']),
                      (js_av['slots'].get('home/hero/h1'), sl_av.get('lint'), js_av['notes']))
        else:
            print('  (claims_check.py нет — интеграция не проверена)')
        if lint_module() is not None:
            d = _st_deck()
            sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]
            sl['variants'][0]['text'] = 'Мы предлагаем инновационные решения для вашего бизнеса'
            rep_l = Report()
            pp = run_lint(deck_root(d), ctx, rep_l, page_pass=False)
            hit = [f for f in rep_l.findings if f['where'] == 'home/hero/h1' and f['level'] == 'error']
            check('lint: штамп в заголовке — error', bool(hit), [(f['rule'], f['level']) for f in rep_l.findings if f['where'] == 'home/hero/h1'])
            if hit:
                sl['lint_allow'] = [{'rule': hit[0]['rule'], 'reason': 'слоган из брифа (тест)'}]
                rep_l2 = Report()
                pp2 = run_lint(deck_root(d), ctx, rep_l2, page_pass=False)
                gone = not any(f['rule'] == hit[0]['rule'] and f['where'] == 'home/hero/h1' for f in rep_l2.findings)
                check('lint: lint_allow снимает находку и считает её', gone and pp2['home/hero/h1']['suppressed'] >= 1, pp2.get('home/hero/h1'))
            texts = [('Мы предлагаем инновационные решения для вашего бизнеса', 'landing', 'headline'),
                     ('Смета и выезд замерщика — бесплатно в черте города', 'landing', 'cta-note'),
                     ('Более 1 000 довольных клиентов доверяют нам свои проекты!', 'landing', 'body'),
                     ('Ремонт квартир под ключ в Нижнем Новгороде — Отвес', 'meta', 'meta-title'),
                     ('Не просто сервис, а настоящий партнёр: быстро, качественно, надёжно.', 'site-page', 'subheadline'),
                     ('We help you unlock seamless workflows and supercharge growth.', 'landing', 'headline')]
            C = lint_module()
            sig = lambda r: (r['summary']['error'], r['summary']['warning'], r['summary']['info'],
                             sorted((f['id'], f['level'], f.get('fragment')) for f in r.get('findings') or []))
            with_cache = [sig(C.lint_text(t, genre=g, slot_type=st)) for t, g, st in texts]
            lint_cache(False)
            without = [sig(C.lint_text(t, genre=g, slot_type=st)) for t, g, st in texts]
            lint_cache(True)
            again = [sig(C.lint_text(t, genre=g, slot_type=st)) for t, g, st in texts]
            check('lint: кэш загрузки правил не меняет находок (6 текстов, RU и EN)', with_cache == without == again,
                  [i for i, (a, b) in enumerate(zip(with_cache, without)) if a != b])
            rep_l3 = Report()
            run_lint(deck_root(_st_deck()), ctx, rep_l3, final=True, page_pass=True)
            check('lint: --final — [PLACEHOLDER] становится error', any(f['rule'] == 'art-placeholder-marker' and f['level'] == 'error' for f in rep_l3.findings))
            d = _st_deck(); sl = d['copy_deck']['pages'][0]['sections'][0]['slots'][0]
            sl['variants'].append({'id': 'b', 'text': 'Мы предлагаем инновационные решения для вашего бизнеса', 'status': 'draft'})
            rep_l4 = Report()
            pp4 = run_lint(deck_root(d), ctx, rep_l4, all_variants=True, page_pass=False)
            check('lint --all-variants: находки альтернативы — в её итогах, выбранный текст чист',
                  pp4['home/hero/h1']['errors'] == 0 and pp4['home/hero/h1']['variants']['b']['errors'] >= 1, pp4.get('home/hero/h1'))
            d = _st_deck(); d['copy_deck']['pages'][0]['meta']['title'] = 'Ремонт квартир за 45 дней по договору — Демо'
            d['copy_deck']['pages'][0]['meta']['fact_ids'] = ['guarantee-3']
            rep_l5 = Report()
            run_lint(deck_root(d), ctx, rep_l5, page_pass=False)
            par = (rep_l5.tools.get('lint') or {}).get('parity_copy_lint') or {}
            check('lint: meta.fact_ids снимают число в мета — заметка паритета с copy_lint.py',
                  par.get('meta_fact_ids', 0) >= 1 and any('meta.fact_ids' in n for n in rep_l5.notes), (par, rep_l5.notes[:2]))
            # --- факты идут линтеру: адрес из сущности вида place — вне правила о слове на «-ая,»; copy deck линтер не меняет
            fp_place = os.path.join(td, 'facts-place.yaml')
            with open(fp_place, 'w', encoding='utf-8') as f:
                yaml.safe_dump(dict(_st_facts(), entities=[{'id': 'office', 'type': 'place', 'names': ['улица Лесная']}]), f, allow_unicode=True)
            d = _st_deck(); pg_ = d['copy_deck']['pages'][0]
            _st_checked(pg_['sections'][0]['slots'][1], 'Приезжайте: улица Лесная, дом 3, вход со двора.', status='approved')
            pg_['status'], pg_['approval'] = 'approved', {'by': 'заказчик', 'at': '2026-09-24'}
            was = _copy.deepcopy(d)
            ctx_place = Ctx(os.path.join(td, 'deck.yaml'), load_facts(fp_place), '2026-09-24')
            place_hits = lambda rep_: [f['where'] for f in rep_.findings if f['rule'] == 'ux-6-4-10']
            rep_p0, rep_p1, rep_p2 = Report(), Report(), Report()
            run_lint(deck_root(d), ctx, rep_p0)                                    # факты без сущностей мест
            run_lint(deck_root(d), ctx_place, rep_p1)                              # факты — из окружения проверки (check)
            run_lint(deck_root(d), Ctx(os.path.join(td, 'deck.yaml'), None, '2026-09-24'), rep_p2, facts_path=fp_place)   # путь — ключом (lint)
            check('lint: адрес из сущности вида place файла фактов — без находки правила о слове на «-ая,»; без такой сущности — находка',
                  place_hits(rep_p0) == ['home/hero/lead'] and not place_hits(rep_p1) and not place_hits(rep_p2)
                  and rep_p1.tools['lint']['facts'] == fp_place and rep_p0.tools['lint']['facts'] == os.path.join(td, 'facts.yaml'),
                  (place_hits(rep_p0), place_hits(rep_p1), place_hits(rep_p2), rep_p1.tools['lint'].get('facts')))
            check('lint с фактами не меняет copy deck: тексты, статусы, text_hash и запись утверждения остаются на месте', d == was,
                  [k for k in deck_root(d) if deck_root(d)[k] != deck_root(was).get(k)])
            # --- обход страницы (lint_allow) на мета: copydeck lint и линтер на copy deck дают один итог
            short = 'meta-title-too-short'

            def meta_two_ways(dd):
                rep_x = Report()
                pp_x = run_lint(deck_root(dd), ctx, rep_x, page_pass=False)
                prof_x = C.load_profiles()
                units_x, gh_x = C.parse_copy_deck(dd, C.load_vocab(), '<deck>')
                res_x = C.lint_document(C.Document('<deck>', 'yaml', units_x, '', gh_x), C.load_rules(profiles=prof_x, log=[]), prof_x, '', 'auto', '', None)
                return ((any(f['rule'] == short and f['where'] == 'home/meta/title' for f in rep_x.findings), pp_x['home/meta/title']['suppressed']),
                        (any(f['id'] == short for f in res_x.get('findings') or []), res_x['summary'].get('suppressed', 0)))
            d = _st_deck(); d['copy_deck']['pages'][0]['meta'].update(title='Демо', description='', og_title='', og_description='')
            for s_ in d['copy_deck']['pages'][0]['sections']:
                for sl_ in s_['slots']:
                    sl_['variants'][0]['text'] = ''
            d['copy_deck']['pages'][0]['promise'] = {'from': 'home/hero/lead'}
            own_0, direct_0 = meta_two_ways(d)
            d['copy_deck']['pages'][0]['lint_allow'] = [{'rule': short, 'reason': 'известный бренд'}]
            own_1, direct_1 = meta_two_ways(d)
            check('lint_allow страницы на мета: тот же обход — тот же итог в copydeck lint и в линтере на copy deck',
                  own_0 == direct_0 == (True, 0) and own_1 == direct_1 == (False, 1), (own_0, direct_0, own_1, direct_1))
        else:
            print('  (copy_lint.py не импортируется — интеграция не проверена)')
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print(f'copydeck.py {VERSION} selftest: {len(ok)} OK, {len(bad)} FAIL')
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
