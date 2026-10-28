import bpy
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene
for p in ((1.5, 5.0), (3.0, 5.5), (2.0, 3.3), (6.5, 5.3), (3.0, 1.5)):
    hit, loc, nrm, idx, ob, mw = sc.ray_cast(dg, Vector((p[0], p[1], 5.0)), Vector((0, 0, -1)))
    mats = [s.material.name if s.material else None for s in ob.material_slots] if ob else None
    print("RAY", p, hit, ob.name if ob else None, round(loc.z, 4) if hit else None, mats)
fl = bpy.data.objects["Floor"]
print("FLOOR", [s.material.name for s in fl.material_slots], fl.hide_render, [round(v, 3) for v in fl.dimensions])
