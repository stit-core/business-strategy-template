"""study.py — этюд света S1–S4 на кадре hero «Ё» («Снег», 960×540, Cycles 32 спп + OIDN, ГРИП на Ё).

python3 $R/99-raw/tools/slot_run.py --heavy --label KB-light -- python3 $R/99-raw/tools/blender_run.py study.py \
    --blend ../01-build/kb_snow.blend --timeout 900 -- S1,S2,S3,S4 [mask]
"""
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbr  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SCHEMES = (argv[0] if argv else "S1,S2,S3,S4").split(",")
DO_MASK = "mask" in argv
RES = (960, 540)
CAM = dict(az=-26.0, el=36.0, lens=85.0, margin=1.40, shift_x=-0.13, fstop=5.6)
PAGES = {"S1": "#D3D8DD", "S2": "#0F1012", "S3": "#E3D8CB", "S4": "#EFE2D6"}
HAZE = float(os.environ.get("KB_HAZE", "0.0"))

case = [bpy.data.objects["Case_Top"], bpy.data.objects["Case_Bottom"]]
focus = bpy.data.objects["hotspot_yo"]
mn, mx = bpyx.world_bbox(case)
c = (mn + mx) / 2
r = (mx - mn).length / 2
log = {}
for s in SCHEMES:
    t0 = time.time()
    st = D.fresh_collection("STAGE")
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o, do_unlink=True)
    cam = kbr.hero_camera(case, CAM["az"], CAM["el"], CAM["lens"], CAM["margin"], CAM["shift_x"], RES, fstop=CAM["fstop"],
                          focus=focus)
    for o in cam.users_collection:
        o.objects.unlink(cam)
    st.objects.link(cam)
    cyc = kbr.RIGS[s](st, c, r, CAM["az"], PAGES[s], **({"haze": HAZE} if s == "S3" else {}))
    kbr.view("AgX" if s == "S3" else "Khronos PBR Neutral", exposure=0.3 if s == "S3" else -0.25)
    out = os.path.join(HERE, f"light_{s}.png")
    res = kbr.render(out, RES, samples=32)
    log[s] = {"sec": res["sec"], "page_hex": PAGES[s], "view": bpy.context.scene.view_settings.view_transform,
              "lights": {o.name: round(o.data.energy, 2) for o in st.objects if o.type == "LIGHT"}}
    print("KB_LIGHT", s, json.dumps(log[s], ensure_ascii=False))
    if DO_MASK and s == SCHEMES[0]:
        m = kbr.render_mask(os.path.join(HERE, "mask_hero960.png"), RES, [cyc])
        log["mask_sec"] = m["sec"]
cam = bpy.context.scene.camera
camj = {"name": "hero960", "res": list(RES), **CAM, "location": list(cam.matrix_world.translation),
        "quaternion_wxyz": list(cam.matrix_world.to_quaternion()), "sensor_width_mm": cam.data.sensor_width,
        "lens_mm": cam.data.lens, "shift_x": cam.data.shift_x, "shift_y": cam.data.shift_y,
        "focus_world": list(focus.matrix_world.translation), "center": list(c), "radius": r}
json.dump(camj, open(os.path.join(HERE, "camera_hero960.json"), "w"), indent=1)
json.dump(log, open(os.path.join(HERE, f"study_log_{'_'.join(SCHEMES)}.json"), "w"), ensure_ascii=False, indent=1)
print("KB_STUDY_DONE", json.dumps({k: v.get("sec") if isinstance(v, dict) else v for k, v in log.items()}))
