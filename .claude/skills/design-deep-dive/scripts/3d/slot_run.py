#!/usr/bin/env python3
"""slot_run.py — очередь для тяжёлых запусков, когда на машине параллельно работают несколько агентов.

    python3 slot_run.py [--kind blender|browser|none] [--heavy] [--min-mem MB] [--wait SEC] [--label ИМЯ] -- КОМАНДА …
    python3 slot_run.py --status          # кто стоит в очередях (ресурс, место, метка, порог памяти, сколько ждёт)

    --kind blender (умолчание) — занять один из 2 слотов Blender ($DDD_HOME/locks/blender-slot-{1,2}.lock);
    --kind browser — занять общий замок браузера ($DDD_HOME/locks/browser.lock — тот, что берут утилиты с браузером);
    --kind none    — только проверка памяти;
    --heavy        — сначала занять $DDD_HOME/locks/render.lock (Cycles, секвенции, запекание — один такой запуск на
                     машине), потом слот: так тяжёлый запуск в очереди не держит слот, а лёгким остаётся второй;
    --min-mem MB   — ждать, пока MemAvailable ≥ MB (умолчание 2500, для --heavy 3000);
    --wait SEC     — сколько ждать замков и памяти (умолчание 5400), потом код выхода 75;
    --label ИМЯ    — подпись в журнале (задача).

Команда получает stdout/stderr как есть; код выхода — её код; 75 — не дождались замков или памяти.
Журнал всех запусков — $DDD_HOME/locks/slot_run.log (одна строка на старт и на конец): по нему видно очередь и время.
Замки снимаются сами при выходе процесса (flock на открытом файле), даже если команда упала.

Очередь честная, по номерку (FIFO): у каждого ресурса (render, browser, blender-slot) своя очередь номерков
$DDD_HOME/locks/q-<ресурс>/<time_ns>-<pid> (внутри — метка и порог памяти); пробовать замок может только тот, перед кем в
очереди нет «готовых» (готовый — живой процесс, которому сейчас хватает памяти); новая задача встаёт в конец. Кому не
хватает памяти, тот пропускает вперёд тех, кому хватает, но номерок сохраняет и замков, ожидая память, не держит; после
взятия всех замков память перепроверяется — если её не стало, замки отпускаются, номерки остаются. Мёртвые номерки
(процесс умер) и номерки старше 12 ч убираются сами. Не вкладывать --heavy внутрь --kind browser (browser → render против
render → browser — взаимная блокировка).

Наследование замков: slot_run передаёт команде переменную SLOT_RUN_HOLDS (render, browser, slot — что держит он и его
родители); вложенный slot_run уже удержанное не берёт (строка журнала START … nested=…), берёт только недостающее. Файлы
замков браузера и рендера, которые держит очередь, названы команде в DDD_LOCKS_HELD (`kbpaths.lock`): утилита с браузером
под slot_run этот замок не ждёт. Прогон из нескольких коротких замеров ставится одной задачей:
    slot_run.py --kind browser --heavy --label gates -- bash run_gates.sh …
так обёртывают только замеры (до 15 мин на задачу), рендеры — пачками.

Короткие вперёд: в очереди render тихие замеры (--kind browser --heavy) идут раньше рендер-пачек (--kind blender --heavy);
рендер, ждущий дольше SLOT_RUN_STARVE (1200 с), поднимается вперёд со своим номерком и не голодает.
Для самопроверки: переменная окружения SLOT_RUN_LOCKS=<папка> подменяет $DDD_HOME/locks.
"""
import fcntl
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

LOCKS = os.environ.get("SLOT_RUN_LOCKS", str(kbpaths.locks_dir()))
SLOTS = [os.path.join(LOCKS, f"blender-slot-{i}.lock") for i in (1, 2)]
RENDER = os.path.join(LOCKS, "render.lock")
BROWSER = os.path.join(LOCKS, "browser.lock")
JOURNAL = os.path.join(LOCKS, "slot_run.log")
QUEUES = ("render", "browser", "slot")
POLL = 1.0
STALE_NS = 12 * 3600 * 10 ** 9
STARVE_S = float(os.environ.get("SLOT_RUN_STARVE", 1200))  # рендер, ждущий дольше, идёт вперёд тихих замеров


