# Сгенерировано run_recipes.py из 12-recipes/07-lowpoly-diorama.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 38
# Blender 5.2.2 — [проверено] рецепт 07: low-poly остров (3d 05/04 §6: палитра, GN-инстансы)
import sys, random, bpy, bmesh
from mathutils import Vector, Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "07-lowpoly-diorama"
P = dict(palette=["#7CB36B", "#5E9451", "#8A6A4F", "#6B5242", "#B9B2A6", "#8F8A82", "#E8D8A8", "#6FA8C9"],
         seed=7, dist_min=0.085, rock_share=0.28, bg="#E8EEF2", res=(768, 768))


def palette_material(pal, path):
    img = bpy.data.images.new("palette", len(pal), 1)
    lin2srgb = lambda c: c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055   # noqa: E731
    px = [v for h in pal for v in bpyx.color(h)]
    img.pixels.foreach_set([lin2srgb(v) if i % 4 != 3 else v for i, v in enumerate(px)])
    img.filepath_raw = path; img.file_format = "PNG"; img.save()
    im = bpy.data.images.load(path); im.colorspace_settings.name = "sRGB"
    m, pr = bpyx.principled("LowPoly_Palette", roughness=0.85)
    tex = m.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = im; tex.interpolation = "Closest"
    bpyx.link_sockets(m.node_tree, (tex, "Color"), (pr, "Base Color"))
    return m


def paint(ob, idx_fn, mat, n):
    uv = ob.data.uv_layers.get("UVMap") or ob.data.uv_layers.new(name="UVMap")
    for p in ob.data.polygons:
        k = idx_fn(p)
        for li in p.loop_indices:
            uv.data[li].uv = ((k + 0.5) / n, 0.5)                  # грань → центр ячейки палитры
    ob.data.shade_flat()
    bpyx.assign_material(ob, mat)


def jitter(ob, amount, seed):
    rng = random.Random(seed)
    for v in ob.data.vertices:
        v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * amount
    ob.data.update()


def scatter_tree(tree, rock, P):
    t, gi, go = bpyx.gn_tree("Scatter", inputs=[("Seed", "NodeSocketInt", P["seed"])])
    nrm = bpyx.node(t, "GeometryNodeInputNormal"); sep = bpyx.node(t, "ShaderNodeSeparateXYZ")
    cmp = bpyx.node(t, "FunctionNodeCompare", data_type="FLOAT", operation="GREATER_THAN"); cmp.inputs["B"].default_value = 0.6
    dist = bpyx.node(t, "GeometryNodeDistributePointsOnFaces", distribute_method="POISSON")
    dist.inputs["Distance Min"].default_value = P["dist_min"]; dist.inputs["Density Max"].default_value = 60.0
    oi_t = bpyx.node(t, "GeometryNodeObjectInfo"); oi_t.inputs["Object"].default_value = tree
    oi_r = bpyx.node(t, "GeometryNodeObjectInfo"); oi_r.inputs["Object"].default_value = rock
    pick = bpyx.node(t, "FunctionNodeRandomValue", data_type="BOOLEAN"); pick.inputs["Probability"].default_value = P["rock_share"]
    g2i = bpyx.node(t, "GeometryNodeGeometryToInstance")
    inst = bpyx.node(t, "GeometryNodeInstanceOnPoints"); inst.inputs["Pick Instance"].default_value = True
    rs = bpyx.node(t, "FunctionNodeRandomValue", data_type="FLOAT"); rs.inputs["Min"].default_value = 0.7; rs.inputs["Max"].default_value = 1.25
    rr = bpyx.node(t, "FunctionNodeRandomValue", data_type="FLOAT_VECTOR"); rr.inputs["Max"].default_value = (0, 0, 6.283)
    L = lambda a, b: bpyx.link_sockets(t, a, b)  # noqa: E731
    L((nrm, "Normal"), (sep, "Vector")); L((sep, "Z"), (cmp, "A"))
    L((gi, "Geometry"), (dist, "Mesh")); L((cmp, "Result"), (dist, "Selection")); L((gi, "Seed"), (dist, "Seed"))
    L((dist, "Points"), (inst, "Points"))
    L((oi_t, "Geometry"), (g2i, "Geometry")); L((oi_r, "Geometry"), (g2i, "Geometry")); L((g2i, "Instances"), (inst, "Instance"))
    L((pick, "Value"), (inst, "Instance Index")); L((gi, "Seed"), (pick, "Seed"))
    L((rs, "Value"), (inst, "Scale")); L((rr, "Value"), (inst, "Rotation")); L((gi, "Seed"), (rs, "Seed")); L((gi, "Seed"), (rr, "Seed"))
    L((inst, "Instances"), (go, "Geometry"))                          # без Realize → EXT_mesh_gpu_instancing
    return t


