#!/usr/bin/env python3
"""spec_check.py — проверки и проекции подачи: treatment плана страницы, спецификация движения, варианты подачи блоков,
проекция во вход холста.

Числа уровней (пики, акценты, секции с фирменным приёмом, петли в зоне видимости, свойства движения, blur) — из
kb/creative/01-creative-direction/ambition-levels.yaml (--levels — другой файл той же формы); пределы времени и смещения
первого экрана — токены motion.marketing (04-visual-language/marketing-tokens.json). Работает на примерах базы и на файлах
проекта: путь — аргументом; план находит спецификацию движения по page.treatment.motion_spec_ref и арт-дирекцию по
page.treatment.art_direction_ref, спецификация — план по refs.page_plan (пути от файла), если их не назвали ключом, и
арт-дирекцию по refs.art_direction. Шкала длительностей спецификации — токены motion.marketing базы и токены движения
проекта: ветка motion файла refs.tokens (путь от файла спецификации). Ссылка на токен проекта и длительность, равная
токену времени проекта, — не находка (MS-06, MS-07); у токена, который есть и в проекте, и в базе, в суммы и проекции
идёт значение проекта. Пределы первого экрана — токены базы. Переменные токенов движения в дорожках — имена сборки ДС:
`--` + путь токена через дефисы (`var(--motion-marketing-distance-shift-hero)`); имени нет среди токенов базы и проекта —
MS-06. Момент собирается примитивом набора движения (`primitive` — id из kb/creative/11-motion-code/primitives.yaml:
уровень, класс, эффекты и опции примитива — MS-25), эффектом каталога (`effect`) или своим кодом с пометкой `custom`;
момент без всех трёх — MS-26 (warning: исполнитель соберёт его по памяти).

Команды:
  blocks [--yaml F]                              block-treatments.yaml ↔ blocks.yaml site, effects.yaml, cliche-registry.yaml
  plan PLAN.yaml [--overlay T.yaml] [--out M.yaml] [--spec SPEC.yaml]
                                                 treatment секций и страницы: схема page-plan с treatment v1 + правила уровня
  spec SPEC.yaml [--plan PLAN.yaml] [--overlay T.yaml]
                                                 motion-spec: схема + id, эффекты, токены, классы, пределы, свойства, LCP
  moments SPEC.yaml [--section ID]               строки моментов для брифа холста (decisions.motion.moments)
  motion-md SPEC.yaml [--out MOTION.md]          блок движения motion.md входа холста: таймлайн по секциям, раскадровка,
                                                 сокращённое движение, телефон, пауза
  values SPEC.yaml --out DIR                     JSON чисел на секцию для модуля эффекта (код модуля читает числа, а не держит их)
  levels [--check]                               списки effect:<id> по level_min из effects.yaml; --check — сверка с
                                                 x-effect-levels и условиями L0, L1 treatment.schema.json (LV-01, LV-02)
                                                 и свойств приёмов каталога с их минимальным уровнем (LV-03)
  canvas-map [ФАЙЛ …]                            форма ключа x-canvas-map и покрытие полей источника правилами (без
                                                 файлов — все файлы kb с этим ключом); этапы входа холста в stages
                                                 карт — directions, treatment (страница «Подача»), mockup, motion
  --levels FILE                                  файл уровней той же формы, что ambition-levels.yaml
  --selftest                                     самопроверка на файлах базы, фикстуре проекта и подброшенных ошибках
Тяжесть находок plan: error — схема плана (TR-S), ссылка в пустоту (TR-09, TR-10, TR-13, TR-15), уровень эффекта
(TR-11), петля под переключатель страницы, которого нет (TR-16); нормы облика — уровень секции и блока, конверсия — L0,
пики, акценты и фирменные приёмы по уровню, списки page.treatment против секций, один референс — одна секция, петли,
плавная прокрутка, пределы параметров эффекта — warning: облик выбирает заказчик, находка — доклад с нормой в сообщении.
Норма подачи, принятая решением арт-дирекции, остаётся warning и получает строку «принято решением арт-дирекции
<id решения>»: уровень секции и блока (TR-01, TR-23), конверсия (TR-02, TR-03), пики, акценты и фирменные приёмы
(TR-04, TR-05, TR-06), эффекты и роль блока (TR-12, TR-24), визуальный вариант (TR-13), референс (TR-14), ритм пиков
(TR-19, TR-20), петли (TR-21), плавная прокрутка (TR-25), пределы параметров (TR-27).
Тяжесть находок spec: четыре нормы движения — error, пока их не сняло решение арт-дирекции, после — warning с тем же
правилом и той же строкой: свойство и blur по уровню (MS-08), вход элемента LCP (MS-09: transform, clip-path или opacity
от 0,01; opacity из 0 и маска строк — нет), длительность сцены первого экрана (MS-10), свойства страницы шире уровня
(MS-23). Остальные error (схема, ссылки, уровень эффекта, пределы сцен и петель) решением не снимаются.
Запись решения — exclusions.lifted_markers[] арт-дирекции: marker — id правила, decision_ref — id записи decisions[];
у каждого правила своя запись; запись, чьего решения нет в decisions[], ничего не снимает. Область записи —
необязательные page (id страницы плана) и section (id секции): без них запись действует на всю поверхность, с page —
только на этой странице, с section — только у находок этой секции (находку уровня страницы запись секции не снимает).
Страница спецификации — page.id её плана, без плана — имя файла до «.motion-spec».
Коды выхода: 0 — нет error; 1 — есть error; 2 — сбой запуска. Overlay treatment (формат примеров базы):
  {overlay_version: "1.0", plan: <путь к page-plan site>, page: {treatment страницы}, sections: {<id секции>: {treatment}}}
"""
import argparse, copy, glob, json, os, re, sys

try:
    import yaml
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ImportError as e:  # pragma: no cover
    sys.stderr.write(f'нужны pyyaml и jsonschema ≥ 4.18 ({e}); запуск — Python окружения скилла ($DDD_HOME/venv, scripts/install.sh)\n')
    sys.exit(2)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))  # scripts/lib
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb('creative'))
APP = str(kbpaths.kb())
SITE = str(kbpaths.kb('site'))
P = {
    'blocks': os.path.join(SITE, '04-blocks', 'blocks.yaml'),
    'pp_schema': os.path.join(SITE, '10-playbooks-contracts', 'schemas', 'page-plan.schema.json'),
    'sm_schema': os.path.join(SITE, '10-playbooks-contracts', 'schemas', 'site-map.schema.json'),
    'levels': os.path.join(ROOT, '01-creative-direction', 'ambition-levels.yaml'),
    'effects': os.path.join(ROOT, '06-effects-catalog', 'effects.yaml'),
    'cliche': os.path.join(ROOT, '08-uniqueness-anti-slop', 'cliche-registry.yaml'),
    'tokens': os.path.join(ROOT, '04-visual-language', 'marketing-tokens.json'),
    't_schema': os.path.join(ROOT, '09-ai-execution-evaluation', 'treatment.schema.json'),
    'm_schema': os.path.join(ROOT, '09-ai-execution-evaluation', 'motion-spec.schema.json'),
    'bt': os.path.join(ROOT, '09-ai-execution-evaluation', 'block-treatments.yaml'),
    'gates': os.path.join(ROOT, '09-ai-execution-evaluation', 'effect-gates.yaml'),
    'ad_schema': os.path.join(ROOT, '09-ai-execution-evaluation', 'art-direction.v1.schema.json'),
    'primitives': os.path.join(ROOT, '11-motion-code', 'primitives.yaml'),
}
LV = {'L0': 0, 'L1': 1, 'L2': 2}
CHROME_ROLES = {'header', 'footer', 'utility', 'legal'}
ROLES = ['peak', 'accent', 'support', 'calm', 'pause', 'chrome']
# Нормы движения spec, которые снимает решение арт-дирекции: облик выбирает заказчик, записанное отступление — доклад, а
# не стоп. Схема, ссылки и уровень эффекта решением не снимаются — это целостность файла, а не выбор облика.
LIFTABLE = ('MS-08', 'MS-09', 'MS-10', 'MS-23')
# Нормы подачи plan, которые принимает та же запись арт-дирекции: находка остаётся докладом и называет решение.
# Полнота и целостность файла (списки страницы против секций, заметки стратегий, раздел в спецификации) сюда не входят.
PLAN_LIFTABLE = ('TR-01', 'TR-02', 'TR-03', 'TR-04', 'TR-05', 'TR-06', 'TR-12', 'TR-13', 'TR-14', 'TR-19', 'TR-20', 'TR-21',
                 'TR-23', 'TR-24', 'TR-25', 'TR-27')
# Вход элемента LCP (CRV-AL-09 файла уровней): transform, clip-path или появление из 0,01; opacity из 0 и mask — нет.
LCP_PROPS = ('transform', 'translate', 'clip-path', 'opacity')
LCP_OPACITY_MIN = 0.01
LCP_MIN_RU = f'{LCP_OPACITY_MIN:g}'.replace('.', ',')
STAGES = ('directions', 'treatment', 'mockup', 'motion')                      # этапы входа холста
RULES = ('copy', 'map', 'derive', 'drop', 'claude_fills')                      # правила проекции x-canvas-map
POINTER = re.compile(r'^(?:[a-z][a-z0-9-]*#)?(?:/[^/]*)*$')                     # [<документ>#]<JSON Pointer>; * — любой элемент
CANVAS_TOP = {'source', 'stages', 'files', 'drop', 'base'}


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f) if p.endswith('.json') else yaml.safe_load(f)


def css_name(path):
    """Имя CSS-переменной токена — как у сборки ДС (ds_build.py): `--` + путь токена через дефисы."""
    return '--' + path.replace('.', '-')


def css_vars_of(tk):
    """Имена CSS-переменных в значениях дорожки: from, to и ключевые кадры."""
    vals = [tk.get('from'), tk.get('to')] + [k.get('value') for k in tk.get('keyframes') or []]
    return [n for v in vals if isinstance(v, str) for n in re.findall(r'var\((--[a-z0-9-]+)', v)]


def short_hint(ctx, name):
    """Имя токена движения для короткой переменной `--mm-<группа>-<имя>`; токена нет — None."""
    mm = re.match(r'--mm-([a-z]+)-(.+)$', name)
    if not mm:
        return None
    grp, rest = mm.groups()
    groups = {'dur': 'duration', 'ease': 'easing', 'shift': 'distance', 'lift': 'distance', 'magnet': 'distance'}
    if grp in ('shift', 'lift', 'magnet'):
        rest = f'{grp}-{rest}'
    path = f'motion.marketing.{groups.get(grp, grp)}.{rest}'
    return css_name(path) if path in ctx.motion_tokens else None


def primitive_options(pr):
    """Имена опций примитива набора: словарь {имя: умолчание} или список строк и записей {name | attr | var}."""
    opts = pr.get('options') or {}
    names = list(opts) if isinstance(opts, dict) else [o if isinstance(o, str) else (o.get('name') or o.get('attr') or o.get('var'))
                                                      for o in opts if isinstance(o, (str, dict))]
    return {re.sub(r'^(data-mk-|--mk-)', '', n) for n in names if n}


class Report:
    def __init__(self):
        self.items = []

    def add(self, sev, code, where, msg):
        self.items.append((sev, code, where, msg))

    def dump(self, title):
        e = sum(1 for i in self.items if i[0] == 'error')
        w = sum(1 for i in self.items if i[0] == 'warning')
        print(f'== {title}: error {e}, warning {w}, info {len(self.items) - e - w}')
        for sev, code, where, msg in self.items:
            print(f'  {sev:7} {code:6} {where}: {msg}')
        return 1 if e else 0


# ── справочники ────────────────────────────────────────────────────────────────────────────────────────────
class Ctx:
    def __init__(self, levels_path=None):
        self.effects = {e['id']: e for e in load(P['effects'])['effects']}
        self.blocks = load(P['blocks'])['blocks']
        reg = load(P['cliche'])
        self.cliches = {e['id'] for e in reg['entries']} | set((reg.get('id_aliases') or {}).keys())
        self.levels_path = levels_path or P['levels']
        lv = load(self.levels_path)
        self.lv = {L['id']: L for L in lv['levels']}
        self.prop_exc = {k: set(v or []) for k, v in (lv.get('property_exceptions') or {}).items()}
        caps = lv.get('section_caps') or {}
        self.conv_roles = set(caps.get('conversion_roles_max_L0') or [])
        self.conv_blocks = set(caps.get('conversion_blocks_max_L0') or [])
        self.tokens = {}
        tok = load(P['tokens'])
        self._flat(tok.get('motion', {}), 'motion')
        self.motion_tokens = dict(self.tokens)
        for k, v in tok.items():
            if not k.startswith('$') and k != 'motion':
                self._flat(v, k)
        self.all_tokens = set(self.tokens)
        self.tokens = self.motion_tokens
        self.motion_css = {css_name(k): k for k in self.motion_tokens}      # имя CSS-переменной токена → путь токена
        self.bt = load(P['bt'])
        self.primitives = {}
        if os.path.exists(P['primitives']):
            doc = load(P['primitives'])
            items = doc.get('primitives') if isinstance(doc, dict) else doc
            self.primitives = {x['id']: x for x in items or [] if isinstance(x, dict) and x.get('id')}

    def _flat(self, node, path):
        if isinstance(node, dict):
            if '$value' in node:
                self.tokens[path] = node['$value']
                return
            for k, v in node.items():
                if not k.startswith('$'):
                    self._flat(v, f'{path}.{k}')

    # ── уровни: ambition-levels.yaml ────────────────────────────────────────────────────────────────────────
    def dist(self, lvl):
        return self.lv[lvl].get('section_distribution') or {}

    def peaks(self, lvl):
        d = self.dist(lvl)
        return d.get('peaks_min', 0), d.get('peaks_max')

    def accents_max(self, lvl):
        return self.dist(lvl).get('accents_max')

    def accent_sections(self, lvl):
        return self.dist(lvl).get('accent_sections')

    def signature_max(self, lvl):
        return self.lv[lvl].get('signature_moves_max')

    def calm_between_peaks(self, lvl):
        return self.dist(lvl).get('calm_between_peaks_min') or 0

    def hints(self, lvl):
        return self.lv[lvl].get('motion_hints') or {}

    def loops_max(self, lvl, device='desktop'):
        v = self.hints(lvl).get('continuous_motions_in_view_max')
        return v.get(device) if isinstance(v, dict) else v

    def props(self, lvl):
        return set(self.hints(lvl).get('properties_allowed') or [])

    def blur_max(self, lvl):
        return self.hints(lvl).get('blur_max_px')

    def forbids(self, lvl, item):
        return any(f.get('id') == item for f in self.lv[lvl].get('forbidden') or [])

    @staticmethod
    def prop_in(prop, allowed):
        return (prop in allowed or ('--*' in allowed and prop.startswith('--'))
                or ('uniform:*' in allowed and prop.startswith('uniform:')))

    def exc_effects(self, prop):
        """Эффекты, которым свойство разрешено исключением: строка property_exceptions этого свойства и строка-маска
        `--*` (любое пользовательское свойство)."""
        out = set(self.prop_exc.get(prop, ()))
        if prop.startswith('--'):
            out |= self.prop_exc.get('--*', set())
        return out

    def prop_ok(self, lvl, prop, effect=None):
        """Свойство разрешено уровнем или его исключением (property_exceptions: свойство или маска → эффекты)."""
        return self.prop_in(prop, self.props(lvl)) or (effect is not None and effect in self.exc_effects(prop))

    def token_ms(self, ref):
        v = self.tokens.get(ref)
        if isinstance(v, dict) and 'value' in v:
            return float(v['value'])
        if isinstance(v, (int, float)):
            return float(v)
        return None

    def token_num(self, ref, default=None):
        v = self.token_ms(ref)
        return default if v is None else v

    def scale_ms(self):
        out = set()
        for k, v in self.tokens.items():
            if k.startswith('motion.marketing.duration.') or k.startswith('motion.marketing.stagger.'):
                if isinstance(v, dict) and v.get('unit') == 'ms':
                    out.add(float(v['value']))
        return out

    def css_var(self, name):
        """Число токена движения по имени CSS-переменной (`--` + путь токена через дефисы); чужое имя — None."""
        path = self.motion_css.get(name)
        return self.token_ms(path) if path else None

    def block_eff(self, bid):
        """Эффекты блока по уровням (накопительно) и поля блока с наследованием семейства."""
        b = self.bt['blocks'].get(bid)
        if b is None:
            return None
        fam = self.bt['families'].get(b.get('family'), {})
        res = {k: v for k, v in fam.items()}
        res.update(b)
        eff = res.get('effects') or {}
        acc, out = [], {}
        for L in ('L0', 'L1', 'L2'):
            acc = acc + list(eff.get(L) or [])
            out[L] = set(acc)
        res['_eff'] = out
        return res


