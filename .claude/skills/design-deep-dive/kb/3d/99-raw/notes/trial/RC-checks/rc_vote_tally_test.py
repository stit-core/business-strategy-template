#!/usr/bin/env python3
"""Самопроверка rc_vote_tally.py: (1) пробные голоса заказчика vote/votes-test на пробных парах vote/pairs.json (как сейчас на диске,
3 пары) — сверка с тем, что показала бы страница; (2) синтетика: гибрид против кода и якорь — проверка правил доли и L2."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R = "/home/mm/Документы/app-design/blender-research"
V = f"{R}/15-showcase/vote"
T = os.path.join(HERE, "rc_vote_tally.py")

# (1) пробные голоса: pairs.json на диске на 26.09 00:30 — 3 пробные пары (build_pairs.py ещё не перезаписал его)
pj = f"{V}/pairs-test.json" if os.path.exists(f"{V}/pairs-test.json") else f"{V}/pairs.json"
ids = [p["id"] for p in json.load(open(pj))["pairs"]]
if ids == ["test-sculpt", "test-case-island", "test-case-sculpt"]:
    tmp = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, T, pj, f"{V}/votes-test", "--json", f"{tmp}/o.json"], capture_output=True, text=True)
    print(r.stdout.strip())
    o = json.load(open(f"{tmp}/o.json"))
    got = {p["id"]: p["per_voter"][0] for p in o["pairs"]}
    # страница (verdicts()): sculpt — :0 left/flip0 → A, :1 right/flip1 → A ⇒ A; case-island — оба «оба слабо» ⇒ x;
    # case-sculpt — :0 right/flip0 → B, :1 left/flip1 → B ⇒ B
    assert got == {"test-sculpt": "A", "test-case-island": "x", "test-case-sculpt": "B"}, got
else:
    print("pairs.json уже боевой — часть (1) пропущена")

# (2) синтетика
pairs = {"pairs": [
    {"id": "z-hero-ac", "q": "craft", "a": {"v": "A код"}, "b": {"v": "C гибрид"}},
    {"id": "k-first-ac", "q": "page", "a": {"v": "A код"}, "b": {"v": "C гибрид"}},
    {"id": "z-exploded-ac", "q": "craft", "a": {"v": "A код"}, "b": {"v": "C гибрид"}},
    {"id": "z-anchor", "q": "page", "a": {"v": "наш лучший"}, "b": {"v": "якорь hubtown"}},
]}
ans = lambda pid, c0, c1: {pid + ":0": {"pair": pid, "flip": False, "c": c0}, pid + ":1": {"pair": pid, "flip": True, "c": c1}}
doc = {"v": 1, "voter": "synt", "answers": {}}
doc["answers"].update(ans("z-hero-ac", "right", "left"))       # C оба раза → победа C
doc["answers"].update(ans("k-first-ac", "right", "right"))     # C, потом A → ничья
doc["answers"].update(ans("z-exploded-ac", "left", "right"))   # A оба раза → победа A (кода)
doc["answers"].update(ans("z-anchor", "left", "right"))        # наш оба раза → победа над якорем
d = tempfile.mkdtemp()
json.dump(pairs, open(f"{d}/pairs.json", "w"), ensure_ascii=False)
os.makedirs(f"{d}/votes")
json.dump(doc, open(f"{d}/votes/synt.json", "w"), ensure_ascii=False)
r = subprocess.run([sys.executable, T, f"{d}/pairs.json", f"{d}/votes", "--json", f"{d}/o.json"], capture_output=True, text=True)
print(r.stdout.strip())
o = json.load(open(f"{d}/o.json"))
h = o["hybrid_vs_code"]
assert (h["wins"], h["ties"], h["n"], h["score"], h["decision"]) == (1, 1, 3, 0.5, "по бюджету"), h
assert o["anchors"]["z"]["L2"].startswith("не посчитать"), o["anchors"]
print("RC_CHECK_OK")
