"""colorways.py — три расцветки «Ё» в одном свете и кадре (S1, ракурс H1), Cycles SPP + OIDN, 1600×1000.

python3 $R/99-raw/tools/slot_run.py --heavy --label KB-colorways -- python3 $R/99-raw/tools/blender_run.py colorways.py \
    --blend ../01-build/kb_snow.blend --timeout 900 -- [64]
"""
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbb  # noqa: E402
import kbr  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SPP = int(argv[0]) if argv else 64
RES = (1600, 1000)
M = {"alpha": bpy.data.materials["KC_alpha"], "mod": bpy.data.materials["KC_mod"], "accent": bpy.data.materials["KC_accent"],
     "case": bpy.data.materials["Case_Body"], "chamfer": bpy.data.materials["Case_Chamfer"], "plate": bpy.data.materials["Plate"],
     "sw": bpy.data.materials["Switch_Housing"]}
case = [bpy.data.objects["Case_Top"], bpy.data.objects["Case_Bottom"]]
focus = bpy.data.objects["hotspot_yo"]
mn, mx = bpyx.world_bbox(case)
c = (mn + mx) / 2
r = (mx - mn).length / 2
st = D.fresh_collection("STAGE")
cam = kbr.hero_camera(case, -26.0, 36.0, 85.0, 1.34, -0.13, RES, fstop=4.0, focus=focus, name="Cam_colorways")
for o in cam.users_collection:
    o.objects.unlink(cam)
st.objects.link(cam)
cyc = kbr.rig_S1(st, c, r, -26.0, "#D3D8DD")
kbr.view("Khronos PBR Neutral", exposure=-0.25)
log = {}
for cw in ("snow", "graphite", "linen"):
    kbb.apply_colorway(M, cw)
    res = kbr.render(os.path.join(HERE, f"colorway_{cw}.png"), RES, samples=SPP)
    log[cw] = res["sec"]
    print("KB_COLORWAY", cw, res["sec"])
m = kbr.render_mask(os.path.join(HERE, "mask_colorways.png"), RES, [cyc])
json.dump({"sec": log, "spp": SPP, "light": "S1", "page": "#D3D8DD"}, open(os.path.join(HERE, "colorways_log.json"), "w"), indent=1)
