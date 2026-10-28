"""zweb_bake — пробный путь «Звена» в веб на одном модуле (J2), дорожка Z, Blender 5.2.2.

build(P, mode=web, only=j2) → поза «прямо» и модуль в своей системе (узел j2 = шарнир, оси three после экспорта) → детали
слиты в один меш (материалы слотами: вызовов = материалов) → второй UV «AO» (Smart UV) → запекание AO Cycles 64 спп 1024² +
денойз → AO в Occlusion группы «glTF Material Output» (texCoord 1) → экспорт пресетом static_hero → .glb + веб-.blend.

    blender -b --python zweb_bake.py -- --out-dir out/web [--size 1024] [--samples 64] [--ao-dist 0.25]
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
from mathutils import Matrix  # noqa: E402

import bpyx  # noqa: E402
import zbuild  # noqa: E402
import zpass as ZP  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return argv[argv.index(n) + 1] if n in argv else d


OUT = os.path.abspath(opt("--out-dir", Z + "/out/web"))
SIZE = int(opt("--size", 1024))
SPP = int(opt("--samples", 64))
AO_DIST = float(opt("--ao-dist", 0.25))
os.makedirs(OUT, exist_ok=True)
T = {}

t0 = time.time()
bpyx.clear_scene()
c, rep = zbuild.build({"mode": "web", "only": ["j2"], "pose": ZP.POSE_REST, "explode": 0.0, "inner": False})
root = c.roots["j2"]
root.matrix_world = Matrix.Identity(4)                      # модуль в своей системе: код ставит матрицу шарнира сам
bpy.context.view_layer.update()
T["build_s"] = round(time.time() - t0, 2)

# --- слить детали в один меш (связанные копии винтов станут геометрией)
parts = [o for o in c.parts["j2"] if o.type == "MESH"]
for o in parts:
    if o.data.users > 1:
        o.data = o.data.copy()
vl = bpy.context.view_layer
for o in vl.objects:
    o.select_set(False)
for o in parts:
    o.select_set(True)
act = next(o for o in parts if o.name == "j2_shell")
vl.objects.active = act
with bpy.context.temp_override(active_object=act, object=act, selected_objects=parts, selected_editable_objects=parts):
    r = bpy.ops.object.join()
assert r == {"FINISHED"}, r
ob = act
ob.name = "j2_mesh"; ob.data.name = "j2_mesh"
ob.parent = root; ob.matrix_parent_inverse = Matrix.Identity(4)
me = ob.data
T["tris"] = sum(len(p.vertices) - 2 for p in me.polygons)
T["materials"] = [m.name for m in me.materials]

# --- второй UV «AO»: Smart UV без наложений (винты-копии получают свои острова)
uv_first = me.uv_layers[0].name
ao_uv = me.uv_layers.new(name="AO")
me.uv_layers.active = ao_uv
vl.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006)
bpy.ops.uv.average_islands_scale()
bpy.ops.uv.pack_islands(margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")
me.uv_layers[uv_first].active_render = True                 # UV0 для печати остаётся TEXCOORD_0

# --- запекание AO (Cycles): цель — активная нода картинки в КАЖДОМ материале
sc = bpy.context.scene
bpyx.set_engine("CYCLES")
sc.cycles.device = "CPU"; sc.cycles.samples = SPP
w = bpy.data.worlds.new("bakeW"); sc.world = w
w.light_settings.distance = AO_DIST                        # дальность AO: доля размера сустава (Ø 0,47 м)
img = bpy.data.images.new("j2_ao", SIZE, SIZE, alpha=False, float_buffer=True)
img.colorspace_settings.name = "Non-Color"
tmp = []
for m in me.materials:
    nt = m.node_tree
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "AO"
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
    nt.links.new(uvn.outputs["UV"], tn.inputs["Vector"])
    for n in nt.nodes:
        n.select = False
    tn.select = True; nt.nodes.active = tn
    tmp.append((nt, tn, uvn))
t1 = time.time()
me.uv_layers.active = me.uv_layers["AO"]
r = bpy.ops.object.bake(type="AO", margin=8, use_clear=True)
assert "FINISHED" in r, r
T["bake_ao_s"] = round(time.time() - t1, 2)
for nt, tn, uvn in tmp:
    nt.nodes.remove(tn); nt.nodes.remove(uvn)
raw_path = os.path.join(OUT, "j2_ao_raw.png")
img.filepath_raw = raw_path; img.file_format = "PNG"; img.save()

# денойз карты (композитор 5.x: compositing_node_group, выход — Group Output; вид Standard)
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
sc.view_settings.view_transform = "Raw"; sc.view_settings.look = "None"   # AO — данные: без кривой дисплея
old = sc.render.engine
bpyx.set_engine("BLENDER_EEVEE")
hid = [o for o in sc.objects if not o.hide_render]
for o in hid:
    o.hide_render = True
ao_path = os.path.join(OUT, "j2_ao.png")
sc.render.filepath = ao_path
bpy.ops.render.render(write_still=True)
for o in hid:
    o.hide_render = False
sc.render.use_compositing = False; sc.compositing_node_group = None
T["denoise_s"] = round(time.time() - t2, 2)
ao_img = bpy.data.images.load(ao_path, check_existing=False)
ao_img.colorspace_settings.name = "Non-Color"

# --- AO → «glTF Material Output».Occlusion в каждом материале (texCoord 1 = UV «AO»)
from io_scene_gltf2.blender.com.material_helpers import create_settings_group, get_gltf_node_name  # noqa: E402
gname = get_gltf_node_name()
grp = bpy.data.node_groups.get(gname) or create_settings_group(gname)
for m in me.materials:
    nt = m.node_tree
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "AO"
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = ao_img
    nt.links.new(uvn.outputs["UV"], tn.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tn.outputs["Color"], sep.inputs["Color"])
    gn = nt.nodes.new("ShaderNodeGroup"); gn.node_tree = grp
    nt.links.new(sep.outputs["Red"], gn.inputs["Occlusion"])

# --- экспорт пресетом E/24 по коллекции + веб-.blend (для gltf_diff: исходник = то, что уходит в веб)
bpyx.set_engine(old)
exec(open(f"{R}/99-raw/experiments/E/24-presets/presets.py").read())
raw_glb = os.path.join(OUT, "j2_raw.glb")
r = export(raw_glb, "static_hero", collection=c.coll.name)  # noqa: F821
assert r == {"FINISHED"}, r
T["glb_raw_kb"] = round(os.path.getsize(raw_glb) / 1024, 1)
blend = os.path.join(OUT, "j2_web.blend")
img.filepath_raw = raw_path
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
T["total_s"] = round(time.time() - t0, 2)
json.dump(T, open(os.path.join(OUT, "bake.json"), "w"), indent=1, ensure_ascii=False)
print("WEBBAKE", json.dumps(T, ensure_ascii=False))