def registry(t_schema):
    res = []
    for key in ('pp_schema', 'sm_schema'):
        d = load(P[key])
        res.append((d['$id'], Resource.from_contents(d, default_specification=DRAFT202012)))
    res.append((t_schema['$id'], Resource.from_contents(t_schema, default_specification=DRAFT202012)))
    return Registry().with_resources(res)


# ── blocks ─────────────────────────────────────────────────────────────────────────────────────────────────
def cmd_blocks(ctx, R, path=None):
    bt = load(path) if path else ctx.bt
    site_ids, our_ids = set(ctx.blocks), set(bt['blocks'])
    for b in sorted(site_ids - our_ids):
        R.add('error', 'BT-01', b, 'блок есть в blocks.yaml site, но нет в block-treatments.yaml')
    for b in sorted(our_ids - site_ids):
        R.add('error', 'BT-01', b, 'блока нет в blocks.yaml site')
    fams = bt.get('families') or {}
    for name, fam in list(fams.items()) + [(k, v) for k, v in bt['blocks'].items()]:
        where = f'{"family " if name in fams and name not in bt["blocks"] else ""}{name}'
        for L, lst in (fam.get('effects') or {}).items():
            if L not in LV:
                R.add('error', 'BT-02', where, f'ключ уровня {L}')
                continue
            for ref in lst or []:
                eid = ref.split(':', 1)[1] if ref.startswith('effect:') else None
                e = ctx.effects.get(eid)
                if e is None:
                    R.add('error', 'BT-02', where, f'{ref} нет в effects.yaml')
                elif LV[e['level_min']] > LV[L]:
                    R.add('error', 'BT-03', where, f'{ref} level_min {e["level_min"]} > {L}')
        for c in fam.get('avoid') or []:
            if not c.startswith('cliche:') or c[7:] not in ctx.cliches:
                R.add('error', 'BT-04', where, f'{c} нет в cliche-registry.yaml')
        for r in fam.get('roles') or []:
            if r not in ROLES:
                R.add('error', 'BT-08', where, f'роль {r}')
        if fam.get('level_max') and fam['level_max'] not in LV:
            R.add('error', 'BT-09', where, f'level_max {fam["level_max"]}')
    for bid, b in bt['blocks'].items():
        if b.get('family') not in fams:
            R.add('error', 'BT-07', bid, f'семейство {b.get("family")} не описано')
        site = ctx.blocks.get(bid) or {}
        svars = {v.get('id') for v in site.get('variants') or []}
        seen = set()
        full = ctx.block_eff(bid)
        for vv in b.get('visual_variants') or []:
            if vv['id'] in seen:
                R.add('error', 'BT-06', bid, f'повтор visual_variant {vv["id"]}')
            seen.add(vv['id'])
            for s in vv.get('structural') or []:
                if svars and s not in svars:
                    R.add('error', 'BT-05', f'{bid}.{vv["id"]}', f'структурного варианта {s} нет у блока site ({sorted(svars)})')
            for L in vv.get('levels') or []:
                if full and LV.get(L, 9) > LV.get(full.get('level_max', 'L2'), 2):
                    R.add('error', 'BT-09', f'{bid}.{vv["id"]}', f'уровень {L} выше level_max {full.get("level_max")}')
    return R


# ── plan ───────────────────────────────────────────────────────────────────────────────────────────────────
def merge_overlay(plan, ov, R):
    plan = copy.deepcopy(plan)
    pg = plan.setdefault('page', {})
    if ov.get('page') is not None:
        pg['treatment'] = ov['page']
    ids = {s['id']: s for s in plan.get('sections') or []}
    for sid, t in (ov.get('sections') or {}).items():
        if sid not in ids:
            R.add('error', 'TR-09', f'overlay.{sid}', 'секции нет в плане (id v1: роль или блок)')
            continue
        ids[sid]['treatment'] = t
    for sid in ids:
        if sid not in (ov.get('sections') or {}):
            R.add('info', 'TR-00', sid, 'treatment взят из плана site (v0), overlay его не задаёт')
    return plan


def section_targets(s):
    sid = s['id']
    out = {sid}
    for kind, lst in (s.get('slots') or {}).items():
        for x in lst or []:
            out.add(f'{sid}.{x["id"]}')
            g = x.get('group')
            an = x.get('anatomy')
            if g:
                base = re.sub(r'-\d+$', '', g)
                out |= {f'{sid}.{g}', f'{sid}.{base}'}
                if an and '.' in an:
                    el = an.split('.', 1)[1]
                    out |= {f'{sid}.{g}.{el}', f'{sid}.{base}.{el}'}
            if an:
                out.add(f'{sid}.{an}')
                if '.' in an:
                    out.add(f'{sid}.{an.split(".")[0]}')
    return out


def target_ok(t, targets, sid=None):
    if t in ('section', 'page') or t in targets:
        return True
    parts = t.split('.')
    return len(parts) >= 2 and parts[1].startswith('fx-') and (sid is None or parts[0] == sid)


def is_conv(ctx, s):
    role, bid = s.get('role'), s.get('block')
    acts = (s.get('slots') or {}).get('action') or []
    return role in ctx.conv_roles or bid in ctx.conv_blocks or any(a.get('form') or a.get('slot') == 'form' for a in acts)


def ref_file(base_file, ref):
    """Путь из ссылки файла (часть до «#»), от папки этого файла; нет файла — None."""
    if not ref or not isinstance(ref, str):
        return None
    p = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(base_file)), ref.split('#', 1)[0]))
    return p if os.path.isfile(p) else None


def cmd_plan(ctx, R, plan_path, overlay_path=None, out=None, spec=None):
    plan = load(plan_path)
    if overlay_path:
        ov = load(overlay_path)
        plan = merge_overlay(plan, ov, R)
    if spec is None:
        ref = ((plan.get('page') or {}).get('treatment') or {}).get('motion_spec_ref')
        sp = ref_file(overlay_path or plan_path, ref)
        if sp:
            spec = load(sp)
            R.add('info', 'TR-00', 'page', f'спецификация движения — {os.path.relpath(sp)} (page.treatment.motion_spec_ref)')
    t_schema = load(P['t_schema'])
    reg = registry(t_schema)
    v = Draft202012Validator(load(P['pp_schema']), registry=reg)
    for e in sorted(v.iter_errors(plan), key=lambda x: list(x.path)):
        R.add('error', 'TR-S', '/'.join(str(p) for p in e.path), e.message[:220])
    if not isinstance(plan.get('sections'), list) or not all(isinstance(s, dict) for s in plan['sections']):
        R.add('error', 'TR-S', 'sections', 'не план страницы: sections — список секций (overlay подачи — ключом --overlay)')
        return plan
    pg = plan.get('page') or {}
    lvl = pg.get('ambition_level')
    pt = pg.get('treatment') or {}
    ms = pt.get('motion_system') or {}
    lifted = lifted_records(art_direction_of(overlay_path or plan_path, pt.get('art_direction_ref')), PLAN_LIFTABLE)
    page_id = page_id_of(plan, plan_path)

    def norm(code, where, msg, sections=()):
        """Норма подачи — доклад; принятая решением арт-дирекции в области находки (страница, секции) — с решением
        в сообщении. Находка уровня страницы — sections пуст."""
        ok_refs, lost_refs = lifted_for(lifted, code, page_id, sections)
        if ok_refs:
            msg = f'{msg} — принято решением арт-дирекции {", ".join(ok_refs)}'
        elif lost_refs:
            msg = (f'{msg}; снятая примета {code} арт-дирекции не действует: решения '
                   f'{", ".join(str(x) for x in lost_refs)} нет в decisions')
        R.add('warning', code, where, msg)
    flow = [s for s in plan.get('sections') or [] if s.get('role') not in CHROME_ROLES]
    peaks, accents, sigs, used_refs, roles_seq = [], [], [], {}, []
    spec_ids = set()
    if spec is not None:
        spec_ids = {s['id'] for s in spec.get('sections') or []}
    for s in plan.get('sections') or []:
        sid, t = s['id'], s.get('treatment') or {}
        if not t:
            continue
        w = f'{sid}'
        tl = t.get('level') or lvl
        bl = ctx.block_eff(s.get('block'))
        if tl and lvl and LV[tl] > LV[lvl]:
            norm('TR-01', w, f'уровень секции {tl} выше уровня страницы {lvl}', (sid,))
        conv = is_conv(ctx, s)
        if conv and tl and tl != 'L0':
            norm('TR-02', w, f'секция конверсии ({s.get("role")}, {s.get("block")}) — только L0', (sid,))
        effs = t.get('effects') or []
        if conv and any(e.get('purpose') == 'signature' for e in effs):
            norm('TR-03', w, 'фирменный эффект в секции конверсии', (sid,))
        if bl is not None and tl and LV[tl] > LV[bl.get('level_max', 'L2')]:
            norm('TR-23', w, f'уровень {tl} выше level_max блока {s.get("block")} ({bl.get("level_max")})', (sid,))
        vr = t.get('visual_role')
        if s.get('role') in CHROME_ROLES and vr not in (None, 'chrome'):
            R.add('warning', 'TR-22', w, f'служебная роль {s.get("role")} с visual_role {vr}')
        if bl is not None and vr and vr not in (bl.get('roles') or ROLES):
            norm('TR-24', w, f'visual_role {vr} не из ролей блока {bl.get("roles")}', (sid,))
        if vr == 'peak':
            peaks.append(sid)
        if vr == 'accent':
            accents.append(sid)
        if any(e.get('purpose') == 'signature' for e in effs):
            sigs.append(sid)
        if s in flow:
            roles_seq.append((sid, vr))
        targets = section_targets(s)
        for i, e in enumerate(effs):
            we = f'{w}.effects[{i}]'
            eid = e['ref'].split(':', 1)[1]
            ce = ctx.effects.get(eid)
            if ce is None:
                R.add('error', 'TR-10', we, f'{e["ref"]} нет в effects.yaml')
                continue
            if tl and LV[ce['level_min']] > LV[tl]:
                R.add('error', 'TR-11', we, f'{e["ref"]} level_min {ce["level_min"]} > уровня секции {tl}')
            if bl is not None and tl and e['ref'] not in bl['_eff'].get(tl, set()):
                norm('TR-12', we, f'{e["ref"]} не в списке блока {s.get("block")} для {tl} (block-treatments.yaml)', (sid,))
            if e.get('target') and not target_ok(e['target'], targets, sid):
                R.add('error', 'TR-09', we, f'target {e["target"]} не найден в секции (слоты, группы, anatomy, fx-*)')
            kind = (ce.get('motion') or {}).get('kind')
            kinds = kind if isinstance(kind, list) else [kind]   # motion.kind каталога — строка или список классов
            if e.get('class') and kind and e['class'] not in kinds:
                R.add('warning', 'TR-18', we, f'class {e["class"]} ≠ motion.kind каталога {kind}')
            lim = ce.get('limits') or {}
            for k, val in (e.get('params') or {}).items():
                for lk, lv in lim.items():
                    if lv is None or not isinstance(val, (int, float)):
                        continue
                    if lk == f'{k}_max' and val > lv or lk == f'{k}_min' and val < lv:
                        norm('TR-27', we, f'params.{k}={val} вне limits {lk}={lv}', (sid,))
        vw = t.get('viewer') or {}
        if vw.get('effect'):
            ce = ctx.effects.get(vw['effect'].split(':', 1)[1])
            if ce is None:
                R.add('error', 'TR-10', f'{w}.viewer', f'{vw["effect"]} нет в effects.yaml')
            elif tl and LV[ce['level_min']] > LV[tl]:
                R.add('error', 'TR-11', f'{w}.viewer', f'{vw["effect"]} level_min {ce["level_min"]} > уровня секции {tl}')
        if vw.get('target') and not target_ok(vw['target'], targets, sid):
            R.add('error', 'TR-09', f'{w}.viewer', f'target {vw["target"]} не найден в секции (слоты, группы, anatomy, fx-*)')
        tok = (t.get('background') or {}).get('token')
        if tok and tok not in ctx.all_tokens:
            R.add('warning', 'TR-28', w, f'background.token {tok} нет в marketing-tokens.json')
        vv = t.get('visual_variant')
        if vv and bl is not None:
            vmap = {x['id']: x for x in bl.get('visual_variants') or []}
            if vv not in vmap:
                R.add('error', 'TR-13', w, f'visual_variant {vv} нет у блока {s.get("block")} ({sorted(vmap)})')
            elif s.get('variant') and vmap[vv].get('structural') and s['variant'] not in vmap[vv]['structural']:
                norm('TR-13', w, f'visual_variant {vv} задуман для {vmap[vv]["structural"]}, а вариант плана {s["variant"]}', (sid,))
            elif vmap.get(vv, {}).get('levels') and tl not in vmap[vv]['levels']:
                norm('TR-13', w, f'visual_variant {vv} задуман для уровней {vmap[vv]["levels"]}, секция {tl}', (sid,))
        for r in t.get('refs') or []:
            used_refs.setdefault(r, []).append(sid)
        if t.get('loop_control') == 'page-toggle' and not ms.get('reduce_toggle'):
            R.add('error', 'TR-16', w, 'loop_control page-toggle без page.treatment.motion_system.reduce_toggle: true')
        if (t.get('mobile') or {}).get('strategy') in ('simplified', 'separate-asset') and not (t.get('mobile') or {}).get('note'):
            R.add('warning', 'TR-17', w, 'mobile simplified/separate-asset без note: объявите, что меняется')
        if (t.get('reduce') or {}).get('strategy') == 'custom' and not (t.get('reduce') or {}).get('note'):
            R.add('warning', 'TR-26', w, 'reduce custom без note')
        lmax = ctx.loops_max(tl) if tl else None
        if lmax is not None and (t.get('loops') or 0) > lmax:
            norm('TR-21', w, f'петель {t["loops"]} > {lmax} для {tl} (ambition-levels.yaml continuous_motions_in_view_max)', (sid,))
        msr = t.get('motion_spec_ref')
        if msr and spec is not None and '#/sections/' in msr and msr.split('#/sections/')[1] not in spec_ids:
            R.add('error', 'TR-15', w, f'motion_spec_ref → секции {msr.split("#/sections/")[1]} нет в motion-spec')
        if spec is not None and vr in ('peak', 'accent') and sid not in spec_ids:
            R.add('warning', 'TR-15', w, f'{vr} без раздела в motion-spec')
    if lvl:
        lo, hi = ctx.peaks(lvl)
        if not lo <= len(peaks) <= (hi if hi is not None else len(peaks)):
            norm('TR-04', 'page', f'пиков {len(peaks)} {peaks}, норма {lo}–{hi} для {lvl}')
        amax, where = ctx.accents_max(lvl), ctx.accent_sections(lvl)
        if amax is not None and len(accents) > amax:
            norm('TR-05', 'page', f'акцентов {len(accents)} {accents} > {amax} для {lvl}')
        smax = ctx.signature_max(lvl)
        if smax is not None and len(sigs) > smax:
            norm('TR-06', 'page', f'секций с signature {len(sigs)} {sigs} > {smax} для {lvl}')
        if where and any(a not in where for a in accents):
            norm('TR-05', 'page', f'на {lvl} акцент — только {", ".join(where)}: {accents}')
    if pt.get('peaks') is not None and set(pt['peaks']) != set(peaks):
        R.add('warning', 'TR-07', 'page', f'page.treatment.peaks {pt["peaks"]} ≠ секции-пики {peaks}')
    if pt.get('accents') is not None and set(pt['accents']) != set(accents):
        R.add('warning', 'TR-08', 'page', f'page.treatment.accents {pt["accents"]} ≠ секции-акценты {accents}')
    if pt.get('signature_sections') is not None and set(pt['signature_sections']) != set(sigs):
        R.add('warning', 'TR-08', 'page', f'signature_sections {pt["signature_sections"]} ≠ {sigs}')
    if ms.get('smooth_scroll') and lvl != 'L2':
        norm('TR-25', 'page', f'плавная прокрутка на {lvl} (только L2)')
    calm = ctx.calm_between_peaks(lvl) if lvl else 0
    for i in range(1, len(roles_seq)):
        if roles_seq[i][1] == 'peak' and roles_seq[i - 1][1] == 'peak':
            norm('TR-19', f'{roles_seq[i - 1][0]}+{roles_seq[i][0]}', 'два пика подряд (где пиков несколько — только одна сквозная сцена)',
                 (roles_seq[i - 1][0], roles_seq[i][0]))
    if calm:
        idx = [i for i, (_, r) in enumerate(roles_seq) if r == 'peak']
        for a, b in zip(idx, idx[1:]):
            if not any(r in ('calm', 'pause') for _, r in roles_seq[a + 1:b]):
                norm('TR-20', f'{roles_seq[a][0]}…{roles_seq[b][0]}', 'между пиками нет calm или pause', (roles_seq[a][0], roles_seq[b][0]))
    for r, where in used_refs.items():
        if len(where) > 1:
            norm('TR-14', 'page', f'референс {r} в {len(where)} секциях {where}', tuple(where))
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            yaml.safe_dump(plan, f, allow_unicode=True, sort_keys=False, width=140)
    return plan


