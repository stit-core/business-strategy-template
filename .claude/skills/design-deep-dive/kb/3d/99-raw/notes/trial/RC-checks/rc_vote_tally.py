#!/usr/bin/env python3
"""rc_vote_tally.py — итоги слепого голосования «Кадр против кадра» (15-showcase/vote) по протоколу 11-evaluation-qa/06.

    python3 rc_vote_tally.py PAIRS.json VOTES [--json out.json]
      PAIRS.json — pairs.json страницы (build_pairs.py); VOTES — папка votes/ (vote_server.py), файл /api/all (dict голосующих)
      или файл «Скопировать результаты (JSON)» со страницы ({doc, verdicts}).

Правила (как verdicts() страницы + протокол 06):
  • пара у голосующего засчитывается, только если оба порядка согласны; расхождение → «ничья»; оба раза «оба слабо» → «оба слабо»;
  • счёт стороны = (победы + 0,5 × ничьи) / (решённые пары без «оба слабо»); рядом — строгая доля побед и интервал Уилсона 95 %;
  • гибрид против кода — пары, где подписи вариантов начинаются с «A » и «C »: доля C ≥ 0,75 → «Blender обязателен»,
    0,4–0,75 → «по бюджету», < 0,4 → «не нужен» (digests/04 F, KIT §0);
  • якоря — пары, где одна подпись содержит «якорь»: правило L2 = победа или ничья в ≥ 2 из 3 вопросов (craft, page≈concept,
    motion); вопросов с якорем меньше трёх — «не посчитать».
Только чтение; ничего не пишет, кроме --json.
"""
import glob
import json
import math
import os
import sys
from collections import defaultdict


def load_votes(src):
    docs = {}
    paths = sorted(glob.glob(os.path.join(src, "*.json"))) if os.path.isdir(src) else [src]
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        if "answers" in d:
            docs[d.get("voter") or os.path.basename(p)] = d
        elif "doc" in d:
            docs[d["doc"].get("voter") or os.path.basename(p)] = d["doc"]
        else:                                    # /api/all: {voter: doc}
            docs.update({k: v for k, v in d.items() if isinstance(v, dict) and "answers" in v})
    return docs


def pref(ans):
    if not ans:
        return None
    if ans["c"] == "equal":
        return "="
    if ans["c"] == "both_bad":
        return "x"
    left_is_a = not ans["flip"]
    return "A" if (ans["c"] == "left") == left_is_a else "B"


def verdict(doc, pid):
    x, y = pref(doc["answers"].get(pid + ":0")), pref(doc["answers"].get(pid + ":1"))
    if x is None or y is None:
        return "—"
    if x == "x" and y == "x":
        return "x"
    if x == y and x in ("A", "B"):
        return x
    return "="


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def side_score(results, side):
    """results: список 'A'/'B'/'='/'x'; side — 'A' или 'B'. → (счёт с полуничьими, строгая доля, n, Уилсон строгой доли)."""
    dec = [r for r in results if r in ("A", "B", "=")]
    n = len(dec)
    if not n:
        return None
    w = sum(r == side for r in dec)
    t = sum(r == "=" for r in dec)
    return {"score": round((w + 0.5 * t) / n, 3), "wins": w, "ties": t, "n": n, "win_share": round(w / n, 3),
            "wilson95": wilson(w, n), "both_bad": sum(r == "x" for r in results)}


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    pairs = json.load(open(a[0], encoding="utf-8"))["pairs"]
    docs = load_votes(a[1])
    out = {"voters": sorted(docs), "pairs": [], "hybrid_vs_code": None, "anchors": {}}
    hv = []
    anchor_q = defaultdict(list)
    for p in pairs:
        res = [verdict(d, p["id"]) for d in docs.values()]
        la, lb = p["a"].get("v", "A"), p["b"].get("v", "B")
        row = {"id": p["id"], "q": p.get("q"), "a": la, "b": lb, "per_voter": res, "a_side": side_score(res, "A")}
        out["pairs"].append(row)
        ta, tb = la.split(" ")[0], lb.split(" ")[0]
        if {ta, tb} == {"A", "C"} and not p["id"].startswith("s-"):          # «Сдано»: A — SVG, не код 3D
            hv += [("A" if ta == "C" else "B") if r == "A" else ("A" if tb == "C" else "B") if r == "B" else r
                   for r in res]                                             # 'A' здесь = победа гибрида C
        if "якорь" in la or "якорь" in lb:
            ours = "B" if "якорь" in la else "A"
            anchor_q[p["id"].split("-")[0]].append((p.get("q"), [("win" if r == ours else "tie" if r == "=" else
                                                                   "loss" if r in ("A", "B") else r) for r in res]))
        print(f"{p['id']:16s} {p.get('q', ''):6s} {la} ↔ {lb}: {' '.join(res)}")
    if hv:
        s = side_score(hv, "A")
        dec = ("Blender обязателен" if s["score"] >= 0.75 else "по бюджету" if s["score"] >= 0.4 else "не нужен") if s else "—"
        out["hybrid_vs_code"] = {**(s or {}), "decision": dec}
        print("гибрид против кода:", json.dumps(out["hybrid_vs_code"], ensure_ascii=False))
    for subj, items in anchor_q.items():
        qs = {q for q, _ in items}
        ok = [q for q, rs in items if rs and all(r in ("win", "tie") for r in rs)]
        verdict_l2 = ("не посчитать: вопросов против якоря %d из 3" % len(qs)) if len(qs) < 3 else (
            "L2 пройдено" if len(set(ok)) >= 2 else "L2 не пройдено")
        out["anchors"][subj] = {"items": items, "L2": verdict_l2}
        print("якорь", subj, json.dumps(out["anchors"][subj], ensure_ascii=False))
    if "--json" in a:
        json.dump(out, open(a[a.index("--json") + 1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
