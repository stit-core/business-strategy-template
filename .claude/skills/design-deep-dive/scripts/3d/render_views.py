"""Рендер модели с нескольких ракурсов + контактный лист + статистика геометрии. Запускается ВНУТРИ Blender:

    python3 blender_run.py render_views.py -- INPUT OUT_DIR [--views 4|6|turntable:8] [--size 512]
        [--engine eevee|cycles|workbench] [--samples 32] [--clay] [--hdri FILE] [--bg #RRGGBB|transparent]
        [--keep-lights] [--keep-camera] [--view-transform AgX|Standard|Khronos PBR Neutral|...] [--frame N]
        [--lens 50] [--no-render]

INPUT: .glb/.gltf/.fbx/.obj/.stl/.ply/.usd/.usda/.usdc/.usdz/.abc/.blend
    .blend открывается как есть. По умолчанию собственные камеры и свет сцены отключаются для рендера и ставится
    нейтральная студия (key/fill/rim, площади источников и мощность масштабируются по размеру модели);
    --keep-lights оставляет свет сцены (и мир), --keep-camera добавляет кадр из активной камеры сцены.
Выход:
    OUT_DIR/view_<n>_az<A>_el<E>.png  — RGBA-кадры с прозрачным фоном (плёнка прозрачная всегда)
    OUT_DIR/sheet.png                  — контактный лист на фоне --bg (по умолчанию #d4d4d8)
    OUT_DIR/stats.json                 — статистика: объекты, треугольники после модификаторов, n-гоны,
        неманифолдные и граничные рёбра, вершины без граней, неприменённый и отрицательный масштаб, UV-наборы,
        материалы и типы нод в них, изображения (размер, цветовое пространство), габариты и центр сцены,
        время рендера.
Ракурсы: азимут от вида спереди (камера на −Y смотрит на +Y) против часовой при взгляде сверху, угол места — вверх.
    4: 3/4 спереди-справа, спереди, справа, сзади-сверху; 6: + сверху и снизу-сбоку; turntable:N — N азимутов при 20°.
--clay: переопределение материалов серой глиной (форма без отвлечения на цвет).
--engine workbench: быстрый «студийный» рендер без материалов, случайный цвет на объект — видно разбиение на части.
"""
import json, math, os, sys, time, warnings

import bpy
import bmesh

warnings.filterwarnings("ignore", category=DeprecationWarning)  # use_nodes в 5.x: предупреждение, не ошибка
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    print(__doc__); raise SystemExit(2)
INPUT, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
opts = argv[2:]


def opt(name, default=None):
    return opts[opts.index(name) + 1] if name in opts else default


VIEWS = opt("--views", "4")
SIZE = int(opt("--size", 512))
ENGINE = opt("--engine", "eevee").lower()
SAMPLES = int(opt("--samples", 32))
CLAY = "--clay" in opts
HDRI = opt("--hdri")
BG = opt("--bg", "#d4d4d8")
KEEP_LIGHTS = "--keep-lights" in opts
KEEP_CAMERA = "--keep-camera" in opts
VIEW_TRANSFORM = opt("--view-transform")
FRAME = opt("--frame")
LENS = float(opt("--lens", 50))
NO_RENDER = "--no-render" in opts
os.makedirs(OUT, exist_ok=True)
t_start = time.time()

# ---------- загрузка ----------
ext = os.path.splitext(INPUT)[1].lower()
if ext == ".blend":
    bpy.ops.wm.open_mainfile(filepath=INPUT)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    importers = {
        ".glb": lambda p: bpy.ops.import_scene.gltf(filepath=p),
        ".gltf": lambda p: bpy.ops.import_scene.gltf(filepath=p),
        ".fbx": lambda p: bpy.ops.import_scene.fbx(filepath=p),
        ".obj": lambda p: bpy.ops.wm.obj_import(filepath=p),
        ".stl": lambda p: bpy.ops.wm.stl_import(filepath=p),
        ".ply": lambda p: bpy.ops.wm.ply_import(filepath=p),
        ".abc": lambda p: bpy.ops.wm.alembic_import(filepath=p),
    }
    for e in (".usd", ".usda", ".usdc", ".usdz"):
        importers[e] = lambda p: bpy.ops.wm.usd_import(filepath=p)
    if ext not in importers:
        raise SystemExit(f"Неизвестный формат: {ext}")
    importers[ext](INPUT)

