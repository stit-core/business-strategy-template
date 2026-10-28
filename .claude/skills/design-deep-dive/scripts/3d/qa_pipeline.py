#!/usr/bin/env python3
"""qa_pipeline.py — сводный конвейер проверок 3D: сцена → GLB → страница; JSON с порогами и вердиктом.
Тонкая обёртка над утилитами этой папки (ничего не считает сам):
  scene: scene_check.py и preflight() из preflight_block.py (kb/3d 08-export-gltf/04 §5) — в одном фоновом Blender;
  glb:   коллизии имён узлов после санитизации three → gltf_check.py (валидатор Khronos) → glb_lint() из glb_lint_block.py
         (08/04 §6) → gltf_web_inspect.py → [gltf_diff.py по копии .blend только с ASSET_*] → [gltf_load_bench.py];
  page:  site_probe.py → ворота 3D gate_check.evaluate() (пороги — kb/3d/09-web-runtime/page-3d-gates.yaml, описание —
         09/05 §7.2) + статическая проверка import map (одна версия three; min-ядро с jsDelivr — с переназначением three.core.js).

  python3 qa_pipeline.py scene A.blend [B.blend …] [--passport P.json | --passports MAP.json] [--out r.json] [--strict]
  python3 qa_pipeline.py glb M.glb [--blend S.blend --diff [--tone neutral] [--engine cycles]] [--bench] [--max-tris N] [--max-kb N]
                         [--out r.json] [--strict]
  python3 qa_pipeline.py page URL|DIR [--mobile] [--reduced] [--wait 16000] [--out r.json] [--strict]
  python3 qa_pipeline.py --selftest      # без Blender и браузера: вердикт page по тяжести строк ворот 3D и коды выхода

MAP.json для пакета: {"<имя файла без .blend>": {паспорт}, …}. Вердикт каждой стадии и общий: fail (есть ERROR) → review
(есть WARN) → pass. У page тяжесть строки ворот 3D решает уровень: провал B — ERROR (fail), провал S — WARN (review:
исправить или записать исключением плана), зеркала метрик страницы D — INFO; все строки — в поле gates, итог — gate_summary.
Вердикт собранной страницы по профилю бюджета ставит site/page_gates.py. Код выхода: 0 — замер выполнен (вердикт и находки — в
JSON: строка stdout и файл ключа --out; обёртка читает JSON), 2 — ошибка вызова или стадия не дала результата (поле error).
С --strict — выход по находкам: 1 — fail, 3 — review. Временные папки удаляются (--keep — оставить). Пороги gltf_diff —
kb/3d 11-evaluation-qa/03 §2.2.
"""
import json, os, re, shutil, struct, subprocess, sys, tempfile, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb("3d"))
TOOLS = str(kbpaths.scripts("3d"))
E26 = TOOLS  # preflight_block, glb_lint_block — scripts/3d
SERVE_BR = TOOLS  # serve_br — scripts/3d
RANK = {"pass": 0, "review": 1, "fail": 2}             # порядок вердиктов для worst(); коды выхода — exit_code()
STRICT_CODE = {"pass": 0, "fail": 1, "review": 3}     # выход по находкам (--strict): есть ERROR — 1, только WARN — 3

sys.path.insert(0, TOOLS)
from gate_check import evaluate, gate_check  # noqa: F401 — gate_check: кортежи ворот 3D для кода, который берёт их отсюда
GATE_LEVEL = {"B": "ERROR", "S": "WARN", "D": "INFO"}   # тяжесть строки ворот 3D → уровень находки: fail только у B

