"""zgeo — геометрия «Звена» кодом (bmesh, без операторов в цикле). Дорожка Z, Blender 5.2.2.

Тела вращения — кольцами профиля (r, h) вокруг локальной Z (h = z), с радиусом-функцией угла (рифление, шестигранник,
зубья); затем поворот оси Z → ±X для суставов. Профили — ломаная со скруглениями (d1lib.fillet_polyline). Шов — канавка в
профиле (0,3 мм на дне). Крепёж — винт с внутренним шестигранником (DIN 912 по пропорциям). Всё в метрах scene.js.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import d1lib as D

TAU = 2 * math.pi


# ------------------------------------------------------------------ кольца профиля
def loft_rings(name, rings, segs, coll=None, *, closed=False, smooth_angle=35.0, uv=True, phase=0.0):
    """rings: [(r, z)], r — число или функция угла θ → радиус; r ≤ 1e-9 — полюс на оси. closed — профиль замкнут (кольцо,
    трубка со стенкой). Грани: квады между кольцами; UV: u — угол, v — длина профиля."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap") if uv else None
    vrings = []
    for r, z in rings:
        if not callable(r) and r <= 1e-9:
            vrings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        vs = []
        for k in range(segs):
            th = phase + TAU * k / segs
            rr = r(th) if callable(r) else r
            vs.append(bm.verts.new((rr * math.cos(th), rr * math.sin(th), z)))
        vrings.append(vs)
    L = [0.0]
    for j in range(len(rings) - 1):
        r0 = rings[j][0] if not callable(rings[j][0]) else rings[j][0](0.0)
        r1 = rings[j + 1][0] if not callable(rings[j + 1][0]) else rings[j + 1][0](0.0)
        L.append(L[-1] + math.hypot(r1 - r0, rings[j + 1][1] - rings[j][1]))
    pairs = list(range(len(vrings) - 1)) + ([len(vrings) - 1] if closed else [])
    tot = max(L[-1], 1e-9)
    for j in pairs:
        a, b = vrings[j], vrings[(j + 1) % len(vrings)]
        v0 = L[j] / tot
        v1 = (L[j + 1] / tot) if j + 1 < len(L) else 1.0
        for k in range(segs):
            k2 = (k + 1) % segs
            u0, u1 = k / segs, (k + 1) / segs
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                f = bm.faces.new((a[0], b[k], b[k2])); uvs = ((u0, v0), (u0, v1), (u1, v1))
            elif len(b) == 1:
                f = bm.faces.new((a[k], a[k2], b[0])); uvs = ((u0, v0), (u1, v0), (u0, v1))
            else:
                f = bm.faces.new((a[k], a[k2], b[k2], b[k])); uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
            if uvl is not None:
                for lp, uvv in zip(f.loops, uvs):
                    lp[uvl].uv = uvv
    # совпавшие кольца (скругления соседних углов сходятся в точку) → двойные вершины и вырожденные грани (scene_check)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1.5e-5)     # 0,015 мм — на порядок мельче шва 0,3 мм
    bmesh.ops.dissolve_degenerate(bm, dist=1.5e-5, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return D.obj_from_bm(bm, name, coll, smooth_angle=smooth_angle)


def fillet(pts, radii, seg):
    return D.fillet_polyline(pts, radii, seg)


def to_axis(ob, axis="X", sign=1, offset=0.0):
    """Ось вращения тела Z → ±X (или ±Y), затем сдвиг вдоль новой оси."""
    if axis == "X":
        ob.data.transform(Matrix.Rotation(math.radians(90 * sign), 4, "Y"))
        ob.data.transform(Matrix.Translation((offset, 0, 0)))
    elif axis == "Y":
        ob.data.transform(Matrix.Rotation(math.radians(-90 * sign), 4, "X"))
        ob.data.transform(Matrix.Translation((0, offset, 0)))
    else:
        if sign < 0:
            ob.data.transform(Matrix.Scale(-1, 4, (0, 0, 1)))
            _flip(ob)
        ob.data.transform(Matrix.Translation((0, 0, offset)))
    ob.data.update()
    return ob


def _flip(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()


def groove(h0, R, w, d, gap, rf, seg):
    """Точки канавки шва (r, h) на цилиндре радиуса R вокруг h0 (порядок по возрастанию h)."""
    pts = [(R, h0 - w / 2 - rf), (R, h0 - w / 2), (R - d, h0 - gap / 2), (R - d, h0 + gap / 2), (R, h0 + w / 2),
           (R, h0 + w / 2 + rf)]
    return pts


def shell_profile(R, h0, h1, *, end_fillet, seams=(), seam=None, pocket=None, seg=4, close_ends=True):
    """Профиль (r, h) корпуса-цилиндра радиуса R от h0 до h1: торцы со скруглением end_fillet, канавки швов в seams,
    pocket=(r_lip, depth) — карман под крышку на обоих торцах (крышка садится с зазором-швом)."""
    s = seam or {}
    pts, rad = [], []

    def add(p, r=0.0):
        pts.append(p); rad.append(r)
    if close_ends:
        if pocket:
            add((0.0, h0 + pocket[1])); add((pocket[0], h0 + pocket[1])); add((pocket[0], h0), 0.0008)
        else:
            add((0.0, h0))
        add((R, h0), end_fillet)
    for hs in sorted(seams):
        for p in groove(hs, R, s.get("w", 0.0028), s.get("d", 0.0016), s.get("gap", 0.0003), 0.0008, seg):
            add(p, 0.0006 if abs(p[0] - R) < 1e-9 else 0.0)
    if close_ends:
        add((R, h1), end_fillet)
        if pocket:
            add((pocket[0], h1), 0.0008); add((pocket[0], h1 - pocket[1])); add((0.0, h1 - pocket[1]))
        else:
            add((0.0, h1))
    return fillet(pts, rad, seg)


def cap_profile(r, seg=4, back=-0.025):
    """Точёная крышка (профиль кода capX + скругления): борт, фаска, поле под винты (0,8–0,9 r), V-канавка на 0,78 r, плато,
    пологий купол. h от задней грани (back) к лицу (+0,012)."""
    pts = [(0.0, back), (r, back), (r, -0.012), (0.96 * r, -0.003), (0.9 * r, 0.002), (0.8 * r, 0.002),
           (0.785 * r, 0.0005), (0.78 * r, -0.0012), (0.775 * r, 0.0005), (0.76 * r, 0.002), (0.42 * r, 0.003),
           (0.3 * r, 0.0075), (0.15 * r, 0.0105), (0.0, 0.0115)]
    rad = [0, 0.0015, 0.004, 0.003, 0.002, 0.0006, 0.0003, 0.0, 0.0003, 0.0006, 0.004, 0.006, 0.004, 0]
    return fillet(pts, rad, seg)


# ------------------------------------------------------------------ крепёж
def hex_r(th, s):
    """Радиус шестигранника с размером под ключ s (углы на 0°, 60°, …)."""
    a = (th % (math.pi / 3)) - math.pi / 6
    return (s / 2) / math.cos(a)


def screw_mesh(name, Dh, H, *, segs=24, socket=True, fil=None):
    """Винт с цилиндрической головкой и внутренним шестигранником (DIN 912: s ≈ 0,47 D, глубина ≈ 0,6 H). Низ головки —
    z = 0, ось Z. Возвращает меш (для связанных копий)."""
    R = Dh / 2
    f = fil if fil is not None else 0.1 * Dh
    s = 0.47 * Dh
    rings = [(0.0, -0.25 * H), (R * 0.98, -0.25 * H), (R, 0.0), (R, H - f)]
    for i in range(1, 4):
        a = math.pi / 2 * i / 3
        rings.append((R - f + f * math.cos(a), H - f + f * math.sin(a)))
    if socket:
        rings += [((lambda th, s=s: hex_r(th, s) * 1.1), H), ((lambda th, s=s: hex_r(th, s)), H - 0.08 * s),
                  ((lambda th, s=s: hex_r(th, s)), H - 0.6 * H), (0.0, H - 0.6 * H - 0.25 * s)]
    else:
        rings.append((0.0, H))
    segs = max(12, segs - segs % 6)
    ob = loft_rings(name, rings, segs, None, smooth_angle=40.0)
    me = ob.data
    bpy.data.objects.remove(ob)
    return me


def place_linked(me, name, coll, mats, *, parent=None):
    """Объекты по списку матриц с общим мешем (связанные копии: рендер дешевле, веб — инстансы)."""
    obs = []
    for i, m in enumerate(mats):
        ob = bpy.data.objects.new(f"{name}_{i:02d}", me)
        ob.matrix_world = m
        coll.objects.link(ob)
        if parent is not None:
            ob.parent = parent
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_basis = m
        obs.append(ob)
    return obs


def circle_mats(radius, n, *, axis="X", at=0.0, phase=0.0, outward=1, embed=0.0005):
    """Матрицы крепежа по окружности на торце, нормаль торца — ±axis (outward). Винт смотрит головкой наружу."""
    out = []
    for i in range(n):
        a = phase + TAU * i / n
        if axis == "X":
            loc = Vector((at - outward * embed, radius * math.cos(a), radius * math.sin(a)))
            rot = Matrix.Rotation(math.radians(90 * outward), 4, "Y")
        elif axis == "Z":
            loc = Vector((radius * math.cos(a), radius * math.sin(a), at - outward * embed))
            rot = Matrix.Identity(4) if outward > 0 else Matrix.Rotation(math.pi, 4, "X")
        else:
            raise ValueError(axis)
        out.append(Matrix.Translation(loc) @ rot @ Matrix.Rotation(a * 3.7, 4, "Z"))
    return out


# ------------------------------------------------------------------ кольцо-замок
def lock_ring(name, r_in, R, w, *, segs, ridges=48, depth=0.0012, led_w=0.0035, seg=3, coll=None, ridged=True):
    """Оранжевое кольцо вокруг локальной Z от h = 0 до w: рифлёные пояски и канавка по центру под светодиодную полосу.
    Возвращает (кольцо, полоса)."""
    f = min(0.002, w * 0.12)
    g0, g1 = w / 2 - led_w / 2, w / 2 + led_w / 2
    gd = 0.0016

    def ridge(th):
        c = 0.5 - 0.5 * math.cos(ridges * th)
        return R - depth * c ** 3
    rr = ridge if (ridged and ridges) else R
    rings = [(r_in, 0.0), (R - f, 0.0)]
    for i in range(1, seg + 1):
        a = math.pi / 2 * i / seg
        rings.append((R - f + f * math.sin(a), f - f * math.cos(a)))
    band = [(rr, f + 0.0008), (rr, g0 - 0.0006), (R, g0 - 0.0002), (R - gd, g0 + 0.0002), (R - gd, g1 - 0.0002),
            (R, g1 + 0.0002), (rr, g1 + 0.0006), (rr, w - f - 0.0008)]
    rings += band
    for i in range(seg + 1):
        a = math.pi / 2 * i / seg
        rings.append((R - f + f * math.cos(a), w - f + f * math.sin(a)))
    rings.append((r_in, w))
    ring = loft_rings(name, rings, segs, coll, closed=True, smooth_angle=32.0)
    led = loft_rings(name + "_led", [(R - gd - 0.0002, g0 + 0.0004), (R - gd + 0.0009, g0 + 0.0004),
                                     (R - gd + 0.0009, g1 - 0.0004), (R - gd - 0.0002, g1 - 0.0004)],
                     segs, coll, closed=True, smooth_angle=60.0)
    return ring, led


def torus_seal(name, R, minor, *, segs, ring_segs=12, coll=None):
    """Резиновое уплотнение-тор вокруг локальной Z (сплюснутое 0,8)."""
    rings = []
    for i in range(ring_segs):
        a = TAU * i / ring_segs
        rings.append((R + minor * math.cos(a), minor * 0.8 * math.sin(a)))
    return loft_rings(name, rings, segs, coll, closed=True, smooth_angle=80.0)


# ------------------------------------------------------------------ наклейки/печать
def cyl_patch(name, R, a_center, h_center, width, height, *, nu=48, nv=4, coll=None):
    """Участок цилиндра вокруг локальной Z (печать на корпусе): ширина — по дуге, UV 0..1 (u — слева направо снаружи)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    span = width / R
    grid = []
    for j in range(nv + 1):
        z = h_center - height / 2 + height * j / nv
        row = []
        for i in range(nu + 1):
            a = a_center - span / 2 + span * i / nu
            row.append(bm.verts.new((R * math.cos(a), R * math.sin(a), z)))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for lp, (uu, vv) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = (uu / nu, vv / nv)
    return D.obj_from_bm(bm, name, coll, smooth_angle=180.0)


def flat_patch(name, width, height, *, coll=None):
    """Плоская наклейка в плоскости XY, лицом +Z, центр 0, UV 0..1."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new((x, y, 0.0)) for x, y in ((-width / 2, -height / 2), (width / 2, -height / 2),
                                                  (width / 2, height / 2), (-width / 2, height / 2))]
    f = bm.faces.new(vs)
    for lp, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uvl].uv = uvv
    return D.obj_from_bm(bm, name, coll, smooth_angle=None)


