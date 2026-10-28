"""run_study.py — сборка квартиры и этюд света S1–S4 (одинаковый кадр 960×540, Cycles превью + OIDN), маска, координаты.
    blender -b --python run_study.py -- OUT_DIR [--schemes S1,S2,S3,S4] [--samples 32] [--res 960x540] [--floor screed|paper]
Печатает строки STUDY {...} (время кадров, треугольники, габарит)."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import sdano_lib as S  # noqa: E402
import bpyx  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0]) if argv else f"{S.X_OUT}/renders/study"


def opt(n, d):
    return argv[argv.index(n) + 1] if n in argv else d


schemes = opt("--schemes", "S1,S2,S3,S4").split(",")
samples = int(opt("--samples", "32"))
res = tuple(int(v) for v in opt("--res", "960x540").split("x"))
S.P["floor_mode"] = opt("--floor", "screed")
os.makedirs(out, exist_ok=True)

t0 = time.time()
bpyx.clear_scene()
C, heads = S.build(S.P)
t_build = time.time() - t0
S.shadow_catcher()
objs = S.asset_objects()
cam = S.camera_iso(objs, res=res, margin=1.08)
rep = S.report(C)
print("STUDY", json.dumps({"build_s": round(t_build, 2), **rep}, ensure_ascii=False))
times = {}
KMUL = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in opt("--k", "").split(",") if "=" in kv}
for sc_name in schemes:
    S.light_scheme(sc_name, objs, k=KMUL.get(sc_name, 1.0))
    r = S.render(f"{out}/{sc_name}.png", res, samples)
    times[sc_name] = r["sec"]
    print("STUDY", json.dumps({"scheme": sc_name, "sec": r["sec"], "bytes": r["bytes"]}))
S.render_mask(f"{out}/mask.png", res)
marks = S.mark_screen(heads, cam)
S.save_json(f"{out}/marks.json", {"res": res, "ortho_scale": cam.data.ortho_scale, "marks": marks})
S.save_json(f"{out}/study.json", {"times_s": times, "samples": samples, "res": res, "report": rep, "k": KMUL,
                                  "floor_mode": S.P["floor_mode"], "total_s": round(time.time() - t0, 1)})
bpy.ops.wm.save_as_mainfile(filepath=f"{out}/sdano_study.blend")
print("STUDY", json.dumps({"done": True, "total_s": round(time.time() - t0, 1)}))
