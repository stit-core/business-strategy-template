"""passes_convert.py — многочастный EXR проходов → PNG для «фонарика» (C). Запуск с --blend sdano_v2.blend (камера):
    blender -b sdano_v2.blend --python passes_convert.py -- OUT_DIR"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import sdano_lib as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0])
cam = bpy.data.objects["SD_Cam"]
mk = json.load(open(f"{out}/B2_marks.json"))
FR = mk["frame_uw"]
full = tuple(mk["res"])
half = (full[0] // 2, full[1] // 2)
T = json.load(open(f"{out}/pass_times.json")) if os.path.exists(f"{out}/pass_times.json") else {}
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
