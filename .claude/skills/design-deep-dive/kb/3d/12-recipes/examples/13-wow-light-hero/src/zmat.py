"""zmat — материалы «Звена» в двух режимах одного паспорта. Blender 5.2.2.

render — для Cycles: процедурный шум шероховатости, «апельсиновая корка» лака (нормаль Coat), анизотропия (точёные крышки —
радиальные полосы, трубы — вдоль оси), медь, плата, светодиод. web — только Principled + константы и картинки (запекание),
Coat Roughness не меньше 0,05, без анизотропии и процедур (иначе ΔE 12–33 в three).
Сокеты ищутся по имени среди доступных (bpyx.sock), ноды — по типу; hex → линейный через bpyx.color.
"""
import bpy
import bpyx

from zpass import HEX

MAT_CACHE = {}


def _nt(mat):
    nt = mat.node_tree
    p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    return nt, p, out


def _set(p, **kw):
    for k, v in kw.items():
        bpyx.set_input(p, bpyx._principled_key(p, k), v)


def _noise(nt, scale, detail=2.0, rough=0.55, coord="Object", dims="3D"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.noise_dimensions = dims
    bpyx.set_input(nz, "Scale", scale); bpyx.set_input(nz, "Detail", detail); bpyx.set_input(nz, "Roughness", rough)
    bpyx.link_sockets(nt, bpyx.sock(tc, coord, out=True), bpyx.sock(nz, "Vector"))
    return nz


def _map(nt, src, a, b, lo=0.3, hi=0.7):
    mr = nt.nodes.new("ShaderNodeMapRange")
    bpyx.set_input(mr, "From Min", lo); bpyx.set_input(mr, "From Max", hi)
    bpyx.set_input(mr, "To Min", a); bpyx.set_input(mr, "To Max", b)
    bpyx.link_sockets(nt, src, bpyx.sock(mr, "Value"))
    return bpyx.sock(mr, "Result", out=True)


def _rough_noise(nt, p, a, b, scale=6.0, target="Roughness"):
    nz = _noise(nt, scale, 3.0, 0.6)
    bpyx.link_sockets(nt, _map(nt, bpyx.sock(nz, "Factor", out=True), a, b), bpyx.sock(p, target))


def _bump(nt, scale, strength, distance=0.0005, target=None, p=None):
    nz = _noise(nt, scale, 4.0, 0.65)
    bp = nt.nodes.new("ShaderNodeBump")
    bpyx.set_input(bp, "Strength", strength); bpyx.set_input(bp, "Distance", distance)
    bpyx.link_sockets(nt, bpyx.sock(nz, "Factor", out=True), bpyx.sock(bp, "Height"))
    if target:
        bpyx.link_sockets(nt, bpyx.sock(bp, "Normal", out=True), bpyx.sock(p, target))
    return bp


def _tangent(nt, p, axis):
    tg = nt.nodes.new("ShaderNodeTangent")
    tg.direction_type = "RADIAL"; tg.axis = axis
    bpyx.link_sockets(nt, bpyx.sock(tg, "Tangent", out=True), bpyx.sock(p, "Tangent"))


def mat(name, mode, **over):
    """Материал по имени роли и режиму. Кэш по (имя, режим)."""
    key = (name, mode, tuple(sorted(over.items())))
    if key in MAT_CACHE and MAT_CACHE[key].name in bpy.data.materials:
        return MAT_CACHE[key]
    full = f"Z_{name}" + ("" if mode == "render" else "_web") + (("_" + "_".join(f"{k}{v}" for k, v in sorted(over.items()))) if over else "")
    m = bpy.data.materials.get(full)
    if m is not None:
        bpy.data.materials.remove(m)
    m, p = bpyx.principled(full, reuse=False)
    nt, p, out = _nt(m)
    R = mode == "render"
    if name == "shell":                         # белый лак с покрытием
        _set(p, base_color=HEX["shell"], metallic=0.0, roughness=0.34, specular_ior_level=0.5,
             coat_weight=1.0, coat_roughness=0.035 if R else 0.05, coat_ior=1.5)
        if R:
            _rough_noise(nt, p, 0.28, 0.40, 4.0)
            _rough_noise(nt, p, 0.028, 0.05, 2.5, target="Coat Roughness")
            _bump(nt, 320.0, 0.018, 0.0004, "Coat Normal", p)         # «апельсиновая корка» — слабо: при 4 мм/px сильная корка = мерцание
    elif name == "cap":                         # графит: точёный анодированный алюминий
        _set(p, base_color="#7a7f88", metallic=1.0, roughness=0.26 if R else 0.34)
        if R:
            _set(p, anisotropic=0.7, anisotropic_rotation=0.25)
            _tangent(nt, p, over.get("axis", "X"))
            _rough_noise(nt, p, 0.26, 0.36, 9.0)
        else:                                   # фаза 2 (гибрид C): KHR_materials_anisotropy — круговая шлифовка по UV токарного
            _set(p, anisotropic=0.8, anisotropic_rotation=0.0)   # профиля (u — по окружности), как приём texture кода
    elif name == "graphite":                    # литой/порошковая краска
        _set(p, base_color=HEX["graphite"], metallic=0.0, roughness=0.5, specular_ior_level=0.5, coat_weight=0.25,
             coat_roughness=0.25)
        if R:
            _rough_noise(nt, p, 0.42, 0.62, 5.0)
            _bump(nt, 260.0, 0.08, 0.0006, "Normal", p)               # мелкая шагрень порошковой краски
    elif name == "alu":                         # сатиновый алюминий (не хром)
        _set(p, base_color=(0.916, 0.923, 0.924, 1.0), metallic=1.0, roughness=0.3 if R else 0.36)
        if R:
            _set(p, anisotropic=0.6, anisotropic_rotation=0.0)
            _tangent(nt, p, over.get("axis", "Z"))
            # шлифовка вдоль оси: шум, растянутый по Z объекта (штрихи), узкий разброс — сатин, а не «оцинковка»
            tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (1.0, 1.0, 0.012)
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            nz = nt.nodes.new("ShaderNodeTexNoise"); bpyx.set_input(nz, "Scale", 420.0); bpyx.set_input(nz, "Detail", 2.0)
            nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
            bpyx.link_sockets(nt, _map(nt, bpyx.sock(nz, "Factor", out=True), 0.25, 0.33), bpyx.sock(p, "Roughness"))
        else:                                   # веб: шлифовка вдоль трубы (v — вдоль оси): поворот ¼ оборота = π/2, как alu кода
            _set(p, anisotropic=0.35, anisotropic_rotation=0.25)
    elif name == "ring":                        # оранжевый лак кольца-замка
        _set(p, base_color=HEX["accent"], metallic=0.0, roughness=0.36, specular_ior_level=0.5, coat_weight=0.6,
             coat_roughness=0.08 if R else 0.08)
        if R:
            _rough_noise(nt, p, 0.3, 0.42, 7.0)
    elif name == "led":                         # светодиодная полоса кольца: «под питанием»
        _set(p, base_color="#1a0a05", roughness=0.4, emission_color=over.get("color", "#ff5a1f"),
             emission_strength=over.get("strength", 5.0 if R else 2.0))
    elif name == "rubber":
        _set(p, base_color=HEX["rubber"], roughness=0.72, specular_ior_level=0.45, sheen_weight=0.25, sheen_roughness=0.5)
    elif name == "steel":                       # нержавеющий крепёж
        _set(p, base_color=(0.62, 0.62, 0.63, 1.0), metallic=1.0, roughness=0.24)
    elif name == "blackox":                     # воронёный крепёж
        _set(p, base_color=(0.06, 0.06, 0.065, 1.0), metallic=1.0, roughness=0.36)
    elif name == "floor":                       # «чёрный акрил»: мягкое неровное отражение
        _set(p, base_color="#44474c", metallic=0.0, roughness=0.26, specular_ior_level=0.5)   # тёмно-серый: дальний пол = фон страницы при свете пола
        if R:
            _rough_noise(nt, p, 0.12, 0.28, 0.35)          # «чёрный акрил»: отражение мягкое, но читается
    elif name == "copper":                      # эмалированный провод
        _set(p, base_color=(0.955, 0.638, 0.538, 1.0), metallic=1.0, roughness=0.22, coat_weight=0.7,
             coat_roughness=0.06, coat_tint="#ffd9b0")
    elif name == "lamination":
        _set(p, base_color=(0.25, 0.26, 0.28, 1.0), metallic=1.0, roughness=0.42)
    elif name == "steelb":
        _set(p, base_color=(0.72, 0.72, 0.73, 1.0), metallic=1.0, roughness=0.16)
    elif name == "magnet":
        _set(p, base_color=(0.5, 0.5, 0.52, 1.0), metallic=1.0, roughness=0.3)
    elif name == "pcb":
        _set(p, base_color=HEX["pcb"], roughness=0.45, coat_weight=0.8, coat_roughness=0.12)
    elif name == "gold":
        _set(p, base_color=(1.0, 0.77, 0.34, 1.0), metallic=1.0, roughness=0.22)
    elif name == "chip":
        _set(p, base_color="#121314", roughness=0.55, specular_ior_level=0.4)
    elif name == "encoder":
        _set(p, base_color=(0.85, 0.85, 0.86, 1.0), metallic=1.0, roughness=0.1)
    elif name == "mask_white":                  # маска для img_metrics (Workbench/emission)
        nt.nodes.remove(p)
        em = nt.nodes.new("ShaderNodeEmission")
        bpyx.set_input(em, "Color", (1, 1, 1, 1)); bpyx.set_input(em, "Strength", 1.0)
        bpyx.link_sockets(nt, bpyx.sock(em, "Emission", out=True), out.inputs["Surface"])
    else:
        raise KeyError(name)
    MAT_CACHE[key] = m
    return m


def decal(name, image_path, mode, *, kind="ink"):
    """Печать под лаком (ink) или лазерная гравировка на графите (etch): картинка-маска (альфа) → прозрачно/краска.
    web: alpha через Math «больше чем» 0,5 → экспорт alphaMode MASK."""
    full = f"Z_decal_{name}" + ("" if mode == "render" else "_web")
    m = bpy.data.materials.get(full)
    if m is not None:
        bpy.data.materials.remove(m)
    m, p = bpyx.principled(full, reuse=False)
    nt, p, out = _nt(m)
    img = bpy.data.images.load(image_path, check_existing=True)
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.extension = "CLIP"; tex.interpolation = "Cubic"
    if kind == "color":                       # двухцветная печать (знак в акценте + буквы): цвет из картинки
        tex.image.colorspace_settings.name = "sRGB"
        bpyx.link_sockets(nt, bpyx.sock(tex, "Color", out=True), bpyx.sock(p, "Base Color"))
        _set(p, roughness=0.55, specular_ior_level=0.35)
    elif kind == "ink":
        # печать тампоном ПОВЕРХ лака (без покрытия): под лаком зеркальная полоса смывала стойку «В» — «ЗВЕНО» читалось «ЗЗЕНО»
        _set(p, base_color=HEX["ink"], roughness=0.55, specular_ior_level=0.35)
    else:
        _set(p, base_color=HEX["etch"], metallic=0.35, roughness=0.62)
    a = bpyx.sock(tex, "Alpha", out=True)
    if mode == "web":
        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"
        bpyx.link_sockets(nt, a, gt.inputs[0]); gt.inputs[1].default_value = 0.5
        a = gt.outputs[0]
    bpyx.link_sockets(nt, a, bpyx.sock(p, "Alpha"))
    try:
        m.surface_render_method = "DITHERED"
    except (AttributeError, TypeError):
        pass
    return m


def backdrop_emission(name, stops):
    """Задник-излучатель: радиальный градиент по Object-координатам плоскости (центр 0,0), stops — [(t, (r, g, b)) линейные
    значения ДО Neutral]; результат рассчитан обратной кривой Neutral (zstudio.inv_neutral)."""
    m = bpy.data.materials.get(name)
    if m is not None:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "LENGTH"
    bpyx.link_sockets(nt, bpyx.sock(tc, "Object", out=True), vm.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1.0)
    for t, c in stops[1:]:
        e = cr.elements.new(t); e.color = (*c, 1.0)
    bpyx.link_sockets(nt, bpyx.sock(vm, "Value", out=True), bpyx.sock(ramp, "Factor"))
    em = nt.nodes.new("ShaderNodeEmission")
    bpyx.link_sockets(nt, bpyx.sock(ramp, "Color", out=True), bpyx.sock(em, "Color"))
    bpyx.set_input(em, "Strength", 1.0)
    bpyx.link_sockets(nt, bpyx.sock(em, "Emission", out=True), out.inputs["Surface"])
    for owner in (m, getattr(m, "cycles", None)):          # большой тусклый излучатель не сэмплировать как лампу (шум)
        if owner is not None and "emission_sampling" in owner.bl_rna.properties:
            owner.emission_sampling = "NONE"
    return m
