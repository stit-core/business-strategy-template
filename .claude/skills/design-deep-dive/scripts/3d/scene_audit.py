# Blender 5.2.2 — аудит сцены для агента (отправляется целиком через execute_blender_code или запускается в фоне)
# [проверено]. Совместим с BLENDER_MCP_SAFE_MODE (нет lambda/os/numpy/time/class).
# Печатает ОДНУ последнюю строку: AUDIT {json}. Флаги (коды каталога 04-ai-agents-mcp/05, группы M2–M6):
#   default_cube_left, default_names, unapplied_scale, negative_scale, origin_far, floating, below_ground,
#   interpenetration, ngons, nonmanifold, raw_sharp_edges, smooth_across_hard_edges, faceted_curved,
#   no_material, default_gray, viewport_only_color, procedural_textures, many_materials,
#   no_lights, single_sun_only, no_camera, not_in_frame, cropped, too_small_in_frame, off_center, huge_scale, tiny_scale,
#   heavy_mesh, many_draw_calls, text_not_converted
import bpy
import bmesh
import json
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

DEFAULT_PREFIXES = ("Cube", "Sphere", "Cylinder", "Cone", "Torus", "Plane", "Circle", "Icosphere", "Text",
                    "Suzanne", "Mesh", "BezierCurve", "NurbsPath", "Grid")
PROCEDURAL = {"ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeTexWave", "ShaderNodeTexMagic",
              "ShaderNodeTexGradient", "ShaderNodeTexChecker", "ShaderNodeTexBrick", "ShaderNodeTexWhiteNoise",
              "ShaderNodeTexGabor", "ShaderNodeValToRGB", "ShaderNodeBump"}


def is_default_name(name):
    base = name.split(".")[0]
    return base in DEFAULT_PREFIXES


