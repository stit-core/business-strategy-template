# Blender 5.2.2 — помощники вариантов модели: рендер варианта в плитку, контактный лист, разбор GLB, постобработка.
import json, math, os, struct, subprocess, sys, time

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb("3d"))
NODE_DIR = str(kbpaths.node_home())  # npm-зависимости — $DDD_HOME/node
NODE_BIN = os.path.dirname(kbpaths.node())


def glb_info(path):
    """Разбор GLB без внешних инструментов: узлы, меши, треугольники и вершины (по аксессорам), материалы,
    расширения, размер. Вершины — сумма count у POSITION примитивов (как их увидит GPU)."""
    data = open(path, "rb").read()
    ln = struct.unpack_from("<I", data, 12)[0]
    j = json.loads(data[20:20 + ln])
    acc = j.get("accessors", [])
    verts = tris = prims = 0
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            prims += 1
            verts += acc[p["attributes"]["POSITION"]]["count"]
            if "indices" in p:
                tris += acc[p["indices"]]["count"] // 3
            else:
                tris += acc[p["attributes"]["POSITION"]]["count"] // 3
    inst = sum(1 for n in j.get("nodes", []) if "EXT_mesh_gpu_instancing" in n.get("extensions", {}))
    return {"bytes": len(data), "kb": round(len(data) / 1024, 1), "nodes": len(j.get("nodes", [])),
            "meshes": len(j.get("meshes", [])), "primitives": prims, "gltf_verts": verts, "tris": tris,
            "materials": [m.get("name") for m in j.get("materials", [])],
            "extensionsUsed": j.get("extensionsUsed", []), "instanced_nodes": inst,
            "node_names": sorted(n.get("name", "") for n in j.get("nodes", []))[:40]}


def gltf_optimize(inp, out, *, safe=True, extra=()):
    """gltf-transform optimize (meshopt + квантование) с безопасными флагами для частей (E 03 §4.1)."""
    env = dict(os.environ, PATH=NODE_BIN + ":" + os.environ.get("PATH", ""))
    cmd = ["npx", "--no-install", "gltf-transform", "optimize", os.path.abspath(inp), os.path.abspath(out),
           "--compress", "meshopt", "--texture-compress", "webp"]
    if safe:
        cmd += ["--flatten", "false", "--join", "false", "--simplify", "false"]
    cmd += list(extra)
    r = subprocess.run(cmd, cwd=NODE_DIR, capture_output=True, text=True, timeout=300, env=env)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])
    return {"bytes": os.path.getsize(out), "kb": round(os.path.getsize(out) / 1024, 1)}


def sheet(pngs, out, cols=None, bg=(0.91, 0.906, 0.89)):
    """Склеить PNG одного размера в лист (OpenImageIO внутри Blender); прозрачность — на фон bg."""
    import numpy as np
    import OpenImageIO as oiio
    tiles = []
    for fp in pngs:
        px = oiio.ImageBuf(fp).get_pixels(oiio.FLOAT)
        if px.shape[2] == 3:
            px = np.concatenate([px, np.ones(px.shape[:2] + (1,), np.float32)], axis=2)
        a = px[..., 3:4]
        px = np.concatenate([px[..., :3] * a + np.array(bg, np.float32) * (1 - a), np.ones_like(a)], axis=2)
        tiles.append(px)
    cols = cols or len(tiles)
    rows = math.ceil(len(tiles) / cols)
    h, w = tiles[0].shape[:2]
    sh = np.zeros((rows * h, cols * w, 4), np.float32)
    sh[..., :3] = bg
    sh[..., 3] = 1
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sh[r * h:(r + 1) * h, c * w:(c + 1) * w] = t[:h, :w]
    spec = oiio.ImageSpec(cols * w, rows * h, 4, oiio.UINT8)
    o = oiio.ImageOutput.create(out)
    o.open(out, spec)
    o.write_image(np.clip(sh, 0, 1))
    o.close()
    return out


def clay_override(on=True):
    """Серая глина поверх всех материалов (форма без цвета) — как render_views.py --clay."""
    vl = bpy.context.view_layer
    if not on:
        vl.material_override = None
        return
    m = bpy.data.materials.get("_d1_clay") or bpy.data.materials.new("_d1_clay")
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (0.62, 0.62, 0.64, 1)
    p.inputs["Roughness"].default_value = 0.55
    vl.material_override = m


def render_to(path, res=(768, 768)):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = os.path.abspath(path)
    t = time.time()
    r = bpy.ops.render.render(write_still=True)
    assert r == {"FINISHED"} and os.path.exists(path), r
    return round(time.time() - t, 2)


def save(obj, path):
    json.dump(obj, open(path, "w"), ensure_ascii=False, indent=1, default=str)
    print("RESULT_JSON", path)
