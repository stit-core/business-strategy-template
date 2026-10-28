"""sdano_lib — дорожка SD (15-showcase «Сдано»): паспорт квартиры из SVG-плана l0-sdano, build(P), свет S1–S4, камера,
рендер с альфой, маска объекта и экранные координаты отметок. Blender 5.2.2, только `blender -b` через slot_run.

Единицы: 1 м = 60 ед. SVG (viewBox 0 0 640 470). Мир: X = (x − 40)/60, Y = (430 − y)/60, Z вверх; план «сверху» — как SVG.
Паспорт и расхождения с подписями плана — 15-showcase/sdano/art-direction.md §3.
"""
import json
import math
import os
import sys

R = "/home/mm/Документы/app-design/blender-research"
for p in (f"{R}/03-bpy-api/snippets", f"{R}/99-raw/experiments/D1/_lib"):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

X_OUT = f"{R}/99-raw/experiments/SD"
U = 60.0


def sx(x):
    return (x - 40.0) / U


def sy(y):
    return (430.0 - y) / U


# ====================================================================== паспорт (метры)
P = dict(
    T_out=0.20, T_in=0.12, H_cut=1.10, sill=0.85, floor_t=0.02,
    # стены — осевые линии SVG (x1, y1, x2, y2); w1 продлена до y=260 (на плане висит в проёме d2 — ошибка плана)
    walls_in={
        "w1": (300, 40, 300, 260), "w2": (300, 300, 300, 430), "w3": (40, 260, 130, 260), "w4": (180, 260, 300, 260),
        "w5": (300, 190, 430, 190), "w6": (480, 190, 600, 190), "w7": (430, 300, 600, 300), "w8": (430, 300, 430, 430),
        "w9": (370, 300, 430, 300), "w10": (40, 330, 120, 330),
    },
    # концы внутренних стен, упирающиеся в другую стену: укоротить на полтолщины той стены
    ends={"w1": ("out", "in"), "w2": (None, "out"), "w3": ("out", None), "w4": (None, "ext"), "w5": ("in", None),
          "w6": (None, "out"), "w7": (None, "out"), "w8": ("in", "out"), "w9": (None, None), "w10": ("out", None)},
    # проёмы во внешних стенах: стена, от, до (ед. SVG вдоль стены), вид
    openings_out=[
        ("N", 90, 230, "window"), ("N", 370, 540, "window"), ("E", 230, 280, "window"),
        ("S", 90, 230, "window"), ("S", 470, 560, "window"),
        ("W", 360, 414, "door"),            # вход — добавлен (на плане входной двери нет)
    ],
    # проём кухни в w7 — добавлен (на плане кухня замкнута): x 490..540
    kitchen_door=(490, 540),
    # двери: петля (x, y), закрытое положение → открытое (ед. SVG), только для дуги-«чертежа» на полу и полотна
    doors={
        "d1": dict(hinge=(180, 260), closed=(130, 260), open=(180, 210)),
        "d3": dict(hinge=(480, 190), closed=(430, 190), open=(480, 240)),
        "d4": dict(hinge=(310, 300), closed=(370, 300), open=(310, 360)),
        "d5": dict(hinge=(540, 300), closed=(490, 300), open=(540, 350)),
        "d6": dict(hinge=(40, 414), closed=(40, 360), open=(94, 414)),
    },
    # отметки дефектов — центры кружков SVG; z основания булавки, м
    marks={
        1: dict(svg=(190, 175), z=0.0, what="трещина в стяжке гостиной"),
        2: dict(svg=(160, 62), z=0.0, what="продувает окно: нет пароизоляции шва"),
        3: dict(svg=(235, 225), z=0.0, what="уклон пола 9 мм на 2 м"),
        4: dict(svg=(575, 150), z=0.0, what="розетка без заземления"),
        5: dict(svg=(395, 340), z=0.0, what="течь под раковиной"),
        6: dict(svg=(575, 405), z=None, what="нет тяги в вентиляции кухни"),   # z = верх короба
        7: dict(svg=(455, 262), z=0.0, what="дверь не закрывается"),
    },
    pin_head_z=1.46, pin_head_r=0.12, pin_r=0.014,
    palette={"white": "#e6e4df", "floor": "#d2cdc4", "cut": "#161616", "red": "#cf2419", "ink": "#1c1d20",
             "ink2": "#3d4046", "ceramic": "#eeeeec", "page": "#ffffff"},
    floor_mode="screed",   # screed — тёплый серый пол; paper — пол = лист страницы (ловец теней)
)


