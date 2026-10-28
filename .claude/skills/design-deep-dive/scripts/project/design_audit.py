#!/usr/bin/env python3
"""design_audit — структурный прогон правил `/design-audit` по файлам проекта: слой страницы `site/<surface>/`, слой
дизайна `design/`, факты и голос продукта.

Спецификация — реестр правил `.claude/skills/design-audit/references/rules.md` (id `R-<КАТЕГОРИЯ>-NNN`), уровни
тяжести и отчёт — `.claude/skills/design-audit/SKILL.md`. Утилита проверяет детерминированные правила сама или вызовом
валидаторов баз и утилит `project/`, находку вызванной утилиты переводит в правило реестра; правила, которым нужно
чтение или слово человека, перечисляет для скилла — что прочитать. Суждений модели в коде нет: смысл, облик и вкус —
чтение скилла и макетный прогон по просьбе заказчика. Отчёт `last-report.md` пишет скилл, не утилита.

    design_audit check <slug> [<surface>] [--repo DIR] [--today ГГГГ-ММ-ДД] [--visual-list] [--out DIR] [--json]
        структурный прогон R-SURF → R-STRUCT → R-REF → R-COV → R-PROJ → R-FRESH → R-MAT → R-SEM → R-DEBT; без
        <surface> — уровень продукта и все поверхности со слоем страницы или дизайна, папки вне реестра и поверхности
        маршрута дизайна без папок (подсказкой); --visual-list — в сводку перечень макетного прогона R-VIS
    design_audit visual <slug> <surface> --report [ЕДИНИЦА=]ОТЧЁТ.json … [--repo DIR] [--json]
        отчёты mockup_checks.py page (JSON) макетного прогона → находки R-VIS-001 по шкале ворот и сводка примет по
        доменам в единице домена (страница или экран одного прогона; домены и единицы не складываются); находка,
        снятая ключом --allow реестра примет (поле allowed отчёта), в R-VIS-001 не идёт — строка «Заметка» называет
        её с ключом и причиной (поле reason находки)
    design_audit --selftest       фикстуры package-landing и package-cabinet (0 error), package-defects (14
                                  посеянных дефектов — шапки манифестов package-*-defects), сценарии правил на
                                  копиях фикстур package-landing, input-site и package-cabinet, без сети

Вывод check: без --json — отчёт по группам (уровень продукта, затем поверхность → категория → error, warning, hint),
сводка и список правил чтением; с --json — только строки находок контракта `findings.py` (поля rule, severity,
surface, kind, ref, path, message, fix). Полный результат всегда пишется в папку выхода (по умолчанию
$DDD_HOME/out/project/design_audit/<slug>/): findings.jsonl и summary.json — счёт, какие утилиты запускались и с каким
итогом, этап поверхностей, правила чтением (id, что прочитать), перечень R-VIS с --visual-list, заметки.
Ключи summary.json: tool, project, surface, root, today, utilities, called (утилита → итоги вызовов, «код N» — код
выхода), surfaces (surface, type, web_kind, route, input_stage — этап действующего входа холста, accepted — единицы с
принятым макетом, ready — статус манифеста готовности ready.yaml: ready · partial · not-ready, null — манифеста нет),
counts, notes, reading, visual. Коды в called — один порядок утилит скилла: 0 — error нет; 1 — есть error (находки
вызванной утилиты — в отчёте по правилам или отброшены по реестру); 2 — сбой вызова или окружения; 3 у
text/copydeck.py check — сверка фактов не отработала: заметка сводки с причиной, находки сверки copy deck неполны.
Заметки сводки (notes) называют и обходы copy deck с причинами: claims_allow — поле allowed вывода copydeck.py check,
lint_allow — его заметки.

Тяжесть — по правилу реестра: где правило зависит от этапа, этап выводится из статусов файлов (вход холста страницы
или поверхности, закрытый copy deck, закрытая арт-дирекция, вердикт REVIEW.md); у находки валидатора — его уровень
(error → error, warning → warning, сведения не переносятся), кроме правил с тяжестью по закрытию файла (R-REF-006 из
ad_check: warning, error у закрытой арт-дирекции); шкала ворот и приёмки B/S/D → error/warning/hint. R-FRESH-005 —
статичные копии артбордов — сверяется только при постоянной просьбе заказчика о проверках макета (строка «Проверки
макета: разрешены» в ARTIFACTS.md): копии нужны скриптам проверок, а оригинал макета — холст в claude.ai; без строки
копий может не быть, и это не находка и не заметка; манифест кадров kit.json в git не хранится и не сверяется.
R-COV-002 — error под гейтом 2: у страницы строка «Приёмка» в REVIEW.md или она в партии действующего входа холста
(поле units INPUT.md или папка pages/<id>/) этапа mockup или motion; в партии входа направлений или подачи — warning
(тексты — до макета); закрытый copy deck без текста в слоте — error; слот без текста у образца шаблона
коллекции (страница copy deck с site_page_id = id плана) — warning: запись коллекции может слот не вести. Одобрение
единицы (R-MAT-004) сверяется с отпечатком `ready`: артборды и источники единицы. Непройденный пункт S и исключение
ворот (R-MAT-005) — по единице: исключение `x-gate-exception` плана снимает пункт только у своей страницы.
Ключ ассета — страница и слот: строка манифеста ассетов с полем page сверяется с планом ассетов этой страницы, без
page — общая для страниц с таким слотом, у которых нет своих строк (R-MAT-007, R-MAT-008, R-REF-008, R-COV-009); строка
манифеста — на файл, слот принят, когда принята хотя бы одна его строка. Источник файла (R-MAT-008) — у варианта плана
ассетов, который называет строка манифеста (`variants[].source`); у варианта без поля — источник слота. R-MAT-013 —
общие шапка и подвал: у страниц с той же секцией роли header или footer (блок и вариант; хлебные крошки — секция своей
страницы) набор слотов плана и выбранные тексты copy deck равны, расхождение — warning с парой страниц и слотом.
R-MAT-014 — загрузки принятых артбордов: файл загрузки `/_blob/<id>` (строка «Загрузок» ARTIFACTS.md) — из манифеста
ассетов или демо-кадр `x-demo` плана ассетов этой страницы, иначе error у принятой единицы. R-FRESH-007 — колонка
sha256 «Загрузок» ARTIFACTS.md против файла: расхождение — warning, отпечатка нет — одна подсказка со счётом, файла нет
на машине — заметка сводки.
R-REF-001 у ссылок плана на файлы следующих этапов — hint, пока этап не начат: refs.copy_deck — copy deck страницы
не заведён, refs.asset_plan — плана ассетов страницы нет, refs.treatment — арт-дирекции поверхности нет. Страницы copy
deck с site_page_id = id плана — образцы шаблона коллекции (page.template): их стык с планом сверяет R-REF-003.
R-MAT-009 — error у вопроса, который держит закрытие, hint у блокера публикации (пункт называет пробел фактов
missing[] по id). R-COV-005 «нет карты решений» у сайта до этапа дизайн-системы (арт-дирекция не утверждена, токенов ДС
нет) — hint. R-COV-007: у продукта без поверхностей рода landing и site профиль голоса один — voice.product.yaml с
каналом product-ui. R-PROJ-001…003: источник первичен, копия его поля в брифе на вид и арт-дирекции необязательна —
сверяется только записанная копия, расхождение — warning.
Ошибки публикуемости фактов из claims_check.py lint-facts (разрешение, срок, проверка) в R-STRUCT-003 не идут: их сверяет
R-COV-003 там, где факт стоит (план, copy deck). Предупреждение SM-22 site_validate (служебный шаблон без плана) в
отчёт не идёт: страницу без плана называет R-COV-001 аудита; PL-U01 (план approved без записи approval) и PL-F08
(значения цели-контакта нет у machine фактов) — по одной находке со списком планов. Совет находки называет этап: у
site_validate — по коду (SB-* — brief, SM-* — site-map, PL-* — page-plan; значение контакта PL-F08 и SM-24 — meaning),
факты и голос — meaning, copy deck — copy. Правило, которое утилита не проверила (свежесть производных при
битых токенах; артефакт ДС без токенов DTCG system.tokens.json и system.tokens.css — ds_build не зовётся), — заметка
сводки, а не находка.
Окружение не установлено (нет PyYAML или jsonschema в Python окружения) — валидаторы не запускаются, в сводке —
«утилиты не запускались», их правила уходят в чтение.

Какие утилиты зовутся: site_validate.py (папка слоя страницы), vocab_lint.py (бриф, карта, планы, copy deck и факты),
page_gates.py --resolve (профиль бюджета каждого плана), copydeck.py check, claims_check.py lint-facts,
validate_any.py, validate_voice.py, spec_check.py spec, ad_check.py, vlm_to_dna.py validate, plan_to_assets.py check,
утилиты project/ — ds_build (check), ds_coverage, canvas_input (check; у кабинета со входом в неё входят находки
contract и demo_data), screen_map (check — только расхождения свода для R-MAT-011), ready (check),
claude-design/dc_to_html.py check (при строке «Проверки макета: разрешены»); находки утилит экранов (tree, states) —
правила /screen-audit, сюда они не переносятся.
Код выхода: 0 — ошибок нет; 1 — есть error; 2 — ошибка вызова или окружения.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "lib"))
import kbpaths  # noqa: E402
import docpaths  # noqa: E402
import findings as F  # noqa: E402

TOOL = "design_audit"
CATEGORIES = ("R-SURF", "R-STRUCT", "R-REF", "R-COV", "R-PROJ", "R-FRESH", "R-MAT", "R-SEM", "R-DEBT", "R-VIS")
RULES_MD = (".claude", "skills", "design-audit", "references", "rules.md")
STATE = (".claude", "skills", "entrypoint", "state", "projects")
CLOSED = {"site-brief": ("approved",), "meaning": ("approved",), "hierarchy": ("approved",), "voice": ("approved",),
          "facts": ("confirmed",), "site-map": ("approved",), "page-plan": ("approved",), "copy-deck": ("approved",),
          "brand": ("verified",), "design-system": ("approved",), "app-brief": ("approved",),
          "art-direction": ("approved",), "visual-dna": ("approved",), "asset-plan": ("approved",),
          "motion-spec": ("approved",)}
ACCEPTED = ("accepted", "accepted_with_notes")
TEXT_GATE_STAGES = ("mockup", "motion")                   # этапы входа холста под гейтом 2: тексты — утверждённые
COPYDECK_NO_CLAIMS = 3                                    # особый исход copydeck.py check: сверка фактов не отработала
SITE_FILES = ("site-brief.yaml", "meaning.yaml", "site-map.yaml")
SITE_DIRS = ("hierarchy", "plans", "copy")
DESIGN_SURF = ("art-direction.json", "visual-dna.json", "assets", "motion", "canvas", "input", "review", "ready.yaml")
PAGE_ONLY = ("art-direction.json", "visual-dna.json", "motion")
GATE = {"critical": "error", "major": "warning", "minor": "hint"}
BSD = {"B": "error", "S": "warning", "D": "hint"}
LOOK = ("#", "rgb(", "hsl(", "px", "rem", "font-", "шрифт", "палитр", "градиент", "тень")
# Папка итерации в review/ — имя с номером, датой или словом о прошлом прогоне (iter-02, round3, v2, 2026-09-30, prev);
# папка машинных отчётов последнего результата (checks/, shots/, кадры ширины 390/) — не итерация: номер итерации — до
# двух цифр, ширина артборда — от трёх.
ITER_DIR = re.compile(r"^(?:(?:iter(?:ation)?|round|run|pass|rev|итерац[а-яё]*|раунд|проход|прогон|верси[а-яё]*)"
                      r"[-_. ]?\d+|[vr]\d+|\d{1,2}|\d{4}-\d{2}-\d{2}|\d{8}|prev(?:ious)?|old|archive|history|backup"
                      r"|архив|прошл(?:ое|ая|ые|ый)|стар(?:ое|ая|ые|ый))(?:[-_. ].*)?$", re.I)

# Правила, которые утилита проверяет не целиком или не проверяет: id → что прочитать скиллу. Правило вне словаря
# утилита проверяет целиком; сверку со списком реестра держит самопроверка.
READING = {
    "R-STRUCT-001": "раскладку сверяет утилита; «своя форма поля вместо схемы базы» — чтением файлов слоя против схем",
    "R-STRUCT-004": "арт-дирекция — чек-лист creative 01/02 § Чек-лист чтением; схему, паспорт и ссылки проверяет "
                    "ad_check.py",
    "R-STRUCT-005": "файлы ассетов — asset_audit.py, check_icons.py, provenance_check.py по типу файла: в структурный "
                    "прогон не входят (нужны модели и бинарники окружения); план ассетов проверяет plan_to_assets.py",
    "R-STRUCT-006": "контраст пар токенов проекта (lib/color.py contrast) и строка слабой пары в «известных проблемах» прозы "
                    "DESIGN.md — чтением; формат DTCG, ссылки и режимы проверяет ds_build",
    "R-STRUCT-007": "значения границ: у сайта — blocks.yaml#conventions.breakpoints, у приложения — ui 09/04 §1.3, у "
                    "смешанного продукта — одна шкала с именами по смыслу; наличие breakpoint.* и size.panel.* "
                    "проверяет утилита",
    "R-REF-005": "id блоков, слотов, событий и форм сверяют site_validate.py и vocab_lint.py; poster 3D-слота — "
                 "чтением плана",
    "R-REF-006": "site-brief.ambition.allow.markers — слово заказчика в журнале вопросов брифа: чтением",
    "R-COV-008": "получатели брифа (analytics.crm, constraints.integrations) сверяются со строками integration.md по "
                 "любому слову; сомнительное сопоставление — чтением",
    "R-COV-009": "мастер-файлы и исходники генераций вне git — `git ls-files` по папкам дизайна; бюджет типа — "
                 "asset_audit.py",
    "R-PROJ-001": "app_type, ai_layer, mobile_scope, constraints.accessibility, раздел surfaces.<surface> — чтением "
                  "vision, паспортов ai и свода map.md; постуры, указатели, статусы и ограничения сверяет утилита",
    "R-MAT-002": "у брифа — вопросы приоритета 1 закрыты: чтением журнала вопросов; записи закрытия, выбор и "
                 "text_hash copy deck, конвенции ДС сверяет утилита",
    "R-MAT-005": "пункты S, принятые строкой итога REVIEW.md, — чтением: кто принял",
    "R-MAT-006": "разовая просьба заказчика о проверке следа в файлах не оставляет — одним вопросом человеку "
                 "(AskUserQuestion), если в review/ есть результаты проверок, а строки «Проверки макета» нет",
    "R-MAT-007": "порядок во времени — по заметке пропусков ветки дизайна; утилита сверяет статусы",
    "R-MAT-010": "поле ядра без источника — вопрос questions[] со статусом assumed и долг в заметке пропусков: чтением",
    "R-SEM-001": "облик в брифе (кроме brand.expression и уровня), смысле, иерархиях, плане вне treatment и в copy "
                 "deck — смысловой разбор, а не поиск по словам",
    "R-SEM-002": "референсы отклонённых направлений в мудборде — чтением; поля журнала и статусы сверяет утилита",
    "R-SEM-003": "голос в прозе ДС и в брифе холста — проекция projections.tone_of_voice профиля голоса, а не свой "
                 "текст",
    "R-SEM-004": "метафора пустого состояния — одна на смысл пустоты и повторяется на экранах с тем же смыслом",
}
VISUAL = {
    "R-VIS-001": "кадры статичных копий артбордов (kit/shot.py --manifest kit.json) → mockup_checks.py page → "
                 "ui_audit.py, у сайта — marketing_audit.py; отчёты — design_audit visual (сводка по доменам)",
    "R-VIS-002": "claims_check.py на копиях: числа, отзывы, подписи и alt против фактов, текстов и списка ассетов "
                 "входа",
    "R-VIS-003": "пункты input/ACCEPTANCE.md места «макет» у принятых страниц и экранов — способом пункта",
    "R-VIS-004": "literal_tokens.py check <slug> <surface> --accepted: литералы облика в исходниках холста против "
                 "токенов ДС",
    "R-VIS-005": "агент design-judge, вызов «рубрика»: один пакет asset_audit.py judge-jobs --mode checklist --runs 3 "
                 "(три прогона — задания пакета), разбор judge-parse — находка из двух; пока скрипты или сверка "
                 "фактов красные, судья не зовётся",
}
# Секция роли header, которую страницы не делят: хлебные крошки — путь своей страницы, её слоты и тексты у каждой свои.
OWN_CHROME = ("breadcrumbs",)
BLOB = re.compile(r"/_blob/([A-Za-z0-9_-]+)")              # загрузка холста на артборде: /_blob/<id загрузки>


# ------------------------------------------------------------------ окружение и модули соседей

def _reexec_venv():
    """Без PyYAML или jsonschema в текущем Python — один перезапуск в Python окружения скилла."""
    import importlib.util
    if all(importlib.util.find_spec(m) for m in ("yaml", "jsonschema")):
        return
    py = kbpaths.python()
    if os.environ.get("DDD_AUDIT_VENV") or not Path(py).exists():
        return
    os.environ["DDD_AUDIT_VENV"] = "1"
    os.execv(py, [py, str(Path(__file__).resolve())] + sys.argv[1:])


def env_ok():
    import importlib.util
    return all(importlib.util.find_spec(m) for m in ("yaml", "jsonschema"))


_MOD = {}


def mod(name):
    """Модуль соседней утилиты по имени: project/ — рядом; dc_to_html (claude-design), kit_manifest (claude-design/kit),
    claims_check (text)."""
    if name not in _MOD:
        import importlib
        if name == "dc_to_html":
            kbpaths.use("claude-design")
        elif name == "kit_manifest":
            kit = str(kbpaths.scripts("claude-design", "kit"))
            if kit not in sys.path:
                sys.path.insert(0, kit)
        elif name == "claims_check":
            kbpaths.use("text")
        _MOD[name] = importlib.import_module(name)
    return _MOD[name]


def yaml_mod():
    import yaml
    return yaml


def get(d, *path, default=None):
    for k in path:
        if isinstance(d, list) and isinstance(k, int) and -len(d) <= k < len(d):
            d = d[k]
            continue
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def listify(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def listed(items, n=6, sep=", "):
    """Список для сообщения: первые n и хвост «и ещё N» — один вид у всех находок."""
    items = [str(x) for x in items]
    return sep.join(items[:n]) + (f" и ещё {len(items) - n}" if len(items) > n else "")


def rules_catalog():
    """Правила реестра: [(id, заголовок, тяжесть)] по заголовкам «### R-… «…» · тяжесть»."""
    p = kbpaths.repo(*RULES_MD)
    out = []
    if not p.is_file():
        return out
    for m in re.finditer(r"^### (R-[A-Z]+-\d{3}) «(.+)» · (.+)$", p.read_text(encoding="utf-8"), re.M):
        out.append((m.group(1), m.group(2), m.group(3).strip()))
    return out


# ------------------------------------------------------------------ вызов утилит баз

@dataclass
class Run:
    rc: int | None
    out: str = ""
    err: str = ""
    data: object = None


class Tools:
    """Запуск утилит скилла Python окружения; итог каждой — в сводку (запускалась, код, сбой)."""

    def __init__(self, tmp):
        self.tmp = Path(tmp)
        self.used = {}
        self.n = 0
        self.py = kbpaths.python() if Path(kbpaths.python()).exists() else sys.executable

    def run(self, name, args, json_out=False, timeout=240):
        self.n += 1
        out_file = self.tmp / f"{self.n:03d}.json" if json_out else None
        argv = [self.py, str(kbpaths.scripts(None, *name.split("/")))] + [str(a) for a in args]
        if out_file is not None:
            argv += ["--json", str(out_file)]
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, cwd=str(self.tmp))
        except (OSError, subprocess.TimeoutExpired) as e:
            self.note(name, f"не запустилась: {e}")
            return Run(None, err=str(e))
        data = None
        if out_file is not None and out_file.is_file():
            try:
                data = json.loads(out_file.read_text(encoding="utf-8"))
            except ValueError:
                data = None
        self.note(name, f"код {r.returncode}")
        return Run(r.returncode, r.stdout, r.stderr, data)

    def note(self, name, what):
        self.used.setdefault(name, []).append(what)


def last_line(text):
    lines = [x for x in str(text or "").splitlines() if x.strip()]
    return lines[-1][:200] if lines else ""


# ------------------------------------------------------------------ аудит

