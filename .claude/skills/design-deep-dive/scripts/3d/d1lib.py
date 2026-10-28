"""d1lib — помощники моделирования кодом для Blender 5.2.

Надстройка над bpyx.py (рядом, scripts/3d). Проверено: Blender 5.2.2 LTS (Python 3.13).

Принципы (все — проверенные ловушки 5.2):
- геометрия строится bmesh/data API, без bpy.ops в цикле; UV-слой создаётся ДО операций; bm.to_mesh + bm.free;
- размеры — в метрах в вершинах, масштаб объекта = 1 (не obj.scale); pivot (origin) ставится осознанно;
- гладкость: Mesh.shade_smooth() + Mesh.set_sharp_from_angle() (данные, переживают экспорт без apply);
- у bmesh.ops.bevel умолчания affect='VERTICES', segments=0, profile=0.0 — всегда задавать явно;
- детали собираются «от опорной детали»: координаты вычисляются из габаритов соседей, а не числами наугад.

Группы функций:
  профили 2D     rrect_pts, squircle_pts, circle_pts, ellipse_pts
  тела           loft_slab (пластина/таблетка/корпус с профилем кромки), lathe (тело вращения по профилю),
                 lathe_shell (стенка с толщиной), sweep (трубка/лента по пути с параллельным переносом),
                 extrude_outline (контур с отверстиями → тело через кривую), text_mesh, svg_mesh
  пути           torus_knot_pts, helix_pts, superformula_pts, bezier_pts
  органика       metaball_mesh, noise_displace, sdf_blob_gn (GN: точки → SDF → fillet → меш)
  отделка        hard_surface (Bevel + Weighted Normal), smooth_by_angle_modifier (ассет без окна),
                 boolean_apply (булево + очистка), finish_shading
  pivots/данные  set_origin, add_marker, export_points_f32, export_curve_json, surface_points
  проверки       gltf_vertex_estimate, form_report, silhouette_metrics, part_hierarchy
  сцена          fresh_collection, stage (циклорама + свет от габаритов), frame (камера по габаритам)
"""
from __future__ import annotations

import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector, noise as mnoise

SNIPPETS = os.path.dirname(os.path.abspath(__file__))  # bpyx.py — рядом (scripts/3d)
if SNIPPETS not in sys.path:
    sys.path.insert(0, SNIPPETS)
import bpyx  # noqa: E402

__version__ = "0.1.1"
TESTED_WITH = (5, 2, 2)


def _warn(msg):
    print(f"[d1lib] ВНИМАНИЕ: {msg}")


# ====================================================================== коллекции и объекты

def fresh_collection(name: str, parent=None):
    """Снести свою коллекцию (объекты, дочерние коллекции, данные-сироты) и создать заново. Идемпотентность build(P).
    Чужие объекты сцены не трогает (в отличие от «очистить сцену» — ошибка M6.6). [5.2.2]"""
    old = bpy.data.collections.get(name)
    if old is not None:
        datas = []
        for ob in list(old.all_objects):
            datas.append(ob.data)
            bpy.data.objects.remove(ob, do_unlink=True)
        for ch in list(old.children_recursive):
            bpy.data.collections.remove(ch)
        bpy.data.collections.remove(old)
        for d in datas:
            if d is None or d.users:
                continue
            for pool in (bpy.data.meshes, bpy.data.curves, bpy.data.lights, bpy.data.cameras, bpy.data.metaballs):
                if pool.get(d.name) == d:
                    pool.remove(d)
                    break
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def obj_from_bm(bm, name: str, collection=None, *, smooth_angle: float | None = 30.0, location=(0, 0, 0)):
    """bmesh → меш-объект в коллекции. smooth_angle: None — плоско; число — гладко + острые рёбра по углу. [5.2.2]"""
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    if smooth_angle is not None:
        me.shade_smooth()
        if smooth_angle < 180:
            me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    else:
        me.shade_flat()
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


# ====================================================================== 2D-профили (контуры в плоскости XY, CCW)

def rrect_pts(w: float, h: float, r: float, seg: int = 8):
    """Скруглённый прямоугольник w×h с радиусом r, CCW, центр в 0. Число точек = 4·(seg+1) при любом r
    (нужно для перемычек колец одинаковой длины). r обрезается до min(w, h)/2. [5.2.2]"""
    r = max(0.0, min(r, w / 2, h / 2))
    cx, cy = w / 2 - r, h / 2 - r
    pts = []
    for k, (sx, sy, a0) in enumerate(((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270))):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((sx * cx + r * math.cos(a), sy * cy + r * math.sin(a)))
    return pts


def squircle_pts(w: float, h: float, n: float = 4.0, count: int = 64):
    """Суперэллипс |x/a|^n + |y/b|^n = 1 (n=2 — эллипс, 4–5 — «иконка iOS» с непрерывной кривизной), CCW. [5.2.2]"""
    a, b = w / 2, h / 2
    pts = []
    for i in range(count):
        t = 2 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        pts.append((a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s) ** (2 / n), s)))
    return pts


def circle_pts(r: float, count: int = 32):
    return [(r * math.cos(2 * math.pi * i / count), r * math.sin(2 * math.pi * i / count)) for i in range(count)]


def ellipse_pts(a: float, b: float, count: int = 48):
    return [(a * math.cos(2 * math.pi * i / count), b * math.sin(2 * math.pi * i / count)) for i in range(count)]


def superformula_pts(m=6, n1=0.3, n2=0.3, n3=0.3, a=1.0, b=1.0, scale=1.0, count=256):
    """Суперформула Гиелиса — органичные «цветочные» контуры для логотипов и скульптур. [5.2.2]"""
    pts = []
    for i in range(count):
        t = 2 * math.pi * i / count
        p1 = abs(math.cos(m * t / 4) / a) ** n2
        p2 = abs(math.sin(m * t / 4) / b) ** n3
        r = (p1 + p2) ** (-1 / n1) if (p1 + p2) > 0 else 0
        pts.append((scale * r * math.cos(t), scale * r * math.sin(t)))
    return pts


# ====================================================================== пластины, корпуса, «таблетки»

def edge_profile(bottom_r: float, top_r: float, height: float, seg: int = 6, power: float = 2.0):
    """Профиль кромки [(inset, z)] снизу вверх: нижняя дуга радиуса bottom_r, прямой борт, верхняя дуга top_r.
    power=2 — окружность; >2 — «супер»-дуга (мягче переход к плоскости, ближе к G2). [5.2.2]"""
    prof = []

    def arc(r, z0, up):
        out = []
        for i in range(seg + 1):
            t = i / seg                                            # 0 → 1
            ang = math.pi / 2 * t
            c, s = math.cos(ang), math.sin(ang)
            cc, ss = abs(c) ** (2 / power), abs(s) ** (2 / power)
            if up:     # нижняя дуга: от (inset=r, z=0) к (0, r)
                out.append((r * (1 - ss), z0 + r * (1 - cc)))
            else:      # верхняя дуга: от (0, h-r) к (r, h)
                out.append((r * (1 - cc), z0 + r * ss))
        return out
    if bottom_r > 0:
        prof += arc(bottom_r, 0.0, True)
    else:
        prof.append((0.0, 0.0))
    if top_r > 0:
        top = arc(top_r, height - top_r, False)
    else:
        top = [(0.0, height)]
    if abs(prof[-1][1] - top[0][1]) < 1e-9:
        top = top[1:]
    prof += top
    return prof


