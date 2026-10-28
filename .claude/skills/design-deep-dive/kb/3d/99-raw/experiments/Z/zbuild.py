"""zbuild — идемпотентная сборка «Звена» (дорожка Z): build(P, mode) → коллекция ASSET_zveno[_web] с 8 модулями.

Каждый модуль — пустышка с именем как в scene.js (base, j1, j2, l1, j3, l2, wrist, grip) с точкой вращения в шарнире и
локальными осями = оси three (через C: X = X, Y = −Z, Z = Y); детали — дети с единичной матрицей, их меш уже в системе
модуля. Поза — матрицами как в коде (zkin). Режимы: render (Cycles, детали, процедуры) и web (сегменты ниже, Principled).

    blender -b --python zbuild.py -- [--mode render|web] [--pose work|rest|first] [--explode 0] [--out file.blend]
         [--only j2] [--no-inner] [--cam-az RAD]
"""
import json
import math
import os
import sys
import time

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
for p in (R + "/03-bpy-api/snippets", R + "/99-raw/experiments/D1/_lib", Z + "/lib"):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bpyx  # noqa: E402
import d1lib as D  # noqa: E402
import zgeo as G  # noqa: E402
import zkin as K  # noqa: E402
import zmat as ZM  # noqa: E402
import zpass as ZP  # noqa: E402

DT = ZP.DETAIL
LBL = json.load(open(Z + "/tex/labels.json"))


class Ctx:
    def __init__(self, mode, coll, cam_az_three):
        self.mode = mode
        self.S = ZP.SEG[mode]
        self.coll = coll
        self.cam_az = cam_az_three          # азимут камеры hero в осях three (atan2(x, z)) — куда смотрит печать
        self.roots = {}
        self.parts = {}
        self.shell = []
        self.inner = []

    def m(self, name, **kw):
        return ZM.mat(name, self.mode, **kw)


def prof(spec, seg):
    """Профиль (r, h) со скруглениями; элемент ("G", R, h0) — канавка шва 0,3 мм."""
    pts, rad = [], []
    for it in spec:
        if it[0] == "G":
            _, Rr, h0 = it
            for q in G.groove(h0, Rr, DT["seam_w"], DT["seam_d"], DT["seam_gap"], 0.0008, seg):
                pts.append(q); rad.append(0.0006 if abs(q[0] - Rr) < 1e-9 else 0.0)
        else:
            pts.append((it[0], it[1])); rad.append(it[2] if len(it) > 2 else 0.0)
    return G.fillet(pts, rad, seg)


def root(c, name):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "ARROWS"; e.empty_display_size = 0.15
    c.coll.objects.link(e)
    e["zveno_module"] = name
    c.roots[name] = e
    c.parts[name] = []
    return e


def part(c, mod, ob, mat, *, shell=False, inner=False):
    if ob.name not in c.coll.objects:
        for uc in list(ob.users_collection):
            uc.objects.unlink(ob)
        c.coll.objects.link(ob)
    if mat is not None:
        if ob.data.users > 1:
            if not ob.data.materials:
                ob.data.materials.append(mat)
        else:
            bpyx.assign_material(ob, mat)
    ob.parent = c.roots[mod]
    ob.matrix_parent_inverse = Matrix.Identity(4)
    c.parts[mod].append(ob)
    if shell:
        c.shell.append(ob)
    if inner:
        c.inner.append(ob)
    return ob


def lathe(c, mod, name, spec, mat, *, segs=None, axis=None, sign=1, offset=0.0, closed=False, shell=False, seg=None,
          smooth=35.0):
    rings = prof(spec, seg or c.S["fillet"]) if spec and isinstance(spec[0], tuple) and spec[0][0] != "G" or True else spec
    ob = G.loft_rings(f"{mod}_{name}", rings, segs or c.S["big"], c.coll, closed=closed, smooth_angle=smooth)
    if axis:
        G.to_axis(ob, axis, sign, offset)
    return part(c, mod, ob, mat, shell=shell)


def screws(c, mod, name, Dh, H, mats_local, mat, *, segs=None):
    if c.mode == "webl" and name != "anchor":
        return []
    me = G.screw_mesh(f"{mod}_{name}_me", Dh, H, segs=segs or (36 if c.mode == "render" else 12),
                      socket=c.mode == "render")                 # веб: головка без шестигранника (4 px в кадре — не виден)
    me.materials.append(mat)
    obs = []
    for i, ml in enumerate(mats_local):
        ob = bpy.data.objects.new(f"{mod}_{name}_{i:02d}", me)
        c.coll.objects.link(ob)
        ob.parent = c.roots[mod]
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = ml
        c.parts[mod].append(ob)
        obs.append(ob)
    return obs