class Audit:
    """Структурный прогон одного проекта: rep — находки, tools — вызовы, notes — заметки сводки."""

    def __init__(self, slug, repo=None, surface=None, today=None, tmp=None, run_tools=True):
        self.slug = slug
        self.root = docpaths.root(repo)
        self.repo = self.root
        self.project = docpaths.project(slug, repo=self.root)
        self.surfaces = docpaths.surfaces(slug, self.root)
        self.reg = {s.slug: s for s in self.surfaces}
        self.one = surface
        self.today = today or dt.date.today()
        self.rep = F.Report()
        self.notes = []
        self.docs = {}
        self.env = env_ok() and run_tools
        self._tmp = tmp
        self.tools = None
        self._facts = None
        self._stage = {}
        self._review = {}
        self._layers = {}
        self.fingerprinted = set()      # манифесты ассетов, отпечатки принятых строк которых сверил plan_to_assets

    # ---------- пути и чтение
    def rel(self, p):
        return docpaths.rel(p, self.root)

    def prel(self, p):
        try:
            return Path(p).resolve().relative_to(self.project.resolve()).as_posix()
        except ValueError:
            return self.rel(p)

    def dprod(self, *parts):
        return docpaths.design(self.slug, *parts, repo=self.root)

    def dsurf(self, s, *parts):
        return docpaths.design(self.slug, *parts, surface=s, repo=self.root)

    def site(self, s, *parts):
        return docpaths.site(self.slug, s, *parts, repo=self.root)

    def load(self, path):
        """Данные YAML или JSON (кэш); нет файла — None; не разбирается — None и строка в self.docs[path] = ошибка."""
        p = Path(path)
        key = str(p)
        if key not in self.docs:
            if not p.is_file():
                self.docs[key] = (None, None)
            else:
                try:
                    text = p.read_text(encoding="utf-8")
                    data = json.loads(text) if p.suffix == ".json" else yaml_mod().safe_load(text)
                    self.docs[key] = (data, None)
                except Exception as e:                      # noqa: BLE001 — yaml.YAMLError, JSONDecodeError
                    self.docs[key] = (None, str(e).splitlines()[0][:160])
        return self.docs[key][0]

    def status(self, path):
        return docpaths.status(path) if Path(path).is_file() else None

    def closed(self, kind, path):
        return self.status(path) in CLOSED.get(kind, ())

    def add(self, rule, severity, surface, kind, ref, path, message, fix=""):
        self.rep.add(rule, severity, surface=surface, kind=kind, ref=str(ref), path=self.rel(path) if isinstance(
            path, Path) else str(path), message=message, fix=fix)

    def dd(self, s=None, what=""):
        """Шаг исправления: этап или запись /design-deep-dive."""
        return f"/design-deep-dive {self.slug}" + (f" {s}" if s else "") + (f" — {what}" if what else "")

    # ---------- объём
    @property
    def scope(self):
        """Поверхности прогона: одна по аргументу или реестровые со слоем страницы или дизайна и маршрута дизайна."""
        if self.one:
            return [self.reg[self.one]]
        out = []
        for s in self.surfaces:
            has = docpaths.layer(self.slug, "site", s.slug, self.root).is_dir() or \
                self.dsurf(s.slug).is_dir()
            if has or s.page or s.app:
                out.append(s)
        return out

    @property
    def has_app(self):
        return any(s.app for s in self.surfaces)

    def plans(self, s):
        """{page_id: (путь, данные)} планов поверхности."""
        d = self.site(s, "plans")
        out = {}
        for p in sorted(d.glob("*.yaml")) if d.is_dir() else []:
            data = self.load(p)
            pid = str(get(data, "page", "id", default=p.stem) or p.stem) if isinstance(data, dict) else p.stem
            out[pid] = (p, data if isinstance(data, dict) else {})
        return out

    def decks(self, s):
        """[(путь, данные copy_deck, язык)] copy deck поверхности."""
        d = self.site(s, "copy")
        out = []
        for p in sorted(d.glob("*.yaml")) if d.is_dir() else []:
            data = self.load(p)
            m = re.match(r"^(.+?)(?:\.([a-z]{2,3}))?\.yaml$", p.name)
            out.append((p, get(data, "copy_deck") if isinstance(data, dict) else None, m.group(2) if m else None))
        return out

    def brief(self, s):
        d = self.load(self.site(s, "brief"))
        return d if isinstance(d, dict) else {}

    def input_stage(self, s):
        if s not in self._stage:
            self._stage[s] = mod("ds_coverage").input_stage(self.slug, s, self.root)
        return self._stage[s]

    def input_units(self, s):
        """Партия действующего входа холста — поле units передней части INPUT.md; входа или поля нет — []."""
        p = self.dsurf(s, "input") / "INPUT.md"
        if not p.is_file():
            return []
        try:
            fm = mod("canvas_input").read_manifest(p)[0]
        except Exception:                                   # noqa: BLE001 — манифест входа сверяет его проверка
            return []
        return [str(u) for u in listify(get(fm, "units"))]

    def page_has_input(self, s, pid):
        """Страница передана в дизайн — (причина, гейт 2) или None. Гейт 2 (чистовой макет — только на утверждённых
        текстах) — у страницы строка «Приёмка» в REVIEW.md или она в партии действующего входа холста (units INPUT.md
        или папка pages/<id>/) этапа mockup или motion; партия входа направлений или подачи — передача до гейта."""
        if pid in self.review(s)[1]:
            return "строка «Приёмка» в REVIEW.md", True
        if (self.dsurf(s, "input") / "pages" / pid).is_dir() or pid in self.input_units(s):
            st = self.input_stage(s)
            return (f"в партии входа холста этапа {st}" if st else "в партии входа холста без этапа в INPUT.md"), \
                st in TEXT_GATE_STAGES
        return None

    def review(self, s):
        """(паспорт REVIEW.md, строки «Приёмка» {единица: {...}}, строки «Пункты ACCEPTANCE»)."""
        if s not in self._review:
            p = self.dsurf(s, "review") / "REVIEW.md"
            fm, rows, items = {}, {}, []
            if p.is_file():
                L = mod("layer")
                md = L.Md(p)
                fm = md.fm or {}
                t = md.table(("вердикт",))
                for r in t.rows if t else []:
                    u = L.cell(r.get("страница или экран"))
                    if not L.is_empty(u):
                        rows[u] = {k: L.cell(r.get(k)) for k in t.columns}
                        rows[u]["artboards"] = [a.strip().strip("`") for a in
                                                re.split(r"[,;]", str(r.get("артборды") or "")) if a.strip()
                                                and not L.is_empty(a)]
                ti = md.table(("итог",))
                for r in ti.rows if ti else []:
                    items.append({k: L.cell(r.get(k)) for k in ti.columns})
            self._review[s] = (fm if isinstance(fm, dict) else {}, rows, items)
        return self._review[s]

    def verdicts(self, s):
        return {u: r.get("вердикт") for u, r in self.review(s)[1].items()}

    def item_unit(self, s, it, rows):
        """Единица строки «Пункты ACCEPTANCE» REVIEW.md: колонка «страница или экран»; пусто — у пункта ST-<экран>-…
        экран из id; иначе None — пункт всей поверхности."""
        if it.get("страница или экран"):
            return it["страница или экран"]
        i = str(it.get("id") or "")
        if not i.startswith("ST-") or i == "ST-DYN":
            return None
        d = docpaths.layer(self.slug, "screens", s, self.root) / "screens"
        known = set(rows) | ({p.name for p in d.iterdir() if p.is_dir()} if d.is_dir() else set())
        hit = [x for x in known if i.startswith(f"ST-{x}-")]
        return max(hit, key=len) if hit else None

    def facts(self):
        """(данные facts.yaml или {}, факты по id, id пробелов)."""
        if self._facts is None:
            data = self.load(docpaths.facts(self.slug, repo=self.root))
            data = data if isinstance(data, dict) else {}
            self._facts = (data, {f.get("id"): f for f in data.get("facts") or [] if isinstance(f, dict)},
                           {m.get("id"): m for m in data.get("missing") or [] if isinstance(m, dict)})
        return self._facts

    def state(self, *parts):
        return self.root.joinpath(*STATE, self.slug, *parts)

    # ---------- прогон
    def run(self, visual_list=False):
        with tempfile.TemporaryDirectory(prefix="ddd-audit-") as td:
            self.tools = Tools(self._tmp or td)
            for step in (self.r_surf, self.r_struct, self.r_ref, self.r_cov, self.r_proj, self.r_fresh, self.r_mat,
                         self.r_sem, self.r_debt):
                try:
                    step()
                except F.ToolError as e:
                    self.notes.append(f"{step.__name__}: {e}")
            self.visual = self.visual_list() if visual_list else None
        return self

    # ================================================================ R-SURF
    def r_surf(self):
        if not self.one:
            for layer in ("site", "design"):
                d = self.project / layer
                for x in sorted(p for p in d.iterdir() if p.is_dir()) if d.is_dir() else []:
                    if x.name.startswith("_") or x.name in self.reg:
                        continue
                    self.add("R-SURF-001", "error", None, "surface", x.name, x,
                             f"папка {layer}/{x.name}/ — поверхности `{x.name}` нет в реестре surface.md",
                             f"строка поверхности — /project-deep-dive {self.slug}; осиротевшая папка — "
                             f"{self.dd(what='удаление с каскадом')}")
            if (self.dprod("app-brief").is_file() or self.dprod("visual-dna").is_file()) and not self.has_app:
                for k in ("app-brief", "visual-dna"):
                    if self.dprod(k).is_file():
                        self.add("R-SURF-006", "error", None, k, k, self.dprod(k),
                                 f"design/{self.dprod(k).name} есть, а поверхности маршрута кабинета (web рода app, "
                                 "admin, desktop, embed) у продукта нет", f"/project-deep-dive {self.slug} — род")
            if self.has_app and not self.dprod("app-brief").is_file():
                self.add("R-SURF-007", "hint", None, "app-brief", "app-brief", self.dprod("app-brief"),
                         "у продукта есть поверхность кабинета, брифа на вид design/app-brief.yaml нет — этап "
                         "app-brief не начат или отложен", self.dd(what="app-brief"))
        for s in self.scope:
            sd = docpaths.layer(self.slug, "site", s.slug, self.root)
            ds = self.dsurf(s.slug)
            if sd.is_dir() and not s.page:
                kind = s.type + (f" рода {s.web_kind}" if s.web_kind else " без рода")
                self.add("R-SURF-002", "error", s.slug, "surface", s.slug, sd,
                         f"слой страницы site/{s.slug}/ у поверхности {kind}: он только у web рода landing или site",
                         f"род — /project-deep-dive {self.slug}; композиция кабинета — interface, экраны, FSD-карта")
            if s.page:
                self.site_type(s)
                for layer in ("interface", "screens", "fsd"):
                    p = self.project / layer / s.slug
                    if p.is_dir():
                        self.add("R-SURF-004", "error", s.slug, "surface", s.slug, p,
                                 f"у поверхности рода {s.web_kind} есть {layer}/{s.slug}/ — её место занимает слой "
                                 f"страницы site/{s.slug}/", f"нужное — в слой страницы: {self.dd(s.slug)}; папку "
                                 "соседнего слоя убирает его исполнитель")
                if not sd.is_dir():
                    self.add("R-SURF-007", "hint", s.slug, "surface", s.slug, sd,
                             f"у поверхности рода {s.web_kind} нет site/{s.slug}/ — этап brief не начат",
                             self.dd(s.slug, "brief"))
            if ds.is_dir() and not s.design:
                self.add("R-SURF-005", "error", s.slug, "surface", s.slug, ds,
                         f"папка design/{s.slug}/ у поверхности {s.type}: облик mobile, bot, api и other — токены ДС "
                         "продукта и голос", self.dd(what="удаление папки с каскадом"))
            if ds.is_dir() and not s.page:
                for name in PAGE_ONLY:
                    p = ds / name
                    if p.exists():
                        self.add("R-SURF-006", "error", s.slug, "art-direction" if name.startswith("art") else
                                 ("visual-dna" if name.startswith("visual") else "motion-spec"), s.slug, p,
                                 f"design/{s.slug}/{name} — только у поверхности рода landing или site",
                                 "у кабинета облик — ДС и продуктовый паспорт: " + self.dd())
            if ds.is_dir() and (ds / "app-brief.yaml").is_file():
                self.add("R-SURF-006", "error", s.slug, "app-brief", s.slug, ds / "app-brief.yaml",
                         "бриф на вид по поверхности не заводится: один бриф на продукт — design/app-brief.yaml, "
                         f"раздел surfaces.{s.slug}", self.dd(what="app-brief"))
            if (s.page or s.app) and not ds.is_dir():
                self.add("R-SURF-007", "hint", s.slug, "surface", s.slug, ds,
                         f"у поверхности маршрута дизайна нет design/{s.slug}/ — этапы дизайна не начаты",
                         self.dd(s.slug))

    def site_type(self, s):
        b = self.brief(s.slug)
        st = b.get("site_type")
        if not st:
            return
        voc = self.load(kbpaths.kb("site", "02-site-types", "vocabulary.yaml")) or {}
        row = next((v for v in get(voc, "namespaces", "site_type", "values", default=[]) or []
                    if isinstance(v, dict) and v.get("id") == st), None)
        path = self.site(s.slug, "brief")
        fix = f"тип — {self.dd(s.slug, 'brief')}; род — /project-deep-dive {self.slug}"
        if row is None:
            return                                           # id вне словаря ловит site_validate (R-STRUCT-002)
        if row.get("status") == "out-of-scope":
            self.add("R-SURF-003", "error", s.slug, "site-brief", "site-brief#/site_type", path,
                     f"site_type {st} — вне рамок скилла (out-of-scope)", fix)
        elif s.web_kind == "landing" and st != "landing-site":
            self.add("R-SURF-003", "error", s.slug, "site-brief", "site-brief#/site_type", path,
                     f"род landing, а site_type брифа — {st} (у лендинга — landing-site)", fix)
        elif s.web_kind == "site" and not row.get("multipage"):
            self.add("R-SURF-003", "error", s.slug, "site-brief", "site-brief#/site_type", path,
                     f"род site, а site_type брифа {st} — не многостраничный тип (multipage: false)", fix)

    # ================================================================ R-STRUCT
    def r_struct(self):
        for s in self.scope:
            if s.page:
                self.layout_site(s.slug)
            if s.design:
                self.layout_design(s.slug)
        if not self.env:
            self.notes.append("утилиты не запускались: окружение не установлено (Python окружения скилла без PyYAML "
                              "или jsonschema) — правила валидаторов проверяются чтением")
            return
        for s in self.scope:
            if s.page and docpaths.layer(self.slug, "site", s.slug, self.root).is_dir():
                self.site_validate(s.slug)
                self.vocab(s.slug)
                self.budgets(s.slug)
                self.copy_decks(s.slug)
                self.text_files(s.slug)
            if s.design and self.dsurf(s.slug).is_dir():
                self.design_files(s.slug)
                if s.page:
                    self.asset_plans(s.slug)
        self.product_files()

    # ---------- раскладка
    def layout_site(self, s):
        d = docpaths.layer(self.slug, "site", s, self.root)
        if not d.is_dir():
            return
        surf = self.reg[s]
        for p in sorted(d.iterdir()):
            name = p.name
            if p.is_dir():
                if name not in SITE_DIRS:
                    self.add("R-STRUCT-001", "warning", s, "surface", f"{s}#{name}", p,
                             f"папка site/{s}/{name}/ вне раскладки слоя (site-brief.yaml, meaning.yaml, "
                             "site-map.yaml, "
                             "hierarchy/, plans/, copy/)", self.dd(s))
                    continue
                for f in sorted(p.iterdir()):
                    if f.suffix == ".md":
                        self.add("R-STRUCT-001", "error", s, "surface", f"{s}#{name}/{f.name}", f,
                                 f"md-копия машинного файла {name}/{f.name}: источник правды — YAML по схеме базы, "
                                 "md-копий нет", self.dd(s))
                    elif f.suffix not in (".yaml", ".yml") or f.is_dir():
                        self.add("R-STRUCT-001", "warning", s, "surface", f"{s}#{name}/{f.name}", f,
                                 f"{name}/{f.name} вне раскладки слоя", self.dd(s))
                continue
            if name in SITE_FILES:
                if name == "site-map.yaml" and surf.web_kind == "landing":
                    self.add("R-STRUCT-001", "warning", s, "site-map", "site-map", p,
                             "карта сайта у рода landing: карта — только у рода site", self.dd(s))
                continue
            if name.endswith(".md") and Path(name).stem in {Path(x).stem for x in SITE_FILES}:
                self.add("R-STRUCT-001", "error", s, "surface", f"{s}#{name}", p,
                         f"md-копия машинного файла {name}: источник правды — YAML по схеме базы", self.dd(s))
            elif "brief" in name:
                self.add("R-STRUCT-001", "error", s, "site-brief", f"{s}#{name}", p,
                         f"второй бриф в папке поверхности: {name} (бриф — один site-brief.yaml)", self.dd(s, "brief"))
            else:
                self.add("R-STRUCT-001", "warning", s, "surface", f"{s}#{name}", p,
                         f"файл site/{s}/{name} вне раскладки слоя", self.dd(s))

    def layout_design(self, s):
        d = self.dsurf(s)
        if not d.is_dir():
            return
        for p in sorted(d.iterdir()):
            if p.name in DESIGN_SURF or p.name == "_phase-jump.md":
                continue
            if p.name == "app-brief.yaml":
                continue                                     # R-SURF-006
            sev = "error" if p.suffix == ".md" and Path(p.name).stem in ("art-direction", "visual-dna", "ready") \
                else "warning"
            what = "md-копия машинного файла" if sev == "error" else "вне раскладки слоя дизайна"
            self.add("R-STRUCT-001", sev, s, "surface", f"{s}#{p.name}", p, f"design/{s}/{p.name} — {what}",
                     self.dd(s))

    # ---------- site_validate, vocab_lint, page_gates
    # код site_validate → правило; None — правило считает сам аудит (ссылки, slug, страницы без плана): не дублировать
    SV = ((r"^SB-(B01|F01|M00)$", None), (r"^PL-F00$", None), (r"^PJ-0[23]$", None), (r"^PJ-00$|^PL-00$", None),
          (r"^SB-F0[34]$", None), (r"^SB-M02$", None),
          (r"^SB-B02$", "R-STRUCT-008"), (r"^SB-F02$", "R-STRUCT-003"), (r"^SB-M01$", "R-STRUCT-003"),
          (r"^SB-M03$", "R-REF-001"), (r"^SB-P0\d$", "R-COV-003"), (r"^PL-F0\d$", "R-COV-003"),
          (r"^SB-(R0\d|M05)$", "R-REF-005"), (r"^PL-(B0\d|A0\d|E0\d|T0\d|R01)$", "R-REF-005"),
          (r"^PL-(N01|K0\d)$", "R-REF-004"), (r"^PL-C0\d$", "R-STRUCT-004"), (r"^PL-D01$", "R-COV-004"),
          (r"^PJ-01$", "R-STRUCT-001"), (r"^SM-2[23]$", "R-COV-001"), (r"^SM-24$", "R-COV-003"))
    # (код, уровень) site_validate, который повторяет находку самого аудита: служебный шаблон без плана — та же
    # страница без плана, что называет R-COV-001 аудита; error того же кода (план не связан с шаблоном) остаётся
    SV_TWIN = (("SM-22", "warning"),)
    # код site_validate, который сводится в одну находку со списком планов: (правило, сообщение, (слово сообщения
    # валидатора, приписка о планах с этим словом), шаг исправления)
    SV_ONE = {"PL-U01": ("R-STRUCT-002", "планы approved без записи утверждения approval {by, date} — кто и когда "
                                         "утвердил",
                         ("x-approval", "запись лежит расширением x-approval, её место — approval"),
                         "page-plan — запись approval словом владельца"),
              "PL-F08": ("R-COV-003", "значения цели-контакта нет у machine фактов: литерал цели телефона, почты и "
                                      "мессенджера — копия machine факта",
                         ("target messenger:", "у факта цели messenger:<fact-id> нет machine с адресом ссылки"),
                         "meaning — machine фактов-контактов: подсказка claims_check.py lint-facts")}

    def sv_rule(self, code):
        for rx, rule in self.SV:
            if re.match(rx, code or ""):
                return rule
        return "R-STRUCT-002"

    # код site_validate → этап, где правится файл: бриф, карта сайта, план страницы; None — по файлу находки (форма
    # адресов PJ-04 правится в карте или в плане, у лендинга — в планах); значение контакта цели призыва шапки (SM-24)
    # — machine факта
    SV_STAGE = (("SB-", "brief"), ("PJ-04", None), ("PJ-", "brief"), ("SM-24", "meaning"), ("SM-", "site-map"),
                ("PL-", "page-plan"))

    def sv_stage(self, code, kind, page):
        stage = next((st for pre, st in self.SV_STAGE if str(code or "").startswith(pre)), None) or \
            {"site-brief": "brief", "site-map": "site-map", "page-plan": "page-plan"}.get(kind)
        return f"page-plan:{page}" if stage == "page-plan" and kind == "page-plan" else stage or ""

    @staticmethod
    def where_path(where, base):
        """Поле where валидатора → (путь, место): путь — от base (site_validate пишет пути от kb/site), место — после
        «:» или «#»."""
        m = re.match(r"^(.*?\.(?:ya?ml|json|md))(?:[:#](.*))?$", str(where or ""))
        raw, spot = (m.group(1), m.group(2) or "") if m else (str(where or ""), "")
        p = Path(raw)
        if not p.is_absolute():
            p = Path(base) / p
        return p.resolve(), spot

    def site_validate(self, s):
        d = docpaths.layer(self.slug, "site", s, self.root)
        r = self.tools.run("site/site_validate.py", [d, "--quiet", "--today", self.today.isoformat()], json_out=True)
        if r.rc not in (0, 1) or not isinstance(r.data, list):
            self.notes.append(f"site_validate.py {s}: не отработал ({last_line(r.err) or r.rc})")
            return
        one = {}
        for x in r.data:
            lvl = x.get("level")
            if lvl not in ("error", "warning"):
                continue
            rule = self.sv_rule(x.get("code"))
            if rule is None or x.get("code") == "SB-M03" and not self.proof_refs_ok(s):
                continue                                     # битую ссылку уже называет R-REF-001
            if (x.get("code"), lvl) in self.SV_TWIN:
                continue
            p, spot = self.where_path(x.get("where"), kbpaths.kb("site"))
            kind = "site-brief" if p.name == "site-brief.yaml" else "site-map" if p.name == "site-map.yaml" else \
                "page-plan" if p.parent.name == "plans" else "surface"
            if x.get("code") in self.SV_ONE and kind == "page-plan":
                one.setdefault((x.get("code"), lvl), []).append((p, str(x.get("msg") or "")))
                continue
            ref = (p.stem if kind == "page-plan" else kind if kind != "surface" else s) + (f"#{spot}" if spot else "")
            self.add(rule, lvl, s, kind, ref, p, f"{x.get('code')}: {x.get('msg')}",
                     self.dd(s, self.sv_stage(x.get("code"), kind, p.stem)))
        by_file = {pp.resolve(): pid for pid, (pp, _plan) in self.plans(s).items()}
        for (code, lvl), hits in one.items():
            rule, what, (word, also), step = self.SV_ONE[code]
            pids = sorted({by_file.get(f, f.stem) for f, _msg in hits})
            marked = sorted({by_file.get(f, f.stem) for f, msg in hits if word in msg})
            self.add(rule, lvl, s, "page-plan", f"{s}#{code}", d / "plans",
                     f"{code}: {what} — {len(pids)}: {', '.join(pids)}"
                     + (f"; {also} — {', '.join(marked)}" if marked else ""),
                     self.dd(s, step))

    def proof_refs_ok(self, s):
        """proof.facts_ref брифа и proof_ref смысла ведут в файлы (тогда их неравенство — отдельная находка SB-M03)."""
        b = self.site(s, "brief")
        bd = self.brief(s)
        refs = [get(bd, "proof", "facts_ref"), get(bd, "meaning", "proof_ref")]
        md = self.load(self.site(s, "meaning"))
        if isinstance(md, dict):
            refs.append(md.get("proof_ref"))
        for i, v in enumerate(refs):
            if v:
                base = self.site(s, "meaning") if i == 2 else b
                p, _why = self.ref_target(base, v)
                if p is None or not p.is_file():
                    return False
        return True

    def vocab(self, s):
        """Словарь site у файлов слоя страницы — брифа, карты, планов и copy deck — и у фактов продукта (места use):
        находка в фактах — уровня продукта, одна на прогон при любом числе поверхностей."""
        d = docpaths.layer(self.slug, "site", s, self.root)
        facts = docpaths.facts(self.slug, repo=self.root)
        files = [f for f in [self.site(s, "brief"), self.site(s, "site-map")] if f.is_file()]
        for sub in ("plans", "copy"):
            files += sorted((d / sub).glob("*.yaml")) if (d / sub).is_dir() else []
        files += [facts] if facts.is_file() else []
        if not files:
            return
        r = self.tools.run("site/vocab_lint.py", files)
        if r.rc not in (0, 1):
            self.notes.append(f"vocab_lint.py {s}: не отработал ({last_line(r.err) or r.rc})")
            return
        for line in r.out.splitlines():
            m = re.match(r"^(.+?):(\d+): (error|warning) (\S+) '([^']*)' — (.+)$", line.strip())
            if not m:
                continue
            p = Path(m.group(1))
            p = p if p.is_absolute() else (self.tools.tmp / p).resolve()
            msg = f"vocab_lint: {m.group(4)} «{m.group(5)}» — {m.group(6)}"
            if p == facts.resolve():
                self.add("R-STRUCT-002", m.group(3), None, "facts", f"facts#стр. {m.group(2)}", p, msg,
                         self.dd(what="meaning (факты)"))
                continue
            kind = "page-plan" if p.parent.name == "plans" else "copy-deck" if p.parent.name == "copy" else \
                "site-map" if p.name == "site-map.yaml" else "site-brief"
            self.add("R-STRUCT-002", m.group(3), s, kind, f"{p.stem}#стр. {m.group(2)}", p, msg,
                     self.dd(s, "copy" if kind == "copy-deck" else self.sv_stage("", kind, p.stem)))

    def budgets(self, s):
        seen = {}
        for pid, (p, plan) in self.plans(s).items():
            prof = get(plan, "page", "budget_profile")
            if not isinstance(prof, str) or not prof:
                continue
            if prof not in seen:
                r = self.tools.run("site/page_gates.py", ["--resolve", prof, "--json"])
                ok = r.rc == 0
                if ok:
                    try:
                        json.loads(r.out)
                    except ValueError:
                        ok = False
                why = re.sub(r"^page_gates\.py:\s*", "", last_line(r.err) or last_line(r.out))
                seen[prof] = (ok, why or f"код {r.rc}")
            ok, why = seen[prof]
            if not ok:
                self.add("R-STRUCT-002", "error", s, "page-plan", f"{pid}#/page/budget_profile", p,
                         f"профиль бюджета {prof} не резолвится (page_gates.py --resolve: {why})",
                         self.dd(s, f"page-plan:{pid}"))

    # ---------- тексты и факты
    COPY_SKIP = ("COPY-D-PLAN", "COPY-D-VOICE", "COPY-D-EXAMPLE", "COPY-F-EXAMPLE", "COPY-D-FACTS-STATUS",
                 "COPY-D-PLACEHOLDER", "COPY-D-RULES-MISSING", "COPY-D-RULES-FORMAT", "COPY-D-TOOL",
                 "COPY-D-STAGE", "COPY-D-FACTS-MISSING")
    COPY_MAT = ("COPY-D-STATUS", "COPY-D-CHOSEN", "COPY-D-SELECT", "COPY-D-HASH", "COPY-D-APPROVE")

    def copy_decks(self, s):
        facts = docpaths.facts(self.slug, repo=self.root)
        for p, deck, _lang in self.decks(s):
            if deck is None:
                continue
            args = ["check", p, "--quiet", "--today", self.today.isoformat()]
            if facts.is_file():
                args += ["--facts", facts]
            r = self.tools.run("text/copydeck.py", args, json_out=True)
            if not isinstance(r.data, dict):
                self.notes.append(f"copydeck.py check {p.name}: не отработал ({last_line(r.err) or r.rc})")
                continue
            if r.rc == COPYDECK_NO_CLAIMS:                   # причина — находка COPY-D-TOOL сверки, она в COPY_SKIP
                why = next((str(x.get("message") or "") for x in r.data.get("findings") or []
                            if x.get("rule") == "COPY-D-TOOL" and x.get("tool") == "claims"), "")
                self.notes.append(f"copydeck.py check {p.name}: сверка фактов не отработала — находки сверки неполны"
                                  + (f" ({why[:200]})" if why else ""))
            approved = {pg.get("page_id") for pg in deck.get("pages") or [] if isinstance(pg, dict)
                        and pg.get("status") == "approved"}
            for x in r.data.get("findings") or []:
                lvl, code, tool = x.get("level"), str(x.get("rule") or ""), x.get("tool")
                if lvl not in ("error", "warning") or code in self.COPY_SKIP:
                    if code in ("COPY-D-RULES-MISSING",) and x.get("message"):
                        self.note_once(f"copydeck.py: {x.get('message')}")
                    continue
                if tool == "lint" and lvl != "error":
                    continue                                 # стиль текста — этап copy-audit, не структура
                where = str(x.get("where") or "")
                page = where.split("/", 1)[0] if where and where != "—" else ""
                if code in self.COPY_MAT:
                    rule = "R-MAT-002" if page in approved else "R-STRUCT-003"
                    lvl = "error" if page in approved else lvl
                elif code in ("COPY-D-PROCESS-LOG", "COPY-D-REJECTED"):
                    rule, lvl = "R-SEM-002", "hint"
                elif code in ("COPY-D-FACT-REF", "COPY-D-MISSING-REF", "COPY-D-VOCAB", "COPY-D-BLOCK"):
                    rule = "R-REF-005"
                elif code in ("COPY-D-FACT-UNPUBLISHABLE", "COPY-D-FACT-EXPIRED", "COPY-D-FACT-REQUIRED"):
                    rule = "R-COV-003"
                else:
                    rule = "R-STRUCT-003"
                ref = (page or p.stem) + (f"#{where.split('/', 1)[1]}" if "/" in where else "")
                self.add(rule, lvl, s, "copy-deck", ref, p, f"{code}: {x.get('message')}", self.dd(s, "copy"))
            self.deck_bypasses(p, r.data)

    def deck_bypasses(self, p, data):
        """Обходы сверки и линтера copy deck — заметки сводки: решение человека с причиной, а не находка. Обходы
        claims_allow — поле allowed вывода copydeck.py check ({rule, where, reason, by}), обходы lint_allow — его
        заметки «lint_allow…: <правило> @ <место>: <причина>»."""
        claims = [f"{x.get('rule')} @ {x.get('where')} — {x.get('reason')} ({x.get('by')})"
                  for x in data.get("allowed") or [] if isinstance(x, dict)]
        lint = [m.group(1) for m in (re.match(r"^lint_allow[^:]*:\s*(.+)$", str(n)) for n in data.get("notes") or [])
                if m]
        for name, rows in (("claims_allow", claims), ("lint_allow", lint)):
            rows = list(dict.fromkeys(rows))
            if rows:
                self.note_once(f"обходы {name} copy deck {p.name} — {len(rows)}: " + listed(rows, 6, "; "))

    def note_once(self, text):
        if text not in self.notes:
            self.notes.append(text)

    def text_files(self, s):
        d = docpaths.layer(self.slug, "site", s, self.root)
        files = [f for f in [self.site(s, "meaning")] if f.is_file()]
        files += sorted((d / "hierarchy").glob("*.yaml")) if (d / "hierarchy").is_dir() else []
        for f in files:
            r = self.tools.run("text/validate_any.py", [f])
            if r.rc is None:
                continue
            kind = "meaning" if f.name == "meaning.yaml" else "hierarchy"
            for line in r.out.splitlines():
                m = re.match(r"^\s*(ОШИБКА|предупреждение):\s*(.+)$", line)
                if not m:
                    continue
                msg = m.group(2).strip()
                if kind == "hierarchy" and msg.startswith("meaning_ref не найден") or \
                        kind == "meaning" and msg.startswith("facts.yaml по proof_ref не найден"):
                    continue                                 # ссылку проверяет R-REF-001
                self.add("R-STRUCT-003", "error" if m.group(1) == "ОШИБКА" else "warning", s, kind,
                         f.stem if kind == "hierarchy" else kind, f, f"validate_any: {msg}",
                         self.dd(s, "meaning" if kind == "meaning" else "page-plan"))

    def product_files(self):
        facts = docpaths.facts(self.slug, repo=self.root)
        if facts.is_file():
            r = self.tools.run("text/claims_check.py", ["lint-facts", facts, "--quiet", "--today",
                                                         self.today.isoformat()], json_out=True)
            if isinstance(r.data, dict):
                for x in r.data.get("findings") or []:
                    code, lvl = str(x.get("rule") or ""), x.get("level")
                    if lvl not in ("error", "warning") or code == "COPY-F-EXAMPLE":
                        continue
                    if code in ("COPY-F-UNVERIFIED", "COPY-F-INFERRED", "COPY-F-EXPIRED", "COPY-F-STALE",
                                "COPY-F-LEGAL") or code == "COPY-F-PERMISSION" and "not-required" not in \
                            str(x.get("message")):
                        continue                             # публикуемость факта — там, где он стоит (R-COV-003)
                    self.add("R-STRUCT-003", lvl, None, "facts", str(x.get("unit") or "facts"), facts,
                             f"{code}: {x.get('message')}", self.dd(what="meaning (факты)"))
            else:
                self.notes.append(f"claims_check.py lint-facts: не отработал ({last_line(r.err) or r.rc})")
        for vp in [docpaths.voice(self.slug, repo=self.root), docpaths.voice(self.slug, True, self.root)]:
            if vp.is_file():
                self.voice_file(vp)
        voc = docpaths.voc(self.slug, repo=self.root)
        if voc.is_file():
            self.schema_file(voc, kbpaths.kb("text", "02-strategy-messaging", "voc.schema.yaml"), "voc")
        if self.dprod("tokens").is_file() or self.dprod("tokens-css").is_file():
            self.ds_build()
        elif any((self.dprod("ds-project") / f).is_file() for f in ("tokens.json", "README.md")):
            # артефакт ДС без источника DTCG: ds_build не зовётся — заметка сводки, чтобы счёт не читался как полный
            self.note_once("производные ДС не проверены: нет источника DTCG system.tokens.json — ds_build check "
                           "назовёт R-STRUCT-006")
        self.forms()
        for vd in [self.dprod("visual-dna")] + [self.dsurf(s.slug, "visual-dna") for s in self.scope if s.design]:
            if vd.is_file():
                self.passport(vd)

    def voice_file(self, vp):
        r = self.tools.run("text/validate_voice.py", [vp])
        if r.rc is None:
            return
        name = vp.name
        fref, _why = self.ref_target(vp, get(self.load(vp), "brand", "facts_ref"))
        lost = fref is None or not fref.is_file()
        current = None
        for line in r.out.splitlines():
            head = re.match(r"^(OK|FAIL)\s+(\S+?):", line)
            if head or not line.strip():
                current = head.group(2) if head else None
                continue
            m = re.match(r"^\s+(схема|смысл|предупреждение):\s*(.+)$", line)
            if not m or current != name:
                continue
            msg = m.group(2).strip()
            if msg.startswith("facts_ref не найден") or msg.startswith("meaning_ref не найден") or \
                    lost and "нет в facts.yaml" in msg:
                continue                                     # ссылку и её следствия называет R-REF-001
            self.add("R-STRUCT-003", "warning" if m.group(1) == "предупреждение" else "error", None,
                     "voice-product" if "product" in name else "voice", vp.stem, vp, f"validate_voice: {msg}",
                     self.dd(what="meaning (голос)"))

    def schema_file(self, path, schema_path, kind):
        import jsonschema
        data = self.load(path)
        sch = self.load(schema_path)
        if not isinstance(sch, dict):
            return
        for e in sorted(jsonschema.Draft202012Validator(sch).iter_errors(data), key=lambda e: list(e.path))[:10]:
            ptr = "/" + "/".join(map(str, e.absolute_path))
            self.add("R-STRUCT-003", "error", None, kind, f"{kind}#{ptr}", path, f"схема {schema_path.name}: "
                     f"{e.message[:160]}", self.dd(what="meaning"))

    def ds_build(self):
        B = mod("ds_build")
        try:
            items = B.check(B.Project.of(self.slug, self.root))
        except Exception as e:                              # noqa: BLE001 — сбой утилиты — заметка сводки
            self.notes.append(f"ds_build check: {e}")
            return
        self.tools.note("project/ds_build.py", "check")
        # «свежесть не сверялась» при битых токенах — строка сводки, а не находка: правило не проверялось
        skipped = [f for f in items if f.rule == "R-FRESH-001" and f.severity == "hint"]
        for f in skipped:
            self.note_once(f"ds_build: R-FRESH-001 не проверялось — {f.message}")
        self.rep.extend([f for f in items if f not in skipped])

    def passport(self, vd):
        r = self.tools.run("ai-media/vlm_to_dna.py", ["validate", vd])
        if r.rc in (0, None):
            return
        s = vd.parent.name if vd.parent.name != "design" else None
        msgs = [x.strip() for x in (r.out + "\n" + r.err).splitlines() if x.strip() and not x.startswith("OK")]
        self.add("R-STRUCT-004", "error", s, "visual-dna", "visual-dna", vd,
                 "vlm_to_dna validate: " + ("; ".join(msgs[-4:])[:300] or f"код {r.rc}"),
                 self.dd(s, "art-direction" if s else "passport-icons"))

    def design_files(self, s):
        ad = self.dsurf(s, "art-direction")
        if ad.is_file():
            r = self.tools.run("creative/ad_check.py", [ad, "--json"])
            try:
                res = json.loads(r.out).get("files") or {}
            except (ValueError, AttributeError):
                res = {}
                self.notes.append(f"ad_check.py {s}: не отработал ({last_line(r.err) or r.rc})")
            closed = self.closed("art-direction", ad)
            for _f, v in res.items():
                # снятые приметы (ключи --allow, lifted_markers) — правила ad_check, тяжесть — по R-REF-006: warning,
                # error у закрытой арт-дирекции; ошибки схемы и паспорта о тех же полях — форма файла (R-STRUCT-004)
                for part in ("schema", "visual_dna", "refs", "rules", "warnings"):
                    for msg in v.get(part) or []:
                        msg = str(msg)
                        if part in ("rules", "warnings") and re.search(r"--allow|lifted_markers", msg):
                            rule, sev = "R-REF-006", "error" if closed else "warning"
                        else:
                            rule, sev = "R-STRUCT-004", "warning" if part == "warnings" else "error"
                        self.add(rule, sev, s, "art-direction", "art-direction", ad, f"ad_check: {msg[:300]}",
                                 self.dd(s, "art-direction"))
        md = self.dsurf(s, "motion")
        for spec in sorted(md.glob("*.motion-spec.yaml")) if md.is_dir() else []:
            r = self.tools.run("creative/spec_check.py", ["spec", spec])
            for line in r.out.splitlines():
                m = re.match(r"^\s+(error|warning)\s+(\S+)\s+(.+)$", line)
                if m:
                    self.add("R-STRUCT-004", m.group(1), s, "motion-spec", spec.name.split(".")[0], spec,
                             f"spec_check {m.group(2)}: {m.group(3)[:260]}", self.dd(s, "motion"))

    def asset_plans(self, s):
        if not (self.dsurf(s, "asset-plans").is_dir() or self.plans(s)):
            return
        r = self.tools.run("site/plan_to_assets.py", ["check", self.slug, s, "--repo", self.root, "--json"])
        if r.rc not in (0, 1):
            self.notes.append(f"plan_to_assets.py check {s}: не отработал ({last_line(r.err) or r.rc})")
            return
        try:
            self.rep.extend(F.parse_lines(r.out))
        except ValueError as e:
            self.notes.append(f"plan_to_assets.py check {s}: вывод не по контракту находок ({e})")
            return
        self.fingerprinted |= {self.dsurf(s, "assets") / "manifest.yaml", self.dprod("assets") / "manifest.yaml"}

    # ---------- токены и формы
    def forms(self):
        tokens = self.load(self.dprod("tokens"))
        if isinstance(tokens, dict):
            if "breakpoint" not in tokens:
                self.add("R-STRUCT-007", "error", None, "design-system", "tokens#/breakpoint", self.dprod("tokens"),
                         "в system.tokens.json нет breakpoint.* — границы объявляются до экранов", self.dd(
                             what="design-system"))
            if self.has_app and "panel" not in (tokens.get("size") or {}):
                self.add("R-STRUCT-007", "error", None, "design-system", "tokens#/size/panel", self.dprod("tokens"),
                         "у продукта с кабинетом в system.tokens.json нет size.panel.* рядом с breakpoint.*: развал "
                         "каркаса считается по обоим", self.dd(what="design-system"))
        C = mod("ds_coverage")
        reg = None
        for kind in ("brand", "system", "app-brief"):
            p = self.dprod(kind)
            if not p.is_file():
                continue
            data = self.load(p)
            stage = {"brand": "brand", "system": "design-system", "app-brief": "app-brief"}[kind]
            if data is None:
                self.add("R-STRUCT-008", "error", None, "design-system" if kind == "system" else kind, kind, p,
                         f"{p.name} не разбирается: {self.docs[str(p)][1]}", self.dd(what=stage))
                continue
            try:
                reg = reg or C.registry()
                errs = C.form_errors(kind, data, reg)
            except Exception as e:                          # noqa: BLE001
                self.notes.append(f"форма {p.name}: {e}")
                continue
            for ptr, msg in errs[:12]:
                self.add("R-STRUCT-008", "error", None, "design-system" if kind == "system" else kind,
                         f"{kind}#{ptr}", p, f"форма {p.name}: {msg}", self.dd(what=stage))
        self.form_artifacts()
        for s in self.scope:
            rv = self.dsurf(s.slug, "review") / "REVIEW.md"
            if rv.is_file():
                self.form_review(s.slug, rv)
            rd = self.dsurf(s.slug, "ready")
            if rd.is_file():
                data = self.load(rd)
                for ptr, msg, sev in mod("ready").form_errors(data):
                    self.add("R-STRUCT-008", sev, s.slug, "ready", f"{s.slug}#{ptr}", rd, f"форма ready.yaml: {msg}",
                             f"ready build {self.slug} {s.slug}")

    def form_artifacts(self):
        p = self.dprod("artifacts")
        if not p.is_file():
            return
        L = mod("layer")
        md = L.Md(p)
        need = {"Артефакты": ("артефакт", "тип", "адрес"), "Загрузки": ("id", "файл", "слот", "артефакт"),
                "Условия холста": ("поверхность",)}
        for title, cols in need.items():
            t = md.table(cols)
            if t is None:
                self.add("R-STRUCT-008", "error", None, "artifacts", f"ARTIFACTS#{title}", p,
                         f"в ARTIFACTS.md нет таблицы «{title}» с колонками {', '.join(cols)}", self.dd())

    def form_review(self, s, p):
        L = mod("layer")
        md = L.Md(p)
        t = md.table(("вердикт",))
        if t is None:
            self.add("R-STRUCT-008", "error", s, "review", f"{s}#Приёмка", p,
                     "в REVIEW.md нет таблицы «Приёмка» (страница или экран, артборды, вердикт, одобрил, дата, "
                     "отпечаток)", self.dd(s, "acceptance"))
            return
        for c in ("страница или экран", "артборды", "вердикт", "одобрил", "дата", "отпечаток"):
            if c not in t.columns:
                self.add("R-STRUCT-008", "error", s, "review", f"{s}#Приёмка", p,
                         f"в таблице «Приёмка» REVIEW.md нет колонки «{c}»", self.dd(s, "acceptance"))
        for r in t.rows:
            v = L.cell(r.get("вердикт"))
            u = L.cell(r.get("страница или экран"))
            if not L.is_empty(v) and v not in ("accepted", "accepted_with_notes", "blocked"):
                self.add("R-STRUCT-008", "error", s, "review", f"{s}#Приёмка/{u}", p,
                         f"вердикт «{v}» у {u} вне перечня: accepted · accepted_with_notes · blocked",
                         self.dd(s, "acceptance"))

    # ================================================================ R-REF
    def r_ref(self):
        self.refs_product()
        for s in self.scope:
            if s.page:
                self.refs_site(s.slug)
                self.slugs_site(s.slug)
                self.junction(s.slug)
                self.pages_ids(s.slug)
            if s.design:
                self.uploads(s.slug)
        self.slugs_product()
        self.app_allow()
        for s in self.scope:
            if s.app:
                self.metaphors(s.slug)

    @staticmethod
    def ref_target(base, value):
        """Значение поля-ссылки → (путь, почему не путь): фрагмент «#…» отбрасывается."""
        v = str(value or "").split("#", 1)[0].strip()
        if not v:
            return None, "пусто"
        if re.search(r"\s", v) or re.match(r"^[a-z][a-z0-9+.-]*:", v):
            return None, f"«{str(value)[:80]}» — не путь к файлу"
        return (Path(base).parent / v), None

    def check_ref(self, rule_kind, s, ref_id, base, field_path, value, fix, ahead=None):
        """ahead — (причина, совет): файл ссылки создаёт следующий этап, и он ещё не начат — подсказка, не ошибка."""
        if value in (None, "", [], {}):
            return
        for v in listify(value):
            p, why = self.ref_target(base, v)
            if p is not None and p.exists():
                continue
            ref = f"{ref_id}#/{field_path.replace('.', '/')}"
            if ahead and not why:
                self.add("R-REF-001", "hint", s, rule_kind, ref, base,
                         f"{field_path} ведёт в файл, которого ещё нет: {v} — {ahead[0]}", ahead[1])
                continue
            msg = f"{field_path}: {why}" if why else f"{field_path} ведёт в несуществующий файл: {v}"
            self.add("R-REF-001", "error", s, rule_kind, ref, base, msg, fix)

    def refs_site(self, s):
        b = self.site(s, "brief")
        bd = self.brief(s)
        fix_b = self.dd(s, "brief")
        for fld in ("proof.facts_ref", "meaning_ref", "brand.ref", "meaning.proof_ref"):
            self.check_ref("site-brief", s, "site-brief", b, fld, get(bd, *fld.split(".")), fix_b)
        m = self.site(s, "meaning")
        md = self.load(m)
        if isinstance(md, dict):
            self.check_ref("meaning", s, "meaning", m, "proof_ref", md.get("proof_ref"), self.dd(s, "meaning"))
        hd = self.site(s, "hierarchy")
        for h in sorted(hd.glob("*.yaml")) if hd.is_dir() else []:
            data = self.load(h)
            if isinstance(data, dict):
                self.check_ref("hierarchy", s, h.stem, h, "meaning_ref", data.get("meaning_ref"),
                               self.dd(s, "page-plan"))
        started = {p.name[:-len(f".{lang}.yaml")] if lang else p.stem for p, _deck, lang in self.decks(s)}
        for pid, (p, plan) in self.plans(s).items():
            fix = self.dd(s, f"page-plan:{pid}")
            # план называет файлы следующих этапов заранее: пока этап не начат — текстов страницы нет ни на одном
            # языке, плана ассетов страницы нет, арт-дирекции поверхности нет, — ссылка ждёт файл
            ahead = {}
            if pid not in started:
                ahead["copy_deck"] = ("этап copy страницы не начат",
                                      self.dd(s, f"copy — каркас copy deck {pid}: copydeck.py skeleton"))
            if not (self.dsurf(s, "asset-plans") / f"{pid}.yaml").is_file():
                ahead["asset_plan"] = ("этап asset-plan страницы не начат", self.dd(
                    s, f"asset-plan — каркас плана ассетов {pid}: plan_to_assets.py build {self.slug} {s} --write"))
            if not self.dsurf(s, "art-direction").is_file():
                ahead["treatment"] = ("этап art-direction не начат", self.dd(s, "art-direction"))
            for fld in ("brief", "facts", "copy_deck", "asset_plan", "treatment"):
                self.check_ref("page-plan", s, pid, p, f"refs.{fld}", get(plan, "refs", fld), fix, ahead.get(fld))
            for fld in ("tokens_ref", "motion_spec_ref"):
                self.check_ref("page-plan", s, pid, p, f"page.treatment.{fld}", get(plan, "page", "treatment", fld),
                               fix)
            for i, sec in enumerate(plan.get("sections") or []):
                if isinstance(sec, dict):
                    self.check_ref("page-plan", s, pid, p, f"sections.{i}.treatment.motion_spec_ref",
                                   get(sec, "treatment", "motion_spec_ref"), fix)
        for p, deck, _lang in self.decks(s):
            if not isinstance(deck, dict):
                continue
            fix = self.dd(s, "copy")
            for fld in ("facts_ref", "voice_ref", "meaning_ref", "page_plan_ref"):
                self.check_ref("copy-deck", s, p.stem, p, f"copy_deck.{fld}", deck.get(fld), fix)
            for i, pg in enumerate(deck.get("pages") or []):
                if isinstance(pg, dict):
                    for fld in ("page_plan_ref", "hierarchy_ref"):
                        self.check_ref("copy-deck", s, pg.get("page_id") or p.stem, p, f"pages.{i}.{fld}",
                                       pg.get(fld), fix)
        vd = self.dsurf(s, "visual-dna")
        data = self.load(vd)
        if isinstance(data, dict):
            self.check_ref("visual-dna", s, "visual-dna", vd, "derived_from_ui.tokens",
                           get(data, "derived_from_ui", "tokens"), self.dd(s, "art-direction"))

    def refs_product(self):
        for product, fix in ((False, self.dd(what="meaning (голос)")), (True, self.dd(what="голос продукта"))):
            vp = docpaths.voice(self.slug, product, self.root)
            data = self.load(vp)
            if isinstance(data, dict):
                kind = "voice-product" if product else "voice"
                self.check_ref(kind, None, kind, vp, "scope.product_voice_ref", get(data, "scope",
                                                                                    "product_voice_ref"), fix)
                for fld in ("brand.facts_ref", "brand.meaning_ref"):
                    self.check_ref(kind, None, kind, vp, fld, get(data, *fld.split(".")), fix)
        br = self.dprod("brand")
        data = self.load(br)
        if isinstance(data, dict):
            self.check_ref("brand", None, "brand", br, "voice_ref", data.get("voice_ref"), self.dd(what="brand"))
        ab = self.dprod("app-brief")
        data = self.load(ab)
        if isinstance(data, dict):
            self.check_ref("app-brief", None, "app-brief", ab, "brand.ref", get(data, "brand", "ref"),
                           self.dd(what="app-brief"))

    # ---------- один slug
    def slug_eq(self, s, kind, ref, path, field_name, value, fix):
        if value is not None and str(value) != self.slug:
            self.add("R-REF-002", "error", s, kind, f"{ref}#/{field_name.replace('.', '/')}", path,
                     f"{field_name} — «{value}», а slug проекта — {self.slug}", fix)

    def slugs_site(self, s):
        b = self.site(s, "brief")
        bd = self.brief(s)
        self.slug_eq(s, "site-brief", "site-brief", b, "project.slug", get(bd, "project", "slug"), self.dd(s, "brief"))
        for key, kind in (("meaning", "meaning"), ("site-map", "site-map")):
            p = self.site(s, key)
            d = self.load(p)
            if isinstance(d, dict):
                self.slug_eq(s, kind, kind, p, "site", d.get("site"), self.dd(s, kind))
        for pid, (p, plan) in self.plans(s).items():
            self.slug_eq(s, "page-plan", pid, p, "site", plan.get("site"), self.dd(s, f"page-plan:{pid}"))
        for p, deck, _lang in self.decks(s):
            if isinstance(deck, dict):
                self.slug_eq(s, "copy-deck", p.stem, p, "copy_deck.site", deck.get("site"), self.dd(s, "copy"))
        juris = listify(get(bd, "constraints", "jurisdiction"))
        fdata, _f, _m = self.facts()
        if juris and fdata.get("jurisdiction") and fdata.get("jurisdiction") != juris[0]:
            self.add("R-REF-002", "error", None, "facts", "facts#/jurisdiction",
                     docpaths.facts(self.slug, repo=self.root),
                     f"jurisdiction фактов — «{fdata.get('jurisdiction')}», основная юрисдикция брифа {s} — {juris[0]}",
                     self.dd(what="meaning (факты)"))

    def slugs_product(self):
        fdata, _f, _m = self.facts()
        if fdata:
            self.slug_eq(None, "facts", "facts", docpaths.facts(self.slug, repo=self.root), "site", fdata.get("site"),
                         self.dd(what="meaning (факты)"))
        ab = self.load(self.dprod("app-brief"))
        if isinstance(ab, dict):
            self.slug_eq(None, "app-brief", "app-brief", self.dprod("app-brief"), "project.slug",
                         get(ab, "project", "slug"), self.dd(what="app-brief"))

    # ---------- стык copy deck с планом
    @staticmethod
    def plan_text_slots(plan):
        """{(секция, слот): описание слота} текстовых слотов плана и {секция} плана."""
        slots, sections = {}, set()
        for sec in plan.get("sections") or []:
            if not isinstance(sec, dict) or not sec.get("id"):
                continue
            sections.add(sec["id"])
            for t in get(sec, "slots", "text", default=[]) or []:
                if isinstance(t, dict) and t.get("id"):
                    slots[(sec["id"], t["id"])] = t
        return slots, sections

    def junction(self, s):
        plans = self.plans(s)
        for p, deck, lang in self.decks(s):
            if not isinstance(deck, dict):
                continue
            stem = p.name[:-len(f".{lang}.yaml")] if lang else p.stem
            fix = self.dd(s, f"copy-deck:{stem} — стык copy deck с планом")
            if stem not in plans:
                continue                                     # copy deck без плана — R-COV-001
            pp, plan = plans[stem]
            slots, sections = self.plan_text_slots(plan)
            pages = [pg for pg in deck.get("pages") or [] if isinstance(pg, dict)]
            # у шаблона коллекции рядом со страницей шаблона — образцы записей: page_id свой, site_page_id — id плана
            template = bool(get(plan, "page", "template"))
            own = [pg for pg in pages if pg.get("page_id") == stem]
            samples = [pg for pg in pages if pg.get("page_id") != stem and pg.get("site_page_id") == stem]
            if len(own) != 1 or len(own) + (len(samples) if template else 0) != len(pages):
                ids = ", ".join(str(pg.get("page_id")) for pg in pages) or "—"
                why = " — образцы (site_page_id — id плана) есть только у шаблона коллекции (page.template: true)" \
                    if samples and not template else ""
                self.add("R-REF-003", "error", s, "copy-deck", stem, p,
                         f"один copy deck на план: в {p.name} страницы {ids}, а файл — страница {stem} (page.id плана)"
                         + why, fix)
            for pg in own + (samples if template else []):
                pid = pg.get("page_id")
                ref = pg.get("page_plan_ref")
                if ref:
                    t, _why = self.ref_target(p, ref)
                    if t is not None and t.exists() and t.resolve() != pp.resolve():
                        self.add("R-REF-003", "error", s, "copy-deck", f"{pid}#/page_plan_ref", p,
                                 f"page_plan_ref ведёт не в план страницы {stem}: {ref}", fix)
                for sec in pg.get("sections") or []:
                    if not isinstance(sec, dict):
                        continue
                    sid = sec.get("section_id")
                    ssid = sec.get("site_section_id")
                    if sid not in sections:
                        self.add("R-REF-003", "error", s, "copy-deck", f"{pid}#/{sid}", p,
                                 f"секции `{sid}` copy deck нет в плане {stem}", fix)
                        continue
                    if ssid and ssid != sid:
                        self.add("R-REF-003", "error", s, "copy-deck", f"{pid}#/{sid}", p,
                                 f"секция `{sid}`: site_section_id `{ssid}` — не id секции плана", fix)
                    for sl in sec.get("slots") or []:
                        if not isinstance(sl, dict):
                            continue
                        slid = sl.get("slot_id")
                        t = slots.get((sid, slid))
                        if t is None:
                            self.add("R-REF-003", "error", s, "copy-deck", f"{pid}#/{sid}/{slid}", p,
                                     f"слота `{sid}/{slid}` copy deck нет среди текстовых слотов плана {stem}", fix)
                            continue
                        if sl.get("slot_type") and t.get("slot") and sl["slot_type"] != t["slot"]:
                            self.add("R-REF-003", "error", s, "copy-deck", f"{pid}#/{sid}/{slid}", p,
                                     f"слот `{sid}/{slid}`: slot_type {sl['slot_type']}, а slot плана — {t['slot']}",
                                     fix)
                        if sl.get("site_slot_id") and t.get("anatomy") and sl["site_slot_id"] != t["anatomy"]:
                            self.add("R-REF-003", "error", s, "copy-deck", f"{pid}#/{sid}/{slid}", p,
                                     f"слот `{sid}/{slid}`: site_slot_id {sl['site_slot_id']}, а anatomy плана — "
                                     f"{t['anatomy']}", fix)
                        if (sl.get("group") or t.get("group")) and sl.get("group") != t.get("group"):
                            self.add("R-REF-003", "error", s, "copy-deck", f"{pid}#/{sid}/{slid}", p,
                                     f"слот `{sid}/{slid}`: group {sl.get('group') or '—'}, а экземпляр группы слота "
                                     f"плана — {t.get('group') or '—'}", fix)

    # ---------- страницы и их id
    def site_pages(self, s):
        """id страниц, которые называет бриф (лендинг) или карта (род site)."""
        if self.reg[s].web_kind == "site":
            m = self.load(self.site(s, "site-map"))
            out = []
            for x in listify(get(m, "pages")):
                if isinstance(x, dict) and x.get("id"):
                    out.append(str(x["id"]))
            if isinstance(get(m, "pages"), dict):
                out = [str(k) for k in m["pages"]]
            for u in (get(m, "utility_pages") or {}).values() if isinstance(get(m, "utility_pages"), dict) else []:
                # служебная страница — id строкой или запись карты: у «спасибо» id страницы лежит в поле page
                ids = [(x.get("id") or x.get("page")) if isinstance(x, dict) else x for x in listify(u)]
                out += [str(i) for i in ids if i]
            return out
        return [str(x.get("id")) for x in get(self.brief(s), "pages", "list", default=[]) or []
                if isinstance(x, dict) and x.get("id")]

    def pages_ids(self, s):
        known = set(self.site_pages(s))
        for pid, (p, plan) in self.plans(s).items():
            fix = self.dd(s, f"page-plan:{pid}")
            if p.stem != pid:
                self.add("R-REF-004", "error", s, "page-plan", pid, p,
                         f"имя файла плана {p.name} — не id страницы (page.id {pid})", fix)
            if known and pid not in known and not get(plan, "page", "template"):
                src = "карты сайта" if self.reg[s].web_kind == "site" else "pages.list брифа"
                self.add("R-REF-004", "error", s, "page-plan", pid, p, f"page.id {pid} нет среди страниц {src}", fix)
        hd = self.site(s, "hierarchy")
        for h in sorted(hd.glob("*.yaml")) if hd.is_dir() else []:
            page = next((x for x in sorted(self.plans(s), key=len, reverse=True) if h.stem.startswith(x + "-")), None)
            if page is None and known and not any(h.stem.startswith(x + "-") for x in known):
                self.add("R-REF-004", "error", s, "hierarchy", h.stem, h,
                         f"иерархия {h.name} не называет страницу: имя — <page-id>-<осведомлённость>", self.dd(s))

    # ---------- снятые приметы брифа на вид, метафоры, загрузки
    def app_allow(self):
        ab = self.load(self.dprod("app-brief"))
        if not isinstance(ab, dict):
            return
        allow = ab.get("allow") if isinstance(ab.get("allow"), dict) else {}
        markers = listify(allow.get("markers"))
        if not markers:
            return
        keys = set(allow_keys().values())
        closed = self.closed("app-brief", self.dprod("app-brief"))
        sev = "error" if closed else "warning"
        for m in markers:
            if m not in keys:
                self.add("R-REF-006", sev, None, "app-brief", f"app-brief#/allow/markers/{m}", self.dprod("app-brief"),
                         f"ключ --allow «{m}» не из раздела checks реестра примет kb/common/tells.yaml",
                         self.dd(what="app-brief"))
        if not str(allow.get("why") or "").strip():
            self.add("R-REF-006", sev, None, "app-brief", "app-brief#/allow/why", self.dprod("app-brief"),
                     "ключи --allow брифа на вид без причины (allow.why)", self.dd(what="app-brief"))

    def layer_of(self, s):
        if s not in self._layers:
            L, T = mod("layer"), mod("tree")
            lay = L.Layer(self.slug, s, self.root)
            self._layers[s] = (lay, T.parse_layer(lay))
        return self._layers[s]

    def metaphors(self, s):
        T = mod("tree")
        lay, trees = self.layer_of(s)
        vd = self.dprod("visual-dna")
        data = self.load(vd)
        known = {str(m.get("id")) for m in get(data, "illustration", "metaphors", default=[]) or []
                 if isinstance(m, dict) and m.get("id")}
        closed = self.closed("visual-dna", vd)
        for slug, p in sorted(trees.screens.items()):
            if not p.record.stable:
                continue
            for n in T.screen_nodes(trees, slug):
                if n.ui_type != "EmptyState":
                    continue
                m = n.attrs.get("illustration")
                if not m or m in known:
                    continue
                why = "паспорта визуала нет" if data is None else ("метафоры нет в списке паспорта" if closed else
                                                                   "паспорт в работе, метафоры в списке нет")
                self.add("R-REF-007", "error" if closed and m not in known else "warning", s, "screen",
                         f"{slug}#{n.pointer}", p.record.path, f"ui:EmptyState illustration={m}: {why} "
                         "(design/visual-dna.json → illustration.metaphors)",
                         f"метафору экрана — /screen-deep-dive {self.slug} {s}; список паспорта — этапы passport-icons "
                         "и ds-components")

    def uploads(self, s):
        p = self.dprod("artifacts")
        if not p.is_file():
            return
        L = mod("layer")
        md = L.Md(p)
        t = md.table(("id", "файл", "слот", "артефакт"))
        ta = md.table(("артефакт", "тип", "адрес"))
        arts = {L.cell(r.get("артефакт")) for r in ta.rows} if ta else set()
        slots = self.plan_slots(s)
        folder = self.dsurf(s, "assets")
        man = self.manifest_rows(folder / "manifest.yaml")
        for r in t.rows if t else []:
            f = self.upload_file(r.get("файл"))
            a = L.cell(r.get("артефакт"))
            if L.is_empty(r.get("id")) and not f:
                continue
            if (not f.startswith(f"design/{s}/") and not f.startswith(f"{s}/") and "/" in f) or \
                    (not f and a != f"canvas:{s}"):
                continue                                     # загрузка другой поверхности
            problems = []
            name = Path(f).name
            if L.is_empty(r.get("id")):
                problems.append("нет id загрузки")
            up = self.upload_path(f, s)
            same = [x for x in man if f and Path(str(x.get("file") or "")).name == name]
            if not f:
                problems.append("нет файла")
            elif up is None and not (folder / name).is_file() and not same:
                problems.append(f"файла {name} нет в ассетах поверхности и строке манифеста")
            # страницу слота называет строка манифеста файла загрузки; у одноимённых файлов страниц — строка этого пути
            row = next((x for x in same if up is not None and self.asset_path(folder, x) == up),
                       same[0] if len(same) == 1 else None)
            page = str(row.get("page")) if row and row.get("page") not in (None, "") else None
            sl = L.cell(r.get("слот"))
            if slots and page and (page, sl) not in slots:
                problems.append(f"слот {sl} — не id слота плана ассетов страницы {page} (page строки манифеста)")
            elif slots and not page and sl not in {x for _pg, x in slots}:
                problems.append(f"слот {sl} — не id слота плана ассетов")
            if arts and a not in arts:
                problems.append(f"артефакт {a} не из таблицы «Артефакты»")
            if problems:
                self.add("R-REF-008", "warning", s, "artifacts", f"ARTIFACTS#Загрузки/{L.cell(r.get('id'))}", p,
                         "строка «Загрузки»: " + "; ".join(problems), self.dd(s, "холст — загрузки"))

    def manifest_rows(self, path):
        d = self.load(path)
        rows = d if isinstance(d, list) else get(d, "assets", default=[]) if isinstance(d, dict) else []
        return [r for r in rows or [] if isinstance(r, dict)]

    def asset_path(self, folder, row):
        """Файл строки манифеста ассетов: от папки манифеста, от корня данных или от design/ продукта — как у сборщика
        входа холста; файла нет — None."""
        v = str(row.get("file") or "").strip()
        if not v:
            return None
        return next((p.resolve() for p in (folder / v, self.root / v, self.dprod() / v) if p.is_file()), None)

    @staticmethod
    def upload_file(value):
        """Ячейка «файл» строки «Загрузки» → путь: первое значение в обратных кавычках (после него — пояснение),
        без кавычек — ячейка целиком; пусто — ''."""
        v = str(value or "").strip()
        m = re.search(r"`([^`]+)`", v)
        v = m.group(1).strip() if m else v
        return "" if mod("layer").is_empty(v) else v

    def upload_path(self, f, s=None):
        """Файл загрузки на диске: `design/…` — от папки проекта, `docs/…` — от корня данных, `<surface>/…` — от
        design/, имя без папки — в ассетах поверхности s; `$DDD_HOME/…`, `~/…` и абсолютный путь — файл вне
        репозитория (демо-кадр); файла нет — None."""
        if not f:
            return None
        if f.startswith("$DDD_HOME/"):
            cands = [kbpaths.home(f[len("$DDD_HOME/"):])]
        elif f.startswith("~") or Path(f).is_absolute():
            cands = [Path(f).expanduser()]
        else:
            cands = [self.project / f, self.root / f, self.dprod() / f]
            if s:
                cands.append(self.dsurf(s, "assets") / f)
        return next((p.resolve() for p in cands if p.is_file()), None)

    def plan_slots(self, s):
        """{(страница, id слота): (путь плана ассетов, слот, план)}. id слота повторяется между страницами (знак
        шапки, обложка, визуал первого экрана), поэтому ключ ассета — страница и слот; страница — page.id плана
        ассетов, без него — имя файла плана."""
        out = {}
        d = self.dsurf(s, "asset-plans")
        for ap in sorted(d.glob("*.yaml")) if d.is_dir() else []:
            data = self.load(ap)
            page = str(get(data, "page", "id") or ap.stem)
            for x in listify(get(data, "slots")):
                if isinstance(x, dict) and x.get("id"):
                    out[(page, str(x["id"]))] = (ap, x, data)
        return out

    @staticmethod
    def row_slots(slots, row, rows=()):
        """Слоты планов ассетов строки манифеста — как её читает вход холста: с полем page — слот плана этой страницы;
        без него — слот с таким id в планах страниц, у которых нет своих строк (rows — строки манифеста), а когда
        свои строки есть у всех — в плане любой страницы."""
        sid, page = str(row.get("slot") or ""), row.get("page")
        if page not in (None, ""):
            hit = slots.get((str(page), sid))
            return [hit] if hit else []
        own = {str(r.get("page")) for r in rows if str(r.get("slot") or "") == sid and r.get("page") not in (None, "")}
        same = [(pg, v) for (pg, x), v in slots.items() if x == sid]
        return [v for pg, v in same if pg not in own] or [v for _pg, v in same]

    # ================================================================ R-COV
    def r_cov(self):
        for s in self.scope:
            if s.page:
                self.cov_pages(s.slug)
                self.cov_texts(s.slug)
            if self.env and (s.page or s.app):
                self.cov_ds(s.slug)
            if s.app:
                self.cov_roles(s.slug)
            if s.page:
                self.cov_receivers(s.slug)
            if s.design:
                self.cov_assets(self.dsurf(s.slug, "assets"), s.slug)
        self.cov_assets(self.dprod("assets"), None)
        self.cov_voice()

    def design_files_of(self, s, pid):
        """Файлы слоя дизайна и текстов страницы: copy deck, план ассетов, спецификация движения, вход холста."""
        out = [self.site(s, "copy", f"{pid}.yaml"), self.dsurf(s, "asset-plans") / f"{pid}.yaml",
               self.dsurf(s, "motion") / f"{pid}.motion-spec.yaml", self.dsurf(s, "input") / "pages" / pid]
        return [p for p in out if p.exists()]

    def cov_pages(self, s):
        plans = self.plans(s)
        surf = self.reg[s]
        if surf.web_kind == "site" and plans and not self.site(s, "site-map").is_file():
            self.add("R-COV-001", "error", s, "site-map", "site-map", self.site(s, "site-map"),
                     "у рода site планы есть, а карты сайта site-map.yaml нет", self.dd(s, "site-map"))
        for pid in self.site_pages(s):
            if pid in plans:
                continue
            have = self.design_files_of(s, pid)
            if have:
                self.add("R-COV-001", "error", s, "page-plan", pid, self.site(s, "plans", f"{pid}.yaml"),
                         f"у страницы {pid} есть файлы ({', '.join(self.prel(x) for x in have)}), а плана нет",
                         self.dd(s, "page-plan"))
            else:
                self.add("R-COV-001", "hint", s, "page-plan", pid, self.site(s, "plans", f"{pid}.yaml"),
                         f"страница {pid} без плана — этап page-plan не начат", self.dd(s, "page-plan"))
        for p, deck, lang in self.decks(s):
            stem = p.name[:-len(f".{lang}.yaml")] if lang else p.stem
            if stem not in plans and stem not in self.site_pages(s):
                self.add("R-COV-001", "error", s, "copy-deck", stem, p,
                         f"copy deck {p.name} без плана страницы {stem}", self.dd(s, "page-plan"))

    @staticmethod
    def chosen(slot):
        return next((v for v in slot.get("variants") or []
                     if isinstance(v, dict) and v.get("id") == slot.get("chosen")),
                    None)

    def deck_of(self, s, pid):
        """(путь, страница copy deck) основного языка или (путь или None, None)."""
        p = self.site(s, "copy", f"{pid}.yaml")
        deck = get(self.load(p), "copy_deck")
        for pg in listify(get(deck, "pages")):
            if isinstance(pg, dict) and pg.get("page_id") == pid:
                return p, pg
        return (p if p.is_file() else None), None

    def cov_texts(self, s):
        for pid, (pp, plan) in self.plans(s).items():
            if docpaths.status(pp) != "approved":
                continue
            slots, _sections = self.plan_text_slots(plan)
            if not slots:
                continue
            dp, page = self.deck_of(s, pid)
            path = dp or self.site(s, "copy", f"{pid}.yaml")
            # у шаблона коллекции тексты слотов плана ведёт и каждый образец записи — страница того же copy deck с
            # site_page_id = id плана
            samples = [pg for pg in listify(get(self.load(path), "copy_deck", "pages"))
                       if isinstance(pg, dict) and pg.get("page_id") != pid and pg.get("site_page_id") == pid] \
                if get(plan, "page", "template") else []
            for unit, pg in [(pid, page)] + [(str(x.get("page_id")), x) for x in samples]:
                have = {}
                for sec in listify(get(pg, "sections")):
                    for sl in listify(get(sec, "slots")):
                        if isinstance(sl, dict):
                            var = self.chosen(sl)
                            have[(sec.get("section_id"), sl.get("slot_id"))] = bool(
                                var and str(var.get("text") or "").strip())
                miss = [k for k in slots if not have.get(k)]
                if not miss:
                    continue
                handed = self.page_has_input(s, pid)
                closed = bool(pg and pg.get("status") == "approved")
                if unit != pid:
                    # запись коллекции может не вести слот шаблона (услуг три, а не четыре): у образца — доклад
                    sev, why = "warning", "образец шаблона коллекции: запись либо ведёт слот, либо его не показывает"
                elif handed and handed[1]:
                    sev, why = "error", f"страница передана в дизайн: {handed[0]}"
                elif closed:
                    sev, why = "error", "copy deck закрыт"
                elif handed:
                    sev, why = "warning", f"{handed[0]}: тексты — до макета (гейт 2)"
                else:
                    sev, why = "warning", "до передачи в дизайн"
                whose = pid if unit == pid else f"{pid} у образца {unit}"
                fix = self.dd(s, f"copy — copy deck {pid}")
                if len(miss) > 10:
                    self.add("R-COV-002", sev, s, "copy-deck", unit, path,
                             f"текстовые слоты утверждённого плана {whose} без текста в copy deck ({why}) — "
                             f"{len(miss)}: " + listed((f"{a}/{b}" for a, b in miss), 8), fix)
                    continue
                for a, b in miss:
                    self.add("R-COV-002", sev, s, "copy-deck", f"{unit}#/{a}/{b}", path,
                             f"текстовый слот `{a}/{b}` утверждённого плана {whose} без текста в copy deck ({why})",
                             fix)

    def cov_ds(self, s):
        try:
            cov = mod("ds_coverage").coverage(self.slug, self.root, s)
        except Exception as e:                              # noqa: BLE001 — сбой утилиты — заметка сводки
            self.notes.append(f"ds_coverage {s}: {e}")
            return
        self.tools.note("project/ds_coverage.py", f"check {s}")
        # у сайта карта решений появляется на этапе дизайн-системы — после утверждённой арт-дирекции; пока её нет и
        # токенов ДС нет, «нет карты решений» — этап не начат, а не разрыв покрытия
        early = self.reg[s].page and not self.dprod("system").is_file() and not self.ds_stage(s)
        for f in cov.rep.items:
            if early and f.rule == "R-COV-005" and f.surface == s and f.ref == "system":
                self.add(f.rule, "hint", f.surface, f.kind, f.ref, f.path,
                         f.message + " — этап дизайн-системы не начат (арт-дирекция не утверждена, токенов ДС нет)",
                         self.dd(what="design-system — после утверждённой арт-дирекции"))
                continue
            self.rep.extend([f])

    def ds_stage(self, s):
        """Поверхность сайта дошла до этапа дизайн-системы: арт-дирекция утверждена или токены ДС заведены."""
        return self.closed("art-direction", self.dsurf(s, "art-direction")) or self.dprod("tokens").is_file() or \
            self.dprod("tokens-css").is_file()

    def cov_roles(self, s):
        sysd = self.load(self.dprod("system"))
        if not isinstance(sysd, dict):
            return
        styles = set((sysd.get("text_styles") or {}).keys()) if isinstance(sysd.get("text_styles"), dict) else set()
        lay, _trees = self.layer_of(s)
        roles = {"body"}
        if lay.texts.exists:
            roles |= {str(r.role) for r in lay.texts.rows.values() if r.role}
        miss = sorted(x for x in roles if x not in styles)
        if miss:
            self.add("R-COV-006", "warning", s, "design-system", "system#/text_styles", self.dprod("system"),
                     f"роли строк без стиля текста в text_styles карты решений ({s}): {', '.join(miss)}",
                     self.dd(what="design-system — text_styles"))

    def cov_receivers(self, s):
        """R-COV-008: получатели заявок брифа — analytics.crm и constraints.integrations (каналы конверсии — не
        получатели) — против строк integration.md с поверхностью: совпадение по любому слову получателя от трёх
        букв в slug, имени или описании строки."""
        b = self.brief(s)
        crm = [str(x) for x in listify(get(b, "analytics", "crm")) if str(x).strip()]
        integ = [str(x) for x in listify(get(b, "constraints", "integrations")) if str(x).strip()]
        if not crm and not integ:
            return
        rows = []
        md_path = docpaths.project(self.slug, "integration.md", repo=self.root)
        if md_path.is_file():
            L = mod("layer")
            t = L.Md(md_path).table(("slug", "surface"))
            for r in t.rows if t else []:
                if s in L.refs(r.get("surface")) or L.cell(r.get("surface")) == s:
                    rows.append(" ".join(str(r.get(c) or "") for c in ("slug", "name", "description")).lower())
        miss = [x for x in crm + integ if not any(w in r for w in re.findall(r"[^\W_]{3,}", x.lower()) for r in rows)]
        if miss:
            ref = "site-brief#/constraints/integrations" if set(miss) & set(integ) else "site-brief#/analytics/crm"
            self.add("R-COV-008", "warning", s, "site-brief", ref, self.site(s, "brief"),
                     f"получатели брифа без строки integration.md с поверхностью {s}: {', '.join(miss)}",
                     f"/project-deep-dive {self.slug} — строка интеграции с поверхностью {s}")

    def cov_assets(self, folder, s):
        if not folder.is_dir():
            return
        man_path = folder / "manifest.yaml"
        rows = self.manifest_rows(man_path)
        # строка манифеста — на файл: у слота их несколько (форматы, варианты), а файлы страниц с одним id слота
        # одноимённы в своих подпапках — строку находит путь файла, имя — когда строка называет файл без папки
        by_path, by_name = {}, {}
        for r in rows:
            if r.get("file"):
                rp = self.asset_path(folder, r)
                if rp is not None:
                    by_path[rp] = r
                else:
                    by_name[Path(str(r["file"])).name] = r
        slots = self.plan_slots(s) if s else {}
        for f in sorted(x for x in folder.rglob("*") if x.is_file()):
            relp = f.relative_to(folder).as_posix()
            if f.name == "manifest.yaml" or relp.startswith("plans/"):
                continue
            r = by_path.get(f.resolve()) or by_name.get(f.name)
            if r is None:
                self.add("R-COV-009", "warning", s, "asset", relp, f, f"файл ассета {relp} без строки манифеста "
                         f"{self.prel(man_path)}", self.dd(s, "assets"))
                continue
            # отпечаток принятой строки сверил plan_to_assets (R-STRUCT-005 error): одна несостыковка — одна находка
            own_sha = not (r.get("status") == "accepted" and man_path in self.fingerprinted)
            # роль ассета (несёт смысл или украшает) — о картинке слота: у строки файла шрифта (font) её нет
            need = [k for k, alts in (("slot", ("slot",)), ("role", () if r.get("font") else ("role",)),
                                      ("license", ("license",)), ("origin", ("origin", "provenance")),
                                      ("ai", ("ai", "ai_mark", "ai_label")),
                                      ("sha256", ("sha256",) if own_sha else ()), ("status", ("status",)))
                    if alts and not any(r.get(a) not in (None, "") for a in alts)]
            sha = str(r.get("sha256") or "").replace("sha256:", "")
            if own_sha and sha and sha != __import__("hashlib").sha256(f.read_bytes()).hexdigest():
                need.append("sha256 не совпадает с файлом")
            if r.get("page") not in (None, "") and r.get("slot") and slots and not self.row_slots(slots, r):
                need.append(f"page {r['page']}: слота {r['slot']} нет в плане ассетов этой страницы")
            if need:
                self.add("R-COV-009", "warning", s, "asset", relp, man_path,
                         f"строка манифеста ассета {relp}: нет или неверно — {', '.join(need)}", self.dd(s, "assets"))

    def cov_voice(self):
        vp = docpaths.voice(self.slug, repo=self.root)
        vpp = docpaths.voice(self.slug, True, self.root)
        pages = [s for s in self.surfaces if s.page]
        ui = [s for s in self.surfaces if s.app or s.type in ("mobile", "bot")]
        if not pages and not ui:
            return
        data = self.load(vp)
        fix = self.dd(what="meaning (голос)")

        def channels(d):
            return {str(x["surface"]): str(x.get("voice") or "") for x in listify(get(d, "scope", "surfaces"))
                    if isinstance(x, dict) and x.get("surface")}

        if not isinstance(data, dict) and not pages:
            # продукт без сайта и лендинга: профиль голоса один — голос продукта, профиля бренда и ссылки
            # scope.product_voice_ref у него нет
            names = ", ".join(s.slug for s in ui)
            pdata = self.load(vpp)
            fix_p = self.dd(what="meaning (голос продукта)")
            if not isinstance(pdata, dict):
                self.add("R-COV-007", "warning", None, "voice-product", "voice-product", vpp,
                         f"профиля голоса продукта voice.product.yaml нет: интерфейсу ({names}) не на что опереть "
                         "тексты", fix_p)
            elif channels(pdata).get("product-ui") != "product":
                self.add("R-COV-007", "warning", None, "voice-product", "voice-product#/scope/surfaces", vpp,
                         f"у интерфейса ({names}) нет канала product-ui с голосом product в voice.product.yaml", fix_p)
            return
        if not isinstance(data, dict):
            self.add("R-COV-007", "warning", None, "voice", "voice", vp,
                     "профиля голоса voice.yaml нет: поверхностям " + ", ".join(s.slug for s in pages + ui)
                     + " не на что опереть тексты", fix)
            return
        ch = channels(data)
        if pages and ch.get("marketing-site") != "brand":
            self.add("R-COV-007", "warning", None, "voice", "voice#/scope/surfaces", vp,
                     f"у поверхностей рода landing или site ({', '.join(s.slug for s in pages)}) нет канала "
                     "marketing-site с голосом brand", fix)
        if ui:
            names = ", ".join(s.slug for s in ui)
            if ch.get("product-ui") != "product":
                self.add("R-COV-007", "warning", None, "voice", "voice#/scope/surfaces", vp,
                         f"у интерфейса ({names}) нет канала product-ui с голосом product", fix)
            elif not vpp.is_file():
                self.add("R-COV-007", "warning", None, "voice", "voice#/scope/surfaces", vp,
                         f"канал product-ui есть, а профиля голоса продукта voice.product.yaml нет (интерфейс: "
                         f"{names})", self.dd(what="meaning (голос продукта)"))
            else:
                ref, _why = self.ref_target(vp, get(data, "scope", "product_voice_ref"))
                if ref is None or not ref.exists() or ref.resolve() != vpp.resolve():
                    self.add("R-COV-007", "warning", None, "voice", "voice#/scope/product_voice_ref", vp,
                             "scope.product_voice_ref не ведёт в voice.product.yaml", fix)
        legal = [s.slug for s in pages if any(str(x.get("page_type")) == "legal-page" for x in
                                               get(self.brief(s.slug), "pages", "list", default=[]) or []
                                               if isinstance(x, dict))]
        if legal and ch.get("legal") != "neutral-legal":
            self.add("R-COV-007", "hint", None, "voice", "voice#/scope/surfaces", vp,
                     f"у сайта с юридическими страницами ({', '.join(legal)}) нет канала legal с голосом neutral-legal",
                     fix)
        if "marketing-site" in ch and not pages:
            self.add("R-COV-007", "hint", None, "voice", "voice#/scope/surfaces", vp,
                     "канал marketing-site без поверхности рода landing или site", fix)
        if "product-ui" in ch and not ui:
            self.add("R-COV-007", "hint", None, "voice", "voice#/scope/surfaces", vp,
                     "канал product-ui без поверхности интерфейса", fix)

    # ================================================================ R-PROJ
    def r_proj(self):
        for s in self.scope:
            if s.page:
                self.proj_ad(s.slug)
        if self.has_app:
            self.proj_app()

    def proj_ad(self, s):
        adp = self.dsurf(s, "art-direction")
        ad = self.load(adp)
        if not isinstance(ad, dict):
            return
        b = get(self.brief(s), "ambition")
        amb = ad.get("ambition") if isinstance(ad.get("ambition"), dict) else {}
        # источник первичен: копия поля в арт-дирекции необязательна, сверяется только та, что записана
        fix = f"источник — бриф ({self.dd(s, 'brief')}); копию в арт-дирекции обновляет этап — " \
              f"{self.dd(s, 'art-direction')}"
        if isinstance(b, dict):
            diff = []
            if b.get("level") and amb.get("level") and amb.get("level") != b.get("level"):
                diff.append(f"level {amb.get('level')} ≠ {b.get('level')}")
            if b.get("motion_cap") and amb.get("motion_cap") and amb.get("motion_cap") != b.get("motion_cap"):
                diff.append(f"motion_cap {amb.get('motion_cap')} ≠ {b.get('motion_cap')}")
            ad_roles = {str(x.get("role")): x.get("level") for x in listify(amb.get("by_section_role"))
                        if isinstance(x, dict)}
            for x in listify(b.get("by_section_role")):
                if isinstance(x, dict) and str(x.get("role")) in ad_roles and \
                        ad_roles[str(x.get("role"))] != x.get("level"):
                    diff.append(f"секции {x.get('role')}: {ad_roles.get(str(x.get('role')))} ≠ {x.get('level')}")
            b_roles = {str(x.get("role")) for x in listify(b.get("by_section_role")) if isinstance(x, dict)}
            for role, lv in ad_roles.items():
                if role not in b_roles and lv != b.get("level"):
                    diff.append(f"секции {role}: {lv} — уровня нет в брифе")
            if diff:
                self.add("R-PROJ-002", "warning", s, "art-direction", "art-direction#/ambition", adp,
                         "копия уровня в арт-дирекции отстала от брифа: " + "; ".join(diff), fix)
        main = self.main_page(s)
        if main is None:
            return
        pid, (pp, plan) = main
        prof = get(plan, "page", "budget_profile")
        for fld, val in (("budget.profile", get(ad, "budget", "profile")),
                         ("ambition.budget_profile", amb.get("budget_profile"))):
            if prof and val and val != prof:
                self.add("R-PROJ-003", "warning", s, "art-direction", f"art-direction#/{fld.replace('.', '/')}", adp,
                         f"копия {fld} арт-дирекции — {val} — отстала от профиля плана главной страницы {pid}: {prof}",
                         f"источник — план страницы ({self.dd(s, f'page-plan:{pid}')}); копию в арт-дирекции "
                         f"обновляет этап — {self.dd(s, 'art-direction')}")

    def main_page(self, s):
        plans = self.plans(s)
        if not plans:
            return None
        b = self.brief(s)
        order = []
        if self.reg[s].web_kind == "site":
            m = self.load(self.site(s, "site-map"))
            order = [x.get("id") if isinstance(x, dict) else x for x in listify(get(m, "build_order"))]
        order += [str(x.get("id")) for x in get(b, "pages", "list", default=[]) or [] if isinstance(x, dict)
                  and (not b.get("primary_page_type") or x.get("page_type") == b.get("primary_page_type"))]
        for x in order:
            if x in plans:
                return x, plans[x]
        return None

    def proj_app(self):
        abp = self.dprod("app-brief")
        ab = self.load(abp)
        if not isinstance(ab, dict):
            return
        core = ab.get("core") if isinstance(ab.get("core"), dict) else {}
        apps = sorted(s.slug for s in self.surfaces if s.app)
        diff = []
        pointer = core.get("pointer")
        if isinstance(pointer, dict) and set(pointer) != set(apps):
            diff.append(f"pointer — поверхности {', '.join(sorted(pointer)) or '—'}, в реестре кабинет — "
                        f"{', '.join(apps)}")
        surfs = ab.get("surfaces")
        if isinstance(surfs, dict) and surfs and not set(surfs) <= set(apps):
            diff.append(f"surfaces — {', '.join(sorted(set(surfs) - set(apps)))} нет среди поверхностей кабинета")
        L = mod("layer")
        prod = L.Product(self.slug, apps[0], self.root) if apps else None
        if prod is not None:
            real = {(u, p) for u, _s, r in prod.postures for p in [L.cell(r.get("posture"))]}
            for x in listify(core.get("postures")):
                if isinstance(x, dict) and real and (str(x.get("user")), str(x.get("posture"))) not in real:
                    diff.append(f"postures — {x.get('user')}: {x.get('posture')} нет в таблице «Постура» user.md")
            objs = prod.objects if prod.has_objects else {}
            for sr in listify(core.get("status_roles")):
                o = str(sr).split(".", 1)[0]
                if objs and o not in objs:
                    diff.append(f"status_roles — объекта {o} нет в object.md")
        cons = docpaths.project(self.slug, "constraint.md", repo=self.root)
        if listify(core.get("platform_constraints")) and cons.is_file():
            t = L.Md(cons).table(("slug",))
            known = {L.cell(r.get("slug")) for r in t.rows} if t else set()
            for c in listify(core.get("platform_constraints")):
                if known and str(c) not in known:
                    diff.append(f"platform_constraints — {c} нет в constraint.md")
        if diff:
            # источник первичен: копия в ядре брифа необязательна, сверяется только та, что записана
            self.add("R-PROJ-001", "warning", None, "app-brief", "app-brief#/core", abp,
                     "ядро брифа на вид отстало от источников: " + listed(diff, 6, "; "),
                     "копию обновляет этап app-brief: " + self.dd(what="app-brief") + "; источник — его исполнитель")

    # ================================================================ R-FRESH
    FROM_INPUT = ("R-FRESH-002", "R-FRESH-003", "R-FRESH-004", "R-MAT-012", "R-MAT-003", "R-MAT-011")

    def r_fresh(self):
        self._maps = None
        for s in self.scope:
            if not (s.page or s.app):
                continue
            if self.env and (self.dsurf(s.slug, "input") / "INPUT.md").is_file():
                self.fresh_input(s)
            if self.env and (self.dsurf(s.slug, "canvas-project").is_dir()
                             or self.dsurf(s.slug, "canvas-html").is_dir()):
                self.fresh_copies(s.slug)
            if self.dsurf(s.slug, "ready").is_file():
                try:
                    self.rep.extend(mod("ready").check_surface(self.slug, s, self.root, self.today))
                    self.tools.note("project/ready.py", f"check {s.slug}")
                except Exception as e:                      # noqa: BLE001
                    self.notes.append(f"ready check {s.slug}: {e}")
        self.fresh_uploads()

    def fresh_input(self, s):
        CI = mod("canvas_input")
        try:
            if self._maps is None:
                self._maps = CI.Maps()
                self._maps.check()
            items, _ctx = CI.check_surface(self.slug, s, self.root, None, self._maps, self.today.isoformat())
        except (Exception, SystemExit) as e:                # noqa: BLE001 — сбой сборщика — заметка сводки
            self.notes.append(f"canvas_input check {s.slug}: {e}")
            return
        self.tools.note("project/canvas_input.py", f"check {s.slug}")
        accepted = any(v in ACCEPTED for v in self.verdicts(s.slug).values())
        for f in items:
            if f.rule not in self.FROM_INPUT:
                continue
            sev = "error" if f.rule == "R-MAT-003" and accepted else f.severity
            self.add(f.rule, sev, f.surface, f.kind, f.ref, f.path, f.message, f.fix)

    def checks_permitted(self):
        """Постоянная просьба заказчика о проверках макета: строка «Проверки макета: разрешены» в ARTIFACTS.md."""
        p = self.dprod("artifacts")
        text = p.read_text(encoding="utf-8") if p.is_file() else ""
        return bool(re.search(r"^Проверки макета:\s*разрешен", text, re.M | re.I))

    def fresh_copies(self, s):
        """R-FRESH-005 статичных копий артбордов — только при постоянной просьбе о проверках макета: копии читают
        кадры и скрипты проверок, оригинал макета — холст в claude.ai. Без просьбы копий может не быть: утилита не
        зовётся, находок и заметок о копиях нет. Манифест кадров kit.json в git не хранится — его собирает прогон
        кадров, свежесть его здесь не сверяется."""
        if not self.checks_permitted():
            return
        for name, args in (("claude-design/dc_to_html.py", ["check", self.slug, s, "--repo", self.root, "--json"]),):
            r = self.tools.run(name, args)
            if r.rc not in (0, 1):
                self.notes.append(f"{name} check {s}: не отработал ({last_line(r.err) or r.rc})")
                continue
            try:
                items = F.parse_lines(r.out)
            except ValueError as e:
                self.notes.append(f"{name} check {s}: вывод не по контракту находок ({e})")
                continue
            for f in items:
                self.add(f.rule, f.severity, f.surface, f.kind, f.ref, f.path, f.message, f.fix)

    def fresh_uploads(self):
        """R-FRESH-007: файл загрузки холста заменён после загрузки — колонка sha256 «Загрузок» ARTIFACTS.md против
        файла: холст показывает загруженную версию, репозиторий — новую. Отпечаток — sha256 файла целиком или его
        начало от восьми знаков. Строки без отпечатка (или таблица без колонки) — одна подсказка со счётом: сверять
        нечем; файла строки нет на машине (демо-кадр вне git) — заметка сводки."""
        p = self.dprod("artifacts")
        if not p.is_file():
            return
        L = mod("layer")
        t = L.Md(p).table(("id", "файл", "слот", "артефакт"))
        if t is None:
            return
        scope = {x.slug for x in self.scope}
        empty, lost, total = [], [], 0
        for r in t.rows:
            f, uid = self.upload_file(r.get("файл")), L.cell(r.get("id")) or "—"
            art = L.cell(r.get("артефакт")) or ""
            s = art.split(":", 1)[1] if art.startswith("canvas:") else None
            if not f or (s is not None and s not in scope):
                continue
            total += 1
            sha = (L.cell(r.get("sha256")) or "").replace("sha256:", "").strip().lower()
            if not sha:
                empty.append(uid)
                continue
            ref, fix = f"ARTIFACTS#Загрузки/{uid}", self.dd(s, "холст — загрузки")
            if not re.fullmatch(r"[0-9a-f]{8,64}", sha):
                self.add("R-FRESH-007", "warning", s, "artifacts", ref, p, f"отпечаток загрузки {uid} не по форме: "
                         "sha256 файла — шестнадцатеричные знаки, от восьми", fix)
                continue
            path = self.upload_path(f, s)
            if path is None:
                lost.append(uid)
            elif not __import__("hashlib").sha256(path.read_bytes()).hexdigest().startswith(sha):
                self.add("R-FRESH-007", "warning", s, "artifacts", ref, p,
                         f"файл загрузки {uid} изменился после загрузки: sha256 строки «Загрузки» не равен файлу "
                         f"{self.prel(path)} — холст показывает загруженный кадр, а не файл репозитория",
                         "замена загрузки по протоколу холста: новая загрузка, её id — в исходники артбордов, новые id "
                         "и sha256 — в строку «Загрузок» — " + fix)
        if empty:
            col = "" if "sha256" in t.columns else "в «Загрузках» нет колонки sha256: "
            self.add("R-FRESH-007", "hint", None, "artifacts", "ARTIFACTS#Загрузки", p,
                     f"{col}загрузки холста без отпечатка файла — {len(empty)} из {total} ({listed(empty, 4)}): замена "
                     "файла после загрузки не ловится", "колонка sha256 после «файл» — sha256 файла на момент "
                     "загрузки: " + self.dd(what="холст — загрузки"))
        if lost:
            self.note_once(f"R-FRESH-007 не проверялось у загрузок, файла которых нет на этой машине, — {len(lost)}: "
                           + listed(lost, 4))

    # ================================================================ R-MAT
    def r_mat(self):
        for s in self.scope:
            if s.page:
                self.mat_site(s.slug)
                self.mat_chrome(s.slug)
            if s.design:
                self.mat_review(s.slug)
                self.mat_iterations(s.slug)
                self.mat_boards(s.slug)
                self.mat_assets(s.slug)
            if s.app:
                self.mat_second_input(s)
        self.mat_ds()
        self.mat_artifacts()
        self.mat_blockers()
        self.mat_first_input()

    def mat_site(self, s):
        bst = self.status(self.site(s, "brief"))
        mst = self.status(self.site(s, "meaning"))
        fst = self.status(docpaths.facts(self.slug, repo=self.root))
        plans = self.plans(s)
        for pid, (pp, plan) in plans.items():
            if docpaths.status(pp) == "approved" and (bst != "approved" or (mst and mst != "approved")):
                self.add("R-MAT-001", "warning", s, "page-plan", pid, pp,
                         f"план {pid} approved при брифе {bst or 'нет'} и смысле {mst or 'нет'}",
                         self.dd(s, "brief"))
            tst = get(plan, "page", "treatment", "status")
            if tst == "approved" and self.verdicts(s).get(pid) not in ACCEPTED:
                self.add("R-MAT-001", "warning", s, "page-plan", f"{pid}#/page/treatment", pp,
                         f"подача страницы {pid} approved без принятого статичного макета", self.dd(s, "motion"))
        for p, deck, _lang in self.decks(s):
            for pg in listify(get(deck, "pages")):
                if not isinstance(pg, dict) or pg.get("status") != "approved":
                    continue
                pid = pg.get("page_id")
                # образец шаблона коллекции стоит на плане шаблона: его называет site_page_id
                plan_id = next((x for x in (pg.get("site_page_id"), pid) if x in plans), None)
                pst = docpaths.status(plans[plan_id][0]) if plan_id else None
                open_ = ([f"план {pst or 'нет'}"] if pst != "approved" else []) + \
                    ([f"факты {fst or 'нет'} (confirmed ставит заказчик)"] if fst != "confirmed" else [])
                if open_:
                    self.add("R-MAT-001", "warning", s, "copy-deck", pid, p,
                             f"copy deck {pid} approved на открытом: " + ", ".join(open_), self.dd(s, "copy-audit"))
        adp = self.dsurf(s, "art-direction")
        ad = self.load(adp)
        if isinstance(ad, dict) and ad.get("status") == "approved":
            open_plans = [pid for pid, (pp, _p) in plans.items() if docpaths.status(pp) != "approved"]
            if not get(ad, "choice", "chosen") or open_plans:
                self.add("R-MAT-001", "warning", s, "art-direction", "art-direction", adp,
                         "арт-дирекция approved " + ("без выбранного направления" if not get(ad, "choice", "chosen")
                                                     else f"при планах не approved: {', '.join(open_plans)}"),
                         self.dd(s, "art-direction"))
        for ap in sorted(self.dsurf(s, "asset-plans").glob("*.yaml")) if self.dsurf(s, "asset-plans").is_dir() else []:
            if docpaths.status(ap) != "approved":
                continue
            pid = ap.stem
            pst = docpaths.status(plans[pid][0]) if pid in plans else None
            ast = self.status(adp)
            if pst != "approved" or ast != "approved":
                self.add("R-MAT-001", "warning", s, "asset-plan", pid, ap,
                         f"план ассетов {pid} approved при плане страницы {pst or 'нет'} и арт-дирекции {ast or 'нет'}",
                         self.dd(s, "asset-plan"))
        if self.closed("site-brief", self.site(s, "brief")):
            wd = [q.get("id") for q in listify(get(self.brief(s), "questions")) if isinstance(q, dict)
                  and q.get("status") == "withdrawn"]
            if wd:
                self.add("R-SEM-002", "hint", s, "site-brief", "site-brief#/questions", self.site(s, "brief"),
                         f"журнал процесса в утверждённом брифе: вопросы withdrawn ({', '.join(map(str, wd))})",
                         self.dd(s, "brief"))

    def mat_ds(self):
        sp = self.dprod("system")
        if self.status(sp) != "approved":
            return
        pages = [s.slug for s in self.surfaces if s.page]
        ok_site = any(self.status(self.dsurf(s, "art-direction")) == "approved" for s in pages)
        ab = self.dprod("app-brief")
        ok_app = self.has_app and self.status(ab) == "approved" and bool(get(self.load(ab), "choice", "chosen"))
        if (pages or self.has_app) and not (ok_site or ok_app):
            why = []
            if pages:
                why.append("арт-дирекция сайта не approved")
            if self.has_app:
                why.append(f"бриф на вид {self.status(ab) or 'нет'}" + ("" if get(self.load(ab), "choice", "chosen")
                                                                        else ", карточка стиля не выбрана"))
            self.add("R-MAT-001", "warning", None, "design-system", "system", sp,
                     "ДС approved на открытом: " + "; ".join(why), self.dd(what="design-system"))
        for s in self.scope:
            if s.design and any(v in ACCEPTED for v in self.verdicts(s.slug).values()) and \
                    self.status(sp) != "approved":
                self.add("R-MAT-001", "warning", s.slug, "review", s.slug, self.dsurf(s.slug, "review") / "REVIEW.md",
                         "принятый макет при ДС не approved", self.dd(what="design-system"))

    def mat_review(self, s):
        fm, rows, items = self.review(s)
        rv = self.dsurf(s, "review") / "REVIEW.md"
        if not rows and not fm:
            return
        R = mod("ready")
        b = R.Build(self.slug, self.reg[s], self.root, self.today)
        acc = {}
        ap = self.dsurf(s, "input") / "ACCEPTANCE.md"
        if ap.is_file():
            arows, _h = mod("canvas_input").parse_acceptance(ap.read_text(encoding="utf-8"))
            acc = {r.get("id"): r.get("серьёзность") for r in arows}
        plans = self.plans(s) if self.reg[s].page else {}
        # исключение ворот — запись плана своей страницы: пункт S оно снимает только у неё
        exc = {pid: {str(e.get("id")) for e in listify(get(plan, "page", "x-gate-exception")) if isinstance(e, dict)}
               for pid, (_p, plan) in plans.items()}
        failed = [(it.get("id"), self.item_unit(s, it, rows)) for it in items
                  if (it.get("итог") or "").startswith("не пройдено")]
        for unit, row in rows.items():
            v = row.get("вердикт")
            if v not in ACCEPTED:
                continue
            # непройденный пункт с единицей держит только её, без единицы — все принятые единицы
            open_b = [i for i, u in failed if acc.get(i) == "B" and u in (None, unit)]
            open_s = [i for i, u in failed if acc.get(i) == "S" and i not in exc.get(unit, ()) and u in (None, unit)]
            fix = self.dd(s, "acceptance")
            if not row.get("одобрил") or row.get("одобрил") in ("—", "-") or not row.get("дата") or \
                    row.get("дата") in ("—", "-"):
                self.add("R-MAT-005", "error", s, "review", f"{s}#Приёмка/{unit}", rv,
                         f"{unit}: вердикт {v} без одобрения заказчика с ролью и датой", fix)
            if open_b:
                self.add("R-MAT-005", "error", s, "review", f"{s}#Приёмка/{unit}", rv,
                         f"{unit}: вердикт {v} при непройденных пунктах B: {', '.join(open_b)}", fix)
            if v == "accepted" and open_s:
                self.add("R-MAT-005", "error", s, "review", f"{s}#Приёмка/{unit}", rv,
                         f"{unit}: вердикт accepted при непройденных пунктах S: {', '.join(open_s)} "
                         "(accepted_with_notes — с записью каждого S)", fix)
            now = b.fingerprint(unit, row.get("artboards") or [])
            if now != row.get("отпечаток"):
                self.add("R-MAT-004", "warning", s, "review", f"{s}#Приёмка/{unit}", rv,
                         f"одобрение {unit} снято: отпечаток артбордов и источников единицы в REVIEW.md не совпал с "
                         "текущим" + ("" if now else " (артборда или единицы нет)")
                         + f" — текущий: ready show {self.slug} {s}", fix)
        inp = self.dsurf(s, "input") / "INPUT.md"
        if inp.is_file() and fm.get("stage"):
            ifm, _body, _src = mod("canvas_input").read_manifest(inp)
            errs = get(ifm, "check", "error", default=0) or 0
            if ifm and ifm.get("stage") == fm.get("stage") and errs:
                self.add("R-MAT-012", "error", s, "input", "INPUT.md", inp,
                         f"холст этапа {fm.get('stage')} опубликован на входе с ошибками проверки ({errs} error в "
                         "манифесте)", f"canvas_input build {self.slug} {s} --stage {fm.get('stage')}")

    def mat_iterations(self, s):
        """R-SEM-002: папка итерации в review/ — review/ держит последний результат; сверяется и без REVIEW.md."""
        d = self.dsurf(s, "review")
        for p in sorted(d.iterdir()) if d.is_dir() else []:
            if p.is_dir() and ITER_DIR.match(p.name):
                self.add("R-SEM-002", "warning", s, "review", f"{s}#{p.name}", p,
                         f"папка по итерациям в review/: {p.name} — review/ держит последний результат", self.dd(s))

    # ---------- общие секции страниц
    def chrome_slots(self, s, pid, plan):
        """Общие секции страницы — роли header и footer, кроме секций своей страницы (OWN_CHROME): {(роль, блок,
        вариант): {слот: текст выбранного варианта copy deck или None — у слота без текста и у слота не текста}}.
        Ключ слота — «<группа слотов>/<id>»; секции одного ключа складываются."""
        _dp, page = self.deck_of(s, pid)
        texts = {}
        for sec in listify(get(page, "sections")):
            for sl in listify(get(sec, "slots")) if isinstance(sec, dict) else []:
                if isinstance(sl, dict):
                    var = self.chosen(sl)
                    texts[(sec.get("section_id"), sl.get("slot_id"))] = str(var.get("text") or "").strip() \
                        if var else None
        out = {}
        for sec in listify(plan.get("sections")):
            if not isinstance(sec, dict) or sec.get("role") not in ("header", "footer") or \
                    sec.get("block") in OWN_CHROME:
                continue
            key = (str(sec.get("role")), str(sec.get("block") or "—"), str(sec.get("variant") or "—"))
            slots = out.setdefault(key, {})
            for group, items in (sec.get("slots") or {}).items() if isinstance(sec.get("slots"), dict) else []:
                for x in listify(items):
                    if isinstance(x, dict) and x.get("id"):
                        slots[f"{group}/{x['id']}"] = texts.get((sec.get("id"), x["id"])) if group == "text" else None
        return out

    def mat_chrome(self, s):
        """R-MAT-013: общие шапка и подвал живут копиями в плане и copy deck каждой страницы — у страниц с той же
        секцией (роль, блок, вариант) набор слотов и выбранные тексты равны. Образец — значение большинства страниц
        (при равенстве — страницы, что раньше по порядку: главная, затем по id); находка — на страницу и слот, с
        парой «страница — образец»; текст сверяется, когда он есть у обеих страниц."""
        plans = self.plans(s)
        main = self.main_page(s)
        order = sorted(plans, key=lambda x: (main is None or x != main[0], x))
        by_key = {}
        for pid in order:
            for key, slots in self.chrome_slots(s, pid, plans[pid][1]).items():
                by_key.setdefault(key, {})[pid] = slots
        for (role, block, variant), pages in by_key.items():
            if len(pages) < 2:
                continue
            what = f"секции {role} (блок {block}" + (f", вариант {variant}" if variant != "—" else "") + ")"
            for slot in sorted({x for slots in pages.values() for x in slots}):
                have = [pid for pid in pages if slot in pages[pid]]
                # набор слотов: образец — большинство (есть или нет)
                norm_has = len(have) * 2 >= len(pages)
                odd = [pid for pid in pages if (slot in pages[pid]) != norm_has]
                ref_page = next(pid for pid in pages if (slot in pages[pid]) == norm_has)
                for pid in odd:
                    self.add("R-MAT-013", "warning", s, "page-plan", f"{pid}#/{role}/{slot}", plans[pid][0],
                             f"слот {slot} {what}: у страницы {pid} его " + ("нет" if norm_has else "есть")
                             + f", у страницы {ref_page} — " + ("есть" if norm_has else "нет")
                             + ": общая секция расходится между страницами",
                             self.dd(s, f"page-plan:{pid} — общая секция по образцу страницы {ref_page}"))
                # тексты: образец — самый частый текст
                texts = {pid: pages[pid][slot] for pid in have if pages[pid][slot]}
                if len(set(texts.values())) < 2:
                    continue
                count = {}
                for pid, t in texts.items():
                    count[t] = count.get(t, 0) + 1
                norm = max(count, key=lambda t: (count[t], -list(texts.values()).index(t)))
                ref_page = next(pid for pid, t in texts.items() if t == norm)
                for pid, t in texts.items():
                    if t != norm:
                        dp, _pg = self.deck_of(s, pid)
                        self.add("R-MAT-013", "warning", s, "copy-deck", f"{pid}#/{role}/{slot}",
                                 dp or plans[pid][0],
                                 f"текст слота {slot} {what}: у страницы {pid} — «{t[:80]}», у страницы {ref_page} — "
                                 f"«{norm[:80]}»: общая секция расходится между страницами",
                                 self.dd(s, f"copy — copy deck {pid}: текст общей секции по образцу страницы "
                                            f"{ref_page}"))

    # ---------- загрузки принятых артбордов
    def path_key(self, f, s=None):
        """Путь файла загрузки или демо-кадра для сравнения: файл на диске — его полный путь; файла на машине нет
        (демо-кадр вне git) — путь как записан, с раскрытыми `$DDD_HOME` и `~`."""
        p = self.upload_path(f, s)
        if p is not None:
            return str(p)
        if f.startswith("$DDD_HOME/"):
            return str(kbpaths.home(f[len("$DDD_HOME/"):]))
        return str(Path(f).expanduser()) if f.startswith("~") else f

    def demo_paths(self, s, pid):
        """Пути демо-кадров плана ассетов страницы — расширение x-demo его слотов (ключи path_key)."""
        data = self.load(self.dsurf(s, "asset-plans") / f"{pid}.yaml")
        return {self.path_key(f, s) for sl in listify(get(data, "slots")) if isinstance(sl, dict)
                for _var, f, _what in mod("canvas_input").demo_files(sl)}

    def mat_boards(self, s):
        """R-MAT-014: что стоит на артбордах принятой единицы. Загрузка холста на артборде — `/_blob/<id>`; её файл
        называет строка «Загрузок» ARTIFACTS.md с этим id. Файл — из манифеста ассетов поверхности или продукта либо
        демо-кадр `x-demo` плана ассетов этой страницы; иначе единица принята на файле, которого нет ни в плане, ни
        в манифесте."""
        rows = {u: r for u, r in self.review(s)[1].items() if r.get("вердикт") in ACCEPTED}
        art = self.dprod("artifacts")
        if not rows or not art.is_file():
            return
        L = mod("layer")
        t = L.Md(art).table(("id", "файл", "слот", "артефакт"))
        ups = {L.cell(r.get("id")): self.upload_file(r.get("файл")) for r in t.rows} if t else {}
        known = set()
        for folder in (self.dsurf(s, "assets"), self.dprod("assets")):
            for r in self.manifest_rows(folder / "manifest.yaml"):
                p = self.asset_path(folder, r)
                if p is not None:
                    known.add(str(p))
        proj = self.dsurf(s, "canvas-project")
        rv = self.dsurf(s, "review") / "REVIEW.md"
        for unit, row in rows.items():
            ids = {}
            for a in row.get("artboards") or []:
                p = proj / a
                if Path(a).name == a and p.is_file():
                    for i in BLOB.findall(p.read_text(encoding="utf-8", errors="replace")):
                        ids.setdefault(i, a)
            if not ids:
                continue
            demo = self.demo_paths(s, unit)
            lost, stray = [], []
            for i, a in sorted(ids.items()):
                f = ups.get(i)
                if not f:
                    lost.append(f"{i} ({a})")
                    continue
                key = self.path_key(f, s)
                if key not in known and key not in demo:
                    stray.append(f"{i} — {f}")
            fix = self.dd(s, "assets — файл в манифест ассетов или демо-кадром x-demo плана ассетов страницы; строка "
                             "«Загрузок» — по протоколу холста")
            if stray:
                self.add("R-MAT-014", "error", s, "review", f"{s}#Приёмка/{unit}", rv,
                         f"{unit}: на принятых артбордах загрузки вне манифеста ассетов и вне x-demo плана ассетов "
                         f"страницы — {len(stray)}: " + listed(stray, 4, "; "), fix)
            if lost:
                self.add("R-MAT-014", "error", s, "review", f"{s}#Приёмка/{unit}", rv,
                         f"{unit}: на принятых артбордах загрузки без строки «Загрузок» ARTIFACTS.md — {len(lost)}: "
                         + listed(lost, 4, "; ") + " — файл загрузки не установить", fix)

    def mat_artifacts(self):
        p = self.dprod("artifacts")
        if not p.is_file():
            return
        L = mod("layer")
        md = L.Md(p)
        t = md.table(("артефакт", "тип", "адрес"))
        for r in t.rows if t else []:
            a = L.cell(r.get("артефакт"))
            miss = [c for c in t.columns if c != "артефакт" and L.is_empty(r.get(c))]
            if miss:
                self.add("R-MAT-006", "warning", None, "artifacts", f"ARTIFACTS#Артефакты/{a}", p,
                         f"артефакт {a}: нет полей {', '.join(miss)}", self.dd(what="холст — ARTIFACTS.md"))
        permitted = self.checks_permitted()
        for s in self.scope:
            rd = self.dsurf(s.slug, "review")
            results = [x for x in rd.iterdir() if x.is_file() and x.name != "REVIEW.md"] if rd.is_dir() else []
            if results and not permitted:
                self.add("R-MAT-006", "error", s.slug, "review", f"{s.slug}#review", rd,
                         f"в review/ есть результаты проверок артефакта ({listed((x.name for x in results), 4)}), а "
                         "строки «Проверки макета» в ARTIFACTS.md нет — снимается только подтверждённой человеком "
                         "разовой просьбой заказчика", self.dd(s.slug, "checks"))

    GENERATED = ("generate", "edit-real")                   # источники слота и варианта, которые идут генерацией

    @staticmethod
    def row_source(slot, row):
        """Источник файла строки манифеста → (источник, вариант плана или None). Строка называет вариант плана ассетов
        (`variant`; файл на несколько вариантов — `desktop+mobile`): у варианта с полем `source` источник — его, у
        варианта без поля и у строки без варианта — источник слота. Вариант-генерация среди вариантов строки —
        первым."""
        base = str(slot.get("source") or "")
        by_id = {str(v.get("id")): v for v in listify(slot.get("variants")) if isinstance(v, dict)}
        srcs = [(str(by_id[n].get("source") or base), n if by_id[n].get("source") else None)
                for n in str(row.get("variant") or "").split("+") if n in by_id]
        return next((x for x in srcs if x[0] in Audit.GENERATED), srcs[0] if srcs else (base, None))

    def mat_assets(self, s):
        folder = self.dsurf(s, "assets")
        rows = self.manifest_rows(folder / "manifest.yaml")
        slots = self.plan_slots(s)
        for r in rows:
            sid = str(r.get("slot") or "")
            hits = self.row_slots(slots, r, rows)
            f = self.asset_path(folder, r) or folder / Path(str(r.get("file") or "")).name
            if not hits:
                # у сайта генерация идёт только по плану ассетов страницы; иллюстрации кабинета — по ДС и паспорту
                if self.reg[s].page and any(r.get(k) is True for k in ("ai", "ai_mark", "ai_label")):
                    where = f"в плане ассетов страницы {r['page']}" if r.get("page") not in (None, "") else \
                        "ни в одном плане ассетов поверхности"
                    self.add("R-MAT-008", "error", s, "asset", sid or f.name, f if f.is_file() else
                             folder / "manifest.yaml", f"ассет слота {sid or '—'} с пометкой ИИ, а слота нет {where}: "
                             "генерация — только по утверждённому плану", self.dd(s, "asset-plan"))
                continue
            ai = bool(r.get("ai") or r.get("ai_mark"))
            # источник файла — у варианта плана, который называет строка; у варианта без поля — источник слота
            src = {id(slot): self.row_source(slot, r) for _ap, slot, _plan in hits}
            # строка без page при одном id слота у нескольких страниц — общая для страниц без своих строк: генерацию
            # разрешает утверждённый план любой из них, находка — когда не разрешает ни один
            open_ = [(ap, slot, plan) for ap, slot, plan in hits
                     if (ai or src[id(slot)][0] in self.GENERATED)
                     and not (get(plan, "status") == "approved" and bool(get(plan, "approval")))]
            if len(open_) == len(hits):
                # первым — план, где слот генерируется: его источник и id называет находка
                open_.sort(key=lambda x: (src[id(x[1])][0] not in self.GENERATED, x[0].stem))
                ap, slot, plan = open_[0]
                source, var = src[id(slot)]
                what = "; ".join(f"план ассетов {a.stem} — {get(p, 'status') or 'без статуса'}"
                                 + ("" if get(p, "approval") else " без approval") for a, _sl, p in open_)
                self.add("R-MAT-008", "error", s, "asset-plan", f"{ap.stem}#{sid}" + (f"/{var}" if var else ""),
                         f if f.is_file() else ap,
                         f"ассет слота {sid}" + (f", вариант {var}" if var else "") + f" ({source or None}) есть, а "
                         f"{what}: генерация — только после утверждения плана", self.dd(s, "asset-plan — утверждение"))
        # ключевые ассеты и ДС (R-MAT-007)
        if not self.reg[s].page:
            return
        keys = [(pg, sid) for (pg, sid), (_ap, sl, _p) in slots.items() if sl.get("key") and
                str(sl.get("source") or "") in ("generate", "edit-real")]
        if not keys:
            return
        many = {sid for _pg, sid in keys if sum(1 for _p, x in slots if x == sid) > 1}

        def name(pg, sid):                                  # id слота, у повторяющегося между страницами — со страницей
            return f"{pg}/{sid}" if sid in many else sid

        def rows_of(pg, sid):           # строки слота страницы, как у входа холста: с её page, без таких — без page
            mine = [r for r in rows if str(r.get("slot")) == sid]
            return [r for r in mine if str(r.get("page") or "") == pg] or [r for r in mine if not r.get("page")]

        note = self.state("design", "_phase-jump.md")
        debt = note.is_file() and re.search(r"ДС до ключевых ассетов", note.read_text(encoding="utf-8"))
        if self.status(self.dprod("system")) == "approved" and not debt:
            # у слота несколько строк — по файлу на формат и вариант; принят — есть принятая строка: её берёт вход
            late = [name(pg, sid) for pg, sid in keys
                    if not any(r.get("file") and r.get("status") == "accepted" for r in rows_of(pg, sid))]
            if late:
                self.add("R-MAT-007", "warning", s, "design-system", "system", self.dprod("system"),
                         f"ДС утверждена раньше ключевых ассетов {s}: {', '.join(late)} не приняты, долга «ДС до "
                         "ключевых ассетов» в заметке пропусков нет", self.dd(what="design-system"))
        vd = self.dsurf(s, "visual-dna")
        made = [name(pg, sid) for pg, sid in keys if rows_of(pg, sid)]
        if made and self.status(vd) != "approved":
            self.add("R-MAT-007", "warning", s, "visual-dna", "visual-dna", vd,
                     f"ключевые ассеты генерации ({', '.join(made)}) есть, а маркетинговый паспорт не approved",
                     self.dd(s, "art-direction"))

    def mat_blockers(self):
        """R-MAT-009: строка **blocker** заметки ветки у закрытого файла. Закрытие держит вопрос без ответа; строка,
        которая называет пробел фактов missing[] по id, — блокер публикации: файл закрывается с заглушкой пробела, а
        публикацию держит copydeck.py validate --final — подсказка."""
        gaps = [str(g) for g in self.facts()[2] if g]
        for branch in ("site", "design"):
            d = self.state(branch)
            for note in sorted(d.rglob("*.md")) if d.is_dir() else []:
                text = note.read_text(encoding="utf-8")
                m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
                ref = re.search(r"^ref:\s*(\S+)", m.group(1), re.M) if m else None
                if not ref or "**blocker**" not in text:
                    continue
                target = self.root / ref.group(1).strip().strip("'\"")
                if not target.is_file():
                    continue
                st = self.status(target)
                if st not in ("approved", "confirmed", "verified", "stable"):
                    continue
                # пункт списка — строка «- …» с продолжением до следующего пункта, заголовка или пустой строки
                items = [x for x in re.split(r"\n(?=\s*[-*]\s)|\n\s*\n|\n(?=#)", text[m.end():]) if "**blocker**" in x]
                publish = [x for x in items if any(re.search(rf"(?<![\w-]){re.escape(g)}(?![\w-])", x) for g in gaps)]
                hold = len(items) - len(publish)
                if hold:
                    self.add("R-MAT-009", "error", None, "state", note.stem, note,
                             f"строки **blocker** в заметке у закрытого файла {self.rel(target)} ({st}) — {hold}",
                             "закрыть вопрос словом владельца или вернуть файл в работу — " + self.dd())
                if publish:
                    named = sorted({g for g in gaps for x in publish
                                    if re.search(rf"(?<![\w-]){re.escape(g)}(?![\w-])", x)})
                    self.add("R-MAT-009", "hint", None, "state", note.stem, note,
                             f"блокер публикации в заметке у закрытого файла {self.rel(target)} ({st}) — "
                             f"{len(publish)}: пробелы фактов {listed(named)}; закрытие он не держит",
                             "перед публикацией сайта — copydeck.py validate --final (0 заглушек); пробел закрывает "
                             "источник заказчика: " + self.dd(what="meaning (факты)"))

    def mat_first_input(self):
        ab = self.dprod("app-brief")
        if not self.has_app or self.status(ab) != "approved":
            return
        L = mod("layer")
        srcs = [docpaths.project(self.slug, n, repo=self.root) for n in ("vision.md", "user.md", "surface.md",
                                                                         "object.md", "action.md")]
        srcs += [docpaths.layer(self.slug, "capability", s.slug, self.root) for s in self.surfaces if s.app]
        srcs += [docpaths.layer(self.slug, "interface", s.slug, self.root) / "scenario.md" for s in self.surfaces
                 if s.app]
        R = mod("ready")
        open_ = []
        for p in srcs:
            if not p.is_file():
                open_.append(f"{self.prel(p)} — нет")
                continue
            st = docpaths.status(p) or R.md_rows_status(p)
            if st not in (None, "stable"):
                open_.append(f"{self.prel(p)} — {st}")
        if open_:
            hubs = "; ".join(f"/interface-deep-dive {self.slug} {s.slug}" for s in self.surfaces if s.app)
            self.add("R-MAT-010", "warning", None, "app-brief", "app-brief", ab,
                     "бриф на вид закрыт, а источники первого входа не stable: " + listed(open_, 6, "; "),
                     f"источник закрывает слой проекта — /project-deep-dive {self.slug} (vision, user, surface, "
                     f"object, action, capability), сценарии хабов — {hubs}; поле ядра без источника — вопрос "
                     "questions[] со статусом assumed и долг в заметке пропусков: " + self.dd(what="app-brief"))
        _ = L

    def mat_second_input(self, s):
        if not self.env or not (self.dsurf(s.slug, "input") / "INPUT.md").is_file():
            return
        try:
            lay, _trees = self.layer_of(s.slug)
            items = mod("screen_map").check_layer(lay)
        except Exception as e:                              # noqa: BLE001
            self.notes.append(f"screen_map check {s.slug}: {e}")
            return
        self.tools.note("project/screen_map.py", f"check {s.slug}")
        bad = [f for f in items if f.severity in ("error", "warning")]
        if bad:
            # error — только если сам свод сломан (ошибка screen_map); расхождения уровня warning — доклад
            sev = "error" if any(f.severity == "error" for f in bad) else "warning"
            self.add("R-MAT-011", sev, s.slug, "map", "map", lay.map_path,
                     f"вход холста кабинета собран при своде map.md с расхождениями (screen_map check: {len(bad)} — "
                     + listed((f"{f.rule} {f.message[:60]}" for f in bad), 3, "; ") + ")",
                     f"свод и экраны — /screen-deep-dive {self.slug} {s.slug}; затем пересборка входа")

    # ================================================================ R-SEM
    def r_sem(self):
        files = [self.dprod(k) for k in ("brand", "system", "app-brief", "visual-dna")]
        for s in self.scope:
            if s.design:
                files += [self.dsurf(s.slug, "art-direction"), self.dsurf(s.slug, "visual-dna")]
                md = self.dsurf(s.slug, "motion")
                files += sorted(md.glob("*.yaml")) if md.is_dir() else []
                ad = self.dsurf(s.slug, "asset-plans")
                files += sorted(ad.glob("*.yaml")) if ad.is_dir() else []
        for f in files:
            data = self.load(f)
            if not isinstance(data, dict):
                continue
            s = f.parent.name if f.parent.name not in ("design", "plans", "motion") else \
                (f.parent.parent.name if f.parent.name == "motion" else
                 (f.parent.parent.parent.name if f.parent.name == "plans" else None))
            why = []
            st = str(data.get("status") or get(data, "project", "status") or "")
            if st in ("superseded", "retired"):
                why.append(f"статус {st}")
            if "supersedes" in data:
                why.append("поле supersedes")
            hist = get(data, "lifecycle", "history")
            if isinstance(hist, list) and len(hist) > 1:
                why.append(f"lifecycle.history, записей — {len(hist)} (остаётся текущая)")
            if why:
                kind = "design-system" if f.name == "system.yaml" else f.stem.split(".")[0]
                self.add("R-SEM-002", "warning", s, kind,
                         f.stem, f, "журнал версий в файле дизайна: " + ", ".join(why), self.dd(s))

    # ================================================================ R-DEBT
    def r_debt(self):
        notes = [("design", None, self.state("design", "_phase-jump.md"))]
        for s in self.scope:
            notes += [("site", s.slug, self.state("site", s.slug, "_phase-jump.md")),
                      ("design", s.slug, self.state("design", s.slug, "_phase-jump.md"))]
        for branch, s, p in notes:
            if not p.is_file():
                continue
            L = mod("layer")
            _line, body = L.section(p.read_text(encoding="utf-8"), "Что копать дальше")
            for item in re.findall(r"^\s*[-*]\s+(.+)$", body or "", re.M):
                self.add("R-DEBT-001", "hint", s, "state", f"{branch}/_phase-jump", p,
                         f"долг: {item.strip()[:220]}", "снимет слово владельца или названный этап")
        fdata, facts, _gaps = self.facts()
        fp = docpaths.facts(self.slug, repo=self.root)
        demo_file = bool(fdata.get("example"))
        demo_ids = {i for i, f in facts.items() if demo_file or f.get("example")}
        if demo_file:
            self.add("R-DEBT-002", "hint", None, "facts", "facts", fp,
                     "факты продукта — демо-данные (example: true): макет на них допустим, перед публикацией — "
                     "copydeck.py validate --final (0 демо-фактов)", self.dd(what="meaning (факты заказчика)"))
        elif demo_ids:
            self.add("R-DEBT-002", "hint", None, "facts", "facts", fp,
                     f"демо-факты в facts.yaml: {', '.join(sorted(demo_ids))}", self.dd(what="meaning"))
        for s in self.scope:
            if s.page:
                self.debt_decks(s.slug, demo_ids)
            if s.design:
                self.debt_review(s.slug)

    def debt_decks(self, s, demo_ids):
        for p, deck, _lang in self.decks(s):
            for pg in listify(get(deck, "pages")):
                if not isinstance(pg, dict):
                    continue
                pid = pg.get("page_id")
                used, holes = set(), []
                for f in listify(get(pg, "meta", "fact_ids")):
                    used.add(str(f))
                for sec in listify(pg.get("sections")):
                    for sl in listify(get(sec, "slots")):
                        if not isinstance(sl, dict):
                            continue
                        var = self.chosen(sl)
                        used |= {str(x) for x in listify(sl.get("fact_ids"))}
                        if var is not None:
                            used |= {str(x) for x in listify(var.get("fact_ids"))}
                            if "[PLACEHOLDER" in str(var.get("text") or ""):
                                holes.append(f"{sec.get('section_id')}/{sl.get('slot_id')}")
                demo = sorted(used & demo_ids)
                closed = pg.get("status") == "approved"
                if demo:
                    what = "закрытом copy deck" if closed else "copy deck"
                    self.add("R-DEBT-002", "hint", s, "copy-deck", f"{pid}#/fact_ids", p,
                             f"демо-факты (example: true) в {what} {pid}: {', '.join(demo)} — перед публикацией сайта "
                             "copydeck.py validate --final", self.dd(s, "copy — факты заказчика"))
                if holes:
                    self.add("R-DEBT-002", "hint", s, "copy-deck", f"{pid}#/placeholders", p,
                             f"заглушки [PLACEHOLDER] в copy deck {pid}: {listed(holes, 8)}",
                             self.dd(s, "copy — факты заказчика"))

    def debt_review(self, s):
        _fm, rows, _items = self.review(s)
        rv = self.dsurf(s, "review") / "REVIEW.md"
        for unit, row in rows.items():
            o = row.get("открыто")
            if o and o not in ("—", "-"):
                self.add("R-DEBT-002", "hint", s, "review", f"{s}#Приёмка/{unit}", rv, f"{unit}: открыто — {o[:200]}",
                         self.dd(s, "acceptance"))
        rd = self.dsurf(s, "ready")
        data = self.load(rd)
        units = [u for u in listify(get(data, "units")) if isinstance(u, dict) and u.get("open")]
        if units:
            self.add("R-DEBT-002", "hint", s, "ready", s, rd, "open манифеста готовности: " + listed(
                (f"{u.get('id')} — {len(listify(u.get('open')))}" for u in units), 6, "; "), self.dd(s, "package"))

    # ================================================================ R-VIS — перечень макетного прогона
    def visual_list(self):
        permitted = self.checks_permitted()
        out = []
        for s in self.scope:
            if not s.design:
                continue
            html = self.dsurf(s.slug, "canvas-html")
            copies = sorted(x.name for x in html.glob("*.html")) if html.is_dir() else []
            accepted = sorted(u for u, v in self.verdicts(s.slug).items() if v in ACCEPTED)
            out.append({"surface": s.slug, "request": "постоянная просьба в ARTIFACTS.md" if permitted else
                        "нет строки «Проверки макета»: прогон — только по разовой просьбе заказчика в сессии",
                        "copies": copies, "accepted": accepted,
                        "kit": (html / "kit.json").is_file(),
                        "rules": [{"rule": r, "how": h} for r, h in VISUAL.items()]})
        return out

    # ================================================================ итог
    def stages(self):
        out = []
        for s in self.scope:
            inp = self.input_stage(s.slug) if (s.page or s.app) else None
            verdicts = self.verdicts(s.slug) if s.design else {}
            out.append({"surface": s.slug, "type": s.type, "web_kind": s.web_kind, "route": s.route,
                        "input_stage": inp, "accepted": sorted(u for u, v in verdicts.items() if v in ACCEPTED),
                        "ready": self.ready_status(s.slug) if s.design else None})
        return out

    def ready_status(self, s):
        """Статус манифеста готовности поверхности: ready · partial · not-ready; «—» — статуса в файле нет; None —
        манифеста нет."""
        rd = self.dsurf(s, "ready")
        if not rd.is_file():
            return None
        st = get(self.load(rd), "status")
        return str(st) if st not in (None, "") else "—"

    def reading(self):
        cat = rules_catalog()
        out = []
        for rid, title, _sev in cat:
            if rid.startswith("R-VIS") or (rid == "R-FRESH-005" and not self.checks_permitted()):
                continue                                    # копии без просьбы о проверках — не предмет аудита
            what = READING.get(rid)
            if what is None and not self.env and rid in NEEDS_ENV:
                what = "окружение не установлено — правило проверяется чтением по форме"
            if what:
                out.append({"rule": rid, "title": title, "read": what})
        return out

    def result(self):
        items = self.rep.items
        return {"tool": TOOL, "project": self.slug, "surface": self.one, "root": str(self.root),
                "today": self.today.isoformat(), "utilities": "запускались" if self.env else
                "не запускались: окружение не установлено", "called": self.tools.used if self.tools else {},
                "surfaces": self.stages(), "counts": F.count(items), "notes": self.notes,
                "reading": self.reading(), "visual": getattr(self, "visual", None),
                "findings": [f.as_dict() for f in items]}