RUNNER = r'''
import bpy, io, json, sys, traceback
from contextlib import redirect_stdout
a = sys.argv[sys.argv.index("--") + 1:]
cfg = json.load(open(a[0]))
sc_code = open(cfg["scene_check"], encoding="utf-8").read()
pf_code = open(cfg["preflight"], encoding="utf-8").read()
res = {}
for f in cfg["files"]:
    r = {}
    try:
        bpy.ops.wm.open_mainfile(filepath=f)
    except Exception as e:
        res[f] = {"open_error": str(e)}
        continue
    P = cfg["passports"].get(f)
    code = sc_code.replace("\nPASSPORT = None\n", "\nPASSPORT = " + repr(P) + "\n", 1) if P else sc_code
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(code, {"bpy": bpy})
        line = [l for l in buf.getvalue().splitlines() if l.startswith("SCENE_CHECK ")][-1]
        r["scene_check"] = json.loads(line[len("SCENE_CHECK "):])
    except Exception:
        r["scene_check_error"] = traceback.format_exc()[-1500:]
    try:
        ns = {"__name__": "preflight"}
        exec(pf_code, ns)
        r["preflight"] = [list(x) for x in ns["preflight"]()]
    except Exception:
        r["preflight_error"] = traceback.format_exc()[-1500:]
    res[f] = r
json.dump(res, open(a[1], "w"), ensure_ascii=False)
print("QA_SCENE_DONE", len(res))
'''


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def worst(*verdicts):
    v = [x for x in verdicts if x in RANK]
    return max(v, key=RANK.get) if v else "pass"


def issue(level, code, msg, stage):
    return {"level": level, "code": code, "msg": msg, "stage": stage}


def verdict_of(issues):
    lv = {i["level"] for i in issues}
    return "fail" if "ERROR" in lv else ("review" if "WARN" in lv else "pass")


def exit_code(res, strict=False):
    """Код выхода по результату стадии: замер выполнен — 0, вердикт и находки остаются в JSON (вердикт страницы решает
    site/page_gates.py); стадия не дала результата (поле error) — 2; с --strict — по вердикту: fail — 1, review — 3."""
    if res.get("error") or res.get("verdict") not in STRICT_CODE:
        return 2
    return STRICT_CODE[res["verdict"]] if strict else 0


def usage_error(msg):
    print(f"qa_pipeline.py: {msg} (справка: --help)", file=sys.stderr)
    sys.exit(2)


# ------------------------------------------------------------------------------------------------ scene
def run_scene(files, passports, timeout=600):
    files = [os.path.abspath(f) for f in files]
    tmp = tempfile.mkdtemp(prefix="qa_scene_")
    cfg = {"files": files, "passports": {}, "scene_check": os.path.join(TOOLS, "scene_check.py"),
           "preflight": os.path.join(E26, "preflight_block.py")}
    for f in files:
        key = os.path.splitext(os.path.basename(f))[0]
        if key in passports:
            cfg["passports"][f] = passports[key]
        elif "*" in passports:
            cfg["passports"][f] = passports["*"]
    cp, outp, runner = (os.path.join(tmp, n) for n in ("cfg.json", "out.json", "runner.py"))
    json.dump(cfg, open(cp, "w"))
    open(runner, "w").write(RUNNER)
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "blender_run.py"), runner, "--timeout", str(timeout), "--",
                        cp, outp], capture_output=True, text=True)
    if not os.path.exists(outp):
        return {"verdict": "fail", "error": (r.stdout[-2000:] + r.stderr[-1000:]), "tmp": tmp}
    raw = json.load(open(outp))
    out = {}
    for f, r in raw.items():
        iss = []
        sc = r.get("scene_check") or {}
        for i in sc.get("issues", []):
            iss.append(issue(i["level"], i["code"], f'{i["obj"]}: {i["msg"]} [{i["m"]}]', "scene_check"))
        asset = set((sc.get("metrics") or {}).get("objects", {}).keys())
        for lvl, code, ob, msg in r.get("preflight", []):
            if asset and ob not in asset and ob != "scene" and not ob.startswith("action:"):
                lvl, msg = "INFO", msg + " (вне ассета)"
            iss.append(issue(lvl, "PF_" + code, f"{ob}: {msg}", "preflight"))
        for k in ("open_error", "scene_check_error", "preflight_error"):
            if k in r:
                iss.append(issue("ERROR", k, r[k][-400:], "runner"))
        out[os.path.basename(f)] = {"verdict": verdict_of(iss), "scene_verdict": sc.get("verdict"),
                                    "codes": sorted({i["code"] for i in iss if i["level"] != "INFO"}),
                                    "issues": iss, "metrics": sc.get("metrics", {})}
    return {"verdict": worst(*[v["verdict"] for v in out.values()]), "files": out, "tmp": tmp}


