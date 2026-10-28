"""Тесты bpyx.py для Blender 5.2.x. Запуск (фон, --factory-startup):

    python3 scripts/3d/blender_run.py scripts/3d/test_bpyx.py [-- OUT_DIR]

Код выхода 0 — все тесты зелёные, 1 — есть провалы. OUT_DIR (необязательно) — куда писать test_results.json и
временные файлы рендера/экспорта (по умолчанию — временный каталог, удаляется).
"""
import io
import json
import math
import os
import sys
import tempfile
import time
import traceback
from contextlib import redirect_stdout

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import importlib  # noqa: E402

import bpyx  # noqa: E402

importlib.reload(bpyx)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else None
TMP = tempfile.mkdtemp(prefix="bpyx_test_")
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def fresh(empty=True):
    bpy.ops.wm.read_factory_settings(use_empty=empty)


def approx(a, b, tol=1e-3):
    return abs(a - b) <= tol


def vapprox(a, b, tol=1e-3):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


# ---------------------------------------------------------------------------------------------------- тесты

@test
def t01_version_introspection():
    assert bpyx.version_at_least(5, 2)
    assert bpyx.rna_has(bpy.types.Mesh, "vertices") and not bpyx.rna_has(bpy.types.Mesh, "use_auto_smooth")
    assert not hasattr(bpy.types.Mesh, "vertices"), "hasattr на классе должен быть False (иначе правило устарело)"
    eng = bpyx.enum_values(bpy.context.scene.render, "engine")
    assert {"BLENDER_EEVEE", "CYCLES", "BLENDER_WORKBENCH"} <= set(eng), eng
    vt = bpyx.enum_values(bpy.context.scene.view_settings, "view_transform")
    assert {"AgX", "Standard", "Khronos PBR Neutral"} <= set(vt), vt
    try:
        bpyx.set_enum(bpy.context.scene.render, "engine", "BLENDER_EEVEE_NEXT")
        raise AssertionError("ожидали ValueError")
    except ValueError as e:
        assert "допустимо" in str(e)
    return {"engines": eng, "view_transforms": len(vt)}


@test
def t02_clear_scene():
    fresh(empty=False)
    n0 = len(bpy.context.scene.objects)
    bpyx.ensure_collection("Tmp")
    r = bpyx.clear_scene()
    assert len(bpy.context.scene.objects) == 0 and r["objects"] == n0 == 3, r
    assert len(bpy.context.scene.collection.children) == 0
    assert bpy.context.scene.world is not None
    return r


@test
def t03_collection_link():
    fresh()
    c1 = bpyx.ensure_collection("Props"); c2 = bpyx.ensure_collection("Props")
    assert c1 == c2 and c1.name in bpy.context.scene.collection.children
    sub = bpyx.ensure_collection("Small", parent=c1)
    ob = bpy.data.objects.new("E", None)
    bpyx.link(ob, sub); bpyx.link(ob, sub)
    assert ob.name in bpy.context.scene.objects and len(ob.users_collection) == 1
    return {"collections": [c.name for c in bpy.data.collections]}


