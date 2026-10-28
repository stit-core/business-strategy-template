"""iso_grid.py — изометрическая сетка «миллиметровки» плана (шаг 20 ед. SVG = 1/3 м) на листе под кадром Blender:
точная проекция орто-камеры (базис из *_marks.json), 2× суперсэмплинг, затухание к краям; кадр RGBA кладётся сверху
(тень ловца затемняет и линии сетки). python3 iso_grid.py RENDER.png MARKS.json OUT.png [--step 0.3333] [--color #e9ecef]"""
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw

a = sys.argv[1:]
src, mj, out = a[0], a[1], a[2]
opt = lambda n, d: a[a.index(n) + 1] if n in a else d
step = float(opt("--step", 1 / 3)); col = opt("--color", "#e9ecef").lstrip("#")
rgb = tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))
cam = json.load(open(mj))["camera"]
W, H = cam["res"]; SS = 2
def proj(p):
    d = [p[i] - cam["loc"][i] for i in range(3)]
    du = sum(d[i] * cam["right"][i] for i in range(3)); dv = sum(d[i] * cam["up"][i] for i in range(3))
    sw = cam["ortho_scale"]; sh = sw * H / W
    return ((du / sw + 0.5) * W * SS, (0.5 - dv / sh) * H * SS)
z = -0.02
lines = Image.new("L", (W * SS, H * SS), 0); dr = ImageDraw.Draw(lines)
lo, hi = -12.0, 22.0
k0, k1 = math.floor(lo / step), math.ceil(hi / step)
for k in range(k0, k1 + 1):
    v = k * step
    dr.line([proj((v, lo, z)), proj((v, hi, z))], fill=255, width=2 * SS)
    dr.line([proj((lo, v, z)), proj((hi, v, z))], fill=255, width=2 * SS)
lines = lines.resize((W, H), Image.LANCZOS)
yy, xx = np.mgrid[0:H, 0:W]
cx, cy = proj((4.67, 3.25, z)); cx /= SS; cy /= SS
r = np.hypot((xx - cx) / (W * 0.62), (yy - cy) / (H * 0.62))
fade = np.clip(1.25 - r, 0, 1) ** 1.5
al = (np.asarray(lines).astype(np.float64) / 255) * fade
base = np.ones((H, W, 3)) * 255
base = base * (1 - al[..., None]) + np.array(rgb)[None, None, :] * al[..., None]
bg = Image.fromarray(base.astype(np.uint8), "RGB").convert("RGBA")
im = Image.open(src).convert("RGBA")
bg.alpha_composite(im)
bg.convert("RGB").save(out)
print(out)
