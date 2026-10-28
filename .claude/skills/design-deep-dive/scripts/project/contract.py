#!/usr/bin/env python3
"""contract — контракт генерации экранов поверхности кабинета для входа холста: десять разделов ux 11/04 §7.3 и раздел
на каждый экран. Контракт собирается из артефактов слоя проекта, у каждого раздела — источник (путь и раздел файла):
массовый провал на макете ведёт в слой проекта, а не в правку входа. Канон — `docs/projects/_template/screens/
README.md`, «Что слой отдаёт макету»; раскладка входа — `references/claude-design.md § 6. Вход холста`.

Заголовки разделов, их порядок и строки-нормы (ЗАПРЕТ, ПРАВИЛО, критерии) — из шаблона ux 11/04 §7.3; поля шаблона
заполняются из слоя проекта:
  Контекст продукта       vision `Users` и постура user.md; `Problem` — наблюдения ограничениями; решения map.md;
                          задача экрана, ключевое действие и плотность — в разделе экрана
  Объектная модель        object.md (объекты, атрибуты, представления), action.md; права — матрица «пользователь ×
                          объект × действие» из возможностей поверхности и колонок creates · deletes
  Карта экранов           маршруты — закрытый список полей экранов; переходы; «Переход», «Навигация», «Узкий экран»
  Дизайн-система          артефакт, токены и проза ДС; конвенции map.md и карты решений; типы ui: поверхности →
                          компоненты design/system.yaml; правило заземления; нет ДС — пробел
  Обязательные состояния  приоритет и наложения, строки словаря для S-id поверхности, состояния приложения каркаса;
                          набор экрана — в его разделе
  Данные                  демо-набор demo-data.json (модуль demo_data): коллекции, наборы, крайние случаи
  Тексты                  глоссарий (имена и aliases объектов, verb, past и banned действий), правила текстов, строки
                          texts.md статусов этапа
  Запреты                 список сбоев шаблона, этика ux 06/04 §8.1, бан-лист холста — brief.yaml входа
  Примеры                 эталонные экраны design/system.yaml#starter; взаимодействия — шаги и ветвления сценариев,
                          события map.md
  Критерии приёмки        строки шаблона, «Приёмка» сценариев, «как проверить» словаря по S-id, ACCEPTANCE.md входа
Раздел экрана: тип, объект, главная задача, ключевое действие, для кого и плотность, маршрут и доступ, каркас и слоты,
блоки и компоненты (tree), переходы, ситуации и сценарии, данные набора, ключи текстов; обязательные состояния — S-id:
ключи `states` экрана ∪ обязательный набор (states), покрытие — дельта или «не применимо: причина»; блоки со своим
источником — свой набор; работа без сети и живые данные — по решению поверхности, чтением.

Тексты — строки реестра статуса этапа: этап холста контракта — mockup (`--stage`), он берёт только approved;
остальные строки — пробел, на артборде — заглушка.

Партия экранов (Python: `build(…, screens=[slug …])`; её задаёт вход холста `canvas_input --screen`): разделы экранов —
только экранов партии, раздел «Тексты» и находка о статусе строк — только ключи, которые называют экраны партии, блоки
их состава и каркасы; демо-набор — коллекции экранов партии, их объекты и объекты экранов с целями ссылок; пробелы и
находки демо-набора — только их. Десять разделов шаблона — вся поверхность. Экран вне партии, в том числе не stable,
находок не даёт: вход называет его строкой пробелов. Без партии — все экраны и весь реестр текстов.

    contract build <slug> <surface> [--repo DIR] [--stage mockup] [--out DIR] [--json]
    contract check <slug> [<surface>] [--repo DIR] [--stage mockup] [--json]
    contract --selftest

`build` печатает contract.md (`--json` — структуру: разделы, источники, пробелы, наборы экранов); `--out DIR` пишет
DIR/contract.md и печатает путь. В репозиторий проекта утилита не пишет: вход холста собирает `canvas_input`. `check` —
пробелы источников находками (модуль findings) вместе с пробелами демо-набора, ничего не пишет; без <surface> — все
поверхности кабинета. Из Python: `build(Layer, stage, demo=None, screens=None)` → Contract (`sections`, `screens`,
`findings`, `demo` — демо-набор партии, `keys` — ключи текстов партии или None, `units`, `outside`, `render()`,
`as_dict()`), `render(Layer, stage)`, `text_rows(Layer, stage, keys=None)` → (строки этапа, строки не того статуса),
`batch_scope(Layer, trees, screens)` → состав партии, `check(Layer, stage)` → находки.

Правила находок (`.claude/skills/design-audit/references/rules.md`):
  R-MAT-011   пункт блока PRE ux 12/02 §2 не заполнен: экран партии не stable (вход — на stable-экранах); нет
              texts.md, map.md, object.md, action.md; у vision нет Problem или Users; у пользователя поверхности нет
              строки постуры; у экрана нет главной задачи; раздел «Переход» пуст; обязательное состояние экрана не
              покрыто; коллекция без объёма (demo_data) — доклад заказчику, пункт закрывает слой проекта. Запись
              экрана не разбирается (файл или frontmatter) — одна находка с причиной разбора: находок о статусе,
              главной задаче и состояниях этой записи нет — её поля не читаются                          warning
  R-MAT-003   этап mockup: строки texts.md не approved — одна находка на реестр (отчёт контракта; во входе
              холста canvas_input поднимает её в R-MAT-012 error — гейт макета на утверждённых текстах)  warning
  R-COV-005   этап mockup: нет карты решений design/system.yaml — типам экранов не сопоставить компоненты  error
  R-DEBT-002  заглушки демо-набора (demo_data)                                                      hint
Код выхода: 0 — нет error, 1 — есть error, 2 — ошибка вызова или окружения.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "lib"))
import kbpaths  # noqa: E402
import docpaths  # noqa: E402
import findings as F  # noqa: E402
import layer as L  # noqa: E402
import tree as T  # noqa: E402
import states as S  # noqa: E402
import screen_map as M  # noqa: E402
import demo_data as D  # noqa: E402

TEMPLATE = kbpaths.kb("ux", "11-ai-generated-ui", "04-constraints-prompts-and-checks.md")
ETHICS = kbpaths.kb("ux", "06-feedback-states-motion", "04-dark-patterns-and-ethics.md")
BANNED = kbpaths.kb("ux", "07-ux-writing", "06-banned-words-and-patterns.md")
COMPONENTS = kbpaths.kb(None, "common", "components.yaml")
STAGES = ("mockup",)
STAGE_STATUSES = {"mockup": ("approved",)}
DEMO_FILE = "demo-data.json"
TEXT_PLACEHOLDER = "[PLACEHOLDER: текст на утверждении]"
NBSP = " "


# ------------------------------------------------------------------ шаблон ux 11/04 §7.3

@dataclass
class Part:
    title: str                                          # заголовок раздела шаблона
    short: str                                          # без пояснения в скобках — заголовок раздела контракта
    entries: list                                       # [(ключ | None, текст, заготовка ли)]


def _entries(body):
    """Строки раздела шаблона: «Ключ: текст» или предложение; строчная буква или незакрытая «<» — продолжение."""
    out, cur = [], None
    for raw in str(body).splitlines():
        line = raw.strip()
        if not line:
            cur = None
            continue
        if cur is not None and (cur[2] or line[:1].islower()):
            cur[1] += " " + line
            cur[2] = cur[1].count("<") > cur[1].count(">")
            continue
        m = re.match(r"^([^:<]{1,60}):\s*(.*)$", line)
        cur = [m.group(1).strip() if m else None, (m.group(2) if m else line).strip(), False]
        cur[2] = cur[1].count("<") > cur[1].count(">")
        out.append(cur)
    return [(k, t, "<" in t) for k, t, _ in out]


_TEMPLATE = None


def template(path=TEMPLATE):
    """Шаблон контракта ux 11/04 §7.3 — десять разделов по порядку."""
    global _TEMPLATE
    if _TEMPLATE is not None and path == TEMPLATE:
        return _TEMPLATE
    text = Path(path).read_text(encoding="utf-8")
    body = next((b for t, _, b in L.sections(text, 3) if t.startswith("7.3")), "")
    m = re.search(r"^```markdown\s*\n(.*?)^```", body, re.S | re.M)
    if not m:
        raise F.ToolError(f"{path}: нет шаблона контракта в §7.3 (блок ```markdown)")
    parts = [Part(t, re.sub(r"\s*\(.*\)\s*$", "", t).strip(), _entries(b)) for t, _, b in L.sections(m.group(1), 2)]
    if len(parts) != 10:
        raise F.ToolError(f"{path}: в шаблоне §7.3 разделов {len(parts)}, а не десять")
    if path == TEMPLATE:
        _TEMPLATE = parts
    return parts


def readme_names():
    """Разделы контракта в таблице канона экранов («Что слой отдаёт макету») — по порядку."""
    md = L.Md(docpaths.template("screens", "README.md"))
    _, body = md.section("Что слой отдаёт макету")
    t = L.find_table(body or "", ("раздел контракта",))
    return [(r.get("раздел контракта") or "").strip() for r in (t.rows if t else [])]


def ethics(path=ETHICS):
    """Закрытый список запретов ux 06/04 §8.1 — пункты по порядку."""
    text = Path(path).read_text(encoding="utf-8")
    body = next((b for t, _, b in L.sections(text, 3) if t.startswith("8.1")), "")
    m = re.search(r"^```\s*\n(.*?)^```", body, re.S | re.M)
    return [x.group(1).strip() for x in re.finditer(r"^\s*\d+\.\s+(.+)$", m.group(1) if m else "", re.M)]


# ------------------------------------------------------------------ модель контракта

@dataclass
class Source:
    path: str                                           # от корня данных (docs/projects/…) или от папки скилла (kb/…)
    part: str = ""


@dataclass
class Section:
    title: str
    sources: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    gaps: list = field(default_factory=list)


@dataclass
class ScreenPart:
    slug: str
    name: str
    status: str | None
    sources: list = field(default_factory=list)
    lines: list = field(default_factory=list)
    states: list = field(default_factory=list)          # [{id, key, required, covered, na, reasons}]
    own: dict = field(default_factory=dict)             # блок со своим источником → строки набора
    manual: list = field(default_factory=list)          # по решению поверхности — чтением
    gaps: list = field(default_factory=list)


@dataclass
class Contract:
    project: str
    surface: str
    kind: str
    stage: str
    demo_ref: str
    sections: list = field(default_factory=list)
    screens: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    demo: dict = field(default_factory=dict)            # демо-набор партии (без партии — весь)
    keys: list | None = None                            # ключи texts.md экранов партии; None — весь реестр
    units: list = field(default_factory=list)           # экраны партии
    outside: list = field(default_factory=list)         # экраны вне партии: [(slug, статус)]

    def render(self):
        out = [f"# Контракт генерации экранов — `{self.surface}`", "",
               f"Проект `{self.project}`, поверхность `{self.surface}` ({self.kind}). Этап `{self.stage}`: тексты — "
               f"строки {', '.join(f'`{s}`' for s in STAGE_STATUSES[self.stage])} реестра.", "",
               "Контракт производный: его собирает `scripts/project/contract.py` из файлов слоя проекта, руками он не "
               "правится — правка идёт в источник раздела, вход собирается заново. Десять разделов — шаблон ux 11/04 "
               f"§7.3; за ними — раздел на каждый экран {'партии' if self.outside else 'поверхности'}. Данные — "
               f"`{self.demo_ref}` рядом.", ""]
        if self.outside:
            out += [f"Экраны партии: {_codes(self.units)}; вне партии — {_codes([s for s, _st in self.outside])}: их "
                    "разделов, строк текстов и записей демо-набора в контракте нет.", ""]
        for title, sources, gaps, lines in [(s.title, s.sources, s.gaps, s.lines) for s in self.sections] + \
                [(f"Экран `{p.slug}` — {p.name}", p.sources, p.gaps, p.lines) for p in self.screens]:
            out += [f"## {title}", "", _sources_line(sources), ""]
            for g in gaps:
                out += [f"Пробел: {g}", ""]
            out += lines + [""]
        text = "\n".join(out)
        text = re.sub(r"\n{3,}", "\n\n", text).rstrip("\n")
        return text + "\n"

    def as_dict(self):
        def srcs(lst):
            return [{"path": s.path, "part": s.part} for s in lst]
        return {"project": self.project, "surface": self.surface, "stage": self.stage,
                "texts_statuses": list(STAGE_STATUSES[self.stage]), "demo": self.demo_ref, "units": self.units,
                "outside": [{"slug": s, "status": st} for s, st in self.outside],
                "sections": [{"title": s.title, "sources": srcs(s.sources), "gaps": s.gaps} for s in self.sections],
                "screens": [{"slug": p.slug, "name": p.name, "status": p.status, "sources": srcs(p.sources),
                             "states": p.states, "own": p.own, "manual": p.manual, "gaps": p.gaps}
                            for p in self.screens]}


def _sources_line(sources):
    """Строка источников: разделы одного файла — через запятую при нём."""
    parts = {}
    for s in sources:
        parts.setdefault(s.path, [])
        if s.part and s.part not in parts[s.path]:
            parts[s.path].append(s.part)
    return "Источник: " + (" · ".join(f"`{p}`" + (f" § {', '.join(v)}" if v else "") for p, v in parts.items())
                           if parts else "—")


def _esc(v):
    return str(v if v is not None else "—").replace("\n", " ").replace("|", "\\|").strip() or "—"


def _table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    return out + ["| " + " | ".join(_esc(c) for c in r) + " |" for r in rows]


def _num(n):
    return f"{n:,}".replace(",", NBSP)


def _codes(items):
    return ", ".join(f"`{x}`" for x in items) if items else "—"


def _sentence(text):
    t = str(text or "").strip()
    return t if not t or t[-1] in ".!?…»" else t + "."


def _plural(n, one, few, many):
    k = n % 100
    return one if k % 10 == 1 and k != 11 else few if 2 <= k % 10 <= 4 and not 12 <= k <= 14 else many


def _covered(covered, na):
    return "дельта" if covered == "delta" else f"не применимо: {na}" if covered == "na" else "НЕ ПОКРЫТО"


def _trigger(lay, value):
    """Чем вызван переход: действие словаря — со своим глаголом, событие — как есть."""
    v = str(value or "").strip()
    row = lay.product.actions.get(v)
    return f"`{v}` — «{(row.get('verb') or '').strip()}»" if row is not None else (v or "—")


# ------------------------------------------------------------------ источники слоя проекта

@dataclass
class Scenario:
    slug: str
    meta: dict
    steps: list                                         # [(№, ситуация, что делает, что показывает)]
    branches: list                                      # [(условие, на шаге, куда, что меняется)]
    acceptance: list


def scenarios(lay):
    """Сценарии поверхности (interface/<surface>/scenario.md): мета, основной путь, ветвления, приёмка."""
    out = []
    for title, _, body in L.sections(lay.interface.scenario_text(), 2):
        slug = title.strip().strip("`")
        if not docpaths.SLUG.match(slug):
            continue
        meta = {}
        m = re.search(r"^```ya?ml\s*\n(.*?)^```", body, re.S | re.M)
        if m:
            try:
                meta = L._yaml().safe_load(m.group(1)) or {}
            except Exception:                           # noqa: BLE001 — битую мету проверяет /interface-audit
                meta = {}
        subs = {t.strip(): b for t, _, b in L.sections(body, 3)}

        def rows(name, cols):
            t = L.find_table(subs.get(name) or "", cols[:1])
            return [tuple((r.get(c) or "").strip() for c in cols) for r in (t.rows if t else [])
                    if not all(L.is_empty(r.get(c)) for c in cols)]

        steps = rows("Happy path", ("#", "situation", "что делает пользователь", "что показывает система"))
        branches = rows("Ветвления", ("условие", "на шаге", "куда", "что меняется"))
        acc = [x.strip()[2:].strip() for x in (subs.get("Приёмка") or "").splitlines()
               if x.strip().startswith("- ") and not L.is_empty(x.strip()[2:])]
        out.append(Scenario(slug, meta if isinstance(meta, dict) else {}, steps, branches, acc))
    return out


def text_rows(lay, stage, keys=None):
    """Строки реестра texts.md: (статус этапа, не того статуса) — в порядке реестра; keys — только эти ключи (ключи
    экранов партии), None — весь реестр."""
    allowed = STAGE_STATUSES[stage]
    rows = list(lay.texts.rows.values()) if lay.texts.exists else []
    if keys is not None:
        keys = set(keys)
        rows = [r for r in rows if r.key in keys]
    return [r for r in rows if r.status in allowed], [r for r in rows if r.status not in allowed]


def record_error(rec):
    """Причина, по которой поля записи слоя не читаются: файл или frontmatter не разбираются; запись читается —
    None."""
    if rec.error or rec.md is None:
        return f"файл не читается: {rec.error}"
    return rec.md.fm_error


def record_note(rec):
    """Пометка записи не stable: «не разбирается» — раньше статуса; иначе статус или «без статуса»."""
    return "не разбирается" if record_error(rec) else rec.status or "без статуса"


def batch_scope(lay, trees, screens):
    """Состав экранов партии: {screens, blocks — блоки состава с вложенными, shells — каркасы экранов, keys — ключи
    texts.md, которые называют экраны, их блоки и каркасы (порядок — первое упоминание), objects — объекты глоссария
    экранов (поле object и датумы деревьев)}."""
    blocks, shells, parsed = [], [], []
    for s in screens:
        p = trees.screens[s]
        parsed.append(p)
        blocks += [b for b in T.composition(trees, s)["blocks"] if b not in blocks]
        sh = str(p.record.fm.get("shell") or "").strip()
        if sh in trees.shells and sh not in shells:
            shells.append(sh)
    parsed += [trees.blocks[b] for b in blocks if b in trees.blocks] + [trees.shells[x] for x in shells]
    mine = {id(x) for x in parsed}
    keys = list(dict.fromkeys(u.key for u in T.text_uses(trees, lay.components) if id(u.parsed) in mine))
    objs = [L.cell(str(trees.screens[s].record.fm.get("object") or "")) for s in screens]
    objs = list(dict.fromkeys([o for o in objs if o] + D.items_of(lay, parsed)))
    return {"screens": list(screens), "blocks": blocks, "shells": shells, "keys": keys, "objects": objs}


def _in_scope(ref, scope, objs):
    """Находка демо-набора — о коллекции экрана или блока партии либо об объекте её набора."""
    head, _, tail = str(ref).partition("#")
    if head == "object":
        return re.split(r"[/.]", tail, maxsplit=1)[0] in objs
    return head in scope["screens"] or head in scope["blocks"]


def demo_part(doc, lay, trees, scope):
    """Демо-набор партии: коллекции её экранов, объекты экранов и коллекций с целями ссылок (ref:<объект>), пробелы и
    источники только их; окно, нормы и локализация — как у набора поверхности."""
    colls = {cid: c for cid, c in doc["collections"].items() if set(c.get("screens") or []) & set(scope["screens"])}
    queue = [o for o in list(scope["objects"]) + [c.get("object") for c in colls.values()] if o in doc["objects"]]
    objs = []
    while queue:
        o = queue.pop(0)
        if o in objs:
            continue
        objs.append(o)
        for a in doc["objects"][o].get("attributes") or []:
            t = str(a.get("type") or "")
            if t.startswith("ref:"):
                queue.append(t[4:].removesuffix("[]").strip())
        queue = [x for x in queue if x in doc["objects"]]
    kept = {lay.rel(trees.blocks[c].record.path) if c in trees.blocks else
            lay.rel(trees.screens[c.split("#", 1)[0]].record.path) for c in colls}
    dropped = {lay.rel(trees.blocks[c].record.path) if c in trees.blocks else
               lay.rel(trees.screens[c.split("#", 1)[0]].record.path) for c in doc["collections"] if c not in colls}
    out = dict(doc)
    out["objects"] = {o: v for o, v in doc["objects"].items() if o in objs}
    out["collections"] = colls
    out["sources"] = [s for s in doc["sources"] if s not in dropped - kept]
    out["gaps"] = [{"rule": f.rule, "severity": f.severity, "path": f.path, "message": f.message}
                   for f in D.gaps(lay, trees) if _in_scope(f.ref, scope, objs)]
    return out


def _dict(value):
    """Словарь или пустой словарь — битую форму файла дизайна проверяет /design-audit."""
    return value if isinstance(value, dict) else {}


def _yaml_file(path):
    if not Path(path).is_file():
        return None
    try:
        data = L._yaml().safe_load(Path(path).read_text(encoding="utf-8"))
    except Exception:                                   # noqa: BLE001 — битый файл дизайна проверяет /design-audit
        return None
    return data if isinstance(data, dict) else None


def _map_rows(lay, section, col):
    """Строки первой таблицы раздела map.md с колонкой col — без заготовок и пустых строк."""
    if lay.map is None:
        return []
    _, body = lay.map.section(section)
    t = L.find_table(body or "", (col,))
    return [r for r in (t.rows if t else []) if not all(L.is_empty(v) for v in r.cells.values())
            and not any(L.PLACEHOLDER.match((v or "").strip()) for v in r.cells.values())]


def _paragraphs(body):
    paras, cur = [], []
    for line in (body or "").splitlines():
        s = line.strip()
        if not s or s.startswith(("|", "```", "#")):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        if not s.startswith("- "):
            cur.append(s)
    if cur:
        paras.append(" ".join(cur))
    return paras


class Ctx:
    """Всё, что читает сборка контракта одной поверхности, и пробелы с находками; screens — партия экранов."""

    def __init__(self, lay, stage, demo=None, demo_ref=DEMO_FILE, screens=None):
        if stage not in STAGES:
            raise ValueError(f"этап: {' · '.join(STAGES)}, не {stage!r}")
        self.lay, self.stage, self.demo_ref = lay, stage, demo_ref
        self.trees = T.parse_layer(lay)
        self.parts = template()
        self.dict = S.dictionary()
        self.derived = M.derive(lay, self.trees)
        want = set(screens) if screens is not None else None
        lost = sorted(want - set(self.trees.screens)) if want is not None else []
        if lost:
            raise F.ToolError(f"экранов {', '.join(lost)} нет на поверхности {lay.surface}")
        self.units = [s for s in sorted(self.trees.screens) if want is None or s in want]
        self.outside = [(s, record_note(lay.screens[s])) for s in sorted(self.trees.screens)
                        if s not in self.units]
        self.scope = batch_scope(lay, self.trees, self.units) if want is not None else None
        self.keys = self.scope["keys"] if self.scope is not None else None
        demo = demo if demo is not None else D.build(lay, trees=self.trees)
        self.demo = demo_part(demo, lay, self.trees, self.scope) if self.scope is not None else demo
        self.objs = D.objects(lay)
        self.sets = {s: S.screen_set(lay, s, self.trees) for s in self.trees.screens}
        self.own = {b: S.block_set(lay, b, self.trees) for b in self.trees.blocks if T.is_own(self.trees, b)}
        self.scen = scenarios(lay)
        self.rep = F.Report()
        self.design = {k: docpaths.design(lay.slug, k, repo=lay.repo) for k in
                       ("system", "tokens", "tokens-css", "design-md", "app-brief", "ds-project", "artifacts")}
        self.system = _yaml_file(self.design["system"])
        self.app_brief = _yaml_file(self.design["app-brief"])

    def proj(self, *parts):
        return docpaths.project(self.lay.slug, *parts, repo=self.lay.repo)

    def src(self, path, part=""):
        p = Path(path)
        try:
            rel = "kb/" + p.resolve().relative_to(kbpaths.kb().resolve()).as_posix()
        except ValueError:
            rel = self.lay.rel(p)
        return Source(rel, part)

    def finding(self, rule, severity, kind, ref, path, message, fix=""):
        self.rep.add(rule, severity, surface=self.lay.surface, kind=kind, ref=ref, path=self.lay.rel(path),
                     message=message, fix=fix)

    def pre(self, where, pre, text, kind, ref, path, fix):
        """Пробел второго входа (пункт блока PRE или stable-экраны): строка «Пробел» раздела и находка R-MAT-011 —
        доклад заказчику (warning), пункт закрывает исполнитель слоя проекта."""
        where.gaps.append(f"{pre} — {text}")
        self.finding("R-MAT-011", "warning", kind, ref, path, f"{pre}: {text}", fix)

    def fix_project(self, what=""):
        return f"/project-deep-dive {self.lay.slug}" + (f" {what}" if what else "")

    def fix_screens(self, what=""):
        return f"/screen-deep-dive {self.lay.slug} {self.lay.surface}" + (f" {what}" if what else "")

    def fixed(self, part, keys=None):
        """Строки-нормы раздела шаблона (без заготовок); keys — только эти ключи."""
        return [f"{k}: {t}" if k else t for k, t, ph in part.entries if not ph and (keys is None or k in keys)]

    def entry_keys(self, part):
        return [k for k, _, ph in part.entries if ph]


# ------------------------------------------------------------------ разделы

def sec_context(c, part):
    s = Section(part.short)
    lay = c.lay
    vision = c.proj("vision.md")
    md = L.Md(vision) if vision.is_file() else None
    fix = c.fix_project("--phase discovery")
    users_body = md.section("Users")[1] if md else None
    problem = _paragraphs(md.section("Problem")[1]) if md else []
    bullets = [x.strip() for x in (users_body or "").splitlines() if x.strip().startswith("- ")]
    if md is None:
        c.pre(s, "PRE-01, PRE-03", "нет vision.md — пользователей и ограничений не собрать", "vision", "vision",
              vision, fix)
    else:
        if problem:
            s.sources.append(c.src(vision, "Problem"))
        else:
            c.pre(s, "PRE-03", "у vision нет раздела Problem с наблюдениями", "vision", "vision#Problem", vision, fix)
        if bullets:
            s.sources.append(c.src(vision, "Users"))
        else:
            c.pre(s, "PRE-01", "у vision нет раздела Users со списком пользователей", "vision", "vision#Users",
                  vision, fix)
    user_md = c.proj("user.md")
    posture = {u: row for u, surf, row in lay.product.postures if surf in (None, lay.surface)}
    if posture:
        s.sources.append(c.src(user_md, "Постура"))
    for u in lay.surf.users:
        if u not in posture:
            c.pre(s, "PRE-01, PRE-04", f"у пользователя `{u}` поверхности нет строки постуры", "user", f"user#{u}",
                  user_md, c.fix_project(f"user:{u}"))
    decisions = _map_rows(lay, "Решения", "решение")
    if decisions:
        s.sources.append(c.src(lay.map_path, "Решения"))
    names = {u: (r.get("name") or "").strip() for u, r in lay.product.users.items()}
    cols = ("hours", "return", "main-work", "posture", "density", "accelerators", "learning")
    for key in c.entry_keys(part):
        if key == "Пользователи":
            s.lines += [f"{key}:", ""] + bullets + [""]
            s.lines += _table(("пользователь", "часов в день", "возврат", "основная работа", "постура", "плотность",
                               "ускорители", "обучение"),
                              [[f"`{u}` — {names.get(u) or u}"] + [r.get(x) for x in cols] for u, r in posture.items()])
            s.lines.append("")
        elif key == "Выводы исследований как ограничения":
            s.lines += [f"{key}:", ""] + [f"> {p}" for p in problem] + [""]
        elif key == "Задача экрана":
            s.lines += [f"{key}: в разделе экрана — `main-task`, возможность поверхности.", ""]
        elif key == "Ключевое действие":
            s.lines += [f"{key}: в разделе экрана — `key-action`, действие словаря.", ""]
        elif key == "Плотность":
            dens = ((c.app_brief or {}).get("core") or {}).get("density") if c.app_brief else None
            extra = f"; режим продукта — `{dens.get('default')}` (бриф на вид)" if isinstance(dens, dict) and \
                dens.get("default") and not L.PLACEHOLDER.match(str(dens.get("default"))) else ""
            s.lines += [f"{key}: в разделе экрана — из постуры пользователей и типа экрана (свод map.md){extra}.", ""]
        else:
            s.lines += [f"{key}: —", ""]
            s.gaps.append(f"у поля шаблона «{key}» нет источника в слое проекта")
    s.lines += [""] + (["Решения поверхности:", ""] + [f"- {r.get('решение')} — почему: {r.get('почему')}; кто теряет: "
                                                      f"{r.get('кто теряет')}" for r in decisions] if decisions else [])
    return s


def sec_objects(c, part):
    s = Section(part.short)
    lay = c.lay
    omd, amd = c.proj("object.md"), c.proj("action.md")
    cap = docpaths.layer(lay.slug, "capability", lay.surface, lay.repo)
    if omd.is_file():
        s.sources.append(c.src(omd, "Объекты, Атрибуты"))
    else:
        c.pre(s, "PRE-05", "нет object.md — объектов и атрибутов не собрать", "object", "object", omd, c.fix_project())
    if amd.is_file():
        s.sources.append(c.src(amd))
    else:
        c.pre(s, "PRE-05", "нет action.md — действий не собрать", "action", "action", amd, c.fix_project())
    if cap.is_file():
        s.sources.append(c.src(cap, "возможности: user · object · action"))
    views = []
    if omd.is_file():
        t = L.Md(omd).table(("object", "context", "attributes"))
        views = [r for r in (t.rows if t else []) if L.cell(r.get("object")) and not
                 L.PLACEHOLDER.match(L.cell(r.get("object")) or "")]
    rows = {slug: r for slug, r in lay.product.objects.items()}
    for key in c.entry_keys(part):
        if key == "Сущности и поля":
            s.lines += [f"{key}:", ""]
            for slug, o in c.objs.items():
                r = rows[slug]
                st = " · ".join(f"`{a}` — {b}" for a, b in o.statuses) or "—"
                s.lines += [f"**`{slug}` — {o.name}.** {_sentence(o.description)} Статусы: {st}. Создают: "
                            f"{_codes(L.refs(r.get('creates')))}; удаляют: {_codes(L.refs(r.get('deletes')))}.", ""]
                s.lines += _table(("атрибут", "имя", "ранг", "тип", "обязателен", "длина", "значения"),
                                  [[f"`{a.slug}`", a.name, a.rank if a.rank != 99 else "—", f"`{a.type}`",
                                    "да" if a.required else "нет",
                                    " / ".join(map(str, a.length)) if a.length else "—",
                                    ", ".join(a.values) or "—"] for a in o.attrs]) + [""]
            if views:
                s.lines += ["Представления — исключения из правила рангов:", ""]
                s.lines += [f"- `{L.cell(r.get('object'))}` · {L.cell(r.get('context'))}: {r.get('attributes')} — "
                            f"{r.get('why')}" for r in views] + [""]
        elif key == "Действия над сущностями":
            s.lines += [f"{key}:", ""]
            s.lines += _table(("действие", "имя", "на кнопке", "в сообщении", "обратимость", "объекты"),
                              [[f"`{a}`", r.get("name"), r.get("verb"), r.get("past"), L.cell(r.get("reversibility")),
                                _codes(L.refs(r.get("objects")))] for a, r in lay.product.actions.items()]) + [""]
        elif key == "Права":
            verbs = {a: (r.get("verb") or a).strip() for a, r in lay.product.actions.items()}
            may = {}
            for _, r in lay.product.capabilities.items():
                obj, act = r.value("object"), r.value("action")
                for u in r.refs("user"):
                    if obj:
                        may.setdefault(u, {}).setdefault(obj, [])
                        if act and verbs.get(act, act) not in may[u][obj]:
                            may[u][obj].append(verbs.get(act, act))
            for slug, r in rows.items():
                for col, word in (("creates", "создаёт"), ("deletes", "удаляет")):
                    for u in L.refs(r.get(col)):
                        if u != "system":
                            may.setdefault(u, {}).setdefault(slug, []).append(word)
            s.lines += [f"{key} — матрица «пользователь × объект × действие» из возможностей поверхности и колонок "
                        "creates · deletes:", ""]
            s.lines += [f"- `{u}`: " + " · ".join(f"`{o}` — {', '.join(v) or 'видит'}" for o, v in objs.items())
                        for u, objs in may.items()] + [""]
        else:
            s.lines += [f"{key}: —", ""]
            s.gaps.append(f"у поля шаблона «{key}» нет источника в слое проекта")
    return s


def sec_map(c, part):
    s = Section(part.short)
    lay = c.lay
    if lay.map is None:
        c.pre(s, "PRE-06", "нет map.md — закрытого списка маршрутов нет", "map", "map", lay.map_path,
              c.fix_screens("map"))
    else:
        s.sources.append(c.src(lay.map_path, "Маршруты, Навигация, Переход, Узкий экран"))
    s.sources.append(c.src(lay.folder / "screens", "поля route, params, access, url-state, transitions-to-screen"))
    moves = _map_rows(lay, "Переход", "что")
    if lay.map is not None and not moves:
        c.pre(s, "PRE-07", "раздел «Переход» map.md пуст — не сказано, что переживает переход", "map", "map#Переход",
              lay.map_path, c.fix_screens("map"))
    for k, t, ph in part.entries:
        if not ph:
            s.lines += [f"{k}: {t}" if k else t, ""]
            continue
        if k == "Маршруты":
            s.lines += [f"{k}:", ""]
            routes = sorted(c.derived.routes.values(), key=lambda r: (r["route"] or "", r["screen"]))
            s.lines += _table(("маршрут", "экран", "параметры", "доступ", "состояние в адресе"),
                              [[f"`{r['route']}`", f"`{r['screen']}`", M.cparams(r["params"]), f"`{r['access']}`",
                                ", ".join(r["url-state"]) or "—"] for r in routes]) + [""]
        elif k == "Переходы":
            s.lines += [f"{k}:", ""]
            for slug, p in sorted(c.trees.screens.items()):
                for tr in M.transitions(p.record.fm):
                    s.lines.append(f"- `{slug}` → `{tr.get('to')}`: {_trigger(lay, tr.get('trigger'))}; сохраняется: "
                                   f"{tr.get('keeps') or '—'}; назад: {tr.get('back') or '—'}")
            s.lines.append("")
        elif k == "Состояние между экранами":
            s.lines += [f"{k}:", ""] + [f"- {r.get('что')}: {r.get('где живёт')}, {r.get('срок')}; переживает — "
                                        f"{r.get('переживает')}; проверка — {r.get('как проверить')}"
                                        for r in moves] + [""]
        else:
            s.lines += [f"{k}: —", ""]
            s.gaps.append(f"у поля шаблона «{k}» нет источника в слое проекта")
    nav = _map_rows(lay, "Навигация", "level")
    if nav:
        s.lines += ["Навигация:", ""] + _table(("уровень", "элемент", "пункты", "для кого", "активное",
                                                "на узкой ширине"),
                                               [[r.get(x) for x in ("level", "element", "items", "who", "active",
                                                                    "narrow")] for r in nav]) + [""]
    narrow = _map_rows(lay, "Узкий экран", "тип экрана")
    if narrow:
        s.lines += ["На узкой ширине:", ""] + _table(("тип экрана", "reveal", "divide", "resize", "reposition", "swap"),
                                                     [[r.get(x) for x in ("тип экрана", "reveal", "divide", "resize",
                                                                          "reposition", "swap")] for r in narrow])
    return s


def sec_design(c, part):
    s = Section(part.short)
    lay, d = c.lay, c.design
    for key in ("ds-project", "tokens", "tokens-css", "design-md", "system", "app-brief"):
        if d[key].exists():
            s.sources.append(c.src(d[key]))
    conv = _map_rows(lay, "Конвенции", "конвенция")
    if conv:
        s.sources.append(c.src(lay.map_path, "Конвенции"))
    s.sources.append(c.src(COMPONENTS, "types"))
    if c.system is None:
        s.gaps.append("нет карты решений `design/system.yaml` — сопоставление «тип → компонент ДС» собирает этап "
                      "ds-components; макет без неё не собирается")
        c.finding("R-COV-005", "error", "system", "system", d["system"],
                  "этап mockup: нет карты решений design/system.yaml — типам экранов не сопоставить компоненты ДС",
                  f"/design-deep-dive {lay.slug} — этап ds-components")
    comps = _dict((c.system or {}).get("components"))
    exts = {e.get("id"): e for e in (c.system or {}).get("extensions") or [] if isinstance(e, dict)}
    uses = {}
    for slug in c.trees.screens:
        for n in T.screen_nodes(c.trees, slug):
            if n.ui_type:
                uses.setdefault(n.ui_type, set()).add(slug)
    for p in T.main_shells(c.trees):
        for n, _ in T.walk(p.nodes):
            if n.ui_type:
                uses.setdefault(n.ui_type, set()).add(f"каркас {p.slug}")
    for k, t, ph in part.entries:
        if not ph:
            s.lines += [f"{k}: {t}" if k else t, ""]
            continue
        if k.startswith("Источник"):
            have = [f"артефакт Design System — исходники `{c.src(d['ds-project']).path}`" if d["ds-project"].exists()
                    else None, f"адрес артефакта — `{c.src(d['artifacts']).path}`" if d["artifacts"].exists() else None]
            have = [x for x in have if x]
            s.lines += [f"{k}: " + ("; ".join(have) if have else "— (артефакта ДС ещё нет)"), ""]
        elif k == "Токены":
            have = [f"`{c.src(d[x]).path}`" for x in ("tokens", "tokens-css", "design-md") if d[x].exists()]
            s.lines += [f"{k}: " + (", ".join(have) + " — значения только из токенов" if have else "— (токенов ДС "
                                                                                                 "ещё нет)"), ""]
        elif k == "Конвенции размещения":
            s.lines += [f"{k}:", ""] + [f"- {r.get('конвенция')}: {r.get('решение')} ({r.get('норма')})" for r in conv]
            for ck, cv in _dict((c.system or {}).get("conventions")).items():
                if not L.PLACEHOLDER.match(str(cv)):
                    s.lines.append(f"- {ck}: {json.dumps(cv, ensure_ascii=False) if not isinstance(cv, str) else cv}")
            s.lines.append("")
        elif k == "Устаревшее и запрещённое":
            s.lines += [f"{k}: раздел «Запреты» — бан-лист холста и запреты брифа на вид.", ""]
        else:
            s.lines += [f"{k}: —", ""]
            s.gaps.append(f"у поля шаблона «{k}» нет источника в слое проекта")
    rows = []
    for t in sorted(uses):
        comp = comps.get(t)
        name = comp.get("component") if isinstance(comp, dict) else (comp if isinstance(comp, str) else None)
        if name is None and t in exts:
            name = f"расширение {t}"
        rows.append([f"`{t}`", name or ("пробел" if c.system is not None else "—"), ", ".join(sorted(uses[t]))])
    s.lines += ["Типы экранов → компоненты ДС (карта решений `components` и `extensions`):", ""]
    s.lines += _table(("тип", "компонент ДС", "где"), rows)
    return s


def _surface_states(c):
    """S-id поверхности: ключи наборов экранов, ключи `states` и наборы блоков со своим источником."""
    keys = set()
    for slug, res in c.sets.items():
        keys |= {i.key for i in res.items} | {k for k in c.trees.screens[slug].states if k in c.dict.key2id}
    for res in c.own.values():
        keys |= {i.key for i in res.items}
    return [sid for sid in c.dict.states if c.dict.key(sid) in keys]


def sec_states(c, part):
    s = Section(part.short)
    lay = c.lay
    s.sources.append(c.src(lay.folder / "screens", "states"))
    for name in ("situation",):
        if lay.interface.exists(name):
            s.sources.append(c.src(lay.interface.path(name), "refusals"))
    cap = docpaths.layer(lay.slug, "capability", lay.surface, lay.repo)
    if cap.is_file() and lay.product.passports:
        s.sources.append(c.src(cap, "Паспорта: duration"))
    shells = T.main_shells(c.trees)
    for p in shells:
        s.sources.append(c.src(p.record.path, "Состояния приложения"))
    s.sources.append(c.src(S.DICT_PATH))
    d = c.dict
    s.lines += ["Экран, коллекция, форма: состояния — по id словаря, а не словами; набор каждого экрана — в его "
                "разделе ниже: ключи `states` ∪ обязательный набор, «не применимо» — с причиной.", "",
                f"Приоритет, когда состояний несколько: {' > '.join(f'`{k}`' for k in d.priority)}; поверх "
                f"содержимого: {', '.join(f'`{k}`' for k in d.overlays)}.", ""]
    readme = docpaths.template("screens", "README.md").read_text(encoding="utf-8")
    m = re.search(r"\*\*Пусто — только после загрузки\*\*.*?(?=\n\n)", readme, re.S)
    if m:
        s.lines += [" ".join(x.strip() for x in m.group(0).splitlines()), ""]
    s.lines += ["Состояния поверхности — что показать и что предложить (ux 06/01 §2):", ""]
    s.lines += _table(("S-id", "ключ", "когда", "показать", "предложить"),
                      [[sid, f"`{d.key(sid)}`", d.states[sid].get("when"), d.states[sid].get("show"),
                        d.states[sid].get("offer")] for sid in _surface_states(c)]) + [""]
    for p in shells:
        rows = T.app_state_rows(p.record) or []
        if rows:
            s.lines += [f"Состояния приложения — раз на продукт, в основном каркасе `{p.slug}`:", ""]
            s.lines += _table(("состояние", "где видно", "форма", "тексты"),
                              [[f"`{st}`", r.get("где видно"), r.get("форма"), r.get("тексты")] for st, r in rows])
            s.lines.append("")
    s.lines += [f"{x} — состояния компонента ДС по `kb/common/components.yaml` (`states` типа)."
                for x in c.fixed(part, keys=("Элемент",))]
    return s


def sec_data(c, part):
    s = Section(part.short)
    lay, doc = c.lay, c.demo
    omd = c.proj("object.md")
    if omd.is_file():
        s.sources.append(c.src(omd, "Объекты, Атрибуты"))
    if lay.interface.exists("data-items"):
        s.sources.append(c.src(lay.interface.path("data-items"), "object"))
    for coll in D.collections(lay, c.trees).values():
        if coll.kind == "block":
            s.sources.append(c.src(coll.rec.path, "collection.volume"))
    s.gaps += [f"{g['message']} ({g['path']})" for g in doc["gaps"]]
    for k, t, ph in part.entries:
        if not ph:
            s.lines += [f"{k}: {t}" if k else t, ""]
        elif k == "Набор":
            s.lines += [f"{k}: `{c.demo_ref}` рядом с контрактом — производный (`scripts/project/demo_data.py`, зерно "
                        f"`{doc['seed']}`, «сегодня» — {doc['anchor']}); каждая запись и набор — `example: true`: "
                        "макет на нём допустим, публикация — нет. Числа на экране — только из набора.", ""]
        else:
            s.lines += [f"{k}: —", ""]
            s.gaps.append(f"у поля шаблона «{k}» нет источника в слое проекта")
    rows = []
    for cid, coll in doc["collections"].items():
        cnt = {k: _num(v["count"]) for k, v in coll["sets"].items()}
        rows.append([f"`{cid}`", f"`{coll['object']}`" if coll["object"] else "—", _codes(coll["screens"]),
                     cnt["empty"], cnt["few"], cnt["typical"], cnt["max"],
                     "collection.volume" if coll["volume"] else "ux 13/04 §12 — объёма нет"])
    if rows:
        s.lines += [f"Коллекции — `collections.<id>.sets` (записи — не больше {doc['window']}, count — полный объём):",
                    ""]
        s.lines += _table(("коллекция", "объект", "экраны", "empty", "few", "typical", "max", "объём"), rows) + [""]
    s.lines += ["Объекты — `objects.<объект>`: записи `records`, крайние случаи `edge_cases`:", ""]
    for o, ob in doc["objects"].items():
        cases = ", ".join(e["_case"] for e in ob["edge_cases"]) or "—"
        na = "; ".join(f"{x['case']} — {x['why']}" for x in ob["not_applicable"])
        s.lines.append(f"- `{o}` — {ob['name']}: записей {len(ob['records'])}; крайние случаи: {cases}"
                       + (f"; не применимо: {na}" if na else ""))
    if doc["localization"]:
        s.lines += ["", "Самая длинная строка каждой роли реестра — `localization`: подпись переносится, фиксированные "
                        "ширины не ломаются."]
    return s


def sec_texts(c, part):
    s = Section(part.short)
    lay = c.lay
    ok, bad = text_rows(lay, c.stage, c.keys)
    if lay.texts.exists:
        s.sources.append(c.src(lay.texts_path))
    else:
        c.pre(s, "PRE-11", "нет реестра texts.md — тексты экранов не собрать", "texts", "texts", lay.texts_path,
              c.fix_screens("texts"))
    omd, amd = c.proj("object.md"), c.proj("action.md")
    if omd.is_file():
        s.sources.append(c.src(omd, "Объекты: name, aliases"))
    if amd.is_file():
        s.sources.append(c.src(amd, "verb, past, banned"))
    voice = docpaths.voice(lay.slug, product=True, repo=lay.repo)
    if voice.is_file():
        s.sources.append(c.src(voice))
    s.sources.append(c.src(BANNED))
    if bad:
        by = {}
        for r in bad:
            by.setdefault(r.status or "без статуса", []).append(r.key)
        detail = "; ".join(f"`{st}` — {len(v)}" for st, v in by.items())
        s.gaps.append(f"строки не того статуса ({detail}): на артборде — заглушка {TEXT_PLACEHOLDER}; ключи — "
                      + ", ".join(f"`{r.key}`" for r in bad))
        c.finding("R-MAT-003", "warning", "texts", "texts", lay.texts_path,
                  f"этап mockup берёт только approved: строк не того статуса {len(bad)} ({detail}) — "
                  + ", ".join(r.key for r in bad[:5]) + (f" и ещё {len(bad) - 5}" if len(bad) > 5 else ""),
                  c.fix_screens("texts") + " — утверждает владелец продукта")
    banned_words = []
    for k, t, ph in part.entries:
        if not ph:
            s.lines += [f"{k}: {t}" if k else t, ""]
        elif k == "Глоссарий":
            s.lines += [f"{k} — объекты называются своим именем, синонимы не говорим:", ""]
            for o, ob in c.objs.items():
                s.lines.append(f"- `{o}` — {ob.name}: {_sentence(ob.description)}"
                               + (f" Не говорим: {', '.join(ob.aliases)}." if ob.aliases else ""))
                banned_words += ob.aliases
            s.lines += ["", "Действия — один корень по всему потоку: кнопка, заголовок, сообщение, статус:", ""]
            for a, r in lay.product.actions.items():
                ban = [x for x in D._list(r.get("banned"))]
                banned_words += ban
                s.lines.append(f"- `{a}` — «{(r.get('verb') or '').strip()}» / «{(r.get('past') or '').strip()}»"
                               + (f"; не говорим: {', '.join(ban)}" if ban else ""))
            s.lines.append("")
        elif k == "Запрещённые слова":
            s.lines += [f"{k}: " + (", ".join(dict.fromkeys(banned_words)) or "—") + "; словарь запретов по ролям "
                        "строк — `kb/ux/07-ux-writing/06-banned-words-and-patterns.md`.", ""]
        else:
            s.lines += [f"{k}: —", ""]
            s.gaps.append(f"у поля шаблона «{k}» нет источника в слое проекта")
    if voice.is_file():
        s.lines += [f"Голос продукта — `{c.src(voice).path}`; проекция тона — в брифе холста.", ""]
    statuses = ", ".join(f"`{x}`" for x in STAGE_STATUSES[c.stage])
    s.lines += [f"Строки этапа `{c.stage}` — статусы {statuses}; текст — дословно, число и имя — из данных "
                "(подстановки `{…}`):", ""]
    s.lines += _table(("ключ", "роль", "текст", "maxlen", "статус"),
                      [[f"`{r.key}`", f"`{r.role}`" if r.role else "—", r.text, r.maxlen or "—", f"`{r.status}`"]
                       for r in ok])
    return s


def sec_bans(c, part):
    s = Section(part.short)
    s.sources += [c.src(TEMPLATE, "7.3 (список сбоев ux 11/01 F11.1, F13.1)"), c.src(ETHICS, "8.1")]
    if c.design["app-brief"].exists():
        s.sources.append(c.src(c.design["app-brief"], "core.bans"))
    for k, t, ph in part.entries:
        if not ph:
            s.lines += [f"{k}: {t}" if k else t, ""]
            continue
        body = t.strip().lstrip("<").rstrip(">")
        items = body.split(":", 1)[1] if ":" in body else body
        s.lines += ["Сбои, которых на макете нет (шаблон ux 11/04 §7.3; ux 11/01 F11.1, F13.1):", ""]
        s.lines += [f"- {x.strip()}" for x in items.split(";") if x.strip()] + [""]
    eth = ethics()
    if eth:
        s.lines += ["Этика — закрытый список ux 06/04 §8.1:", ""] + [f"{i}. {x}" for i, x in enumerate(eth, 1)] + [""]
    bans = [b for b in (((c.app_brief or {}).get("core") or {}).get("bans") or []) if not L.PLACEHOLDER.match(str(b))]
    s.lines.append("Бан-лист холста — `brief.yaml` этого входа (`design_system.bans`: приметы дефолтного вида и "
                   "запреты проекта)" + (f"; запреты брифа на вид: {'; '.join(map(str, bans))}." if bans else "."))
    return s


def sec_examples(c, part):
    s = Section(part.short)
    lay = c.lay
    starter = [x for x in ((c.system or {}).get("starter") or []) if isinstance(x, dict)
               and x.get("surface") == lay.surface and not L.PLACEHOLDER.match(str(x.get("screen")))]
    if starter:
        s.sources.append(c.src(c.design["system"], "starter"))
    if c.scen:
        s.sources.append(c.src(lay.interface.path("scenario"), "Happy path, Ветвления"))
    events = _map_rows(lay, "События", "событие")
    if events:
        s.sources.append(c.src(lay.map_path, "События"))
    for k, t, ph in part.entries:
        if not ph:
            s.lines += [f"{k}: {t}" if k else t, ""]
        elif k == "Эталонный экран":
            if starter:
                canvas = docpaths.design(lay.slug, "canvas-project", surface=lay.surface, repo=lay.repo)
                s.lines += [f"{k}: " + ", ".join(f"`{x['screen']}`" for x in starter) + " — принятые экраны макета, "
                            f"исходники — `{c.src(canvas).path}`.", ""]
            else:
                s.lines += [f"{k}: —", ""]
                s.gaps.append("эталонных экранов нет: они появляются после приёмки первых экранов макета "
                              "(`design/system.yaml`, `starter`)")
        elif k == "Описание взаимодействий текстом":
            s.lines += [f"{k}:", ""]
            for sc in c.scen:
                s.lines += [f"Сценарий `{sc.slug}` — {sc.meta.get('name') or sc.slug}:", ""]
                s.lines += [f"{no}. `{L.cell(sit) or '—'}`: {does} → {shows}" for no, sit, does, shows in sc.steps]
                s.lines += [f"- если {cond} (шаг {step}) → {L.cell(to) or to}: {what}" for cond, step, to, what in
                            sc.branches]
                s.lines.append("")
            if not c.scen:
                s.gaps.append("сценариев поверхности нет — взаимодействия только по переходам экранов")
            if events:
                s.lines += ["События — одна форма сообщения на событие (map.md):", ""]
                s.lines += [f"- {r.get('событие')} → {r.get('форма')}" for r in events] + [""]
        else:
            s.lines += [f"{k}: —", ""]
            s.gaps.append(f"у поля шаблона «{k}» нет источника в слое проекта")
    return s


def sec_accept(c, part):
    s = Section(part.short)
    lay = c.lay
    acc = [(sc.slug, x) for sc in c.scen for x in sc.acceptance]
    if acc:
        s.sources.append(c.src(lay.interface.path("scenario"), "Приёмка"))
    else:
        s.gaps.append("у сценариев поверхности нет «Приёмки» — критерии только по состояниям и маршрутам")
    s.sources.append(c.src(S.DICT_PATH, "check"))
    s.lines += [x for f in c.fixed(part) for x in (f, "")]
    if acc:
        s.lines += ["Сценарии:", ""] + [f"- `{sc}`: {x}" for sc, x in acc] + [""]
    s.lines += ["Состояния — как проверить (ux 06/01 §2):", ""]
    s.lines += _table(("S-id", "ключ", "проверка"), [[sid, f"`{c.dict.key(sid)}`", c.dict.states[sid].get("check")]
                                                    for sid in _surface_states(c)]) + [""]
    s.lines.append("Маршруты — только из списка «Карты экранов»; приёмка холста по роду и уровню — `ACCEPTANCE.md` "
                   "этого входа.")
    return s


BUILDERS = {"Контекст продукта": sec_context, "Объектная модель": sec_objects, "Карта экранов": sec_map,
            "Дизайн-система": sec_design, "Обязательные состояния": sec_states, "Данные": sec_data,
            "Тексты": sec_texts, "Запреты": sec_bans, "Примеры": sec_examples, "Критерии приёмки": sec_accept}


# ------------------------------------------------------------------ раздел экрана

def screen_states(c, slug):
    """S-id экрана: ключи `states` ∪ обязательный набор — по порядку словаря, с покрытием и причинами."""
    res = c.sets[slug]
    p = c.trees.screens[slug]
    req = {i.key: i for i in res.items}
    out = []
    for sid in c.dict.states:
        key = c.dict.key(sid)
        sv = p.states.get(key)
        if key not in req and sv is None:
            continue
        item = req.get(key)
        covered = item.covered if item else ("na" if sv.na is not None and sv.na.strip() else
                                             ("delta" if sv.slots else None))
        na = item.na if item else (sv.na if sv is not None else None)
        out.append({"id": sid, "key": key, "required": item is not None, "covered": covered, "na": na,
                    "reasons": list(item.reasons) if item else ["сверх набора — дельта экрана"]})
    return out


def screen_part(c, slug):
    lay = c.lay
    p = c.trees.screens[slug]
    rec, fm = p.record, p.record.fm
    part = ScreenPart(slug=slug, name=str(fm.get("name") or slug).strip(), status=rec.status)
    comp = T.composition(c.trees, slug)
    blocks = comp["blocks"]
    part.sources.append(c.src(rec.path, "поля, slot-fills, states"))
    part.sources += [c.src(lay.blocks[b].path, "tree") for b in blocks if b in lay.blocks]
    fix = c.fix_screens(f"screen:{slug}")
    # запись не разбирается — первая и единственная находка записи: её поля не читаются, и находки о статусе,
    # главной задаче и состояниях были бы следствием разбора, а не пробелами экрана
    broken = record_error(rec)
    if broken:
        c.pre(part, "второй вход", f"запись экрана `{slug}` не разбирается — {broken}: поля записи не читаются, "
                                   "раздел экрана собран без них", "screen", slug, rec.path, fix)
    elif not rec.stable:
        c.pre(part, "второй вход", f"экран `{slug}` — {rec.status or 'без статуса'}: вход холста кабинета "
                                   "собирается на stable-экранах", "screen", slug, rec.path, fix)
    typ, obj = str(fm.get("type") or "").strip(), L.cell(str(fm.get("object") or ""))
    mt, ka = L.cell(str(fm.get("main-task") or "")), L.cell(str(fm.get("key-action") or ""))
    if not mt and typ != "service" and not broken:
        c.pre(part, "PRE-02", f"у экрана `{slug}` нет главной задачи (`main-task`)", "screen", f"{slug}#/main-task",
              rec.path, fix)
    caps, acts = lay.product.capabilities, lay.product.actions
    row = c.derived.screens.get(slug) or {}
    route = c.derived.routes.get(slug) or {}
    o = c.objs.get(obj) if obj else None
    part.lines.append(f"- Тип `{typ or '—'}` · объект " + (f"`{obj}` — {o.name}" if o else f"`{obj}`" if obj else "—")
                      + f" · статус `{rec.status or '—'}`")
    part.lines.append("- Главная задача: " + (f"`{mt}` — {(caps[mt].get('name') or '').strip()}" if mt in caps else
                                              f"`{mt}`" if mt else "—"))
    part.lines.append("- Ключевое действие: " + (f"`{ka}` — «{(acts[ka].get('verb') or '').strip()}»" if ka in acts else
                                                 f"`{ka}`" if ka else "— (экран только для чтения)"))
    mrow = {L.cell(r.get("screen")): r for r in _map_rows(lay, "Карта экранов", "screen")}.get(slug)
    entry = M.entry_items(mrow.get("entry-points")) if mrow is not None else row.get("entry-points") or []
    part.lines.append(f"- Для кого: {_codes(M._list(fm.get('who')))} · плотность: {row.get('density') or '—'} · "
                      f"точки входа: {', '.join(entry) or '—'}")
    part.lines.append(f"- Маршрут `{route.get('route') or '—'}` · параметры {M.cparams(route.get('params'))} · доступ "
                      f"`{route.get('access') or '—'}` · в адресе: {', '.join(route.get('url-state') or []) or '—'} · "
                      f"вьюпорт `{L.cell(str(fm.get('viewport') or '')) or '—'}`")
    slots = []
    for name, f in p.fills.items():
        slots.append(f"`{name}` — " + (f"блок `{f.block}`" if f.kind == "block" else "дерево" if f.kind == "tree"
                                       else "пусто"))
    part.lines.append(f"- Каркас `{fm.get('shell') or '—'}`: " + ("; ".join(slots) or "—"))
    types = sorted({n.ui_type for n in T.screen_nodes(c.trees, slug) if n.ui_type})
    part.lines.append(f"- Блоки: {_codes(blocks)}; компоненты: {', '.join(types) or '—'}")
    trs = M.transitions(fm)
    part.lines.append("- Переходы: " + ("; ".join(f"→ `{t.get('to')}` ({_trigger(lay, t.get('trigger'))}; "
                                                  f"сохраняется: {t.get('keeps') or '—'}; "
                                                  f"назад: {t.get('back') or '—'})" for t in trs) or "—"))
    sits = M._list(fm.get("situations"))
    scs = [sc.slug for sc in c.scen if any(L.cell(st[1]) in sits for st in sc.steps)]
    part.lines.append(f"- Ситуации: {_codes(sits)}; сценарии: {_codes(scs)}")
    doc = c.demo
    data = []
    for cid, coll in doc["collections"].items():
        if slug in coll["screens"]:
            cnt = " · ".join(f"{k} {_num(v['count'])}" for k, v in coll["sets"].items())
            data.append(f"коллекция `{cid}` → `{c.demo_ref}` `collections.{cid}` ({cnt})")
    items = D.items_of(lay, [p] + [c.trees.blocks[b] for b in blocks if b in c.trees.blocks])
    objs = [x for x in dict.fromkeys(([obj] if obj else []) + items) if x in doc["objects"]]
    data += [f"`{x}` → `objects.{x}.records` (`{x}-1` …), крайние случаи — `objects.{x}.edge_cases`" for x in objs]
    part.lines.append("- Данные: " + ("; ".join(data) or "—"))
    comps = lay.components
    mine = {id(p)} | {id(c.trees.blocks[b]) for b in blocks if b in c.trees.blocks}
    keys = list(dict.fromkeys(u.key for u in T.text_uses(c.trees, comps) if id(u.parsed) in mine))
    allowed = STAGE_STATUSES[c.stage]
    rows = lay.texts.rows
    miss = [k for k in keys if k not in rows or rows[k].status not in allowed]
    part.lines.append(f"- Тексты — {len(keys)} {_plural(len(keys), 'ключ', 'ключа', 'ключей')}, строки — в "
                      f"разделе «Тексты»: {_codes(keys)}"
                      + (f"; не этого этапа или нет строки: {_codes(miss)}" if miss else ""))
    part.states = screen_states(c, slug)
    part.lines += ["", "### Обязательные состояния", ""]
    part.lines += _table(("S-id", "ключ", "покрытие", "почему в наборе"),
                         [[x["id"], f"`{x['key']}`", _covered(x["covered"], x["na"]), "; ".join(x["reasons"])]
                          for x in part.states])
    uncovered = [x for x in part.states if x["required"] and not x["covered"]]
    if uncovered and not broken:
        c.pre(part, "PRE-08", f"у экрана `{slug}` не покрыты обязательные состояния: "
                              + ", ".join(f"{x['id']} `{x['key']}`" for x in uncovered), "screen", f"{slug}#/states",
              rec.path, fix)
    for b in blocks:
        if b in c.own:
            its = c.own[b].items
            part.own[b] = [{"id": i.id, "key": i.key, "covered": i.covered, "na": i.na} for i in its]
            part.lines += ["", f"Блок `{b}` со своим источником — свой набор: " + ", ".join(
                f"{i.id} `{i.key}` ({_covered(i.covered, i.na)})" for i in its)]
    res = c.sets[slug]
    have = {x["key"] for x in part.states}
    part.manual = [{"key": m["key"], "why": m["why"]} for m in res.manual if m["key"] not in have]
    if part.manual:
        part.lines += [""] + [f"По решению поверхности — `{m['key']}`: {m['why'].split(':', 1)[0]}; состояние "
                              "решает экран, в набор оно не входит." for m in part.manual]
    return part


# ------------------------------------------------------------------ сборка и проверка

def build(lay, stage="mockup", demo=None, demo_ref=DEMO_FILE, screens=None):
    """Контракт поверхности → Contract (разделы шаблона по порядку и раздел на экран); screens — партия экранов:
    разделы, строки текстов, демо-набор и находки — только её."""
    c = Ctx(lay, stage, demo, demo_ref, screens)
    kind = lay.surf.type + (f" рода {lay.surf.web_kind}" if lay.surf.web_kind else "")
    con = Contract(project=lay.slug, surface=lay.surface, kind=kind, stage=stage, demo_ref=demo_ref, demo=c.demo,
                   keys=c.keys, units=list(c.units), outside=list(c.outside))
    for part in c.parts:
        fn = BUILDERS.get(part.short)
        if fn is None:
            raise F.ToolError(f"раздел шаблона §7.3 «{part.short}» без сборщика — разделы: {', '.join(BUILDERS)}")
        con.sections.append(fn(c, part))
    con.screens = [screen_part(c, slug) for slug in c.units]
    items = F.Report()
    # пункт PRE-14 демо-набора (объём коллекции) — тоже пункт блока PRE: доклад, как остальные
    items.extend(replace(f, severity="warning") if f.rule == "R-MAT-011" and f.severity == "error" else f
                 for f in D.gaps(lay, c.trees)
                 if c.scope is None or _in_scope(f.ref, c.scope, set(c.demo["objects"])))
    items.extend(c.rep.items)
    con.findings = items.items
    return con


def render(lay, stage="mockup", demo=None, demo_ref=DEMO_FILE):
    return build(lay, stage, demo, demo_ref).render()


def check(lay, stage="mockup"):
    """Пробелы источников контракта и демо-набора — находки."""
    return build(lay, stage).findings


# ------------------------------------------------------------------ вызов

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return _selftest()
    ap = docpaths.parser("contract", __doc__, commands=("build", "check"), surface="optional", stages=STAGES,
                         accept=lambda s: s.app)
    call = docpaths.parse(ap, argv)
    stage = call.stage or "mockup"
    try:
        lays = T.layers_of(call)
        if not lays:
            print(f"contract: у проекта {call.slug} нет поверхностей кабинета (web рода app, admin, desktop, embed)",
                  file=sys.stderr)
            return F.EXIT_USAGE
        if call.command == "check":
            items = []
            for lay in lays:
                items += check(lay, stage)
            F.print_findings(items, as_json=call.json)
            return F.exit_code(items)
        if len(lays) != 1:
            ap.error("build — одна поверхность: contract build <slug> <surface>; поверхности кабинета: "
                     + ", ".join(x.surface for x in lays))
        con = build(lays[0], stage)
        if call.out is not None:
            target = Path(call.out) / "contract.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(con.render(), encoding="utf-8")
            print(json.dumps({"surface": con.surface, "stage": stage, "path": str(target)}, ensure_ascii=False)
                  if call.json else f"{con.surface}: {target}")
        elif call.json:
            print(json.dumps(con.as_dict(), ensure_ascii=False, indent=1))
        else:
            sys.stdout.write(con.render())
        return F.EXIT_OK
    except (F.ToolError, docpaths.DocPathError, RuntimeError, OSError, ValueError) as e:
        print(f"contract: {e}", file=sys.stderr)
        return F.EXIT_USAGE


# ------------------------------------------------------------------ самопроверка

def _h2(text):
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def _selftest():
    import shutil
    import subprocess
    import tempfile
    ok = True

    def check_(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)

    parts = template()
    names = [p.short for p in parts]
    check_("шаблон ux 11/04 §7.3: десять разделов, те же, что в каноне экранов («Что слой отдаёт макету»)",
           len(names) == 10 and names == readme_names())
    check_("у каждого раздела шаблона — сборщик", all(n in BUILDERS for n in names))
    fixed = [t for p in parts for k, t, ph in p.entries if not ph and k == "ЗАПРЕТ"]
    check_("строки-нормы шаблона: запрет маршрутов вне списка и чисел без источника",
           any("маршруты вне списка" in t for t in fixed) and any("числа без источника" in t for t in fixed))
    check_("этика ux 06/04 §8.1 — 22 пункта", len(ethics()) == 22)
    check_("строки шаблона: продолжение строчной буквой и незакрытая «<»",
           _entries("Правила: a;\nb.\n<список: x;\nY; z>") == [("Правила", "a; b.", False), (None, "<список: x; Y; z>",
                                                                                              True)])
    kbpaths.use("tests")
    import fixture_project
    with fixture_project.built("cabinet-demo") as fx:
        lay = L.Layer(fx.slug, "office", fx.root)
        con = build(lay, "mockup")
        text = con.render()
        h2 = _h2(text)
        check_("contract build: десять разделов в порядке §7.3, затем раздел на каждый экран",
               h2[:10] == names and h2[10:] == [f"Экран `{s}` — {lay.screens[s].fm.get('name')}"
                                                for s in sorted(lay.screens)])
        check_("у каждого раздела — источник, пути существуют", all(
            sec.sources and all(((fx.root if not x.path.startswith("kb/") else kbpaths.kb().parent) / x.path).exists()
                                for x in sec.sources) for sec in con.sections + con.screens))
        dump = S.dump(lay)
        same = True
        for p in con.screens:
            want = {i["key"] for i in dump["screens"][p.slug]["required"]} | {
                k for k in T.parse_layer(lay).screens[p.slug].states if k in S.dictionary().key2id}
            same = same and {x["key"] for x in p.states} == want and all(x["id"] == S.dictionary().key2id[x["key"]]
                                                                        for x in p.states)
        check_("S-id раздела экрана = набор states ∪ ключи states экрана", same)
        card = next(p for p in con.screens if p.slug == "request-card")
        check_("«не применимо» — с причиной; карточка: not-found и offline", any(
            x["covered"] == "na" and x["na"] for p in con.screens for x in p.states) and
            {"not-found", "offline"} <= {x["key"] for x in card.states})
        rules = {(f.rule, f.severity) for f in con.findings}
        check_("чистая фикстура без ДС: находки — только R-MAT-003 warning (одна на реестр) и R-COV-005 error без "
               "карты решений ДС; пробел ДС — и пометкой раздела",
               rules == {("R-MAT-003", "warning"), ("R-COV-005", "error")}
               and len([f for f in con.findings if f.rule == "R-MAT-003"]) == 1
               and any("design/system.yaml" in g for g in con.sections[3].gaps))
        check_("повторная сборка — тот же текст байт в байт", render(L.Layer(fx.slug, "office", fx.root)) == text)
        mt = con.sections[6]
        check_("тексты макета — только approved (8 строк), прочие — пробел",
               len([line for line in mt.lines if line.startswith("| `")]) == 8 and mt.gaps)
        m3 = next((f for f in con.findings if f.rule == "R-MAT-003"), None)
        check_("R-MAT-003: 45 строк не того статуса — пять ключей и хвост «и ещё 40»",
               m3 is not None and "строк не того статуса 45" in m3.message and m3.message.endswith(" и ещё 40"))
        d = con.as_dict()
        check_("JSON: разделы с источниками, экраны с наборами", len(d["sections"]) == 10 and
               all(s["sources"] for s in d["sections"]) and all(p["states"] for p in d["screens"]))
        check_("данные — наборы коллекции и ссылка на demo-data.json",
               "`requests-list`" in "\n".join(con.sections[5].lines) and "demo-data.json" in text)
        check_("запреты: список сбоев, этика, бан-лист холста", "- отсутствующий интерактивный элемент" in
               con.sections[7].lines and "brief.yaml" in "\n".join(con.sections[7].lines))
        check_("примеры: шаги сценария и события", any("`find-request`" in x for x in con.sections[8].lines) and
               any("`create` →" in x for x in con.sections[8].lines))
        script = HERE / "contract.py"
        with tempfile.TemporaryDirectory(prefix="ddd-contract-") as td:
            r = subprocess.run([sys.executable, str(script), "build", fx.slug, "office", "--repo", str(fx.root)],
                               cwd=td, capture_output=True, text=True)
            check_("build из чужой рабочей папки с --repo — тот же contract.md", r.returncode == 0 and r.stdout == text)
            r = subprocess.run([sys.executable, str(script), "build", fx.slug, "office", "--repo", str(fx.root),
                                "--stage", "mockup", "--out", str(Path(td) / "in")], cwd=td, capture_output=True,
                               text=True)
            check_("build --stage mockup --out: DIR/contract.md", r.returncode == 0 and
                   (Path(td) / "in" / "contract.md").read_text(encoding="utf-8") == text)
            r = subprocess.run([sys.executable, str(script), "check", fx.slug, "--repo", str(fx.root), "--json"],
                               cwd=td, capture_output=True, text=True)
            check_("check --json без поверхности — строки находок; error — только R-COV-005 (карты решений ДС нет), "
                   "код 1", r.returncode == 1 and
                   {f.rule for f in F.parse_lines(r.stdout) if f.severity == "error"} == {"R-COV-005"})
            r = subprocess.run([sys.executable, str(script), "check", fx.slug, "office", "--repo", str(fx.root),
                                "--stage", "mockup"], cwd=td, capture_output=True, text=True)
            check_("check --stage mockup без ДС — код 1", r.returncode == 1 and "R-COV-005" in r.stdout)
            root = Path(td) / "r"
            shutil.copytree(fx.root, root)
            proj = root / "docs" / "projects" / fx.slug
            scr = proj / "screens" / "office" / "screens" / "requests-list" / "index.md"
            text2 = scr.read_text(encoding="utf-8").replace("status: stable", "status: draft", 1)
            scr.write_text(text2.replace("  error-load:\n    main:\n      - ui:Alert:\n          - text:requests.list."
                                         "error-load.inline-message\n          - ui:Button level=secondary:\n"
                                         "              - text:requests.list.retry.action\n", "", 1), encoding="utf-8")
            blk = proj / "screens" / "office" / "blocks" / "requests-list" / "index.md"
            blk.write_text(blk.read_text(encoding="utf-8").replace("  volume: {typical: 60, max: 3000}\n", "", 1),
                           encoding="utf-8")
            usr = proj / "user.md"
            usr.write_text("\n".join(x for x in usr.read_text(encoding="utf-8").splitlines()
                                     if not x.startswith("| `surveyor` | `—`")) + "\n", encoding="utf-8")
            items = check(L.Layer(fx.slug, "office", root))
            got = {f.message.split(":")[0] for f in items if f.rule == "R-MAT-011"}
            check_("пробелы PRE: экран draft, состояние не покрыто, постура, объём коллекции — R-MAT-011 warning "
                   "(доклад): error — только R-COV-005 (карты решений ДС нет)",
                   {"второй вход", "PRE-08", "PRE-01, PRE-04", "PRE-14"} <= got and all(
                       f.severity == "warning" for f in items if f.rule == "R-MAT-011")
                   and {f.rule for f in items if f.severity == "error"} == {"R-COV-005"})
            check_("у находки — путь файла проекта", all(f.path.startswith("docs/projects/") for f in items))
            card = proj / "screens" / "office" / "screens" / "request-card" / "index.md"
            card.write_text(re.sub(r"(?m)^name: .*$", "name: Карточка: заявка", card.read_text(encoding="utf-8"),
                                   count=1), encoding="utf-8")
            lay3 = L.Layer(fx.slug, "office", root)
            mine = [f for f in check(lay3) if f.ref.split("#")[0] == "request-card"]
            check_("двоеточие в name экрана — одна находка: запись не разбирается, причина — frontmatter; находок о "
                   "статусе, главной задаче и состояниях этой записи нет",
                   len(mine) == 1 and mine[0].rule == "R-MAT-011" and mine[0].severity == "warning"
                   and "не разбирается" in mine[0].message and "frontmatter" in mine[0].message
                   and record_note(lay3.screens["request-card"]) == "не разбирается")
            # партия экранов: экран вне партии (draft requests-list) находок не даёт, объём его коллекции — тоже
            part = build(L.Layer(fx.slug, "office", root), "mockup", screens=["plan-dashboard"])
            keys = set(part.keys or [])
            texts = [line for line in part.sections[6].lines if line.startswith("| `")]
            check_("партия plan-dashboard: раздел одного экрана, вне партии — экраны со статусом, без их находок",
                   [p.slug for p in part.screens] == ["plan-dashboard"] and part.units == ["plan-dashboard"]
                   and ("requests-list", "draft") in part.outside
                   and not [f for f in part.findings if f.rule == "R-MAT-011"
                            and f.ref.split("#")[0] in ("requests-list", "request-card")]
                   and "Экраны партии: `plan-dashboard`; вне партии —" in part.render())
            check_("партия: тексты и находка о статусе — только ключи экранов партии, демо-набор — без чужих коллекций",
                   keys and all(line.split("`")[1] in keys for line in texts)
                   and "requests-list" not in part.demo["collections"] and part.demo["objects"]
                   and all(g["path"] != "docs/projects/otves-office/screens/office/blocks/requests-list/index.md"
                           for g in part.demo["gaps"]))
    print("contract selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