@test
def t04_mesh_object():
    fresh()
    v = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0), (0, 0, 1)]
    f = [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    ob = bpyx.mesh_object("Pyr", v, f)
    me = ob.data
    assert (len(me.vertices), len(me.edges), len(me.polygons)) == (5, 8, 5)
    assert not me.polygons[0].use_smooth and ob.name in bpy.context.scene.objects
    ob2 = bpyx.mesh_object("PyrS", v, f, smooth=True, location=(3, 0, 0))
    assert ob2.data.polygons[0].use_smooth and tuple(ob2.location) == (3, 0, 0)
    return {"verts": len(me.vertices)}


@test
def t05_primitives():
    fresh()
    exp = {"cube": ((8, 6), (2, 2, 2)), "uvsphere": ((482, 512), (2, 2, 2)), "icosphere": ((42, 80), (1.902, 2, 2)),
           "cylinder": ((64, 34), (2, 2, 2)), "cone": ((33, 33), (2, 2, 2)), "plane": ((4, 1), (2, 2, 0)),
           "circle": ((32, 1), (2, 2, 0)), "torus": ((512, 512), (2.5, 2.5, 0.5)), "monkey": ((507, 500), None)}
    out = {}
    for i, (k, ((nv, nf), dims)) in enumerate(exp.items()):
        ob = bpyx.primitive(k, location=(i * 3, 0, 0))
        me = ob.data
        assert (len(me.vertices), len(me.polygons)) == (nv, nf), (k, len(me.vertices), len(me.polygons))
        assert me.uv_layers.get("UVMap") is not None, k
        uvs = {tuple(round(c, 4) for c in d.vector) for d in me.uv_layers["UVMap"].uv}
        assert len(uvs) > 3, (k, "UV вырождены")
        if dims:
            mn, mx = bpyx.world_bbox([ob])
            assert vapprox(mx - mn, dims, 1e-2), (k, tuple(mx - mn))
        out[k] = (len(me.vertices), len(me.polygons), len(uvs))
    cyl = bpy.data.objects["Cylinder"].data
    assert cyl.polygons[0].use_smooth and "sharp_edge" in cyl.attributes
    assert not bpy.data.objects["Cube"].data.polygons[0].use_smooth
    return out


@test
def t06_convert_to_mesh():
    fresh()
    cu = bpy.data.curves.new("Title", "FONT"); cu.body = "Hi"; cu.extrude = 0.1
    ob = bpyx.link(bpy.data.objects.new("Title", cu))
    ob.location = (1, 2, 3)
    new = bpyx.convert_to_mesh(ob)
    assert new.type == "MESH" and new.name == "Title" and len(new.data.vertices) > 50
    assert "Title" in bpy.context.scene.objects and bpy.data.objects["Title"] == new
    assert vapprox(new.location, (1, 2, 3))
    mn, mx = bpyx.world_bbox([new])
    assert approx(mx.z - mn.z, 0.2, 1e-3), mx.z - mn.z
    return {"verts": len(new.data.vertices)}


@test
def t07_add_modifier():
    fresh()
    ob = bpyx.primitive("cube")
    b = bpyx.add_modifier(ob, "BEVEL", width=0.05, segments=3, limit_method="ANGLE", affect="EDGES")
    assert b.segments == 3 and b.affect == "EDGES"
    try:
        bpyx.add_modifier(ob, "MIRROR", use_x=True)
        raise AssertionError("ожидали AttributeError")
    except AttributeError as e:
        assert "use_x" in str(e)
    try:
        bpyx.add_modifier(ob, "GREASE_PENCIL_TINT")
        raise AssertionError("ожидали ValueError")
    except ValueError:
        pass
    try:
        bpyx.add_modifier(ob, "SUBDIVISION")
        raise AssertionError("ожидали TypeError")
    except TypeError:
        pass
    assert [m.type for m in ob.modifiers] == ["BEVEL"]
    return {"modifiers": [m.name for m in ob.modifiers]}


@test
def t08_apply_modifiers():
    fresh()
    ob = bpyx.primitive("cube")
    mat, _ = bpyx.principled("Red", base_color="#FF0000")
    bpyx.assign_material(ob, mat)
    vg = ob.vertex_groups.new(name="all"); vg.add(list(range(8)), 1.0, "REPLACE")
    bpyx.add_modifier(ob, "SUBSURF", levels=2)
    bpyx.add_modifier(ob, "TRIANGULATE")
    bpyx.apply_modifiers(ob, count=1)
    assert len(ob.data.vertices) == 98 and [m.type for m in ob.modifiers] == ["TRIANGULATE"]
    assert ob.data.materials[0] == mat and sum(1 for v in ob.data.vertices if v.groups) == 98
    bpyx.apply_modifiers(ob)
    assert not ob.modifiers and all(len(p.vertices) == 3 for p in ob.data.polygons)
    return {"verts": len(ob.data.vertices), "faces": len(ob.data.polygons)}


@test
def t09_apply_transforms():
    fresh()
    ob = bpyx.primitive("cube", size=1.0)
    ob.location = (2, 0, 0); ob.rotation_euler = (0, 0, math.radians(45)); ob.scale = (2, 1, 1)
    child = bpyx.link(bpy.data.objects.new("Child", None))
    child.parent = ob; child.location = (1, 0, 0)
    bpy.context.view_layer.update()
    before_child = child.matrix_world.translation.copy()
    before_v = [ob.matrix_world @ v.co for v in ob.data.vertices]
    dims_before = ob.dimensions.copy()
    bpyx.apply_transforms(ob)
    after_v = [ob.matrix_world @ v.co for v in ob.data.vertices]
    assert all(vapprox(a, b) for a, b in zip(before_v, after_v))
    assert vapprox(ob.scale, (1, 1, 1)) and vapprox(ob.rotation_euler, (0, 0, 0)) and vapprox(ob.location, (2, 0, 0))
    assert vapprox(child.matrix_world.translation, before_child), (tuple(child.matrix_world.translation), tuple(before_child))
    return {"dims_before": [round(x, 3) for x in dims_before], "dims_after": [round(x, 3) for x in ob.dimensions]}


@test
def t10_smooth_by_angle():
    fresh()
    cyl = bpyx.primitive("cylinder", smooth=False)
    bpyx.smooth_by_angle(cyl, 30)
    sharp = cyl.data.attributes["sharp_edge"]
    n_sharp = sum(1 for d in sharp.data if d.value)
    assert n_sharp == 64 and cyl.data.polygons[0].use_smooth, n_sharp
    cube = bpyx.primitive("cube")
    m = bpyx.smooth_by_angle(cube, 30, method="MODIFIER")
    assert m.type == "NODES" and m.node_group.name.startswith("Smooth by Angle")
    return {"sharp_edges": n_sharp, "modifier": m.name}


@test
def t11_world_bbox_font_fix():
    fresh()
    cu = bpy.data.curves.new("T", "FONT"); cu.body = "Hello"; cu.extrude = 0.1; cu.bevel_depth = 0.02
    ob = bpyx.link(bpy.data.objects.new("T", cu))
    mn, mx = bpyx.world_bbox([ob])
    dz = mx.z - mn.z
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    dz_eval = max(c[2] for c in oe.bound_box) - min(c[2] for c in oe.bound_box)
    assert approx(dz, 0.24, 1e-3) and dz_eval < 1e-6, (dz, dz_eval)
    return {"dz_original": round(dz, 4), "dz_evaluated_bbox": round(dz_eval, 4)}


@test
def t12_floor_center_origin():
    fresh()
    a = bpyx.primitive("cube", location=(5, 3, 2)); b = bpyx.primitive("uvsphere", location=(7, 3, -1))
    bpyx.put_on_floor([a, b])
    mn, mx = bpyx.world_bbox([a, b])
    assert approx(mn.z, 0.0)
    bpyx.center_objects([a, b], "XY")
    mn, mx = bpyx.world_bbox([a, b])
    assert approx((mn.x + mx.x) / 2, 0) and approx((mn.y + mx.y) / 2, 0) and approx(mn.z, 0)
    c = bpyx.primitive("cube", size=1.0)
    c.data.transform(__import__("mathutils").Matrix.Translation((3, 0, 1)))
    w_before = [c.matrix_world @ v.co for v in c.data.vertices]
    off = bpyx.origin_to_center(c)
    w_after = [c.matrix_world @ v.co for v in c.data.vertices]
    assert vapprox(off, (3, 0, 1)) and all(vapprox(x, y) for x, y in zip(w_before, w_after)) and vapprox(c.location, (3, 0, 1))
    return {"floor_min_z": round(mn.z, 5)}


@test
def t13_stats_report():
    fresh()
    ob = bpyx.primitive("cube"); bpyx.add_modifier(ob, "SUBSURF", levels=1)
    s = bpyx.object_stats(ob)
    assert s["verts"] == 26 and s["tris"] == 48 and s["ngons"] == 0, s
    assert s["dims"] == [2.0, 2.0, 2.0] and s["modifiers"] == ["SUBSURF"] and s["uv_layers"] == ["UVMap"], s
    bpyx.add_camera()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rep = bpyx.scene_report()
    assert rep["tris"] == 48 and rep["camera"] == "Camera" and "SCENE_REPORT" in buf.getvalue()
    return {"stats": s, "report_tris": rep["tris"]}


@test
def t14_color():
    c = bpyx.color("#FF8000")
    assert vapprox(c, (1.0, 0.2158605, 0.0, 1.0), 1e-4), c
    assert bpyx.color((0.2, 0.3, 0.4)) == (0.2, 0.3, 0.4, 1.0)
    buf = io.StringIO()
    with redirect_stdout(buf):
        c2 = bpyx.color((255, 128, 0))
    assert vapprox(c2, (1.0, 0.2158605, 0.0, 1.0), 1e-4) and "0..255" in buf.getvalue()
    try:
        bpyx.color((1, 0))
        raise AssertionError("ожидали ValueError")
    except ValueError:
        pass
    return {"hex_FF8000_linear": [round(x, 4) for x in c]}


@test
def t15_principled():
    fresh()
    buf = io.StringIO()
    with redirect_stdout(buf):
        mat, p = bpyx.principled("Glass", base_color="#88CCFF", roughness=0.05, transmission=1.0, ior=1.45,
                                 emission_color=(1, 0.5, 0.1), emission_strength=0.0, specular=0.5)
    assert p.inputs["Transmission Weight"].default_value == 1.0 and approx(p.inputs["IOR"].default_value, 1.45)
    assert approx(p.inputs["Specular IOR Level"].default_value, 0.5) and "переименован" in buf.getvalue()
    assert bpyx.find_node(mat.node_tree, "OUTPUT_MATERIAL").inputs["Surface"].is_linked
    assert bpyx.assert_valid_links(mat.node_tree) == 1
    try:
        bpyx.principled("X", roughnes=0.3)
        raise AssertionError("ожидали KeyError")
    except KeyError as e:
        assert "Roughness" in str(e)
    m2, p2 = bpyx.principled("Glass", roughness=0.2)
    assert m2 == mat and approx(p2.inputs["Roughness"].default_value, 0.2)
    return {"inputs_set": 7}


@test
def t16_nodes_sockets_links():
    fresh()
    mat, p = bpyx.principled("Proc")
    t = mat.node_tree
    noise = bpyx.node(t, "ShaderNodeTexNoise", inputs={"Scale": 4.0, "Detail": 6.0})
    mix = bpyx.node(t, "ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    assert bpyx.sock(mix, "A").identifier == "A_Color" and bpyx.sock(mix, "A_Color").identifier == "A_Color"
    try:
        bpyx.sock(mix, "A_Float")
        raise AssertionError("ожидали KeyError")
    except KeyError as e:
        assert "недоступен" in str(e)
    bpyx.set_input(mix, "B", "#FFFFFF")
    bpyx.link_sockets(t, (noise, "Color"), (mix, "A"))
    bpyx.link_sockets(t, (mix, "Result"), (p, "Base Color"))
    try:
        bpyx.link_sockets(t, (p, "BSDF"), (mix, "B"))
        raise AssertionError("ожидали ValueError")
    except ValueError:
        pass
    try:
        bpyx.node(t, "ShaderNodeMix", datatype="RGBA")
        raise AssertionError("ожидали AttributeError")
    except AttributeError as e:
        assert "data_type" in str(e)
    fr = t.nodes.new("NodeFrame"); fr.location = (300, 300); noise.parent = fr
    cols = bpyx.layout_tree(t)
    assert cols >= 3 and bpyx.assert_valid_links(t) == 3
    return {"columns": cols}


@test
def t17_assign_material():
    fresh()
    ob = bpyx.primitive("cube")
    m1, _ = bpyx.principled("A"); m2, _ = bpyx.principled("B"); m3, _ = bpyx.principled("C")
    bpyx.assign_material(ob, m1)
    bpyx.assign_material(ob, m2, replace=False)
    bpyx.assign_material(ob, m3, slot=3)
    assert [m.name if m else None for m in ob.data.materials] == ["A", "B", None, "C"]
    bpyx.assign_material(ob, m2)
    assert [m.name for m in ob.data.materials] == ["B"]
    return {"slots": len(ob.material_slots)}


@test
def t18_camera_light_frame():
    fresh()
    from bpy_extras.object_utils import world_to_camera_view
    a = bpyx.primitive("cube", location=(0, 0, 1)); b = bpyx.primitive("uvsphere", location=(3, 1, 1))
    cam = bpyx.add_camera(location=(4, -8, 5), target=(1.5, 0.5, 1))
    bpy.context.view_layer.update()
    p = world_to_camera_view(bpy.context.scene, cam, Vector((1.5, 0.5, 1)))
    assert approx(p.x, 0.5) and approx(p.y, 0.5) and p.z > 0, tuple(p)
    bpyx.frame_camera(cam, [a, b], margin=1.1)
    mn, mx = bpyx.world_bbox([a, b])
    corners = [Vector((x, y, z)) for x in (mn.x, mx.x) for y in (mn.y, mx.y) for z in (mn.z, mx.z)]
    proj = [world_to_camera_view(bpy.context.scene, cam, c) for c in corners]
    assert all(0 <= q.x <= 1 and 0 <= q.y <= 1 and q.z > 0 for q in proj), [tuple(round(v, 3) for v in q) for q in proj]
    lights = bpyx.three_point_lights([a, b])
    assert len(lights) == 3 and all(l.type == "LIGHT" and l.data.type == "AREA" for l in lights)
    sun = bpyx.add_light("SUN", energy=3.0, size=0.5)
    assert approx(sun.data.angle, 0.5)
    # орто 16:9: брус 11,5 м целиком в кадре при любом исходном ortho_scale (10,0 и 5,9 резали модель)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    beam = bpyx.primitive("cube", "Beam", size=1.0, location=(0, 5, 1.5)); beam.scale = (11.5, 1.0, 3.0)
    oc = bpyx.add_camera("OrthoCam", location=(0, -25, 1.5), target=(0, 5, 1.5), set_active=False)
    oc.data.type = "ORTHO"
    for s0 in (6.0, 20.0):
        oc.data.ortho_scale = s0
        bpyx.frame_camera(oc, [beam], margin=1.1)
        qo = [world_to_camera_view(sc, oc, beam.matrix_world @ Vector(c)) for c in beam.bound_box]
        assert all(0 <= p.x <= 1 and 0 <= p.y <= 1 for p in qo) and approx(oc.data.ortho_scale, 12.65), (s0, oc.data.ortho_scale)
    return {"key_W": round(lights[0].data.energy, 1), "proj_x_range": [round(min(q.x for q in proj), 3), round(max(q.x for q in proj), 3)],
            "ortho_scale_16x9": round(oc.data.ortho_scale, 3)}


@test
def t19_engine_color():
    fresh()
    assert bpyx.set_engine("EEVEE") == "BLENDER_EEVEE" and bpyx.set_engine("BLENDER_EEVEE_NEXT") == "BLENDER_EEVEE"
    assert bpyx.set_engine("Cycles") == "CYCLES" and bpyx.set_engine("WORKBENCH") == "BLENDER_WORKBENCH"
    try:
        bpyx.set_engine("OCTANE")
        raise AssertionError("ожидали ValueError")
    except ValueError as e:
        assert "CYCLES" in str(e)
    r = bpyx.set_color_management("Khronos PBR Neutral")
    assert r["view_transform"] == "Khronos PBR Neutral"
    r = bpyx.set_color_management("AgX", look="AgX - Punchy")
    assert r["look"] == "AgX - Punchy"
    try:
        bpyx.set_color_management("Filmic2")
        raise AssertionError("ожидали ValueError")
    except ValueError:
        pass
    return r


@test
def t20_render_still():
    fresh()
    bpyx.primitive("uvsphere"); bpyx.add_camera(location=(0, -5, 2)); bpyx.three_point_lights()
    out = OUT or TMP
    r1 = bpyx.render_still(os.path.join(out, "t20_eevee.png"), resolution=(96, 96), engine="EEVEE", samples=4,
                           transparent=True)
    r2 = bpyx.render_still(os.path.join(out, "t20_cycles.webp"), resolution=(96, 96), engine="CYCLES", samples=8,
                           file_format="WEBP", quality=80)
    try:
        bpy.context.scene.camera = None
        bpyx.render_still(os.path.join(out, "x.png"), resolution=(32, 32))
        raise AssertionError("ожидали RuntimeError")
    except RuntimeError as e:
        assert "камеры" in str(e)
    for f in ("t20_eevee.png", "t20_cycles.webp"):
        if OUT is None:
            os.remove(os.path.join(out, f))
    return {"eevee": r1["sec"], "cycles": r2["sec"], "bytes": [r1["bytes"], r2["bytes"]]}


@test
def t21_export_glb():
    fresh()
    a = bpyx.primitive("cube", name="Keep"); b = bpyx.primitive("uvsphere", name="Skip", location=(3, 0, 0))
    ch = bpyx.primitive("cone", name="KeepChild", location=(0, 0, 2)); ch.parent = a
    bpyx.add_modifier(a, "SUBSURF", levels=1)
    b.select_set(True); bpy.context.view_layer.objects.active = b
    buf = io.StringIO()
    with redirect_stdout(buf):
        r = bpyx.export_glb(os.path.join(TMP, "t21"), [a], export_selected=True, export_draco_mesh_compression_enable=False)
    assert r["path"].endswith(".glb") and r["bytes"] > 1000 and "export_selected" in buf.getvalue()
    import struct
    data = open(r["path"], "rb").read()
    jlen = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + jlen])
    names = sorted(n["name"] for n in gltf["nodes"])
    assert names == ["Keep", "KeepChild"], names
    assert b.select_get() and bpy.context.view_layer.objects.active == b and not a.select_get()
    os.remove(r["path"])
    return {"nodes": names, "bytes": r["bytes"]}


