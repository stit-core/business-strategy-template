"""variants_export.py — пробел базы: пишет ли glTF-IO 5.2.40 (Blender 5.2.2) KHR_materials_variants из фона.

python3 $R/99-raw/tools/slot_run.py --label KB-variants -- python3 $R/99-raw/tools/blender_run.py variants_export.py --timeout 300
Что делает: 3 колпачка «Ё» (Ё, Й, tab) → по 3 материала-варианта на роль (snow / graphite / linen; у Й в «графите» — своя
текстура надписей, светлая на тёмном) → варианты через данные аддона (scenes[0].gltf2_KHR_materials_variants_variants,
mesh.gltf2_variant_mesh_data, gltf2_variant_default_materials) → экспорт GLB пресетом static_hero → отчёт по JSON файла.
Условие аддона (исходник io_scene_gltf2 5.2.40, primitives.py:336): предпочтение KHR_materials_variants_ui = True —
без него расширение не пишется (и типы свойств не зарегистрированы). В фоне с --factory-startup это настройка в памяти
процесса, в userpref.blend не сохраняется (Blender -b не пишет настройки при выходе).
"""
import json
import os
import struct
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbb  # noqa: E402
import kbp  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

R = "/home/mm/Документы/app-design/blender-research"
exec(open(f"{R}/99-raw/experiments/E/24-presets/presets.py").read())   # export(path, preset, **over)

bpyx.clear_scene()
prefs = bpy.context.preferences.addons["io_scene_gltf2"].preferences
before = {"KHR_materials_variants_ui": prefs.KHR_materials_variants_ui,
          "scene_has_prop": "gltf2_KHR_materials_variants_variants" in bpy.types.Scene.bl_rna.properties}
prefs.KHR_materials_variants_ui = True                       # update-колбэк регистрирует типы variant_register()
after = {"KHR_materials_variants_ui": prefs.KHR_materials_variants_ui,
         "scene_has_prop": "gltf2_KHR_materials_variants_variants" in bpy.types.Scene.bl_rna.properties}

C = D.fresh_collection("ASSET_variants")
CWS = ["snow", "graphite", "linen"]


