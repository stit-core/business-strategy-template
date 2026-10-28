# Blender 5.2.2 — [проверено] сцена для «путь камеры + клип на прокрутке»
# Запуск: python3 scripts/3d/blender_run.py kb/3d/09-web-runtime/examples/camera-path-scroll/build_scene.py -- OUT_DIR
# Даёт: OUT_DIR/scene.glb (кольца-галерея, пол, стопка плит с клипом сборки, пустышки hotspot_*),
#       OUT_DIR/cam_path.json (точки кривой в осях three: [x, z, -y], метры), OUT_DIR/build_report.json
import bpy, json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: bpyx.py — scripts/3d
import bpyx

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else os.path.abspath("out")
os.makedirs(OUT, exist_ok=True)
bpyx.clear_scene()
col = bpyx.ensure_collection("WEB")

# --- кривая пути камеры (Blender Z-up), объект берём по имени, а не active_object
CTRL = [(0.0, 9.0, 1.3), (1.6, 5.5, 1.2), (-1.4, 1.5, 1.1), (1.2, -2.5, 1.0), (0.0, -5.2, 1.25)]
cu = bpy.data.curves.new("cam_path", "CURVE")
cu.dimensions = "3D"
cu.resolution_u = 24                                   # точек на сегмент Безье → плотность JSON
sp = cu.splines.new("BEZIER")
sp.bezier_points.add(len(CTRL) - 1)
for bp, co in zip(sp.bezier_points, CTRL):
    bp.co = co
    bp.handle_left_type = bp.handle_right_type = "AUTO"
path_ob = bpy.data.objects.new("cam_path", cu)
bpy.context.scene.collection.objects.link(path_ob)     # не в WEB: кривая без bevel в GLB не нужна

# --- кольца-галерея вдоль пути (торы стоят вертикально, повёрнуты по касательной)
PALETTE = ["#f4b8a0", "#f2c6b4", "#e8c7d8", "#d6c8ec", "#c3cdf0", "#b8d8e8"]
deps = bpy.context.evaluated_depsgraph_get()
ev = path_ob.evaluated_get(deps)
me = ev.to_mesh()
pts = [path_ob.matrix_world @ v.co for v in me.vertices]   # вершины вычисленной кривой, по порядку сплайна
ev.to_mesh_clear()
n_rings = 6
for i in range(n_rings):
    k = int((i + 0.5) / n_rings * (len(pts) - 2))
    p, q = pts[k], pts[k + 1]
    ang = math.atan2(q.y - p.y, q.x - p.x)             # направление пути в плоскости XY
    ring = bpyx.primitive("torus", f"ring_{i + 1}", radius=1.25, minor_radius=0.07, segments=96, rings=16,
                          location=(p.x, p.y, 1.25 + 0.07), collection=col)   # стоит на полу: центр = R + r (иначе «пророс», M2.3)
    ring.rotation_euler = (math.radians(90), 0.0, ang + math.radians(90))
    mat, _ = bpyx.principled(f"ring_{i + 1}_mat", base_color=bpyx.color(PALETTE[i]), roughness=0.35)
    bpyx.assign_material(ring, mat)
    e = bpy.data.objects.new(f"hotspot_{i + 1}", None)         # пустышка = точка метки/клика в JS
    e.empty_display_type = "SPHERE"; e.empty_display_size = 0.15
    e.location = (p.x, p.y, 2.75)
    e["label"] = f"Кольцо {i + 1}"                              # → userData.label (export_extras=True)
    col.objects.link(e)

floor = bpyx.primitive("plane", "floor", size=40, location=(0, 0, 0), collection=col)
fm, _ = bpyx.principled("floor_mat", base_color=bpyx.color("#efe9e4"), roughness=0.9)
bpyx.assign_material(floor, fm)

# --- стопка плит с клипом «сборки»: каждая плита — отдельный объект с origin в центре
SLAB_COLORS = ["#2f2a4a", "#4b4380", "#7a6fc0", "#b3a8ea", "#e6e0ff"]
base = (0.0, -8.4, 0.0)                                 # 3,2 м от конца пути: стопка ≈ 45 % высоты кадра при FOV 50
slabs = []
for i, hx in enumerate(SLAB_COLORS):
    s = bpyx.primitive("cube", f"slab_{i + 1}", size=1.0, location=(base[0], base[1], 0.14 + i * 0.26), collection=col)
    s.scale = (1.4 - i * 0.16, 1.4 - i * 0.16, 0.22)
    bpyx.apply_transforms(s, scale=True)
    bpyx.add_modifier(s, "BEVEL", width=0.035, segments=3)
    m, _ = bpyx.principled(f"slab_{i + 1}_mat", base_color=bpyx.color(hx), roughness=0.45)
    bpyx.assign_material(s, m)
    slabs.append(s)
scn = bpy.context.scene
scn.render.fps = 30
scn.frame_start, scn.frame_end = 1, 60
for i, s in enumerate(slabs):                           # кадр 1 — разлёт, кадр 60 — сборка
    rest = s.location.copy()
    s.location = (rest.x + (i - 2) * 1.1, rest.y + 0.6 * (i % 2 * 2 - 1), rest.z + 1.2 + i * 0.55)
    s.rotation_euler = (0.0, 0.0, math.radians(35 * (i - 2)))
    s.keyframe_insert(data_path="location", frame=1)
    s.keyframe_insert(data_path="rotation_euler", frame=1)
    s.location = rest
    s.rotation_euler = (0.0, 0.0, 0.0)
    s.keyframe_insert(data_path="location", frame=60)
    s.keyframe_insert(data_path="rotation_euler", frame=60)
scn.frame_set(60)                                       # поза покоя в файле = собранная стопка (см. ниже export)

# --- JSON пути в осях three (Y-up): (x, y, z)_blender → (x, z, -y)
path_json = {"name": "cam_path", "closed": False, "units": "m", "axes": "three-yup",
             "source": "Blender 5.2.2 Bezier, resolution_u=24", "count": len(pts),
             "points": [[round(p.x, 4), round(p.z, 4), round(-p.y, 4)] for p in pts]}
json.dump(path_json, open(os.path.join(OUT, "cam_path.json"), "w"), ensure_ascii=False)

objs = [o for o in col.objects]
res = bpyx.export_glb(os.path.join(OUT, "scene.glb"), objs, apply_modifiers=True,
                      export_yup=True, export_extras=True, export_animations=True,
                      export_animation_mode="ACTIVE_ACTIONS", export_anim_slide_to_zero=True,
                      export_force_sampling=True, export_current_frame=False)
report = {"glb_bytes": res["bytes"], "path_points": len(pts), "objects": [o.name for o in objs],
          "tris": sum(bpyx.object_stats(o).get("tris", 0) for o in objs if o.type == "MESH")}
json.dump(report, open(os.path.join(OUT, "build_report.json"), "w"), ensure_ascii=False, indent=1)
print("REPORT", json.dumps(report, ensure_ascii=False))