# ------------------------------------------------------------------------------------------------ glb
ASSET_ONLY = r'''
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
keep = set()
for c in bpy.data.collections:
    if c.name.startswith("ASSET_"):
        keep |= {o.name for o in c.all_objects}
n = 0
if keep:
    for o in list(bpy.data.objects):
        if o.type in ("MESH", "CURVE", "FONT", "SURFACE", "META") and o.name not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
bpy.ops.wm.save_as_mainfile(filepath=a[1], copy=True)
print("ASSET_ONLY removed", n, "kept", len(keep))
'''


def asset_only_blend(blend, tmp):
    """Копия .blend без подложки (циклорама, пол, фон вне ASSET_*): gltf_diff рендерит ВСЮ видимую геометрию источника,
    а в GLB — только ассет; без копии сравнение ложно «сломано» (kb/3d 11-evaluation-qa/03 §2.2)."""
    runner, out = os.path.join(tmp, "asset_only.py"), os.path.join(tmp, "asset_only.blend")
    open(runner, "w").write(ASSET_ONLY)
    subprocess.run([sys.executable, os.path.join(TOOLS, "blender_run.py"), runner, "--", os.path.abspath(blend), out],
                   capture_output=True, text=True, timeout=300)
    return out if os.path.exists(out) else os.path.abspath(blend)


GLB_SANITIZE = re.compile(r"[\[\].:/]")           # символы, которые three удаляет из имени узла (NAME_COLLISION)


def glb_three_name(name):
    """Как PropertyBinding.sanitizeNodeName three r186 (02-blender-workflow/01 §8.2): пробел → '_', удалить [ ] . : /"""
    return GLB_SANITIZE.sub("", re.sub(r"\s", "_", name))


def glb_json(path):
    """JSON-чанк .glb без парсера/трёх.js: 12 байт заголовка + 4 байта длины 1-го чанка + 4 байта типа → JSON."""
    data = open(path, "rb").read()
    n = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20 + n])


def glb_name_collisions(glb):
    """Узлы .glb, чьи имена после санитизации three (02-blender-workflow/01 §8.2) совпадают — ERROR, критично для интерактива
    (getObjectByName найдёт не тот узел). Возвращает [(имя1, имя2, санитизированное), …]."""
    seen, dups = {}, []
    for node in glb_json(glb).get("nodes", []):
        name = node.get("name")
        if not name:
            continue
        t = glb_three_name(name)
        if t in seen:
            dups.append((seen[t], name, t))
        else:
            seen[t] = name
    return dups


