"""sdano_v2 — сцена B/C «Сдано» поверх sdano_lib (sdano_lib не меняется).
Отличия: 4 отметки (пункты «первой страницы акта»), трещина крупнее, белая масштабная фигура инженера (SDF из сфер по
скелету, без лица), лазерный нивелир на штативе и красная линия лазера на стенах гостиной у отметки 3, солнце теплее,
пол темнее стен. Кадр задаётся прямо в экранных осях орто-камеры (u, w в метрах): u = (x − y)/√2, w = (x + y)·0,408 + z·0,816.
"""
import copy
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import sdano_lib as S  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

P2 = copy.deepcopy(S.P)
P2.update(
    marks={k: v for k, v in S.P["marks"].items() if k in (1, 2, 3, 4)},
    pin_head_z=1.52, pin_head_r=0.15, pin_r=0.016,
    palette=dict(S.P["palette"], white="#ebe9e4", floor="#c8c0b3"),
    engineer=dict(pos=(0.52, 3.95), facing=120.0, height=1.72),    # у западной стены гостиной, почти в профиль, смотрит на нивелир
    laser=dict(pos=(3.58, 3.95), h=0.34),                          # штатив у отметки 3, луч на 0,34 м
    crack=dict(len=1.25, width=0.036, ring=(0.82, 0.64), ring_w=0.05),
    puddle=False,
)
SUN_WARM = (1.0, 0.955, 0.9)      # ≈ 5000 K, чуть теплее белого


# ====================================================================== сборка
def build_v2(Pp=P2):
    S.P.update({k: Pp[k] for k in ("palette",)})
    C, _ = S.build(dict(Pp, marks={}))         # квартира без отметок фазы 1
    for nm in ("Crack", "ChalkRing", "SeamTape", "LevelRule", "Puddle"):
        ob = bpy.data.objects.get(nm)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
    heads = pins(Pp, C)
    crack_v2(Pp, C)
    seam_tape(Pp, C)
    level_rule(Pp, C)
    eng = engineer(Pp, C)
    laser_rig(Pp, C)
    return C, heads, eng


def pins(Pp, C):
    red, ink = S.MAT["red"], S.MAT["ink"]
    heads = {}
    for k, m in Pp["marks"].items():
        x, y = S.sx(m["svg"][0]), S.sy(m["svg"][1])
        zb = Pp["H_cut"] if m["z"] is None else m["z"]
        zt = Pp["pin_head_z"]
        n = bpyx.primitive("cylinder", f"Pin{k}_Needle", radius=Pp["pin_r"], depth=zt - zb, segments=12,
                           location=(x, y, (zt + zb) / 2), collection=C)
        bpyx.assign_material(n, ink)
        h = bpyx.primitive("uvsphere", f"Pin{k}_Head", radius=Pp["pin_head_r"], segments=40, rings=20, location=(x, y, zt),
                           collection=C)
        bpyx.assign_material(h, red)
        heads[k] = dict(head=(x, y, zt), base=(x, y, zb), what=m["what"])
    return heads


def crack_v2(Pp, C):
    """Трещина 1,25 м с двумя ответвлениями (тёмная, 3,6 см) и толстое красное кольцо мелом вокруг."""
    import random
    x, y = S.sx(190), S.sy(175)
    cp = Pp["crack"]
    rng = random.Random(11)
    main = []
    n = 14
    for i in range(n):
        u = -0.5 + i / (n - 1)
        main.append((x + u * cp["len"] * 0.92, y + u * cp["len"] * 0.38 + rng.uniform(-0.045, 0.045), 0.002))
    prof = lambda w: [(0.0, -w / 2), (0.004, -w / 2), (0.004, w / 2), (0.0, w / 2)]  # noqa: E731
    D.sweep("Crack", main, prof(cp["width"]), C, smooth_angle=None, scale=lambda t: 0.45 + 0.55 * math.sin(math.pi * t))
    for j, (i0, dx, dy) in enumerate(((5, 0.06, 0.34), (9, 0.30, -0.22))):
        p0 = main[i0]
        br = [(p0[0] + dx * s + rng.uniform(-0.02, 0.02), p0[1] + dy * s + rng.uniform(-0.02, 0.02), 0.002) for s in (0.0, 0.35, 0.7, 1.0)]
        D.sweep(f"CrackBranch{j}", br, prof(cp["width"] * 0.6), C, smooth_angle=None, scale=lambda t: 1.0 - 0.8 * t)
    for nm in ("Crack", "CrackBranch0", "CrackBranch1"):
        bpyx.assign_material(bpy.data.objects[nm], S.MAT["ink"])
    rx, ry = cp["ring"]
    ring = [(x + rx * math.cos(2 * math.pi * i / 80), y + ry * math.sin(2 * math.pi * i / 80), 0.003) for i in range(80)]
    D.sweep("ChalkRing", ring, prof(cp["ring_w"]), C, closed=True, smooth_angle=None)
    bpyx.assign_material(bpy.data.objects["ChalkRing"], S.MAT["red"])


