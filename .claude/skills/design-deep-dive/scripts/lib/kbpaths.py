#!/usr/bin/env python3
"""kbpaths — пути скилла design-deep-dive и окружения его утилит. Только стандартная библиотека.

Утилиты скилла находят базу, соседние утилиты, данные, выходы, блокировки, бинарники и ключи через этот модуль, а не
через пути, зашитые в код. Корень скилла вычисляется от этого файла (`scripts/lib/kbpaths.py` → два уровня вверх),
поэтому скилл работает в любом клоне шаблона и из соседнего чекаута: репозиторий кода запускает
`../strategy/.claude/skills/design-deep-dive/scripts/…` со своей рабочей папкой, и пути ведут в чекаут стратегии.
`repo()` — репозиторий, в котором лежит скилл; файлы проектов `docs/projects/<slug>/` утилиты находят через соседний
модуль `docpaths` (корень данных — ключ `--repo`, переменная DDD_REPO или этот репозиторий). Окружение (venv, npm,
бинарники, модели, браузеры, выходы, блокировки) живёт вне репозитория: `$DDD_HOME`, иначе
`$XDG_CACHE_HOME/design-deep-dive`, иначе `~/.cache/design-deep-dive` — одно на машину для всех клонов.

Подключение в утилите `scripts/<домен>/<утилита>.py`:

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
    import kbpaths

    kbpaths.kb("site", "02-site-types", "vocabulary.yaml")   # файл базы site
    kbpaths.skill_version()                                     # версия скилла: файл VERSION
    kbpaths.use("ui"); import ui_audit                          # модуль соседнего домена
    kbpaths.out("creative", "audit")                            # каталог выходов (создаётся)
    with kbpaths.lock("browser"): ...                           # общая блокировка браузера, с ожиданием

Блокировка реентерабельна по дереву процессов: пока замок взят, его файл назван в переменной окружения DDD_LOCKS_HELD,
и вложенный `lock()` — в том же процессе или в утилите, запущенной из него, — замок не берёт и не ждёт. Внешний `flock`
на файл замка утилитам не нужен: под ним утилита ждёт обёртку до таймаута.

Байт-код в папку скилла не пишется: импорт модуля ставит запрет этому процессу и переменной PYTHONDONTWRITEBYTECODE —
дочерним, а кэш модулей скилла, импортированных до запрета (и этого файла), снимает сам.

Диагностика: `python3 kbpaths.py` — где что лежит; `python3 kbpaths.py --bins` — внешние программы (путь, переменная
окружения, версия); `python3 kbpaths.py --selftest` — самопроверка без сети, с запуском из соседнего чекаута во
временной папке.
"""
import contextlib
import fcntl
import os
import shutil
import sys
import time
from pathlib import Path

LIB = Path(__file__).resolve().parent                  # .../design-deep-dive/scripts/lib
SCRIPTS = LIB.parent                                    # .../design-deep-dive/scripts
SKILL = SCRIPTS.parent                                  # .../.claude/skills/design-deep-dive
KB = SKILL / "kb"
ASSETS = SKILL / "assets"

BASES = ("ux", "ui", "site", "text", "creative", "ai-media", "3d", "claude-design")
DOMAINS = BASES + ("lib", "maint", "tests", "project")  # папки scripts/; project — утилиты по файлам docs/projects/

ENV_HOME = "DDD_HOME"
ENV_LOCKS = "DDD_LOCKS_HELD"                            # файлы замков, взятых этим процессом или его предком
ENV_BIN = {                                             # переопределение пути к бинарнику (иначе $DDD_HOME/bin, затем PATH)
    "blender": "DDD_BLENDER",
    "node": "DDD_NODE",
    "npx": "DDD_NPX",
    "npm": "DDD_NPM",
    "ffmpeg": "DDD_FFMPEG",
    "ffprobe": "DDD_FFPROBE",
    "brave": "DDD_BRAVE",
    "chromium": "DDD_CHROMIUM",
}


# ------------------------------------------------------------------ имена

def base_name(name):
    """Имя базы (`kb/<база>/`); неизвестное имя — ValueError."""
    n = str(name).strip().strip("/")
    if n not in BASES:
        raise ValueError(f"неизвестная база: {name!r} (есть: {', '.join(BASES)})")
    return n


