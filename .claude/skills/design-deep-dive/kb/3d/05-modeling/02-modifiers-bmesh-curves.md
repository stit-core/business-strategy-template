# Модификаторы, bmesh, кривые, текст и SVG в Blender 5.2: порядок, числа и ловушки для кода

Волна 2 · агент D1 · 23.09.2026 · источники: руководство Blender 5.2 (18 страниц модификаторов — заметки помощника
`99-raw/notes/wave2/D1-subnotes/manual-modifiers-curves.md`), RNA и докстринги `bmesh.ops` Blender 5.2.2 (зонд
`99-raw/experiments/D1/00-api-probe/probe.json`: 30 модификаторов, 53 оператора, 84 GN-ноды, 83 `bmesh.ops`), файлы B и E
волны 1, ролики через W4 · эксперименты D1/00–07 · Blender 5.2.2 LTS, glTF-IO 5.2.40. Все блоки `python` выполнены в
напечатанном виде (`99-raw/experiments/D1/09-doc-snippets`).

## Выжимка для агента

1. **Модификаторы задавай через `bpyx.add_modifier(ob, TYPE, **props)`**: он проверяет имена свойств по RNA 5.2 (старые `use_x`, `use_only_vertices` → ошибка с подсказкой). → §1 [проверено: B, D1/00]
2. **Умолчания 5.2.2 не для веба**: Bevel `width=0.1` м и `segments=1`; Boolean `solver='EXACT'`; Subdivision `levels=1`/`render_levels=2`; Weighted Normal `keep_sharp=False`. Задавай все ключевые значения явно. → §1 [проверено]
3. **Стек hard-surface**: Mirror → Boolean → Weld → Bevel (angle, harden) → Weighted Normal (keep_sharp) последним; SubD — только с опорами. → §2 [проверено: D1/01, D1/03; документация]
4. **Для веба модификаторы доходят только применёнными** (`export_apply=True` берёт уровень вьюпорта `levels`); с shape keys — применить до морфов. → §2.3 [проверено]
5. **«Smooth by Angle» без окна** — ассет из `geometry_nodes_essentials.blend` через `bpy.data.libraries.load` + модификатор NODES (`d1lib.smooth_by_angle_modifier`); проще и дешевле — данные `set_sharp_from_angle`. → §1.3 [проверено: D1/_lib t08, D1/01]
6. **Edge Split не использовать** («kept mostly for historical/compatibility reasons») — рвёт меш. → §1 [документация 5.2]
7. **В 5.2 два Array**: классический `ARRAY` (legacy) и ассет «Array» на geometry nodes (выдаёт инстансы, Realize — опция). Из кода — классический или свой GN (файл 03). → §1 [документация 5.2]
8. **У `bmesh.ops.bevel` другие умолчания, чем у модификатора**: `affect='VERTICES'`, `segments=0`, `profile=0.0`, `clamp_overlap=False` — задавай `affect='EDGES'`, сегменты, `profile=0.5`, `clamp_overlap=True` явно. → §3.1 [проверено: D1/00 докстринг]
9. **Корпуса и «таблетки» — кольцами контура по профилю кромки** (`d1lib.rounded_slab`): квады на боковине, точные размеры, 0,02 с. → §3.2 [проверено: D1/02–04]
10. **Разрез тела на части — `bisect_plane` + `edgeloop_fill`**: две замкнутые детали из одной формы (крышка/база). → §3.3 [проверено]
11. **Тела вращения — свой `lathe` по профилю (r, z)** на bmesh: точки на оси → полюса, UV по длине профиля; профиль — гладкая кривая. → §4.1 [проверено]
12. **Трубки и ленты — протяжка с параллельным переносом рамок** (`d1lib.sweep`), не кривая с `bevel_depth`, когда нужны закрут, сужение и UV. → §4.2 [проверено]
13. **Плоский контур с отверстиями — кривая POLY с `fill_mode='BOTH'`** + extrude/bevel, `offset = −bevel` (фаска не раздувает контур), затем **сварка вершин**: без неё 3 280 неманифолдных рёбер на решётке 7×7. → §5.1 [проверено]
14. **`resolution_u` кривой — на сегмент Безье**, а не на всю кривую: 2 больших сегмента × 6 = гранёный 12-угольник; крупные дуги — 12–16. → §5.2 [проверено]
15. **3D-текст: `resolution_u` 3–6, `bevel_resolution` 1–2**: «Nova» 12/4 — 6 880 треуг., 6/2 — 2 472, 3/1 — 1 060; 3/1 гранит «o» в крупном плане. → §6.1 [проверено]
16. **Текст ставь вертикально лицом к −Y и низом на z = 0** (иначе лежит плашмя, M2.12); шрифт — встроенный или файл проекта (M1.13). → §6.1 [проверено: D1/05; C1]
17. **SVG → `bpy.ops.import_curve.svg(filepath=…)`** (5.2.2, работает в фоне); `wm.svg_import` не существует; `wm.grease_pencil_import_svg` импортирует в Grease Pencil. Кривые приходят крошечными (px → м) — масштабировать. → §6.2 [проверено]
18. **Меш из кривой, текста, SVG — сварить** (`d1lib.weld_mesh`): `new_from_object` оставляет швы заливки и фаски несваренными. → §5.1 [проверено]
19. **Масштаб объекта = 1, размеры в вершинах**: толщина Solidify, ширина Bevel и шаг Array считаются в локальных координатах. → §2.2 [документация 5.2; C1 M2.10]
20. **Модификатор «правь поверх», bmesh «пересобери»**: в `build(P)` геометрию строит bmesh из параметров, модификаторы — только неразрушающая отделка (Bevel, WN, Mirror, Array), которая применяется при экспорте. → §2 [мнение D1 по экспериментам 01–07]

