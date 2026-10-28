#!/usr/bin/env python3
"""blender_supervisor.py — фоновый Blender 5.2 под надзором для агента.

Один процесс Blender на рабочую папку WORK. Каждый вызов — транзакция: успех → контрольная точка .blend,
ошибка → откат к последней точке. Падение, убийство по таймауту или зависание → перезапуск и восстановление
из последней точки. Журнал JSONL — WORK/sup/journal.jsonl (код, итог, время, события процесса).
Связь — Unix-сокет WORK/sup/blender.sock (права 0600, не TCP: работает и в песочнице без сети).

  python3 blender_supervisor.py start WORK [--mem 4G] [--cpu 400%] [--sandbox] [--online] [--keep 5]
  python3 blender_supervisor.py exec WORK script.py [--timeout 120] [--no-checkpoint] [-- арг1 арг2]
  python3 blender_supervisor.py status WORK | stop WORK | replay WORK journal.jsonl
Код выхода exec: 0 — успех, 1 — исключение в коде (сцена откатена), 2 — процесс убит/упал (восстановлен).
[проверено: падения процесса и песочница --sandbox]
"""
import argparse, json, os, shutil, signal, socket, subprocess, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

BLENDER = os.environ.get("BLENDER") or kbpaths.blender()
GRACE, HB_MAX, START_MAX = 5.0, 30.0, 90.0          # с: запас к таймауту, тишина в простое, старт процесса
SOCK_MAX = 107                                      # sizeof(sockaddr_un.sun_path) Linux — 108 байт минус '\0'

WORKER = r'''
import bpy, contextlib, hashlib, io, json, os, socket, sys, time, traceback
W = os.environ["SUP_WORK"]; S = os.path.join(W, "sup"); C = os.path.join(W, "checkpoints")
KEEP = int(os.environ.get("SUP_KEEP", "5")); TAIL = 65536
def wfile(p, text):
    with open(p, "w") as f:
        f.write(text)
def jlog(rec):
    with open(os.path.join(S, "journal.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": round(time.time(), 3), **rec}, ensure_ascii=False, default=str) + "\n")
def ckpts():
    return sorted(os.path.join(C, n) for n in os.listdir(C) if n.startswith("ckpt_") and n.endswith(".blend"))
def restore(first=False):
    c = ckpts()
    if c:
        bpy.ops.wm.open_mainfile(filepath=c[-1], load_ui=False)
        return c[-1]
    if not first:
        bpy.ops.wm.read_homefile(use_factory_startup=True)
    return None
def next_seq():
    p = os.path.join(S, "seq"); n = int(open(p).read()) + 1 if os.path.exists(p) else 1
    wfile(p, str(n)); return n
def handle(req):
    if req.get("op") == "ping":
        return {"ok": True, "pid": os.getpid(), "file": bpy.data.filepath, "objects": len(bpy.data.objects)}
    seq, code, t0, name = next_seq(), req["code"], time.time(), req.get("name", "<agent>")
    busy = os.path.join(S, "busy.json")
    wfile(busy, json.dumps({"seq": seq, "deadline": t0 + float(req.get("timeout", 120))}))
    buf, err, ck, back = io.StringIO(), None, None, None
    argv0 = sys.argv[:]; sys.argv = [name, "--", *req.get("args", [])]
    try:
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(code, name, "exec"), {"__name__": "__main__", "__file__": name, "bpy": bpy})
        except BaseException as e:        # SystemExit и KeyboardInterrupt тоже: процесс остаётся жив
            err = {"type": type(e).__name__, "message": str(e)[:2000], "traceback": traceback.format_exc()[-6000:]}
        sys.argv = argv0; dt = round(time.time() - t0, 3)
        if err is None and req.get("checkpoint", True):
            ck = os.path.join(C, "ckpt_%06d.blend" % seq)
            bpy.ops.wm.save_as_mainfile(filepath=ck, copy=True)
            for old in ckpts()[:-KEEP]:
                os.remove(old)
        elif err is not None:
            back = restore()                  # транзакция: сцена = последняя удачная точка
    finally:
        sys.argv = argv0; os.remove(busy)
    out = buf.getvalue()
    res = {"ok": err is None, "seq": seq, "dt": dt, "error": err, "checkpoint": ck, "reverted_to": back,
           "stdout_bytes": len(out.encode()), "stdout": out[-TAIL:]}
    jlog({"ev": "run", "seq": seq, "name": name, "ok": res["ok"], "dt": dt, "error": err, "checkpoint": ck,
          "reverted_to": back, "stdout_tail": out[-2000:], "args": req.get("args", []),
          "code_sha256": hashlib.sha256(code.encode()).hexdigest(), "code": code})
    return res
os.makedirs(C, exist_ok=True)
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); path = os.path.join(S, "blender.sock")
if os.path.exists(path):
    os.remove(path)
t_ready = time.time(); got = restore(first=True)
srv.bind(path); os.chmod(path, 0o600); srv.listen(4); srv.settimeout(1.0)
jlog({"ev": "ready", "pid": os.getpid(), "blender": bpy.app.version_string, "restored": got,
      "restore_s": round(time.time() - t_ready, 3), "online_access": bpy.app.online_access})
while not os.path.exists(os.path.join(S, "STOP")):
    wfile(os.path.join(S, "hb"), str(time.time()))
    try:
        conn, _ = srv.accept()
    except socket.timeout:
        continue
    with conn:
        conn.settimeout(30); raw = b""
        while not raw.endswith(b"\n"):
            chunk = conn.recv(1 << 20)
            if not chunk:
                break
            raw += chunk
        try:
            resp = handle(json.loads(raw))
        except Exception as e:
            resp = {"ok": False, "error": {"type": type(e).__name__, "message": str(e)}}
        with contextlib.suppress(OSError):
            conn.sendall(json.dumps(resp, ensure_ascii=False, default=str).encode() + b"\n")
srv.close(); os.remove(path); jlog({"ev": "stopped", "pid": os.getpid()})
'''