def ring(c, mod, name, r_in, Rr, w, *, axis=None, sign=1, offset=0.0):
    rg, led = G.lock_ring(f"{mod}_{name}", r_in, Rr, w, segs=c.S["mid"], ridges=DT["ring_ridges"] if c.mode == "render" else 0,
                          depth=DT["ring_ridge_depth"], led_w=DT["led_w"], seg=3 if c.mode == "render" else 2, coll=c.coll,
                          ridged=c.mode == "render")
    for ob in (rg, led):
        if axis:
            G.to_axis(ob, axis, sign, offset)
        else:
            ob.data.transform(Matrix.Translation((0, 0, offset)))
    part(c, mod, rg, c.m("ring"))
    part(c, mod, led, c.m("led"))
    return rg, led


def seal(c, mod, name, Rr, z, *, minor=None, axis=None, sign=1, offset=0.0):
    ob = G.torus_seal(f"{mod}_{name}", Rr, minor or DT["seal_minor"], segs=c.S["mid"], ring_segs=12 if c.mode == "render" else 6,
                      coll=c.coll)
    ob.data.transform(Matrix.Translation((0, 0, z)))
    if axis:
        G.to_axis(ob, axis, sign, offset)
    return part(c, mod, ob, c.m("rubber"))


def label_angle(c, pose_j1):
    """Угол печати на J1 (локальная система модуля, Blender XY), чтобы в позе hero она смотрела на камеру."""
    a = c.cam_az - pose_j1 - math.radians(12)           # чуть к ключу (слева) — печать на освещённой стороне
    return math.atan2(-math.cos(a), math.sin(a))


def decal_cyl(c, mod, name, lbl, Rr, a, h, width, *, kind="ink"):
    L = LBL[lbl]
    height = width / L["aspect"]
    ob = G.cyl_patch(f"{mod}_{name}", Rr, a, h, width, height, nu=64 if c.mode == "render" else 24, coll=c.coll)
    return part(c, mod, ob, ZM.decal(f"{mod}_{name}", L["path"], c.mode, kind=kind))


