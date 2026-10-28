# Blender 5.2.2 — утверждения по паспорту ассета: габариты, контакты частей, бюджет треугольников
# Отправляется в execute_blender_code как есть (после правки PASSPORT) или исполняется в фоне; проходит safe mode.
import bpy, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh

PASSPORT = {
    "collection": "ASSET_laptop",
    "dims_m": [0.304, 0.284, 0.213], "dims_tol": 0.05,          # ожидаемые габариты ассета и допуск ±5 %
    "touch": [["Laptop_Keys", "Laptop_Base"], ["Laptop_Lid", "Laptop_Base"], ["Laptop_Screen", "Laptop_Lid"]],
    "max_gap_m": 0.001,                                         # «касается» = зазор ≤ 1 мм
    "max_tris": 20000, "max_materials": 8,
}


def eval_mesh_world(ob, dg):
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    oe.to_mesh_clear()
    return bm


def check(P):
    dg = bpy.context.evaluated_depsgraph_get()
    coll = bpy.data.collections[P["collection"]]
    obs = [o for o in coll.all_objects if o.type == "MESH"]
    res = {"ok": True, "fails": []}
    pts, tris, mats, bms = [], 0, set(), {}
    for o in obs:
        bm = eval_mesh_world(o, dg)
        bms[o.name] = bm
        pts += [v.co.copy() for v in bm.verts]
        tris += sum(len(f.verts) - 2 for f in bm.faces)
        mats |= {s.material.name for s in o.material_slots if s.material}
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    dims = [round(v, 4) for v in (hi - lo)]
    res["dims_m"], res["tris"], res["materials"] = dims, tris, len(mats)
    for i, (d, e) in enumerate(zip(dims, P["dims_m"])):
        if abs(d - e) > e * P["dims_tol"]:
            res["fails"].append(f"dim[{i}] {d} vs {e} ±{int(P['dims_tol'] * 100)}%")
    for a, b in P["touch"]:
        ta = BVHTree.FromBMesh(bms[a]); tb = BVHTree.FromBMesh(bms[b])
        if ta.overlap(tb):
            gap = 0.0
        else:  # минимальное расстояние от вершин a до поверхности b
            gap = min((tb.find_nearest(v.co)[3] for v in bms[a].verts), default=1e9)
        res.setdefault("gaps_m", {})[f"{a}~{b}"] = round(gap, 5)
        if gap > P["max_gap_m"]:
            res["fails"].append(f"{a} not touching {b}: gap {gap:.4f} m")
    if tris > P["max_tris"]:
        res["fails"].append(f"tris {tris} > {P['max_tris']}")
    if len(mats) > P["max_materials"]:
        res["fails"].append(f"materials {len(mats)} > {P['max_materials']}")
    for bm in bms.values():
        bm.free()
    res["ok"] = not res["fails"]
    return res


print("ASSERT " + json.dumps(check(PASSPORT), ensure_ascii=False))
