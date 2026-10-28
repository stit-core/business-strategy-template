# D1/_lib — d1lib 0.1.1 (заморожена 23.09.2026 13:40) и помощники экспериментов

Надстройка над `../../scripts/3d/bpyx.py` (B) и идеями `99-raw/experiments/C1/12-protocol-objects/proto_lib.py` (C1).
Blender 5.2.2. Тесты: `python3 ../../scripts/3d/blender_run.py 99-raw/experiments/D1/_lib/test_d1lib.py` — 12/12 (0.1.0; перепрогон
0.1.1 — в `09-doc-snippets`). Подключение: `sys.path.insert(0, ".../99-raw/experiments/D1/_lib"); import d1lib as D`.

| Функция | Что делает |
|---|---|
| `fresh_collection(name)` | снести свою коллекцию с данными-сиротами и создать заново (идемпотентный `build(P)`, чужое не трогает) |
| `obj_from_bm(bm, name, coll, smooth_angle=30)` | bmesh → объект; `None` — flat, число — гладко + острые рёбра по углу |
| `rrect_pts(w, h, r, seg)` | скруглённый прямоугольник, постоянное число точек при любом r (для колец одинаковой длины) |
| `squircle_pts(w, h, n, count)` | суперэллипс (n 4–5 — «иконка iOS», непрерывная кривизна) |
| `circle_pts`, `ellipse_pts`, `superformula_pts` | контуры: окружность, эллипс, суперформула Гиелиса |
| `edge_profile(bottom_r, top_r, h, seg, power)` | профиль кромки [(inset, z)]; `power` > 2 — мягкий переход в плоскость |
| `loft_slab(name, outline, profile, …)` | тело из колец контура по профилю кромки (боковина — квады, крышки — n-гоны, UV) |
| `rounded_slab(name, w, d, h, corner_r, edge_r, kind='rrect'/'squircle', power)` | корпус/таблетка/кнопка/иконка; проверяет edge_r ≤ corner_r |
| `lathe(name, profile_rz, segments)` | тело вращения по профилю (r, z); точки на оси — полюса |
| `round_corner`, `fillet_polyline(pts, radii, seg)` | скругление углов ломаной (профили) |
| `lathe_shell(name, outer_rz, wall)` | сосуд со стенкой и скруглённой кромкой (кружки, стаканы) |
| `sweep(name, path, profile, closed, twist, scale)` | трубка/лента по пути: параллельный перенос рамок, раздача голономии, закрут, сужение |
| `torus_knot_pts`, `helix_pts`, `bezier_pts` | пути: торический узел, спираль, кубическая Безье |
| `resample_polyline(pts, n, closed)` | равномерная пересборка ломаной по длине |
| `catmull_rom_pts(ctrl, count, closed)` | гладкая кривая через точки (профили без «ступенек» затенения) |
| `weld_mesh(me, dist)` | сварка совпадающих вершин (меш из кривой/текста не сварен по швам) |
| `extrude_outline(name, loops, depth, bevel)` | контур с отверстиями → тело через заливку кривой, offset = −bevel, сварка |
| `text_mesh(name, body, size, extrude, bevel, bevel_res, resolution_u)` | 3D-текст → меш, стоит лицом к −Y, низ на z = 0 |
| `svg_mesh(name, svg_path, size, depth, bevel, resolution_u)` | SVG (`import_curve.svg`) → один меш заданной ширины, вертикально |
| `metaball_mesh(name, balls, resolution)` | метаболы → меш |
| `sdf_blob_gn(name, balls, voxel, fillet_iter, smooth_width, smooth_iter)` | блоб через SDF-ноды 5.2 (Points to SDF Grid → Fillet → Mean → Grid to Mesh) |
| `noise_displace(ob, strength, scale, octaves, seed)` | детерминированное смещение вершин шумом mathutils |
| `hard_surface(ob, bevel_width, segments, angle)` | Bevel (angle, harden_normals, clamp, miter arc) + Weighted Normal (keep_sharp) |
| `smooth_by_angle_modifier(ob, angle)` | ассет «Smooth by Angle» без окна: `libraries.load(geometry_nodes_essentials.blend)` + NODES |
| `boolean_apply(target, cutters, solver='EXACT')` | булево + Weld + limited dissolve + нормали + острые рёбра; резаки удаляются; отчёт |
| `set_origin(ob, point)` | pivot в мировую точку без сдвига геометрии (петли, оси) |
| `add_marker(name, loc, kind, extras)` | пустышка `hotspot_/collider_/cam_…` с extras для JS |
| `surface_points(ob, n, seed)` | ровно n точек на поверхности, равномерно по площади, детерминированно |
| `to_three(v)`, `export_points_f32(points, path)` | оси Blender → three (x, z, −y); точки → .bin Float32 LE |
| `export_curve_json(name, path, samples)` | кривая по имени → JSON точек в осях three |
| `gltf_vertex_estimate(ob)` | сколько вершин будет в glTF (позиция + нормаль угла + UV) |
| `edge_sharpness_report(ob)` | доля «сырых» острых рёбер (нет фасок, M3.2) |
| `part_hierarchy(objects)` | классы частей по размеру: крупная ≥ 0,5, средняя 0,15–0,5, мелкая < 0,15 |
| `silhouette_metrics(png)` | заполнение, компактность, выпуклость, отверстия силуэта по альфе рендера [не проверено в экспериментах] |
| `stage(objs, bg, az)` | студия: key/fill/rim по радиусу ассета, мир и циклорама цвета фона |
| `frame(objs, az, el, lens, margin, ortho)` | камера по габаритам (подгонка по 8 углам через `camera_fit_coords`) |
| `render_setup(samples, view, look)` | EEVEE/Cycles, view transform, прозрачность |
| `export_web(path, collection, preset)` | экспорт коллекции пресетом E/24 (`static_hero`, `instances`, …) |

`d1exp.py` — помощники экспериментов: `glb_info` (разбор GLB без инструментов), `gltf_optimize` (gltf-transform с
безопасными флагами), `sheet` (контактный лист), `clay_override`, `render_to`, `save`.