# ------------------------------------------------------------------ прочее
def rbox(name, w, d, h, r_corner, r_edge, coll=None, *, seg=6, center=(0, 0, 0)):
    """Скруглённый брусок (d1lib.rounded_slab), центр по XY, низ по Z → центр по Z; ставится в center."""
    ob = D.rounded_slab(name, w, d, h, r_corner, (r_edge, r_edge), coll, corner_seg=seg, edge_seg=max(2, seg // 2),
                        power=2.2, uv=True)
    ob.data.transform(Matrix.Translation((center[0], center[1], center[2] - h / 2)))
    return ob


def gear_ring_r(teeth, r_root, r_tip, sharp=2.0):
    """Радиус-функция зубчатого венца (эвольвенту заменяет сглаженная трапеция)."""
    def f(th):
        c = 0.5 + 0.5 * math.cos(teeth * th)
        c = min(1.0, max(0.0, (c - 0.5) * sharp + 0.5))
        return r_root + (r_tip - r_root) * c
    return f


def sweep_path(name, pts, radius, coll=None, *, segs=24, smooth=60.0):
    prof = D.circle_pts(radius, segs)
    return D.sweep(name, pts, prof, coll, closed=False, cap=True, smooth_angle=smooth)


def keep_below(ob, z=0.0):
    """Срезать меш плоскостью z (локальные оси) и оставить низ, срез залить (веб-разрез мотора для гибрида C: плоскость скана кода
    режет только корпус — медь в пазах видна, когда верх статора срезан заранее)."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=(0.0, 0.0, z), plane_no=(0.0, 0.0, 1.0), clear_outer=True)
    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return ob