@test
def t22_uv_unwrap():
    fresh()
    cube = bpyx.primitive("cube", uv=False)
    other = bpyx.primitive("uvsphere", location=(3, 0, 0)); other.select_set(True)
    bpy.context.view_layer.objects.active = other
    res = {}
    for m in ("SMART", "ANGLE_BASED", "LIGHTMAP", "CUBE"):
        name = bpyx.uv_unwrap(cube, m)
        uv = cube.data.uv_layers[name]
        pts = {tuple(round(c, 4) for c in d.vector) for d in uv.uv}
        # CUBE: каждая грань куба проецируется в один и тот же квадрат (острова перекрываются) → 4 точки
        assert len(pts) >= (4 if m == "CUBE" else 8), (m, len(pts))
        res[m] = len(pts)
    assert bpy.context.mode == "OBJECT" and bpy.context.view_layer.objects.active == other and other.select_get()
    assert not cube.select_get()
    return res


@test
def t23_geometry_nodes():
    fresh()
    tree, gi, go = bpyx.gn_tree("Line", inputs=[("Count", "NodeSocketInt", 4, 2, 100),
                                                {"name": "Spacing", "socket_type": "NodeSocketFloat", "default": 0.5,
                                                 "subtype": "DISTANCE"}], geometry_input=False)
    line = bpyx.node(tree, "GeometryNodeMeshLine")
    comb = bpyx.node(tree, "ShaderNodeCombineXYZ")
    bpyx.link_sockets(tree, (gi, "Count"), (line, "Count"))
    bpyx.link_sockets(tree, (gi, "Spacing"), (comb, "X"))
    bpyx.link_sockets(tree, (comb, "Vector"), (line, "Offset"))
    bpyx.link_sockets(tree, (line, "Mesh"), (go, "Geometry"))
    ob = bpyx.link(bpy.data.objects.new("GN", bpy.data.meshes.new("GN")))
    mod = bpyx.gn_modifier(ob, tree, Count=10)
    dg = bpy.context.evaluated_depsgraph_get()
    n1 = len(ob.evaluated_get(dg).data.vertices)
    bpyx.gn_set_input(mod, "Count", 25)
    n2 = len(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices)
    ident = bpyx.gn_set_input(mod, "Spacing", 1.0)
    mn, mx = bpyx.world_bbox([ob])
    assert (n1, n2) == (10, 25) and approx(mx.x - mn.x, 24.0), (n1, n2, mx.x - mn.x)
    assert set(bpyx.gn_inputs(mod)) == {"Count", "Spacing"} and ident.startswith("Socket_")
    bpyx.apply_modifiers(ob)
    assert len(ob.data.vertices) == 25 and not ob.modifiers
    return {"n1": n1, "n2": n2, "inputs": bpyx.gn_inputs.__name__}


