"""export_web.py — веб-GLB клавиатуры «Ё» для гибрида C (Blender 5.2.2, glTF-IO 5.2.40), фаза 2 (KB2).

python3 $R/99-raw/tools/slot_run.py --label KB2-export -- python3 $R/99-raw/tools/blender_run.py export_web.py \
    --blend ../01-build/kb_snow.blend --timeout 600
Что делает (в памяти, .blend не сохраняет):
  • колпачки LOD1 (SubD 1, без полости и штока): 13 прототипов на 67 клавиш — общие меши на узлах (инстансы glTF);
    надписи — полноцветный атлас расцветки (tex/kc_<cw>.png); UV прототипа смотрят в пустую ячейку (пробел) — в чужом
    просмотрщике колпачки чистые, а страница двигает UV на ячейку клавиши по extras узла kb_uv4 = [c, a, d, b]
    (uv_ключа = (c, a) + (d, b)·uv, пространство UV glTF);
  • Ё — свой меш и своя текстура (tex/yo_<cw>.png: «Ё» и «esc» читаются);
  • узлы слоёв разборки: KB_root → KB_deck → L_keycaps / L_switches / L_stabs / Plate / PCB; корпус, плита, полоса, USB,
    ножки — у KB_root (страница двигает слой по нормали деки, закон kbb.apply_explode);
  • материалы веба по расцветкам (KC_, Yo_, Case_, Chamfer_, Plate_, Switch_<cw>) + общие; привязки
    KHR_materials_variants (условие 1: предпочтение аддона KHR_materials_variants_ui = True; данные — scenes[0]);
  • экспорт пресетом static_hero по коллекции ASSET_web → out/kb_web_raw.glb + отчёт out/export_report.json.
"""
import json
import math
import os
import struct
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbb  # noqa: E402
import kbp  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

R = "/home/mm/Документы/app-design/blender-research"
exec(open(f"{R}/99-raw/experiments/E/24-presets/presets.py").read())   # export(path, preset, **over)
OUT = os.path.join(HERE, "out")
TEX = os.path.join(HERE, "tex")
os.makedirs(OUT, exist_ok=True)
CWS = ["snow", "graphite", "linen"]
AT = json.load(open(os.path.join(TEX, "atlas_web.json")))

prefs = bpy.context.preferences.addons["io_scene_gltf2"].preferences
prefs.KHR_materials_variants_ui = True
sc0 = bpy.data.scenes[0]
sc0.gltf2_KHR_materials_variants_variants.clear()
for i, cw in enumerate(CWS):
    v = sc0.gltf2_KHR_materials_variants_variants.add()
    v.variant_idx = i
    v.name = kbp.COLORWAYS[cw]["title"]


# ---------------------------------------------------------------------- материалы веба
def img(path):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = "sRGB"
    return im


def tex_mat(name, path, rough, ior=1.54):
    mat, bsdf = bpyx.principled(name, base_color="#FFFFFF", roughness=rough, reuse=False)
    nt = mat.node_tree
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img(path)
    t.interpolation = "Linear"
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "LegendUV"
    nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["IOR"].default_value = ior
    return mat


def metal(name, lin, rough):
    return bpyx.principled(name, base_color=(*lin, 1.0), metallic=1.0, roughness=rough, reuse=False)[0]


def plastic(name, hexcol, rough, **kw):
    return bpyx.principled(name, base_color=hexcol, roughness=rough, reuse=False, **kw)[0]


MW = {}
for cw in CWS:
    c = kbp.COLORWAYS[cw]
    MW[("kc", cw)] = tex_mat(f"KC_{cw}", os.path.join(TEX, f"kc_{cw}.png"), 0.58)
    MW[("yo", cw)] = tex_mat(f"Yo_{cw}", os.path.join(TEX, f"yo_{cw}.png"), 0.56)
    MW[("case", cw)] = metal(f"Case_{cw}", c["case"], 0.52)
    MW[("chamfer", cw)] = metal(f"Chamfer_{cw}", c["case"], 0.12)
    MW[("plate", cw)] = metal(f"Plate_{cw}", c["plate"], 0.50)
    MW[("sw", cw)] = plastic(f"Switch_{cw}", c["switch"], 0.42)
MS = {"stem": plastic("Stem", "#EDE4CF", 0.35), "wire": metal("Wire", (0.8, 0.8, 0.82), 0.25),
      "pcb": plastic("PCB_web", "#15171A", 0.5), "brass": metal("Brass_web", kbp.BRASS, 0.30),
      "silicone": plastic("Silicone_web", "#2A2A2B", 0.85, specular_ior_level=0.35), "port": plastic("Port_web", "#0E0F10", 0.6)}