def domain_name(name):
    """Имя папки утилит (`scripts/<домен>/`); неизвестное имя — ValueError."""
    n = str(name).strip().strip("/")
    if n not in DOMAINS:
        raise ValueError(f"неизвестный домен scripts/: {name!r} (есть: {', '.join(DOMAINS)})")
    return n


# ------------------------------------------------------------------ скилл и репозиторий

def skill(*parts):
    """Корень скилла `.claude/skills/design-deep-dive/` (+ части пути)."""
    return SKILL.joinpath(*parts)


def repo(*parts):
    """Корень репозитория, в котором лежит скилл: skill → skills → .claude → корень. Канон форм проекта
    (`docs/projects/_template/`) берут отсюда; корень данных проектов для утилит — `docpaths.root()`."""
    return SKILL.parents[2].joinpath(*parts)


def skill_version():
    """Версия скилла — строка файла `VERSION` в его корне: версия контракта утилит с репозиторием кода, её несут
    манифест готовности и JSON ворот страницы, copy deck и сверки фактов. Нет файла или он пуст — None."""
    try:
        return (SKILL / "VERSION").read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def kb(base=None, *parts):
    """База знаний: kb() — `kb/`, kb("site", "04-blocks", "blocks.yaml") — файл базы."""
    if base is None:
        return KB.joinpath(*parts)
    return KB.joinpath(base_name(base), *parts)


def scripts(domain=None, *parts):
    """Утилиты: scripts() — `scripts/`, scripts("ai-media", "page_accept.py") — файл утилиты домена."""
    if domain is None:
        return SCRIPTS.joinpath(*parts)
    return SCRIPTS.joinpath(domain_name(domain), *parts)


def data(domain, *parts):
    """Данные, которые читает только код: `scripts/<домен>/data/…`."""
    return scripts(domain, "data", *parts)


def assets(*parts):
    """Ассеты скилла (`assets/calibration/…`)."""
    return ASSETS.joinpath(*parts)


def use(domain):
    """Подключить модули соседнего домена: добавить `scripts/<домен>/` в sys.path (один раз). Возвращает путь."""
    p = str(scripts(domain))
    if p not in sys.path:
        sys.path.insert(0, p)
    return Path(p)


# ------------------------------------------------------------------ окружение вне репозитория

def home(*parts):
    """Домашний каталог окружения: $DDD_HOME → $XDG_CACHE_HOME/design-deep-dive → ~/.cache/design-deep-dive."""
    h = os.environ.get(ENV_HOME)
    if h:
        base = Path(h).expanduser()
    else:
        xdg = os.environ.get("XDG_CACHE_HOME")
        base = (Path(xdg).expanduser() if xdg else Path.home() / ".cache") / "design-deep-dive"
    return base.joinpath(*parts)


def _dir(p, create):
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def venv(*parts):
    return home("venv", *parts)


def python():
    """Python окружения скилла (venv с зависимостями), иначе текущий интерпретатор."""
    p = venv("bin", "python")
    return str(p) if p.exists() else sys.executable


def node_home(*parts):
    """Каталог npm-зависимостей: `$DDD_HOME/node/` (package.json скилла ставится сюда)."""
    return home("node", *parts)


def node_modules(*parts):
    return node_home("node_modules", *parts)


def bin_dir(*parts):
    """Бинарники, которые ставит install.sh: `$DDD_HOME/bin/`."""
    return home("bin", *parts)


def models(*parts):
    """Модели ONNX: `$DDD_HOME/models/`."""
    return home("models", *parts)


def browsers():
    """Браузеры Playwright, если их ставил install.sh: `$DDD_HOME/browsers/`."""
    return home("browsers")


def out(domain, *parts, create=True):
    """Каталог выходов утилиты: `$DDD_HOME/out/<домен>/…` (создаётся)."""
    return _dir(home("out", domain_name(domain), *parts), create)


def cache(domain, *parts, create=True):
    """Каталог кэша утилиты (снимки каталогов, ответы API): `$DDD_HOME/cache/<домен>/…` (создаётся)."""
    return _dir(home("cache", domain_name(domain), *parts), create)