@test
def t24_view3d_override():
    fresh(empty=False)
    ov = bpyx.view3d_override()
    assert ov is not None and ov["area"].type == "VIEW_3D"
    cam = bpy.context.scene.camera
    before = cam.location.copy()
    with bpy.context.temp_override(**ov):
        r = bpy.ops.view3d.camera_to_view_selected()
    assert r == {"FINISHED"} and (cam.location - before).length > 1e-3
    return {"moved": round((cam.location - before).length, 3)}


@test
def t25_mcp_style_loading():
    fresh()
    src = os.path.join(HERE, "bpyx.py")
    ns = {"bpy": bpy}
    exec(compile(open(src, encoding="utf-8").read(), src, "exec"), ns)       # как вставка в execute_blender_code
    ob = ns["primitive"]("cube", name="ViaExec")
    assert ob.name == "ViaExec" and ns["rna_has"](bpy.types.Mesh, "vertices")
    ns2 = {"bpy": bpy}
    code = (f"import sys, importlib\nsys.dont_write_bytecode = True\np = {HERE!r}\n"
            "if p not in sys.path:\n    sys.path.insert(0, p)\nimport bpyx\nimportlib.reload(bpyx)\n"
            "print(bpyx.__version__, len(bpy.data.objects))")
    buf = io.StringIO()
    with redirect_stdout(buf):
        exec(code, ns2)
    assert buf.getvalue().strip() == f"{bpyx.__version__} 1", buf.getvalue()
    return {"exec_ok": True, "import_ok": buf.getvalue().strip()}


