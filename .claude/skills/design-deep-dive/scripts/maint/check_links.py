#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка перекрёстных ссылок, меток и структуры одной базы знаний `kb/<база>/`: то, чего не делает `refcheck.py`, —
источники `[S…]`, ролики `[V:…]` по форме, README папок против диска, метки опытов, разделы по номерам папок.

База — папка `kb/<база>/` скилла (ux, ui, site, text, creative, ai-media, 3d, claude-design); соседние базы —
папки рядом. Обходит `.md` тематических папок `NN-…` (кроме `99-raw/`), файлы `NN-….md` корня базы и корневые
`README.md`, `PLAN.md`, `CONTRADICTIONS.md` (папки `transcripts/` не разбираются); по умолчанию ещё
`99-raw/tools/README.md` и `99-raw/phase5/*.md`, если есть, — только для проверок (а) и (ж).
Проверки:

  (а) относительные ссылки на файлы и папки — `../02-strategy-messaging/03-proof-and-facts.md`, `06/02`,
      `99-raw/experiments/C/04-overcorrection/run.py`, `[текст](путь)` — существует ли цель. Многоточие `…`/`...`
      в конце — префикс, `*` — глоб; диапазоны `01–04`, `01…05` — существуют ли оба конца. Путь от корня базы внутри
      подпапки принимается (сводка INFO); `experiments/…`, `tools/…`, `notes/…`, `reports/…`, `prompts/…`, `cache/…`
      ищутся и от `99-raw/`. Пути в соседние базы (`../../ux/…`) проверяются в соседней базе (только чтение);
      записанные от корня этой базы (`../ux/` в подпапке) — INFO. Прежнее имя папки базы `<база>-research/` ведёт в
      папку базы (сводка INFO по файлу); путь в базу, которой в скилле нет, — WARN. Утилита по имени файла (`foo.py`)
      ищется в `scripts/` скилла, в `99-raw/` этой и соседних баз. Голое имя `NN-*.md` ищется в папке предыдущего пути
      той же строки, в соседней базе, названной на строке, и по всей базе.
  (б) ссылки на разделы `§N.M` — есть ли в целевом файле заголовок `## N.` / `### N.M`. Цель — ближайший путь на той
      же строке (или на предыдущей, если строка — продолжение абзаца): `` `../папка/файл.md` ``, `` `NN/NN` `` и
      NN/NN без бэктиков, `` `папка/NN` ``, `` `NN-…` ``, `` `NN` `` (файл NN папки предыдущего пути на строке или
      своей папки; у базы site после буквы автора раздела — его папка: «E `01` §2» = `04/01`), «ux 07/06»,
      «cd 06/04», «файл NN», «там же», `PLAN.md`. Форма «→ §N» — тот же файл. Ссылки на внешние документы (законы
      «ст. 5», WCAG, условия вендоров), на источники «[S1 §14]» и на отчёты и заметки («отчёт A §4», «V §4») не
      проверяются (INFO). Если цель не найдена и выбрана по умолчанию (свой файл) — WARN, если раздел есть в
      соседнем файле — WARN с подсказкой, иначе ERROR.
  (в) ссылки `[S<n>]` — определён ли номер в разделе «Источники» того же файла; если нет — в другом файле той же
      папки или базы; какие номера определены, но не используются (для README и дайджестов не считается).
  (г) ссылки `[V:<id> mm:ss]` (и несколько в одних скобках через `;`) — id ролика из 11 символов (иначе WARN),
      таймкод по форме (минуты и секунды меньше 60) — иначе ERROR. Роликов в скилле нет: ссылка сверяется только по
      форме (сводка INFO).
  (д) README папок: все ли файлы и подпапки упомянуты в `README.md`; все ли упомянутые в README файлы этой папки
      (`NN-….md`, `*.yaml`, `*.json`, `*.tsv`, `*.html`) есть на диске; заявленное в таблице README число строк.
  (е) обязательные разделы содержательного файла («Выжимка для агента», «Частые ошибки», «Чек-лист», «Открытые
      вопросы», «Источники»).
  (ж) метки `[проверено: …]`: пути `99-raw/experiments/…` и сокращения `<опыт>/<NN>` (`H/02`, `C/01–05`,
      «ai-media E/03» — опыт соседней базы) ведут на существующую папку или файл опыта; голые `[проверено]` без пути
      опыта на той же строке — сводка INFO по файлу.

Использование (пути — через `scripts/lib/kbpaths.py`, рабочая папка любая):
    python3 .claude/skills/design-deep-dive/scripts/maint/check_links.py --base site     # отчёт по базе в stdout
    python3 .claude/skills/design-deep-dive/scripts/maint/check_links.py --all           # все базы: сводки
    python3 …/check_links.py                 # база рабочей папки (запуск из kb/<база>/…), иначе все базы
    python3 …/check_links.py --root ПУТЬ     # другая папка базы (имя папки — имя базы для соседей)
    python3 …/check_links.py --out ФАЙЛ      # отчёт в файл (сводка по категориям + находки), в stdout — сводка
    python3 …/check_links.py --only а,б      # только перечисленные проверки (буквы а–ж)
    python3 …/check_links.py --json ФАЙЛ     # дополнительно сохранить находки в JSON
    python3 …/check_links.py --no-raw        # без файлов 99-raw/tools/README.md и 99-raw/phase5/*.md
    python3 …/check_links.py --quiet-info    # не печатать строки INFO (счётчики остаются)
    python3 …/check_links.py --selftest      # офлайн-тест на временной мини-раскладке kb/<база>/

Уровни: ERROR (битая ссылка, неопределённый источник), WARN (вероятная проблема, нужен человек; нет обязательного
раздела), INFO (сведения). Код возврата 1, если есть находки уровня ERROR.
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import kbpaths  # noqa: E402

CONTENT_DIRS_RE = re.compile(r"^(?!99-)\d\d-")          # тематические папки базы; 99-raw — материал к разбору
ROOT_MD_RE = re.compile(r"^\d\d-.*\.md$")                # тематический файл в корне базы (ux `00-glossary.md`)
ROOT_FILES = ["README.md", "PLAN.md", "CONTRADICTIONS.md"]
SKIP_DIR_NAMES = {"__pycache__", ".git", "transcripts", "node_modules", "assets"}
# Соседние базы — папки kb/<база>/ рядом с проверяемой. Короткое имя в тексте: «ux 07/06», «ai-media 05/03 §7»,
# «cd 06/04»; слово text в базе ещё и `slot_kind`, site — часть имён, поэтому text, site и cd распознаются только перед
# номером папки или опыта («text 03…», «site `05`», «text A/01») или с суффиксом `-research` у имени папки базы в её
# источниках; 3d в именах и значениях стоит с дефисом или подчёркиванием («3d-object», «js_3d_kb_br») и словом не считается.
SHORT_NAMES = {"ux": "ux", "ui": "ui", "site": "site", "text": "text", "creative": "creative", "ai-media": "ai-media",
               "3d": "3d", "claude-design": "claude-design", "cd": "claude-design"}
GUARDED_NAMES = {"text", "site", "cd"}
# Путь в соседнюю базу: первый сегмент после «../» — имя папки базы или прежнее имя `<имя>-research`
NB_SEG_RE = re.compile(r"^(?:\.\./)*([a-z0-9][a-z0-9-]*?)(-research)?(?=/|$)")
NEIGHBORS = ()          # папки соседних баз — configure()
NEIGHBOR_SHORT = {}     # короткое имя в тексте → папка соседа — configure()
NB = ""                 # регулярка короткого имени соседа — configure()
NB_WORD_RE = None
PATH_EXTS = (".md", ".py", ".sh", ".css", ".html", ".json", ".txt", ".js", ".png", ".jsonl", ".yml", ".yaml",
             ".jpg", ".avif", ".webp", ".mp4", ".webm", ".svg", ".cube", ".csv", ".tsv", ".onnx")
LOCAL_SUBDIRS = ("digests/", "transcripts/", "examples/", "tools/", "cache/", "notes/", "reports/", "prompts/",
                 "experiments/", "lexicon/", "facts/", "youtube/", "schemas/")
RAW_SUBDIRS = {"experiments/": "99-raw/", "tools/": "99-raw/", "notes/": "99-raw/", "reports/": "99-raw/",
               "prompts/": "99-raw/", "cache/": "99-raw/", "youtube/": "99-raw/"}
EXTERNAL_DOC_MARKERS = ("Module", "WCAG", "Understanding", "ISO ", "RFC", "SC ", "spec", "Spec", "стандарт", "ст.",
                        "стать", "Art.", "Article", "AI Act", "Руководств", "Кодекс", "Code of Practice", "Measure",
                        "DT", "Developer Terms", "Terms", "ToS", "ToU", "AUP", "оферт", "C2PA", "IPTC", "GB ", "ГК",
                        "ФЗ", "закон", "Закон", "Guidance", "Guidelines", "Recital", "пункт", "Regulation",
                        "Регламент", "Policy", "policy", "лицензи", "License", "NY", "Civil", "CFR", "U.S.C",
                        "Cal.", "Code", "CSS ", "Images 3", "Getting Started", "Help Center", "docs", "документаци",
                        "гайд", "README", "helper", "заметок", "notes", "-notes", "Кодекса", "Цифрового", "помощник",
                        "условия", "Условия", "Prohibited", "taste", "humanizer", "SKILL", "SQRG", "Rater",
                        "Search Quality", "ЗоЗПП", "КоАП", "ГОСТ", "Пленум", "постановлени",
                        "приказ", "Директив", "Directive", "UCPD", "FTC", "GDPR", "DSA", "контракт", "контракта")
AGENT_TOKEN = r"(?:A|B|M2?|C|E|F2?|G2?|H2?|P|I|V|W2?|J|K[23]?|X2?|S[12]?)"
# буква автора раздела → папка его файлов (форма «E `01` §2», «B1 `02` §4», «G 03 §5»); такие ссылки пишет база site
AGENT_FOLDERS = {"site": {"A": "01", "B": "02", "M": "02", "M2": "02", "C": "03", "E": "04", "F": "05", "F2": "05",
                          "G": "06", "G2": "06", "H": "07", "H2": "07", "P": "07", "I": "08", "K": "09", "K2": "09",
                          "K3": "09", "J": "10", "V": "91", "W": "91", "W2": "91"}}
AGENT_FOLDER = {}       # у проверяемой базы — configure()
# пути, которые создаются при исполнении и в базе не хранятся
RUNTIME_PATHS = ()
# просмотренные не-ссылки: (файл, токен)
KNOWN_NON_LINKS = set()
# файлы, которым разделы формата содержательного файла не нужны: анкета, шаблон, план, промты (README и дайджесты
# проверяются своими правилами)
FORMAT_EXEMPT = ()
RANGE_SEG_RE = re.compile(r"^(?P<p1>(?:[A-Za-z][A-Za-z_]*\d?-|[A-Za-z_]+)?)(?P<a>\d+)(?:…|\.\.\.|–|\.\.)(?P<p2>[A-Za-z][A-Za-z_]*\d?-|[A-Za-z_]+)?(?P<b>\d+)(?P<post>[^/…]*)$")

REQUIRED_DEFAULT = [
    ("Выжимка для агента", ("выжимка",)),
    ("Частые ошибки", ("частые ошибки", "типичные ошибки", "ошибок", "ошибки")),
    ("Чек-лист", ("чек-лист", "чеклист")),
    ("Открытые вопросы", ("открытые вопросы",)),
    ("Источники", ("источники",)),
]

