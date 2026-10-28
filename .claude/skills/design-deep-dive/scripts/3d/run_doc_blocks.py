#!/usr/bin/env python3
"""run_doc_blocks.py — исполнить блоки кода итоговых .md базы в напечатанном виде.

    python3 run_doc_blocks.py FILE.md [FILE2.md …] [--json result.json] [--only python,bash] [--timeout 600] [--keep]
    python3 run_doc_blocks.py FILE.md [FILE2.md …] --dry-run [--json plan.json] [--only python,bash]
    python3 run_doc_blocks.py --selftest

python → один фоновый Blender 5.2.2 (blender_run.py); перед каждым блоком read_factory_settings(use_empty=True), своё
         пространство имён, stdout перехвачен; блок с первой строкой «# run: system» — Python, которым запущена утилита.
bash   → `bash -e -c` (переменная OUT_DIR — временная папка; --keep её оставляет).
js     → не исполняется: нужна страница с import map — помечается skip.
Рабочая папка всех блоков — корень базы kb/3d: пути в блоках пишутся от него (утилиты — ../../scripts/3d).
Блок пропускается, если в первых двух строках есть «[не проверено]» или «# run: skip». Итог — строка RESULT ok/total.
--dry-run — разбор блоков без запуска Blender, Python и bash: строка PLAN на блок (что с ним будет: blender, system, bash,
skip или js; язык; файл:строка; первая строка блока) и строка BLOCKS со счётом; --json пишет план.
Код выхода: 0 — все исполненные блоки прошли (у --dry-run — разбор выполнен), 1 — есть упавший блок.
"""
import json, os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb("3d"))
TOOLS = str(kbpaths.scripts("3d"))
RUNNER = r'''
import bpy, json, sys, traceback, io, contextlib
a = sys.argv[sys.argv.index("--") + 1:]
bl = json.load(open(a[0])); out = []
for b in bl:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ns = {"__name__": "__doc_block__"}; buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(b["code"], "%s:%d" % (b["doc"], b["line"]), "exec"), ns)
        out.append({"doc": b["doc"], "line": b["line"], "ok": True, "stdout": buf.getvalue()[-600:]})
    except Exception:
        out.append({"doc": b["doc"], "line": b["line"], "ok": False, "stdout": buf.getvalue()[-300:],
                    "error": traceback.format_exc()[-1500:]})
json.dump(out, open(a[1], "w"), ensure_ascii=False, indent=1)
print("BL_RUNNER_DONE", sum(o["ok"] for o in out), len(out))
'''


def blocks_of(path):
    src = open(path, encoding="utf-8").read()
    for m in re.finditer(r"^```(\w+)\n(.*?)^```", src, re.S | re.M):
        head = "\n".join(m.group(2).splitlines()[:2])
        yield {"doc": os.path.basename(path), "lang": m.group(1), "line": src[:m.start()].count("\n") + 1,
               "code": m.group(2), "skip": "[не проверено]" in head or "# run: skip" in head}


def action(b):
    """Что раннер делает с блоком: skip — пропуск по метке; blender — фоновый Blender; system — Python утилиты; bash;
    js — не исполняется; None — у языка нет исполнителя."""
    if b["skip"]:
        return "skip"
    if b["lang"] == "python":
        return "system" if b["code"].lstrip().startswith("# run: system") else "blender"
    if b["lang"] == "bash":
        return "bash"
    if b["lang"] in ("js", "javascript"):
        return "js"
    return None


def plan(blocks):
    """Разбор без исполнения: [{doc, line, lang, action, head}] по блокам и счёт по действиям."""
    rows = [{"doc": b["doc"], "line": b["line"], "lang": b["lang"], "action": action(b),
             "head": (b["code"].splitlines() or [""])[0][:160]} for b in blocks]
    count = {}
    for r in rows:
        count[r["action"] or "none"] = count.get(r["action"] or "none", 0) + 1
    return rows, count


