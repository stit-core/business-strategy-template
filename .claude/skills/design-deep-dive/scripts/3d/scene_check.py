# Blender 5.2.2 — scene_check.py: проверка сцены и ассета кодом, одна строка JSON.
# Объединяет scene_audit.py + passport_asserts.py + метрики d1lib (доля острых рёбер, иерархия частей).
# Совместим с BLENDER_MCP_SAFE_MODE (нет sys/os/open/lambda/class/global): можно отправить текстом в execute_blender_code.
# Паспорт: заменить PASSPORT = None на dict ИЛИ положить JSON в свойство коллекции ASSET_*: coll["passport"] = json.dumps(P).
# Запуск в фоне с аргументами — через qa_pipeline.py: python3 scripts/3d/qa_pipeline.py scene file.blend [--passport p.json]
# Вывод: последняя строка "SCENE_CHECK {json}": verdict (fail/review/pass), issues [{code, level, m, obj, msg}], metrics.
# Пороги откалиброваны на 32 сценах.
import bpy
import bmesh
import json
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PASSPORT = None
OPTS = {}

DEFAULTS = {
    "touch_m": 0.001,          # «касается»: зазор ≤ 1 мм
    "touch_rel": 0.002,        # … или ≤ 0,2 % диагонали ассета (крупные сцены)
    "dims_tol": 0.05,          # габариты против паспорта ±5 %
    "sharp_deg": 85.0,         # «сырое» ребро: двугранный угол > 85°
    "sharp_share": 0.10,       # доля видимых сырых рёбер (по длине) у объекта без фасок, выше — флаг
    "inside_hidden": 0.98,     # доля площади части внутри другой: ≥ 0,98 — спрятанная внутренняя деталь
    "stage_ratio": 3.0,        # подложка: плоский меш в ≥ 3 раза шире остального или is_shadow_catcher
    "frame_min_area": 0.08, "frame_max_area": 0.90, "center_tol": 0.20, "margin_min": 0.02,
    "huge_m": 30.0, "tiny_m": 0.02, "max_tris": 150000, "max_draw_calls": 100, "max_materials": 12,
    "max_tex_px": 2048, "sample_verts": 3000,
}

M_CODE = {
    "unapplied_scale": "M2.10", "negative_scale": "M2.10", "origin_far": "M2.9", "origins_at_world_zero": "M1.9",
    "floating_part": "M2.2", "floating_allowed": "M2.2", "hidden_inside": "M2.3", "embedded_joint": "M2.3",
    "ngons": "M2.7", "ngons_nonplanar": "M2.7", "nonmanifold": "M2.8", "double_verts": "M2.8", "loose_geometry": "M2.8",
    "inverted_normals": "M2.6", "degenerate_faces": "M2.8", "raw_sharp_edges": "M3.2", "smooth_across_hard_edges": "M3.3",
    "faceted_curved": "M3.3", "default_names": "M3.1", "text_not_converted": "M2.12", "no_material": "M3.5",
    "default_gray": "M3.5", "viewport_only_color": "M4.8", "procedural_textures": "M4.1", "many_materials": "M4.10",
    "big_textures": "M5.2", "no_lights": "M3.4", "single_sun_only": "M3.4", "no_camera": "M3.7", "not_in_frame": "M3.7",
    "cropped": "M3.7", "too_small_in_frame": "M3.7", "too_big_in_frame": "M3.7", "tight_margin": "M3.7",
    "off_center": "M3.7", "huge_scale": "M2.1", "tiny_scale": "M2.1", "heavy_mesh": "M5.2", "many_draw_calls": "M5.3",
    "dims_mismatch": "M2.1", "not_touching": "M2.2", "over_budget_tris": "M5.2", "over_budget_materials": "M4.10",
    "not_on_ground": "M2.2", "default_cube_left": "M6.6", "stage_objects": "M5.4",
}

DEFAULT_PREFIXES = ("Cube", "Sphere", "Cylinder", "Cone", "Torus", "Plane", "Circle", "Icosphere", "Text",
                    "Suzanne", "Mesh", "BezierCurve", "NurbsPath", "Grid")