def loft_slab(name: str, outline, profile, collection=None, *, cap_bottom=True, cap_top=True, smooth_angle=35.0,
              triangulate_caps=False, uv=True, location=(0, 0, 0)):
    """Тело из колец контура по профилю кромки — корпуса устройств, «таблетки», кнопки, мягкие иконки.

    outline(inset) → список (x, y) CCW одинаковой длины при любом inset (rrect_pts с r−inset, squircle);
    profile — [(inset, z)] снизу вверх (edge_profile). Боковина — квады (без полюсов и n-гонов), крышки — n-гон
    (выпуклый контур) или треугольники (triangulate_caps). UV: боковина — развёртка по длине контура и профиля,
    крышки — планарная проекция. Возвращает объект; в ob["d1_rings"] — число колец. [5.2.2]"""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap") if uv else None
    rings = []
    for inset, z in profile:
        pts = outline(inset)
        rings.append([bm.verts.new((x, y, z)) for x, y in pts])
    n = len(rings[0])
    if any(len(r) != n for r in rings):
        bm.free()
        raise ValueError("loft_slab: у колец разное число точек — outline(inset) должен давать одинаковую длину")
    # длины для UV
    per = [0.0]
    for i in range(n):
        a, b = rings[len(rings) // 2][i].co, rings[len(rings) // 2][(i + 1) % n].co
        per.append(per[-1] + (b - a).length)
    vlen = [0.0]
    for j in range(len(profile) - 1):
        (i0, z0), (i1, z1) = profile[j], profile[j + 1]
        vlen.append(vlen[-1] + math.hypot(i1 - i0, z1 - z0))
    for j in range(len(rings) - 1):
        ra, rb = rings[j], rings[j + 1]
        for i in range(n):
            i2 = (i + 1) % n
            f = bm.faces.new((ra[i], ra[i2], rb[i2], rb[i]))
            if uvl is not None:
                us = (per[i] / per[-1], per[i + 1] / per[-1])
                vs = (vlen[j] / max(vlen[-1], 1e-9), vlen[j + 1] / max(vlen[-1], 1e-9))
                for loop, uvv in zip(f.loops, ((us[0], vs[0]), (us[1], vs[0]), (us[1], vs[1]), (us[0], vs[1]))):
                    loop[uvl].uv = uvv
    caps = []
    if cap_bottom:
        caps.append(bm.faces.new(list(reversed(rings[0]))))
    if cap_top:
        caps.append(bm.faces.new(rings[-1]))
    if uvl is not None and caps:
        xs = [v.co.x for v in rings[0]]
        ys = [v.co.y for v in rings[0]]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        for f in caps:
            for loop in f.loops:
                loop[uvl].uv = ((loop.vert.co.x - x0) / max(x1 - x0, 1e-9), (loop.vert.co.y - y0) / max(y1 - y0, 1e-9))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if triangulate_caps and caps:
        bmesh.ops.triangulate(bm, faces=caps, quad_method="BEAUTY", ngon_method="BEAUTY")
    ob = obj_from_bm(bm, name, collection, smooth_angle=smooth_angle, location=location)
    ob["d1_rings"] = len(rings)
    return ob


def rounded_slab(name: str, w: float, d: float, h: float, corner_r: float, edge_r: float | tuple = 0.0,
                 collection=None, *, corner_seg: int = 8, edge_seg: int = 4, power: float = 2.0, kind: str = "rrect",
                 squircle_n: float = 4.5, **kw):
    """Пластина w×d×h (Z — толщина) со скруглёнными углами corner_r и кромкой edge_r (или (низ, верх)).
    kind='rrect' — точное смещение колец (углы окружностью); 'squircle' — суперэллипс n (непрерывная кривизна,
    смещение приближённое). edge_r ≤ corner_r (иначе угол вырождается). [5.2.2]"""
    eb, et = (edge_r, edge_r) if not isinstance(edge_r, (tuple, list)) else edge_r
    if max(eb, et) > corner_r + 1e-9 and kind == "rrect":
        raise ValueError(f"rounded_slab {name}: edge_r {max(eb, et)} > corner_r {corner_r} — угол вырождается")
    if eb + et > h + 1e-9:
        raise ValueError(f"rounded_slab {name}: кромки {eb}+{et} больше толщины {h}")
    if kind == "rrect":
        outline = lambda inset: rrect_pts(w - 2 * inset, d - 2 * inset, corner_r - inset, corner_seg)  # noqa: E731
    elif kind == "squircle":
        cnt = corner_seg * 8
        outline = lambda inset: squircle_pts(w - 2 * inset, d - 2 * inset, squircle_n, cnt)  # noqa: E731
    else:
        raise ValueError("kind: rrect | squircle")
    prof = edge_profile(eb, et, h, edge_seg, power)
    return loft_slab(name, outline, prof, collection, **kw)


# ====================================================================== тела вращения

def lathe(name: str, profile_rz, collection=None, *, segments: int = 64, smooth_angle: float = 40.0, uv=True,
          location=(0, 0, 0)):
    """Тело вращения вокруг Z из профиля [(r, z), …] (открытая полилиния, снизу вверх). Точки с r == 0 — полюса на
    оси (схлопываются в одну вершину). Боковина — квады, у оси — треугольники-веер. UV: u — угол, v — длина профиля.
    [5.2.2]"""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap") if uv else None
    rings = []
    for r, z in profile_rz:
        if r <= 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segments), r * math.sin(2 * math.pi * k / segments), z))
                          for k in range(segments)])
    L = [0.0]
    for j in range(len(profile_rz) - 1):
        (r0, z0), (r1, z1) = profile_rz[j], profile_rz[j + 1]
        L.append(L[-1] + math.hypot(r1 - r0, z1 - z0))
    for j in range(len(rings) - 1):
        a, b = rings[j], rings[j + 1]
        v0, v1 = L[j] / max(L[-1], 1e-9), L[j + 1] / max(L[-1], 1e-9)
        for k in range(segments):
            k2 = (k + 1) % segments
            u0, u1 = k / segments, (k + 1) / segments
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                f = bm.faces.new((a[0], b[k], b[k2]))
                uvs = ((u0 + 0.5 / segments, v0), (u0, v1), (u1, v1))
            elif len(b) == 1:
                f = bm.faces.new((a[k], a[k2], b[0]))
                uvs = ((u0, v0), (u1, v0), (u0 + 0.5 / segments, v1))
            else:
                f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
                uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
            if uvl is not None:
                for loop, uvv in zip(f.loops, uvs):
                    loop[uvl].uv = uvv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obj_from_bm(bm, name, collection, smooth_angle=smooth_angle, location=location)