def selftest():
    """Без Blender: разбор блоков вымышленного файла, действие на блок и вызов --dry-run."""
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)
    md = ("# Образец\n\n```python\n# сборка\nprint(1)\n```\n\n```python\n# run: system\nprint(2)\n```\n\n"
          "```python\n# отрывок [не проверено]\nx()\n```\n\n```bash\necho 3\n```\n\n```bash\n# шаг\n# run: skip — долго\necho 4\n```\n\n"
          "```js\nconsole.log(5)\n```\n\n```glsl\nvoid main() {}\n```\n\n```python\n# третья строка не метка\ny = 1\n# run: skip\n```\n")
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "sample.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(md)
        bl = list(blocks_of(p))
        check("блоки всех языков с номерами строк", [(b["lang"], b["line"]) for b in bl] ==
              [("python", 3), ("python", 8), ("python", 13), ("bash", 18), ("bash", 22), ("js", 28), ("glsl", 32), ("python", 36)])
        check("действие на блок: метка пропуска — в первых двух строках; «# run: system» — Python утилиты; у glsl исполнителя нет",
              [action(b) for b in bl] == ["blender", "system", "skip", "bash", "skip", "js", None, "blender"])
        rows, count = plan(bl)
        check("счёт плана по действиям", count == {"blender": 2, "system": 1, "skip": 2, "bash": 1, "js": 1, "none": 1})
        jp = os.path.join(td, "plan.json")
        env = dict(os.environ, DDD_BLENDER=os.path.join(td, "no-blender"))       # запуск Blender здесь дал бы ошибку
        r = subprocess.run([sys.executable, os.path.abspath(__file__), p, "--dry-run", "--json", jp], capture_output=True, text=True, env=env)
        check("--dry-run: код 0, строка PLAN на блок и BLOCKS со счётом, без исполнения (нет RESULT)",
              r.returncode == 0 and r.stdout.count("PLAN ") == 7 and "BLOCKS 7: blender 2, system 1, bash 1, js 1, skip 2" in r.stdout
              and "RESULT" not in r.stdout)
        check("--dry-run --json: план файлом", os.path.isfile(jp) and [x["action"] for x in json.load(open(jp, encoding="utf-8"))] ==
              ["blender", "system", "skip", "bash", "skip", "js", "blender"])
        r2 = subprocess.run([sys.executable, os.path.abspath(__file__), p, "--dry-run", "--only", "bash"], capture_output=True, text=True)
        check("--dry-run --only bash: только блоки bash", r2.returncode == 0 and "BLOCKS 2: bash 1, skip 1" in r2.stdout)
        p3, j3 = os.path.join(td, "cwd.md"), os.path.join(td, "cwd.json")
        with open(p3, "w", encoding="utf-8") as f:
            f.write("```python\n# run: system\nimport os\nprint(os.getcwd())\n```\n\n```bash\npwd\n```\n")
        r3 = subprocess.run([sys.executable, os.path.abspath(__file__), p3, "--json", j3], capture_output=True, text=True, cwd=td)
        got = [x.get("stdout", "").strip() for x in json.load(open(j3, encoding="utf-8"))] if os.path.isfile(j3) else []
        check("исполнение: рабочая папка блоков — корень базы kb/3d, а не папка вызова; RESULT 2/2, код 0",
              r3.returncode == 0 and "RESULT 2/2" in r3.stdout and got == [os.path.realpath(ROOT)] * 2)
    check("утилита запуска Blender — scripts/3d/blender_run.py", os.path.isfile(os.path.join(TOOLS, "blender_run.py")))
    print("run_doc_blocks selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if a[0] == "--selftest":
        sys.exit(selftest())
    opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    only = set((opt("--only") or "python,bash,js").split(","))
    docs = [x for x in a if x.endswith(".md")]
    blocks = [b for d in docs for b in blocks_of(d) if b["lang"] in only]
    if "--dry-run" in a:
        rows, count = plan(blocks)
        for r in rows:
            print("PLAN %-7s %-10s %s:%s  %s" % (r["action"] or "none", r["lang"], r["doc"], r["line"], r["head"]))
        if opt("--json"):
            json.dump(rows, open(opt("--json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        order = [k for k in ("blender", "system", "bash", "js", "skip", "none") if k in count]
        print("BLOCKS %d: %s" % (len(rows), ", ".join("%s %d" % (k, count[k]) for k in order)))
        sys.exit(0)
    tmp = tempfile.mkdtemp(prefix="docblocks_")
    env = dict(os.environ, OUT_DIR=tmp)
    res = []
    bl = [b for b in blocks if b["lang"] == "python" and not b["skip"] and not b["code"].lstrip().startswith("# run: system")]
    if bl:
        jp, op, rp = (os.path.join(tmp, n) for n in ("bl.json", "bl_out.json", "runner.py"))
        json.dump(bl, open(jp, "w"))
        open(rp, "w").write(RUNNER)
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "blender_run.py"), rp, "--timeout", opt("--timeout", "600"),
                            "--", jp, op], capture_output=True, text=True, env=env, cwd=ROOT)
        if os.path.exists(op):
            res += [dict(o, lang="python/blender") for o in json.load(open(op))]
        else:
            res.append({"lang": "python/blender", "ok": False, "error": r.stdout[-2000:] + r.stderr[-1000:]})
    for b in blocks:
        if b["skip"]:
            res.append({"lang": b["lang"], "doc": b["doc"], "line": b["line"], "ok": None, "note": "skip"})
        elif b["lang"] == "python" and b["code"].lstrip().startswith("# run: system"):
            p = os.path.join(tmp, "sys_%d.py" % b["line"]); open(p, "w").write(b["code"])
            q = subprocess.run([sys.executable, p], capture_output=True, text=True, env=env, cwd=ROOT, timeout=600)
            res.append({"lang": "python/system", "doc": b["doc"], "line": b["line"], "ok": q.returncode == 0,
                        "stdout": q.stdout[-600:], "error": q.stderr[-1500:] if q.returncode else ""})
        elif b["lang"] == "bash":
            q = subprocess.run(["bash", "-e", "-c", b["code"]], capture_output=True, text=True, env=env, cwd=ROOT, timeout=900)
            res.append({"lang": "bash", "doc": b["doc"], "line": b["line"], "ok": q.returncode == 0,
                        "stdout": q.stdout[-800:], "error": q.stderr[-1500:] if q.returncode else ""})
        elif b["lang"] in ("js", "javascript"):
            res.append({"lang": "js", "doc": b["doc"], "line": b["line"], "ok": None, "note": "js — нужна страница с import map"})
    ran = [r for r in res if r.get("ok") is not None]
    ok = sum(1 for r in ran if r["ok"])
    for r in res:
        mark = "SKIP" if r.get("ok") is None else ("OK  " if r["ok"] else "FAIL")
        print(mark, r.get("lang"), "%s:%s" % (r.get("doc"), r.get("line")), (r.get("error") or "")[-300:].replace("\n", " | "))
    if opt("--json"):
        json.dump(res, open(opt("--json"), "w"), ensure_ascii=False, indent=1)
    print("RESULT %d/%d (пропущено %d)" % (ok, len(ran), len(res) - len(ran)))
    if "--keep" not in a:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(0 if ok == len(ran) else 1)


if __name__ == "__main__":
    main()