def variants(me, slot_roles):
    """slot_roles: {индекс слота: ключ роли MW} → привязки вариантов (по умолчанию — «Снег»)."""
    me.gltf2_variant_mesh_data.clear()
    me.gltf2_variant_default_materials.clear()
    for slot, role in slot_roles.items():
        for i, cw in enumerate(CWS):
            d = me.gltf2_variant_mesh_data.add()
            d.material_slot_index = slot
            d.material = MW[(role, cw)]
            d.variants.add().variant.variant_idx = i
        dm = me.gltf2_variant_default_materials.add()
        dm.material_slot_index = slot
        dm.default_material = MW[(role, "snow")]


# ---------------------------------------------------------------------- сцена веба
C = D.fresh_collection("ASSET_web")
src = {o.name: o for o in bpy.data.collections["ASSET_kb"].all_objects}
for _n, _o in src.items():                       # имена узлов веба = имена оригиналов → оригиналы переименовать
    _o.name = "SRC_" + _n
dg = bpy.context.evaluated_depsgraph_get()
cd, a, top, M_deck = kbb.case_frames()
root = bpy.data.objects.new("KB_root", None)
C.objects.link(root)
deck = bpy.data.objects.new("KB_deck", None)
C.objects.link(deck)
deck.parent = root
deck.matrix_world = M_deck
layers = {}
for L in ("L_keycaps", "L_switches", "L_stabs"):
    e = bpy.data.objects.new(L, None)
    C.objects.link(e)
    e.parent = deck
    e.matrix_parent_inverse = Matrix.Identity(4)
    e.location = (0, 0, 0)
    layers[L] = e


def baked(ob, name, slots):
    """Меш объекта с применёнными модификаторами (фаски, Weighted Normal) и материалами веба по слотам."""
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = name
    me.materials.clear()
    for m in slots:
        me.materials.append(m)
    return me


def place(name, me, parent, local_matrix, props=None):
    o = bpy.data.objects.new(name, me)
    C.objects.link(o)
    o.parent = parent
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = local_matrix
    for k, v in (props or {}).items():
        o[k] = v
    return o


blank = AT["cells"][AT["blank"]]
Ob, Sb = blank["off"], blank["scl"]
protos = {}
tris = {}
for k in kbp.keys():
    kid = k["id"]
    is_yo = kid == "yo"
    pk = ("yo",) if is_yo else (k["w"], k["profile"], k["homing"])
    if pk not in protos:
        pname = "KCW_yo" if is_yo else "KCW_%su_%s%s" % (k["w"], k["profile"], "_hom" if k["homing"] else "")
        me, info = kbb.keycap_mesh(pname, k["w"], k["profile"], homing=(k["homing"] and not is_yo), subd=1, stem=False,
                                   inner=False)
        if "SideUV" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["SideUV"])
        lu = me.uv_layers["LegendUV"]
        if is_yo:
            so, ss = AT["yo"]["off"], AT["yo"]["scl"]
        else:
            so, ss = Ob, Sb
        for d_ in lu.data:
            d_.uv = (d_.uv[0] * ss[0] + so[0], d_.uv[1] * ss[1] + so[1])
        me.materials.append(MW[("yo" if is_yo else "kc", "snow")])
        variants(me, {0: "yo" if is_yo else "kc"})
        protos[pk] = me
    me = protos[pk]
    if is_yo:
        uv4 = [0.0, 0.0, 1.0, 1.0]
    else:
        ck = AT["cells"][kid]
        Ok, Sk = ck["off"], ck["scl"]
        d_u, b_v = Sk[0] / Sb[0], Sk[1] / Sb[1]
        uv4 = [Ok[0] - d_u * Ob[0], 1 - Ok[1] - b_v * (1 - Ob[1]), d_u, b_v]
    place(f"Key_{kid}", me, layers["L_keycaps"], Matrix.Translation((k["cx"], k["cy"], kbp.DECK["keycap_bottom"])),
          {"kb_id": kid, "kb_code": k["code"], "kb_row": k["row"], "kb_w": k["w"], "kb_role": k["role"], "kb_l1": k["l1"],
           "kb_l2": k["l2"], "kb_uv4": uv4})
# фокус-пустышка (для камеры страницы): верх Ё
hy = bpy.data.objects.new("hotspot_yo", None)
C.objects.link(hy)
hy.parent = bpy.data.objects["Key_yo"]
hy.matrix_parent_inverse = Matrix.Identity(4)
hy.location = src["hotspot_yo"].location.copy()
# свитчи — один меш на 68 узлов
sw_src = src["Sw_q"]
sw_me = sw_src.data.copy()
sw_me.name = "SW_web"
sw_me.materials.clear()
sw_me.materials.append(MW[("sw", "snow")])
sw_me.materials.append(MS["stem"])
variants(sw_me, {0: "sw"})
for k in kbp.keys():
    place(f"Sw_{k['id']}", sw_me, layers["L_switches"], Matrix.Translation((k["cx"], k["cy"], 0.0)))
