"""zstudio — свет, фон, пол, дымка, камера и рендер «Звена» (дорожка Z, Blender 5.2.2, Cycles CPU).

Правки KIT §4.4: ключ 30–45° от оси камеры, подъём 30–45°, d = 3–4r, P = π·d²·E; большой софтбокс ради длинной полосы;
контровые ±135° × 1,2–2 от ключа; лампы белые; мир 0–0,15; фон — своя декорация (не мир).
Фон считается через ОБРАТНУЮ кривую Khronos PBR Neutral: у Neutral тёмные тона вычитают min-канал (x − 6,25x² при x < 0,08),
поэтому «#101215 на экране» требует ≈ 0,029 линейного на входе — иначе фон провалится в чёрный.
"""
import math

import bpy
from mathutils import Vector

import bpyx
import d1lib as D
import zmat


# маска HDRI по углу места (sin) для лучей не из камеры: None — как в фазе 1; (0,45; 0,75) — фаза 2 (секвенции)
ENV_MASK = None


# ------------------------------------------------------------------ цвет
def hex_lin(h):
    return tuple(bpyx.color(h)[:3])


def neutral(c):
    """Khronos PBR Neutral (линейный Rec.709 → линейный) — для проверки обратной функции."""
    c = list(c)
    x = min(c)
    off = x - 6.25 * x * x if x < 0.08 else 0.04
    c = [v - off for v in c]
    peak = max(c)
    s = 0.76
    if peak < s:
        return c
    d = 1 - s
    npk = 1 - d * d / (peak + d - s)
    c = [v * npk / peak for v in c]
    g = 1 - 1 / (0.15 * (peak - npk) + 1)
    return [v * (1 - g) + npk * g for v in c]


def inv_neutral(target_lin):
    """Вход сцены, который Neutral превратит в target (для тёмных и средних тонов, peak < 0,76)."""
    t = list(target_lin)
    m_out = min(t)
    m_in = math.sqrt(m_out / 6.25) if m_out < 0.04 else m_out + 0.04
    off = m_in - m_out
    return tuple(v + off for v in t)


def inv_neutral_hex(h, gain=1.0):
    return inv_neutral([v * gain for v in hex_lin(h)])


# ------------------------------------------------------------------ сцена рендера
def render_setup(*, samples=64, res=(1600, 1000), exposure=0.0, denoise=True, transparent=False, adaptive=0.01,
                 clamp=8.0, bounces=None, seed=0):
    sc = bpy.context.scene
    bpyx.set_engine("CYCLES")
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_denoising = denoise
    try:
        cy.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    cy.use_adaptive_sampling = adaptive is not None
    if adaptive is not None:
        cy.adaptive_threshold = adaptive
    cy.sample_clamp_indirect = clamp
    b = dict(max_bounces=12, diffuse_bounces=4, glossy_bounces=8, transmission_bounces=12, volume_bounces=1,
             transparent_max_bounces=16)
    b.update(bounces or {})
    for k, v in b.items():
        setattr(cy, k, v)
    cy.caustics_reflective = False
    cy.blur_glossy = 0.5
    cy.seed = seed
    cy.use_light_tree = True
    r = sc.render
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.film_transparent = transparent
    r.use_persistent_data = True
    ims = r.image_settings
    if getattr(ims, "media_type", "IMAGE") != "IMAGE":
        ims.media_type = "IMAGE"
    ims.file_format = "PNG"; ims.color_mode = "RGBA" if transparent else "RGB"; ims.color_depth = "8"
    bpyx.set_color_management("Khronos PBR Neutral", look="None", exposure=exposure)
    sc.display_settings.display_device = "sRGB"
    return sc


