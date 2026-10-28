"""build.py — сборка «Ё» (фон Blender 5.2.2): build(P) → проверки → kb_<расцветка>.blend → превью формы.

python3 $R/99-raw/tools/slot_run.py --label KB-build -- python3 $R/99-raw/tools/blender_run.py build.py --timeout 900 -- [snow] [subd]
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbb  # noqa: E402
import kbp  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CW = argv[0] if argv else "snow"
SUBD = int(argv[1]) if len(argv) > 1 else 2
t0 = time.time()
bpyx.clear_scene()
objs = kbb.build(colorway=CW, subd=SUBD)
t_build = time.time() - t0

# ---------------------------------------------------------------- проверки кодом (паспорт в метрах, касания, счёт)
cd = kbp.case_dims()
case = [objs["Case_Top"], objs["Case_Bottom"]]
mn, mx = bpyx.world_bbox(case)
dims = [round(v, 4) for v in (mx - mn)]
exp = [cd["W"], cd["D"], cd["h_back"] - kbp.CASE["foot_h"]]  # корпус стоит на ножках 1,8 мм
ok_dims = all(abs(d - e) <= 0.05 * e for d, e in zip(dims, exp))
keys = objs["keys"]
coll = bpy.data.collections["ASSET_kb"]
meshes = [o for o in coll.all_objects if o.type == "MESH"]
unique = {o.data.name for o in meshes}
dg = bpy.context.evaluated_depsgraph_get()
tris_total, tris_unique = 0, 0
seen = set()
for o in meshes:
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    t = sum(len(p.vertices) - 2 for p in me.polygons)
    oe.to_mesh_clear()
    tris_total += t
    if o.data.name not in seen:
        seen.add(o.data.name)
        tris_unique += t
# колпачки внутри колодца: все юбки выше пластины и ниже верха колпачков — простая проверка по габаритам в деке
deck_inv = objs["deck"].matrix_world.inverted()
bad = []
for kid, o in keys.items():
    kmn, kmx = bpyx.world_bbox([o])
    pts = [deck_inv @ (o.matrix_world @ Vector(c)) for c in o.bound_box]
    zmin = min(p.z for p in pts)
    if zmin < kbp.DECK["keycap_bottom"] - 1e-4:
        bad.append(kid)
rep = {"colorway": CW, "subd": SUBD, "sec_build": round(t_build, 2), "case_dims_m": dims, "case_expected_m": [round(e, 4) for e in exp],
       "dims_ok": ok_dims, "keys": len(keys), "mesh_objects": len(meshes), "unique_meshes": len(unique),
       "keycap_protos": len(objs["protos"]), "tris_scene": tris_total, "tris_unique_meshes": tris_unique,
       "keys_below_skirt": bad}
print("KB_BUILD", json.dumps(rep, ensure_ascii=False))
assert ok_dims, rep
assert len(keys) == 68 and len(objs["protos"]) == 13, rep
assert not bad, bad

# масса (оценка по объёму сеток: алюминий 2,70, латунь 8,5 г/см³) — для текста «масса считана с модели»
import bmesh  # noqa: E402


def volume(o):
    bm = bmesh.new()
    bm.from_object(o, dg)
    bm.transform(o.matrix_world)
    v = abs(bm.calc_volume(signed=True))
    bm.free()
    return v


v_al = sum(volume(o) for o in case)
v_br = volume(objs["weight"])
rep["mass_g"] = {"case_al_solid": round(v_al * 2.70e6), "brass": round(v_br * 8.5e6),
                 "note": "корпус как сплошное тело без полости под плату — верхняя оценка"}
json.dump(rep, open(os.path.join(HERE, f"build_{CW}.json"), "w"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- сохранение и превью формы
blend = os.path.join(HERE, f"kb_{CW}.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
target = (mn + mx) / 2
a, e = math.radians(-28), math.radians(30)
cam = bpyx.add_camera("PreviewCam", target + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 2,
                      target, lens=70)
bpyx.frame_camera(cam, case, margin=1.12)
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True
bpyx.render_still(os.path.join(HERE, f"preview_{CW}_workbench.png"), resolution=(1280, 720))
# EEVEE с простым светом — материалы и надписи
bpyx.set_color_management("Khronos PBR Neutral", look="None")
r_ = max((mx - mn).length / 2, 0.01)
d = 4 * r_
for nm, az, el, share, sz in (("Key", -60, 45, 1.0, 2.0), ("Fill", 40, 20, 0.35, 3.0), ("Rim", 160, 45, 0.8, 1.5)):
    aa, ee = math.radians(az), math.radians(el)
    bpyx.add_light("AREA", nm, target + Vector((math.sin(aa) * math.cos(ee), -math.cos(aa) * math.cos(ee), math.sin(ee))) * d,
                   target, energy=math.pi * d * d * 3.0 * share, size=r_ * sz)
w = sc.world or bpy.data.worlds.new("World")
sc.world = w
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = bpyx.color("#EDEFF0")
bg.inputs["Strength"].default_value = 0.25
bpyx.set_engine("BLENDER_EEVEE")
sc.eevee.taa_render_samples = 16
bpyx.render_still(os.path.join(HERE, f"preview_{CW}_eevee.png"), resolution=(1280, 720), samples=16)
# крупно Ё
yo = objs["keys"]["yo"]
f = objs["focus"].matrix_world.translation
cam2 = bpyx.add_camera("YoCam", f + Vector((-0.03, -0.09, 0.07)), f, lens=100, set_active=True)
bpyx.render_still(os.path.join(HERE, f"preview_{CW}_yo.png"), resolution=(1280, 720), samples=16)
print("KB_DONE", round(time.time() - t0, 1), "s")