# ------------------------------------------------------------------ блокировки

def locks_dir(create=True):
    return _dir(home("locks"), create)


def lock_path(name="browser", domain=None):
    """Файл блокировки. Общая на машину: lock_path("browser") → `$DDD_HOME/locks/browser.lock`. Своя у домена:
    lock_path("browser", "site") → `$DDD_HOME/locks/site/browser.lock`."""
    d = locks_dir()
    if domain is not None:
        d = _dir(d / domain_name(domain), True)
    return str(d / f"{name}.lock")


def locks_held():
    """Файлы замков, которые уже держит этот процесс или его предок: абсолютные пути из переменной DDD_LOCKS_HELD."""
    return [p for p in os.environ.get(ENV_LOCKS, "").split(os.pathsep) if p]


def lock_held(name="browser", domain=None):
    """Взят ли замок этим процессом или его предком. Утилита со своим `flock` на файл замка спрашивает здесь, прежде
    чем брать его: повторная блокировка того же файла ждала бы держателя до таймаута."""
    return os.path.abspath(lock_path(name, domain)) in locks_held()


@contextlib.contextmanager
def lock(name="browser", domain=None, timeout=900.0, poll=0.5):
    """Исключительная блокировка flock с ожиданием (до timeout секунд, затем TimeoutError); None — ждать без предела.

    Реентерабельна по дереву процессов: пока замок взят, его файл назван в переменной окружения DDD_LOCKS_HELD, и
    вложенный вызов — в этом процессе или в утилите, запущенной из него с этим окружением, — замок не берёт и не
    ждёт; процесс без переменной ждёт держателя. Внешний `flock` на файл замка утилитам не нужен: под ним утилита
    ждёт обёртку до таймаута. Обёртка, которая держит замок сама, называет его файл в DDD_LOCKS_HELD."""
    path = lock_path(name, domain)
    mark = os.path.abspath(path)
    if mark in locks_held():
        yield path
        return
    f = open(path, "a")
    t0 = time.monotonic()
    try:
        while True:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if timeout is not None and time.monotonic() - t0 > timeout:
                    raise TimeoutError(f"{path} занят дольше {timeout:.0f} с")
                time.sleep(poll)
        os.environ[ENV_LOCKS] = os.pathsep.join(locks_held() + [mark])
        try:
            yield path
        finally:
            rest = [p for p in locks_held() if p != mark]
            if rest:
                os.environ[ENV_LOCKS] = os.pathsep.join(rest)
            else:
                os.environ.pop(ENV_LOCKS, None)
    finally:
        try:
            fcntl.flock(f, fcntl.LOCK_UN)
        finally:
            f.close()


# ------------------------------------------------------------------ бинарники, Node, Playwright, ключи

def find(name, env=None, names=(), dirs=()):
    """Путь к бинарнику или None: переменная окружения (env или DDD_<ИМЯ> из ENV_BIN) → `$DDD_HOME/bin/<имя>`,
    `$DDD_HOME/bin/<имя>/<имя>` или `$DDD_HOME/bin/<папка>/<имя>` для папок dirs → `$DDD_HOME/node/node_modules/.bin/<имя>`
    → PATH; names — другие имена того же бинарника."""
    var = env or ENV_BIN.get(name)
    if var and os.environ.get(var):
        return os.environ[var]
    for n in (name,) + tuple(names):
        cands = [bin_dir(n), bin_dir(n, n)] + [bin_dir(d, n) for d in dirs] + [node_modules(".bin", n)]
        for cand in cands:
            if cand.is_file() and os.access(cand, os.X_OK):
                return str(cand)
        p = shutil.which(n)
        if p:
            return p
    return None


def which(name, env=None, names=(), dirs=()):
    """Путь к бинарнику, как `find()`. Не найден — возвращает имя как есть: ошибка проявится при вызове, а импорт и
    --help утилиты работают без бинарника."""
    return find(name, env, names, dirs) or name