# ── spec ───────────────────────────────────────────────────────────────────────────────────────────────────
def time_ms(v):
    """Значение токена времени в мс: размерность {value, unit: ms | s}; другое значение — None."""
    if not isinstance(v, dict) or isinstance(v.get('value'), bool) or not isinstance(v.get('value'), (int, float)):
        return None
    return {'ms': 1.0, 's': 1000.0}[v['unit']] * v['value'] if v.get('unit') in ('ms', 's') else None


def project_motion(spec_path, spec):
    """Токены движения проекта: ветка motion файла refs.tokens спецификации (путь от её папки) → {путь токена: значение}.
    Ссылки нет, файл не читается или это marketing-tokens.json базы — пусто: действует только шкала базы."""
    path = ref_file(spec_path, (spec.get('refs') or {}).get('tokens')) if isinstance(spec, dict) else None
    if not path or os.path.samefile(path, P['tokens']):
        return {}
    try:
        doc = load(path)
    except (OSError, ValueError, yaml.YAMLError):
        return {}
    out = {}

    def walk(node, p):
        if isinstance(node, dict):
            if '$value' in node:
                out[p] = node['$value']
                return
            for k, v in node.items():
                if not str(k).startswith('$'):
                    walk(v, f'{p}.{k}')
    walk(doc.get('motion') if isinstance(doc, dict) else None, 'motion')
    return out


def project_scale(ptok):
    """Шкала движения проекта: длительности в мс всех токенов времени ветки motion проекта."""
    return {ms for ms in (time_ms(v) for v in (ptok or {}).values()) if ms is not None}


def dur_ms(ctx, d, base, ptok=None):
    """Длительность в мс: число, токен (токен проекта ptok, иначе токен базы) или доля базовой длительности."""
    if not d:
        return None
    if 'ms' in d:
        return float(d['ms'])
    if 'token' in d:
        own = time_ms((ptok or {}).get(d['token']))
        return ctx.token_ms(d['token']) if own is None else own
    if 'share' in d and base:
        return float(d['share']) * base
    return None


def px_of(ctx, s):
    """Максимальное смещение в px из строки transform; var(--motion-marketing-…) — по токенам."""
    if isinstance(s, (int, float)):
        return None
    vals = [float(x) for x in re.findall(r'(-?\d+(?:\.\d+)?)px', s or '')]
    for name in re.findall(r'var\((--[a-z0-9-]+)', s or ''):
        v = ctx.css_var(name)
        if v is not None:
            vals.append(v)
    return max((abs(x) for x in vals), default=None)


def art_direction_of(base_file, ref):
    """Арт-дирекция по ссылке файла (путь до «#» — от папки файла); файла нет или он не читается — None."""
    ad_path = ref_file(base_file, ref)
    if not ad_path:
        return None
    try:
        ad = load(ad_path)
    except (OSError, ValueError, yaml.YAMLError):
        return None
    return ad if isinstance(ad, dict) else None


def lifted_records(ad, rules):
    """Записи exclusions.lifted_markers[] арт-дирекции о правилах rules: marker — ровно id правила, decision_ref — id
    записи decisions[] (known — запись есть), page и section — необязательная область. Арт-дирекции нет — пусто."""
    if not isinstance(ad, dict):
        return []
    known = {d.get('id') for d in ad.get('decisions') or [] if isinstance(d, dict)}
    ex = ad.get('exclusions')
    out = []
    for lm in (ex.get('lifted_markers') if isinstance(ex, dict) else None) or []:
        if not isinstance(lm, dict):
            continue
        rule, ref = str(lm.get('marker') or '').strip(), lm.get('decision_ref')
        if rule in rules:
            out.append({'rule': rule, 'ref': ref, 'known': isinstance(ref, str) and ref in known,
                        'page': lm.get('page'), 'section': lm.get('section')})
    return out


def lifted_for(records, rule, page=None, sections=()):
    """Решения о правиле rule для находки на странице page в секциях sections: ([id решений], [decision_ref без записи
    в decisions[]]). Запись без области действует везде; с page — только на этой странице; с section — только у
    находки этой секции: находку уровня страницы (sections пуст) запись секции не снимает."""
    ok, lost = [], []
    for r in records:
        if r['rule'] != rule or (r['page'] is not None and r['page'] != page):
            continue
        if r['section'] is not None and r['section'] not in sections:
            continue
        lst = ok if r['known'] else lost
        if r['ref'] not in lst:
            lst.append(r['ref'])
    return ok, lost


def page_id_of(plan, path):
    """id страницы для области записей: page.id плана; плана нет — имя файла path без расширения и «.motion-spec»
    (файлы проекта названы id страницы)."""
    pid = (plan.get('page') or {}).get('id') if isinstance(plan, dict) else None
    if isinstance(pid, str) and pid:
        return pid
    name = os.path.basename(str(path or ''))
    for suf in ('.motion-spec.yaml', '.motion-spec.yml', '.yaml', '.yml', '.json'):
        if name.endswith(suf):
            return name[:-len(suf)]
    return name or None