def world_bbox(obj, dg):
    oe = obj.evaluated_get(dg)
    pts = [oe.matrix_world @ Vector(c) for c in oe.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def bbox_gap(a, b):
    d = 0.0
    for i in range(3):
        g = max(b[0][i] - a[1][i], a[0][i] - b[1][i], 0.0)
        d += g * g
    return math.sqrt(d)


def principled_of(mat):
    if not mat or not mat.node_tree:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


def audit():
    scene = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    flags = []
    per_obj = []
    objs = [o for o in scene.objects if o.visible_get()]
    # Область ассета: если есть коллекции ASSET_*, проверяем только их (пол, фон, свет студии — в STAGE)
    asset_names = set()
    for c in bpy.data.collections:
        if c.name.startswith("ASSET_"):
            for o in c.all_objects:
                asset_names.add(o.name)
    geo = [o for o in objs if o.type in ("MESH", "CURVE", "FONT", "SURFACE", "META")]
    if asset_names:
        geo = [o for o in geo if o.name in asset_names]
    meshes = [o for o in geo if o.type == "MESH"]
    counts = {}
    for o in objs:
        counts[o.type] = counts.get(o.type, 0) + 1
    tot = {"tris": 0, "verts": 0, "ngons": 0, "nonmanifold": 0, "draw_calls": 0}
    boxes = {}
    bvh = {}
    for o in geo:
        boxes[o.name] = world_bbox(o, dg)
    # сцена целиком
    if boxes:
        lo = Vector((min(b[0].x for b in boxes.values()), min(b[0].y for b in boxes.values()), min(b[0].z for b in boxes.values())))
        hi = Vector((max(b[1].x for b in boxes.values()), max(b[1].y for b in boxes.values()), max(b[1].z for b in boxes.values())))
    else:
        lo = hi = Vector((0, 0, 0))
    diag = (hi - lo).length
    dims = hi - lo
    for o in geo:
        info = {"name": o.name, "type": o.type}
        s = o.scale
        if any(abs(v - 1.0) > 1e-4 for v in s):
            info["scale"] = [round(v, 3) for v in s]
            flags.append(("unapplied_scale", o.name))
        if o.matrix_world.determinant() < 0:
            flags.append(("negative_scale", o.name))
        if o.type == "FONT":
            flags.append(("text_not_converted", o.name))
        oe = o.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except RuntimeError:
            me = None
        if me is not None and len(me.polygons):
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
            bm.normal_update()
            tris = 0
            ngons = 0
            for f in bm.faces:
                tris += len(f.verts) - 2
                if len(f.verts) > 4:
                    ngons += 1
            nonman = 0
            raw_sharp = 0
            smooth_hard = 0
            sharp_layer = None
            for e in bm.edges:
                if not e.is_manifold and not e.is_boundary:
                    nonman += 1
                if len(e.link_faces) == 2:
                    ang = e.calc_face_angle(0.0)
                    if ang > math.radians(85):
                        raw_sharp += 1
                    if ang > math.radians(60) and e.link_faces[0].smooth and e.link_faces[1].smooth and e.smooth:
                        smooth_hard += 1
            smooth_faces = sum(1 for f in bm.faces if f.smooth)
            nf = len(bm.faces)
            info.update(tris=tris, ngons=ngons, nonmanifold=nonman, raw_sharp_edges=raw_sharp,
                        smooth_across_hard=smooth_hard, smooth_ratio=round(smooth_faces / nf, 2) if nf else 0)
            tot["tris"] += tris
            tot["verts"] += len(bm.verts)
            tot["ngons"] += ngons
            tot["nonmanifold"] += nonman
            mats_used = {f.material_index for f in bm.faces}
            tot["draw_calls"] += max(1, len(mats_used))
            has_bevel = any(m.type in ("BEVEL", "SUBSURF") for m in o.modifiers)
            info["bevel_or_subsurf"] = has_bevel
            if raw_sharp and not has_bevel and o.type == "MESH":
                flags.append(("raw_sharp_edges", o.name))
            if smooth_hard > 4:
                flags.append(("smooth_across_hard_edges", o.name))
            if nf > 48 and smooth_faces == 0 and raw_sharp == 0:
                flags.append(("faceted_curved", o.name))
            if ngons:
                flags.append(("ngons", o.name))
            if nonman:
                flags.append(("nonmanifold", o.name))
            if o.type == "MESH":
                bm.transform(o.matrix_world)          # BVH в МИРОВЫХ координатах (FromObject даёт локальные)
                bvh[o.name] = BVHTree.FromBMesh(bm)
            bm.free()
        if me is not None:
            oe.to_mesh_clear()
        # origin далеко от геометрии
        blo, bhi = boxes[o.name]
        size = (bhi - blo).length
        c = (blo + bhi) / 2
        if size > 0 and (o.matrix_world.translation - c).length > 0.75 * size + 1e-6:
            flags.append(("origin_far", o.name))
        # материалы
        slots = [sl.material for sl in o.material_slots]
        if not slots or all(m is None for m in slots):
            flags.append(("no_material", o.name))
        if is_default_name(o.name):
            info["default_name"] = True
        per_obj.append(info)
    # дефолтный куб: объект и меш «Cube», 8 вершин, габарит 2 м, в начале координат
    cube = scene.objects.get("Cube")
    if (cube and cube.type == "MESH" and cube.data.name == "Cube" and len(cube.data.vertices) == 8
            and cube.location.length < 1e-4 and all(abs(d - 2.0) < 1e-4 for d in cube.dimensions)):
        flags.append(("default_cube_left", "Cube"))
    # все начала координат в нуле мира при разнесённых частях (след transform_apply() с location=True по умолчанию)
    far_parts = [o for o in geo if o.matrix_world.translation.length < 1e-6 and
                 ((boxes[o.name][0] + boxes[o.name][1]) / 2).length > 0.1 * max(diag, 1e-6)]
    if len(far_parts) >= 2:
        flags.append(("origins_at_world_zero", f"{len(far_parts)} of {len(geo)}"))
    dn = [o.name for o in geo if is_default_name(o.name)]
    if len(dn) >= 2:
        flags.append(("default_names", f"{len(dn)} of {len(geo)}"))
    # парение (по мировым AABB) и пересечения (по BVH мировых мешей)
    names = [o.name for o in meshes]
    ground_z = lo.z
    for i in range(len(names)):
        a = names[i]
        best = None
        for j in range(len(names)):
            if i == j:
                continue
            g = bbox_gap(boxes[a], boxes[names[j]])
            best = g if best is None else min(best, g)
        if best is not None and best > max(0.002, 0.01 * diag):
            flags.append(("floating", f"{a} gap={best:.3f}m"))
    # пересечения поверхностей (информативно)
    inter = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ta = bvh.get(names[i])
            tb = bvh.get(names[j])
            if ta and tb and bbox_gap(boxes[names[i]], boxes[names[j]]) == 0.0:
                ov = ta.overlap(tb)
                if ov:
                    inter.append(f"{names[i]}×{names[j]}:{len(ov)}")
    if inter:
        flags.append(("interpenetration", "; ".join(inter[:8])))
    # материалы, которые реально стоят на объектах сцены (не на осиротевших мешах)
    used = set()
    for o in geo:
        for sl in o.material_slots:
            if sl.material is not None:
                used.add(sl.material.name)
    mats = [m for m in bpy.data.materials if m.name in used]
    mat_info = {}
    for m in mats:
        p = principled_of(m)
        rec = {}
        if p is not None:
            bc = p.inputs["Base Color"]
            if not bc.is_linked:
                col = [round(v, 3) for v in bc.default_value[:3]]
                rec["base_color"] = col
                if all(abs(v - 0.8) < 1e-3 for v in col):
                    dc = [round(v, 3) for v in m.diffuse_color[:3]]
                    if any(abs(v - 0.8) > 1e-3 for v in dc):
                        flags.append(("viewport_only_color", m.name))
                    else:
                        flags.append(("default_gray", m.name))
            rec["metallic"] = round(p.inputs["Metallic"].default_value, 2)
            rec["roughness"] = round(p.inputs["Roughness"].default_value, 2)
        if m.node_tree:
            proc = sorted({n.bl_idname for n in m.node_tree.nodes if n.bl_idname in PROCEDURAL})
            if proc:
                rec["procedural"] = proc
                flags.append(("procedural_textures", m.name))
        mat_info[m.name] = rec
    if len(mats) > 12:
        flags.append(("many_materials", str(len(mats))))
    # свет
    lights = [o for o in objs if o.type == "LIGHT"]
    ltypes = [o.data.type for o in lights]
    world_strength = None
    world_color = None
    w = scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.type == "BACKGROUND":
                world_strength = round(n.inputs["Strength"].default_value, 3)
                if n.inputs["Color"].is_linked:
                    world_color = "texture"
                else:
                    world_color = [round(v, 3) for v in n.inputs["Color"].default_value[:3]]
    if not lights and (world_strength is None or world_strength < 0.5):
        flags.append(("no_lights", ""))
    if ltypes and all(t == "SUN" for t in ltypes) and len(ltypes) == 1:
        flags.append(("single_sun_only", ""))
    # камера и кадр
    cam = scene.camera
    frame = None
    if cam is None:
        flags.append(("no_camera", ""))
    elif boxes:
        r = scene.render
        pm = cam.calc_matrix_camera(dg, x=r.resolution_x, y=r.resolution_y,
                                    scale_x=r.pixel_aspect_x, scale_y=r.pixel_aspect_y)
        vm = cam.matrix_world.inverted()
        xs = []
        ys = []
        behind = False
        for o in geo:
            blo, bhi = boxes[o.name]
            for cx in (blo.x, bhi.x):
                for cy in (blo.y, bhi.y):
                    for cz in (blo.z, bhi.z):
                        v = pm @ (vm @ Vector((cx, cy, cz, 1.0)))
                        if v.w <= 0:
                            behind = True
                            continue
                        xs.append((v.x / v.w + 1) / 2)
                        ys.append((v.y / v.w + 1) / 2)
        if xs:
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            area = max(0.0, min(x1, 1) - max(x0, 0)) * max(0.0, min(y1, 1) - max(y0, 0))
            frame = {"x": [round(x0, 3), round(x1, 3)], "y": [round(y0, 3), round(y1, 3)], "area": round(area, 3)}
            if x0 < -0.001 or y0 < -0.001 or x1 > 1.001 or y1 > 1.001 or behind:
                flags.append(("cropped", f"x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f}"))
            if area < 0.005:
                flags.append(("not_in_frame", f"visible bbox area {area:.3f}"))
            elif area < 0.08:
                flags.append(("too_small_in_frame", f"{area:.3f}"))
            cxm = (x0 + x1) / 2
            cym = (y0 + y1) / 2
            if abs(cxm - 0.5) > 0.2 or abs(cym - 0.5) > 0.2:
                flags.append(("off_center", f"center {cxm:.2f},{cym:.2f}"))
    if dims.length > 0:
        if max(dims) > 30:
            flags.append(("huge_scale", f"{max(dims):.1f}m"))
        if max(dims) < 0.02:
            flags.append(("tiny_scale", f"{max(dims):.3f}m"))
    if tot["tris"] > 150000:
        flags.append(("heavy_mesh", str(tot["tris"])))
    if tot["draw_calls"] > 100:
        flags.append(("many_draw_calls", str(tot["draw_calls"])))
    view = scene.view_settings
    return {
        "counts": counts, "totals": tot, "dims_m": [round(v, 3) for v in dims], "bbox_min": [round(v, 3) for v in lo],
        "lights": ltypes, "light_energy": [round(o.data.energy, 1) for o in lights], "world_strength": world_strength, "world_color": world_color,
        "camera": cam.name if cam else None, "frame": frame, "engine": scene.render.engine,
        "view_transform": view.view_transform, "look": view.look, "materials": mat_info,
        "asset_scope": bool(asset_names),
        "objects": per_obj, "flags": [f"{a}: {b}" if b else a for a, b in flags],
        "flag_codes": sorted({a for a, _ in flags}),
    }


print("AUDIT " + json.dumps(audit(), ensure_ascii=False))