BIN_LOOKUP = {                                          # как искать внешние программы: find() и отчёт --bins
    "blender": {},
    "node": {},
    "npx": {},
    "npm": {},
    "ffmpeg": {},
    "ffprobe": {"dirs": ("ffmpeg",)},                   # статическая сборка install.sh --ffmpeg: $DDD_HOME/bin/ffmpeg/
    "brave": {"names": ("brave-browser", "brave-browser-stable")},
}
BIN_VERSION = {"blender": "--version", "node": "--version", "npm": "--version", "ffmpeg": "-version",
               "ffprobe": "-version", "brave": "--version"}


def blender():
    return which("blender")


def node():
    return which("node")


def npx():
    return which("npx")


def ffmpeg():
    return which("ffmpeg")


def ffprobe():
    return which("ffprobe", **BIN_LOOKUP["ffprobe"])


def brave():
    return which("brave", **BIN_LOOKUP["brave"])


def node_env(env=None):
    """Окружение для вызова node/npx: PATH с каталогом node и `node_modules/.bin` скилла, NODE_PATH на node_modules."""
    e = dict(os.environ if env is None else env)
    extra = [str(node_modules(".bin"))]
    n = node()
    if os.sep in n:
        extra.append(os.path.dirname(n))
    e["PATH"] = os.pathsep.join(extra + [e.get("PATH", "")])
    e.setdefault("NODE_PATH", str(node_modules()))
    return e


def playwright_env(env=None):
    """Окружение для Playwright: PLAYWRIGHT_BROWSERS_PATH на `$DDD_HOME/browsers`, если браузеры поставлены туда
    и переменная не задана; иначе Playwright ищет браузеры в своём месте по умолчанию."""
    e = dict(os.environ if env is None else env)
    b = browsers()
    if "PLAYWRIGHT_BROWSERS_PATH" not in e and b.is_dir():
        e["PLAYWRIGHT_BROWSERS_PATH"] = str(b)
    return e


def key(name, required=False):
    """Ключ API — только из переменной окружения владельца (в репозитории ключей нет)."""
    v = os.environ.get(name)
    if required and not v:
        raise SystemExit(f"нет ключа: задайте переменную окружения {name}")
    return v


def _init_env():
    """Окружение процесса утилиты: браузеры Playwright из `$DDD_HOME/browsers`, если их ставил install.sh; статическая
    сборка ffmpeg из `$DDD_HOME/bin/ffmpeg/` — первой в PATH (утилиты и их подпроцессы зовут ffmpeg и ffprobe по имени)."""
    b = browsers()
    if "PLAYWRIGHT_BROWSERS_PATH" not in os.environ and b.is_dir():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(b)
    ff = bin_dir("ffmpeg")
    path = os.environ.get("PATH", "")
    if ff.is_dir() and str(ff) not in path.split(os.pathsep):
        os.environ["PATH"] = os.pathsep.join([str(ff), path]) if path else str(ff)


def _no_bytecode():
    """Байт-код в папку скилла не пишется: запрет — этому процессу, переменная PYTHONDONTWRITEBYTECODE — дочерним.
    Кэш модуля пишется до исполнения его кода, поэтому запрет не застаёт этот файл и модули скилла, импортированные
    раньше него: их кэш в `scripts/**/__pycache__/` снимается здесь, пустая папка кэша — тоже. Порядок импорта в
    утилите значения не имеет."""
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    if sys.dont_write_bytecode:
        return
    sys.dont_write_bytecode = True
    import importlib.util
    sources = {str(Path(__file__).resolve())}
    for mod in list(sys.modules.values()):
        src = getattr(mod, "__file__", None)
        if isinstance(src, str) and src.endswith(".py"):
            sources.add(src)
    frame = sys._getframe()
    while frame is not None:                            # загруженного по пути файла модуля в sys.modules может не быть
        src = frame.f_globals.get("__file__")
        if isinstance(src, str) and src.endswith(".py"):
            sources.add(src)
        frame = frame.f_back
    root = str(SCRIPTS) + os.sep
    for src in sources:
        try:
            if not os.path.realpath(src).startswith(root):
                continue
            pyc = importlib.util.cache_from_source(src)
            folder = os.path.dirname(pyc)
            if os.path.basename(folder) != "__pycache__" or not os.path.realpath(pyc).startswith(root):
                continue                                # кэш вынесен из папки скилла (PYTHONPYCACHEPREFIX) — не наш
            os.unlink(pyc)
            os.rmdir(folder)                            # снимается только пустая папка
        except (OSError, ValueError, NotImplementedError):
            continue


