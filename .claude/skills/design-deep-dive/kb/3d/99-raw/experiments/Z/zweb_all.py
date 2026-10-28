"""zweb_all — ассет гибрида C: все 8 модулей «Звена» + начинка J3 + кабель → GLB по контракту крюка CD2
(`15-showcase/_shared/code3d/README.md`), дорожка Z2, Blender 5.2.2.

build(P: web | webl, поза «прямо», начинка) →
  • модуль: детали (кроме начинки, кабеля и наклеек) слиты в меш `<модуль>_mesh`, наклейки — в `<модуль>_decal` (без AO);
    оба — дети пустышки модуля (точка — шарнир, оси three после экспорта +Y, метры scene.js; TRS пустышки код отбрасывает);
  • начинка J3: пустышка `j3_inner` (ребёнок j3) → слои `j3in_<слой>` с extras spread/spin (разведение по X и доля угла ротора —
    как в scanFrame: медь +0,07, генератор волн −0,03, энкодер и плата −0,07; код умножает разведение на 0,9); начало слоёв — на оси X;
  • кабель с сальником — пустышка `cable` (extras zveno_prop = cable): процедурный кабель кода тогда выключен;
  • один атлас AO на всю руку (UV «AO» = TEXCOORD_1, материалы общие → вызовов не больше, чем материалов в меше); на время запекания
    модули и слои разнесены в пространстве: AO только своё (позы и разнос в коде меняют соседей), дальность 0,08 м;
  • экспорт пресетом static_hero по коллекции (custom properties → extras) → `<имя>_raw.glb` + веб-.blend для gltf_diff.

    blender -b --python zweb_all.py -- --mode web|webl --out-dir DIR [--size 2048] [--samples 64] [--ao-dist 0.08] [--cam-az 0.62]
"""
import json
import math
import os
import sys
import time

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
for p in (R + "/03-bpy-api/snippets", R + "/99-raw/experiments/D1/_lib", Z + "/lib", Z):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bpyx  # noqa: E402
import zbuild  # noqa: E402
import zpass as ZP  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return argv[argv.index(n) + 1] if n in argv else d


MODE = opt("--mode", "web")
OUT = os.path.abspath(opt("--out-dir", Z + "/out/web_all"))
SIZE = int(opt("--size", 2048 if MODE == "web" else 1024))
SPP = int(opt("--samples", 64))
AO_DIST = float(opt("--ao-dist", 0.08))
CAM_AZ = float(opt("--cam-az", 0.62))           # печать J1 и кабель — под камеру hero кода (C — камера кода)
NAME = opt("--name", "zveno" if MODE == "web" else "zveno-low")
os.makedirs(OUT, exist_ok=True)
T = {"mode": MODE, "size": SIZE, "samples": SPP, "ao_dist": AO_DIST}

# слои начинки: (признаки имени, spread — м вдоль X при полном разведении ДО ×0,9 кода, spin — доля угла ротора)
LAYERS = [
    ("motor", ("stator", "winding", "endwind"), 0.07, 0.0),
    ("rotor", ("rotor", "mag_"), 0.07, 1.0),
    ("wave", ("wavegen", "flexbearing", "flexspline"), -0.03, 1.0),
    ("gear", ("circspline", "csscrew"), 0.0, 0.0),
    ("outrot", ("xrb_in",), 0.0, -1 / 12),
    ("out", ("xrb_out", "shaft"), 0.0, 0.0),
    ("enc", ("encoder", "slot_"), -0.07, -1 / 12),
    ("pcb", ("readhead", "pcb", "ic_", "capa_", "smd_"), -0.07, 0.0),
]


def layer_of(name):
    n = name[len("j3_in_"):]
    for lay, keys, sp, spin in LAYERS:
        if n.startswith(keys):
            return lay
    return "pcb"


def join(objs, name, parent):
    """Слить объекты в один меш (связанные копии — своими данными), родитель — parent с единичной матрицей."""
    objs = [o for o in objs if o.type == "MESH"]
    for o in objs:
        if o.data.users > 1:
            o.data = o.data.copy()
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    act = objs[0]
    for o in objs:
        o.select_set(True)
    vl.objects.active = act
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=act, object=act, selected_objects=objs, selected_editable_objects=objs):
            r = bpy.ops.object.join()
        assert r == {"FINISHED"}, r
    ob = act
    ob.name = name; ob.data.name = name
    mw = ob.matrix_world.copy()
    ob.parent = parent
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_world = mw
    bpy.context.view_layer.update()
    # геометрию — в систему родителя с единичной локальной матрицей (начало меша = точка модуля / ось слоя)
    loc = ob.matrix_basis.copy()
    if loc != Matrix.Identity(4):
        ob.data.transform(loc)
        ob.matrix_basis = Matrix.Identity(4)
    return ob


def empty(name, coll, parent=None, **props):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"; e.empty_display_size = 0.1
    coll.objects.link(e)
    if parent is not None:
        e.parent = parent; e.matrix_parent_inverse = Matrix.Identity(4)
    for k, v in props.items():
        e[k] = v
    return e