def track_start(tk):
    """Начальное значение дорожки числом: from или первый keyframe; не число — None."""
    v = tk.get('from') if 'from' in tk else ((tk.get('keyframes') or [{}])[0].get('value'))
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cmd_spec(ctx, R, spec_path, plan_path=None, overlay_path=None):
    spec = load(spec_path)
    v = Draft202012Validator(load(P['m_schema']))
    for e in sorted(v.iter_errors(spec), key=lambda x: list(x.path)):
        R.add('error', 'MS-S', '/'.join(str(p) for p in e.path), e.message[:220])
    if any(i[1] == 'MS-S' for i in R.items):
        return spec
    lifted = lifted_records(art_direction_of(spec_path, (spec.get('refs') or {}).get('art_direction')), LIFTABLE)
    lvl = spec['level']
    page = spec['page']
    base = (page.get('base') or {}).get('duration_ms')
    plan = None
    if not plan_path and not overlay_path:
        plan_path = ref_file(spec_path, (spec.get('refs') or {}).get('page_plan'))
        if plan_path:
            R.add('info', 'MS-00', 'refs', f'план страницы — {os.path.relpath(plan_path)} (refs.page_plan)')
    if plan_path:
        plan = load(plan_path)
        if overlay_path:
            plan = merge_overlay(plan, load(overlay_path), Report())
    page_id = page_id_of(plan, spec_path)

    def norm(code, where, msg, section=None):
        """Норма движения: снятая решением арт-дирекции в области находки (страница, секция) — доклад с тем же
        правилом и решением; иначе error. Находка уровня страницы — section не задан."""
        ok_refs, lost_refs = lifted_for(lifted, code, page_id, (section,) if section else ())
        if ok_refs:
            R.add('warning', code, where, f'{msg} — принято решением арт-дирекции {", ".join(ok_refs)}')
        elif lost_refs:
            R.add('error', code, where, f'{msg}; снятая примета {code} арт-дирекции не действует: решения '
                                        f'{", ".join(str(x) for x in lost_refs)} нет в decisions')
        else:
            R.add('error', code, where, msg)
    page_props = page.get('properties_allowed') or []
    wide = [p for p in page_props if not ctx.prop_in(p, ctx.props(lvl)) and not ctx.exc_effects(p)]
    if wide:
        norm('MS-23', 'page.properties_allowed', f'шире уровня {lvl}: {wide} (ambition-levels.yaml motion_hints.properties_allowed)')
    shift_max = ctx.token_ms('motion.marketing.distance.shift-hero')
    scene_max = ctx.token_ms('motion.marketing.duration.hero-scene-max')
    group_max = ctx.token_ms('motion.marketing.stagger.group-total-max')
    if plan and (plan.get('page') or {}).get('ambition_level') not in (None, lvl):
        R.add('error', 'MS-01', 'level', f'уровень спецификации {lvl} ≠ уровню плана {plan["page"]["ambition_level"]}')
    psec = {s['id']: s for s in (plan or {}).get('sections') or []}
    # шкала длительностей: токены базы и токены движения проекта (refs.tokens) — дизайн-система проекта ведёт свою шкалу
    ptok = project_motion(spec_path, spec)
    scale = ctx.scale_ms() | project_scale(ptok)
    own = ' и токенов движения проекта (refs.tokens)' if ptok else ''
    for key in ('lcp',):
        t = page[key]['target']
        if plan and not any(target_ok(t, section_targets(s)) for s in psec.values()):
            R.add('error', 'MS-03', f'page.{key}', f'target {t} не найден в плане')
    first_flow = next((s['id'] for s in (plan or {}).get('sections') or [] if s.get('role') not in CHROME_ROLES), None)
    for si, sec in enumerate(spec['sections']):
        sid = sec['id']
        w = sid
        ps = psec.get(sid)
        if plan and ps is None:
            R.add('error', 'MS-01', w, 'секции нет в плане (id v1)')
        tr = (ps or {}).get('treatment') or {}
        if tr.get('visual_role') and tr['visual_role'] != sec['role']:
            R.add('error', 'MS-02', w, f'role {sec["role"]} ≠ treatment.visual_role {tr["visual_role"]}')
        slvl = sec.get('level') or tr.get('level') or lvl
        targets = section_targets(ps) if ps else None
        scene = sec.get('scene') or {}
        st_ids = {x['id'] for x in scene.get('stations') or []}
        L = scene.get('length_vh')
        if L is not None:
            cap = ctx.token_ms('motion.marketing.scroll.pin-l1-max-vh') if slvl == 'L1' else ctx.token_ms('motion.marketing.scroll.pin-l2-max-vh')
            if scene.get('scroll_mode') == 'beats' and slvl != 'L1':      # шаги с доигрышем — свой потолок поля (05/02 §4.1.1)
                cap = ctx.token_ms('motion.marketing.scroll.pin-beats-max-vh') or cap
            if ctx.forbids(slvl, 'pin-scrub') and scene.get('pin') not in (None, 'none', 'sticky'):
                R.add('error', 'MS-13', w, f'закрепление со скрабом запрещено уровнем {slvl} (только sticky)')
            elif cap and scene.get('pin') not in (None, 'none') and L > cap:
                R.add('error', 'MS-13', w, f'длина сцены {L}vh > {cap:g}vh для {slvl}')
            nst = len(scene.get('stations') or [])
            if nst >= 2 and L / (nst - 1) > 150:
                R.add('warning', 'MS-13', w, f'шаг между станциями {L / (nst - 1):.0f}vh > 150vh')
        if sec['reduce']['strategy'] == 'stations' and not st_ids:
            R.add('error', 'MS-18', w, 'reduce stations без scene.stations')
        if (tr.get('reduce') or {}).get('stations') and st_ids and tr['reduce']['stations'] != len(st_ids):
            R.add('warning', 'MS-17', w, f'treatment.reduce.stations {tr["reduce"]["stations"]} ≠ станций сцены {len(st_ids)}')
        loops = 0
        t_end = 0.0
        tr_effs = {e['ref'] for e in tr.get('effects') or []}
        used_effs = set()
        for m in sec['moments']:
            wm = f'{sid}.{m["id"]}'
            for tg in [m['target']] + list(m.get('stagger_targets') or []):
                if targets is not None and not target_ok(tg, targets, sid):
                    R.add('error', 'MS-03', wm, f'target {tg} не найден (слоты, группы, anatomy, fx-*)')
            if m.get('effect'):
                used_effs.add(m['effect'])
                ce = ctx.effects.get(m['effect'].split(':', 1)[1])
                if ce is None:
                    R.add('error', 'MS-04', wm, f'{m["effect"]} нет в effects.yaml')
                else:
                    kind = (ce.get('motion') or {}).get('kind')
                    kinds = kind if isinstance(kind, list) else [kind]   # motion.kind каталога — строка или список классов
                    if kind and m['class'] not in kinds and 'static' not in kinds:
                        R.add('warning', 'MS-05', wm, f'class {m["class"]} ≠ motion.kind {kind}')
                    if LV[ce['level_min']] > LV[slvl]:
                        R.add('error', 'MS-04', wm, f'{m["effect"]} level_min {ce["level_min"]} > {slvl}')
                    lim = ce.get('limits') or {}
                    sp = (m.get('loop') or {}).get('speed_px_s')
                    if sp is not None and lim.get('speed_px_s_max') and not lim.get('speed_px_s_min', 0) <= sp <= lim['speed_px_s_max']:
                        R.add('error', 'MS-12', wm, f'скорость {sp} px/с вне {lim.get("speed_px_s_min")}–{lim["speed_px_s_max"]}')
            prim = m.get('primitive')
            if prim:
                pr = ctx.primitives.get(prim)
                if pr is None:
                    R.add('error', 'MS-25', wm, f'примитива {prim} нет в наборе движения (11-motion-code/primitives.yaml)')
                else:
                    if LV.get(pr.get('level_min') or 'L0', 0) > LV[slvl]:
                        R.add('error', 'MS-25', wm, f'примитив {prim} — с уровня {pr["level_min"]}, секция {slvl}')
                    pcls = pr.get('class')
                    pcls = pcls if isinstance(pcls, list) else [pcls] if pcls else []
                    if pcls and m['class'] not in pcls:
                        R.add('warning', 'MS-25', wm, f'class {m["class"]} ≠ классу примитива {prim} {pcls}')
                    peff = {e if str(e).startswith('effect:') else f'effect:{e}' for e in pr.get('effects') or []}
                    if m.get('effect') and peff and m['effect'] not in peff:
                        R.add('warning', 'MS-25', wm, f'{m["effect"]} не исполняется примитивом {prim} ({", ".join(sorted(peff))})')
                    opts = primitive_options(pr)
                    extra = sorted(set(m.get('params') or {}) - opts) if opts else []
                    if extra:
                        R.add('warning', 'MS-25', wm, f'параметры {extra} — не опции примитива {prim}: {sorted(opts)}')
            elif not m.get('effect') and not m.get('custom'):
                R.add('warning', 'MS-26', wm, 'момент без опоры: нет примитива набора (primitive), эффекта каталога (effect) и '
                                              'пометки custom — исполнитель соберёт его по памяти')
            elif m.get('effect') and not m.get('custom'):
                eid = m['effect'].split(':', 1)[1]
                by = sorted(k for k, x in ctx.primitives.items() if eid in {str(e).split(':', 1)[-1] for e in x.get('effects') or []})
                if by:
                    R.add('info', 'MS-26', wm, f'{m["effect"]} исполняет примитив набора {", ".join(by)}: укажите primitive')
            for fld in ('duration', 'easing'):
                d = m.get(fld) or {}
                if 'token' in d and d['token'] not in ctx.tokens and d['token'] not in ptok:
                    R.add('error', 'MS-06', wm, f'токена {d["token"]} нет в marketing-tokens.json'
                                                + (' и в токенах движения проекта (refs.tokens)' if ptok else ''))
            pnames = {css_name(k) for k in ptok}
            for tk in m['tracks']:
                for fld in ('duration', 'easing'):
                    d = tk.get(fld) or {}
                    if 'token' in d and d['token'] not in ctx.tokens and d['token'] not in ptok:
                        R.add('error', 'MS-06', wm, f'{tk["property"]}: токена {d["token"]} нет в marketing-tokens.json'
                                                    + (' и в токенах движения проекта (refs.tokens)' if ptok else ''))
                for name in css_vars_of(tk):
                    if (name.startswith('--mm-') or name.startswith('--motion-')) and name not in ctx.motion_css and name not in pnames:
                        hint = short_hint(ctx, name)
                        R.add('error', 'MS-06', wm, f'{tk["property"]}: переменной {name} нет среди токенов движения'
                                                    + (f'; имя токена — {hint}' if hint else ' (имя — `--` + путь токена через дефисы)'))
            if (m.get('stagger') or {}).get('each_share') and m['class'] != 'scroll-linked':
                R.add('warning', 'MS-11', wm, 'stagger.each_share — стаггер по прокрутке, только у scroll-linked')
            d_ms = dur_ms(ctx, m.get('duration'), base, ptok)
            if 'ms' in (m.get('duration') or {}) and d_ms not in scale:
                R.add('warning', 'MS-07', wm, f'{d_ms:g} мс вне шкалы motion.marketing{own} (CRV-MO-14): возьмите токен или долю базы')
            for tk in m['tracks']:
                prop = tk['property']
                if not ctx.prop_ok(slvl, prop, m.get('effect')):
                    norm('MS-08', wm, f'свойство {prop} не разрешено уровнем {slvl} (ambition-levels.yaml motion_hints.properties_allowed)', sid)
                elif page_props and not ctx.prop_in(prop, set(page_props)) and m.get('effect') not in ctx.exc_effects(prop):
                    R.add('error', 'MS-24', wm, f'свойство {prop} вне page.properties_allowed {page_props}')
                bmax = ctx.blur_max(slvl)
                if prop == 'filter' and bmax is not None:
                    for b in re.findall(r'blur\((\d+(?:\.\d+)?)px\)', f'{tk.get("from", "")} {tk.get("to", "")}'):
                        if float(b) > bmax:
                            norm('MS-08', wm, f'blur {b}px > {bmax:g} px для {slvl} (ambition-levels.yaml motion_hints.blur_max_px)', sid)
                if prop == 'opacity' and str(tk.get('from')) in ('0', '0.0') and m['class'] == 'one-shot' and sid == first_flow:
                    R.add('warning', 'MS-19', wm, 'появление из opacity 0 в первом экране: возьмите .01 (кандидат LCP сохраняется — creative 05-motion/02 §10)')
            is_lcp = m.get('lcp') == 'is-lcp' or m['target'] == page['lcp']['target']
            if is_lcp:
                if page['lcp']['entrance'] == 'none':
                    norm('MS-09', wm, f'элемент LCP {page["lcp"]["target"]} анимируется, а page.lcp.entrance = none', sid)
                for tk in m['tracks']:
                    if tk['property'] not in LCP_PROPS:
                        norm('MS-09', wm, f'LCP-элемент: свойство {tk["property"]} (только transform, clip-path или opacity '
                                          f'от {LCP_MIN_RU} — CRV-AL-09 ambition-levels.yaml)', sid)
                    elif tk['property'] == 'opacity':
                        o = track_start(tk)
                        if o is not None and o < LCP_OPACITY_MIN:
                            norm('MS-09', wm, f'LCP-элемент: opacity из {f"{o:g}".replace(".", ",")} (появление — от {LCP_MIN_RU}, '
                                              f'не из 0 — CRV-AL-09 ambition-levels.yaml)', sid)
                    px = px_of(ctx, tk.get('from'))
                    if px is not None and shift_max is not None and px > shift_max:
                        norm('MS-09', wm, f'LCP-элемент: сдвиг {px:g} px > {shift_max:g} (токен distance.shift-hero)', sid)
            if m['class'] == 'one-shot' and m['trigger']['type'] == 'load' and sid == first_flow:
                st = m.get('stagger') or {}
                each = dur_ms(ctx, st.get('each'), base, ptok) or 0
                n = 1 + len(m.get('stagger_targets') or [])
                end = (m['trigger'].get('delay_ms') or 0) + (d_ms or 0) + each * (n - 1)
                t_end = max(t_end, end)
            st = m.get('stagger') or {}
            if st.get('each'):
                each = dur_ms(ctx, st['each'], base, ptok) or 0
                if not 40 <= each <= 80:
                    R.add('warning', 'MS-11', wm, f'стаггер {each:g} мс вне 40–80 (creative 05-motion/01 §7.4)')
                if st.get('max_items') and group_max is not None and each * (st['max_items'] - 1) > group_max:
                    R.add('error', 'MS-11', wm, f'сумма стаггера {each * (st["max_items"] - 1):g} мс > {group_max:g} (токен stagger.group-total-max)')
            if m['class'] == 'loop':
                loops += 1
                per = (m.get('loop') or {}).get('period_ms')
                if per and 2500 <= per <= 6000:
                    fam = (ctx.effects.get((m.get('effect') or ':').split(':', 1)[1]) or {}).get('family')
                    sev = 'error' if fam in ('background', '3d', 'video') else 'warning'
                    R.add(sev, 'MS-15', wm, f'период петли {per:g} мс в полосе 2,5–6 с (вестибулярный риск, creative 05-motion/01 §6.3)')
                if (m.get('pause') or {}).get('control') == 'page-toggle' and not page['toggle'].get('required'):
                    R.add('error', 'MS-14', wm, 'пауза page-toggle, а page.toggle.required = false')
            if m.get('scrub', {}).get('snap') == 'stations' and slvl != 'L2':
                R.add('error', 'MS-13', wm, 'привязка к станциям (snap) — только L2')
        if sid == first_flow and scene_max is not None and t_end > scene_max:
            norm('MS-10', w, f'сцена первого экрана {t_end:g} мс > {scene_max:g} (токен duration.hero-scene-max)', sid)
        lmax = ctx.loops_max(slvl)
        if lmax is not None and loops > lmax:
            R.add('error', 'MS-14', w, f'петель {loops} > {lmax} для {slvl} (ambition-levels.yaml continuous_motions_in_view_max)')
        gids = set()
        if os.path.exists(P['gates']):
            gids = {g.get('id') for g in (load(P['gates']).get('gates') or [])}
        for ac in sec.get('acceptance') or []:
            if ac.get('gate') and gids and ac['gate'] not in gids:
                R.add('warning', 'MS-22', f'{sid}.{ac["id"]}', f'ворот {ac["gate"]} нет в effect-gates.yaml')
        for ef in sorted(tr_effs - used_effs):
            R.add('warning', 'MS-21', w, f'эффект treatment {ef} не описан ни одним моментом')
    if plan:
        for sid, s in psec.items():
            vr = ((s.get('treatment') or {}).get('visual_role'))
            if vr in ('peak', 'accent') and sid not in {x['id'] for x in spec['sections']}:
                R.add('warning', 'MS-16', sid, f'{vr} плана без раздела motion-spec')
    return spec


# ── проекции ───────────────────────────────────────────────────────────────────────────────────────────────
def fmt_dur(ctx, d, base, ptok=None):
    ms = dur_ms(ctx, d, base, ptok)
    return f'{ms:g} ms' if ms is not None else '?'


def fmt_ease(ctx, e, ptok=None):
    if not e:
        return 'no easing'
    if e.get('none'):
        return 'no easing (scrub)'
    if 'css' in e:
        return e['css']
    v = (ptok or {}).get(e.get('token'), ctx.tokens.get(e.get('token')))
    return f'cubic-bezier({", ".join(f"{x:g}" for x in v)})' if isinstance(v, list) else e.get('token', '?')


def fmt_trigger(m, sec):
    t = m['trigger']
    ty = t['type']
    if ty in ('scroll-scrub', 'pin-scrub'):
        if t.get('range_vh'):
            r = t['range_vh']
            s = f'scroll {r.get("start", 0):g}–{r.get("start", 0) + r["length"]:g}vh of #{sec["id"]}'
        elif t.get('progress'):
            s = f'scroll progress {t["progress"]["start"]:g}–{t["progress"]["end"]:g} of #{sec["id"]}'
        else:
            s = f'scroll {t["range"]["start"]} → {t["range"]["end"]} of ' + (f'`{t["subject"]}`' if t.get('subject') else f'#{sec["id"]}')
        return s + (' (pinned)' if ty == 'pin-scrub' else '')
    extra = []
    if t.get('delay_ms'):
        extra.append(f'+{t["delay_ms"]:g} ms')
    if t.get('after'):
        extra.append(f'after {t["after"]}')
    if ty == 'in-view' and t.get('threshold') is not None:
        extra.append(f'{int(t["threshold"] * 100)} % visible, once' if t.get('once', True) else f'{int(t["threshold"] * 100)} % visible')
    return ty + (f' ({", ".join(extra)})' if extra else '')


def fmt_track(ctx, tk, base, ptok=None):
    """Дорожка момента: свойство от → до или ключевые кадры; своя длительность, кривая и задержка свойства; пояснение."""
    s = (f'{tk["property"]} {tk["from"]} -> {tk["to"]}' if 'from' in tk else
         f'{tk["property"]} ' + ' / '.join(f'{k["at"]:g}:{k["value"]}' for k in tk['keyframes']))
    own = ([fmt_dur(ctx, tk['duration'], base, ptok)] if tk.get('duration') else []) + \
          ([fmt_ease(ctx, tk['easing'], ptok)] if tk.get('easing') else []) + \
          ([f'+{tk["delay_ms"]:g} ms'] if tk.get('delay_ms') else [])
    return s + (f' ({", ".join(own)})' if own else '') + (f' [{tk["unit_note"]}]' if tk.get('unit_note') else '')


def moment_tail(ctx, m, base, ptok=None):
    """Части строки момента после времени, кривой и стаггера: пружина, повтор, прерывание, выход, привязка, станции,
    чем собирается (примитив набора, эффект, свой код), откуда числа и заметка."""
    parts = []
    sp = m.get('spring') or {}
    if m.get('model') == 'spring' or sp:
        parts.append('spring' + (' ' + ', '.join(f'{k} {v:g}' for k, v in sp.items()) if sp else ''))
    if m.get('repeat') not in (None, 'once') and m['class'] != 'loop':
        parts.append(f'repeat {m["repeat"]}')
    if (m.get('scrub') or {}).get('snap') not in (None, 'none'):
        parts.append(f'snap to {m["scrub"]["snap"]}')
    if (m.get('stagger') or {}).get('each_share'):
        parts.append(f'scroll stagger {m["stagger"]["each_share"]:g} of the range per item')
    if m.get('interrupt'):
        parts.append(f'interrupt: {m["interrupt"]}')
    ex = m.get('exit') or {}
    if ex:
        parts.append('exit: ' + ', '.join([ex.get('behavior', 'reverse')]
                                         + ([fmt_dur(ctx, ex['duration'], base, ptok)] if ex.get('duration') else [])
                                         + ([fmt_ease(ctx, ex['easing'], ptok)] if ex.get('easing') else [])))
    if m.get('attach'):
        parts.append(f'moves with the {m["attach"]["point"]} point of {m["attach"]["to"]}')
    prm = (' ' + json.dumps(m['params'], ensure_ascii=False)) if m.get('params') else ''
    if m.get('primitive'):
        parts.append(f'motion kit: data-mk="{m["primitive"]}"{prm}' + (f' ({m["effect"]})' if m.get('effect') else ''))
    elif m.get('effect'):
        parts.append(f'effect: {m["effect"]}{prm}')
    if m.get('custom'):
        parts.append(f'own code: {m["custom"]}')
    src = m.get('source') or {}
    if src:
        parts.append(f'numbers from reference {src["ref"]}' + (f'#{src["moment"]}' if src.get('moment') else '')
                     + (f' ({", ".join(src["take"])})' if src.get('take') else ''))
    if m.get('note'):
        parts.append(f'note: {m["note"]}')
    return parts