_init_env()
_no_bytecode()


# ------------------------------------------------------------------ диагностика

def describe():
    rows = [("skill", SKILL), ("version", skill_version() or "— нет файла VERSION"), ("repo", repo()), ("kb", KB),
            ("scripts", SCRIPTS), ("home", home()),
            ("python", python()), ("node_modules", node_modules()), ("bin", bin_dir()), ("models", models()),
            ("browsers", browsers()), ("locks", home("locks")), ("out", home("out")), ("cache", home("cache"))]
    for b in BASES:
        rows.append((f"kb/{b}", kb(b)))
    for n in ("blender", "node", "npx", "ffmpeg", "ffprobe", "brave"):
        rows.append((n, find(n, **BIN_LOOKUP[n]) or "— не найден"))
    return rows


def bins(version=True):
    """Внешние программы: [(имя, переменная окружения, путь или None, первая строка версии или None)]."""
    import subprocess
    rows = []
    for n, how in BIN_LOOKUP.items():
        p = find(n, **how)
        v = None
        if p and version and n in BIN_VERSION:
            try:
                r = subprocess.run([p, BIN_VERSION[n]], capture_output=True, text=True, timeout=30)
                v = next((ln.strip() for ln in (r.stdout or r.stderr).splitlines() if ln.strip()), None)
            except (OSError, subprocess.SubprocessError):
                v = None
        rows.append((n, ENV_BIN.get(n, "-"), p, v))
    return rows


SIBLING_UTILITY = ("site", "page_gates.py", "--resolve", "landing-lead-services@L1")   # утилита базы и её вызов
SIBLING_KB = ("site", "07-seo-geo-performance-analytics", "budgets.yaml")               # файл базы, который она читает


def _sibling_check(check):
    """Соседний чекаут: копия скилла в `<tmp>/strategy/.claude/skills/design-deep-dive/` (lib, одна утилита базы и файл
    базы, который она читает), рабочая папка `<tmp>/site/`, запуск по пути `../strategy/…` — пути ведут в копию."""
    import importlib.util
    import subprocess
    import tempfile
    rel = Path("..", "strategy", ".claude", "skills", "design-deep-dive")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="ddd-sibling-") as td:
        t = Path(td).resolve()
        copy = t / "strategy" / ".claude" / "skills" / "design-deep-dive"
        shutil.copytree(LIB, copy / "scripts" / "lib", ignore=shutil.ignore_patterns("__pycache__"))
        cwd = t / "site"
        cwd.mkdir()
        r = subprocess.run([sys.executable, str(rel / "scripts" / "lib" / "kbpaths.py")], cwd=cwd, env=env,
                           capture_output=True, text=True, timeout=120)
        got = dict(ln.split(None, 1) for ln in r.stdout.splitlines() if len(ln.split(None, 1)) == 2)
        check("соседний чекаут: kbpaths.py из ../strategy/… — skill, kb и repo в копии, не в рабочей папке",
              r.returncode == 0 and got.get("skill") == str(copy) and got.get("kb") == str(copy / "kb")
              and got.get("repo") == str(t / "strategy"))
        util = SCRIPTS / SIBLING_UTILITY[0] / SIBLING_UTILITY[1]
        src = kb(*SIBLING_KB)
        if not (util.is_file() and src.is_file()) or importlib.util.find_spec("yaml") is None:
            print("SKIP соседний чекаут: нет утилиты базы, её файла или PyYAML у этого Python")
            return
        (copy / "scripts" / SIBLING_UTILITY[0]).mkdir(parents=True)
        shutil.copy2(util, copy / "scripts" / SIBLING_UTILITY[0] / SIBLING_UTILITY[1])
        dst = copy / "kb" / Path(*SIBLING_KB)
        dst.parent.mkdir(parents=True)
        shutil.copy2(src, dst)
        cmd = [sys.executable, str(rel / "scripts" / SIBLING_UTILITY[0] / SIBLING_UTILITY[1]), *SIBLING_UTILITY[2:]]
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)
        check(f"соседний чекаут: {SIBLING_UTILITY[1]} {' '.join(SIBLING_UTILITY[2:])} читает базу копии",
              r.returncode == 0 and r.stdout.strip())
        dst.unlink()
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)
        check("соседний чекаут: без файла базы в копии утилита падает — чужая база не подхватывается", r.returncode != 0)