def run_glb(glb, a):
    glb = os.path.abspath(glb)
    tmp = tempfile.mkdtemp(prefix="qa_glb_")
    iss, rep = [], {"file_kb": round(os.path.getsize(glb) / 1024, 1)}
    # 0. коллизии имён узлов после санитизации three (02-blender-workflow/01 §8.2) — критично для интерактива
    dups = glb_name_collisions(glb)
    if dups:
        rep["name_collisions"] = dups
        for a_name, b_name, t in dups:
            iss.append(issue("ERROR", "NAME_COLLISION", f"{a_name!r} и {b_name!r} → оба {t!r} (getObjectByName найдёт не тот)", "names"))
    # 1. валидатор Khronos + inspect
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "gltf_check.py"), glb, "--json"], capture_output=True, text=True, timeout=300)
    try:
        chk = json.loads(r.stdout[r.stdout.index("{"):])
        rep["validator"] = chk.get("issues")
        rep["hints"] = chk.get("hints", [])
        if chk["issues"].get("numErrors"):
            iss.append(issue("ERROR", "validator_errors", f'{chk["issues"]["numErrors"]} ошибок валидатора', "gltf_check"))
        if chk["issues"].get("numWarnings"):
            iss.append(issue("WARN", "validator_warnings", f'{chk["issues"]["numWarnings"]} предупреждений', "gltf_check"))
        for h in chk.get("hints", []):
            iss.append(issue("WARN" if "сжат" in h or "> 5 МБ" in h else "INFO", "hint", h, "gltf_check"))
    except (ValueError, KeyError):
        iss.append(issue("ERROR", "gltf_check_failed", (r.stdout + r.stderr)[-400:], "gltf_check"))
    # 2. glb_lint (08-export-gltf/04 §6)
    sys.path.insert(0, E26)
    from glb_lint_block import glb_lint
    lint = glb_lint(glb)
    rep["glb_lint"] = lint
    for w in lint.get("warnings", []):
        iss.append(issue("WARN", "glb_lint", w, "glb_lint"))
    # бюджет из паспорта / таблицы 09/05 §1.1 (hero: телефон 50 тыс. треуг. и 820 КБ, десктоп 100 тыс. и 1536 КБ)
    if opt(a, "--max-tris") and (lint.get("triangles") or 0) > int(opt(a, "--max-tris")):
        iss.append(issue("ERROR", "over_budget_tris", f'{lint.get("triangles")} > {opt(a, "--max-tris")} треугольников', "budget"))
    if opt(a, "--max-kb") and rep["file_kb"] > float(opt(a, "--max-kb")):
        iss.append(issue("ERROR", "over_budget_kb", f'{rep["file_kb"]} > {opt(a, "--max-kb")} КБ', "budget"))
    # 3. что создал three r186
    wi = os.path.join(tmp, "three.json")
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "gltf_web_inspect.py"), glb, "--out", wi], capture_output=True,
                       text=True, timeout=300)
    if os.path.exists(wi):
        w = json.load(open(wi))
        errs = [c for c in w.get("console", []) if c.startswith("error") or c.startswith("pageerror")]
        rep["three"] = {k: w.get(k) for k in ("draw_calls", "calls", "triangles", "render", "clips") if k in w}
        rep["three_console"] = w.get("console", [])[:10]
        if errs:
            iss.append(issue("ERROR", "three_console_errors", "; ".join(errs[:3]), "gltf_web_inspect"))
        if any("Multiple instances of Three.js" in c for c in w.get("console", [])):
            iss.append(issue("WARN", "three_multiple_instances", "две копии three", "gltf_web_inspect"))
    else:
        iss.append(issue("ERROR", "web_inspect_failed", (r.stdout + r.stderr)[-400:], "gltf_web_inspect"))
    # 4. Blender против three (по запросу)
    if "--diff" in a and opt(a, "--blend"):
        dd = os.path.join(tmp, "diff")
        src = asset_only_blend(opt(a, "--blend"), tmp)
        cmd = [sys.executable, os.path.join(TOOLS, "gltf_diff.py"), src, dd, "--glb", glb]
        for k in ("--tone", "--engine", "--views", "--hdri"):
            if opt(a, k):
                cmd += [k, opt(a, k)]
        subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        mp = os.path.join(dd, "diff_metrics.json")
        if os.path.exists(mp):
            m = json.load(open(mp))["mean"]
            rep["diff"] = dict(m, sheet=os.path.join(dd, "diff_sheet.png"))
            de, iou = m["de2000_mean"], m["iou"]
            if de > 6 or iou < 0.95:
                iss.append(issue("ERROR", "diff_broken", f"ΔE {de}, IoU {iou} (поломка: ΔE > 6 или IoU < 0,95, 11/03 §2.2)", "gltf_diff"))
            elif de > 3.5 or iou < 0.99:
                iss.append(issue("WARN", "diff_drift", f"ΔE {de}, IoU {iou} (норма ΔE ≤ 3,5 и IoU ≥ 0,99)", "gltf_diff"))
        else:
            iss.append(issue("ERROR", "diff_failed", "gltf_diff не дал diff_metrics.json", "gltf_diff"))
    # 5. цена загрузки (по запросу)
    if "--bench" in a:
        bj = os.path.join(tmp, "bench.json")
        subprocess.run([sys.executable, os.path.join(TOOLS, "gltf_load_bench.py"), glb, "--runs", "3", "--json", bj],
                       capture_output=True, text=True, timeout=600)
        if os.path.exists(bj):
            rep["bench"] = json.load(open(bj))
    return {"verdict": verdict_of(iss), "codes": sorted({i["code"] for i in iss if i["level"] != "INFO"}),
            "issues": iss, "report": rep, "tmp": tmp}