t0 = time.time()
bpyx.clear_scene()
# поза hero (POSE_WORK): печать J1 смотрит на камеру hero кода; позу пустышек код всё равно отбрасывает
c, rep = zbuild.build({"mode": MODE, "pose": ZP.POSE_WORK, "explode": 0.0, "inner": True, "cam_az_three": CAM_AZ})
T["build_s"] = round(time.time() - t0, 2)
coll = c.coll
inner_set = set(c.inner)
is_cable = lambda o: o.name.startswith(("base_cable", "base_gland"))  # noqa: E731
is_decal = lambda o: any(ms.material and ms.material.name.startswith("Z_decal_") for ms in o.material_slots)  # noqa: E731

cable_objs = [o for o in c.parts["base"] if o.type == "MESH" and is_cable(o)]   # до слияний: слитые объекты удаляются
meshes, decals, layers = {}, {}, {}
for k in ZP.ORDER:
    root = c.roots[k]
    parts = [o for o in c.parts[k] if o.type == "MESH" and o not in inner_set and not is_cable(o)]
    dec = [o for o in parts if is_decal(o)]
    body = [o for o in parts if o not in dec]
    meshes[k] = join(body, f"{k}_mesh", root)
    if dec:
        decals[k] = join(dec, f"{k}_decal", root)
# начинка: слои под пустышкой j3_inner
inner_root = empty("j3_inner", coll, c.roots["j3"], zveno_inner=True)
cable_root = empty("cable", coll, None, zveno_prop="cable")
bpy.context.view_layer.update()                  # мировые матрицы новых пустышек — до слияния (иначе слой получит двойной сдвиг)
by_layer = {}
for o in c.inner:
    if o.type == "MESH":
        by_layer.setdefault(layer_of(o.name), []).append(o)
for lay, keys, sp, spin in LAYERS:
    if lay in by_layer:
        ob = join(by_layer[lay], f"j3in_{lay}", inner_root)
        ob["spread"] = sp; ob["spin"] = spin
        layers[lay] = ob
# кабель с сальником — свой узел
cab = join(cable_objs, "cable_mesh", cable_root)
bpy.context.view_layer.update()

baked = list(meshes.values()) + list(layers.values()) + [cab]
T["tris"] = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in baked + list(decals.values())}
T["tris_total"] = sum(T["tris"].values())
T["tris_inner"] = sum(v for n, v in T["tris"].items() if n.startswith("j3in_"))
T["materials"] = sorted({ms.material.name for o in baked + list(decals.values()) for ms in o.material_slots if ms.material})
T["draw_calls_est"] = sum(len([ms for ms in o.material_slots if ms.material]) for o in baked + list(decals.values()))

if "--dry" in argv:                               # сухой прогон: треугольники и вызовы без запекания
    print("WEBALL-DRY", json.dumps({k: v for k, v in T.items() if k != "materials"}, ensure_ascii=False))
    print("WEBALL-MATS", len(T["materials"]), T["materials"])
    raise SystemExit(0)                          # сухой прогон кончается здесь (без запекания и экспорта)

# --- UV «AO»: один атлас на все запекаемые меши (редактирование нескольких объектов)
for o in baked:
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    first = me.uv_layers[0].name
    ao = me.uv_layers.new(name="AO")
    me.uv_layers.active = ao
    me.uv_layers[first].active_render = True
vl = bpy.context.view_layer
for o in vl.objects:
    o.select_set(False)
for o in baked:
    o.select_set(True)
vl.objects.active = baked[0]
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003)
bpy.ops.uv.average_islands_scale()
bpy.ops.uv.pack_islands(margin=0.002)
bpy.ops.object.mode_set(mode="OBJECT")

# --- разнести модули, слои и кабель в пространстве на время запекания (AO — только своё)
saved = {}
movers = list(c.roots.values()) + [inner_root, cable_root]
for i, e in enumerate(movers):
    saved[e.name] = (e.parent, e.matrix_parent_inverse.copy(), e.matrix_world.copy())
for e in movers:
    mw = e.matrix_world.copy(); e.parent = None; e.matrix_world = mw
for i, e in enumerate(movers):
    e.matrix_world = Matrix.Translation((6.0 * (i + 1), 0.0, 0.0))
lay_saved = {o.name: o.matrix_basis.copy() for o in layers.values()}
for j, o in enumerate(layers.values()):
    o.matrix_basis = Matrix.Translation((0.0, 1.2 * (j + 1), 0.0))
for o in decals.values():
    o.hide_render = True
bpy.context.view_layer.update()

