#!/usr/bin/env python3
"""ready — манифест готовности поверхности к сборке `docs/projects/<slug>/design/<surface>/ready.yaml` для репозитория
кода и проверка его свежести.

Форма — `docs/projects/_template/design/_template/ready.yaml`; канон — `docs/projects/_template/design/README.md`,
«Пакет для кода»; этап — `references/phases.md`, `package`. Манифест производный: его собирает эта утилита из закрытых
файлов стратегии, он коммитится вместе с источниками и руками не правится. Репозиторий кода собирает единицы с
`ready: true` и проверяет пункты «после сборки» способом из манифеста.

    ready build <slug> <surface> [--repo DIR] [--out DIR] [--today ГГГГ-ММ-ДД] [--json]
        собрать и записать design/<surface>/ready.yaml (--out DIR — в DIR/ready.yaml); --json — манифест JSON в stdout
    ready check <slug> [<surface>] [--repo DIR] [--today …] [--json]
        свежесть: файл равен сборке по текущим источникам (R-FRESH-006); без <surface> — все поверхности с ready.yaml
    ready show  <slug> <surface> [--repo DIR] [--today …] [--json]
        единицы: статусы, вердикт REVIEW.md, отпечаток одобрения из REVIEW.md и текущий — по артбордам строки «Приёмка»
        и источникам единицы; текущий этап acceptance пишет в колонку «отпечаток» REVIEW.md
    ready --selftest                  фикстуры package-landing, input-landing, input-site и package-cabinet, без сети

Поверхности — с маршрутом дизайна и холстом: web рода landing, site или app; admin, desktop, embed.

Что собирается (поля формы):
  skill_version                       версия скилла (файл VERSION, kbpaths.skill_version) — версия контракта утилит с
                                      репозиторием кода; check её не сравнивает
  surface, type, web_kind, consumer   реестр surface.md: landing и site → <org>/site; app, admin, desktop, embed →
                                      <org>/frontend; web_kind у admin, desktop, embed — «—»
  sources                             файлы, которые читает код, со статусом и sha256 (путь — от папки проекта): сайт —
                                      бриф, карта, планы, copy deck, факты, голос, ДС (статус токенов, CSS и прозы —
                                      статус system.yaml), бренд, манифест ассетов продукта, арт-дирекция, спецификации
                                      движения, манифест ассетов поверхности, исходники холста принятых единиц,
                                      REVIEW.md, integration.md; кабинет — экраны, блоки, каркасы, map.md, texts.md,
                                      FSD-карта, ДС, бриф на вид, продуктовый паспорт, манифесты ассетов, исходники
                                      холста принятых экранов, REVIEW.md. Исходники холста принятой единицы — её
                                      артборды из строки «Приёмка» REVIEW.md с вердиктом accepted или
                                      accepted_with_notes (`canvas/project/<Имя>.dc.html`, все ширины приёмки) и их
                                      статичные копии `canvas/html/<Имя>.html`, если собраны (проверки по просьбе).
                                      Лабораторная страница принятого приёма сайта — источник-папка
                                      `design/<surface>/motion/lab/<id>/` (путь с «/» на конце): её называет
                                      prototype.lab_path арт-дирекции или references[].source.url спецификации движения
                                      страницы; статус — prototype.status (у папки из спецификации — «—»), sha256 —
                                      отпечаток папки (dir_sha); папки нет — источника нет
  units                               сайт — страницы планов site/<surface>/plans/ (порядок build_order карты или
                                      pages.list брифа); кабинет — экраны screens/<surface>/screens/
    composition                       сайт — статус плана; кабинет — статус экрана
    texts                             сайт — статус страницы copy deck (none — текстов нет); кабинет — наименьший статус
                                      строк texts.md, которые экран называет (draft < assumed < checked < approved)
    mockup                            вердикт строки «Приёмка» review/REVIEW.md, если отпечаток одобрения совпал с
                                      текущим; не совпал или строки нет — none; skipped — строка «макет пропущен»
                                      заметки пропусков поверхности (<state>/design/<surface>/_phase-jump.md)
    budget_profile, gate_exceptions   сайт — page.budget_profile и id x-gate-exception плана своей страницы (исключение
                                      ворот соседней страницы в единицу не идёт); кабинет — «—» и []
    after_build                       пункты места «после сборки» kb/common/acceptance-criteria.yaml рода поверхности
                                      с выполненным условием when: {id, severity, check} — тяжесть по условиям пункта
                                      (у сайта условия eu и law — по основной юрисдикции своей страницы: вне ru и eu
                                      пунктов права J4b и L3 нет), способ проверки — поле check (gates, tool, code,
                                      manual); вход холста манифест не читает
    open                              заглушки [PLACEHOLDER] выбранных текстов (вариант chosen, у слота без chosen —
                                      единственный), демо-факты (example: true), которые страница называет,
                                      демо-кадры — «демо-кадр: <слот>» на слот плана ассетов страницы с расширением
                                      x-demo (кадр макета не для публикации), и у каждой единицы — «шрифт: <семейство>
                                      [<насыщенности>] …»: начертание токенов ДС, которому нужен файл
                                      (ds_build.font_needs — семейство и насыщенности его типографики), без принятой
                                      строки манифеста ассетов продукта с этим font, файлом и лицензией, и «тема: …»:
                                      бриф поверхности ждёт темы, которой нет у токенов ДС (ds_build.theme_gaps,
                                      правило R-COV-010); вход сверки, который есть, но не читается, — та же строка с
                                      причиной «… сверить нечем»: токены ДС (не разбираются, не объект или не по
                                      форме — ошибки R-STRUCT-006) — «шрифт: …» и «тема: …», бриф — «тема: …», план
                                      ассетов страницы — «демо-кадр: …»; токенов или брифа нет — строки нет; затем
                                      строки «решение заказчика: …» — ДС не утверждена, у
                                      кабинета ещё покрытие ДС типов своего экрана не полное (ds_coverage) и FSD-карта
                                      не stable, и открытые источники группы «контекст» («<путь> <статус>»,
                                      context_open): готовность они не держат, решает заказчик
    ready                             композиция закрыта (план approved, экран stable), тексты approved, факты
                                      публикуемы или пробел назван, макет принят с совпавшим отпечатком (или пропущен
                                      решением заказчика); у сайта ещё закрыта поверхность — бриф и у рода site карта
                                      approved (иначе блокер «поверхность: …»)
    publishable                       ready, а в open только строки «решение заказчика: …» — единицу код публикует
                                      (вместе с copydeck.py validate --final без error)
  факты единицы сайта — ссылки fact: и missing: слотов данных плана и fact_ids выбранных текстов copy deck: демо-факт —
  строка open (пробел назван), missing: со строкой пробела в facts.yaml — названный пробел; готовность единицы они не
  держат, публикацию сайта с демо-фактом держит copydeck.py validate --final; в blockers («факты: …») — факт, которого
  нет в facts.yaml, missing: без строки пробела, факт, который claims_check не допускает к публикации (разрешение,
  срок, проверка), и факт с machine не по форме или не из canonical (claims_check.machine_issues, error), значение
  которого берёт страница: она называет факт (ссылка fact:<id> плана в любом поле, fact_ids её текстов — те же записи
  фактов, что в отпечатке одобрения: canvas_input.page_fact_ids), на него ведёт цель messenger:<fact-id> плана или
  призыва шапки карты или его machine стоит литералом цели плана (tel:, mailto:, адрес ссылки). Исправление machine
  снимает блокер без новой приёмки макета: в отпечаток одобрения machine не входит. Файл фактов есть, но не читается
  (YAML не разбирается, не форма фактов — claims_check его не загружает) — сверить факты нечем: блокер «факты: файл
  фактов не читается» у единицы, которая берёт факты (называет факт или пробел, ведёт цель messenger:, tel:, mailto:
  или адресом ссылки); сверка упала на записи факта — «факты: fact:<id> (запись факта не читается)»
  perf                                сайт — plans; кабинет — {field: p75, rum: true, lab: [AC-PRF-04, AC-PRF-05,
                                      AC-PRF-06]}
  frontend_design                     сайт — род, уровень и потолок движения брифа (потолок без поля брифа — уровень
                                      движения ambition-levels.yaml); кабинет — поправки ui/CONTRADICTIONS.md §[C25]
  status, blockers                    ready — готовы все единицы, partial — часть, not-ready — ни одной; blockers —
                                      строка на причину, по которой единица или поверхность не готова

Отпечаток одобрения единицы — sha256 двух строк: «артборды:<`dc_to_html.fingerprint` её артбордов>» (колонка
«артборды» таблицы «Приёмка», `canvas/project/<Имя>.dc.html`) и «источники:<`canvas_input.unit_fingerprint`>» —
источники единицы: у страницы план, её тексты в copy deck, план ассетов и файлы слотов, спецификация движения, записи
фактов, бренд и арт-дирекция; у экрана файл экрана, его блоки и каркас, его строки texts.md, бриф на вид; у обеих
токены ДС и system.yaml. Правка артборда или источника единицы снимает одобрение; пересборка входа (вход motion тоже),
дата в ARTIFACTS.md, поля вне отпечатка (canvas_input.OUTSIDE_FP: запись решения — статус, утверждение, starter — и
machine факта) и правка соседней единицы — нет.

Проверка (check): манифест на диске против сборки в памяти по тем же источникам; ключ `example` (пометка иллюстрации
у фикстур) не сравнивается. Находка — строка контракта `findings.py`: R-FRESH-006, error, kind ready. Файла нет —
проверять нечего. Форма файла (R-STRUCT-008) — `form_errors(data)`, её зовёт design_audit.
Код выхода: 0 — ошибок нет; 1 — есть error; 2 — ошибка вызова или окружения.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "lib"))
import kbpaths  # noqa: E402
import docpaths  # noqa: E402
import findings as F  # noqa: E402

TOOL = "ready"
KIND = "ready"
RULE = "R-FRESH-006"
FILE = "ready.yaml"
CONSUMER = {"page": "<org>/site", "app": "<org>/frontend"}
PERF_APP = {"field": "p75", "rum": True, "lab": ["AC-PRF-04", "AC-PRF-05", "AC-PRF-06"]}
C25 = ("ui/CONTRADICTIONS.md §[C25]: фон сплошной, градиент только в названных местах, без оркестрованной загрузки, "
       "гарнитура с проверенной кириллицей")
VERDICTS = ("accepted", "accepted_with_notes", "blocked", "none", "skipped")
ACCEPTED = ("accepted", "accepted_with_notes")
TEXT_ORDER = ("draft", "assumed", "checked", "approved")
STATE = (".claude", "skills", "entrypoint", "state", "projects")
SKIP_LINE = re.compile(r"макет\s+пропущен", re.I)
LAB_PATH = re.compile(r"(?:^|/)motion/lab/([A-Za-z0-9][A-Za-z0-9._-]*)")   # папка лабораторной страницы приёма → её id
DECIDE = "решение заказчика: "                          # строка open: готовность не держит, решает заказчик
CLOSED = ("approved", "verified", "stable", "accepted")   # закрытый статус источника контекста по его форме
FORM_KEYS = ("skill_version", "surface", "type", "web_kind", "consumer", "status", "sources", "units", "perf",
             "frontend_design", "blockers")
UNIT_KEYS = ("id", "ready", "publishable", "composition", "texts", "mockup", "budget_profile", "gate_exceptions",
             "after_build", "open")
FD_KEYS = ("surface", "ambition", "motion_cap", "app_screens")
HEADER = ("# ready.yaml — готовность поверхности {surface} к сборке для репозитория кода.",
          "# Производный файл: собирает `scripts/project/ready.py build {slug} {surface}` из файлов стратегии; руками "
          "не правится.",
          "# Форма — docs/projects/_template/design/_template/ready.yaml.")


# ------------------------------------------------------------------ окружение и модули соседей

def _reexec_venv():
    """Без PyYAML или jsonschema (формат токенов ДС сверяет `ds_build.validate`) в текущем Python — один перезапуск
    в Python окружения скилла."""
    import importlib.util
    if all(importlib.util.find_spec(m) is not None for m in ("yaml", "jsonschema")):
        return
    py = kbpaths.python()
    if os.environ.get("DDD_READY_VENV") or not Path(py).exists():
        return
    os.environ["DDD_READY_VENV"] = "1"
    os.execv(py, [py, str(Path(__file__).resolve())] + sys.argv[1:])


_MOD = {}


def mod(name):
    """Модуль соседней утилиты: dc_to_html (claude-design), claims_check и copydeck (text), утилиты project/ — по
    имени."""
    if name not in _MOD:
        import importlib
        if name == "dc_to_html":
            kbpaths.use("claude-design")
        elif name in ("claims_check", "copydeck"):
            kbpaths.use("text")
        _MOD[name] = importlib.import_module(name)
    return _MOD[name]


def yaml_mod():
    import yaml
    return yaml


def load(path):
    """YAML или JSON файла; нет файла или он не разбирается — None."""
    p = Path(path)
    if not p.is_file():
        return None
    try:
        text = p.read_text(encoding="utf-8")
        return json.loads(text) if p.suffix == ".json" else yaml_mod().safe_load(text)
    except Exception:                                       # noqa: BLE001 — битый файл ловят валидаторы его вида
        return None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dir_sha(path):
    """Отпечаток папки: sha256 строк «<путь файла от папки>\\t<sha256 файла>» через перевод строки, UTF-8. Порядок —
    sorted(Path): по сегментам пути, сегменты — посимвольно по кодовым точкам Unicode, без учёта локали."""
    root = Path(path)
    lines = [f"{p.relative_to(root).as_posix()}\t{sha(p)}" for p in sorted(x for x in root.rglob("*") if x.is_file())]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def get(d, *path, default=None):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def dash(v):
    return "—" if v in (None, "", [], {}) else v


def font_span(weight):
    """Насыщенность строки манифеста ассетов (`font.weight`): число 400 → (400, 400), диапазон вариативного шрифта
    «100 900» → (100, 900); значение вне формы — None."""
    ok = isinstance(weight, (int, str)) and not isinstance(weight, bool)
    m = re.fullmatch(r"(\d+)(?: (\d+))?", str(weight)) if ok else None
    return (int(m.group(1)), int(m.group(2) or m.group(1))) if m else None


# ------------------------------------------------------------------ статусы источников

def md_rows_status(path):
    """Статус md-файла таблиц со столбцом status (FSD-карта, texts.md): все строки stable/approved — он же, иначе
    наименьший; нет строк — None."""
    L = mod("layer")
    try:
        md = L.Md(path)
    except Exception:                                       # noqa: BLE001
        return None
    vals = []
    for t in md.tables():
        if "status" in t.columns:
            vals += [L.cell(r.get("status")) for r in t.rows if not L.is_empty(r.get("status"))]
    if not vals:
        return None
    for order in (TEXT_ORDER, ("draft", "stable")):
        if all(v in order for v in vals):
            return min(vals, key=order.index)
    return vals[0]


def file_status(path, ds_status=None):
    p = Path(path)
    if p.name in ("system.tokens.json", "system.tokens.css", "DESIGN.md") and p.parent.name == "design":
        return ds_status or "—"
    st = docpaths.status(p)
    if st is None and p.suffix == ".md":
        st = md_rows_status(p)
    return st or "—"


# ------------------------------------------------------------------ сборка

class Build:
    """Сборка манифеста одной поверхности в памяти: data — словарь формы, blockers, units."""

    def __init__(self, slug, surf, repo, today=None):
        self.slug, self.surf = slug, surf
        self.repo = docpaths.root(repo)
        self.surface = surf.slug
        self.project = docpaths.project(slug, repo=self.repo)
        self.today = today or dt.date.today()
        self.blockers = []
        self.surf_open = []
        self.context = []
        self.header_cta = ""
        self.facts_unreadable = False
        self._facts = None
        self._tokens = None
        self._fonts = None
        self._theme = None
        self._src = {}

    # пути
    def prel(self, p):
        return Path(p).resolve().relative_to(self.project.resolve()).as_posix()

    def dsurf(self, *parts):
        return docpaths.design(self.slug, *parts, surface=self.surface, repo=self.repo)

    def dprod(self, *parts):
        return docpaths.design(self.slug, *parts, repo=self.repo)

    # общее
    @property
    def ds_status(self):
        return docpaths.status(self.dprod("system")) if self.dprod("system").is_file() else None

    def tokens(self):
        """Токены ДС для сверок шрифта и темы: (словарь, None). Файла нет — (None, None): ДС без токенов — решение
        заказчика (строка «ДС не утверждена»), сверять нечего. Файл есть, а не разбирается, не объект или не по форме
        DTCG (ошибки `ds_build.validate`, правило R-STRUCT-006: по токену с ошибкой начертание или тему не вывести)
        — (None, причина): сверить нечем, и строки open «шрифт: …» и «тема: …» называют причину вместо находок."""
        if self._tokens is None:
            p = self.dprod("tokens")
            data, why = load(p), None
            if p.is_file() and not isinstance(data, dict):
                why = f"токены ДС не читаются ({self.prel(p)})"
            elif isinstance(data, dict) and any(i.severity == "error" for i in mod("ds_build").validate(data)):
                why = f"токены ДС не по форме ({self.prel(p)}: ошибки R-STRUCT-006)"
            self._tokens = (data if isinstance(data, dict) and not why else None, why)
        return self._tokens

    @property
    def fonts_open(self):
        """Строки open «шрифт: <семейство> [<насыщенности>] …» — у каждой единицы: начертание токенов ДС, которому
        нужен файл (`ds_build.font_needs`: семейство и насыщенности его типографики, начертание normal), без файла —
        принятой строки манифеста ассетов продукта с этим `font` (семейство, насыщенность числом или диапазоном
        вариативного шрифта, `style: normal`), файлом на диске и лицензией `license`. Семейству без типографического
        токена хватает одного такого файла. Код подключает шрифты по строкам манифеста; без файла начертания
        страница — не та, что одобрена на макете. Токены не читаются или не по форме (`tokens`) — строка «шрифт: … —
        начертания сверить нечем»; манифест, который не читается, строк не снимает: принятого файла по нему нет."""
        if self._fonts is None:
            data, unread = self.tokens()
            man = self.dprod("assets") / "manifest.yaml"
            rows = load(man)
            rows = rows.get("assets") if isinstance(rows, dict) else rows
            have = {}
            for r in rows if isinstance(rows, list) else []:
                f = r.get("font") if isinstance(r, dict) else None
                span = font_span(f.get("weight")) if isinstance(f, dict) and f.get("style") == "normal" else None
                if span and r.get("status") == "accepted" and isinstance(r.get("file"), str) \
                        and (man.parent / r["file"]).is_file() and str(r.get("license") or "").strip():
                    have.setdefault(str(f.get("family")).lower(), []).append(span)
            self._fonts = [f"шрифт: {unread} — начертания сверить нечем"] if unread else []
            for fam, weights in (mod("ds_build").font_needs(data) if data else {}).items():
                got = have.get(fam.lower(), [])
                lack = [w for w in weights if not any(lo <= w <= hi for lo, hi in got)]
                if lack or not got:
                    what = " " + ", ".join(f"{w:g}" for w in lack) if lack else ""
                    self._fonts.append(f"шрифт: {fam}{what} — нет принятого файла с лицензией (строка манифеста "
                                       "design/_assets/ с font)")
        return self._fonts

    @property
    def theme_open(self):
        """Строка open «тема: …» — у каждой единицы: бриф поверхности (у сайта — бриф сайта, у кабинета — бриф на вид)
        ждёт темы, которой нет у токенов ДС ни темой значений `modes.base`, ни режимом (`ds_build.theme_gaps`, правило
        R-COV-010). Код ставит тему брифа атрибутом `data-theme`; без неё у токенов страница получит не ту
        `color-scheme`. Бриф есть, а сверить нечем — он сам не читается или токены не читаются или не по форме
        (`tokens`) — строка «тема: … сверить нечем». Брифа или токенов нет — строки нет: сверять нечего."""
        if self._theme is None:
            DB = mod("ds_build")
            data, unread = self.tokens()
            own = self.surface if self.surf.page else None
            brief = docpaths.site(self.slug, own, "brief", repo=self.repo) if own else self.dprod("app-brief")
            self._theme, has = [], brief.is_file()
            if has and not isinstance(load(brief), dict):
                self._theme = [f"тема: бриф не читается ({self.prel(brief)}) — тему сверить нечем"]
            elif has and unread:
                self._theme = [f"тема: {unread} — тему брифа сверить нечем"]
            elif has and data is not None:
                try:
                    gaps = DB.theme_gaps(DB.Project.of(self.slug, self.repo), DB.Tokens(data))
                except Exception:                           # noqa: BLE001 — темы брифов продукта не вывести
                    gaps = None
                self._theme = ["тема: темы брифов не вывести (ds_build.theme_gaps) — тему сверить нечем"] \
                    if gaps is None else [
                        f"тема: бриф ждёт {', '.join(sorted(need))}, у токенов ДС — {', '.join(sorted(have))} "
                        "(тема значений modes.base или режим)" for surf, _path, need, have in gaps if surf == own]
        return self._theme

    def review(self):
        """Строки «Приёмка» REVIEW.md: {единица: {artboards, verdict, fingerprint, by, date, open}}."""
        p = self.dsurf("review") / "REVIEW.md"
        if not p.is_file():
            return {}
        L = mod("layer")
        t = L.Md(p).table(("вердикт",))
        out = {}
        for r in t.rows if t else []:
            unit = L.cell(r.get("страница или экран"))
            if L.is_empty(unit):
                continue
            abs_ = [a.strip().strip("`") for a in re.split(r"[,;]", str(r.get("артборды") or "")) if a.strip()]
            out[unit] = {"artboards": [a for a in abs_ if a and not L.is_empty(a)],
                         "verdict": L.cell(r.get("вердикт")), "by": L.cell(r.get("одобрил")),
                         "date": L.cell(r.get("дата")), "fingerprint": L.cell(r.get("отпечаток")),
                         "open": L.cell(r.get("открыто"))}
        return out

    def fingerprint(self, unit, artboards):
        """Отпечаток одобрения единицы: sha256 строк «артборды:<отпечаток её артбордов>» и «источники:<отпечаток
        источников единицы>»; нет артборда или единицы — None."""
        if not artboards:
            return None
        proj = self.dsurf("canvas-project")
        paths = [proj / a for a in artboards]
        if any(not p.is_file() for p in paths):
            return None
        if unit not in self._src:
            self._src[unit] = mod("canvas_input").unit_fingerprint(self.slug, self.surface, unit, self.repo)
        if self._src[unit] is None:
            return None
        lines = (f"артборды:{mod('dc_to_html').fingerprint(paths)}", f"источники:{self._src[unit]}")
        return "sha256:" + hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()

    def jump_note(self):
        return docpaths.root(self.repo).joinpath(*STATE, self.slug, "design", self.surface, "_phase-jump.md")

    def skipped(self, unit, units):
        """Решение заказчика «макет пропущен» в заметке пропусков поверхности: строка называет единицу или ни одну."""
        p = self.jump_note()
        if not p.is_file():
            return False
        for line in p.read_text(encoding="utf-8").splitlines():
            if not SKIP_LINE.search(line):
                continue
            named = [u for u in units if re.search(rf"(?<![\w-]){re.escape(u)}(?![\w-])", line)]
            if not named or unit in named:
                return True
        return False

    def after_build(self, page=None):
        """Пункты места «после сборки» критериев приёмки базы (`canvas_input.after_build_items`): [{id, severity,
        check}] в порядке списка — способ проверки и тяжесть пункта, у сайта условия eu и law — по основной
        юрисдикции своей страницы (`canvas_input.page_flags`, page — раздел page плана); вход холста манифест не
        читает."""
        CI = mod("canvas_input")
        if not self.surf.page:
            return CI.after_build_items("app")
        return CI.after_build_items("site", CI.page_flags(page))

    def mockup(self, unit, rev, units):
        """(вердикт для манифеста, причина блокера или None)."""
        row = rev.get(unit)
        if row is None:
            if self.skipped(unit, units):
                return "skipped", None
            return "none", "макета нет: строки в REVIEW.md и решения «макет пропущен» нет"
        verdict = row["verdict"] if row["verdict"] in ACCEPTED + ("blocked",) else "none"
        if verdict == "blocked":
            return "blocked", "вердикт blocked — есть непройденный пункт B"
        if verdict == "none":
            return "none", f"вердикт REVIEW.md «{row['verdict']}» вне формы"
        now = self.fingerprint(unit, row["artboards"])
        if now is None:
            return "none", ("одобрение не проверить: нет артбордов "
                            + (", ".join(row["artboards"]) or "в колонке «артборды»") + " или источников единицы")
        if now != row["fingerprint"]:
            return "none", "одобрение снято: отпечаток артбордов и источников единицы не совпал с REVIEW.md"
        return verdict, None

    # факты
    def facts(self):
        """(факты по id, id пробелов, демо у файла, claims_check.Facts или None). Файл есть, а claims_check его не
        загрузил (YAML не разбирается, верхний уровень — не объект, не форма фактов) — facts_unreadable: сверить факты
        нечем."""
        if self._facts is None:
            p = docpaths.facts(self.slug, repo=self.repo)
            data = load(p) if p.is_file() else None
            obj = None
            if isinstance(data, dict):
                try:
                    cc = mod("claims_check")
                    obj = cc.load_facts(str(p), cc.load_schema(), True)
                except (Exception, SystemExit):                 # noqa: BLE001 — форму фактов проверяет R-STRUCT-003
                    obj = None
            else:
                data = {}
            self.facts_unreadable = p.is_file() and obj is None

            def rows(key):
                return [x for x in (data.get(key) if isinstance(data.get(key), list) else [])
                        if isinstance(x, dict) and isinstance(x.get("id"), str)]
            self._facts = ({f["id"]: f for f in rows("facts")}, {m["id"] for m in rows("missing")},
                           bool(data.get("example")), obj)
        return self._facts

    def fact_problems(self, refs, named=frozenset(), targets=frozenset()):
        """Ссылки fact:/missing: единицы → ([непубликуемые или нет], [демо]). К непубликуемым идёт и факт с machine не
        по форме или не из canonical (`claims_check.machine_issues`, error), значение которого берёт страница: она
        называет факт (refs и named — id фактов страницы, `canvas_input.page_fact_ids`), на него ведёт цель
        messenger:<fact-id> или его machine стоит литералом цели (targets — значения целей) — «tel:<номер>»,
        «mailto:<почта>», адрес ссылки. Факт узнаётся и по id из aliases. Проверка, которой нечем сверять, готовой
        единицу не называет: файл фактов не читается (facts_unreadable) — «файл фактов не читается» у единицы, которая
        берёт факты; сверка упала на записи факта — «запись факта не читается»."""
        facts, missing, demo_file, obj = self.facts()
        if self.facts_unreadable:
            takes = refs or named or any(re.match(r"(?:messenger|tel|mailto|https?):", t) for t in targets)
            return (["файл фактов не читается"] if takes else []), []
        bad, demo = [], []
        for kind, fid in sorted(refs):
            if kind == "missing":
                if fid not in missing:
                    bad.append(f"missing:{fid} (пробел не назван)")
                continue
            f = facts.get(fid)
            if f is None:
                bad.append(f"fact:{fid} (нет в facts.yaml)")
                continue
            if demo_file or f.get("example"):
                demo.append(fid)
            if obj is not None:
                try:
                    issues = mod("claims_check").publishable_issues(f, obj, self.today)
                except Exception:                           # noqa: BLE001 — форму фактов проверяет R-STRUCT-003
                    issues = [("error", "", "запись факта не читается", "")]
                if any(lv == "error" for lv, *_ in issues):
                    bad.append(f"fact:{fid} ({'; '.join(m for lv, _r, m, _f in issues if lv == 'error')[:120]})")
        if obj is not None:
            cc, jur = mod("claims_check"), obj.data.get("jurisdiction") or "ru"
            named = set(named) | {fid for kind, fid in refs if kind == "fact"}
            named |= {t[len("messenger:"):] for t in targets if t.startswith("messenger:")}
            literals = {t.removeprefix("tel:").removeprefix("mailto:") for t in targets}
            for fid in sorted(k for k, f in facts.items() if isinstance(k, str) and "machine" in f):
                m = facts[fid]["machine"]
                value = m.get("value") if isinstance(m, dict) else None
                ids = {fid, *(str(a) for a in facts[fid].get("aliases") or [])}
                if not (ids & named or isinstance(value, str) and value in literals):
                    continue
                try:
                    issues = cc.machine_issues(facts[fid], jur)
                except Exception:                           # noqa: BLE001 — форму фактов проверяет R-STRUCT-003
                    issues = [("error", "запись факта не читается", "")]
                bad += [f"fact:{fid} ({msg[:120]})" for lv, msg, _fix in issues if lv == "error"]
        return bad, demo

    # сайт
    def site_units(self):
        plans_dir = docpaths.site(self.slug, self.surface, "plans", repo=self.repo)
        plans = {}
        for p in sorted(plans_dir.glob("*.yaml")) if plans_dir.is_dir() else []:
            d = load(p)
            pid = str(get(d, "page", "id", default=p.stem) or p.stem)
            plans[pid] = (p, d if isinstance(d, dict) else {})
        order = []
        smap = load(docpaths.site(self.slug, self.surface, "site-map", repo=self.repo))
        self.header_cta = str(get(smap, "chrome", "header", "utilities", "cta", "target", default="") or "")
        for x in (smap or {}).get("build_order") or [] if isinstance(smap, dict) else []:
            x = x.get("id") if isinstance(x, dict) else x
            if isinstance(x, str) and x in plans and x not in order:
                order.append(x)
        brief = load(docpaths.site(self.slug, self.surface, "brief", repo=self.repo))
        for x in get(brief, "pages", "list", default=[]) or []:
            x = x.get("id") if isinstance(x, dict) else None
            if x in plans and x not in order:
                order.append(x)
        order += [x for x in sorted(plans) if x not in order]
        return [(x,) + plans[x] for x in order], brief if isinstance(brief, dict) else {}

    def deck_page(self, pid):
        p = docpaths.site(self.slug, self.surface, "copy", f"{pid}.yaml", repo=self.repo)
        d = load(p)
        for pg in get(d, "copy_deck", "pages", default=[]) or []:
            if isinstance(pg, dict) and pg.get("page_id") == pid:
                return p, pg
        return (p if p.is_file() else None), None

    @staticmethod
    def chosen_texts(page):
        """[(место, текст, fact_ids)] выбранных вариантов страницы copy deck: вариант `chosen`, у слота без `chosen` —
        его единственный вариант (`copydeck.chosen_variant` — то же правило, что читает код)."""
        out = []
        for key, val in (get(page, "meta") or {}).items() if isinstance(get(page, "meta"), dict) else []:
            if isinstance(val, str):
                out.append((f"meta/{key}", val, []))
        for s in page.get("sections") or []:
            for sl in s.get("slots") or [] if isinstance(s, dict) else []:
                if not isinstance(sl, dict):
                    continue
                var = mod("copydeck").chosen_variant(sl)
                if var is not None:
                    out.append((f"{s.get('section_id')}/{sl.get('slot_id')}", str(var.get("text") or ""),
                                list(sl.get("fact_ids") or []) + list(var.get("fact_ids") or [])))
        mf = get(page, "meta", "fact_ids")
        if isinstance(mf, list):
            out.append(("meta", "", mf))
        return out

    @staticmethod
    def target_values(plan):
        """Значения целей действий плана: target action-слотов секций и overlays и page.cta_target."""
        out = set()

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in ("target", "cta_target") and isinstance(v, dict):
                        out.add(str(v.get("value") or ""))
                    else:
                        walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(plan)
        return out

    @staticmethod
    def plan_fact_refs(plan):
        refs = set()
        for s in plan.get("sections") or []:
            for sl in get(s, "slots", "data", default=[]) or [] if isinstance(s, dict) else []:
                for ref in [sl.get("fact")] + list(sl.get("facts") or []) if isinstance(sl, dict) else []:
                    m = re.match(r"^(fact|missing):([a-z0-9][a-z0-9_-]*)$", str(ref or ""))
                    if m:
                        refs.add((m.group(1), m.group(2)))
        return refs

    def surface_open(self):
        """Группа «поверхность» не закрыта: [«бриф <статус>», «карта <статус>»] — у брифа и у рода site карты статус не
        approved или файла нет; у кабинета группы нет — []."""
        if not self.surf.page:
            return []
        out = []
        for word, kind in [("бриф", "brief")] + ([("карта", "site-map")] if self.surf.web_kind == "site" else []):
            p = docpaths.site(self.slug, self.surface, kind, repo=self.repo)
            st = docpaths.status(p) if p.is_file() else None
            if st != "approved":
                out.append(f"{word} {st or 'нет'}")
        return out

    def site(self):
        units, brief = self.site_units()
        rev = self.review()
        ds = self.ds_status
        self.surf_open = self.surface_open()
        ids = [u[0] for u in units]
        out = []
        for pid, path, plan in units:
            why = []
            comp = docpaths.status(path) or "draft"
            if comp != "approved":
                why.append(f"план {comp}")
            deck_path, page = self.deck_page(pid)
            texts = str(page.get("status") or "draft") if page else "none"
            if texts != "approved":
                why.append("текстов нет" if texts == "none" else f"тексты {texts}")
            verdict, mwhy = self.mockup(pid, rev, ids)
            if mwhy:
                why.append(mwhy)
            refs = self.plan_fact_refs(plan)
            opened = []
            for where, text, fids in self.chosen_texts(page) if page else []:
                refs |= {("fact", f) for f in fids if isinstance(f, str)}
                if "[PLACEHOLDER" in text:
                    opened.append(f"[PLACEHOLDER]: {where}")
            bad, demo = self.fact_problems(refs, mod("canvas_input").page_fact_ids(plan, page),
                                           self.target_values(plan) | {self.header_cta})
            if bad:
                why.append("факты: " + ", ".join(bad[:4]) + (f" и ещё {len(bad) - 4}" if len(bad) > 4 else ""))
            opened += [f"демо-факт: {x}" for x in sorted(set(demo))]
            opened += [f"демо-кадр: {x}" for x in self.demo_slots(pid)] + self.fonts_open + self.theme_open
            decide = [] if ds == "approved" else [f"ДС не утверждена (system.yaml {ds or 'нет'})"]
            decide += [line for line, scope in self.context if scope in (None, ("page", pid))]
            exc = [str(e.get("id")) for e in get(plan, "page", "x-gate-exception", default=[]) or []
                   if isinstance(e, dict) and e.get("id")]
            out.append((self.unit(pid, not why and not self.surf_open, comp, texts, verdict,
                                  dash(get(plan, "page", "budget_profile")), exc, self.after_build(get(plan, "page")),
                                  self.open_list(opened, decide)), why))
        return out, brief

    @staticmethod
    def unit(uid, ready, comp, texts, verdict, budget, exc, after, opened):
        """Единица формы; publishable — готова, а в open только «решение заказчика: …» (заглушек, демо-фактов,
        демо-кадров, шрифтов без файла и темы брифа без темы токенов нет): такую единицу код публикует."""
        return {"id": uid, "ready": ready, "publishable": ready and all(o.startswith(DECIDE) for o in opened),
                "composition": comp, "texts": texts, "mockup": verdict, "budget_profile": budget,
                "gate_exceptions": exc, "after_build": after, "open": opened}

    def demo_slots(self, pid):
        """id слотов плана ассетов страницы с демо-кадром (расширение x-demo слота): кадр стоит на макете, в
        публикацию идёт файл слота. План есть, а не читается (не разбирается, не объект, `slots` не списком) — одна
        строка с причиной: демо-кадры сверить нечем."""
        p = self.dsurf("asset-plans") / f"{pid}.yaml"
        d = load(p)
        slots = get(d, "slots", default=[]) or []
        if p.is_file() and not (isinstance(d, dict) and isinstance(slots, list)):
            return [f"план ассетов не читается ({self.prel(p)}) — демо-кадры сверить нечем"]
        demo = mod("canvas_input").demo_files
        return [str(sl["id"]) for sl in slots if isinstance(sl, dict) and sl.get("id") and demo(sl)]

    @staticmethod
    def open_list(opened, decide):
        """Строки open единицы: заглушки, демо-кадры, демо-факты, шрифты без файла и тема брифа без темы токенов по
        алфавиту, затем по алфавиту решения заказчика (ДС, покрытие, FSD-карта, открытые источники контекста)."""
        return sorted(set(opened)) + sorted({DECIDE + d for d in decide})

    # кабинет
    def app(self):
        L, T = mod("layer"), mod("tree")
        lay = L.Layer(self.slug, self.surface, self.repo)
        trees = T.parse_layer(lay)
        comps = lay.components
        uses = T.text_uses(trees, comps)
        rows = lay.texts.rows if lay.texts.exists else {}
        rev = self.review()
        after = self.after_build()
        ds = self.ds_status
        cov, cov_err = None, None
        try:
            cov = mod("ds_coverage").coverage(self.slug, self.repo, self.surface)
        except Exception as e:                              # noqa: BLE001 — покрытие не посчитать — решение заказчика
            cov_err = (str(e).splitlines() or [type(e).__name__])[0][:120]
        fsd = self.fsd_status()
        ids = sorted(trees.screens)
        out = []
        for slug in ids:
            rec = lay.screens[slug]
            why = []
            comp = rec.status or "draft"
            if comp != "stable":
                why.append(f"экран {comp}")
            comp_recs = {slug} | set(T.composition(trees, slug)["blocks"])
            shell = str(rec.fm.get("shell") or "")
            keys = sorted({u.key for u in uses if u.parsed.record.slug in comp_recs | {shell}})
            sts = []
            opened = []
            for k in keys:
                r = rows.get(k)
                sts.append(str(r.status) if r is not None and r.status else "draft")
                if r is not None and "[PLACEHOLDER" in str(r.text or ""):
                    opened.append(f"[PLACEHOLDER]: {k}")
            known = [s for s in sts if s in TEXT_ORDER]
            texts = min(known, key=TEXT_ORDER.index) if known else ("none" if not keys else sts[0])
            if texts != "approved":
                why.append("строк текстов нет" if texts == "none" else f"тексты {texts}")
            verdict, mwhy = self.mockup(slug, rev, ids)
            if mwhy:
                why.append(mwhy)
            opened += self.fonts_open + self.theme_open
            decide = [] if ds == "approved" else [f"ДС не утверждена (system.yaml {ds or 'нет'})"]
            if cov_err:
                decide.append(f"покрытие ДС не посчитано ({cov_err})")
            elif cov is not None:
                bad = self.cov_of(cov, slug)
                if bad:
                    decide.append(f"покрытие ДС типов экрана не полное (ds_coverage: {len(bad)} — "
                                  f"{', '.join(sorted({t for _f, ts in bad for t in ts}))})")
            if fsd != "stable":
                decide.append("FSD-карты нет" if fsd == "none" else f"FSD-карта {fsd}")
            decide += [line for line, scope in self.context
                       if scope is None or scope in {("record", r) for r in comp_recs | {shell}}]
            out.append((self.unit(slug, not why, comp, texts, verdict, "—", [], [dict(a) for a in after],
                                  self.open_list(opened, decide)), why))
        return out, lay

    def cov_of(self, cov, screen):
        """Находки покрытия ДС (R-COV-005, error и warning) о типах экрана: [(находка, [типы])]. Тип находки — по ref:
        ключ карты решений (или его тип словаря по aka), расширение, компонент артефакта; карты решений нет — все типы
        экрана. Экран вне сверки покрытия (не stable) — []."""
        types = {t for t, u in (cov.uses.get(self.surface) or {}).items() if screen in u.where}
        if not types:
            return []
        by_comp = {}
        for r in cov.rows:
            if r.component:
                by_comp.setdefault(r.component, set()).add(r.use.type)
        by_ext = {i: eid for eid, (i, _e) in cov.system.extensions.items()}
        out = []
        for f in cov.rep.items:
            if f.rule != "R-COV-005" or f.severity not in ("error", "warning"):
                continue
            m = re.match(r"^system#/components/([^/]+)", f.ref)
            e = re.match(r"^system#/extensions/(\d+)", f.ref)
            c = re.match(r"^artifact#components/(.+)$", f.ref)
            if m:
                hit = {m.group(1), cov.comps.type_of(m.group(1))} & types
            elif e:
                hit = {by_ext.get(int(e.group(1)))} & types
            elif c:
                hit = by_comp.get(c.group(1), set()) & types
            else:
                hit = set(types)
            if hit:
                out.append((f, sorted(hit)))
        return out

    def fsd_status(self):
        d = docpaths.layer(self.slug, "fsd", self.surface, self.repo)
        files = sorted(d.glob("*.md")) if d.is_dir() else []
        if not files:
            return "none"
        sts = [md_rows_status(f) or "draft" for f in files]
        return "stable" if all(s == "stable" for s in sts) else "draft"

    # источники
    def source_files(self, units_extra=()):
        p = []
        sdir = docpaths.layer(self.slug, "site", self.surface, self.repo) if self.surf.page else None
        if self.surf.page:
            p += [docpaths.site(self.slug, self.surface, "brief", repo=self.repo),
                  docpaths.site(self.slug, self.surface, "site-map", repo=self.repo)]
            for sub in ("plans", "copy"):
                d = sdir / sub
                p += sorted(d.glob("*.yaml")) if d.is_dir() else []
            prod = docpaths.product_files(self.slug, repo=self.repo)
            p += prod["facts"] + [x for x in prod["voice"] if x.name == "voice.yaml"]
            p.append(docpaths.project(self.slug, "integration.md", repo=self.repo))
        else:
            folder = docpaths.layer(self.slug, "screens", self.surface, self.repo)
            p += [folder / "map.md", folder / "texts.md"]
            for sub in ("screens", "blocks", "shells"):
                d = folder / sub
                p += sorted(d.glob("*/index.md")) if d.is_dir() else []
            fsd = docpaths.layer(self.slug, "fsd", self.surface, self.repo)
            p += sorted(fsd.glob("*.md")) if fsd.is_dir() else []
            p += [self.dprod("app-brief"), self.dprod("visual-dna"),
                  docpaths.voice(self.slug, product=True, repo=self.repo)]
        p += [self.dprod(k) for k in ("tokens", "tokens-css", "design-md", "system", "brand")]
        p.append(self.dprod("assets") / "manifest.yaml")
        if self.surf.page:
            p.append(self.dsurf("art-direction"))
            md = self.dsurf("motion")
            p += sorted(md.glob("*.motion-spec.yaml")) if md.is_dir() else []
        p.append(self.dsurf("assets") / "manifest.yaml")
        p += self.canvas_sources()
        p.append(self.dsurf("review") / "REVIEW.md")
        return [x for x in dict.fromkeys(p) if x is not None and Path(x).is_file()]

    def canvas_sources(self):
        """Исходники холста принятых единиц: артборды строки «Приёмка» с вердиктом accepted или accepted_with_notes
        (`canvas/project/<Имя>.dc.html`) и их статичные копии, если собраны; имя артборда — файл без пути."""
        proj, html = self.dsurf("canvas-project"), self.dsurf("canvas-html")
        dc = mod("dc_to_html")
        out = []
        for row in self.review().values():
            if row["verdict"] not in ACCEPTED:
                continue
            for a in row["artboards"]:
                if Path(a).name != a or not a.endswith(".dc.html"):
                    continue
                out.append(proj / a)
                c = html / dc.copy_name(a)
                if c.is_file() and dc.copy_source(c.read_text(encoding="utf-8", errors="replace")) == a:
                    out.append(c)
        return out

    def lab_dirs(self):
        """Лабораторные страницы принятых приёмов сайта — папки design/<surface>/motion/lab/<id>/, которые называет
        арт-дирекция (prototype.lab_path) или ссылка спецификации движения страницы (references[].source.url):
        [(папка, статус)] по id. Статус — prototype.status у папки из арт-дирекции, у папки из спецификации — «—».
        Значение без `motion/lab/<id>` (адрес в сети) и папка, которой нет, источника не дают."""
        if not self.surf.page:
            return []
        named = {}

        def name(value, status):
            m = LAB_PATH.search(str(value or ""))
            if m:
                named.setdefault(m.group(1), status)

        proto = get(load(self.dsurf("art-direction")), "prototype")
        if isinstance(proto, dict):
            name(proto.get("lab_path"), dash(proto.get("status")))
        md = self.dsurf("motion")
        for spec in sorted(md.glob("*.motion-spec.yaml")) if md.is_dir() else []:
            for sec in get(load(spec), "sections", default=[]) or []:
                for ref in get(sec, "references", default=[]) or []:
                    name(get(ref, "source", "url"), "—")
        return [(md / "lab" / i, st) for i, st in sorted(named.items()) if (md / "lab" / i).is_dir()]

    def context_open(self, files, labs):
        """Открытые источники группы «контекст» (design README, «Что обязано быть закрыто») — строки решения
        заказчика: [(«<путь> <статус>», область)]. Контекст — всё в sources[], что не единица (планы, copy deck, факты,
        холст, REVIEW.md; у кабинета — экраны и texts.md) и не поверхность (бриф, карта), и строка поверхности в
        surface.md. Открыт — статус есть и не закрытый (CLOSED); без статуса («—»: манифесты ассетов, папка из
        спецификации) строки нет. ДС и FSD-карта — своими строками: их статус сводный. Область — None (у всех
        единиц), ("page", id) — спецификация движения страницы, ("record", slug) — блок или каркас кабинета."""
        page = self.surf.page
        layer = docpaths.layer(self.slug, "site" if page else "screens", self.surface, self.repo)
        own = [layer / "plans", layer / "copy"] if page else [layer / "screens",
                                                              docpaths.layer(self.slug, "fsd", self.surface, self.repo)]
        own += [self.dsurf("canvas-project"), self.dsurf("canvas-html")]
        skip = {self.dsurf("review") / "REVIEW.md"} | {self.dprod(k) for k in ("tokens", "tokens-css", "design-md",
                                                                               "system")}
        if page:
            skip |= {docpaths.site(self.slug, self.surface, k, repo=self.repo) for k in ("brief", "site-map")}
            skip |= set(docpaths.product_files(self.slug, repo=self.repo)["facts"])
        else:
            skip.add(layer / "texts.md")
        skip = {Path(x).resolve() for x in skip}
        own = [Path(x).resolve() for x in own]
        out = []
        if self.surf.status and self.surf.status not in CLOSED:
            out.append((f"строка {self.surface} в surface.md {self.surf.status}", None))
        for f, st in [(f, file_status(f)) for f in files] + [(d, st) for d, st in labs]:
            r = Path(f).resolve()
            if r in skip or any(o == r or o in r.parents for o in own) or st in CLOSED or st == "—":
                continue
            scope = None
            if page and r.name.endswith(".motion-spec.yaml"):
                scope = ("page", r.name[:-len(".motion-spec.yaml")])
            elif not page and r.name == "index.md" and r.parent.parent.name in ("blocks", "shells"):
                scope = ("record", r.parent.name)
            out.append((f"{self.prel(f)}{'/' if Path(f).is_dir() else ''} {st}", scope))
        return out

    def run(self):
        page = self.surf.page
        ds = self.ds_status
        files, labs = self.source_files(), self.lab_dirs()
        self.context = self.context_open(files, labs)
        if page:
            units, brief = self.site()
        else:
            units, _lay = self.app()
            brief = {}
        sources = [{"path": self.prel(f), "status": file_status(f, ds), "sha256": sha(f)} for f in files]
        sources += [{"path": self.prel(d) + "/", "status": st, "sha256": dir_sha(d)} for d, st in labs]
        sources.sort(key=lambda s: s["path"])
        ready = [u for u, _ in units if u["ready"]]
        status = "ready" if units and len(ready) == len(units) else ("partial" if ready else "not-ready")
        blockers = []
        if not units:
            blockers.append("единиц нет: " + ("планов страниц нет" if page else "экранов нет"))
        if self.surf_open:
            blockers.append("поверхность: " + ", ".join(self.surf_open))
        for u, why in units:
            blockers += [f"{u['id']}: {w}" for w in why]
        if page:
            amb = brief.get("ambition") if isinstance(brief.get("ambition"), dict) else {}
            level = amb.get("level")
            cap = amb.get("motion_cap") or self.level_motion(level)
            fd = {"surface": self.surf.web_kind, "ambition": dash(level), "motion_cap": dash(cap),
                  "app_screens": "—"}
        else:
            fd = {"surface": self.surf.web_kind if self.surf.type == "web" else self.surf.type, "ambition": "—",
                  "motion_cap": "—", "app_screens": C25}
        self.data = {"skill_version": kbpaths.skill_version() or "—", "surface": self.surface, "type": self.surf.type,
                     "web_kind": self.surf.web_kind if self.surf.type == "web" and self.surf.web_kind else "—",
                     "consumer": CONSUMER["page" if page else "app"], "status": status, "sources": sources,
                     "units": [u for u, _ in units], "perf": "plans" if page else dict(PERF_APP),
                     "frontend_design": fd, "blockers": blockers}
        return self

    @staticmethod
    def level_motion(level):
        if not level:
            return None
        lv = load(kbpaths.kb("creative", "01-creative-direction", "ambition-levels.yaml"))
        for row in (lv or {}).get("levels") or []:
            if isinstance(row, dict) and row.get("id") == level:
                return get(row, "maps_to", "claude_design", "motion_level")
        return None


def build(slug, surf, repo=None, today=None):
    """Манифест поверхности в памяти → словарь формы."""
    return Build(slug, surf, repo, today).run().data


# ------------------------------------------------------------------ запись и форма

def _flow(v):
    s = yaml_mod().safe_dump(v, default_flow_style=True, allow_unicode=True, sort_keys=False, width=10 ** 6).strip()
    return s[:-4].strip() if s.endswith("\n...") else (s[:-3].strip() if s.endswith("...") else s)


def render(slug, data):
    """Текст ready.yaml: ключи — в порядке формы, источник и пункт after_build — строкой, прочие списки — в строку."""
    out = [h.format(slug=slug, surface=data["surface"]) for h in HEADER] + [""]
    for k in ("skill_version", "surface", "type", "web_kind", "consumer", "status"):
        out.append(f"{k}: {_flow(data[k])}")
    out.append("")
    out.append("sources:" + ("" if data["sources"] else " []"))
    out += [f"  - {_flow(s)}" for s in data["sources"]]
    out.append("")
    out.append("units:" + ("" if data["units"] else " []"))
    for u in data["units"]:
        out.append(f"  - id: {_flow(u['id'])}")
        for k in UNIT_KEYS[1:]:
            if k == "after_build" and u[k]:
                out.append(f"    {k}:")
                out += [f"      - {_flow(a)}" for a in u[k]]
            else:
                out.append(f"    {k}: {_flow(u[k])}")
    out.append("")
    out.append(f"perf: {_flow(data['perf'])}")
    out.append(f"frontend_design: {_flow(data['frontend_design'])}")
    out.append("blockers:" + ("" if data["blockers"] else " []"))
    out += [f"  - {_flow(b)}" for b in data["blockers"]]
    return "\n".join(out) + "\n"


def form_errors(data):
    """Форма ready.yaml (R-STRUCT-008): [(JSON Pointer, сообщение, тяжесть)] — нет ключа или значение вне перечня —
    error; ключ вне формы — warning; `example` — пометка иллюстрации, не ключ формы. Манифест без skill_version —
    форма другой версии скилла: поштучных замечаний нет, его называет одна находка R-FRESH-006 (`check_surface`)."""
    out = []
    if not isinstance(data, dict):
        return [("", "ready.yaml — не словарь формы", "error")]
    if "skill_version" not in data:
        return []
    for k in FORM_KEYS:
        if k not in data:
            out.append((f"/{k}", f"нет ключа {k}", "error"))
    for k in data:
        if k not in FORM_KEYS and k != "example":
            out.append((f"/{k}", f"ключ {k} вне формы", "warning"))
    if "skill_version" in data and not (isinstance(data["skill_version"], str) and data["skill_version"].strip()):
        out.append(("/skill_version", "skill_version — строка версии скилла (файл VERSION)", "error"))
    if "status" in data and data["status"] not in ("ready", "partial", "not-ready"):
        out.append(("/status", f"status «{data['status']}» — ready · partial · not-ready", "error"))
    if "consumer" in data and data["consumer"] not in CONSUMER.values():
        out.append(("/consumer", f"consumer «{data['consumer']}» — {' · '.join(CONSUMER.values())}", "error"))
    if "web_kind" in data and data["web_kind"] not in ("landing", "site", "app", "—"):
        out.append(("/web_kind", f"web_kind «{data['web_kind']}» — landing · site · app · —", "error"))
    for i, s in enumerate(data.get("sources") or [] if isinstance(data.get("sources"), list) else []):
        if not (isinstance(s, dict) and all(k in s for k in ("path", "status", "sha256"))):
            out.append((f"/sources/{i}", "источник — {path, status, sha256}", "error"))
    if "sources" in data and not isinstance(data["sources"], list):
        out.append(("/sources", "sources — список", "error"))
    units = data.get("units")
    if "units" in data and not isinstance(units, list):
        out.append(("/units", "units — список", "error"))
    for i, u in enumerate(units if isinstance(units, list) else []):
        if not isinstance(u, dict):
            out.append((f"/units/{i}", "единица — словарь формы", "error"))
            continue
        for k in UNIT_KEYS:
            if k not in u:
                out.append((f"/units/{i}/{k}", f"у единицы {u.get('id', i)} нет ключа {k}", "error"))
        for k in u:
            if k not in UNIT_KEYS:
                out.append((f"/units/{i}/{k}", f"ключ единицы {k} вне формы", "warning"))
        if "mockup" in u and u["mockup"] not in VERDICTS:
            out.append((f"/units/{i}/mockup", f"mockup «{u['mockup']}» — {' · '.join(VERDICTS)}", "error"))
        for k in ("ready", "publishable"):
            if k in u and not isinstance(u[k], bool):
                out.append((f"/units/{i}/{k}", f"{k} — true или false", "error"))
        ab = u.get("after_build")
        if "after_build" in u and not (isinstance(ab, list) and all(
                isinstance(a, dict) and set(a) == {"id", "severity", "check"} and a["severity"] in ("B", "S", "D")
                and mod("canvas_input").check_form(a["check"]) is None for a in ab)):
            out.append((f"/units/{i}/after_build", f"after_build единицы {u.get('id', i)} — пункты {{id, severity, "
                        "check}: тяжесть B · S · D, способ — {gates}, {tool, field, pass}, code или manual", "error"))
    fd = data.get("frontend_design")
    if "frontend_design" in data:
        if not isinstance(fd, dict):
            out.append(("/frontend_design", "frontend_design — {surface, ambition, motion_cap, app_screens}", "error"))
        else:
            out += [(f"/frontend_design/{k}", f"нет ключа frontend_design.{k}", "error") for k in FD_KEYS
                    if k not in fd]
    if "blockers" in data and not isinstance(data["blockers"], list):
        out.append(("/blockers", "blockers — список строк", "error"))
    return out


def _ab_diff(old, new):
    """id пунктов after_build, которые на диске и в сборке разные: нет, лишний, другие тяжесть или способ."""
    om = {a.get("id"): a for a in old if isinstance(a, dict)} if isinstance(old, list) else {}
    nm = {a["id"]: a for a in new}
    return ", ".join(i for i in dict.fromkeys(list(nm) + list(om)) if om.get(i) != nm.get(i)) or "(форма)"


def _diff(old, new):
    """Расхождения манифеста на диске и сборки — строки для сообщения. skill_version не сравнивается: смена версии
    скилла без смены содержания манифест не устаревает."""
    out = []
    old = {k: v for k, v in (old or {}).items() if k != "example"}
    for k in FORM_KEYS[1:]:
        a, b = old.get(k), new.get(k)
        if a == b:
            continue
        if k == "sources" and isinstance(a, list):
            am = {s.get("path"): s for s in a if isinstance(s, dict)}
            bm = {s["path"]: s for s in b}
            for p in sorted(set(am) | set(bm)):
                if p not in bm:
                    out.append(f"источник {p} больше не читается")
                elif p not in am:
                    out.append(f"новый источник {p}")
                elif am[p] != bm[p]:
                    what = ", ".join(x for x in ("status", "sha256") if am[p].get(x) != bm[p].get(x)) or "поля"
                    out.append(f"источник {p}: {what} не совпадает с файлом")
        elif k == "units" and isinstance(a, list):
            am = {u.get("id"): u for u in a if isinstance(u, dict)}
            bm = {u["id"]: u for u in b}
            for i in list(dict.fromkeys(list(bm) + list(am))):
                if i not in bm:
                    out.append(f"единицы {i} больше нет")
                elif i not in am:
                    out.append(f"новая единица {i}")
                elif am[i] != bm[i]:
                    for f in UNIT_KEYS[1:]:
                        if am[i].get(f) == bm[i].get(f):
                            continue
                        if f == "after_build":
                            out.append(f"{i}.after_build: не равны сборке пункты {_ab_diff(am[i].get(f), bm[i][f])}")
                        else:
                            out.append(f"{i}.{f}: {_flow(am[i].get(f))} → {_flow(bm[i].get(f))}")
        else:
            out.append(f"{k}: {_flow(a)} → {_flow(b)}")
    return out


def check_surface(slug, surf, repo=None, today=None):
    """Находки R-FRESH-006 одной поверхности: манифест на диске против сборки; файла нет — []. Манифест без
    skill_version — форма другой версии скилла: одна находка с порядком пересборки (вход холста, затем манифест), без
    сверки по полям."""
    r = docpaths.root(repo)
    p = docpaths.design(slug, "ready", surface=surf.slug, repo=r)
    if not p.is_file():
        return []
    rep = F.Report()
    tail = (f"ready build {slug} {surf.slug} — на этапе package, после аудита: design_audit check на переходе, скилл "
            "/design-audit — перед коммитом")
    kw = dict(surface=surf.slug, kind=KIND, ref=surf.slug, path=docpaths.rel(p, r))
    try:
        old = yaml_mod().safe_load(p.read_text(encoding="utf-8"))
    except Exception as e:                                  # noqa: BLE001
        rep.add(RULE, "error", message=f"ready.yaml не разбирается: {str(e).splitlines()[0][:120]}", fix=tail, **kw)
        return rep.items
    if isinstance(old, dict) and "skill_version" not in old:
        inp = docpaths.design(slug, "input", surface=surf.slug, repo=r) / "INPUT.md"
        stage = (mod("canvas_input").read_manifest(inp)[0] or {}).get("stage") if inp.is_file() else None
        fix = (f"пересобрать вход холста и манифест: canvas_input build {slug} {surf.slug} --stage {stage}, затем "
               if stage else "пересобрать манифест: ") + tail
        rep.add(RULE, "error", message="манифест готовности не по форме этой версии скилла: нет skill_version — форма "
                "единиц и пунктов after_build другой версии", fix=fix, **kw)
        return rep.items
    kw["fix"] = tail
    new = build(slug, surf, r, today)
    diff = _diff(old if isinstance(old, dict) else {}, new)
    if diff:
        more = f" и ещё {len(diff) - 5}" if len(diff) > 5 else ""
        rep.add(RULE, "error", message="манифест готовности отстал от источников: " + "; ".join(diff[:5]) + more,
                **kw)
    return rep.items


def show_units(slug, surf, repo=None, today=None):
    """Единицы с отпечатками одобрения (артборды строки «Приёмка» и источники единицы): [{id, composition, texts,
    verdict, artboards, review, current, match}]."""
    b = Build(slug, surf, repo, today)
    rev = b.review()
    data = b.run().data
    out = []
    for u in data["units"]:
        row = rev.get(u["id"]) or {}
        cur = b.fingerprint(u["id"], row.get("artboards") or [])
        out.append({"id": u["id"], "composition": u["composition"], "texts": u["texts"],
                    "verdict": row.get("verdict") or "—", "artboards": row.get("artboards") or [],
                    "review": row.get("fingerprint") or "—", "current": cur or "—",
                    "match": bool(cur and cur == row.get("fingerprint")), "mockup": u["mockup"]})
    return out


# ------------------------------------------------------------------ вызов

def _today(ap, s):
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        ap.error("--today: ГГГГ-ММ-ДД")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    _reexec_venv()
    if "--selftest" in argv:
        return _selftest()
    ap = docpaths.parser(TOOL, __doc__, commands=("build", "check", "show"), surface="optional",
                         accept=lambda s: s.design and (s.page or s.app))
    ap.add_argument("--today", metavar="ГГГГ-ММ-ДД", help="дата для сроков фактов (по умолчанию сегодня)")
    call = docpaths.parse(ap, argv)
    today = _today(ap, call.args.today)
    if call.command in ("build", "show") and call.surf is None:
        ap.error(f"{call.command}: нужна поверхность — {call.command} <slug> <surface>")
    try:
        if call.command == "check":
            surfs = [call.surf] if call.surf else [s for s in call.surfaces if s.design and (s.page or s.app)]
            items = []
            for s in surfs:
                items += check_surface(call.slug, s, call.repo, today)
            F.print_findings(items, as_json=call.json)
            return F.exit_code(items)
        if call.command == "show":
            rows = show_units(call.slug, call.surf, call.repo, today)
            if call.json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            else:
                for r in rows:
                    mark = "совпал" if r["match"] else ("нет одобрения" if r["review"] == "—" else "не совпал")
                    print(f"{r['id']:<22} {r['composition']:<9} тексты {r['texts']:<9} макет {r['mockup']:<20} "
                          f"{mark}")
                    boards = ", ".join(r["artboards"]) or "— (колонка «артборды» строки «Приёмка»)"
                    print(f"{'':<22} артборды: {boards}")
                    print(f"{'':<22} отпечаток одобрения сейчас: {r['current']}")
            return F.EXIT_OK
        data = build(call.slug, call.surf, call.repo, today)
        text = render(call.slug, data)
        dest = (call.out / FILE) if call.out is not None else docpaths.design(call.slug, "ready",
                                                                             surface=call.surface, repo=call.repo)
        dest.parent.mkdir(parents=True, exist_ok=True)
        old = dest.read_text(encoding="utf-8") if dest.is_file() else None
        if old != text:
            dest.write_text(text, encoding="utf-8")
        if call.json:
            print(json.dumps(data, ensure_ascii=False, indent=1))
        else:
            n = len(data["units"])
            print(f"{docpaths.rel(dest, call.repo)} — {'записан' if old != text else 'без изменений'}: "
                  f"{data['status']}, единиц {n}, готовы {sum(1 for u in data['units'] if u['ready'])}, "
                  f"публикуемы {sum(1 for u in data['units'] if u['publishable'])}, "
                  f"источников {len(data['sources'])}")
            for b in data["blockers"][:12]:
                print(f"  блокер: {b}")
            if len(data["blockers"]) > 12:
                print(f"  … и ещё {len(data['blockers']) - 12}")
            decide = {}
            for u in data["units"]:
                for o in u["open"]:
                    if o.startswith(DECIDE):
                        decide.setdefault(o[len(DECIDE):], []).append(u["id"])
            for what, ids in decide.items():
                print(f"  {DECIDE}{what} — {', '.join(ids)}")
        return F.EXIT_OK
    except (F.ToolError, docpaths.DocPathError, OSError) as e:
        print(f"{TOOL}: {e}", file=sys.stderr)
        return F.EXIT_USAGE


def _selftest():
    """Фикстуры package-landing и input-landing (лендинг), input-site (многостраничник) и package-cabinet (кабинет)
    сборщика fixture_project, без сети."""
    import shutil
    import subprocess
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)

    me = str(Path(__file__).resolve())
    kbpaths.use("tests")
    import fixture_project
    today = dt.date.fromisoformat(fixture_project.today())    # опорная дата фикстур: ключ today данных сверки

    def cli(*args, cwd):
        return subprocess.run([sys.executable, me, *map(str, args)], cwd=cwd, capture_output=True, text=True)

    with fixture_project.built("package-landing") as fx, tempfile.TemporaryDirectory(prefix="ddd-ready-cwd-") as cwd:
        root, slug = fx.root, fx.slug
        surf = docpaths.surface(slug, "promo", root)
        r = cli("build", slug, "promo", "--repo", root, "--today", today.isoformat(), cwd=cwd)
        path = docpaths.design(slug, "ready", surface="promo", repo=root)
        check("build из чужой рабочей папки с --repo — код 0, файл design/promo/ready.yaml записан",
              r.returncode == 0 and path.is_file())
        data = yaml_mod().safe_load(path.read_text(encoding="utf-8"))
        check("лендинг: type web, web_kind landing, consumer <org>/site, perf plans",
              (data["type"], data["web_kind"], data["consumer"], data["perf"]) == ("web", "landing", "<org>/site",
                                                                                   "plans"))
        check("единицы — страницы планов (home, spasibo), budget_profile — из планов",
              [u["id"] for u in data["units"]] == ["home", "spasibo"]
              and [u["budget_profile"] for u in data["units"]] == ["landing-lead-services@L1", "thank-you-page@L0"])
        check("frontend_design лендинга: surface landing, ambition L1, motion_cap expressive (уровень движения L1)",
              data["frontend_design"] == {"surface": "landing", "ambition": "L1", "motion_cap": "expressive",
                                          "app_screens": "—"})
        check("источники — путь от папки проекта, статус и sha256 файла",
              any(s["path"] == "site/promo/plans/spasibo.yaml" and s["status"] == "approved"
                  and s["sha256"] == sha(docpaths.site(slug, "promo", "plans", "spasibo.yaml", repo=root))
                  for s in data["sources"]))
        check("status not-ready: макета нет — блокеры называют единицы",
              data["status"] == "not-ready" and any(b.startswith("spasibo: макета нет") for b in data["blockers"]))
        check("форма ready.yaml (R-STRUCT-008) — без замечаний", not form_errors(data))
        hm, sp = ({u["id"]: u for u in data["units"]}[i] for i in ("home", "spasibo"))
        common = {DECIDE + x for x in ("design/brand.yaml none", "design/promo/art-direction.json proposed",
                                       "voice.yaml draft", "строка promo в surface.md draft")}
        check("контекст: открытые источники вне единицы и поверхности — строки «решение заказчика: <путь> <статус>» у "
              "каждой единицы (бренд none, арт-дирекция proposed, голос draft, строка поверхности draft); спецификация "
              "движения home — только у home; бриф, планы, copy deck и факты строк решения не дают",
              common <= set(hm["open"]) and common <= set(sp["open"])
              and f"{DECIDE}design/promo/motion/home.motion-spec.yaml proposed" in hm["open"]
              and not any("motion-spec" in o for o in sp["open"])
              and not any(x in o for o in hm["open"] + sp["open"] for x in ("site-brief", "plans/", "copy/", "facts")))
        check("skill_version — версия скилла (VERSION); поверхность лендинга не закрыта (бриф proposed) — блокер "
              "«поверхность: бриф proposed»; не готовая единица — publishable false",
              data["skill_version"] == kbpaths.skill_version() and "поверхность: бриф proposed" in data["blockers"]
              and not any(u["publishable"] for u in data["units"]))
        r = cli("check", slug, "--repo", root, "--today", today.isoformat(), "--json", cwd=cwd)
        check("check сразу после build — код 0, находок нет", r.returncode == 0 and not F.parse_lines(r.stdout))
        text = path.read_text(encoding="utf-8")
        r = cli("build", slug, "promo", "--repo", root, "--today", today.isoformat(), cwd=cwd)
        check("повторная сборка — те же байты («без изменений»)",
              path.read_text(encoding="utf-8") == text and "без изменений" in r.stdout)
        path.write_text(text.replace("surface: promo\n", "example: true\nsurface: promo\n"), encoding="utf-8")
        check("пометка иллюстрации example: true — не расхождение и не ключ вне формы",
              not check_surface(slug, surf, root, today)
              and not form_errors(yaml_mod().safe_load(path.read_text(encoding="utf-8"))))
        path.write_text(text.replace(f"skill_version: {data['skill_version']}\n", "skill_version: 0.0.1\n"),
                        encoding="utf-8")
        check("check не сравнивает skill_version: другая версия при том же содержании — находок нет",
              "skill_version: 0.0.1\n" in path.read_text(encoding="utf-8") and not check_surface(slug, surf, root, today))
        path.write_text(text, encoding="utf-8")
        plan = docpaths.site(slug, "promo", "plans", "spasibo.yaml", repo=root)
        ptext = plan.read_text(encoding="utf-8")
        plan.write_text(ptext.replace("goal: подтвердить заявку", "goal: подтвердить заявку на замер"),
                        encoding="utf-8")
        items = check_surface(slug, surf, root, today)
        check("правка источника без build → R-FRESH-006 error с путём манифеста и источником в сообщении",
              len(items) == 1 and items[0].rule == RULE and items[0].severity == "error"
              and items[0].path == docpaths.rel(path, root) and "site/promo/plans/spasibo.yaml" in items[0].message)
        check("совет R-FRESH-006: пересборка на этапе package после аудита — design_audit check на переходе, скилл "
              "/design-audit — перед коммитом",
              items and "на этапе package" in items[0].fix and "design_audit check на переходе" in items[0].fix
              and "/design-audit — перед коммитом" in items[0].fix and "без error" not in items[0].fix)
        plan.write_text(ptext, encoding="utf-8")
        bad = dict(data, status="done", skill_version="", units=[dict(data["units"][0], mockup="ok", extra=1,
                                                                      publishable="да")])
        bad.pop("blockers")
        errs = form_errors(bad)
        check("форма: нет ключа (blockers), пустая skill_version и значение вне перечня (status, mockup, publishable не "
              "bool) — error, ключ вне формы — warning",
              all(any(p == x and s == "error" for p, _m, s in errs)
                  for x in ("/blockers", "/skill_version", "/status", "/units/0/mockup", "/units/0/publishable"))
              and any(p == "/units/0/extra" and s == "warning" for p, _m, s in errs))
        older = {k: v for k, v in bad.items() if k != "skill_version"}
        path.write_text(text.replace(f"skill_version: {data['skill_version']}\n", ""), encoding="utf-8")
        items = check_surface(slug, surf, root, today)
        check("манифест без skill_version — форма другой версии скилла: одна находка R-FRESH-006 с советом пересборки "
              "(входа нет — ready build), поштучных замечаний формы нет",
              not form_errors(older) and len(items) == 1 and items[0].rule == RULE and "skill_version" in
              items[0].message and items[0].fix.startswith(f"пересобрать манифест: ready build {slug} promo"))
        path.write_text(text, encoding="utf-8")
        ab = {u["id"]: {a["id"]: a["severity"] for a in u["after_build"]} for u in data["units"]}
        sp_plan = docpaths.site(slug, "promo", "plans", "spasibo.yaml", repo=root)
        sp_text = sp_plan.read_text(encoding="utf-8")
        sp_plan.write_text(sp_text.replace("  jurisdiction:\n  - ru\n", "  jurisdiction:\n  - eu\n  - ru\n"),
                           encoding="utf-8")
        eu = {u["id"]: {a["id"]: a["severity"] for a in u["after_build"]} for u in build(slug, surf, root, today)["units"]}
        sp_plan.write_text(sp_text.replace("  jurisdiction:\n  - ru\n", "  jurisdiction:\n  - kz\n  - ru\n"),
                           encoding="utf-8")
        kz = {u["id"]: {a["id"]: a["severity"] for a in u["after_build"]} for u in build(slug, surf, root, today)["units"]}
        sp_plan.write_text(sp_text, encoding="utf-8")
        check("after_build без входа холста — пункты критериев приёмки «после сборки» у каждой единицы (F2 B, K1 B, I6 "
              "S); J4b и L3 — по основной юрисдикции своей страницы: ru — S, у spasibo с [eu, ru] — B, у home — S; у "
              "spasibo с [kz, ru] (вне права базы) — пунктов J4b и L3 нет",
              ab["home"] == ab["spasibo"] and {"F2", "K1", "J4b", "L3", "D5"} <= set(ab["home"])
              and ab["home"]["F2"] == ab["home"]["K1"] == "B" and ab["home"]["I6"] == "S"
              and ab["home"]["J4b"] == ab["home"]["L3"] == "S" and eu["spasibo"]["J4b"] == eu["spasibo"]["L3"] == "B"
              and eu["home"]["J4b"] == "S" and kz["home"] == ab["home"]
              and kz["spasibo"] == {k: v for k, v in ab["spasibo"].items() if k not in ("J4b", "L3")})
        # лабораторная страница приёма — источник-папка манифеста
        lab_row = "design/promo/motion/lab/mask-reveal/"
        adp = docpaths.design(slug, "art-direction", surface="promo", repo=root)
        adt = adp.read_text(encoding="utf-8")
        ad = json.loads(adt)
        ad["prototype"] = {"status": "built", "lab_path": lab_row}
        adp.write_text(json.dumps(ad, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        no_dir = build(slug, surf, root, today)
        lab = docpaths.design(slug, "motion", surface="promo", repo=root) / "lab" / "mask-reveal"
        (lab / "media").mkdir(parents=True)
        (lab / "index.html").write_text("<!doctype html><title>иллюстрация самопроверки</title>\n", encoding="utf-8")
        (lab / "media" / "take.txt").write_text("иллюстрация: запись приёма\n", encoding="utf-8")
        with_dir = build(slug, surf, root, today)
        row, lab_sha = next((s for s in with_dir["sources"] if s["path"] == lab_row), None), dir_sha(lab)
        path.write_text(render(slug, with_dir), encoding="utf-8")
        fresh = check_surface(slug, surf, root, today)
        (lab / "media" / "take.txt").write_text("иллюстрация: запись приёма, правка\n", encoding="utf-8")
        stale = check_surface(slug, surf, root, today)
        ad["prototype"]["lab_path"] = "https://example.invalid/lab/mask-reveal"
        adp.write_text(json.dumps(ad, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        by_url = build(slug, surf, root, today)
        check("лабораторная страница приёма: папка motion/lab/<id>/, которую называет prototype.lab_path арт-дирекции, "
              "— источник манифеста (путь папки, статус прототипа, отпечаток папки), форма без замечаний; правка файла "
              "папки — R-FRESH-006 с путём папки; папки нет или lab_path — адрес в сети — источника нет",
              row is not None and row["status"] == "built" and row["sha256"] == lab_sha != dir_sha(lab)
              and not form_errors(with_dir) and not fresh
              and len(stale) == 1 and stale[0].rule == RULE and f"источник {lab_row}: sha256" in stale[0].message
              and not any("/lab/" in s["path"] for s in no_dir["sources"] + by_url["sources"])
              and [s["path"] for s in no_dir["sources"]] == [s["path"] for s in data["sources"]])
        adp.write_text(adt, encoding="utf-8")
        shutil.rmtree(lab.parent)
        path.write_text(text, encoding="utf-8")
        # демо-кадры x-demo плана ассетов страницы — строки open; исключение ворот — у единицы своей страницы
        apl = docpaths.design(slug, "asset-plans", surface="promo", repo=root) / "spasibo.yaml"
        apt = apl.read_text(encoding="utf-8")
        ap = yaml_mod().safe_load(apt)
        ap.setdefault("slots", []).append({"id": "confirmation-photo", "source": "real", "x-demo": {
            "file": "$DDD_HOME/out/selftest-no-such/confirmation-photo-demo.webp", "what": "иллюстрация: кадр макета"}})
        apl.write_text(yaml_mod().safe_dump(ap, allow_unicode=True, sort_keys=False), encoding="utf-8")
        plan.write_text(ptext.replace("\npage:\n", "\npage:\n  x-gate-exception:\n  - {id: SG-DEMO, why: иллюстрация, "
                                      "who: владелец продукта}\n", 1), encoding="utf-8")
        units = {u["id"]: u for u in build(slug, surf, root, today)["units"]}
        was = {u["id"]: u for u in data["units"]}
        check("демо-кадр x-demo плана ассетов страницы — строка open «демо-кадр: <слот>» у её единицы; у соседней и "
              "без x-demo таких строк нет; исключение ворот плана — в gate_exceptions своей единицы, у соседней — []",
              "\n  x-gate-exception:" in plan.read_text(encoding="utf-8")
              and units["spasibo"]["open"] == sorted(was["spasibo"]["open"] + ["демо-кадр: confirmation-photo"],
                                                     key=lambda x: (x.startswith(DECIDE), x))
              and units["home"]["open"] == was["home"]["open"]
              and not any("демо-кадр" in o for o in was["spasibo"]["open"])
              and units["spasibo"]["gate_exceptions"] == ["SG-DEMO"] and units["home"]["gate_exceptions"] == []
              and units["spasibo"]["ready"] == was["spasibo"]["ready"])
        apl.write_text(apt, encoding="utf-8")
        plan.write_text(ptext, encoding="utf-8")
        # одобрение с отпечатком по артбордам и источникам единицы (вход собирается и с ошибкой проверки: главная в
        # работе)
        def ci(stage):
            return subprocess.run([sys.executable, str(HERE / "canvas_input.py"), "build", slug, "promo", "--stage",
                                   stage, "--repo", str(root), "--today", today.isoformat()], capture_output=True, text=True,
                                  cwd=cwd)

        ci("mockup")
        proj = docpaths.design(slug, "canvas-project", surface="promo", repo=root)
        proj.mkdir(parents=True, exist_ok=True)
        (proj / "Spasibo.dc.html").write_text("<section id='confirmation'>Заявка на замер принята</section>\n",
                                              encoding="utf-8")
        (proj / "Home.dc.html").write_text("<section id='hero'>Главная</section>\n", encoding="utf-8")
        b = Build(slug, surf, root, today)
        fp_sp, fp_home = b.fingerprint("spasibo", ["Spasibo.dc.html"]), b.fingerprint("home", ["Home.dc.html"])
        rv = docpaths.design(slug, "review", surface="promo", repo=root)
        rv.mkdir(parents=True, exist_ok=True)
        (rv / "REVIEW.md").write_text(
            "# REVIEW\n\nИллюстрация самопроверки.\n\n## Приёмка\n\n"
            "| страница или экран | артборды | вердикт | одобрил | дата | отпечаток | открыто |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| `spasibo` | `Spasibo.dc.html` | `accepted_with_notes` | владелец продукта | 2026-09-29 | {fp_sp} "
            "| — |\n"
            f"| `home` | `Home.dc.html` | `accepted` | владелец продукта | 2026-09-29 | {fp_home} | — |\n",
            encoding="utf-8")
        units = {u["id"]: u for u in build(slug, surf, root, today)["units"]}
        check("вердикт REVIEW.md с совпавшим отпечатком артбордов и источников единицы → mockup accepted_with_notes; "
              "отпечаток — sha256, у единиц разный",
              units["spasibo"]["mockup"] == "accepted_with_notes" and units["home"]["mockup"] == "accepted"
              and str(fp_sp).startswith("sha256:") and fp_sp != fp_home)
        # machine факта не из canonical: держит единицу, которая берёт его значение; одобрение макета — то же
        fy = docpaths.facts(slug, repo=root)
        ft = fy.read_text(encoding="utf-8")
        tel_ok, tel_bad = ('machine: {type: telephone, value: "+7900000000' + n + '"}' for n in "19")
        fy.write_text(ft.replace("{type: messenger, network: max,", "{type: messenger, network: telegram,"),
                      encoding="utf-8")
        d_net = build(slug, surf, root, today)
        fy.write_text(ft.replace(tel_ok, tel_bad), encoding="utf-8")
        d_tel = build(slug, surf, root, today)
        fy.write_text(ft, encoding="utf-8")
        d_fix = build(slug, surf, root, today)
        check("machine не из canonical у факта цели messenger:<fact-id> (сеть не по ссылке) — блокер «факты: …» у "
              "home, которая на него ведёт, у spasibo его нет; вердикты макета те же, после исправления machine "
              "блокера нет — новая приёмка не нужна; чужой номер в machine, которого нет в литерале цели, единицу не "
              "держит: значения machine страница не берёт",
              tel_ok in ft and "network: max," in ft
              and [b for b in d_net["blockers"] if "machine" in b and b.startswith("home: факты: fact:company-max (")]
              and not any("company-max" in b for b in d_net["blockers"] if not b.startswith("home:"))
              and all({u["id"]: u["mockup"] for u in d["units"]} == {"home": "accepted",
                                                                     "spasibo": "accepted_with_notes"}
                      for d in (d_net, d_tel, d_fix))
              and not any("machine" in b for b in d_tel["blockers"] + d_fix["blockers"]))
        html = docpaths.design(slug, "canvas-html", surface="promo", repo=root)
        html.mkdir(parents=True, exist_ok=True)
        (html / "Spasibo.html").write_text("<!doctype html><head><!-- dc_to_html: статичная копия артборда "
                                           "Spasibo.dc.html; рамка 1440×900 --></head>\n", encoding="utf-8")
        (html / "landing.html").write_text("<!doctype html><title>страница</title>\n", encoding="utf-8")
        (proj / "Draft.dc.html").write_text("<section id='hero'>Черновик</section>\n", encoding="utf-8")
        srcs = {s["path"] for s in build(slug, surf, root, today)["sources"]}
        check("источники пакета — исходники холста принятых единиц (артборды «Приёмки») и статичная копия, если "
              "собрана; HTML не копия и артборд без приёмки — не источники",
              {"design/promo/canvas/project/Spasibo.dc.html", "design/promo/canvas/project/Home.dc.html",
               "design/promo/canvas/html/Spasibo.html"} <= srcs
              and not {"design/promo/canvas/html/landing.html", "design/promo/canvas/project/Draft.dc.html"} & srcs)
        shutil.rmtree(html)
        (proj / "Draft.dc.html").unlink()
        art = docpaths.design(slug, "artifacts", repo=root)
        at = art.read_text(encoding="utf-8")
        art.write_text(at.replace("| 2026-09-29 | аналитик |", "| 2026-10-02 | аналитик |"), encoding="utf-8")
        rebuilt = ci("mockup")
        sysp = docpaths.design(slug, "system", repo=root)
        st = sysp.read_text(encoding="utf-8")
        sysp.write_text(st.replace("status: approved", "status: proposed", 1).replace("starter: []",
                                                                                     "starter: [spasibo]"),
                        encoding="utf-8")
        d = build(slug, surf, root, today)
        units = {u["id"]: u for u in d["units"]}
        check("дата «последнего чтения» в ARTIFACTS.md, пересборка входа, starter и статус system.yaml — одобрение то "
              "же; ДС не утверждена — строка open «решение заказчика», не блокер",
              at.count("| 2026-09-29 | аналитик |") == 2 and rebuilt.returncode in (0, 1)
              and "starter: [spasibo]" in sysp.read_text(encoding="utf-8")
              and units["spasibo"]["mockup"] == "accepted_with_notes" and units["home"]["mockup"] == "accepted"
              and f"{DECIDE}ДС не утверждена (system.yaml proposed)" in units["spasibo"]["open"]
              and not any("ДС" in x for x in d["blockers"]))
        mo = ci("motion")
        inp = docpaths.design(slug, "input", surface="promo", repo=root) / "INPUT.md"
        units = {u["id"]: u for u in build(slug, surf, root, today)["units"]}
        check("вход motion заменяет вход макета — одобрение то же",
              mo.returncode in (0, 1) and "stage: motion" in inp.read_text(encoding="utf-8")
              and units["spasibo"]["mockup"] == "accepted_with_notes" and units["home"]["mockup"] == "accepted")
        dk = docpaths.site(slug, "promo", "copy", "spasibo.yaml", repo=root)
        dtext = dk.read_text(encoding="utf-8")
        dk.write_text(dtext.replace("text: 'Вызвать замерщика'", "text: 'Позвать замерщика'", 1), encoding="utf-8")
        d = build(slug, surf, root, today)
        units = {u["id"]: u for u in d["units"]}
        check("правка своего текста в copy deck снимает одобрение единицы (spasibo — mockup none, блокер); правка "
              "copy deck соседней страницы одобрение home не снимает",
              "Позвать замерщика" in dk.read_text(encoding="utf-8") and units["spasibo"]["mockup"] == "none"
              and units["home"]["mockup"] == "accepted" and any("spasibo: одобрение снято" in x for x in d["blockers"]))
        dk.write_text(dtext, encoding="utf-8")
        (proj / "Spasibo.dc.html").write_text("<section id='confirmation'>Заявка принята</section>\n",
                                              encoding="utf-8")
        d = build(slug, surf, root, today)
        units = {u["id"]: u for u in d["units"]}
        check("правка артборда единицы снимает её одобрение (mockup none, блокер), соседней — нет",
              units["spasibo"]["mockup"] == "none" and units["home"]["mockup"] == "accepted"
              and any("spasibo: одобрение снято" in x for x in d["blockers"]))
        rows = show_units(slug, surf, root, today)
        check("show: у единицы — отпечаток из REVIEW.md и текущий, совпадение",
              {r["id"]: r["match"] for r in rows} == {"home": True, "spasibo": False}
              and next(r["current"] for r in rows if r["id"] == "home") == fp_home)
        note = docpaths.root(root).joinpath(*STATE, slug, "design", "promo", "_phase-jump.md")
        note.parent.mkdir(parents=True, exist_ok=True)
        (rv / "REVIEW.md").unlink()
        note.write_text("---\nkind: phase-jump\nref: docs/projects/otves-remont-nn/design/promo/\n---\n\n"
                        "## Доменные решения\n- `mockup` для `spasibo` — макет пропущен: сборка по ДС и плану.\n",
                        encoding="utf-8")
        units = {u["id"]: u for u in build(slug, surf, root, today)["units"]}
        check("решение «макет пропущен» в заметке пропусков → mockup skipped у названной единицы",
              units["spasibo"]["mockup"] == "skipped" and units["home"]["mockup"] == "none")
        # публикация: поверхность закрыта, тексты утверждены, макет пропущен решением заказчика
        bp = docpaths.site(slug, "promo", "brief", repo=root)
        btext = bp.read_text(encoding="utf-8")
        approved = dtext.replace("    status: draft\n", "    status: approved\n", 1)
        dk.write_text(approved, encoding="utf-8")
        d_open = build(slug, surf, root, today)
        bp.write_text(btext.replace("project:\n  slug: otves-remont-nn\n  status: proposed\n",
                                    "project:\n  slug: otves-remont-nn\n  status: approved\n", 1), encoding="utf-8")
        d_pub = build(slug, surf, root, today)
        # machine не из canonical, значение которого берёт готовая единица: литералом цели и ссылкой fact:<id> плана
        fy.write_text(ft.replace(tel_ok, tel_bad), encoding="utf-8")
        plan.write_text(ptext.replace("value: tel:+79000000001", "value: tel:+79000000009"), encoding="utf-8")
        d_lit = build(slug, surf, root, today)
        job = "job: логотип → главная, призыв, телефон"
        plan.write_text(ptext.replace(job, job + " — fact:company-phone"), encoding="utf-8")
        d_named = build(slug, surf, root, today)
        fy.write_text(ft, encoding="utf-8")
        d_right = build(slug, surf, root, today)
        plan.write_text(ptext, encoding="utf-8")
        s_lit, s_named, s_right = ({u["id"]: u for u in x["units"]}["spasibo"] for x in (d_lit, d_named, d_right))
        held = "spasibo: факты: fact:company-phone (fact:company-phone: machine — номера +79000000009 в canonical нет)"
        check("готовая единица с чужим номером в machine: литерал цели плана несёт этот номер — не готова, блокер "
              "«факты: fact:… (machine — …)»; план называет факт ссылкой fact:<id> вне слота данных — тот же блокер; "
              "machine из формулировки — готова",
              "value: tel:+79000000001" in ptext and ptext.count(job) == 1
              and not s_lit["ready"] and held in d_lit["blockers"]
              and not s_named["ready"] and held in d_named["blockers"]
              and s_right["ready"] and not any("machine" in b for b in d_right["blockers"]))
        # файл фактов не читается: сверить факты нечем — единица с фактами не готова, единица без них готова
        broken = ft.replace(tel_ok, tel_bad).replace("\nentities:\n", '\nentities: ["не объект"]\nentities_was:\n')
        fy.write_text(broken, encoding="utf-8")
        plan.write_text(ptext.replace("value: tel:+79000000001", "value: tel:+79000000009"), encoding="utf-8")
        d_broken = build(slug, surf, root, today)
        fy.write_text("- не объект\n", encoding="utf-8")
        d_list = build(slug, surf, root, today)
        fy.write_text("facts: [\n", encoding="utf-8")
        d_garbage = build(slug, surf, root, today)
        plan.write_text(ptext.replace("value: tel:+79000000001", "value: '#lead-form'")
                        .replace("fact: missing:legal-details", "fact: null"), encoding="utf-8")
        d_nofacts = build(slug, surf, root, today)
        fy.write_text(ft, encoding="utf-8")
        plan.write_text(ptext, encoding="utf-8")
        s_broken, s_list, s_garbage, s_nofacts = ({u["id"]: u for u in x["units"]}["spasibo"]
                                                  for x in (d_broken, d_list, d_garbage, d_nofacts))
        unread = "spasibo: факты: файл фактов не читается"
        check("файл фактов не читается (entities не объектом при чужом номере в machine; верхний уровень — список; "
              "YAML не разбирается) — единица с фактами не готова, блокер «факты: файл фактов не читается»; единица "
              "без ссылок на факты и без целей-контактов при том же файле готова",
              broken.count("entities_was:") == 1 and tel_bad in broken
              and not s_broken["ready"] and unread in d_broken["blockers"]
              and not s_list["ready"] and unread in d_list["blockers"]
              and not s_garbage["ready"] and unread in d_garbage["blockers"]
              and s_nofacts["ready"] and not any(b.startswith("spasibo: факты") for b in d_nofacts["blockers"]))
        # тема брифа без темы токенов: бриф ждёт тёмную тему, значения токенов — светлая тема (modes.base не объявлена)
        tk = docpaths.design(slug, "tokens", repo=root)
        ink = {"color": {"$type": "color", "bg": {"$value": {"colorSpace": "srgb", "components": [0.1, 0.1, 0.1],
                                                             "hex": "#1A1A1A"}}}}
        tk.write_text(json.dumps(ink), encoding="utf-8")
        bp.write_text(bp.read_text(encoding="utf-8").replace("themes:\n  default: light\n", "themes:\n  default: dark\n",
                                                             1), encoding="utf-8")
        d_dark = build(slug, surf, root, today)
        tk.write_text(json.dumps(dict(ink, **{"$extensions": {"org.design-deep-dive.modes": {"base": "dark"}}})),
                      encoding="utf-8")
        d_based = build(slug, surf, root, today)
        tk.write_text("{", encoding="utf-8")
        d_unread = build(slug, surf, root, today)
        tk.unlink()
        bp.write_text(bp.read_text(encoding="utf-8").replace("themes:\n  default: dark\n", "themes:\n  default: light\n",
                                                             1), encoding="utf-8")
        ap = docpaths.design(slug, "asset-plans", surface="promo", repo=root) / "spasibo.yaml"
        aptext = ap.read_text(encoding="utf-8")
        ap.write_text("slots: [\n", encoding="utf-8")
        d_noplan = build(slug, surf, root, today)
        ap.write_text(aptext, encoding="utf-8")
        theme = "тема: бриф ждёт dark, у токенов ДС — light (тема значений modes.base или режим)"
        s_dark, s_based = ({u["id"]: u for u in x["units"]}["spasibo"] for x in (d_dark, d_based))
        check("тема брифа, которой нет у токенов ДС, — строка open «тема: …» у каждой единицы: готовность не держит, "
              "публикацию держит; токены с modes.base: dark — строки нет",
              all(theme in u["open"] for u in d_dark["units"]) and s_dark["ready"] and not s_dark["publishable"]
              and not any(o.startswith("тема:") for u in d_based["units"] for o in u["open"])
              and s_based["publishable"])
        s_unread, s_noplan = ({u["id"]: u for u in x["units"]}["spasibo"] for x in (d_unread, d_noplan))
        gone = "токены ДС не читаются (design/system.tokens.json)"
        check("вход сверки публикации есть, но не читается — сверить нечем: единица готова, публикацию держит строка "
              "open с причиной — токены ДС: «шрифт: … начертания сверить нечем» и «тема: … тему брифа сверить нечем»; "
              "план ассетов страницы: «демо-кадр: … демо-кадры сверить нечем»",
              s_unread["ready"] and not s_unread["publishable"]
              and f"шрифт: {gone} — начертания сверить нечем" in s_unread["open"]
              and f"тема: {gone} — тему брифа сверить нечем" in s_unread["open"]
              and s_noplan["ready"] and not s_noplan["publishable"]
              and "демо-кадр: план ассетов не читается (design/promo/assets/plans/spasibo.yaml) — демо-кадры сверить "
                  "нечем" in s_noplan["open"])
        dk.write_text(approved.replace("        - {id: a, text: 'Прораб позвонит и договорится о дне замера', status: "
                                       "assumed, source: ai-self}\n        chosen: a\n",
                                       "        - {id: a, text: '[PLACEHOLDER: срок звонка] Прораб позвонит', status: "
                                       "assumed, source: ai-self}\n", 1), encoding="utf-8")
        d_ph = build(slug, surf, root, today)
        s_open, s_pub, s_ph = ({u["id"]: u for u in x["units"]}["spasibo"] for x in (d_open, d_pub, d_ph))
        check("публикация: тексты approved, макет пропущен, бриф proposed — spasibo не готова, блокер поверхности; бриф "
              "approved — готова и publishable (в open только «решение заказчика: …»); заглушка в единственном "
              "варианте слота без chosen — строка open, ready true, publishable false",
              not s_open["ready"] and "поверхность: бриф proposed" in d_open["blockers"]
              and not any(b.startswith("spasibo:") for b in d_open["blockers"])
              and s_pub["ready"] and s_pub["publishable"] and s_pub["open"]
              and all(o.startswith(DECIDE) for o in s_pub["open"])
              and not any(b.startswith("поверхность") for b in d_pub["blockers"])
              and s_ph["ready"] and not s_ph["publishable"] and "[PLACEHOLDER]: confirmation/next-steps" in s_ph["open"]
              and "chosen: a\n        fact_ids: []\n        claim_flags: []\n    - section_id: footer"
              not in dk.read_text(encoding="utf-8"))
        bp.write_text(btext, encoding="utf-8")
        dk.write_text(dtext, encoding="utf-8")
        shutil.rmtree(note.parents[3])
        r = cli("build", "nope", "promo", "--repo", root, cwd=cwd)
        r2 = cli("build", slug, "--repo", root, cwd=cwd)
        check("нет проекта — код 2; build без поверхности — код 2", r.returncode == 2 and r2.returncode == 2)
    with fixture_project.built("input-landing") as fx, tempfile.TemporaryDirectory(prefix="ddd-ready-cwd-") as cwd:
        root, slug = fx.root, fx.slug
        surf = docpaths.surface(slug, "promo", root)
        ci = subprocess.run([sys.executable, str(HERE / "canvas_input.py"), "build", slug, "promo", "--stage",
                             "directions", "--repo", str(root), "--today", today.isoformat()], capture_output=True, text=True,
                            cwd=cwd)
        r = cli("build", slug, "promo", "--repo", root, "--today", today.isoformat(), cwd=cwd)
        data = yaml_mod().safe_load(docpaths.design(slug, "ready", surface="promo", repo=root).read_text(
            encoding="utf-8"))
        ab = data["units"][0]["after_build"]
        by_id = {a["id"]: a for a in ab}
        check("лендинг input-landing со входом directions: after_build — пункты списка базы места «после сборки» "
              "(I2, K1, L2 …), единица home, профиль landing-lead-services@L1",
              ci.returncode == 0 and r.returncode == 0 and {"I2", "K1", "L2"} <= set(by_id) and "A1" not in by_id
              and data["units"][0]["id"] == "home" and data["units"][0]["budget_profile"] == "landing-lead-services@L1")
        gate_ids = {g["id"] for g in yaml_mod().safe_load(kbpaths.kb(
            "site", "07-seo-geo-performance-analytics", "page-gates.yaml").read_text(encoding="utf-8"))["gates"]}
        check("пункт after_build — {id, severity, check} списка базы: тяжесть по юрисдикции страницы (J4b и L3 при ru — "
              "S, как SG-LEGAL-01), способ — поле check; id ворот пунктов gates — строки page-gates.yaml; форма "
              "манифеста без замечаний",
              all(set(a) == {"id", "severity", "check"} for a in ab)
              and by_id["J4b"] == {"id": "J4b", "severity": "S", "check": {"gates": ["SG-LEGAL-01"]}}
              and by_id["L3"]["severity"] == "S" and by_id["K1"] == {"id": "K1", "severity": "B", "check": "code"}
              and {g for a in ab if isinstance(a["check"], dict) for g in a["check"].get("gates", [])} <= gate_ids
              and any("tool" in a["check"] for a in ab if isinstance(a["check"], dict)) and not form_errors(data))
        r = cli("check", slug, "promo", "--repo", root, "--today", today.isoformat(), cwd=cwd)
        check("input-landing: check сразу после build — код 0", r.returncode == 0 and "0 error" in r.stdout)
        old = dict(data["units"][0], after_build=[a["id"] for a in ab])
        stale = dict(data, units=[old])
        errs = form_errors(stale)
        diff = _diff(stale, data)
        check("after_build строками id — форма не та (error), расхождение со сборкой называет пункты",
              any(p == "/units/0/after_build" and s == "error" for p, _m, s in errs)
              and any(d.startswith("home.after_build: не равны сборке пункты ") and "J4b" in d for d in diff))
        mp = docpaths.design(slug, "ready", surface="promo", repo=root)
        mtext = mp.read_text(encoding="utf-8")
        mp.write_text(mtext.replace(f"skill_version: {data['skill_version']}\n", ""), encoding="utf-8")
        items = check_surface(slug, surf, root, today)
        mp.write_text(mtext, encoding="utf-8")
        check("манифест без skill_version при входе холста — совет называет порядок: вход холста (canvas_input build с "
              "этапом входа), затем ready build",
              len(items) == 1 and f"canvas_input build {slug} promo --stage directions, затем ready build {slug} promo"
              in items[0].fix)
    with fixture_project.built("input-site") as fx:
        root, slug = fx.root, fx.slug
        surf = docpaths.surface(slug, "corp", root)
        mp, fy = docpaths.site(slug, "corp", "site-map", repo=root), docpaths.facts(slug, repo=root)
        mt, ft = mp.read_text(encoding="utf-8"), fy.read_text(encoding="utf-8")
        cta = "      cta:\n        action: request-quote\n        target: "
        tel = "machine: {type: telephone, value: '+7900000000"
        mp.write_text(mt.replace(cta + "request\n", cta + "messenger:sales-phone\n"), encoding="utf-8")
        fy.write_text(ft.replace(tel + "2'}", tel + "9'}").replace("- id: company-phone\n", "- id: company-phone\n"
                                                                    "  aliases: [sales-phone]\n"), encoding="utf-8")
        held = [b for b in build(slug, surf, root, today)["blockers"] if "fact:company-phone" in b and "machine" in b]
        mp.write_text(mt, encoding="utf-8")
        free = [b for b in build(slug, surf, root, today)["blockers"] if "machine" in b]
        check("многостраничник: цель призыва шапки карты messenger:<fact-id> ведёт (по id из aliases) на факт с "
              "machine не из canonical — блокер «факты: …» у каждой единицы; цель шапки — страница — блокера нет",
              cta + "request\n" in mt and tel + "2'}" in ft and "- id: company-phone\n" in ft and len(held) == 15
              and not free)
    with fixture_project.built("package-cabinet") as fx:
        root, slug = fx.root, fx.slug
        surf = docpaths.surface(slug, "office", root)
        data = build(slug, surf, root, today)
        check("кабинет: consumer <org>/frontend, web_kind app, единицы — пять экранов",
              data["consumer"] == "<org>/frontend" and data["web_kind"] == "app" and len(data["units"]) == 5)
        check("кабинет: perf — поле p75, RUM и сценарии AC-PRF-04…06; budget_profile «—»",
              data["perf"] == PERF_APP and all(u["budget_profile"] == "—" for u in data["units"]))
        check("кабинет: frontend_design — поправки ui C25, уровней нет",
              data["frontend_design"]["app_screens"].startswith("ui/CONTRADICTIONS.md §[C25]")
              and data["frontend_design"]["ambition"] == "—")
        check("кабинет: тексты утверждены — у единиц approved; FSD-карты нет — строка open «решение заказчика» у "
              "каждой единицы, не блокер",
              {u["texts"] for u in data["units"]} == {"approved"}
              and all(f"{DECIDE}FSD-карты нет" in u["open"] for u in data["units"])
              and not any("FSD" in b for b in data["blockers"]))
        dest = docpaths.design(slug, "ready", surface="office", repo=root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(slug, data), encoding="utf-8")
        check("кабинет: check сразу после записи — 0", not check_surface(slug, surf, root, today))
        tp = docpaths.project(slug, "screens", "office", "texts.md", repo=root)
        lines = tp.read_text(encoding="utf-8").splitlines(keepends=True)
        k = next(i for i, x in enumerate(lines) if x.startswith("| `requests.new.client.label` |"))
        lines[k] = lines[k].replace("| `approved` |", "| `checked` |")
        tp.write_text("".join(lines), encoding="utf-8")
        low = {u["id"]: u["texts"] for u in build(slug, surf, root, today)["units"]}
        check("кабинет: тексты единицы — наименьший статус её строк texts.md (подпись поля бланка checked → "
              "request-new checked, прочие approved)",
              low.get("request-new") == "checked" and {v for u, v in low.items() if u != "request-new"} == {"approved"})
        # готовность — гейты 2–4 и закрытая композиция: ДС, покрытие ДС типов экрана и FSD-карта — решения заказчика
        sysp = docpaths.design(slug, "system", repo=root)
        st = sysp.read_text(encoding="utf-8")
        sysp.write_text(st.replace("  KpiTile: {component: KpiTile}\n",
                                   "  KpiTile: {component: KpiTile, optional_states: [bogus]}\n"), encoding="utf-8")
        proj = docpaths.design(slug, "canvas-project", surface="office", repo=root)
        proj.mkdir(parents=True, exist_ok=True)
        (proj / "PlanDashboard.dc.html").write_text("<main data-screen='plan-dashboard'>План</main>\n",
                                                    encoding="utf-8")
        fp = Build(slug, surf, root, today).fingerprint("plan-dashboard", ["PlanDashboard.dc.html"])
        rv = docpaths.design(slug, "review", surface="office", repo=root)
        rv.mkdir(parents=True, exist_ok=True)
        (rv / "REVIEW.md").write_text(
            "# REVIEW\n\nИллюстрация самопроверки.\n\n## Приёмка\n\n"
            "| страница или экран | артборды | вердикт | одобрил | дата | отпечаток | открыто |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| `plan-dashboard` | `PlanDashboard.dc.html` | `accepted` | владелец продукта | 2026-09-29 | {fp} "
            "| — |\n", encoding="utf-8")
        sysp.write_text(sysp.read_text(encoding="utf-8").replace("status: approved", "status: proposed", 1)
                        + "starter: [plan-dashboard]\n", encoding="utf-8")
        d = build(slug, surf, root, today)
        tail = " — нет принятого файла с лицензией (строка манифеста design/_assets/ с font)"
        font = "шрифт: Golos Text 400, 500, 600" + tail
        pd0 = next(u for u in d["units"] if u["id"] == "plan-dashboard")
        fdir = docpaths.design(slug, "assets", repo=root) / "fonts"
        fdir.mkdir(parents=True, exist_ok=True)
        (fdir / "golos-text.woff2").write_bytes(b"wOF2 demo")
        row = {"slot": "font-golos-text", "file": "fonts/golos-text.woff2", "status": "accepted",
               "font": {"family": "Golos Text", "weight": 400, "style": "normal"}, "license": "OFL (демо)",
               "sha256": sha(fdir / "golos-text.woff2")}
        wide = dict(row, font=dict(row["font"], weight="400 600"))     # вариативный файл на все насыщенности токенов

        def fonts_of(*rows):
            (fdir.parent / "manifest.yaml").write_text(yaml_mod().safe_dump({"assets": list(rows)}, allow_unicode=True),
                                                       encoding="utf-8")
            data = build(slug, surf, root, today)
            return data, [sorted(o for o in u["open"] if o.startswith("шрифт:")) for u in data["units"]]
        draft = fonts_of(dict(wide, status="draft"))[1]
        part = fonts_of(row)[1]
        bare = fonts_of({k: v for k, v in wide.items() if k != "license"})[1]
        slant = fonts_of(dict(wide, font=dict(wide["font"], style="italic")))[1]
        d, full = fonts_of(wide)
        check("начертания шрифта токенов ДС без принятого файла с лицензией — строка open «шрифт: <семейство> "
              "<насыщенности> …» у каждой единицы, публикацию держит: черновая строка манифеста, строка без license и "
              "курсив её не снимают, файл одной насыщенности оставляет недостающие; вариативный файл на все "
              "насыщенности с лицензией её снимает",
              pd0["ready"] and not pd0["publishable"] and font in pd0["open"]
              and draft == bare == slant == [[font]] * len(d["units"])
              and part == [["шрифт: Golos Text 500, 600" + tail]] * len(d["units"]) and not any(full))
        units = {u["id"]: u for u in d["units"]}
        pd = units["plan-dashboard"]
        cov_lines = {u: [o for o in x["open"] if o.startswith(f"{DECIDE}покрытие ДС")] for u, x in units.items()}
        check("кабинет: FSD-карты нет, ДС не утверждена, у KpiTile optional_states вне словаря — plan-dashboard готова "
              "(макет принят, отпечаток совпал после starter и статуса ДС), решения заказчика — строки open; "
              "покрытие — только у экрана с KpiTile; блокеров о ДС, покрытии и FSD нет; статус partial",
              pd["ready"] and pd["publishable"] and pd["mockup"] == "accepted" and d["status"] == "partial"
              and not any(u["publishable"] for u in d["units"] if u["id"] != "plan-dashboard")
              and f"{DECIDE}FSD-карты нет" in pd["open"]
              and f"{DECIDE}ДС не утверждена (system.yaml proposed)" in pd["open"]
              and len(cov_lines["plan-dashboard"]) == 1 and "KpiTile" in cov_lines["plan-dashboard"][0]
              and not any(v for u, v in cov_lines.items() if u != "plan-dashboard")
              and not any(w in x for x in d["blockers"] for w in ("ДС", "FSD", "покрытие")))
        tk = docpaths.design(slug, "tokens", repo=root)
        tk0, lost = tk.read_text(encoding="utf-8"), {}
        for form, text in (("не разбираются", "{"), ("список", "[]")):
            tk.write_text(text, encoding="utf-8")
            lost[form] = next(u for u in build(slug, surf, root, today)["units"] if u["id"] == "plan-dashboard")
        void = json.loads(tk0)
        void["font"]["sans"]["$value"] = "{font.nowhere}"
        tk.write_text(json.dumps(void, ensure_ascii=False), encoding="utf-8")
        odd = next(u for u in build(slug, surf, root, today)["units"] if u["id"] == "plan-dashboard")
        tk.write_text(tk0, encoding="utf-8")
        back = next(u for u in build(slug, surf, root, today)["units"] if u["id"] == "plan-dashboard")
        gone = "токены ДС не читаются (design/system.tokens.json)"
        form = "токены ДС не по форме (design/system.tokens.json: ошибки R-STRUCT-006)"
        check("кабинет: токены ДС есть, но не читаются (не разбираются, не объект) или не по форме (семейство шрифта — "
              "алиас в пустоту) — экран с принятым макетом готов (отпечаток одобрения стоит на производном CSS), "
              "публикацию держат строки open «шрифт: … сверить нечем» и «тема: … сверить нечем»; токены возвращены — "
              "экран публикуем",
              all(u["ready"] and not u["publishable"] and f"шрифт: {gone} — начертания сверить нечем" in u["open"]
                  and f"тема: {gone} — тему брифа сверить нечем" in u["open"] for u in lost.values())
              and odd["ready"] and not odd["publishable"] and f"шрифт: {form} — начертания сверить нечем" in odd["open"]
              and f"тема: {form} — тему брифа сверить нечем" in odd["open"]
              and back["ready"] and back["publishable"])
        r = subprocess.run([sys.executable, me, "build", slug, "office", "--repo", str(root), "--today", today.isoformat()],
                           capture_output=True, text=True)
        check("build: решения заказчика — строками «решение заказчика: …» с единицами",
              r.returncode == 0 and f"{DECIDE}FSD-карты нет — not-found, plan-dashboard" in r.stdout)
    print("ready selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