# стабилизаторы — один меш (4 штуки склеены в координатах деки)
bm = bmesh.new()
for o in [o for n, o in src.items() if n.startswith("Stab_")]:
    tmp = bmesh.new()
    tmp.from_mesh(o.data)
    tmp.transform(Matrix.Translation(o.location))
    tm = bpy.data.meshes.new("tmp_stab")
    tmp.to_mesh(tm)
    tmp.free()
    bm.from_mesh(tm)
    bpy.data.meshes.remove(tm)
st_me = bpy.data.meshes.new("Stabs_web")
bm.to_mesh(st_me)
bm.free()
for m in (MW[("sw", "snow")], MS["stem"], MS["wire"]):
    st_me.materials.append(m)
st_me.shade_smooth()
st_me.set_sharp_from_angle(angle=math.radians(35))
variants(st_me, {0: "sw"})
place("Stabs", st_me, layers["L_stabs"], Matrix.Identity(4))
# пластина и плата (дети деки), корпус и латунь (дети корня)
pl_me = baked(src["Plate"], "Plate_web", [MW[("plate", "snow")]])
variants(pl_me, {0: "plate"})
place("Plate", pl_me, deck, src["Plate"].matrix_basis.copy())
place("PCB", baked(src["PCB"], "PCB_web", [MS["pcb"]]), deck, src["PCB"].matrix_basis.copy())
for nm in ("Case_Top", "Case_Bottom"):
    me = baked(src[nm], f"{nm}_web", [MW[("case", "snow")], MW[("chamfer", "snow")]])
    variants(me, {0: "case", 1: "chamfer"})
    place(nm, me, root, src[nm].matrix_basis.copy())
place("Weight", baked(src["Weight"], "Weight_web", [MS["brass"]]), root, src["Weight"].matrix_basis.copy())
place("Brass_Strip", baked(src["Brass_Strip"], "Strip_web", [MS["brass"]]), root, src["Brass_Strip"].matrix_basis.copy())
place("USB_C", baked(src["USB_C"], "USB_web", [MS["port"]]), root, src["USB_C"].matrix_basis.copy())
bm = bmesh.new()
for n in ("Foot_LF", "Foot_LB", "Foot_RF", "Foot_RB"):
    o = src[n]
    tm = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    tm.transform(o.matrix_basis)
    bm.from_mesh(tm)
    bpy.data.meshes.remove(tm)
ft_me = bpy.data.meshes.new("Feet_web")
bm.to_mesh(ft_me)
bm.free()
ft_me.materials.append(MS["silicone"])
place("Feet", ft_me, root, Matrix.Identity(4))
n_deck = (M_deck.to_3x3() @ Vector((0, 0, 1))).normalized()
root["kb_explode"] = dict(kbp.EXPLODE)
root["kb_ranges"] = {k: list(v) for k, v in kbp.EXPLODE_RANGES.items()}
root["kb_travel"] = kbp.DECK["travel"]
root["kb_deck_normal_three"] = [n_deck.x, n_deck.z, -n_deck.y]
root["kb_colorways"] = CWS
# прятать оригинал: экспорт по коллекции, но на всякий случай
for o in src.values():
    o.hide_render = True
bpy.context.view_layer.update()

# ---------------------------------------------------------------------- счёт и экспорт
dg = bpy.context.evaluated_depsgraph_get()
tri_scene = 0
tri_unique = 0
seen = set()
per = {}
for o in C.all_objects:
    if o.type != "MESH":
        continue
    t = sum(len(p.vertices) - 2 for p in o.data.polygons)
    tri_scene += t
    grp = o.name.split("_")[0]
    per[grp] = per.get(grp, 0) + t
    if o.data.name not in seen:
        seen.add(o.data.name)
        tri_unique += t
raw = os.path.join(OUT, "kb_web_raw.glb")
r = export(raw, "static_hero", collection="ASSET_web")


def glb_json(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])


j = glb_json(raw)
prims = [(m["name"], p.get("material"), bool(p.get("extensions", {}).get("KHR_materials_variants"))) for m in j["meshes"]
         for p in m["primitives"]]
rep = {"export": list(r), "bytes": os.path.getsize(raw), "tris_scene": tri_scene, "tris_unique_meshes": tri_unique,
       "tris_by_group": per, "nodes": len(j["nodes"]), "meshes": len(j["meshes"]), "materials": len(j["materials"]),
       "images": len(j.get("images", [])), "extensionsUsed": j.get("extensionsUsed"),
       "variants": j.get("extensions", {}).get("KHR_materials_variants"),
       "prims_total": len(prims), "prims_with_variants": sum(1 for p in prims if p[2]),
       "prims_without": [p[0] for p in prims if not p[2]], "key_nodes": sum(1 for n in j["nodes"] if n["name"].startswith("Key_")),
       "extras_example": next(n.get("extras") for n in j["nodes"] if n["name"] == "Key_q")}
json.dump(rep, open(os.path.join(OUT, "export_report.json"), "w"), ensure_ascii=False, indent=1)
print("KB_EXPORT", json.dumps(rep, ensure_ascii=False))