def world(color_hex="#101215", strength=0.05, hdri=None, hdri_strength=0.4, hdri_rot=0.0, desat=True):
    """Мир: тёмный цвет страницы × сила (заливка почти ноль). hdri — только для отражений (камера мир не видит: фон —
    декорация); desat — обесцветить (бренду — нейтральные отражения)."""
    sc = bpy.context.scene
    w = bpy.data.worlds.get("Z_World") or bpy.data.worlds.new("Z_World")
    sc.world = w
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    if hdri:
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
        env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdri, check_existing=True)
        mp.inputs["Rotation"].default_value[2] = math.radians(hdri_rot)
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
        src = env.outputs["Color"]
        if desat:
            hs = nt.nodes.new("ShaderNodeHueSaturation")
            hs.inputs["Saturation"].default_value = 0.0
            nt.links.new(src, hs.inputs["Color"]); src = hs.outputs["Color"]
        nt.links.new(src, bg.inputs["Color"])
        bg.inputs["Strength"].default_value = hdri_strength
    else:
        bg.inputs["Color"].default_value = bpyx.color(color_hex)
        bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    # камера мир не видит (фон — декорация): лучи камеры → прозрачно не нужно; делаем мир невидимым для камеры
    w.cycles_visibility.camera = False if hdri else True
    return w


def stage_collection(name="STAGE"):
    return D.fresh_collection(name)


def light_power(d, E):
    return math.pi * d * d * E


def area(coll, name, pos, target, *, size, size_y=None, power, spread=180.0, color=(1, 1, 1), shape=None,
         visible_camera=False, visible_glossy=True):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.color = color
    if size_y is not None:
        ld.shape = shape or "RECTANGLE"; ld.size = size; ld.size_y = size_y
    else:
        ld.shape = shape or "SQUARE"; ld.size = size
    ld.spread = math.radians(spread)
    lo = bpy.data.objects.new(name, ld)
    coll.objects.link(lo)
    lo.location = pos
    bpyx.look_at(lo, target)
    lo.visible_camera = visible_camera
    lo.visible_glossy = visible_glossy
    return lo


def dir_from(cam_pos, target, az_rel_deg, el_deg):
    """Направление от цели к лампе: азимут относительно направления на камеру (+ — вправо на экране), угол места."""
    v = Vector(cam_pos) - Vector(target)
    az0 = math.atan2(v.y, v.x)
    a = az0 + math.radians(az_rel_deg)
    e = math.radians(el_deg)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def floor(coll, mode="render", size=60.0, z=0.0):
    ob = bpyx.primitive("plane", "Z_Floor", size=size, location=(0, 0, z), collection=coll)
    bpyx.assign_material(ob, zmat.mat("floor", mode))
    return ob


def backdrop(coll, cam_pos, target, *, dist=16.0, size=60.0, glow_at=None, stops=None, name="Z_Backdrop"):
    """Задник-излучатель, перпендикулярный линии взгляда камеры, за объектом на dist м. Радиальный градиент в
    координатах объекта (центр — glow_at, мировая точка на плоскости) — как CSS-фон страницы."""
    v = (Vector(target) - Vector(cam_pos)); v.z = 0; v.normalize()
    c = Vector(target) + v * dist
    c.z = max(c.z, size / 2 - 2.0)
    ob = bpyx.primitive("plane", name, size=size, location=(0, 0, 0), collection=coll)
    ob.rotation_euler = (math.radians(90), 0, math.atan2(v.y, v.x) - math.radians(90))   # нормаль — к камере
    ob.location = c
    bpy.context.view_layer.update()
    if glow_at is not None:                      # сдвиг центра градиента: геометрию двигаем в системе объекта
        g = ob.matrix_world.inverted() @ Vector(glow_at)
        me = ob.data
        for vtx in me.vertices:
            vtx.co.x -= g.x; vtx.co.y -= g.y
        ob.location = ob.matrix_world @ Vector((g.x, g.y, 0))
    m = zmat.backdrop_emission(name + "_M", stops)
    bpyx.assign_material(ob, m)
    ob.visible_shadow = False
    ob.visible_diffuse = True
    return ob


