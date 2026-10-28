#!/usr/bin/env python3
"""fill_readme.py — таблицы «Числа фазы 2» в 15-showcase/keyboard/README.md из numbers.json (phase2)."""
import json
import os

K = os.path.dirname(os.path.abspath(__file__))
S = os.path.normpath(os.path.join(K, "../../../15-showcase/keyboard"))
N = json.load(open(f"{S}/numbers.json"))["phase2"]
f = lambda v, d=1: "—" if v is None else (f"{v:.{d}f}".replace(".", ",") if isinstance(v, (int, float)) else str(v))  # noqa: E731


def frame_row(name, m, mf):
    m = m or {}
    mf = mf or {}
    return (f"| {name} | {f(mf.get('top_L_median'))} / {f(mf.get('top_L_min'))} | {f(m.get('clip_obj_pct'), 2)} | "
            f"{f(m.get('hi_obj_pct'), 2)} | {f(m.get('obj_minus_bg_L'))} | {f(m.get('noise_bg_e3'), 2)} | {f(m.get('obj_share'), 2)} |")


out = ["### Постер первого экрана (камера H2v2; метрики `kbm.py` + `kbtop.py`, маска одна — паспорт общий)", "",
       "| Кадр | Верх белых колпачков L* (мед./мин.) | Пересвет, % | Блик ≥ 97, % | Объект−фон, L* | Шум фона ×10⁻³ | Доля объекта |",
       "|---|---|---|---|---|---|---|"]
B, A = N["B_blender"], N["A_code"]
out.append(frame_row("B hero2 десктоп v1 (полосы E 2,2/1,6)", B.get("hero2_v1_metrics", {}).get("desk"), None))
for t, nm in (("desk", "десктоп"), ("mob", "портрет")):
    out.append(frame_row(f"B hero2 {nm} (Cycles 128 спп)", B["hero2"][t]["metrics"], B["hero2"][t]["main_face"]))
    out.append(frame_row(f"A hero2 {nm} (three, кадр своей страницы)", A["hero2"][t]["metrics"], A["hero2"][t]["main_face"]))
sc = N.get("same_camera", {}).get("after") or {}
out += ["", "### A/B/C в одной камере (после поправки экспозиции three по сценам)", "",
        "| Сцена | B: верх колпачков L* | A | C | A−B ΔL* объекта (сред. / мед. \\|·\\|) | C−B |", "|---|---|---|---|---|---|",
        f"| набор T (тёмный фон) | {f(sc.get('type_B', [None])[0])} | {f(sc.get('type_A', [None])[0])} | {f(sc.get('type_C', [None])[0])} | — | — |",
        f"| оборот R «Снег» | {f(sc.get('turn_B', [None])[0])} | {f(sc.get('turn_A', [None])[0])} | {f(sc.get('turn_C', [None])[0])} | "
        f"{' / '.join(f(x) for x in sc.get('turn_dL_A-B', []))} | {' / '.join(f(x) for x in sc.get('turn_dL_C-B', []))} |",
        f"| разборка X, станция 4 | — | — | — | {' / '.join(f(x) for x in sc.get('x3_dL_A-B', []))} | {' / '.join(f(x) for x in sc.get('x3_dL_C-B', []))} |"]


def js_sum(js, skip=()):
    return sum(v["kb_br"] for v in js.values() if v["role"] not in skip)


C = N["C_hybrid"]
glb = C["glb"]
out += ["", "### Вес и JS (brotli q11)", "",
        "| | A — код | B — Blender | C — гибрид |", "|---|---|---|---|",
        f"| JS страницы (до 3D), КБ br | {f(js_sum(A['js'], ('three', 'n8ao+post', 'loaders', 'model', 'stage3d', 'other')))} | "
        f"{f(js_sum(B['js']))} | {f(js_sum(C['js'], ('three', 'n8ao+post', 'loaders', 'model', 'stage3d', 'other')))} |",
        f"| JS всего с 3D (страница + three + модель + сцена; десктоп + N8AO), телефон / десктоп, КБ br | {f(js_sum(A['js'], ('n8ao+post',)))} / {f(js_sum(A['js']))} | 0 / 0 | "
        f"{f(js_sum(C['js'], ('n8ao+post',)))} / {f(js_sum(C['js']))} |",
        f"| 3D-ассеты | 0 (модель — код) | 0 | GLB десктоп {f(glb['kb_desk.glb']['kb'])} КБ ({f(glb['kb_desk.glb']['kb_br'])} br, WebP 2048; "
        f"KTX2 ETC1S был {f(glb['kb_desk_ktx2.glb']['kb_br'])} br + транскодер 212 br), "
        f"телефон {f(glb['kb_mob.glb']['kb'])} КБ ({f(glb['kb_mob.glb']['kb_br'])} br, WebP 512) + тень 4 КБ |",
        f"| Кадры в папке (все), КБ | {f(sum(v for k, v in A['page_assets_kb'].items() if k.startswith('img')))} | "
        f"{f(sum(v for k, v in B['page_assets_kb'].items() if k.startswith('img')))} | "
        f"{f(sum(v for k, v in C['page_assets_kb'].items() if k.startswith('img')))} |"]
g = N.get("gates", {})
out += ["", "### Ворота (KIT §6; «тишина» — render.lock + browser.lock)", "",
        "| Ворота | A | B | C |", "|---|---|---|---|"]
for k, nm in (("desktop", "gate_check десктоп"), ("mobile", "gate_check Pixel 7 (×4 CPU, 1,6 Мбит/с)"), ("reduce", "gate_check reduce")):
    row = []
    for v in ("a", "b", "c"):
        x = (g.get(v) or {}).get(k)
        row.append("—" if not x else (f"{x['pass']} OK" + (f", FAIL: {'; '.join(x['fail'])}" if x["fail"] else "")))
    out.append(f"| {nm} | " + " | ".join(row) + " |")
for k, nm in (("motion", "motion_check L1 (FAIL B / S)"), ("marketing", "marketing_audit L1")):
    row = []
    for v in ("a", "b", "c"):
        x = (g.get(v) or {}).get(k)
        row.append("—" if not x else json.dumps(x, ensure_ascii=False)[:160].replace("|", "/"))
    out.append(f"| {nm} | " + " | ".join(row) + " |")
q, q3 = N["queue"], N.get("queue_KB3") or {}
at = N["agent_time"]
out += ["", f"Время: агент KB {at['KB']['minutes']} мин + KB2 {at['KB2']['start']}–{at['KB2']['end']} ({at['KB2'].get('minutes', '—')} мин) + "
        f"KB3 {at['KB3']['start']}–{at['KB3']['end']} (26.09); машина фазы 2 (журнал очереди, KB2 + KB3) — {q['machine_total_s']:.0f} с "
        f"({', '.join(f'{k} {v:.0f} с' for k, v in q['machine_s'].items())}), ожидание очереди {q['queue_wait_s']} с, запусков {q['runs']}; "
        f"из них KB3 — {q3.get('machine_total_s', 0):.0f} с машины, ожидание {q3.get('queue_wait_s', 0)} с, запусков {q3.get('runs', 0)}."]
p = f"{S}/README.md"
s = open(p).read()
a, b = s.index("<!-- NUMBERS2 -->"), s.index("## Числа фазы 1")
s = s[:a] + "<!-- NUMBERS2 -->\n" + "\n".join(out) + "\n\n" + s[b:]
open(p, "w").write(s)
print("\n".join(out[-12:]))