def build(P):
    C = D.fresh_collection("ASSET_island")
    n = len(P["palette"]); mat = palette_material(P["palette"], f"{rk.out_dir(SLUG)}/palette.png")
    prof = [(0.0, -0.55), (0.18, -0.42), (0.34, -0.22), (0.46, -0.06), (0.52, 0.0), (0.5, 0.03), (0.0, 0.035)]
    island = D.lathe("Island", prof, C, segments=12, smooth_angle=None)
    jitter(island, 0.018, 1)
    paint(island, lambda p: 0 if p.normal.z > 0.6 else (3 if p.center.z > -0.2 else 5), mat, n)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.018, radius2=0.013, depth=0.09, matrix=Matrix.Translation((0, 0, 0.045)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.075, radius2=0.0, depth=0.13, matrix=Matrix.Translation((0, 0, 0.13)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.055, radius2=0.0, depth=0.10,
                          matrix=Matrix.Translation((0, 0, 0.2)) @ Matrix.Rotation(0.4, 4, "Z"))
    tree = D.obj_from_bm(bm, "TreeProto", C, smooth_angle=None)
    paint(tree, lambda p: 2 if p.center.z < 0.07 else (1 if p.center.z < 0.18 else 0), mat, n)
    rock = bpyx.primitive("icosphere", "RockProto", radius=0.04, subdivisions=1, collection=C)
    jitter(rock, 0.008, 3); rock.data.transform(Matrix.Scale(0.6, 4, (0, 0, 1)))
    paint(rock, lambda p: 4 if p.normal.z > 0.3 else 5, mat, n)
    hidden = D.fresh_collection("glTF_not_exported")                 # прототипы: экспортёр пропускает эту коллекцию
    for proto in (tree, rock):
        C.objects.unlink(proto); hidden.objects.link(proto); proto.hide_render = True
    flora = bpy.data.objects.new("Flora", island.data.copy()); C.objects.link(flora)
    flora.data.materials.clear(); flora.data.materials.append(mat)
    bpyx.gn_modifier(flora, scatter_tree(tree, rock, P))
    return C, island, flora


rk.reset()
C, island, flora = build(P)
dg = bpy.context.evaluated_depsgraph_get()
n_inst = sum(1 for oi in dg.object_instances if oi.is_instance and oi.parent and oi.parent.name == "Flora")
assert 10 <= n_inst <= 80, n_inst                                     # разброс не пустой и не «лес»
rk.studio([island, flora], bg=P["bg"], E_key=2.5, az=45, world=0.7)
rk.camera([island, flora], az=45, el=35.264, ortho=True, margin=1.08, res=P["res"])
rk.neutral(samples=32)
rk.audit()
rk.render(SLUG, "iso_blender", res=P["res"], samples=32)
res = rk.ship(SLUG, "ASSET_island", "island", preset="instances", optimize="meshopt")
assert res["raw"]["instanced_nodes"] >= 2, res["raw"]                 # по узлу EXT_mesh_gpu_instancing на прототип
rk.save(SLUG, instances=n_inst, passport=P)