def moment_line(ctx, m, sec, base, ptok=None):
    """Строка момента для брифа холста; ptok — токены движения проекта (project_motion): их значения идут первыми.
    Части через «; »: триггер → элемент → дорожки, время, кривая, затем стаггер, сокращённое движение, телефон, пауза,
    LCP и хвост moment_tail — описание доходит до исполнителя целиком."""
    el = ', '.join([m['target']] + list(m.get('stagger_targets') or [])) + f' [data-moment={m["id"]}]' + (f' `{m["selector_hint"]}`' if m.get('selector_hint') else '')
    props = ', '.join(fmt_track(ctx, tk, base, ptok) for tk in m['tracks'])
    if m['class'] in ('scroll-linked',):
        timing = 'progress = scroll' + (f', smoothing {m["scrub"]["smoothing_s"]:g} s' if m.get('scrub', {}).get('smoothing_s') else '')
    elif m['class'] == 'loop':
        lp = m.get('loop') or {}
        timing = (f'{lp["speed_px_s"]:g} px/s' if lp.get('speed_px_s') else f'period {lp.get("period_ms", 0):g} ms') + ', infinite'
    else:
        timing = fmt_dur(ctx, m.get('duration'), base, ptok)
    parts = [f'{fmt_trigger(m, sec)} -> {el} -> {props}', timing, fmt_ease(ctx, m.get('easing'), ptok)]
    st = m.get('stagger') or {}
    if st.get('each'):
        parts.append(f'stagger {fmt_dur(ctx, st["each"], base, ptok)} ({st.get("order", "dom")})')
    red = m['reduce']
    parts.append(f'reduced motion: {red["strategy"]}' + (f' — {red["describe"]}' if red.get('describe') else ''))
    if m.get('mobile'):
        parts.append(f'phone: {m["mobile"]["strategy"]}' + (f' — {m["mobile"]["describe"]}' if m['mobile'].get('describe') else ''))
    if m.get('pause', {}).get('control') not in (None, 'not-needed'):
        parts.append(f'pause: {m["pause"]["control"]}')
    if m.get('lcp') == 'is-lcp':
        parts.append('LCP element: transform, clip-path or opacity from 0.01 only')
    return '; '.join(parts + moment_tail(ctx, m, base, ptok))


def cmd_moments(ctx, spec, section=None, ptok=None):
    base = (spec['page'].get('base') or {}).get('duration_ms')
    lines = []
    for sec in spec['sections']:
        if section and sec['id'] != section:
            continue
        for m in sec['moments']:
            lines.append(moment_line(ctx, m, sec, base, ptok))
    for i, l in enumerate(lines, 1):
        print(f'{i}. {l}')
    return lines


def cmd_motion_md(ctx, spec, out=None, ptok=None):
    pg = spec['page']
    base = (pg.get('base') or {}).get('duration_ms')
    L = [f'# MOTION — {spec["id"]}', '',
         f'<!-- motion-spec {spec["motion_spec_version"]} · {spec["checked_at"]} · сгенерировано spec_check.py motion-md; правится спецификация, не этот файл -->', '',
         f'Motion thesis: {pg["thesis"]}']
    if pg.get('character'):
        L.append(f'Character: {", ".join(pg["character"])}.')
    if base:
        L.append(f'Base duration: {base:g} ms; parts use shares of it.')
    if pg.get('primitives'):
        L.append(f'Entrance system (only these primitives): {", ".join(pg["primitives"])}; sections without moments do not animate.')
    lc = pg['lcp']
    L.append(f'LCP element: `{lc["target"]}` — ' + ('no animation at all.' if lc['entrance'] == 'none' else
                                                         'transform (shift ≤ 24 px), clip-path or opacity from 0.01 only; never from opacity 0 or a line mask.'))
    tg = pg['toggle']
    L.append('Motion toggle: ' + (f'required — attribute `data-motion` on <html> with states {", ".join(tg.get("states", []))}; '
                                  f'placement {tg.get("placement", "sticky-header")}; it also pauses every loop.' if tg['required'] else 'not required.'))
    sc = pg.get('scroll') or {}
    L.append('Scrolling: native' + (' + smooth scroll' if sc.get('smooth') else '') + '; never change scroll speed or direction.')
    L.append('Markup contract: data-section="<section id>" on each section, data-slot="<slot id>", data-group="<group-N>", data-fx="<name>" on '
             'decorative elements (targets <section>.fx-<name>), data-moment="<moment id>" on the element a moment moves, data-effect="<effect id>" '
             'for effect modules. Checks find elements by these attributes.')
    L.append('Code: the motion kit (lib/motion-kit.js as a support file, kit CSS in <helmet><style>, MotionKit.mount(root) on mount, '
             'destroy() on unmount; no libraries, no network, no markup built by script). A moment with "motion kit" uses that '
             'primitive markup (data-mk and its options); own code only where a moment says "own code".')
    allowed = pg.get('properties_allowed')
    if allowed:
        L.append(f'Animate only: {", ".join(allowed)}. Never width, height, top, left, margin, padding; never `transition: all`.')
    for n in pg.get('never') or []:
        L.append(f'- Never: {n}')
    L.append('')
    for sec in spec['sections']:
        L.append(f'## #{sec["id"]} — {sec["role"]}' + (f' · {sec["intent"]}' if sec.get('intent') else ''))
        scn = sec.get('scene') or {}
        if scn:
            L.append(f'Scene: pin {scn.get("pin", "none")}, length {scn.get("length_vh", "—")}vh (phone {scn.get("length_vh_mobile", "—")}vh).')
            for stt in scn.get('stations') or []:
                pos = f'at {stt["at"]:g}' if 'at' in stt else f'when `{stt["anchor"]}` is at {stt.get("anchor_line", "viewport-center")}'
                L.append(f'- station {stt["id"]} {pos}: {stt["describe"]}')
        if sec['moments']:
            L += ['', '| # | moment | class | trigger → element → property | time / range | easing | built with | reduced motion | phone |',
                  '|---|---|---|---|---|---|---|---|---|']
            tails = []
            for i, m in enumerate(sec['moments'], 1):
                props = '; '.join(fmt_track(ctx, tk, base, ptok).replace(' -> ', ' → ') for tk in m['tracks'])
                timing = moment_line(ctx, m, sec, base, ptok).split('; ')[1]
                built = (f'kit `{m["primitive"]}`' if m.get('primitive') else m.get('effect') or '') + (' + own code' if m.get('custom') else '')
                L.append(f'| {i} | {m["id"]} | {m["class"]} | {fmt_trigger(m, sec)} → `{m["target"]}` → {props} | {timing} | {fmt_ease(ctx, m.get("easing"), ptok)} | '
                         f'{built or "—"} | {m["reduce"]["strategy"]} | {(m.get("mobile") or {}).get("strategy", "same")} |')
                tail = [x for x in moment_tail(ctx, m, base, ptok) if not x.startswith(('motion kit:', 'effect:'))]
                if tail:
                    tails.append(f'- {m["id"]}: ' + '; '.join(tail))
            if tails:
                L += [''] + tails
        L.append('')
        L.append(f'Reduced motion for the section: {sec["reduce"]["strategy"]} — {sec["reduce"]["describe"]}')
        L.append(f'Phone: {sec["mobile"]["strategy"]} — {sec["mobile"]["describe"]}')
        fb = sec.get('fallback') or {}
        if fb:
            L.append('Fallback: ' + '; '.join(f'{k.replace("_", " ")} — {v}' for k, v in fb.items() if v))
        for fr in (sec.get('storyboard') or {}).get('frames') or []:
            at = ', '.join(f'{k} {v}' for k, v in fr['at'].items())
            L.append(f'- frame {fr["id"]} ({fr["viewport"]}, {at}): {fr["describe"]}' + (f' Check: {fr["check"]}' if fr.get('check') else ''))
        for rf in sec.get('references') or []:
            L.append(f'- reference {rf["id"]} ({rf["kind"]}{", " + rf["file"] if rf.get("file") else ""}):')
            for tk in rf['take']:
                span = f'{tk.get("from", "")}–{tk.get("to", "")} ' if tk.get('from') else ''
                L.append(f'  - Take {span}{tk["what"]}')
            for d in rf['do_not_take']:
                L.append(f'  - Do not take: {d}')
        L.append('')
    txt = '\n'.join(L)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(txt)
    else:
        print(txt)
    return txt


