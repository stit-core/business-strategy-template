#!/usr/bin/env python3
"""run_recipes.py — сквозной прогон рецептов kb/3d/12-recipes: блоки ```python рецепта (в напечатанном виде, по порядку) →
один скрипт examples/<slug>/build.py → Blender 5.2.2 без окна (blender_run.py) → для каждого <name>.glb в examples/<slug>/
(кроме *_raw, *_ar): валидатор Khronos (gltf_check.py --json) и three r186 в Chromium (web_view.py, тонмаппинг Neutral).
Блок пропускается, если в его первой строке есть «[не проверено]» или «[не исполняется]»; блоки с первой строкой
«# run: system» собираются в examples/<slug>/post.py и идут Python окружения скилла после Blender.

    python3 run_recipes.py РЕЦЕПТ.md [ещё.md …] [--no-web]     # путь рецепта — от рабочей папки или полный
    python3 run_recipes.py --selftest                           # без Blender и браузера: разбор блоков, пути утилит и
                                                                # результата, пути numbers.json (rk.portable)

Утилиты зовутся из scripts/3d/ (пути — scripts/lib/kbpaths.py), рабочая папка вызовов — корень базы kb/3d.
Собранный образец рецепта (build.py, post.py, GLB, числа, web/<name>/) лежит в examples/<slug>/ базы; результат прогона —
$DDD_HOME/out/3d/run_recipes/result.json (по slug: код выхода, время, блоки, веб-проверки), новый прогон дополняет файл.
Код выхода: 0 — прогон выполнен (коды рецептов — в result.json и в итоговой строке stdout), 2 — ошибка вызова."""
import glob, json, os, re, subprocess, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb("3d"))
TOOLS = str(kbpaths.scripts("3d"))
PY = kbpaths.python()                                       # Python окружения скилла: утилиты и блоки «# run: system»
RES = str(kbpaths.out("3d", "run_recipes") / "result.json")
USED = ("blender_run.py", "gltf_check.py", "web_view.py")  # утилиты scripts/3d, которые зовёт прогон


def tool(name):
    return os.path.join(TOOLS, name)


def blocks(md):
    src = open(md, encoding="utf-8").read()
    out = []
    for m in re.finditer(r"```python\n(.*?)```", src, re.S):
        code = m.group(1)
        first = code.split("\n", 1)[0]
        line = src[:m.start()].count("\n") + 1
        skip = "[не проверено]" in first or "[не исполняется]" in first
        out.append({"line": line, "code": code, "skip": skip, "system": first.startswith("# run: system")})
    return out


def run(cmd, timeout=600):
    t = time.time()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return r, round(time.time() - t, 1)