## 1. Модификаторы 5.2.2: свойства, умолчания, значения для веба

Имена свойств и умолчания — из RNA Blender 5.2.2 (зонд D1/00); смысл и предупреждения — руководство 5.2 (через заметки
помощника); «для веба» — значения из экспериментов D1 [проверено] или [мнение D1].

| Тип (`modifiers.new`) | Ключевые свойства и умолчания 5.2.2 | Для веба (D1) | Ловушки |
|---|---|---|---|
| `BEVEL` | `width` 0,1; `segments` 1; `limit_method` ANGLE, `angle_limit` 30°; `offset_type` OFFSET\|WIDTH\|DEPTH\|PERCENT\|ABSOLUTE; `profile` 0,5; `use_clamp_overlap` True; `harden_normals` False; `miter_outer` MITER_SHARP\|PATCH\|ARC; `edge_weight` 'bevel_weight_edge' | 1–3 % размера детали; 1 сегм. (дёшево) или 3 + `harden_normals` (глянец) | без harden/WN — полосы (D1/01); ширина в локальных единицах — масштаб применить |
| `SUBSURF` | `levels` 1, `render_levels` 2, `quality` 3, `use_creases` True, `use_limit_surface` True; новое: `use_adaptive_subdivision` (Cycles) | 1–2 и применить; hard-surface — с опорами или не использовать | экспорт берёт `levels`; ×4 граней на уровень; без опор — «подушка» (D1/01) |
| `SOLIDIFY` | `thickness` 0,01, `offset` −1, `use_even_offset` False, `use_rim` True, `use_flip_normals`, `material_offset`, `solidify_mode` EXTRUDE\|NON_MANIFOLD | стенки листов; контур inverted hull (−t, flip, offset материала) | Complex «much slower»; толщина приближённая |
| `ARRAY` (legacy) | `count` 2, `relative_offset_displace` (1,0,0), `use_merge_vertices` False, `fit_type`, `offset_object`, `start_cap`/`end_cap` | повторы деталей; для инстансов в glTF — GN (файл 03) | Fit считает по локальному размеру |
| `MIRROR` | `use_axis` [T,F,F], `use_mirror_merge` True, `merge_threshold` 0,001, `use_clip` False, `use_bisect_axis` | первым в стеке; половина модели кодом | вершины не на оси — шов; `use_x` не существует (B) |
| `BOOLEAN` | `solver` **EXACT** \| FLOAT \| MANIFOLD; `operation` DIFFERENCE; `operand_type` OBJECT\|COLLECTION; `use_self`, `use_hole_tolerant` (только Exact); `double_threshold` 1e-6 | EXACT + очистка (§ файла 05) | `'FAST'` → ошибка (стало FLOAT, 5.0); Manifold работает только на манифолд-мешах |
| `WELD` | `mode` ALL\|CONNECTED, `merge_threshold` 0,001 | после Boolean/склеек | слипание мелких деталей при крупном пороге |
| `WEIGHTED_NORMAL` | `weight` 50, `mode` FACE_AREA\|CORNER_ANGLE\|FACE_AREA_WITH_ANGLE, `thresh` 0,01, `keep_sharp` False, `use_face_influence` False | последним; `keep_sharp=True` | требование Auto Smooth в 5.2 нет; без apply нормали теряются в glTF |
| `TRIANGULATE` | `quad_method` SHORTEST_DIAGONAL, `ngon_method` BEAUTY\|CLIP, `min_vertices` 4, `keep_custom_normals` False | перед запеканием нормалей (фиксирует разбиение) | мешает SubD |
| `DISPLACE` | `strength` 1, `mid_level` 0,5, `direction` NORMAL, `texture_coords` LOCAL\|GLOBAL\|OBJECT\|UV | органика; проще — `d1lib.noise_displace` в вершины | процедурная текстура — только через apply |
| `SCREW` | `steps`/`render_steps` 16, `angle` 2π, `axis` Z, `screw_offset` 0, `use_merge_vertices` False | тела вращения из профиля-меша; кодом проще свой `lathe` | без merge — шов на 360° |
| `SKIN` | `branch_smoothing` 0, `use_smooth_shade` False | каркас «трубок» из рёбер (маскоты, ветви) [не проверено] | радиусы — в данных вершин skin |
| `WIREFRAME` | `thickness` 0,02, `use_even_offset` True, `use_replace` True | «сетчатые» скульптуры | треугольники ×(8–12) |
| `REMESH` | `mode` VOXEL\|SHARP\|SMOOTH\|BLOCKS, `voxel_size` 0,1, `adaptivity` 0 | сварить булевы/метаболы в один объём; затем Decimate | voxel 0,1 м по умолчанию — для 10-см объекта грубо |
| `DECIMATE` | `decimate_type` COLLAPSE\|UNSUBDIV\|DISSOLVE, `ratio` 1, `angle_limit` 5°, `use_symmetry`, `delimit` | LOD готовых ассетов (файл 05 §5) | стиль и low-poly — параметрами, не Decimate [V:H1oNuKChsdU 26:17] |
| `SHRINKWRAP` | `wrap_method` NEAREST_SURFACEPOINT\|PROJECT\|NEAREST_VERTEX\|TARGET_PROJECT, `wrap_mode` ON_SURFACE…, `offset` 0 | «прилипание» деталей к кривой поверхности [не проверено] | — |
| `LATTICE`, `SIMPLE_DEFORM`, `CURVE`, `CAST` | Simple Deform `deform_method` TWIST\|BEND\|TAPER\|STRETCH, `angle` 45°; Curve `deform_axis` POS_X…; Cast SPHERE\|CYLINDER\|CUBOID | изгиб плоской детали по цилиндру: Bend → Weld → SubD [V:MD1QmdqXRfc 27:08] | деформация по оси объекта — pivot важен |
| `EDGE_SPLIT` | `split_angle` 30° | **не использовать** | «not advised to use it in new projects» (руководство 5.2) |
| «Smooth by Angle» (ассет, NODES) | входы Mesh, Angle, Ignore Sharpness | вместо удалённого Auto Smooth; экспорт только с apply | в фоне оператор `modifier_add_node_group` отменяется (B) |

