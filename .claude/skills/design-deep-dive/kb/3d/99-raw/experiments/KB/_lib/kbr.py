"""kbr — студия и кадр «Ё» для Cycles (дорожка KB): циклорама, лампа фона, схемы S1–S4, камера (shift_x, ГРИП), маска.

Свет — по правкам KIT §4: лампы белые, P = π·d²·E, d ≈ 3,5r, ключ 30–45° от оси камеры, полосы — под блики фасок корпуса
(азимуты посчитаны зеркалом от камеры к фаске), контровые ±135–150°, мир 0–0,15, фон — своей лампой.
Схема «вращается» вместе с камерой: азимуты ламп заданы относительно азимута камеры (az_cam).
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

R = "/home/mm/Документы/app-design/blender-research"
for p in (f"{R}/99-raw/experiments/D1/_lib", f"{R}/99-raw/experiments/KB/_lib", f"{R}/03-bpy-api/snippets"):
    if p not in sys.path:
        sys.path.insert(0, p)
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

MM = 0.001


def sph(c, az, el, d):
    a, e = math.radians(az), math.radians(el)
    return Vector(c) + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d


def orient(ob, target, xdir=None):
    """−Z объекта (лампы/камеры) — на цель; локальная X — как можно ближе к xdir (длинная сторона полосы)."""
    bpy.context.view_layer.update()
    pos = ob.matrix_world.translation.copy()
    z = (pos - Vector(target)).normalized()
    if xdir is None:
        ob.rotation_euler = (Vector(target) - pos).to_track_quat("-Z", "Y").to_euler()
        return ob
    x = Vector(xdir) - z * Vector(xdir).dot(z)
    if x.length < 1e-6:
        x = Vector((1, 0, 0)) - z * z.x
    x.normalize()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = pos
    ob.matrix_world = m
    return ob


def area(coll, name, pos, target, E, d, size, size_y=None, xdir=None, spread=None, shape="RECTANGLE"):
    """Area-лампа мощностью P = π·d²·E (E — освещённость на оси на расстоянии d, Вт/м²)."""
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape
    ld.size = size
    ld.size_y = size_y or size
    ld.energy = math.pi * d * d * E
    ld.color = (1.0, 1.0, 1.0)
    if spread is not None:
        ld.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, ld)
    coll.objects.link(ob)
    ob.location = pos
    orient(ob, target, xdir)
    return ob


def cyclorama(coll, c, az_cam, color, gap=0.30, rc=0.30, width=5.0, front=4.0, height=2.0, rough=0.92):
    """Бесшовный фон: пол (к камере) → дуга rc → стена, повёрнут лицом к камере; начало дуги — gap за центром объекта."""
    prof = [(-front, 0.0), (0.0, 0.0)]
    for i in range(1, 13):
        t = math.radians(90 * i / 12)
        prof.append((rc * math.sin(t), rc * (1 - math.cos(t))))
    prof.append((rc, height))
    bm = bmesh.new()
    rows = [(bm.verts.new((-width / 2, y, z)), bm.verts.new((width / 2, y, z))) for y, z in prof]
    for a, b in zip(rows[:-1], rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    ob = D.obj_from_bm(bm, "Cyc", coll, smooth_angle=180.0)
    th = math.radians(az_cam)
    back = Vector((-math.sin(th), math.cos(th), 0.0))
    ob.location = Vector((c.x, c.y, 0.0)) + back * gap
    ob.rotation_euler = (0, 0, th)
    mat, bsdf = bpyx.principled("Cyc_mat", base_color=color, roughness=rough, specular_ior_level=0.3, reuse=False)
    bpyx.assign_material(ob, mat)
    return ob


def world(color="#FFFFFF", strength=0.0):
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = bpyx.color(color)
    bg.inputs["Strength"].default_value = strength
    return w


def hero_camera(frame_objs, az, el, lens, margin, shift_x, res, fstop=None, focus=None, shift_y=0.0, name="HeroCam",
                blades=7):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res[0], res[1], 100
    mn, mx = bpyx.world_bbox(frame_objs)
    c = (mn + mx) / 2
    cam = bpyx.add_camera(name, sph(c, az, el, 2.0), c, lens=lens)
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    bpyx.frame_camera(cam, frame_objs, margin=margin)
    cam.data.shift_x = shift_x
    cam.data.shift_y = shift_y
    if fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.aperture_blades = blades
        cam.data.dof.aperture_rotation = math.radians(12)
        if focus is not None:
            cam.data.dof.focus_object = focus
    return cam


def cycles(samples=32, denoise=True, transparent=False, clamp_indirect=6.0):
    sc = bpy.context.scene
    bpyx.set_engine("CYCLES")
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = denoise
    if denoise:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 10
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 6
    sc.cycles.transmission_bounces = 8
    sc.cycles.sample_clamp_indirect = clamp_indirect
    sc.render.film_transparent = transparent
    return sc


def view(name="Khronos PBR Neutral", exposure=0.0):
    bpyx.set_color_management(name, look="None", exposure=exposure)


# ---------------------------------------------------------------------- схемы S1–S4 (r — радиус описанной сферы корпуса)
def rig_S1(coll, c, r, az_cam, page="#D3D8DD", E=1.0, bg_E=1.4):
    """S1 студия: софтбокс-ключ спереди (38° от оси камеры), заливка слева, две полосы под фаски, контровой справа-сзади."""
    d = 3.5 * r
    area(coll, "S1_Key", sph(c, az_cam + 38, 48, d), c, E, d, 2.4 * r, 1.8 * r)
    area(coll, "S1_Fill", sph(c, az_cam - 70, 18, 4 * r), c, E * 0.27, 4 * r, 3 * r)
    area(coll, "S1_StripFront", sph(c, 52, 57, d), c, E * 0.45, d, 5.0 * r, 0.18 * r, xdir=(1, 0, 0))
    area(coll, "S1_StripLeft", sph(c, -146, 25, d), c, E * 1.0, d, 5.0 * r, 0.18 * r, xdir=(0, 1, 0))
    area(coll, "S1_RimR", sph(c, 135, 30, d), c, E * 0.9, d, 1.5 * r)
    cyc = cyclorama(coll, c, az_cam, page)
    bg_lamp(coll, c, az_cam, bg_E, r)
    world("#FFFFFF", 0.03)
    return cyc


def rig_S2(coll, c, r, az_cam, page="#0F1012", E=4.0):
    """S2 низкий ключ: скользящий ключ слева (виден рельеф рядов и выемки), два контровых ×1,7 по силуэту, тёмный фон."""
    d = 3.5 * r
    area(coll, "S2_Key", sph(c, az_cam - 55, 16, d), c, E, d, 1.4 * r, 3.5 * r)
    area(coll, "S2_RimL", sph(c, -150, 22, d), c, E * 1.2, d, 5.0 * r, 0.2 * r, xdir=(0, 1, 0))
    area(coll, "S2_RimR", sph(c, 140, 22, d), c, E * 1.2, d, 5.0 * r, 0.2 * r, xdir=(0, 1, 0))
    area(coll, "S2_Top", sph(c, 180, 62, d), c, E * 0.25, d, 2.5 * r)
    cyc = cyclorama(coll, c, az_cam, page, rough=0.7)
    bg_lamp(coll, c, az_cam, 0.6, r)
    world("#FFFFFF", 0.0)
    return cyc


def rig_S3(coll, c, r, az_cam, wall="#E3D8CB", sun_E=6.0, haze=0.0):
    """S3 атмосфера: низкое солнце справа через переплёт окна (тени рам ложатся на клавиши), стена сзади — не заслоняет;
    тёплый свет и AgX — атмосферный кадр без брендового hex (журнал правил)."""
    az_sun = az_cam + 95
    sd = sph(c, az_sun, 24, 1.0) - c
    sun = bpy.data.lights.new("S3_Sun", "SUN")
    sun.energy = sun_E
    sun.angle = math.radians(0.8)
    sun.color = (1.0, 0.92, 0.82)
    so = bpy.data.objects.new("S3_Sun", sun)
    coll.objects.link(so)
    so.location = c + sd * 2
    orient(so, c)
    ww, wh, bar = 0.80, 0.70, 0.045
    pw, ph = (ww - 3 * bar) / 2, (wh - 3 * bar) / 2
    loops = [D.rrect_pts(ww, wh, 0.001, 1)]
    for i in (0, 1):
        for j in (0, 1):
            cx = -ww / 2 + bar + pw / 2 + i * (pw + bar)
            cy = -wh / 2 + bar + ph / 2 + j * (ph + bar)
            loops.append([(cx + x, cy + y) for x, y in reversed(D.rrect_pts(pw, ph, 0.001, 1))])
    gobo = D.extrude_outline("S3_Window", loops, 0.02, coll, bevel=0.0)
    gobo.location = c + sd * 0.55 + Vector((0.05, 0.02, 0.06))
    orient(gobo, c, xdir=(0, 0, 1))
    gobo.visible_camera = False
    gobo.visible_glossy = False
    gm, _ = bpyx.principled("S3_Window_mat", base_color="#101010", roughness=0.9, reuse=False)
    bpyx.assign_material(gobo, gm)
    area(coll, "S3_Bounce", sph(c, az_cam - 40, 30, 4 * r), c, 0.35, 4 * r, 4 * r)
    cyc = cyclorama(coll, c, az_cam, wall)
    world("#D9D2C8", 0.10)
    if haze > 0:
        vol = bpyx.primitive("cube", "S3_Haze", size=1.0, collection=coll)
        vol.scale = (2.4, 2.4, 1.4)
        vol.location = (c.x, c.y, 0.7)
        vm = bpy.data.materials.new("S3_Haze_mat")
        nt = vm.node_tree
        for n in list(nt.nodes):
            if n.type == "BSDF_PRINCIPLED":
                nt.nodes.remove(n)
        pv = nt.nodes.new("ShaderNodeVolumePrincipled")
        pv.inputs["Density"].default_value = haze
        pv.inputs["Anisotropy"].default_value = 0.45
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        nt.links.new(pv.outputs["Volume"], out.inputs["Volume"])
        bpyx.assign_material(vol, vm)
    return cyc


def rig_S4(coll, c, r, az_cam, page="#EFE2D6", E=1.25, bg_E=1.6):
    """S4 светлая пастельная циклорама: большой верхний софтбокс, низкая заливка-карта, мягкий контровой, фон — лампой."""
    d = 3.5 * r
    area(coll, "S4_Soft", sph(c, az_cam + 25, 62, d), c, E, d, 4.0 * r, 3.0 * r)
    area(coll, "S4_Card", sph(c, az_cam - 80, 10, 4 * r), c, E * 0.3, 4 * r, 4 * r)
    area(coll, "S4_Rim", sph(c, 160, 35, d), c, E * 0.8, d, 2.0 * r)
    area(coll, "S4_StripFront", sph(c, 52, 57, d), c, E * 0.5, d, 5.0 * r, 0.25 * r, xdir=(1, 0, 0))
    cyc = cyclorama(coll, c, az_cam, page)
    bg_lamp(coll, c, az_cam, bg_E, r)
    world(page, 0.1)
    return cyc


def bg_lamp(coll, c, az_cam, E, r):
    """Лампа фона: сверху-сзади на пол за клавиатурой (фон = цвет страницы ± 3 L*), узкий конус — не светит на корпус."""
    th = math.radians(az_cam)
    back = Vector((-math.sin(th), math.cos(th), 0.0))
    tgt = Vector((c.x, c.y, 0.0)) + back * 0.45
    pos = Vector((c.x, c.y, 0.0)) + back * 0.75 + Vector((0, 0, 0.9))
    d = (pos - tgt).length
    return area(coll, "BG_Lamp", pos, tgt, E, d, 1.2, 1.2, spread=55)


RIGS = {"S1": rig_S1, "S2": rig_S2, "S3": rig_S3, "S4": rig_S4}


def render(path, res, samples=32, denoise=True):
    cycles(samples, denoise)
    return bpyx.render_still(path, resolution=res, samples=samples)


def render_mask(path, res, holdout_objs, samples=8):
    """Маска объекта для img_metrics: фон (циклорама) — holdout, прозрачный кадр → альфа = объект (с тем же ГРИП)."""
    sc = bpy.context.scene
    keep = {o.name: o.is_holdout for o in holdout_objs}
    for o in holdout_objs:
        o.is_holdout = True
    hidden = []
    for o in bpy.data.objects:
        if o.name.startswith("S3_Haze") and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    cycles(samples, denoise=False, transparent=True)
    r = bpyx.render_still(path, resolution=res, samples=samples, transparent=True)
    for o in holdout_objs:
        o.is_holdout = keep[o.name]
    for o in hidden:
        o.hide_render = False
    sc.render.film_transparent = False
    return r