HEADING_RE = re.compile(r"^(#{1,4})\s+(.*?)\s*$")
NUM_HEADING_RE = re.compile(r"^(?:Шаг\s+)?(\d+(?:\.\d+)*[a-z]?)\.?(?:\s+|$)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
BARE_PATH_RE = re.compile(r"(?<![\w`/.])((?:\.\./)+|\./)?(\d\d-[a-z][\w-]*/[\w./…*–-]+)")
S_REF_RE = re.compile(r"\[([SM])(\d+[a-z]?)\]")
V_REF_RE = re.compile(r"\[V:([^\]\n]*)\]")
V_ID_RE = re.compile(r"^\s*([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")
TIMECODE_RE = re.compile(r"(?<![\d:])(\d{1,2}(?::\d{2}){1,2})(?![\d:])")
SECT_RE = re.compile(r"§\s?(\d+(?:\.\d+)*[a-z]?)")
RANGE_TAIL_RE = re.compile(r"^\s*[–\-]\s*§?(\d+(?:\.\d+)*[a-z]?)")
FILE_NN_RE = re.compile(r"файл[а-яё]*\s+(\d\d)\b")
FOLDER_NN_RE = re.compile(r"^((?:\.\./)*)((?:[\w.…-]+/)*[\w.…-]+)/(\d\d)$")
PREFIX_SAME_RE = re.compile(r"^(\d\d)-(?:…|\.\.\.)(?:/README\.md)?$")
PREFIX_FOLDER_FILE_RE = re.compile(r"^((?:\.\./)*)(\d\d)-(?:…|\.\.\.)/(\d\d)$")
CHAIN_SEP_RE = re.compile(r"^[`\s]*(?:§\s?\d+(?:\.\d+)*[a-z]?(?:\s*[–-]\s*§?\d+(?:\.\d+)*)?(?:\s*п\.\s*\d+(?:[–-]\d+)?)?[\s,;]*)*(?:и\s+)?[`\s,;]*$")
CHAIN_RE = re.compile(r"§[\d.a-z]+(?:\s*(?:п\.\s*\d+|строка\s*\d+))?\s*[,;–\-]?\s*(?:и\s+)?$")
PLACEHOLDER_RE = re.compile(r"wave[NX]\b|<[^>]*>|\{\{|\bNN\b|\bNN-|-0N-|\b0N\b|/X-notes|YYYY|ГГГГ|\$\(|<агент>")
README_ROW_RE = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|.*\|\s*(\d+)\s*\|\s*$")
VERIFIED_RE = re.compile(r"\[(проверено|стенд)([^\]\n]*)\]")
# внутри метки [проверено: …] буква опыта — любая заглавная латинская с необязательной цифрой (A, B1, E3, опыты соседей)
EXP_SHORT_RE = None     # configure()
EXP_PATH_RE = None      # configure()


def configure(base):
    """Соседи проверяемой базы: все базы `kb/`, кроме неё (base — имя папки базы или None — все базы)."""
    global NEIGHBORS, NEIGHBOR_SHORT, NB, NB_WORD_RE, EXP_SHORT_RE, EXP_PATH_RE, AGENT_FOLDER
    NEIGHBOR_SHORT = {k: v for k, v in SHORT_NAMES.items() if v != base}
    NEIGHBORS = tuple(dict.fromkeys(NEIGHBOR_SHORT.values()))
    alts = [re.escape(k) + (r"(?=-research|\s+`?\d\d|\s+[A-Z]\d?/\d\d)" if k in GUARDED_NAMES else "")
            for k in sorted(NEIGHBOR_SHORT, key=len, reverse=True)]
    NB = "(" + "|".join(alts) + ")"
    NB_WORD_RE = re.compile(r"(?<![\w.-])" + NB + r"(?:-research)?(?![\w-]|\.\w)")
    EXP_SHORT_RE = re.compile(r"(?<![\w/.-])(?:" + NB + r"\s+)?([A-Z]\d?)/(\d\d)(?:[–-](\d\d))?([a-z]?)(?![\w])")
    EXP_PATH_RE = re.compile(r"(?:(?:\.\./)+(" + "|".join(re.escape(x) for x in NEIGHBORS) + r")(?:-research)?/)?"
                             r"99-raw/experiments/([\w-]+)/([\w.…-]+)")
    AGENT_FOLDER = AGENT_FOLDERS.get(base, {})


configure(None)


class Report:
    def __init__(self):
        self.items = []  # (check, level, path, line, message)
        self.counts = defaultdict(lambda: defaultdict(int))
        self.checked = defaultdict(int)
        self.cats = defaultdict(lambda: defaultdict(int))

    def add(self, check, level, path, line, message):
        self.items.append((check, level, path, line, message))
        self.counts[check][level] += 1

    def tick(self, check, n=1):
        self.checked[check] += n

    def cat(self, check, name, n=1):
        """Счётчик категории внутри проверки (для сводки в шапке отчёта)."""
        self.cats[check][name] += n


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def is_raw(relpath):
    return relpath.startswith("99-raw/")


def collect_files(root, with_raw):
    files = []
    for name in sorted(os.listdir(root)):
        full = os.path.join(root, name)
        if os.path.isdir(full) and CONTENT_DIRS_RE.match(name):
            for dirpath, dirnames, filenames in os.walk(full):
                dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIR_NAMES)
                for fn in sorted(filenames):
                    if fn.endswith(".md"):
                        files.append(os.path.join(dirpath, fn))
        elif os.path.isfile(full) and (name in ROOT_FILES or ROOT_MD_RE.match(name)):
            files.append(full)
    if with_raw:
        for p in [os.path.join(root, "99-raw", "tools", "README.md")] + sorted(
                glob.glob(os.path.join(root, "99-raw", "phase5", "*.md"))):
            if os.path.isfile(p):
                files.append(p)
    return files


def strip_fences(lines):
    """Флаги «строка внутри блока кода»."""
    inside = False
    flags = []
    for ln in lines:
        if FENCE_RE.match(ln):
            inside = not inside
            flags.append(True)
            continue
        flags.append(inside)
    return flags


def heading_index(lines):
    """Номера разделов файла и список заголовков (номер строки, уровень, текст)."""
    nums = {}
    heads = []
    infence = strip_fences(lines)
    for i, ln in enumerate(lines):
        if infence[i]:
            continue
        m = HEADING_RE.match(ln)
        if not m:
            continue
        level, text = len(m.group(1)), m.group(2)
        heads.append((i + 1, level, text))
        mr = re.match(r"^(\d+(?:\.\d+)*)[–-](\d+(?:\.\d+)*)\.?(?:\s+|$)", text)
        if mr and level >= 2:  # «### 6.2–6.3. Финансы» — оба конца и середина
            a, b = mr.group(1), mr.group(2)
            nums.setdefault(a, i)
            nums.setdefault(b, i)
            pa, pb = a.rsplit(".", 1) if "." in a else ("", a), b.rsplit(".", 1) if "." in b else ("", b)
            if pa[0] == pb[0] and pa[1].isdigit() and pb[1].isdigit():
                for k in range(int(pa[1]), int(pb[1]) + 1):
                    nums.setdefault((pa[0] + "." if pa[0] else "") + str(k), i)
            continue
        mn = NUM_HEADING_RE.match(text)
        if mn and level >= 2:
            nums.setdefault(mn.group(1), i)
    return nums, heads


def sources_span(lines, heads):
    """Границы раздела «Источники» (последний заголовок уровня 2, начинающийся со слова «источники»)."""
    start = None
    fallback = None
    for lineno, level, text in heads:
        t = re.sub(r"^\d+(\.\d+)*\.?\s*", "", text).lower()
        if level == 2 and t.startswith("источник"):
            start = lineno - 1
        elif level == 2 and "источник" in t and not t.startswith("ссылки"):
            fallback = lineno - 1
    if start is None:
        start = fallback
    if start is None:
        return None, None
    end = len(lines)
    for lineno, level, text in heads:
        if lineno - 1 > start and level <= 2:
            end = lineno - 1
            break
    return start, end


def clean_path_token(tok):
    tok = tok.strip()
    if tok.endswith("..."):
        tok = tok[:-3].rstrip(".,;:)»”\"'") + "..."
    else:
        tok = tok.rstrip(".,;:)»”\"'")
    tok = tok.split("#", 1)[0]
    tok = re.sub(r":\d+(?:-\d+)?$", "", tok)  # «путь:строка»
    tok = tok.split(" §", 1)[0].strip()
    return tok


def neighbor_split(tok):
    """Путь в соседнюю базу → (папка соседа, хвост пути) или (None, None). Первый сегмент после «../» — имя папки
    соседа (`../../ux/07-…`) или прежнее имя `<имя>-research`: у базы скилла оно ведёт в её папку, у базы, которой в
    скилле нет, — в папку, которой нет на диске."""
    m = NB_SEG_RE.match(tok)
    if not m:
        return None, None
    name, legacy = m.group(1), m.group(2)
    if legacy:
        folder = name if name in kbpaths.BASES else name + legacy
    elif name in NEIGHBORS:
        folder = name
    else:
        return None, None
    return folder, tok[m.end():].lstrip("/")


def neighbor_of(tok):
    return neighbor_split(tok)[0]


def legacy_name(tok):
    """Путь записан прежним именем папки базы скилла (`ux-research/…` → `ux/…`)."""
    m = NB_SEG_RE.match(tok)
    return bool(m and m.group(2) and m.group(1) in kbpaths.BASES)


def neighbor_on_line(text):
    """Соседняя база, названная на строке обычным текстом («ui 11/…», «ui-research, `11-…`», «blender `05`»)."""
    m = None
    for m in NB_WORD_RE.finditer(text):
        pass
    return NEIGHBOR_SHORT[m.group(1)] if m else None


def path_candidates(root, filedir, tok, line_dirs=(), line_neighbor=None):
    """Кандидаты (как, путь): от файла, от корня, от 99-raw, от папки предыдущего пути строки, в соседней базе."""
    cands = [("dir", os.path.normpath(os.path.join(filedir, tok)))]
    if not tok.startswith(("../", "./")):
        cands.append(("root", os.path.normpath(os.path.join(root, tok))))
        for sub, pre in RAW_SUBDIRS.items():
            if tok.startswith(sub):
                cands.append(("raw", os.path.normpath(os.path.join(root, pre, tok))))
        if tok.startswith(LOCAL_SUBDIRS):
            cands.append(("parent", os.path.normpath(os.path.join(filedir, "..", tok))))
    else:
        cands.append(("root", os.path.normpath(os.path.join(root, tok))))  # `../папка/…` записано от корня базы
    for d in line_dirs:
        cands.append(("line-folder", os.path.normpath(os.path.join(d, tok))))
    nb, tail = neighbor_split(tok)
    if nb:
        cands.append(("neighbor", os.path.normpath(os.path.join(root, "..", nb, tail))))
    elif line_neighbor and not tok.startswith("../"):
        cands.append(("line-neighbor", os.path.normpath(os.path.join(root, "..", line_neighbor, tok))))
        for d in glob.glob(os.path.join(root, "..", line_neighbor, "[0-9][0-9]-*")):
            if os.path.isdir(d) and "/" not in tok:
                cands.append(("line-neighbor", os.path.normpath(os.path.join(d, tok))))
    out = []
    seen = set()
    for how, c in cands:
        if c not in seen:
            seen.add(c)
            out.append((how, c))
    return out


def resolve_exists(cand):
    """Существует ли цель; диапазон `01–04`/`01…05`/`G-01…G-06` — оба конца; `…`/`...` в конце — префикс; `*` — глоб."""
    head, seg = os.path.split(cand)
    rm = RANGE_SEG_RE.match(seg)
    if rm and head:
        hdirs = glob.glob(head.replace("…", "*")) if ("…" in head or "*" in head) else [head]
        p2 = rm.group("p2") if rm.group("p2") is not None else rm.group("p1")
        for hd in hdirs:
            a = glob.glob(os.path.join(hd, rm.group("p1") + rm.group("a") + "*" + rm.group("post")))
            b = glob.glob(os.path.join(hd, p2 + rm.group("b") + "*" + rm.group("post")))
            if not a and rm.group("post"):
                a = glob.glob(os.path.join(hd, rm.group("p1") + rm.group("a") + rm.group("post")))
                b = glob.glob(os.path.join(hd, p2 + rm.group("b") + rm.group("post")))
            if a and b:
                return True, a + b
        return False, []
    if "…" in cand or "*" in cand or "..." in cand:
        pattern = cand.replace("…", "*").replace("...", "*")
        matches = glob.glob(pattern)
        if not matches and pattern.endswith("/"):
            matches = glob.glob(pattern.rstrip("/"))
        return bool(matches), matches
    return os.path.exists(cand), ([cand] if os.path.exists(cand) else [])


def looks_like_repo_path(tok, top_dirs):
    if not tok or " " in tok or "$" in tok or "<" in tok or ">" in tok or "{" in tok or "=" in tok:
        return False
    if tok.startswith(("http://", "https://", "mailto:", "#", "~", "/")):
        return False
    if tok.endswith(".mdx"):
        return False  # файлы документации polza (`docs-repo/`), не пути базы
    if tok.startswith(("../", "./")):
        return True
    if neighbor_of(tok):
        return True
    first = tok.split("/", 1)[0]
    if first in top_dirs:
        return True
    if tok.startswith(LOCAL_SUBDIRS):
        return True
    if "/" not in tok and tok.endswith(".md") and (tok in ("README.md", "PLAN.md", "CONTRADICTIONS.md") or re.match(r"^\d\d-", tok)):
        return True
    return False