def selftest():
    """Без Blender и браузера: разбор блоков рецепта (пропуски, системные блоки, номера строк), пути утилит и результата,
    пути numbers.json — rk.portable (функция берётся из исходника rk.py: модуль импортирует bpy)."""
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)
    md = ("# Рецепт-образец\n\n```python\n# Blender — сборка\nprint(1)\n```\n\nтекст\n\n```python\n# отрывок [не исполняется]\nx()\n```\n\n"
          "```python\n# run: system\nprint(2)\n```\n\n```python\n# проба [не проверено]\ny()\n```\n\n```bash\necho 3\n```\n")
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "90-sample.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(md)
        bl = blocks(p)
    check("блоки python рецепта: 4, блок bash в прогон не входит", len(bl) == 4)
    check("номера строк блоков — по файлу рецепта", [b["line"] for b in bl] == [3, 10, 15, 20])
    check("«[не исполняется]» и «[не проверено]» в первой строке — пропуск", [b["skip"] for b in bl] == [False, True, False, True])
    check("«# run: system» в первой строке — блок Python окружения, не Blender", [b["system"] for b in bl] == [False, False, True, False])
    check("утилиты прогона лежат в scripts/3d: " + ", ".join(USED), all(os.path.isfile(tool(n)) for n in USED))
    check("результат — $DDD_HOME/out/3d/run_recipes/result.json",
          os.path.normpath(RES) == os.path.normpath(str(kbpaths.home("out", "3d", "run_recipes", "result.json"))))
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    raw = "99-" + "raw"
    check("в коде нет путей материала к разбору и вызова утилит через python3 из PATH",
          raw not in src and '"python' + '3"' not in src)
    me = os.path.abspath(__file__)
    rc = {k: subprocess.run([sys.executable, me] + a, capture_output=True, text=True).returncode
          for k, a in (("help", ["--help"]), ("none", []), ("flag", ["--no-web"]), ("lost", [os.path.join(td, "none.md")]))}
    check("вызов: --help — код 0; без рецептов и с несуществующим файлом — код 2", rc == {"help": 0, "none": 2, "flag": 2, "lost": 2})
    import ast
    tree = ast.parse(open(tool("rk.py"), encoding="utf-8").read())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "portable")
    ns = {"os": os, "kbpaths": kbpaths}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), tool("rk.py"), "exec"), ns)
    with tempfile.TemporaryDirectory() as td:
        num = {"passport": {"glb": f"{ROOT}/12-recipes/examples/04-sample/form_raw.glb", "dims_m": [0.1, 0.2]},
               "renders": [os.path.join(td, "shot.png")], "sec_total": 1.5}
        p = os.path.join(td, "numbers.json")
        json.dump(ns["portable"](num, f"{ROOT}/12-recipes/examples/90-sample"), open(p, "w"), ensure_ascii=False)
        text = open(p, encoding="utf-8").read()
        back = json.loads(text)
    check("rk.save: пути numbers.json — внутри скилла от папки примера, вне скилла — имя файла; абсолютных путей нет",
          back == {"passport": {"glb": "../04-sample/form_raw.glb", "dims_m": [0.1, 0.2]}, "renders": ["shot.png"],
                   "sec_total": 1.5} and ROOT not in text and td not in text)
    print("run_recipes selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(__doc__); sys.exit(0)
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    web = "--no-web" not in sys.argv
    lost = [a for a in args if not (a.endswith(".md") and os.path.isfile(a))]
    if not args or lost:
        print("run_recipes.py: " + ("нет файла рецепта .md: " + ", ".join(lost) if lost else "нужен хотя бы один рецепт .md")
              + " (справка: --help)", file=sys.stderr)
        sys.exit(2)
    res = json.load(open(RES)) if os.path.exists(RES) else {}
    for md in args:
        md = os.path.abspath(md)
        slug = os.path.basename(md)[:-3]
        bl = blocks(md)
        ex = f"{ROOT}/12-recipes/examples/{slug}"
        os.makedirs(ex, exist_ok=True)
        run_bl = [b for b in bl if not b["skip"] and not b["system"]]
        sys_bl = [b for b in bl if not b["skip"] and b["system"]]
        rec = {"md": os.path.relpath(md, ROOT), "blocks_python": len(bl), "blocks_run": len(run_bl),
               "blocks_skipped_lines": [b["line"] for b in bl if b["skip"]]}
        if run_bl:
            script = f"{ex}/build.py"
            with open(script, "w", encoding="utf-8") as f:
                f.write(f"# Сгенерировано run_recipes.py из {rec['md']} — блоки python в напечатанном виде, по порядку.\n")
                for b in run_bl:
                    f.write(f"\n# ---- блок со строки {b['line']}\n{b['code']}")
            r, sec = run([PY, tool("blender_run.py"), script, "--timeout", "600"])
            rec.update(exit=r.returncode, sec=sec, tail=(r.stdout + r.stderr)[-1500:])
            print(f"[{slug}] blender exit={r.returncode} {sec}s")
        if sys_bl and rec.get("exit", 0) == 0:          # блоки «# run: system» — Python окружения скилла (Pillow, ffmpeg)
            script = f"{ex}/post.py"
            with open(script, "w", encoding="utf-8") as f:
                f.write(f"# Сгенерировано run_recipes.py из {rec['md']} — блоки «run: system» в напечатанном виде.\n")
                for b in sys_bl:
                    f.write(f"\n# ---- блок со строки {b['line']}\n{b['code']}")
            r, sec = run([PY, script])
            rec.update(system_exit=r.returncode, system_sec=sec, system_tail=(r.stdout + r.stderr)[-1200:])
            print(f"[{slug}] system exit={r.returncode} {sec}s")
            if r.returncode != 0:
                rec["exit"] = 100 + r.returncode
        if web and rec.get("exit", 0) == 0:
            rec["web"] = {}
            for glb in sorted(glob.glob(f"{ex}/*.glb")):
                name = os.path.basename(glb)[:-4]
                if name.endswith("_raw") or name.endswith("_ar"):
                    continue
                w = {}
                r, sec = run([PY, tool("gltf_check.py"), glb, "--json"], timeout=180)
                try:
                    j = json.loads(r.stdout)
                    v = j.get("validator", j)
                    w["validator"] = {k: v.get(k) for k in ("numErrors", "numWarnings")} if isinstance(v, dict) else None
                    if w["validator"] is None or w["validator"].get("numErrors") is None:
                        iss = (j.get("validator") or {}).get("issues") or j.get("issues") or {}
                        w["validator"] = {k: iss.get(k) for k in ("numErrors", "numWarnings")}
                except Exception as e:  # noqa
                    w["validator_raw"] = (r.stdout + r.stderr)[-400:]
                out = f"{ex}/web/{name}"
                r, sec = run([PY, tool("web_view.py"), glb, out, "--tone", "neutral", "--views", "4",
                              "--size", "800x600"], timeout=300)
                w["web_view_exit"], w["web_view_sec"] = r.returncode, sec
                st = f"{out}/stats.json" if os.path.exists(f"{out}/stats.json") else f"{out}/web_stats.json"
                if os.path.exists(st):
                    s = json.load(open(st))
                    info = s.get("info") or {}
                    w["three"] = {"rev": info.get("three"), "load_ms": info.get("load_ms"), "meshes": info.get("meshes"),
                                  "materials": info.get("materials"), "textures": info.get("textures"),
                                  "max_tex": info.get("max_texture_px"), "types": info.get("material_types"),
                                  "anims": len(info.get("animations") or []), "frame_time": s.get("frame_time"),
                                  "console": s.get("console")}
                rec["web"][name] = w
                print(f"[{slug}] web {name}: {w.get('validator')} exit={w['web_view_exit']}")
        res[slug] = rec
        json.dump(res, open(RES, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: {kk: v.get(kk) for kk in ("exit", "sec", "blocks_run")} for k, v in res.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
