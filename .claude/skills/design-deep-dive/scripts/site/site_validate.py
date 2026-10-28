#!/usr/bin/env python3
"""site_validate.py — схемы и перекрёстные ссылки контрактов сайта: бриф, план страницы, карта сайта, каталог блоков, формы.

Формат — v1, схемы kb/site/10-playbooks-contracts/schemas/: файл другой версии — ошибка схемы (SB-S01, PL-S01, SM-S01).
Коды — в выводе и в kb/site/10-playbooks-contracts/01-procedure-brief-to-pages.md §12:
  brief  (site-brief)  SB-S01 схема; SB-F01…F04 facts.yaml; SB-P01…P03 обязательные и желательные виды фактов;
         SB-R01…R04 ссылки fact:/missing:, срок стимула; SB-M00…M05 смысл text; SB-Q01…Q02 журнал вопросов; SB-T01…T03
         трафик и страницы; SB-D01…D03 умолчания брифа: аналитика, прелоадер, окно захвата; SB-A01…A03 подача
         (уровни ролей, один референс — одно место) и правило лидогенерации услуг (поля
         levels[id=L0].appropriate_for.lead_services файла ambition-levels.yaml); SB-L01…L03 правовой опросник;
         SB-B01…B02 бренд продукта по ссылке brand.ref: файл есть и проходит схему kb/common/brand.schema.yaml;
         SB-C01…C03 темы: при двух темах — переключатель и умолчание по системе (ui 11/03 §6.4); одна тёмная тема —
         с причиной themes.dark.why (без причины — warning), «по системе» без второй темы — error.
         Файл фактов или смысла по ссылке брифа, которого ещё нет (SB-F01, SB-M00): у брифа draft — info «этап не
         начат», со статуса proposed — error. SB-D01 — система аналитики не yandex-metrica и не none. SB-L03 об
         уведомлении РКН — у сайта с формой (канал-форма в conversion.channels брифа или action-слот с формой в планах
         папки слоя) или с необязательными cookie.
  plan   (page-plan)   PL-S01 схема; PL-V01 id словаря; PL-B01…B03 блок и вариант; PL-A01…A05 слоты и анатомия
         (группа.элемент, экземпляр группа-N; target.prefill — текстовый слот messenger-prefill своей секции или overlay,
         у page.cta_target — «секция.слот»); PL-F00…F07 факты: есть (и факт цели-мессенджера messenger:<fact-id>), вид,
         допуск, use.page_types (у факта шапки и подвала с ролью секции в use.section_roles не сверяется), срок
         valid.until, «популярный», минимумы доказательств (секция с пробелом и on_missing: omit-block — info);
         PL-F08 цель-контакт (warning): литерал цели — «tel:+7…», «mailto:…», адрес ссылки у kind: messenger — равен
         machine факта: значение живёт в факте, литерал — его копия (находка на значение плана); у факта цели
         messenger:<fact-id> — machine с адресом ссылки (вид messenger или url);
         PL-F09 цель-контакт не по форме (warning): у kind: tel — не литерал «tel:+<номер E.164>», у kind: messenger —
         не адрес ссылки и не messenger:<fact-id> (цель словами): ссылку по такой цели код не соберёт;
         PL-H01 один H1; PL-R01 ссылки «секция.слот»; PL-L01 длина; PL-N01 id секций из роли или блока; PL-N02
         навигация = карта (шаблон, архетип шапки, крошки, local_nav); PL-O01…O02 overlays и политики брифа;
         PL-E01…E02 события events.yaml и цели; PL-P01…P03 профиль бюджета и уровень (умолчания по типу —
         ambition-levels.yaml#defaults_by_page_type);
         PL-G01…G04 право (согласие ПД в ru, req:, оператор, cookie); PL-C01 подача — находки spec_check.py plan с их
         тяжестью (creative, владелец норм подачи; нормы облика — warning); PL-C02 переходы страниц по уровню
         (x-effect-levels подсхемы treatment, library_level_min каталога эффектов); PL-K01…K03 бриф ↔ план; PL-W01
         виджеты фасадом; PL-X01 x-gate-exception: id ворот страницы (page-gates.yaml) или ворот эффектов
         (effect-gates.yaml); PL-U01 план approved без записи утверждения approval — warning;
         PL-D01 3D: постер, призыв до 3D; PL-D02 recipe: — рецепт 3d 12-recipes есть; PL-D03 загрузка 3D по месту
         секции (ниже первого экрана — on-interaction); PL-T01…T02 формы lead-forms.yaml (PL-T02 — у формы без JS,
         то есть без success: inline, есть адрес «спасибо» thank_you_page); PL-SEO01 разметка по head-kit:
         типы страницы и подтипы её structured_data_subtypes.
  map    (site-map)    SM-S01 схема; SM-01…SM-18 перекрёстные ссылки карты; SM-19 входящие ссылки (граф); SM-20 крошки по
         глубине; SM-21 уровень шаблона ≤ сайта; SM-22 планы шаблонов; SM-23 «спасибо» у страниц с формой.
         SM-22 в папке слоя: файл плана есть, а его page.template_id — не этот шаблон — error; служебный шаблон
         (thank-you-page, legal-page, not-found-page) без плана, когда планы уже пишутся, — warning; остальные шаблоны
         без плана — info: планы — выход этапа page-plan, шаблоны идут по build_order.
         SM-01 — и цель призыва шапки: страница карты, #якорь формы или messenger:<fact-id> — факт есть в facts.yaml;
         SM-24 — у факта этой цели есть machine с адресом ссылки (warning, как PL-F08).
  blocks (blocks.yaml)       BL-* — каталог блоков; BL-14 — информационные картинки без парного элемента image-alt
                             (warning одной строкой каталога).
  forms  (lead-forms.yaml)   LF-01…LF-06 — наборы, действия, блоки, события, поля; LF-07 — профиль формы без JS
                             держится на полных перечнях: слои antispam.without_js — из layers; каждое поле
                             hidden_fields — ровно в одном перечне hidden_fields_without_js (build · server ·
                             js_only); success.without_js — не inline; цель формы и автоцели
                             events.yaml#defaults.without_js — id событий, у автоцели она названа в metrica.type.
  project DIR                бриф + facts + site-map + plans/*.yaml одной папки со всеми связями (PJ-*); страница брифа
                             без плана и без строки карты — PJ-03: error, у служебной (thank-you-page, legal-page,
                             not-found-page) — warning. PJ-04 — адреса страниц (warning): хвостовой слеш адресов карты
                             (pages[].url, collections[].url_pattern) и планов (page.url) — url_policy.trailing_slash
                             карты; у лендинга без карты — page.url у каждого плана и одна форма у адресов планов (site
                             06/02 §4.1); корень «/» формы не имеет.

Запуск:
  python3 scripts/site/site_validate.py PATH [PATH…] [--today ГГГГ-ММ-ДД] [--json [OUT]] [--quiet]
  python3 scripts/site/site_validate.py --all          # каталог блоков, наборы форм, примеры 10-playbooks-contracts/examples
  python3 scripts/site/site_validate.py --selftest     # примеры lead-services-otves и corporate-b2b-stalkon проходят, посеянные
                                                       # дефекты — каждый своим кодом и тяжестью, законные правки — без находки
Сроки фактов (valid.until) считаются от даты прогона: файлы проекта — сегодня или --today; --all — дата примеров базы
(EXAMPLES_TODAY), --today её переопределяет; самопроверка — всегда на дате примеров, так её итог не зависит от календаря.
--json OUT — находки списком JSON (level, code, where, msg) в файл; --json без файла — тот же список в stdout вместо
строк отчёта, итог — в stderr.
Схемам нужны jsonschema + referencing: без них в системном python утилита перезапускается Python окружения скилла.
Код выхода: 1 — есть error; 2 — вызов: не названы пути, у --today нет даты. Уровни: error (блокер SITE-PRE), warning
(доклад: решает заказчик, обход — с записанной причиной), info, ok.
"""
import copy
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import kbpaths  # noqa: E402
ROOT = kbpaths.kb("site")
APP = ROOT.parent


def _reexec():
    try:
        import jsonschema  # noqa: F401
        import referencing  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get('SITE_VALIDATE_NOVENV'):
        return
    for py in (Path(kbpaths.python()),):
        if py.exists():
            os.environ['SITE_VALIDATE_NOVENV'] = '1'
            os.execv(str(py), [str(py)] + sys.argv)


_reexec()
import yaml  # noqa: E402

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ImportError:  # pragma: no cover
    Draft202012Validator = None

P = {
    'vocab': ROOT / '02-site-types' / 'vocabulary.yaml',
    'blocks': ROOT / '04-blocks' / 'blocks.yaml',
    'forms': ROOT / '05-conversion-funnels' / 'lead-forms.yaml',
    'events': ROOT / '07-seo-geo-performance-analytics' / 'events.yaml',
    'budgets': ROOT / '07-seo-geo-performance-analytics' / 'budgets.yaml',
    'gates': ROOT / '07-seo-geo-performance-analytics' / 'page-gates.yaml',
    'effect_gates': kbpaths.kb('creative') / '09-ai-execution-evaluation' / 'effect-gates.yaml',
    'headkit': ROOT / '07-seo-geo-performance-analytics' / 'head-kit.yaml',
    'legal': ROOT / '08-legal-trust-a11y' / 'legal-requirements.yaml',
    'levels': kbpaths.kb('creative') / '01-creative-direction' / 'ambition-levels.yaml',
    'effects': kbpaths.kb('creative') / '06-effects-catalog' / 'effects.yaml',
    'facts_schema': kbpaths.kb('text') / '02-strategy-messaging' / 'facts.schema.yaml',
    'meaning_schema': kbpaths.kb('text') / '02-strategy-messaging' / 'meaning.schema.yaml',
    'treatment': kbpaths.kb('creative') / '09-ai-execution-evaluation' / 'treatment.schema.json',  # подсхема treatment плана
    'brand_schema': kbpaths.kb() / 'common' / 'brand.schema.yaml',
    'recipes': kbpaths.kb('3d') / '12-recipes',
}
SCHEMA = {
    ('brief', '1'): ROOT / '10-playbooks-contracts' / 'schemas' / 'site-brief.schema.json',
    ('plan', '1'): ROOT / '10-playbooks-contracts' / 'schemas' / 'page-plan.schema.json',
    ('map', '1'): ROOT / '10-playbooks-contracts' / 'schemas' / 'site-map.schema.json',
    ('blocks', '1'): ROOT / '10-playbooks-contracts' / 'schemas' / 'blocks.schema.json',
}
LEVEL = {'L0': 0, 'L1': 1, 'L2': 2}
PD_FIELDS = {'name', 'phone', 'email', 'address', 'contact-channel', 'company', 'role'}
CHROME_ROLES = {'header', 'footer', 'utility', 'legal'}
PROOF_MIN = {'logo-wall': 4, 'stat-strip': 3, 'hero-stat': 1, 'testimonial-cards': 2, 'testimonial-single': 1, 'hero-quote': 1,
             'case-cards': 2, 'case-study': 1, 'before-after': 1, 'review-aggregate': 1, 'awards-press': 1, 'credentials': 1,
             'guarantee': 1, 'founder-note': 1, 'team-grid': 1}           # site 05/02 §1.6
WIDGET_MEDIA = {'map', 'video'}
WIDGET_BLOCKS = {'booking-widget', 'chat-widget', 'location-map', 'interactive-demo'}
# служебные страницы: план у них короткий и строится по плейбуку перед их сборкой — без плана PJ-03 и SM-22 warning
SERVICE_PAGE_TYPES = {'thank-you-page', 'legal-page', 'not-found-page'}
# каналы брифа (conversion_channel словаря), где действие принимает форма на самом сайте: с ними сайт собирает ПД формой
FORM_CHANNELS = {'form', 'quiz', 'calculator', 'callback', 'chat', 'booking-widget', 'checkout'}
# текстовый слот готового первого сообщения мессенджера: на него ссылается target.prefill цели-мессенджера
PREFILL_SLOT = 'messenger-prefill'
# дата примеров базы 10-playbooks-contracts/examples: сроки их фактов (valid.until) считаются от неё в --all и самопроверке
EXAMPLES_TODAY = dt.date(2026, 9, 29)


# ─────────────────────────────────────────── отчёт ───────────────────────────────────────────
class Report:
    def __init__(self):
        self.items = []

    def add(self, level, code, where, msg):
        self.items.append((level, code, str(where), msg))

    def count(self):
        return Counter(i[0] for i in self.items)


R = Report()


def rel(p):
    try:
        return os.path.relpath(str(p), str(ROOT))
    except ValueError:
        return str(p)