def round_corner(p0, corner, p1, radius, seg=4):
    """Точки дуги, вписанной в угол p0–corner–p1 (2D, (r, z)): для профилей тел вращения со скруглениями. [5.2.2]"""
    c = Vector(corner)
    a, b = (Vector(p0) - c).normalized(), (Vector(p1) - c).normalized()
    ang = math.acos(max(-1.0, min(1.0, a.dot(b))))
    if ang < 1e-4 or abs(ang - math.pi) < 1e-4 or radius <= 0:
        return [tuple(c)]
    t = radius / math.tan(ang / 2)
    s, e = c + a * t, c + b * t
    bis = (a + b).normalized()
    center = c + bis * (radius / math.sin(ang / 2))
    v0, v1 = s - center, e - center
    a0, a1 = math.atan2(v0.y, v0.x), math.atan2(v1.y, v1.x)
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    return [tuple(center + Vector((math.cos(a0 + da * i / seg), math.sin(a0 + da * i / seg))) * radius)
            for i in range(seg + 1)]


def fillet_polyline(pts, radii, seg=4):
    """Полилиния [(x, y)] со скруглением внутренних углов радиусами radii (число или список на каждую точку). [5.2.2]"""
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * len(pts)
    out = [tuple(pts[0])]
    for i in range(1, len(pts) - 1):
        r = radii[i]
        if r and r > 0:
            out += round_corner(pts[i - 1], pts[i], pts[i + 1], r, seg)
        else:
            out.append(tuple(pts[i]))
    out.append(tuple(pts[-1]))
    return out


def lathe_shell(name: str, outer_rz, wall: float, collection=None, *, lip_seg: int = 4, **kw):
    """Сосуд со стенкой толщины wall: наружный профиль снизу (от оси) вверх до кромки, затем скруглённая кромка и
    внутренний профиль обратно вниз (смещение по нормали профиля на wall). Кружки, стаканы, флаконы. [5.2.2]"""
    pts = [Vector(p) for p in outer_rz]
    # внутренний профиль: смещение каждой точки внутрь по нормали полилинии (без точки на оси)
    inner = []
    for i, p in enumerate(pts):
        if p.x <= 1e-9:
            continue
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        nrm = Vector((-t.y, t.x))           # влево от направления (наружу — вправо) → внутрь/вверх
        q = p + nrm * wall
        inner.append((max(q.x, 0.0), q.y))
    top_o = pts[-1]
    top_i = Vector(inner[-1])
    lip_c = (top_o + top_i) / 2
    lip = []
    for k in range(1, lip_seg):
        ang = math.pi * k / lip_seg
        lip.append((lip_c.x + (top_o.x - lip_c.x) * math.cos(ang), top_o.y + wall / 2 * math.sin(ang)))
    inner_rev = list(reversed(inner))
    # дно внутри: последняя внутренняя точка → к оси на её высоте
    bottom_inner = (0.0, inner_rev[-1][1])
    prof = [tuple(p) for p in pts] + lip + inner_rev + [bottom_inner]
    return lathe(name, prof, collection, **kw)


# ====================================================================== протяжка по пути (трубки, ленты, узлы)

def _frames(path, closed):
    n = len(path)
    P = [Vector(p) for p in path]
    T = []
    for i in range(n):
        if closed:
            t = P[(i + 1) % n] - P[i - 1]
        else:
            t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
        T.append(t.normalized())
    # начальная нормаль: перпендикуляр к T0, по наименьшей компоненте
    t0 = T[0]
    ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    N = [(ref - t0 * ref.dot(t0)).normalized()]
    for i in range(1, n):
        v = T[i - 1].cross(T[i])
        if v.length < 1e-9:
            N.append(N[-1].copy())
            continue
        ang = math.acos(max(-1.0, min(1.0, T[i - 1].dot(T[i]))))
        N.append((Matrix.Rotation(ang, 3, v.normalized()) @ N[-1]).normalized())
    twist_fix = 0.0
    if closed:
        # голономия: перенести N[-1] в T[0] и измерить угол до N[0]; раздать поровну по кольцам
        v = T[-1].cross(T[0])
        n_end = N[-1]
        if v.length > 1e-9:
            ang = math.acos(max(-1.0, min(1.0, T[-1].dot(T[0]))))
            n_end = (Matrix.Rotation(ang, 3, v.normalized()) @ N[-1]).normalized()
        cosang = max(-1.0, min(1.0, n_end.dot(N[0])))
        twist_fix = math.acos(cosang)
        if T[0].dot(n_end.cross(N[0])) < 0:
            twist_fix = -twist_fix
    return P, T, N, twist_fix


def sweep(name: str, path, profile, collection=None, *, closed: bool = False, twist: float = 0.0, scale=None,
          cap: bool = True, smooth_angle: float = 40.0, uv: bool = True, location=(0, 0, 0)):
    """Протяжка профиля вдоль пути с параллельным переносом рамок (без переворотов, в отличие от Frenet).

    path — точки 3D; profile — число (радиус круглой трубки, 16 сегментов), или список (u, v) в плоскости N–B
    (замкнутый контур, CCW); closed — замкнутый путь (кольца стыкуются, голономия раздаётся равномерно);
    twist — полный закрут ленты вдоль пути, рад; scale — функция t∈[0,1] → множитель профиля (сужения, капли);
    cap — заглушки на концах открытого пути (n-гон). [5.2.2]"""
    if isinstance(profile, (int, float)):
        profile = circle_pts(float(profile), 16)
    P, T, N, fix = _frames(path, closed)
    n = len(P)
    m = len(profile)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap") if uv else None
    L = [0.0]
    for i in range(1, n):
        L.append(L[-1] + (P[i] - P[i - 1]).length)
    total = L[-1] + ((P[0] - P[-1]).length if closed else 0.0)
    rings = []
    for i in range(n):
        t = L[i] / max(total, 1e-9)
        ang = twist * t + (fix * t if closed else 0.0)
        Ni = Matrix.Rotation(ang, 3, T[i]) @ N[i]
        Bi = T[i].cross(Ni)
        s = scale(t) if scale else 1.0
        rings.append([bm.verts.new(P[i] + (Ni * u + Bi * v) * s) for u, v in profile])
    per = [0.0]
    for k in range(m):
        a, b = Vector(profile[k]), Vector(profile[(k + 1) % m])
        per.append(per[-1] + (b - a).length)
    nseg = n if closed else n - 1
    for i in range(nseg):
        a, b = rings[i], rings[(i + 1) % n]
        t0 = L[i] / max(total, 1e-9)
        t1 = (L[i + 1] if i + 1 < n else total) / max(total, 1e-9)
        for k in range(m):
            k2 = (k + 1) % m
            f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
            if uvl is not None:
                u0, u1 = per[k] / per[-1], per[k + 1] / per[-1]
                for loop, uvv in zip(f.loops, ((t0, u0), (t0, u1), (t1, u1), (t1, u0))):
                    loop[uvl].uv = uvv
    if not closed and cap:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obj_from_bm(bm, name, collection, smooth_angle=smooth_angle, location=location)