def find_nn_file(dirpath, nn, md_only=True):
    if not dirpath or not os.path.isdir(dirpath):
        return None
    pat = "%s-*.md" % nn if md_only else "%s-*" % nn
    matches = sorted(glob.glob(os.path.join(dirpath, pat)))
    matches = [m for m in matches if os.path.basename(m) not in ("README.md", "glossary.md")]
    if len(matches) == 1:
        return matches[0]
    if not md_only and matches:
        return matches[0]
    return None


def find_folder(root, filedir, prefix_dots, name_or_nn):
    """Папка по имени (`08-image-post-processing`, `02-site-types/examples`, `07-…`) или номеру (`08`), от файла или
    корня."""
    for base in (os.path.normpath(os.path.join(filedir, prefix_dots)), root):
        if re.match(r"^\d\d$", name_or_nn):
            hits = [h for h in sorted(glob.glob(os.path.join(base, name_or_nn + "-*"))) if os.path.isdir(h)]
            if len(hits) == 1:
                return hits[0]
        elif "…" in name_or_nn or "*" in name_or_nn:
            hits = [h for h in sorted(glob.glob(os.path.join(base, name_or_nn.replace("…", "*")))) if os.path.isdir(h)]
            if len(hits) == 1:
                return hits[0]
        else:
            cand = os.path.join(base, name_or_nn)
            if os.path.isdir(cand):
                return cand
    return None


def neighbor_folder(root, nb, nn):
    base = os.path.normpath(os.path.join(root, "..", nb))
    hits = [h for h in sorted(glob.glob(os.path.join(base, nn + "-*"))) if os.path.isdir(h)]
    return hits[0] if len(hits) == 1 else None


def agent_folder(root, agent):
    nn = AGENT_FOLDER.get(agent)
    return find_folder(root, root, "", nn) if nn else None


# ----------------------------------------------------------------------------------------------------- (а)
def check_paths(root, relpath, lines, infence, rep, top_dirs, tools_names, basename_index):
    filedir = os.path.dirname(os.path.join(root, relpath))
    seen = set()
    root_relative = []
    neighbor_rootrel = []
    legacy = []  # пути в соседние базы по прежнему имени папки
    prev_dirs, prev_nb = [], None
    open_tail = None  # код в бэктиках, начатый на прошлой строке и не закрытый («`../ux/06-…/` + перенос)
    for i, ln in enumerate(lines):
        toks = []
        for m in MD_LINK_RE.finditer(ln):
            toks.append(m.group(1))
        work = ln
        if not infence[i]:
            if open_tail is not None:
                k = ln.find("`")
                if k >= 0:
                    toks.append(open_tail + ln[:k].strip())  # путь, разорванный переносом строки
                    work = ln[k + 1:]
                open_tail = None
            for m in BACKTICK_RE.finditer(work):
                t = m.group(1)
                if "/" in t or t.endswith(PATH_EXTS):
                    toks.append(t)
            stripped = BACKTICK_RE.sub(" ", work)
            for m in BARE_PATH_RE.finditer(stripped):
                toks.append((m.group(1) or "") + m.group(2))
            if work.count("`") % 2 == 1:
                open_tail = work[work.rfind("`") + 1:].strip()
        else:
            open_tail = None
        cont = i > 0 and lines[i - 1].strip() != "" and not re.match(r"^\s*(?:[-*]\s|\||#|\d+\.\s)", ln)
        line_dirs = list(prev_dirs) if cont else []
        line_nb = neighbor_on_line(ln) or (prev_nb if cont else None)
        for raw in toks:
            tok = clean_path_token(raw)
            if not tok:
                continue
            key = (i, tok)
            if key in seen:
                continue
            seen.add(key)
            if (relpath, tok) in KNOWN_NON_LINKS:
                continue
            if "/" not in tok and tok.endswith((".py", ".sh", ".mjs")):
                rep.tick("а")
                rep.cat("а", "утилита по имени файла")
                if tok not in tools_names:
                    hits = glob.glob(os.path.join(root, "99-raw", "**", tok), recursive=True)
                    nb_hits = []
                    if not hits:
                        for nb in NEIGHBORS:
                            nb_hits += glob.glob(os.path.join(root, "..", nb, "99-raw", "**", tok), recursive=True)
                            nb_hits += glob.glob(os.path.join(root, "..", nb, "03-bpy-api", "snippets", tok))
                    if hits or nb_hits:
                        pass
                    elif re.search(r"99-raw/tools|python3 |venv", ln):
                        rep.add("а", "WARN", relpath, i + 1, "утилита `%s` не найдена ни в scripts/ скилла, ни в 99-raw/ этой и соседних баз" % tok)
                    else:
                        rep.add("а", "INFO", relpath, i + 1, "`%s`: нет в scripts/ скилла и в 99-raw/ этой и соседних баз — вероятно, файл внешнего репозитория" % tok)
                continue
            if not looks_like_repo_path(tok, top_dirs):
                continue
            rep.tick("а")
            if PLACEHOLDER_RE.search(tok):
                rep.cat("а", "шаблон пути (не проверяется)")
                rep.add("а", "INFO", relpath, i + 1, "`%s`: шаблон пути, не проверяется" % tok)
                continue
            if any(tok.rstrip("/").endswith(rp) or tok.startswith(rp) for rp in RUNTIME_PATHS):
                rep.add("а", "INFO", relpath, i + 1, "`%s`: создаётся при исполнении, в базе не хранится" % tok)
                continue
            # `NN/NN` — папка и файл по номерам
            sm = re.match(r"^(\d\d)/(\d\d)$", tok)
            if sm:
                if line_nb:
                    folder = neighbor_folder(root, line_nb, sm.group(1))
                    target = find_nn_file(folder, sm.group(2)) if folder else None
                    if target:
                        continue
                folder = find_folder(root, filedir, "", sm.group(1))
                target = find_nn_file(folder, sm.group(2)) if folder else None
                if target is None:
                    rep.cat("а", "битая")
                    rep.add("а", "ERROR", relpath, i + 1, "`%s`: папки или файла с такими номерами нет" % tok)
                else:
                    rep.cat("а", "NN/NN этой базы — есть")
                    line_dirs.append(os.path.dirname(target))
                continue
            fm = FOLDER_NN_RE.match(tok) or PREFIX_FOLDER_FILE_RE.match(tok)
            if fm:
                target = None
                folder = None
                if neighbor_of(tok):
                    nb = neighbor_of(tok)
                    tail = neighbor_split(fm.group(2))[1] if neighbor_of(fm.group(2)) else ""
                    folder = find_folder(os.path.normpath(os.path.join(root, "..", nb)), root, "", tail) if tail else None
                else:
                    folder = find_folder(root, filedir, fm.group(1), fm.group(2))
                    if folder is None:
                        for sub, pre in RAW_SUBDIRS.items():
                            if fm.group(2).startswith(sub.rstrip("/")):
                                folder = find_folder(root, os.path.join(root, pre), "", fm.group(2))
                if folder is not None:
                    target = find_nn_file(folder, fm.group(3), md_only=False)
                if target is None and not neighbor_of(tok) and not fm.group(1):
                    # `pages/07` после пути `../10-web-integration/…` на той же строке или после буквы агента «J (`01`, `pages/08`)»
                    pos = ln.find(raw)
                    agents = [a.group(1) for a in re.finditer(r"(?:^|[\s(,;\[])(" + AGENT_TOKEN + r")\s*[(`]", ln[: pos if pos >= 0 else len(ln)])]
                    extra = list(line_dirs[::-1]) + [agent_folder(root, a) for a in agents[::-1] if agent_folder(root, a)]
                    for d in extra:
                        f2 = find_folder(d, d, "", fm.group(2))
                        t2 = find_nn_file(f2, fm.group(3), md_only=False) if f2 else None
                        if t2:
                            folder, target = f2, t2
                            break
                if target is None and line_nb and not neighbor_of(tok):
                    nroot = os.path.normpath(os.path.join(root, "..", line_nb))
                    nfolder = find_folder(nroot, os.path.join(nroot, rel(root, filedir)), "", fm.group(2))
                    ntarget = find_nn_file(nfolder, fm.group(3), md_only=False) if nfolder else None
                    if ntarget:
                        rep.cat("а", "в соседней базе по её имени на строке")
                        rep.add("а", "INFO", relpath, i + 1, "`%s`: в соседней базе %s (`%s`), база названа на строке" % (tok, line_nb, rel(nroot, ntarget)))
                        continue
                if target is None:
                    rep.cat("а", "битая")
                    rep.add("а", "ERROR", relpath, i + 1, "`%s`: файла или папки с таким номером нет" % tok)
                else:
                    rep.cat("а", "папка/NN — есть")
                    line_dirs.append(folder)
                continue
            cands = path_candidates(root, filedir, tok, line_dirs[::-1], line_nb)
            ok = False
            how = None
            found = None
            for h, c in cands:
                exists, matches = resolve_exists(c)
                if exists:
                    ok, how, found = True, h, matches[0]
                    break
            if ok:
                d = found if os.path.isdir(found) else os.path.dirname(found)
                line_dirs.append(d)
                rep.cat("а", {"dir": "путь от файла — есть", "root": "путь от корня базы — есть", "raw": "путь от 99-raw — есть",
                              "parent": "путь от родительской папки — есть", "line-folder": "по папке пути на строке — есть",
                              "neighbor": "соседняя база — есть", "line-neighbor": "соседняя база по имени на строке — есть"}.get(how, how))
                if how == "neighbor" and legacy_name(tok):
                    legacy.append(tok)
            if not ok:
                base = os.path.basename(tok.rstrip("/"))
                nb = neighbor_of(tok)
                glob_hits = []
                if not tok.startswith("../") and not RANGE_SEG_RE.match(os.path.basename(tok)):
                    tail = tok.lstrip("./").replace("…", "*")
                    glob_hits = [g for g in glob.glob(os.path.join(root, "**", tail), recursive=True)
                                 if "/cache/" not in g and "/venv-" not in g]
                if nb:
                    nb_exists = os.path.isdir(os.path.join(root, "..", nb))
                    rep.add("а", "ERROR" if nb_exists else "WARN", relpath, i + 1,
                            "`%s`: цель в соседней базе %s не найдена%s" % (tok, nb, "" if nb_exists else " (такой базы в скилле нет)"))
                    rep.cat("а", "битая в соседней базе" if nb_exists else "базы нет в скилле")
                elif glob_hits:
                    rep.cat("а", "не рядом, найдено в другой папке (INFO)")
                    rep.add("а", "INFO", relpath, i + 1, "`%s`: рядом с файлом нет, найдено в `%s`" % (tok, rel(root, os.path.dirname(glob_hits[0]))))
                elif "/" not in tok and base in basename_index and len(basename_index[base]) == 1:
                    rep.cat("а", "не рядом, одноимённый файл базы (INFO)")
                    rep.add("а", "INFO", relpath, i + 1, "`%s`: рядом с файлом нет, лежит в `%s/`" % (tok, os.path.dirname(basename_index[base][0])))
                elif "/" not in tok and base in basename_index:
                    rep.cat("а", "неоднозначное имя (WARN)")
                    rep.add("а", "WARN", relpath, i + 1, "`%s`: рядом с файлом нет; одноимённые файлы: %s" % (tok, ", ".join(basename_index[base][:4])))
                elif "…" in tok or "*" in tok or "..." in tok or RANGE_SEG_RE.match(os.path.basename(tok)):
                    rep.cat("а", "битая")
                    rep.add("а", "ERROR", relpath, i + 1, "`%s`: по префиксу, глобу или диапазону ничего не найдено" % tok)
                else:
                    rep.cat("а", "битая")
                    rep.add("а", "ERROR", relpath, i + 1, "`%s`: файл или папка не существует" % tok)
            elif how == "root" and tok.startswith("../") and neighbor_of(tok) is None:
                root_relative.append(tok)
            elif how == "neighbor" and tok.startswith("../") and os.path.dirname(relpath) and not tok.startswith("../../"):
                neighbor_rootrel.append(tok)
            elif how == "root" and not tok.startswith(("../", "./")) and os.path.dirname(relpath):
                root_relative.append(tok)
            elif how == "line-neighbor":
                rep.add("а", "INFO", relpath, i + 1, "`%s`: найдено в соседней базе %s по имени базы на строке; путь неполный" % (tok, line_nb))
            elif how == "parent":
                rep.add("а", "INFO", relpath, i + 1, "`%s`: путь записан относительно родительской папки" % tok)
        prev_dirs, prev_nb = line_dirs, line_nb
    if root_relative:
        uniq = sorted(set(root_relative))
        rep.add("а", "INFO", relpath, 0, "%d путей записаны от корня базы, а не относительно файла (например `%s`)" % (len(root_relative), uniq[0]))
    if neighbor_rootrel:
        uniq = sorted(set(neighbor_rootrel))
        rep.add("а", "INFO", relpath, 0, "%d путей в соседние базы записаны от корня этой базы (`%s`); от файла — `../%s`" % (len(neighbor_rootrel), uniq[0], uniq[0]))
    if legacy:
        uniq = sorted(set(legacy))
        rep.cat("а", "путь в соседнюю базу по прежнему имени папки (INFO)", len(legacy))
        rep.add("а", "INFO", relpath, 0, "%d путей в соседние базы записаны прежним именем папки `<база>-research/` (например `%s`); папка базы — `kb/<база>/`" % (len(legacy), uniq[0]))