def haze(coll, center, size, density=0.004, anisotropy=0.35, color=(1, 1, 1)):
    """Дымка: куб с однородным объёмом (однородный — Cycles сэмплирует расстояние без шагов)."""
    ob = bpyx.primitive("cube", "Z_Haze", size=1.0, location=center, collection=coll)
    ob.scale = size
    m = bpy.data.materials.get("Z_HazeM") or bpy.data.materials.new("Z_HazeM")
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    bpyx.set_input(vs, "Density", density); bpyx.set_input(vs, "Anisotropy", anisotropy)
    bpyx.set_input(vs, "Color", (*color, 1.0))
    nt.links.new(vs.outputs["Volume"], out.inputs["Volume"])
    ob.data.materials.clear(); ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob


# ------------------------------------------------------------------ камера
def camera_lookat(coll, pos, target, *, lens=None, fov_v_deg=None, shift_x=0.0, shift_y=0.0, name="Z_Cam",
                  dof=None):
    cd = bpy.data.cameras.new(name)
    if fov_v_deg is not None:
        cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24.0
        cd.lens = 12.0 / math.tan(math.radians(fov_v_deg / 2))
    else:
        cd.sensor_fit = "AUTO"; cd.lens = lens or 85.0
    cd.shift_x, cd.shift_y = shift_x, shift_y
    cd.clip_start, cd.clip_end = 0.05, 200.0
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance = dof["dist"]
        cd.dof.aperture_fstop = dof["fstop"]
    cam = bpy.data.objects.new(name, cd)
    coll.objects.link(cam)
    cam.location = pos
    bpyx.look_at(cam, target)
    bpy.context.scene.camera = cam
    return cam


def render(path, *, samples=None):
    sc = bpy.context.scene
    if samples:
        sc.cycles.samples = samples
    sc.render.filepath = path
    import time
    t = time.time()
    r = bpy.ops.render.render(write_still=True)
    if r != {"FINISHED"}:
        raise RuntimeError(f"render {path}: {r}")
    return round(time.time() - t, 1)


def render_masks(path, asset_objs, shell_objs, *, stage_objs):
    """Маски для img_metrics одним кадром Workbench: альфа — объект, R — видимый белый лак. Та же камера и разрешение."""
    sc = bpy.context.scene
    old = (sc.render.engine, sc.render.film_transparent, sc.render.image_settings.color_mode,
           sc.view_settings.view_transform)
    hidden = []
    for o in stage_objs:
        if not o.hide_render:
            o.hide_render = True; hidden.append(o)
    for o in asset_objs:
        o.color = (1, 1, 1, 1) if o in shell_objs else (0, 0, 0, 1)
    bpyx.set_engine("BLENDER_WORKBENCH")
    sh = sc.display.shading
    sh.light = "FLAT"; sh.color_type = "OBJECT"
    sc.display.render_aa = "8"
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    sc.render.engine, sc.render.film_transparent, sc.render.image_settings.color_mode = old[0], old[1], old[2]
    sc.view_settings.view_transform = old[3]
    return path