def mem_available_mb():
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    return 0


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} pid={os.getpid()} {msg}\n"
    try:
        with open(JOURNAL, "a") as f:
            f.write(line)
    except OSError:
        pass


def try_lock(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o664)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        os.close(fd)
        return None


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def qdir(res):
    return os.path.join(LOCKS, "q-" + res)


def entries(res):
    """Живые номерки очереди res по порядку: [(имя, pid, t_ns, метка, порог)]; мёртвые и старые удаляются."""
    d = qdir(res)
    out = []
    try:
        names = sorted(os.listdir(d))
    except FileNotFoundError:
        return out
    now = time.time_ns()
    for name in names:
        p = os.path.join(d, name)
        try:
            ts, pid = name.split("-")
            ts, pid = int(ts), int(pid)
        except ValueError:
            continue
        if not pid_alive(pid) or now - ts > STALE_NS:
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass
            continue
        try:
            f = open(p).read().rstrip("\n").split("\t")
            label, mm = f[0], int(f[1])
            cls = int(f[2]) if len(f) > 2 else 1
        except (OSError, ValueError, IndexError):
            label, mm, cls = "?", 0, 1
        out.append((name, pid, ts, label, mm, cls))
    return out


class Ticket:
    """Номерок в очереди ресурса; имя (время постановки + pid) не меняется до выхода — место не теряется."""

    def __init__(self, res, name, label, min_mem, cls=1):
        self.res = res
        self.name = name
        self.cls = cls
        self.path = os.path.join(qdir(res), name)
        self.body = f"{label}\t{min_mem}\t{cls}\n"
        self.put()

    def put(self):
        os.makedirs(qdir(self.res), exist_ok=True)
        with open(self.path, "w") as f:
            f.write(self.body)

    def drop(self):
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def ready_ahead(self, avail):
        """Сколько живых ждущих впереди, которым хватает памяти прямо сейчас (они идут первыми).
        Только очередь render: тихие замеры (класс 0) идут раньше рендеров (класс 1); рендер, ждущий > STARVE_S,
        получает класс 0 со своим старым номерком (не голодает); внутри класса — по номерку (FIFO)."""
        now = time.time_ns()

        def key(name, ts, cls):
            if self.res != "render":
                return (0, name)
            return (0 if cls == 0 or (now - ts) / 1e9 > STARVE_S else 1, name)
        me = key(self.name, int(self.name.split("-")[0]), self.cls)
        return sum(1 for (name, _pid, ts, _l, mm, cls) in entries(self.res)
                   if name != self.name and key(name, ts, cls) < me and mm <= avail)


def status():
    now = time.time_ns()
    any_ = False
    for res in QUEUES:
        for k, (name, pid, ts, label, mm, cls) in enumerate(entries(res), 1):
            any_ = True
            tag = ("тихий" if cls == 0 else "рендер") if res == "render" else ""
            print(f"{res:7s} #{k:<2d} {label:28s} pid={pid:<8d} порог={mm:>5d} МБ  ждёт {(now - ts) / 1e9 / 60:5.1f} мин  {tag}")
    if not any_:
        print("очереди пусты")
    print(f"MemAvailable {mem_available_mb()} МБ")
    return 0


