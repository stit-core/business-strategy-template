"""run_v2.py — фаза 2: кадр B (портрет под правую половину экрана) + маска + координаты + проходы для C.
    blender -b --python run_v2.py -- OUT_DIR [--samples 128] [--width 1800] [--no-passes] [--pass-samples 64]
Кадр в экранных осях орто-камеры: u ∈ [−4,9; 3,7], w ∈ [−0,6; 8,5] м (гостиная и спальня целиком, кухня уходит за правый край)."""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import sdano_lib as S  # noqa: E402
import sdano_v2 as V  # noqa: E402
import bpyx  # noqa: E402
from mathutils import Vector  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0]) if argv else f"{S.X_OUT}/renders/v2"
opt = lambda n, d: argv[argv.index(n) + 1] if n in argv else d  # noqa: E731
samples = int(opt("--samples", "128"))
width = int(opt("--width", "1800"))
FR = dict(u0=-4.9, u1=3.7, w0=-0.6, w1=8.5)
res = (width, round(width * (FR["w1"] - FR["w0"]) / (FR["u1"] - FR["u0"])))
os.makedirs(out, exist_ok=True)
T = {}
t0 = time.time()
bpyx.clear_scene()
C, heads, eng = V.build_v2(V.P2)
S.shadow_catcher()
objs = S.asset_objects()
cam = V.camera_uw(FR["u0"], FR["u1"], FR["w0"], FR["w1"], res)
V.sun_warm(objs)
T["build_s"] = round(time.time() - t0, 2)
rep = S.report(C)
print("V2", json.dumps({"build": T["build_s"], **rep, "res": res}))
r = S.render(f"{out}/B2.png", res, samples)
T["beauty_s"] = r["sec"]
S.render_mask(f"{out}/B2_mask.png", res)
marks = S.mark_screen(heads, cam)
rooms = S.room_screen(cam)
S.save_json(f"{out}/B2_marks.json", {"res": res, "frame_uw": FR, "ortho_scale": cam.data.ortho_scale, "marks": marks,
                                     "rooms": rooms, "camera": S.camera_basis(cam)})
bpy.ops.wm.save_as_mainfile(filepath=f"{out}/sdano_v2.blend")
print("V2", json.dumps({"beauty_s": T["beauty_s"]}))