# ------------------------------------------------------------------------------------------------ page
def importmap_check(html_path):
    """Статика (09-web-runtime/01 §1.2): import map — одна версия three для ядра и addons, без *.min.js ядра с jsDelivr."""
    iss = []
    src = open(html_path, encoding="utf-8").read()
    m = re.search(r'<script type="importmap">(.*?)</script>', src, re.S)
    if not m:
        return iss
    try:
        imports = json.loads(m.group(1)).get("imports", {})
    except ValueError:
        return [issue("ERROR", "importmap_invalid", "import map не JSON", "static")]
    vers = {re.search(r"three@([\d.]+)", u).group(1) for u in imports.values() if re.search(r"three@([\d.]+)", u)}
    if len(vers) > 1:
        iss.append(issue("ERROR", "importmap_versions", f"разные версии three: {sorted(vers)}", "static"))
    core = imports.get("three", "")
    remap = any(k.endswith("three.core.js") and v.endswith("three.core.min.js") for k, v in imports.items())
    if core.endswith(".min.js") and "jsdelivr" in core and not remap:
        iss.append(issue("WARN", "importmap_min_core", "three.module.min.js с jsDelivr без переназначения three.core.js → "
                         "three.core.min.js тянет неминифицированное ядро 204 КБ br (09/01 §1.2)", "static"))
    return iss