def load_yaml(p):
    with open(p, encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_any(p):
    p = Path(p)
    return json.loads(p.read_text(encoding='utf-8')) if p.suffix == '.json' else load_yaml(p)


# ─────────────────────────────────────────── контекст ───────────────────────────────────────────
class Ctx:
    def __init__(self, today):
        self.today = today
        v = load_yaml(P['vocab'])
        ns = v['namespaces']
        self.vids = {k: {str(x['id']) for x in b.get('values') or []} for k, b in ns.items()}
        self.vrows = {k: {str(x['id']): x for x in b.get('values') or []} for k, b in ns.items()}
        self.blocks_doc = load_yaml(P['blocks'])
        self.B = self.blocks_doc.get('blocks') or {}
        self.forms = load_yaml(P['forms'])
        self.form_sets = {s['id']: s for s in self.forms.get('form_sets') or []}
        ev = load_yaml(P['events'])
        self.events_doc = ev
        self.events = {e['id']: e for e in ev.get('events') or []}
        self.budgets = load_yaml(P['budgets']) if P['budgets'].exists() else {}
        # ворота страницы (site, SG-…) и ворота эффектов (creative, EG-…): исключение x-gate-exception называет id любого файла
        self.gate_ids = set()
        for key, rx in (('gates', r'\bSG-[A-Z0-9]+-\d{2}\b'), ('effect_gates', r'\bEG-[A-Z0-9]+-\d{2}\b')):
            if not P[key].exists():
                continue
            g = load_yaml(P[key]) or {}
            ids = {x['id'] for k in ('gates', 'rows', 'items') for x in (g.get(k) or []) if isinstance(x, dict) and x.get('id')}
            self.gate_ids |= ids or set(re.findall(rx, P[key].read_text(encoding='utf-8')))
        hk = load_yaml(P['headkit']) if P['headkit'].exists() else {}
        self.headkit = hk.get('page_types') or {}
        lg = load_yaml(P['legal']) if P['legal'].exists() else {}
        self.req_ids = {r['id'] for r in lg.get('requirements') or []}
        lv = load_yaml(P['levels']) if P['levels'].exists() else {}
        # умолчания уровня по типу страницы — одна таблица creative; типы со статусом proposed — её раздел proposed
        self.level_defaults = {}
        dpt = lv.get('defaults_by_page_type') or {}
        for table in (dpt, dpt.get('proposed') or {}):
            for L, arr in table.items():
                if L in LEVEL and isinstance(arr, list):
                    for pt in arr:
                        self.level_defaults.setdefault(pt, L)
        # правило лидогенерации услуг: тип страницы, порог доли горячего трафика с телефонов, полосы цены, уровни
        l0 = next((l for l in lv.get('levels') or [] if l.get('id') == 'L0'), {})
        self.lead_rule = (l0.get('appropriate_for') or {}).get('lead_services') or {}
        # нижний уровень эффекта — x-effect-levels подсхемы treatment; библиотеки переходов страниц — limits каталога
        tr = load_any(P['treatment']) if P['treatment'].exists() else {}
        self.effect_min = {}
        for key, L in (('level_min_L1', 'L1'), ('level_min_L2', 'L2')):
            for ref in (tr.get('x-effect-levels') or {}).get(key) or []:
                self.effect_min[ref] = L
        eff = load_yaml(P['effects']) if P['effects'].exists() else {}
        pte = next((e for e in eff.get('effects') or [] if e.get('id') == 'page-transition'), {})
        self.transition_library_min = (pte.get('limits') or {}).get('library_level_min')
        self.recipes = ({p.stem for p in P['recipes'].glob('[0-9][0-9]-*.md') if not p.stem.startswith('00-')}
                        if P['recipes'].is_dir() else set())
        self._sc, self._sc_error, self.sc_ctx = None, None, None
        fs = load_yaml(P['facts_schema']) if P['facts_schema'].exists() else {}
        self.fact_kinds = set(((fs.get('$defs') or {}).get('kind') or {}).get('enum') or []) or set((fs.get('x-kinds') or {}).keys())
        self.validators = {}
        self.registry = None
        if Draft202012Validator is not None:
            res = []
            for key in ('facts_schema', 'meaning_schema', 'treatment', 'brand_schema'):
                if P[key].exists():
                    d = load_any(P[key])
                    res.append((d['$id'], Resource.from_contents(d, default_specification=DRAFT202012)))
            for sp in SCHEMA.values():
                if sp.exists():
                    d = load_any(sp)
                    res.append((d['$id'], Resource.from_contents(d, default_specification=DRAFT202012)))
            self.registry = Registry().with_resources(res)

    def validator(self, kind, version):
        key = (kind, version)
        if key not in self.validators:
            sp = SCHEMA.get(key)
            if sp is None or not sp.exists() or Draft202012Validator is None:
                self.validators[key] = None
            else:
                self.validators[key] = Draft202012Validator(load_any(sp), registry=self.registry)
        return self.validators[key]

    def vok(self, ns, val):
        return val is not None and str(val) in self.vids.get(ns, set())

    def spec_check(self):
        """Модуль spec_check.py creative (проверка подачи плана) и его контекст; None — модуль не загрузился."""
        if self._sc is None and self._sc_error is None:
            try:
                kbpaths.use('creative')
                import spec_check
                self.sc_ctx = spec_check.Ctx()
                self._sc = spec_check
            except Exception as ex:  # noqa: BLE001 — причину покажет находка PL-C01
                self._sc_error = f'{type(ex).__name__}: {ex}'
        return self._sc


def schema_check(ctx, kind, version, doc, where, code):
    v = ctx.validator(kind, version)
    if v is None:
        R.add('warning', code, where, f'схема {kind} {version} не проверена (нет jsonschema или файла схемы)')
        return False
    n = 0
    for e in sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        n += 1
        R.add('error', code, f"{where}:/{'/'.join(map(str, e.absolute_path))}", 'схема: ' + e.message[:260])
    if n == 0:
        R.add('ok', code, where, f'схема {kind} v{version}: валиден')
    return n == 0


# ─────────────────────────────────────────── факты ───────────────────────────────────────────
def admitted(f, today):
    """Допуск факта на страницу: таблица допуска site 08/02 §1.2 и фильтр публикации фактов text."""
    why = []
    ver = (f.get('verification') or {}).get('status')
    perm = (f.get('permission') or {}).get('status')
    der = (f.get('source') or {}).get('derivation', 'direct')
    until = (f.get('valid') or {}).get('until')
    review = ((f.get('legal') or {}).get('review') or {}).get('status')
    if ver not in ('verified', 'stated'):
        why.append(f'verification {ver}')
    if perm not in ('granted', 'not-required'):
        why.append(f'permission {perm}')
    if der == 'inferred':
        why.append('derivation inferred')
    if until and str(until) < today.isoformat()[:len(str(until))]:
        why.append(f'valid.until {until} прошёл')
    if review in ('required', 'rejected'):
        why.append(f'legal.review {review}')
    if f.get('kind') in ('testimonial', 'client', 'person', 'case') and perm == 'not-required':
        why.append(f'вид {f.get("kind")} требует письменного разрешения (site 08/02 §1.2)')
    return (not why), why


def load_facts(path):
    d = load_yaml(path)
    facts = {f['id']: f for f in d.get('facts') or []}
    for f in list(facts.values()):
        for a in f.get('aliases') or []:
            facts.setdefault(a, f)
    missing = {m['id']: m for m in d.get('missing') or []}
    return d, facts, missing


# Цель-контакт: значение телефона, почты и мессенджера живёт в факте — machine (facts.schema.yaml $defs/machine).
# Литерал цели плана — его копия, цель messenger:<fact-id> — ссылка на факт с адресом; расхождение — PL-F08 (у карты —
# SM-24). Цель телефона или мессенджера в другой форме (словами) — PL-F09: ссылку по ней код не соберёт.
LINK_MACHINE = ('messenger', 'url')                      # виды machine с адресом ссылки: канал, профиль, мессенджер


def contact_literal(tgt):
    """Вид литерала цели-контакта: tel («tel:+<номер E.164>»), email («mailto:…»), messenger (адрес ссылки у kind:
    messenger); цель словами, якорь, маршрут и внешняя ссылка — None."""
    val = str(tgt.get('value') or '')
    if re.match(r'^tel:\+[1-9]\d{6,14}$', val):
        return 'tel'
    if re.match(r'^mailto:\S+@', val):
        return 'email'
    return 'messenger' if tgt.get('kind') == 'messenger' and re.match(r'^https?://\S+$', val) else None


def contact_gap(tgt):
    """Цель телефона или мессенджера не в форме, по которой код соберёт ссылку: у kind: tel — не литерал номера, у
    kind: messenger — не адрес ссылки и не messenger:<fact-id>."""
    kind, val = tgt.get('kind'), str(tgt.get('value') or '')
    return kind == 'tel' and contact_literal(tgt) != 'tel' or \
        kind == 'messenger' and not (val.startswith('messenger:') or contact_literal(tgt))


def contact_hrefs(facts):
    """Адреса ссылок-контактов по machine фактов {id: факт}: {tel: {«tel:<номер E.164>»}, email: {«mailto:<почта>»},
    messenger: {адрес ссылки мессенджера, профиля или канала}}."""
    href = {'telephone': ('tel', 'tel:'), 'email': ('email', 'mailto:'), **{t: ('messenger', '') for t in LINK_MACHINE}}
    out = {'tel': set(), 'email': set(), 'messenger': set()}
    for f in (facts or {}).values():
        m = f.get('machine') if isinstance(f, dict) else None
        if isinstance(m, dict) and m.get('value') and m.get('type') in href:
            kind, scheme = href[m['type']]
            out[kind].add(scheme + str(m['value']))
    return out


def link_fact_gap(fid, facts):
    """Цель messenger:<fact-id>: факт есть, а machine с адресом ссылки (LINK_MACHINE) у него нет — сообщение; иначе
    None (нет факта — PL-F01 и SM-01)."""
    f = (facts or {}).get(fid)
    m = f.get('machine') if isinstance(f, dict) else None
    if not isinstance(f, dict) or isinstance(m, dict) and m.get('type') in LINK_MACHINE:
        return None
    return (f'target messenger:{fid}: у факта нет machine вида messenger — адреса ссылки коду взять неоткуда; значение — '
            'подсказка claims_check.py lint-facts')


# ─────────────────────────────────────────── бриф ───────────────────────────────────────────
def check_brief(path, ctx, facts_override=None, plan_forms=False):
    """plan_forms — в планах папки слоя есть action-слот с формой: вместе с каналами-формами брифа (FORM_CHANNELS)
    это признак «у сайта есть формы» для вопроса об уведомлении РКН (SB-L03)."""
    w0 = rel(path)
    b = load_yaml(path)
    ver = str(b.get('version', ''))
    if ver != '1':
        R.add('error', 'SB-S01', w0, f'version {ver or "—"}: формат брифа — v1 (10-playbooks-contracts/schemas/site-brief.schema.json)')
        return b, None, None, None
    schema_check(ctx, 'brief', ver, b, w0, 'SB-S01')
    bdir = Path(path).resolve().parent
    slug = (b.get('project') or {}).get('slug')
    proof = b.get('proof') or {}
    # бриф выходит из своего этапа черновиком раньше файлов фактов и смысла: у draft ссылка на файл, которого ещё нет, —
    # ход работы; со статуса proposed — разрыв
    draft = (b.get('project') or {}).get('status') == 'draft'
    facts_doc = facts = missing = None
    if facts_override is not None:
        facts_doc = facts_override
        facts = {f['id']: f for f in facts_doc.get('facts') or []}
        missing = {m['id']: m for m in facts_doc.get('missing') or []}
    elif proof.get('facts_ref'):
        fp = (bdir / proof['facts_ref']).resolve()
        if not fp.exists():
            R.add('info' if draft else 'error', 'SB-F01', w0, f'proof.facts_ref не найден: {proof["facts_ref"]}'
                                                             + (' — этап фактов не начат (бриф draft)' if draft else ''))
        else:
            facts_doc, facts, missing = load_facts(fp)
    if facts_doc is not None:
        if ctx.registry is not None:
            try:
                fs = load_any(P['facts_schema'])
                v = Draft202012Validator(fs, registry=ctx.registry)
                for e in list(v.iter_errors(facts_doc))[:10]:
                    R.add('error', 'SB-F02', w0, f'facts.yaml не проходит схему text: /{"/".join(map(str, e.absolute_path))}: {e.message[:200]}')
            except Exception as ex:  # схема text могла измениться
                R.add('warning', 'SB-F02', w0, f'схема facts text не применена: {ex}')
        if facts_doc.get('site') != slug:
            R.add('error', 'SB-F03', w0, f'facts.site «{facts_doc.get("site")}» ≠ project.slug «{slug}»')
        jur = (b.get('constraints') or {}).get('jurisdiction') or ['ru']
        if facts_doc.get('jurisdiction', 'ru') != jur[0]:
            R.add('error', 'SB-F04', w0, f'facts.jurisdiction «{facts_doc.get("jurisdiction")}» ≠ основной юрисдикции брифа «{jur[0]}»')
        for k in proof.get('required_kinds') or []:
            pub = [f['id'] for f in facts_doc.get('facts') or [] if f.get('kind') == k and admitted(f, ctx.today)[0]]
            blk = [m['id'] for m in facts_doc.get('missing') or [] if m.get('kind') == k and m.get('blocking')]
            if not pub and not blk:
                R.add('error', 'SB-P01', w0, f'обязательный вид «{k}»: нет допущенного факта и нет missing с blocking: true (сначала анкета proof-intake.md)')
            elif not pub:
                R.add('warning', 'SB-P02', w0, f'обязательный вид «{k}»: только блокирующий пробел {blk} — страница не публикуется до ответа')
        for k in proof.get('wanted_kinds') or []:
            if not [f for f in facts_doc.get('facts') or [] if f.get('kind') == k and admitted(f, ctx.today)[0]]:
                R.add('warning', 'SB-P03', w0, f'желательный вид «{k}»: допущенных фактов нет — блок не строится (не выдумывается)')

        def cref(ref, where):
            if not isinstance(ref, str) or ':' not in ref:
                return
            ns_, rid = ref.split(':', 1)
            if ns_ == 'fact' and rid not in facts:
                R.add('error', 'SB-R01', w0, f'{where}: {ref} нет в facts.yaml')
            if ns_ == 'missing' and rid not in missing:
                R.add('error', 'SB-R02', w0, f'{where}: {ref} нет в facts.yaml missing[]')
        off = b.get('offer') or {}
        for key in ('price_refs', 'terms_refs'):
            for r in off.get(key) or []:
                cref(r, f'/offer/{key}')
        for key in ('incentive_ref', 'deadline_ref'):
            if off.get(key):
                cref(off[key], f'/offer/{key}')
        conv = b.get('conversion') or {}
        if conv.get('response_time_ref'):
            cref(conv['response_time_ref'], '/conversion/response_time_ref')
        geo = (b.get('business') or {}).get('geography') or {}
        if geo.get('address_ref'):
            cref(geo['address_ref'], '/business/geography/address_ref')
        dl = off.get('deadline_ref')
        if dl and dl.startswith('fact:'):
            f = facts.get(dl[5:])
            if f is not None and not (f.get('valid') or {}).get('until'):
                R.add('error', 'SB-R03', w0, f'/offer/deadline_ref: у {dl} нет valid.until — срок акции без реальной даты запрещён')
        for r in off.get('price_refs') or []:
            f = facts.get(r[5:]) if r.startswith('fact:') else None
            if f is not None and f.get('kind') not in ('price', 'promo', 'offer-terms'):
                R.add('warning', 'SB-R04', w0, f'/offer/price_refs: {r} вида «{f.get("kind")}», ожидалась цена')
    mean = b.get('meaning')
    if mean is None and b.get('meaning_ref'):
        mp = (bdir / b['meaning_ref']).resolve()
        if not mp.exists():
            R.add('info' if draft else 'error', 'SB-M00', w0, f'meaning_ref не найден: {b["meaning_ref"]}'
                                                             + (' — этап смысла не начат (бриф draft)' if draft else ''))
        else:
            mean = load_yaml(mp)
    if mean is not None:
        if mean.get('site') and mean.get('site') != slug:
            R.add('error', 'SB-M02', w0, f'meaning.site «{mean.get("site")}» ≠ project.slug «{slug}»')
        if mean.get('proof_ref') and proof.get('facts_ref') and (bdir / mean['proof_ref']).resolve() != (bdir / proof['facts_ref']).resolve():
            R.add('error', 'SB-M03', w0, 'meaning.proof_ref ≠ proof.facts_ref (одна ссылка на facts.yaml)')
        la = {(x['lang'], x['role']) for x in b.get('languages') or []}
        lb = {(x['lang'], x['role']) for x in mean.get('languages') or []}
        if lb and la != lb:
            R.add('error', 'SB-M04', w0, f'языки брифа {sorted(la)} ≠ meaning.languages {sorted(lb)}')
        rr = {r['id'] for r in mean.get('risk_reversal') or []}
        for r in (b.get('offer') or {}).get('risk_reversal_refs') or []:
            if r not in rr:
                R.add('error', 'SB-M05', w0, f'/offer/risk_reversal_refs: «{r}» нет в meaning.risk_reversal')
    qids = [q['id'] for q in b.get('questions') or []]
    if len(qids) != len(set(qids)):
        R.add('error', 'SB-Q01', w0, 'id вопросов в questions[] повторяются')
    if mean is not None:
        qs = set(qids)

        def walk(node, path=''):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == 'question_id' and isinstance(v, str) and v not in qs:
                        R.add('error', 'SB-Q02', w0, f'/meaning{path}: допущение ссылается на вопрос «{v}», которого нет в questions[]')
                    walk(v, f'{path}/{k}')
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f'{path}/{i}')
        walk(mean)
    srcs = (b.get('traffic') or {}).get('sources') or []
    share = sum(s.get('share', 0) or 0 for s in srcs)
    if share > 1.0001:
        R.add('error', 'SB-T01', w0, f'сумма долей трафика {share:.2f} > 1')
    pages = b.get('pages') or {}
    pids = {p['id'] for p in pages.get('list') or []}
    if pages.get('mode') == 'listed':
        for s in srcs:
            if s.get('entry_page') and s['entry_page'] not in pids:
                R.add('error', 'SB-T02', w0, f'traffic: entry_page «{s["entry_page"]}» нет в pages.list')
        for x in (b.get('ambition') or {}).get('by_page') or []:
            if x['page'] not in pids:
                R.add('error', 'SB-T03', w0, f'ambition.by_page: «{x["page"]}» нет в pages.list')
    pol = b.get('policies') or {}
    amb = b.get('ambition') or {}
    lvl = amb.get('level')
    if (b.get('analytics') or {}).get('system') not in (None, 'yandex-metrica', 'none'):   # none — аналитики нет вовсе
        R.add('warning', 'SB-D01', w0, 'аналитика не Яндекс Метрика: причина — в брифе; зарубежный сервис при юрисдикции ru — '
                                       'уведомление РКН о трансграничной передаче и согласие на cookie (req:LR-RU-08, LR-RU-10)')
    if pol.get('preloader') == 'on' and not (lvl == 'L2' and (b.get('site_type') == 'campaign-site' or b.get('primary_page_type') == 'landing-campaign')):
        R.add('warning', 'SB-D02', w0, 'прелоадер вне L2-кампании: норма уровней — только кампания L2 (ambition-levels.yaml, '
                                       'forbidden); включить иначе — решение заказчика с причиной в policies.rationale')
    for r in amb.get('by_section_role') or []:
        if lvl and LEVEL.get(r.get('level'), 0) > LEVEL.get(lvl, 0):
            R.add('error', 'SB-A01', w0, f'ambition.by_section_role[{r.get("role")}] {r.get("level")} выше ambition.level {lvl}')
    places = defaultdict(set)
    for r in b.get('references') or []:
        if r.get('applies_to'):
            places[r.get('ref') or r.get('url')].add(r['applies_to'])
    for k, pl in places.items():
        if len(pl) > 1:
            R.add('warning', 'SB-A02', w0, f'референс {k} применён к {sorted(pl)}: норма — один референс, одно место '
                                           '(creative 01/01 §6.4); два места — по слову заказчика, с причиной')
    lead = ctx.lead_rule
    if lead.get('page_type') and b.get('primary_page_type') == lead['page_type'] and amb.get('source', 'default') == 'default':
        hot_mob = sum((s.get('share') or 0) for s in srcs if s.get('temperature') == 'hot' and s.get('device') == 'mobile')
        band = (b.get('decision_context') or {}).get('price_band')
        smin, bands = lead.get('hot_mobile_share_min'), lead.get('price_bands') or []
        rule = 'правило лидогенерации услуг (ambition-levels.yaml, levels[L0].appropriate_for.lead_services)'
        if not any(s.get('share') for s in srcs):
            R.add('info', 'SB-A03', w0, f'{rule}: долей трафика нет — уровень {lead.get("no_data")} и вопрос в журнал брифа')
        elif smin is not None and hot_mob >= smin and band in bands:
            if lvl != 'L0':
                R.add('warning', 'SB-A03', w0, f'{rule}: горячий мобильный трафик {hot_mob:.0%} ≥ {smin:.0%} и price_band {band} → '
                                                f'умолчание L0, а не {lvl}')
        elif smin is not None and lvl == 'L0' and lead.get('otherwise') and lead['otherwise'] != 'L0':
            R.add('warning', 'SB-A03', w0, f'{rule}: горячий мобильный трафик {hot_mob:.0%} (порог {smin:.0%}), price_band {band} '
                                            f'(полосы {bands}) → умолчание {lead["otherwise"]}, а не L0')
    # бренд продукта — ссылкой на файл бренда слоя дизайна
    brand = b.get('brand') or {}
    if brand.get('ref'):
        bp = (bdir / brand['ref']).resolve()
        if not bp.is_file():
            R.add('error', 'SB-B01', w0, f'brand.ref не найден: {brand["ref"]} (бренд продукта — ../../design/brand.yaml от брифа)')
        elif ctx.registry is not None and P['brand_schema'].exists():
            try:
                v = Draft202012Validator(load_any(P['brand_schema']), registry=ctx.registry)
                for e in sorted(v.iter_errors(load_yaml(bp)), key=lambda e: list(e.absolute_path))[:10]:
                    R.add('error', 'SB-B02', w0, f'{brand["ref"]} не проходит схему brand: /{"/".join(map(str, e.absolute_path))}: {e.message[:200]}')
            except Exception as ex:  # noqa: BLE001 — битый YAML бренда или сменившаяся схема
                R.add('error', 'SB-B02', w0, f'{brand["ref"]}: схема brand не применена — {ex}')
    # темы: светлая по умолчанию; две темы — переключатель на странице и умолчание по системе (ui 11/03 §6.4). Одна тёмная
    # тема — решение брифа, а не разрыв контракта: с причиной она проходит, без причины — доклад заказчику
    th = b.get('themes') or {}
    if th:
        dark = th.get('dark') or {}
        two = bool(dark.get('needed'))
        dflt = th.get('default', 'light')
        if two and th.get('switcher') is not True:
            R.add('error', 'SB-C01', w0, 'две темы — переключатель темы на странице обязателен: themes.switcher: true (ui 11/03 §6.4)')
        if not two and dflt == 'system':
            R.add('error', 'SB-C02', w0, 'themes.default system без второй темы: по системе — только при двух темах '
                                         '(themes.dark.needed: true с причиной)')
        if not two and dflt == 'dark':
            if str(dark.get('why') or '').strip():
                R.add('info', 'SB-C02', w0, 'одна тёмная тема — решение брифа с причиной в themes.dark.why')
            else:
                R.add('warning', 'SB-C02', w0, 'одна тёмная тема без причины: причина — в themes.dark.why (отрасль, аудитория, слово '
                                               'заказчика; ui 11/03 §6.4); themes.dark.needed остаётся false — он о второй теме')
        if two and dflt != 'system':
            R.add('warning', 'SB-C03', w0, f'две темы, умолчание {dflt}: по умолчанию — по системе (system); {dflt} — только по '
                                           'отраслевой причине в themes.dark.why (ui 11/03 §6.4)')
        if not two and th.get('switcher'):
            R.add('warning', 'SB-C03', w0, 'переключатель темы без второй темы')
    li = (b.get('constraints') or {}).get('legal_intake') or {}
    jur = (b.get('constraints') or {}).get('jurisdiction') or ['ru']
    if li:
        if li.get('leads_storage') == 'abroad' and 'ru' in jur:
            R.add('error', 'SB-L01', w0, 'заявки хранятся за рубежом, а юрисдикция ru: первичная запись ПД — в РФ (req:LR-RU-07)')
        if li.get('optional_cookies') and pol.get('cookie_banner') == 'none':
            R.add('error', 'SB-L02', w0, 'есть необязательные cookie, а policies.cookie_banner: none (req:LR-RU-10, LR-EU-01)')
        # уведомление РКН — вопрос сайта, который собирает данные: формой или необязательными cookie; без них предмета нет
        forms = plan_forms or bool(set((b.get('conversion') or {}).get('channels') or []) & FORM_CHANNELS)
        if li.get('rkn_registry') in ('no', 'unknown') and (forms or li.get('optional_cookies')):
            R.add('warning', 'SB-L03', w0, f'уведомление РКН: {li.get("rkn_registry")} — до запуска '
                                           f'{"формы" if forms else "необязательных cookie"} (req:LR-RU-09); вопрос заказчику')
        abroad = [t['service'] for t in li.get('third_party') or [] if t.get('location') == 'abroad']
        if abroad and 'ru' in jur:
            R.add('info', 'SB-L03', w0, f'сервисы за рубежом {abroad}: трансграничная передача (req:LR-RU-08) — page.legal.cross_border планов')
    elif (b.get('project') or {}).get('status') in ('proposed', 'approved'):
        R.add('warning', 'SB-L03', w0, 'нет constraints.legal_intake: вопросы правового опросника (site 08/01 §6, шаг 1) не заданы')
    if pol.get('capture_popup') in ('engaged', 'on'):
        paid = [s['source'] for s in srcs if s.get('source') in ('paid-search', 'paid-social', 'paid-display', 'retargeting')]
        if paid:
            R.add('warning', 'SB-D03', w0, f'окно захвата {pol["capture_popup"]} при платном трафике {paid}: не на посадочной под рекламу (site 05/01 §11)')
    return b, facts_doc, facts, missing


