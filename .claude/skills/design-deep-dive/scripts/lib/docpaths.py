#!/usr/bin/env python3
"""docpaths — раскладка файлов проекта `docs/projects/<slug>/` для утилит `scripts/project/`. Стандартная библиотека;
статусы YAML-файлов читает PyYAML, если он есть, иначе — поиском поля в тексте.

Корень данных — репозиторий, в папке `docs/projects/` которого лежат проекты:
  1. ключ `--repo DIR` утилиты (аргумент `repo=` функций модуля);
  2. переменная окружения DDD_REPO — её читает только этот модуль;
  3. репозиторий, в котором лежит скилл (`kbpaths.repo()`).
Так репозиторий кода указывает соседний чекаут стратегии (`--repo ../strategy`), а самопроверки — временную папку
сборщика фикстур (`scripts/tests/fixture_project.py`). Канон форм `docs/projects/_template/` берётся всегда из
репозитория скилла (`template()`): во временной папке фикстуры лежат только проекты.

Раскладка — по канону `docs/projects/README.md` и README слоёв `docs/projects/_template/`:
  - проекты — папки `docs/projects/<slug>/`, кроме `_…`, `.…` и `infrastructure/`; файлы-реестры (`README.md`,
    `project-map.md`) проектами не считаются;
  - реестр поверхностей — таблица `surface.md` (slug, name, description, type, lives-at, user, web-kind, status);
  - слои поверхности по типу и роду (как правило R-STRUCT-010 `/project-audit`): interface — у всех, кроме `web` рода
    `landing` и `site`; screens и fsd — у `web` рода `app`, у `admin`, `desktop`, `embed`; site — у `web` рода `landing`
    и `site`; telegram-bot-flow — у `bot`; mobile — у `mobile`; design/<surface>/ — у `web`, `admin`, `desktop`,
    `embed`; файл возможностей capability/<surface>.md — у каждой;
  - файлы уровня продукта — `facts.yaml` (второй язык — `facts.<lang>.yaml`), `voice.yaml`, `voice.product.yaml`,
    `voc.yaml` и md продуктового слоя в корне папки продукта.

Общий вызов утилит `project/`:
    <утилита> <команда> <slug> [<surface>] [--repo DIR] [--stage …] [--out DIR] [--json]    команды build и check
    <утилита> --selftest                                                                  на встроенной фикстуре
Разбор — `parser()` и `parse()`: ошибка вызова или окружения (нет корня, проекта, поверхности) — код выхода 2.

    ap = docpaths.parser("canvas_input", "Вход холста …", surface="required", accept=lambda s: s.design,
                         stages=("directions", "treatment", "mockup", "motion"))
    ap.add_argument("--width", type=int)          # свои ключи утилиты
    call = docpaths.parse(ap)                     # call.command, call.slug, call.surf, call.repo, call.out, call.json …

Пути к файлам слоёв — `site()`, `screens()`, `design()`, `layer()`, `facts()`, `voice()`; путь для сообщений и находок —
`rel()`; статус файла по его форме — `status()`.

Диагностика: `python3 docpaths.py [<slug>] [--repo DIR] [--json]` — корень, проекты, поверхности и папки их слоёв,
файлы уровня продукта со статусами; `python3 docpaths.py --selftest` — самопроверка на фикстуре `minimal` сборщика, без
сети.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbpaths  # noqa: E402

ENV_REPO = "DDD_REPO"
RESERVED = ("infrastructure",)                          # папки docs/projects/, которые не проекты
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TYPES = ("web", "mobile", "api", "admin", "bot", "desktop", "embed", "other")
WEB_KINDS = ("landing", "site", "app")
PAGE_KINDS = ("landing", "site")                        # род web со слоем страницы
APP_TYPES = ("admin", "desktop", "embed")               # типы с маршрутом кабинета, как web рода app
LAYERS = ("capability", "interface", "screens", "fsd", "site", "telegram-bot-flow", "mobile", "design")

# имена файлов и папок слоёв: ключ → путь от папки слоя (ключ, которого нет в словаре, — часть пути как есть)
SITE_FILES = {"brief": "site-brief.yaml", "meaning": "meaning.yaml", "site-map": "site-map.yaml",
              "hierarchy": "hierarchy", "plans": "plans", "copy": "copy"}
SCREENS_FILES = {"map": "map.md", "texts": "texts.md", "flows": "flows", "screens": "screens", "blocks": "blocks",
                 "shells": "shells", "assets": "assets"}
DESIGN_PRODUCT = {"brand": "brand.yaml", "tokens": "system.tokens.json", "tokens-css": "system.tokens.css",
                  "design-md": "DESIGN.md", "system": "system.yaml", "app-brief": "app-brief.yaml",
                  "visual-dna": "visual-dna.json", "artifacts": "ARTIFACTS.md", "ds-project": "_design-system/project",
                  "assets": "_assets"}
DESIGN_SURFACE = {"art-direction": "art-direction.json", "visual-dna": "visual-dna.json", "assets": "assets",
                  "asset-plans": "assets/plans", "motion": "motion", "canvas": "canvas",
                  "canvas-project": "canvas/project", "canvas-html": "canvas/html", "input": "input",
                  "review": "review", "ready": "ready.yaml"}


class DocPathError(LookupError):
    """Нет корня данных, проекта или поверхности — ошибка окружения или вызова (код выхода 2 у утилит)."""


# ------------------------------------------------------------------ корень и проекты

def root_source(repo=None):
    """Откуда взят корень данных: «--repo», «DDD_REPO» или «скилл»."""
    if repo:
        return "--repo"
    if os.environ.get(ENV_REPO):
        return ENV_REPO
    return "скилл"


def root(repo=None):
    """Корень данных: repo (ключ --repo) → $DDD_REPO → репозиторий скилла. Без `docs/projects/` — DocPathError."""
    r = Path(repo or os.environ.get(ENV_REPO) or kbpaths.repo()).expanduser().resolve()
    if not (r / "docs" / "projects").is_dir():
        raise DocPathError(f"нет папки docs/projects/ в {r} (корень — {root_source(repo)})")
    return r


def projects_dir(repo=None):
    return root(repo) / "docs" / "projects"


def template(*parts):
    """Канон форм `docs/projects/_template/` — всегда из репозитория скилла."""
    return kbpaths.repo("docs", "projects", "_template", *parts)


def projects(repo=None):
    """Slug'и проектов по порядку: папки `docs/projects/`, кроме `_…`, `.…` и `infrastructure/`."""
    d = projects_dir(repo)
    return sorted(p.name for p in d.iterdir()
                  if p.is_dir() and not p.name.startswith(("_", ".")) and p.name not in RESERVED)