scene = bpy.context.scene
if FRAME is not None:
    scene.frame_set(int(FRAME))
dg = bpy.context.evaluated_depsgraph_get()
GEOM = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "POINTCLOUD", "VOLUME", "GREASEPENCIL"}
geo_objs = [o for o in scene.objects if o.type in GEOM and o.visible_get()]

# ---------- статистика ----------
stats = {"input": INPUT, "blender": bpy.app.version_string, "objects": [], "totals": {}, "materials": {},
         "images": [], "warnings": []}
bb_min = Vector((1e18, 1e18, 1e18)); bb_max = Vector((-1e18, -1e18, -1e18))
tot = dict(tris=0, verts=0, ngons=0, nonmanifold_edges=0, boundary_edges=0, loose_verts=0)
for o in geo_objs:
    oe = o.evaluated_get(dg)
    # Габариты: по вершинам вычисленного меша в мире (точно для мешей, текста, кривых, GN). bound_box у
    # oe для FONT/CURVE в 5.2.2 не учитывает extrude/bevel — он только запасной путь,
    # и берётся у ОРИГИНАЛА после вычисления depsgraph (как bpyx.world_bbox).
    _bb_done = False
    try:
        _me = oe.to_mesh()
        if _me is not None and len(_me.vertices):
            import numpy as _np
            _co = _np.empty(len(_me.vertices) * 3, dtype=_np.float32)
            _me.vertices.foreach_get("co", _co)
            _co = _co.reshape(-1, 3)
            _m = _np.array(oe.matrix_world, dtype=_np.float64)
            _w = _co @ _m[:3, :3].T + _m[:3, 3]
            bb_min = Vector(map(min, bb_min, _w.min(axis=0))); bb_max = Vector(map(max, bb_max, _w.max(axis=0)))
            _bb_done = True
        oe.to_mesh_clear()
    except RuntimeError:
        pass
    if not _bb_done:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            bb_min = Vector(map(min, bb_min, w)); bb_max = Vector(map(max, bb_max, w))
    info = {"name": o.name, "type": o.type, "modifiers": [m.type for m in o.modifiers],
            "scale": [round(v, 4) for v in o.scale], "rotation": [round(v, 4) for v in o.rotation_euler],
            "parent": o.parent.name if o.parent else None}
    if any(abs(s - 1) > 1e-4 for s in o.scale):
        info["unapplied_scale"] = True
    if o.matrix_world.determinant() < 0:
        info["negative_scale"] = True
        stats["warnings"].append(f"{o.name}: отрицательный масштаб (нормали и экспорт могут перевернуться)")
    try:
        me = oe.to_mesh()
    except RuntimeError:
        me = None
    if me is not None:
        bm = bmesh.new(); bm.from_mesh(me)
        nv0 = len(bm.verts)
        # glTF/FBX при импорте расщепляют вершины по швам UV и жёстким рёбрам: для подсчёта топологии
        # сшиваем совпадающие вершины (на рендер это не влияет — считаем на копии)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        info["welded_split_verts"] = nv0 - len(bm.verts)
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
        boundary = sum(1 for e in bm.edges if e.is_boundary)
        nonman = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        loose = sum(1 for v in bm.verts if not v.link_faces)
        info.update(tris=tris, verts=nv0, faces=len(bm.faces), ngons=ngons, boundary_edges=boundary,
                    nonmanifold_edges=nonman, loose_verts=loose, uv_layers=[u.name for u in me.uv_layers],
                    color_attributes=[c.name for c in getattr(me, "color_attributes", [])],
                    materials=[m.name if m else None for m in me.materials])
        for k, v in (("tris", tris), ("verts", nv0), ("ngons", ngons), ("nonmanifold_edges", nonman),
                     ("boundary_edges", boundary), ("loose_verts", loose)):
            tot[k] += v
        bm.free(); oe.to_mesh_clear()
    stats["objects"].append(info)
for m in bpy.data.materials:
    if m.users == 0:
        continue
    nodes = sorted({n.bl_idname for n in m.node_tree.nodes}) if m.node_tree else []
    stats["materials"][m.name] = {"nodes": nodes, "blend_method": getattr(m, "surface_render_method", None)}