# ─────────────────────────────────────────── каталог блоков ───────────────────────────────────────────
def anatomy_index(block):
    idx, groups = {}, {}
    for s in block.get('slots') or []:
        idx[s['id']] = dict(s, _group=None)
    for g in block.get('groups') or []:
        groups[g['id']] = g
        for s in g.get('slots') or []:
            idx[g['id'] + '.' + s['id']] = dict(s, _group=g['id'])
    return idx, groups


def check_blocks(ctx, path=P['blocks']):
    w = rel(path)
    doc = load_yaml(path)
    schema_check(ctx, 'blocks', '1', doc, w, 'BL-S01')
    B = doc.get('blocks') or {}
    for bid, r in ctx.vrows['block'].items():
        if r.get('status', 'active') not in ('measurement-only', 'deprecated', 'out-of-scope') and bid not in B:
            R.add('error', 'BL-01', w, f'блок словаря {bid} нет в каталоге')
    complete = 0
    no_alt = []
    for bid, b in B.items():
        wb = f'{w}#{bid}'
        if bid not in ctx.vids['block']:
            R.add('error', 'BL-02', wb, 'id блока нет в словаре')
            continue
        vr = ctx.vrows['block'][bid]
        if b.get('family') != vr.get('family'):
            R.add('error', 'BL-03', wb, f"family {b.get('family')} ≠ словарь {vr.get('family')}")
        for r in b.get('serves') or []:
            if r not in ctx.vids['section_role']:
                R.add('error', 'BL-04', wb, f'serves: роль {r} нет в словаре')
        idx, groups = anatomy_index(b)
        seen = set()
        for s in b.get('slots') or []:
            if s['id'] in seen:
                R.add('error', 'BL-05', wb, f"повтор id элемента {s['id']}")
            seen.add(s['id'])
        for g in groups:
            if g in seen:
                R.add('error', 'BL-05', wb, f'id группы {g} совпадает с элементом')
        variants = {v['id'] for v in b.get('variants') or []}
        if len([v for v in b.get('variants') or [] if v.get('default')]) != 1:
            R.add('warning', 'BL-06', wb, 'вариантов по умолчанию не 1')
        for v in b.get('variants') or []:
            for a in (v.get('adds') or []) + (v.get('drops') or []):
                if a not in idx:
                    R.add('error', 'BL-07', wb, f"вариант {v['id']}: adds/drops {a} нет в анатомии")
        has_data = False
        for ref, s in idx.items():
            sl = s['slot']
            if sl not in ctx.vids['slot']:
                R.add('error', 'BL-08', wb, f'элемент {ref}: слот {sl} нет в словаре')
                continue
            kind = ctx.vrows['slot'][sl].get('kind')
            if 'heading' in s and kind != 'text':
                R.add('error', 'BL-09', wb, f'элемент {ref}: heading у слота вида {kind}')
            for k in s.get('fact_kinds') or []:
                if ctx.fact_kinds and k not in ctx.fact_kinds:
                    R.add('error', 'BL-10', wb, f'элемент {ref}: вид факта {k} нет в facts.schema.yaml')
            if kind == 'data':
                has_data = True
            for vv in s.get('variants') or []:
                if vv not in variants:
                    R.add('error', 'BL-11', wb, f'элемент {ref}: вариант {vv} не объявлен')
        if b.get('requires_facts') and not has_data:
            R.add('error', 'BL-12', wb, 'requires_facts, но нет data-элемента')
        # информационная картинка (media_role: informational; видео — не картинка) и её alt: парный элемент image-alt —
        # в той же группе, у элемента блока — на уровне блока
        alt_scopes = {s['_group'] for s in idx.values() if s['slot'] == 'image-alt'}
        no_alt += [f'{bid}.{ref}' for ref, s in idx.items() if s.get('media_role') == 'informational' and s['slot'] != 'video'
                   and ctx.vrows['slot'].get(s['slot'], {}).get('kind') == 'media' and s['_group'] not in alt_scopes]
        if all(b.get(k) for k in ('slots', 'variants', 'mobile', 'html', 'refs')):
            complete += 1
    n = max(len(B), 1)
    R.add('ok' if complete / n >= 0.8 else 'error', 'BL-13', w, f'полнота анатомии: {complete} из {len(B)} блоков')
    if no_alt:
        R.add('warning', 'BL-14', w, f'информационные картинки без парного элемента image-alt ({len(no_alt)}): '
                                     f'{", ".join(no_alt)} — тексту alt в плане нет места')
    return B


HIDDEN_BY = ('build', 'server', 'js_only')               # кто ставит скрытое поле формы без JS: hidden_fields_without_js


def without_js_gaps(defaults, events_doc):
    """Профиль формы без JS держится на полных перечнях (LF-07) → [(что, [не так])]: слои антиспама — из layers;
    скрытые поля — каждое поле hidden_fields ровно в одном перечне build · server · js_only; успех without_js — не
    inline (адреса успеха у него нет); цель формы form_success и автоцели counter_goals — id событий events.yaml, у
    автоцели она названа в metrica.type события."""
    asp = defaults.get('antispam') or {}
    hid = defaults.get('hidden_fields_without_js') or {}
    out = [('antispam.without_js — слоя нет в layers',
            [x for x in asp.get('without_js') or [] if x not in (asp.get('layers') or [])])]
    full = defaults.get('hidden_fields') or []
    out += [(f'hidden_fields_without_js.{k} — поля нет в hidden_fields', [x for x in hid.get(k) or [] if x not in full])
            for k in HIDDEN_BY]
    placed = Counter(x for k in HIDDEN_BY for x in hid.get(k) or [])
    out.append(('hidden_fields_without_js — поле в двух перечнях', sorted(x for x, n in placed.items() if n > 1)))
    out.append((f"hidden_fields_without_js — поля hidden_fields нет ни в одном перечне ({', '.join(HIDDEN_BY)})",
                [x for x in full if x not in placed]))
    out.append(('success.without_js — без JS адреса успеха нет',
                [x for x in [(defaults.get('success') or {}).get('without_js')] if x == 'inline']))
    ev = events_doc or {}
    events = {e.get('id'): e for e in ev.get('events') or [] if isinstance(e, dict)}
    wj = (ev.get('defaults') or {}).get('without_js') or {}
    goals = wj.get('counter_goals') or []
    out.append(('events.yaml defaults.without_js.form_success — не id события',
                [str(x) for x in [wj.get('form_success')] if x not in events]))
    out.append(('events.yaml defaults.without_js.counter_goals — не id события', [x for x in goals if x not in events]))
    out.append(('events.yaml defaults.without_js.counter_goals — у события нет автоцели в metrica.type',
                [x for x in goals if x in events and 'автоцел' not in str((events[x].get('metrica') or {}).get('type'))]))
    return [(w, b) for w, b in out if b]


def check_forms(ctx, path=P['forms']):
    w = rel(path)
    d = load_yaml(path)
    ids = [s['id'] for s in d.get('form_sets') or []]
    if len(ids) != len(set(ids)):
        R.add('error', 'LF-01', w, 'id наборов повторяются')
    fields = set((d.get('fields') or {}).keys())
    for s in d.get('form_sets') or []:
        ws = f"{w}#{s['id']}"
        if s.get('action') and not ctx.vok('action', s['action']):
            R.add('error', 'LF-02', ws, f"action {s['action']} нет в словаре")
        for bl in s.get('blocks') or []:
            if bl not in ctx.B:
                R.add('error', 'LF-03', ws, f'блок {bl} нет в blocks.yaml')
        for f in s.get('fields') or []:
            if isinstance(f, dict) and f.get('field') and f['field'] not in fields:
                R.add('error', 'LF-05', ws, f"поле {f['field']} нет в библиотеке fields")
        for pt in s.get('page_types') or []:
            if not ctx.vok('page_type', pt):
                R.add('error', 'LF-06', ws, f'page_type {pt} нет в словаре')
    for k, e in ((d.get('defaults') or {}).get('events') or {}).items():
        if e is None:
            continue
        if not str(e).startswith('event:') or str(e)[6:] not in ctx.events:
            R.add('error', 'LF-04', w, f'defaults.events.{k}: {e} — не id events.yaml (event:<id>)')
    for what, bad in without_js_gaps(d.get('defaults') or {}, ctx.events_doc):
        R.add('error', 'LF-07', w, f'{what}: {", ".join(bad)}')
    for pt, pl in (d.get('placement_defaults') or {}).items():
        if not ctx.vok('page_type', pt):
            R.add('error', 'LF-06', w, f'placement_defaults: page_type {pt} нет в словаре')
        for sid in [pl.get('primary')] + list(pl.get('alt') or []):
            if sid and sid not in ctx.form_sets:
                R.add('error', 'LF-01', w, f'placement_defaults.{pt}: набор {sid} не существует')
    R.add('ok', 'LF-00', w, f'наборов {len(ids)}, полей {len(fields)}')


# ─────────────────────────────────────────── план страницы ───────────────────────────────────────────
def plan_version(p):
    v = str(p.get('page_plan_version', ''))
    return '1' if v in ('1', '1.0') else v