### 1.1. Проверка имён и типов

Неверный тип → `TypeError` со списком; тип, несовместимый с объектом (GREASE_PENCIL_* на меше) → `modifiers.new()` вернёт
`None`; устаревшее имя свойства → `AttributeError` (`MirrorModifier.use_x` → `use_axis[0]`; `BevelModifier.use_only_vertices`
→ `affect='VERTICES'`) [проверено: B `../03-bpy-api/01 §7.1`]. `bpyx.add_modifier` превращает всё это в понятную ошибку с
подсказкой.

### 1.2. Порядок и «Pin to Last»

Модификаторы вычисляются сверху вниз; новые добавляются в конец; «Applying a modifier that is not first in the stack will
ignore the stack order» (руководство 5.2 — через заметки помощника). Weighted Normal, Triangulate и «Smooth by Angle» держат
последними (`use_pin_to_last`). Порядок из кода: `ob.modifiers.move(from, to)` (B).

### 1.3. «Smooth by Angle» без окна

`d1lib.smooth_by_angle_modifier(ob, 30)` загружает группу из
`bpy.utils.system_resource("DATAFILES", path="assets/nodes")/geometry_nodes_essentials.blend` (`libraries.load(link=False)`),
ставит модификатор NODES и входы через `mod.properties.inputs` + `update_tag()` (API 5.2, B `../03-bpy-api/02 §5.2`).
При экспорте с apply цилиндр 32 даёт 130 вершин glTF — как `set_sharp_from_angle` [проверено: D1/_lib t08]. Для веба
модификатор не нужен: данные `sharp_edge` переживают экспорт и без apply (E `../08-export-gltf/01 §4.2`).

## 2. Стеки для типичных задач

### 2.1. Рабочие стеки