def cmd_values(ctx, spec, out, ptok=None):
    os.makedirs(out, exist_ok=True)
    base = (spec['page'].get('base') or {}).get('duration_ms')
    files = []
    for sec in spec['sections']:
        d = {'spec': spec['id'], 'checked_at': spec['checked_at'], 'section': sec['id'], 'scene': sec.get('scene') or {}, 'moments': {}}
        for m in sec['moments']:
            e = m.get('easing') or {}
            ez = (ptok or {}).get(e['token'], ctx.tokens.get(e['token'])) if e.get('token') else e.get('css')
            mv = {'class': m['class'], 'duration_ms': dur_ms(ctx, m.get('duration'), base, ptok), 'easing': ez,
                  'stagger_ms': dur_ms(ctx, (m.get('stagger') or {}).get('each'), base, ptok), 'trigger': m['trigger'],
                  'tracks': m['tracks'], 'reduce': m['reduce']['strategy']}
            for k in ('loop', 'scrub', 'spring', 'params', 'primitive', 'effect', 'custom', 'source', 'exit', 'interrupt', 'attach'):
                if m.get(k):
                    mv[k] = m[k]
            if m.get('tunable'):
                mv['tunable'] = m['tunable']
            d['moments'][m['id']] = mv
        p = os.path.join(out, f'{sec["id"]}.motion.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        files.append(p)
    print('\n'.join(files))
    return files


def effect_levels(ctx):
    out = {'L1': [], 'L2': []}
    for eid, e in ctx.effects.items():
        if e['level_min'] in out:
            out[e['level_min']].append(f'effect:{eid}')
    return out


def effect_props(e, vocab):
    """Свойства приёма каталога для сверки с уровнем: машинный список motion.properties; без него — записи
    описательного motion.props, которые без пояснения в скобках входят в словарь track.property (vocab)."""
    mo = e.get('motion') or {}
    if isinstance(mo.get('properties'), list):
        return [str(p) for p in mo['properties']]
    out = []
    for p in mo.get('props') or []:
        tok = str(p).split('(')[0].strip()
        if vocab.match(tok):
            out.append(tok)
    return out


def cmd_levels(ctx, R=None):
    """Списки effect:<id> по level_min; с R — сверка x-effect-levels и условий L0, L1 treatment.schema.json с каталогом
    (LV-01, LV-02) и свойств каждого приёма с его минимальным уровнем: свойство разрешено уровнем или исключением
    файла уровней (LV-03)."""
    out = effect_levels(ctx)
    if R is None:
        print(json.dumps(out, ensure_ascii=False))
        return out
    t = load(P['t_schema'])
    xl = t.get('x-effect-levels') or {}
    for lvl in ('L1', 'L2'):
        have = xl.get(f'level_min_{lvl}') or []
        if have != out[lvl]:
            R.add('error', 'LV-01', f'x-effect-levels.level_min_{lvl}',
                  f'не как в effects.yaml: лишние {sorted(set(have) - set(out[lvl]))}, нет {sorted(set(out[lvl]) - set(have))}')
    cond = {}
    for c in t.get('allOf') or []:
        lv_ = (((c.get('if') or {}).get('properties') or {}).get('level') or {}).get('const')
        eff = (((((c.get('then') or {}).get('properties') or {}).get('effects') or {}).get('items') or {}).get('properties') or {}).get('ref')
        if lv_ and eff:
            cond[lv_] = (eff.get('not') or {}).get('enum')
    for lvl, want in (('L0', out['L1'] + out['L2']), ('L1', out['L2'])):
        if cond.get(lvl) != want:
            R.add('error', 'LV-02', f'allOf {lvl}', 'перечень запрещённых эффектов не как в effects.yaml (пересоберите: spec_check.py levels)')
    vocab = re.compile(load(P['m_schema'])['$defs']['track']['properties']['property']['pattern'])
    for eid, e in ctx.effects.items():
        for prop in effect_props(e, vocab):
            if not ctx.prop_ok(e['level_min'], prop, f'effect:{eid}'):
                R.add('error', 'LV-03', f'effects.{eid}', f'свойство {prop} на минимальном уровне {e["level_min"]} не разрешено уровнем и не '
                      'названо исключением (ambition-levels.yaml: motion_hints.properties_allowed, property_exceptions)')
    return out


# ── проекция во вход холста: форма x-canvas-map и покрытие полей ─────────────────────────────────────────────
def canvas_files():
    """Файлы kb с ключом x-canvas-map: схемы (*.schema.json, *.schema.yaml) и файл уровней."""
    out = []
    for f in sorted(glob.glob(os.path.join(APP, '**', '*'), recursive=True)):
        if '/99-raw/' in f or not os.path.isfile(f):
            continue
        if not (f.endswith(('.schema.json', '.schema.yaml', '.schema.yml')) or os.path.abspath(f) == os.path.abspath(P['levels'])):
            continue
        with open(f, encoding='utf-8') as fh:
            if 'x-canvas-map' in fh.read():
                out.append(f)
    return out


def split_ptr(ptr):
    return [x.replace('~1', '/').replace('~0', '~') for x in ptr.split('/')[1:]] if ptr else []


def ptr_match(q, p):
    """Указатель правила q покрывает путь p: q — префикс p; «*» с любой стороны совпадает с элементом списка."""
    return len(q) <= len(p) and all(a == b or a == '*' or b == '*' for a, b in zip(q, p))


def schema_paths(doc, roots):
    """Все пути полей схемы от корней roots {указатель схемы: префикс в источнике}; листья — отдельным списком."""
    nodes, leaves = [], []

    def deref(n, seen=0):
        while isinstance(n, dict) and isinstance(n.get('$ref'), str) and n['$ref'].startswith('#/') and seen < 20:
            cur = doc
            for part in split_ptr(n['$ref'][1:]):
                cur = cur.get(part, {}) if isinstance(cur, dict) else {}
            n, seen = cur, seen + 1
        return n if isinstance(n, dict) else {}

    def walk(n, path, depth=0):
        n = deref(n)
        nodes.append(path)
        props = n.get('properties')
        if isinstance(props, dict) and props and depth < 30:
            for k, sub in props.items():
                walk(sub, path + [k], depth + 1)
            return
        it = n.get('items')
        if isinstance(it, dict):
            itd = deref(it)
            if isinstance(itd.get('properties'), dict) and itd['properties']:
                walk(itd, path + ['*'], depth + 1)
                return
        leaves.append(path)
    for sch, prefix in roots.items():
        node = doc if sch in ('#', '') else deref({'$ref': sch})
        walk(node, split_ptr(prefix))
    return nodes, leaves


def data_paths(doc):
    nodes, leaves = [], []

    def walk(x, path):
        nodes.append(path)
        if isinstance(x, dict) and x:
            for k, v in x.items():
                if not path and str(k).startswith('x-'):
                    continue
                walk(v, path + [str(k)])
            return
        if isinstance(x, list) and x and all(isinstance(i, dict) for i in x):
            for i in x:
                walk(i, path + ['*'])
            return
        leaves.append(path)
    walk(doc, [])
    return nodes, leaves


def own_pointers(m):
    """Указатели карты на свой документ-источник (без префикса <документ>#) — из правил файлов и drop; base — корни
    подсхемы внутри чужого документа: поддерево целиком покрыто картой подсхемы (для покрытия карт того же source)."""
    out = [split_ptr(v) for v in (m.get('base') or {}).values() if isinstance(v, str) and v]
    for fields in (m.get('files') or {}).values():
        for r in (fields or {}).values() if isinstance(fields, dict) else []:
            out += [split_ptr(q) for q in (r.get('from') or []) if isinstance(r, dict) and isinstance(q, str) and '#' not in q]
    for dr in m.get('drop') or []:
        out += [split_ptr(q) for q in (dr.get('from') or []) if isinstance(dr, dict) and isinstance(q, str) and '#' not in q]
    return out


def canvas_check(path, m, R, doc=None, shared=()):
    """Форма x-canvas-map и покрытие: у каждого поля источника есть правило (сам указатель или предок). shared —
    указатели других карт того же source: подсхема чужого документа (treatment в page-plan) покрывает свои поля сама."""
    w = os.path.relpath(path, APP) if path else 'x-canvas-map'
    if not isinstance(m, dict):
        R.add('error', 'CM-01', w, 'x-canvas-map — не объект')
        return
    if not isinstance(m.get('source'), str) or not m.get('source'):
        R.add('error', 'CM-01', w, 'нет source — id документа-источника')
    stages = m.get('stages')
    if not isinstance(stages, list) or not stages or any(x not in STAGES for x in stages):
        R.add('error', 'CM-01', w, f'stages — непустой список из {STAGES}')
        stages = list(STAGES)
    files = m.get('files')
    if not isinstance(files, dict) or not files:
        R.add('error', 'CM-01', w, 'files — объект «файл входа → поле холста → правило»')
        files = {}
    own = []

    def take(ptrs, where):
        if not isinstance(ptrs, list):
            R.add('error', 'CM-02', where, 'from — список указателей')
            return
        for q in ptrs:
            if not isinstance(q, str) or not POINTER.match(q):
                R.add('error', 'CM-02', where, f'указатель {q!r} — не [<документ>#]<JSON Pointer>')
            elif '#' not in q:
                own.append((split_ptr(q), where, q))
    for fname, fields in files.items():
        if not isinstance(fields, dict) or not fields:
            R.add('error', 'CM-01', f'{w}:{fname}', 'у файла входа нет полей')
            continue
        for fld, r in fields.items():
            wf = f'{w}:{fname}:{fld}'
            if not isinstance(r, dict):
                R.add('error', 'CM-02', wf, 'правило — объект {rule, from, note}')
                continue
            extra = set(r) - {'rule', 'from', 'note', 'stages', 'values'}
            if extra:
                R.add('error', 'CM-02', wf, f'лишние ключи правила: {sorted(extra)}')
            if r.get('rule') not in RULES:
                R.add('error', 'CM-02', wf, f'rule {r.get("rule")!r} — не из {RULES}')
            take(r.get('from'), wf)
            if r.get('rule') == 'claude_fills' and r.get('from'):
                R.add('error', 'CM-02', wf, 'claude_fills — у поля нет источника: from пустой')
            if r.get('rule') != 'claude_fills' and not r.get('from'):
                R.add('error', 'CM-02', wf, 'from пустой: источник поля не назван')
            if r.get('rule') in ('map', 'derive', 'drop', 'claude_fills') and not r.get('note'):
                R.add('error', 'CM-02', wf, f'правило {r.get("rule")} без note')
            if r.get('stages') is not None and (not isinstance(r['stages'], list) or any(x not in stages for x in r['stages'])):
                R.add('error', 'CM-02', wf, f'stages правила — подмножество stages файла {stages}')
            if 'values' in r and (r.get('rule') != 'map' or not isinstance(r['values'], dict)):
                R.add('error', 'CM-02', wf, 'values — словарь перевода только у map')
    for i, dr in enumerate(m.get('drop') or []):
        wd = f'{w}:drop[{i}]'
        if not isinstance(dr, dict) or not dr.get('note'):
            R.add('error', 'CM-02', wd, 'drop — {from, note}: причина обязательна')
            continue
        take(dr.get('from'), wd)
    base = m.get('base') or {'#': ''}
    if doc is None:
        return
    if isinstance(doc.get('properties'), dict):
        nodes, leaves = schema_paths(doc, base)
    else:
        nodes, leaves = data_paths(doc)
    for q, where, raw in own:
        if not any(ptr_match(q, n) and len(q) == len(n) for n in nodes):
            R.add('error', 'CM-03', where, f'указатель {raw} не находит поля источника')
    cover = [q for q, _, _ in own] + list(shared)
    miss = ['/' + '/'.join(p) for p in leaves if not any(ptr_match(q, p) for q in cover)]
    for p in sorted(set(miss)):
        R.add('error', 'CM-04', w, f'поле источника без правила: {p}')


def cmd_canvas_map(R, files=None):
    every = {f: load(f) for f in canvas_files()}
    files = files or list(every)
    for f in files:
        doc = every.get(f) or load(f)
        if 'x-canvas-map' not in doc:
            R.add('error', 'CM-01', os.path.relpath(f, APP), 'нет ключа x-canvas-map')
            continue
        src = (doc['x-canvas-map'] or {}).get('source')
        shared = [q for g, d in every.items() if g != f and isinstance(d.get('x-canvas-map'), dict)
                  and d['x-canvas-map'].get('source') == src for q in own_pointers(d['x-canvas-map'])]
        canvas_check(f, doc['x-canvas-map'], R, doc, shared)
        R.add('info', 'CM-00', os.path.relpath(f, APP), f'правил: {sum(len(v) for v in (doc["x-canvas-map"].get("files") or {}).values())}, drop: {len(doc["x-canvas-map"].get("drop") or [])}')
    return R


# ── самопроверка ───────────────────────────────────────────────────────────────────────────────────────────
EX = os.path.join(ROOT, '09-ai-execution-evaluation', 'examples')


def example(name):
    """План site, overlay и спецификация примера базы по имени (otves, okoshko, stalkon)."""
    ov = os.path.join(EX, f'{name}-home.treatment.yaml')
    plan = os.path.normpath(os.path.join(EX, load(ov)['plan']))
    return plan, ov, os.path.join(EX, f'{name}-home.motion-spec.yaml')


def codes(R, sev='error'):
    return {i[1] for i in R.items if i[0] == sev}


def levels_copy(tmp, mutate, top=None):
    """Копия файла уровней: mutate правит уровни по id, top — ключи верхнего уровня (property_exceptions)."""
    lv = load(P['levels'])
    mutate({L['id']: L for L in lv['levels']})
    if top:
        top(lv)
    p = os.path.join(tmp, 'ambition-levels.yaml')
    with open(p, 'w', encoding='utf-8') as f:
        yaml.safe_dump(lv, f, allow_unicode=True, sort_keys=False)
    return p


def selftest(ctx):
    import tempfile
    ok = True

    def expect(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(f'{"OK  " if cond else "FAIL"} {name}')
    for key in ('t_schema', 'm_schema'):
        Draft202012Validator.check_schema(load(P[key]))
    R = cmd_blocks(ctx, Report())
    expect('blocks: 0 error', not codes(R))
    tv = Draft202012Validator(load(P['t_schema']))
    bad = [({'level': 'L0', 'effects': [{'ref': 'effect:pin-scrub-story'}], 'reduce': {'strategy': 'final-state'}, 'mobile': {'strategy': 'static'}}, 'L0 + pin'),
           ({'visual_role': 'peak', 'effects': [{'ref': 'effect:sticky-stack', 'purpose': 'support'}], 'reduce': {'strategy': 'final-state'}, 'mobile': {'strategy': 'same'}}, 'peak без signature'),
           ({'composition': {'text_media': 'text-over'}}, 'text-over без text_contrast'),
           ({'background': {'kind': 'video-loop'}, 'mobile': {'strategy': 'poster'}}, 'видео без flash_check'),
           ({'motion_level': 'cinematic', 'reduce': {'strategy': 'final-state'}}, 'cinematic без ролика')]
    for doc, name in bad:
        expect(f'treatment «{name}»: схема ловит', list(tv.iter_errors(doc)))
    mom = Draft202012Validator({'$ref': '#/$defs/moment', '$defs': load(P['m_schema'])['$defs']})
    m_bad = {'id': 'x', 'class': 'one-shot', 'purpose': 'guide', 'target': 'hero.headline', 'lcp': 'is-lcp', 'trigger': {'type': 'load'},
             'tracks': [{'property': 'opacity', 'from': 0, 'to': 1}], 'duration': {'ms': 600}, 'reduce': {'strategy': 'final-state'}}
    expect('motion-spec «LCP из opacity»: схема ловит', list(mom.iter_errors(m_bad)))
    m_defs = load(P['m_schema'])['$defs']
    scene_v = Draft202012Validator({'$defs': m_defs, **m_defs['section']['properties']['scene']})
    st7 = [{'id': f'beat-{i}', 'at': round(i / 6, 3), 'describe': f'точка покоя {i}'} for i in range(7)]
    expect('motion-spec: 7 точек покоя у шагов с доигрышем (scroll_mode: beats) — схема пропускает',
           not list(scene_v.iter_errors({'scroll_mode': 'beats', 'pin': 'sticky', 'length_vh': 450, 'stations': st7})))
    expect('motion-spec: 7 станций у скраба — схема ловит (2–6)',
           list(scene_v.iter_errors({'pin': 'sticky', 'length_vh': 450, 'stations': st7})))
    expect('токен потолка шагов с доигрышем pin-beats-max-vh — 450vh',
           ctx.token_ms('motion.marketing.scroll.pin-beats-max-vh') == 450)
    for tracks, name, clean in (([{'property': 'clip-path', 'from': 'inset(0 0 100% 0)', 'to': 'inset(0 0 0 0)'}], 'clip-path', True),
                                ([{'property': 'opacity', 'from': 0.01, 'to': 1}], 'opacity от 0,01', True),
                                ([{'property': 'opacity', 'keyframes': [{'at': 0, 'value': 0}, {'at': 1, 'value': 1}]}], 'opacity из 0 первым кадром', False),
                                ([{'property': 'mask', 'from': 'linear-gradient(#000 0 0)', 'to': 'none'}], 'mask', False)):
        expect(f'motion-spec, вход LCP — {name}: схема {"пропускает" if clean else "ловит"}',
               bool(list(mom.iter_errors(dict(m_bad, tracks=tracks)))) != clean)
    for name in ('otves', 'okoshko', 'stalkon'):
        plan, ov, sp = example(name)
        Rp, Rs = Report(), Report()
        cmd_plan(ctx, Rp, plan, ov, spec=load(sp))
        cmd_spec(ctx, Rs, sp, plan, ov)
        expect(f'пример {name}: plan и spec — 0 error', not codes(Rp) and not codes(Rs))
    R = Report()
    cmd_levels(ctx, R)
    expect('levels --check: x-effect-levels, условия L0, L1 и свойства приёмов на минимальном уровне — как в effects.yaml', not codes(R))

    def lv03(c, motion):
        """Находки LV-03 у вымышленного приёма уровня L0 с полем motion."""
        c.effects = dict(c.effects, **{'demo-fade': {'id': 'demo-fade', 'level_min': 'L0', 'motion': motion}})
        R_ = Report()
        cmd_levels(c, R_)
        return [i[3] for i in R_.items if i[1] == 'LV-03' and i[2] == 'effects.demo-fade']
    found = lv03(Ctx(), {'properties': ['opacity', 'filter']})
    expect('levels --check: свойство приёма вне его минимального уровня → LV-03 (свойство уровня — чисто)',
           len(found) == 1 and 'filter' in found[0])
    found = lv03(Ctx(), {'props': ['filter (затемнение)', 'textContent']})
    expect('levels --check: без машинного списка сверяются записи motion.props из словаря track.property',
           len(found) == 1 and 'filter' in found[0])
    for ref in ('motion.marketing.distance.shift-hero', 'motion.marketing.duration.hero-scene-max', 'motion.marketing.stagger.group-total-max'):
        expect(f'токен {ref} есть', ctx.token_ms(ref) is not None)
    mq = (ctx.effects.get('marquee-logos') or {}).get('limits') or {}
    tok = load(P['tokens'])['motion']['marketing']['loop']['marquee-speed']['$value']
    expect('токен loop.marquee-speed в пределах marquee-logos.limits', mq.get('speed_px_s_min', 0) <= tok <= mq.get('speed_px_s_max', 0))
    # числа уровней — из файла уровней: копия с другим значением меняет вердикт
    plan, ov, sp = example('otves')
    with tempfile.TemporaryDirectory() as tmp:
        c2 = Ctx(levels_copy(tmp, lambda L: L['L1']['section_distribution'].update(peaks_max=0)))
        R = Report()
        cmd_plan(c2, R, plan, ov, spec=load(sp))
        expect('копия уровней: пиков L1 ≤ 0 → TR-04 warning (норма облика — доклад)',
               'TR-04' in codes(R, 'warning') and 'TR-04' not in codes(R))
        c3 = Ctx(levels_copy(tmp, lambda L: L['L1']['motion_hints'].update(properties_allowed=['opacity', 'color'])))
        R = Report()
        cmd_spec(c3, R, sp, plan, ov)
        expect('копия уровней: без transform у L1 → MS-08 и MS-23', {'MS-08', 'MS-23'} <= codes(R))
        c4 = Ctx(levels_copy(tmp, lambda L: L['L1']['motion_hints'].update(continuous_motions_in_view_max={'mobile': 0, 'desktop': 0})))
        pl = load(plan)
        for s_ in pl['sections']:
            if s_['id'] == 'hero':
                s_.setdefault('treatment', {}).update(loops=1, loop_control='stops-within-5s')
        p2 = os.path.join(tmp, 'plan.yaml')
        with open(p2, 'w', encoding='utf-8') as f:
            yaml.safe_dump(pl, f, allow_unicode=True, sort_keys=False)
        R0, R1 = Report(), Report()
        cmd_plan(ctx, R0, p2)
        cmd_plan(c4, R1, p2)
        expect('копия уровней: петель L1 ≤ 0 → TR-21 warning (с файлом базы — нет)',
               'TR-21' in codes(R1, 'warning') and 'TR-21' not in codes(R1) | codes(R0, 'warning'))
        # тяжесть: нормы облика — warning, схема плана и уровень эффекта — error
        pl = merge_overlay(load(plan), load(ov), Report())
        secs = {s_['id']: s_ for s_ in pl['sections']}
        secs['hero']['treatment']['level'] = 'L2'
        p3 = os.path.join(tmp, 'plan-norms.yaml')
        with open(p3, 'w', encoding='utf-8') as f:
            yaml.safe_dump(pl, f, allow_unicode=True, sort_keys=False)
        R = Report()
        cmd_plan(ctx, R, p3, spec=load(sp))
        expect('норма облика — доклад: секция L2 на странице L1 → TR-01 warning, 0 error',
               'TR-01' in codes(R, 'warning') and not codes(R))
        crit0 = {k: {'result': 'pass'} for k in ('concept', 'brand', 'execution', 'epoch', 'singularity')}
        pl['page']['treatment']['art_direction_ref'] = 'art-direction.json#/directions/0'
        with open(p3, 'w', encoding='utf-8') as f:
            yaml.safe_dump(pl, f, allow_unicode=True, sort_keys=False)
        pid = page_id_of(pl, p3)

        def plan_lift(records, rule='TR-01'):
            """Находки правила rule у плана p3 с записями lifted_markers арт-дирекции рядом с ним."""
            ad_ = {'decisions': [{'id': 'd-hero-level', 'technique': 'уровень первого экрана', 'decision': 'use', 'criteria': crit0,
                                  'why': 'заказчик выбрал подачу первого экрана на прототипе'}],
                   'exclusions': {'lifted_markers': records}}
            with open(os.path.join(tmp, 'art-direction.json'), 'w', encoding='utf-8') as f:
                json.dump(ad_, f, ensure_ascii=False)
            R_ = Report()
            cmd_plan(ctx, R_, p3, spec=load(sp))
            return [i for i in R_.items if i[1] == rule]
        got = plan_lift([{'marker': 'TR-01', 'decision_ref': 'd-hero-level'}])
        expect('норма подачи с записью арт-дирекции: TR-01 — warning «принято решением арт-дирекции d-hero-level»',
               got and all(i[0] == 'warning' and 'принято решением арт-дирекции d-hero-level' in i[3] for i in got))
        got = plan_lift([{'marker': 'TR-01', 'decision_ref': 'd-hero-level', 'page': 'other-page'}])
        expect('норма подачи: запись с page другой страницы её не снимает', got and all('принято решением' not in i[3] for i in got))
        got = plan_lift([{'marker': 'TR-01', 'decision_ref': 'd-hero-level', 'page': pid, 'section': 'hero'}])
        expect('норма подачи: запись с page и section находки снимает её', got and all('d-hero-level' in i[3] for i in got))
        got = plan_lift([{'marker': 'TR-01', 'decision_ref': 'd-hero-level', 'section': 'how-it-works'}])
        expect('норма подачи: запись с section другой секции её не снимает', got and all('принято решением' not in i[3] for i in got))
        got = plan_lift([{'marker': 'TR-01', 'decision_ref': 'd-no-such-decision'}])
        expect('норма подачи: decision_ref в пустоту — warning с причиной, без «принято»',
               got and all(i[0] == 'warning' and 'd-no-such-decision нет в decisions' in i[3] for i in got))
        secs['how-it-works']['treatment']['effects'].append({'ref': 'effect:smooth-scroll'})
        pl['page']['design_system'] = {'style': 'x'}
        with open(p3, 'w', encoding='utf-8') as f:
            yaml.safe_dump(pl, f, allow_unicode=True, sort_keys=False)
        R = Report()
        cmd_plan(ctx, R, p3, spec=load(sp))
        expect('уровень эффекта и схема плана — error: эффект L2 в секции L1 → TR-11, чужой ключ → TR-S',
               {'TR-11', 'TR-S'} <= codes(R))
        got = plan_lift([{'marker': 'TR-11', 'decision_ref': 'd-hero-level'}], 'TR-11')
        expect('уровень эффекта решением не снимается: TR-11 с записью — error', got and all(i[0] == 'error' for i in got))
        # сводка ритма страницы выводится из секций: план без списков — чисто, разошедшийся список — warning
        pl = merge_overlay(load(plan), load(ov), Report())
        for k in ('peaks', 'accents', 'signature_sections'):
            pl['page']['treatment'].pop(k, None)
        p4 = os.path.join(tmp, 'plan-lists.yaml')

        def plan_run(c=ctx):
            with open(p4, 'w', encoding='utf-8') as f:
                yaml.safe_dump(pl, f, allow_unicode=True, sort_keys=False)
            R_ = Report()
            cmd_plan(c, R_, p4, spec=load(sp))
            return R_
        R = plan_run()
        expect('план без списков peaks, accents, signature_sections: 0 error, TR-07 и TR-08 нет',
               not codes(R) and not {'TR-07', 'TR-08'} & codes(R, 'warning'))
        pl['page']['treatment']['peaks'] = ['hero']
        R = plan_run()
        expect('список peaks, разошедшийся с секциями: TR-07 warning', 'TR-07' in codes(R, 'warning') and 'TR-07' not in codes(R))
        pl['page']['treatment'].pop('peaks')
        # наложение-просмотр: эффект поля viewer разрешается в каталоге
        hero_t = next(s_ for s_ in pl['sections'] if s_['id'] == 'hero')['treatment']
        hero_t['viewer'] = {'effect': 'effect:' + next(k for k, e_ in ctx.effects.items() if e_['level_min'] == 'L0'), 'note': 'окно кадра по клику'}
        R = plan_run()
        expect('наложение-просмотр с эффектом каталога: 0 error', not codes(R))
        hero_t['viewer'] = {'effect': 'effect:no-such-effect'}
        R = plan_run()
        expect('наложение-просмотр: эффекта нет в каталоге → TR-10', any(i[1] == 'TR-10' and i[2] == 'hero.viewer' for i in R.items))
        hero_t.pop('viewer')
        # класс эффекта секции сверяется со списком классов каталога
        eff0 = next(e_ for e_ in hero_t['effects'] if e_['ref'].split(':', 1)[1] in ctx.effects)
        eid0 = eff0['ref'].split(':', 1)[1]
        k0 = ctx.effects[eid0]['motion']['kind']
        k0 = k0 if isinstance(k0, list) else [k0]
        eff0['class'] = next(k for k in ('loop', 'pointer', 'transition') if k not in k0)
        c_kind = Ctx()
        c_kind.effects = dict(c_kind.effects, **{eid0: dict(ctx.effects[eid0], motion=dict(ctx.effects[eid0]['motion'], kind=k0 + [eff0['class']]))})
        expect('класс эффекта вне motion.kind каталога → TR-18; класс из списка классов — чисто',
               'TR-18' in codes(plan_run(), 'warning') and 'TR-18' not in codes(plan_run(c_kind), 'warning'))
    # нормы движения, снятые решением арт-дирекции: копия примера с четырьмя отступлениями и арт-дирекция рядом с ней.
    # Уровни — копией без исключения clip-path и с ним: вердикт случаев не зависит от состава property_exceptions базы
    with tempfile.TemporaryDirectory() as tmp:
        c_plain = Ctx(levels_copy(tmp, lambda L: None, lambda t: (t.get('property_exceptions') or {}).pop('clip-path', None)))
        c_exc = Ctx(levels_copy(tmp, lambda L: None, lambda t: t.setdefault('property_exceptions', {}).update({'clip-path': ['effect:mask-reveal']})))
        doc = load(sp)
        doc['refs']['art_direction'] = 'art-direction.json#/directions/0'
        doc['page']['properties_allowed'] = list(doc['page']['properties_allowed']) + ['currentTime']       # MS-23: шире L1
        hero = next(s_ for s_ in doc['sections'] if s_['id'] == 'hero')
        hero['level'] = 'L0'
        moms = {m_['id']: m_ for m_ in hero['moments']}
        frame, rise = moms['hero-photo-settle'], moms['hero-copy-rise']
        frame.pop('lcp')                                                                                    # LCP — по цели page.lcp.target
        frame['tracks'] = [{'property': 'filter', 'from': 'brightness(0.3)', 'to': 'brightness(1)'}]        # MS-09 и MS-08 (filter на L0)
        rise['effect'] = 'effect:mask-reveal'
        rise['tracks'] = [{'property': 'clip-path', 'from': 'inset(100% 0 0 0)', 'to': 'inset(0 0 0 0)'}]   # MS-08 (clip-path на L0)
        rise['trigger']['delay_ms'] = 2000                                                                  # MS-10
        p_spec = os.path.join(tmp, 'home.motion-spec.yaml')
        crit = {k: {'result': 'pass'} for k in ('concept', 'brand', 'execution', 'epoch', 'singularity')}
        decisions = [{'id': 'd-frame-light', 'technique': 'effect:mask-reveal', 'decision': 'use', 'criteria': crit,
                      'why': 'заказчик выбрал подачу первого экрана на прототипе', 'where': 'hero'},
                     {'id': 'd-other-page', 'technique': 'effect:mask-reveal', 'decision': 'use', 'criteria': crit,
                      'why': 'заказчик принял подачу другой страницы на прототипе'}]

        def lifted_run(c, markers, ref=True):
            """Находки spec у копии с отступлениями; markers — записи lifted_markers: (marker, decision_ref) и, при
            области, (marker, decision_ref, page, section) — None у page или section поле не пишет."""
            keys = ('marker', 'decision_ref', 'page', 'section')
            ad = {'decisions': decisions,
                  'exclusions': {'lifted_markers': [{k: v for k, v in zip(keys, rec) if v is not None} for rec in markers]}}
            with open(os.path.join(tmp, 'art-direction.json'), 'w', encoding='utf-8') as f:
                json.dump(ad, f, ensure_ascii=False)
            d = copy.deepcopy(doc)
            if not ref:
                d['refs'].pop('art_direction')
            with open(p_spec, 'w', encoding='utf-8') as f:
                yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
            R = Report()
            cmd_spec(c, R, p_spec, plan, ov)
            return R, ad
        every = [(k, 'd-frame-light') for k in LIFTABLE]
        R0, _ = lifted_run(c_plain, [])
        R1, ad1 = lifted_run(c_plain, every)
        R2, _ = lifted_run(c_plain, [(k, 'd-no-such-decision') for k in LIFTABLE])
        for k in LIFTABLE:
            expect(f'снятая норма {k}: записи нет → error', k in codes(R0))
            expect(f'снятая норма {k}: запись с решением → warning «принято решением арт-дирекции d-frame-light»',
                   k in codes(R1, 'warning') and k not in codes(R1)
                   and all('принято решением арт-дирекции d-frame-light' in i[3] for i in R1.items if i[1] == k))
            expect(f'снятая норма {k}: decision_ref в пустоту → error с причиной',
                   k in codes(R2) and k not in codes(R2, 'warning')
                   and all('d-no-such-decision нет в decisions' in i[3] for i in R2.items if i[1] == k))
        expect('снятые нормы: четыре записи с решением → 0 error у копии с отступлениями', not codes(R1))
        ad_s = load(P['ad_schema'])
        adv = Draft202012Validator({'properties': {k: ad_s['properties'][k] for k in ('decisions', 'exclusions')}, '$defs': ad_s['$defs']})
        expect('снятые нормы: записи (marker — id правила) проходят схему арт-дирекции', not list(adv.iter_errors(ad1)))
        R, _ = lifted_run(c_plain, [('MS-08', 'd-frame-light')])
        expect('у каждого правила своя запись: примета MS-08 не снимает MS-09, MS-10, MS-23',
               'MS-08' in codes(R, 'warning') and {'MS-09', 'MS-10', 'MS-23'} <= codes(R))
        R, _ = lifted_run(c_plain, [('длительность сцены первого экрана (MS-10)', 'd-frame-light')])
        expect('marker — ровно id правила: текст с id в скобках норму не снимает', 'MS-10' in codes(R))
        R, _ = lifted_run(c_plain, every, ref=False)
        expect('без refs.art_direction у спецификации записи не читаются: error', set(LIFTABLE) <= codes(R))
        pid = page_id_of(load(plan), p_spec)
        R, ad2 = lifted_run(c_plain, [(k, 'd-frame-light', 'other-page') for k in LIFTABLE])
        expect('область записи: запись с page другой страницы норму не снимает — четыре error', set(LIFTABLE) <= codes(R))
        expect('область записи: записи с page и section проходят схему арт-дирекции', not list(adv.iter_errors(ad2)))
        R, _ = lifted_run(c_plain, [(k, 'd-frame-light', pid) for k in LIFTABLE])
        expect('область записи: запись с page этой страницы снимает норму — 0 error', not codes(R))
        R, _ = lifted_run(c_plain, [(k, 'd-frame-light', None, 'hero') for k in LIFTABLE])
        expect('область записи: запись с section снимает нормы этой секции, норму уровня страницы (MS-23) — нет',
               codes(R) == {'MS-23'} and {'MS-08', 'MS-09', 'MS-10'} <= codes(R, 'warning'))
        R, _ = lifted_run(c_plain, [(k, 'd-frame-light', pid, 'final-cta') for k in LIFTABLE])
        expect('область записи: запись с section другой секции норму не снимает', set(LIFTABLE) <= codes(R))
        R, _ = lifted_run(c_plain, [('MS-08', 'd-frame-light', pid), ('MS-08', 'd-other-page', 'other-page')])
        got = [i[3] for i in R.items if i[1] == 'MS-08']
        expect('область записи: приписка называет только решение своей страницы',
               got and all('d-frame-light' in m_ and 'd-other-page' not in m_ for m_ in got))

        def ms08(R_, moment):
            return {i[0] for i in R_.items if i[1] == 'MS-08' and i[2] == f'hero.{moment}'}
        R, _ = lifted_run(c_exc, [])
        expect('приём каталога на своём уровне: без строки property_exceptions clip-path у mask-reveal на L0 — MS-08 error',
               ms08(R0, 'hero-copy-rise') == {'error'})
        expect('приём каталога на своём уровне: строка property_exceptions (clip-path → effect:mask-reveal) снимает MS-08 без '
               'записи арт-дирекции, filter без исключения остаётся', not ms08(R, 'hero-copy-rise') and ms08(R, 'hero-photo-settle') == {'error'})
        # маска --* таблицы исключений: пользовательское свойство — только у названного приёма
        c_mask = Ctx(levels_copy(tmp, lambda L: None, lambda t: t.update(property_exceptions={'--*': ['effect:mesh-gradient-css']})))
        rise['tracks'] = [{'property': '--mesh-x', 'from': '0%', 'to': '100%'}]
        rise['effect'] = 'effect:mesh-gradient-css'
        R, _ = lifted_run(c_mask, [])
        expect('маска --* в property_exceptions: пользовательское свойство у приёма с исключением на L0 — MS-08 нет',
               not ms08(R, 'hero-copy-rise'))
        rise['effect'] = 'effect:mask-reveal'
        R, _ = lifted_run(c_mask, [])
        expect('маска --* в property_exceptions: то же свойство у другого приёма — MS-08 error', ms08(R, 'hero-copy-rise') == {'error'})
        expect('таблица исключений базы: filter — у sticky-stack, пользовательское свойство — у mesh-gradient-css, у других приёмов — нет',
               ctx.prop_ok('L0', 'filter', 'effect:sticky-stack') and ctx.prop_ok('L0', '--mesh-x', 'effect:mesh-gradient-css')
               and not ctx.prop_ok('L0', 'filter', 'effect:mask-reveal') and not ctx.prop_ok('L0', '--mesh-x', 'effect:sticky-stack'))
    # вход элемента LCP по норме CRV-AL-09: transform, clip-path и opacity от 0,01 — чисто; opacity из 0 и mask — MS-09
    with tempfile.TemporaryDirectory() as tmp:
        p_lcp = os.path.join(tmp, 'home.motion-spec.yaml')

        def lcp_run(tracks, declared=True):
            """Находки spec у копии примера с дорожками tracks у момента LCP; declared — у момента стоит lcp: is-lcp
            (иначе элемент LCP узнаётся по цели page.lcp.target и условие схемы не действует)."""
            d = load(sp)
            hero_ = next(s_ for s_ in d['sections'] if s_['id'] == 'hero')
            fr = next(m_ for m_ in hero_['moments'] if m_['id'] == 'hero-photo-settle')
            fr['tracks'] = tracks
            if not declared:
                fr.pop('lcp', None)
            with open(p_lcp, 'w', encoding='utf-8') as f:
                yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
            R_ = Report()
            cmd_spec(ctx, R_, p_lcp, plan, ov)
            return codes(R_)
        expect('вход LCP: clip-path — схема проходит, MS-09 нет',
               not {'MS-S', 'MS-09'} & lcp_run([{'property': 'clip-path', 'from': 'inset(0 0 100% 0)', 'to': 'inset(0 0 0 0)'}]))
        expect('вход LCP: opacity от 0,01 — схема проходит, MS-09 нет',
               not {'MS-S', 'MS-09'} & lcp_run([{'property': 'opacity', 'from': 0.01, 'to': 1}]))
        expect('вход LCP: opacity из 0 — MS-09 (у момента is-lcp — находка схемы)',
               'MS-09' in lcp_run([{'property': 'opacity', 'from': 0, 'to': 1}], declared=False)
               and 'MS-S' in lcp_run([{'property': 'opacity', 'from': 0, 'to': 1}]))
        expect('вход LCP: opacity ниже 0,01, записанная строкой, — MS-09',
               'MS-09' in lcp_run([{'property': 'opacity', 'from': '0.005', 'to': 1}], declared=False))
        expect('вход LCP: mask — MS-09',
               'MS-09' in lcp_run([{'property': 'mask', 'from': 'linear-gradient(#000 0 0)', 'to': 'none'}], declared=False))
    # шкала движения проекта: токены ветки motion файла refs.tokens — в шкале; чужое значение и чужой токен — находки
    with tempfile.TemporaryDirectory() as tmp:
        p_own = os.path.join(tmp, 'home.motion-spec.yaml')
        with open(os.path.join(tmp, 'system.tokens.json'), 'w', encoding='utf-8') as f:
            json.dump({'motion': {'duration': {'base': {'$value': {'value': 0.24, 'unit': 's'}}},
                                  'marketing': {'duration': {'sweep': {'$value': {'value': 730, 'unit': 'ms'}}},
                                                'easing': {'settle': {'$value': [0.2, 0.8, 0.2, 1]}},
                                                'distance': {'step': {'$value': {'value': 515, 'unit': 'px'}}}}}}, f)

        def own_run(duration, easing=None, tokens='system.tokens.json'):
            """Находки MS-06 и MS-07 момента hero-copy-rise у копии примера с длительностью duration; tokens —
            refs.tokens копии (None — ссылка примера, от папки копии она не разрешается: шкала только базы)."""
            d = load(sp)
            if tokens:
                d['refs']['tokens'] = tokens
            mm = next(m_ for s_ in d['sections'] if s_['id'] == 'hero' for m_ in s_['moments'] if m_['id'] == 'hero-copy-rise')
            mm['duration'] = duration
            if easing:
                mm['easing'] = easing
            with open(p_own, 'w', encoding='utf-8') as f:
                yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
            R_ = Report()
            cmd_spec(ctx, R_, p_own, plan, ov)
            return sorted(i[1] for i in R_.items if i[2] == 'hero.hero-copy-rise' and i[1] in ('MS-06', 'MS-07')), mm
        t_sweep, t_settle = {'token': 'motion.marketing.duration.sweep'}, {'token': 'motion.marketing.easing.settle'}
        expect('шкала проекта: длительность, равная токену времени проекта (мс и секунды), — без MS-07; без токенов проекта — MS-07',
               own_run({'ms': 730})[0] == [] and own_run({'ms': 240})[0] == [] and own_run({'ms': 730}, tokens=None)[0] == ['MS-07'])
        got, mm_own = own_run(t_sweep, t_settle)
        ptok = project_motion(p_own, load(p_own))
        expect('шкала проекта: ссылка на токен проекта (длительность, кривая) — без MS-06; без токенов проекта — MS-06',
               got == [] and own_run(t_sweep, t_settle, tokens=None)[0] == ['MS-06', 'MS-06'])
        expect('шкала проекта: значение токена проекта идёт в длительность момента и в строку момента',
               dur_ms(ctx, t_sweep, None, ptok) == 730 and dur_ms(ctx, t_sweep, None) is None
               and '730 ms; cubic-bezier(0.2, 0.8, 0.2, 1)' in moment_line(ctx, mm_own, {'id': 'hero'}, None, ptok))
        expect('шкала проекта: чужое значение — MS-07, чужой токен — MS-06, токен расстояния в шкалу времени не идёт',
               own_run({'ms': 745})[0] == ['MS-07'] and own_run({'token': 'motion.marketing.duration.nope'})[0] == ['MS-06']
               and own_run({'ms': 515})[0] == ['MS-07'])
        expect('шкала проекта: refs.tokens на marketing-tokens.json базы — шкала только базы',
               project_motion(sp, load(sp)) == {} and project_scale(ptok) == {240.0, 730.0})
    # набор движения, опора момента, имена переменных токенов, полная строка момента
    with tempfile.TemporaryDirectory() as tmp:
        p_kit = os.path.join(tmp, 'home.motion-spec.yaml')
        saved = ctx.primitives
        ctx.primitives = {'rise': {'id': 'rise', 'class': 'one-shot', 'level_min': 'L0', 'effects': ['hero-entrance-once', 'scroll-reveal-system'],
                                   'options': {'shift': '--motion-marketing-distance-shift-reveal', 'each': 60}},
                          'magnet': {'id': 'magnet', 'class': 'pointer', 'level_min': 'L2', 'options': ['max']}}

        def kit_run(mutate):
            """Находки момента hero-copy-rise копии примера после mutate(момент): (коды error, коды warning, коды info)."""
            d = load(sp)
            mm = next(m_ for s_ in d['sections'] if s_['id'] == 'hero' for m_ in s_['moments'] if m_['id'] == 'hero-copy-rise')
            mutate(mm)
            with open(p_kit, 'w', encoding='utf-8') as f:
                yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
            R_ = Report()
            cmd_spec(ctx, R_, p_kit, plan, ov)
            mine = [i for i in R_.items if i[2] == 'hero.hero-copy-rise']
            return tuple({i[1] for i in mine if i[0] == sev} for sev in ('error', 'warning', 'info'))
        try:
            def no_anchor(m):
                m.pop('effect', None)
                m.pop('primitive', None)
                m.pop('custom', None)
            expect('опора момента: без примитива, эффекта и custom — MS-26 warning; с custom — нет',
                   'MS-26' in kit_run(no_anchor)[1]
                   and 'MS-26' not in kit_run(lambda m: (no_anchor(m), m.update(custom='свой код: линия рисуется по длине пути SVG')))[1])
            expect('набор движения: примитив есть — без MS-25; чужой — MS-25 error; уровень выше секции — MS-25 error',
                   'MS-25' not in kit_run(lambda m: m.update(primitive='rise'))[0] | kit_run(lambda m: m.update(primitive='rise'))[1]
                   and 'MS-25' in kit_run(lambda m: m.update(primitive='nope'))[0]
                   and 'MS-25' in kit_run(lambda m: m.update(primitive='magnet'))[0])
            expect('набор движения: эффект, которого примитив не исполняет, — MS-25 warning',
                   'MS-25' in kit_run(lambda m: m.update(primitive='rise', effect='effect:marquee-logos'))[1])
            expect('набор движения: опция вне примитива — MS-25 warning; эффект, который исполняет примитив, без primitive — MS-26 info',
                   'MS-25' in kit_run(lambda m: m.update(primitive='rise', params={'spin': 1}))[1]
                   and 'MS-25' not in kit_run(lambda m: m.update(primitive='rise', params={'shift': 16}))[1]
                   and 'MS-26' in kit_run(lambda m: (m.pop('primitive', None), m.update(effect='effect:scroll-reveal-system')))[2])

            def legacy_var(m):
                m['tracks'][0] = {'property': 'transform', 'from': 'translateY(var(--mm-shift-hero))', 'to': 'none'}

            def track_token(m):
                m['tracks'][0] = dict(m['tracks'][0], easing={'token': 'motion.marketing.easing.nope'})
            expect('имена переменных: короткое --mm-* и чужое --motion-* — MS-06 error; имя сборки ДС — без MS-06',
                   'MS-06' in kit_run(legacy_var)[0]
                   and 'MS-06' in kit_run(lambda m: m['tracks'].__setitem__(0, {'property': 'transform', 'from': 'translateY(var(--motion-marketing-distance-nope))', 'to': 'none'}))[0]
                   and 'MS-06' not in kit_run(lambda m: m['tracks'].__setitem__(0, {'property': 'transform', 'from': 'translateY(var(--motion-marketing-distance-shift-hero))', 'to': 'none'}))[0])
            expect('своя кривая дорожки: чужой токен — MS-06', 'MS-06' in kit_run(track_token)[0])
            mx = {'id': 'm', 'class': 'one-shot', 'target': 'hero.title', 'trigger': {'type': 'in-view'}, 'reduce': {'strategy': 'final-state'},
                  'tracks': [{'property': 'opacity', 'from': 0.01, 'to': 1, 'duration': {'ms': 300}, 'delay_ms': 80},
                             {'property': 'transform', 'from': 'translateY(16px)', 'to': 'none'}],
                  'duration': {'ms': 560}, 'easing': {'token': 'motion.marketing.easing.out-expo'},
                  'interrupt': 'jump-to-end', 'exit': {'behavior': 'fade', 'duration': {'ms': 200}},
                  'attach': {'to': 'hero.line', 'point': 'end'}, 'model': 'spring', 'spring': {'stiffness': 170, 'damping': 26},
                  'primitive': 'rise', 'params': {'shift': 16}, 'source': {'ref': 'ref-a', 'moment': 'm3', 'take': ['duration']},
                  'note': 'подзаголовок идёт за строкой'}
            ln = moment_line(ctx, mx, {'id': 'hero'}, None)
            expect('строка момента несёт всё описание: дорожка со своим временем, выход, прерывание, привязка, пружина, набор, источник, заметка',
                   all(x in ln for x in ('opacity 0.01 -> 1 (300 ms, +80 ms)', 'interrupt: jump-to-end', 'exit: fade, 200 ms',
                                         'moves with the end point of hero.line', 'spring stiffness 170, damping 26',
                                         'motion kit: data-mk="rise" {"shift": 16}', 'numbers from reference ref-a#m3 (duration)',
                                         'note: подзаголовок идёт за строкой')))
        finally:
            ctx.primitives = saved
    # файлы проекта: план с подачей и спецификация движения находят друг друга по ссылкам
    try:
        kbpaths.use('tests')
        import docpaths
        import fixture_project
        with fixture_project.built('minimal') as fx:
            pp = docpaths.site(fx.slug, 'promo', 'plans', 'home.yaml', repo=fx.root)
            mp = docpaths.design(fx.slug, 'motion', surface='promo', repo=fx.root) / 'home.motion-spec.yaml'
            merged = merge_overlay(load(str(pp)), load(ov), Report())
            merged['page']['treatment']['motion_spec_ref'] = os.path.relpath(mp, pp.parent)
            for s_ in merged['sections']:
                t_ = s_.get('treatment') or {}
                if t_.get('motion_spec_ref'):
                    t_['motion_spec_ref'] = os.path.relpath(mp, pp.parent) + '#/sections/' + t_['motion_spec_ref'].split('#/sections/')[-1]
            with open(pp, 'w', encoding='utf-8') as f:
                yaml.safe_dump(merged, f, allow_unicode=True, sort_keys=False)
            spec_doc = load(sp)
            spec_doc['refs']['page_plan'] = os.path.relpath(pp, mp.parent)
            mp.parent.mkdir(parents=True, exist_ok=True)
            with open(mp, 'w', encoding='utf-8') as f:
                yaml.safe_dump(spec_doc, f, allow_unicode=True, sort_keys=False)
            Rp, Rs = Report(), Report()
            cmd_plan(ctx, Rp, str(pp))
            cmd_spec(ctx, Rs, str(mp))
            expect('файлы проекта: plan находит спецификацию по motion_spec_ref, 0 error',
                   not codes(Rp) and any(i[1] == 'TR-00' and 'motion_spec_ref' in i[3] for i in Rp.items))
            expect('файлы проекта: spec находит план по refs.page_plan, 0 error',
                   not codes(Rs) and any(i[1] == 'MS-00' for i in Rs.items))
    except ImportError as e:  # pragma: no cover
        expect(f'фикстура проекта: {e}', False)
    # x-canvas-map: форма и покрытие у схем зоны; подброшенные ошибки ловятся
    mine = [P['t_schema'], P['m_schema'], P['ad_schema'], P['levels']]
    R = cmd_canvas_map(Report(), mine)
    expect('x-canvas-map treatment, motion-spec, art-direction.v1, ambition-levels: 0 error', not codes(R))
    t = load(P['t_schema'])
    m = copy.deepcopy(t['x-canvas-map'])
    del m['files']['pages/<page-id>/page.yaml']['sections[].treatment.composition']
    R = Report()
    canvas_check(P['t_schema'], m, R, t)
    expect('x-canvas-map: поле без правила (composition) → CM-04', any(i[1] == 'CM-04' and 'composition' in i[3] for i in R.items))
    m = copy.deepcopy(t['x-canvas-map'])
    m['files']['pages/<page-id>/page.yaml']['treatment.theme'] = {'rule': 'paste', 'from': ['/page/treatment/them']}
    R = Report()
    canvas_check(P['t_schema'], m, R, t)
    expect('x-canvas-map: неизвестное правило и указатель в пустоту → CM-02, CM-03', {'CM-02', 'CM-03'} <= codes(R))
    a = load(P['ad_schema'])
    am = a['x-canvas-map']
    expect('x-canvas-map: этап treatment (страница «Подача») — варианты подачи арт-дирекции идут правилом своего этапа, а не drop',
           'treatment' in STAGES and am['files']['brief.yaml'].get('treatment_variants[]', {}).get('stages') == ['treatment']
           and not any('/treatment_variants' in (d.get('from') or []) for d in am.get('drop') or []))
    m = copy.deepcopy(am)
    m['stages'] = m['stages'] + ['layout']
    R = Report()
    canvas_check(P['ad_schema'], m, R, a)
    expect('x-canvas-map: этап вне этапов входа холста → CM-01', 'CM-01' in codes(R))
    print('selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--levels', help='файл уровней той же формы, что ambition-levels.yaml')
    sub = ap.add_subparsers(dest='cmd')
    b = sub.add_parser('blocks'); b.add_argument('--yaml')
    p = sub.add_parser('plan'); p.add_argument('plan'); p.add_argument('--overlay'); p.add_argument('--out'); p.add_argument('--spec')
    s = sub.add_parser('spec'); s.add_argument('spec'); s.add_argument('--plan'); s.add_argument('--overlay')
    m = sub.add_parser('moments'); m.add_argument('spec'); m.add_argument('--section')
    md = sub.add_parser('motion-md'); md.add_argument('spec'); md.add_argument('--out')
    v = sub.add_parser('values'); v.add_argument('spec'); v.add_argument('--out', required=True)
    lv = sub.add_parser('levels'); lv.add_argument('--check', action='store_true')
    cm = sub.add_parser('canvas-map'); cm.add_argument('files', nargs='*')
    a = ap.parse_args()
    if a.levels and not os.path.isfile(a.levels):
        ap.error(f'нет файла уровней {a.levels}')
    ctx = Ctx(a.levels)
    if a.selftest:
        return selftest(ctx)
    if a.cmd == 'blocks':
        return cmd_blocks(ctx, Report(), a.yaml).dump('block-treatments')
    if a.cmd == 'plan':
        R = Report()
        spec = load(a.spec) if a.spec else None
        cmd_plan(ctx, R, a.plan, a.overlay, a.out, spec)
        return R.dump(f'plan {os.path.basename(a.plan)}')
    if a.cmd == 'spec':
        R = Report()
        cmd_spec(ctx, R, a.spec, a.plan, a.overlay)
        return R.dump(f'motion-spec {os.path.basename(a.spec)}')
    if a.cmd in ('moments', 'motion-md', 'values'):
        spec = load(a.spec)
        ptok = project_motion(a.spec, spec)
        if a.cmd == 'moments':
            cmd_moments(ctx, spec, a.section, ptok)
        elif a.cmd == 'motion-md':
            cmd_motion_md(ctx, spec, a.out, ptok)
        else:
            cmd_values(ctx, spec, a.out, ptok)
        return 0
    if a.cmd == 'levels':
        if a.check:
            R = Report()
            cmd_levels(ctx, R)
            return R.dump('x-effect-levels')
        cmd_levels(ctx)
        return 0
    if a.cmd == 'canvas-map':
        return cmd_canvas_map(Report(), [os.path.abspath(f) for f in a.files] or None).dump('x-canvas-map')
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
