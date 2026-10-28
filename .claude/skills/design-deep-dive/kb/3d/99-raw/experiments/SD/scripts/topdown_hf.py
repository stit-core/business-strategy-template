"""topdown_hf.py (SD3) — карта высот «сверху» для теней фонаря (C): для каждой клетки 2 см плана — верх и низ первого
твёрдого тела под лучом, идущим вертикально вниз (стены 0…1,1 м, фигура 0…1,77, головка булавки 1,34…1,58 — «парит»).
Лучи — BVHTree по оценённым сеткам всех видимых в рендере объектов (без ловца теней); тела объединяются подсчётом глубины
(лицевая грань — вход, тыльная — выход), касающиеся интервалы (< 1 см) сливаются.
    python3 blender_run.py topdown_hf.py --blend renders/v2/sdano_v2.blend -- OUT_DIR [--cell 0.02]
Пишет OUT_DIR/topdown.npy (float32 [ny, nx, 3]: верх и низ первого тела, верх первого СТОЯЩЕГО на полу тела; строка j —
y = y0 + (j + ½)·cell) и topdown.json (сетка, объекты)."""
import json
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0])
cell = float(argv[argv.index("--cell") + 1]) if "--cell" in argv else 0.02
os.makedirs(out, exist_ok=True)
t0 = time.time()
dg = bpy.context.evaluated_depsgraph_get()
verts, polys, info = [], [], []
for ob in bpy.context.scene.objects:
    if ob.type not in {"MESH", "CURVE", "FONT", "SURFACE", "META"}:
        continue
    if ob.hide_render or ob.name.startswith(("SD_ShadowCatcher", "SD_Ground", "WindowGlassLines", "LaserLine", "DoorArcs")):
        continue                        # стекло прозрачно; линия лазера и дуги дверей — не тела
    if not ob.visible_get():
        continue
    ev = ob.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        continue
    if me is None or not len(me.polygons):
        ev.to_mesh_clear()
        continue
    M = ob.matrix_world.copy()
    off = len(verts)
    vs = [M @ v.co for v in me.vertices]
    verts.extend(vs)
    for p in me.polygons:
        polys.append([off + i for i in p.vertices])
    zs = [v.z for v in vs]
    info.append({"name": ob.name, "type": ob.type, "faces": len(me.polygons), "z": [round(min(zs), 3), round(max(zs), 3)]})
    ev.to_mesh_clear()
bvh = BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)
xs = np.array([v.x for v in verts]); ys = np.array([v.y for v in verts])
x0, x1 = float(np.floor((xs.min() - 0.3) / cell) * cell), float(np.ceil((xs.max() + 0.3) / cell) * cell)
y0, y1 = float(np.floor((ys.min() - 0.3) / cell) * cell), float(np.ceil((ys.max() + 0.3) / cell) * cell)
nx, ny = int(round((x1 - x0) / cell)), int(round((y1 - y0) / cell))
FLOOR = -0.02
down = Vector((0.0, 0.0, -1.0))
hf = np.full((ny, nx, 3), FLOOR, np.float32)
casts = 0
for j in range(ny):
    y = y0 + (j + 0.5) * cell
    for i in range(nx):
        x = x0 + (i + 0.5) * cell
        z = 3.0
        depth = 0
        ivs = []
        start = None
        for _ in range(24):
            loc, nrm, idx, dist = bvh.ray_cast(Vector((x, y, z)), down, 10.0)
            casts += 1
            if loc is None:
                break
            hz = loc.z
            if nrm.z > 1e-4:            # лицевая для луча вниз — вход в тело
                if depth == 0:
                    start = hz
                depth += 1
            elif nrm.z < -1e-4:         # тыльная — выход
                if depth > 0:
                    depth -= 1
                    if depth == 0:
                        ivs.append([hz, start])
            z = hz - 1e-4
            if z < FLOOR - 0.01:
                break
        if depth > 0 and start is not None:
            ivs.append([FLOOR, start])
        if not ivs:
            continue
        merged = []                     # касающиеся (< 1 см: игла под головкой, стена на полу) — одно тело
        for bb, tt in ivs:
            if merged and merged[-1][0] - tt < 0.01:
                merged[-1][0] = min(merged[-1][0], bb)
            else:
                merged.append([bb, tt])
        b, t = merged[0]
        g = next((tt for bb, tt in merged if bb <= FLOOR + 0.03), FLOOR)
        hf[j, i] = (t, max(FLOOR, b), g)
np.save(f"{out}/topdown.npy", hf)
meta = {"x0": x0, "y0": y0, "cell": cell, "nx": nx, "ny": ny, "floor": FLOOR, "casts": casts,
        "sec": round(time.time() - t0, 2), "objects": info,
        "top_max": float(hf[..., 0].max()), "n_float": int(((hf[..., 1] > 0.05) & (hf[..., 0] > 0.1)).sum())}
json.dump(meta, open(f"{out}/topdown.json", "w"), ensure_ascii=False, indent=1)
print("TOPDOWN", json.dumps({k: v for k, v in meta.items() if k != "objects"}), "objects", len(info))
for o in info:
    print("  ", o)