def run_page(target, a):
    tmp = tempfile.mkdtemp(prefix="qa_page_")
    iss, httpd, url = [], None, target
    if os.path.isdir(target) or target.endswith(".html"):
        src_root = target if os.path.isdir(target) else os.path.dirname(os.path.abspath(target))
        page = "index.html" if os.path.isdir(target) else os.path.basename(target)
        if os.path.exists(os.path.join(src_root, page)):
            iss += importmap_check(os.path.join(src_root, page))
        # раздаём из временной копии: serve_br.precompress() пишет file.br рядом со страницей, а страница может
        # лежать в базе (09-web-runtime/examples/…); на проверку копия не влияет
        root = os.path.join(tmp, "site")
        shutil.copytree(os.path.abspath(src_root), root)
        sys.path.insert(0, SERVE_BR)
        from serve_br import start
        httpd = start(root, int(opt(a, "--port", "0")))     # 0 — свободный порт
        url = f"http://127.0.0.1:{httpd.server_address[1]}/{page}"
    mobile, reduced = "--mobile" in a, "--reduced" in a
    cmd = [sys.executable, os.path.join(TOOLS, "site_probe.py"), url, tmp, "--quick"]
    if mobile:
        cmd += ["--mobile", "--throttle", "--wait", opt(a, "--wait", "16000")]
    elif opt(a, "--wait"):
        cmd += ["--wait", opt(a, "--wait")]
    if reduced:
        cmd += ["--reduced-motion"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    finally:
        if httpd:
            httpd.shutdown()
            httpd.server_close()
    suffix = ("_mobile" if mobile else "") + ("_thr" if mobile else "") + ("_rm" if reduced else "") + ("_quick" if not reduced else "")
    pp = os.path.join(tmp, f"probe{suffix}.json")
    if not os.path.exists(pp):
        iss.append(issue("ERROR", "probe_failed", (r.stdout + r.stderr)[-500:], "site_probe"))
        return {"verdict": "fail", "error": "site_probe.py не дал отчёта зонда", "codes": ["probe_failed"], "issues": iss,
                "url": url, "tmp": tmp}
    return page_report(pp, mobile, reduced, iss, url, tmp)


def page_report(pp, mobile, reduced, iss, url, tmp):
    """Результат page по отчёту зонда pp: строки ворот 3D с тяжестью (B — ERROR, S — WARN, D — INFO) к находкам iss."""
    rep = evaluate(pp, "mobile" if mobile else "desktop", reduced)
    for r in rep["rows"]:
        if r["status"] == "FAIL":
            iss.append(issue(GATE_LEVEL.get(r["severity"], "INFO"), "gate:" + r["check"],
                             f"{r['value']} при пороге {r['limit']} ({r['id']}, {r['severity']})", "gate_check"))
    txt = open(pp, encoding="utf-8").read()
    if "Multiple instances of Three.js" in txt:
        iss.append(issue("WARN", "three_multiple_instances", "в консоли «Multiple instances of Three.js»", "site_probe"))
    st = json.loads(txt)
    timing = st.get("page_timing") or st.get("timing") or {}
    return {"verdict": verdict_of(iss), "url": url, "mode": ("mobile" if mobile else "desktop") + ("+reduce" if reduced else ""),
            "gates": [{"id": r["id"], "check": r["check"], "value": r["value"], "limit": r["limit"], "severity": r["severity"],
                       "status": r["status"], "ok": r["status"] != "FAIL", **({"mirror": r["mirror"]} if r.get("mirror") else {})}
                      for r in rep["rows"]],
            "gate_summary": rep["summary"],
            "codes": sorted({i["code"] for i in iss if i["level"] != "INFO"}), "issues": iss, "probe": pp, "timing": timing,
            "tmp": tmp}


def selftest():
    """Без Blender и браузера: вердикт page по тяжести строк ворот 3D на отчётах зонда из словарей, коды выхода с --strict
    и без него, ошибки вызова."""
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)
    base = {"vitals_pre_scroll": {"lcp": {"tag": "IMG", "t": 900}, "cls": 0.02, "tbt_ms": 120, "first_draw_ms": 1500},
            "network": {"transfer_kb": 2900.0, "by_category": {"model3d": {"n": 1, "transfer_kb": 700.0}}},
            "idle": {"dc_median": 12}, "detected": {"canvases": [{"w": 960, "css": [640, 480], "vis": True}]}, "console_errors": 0}
    only_s = json.loads(json.dumps(base))
    only_s["idle"]["dc_median"] = 75
    only_s["vitals_pre_scroll"]["first_draw_ms"] = 2600
    with_b = json.loads(json.dumps(only_s))
    with_b["vitals_pre_scroll"]["lcp"]["tag"] = "CANVAS"
    with tempfile.TemporaryDirectory() as td:
        res = {}
        for name, probe in (("clean", base), ("only_s", only_s), ("with_b", with_b)):
            pp = os.path.join(td, name + ".json")
            with open(pp, "w", encoding="utf-8") as f:
                json.dump(probe, f)
            res[name] = page_report(pp, False, False, [], "selftest", td)
    check("ворота 3D пройдены → pass, код 0 и со --strict",
          res["clean"]["verdict"] == "pass" and exit_code(res["clean"]) == 0 and exit_code(res["clean"], strict=True) == 0)
    s = res["only_s"]
    check("только S (вызовы 75 > 60, первый кадр 2 600 > 2 000) → review, находки WARN; B 0, S 2; код 0, со --strict — 3",
          s["verdict"] == "review" and {i["level"] for i in s["issues"]} == {"WARN"}
          and s["gate_summary"]["B"] == 0 and s["gate_summary"]["S"] == 2
          and exit_code(s) == 0 and exit_code(s, strict=True) == 3)
    b = res["with_b"]
    check("провал B (LCP-элемент canvas) → fail; S остаются в отчёте предупреждениями; код 0, со --strict — 1",
          b["verdict"] == "fail" and sum(i["level"] == "ERROR" for i in b["issues"]) == 1
          and sum(i["level"] == "WARN" for i in b["issues"]) == 2 and b["gate_summary"]["blocked"]
          and exit_code(b) == 0 and exit_code(b, strict=True) == 1)
    lost = {"verdict": "fail", "error": "стадия не дала результата", "issues": []}
    check("стадия не дала результата (поле error) → код 2 и без --strict", exit_code(lost) == 2 and exit_code(lost, strict=True) == 2)
    me = os.path.abspath(__file__)
    rc = {k: subprocess.run([sys.executable, me] + args, capture_output=True, text=True).returncode
          for k, args in (("help", ["--help"]), ("none", []), ("mode", ["render"]), ("glb", ["glb"]), ("scene", ["scene", "--strict"]),
                          ("no_file", ["glb", os.path.join(tempfile.gettempdir(), "qa_pipeline_selftest_none.glb")]))}
    check("вызов: --help — код 0; без режима, чужой режим, режим без входа, нет файла GLB — код 2",
          rc == {"help": 0, "none": 2, "mode": 2, "glb": 2, "scene": 2, "no_file": 2})

    def staged(res, args):
        """main() на подменённой стадии glb → (код выхода, строка JSON из stdout)."""
        import contextlib, io
        saved, argv, buf = globals()["run_glb"], sys.argv, io.StringIO()
        globals()["run_glb"] = lambda glb, a: dict(res)
        try:
            sys.argv = ["qa_pipeline.py", "glb", me] + args          # вход — существующий файл: стадия подменена
            with contextlib.redirect_stdout(buf):
                main()
        except SystemExit as e:
            return e.code, json.loads(buf.getvalue().strip().splitlines()[-1])
        finally:
            globals()["run_glb"], sys.argv = saved, argv
    with tempfile.TemporaryDirectory() as td:
        outp = os.path.join(td, "r.json")
        rv = {"verdict": "review", "codes": ["glb_lint"], "issues": [issue("WARN", "glb_lint", "образец", "glb_lint")], "report": {}, "tmp": ""}
        c0, s0 = staged(rv, ["--out", outp])
        c1, _ = staged(rv, ["--out", outp, "--strict"])
        full = json.load(open(outp, encoding="utf-8"))
        c2, s2 = staged({"verdict": "fail", "error": "стадия не дала результата", "tmp": ""}, ["--strict"])
    check("main() на подменённой стадии: review — код 0, вердикт в stdout и в файле --out; со --strict — 3; стадия без результата — 2 и error",
          (c0, c1, c2) == (0, 3, 2) and s0["verdict"] == "review" and full["verdict"] == "review" and len(full["issues"]) == 1
          and "error" in s2)
    g = {x["id"] + ":" + x["check"]: x for x in s["gates"]}
    check("поле gates — все строки ворот с id, тяжестью и статусом; зеркала D без профиля — SKIP",
          all({"id", "severity", "status", "ok"} <= set(x) for x in s["gates"])
          and any(x.get("mirror") and x["severity"] == "D" and x["status"] == "SKIP" for x in s["gates"])
          and any(x["severity"] == "S" and x["status"] == "FAIL" and not x["ok"] for x in g.values()))
    print("qa_pipeline selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        sys.exit(selftest())
    if a and a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if not a or a[0] not in ("scene", "glb", "page"):
        usage_error("нужен режим: scene, glb или page")
    t0 = time.time()
    mode = a[0]
    if mode != "scene" and (len(a) < 2 or a[1].startswith("--")):
        usage_error(f"{mode}: нужен вход — " + ("файл .glb" if mode == "glb" else "URL, папка или файл .html"))
    if mode == "glb" and not os.path.isfile(a[1]):
        usage_error(f"glb: нет файла {a[1]}")
    if mode == "scene":
        files = [x for x in a[1:] if x.endswith(".blend")]
        if not files:
            usage_error("scene: нужен хотя бы один файл .blend")
        passports = {}
        if opt(a, "--passports"):
            passports = json.load(open(opt(a, "--passports")))
        elif opt(a, "--passport"):
            passports = {"*": json.load(open(opt(a, "--passport")))}
        res = run_scene(files, passports)
    elif mode == "glb":
        res = run_glb(a[1], a)
    else:
        res = run_page(a[1], a)
    res["sec"] = round(time.time() - t0, 1)
    if "--keep" not in a:                      # временные папки (кадры diff, отчёты зонда) — удалить; --keep оставляет
        d = res.get("tmp", "")
        if d and os.path.isdir(d) and os.path.basename(d).startswith("qa_"):
            shutil.rmtree(d, ignore_errors=True)
        if isinstance(res.get("probe"), str) and "--out" in a:
            res["probe_note"] = "папка зонда удалена; --keep, чтобы оставить"
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if opt(a, "--out"):
        open(opt(a, "--out"), "w").write(txt)
    short = {k: res[k] for k in ("verdict", "codes", "sec") if k in res}
    if mode == "scene":
        short["files"] = {k: [v["verdict"], v["codes"]] for k, v in res.get("files", {}).items()}
    if res.get("error"):
        short["error"] = res["error"][-400:]
    print(json.dumps(short, ensure_ascii=False))
    sys.exit(exit_code(res, "--strict" in a))


if __name__ == "__main__":
    main()
