"""check_weight.py — латунная плита внутри корпуса: не пересекает плату и дно, зазоры в мм (BVH)."""
import sys, os, json
import bpy, bmesh
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_lib"))
dg = bpy.context.evaluated_depsgraph_get()
def bvh(name):
    o = bpy.data.objects[name]; bm = bmesh.new(); bm.from_object(o, dg); bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm); vs = [v.co.copy() for v in bm.verts]; bm.free(); return t, vs
W, wv = bvh("Weight"); P, pv = bvh("PCB"); CB, cbv = bvh("Case_Bottom")
rep = {"weight_pcb_overlap": bool(W.overlap(P)), "weight_case_overlap": bool(W.overlap(CB)),
       "gap_weight_pcb_mm": round(min(P.find_nearest(v)[3] for v in wv) * 1000, 2),
       "gap_weight_floor_mm": round(min(CB.find_nearest(v)[3] for v in wv) * 1000, 2)}
print("KB_WEIGHT", json.dumps(rep))
