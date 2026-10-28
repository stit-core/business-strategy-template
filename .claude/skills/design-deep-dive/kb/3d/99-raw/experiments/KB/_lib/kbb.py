"""kbb — сборка клавиатуры «Ё» в Blender 5.2.2 (дорожка KB): build(P) в коллекцию ASSET_kb по паспорту kbp (метры).

Колпачок Cherry: клетка (кольца по 20 точек: 4 на сторону + угол) → Subdivision с креасами (кромки юбки острые) → выемка
смещением вершин верха (цилиндрическая, по X) → шток MX крестом и риски А/О → UV «LegendUV» (проекция на верх, 0..1 = верх
колпачка) и «SideUV» (лицевая грань). Повторы — связанными дубликатами (13 прототипов на 68 клавиш), надписи — атлас по
атрибуту объекта (kb_off/kb_scl), материалы — на слоте объекта (link OBJECT): у всех 1u одного ряда один меш.
Корпус — два тела (верх/низ по шву 0,3 мм) кольцами в мировых координатах: стенки вертикальны, верх наклонён на угол набора.
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
import kbp  # noqa: E402

MM = 0.001
ATLAS_DIR = f"{R}/99-raw/experiments/KB/01-build/out"
CH_B = [15, 16, 17, 18, 19, 0]
CH_T = [10, 9, 8, 7, 6, 5]
CH_L = [15, 14, 13, 12, 11, 10]
CH_R = [0, 1, 2, 3, 4, 5]


# ====================================================================== колпачок
def ring20(a, b, d):
    """Кольцо клетки: 4 точки на сторону (прямые участки остаются прямыми после SubD) + точка угла (скругление ≈ 1,4·d)."""
    c = 0.293 * d
    return [(a - c, -(b - c)), (a, -(b - d)), (a, -(b - 2 * d)), (a, b - 2 * d), (a, b - d),
            (a - c, b - c), (a - d, b), (a - 2 * d, b), (-(a - 2 * d), b), (-(a - d), b),
            (-(a - c), b - c), (-a, b - d), (-a, b - 2 * d), (-a, -(b - 2 * d)), (-a, -(b - d)),
            (-(a - c), -(b - c)), (-(a - d), -b), (-(a - 2 * d), -b), (a - 2 * d, -b), (a - d, -b)]


def coons(ring2d):
    """Внутренние точки сетки 5×5 крышки по кольцу из 20 точек (патч Кунса по четырём цепочкам)."""
    B = [ring2d[k] for k in CH_B]
    T = [ring2d[k] for k in CH_T]
    L = [ring2d[k] for k in CH_L]
    Rr = [ring2d[k] for k in CH_R]
    us = [(B[i][0] - B[0][0]) / (B[5][0] - B[0][0]) for i in range(6)]
    vs = [(L[j][1] - L[0][1]) / (L[5][1] - L[0][1]) for j in range(6)]
    P = {}
    for i in range(1, 5):
        for j in range(1, 5):
            u, v = us[i], vs[j]
            p = []
            for c in (0, 1):
                p.append((1 - v) * B[i][c] + v * T[i][c] + (1 - u) * L[j][c] + u * Rr[j][c]
                         - ((1 - u) * (1 - v) * B[0][c] + u * (1 - v) * B[5][c] + (1 - u) * v * T[0][c] + u * v * T[5][c]))
            P[(i, j)] = tuple(p)
    return P


def grid_faces(bm, ring_verts, inner):
    """Грани сетки 5×5: граница — вершины кольца, внутренние — inner[(i, j)]."""
    def V(i, j):
        if j == 0:
            return ring_verts[CH_B[i]]
        if j == 5:
            return ring_verts[CH_T[i]]
        if i == 0:
            return ring_verts[CH_L[j]]
        if i == 5:
            return ring_verts[CH_R[j]]
        return inner[(i, j)]
    for i in range(5):
        for j in range(5):
            bm.faces.new((V(i, j), V(i + 1, j), V(i + 1, j + 1), V(i, j + 1)))


def top_frame(kd):
    th = math.radians(kd["tilt"])
    T0 = Vector((0.0, kd["yoff"], kd["h"]))
    return T0, Vector((1, 0, 0)), Vector((0, math.cos(th), math.sin(th))), Vector((0, -math.sin(th), math.cos(th)))


def keycap_mesh(name, w, profile, homing=False, subd=2, stem=True, inner=True):
    """Прототип колпачка: меш в системе колпачка (0 — низ юбки по центру, Z вверх). Возвращает (mesh, info)."""
    K = kbp.KEYCAP
    kd = kbp.keycap_dims(w, profile)
    T0, xt, yt, zt = top_frame(kd)
    ab, bb, at, bt = kd["wb"] / 2, kd["db"] / 2, kd["wt"] / 2, kd["dt"] / 2
    d_b, d_t = K["corner_b"] / 1.4, K["corner_t"] / 1.4
    bm = bmesh.new()
    crease = bm.edges.layers.float.new("crease_edge")
    bot = [Vector((x, y, 0.0)) for x, y in ring20(ab, bb, d_b)]
    top2 = ring20(at, bt, d_t)
    top = [T0 + xt * x + yt * y for x, y in top2]

    def nrm(i):
        t = bot[(i + 1) % 20] - bot[i - 1]
        return Vector((t.y, -t.x, 0.0)).normalized()
    rings = []
    for s in (0.0, 0.035, 0.5, 0.9, 1.0):
        pts = [bot[i].lerp(top[i], s) + nrm(i) * (4 * s * (1 - s) * K["bulge"]) for i in range(20)]
        rings.append([bm.verts.new(p) for p in pts])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(20):
            bm.faces.new((a[i], a[(i + 1) % 20], b[(i + 1) % 20], b[i]))
    cap_in = {k: bm.verts.new(T0 + xt * x + yt * y) for k, (x, y) in coons(top2).items()}
    grid_faces(bm, rings[-1], cap_in)
    if inner:
        tw = K["wall"]
        ibot = [bm.verts.new((x, y, 0.0)) for x, y in ring20(ab - tw, bb - tw, max(d_b - 0.3 * MM, 0.25 * MM))]
        sc = (kd["h"] - K["ceil"]) / kd["h"]
        ai, bi = ab + (at - ab) * sc - tw, bb + (bt - bb) * sc - tw
        ic2 = ring20(ai, bi, max(d_t * 0.8, 0.4 * MM))
        C0 = T0 - zt * K["ceil"]
        iceil = [bm.verts.new(C0 + xt * x + yt * y) for x, y in ic2]
        for i in range(20):
            bm.faces.new((rings[0][i], rings[0][(i + 1) % 20], ibot[(i + 1) % 20], ibot[i]))
            bm.faces.new((ibot[i], ibot[(i + 1) % 20], iceil[(i + 1) % 20], iceil[i]))
        grid_faces(bm, iceil, {k: bm.verts.new(C0 + xt * x + yt * y) for k, (x, y) in coons(ic2).items()})
        loops = ((rings[0], 1.0), (ibot, 1.0), (iceil, 0.7), (rings[-1], 0.15))
    else:
        loops = ((rings[-1], 0.15),)
    for ring, cval in loops:
        for i in range(20):
            e = bm.edges.get((ring[i], ring[(i + 1) % 20]))
            if e is not None:
                e[crease] = cval
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    tmp = bpy.data.objects.new(name + "_cage", me)
    bpy.context.scene.collection.objects.link(tmp)
    if subd > 0:
        bpyx.add_modifier(tmp, "SUBSURF", levels=subd, render_levels=subd, quality=3, use_creases=True,
                          use_limit_surface=True)
        bpyx.apply_modifiers(tmp)
    me = tmp.data
    bpy.data.objects.remove(tmp, do_unlink=True)
    # выемка: цилиндрическая по X (кромка верха провисает посередине передней/задней стороны — «улыбка» Cherry)
    for v in me.vertices:
        q = Vector(v.co) - T0
        zp = q.dot(zt)
        if zp > -1.3 * MM:
            t = min(1.0, max(0.0, (zp + 1.3 * MM) / (1.3 * MM)))
            wgt = t * t * (3 - 2 * t)
            xp = q.dot(xt)
            dish = kd["dish"] * max(0.0, 1.0 - (xp / at) ** 2)
            v.co = Vector(v.co) - zt * (dish * wgt)
    bm = bmesh.new()
    bm.from_mesh(me)
    extra = []
    if stem:
        K2 = K["stem_cross"]
        ax, aw = K2[0] / 2, K2[1] / 2
        cross = [(ax, -aw), (ax, aw), (aw, aw), (aw, ax), (-aw, ax), (-aw, aw), (-ax, aw), (-ax, -aw), (-aw, -aw),
                 (-aw, -ax), (aw, -ax), (aw, -aw)]
        C0 = T0 - zt * K["ceil"]
        z_ceil = C0.z - C0.y * math.tan(math.radians(kd["tilt"]))
        z0, z1 = K["stem_bottom"], z_ceil + 0.3 * MM
        st = D.extrude_outline(name + "_stem", [D.circle_pts(K["stem_d"] / 2, 32), list(reversed(cross))], z1 - z0,
                               bevel=0.08 * MM, bevel_res=1)
        st.data.transform(Matrix.Translation((0, 0, (z0 + z1) / 2)))
        extra.append(st)
    if homing:
        H = K["homing"]
        hb = D.rounded_slab(name + "_hom", H["len"], H["w"], H["h"], H["w"] / 2 - 1e-5, (0.0, 0.12 * MM),
                            corner_seg=6, edge_seg=3)
        yp = -bt + H["v"] * kd["dt"]
        base = T0 + yt * yp - zt * (kd["dish"] + 0.09 * MM)
        M = Matrix.Translation(base) @ Matrix(((xt.x, yt.x, zt.x, 0), (xt.y, yt.y, zt.y, 0), (xt.z, yt.z, zt.z, 0),
                                               (0, 0, 0, 1)))
        hb.data.transform(M)
        extra.append(hb)
    for ob in extra:
        bm.from_mesh(ob.data)
        d = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(d)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(40))
    # UV: верх колпачка 0..1 (атлас надписей) и лицевая грань (надпись «esc» у Ё)
    lu = me.uv_layers.new(name="LegendUV")
    su = me.uv_layers.new(name="SideUV")
    for loop in me.loops:
        p = Vector(me.vertices[loop.vertex_index].co)
        q = p - T0
        lu.data[loop.index].uv = (q.dot(xt) / kd["wt"] + 0.5, q.dot(yt) / kd["dt"] + 0.5)
        su.data[loop.index].uv = (p.x / kd["wb"] + 0.5, p.z / (10.0 * MM))
    me.uv_layers.active = lu
    me["kb_proto"] = f"{w}u_{profile}" + ("_hom" if homing else "")
    info = dict(kd, top_center=list(T0), wb=kd["wb"])
    return me, info


# ====================================================================== свитч, стабилизатор, пластина, плата
def switch_mesh(name="SwitchProto"):
    S, Dk = kbp.SWITCH, kbp.DECK
    parts = []
    lo = D.rounded_slab(name + "_lo", S["lower"][0], S["lower"][1], Dk["plate_top"] - Dk["pcb_top"], 0.6 * MM,
                        (0.2 * MM, 0.2 * MM), corner_seg=3, edge_seg=1)
    lo.data.transform(Matrix.Translation((0, 0, Dk["pcb_top"])))
    parts.append((lo, 0))
    wb_, wt_ = S["top_b"][0], S["top_t"][0]
    inset = (wb_ - wt_) / 2
    prof = [(0.0, 0.0), (0.0, 0.8 * MM), (inset * 0.55, S["top_h"] * 0.55), (inset, S["top_h"] - 0.4 * MM),
            (inset + 0.4 * MM, S["top_h"])]
    top = D.loft_slab(name + "_top", lambda i: D.rrect_pts(wb_ - 2 * i, wb_ - 2 * i, max(1.4 * MM - i * 0.3, 0.5 * MM), 3),
                      prof, smooth_angle=35)
    top.data.transform(Matrix.Translation((0, 0, Dk["plate_top"])))
    parts.append((top, 0))
    ax, aw = S["stem"][0] / 2, S["stem"][1] / 2
    cross = [(ax, -aw), (ax, aw), (aw, aw), (aw, ax), (-aw, ax), (-aw, aw), (-ax, aw), (-ax, -aw), (-aw, -aw),
             (-aw, -ax), (aw, -ax), (aw, -aw)]
    z0, z1 = Dk["plate_top"] + S["top_h"] - 0.6 * MM, S["stem_top"]
    st = D.extrude_outline(name + "_stem", [cross], z1 - z0, bevel=0.1 * MM, bevel_res=1)
    st.data.transform(Matrix.Translation((0, 0, (z0 + z1) / 2)))
    parts.append((st, 1))
    return merge_parts(name, parts)


def stab_mesh(name, half):
    Dk = kbp.DECK
    parts = []
    for s in (-1, 1):
        h = D.rounded_slab(f"{name}_{s}", 6.4 * MM, 11.0 * MM, 5.4 * MM, 1.0 * MM, (0.3 * MM, 0.5 * MM), corner_seg=3,
                           edge_seg=2)
        h.data.transform(Matrix.Translation((s * half, 0.8 * MM, Dk["plate_top"] - 0.4 * MM)))
        parts.append((h, 0))
        st = D.rounded_slab(f"{name}_st{s}", 4.1 * MM, 1.2 * MM, 4.0 * MM, 0.5 * MM, 0.0, corner_seg=2)
        st.data.transform(Matrix.Translation((s * half, 0, Dk["plate_top"] + 4.5 * MM)))
        parts.append((st, 1))
    wire = bpyx.primitive("cylinder", f"{name}_wire", radius=0.6 * MM, depth=2 * half + 2 * MM, segments=12)
    wire.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))
    wire.data.transform(Matrix.Translation((0, -3.5 * MM, Dk["plate_top"] - 2.2 * MM)))
    parts.append((wire, 2))
    return merge_parts(name, parts)


def merge_parts(name, parts):
    """[(объект, индекс материала)] → один меш (индексы граней = слот материала); временные объекты удаляются."""
    bm = bmesh.new()
    for ob, mi in parts:
        n0 = len(bm.faces)
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f.material_index = mi
        d = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if d.users == 0:
            bpy.data.meshes.remove(d)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(35))
    return me


# ====================================================================== корпус (мировые координаты, две части по шву)
def case_frames():
    cd = kbp.case_dims()
    C = kbp.CASE
    a = math.radians(C["angle"])
    D_ = cd["D"]

    def top(y):
        return C["h_front"] + (y + D_ / 2) * math.tan(a)
    M_deck = Matrix.Translation((0, 0, top(0.0))) @ Matrix.Rotation(a, 4, "X")
    return cd, a, top, M_deck


def loft(bm, rings, closed=False, mats=None, cap_first=False, cap_last=False):
    """Кольца (списки Vector одинаковой длины) → квады между соседними; closed — последнее кольцо соединяется с первым."""
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    pairs = list(zip(vs[:-1], vs[1:])) + ([(vs[-1], vs[0])] if closed else [])
    for bi, (A, B) in enumerate(pairs):
        for i in range(n):
            f = bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
            if mats:
                f.material_index = mats[bi]
    if cap_first:
        bm.faces.new(list(reversed(vs[0])))
    if cap_last:
        bm.faces.new(vs[-1])
    return vs


def case_meshes(seg=16):
    cd, a, top, M_deck = case_frames()
    C = kbp.CASE
    W, D_ = cd["W"], cd["D"]
    sd = C["seam_depth"]

    def outline(inset):
        return D.rrect_pts(W - 2 * inset, D_ - 2 * inset, C["corner"] - inset, seg)

    def seam(y):
        return top(y) - sd / math.cos(a)

    def ring_z(inset, zf):
        return [Vector((x, y, zf(y))) for x, y in outline(inset)]

    def well(expand, zd):
        ww, wd = cd["well"]
        pts = D.rrect_pts(ww + 2 * expand, wd + 2 * expand, C["well_corner"] + expand, seg)
        return [M_deck @ Vector((x, y + cd["well_cy"], zd)) for x, y in pts]
    v = C["seam_v"]
    ch = C["chamfer"]
    # верхняя часть: шов → стенка → фаска → верх → фаска колодца → стенка колодца до шва → низ рамки по плоскости шва
    rings_t = [ring_z(v, seam), ring_z(0.0, lambda y: seam(y) + v), ring_z(0.0, lambda y: top(y) - ch),
               ring_z(ch, top), well(C["well_chamfer"], 0.0), well(0.0, -C["well_chamfer"]), well(0.0, -sd)]
    bm = bmesh.new()
    loft(bm, rings_t, closed=True, mats=[0, 0, 1, 0, 1, 0, 0])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me_t = bpy.data.meshes.new("Case_Top")
    bm.to_mesh(me_t)
    bm.free()
    # нижняя часть: дно → скругление → стенка → шов → плоскость шва → стенка колодца → пол колодца
    fb = C["bottom_fillet"]
    fh = C["foot_h"]
    floor_z = fh + C["floor_skin"]
    rings_b = [ring_z(fb, lambda y: fh), ring_z(fb * 0.293, lambda y: fh + fb * 0.293), ring_z(0.0, lambda y: fh + fb),
               ring_z(0.0, lambda y: seam(y) - v), ring_z(v, seam), well(0.0, -sd),
               [Vector((p.x, p.y, floor_z)) for p in well(0.0, -sd)]]      # дно параллельно столу (сзади глубже — под плиту)
    bm = bmesh.new()
    loft(bm, rings_b, cap_first=True, cap_last=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me_b = bpy.data.meshes.new("Case_Bottom")
    bm.to_mesh(me_b)
    bm.free()
    for me in (me_t, me_b):
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(30))
    return me_t, me_b


# ====================================================================== материалы (режим предрендера; веб — отдельно)
def _img(path, colorspace="Non-Color"):
    im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = colorspace
    return im


def _noise(nt, scale, detail=2.0, coord="Object"):
    tc = bpyx.find_node(nt, "TEX_COORD") or nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs[coord], n.inputs["Vector"])
    return n


def _bump(nt, bsdf, height_socket, strength, distance):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height_socket, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return b


def _mix(nt, fac, a, b):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    nt.links.new(fac, m.inputs[0])
    for sock_name, val in (("A", a), ("B", b)):
        s = bpyx.sock(m, sock_name)
        if isinstance(val, tuple):
            s.default_value = val
        else:
            nt.links.new(val, s)
    return m


def keycap_material(name, role, cw, atlas_meta=None):
    """PBT: цвет + надписи атласом (маски R/G → цвета расцветки), зерно в шероховатость и рельеф, лёгкое подповерхностное."""
    mat, bsdf = bpyx.principled(name, base_color=cw[role if role != "accent" else "accent"], roughness=0.58,
                                reuse=False)
    nt = mat.node_tree
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "LegendUV"
    base_col = bpyx.color(cw["accent"] if role == "accent" else cw[role])
    if role == "accent":
        m = kbp.KEYCAP
        kd = kbp.keycap_dims(1, "R1")
        mg = 4.5 * MM
        scl = (kd["wt"] / (kd["wt"] + 2 * mg), kd["dt"] / (kd["dt"] + 2 * mg), 1.0)
        off = (mg / (kd["wt"] + 2 * mg), mg / (kd["dt"] + 2 * mg), 0.0)
        vm = nt.nodes.new("ShaderNodeVectorMath")
        vm.operation = "MULTIPLY_ADD"
        nt.links.new(uv.outputs["UV"], vm.inputs[0])
        vm.inputs[1].default_value = scl
        vm.inputs[2].default_value = off
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _img(f"{ATLAS_DIR}/yo_top.png")
        tex.extension = "CLIP"
        tex.interpolation = "Cubic"
        nt.links.new(vm.outputs["Vector"], tex.inputs["Vector"])
        suv = nt.nodes.new("ShaderNodeUVMap")
        suv.uv_map = "SideUV"
        stex = nt.nodes.new("ShaderNodeTexImage")
        stex.image = _img(f"{ATLAS_DIR}/yo_side.png")
        stex.extension = "CLIP"
        stex.interpolation = "Cubic"
        nt.links.new(suv.outputs["UV"], stex.inputs["Vector"])
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Normal"], sep.inputs["Vector"])
        front = nt.nodes.new("ShaderNodeMath")
        front.operation = "LESS_THAN"
        nt.links.new(sep.outputs["Y"], front.inputs[0])
        front.inputs[1].default_value = -0.55
        side = nt.nodes.new("ShaderNodeMath")
        side.operation = "MULTIPLY"
        nt.links.new(front.outputs["Value"], side.inputs[0])
        nt.links.new(stex.outputs["Color"], side.inputs[1])
        lg = nt.nodes.new("ShaderNodeMath")
        lg.operation = "MAXIMUM"
        nt.links.new(tex.outputs["Color"], lg.inputs[0])
        nt.links.new(side.outputs["Value"], lg.inputs[1])
        mix = _mix(nt, lg.outputs["Value"], base_col, bpyx.color(cw["legend_accent"]))
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        a1 = nt.nodes.new("ShaderNodeAttribute")
        a1.attribute_type = "OBJECT"
        a1.attribute_name = "kb_scl"
        a2 = nt.nodes.new("ShaderNodeAttribute")
        a2.attribute_type = "OBJECT"
        a2.attribute_name = "kb_off"
        vm = nt.nodes.new("ShaderNodeVectorMath")
        vm.operation = "MULTIPLY_ADD"
        nt.links.new(uv.outputs["UV"], vm.inputs[0])
        nt.links.new(a1.outputs["Vector"], vm.inputs[1])
        nt.links.new(a2.outputs["Vector"], vm.inputs[2])
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = _img(f"{ATLAS_DIR}/atlas_legends.png")
        tex.extension = "CLIP"
        tex.interpolation = "Cubic"
        nt.links.new(vm.outputs["Vector"], tex.inputs["Vector"])
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tex.outputs["Color"], sep.inputs["Color"])
        m1 = _mix(nt, sep.outputs["Red"], base_col, bpyx.color(cw["legend1"]))
        m2 = _mix(nt, sep.outputs["Green"], m1.outputs["Result"], bpyx.color(cw["legend2"]))
        nt.links.new(m2.outputs["Result"], bsdf.inputs["Base Color"])
    # фактура PBT: зерно ≈ 0,05–0,1 мм, шероховатость 0,52–0,64
    n1 = _noise(nt, 9000.0, 3.0)
    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.3, 0.7
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.52, 0.64
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _bump(nt, bsdf, n1.outputs["Fac"], 0.12, 0.00002)
    light = sum(base_col[:3]) / 3 > 0.3
    bsdf.inputs["Subsurface Weight"].default_value = 0.04 if light else 0.0
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.85, 0.7)
    bsdf.inputs["Subsurface Scale"].default_value = 0.0012
    bsdf.inputs["IOR"].default_value = 1.54
    mat["kb_role"] = role
    return mat


def metal_material(name, color_lin, rough, grain=0.0, grain_scale=24000.0):
    mat, bsdf = bpyx.principled(name, base_color=(*color_lin, 1.0), metallic=1.0, roughness=rough, reuse=False)
    if grain > 0:
        nt = mat.node_tree
        n = _noise(nt, grain_scale, 2.0)
        _bump(nt, bsdf, n.outputs["Fac"], grain, 0.00002)
        mr = nt.nodes.new("ShaderNodeMapRange")
        nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = rough - 0.05, rough + 0.05
        nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    return mat


def plastic(name, hexcol, rough, **kw):
    return bpyx.principled(name, base_color=hexcol, roughness=rough, reuse=False, **kw)[0]


def materials(cw):
    M = {}
    M["alpha"] = keycap_material("KC_alpha", "alpha", cw)
    M["mod"] = keycap_material("KC_mod", "mod", cw)
    M["accent"] = keycap_material("KC_accent", "accent", cw)
    M["case"] = metal_material("Case_Body", cw["case"], 0.52, grain=0.14)   # пескоструй: 0,47–0,57 и зерно ~0,04 мм
    M["chamfer"] = metal_material("Case_Chamfer", cw["case"], 0.08)
    M["plate"] = metal_material("Plate", cw["plate"], 0.50, grain=0.08)
    M["sw"] = plastic("Switch_Housing", cw["switch"], 0.42)
    M["stem"] = plastic("Switch_Stem", "#EDE4CF", 0.35)
    M["wire"] = metal_material("Stab_Wire", (0.8, 0.8, 0.82), 0.25)
    M["pcb"] = plastic("PCB", "#15171A", 0.5)
    M["brass"] = metal_material("Brass", kbp.BRASS, 0.28, grain=0.04, grain_scale=15000.0)
    M["silicone"] = plastic("Silicone", "#2A2A2B", 0.85, specular_ior_level=0.35)
    M["port"] = plastic("Port", "#0E0F10", 0.6)
    return M


def brass_mark(mat, img="brass_mark.png", w=60 * MM, h=7 * MM, axes=("X", "Z")):
    """Гравировка марки на латуни: маска (проекция осей объекта) → рельеф (только предрендер)."""
    nt = mat.node_tree
    bsdf = bpyx.find_node(nt, "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mu = nt.nodes.new("ShaderNodeMath")
    mu.operation = "MULTIPLY_ADD"
    nt.links.new(sep.outputs[axes[0]], mu.inputs[0])
    mu.inputs[1].default_value, mu.inputs[2].default_value = 1 / w, 0.5
    mv = nt.nodes.new("ShaderNodeMath")
    mv.operation = "MULTIPLY_ADD"
    nt.links.new(sep.outputs[axes[1]], mv.inputs[0])
    mv.inputs[1].default_value, mv.inputs[2].default_value = 1 / h, 0.5
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(mu.outputs["Value"], cmb.inputs["X"])
    nt.links.new(mv.outputs["Value"], cmb.inputs["Y"])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = _img(f"{ATLAS_DIR}/{img}")
    tex.extension = "CLIP"
    nt.links.new(cmb.outputs["Vector"], tex.inputs["Vector"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(tex.outputs["Color"], inv.inputs[1])
    _bump(nt, bsdf, inv.outputs["Value"], 0.6, 0.00015)


# ====================================================================== сборка
def build(P=None, colorway="snow", subd=2, coll_name="ASSET_kb"):
    """Идемпотентная сборка в коллекцию coll_name. Возвращает словарь объектов и чисел."""
    cw = kbp.COLORWAYS[colorway]
    C = D.fresh_collection(coll_name)
    hidden = D.fresh_collection("glTF_not_exported")
    M = materials(cw)
    cd, a, top, M_deck = case_frames()
    root = bpy.data.objects.new("KB_root", None)
    C.objects.link(root)
    deck = bpy.data.objects.new("KB_deck", None)
    C.objects.link(deck)
    deck.parent = root
    deck.matrix_world = M_deck
    import json
    atlas = json.load(open(f"{ATLAS_DIR}/atlas_legends.json"))
    protos = {}
    keys = kbp.keys()
    objs = {"keys": {}, "switches": {}}
    Dk = kbp.DECK
    for k in keys:
        pk = (k["w"], k["profile"], k["homing"])
        if pk not in protos:
            protos[pk] = keycap_mesh(f"KC_{k['w']}u_{k['profile']}{'_hom' if k['homing'] else ''}", k["w"], k["profile"],
                                     homing=k["homing"], subd=subd)
            protos[pk][0].materials.append(M["alpha"])
        me, info = protos[pk]
        ob = bpy.data.objects.new(f"Key_{k['id']}", me)
        C.objects.link(ob)
        ob.parent = deck
        ob.location = (k["cx"], k["cy"], Dk["keycap_bottom"])
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = M[k["role"]]
        cell = atlas["keys"][k["id"]]
        ob["kb_off"] = (cell["off"][0], cell["off"][1], 0.0)
        ob["kb_scl"] = (cell["scl"][0], cell["scl"][1], 0.0)
        ob["kb_code"] = k["code"]
        ob["kb_row"] = k["row"]
        objs["keys"][k["id"]] = ob
    # свитчи и стабилизаторы
    sw_me = switch_mesh()
    sw_me.materials.append(M["sw"])
    sw_me.materials.append(M["stem"])
    for k in keys:
        ob = bpy.data.objects.new(f"Sw_{k['id']}", sw_me)
        C.objects.link(ob)
        ob.parent = deck
        ob.location = (k["cx"], k["cy"], 0.0)
        objs["switches"][k["id"]] = ob
        half = kbp.STAB.get(k["w"])
        if half:
            st_me = stab_mesh(f"Stab_{k['id']}", half)
            for m_ in (M["sw"], M["stem"], M["wire"]):
                st_me.materials.append(m_)
            so = bpy.data.objects.new(f"Stab_{k['id']}", st_me)
            C.objects.link(so)
            so.parent = deck
            so.location = (k["cx"], k["cy"], 0.0)
    # пластина с вырезами под свитчи и стабилизаторы
    ww, wd = cd["well"]
    oy = cd["well_cy"]
    loops = [[(x, y + oy) for x, y in D.rrect_pts(ww - 0.4 * MM, wd - 0.4 * MM, 1.2 * MM, 6)]]
    cut = kbp.SWITCH["plate_cut"]
    for k in keys:
        loops.append([(k["cx"] + x, k["cy"] + y) for x, y in reversed(D.rrect_pts(cut, cut, 0.3 * MM, 2))])
        half = kbp.STAB.get(k["w"])
        if half:
            for s in (-1, 1):
                loops.append([(k["cx"] + s * half + x, k["cy"] + 0.8 * MM + y)
                              for x, y in reversed(D.rrect_pts(6.8 * MM, 12.2 * MM, 0.5 * MM, 2))])
    plate = D.extrude_outline("Plate", loops, Dk["plate_t"], C, bevel=0.12 * MM, bevel_res=1)
    plate.data.transform(Matrix.Translation((0, 0, Dk["plate_top"] - Dk["plate_t"] / 2)))
    bpyx.assign_material(plate, M["plate"])
    plate.parent = deck
    pcb = D.rounded_slab("PCB", ww - 2.0 * MM, wd - 2.0 * MM, Dk["pcb_t"], 1.0 * MM, (0.1 * MM, 0.1 * MM), C,
                         corner_seg=4, edge_seg=1)
    pcb.location = (0, oy, Dk["pcb_top"] - Dk["pcb_t"])
    bpyx.assign_material(pcb, M["pcb"])
    pcb.parent = deck
    # корпус
    me_t, me_b = case_meshes()
    for me, nm in ((me_t, "Case_Top"), (me_b, "Case_Bottom")):
        me.materials.append(M["case"])
        me.materials.append(M["chamfer"])
        ob = bpy.data.objects.new(nm, me)
        C.objects.link(ob)
        ob.parent = root
        D.hard_surface(ob, bevel_width=kbp.CASE["micro_bevel"], segments=2, angle=35)
        objs[nm] = ob
    # латунь: полоса-вставка на задней грани (выступ 0,3 мм, марка «Ё · 65») и грузик-плита 200 × 40 × 6 мм (≈ 408 г) на дне
    Wt = kbp.WEIGHT
    wt = D.rounded_slab("Brass_Strip", Wt["strip_w"], Wt["strip_h"], 1.2 * MM, Wt["corner"], (0.25 * MM, 0.25 * MM), C,
                        corner_seg=6, edge_seg=2)
    wt.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))           # лицо — назад (+Y)
    wt.location = (0, cd["D"] / 2 + Wt["strip_proud"], kbp.CASE["foot_h"] + kbp.CASE["bottom_fillet"] + 1.2 * MM
                   + Wt["strip_h"] / 2)
    smat = M["brass"].copy()
    smat.name = "Brass_Strip"
    brass_mark(smat)
    bpyx.assign_material(wt, smat)
    wt.parent = root
    plate_w = D.rounded_slab("Weight", Wt["w"], Wt["d"], Wt["t"], Wt["corner"], (0.4 * MM, 0.4 * MM), C, corner_seg=6,
                             edge_seg=2)
    plate_w.location = (0, Wt["y_center"], kbp.CASE["foot_h"] + kbp.CASE["floor_skin"] + 0.1 * MM)   # зазор 0,1 мм над дном (не компланарно)
    wmat = M["brass"].copy()
    wmat.name = "Brass_Weight"
    brass_mark(wmat, "brass_plate_mark.png", 80 * MM, 26 * MM, ("X", "Y"))
    bpyx.assign_material(plate_w, wmat)
    plate_w.parent = root
    # USB-C сзади слева
    U_ = kbp.CASE["usb"]
    port = D.rounded_slab("USB_C", U_["w"], U_["h"], 1.0 * MM, U_["h"] / 2 - 1e-5, (0.2 * MM, 0.2 * MM), C,
                          corner_seg=8, edge_seg=2)
    port.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))
    port.location = (U_["x"], cd["D"] / 2 + 0.02 * MM, top(cd["D"] / 2) - U_["below_top"])
    bpyx.assign_material(port, M["port"])
    port.parent = root
    # ножки
    F = kbp.FEET
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = D.rounded_slab(f"Foot_{'L' if sx < 0 else 'R'}{'F' if sy < 0 else 'B'}", F["d"], F["d"],
                               kbp.CASE["foot_h"] + 0.2 * MM, F["d"] / 2 - 1e-5, (0.6 * MM, 0.0), C, corner_seg=6,
                               edge_seg=2)
            f.location = (sx * (cd["W"] / 2 - F["inset"][0]), sy * (cd["D"] / 2 - F["inset"][1]), 0.0)
            bpyx.assign_material(f, M["silicone"])
            f.parent = root
    # фокус-пустышка на верху Ё (для ГРИП и для кода: имя hotspot_yo)
    kyo = objs["keys"]["yo"]
    info = protos[(1, "R1", False)][1]
    e = bpy.data.objects.new("hotspot_yo", None)
    C.objects.link(e)
    e.parent = kyo
    e.location = Vector(info["top_center"]) - Vector((0, 0, info["dish"]))
    e.empty_display_size = 0.005
    bpy.context.view_layer.update()
    objs.update(root=root, deck=deck, plate=plate, pcb=pcb, weight=plate_w, strip=wt, port=port, focus=e, materials=M,
                protos={f"{k[0]}u_{k[1]}{'_hom' if k[2] else ''}": v[0].name for k, v in protos.items()})
    return objs


def apply_colorway(M, colorway):
    """Сменить расцветку на месте: значения входов материалов (надписи — те же маски атласа)."""
    cw = kbp.COLORWAYS[colorway]
    for role in ("alpha", "mod", "accent"):
        nt = M[role].node_tree
        mixes = [n for n in nt.nodes if n.bl_idname == "ShaderNodeMix"]
        base = bpyx.color(cw["accent"] if role == "accent" else cw[role])
        if role == "accent":
            bpyx.sock(mixes[0], "A").default_value = base
            bpyx.sock(mixes[0], "B").default_value = bpyx.color(cw["legend_accent"])
        else:
            m1 = next(m for m in mixes if not bpyx.sock(m, "A").is_linked)
            m2 = next(m for m in mixes if bpyx.sock(m, "A").is_linked)
            bpyx.sock(m1, "A").default_value = base
            bpyx.sock(m1, "B").default_value = bpyx.color(cw["legend1"])
            bpyx.sock(m2, "B").default_value = bpyx.color(cw["legend2"])
        bsdf = bpyx.find_node(nt, "BSDF_PRINCIPLED")
        bsdf.inputs["Subsurface Weight"].default_value = 0.04 if sum(base[:3]) / 3 > 0.3 else 0.0
    for key, col in (("case", cw["case"]), ("chamfer", cw["case"]), ("plate", cw["plate"])):
        bpyx.find_node(M[key].node_tree, "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (*col, 1.0)
    bpyx.find_node(M["sw"].node_tree, "BSDF_PRINCIPLED").inputs["Base Color"].default_value = bpyx.color(cw["switch"])


# ====================================================================== разборка слоями (тот же закон, что у JS в A/C)
def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def layer_of(ob):
    n = ob.name
    if n.startswith("Key_") or n == "hotspot_yo":
        return "keycaps"
    if n.startswith("Sw_"):
        return "switches"
    if n.startswith("Stab_"):
        return "stabs"
    if n == "Plate":
        return "plate"
    if n == "PCB":
        return "pcb"
    if n == "Weight":
        return "weight"
    return None


def apply_explode(p, coll_name="ASSET_kb"):
    """p ∈ [0, 1] — доля прокрутки сцены: слой L поднимается на EXPLODE[L]·smooth((p − a)/(b − a)) по нормали деки."""
    deck = bpy.data.objects["KB_deck"]
    n_deck = (deck.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    E, RG = kbp.EXPLODE, kbp.EXPLODE_RANGES
    for ob in bpy.data.collections[coll_name].all_objects:
        L = layer_of(ob)
        if L is None or ob.name == "hotspot_yo":
            continue
        a, b = RG[L]
        d = E[L] * (_smooth((p - a) / (b - a)) if b > a else 0.0)
        base = ob.get("kb_base")
        if base is None:
            ob["kb_base"] = list(ob.location)
            base = ob["kb_base"]
        base = Vector(base)
        if ob.parent is not None and ob.parent.name == "KB_deck":
            ob.location = base + Vector((0, 0, d))
        else:
            ob.location = base + n_deck * d
    bpy.context.view_layer.update()