def sup_dir(work):
    return os.path.join(os.path.abspath(work), "sup")


def jlog(work, rec):
    with open(os.path.join(sup_dir(work), "journal.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": round(time.time(), 3), **rec}, ensure_ascii=False) + "\n")


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def journal(work, since):
    p = os.path.join(sup_dir(work), "journal.jsonl")
    with open(p, encoding="utf-8") as f:
        return [e for e in map(json.loads, f) if e["ts"] >= since]


def bwrap_prefix(work, blender_dir, online, keep):
    """Песочница по белому списку: /usr, /etc, /sys и Blender — только чтение, запись — только WORK;
    /home, /run, /media, /var нет вовсе; без сети, без чужих процессов и без переменных окружения родителя."""
    a = ["bwrap", "--die-with-parent", "--unshare-all", "--new-session", "--ro-bind", "/usr", "/usr",
         "--symlink", "usr/bin", "/bin", "--symlink", "usr/sbin", "/sbin", "--symlink", "usr/lib", "/lib",
         "--symlink", "usr/lib64", "/lib64", "--ro-bind", "/etc", "/etc", "--ro-bind", "/sys", "/sys",
         "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
         "--ro-bind", blender_dir, blender_dir, "--bind", work, work, "--chdir", work, "--clearenv",
         "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", work, "--setenv", "LANG", "C.UTF-8",
         "--setenv", "TMPDIR", os.path.join(work, "tmp"), "--setenv", "SUP_WORK", work,
         "--setenv", "SUP_KEEP", str(keep)]
    if os.path.isdir("/dev/dri"):
        a += ["--dev-bind", "/dev/dri", "/dev/dri"]      # GPU для EEVEE через EGL
    return a + (["--share-net"] if online else [])


def launch_cmd(work, o):
    real = os.path.realpath(BLENDER)
    cmd = [real, "-b", "--factory-startup", "-Y", "--online-mode" if o.online else "--offline-mode",
           "--python-exit-code", "1", "--python", os.path.join(sup_dir(work), "worker.py")]
    if o.sandbox:
        cmd = bwrap_prefix(work, os.path.dirname(real), o.online, o.keep) + ["--"] + cmd
    if o.mem or o.cpu:                    # cgroup v2 через systemd --user; без MemorySwapMax=0 лимит уходит в своп
        lim = ["systemd-run", "--user", "--scope", "-q", "--collect"]
        lim += ["-p", "MemoryMax=" + o.mem, "-p", "MemorySwapMax=0"] if o.mem else []
        lim += ["-p", "CPUQuota=" + o.cpu] if o.cpu else []
        cmd = lim + ["--"] + cmd
    return ["nice", "-n", "10"] + cmd