# ====================================================================== материалы
MAT = {}


def materials(Pp=P):
    pal = Pp["palette"]
    MAT["white"] = bpyx.principled("SD_White", base_color=pal["white"], roughness=0.88, specular_ior_level=0.35)[0]
    MAT["floor"] = bpyx.principled("SD_Floor", base_color=pal["floor"], roughness=0.92, specular_ior_level=0.3)[0]
    MAT["cut"] = bpyx.principled("SD_Cut", base_color=pal["cut"], roughness=0.7, specular_ior_level=0.3)[0]
    MAT["red"] = bpyx.principled("SD_Red", base_color=pal["red"], roughness=0.42, specular_ior_level=0.5)[0]
    MAT["ink"] = bpyx.principled("SD_Ink", base_color=pal["ink"], roughness=0.45, specular_ior_level=0.4)[0]
    MAT["ink2"] = bpyx.principled("SD_Ink2", base_color=pal["ink2"], roughness=0.8)[0]
    MAT["ceramic"] = bpyx.principled("SD_Ceramic", base_color=pal["ceramic"], roughness=0.3, specular_ior_level=0.5)[0]
    MAT["glass"] = bpyx.principled("SD_GlassLine", base_color="#dde1e4", roughness=0.22, specular_ior_level=0.5)[0]
    return MAT


# ====================================================================== геометрия
def _box(bm, x0, x1, y0, y1, z0, z1, top_mat=1, side_mat=0):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    if x1 - x0 < 1e-5 or y1 - y0 < 1e-5 or z1 - z0 < 1e-5:
        return
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    v = [bm.verts.new(p) for p in c]
    for idx, m in (((0, 3, 2, 1), side_mat), ((4, 5, 6, 7), top_mat), ((0, 1, 5, 4), side_mat), ((1, 2, 6, 5), side_mat),
                   ((2, 3, 7, 6), side_mat), ((3, 0, 4, 7), side_mat)):
        f = bm.faces.new([v[i] for i in idx])
        f.material_index = m


def _obj(bm, name, coll, mats, smooth=None):
    ob = D.obj_from_bm(bm, name, coll, smooth_angle=smooth)
    # без materials.clear(): он обнуляет material_index граней (срез становился белым) — новый меш и так без слотов
    for m in mats:
        ob.data.materials.append(m)
    return ob


