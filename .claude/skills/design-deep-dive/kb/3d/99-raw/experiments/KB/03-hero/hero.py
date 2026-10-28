"""hero.py — hero-варианты «Ё» в Cycles 1600×1000 с ГРИП (фокус — Ё) + маска + экранные точки верха колпачков.

python3 $R/99-raw/tools/slot_run.py --heavy --label KB-hero -- python3 $R/99-raw/tools/blender_run.py hero.py \
    --blend ../01-build/kb_snow.blend --timeout 900 -- H1,H2 [samples]
H1 — весь продукт 3/4, низкий ключ (S2), f/4; H2 — макро Ё, f/2,8; H3 — светлая пастель (S4), весь продукт, f/4;
H4 — низкий ракурс вдоль ряда цифр (S2), f/3,5. Камера каждого варианта → camera_<H>.json (для кода A и гибрида C).
"""
import json
import math
import os
import sys
import time

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbr  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VARS = (argv[0] if argv else "H1").split(",")
SPP = int(argv[1]) if len(argv) > 1 else 128
RES = (1600, 1000)
case = [bpy.data.objects["Case_Top"], bpy.data.objects["Case_Bottom"]]
focus = bpy.data.objects["hotspot_yo"]
mn, mx = bpyx.world_bbox(case)
c = (mn + mx) / 2
r = (mx - mn).length / 2
fw = focus.matrix_world.translation.copy()
V = {
    "H1": dict(rig="S2", page="#1E2023", cyc="#0D0E10", az=-26.0, el=36.0, lens=85.0, margin=1.34, shift_x=-0.13, fstop=4.0,
               exposure=-0.35),
    "H2": dict(rig="S2", page="#1E2023", cyc="#0D0E10", az=-22.0, el=30.0, lens=100.0, dist=0.34, target="yo",
               shift_x=-0.10, shift_y=0.02, fstop=2.8, exposure=-0.35),
    "H3": dict(rig="S4", page="#EFE2D6", cyc="#EFE2D6", az=-26.0, el=36.0, lens=85.0, margin=1.34, shift_x=-0.13, fstop=4.0,
               exposure=-0.35),
    "H4": dict(rig="S2", page="#1E2023", cyc="#0D0E10", az=-78.0, el=13.0, lens=85.0, dist=0.62, target="yo_row",
               shift_x=-0.12, shift_y=0.05, fstop=3.5, exposure=-0.35),
}
keys = [o for o in bpy.data.objects if o.name.startswith("Key_")]
log = {}
for h in VARS:
    v = V[h]
    t0 = time.time()
    st = D.fresh_collection("STAGE")
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o, do_unlink=True)
    if "margin" in v:
        cam = kbr.hero_camera(case, v["az"], v["el"], v["lens"], v["margin"], v["shift_x"], RES, fstop=v["fstop"], focus=focus,
                              name=f"Cam_{h}")
    else:
        sc = bpy.context.scene
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RES[0], RES[1], 100
        tgt = fw.copy()
        if v["target"] == "yo_row":                    # взгляд вдоль ряда цифр: цель — чуть правее Ё, фокус — Ё
            tgt = fw + (bpy.data.objects["Key_5"].matrix_world.translation - fw) * 0.9
        cam = bpyx.add_camera(f"Cam_{h}", kbr.sph(tgt, v["az"], v["el"], v["dist"]), tgt, lens=v["lens"])
        cam.data.sensor_fit = "HORIZONTAL"
        cam.data.sensor_width = 36.0
        cam.data.shift_x, cam.data.shift_y = v["shift_x"], v.get("shift_y", 0.0)
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = v["fstop"]
        cam.data.dof.aperture_blades = 7
        cam.data.dof.aperture_rotation = math.radians(12)
        cam.data.dof.focus_object = focus
    for o in cam.users_collection:
        o.objects.unlink(cam)
    st.objects.link(cam)
    cyc = kbr.RIGS[v["rig"]](st, c, r, v["az"], v["cyc"])
    kbr.view("Khronos PBR Neutral", exposure=v["exposure"])
    out = os.path.join(HERE, f"hero_{h}.png")
    res = kbr.render(out, RES, samples=SPP)
    m = kbr.render_mask(os.path.join(HERE, f"mask_{h}.png"), RES, [cyc])
    # экранные координаты центров верха колпачков (для метрики «главная грань» — белые колпачки, верх)
    sc = bpy.context.scene
    pts = {}
    for o in keys:
        me = o.data
        top = max((Vector(vv.co) for vv in me.vertices), key=lambda p: p.z - 0.3 * abs(p.x) - 0.3 * abs(p.y))
        w = o.matrix_world @ Vector((0.0, top.y * 0.2, top.z - 0.0006))
        u, vv_, z = world_to_camera_view(sc, cam, w)
        if 0 <= u <= 1 and 0 <= vv_ <= 1 and z > 0:
            pts[o.name[4:]] = [round(u * RES[0], 1), round((1 - vv_) * RES[1], 1), o.material_slots[0].material.name]
    json.dump(pts, open(os.path.join(HERE, f"keytops_{h}.json"), "w"), ensure_ascii=False)
    camj = {"name": h, "res": list(RES), **{k: v[k] for k in v if k != "target"}, "location": list(cam.matrix_world.translation),
            "quaternion_wxyz": list(cam.matrix_world.to_quaternion()), "sensor_width_mm": cam.data.sensor_width,
            "lens_mm": cam.data.lens, "shift_x": cam.data.shift_x, "shift_y": cam.data.shift_y,
            "focus_distance_m": (cam.matrix_world.translation - fw).length, "focus_world": list(fw),
            "clip": [cam.data.clip_start, cam.data.clip_end]}
    json.dump(camj, open(os.path.join(HERE, f"camera_{h}.json"), "w"), indent=1)
    log[h] = {"sec": res["sec"], "mask_sec": m["sec"], "spp": SPP, "keytops_in_frame": len(pts),
              "lights": {o.name: round(o.data.energy, 2) for o in st.objects if o.type == "LIGHT"}}
    print("KB_HERO", h, json.dumps(log[h], ensure_ascii=False))
json.dump(log, open(os.path.join(HERE, f"hero_log_{'_'.join(VARS)}.json"), "w"), ensure_ascii=False, indent=1)