def torus_knot_pts(p: int = 2, q: int = 3, R: float = 1.0, r: float = 0.4, count: int = 256):
    """Точки торического узла (p, q): p оборотов вокруг оси, q — через дырку тора. Замкнутый путь. [5.2.2]"""
    pts = []
    for i in range(count):
        t = 2 * math.pi * i / count
        rr = R + r * math.cos(q * t)
        pts.append((rr * math.cos(p * t), rr * math.sin(p * t), r * math.sin(q * t)))
    return pts


def helix_pts(radius: float, height: float, turns: float, count: int = 128, taper: float = 0.0):
    return [(radius * (1 - taper * i / (count - 1)) * math.cos(2 * math.pi * turns * i / (count - 1)),
             radius * (1 - taper * i / (count - 1)) * math.sin(2 * math.pi * turns * i / (count - 1)),
             height * i / (count - 1)) for i in range(count)]


def bezier_pts(ctrl, count: int = 64):
    """Кубическая кривая Безье по 4 точкам (или цепочке 3k+1 точек) → равномерные по параметру точки. [5.2.2]"""
    C = [Vector(c) for c in ctrl]
    segs = (len(C) - 1) // 3
    out = []
    for s in range(segs):
        p0, p1, p2, p3 = C[3 * s:3 * s + 4]
        for i in range(count // segs + (1 if s == segs - 1 else 0)):
            t = i / (count // segs)
            if t > 1:
                break
            out.append(tuple(p0 * (1 - t) ** 3 + p1 * 3 * (1 - t) ** 2 * t + p2 * 3 * (1 - t) * t ** 2 + p3 * t ** 3))
    return out


def resample_polyline(pts, count, closed=False):
    """Равномерная по длине пересборка полилинии (для sweep и путей камеры). [5.2.2]"""
    P = [Vector(p) for p in pts]
    if closed:
        P = P + [P[0]]
    L = [0.0]
    for i in range(1, len(P)):
        L.append(L[-1] + (P[i] - P[i - 1]).length)
    out = []
    n = count if closed else count - 1
    j = 0
    for k in range(count):
        s = L[-1] * k / n
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        seg = max(L[j + 1] - L[j], 1e-12)
        t = (s - L[j]) / seg
        out.append(tuple(P[j].lerp(P[j + 1], min(max(t, 0.0), 1.0))))
    return out



def weld_mesh(me, dist: float = 1e-6):
    """Сварить совпадающие вершины: меш из кривой/текста (new_from_object) не сварен по швам заливки и фаски —
    неманифолдные рёбра (3280 на решётке 7×7). [5.2.2]"""
    bm = bmesh.new()
    bm.from_mesh(me)
    n0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    n1 = len(bm.verts)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return n0 - n1


def catmull_rom_pts(ctrl, count: int = 64, closed: bool = False):
    """Гладкая кривая Catmull-Rom (centripetal-приближение uniform) через контрольные точки 2D/3D, затем равномерная
    пересборка по длине — для профилей тел вращения без «ступенек» затенения (колокол из ломаной даёт
    полосы). [5.2.2]"""
    P = [Vector(p) for p in ctrl]
    n = len(P)
    dense = []
    segs = n if closed else n - 1
    for i in range(segs):
        p0 = P[(i - 1) % n] if (closed or i > 0) else P[0] * 2 - P[1]
        p1, p2 = P[i % n], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (closed or i + 2 < n) else P[-1] * 2 - P[-2]
        for k in range(16):
            t = k / 16
            t2, t3 = t * t, t * t * t
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        dense.append(P[-1])
    return [tuple(v) for v in [Vector(q) for q in resample_polyline([tuple(d) for d in dense], count, closed=closed)]]

# ====================================================================== контуры, текст, SVG

def extrude_outline(name: str, loops, depth: float, collection=None, *, bevel: float = 0.0, bevel_res: int = 2,
                    resolution: int = 12, keep_size: bool = True, smooth_angle: float = 30.0):
    """Плоский контур (внешний + отверстия, каждый — список (x, y)) → тело толщины depth с фаской bevel.

    Через кривую POLY с fill_mode='BOTH' (заливка с отверстиями и вогнутостями без ручной триангуляции), extrude,
    bevel_depth; keep_size=True — offset = −bevel, чтобы фаска не раздувала контур. Затем → меш (new_from_object).
    Лицо смотрит на +Z; поставить вертикально — ob.data.transform(Matrix.Rotation(π/2, 4, 'X')). [5.2.2]"""
    cu = bpy.data.curves.new(name + "_crv", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.resolution_u = resolution
    for loop in loops:
        sp = cu.splines.new("POLY")
        sp.points.add(len(loop) - 1)
        for p, (x, y) in zip(sp.points, loop):
            p.co = (x, y, 0.0, 1.0)
        sp.use_cyclic_u = True
    cu.extrude = max(depth / 2 - bevel, 0.0)
    cu.bevel_depth = bevel
    cu.bevel_resolution = bevel_res
    if keep_size and bevel > 0:
        cu.offset = -bevel
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)
    me.name = name
    weld_mesh(me)
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def text_mesh(name: str, body: str, collection=None, *, size: float = 0.2, extrude: float = 0.02,
              bevel: float = 0.004, bevel_res: int = 1, resolution_u: int = 3, font_path: str | None = None,
              align_x: str = "CENTER", upright: bool = True, smooth_angle: float = 30.0, offset_bevel: bool = True):
    """3D-текст → меш. resolution_u 3–4 и bevel_res 0–1 — веб-бюджет (9968 → 1520 треуг.).
    upright=True — буквы стоят лицом к −Y (к камере «спереди»), низ базовой линии на z=0 (ошибка M2.12 — текст
    плашмя). offset_bevel — фаска не утолщает буквы (offset = −bevel). Шрифт — встроенный или файл проекта
    (не путь ОС — M1.13). [5.2.2]"""
    cu = bpy.data.curves.new(name + "_txt", "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = bevel_res
    cu.resolution_u = resolution_u
    cu.align_x = align_x
    cu.align_y = "BOTTOM_BASELINE"
    if offset_bevel and bevel > 0:
        cu.offset = -bevel
    if font_path:
        cu.font = bpy.data.fonts.load(font_path, check_existing=True)
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)
    me.name = name
    weld_mesh(me)
    if upright:
        me.transform(Matrix.Rotation(math.radians(90), 4, "X"))
        zmin = min(v.co.z for v in me.vertices) if me.vertices else 0.0
        me.transform(Matrix.Translation((0, 0, -zmin)))
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def svg_mesh(name: str, svg_path: str, collection=None, *, size: float = 0.2, depth: float = 0.02,
             bevel: float = 0.002, bevel_res: int = 1, resolution_u: int = 4, upright: bool = True,
             smooth_angle: float = 30.0):
    """SVG → кривые (оператор import_curve.svg, 5.2.2: аддон io_curve_svg, работает в фоне) → одна сетка с толщиной.

    Импортёр создаёт коллекцию с кривыми в метрах по viewBox (px → м, крошечные); здесь: объединить кривые,
    отцентрировать и масштабировать к ширине size, задать extrude/bevel/resolution, конвертировать в меш. [5.2.2]"""
    before = set(bpy.data.objects)
    before_coll = set(bpy.data.collections)
    r = bpy.ops.import_curve.svg(filepath=os.path.abspath(svg_path))
    if r != {"FINISHED"}:
        raise RuntimeError(f"import_curve.svg → {r}")
    new_obs = [o for o in bpy.data.objects if o not in before and o.type == "CURVE"]
    if not new_obs:
        raise RuntimeError("SVG: кривые не импортированы")
    dg = bpy.context.evaluated_depsgraph_get()
    # габариты всех кривых в мире
    pts = []
    for o in new_obs:
        for sp in o.data.splines:
            for bp in sp.bezier_points:
                pts.append(o.matrix_world @ bp.co)
            for p in sp.points:
                pts.append(o.matrix_world @ Vector(p.co[:3]))
    mn = Vector(map(min, *pts))
    mx = Vector(map(max, *pts))
    w = max(mx.x - mn.x, 1e-9)
    k = size / w
    c = (mn + mx) / 2
    meshes = []
    for o in new_obs:
        cu = o.data
        cu.dimensions = "2D"
        cu.fill_mode = "BOTH"
        cu.resolution_u = resolution_u
        # толщину и фаску задаём в единицах кривой, чтобы после масштаба k получить метры
        cu.extrude = max(depth / 2 - bevel, 0.0) / k / max(o.matrix_world.to_scale().x, 1e-9)
        cu.bevel_depth = bevel / k / max(o.matrix_world.to_scale().x, 1e-9)
        cu.bevel_resolution = bevel_res
        if bevel > 0:
            cu.offset = -cu.bevel_depth
    dg = bpy.context.evaluated_depsgraph_get()
    for o in new_obs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        me.transform(Matrix.Translation(-c))
        me.transform(Matrix.Scale(k, 4))
        meshes.append(me)
    # объединить в один меш через bmesh
    bm = bmesh.new()
    for me in meshes:
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in new_obs:
        bpy.data.objects.remove(o, do_unlink=True)
    for cl in [c2 for c2 in bpy.data.collections if c2 not in before_coll]:
        if not cl.all_objects:
            bpy.data.collections.remove(cl)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    if upright:
        bmesh.ops.rotate(bm, verts=bm.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
        zmin = min(v.co.z for v in bm.verts)
        bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, -zmin))
    return obj_from_bm(bm, name, collection, smooth_angle=smooth_angle)


# ====================================================================== органика

def metaball_mesh(name: str, balls, collection=None, *, resolution: float = 0.05, threshold: float = 0.6,
                  smooth_angle: float = 180.0):
    """Метаболы → меш (блобы): balls = [(x, y, z, radius[, stiffness])]. resolution — размер ячейки полигонизации
    в метрах (меньше — плотнее: число треугольников ~ (размер/resolution)²). [5.2.2]"""
    mb = bpy.data.metaballs.new(name + "_mb")
    mb.resolution = resolution
    mb.render_resolution = resolution
    mb.threshold = threshold
    for b in balls:
        e = mb.elements.new()
        e.co = b[:3]
        e.radius = b[3]
        if len(b) > 4:
            e.stiffness = b[4]
    tmp = bpy.data.objects.new(name + "_tmp", mb)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    me.name = name
    me.shade_smooth()
    if smooth_angle < 180:
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob


def sdf_blob_gn(name: str, balls, collection=None, *, voxel: float = 0.004, fillet_iter: int = 4,
                smooth_width: int = 0, smooth_iter: int = 0, threshold: float = 0.0, apply: bool = True):
    """Блоб через SDF-ноды 5.2: вершины-центры с атрибутом radius → Mesh to Points → Points to SDF Grid →
    SDF Grid Fillet (сглаживает впадины между шарами) → Grid to Mesh → Set Shade Smooth. voxel — размер вокселя
    (треугольники ~ (размер/voxel)²). apply=True — сразу меш без модификатора. [5.2.2]"""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(b[:3]) for b in balls], [], [])
    ra = me.attributes.new("radius", "FLOAT", "POINT")
    ra.data.foreach_set("value", [float(b[3]) for b in balls])
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    t, gi, go = bpyx.gn_tree(name + "_SDF", inputs=[("Voxel Size", "NodeSocketFloat", voxel),
                                                    ("Fillet", "NodeSocketInt", fillet_iter)])
    na = bpyx.node(t, "GeometryNodeInputNamedAttribute", data_type="FLOAT")
    na.inputs["Name"].default_value = "radius"
    m2p = bpyx.node(t, "GeometryNodeMeshToPoints", mode="VERTICES")
    p2s = bpyx.node(t, "GeometryNodePointsToSDFGrid")
    fil = bpyx.node(t, "GeometryNodeSDFGridFillet")
    g2m = bpyx.node(t, "GeometryNodeGridToMesh")
    g2m.inputs["Threshold"].default_value = threshold
    ssm = bpyx.node(t, "GeometryNodeSetShadeSmooth")
    L = lambda a, b: bpyx.link_sockets(t, a, b)  # noqa: E731
    L((gi, "Geometry"), (m2p, "Mesh"))
    L((na, "Attribute"), (m2p, "Radius"))
    L((m2p, "Points"), (p2s, "Points"))
    L((na, "Attribute"), (p2s, "Radius"))
    L((gi, "Voxel Size"), (p2s, "Voxel Size"))
    L((p2s, "SDF Grid"), (fil, "Grid"))
    L((gi, "Fillet"), (fil, "Iterations"))
    if smooth_iter > 0:                  # SDF Grid Mean: общее сглаживание поля (капля, а не «гроздь шаров»)
        mean = bpyx.node(t, "GeometryNodeSDFGridMean")
        mean.inputs["Width"].default_value = max(1, smooth_width)
        mean.inputs["Iterations"].default_value = smooth_iter
        L((fil, "Grid"), (mean, "Grid"))
        L((mean, "Grid"), (g2m, "Grid"))
    else:
        L((fil, "Grid"), (g2m, "Grid"))
    L((g2m, "Mesh"), (ssm, "Mesh"))
    L((ssm, "Mesh"), (go, "Geometry"))
    bpyx.gn_modifier(ob, t)
    if apply:
        bpyx.apply_modifiers(ob)
        ob.data.shade_smooth()
    return ob


