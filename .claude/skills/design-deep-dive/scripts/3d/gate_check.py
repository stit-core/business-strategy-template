#!/usr/bin/env python3
"""gate_check.py — ворота страницы с 3D по отчёту зонда site_probe.py (probe*.json).

Пороги и серьёзность — kb/3d/09-web-runtime/page-3d-gates.yaml (одно место чисел ворот 3D; описание — 09/05 §7.2).
Ворота 3D владеют долей и поведением 3D: LCP-элемент не canvas (B), 3D-ассеты (B), вызовы отрисовки и DPR холста (S), первый
кадр 3D (S), ошибки консоли (B), reduce — 0 вызовов и движение в покое (B), вклад 3D в TBT (S) — разность TBT страницы с
прогоном «постер без 3D» (site_probe.py --no-3d, ключ --baseline). Метрики страницы целиком — LCP, CLS, TBT и вес — в отчёте
зеркалом (D) строки-владельца page-gates.yaml: с --profile <page_type>@L<n> — против порога профиля страницы (page_gates.py),
без профиля — только значение. Вердикт страницы ставит page_gates.py (--gate3d FILE): провал ворот 3D там — SG-WEIGHT-08 (D).

  gate_check.py probe_quick.json [mobile|desktop] [--reduced] [--baseline probe_no3d.json] [--profile landing-product@L1]
      [--gates FILE] [--json] [--strict]
  gate_check.py --selftest
  from gate_check import gate_check, evaluate
  rows = gate_check("probe_quick.json", mode="desktop", reduced=False)   # [(проверка, значение, порог, прошла ли)] — ворота 3D
  rep = evaluate("probe_quick.json", "desktop", baseline="probe_no3d.json", profile="landing-product@L1")   # полный отчёт

Код выхода: 0 — замер выполнен (находки — в отчёте: строки со status FAIL и итог summary; обёртка читает отчёт ключа --json,
вердикт страницы решает page_gates.py), 2 — ошибка вызова. С --strict — выход по находкам: 1 — провалена строка B ворот 3D
(summary.blocked). Провал S (вызовы, DPR, первый кадр, вклад в TBT) и зеркала D код не меняют и со --strict: они в отчёте —
S исправить или записать исключением плана.
Код репозитория запускает утилиту соседним чекаутом: ../strategy/.claude/skills/design-deep-dive/scripts/3d/gate_check.py.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

GATES = str(kbpaths.kb("3d", "09-web-runtime", "page-3d-gates.yaml"))
MODES = ("mobile", "desktop")


def load_gates(path=None):
    import yaml
    with open(path or GATES, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load(p):
    if isinstance(p, dict):
        return p
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _dig(d, path):
    cur = d
    for k in path.split("."):
        cur = cur.get(k) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def _limit(g, mode, ktx2=False):
    lim = g.get("limit")
    if ktx2 and isinstance(g.get("limit_ktx2"), dict) and mode in g["limit_ktx2"]:
        return g["limit_ktx2"][mode]
    return lim.get(mode) if isinstance(lim, dict) else lim


def measure(st, key, base=None):
    """Значение проверки по отчёту зонда: key — ключ строки page-3d-gates.yaml."""
    v = st.get("vitals_pre_scroll") or {}
    net = st.get("network") or {}
    cat = net.get("by_category") or {}
    idle = st.get("idle") or {}
    if key == "lcp_not_canvas":
        return (v.get("lcp") or {}).get("tag")
    if key == "kb3d":
        return round(sum((cat.get(k) or {}).get("transfer_kb", 0) for k in ("model3d", "texture3d", "bin")), 1)
    if key in ("dc", "reduce_dc"):
        return idle.get("dc_median")
    if key == "dpr":
        canv = [c for c in (st.get("detected") or {}).get("canvases", []) if c.get("vis") and c.get("css", [0])[0]]
        return round(max((c["w"] / c["css"][0] for c in canv), default=0), 2)
    if key == "canvas_mpx":
        canv = [c for c in (st.get("detected") or {}).get("canvases", []) if c.get("vis") and c.get("w") and c.get("h")]
        return round(max((c["w"] * c["h"] / 1e6 for c in canv), default=0), 2)
    if key == "first_frame":
        return v.get("first_draw_ms")
    if key == "reduce_idle":
        return st.get("idle_motion_pct")
    if key == "console":
        return st.get("console_errors")
    if key == "tbt3d":
        if base is None or v.get("tbt_ms") is None:
            return None
        return max(0, v["tbt_ms"] - ((base.get("vitals_pre_scroll") or {}).get("tbt_ms") or 0))
    raise KeyError(key)


def _profile(profile):
    """Профиль страницы site (page_gates.py) и пороги строк-владельцев page-gates.yaml; нет профиля — (None, None)."""
    if not profile:
        return None, None
    kbpaths.use("site")
    import page_gates as PG
    return PG.resolve_profile(profile), PG


def evaluate(probe, mode="mobile", reduced=False, baseline=None, profile=None, gates=None):
    """Полный отчёт ворот 3D: строки ворот (id, key, check, value, limit, severity, status) и зеркала метрик страницы
    (mirror — id строки-владельца page-gates.yaml, severity D)."""
    st, doc = _load(probe), (gates if isinstance(gates, dict) else load_gates(gates))
    base = _load(baseline) if baseline else None
    cat = (st.get("network") or {}).get("by_category") or {}
    ktx2 = (cat.get("texture3d") or {}).get("n", 0) > 0
    rows = []
    for g in doc.get("gates") or []:
        if bool(g.get("reduced")) != bool(reduced) and g["key"] not in ("lcp_not_canvas", "console"):
            continue
        val = measure(st, g["key"], base)
        lim = _limit(g, mode, ktx2 and g["key"] == "tbt3d")
        if g["key"] == "lcp_not_canvas":
            ok, lim = (val != "CANVAS"), "не CANVAS"
            status = "SKIP" if val is None else ("PASS" if ok else "FAIL")
        elif val is None:
            status = "SKIP"
        elif g["key"] in ("dpr", "canvas_mpx"):
            status = "PASS" if val <= lim + 0.01 else "FAIL"
        else:
            status = "PASS" if val <= lim else "FAIL"
        note = ""
        if g["key"] == "tbt3d" and base is None:
            note = "нужен прогон «постер без 3D»: site_probe.py … --no-3d и ключ --baseline"
        elif g["key"] == "tbt3d" and ktx2 and mode == "desktop":
            note = "десктоп с 3D-текстурами (транскодер KTX2) — limit_ktx2"
        rows.append({"id": g["id"], "key": g["key"], "check": g["check"], "value": val, "limit": lim, "severity": g["severity"],
                     "status": status, "note": note or g.get("note", "")})
    prof, PG = _profile(profile)
    for m in doc.get("mirrors") or []:
        owner = m["owner"][mode] if isinstance(m["owner"], dict) else m["owner"]
        val = _dig(st, m["field"])
        lim = None
        if PG is not None:
            lim = PG.owner_threshold(prof, owner, mode)          # threshold.S строки-владельца page-gates.yaml по профилю
        status = "SKIP" if (val is None or lim is None) else ("PASS" if val <= lim else "FAIL")
        rows.append({"id": owner, "key": m["key"], "check": m["check"], "value": val, "limit": lim,
                     "severity": "D", "status": status, "mirror": owner,
                     "note": "зеркало: вердикт — ворота страницы (page_gates.py)" + ("" if prof else "; без --profile порога нет")})
    owned = [r for r in rows if not r.get("mirror")]
    summary = {k: sum(1 for r in rows if r["status"] == "FAIL" and r["severity"] == k) for k in ("B", "S", "D")}
    summary["blocked"] = any(r["status"] == "FAIL" and r["severity"] == "B" for r in owned)
    return {"tool": "gate_check.py", "probe": probe if isinstance(probe, str) else None, "mode": mode, "reduced": bool(reduced),
            "baseline": baseline if isinstance(baseline, str) else None, "profile": (prof or {}).get("id"),
            "gates": gates if isinstance(gates, str) else GATES, "rows": rows, "summary": summary}


def gate_check(probe_path, mode="mobile", reduced=False, baseline=None):
    """Список (проверка, значение, порог, прошла ли) — строки ворот 3D без зеркал; SKIP считается прошедшей."""
    rep = evaluate(probe_path, mode, reduced, baseline)
    return [(r["check"], r["value"], r["limit"], r["status"] != "FAIL") for r in rep["rows"] if not r.get("mirror")]


def exit_code(rep, strict=False):
    """Код выхода по отчёту evaluate(): замер выполнен — 0, находки остаются в отчёте (вердикт страницы решает page_gates.py);
    с --strict — 1 при проваленной строке B ворот 3D (S и зеркала D — только в отчёте)."""
    return 1 if strict and rep["summary"]["blocked"] else 0


def selftest():
    """Без браузера: отчёты зонда из словарей, пороги из YAML (в том числе правленая копия), зеркала с профилем site."""
    import copy
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)
    doc = load_gates()
    probe = {"vitals_pre_scroll": {"lcp": {"tag": "IMG", "t": 900}, "cls": 0.02, "tbt_ms": 420, "first_draw_ms": 1500},
             "network": {"transfer_kb": 2900.0, "by_category": {"model3d": {"n": 1, "transfer_kb": 700.0}, "texture3d": {"n": 2, "transfer_kb": 300.0}}},
             "idle": {"dc_median": 12}, "detected": {"canvases": [{"w": 960, "h": 720, "css": [640, 480], "vis": True}]}, "console_errors": 0}
    base = {"vitals_pre_scroll": {"tbt_ms": 230}}
    rep = evaluate(probe, "desktop", baseline=base, profile="landing-product@L1")
    by = {r["key"]: r for r in rep["rows"]}
    check("пороги из page-3d-gates.yaml: 3D-ассеты десктопа 1 536, вызовов 60", by["kb3d"]["limit"] == 1536 and by["dc"]["limit"] == 60)
    check("вклад 3D = 420 − 230 = 190 мс; с 3D-текстурами десктоп — предел 200 → PASS", by["tbt3d"]["value"] == 190 and by["tbt3d"]["limit"] == 200
          and by["tbt3d"]["status"] == "PASS")
    check("TBT страницы 420 — зеркало D строки SG-PERF-05 против профиля (L1 десктоп 200) → FAIL D",
          by["tbt"]["mirror"] == "SG-PERF-05" and by["tbt"]["limit"] == 200 and by["tbt"]["status"] == "FAIL" and by["tbt"]["severity"] == "D")
    check("LCP страницы — зеркало SG-PERF-02, вес — зеркало SG-WEIGHT-02; ворота 3D не блокированы",
          by["lcp"]["mirror"] == "SG-PERF-02" and by["transfer"]["mirror"] == "SG-WEIGHT-02" and not rep["summary"]["blocked"])
    check("DPR 1,5 ≤ 2 десктопа; первый кадр 1 500 ≤ 2 000", by["dpr"]["status"] == "PASS" and by["first_frame"]["status"] == "PASS")
    check("пиксели холста 960 × 720 = 0,69 Мпикс ≤ 4,6 десктопа", by["canvas_mpx"]["value"] == 0.69 and by["canvas_mpx"]["status"] == "PASS")
    pm = copy.deepcopy(probe)
    pm["detected"]["canvases"] = [{"w": 780, "h": 1600, "css": [390, 800], "vis": True}]
    rm = {r["key"]: r for r in evaluate(pm, "mobile")["rows"]}
    check("телефон: DPR 2 в пределе, 1,25 Мпикс ≤ 1,9 — PASS; холст 1 170 × 2 400 (2,81 Мпикс) — FAIL S",
          rm["dpr"]["status"] == "PASS" and rm["canvas_mpx"]["status"] == "PASS"
          and {r["key"]: r for r in evaluate(dict(pm, detected={"canvases": [{"w": 1170, "h": 2400, "css": [390, 800], "vis": True}]}),
                                             "mobile")["rows"]}["canvas_mpx"]["status"] == "FAIL")
    p2 = copy.deepcopy(probe)
    p2["vitals_pre_scroll"]["lcp"]["tag"] = "CANVAS"
    p2["network"]["by_category"]["model3d"]["transfer_kb"] = 1500.0
    r2 = {r["key"]: r for r in evaluate(p2, "desktop")["rows"]}
    check("LCP-элемент canvas → B; 3D-ассеты 1 800 > 1 536 → B", r2["lcp_not_canvas"]["status"] == "FAIL" and r2["kb3d"]["status"] == "FAIL"
          and r2["kb3d"]["severity"] == "B")
    check("без прогона без 3D вклад 3D не считается (SKIP с подсказкой)", r2["tbt3d"]["status"] == "SKIP" and "--no-3d" in r2["tbt3d"]["note"])
    check("без --profile зеркало без порога (SKIP)", r2["lcp"]["status"] == "SKIP" and r2["lcp"]["limit"] is None)
    rr = {r["key"]: r for r in evaluate({"idle": {"dc_median": 3}, "idle_motion_pct": 0.2, "console_errors": 0, "vitals_pre_scroll": {"lcp": {"tag": "IMG"}}},
                                        "mobile", reduced=True)["rows"]}
    check("reduce: 3 вызова и 0,2 % в покое → B", rr["reduce_dc"]["status"] == "FAIL" and rr["reduce_idle"]["status"] == "FAIL"
          and "kb3d" not in rr)
    p3 = copy.deepcopy(probe)
    p3["idle"]["dc_median"] = 75
    p3["vitals_pre_scroll"]["first_draw_ms"] = 2600
    rep3 = evaluate(p3, "desktop", baseline=base)
    check("только S (75 вызовов > 60, первый кадр 2 600 > 2 000) → в отчёте S 2, не блокировано, код 0 и со --strict",
          rep3["summary"]["S"] == 2 and rep3["summary"]["B"] == 0 and not rep3["summary"]["blocked"] and exit_code(rep3) == 0
          and exit_code(rep3, strict=True) == 0)
    rep2 = evaluate(p2, "desktop")
    check("провал B (LCP-элемент canvas, 3D-ассеты сверх предела): замер — код 0, находки в отчёте (B 2, blocked); со --strict — код 1",
          exit_code(rep2) == 0 and rep2["summary"]["B"] == 2 and rep2["summary"]["blocked"] and exit_code(rep2, strict=True) == 1)
    legacy = gate_check(probe, "desktop", baseline=base)
    check("gate_check(): кортежи (проверка, значение, порог, прошла ли) — только ворота 3D", legacy and all(len(t) == 4 for t in legacy)
          and not any("страницы" in t[0] for t in legacy))
    with tempfile.TemporaryDirectory() as td:
        d2 = copy.deepcopy(doc)
        next(g for g in d2["gates"] if g["key"] == "kb3d")["limit"]["desktop"] = 900
        import yaml
        pth = os.path.join(td, "gates.yaml")
        with open(pth, "w", encoding="utf-8") as f:
            yaml.safe_dump(d2, f, allow_unicode=True)
        r3 = {r["key"]: r for r in evaluate(probe, "desktop", gates=pth)["rows"]}
        check("порог читается из YAML, а не из кода (правленая копия: 900 → FAIL)", r3["kb3d"]["limit"] == 900 and r3["kb3d"]["status"] == "FAIL")
        import subprocess
        rc, blocked = {}, None
        for name, pr in (("only_s", p3), ("b", p2)):
            pp = os.path.join(td, name + ".json")
            with open(pp, "w", encoding="utf-8") as f:
                json.dump(pr, f)
            for key, extra in ((name, []), (name + "_strict", ["--strict"])):
                r = subprocess.run([sys.executable, os.path.abspath(__file__), pp, "desktop", "--json"] + extra,
                                   capture_output=True, text=True)
                rc[key] = r.returncode
                if key == "b":
                    blocked = json.loads(r.stdout)["summary"]["blocked"]
        check("вызов из командной строки: только S — код 0 и со --strict; провал B — код 0 с blocked в JSON, со --strict — код 1",
              rc == {"only_s": 0, "only_s_strict": 0, "b": 0, "b_strict": 1} and blocked is True)
        check("нет файла отчёта зонда — код 2", subprocess.run([sys.executable, os.path.abspath(__file__), os.path.join(td, "none.json")],
                                                               capture_output=True).returncode == 2)
    src = open(os.path.abspath(__file__), encoding="utf-8").read().split("\ndef selftest")[0]
    check("в коде нет чисел порогов ворот 3D", "LIMITS" not in src and "820" not in src and "1536" not in src and "3072" not in src)
    print("gate_check selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    if a[0] == "--selftest":
        sys.exit(selftest())

    def opt(name):
        return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else None
    mode = a[1] if len(a) > 1 and a[1] in MODES else "mobile"
    try:
        rep = evaluate(a[0], mode, "--reduced" in a, opt("--baseline"), opt("--profile"), opt("--gates"))
    except (OSError, ValueError, KeyError) as e:
        print(f"gate_check.py: {e}", file=sys.stderr)
        sys.exit(2)
    if "--json" in a:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        for r in rep["rows"]:
            print(f"{r['status']:4} {r['severity']} {r['id']:10} {r['check']}: {r['value']} (порог {r['limit']})"
                  + (f" — {r['note']}" if r.get("note") else ""))
        print("итог:", rep["summary"], "— провал B блокирует ворота 3D (код 1 — с --strict); S — исправить или записать исключением плана")
    sys.exit(exit_code(rep, "--strict" in a))


if __name__ == "__main__":
    main()