def project(slug, *parts, repo=None, must_exist=True):
    """Папка проекта `docs/projects/<slug>/` (+ части пути). Неверный slug или нет папки — DocPathError."""
    s = str(slug or "")
    if not SLUG.match(s) or s in RESERVED:
        raise DocPathError(f"неверный slug проекта: {slug!r} (kebab-case, не {', '.join(RESERVED)})")
    p = projects_dir(repo) / s
    if must_exist and not p.is_dir():
        have = ", ".join(projects(repo)) or "—"
        raise DocPathError(f"нет проекта {s!r} в {projects_dir(repo)}; есть: {have}")
    return p.joinpath(*parts)


def rel(path, repo=None):
    """Путь от корня данных, через «/» — для сообщений и поля `path` находок; вне корня — абсолютный."""
    p = Path(path).resolve()
    try:
        return p.relative_to(root(repo)).as_posix()
    except (ValueError, DocPathError):
        return p.as_posix()


# ------------------------------------------------------------------ реестр поверхностей

@dataclass(frozen=True)
class Surface:
    """Строка реестра `surface.md`."""
    slug: str
    name: str = ""
    description: str = ""
    type: str = ""
    lives_at: str = ""
    users: tuple = ()
    web_kind: str | None = None                         # landing · site · app у web, иначе None («—»)
    status: str | None = None
    line: int = 0                                       # номер строки в surface.md

    @property
    def route(self):
        """Маршрут по типу и роду: landing · site · app · mobile · bot · none (api, other, web без рода)."""
        if self.type == "web" and self.web_kind in WEB_KINDS:
            return self.web_kind
        if self.type in APP_TYPES:
            return "app"
        if self.type in ("mobile", "bot"):
            return self.type
        return "none"

    @property
    def page(self):
        """Слой страницы `site/<surface>/`: web рода landing или site."""
        return self.type == "web" and self.web_kind in PAGE_KINDS

    @property
    def app(self):
        """Маршрут кабинета: web рода app, admin, desktop, embed."""
        return self.route == "app"

    @property
    def design(self):
        """Папка облика `design/<surface>/`: web, admin, desktop, embed."""
        return self.type in ("web",) + APP_TYPES

    @property
    def layers(self):
        """Слои, которые поверхность получает по типу и роду (capability — у каждой)."""
        out = ["capability"]
        if not self.page:
            out.append("interface")
        if self.app:
            out += ["screens", "fsd"]
        if self.page:
            out.append("site")
        if self.type == "bot":
            out.append("telegram-bot-flow")
        if self.type == "mobile":
            out.append("mobile")
        if self.design:
            out.append("design")
        return tuple(out)

    def as_dict(self):
        return {"slug": self.slug, "name": self.name, "type": self.type, "web_kind": self.web_kind,
                "route": self.route, "users": list(self.users), "status": self.status, "layers": list(self.layers),
                "line": self.line}