def noise_displace(ob, *, strength: float = 0.05, scale: float = 2.0, octaves: int = 3, seed: int = 1,
                   basis: str = "PERLIN_ORIGINAL", along_normal: bool = True):
    """Детерминированное смещение вершин фрактальным шумом mathutils.noise (без текстур и модификаторов — сразу
    в меш, экспорт без потерь). seed фиксирует результат. [5.2.2]"""
    mnoise.seed_set(seed)
    me = ob.data
    for v in me.vertices:
        p = v.co * scale
        val = mnoise.fractal(p, 0.5, 2.0, octaves, noise_basis=basis)
        if along_normal:
            v.co += v.normal * (val * strength)
        else:
            v.co += Vector(mnoise.noise_vector(p, noise_basis=basis)) * strength
    me.update()
    return ob


# ====================================================================== отделка: фаски, нормали, булевы

def hard_surface(ob, *, bevel_width: float, segments: int = 3, angle: float = 30.0, profile: float = 0.5,
                 harden: bool = True, weighted: bool = True, wn_weight: int = 50, clamp: bool = True,
                 limit_method: str = "ANGLE", miter_outer: str = "MITER_ARC"):
    """Hard-surface стек: Bevel (по углу, harden_normals) → Weighted Normal (keep_sharp). Экспорт — только с
    export_apply=True (иначе уходит голый меш). Возвращает (bevel, wn). [5.2.2]"""
    b = bpyx.add_modifier(ob, "BEVEL", width=bevel_width, segments=segments, limit_method=limit_method,
                          angle_limit=math.radians(angle), profile=profile, harden_normals=harden,
                          use_clamp_overlap=clamp, miter_outer=miter_outer)
    wn = None
    if weighted:
        wn = bpyx.add_modifier(ob, "WEIGHTED_NORMAL", weight=wn_weight, keep_sharp=True, mode="FACE_AREA")
    ob.data.shade_smooth()
    return b, wn