for im in bpy.data.images:
    if im.users == 0 or im.type != "IMAGE":
        continue
    stats["images"].append({"name": im.name, "size": list(im.size), "colorspace": im.colorspace_settings.name,
                            "packed": bool(im.packed_file), "filepath": im.filepath})
if not geo_objs:
    raise SystemExit("В сцене нет видимой геометрии")
center = (bb_min + bb_max) / 2
dims = bb_max - bb_min
radius = max(dims.length / 2, 1e-4)
stats["totals"] = dict(objects=len(geo_objs), **tot)
stats["bbox"] = {"min": [round(v, 4) for v in bb_min], "max": [round(v, 4) for v in bb_max],
                 "dimensions": [round(v, 4) for v in dims], "center": [round(v, 4) for v in center]}
if tot["ngons"]:
    stats["warnings"].append(f"n-гонов: {tot['ngons']} (при экспорте триангулируются; проверь затенение)")
if tot["nonmanifold_edges"]:
    stats["warnings"].append(f"неманифолдных рёбер: {tot['nonmanifold_edges']}")
if tot["loose_verts"]:
    stats["warnings"].append(f"вершин без граней: {tot['loose_verts']}")

if NO_RENDER:
    json.dump(stats, open(os.path.join(OUT, "stats.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(stats["totals"], ensure_ascii=False)); print("STATS", os.path.join(OUT, "stats.json"))
    raise SystemExit(0)

# ---------- студия ----------
if not KEEP_LIGHTS:
    for o in scene.objects:
        if o.type == "LIGHT":
            o.hide_render = True
scene_cam = scene.camera
for o in scene.objects:
    if o.type == "CAMERA":
        o.hide_render = True
coll = bpy.data.collections.new("_render_views"); scene.collection.children.link(coll)


def add_area(name, az, el, dist, power, size):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = power; ld.size = size
    ob = bpy.data.objects.new(name, ld); coll.objects.link(ob)
    a, e = math.radians(az), math.radians(el)
    ob.location = center + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    ob.rotation_euler = (center - ob.location).to_track_quat("-Z", "Y").to_euler()
    return ob


if not KEEP_LIGHTS:
    d = radius * 4.0
    k = 900.0 * (d / 7.0) ** 2  # калибровка: 900 Вт на 7 м ≈ нормальная экспозиция при AgX
    add_area("_key", 40, 45, d, k, radius * 2.0)
    add_area("_fill", -70, 15, d, k * 0.35, radius * 3.0)
    add_area("_rim", 170, 50, d, k * 0.6, radius * 1.5)
    world = bpy.data.worlds.new("_studio_world"); scene.world = world
    try:
        world.use_nodes = True
    except Exception:
        pass
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    if HDRI:
        env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.abspath(HDRI))
        nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
    else:
        bg.inputs["Color"].default_value = (0.25, 0.25, 0.27, 1.0); bg.inputs["Strength"].default_value = 0.6

if CLAY:
    clay = bpy.data.materials.new("_clay")
    try:
        clay.use_nodes = True
    except Exception:
        pass
    p = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (0.62, 0.62, 0.64, 1); p.inputs["Roughness"].default_value = 0.55
    bpy.context.view_layer.material_override = clay

# ---------- движок ----------
r = scene.render
r.resolution_x = r.resolution_y = SIZE; r.resolution_percentage = 100
r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"
eng_map = {"eevee": "BLENDER_EEVEE", "cycles": "CYCLES", "workbench": "BLENDER_WORKBENCH"}
try:
    r.engine = eng_map.get(ENGINE, ENGINE)
except TypeError as e:
    raise SystemExit(f"Движок не принят: {e}")
if r.engine == "CYCLES":
    scene.cycles.samples = SAMPLES; scene.cycles.device = "CPU"
    try:
        scene.cycles.use_denoising = True
    except Exception:
        pass
elif r.engine == "BLENDER_EEVEE":
    try:
        scene.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass
elif r.engine == "BLENDER_WORKBENCH":
    sh = scene.display.shading
    sh.light = "STUDIO"; sh.color_type = "RANDOM" if not CLAY else "SINGLE"
    sh.show_cavity = True; sh.show_object_outline = True
if VIEW_TRANSFORM:
    try:
        scene.view_settings.view_transform = VIEW_TRANSFORM
    except TypeError as e:
        stats["warnings"].append(f"view_transform {VIEW_TRANSFORM} не принят: {e}")
stats["view_transform"] = scene.view_settings.view_transform
stats["engine"] = r.engine

# ---------- ракурсы ----------
if VIEWS.startswith("turntable"):
    n = int(VIEWS.split(":")[1]) if ":" in VIEWS else 8
    views = [(i * 360.0 / n, 20.0) for i in range(n)]
elif VIEWS == "6":
    views = [(35, 20), (0, 5), (90, 5), (200, 35), (0, 85), (300, -25)]
else:
    views = [(35, 20), (0, 5), (90, 5), (200, 35)]
cam_data = bpy.data.cameras.new("_rv_cam"); cam_data.lens = LENS; cam_data.sensor_fit = "AUTO"
cam = bpy.data.objects.new("_rv_cam", cam_data); coll.objects.link(cam)
half_fov = math.atan(cam_data.sensor_width / 2 / cam_data.lens)
dist = radius / math.sin(half_fov) * 1.08
cam_data.clip_start = max(dist - radius * 3, radius * 0.01); cam_data.clip_end = dist + radius * 4
files = []
for i, (az, el) in enumerate(views):
    a, e = math.radians(az), math.radians(el)
    cam.location = center + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    fp = os.path.join(OUT, f"view_{i}_az{int(az)}_el{int(el)}.png")
    r.filepath = fp
    t = time.time(); bpy.ops.render.render(write_still=True)
    files.append((fp, round(time.time() - t, 2)))
if KEEP_CAMERA and scene_cam is not None:
    scene_cam.hide_render = False; scene.camera = scene_cam
    fp = os.path.join(OUT, f"view_{len(files)}_scene_camera.png"); r.filepath = fp
    t = time.time(); bpy.ops.render.render(write_still=True); files.append((fp, round(time.time() - t, 2)))
stats["renders"] = [{"file": f, "sec": s} for f, s in files]

# ---------- контактный лист ----------
try:
    import numpy as np
    import OpenImageIO as oiio
    hexs = BG.lstrip("#")
    bgc = np.array([int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32) if BG != "transparent" else None
    tiles = []
    for fp, _ in files:
        px = oiio.ImageBuf(fp).get_pixels(oiio.FLOAT)
        if px.shape[2] == 3:
            px = np.concatenate([px, np.ones(px.shape[:2] + (1,), np.float32)], axis=2)
        if bgc is not None:
            a_ = px[..., 3:4]; px = np.concatenate([px[..., :3] * a_ + bgc * (1 - a_), np.ones_like(a_)], axis=2)
        tiles.append(px)
    cols = min(len(tiles), 4); rows = math.ceil(len(tiles) / cols)
    h, w = tiles[0].shape[:2]
    sheet = np.zeros((rows * h, cols * w, 4), np.float32)
    if bgc is not None:
        sheet[..., :3] = bgc; sheet[..., 3] = 1
    for i, t in enumerate(tiles):
        rr, cc = divmod(i, cols); sheet[rr * h:(rr + 1) * h, cc * w:(cc + 1) * w] = t
    spec = oiio.ImageSpec(cols * w, rows * h, 4, oiio.UINT8)
    outp = oiio.ImageOutput.create(os.path.join(OUT, "sheet.png"))
    outp.open(os.path.join(OUT, "sheet.png"), spec); outp.write_image(np.clip(sheet, 0, 1)); outp.close()
    stats["sheet"] = os.path.join(OUT, "sheet.png")
except Exception as ex:  # лист — удобство, не обязательная часть
    stats["warnings"].append(f"контактный лист не собран: {ex}")

stats["total_sec"] = round(time.time() - t_start, 1)
json.dump(stats, open(os.path.join(OUT, "stats.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({"totals": stats["totals"], "bbox": stats["bbox"], "warnings": stats["warnings"],
                  "engine": stats["engine"], "view_transform": stats["view_transform"],
                  "renders": len(files), "total_sec": stats["total_sec"]}, ensure_ascii=False, indent=1))
print("SHEET", stats.get("sheet")); print("STATS", os.path.join(OUT, "stats.json"))