# ------------------------------------------------------------------ фон = CSS-градиент страницы в экранных координатах
def css_stops(stops_hex, n=9):
    """CSS интерполирует в sRGB: пересчитать стопы [(t, hex)] в n точек (sRGB-lerp → линейный → обратный Neutral)."""
    def h2s(h):
        h = h.lstrip("#"); return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    out = []
    for i in range(n):
        t = i / (n - 1)
        for (t0, a), (t1, b) in zip(stops_hex[:-1], stops_hex[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / max(t1 - t0, 1e-9)
                s = [x + (y - x) * u for x, y in zip(h2s(a), h2s(b))]
                lin = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in s]
                out.append((t, inv_neutral(lin)))
                break
    return out


def page_gradient_group(stops_hex, *, center=(0.7, 0.4), radii=(1.2, 0.9), name="Z_PageGradient"):
    """Группа шейдера: цвет = radial-gradient(радиусы, at center) страницы по Window-координатам (y CSS — сверху)."""
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, "ShaderNodeTree")
    ng.interface.new_socket(name="Color", in_out="OUTPUT", socket_type="NodeSocketColor")
    go = ng.nodes.new("NodeGroupOutput")
    tc = ng.nodes.new("ShaderNodeTexCoord")
    sep = ng.nodes.new("ShaderNodeSeparateXYZ")
    ng.links.new(tc.outputs["Window"], sep.inputs["Vector"])

    def math_node(op, a=None, b=None, va=None, vb=None):
        n = ng.nodes.new("ShaderNodeMath"); n.operation = op
        if a is not None:
            ng.links.new(a, n.inputs[0])
        else:
            n.inputs[0].default_value = va
        if b is not None:
            ng.links.new(b, n.inputs[1])
        elif vb is not None:
            n.inputs[1].default_value = vb
        return n.outputs[0]
    dx = math_node("DIVIDE", math_node("SUBTRACT", sep.outputs["X"], vb=center[0]), vb=radii[0])
    ycss = math_node("SUBTRACT", None, sep.outputs["Y"], va=1.0)
    dy = math_node("DIVIDE", math_node("SUBTRACT", ycss, vb=center[1]), vb=radii[1])
    t = math_node("SQRT", math_node("ADD", math_node("MULTIPLY", dx, dx), math_node("MULTIPLY", dy, dy)))
    ramp = ng.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp; cr.interpolation = "LINEAR"
    st = css_stops(stops_hex)
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = st[0][0]; cr.elements[0].color = (*st[0][1], 1.0)
    for tt, col in st[1:]:
        e = cr.elements.new(tt); e.color = (*col, 1.0)
    ng.links.new(t, ramp.inputs["Factor"])
    # фаза 2: ореол за предметом в экранных координатах (как setGlow/uHalo кода): halo_k · exp(−r²/halo_r²), r — в долях высоты
    # кадра; центр halo_x/halo_y (Window, y вверх) ставит zseq на каждый кадр по проекции предмета; halo_k = 0 — как в фазе 1
    val = {}
    for nm, v in (("halo_x", 0.62), ("halo_y", 0.55), ("halo_r", 0.42), ("halo_k", 0.0), ("aspect", 1.6)):
        n = ng.nodes.new("ShaderNodeValue"); n.name = n.label = nm; n.outputs[0].default_value = v; val[nm] = n.outputs[0]
    hdx = math_node("MULTIPLY", math_node("SUBTRACT", sep.outputs["X"], val["halo_x"]), val["aspect"])
    hdy = math_node("SUBTRACT", sep.outputs["Y"], val["halo_y"])
    r2 = math_node("ADD", math_node("MULTIPLY", hdx, hdx), math_node("MULTIPLY", hdy, hdy))
    g = math_node("EXPONENT", math_node("MULTIPLY", math_node("DIVIDE", r2, math_node("MULTIPLY", val["halo_r"], val["halo_r"])), vb=-1.0))
    gk = math_node("MULTIPLY", g, val["halo_k"])
    hc = ng.nodes.new("ShaderNodeCombineColor")
    for ch, kk in (("Red", 0.021), ("Green", 0.0225), ("Blue", 0.027)):   # холодно-нейтральный ореол (как #1d2026 страницы, ярче)
        ng.links.new(math_node("MULTIPLY", gk, vb=kk), hc.inputs[ch])
    add = ng.nodes.new("ShaderNodeMix"); add.data_type = "RGBA"; add.blend_type = "ADD"
    add.inputs[0].default_value = 1.0
    ng.links.new(ramp.outputs["Color"], bpyx.sock(add, "A")); ng.links.new(hc.outputs["Color"], bpyx.sock(add, "B"))
    ng.links.new(bpyx.sock(add, "Result", out=True), go.inputs["Color"])
    return ng