ESSENTIALS = None


def smooth_by_angle_modifier(ob, angle: float = 30.0, *, ignore_sharpness: bool = False):
    """Модификатор-ассет «Smooth by Angle» без окна и без оператора: node group из
    <datafiles>/assets/nodes/geometry_nodes_essentials.blend через bpy.data.libraries.load (append) + NODES.
    (Оператор modifier_add_node_group в фоне отменяется; object.shade_auto_smooth работает, но требует контекст.)
    [5.2.2]"""
    global ESSENTIALS
    ng = next((g for g in bpy.data.node_groups if g.name.startswith("Smooth by Angle")), None)
    if ng is None:
        if ESSENTIALS is None:
            base = bpy.utils.system_resource("DATAFILES", path="assets/nodes")
            ESSENTIALS = os.path.join(base, "geometry_nodes_essentials.blend")
        with bpy.data.libraries.load(ESSENTIALS, link=False) as (src, dst):
            names = [n for n in src.node_groups if n.startswith("Smooth by Angle")]
            if not names:
                raise RuntimeError(f"в {ESSENTIALS} нет группы Smooth by Angle: {list(src.node_groups)[:20]}")
            dst.node_groups = names[:1]
        ng = dst.node_groups[0]
    m = ob.modifiers.new("Smooth by Angle", "NODES")
    m.node_group = ng
    ids = bpyx.gn_inputs(m)
    angle_id = next((i for n, i in ids.items() if n.lower().startswith("angle")), None)
    if angle_id:
        bpyx.gn_set_input(m, angle_id, math.radians(angle))
    ign = next((i for n, i in ids.items() if "ignore" in n.lower()), None)
    if ign:
        bpyx.gn_set_input(m, ign, ignore_sharpness)
    ob.data.shade_smooth()
    ob.update_tag()
    return m