# --- запекание AO (Cycles): активная нода картинки в КАЖДОМ материале запекаемых мешей
sc = bpy.context.scene
bpyx.set_engine("CYCLES")
sc.cycles.device = "CPU"; sc.cycles.samples = SPP
w = bpy.data.worlds.new("bakeW"); sc.world = w
w.light_settings.distance = AO_DIST
img = bpy.data.images.new(f"{NAME}_ao", SIZE, SIZE, alpha=False, float_buffer=True)
img.colorspace_settings.name = "Non-Color"
mats = sorted({ms.material for o in baked for ms in o.material_slots if ms.material}, key=lambda m: m.name)
tmp = []
for m in mats:
    nt = m.node_tree
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "AO"
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
    nt.links.new(uvn.outputs["UV"], tn.inputs["Vector"])
    for n in nt.nodes:
        n.select = False
    tn.select = True; nt.nodes.active = tn
    tmp.append((nt, tn, uvn))
for o in vl.objects:
    o.select_set(False)
for o in baked:
    o.select_set(True)
    o.data.uv_layers.active = o.data.uv_layers["AO"]
vl.objects.active = baked[0]
t1 = time.time()
r = bpy.ops.object.bake(type="AO", margin=6, use_clear=True)
assert "FINISHED" in r, r
T["bake_ao_s"] = round(time.time() - t1, 2)
for nt, tn, uvn in tmp:
    nt.nodes.remove(tn); nt.nodes.remove(uvn)
raw_path = os.path.join(OUT, f"{NAME}_ao_raw.png")
img.filepath_raw = raw_path; img.file_format = "PNG"; img.save()

# денойз карты (композитор 5.x; вид Raw — AO как данные)
t2 = time.time()
ng = bpy.data.node_groups.new("DenoiseBake", "CompositorNodeTree")
ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
im = ng.nodes.new("CompositorNodeImage"); im.image = img
dn = ng.nodes.new("CompositorNodeDenoise")
go = ng.nodes.new("NodeGroupOutput")
ng.links.new(im.outputs["Image"], dn.inputs["Image"]); ng.links.new(dn.outputs["Image"], go.inputs[0])
sc.compositing_node_group = ng
sc.render.use_compositing = True
sc.render.resolution_x = sc.render.resolution_y = SIZE; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "BW"
sc.view_settings.view_transform = "Raw"; sc.view_settings.look = "None"
bpyx.set_engine("BLENDER_EEVEE")
hid = [o for o in sc.objects if not o.hide_render]
for o in hid:
    o.hide_render = True
ao_path = os.path.join(OUT, f"{NAME}_ao.png")
sc.render.filepath = ao_path
bpy.ops.render.render(write_still=True)
for o in hid:
    o.hide_render = False
sc.render.use_compositing = False; sc.compositing_node_group = None
T["denoise_s"] = round(time.time() - t2, 2)
ao_img = bpy.data.images.load(ao_path, check_existing=False)
ao_img.colorspace_settings.name = "Non-Color"

# --- AO → «glTF Material Output».Occlusion (texCoord 1 = UV «AO») во всех запекаемых материалах
from io_scene_gltf2.blender.com.material_helpers import create_settings_group, get_gltf_node_name  # noqa: E402
gname = get_gltf_node_name()
grp = bpy.data.node_groups.get(gname) or create_settings_group(gname)
for m in mats:
    nt = m.node_tree
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "AO"
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = ao_img
    nt.links.new(uvn.outputs["UV"], tn.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tn.outputs["Color"], sep.inputs["Color"])
    gn = nt.nodes.new("ShaderNodeGroup"); gn.node_tree = grp
    nt.links.new(sep.outputs["Red"], gn.inputs["Occlusion"])

# --- вернуть иерархию и позу hero (код её всё равно переставит)
for e in movers:
    par, pinv, mw = saved[e.name]
    e.parent = par; e.matrix_parent_inverse = pinv; e.matrix_world = mw
for o in layers.values():
    o.matrix_basis = lay_saved[o.name]
inner_root.matrix_basis = Matrix.Identity(4)
for o in decals.values():
    o.hide_render = False
bpy.context.view_layer.update()

# --- экспорт пресетом E/24 по коллекции + веб-.blend (исходник для gltf_diff)
bpyx.set_engine("CYCLES")
exec(open(f"{R}/99-raw/experiments/E/24-presets/presets.py").read())
raw_glb = os.path.join(OUT, f"{NAME}_raw.glb")
# Z3: --tangents — атрибут TANGENT (MikkTSpace по UV0): без него three берёт направление анизотропии из экранных производных UV0,
# постоянных на треугольнике, — на 48 гранях точёной крышки «веер»; телефону не нужно (Standard без анизотропии)
r = export(raw_glb, "static_hero", collection=coll.name, **({"export_tangents": True} if "--tangents" in argv else {}))  # noqa: F821
assert r == {"FINISHED"}, r
T["glb_raw_kb"] = round(os.path.getsize(raw_glb) / 1024, 1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{NAME}_web.blend"), compress=True)
T["total_s"] = round(time.time() - t0, 2)
json.dump(T, open(os.path.join(OUT, f"{NAME}_bake.json"), "w"), indent=1, ensure_ascii=False)
print("WEBALL", json.dumps({k: v for k, v in T.items() if k != "materials"}, ensure_ascii=False))