# ноды, которые не переживают экспорт glTF (= LOST_NODES из preflight_block.py, 08-export-gltf/04 §5)
PROCEDURAL = {"TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MAGIC", "TEX_GRADIENT", "TEX_CHECKER", "TEX_BRICK",
              "TEX_WHITE_NOISE", "TEX_GABOR", "LAYER_WEIGHT", "FRESNEL", "BUMP", "VALTORGB", "HUE_SAT",
              "BRIGHTCONTRAST", "GAMMA", "INVERT", "CURVE_RGB", "AMBIENT_OCCLUSION", "SHADERTORGB", "WIREFRAME",
              "BEVEL", "TEX_ENVIRONMENT", "TEX_SKY", "DISPLACEMENT"}
GEO_TYPES = ("MESH", "CURVE", "FONT", "SURFACE", "META")


def opt(k):
    return OPTS[k] if k in OPTS else DEFAULTS[k]


def aabb_of(points):
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi


def aabb_gap(a, b):
    d = 0.0
    for i in range(3):
        g = max(b[0][i] - a[1][i], a[0][i] - b[1][i], 0.0)
        d += g * g
    return math.sqrt(d)


def principled_of(mat):
    if mat is None or mat.node_tree is None:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


def tree_nodes(tree, depth):
    out = []
    if tree is None or depth > 4:
        return out
    for n in tree.nodes:
        out.append(n)
        if n.type == "GROUP" and n.node_tree is not None:
            out += tree_nodes(n.node_tree, depth + 1)
    return out


def world_bmesh(ob, dg):
    """Вычисленный меш объекта в мировых координатах (модификаторы, текст и кривые — уже меш)."""
    oe = ob.evaluated_get(dg)
    try:
        me = oe.to_mesh()
    except RuntimeError:
        return None
    if me is None:
        return None
    bm = bmesh.new()
    bm.from_mesh(me)
    oe.to_mesh_clear()
    bm.transform(ob.matrix_world)
    return bm


def see_through(ob):
    """Материал пропускает свет (Alpha < 1 или Transmission > 0) — внутренняя деталь видна."""
    for sl in ob.material_slots:
        p = principled_of(sl.material)
        if p is None:
            continue
        a = p.inputs["Alpha"]
        t = p.inputs["Transmission Weight"]
        if a.is_linked or a.default_value < 0.999 or t.is_linked or t.default_value > 0.001:
            return True
    return False


def box_inside(a, b, parts):
    """Габаритная коробка части a целиком внутри коробки части b."""
    for i in range(3):
        if parts[a]["lo"][i] < parts[b]["lo"][i] or parts[a]["hi"][i] > parts[b]["hi"][i]:
            return False
    return True