def _cells(line):
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|") and len(s) > 1):
        return None
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s[1:-1])]


def _plain(cell):
    """`web` → web; «—», «-» и пусто → None."""
    v = (cell or "").strip()
    if v in ("", "—", "–", "-", "`—`"):
        return None
    m = re.fullmatch(r"`([^`]*)`", v)
    return m.group(1).strip() if m else v


def _refs(cell):
    """`` [`a`, `b`] `` или `a` → ('a', 'b')."""
    v = (cell or "").strip()
    if v.startswith("``") and v.endswith("``"):
        v = v[2:-2].strip()
    return tuple(x.strip() for x in re.findall(r"`([^`]+)`", v))


def read_surfaces(path):
    """Строки первой таблицы файла с колонками slug и type. Строки-заготовки (`<slug>`) и строки с неверным slug
    пропускаются; файла нет — пустой список."""
    p = Path(path)
    if not p.is_file():
        return []
    cols, out = None, []
    for no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        cells = _cells(line)
        if cells is None:
            if cols is not None and out:
                break                                   # таблица кончилась
            continue
        if cols is None:
            names = [c.strip("` ").lower() for c in cells]
            if "slug" in names and "type" in names:
                cols = {n: i for i, n in enumerate(names)}
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue

        def col(name):
            i = cols.get(name)
            return cells[i] if i is not None and i < len(cells) else ""

        slug = _plain(col("slug")) or ""
        if not SLUG.match(slug):
            continue
        out.append(Surface(slug=slug, name=col("name"), description=col("description"),
                           type=_plain(col("type")) or "", lives_at=_plain(col("lives-at")) or "",
                           users=_refs(col("user")), web_kind=_plain(col("web-kind")),
                           status=_plain(col("status")), line=no))
    return out


def surfaces(slug, repo=None):
    """Поверхности проекта по реестру `surface.md` (порядок — как в файле)."""
    return read_surfaces(project(slug, "surface.md", repo=repo))


def surface(slug, surface_slug, repo=None):
    """Строка реестра по slug поверхности; нет — DocPathError со списком."""
    ss = surfaces(slug, repo)
    for s in ss:
        if s.slug == surface_slug:
            return s
    raise DocPathError(f"нет поверхности {surface_slug!r} в {rel(project(slug, 'surface.md', repo=repo), repo)}; "
                       f"есть: {', '.join(s.slug for s in ss) or '—'}")


# ------------------------------------------------------------------ папки и файлы слоёв

def _join(base, names, parts):
    parts = [str(p) for p in parts]
    if parts and parts[0] in names:
        parts[0] = names[parts[0]]
    return base.joinpath(*parts)


def layer(slug, name, surface=None, repo=None):
    """Папка слоя: layer(slug, "screens", "web-app") → …/screens/web-app/; layer(slug, "design") → …/design/;
    layer(slug, "capability", "web-app") → …/capability/web-app.md."""
    if name not in LAYERS:
        raise ValueError(f"неизвестный слой: {name!r} (есть: {', '.join(LAYERS)})")
    if name == "capability":
        if not surface:
            return project(slug, "capability", repo=repo)
        return project(slug, "capability", f"{surface}.md", repo=repo)
    if surface is None:
        if name != "design":
            raise ValueError(f"слой {name} — по поверхности: нужен surface")
        return project(slug, "design", repo=repo)
    return project(slug, name, surface, repo=repo)


def site(slug, surface, *parts, repo=None):
    """Слой страницы: site(slug, "promo", "brief") → …/site/promo/site-brief.yaml; ключи — SITE_FILES."""
    return _join(layer(slug, "site", surface, repo), SITE_FILES, parts)


