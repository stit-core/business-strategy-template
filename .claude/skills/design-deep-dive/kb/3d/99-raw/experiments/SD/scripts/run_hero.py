"""run_hero.py — hero-варианты 1600×1000 (Cycles + OIDN), маска и экранные координаты булавок для HTML-номеров.
    blender -b --python run_hero.py -- OUT_DIR [--variants H1,H2,H3] [--samples 128] [--res 1600x1000]
H1 — солнце 28° + стяжка; H2 — то же, пол = лист страницы; H3 — свод + высокое мягкое солнце, стяжка."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import sdano_lib as S  # noqa: E402
import bpyx  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0]) if argv else f"{S.X_OUT}/renders/hero"


def opt(n, d):
    return argv[argv.index(n) + 1] if n in argv else d


VAR = {"H1": ("screed", "H_SUN", (-128, 28)), "H2": ("paper", "H_SUN", (-128, 28)), "H3": ("screed", "H_SOFT", (-120, 52)),
       "H1b": ("screed", "H_SUN2", (-128, 32)), "H3b": ("screed", "H_SOFT", (-120, 52))}
variants = opt("--variants", "H1,H2,H3").split(",")
samples = int(opt("--samples", "128"))
res = tuple(int(v) for v in opt("--res", "1600x1000").split("x"))
os.makedirs(out, exist_ok=True)
log = {}
for vn in variants:
    t0 = time.time()
    floor, scheme, (az, el) = VAR[vn]
    bpyx.clear_scene()
    S.P["floor_mode"] = floor
    C, heads = S.build(S.P)
    S.shadow_catcher()
    objs = S.asset_objects()
    cam = S.camera_iso(objs, res=res, margin=float(opt("--margin", "1.07")), extra_pts=S.shadow_points(objs, az, el, h=float(opt("--shadow-h", "1.1"))))
    S.light_scheme(scheme, objs)
    r = S.render(f"{out}/{vn}.png", res, samples)
    S.render_mask(f"{out}/{vn}_mask.png", res)
    marks = S.mark_screen(heads, cam)
    S.save_json(f"{out}/{vn}_marks.json", {"res": res, "ortho_scale": cam.data.ortho_scale, "marks": marks,
                                           "variant": vn, "floor": floor, "scheme": scheme, "rooms": S.room_screen(cam),
                                           "camera": S.camera_basis(cam)})
    log[vn] = {"render_s": r["sec"], "total_s": round(time.time() - t0, 1), "samples": samples}
    print("HERO", json.dumps({vn: log[vn]}))
    bpy.ops.wm.save_as_mainfile(filepath=f"{out}/sdano_{vn}.blend")
S.save_json(f"{out}/hero_times.json", log)