def sample(seq, n):
    step = max(1, len(seq) // max(n, 1))
    return seq[::step]


def mesh_distance(a, b, parts):
    """Минимальный зазор между поверхностями частей a и b (0 — пересекаются), по вершинам в обе стороны."""
    ta = parts[a]["bvh"]
    tb = parts[b]["bvh"]
    if ta.overlap(tb):
        return 0.0
    best = 1e18
    for v in parts[a]["sample"]:
        hit = tb.find_nearest(v)
        if hit[0] is not None and hit[3] < best:
            best = hit[3]
    for v in parts[b]["sample"]:
        hit = ta.find_nearest(v)
        if hit[0] is not None and hit[3] < best:
            best = hit[3]
    return best


RAY_DIR = Vector((0.5773, 0.5774, 0.5775))


def point_inside(tree, pt):
    """Точка внутри замкнутого меша: нечётное число пересечений луча (не зависит от направления нормалей)."""
    n = 0
    o = pt.copy()
    for k in range(64):
        hit = tree.ray_cast(o, RAY_DIR)
        if hit[0] is None:
            break
        n += 1
        o = hit[0] + RAY_DIR * 1e-6
    return n % 2 == 1


def inside_share(a, b, parts):
    """Доля части a внутри замкнутой части b: минимум из доли площади (центры граней) и доли вершин; глубина, м.
    Только вершины нельзя: у вставленного цилиндра или ребра половина вершин всегда внутри;
    только центры нельзя: у плоскости из одной грани центр может попасть внутрь, а углы — нет."""
    if not parts[b]["closed"]:
        return 0.0, 0.0
    tb = parts[b]["bvh"]
    a_in = 0.0
    a_all = 0.0
    depth = 0.0
    for c, area in parts[a]["centers"]:
        a_all += area
        if point_inside(tb, c):
            a_in += area
            hit = tb.find_nearest(c)
            if hit[0] is not None and hit[3] > depth:
                depth = hit[3]
    share = a_in / a_all if a_all else 0.0
    if share > 0:                             # крупная грань: центр внутри, углы снаружи — проверить и вершины
        pts = parts[a]["sample"]
        v_in = sum(1 for v in pts if point_inside(tb, v))
        share = min(share, v_in / len(pts) if pts else 0.0)
    return share, depth


def analyze_mesh(bm):
    """Топология и затенение одной части (bm в мировых координатах; меняется: сварка 0,01 мм)."""
    r = {}
    dbl = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=1e-5)["targetmap"]
    r["double_verts"] = len(dbl)
    if dbl:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.normal_update()
    tris = 0
    ngons = 0
    nonplanar = 0
    degenerate = 0
    for f in bm.faces:
        k = len(f.verts)
        tris += k - 2
        area = f.calc_area()
        if area < 1e-12:
            degenerate += 1
            continue
        if k > 4:
            ngons += 1
            c = f.calc_center_median()
            dev = max(abs((v.co - c).dot(f.normal)) for v in f.verts)
            if dev > 0.01 * math.sqrt(area):
                nonplanar += 1
    nonman = 0
    boundary = 0
    loose_e = 0
    sharp_len = 0.0
    tot_len = 0.0
    sharp30 = 0
    n2 = 0
    smooth_hard = 0
    gentle = 0
    hard = []
    for e in bm.edges:
        lf = len(e.link_faces)
        if lf == 0:
            loose_e += 1
            continue
        if lf == 1:
            boundary += 1
        elif lf > 2:
            nonman += 1
        if lf == 2:
            n2 += 1
            ln = e.calc_length()
            tot_len += ln
            ang = math.degrees(e.calc_face_angle(0.0))
            if ang > 30.0:
                sharp30 += 1
            if ang > opt("sharp_deg"):
                sharp_len += ln
                hard.append((e.verts[0].co.lerp(e.verts[1].co, 0.5), ln, "S",
                             (e.link_faces[0].normal + e.link_faces[1].normal).normalized()))
            if 5.0 < ang <= 30.0:
                gentle += 1
            if ang > 80.0 and e.smooth and e.link_faces[0].smooth and e.link_faces[1].smooth:
                smooth_hard += 1
                hard.append((e.verts[0].co.lerp(e.verts[1].co, 0.5), ln, "H",
                             (e.link_faces[0].normal + e.link_faces[1].normal).normalized()))
    loose_v = sum(1 for v in bm.verts if not v.link_edges)
    nf = len(bm.faces)
    smooth_faces = sum(1 for f in bm.faces if f.smooth)
    flipped = 0
    closed = nf > 0 and boundary == 0 and nonman == 0
    if closed:
        bm2 = bm.copy()
        bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
        bm2.faces.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        for i in range(nf):
            if bm.faces[i].normal.dot(bm2.faces[i].normal) < 0:
                flipped += 1
        bm2.free()
    r.update(tris=tris, faces=nf, verts=len(bm.verts), ngons=ngons, ngons_nonplanar=nonplanar, degenerate=degenerate,
             nonmanifold=nonman, boundary=boundary, loose=loose_e + loose_v, flipped=flipped, closed=closed,
             sharp_len_share=round(sharp_len / tot_len, 3) if tot_len else 0.0,
             sharp30_share=round(sharp30 / n2, 3) if n2 else 0.0, smooth_across_hard=smooth_hard,
             gentle_share=round(gentle / n2, 3) if n2 else 0.0, tot_len=tot_len, hard=hard,
             smooth_ratio=round(smooth_faces / nf, 2) if nf else 0.0)
    return r


def passport_from_scene():
    for c in bpy.data.collections:
        if c.name.startswith("ASSET_") and "passport" in c.keys():
            try:
                return json.loads(c["passport"])
            except ValueError:
                return None
    return None