def boolean_apply(target, cutters, *, operation: str = "DIFFERENCE", solver: str = "EXACT", weld: float = 1e-5,
                  dissolve_deg: float = 0.5, remove_cutters: bool = True, recalc_sharp: float | None = 30.0):
    """Булево и очистка «как у hard-surface практиков», но сразу в данные: модификаторы Boolean (по одному на
    резак) → применить → Weld (merge by distance) → растворить вырожденное (limited dissolve 0,5°) → нормали
    наружу → острые рёбра по углу. Резаки удаляются. Возвращает отчёт {tris_before, tris_after, ngons, nonmanifold}.
    [5.2.2]"""
    if not isinstance(cutters, (list, tuple)):
        cutters = [cutters]
    st0 = bpyx.object_stats(target)
    for c in cutters:
        m = bpyx.add_modifier(target, "BOOLEAN", operation=operation, solver=solver, object=c)
        c.hide_render = True
        c.display_type = "WIRE"
    bpyx.apply_modifiers(target)
    bm = bmesh.new()
    bm.from_mesh(target.data)
    if weld:
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=weld)
    if dissolve_deg:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(dissolve_deg), verts=bm.verts[:], edges=bm.edges[:],
                                 delimit={"NORMAL"})
    bmesh.ops.dissolve_degenerate(bm, dist=weld or 1e-6, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    nonman = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
    bm.to_mesh(target.data)
    bm.free()
    if recalc_sharp is not None:
        target.data.shade_smooth()
        target.data.set_sharp_from_angle(angle=math.radians(recalc_sharp))
    target.data.update()
    if remove_cutters:
        for c in cutters:
            d = c.data
            bpy.data.objects.remove(c, do_unlink=True)
            if d is not None and d.users == 0:
                bpy.data.meshes.remove(d)
    st1 = bpyx.object_stats(target)
    return {"tris_before": st0.get("tris"), "tris_after": st1.get("tris"), "ngons": ngons, "nonmanifold": nonman}


# ====================================================================== pivots, маркеры, данные для веба

def set_origin(ob, point_world):
    """Перенести origin (pivot) объекта в мировую точку, не сдвигая геометрию (петля крышки, ось колеса). [5.2.2]"""
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    local = mw.inverted() @ Vector(point_world)
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    ob.data.transform(Matrix.Translation(-local))
    ob.matrix_world = mw @ Matrix.Translation(local)
    for ch in ob.children:
        ch.matrix_parent_inverse = Matrix.Translation(-local) @ ch.matrix_parent_inverse
    bpy.context.view_layer.update()
    return ob


def add_marker(name: str, location, collection=None, *, kind: str = "hotspot", display: str = "SPHERE",
               size: float = 0.02, extras: dict | None = None, parent=None):
    """Пустышка-маркер для JS: имя `<kind>_<name>` (hotspot_, collider_, cam_, pivot_), extras → userData
    (export_extras=True). [5.2.2]"""
    e = bpy.data.objects.new(f"{kind}_{name}", None)
    e.empty_display_type = display
    e.empty_display_size = size
    e.location = location
    for k, v in (extras or {}).items():
        e[k] = v
    (collection or bpy.context.scene.collection).objects.link(e)
    if parent is not None:
        bpy.context.view_layer.update()
        e.parent = parent
        e.matrix_parent_inverse = parent.matrix_world.inverted()
    return e


def surface_points(ob, count: int, seed: int = 0):
    """Равномерная по площади выборка ровно count точек на поверхности вычисленного меша, детерминированно
    (свой генератор: треугольники → площади → random.Random(seed)). Порядок стабилен при одинаковых меше и seed.
    Возвращает список Vector в мировых координатах Blender (Z вверх). [5.2.2]"""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    me.calc_loop_triangles()
    mw = ob.matrix_world
    tris = []
    areas = []
    for lt in me.loop_triangles:
        a, b, c = (mw @ me.vertices[i].co for i in lt.vertices)
        ar = ((b - a).cross(c - a)).length / 2
        tris.append((a, b, c))
        areas.append(ar)
    oe.to_mesh_clear()
    total = sum(areas)
    cum = []
    s = 0.0
    for ar in areas:
        s += ar
        cum.append(s / total)
    rng = random.Random(seed)
    import bisect
    out = []
    for _ in range(count):
        k = bisect.bisect_left(cum, rng.random())
        a, b, c = tris[min(k, len(tris) - 1)]
        u, v = rng.random(), rng.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        out.append(a + (b - a) * u + (c - a) * v)
    return out


def to_three(v):
    """Blender (x, y, z; Z вверх) → three.js (x, z, −y; Y вверх) — как экспорт glTF с export_yup. [5.2.2]"""
    return (v[0], v[2], -v[1])


def export_points_f32(points, path: str):
    """Точки → .bin Float32 little-endian (x, z, −y) — 12 байт на точку, порядок сохраняется. [5.2.2]"""
    import array
    arr = array.array("f")
    for p in points:
        arr.extend(to_three(p))
    if sys.byteorder != "little":
        arr.byteswap()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        arr.tofile(f)
    return {"path": os.path.abspath(path), "count": len(points), "bytes": os.path.getsize(path)}


def export_curve_json(curve_name: str, path: str, samples: int | None = None):
    """Кривая по ИМЕНИ (не active_object) → JSON [[x, z, −y], …] мировых точек вычисленного меша кривой; samples —
    равномерная пересборка по длине. Для CatmullRomCurve3 в three. [5.2.2]"""
    ob = bpy.data.objects[curve_name]
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    # порядок точек сплайна: вершины оценённой кривой без фаски идут по порядку
    pts = [ob.matrix_world @ v.co for v in me.vertices]
    oe.to_mesh_clear()
    cyc = any(sp.use_cyclic_u for sp in ob.data.splines)
    if samples:
        pts = [Vector(p) for p in resample_polyline(pts, samples, closed=cyc)]
    data = {"name": curve_name, "closed": cyc, "points": [[round(c, 6) for c in to_three(p)] for p in pts]}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    json.dump(data, open(path, "w"), ensure_ascii=False)
    return {"path": os.path.abspath(path), "count": len(pts), "closed": cyc}


# ====================================================================== проверки качества и бюджета

def gltf_vertex_estimate(ob) -> dict:
    """Сколько вершин получит glTF: уникальные сочетания (позиция, нормаль угла, UV0) по углам вычисленного меша
    (экспортёр 5.2.40 размножает вершины на швах UV и острых рёбрах). Треугольники — после триангуляции. [5.2.2]"""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    cn = me.corner_normals
    uvl = me.uv_layers.active
    keys = set()
    for i, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        n = cn[i].vector
        k = (round(co.x, 6), round(co.y, 6), round(co.z, 6), round(n.x, 4), round(n.y, 4), round(n.z, 4))
        if uvl is not None:
            u = uvl.uv[i].vector
            k += (round(u.x, 5), round(u.y, 5))
        keys.add(k)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    res = {"blender_verts": len(me.vertices), "gltf_verts_est": len(keys), "tris": tris,
           "ratio": round(len(keys) / max(len(me.vertices), 1), 2)}
    oe.to_mesh_clear()
    return res


def edge_sharpness_report(ob, sharp_deg: float = 30.0) -> dict:
    """Доля «сырых» острых рёбер (двугранный угол > sharp_deg) — признак модели без фасок (M3.2), и средняя длина
    самых коротких рёбер как оценка ширины фаски. Считается по вычисленному мешу. [5.2.2]"""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    oe.to_mesh_clear()
    sharp = 0
    total = 0
    lens = []
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        total += 1
        ang = math.degrees(e.calc_face_angle(0.0))
        if ang > sharp_deg:
            sharp += 1
        lens.append(e.calc_length())
    bm.free()
    lens.sort()
    return {"edges": total, "raw_sharp": sharp, "raw_sharp_share": round(sharp / max(total, 1), 3),
            "edge_len_p10": round(lens[len(lens) // 10], 5) if lens else 0.0}


def part_hierarchy(objects) -> dict:
    """Иерархия форм по частям ассета: наибольший размер каждой части относительно наибольшей части → классы
    крупная (≥ 0,5), средняя (0,15–0,5), мелкая (< 0,15). Правило D1: 1–3 крупные, 3–10 средних, мелких больше, но
    сгруппированы (иерархия «крупная → средняя → мелкая»). [5.2.2]"""
    sizes = []
    for o in objects:
        if o.type not in ("MESH", "CURVE", "FONT"):
            continue
        mn, mx = bpyx.world_bbox([o])
        sizes.append((o.name, max(mx - mn)))
    if not sizes:
        return {}
    big = max(s for _, s in sizes)
    cls = {"primary": [], "secondary": [], "tertiary": []}
    for n, s in sizes:
        r = s / big
        cls["primary" if r >= 0.5 else "secondary" if r >= 0.15 else "tertiary"].append((n, round(r, 3)))
    return {"counts": {k: len(v) for k, v in cls.items()}, "parts": cls}


def silhouette_metrics(png_path: str) -> dict:
    """Метрики силуэта по альфе RGBA-рендера (render_views.py даёт прозрачный фон): заполнение кадра, компактность
    4πA/P² (1 — круг, меньше — сложнее контур), выпуклость A/A_hull (1 — выпуклый «блоб», < 0,85 — есть вырезы и
    выступы), число отверстий. [5.2.2]"""
    import numpy as np
    import OpenImageIO as oiio
    px = oiio.ImageBuf(png_path).get_pixels(oiio.FLOAT)
    a = px[..., 3] > 0.5
    area = float(a.sum())
    if area == 0:
        return {"fill": 0.0}
    h, w = a.shape
    # периметр: число граничных переходов по 4-соседству
    per = float((a[1:, :] != a[:-1, :]).sum() + (a[:, 1:] != a[:, :-1]).sum())
    ys, xs = np.nonzero(a)
    pts = np.stack([xs, ys], 1).astype(np.float64)
    # выпуклая оболочка (монотонная цепь)
    P = sorted(set(map(tuple, pts[:: max(1, len(pts) // 20000)].tolist())) |
               set(map(tuple, pts[np.argsort(xs)[[0, -1]]].tolist())))
    def cross(o, a_, b):
        return (a_[0] - o[0]) * (b[1] - o[1]) - (a_[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in P:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(P):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    hull_area = 0.0
    for i in range(len(hull)):
        x1, y1 = hull[i]
        x2, y2 = hull[(i + 1) % len(hull)]
        hull_area += x1 * y2 - x2 * y1
    hull_area = abs(hull_area) / 2
    # отверстия: связные компоненты фона, не касающиеся края
    try:
        from scipy import ndimage  # noqa
        lab, nlab = ndimage.label(~a)
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        holes = len([i for i in range(1, nlab + 1) if i not in border])
    except Exception:
        holes = None
    return {"fill": round(area / (h * w), 3), "compactness": round(4 * math.pi * area / max(per, 1) ** 2, 3),
            "convexity": round(area / max(hull_area, 1), 3), "holes": holes,
            "bbox_fill": round(area / ((xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)), 3)}


# ====================================================================== студия и камера (паспорт стиля D1)

def stage(objs, *, bg: str = "#E9E7E3", az: float = 35.0, key_warm: str = "#FFF1E0", fill_cool: str = "#E6EEFF",
          world_strength: float = 0.4, backdrop: bool = True, power: float = 1.0, coll_name: str = "STAGE"):
    """Студия D1 (идея C1 proto_lib.studio): key/fill/rim area по радиусу ассета (900 Вт × (d/7)², d = 4r),
    мир и циклорама цвета фона страницы (без линии горизонта — M3.8). [5.2.2]"""
    st = fresh_collection(coll_name)
    mn, mx = bpyx.world_bbox(objs)
    c = (mn + mx) / 2
    r = max((mx - mn).length / 2, 1e-3)
    d = r * 4.0
    k = 900.0 * (d / 7.0) ** 2 * power

    def area(name, a_deg, e_deg, pw, size, hexcol):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = pw
        ld.size = size
        ld.color = bpyx.color(hexcol)[:3]
        lo = bpy.data.objects.new(name, ld)
        st.objects.link(lo)
        a, e = math.radians(a_deg), math.radians(e_deg)
        lo.location = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
        lo.rotation_euler = (c - lo.location).to_track_quat("-Z", "Y").to_euler()
        return lo
    area("Key", az + 45, 45, k, r * 2.5, key_warm)
    area("Fill", az - 70, 20, k * 0.3, r * 3.0, fill_cool)
    area("Rim", az + 170, 50, k * 0.8, r * 1.5, "#FFFFFF")
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    bgn = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bgn.inputs["Color"].default_value = bpyx.color(bg)
    bgn.inputs["Strength"].default_value = world_strength
    if backdrop:
        prof = [(-14 * r, 0.0), (3.5 * r, 0.0)]
        fr = 6.0 * r
        for i in range(1, 13):
            t = math.radians(90 * i / 12)
            prof.append((3.5 * r + fr * math.sin(t), fr * (1 - math.cos(t))))
        prof.append((3.5 * r + fr, 20 * r))
        bm = bmesh.new()
        rows = [(bm.verts.new((-20 * r, y, z)), bm.verts.new((20 * r, y, z))) for y, z in prof]
        for i in range(len(rows) - 1):
            a_, b_ = rows[i], rows[i + 1]
            bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
        bd = obj_from_bm(bm, "Backdrop", st, smooth_angle=180.0)
        bd.location = (c.x, c.y, mn.z)
        bd.rotation_euler = (0, 0, math.radians(az))
        mat, _ = bpyx.principled("D1_Backdrop", base_color=bg, roughness=0.9)
        bpyx.assign_material(bd, mat)
    return st


def frame(objs, *, az: float = 35.0, el: float = 18.0, lens: float = 70.0, margin: float = 1.15,
          res=(1024, 1024), ortho: bool = False, coll=None, shift_y: float = 0.0, fit: bool = True):
    """Камера по габаритам и FOV (не углами «на глаз» — M3.7): направление az/el к центру габаритов, дистанция из
    радиуса описанной сферы. Возвращает камеру (активная камера сцены). [5.2.2]"""
    mn, mx = bpyx.world_bbox(objs)
    c = (mn + mx) / 2
    r = max((mx - mn).length / 2, 1e-4)
    cd = bpy.data.cameras.new("D1_Camera")
    cam = bpy.data.objects.new("D1_Camera", cd)
    (coll or bpy.data.collections.get("STAGE") or bpy.context.scene.collection).objects.link(cam)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    a, e = math.radians(az), math.radians(el)
    dirv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    if ortho:
        cd.type = "ORTHO"
        cam.location = c + dirv * r * 6
        cd.ortho_scale = 2 * r * margin
    else:
        cd.lens = lens
        cd.sensor_fit = "AUTO"
        half = math.atan(cd.sensor_width / 2 / lens)
        aspect = min(res) / max(res)
        dist = r / math.sin(half * (aspect if res[0] >= res[1] else 1.0)) * margin
        cam.location = c + dirv * dist
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cd.shift_y = shift_y
    cd.clip_start = max(r * 0.01, 0.0005)
    cd.clip_end = r * 60
    sc.camera = cam
    if fit and not ortho:            # подогнать по 8 углам габарита (как view3d.camera_to_view_selected)
        bpyx.frame_camera(cam, objs, margin=margin)
    return cam


def render_setup(samples: int = 48, view: str = "AgX", look: str | None = "AgX - Base Contrast",
                 transparent: bool = False, engine: str = "EEVEE"):
    bpyx.set_engine(engine)
    sc = bpy.context.scene
    if sc.render.engine == "BLENDER_EEVEE":
        sc.eevee.taa_render_samples = samples
    else:
        sc.cycles.samples = samples
        sc.cycles.device = "CPU"
    bpyx.set_color_management(view, look=look)
    sc.render.film_transparent = transparent
    return sc


def export_web(path: str, collection_name: str, preset: str = "static_hero", **over):
    """Экспорт коллекции ассета пресетом presets.py (рядом) с collection=…
    (без выделения: use_selection в фоне без выделения даёт пустой GLB). [5.2.2]"""
    E24 = os.path.dirname(os.path.abspath(__file__))  # presets.py — рядом
    if E24 not in sys.path:
        sys.path.insert(0, E24)
    import presets  # noqa
    r = presets.export(path, preset, collection=collection_name, **over)
    if r != {"FINISHED"} or not os.path.exists(path):
        raise RuntimeError(f"export_web {path}: {r}")
    return {"path": os.path.abspath(path), "bytes": os.path.getsize(path)}
