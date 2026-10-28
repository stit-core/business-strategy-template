# Blender 5.2.2 / glTF-IO 5.2.40 — [проверено] предэкспортная проверка сцены для веба
import bpy
from mathutils import Vector

LOST_NODES = {"TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MAGIC", "TEX_GRADIENT", "TEX_CHECKER", "TEX_BRICK",
              "TEX_WHITE_NOISE", "TEX_GABOR", "LAYER_WEIGHT", "FRESNEL", "BUMP", "VALTORGB", "HUE_SAT",
              "BRIGHTCONTRAST", "GAMMA", "INVERT", "CURVE_RGB", "AMBIENT_OCCLUSION", "SHADERTORGB", "WIREFRAME",
              "BEVEL", "TEX_ENVIRONMENT", "TEX_SKY", "DISPLACEMENT"}
LOST_SHADERS = {"ADD_SHADER", "BSDF_DIFFUSE", "BSDF_GLOSSY", "BSDF_TOON", "BSDF_METALLIC", "BSDF_SHEEN",
                "SUBSURFACE_SCATTERING", "BSDF_TRANSLUCENT"}
BAD_NAME_CHARS = set(" .[]:/")


def _tree_nodes(tree, depth=0):
    """Все ноды дерева материала, включая вложенные группы."""
    out = []
    for n in tree.nodes:
        out.append(n)
        if n.type == "GROUP" and n.node_tree and depth < 8:
            out += _tree_nodes(n.node_tree, depth + 1)
    return out


def _material_issues(mat):
    issues = []
    if not mat.node_tree:
        return issues
    nodes = _tree_nodes(mat.node_tree)
    types = {n.type for n in nodes}
    for t in sorted(types & LOST_NODES):
        issues.append(("WARN", "NODE_LOST", f"нода {t} не экспортируется — запечь (02-baking)"))
    for t in sorted(types & LOST_SHADERS):
        issues.append(("WARN", "SHADER_LOST", f"шейдер {t} → материал без PBR (metal 1 / rough 1)"))
    if "MIX_SHADER" in types and "LIGHT_PATH" not in types:
        issues.append(("WARN", "MIX_SHADER", "Mix Shader → в glTF останется один BSDF"))
    for n in nodes:
        if n.type != "TEX_IMAGE" or not n.image:
            continue
        cs = n.image.colorspace_settings.name
        for link in n.outputs["Color"].links:
            to_node, to_name = link.to_node, link.to_socket.name
            if to_node.type == "BSDF_PRINCIPLED" and to_name in ("Base Color", "Emission Color") and cs != "sRGB":
                issues.append(("WARN", "COLORSPACE", f"{n.image.name}: {cs} на цветовом входе {to_name} (нужен sRGB)"))
            if (to_node.type in ("NORMAL_MAP", "SEPARATE_COLOR") or to_name in ("Roughness", "Metallic")) and cs == "sRGB":
                issues.append(("WARN", "COLORSPACE", f"{n.image.name}: sRGB на данных ({to_node.type}.{to_name}) — нужен Non-Color"))
    return issues


def preflight(scene=None):
    """Список (уровень, код, объект, сообщение). Уровни: ERROR — сломается, WARN — потеряется/исказится, INFO — проверить."""
    sc = scene or bpy.context.scene
    rep = []
    add = lambda lvl, code, ob, msg: rep.append((lvl, code, ob, msg))
    if abs(sc.unit_settings.scale_length - 1.0) > 1e-6:
        add("WARN", "UNIT_SCALE", "scene", f"scale_length {sc.unit_settings.scale_length} игнорируется экспортом (1 BU = 1 м)")
    for ob in sc.objects:
        name = ob.name
        if BAD_NAME_CHARS & set(name):
            add("INFO", "NAME_SANITIZED", name, "three переименует узел (пробел → _, удалит . [ ] : /)")
        if ob.hide_get() or ob.hide_viewport or ob.hide_render:
            add("INFO", "HIDDEN_OBJECT", name, "скрытые объекты экспортируются по умолчанию (use_visible/use_renderable)")
        if ob.type == "LIGHT":
            add("INFO", "LIGHT", name, "свет не экспортируется по умолчанию; при export_lights — режим COMPAT")
            if ob.data.type == "AREA":
                add("WARN", "AREA_LIGHT", name, "Area-свет не экспортируется никогда")
        if ob.type == "FONT" and (ob.data.resolution_u > 4 or ob.data.bevel_resolution > 1):
            add("WARN", "TEXT_DENSE", name, f"resolution_u {ob.data.resolution_u}, bevel_resolution {ob.data.bevel_resolution} → тысячи треуг.")
        if any(abs(s - 1.0) > 1e-4 for s in ob.scale):
            add("INFO", "UNAPPLIED_SCALE", name, f"масштаб {tuple(round(s, 3) for s in ob.scale)} — применить (Ctrl+A)")
        if any(s < 0 for s in ob.scale):
            add("INFO", "NEGATIVE_SCALE", name, "отрицательный масштаб")
        if ob.type != "MESH":
            continue
        me = ob.data
        mods = [m for m in ob.modifiers if m.type != "ARMATURE"]
        if me.shape_keys and mods:
            add("ERROR", "SHAPEKEYS_WITH_MODIFIERS", name, "export_apply=True удалит shape keys молча")
        for m in mods:
            if not m.show_viewport and m.show_render:
                add("WARN", "MOD_VIEWPORT_OFF", name, f"модификатор {m.name} выключен во вьюпорте — export_apply его не применит")
            if m.type == "SUBSURF" and m.levels != m.render_levels:
                add("INFO", "SUBSURF_LEVELS", name, f"экспорт возьмёт levels={m.levels}, а не render_levels={m.render_levels}")
            if m.type == "NODES":
                add("INFO", "GEONODES", name, "нужен export_apply (+ export_gn_mesh/export_gpu_instances для инстансов)")
        if len(me.uv_layers) > 4:
            add("ERROR", "UV_OVER_4", name, f"{len(me.uv_layers)} UV-слоёв: three читает 4, texCoord ≥ 4 ломает шейдер")
        elif len(me.uv_layers) > 2:
            add("WARN", "UV_MANY", name, f"{len(me.uv_layers)} UV-слоёв уходят в файл")
        if len(me.color_attributes) >= 2:
            add("WARN", "MULTI_COLOR_ATTR", name, "≥ 2 цветовых атрибута: export_all_vertex_colors=False (баг белого COLOR_0)")
        if not any(slot.material for slot in ob.material_slots):
            add("INFO", "NO_MATERIAL", name, "в three DefaultMaterial: белый, metalness 1, roughness 1")
        if me.vertices:
            c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8      # центр габарита в координатах объекта
            if c.length > max(max(ob.dimensions), 1e-6):
                add("INFO", "ORIGIN_FAR", name, f"геометрия в {c.length:.2f} BU от origin — pivot в JS будет чужим")
    for mat in bpy.data.materials:
        if mat.users:
            for lvl, code, msg in _material_issues(mat):
                add(lvl, code, f"material:{mat.name}", msg)
    for act in bpy.data.actions:
        if act.use_fake_user and act.users <= 1:
            add("WARN", "FAKE_USER_ACTION", f"action:{act.name}", "действие только с fake user — не экспортируется")
    return rep