LOCK_PROBE = ("import sys\nsys.path.insert(0, sys.argv[1])\nimport kbpaths\n"
              "try:\n    with kbpaths.lock('browser', timeout=float(sys.argv[2]), poll=0.05):\n        pass\n"
              "except TimeoutError:\n    sys.exit(3)\n")       # проба: взял замок — 0, не дождался — 3


def _lock_check(check):
    """Реентерабельность замка в `$DDD_HOME` самопроверки: вложенный вызов в том же процессе и в дочернем процессе
    не ждёт, независимый процесс (без переменной держателя) ждёт до таймаута."""
    import subprocess

    def probe(env, timeout):
        t0 = time.monotonic()
        r = subprocess.run([sys.executable, "-c", LOCK_PROBE, str(LIB), str(timeout)], env=env, capture_output=True,
                           text=True, timeout=120)
        return r.returncode, time.monotonic() - t0

    free = {k: v for k, v in os.environ.items() if k != ENV_LOCKS}
    with lock("browser", timeout=5) as p:
        check("lock() берёт блокировку", os.path.exists(p))
        check("lock(): взятый замок назван в DDD_LOCKS_HELD, соседний — нет",
              lock_held("browser") and not lock_held("browser", "site"))
        t0 = time.monotonic()
        with lock("browser", timeout=5):
            nested = time.monotonic() - t0
        check("lock(): вложенный вызов в том же процессе не ждёт, замок остаётся за держателем",
              nested < 1 and lock_held("browser"))
        rc, spent = probe(dict(os.environ), 5)
        check("lock(): дочерний процесс с переменной держателя замок не берёт и не ждёт", rc == 0 and spent < 4)
        rc, spent = probe(free, 1)
        check("lock(): независимый процесс ждёт держателя до таймаута", rc == 3 and spent >= 1)
    check("lock(): после выхода замок свободен и из переменной убран",
          not lock_held("browser") and ENV_LOCKS not in os.environ and probe(free, 5)[0] == 0)


def _bytecode_check(check):
    """Запрет байт-кода при любом порядке импорта: копия lib и модули-пробы во временной папке, запуск без запрета в
    окружении. Модуль до kbpaths, сам kbpaths, модуль после него и дочерний процесс папок `__pycache__` не оставляют."""
    import subprocess
    import tempfile
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX")}
    with tempfile.TemporaryDirectory(prefix="ddd-bytecode-") as td:
        root = Path(td).resolve() / "skill" / "scripts"
        shutil.copytree(LIB, root / "lib", ignore=shutil.ignore_patterns("__pycache__"))
        dom = root / "ui"
        dom.mkdir()
        for n in ("early", "late", "child"):
            (dom / f"probe_{n}.py").write_text("X = 1\n", encoding="utf-8")
        head = "import os, subprocess, sys\nsys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), sys.argv[1]]\n"
        (dom / "control.py").write_text(head + "import probe_early\n", encoding="utf-8")
        (dom / "probe.py").write_text(
            head + "import probe_early\nimport kbpaths\nimport probe_late\n"
            "subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, sys.argv[1]); import probe_child',\n"
            "                sys.path[0]], check=True)\n", encoding="utf-8")

        def run(name):
            r = subprocess.run([sys.executable, str(dom / name), str(root / "lib")], env=env, capture_output=True,
                               text=True, timeout=120)
            return r.returncode, sorted(root.rglob("__pycache__"))

        rc, cached = run("control.py")
        if rc != 0 or not cached:
            print("SKIP байт-код: этот Python не пишет кэш и без запрета")
            return
        for d in cached:
            shutil.rmtree(d)
        rc, cached = run("probe.py")
        check("байт-код: модуль до kbpaths, kbpaths, модуль после и дочерний процесс не оставляют __pycache__",
              rc == 0 and not cached)