| Задача | Стек (сверху вниз) | Где проверено |
|---|---|---|
| hard-surface корпус с вырезами | (Mirror) → Boolean EXACT → применить + Weld + limited dissolve → Bevel (angle 30°, 1–3 сегм., harden) → Weighted Normal (keep_sharp) | D1/01 C, D1/03 |
| мягкий корпус/иконка | без модификаторов: `rounded_slab` с профилем кромки | D1/03, D1/04 |
| SubD-форма с жёсткими кромками | Bevel `segments=2, profile=1.0` (опоры) → Subdivision 1–2 → применить | D1/01 F2; W4/02 |
| повтор деталей | Array (legacy) → применить; для веба лучше GN-инстансы (файл 03) | D1/07 |
| контур «inverted hull» | … → Solidify (`thickness<0`, `use_flip_normals`, `material_offset=1`, `use_rim=False`) последним, материал контура с backface culling | [не проверено в D1; практика A `01 §21.3`] |
| изгиб плоской детали по цилиндру | деталь плоско → Simple Deform BEND → Weld → SubD | [V:MD1QmdqXRfc 27:08] [не проверено] |

### 2.2. Масштаб

Ширина Bevel, толщина Solidify, шаг Array и радиус Displace считаются в локальных координатах объекта; при неприменённом
масштабе фаска получается разной по осям (руководство 5.2; C1 M2.10, M3.11). В `build(P)` размеры сразу в вершинах, масштаб
объекта 1 — тогда вопрос не возникает [проверено: все эксперименты D1 — `scale_applied=True`].

### 2.3. Применение

- Для экспорта в веб — `export_apply=True` (пресеты E) или `bpyx.apply_modifiers(ob)` (без оператора, материалы и группы
  вершин сохраняются, shape keys теряются) [проверено: B, E/07].
- Экспорт и `new_from_object` берут уровень **вьюпорта** (`levels`), модификаторы с `show_viewport=False` пропускаются (E/07).
- Морф-ассет: модификаторы применить до создания shape keys (E `01 §4.6`, H).

```python
# Blender 5.2.2 — [проверено] стек hard-surface с явными значениями и порядком
import sys, math; sys.path.insert(0, "../../scripts/3d")
import bpy, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
C = D.fresh_collection("ASSET_block")
ob = D.rounded_slab("Block", 0.10, 0.07, 0.035, 0.012, 0.0, C, corner_seg=6, smooth_angle=None)
cut = bpyx.primitive("cylinder", "Cut", radius=0.011, depth=0.03, segments=32, collection=C)
cut.location = (0, 0, 0.035)
rep = D.boolean_apply(ob, [cut], solver="EXACT")                    # Boolean → применить → Weld → dissolve → нормали
b = bpyx.add_modifier(ob, "BEVEL", width=0.0015, segments=3, limit_method="ANGLE", angle_limit=math.radians(30),
                      harden_normals=True, use_clamp_overlap=True, miter_outer="MITER_ARC")
wn = bpyx.add_modifier(ob, "WEIGHTED_NORMAL", weight=50, mode="FACE_AREA", keep_sharp=True)
wn.use_pin_to_last = True
try:
    bpyx.add_modifier(ob, "MIRROR", use_x=True)                     # имя 3.x → понятная ошибка, а не молчание
except AttributeError as e:
    print("ожидаемо:", str(e)[:60])
assert [m.type for m in ob.modifiers] == ["BEVEL", "WEIGHTED_NORMAL"] and rep["nonmanifold"] == 0
print(rep, D.gltf_vertex_estimate(ob))
```

## 3. bmesh: операции, умолчания, приёмы

### 3.1. Умолчания `bmesh.ops` ≠ умолчания модификатора и оператора

Сигнатуры 5.2.2 (докстринги самого Blender, зонд D1/00) [проверено]:

| Операция | Сигнатура (важное) | Возвращает | Ловушка |
|---|---|---|---|
| `bevel` | `geom, offset=0.0, offset_type='OFFSET', profile_type='SUPERELLIPSE', segments=0, profile=0.0, affect='VERTICES', clamp_overlap=False, harden_normals=False, miter_outer='SHARP'` | `faces, edges, verts` | **`affect` по умолчанию VERTICES**, `segments=0`, `profile=0.0` — задавать явно |
| `spin` | `geom, cent, axis, dvec, angle, space, steps=0, use_merge=False, use_duplicate=False` | `geom_last` | для 360° — `use_merge=True` |
| `bridge_loops` | `edges, use_pairs, use_cyclic, use_merge, merge_factor, twist_offset` | `faces, edges` | петли одинаковой длины |
| `inset_region` | `faces, thickness, depth, use_even_offset, use_boundary, use_outset` | `faces` | — |
| `extrude_face_region` | `geom, use_keep_orig, use_normal_flip, …` | `geom` | сдвиг — отдельно `translate` по вершинам из `geom` |
| `bisect_plane` | `geom, dist, plane_co, plane_no, clear_outer, clear_inner` | `geom_cut, geom` | срез потом залить (`edgeloop_fill`) |
| `edgeloop_fill` / `holes_fill` / `grid_fill` / `triangle_fill` | `edges` (+ `use_beauty` у triangle_fill) | `faces` / `geom` | edgeloop_fill — n-гон |
| `solidify` | `geom, thickness` | `geom` | без фасок и rim-настроек (как Simple) |
| `remove_doubles` | `verts, dist=0.0, use_connected` | — | dist задавать (1e-6…1e-5 м) |
| `dissolve_limit` | `angle_limit, use_dissolve_boundaries, verts, edges, delimit` | `region` | после булевых 0,5° |
| `triangulate` | `faces, quad_method='BEAUTY', ngon_method='BEAUTY'` | `faces, face_map` | — |
| `recalc_face_normals` | `faces` | — | после ручных граней обязательно |
| `create_circle` | `cap_ends=False, cap_tris=False, segments=0, radius=0.0` | `verts` | `cap_ends=True` → одна n-гонная грань (B) |

Жизненный цикл: UV-слой создать ДО `create_*`/граней, в конце `bm.to_mesh(me); bm.free()`; после изменений —
`ensure_lookup_table()` (B `../03-bpy-api/01 §6.2`, B6.1–B6.4).

```python
# Blender 5.2.2 — [проверено] bmesh.bevel с явными аргументами (умолчания — вершины!)
import math, bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=0.1)
sharp = [e for e in bm.edges if e.calc_face_angle(0) > math.radians(30)]
res = bmesh.ops.bevel(bm, geom=sharp, offset=0.002, offset_type="OFFSET", segments=3, profile=0.5,
                      affect="EDGES", clamp_overlap=True, harden_normals=False)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("Box"); bm.to_mesh(me); bm.free()
me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(30))
ob = bpy.data.objects.new("Box", me); bpy.context.scene.collection.objects.link(ob)
print(len(me.vertices), len(me.polygons), len(res["faces"]))
assert len(res["faces"]) > 0 and len(me.polygons) > 6 * 5      # скошены РЁБРА, а не вершины
```

### 3.2. Корпус кольцами контура (`rounded_slab`)

Тело строится как стопка колец контура: контур задаётся функцией смещения `outline(inset)` (скруглённый прямоугольник
с радиусом `r − inset` — точно; суперэллипс — приближённо), профиль кромки — список `(inset, z)` из `edge_profile`
(нижняя дуга, борт, верхняя дуга; `power` > 2 — мягкий переход). Боковина — только квады, крышки — выпуклые n-гоны
(или треугольники `triangulate_caps=True`), UV — развёртка боковины и планарные крышки. Телефон 71,5 × 147 × 7,8 мм — 716
треуг. (углы 8 сегм., кромка 4) за 0,02 с [проверено: D1/_lib t02, D1/02, D1/03].

### 3.3. Разрез тела на части

```python
# Blender 5.2.2 — [проверено] база и крышка из одного тела: разрез с зазором 0,3 мм
import sys, math; sys.path.insert(0, "../../scripts/3d")
import bpy, bmesh, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
C = D.fresh_collection("ASSET_case")
base = D.rounded_slab("Base", 0.0606, 0.0217, 0.0452, 0.0105, 0.0085, C, corner_seg=10, edge_seg=8, power=2.6)
lid = bpy.data.objects.new("Lid", base.data.copy()); C.objects.link(lid)
def split(ob, z, keep_above):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1),
                               clear_inner=keep_above, clear_outer=not keep_above)
    bmesh.ops.edgeloop_fill(bm, edges=[e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()
    ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(35))
split(base, 0.0335 - 0.00015, keep_above=False)
split(lid, 0.0335 + 0.00015, keep_above=True)
D.set_origin(lid, (0, 0.0217 / 2 - 0.0012, 0.0335))                   # pivot крышки — на оси петли
bm = bmesh.new(); bm.from_mesh(lid.data)
assert all(e.is_manifold for e in bm.edges); bm.free()
print(bpyx.object_stats(base)["tris"], bpyx.object_stats(lid)["tris"], tuple(round(v, 4) for v in lid.location))
```

## 4. Тела вращения и протяжка

### 4.1. `lathe` и `lathe_shell`

