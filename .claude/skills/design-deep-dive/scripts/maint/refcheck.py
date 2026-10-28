#!/usr/bin/env python3
"""Проверка ссылок и forward-only в текстах скилла design-deep-dive (kb/common, kb/INDEX.md, SKILL.md и др.).

Что ищет в каждом файле:
  • ссылки markdown `[..](путь)` — от папки файла; образец (`[...](...)`, `<…>`) — не ссылка;
  • пути в обратных кавычках (`kb/…`, `common/…`, `ux/03-…/01-….md`, `scripts/…`, `assets/…`, `docs/…`) — от папки файла,
    от `kb/`, от корня скилла, от корня репозитория, от канона продуктовых слоёв; `*` — шаблон (нужно ≥ 1 совпадение);
    `…`, `<…>`, `{…}` — образец, не ссылка; выделение `_…_` вокруг спана снимается; раздел `§` ищется во всех файлах,
    куда ведёт путь; голое имя (`canon.tsv`, `docs/`) — имя: достаточно, чтобы такой файл или папка были в корне
    репозитория, в скилле, `docs/`, `.claude/` или `client-onboarding/`. В текстах вне `kb/` путь ищется ещё от папок
    слоёв с их формами (короткий адрес `_templates/service-readme.md`), а шаблон раскладки проекта, у которого папка до
    первого `*` есть у слоя (`jobs/*.md`, `services/*/domains/`), совпадений не требует;
  • адрес вида артефакта слоя `<слой>/<вид>[.поле]` (`business/profile`, `hypothesis-map/metric.current`,
    `interface/block`) — верен, когда у слоя есть файл вида; слой есть, вида нет — битый адрес;
  • не ссылки, когда файла по пути нет: расширение файла (`.glb`); домен с путём (`cdn.example.net/npm/`); тип
    содержимого (`text/plain`, `model/gltf-binary`); часовой пояс (`Europe/Moscow`); синтаксис вызова — первое слово
    спана заглавными от трёх знаков, за которым идут ещё слова или «/» (`ФАЙЛ.md … [--json ОТЧЁТ]`, `OUT_DIR/_source/`);
    путь с `../`, который поднимается к корню репозитория или выше и входит в папку, которой там нет, или из текста
    вне папки скилла входит в соседний чекаут орги (`../backend/…`), которого нет на месте; путь через имя из
    `scripts/maint/data/notlinks.tsv` — файлы и папки проекта и рабочей памяти скиллов, выходы утилит, пути соседних
    репозиториев, значения через «/» (в статьях `kb/` — только значения). Путь от корня скилла (`kb/`, `scripts/`,
    `references/`, `assets/`, папки баз) списком не прощается;
  • короткие адреса «<база> NN/MM § X.Y» (база: ux, ui, site, text, creative, ai-media, 3d, claude-design, cd) —
    файл `kb/<база>/NN-*/MM-*` и раздел по заголовкам (§ X.Y — заголовок, начинающийся с «X.Y»; § имя — заголовок или
    строка с этим именем);
  • следы журнала (forward-only): Р-номера, пути в журнал сборки, имена фаз сборки, даты, слова сравнения с прошлым,
    имя снятого генератора, пути машины — шаблоны `forward-only` в `scripts/maint/data/traces.tsv`. Дата в строке,
    которая начинается со слова «Снимок:», — не след: статья со скоропортящимся знанием называет день своего снимка.
    Слово сравнения в кавычках-ёлочках («было/стало») — упоминание слова, а не след; «больше не» после отрицательного
    местоимения («ни на что больше не») значит «ни на что другое», а не «уже не».

Корень скилла и репозитория — через `scripts/lib/kbpaths.py`: утилита работает в любом клоне и из соседнего чекаута.
Находки выводятся с путём от корня репозитория.

Запуск (Python ≥ 3.11, только стандартная библиотека):
    python3 .claude/skills/design-deep-dive/scripts/maint/refcheck.py <файл> [...]        # ссылки + forward-only
    python3 .claude/skills/design-deep-dive/scripts/maint/refcheck.py --strict <файл> ...  # код 1 и при следах журнала
    python3 .claude/skills/design-deep-dive/scripts/maint/refcheck.py --selftest           # самопроверка во временной папке
Код выхода: 0 — битых ссылок нет; 1 — есть битые (или следы журнала при --strict), самопроверка не прошла; 2 — ошибка
вызова.
"""
from __future__ import annotations

