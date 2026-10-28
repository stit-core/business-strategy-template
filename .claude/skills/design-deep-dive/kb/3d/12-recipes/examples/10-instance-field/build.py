# Сгенерировано run_recipes.py из 12-recipes/10-instance-field.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 35
# Blender 5.2.2 — [проверено] рецепт 10: 900 GN-инстансов → EXT_mesh_gpu_instancing
import sys, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "10-instance-field"
P = dict(n=30, size=1.2, tile=(0.034, 0.034, 0.1), corner=0.006, edge=0.003, h=(0.2, 1.6), seed=11, color="#635BFF",
         bg="#EEF0F6", cam=dict(az=35, el=32, lens=70, margin=1.05, res=(1280, 720)))


def field_tree(proto, P):
    t, gi, go = bpyx.gn_tree("Field", inputs=[("Seed", "NodeSocketInt", P["seed"])], geometry_input=False)
    grid = bpyx.node(t, "GeometryNodeMeshGrid")
    grid.inputs["Size X"].default_value = grid.inputs["Size Y"].default_value = P["size"]
    grid.inputs["Vertices X"].default_value = grid.inputs["Vertices Y"].default_value = P["n"]
    oi = bpyx.node(t, "GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = proto
    inst = bpyx.node(t, "GeometryNodeInstanceOnPoints")
    rnd = bpyx.node(t, "FunctionNodeRandomValue", data_type="FLOAT")
    rnd.inputs["Min"].default_value, rnd.inputs["Max"].default_value = P["h"]
    xyz = bpyx.node(t, "ShaderNodeCombineXYZ"); xyz.inputs["X"].default_value = xyz.inputs["Y"].default_value = 1.0
    L = lambda a, b: bpyx.link_sockets(t, a, b)  # noqa: E731
    L((grid, "Mesh"), (inst, "Points")); L((oi, "Geometry"), (inst, "Instance"))
    L((gi, "Seed"), (rnd, "Seed")); L((rnd, "Value"), (xyz, "Z")); L((xyz, "Vector"), (inst, "Scale"))
    L((inst, "Instances"), (go, "Geometry"))                          # без Realize
    return t


rk.reset()
C = D.fresh_collection("ASSET_field")
mat = rk.web_material("Field_Plastic", "plastic_gloss", P["color"])
proto = D.rounded_slab("TileProto", *P["tile"], P["corner"], (P["edge"], P["edge"]), None, corner_seg=4, edge_seg=2)
bpyx.assign_material(proto, mat)                                      # низ на z = 0 — масштаб Z растит столбик вверх
hidden = D.fresh_collection("glTF_not_exported"); hidden.objects.link(proto); proto.hide_render = True
for c in list(proto.users_collection):
    if c is not hidden:
        c.objects.unlink(proto)
field = bpy.data.objects.new("Field", bpy.data.meshes.new("Field_empty")); C.objects.link(field)
bpyx.gn_modifier(field, field_tree(proto, P))
dg = bpy.context.evaluated_depsgraph_get()
n_inst = sum(1 for oi in dg.object_instances if oi.is_instance and oi.parent and oi.parent.name == "Field")
assert n_inst == P["n"] ** 2, n_inst
# габарит объекта, у которого GN выдаёт только инстансы, bound_box не видит (кадр «в пустоту») → прокси-габарит из паспорта
hx = P["size"] / 2 + P["tile"][0] / 2; hz = P["tile"][2] * P["h"][1]
proxy = bpyx.mesh_object("FieldBounds", [(x, y, z) for x in (-hx, hx) for y in (-hx, hx) for z in (0, hz)],
                         faces=[(0, 1, 3, 2)], collection=hidden)
proxy.hide_render = True
rk.studio([proxy], bg=P["bg"], E_key=2.5, az=P["cam"]["az"], world=0.5)
rk.camera([proxy], **P["cam"])
rk.neutral(samples=32)
rk.render(SLUG, "field_blender", res=P["cam"]["res"], samples=32)
res = rk.ship(SLUG, "ASSET_field", "field", preset="instances", optimize="meshopt")
assert res["raw"]["instanced_nodes"] == 1 and res["raw"]["tris"] < 1000, res["raw"]   # один узел инстансинга, в файле — прототип
rk.save(SLUG, instances=n_inst, passport=P)