NEEDS_ENV = ("R-STRUCT-002", "R-STRUCT-003", "R-STRUCT-004", "R-STRUCT-005", "R-STRUCT-006", "R-COV-003",
             "R-COV-004", "R-COV-005", "R-FRESH-001", "R-FRESH-002", "R-FRESH-003", "R-FRESH-004", "R-FRESH-005",
             "R-MAT-011", "R-MAT-012")


# ------------------------------------------------------------------ вывод

def category(rule):
    return next((c for c in CATEGORIES if rule.startswith(c + "-")), "R-?")


def print_report(res, out=None):
    out = out or sys.stdout
    items = [F.Finding.from_dict(d) for d in res["findings"]]
    print(f"=== design_audit {res['project']}" + (f" {res['surface']}" if res["surface"] else "") + " ===", file=out)
    kinds = ", ".join(f"{s['surface']} ({s['type']}" + (f" · {s['web_kind']}" if s["web_kind"] else "") + ")"
                      for s in res["surfaces"]) or "—"
    print(f"Поверхности: {kinds}", file=out)
    print(f"Утилиты: {res['utilities']}; вызовов: " + (", ".join(f"{k} ×{len(v)}" for k, v in res["called"].items())
                                                       or "—"), file=out)
    groups = [(None, "Уровень продукта")] + [(s["surface"], f"Поверхность {s['surface']}") for s in res["surfaces"]]
    order = {s: i for i, s in enumerate(F.SEVERITIES)}
    for surf, title in groups:
        mine = [f for f in items if f.surface == surf]
        if not mine:
            continue
        print(f"\n— {title} —", file=out)
        for cat in CATEGORIES:
            cf = sorted((f for f in mine if category(f.rule) == cat), key=lambda f: (order[f.severity], f.path, f.ref))
            if not cf:
                continue
            print(cat, file=out)
            for f in cf:
                where = f"{surf} / " if surf else ""
                print(f"[{f.severity}] {where}{f.kind}:{f.ref} → {f.message} ({f.rule}).", file=out)
                print(f"  {f.path}" + (f"\n  Что делать: {f.fix}" if f.fix else ""), file=out)
    stray = [f for f in items if f.surface is not None and f.surface not in {s["surface"] for s in res["surfaces"]}]
    for f in stray:
        print(f"[{f.severity}] {f.surface} / {f.kind}:{f.ref} → {f.message} ({f.rule}).", file=out)
    c = res["counts"]
    verdict = "есть errors" if c["error"] else ("есть warnings" if c["warning"] else "чисто")
    print(f"\nСводка: {c['error']} error / {c['warning']} warning / {c['hint']} hint. Вердикт: {verdict}.", file=out)
    for n in res["notes"]:
        print(f"Заметка: {n}", file=out)
    if res["reading"]:
        print("\nЧтением (скилл):", file=out)
        for r in res["reading"]:
            print(f"  {r['rule']} «{r['title']}» — {r['read']}", file=out)
    if res.get("visual") is not None:
        print("\nМакетный прогон (R-VIS) — только с --visual и по просьбе заказчика:", file=out)
        for v in res["visual"]:
            print(f"  {v['surface']}: {v['request']}; копий {len(v['copies'])}, принято: "
                  f"{', '.join(v['accepted']) or '—'}", file=out)
        for r, h in VISUAL.items():
            print(f"  {r} — {h}", file=out)