def check_plan(path, ctx, brief=None, facts_pack=None, sitemap=None):
    w0 = rel(path)
    p = load_yaml(path)
    ver = plan_version(p)
    if ver != '1':
        R.add('error', 'PL-S01', w0, f'page_plan_version {ver or "—"}: формат плана — v1 (10-playbooks-contracts/schemas/page-plan.schema.json)')
        return p
    schema_check(ctx, 'plan', ver, p, w0, 'PL-S01')
    base = Path(path).resolve().parent
    refs = p.get('refs') or {}
    facts = missing = None
    if facts_pack is not None:
        _, facts, missing = facts_pack
    elif refs.get('facts'):
        fp = (base / refs['facts']).resolve()
        if fp.exists():
            fd, facts, missing = load_facts(fp)
            if fd.get('site') != p.get('site'):
                R.add('warning', 'PL-F00', w0, f"site плана {p.get('site')} ≠ site фактов {fd.get('site')}")
        else:
            R.add('error', 'PL-F00', w0, f'facts не найден: {refs["facts"]}')
    pg = p.get('page') or {}
    pt = pg.get('page_type')

    def vcheck(ns, val, where):
        if val is not None and not ctx.vok(ns, val):
            R.add('error', 'PL-V01', where, f'{ns} {val} нет в словаре')

    hrefs, literals, worded = contact_hrefs(facts), defaultdict(list), defaultdict(list)

    def tcheck(where, tgt, texts, scope):
        """Цель-мессенджер: value messenger:<fact-id> — факт или названный пробел есть в facts.yaml (PL-F01), у факта —
        machine с адресом ссылки (PL-F08); литерал цели-контакта (contact_literal), которого нет среди machine фактов,
        — в literals (PL-F08 одной находкой на значение); цель телефона или мессенджера не по форме (contact_gap) — в
        worded (PL-F09 так же); prefill — текстовый слот готового сообщения (PREFILL_SLOT) среди texts {ссылка: слот}
        своей секции, overlay или страницы."""
        if not isinstance(tgt, dict):
            return
        val = str(tgt.get('value') or '')
        if contact_gap(tgt):
            worded[val].append(where)
        elif tgt.get('kind') == 'messenger' and val.startswith('messenger:') and facts is not None:
            if val[10:] not in facts and val[10:] not in (missing or {}):
                R.add('error', 'PL-F01', where, f'target {val}: факта {val[10:]} нет в facts.yaml')
            elif link_fact_gap(val[10:], facts):
                R.add('warning', 'PL-F08', where, link_fact_gap(val[10:], facts))
        elif facts is not None and contact_literal(tgt) and val not in hrefs[contact_literal(tgt)]:
            literals[val].append(where)
        pf = tgt.get('prefill')
        if pf is not None and pf not in texts:
            R.add('error', 'PL-A03', where, f'target.prefill → {pf}: текстового слота нет {scope}')
        elif pf is not None and texts[pf].get('slot') != PREFILL_SLOT:
            R.add('error', 'PL-A03', where, f"target.prefill → {pf}: слот {texts[pf].get('slot')}, нужен {PREFILL_SLOT}")
    vcheck('page_type', pt, w0 + ':page')
    if pt in ctx.vrows['page_type'] and ctx.vrows['page_type'][pt].get('status') == 'proposed':
        R.add('info', 'PL-V01', w0 + ':page', f'page_type {pt} — proposed (словарь v1)')
    vcheck('action', pg.get('primary_action'), w0 + ':page')
    if pg.get('primary_action') in ctx.vrows['action'] and ctx.vrows['action'][pg['primary_action']].get('level') != 'macro':
        R.add('error', 'PL-V01', w0 + ':page', 'primary_action не macro')
    for a in pg.get('secondary_actions') or []:
        vcheck('action', a, w0 + ':page.secondary_actions')
    vcheck('awareness', pg.get('awareness'), w0 + ':page')
    for j in pg.get('jurisdiction') or []:
        vcheck('jurisdiction', j, w0 + ':page')
    ms = pg.get('macrostructure')
    vcheck('macrostructure', ms, w0 + ':page')
    if ms in ctx.vrows['macrostructure'] and ctx.vrows['macrostructure'][ms].get('layout_family') != pg.get('macrostructure_family'):
        R.add('error', 'PL-V01', w0 + ':page', f"macrostructure_family {pg.get('macrostructure_family')} ≠ layout_family {ctx.vrows['macrostructure'][ms].get('layout_family')}")
    for m in pg.get('macrostructure_alternatives') or []:
        vcheck('macrostructure', m, w0 + ':page.alternatives')
    for t in pg.get('traffic') or []:
        vcheck('traffic_source', t.get('traffic_source'), w0 + ':page.traffic')
    # профиль бюджета и уровень
    bp = pg.get('budget_profile') or ''
    lvl = pg.get('ambition_level')
    if bp and not re.match(r'^[a-z0-9-]+@L[0-2]$', bp):
        R.add('error', 'PL-P01', w0 + ':page', f'budget_profile {bp}: формат <page_type>@L<n> (budgets.yaml)')
    elif bp:
        if not bp.startswith(str(pt) + '@'):
            R.add('warning', 'PL-P01', w0 + ':page', f'budget_profile {bp} не начинается с page_type {pt}')
        if not bp.endswith('@' + str(lvl)):
            R.add('warning', 'PL-P01', w0 + ':page', f'budget_profile {bp} ≠ ambition_level {lvl}')
    dflt = ctx.level_defaults.get(pt)
    if dflt and lvl and LEVEL[lvl] > LEVEL[dflt]:
        R.add('info', 'PL-P02', w0 + ':page', f'уровень {lvl} выше умолчания {dflt} для {pt} (ambition-levels.yaml#defaults_by_page_type) '
                                              '— нужна причина в брифе')
    if brief is not None:
        blvl = (brief.get('ambition') or {}).get('level')
        if blvl and lvl and LEVEL[lvl] > LEVEL[blvl]:
            R.add('error', 'PL-P03', w0 + ':page', f'уровень страницы {lvl} выше уровня сайта {blvl}: не выше ambition.level брифа '
                                                   '(creative 01/03 §5.2)')
    # навигация и шаблон
    nav = pg.get('navigation') or {}
    tpl = None
    if sitemap is not None:
        tpl_id = pg.get('template_id')
        tmap = {t['id']: t for t in sitemap.get('templates') or []}
        if tpl_id and tpl_id not in tmap:
            R.add('error', 'PL-N02', w0 + ':page', f'template_id {tpl_id} нет в site-map')
        tpl = tmap.get(tpl_id)
        arch = ((sitemap.get('chrome') or {}).get('header') or {}).get('archetype')
        if nav.get('header') == 'site' and nav.get('archetype') and arch and nav['archetype'] != arch:
            R.add('error', 'PL-N02', w0 + ':page', f"navigation.archetype {nav['archetype']} ≠ site-map.chrome.header.archetype {arch}")
        if tpl is not None:
            if tpl.get('page_type') != pt:
                R.add('error', 'PL-N02', w0 + ':page', f"page_type {pt} ≠ шаблона {tpl.get('page_type')}")
            if tpl.get('level') and lvl and LEVEL[lvl] > LEVEL[tpl['level']]:
                R.add('error', 'PL-P03', w0 + ':page', f"уровень {lvl} выше уровня шаблона {tpl['level']}")
            if nav.get('breadcrumbs') is not None and bool(nav['breadcrumbs']) != bool(tpl.get('breadcrumbs')):
                R.add('warning', 'PL-N02', w0 + ':page', f"navigation.breadcrumbs {nav['breadcrumbs']} ≠ шаблона {tpl.get('breadcrumbs')}")
            # локальная навигация раздела — копия шаблона: вид и липкость; без поля в плане она не дойдёт до макета
            ln, tn = ((x.get('kind'), bool(x.get('sticky'))) if isinstance(x, dict) and x else None
                      for x in (nav.get('local_nav'), tpl.get('local_nav')))
            if ln != tn:
                show = ['нет' if x is None else f"{x[0]}{', sticky' if x[1] else ''}" for x in (ln, tn)]
                R.add('warning', 'PL-N02', w0 + ':page', f'navigation.local_nav ({show[0]}) ≠ шаблона ({show[1]}) — '
                                                         'site-map.templates[].local_nav')
    # секции
    h1 = 0
    sec_ids, sec_slot_ids = set(), {}
    nflow = 0
    has_pd_form = False
    used_events = set()
    # первый экран — первая секция потока и секции из first_screen.must_show («секция.слот»)
    first_screen = {str(r).partition('.')[0] for r in (pg.get('first_screen') or {}).get('must_show') or []}
    first_screen |= set([s.get('id') for s in (p.get('sections') or []) if s.get('role') not in CHROME_ROLES][:1])
    for s in p.get('sections') or []:
        sid = s.get('id')
        w = f'{w0}#{sid}'
        if sid in sec_ids:
            R.add('error', 'PL-A01', w, 'повтор id секции')
        sec_ids.add(sid)
        role, bid = s.get('role'), s.get('block')
        vcheck('section_role', role, w)
        if role == 'other':
            R.add('error', 'PL-V01', w, 'role other запрещён в плане')
        if role not in CHROME_ROLES:
            nflow += 1
        stem = re.sub(r'-(\d+|[a-z]+)$', '', str(sid))
        if not (str(sid) in (role, bid) or str(sid).startswith(f'{role}-') or str(sid).startswith(f'{bid}-')):
            R.add('error', 'PL-N01', w, f'id секции «{sid}» не из роли ({role}) или блока ({bid}) — SITE-PRE-15')
        if bid not in ctx.B:
            R.add('error', 'PL-B01', w, f'блока {bid} нет в blocks.yaml')
            continue
        b = ctx.B[bid]
        if b.get('status') in ('deprecated', 'measurement-only'):
            R.add('error', 'PL-B01', w, f'блок {bid} со статусом {b.get("status")}')
        if role not in (b.get('serves') or []):
            R.add('warning', 'PL-B03', w, f'роль {role} не среди serves блока {bid} {b.get("serves")}')
        var = s.get('variant')
        vmap = {v['id']: v for v in b.get('variants') or []}
        if var and var not in vmap:
            R.add('error', 'PL-B02', w, f'вариант {var} не объявлен у блока {bid}')
        idx, groups = anatomy_index(b)
        slots = s.get('slots') or {}
        ids = {}
        used = Counter()
        ginst = defaultdict(set)
        for kind in ('text', 'media', '3d', 'data', 'action'):
            for sl in slots.get(kind) or []:
                lid = sl['id']
                if lid in ids:
                    R.add('error', 'PL-A01', w, f'повтор id слота {lid}')
                ids[lid] = (kind, sl)
                vs = sl.get('slot')
                if not ctx.vok('slot', vs):
                    R.add('error', 'PL-A02', w, f'слот {lid}: {vs} нет в словаре')
                    continue
                vk = ctx.vrows['slot'][vs].get('kind')
                if vk != kind:
                    R.add('error', 'PL-A02', w, f'слот {lid}: {vs} вида {vk} лежит в slots.{kind}')
                anat = sl.get('anatomy') or (None if kind == 'data' else lid)
                el = idx.get(anat) if anat else None
                if el is None and kind == 'data' and not sl.get('anatomy'):
                    pass
                elif el is None:
                    R.add('error', 'PL-A03', w, f'слот {lid}: элемента анатомии «{anat}» нет у блока {bid}')
                else:
                    if el['slot'] != vs and not (kind == 'data' and ctx.vrows['slot'][el['slot']].get('kind') == 'data'):
                        R.add('error', 'PL-A03', w, f"слот {lid}: {vs} ≠ слот элемента {anat} ({el['slot']})")
                    used[anat] += 1
                    if el['_group']:
                        g = sl.get('group')
                        if not g:
                            R.add('error', 'PL-A04', w, f'слот {lid}: элемент группы {anat} без group (экземпляр «группа-N»)')
                        elif not re.match(rf'^{re.escape(el["_group"])}-\d+$', g):
                            R.add('error', 'PL-A04', w, f'слот {lid}: group {g} не экземпляр группы {el["_group"]}')
                        else:
                            ginst[el['_group']].add(g)
                if kind == 'text' and sl.get('heading') == 'h1':
                    h1 += 1
                if kind == 'action':
                    vcheck('action', sl.get('action'), w + '.' + lid)
                    if sl.get('event'):
                        used_events.add(sl['event'])
                    fm = sl.get('form') or {}
                    if fm:
                        check_form_slot(ctx, w + '.' + lid, sl, fm, pg)
                        if form_collects_pd(ctx, fm):
                            has_pd_form = True
                    if (bid in WIDGET_BLOCKS or vs == 'form' and bid == 'booking-widget') and sl.get('load') == 'eager':
                        R.add('warning', 'PL-W01', w + '.' + lid, 'виджет грузится eager: фасадом on-visible | on-interaction (site 07/03 §5.2)')
                if kind == 'media' and vs in WIDGET_MEDIA and sl.get('load') == 'eager' and not sl.get('lcp_candidate'):
                    R.add('warning', 'PL-W01', w + '.' + lid, f'{vs}: виджет eager — фасадом on-visible | on-interaction (site 07/03 §5.2)')
        sec_slot_ids[sid] = ids
        for anat, n in used.items():
            el = idx[anat]
            if el['_group'] is None and el.get('max') is not None and n > el['max']:
                R.add('error', 'PL-A05', w, f'элемент {anat} использован {n} раз, max {el["max"]}')
        req = {a for a, el in idx.items() if el['_group'] is None and el.get('required') is True}
        if var and var in vmap:
            req |= set(vmap[var].get('adds') or [])
            req -= set(vmap[var].get('drops') or [])
        for a in sorted(req):
            if used[a] == 0:
                R.add('warning', 'PL-A05', w, f'обязательный элемент {a} блока {bid} не заполнен')
        for gid, g in groups.items():
            n = len(ginst.get(gid, set()))
            if g.get('max') and n > g['max']:
                R.add('error', 'PL-A05', w, f'группа {gid}: {n} экземпляров > max {g["max"]}')
            if n and n < g.get('min', 0):
                R.add('warning', 'PL-A05', w, f'группа {gid}: {n} экземпляров < min {g["min"]}')
        # факты
        nfacts = 0
        for lid, (kind, sl) in ids.items():
            if kind == 'data':
                ref = sl.get('fact', '')
                pre, _, fid = ref.partition(':')
                allowed = ctx.vrows['slot'].get(sl.get('slot'), {}).get('fact_kinds') or []
                for bnd in sl.get('binds') or []:
                    if bnd not in ids:
                        R.add('error', 'PL-F01', w, f'{lid}: binds → {bnd} нет в секции')
                if facts is None:
                    continue
                if pre == 'fact':
                    f = facts.get(fid)
                    if f is None:
                        R.add('error', 'PL-F01', w, f'{lid}: fact:{fid} нет в facts.yaml')
                        continue
                    nfacts += 1
                    if allowed and f.get('kind') not in allowed:
                        R.add('error', 'PL-F01', w, f"{lid}: вид факта {f.get('kind')} не входит в {sl.get('slot')} {allowed}")
                    ok, why = admitted(f, ctx.today)
                    if not ok:
                        R.add('error', 'PL-F03', w, f'{lid}: fact:{fid} не допущен на страницу — {"; ".join(why)} (site 08/02 §1.2)')
                    use = f.get('use') or {}
                    # факт общей шапки или подвала стоит на каждой странице сайта: когда роль секции названа в его
                    # use.section_roles, use.page_types со страницей не сверяется
                    chrome = role in ('header', 'footer') and role in (use.get('section_roles') or [])
                    if use.get('page_types') and pt not in use['page_types'] and not chrome:
                        R.add('warning', 'PL-F04', w, f'{lid}: fact:{fid}.use.page_types {use["page_types"]} без {pt}')
                    for bnd in sl.get('binds') or []:
                        if bnd in ids and ids[bnd][0] == 'text' and use.get('slot_types') and ids[bnd][1].get('slot') not in use['slot_types']:
                            R.add('info', 'PL-F04', w, f'{lid}: fact:{fid}.use.slot_types без {ids[bnd][1].get("slot")}')
                elif pre == 'missing':
                    m = missing.get(fid)
                    if m is None:
                        R.add('error', 'PL-F02', w, f'{lid}: missing:{fid} нет в facts.yaml missing')
                        continue
                    if not sl.get('on_missing'):
                        R.add('warning', 'PL-F02', w, f'{lid}: missing без on_missing')
                    if m.get('blocking'):
                        R.add('info', 'PL-F02', w, f'{lid}: блокирующий пробел missing:{fid} — страница не публикуется до ответа')
            if kind == 'action' and sl.get('label') and sl['label'] not in ids:
                R.add('error', 'PL-A03', w, f"{lid}: label → {sl['label']} нет в секции")
            if kind == 'action':
                tcheck(w + '.' + lid, sl.get('target'), {i: x for i, (k, x) in ids.items() if k == 'text'}, 'в секции')
            if kind == 'media' and sl.get('alt') and sl['alt'] != 'decorative' and sl['alt'] not in ids:
                R.add('error', 'PL-A03', w, f"{lid}: alt → {sl['alt']} нет в секции")
            if kind == '3d':
                if sl.get('poster') not in ids:
                    R.add('error', 'PL-D01', w, f'{lid}: poster → {sl.get("poster")} нет в секции')
                if sl.get('cta_before_3d') is False:
                    R.add('error', 'PL-D01', w, f'{lid}: призыв ждёт 3D (CTA и форма работают до загрузки 3D)')
                rec = sl.get('recipe')
                if rec and ctx.recipes and rec.partition(':')[2] not in ctx.recipes:
                    R.add('error', 'PL-D02', w, f'{lid}: {rec} — такого рецепта нет в 3d 12-recipes')
                load = sl.get('load')
                if sid not in first_screen:
                    if load == 'on-visible':
                        R.add('warning', 'PL-D03', w, f'{lid}: 3D ниже первого экрана по видимости — риск длинных кадров прокрутки '
                                                      '(ворота EG-PERF-01); по умолчанию — on-interaction')
                    elif load == 'after-lcp':
                        R.add('warning', 'PL-D03', w, f'{lid}: 3D ниже первого экрана грузится сразу после LCP — по намерению: '
                                                      'on-interaction (3d 12/15)')
                elif load is None:
                    R.add('info', 'PL-D03', w, f'{lid}: 3D первого экрана без load — умолчание on-interaction; после LCP и load — '
                                               'after-lcp')
        mn = PROOF_MIN.get(bid)
        if mn and facts is not None and nfacts < mn:
            # пробел missing: с on_missing: omit-block — секция по плану снимается, пока факта нет: минимум ей не в упрёк
            omit = [lid for lid, (k, sl) in ids.items() if k == 'data' and str(sl.get('fact', '')).startswith('missing:')
                    and sl.get('on_missing') == 'omit-block']
            if omit:
                R.add('info', 'PL-F07', w, f'блок {bid}: допущенных фактов {nfacts} < минимума {mn} (site 05/02 §1.6) — секция '
                                           f'снимается до факта (on_missing: omit-block у {", ".join(omit)})')
            else:
                R.add('warning', 'PL-F07', w, f'блок {bid}: допущенных фактов {nfacts} < минимума {mn} (site 05/02 §1.6) — снять блок или сменить вариант')
        if bid == 'pricing-cards':
            badges = [lid for lid, (k, sl) in ids.items() if k == 'text' and sl.get('slot') == 'badge']
            share_facts = [lid for lid, (k, sl) in ids.items() if k == 'data' and facts and sl.get('fact', '').startswith('fact:')
                           and (facts.get(sl['fact'][5:]) or {}).get('kind') in ('metric', 'research')]
            if badges and not share_facts:
                R.add('error', 'PL-F06', w, 'метка «популярный» без факта доли продаж или выбора (site 05/02 §2.5)')
        exp = s.get('expires') or {}
        if exp and facts is not None and exp.get('fact', '').startswith('fact:'):
            f = facts.get(exp['fact'][5:])
            if f is None:
                R.add('error', 'PL-F05', w, f"expires.fact {exp['fact']} нет в facts.yaml")
            elif not (f.get('valid') or {}).get('until'):
                R.add('error', 'PL-F05', w, f"expires.fact {exp['fact']} без valid.until")
            elif str(f['valid']['until']) < ctx.today.isoformat()[:len(str(f['valid']['until']))]:
                R.add('error', 'PL-F05', w, f"срок {f['valid']['until']} прошёл — секция должна быть снята ({exp.get('then')})")
        if bid in ('promo-offer', 'announcement-bar') and facts is not None and not exp:
            R.add('warning', 'PL-F05', w, f'{bid} без expires (факт со сроком акции: после срока — скрыть; site 05/02 §4.3)')
        for e in s.get('events') or []:
            if e.get('target') not in ids and e.get('target') != sid:
                R.add('error', 'PL-E01', w, f"событие → {e.get('target')} нет в секции")
            if e.get('action'):
                vcheck('action', e['action'], w + '.events')
            if e.get('event'):
                used_events.add(e['event'])
    check_treatment(path, p, ctx, w0)
    tcheck(w0 + ':page.cta_target', pg.get('cta_target'),
           {f'{sid}.{i}': x for sid, ids in sec_slot_ids.items() for i, (k, x) in ids.items() if k == 'text'},
           'на странице («секция.слот»)')
    if h1 != 1:
        R.add('error', 'PL-H01', w0, f'H1 на странице: {h1} (нужен ровно 1)')
    ln = pg.get('length') or {}
    if ln and not (ln.get('sections_min', 0) <= nflow <= ln.get('sections_max', 99)):
        R.add('warning', 'PL-L01', w0, f"секций потока {nflow} вне length {ln.get('sections_min')}–{ln.get('sections_max')}")
    fs = pg.get('first_screen') or {}
    refs2 = list(fs.get('must_show') or []) + [x for mm in fs.get('message_match') or [] for x in mm.get('slots') or []]
    refs2 += [x for v in (fs.get('variant_map') or {}).get('variants') or [] for x in v.get('slots') or []]
    if (pg.get('seo') or {}).get('h1'):
        refs2.append(pg['seo']['h1'])
    for r in refs2:
        a, _, b2 = r.partition('.')
        if a not in sec_slot_ids or b2 not in sec_slot_ids[a]:
            R.add('error', 'PL-R01', w0 + ':page', f'ссылка «{r}» (секция.слот) не найдена')
    # overlays и политики брифа
    pol = (brief or {}).get('policies') or {}
    for ov in p.get('overlays') or []:
        if ov.get('block') not in ctx.B:
            R.add('error', 'PL-O01', w0 + ':overlays', f"блока {ov.get('block')} нет")
        otexts = {x.get('id'): x for x in (ov.get('slots') or {}).get('text') or []}
        for a in (ov.get('slots') or {}).get('action') or []:
            tcheck(f"{w0}:overlays.{ov.get('id')}.{a.get('id')}", a.get('target'), otexts, 'в overlay')
        if brief is not None and ov.get('state') == 'on':
            if ov.get('block') == 'capture-popup' and pol.get('capture_popup', 'off') == 'off':
                R.add('error', 'PL-O02', w0 + ':overlays', 'окно захвата включено, а в брифе policies.capture_popup: off — '
                                                           'включить в брифе с policies.rationale и согласием заказчика или выключить в плане')
            if ov.get('block') == 'chat-widget' and pol.get('chat_widget', 'off') == 'off':
                R.add('error', 'PL-O02', w0 + ':overlays', 'чат включён, а в брифе policies.chat_widget: off')
    # литерал цели-контакта — копия machine факта: значения, которого у фактов нет, — одна находка на план; цель
    # телефона или мессенджера не по форме — так же
    def seen(places):
        return ', '.join(x.removeprefix(w0).lstrip(':') for x in places[:2]) + (f' и ещё {len(places) - 2}' if len(places) > 2 else '')
    for val, places in sorted(literals.items()):
        R.add('warning', 'PL-F08', w0, f'цель {val} ({seen(places)}): такого значения нет у machine фактов — телефон, '
                                       'почта и мессенджер живут в факте (machine), литерал цели — его копия; '
                                       'значение — подсказка claims_check.py lint-facts')
    for val, places in sorted(worded.items()):
        R.add('warning', 'PL-F09', w0, f'цель «{val}» ({seen(places)}) — не адрес ссылки: у телефона — литерал '
                                       '«tel:+<номер E.164>», копия machine факта, у мессенджера — адрес ссылки или '
                                       'messenger:<fact-id>; ссылку по такой цели код не соберёт')
    # события
    for e in used_events:
        if not str(e).startswith('event:') or str(e)[6:] not in ctx.events:
            R.add('error', 'PL-E01', w0, f'событие {e} — не id events.yaml')
    goals = (pg.get('analytics') or {}).get('goals') or []
    macro_by_action = defaultdict(set)
    for eid, e in ctx.events.items():
        if e.get('action'):
            macro_by_action[e['action']].add(eid)
    for g in goals:
        if g not in macro_by_action:
            R.add('warning', 'PL-E02', w0, f'цель {g}: нет события-действия в events.yaml')
        elif used_events and not ({f'event:{x}' for x in macro_by_action[g]} & used_events):
            R.add('warning', 'PL-E02', w0, f'цель {g}: в плане нет события {sorted(macro_by_action[g])}')
    # право
    legal = pg.get('legal') or {}
    jur = pg.get('jurisdiction') or []
    if has_pd_form and legal.get('pd_consent') == 'not-collected':
        R.add('error', 'PL-G01', w0, 'на странице форма со сбором ПД, а page.legal.pd_consent: not-collected')
    for r in legal.get('requirements') or []:
        if r[4:] not in ctx.req_ids:
            R.add('error', 'PL-G02', w0, f'{r} нет в legal-requirements.yaml')
    if legal.get('operator_ref') and facts is not None:
        oid = legal['operator_ref'].partition(':')[2]
        f = facts.get(oid) or (missing or {}).get(oid)
        if f is None:
            R.add('error', 'PL-G03', w0, f"operator_ref {legal['operator_ref']} нет в facts.yaml")
        elif f.get('kind') not in (None, 'company'):
            R.add('error', 'PL-G03', w0, f"operator_ref: вид {f.get('kind')}, нужен company")
    if 'eu' in jur and legal.get('analytics_before_consent'):
        R.add('error', 'PL-G04', w0, 'eu: счётчики до согласия запрещены (req:LR-EU-01)')
    if legal.get('cookie_mode') == 'none' and brief is not None and ((brief.get('constraints') or {}).get('legal_intake') or {}).get('optional_cookies'):
        R.add('error', 'PL-G04', w0, 'cookie_mode none, а в брифе есть необязательные cookie (req:LR-RU-10)')
    # x-gate-exception
    for x in pg.get('x-gate-exception') or []:
        if ctx.gate_ids and x.get('id') not in ctx.gate_ids:
            R.add('error', 'PL-X01', w0, f"x-gate-exception {x.get('id')} нет ни в page-gates.yaml (ворота страницы), "
                                         'ни в effect-gates.yaml (ворота эффектов)')
    # SEO
    hk = ctx.headkit.get(pt) or {}
    sd = (pg.get('seo') or {}).get('structured_data') or []
    if hk and sd:
        # подтипы, допустимые вместо типа страницы, — structured_data_subtypes head-kit {тип: [подтипы]}
        sub = {x for v in (hk.get('structured_data_subtypes') or {}).values() for x in v or []}
        extra = [x for x in sd if x not in (hk.get('structured_data') or []) and x not in sub
                 and x not in ('Organization', 'WebSite', 'BreadcrumbList')]
        if extra:
            R.add('warning', 'PL-SEO01', w0, f'структурированные данные {extra} вне head-kit для {pt} {hk.get("structured_data")}'
                                             + (f', подтипы {sorted(sub)}' if sub else ''))
    if hk and (pg.get('seo') or {}).get('indexable') is not None and (pg['seo']['indexable'] != hk.get('indexable')):
        R.add('info', 'PL-SEO01', w0, f"indexable {pg['seo']['indexable']} ≠ умолчания head-kit {hk.get('indexable')} для {pt}")
    # бриф ↔ план
    if brief is not None:
        bp_pages = {x['id']: x for x in (brief.get('pages') or {}).get('list') or []}
        bpage = bp_pages.get(pg.get('id'))
        want_action = (bpage or {}).get('action') or (brief.get('conversion') or {}).get('action')
        if want_action and pg.get('primary_action') and pg['primary_action'] != want_action and not (pg.get('template') or tpl is not None):
            R.add('warning', 'PL-K03', w0, f"primary_action {pg['primary_action']} ≠ брифа {want_action}")
        if bpage and bpage.get('main_sources'):
            ab = (pg.get('awareness_basis') or {}).get('main_sources') or []
            if ab and set(ab) != set(bpage['main_sources']):
                R.add('warning', 'PL-K01', w0, f"awareness_basis.main_sources {ab} ≠ брифа {bpage['main_sources']}")
        srcs = (brief.get('traffic') or {}).get('sources') or []
        entry = [s['source'] for s in srcs if s.get('entry_page') == pg.get('id')]
        have = {t.get('traffic_source') for t in pg.get('traffic') or []}
        for s in entry:
            if s not in have:
                R.add('warning', 'PL-K02', w0, f'источник {s} ведёт на страницу (entry_page), а в page.traffic его нет')
        ml = (((brief.get('meaning') or {}).get('awareness') or {}).get('level'))
        levels = {ml} | {x.get('level') for x in (((brief.get('meaning') or {}).get('awareness') or {}).get('by_source') or [])}
        if ml and pg.get('awareness') and pg['awareness'] not in levels:
            R.add('warning', 'PL-K01', w0, f"awareness {pg['awareness']} нет среди уровней meaning.awareness {sorted(x for x in levels if x)}")
    if p.get('status') == 'approved' and not p.get('approval'):
        R.add('warning', 'PL-U01', w0, 'план approved без записи утверждения approval {by, date}: кто и когда утвердил'
                                       + (' (запись лежит расширением x-approval — её место в approval)' if p.get('x-approval') else ''))
    R.add('info', 'PL-00', w0, f"секций {len(p.get('sections') or [])}, потока {nflow}; версия плана {ver}")
    return p


