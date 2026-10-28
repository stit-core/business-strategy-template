#!/usr/bin/env python3
"""Запуск Python-кода в Blender без окна (background) с таймаутом, кодом выхода и журналом.

Использование:
    python3 blender_run.py script.py [--blend file.blend] [--timeout 600] [--user-prefs] [--log path] [--all] [-- аргументы скрипта]
    python3 blender_run.py --expr "import bpy; print(bpy.app.version_string)"
    python3 blender_run.py --version

Что делает:
    - запускает `blender -b [--factory-startup] [file.blend] --python-exit-code 1 --python script.py -- args`;
      по умолчанию --factory-startup: чистые настройки без пользовательских аддонов (MCP, MPFB), чтобы
      запуск был воспроизводим; --user-prefs — с настройками и аддонами пользователя;
    - аргументы после `--` скрипт читает так: `argv = sys.argv[sys.argv.index("--") + 1:]`;
    - код выхода: 0 — успех, 1 — исключение в скрипте, 124 — таймаут;
    - вывод фильтруется от шума рендера (строки Fra:, прогресс сэмплов); --all печатает всё;
    - полный журнал всегда сохраняется в $DDD_HOME/out/3d/logs/<имя>_<время>.log (или --log).

Blender: DDD_BLENDER или blender из PATH (5.2.2 LTS). EEVEE в фоне работает через EGL на видеокарте машины, Cycles без
GPU — на CPU. Параллельно работают несколько агентов: держи рендеры маленькими
(≤ 1024 px, Cycles ≤ 64 сэмплов), ставь таймаут и не оставляй процессы висеть.
"""
import os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import kbpaths  # noqa: E402
LOGDIR = str(kbpaths.out("3d", "logs"))
BLENDER = kbpaths.blender()
NOISE = re.compile(r"^(Fra:\d+|\s*$|.*\| (Sample|Rendering|Updating|Loading render kernels|Synchronizing|Initializing|Compiling|Waiting|Finishing).*|Read blend:|Color management:.*|.*Compositing.*|.*\bRemaining:.*)")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if a[0] == "--version":
        r = subprocess.run([BLENDER, "--version"], capture_output=True, text=True)
        print(r.stdout.splitlines()[0] if r.stdout else r.stderr); return
    script_args = []
    if "--" in a:
        i = a.index("--"); script_args = a[i + 1:]; a = a[:i]

    def opt(name, default=None):
        if name in a:
            v = a[a.index(name) + 1]; return v
        return default

    timeout = int(opt("--timeout", 600))
    blend = opt("--blend")
    expr = opt("--expr")
    log = opt("--log")
    show_all = "--all" in a
    user_prefs = "--user-prefs" in a
    script = None
    if not expr:
        script = next((x for x in a if x.endswith(".py")), None)
        if not script:
            print("Нужен script.py или --expr"); sys.exit(2)
        script = os.path.abspath(script)
    cmd = [BLENDER, "-b"]
    if not user_prefs:
        cmd.append("--factory-startup")
    if blend:
        cmd.append(os.path.abspath(blend))
    cmd += ["--python-exit-code", "1"]
    cmd += ["--python-expr", expr] if expr else ["--python", script]
    if script_args:
        cmd += ["--"] + script_args
    os.makedirs(LOGDIR, exist_ok=True)
    name = os.path.splitext(os.path.basename(script))[0] if script else "expr"
    log = log or os.path.join(LOGDIR, f"{name}_{time.strftime('%Y%m%d-%H%M%S')}.log")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out, code = (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        out += (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        out += f"\n[blender_run] ТАЙМАУТ {timeout} с\n"; code = 124
    dt = time.time() - t0
    with open(log, "w", encoding="utf-8") as f:
        f.write("$ " + " ".join(cmd) + "\n\n" + out + f"\n[blender_run] exit={code} time={dt:.1f}s\n")
    lines = out.splitlines()
    if not show_all:
        lines = [l for l in lines if not NOISE.match(l)]
    print("\n".join(lines[-400:]))
    print(f"[blender_run] exit={code} time={dt:.1f}s log={log}")
    sys.exit(code)


if __name__ == "__main__":
    main()