def seam_tape(Pp, C):
    bm = bmesh.new()
    Y1 = S.sy(40)
    S._box(bm, S.sx(90), S.sx(230), Y1 - 0.09, Y1 - 0.055, Pp["sill"], Pp["sill"] + 0.035, 0, 0)
    S._obj(bm, "SeamTape", C, [S.MAT["red"]])


def level_rule(Pp, C):
    x3, y3 = S.sx(235), S.sy(225)
    rule = D.rounded_slab("LevelRule", 0.1, 2.0, 0.03, 0.01, (0.0, 0.004), C, corner_seg=3, edge_seg=2)
    rule.location = (x3 + 0.16, y3 + 0.9, 0.0)
    bpyx.assign_material(rule, S.MAT["ink"])


def _bones(height):
    """Скелет фигуры 1,72 м (свои оси: лицо к +Y): стройнее, голова крупнее — пропорции масштабной фигуры макета."""
    k = height / 1.72
    B = [((0, 0, 0.95), (0, 0, 1.12), 0.12, 0.105), ((0, 0, 1.12), (0, 0.015, 1.30), 0.105, 0.13),
         ((0, 0.015, 1.30), (0, 0.005, 1.40), 0.13, 0.115), ((0, 0.01, 1.45), (0, 0.015, 1.53), 0.05, 0.045),
         ((0, 0.02, 1.605), (0, 0.03, 1.645), 0.098, 0.088)]
    for s in (-1, 1):
        B += [((0, 0, 1.40), (s * 0.17, 0, 1.39), 0.06, 0.055),
              ((s * 0.17, 0, 1.39), (s * 0.2, 0.05, 1.14), 0.048, 0.04),
              ((s * 0.2, 0.05, 1.14), (s * 0.09, 0.24, 1.06), 0.038, 0.032),
              ((s * 0.075, 0, 0.93), (s * 0.085, 0.03, 0.50), 0.085, 0.055),
              ((s * 0.085, 0.03, 0.50), (s * 0.085, -0.01, 0.09), 0.052, 0.038),
              ((s * 0.085, -0.02, 0.055), (s * 0.085, 0.12, 0.04), 0.042, 0.032)]
    balls = []
    for a, b, r0, r1 in B:
        a, b = Vector(a) * k, Vector(b) * k
        L = (b - a).length
        n = max(2, int(L / 0.02) + 1)
        for i in range(n):
            t = i / (n - 1)
            p = a.lerp(b, t)
            balls.append((p.x, p.y, p.z, (r0 + (r1 - r0) * t) * k))
    return balls


def engineer(Pp, C):
    """Белая масштабная фигура (стиль архитектурного макета, без лица): SDF из сфер по скелету + сглаживание поля;
    планшет-акт в руках (чёрный). Смотрит на СВ — к лазерной линии, спиной к камере."""
    e = Pp["engineer"]
    balls = _bones(e["height"])
    fig = D.sdf_blob_gn("Engineer", balls, C, voxel=0.011, fillet_iter=3, smooth_width=1, smooth_iter=1)
    fig.data.shade_smooth()
    bpyx.assign_material(fig, S.MAT["white"])
    kk = e["height"] / 1.72
    tab = D.rounded_slab("Engineer_Tablet", 0.25, 0.18, 0.012, 0.012, (0.0, 0.003), C, corner_seg=4, edge_seg=2)
    tab.rotation_euler = (math.radians(-40), 0, 0)
    tab.location = (0, 0.27 * kk, 1.065 * kk)
    bpyx.assign_material(tab, S.MAT["ink"])
    # каска: купол + козырёк — белая, как фигура (узнаваемость «инженер» без лица)
    dome = D.lathe("Engineer_Helmet", D.catmull_rom_pts([(0.0, 0.0), (0.118, 0.0), (0.114, 0.045), (0.09, 0.095), (0.05, 0.122),
                                                         (0.0, 0.13)], 24), C, segments=40, smooth_angle=60)
    dome.location = (0, 0.02 * kk, 1.64 * kk)
    brim = D.rounded_slab("Engineer_Brim", 0.27, 0.25, 0.012, 0.11, (0.004, 0.004), C, corner_seg=10, edge_seg=2)
    brim.location = (0, 0.045 * kk, 1.632 * kk)
    for o in (dome, brim):
        bpyx.assign_material(o, S.MAT["white"])
    root = bpy.data.objects.new("Engineer_Root", None)
    C.objects.link(root)
    for o in (fig, tab, dome, brim):
        o.parent = root
    # фигура в своих осях смотрит на +Y; поворот на −facing вокруг Z переводит взгляд в (sin f, cos f): 40° — на северо-восток
    root.rotation_euler = (0, 0, math.radians(-e["facing"]))
    root.location = (e["pos"][0], e["pos"][1], 0.0)
    bpy.context.view_layer.update()
    return fig


