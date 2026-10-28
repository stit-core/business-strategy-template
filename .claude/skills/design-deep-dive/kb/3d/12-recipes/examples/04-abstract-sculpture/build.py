# Сгенерировано run_recipes.py из 12-recipes/04-abstract-sculpture.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 36
# Blender 5.2.2 — [проверено] рецепт 04: лента по узлу (3d 05/04 §5), два варианта паспорта
import sys, math, bpy
from mathutils import Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "04-abstract-sculpture"
BASE = dict(plinth_r=0.085, plinth_h=0.028, knot=(2, 3), knot_R=0.075, knot_r=0.034, ribbon_w=0.034, ribbon_t=0.0075,
            twist_turns=3, spin_deg=18, orb_r=0.013, embed=0.004, ribbon="#EDE7E1", plinth="#8C8680", orb="gold",
            bg="#E9E6E1", cam=dict(az=30, el=12, lens=85, margin=1.15, res=(1280, 720)))
VARIANTS = {"pearl_23": {}, "ink_34": dict(knot=(3, 4), knot_R=0.07, knot_r=0.03, ribbon_w=0.026, twist_turns=5,
                                           ribbon="#1F2A44", plinth="#D9D4CC", orb="copper", bg="#F1EEE9")}


def build(P):
    C = D.fresh_collection("ASSET_sculpture")                    # тот же слот коллекции для всех вариантов — идемпотентно
    stone = rk.web_material("Sc_Stone", "plastic_matte", P["plinth"], roughness=0.7)
    ribbon_m = rk.web_material("Sc_Ribbon", "ceramic_glaze", P["ribbon"])
    orb_m = rk.web_material("Sc_Orb", "metal_polished", P["orb"], roughness=0.22)
    prof = D.fillet_polyline([(0.0, 0.0), (P["plinth_r"], 0.0), (P["plinth_r"], P["plinth_h"]), (0.0, P["plinth_h"])],
                             [0, 0.002, 0.004, 0], 4)
    plinth = D.lathe("Sc_Plinth", prof, C, segments=96, smooth_angle=40)
    bpyx.assign_material(plinth, stone)
    path = D.torus_knot_pts(*P["knot"], P["knot_R"], P["knot_r"], 420)
    sec = D.rrect_pts(P["ribbon_w"], P["ribbon_t"], P["ribbon_t"] / 2 * 0.95, 6)       # «капсула» — без острых кромок
    ribbon = D.sweep("Sc_Ribbon", path, sec, C, closed=True, twist=2 * math.pi * P["twist_turns"], smooth_angle=60)
    ribbon.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))                    # узел встаёт вертикально
    ribbon.data.transform(Matrix.Rotation(math.radians(P["spin_deg"]), 4, "Z"))
    zmin = min(v.co.z for v in ribbon.data.vertices)
    ribbon.location.z = P["plinth_h"] - zmin - P["embed"]                               # врастает в цоколь
    bpyx.assign_material(ribbon, ribbon_m)
    orb = bpyx.primitive("uvsphere", "Sc_Orb", radius=P["orb_r"], segments=32, rings=16, collection=C)
    orb.location = (P["plinth_r"] * 0.55, -P["plinth_r"] * 0.45, P["plinth_h"] + P["orb_r"] * 0.92)
    bpyx.assign_material(orb, orb_m)
    return C, [plinth, ribbon, orb]


for i, (name, over) in enumerate(VARIANTS.items()):
    P = dict(BASE, **over)
    rk.reset(keep_numbers=i > 0)
    C, parts = build(P)
    mn, mx = bpyx.world_bbox(parts)
    assert 0.20 <= mx.z - mn.z <= 0.32, f"высота статуэтки {mx.z - mn.z:.3f} м вне 0,20–0,32"   # масштаб (M2.1)
    rk.asserts("ASSET_sculpture", tuple(mx - mn), touch=[("Sc_Ribbon", "Sc_Plinth"), ("Sc_Orb", "Sc_Plinth")],
               max_tris=40000)                                    # габарит — из bbox; смысл — касания и бюджет
    rk.studio(parts, bg=P["bg"], E_key=2.5, az=P["cam"]["az"])
    rk.camera(parts, **P["cam"])
    rk.neutral(samples=48)
    rk.audit()
    rk.render(SLUG, f"hero_{name}", res=P["cam"]["res"], samples=48)
    rk.ship(SLUG, "ASSET_sculpture", f"sculpture_{name}", preset="static_hero", optimize="meshopt")
rk.save(SLUG, variants=list(VARIANTS))