def screens(slug, surface, *parts, repo=None):
    """Слой экранов: screens(slug, "web-app", "map") → …/screens/web-app/map.md; ключи — SCREENS_FILES."""
    return _join(layer(slug, "screens", surface, repo), SCREENS_FILES, parts)


def design(slug, *parts, surface=None, repo=None):
    """Слой дизайна: design(slug, "tokens") → …/design/system.tokens.json (ключи — DESIGN_PRODUCT);
    design(slug, "input", surface="promo") → …/design/promo/input/ (ключи — DESIGN_SURFACE)."""
    if surface:
        return _join(layer(slug, "design", surface, repo), DESIGN_SURFACE, parts)
    return _join(layer(slug, "design", None, repo), DESIGN_PRODUCT, parts)


def facts(slug, lang=None, repo=None):
    """Факты продукта: facts.yaml или facts.<lang>.yaml (второй язык с теми же id)."""
    return project(slug, f"facts.{lang}.yaml" if lang else "facts.yaml", repo=repo)


def voice(slug, product=False, repo=None):
    """Голос: voice.yaml (бренд) или voice.product.yaml (продукт — интерфейс, мобильное приложение, бот)."""
    return project(slug, "voice.product.yaml" if product else "voice.yaml", repo=repo)


def voc(slug, repo=None):
    """Голос клиента: voc.yaml (по желанию)."""
    return project(slug, "voc.yaml", repo=repo)


def product_files(slug, repo=None):
    """Файлы уровня продукта, которые есть: {"facts": [...], "voice": [...], "voc": [...], "md": [...]}."""
    d = project(slug, repo=repo)
    files = sorted(p for p in d.iterdir() if p.is_file())
    return {"facts": [p for p in files if re.fullmatch(r"facts(\.[a-z]{2,3})?\.yaml", p.name)],
            "voice": [p for p in files if p.name in ("voice.yaml", "voice.product.yaml")],
            "voc": [p for p in files if p.name == "voc.yaml"],
            "md": [p for p in files if p.suffix == ".md"]}


def layer_dirs(slug, surface_row, repo=None):
    """Папки и файлы слоёв поверхности: {слой: путь} по её типу и роду (папка может ещё не существовать)."""
    return {name: layer(slug, name, surface_row.slug, repo) for name in surface_row.layers}


# ------------------------------------------------------------------ статус файла

def _frontmatter(text):
    if not text.startswith("---"):
        return None
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(\r?\n|$)", text, re.S)
    return m.group(1) if m else None


def _scalar(v):
    v = str(v).split("#", 1)[0].strip().strip("'\"`")
    return v or None


def status(path):
    """Статус файла по его форме: у md — поле `status` frontmatter или строка `**status:** `…``; у YAML и JSON —
    `status` верхнего уровня, иначе `project.status` (брифы), у copy deck — статус страниц, если он у всех один
    (`copy_deck.pages[].status`). Нет файла или поля — None."""
    p = Path(path)
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix == ".md":
        fm = _frontmatter(text)
        if fm is not None:
            m = re.search(r"^status:[ \t]*(.+)$", fm, re.M)
            return _scalar(m.group(1)) if m else None
        m = re.search(r"^\*\*status:\*\*[ \t]*`?([A-Za-z_-]+)`?", text, re.M)
        return m.group(1) if m else None
    data = None
    if p.suffix == ".json":
        try:
            data = json.loads(text)
        except ValueError:
            return None
    elif p.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            m = re.search(r"^status:[ \t]*(.+)$", text, re.M) or \
                re.search(r"^project:[ \t]*\r?\n(?:[ \t]+.*\r?\n)*?[ \t]+status:[ \t]*(.+)$", text, re.M)
            return _scalar(m.group(1)) if m else None
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            return None
    if not isinstance(data, dict):
        return None
    if isinstance(data.get("status"), str):
        return data["status"]
    proj = data.get("project")
    if isinstance(proj, dict) and isinstance(proj.get("status"), str):
        return proj["status"]
    deck = data.get("copy_deck")
    if isinstance(deck, dict):
        if isinstance(deck.get("status"), str):
            return deck["status"]
        st = {pg.get("status", "draft") for pg in deck.get("pages") or [] if isinstance(pg, dict)}
        if len(st) == 1:
            return st.pop()
    return None