# ----------------------------------------------------------------------------------------------------- (б)
def target_from_context(root, relpath, filedir, text, last_target, basename_index=None, split_pos=0):
    """Файл-цель по тексту перед ссылкой §. Возвращает (abs_path|'FOLDER'|'EXTERNAL'|None, how, from_prev_line)."""
    best = None
    last_dir = None
    last_nb = None  # (база, позиция конца) последней ссылки на файл соседа — для цепочки «`ux 07/01` §3.3, `07/03` §11.1»

    def consider(pos, path, how):
        nonlocal best
        if path and (best is None or pos > best[0]):
            best = (pos, path, how)

    for m in BACKTICK_RE.finditer(text):
        raw = m.group(1)
        tok = clean_path_token(raw)
        pos = m.end()
        pre = text[: m.start()]
        nbt = re.match(r"^" + NB + r"(?:-research)?\s+(\d\d)/(\d\d)$", raw.strip())
        if nbt:  # «`ux 07/06`», «`ai-media 01/01`»
            nbk = NEIGHBOR_SHORT[nbt.group(1)]
            folder = neighbor_folder(root, nbk, nbt.group(2))
            t = find_nn_file(folder, nbt.group(3)) if folder else None
            consider(pos, t or ("MISSING:%s" % raw.strip()), "neighbor nn/nn")
            last_nb = (nbk, pos)
            if t:
                last_dir = os.path.dirname(t)
            continue
        if re.match(r"^" + NB + r"(?:-research)?\s+(\d\d)$", raw.strip()):
            consider(pos, "FOLDER", "neighbor-folder")
            continue
        if re.match(r"^\d\d$", tok):
            nbm = re.search(r"(?<![\w-])" + NB + r"(?:-research)?\s*$", pre)
            agm = re.search(r"(?:^|[\s(\[;,])(" + AGENT_TOKEN + r")\s*\(?\s*$", pre)  # и «G (`02`»
            if nbm:
                consider(pos, "FOLDER", "neighbor-folder")
            elif agm and agent_folder(root, agm.group(1)):
                consider(pos, find_nn_file(agent_folder(root, agm.group(1)), tok), "agent-folder nn")
            elif last_dir:
                consider(pos, find_nn_file(last_dir, tok), "nn-line-folder")
            else:
                t = find_nn_file(filedir, tok)
                up = filedir
                while t is None and os.path.dirname(up).startswith(root) and os.path.dirname(up) != root:
                    up = os.path.dirname(up)
                    t = find_nn_file(up, tok)
                consider(pos, t, "nn-same-folder")
            continue
        pm = PREFIX_SAME_RE.match(tok)
        if pm:
            consider(pos, find_nn_file(filedir, pm.group(1)), "prefix-same")
            continue
        sm = re.match(r"^(\d\d)/(\d\d)$", tok)
        if sm:
            nbm = re.search(r"(?<![\w-])" + NB + r"(?:-research)?[\s,]*$", pre)
            nbk = NEIGHBOR_SHORT[nbm.group(1)] if nbm else None
            if not nbk and last_nb and CHAIN_SEP_RE.match(text[last_nb[1]: m.start()]):
                nbk = last_nb[0]  # цепочка после ссылки на соседа
            if nbk:
                folder = neighbor_folder(root, nbk, sm.group(1))
                t = find_nn_file(folder, sm.group(2)) if folder else None
                consider(pos, t or ("MISSING:%s %s" % (nbk, tok)), "neighbor nn/nn")
                last_nb = (nbk, pos)
                if t:
                    last_dir = os.path.dirname(t)
            else:
                folder = find_folder(root, filedir, "", sm.group(1))
                t = find_nn_file(folder, sm.group(2)) if folder else None
                consider(pos, t, "nn/nn")
                if t:
                    last_dir = os.path.dirname(t)
            continue
        fm = PREFIX_FOLDER_FILE_RE.match(tok)
        if fm:
            folder = find_folder(root, filedir, fm.group(1), fm.group(2))
            consider(pos, find_nn_file(folder, fm.group(3)) if folder else None, "prefix-folder-nn")
            continue
        fm = FOLDER_NN_RE.match(tok)
        if fm:
            t = None
            if not neighbor_of(tok):
                folder = find_folder(root, filedir, fm.group(1), fm.group(2))
                t = find_nn_file(folder, fm.group(3)) if folder else None
                how_f = "folder-nn"
            nb = neighbor_of(tok) or (neighbor_on_line(pre) if not tok.startswith("../") else None)
            if t is None and nb:
                tail = neighbor_split(fm.group(2))[1] if neighbor_of(fm.group(2)) else fm.group(2)
                nroot = os.path.normpath(os.path.join(root, "..", nb))
                folder = find_folder(nroot, nroot, "", tail) if tail else None
                t = find_nn_file(folder, fm.group(3)) if folder else None
                how_f = "neighbor folder-nn"
            consider(pos, t, how_f)
            if t:
                last_dir = os.path.dirname(t)
            continue
        if tok.endswith("/") or re.match(r"^(?:\.\./)*\d\d-[a-z][\w-]*/(?:…|\.\.\.)$", tok):
            consider(pos, "FOLDER", "folder")
            continue
        if tok.startswith(("http", "$")) or ("/" not in tok and not tok.endswith(".md")):
            continue
        nb_line = neighbor_on_line(pre) if not neighbor_of(tok) else None
        if "…" in tok or "*" in tok or "..." in tok:
            for _, c in path_candidates(root, filedir, tok, [last_dir] if last_dir else [], nb_line):
                ok, matches = resolve_exists(c)
                if ok:
                    md = [x for x in matches if x.endswith(".md")]
                    if len(md) == 1:
                        consider(pos, md[0], "path-glob")
                        last_dir = os.path.dirname(md[0])
                    break
            continue
        if not tok.endswith(".md"):
            continue
        found = None
        for _, c in path_candidates(root, filedir, tok, [last_dir] if last_dir else [], nb_line):
            if os.path.exists(c):
                found = c
                break
        if found is None and "/" not in tok and basename_index and len(basename_index.get(tok, [])) == 1:
            found = os.path.join(root, basename_index[tok][0])
        if found:
            consider(pos, found, "path")
            last_dir = os.path.dirname(found)
    # соседняя база и папки базы без бэктиков: «ui 07/02 §2.1», «E 13/01 §4.2», «(02/05 §9)», «3d 01 §9.5»
    chain_nb = None
    for m in re.finditer(r"(?<![\w/`.])(?:(?<![\w-])" + NB + r"(?:-research)?\s+)?(\d\d)/(\d\d)(?![\w/`])", text):
        nbk = m.group(1)
        if not nbk and chain_nb and re.match(r"^\s*,\s*$", text[chain_nb[1]: m.start()]):
            nbk = chain_nb[0]  # «ui 07/02, 12/01 §6.2» — префикс базы действует на весь перечень
        if nbk:
            folder = neighbor_folder(root, NEIGHBOR_SHORT[nbk], m.group(2))
            consider(m.end(), find_nn_file(folder, m.group(3)) if folder else None, "neighbor nn/nn")
            chain_nb = (nbk, m.end())
        else:
            folder = find_folder(root, filedir, "", m.group(2))
            consider(m.end(), find_nn_file(folder, m.group(3)) if folder else None, "plain nn/nn")
            chain_nb = None
    for m in re.finditer(r"(?<![\w/`.])(\d\d-[a-z][\w-]*)/(\d\d)(?![\w/`])", text):
        folder = find_folder(root, filedir, "", m.group(1))
        consider(m.end(), find_nn_file(folder, m.group(2)) if folder else None, "plain folder/nn")
    for m in re.finditer(r"(?<![\w-])" + NB + r"(?:-research)?\s+`?(\d\d)`?(?![/\d])", text):
        consider(m.end(), "FOLDER", "neighbor-folder")
    # «(01 §12.2)», «OpenAI, 01 §4.5» — файл NN своей папки (или папки агента: «A 01 §2»)
    pm = re.search(r"(?:^|[\s(,;])(?:(" + AGENT_TOKEN + r")\s+)?(\d\d)\s*$", text)
    if pm:
        folder = agent_folder(root, pm.group(1)) if pm.group(1) else (last_dir or filedir)
        consider(pm.end(), find_nn_file(folder, pm.group(2)), "plain nn")
    for m in re.finditer(r"\bPLAN(?:\.md)?`?\s*$", text):
        consider(m.end(), os.path.join(root, "PLAN.md"), "plan")
    for m in FILE_NN_RE.finditer(text):
        consider(m.end(), find_nn_file(filedir, m.group(1)), "file-nn")
    for m in re.finditer(r"там же", text):
        if last_target:
            consider(m.end(), last_target, "same-as-previous")
    # «отчёт A §4», «V §4», «C2 §2.5», «H-plan §3», «[S1 §14]» — отчёты, планы, источники: цель не определяется
    am = re.search(r"(?:(?:отч[её]т[а-я]*|агент[а-я]*|заметк[а-я]*|помощник[а-я]*)\s+|[(\[;,]\s*|^|\s)(?:" + AGENT_TOKEN + r"(?:-plan|-notes|-helper[\w-]*)?|S\d+)\s*\(?\s*$", text)
    if am and (best is None or am.end() > best[0]):
        best = (am.end(), "EXTERNAL", "agent-report")
    # аудиты соседей («аудит UX §2.1») — заметки `99-raw/notes/…/<СОСЕД>-report.md`, не файлы базы
    am2 = re.search(r"(?:отч[её]т[а-я]*|контракт[а-я]*(?:\s+тройки)?(?:\s+v\d)?|[\w-]+-report`?|report|аудит[а-я]*\s+[A-Z][A-Z-]+)\s*\(?\s*$", text)
    if am2 and (best is None or am2.end() > best[0]):
        best = (am2.end(), "EXTERNAL", "report-or-contract")
    sm2 = re.search(r"спецификаци[а-я]*\s+линтера\s*$", text)
    if sm2 and (best is None or sm2.end() > best[0]):
        best = (sm2.end(), os.path.join(root, "06-anti-slop", "02-linter-spec-and-profiles.md"), "named-spec")
    cm2 = re.search(r"(?<![\w-])каталог[а-я]*\s*\(?\s*$", text)  # «(каталог §10)» — каталог маркеров C
    if cm2 and (best is None or cm2.end() > best[0]):
        best = (cm2.end(), os.path.join(root, "06-anti-slop", "01-text-slop-markers-by-genre.md"), "named-catalog")
    hm2 = re.search(r"(?<![\w-])здесь(?:\s+же)?\s*$", text)  # «здесь §4.3» — этот файл
    if hm2 and (best is None or hm2.end() > best[0]):
        best = (hm2.end(), os.path.join(root, relpath), "here")
    em = re.search(r"(?<![\w/])" + AGENT_TOKEN + r"/\d\d[a-z]?\s*$", text)  # «J/01 §4.3» — README опыта
    if em and (best is None or em.end() >= best[0]):
        best = (em.end(), "EXTERNAL", "experiment")
    nm = re.search(r"(?<![\w-])" + NB + r"(?:-research)?\s*$", text)  # «blender §11.4» — файл соседней базы не назван
    if nm and (best is None or nm.end() >= best[0]):
        best = (nm.end(), "FOLDER", "neighbor-no-file")
    if best is None:
        return None, None, False
    return best[1], best[2], best[0] <= split_pos