Профиль `(r, z)` снизу вверх; точки с `r = 0` — полюс на оси (треугольники-веер), остальное — квады; UV — угол × длина
профиля. `lathe_shell(name, outer, wall)` строит сосуд: наружный профиль → скруглённая кромка → внутренний (смещение по
нормали профиля) → дно; кружка Ø 84 × 97 мм, стенка 3,5 мм — 864 треуг., манифолд [проверено: D1/_lib t03]. Профиль —
гладкой кривой (`catmull_rom_pts`, 30–60 точек), иначе полосы затенения на каждом изломе (колокол D1/04) [проверено].
Модификатор Screw делает то же из меша-профиля, но из кода свой `lathe` проще контролировать (полюса, UV, число сегментов).

### 4.2. `sweep`: трубки, ленты, хвосты

Путь — список точек (`torus_knot_pts`, `helix_pts`, `bezier_pts`, `catmull_rom_pts`, `resample_polyline`); сечение — радиус
(круг 16 сегм.) или замкнутый контур `(u, v)`; рамки — параллельный перенос (без переворотов на перегибах, как у Frenet);
на замкнутом пути рассогласование рамки (голономия) раздаётся равномерно; `twist` — закрут; `scale(t)` — сужение; UV —
длина пути × периметр сечения. Узел (2,3) 200 × 16 — 6 400 треуг. манифолд; лента по узлу 420 × 28 — 26 400 треуг.
[проверено: D1/_lib t04, D1/06]. Кривая с `bevel_depth` быстрее пишется, но не даёт переменного закрута, сечения-контура и
управляемой UV (B `../03-bpy-api/01 §8`).

```python
# Blender 5.2.2 — [проверено] сосуд по профилю и лента по узлу с закрутом
import sys, math; sys.path.insert(0, "../../scripts/3d")
import bpy, bmesh, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
C = D.fresh_collection("ASSET_demo")
cup = D.lathe_shell("Cup", [(0.0, 0.0), (0.038, 0.0), (0.041, 0.004), (0.042, 0.095)], 0.0035, C, segments=48)
path = D.torus_knot_pts(2, 3, 0.075, 0.034, 420)
ribbon = D.sweep("Ribbon", path, D.rrect_pts(0.034, 0.0075, 0.0035, 6), C, closed=True, twist=2 * math.pi * 3,
                 smooth_angle=60)
ribbon.location.x = 0.25
for o in (cup, ribbon):
    bm = bmesh.new(); bm.from_mesh(o.data)
    assert all(e.is_manifold for e in bm.edges), o.name
    bm.free()
print(bpyx.object_stats(cup)["tris"], bpyx.object_stats(ribbon)["tris"])
```

## 5. Кривые: заливка, фаска, разрешение

### 5.1. Контур с отверстиями → тело

`d1lib.extrude_outline(name, [outer, hole1, …], depth, bevel=…)`: кривая `dimensions='2D'`, `fill_mode='BOTH'`, сплайны
POLY; `extrude = depth/2 − bevel`, `bevel_depth = bevel`, `offset = −bevel` (фаска не раздувает контур); `new_from_object`
→ меш → `weld_mesh` → острые рёбра 30°. Отверстия и вогнутости заливаются без ручной триангуляции, n-гонов 0. Решётка
60 × 60 × 4 мм с 49 отверстиями — 10 032 треуг., 8 653 вершины glTF, 0,2–0,6 с; без сварки — 3 280 неманифолдных рёбер
[проверено]. Кольцо Ø 100/40 мм — 1 280 треуг., звезда из 10 точек — 36 треуг. [проверено: D1/_lib t05].

```python
# Blender 5.2.2 — [проверено] контур с отверстиями через заливку кривой + сварка
import sys; sys.path.insert(0, "../../scripts/3d")
import bpy, bmesh, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
C = D.fresh_collection("ASSET_plate")
loops = [D.rrect_pts(0.06, 0.06, 0.008, 8)]
for i in range(3):
    for j in range(3):
        c = ((i - 1) * 0.018, (j - 1) * 0.018)
        loops.append([(c[0] + x, c[1] + y) for x, y in reversed(D.circle_pts(0.004, 16))])   # отверстие — обход назад
plate = D.extrude_outline("Plate", loops, 0.004, C, bevel=0.0004, bevel_res=1)
bm = bmesh.new(); bm.from_mesh(plate.data)
nonman = sum(1 for e in bm.edges if not e.is_manifold); ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
bm.free()
mn, mx = bpyx.world_bbox([plate])
print(nonman, ngons, bpyx.object_stats(plate)["tris"], [round(v, 4) for v in (mx - mn)])
assert nonman == 0 and ngons == 0 and abs((mx - mn).x - 0.06) < 1e-4
```

### 5.2. Разрешение — на сегмент Безье