def nanny(work, o):
    """Держит один Blender живым: перезапуск после падения, убийство по таймауту шага и по тишине."""
    s, tmp = sup_dir(work), os.path.join(work, "tmp")
    env = dict(os.environ, SUP_WORK=work, SUP_KEEP=str(o.keep), TMPDIR=tmp)
    starts, stop, hbp, busyp = [], os.path.join(s, "STOP"), os.path.join(s, "hb"), os.path.join(s, "busy.json")
    while not os.path.exists(stop):
        starts = [t for t in starts if time.time() - t < 120] + [time.time()]
        if len(starts) > 5:
            jlog(work, {"ev": "give_up", "why": "более 5 перезапусков за 120 с"}); break
        with open(os.path.join(s, "blender.log"), "ab") as log:
            p = subprocess.Popen(launch_cmd(work, o), env=env, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        t0, why = time.time(), None
        with open(os.path.join(s, "state.json"), "w") as f:
            json.dump({"nanny": os.getpid(), "pid": p.pid, "started": t0}, f)
        jlog(work, {"ev": "spawn", "pid": p.pid, "sandbox": o.sandbox, "mem": o.mem, "cpu": o.cpu})
        while p.poll() is None:
            time.sleep(0.25)
            busy = read_json(busyp)
            hb = os.path.getmtime(hbp) if os.path.exists(hbp) else 0
            if busy and time.time() > busy["deadline"] + GRACE:
                why = {"ev": "timeout_kill", "seq": busy["seq"]}
            elif not busy and hb > t0 and time.time() - hb > HB_MAX:
                why = {"ev": "hang_kill", "hb_age": round(time.time() - hb, 1)}
            elif hb <= t0 and time.time() - t0 > START_MAX:
                why = {"ev": "start_timeout"}
            if why:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                p.wait()
        rc, busy = p.returncode, read_json(busyp)
        if busy:
            os.remove(busyp)
        crash = sorted((os.path.join(tmp, n) for n in os.listdir(tmp) if n.endswith(".crash.txt")),
                       key=os.path.getmtime)
        jlog(work, {**(why or {"ev": "exit"}), "rc": rc, "signal": -rc if rc and rc < 0 else rc - 128 if rc and rc > 128 else None,
                    "uptime": round(time.time() - t0, 2), "lost_seq": (busy or {}).get("seq"),
                    "crash_log": crash[-1] if crash and os.path.getmtime(crash[-1]) >= t0 else None})
    jlog(work, {"ev": "nanny_exit"})


def call(work, req, wait):
    path, t0 = os.path.join(sup_dir(work), "blender.sock"), time.time()
    while True:                                          # ждём готовности (после старта или перезапуска)
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            c.connect(path); break
        except OSError:
            c.close()
            if time.time() - t0 > START_MAX:
                return {"ok": False, "error": {"type": "NotRunning", "message": "нет сокета " + path}}
            time.sleep(0.2)
    c.settimeout(wait); c.sendall(json.dumps(req, ensure_ascii=False).encode() + b"\n"); raw = b""
    try:
        while not raw.endswith(b"\n"):
            chunk = c.recv(1 << 20)
            if not chunk:
                break
            raw += chunk
    except socket.timeout:
        pass
    c.close()
    if raw.endswith(b"\n"):
        return json.loads(raw)
    while time.time() - t0 < wait + START_MAX:           # процесс умер: ждём причину и восстановление
        evs = [e for e in journal(work, t0) if e["ev"] != "run"]
        if any(e["ev"] in ("ready", "give_up") for e in evs if e["ts"] > t0):
            break
        time.sleep(0.5)
    return {"ok": False, "error": {"type": "WorkerDied", "message": "Blender убит или упал; сцена восстановлена "
            "из последней контрольной точки (см. events: ready.restored)"}, "events": evs}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["start", "exec", "status", "stop", "replay", "_nanny"])
    ap.add_argument("work")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--mem"); ap.add_argument("--cpu"); ap.add_argument("--keep", type=int, default=5)
    ap.add_argument("--sandbox", action="store_true"); ap.add_argument("--online", action="store_true")
    ap.add_argument("--no-checkpoint", action="store_true")
    argv = sys.argv[1:]; cut = argv.index("--") if "--" in argv else len(argv)
    o, extra = ap.parse_args(argv[:cut]), argv[cut + 1:]
    work = os.path.abspath(o.work); s = sup_dir(work)
    if o.cmd == "start":
        sock_path = os.path.join(s, "blender.sock")
        sock_len = len(sock_path.encode())
        if sock_len > SOCK_MAX:                     # иначе call() ждёт START_MAX (90 с) и падает «нет сокета»
            sys.exit(f"путь Unix-сокета {sock_len} байт > {SOCK_MAX} (sockaddr_un.sun_path короче ОС не даст "
                     f"привязать): {sock_path!r} — укажи WORK короче")
        st = read_json(os.path.join(s, "state.json"), {})
        if st.get("nanny") and os.path.exists("/proc/%d" % st["nanny"]) and not os.path.exists(os.path.join(s, "STOP")):
            sys.exit("уже запущен: nanny %d" % st["nanny"])
        for d in (s, os.path.join(work, "tmp"), os.path.join(work, "checkpoints")):
            os.makedirs(d, exist_ok=True)
        os.chmod(s, 0o700)
        for n in ("STOP", "busy.json", "hb"):
            if os.path.exists(os.path.join(s, n)):
                os.remove(os.path.join(s, n))
        with open(os.path.join(s, "worker.py"), "w") as f:
            f.write(WORKER)
        fwd = [a for k, v in (("--mem", o.mem), ("--cpu", o.cpu)) if v for a in (k, v)]
        fwd += ["--keep", str(o.keep)] + ["--sandbox"] * o.sandbox + ["--online"] * o.online
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "_nanny", work] + fwd,
                         start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(json.dumps(call(work, {"op": "ping"}, 30), ensure_ascii=False))
    elif o.cmd == "_nanny":
        nanny(work, o)
    elif o.cmd == "exec":
        code = sys.stdin.read() if o.file in (None, "-") else open(o.file, encoding="utf-8").read()
        req = {"code": code, "name": os.path.abspath(o.file) if o.file not in (None, "-") else "<stdin>",
               "args": extra, "timeout": o.timeout, "checkpoint": not o.no_checkpoint}
        r = call(work, req, o.timeout + GRACE + 10)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        sys.exit(0 if r.get("ok") else 2 if r.get("error", {}).get("type") in ("WorkerDied", "NotRunning") else 1)
    elif o.cmd == "status":
        st, hb = read_json(os.path.join(s, "state.json"), {}), os.path.join(s, "hb")
        st["hb_age"] = round(time.time() - os.path.getmtime(hb), 1) if os.path.exists(hb) else None
        st["busy"] = read_json(os.path.join(s, "busy.json"))
        st["checkpoints"] = sorted(os.listdir(os.path.join(work, "checkpoints")))[-3:]
        print(json.dumps(st, ensure_ascii=False))
    elif o.cmd == "stop":
        open(os.path.join(s, "STOP"), "w").close()
        st = read_json(os.path.join(s, "state.json"), {})
        for _ in range(40):
            if not os.path.exists(os.path.join(s, "blender.sock")):
                break
            time.sleep(0.25)
        else:
            if st.get("pid"):
                os.killpg(st["pid"], signal.SIGTERM)
        print(json.dumps({"stopped": True, "pid": st.get("pid")}))
    elif o.cmd == "replay":                              # повтор удачных шагов журнала в запущенном WORK
        with open(o.file, encoding="utf-8") as f:
            steps = [e for e in map(json.loads, f) if e.get("ev") == "run" and e.get("ok")]
        for e in steps:
            r = call(work, {"code": e["code"], "name": e.get("name") or "<replay>", "args": e.get("args", []),
                            "timeout": o.timeout, "checkpoint": True}, o.timeout + GRACE + 10)
            print(json.dumps({"replayed": e["seq"], "ok": r.get("ok"), "error": r.get("error")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