def decal_cap(c, mod, name, lbl, x_face, zc, width, *, sign=1):
    L = LBL[lbl]
    ob = G.flat_patch(f"{mod}_{name}", width, width / L["aspect"], coll=c.coll)
    M = Matrix(((0, 0, sign, 0), (sign, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # u → ±Y, v → Z, нормаль → ±X
    ob.data.transform(M)
    ob.data.transform(Matrix.Translation((x_face, 0, zc)))
    return part(c, mod, ob, ZM.decal(f"{mod}_{name}", L["path"], c.mode, kind="etch"))


# ====================================================================== модули
def build_base(c, P):
    s = c.S
    root(c, "base")
    body = lathe(c, "base", "body", [(0.0, 0.0), (0.44, 0.0, 0.002), (0.44, 0.05, 0.004), (0.345, 0.05, 0.012),
                                      (0.3, 0.1, 0.02), ("G", 0.3, 0.2), (0.3, 0.325, 0.006), (0.285, 0.34, 0.003),
                                      (0.0, 0.34)], c.m("graphite"), seg=s["fillet"] + 1)
    # анкерные отверстия: 4 зенковки под болты (π/4 + iπ/2) и 4 пустых отверстия между ними
    cut = []
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        cb = bpyx.primitive("cylinder", f"cut_cb{i}", radius=0.034, depth=0.03, segments=48 if c.mode == "render" else 16,
                            location=(math.cos(a) * 0.37, -math.sin(a) * 0.37, 0.038 + 0.015), collection=c.coll)
        a2 = i * math.pi / 2
        th = bpyx.primitive("cylinder", f"cut_th{i}", radius=0.019, depth=0.1, segments=40 if c.mode == "render" else 14,
                            location=(math.cos(a2) * 0.395, -math.sin(a2) * 0.395, 0.0), collection=c.coll)
        cut += [cb, th]
    rep = D.boolean_apply(body, cut, solver="EXACT", dissolve_deg=0.0, recalc_sharp=35.0)
    # болты анкеров с шайбами
    wm = G.loft_rings("base_washer_me", [(0.017, 0.038), (0.033, 0.038), (0.033, 0.043), (0.017, 0.043)],
                      s["small"], None, closed=True, smooth_angle=40.0)
    mats = []
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        mats.append(Matrix.Translation((math.cos(a) * 0.37, -math.sin(a) * 0.37, 0.0)) @ Matrix.Rotation(i * 0.7, 4, "Z"))
    for i, m in enumerate(mats):
        ob = bpy.data.objects.new(f"base_washer_{i}", wm.data)
        part(c, "base", ob, c.m("steel") if i == 0 else None)
        ob.matrix_basis = m
    if not wm.data.materials:
        wm.data.materials.append(c.m("steel"))
    bpy.data.objects.remove(wm)
    screws(c, "base", "anchor", 0.06, 0.03, [Matrix.Translation((0, 0, 0.043)) @ m for m in mats], c.m("blackox"))
    ring(c, "base", "ring", 0.296, 0.306, 0.04, offset=0.28)
    # кабель питания: сальник на колонне справа-сзади (относительно камеры hero), по полу в темноту
    az = c.cam_az
    v3 = Vector((math.sin(az), 0, math.cos(az)))               # на камеру (three)
    right3 = Vector((v3.z, 0, -v3.x))                           # вправо на экране
    back3 = -v3
    u3 = (right3 * 0.72 + back3 * 0.28).normalized()
    w3 = (back3 - u3 * back3.dot(u3)).normalized()
    u, w = K.t2b(u3), K.t2b(w3)
    up = Vector((0, 0, 1))
    rot = Vector((0, 0, 1)).rotation_difference(u).to_matrix().to_4x4()
    gl = G.loft_rings("base_gland", G.fillet([(0.0, -0.01), (0.036, -0.01), (0.036, 0.012), (0.03, 0.022), (0.0, 0.022)],
                                              [0, 0.002, 0.003, 0.002, 0], 2),
                      12 * 3 if c.mode == "render" else 12, c.coll, smooth_angle=25.0)
    gl.data.transform(Matrix.Translation(u * 0.3 + up * 0.19) @ rot)
    part(c, "base", gl, c.m("graphite"))
    nut = G.loft_rings("base_gland_nut", [(0.03, 0.0), ((lambda th: G.hex_r(th, 0.078)), 0.0),
                                          ((lambda th: G.hex_r(th, 0.078)), 0.014), (0.03, 0.014)],
                       36 if c.mode == "render" else 12, c.coll, closed=True, smooth_angle=25.0)
    nut.data.transform(Matrix.Translation(u * 0.3 + up * 0.19) @ rot @ Matrix.Translation((0, 0, 0.004)))
    part(c, "base", nut, c.m("steel"))
    boot = G.loft_rings("base_gland_boot", G.fillet([(0.0, 0.02), (0.028, 0.02), (0.024, 0.06), (0.019, 0.085), (0.0, 0.085)],
                                                     [0, 0.004, 0.01, 0.003, 0], 3), s["small"], c.coll, smooth_angle=50.0)
    boot.data.transform(Matrix.Translation(u * 0.3 + up * 0.19) @ rot)
    part(c, "base", boot, c.m("rubber"))
    rc = DT["cable_r"]
    ctrl = [u * 0.33 + up * 0.19, u * 0.43 + up * 0.19, u * 0.52 + up * 0.165, u * 0.585 + up * 0.105,
            u * 0.62 + up * 0.045, u * 0.68 + up * (rc - 0.001), u * 0.9 + w * 0.06 + up * (rc - 0.001),
            u * 1.35 + w * 0.22 + up * (rc - 0.001), u * 2.0 + w * 0.5 + up * (rc - 0.001),
            u * 2.7 + w * 0.95 + up * (rc - 0.001), u * 3.3 + w * 1.45 + up * (rc - 0.004),
            u * 3.7 + w * 1.8 + up * (-0.06)]                       # уходит под пол (в темноту), без «шнура до горизонта»
    pts = D.catmull_rom_pts([tuple(p) for p in ctrl], 260 if c.mode == "render" else 80)
    cab = G.sweep_path("base_cable", pts, rc, c.coll, segs=24 if c.mode == "render" else 10)
    part(c, "base", cab, c.m("rubber"))
    return rep


def build_j1(c, P):
    s = c.S
    root(c, "j1")
    lathe(c, "j1", "shell", [(0.0, 0.0), (0.238, 0.0, 0.004), (0.25, 0.012, 0.008), ("G", 0.25, 0.125),
                             (0.25, 0.33, 0.014), (0.232, 0.36, 0.005), (0.0, 0.36)], c.m("shell"), shell=True)
    lathe(c, "j1", "neck", [(0.0, 0.35), (0.2, 0.35, 0.0), (0.2, 0.49), (0.0, 0.49)], c.m("graphite"), segs=s["mid"])
    seal(c, "j1", "seal", 0.2015, 0.3615, minor=0.004)
    ring(c, "j1", "ring", 0.246, 0.2565, 0.035, offset=0.0175)
    a = label_angle(c, P["pose"]["j1"])
    decal_cyl(c, "j1", "print_zveno", "zveno_mark", 0.2504, a, 0.228, 0.29, kind="color")   # знак страницы + «ЗВЕНО»
    decal_cyl(c, "j1", "print_j1", "j1", 0.2504, a - 0.26, 0.088, 0.03)
    decal_cyl(c, "j1", "print_spec", "spec", 0.2504, a, 0.305, 0.15)


def joint(c, mod, *, Rr, half, cap_r, cap_x, ring_spec, seams, lip, lbl, cap_both_labels=False, hollow=False):
    s = c.S
    root(c, mod)
    pd = 0.008
    # hollow (фаза 2, рентген-сечение B): корпус — литая стенка 6 мм с бортами под крышки, а не сплошное тело: в сечении видна
    # стенка, внутри — пустота под начинку (сплошной корпус давал в срезе «заливку» вместо стенки)
    r_in = Rr - 0.006 if hollow else 0.0
    spec = [(r_in, -half + pd), (lip, -half + pd, 0.0), (lip, -half, 0.0008), (Rr, -half, DT["shell_fillet"])]
    spec += [("G", Rr, h) for h in seams]
    spec += [(Rr, half, DT["shell_fillet"]), (lip, half, 0.0008), (lip, half - pd, 0.0), (r_in, half - pd)]
    lathe(c, mod, "shell", spec, c.m("shell"), axis="X", shell=True, closed=hollow)
    for sign in (1, -1):
        cp = G.loft_rings(f"{mod}_cap_{'p' if sign > 0 else 'n'}", G.cap_profile(cap_r, s["fillet"] + 1), s["big"], c.coll,
                          smooth_angle=30.0)
        G.to_axis(cp, "X", sign, sign * cap_x)
        part(c, mod, cp, c.m("cap", axis="X"))
        face = sign * (cap_x + 0.002)
        screws(c, mod, f"capscrew_{'p' if sign > 0 else 'n'}", DT["cap_screw_head_r"] * 2 * cap_r / 0.2,
               DT["cap_screw_h"] * cap_r / 0.2,
               G.circle_mats(0.85 * cap_r, DT["cap_screws"], axis="X", at=face, phase=math.pi / 8, outward=sign), c.m("steel"))
        if lbl and (sign > 0 or cap_both_labels):
            decal_cap(c, mod, f"etch_{'p' if sign > 0 else 'n'}", lbl, sign * (cap_x + 0.0029), 0.58 * cap_r, 0.19 * cap_r,
                      sign=sign)
    rr, x0, w = ring_spec
    ring(c, mod, "ring", Rr - 0.004, rr, w, axis="X", sign=1, offset=x0)


def link(c, mod, *, tube_r, z0, z1, lower, upper, ring_spec, screw_r, screw_z, screw_d, seals):
    s = c.S
    root(c, mod)
    lathe(c, mod, "tube", [(0.0, z0), (tube_r, z0), (tube_r, z1), (0.0, z1)], c.m("alu", axis="Z"), segs=s["big"])
    lathe(c, mod, "collar_lo", lower, c.m("graphite"), segs=s["big"])
    lathe(c, mod, "collar_hi", upper, c.m("graphite"), segs=s["big"])
    screws(c, mod, "flange", screw_d, 0.004 * screw_d / 0.0116,
           G.circle_mats(screw_r, DT["flange_screws"], axis="Z", at=screw_z, phase=math.pi / 8, outward=1), c.m("blackox"))
    for i, (rr, z) in enumerate(seals):
        seal(c, mod, f"seal{i}", rr, z)
    ri, ro, zr, w = ring_spec
    ring(c, mod, "ring", ri, ro, w, offset=zr)


def build_grip(c, P):
    s = c.S
    root(c, "grip")
    lathe(c, "grip", "flange", [(0.0, -0.015), (0.1, -0.015, 0.002), (0.1, 0.005, 0.002), (0.0, 0.005)], c.m("alu", axis="Z"),
          segs=s["mid"])
    screws(c, "grip", "flscrew", 0.0104, 0.004,
           [Matrix.Translation((0.088 * math.cos(math.radians(a)), 0.088 * math.sin(math.radians(a)), 0.0045))
            for a in (60, 120, 240, 300)], c.m("steel"))
    part(c, "grip", G.rbox("grip_palm", 0.26, 0.14, 0.07, 0.022, 0.008, c.coll, seg=s["fillet"] + 2, center=(0, 0, 0.035)),
         c.m("graphite"))
    for sx in (-1, 1):
        part(c, "grip", G.rbox(f"grip_finger_{sx:+d}", 0.034, 0.08, 0.17, 0.008, 0.004, c.coll, seg=s["fillet"] + 1,
                               center=(sx * 0.09, 0, 0.155)), c.m("graphite"))
        part(c, "grip", G.rbox(f"grip_pad_{sx:+d}", 0.012, 0.066, 0.09, 0.004, 0.002, c.coll, seg=s["fillet"],
                               center=(sx * 0.07, 0, 0.19)), c.m("ring"))
        if c.mode == "render":
            for i in range(6):
                part(c, "grip", G.rbox(f"grip_rib_{sx:+d}_{i}", 0.004, 0.058, 0.0045, 0.0015, 0.0012, c.coll, seg=2,
                                       center=(sx * 0.0635, 0, 0.1545 + i * 0.0142)), c.m("ring"))


def build_inner(c):
    """Начинка J3 вдоль X (только рендер): статор с зубцами и медными катушками витками, ротор с магнитами, полый вал,
    волновая передача (жёсткое колесо, гибкое колесо, эллиптический генератор с подшипником), перекрёстный роликовый
    подшипник, диск энкодера с щелями и считывающей головкой, плата с компонентами. Размеры — оболочки кода."""
    mod = "j3"
    S = c.S
    R = c.mode == "render"
    q = 1.0 if R else (0.34 if c.mode == "web" else 0.15)        # плотность тел вращения начинки: веб ≈ ⅓, телефон ≈ ⅕
    segs = 180 if R else int(180 * q)
    nseg = lambda n: max(12, int(n * q) - int(n * q) % 6)  # noqa: E731

    def add(ob, mat):
        part(c, mod, ob, mat, inner=True)
        return ob
    # статор: ярмо r 0.118, зубцы до r 0.075, x 0.02–0.125
    tooth = G.gear_ring_r(18, 0.1, 0.075, sharp=2.6)
    st = G.loft_rings("j3_in_stator", [(tooth, 0.02), (0.118, 0.02), (0.118, 0.125), (tooth, 0.125)], 18 * (20 if R else (6 if c.mode == "web" else 4)), c.coll,
                      closed=True, smooth_angle=30.0)
    G.to_axis(st, "X", 1, 0.0)
    if not R:                                                  # веб: разрез статора по оси (см. keep_below)
        G.keep_below(st)
    add(st, c.m("lamination"))
    # обмотка (фаза 2): медь пазов сплошными брусками + две «лобовые части» с буграми катушек у торцов пакета. Фаза 1 —
    # 18 × 6 витков-петель вокруг зубцов: плоскость скана (через середины пазов, θ 90°/270°) проходила в 6–8 мм от сторон
    # катушек — в сечении меди почти не было. Пазы — на (k + 0,5)·20° профиля статора (зубец — на 0°), в осях модуля
    # направление паза (sin θ, −cos θ) в плоскости YZ (как у G.to_axis «Z → X»).
    for k in range(18):
        th = 2 * math.pi * (k + 0.5) / 18
        if not R and math.cos(th + math.pi) > 0.05:             # веб (гибрид C): мотор срезан по оси — верхних пазов нет
            continue
        bar = G.rbox(f"j3_in_winding_{k:02d}", 0.105, 0.0128, 0.0228, 0.0026, 0.0018, c.coll, seg=2 if R else 1, center=(0, 0, 0))
        bar.data.transform(Matrix.Translation((0.0725, 0, 0)) @ Matrix.Rotation(th + math.pi, 4, "X")
                           @ Matrix.Translation((0, 0, 0.0882)))
        add(bar, c.m("copper"))
    lump = lambda th: 0.1 + 0.0036 * max(0.0, math.cos(18 * th)) ** 2  # noqa: E731  бугры катушек — у зубцов (θ = k·20°)
    # со стороны редуктора лобовая часть тоньше: гибкое колесо кончается на x 0,012, пакет статора начинается с 0,02
    for nm, (z0, z1) in (("endwind_n", (0.0125, 0.0205)), ("endwind_p", (0.1245, 0.1405))):
        ew = G.loft_rings(f"j3_in_{nm}", [(0.0772, z0), (lump, z0), (lump, z1), (0.0772, z1)], 18 * (16 if R else 4), c.coll, closed=True,
                          smooth_angle=40.0)
        G.to_axis(ew, "X", 1, 0.0)
        if not R:
            G.keep_below(ew)
        add(ew, c.m("copper"))
    # ротор и магниты
    ro = G.loft_rings("j3_in_rotor", [(0.03, 0.022), (0.07, 0.022), (0.07, 0.123), (0.03, 0.123)], segs, c.coll, closed=True)
    G.to_axis(ro, "X", 1, 0.0); add(ro, c.m("lamination"))
    for k in range(12):
        th = 2 * math.pi * k / 12
        mg = G.rbox(f"j3_in_mag_{k:02d}", 0.1, 0.02, 0.005, 0.002, 0.001, c.coll, seg=2, center=(0, 0, 0))
        mg.data.transform(Matrix.Translation((0.0725, 0, 0)) @ Matrix.Rotation(th, 4, "X") @ Matrix.Translation((0, 0, 0.0725)))
        add(mg, c.m("magnet"))
    # полый вал
    sh = G.loft_rings("j3_in_shaft", [(0.02, -0.22), (0.028, -0.22), (0.028, 0.22), (0.02, 0.22)], nseg(96), c.coll, closed=True)
    G.to_axis(sh, "X", 1, 0.0); add(sh, c.m("steelb"))
    # генератор волн: эллипс 0.11 × 0.09, подшипник, гибкое колесо с зубьями, жёсткое колесо
    ea_, eb_ = 0.11, 0.09
    ell = lambda th, o=0.0: ea_ * eb_ / math.sqrt((eb_ * math.cos(th)) ** 2 + (ea_ * math.sin(th)) ** 2) + o  # noqa: E731
    wg = G.loft_rings("j3_in_wavegen", [(0.029, -0.019), ((lambda th: ell(th)), -0.019), ((lambda th: ell(th)), 0.009),
                                       (0.029, 0.009)], nseg(240), c.coll, closed=True, smooth_angle=30.0)
    G.to_axis(wg, "X", 1, 0.0); add(wg, c.m("steelb"))
    br = G.loft_rings("j3_in_flexbearing", [((lambda th: ell(th, 0.001)), -0.017), ((lambda th: ell(th, 0.006)), -0.017),
                                           ((lambda th: ell(th, 0.006)), 0.007), ((lambda th: ell(th, 0.001)), 0.007)],
                      nseg(240), c.coll, closed=True, smooth_angle=30.0)
    G.to_axis(br, "X", 1, 0.0); add(br, c.m("steel"))
    teeth = 160
    fl_t = lambda th: ell(th, 0.0075) + 0.003 * max(0.0, math.cos(teeth * th)) ** 0.7  # noqa: E731
    fs = G.loft_rings("j3_in_flexspline", [((lambda th: ell(th, 0.0061)), -0.02), (fl_t, -0.02), (fl_t, 0.012),
                                          ((lambda th: ell(th, 0.0061)), 0.012)], teeth * (6 if R else (2 if c.mode == "web" else 1)), c.coll, closed=True,
                      smooth_angle=50.0)
    G.to_axis(fs, "X", 1, 0.0); add(fs, c.m("steelb"))
    cs_in = lambda th: 0.1215 + 0.0028 * max(0.0, -math.cos((teeth + 2) * th)) ** 0.7  # noqa: E731
    cs = G.loft_rings("j3_in_circspline", [(cs_in, -0.02), (0.155, -0.02), (0.155, 0.03), (cs_in, 0.03)], (teeth + 2) * (6 if R else (2 if c.mode == "web" else 1)),
                      c.coll, closed=True, smooth_angle=50.0)
    G.to_axis(cs, "X", 1, 0.0); add(cs, c.m("lamination"))
    for o in screws(c, mod, "in_csscrew", 0.009, 0.004, G.circle_mats(0.142, 12, axis="X", at=0.03, outward=1), c.m("blackox")):
        c.inner.append(o)
    # перекрёстный роликовый подшипник (выход)
    for nm, (r0, r1) in (("xrb_out", (0.168, 0.182)), ("xrb_in", (0.142, 0.158))):
        b = G.loft_rings(f"j3_in_{nm}", prof([(r0, -0.087), (r1, -0.087, 0.0015), (r1, -0.063, 0.0015), (r0, -0.063)], 2),
                         segs, c.coll, closed=True)
        G.to_axis(b, "X", 1, 0.0); add(b, c.m("steelb"))
    # диск энкодера и головка
    en = G.loft_rings("j3_in_encoder", [(0.03, -0.1155), (0.125, -0.1155), (0.125, -0.1145), (0.03, -0.1145)], segs, c.coll,
                      closed=True)
    G.to_axis(en, "X", 1, 0.0); add(en, c.m("chip"))
    slot = G.rbox("j3_in_slot_me", 0.0016, 0.0018, 0.012, 0.0004, 0.0002, None, seg=1)
    nslot = 128 if R else (64 if c.mode == "web" else 24)
    for k in range(nslot):
        th = 2 * math.pi * k / nslot
        ob = bpy.data.objects.new(f"j3_in_slot_{k:03d}", slot.data)
        add(ob, c.m("encoder") if k == 0 else None)
        ob.matrix_basis = Matrix.Rotation(th, 4, "X") @ Matrix.Translation((-0.115, 0, 0.116))
    if not slot.data.materials:
        slot.data.materials.append(c.m("encoder"))
    bpy.data.objects.remove(slot)
    hd = G.rbox("j3_in_readhead", 0.024, 0.03, 0.026, 0.003, 0.0015, c.coll, seg=2, center=(-0.115, 0, 0.128))
    add(hd, c.m("chip"))
    led = G.rbox("j3_in_readhead_led", 0.004, 0.006, 0.003, 0.001, 0.0005, c.coll, seg=1, center=(-0.1275, 0.006, 0.137))
    add(led, c.m("led", strength=8.0))
    # плата: диск r 0.13 толщ. 4 мм на x −0.13, компоненты на стороне −X
    pcb = G.loft_rings("j3_in_pcb", prof([(0.032, -0.132), (0.13, -0.132, 0.001), (0.13, -0.128, 0.001), (0.032, -0.128)], 2),
                       segs, c.coll, closed=True)
    G.to_axis(pcb, "X", 1, 0.0); add(pcb, c.m("pcb"))
    comp = [("chip", 0.004, 0.034, 0.034, 0.0, 0.07, 0.25), ("chip", 0.003, 0.016, 0.022, 0.06, -0.04, 0.0),
            ("chip", 0.003, 0.016, 0.016, -0.07, -0.02, 0.4), ("chip", 0.0025, 0.012, 0.018, -0.02, -0.085, 0.1),
            ("chip", 0.0025, 0.012, 0.012, 0.085, 0.03, 0.0), ("chip", 0.0025, 0.01, 0.018, 0.035, 0.09, 0.8)]
    for i, (mt, h, a, b, y, z, rot) in enumerate(comp):
        ob = G.rbox(f"j3_in_ic_{i}", a, b, h, 0.0008, 0.0004, c.coll, seg=1)
        ob.data.transform(Matrix.Translation((0, 0, h / 2)))
        ob.data.transform(Matrix.Translation((-0.132, y, z)) @ Matrix.Rotation(math.pi / 2 * -1, 4, "Y") @ Matrix.Rotation(rot, 4, "Z"))
        add(ob, c.m(mt))
    import random
    rnd = random.Random(7)
    capm = G.loft_rings("j3_in_cap_me", [(0.0, 0.0), (0.0045, 0.0), (0.0045, 0.009, ), (0.0, 0.0095)], 24 if R else 8, None,
                        smooth_angle=40.0)
    k = 0
    for i in range(40 if R else (20 if c.mode == "web" else 0)):
        ang = rnd.uniform(0, 2 * math.pi); rad = rnd.uniform(0.045, 0.118)
        y, z = rad * math.cos(ang), rad * math.sin(ang)
        if abs(y) < 0.03 and abs(z - 0.07) < 0.03:
            continue
        if i % 4 == 0 and k < 9:
            ob = bpy.data.objects.new(f"j3_in_capa_{k}", capm.data); k += 1
            add(ob, c.m("alu", axis="Z") if k == 1 else None)
            ob.matrix_basis = Matrix.Translation((-0.132, y, z)) @ Matrix.Rotation(-math.pi / 2, 4, "Y")
        else:
            ob = G.rbox(f"j3_in_smd_{i}", 0.004, 0.002, 0.0012, 0.0003, 0.0002, c.coll, seg=1)
            ob.data.transform(Matrix.Translation((0, 0, 0.0006)))
            ob.data.transform(Matrix.Translation((-0.132, y, z)) @ Matrix.Rotation(-math.pi / 2, 4, "Y") @ Matrix.Rotation(ang, 4, "Z"))
            add(ob, c.m("chip") if i % 3 else c.m("gold"))
    if not capm.data.materials:
        capm.data.materials.append(c.m("alu", axis="Z"))
    bpy.data.objects.remove(capm)


def build(P):
    """P: mode, pose, explode, only, inner, cam_az_three. Идемпотентно: коллекция пересоздаётся."""
    t0 = time.time()
    mode = P.get("mode", "render")
    coll = D.fresh_collection("ASSET_zveno" + ("" if mode == "render" else "_web"))
    c = Ctx(mode, coll, P.get("cam_az_three", 0.62))
    only = P.get("only")
    todo = only or ZP.ORDER
    rep = {}
    if "base" in todo:
        rep["base_bool"] = build_base(c, P)
    if "j1" in todo:
        build_j1(c, P)
    if "j2" in todo:
        joint(c, "j2", Rr=0.235, half=0.23, cap_r=0.2, cap_x=0.246, ring_spec=(0.241, -0.2075, 0.035), seams=(-0.13, 0.13),
              lip=0.204, lbl="j2")
    if "l1" in todo:
        link(c, "l1", tube_r=0.1, z0=0.2, z1=0.98,
             lower=[(0.0, 0.17), (0.145, 0.17, 0.0), (0.145, 0.215, 0.004), (0.118, 0.215, 0.002), (0.106, 0.232, 0.003),
                    (0.1015, 0.24), (0.1015, 0.25), (0.0, 0.25)],
             upper=[(0.0, 0.925), (0.1015, 0.925), (0.1015, 0.935), (0.106, 0.943, 0.003), (0.14, 0.968, 0.008),
                    (0.14, 1.07), (0.0, 1.07)],
             ring_spec=(0.141, 0.151, 0.182, 0.03), screw_r=0.1315, screw_z=0.215, screw_d=0.0116,
             seals=[(0.1015, 0.2515), (0.1015, 0.9235)])
    if "j3" in todo:
        joint(c, "j3", Rr=0.2, half=0.2, cap_r=0.17, cap_x=0.216, ring_spec=(0.206, 0.145, 0.03), seams=(-0.11, 0.11),
              lip=0.174, lbl="j3", hollow=mode == "render")
        if P.get("inner", mode == "render"):
            build_inner(c)
    if "l2" in todo:
        link(c, "l2", tube_r=0.085, z0=0.17, z1=0.79,
             lower=[(0.0, 0.15), (0.125, 0.15, 0.0), (0.125, 0.186, 0.004), (0.1, 0.186, 0.002), (0.09, 0.2, 0.003),
                    (0.0865, 0.205), (0.0865, 0.215), (0.0, 0.215)],
             upper=[(0.0, 0.735), (0.0865, 0.735), (0.0865, 0.745), (0.09, 0.752, 0.003), (0.12, 0.774, 0.008),
                    (0.12, 0.905), (0.0, 0.905)],
             ring_spec=(0.121, 0.131, 0.158, 0.026), screw_r=0.1125, screw_z=0.186, screw_d=0.0096,
             seals=[(0.0865, 0.2165), (0.0865, 0.7345)])
    if "wrist" in todo:
        joint(c, "wrist", Rr=0.14, half=0.14, cap_r=0.12, cap_x=0.156, ring_spec=(0.146, -0.112, 0.024), seams=(), lip=0.124,
              lbl=None)
        lathe(c, "wrist", "cup", [(0.0, 0.12), (0.11, 0.12, 0.0), ("G", 0.11, 0.2), (0.11, 0.27, 0.006), (0.1, 0.285, 0.003),
                                  (0.0, 0.285)], c.m("shell"), segs=c.S["mid"], shell=True)
    if "grip" in todo:
        build_grip(c, P)
    pose = P.get("pose_angles") or ZP.POSES[P.get("pose", "work")] if isinstance(P.get("pose"), str) else P.get("pose")
    apply_pose(c, pose, P.get("explode", 0.0))
    coll["passport"] = json.dumps({"collection": coll.name, "mode": mode, "units": "m (scene.js)", "axes": "three Y-up → Blender Z-up"})
    tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    seen = set()
    for o in coll.all_objects:
        if o.type == "MESH" and o.data.name not in seen:
            seen.add(o.data.name)
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    rep.update({"mode": mode, "modules": list(c.roots), "objects": len(coll.all_objects), "unique_mesh_tris": tris,
                "sec": round(time.time() - t0, 1)})
    return c, rep


def apply_pose(c, pose, explode=0.0):
    Mb = K.module_world_blender(pose, explode)
    for k, e in c.roots.items():
        e.matrix_world = Mb[k]
    bpy.context.view_layer.update()


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(n, d=None):
        return argv[argv.index(n) + 1] if n in argv else d
    bpyx.clear_scene()
    P = {"mode": opt("--mode", "render"), "pose": ZP.POSES[opt("--pose", "work")], "explode": float(opt("--explode", 0)),
         "only": opt("--only").split(",") if opt("--only") else None, "inner": "--no-inner" not in argv,
         "cam_az_three": float(opt("--cam-az", 0.62))}
    c, rep = build(P)
    print("KIN", json.dumps(K.self_test()))
    out = opt("--out", f"{Z}/blend/zveno_{P['mode']}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print("BUILD", json.dumps(rep, ensure_ascii=False, default=str))