`resolution_u` — число шагов на каждый сегмент Безье (между соседними контрольными точками), а не на всю кривую. Лист
логотипа из 2 больших сегментов при 6 шагах — 12-угольный гранёный контур (956 треуг.), при 16 — гладкий (2 556 треуг., 74 КБ);
отверстие из 4 сегментов при 6 шагах (24 точки) уже гладкое [проверено]. Правило: число точек на полный оборот
окружности ≥ 24–32 для hero-размера; крупная дуга из одного сегмента — 12–16 шагов; или уплотнить путь контрольными точками.

## 6. Текст и SVG

### 6.1. 3D-текст

`d1lib.text_mesh(name, body, size, extrude, bevel, bevel_res, resolution_u)`: кривая FONT → `new_from_object` → сварка →
поворот 90° по X (лицом к −Y) → низ базовой линии на z = 0 → острые рёбра 30°; `offset = −bevel` — буквы не толстеют от фаски.
«Nova» size 0,1 м, extrude 12 мм, bevel 2,5 мм: [проверено]

| `resolution_u` / `bevel_resolution` | Треуг. | Вершин glTF (оценка) | Вид в кадре 384 px |
|---|---|---|---|
| 12 / 4 (≈ умолчания) | 6 880 | 4 293 | гладко |
| 6 / 2 | 2 472 | 1 994 | гладко — выбор для hero-заголовка |
| 3 / 1 | 1 060 | 1 114 | «o», «a» гранёные крупно; для мелких подписей |

E/09: «Hello 3D» 12/4 → 9 968 треуг., 3/1 → 1 520 (E `../08-export-gltf/01 §4.8`). Текст для веба дешевле HTML/SDF
(F, A `01 §8.2`); 3D-текст — для hero-логотипа или предрендера. Шрифт: встроенный «Bfont Regular» (кириллица есть, B) или
файл в папке проекта; `fonts.load("/usr/share/fonts/…")` — другой вид на другой машине (M1.13).

### 6.2. SVG → меш

Оператор 5.2.2 — `bpy.ops.import_curve.svg(filepath=abs_path)` (встроенный аддон io_curve_svg включён и при
`--factory-startup`, `poll` в фоне — True); `wm.svg_import` нет; `wm.grease_pencil_import_svg` создаёт Grease Pencil (для
2D-штрихов, не для 3D-логотипа) [проверено]. Импорт даёт коллекцию кривых в метрах по viewBox (120 px → 0,12 м…
в долях) — `d1lib.svg_mesh` объединяет кривые, центрирует, масштабирует к ширине `size`, задаёт `fill_mode='BOTH'`, extrude,
bevel с `offset`, конвертирует, сваривает и ставит вертикально. Путь с отверстием (`fill-rule="evenodd"`) — отверстие
вырезано; логотип 120 × 102 × 12 мм: неманифолда 0, n-гонов 0 [проверено]. Перед импортом из SVG убрать
перекрывающиеся фигуры и 2D-блики, иконку сразу масштабировать [V:zthvZvw-yJE 00:36, 01:03].

```python
# Blender 5.2.2 — [проверено] SVG → меш заданной ширины и 3D-текст с бюджетом
import sys, os, tempfile; sys.path.insert(0, "../../scripts/3d")
import bpy, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
svg = os.path.join(tempfile.mkdtemp(), "mark.svg")
open(svg, "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path fill-rule="evenodd" '
                     'd="M 10 90 C 10 40 40 10 90 10 C 90 60 60 90 10 90 Z M 45 45 L 60 45 L 60 60 L 45 60 Z"/></svg>')
C = D.fresh_collection("ASSET_logo")
logo = D.svg_mesh("Mark", svg, C, size=0.10, depth=0.01, bevel=0.001, bevel_res=2, resolution_u=16)
txt = D.text_mesh("Title", "Nova", C, size=0.1, extrude=0.012, bevel=0.0025, bevel_res=2, resolution_u=6)
mn, mx = bpyx.world_bbox([logo])
assert abs((mx - mn).x - 0.10) < 1e-3 and (mx - mn).y < 0.011       # ширина 10 см, толщина 1 см, стоит вертикально
assert bpyx.object_stats(txt)["tris"] < 3000
print(bpyx.object_stats(logo)["tris"], bpyx.object_stats(txt)["tris"])
```

## Частые ошибки

1. **`bmesh.ops.bevel(bm, geom=edges, offset=…)` без `affect`** — скошены вершины, а не рёбра; `segments=0` [проверено].
2. **Модификатор Bevel со значениями по умолчанию** — фаска 10 см на 10-см детали [проверено: D1/00 умолчание `width=0.1`].
3. **Нода `Mesh Bevel` с одним входом `Offset`** — в режиме Edges ширина из 4 входов Start/End Left/Right Offset (0,1 м) —
   модель разрушена (файл 03 §5) [проверено: D1/01 E0].