def _section_as_item(target, s, nums):
    """Раздел как пункт: «§3.4» — строка таблицы `| 3.4 |` или пункт `4.` списка раздела 3."""
    tlines = read_lines(target)
    if any(re.match(r"^\s*\|\s*§?%s\.?\s*\|" % re.escape(s), x) for x in tlines):
        return "строка таблицы %s" % s
    top = s.split(".")[0]
    if "." in s and top in nums and re.match(r"^\d+\.\d+$", s):
        item = s.split(".")[1]
        start = nums[top]
        end = len(tlines)
        for k in range(start + 1, len(tlines)):
            if re.match(r"^##\s", tlines[k]):
                end = k
                break
        if any(re.match(r"^\s*(?:\|\s*)?%s\.\s" % item, x) for x in tlines[start:end]):
            return "пункт %s списка раздела %s" % (item, top)
    return None


def _context_neighbors(lines, i):
    """Соседние базы, названные на строке, в её абзаце (до пустой строки вверх) или в шапке таблицы."""
    found = []
    j = i
    while j >= 0 and lines[j].strip() != "" and i - j < 40:
        for m in NB_WORD_RE.finditer(lines[j]):
            nb = NEIGHBOR_SHORT[m.group(1)]
            if nb not in found:
                found.append(nb)
        j -= 1
    return found


def check_sections(root, relpath, lines, infence, rep, index_cache, folder_files, basename_index):
    filedir = os.path.dirname(os.path.join(root, relpath))
    this_abs = os.path.join(root, relpath)
    last_target = None
    reported = set()
    _nums, _heads = heading_index(lines)
    src_start, src_end = sources_span(lines, _heads)

    def index_of(path):
        if path not in index_cache:
            nums = heading_index(read_lines(path))[0] if os.path.exists(path) else {}
            index_cache[path] = nums
        return index_cache[path]

    def has_section(path, sec):
        if not path or not os.path.exists(path):
            return None
        nums = index_of(path)
        if sec in nums:
            return "заголовок"
        return _section_as_item(path, sec, nums)

    for i, ln in enumerate(lines):
        if infence[i] or "§" not in ln:
            continue
        continuation = not re.match(r"^\s*(?:[-*]\s|\|\s|#|\d+\.\s)", ln) and i > 0 and lines[i - 1].strip() != ""
        in_sources = src_start is not None and src_start <= i < src_end
        src_url = in_sources and bool(re.search(r"https?://", ln + " " + (lines[i - 1] if continuation else "")))
        is_row = ln.lstrip().startswith("|")
        line_target = None
        ext_end = None  # конец последней внешней ссылки § на строке («SQRG: §4.6.5 scaled content abuse, §4.6.6»)
        code_spans = [(cm.start(), cm.end()) for cm in BACKTICK_RE.finditer(ln)]
        for m in SECT_RE.finditer(ln):
            if any(a < m.start() < b for a, b in code_spans):
                continue  # ссылка внутри кода: пояснение нотации, не ссылка
            sec = m.group(1)
            before = ln[: m.start()]
            if ext_end is not None and m.start() - ext_end < 45 and "`" not in ln[ext_end: m.start()] \
                    and not re.search(r"\b\d\d/\d\d\b|→", ln[ext_end: m.start()]):
                rep.tick("б")
                rep.cat("б", "продолжение внешней ссылки (не проверяется)")
                rep.add("б", "INFO", relpath, i + 1, "§%s: продолжение перечня внешнего документа, не проверяется" % sec)
                ext_end = m.end()
                continue
            tail = RANGE_TAIL_RE.match(ln[m.end():])
            secs = [sec] + ([tail.group(1)] if tail and tail.group(1).count(".") == sec.count(".") else [])
            ctx = before[-70:]
            how = None
            target = None
            after_s = ln[m.end(): m.end() + 25]
            if src_url and not re.search(r"`[^`]*\.md`[^§]{0,20}$", before):
                rep.tick("б", len(secs))
                rep.cat("б", "раздел документа-источника в «Источниках» (не проверяется)", len(secs))
                rep.add("б", "INFO", relpath, i + 1, "§%s: в разделе «Источники» у внешнего URL — раздел документа-источника" % sec)
                continue
            if int(sec.split(".")[0]) > 40 or re.search(r"(?:%s)[^§`]{0,30}$" % "|".join(re.escape(x) for x in EXTERNAL_DOC_MARKERS), ctx) \
                    or re.match(r"^\s*(?:заметок|отч[её]та|помощника|report|notes)", after_s):
                rep.tick("б", len(secs))
                rep.cat("б", "внешний документ (не проверяется)", len(secs))
                rep.add("б", "INFO", relpath, i + 1, "§%s: ссылка на внешний документ, не проверяется" % sec)
                ext_end = m.end()
                continue
            from_prev = False
            this_after = re.match(r"^(?:\s*[–-]\s*§?\d+(?:\.\d+)*[a-z]?)?(?:\s*(?:,|и)\s*§\s?\d+(?:\.\d+)*[a-z]?(?:\s*[–-]\s*§?\d+(?:\.\d+)*)?)*\s+(?:этого|этом|настоящего)\s+файл", ln[m.end():])
            if this_after:  # «поправки — §1.2 и §2.6 этого файла»
                target, how = this_abs, "this-file-after"
            elif re.search(r"→\s*$", ctx):
                head = ctx.rstrip("→ \t").rstrip()
                if head.endswith(")") and line_target is not None:
                    target, how = line_target, "arrow-chain"
                else:
                    target, how = this_abs, "arrow-same-file"
            elif not before.strip() and not is_row and i > 0 and re.search(r"→\s*$", lines[i - 1]):
                target, how = this_abs, "arrow-same-file-prev-line"  # «… →» + перенос + «§6 [практика]» — свой файл
            elif CHAIN_RE.search(ctx) and line_target is not None:
                target, how = line_target, "chain"
            elif re.match(r"^\s*спецификаци[а-я]*\s+линтера", ln[m.end():]):  # «(типы §3.4 спецификации линтера»
                target, how = os.path.join(root, "06-anti-slop", "02-linter-spec-and-profiles.md"), "named-spec-after"
            else:
                text = before
                split_pos = 0
                if is_row:
                    text = before[before.rfind("|") + 1:]  # строка таблицы: контекст — своя ячейка
                    continuation_here = False
                else:
                    continuation_here = continuation
                if continuation_here:
                    prev = lines[i - 1]
                    if prev.count("`") % 2 == 1:  # путь в бэктиках разорван переносом строки
                        text = prev + before.lstrip()
                    else:
                        text = prev + " " + before
                    split_pos = len(prev)
                target, how, from_prev = target_from_context(root, relpath, filedir, text, last_target, basename_index, split_pos)
                if target is None and continuation and not before.strip() and last_target is not None:
                    target, how = last_target, "chain-prev-line"  # строка-продолжение начинается с «§8.1 п. 10–12»
                if target is None and is_row and before.rfind("|") > ln.find("|"):
                    cells = ln.split("|")
                    first = cells[1] if len(cells) > 2 else ""
                    t6, h6 = None, None
                    if re.match(r"^\s*`[^`]+\.md`\s*$", first):  # строка README: первая ячейка — файл строки
                        t6, h6, _ = target_from_context(root, relpath, filedir, first, None, basename_index, 0)
                    if t6 is not None and t6 not in ("FOLDER", "EXTERNAL"):
                        target, how = t6, "table-row-file " + h6  # README: «| `01-hero-and-cta.md` | … §9 — поправки |»
                    else:
                        target, how = this_abs, "same-file-table-cell"  # не первая ячейка без пути — свой файл
                if target is None and is_row:
                    # строка таблицы: цель — в шапке таблицы или в строке перед таблицей («| Правило ux 07/06 |»)
                    j = i
                    while j > 0 and lines[j - 1].lstrip().startswith("|"):
                        j -= 1
                    hdr = (lines[j - 1] if j > 0 else "") + " " + lines[j]
                    t2, h2, _ = target_from_context(root, relpath, filedir, hdr + " " + before, last_target, basename_index, len(hdr) + 1)
                    if t2 is not None:
                        target, how = t2, "table-header " + h2
                if target is None:
                    after = ln[m.end(): m.end() + 90]
                    am = re.match(r"[^`]{0,25}\b(?:в|из|см\.)\s+`([^`]+\.md)`", after)
                    fm = re.match(r"[^§]{0,6}файл[а-яё]*\s+(\d\d)\b", after)
                    if am:
                        for _, c in path_candidates(root, filedir, clean_path_token(am.group(1))):
                            if os.path.exists(c):
                                target, how = c, "path-after"
                                break
                    elif fm:
                        target, how = find_nn_file(filedir, fm.group(1)), "file-nn-after"
                if target is None:
                    target, how = this_abs, "same-file"
            if target == "FOLDER":
                rep.tick("б", len(secs))
                rep.cat("б", "цель — папка или сосед без файла (не проверяется)", len(secs))
                rep.add("б", "INFO", relpath, i + 1, "§%s: цель — папка (%s), раздел не проверяется" % (sec, how))
                line_target = None
                continue
            if target == "EXTERNAL":
                rep.tick("б", len(secs))
                rep.cat("б", "отчёт, заметки, контракт, источник (не проверяется)", len(secs))
                rep.add("б", "INFO", relpath, i + 1, "§%s: ссылка на отчёт, заметки или источник, цель не определяется" % sec)
                line_target = None
                ext_end = m.end()
                continue
            if isinstance(target, str) and target.startswith("MISSING:"):
                rep.tick("б", len(secs))
                rep.cat("б", "файл соседа не найден (битая)", len(secs))
                rep.add("б", "ERROR", relpath, i + 1, "§%s: файл `%s` не найден" % (sec, target[len("MISSING:"):]))
                line_target = None
                continue
            if from_prev and target != this_abs:
                own = index_of(this_abs)
                if any(x not in index_of(target) and x in own for x in secs):
                    target, how = this_abs, "same-file"
            line_target = target
            last_target = target
            trel = rel(root, target)
            for s in secs:
                if (i, s, target) in reported:
                    continue
                reported.add((i, s, target))
                rep.tick("б")
                found = has_section(target, s)
                if found == "заголовок":
                    rep.cat("б", "раздел найден")
                    continue
                if found:
                    rep.cat("б", "найден как пункт или строка таблицы")
                    continue
                if in_sources and how in ("same-file", "chain", "arrow-same-file") and target == this_abs:
                    rep.cat("б", "раздел документа-источника в «Источниках» (не проверяется)")
                    rep.add("б", "INFO", relpath, i + 1, "§%s: в разделе «Источники» — раздел внешнего документа, не проверяется" % s)
                    continue
                # запасные цели: соседи, названные в абзаце, с теми же номерами; файл NN своей папки
                alts = []
                tr = rel(root, target)
                mm = re.match(r"^(\d\d)-[^/]+/(\d\d)-", tr)
                if mm:
                    for nb in _context_neighbors(lines, i):
                        folder = neighbor_folder(root, nb, mm.group(1))
                        t3 = find_nn_file(folder, mm.group(2)) if folder else None
                        if t3:
                            alts.append((t3, "сосед %s, тот же номер" % nb))
                mb = re.search(r"`(\d\d)`[^`§]{0,12}$", before)
                if mb:
                    t4 = find_nn_file(filedir, mb.group(1))
                    if t4 and t4 != target:
                        alts.append((t4, "файл %s своей папки" % mb.group(1)))
                alt_hit = None
                for t5, why in alts:
                    if has_section(t5, s):
                        alt_hit = (t5, why)
                        break
                if alt_hit:
                    rep.cat("б", "раздел найден в запасной цели (сосед или своя папка)")
                    rep.add("б", "INFO", relpath, i + 1, "§%s: в `%s` нет, найден в `%s` (%s) — цель по контексту" % (s, trel, rel(root, alt_hit[0]), alt_hit[1]))
                    continue
                nums = index_of(target)
                tdir = os.path.dirname(target)
                siblings = [f for f in folder_files.get(tdir, []) if f != target and s in index_of(f)]
                hint = ""
                if siblings:
                    hint = "; есть в " + ", ".join("`%s`" % rel(root, f) for f in siblings[:3])
                external_target = not os.path.abspath(target).startswith(os.path.abspath(root) + os.sep)
                if not nums:
                    rep.cat("б", "в цели нет нумерованных заголовков")
                    rep.add("б", "WARN", relpath, i + 1, "§%s → `%s`: в целевом файле нет нумерованных заголовков (%s)" % (s, trel, how))
                    continue
                if how in ("same-file",) or siblings or external_target:
                    level = "WARN"  # цель угадана по умолчанию, раздел есть рядом или цель — соседняя база
                    rep.cat("б", "раздела нет, цель угадана (WARN)")
                else:
                    level = "ERROR"
                    rep.cat("б", "раздела нет (битая)")
                rep.add("б", level, relpath, i + 1, "§%s → `%s`: раздела нет (%s)%s" % (s, trel, how, hint))