def _selftest():
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)

    check("корень скилла от файла: scripts/lib → skill", LIB.name == "lib" and SCRIPTS.name == "scripts")
    check("kb('site') — kb/site", kb("site") == KB / "site")
    try:
        kb("no-such-base")
        check("неизвестная база — ValueError", False)
    except ValueError:
        check("неизвестная база — ValueError", True)
    check("scripts('ai-media', 'x.py')", scripts("ai-media", "x.py") == SCRIPTS / "ai-media" / "x.py")
    check("data('3d')", data("3d") == SCRIPTS / "3d" / "data")
    check("домен project: scripts('project')", scripts("project") == SCRIPTS / "project")
    check("repo() — репозиторий скилла: .claude/skills/<скилл> внутри", SKILL == repo(".claude", "skills", SKILL.name))
    check("skill_version() — строка файла VERSION корня скилла (<major>.<minor>.<patch>)",
          skill_version() == (SKILL / "VERSION").read_text(encoding="utf-8").strip()
          and len(str(skill_version()).split(".")) == 3)
    with tempfile.TemporaryDirectory() as td:
        old = os.environ.get(ENV_HOME)
        old_path = os.environ.get("PATH", "")
        os.environ[ENV_HOME] = td
        try:
            check("DDD_HOME переопределяет home()", home() == Path(td))
            check("out() создаёт каталог", out("ui", "audit").is_dir())
            check("out('project') создаёт каталог", out("project", "canvas").is_dir())
            check("cache() создаёт каталог", cache("ai-media", "polza").is_dir())
            check("lock_path общая", lock_path() == str(Path(td) / "locks" / "browser.lock"))
            check("lock_path домена", lock_path("browser", "site") == str(Path(td) / "locks" / "site" / "browser.lock"))
            _lock_check(check)
            os.environ["DDD_BLENDER"] = "/nonexistent/blender"
            check("DDD_BLENDER переопределяет поиск", blender() == "/nonexistent/blender")
            del os.environ["DDD_BLENDER"]
            check("не найденный бинарник — имя как есть", which("ddd-no-such-binary") == "ddd-no-such-binary")
            check("не найденный бинарник — find() даёт None", find("ddd-no-such-binary") is None)
            ffdir = bin_dir("ffmpeg")
            ffdir.mkdir(parents=True)
            for n in ("ffmpeg", "ffprobe"):
                (ffdir / n).write_text("#!/bin/sh\n")
                (ffdir / n).chmod(0o755)
            saved = {v: os.environ.pop(v) for v in ("DDD_FFMPEG", "DDD_FFPROBE") if v in os.environ}
            check("статическая сборка: ffmpeg() и ffprobe() находят $DDD_HOME/bin/ffmpeg/",
                  ffmpeg() == str(ffdir / "ffmpeg") and ffprobe() == str(ffdir / "ffprobe"))
            _init_env()
            check("статическая сборка: $DDD_HOME/bin/ffmpeg первой в PATH (ffprobe по имени)",
                  shutil.which("ffprobe") == str(ffdir / "ffprobe"))
            os.environ.update(saved)
        finally:
            os.environ["PATH"] = old_path
            if old is None:
                os.environ.pop(ENV_HOME, None)
            else:
                os.environ[ENV_HOME] = old
    check("key() без переменной — None", key("DDD_NO_SUCH_KEY_FOR_TEST") is None)
    before = list(sys.path)
    use("ui")
    check("use('ui') добавляет scripts/ui в sys.path", str(SCRIPTS / "ui") in sys.path)
    sys.path[:] = before
    _sibling_check(check)
    _bytecode_check(check)
    print("kbpaths selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__)
        sys.exit(0)
    if "--bins" in sys.argv[1:]:
        for n, var, p, v in bins():
            print(f"{n}\t{var}\t{p or ''}\t{v or ''}")
        sys.exit(0)
    for k, v in describe():
        print(f"{k:<16} {v}")