4. **`solver='FAST'`** у Boolean — TypeError в 5.x (стало FLOAT) [B].
5. **Edge Split вместо острых рёбер данными** — разрыв меша, лишние вершины [документация 5.2].
6. **Меш из кривой/текста/SVG без сварки** — неманифолд по швам заливки и фаски [проверено].
7. **`resolution_u` «на кривую»** — крупные дуги гранёные [проверено].
8. **Текст плашмя и шрифт по пути ОС** (M2.12, M1.13) [C1].
9. **Импорт SVG «по памяти»** через несуществующий `wm.svg_import` или старый путь `bpy.ops.import_curve.svg` без абсолютного пути [проверено].
10. **Модификаторы не применены при экспорте** — в вебе голый меш (M5.5) [E/07].

## Чек-лист

- [ ] Все модификаторы созданы с явными ключевыми значениями (ширина, сегменты, решатель, keep_sharp)?
- [ ] Порядок: Mirror → Boolean → Weld → Bevel → WN (последним); SubD — только с опорами?
- [ ] Масштаб объектов 1, размеры в вершинах?
- [ ] bmesh: UV до граней, `affect/segments/profile/clamp_overlap` у bevel заданы, `to_mesh` + `free`?
- [ ] Тела вращения — по гладкому профилю; ленты — `sweep` с переносом рамок?
- [ ] Меш из кривой/текста/SVG сварен, неманифолда 0?
- [ ] Разрешение кривых: ≥ 24–32 точек на оборот для hero; текст 6/2 (hero) или 3–4/1 (подписи)?
- [ ] SVG импортирован `import_curve.svg`, масштабирован к ширине, стоит вертикально?
- [ ] Экспорт с `export_apply=True` (или модификаторы применены)?

## Открытые вопросы и противоречия

- Ассет «Array» на geometry nodes (5.2, руководство) из кода не проверялся — в D1 повторы делались GN-деревом (файл 03) и
  legacy Array. `[не проверено]`
- Skin, Shrinkwrap, Lattice, Simple Deform, Wireframe, Remesh в экспериментах D1 не запускались (кроме зонда умолчаний) —
  значения для веба в таблице §1 — `[мнение D1]` / `[не проверено]`.
- Руководство 5.2 не называет умолчания свойств — они взяты из RNA 5.2.2 (зонд), что надёжнее; расхождения руководства и RNA
  не искались.
- Inverted hull (Solidify с flip и material offset) в D1 не проверялся (эксперимент снят по решению заказчика) — описание A
  `01 §21.3` и практики `[не проверено]`.

## Источники

- [S1] Blender Foundation. Blender 5.2 Manual — Modifiers (index, introduction, common options, Bevel, Subdivision Surface,
  Solidify, Array, Array (Legacy), Mirror, Booleans, Weld, Triangulate, Edge Split, Weighted Normal, Smooth by Angle, Normal
  Edit), https://docs.blender.org/manual/en/5.2/modeling/modifiers/ — 18 страниц целиком через помощника
  (`99-raw/notes/wave2/D1-subnotes/manual-modifiers-curves.md`) [документация].
- [S2] Blender 5.2.2 RNA и докстринги `bmesh.ops` — зонд `99-raw/experiments/D1/00-api-probe/probe_modeling_api.py` →
  `probe.json` (30 модификаторов, 53 оператора, 84 GN-ноды, 83 bmesh.ops) [проверено].
- [S3] B: `../03-bpy-api/01-data-model-and-basics.md` §6–§8, `03-version-drift-3.6-to-5.2.md` §4, `snippets/bpyx.py` [проверено].
- [S4] E: `../08-export-gltf/01-export-contract.md` §4 [проверено].
- [S5] C1: `../04-ai-agents-mcp/05-failure-modes-catalog.md` (M1.13, M2.10, M2.12, M3.11) [проверено C1].
- [S6] Эксперименты D1/00–07 и `_lib/test_d1lib.py` (12/12) [проверено].
- [S7] Polyfjord, «Rendering 2D Icons as 3D Objects in Blender», 2021, https://www.youtube.com/watch?v=zthvZvw-yJE — через
  `D1-subnotes/videos-style-gn.md` [практика].
- [S8] PzThree, «Blender - Topology Fundamentals», 2023, https://www.youtube.com/watch?v=MD1QmdqXRfc — через W4 и
  `D1-subnotes/videos-topology.md` [практика].
- [S9] Ethan Redd, «Low Poly Modeling: Style Through Economy», GDC 2017, https://www.youtube.com/watch?v=H1oNuKChsdU [практика].