def set_halo(x, y, r, k, aspect, name="Z_PageGradient"):
    ng = bpy.data.node_groups.get(name)
    if ng is None:
        return
    for nm, v in (("halo_x", x), ("halo_y", y), ("halo_r", r), ("halo_k", k), ("aspect", aspect)):
        ng.nodes[nm].outputs[0].default_value = v


def world_page(stops_hex, *, hdri=None, hdri_strength=0.5, hdri_rot=40.0, **kw):
    """Мир: лучи камеры видят CSS-градиент страницы (Window), остальные — обесцвеченный HDRI только для бликов."""
    sc = bpy.context.scene
    w = bpy.data.worlds.get("Z_World") or bpy.data.worlds.new("Z_World")
    sc.world = w
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    ng = page_gradient_group(stops_hex, **kw)
    grp = nt.nodes.new("ShaderNodeGroup"); grp.node_tree = ng
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(grp.outputs["Color"], bg_cam.inputs["Color"]); bg_cam.inputs["Strength"].default_value = 1.0
    bg_env = nt.nodes.new("ShaderNodeBackground")
    if hdri:
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
        env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdri, check_existing=True)
        mp.inputs["Rotation"].default_value[2] = math.radians(hdri_rot)
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
        hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 0.0
        nt.links.new(env.outputs["Color"], hs.inputs["Color"])
        if ENV_MASK:                                  # фаза 2: ниже угла места HDRI гаснет — глянцевый пол не отражает софтбоксы HDRI
            sepd = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sepd.inputs["Vector"])
            mrk = nt.nodes.new("ShaderNodeMapRange"); mrk.interpolation_type = "SMOOTHSTEP"
            bpyx.set_input(mrk, "From Min", ENV_MASK[0]); bpyx.set_input(mrk, "From Max", ENV_MASK[1])
            nt.links.new(sepd.outputs["Z"], bpyx.sock(mrk, "Value"))
            mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
            bpyx.set_input(mul, "Factor", 1.0)
            nt.links.new(hs.outputs["Color"], bpyx.sock(mul, "A"))
            cv = nt.nodes.new("ShaderNodeCombineColor")
            for ch in ("Red", "Green", "Blue"):
                nt.links.new(bpyx.sock(mrk, "Result", out=True), cv.inputs[ch])
            nt.links.new(cv.outputs["Color"], bpyx.sock(mul, "B"))
            nt.links.new(bpyx.sock(mul, "Result", out=True), bg_env.inputs["Color"])
        else:
            nt.links.new(hs.outputs["Color"], bg_env.inputs["Color"])
    else:
        bg_env.inputs["Color"].default_value = (0, 0, 0, 1)
    bg_env.inputs["Strength"].default_value = hdri_strength
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg_env.outputs["Background"], mix.inputs[1]); nt.links.new(bg_cam.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    w.cycles_visibility.camera = True
    w.cycles_visibility.diffuse = False
    w.cycles_visibility.scatter = False
    return w, ng


def floor_fade(floor_ob, ng, r0=2.8, r1=8.0):
    """Пол растворяется в градиенте страницы: mix(BSDF пола, излучение группы-градиента) по расстоянию от основания."""
    m = floor_ob.active_material
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], cmb.inputs["X"]); nt.links.new(sep.outputs["Y"], cmb.inputs["Y"])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(cmb.outputs["Vector"], ln.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHERSTEP"
    bpyx.set_input(mr, "From Min", r0); bpyx.set_input(mr, "From Max", r1)
    nt.links.new(ln.outputs["Value"], bpyx.sock(mr, "Value"))
    grp = nt.nodes.new("ShaderNodeGroup"); grp.node_tree = ng
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(grp.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(bpyx.sock(mr, "Result", out=True), mix.inputs[0])
    nt.links.new(src, mix.inputs[1]); nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m