import argparse
import csv
import glob
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import kbpaths  # noqa: E402

ROOT = kbpaths.repo()
SKILL = kbpaths.skill()
KB = kbpaths.kb()
TEMPLATE = ROOT / "docs" / "projects" / "_template"
TRACES = kbpaths.data("maint", "traces.tsv")
NOTLINKS = kbpaths.data("maint", "notlinks.tsv")
BASES = list(kbpaths.BASES)
ALIAS = {"cd": "claude-design"}
EXT = (".md", ".yaml", ".yml", ".json", ".tsv", ".csv", ".py", ".js", ".mjs", ".ts", ".html", ".css", ".txt", ".sh",
       ".webp", ".avif", ".png", ".jpg", ".svg", ".glb", ".blend", ".toml")

MD_LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
TICK = re.compile(r"`([^`\n]+)`")
BASE_RE = "|".join(sorted([re.escape(b) for b in BASES] + ["cd"], key=len, reverse=True))
SHORT = re.compile(
    rf"(?<![\w/.-])({BASE_RE})\s+(\d{{2}})/(\d{{2}}|README)(?![\w/])"
    r"(?:\s*§\s*([0-9]+(?:\.[0-9]+)*|[^\s,;:)`«»\"]+))?")


def trace_rows(kind: str) -> list[dict]:
    """Строки одного вида из `data/traces.tsv` в порядке файла: {kind, label, pattern, example}."""
    lines = [x for x in TRACES.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
    return [row for row in csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE) if row["kind"] == kind]


def load_traces(kind: str) -> list[tuple[str, re.Pattern]]:
    """Шаблоны одного вида: [(метка, регулярка)] в порядке файла."""
    return [(row["label"], re.compile(row["pattern"])) for row in trace_rows(kind)]


FWD = load_traces("forward-only")
DATE = "дата"                  # имя следа в данных: в строке снимка статьи он не ищется
WORDS = "сравнение с прошлым"  # имя следа в данных: слово в ёлочках — упоминание
SNAPSHOT = "Снимок:"           # начало строки, которой статья называет день своего снимка
ELSE_BEFORE = re.compile(r"(?i)(?:\bни(?:\s+[\w-]+){1,2}|\bни(?:что|чего|чем|чему|кто|кого|кому|где|куда))\s+$")


def mention(line: str, m: re.Match) -> bool:
    """Слово сравнения, которое о прошлом не говорит: названо в ёлочках как слово («было/стало») или «больше не» после
    отрицательного местоимения («ни на что больше не» — «ни на что другое»)."""
    if line[m.start() - 1:m.start()] == "«" and line[m.end():m.end() + 1] == "»":
        return True
    return m.group(0).lower() == "больше не" and bool(ELSE_BEFORE.search(line[:m.start()]))


def notlink_rows() -> list[dict]:
    """Строки `data/notlinks.tsv`: {kind, name, what}."""
    lines = [x for x in NOTLINKS.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE))


ELSEWHERE = [(r["kind"], tuple(r["name"].split("/"))) for r in notlink_rows() if r["kind"] != "sibling"]
SIBLINGS = {r["name"] for r in notlink_rows() if r["kind"] == "sibling"}
SKILL_HEADS = {"kb", "scripts", "references", "assets", "common", "cd", *BASES}   # путь от корня скилла


def layer_dirs() -> dict[str, list[Path]]:
    """Папки слоёв по имени слоя: `docs/<слой>/` верхних слоёв, `docs/projects/infrastructure/`, канон продуктовых
    слоёв `docs/projects/_template/<слой>/` — каждая вместе с подпапками форм `_template/`, `_templates/`."""
    docs = ROOT / "docs"
    roots = [d for d in sorted(docs.iterdir()) if d.is_dir() and d.name != "projects"] if docs.is_dir() else []
    roots.append(docs / "projects" / "infrastructure")
    roots += [d for d in sorted(TEMPLATE.iterdir()) if d.is_dir()] if TEMPLATE.is_dir() else []
    out: dict[str, list[Path]] = {}
    for d in roots:
        if d.is_dir():
            out.setdefault(d.name, []).extend([d] + [d / s for s in ("_template", "_templates") if (d / s).is_dir()])
    return out