# ----------------------------------------------------------------------------------------------------- (в)
def collect_source_defs(root, files):
    per_file = {}
    per_folder = defaultdict(set)
    where_defined = defaultdict(list)
    for path in files:
        relpath = rel(root, path)
        lines = read_lines(path)
        nums, heads = heading_index(lines)
        start, end = sources_span(lines, heads)
        defs = set()
        if start is not None:
            for ln in lines[start:end]:
                for m in S_REF_RE.finditer(ln):
                    defs.add(m.group(1) + m.group(2))
        per_file[relpath] = (defs, start, end)
        folder = relpath.split("/", 1)[0]
        per_folder[folder] |= defs
        for d in defs:
            where_defined[d].append(relpath)
    return per_file, per_folder, where_defined


def check_source_refs(root, relpath, lines, infence, rep, per_file, per_folder, where_defined):
    if relpath.startswith(("90-sources/", "00-glossary/", "99-raw/")) or relpath in ("PLAN.md", "CONTRADICTIONS.md"):
        return  # индексные папки и сводные файлы: метки других файлов упоминаются как данные
    defs, start, end = per_file[relpath]
    uses = defaultdict(list)
    for i, ln in enumerate(lines):
        if start is not None and start <= i < end:
            continue
        for m in S_REF_RE.finditer(ln):
            uses[m.group(1) + m.group(2)].append(i + 1)
    rep.tick("в", sum(len(v) for v in uses.values()))
    folder = relpath.split("/", 1)[0]
    is_index = relpath.endswith(("README.md", "glossary.md"))
    if not uses and not defs:
        return
    if uses and start is None and not is_index:
        rep.add("в", "WARN", relpath, 0, "в файле есть ссылки %s, но нет раздела «Источники»" % ", ".join("[%s]" % k for k in sorted(uses)[:5]))

    def keyf(k):
        return (k[0], int(re.match(r"[SM](\d+)", k).group(1)), k)

    for key in sorted(uses, key=keyf):
        if key in defs:
            rep.cat("в", "определён в своём файле", len(uses[key]))
            continue
        where = uses[key]
        if is_index:
            rep.cat("в", "README цитирует чужую метку (не проверяется)", len(where))
            continue  # README цитирует метки других файлов
        if key in per_folder[folder]:
            rep.cat("в", "определён в другом файле папки (INFO)", len(where))
            rep.add("в", "INFO", relpath, where[0], "[%s] не определён в файле, но определён в другом файле папки (%d использований)" % (key, len(where)))
        elif key in where_defined:
            others = sorted(set(where_defined[key]))
            rep.cat("в", "определён только в другой папке (WARN)", len(where))
            rep.add("в", "WARN", relpath, where[0], "[%s] не определён в папке; определён в %s (%d использований)" % (key, ", ".join("`%s`" % o for o in others[:3]), len(where)))
        else:
            rep.cat("в", "не определён (битая)", len(where))
            rep.add("в", "ERROR", relpath, where[0], "[%s] не определён ни в файле, ни в базе (%d использований)" % (key, len(where)))
    if not is_index:
        unused = sorted(defs - set(uses), key=keyf)
        if unused:
            rep.add("в", "INFO", relpath, (start or 0) + 1, "определены, но не используются в тексте: %s" % ", ".join("[%s]" % k for k in unused))


# ----------------------------------------------------------------------------------------------------- (г)
def tc_valid(tc):
    """Таймкод по форме: минуты и секунды (и минуты часового таймкода) меньше 60."""
    return all(int(p) < 60 for p in tc.split(":")[1:])


def check_video_refs(root, relpath, lines, infence, rep):
    """Ссылки `[V:<id> mm:ss]` по форме: id ролика из 11 символов, таймкод с минутами и секундами меньше 60."""
    no_tc = 0
    outside = 0
    for i, ln in enumerate(lines):
        for m in V_REF_RE.finditer(ln):
            for body in re.split(r"[;,]\s*V:", m.group(1)):
                idm = V_ID_RE.match(body)
                if not idm:
                    if not body.strip() or re.search(r"<|…|\bid\b|мм:сс", body):  # пустое «[V:]» — формат
                        continue  # шаблон записи в описании формата
                    rep.tick("г")
                    rep.cat("г", "не похоже на id")
                    rep.add("г", "WARN", relpath, i + 1, "[V:%s]: не похоже на id ролика YouTube (11 символов)" % body)
                    continue
                vid = idm.group(1)
                rep.tick("г")
                tcs = TIMECODE_RE.findall(body[idm.end():])
                for tc in tcs:
                    if not tc_valid(tc):
                        rep.cat("г", "таймкод не по форме (битая)")
                        rep.add("г", "ERROR", relpath, i + 1, "[V:%s %s]: таймкод не по форме — минуты и секунды меньше 60" % (vid, tc))
                outside += 1
                if not tcs:
                    no_tc += 1
    if outside:
        rep.cat("г", "роликов в скилле нет — сверена форма (INFO)", outside)
        rep.add("г", "INFO", relpath, 0, "%d ссылок [V:…]: дайджестов, транскриптов и каталога роликов в скилле нет — сверены id и таймкоды по форме" % outside)
    if no_tc:
        rep.add("г", "INFO", relpath, 0, "%d ссылок [V:…] без таймкода" % no_tc)
        rep.cat("г", "без таймкода", no_tc)


# ----------------------------------------------------------------------------------------------------- (д)
# имена форматов, которые README называют как понятие («запись `facts.yaml`», «`blocks.yaml` site»), а не как файл папки
GENERIC_FORMAT_NAMES = {"facts.yaml", "voc.yaml", "meaning.yaml", "blocks.yaml", "voice.yaml", "brief.yaml",
                        "page-plan.yaml", "vocabulary.yaml", "site-brief.yaml", "copy.md", "facts.md", "TASK.md",
                        "ACCEPTANCE.md", "hierarchy.yaml", "deck.yaml", "treatment.yaml", "crosswalk.tsv",
                        "queries.tsv", "serp.tsv", "clusters.tsv", "info.json"}
README_FILE_TOKEN_RE = re.compile(r"`((?:[\w.-]+/)*[\w.-]+\.(?:md|ya?ml|json|html|jsonl|tsv))`")


def check_readme_coverage(root, rep, basename_index_all):
    dirs = [d for d in sorted(os.listdir(root)) if CONTENT_DIRS_RE.match(d) and os.path.isdir(os.path.join(root, d))]
    queue = [os.path.join(root, d) for d in dirs]
    while queue:
        d = queue.pop(0)
        rd = rel(root, d)
        readme = os.path.join(d, "README.md")
        entries = sorted(e for e in os.listdir(d) if not e.startswith(".") and e not in SKIP_DIR_NAMES | {"README.md"})
        if not os.path.exists(readme):
            if rd.count("/") == 0 and not entries:
                rep.add("д", "INFO", rd, 0, "папка пуста, README.md нет")
                continue
            rep.add("д", "ERROR" if rd.count("/") == 0 else "INFO", rd, 0, "нет README.md (%d файлов и папок внутри)" % len(entries))
            continue
        rlines = read_lines(readme)
        text = "\n".join(rlines) + "\n"
        for e in entries:
            full = os.path.join(d, e)
            rep.tick("д")
            if os.path.isdir(full):
                inner = [x for x in os.listdir(full) if not x.startswith(".") and x not in SKIP_DIR_NAMES]
                has_index = os.path.exists(os.path.join(full, "README.md"))
                if has_index:
                    queue.append(full)
                if e + "/" not in text and e not in text:
                    rep.cat("д", "папка не упомянута в README (битая)")
                    rep.add("д", "ERROR", rd, 0, "папка `%s/` не упомянута в README.md (%d файлов)" % (e, len(inner)))
                else:
                    rep.cat("д", "папка упомянута")
                if (e + "/" in text or e in text) and not has_index:
                    missing = [x for x in inner if x not in text and os.path.splitext(x)[0] not in text]
                    if missing and e != "transcripts":
                        rep.add("д", "INFO", rd, 0, "папка `%s/` упомянута, но %d из %d файлов не перечислены поимённо: %s" % (e, len(missing), len(inner), ", ".join(sorted(missing)[:8]) + (" …" if len(missing) > 8 else "")))
            else:
                if e not in text:
                    rep.cat("д", "файл не упомянут в README (битая)")
                    rep.add("д", "ERROR", rd, 0, "файл `%s` не упомянут в README.md" % e)
                else:
                    rep.cat("д", "файл упомянут")
        # обратное направление: упомянутые в README файлы этой папки есть на диске
        for i, ln in enumerate(rlines):
            for m in README_FILE_TOKEN_RE.finditer(ln):
                tok = m.group(1)
                if tok.startswith(("99-raw/", "../")) or ("/" in tok and tok.split("/", 1)[0] in os.listdir(root)):
                    continue  # ссылки наружу проверяет (а)
                if PLACEHOLDER_RE.search(tok) or "*" in tok or os.path.basename(tok) in GENERIC_FORMAT_NAMES:
                    continue
                rep.tick("д")
                cand = [os.path.join(d, tok)] + glob.glob(os.path.join(d, "**", os.path.basename(tok)), recursive=True)
                if any(os.path.exists(c) for c in cand):
                    rep.cat("д", "упомянутый в README файл есть")
                    continue
                elsewhere = basename_index_all.get(os.path.basename(tok), [])
                if elsewhere:
                    rep.add("д", "INFO", rd + "/README.md", i + 1, "`%s` в папке нет, лежит в `%s`" % (tok, elsewhere[0]))
                elif re.match(r"^\d\d[a-z]?-", os.path.basename(tok)) or tok.endswith((".yaml", ".yml", ".html", ".tsv", ".json")):
                    rep.cat("д", "README называет несуществующий файл (битая)")
                    rep.add("д", "ERROR", rd + "/README.md", i + 1, "в README упомянут `%s`, на диске его нет" % tok)
        for i, ln in enumerate(rlines):
            m = README_ROW_RE.match(ln)
            if not m:
                continue
            fn, claimed = m.group(1), int(m.group(2))
            j = i
            while j > 0 and rlines[j - 1].lstrip().startswith("|"):
                j -= 1
            if "строк" not in rlines[j].rstrip(" |").split("|")[-1].lower():
                continue  # последняя колонка таблицы — не число строк («Фаза», «Волна»)
            target = os.path.normpath(os.path.join(d, fn))
            if os.path.exists(target):
                tl = read_lines(target)
                actual = len(tl) - (1 if tl and tl[-1] == "" else 0)
                rep.tick("д")
                if actual != claimed:
                    rep.cat("д", "число строк в таблице README не совпало (INFO)")
                    rep.add("д", "INFO", rd + "/README.md", i + 1, "`%s`: заявлено %d строк, фактически %d" % (fn, claimed, actual))