def build(Pp=P):
    """Квартира в коллекцию ASSET_sdano: стены со срезом (чёрный верх), окна (подоконник + двойная линия стекла),
    двери (полотно + дуга на полу), пол, сантехника, короб вентиляции, радиаторы, отметки-булавки и признаки дефектов."""
    materials(Pp)
    C = D.fresh_collection("ASSET_sdano")
    T, t, H, S, ft = Pp["T_out"], Pp["T_in"], Pp["H_cut"], Pp["sill"], Pp["floor_t"]
    X1, Y1 = sx(600), sy(40)                     # 9.333 × 6.5 по осям
    z0 = -ft
    wall = bmesh.new()                           # материалы: 0 — белый, 1 — срез (чёрный)
    glass = bmesh.new()
    sills = bmesh.new()

    # ---- внешние стены: N и S на всю длину (+T/2 с концов), E и W между ними
    def outer_segments(side):
        ops = sorted([(a, b, k) for s, a, b, k in Pp["openings_out"] if s == side], key=lambda q: q[0])
        if side in ("N", "S"):
            lo, hi = sx(40) - T / 2, sx(600) + T / 2
            conv = sx
        else:
            lo, hi = sy(430) + T / 2, sy(40) - T / 2
            conv = sy
        cuts = []
        for a, b, k in ops:
            u0, u1 = sorted((conv(a), conv(b)))
            cuts.append((u0, u1, k))
        segs, cur = [], lo
        for u0, u1, k in sorted(cuts):
            segs.append((cur, u0, "solid"))
            segs.append((u0, u1, k))
            cur = u1
        segs.append((cur, hi, "solid"))
        return segs

    for side in ("N", "S", "E", "W"):
        for u0, u1, kind in outer_segments(side):
            if side == "N":
                box = lambda z_0, z_1, tm: _box(wall, u0, u1, Y1 - T / 2, Y1 + T / 2, z_0, z_1, tm)  # noqa: E731
            elif side == "S":
                box = lambda z_0, z_1, tm: _box(wall, u0, u1, -T / 2, T / 2, z_0, z_1, tm)  # noqa: E731
            elif side == "E":
                box = lambda z_0, z_1, tm: _box(wall, X1 - T / 2, X1 + T / 2, u0, u1, z_0, z_1, tm)  # noqa: E731
            else:
                box = lambda z_0, z_1, tm: _box(wall, -T / 2, T / 2, u0, u1, z_0, z_1, tm)  # noqa: E731
            if kind == "solid":
                box(z0, H, 1)
            elif kind == "window":
                box(z0, S, 0)                    # подоконная часть: верх — белый подоконник
                # двойная линия стекла (как на плане) — две тонкие пластины до среза
                for off in (-0.045, 0.045):
                    g = 0.02
                    if side in ("N", "S"):
                        yc = (Y1 if side == "N" else 0.0) + off
                        _box(glass, u0, u1, yc - g / 2, yc + g / 2, S, H, 1, 0)
                    else:
                        xc = (X1 if side == "E" else 0.0) + off
                        _box(glass, xc - g / 2, xc + g / 2, u0, u1, S, H, 1, 0)
                # доска подоконника внутрь комнаты
                sb = 0.06
                if side == "N":
                    _box(sills, u0 - 0.03, u1 + 0.03, Y1 - T / 2 - sb, Y1 - T / 2 + 0.01, S - 0.03, S, 0, 0)
                elif side == "S":
                    _box(sills, u0 - 0.03, u1 + 0.03, T / 2 - 0.01, T / 2 + sb, S - 0.03, S, 0, 0)
                elif side == "E":
                    _box(sills, X1 - T / 2 - sb, X1 - T / 2 + 0.01, u0 - 0.03, u1 + 0.03, S - 0.03, S, 0, 0)
            # door — проём до пола: ничего

    # ---- внутренние перегородки
    kd = Pp.get("kitchen_door")
    for name, (x1_, y1_, x2_, y2_) in Pp["walls_in"].items():
        e0, e1 = Pp["ends"][name]
        if y1_ == y2_:                             # горизонтальная (вдоль X)
            a, b = sorted((sx(x1_), sx(x2_)))
            if e0:
                a += (T if e0 == "out" else t) / 2 * (-1 if e0 == "ext" else 1)
            if e1:
                b -= (T if e1 == "out" else t) / 2 * (-1 if e1 == "ext" else 1)
            yc = sy(y1_)
            spans = [(a, b)]
            if name == "w7" and kd:
                k0, k1 = sx(kd[0]), sx(kd[1])
                spans = [(a, k0), (k1, b)]
            for p0, p1 in spans:
                _box(wall, p0, p1, yc - t / 2, yc + t / 2, z0, H, 1)
        else:                                      # вертикальная (вдоль Y)
            a, b = sorted((sy(y1_), sy(y2_)))       # a — южный конец (больший y SVG)
            s_e0, s_e1 = (e1, e0) if sy(y1_) > sy(y2_) else (e0, e1)
            if s_e0:
                a += (T if s_e0 == "out" else t) / 2 * (-1 if s_e0 == "ext" else 1)
            if s_e1:
                b -= (T if s_e1 == "out" else t) / 2 * (-1 if s_e1 == "ext" else 1)
            xc = sx(x1_)
            _box(wall, xc - t / 2, xc + t / 2, a, b, z0, H, 1)

    walls = _obj(wall, "Walls", C, [MAT["white"], MAT["cut"]])
    _obj(glass, "WindowGlassLines", C, [MAT["glass"], MAT["cut"]])
    _obj(sills, "WindowSills", C, [MAT["white"]])

    # ---- пол
    fl = bmesh.new()
    _box(fl, 0.0, X1, 0.0, Y1, z0, 0.0, 0, 0)
    floor = _obj(fl, "Floor", C, [MAT["floor"] if Pp["floor_mode"] == "screed" else MAT["white"]])
    if Pp["floor_mode"] == "paper":
        floor.hide_render = True

    # ---- двери: полотно (срез по H) и дуга «чертежа» на полу
    leaves = bmesh.new()
    arcs = bmesh.new()
    lw, lt = 0.80, 0.04
    for dn, d in Pp["doors"].items():
        hx, hy = sx(d["hinge"][0]), sy(d["hinge"][1])
        ox, oy = sx(d["open"][0]), sy(d["open"][1])
        cx, cy = sx(d["closed"][0]), sy(d["closed"][1])
        L = math.hypot(ox - hx, oy - hy)
        ux, uy = (ox - hx) / L, (oy - hy) / L
        nx, ny = -uy, ux
        ll = min(lw, L)
        pts = [(hx + nx * lt / 2, hy + ny * lt / 2), (hx + ux * ll + nx * lt / 2, hy + uy * ll + ny * lt / 2),
               (hx + ux * ll - nx * lt / 2, hy + uy * ll - ny * lt / 2), (hx - nx * lt / 2, hy - ny * lt / 2)]
        vb = [leaves.verts.new((x, y, 0.0)) for x, y in pts]
        vt = [leaves.verts.new((x, y, H - 0.005)) for x, y in pts]
        fb = leaves.faces.new(list(reversed(vb)))
        ftp = leaves.faces.new(vt)
        ftp.material_index = 1
        fb.material_index = 0
        for i in range(4):
            j = (i + 1) % 4
            leaves.faces.new((vb[i], vb[j], vt[j], vt[i])).material_index = 0
        # дуга: от закрытого положения к открытому, центр — петля
        a0 = math.atan2(cy - hy, cx - hx)
        a1 = math.atan2(oy - hy, ox - hx)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        rr = ll
        ring = []
        n = 24
        for i in range(n + 1):
            aa = a0 + da * i / n
            ring.append((hx + rr * math.cos(aa), hy + rr * math.sin(aa)))
        w_ = 0.014
        prev = None
        for i in range(n):
            (xa, ya), (xb, yb) = ring[i], ring[i + 1]
            L2 = math.hypot(xb - xa, yb - ya)
            px, py = -(yb - ya) / L2 * w_ / 2, (xb - xa) / L2 * w_ / 2
            q = [arcs.verts.new((xa + px, ya + py, 0.001)), arcs.verts.new((xb + px, yb + py, 0.001)),
                 arcs.verts.new((xb - px, yb - py, 0.001)), arcs.verts.new((xa - px, ya - py, 0.001))]
            arcs.faces.new(q)
            prev = q
    bmesh.ops.recalc_face_normals(leaves, faces=leaves.faces[:])
    _obj(leaves, "DoorLeaves", C, [MAT["white"], MAT["cut"]])
    arcs.normal_update()
    for f in arcs.faces:
        if f.normal.z < 0:
            f.normal_flip()
    _obj(arcs, "DoorArcs", C, [MAT["ink2"]])

    # ---- радиаторы под окнами (белые, 0,5 м, с рёбрами)
    rad = bmesh.new()
    for side, a, b, kind in Pp["openings_out"]:
        if kind != "window":
            continue
        conv = sx if side in ("N", "S") else sy
        u0, u1 = sorted((conv(a), conv(b)))
        cu, wu = (u0 + u1) / 2, max(0.5, (u1 - u0) * 0.62)
        z_a, z_b, dpt = 0.12, 0.62, 0.09
        nfin = max(4, int(wu / 0.1))
        for i in range(nfin):
            f0 = cu - wu / 2 + i * wu / nfin + 0.012
            f1 = f0 + wu / nfin - 0.024
            if side == "N":
                _box(rad, f0, f1, Y1 - T / 2 - 0.04 - dpt, Y1 - T / 2 - 0.04, z_a, z_b, 0, 0)
            elif side == "S":
                _box(rad, f0, f1, T / 2 + 0.04, T / 2 + 0.04 + dpt, z_a, z_b, 0, 0)
            elif side == "E":
                _box(rad, X1 - T / 2 - 0.04 - dpt, X1 - T / 2 - 0.04, f0, f1, z_a, z_b, 0, 0)
    _obj(rad, "Radiators", C, [MAT["white"]])

    # ---- санузел: ванна у южной стены, раковина на восточной стене (у отметки 5)
    bx0, bx1 = sx(300) + t / 2, sx(430) - t / 2          # 4.393 … 6.44
    by0, by1 = T / 2, sy(300) - t / 2                    # 0.1 … 2.107
    tub = D.rounded_slab("Bathtub", 1.70, 0.72, 0.56, 0.12, (0.0, 0.03), C, corner_seg=6, edge_seg=3)
    tub.location = (bx0 + 0.85, by0 + 0.36, 0.0)
    bpyx.assign_material(tub, MAT["ceramic"])
    inner = D.rounded_slab("Bathtub_In", 1.52, 0.56, 0.5, 0.2, (0.08, 0.0), C, corner_seg=6, edge_seg=3)
    inner.location = (bx0 + 0.85, by0 + 0.36, 0.1)
    bpyx.assign_material(inner, MAT["ceramic"])
    D.boolean_apply(tub, inner)
    sink = D.rounded_slab("Sink", 0.46, 0.55, 0.16, 0.12, (0.05, 0.03), C, corner_seg=6, edge_seg=3)
    sink.location = (bx1 - 0.23, sy(340), 0.72)
    bpyx.assign_material(sink, MAT["ceramic"])
    bowl = D.rounded_slab("SinkBowl", 0.32, 0.40, 0.2, 0.1, (0.06, 0.0), C, corner_seg=6, edge_seg=3)
    bowl.location = (bx1 - 0.25, sy(340), 0.76)
    D.boolean_apply(sink, bowl)
    ped = D.rounded_slab("SinkTrap", 0.07, 0.07, 0.72, 0.03, 0.0, C, corner_seg=4)
    ped.location = (bx1 - 0.12, sy(340), 0.0)
    bpyx.assign_material(ped, MAT["ink2"])

    # ---- короб вентиляции в углу кухни (отметка 6)
    duct = bmesh.new()
    kx1, ky0 = X1 - T / 2, T / 2
    _box(duct, kx1 - 0.52, kx1, ky0, ky0 + 0.46, z0, H, 1)
    _obj(duct, "VentDuct", C, [MAT["white"], MAT["cut"]])

    # ---- розетка (отметка 4) на восточной стене спальни, 0,5 м
    outlet = D.rounded_slab("Outlet", 0.085, 0.085, 0.018, 0.012, (0.0, 0.004), C, corner_seg=4, edge_seg=2)
    outlet.data.transform(Matrix.Rotation(math.radians(-90), 4, "Y"))
    outlet.location = (X1 - T / 2 + 0.001, sy(150), 0.5)
    bpyx.assign_material(outlet, MAT["ceramic"])

    marks = build_marks(Pp, C)
    return C, marks