LAYERS = layer_dirs()
LAYER_BASES = [p for dirs in LAYERS.values() for p in dirs]
LAYOUT_BASES = [TEMPLATE, ROOT / "docs" / "projects", ROOT / "docs", *LAYER_BASES]


def headings(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    out, fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence and re.match(r"^#{1,6}\s", line):
            out.append(re.sub(r"^#{1,6}\s+", "", line).strip())
    return out


def section_ok(path: Path, sec: str) -> bool:
    if not path.is_file() or path.suffix != ".md":
        return True  # раздел проверяем только у md
    heads = headings(path)
    sec = sec.strip().rstrip(".")
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", sec):
        pat = re.compile(rf"^(?:§\s*)?(?:[A-Za-zА-Яа-я]+\s+)?{re.escape(sec)}(?:[.\s)]|$)")
        return any(pat.match(h) for h in heads)
    low = sec.lower()
    if any(low in h.lower() for h in heads):
        return True
    return low in path.read_text(encoding="utf-8").lower()


def resolve_short(base: str, nn: str, mm: str) -> Path | None:
    base = ALIAS.get(base, base)
    dirs = sorted((KB / base).glob(f"{nn}-*"))
    dirs = [d for d in dirs if d.is_dir()]
    if not dirs:
        return None
    if mm == "README":
        p = dirs[0] / "README.md"
        return p if p.exists() else None
    files = sorted(dirs[0].glob(f"{mm}-*"))
    md = [f for f in files if f.suffix == ".md"]
    return (md or files or [None])[0]


def looks_like_path(tok: str) -> bool:
    if any(c in tok for c in "…<>{}=()|\"'") or "..." in tok:
        return False
    if tok.startswith(("-", "http", "$", "~", "#", "/")) or ":" in tok:
        return False
    if re.match(r"\d{2}/", tok):
        return False  # адрес папки без базы («04/*», «11/») — база названа в тексте рядом
    if tok.startswith(".") and "/" not in tok:
        return False  # расширение файла («.glb», «.glb.json»), а не имя файла
    return "/" in tok or tok.lower().endswith(EXT)


HOST = re.compile(r"(?:[a-z0-9-]+\.)+[a-z]{2,}", re.I)
MEDIA_TYPES = ("application", "audio", "font", "image", "message", "model", "multipart", "text", "video")
MEDIA_SUBTYPE = re.compile(r"(?!\d{2}-)[a-z0-9][a-z0-9.+-]*", re.I)   # «NN-имя» — папка базы, а не подтип
TIME_ZONE = re.compile(r"(?:Africa|America|Antarctica|Arctic|Asia|Atlantic|Australia|Europe|Indian|Pacific|Etc)"
                       r"(?:/[A-Z][A-Za-z0-9_+-]*)+")
ARG = re.compile(r"[A-ZА-ЯЁ][A-ZА-ЯЁ0-9_]+[A-ZА-ЯЁ0-9]")   # имя аргумента заглавными от трёх знаков: ФАЙЛ, OUT_DIR


def not_a_file(tok: str) -> bool:
    """Спан с «/», который называет не файл скилла: домен с путём без схемы (`cdn.example.net/npm/`), тип содержимого
    из двух слов без расширения файла (`text/plain`, `model/gltf-binary`) или часовой пояс (`Europe/Moscow`).
    Спрашивается, когда файла по такому пути нет: существующий путь остаётся ссылкой."""
    tok = tok.rstrip(".,;")
    head, sep, rest = tok.partition("/")
    if not sep:
        return False
    if HOST.fullmatch(head) and not head.lower().endswith(EXT):   # «notes.md/json» — имя файла, а не домен
        return True
    if TIME_ZONE.fullmatch(tok):
        return True
    return (head.lower() in MEDIA_TYPES and "/" not in rest and bool(MEDIA_SUBTYPE.fullmatch(rest))
            and not rest.lower().endswith(EXT))


def call_argument(first: str, more: bool) -> bool:
    """Синтаксис вызова, а не путь: первое слово спана — имя аргумента заглавными от трёх знаков (`ФАЙЛ.md`,
    `SHEET.svg`, `OUT_DIR`), за которым идут ещё слова (`ФАЙЛ.md … [--json ОТЧЁТ]`, `more`) или «/»
    (`OUT_DIR/_source/`). Имя заглавными без продолжения (`ПЛАН.md`) и папка из двух заглавных (`CD/x.md`) остаются
    путём."""
    head, sep, _ = first.partition("/")
    return bool(ARG.fullmatch(head.split(".", 1)[0])) and (bool(sep) or more)


def outside_repo(tok: str, here: Path, root: Path = ROOT, skill: Path = SKILL) -> bool:
    """Путь с `../`, который ведёт не в этот репозиторий: поднимается к корню репозитория или выше и входит в папку,
    которой там нет (`../strategy`, пример пути другого репозитория), или входит в соседний чекаут орги
    (`../backend/…` — вид `sibling` в `notlinks.tsv`), которого на месте нет; внутри папки скилла `../` ведёт между
    его папками, и имя соседа там не прощает. Путь, который входит в существующую папку, сверяется как ссылка."""
    parts = tok.split("/")
    ups = 0
    while ups < len(parts) and parts[ups] == "..":
        ups += 1
    rest = [p for p in parts[ups:] if p and p != "."]
    if not ups or not rest:
        return False
    base = here.parent
    for _ in range(ups):
        base = base.parent
    if (base / rest[0]).exists():
        return False
    return (base == root or not base.is_relative_to(root)
            or (rest[0] in SIBLINGS and not base.is_relative_to(skill)))


LAYER_KIND = re.compile(r"([a-z][a-z-]*)/([a-z][a-z0-9-]*)(?:\.[A-Za-z][\w-]*)?")


def layer_kind(tok: str) -> bool | None:
    """Адрес вида артефакта слоя `<слой>/<вид>[.поле]` (`business/profile`, `swot/bet.promoted-to`,
    `interface/block`): True — у слоя есть файл вида, False — слой есть, вида нет; None — не адрес вида (нет такого
    слоя, путь с расширением файла, папка)."""
    m = LAYER_KIND.fullmatch(tok)
    if not m or tok.lower().endswith(EXT) or m.group(1) not in LAYERS:
        return None
    layer, kind = m.groups()
    return any((d / f"{kind}{ext}").is_file() for d in LAYERS[layer] for ext in (".md", ".yaml"))


def elsewhere(tok: str, kinds: tuple[str, ...] | None = None) -> bool:
    """Путь, который живёт не в этом репозитории: один из его сегментов — имя из `notlinks.tsv` (имя из нескольких
    сегментов — начало пути); `kinds` — только эти виды строк. Путь от корня скилла (`kb/`, `scripts/`, папки баз)
    так не прощается."""
    segs = [s for s in tok.split("/") if s and s not in (".", "..")]
    if not segs or segs[0] in SKILL_HEADS or re.match(r"\d{2}-", segs[0]):
        return False
    return any(name[0] in segs if len(name) == 1 else tuple(segs[:len(name)]) == name
               for kind, name in ELSEWHERE if kinds is None or kind in kinds)


_NAMES: dict[str, bool] = {}
NAME_BASES = (SKILL, ROOT / "docs", ROOT / ".claude", ROOT / "client-onboarding")


def name_exists(name: str) -> bool:
    """Голое имя файла или папки (без «/») — имя, место даёт контекст: достаточно, чтобы такое имя было в корне
    репозитория (`CLAUDE.md`, `docs/`), в скилле, `docs/`, `.claude/` или `client-onboarding/`."""
    if name not in _NAMES:
        found = (ROOT / name).exists()
        for base in () if found else NAME_BASES:
            if base.is_dir() and any(base.rglob(name)):
                found = True
                break
        _NAMES[name] = found
    return _NAMES[name]


def resolve_path(tok: str, here: Path, layers: bool = True) -> bool:
    """Путь от папки файла, `kb/`, корня скилла и репозитория, канона слоёв; `layers` — ещё от папок слоёв с формами
    и шаблон раскладки проекта (тексты вне `kb/`: база пишет пути своих файлов)."""
    tok = tok.rstrip(".,;")
    if "/" not in tok.rstrip("/"):
        return name_exists(tok.rstrip("/"))
    pattern = "*" in tok or "?" in tok
    cands = [here.parent, KB, SKILL, ROOT, TEMPLATE, ROOT / "docs" / "projects", ROOT / "docs"]
    cands += LAYER_BASES if layers else []
    for base in cands:
        target = base / tok
        if pattern:
            if glob.glob(str(target)):
                return True
        elif target.exists():
            return True
    if pattern and layers:   # раскладка проекта: папка до первого шаблона есть у слоя — файлы появятся в проекте
        head = tok[:min(i for i in (tok.find("*"), tok.find("?")) if i >= 0)].rpartition("/")[0]
        return bool(head) and any((base / head).is_dir() for base in LAYOUT_BASES)
    return False


def check_file(path: Path, in_kb: bool | None = None) -> tuple[list[str], list[str], int]:
    """Битые ссылки, следы журнала и число сверенных ссылок файла. `in_kb` — правила статьи базы (по умолчанию — по
    месту файла): имена проекта и памяти скиллов из списка не прощаются, папки слоёв путей не дают."""
    broken, fwd, n = [], [], 0
    in_kb = path.is_relative_to(KB) if in_kb is None else in_kb
    text = path.read_text(encoding="utf-8")
    fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        # ссылки markdown
        for m in MD_LINK.finditer(line):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if any(c in target for c in "…<>{}") or "..." in target:
                continue  # образец ссылки: `[...](...)`
            n += 1
            file_part = target.split("#", 1)[0]
            if file_part and not (path.parent / file_part).exists():
                broken.append(f"{i}: ссылка ({target})")
        # пути в обратных кавычках
        for m in TICK.finditer(line):
            tok = m.group(1).strip()
            if len(tok) > 2 and tok[0] == tok[-1] == "_":
                tok = tok[1:-1]   # выделение в спане: `_N/A_`
            words = tok.split(" §")[0].split("#")[0].split()
            first = words[0] if words else ""
            if not looks_like_path(first):
                continue
            found = resolve_path(first, path, layers=not in_kb)
            if not found:
                cand = first.rstrip(".,;")
                if (not_a_file(cand) or call_argument(cand, len(words) > 1) or outside_repo(cand, path)):
                    continue
                kind = layer_kind(cand)
                if kind is None and elsewhere(cand, ("value",) if in_kb else None):
                    continue
                found = bool(kind)
            n += 1
            if not found:
                broken.append(f"{i}: путь `{tok}`")
                continue
            msec = re.search(r"§\s*([0-9]+(?:\.[0-9]+)*|[^\s,;:)`]+)", tok)
            if msec:
                targets = [t for t in (base / first for base in (path.parent, KB, SKILL, ROOT)) if t.exists()]
                if targets and not any(section_ok(t, msec.group(1)) for t in targets):
                    broken.append(f"{i}: раздел `{tok}`")
        # короткие адреса
        for m in SHORT.finditer(line):
            base, nn, mm, sec = m.group(1), m.group(2), m.group(3), m.group(4)
            n += 1
            p = resolve_short(base, nn, mm)
            if p is None:
                broken.append(f"{i}: адрес «{m.group(0).strip()}» — нет файла")
                continue
            if sec:
                secs = [sec]
                tail = line[m.end():m.end() + 12]
                mt = re.match(r"\s*[–-]\s*§?\s*([0-9]+(?:\.[0-9]+)*)", tail)
                if mt:
                    secs.append(mt.group(1))
                for s in secs:
                    if not section_ok(p, s):
                        broken.append(f"{i}: адрес «{base} {nn}/{mm} § {s}» — нет раздела в {p.relative_to(KB)}")
        snapshot = line.lstrip().startswith(SNAPSHOT)
        for label, rx in FWD:
            if snapshot and label == DATE:
                continue
            for m in rx.finditer(line):
                if label == WORDS and mention(line, m):
                    continue
                fwd.append(f"{i}: {label}: «{m.group(0)}»")
    return broken, fwd, n


def selftest() -> int:
    """Временная папка с файлами-пробами: по хорошему и битому случаю на каждый вид ссылки и на каждое правило «не
    ссылка», по строке на каждый след."""
    import tempfile
    ok = fail = 0

    def check(name, cond):
        nonlocal ok, fail
        print(("OK   " if cond else "FAIL ") + name)
        ok, fail = ok + bool(cond), fail + (not cond)

    samples = [row["example"] for row in trace_rows("forward-only")]
    check("данные: пример каждого следа находится своим шаблоном",
          all(rx.search(s) for (_, rx), s in zip(FWD, samples)) and len(samples) == len(FWD))
    rows = notlink_rows()
    check("данные: у каждой строки «не ссылок» есть вид из списка, имя и место",
          bool(rows) and all(r["kind"] in ("project", "state", "output", "neighbor", "sibling", "value")
                             and r["name"] and r["what"] for r in rows))
    with tempfile.TemporaryDirectory(prefix="refcheck-") as td:
        d = Path(td)
        (d / "sub").mkdir()
        (d / "sub" / "doc.md").write_text("# Док\n\n## 2. Раздел\n\nтекст\n", encoding="utf-8")
        (d / "other.md").write_text("# Другой\n", encoding="utf-8")
        probe = d / "probe.md"
        probe.write_text("\n".join([
            "# Проба",
            "[есть](other.md) и [нет](missing.md); [снаружи](https://example.org) не считается.",
            "`kb/common/canon.tsv`, `kb/common/nope.tsv`, `kb/common/*.md`, `kb/nope/*.md`.",
            "`sub/doc.md §2` есть, `sub/doc.md §7` нет; `canon.tsv` — имя, `nosuchfile-xyz.md` — нет.",
            "Образцы не ссылки: `kb/<база>/…`, `scripts/{домен}/`.",
            "Адрес ux 06/01 есть, адрес ux 06/99 — нет, ux 06/01 §99.9 — нет раздела.",
            "```",
            f"`kb/в/блоке/кода.md` {samples[0]} — не проверяется",
            "```",
            "Следы: " + "; ".join(samples) + ".",
            "Не файлы: `.glb`, `.glb.json`, `cdn.example.net/npm/`, `text/plain`, `model/gltf-binary`.",
            "Битые пути: `sub/nope`, `text/09-nope`, `sub/nope.glb`, `nope.md/json`.",
            "Снимок: 01.02.2030 · среда и версия.",
            "- Проба: прогон 01.02.2030.",
        ]) + "\n", encoding="utf-8")
        broken, fwd, n = check_file(probe)
        text = "\n".join(broken)
        check("ссылка markdown: битая найдена, живая — нет", "(missing.md)" in text and "(other.md)" not in text)
        check("путь в кавычках: битый найден, живой — нет", "`kb/common/nope.tsv`" in text
              and "`kb/common/canon.tsv`" not in text)
        check("шаблон пути: без совпадений — битый", "`kb/nope/*.md`" in text and "`kb/common/*.md`" not in text)
        check("раздел: нет — битый, есть — нет находки", "`sub/doc.md §7`" in text and "`sub/doc.md §2`" not in text)
        check("голое имя: нет файла — битое, есть — нет", "nosuchfile-xyz.md" in text and "`canon.tsv`" not in text)
        check("образец `<…>`, `{…}` — не ссылка", "<база>" not in text and "{домен}" not in text)
        check("короткий адрес: нет файла и нет раздела — битые", "ux 06/99" in text and "§ 99.9" in text)
        check("блок кода не проверяется", "в/блоке" not in text and not any(f.startswith("8:") for f in fwd))
        labels = [f.split(": ")[1] for f in fwd if f.startswith("10:")]
        check("следы: каждый вид на строке следов — по одному", sorted(labels) == sorted(lbl for lbl, _ in FWD))
        check("расширение, домен с путём и тип содержимого — не ссылки",
              not any(f.startswith("11:") for f in broken) and n == 17)
        check("битый путь без расширения, папка базы под именем типа, файл с расширением и имя файла перед «/» — "
              "находки",
              all(s in text for s in ("`sub/nope`", "`text/09-nope`", "`sub/nope.glb`", "`nope.md/json`")))
        check("дата в строке «Снимок:» — не след, в обычной строке — след",
              not any(f.startswith("13:") for f in fwd) and [f for f in fwd if f.startswith("14:")] == [
                  f"14: {DATE}: «01.02.2030»"])
        check("битых ссылок — 11", len(broken) == 11)

        # правила «не ссылка»: на каждое — случай и настоящая битая ссылка рядом
        probe2 = d / "probe2.md"
        probe2.write_text("\n".join([
            "# Проба правил",
            "Вызов: `ФАЙЛ.md … [--json ОТЧЁТ]`, `SHEET.svg OUT_DIR --grid 4x2`, `OUT_DIR/_source/`; "
            "битые: `ПЛАН-ПРОБЫ.md`, `scripts/nope-tool.py --selftest`.",
            "Пояс `Europe/Moscow`; битый: `Europe/nope.md`.",
            "Виды слоёв: `business/profile`, `hypothesis-map/metric.current`, `swot/bet.promoted-to = goal:...`, "
            "`interface/block`; битый: `business/nope-kind`.",
            "Короткий адрес слоя `_templates/service-readme.md`, раскладка `jobs/*.md`, `services/*/domains/`; "
            "битые: `_templates/nope.md`, `jobs-nope/*.md`.",
            "Не здесь: `kit.json`, `_interview/`, `entrypoint/state/ajtbd/`, "
            "`.claude/skills/x/audit-state/last-report.md`, `docs/reference/x.md`, `_N/A_`, `stit-core/*`; "
            "битые: `docs/nope-dir/x.md`, `kb/common/state/x.md`, `kit-nope.json`.",
            "Корень: `docs/`, `CLAUDE.md`; образец [ссылки](...) — не ссылка.",
            "Упоминание: без «было/стало»; ни на что больше не завязанные; следы: было/стало, больше не.",
        ]) + "\n", encoding="utf-8")
        broken2, fwd2, _ = check_file(probe2)
        text2 = "\n".join(broken2)

        def line_of(k):
            return [b for b in broken2 if b.startswith(f"{k}:")]

        check("вызов: аргумент заглавными со словами или «/» — не путь; имя заглавными без продолжения и путь утилиты "
              "в вызове — битые",
              len(line_of(2)) == 2 and "`ПЛАН-ПРОБЫ.md`" in text2 and "`scripts/nope-tool.py --selftest`" in text2)
        check("часовой пояс — не ссылка, файл под именем пояса — битый",
              line_of(3) == ["3: путь `Europe/nope.md`"])
        check("вид слоя: есть файл вида — ссылка, вида нет — битый адрес",
              line_of(4) == ["4: путь `business/nope-kind`"])
        check("короткий адрес слоя и раскладка проекта — ссылки, нет файла и нет папки слоя — битые",
              line_of(5) == ["5: путь `_templates/nope.md`", "5: путь `jobs-nope/*.md`"])
        check("файлы проекта, память скиллов, соседи и значения — не ссылки; путь скилла через имя списка и имя вне "
              "списка — битые",
              line_of(6) == ["6: путь `docs/nope-dir/x.md`", "6: путь `kb/common/state/x.md`",
                             "6: путь `kit-nope.json`"])
        check("папка и файл корня — ссылки, образец ссылки markdown — не ссылка", not line_of(7))
        check("слово сравнения в ёлочках и «больше не» после «ни на что» — не след, без них — след",
              [f.split(": ", 2)[2] for f in fwd2 if f.startswith("8:")] == ["«было/стало»", "«больше не»"])
        check("битых ссылок в пробе правил — 9", len(broken2) == 9)

        # путь с `../`: дерево-образец репозитория
        root = d / "repo"
        (root / "docs" / "a").mkdir(parents=True)
        (root / ".claude" / "skills" / "s").mkdir(parents=True)
        (root / ".claude" / "skills" / "entrypoint").mkdir()
        doc, skill = root / "docs" / "a" / "x.md", root / ".claude" / "skills" / "s" / "SKILL.md"
        check("`../` к корню и выше в папку, которой нет, и в соседний чекаут — не ссылка",
              outside_repo("../../../strategy", doc, root) and outside_repo("../../_assets/icons/play.svg", doc, root)
              and outside_repo("../backend/api/openapi.yaml", skill, root))
        check("`../` в существующую папку и в папку без имени соседа ниже корня — сверяется как ссылка",
              not outside_repo("../a/nope.md", doc, root) and not outside_repo("../nope-dir/x.md", doc, root)
              and not outside_repo("../entrypoint/state/", skill, root))
        kbdoc = root / ".claude" / "skills" / "ddd" / "kb" / "creative" / "06-x" / "a.md"
        kbdoc.parent.mkdir(parents=True)
        check("`../<сосед>` внутри папки скилла — ссылка между его папками, вне скилла — соседний чекаут",
              not outside_repo("../site/x.md", kbdoc, root, kbdoc.parents[3])
              and outside_repo("../site/x.md", doc, root, kbdoc.parents[3]))

        probe3 = d / "probe3.md"
        probe3.write_text("\n".join([
            "# Проба статьи базы",
            "`kit.json`, `state/x.md`, `jobs/*.md`, `CD/rules.md`; не ссылки: `N/A`, `_N/A (stateless)_`.",
        ]) + "\n", encoding="utf-8")
        broken3, _, _ = check_file(probe3, in_kb=True)
        broken3_out, _, _ = check_file(probe3, in_kb=False)
        check("статья базы: имена списка и раскладка слоя — битые, значения — нет; папка из двух заглавных — путь",
              broken3 == ["2: путь `kit.json`", "2: путь `state/x.md`", "2: путь `jobs/*.md`", "2: путь `CD/rules.md`"]
              and broken3_out == ["2: путь `CD/rules.md`"])

        rc_plain = main([str(probe), "--quiet"])
        (d / "clean.md").write_text(f"# Чисто\n\nтекст и `kb/common/canon.tsv`; {samples[0]}\n", encoding="utf-8")
        rc_soft = main([str(d / "clean.md"), "--quiet"])
        rc_strict = main([str(d / "clean.md"), "--strict", "--quiet"])
        check("код выхода: битые — 1, следы без --strict — 0, с --strict — 1",
              rc_plain == 1 and rc_soft == 0 and rc_strict == 1)
    print(f"selftest: {ok} OK, {fail} FAIL")
    return 0 if not fail else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--strict", action="store_true", help="код 1 и при следах журнала")
    ap.add_argument("--quiet", action="store_true", help="только итоги по файлам")
    ap.add_argument("--selftest", action="store_true", help="самопроверка во временной папке, без сети")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.files:
        ap.error("назовите файлы или --selftest")
    missing = [f for f in args.files if not Path(f).resolve().exists()]
    if missing:
        print("refcheck: нет файла — " + ", ".join(missing), file=sys.stderr)
        return 2
    total_broken = total_fwd = 0
    for f in args.files:
        p = Path(f).resolve()
        broken, fwd, n = check_file(p)
        total_broken += len(broken)
        total_fwd += len(fwd)
        rel = p.relative_to(ROOT) if p.is_relative_to(ROOT) else p
        print(f"{rel}: ссылок {n}, битых {len(broken)}, следов журнала {len(fwd)}")
        if not args.quiet:
            for b in broken:
                print(f"  БИТАЯ · {b}")
            for w in fwd:
                print(f"  СЛЕД · {w}")
    print(f"итого: битых {total_broken}, следов журнала {total_fwd}")
    return 1 if total_broken or (args.strict and total_fwd) else 0


if __name__ == "__main__":
    sys.exit(main())