def check_treatment(path, p, ctx, w0):
    """Подача плана — владелец норм creative. PL-C01: находки `spec_check.py plan` (уровень секции, конверсия, пики,
    акценты, фирменные приёмы, референсы, петли, плавная прокрутка); форму плана с подсхемой treatment проверяет PL-S01.
    PL-C02: уровни эффектов секций и переходов страниц — x-effect-levels подсхемы treatment, библиотеки переходов —
    library_level_min эффекта page-transition каталога (нативный кросс-документный переход — с L1)."""
    pg = p.get('page') or {}
    lvl = pg.get('ambition_level')
    ptr = pg.get('treatment') or {}
    secs = [s for s in p.get('sections') or [] if s.get('treatment')]
    if not (ptr or secs):
        return
    sc = ctx.spec_check()
    if sc is None:
        R.add('warning', 'PL-C01', w0, f'подача не проверена: spec_check.py не загрузился ({ctx._sc_error})')
    else:
        rep = sc.Report()
        try:
            sc.cmd_plan(ctx.sc_ctx, rep, str(path))
        except Exception as ex:  # noqa: BLE001 — падение соседней утилиты не останавливает проверку плана
            R.add('warning', 'PL-C01', w0, f'подача не проверена: spec_check.py plan — {type(ex).__name__}: {ex}')
        else:
            for sev, code, where, msg in rep.items:
                if code in ('TR-S', 'TR-11'):   # схема плана — PL-S01; уровень эффекта — PL-C02 по x-effect-levels
                    continue
                R.add(sev, 'PL-C01', w0 + (':page' if where in ('page', '') else f'#{where}'), f'{code}: {msg}')
    for s in secs:
        t = s['treatment'] if isinstance(s['treatment'], dict) else {}
        tl = t.get('level') or lvl
        for e in t.get('effects') or []:
            need = ctx.effect_min.get(e.get('ref')) if isinstance(e, dict) else None
            if need and tl in LEVEL and LEVEL[tl] < LEVEL[need]:
                R.add('error', 'PL-C02', f"{w0}#{s.get('id')}", f"{e.get('ref')} — с уровня {need}, секция {tl} (x-effect-levels treatment)")
    mode = (ptr.get('motion_system') or {}).get('page_transitions') if isinstance(ptr, dict) else None
    need = {'view-transitions': ctx.effect_min.get('effect:page-transition'),
            'library': ctx.transition_library_min, 'custom': ctx.transition_library_min}.get(mode)
    if need in LEVEL and lvl in LEVEL and LEVEL[lvl] < LEVEL[need]:
        R.add('error', 'PL-C02', w0 + ':page', f'переходы страниц {mode} — с уровня {need}, страница {lvl} (effects.yaml#page-transition)')


def form_collects_pd(ctx, fm):
    ref = fm.get('ref') or ''
    sid = ref.partition('#')[2]
    s = ctx.form_sets.get(sid)
    if s is None:
        return True
    return any(isinstance(f, dict) and f.get('field') in PD_FIELDS for f in s.get('fields') or [])


def check_form_slot(ctx, where, sl, fm, pg):
    ref = fm.get('ref')
    if ref:
        sid = ref.partition('#')[2]
        s = ctx.form_sets.get(sid)
        if s is None:
            R.add('error', 'PL-T01', where, f'form.ref {ref}: набора нет в lead-forms.yaml')
        elif s.get('action') and sl.get('action') and s['action'] != sl['action']:
            R.add('warning', 'PL-T01', where, f"form.ref {sid} для действия {s['action']}, а слот — {sl['action']}")
    else:
        R.add('warning', 'PL-T01', where, 'форма без form.ref (набор lead-forms.yaml)')
    jur = pg.get('jurisdiction') or []
    if 'ru' in jur and fm.get('consent') in ('link-only', 'none') and form_collects_pd(ctx, fm):
        R.add('error', 'PL-G01', where, f"согласие {fm.get('consent')} при сборе ПД в ru — нужна отдельная неотмеченная галочка (req:LR-RU-01, 02)")
    # профиль формы решает план: success: inline — остров формы; иначе форма без JS — 303 на адрес thank_you_page
    if fm.get('success') == 'thank-you-page' and not fm.get('thank_you_page'):
        R.add('warning', 'PL-T02', where, 'success: thank-you-page без thank_you_page')
    elif not fm.get('success') and not fm.get('thank_you_page'):
        R.add('warning', 'PL-T02', where, 'форма без success и без thank_you_page: без JS успех формы — 303 на адрес '
                                          '«спасибо» плана (lead-forms.yaml#defaults.success); остров формы — success: inline')


# ─────────────────────────────────────────── карта сайта ───────────────────────────────────────────
def check_map(path, ctx, brief=None, plans=None, plan_tpl=None, facts_pack=None):
    """plans и plan_tpl — планы папки слоя: шаблон → файл плана и файл плана → его page.template_id; без них карта
    проверяется одна (пример карты без планов). facts_pack — факты брифа (документ, факты, пробелы): по ним сверяется
    цель-мессенджер призыва шапки; без фактов цель не сверяется."""
    w0 = rel(path)
    m = load_yaml(path)
    ver = str(m.get('site_map_version', ''))
    if ver not in ('1', '1.0'):
        R.add('error', 'SM-S01', w0, f'site_map_version {ver or "—"}: формат карты — v1 (10-playbooks-contracts/schemas/site-map.schema.json)')
        return m
    schema_check(ctx, 'map', '1', m, w0, 'SM-S01')
    pages = {p['id']: p for p in m.get('pages') or []}
    tmpl = {t['id']: t for t in m.get('templates') or []}
    colls = {c['id']: c for c in m.get('collections') or []}
    chrome = m.get('chrome') or {}
    link = m.get('linking') or {}
    util = m.get('utility_pages') or {}

    def need_page(pid, where, code):
        if pid not in pages:
            R.add('error', code, f'{w0}:{where}', f'страница {pid} нет в pages[]')
    hdr = chrome.get('header') or {}
    for it in hdr.get('items') or []:
        need_page(it.get('page'), 'chrome.header.items', 'SM-01')
        for g in it.get('groups') or []:
            for pid in g.get('pages') or []:
                if pid not in pages and pid not in tmpl:
                    R.add('error', 'SM-01', f'{w0}:chrome.header.groups', f'{pid} нет ни в pages, ни в templates')
            if g.get('from_collection') and g['from_collection'] not in colls:
                R.add('error', 'SM-01', f'{w0}:chrome.header.groups', f"коллекции {g['from_collection']} нет")
    cta = (hdr.get('utilities') or {}).get('cta') or {}
    tgt = str(cta.get('target') or '')
    # цель призыва шапки: страница карты, #якорь формы или канал-мессенджер messenger:<fact-id> — факт или названный пробел
    if tgt.startswith('messenger:'):
        if facts_pack is not None and tgt[10:] not in facts_pack[1] and tgt[10:] not in (facts_pack[2] or {}):
            R.add('error', 'SM-01', f'{w0}:chrome.header.utilities.cta', f'target {tgt}: факта {tgt[10:]} нет в facts.yaml')
        elif facts_pack is not None and link_fact_gap(tgt[10:], facts_pack[1]):
            R.add('warning', 'SM-24', f'{w0}:chrome.header.utilities.cta', link_fact_gap(tgt[10:], facts_pack[1]))
    elif tgt and not tgt.startswith('#'):
        need_page(tgt, 'chrome.header.utilities.cta', 'SM-01')
    if cta.get('action') and not ctx.vok('action', cta['action']):
        R.add('error', 'SM-01', f'{w0}:chrome.header.utilities.cta', f"action {cta['action']} нет в словаре")
    ftr = chrome.get('footer') or {}
    for g in ftr.get('groups') or []:
        for pid in g.get('pages') or []:
            if pid not in pages:
                R.add('error', 'SM-02', f'{w0}:chrome.footer.groups', f'страница {pid} нет в pages[]')
    for pid in ftr.get('legal') or []:
        need_page(pid, 'chrome.footer.legal', 'SM-03')
    for pid, p in pages.items():
        if p.get('template') not in tmpl:
            R.add('error', 'SM-04', f'{w0}:pages.{pid}', f"шаблон {p.get('template')} нет в templates[]")
        elif tmpl[p['template']].get('page_type') != p.get('page_type'):
            R.add('error', 'SM-14', f'{w0}:pages.{pid}', f"page_type {p.get('page_type')} ≠ шаблона {tmpl[p['template']].get('page_type')}")
        if p.get('parent') and p['parent'] not in pages:
            R.add('error', 'SM-05', f'{w0}:pages.{pid}', f"parent {p['parent']} нет в pages[]")
        if not ctx.vok('page_type', p.get('page_type')):
            R.add('error', 'SM-13', f'{w0}:pages.{pid}', f"page_type {p.get('page_type')} нет в словаре")
        if p.get('action') and not ctx.vok('action', p['action']):
            R.add('error', 'SM-13', f'{w0}:pages.{pid}', f"action {p['action']} нет в словаре")
        for s in p.get('main_sources') or []:
            if not ctx.vok('traffic_source', s):
                R.add('error', 'SM-13', f'{w0}:pages.{pid}', f'traffic_source {s} нет в словаре')
    for cid, c in colls.items():
        if c.get('template') not in tmpl:
            R.add('error', 'SM-06', f'{w0}:collections.{cid}', f"шаблон {c.get('template')} нет")
        if c.get('hub_page') and c['hub_page'] not in pages:
            R.add('error', 'SM-06', f'{w0}:collections.{cid}', f"hub_page {c['hub_page']} нет в pages[]")
    for tid, t in tmpl.items():
        if t.get('instances') == 'collection':
            if t.get('collection') not in colls:
                R.add('error', 'SM-06', f'{w0}:templates.{tid}', f"instances: collection без коллекции ({t.get('collection')})")
        if t.get('related') and t['related'] not in {r['id'] for r in link.get('related_rules') or []}:
            R.add('error', 'SM-08', f'{w0}:templates.{tid}', f"related {t['related']} нет в linking.related_rules")
        if not ctx.vok('page_type', t.get('page_type')):
            R.add('error', 'SM-13', f'{w0}:templates.{tid}', f"page_type {t.get('page_type')} нет в словаре")
    for r in link.get('related_rules') or []:
        if r.get('from') not in tmpl:
            R.add('error', 'SM-07', f"{w0}:linking.related_rules.{r.get('id')}", f"from {r.get('from')} не шаблон")
        if r.get('to') not in tmpl and r.get('to') not in colls:
            R.add('error', 'SM-07', f"{w0}:linking.related_rules.{r.get('id')}", f"to {r.get('to')} не шаблон и не коллекция")
        if r.get('block') and r['block'] not in ctx.B:
            R.add('error', 'SM-07', f"{w0}:linking.related_rules.{r.get('id')}", f"блок {r['block']} нет в blocks.yaml")
    for h in link.get('hubs') or []:
        need_page(h.get('page'), 'linking.hubs', 'SM-09')
        if h.get('lists') not in colls and h.get('lists') not in tmpl:
            R.add('error', 'SM-09', f'{w0}:linking.hubs', f"lists {h.get('lists')} не коллекция и не шаблон")
    for pid in link.get('orphans_allowed') or []:
        need_page(pid, 'linking.orphans_allowed', 'SM-10')
    bo = [x.get('template') for x in m.get('build_order') or []]
    for tid in tmpl:
        if tid not in bo:
            R.add('error', 'SM-11', f'{w0}:build_order', f'шаблон {tid} не в build_order')
    for tid in bo:
        if tid not in tmpl:
            R.add('error', 'SM-11', f'{w0}:build_order', f'{tid} нет в templates[]')
    if util.get('not_found'):
        need_page(util['not_found'], 'utility_pages.not_found', 'SM-12')
    for x in util.get('thank_you') or []:
        need_page(x.get('after'), 'utility_pages.thank_you.after', 'SM-12')
        need_page(x.get('page'), 'utility_pages.thank_you.page', 'SM-12')
    for pid in util.get('legal_set') or []:
        need_page(pid, 'utility_pages.legal_set', 'SM-12')
    srch = chrome.get('search') or {}
    if srch.get('enabled') and srch.get('results_page'):
        need_page(srch['results_page'], 'chrome.search.results_page', 'SM-12')
    # глубина и крошки
    depth = {}

    def dep(pid, seen=()):
        if pid in depth:
            return depth[pid]
        p = pages.get(pid) or {}
        par = p.get('parent')
        d = 0 if (pid == 'home' or p.get('page_type') == 'home-multipage') else (1 if not par or par in seen else dep(par, seen + (pid,)) + 1)
        depth[pid] = d
        return d
    for pid in pages:
        dep(pid)
    for pid, p in pages.items():
        t = tmpl.get(p.get('template')) or {}
        if t.get('breadcrumbs') and depth[pid] < 2:
            R.add('warning', 'SM-20', f'{w0}:pages.{pid}', f'крошки на странице глубины {depth[pid]} (правило — глубина ≥ 2, site 06/02 §2.1)')
    # граф входящих ссылок
    inbound = defaultdict(set)
    for it in hdr.get('items') or []:
        inbound[it.get('page')].add('header')
        for g in it.get('groups') or []:
            for pid in g.get('pages') or []:
                for q in ([pid] if pid in pages else [x for x, pp in pages.items() if pp.get('template') == pid]):
                    inbound[q].add('header-menu')
            if g.get('from_collection') in colls:
                ct = colls[g['from_collection']].get('template')
                for q, pp in pages.items():
                    if pp.get('template') == ct:
                        inbound[q].add('header-menu')
    for g in ftr.get('groups') or []:
        for pid in g.get('pages') or []:
            inbound[pid].add('footer')
    for pid in ftr.get('legal') or []:
        inbound[pid].add('footer-legal')
    for h in link.get('hubs') or []:
        lst = h.get('lists')
        ct = colls[lst].get('template') if lst in colls else lst
        for q, pp in pages.items():
            if pp.get('template') == ct:
                inbound[q].add(f"hub:{h.get('page')}")
    for r in link.get('related_rules') or []:
        to = r.get('to')
        tt = colls[to].get('template') if to in colls else to
        for q, pp in pages.items():
            if pp.get('template') == tt:
                inbound[q].add(f"related:{r.get('id')}")
    for pid, p in pages.items():
        t = tmpl.get(p.get('template')) or {}
        if p.get('parent') and (t.get('breadcrumbs') or True):
            inbound[p['parent']].add(f'child:{pid}')
        for x in p.get('also_listed_in') or []:
            inbound[pid].add(f'listed:{x}')
    for x in util.get('thank_you') or []:
        inbound[x.get('page')].add(f"form:{x.get('after')}")
    if tgt in pages:
        inbound[tgt].add('header-cta')
    need = link.get('min_inbound_links', 1)
    for pid, p in pages.items():
        t = tmpl.get(p.get('template')) or {}
        idx_ = p.get('indexable', t.get('indexable', True))
        if dep(pid) == 0 or pid in (link.get('orphans_allowed') or []) or not idx_:
            continue
        if len(inbound[pid]) < need:
            R.add('error', 'SM-19', f'{w0}:pages.{pid}', f'сирота: входящих ссылок {len(inbound[pid])} < {need} (меню, подвал, хаб, связанные, крошки)')
    # уровень шаблона
    blvl = (brief or {}).get('ambition', {}).get('level') if brief else None
    for tid, t in tmpl.items():
        if t.get('level') and blvl and LEVEL[t['level']] > LEVEL[blvl]:
            R.add('error', 'SM-21', f'{w0}:templates.{tid}', f"уровень шаблона {t['level']} выше уровня сайта {blvl}: "
                                                             'не выше ambition.level брифа (creative 01/03 §5.2)')
        dflt = ctx.level_defaults.get(t.get('page_type'))
        if t.get('level') and dflt and LEVEL[t['level']] > LEVEL[dflt] and not t.get('level_why'):
            R.add('warning', 'SM-21', f'{w0}:templates.{tid}', f"уровень {t['level']} выше умолчания {dflt} без level_why")
        if not t.get('level'):
            R.add('warning', 'SM-21', f'{w0}:templates.{tid}', 'нет templates[].level')
    # планы шаблонов. В папке слоя план — выход этапа page-plan, шаблоны идут по build_order по одному, поэтому шаблон без
    # плана — ход работы, а не разрыв: ошибка — только файл плана, который есть, но с шаблоном не связан
    if plans is not None:
        base = Path(path).resolve().parent
        started = bool(plan_tpl)
        waiting = []
        for tid, t in tmpl.items():
            if plans.get(tid) is not None:
                continue
            pp, pt = t.get('page_plan'), t.get('page_type')
            pfile = (base / pp).resolve() if pp else None
            if pfile is not None and pfile in (plan_tpl or {}):
                R.add('error', 'SM-22', f'{w0}:templates.{tid}', f'план {pp} есть, а с шаблоном не связан: page.template_id в нём — '
                                                                 f'«{plan_tpl[pfile] or "—"}», нужен «{tid}»')
            elif started and pt in SERVICE_PAGE_TYPES:
                R.add('warning', 'SM-22', f'{w0}:templates.{tid}', f'служебный шаблон {tid} ({pt}) без плана ({pp}): план по '
                                                                   'site 10/02 §2.1 — до его макета, другие страницы он не держит')
            else:
                waiting.append(tid)
        if waiting:
            R.add('info', 'SM-22', w0, f"шаблоны без плана ({len(waiting)} из {len(tmpl)}): {', '.join(waiting)} — "
                                       + ('очередь этапа page-plan по build_order' if started else 'этап page-plan не начат'))
    else:
        base = Path(path).resolve().parent
        missing_plans = [t.get('page_plan') for t in tmpl.values() if t.get('page_plan') and not (base / t['page_plan']).exists()]
        if missing_plans:
            R.add('info', 'SM-22', w0, f'планы шаблонов не найдены ({len(missing_plans)}): пример карты без планов')
    # «спасибо» у страниц с формой
    ty_after = {x.get('after') for x in util.get('thank_you') or []}
    for pid, p in pages.items():
        if p.get('page_type') == 'form-page' and pid not in ty_after:
            R.add('warning', 'SM-23', f'{w0}:pages.{pid}', 'страница формы без «спасибо» в utility_pages.thank_you')
    if brief is not None and m.get('site') != (brief.get('project') or {}).get('slug'):
        R.add('error', 'SM-18', w0, f"site {m.get('site')} ≠ брифа {(brief.get('project') or {}).get('slug')}")
    R.add('info', 'SM-00', w0, f'страниц {len(pages)}, шаблонов {len(tmpl)}, коллекций {len(colls)}')
    return m