# ----------------------------------------------------------------------------------------------------- (е)
def check_required_sections(root, relpath, lines, heads, rep):
    base = os.path.basename(relpath)
    if base in ("README.md", "glossary.md", "PLAN.md", "CONTRADICTIONS.md") or is_raw(relpath):
        return
    if relpath.startswith(("90-sources/", "00-glossary/")):
        return
    if "/examples/" in relpath or "/pages/" in relpath or "/prompts/" in relpath or relpath in FORMAT_EXEMPT:
        return  # примеры, промты, анкета, шаблон, план живого теста — разделы формата не нужны
    else:
        profile, label = REQUIRED_DEFAULT, "содержательный файл"
    texts = [re.sub(r"^\d+(\.\d+)*\.?\s*", "", t).lower() for (_, lvl, t) in heads if lvl == 2]
    missing = []
    renamed = []
    for name, keys in profile:
        hit = [t for t in texts if any(k in t for k in keys)]
        if not hit:
            missing.append(name)
        elif not any(t.startswith(keys[0]) or keys[0] in t for t in hit):
            renamed.append((name, hit[0]))
    rep.tick("е", len(profile))
    if missing:
        level = "WARN"  # отсутствие раздела — замечание, не битая ссылка
        rep.add("е", level, relpath, 0, "%s: нет разделов %s" % (label, ", ".join("«%s»" % x for x in missing)))
    for name, actual in renamed:
        rep.add("е", "INFO", relpath, 0, "%s: раздел «%s» назван иначе: «%s»" % (label, name, actual))


# ----------------------------------------------------------------------------------------------------- (ж)
def check_verified_labels(root, relpath, lines, rep, exp_agents):
    bare = []
    parts = 0
    exp_root = os.path.join(root, "99-raw", "experiments")
    for i, ln in enumerate(lines):
        for m in VERIFIED_RE.finditer(ln):
            kind, body = m.group(1), m.group(2)
            rep.tick("ж")
            refs = []
            for pm in EXP_PATH_RE.finditer(body):  # путь с префиксом `../../<база>/` — опыт соседа
                nbk = [k for k, v in NEIGHBOR_SHORT.items() if v == pm.group(1)][0] if pm.group(1) else None
                refs.append((nbk, pm.group(2), pm.group(3), None, "", "path"))
            chain_nb = None  # «[проверено: ai-media J/04, J/06]» — префикс базы действует на перечень через «,» или «и»
            for sm in EXP_SHORT_RE.finditer(body):
                nb, agent, nn, nn2, part = sm.group(1), sm.group(2), sm.group(3), sm.group(4), sm.group(5)
                if not nb and chain_nb and re.match(r"^\s*(?:,|и)\s*$", body[chain_nb[1]: sm.start()]):
                    nb = chain_nb[0]
                chain_nb = (nb, sm.end()) if nb else None
                if nb or agent in exp_agents:
                    refs.append((nb, agent, nn, nn2, part, "short"))
                elif re.match(r"^[A-Z]\d$", agent) and agent[0] in exp_agents and agent not in ("W2",):
                    refs.append((None, agent[0], nn, nn2, part, "continuation"))  # «E3/04» → опыт E/04-…
            for tok in re.findall(r"(?:\d\d-[a-z][\w-]*|99-raw)/[\w./…-]+", body):
                if tok.startswith("99-raw/experiments/"):
                    continue
                if re.search(r"(?:\.\./)+(?:%s)(?:-research)?/%s" % ("|".join(re.escape(x) for x in NEIGHBORS), re.escape(tok)), body):
                    continue  # путь внутри соседней базы (`../../text/09-…`) — не файл этой базы
                tok = clean_path_token(tok)
                cand = os.path.join(root, tok.replace("…", "*"))
                rep.cat("ж", "путь к файлу базы")
                if not glob.glob(cand) and not glob.glob(cand + "*"):
                    rep.cat("ж", "битая")
                    rep.add("ж", "ERROR", relpath, i + 1, "[%s: …] ссылается на `%s` — такого пути нет" % (kind, tok))
            for nb, agent, nn, nn2, part, how in refs:
                nbase = NEIGHBOR_SHORT[nb] if nb else None
                base = os.path.join(root, "..", nbase, "99-raw", "experiments") if nb else exp_root
                adir = os.path.join(base, agent)
                where = ("99-raw/experiments/%s/" % agent) if not nb else ("../%s/99-raw/experiments/%s/" % (nbase, agent))
                rep.cat("ж", ("опыт соседней базы (полный путь)" if how == "path" else "опыт соседней базы") if nb else ("полный путь опыта" if how == "path" else "сокращение опыта"))
                if not os.path.isdir(adir):
                    rep.cat("ж", "битая")
                    rep.add("ж", "ERROR", relpath, i + 1, "[%s: %s/%s%s]: папки опытов `%s` нет" % (kind, agent, nn, part, where))
                    continue
                ends = [nn] + ([nn2] if nn2 else [])
                for end in ends:
                    pat = end.replace("…", "*").rstrip("/")
                    hits = glob.glob(os.path.join(adir, pat + part)) or glob.glob(os.path.join(adir, pat + part + "*"))
                    if not hits and part:
                        hits = glob.glob(os.path.join(adir, pat + "-*"))
                        if hits:
                            parts += 1
                    if not hits:
                        rep.cat("ж", "битая")
                        rep.add("ж", "ERROR", relpath, i + 1, "[%s: %s/%s%s]: опыта нет в `%s`" % (kind, agent, end, part, where))
                    elif how == "continuation":
                        rep.add("ж", "INFO", relpath, i + 1, "[%s: …]: сокращение продолжателя — опыт лежит в `%s%s`" % (kind, where, os.path.basename(hits[0])))
            if kind == "проверено" and not refs and not body.strip(": "):
                if not (EXP_PATH_RE.search(ln) or any(s.group(2) in exp_agents for s in EXP_SHORT_RE.finditer(ln))):
                    bare.append(i + 1)
                    rep.cat("ж", "голая метка без пути на строке")
            elif kind == "проверено" and not refs and body.strip(": "):
                rep.cat("ж", "метка с текстом без пути опыта")
                rep.add("ж", "INFO", relpath, i + 1, "[проверено%s]: путь опыта не распознан — проверить вручную" % body[:60])
    if parts:
        rep.add("ж", "INFO", relpath, 0, "%d ссылок на части опыта (`H/05a` → `H/05-…`): папка части не выделена" % parts)
    if bare:
        rep.add("ж", "INFO", relpath, bare[0], "%d голых меток [проверено] без пути опыта на строке (строки %s)" % (len(bare), ", ".join(map(str, bare[:12])) + (" …" if len(bare) > 12 else "")))


# ----------------------------------------------------------------------------------------------------- main
TITLES = {
    "а": "(а) Относительные ссылки на файлы и папки (в том числе соседние базы)",
    "б": "(б) Ссылки на разделы §N.M (в том числе «→ §N» — тот же файл)",
    "в": "(в) Ссылки на источники [S<n>] / [M<n>]",
    "г": "(г) Ссылки на ролики [V:<id> mm:ss]",
    "д": "(д) README папок: полнота и соответствие диску",
    "е": "(е) Обязательные разделы содержательных файлов и дайджестов",
    "ж": "(ж) Метки [проверено: …] → папки и файлы опытов",
}