def build_marks(Pp, C):
    """Булавки: основание — место дефекта с плана, головка на общей высоте над срезом (номера — в HTML).
    Плюс признаки: красный круг мелом вокруг трещины (1), лента по шву окна (2), правило 2 м (3), лужа (5)."""
    red, ink = MAT["red"], MAT["ink"]
    heads = {}
    H, zt = Pp["H_cut"], Pp["pin_head_z"]
    for k, m in Pp["marks"].items():
        x, y = sx(m["svg"][0]), sy(m["svg"][1])
        zb = H if m["z"] is None else m["z"]
        needle = bpyx.primitive("cylinder", f"Pin{k}_Needle", radius=Pp["pin_r"], depth=zt - zb, segments=12,
                                location=(x, y, (zt + zb) / 2), collection=C)
        bpyx.assign_material(needle, ink)
        head = bpyx.primitive("uvsphere", f"Pin{k}_Head", radius=Pp["pin_head_r"], segments=32, rings=16,
                              location=(x, y, zt), collection=C)
        bpyx.assign_material(head, red)
        heads[k] = dict(head=(x, y, zt), base=(x, y, zb), what=m["what"])

    # 1 — трещина (тёмная ломаная) + красное кольцо мелом
    x, y = sx(190), sy(175)
    crack = []
    import random
    rng = random.Random(3)
    for i in range(9):
        u = -0.4 + 0.8 * i / 8
        crack.append((x + u * 0.8, y + u * 0.35 + rng.uniform(-0.05, 0.05), 0.002))
    D.sweep("Crack", crack, [(0.0, -0.012), (0.003, -0.012), (0.003, 0.012), (0.0, 0.012)], C, smooth_angle=None)
    bpyx.assign_material(bpy.data.objects["Crack"], MAT["ink2"])
    ring = [(x + 0.55 * math.cos(2 * math.pi * i / 64), y + 0.42 * math.sin(2 * math.pi * i / 64), 0.003) for i in range(64)]
    D.sweep("ChalkRing", ring, [(0.0, -0.022), (0.004, -0.022), (0.004, 0.022), (0.0, 0.022)], C, closed=True,
            smooth_angle=None)
    bpyx.assign_material(bpy.data.objects["ChalkRing"], red)

    # 2 — красная лента по шву окна гостиной (низ рамы на подоконнике)
    tape = bmesh.new()
    Y1 = sy(40)
    _box(tape, sx(90), sx(230), Y1 - 0.09, Y1 - 0.055, Pp["sill"], Pp["sill"] + 0.03, 0, 0)
    _obj(tape, "SeamTape", C, [red])

    # 3 — правило 2 м на полу (чёрный алюминий), вдоль Y
    x3, y3 = sx(235), sy(225)
    rule = D.rounded_slab("LevelRule", 0.1, 2.0, 0.03, 0.01, (0.0, 0.004), C, corner_seg=3, edge_seg=2)
    rule.location = (x3 + 0.18, y3 + 0.85, 0.0)
    bpyx.assign_material(rule, ink)

    # 5 — лужа под раковиной
    x5, y5 = sx(395), sy(340)
    pts = []
    rng = random.Random(5)
    for i in range(40):
        a = 2 * math.pi * i / 40
        rr = 0.26 * (1 + 0.18 * math.sin(3 * a + 0.7) + 0.08 * math.sin(7 * a))
        pts.append((rr * math.cos(a) * 1.25, rr * math.sin(a)))
    pud = D.extrude_outline("Puddle", [pts], 0.004, C, bevel=0.0)
    pud.location = (x5 + 0.1, y5, 0.0)
    bpyx.assign_material(pud, red)
    return heads