def legend_image(name, fg, bg, letter="Й", px=256):
    """Маленькая текстура надписи (без Pillow): квадрат цвета колпачка с «плашкой» надписи — достаточно для проверки."""
    im = bpy.data.images.new(name, px, px, alpha=False)
    im.colorspace_settings.name = "sRGB"                     # ДО пикселей (06/01 §5)
    fgc = [int(fg[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    bgc = [int(bg[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    pix = []
    for y in range(px):
        for x in range(px):
            on = 0.62 * px < y < 0.84 * px and 0.12 * px < x < 0.40 * px      # «надпись» сверху слева (как кириллица)
            on = on or (0.16 * px < y < 0.26 * px and 0.66 * px < x < 0.86 * px)  # вторая — снизу справа (латиница)
            c = fgc if on else bgc
            pix += [*c, 1.0]
    im.pixels.foreach_set(pix)
    im.filepath_raw = os.path.join(HERE, f"{name}.png")
    im.file_format = "PNG"
    im.save()
    return im


def web_keycap_material(name, cw, role, tex=None):
    col = cw["accent"] if role == "accent" else cw[role]
    mat, bsdf = bpyx.principled(name, base_color=col, roughness=0.58, reuse=False)
    if tex is not None:
        nt = mat.node_tree
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = tex
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "LegendUV"
        nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    mat["kb_variant"] = cw["title"]
    return mat


mats = {}
for cwn in CWS:
    cw = kbp.COLORWAYS[cwn]
    tex = legend_image(f"legend_q_{cwn}", cw["legend1"], cw["alpha"])
    mats[("alpha", cwn)] = web_keycap_material(f"KC_alpha_{cwn}", cw, "alpha", tex)
    mats[("mod", cwn)] = web_keycap_material(f"KC_mod_{cwn}", cw, "mod")
    mats[("accent", cwn)] = web_keycap_material(f"KC_accent_{cwn}", cw, "accent")

sc0 = bpy.data.scenes[0]                                     # аддон читает именно scenes[0], не context.scene
for i, cwn in enumerate(CWS):
    v = sc0.gltf2_KHR_materials_variants_variants.add()
    v.variant_idx = i
    v.name = cwn
objs = []
for kid, role, x in (("yo", "accent", -0.02), ("q", "alpha", 0.0), ("tab", "mod", 0.028)):
    k = next(k for k in kbp.keys() if k["id"] == kid)
    me, info = kbb.keycap_mesh(f"KC_{kid}", k["w"], k["profile"], subd=1, inner=False, stem=False)
    ob = bpy.data.objects.new(f"Key_{kid}", me)
    C.objects.link(ob)
    ob.location = (x, 0, 0)
    me.materials.append(mats[(role, "snow")])               # текущий материал = вариант по умолчанию
    for i, cwn in enumerate(CWS):
        d = me.gltf2_variant_mesh_data.add()
        d.material_slot_index = 0
        d.material = mats[(role, cwn)]
        vv = d.variants.add()
        vv.variant.variant_idx = i
    dm = me.gltf2_variant_default_materials.add()
    dm.material_slot_index = 0
    dm.default_material = mats[(role, "snow")]
    objs.append(ob)

out = os.path.join(HERE, "variants_raw.glb")
r = export(out, "static_hero", collection="ASSET_variants")


def glb_json(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])


j = glb_json(out)
rep = {"blender": bpy.app.version_string, "gltf_io": ".".join(map(str, __import__("io_scene_gltf2").bl_info["version"])),
       "pref_before": before, "pref_after": after, "export": list(r), "bytes": os.path.getsize(out),
       "extensionsUsed": j.get("extensionsUsed"),
       "root_variants": j.get("extensions", {}).get("KHR_materials_variants"),
       "materials": [m["name"] for m in j.get("materials", [])],
       "meshes": [{"name": m["name"], "prim_variants": [p.get("extensions", {}).get("KHR_materials_variants") for p in m["primitives"]],
                   "default_material": [p.get("material") for p in m["primitives"]]} for m in j.get("meshes", [])],
       "images": len(j.get("images", []))}
json.dump(rep, open(os.path.join(HERE, "variants_export_report.json"), "w"), ensure_ascii=False, indent=1)
print("KB_VARIANTS", json.dumps(rep, ensure_ascii=False))

# ---------------------------------------------------------------- вторая сцена: 12 колпачков (≥ 5 примитивов — включается palette)
C2 = D.fresh_collection("ASSET_variants12")
ids = [("yo", "accent"), ("q", "alpha"), ("w", "alpha"), ("e", "alpha"), ("a", "alpha"), ("s", "alpha"), ("d", "alpha"),
       ("tab", "mod"), ("caps", "mod"), ("lshift", "mod"), ("lctrl", "mod"), ("lalt", "mod")]
protos = {}
for kid, role in ids:
    k = next(k for k in kbp.keys() if k["id"] == kid)
    pk = (k["w"], k["profile"], role)
    if pk not in protos:
        me, info = kbb.keycap_mesh(f"KC12_{k['w']}_{k['profile']}_{role}", k["w"], k["profile"], subd=1, inner=False, stem=False)
        me.materials.append(mats[(role, "snow")])
        for i, cwn in enumerate(CWS):
            d = me.gltf2_variant_mesh_data.add()
            d.material_slot_index = 0
            d.material = mats[(role, cwn)]
            d.variants.add().variant.variant_idx = i
        dm = me.gltf2_variant_default_materials.add()
        dm.material_slot_index = 0
        dm.default_material = mats[(role, "snow")]
        protos[pk] = me
    ob = bpy.data.objects.new(f"Key_{kid}", protos[pk])
    C2.objects.link(ob)
    ob.location = (k["cx"], k["cy"], 0.0)
for ob in list(C.all_objects):
    ob.hide_render = True                                     # первая сцена не попадает во второй экспорт (use_renderable)
out2 = os.path.join(HERE, "variants12_raw.glb")
r2 = export(out2, "static_hero", collection="ASSET_variants12")
j2 = glb_json(out2)
print("KB_VARIANTS12", json.dumps({"export": list(r2), "bytes": os.path.getsize(out2), "extensionsUsed": j2.get("extensionsUsed"),
      "variants": j2.get("extensions", {}).get("KHR_materials_variants"), "materials": len(j2.get("materials", [])),
      "meshes": len(j2.get("meshes", [])), "nodes": len(j2.get("nodes", []))}, ensure_ascii=False))
