import bpy, math
from collections import Counter
cam = bpy.data.objects["SD_Cam"]
print("CAM", cam.data.type, round(cam.data.ortho_scale, 3), [round(v, 3) for v in cam.location], [round(math.degrees(a), 2) for a in cam.rotation_euler], cam.data.sensor_fit)
sc = bpy.context.scene
print("RES", sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage)
w = bpy.data.objects["Walls"]
print("WALL mats", [m.name for m in w.data.materials], Counter(p.material_index for p in w.data.polygons))
tops = [p for p in w.data.polygons if p.normal.z > 0.9]
print("tops", len(tops), Counter(p.material_index for p in tops), Counter(round(p.center.z, 3) for p in tops))