# ====================================================================== свет: этюд S1–S4
def _rig_coll():
    return D.fresh_collection("STAGE_LIGHT")


def world_color(hex_, strength):
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = bpyx.color(hex_)
    bg.inputs["Strength"].default_value = strength
    return w


def light_scheme(name, objs, k=1.0):
    """S1 студия · S2 низкое солнце · S3 мягкий свет из окна · S4 пасмурное небо (свод). Азимут — как bpyx
    (0 — с юга, −90 — с запада); камера стоит на −45 (юго-запад). k — общий множитель мощности."""
    L = _rig_coll()
    mn, mx = bpyx.world_bbox(objs)
    c = (mn + mx) / 2
    r = (mx - mn).length / 2

    def pos(az, el, d):
        a, e = math.radians(az), math.radians(el)
        return c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d

    def area(nm, az, el, dist_r, size_r, E, size_y_r=None):
        d = dist_r * r
        lo = bpyx.add_light("AREA", nm, pos(az, el, d), c, energy=math.pi * d * d * E * k, size=size_r * r, collection=L)
        if size_y_r:
            lo.data.shape = "RECTANGLE"
            lo.data.size_y = size_y_r * r
        return lo

    def sun(nm, az, el, S, ang_deg):
        lo = bpyx.add_light("SUN", nm, pos(az, el, 3 * r), c, energy=S * k, size=math.radians(ang_deg), collection=L)
        return lo

    if name == "S1":      # студия: большой софтбокс слева-сверху + заполнение со стороны камеры + мир
        area("Key", -105, 52, 3.0, 1.6, 2.4)
        area("Fill", -15, 28, 3.0, 2.5, 0.55)
        area("Top", -45, 85, 2.5, 2.0, 0.6)
        world_color("#ffffff", 0.12 * k)
    elif name == "S2":    # низкое солнце слева (с северо-запада), длинные тени вправо + небо
        sun("Sun", -128, 21, 3.3, 1.2)
        world_color("#f4f6f8", 0.42 * k)
    elif name == "S3":    # мягкий свет из большого окна: вертикальная панель 12×4 м сзади-слева, низко
        lo = area("Window", -150, 14, 1.9, 1.9, 3.2, size_y_r=0.55)
        area("Bounce", 20, 30, 2.5, 2.0, 0.35)
        world_color("#ffffff", 0.10 * k)
    elif name == "S4":    # пасмурный свод: только мир (белый), без ламп
        world_color("#ffffff", 0.95 * k)
    elif name == "H_SUN":  # hero: солнце 28° с северо-запада (тени короче S2) + светлое небо
        sun("Sun", -128, 28, 3.2, 1.5)
        world_color("#f4f6f8", 0.5 * k)
    elif name == "H_SUN2":  # hero, итерация 2: солнце 32°, небо светлее — тень на листе легче
        sun("Sun", -128, 32, 3.0, 1.5)
        world_color("#f4f6f8", 0.68 * k)
    elif name == "H_ICON":  # иконки серии: свод + высокое солнце 65° (тень короче — предмет крупнее в кадре)
        sun("Sun", -120, 65, 1.7, 3.0)
        world_color("#ffffff", 0.78 * k)
    elif name == "H_SOFT":  # hero: свод + высокое мягкое солнце
        sun("Sun", -120, 52, 1.6, 3.0)
        world_color("#ffffff", 0.75 * k)
    else:
        raise ValueError(name)
    return L