# ─────────────────────────────────────────── проект ───────────────────────────────────────────
def plan_has_form(p):
    """В плане есть action-слот с формой — в секции или в элементе вне потока."""
    holders = (p.get('sections') or []) + (p.get('overlays') or []) if isinstance(p, dict) else []
    return any(isinstance(a, dict) and a.get('form') for h in holders if isinstance(h, dict)
               for a in (h.get('slots') or {}).get('action') or [])


def brief_facts(brief_path, brief):
    """Факты брифа по proof.facts_ref — (документ, факты, пробелы); None — ссылки или файла нет."""
    ref = ((brief or {}).get('proof') or {}).get('facts_ref')
    fp = (Path(brief_path).resolve().parent / ref).resolve() if ref else None
    return load_facts(fp) if fp is not None and fp.is_file() else None


def url_slash(u):
    """Хвостовой слеш адреса: True — есть, False — нет, None — у корня «/» и не пути формы нет."""
    if not isinstance(u, str) or not u.startswith('/'):
        return None
    path = re.split(r'[?#]', u, maxsplit=1)[0]
    return None if path == '/' else path.endswith('/')


def check_url_form(d, sitemap, map_path, plan_files):
    """PJ-04 — адреса страниц: у страниц сайта одна форма адреса, вторая — 301 на первую (site 06/02 §4.1). Форму
    задаёт url_policy.trailing_slash карты; у лендинга без карты адрес страницы — page.url плана: он есть у каждого
    плана, и адреса планов сверяются друг с другом."""
    urls = [(rel(pf), (load_yaml(pf).get('page') or {}).get('url')) for pf in plan_files]
    want = None
    if sitemap is None:
        for w, u in urls:
            if not (isinstance(u, str) and u.startswith('/')):
                R.add('warning', 'PJ-04', w, "у страницы лендинга нет адреса: адрес — page.url плана, путь от корня "
                      "(«/», «/spasibo/»); без него код страницу не соберёт")
    else:
        w0 = rel(map_path)
        urls += [(f"{w0}:pages.{p.get('id')}", p.get('url')) for p in sitemap.get('pages') or [] if isinstance(p, dict)]
        urls += [(f"{w0}:collections.{c.get('id')}", c.get('url_pattern'))
                 for c in sitemap.get('collections') or [] if isinstance(c, dict)]
        want = (sitemap.get('url_policy') or {}).get('trailing_slash')
    forms = [(w, u, url_slash(u)) for w, u in urls if url_slash(u) is not None]
    if isinstance(want, bool):
        for w, u, f in forms:
            if f != want:
                R.add('warning', 'PJ-04', w, f"адрес {u} {'со слешем' if f else 'без слеша'} на конце, а "
                      f"url_policy.trailing_slash карты — {str(want).lower()}: у страниц одна форма адреса, вторая — 301 "
                      "на первую")
    elif sitemap is None:
        slash = sorted({u for _, u, f in forms if f})
        bare = sorted({u for _, u, f in forms if not f})
        if slash and bare:
            R.add('warning', 'PJ-04', rel(d), f"адреса планов в двух формах — со слешем на конце: {', '.join(slash)}; без "
                  f"слеша: {', '.join(bare)}: у страниц лендинга одна форма адреса, вторая — 301 на первую")


def check_project(d, ctx):
    d = Path(d)
    briefs = sorted(d.glob('site-brief*.yaml'))
    plan_files = sorted((d / 'plans').glob('*.yaml')) if (d / 'plans').exists() else sorted(d.glob('page-plan*.yaml'))
    brief = facts_pack = None
    if briefs:
        brief, fdoc, facts, missing = check_brief(briefs[0], ctx,
                                                  plan_forms=any(plan_has_form(load_yaml(pf)) for pf in plan_files))
        if fdoc is not None:
            facts_pack = (fdoc, facts, missing)
    else:
        R.add('error', 'PJ-01', rel(d), 'в папке проекта нет site-brief*.yaml')
    maps = sorted(d.glob('site-map*.yaml'))
    plans_by_tpl, tpl_by_plan = {}, {}
    sitemap = load_yaml(maps[0]) if maps else None
    for pf in plan_files:
        pl = load_yaml(pf)
        pg = pl.get('page') or {}
        tpl_by_plan[pf.resolve()] = pg.get('template_id')
        if pg.get('template_id'):
            plans_by_tpl[pg['template_id']] = pf
    if maps:
        check_map(maps[0], ctx, brief=brief, plans=plans_by_tpl, plan_tpl=tpl_by_plan, facts_pack=facts_pack)
    for pf in plan_files:
        pl = check_plan(pf, ctx, brief=brief, facts_pack=facts_pack, sitemap=sitemap)
        if brief is not None and pl.get('site') != (brief.get('project') or {}).get('slug'):
            R.add('error', 'PJ-02', rel(pf), f"site плана {pl.get('site')} ≠ project.slug брифа")
    if brief is not None and (brief.get('pages') or {}).get('mode') == 'listed':
        ids = {(load_yaml(pf).get('page') or {}).get('id') for pf in plan_files}
        map_ids = {p['id'] for p in (sitemap or {}).get('pages') or []}
        for x in (brief.get('pages') or {}).get('list') or []:
            if x['id'] not in ids and x['id'] not in map_ids:
                pt = x.get('page_type')
                if pt in SERVICE_PAGE_TYPES:
                    R.add('warning', 'PJ-03', rel(d), f"служебная страница брифа {x['id']} ({pt}) без плана и без строки карты: "
                                                      "план по site 10/02 §2.1 — до её макета, другие страницы он не держит")
                else:
                    R.add('error', 'PJ-03', rel(d), f"страница брифа {x['id']} ({pt}) без плана и без строки карты")
    check_url_form(d, sitemap, maps[0] if maps else None, plan_files)
    R.add('info', 'PJ-00', rel(d), f'проект: бриф {len(briefs)}, карт {len(maps)}, планов {len(plan_files)}')


def detect(path):
    p = Path(path)
    if p.is_dir():
        return 'project'
    try:
        d = load_yaml(p)
    except Exception as ex:
        R.add('error', 'IO-01', rel(p), f'YAML не читается: {ex}')
        return None
    if not isinstance(d, dict):
        return None
    if 'blocks_version' in d:
        return 'blocks'
    if 'form_sets' in d:
        return 'forms'
    if 'page_plan_version' in d:
        return 'plan'
    if 'site_map_version' in d:
        return 'map'
    if 'project' in d and 'business' in d:
        return 'brief'
    return None


def run_path(path, ctx):
    k = detect(path)
    if k == 'project':
        check_project(path, ctx)
    elif k == 'blocks':
        check_blocks(ctx, Path(path))
    elif k == 'forms':
        check_forms(ctx, Path(path))
    elif k == 'plan':
        pl = load_yaml(path)
        br = None
        rb = (pl.get('refs') or {}).get('brief')
        if rb and (Path(path).resolve().parent / rb).exists():
            cand = load_yaml(Path(path).resolve().parent / rb)
            if isinstance(cand, dict) and (cand.get('project') or {}).get('slug') == pl.get('site'):
                br = cand
        check_plan(path, ctx, brief=br)
    elif k == 'map':
        m = load_yaml(path)
        br = None
        rb = (m.get('refs') or {}).get('brief')
        if rb and (Path(path).resolve().parent / rb).exists():
            cand = load_yaml(Path(path).resolve().parent / rb)
            if (cand.get('project') or {}).get('slug') == m.get('site'):
                br = cand
            else:
                R.add('info', 'SM-18', rel(path), f"refs.brief другого проекта ({(cand.get('project') or {}).get('slug')}) — сверка с брифом пропущена")
        check_map(path, ctx, brief=br, facts_pack=brief_facts(Path(path).resolve().parent / rb, br) if br else None)
    elif k == 'brief':
        check_brief(path, ctx)
    else:
        R.add('warning', 'IO-02', rel(path), 'тип файла не распознан (не бриф, план, карта, каталог, формы)')


def all_paths():
    out = [P['blocks'], P['forms']]
    ex = ROOT / '10-playbooks-contracts' / 'examples'
    if ex.exists():
        out += sorted(x for x in ex.iterdir() if x.is_dir() and not x.name.startswith('.'))
    return out