def run_checks(root, only=(), with_raw=True):
    """Проверки одной базы: root — папка базы; её имя (`kb/<база>/`) задаёт соседей."""
    def want(ch):
        return not only or ch in only

    base = os.path.basename(os.path.normpath(root))
    configure(base if base in kbpaths.BASES else None)
    rep = Report()
    files = collect_files(root, with_raw)
    top_dirs = {d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))}
    tools_dir = os.path.join(root, "99-raw", "tools")
    tools_names = set(os.listdir(tools_dir)) if os.path.isdir(tools_dir) else set()
    tools_names |= {p.name for p in kbpaths.scripts().rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    exp_dir = os.path.join(root, "99-raw", "experiments")
    exp_agents = {d for d in os.listdir(exp_dir) if os.path.isdir(os.path.join(exp_dir, d))} if os.path.isdir(exp_dir) else set()
    basename_index = defaultdict(list)
    folder_files = defaultdict(list)
    for p in files:
        basename_index[os.path.basename(p)].append(rel(root, p))
        if os.path.basename(p) not in ("README.md", "glossary.md"):
            folder_files[os.path.dirname(p)].append(p)
    basename_index_all = defaultdict(list)
    for dp, dn, fns in os.walk(root):
        dn[:] = [x for x in dn if x not in ("cache", "node_modules", "youtube", ".git", "__pycache__")
                 and not x.startswith("venv")]
        for fn in fns:
            basename_index_all[fn].append(rel(root, os.path.join(dp, fn)))
    per_file, per_folder, where_defined = collect_source_defs(root, files)
    index_cache = {}

    for path in files:
        relpath = rel(root, path)
        lines = read_lines(path)
        infence = strip_fences(lines)
        nums, heads = heading_index(lines)
        index_cache[path] = nums
        raw = is_raw(relpath)
        if want("а"):
            check_paths(root, relpath, lines, infence, rep, top_dirs, tools_names, basename_index)
        if want("б") and not raw:
            check_sections(root, relpath, lines, infence, rep, index_cache, folder_files, basename_index)
        if want("в") and not raw:
            check_source_refs(root, relpath, lines, infence, rep, per_file, per_folder, where_defined)
        if want("г") and not raw:
            check_video_refs(root, relpath, lines, infence, rep)
        if want("е") and not raw:
            check_required_sections(root, relpath, lines, heads, rep)
        if want("ж"):
            check_verified_labels(root, relpath, lines, rep, exp_agents)
    if want("д"):
        check_readme_coverage(root, rep, basename_index_all)
    return rep, files


def render(rep, files, root, only=(), quiet_info=False):
    def want(ch):
        return not only or ch in only

    out = []
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    out.append("Проверка перекрёстных ссылок базы: %s" % root)
    out.append("Файлов .md проверено: %d" % len(files))
    out.append("")
    out.append("СВОДКА ПО ПРОВЕРКАМ И КАТЕГОРИЯМ")
    out.append("%-70s %9s %6s %6s %6s" % ("проверка", "ссылок", "ERROR", "WARN", "INFO"))
    for ch in "абвгдеж":
        if not want(ch):
            continue
        c = rep.counts[ch]
        out.append("%-70s %9d %6d %6d %6d" % (TITLES[ch][:70], rep.checked[ch], c["ERROR"], c["WARN"], c["INFO"]))
        for name, n in sorted(rep.cats[ch].items(), key=lambda x: -x[1]):
            out.append("    · %-64s %9d" % (name, n))
    total_err = sum(rep.counts[ch]["ERROR"] for ch in rep.counts)
    total_warn = sum(rep.counts[ch]["WARN"] for ch in rep.counts)
    total_info = sum(rep.counts[ch]["INFO"] for ch in rep.counts)
    out.append("ИТОГО: ERROR %d, WARN %d, INFO %d" % (total_err, total_warn, total_info))
    out.append("")
    for ch in "абвгдеж":
        if not want(ch):
            continue
        items = [it for it in rep.items if it[0] == ch]
        c = rep.counts[ch]
        out.append("=" * 100)
        out.append("%s — проверено ссылок/пунктов: %d; ERROR %d, WARN %d, INFO %d" % (TITLES[ch], rep.checked[ch], c["ERROR"], c["WARN"], c["INFO"]))
        out.append("=" * 100)
        for it in sorted(items, key=lambda x: (order[x[1]], x[2], x[3])):
            _, level, path, line, msg = it
            if quiet_info and level == "INFO":
                continue
            loc = "%s:%d" % (path, line) if line else path
            out.append("%-5s %s: %s" % (level, loc, msg))
        out.append("")
    out.append("ИТОГО: ERROR %d, WARN %d, INFO %d" % (total_err, total_warn, total_info))
    return "\n".join(out) + "\n", total_err


# ----------------------------------------------------------------------------------------------------- selftest
def selftest():
    """Мини-раскладка `kb/<база>/` во временной папке: по хорошему и битому случаю на каждую проверку."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="check_links_selftest_")
    kb = os.path.join(tmp, "kb")
    root = os.path.join(kb, "site")

    def w(path, text):
        full = os.path.join(kb, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(text)

    std = ("## Частые ошибки\n\n- нет\n\n## Чек-лист\n\n- да\n\n## Открытые вопросы и противоречия\n\n- нет\n\n"
           "## Источники\n\n- [S1] Автор, 2024.\n")
    w("site/01-aaa/README.md", "# 01\n\n| Файл | О чём | Строк |\n|---|---|---|\n| `01-x.md` | тест | 3 |\n\n"
      "Ещё `02-y.md` и `05-gone.md`.\n")
    w("site/01-aaa/01-x.md",
      "# X\n\nВолна 1 · A\n\n## Выжимка для агента\n\n1. Правило → §1.2\n2. Правило → §7\n\n## 1. Раздел\n\n### 1.2 Под\n\n"
      "См. `../02-bbb/01-z.md` §2 и `../02-bbb/09-nope.md`; также 02/01 §2, 02/01 §5.\n"
      "Сосед: `../../ux/07-ux-writing/06-banned.md` §5 и `../../ux/07-ux-writing/99-none.md`.\n"
      "Прежнее имя папки: `../../ux-research/07-ux-writing/06-banned.md`; базы нет: `../../old-research/01-a/01-b.md`.\n"
      "Кратко: ux 07/06 §5.\n"
      "Утилиты: `states_export.py`, запуск `python3 nosuch_tool.py`.\n"
      "Источник [S1] и [S9].\n"
      "Ролики: [V:_EEEEEEEEEE 00:10], [V:AAAAAAAAAAA 01:00], [V:CCCCCCCCCCC], [V:AAAAAAAAAAA 07:75], [V:abc].\n"
      "Опыты: [проверено: 99-raw/experiments/Z/01-ok], [проверено: Z/02], [проверено: Z/01–03], [проверено ai-media Q/01],"
      " [проверено: Z3/01].\nГолая метка [проверено].\n"
      "Аудит соседа: см. аудит MEDIA §4.10.\n"
      "Автор и скобка: B (`01` §2).\n"
      "Формат: `[V:]` — пустое.\n"
      "Опыт соседа путём: [проверено: ../../ai-media/99-raw/experiments/Q/01-ok], "
      "[проверено: ../../ai-media/99-raw/experiments/Q/09-none].\n"
      "Цепочка соседа: [проверено: ai-media Q/01, Z/07].\n"
      "Опыт базы text: [проверено: text A/01], [проверено: text I/03].\n"
      "Свой файл после: `../02-bbb/01-z.md` §2; поправки — §1.2 этого файла.\n"
      "Цель раньше: `../02-bbb/01-z.md` §2.\nПравило без пути, стрелка в конце →\n  §1 `[практика]`.\n\n" + std)
    w("site/01-aaa/02-y.md", "# Y\n\n## Выжимка для агента\n\n- нет\n\n" + std)
    w("site/01-aaa/03-unlisted.md", "# U\n\n## Выжимка для агента\n\n- нет\n\n" + std)
    w("site/02-bbb/README.md", "# 02\n\n`01-z.md`, `02-v.md`\n")
    w("site/02-bbb/02-v.md", "# V\n\n" + std)
    w("site/02-bbb/01-z.md", "# Z\n\n## Выжимка для агента\n\n- нет\n\n## 2. Раздел\n\n- текст\n\n" + std)
    w("site/11-ccc/README.md", "# 11\n\n`01-w.md`\n")
    w("site/11-ccc/01-w.md", "# W\n\n## Выжимка для агента\n\n- нет\n\nСсылка `../02-bbb/08-gone.md`.\n\n" + std)
    w("site/99-raw/experiments/Z/01-ok/README.md", "# ok\n")
    w("site/99-raw/experiments/Z/03-ok/README.md", "# ok\n")
    w("site/99-raw/experiments/A/02-x/README.md", "# x\n")  # у site тоже есть опыт A: «text A/01» ищется у text
    w("ux/07-ux-writing/06-banned.md", "# ux\n\n## 5. Раздел\n")
    w("ai-media/99-raw/experiments/Q/01-ok/README.md", "# ok\n")
    w("ai-media/99-raw/experiments/Z/07-ok/README.md", "# ok\n")
    w("text/99-raw/experiments/A/01-ok/README.md", "# ok\n")
    rep, files = run_checks(root, with_raw=False)
    msgs = [(c, l, m) for (c, l, _p, _n, m) in rep.items]
    # вторая база: ссылки [V:…] с часовым таймкодом
    kb2 = os.path.join(tmp, "kb2")
    os.makedirs(os.path.join(kb2, "text", "01-aaa"))
    with open(os.path.join(kb2, "text", "01-aaa", "01-a.md"), "w", encoding="utf-8") as fh:
        fh.write("# A\n\nРолики: [V:AAAAAAAAAAA 01:00], [V:BBBBBBBBBBB 1:12:61].\n")
    rep2, _ = run_checks(os.path.join(kb2, "text"), only={"г"})
    msgs2 = [(c, l, m) for (c, l, _p, _n, m) in rep2.items]

    if os.environ.get("CHECK_LINKS_DEBUG"):
        for c, l, m in msgs + msgs2:
            print("DEBUG", c, l, m)

    def has(check, level, needle, where=None):
        return any(c == check and l == level and needle in m for c, l, m in (where or msgs))

    def lacks(check, needle):
        return not any(c == check and needle in m and l in ("ERROR", "WARN") for c, l, m in msgs)

    cases = [
        ("а: битый путь — ERROR", has("а", "ERROR", "09-nope.md")),
        ("а: живой путь — без находки", lacks("а", "01-z.md")),
        ("а: битая ссылка в соседнюю базу kb/ux — ERROR", has("а", "ERROR", "99-none.md")),
        ("а: живая ссылка в соседнюю базу — без находки", lacks("а", "06-banned.md")),
        ("а: прежнее имя папки базы — ведёт в kb/ux, сводка INFO", has("а", "INFO", "прежним именем папки")),
        ("а: база вне скилла — WARN", has("а", "WARN", "такой базы в скилле нет")),
        ("а: папка 11-… обходится", has("а", "ERROR", "08-gone.md")),
        ("а: утилита скилла по имени — без находки", lacks("а", "states_export.py")),
        ("а: утилиты нет нигде — WARN", has("а", "WARN", "nosuch_tool.py")),
        ("б: → §1.2 есть — без находки", lacks("б", "§1.2")),
        ("б: → §7 нет в своём файле — находка", has("б", "ERROR", "§7") or has("б", "WARN", "§7")),
        ("б: 02/01 §5 нет — ERROR", has("б", "ERROR", "§5 → `02-bbb/01-z.md`")),
        ("б: 02/01 §2 есть — без находки", lacks("б", "§2 → `02-bbb/01-z.md`")),
        ("б: ux 07/06 §5 есть у соседа — без находки", lacks("б", "§5 → `../ux")),
        ("в: [S9] не определён — ERROR", has("в", "ERROR", "[S9]")),
        ("в: [S1] определён — без находки", lacks("в", "[S1] не определён")),
        ("г: id по форме, с «_» в начале и без таймкода — без находки",
         lacks("г", "[V:AAAAAAAAAAA 01:00") and lacks("г", "_EEEEEEEEEE") and lacks("г", "[V:CCCCCCCCCCC")),
        ("г: не похоже на id — WARN", has("г", "WARN", "[V:abc]: не похоже на id")),
        ("г: таймкод не по форме — ERROR", has("г", "ERROR", "[V:AAAAAAAAAAA 07:75]: таймкод не по форме")),
        ("г: сверка по форме — сводка INFO, ссылки без таймкода — INFO", has("г", "INFO", "4 ссылок [V:…]")
         and has("г", "INFO", "1 ссылок [V:…] без таймкода") and has("г", "INFO", "сверены id и таймкоды", msgs2)),
        ("г: роликов нет — таймкод не по форме — ERROR", has("г", "ERROR", "1:12:61", msgs2)),
        ("д: файл не в README — ERROR", has("д", "ERROR", "03-unlisted.md")),
        ("д: README называет несуществующий — ERROR", has("д", "ERROR", "05-gone.md")),
        ("д: число строк в таблице README — INFO", has("д", "INFO", "заявлено 3 строк")),
        ("ж: полный путь опыта — без находки", lacks("ж", "01-ok")),
        ("ж: сокращение без опыта — ERROR", has("ж", "ERROR", "Z/02")),
        ("ж: диапазон Z/01–03 — концы есть, без находки", lacks("ж", "Z/03")),
        ("ж: опыт соседа ai-media Q/01 — без находки", lacks("ж", "Q/01")),
        ("ж: продолжатель Z3/01 → Z/01 — INFO", has("ж", "INFO", "сокращение продолжателя")),
        ("ж: голая метка — INFO", has("ж", "INFO", "голых меток")),
        ("е: у 02-z нет «Выжимки»? есть — без WARN", lacks("е", "02-bbb/01-z.md")),
        ("б: «аудит MEDIA §4.10» — внешнее, без находки", lacks("б", "§4.10")),
        ("б: «B (`01` §2)» — папка автора раздела, без находки", not any(c == "б" and "§2 →" in m and "01-aaa" in m for c, l, m in msgs)),
        ("б: «§1.2 этого файла» — свой файл, без находки", lacks("б", "§1.2 → `02-bbb")),
        ("б: «→» в конце строки + «§1» в начале следующей — свой файл", lacks("б", "§1 → `02-bbb")),
        ("г: пустое [V:] — без находки", lacks("г", "[V:]")),
        ("е: содержательный файл без «Выжимки» — WARN", has("е", "WARN", "«Выжимка для агента»")),
        ("ж: путь опыта соседа `../../ai-media/…` есть — без находки", lacks("ж", "Q/01-ok")),
        ("ж: путь опыта соседа нет — ERROR в соседней базе", has("ж", "ERROR", "../ai-media/99-raw/experiments/Q/")),
        ("ж: цепочка «ai-media Q/01, Z/07» — сосед наследуется, без находки", lacks("ж", "Z/07")),
        ("ж: «text A/01» — опыт базы text, без находки", lacks("ж", "A/01")),
        ("ж: «text I/03» нет у text — ERROR в базе text", has("ж", "ERROR", "../text/99-raw/experiments/I/")),
    ]
    ok = 0
    for name, res in cases:
        print("%s  %s" % ("OK  " if res else "FAIL", name))
        ok += bool(res)
    shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: %d из %d OK" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def base_of_cwd():
    """База `kb/<база>/`, внутри которой рабочая папка, или None."""
    kb = os.path.realpath(str(kbpaths.kb()))
    cwd = os.path.realpath(os.getcwd())
    if cwd == kb or not cwd.startswith(kb + os.sep):
        return None
    name = os.path.relpath(cwd, kb).split(os.sep)[0]
    return name if name in kbpaths.BASES else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__.split("\n", 2)[2],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", choices=kbpaths.BASES, help="база kb/<база>/ (по умолчанию — база рабочей папки, иначе все)")
    ap.add_argument("--all", action="store_true", help="все базы kb/ по очереди: в stdout — сводки")
    ap.add_argument("--root", help="другая папка базы (имя папки — имя базы для соседей)")
    ap.add_argument("--only", default="", help="буквы проверок через запятую, например а,б,ж")
    ap.add_argument("--json", default="", help="сохранить находки в JSON")
    ap.add_argument("--out", default="", help="записать отчёт в файл (иначе stdout)")
    ap.add_argument("--no-raw", action="store_true", help="не проверять 99-raw/tools/README.md и 99-raw/phase5/*.md")
    ap.add_argument("--quiet-info", action="store_true", help="не печатать строки INFO")
    ap.add_argument("--selftest", action="store_true", help="офлайн-тест на временной мини-раскладке kb/<база>/")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.root:
        roots = [os.path.abspath(args.root)]
    elif args.base:
        roots = [str(kbpaths.kb(args.base))]
    elif not args.all and base_of_cwd():
        roots = [str(kbpaths.kb(base_of_cwd()))]
    else:
        roots = [str(kbpaths.kb(b)) for b in kbpaths.BASES]
    many = len(roots) > 1
    only = set(x.strip() for x in args.only.split(",") if x.strip())
    texts, found, total_err = [], [], 0
    for root in roots:
        if not os.path.isdir(root):
            print("нет папки базы: %s" % root, file=sys.stderr)
            return 2
        rep, files = run_checks(root, only, not args.no_raw)
        text, err = render(rep, files, root, only, args.quiet_info)
        total_err += err
        texts.append(text)
        found += [{"base": os.path.basename(root), "check": c, "level": l, "path": p, "line": n, "message": m}
                  for (c, l, p, n, m) in rep.items]
        if args.out or many:
            print(text.split("\n\n=")[0])
            if many:
                print()
        else:
            sys.stdout.write(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(texts))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(found, fh, ensure_ascii=False, indent=1)
    if many:
        print("ВСЕГО по %d базам: ERROR %d" % (len(roots), total_err))
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