# ------------------------------------------------------------------ общий вызов утилит project/

@dataclass
class Call:
    """Разобранный вызов утилиты `project/`."""
    command: str | None = None
    slug: str | None = None
    surface: str | None = None
    repo: Path | None = None                            # корень данных
    out: Path | None = None                             # --out; по умолчанию — решает утилита
    stage: str | None = None
    json: bool = False
    selftest: bool = False
    args: argparse.Namespace | None = None              # все ключи, со своими ключами утилиты
    project: Path | None = None                         # папка проекта
    surf: Surface | None = None                         # строка реестра поверхности
    surfaces: tuple = field(default_factory=tuple)      # все поверхности проекта


def parser(prog=None, description=None, commands=("build", "check"), surface="optional", stages=None, accept=None,
           epilog=None):
    """Парсер общего вызова `<команда> <slug> [<surface>] [--repo DIR] [--stage …] [--out DIR] [--json]` и
    `--selftest`. surface: "optional" · "required" · "none"; stages — значения `--stage` (нет — ключа нет);
    accept(Surface) → bool — какие поверхности подходят утилите. Свои ключи утилита добавляет в парсер сама."""
    if surface not in ("optional", "required", "none"):
        raise ValueError(f"surface: optional · required · none, не {surface!r}")
    ap = argparse.ArgumentParser(prog=prog, description=description, epilog=epilog,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", choices=tuple(commands), help="команда: " + " · ".join(commands))
    ap.add_argument("slug", nargs="?", help="slug проекта — папка docs/projects/<slug>/")
    if surface != "none":
        ap.add_argument("surface", nargs="?", help="slug поверхности из surface.md проекта"
                        + (" (обязательно)" if surface == "required" else ""))
    ap.add_argument("--repo", metavar="DIR",
                    help=f"корень репозитория с docs/projects/ (по умолчанию ${ENV_REPO} или репозиторий скилла)")
    if stages:
        ap.add_argument("--stage", choices=tuple(stages), help="этап: " + " · ".join(stages))
    ap.add_argument("--out", metavar="DIR", help="куда писать выход вместо места по умолчанию")
    ap.add_argument("--json", action="store_true", help="машинный вывод")
    ap.add_argument("--selftest", action="store_true", help="самопроверка на встроенной фикстуре, без сети")
    ap.set_defaults(_ddd_surface=surface, _ddd_accept=accept)
    return ap


def parse(ap, argv=None, accept=None):
    """Разобрать вызов и проверить окружение: корень, проект, поверхность. Ошибка — `ap.error` (код выхода 2)."""
    a = ap.parse_args(argv)
    mode = getattr(a, "_ddd_surface", "optional")
    accept = accept or getattr(a, "_ddd_accept", None)
    out = getattr(a, "out", None)
    call = Call(command=getattr(a, "command", None), slug=getattr(a, "slug", None), surface=getattr(a, "surface", None),
                out=Path(out).expanduser() if out else None, stage=getattr(a, "stage", None),
                json=bool(getattr(a, "json", False)), selftest=bool(getattr(a, "selftest", False)), args=a)
    if call.selftest:
        return call
    if not call.command or not call.slug:
        ap.error("нужны команда и slug проекта: <команда> <slug>" + (" <surface>" if mode == "required" else
                                                                        " [<surface>]" if mode == "optional" else ""))
    try:
        call.repo = root(getattr(a, "repo", None))
        call.project = project(call.slug, repo=call.repo)
    except DocPathError as e:
        ap.error(str(e))
    call.surfaces = tuple(surfaces(call.slug, call.repo))
    names = ", ".join(s.slug for s in call.surfaces) or "—"
    if call.surface:
        s = next((x for x in call.surfaces if x.slug == call.surface), None)
        if s is None:
            ap.error(f"нет поверхности {call.surface!r} в surface.md проекта {call.slug}; есть: {names}")
        if accept and not accept(s):
            kind = s.type + (f" рода {s.web_kind}" if s.web_kind else "")
            ap.error(f"поверхность {s.slug} ({kind}) не для этой утилиты")
        call.surf = s
    elif mode == "required":
        ok = [s.slug for s in call.surfaces if not accept or accept(s)]
        ap.error(f"нужна поверхность: <команда> <slug> <surface>; подходят: {', '.join(ok) or '—'}")
    return call


# ------------------------------------------------------------------ диагностика и самопроверка

def describe(slug=None, repo=None):
    r = root(repo)
    info = {"root": str(r), "source": root_source(repo), "template": str(template()), "projects": projects(r)}
    if slug:
        d = project(slug, repo=r)
        rows = []
        for s in surfaces(slug, r):
            row = s.as_dict()
            row["layers"] = {n: {"path": rel(p, r), "exists": p.exists()} for n, p in layer_dirs(slug, s, r).items()}
            rows.append(row)
        prod = {k: [{"path": rel(p, r), "status": status(p)} for p in v] for k, v in product_files(slug, r).items()}
        info["project"] = {"slug": slug, "path": str(d), "surfaces": rows, "product": prod}
    return info


def _print(info):
    print(f"root      {info['root']}   (корень — {info['source']})")
    print(f"template  {info['template']}")
    print(f"projects  {', '.join(info['projects']) or '—'}")
    p = info.get("project")
    if not p:
        return
    print(f"project   {p['path']}")
    for s in p["surfaces"]:
        kind = s["type"] + (f"/{s['web_kind']}" if s["web_kind"] else "")
        print(f"surface   {s['slug']:<16} {kind:<14} маршрут {s['route']:<8} статус {s['status'] or '—'}")
        for n, v in s["layers"].items():
            print(f"            {n:<18} {v['path']}{'' if v['exists'] else '   (нет)'}")
    for k, files in p["product"].items():
        shown = ", ".join(f"{Path(f['path']).name} [{f['status'] or '—'}]" for f in files) or "—"
        print(f"{k:<9} {shown}")


def _selftest():
    import contextlib
    import io
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)

    def exits(argv, ap):
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                parse(ap, argv)
            except SystemExit as e:
                return e.code
        return None

    kbpaths.use("tests")
    import fixture_project
    saved = os.environ.pop(ENV_REPO, None)
    try:
        check("template() — канон форм в репозитории скилла", template("project", "surface.md").is_file())
        check("корень по умолчанию — репозиторий скилла", root() == kbpaths.repo().resolve())
        check("заготовка реестра без данных: строк нет", read_surfaces(template("project", "surface.md")) == [])
        with fixture_project.built("minimal") as fx:
            r, slug = fx.root, fx.slug
            check("--repo: корень — сборка фикстуры", root(r) == r.resolve())
            os.environ[ENV_REPO] = str(r)
            check("DDD_REPO: корень — сборка фикстуры", root() == r.resolve() and root_source() == ENV_REPO)
            check("--repo сильнее DDD_REPO", root(kbpaths.repo()) == kbpaths.repo().resolve())
            os.environ.pop(ENV_REPO)
            (projects_dir(r) / "infrastructure").mkdir()
            (projects_dir(r) / "_template").mkdir()
            (projects_dir(r) / "project-map.md").write_text("# project-map\n", encoding="utf-8")
            check(f"projects(): только {slug} (без infrastructure, _template и файлов-реестров)", projects(r) == [slug])
            ss = surfaces(slug, r)
            by = {s.slug: s for s in ss}
            check("реестр: две поверхности", [s.slug for s in ss] == ["promo", "cabinet"])
            pr, cab = by.get("promo"), by.get("cabinet")
            check("promo: web рода landing, маршрут landing, слои capability · site · design",
                  pr and (pr.type, pr.web_kind, pr.route, pr.layers) == ("web", "landing", "landing",
                                                                         ("capability", "site", "design")))
            check("cabinet: web рода app, маршрут app, слои capability · interface · screens · fsd · design",
                  cab and (cab.type, cab.web_kind, cab.route, cab.layers) ==
                  ("web", "app", "app", ("capability", "interface", "screens", "fsd", "design")))
            check("реестр: пользователи и статус строки", cab and cab.users == ("client",) and cab.status == "draft")
            check("bot, mobile, api: маршруты и слои по типу",
                  Surface("b", type="bot").layers == ("capability", "interface", "telegram-bot-flow")
                  and Surface("m", type="mobile").route == "mobile" and Surface("a", type="api").route == "none"
                  and Surface("x", type="admin").layers == ("capability", "interface", "screens", "fsd", "design"))
            check("site(): бриф и план лендинга на месте", site(slug, "promo", "brief", repo=r).is_file()
                  and site(slug, "promo", "plans", "home.yaml", repo=r).is_file())
            check("screens(): map.md кабинета", screens(slug, "cabinet", "map", repo=r).is_file())
            check("design(): пути продукта и поверхности",
                  design(slug, "tokens", repo=r) == project(slug, "design", "system.tokens.json", repo=r)
                  and design(slug, "input", surface="promo", repo=r) == project(slug, "design", "promo", "input", repo=r)
                  and design(slug, "ready", surface="cabinet", repo=r).name == "ready.yaml")
            check("layer(): capability/<surface>.md", layer(slug, "capability", "promo", r).name == "promo.md")
            ld = layer_dirs(slug, pr, r)
            check("layer_dirs(): у лендинга есть site/promo/", ld["site"].is_dir() and not ld["design"].exists())
            pf = product_files(slug, r)
            check("файлы уровня продукта: facts.yaml, voice.yaml; md — surface.md, vision.md",
                  [p.name for p in pf["facts"]] == ["facts.yaml"] and [p.name for p in pf["voice"]] == ["voice.yaml"]
                  and [p.name for p in pf["md"]] == ["surface.md", "vision.md"])
            check("status(): facts — draft, бриф — project.status proposed, план — proposed",
                  status(facts(slug, repo=r)) == "draft" and status(site(slug, "promo", "brief", repo=r)) == "proposed"
                  and status(site(slug, "promo", "plans", "home.yaml", repo=r)) == "proposed")
            check("status(): md — frontmatter map.md, строка **status:** vision.md, у реестра — нет",
                  status(screens(slug, "cabinet", "map", repo=r)) == "draft"
                  and status(project(slug, "vision.md", repo=r)) == "draft"
                  and status(project(slug, "surface.md", repo=r)) is None)
            with tempfile.TemporaryDirectory() as td:
                deck = Path(td, "copy.yaml")
                deck.write_text("copy_deck:\n  pages:\n  - {page_id: a, status: approved}\n"
                                "  - {page_id: b, status: approved}\n", encoding="utf-8")
                check("status(): copy deck — общий статус страниц", status(deck) == "approved")
                check("корень без docs/projects — DocPathError", _raises(lambda: root(td)))
            check("rel(): путь от корня", rel(facts(slug, repo=r), r) == f"docs/projects/{slug}/facts.yaml")
            ap = parser("t", "проверка", surface="required", stages=("directions", "mockup"), accept=lambda s: s.design)
            call = parse(ap, ["build", slug, "promo", "--repo", str(r), "--stage", "mockup", "--json"])
            check("parse(): build <slug> <surface> --stage --json",
                  (call.command, call.slug, call.surf.slug, call.stage, call.json, call.repo) ==
                  ("build", slug, "promo", "mockup", True, r.resolve()))
            check("parse(): нет проекта — код 2", exits(["check", "no-such-project", "--repo", str(r)], ap) == 2)
            check("parse(): нет поверхности — код 2", exits(["check", slug, "nope", "--repo", str(r)], ap) == 2)
            check("parse(): поверхность обязательна — код 2", exits(["check", slug, "--repo", str(r)], ap) == 2)
            check("parse(): неизвестная команда — код 2", exits(["make", slug, "promo", "--repo", str(r)], ap) == 2)
            ap2 = parser("t", "проверка", surface="optional", accept=lambda s: s.page)
            check("parse(): поверхность не той утилиты — код 2", exits(["check", slug, "cabinet", "--repo", str(r)], ap2) == 2)
            check("parse(): без поверхности — весь проект", parse(ap2, ["check", slug, "--repo", str(r)]).surf is None)
            check("parse(): --selftest без проекта", parse(ap, ["--selftest"]).selftest)
            info = describe(slug, r)
            check("describe(): проект, поверхности и слои", len(info["project"]["surfaces"]) == 2)
    finally:
        if saved is not None:
            os.environ[ENV_REPO] = saved
        else:
            os.environ.pop(ENV_REPO, None)
    print("docpaths selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def _raises(fn):
    try:
        fn()
    except DocPathError:
        return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="slug проекта — показать поверхности, слои и файлы уровня продукта")
    ap.add_argument("--repo", metavar="DIR", help=f"корень данных (по умолчанию ${ENV_REPO} или репозиторий скилла)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    try:
        info = describe(a.slug, a.repo)
    except DocPathError as e:
        print(f"docpaths: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(info, ensure_ascii=False, indent=1))
    else:
        _print(info)
    return 0


if __name__ == "__main__":
    sys.exit(main())