def laser_rig(Pp, C):
    """Нивелир на штативе у отметки 3 и красная линия лазера на видимых стенах гостиной (северная стена изнутри,
    западная грань w1) и на лицевой стороне радиатора — эмиссия, 2 см."""
    lp, h = Pp["laser"]["pos"], Pp["laser"]["h"]
    ink = S.MAT["ink"]
    parts = []
    for i in range(3):
        a = math.radians(90 + 120 * i)
        foot = Vector((lp[0] + 0.16 * math.cos(a), lp[1] + 0.16 * math.sin(a), 0.0))
        top = Vector((lp[0], lp[1], h - 0.05))
        leg = D.sweep(f"Tripod_Leg{i}", [tuple(foot), tuple(top)], 0.008, C, cap=True, smooth_angle=40)
        bpyx.assign_material(leg, ink)
        parts.append(leg)
    body = D.rounded_slab("Laser_Body", 0.072, 0.062, 0.088, 0.013, (0.004, 0.012), C, corner_seg=6, edge_seg=3)
    body.location = (lp[0], lp[1], h - 0.05)
    body.rotation_euler = (0, 0, math.radians(-45))
    bpyx.assign_material(body, S.MAT["white"])
    win = D.rounded_slab("Laser_Window", 0.05, 0.036, 0.006, 0.008, (0.0, 0.002), C, corner_seg=4, edge_seg=2)
    win.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    win.location = (lp[0] - 0.024, lp[1] - 0.024, h + 0.0)
    win.rotation_euler = (0, 0, math.radians(-45))
    bpyx.assign_material(win, ink)
    # красная линия: эмиссия
    lm = bpy.data.materials.get("SD_Laser") or bpyx.principled("SD_Laser", base_color="#ff2a1a", roughness=0.5,
                                                                  emission_color="#ff2a1a", emission_strength=6.0)[0]
    T, t = Pp["T_out"], Pp["T_in"]
    Y1 = S.sy(40)
    x_w1 = S.sx(300) - t / 2                  # западная грань w1
    y_s = S.sy(260) + t / 2                   # северная грань w4 (южная граница гостиной)
    w_ = 0.02
    bm = bmesh.new()
    S._box(bm, T / 2, x_w1, Y1 - T / 2 - 0.004, Y1 - T / 2 + 0.0005, h - w_ / 2, h + w_ / 2, 0, 0)   # северная стена
    S._box(bm, x_w1 - 0.004, x_w1 + 0.0005, y_s, Y1 - T / 2, h - w_ / 2, h + w_ / 2, 0, 0)            # w1, западная грань
    rad_front = Y1 - T / 2 - 0.04 - 0.09          # лицевая грань радиатора (build: зазор 0,04 + глубина 0,09)
    cu, wu = (S.sx(90) + S.sx(230)) / 2, max(0.5, (S.sx(230) - S.sx(90)) * 0.62)
    S._box(bm, cu - wu / 2, cu + wu / 2, rad_front - 0.004, rad_front + 0.0005, h - w_ / 2, h + w_ / 2, 0, 0)
    line = S._obj(bm, "LaserLine", C, [lm])
    return parts + [body, win, line]


# ====================================================================== свет и кадр
def sun_warm(objs, az=-128, el=32, S_=3.0, ang=1.5, world=("#eef2f6", 0.62)):
    L = D.fresh_collection("STAGE_LIGHT")
    mn, mx = bpyx.world_bbox(objs)
    c = (mn + mx) / 2
    r = (mx - mn).length / 2
    a, e = math.radians(az), math.radians(el)
    loc = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 3 * r
    lo = bpyx.add_light("SUN", "Sun", loc, c, energy=S_, size=math.radians(ang), color_rgb=SUN_WARM, collection=L)
    S.world_color(*world)
    return lo


def camera_uw(u0, u1, w0, w1, res):
    """Орто-камера az −45°, el 35,264°, кадр ровно по прямоугольнику (u, w) в метрах экранных осей."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res[0], res[1], 100
    old = bpy.data.objects.get("SD_Cam")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    right = Vector((1, -1, 0)).normalized()
    fwd = Vector((1, 1, -1)).normalized()
    up = right.cross(fwd).normalized()
    uc, wc = (u0 + u1) / 2, (w0 + w1) / 2
    loc = right * uc + up * wc - fwd * 30.0
    cam = bpyx.add_camera("SD_Cam", location=loc, target=loc + fwd, lens=50, clip_start=0.1, clip_end=80)
    cam.data.type = "ORTHO"
    W, H = u1 - u0, w1 - w0
    cam.data.ortho_scale = max(W, H) if res[0] >= res[1] else max(H, W)
    cam.data.sensor_fit = "AUTO"
    bpy.context.view_layer.update()
    return cam


def uw(p):
    x, y, z = p
    return (x - y) / math.sqrt(2), (x + y) * 0.408248 + z * 0.816497