if "--no-passes" not in argv:
    # ---- проходы для «фонарика» (C): настоящий белый пол вместо ловца теней, чтобы пол имел альбедо, нормаль, глубину, AO
    catcher = bpy.data.objects.get("SD_ShadowCatcher")
    catcher.hide_render = True
    st = bpy.data.collections.get("STAGE")
    ground = bpyx.primitive("plane", "SD_GroundPaper", size=80.0, location=(4.7, 3.2, -0.02), collection=st)
    gm = bpyx.principled("SD_Paper", base_color="#f6f6f4", roughness=0.95)[0]
    bpyx.assign_material(ground, gm)
    sc = bpy.context.scene
    vl = bpy.context.view_layer
    vl.use_pass_diffuse_color = True
    vl.use_pass_normal = True
    vl.use_pass_z = True
    vl.use_pass_ambient_occlusion = True
    sc.world.light_settings.distance = 0.7
    ps = int(opt("--pass-samples", "64"))

    def exr(path, rres, spp):
        S.cycles(spp, denoise=False)
        sc.render.film_transparent = False
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = rres[0], rres[1], 100
        ims = sc.render.image_settings
        ims.media_type = "MULTI_LAYER_IMAGE"
        ims.color_depth = "32"
        sc.render.filepath = path
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        return round(time.time() - t1, 2)

    full = res
    half = (res[0] // 2, res[1] // 2)
    T["pass_full_s"] = exr(f"{out}/passes_full.exr", full, 16)
    T["pass_half_s"] = exr(f"{out}/passes_half.exr", half, ps)
    import OpenImageIO as oiio

    def read_parts(path):
        inp = oiio.ImageInput.open(path)
        chans = {}
        i = 0
        while inp.seek_subimage(i, 0):
            spec = inp.spec()
            px = inp.read_image(i, 0, 0, spec.nchannels, "float")   # i-я часть многочастного EXR, не 0
            px = np.asarray(px).reshape(spec.height, spec.width, spec.nchannels)
            for ci, nm in enumerate(spec.channelnames):
                chans[nm] = px[..., ci]
            i += 1
        inp.close()
        return chans

    def pick(ch, key, comps):
        names = [n for n in ch if key.lower() in n.lower()]
        out_ = []
        for c in comps:
            m = [n for n in names if n.endswith("." + c)]
            out_.append(ch[m[0]])
        return np.stack(out_, -1), names

    def save_png(path, arr8):
        h, w = arr8.shape[:2]
        nch = 1 if arr8.ndim == 2 else arr8.shape[2]
        spec = oiio.ImageSpec(w, h, nch, "uint8")
        o = oiio.ImageOutput.create(path)
        o.open(path, spec)
        o.write_image(np.ascontiguousarray(arr8))
        o.close()

    lin2srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)  # noqa: E731
    chF = read_parts(f"{out}/passes_full.exr")
    chH = read_parts(f"{out}/passes_half.exr")
    print("V2 channels", sorted(chF)[:40])
    alb, nA = pick(chF, "diffuse", ("R", "G", "B"))
    if not nA:
        alb, nA = pick(chF, "diffcol", ("R", "G", "B"))
    alb8 = (np.clip(lin2srgb(alb), 0, 1) * 255 + 0.5).astype(np.uint8)            # OIIO отдаёт EXR сверху вниз — как PNG
    save_png(f"{out}/C_albedo.png", alb8)
    nrm, nN = pick(chH, "normal", ("X", "Y", "Z"))
    Rm = cam.matrix_world.to_3x3()
    right, up, back = [np.array(Rm.col[i].normalized()) for i in range(3)]
    ncam = np.stack([nrm @ right, nrm @ up, nrm @ back], -1)
    ln = np.linalg.norm(ncam, axis=-1, keepdims=True)
    ncam = ncam / np.maximum(ln, 1e-6)
    nrm8 = (np.clip(ncam * 0.5 + 0.5, 0, 1) * 255 + 0.5).astype(np.uint8)
    save_png(f"{out}/C_normal_cam.png", nrm8)
    dep, nD = pick(chH, "depth", ("Z",))
    dep = dep[..., 0]
    valid = dep < 1e5
    dmin, dmax = float(dep[valid].min()), float(dep[valid].max())
    dn = np.clip((dep - dmin) / (dmax - dmin), 0, 1)
    d16 = (dn * 65535 + 0.5).astype(np.uint32)
    ao, nO = pick(chH, "ambient occlusion", ("R",))
    ao = np.clip(ao[..., 0], 0, 1)
    pack = np.stack([(d16 >> 8).astype(np.uint8), (d16 & 255).astype(np.uint8), (ao * 255 + 0.5).astype(np.uint8)], -1)
    save_png(f"{out}/C_depth_ao.png", pack)
    meta = {"res_full": full, "res_half": half, "depth_min_m": dmin, "depth_max_m": dmax, "frame_w_m": FR["u1"] - FR["u0"],
            "frame_h_m": FR["w1"] - FR["w0"], "normal_space": "camera (X right, Y up, Z to viewer), 0..1 = n*0.5+0.5",
            "depth_pack": "R = hi byte, G = lo byte of 16-bit (d - dmin)/(dmax - dmin); B = AO (0..1)",
            "albedo": "Diffuse Color pass, linear → sRGB 8 bit", "channels": {"albedo": nA, "normal": nN, "depth": nD, "ao": nO},
            "times_s": T}
    S.save_json(f"{out}/C_passes.json", meta)
    print("V2", json.dumps({"passes": T, "dmin": dmin, "dmax": dmax}))