# ====================================================================== камера, рендер, маска, координаты
def shadow_points(objs, az, el, h=1.6):
    """Концы тени верхних углов габарита на земле для солнца (az, el) — чтобы кадр включал тень."""
    mn, mx = bpyx.world_bbox(objs)
    a, e = math.radians(az), math.radians(el)
    dx, dy = -math.sin(a) * math.cos(e) / math.sin(e) * h, math.cos(a) * math.cos(e) / math.sin(e) * h
    return [(x + dx, y + dy, 0.0) for x in (mn.x, mx.x) for y in (mn.y, mx.y)]


def camera_iso(objs, res=(960, 540), margin=1.10, shift=(0.0, 0.0), extra_pts=()):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res[0], res[1], 100
    old = bpy.data.objects.get("SD_Cam")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    mn, mx = bpyx.world_bbox(objs)
    c = (mn + mx) / 2
    a, e = math.radians(-45.0), math.radians(35.264)
    dirv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam = bpyx.add_camera("SD_Cam", location=c + dirv * 40, target=c, lens=50, clip_start=0.1, clip_end=200)
    cam.data.type = "ORTHO"
    frame_ortho(cam, objs, margin=margin, shift=shift, extra_pts=extra_pts)
    return cam


def frame_ortho(cam, objs, margin=1.08, shift=(0.0, 0.0), extra_pts=()):
    """Орто-кадр по проекции всех вершин на оси камеры (camera_fit_coords для ORTHO дал 9,1 м вместо 11,5 — обрезка).
    ortho_scale при sensor_fit AUTO = большая сторона кадра."""
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    Rm = cam.matrix_world.to_3x3()
    right, up, fwd = Rm.col[0].normalized(), Rm.col[1].normalized(), -Rm.col[2].normalized()
    dg = bpy.context.evaluated_depsgraph_get()
    us, vs, ds = [], [], []
    for o in objs:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        mw = o.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            us.append(p.dot(right)); vs.append(p.dot(up)); ds.append(p.dot(fwd))
        oe.to_mesh_clear()
    for p in extra_pts:                          # точки тени на земле: кадр не режет тень
        p = Vector(p)
        us.append(p.dot(right)); vs.append(p.dot(up)); ds.append(p.dot(fwd))
    w, h = max(us) - min(us), max(vs) - min(vs)
    aspect = sc.render.resolution_x / sc.render.resolution_y
    scale = (max(w, h * aspect) if aspect >= 1 else max(w / aspect, h)) * margin
    cu, cv = (max(us) + min(us)) / 2, (max(vs) + min(vs)) / 2
    cam.location = right * cu + up * cv + fwd * (min(ds) - 25.0)
    cam.data.ortho_scale = scale
    cam.data.clip_start, cam.data.clip_end = 0.1, max(ds) - min(ds) + 60.0
    cam.data.shift_x, cam.data.shift_y = shift
    bpy.context.view_layer.update()
    return {"w": w, "h": h, "scale": scale}