def write_out(res, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "findings.jsonl").write_text("".join(json.dumps(f, ensure_ascii=False) + "\n"
                                                    for f in res["findings"]), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps({k: v for k, v in res.items() if k != "findings"},
                                                     ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def audit(slug, repo=None, surface=None, today=None, visual_list=False, run_tools=True):
    """Структурный прогон → словарь результата (находки — в поле findings)."""
    return Audit(slug, repo, surface, today, run_tools=run_tools).run(visual_list).result()


# ------------------------------------------------------------------ макетный прогон: отчёты mockup_checks

def allow_keys():
    """Ключи снятия проверок макета — реестр примет kb/common/tells.yaml, раздел checks: {id проверки: ключ --allow}."""
    p = kbpaths.kb(None, "common", "tells.yaml")
    try:
        checks = (yaml_mod().safe_load(p.read_text(encoding="utf-8")) or {}).get("checks")
    except (OSError, ValueError, ImportError):
        checks = None
    return {str(k): str(v["allow"]) for k, v in (checks or {}).items() if isinstance(v, dict) and v.get("allow")} \
        if isinstance(checks, dict) else {}


def visual_summary(slug, surface, reports, repo=None):
    """Отчёты mockup_checks.py page → (находки R-VIS-001, сводка {единица: {domains, clusters, counts, allowed}}).
    Единица — имя до «=» или target отчёта; счёт примет — по доменам в единице домена, домены и единицы не
    складываются. Находка, снятая ключом --allow (поле allowed отчёта, ключ — у её проверки в реестре примет), в
    R-VIS-001 не идёт при любой тяжести: сводка называет её в allowed — id, ключ, ширина и причина (поле reason находки
    или allowed.reason, когда allowed — запись)."""
    rep = F.Report()
    summ = {}
    root = docpaths.root(repo)
    keys = allow_keys()
    for spec in reports:
        unit, _, path = spec.rpartition("=") if "=" in spec else ("", "", spec)
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        unit = unit or Path(str(data.get("target") or p.stem)).stem
        s = data.get("summary") or {}
        summ[unit] = {"domains": {d: {"unit": v.get("unit"), "count": v.get("count", len(v.get("tells") or [])),
                                      "tells": v.get("tells") or []} for d, v in (s.get("domains") or {}).items()},
                      "clusters": s.get("clusters") or [], "counts": s.get("counts") or {}, "allowed": []}
        for f in data.get("findings") or []:
            mark = f.get("allowed")
            if mark and keys.get(str(f.get("id"))):
                why = mark.get("reason") if isinstance(mark, dict) else f.get("reason")
                summ[unit]["allowed"].append({"id": f.get("id"), "allow": keys[str(f.get("id"))],
                                              "view": f.get("view"), "reason": str(why or "").strip() or None})
                continue
            sev = GATE.get(str(f.get("severity")))
            if sev is None:
                continue
            view = f" · {f.get('view')}" if f.get("view") else ""
            rep.add("R-VIS-001", sev, surface=surface, kind="canvas", ref=f"{unit}#{f.get('id')}",
                    path=docpaths.rel(p, root) if p.is_absolute() else str(p),
                    message=f"{f.get('id')}{view}: {f.get('message')}" + (f" (примета {f.get('tell')})"
                                                                          if f.get("tell") else ""),
                    fix=str(f.get("fix") or ""))
    return rep.items, summ


# ------------------------------------------------------------------ вызов

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    _reexec_venv()
    if "--selftest" in argv:
        return _selftest()
    ap = docpaths.parser(TOOL, __doc__, commands=("check", "visual"), surface="optional")
    ap.add_argument("--today", metavar="ГГГГ-ММ-ДД", help="дата для сроков фактов (по умолчанию сегодня)")
    ap.add_argument("--visual-list", action="store_true", help="перечень макетного прогона R-VIS в сводку")
    ap.add_argument("--report", action="append", metavar="[ЕДИНИЦА=]ФАЙЛ", help="visual: отчёт mockup_checks.py "
                    "page --json (повтором — несколько)")
    call = docpaths.parse(ap, argv)
    today = None
    if call.args.today:
        try:
            today = dt.date.fromisoformat(call.args.today)
        except ValueError:
            ap.error("--today: ГГГГ-ММ-ДД")
    try:
        if call.command == "visual":
            if call.surf is None or not call.args.report:
                ap.error("visual: нужны поверхность и --report — visual <slug> <surface> --report ФАЙЛ.json")
            items, summ = visual_summary(call.slug, call.surface, call.args.report, call.repo)
            if call.json:
                F.print_findings(items, as_json=True)
            else:
                F.print_findings(items)
                for unit, v in summ.items():
                    doms = "; ".join(f"{d} ({x['unit'] or '—'}): {x['count']} — {', '.join(x['tells'])}"
                                     for d, x in v["domains"].items()) or "—"
                    cl = "; ".join(f"{c.get('id')} {len(c.get('members_hit') or [])} из {c.get('members')}"
                                   for c in v["clusters"]) or "—"
                    print(f"{unit}: приметы по доменам (единица домена, домены не складываются): {doms}; "
                          f"кластеры: {cl}")
                    for x in v["allowed"]:
                        view = f" · {x['view']}" if x.get("view") else ""
                        print(f"Заметка: {unit}: {x['id']}{view} снята ключом --allow {x['allow']} — "
                              + (x["reason"] or "причина в отчёте не записана"))
            return F.exit_code(items)
        res = audit(call.slug, call.repo, call.surface, today, call.args.visual_list)
        out_dir = call.out or kbpaths.out("project", TOOL, call.slug)
        write_out(res, out_dir)
        items = [F.Finding.from_dict(d) for d in res["findings"]]
        if call.json:
            F.print_findings(items, as_json=True)
            print(f"{TOOL}: сводка — {out_dir / 'summary.json'}", file=sys.stderr)
        else:
            print_report(res)
            print(f"\nФайлы результата: {out_dir}")
        return F.exit_code(items)
    except (F.ToolError, docpaths.DocPathError, OSError, ValueError) as e:
        print(f"{TOOL}: {e}", file=sys.stderr)
        return F.EXIT_USAGE


# посеянные дефекты фикстуры package-defects: (проект, правило, путь от корня данных) — шапки манифестов фикстур
# package-landing-defects и package-cabinet-defects
SEEDED = (
    ("otves-remont-nn", "R-SURF-004", "docs/projects/otves-remont-nn/screens/promo"),
    ("otves-remont-nn", "R-SURF-001", "docs/projects/otves-remont-nn/site/old-promo"),
    ("otves-remont-nn", "R-STRUCT-006", "docs/projects/otves-remont-nn/design/system.tokens.json"),
    ("otves-remont-nn", "R-REF-001", "docs/projects/otves-remont-nn/site/promo/site-brief.yaml"),
    ("otves-remont-nn", "R-REF-003", "docs/projects/otves-remont-nn/site/promo/copy/spasibo.yaml"),
    ("otves-remont-nn", "R-COV-002", "docs/projects/otves-remont-nn/site/promo/copy/spasibo.yaml"),
    ("otves-remont-nn", "R-COV-003", "docs/projects/otves-remont-nn/site/promo/plans/spasibo.yaml"),
    ("otves-office", "R-COV-005", "docs/projects/otves-office/design/system.yaml"),
    ("otves-office", "R-FRESH-001", "docs/projects/otves-office/design/system.tokens.css"),
    ("otves-office", "R-FRESH-003", "docs/projects/otves-office/design/office/input/copy.md"),
    ("otves-remont-nn", "R-FRESH-006", "docs/projects/otves-remont-nn/design/promo/ready.yaml"),
    ("otves-remont-nn", "R-MAT-008", "docs/projects/otves-remont-nn/design/promo/assets/logo.svg"),
    ("otves-remont-nn", "R-COV-007", "docs/projects/otves-remont-nn/voice.yaml"),
    ("otves-remont-nn", "R-DEBT-002", "docs/projects/otves-remont-nn/site/promo/copy/spasibo.yaml"),
)
# тот же дефект тем же правилом в соседних файлах: правка значения токена (R-FRESH-001) — по находке на производное
SEEDED_ALSO = (
    ("otves-office", "R-FRESH-001", "docs/projects/otves-office/design/DESIGN.md"),
    ("otves-office", "R-FRESH-001", "docs/projects/otves-office/design/_design-system/project/tokens.json"),
)


def _selftest():
    """Фикстуры package-landing, package-cabinet (0 error) и package-defects (14 посеянных дефектов), сценарии правил
    на копиях фикстур package-landing, input-site и package-cabinet — без валидаторов, а где правило идёт вызовом
    утилиты базы — с ней; без сети."""
    import shutil
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)

    cat = rules_catalog()
    ids = {r for r, _t, _s in cat}
    check(f"реестр rules.md читается: {len(cat)} правил, id не повторяются, все категории — из десяти",
          len(cat) == len(ids) >= 60 and all(category(r) in CATEGORIES for r in ids))
    check("правила чтением и макетного прогона — id реестра; R-VIS — все пять",
          set(READING) <= ids and set(VISUAL) == {r for r in ids if r.startswith("R-VIS")})
    kbpaths.use("tests")
    import fixture_project
    today = dt.date.fromisoformat(fixture_project.today())    # опорная дата фикстур: ключ today данных сверки
    me = str(Path(__file__).resolve())
    base, ds = {}, {}
    for name, slug in (("package-landing", "otves-remont-nn"), ("package-cabinet", "otves-office")):
        with fixture_project.built(name) as fx, tempfile.TemporaryDirectory(prefix="ddd-audit-cwd-") as cwd:
            r = subprocess.run([sys.executable, me, "check", slug, "--repo", str(fx.root), "--today",
                                today.isoformat(), "--json", "--out", str(Path(cwd) / "out")], cwd=cwd,
                               capture_output=True, text=True)
            try:
                items = F.parse_lines(r.stdout)
            except ValueError:
                items = None
            errs = [f for f in items or [] if f.severity == "error"]
            base[slug] = items or []
            summ = json.loads((Path(cwd) / "out" / "summary.json").read_text(encoding="utf-8")) \
                if (Path(cwd) / "out" / "summary.json").is_file() else {}
            check(f"{name}: check --json из чужой рабочей папки — код 0, строки контракта, 0 error"
                  + (f" (есть: {'; '.join(f.rule + ' ' + f.message[:70] for f in errs[:3])})" if errs else ""),
                  r.returncode == 0 and items is not None and not errs)
            check(f"{name}: сводка — утилиты запускались, правила чтением с тем, что прочитать",
                  summ.get("utilities") == "запускались" and summ.get("called")
                  and any(x["rule"] == "R-SEM-001" for x in summ.get("reading") or []))
            ds[slug] = (any(str(n).startswith("производные ДС не проверены") for n in summ.get("notes") or []),
                        "project/ds_build.py" in (summ.get("called") or {}))
    check("артефакт ДС без токенов DTCG (package-landing) — заметка сводки «производные ДС не проверены», ds_build не "
          "зовётся, находки R-STRUCT-006 нет; токены DTCG есть (package-cabinet) — ds_build зовётся, заметки нет",
          ds.get("otves-remont-nn") == (True, False) and ds.get("otves-office") == (False, True)
          and not any(f.rule == "R-STRUCT-006" for f in base.get("otves-remont-nn", [])))
    with fixture_project.built("package-defects") as fx:
        found, notes, surfs = {}, {}, {}
        for slug in ("otves-remont-nn", "otves-office"):
            res = audit(slug, fx.root, today=today, visual_list=True)
            found[slug] = [F.Finding.from_dict(d) for d in res["findings"]]
            notes[slug] = res["notes"]
            surfs[slug] = {x["surface"]: x for x in res["surfaces"]}
        seeded = set(SEEDED)
        hit = {(s, r, p) for s, r, p in seeded if any(f.rule == r and f.path == p for f in found[s])}
        miss = sorted(seeded - hit)
        check(f"package-defects: найдены все {len(SEEDED)} посеянных дефектов — своим правилом и с путём"
              + (f" (нет: {miss})" if miss else ""), not miss)
        extra = sorted({(s, f.rule, f.path) for s, fs in found.items() for f in fs if f.severity == "error"}
                       - seeded - set(SEEDED_ALSO))
        check("package-defects: лишних error нет — каждый error своим правилом в месте посева"
              + (f" (есть: {extra[:3]})" if extra else ""), not extra)
        old = [x for x in SEEDED if any(f.rule == x[1] and f.path == x[2] for f in base.get(x[0], []))]
        check("посевы — новые против чистых основ; кроме R-COV-007 в voice.yaml: у основы — другое условие (канала "
              "product-ui нет), у посева — канал есть, профиля голоса продукта нет"
              + (f" (у основы есть: {old})" if old != [SEEDED[12]] else ""),
              old == [SEEDED[12]] and any("профиля голоса продукта" in f.message for f in found[SEEDED[12][0]]
                                          if f.rule == SEEDED[12][1] and f.path == SEEDED[12][2]))
        check("битые токены: «свежесть не сверялась» — заметка сводки, а не находка R-FRESH-001",
              not any(f.rule == "R-FRESH-001" for f in found["otves-remont-nn"])
              and any("R-FRESH-001 не проверялось" in n for n in notes["otves-remont-nn"]))
        sev = {(f.rule, f.path): f.severity for fs in found.values() for f in fs}
        check("тяжесть по реестру и этапу: R-COV-002 error (copy deck закрыт), R-COV-005 error (вход mockup), "
              "R-COV-007 warning, R-DEBT-002 hint",
              sev.get(("R-COV-002", SEEDED[5][2])) == "error" and sev.get(("R-COV-005", SEEDED[7][2])) == "error"
              and sev.get(("R-COV-007", SEEDED[12][2])) == "warning"
              and sev.get(("R-DEBT-002", SEEDED[13][2])) == "hint")
        check("--visual-list: перечень R-VIS по поверхностям дизайна",
              res["visual"] and all(len(v["rules"]) == 5 for v in res["visual"]))
        check("сводка: ready — статус манифеста готовности (promo — not-ready), манифеста нет — null (office)",
              surfs["otves-remont-nn"]["promo"]["ready"] == "not-ready"
              and surfs["otves-office"]["office"]["ready"] is None)
        pl = next((f for f in found["otves-remont-nn"] if f.rule == "R-COV-003" and f.path == SEEDED[6][2]), None)
        sb = [f for f in found["otves-remont-nn"] if f.message.startswith("SB-")]
        m010 = next((f for f in found["otves-office"] if f.rule == "R-MAT-010"), None)
        c007 = next((f for f in found[SEEDED[12][0]] if f.rule == SEEDED[12][1] and f.path == SEEDED[12][2]), None)
        check("советы с этапом: PL-* — page-plan страницы, SB-* — brief, R-MAT-010 — слой проекта и этап app-brief, "
              "R-COV-007 без голоса продукта — meaning (голос продукта)",
              pl is not None and pl.fix.endswith("— page-plan:spasibo") and sb
              and all(f.fix.endswith("— brief") for f in sb) and m010 is not None
              and "/project-deep-dive otves-office" in m010.fix and m010.fix.endswith("— app-brief")
              and c007 is not None and c007.fix.endswith("— meaning (голос продукта)"))
    # сценарии правил на копии чистого лендинга, без валидаторов
    with fixture_project.built("package-landing") as fx:
        root, slug = fx.root, fx.slug
        pj = docpaths.project(slug, repo=root)
        a = Audit(slug, root, today=today, run_tools=False).run()
        res = a.result()
        check("без окружения: «утилиты не запускались», правила валидаторов — в чтении",
              "не запускались" in res["utilities"] and any(x["rule"] == "R-STRUCT-002" for x in res["reading"]))

        def rules_of(**kw):
            return {(f.rule, f.severity) for f in Audit(slug, root, today=today, run_tools=False, **kw).run().rep.items}

        (pj / "design" / "cabinet").mkdir(parents=True)
        (pj / "design" / "cabinet" / "art-direction.json").write_text('{"example": true}\n', encoding="utf-8")
        check("арт-дирекция у поверхности кабинета → R-SURF-006 error", ("R-SURF-006", "error") in rules_of())
        shutil.rmtree(pj / "design" / "cabinet")
        adp = pj / "design" / "promo" / "art-direction.json"
        adt = adp.read_text(encoding="utf-8")
        adp.write_text(adt.replace('"budget_profile": "landing-lead-services@L1"', '"budget_profile": '
                                   '"landing-lead-services@L2"').replace('"level": "L1"', '"level": "L2"', 1),
                       encoding="utf-8")
        got = rules_of()
        bare = json.loads(adt)
        bare.pop("budget", None)
        bare["ambition"] = {k: v for k, v in bare["ambition"].items()
                            if k not in ("level", "motion_cap", "budget_profile", "by_section_role")}
        adp.write_text(json.dumps(bare, ensure_ascii=False), encoding="utf-8")
        no_copy = rules_of()
        check("копии уровня и профиля в арт-дирекции отстали от брифа и плана → R-PROJ-002, R-PROJ-003 warning, не "
              "error; арт-дирекция без копий — находок R-PROJ нет",
              {("R-PROJ-002", "warning"), ("R-PROJ-003", "warning")} <= got
              and not any(r.startswith("R-PROJ") and s == "error" for r, s in got)
              and not any(r.startswith("R-PROJ") for r, _s in no_copy))

        def ad_rules():
            aa = Audit(slug, root, today=today)
            with tempfile.TemporaryDirectory(prefix="ddd-audit-ad-") as td:
                aa.tools = Tools(td)
                aa.design_files("promo")
            return [(f.rule, f.severity, f.message) for f in aa.rep.items]

        ad = json.loads(adt)
        ad["exclusions"]["k3_allow"] = ["no-such-key"]
        ad["decisions"][0]["decision"] = "bogus"
        adp.write_text(json.dumps(ad, ensure_ascii=False), encoding="utf-8")
        got = ad_rules()
        check("ad_check: ключ --allow вне реестра примет у незакрытой арт-дирекции → R-REF-006 warning; ошибка схемы "
              "в decisions → R-STRUCT-004 error, не R-REF-006",
              any(r == "R-REF-006" and s == "warning" for r, s, _m in got)
              and not any(r == "R-REF-006" and s == "error" for r, s, _m in got)
              and any(r == "R-STRUCT-004" and s == "error" and m.startswith("ad_check: decisions/") for r, s, m in got)
              and not any(r == "R-REF-006" and "decisions/" in m for r, s, m in got))
        ad["status"] = "approved"
        adp.write_text(json.dumps(ad, ensure_ascii=False), encoding="utf-8")
        check("ad_check: у закрытой арт-дирекции ключ --allow без решения → R-REF-006 error",
              any(r == "R-REF-006" and s == "error" for r, s, _m in ad_rules()))
        adp.write_text(adt, encoding="utf-8")
        art = pj / "design" / "ARTIFACTS.md"
        at = art.read_text(encoding="utf-8")
        art.write_text(at.replace("Проверки макета: разрешены", "Проверки макета: —"), encoding="utf-8")
        rv = pj / "design" / "promo" / "review"
        rv.mkdir(parents=True)
        (rv / "checks.json").write_text('{"example": true}\n', encoding="utf-8")
        check("результаты проверок в review/ без строки «Проверки макета» → R-MAT-006 error",
              ("R-MAT-006", "error") in rules_of())
        art.write_text(at, encoding="utf-8")
        (rv / "checks.json").unlink()
        (rv / "REVIEW.md").write_text(
            "# REVIEW\n\nИллюстрация самопроверки.\n\n## Приёмка\n\n"
            "| страница или экран | артборды | вердикт | одобрил | дата | отпечаток | открыто |\n"
            "|---|---|---|---|---|---|---|\n"
            "| `spasibo` | `Spasibo.dc.html` | `accepted` | — | — | sha256:0 | демо-факт company-since-2014 |\n",
            encoding="utf-8")
        got = rules_of()
        check("вердикт accepted без одобрения и с чужим отпечатком → R-MAT-005 error, R-MAT-004 warning; «открыто» — "
              "R-DEBT-002 hint", {("R-MAT-005", "error"), ("R-MAT-004", "warning"), ("R-DEBT-002", "hint")} <= got)
        (rv / "REVIEW.md").unlink()

        # одобрение по единице: отпечаток ready — артборды и источники единицы
        def ci(*a):
            return subprocess.run([sys.executable, str(HERE / "canvas_input.py"), "build", slug, "promo", *a, "--repo",
                                   str(root), "--today", today.isoformat()], capture_output=True, text=True)

        def found():
            return [(f.rule, f.severity, f.ref, f.message)
                    for f in Audit(slug, root, today=today, run_tools=False).run().rep.items]

        ci("--stage", "mockup")
        cp = docpaths.design(slug, "canvas-project", surface="promo", repo=root)
        cp.mkdir(parents=True)
        boards = {"home": "Home.dc.html", "spasibo": "Spasibo.dc.html"}
        (cp / boards["home"]).write_text("<section id='hero'>Главная</section>\n", encoding="utf-8")
        (cp / boards["spasibo"]).write_text("<section id='confirmation'>Заявка на замер принята</section>\n",
                                            encoding="utf-8")
        b = mod("ready").Build(slug, docpaths.surface(slug, "promo", root), root, today)
        accept = ("# REVIEW\n\nИллюстрация самопроверки.\n\n## Приёмка\n\n"
                  "| страница или экран | артборды | вердикт | одобрил | дата | отпечаток | открыто |\n"
                  "|---|---|---|---|---|---|---|\n"
                  + "".join(f"| `{u}` | `{a}` | `accepted` | владелец продукта | 2026-09-29 | "
                            f"{b.fingerprint(u, [a])} | — |\n" for u, a in boards.items()))
        (rv / "REVIEW.md").write_text(accept, encoding="utf-8")
        art.write_text(at.replace("| 2026-09-29 | аналитик |", "| 2026-10-02 | аналитик |"), encoding="utf-8")
        ci("--stage", "mockup")
        got0 = found()
        dk = docpaths.site(slug, "promo", "copy", "spasibo.yaml", repo=root)
        dkt = dk.read_text(encoding="utf-8")
        dk.write_text(dkt.replace("text: 'Вызвать замерщика'", "text: 'Позвать замерщика'", 1), encoding="utf-8")
        got1 = found()
        dk.write_text(dkt, encoding="utf-8")
        hb = (cp / boards["home"]).read_text(encoding="utf-8")
        (cp / boards["home"]).write_text(hb.replace("Главная", "Главная страница"), encoding="utf-8")
        got2 = found()
        (cp / boards["home"]).write_text(hb, encoding="utf-8")
        check("одобрение по единице: дата в ARTIFACTS.md и пересборка входа — без R-MAT-004; правка своего текста "
              "(spasibo) — R-MAT-004 только у spasibo; правка артборда home — R-MAT-004 только у home; R-FRESH-005 "
              "нет ни в одном случае",
              not any(r in ("R-MAT-004", "R-FRESH-005") for r, *_ in got0)
              and {(r, ref) for r, _s, ref, _m in got1 if r in ("R-MAT-004", "R-FRESH-005")}
              == {("R-MAT-004", "promo#Приёмка/spasibo")}
              and {(r, ref) for r, _s, ref, _m in got2 if r in ("R-MAT-004", "R-FRESH-005")}
              == {("R-MAT-004", "promo#Приёмка/home")})
        acc_md = ("\n## Пункты ACCEPTANCE\n\n| id | страница или экран | где | итог | доказательство |\n"
                  "|---|---|---|---|---|\n")
        (rv / "REVIEW.md").write_text(accept + acc_md + "| `B1` | `home` | макет | не пройдено | кадр 390 |\n",
                                      encoding="utf-8")
        one_unit = {ref for r, _s, ref, _m in found() if r == "R-MAT-005"}
        (rv / "REVIEW.md").write_text(accept + acc_md + "| `B1` | — | макет | не пройдено | кадр 390 |\n",
                                      encoding="utf-8")
        all_units = {ref for r, _s, ref, _m in found() if r == "R-MAT-005"}
        check("R-MAT-005 по единице: непройденный B с единицей (home) держит только её, без единицы — все принятые",
              one_unit == {"promo#Приёмка/home"} and all_units == {"promo#Приёмка/home", "promo#Приёмка/spasibo"})
        sp = docpaths.site(slug, "promo", "plans", "spasibo.yaml", repo=root)
        spt = sp.read_text(encoding="utf-8")
        (rv / "REVIEW.md").write_text(accept + acc_md + "| `C1` | — | макет | не пройдено | кадр 390 |\n",
                                      encoding="utf-8")
        s_all = {ref for r, _s, ref, m in found() if r == "R-MAT-005" and "пунктах S" in m}
        sp.write_text(spt.replace("\npage:\n", "\npage:\n  x-gate-exception:\n  - {id: C1, why: иллюстрация, who: "
                                  "владелец продукта}\n", 1), encoding="utf-8")
        s_one = {ref for r, _s, ref, m in found() if r == "R-MAT-005" and "пунктах S" in m}
        sp.write_text(spt, encoding="utf-8")
        check("R-MAT-005, пункт S по единице: непройденный S без единицы держит обе принятые единицы; исключение ворот "
              "в плане spasibo снимает его только у spasibo",
              s_all == {"promo#Приёмка/home", "promo#Приёмка/spasibo"} and s_one == {"promo#Приёмка/home"})

        def copies():
            aa = Audit(slug, root, today=today)
            with tempfile.TemporaryDirectory(prefix="ddd-audit-copies-") as td:
                aa.tools = Tools(td)
                aa.fresh_copies("promo")
            return ({f.severity for f in aa.rep.items if f.rule == "R-FRESH-005"}, set(aa.tools.used),
                    [n for n in aa.notes if "копи" in n or "dc_to_html" in n or "kit_manifest" in n])

        def reads_copies():
            return any(x["rule"] == "R-FRESH-005" for x in Audit(slug, root, today=today, run_tools=False).reading())

        asked, asked_read = copies(), reads_copies()
        art.write_text(at.replace("Проверки макета: разрешены", "Проверки макета: —"), encoding="utf-8")
        not_asked, not_asked_read = copies(), reads_copies()
        art.write_text(at, encoding="utf-8")
        check("R-FRESH-005 статичных копий: со строкой «Проверки макета: разрешены» — зовётся dc_to_html check, копий "
              "артбордов нет — error; манифест кадров kit.json не сверяется (kit_manifest не зовётся); без строки — "
              "утилита не зовётся, ни находки, ни заметки о копиях, и без окружения правила нет в чтении",
              asked[0] == {"error"} and asked[1] == {"claude-design/dc_to_html.py"}
              and not_asked == (set(), set(), []) and asked_read and not not_asked_read)
        # R-COV-002 по этапу: error под гейтом 2 — партия входа mockup или motion (units, pages/<id>/) или строка
        # «Приёмка»; партия входа направлений — warning
        (rv / "REVIEW.md").unlink()
        shutil.rmtree(cp.parent)
        hp = docpaths.site(slug, "promo", "plans", "home.yaml", repo=root)
        hpt = hp.read_text(encoding="utf-8")
        hp.write_text(hpt.replace("\nstatus: proposed\n", "\nstatus: approved\n", 1), encoding="utf-8")
        dk.write_text(dkt.replace("text: 'Политика обработки персональных данных'", "text: ''", 1), encoding="utf-8")

        def cov2():
            return {f.ref.split("#")[0]: (f.severity, f.message) for f in Audit(slug, root, today=today,
                                                                                 run_tools=False).run().rep.items
                    if f.rule == "R-COV-002"}

        ci("--stage", "directions", "--page", "home")
        a1 = cov2()
        ci("--stage", "mockup", "--page", "home")
        a4 = cov2()
        (rv / "REVIEW.md").write_text(accept, encoding="utf-8")
        a2 = cov2()
        (rv / "REVIEW.md").unlink()
        ci("--stage", "motion", "--page", "spasibo")
        a3 = cov2()
        hp.write_text(hpt, encoding="utf-8")
        dk.write_text(dkt, encoding="utf-8")
        shutil.rmtree(docpaths.design(slug, "input", surface="promo", repo=root))
        sev = {k: {u: v[0] for u, v in a.items()} for k, a in (("a1", a1), ("a2", a2), ("a3", a3), ("a4", a4))}
        check("R-COV-002 по этапу: партия входа направлений (directions --page home) — warning «тексты — до макета "
              "(гейт 2)», партия макета (mockup --page home) — error, вне партии (spasibo) — warning; строка «Приёмка» "
              "— error; вход без папок pages/ (motion --page spasibo) — error только у страницы из units",
              sev["a1"] == {"home": "warning", "spasibo": "warning"}
              and "этапа directions: тексты — до макета (гейт 2)" in a1["home"][1]
              and sev["a4"] == {"home": "error", "spasibo": "warning"}
              and "передана в дизайн: в партии входа холста этапа mockup" in a4["home"][1]
              and sev["a2"] == {"home": "error", "spasibo": "error"}
              and all("строка «Приёмка»" in a2[u][1] for u in ("home", "spasibo"))
              and sev["a3"] == {"home": "warning", "spasibo": "error"}
              and "в партии входа холста этапа motion" in a3["spasibo"][1])
        ip = pj / "integration.md"
        ip.write_text("# integration\n\nИллюстрация самопроверки.\n\n| slug | name | description | surface |\n"
                      "|---|---|---|---|\n| `amocrm` | amoCRM | Заявки с сайта — в CRM менеджера | [`promo`] |\n",
                      encoding="utf-8")
        r8 = [(f.severity, f.ref, f.message) for f in Audit(slug, root, today=today, run_tools=False).run().rep.items
              if f.rule == "R-COV-008"]
        ip.unlink()
        check("R-COV-008: получатели — CRM и интеграции брифа (каналы конверсии form, phone — нет), совпадение по "
              "любому слову: «CRM — не задана (q-crm)» — строка amoCRM; без строки — только телефония",
              len(r8) == 1 and r8[0][:2] == ("warning", "site-brief#/constraints/integrations")
              and r8[0][2].endswith("с поверхностью promo: телефония — номер компании"))
        note = root.joinpath(*STATE, slug, "site", "promo", "spasibo.md")
        note.parent.mkdir(parents=True)
        note.write_text("---\nkind: page-plan\nslug: spasibo\nref: docs/projects/otves-remont-nn/site/promo/plans/"
                        "spasibo.yaml\n---\n\n## Открытые вопросы\n- (**blocker**) Кто перезванивает — прораб или "
                        "офис?\n", encoding="utf-8")
        jump = root.joinpath(*STATE, slug, "design", "promo", "_phase-jump.md")
        jump.parent.mkdir(parents=True)
        jump.write_text("---\nkind: phase-jump\nref: docs/projects/otves-remont-nn/design/promo/\n---\n\n"
                        "## Что копать дальше\n- `art-direction` — выбрать направление словом заказчика.\n",
                        encoding="utf-8")
        got = rules_of()
        check("строка **blocker** у закрытого плана → R-MAT-009 error; долг заметки пропусков → R-DEBT-001 hint",
              ("R-MAT-009", "error") in got and ("R-DEBT-001", "hint") in got)
        shutil.rmtree(root / ".claude")
        one = {f.surface for f in Audit(slug, root, surface="promo", today=today, run_tools=False).run().rep.items}
        check("вызов с поверхностью — находки уровня продукта и этой поверхности", one <= {None, "promo"})
        y = yaml_mod()
        dp = docpaths.site(slug, "promo", "copy", "spasibo.yaml", repo=root)
        pp = docpaths.site(slug, "promo", "plans", "spasibo.yaml", repo=root)
        dtext, ptext = dp.read_text(encoding="utf-8"), pp.read_text(encoding="utf-8")
        deck, plan = y.safe_load(dtext), y.safe_load(ptext)
        deck["copy_deck"]["pages"][0]["sections"][0]["slots"][0]["group"] = "cta-1"
        plan["sections"][0]["treatment"] = {"motion_spec_ref": "../../../design/promo/motion/spasibo.motion-spec.yaml"
                                                               "#/sections/header"}
        dp.write_text(y.safe_dump(deck, allow_unicode=True, sort_keys=False), encoding="utf-8")
        pp.write_text(y.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
        am = docpaths.design(slug, "assets", surface="promo", repo=root) / "manifest.yaml"
        am.parent.mkdir(parents=True, exist_ok=True)
        am.write_text("example: true\nassets:\n  - {slot: nope-photo, file: nope.avif, ai: true, status: draft}\n",
                      encoding="utf-8")
        sec = deck["copy_deck"]["pages"][0]["sections"][0]
        where = f"spasibo#/{sec['section_id']}/{sec['slots'][0]['slot_id']}"
        got = [(f.rule, f.severity, f.ref, f.message) for f in
               Audit(slug, root, today=today, run_tools=False).run().rep.items]
        check("group слота copy deck не как у плана → R-REF-003 error; motion_spec_ref подачи секции в пустоту → "
              "R-REF-001 error; ассет с пометкой ИИ вне планов ассетов сайта → R-MAT-008 error",
              any(x[:3] == ("R-REF-003", "error", where) and "group cta-1" in x[3] for x in got)
              and any(x[:3] == ("R-REF-001", "error", "spasibo#/sections/0/treatment/motion_spec_ref") for x in got)
              and any(x[:3] == ("R-MAT-008", "error", "nope-photo") for x in got))
        dp.write_text(dtext, encoding="utf-8")
        pp.write_text(ptext, encoding="utf-8")
        am.unlink()
        # ключ ассета — страница и слот: слот header-logo есть в планах ассетов обеих страниц; строка манифеста — на
        # файл (формат, вариант); загрузки холста с отпечатком файла
        import copy
        import hashlib
        adir = am.parent
        aplans = {n: adir / "plans" / f"{n}.yaml" for n in ("home", "spasibo")}
        aplan_texts = {n: p.read_text(encoding="utf-8") for n, p in aplans.items()}

        def asset_plan(name, slots, **top):
            """План ассетов фикстуры с нужным статусом и слотами: слот по id правится или добавляется."""
            data = y.safe_load(aplan_texts[name])
            data.pop("approval", None)
            data.update(top)
            have = {sl.get("id"): sl for sl in data.setdefault("slots", []) if isinstance(sl, dict)}
            for sid, fields in slots.items():
                if sid in have:
                    have[sid].update(fields)
                else:
                    data["slots"].append({"id": sid, **fields})
            aplans[name].write_text(y.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

        asset_plan("home", {"header-logo": {"source": "real"}, "hero-visual": {"source": "edit-real", "key": True}},
                   status="approved", approval={"by": "владелец продукта (демо)", "date": "2026-09-29"})
        asset_plan("spasibo", {"header-logo": {"source": "generate"}}, status="draft")
        made = {"header-logo.svg": "<svg id='home'/>\n", "spasibo/header-logo.svg": "<svg id='spasibo'/>\n",
                "hero-visual-desktop.avif": "avif\n", "hero-visual-desktop.webp": "webp\n",
                "uslugi-header-logo.svg": "<svg id='uslugi'/>\n"}
        sha = {n: hashlib.sha256(text.encode("utf-8")).hexdigest() for n, text in made.items()}
        base_row = "role: informational, license: демо, origin: демо"
        rows = ["slot: header-logo, file: header-logo.svg, ai: true, status: accepted",
                "page: spasibo, slot: header-logo, file: spasibo/header-logo.svg, ai: true, status: draft",
                "slot: hero-visual, variant: desktop, format: avif, file: hero-visual-desktop.avif, ai: false, "
                "status: accepted",
                "slot: hero-visual, variant: desktop, format: webp, file: hero-visual-desktop.webp, ai: false, "
                "status: draft"]
        stray = "page: uslugi, slot: header-logo, file: uslugi-header-logo.svg, ai: true, status: draft"

        def manifest(rws):
            for r in rws:                                   # файл — у каждой строки манифеста, лишних файлов нет
                n = re.search(r"file: ([^,]+)", r).group(1)
                (adir / n).parent.mkdir(parents=True, exist_ok=True)
                (adir / n).write_text(made[n], encoding="utf-8")
            am.write_text("example: true\nassets:\n" + "".join(
                "  - {" + r + f", {base_row}, sha256: {sha[re.search(r'file: ([^,]+)', r).group(1)]}" + "}\n"
                for r in rws), encoding="utf-8")

        def assets():
            aa = Audit(slug, root, today=today, run_tools=False)
            aa.mat_assets("promo")
            aa.cov_assets(adir, "promo")
            aa.uploads("promo")
            aa.fresh_uploads()
            return [(f.rule, f.severity, f.ref, f.message) for f in aa.rep.items], aa.notes

        manifest(rows)
        g1, _n = assets()
        check("ключ ассета — страница и слот: строка без page при одном id слота у двух страниц — генерацию разрешает "
              "утверждённый план одной из них; строка с page — план своей страницы (R-MAT-008 error у spasibo); "
              "одноимённые файлы страниц в подпапках и строки на формат слота — без R-COV-009; у ключевого слота есть "
              "принятая строка — ДС не «раньше ассетов», паспорта нет — R-MAT-007 warning",
              [x[:3] for x in g1 if x[0] == "R-MAT-008"] == [("R-MAT-008", "error", "spasibo#header-logo")]
              and not any(x[0] == "R-COV-009" for x in g1)
              and [x[2] for x in g1 if x[0] == "R-MAT-007"] == ["visual-dna"]
              and any(x[0] == "R-MAT-007" and "(hero-visual)" in x[3] for x in g1))
        manifest(rows + [stray])
        g2, _n = assets()
        check("строка манифеста с page, плана ассетов которой нет: R-MAT-008 error «слота нет в плане ассетов "
              "страницы» и R-COV-009 warning у файла",
              any(x[:3] == ("R-MAT-008", "error", "header-logo") and "страницы uslugi" in x[3] for x in g2)
              and [x[2] for x in g2 if x[0] == "R-COV-009"] == ["uslugi-header-logo.svg"]
              and any(x[0] == "R-COV-009" and "page uslugi: слота header-logo нет" in x[3] for x in g2))
        manifest(["page: home, " + rows[0], rows[1].replace("page: spasibo, ", "")])
        g3, _n = assets()
        check("строка без page — общая для страниц без своих строк, как у входа холста: у home своя строка (план "
              "утверждён), общая строка с пометкой ИИ служит spasibo — R-MAT-008 error по плану spasibo",
              [x[:3] for x in g3 if x[0] == "R-MAT-008"] == [("R-MAT-008", "error", "spasibo#header-logo")])
        (adir / "uslugi-header-logo.svg").unlink()
        # отпечаток принятой строки сверяет plan_to_assets (R-STRUCT-005 error): сверенный им манифест R-COV-009 о
        # sha256 принятой строки не повторяет, черновая строка остаётся за R-COV-009
        manifest(rows)
        am.write_text(am.read_text(encoding="utf-8").replace(sha["header-logo.svg"], "c3" * 32)
                      .replace(sha["hero-visual-desktop.webp"], "c3" * 32), encoding="utf-8")

        def sha_refs(fingerprinted):
            aa = Audit(slug, root, today=today, run_tools=False)
            if fingerprinted:
                aa.fingerprinted.add(am)
            aa.cov_assets(adir, "promo")
            return sorted(f.ref for f in aa.rep.items if f.rule == "R-COV-009" and "sha256" in f.message)

        check("манифест, сверенный plan_to_assets: sha256 принятой строки R-COV-009 не называет, черновой — называет",
              sha_refs(False) == ["header-logo.svg", "hero-visual-desktop.webp"]
              and sha_refs(True) == ["hero-visual-desktop.webp"])
        # строка файла шрифта манифеста продукта: роли ассета у неё нет, остальные поля строки — как у любого файла
        pdir, woff = docpaths.design(slug, "assets", repo=root), b"wOF2\n"
        (pdir / "fonts").mkdir(parents=True)
        (pdir / "fonts" / "demo-400.woff2").write_bytes(woff)
        frow = ("slot: font-demo, file: fonts/demo-400.woff2, status: accepted, license: OFL (демо), ai: false, "
                f"sha256: {hashlib.sha256(woff).hexdigest()}, font: {{family: Demo Sans, weight: 400, style: normal}}")

        def font_need(row):
            (pdir / "manifest.yaml").write_text("example: true\nassets:\n  - {" + row + "}\n", encoding="utf-8")
            aa = Audit(slug, root, today=today, run_tools=False)
            aa.cov_assets(pdir, None)
            return [f.message.rpartition(" — ")[2] for f in aa.rep.items if f.rule == "R-COV-009"]

        fgot = [font_need(frow + ", origin: демо"), font_need(frow),
                font_need(frow.partition(", font:")[0] + ", origin: демо")]
        shutil.rmtree(pdir)                                 # у фикстуры папки ассетов продукта нет
        check("строка файла шрифта (font) манифеста продукта: роль ассета не нужна — с лицензией, происхождением и "
              "пометкой ИИ находок нет; без происхождения — R-COV-009 называет origin; строка без font — и role",
              fgot == [[], ["origin"], ["role"]])
        manifest(rows)
        up = "design/promo/assets/"

        def uploads_table(table):
            """ARTIFACTS.md фикстуры с таблицей table на месте таблицы раздела «Загрузки»."""
            text, n = re.subn(r"(## Загрузки\n(?:(?!\|)[^\n]*\n)*)(?:\|[^\n]*\n)+", lambda m: m.group(1) + table, at,
                              count=1)
            art.write_text(text if n else at + "\n## Загрузки\n\n" + table, encoding="utf-8")

        uploads_table("| id | файл | sha256 | слот | артефакт |\n|---|---|---|---|---|\n"
                      f"| `up-1` | `{up}header-logo.svg` | {sha['header-logo.svg']} | `header-logo` | "
                      "`canvas:promo` |\n"
                      f"| `up-2` | `{up}spasibo/header-logo.svg` — знак страницы «спасибо» | "
                      f"sha256:{sha['header-logo.svg']} | `header-logo` | `canvas:promo` |\n"
                      f"| `up-3` | `{up}hero-visual-desktop.avif` | — | `hero-visual` | `canvas:promo` |\n"
                      "| `up-4` | `$DDD_HOME/out/selftest-no-such/demo.webp` — демо, вне git | 0123456789ab | "
                      "`hero-visual` | `canvas:promo` |\n"
                      f"| `up-5` | `{up}spasibo/header-logo.svg` | {sha['spasibo/header-logo.svg'][:12]} | "
                      "`hero-visual` | `canvas:promo` |\n")
        u1, n1 = assets()
        f7 = [x for x in u1 if x[0] == "R-FRESH-007"]
        check("загрузки холста: sha256 строки не равен файлу — R-FRESH-007 warning (up-2); полный отпечаток и его "
              "начало — без находки (up-1, up-5); пустая ячейка — одна подсказка со счётом (1 из 5); файла нет на "
              "машине — заметка сводки (up-4)",
              "R-FRESH-007" in ids
              and sorted(x[1:3] for x in f7) == [("hint", "ARTIFACTS#Загрузки"), ("warning", "ARTIFACTS#Загрузки/up-2")]
              and any(x[1] == "hint" and "1 из 5 (up-3)" in x[3] and "нет колонки" not in x[3] for x in f7)
              and len(n1) == 1 and "R-FRESH-007 не проверялось" in n1[0] and n1[0].endswith("1: up-4"))
        check("загрузки холста: слот строки «Загрузки» сверяется с планом ассетов страницы файла (page строки "
              "манифеста) — R-REF-008 warning у up-5, у остальных строк находок нет",
              [x[2] for x in u1 if x[0] == "R-REF-008"] == ["ARTIFACTS#Загрузки/up-5"]
              and any(x[0] == "R-REF-008" and "страницы spasibo" in x[3] for x in u1))
        uploads_table("| id | файл | слот | артефакт |\n|---|---|---|---|\n"
                      f"| `up-1` | `{up}header-logo.svg` | `header-logo` | `canvas:promo` |\n")
        u2, _n = assets()
        check("загрузки холста: таблица без колонки sha256 — одна подсказка R-FRESH-007, не ошибка",
              [x[1] for x in u2 if x[0] == "R-FRESH-007"] == ["hint"]
              and any(x[0] == "R-FRESH-007" and "нет колонки sha256" in x[3] and "1 из 1" in x[3] for x in u2))
        # загрузки принятых артбордов: файл — из манифеста ассетов или демо-кадр x-demo плана ассетов страницы
        demo_file = "$DDD_HOME/out/selftest-no-such/hero-visual-demo.webp"
        owner = {"by": "владелец продукта (демо)", "date": "2026-09-29"}
        home_slots = {"header-logo": {"source": "real"}, "hero-visual": {"source": "edit-real", "key": True}}
        with_demo = dict(home_slots, **{"hero-visual": dict(home_slots["hero-visual"], **{
            "x-demo": {"file": demo_file, "what": "иллюстрация: кадр макета"}})})
        cp.mkdir(parents=True)
        (cp / "Home.dc.html").write_text("<img src='/_blob/up-1'><img src=\"/_blob/up-4\"><img src='/_blob/up-6'>"
                                         "<i style='background:url(/_blob/up-9)'></i>\n", encoding="utf-8")
        (cp / "Spasibo.dc.html").write_text("<img src='/_blob/up-6'>\n", encoding="utf-8")
        (rv / "REVIEW.md").write_text(
            "# REVIEW\n\nИллюстрация самопроверки.\n\n## Приёмка\n\n"
            "| страница или экран | артборды | вердикт | одобрил | дата | отпечаток | открыто |\n"
            "|---|---|---|---|---|---|---|\n"
            "| `home` | `Home.dc.html` | `accepted` | владелец продукта | 2026-09-29 | sha256:0 | — |\n"
            "| `spasibo` | `Spasibo.dc.html` | `blocked` | — | — | — | — |\n", encoding="utf-8")
        uploads_table("| id | файл | слот | артефакт |\n|---|---|---|---|\n"
                      f"| `up-1` | `{up}header-logo.svg` | `header-logo` | `canvas:promo` |\n"
                      f"| `up-4` | `{demo_file}` — демо, вне git | `hero-visual` | `canvas:promo` |\n"
                      "| `up-6` | `$DDD_HOME/out/selftest-no-such/stray.webp` | `hero-visual` | `canvas:promo` |\n")

        def boards():
            aa = Audit(slug, root, today=today, run_tools=False)
            aa.mat_boards("promo")
            return [(f.rule, f.severity, f.ref, f.message) for f in aa.rep.items]

        asset_plan("home", with_demo, status="approved", approval=owner)
        m1 = boards()
        asset_plan("home", home_slots, status="approved", approval=owner)
        m2 = boards()
        check("загрузки принятых артбордов (R-MAT-014 error у единицы): файл вне манифеста ассетов и вне x-demo плана "
              "ассетов страницы (up-6) и загрузка без строки «Загрузок» (up-9) — находки; файл манифеста (up-1) и "
              "демо-кадр x-demo (up-4) — нет; без x-demo в плане демо-кадр — тоже находка; единица без принятого "
              "вердикта не сверяется",
              [x[:3] for x in m1] == [("R-MAT-014", "error", "promo#Приёмка/home")] * 2
              and any("— 1: up-6 — " in x[3] for x in m1) and any("— 1: up-9 (Home.dc.html)" in x[3] for x in m1)
              and not any(u in x[3] for x in m1 for u in ("up-1", "up-4"))
              and any("— 2: up-4 — " in x[3] and "up-6" in x[3] for x in m2) and not any("up-1" in x[3] for x in m2)
              and not any("spasibo" in x[2] for x in m1 + m2))
        (rv / "REVIEW.md").unlink()
        shutil.rmtree(cp.parent)
        # источник файла — у варианта плана ассетов, который называет строка манифеста
        made["hero-visual-mobile.webp"] = "webp mobile\n"
        sha["hero-visual-mobile.webp"] = hashlib.sha256(made["hero-visual-mobile.webp"].encode("utf-8")).hexdigest()
        by_variant = [rows[2], "slot: hero-visual, variant: mobile, format: webp, file: hero-visual-mobile.webp, "
                               "ai: false, status: draft"]
        manifest(by_variant)
        asset_plan("home", {"hero-visual": {"source": "real", "variants": [
            {"id": "desktop"}, {"id": "mobile", "source": "generate"}]}}, status="draft")
        g4 = [x for x in assets()[0] if x[0] == "R-MAT-008"]
        asset_plan("home", {"hero-visual": {"source": "generate", "variants": [
            {"id": "desktop", "source": "real"}, {"id": "mobile"}]}}, status="draft")
        g5 = [x for x in assets()[0] if x[0] == "R-MAT-008"]
        (adir / "hero-visual-mobile.webp").unlink()
        check("источник по варианту плана ассетов: у настоящего слота вариант-генерация — R-MAT-008 только у строки "
              "этого варианта, с вариантом в ref; у слота-генерации настоящий вариант — без находки, вариант без "
              "поля source — источник слота",
              [x[1:3] for x in g4] == [("error", "home#hero-visual/mobile")] and "вариант mobile (generate)" in g4[0][3]
              and [x[1:3] for x in g5] == [("error", "home#hero-visual")] and "(generate)" in g5[0][3])
        art.write_text(at, encoding="utf-8")
        for n, p in aplans.items():
            p.write_text(aplan_texts[n], encoding="utf-8")
        am.unlink()
        for r in rows:
            (adir / re.search(r"file: ([^,]+)", r).group(1)).unlink()
        (adir / "spasibo").rmdir()

        def found_of(*rules):
            return [(f.rule, f.severity, f.ref, f.message)
                    for f in Audit(slug, root, today=today, run_tools=False).run().rep.items if f.rule in rules]

        # образцы шаблона коллекции: страницы copy deck с site_page_id = id плана
        deck, plan = y.safe_load(dtext), y.safe_load(ptext)
        sample = copy.deepcopy(deck["copy_deck"]["pages"][0])
        sample.update(page_id="spasibo-obrazec", site_page_id="spasibo", status="approved")
        deck["copy_deck"]["pages"].append(sample)
        dp.write_text(y.safe_dump(deck, allow_unicode=True, sort_keys=False), encoding="utf-8")
        j0 = found_of("R-REF-003")
        plan["page"]["template"] = True
        pp.write_text(y.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
        j1 = found_of("R-REF-003", "R-MAT-001")
        c1 = [x for x in found_of("R-COV-002") if x[2].startswith("spasibo-obrazec")]
        sl0 = sample["sections"][0]["slots"][0]
        var0 = next(v for v in sl0["variants"] if v["id"] == sl0["chosen"])
        text0, var0["text"] = var0["text"], ""
        dp.write_text(y.safe_dump(deck, allow_unicode=True, sort_keys=False), encoding="utf-8")
        c2 = [x for x in found_of("R-COV-002") if x[2].startswith("spasibo-obrazec")]
        var0["text"] = text0
        check("покрытие текстов у образца шаблона коллекции: образец с текстами всех слотов плана — без R-COV-002; "
              "слот образца без текста — R-COV-002 warning с id образца (запись коллекции — доклад, и у закрытой "
              "страницы образца)",
              not c1 and [x[1:3] for x in c2] == [("warning", f"spasibo-obrazec#/{sample['sections'][0]['section_id']}"
                                                   f"/{sl0['slot_id']}")]
              and "у образца spasibo-obrazec" in c2[0][3])
        sample["sections"][0]["slots"][0]["slot_id"] = "no-such-slot"
        dp.write_text(y.safe_dump(deck, allow_unicode=True, sort_keys=False), encoding="utf-8")
        j2 = found_of("R-REF-003")
        dp.write_text(dtext, encoding="utf-8")
        pp.write_text(ptext, encoding="utf-8")
        check("образец шаблона коллекции (вторая страница copy deck с site_page_id = id плана): у плана без "
              "page.template — R-REF-003 error «один copy deck на план»; у шаблона коллекции стык образца сверен и "
              "чист, план образца найден по site_page_id (R-MAT-001 без «план нет»); слот образца вне плана — "
              "R-REF-003 error с id образца",
              [x[1:3] for x in j0] == [("error", "spasibo")] and "только у шаблона коллекции" in j0[0][3]
              and not any(x[0] == "R-REF-003" for x in j1)
              and any(x[0] == "R-MAT-001" and x[2] == "spasibo-obrazec" for x in j1)
              and not any("план нет" in x[3] for x in j1)
              and [x[1:3] for x in j2] == [("error", f"spasibo-obrazec#/{sample['sections'][0]['section_id']}/"
                                            "no-such-slot")])
        # refs.copy_deck плана до этапа copy
        for path, text, ref in ((hp, hpt, "../copy/home.yaml"), (pp, ptext, "../copy/spasibo-typo.yaml")):
            data = y.safe_load(text)
            data["refs"]["copy_deck"] = ref
            path.write_text(y.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        r1 = {x[2]: x for x in found_of("R-REF-001")}
        hp.write_text(hpt, encoding="utf-8")
        pp.write_text(ptext, encoding="utf-8")
        check("refs.copy_deck плана ведёт в файл, которого ещё нет: copy deck страницы не заведён (home) — R-REF-001 "
              "hint «этап copy страницы не начат»; copy deck страницы есть, а ссылка мимо (spasibo) — error",
              r1.get("home#/refs/copy_deck", ("", ""))[1] == "hint"
              and "этап copy страницы не начат" in r1["home#/refs/copy_deck"][3]
              and [k for k, x in r1.items() if x[1] == "error"] == ["spasibo#/refs/copy_deck"])
        # refs.asset_plan и refs.treatment плана до своих этапов
        ap_dir = "../../../design/promo/assets/plans/"
        for path, text, refs in ((hp, hpt, {"asset_plan": ap_dir + "home.yaml"}),
                                 (pp, ptext, {"asset_plan": ap_dir + "spasibo-typo.yaml",
                                              "treatment": "../../../design/promo/art-direction-typo.json"})):
            data = y.safe_load(text)
            data["refs"].update(refs)
            path.write_text(y.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        aplans["home"].unlink()
        r2 = {x[2]: x for x in found_of("R-REF-001")}
        adp.unlink()
        r3 = {x[2]: x for x in found_of("R-REF-001")}
        adp.write_text(adt, encoding="utf-8")
        aplans["home"].write_text(aplan_texts["home"], encoding="utf-8")
        hp.write_text(hpt, encoding="utf-8")
        pp.write_text(ptext, encoding="utf-8")
        none = ("", "", "", "")
        check("refs.asset_plan и refs.treatment плана ведут в файл, которого ещё нет: плана ассетов страницы нет "
              "(home) — R-REF-001 hint «этап asset-plan страницы не начат», арт-дирекции поверхности нет — hint «этап "
              "art-direction не начат»; файл этапа есть, а ссылка мимо (spasibo) — error",
              r2.get("home#/refs/asset_plan", none)[1] == "hint"
              and "этап asset-plan страницы не начат" in r2["home#/refs/asset_plan"][3]
              and "home#/refs/treatment" not in r2
              and [r2.get(f"spasibo#/refs/{k}", none)[1] for k in ("asset_plan", "treatment")] == ["error", "error"]
              and [r3.get(f"{k}#/refs/treatment", none)[1] for k in ("home", "spasibo")] == ["hint", "hint"]
              and "этап art-direction не начат" in r3["home#/refs/treatment"][3])
        # папка итерации в review/ — по имени
        (rv / "REVIEW.md").write_text(accept, encoding="utf-8")
        for n in ("checks", "iter-02"):
            (rv / n).mkdir()
            (rv / n / "home.json").write_text('{"example": true}\n', encoding="utf-8")
        sem = [x[1:3] for x in found_of("R-SEM-002") if x[2].startswith("promo#")]
        (rv / "REVIEW.md").unlink()
        sem_bare = [x[1:3] for x in found_of("R-SEM-002") if x[2].startswith("promo#")]
        for n in ("checks", "iter-02"):
            shutil.rmtree(rv / n)
        check("подпапка review/: папка отчётов checks/ — не находка, папка итерации iter-02/ — R-SEM-002 warning, и "
              "без REVIEW.md тоже",
              sem == [("warning", "promo#iter-02")] == sem_bare and all(ITER_DIR.match(n) for n in (
                  "iter-1", "round3", "v2", "2026-09-30", "prev", "итерация-2", "03-mockup"))
              and not any(ITER_DIR.match(n) for n in ("checks", "shots", "shots-390", "kit", "reports", "runs", "390",
                                                      "1440", "390-dark")))
        # обходы copy deck — заметки сводки; словарь — у copy deck и фактов
        def with_tools(step):
            aa = Audit(slug, root, today=today)
            with tempfile.TemporaryDirectory(prefix="ddd-audit-deck-") as td:
                aa.tools = Tools(td)
                getattr(aa, step)("promo")
            return [(f.rule, f.severity, f.kind, f.message) for f in aa.rep.items], aa.notes

        deck = y.safe_load(dtext)
        d_sec = next(x for x in deck["copy_deck"]["pages"][0]["sections"] if x["section_id"] == "confirmation")
        d_slot = next(x for x in d_sec["slots"] if x["slot_id"] == "title")
        d_slot["lint_allow"] = [{"rule": "ru-syn-passive", "reason": "формула подтверждения заявки"}]
        dp.write_text(y.safe_dump(deck, allow_unicode=True, sort_keys=False), encoding="utf-8")
        _f, n_lint = with_tools("copy_decks")
        dp.write_text(dtext, encoding="utf-8")
        _f, n_none = with_tools("copy_decks")
        aa = Audit(slug, root, today=today, run_tools=False)
        aa.deck_bypasses(dp, {"allowed": [{"rule": "COPY-F-NUM", "where": "spasibo/confirmation/title",
                                           "reason": "номер шага, не утверждение", "by": "аналитик"}], "notes": []})
        check("обходы copy deck — заметки сводки с причиной: lint_allow слота (вывод copydeck.py check) и claims_allow "
              "(поле allowed); copy deck без обходов — заметок нет",
              [n for n in n_lint if n.startswith("обходы")] == [
                  "обходы lint_allow copy deck spasibo.yaml — 1: ru-syn-passive @ spasibo/confirmation/title: формула "
                  "подтверждения заявки"]
              and not [n for n in n_none if n.startswith("обходы")]
              and aa.notes == ["обходы claims_allow copy deck spasibo.yaml — 1: COPY-F-NUM @ spasibo/confirmation/title"
                               " — номер шага, не утверждение (аналитик)"])

        class NoClaims(Tools):
            """copydeck.py check с особым исходом: сверка фактов не отработала (вывод есть, причина — COPY-D-TOOL)."""

            def run(self, name, args, json_out=False, timeout=240):
                if name != "text/copydeck.py":
                    return super().run(name, args, json_out, timeout)
                self.note(name, f"код {COPYDECK_NO_CLAIMS}")
                return Run(COPYDECK_NO_CLAIMS, data={"findings": [{"tool": "claims", "level": "error", "rule": "COPY-D-TOOL",
                                                                   "where": "—", "message": "claims_check.py не отработал "
                                                                   "(код 2): вход не разбирается"}], "allowed": [], "notes": []})

        aa = Audit(slug, root, today=today)
        with tempfile.TemporaryDirectory(prefix="ddd-audit-deck-") as td:
            aa.tools = NoClaims(td)
            aa.copy_decks("promo")
        check("copydeck.py check с кодом 3 (сверка фактов не отработала) — заметка сводки с причиной; находки COPY-D-TOOL "
              "в отчёте нет",
              any(n.startswith("copydeck.py check ") and "сверка фактов не отработала" in n and "вход не разбирается" in n
                  for n in aa.notes) and not aa.rep.items)
        v0, _n = with_tools("vocab")
        dp.write_text(re.sub(r"page_type: \S+", "page_type: no-such-page-type", dtext, count=1), encoding="utf-8")
        v1, _n = with_tools("vocab")
        dp.write_text(dtext, encoding="utf-8")
        check("словарь site сверяется и у copy deck и фактов: чистая фикстура — находок у них нет; page_type вне "
              "словаря в copy deck — R-STRUCT-002 у copy deck",
              not [x for x in v0 if x[2] in ("copy-deck", "facts")]
              and [x[:3] for x in v1 if x[2] == "copy-deck"] == [("R-STRUCT-002", "error", "copy-deck")]
              and "no-such-page-type" in next(x[3] for x in v1 if x[2] == "copy-deck"))
        # голос: у проекта с сайтом профиль бренда обязателен
        vy = pj / "voice.yaml"
        vyt = vy.read_text(encoding="utf-8")
        vy.unlink()
        aa = Audit(slug, root, today=today, run_tools=False)
        aa.cov_voice()
        vy.write_text(vyt, encoding="utf-8")
        check("проект с лендингом без voice.yaml — R-COV-007 warning «профиля голоса voice.yaml нет»",
              [(f.severity, f.kind) for f in aa.rep.items if f.rule == "R-COV-007"] == [("warning", "voice")]
              and "voice.yaml нет" in aa.rep.items[0].message)
        # блокер публикации и блокер закрытия в заметке у закрытого плана
        note.parent.mkdir(parents=True)
        gap = "- (**blocker**) Этапы оплаты — из договора заказчика; до ответа на странице заглушка пробела\n" \
              "  `payment-stages`.\n"
        head = ("---\nkind: page-plan\nslug: spasibo\nref: docs/projects/otves-remont-nn/site/promo/plans/spasibo.yaml"
                "\n---\n\n## Открытые вопросы\n")
        note.write_text(head + gap, encoding="utf-8")
        b1 = found_of("R-MAT-009")
        note.write_text(head + gap + "- (**blocker**) Кто перезванивает — прораб или офис?\n", encoding="utf-8")
        b2 = found_of("R-MAT-009")
        shutil.rmtree(root / ".claude")
        check("R-MAT-009: строка **blocker** с id пробела фактов missing[] у закрытого плана — блокер публикации, hint "
              "(держит validate --final, не закрытие); вопрос без пробела рядом — error со счётом 1",
              [x[1] for x in b1] == ["hint"] and "payment-stages" in b1[0][3]
              and sorted(x[1] for x in b2) == ["error", "hint"]
              and next(x for x in b2 if x[1] == "error")[3].endswith("— 1"))
    # многостраничник: страницы и планы карты, запись утверждения планов, ДС до своего этапа, общие шапка и подвал
    with fixture_project.built("input-site") as fx, tempfile.TemporaryDirectory(prefix="ddd-audit-site-") as td:
        root, slug = fx.root, fx.slug
        y = yaml_mod()
        plans_dir = docpaths.site(slug, "corp", "plans", repo=root)

        def site(*steps):
            aa = Audit(slug, root, today=today)
            aa.tools = Tools(td)
            for step in steps:
                getattr(aa, step)("corp")
            return [(f.rule, f.severity, f.ref, f.message) for f in aa.rep.items], aa

        got, aa = site("site_validate", "cov_pages", "cov_ds", "mat_chrome")
        u01 = [x for x in got if "PL-U01" in x[3]]
        check("многостраничник: страница «спасибо» карты читается из поля page (в страницах — thanks-request, пустых "
              "id нет); страница без плана — одна находка R-COV-001; общие шапка и подвал планов равны — R-MAT-013 нет",
              "thanks-request" in aa.site_pages("corp") and "None" not in aa.site_pages("corp")
              and [x[1:3] for x in got if x[0] == "R-COV-001"] == [("hint", "consent")]
              and not any(x[0] == "R-MAT-013" for x in got))
        check("PL-U01: планы approved без записи approval — одна строка R-STRUCT-002 warning со списком планов",
              [x[:3] for x in u01] == [("R-STRUCT-002", "warning", "corp#PL-U01")] and " — 15: " in u01[0][3]
              and all(p in u01[0][3] for p in ("about", "home", "not-found", "thanks-request")))
        # литерал цели телефона в двух планах не равен machine факта, в третьем цель записана словами; факты проекта —
        # по ссылке брифа от его папки (у фикстуры ссылка примера)
        tel = {plans_dir / p: (plans_dir / p).read_text(encoding="utf-8")
               for p in ("about.yaml", "contacts.yaml", "news.yaml")}
        bpath = docpaths.site(slug, "corp", "brief", repo=root)
        btext = bpath.read_text(encoding="utf-8")
        bpath.write_text(btext.replace("facts_ref: facts.yaml", "facts_ref: ../../facts.yaml"), encoding="utf-8")
        for p, text in tel.items():
            p.write_text(text.replace("value: tel:+79000000002", "value: 'tel: номер отдела продаж'"
                                      if p.name == "news.yaml" else "value: tel:+70000000001"), encoding="utf-8")
        lit, a08 = site("site_validate")
        for p, text in list(tel.items()) + [(bpath, btext)]:
            p.write_text(text, encoding="utf-8")
        f08 = [x for x in lit if "PL-F08" in x[3]]
        f09 = [f for f in a08.rep.items if "PL-F09" in f.message]
        check("PL-F08: литерал цели телефона, которого нет у machine фактов, в двух планах — одна строка R-COV-003 "
              "warning со списком планов, совет — этап meaning; литерал, равный machine факта, — без находки",
              [x[:3] for x in f08] == [("R-COV-003", "warning", "corp#PL-F08")]
              and f08[0][3].endswith(" — 2: about, contacts") and not any("PL-F08" in x[3] for x in got)
              and [f.fix for f in a08.rep.items if "PL-F08" in f.message] == [a08.dd("corp", Audit.SV_ONE["PL-F08"][3])])
        check("PL-F09: цель телефона словами — R-COV-003 warning у своего плана, совет — этап плана страницы; у планов "
              "с литералом — без находки",
              [(f.rule, f.severity, f.ref, f.fix) for f in f09] == [("R-COV-003", "warning", "news",
                                                                     a08.dd("corp", "page-plan:news"))]
              and not any("PL-F09" in x[3] for x in got))
        check("сайт с планами до этапа дизайн-системы (арт-дирекция не утверждена, токенов ДС нет): «нет карты "
              "решений» — R-COV-005 hint",
              [x[1] for x in got if x[0] == "R-COV-005" and x[2] == "system"] == ["hint"])
        texts = {p.name: p.read_text(encoding="utf-8") for p in sorted(plans_dir.glob("*.yaml"))}
        for name, text in texts.items():
            if name not in ("about.yaml", "home.yaml"):
                (plans_dir / name).write_text(text.rstrip("\n") + "\napproval: {by: владелец продукта, date: "
                                              "'2026-09-29'}\n", encoding="utf-8")
        (plans_dir / "about.yaml").write_text(texts["about.yaml"].rstrip("\n") + "\nx-approval: {by: владелец "
                                              "продукта, date: '2026-09-29'}\n", encoding="utf-8")
        (plans_dir / "404.yaml").unlink()
        tk = docpaths.design(slug, "tokens", repo=root)
        tk.write_text('{"example": true}\n', encoding="utf-8")
        got, aa = site("site_validate", "cov_pages", "cov_ds")
        tk.unlink()
        for name, text in texts.items():
            (plans_dir / name).write_text(text, encoding="utf-8")
        u01 = [x for x in got if "PL-U01" in x[3]]
        check("PL-U01: два плана approved без approval — одна строка с двумя id; план с записью в расширении "
              "x-approval назван припиской",
              len(u01) == 1 and u01[0][3].endswith(" — 2: about, home; запись лежит расширением x-approval, её место — "
                                                   "approval — about"))
        check("служебный шаблон без плана: предупреждение SM-22 валидатора в аудит не идёт — у страницы not-found одна "
              "находка R-COV-001, подсказка аудита",
              [x[1] for x in got if x[0] == "R-COV-001" and "not-found" in x[3]] == ["hint"]
              and not any("SM-22" in x[3] for x in got))
        check("сайт с токенами ДС без карты решений — этап дизайн-системы начат: R-COV-005 warning, как у кабинета до "
              "макета", [x[1] for x in got if x[0] == "R-COV-005" and x[2] == "system"] == ["warning"])
        cplan = y.safe_load(texts["contacts.yaml"])
        footer = next(x for x in cplan["sections"] if x.get("role") == "footer")
        footer["slots"]["text"] = [x for x in footer["slots"]["text"] if x["id"] != "nav-3-label"]
        (plans_dir / "contacts.yaml").write_text(y.safe_dump(cplan, allow_unicode=True, sort_keys=False),
                                                 encoding="utf-8")
        copy_dir = docpaths.site(slug, "corp", "copy", repo=root)
        copy_dir.mkdir(parents=True, exist_ok=True)
        for pid, label in (("home", "Оставить заявку"), ("about", "Оставить заявку"), ("contacts", "Отправить запрос")):
            (copy_dir / f"{pid}.yaml").write_text(y.safe_dump({"example": True, "copy_deck": {"pages": [{
                "page_id": pid, "sections": [{"section_id": "header", "slots": [{
                    "slot_id": "cta-label", "chosen": "v1", "variants": [{"id": "v1", "text": label}]}]}]}]}},
                allow_unicode=True, sort_keys=False), encoding="utf-8")
        got, aa = site("mat_chrome")
        (plans_dir / "contacts.yaml").write_text(texts["contacts.yaml"], encoding="utf-8")
        shutil.rmtree(copy_dir)
        ch = {x[2]: x for x in got if x[0] == "R-MAT-013"}
        check("общие шапка и подвал (R-MAT-013 warning, пара страниц и слот): у страницы contacts нет слота подвала "
              "nav-3-label — находка у её плана; текст кнопки шапки в copy deck contacts не как у home — находка у "
              "copy deck; равные тексты (home, about) и хлебные крошки своей страницы — без находок",
              sorted(ch) == ["contacts#/footer/text/nav-3-label", "contacts#/header/text/cta-label"]
              and all(x[1] == "warning" for x in ch.values())
              and re.search(r"у страницы contacts его нет, у страницы [a-z-]+ — есть",
                            ch["contacts#/footer/text/nav-3-label"][3])
              and re.search(r"у страницы contacts — «Отправить запрос», у страницы (home|about) — «Оставить заявку»",
                            ch["contacts#/header/text/cta-label"][3]))
    # продукт только с кабинетом: один профиль голоса продукта; копии ядра брифа на вид
    with fixture_project.built("package-cabinet") as fx:
        root, slug = fx.root, fx.slug
        y = yaml_mod()
        vpp = docpaths.voice(slug, True, root)

        def part(step):
            aa = Audit(slug, root, today=today, run_tools=False)
            getattr(aa, step)()
            return [(f.rule, f.severity, f.kind, f.message) for f in aa.rep.items]

        v_none = part("cov_voice")
        product = {"example": True, "scope": {"genres": ["interface"],
                                              "surfaces": [{"surface": "product-ui", "voice": "product"}]}}
        vpp.write_text(y.safe_dump(product, allow_unicode=True, sort_keys=False), encoding="utf-8")
        v_one = part("cov_voice")
        product["scope"]["surfaces"][0]["voice"] = "brand"
        vpp.write_text(y.safe_dump(product, allow_unicode=True, sort_keys=False), encoding="utf-8")
        v_bad = part("cov_voice")
        vpp.unlink()
        check("продукт только с кабинетом: один профиль voice.product.yaml с каналом product-ui — без R-COV-007 "
              "(voice.yaml и scope.product_voice_ref не нужны); канал не product или профиля нет — R-COV-007 warning у "
              "voice.product.yaml",
              not v_one and [x[:3] for x in v_none] == [("R-COV-007", "warning", "voice-product")]
              and "voice.product.yaml нет" in v_none[0][3]
              and [x[:3] for x in v_bad] == [("R-COV-007", "warning", "voice-product")]
              and "нет канала product-ui" in v_bad[0][3])
        abp = docpaths.design(slug, "app-brief", repo=root)
        abt = abp.read_text(encoding="utf-8")
        ab = y.safe_load(abt)
        p_base = part("proj_app")
        ab["core"]["pointer"] = {"no-such-surface": "both"}
        abp.write_text(y.safe_dump(ab, allow_unicode=True, sort_keys=False), encoding="utf-8")
        p_stale = part("proj_app")
        for k in ("pointer", "postures", "status_roles", "platform_constraints"):
            ab["core"].pop(k, None)
        ab.pop("surfaces", None)
        abp.write_text(y.safe_dump(ab, allow_unicode=True, sort_keys=False), encoding="utf-8")
        p_bare = part("proj_app")
        ab = y.safe_load(abt)
        ab["allow"] = {"markers": ["cards", "no-such-key"], "why": "иллюстрация: решение заказчика"}
        abp.write_text(y.safe_dump(ab, allow_unicode=True, sort_keys=False), encoding="utf-8")
        lifted = part("app_allow")
        abp.write_text(abt, encoding="utf-8")
        check("ключи --allow брифа на вид против реестра примет kb/common/tells.yaml: ключ реестра (cards) — без "
              "находки, ключ вне реестра — R-REF-006",
              [x[0] for x in lifted] == ["R-REF-006"] and "«no-such-key»" in lifted[0][3])
        check("копии источников в ядре брифа на вид: копия отстала — R-PROJ-001 warning с этапом обновления; бриф без "
              "копий и чистая фикстура — без находки",
              not p_base and not p_bare and [x[:3] for x in p_stale] == [("R-PROJ-001", "warning", "app-brief")])
    # макетный прогон: отчёт mockup_checks → R-VIS-001 и сводка по доменам
    with tempfile.TemporaryDirectory(prefix="ddd-audit-vis-") as td:
        rep = Path(td) / "home.json"
        rep.write_text(json.dumps({"target": "canvas/html/home.html", "summary": {
            "counts": {"critical": 1, "major": 1, "minor": 0, "info": 1},
            "domains": {"page-look": {"unit": "страница", "count": 1, "tells": ["caps-eyebrow"]},
                        "honesty": {"unit": "страница", "count": 1, "tells": ["stock-and-hotlink"]}},
            "clusters": []}, "findings": [
            {"id": "HON-STOCK", "tell": "stock-and-hotlink", "severity": "critical", "view": "1440", "message": "сток",
             "fix": "реальное фото", "allowed": False},
            {"id": "LOOK-EYEBROW", "tell": "caps-eyebrow", "severity": "major", "view": "390", "message": "капс",
             "fix": "", "allowed": False},
            {"id": "LOOK-ARROWS", "tell": "arrow-in-button", "severity": "info", "view": "390", "message": "стрелка",
             "fix": "", "allowed": True}]}), encoding="utf-8")
        items, summ = visual_summary("otves-remont-nn", "promo", [f"home={rep}"], repo=None)
        check("отчёт mockup_checks → R-VIS-001: critical → error, major → warning, info и снятое ключом — нет",
              [(f.rule, f.severity) for f in items] == [("R-VIS-001", "error"), ("R-VIS-001", "warning")])
        check("сводка примет — по доменам в единице домена, домены не складываются",
              set(summ["home"]["domains"]) == {"page-look", "honesty"}
              and all(v["count"] == 1 for v in summ["home"]["domains"].values()))
        rep2 = Path(td) / "vhod.json"
        rep2.write_text(json.dumps({"target": "canvas/html/vhod.html", "summary": {}, "findings": [
            {"id": "M-NAV", "severity": "critical", "view": "390", "message": "меню нет", "fix": "", "allowed": True,
             "reason": "страница входа без меню — решение заказчика"},
            {"id": "M-NAV", "severity": "info", "view": "1440", "message": "меню нет", "fix": "",
             "allowed": {"reason": "страница входа без меню"}},
            {"id": "M-OVERFLOW", "severity": "critical", "view": "390", "message": "горизонтальная прокрутка",
             "fix": "", "allowed": True}]}), encoding="utf-8")
        items2, summ2 = visual_summary("otves-remont-nn", "promo", [str(rep2)], repo=None)
        check("находка, снятая ключом --allow реестра примет (M-NAV — no-nav), в R-VIS-001 не идёт и при тяжести "
              "critical: сводка называет её с ключом и причиной; пометка allowed у проверки без ключа снятия в "
              "реестре находку не снимает",
              [(f.severity, f.ref) for f in items2] == [("error", "vhod#M-OVERFLOW")]
              and summ2["vhod"]["allowed"] == [
                  {"id": "M-NAV", "allow": "no-nav", "view": "390",
                   "reason": "страница входа без меню — решение заказчика"},
                  {"id": "M-NAV", "allow": "no-nav", "view": "1440", "reason": "страница входа без меню"}]
              and summ["home"]["allowed"] == [{"id": "LOOK-ARROWS", "allow": "arrows", "view": "390",
                                               "reason": None}])
    check("перечень макетного прогона: R-VIS-005 — один пакет заданий судьи с --runs 3",
          "--runs 3" in VISUAL["R-VIS-005"] and "отдельными заданиями" not in VISUAL["R-VIS-005"])
    print("design_audit selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