# ─────────────────────────────────────────── самопроверка ───────────────────────────────────────────
def selftest(ctx):
    ctx.today = EXAMPLES_TODAY          # примеры — на их дате: итог самопроверки не зависит от календаря и --today
    ex = ROOT / '10-playbooks-contracts' / 'examples' / 'lead-services-otves'
    if not ex.exists():
        print('нет примера 10-playbooks-contracts/examples/lead-services-otves — самопроверка невозможна')
        return 1
    import shutil
    import tempfile
    ok = True
    R.items.clear()
    check_project(ex, ctx)
    base_err = [i for i in R.items if i[0] == 'error']
    print(f"P0 пример lead-services-otves: error {len(base_err)} → {'OK' if not base_err else 'FAIL'}")
    for i in base_err[:5]:
        print('   ', i)
    ok &= not base_err
    plan_name = 'plans/home.yaml'
    site = 'corporate-b2b-stalkon'      # многостраничник: карта сайта и планы шаблонов
    if (ex.parent / site).exists():
        R.items.clear()
        check_project(ex.parent / site, ctx)
        base_err = [i for i in R.items if i[0] == 'error']
        print(f"P0 пример {site}: error {len(base_err)} → {'OK' if not base_err else 'FAIL'}")
        for i in base_err[:5]:
            print('   ', i)
        ok &= not base_err
    else:
        print(f'P0 пример {site}: FAIL (примера нет — случаи карты сайта не проверить)')
        ok = False

    def sec(p, sid):
        return next(s for s in p['sections'] if s['id'] == sid)

    def link(lid, label, **kw):
        return dict({'id': lid, 'slot': 'link', 'action': 'read-more', 'target': {'kind': 'route', 'value': '/team'},
                     'style': 'link', 'label': label}, **kw)

    def add_labels(p):
        # ссылка уровня секции с подписью у team-grid, подпись мессенджера и заголовок группы в подвале
        team, foot = sec(p, 'team')['slots'], sec(p, 'footer')['slots']
        team['text'].append({'id': 'all-label', 'slot': 'cta-secondary-label'})
        team.setdefault('action', []).append(link('all', 'all-label'))
        foot['text'] += [{'id': 'messenger-label', 'slot': 'cta-secondary-label'},
                         {'id': 'company-group-label', 'slot': 'nav-label', 'anatomy': 'group-label'}]
        foot['action'].append({'id': 'messenger', 'slot': 'messenger-link', 'action': 'message', 'style': 'channel',
                               'target': {'kind': 'messenger', 'value': 'канал компании'}, 'label': 'messenger-label'})

    def add_map_texts(p):
        # подпись ссылки маршрута и alt картинки карты
        m = sec(p, 'location-map')['slots']
        m['text'] += [{'id': 'route-label', 'slot': 'cta-secondary-label'}, {'id': 'map-alt', 'slot': 'image-alt'}]
        next(a for a in m['action'] if a['id'] == 'route')['label'] = 'route-label'
        next(x for x in m['media'] if x['id'] == 'map')['alt'] = 'map-alt'

    def objections_cards(p):
        # возражения карточками рядом с решением: секция вопросов примера становится feature-grid в роли objections
        s = sec(p, 'faq')
        s.update({'id': 'objections', 'role': 'objections', 'block': 'feature-grid', 'variant': 'cards'})
        s['slots'] = {'text': [{'id': 'title', 'slot': 'section-title', 'heading': 'h2'}]
                      + [{'id': f'card-{n}-{k}', 'slot': f'card-{k}', 'anatomy': f'card.{k}', 'group': f'card-{n}'}
                         for n in (1, 2, 3) for k in ('title', 'body')]}

    def one_card(p):
        # возражения одной карточкой: у роли objections хватает одной
        s = sec(p, 'faq')
        s.update({'id': 'objections', 'role': 'objections', 'block': 'feature-grid', 'variant': 'cards'})
        s['slots'] = {'text': [{'id': 'title', 'slot': 'section-title', 'heading': 'h2'},
                               {'id': 'card-1-title', 'slot': 'card-title', 'anatomy': 'card.title', 'group': 'card-1'},
                               {'id': 'card-1-body', 'slot': 'card-body', 'anatomy': 'card.body', 'group': 'card-1'}]}

    def siblings(p):
        # соседи раздела: вариант связанных ссылок без заголовка секции
        s = sec(p, 'related')
        s['variant'] = 'section-siblings'
        s['slots']['text'] = [x for x in s['slots']['text'] if x['id'] != 'title']

    def viewer(p):
        # окно просмотра у сетки работ: подписи его кнопок — экземпляр группы viewer
        s = sec(p, 'case-studies')
        s.update({'id': 'portfolio', 'role': 'portfolio', 'block': 'portfolio-grid', 'variant': 'grid'})
        s['slots'] = {'text': [{'id': 'title', 'slot': 'section-title', 'heading': 'h2'}]
                      + [{'id': f'viewer-{k}', 'slot': 'nav-label', 'anatomy': f'viewer.{k}-label', 'group': 'viewer-1'}
                         for k in ('close', 'prev', 'next')]}

    def one_question(p):
        s = sec(p, 'faq')
        s['variant'] = 'objections-near-cta'
        for kind in ('text', 'data'):
            s['slots'][kind] = [x for x in s['slots'][kind] if x.get('group', 'qa-1') == 'qa-1']

    def band_channels(p):
        s = sec(p, 'final-cta')
        s['variant'] = 'final-with-channels'
        s['slots'].setdefault('action', []).extend([
            {'id': 'phone', 'slot': 'phone-link', 'action': 'call', 'style': 'channel',
             'target': {'kind': 'tel', 'value': 'tel:+70000000003'}},
            {'id': 'messenger', 'slot': 'messenger-link', 'action': 'message', 'style': 'channel',
             'target': {'kind': 'messenger', 'value': 'https://t.me/primer_demo'}}])

    def add_3d(p, sid, **slot):
        sec(p, sid).setdefault('slots', {})['3d'] = [dict({'id': 'model', 'slot': 'model-3d', 'poster': 'visual'}, **slot)]

    def add_effect(p, sid, ref, transitions=None):
        sec(p, sid).setdefault('treatment', {}).setdefault('effects', []).append({'ref': ref})
        if transitions:
            p['page']['treatment']['motion_system']['page_transitions'] = transitions

    def header_cta(m, target):
        m['chrome']['header']['utilities']['cta'] = {'action': 'message', 'target': target}

    def add_prefill(p, slot='messenger-message', fact=None, page='footer.messenger-message'):
        # канал-мессенджер из фактов и готовое первое сообщение: ссылка подвала и главный призыв страницы
        add_labels(p)
        foot = sec(p, 'footer')['slots']
        foot['text'].append({'id': 'messenger-message', 'slot': PREFILL_SLOT, 'anatomy': prefill_el})
        target = {'kind': 'messenger', 'value': f'messenger:{fact or plan_fact}'}
        next(a for a in foot['action'] if a['id'] == 'messenger')['target'] = dict(target, prefill=slot)
        p['page']['cta_target'] = dict(target, prefill=page)

    def later(b, status, facts=False):
        # бриф со ссылкой на файл следующего этапа, которого ещё нет
        b['project']['status'] = status
        if facts:
            b['proof']['facts_ref'] = 'facts-later.yaml'
        else:
            b.pop('meaning', None)
            b['meaning_ref'] = 'meaning-later.yaml'

    def proof_gap(p, on_missing):
        # секция доказательств, у которой вместо фактов — названный пробел
        for d in sec(p, 'team')['slots']['data']:
            d.update({'fact': 'missing:foreman-per-object', 'on_missing': on_missing})

    def gate_exception(p, gid):
        p['page']['x-gate-exception'] = [{'id': gid, 'why': 'проверка самопроверки', 'who': 'самопроверка'}]

    def edit(f, fn):
        doc = load_yaml(f)
        fn(doc)
        f.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding='utf-8')

    # id фактов примеров — для целей-мессенджеров messenger:<fact-id>
    plan_fact = next(iter(brief_facts(ex / 'site-brief.yaml', load_yaml(ex / 'site-brief.yaml'))[1]))
    map_fact = next(iter(brief_facts(ex.parent / site / 'site-brief.yaml', load_yaml(ex.parent / site / 'site-brief.yaml'))[1]))
    # элемент готового сообщения у подвала каталога (слот PREFILL_SLOT уровня блока)
    prefill_el = next((r for r, el in anatomy_index(ctx.B['footer'])[0].items()
                       if el['slot'] == PREFILL_SLOT and el['_group'] is None), PREFILL_SLOT)

    drop = object()                     # вместо правки — снять файл из копии примера

    def lead_traffic(b):
        b['decision_context']['price_band'] = 'mid'
        share = {'paid-search': 0.4, 'maps-local': 0.35}
        for s in b['traffic']['sources']:
            s['share'] = share.get(s['source'], s['share'])

    cases = [
        ('N1 блок вне каталога', 'PL-B01', plan_name, lambda p: p['sections'][2].__setitem__('block', 'hero-magic')),
        ('N2 факт вне инвентаря', 'PL-F01', plan_name, lambda p: next(s for s in p['sections'] if s['slots'].get('data'))['slots']['data'][0].__setitem__('fact', 'fact:invented-10000-clients')),
        ('N3 два H1', 'PL-H01', plan_name, lambda p: next(s for s in p['sections'] if s['role'] != 'hero' and s['slots'].get('text'))['slots']['text'][0].__setitem__('heading', 'h1')),
        ('N4 самодельный id секции', 'PL-N01', plan_name, lambda p: p['sections'][3].__setitem__('id', 'blok-tsen')),
        ('N5 согласие link-only в ru', 'PL-G01', plan_name, lambda p: [a['form'].__setitem__('consent', 'link-only') for s in p['sections'] for a in s['slots'].get('action') or [] if a.get('form')]),
        ('N6 событие вне events.yaml', 'PL-E01', plan_name, lambda p: [a.__setitem__('event', 'event:form-submit-attempt') for s in p['sections'] for a in s['slots'].get('action') or [] if a.get('form')]),
        ('N7 окно захвата при off', 'PL-O02', plan_name, lambda p: [o.__setitem__('state', 'on') for o in p.get('overlays') or [] if o['block'] == 'capture-popup']),
        ('N8 уровень страницы выше сайта', 'PL-P03', plan_name, lambda p: (p['page'].__setitem__('ambition_level', 'L2'), p['page'].__setitem__('budget_profile', p['page']['page_type'] + '@L2'))),
        ('N9 профиль бюджета не по формату', 'PL-P01', plan_name, lambda p: p['page'].__setitem__('budget_profile', 'lead-L1')),
        ('N10 набор формы не существует', 'PL-T01', plan_name, lambda p: [a['form'].__setitem__('ref', 'lead-forms.yaml#mega-quiz') for s in p['sections'] for a in s['slots'].get('action') or [] if a.get('form')]),
        ('N88 форма без success и без адреса «спасибо»', ('warning', 'PL-T02'), plan_name, lambda p: [(a['form'].pop('success', None), a['form'].pop('thank_you_page', None)) for s in p['sections'] for a in s['slots'].get('action') or [] if (a.get('form') or {}).get('success') == 'thank-you-page']),
        ('N89 форма-остров: success inline без адреса «спасибо»', ('none', 'PL-T02'), plan_name, lambda p: [(a['form'].__setitem__('success', 'inline'), a['form'].pop('thank_you_page', None)) for s in p['sections'] for a in s['slots'].get('action') or [] if (a.get('form') or {}).get('success') == 'thank-you-page']),
        ('N11 x-gate-exception без ворот', 'PL-X01', plan_name, lambda p: p['page'].__setitem__('x-gate-exception', [{'id': 'SG-PERF-99', 'why': 'проверка самопроверки', 'who': 'самопроверка'}])),
        ('N12 бриф: прелоадер вне L2', ('warning', 'SB-D02'), 'site-brief.yaml', lambda b: (b['policies'].__setitem__('preloader', 'on'), b['policies'].__setitem__('rationale', 'самопроверка'))),
        ('N13 бриф: заявки за рубежом при ru', 'SB-L01', 'site-brief.yaml', lambda b: b['constraints'].setdefault('legal_intake', {}).__setitem__('leads_storage', 'abroad')),
        ('N14 бриф: референс в двух местах', ('warning', 'SB-A02'), 'site-brief.yaml', lambda b: b.__setitem__('references', [{'url': 'https://example.org', 'role': 'composition', 'take': ['сетка 12'], 'dont_take': ['цвета'], 'applies_to': 'section-role:hero'}, {'url': 'https://example.org', 'role': 'typography', 'take': ['кегли'], 'dont_take': ['тексты'], 'applies_to': 'section-role:faq'}])),
        ('N15 схема: чужой ключ в плане', 'PL-S01', plan_name, lambda p: p['page'].__setitem__('design_system', {'style': 'x'})),
        ('N16 метка «популярный» без факта', 'PL-F06', None, None),
        ('N17 бриф: две темы без переключателя', 'SB-C01', 'site-brief.yaml', lambda b: b.__setitem__('themes', {'default': 'system', 'dark': {'needed': True, 'why': 'вечерний трафик'}})),
        ('N18 бриф: brand.ref в пустоту', 'SB-B01', 'site-brief.yaml', lambda b: b.__setitem__('brand', {'ref': '../../design/brand.yaml'})),
        ('N19 бренд не проходит схему brand', 'SB-B02', 'brand.yaml', lambda d: d.pop('status')),
        ('N20 план: recipe: несуществующего рецепта', 'PL-D02', plan_name, lambda p: add_3d(p, 'hero', recipe='recipe:99-no-such-recipe', load='after-lcp')),
        ('N21 план: 3D ниже первого экрана по видимости', ('warning', 'PL-D03'), plan_name, lambda p: add_3d(p, 'how-it-works', recipe='recipe:01-hero-product', load='on-visible')),
        ('N22 план: секция L2 на странице L1 — spec_check.py plan', ('warning', 'PL-C01'), plan_name, lambda p: sec(p, 'hero')['treatment'].__setitem__('level', 'L2')),
        ('N23 план: эффект L2 в секции L1', 'PL-C02', plan_name, lambda p: add_effect(p, 'how-it-works', 'effect:smooth-scroll')),
        ('N24 план: переходы страниц библиотекой на L1', 'PL-C02', plan_name, lambda p: p['page']['treatment']['motion_system'].__setitem__('page_transitions', 'library')),
        ('N25 план: L1 с page-transition проходит', ('clean', 'page-transition'), plan_name, lambda p: add_effect(p, 'how-it-works', 'effect:page-transition', 'view-transitions')),
        ('N26 бриф: правило лидогенерации — L0 по данным уровней', ('warning', 'SB-A03'), 'site-brief.yaml', lead_traffic),
        ('N27 служебная страница брифа без плана', ('warning', 'PJ-03'), 'plans/spasibo.yaml', drop),
        ('N28 статья брифа без плана', 'PJ-03', 'plans/guide.yaml', drop),
        ('N29 план: подписи ссылок и ссылка секции на необязательных элементах каталога', ('none', 'PL-A03'), plan_name, add_labels),
        ('N30 план: подпись ссылки маршрута и alt карты', ('none', 'PL-A03'), 'plans/contacts.yaml', add_map_texts, site),
        ('N31 план: подпись у блока без такого элемента', 'PL-A03', plan_name, lambda p: sec(p, 'faq')['slots']['text'].append({'id': 'all-label', 'slot': 'cta-secondary-label'})),
        ('N32 бриф: одна тёмная тема с причиной', ('info', 'SB-C02'), 'site-brief.yaml', lambda b: b.__setitem__('themes', {'default': 'dark', 'dark': {'why': 'пульт диспетчера работает ночью'}})),
        ('N33 бриф: одна тёмная тема без причины', ('warning', 'SB-C02'), 'site-brief.yaml', lambda b: b.__setitem__('themes', {'default': 'dark'})),
        ('N34 бриф: «по системе» без второй темы', 'SB-C02', 'site-brief.yaml', lambda b: b.__setitem__('themes', {'default': 'system'})),
        ('N35 карта без планов: этап page-plan не начат', ('info', 'SM-22'), 'plans', drop, site),
        ('N36 карта без планов: ошибок нет', ('none', 'SM-22'), 'plans', drop, site),
        ('N37 служебный шаблон без плана', ('warning', 'SM-22'), 'plans/404.yaml', drop, site),
        ('N38 шаблон без плана, когда планы уже пишутся', ('info', 'SM-22'), 'plans/about.yaml', drop, site),
        ('N39 план есть, а с шаблоном не связан', 'SM-22', 'plans/about.yaml', lambda p: p['page'].__setitem__('template_id', 'about-us'), site),
        ('N40 план: возражения карточками — роль objections у feature-grid', ('none', 'PL-B03'), plan_name, objections_cards),
        ('N41 план: один вопрос у призыва', ('none', 'PL-A05'), plan_name, one_question),
        ('N42 план: фото в ряду «текст ↔ картинка»', ('none', 'PL-A03'), plan_name, lambda p: sec(p, 'product-demo')['slots']['media'][0].update({'slot': 'photo', 'anatomy': 'row.photo'}), 'saas-okoshko'),
        ('N43 план: телефон и мессенджер в полосе призыва', ('none', 'PL-A03'), plan_name, band_channels, 'saas-okoshko'),
        ('N47 бриф: аналитики нет — система none', ('none', 'SB-D01'), 'site-brief.yaml', lambda b: b['analytics'].__setitem__('system', 'none')),
        ('N48 бриф: аналитика без Метрики', ('warning', 'SB-D01'), 'site-brief.yaml', lambda b: b['analytics'].__setitem__('system', 'ga4')),
        ('N49 карта: цель призыва шапки — канал-мессенджер из фактов', ('none', 'SM-01'), 'site-map.yaml', lambda m: header_cta(m, f'messenger:{map_fact}'), site),
        ('N50 карта: цель-мессенджер без факта', 'SM-01', 'site-map.yaml', lambda m: header_cta(m, 'messenger:no-such-channel'), site),
        ('N51 карта: цель призыва шапки — якорь формы', ('none', 'SM-01'), 'site-map.yaml', lambda m: header_cta(m, '#lead-form'), site),
        ('N52 план: цель-мессенджер из фактов и готовое сообщение — в подвале и у призыва страницы', ('none', 'PL-A03'), plan_name, add_prefill),
        ('N53 план: prefill в пустоту', 'PL-A03', plan_name, lambda p: add_prefill(p, slot='no-such-slot')),
        ('N54 план: prefill на слот другого типа', 'PL-A03', plan_name, lambda p: add_prefill(p, slot='messenger-label')),
        ('N55 план: prefill страницы без «секция.слот»', 'PL-A03', plan_name, lambda p: add_prefill(p, page='messenger-message')),
        ('N56 план: цель-мессенджер без факта', 'PL-F01', plan_name, lambda p: add_prefill(p, fact='no-such-channel')),
        ('N57 план: prefill у цели не мессенджера', 'PL-S01', plan_name, lambda p: p['page']['cta_target'].__setitem__('prefill', 'footer.legal')),
        ('N60 x-gate-exception: ворота эффектов', ('none', 'PL-X01'), plan_name, lambda p: gate_exception(p, 'EG-PERF-01')),
        ('N61 x-gate-exception: ворот эффектов с таким id нет', 'PL-X01', plan_name, lambda p: gate_exception(p, 'EG-PERF-99')),
        ('N62 бриф draft: файла фактов ещё нет', ('info', 'SB-F01'), 'site-brief.yaml', lambda b: later(b, 'draft', facts=True)),
        ('N63 бриф proposed: файла фактов нет', 'SB-F01', 'site-brief.yaml', lambda b: later(b, 'proposed', facts=True)),
        ('N64 бриф draft: файла смысла ещё нет', ('info', 'SB-M00'), 'site-brief.yaml', lambda b: later(b, 'draft')),
        ('N65 бриф proposed: файла смысла нет', 'SB-M00', 'site-brief.yaml', lambda b: later(b, 'proposed')),
        ('N66 план: минимум фактов у секции, которая снимается до факта', ('info', 'PL-F07'), plan_name, lambda p: proof_gap(p, 'omit-block')),
        ('N67 план: минимум фактов у секции с заглушкой', ('warning', 'PL-F07'), plan_name, lambda p: proof_gap(p, 'placeholder')),
        ('N68 план главной: подтип разметки по head-kit', ('none', 'PL-SEO01'), plan_name, lambda p: p['page']['seo'].__setitem__('structured_data', ['LocalBusiness', 'WebSite']), site),
        ('N69 план главной: тип разметки вне head-kit', ('warning', 'PL-SEO01'), plan_name, lambda p: p['page']['seo'].__setitem__('structured_data', ['Product', 'WebSite']), site),
        ('N70 план шаблона: локальная навигация как у карты', ('none', 'PL-N02'), 'plans/direction.yaml', lambda p: p['page']['navigation'].__setitem__('local_nav', {'kind': 'siblings'}), site),
        ('N71 план шаблона: локальная навигация не как у карты', ('warning', 'PL-N02'), 'plans/direction.yaml', lambda p: p['page']['navigation'].__setitem__('local_nav', {'kind': 'anchors', 'sticky': True}), site),
        ('N72 план шаблона без локальной навигации карты', ('warning', 'PL-N02'), 'plans/direction.yaml', lambda p: p['page']['navigation'].pop('local_nav', None), site),
        ('N73 план approved с записью утверждения', ('none', 'PL-U01'), plan_name, lambda p: p.update({'status': 'approved', 'approval': {'by': 'владелец продукта', 'date': EXAMPLES_TODAY.isoformat()}})),
        ('N74 план approved без записи утверждения', ('warning', 'PL-U01'), plan_name, lambda p: p.__setitem__('status', 'approved')),
        ('N76 план: возражения одной карточкой', ('none', 'PL-A05'), plan_name, one_card),
        ('N77 план: соседи раздела без заголовка секции', ('none', 'PL-A05'), 'plans/news-item.yaml', siblings, site),
        ('N78 план: окно просмотра у сетки работ', ('none', 'PL-A03'), 'plans/projects.yaml', viewer, site),
    ]
    for name, want, fname, fn, *other in cases:
        if fname is None:
            print(f'{name}: пропущен (нет тарифов в примере лидогенерации; покрыт примером SaaS)')
            continue
        level, code = want if isinstance(want, tuple) else ('error', want)
        dst = Path(tempfile.mkdtemp(dir=ex.parent, prefix='.selftest-'))   # та же глубина — относительные пути примера работают
        shutil.copytree(ex.parent / other[0] if other else ex, dst, dirs_exist_ok=True)
        f = dst / fname
        if fn is drop:
            shutil.rmtree(f) if f.is_dir() else f.unlink()
        else:
            doc = load_yaml(f)
            fn(doc)
            f.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding='utf-8')
        R.items.clear()
        check_project(dst, ctx)
        errs = [i for i in R.items if i[0] == 'error']
        if level == 'clean':          # code — подстрока: ни одной ошибки о ней
            good = not [i for i in errs if code in i[3]]
        elif level == 'none':         # законная правка: ошибок нет вовсе, предупреждения с этим кодом — тоже
            good = not errs and not [i for i in R.items if i[1] == code and i[0] == 'warning']
        else:                         # доклад, а не стоп: той же находки уровнем выше нет
            higher = {'warning': ('error',), 'info': ('error', 'warning')}.get(level, ())
            good = bool([i for i in R.items if i[0] == level and i[1] == code])
            good = good and not [i for i in R.items if i[1] == code and i[0] in higher]
        if name.startswith('N26'):    # порог доли — поле ambition-levels.yaml: выше порог — правила нет
            rule, ctx.lead_rule = ctx.lead_rule, dict(ctx.lead_rule, hot_mobile_share_min=0.99)
            R.items.clear()
            check_project(dst, ctx)
            ctx.lead_rule = rule
            good = good and not [i for i in R.items if i[1] == 'SB-A03' and i[0] == 'warning']
        print(f"{name}: {'OK' if good else 'FAIL'} ({level} {code}; ошибок {len(errs)})")
        ok &= good
        shutil.rmtree(dst, ignore_errors=True)
    # форма адресов (PJ-04): у многостраничника — url_policy.trailing_slash карты, у лендинга — одна форма планов
    def url_form_case(name, exname, edits, want):
        dst = Path(tempfile.mkdtemp(dir=ex.parent, prefix='.selftest-'))
        shutil.copytree(ex.parent / exname, dst, dirs_exist_ok=True)
        for fname, fn in edits:
            edit(dst / fname, fn)
        R.items.clear()
        check_project(dst, ctx)
        got = sorted(i[2].replace(rel(dst), '<пример>') for i in R.items if i[1] == 'PJ-04' and i[0] == 'warning')
        good = got == want and not [i for i in R.items if i[1] == 'PJ-04' and i[0] == 'error']
        print(f"{name}: {'OK' if good else 'FAIL ' + str(got)}")
        shutil.rmtree(dst, ignore_errors=True)
        return good

    def url(u):
        return lambda doc: doc['page'].__setitem__('url', u)

    def map_url(pid, u):
        return lambda m: next(p for p in m['pages'] if p['id'] == pid).__setitem__('url', u)

    ok &= url_form_case('N79 карта и планы в форме url_policy — без PJ-04', site,
                        [('plans/news.yaml', url('/o-kompanii/novosti/'))], [])
    ok &= url_form_case('N80 страница карты без слеша при trailing_slash: true → PJ-04 warning', site,
                        [('site-map.yaml', map_url('projects', '/proekty'))], ['<пример>/site-map.yaml:pages.projects'])
    ok &= url_form_case('N81 адрес плана без слеша при trailing_slash: true → PJ-04 warning', site,
                        [('plans/news.yaml', url('/o-kompanii/novosti'))], ['<пример>/plans/news.yaml'])
    ok &= url_form_case('N82 лендинг: у каждого плана адрес, адреса в одной форме — без PJ-04', ex.name, [], [])
    ok &= url_form_case('N83 лендинг: адреса планов в двух формах → одно PJ-04 warning на проект', ex.name,
                        [('plans/spasibo.yaml', url('/spasibo/'))], ['<пример>'])
    ok &= url_form_case('N84 лендинг: план без page.url → PJ-04 warning на план', ex.name,
                        [('plans/spasibo.yaml', lambda doc: doc['page'].pop('url'))], ['<пример>/plans/spasibo.yaml'])
    # сроки фактов считаются от даты прогона: на день позже ближайшего valid.until примера факт не допущен
    fp = (ex / ((load_yaml(ex / 'site-brief.yaml').get('proof') or {}).get('facts_ref') or '')).resolve()
    ends = sorted(dt.date.fromisoformat(str(u)[:10]) for u in ((f.get('valid') or {}).get('until')
                  for f in (load_yaml(fp).get('facts') or [] if fp.is_file() else [])) if u)
    ends = [u for u in ends if u >= EXAMPLES_TODAY]
    if ends:
        ctx.today = ends[0] + dt.timedelta(days=1)
        R.items.clear()
        check_project(ex, ctx)
        good = any(i[0] == 'error' and 'прошёл' in i[3] for i in R.items)
        print(f"N44 дата прогона {ctx.today} — после срока факта примера: {'OK' if good else 'FAIL'} (error «срок прошёл»)")
        ok &= good
        ctx.today = EXAMPLES_TODAY
    else:
        print('N44 дата прогона после срока факта: пропущен (у фактов примера нет valid.until)')
    # подписи ссылок, alt информационных картинок, ссылка секции и каналы полосы призыва — необязательные элементы:
    # обязательный дал бы находку каждому плану, где его нет, а утверждённый план от правки каталога меняться не должен
    optional = {'portfolio-grid': ('all-label', 'project.alt'), 'team-grid': ('all', 'all-label'),
                'location-map': ('route-label', 'map-alt', 'photo-alt'),
                'footer': ('messenger-label', 'group-label', PREFILL_SLOT),
                'audience-grid': ('segment.link-label', 'segment.alt'), 'about-story': ('alt', 'link-label'),
                'cta-band': ('phone', 'messenger'), 'feature-alternating': ('row.photo', 'row.illustration', 'row.video'),
                'service-cards': ('all-label', 'service.alt'), 'article-cards': ('all-label',),
                'integrations-grid': ('all-label',), 'case-cards': ('all-cases-label',), 'faq': ('more-label',),
                'contact-details': ('route-label',), 'case-study': ('link-label',), 'testimonial-single': ('link-label',),
                'pricing-cards': ('compare-link-label',), 'video-showcase': ('transcript-label',),
                'author-bio': ('link-label',), 'feature-grid': ('card.alt',), 'feature-bento': ('tile.alt',)}
    bad = [f'{b}.{e}' for b, els in optional.items() for e in els
           if (anatomy_index(ctx.B.get(b) or {})[0].get(e) or {}).get('required', True) is not False]
    print(f"N45 каталог: подписи ссылок, alt картинок, каналы и готовое сообщение есть и необязательны: "
          f"{'OK' if not bad else 'FAIL ' + ', '.join(bad)}")
    ok &= not bad
    # --json: значение — файл вывода; ключ, папка и YAML после него — вход, JSON тогда идёт в stdout
    got = [json_target(a) for a in (['p.yaml', '--json'], ['--json', '--quiet', 'p.yaml'], ['--json', str(ex), '--quiet'],
                                    ['--json', 'p.yaml'], ['p.yaml', '--json', 'out.json', '--quiet'])]
    good = got == [(None, True, ['p.yaml']), (None, True, ['--quiet', 'p.yaml']), (None, True, [str(ex), '--quiet']),
                   (None, True, ['p.yaml']), ('out.json', False, ['p.yaml', '--quiet'])]
    import subprocess
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(ex / plan_name), '--json', '--today',
                        EXAMPLES_TODAY.isoformat()], capture_output=True, text=True)
    try:
        rows = json.loads(r.stdout)
    except ValueError:
        rows = None
    good = good and r.returncode == 0 and isinstance(rows, list) and bool(rows) and {'level', 'code', 'where', 'msg'} <= set(rows[0]) \
        and 'Итого' in r.stderr
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--json'], capture_output=True, text=True)
    good = good and r.returncode == 2 and 'Traceback' not in r.stderr and not r.stdout.strip()
    print(f"N46 --json без файла — JSON в stdout, итог в stderr; без путей — код 2 без трассировки: {'OK' if good else 'FAIL'}")
    ok &= good
    # уведомление РКН — вопрос сайта с формой (канал брифа или action-слот плана) или с необязательными cookie
    def intake(b, channels, cookies):
        b['conversion']['channels'] = channels
        b['constraints']['legal_intake'].update({'rkn_registry': 'unknown', 'optional_cookies': cookies})

    def rkn(run):
        R.items.clear()
        run()
        return [i[3] for i in R.items if i[0] == 'warning' and i[1] == 'SB-L03' and 'уведомление РКН' in i[3]]
    dst = Path(tempfile.mkdtemp(dir=ex.parent, prefix='.selftest-'))
    shutil.copytree(ex, dst, dirs_exist_ok=True)
    bf = dst / 'site-brief.yaml'
    edit(bf, lambda b: intake(b, ['messenger', 'phone'], False))
    good = not rkn(lambda: check_brief(bf, ctx)) and bool(rkn(lambda: check_brief(bf, ctx, plan_forms=True))) \
        and bool(rkn(lambda: check_project(dst, ctx)))            # форма — в планах примера
    edit(bf, lambda b: intake(b, ['form'], False))
    good = good and bool(rkn(lambda: check_brief(bf, ctx)))
    edit(bf, lambda b: intake(b, ['messenger'], True))
    good = good and any('cookie' in m for m in rkn(lambda: check_brief(bf, ctx)))
    shutil.rmtree(dst, ignore_errors=True)
    print(f"N58 уведомление РКН: без форм и cookie — нет; с формой брифа или плана и с cookie — есть: {'OK' if good else 'FAIL'}")
    ok &= good
    # факт общего подвала: роль секции названа в use.section_roles — use.page_types со страницей не сверяется; в секции
    # другой роли тот же факт сверяется
    dst = Path(tempfile.mkdtemp(dir=ex.parent, prefix='.selftest-'))
    shutil.copytree(ex.parent / site, dst, dirs_exist_ok=True)
    edit(dst / 'facts.yaml', lambda d: next(f for f in d['facts'] if f['id'] == map_fact).__setitem__(
        'use', {'page_types': ['legal-page'], 'section_roles': ['footer']}))
    R.items.clear()
    check_project(dst, ctx)
    shutil.rmtree(dst, ignore_errors=True)
    f04 = [i[2] for i in R.items if i[0] == 'warning' and i[1] == 'PL-F04' and f'fact:{map_fact}' in i[3]]
    good = bool(f04) and not [w for w in f04 if w.endswith('#footer')]
    print(f"N59 факт подвала вне use.page_types: в подвале — без находки, в секции другой роли — warning PL-F04: "
          f"{'OK' if good else 'FAIL'} (находок {len(f04)})")
    ok &= good
    # каталог: информационная картинка без парного элемента alt — доклад BL-14 с адресом «блок.элемент»
    cat = load_yaml(P['blocks'])
    cat['blocks']['about-story']['slots'] = [s for s in cat['blocks']['about-story']['slots'] if s['slot'] != 'image-alt']
    tmp = Path(tempfile.mkdtemp(prefix='site-validate-')) / 'blocks.yaml'
    tmp.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding='utf-8')

    def bl14(path):
        R.items.clear()
        check_blocks(ctx, path)
        return ' '.join(i[3] for i in R.items if i[0] == 'warning' and i[1] == 'BL-14')
    good = 'about-story.photo' in bl14(tmp) and 'about-story.photo' not in bl14(P['blocks'])
    shutil.rmtree(tmp.parent, ignore_errors=True)
    print(f"N75 каталог: информационная картинка без элемента alt — warning BL-14, с элементом — нет: {'OK' if good else 'FAIL'}")
    ok &= good
    # профиль формы без JS держится на полных перечнях: лишний слой, поле или автоцель, поле в двух перечнях или вне
    # их, успех inline, цель формы не из событий, автоцель без автоцели счётчика — LF-07
    forms = load_yaml(P['forms'])
    clean = without_js_gaps(forms['defaults'], ctx.events_doc)
    df = copy.deepcopy(forms['defaults'])
    df['antispam']['without_js'] = df['antispam']['without_js'] + ['captcha-x']
    hid = df['hidden_fields_without_js']
    hid['server'] = hid['server'] + ['landing_ref', 'ym_client_id']       # ym_client_id — уже в js_only
    hid['build'] = [x for x in hid['build'] if x != 'variant']
    df['success']['without_js'] = 'inline'
    ev = copy.deepcopy(ctx.events_doc)
    wj = ev['defaults']['without_js']
    wj.update(counter_goals=wj['counter_goals'] + ['call-done', 'cta-click'], form_success='thank-you-vist')
    got = {k.partition(' — ')[::2]: v for k, v in without_js_gaps(df, ev)}
    good = clean == [] and got == {
        ('antispam.without_js', 'слоя нет в layers'): ['captcha-x'],
        ('hidden_fields_without_js.server', 'поля нет в hidden_fields'): ['landing_ref'],
        ('hidden_fields_without_js', 'поле в двух перечнях'): ['ym_client_id'],
        ('hidden_fields_without_js', 'поля hidden_fields нет ни в одном перечне (build, server, js_only)'): ['variant'],
        ('success.without_js', 'без JS адреса успеха нет'): ['inline'],
        ('events.yaml defaults.without_js.form_success', 'не id события'): ['thank-you-vist'],
        ('events.yaml defaults.without_js.counter_goals', 'не id события'): ['call-done'],
        ('events.yaml defaults.without_js.counter_goals', 'у события нет автоцели в metrica.type'): ['cta-click']}
    print("N85 профиль формы без JS: каталог базы чист; лишний слой, поле и автоцель, поле в двух перечнях и вне "
          f"перечней, успех inline, цель формы не из событий, событие без автоцели — LF-07: {'OK' if good else 'FAIL ' + str(got)}")
    ok &= good
    # цель-контакт: литерал цели tel и мессенджера — копия machine факта, у факта цели messenger:<fact-id> — machine с
    # адресом ссылки (PL-F08 у плана, SM-24 у призыва шапки карты); цель телефона или мессенджера не по форме — PL-F09
    def contact_case(tel, link, literal, cta=None):
        dst = Path(tempfile.mkdtemp(dir=ex.parent, prefix='.selftest-'))
        shutil.copytree(ex.parent / site, dst, dirs_exist_ok=True)

        def machines(d):
            rest = [f for f in d['facts'] if f['id'] != map_fact and 'machine' not in f]
            for f, m in ((next(f for f in d['facts'] if f['id'] == map_fact), link), (rest[0], tel)):
                if m:
                    f['machine'] = m

        def targets(p):
            p['page']['cta_target'] = {'kind': 'messenger', 'value': cta or f'messenger:{map_fact}'}
            for s in p['sections']:
                for a in (s.get('slots') or {}).get('action') or []:
                    if (a.get('target') or {}).get('kind') == 'tel':
                        a['target'].update(kind='url' if literal.startswith('mailto:') else 'tel', value=literal)
        edit(dst / 'facts.yaml', machines)
        edit(dst / 'site-map.yaml', lambda m: header_cta(m, f'messenger:{map_fact}'))
        edit(dst / 'plans/contacts.yaml', targets)
        R.items.clear()
        check_project(dst, ctx)
        shutil.rmtree(dst, ignore_errors=True)
        errs = [i for i in R.items if i[0] == 'error']
        return sorted(i[1] for i in R.items if i[1] in ('PL-F08', 'PL-F09', 'SM-24') and i[0] == 'warning') if not errs else errs[:3]
    phone = {'type': 'telephone', 'value': '+70000000001'}
    chat = {'type': 'messenger', 'network': 'telegram', 'value': 'https://t.me/stalkon_demo'}
    mail = {'type': 'email', 'value': 'zakaz@stalkon.example'}
    got = [contact_case(phone, chat, 'tel:+70000000001'), contact_case(mail, chat, 'mailto:zakaz@stalkon.example'),
           contact_case(phone, chat, 'tel:+70000000001', cta=chat['value']), contact_case(None, None, 'tel:+70000000001'),
           contact_case(dict(phone, value='+70000000002'), chat, 'tel:+70000000001'),
           contact_case(phone, chat, 'mailto:zakaz@stalkon.example')]
    good = got == [[], [], [], ['PL-F08', 'PL-F08', 'SM-24'], ['PL-F08'], ['PL-F08']]
    print("N86 цель-контакт: литерал телефона, почты и адреса мессенджера равен machine факта — без находки; без machine "
          "— PL-F08 у литерала и у цели messenger:<fact-id>, SM-24 у призыва шапки; другой номер и почта без факта — "
          f"PL-F08: {'OK' if good else 'FAIL ' + str(got)}")
    ok &= good
    got = [contact_case(phone, chat, 'tel: номер из facts.yaml'), contact_case(phone, chat, 'tel:8 900 000-00-01'),
           contact_case(phone, chat, 'tel:+70000000001', cta='канал компании в мессенджере')]
    good = got == [['PL-F09']] * 3
    print("N90 цель-контакт не по форме: телефон словами и номером не в E.164, мессенджер словами — PL-F09 warning: "
          f"{'OK' if good else 'FAIL ' + str(got)}")
    ok &= good
    # таблица head-kit «вид machine → свойство JSON-LD» стоит на схеме machine фактов: виды, поля, дни, схемы реквизита
    mdefs = {o['properties']['type']['const']: o['properties'] for o in load_any(P['facts_schema'])['$defs']['machine']['oneOf']}
    table = (load_yaml(P['headkit']).get('jsonld_policy') or {}).get('fields_from_facts') or {}
    hours = mdefs['opening-hours']['hours']['items']['properties']
    days = hours['days']['items']['enum']
    bad = [t for t in table if t not in mdefs]
    for t, row in table.items():
        props = hours if t == 'opening-hours' else mdefs.get(t) or {}
        bad += [f'{t}.{k}' for k in row.get('fields') or {} if k not in props]
        bad += [f'{t}.scheme.{k}' for k in row.get('property_by_scheme') or {} if k not in mdefs['legal-id']['scheme']['enum']]
    good = bool(table) and not bad and sorted((table.get('opening-hours') or {}).get('days') or {}) == sorted(days)
    print("N87 head-kit jsonld_policy.fields_from_facts: виды, поля, дни недели и схемы реквизита — из схемы machine "
          f"фактов: {'OK' if good else 'FAIL ' + ', '.join(bad)}")
    ok &= good
    print('SELFTEST', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


def json_target(args):
    """Ключ --json → (файл вывода или None, JSON в stdout, аргументы без ключа). Значение ключа — файл вывода; ключ,
    папка и YAML после него — уже вход: тогда JSON идёт в stdout, а входной файл не затирается находками."""
    if '--json' not in args:
        return None, False, args
    i = args.index('--json')
    nxt = args[i + 1] if i + 1 < len(args) else None
    if nxt is None or nxt.startswith('--') or nxt.lower().endswith(('.yaml', '.yml')) or Path(nxt).is_dir():
        return None, True, args[:i] + args[i + 1:]
    return nxt, False, args[:i] + args[i + 2:]


def main():
    args = sys.argv[1:]
    if '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)
    today = EXAMPLES_TODAY if '--all' in args else dt.date.today()    # --all — примеры базы на их дате
    if '--today' in args:
        i = args.index('--today')
        try:
            today = dt.date.fromisoformat(args[i + 1])
        except (IndexError, ValueError):
            print('--today ждёт дату ГГГГ-ММ-ДД', file=sys.stderr)
            sys.exit(2)
        del args[i:i + 2]
    out_json, json_stdout, args = json_target(args)
    quiet = '--quiet' in args
    args = [a for a in args if a != '--quiet']
    ctx = Ctx(today)
    if '--selftest' in args:
        sys.exit(selftest(ctx))
    paths = all_paths() if '--all' in args else [Path(a) for a in args if not a.startswith('--')]
    if not paths:
        if len(sys.argv) == 1:
            print(__doc__)
        else:
            print('не названы пути: PATH [PATH…], --all или --selftest (справка — --help)', file=sys.stderr)
        sys.exit(2)
    for pth in paths:
        run_path(pth, ctx)
    cnt = R.count()
    total = (f"Итого: error {cnt['error']}, warning {cnt['warning']}, info {cnt['info']}, ok {cnt['ok']}; "
             f"словарь v{load_yaml(P['vocab']).get('version')}, блоков {len(ctx.B)}, наборов форм {len(ctx.form_sets)}, событий {len(ctx.events)}; дата {today}")
    found = json.dumps([{'level': l, 'code': c, 'where': w, 'msg': m} for l, c, w, m in R.items], ensure_ascii=False, indent=1)
    if json_stdout:                     # stdout — только JSON: его читает вызывающая утилита, итог — в stderr
        print(found)
        print(total, file=sys.stderr)
    else:
        order = ('error', 'warning') if quiet else ('error', 'warning', 'info', 'ok')
        for level in order:
            for l, c, w, m in R.items:
                if l == level:
                    print(f'{l.upper():7} {c:8} {w}: {m}')
        print('\n' + total)
        if out_json:
            Path(out_json).write_text(found, encoding='utf-8')
    sys.exit(1 if cnt['error'] else 0)


if __name__ == '__main__':
    main()