def cycles(samples=32, denoise=True):
    sc = bpy.context.scene
    bpyx.set_engine("CYCLES")
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = denoise
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 8
    bpyx.set_color_management("Khronos PBR Neutral", look="None", exposure=0.0)
    sc.render.film_transparent = True


def shadow_catcher(z=-0.02, size=80.0):
    old = bpy.data.objects.get("SD_ShadowCatcher")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    st = bpy.data.collections.get("STAGE") or D.fresh_collection("STAGE")
    pl = bpyx.primitive("plane", "SD_ShadowCatcher", size=size, location=(4.7, 3.2, z), collection=st)
    pl.is_shadow_catcher = True
    return pl


def render(path, res, samples):
    cycles(samples)
    t0 = __import__("time").time()
    r = bpyx.render_still(path, resolution=res, samples=samples, transparent=True)
    r["sec"] = round(__import__("time").time() - t0, 2)
    return r


def render_mask(path, res):
    """Маска объекта: все материалы → белая эмиссия, ловец теней скрыт, 1 сэмпл; альфа = покрытие объекта."""
    sc = bpy.context.scene
    vl = bpy.context.view_layer
    em = bpy.data.materials.get("SD_MaskEmit")
    if em is None:
        em = bpy.data.materials.new("SD_MaskEmit")
        nt = em.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (1, 1, 1, 1)
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(e.outputs["Emission"], o.inputs["Surface"])
    catcher = bpy.data.objects.get("SD_ShadowCatcher")
    if catcher:
        catcher.hide_render = True
    vl.material_override = em
    cycles(1, denoise=False)
    sc.cycles.use_adaptive_sampling = False
    bpyx.render_still(path, resolution=res, samples=1, transparent=True)
    vl.material_override = None
    if catcher:
        catcher.hide_render = False
    return path