# ---------------------------------------------------------------------------------------------------- раннер

def main():
    results = []
    t_all = time.time()
    for fn in TESTS:
        t0 = time.time()
        try:
            info = fn()
            results.append({"test": fn.__name__, "ok": True, "sec": round(time.time() - t0, 3), "info": info})
            print(f"PASS {fn.__name__} ({time.time() - t0:.2f} s) {json.dumps(info, ensure_ascii=False, default=str)[:180]}")
        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc()
            results.append({"test": fn.__name__, "ok": False, "sec": round(time.time() - t0, 3),
                            "error": f"{type(e).__name__}: {e}", "traceback": tb})
            print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}\n{tb}")
    n_ok = sum(r["ok"] for r in results)
    summary = {"blender": bpy.app.version_string, "bpyx": bpyx.__version__, "passed": n_ok, "total": len(results),
               "sec": round(time.time() - t_all, 2), "results": results}
    print(f"RESULT {n_ok}/{len(results)} passed in {summary['sec']} s (Blender {bpy.app.version_string}, bpyx {bpyx.__version__})")
    if OUT:
        os.makedirs(OUT, exist_ok=True)
        json.dump(summary, open(os.path.join(OUT, "test_results.json"), "w"), ensure_ascii=False, indent=1, default=str)
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
    if n_ok != len(results):
        sys.exit(1)


main()