def main():
    a = sys.argv[1:]
    if a[:1] == ["--status"]:
        return status()
    if "--" not in a or a.index("--") == len(a) - 1:
        print(__doc__)
        return 2
    i = a.index("--")
    opts, cmd = a[:i], a[i + 1:]

    def opt(name, default=None):
        return opts[opts.index(name) + 1] if name in opts else default

    kind = opt("--kind", "blender")
    heavy = "--heavy" in opts
    min_mem = int(opt("--min-mem", 3000 if heavy else 2500))
    deadline = time.time() + int(opt("--wait", 5400))
    label = opt("--label", os.path.basename(cmd[0])).replace("\t", " ")
    t_q = time.time()

    # что брать и в каком порядке: render → слот или браузер
    need = []
    if heavy:
        need.append(("render", [RENDER]))
    if kind == "blender":
        need.append(("slot", SLOTS))
    elif kind == "browser":
        need.append(("browser", [BROWSER]))
    # замки, которые уже держит внешний slot_run (переменная SLOT_RUN_HOLDS от родителя), не берутся повторно —
    # весь прогон ворот встаёт в очередь одной задачей, вложенные вызовы проходят сразу
    holds = set(filter(None, os.environ.get("SLOT_RUN_HOLDS", "").split(",")))
    inherited = [res for res, _ in need if res in holds]
    need = [(res, paths) for res, paths in need if res not in holds]
    child_env = dict(os.environ)
    child_env["SLOT_RUN_HOLDS"] = ",".join(sorted(holds | {res for res, _ in need}))
    # файлы замков браузера и рендера, которые держит очередь, — в DDD_LOCKS_HELD: kbpaths.lock в команде их не ждёт
    named = [os.path.abspath(p) for res, p in (("browser", BROWSER), ("render", RENDER))
             if res in child_env["SLOT_RUN_HOLDS"].split(",")]
    if named:
        child_env[kbpaths.ENV_LOCKS] = os.pathsep.join(dict.fromkeys(kbpaths.locks_held() + named))

    name = f"{time.time_ns():020d}-{os.getpid()}"
    tickets = {}

    def ticket(res):
        # номерок следующего ресурса ставится, когда до него дошли (тяжёлый, ждущий render, не держит очередь слотов),
        # и живёт до старта команды — при откате место сохраняется
        if res not in tickets:
            tickets[res] = Ticket(res, name, label, min_mem, 0 if (heavy and kind == "browser") else 1)
        return tickets[res]

    if need:
        ticket(need[0][0])
    held, slot = [], "-"
    said = 0.0
    try:
        while True:
            # 1) память — до замков (ждущий памяти замков не держит и пропускает тех, кому хватает)
            avail = mem_available_mb()
            ok = avail >= min_mem
            # 2) замки по порядку, без удержания при неудаче; пробовать можно, только если впереди нет готовых
            if ok:
                for res, paths in need:
                    if ticket(res).ready_ahead(avail) > 0:
                        ok = False
                        break
                    fd, got = None, None
                    for p in paths:
                        fd = try_lock(p)
                        if fd is not None:
                            got = p
                            break
                    if fd is None:
                        ok = False
                        break
                    held.append(fd)
                    if res == "slot":
                        slot = os.path.basename(got)
                    elif res == "browser":
                        slot = "browser"
            # 3) перепроверка памяти после замков
            if ok and mem_available_mb() >= min_mem:
                break
            for fd in held:  # не вышло — отпустить всё, номерки остаются (место в очереди сохраняется)
                os.close(fd)
            held, slot = [], "-"
            now = time.time()
            if now > deadline:
                why = "память" if mem_available_mb() < min_mem else "замки"
                log(f"TIMEOUT label={label} ждал {why} {now - t_q:.0f}s mem={mem_available_mb()} < {min_mem}?")
                return 75
            if now - said > 60:
                pos = {res: 1 + sum(1 for e in entries(res) if e[0] < name) for res in tickets}
                where = ", ".join(f"{r} №{p}" for r, p in pos.items()) or "только память"
                print(f"[slot_run] жду: {where}; память {mem_available_mb()} МБ (порог {min_mem})", file=sys.stderr, flush=True)
                said = now
            time.sleep(POLL)
    finally:
        for t in tickets.values():
            t.drop()
    waited = time.time() - t_q
    nested = f" nested={'+'.join(inherited)}" if inherited else ""
    log(f"START label={label} kind={kind} slot={slot} heavy={int(heavy)}{nested} waited={waited:.0f}s mem={mem_available_mb()} cmd={' '.join(cmd)[:200]}")
    t0 = time.time()
    try:
        code = subprocess.call(cmd, env=child_env)
    except KeyboardInterrupt:
        code = 130
    log(f"END   label={label} exit={code} time={time.time() - t0:.0f}s mem={mem_available_mb()}")
    return code


if __name__ == "__main__":
    sys.exit(main())