def mark_screen(heads, cam):
    sc = bpy.context.scene
    out = {}
    for k, h in heads.items():
        u, v, _ = world_to_camera_view(sc, cam, Vector(h["head"]))
        ub, vb, _ = world_to_camera_view(sc, cam, Vector(h["base"]))
        out[str(k)] = {"head_u": round(u, 5), "head_v": round(1 - v, 5), "base_u": round(ub, 5), "base_v": round(1 - vb, 5),
                       "what": h["what"]}
    return out


ROOMS = {  # подписи плана (как в SVG A) и центр пола комнаты по геометрии, м
    "Гостиная": ("17,8 м²", (2.19, 4.65)), "Спальня": ("13,4 м²", (6.81, 5.23)), "Прихожая": ("7,6 м²", (2.19, 1.2)),
    "Кухня": ("11,2 м²", (7.9, 1.1)), "С/у": ("4,1 м²", (5.3, 1.3)),
}


def room_screen(cam, z=0.0):
    sc = bpy.context.scene
    out = {}
    for nm, (area, (x, y)) in ROOMS.items():
        u, v, _ = world_to_camera_view(sc, cam, Vector((x, y, z)))
        out[nm] = {"area": area, "u": round(u, 5), "v": round(1 - v, 5)}
    return out


def camera_basis(cam):
    Rm = cam.matrix_world.to_3x3()
    return {"right": list(Rm.col[0].normalized()), "up": list(Rm.col[1].normalized()), "loc": list(cam.location),
            "ortho_scale": cam.data.ortho_scale, "res": [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y],
            "shift": [cam.data.shift_x, cam.data.shift_y]}


def asset_objects():
    C = bpy.data.collections["ASSET_sdano"]
    return [o for o in C.all_objects if o.type == "MESH" and not o.hide_render]


def report(C):
    tris = 0
    for o in C.all_objects:
        if o.type == "MESH":
            tris += bpyx.object_stats(o).get("tris", 0)
    mn, mx = bpyx.world_bbox([o for o in C.all_objects if o.type == "MESH"])
    return {"tris": tris, "bbox_min": [round(v, 3) for v in mn], "bbox_max": [round(v, 3) for v in mx],
            "objects": len(C.all_objects)}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