def check(P=None):
    scene = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    if P is None:
        P = passport_from_scene()
    lowpoly = bool(P) and P.get("style") == "lowpoly"
    issues = []

    def add(code, level, obj, msg):
        issues.append({"code": code, "level": level, "m": M_CODE.get(code, "—"), "obj": obj, "msg": msg})

    vis = [o for o in scene.objects if o.visible_get() and not o.hide_render]
    asset_names = set()
    coll_name = P.get("collection") if P else None
    for c in bpy.data.collections:
        if (coll_name and c.name == coll_name) or (not coll_name and c.name.startswith("ASSET_")):
            for o in c.all_objects:
                asset_names.add(o.name)
    geo = [o for o in vis if o.type in GEO_TYPES]
    if asset_names:
        geo = [o for o in geo if o.name in asset_names]
    # части: вычисленные меши в мировых координатах
    parts = {}
    for o in geo:
        bm = world_bmesh(o, dg)
        if bm is None or len(bm.verts) == 0:
            if bm is not None:
                bm.free()
            continue
        pts = [v.co.copy() for v in bm.verts]
        lo, hi = aabb_of(pts)
        parts[o.name] = {"ob": o, "bm": bm, "lo": lo, "hi": hi, "pts": pts}
    # подложка (ловец теней, пол/фон много шире остального) — вне ассета
    stage = []
    stage_top = []
    if not asset_names and len(parts) > 1:
        for n in list(parts.keys()):
            p = parts[n]
            o = p["ob"]
            d = p["hi"] - p["lo"]
            others = [q for m, q in parts.items() if m != n]
            olo, ohi = aabb_of([q["lo"] for q in others] + [q["hi"] for q in others])
            od = ohi - olo
            flat = min(d) < 0.01 * max(max(d), 1e-9)
            wide = max(d.x, d.y) >= opt("stage_ratio") * max(od.x, od.y, 1e-9)
            if getattr(o, "is_shadow_catcher", False) or (flat and wide):
                stage.append(n)
        for n in stage:
            stage_top.append(parts[n]["hi"].z)
            parts[n]["bm"].free()
            del parts[n]
        if stage:
            add("stage_objects", "INFO", ", ".join(stage), "подложка исключена из ассета (ловец теней / пол / фон)")
    names = sorted(parts.keys())
    if not names:
        add("no_geometry", "ERROR", "", "в области ассета нет геометрии")
        return {"verdict": "fail", "issues": issues, "metrics": {}}
    lo, hi = aabb_of([parts[n]["lo"] for n in names] + [parts[n]["hi"] for n in names])
    dims = hi - lo
    diag = dims.length
    touch = max(opt("touch_m"), opt("touch_rel") * diag)
    # опора: верх подложки под ассетом (пол, ловец теней), иначе z = 0 мира
    below = [z for z in stage_top if z <= lo.z + 0.01 * diag]
    ground_z = max(below) if below else 0.0
    totals = {"objects": len(names), "tris": 0, "verts": 0, "draw_calls": 0}
    big_part = max(max(parts[n]["hi"] - parts[n]["lo"]) for n in names)
    per_obj = {}
    for n in names:
        p = parts[n]
        o = p["ob"]
        m = analyze_mesh(p["bm"])
        p["closed"] = m["closed"]
        p["centers"] = sample([(f.calc_center_median(), f.calc_area()) for f in p["bm"].faces], opt("sample_verts"))
        p["bvh"] = BVHTree.FromBMesh(p["bm"])
        p["sample"] = sample([v.co.copy() for v in p["bm"].verts], opt("sample_verts"))
        mats_used = {f.material_index for f in p["bm"].faces}
        totals["tris"] += m["tris"]
        totals["verts"] += m["verts"]
        totals["draw_calls"] += max(1, len(mats_used))
        per_obj[n] = m
        if any(abs(v - 1.0) > 1e-4 for v in o.scale):
            add("unapplied_scale", "WARN", n, "масштаб %s" % [round(v, 3) for v in o.scale])
        if o.matrix_world.determinant() < 0:
            add("negative_scale", "WARN", n, "отрицательный масштаб (отражение)")
        if o.type == "FONT":
            add("text_not_converted", "INFO", n, "текст не переведён в меш")
        size = (p["hi"] - p["lo"]).length
        c = (p["lo"] + p["hi"]) / 2
        if size > 0 and (o.matrix_world.translation - c).length > 0.75 * size + 1e-6:
            add("origin_far", "INFO", n, "pivot далеко от геометрии")
        if m["double_verts"]:
            add("double_verts", "WARN", n, "%d двойных вершин (≤ 0,01 мм)" % m["double_verts"])
        if m["nonmanifold"]:
            add("nonmanifold", "WARN", n, "%d рёбер с > 2 гранями" % m["nonmanifold"])
        if m["loose"]:
            add("loose_geometry", "WARN", n, "%d вершин/рёбер без граней" % m["loose"])
        if m["degenerate"]:
            add("degenerate_faces", "INFO", n, "%d граней нулевой площади" % m["degenerate"])
        if m["flipped"]:
            add("inverted_normals", "WARN", n, "%d граней с нормалью внутрь" % m["flipped"])
        if m["ngons_nonplanar"]:
            add("ngons_nonplanar", "WARN", n, "%d неплоских n-гонов" % m["ngons_nonplanar"])
        elif m["ngons"]:
            add("ngons", "INFO", n, "%d плоских n-гонов (торцы — норма)" % m["ngons"])
        if m["faces"] > 48 and m["smooth_ratio"] == 0 and m["gentle_share"] >= 0.5 and not lowpoly:
            add("faceted_curved", "WARN", n, "кривая поверхность (%.0f %% рёбер 5–30°) без сглаживания" % (100 * m["gentle_share"]))
        slots = [sl.material for sl in o.material_slots]
        if not slots or all(mt is None for mt in slots):
            add("no_material", "ERROR", n, "нет материала")
    # стыки, прорастание, спрятанные детали
    overlaps = []
    touching = {}
    contained = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = names[i]
            b = names[j]
            if aabb_gap((parts[a]["lo"], parts[a]["hi"]), (parts[b]["lo"], parts[b]["hi"])) > 0:
                continue
            cont = box_inside(a, b, parts) or box_inside(b, a, parts)
            if not parts[a]["bvh"].overlap(parts[b]["bvh"]) and not cont:
                continue
            touching.setdefault(a, []).append(b)
            touching.setdefault(b, []).append(a)
            sa, da = inside_share(a, b, parts)
            sb, db = inside_share(b, a, parts)
            small, big, s, dep = (a, b, sa, da) if len(parts[a]["pts"]) <= len(parts[b]["pts"]) else (b, a, sb, db)
            if max(sa, sb) > s:
                small, big, s, dep = (a, b, sa, da) if sa >= sb else (b, a, sb, db)
            overlaps.append({"pair": small + "|" + big, "inside": round(s, 3), "depth_m": round(dep, 4)})
            if s >= opt("inside_hidden"):
                contained.append((small, big))
                if see_through(parts[big]["ob"]):
                    add("embedded_joint", "INFO", small, "внутри прозрачной части %s — видна" % big)
                else:
                    add("hidden_inside", "WARN", small, "целиком внутри %s — лишние треугольники" % big)
            else:
                add("embedded_joint", "INFO", small, "пересечение с %s: %.0f %% площади внутри, глубина %.4f м — "
                    "законный стык или прорастание (M2.3) решает рендер" % (big, 100 * s, dep))
    # сырые и «сглаженные острые» рёбра — только видимые: середина ребра не внутри соседней детали (торцы в стенке)
    for n in names:
        p = parts[n]
        m = per_obj[n]
        nb = [q for q in touching.get(n, []) if parts[q]["closed"]]
        if p["closed"]:
            nb.append(n)                      # сам меш: ручка, сваренная с кружкой одним объектом
        s_len = 0.0
        h_cnt = 0
        for mid, ln, kind, nrm in m["hard"]:
            probe = mid + nrm * 1e-4          # точка чуть снаружи ребра
            hidden = False
            for q in nb:
                if point_inside(parts[q]["bvh"], probe):
                    hidden = True
                    break
            if hidden:
                continue
            if kind == "S":
                s_len += ln
            else:
                h_cnt += 1
        m["sharp_len_share"] = round(s_len / m["tot_len"], 3) if m["tot_len"] else 0.0
        m["smooth_across_hard"] = h_cnt
        pd = p["hi"] - p["lo"]
        sheet = min(pd) < 0.02 * max(max(pd), 1e-9)
        has_mod = any(md.type in ("BEVEL", "SUBSURF") for md in p["ob"].modifiers)
        if (p["ob"].type == "MESH" and not has_mod and not sheet and not lowpoly and max(pd) >= 0.15 * big_part
                and m["sharp_len_share"] > opt("sharp_share")):
            add("raw_sharp_edges", "WARN", n, "видимые рёбра > %d° без фаски: %.0f %% длины" % (opt("sharp_deg"), 100 * m["sharp_len_share"]))
        if h_cnt > 4 and not lowpoly:
            add("smooth_across_hard_edges", "WARN", n, "%d видимых рёбер > 80° сглажены" % h_cnt)
    # связность: компоненты по зазору ≤ touch (union-find), парящие компоненты
    parent = {n: n for n in names}

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    gaps = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = names[i]
            b = names[j]
            if aabb_gap((parts[a]["lo"], parts[a]["hi"]), (parts[b]["lo"], parts[b]["hi"])) > touch:
                continue
            d = mesh_distance(a, b, parts)
            gaps[a + "|" + b] = d
            if d <= touch:
                parent[root(a)] = root(b)
    for a, b in contained:                    # спрятанная деталь не «парит» — она внутри
        parent[root(a)] = root(b)
    comps = {}
    for n in names:
        comps.setdefault(root(n), []).append(n)
    comp_list = sorted([(sum(per_obj[m]["tris"] for m in v), sorted(v)) for v in comps.values()], reverse=True)
    allowed = set(P.get("allow_floating", [])) if P else set()
    if len(comp_list) > 1:
        main = comp_list[0][1]
        for tri, members in comp_list[1:]:
            if allowed and all(mb in allowed for mb in members):
                add("floating_allowed", "INFO", ", ".join(members[:4]), "парит по паспорту (allow_floating)")
                continue
            best = 1e18
            for a in members:
                for b in main:
                    gb = aabb_gap((parts[a]["lo"], parts[a]["hi"]), (parts[b]["lo"], parts[b]["hi"]))
                    if gb < best:
                        best = min(best, mesh_distance(a, b, parts)) if gb < 0.1 * diag + touch else min(best, gb)
            add("floating_part", "WARN", ", ".join(members[:4]), "не касается основной группы: зазор %.4f м" % best)
    # материалы и текстуры
    used = {}
    for n in names:
        for sl in parts[n]["ob"].material_slots:
            if sl.material is not None:
                used[sl.material.name] = sl.material
    tex = []
    for mname in sorted(used.keys()):
        mat = used[mname]
        p = principled_of(mat)
        if p is not None:
            bc = p.inputs["Base Color"]
            if not bc.is_linked:
                col = [round(v, 3) for v in bc.default_value[:3]]
                if all(abs(v - 0.8) < 1e-3 for v in col):
                    dc = [round(v, 3) for v in mat.diffuse_color[:3]]
                    if any(abs(v - 0.8) > 1e-3 for v in dc):
                        add("viewport_only_color", "ERROR", mname, "цвет только во вьюпорте (diffuse_color)")
                    else:
                        add("default_gray", "WARN", mname, "серый Principled по умолчанию")
        nodes = tree_nodes(mat.node_tree, 0)
        proc = sorted({nd.type for nd in nodes if nd.type in PROCEDURAL})
        if proc:
            add("procedural_textures", "WARN", mname, "процедурные ноды не доедут до glTF: %s" % ", ".join(proc))
        for nd in nodes:
            if nd.type == "TEX_IMAGE" and nd.image is not None:
                tex.append((nd.image.name, int(nd.image.size[0]), int(nd.image.size[1])))
    if len(used) > opt("max_materials"):
        add("many_materials", "WARN", "", "%d материалов" % len(used))
    big = sorted({t for t in tex if max(t[1], t[2]) > opt("max_tex_px")})
    if big:
        add("big_textures", "WARN", ", ".join(t[0] for t in big[:4]), "текстуры > %d px" % opt("max_tex_px"))
    # свет
    lights = [o for o in vis if o.type == "LIGHT"]
    ltypes = [o.data.type for o in lights]
    world_strength = None
    w = scene.world
    if w is not None and w.node_tree is not None:
        for nd in w.node_tree.nodes:
            if nd.type == "BACKGROUND":
                world_strength = round(nd.inputs["Strength"].default_value, 3)
    if not lights and (world_strength is None or world_strength < 0.5):
        add("no_lights", "WARN", "", "нет ламп и слабый мир")
    if len(ltypes) == 1 and ltypes[0] == "SUN":
        add("single_sun_only", "INFO", "", "одно солнце — плоский свет")
    # кадр: проекция вершин (не углов AABB) в камеру сцены
    cam = scene.camera
    frame = None
    if cam is None:
        add("no_camera", "WARN", "", "нет камеры сцены")
    else:
        r = scene.render
        pm = cam.calc_matrix_camera(dg, x=r.resolution_x, y=r.resolution_y, scale_x=r.pixel_aspect_x, scale_y=r.pixel_aspect_y)
        vm = cam.matrix_world.inverted()
        xs = []
        ys = []
        behind = 0
        for n in names:
            for v in sample(parts[n]["pts"], 4000):
                q = pm @ (vm @ Vector((v.x, v.y, v.z, 1.0)))
                if q.w <= 0:
                    behind += 1
                    continue
                xs.append((q.x / q.w + 1) / 2)
                ys.append((q.y / q.w + 1) / 2)
        if xs:
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            area = max(0.0, min(x1, 1) - max(x0, 0)) * max(0.0, min(y1, 1) - max(y0, 0))
            margin = min(x0, y0, 1 - x1, 1 - y1)
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            frame = {"x": [round(x0, 3), round(x1, 3)], "y": [round(y0, 3), round(y1, 3)], "area": round(area, 3),
                     "margin": round(margin, 3), "center": [round(cx, 3), round(cy, 3)]}
            if area < 0.005:
                add("not_in_frame", "ERROR", "", "ассет вне кадра (площадь %.3f)" % area)
            elif margin < 0 or behind:
                add("cropped", "ERROR", "", "обрезан: x %.2f..%.2f, y %.2f..%.2f" % (x0, x1, y0, y1))
            else:
                if margin < opt("margin_min"):
                    add("tight_margin", "INFO", "", "поле %.3f кадра" % margin)
                bbox_area = (x1 - x0) * (y1 - y0)
                if bbox_area < opt("frame_min_area"):
                    add("too_small_in_frame", "WARN", "", "рамка ассета %.3f кадра" % bbox_area)
                if bbox_area > opt("frame_max_area"):
                    add("too_big_in_frame", "INFO", "", "рамка ассета %.3f кадра" % bbox_area)
            if abs(cx - 0.5) > opt("center_tol") or abs(cy - 0.5) > opt("center_tol"):
                lvl = "WARN" if P and P.get("framing") == "center" else "INFO"
                add("off_center", lvl, "", "центр %.2f, %.2f (трети — вкус, не ошибка)" % (cx, cy))
        else:
            add("not_in_frame", "ERROR", "", "всё позади камеры")
    # масштаб и бюджеты
    if max(dims) > opt("huge_m"):
        add("huge_scale", "WARN", "", "%.1f м" % max(dims))
    if max(dims) < opt("tiny_m"):
        add("tiny_scale", "WARN", "", "%.3f м" % max(dims))
    if totals["tris"] > opt("max_tris"):
        add("heavy_mesh", "WARN", "", "%d треугольников" % totals["tris"])
    if totals["draw_calls"] > opt("max_draw_calls"):
        add("many_draw_calls", "WARN", "", "%d вызовов (объект × материал)" % totals["draw_calls"])
    dn = [n for n in names if n.split(".")[0] in DEFAULT_PREFIXES]
    if len(dn) >= 2:
        add("default_names", "INFO", ", ".join(dn[:4]), "%d из %d с заводскими именами" % (len(dn), len(names)))
    cube = scene.objects.get("Cube")
    if (cube is not None and cube.type == "MESH" and len(cube.data.vertices) == 8 and cube.location.length < 1e-4
            and all(abs(d - 2.0) < 1e-4 for d in cube.dimensions)):
        add("default_cube_left", "WARN", "Cube", "заводской куб остался в сцене")
    zero = [n for n in names if parts[n]["ob"].matrix_world.translation.length < 1e-6
            and ((parts[n]["lo"] + parts[n]["hi"]) / 2).length > 0.1 * max(diag, 1e-6)]
    if len(zero) >= 2:
        add("origins_at_world_zero", "INFO", ", ".join(zero[:4]), "%d pivots в нуле мира при разнесённых частях" % len(zero))
    # паспорт
    ptest = {}
    if P:
        if "dims_m" in P:
            tol = P.get("dims_tol", opt("dims_tol"))
            dev = []
            for i in range(3):
                e = P["dims_m"][i]
                dv = (dims[i] - e) / e if e else 0.0
                dev.append(round(dv, 3))
                if abs(dv) > tol:
                    add("dims_mismatch", "ERROR", "", "ось %d: %.4f м против %.4f (±%d %%)" % (i, dims[i], e, round(tol * 100)))
            ptest["dims_dev"] = dev
        tmax = P.get("max_gap_m", touch)
        for pair in P.get("touch", []):
            a = pair[0]
            b = pair[1]
            if a not in parts or b not in parts:
                add("not_touching", "ERROR", a + "~" + b, "части нет в сцене")
                continue
            d = mesh_distance(a, b, parts)
            ptest.setdefault("gaps_m", {})[a + "~" + b] = round(d, 5)
            if d > tmax:
                add("not_touching", "ERROR", a + "~" + b, "зазор %.4f м > %.4f" % (d, tmax))
        if "max_tris" in P and totals["tris"] > P["max_tris"]:
            add("over_budget_tris", "ERROR", "", "%d > %d треугольников" % (totals["tris"], P["max_tris"]))
        if "max_materials" in P and len(used) > P["max_materials"]:
            add("over_budget_materials", "WARN", "", "%d > %d материалов" % (len(used), P["max_materials"]))
        if P.get("on_ground") and abs(lo.z - ground_z) > touch:
            add("not_on_ground", "ERROR", "", "низ ассета %.4f м над опорой z = %.4f" % (lo.z - ground_z, ground_z))
    for n in names:
        parts[n]["bm"].free()
    levels = {i["level"] for i in issues}
    verdict = "fail" if "ERROR" in levels else ("review" if "WARN" in levels else "pass")
    hier = {"primary": 0, "secondary": 0, "tertiary": 0}
    for n in names:
        rr = max(parts[n]["hi"] - parts[n]["lo"]) / max(big_part, 1e-9)
        hier["primary" if rr >= 0.5 else "secondary" if rr >= 0.15 else "tertiary"] += 1
    view = scene.view_settings
    metrics = {
        "dims_m": [round(v, 4) for v in dims], "bbox_min": [round(v, 4) for v in lo], "touch_m": round(touch, 5),
        "ground_gap_m": round(lo.z - ground_z, 4),
        "totals": totals, "materials": len(used), "textures": len(tex), "lights": ltypes, "world_strength": world_strength,
        "camera": cam.name if cam else None, "frame": frame, "engine": scene.render.engine,
        "view_transform": view.view_transform, "look": view.look, "film_transparent": scene.render.film_transparent,
        "components": len(comp_list), "overlaps": overlaps[:12], "hierarchy": hier, "passport": ptest,
        "objects": {n: {k: per_obj[n][k] for k in ("tris", "ngons", "nonmanifold", "double_verts", "flipped",
                                                   "sharp_len_share", "sharp30_share")} for n in names[:40]},
    }
    return {"verdict": verdict, "codes": sorted({i["code"] for i in issues if i["level"] != "INFO"}),
            "issues": issues, "metrics": metrics}


print("SCENE_CHECK " + json.dumps(check(PASSPORT), ensure_ascii=False))
