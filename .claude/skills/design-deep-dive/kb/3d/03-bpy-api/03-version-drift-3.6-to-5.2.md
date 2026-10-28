# Дрейф Python API Blender 3.6 → 5.2: что изменилось и как писать для 5.2

Волна 1 · агент B · 2026-09-23 · прочитаны release notes (разделы Python API) 3.6, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5,
5.0, 5.1, 5.2 и страницы миграции (4.1 Modeling, 4.2 EEVEE и EEVEE migration, 4.4 Slotted Actions upgrading,
5.0 Compositor, 5.2 Geometry Nodes); в этом файле цитируются 22 источника · экспериментов 7 (00, 01, 02, 03, 12, 16,
19) · Blender 5.2.2 LTS, Python 3.13.13. Таблица §4 сгенерирована из `99-raw/experiments/B/03-version-drift/
drift_results.json`: каждая пара «было → стало» выполнена в чистой сцене 5.2.2. Блоки `python` с меткой
`[проверено]` выполнены автоматически.

## Выжимка для агента

1. **Считай весь код «по памяти» написанным для 3.x–4.x и проверяй в 5.2.2**: из 95 типичных фрагментов старого кода
   87 падают с исключением, 2 выдают DeprecationWarning, 6 работают с оговорками. → §4 [проверено: 03-version-drift]
2. **Ошибки дрейфа узнаваемы по тексту**: `KeyError: … key "Specular" not found`, `AttributeError: 'Mesh' object has no
   attribute 'use_auto_smooth'`, `enum "BLENDER_EEVEE_NEXT" not found`, `'SceneEEVEE' object has no attribute 'use_bloom'`,
   `'Scene' object has no attribute 'node_tree'`, `'Action' object has no attribute 'fcurves'`, `id properties not
   supported for this type`. Увидел — смотри строку таблицы. → §4 [проверено: 03]
3. **Проверка возможностей — `"x" in bpy.types.T.bl_rna.properties` и `bpy.app.version >= (5, 2, 0)`**; не
   `hasattr(bpy.types.T, "x")` (для RNA всегда False). → §1 [проверено: 03, 17]
4. **Движок: `'BLENDER_EEVEE'` (5.0+)**; `'BLENDER_EEVEE_NEXT'` существовал в 4.2–4.5; RNA перечисляет только
   `BLENDER_EEVEE` — присваивать в `try/except TypeError`. → §5.3 [проверено: 03, 13]
5. **EEVEE 4.2+ (Next)**: `use_bloom`, `use_gtao`, `gtao_distance`, `use_ssr`, `use_soft_shadows`, `shadow_cube_size`,
   `use_motion_blur` у `scene.eevee` удалены; замены — Glare в композиторе, `view_layer.eevee.ambient_occlusion_distance`,
   `use_raytracing`, `use_shadows`/`shadow_ray_count`, `scene.render.use_motion_blur`. → §5.3 [проверено: 03]
6. **Principled BSDF v2 (4.0)**: Specular → «Specular IOR Level», Transmission → «Transmission Weight», Clearcoat →
   «Coat Weight», Sheen → «Sheen Weight», Emission → «Emission Color», Subsurface → «Subsurface Weight»; индексы сдвинуты. → §5.1 [проверено: 03, 11]
7. **`use_auto_smooth` удалён (4.1)**: `me.shade_smooth(); me.set_sharp_from_angle(angle=…)` или
   `bpy.ops.object.shade_auto_smooth()`. → §5.2 [проверено: 03, 06]
8. **Слотовые действия (4.4) и удаление `Action.fcurves` (5.0)**: F-кривые — в `channelbag` слота
   (`anim_utils.action_get_channelbag_for_slot`), `action.id_root` → `slot.target_id_type`; `keyframe_insert` —
   только именованные аргументы после data_path. → §5.5 [проверено: 03, 19]
9. **Композитор 5.0**: `scene.node_tree` удалён → `scene.compositing_node_group`; Composite → Group Output; свойства
   нод (Glare «Type») стали входами-меню. → §5.4 [проверено: 03, 13]
10. **Входы модификатора GN 5.2**: `mod["Socket_2"]` → `mod.properties.inputs.Socket_2.value` + `ob.update_tag()`. → §5.6 [проверено: 02, 12]
11. **Интерфейс групп (4.0)**: `tree.inputs.new(...)` → `tree.interface.new_socket(...)`; `interface.move(item,
    to_position)`. → §5.7 [проверено: 03, 42]
12. **Словарь-override в `bpy.ops` удалён (4.0)** → `with bpy.context.temp_override(...)`. → §4 [проверено: 03]
13. **`material.use_nodes`, `world.use_nodes` (5.0), `scene.use_nodes`, `light.use_nodes` устарели — удаление в 6.0**;
    всего в 5.2.2 устаревшими помечены 32 свойства (`bpy_probe.py deprecated`). → §3 [проверено: 00-bpy-probe]
14. **Python 3.13 (5.1+)**: `imp`, `cgi`, `crypt`, `telnetlib`, `asyncore`, `asynchat`, `smtpd`, `imghdr`, `pipes`,
    `lib2to3`, `audioop`, `nntplib` удалены; `importlib.reload` вместо `imp.reload`. → §5.9 [проверено: 03, 42]
15. **Операторы импорта/экспорта**: `import_scene.obj`/`export_scene.obj` → `wm.obj_import`/`wm.obj_export` (4.0),
    `import_mesh.stl` → `wm.stl_import` (4.2), `import_mesh.ply` → `wm.ply_import` (4.0); glTF: `export_selected` →
    `use_selection`, `export_colors` → `export_vertex_color`. → §4 [проверено: 03]
16. **Официальные примеры тоже стареют**: `keyframe_insert("rotation_euler", 1)` из руководства 4.4 и
    `interface.move(item, to_index=2)` из заметок 4.0 в 5.2 дают TypeError. → §6 [проверено: 19, 42]
17. **Ответы Stack Exchange 2021–2024 по GN и auto smooth в 5.2 не работают** (`node_group.inputs`, `mod["Input_6"]`,
    путь ассета `geometry_nodes/smooth_by_angle.blend`). → §6 [проверено: 19]
18. **Порядок работы с незнакомым API**: `bpy_probe.py search <слово>` → `type`/`node`/`op` → код → запуск. → §1 [проверено: 00-bpy-probe]

## 1. Как узнать, что есть в этой сборке

```python
# Blender 5.2.2 — [проверено] проверки возможностей в рантайме
import bpy
V = bpy.app.version                                            # (5, 2, 2)
has = lambda T, name: name in T.bl_rna.properties or name in T.bl_rna.functions
checks = {
    "auto_smooth (≤4.0)": has(bpy.types.Mesh, "use_auto_smooth"),
    "Action.fcurves (≤4.5)": has(bpy.types.Action, "fcurves"),
    "scene.node_tree (≤4.5)": has(bpy.types.Scene, "node_tree"),
    "compositing_node_group (5.0+)": has(bpy.types.Scene, "compositing_node_group"),
    "NodesModifier.properties (5.2+)": has(bpy.types.NodesModifier, "properties"),
    "eevee.use_bloom (≤4.1)": has(bpy.types.SceneEEVEE, "use_bloom"),
}
print(V, checks)
assert checks == {"auto_smooth (≤4.0)": False, "Action.fcurves (≤4.5)": False, "scene.node_tree (≤4.5)": False,
                  "compositing_node_group (5.0+)": True, "NodesModifier.properties (5.2+)": True, "eevee.use_bloom (≤4.1)": False}
dep = bpy.types.Material.bl_rna.properties["use_nodes"]
print(dep.is_deprecated, dep.deprecated_note, tuple(dep.deprecated_removal_version))    # True … (6, 0, 0)
r = bpy.context.scene.render
try:
    r.engine = "BLENDER_EEVEE_NEXT"                             # 4.2–4.5
except TypeError:
    r.engine = "BLENDER_EEVEE"                                  # 5.0+
assert r.engine == "BLENDER_EEVEE"
```

- `hasattr(bpy.types.Mesh, "vertices")` → False: на КЛАССЕ видны только Python-члены (`from_pydata`,
  `shade_smooth`), даже RNA-функции (`validate`) не видны; на экземпляре `hasattr(me, "…")` работает [проверено: 03].
- Список всего, что помечено устаревшим, — `python3 ../../scripts/3d/bpy_probe.py deprecated` (§3); поиск имени —
  `bpy_probe.py search smooth`; одно свойство с вариантами — `bpy_probe.py type SceneEEVEE --own`
  [проверено: 00-bpy-probe].
- Изменения между 5.1 и 5.2 перечислены в документации API: https://docs.blender.org/api/5.2/change_log.html [S16].

## 2. Хронология: что ломало код

| Версия | Главное для кода агента |
|---|---|
| 3.6 LTS | меш хранится атрибутами (`.corner_vert`, `.edge_verts`, `sharp_face`, `.uv_seam`); `Mesh.shade_smooth()/shade_flat()`; меши без `from_pydata` гладкие по умолчанию [S20] |
| 4.0 | Principled BSDF v2 (переименования входов); `NodeTree.interface` вместо `inputs/outputs`; словарь-override в `bpy.ops` удалён; `calc_normals` удалён; bevel weight и crease — атрибуты; Face Maps удалены; `ShaderNodeBsdfGlossy` → Anisotropic; слои костей → bone collections; OBJ/PLY на Python удалены (`wm.obj_*`, `wm.ply_*`); вид по умолчанию AgX [S21] |
| 4.1 | `use_auto_smooth`/`auto_smooth_angle`, `calc_normals_split` удалены (`corner_normals`, «Smooth by Angle»); `foreach_set` строже; LightProbe `CUBEMAP/PLANAR/GRID` → `SPHERE/PLANE/VOLUME`; Musgrave слит с Noise; Python 3.11 [S22, S30] |
| 4.2 LTS | EEVEE Next: id `BLENDER_EEVEE_NEXT`, bloom удалён (→ Glare), `blend_method` → `surface_render_method`, `shadow_method` → видимость лучей, motion blur → `scene.render`; `light.cycles.cast_shadow` → `light.use_shadow`; статически типизированные IDProperties; расширения (`blender_manifest.toml`); `object.load_reference_image` → `empty_image_add` [S23, S31, S32] |
| 4.3 | удалены legacy-свойства EEVEE (`use_bloom`, `ssr_*`, `gtao_*`, `use_soft_shadows`, `shadow_cube_size`, `Material.shadow_method`); `ID.rename()`; `AttributeGroupMesh`; Grease Pencil v3 [S24] |
| 4.4 | слотовые действия (`action.slots`, `layers`, `strips`, `channelbag`); `Sequence` → `Strip`; `super().__init__` в наследниках обязателен [S25, S33] |
| 4.5 LTS | GeometrySet API; изменена дистанция Bump/Displacement; свет: exposure/normalize/temperature [S26] |
| 5.0 | `Action.fcurves/groups/id_root` удалены; `BLENDER_EEVEE_NEXT` → `BLENDER_EEVEE`; `scene.node_tree` → `compositing_node_group`, Composite → Group Output; `material/world.use_nodes` устарели; `bgl`, `Image.bindcode` удалены; `scene['cycles']` (bpy.props в dict) не работает; Separate/Combine RGB/HSV удалены; проходы рендера переименованы; Boolean 'FAST' → 'FLOAT'; `grease_pencils_v3` → `grease_pencils`; `media_type` перед `file_format`; mathutils → float32 [S27, S34] |
| 5.1 | Python 3.13; VSE `strip.frame_*` → `content_*/left_handle/right_handle` (устарели, удаление 6.0); `light.use_nodes` устарел [S28] |
| 5.2 LTS | входы GN-модификатора — `mod.properties` (IDProperty-доступ сломан); Compare/Random Value — новые identifiers; `gpu.init()` в фоне; `bpy.data.all_ids`; `NodesModifier.is_input_used`; ноды GN Mesh Bevel, списки, Bundles [S29, S35] |

## 3. Что в 5.2.2 помечено устаревшим (удаление в 6.0)

Источник — RNA самой сборки: `python3 ../../scripts/3d/bpy_probe.py deprecated` (32 пункта; поле «since» — как в RNA;
`[5, 10, 0]`, вероятно, опечатка 510 вместо 501 = 5.1 в исходнике) [проверено: 00-bpy-probe]. Доступ к этим
свойствам из Python печатает `DeprecationWarning: 'Material.use_nodes' is expected to be removed in Blender 6.0`
[проверено: 03].

| Свойство | Заметка RNA | С версии |
|---|---|---|
| `Material.use_nodes` | «Unused but kept for compatibility reasons. Setting the property has no effect, and getting it always returns True.» | 5.0 |
| `World.use_nodes` | то же | 5.0 |
| `Scene.use_nodes` | то же + «Use scene.render.use_compositing to … enable or disable compositing» | 5.0 |
| `Light.use_nodes` | то же | 5.1 («5.10») |
| `MaterialGPencilStyle.show_stroke`, `show_fill` | «Unused but kept for compatibility» | 5.1 («5.10») |
| `Strip.frame_start` → `content_start`; `frame_final_start` → `left_handle`; `frame_final_end` → `right_handle`; `frame_final_duration` → `duration`; `frame_duration` → `content_duration`; `frame_offset_start/end` → `left/right_handle_offset`; `*Strip.animation_offset_start/end` → `content_trim_start/end` (у 10 типов полос) | «Replaced by …» | 5.1 («5.10») |
| `UILayout.template_list(columns=)` | «Setting the parameter has no effect» | 5.1 |

## 4. Таблица: 95 изменений, проверенных запуском

«Было» — код в стиле туториалов и ответов 2019–2025 годов; «в 5.2.2» — что он делает на этой машине (**ERR** и текст
исключения; WARN — DeprecationWarning; «работает» — выполняется, но см. примечание). «Стало» — код для 5.2,
выполнен без ошибок в 95 из 95 случаев. «Проверка в рантайме» — выражение, по которому код может выбрать ветку
(если пусто — достаточно поймать исключение из «было»). Переменные `ob`, `p`, `m`, `mod`, `tree`, `action` — из общих
заготовок сценария (объект-куб в сцене, Principled нового материала, модификатор GN и т. д., см.
`99-raw/experiments/B/03-version-drift/drift_cases.py`) [проверено: 03-version-drift].

| № | Изменение | Версия | Было (по памяти) → в 5.2.2 | Стало (5.2) — выполнено OK | Проверка в рантайме |
|---|---|---|---|---|---|
| 1 | Principled: Specular → Specular IOR Level | 4.0 | `p.inputs["Specular"].default_value = 0.5` → **ERR** KeyError: 'bpy_prop_collection[key]: key "Specular" not found' | `p.inputs["Specular IOR Level"].default_value = 0.5` | `"Specular IOR Level" in [s.name for s in p.inputs]` |
| 2 | Principled: Subsurface → Subsurface Weight, Subsurface Color удалён | 4.0 | `p.inputs["Subsurface"].default_value = 0.2; p.inputs["Subsurface Color"].default_value = (1, 0.2, 0.2, 1)` → **ERR** KeyError: 'bpy_prop_collection[key]: key "Subsurface" not found' | `p.inputs["Subsurface Weight"].default_value = 0.2; p.inputs["Base Color"].default_value = (1, 0.2, 0.2, 1)` | исключение из «было» |
| 3 | Principled: Transmission → Transmission Weight | 4.0 | `p.inputs["Transmission"].default_value = 1.0` → **ERR** KeyError: 'bpy_prop_collection[key]: key "Transmission" not found' | `p.inputs["Transmission Weight"].default_value = 1.0` | исключение из «было» |
| 4 | Principled: Clearcoat → Coat Weight / Coat Roughness | 4.0 | `p.inputs["Clearcoat"].default_value = 1.0; p.inputs["Clearcoat Roughness"].default_value = 0.1` → **ERR** KeyError: 'bpy_prop_collection[key]: key "Clearcoat" not found' | `p.inputs["Coat Weight"].default_value = 1.0; p.inputs["Coat Roughness"].default_value = 0.1` | исключение из «было» |
| 5 | Principled: Sheen → Sheen Weight | 4.0 | `p.inputs["Sheen"].default_value = 0.5` → **ERR** KeyError: 'bpy_prop_collection[key]: key "Sheen" not found' | `p.inputs["Sheen Weight"].default_value = 0.5` | исключение из «было» |
| 6 | Principled: Emission → Emission Color (+ Emission Strength) | 4.0 | `p.inputs["Emission"].default_value = (1, 0.5, 0, 1)` → **ERR** KeyError: 'bpy_prop_collection[key]: key "Emission" not found' | `p.inputs["Emission Color"].default_value = (1, 0.5, 0, 1); p.inputs["Emission Strength"].default_value = 5.0` | исключение из «было» |
| 7 | Principled: Specular Tint стал цветом (был float) | 4.0 | `p.inputs["Specular Tint"].default_value = 0.5` → **ERR** TypeError: bpy_struct: item.attr = val: | `p.inputs["Specular Tint"].default_value = (1, 1, 1, 1)` | исключение из «было» |
| 8 | Material.use_nodes устарел (удаление в 6.0): дерево создаётся сразу | 5.0 | `m = bpy.data.materials.new("M2"); m.use_nodes = True; assert m.node_tree is not None` → WARN: DeprecationWarning ('Material.use_nodes' is expected to be removed in Blender 6.0) | `m = bpy.data.materials.new("M2"); assert m.node_tree is not None # use_nodes не нужен` | `bpy.types.Material.bl_rna.properties["use_nodes"].is_deprecated` |
| 9 | World.use_nodes устарел: мир создаётся с деревом | 5.0 | `w = bpy.data.worlds.new("W"); w.use_nodes = True; bg = w.node_tree.nodes["Background"]` → WARN: DeprecationWarning ('World.use_nodes' is expected to be removed in Blender 6.0) | `w = bpy.data.worlds.new("W"); bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs["Strength"].default_value = 0.5` | `bpy.types.World.bl_rna.properties["use_nodes"].is_deprecated` |
| 10 | blend_method → surface_render_method (EEVEE Next); blend_method — алиас | 4.2 | `m = bpy.data.materials.new("M3"); m.blend_method = "BLEND"; assert m.surface_render_method == "BLENDED"` → работает (старое работает без предупреждения: BLEND → BLENDED, OPAQUE/CLIP/HASHED → DITHERED) | `m = bpy.data.materials.new("M3"); m.surface_render_method = "BLENDED"` | `"surface_render_method" in bpy.types.Material.bl_rna.properties` |
| 11 | Material.shadow_method удалён → use_transparent_shadow | 4.3 | `m = bpy.data.materials.new("M3b"); m.shadow_method = "HASHED"` → **ERR** AttributeError: 'Material' object has no attribute 'shadow_method' | `m = bpy.data.materials.new("M3b"); m.use_transparent_shadow = True` | `"shadow_method" in bpy.types.Material.bl_rna.properties` |
| 12 | ShaderNodeBsdfGlossy — алиас, создаётся ShaderNodeBsdfAnisotropic | 4.0 | `n = bpy.data.materials.new("M4").node_tree.nodes.new("ShaderNodeBsdfGlossy"); assert n.bl_idname == "ShaderNo…` → **ERR** AssertionError: ShaderNodeBsdfAnisotropic | `n = bpy.data.materials.new("M4").node_tree.nodes.new("ShaderNodeBsdfAnisotropic"); assert n.type == "BSDF_GLOSSY"` | исключение из «было» |
| 13 | ShaderNodeSeparateRGB/CombineRGB/SeparateHSV удалены → Separate/Combine Color | 5.0 | `nt = bpy.data.materials.new("M5").node_tree; nt.nodes.new("ShaderNodeSeparateRGB")` → **ERR** RuntimeError: Error: Node type ShaderNodeSeparateRGB undefined | `nt = bpy.data.materials.new("M5").node_tree; s = nt.nodes.new("ShaderNodeSeparateColor"); s.mode = "RGB"; c = nt.nodes.new("ShaderNodeCombineColor");…` | исключение из «было» |
| 14 | Musgrave Texture удалён → Noise Texture (noise_type) | 4.1 | `bpy.data.materials.new("M6").node_tree.nodes.new("ShaderNodeTexMusgrave")` → **ERR** RuntimeError: Error: Node type ShaderNodeTexMusgrave undefined | `n = bpy.data.materials.new("M6").node_tree.nodes.new("ShaderNodeTexNoise"); n.noise_type = "RIDGED_MULTIFRACTAL"` | исключение из «было» |
| 15 | ShaderNodeMixRGB — устаревшая нода (нет в меню) → ShaderNodeMix(data_type='RGBA') | 3.4 | `n = bpy.data.materials.new("M7").node_tree.nodes.new("ShaderNodeMixRGB"); n.blend_type = "MULTIPLY"; n.inputs…` → работает (старое работает, но нода скрыта из меню; экспорт glTF и новые туториалы ориентируются на S) | `n = bpy.data.materials.new("M7").node_tree.nodes.new("ShaderNodeMix"); n.data_type = "RGBA"; n.blend_type = "MULTIPLY"; n.inputs["A"].default_value =…` | исключение из «было» |
| 16 | Sky Texture: 'NISHITA' → 'MULTIPLE_SCATTERING'/'SINGLE_SCATTERING' | 5.x | `n = bpy.data.worlds.new("W2").node_tree.nodes.new("ShaderNodeTexSky"); n.sky_type = "NISHITA"` → **ERR** TypeError: bpy_struct: item.attr = val: enum "NISHITA" not found in ('SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETH | `n = bpy.data.worlds.new("W2").node_tree.nodes.new("ShaderNodeTexSky"); n.sky_type = "MULTIPLE_SCATTERING"; n.sun_elevation = math.radians(20)` | исключение из «было» |
| 17 | Sky Texture: заметка 5.0 — sun_direction/turbidity/ground_albedo удалены | 5.0 (заметка) | `n = bpy.data.worlds.new("W3").node_tree.nodes.new("ShaderNodeTexSky"); n.sky_type = "HOSEK_WILKIE"; n.turbidi…` → работает (в 5.2.2 свойства есть в RNA (противоречие с заметкой 5.0 — там речь о входах)) | `n = bpy.data.worlds.new("W3").node_tree.nodes.new("ShaderNodeTexSky"); n.sky_type = "MULTIPLE_SCATTERING"; n.sun_elevation = math.radians(15); n.sun_…` | `"turbidity" in bpy.types.ShaderNodeTexSky.bl_rna.properties` |
| 18 | Point Density Texture удалён | 5.0 | `bpy.data.materials.new("M8").node_tree.nodes.new("ShaderNodeTexPointDensity")` → **ERR** RuntimeError: Error: Node type ShaderNodeTexPointDensity undefined | `assert not hasattr(bpy.types, "ShaderNodeTexPointDensity")` | исключение из «было» |
| 19 | material.diffuse_color красит только вьюпорт (не рендер, не glTF) | 2.8+ | `m = bpy.data.materials.new("M9"); m.diffuse_color = (1, 0, 0, 1); p = next(n for n in m.node_tree.nodes if n.…` → **ERR** AssertionError: цвет рендера не изменился | `m = bpy.data.materials.new("M9"); p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); p.inputs["Base Color"].default_value = (1, 0…` | исключение из «было» |
| 20 | Mesh.update(calc_loop_triangles=) удалён; параметры calc_edges, calc_edges_loose | 3.x | `me = bpy.data.meshes.new("U"); me.from_pydata([(0,0,0),(1,0,0),(0,1,0)], [], [(0,1,2)]); me.update(calc_edges…` → **ERR** TypeError: Mesh.update(): was called with invalid keyword argument(s) (calc_loop_triangles), expected (calc_edges, calc_ | `me = bpy.data.meshes.new("U"); me.from_pydata([(0,0,0),(1,0,0),(0,1,0)], [], [(0,1,2)]); me.validate(); me.update()` | исключение из «было» |
| 21 | use_auto_smooth/auto_smooth_angle удалены → smooth by angle | 4.1 | `ob.data.use_auto_smooth = True; ob.data.auto_smooth_angle = math.radians(30)` → **ERR** AttributeError: 'Mesh' object has no attribute 'use_auto_smooth' | `ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(30))` | `"use_auto_smooth" in bpy.types.Mesh.bl_rna.properties` |
| 22 | Mesh.calc_normals() удалён (нормали считаются сами) | 4.0 | `ob.data.calc_normals(); n = ob.data.vertices[0].normal` → **ERR** AttributeError: 'Mesh' object has no attribute 'calc_normals' | `n = ob.data.vertices[0].normal # всегда актуальны` | исключение из «было» |
| 23 | calc_normals_split()/loop.normal → Mesh.corner_normals | 4.1 | `ob.data.calc_normals_split(); n = ob.data.loops[0].normal; ob.data.free_normals_split()` → **ERR** AttributeError: 'Mesh' object has no attribute 'calc_normals_split' | `n = ob.data.corner_normals[0].vector` | исключение из «было» |
| 24 | MeshLoop.normal только для чтения → normals_split_custom_set | 4.1 | `ob.data.loops[0].normal = (0, 0, 1)` → **ERR** AttributeError: bpy_struct: attribute "normal" from "MeshLoop" is read-only | `ob.data.normals_split_custom_set([(0, 0, 1)] * len(ob.data.loops))` | исключение из «было» |
| 25 | vertex_colors (legacy) → color_attributes | 3.2 | `vc = ob.data.vertex_colors.new(name="Col"); vc.data[0].color = (1, 0, 0, 1)` → работает (vertex_colors в 5.2 ещё есть (обёртка над BYTE_COLOR/CORNER), но не видит FLOAT_COLOR и PO) | `ca = ob.data.color_attributes.new(name="Col", type="BYTE_COLOR", domain="CORNER"); ca.data[0].color = (1, 0, 0, 1); ob.data.color_attributes.active_c…` | `"vertex_colors" in bpy.types.Mesh.bl_rna.properties` |
| 26 | MeshEdge.bevel_weight удалён → атрибут bevel_weight_edge | 4.0 | `ob.data.edges[0].bevel_weight = 1.0` → **ERR** AttributeError: 'MeshEdge' object has no attribute 'bevel_weight' | `a = ob.data.attributes.get("bevel_weight_edge") or ob.data.attributes.new("bevel_weight_edge", "FLOAT", "EDGE"); a.data[0].value = 1.0` | исключение из «было» |
| 27 | MeshEdge.crease удалён → атрибут crease_edge | 4.0 | `ob.data.edges[0].crease = 1.0` → **ERR** AttributeError: 'MeshEdge' object has no attribute 'crease' | `a = ob.data.attributes.get("crease_edge") or ob.data.attributes.new("crease_edge", "FLOAT", "EDGE"); a.data[0].value = 1.0` | исключение из «было» |
| 28 | Face Maps удалены → целочисленный атрибут на гранях | 4.0 | `ob.face_maps.new(name="fm")` → **ERR** AttributeError: 'Object' object has no attribute 'face_maps' | `ob.data.attributes.new("face_group", "INT", "FACE")` | исключение из «было» |
| 29 | uv_textures → uv_layers | 2.8 | `ob.data.uv_textures.new(name="UV")` → **ERR** AttributeError: 'Mesh' object has no attribute 'uv_textures' | `ob.data.uv_layers.new(name="UV")` | исключение из «было» |
| 30 | Сглаживание без оператора: Mesh.shade_smooth()/shade_flat() | 3.6 | `for poly in ob.data.polygons:; poly.use_smooth = True` → работает (старое работает (медленно на больших мешах); новое — одна строка, атрибут sharp_face) | `ob.data.shade_smooth()` | исключение из «было» |
| 31 | scene.objects.link → collection.objects.link | 2.8 | `o = bpy.data.objects.new("E", None); bpy.context.scene.objects.link(o)` → **ERR** AttributeError: bpy_prop_collection: attribute "link" not found | `o = bpy.data.objects.new("E", None); bpy.context.scene.collection.objects.link(o)` | исключение из «было» |
| 32 | obj.select = True → select_set(True) | 2.8 | `ob.select = True` → **ERR** AttributeError: 'Object' object has no attribute 'select' | `ob.select_set(True)` | исключение из «было» |
| 33 | scene.objects.active → view_layer.objects.active | 2.8 | `bpy.context.scene.objects.active = ob` → **ERR** AttributeError: bpy_prop_collection: attribute "active" not found | `bpy.context.view_layer.objects.active = ob` | исключение из «было» |
| 34 | context.active_object только для чтения | 2.8 | `bpy.context.active_object = ob` → **ERR** AttributeError: bpy_struct: Context property "active_object" is read-only | `bpy.context.view_layer.objects.active = ob` | исключение из «было» |
| 35 | scene.update() → view_layer.update() | 2.8 | `bpy.context.scene.update()` → **ERR** AttributeError: 'Scene' object has no attribute 'update' | `bpy.context.view_layer.update()` | исключение из «было» |
| 36 | obj.hide → hide_set()/hide_viewport/hide_render | 2.8 | `ob.hide = True` → **ERR** AttributeError: 'Object' object has no attribute 'hide' | `ob.hide_set(True); ob.hide_render = True` | исключение из «было» |
| 37 | Умножение матриц: * → @ | 2.8 | `v = ob.matrix_world * Vector((0, 0, 1))` → **ERR** TypeError: Element-wise multiplication: not supported between 'Matrix' and 'Vector' types | `v = ob.matrix_world @ Vector((0, 0, 1))` | исключение из «было» |
| 38 | mathutils через buffer protocol отдаёт float32 | 5.0 | `import numpy as np; assert np.asarray(Vector((1, 2, 3))).dtype == np.float64, np.asarray(Vector((1, 2, 3))).d…` → **ERR** AssertionError: float32 | `import numpy as np; a = np.array(Vector((1, 2, 3)), dtype=np.float64) # явный dtype; assert a.dtype == np.float64` | исключение из «было» |
| 39 | Словарь-override в bpy.ops удалён → context.temp_override | 4.0 | `ov = bpy.context.copy(); ov["selected_objects"] = [ob]; bpy.ops.object.delete(ov)` → **ERR** ValueError: 1-2 args execution context is supported | `with bpy.context.temp_override(selected_objects=[ob]):; bpy.ops.object.delete()` | исключение из «было» |
| 40 | primitive_cube_add(radius=) → size= | 2.8 | `bpy.ops.mesh.primitive_cube_add(radius=1)` → **ERR** TypeError: Converting py args to operator properties:: keyword "radius" unrecognized | `bpy.ops.mesh.primitive_cube_add(size=2)` | исключение из «было» |
| 41 | primitive_*_add(view_align=) → align='WORLD' | 2.8 | `bpy.ops.mesh.primitive_uv_sphere_add(view_align=False)` → **ERR** TypeError: Converting py args to operator properties:: keyword "view_align" unrecognized | `bpy.ops.mesh.primitive_uv_sphere_add(align="WORLD")` | исключение из «было» |
| 42 | object.load_reference_image → object.empty_image_add | 4.2 | `assert hasattr(bpy.ops.object, "load_reference_image") and bpy.ops.object.load_reference_image.get_rna_type()` → **ERR** KeyError: 'get_rna_type("OBJECT_OT_load_reference_image") not found' | `assert bpy.ops.object.empty_image_add.get_rna_type()` | исключение из «было» |
| 43 | bpy.utils.register_module удалён → register_class | 2.8 | `bpy.utils.register_module(__name__)` → **ERR** AttributeError: module 'bpy.utils' has no attribute 'register_module' | `class T(bpy.types.Operator):; bl_idname = "object.drift_t"; bl_label = "T"; def execute(self, context):; return {"FINISHED"}; bpy.utils.register_clas…` | исключение из «было» |
| 44 | hasattr(bpy.types.X, 'rna_prop') всегда False → bl_rna.properties | всегда | `assert hasattr(bpy.types.Mesh, "vertices"), "hasattr на классе не видит RNA-свойства"` → **ERR** AssertionError: hasattr на классе не видит RNA-свойства | `assert "vertices" in bpy.types.Mesh.bl_rna.properties; assert "validate" in bpy.types.Mesh.bl_rna.functions` | исключение из «было» |
| 45 | import imp удалён из Python → importlib | Py3.12 (Blender 4.2+) | `import imp; imp.reload(math)` → **ERR** ModuleNotFoundError: No module named 'imp' | `import importlib; importlib.reload(math)` | исключение из «было» |
| 46 | bpy.app.version_char удалён | 4.0 | `v = bpy.app.version_char` → **ERR** AttributeError: 'bpy.app' object has no attribute 'version_char' | `v = bpy.app.version_string` | исключение из «было» |
| 47 | Модуль bgl удалён → gpu | 5.0 | `import bgl` → **ERR** ModuleNotFoundError: No module named 'bgl' | `import gpu; import gpu_extras` | исключение из «было» |
| 48 | Image.bindcode удалён → gpu.texture.from_image | 5.0 | `img = bpy.data.images.new("I", 4, 4); c = img.bindcode` → **ERR** AttributeError: 'Image' object has no attribute 'bindcode' | `img = bpy.data.images.new("I", 4, 4); assert "bindcode" not in bpy.types.Image.bl_rna.properties` | исключение из «было» |
| 49 | Свойства bpy.props больше не читаются через dict: scene['cycles'] | 5.0 | `samples = bpy.context.scene["cycles"]["samples"]` → **ERR** KeyError: 'bpy_struct[key]: key "cycles" not found' | `samples = bpy.context.scene.cycles.samples` | исключение из «было» |
| 50 | World.light_settings.use_ambient_occlusion удалён (остались ao_factor, distance) | 4.2 | `w = bpy.data.worlds.new("W4"); w.light_settings.use_ambient_occlusion = True` → **ERR** AttributeError: 'WorldLighting' object has no attribute 'use_ambient_occlusion' | `w = bpy.data.worlds.new("W4"); w.light_settings.distance = 0.5; bpy.context.view_layer.eevee.ambient_occlusion_distance = 0.5` | исключение из «было» |
| 51 | Свойства shadow buffer/falloff у Light удалены (не использовались) | 4.0 | `ld = bpy.data.lights.new("L4", "SPOT"); ld.shadow_buffer_bias = 0.1; ld.falloff_type = "INVERSE_SQUARE"` → **ERR** AttributeError: 'SpotLight' object has no attribute 'shadow_buffer_bias' | `ld = bpy.data.lights.new("L4", "SPOT"); ld.shadow_soft_size = 0.1; ld.use_shadow = True` | исключение из «было» |
| 52 | BLENDER_EEVEE_NEXT (4.2–4.5) → BLENDER_EEVEE | 5.0 | `bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"` → **ERR** TypeError: bpy_struct: item.attr = val: enum "BLENDER_EEVEE_NEXT" not found in ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'C | `bpy.context.scene.render.engine = "BLENDER_EEVEE"` | `bpy.context.scene.render.engine` |
| 53 | EEVEE bloom удалён → Glare (Bloom) в композиторе | 4.2/4.3 | `e = bpy.context.scene.eevee; e.use_bloom = True; e.bloom_intensity = 0.1` → **ERR** AttributeError: 'SceneEEVEE' object has no attribute 'use_bloom' | `scene = bpy.context.scene; tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); scene.compositing_node_group = tree; tree.interface.new_soc…` | `"use_bloom" in bpy.types.SceneEEVEE.bl_rna.properties` |
| 54 | use_gtao/gtao_distance удалены → view_layer.eevee.ambient_occlusion_distance | 5.0 | `e = bpy.context.scene.eevee; e.use_gtao = True; e.gtao_distance = 0.5` → **ERR** AttributeError: 'SceneEEVEE' object has no attribute 'use_gtao' | `bpy.context.view_layer.eevee.ambient_occlusion_distance = 0.5; bpy.context.scene.eevee.use_fast_gi = True` | исключение из «было» |
| 55 | use_ssr/use_ssr_refraction удалены → use_raytracing | 4.2/4.3 | `e = bpy.context.scene.eevee; e.use_ssr = True; e.use_ssr_refraction = True` → **ERR** AttributeError: 'SceneEEVEE' object has no attribute 'use_ssr' | `e = bpy.context.scene.eevee; e.use_raytracing = True; e.ray_tracing_method = "SCREEN"` | исключение из «было» |
| 56 | use_soft_shadows/shadow_cube_size удалены | 4.2/4.3 | `e = bpy.context.scene.eevee; e.use_soft_shadows = True; e.shadow_cube_size = "1024"` → **ERR** AttributeError: 'SceneEEVEE' object has no attribute 'use_soft_shadows' | `e = bpy.context.scene.eevee; e.use_shadows = True; e.shadow_ray_count = 2; e.shadow_resolution_scale = 1.0` | исключение из «было» |
| 57 | eevee.use_motion_blur → render.use_motion_blur | 4.2 | `bpy.context.scene.eevee.use_motion_blur = True` → **ERR** AttributeError: 'SceneEEVEE' object has no attribute 'use_motion_blur' | `bpy.context.scene.render.use_motion_blur = True; bpy.context.scene.render.motion_blur_shutter = 0.5` | исключение из «было» |
| 58 | light.cycles.cast_shadow → light.use_shadow | 4.2 | `ld = bpy.data.lights.new("L", "POINT"); ld.cycles.cast_shadow = False` → **ERR** AttributeError: 'CyclesLightSettings' object has no attribute 'cast_shadow' | `ld = bpy.data.lights.new("L", "POINT"); ld.use_shadow = False` | исключение из «было» |
| 59 | Размер источника: shadow_soft_size (точка/спот), size (area) | 2.8+ | `ld = bpy.data.lights.new("L2", "AREA"); ld.shadow_soft_size = 2.0; assert ld.size == 2.0, "размер area не изм…` → **ERR** AssertionError: размер area не изменился | `ld = bpy.data.lights.new("L2", "AREA"); ld.size = 2.0; ld2 = bpy.data.lights.new("L3", "POINT"); ld2.shadow_soft_size = 0.2` | исключение из «было» |
| 60 | ImageFormatSettings.media_type ставить до file_format (видео) | 5.0 | `bpy.context.scene.render.image_settings.file_format = "FFMPEG"` → **ERR** TypeError: bpy_struct: item.attr = val: enum "FFMPEG" not found in ('AVIF', 'JPEG', 'OPEN_EXR', 'PNG', 'WEBP', 'BMP', 'C | `s = bpy.context.scene.render.image_settings; s.media_type = "VIDEO"; s.file_format = "FFMPEG"; bpy.context.scene.render.ffmpeg.format = "MPEG4"` | исключение из «было» |
| 61 | LightProbe CUBEMAP/PLANAR/GRID → SPHERE/PLANE/VOLUME | 4.1 | `bpy.data.lightprobes.new("P", "CUBEMAP")` → **ERR** TypeError: BlendDataProbes.new(): error with argument 2, "type" -  enum "CUBEMAP" not found in ('SPHERE', 'PLANE', 'VOLU | `bpy.data.lightprobes.new("P", "SPHERE")` | исключение из «было» |
| 62 | Вид по умолчанию AgX (был Filmic); Filmic доступен | 4.0 | `assert bpy.context.scene.view_settings.view_transform == "Filmic", bpy.context.scene.view_settings.view_trans…` → **ERR** AssertionError: AgX | `vs = bpy.context.scene.view_settings; vs.view_transform = "AgX"; vs.look = "AgX - Punchy"` | исключение из «было» |
| 63 | scene.use_nodes + scene.node_tree → scene.compositing_node_group | 5.0 | `scene = bpy.context.scene; scene.use_nodes = True; tree = scene.node_tree; rl = tree.nodes["Render Layers"]` → **ERR** AttributeError: 'Scene' object has no attribute 'node_tree' | `scene = bpy.context.scene; tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); scene.compositing_node_group = tree; rl = tree.nodes.new("C…` | `"compositing_node_group" in bpy.types.Scene.bl_rna.properties` |
| 64 | CompositorNodeComposite удалён → NodeGroupOutput + сокет интерфейса | 5.0 | `tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); tree.nodes.new("CompositorNodeComposite")` → **ERR** RuntimeError: Error: Node type CompositorNodeComposite undefined | `tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor"…` | исключение из «было» |
| 65 | Glare: glare_type/threshold → входы-меню inputs['Type'], ['Threshold'] | 5.0/5.1 | `tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); g = tree.nodes.new("CompositorNodeGlare"); g.g…` → **ERR** AttributeError: 'CompositorNodeGlare' object has no attribute 'glare_type' | `tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); g = tree.nodes.new("CompositorNodeGlare"); g.inputs["Type"].default_value = "Bloom"; g…` | исключение из «было» |
| 66 | Часть нод композитора заменена шейдерными: CompositorNodeGamma → ShaderNodeGamma | 5.0 | `tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); tree.nodes.new("CompositorNodeGamma")` → **ERR** RuntimeError: Error: Node type CompositorNodeGamma undefined | `tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree"); tree.nodes.new("ShaderNodeGamma")` | исключение из «было» |
| 67 | Имена проходов: DiffCol → Diffuse Color, IndexMA → Material Index, Z → Depth | 5.0 | `bpy.context.view_layer.use_pass_diffuse_color = True; bpy.context.view_layer.use_pass_z = True; tree = bpy.da…` → **ERR** KeyError: 'bpy_prop_collection[key]: key "DiffCol" not found' | `bpy.context.view_layer.use_pass_diffuse_color = True; bpy.context.view_layer.use_pass_z = True; tree = bpy.data.node_groups.new("Comp", "CompositorNo…` | исключение из «было» |
| 68 | Action.fcurves удалён → channelbag слота | 5.0 | `for fc in action.fcurves:; fc.keyframe_points[0].interpolation = "LINEAR"` → **ERR** AttributeError: 'Action' object has no attribute 'fcurves' | `from bpy_extras import anim_utils; cb = anim_utils.action_get_channelbag_for_slot(action, ob.animation_data.action_slot); for fc in cb.fcurves:; fc.k…` | `"fcurves" in bpy.types.Action.bl_rna.properties` |
| 69 | action.fcurves.new(action_group=) → channelbag.fcurves.new(group_name=) | 5.0 | `act = bpy.data.actions.new("A"); fc = act.fcurves.new("location", index=0, action_group="Object Transform")` → **ERR** AttributeError: 'Action' object has no attribute 'fcurves' | `act = bpy.data.actions.new("A"); slot = act.slots.new(id_type="OBJECT", name="Obj"); from bpy_extras import anim_utils; cb = anim_utils.action_ensure…` | исключение из «было» |
| 70 | action.id_root удалён → slot.target_id_type | 5.0 | `act = bpy.data.actions.new("A"); act.id_root = "OBJECT"` → **ERR** AttributeError: 'Action' object has no attribute 'id_root' | `act = bpy.data.actions.new("A"); slot = act.slots.new(id_type="OBJECT", name="Obj"); assert slot.target_id_type == "OBJECT"` | исключение из «было» |
| 71 | Назначение action другому объекту: без слота объект не анимирован | 4.4 | `o2 = bpy.data.objects.new("O2", None); bpy.context.scene.collection.objects.link(o2); o2.animation_data_creat…` → **ERR** AssertionError: слот не назначен | `o2 = bpy.data.objects.new("O2", None); bpy.context.scene.collection.objects.link(o2); ad = o2.animation_data_create(); ad.action = action; if ad.acti…` | исключение из «было» |
| 72 | keyframe_insert: всё после data_path — только именованные аргументы | ? | `ob.keyframe_insert("location", -1, 10)` → **ERR** TypeError: bpy_struct.keyframe_insert()() takes at most 1 positional argument (3 given) | `ob.keyframe_insert("location", index=-1, frame=10)` | исключение из «было» |
| 73 | options={'INSERTKEY_XYZ_TO_RGB'} удалён | 5.0 | `ob.keyframe_insert("location", frame=1, options={"INSERTKEY_XYZ_TO_RGB"})` → **ERR** ValueError: bpy_struct.keyframe_insert(): 'INSERTKEY_XYZ_TO_RGB' not found in ('INSERTKEY_NEEDED', 'INSERTKEY_VISUAL', ' | `ob.keyframe_insert("location", frame=1, options={"INSERTKEY_NEEDED"})` | исключение из «было» |
| 74 | Слои костей → bone collections | 4.0 | `arm = bpy.data.armatures.new("Arm"); arm.layers[1] = True` → **ERR** AttributeError: 'Armature' object has no attribute 'layers' | `arm = bpy.data.armatures.new("Arm"); bc = arm.collections.new("Deform"); assert bc.name == "Deform"` | исключение из «было» |
| 75 | Bone.select удалён → pose bone .select / edit bone .select | 5.0 | `arm = bpy.data.armatures.new("Arm"); ao = bpy.data.objects.new("ArmO", arm); bpy.context.scene.collection.obj…` → **ERR** AttributeError: 'Bone' object has no attribute 'select' | `arm = bpy.data.armatures.new("Arm"); ao = bpy.data.objects.new("ArmO", arm); bpy.context.scene.collection.objects.link(ao); bpy.context.view_layer.ob…` | исключение из «было» |
| 76 | NodeTree.inputs.new → tree.interface.new_socket | 4.0 | `g = bpy.data.node_groups.new("G", "GeometryNodeTree"); g.inputs.new("NodeSocketFloat", "Size")` → **ERR** AttributeError: 'GeometryNodeTree' object has no attribute 'inputs' | `g = bpy.data.node_groups.new("G", "GeometryNodeTree"); s = g.interface.new_socket(name="Size", in_out="INPUT", socket_type="NodeSocketFloat"); s.defa…` | исключение из «было» |
| 77 | socket_type только базовый: NodeSocketFloatFactor → NodeSocketFloat + subtype | 4.0 | `g = bpy.data.node_groups.new("G", "GeometryNodeTree"); g.interface.new_socket(name="F", in_out="INPUT", socke…` → **ERR** TypeError: NodeTreeInterface.new_socket(): error with keyword argument "socket_type" -  enum "NodeSocketFloatFactor" not | `g = bpy.data.node_groups.new("G", "GeometryNodeTree"); s = g.interface.new_socket(name="F", in_out="INPUT", socket_type="NodeSocketFloat"); s.subtype…` | исключение из «было» |
| 78 | Элементы интерфейса можно искать по identifier | 5.0 | `item = [i for i in tree.interface.items_tree if i.name == "Size"][0]` → работает (оба варианта работают; по имени — неоднозначно при повторах) | `item = tree.interface.items_tree[size.identifier]` | исключение из «было» |
| 79 | mod['Socket_1'] → mod.properties.inputs.Socket_1.value | 5.2 | `mod[size.identifier] = 2.0` → **ERR** TypeError: bpy_struct[key] = val: id properties not supported for this type | `getattr(mod.properties.inputs, size.identifier).value = 2.0` | `hasattr(mod, "properties")` |
| 80 | mod['Socket_1_use_attribute'] → .type = 'ATTRIBUTE' | 5.2 | `mod[size.identifier + "_use_attribute"] = True; mod[size.identifier + "_attribute_name"] = "w"` → **ERR** TypeError: bpy_struct[key] = val: id properties not supported for this type | `i = getattr(mod.properties.inputs, size.identifier); i.type = "ATTRIBUTE"; i.attribute_name = "w"` | исключение из «было» |
| 81 | Идентификаторы входов 3.x Input_2 → Socket_N (4.0+) | 4.0 | `mod["Input_2"] = 2.0` → **ERR** TypeError: bpy_struct[key] = val: id properties not supported for this type | `ident = next(i.identifier for i in tree.interface.items_tree if i.item_type == "SOCKET" and i.in_out == "INPUT" and i.name == "Size"); getattr(mod.pr…` | исключение из «было» |
| 82 | Свойства GN-нод стали входами-меню: Resample Curve mode → inputs['Mode'] | 5.x | `n = tree.nodes.new("GeometryNodeResampleCurve"); n.mode = "COUNT"` → **ERR** AttributeError: 'GeometryNodeResampleCurve' object has no attribute 'mode' | `n = tree.nodes.new("GeometryNodeResampleCurve"); n.inputs["Mode"].default_value = "Count"; n.inputs["Count"].default_value = 32` | исключение из «было» |
| 83 | Random Value: один динамический выход Value (нет Value_001, outputs[1]) | 5.2 | `r = tree.nodes.new("FunctionNodeRandomValue"); r.data_type = "FLOAT"; out = r.outputs[1]` → **ERR** IndexError: bpy_prop_collection[index]: index 1 out of range, size 1 | `r = tree.nodes.new("FunctionNodeRandomValue"); r.data_type = "FLOAT"; out = r.outputs["Value"]; r.inputs["Min"].default_value = 0.5` | исключение из «было» |
| 84 | Compare: identifiers A_INT/B_VEC3 исчезли (динамические A/B) | 5.2 | `c = tree.nodes.new("FunctionNodeCompare"); c.data_type = "INT"; c.inputs["A_INT"].default_value = 3` → **ERR** KeyError: 'bpy_prop_collection[key]: key "A_INT" not found' | `c = tree.nodes.new("FunctionNodeCompare"); c.data_type = "INT"; c.inputs["A"].default_value = 3` | исключение из «было» |
| 85 | GN Color node: color → value (Node.color — это цвет рамки ноды!) | 4.2 | `n = tree.nodes.new("FunctionNodeInputColor"); n.color = (1, 0, 0, 1)` → **ERR** ValueError: bpy_struct: item.attr = val: sequences of dimension 0 should contain 3 items, not 4 | `n = tree.nodes.new("FunctionNodeInputColor"); n.value = (1, 0, 0, 1)` | исключение из «было» |
| 86 | export_format='GLTF_EMBEDDED' доступен только при allow_embedded_format в настройках аддона | 4.2+ | `bpy.ops.export_scene.gltf(filepath=os.path.join(TMP, "c.gltf"), export_format="GLTF_EMBEDDED")` → **ERR** TypeError: Converting py args to operator properties: enum "GLTF_EMBEDDED" not found in ('GLB', 'GLTF_SEPARATE') | `bpy.ops.export_scene.gltf(filepath=os.path.join(TMP, "c.glb"), export_format="GLB")` | исключение из «было» |
| 87 | import_scene.obj → wm.obj_import | 4.0 | `bpy.ops.import_scene.obj(filepath=os.path.join(TMP, "x.obj"))` → **ERR** AttributeError: Calling operator "bpy.ops.import_scene.obj" error, could not be found | `bpy.ops.wm.obj_export(filepath=os.path.join(TMP, "x.obj")); bpy.ops.wm.obj_import(filepath=os.path.join(TMP, "x.obj"))` | исключение из «было» |
| 88 | export_scene.obj → wm.obj_export | 4.0 | `bpy.ops.export_scene.obj(filepath=os.path.join(TMP, "y.obj"))` → **ERR** AttributeError: Calling operator "bpy.ops.export_scene.obj" error, could not be found | `bpy.ops.wm.obj_export(filepath=os.path.join(TMP, "y.obj"), export_selected_objects=False)` | исключение из «было» |
| 89 | import_mesh.stl → wm.stl_import | 4.2 | `bpy.ops.import_mesh.stl(filepath=os.path.join(TMP, "z.stl"))` → **ERR** AttributeError: Calling operator "bpy.ops.import_mesh.stl" error, could not be found | `bpy.ops.wm.stl_export(filepath=os.path.join(TMP, "z.stl")); bpy.ops.wm.stl_import(filepath=os.path.join(TMP, "z.stl"))` | исключение из «было» |
| 90 | import_mesh.ply → wm.ply_import | 4.0 | `bpy.ops.import_mesh.ply(filepath=os.path.join(TMP, "w.ply"))` → **ERR** AttributeError: Calling operator "bpy.ops.import_mesh.ply" error, could not be found | `bpy.ops.wm.ply_export(filepath=os.path.join(TMP, "w.ply")); bpy.ops.wm.ply_import(filepath=os.path.join(TMP, "w.ply"))` | исключение из «было» |
| 91 | glTF: export_selected → use_selection | 3.x | `bpy.ops.export_scene.gltf(filepath=os.path.join(TMP, "a.glb"), export_selected=True)` → **ERR** TypeError: Converting py args to operator properties:: keyword "export_selected" unrecognized | `bpy.ops.export_scene.gltf(filepath=os.path.join(TMP, "a.glb"), use_selection=True, export_format="GLB")` | исключение из «было» |
| 92 | glTF: export_colors → export_vertex_color | 4.2 | `bpy.ops.export_scene.gltf(filepath=os.path.join(TMP, "b.glb"), export_colors=True)` → **ERR** TypeError: Converting py args to operator properties:: keyword "export_colors" unrecognized | `bpy.ops.export_scene.gltf(filepath=os.path.join(TMP, "b.glb"), export_vertex_color="ACTIVE")` | исключение из «было» |
| 93 | Boolean solver 'FAST' → 'FLOAT' | 5.0 | `b = ob.modifiers.new("B", "BOOLEAN"); b.solver = "FAST"` → **ERR** TypeError: bpy_struct: item.attr = val: enum "FAST" not found in ('FLOAT', 'EXACT', 'MANIFOLD') | `b = ob.modifiers.new("B", "BOOLEAN"); b.solver = "FLOAT" # или "EXACT", "MANIFOLD"` | исключение из «было» |
| 94 | grease_pencils_v3 → grease_pencils (GP v3); старый GP → annotations | 4.3/5.0 | `gp = bpy.data.grease_pencils_v3.new("GP")` → **ERR** AttributeError: 'BlendData' object has no attribute 'grease_pencils_v3' | `gp = bpy.data.grease_pencils.new("GP"); assert gp.bl_rna.identifier == "GreasePencil"; an = bpy.data.annotations.new("A")` | исключение из «было» |
| 95 | Sequence → Strip; sequence_editor.sequences → strips | 4.4/5.0 | `se = bpy.context.scene.sequence_editor_create(); s = se.sequences.new_effect(name="C", type="COLOR", channel=…` → **ERR** AttributeError: 'SequenceEditor' object has no attribute 'sequences' | `se = bpy.context.scene.sequence_editor_create(); s = se.strips.new_effect(name="C", type="COLOR", channel=1, frame_start=1, length=10)` | исключение из «было» |

_Строк: 95; «стало» OK: 95/95; «было»: ERR 87, WARN 2, OK 6 (Blender 5.2.2 LTS)._

Дополнительные изменения, проверенные в других экспериментах:

| № | Изменение | Версия | Было → в 5.2.2 | Стало (5.2) | Эксперимент |
|---|---|---|---|---|---|
| 96 | Поиск сокета Mix/Map Range по identifier | 4.0/5.2 | `mix.inputs["A_Color"]` → **ERR** KeyError (запрет в исходнике) | режим, затем `mix.inputs["A"]` | 01-socket-lookup |
| 97 | Связь с сокетом, взятым до смены `data_type` | 4.0+ | `links.new(x, a_old)` → тихо: `is_valid == False` | режим до поиска сокета | 01-socket-lookup |
| 98 | Входы GN не пересчитываются после присвоения | 5.2 | `mod.properties.inputs.X.value = v` → результат прежний даже после `view_layer.update()` | + `ob.update_tag()` | 12-geonodes |
| 99 | `NodeTreeInterface.move` | 4.0 → 5.2 | `interface.move(item, to_index=0)` → **ERR** `TypeError: … required parameter "to_position" not specified` | `interface.move(item, 0)` / `to_position=0` | 42-doc-snippets |
| 100 | Предел имени ID | ? (не установлена) | совет «имена ≤ 63 байт» → в 5.2.2 до 255 байт | учитывать 255 байт | 05-data-model |
| 101 | `keyframe_insert` с позиционным index (руководство 4.4) | 5.x | `keyframe_insert("rotation_euler", 1)` → **ERR** `TypeError: … takes at most 1 positional argument (2 given)` | `keyframe_insert("rotation_euler", index=1)` | 19-stackexchange-snippets |
| 102 | Путь ассета «Smooth by Angle» | 5.x | `modifier_add_node_group(…, relative_asset_identifier="geometry_nodes/smooth_by_angle.blend/…")` → тихо `{'CANCELLED'}` | `bpy.data.libraries.load(<DATAFILES>/assets/nodes/geometry_nodes_essentials.blend)` или `object.shade_auto_smooth()` | 19-stackexchange-snippets |
| 103 | `node_group.inputs` для GN | 4.0 | `for s in mod.node_group.inputs` → **ERR** AttributeError | `mod.node_group.interface.items_tree` | 19-stackexchange-snippets |
| 104 | Приватные модули Blender | 5.0 | `import rna_info` → **ERR** ModuleNotFoundError | не использовать (внутренние `_rna_info`, `_keyingsets_utils`) | 42-doc-snippets |
| 105 | Модули стандартной библиотеки Python 3.13 | 5.1 | `import imp` (и `cgi`, `crypt`, `telnetlib`, `asyncore`, `imghdr`, `pipes`, `lib2to3`, `audioop`) → **ERR** ModuleNotFoundError | `importlib`, `mimetypes`, `shlex`, `subprocess` | 03, 42-doc-snippets |
| 106 | Collada удалена | 5.0 | `bpy.ops.wm.collada_export(filepath=…)` → **ERR** KeyError (оператора нет) | glTF (`export_scene.gltf`) или USD (`wm.usd_export`) | X/02 |

## 5. Крупные темы подробно

### 5.1 Principled BSDF v2 (4.0)

| 3.x (имя, индекс) | 5.2 (имя = identifier, индекс) | Примечание |
|---|---|---|
| Subsurface [1] | Subsurface Weight [9] | |
| Subsurface Color [3] | — | удалён, цвет SSS = Base Color |
| Metallic [6] | Metallic [1] | |
| Specular [7] | Specular IOR Level [14] | в 5.2 `inputs[7]` — скрытый «Weight» |
| Specular Tint [8] (float) | Specular Tint [15] (цвет) | `= 0.5` → TypeError |
| Roughness [9] | Roughness [2] | в 5.2 `inputs[9]` — Subsurface Weight |
| Clearcoat / Clearcoat Roughness / Clearcoat Normal | Coat Weight [20] / Coat Roughness [21] / Coat Normal [24] | + Coat IOR, Coat Tint |
| Sheen (float) | Sheen Weight [25] | + Sheen Roughness, Sheen Tint (цвет) |
| Transmission | Transmission Weight [19] | |
| Emission (цвет, по умолчанию чёрный) | Emission Color [28] (белый) + Emission Strength [29] (0) | свечение — только при Strength > 0 |
| — | Thin Film Thickness [30], Thin Film IOR [31] | 4.2 |
| — | Diffuse Roughness [8], Thin Wall [5] | новые |

Индексы 3.x даны по раскладке 3.6 для сравнения [S21; «было» 3.x — по памяти практиков, «стало» проверено: 11].
Помощник с переводом имён 3.x — `bpyx.principled(...)` [проверено: 40-bpyx-tests].

```python
# Blender 5.2.2 — [проверено] перевод имён входов Principled из 3.x в 5.2
import bpy
RENAMED = {"Specular": "Specular IOR Level", "Subsurface": "Subsurface Weight", "Transmission": "Transmission Weight",
           "Clearcoat": "Coat Weight", "Clearcoat Roughness": "Coat Roughness", "Clearcoat Normal": "Coat Normal",
           "Sheen": "Sheen Weight", "Emission": "Emission Color"}
def set_principled(p, name, value):
    name = name if name in p.inputs else RENAMED.get(name, name)
    s = p.inputs[name]                                        # KeyError, если имени нет и в 5.2
    if s.type == "RGBA" and len(value) == 3:
        value = (*value, 1.0)
    s.default_value = value
mat = bpy.data.materials.new("Legacy")
p = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
for k, v in {"Specular": 0.3, "Clearcoat": 1.0, "Emission": (1, 0.4, 0.1), "Roughness": 0.25}.items():
    set_principled(p, k, v)
p.inputs["Emission Strength"].default_value = 2.0
assert abs(p.inputs["Coat Weight"].default_value - 1.0) < 1e-6 and p.inputs[7].name == "Weight"
```

### 5.2 Auto smooth → Smooth by Angle (4.1)

Три пути и их последствия — в `01-data-model-and-basics.md §6.7`. Кратко: `me.use_auto_smooth = True` →
`AttributeError`; data API — `me.shade_smooth(); me.set_sharp_from_angle(angle=…)`; неразрушающе —
`bpy.ops.object.shade_auto_smooth(angle=…)` (модификатор-ассет «Smooth by Angle», вход `Input_1` — угол); для
Weighted Normal и Bevel с `harden_normals` включать auto smooth больше не нужно (базовое состояние меша = старый auto
smooth 180°) [S30; проверено: 03, 06]. Ассет в 5.2 лежит в `datafiles/assets/nodes/geometry_nodes_essentials.blend`;
оператор `modifier_add_node_group` в фоне его не загружает («Asset loading is unfinished») [проверено: 19].

### 5.3 EEVEE Next (4.2) и 5.0

| Было (EEVEE Legacy, ≤ 4.1) | 5.2 | Проверено |
|---|---|---|
| `render.engine = 'BLENDER_EEVEE'` (legacy) | `'BLENDER_EEVEE'` (это EEVEE Next; в 4.2–4.5 назывался `'BLENDER_EEVEE_NEXT'`) | 03, 13 |
| `eevee.use_bloom`, `bloom_threshold`, `bloom_intensity`, … | композитор: Glare `inputs["Type"] = "Bloom"` | 03, 13 |
| `eevee.use_gtao`, `gtao_distance`, `gtao_factor` | `view_layer.eevee.ambient_occlusion_distance`; `eevee.use_fast_gi`, `fast_gi_*` | 03 |
| `eevee.use_ssr`, `use_ssr_refraction`, `ssr_*` | `eevee.use_raytracing`, `ray_tracing_method` ('SCREEN'/'PROBE'), `ray_tracing_options` | 03 |
| `eevee.use_soft_shadows`, `shadow_cube_size`, `shadow_cascade_size` | `eevee.use_shadows`, `shadow_ray_count`, `shadow_step_count`, `shadow_resolution_scale`; у света `use_shadow_jitter` | 03 |
| `eevee.use_motion_blur`, `motion_blur_shutter` | `render.use_motion_blur`, `render.motion_blur_shutter` | 03 |
| `material.blend_method = 'BLEND'` | `material.surface_render_method = 'BLENDED'` (`blend_method` ещё принимается как алиас) | 03 |
| `material.shadow_method = 'HASHED'` | `material.use_transparent_shadow`; объект: видимость для теней | 03 |
| `light.cycles.cast_shadow` | `light.use_shadow` | 03 |
| `light.shadow_buffer_bias`, `falloff_type` | удалены (у AREA есть `shadow_filter_radius`, `shadow_maximum_resolution`, `use_shadow_jitter`) | 03 |
| `world.light_settings.use_ambient_occlusion` | удалён (остались `ao_factor`, `distance`) | 03 |
| `eevee.taa_render_samples` | без изменений | 13 |

Свойства `SceneEEVEE` 5.2.2 (53): `bokeh_*`, `clamp_surface_direct/indirect`, `clamp_volume_*`, `fast_gi_bias`,
`fast_gi_distance`, `fast_gi_method`, `fast_gi_quality`, `fast_gi_ray_count`, `fast_gi_resolution`,
`fast_gi_step_count`, `fast_gi_thickness_near`, `gi_cubemap_resolution`, `gi_diffuse_bounces`, `gi_glossy_clamp`,
`gi_irradiance_pool_size`, `gi_visibility_resolution`, `light_threshold`, `motion_blur_depth_scale`,
`motion_blur_max`, `motion_blur_steps`, `overscan_size`, `ray_tracing_method`, `ray_tracing_options`,
`shadow_pool_size`, `shadow_ray_count`, `shadow_resolution_scale`, `shadow_step_count`, `taa_render_samples`,
`taa_samples`, `use_bokeh_jittered`, `use_fast_gi`, `use_overscan`, `use_raytracing`, `use_shadow_jitter_viewport`,
`use_shadows`, `use_taa_reprojection`, `use_volume_custom_range`, `use_volumetric_shadows`, `volumetric_*`
(`bpy_probe.py type SceneEEVEE --own`) [проверено: 42-doc-snippets; S16: в 5.2 удалён `fast_gi_thickness_far`].

```python
# Blender 5.2.2 — [проверено] настройки EEVEE 5.2 вместо удалённых legacy-свойств
import bpy
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
e = scene.eevee
e.taa_render_samples = 64
e.use_raytracing = True; e.ray_tracing_method = "SCREEN"          # вместо use_ssr
e.use_shadows = True; e.shadow_ray_count = 2; e.shadow_resolution_scale = 1.0   # вместо soft shadows
e.use_fast_gi = True
bpy.context.view_layer.eevee.ambient_occlusion_distance = 0.5      # вместо gtao_distance
scene.render.use_motion_blur = False                               # вместо eevee.use_motion_blur
mat = bpy.data.materials.new("Glass")
mat.surface_render_method = "BLENDED"                              # вместо blend_method = 'BLEND'
mat.use_transparent_shadow = True                                  # вместо shadow_method
for gone in ("use_bloom", "use_gtao", "use_ssr", "use_soft_shadows", "use_motion_blur"):
    assert gone not in bpy.types.SceneEEVEE.bl_rna.properties, gone
```

### 5.4 Композитор 5.0

`scene.use_nodes = True; scene.node_tree` → `AttributeError: 'Scene' object has no attribute 'node_tree'`; дерево —
отдельный ID `CompositorNodeTree`, назначается `scene.compositing_node_group`; выход — `NodeGroupOutput` с сокетом
интерфейса «Image» (Color); `CompositorNodeComposite` → `RuntimeError: … undefined`; многие нода-свойства → входы-меню
(«Most nodes now expose their menu options as inputs»); Gamma → `ShaderNodeGamma`; проходы `DiffCol` → `Diffuse
Color`, `Z` → `Depth` [S27, S34; проверено: 03, 13]. Рабочий код — `02-nodes-from-python.md §6`.

### 5.5 Анимация: слоты (4.4) и удаление legacy API (5.0)

Модель 4.4+: Action → слоты (`action.slots`, по одному на анимируемый ID) → слои (`action.layers`; пока один) →
полосы (`layer.strips`; один бесконечный keyframe-strip) → `strip.channelbag(slot)` → `fcurves`, `groups`.
`AnimData` хранит `action` и `action_slot`. `keyframe_insert` по-прежнему создаёт всю цепочку сам [S25, S33].
В 5.0 удалены прокси `action.fcurves`, `action.groups`, `action.id_root` [S27].

```python
# Blender 5.2.2 — [проверено] ключи, F-кривые через channelbag, действие вручную
import bpy
from bpy_extras import anim_utils
ob = bpy.data.objects["Cube"]
ob.location = (0, 0, 0); ob.keyframe_insert("location", frame=1)          # всё после data_path — только keyword
ob.location = (0, 0, 2); ob.keyframe_insert("location", index=2, frame=24)
ad = ob.animation_data
cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)  # было: ad.action.fcurves
for fc in cb.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"
assert ad.action_slot.identifier == "OBCube" and len(cb.fcurves) == 3
# действие вручную (пример официального quickstart 5.2) и назначение другому объекту
act = bpy.data.actions.new("Bounce")
slot = act.slots.new(id_type="OBJECT", name="Light")
strip = act.layers.new("Layer").strips.new(type="KEYFRAME")
fc = strip.channelbag(slot, ensure=True).fcurves.new("location", index=2, group_name="Object Transform")
fc.keyframe_points.add(2)
fc.keyframe_points[0].co = (1, 0.0); fc.keyframe_points[1].co = (24, 1.0)
light = bpy.data.objects["Light"]
lad = light.animation_data_create()
lad.action = act
if lad.action_slot is None:                   # 4.4+: слот назначается не всегда
    lad.action_slot = lad.action_suitable_slots[0]
bpy.context.scene.frame_set(24)
assert abs(light.location.z - 1.0) < 1e-4 and act.slots[0].target_id_type == "OBJECT"
```

Проверено дополнительно [03]: `action.fcurves` → `AttributeError: 'Action' object has no attribute 'fcurves'`;
`action.fcurves.new(..., action_group=...)` → `channelbag.fcurves.new(..., group_name=...)` (или
`anim_utils.action_ensure_channelbag_for_slot(action, slot)`); `action.id_root = "OBJECT"` → AttributeError, тип —
`slot.target_id_type`; присвоение чужого действия без слота оставляет `action_slot = None` (объект не анимирован);
`keyframe_insert("location", -1, 10)` → `TypeError: bpy_struct.keyframe_insert()() takes at most 1 positional argument
(3 given)`; `options={'INSERTKEY_XYZ_TO_RGB'}` удалён (5.0); `Armature.layers` → bone collections
(`arm.collections.new(...)`); `Bone.select` удалён (5.0) → `pose_bone.select`. Анимация для веба (NLA, экспорт
клипов, shape keys) — агент H (волна 2).

### 5.6 Входы модификатора geometry nodes (5.2)

`mod["Socket_2"] = 5.0` → `TypeError: bpy_struct[key] = val: id properties not supported for this type`; новый
доступ — `mod.properties.inputs.Socket_2.value`, `.type = 'ATTRIBUTE'`, `.attribute_name`, выходные атрибуты —
`mod.properties.outputs.<id>.attribute_name`; после присвоения — `ob.update_tag()` [S29; проверено: 02, 12].
Идентификаторы 3.x (`Input_2`) заменены в 4.0 на `Socket_N`, но ассеты, созданные до 4.0, сохраняют `Input_N`
(«Smooth by Angle»: `Input_0`, `Input_1`, `Socket_1`) [проверено: 06]. Подробно и с кодом — `02-nodes-from-python.md §5.2`.

### 5.7 Интерфейс групп нод (4.0)

`group.inputs.new("NodeSocketFloat", "Size")` → `AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'`;
новое — `group.interface.new_socket(name="Size", in_out='INPUT', socket_type='NodeSocketFloat')`; только базовые типы
(`NodeSocketFloatFactor` → TypeError); панели `new_panel(name, description, default_closed)` (параметр `parent`
удалён в 4.2); `move(item, to_position)`; поиск по identifier `items_tree["Socket_1"]` (5.0) [S21, S23; проверено: 03, 11, 42].

### 5.8 Ввод-вывод и операторы

`import_scene.obj`/`export_scene.obj` → `AttributeError: Calling operator "bpy.ops.import_scene.obj" error, could not
be found` → `wm.obj_import`/`wm.obj_export`; `import_mesh.stl` → `wm.stl_import`/`wm.stl_export`;
`import_mesh.ply` → `wm.ply_import`/`wm.ply_export`; `primitive_cube_add(radius=)` (2.7x) → `size=`;
`view_align=False` → `align='WORLD'`; `object.load_reference_image` → `object.empty_image_add`; glTF:
`export_selected` → `use_selection`, `export_colors` → `export_vertex_color` ('MATERIAL'/'ACTIVE'/'NAME'/'NONE'),
`export_format='GLTF_EMBEDDED'` доступен только при включённой в настройках аддона опции `allow_embedded_format`
[проверено: 03]. 110 параметров экспортёра glTF 5.2.40 и их смысл — агент E (`../08-export-gltf/`,
`99-raw/experiments/E/01-export-params/params.json`).

### 5.9 Python 3.13 и модули Blender

Blender 5.1 перешёл на Python 3.13 (4.1 — 3.11) [S22, S28]. В 3.12–3.13 удалены модули `imp`, `cgi`, `crypt`,
`telnetlib`, `asyncore`, `asynchat`, `smtpd`, `imghdr`, `pipes`, `lib2to3`, `audioop`, `nntplib` — в Blender 5.2.2
`import` каждого даёт `ModuleNotFoundError`; `distutils` импортируется (шим setuptools) [проверено: 42-doc-snippets].
Приватными в 5.0 стали модули Blender `rna_info`, `keyingsets_utils`, `bl_ui_utils`, `bl_rna_utils` и др. (`import
rna_info` → ModuleNotFoundError) [S27; проверено: 42]. `bgl` удалён (5.0) → модуль `gpu`; в фоне GPU-функции требуют
`gpu.init()` (5.2) [S27, S29; проверено: 00-bpy-probe: «GPU functions for drawing requires the gpu module to be
initialized»].

```python
# Blender 5.2.2 — [проверено] модули, которых больше нет, и замены
import importlib
gone = []
for name in ("imp", "cgi", "crypt", "telnetlib", "asyncore", "imghdr", "pipes", "lib2to3", "audioop", "bgl", "rna_info"):
    try:
        importlib.import_module(name)
    except ModuleNotFoundError:
        gone.append(name)
assert gone == ["imp", "cgi", "crypt", "telnetlib", "asyncore", "imghdr", "pipes", "lib2to3", "audioop", "bgl", "rna_info"]
import mimetypes, shlex, gpu                       # замены: imghdr → mimetypes/заголовок файла, pipes → shlex, bgl → gpu
importlib.reload(mimetypes)                        # imp.reload → importlib.reload
```

### 5.10 Прочее, что встречается в коде нейросетей

`bpy.app.version_char` удалён (4.0) → `version_string`; `scene["cycles"]["samples"]` → `KeyError` (5.0) →
`scene.cycles.samples`; `bpy.data.grease_pencils_v3` → `bpy.data.grease_pencils` (GP v3), старые аннотации —
`bpy.data.annotations` (5.0); `scene.sequence_editor.sequences` → `.strips` (4.4/5.0), `new_effect(..., frame_end=)`
→ `length=`; `Boolean solver 'FAST'` → `'FLOAT'` (или 'EXACT', 'MANIFOLD'); LightProbe `'CUBEMAP'` → `'SPHERE'`;
`image_settings.file_format = 'FFMPEG'` → сначала `media_type = 'VIDEO'`; mathutils → numpy даёт float32 (5.0);
`bpy.utils.register_module` (2.7x) → `register_class` [проверено: 03].

## 6. Официальные примеры и ответы, которые устарели

| Источник | Код | 5.2.2 |
|---|---|---|
| Release notes 4.0, раздел Node Groups | `tree.interface.move(socket, to_index=2)` | TypeError: нужен `to_position` [проверено: 42] |
| Руководство 4.4 «Slotted Actions: Upgrading», «What did not change» | `pose.bones[…].keyframe_insert("rotation_euler", 1)` | TypeError: позиционный index запрещён [проверено: 19] |
| Release notes 4.2 (Python API) | `scene.eevee.use_motion_blur -> scene.render.user_motion_blur` | опечатка в заметке: свойство `render.use_motion_blur` [проверено: 03] |
| Release notes 5.0 | «sun_direction, turbidity, ground_albedo … removed» у Sky Texture | в RNA 5.2.2 эти свойства есть и присваиваются [проверено: 03] |
| SE 247520 (2021, принятый) | `for input in modifier.node_group.inputs` | AttributeError [проверено: 19] |
| SE 253001 (2022) | `modifiers["GeometryNodes"]["Input_6"] = obj` | TypeError [проверено: 19] |
| SE 316696 (2024, принятый) | `modifier_add_node_group(ESSENTIALS, "geometry_nodes\\smooth_by_angle.blend\\…")` + `modifier["Input_1"]` | CANCELLED + TypeError [проверено: 19] |

## Частые ошибки

- Копировать код из ответа или туториала без версии: из 95 проверенных «старых» фрагментов в 5.2.2 работают 8
  (с оговорками); даже официальные примеры 4.0/4.4 местами не работают (§6).
- Ловить `AttributeError` широко (`except Exception: pass`) — ошибка дрейфа прячется, объект молча не получает
  нужный вид. Ловить узко (`TypeError` при присвоении enum, `KeyError` при сокете) и печатать.
- Проверять версию `if bpy.app.version >= (4, 0)` и считать, что 4.x ≈ 5.x: между 4.5 и 5.0 удалены `Action.fcurves`,
  `scene.node_tree`, `BLENDER_EEVEE_NEXT`, а между 5.1 и 5.2 — IDProperty-входы GN.
- Писать `hasattr(bpy.types.X, "prop")` для выбора ветки — всегда False.
- Устанавливать `material.use_nodes = True` «на всякий случай» — в 5.x это DeprecationWarning и шум в журнале.
- Путать «EEVEE» из статей 2020–2023 (Legacy) с EEVEE Next 4.2+: другие свойства, другой свет, bloom — только в
  композиторе.

## Чек-лист

- [ ] Каждый «кусок по памяти» прогнан в 5.2.2 или сверен с таблицей §4?
- [ ] В коде нет `use_auto_smooth`, `calc_normals`, `Action.fcurves`, `scene.node_tree`, `BLENDER_EEVEE_NEXT`,
  `use_bloom`, `mod["Socket_…"]`, `tree.inputs.new`, `export_selected`?
- [ ] Имена входов Principled — из списка 5.2 (32 входа)?
- [ ] Ветвления по версии — через `bpy.app.version` и `bl_rna.properties`, а не `hasattr` на классе?
- [ ] `material/world.use_nodes` не используются?
- [ ] Анимационный код работает через слот и channelbag?
- [ ] Композитор — через `compositing_node_group` и Group Output?
- [ ] Для новых API (GN-модификатор, меню-входы) после присвоения — `ob.update_tag()`, значения меню — отображаемые?

## Открытые вопросы и противоречия

- Поле `deprecated_version` у ряда свойств — `[5, 10, 0]`: похоже на запись «510» вместо «501» (5.1) в исходнике RNA;
  заметки 5.1 подтверждают, что переименования VSE сделаны в 5.1.
- Заметка 5.0 о Sky Texture противоречит RNA 5.2.2 (§6); в какой версии свойства фактически исчезнут — не выяснено.
- Изменения `Compare`/`Random Value` в 5.2 описаны одной строкой («Socket identifiers … changed»); в 5.2.2 эти ноды
  имеют по одному динамическому сокету — старые индексы и identifiers недействительны; полный список затронутых нод не
  опубликован.
- Строки «было» для 2.7x–2.8x (scene.objects.link, obj.select, `*` для матриц) формально вне диапазона 3.6→5.2, но
  нейросети пишут их регулярно — оставлены в таблице.
- Ветки bpyx для 4.x (IDProperty-входы GN, `BLENDER_EEVEE_NEXT`) не проверены: на машине только 5.2.2.

## Источники

- [S16] Blender Foundation. Change Log 5.1 → 5.2. Python API 5.2 — https://docs.blender.org/api/5.2/change_log.html — перечень добавленного/удалённого между 5.1 и 5.2; первичный.
- [S20] Blender Foundation. Blender 3.6 LTS: Python API & Text Editor — https://developer.blender.org/docs/release_notes/3.6/python_api/ — формат меша на атрибутах; первичный.
- [S21] Blender Foundation. Blender 4.0: Python API — https://developer.blender.org/docs/release_notes/4.0/python_api/ — Principled v2, interface, override, calc_normals; первичный.
- [S22] Blender Foundation. Blender 4.1: Python API — https://developer.blender.org/docs/release_notes/4.1/python_api/ — auto smooth, corner_normals, Python 3.11; первичный.
- [S23] Blender Foundation. Blender 4.2 LTS: Python API — https://developer.blender.org/docs/release_notes/4.2/python_api/ — EEVEE Next id, bloom, IDProperties; первичный (одна опечатка, §6).
- [S24] Blender Foundation. Blender 4.3: Python API — https://developer.blender.org/docs/release_notes/4.3/python_api/ — удаление legacy EEVEE, rename; первичный.
- [S25] Blender Foundation. Blender 4.4: Python API — https://developer.blender.org/docs/release_notes/4.4/python_api/ — слотовые действия, Strip; первичный.
- [S26] Blender Foundation. Blender 4.5 LTS: Python API — https://developer.blender.org/docs/release_notes/4.5/python_api/ — GeometrySet, Bump distance; первичный.
- [S27] Blender Foundation. Blender 5.0: Python API — https://developer.blender.org/docs/release_notes/5.0/python_api/ — удаление Action.fcurves, node_tree, bgl, EEVEE id; первичный.
- [S28] Blender Foundation. Blender 5.1: Python API — https://developer.blender.org/docs/release_notes/5.1/python_api/ — Python 3.13, VSE; первичный.
- [S29] Blender Foundation. Blender 5.2 LTS: Python API — https://developer.blender.org/docs/release_notes/5.2/python_api/ — входы GN, gpu.init, all_ids; первичный.
- [S30] Blender Foundation. Blender 4.1: Modeling — https://developer.blender.org/docs/release_notes/4.1/modeling/ — Auto Smooth → ассет; первичный.
- [S31] Blender Foundation. EEVEE migration to 4.2 LTS — https://developer.blender.org/docs/release_notes/4.2/eevee_migration/ — Blend Mode, Shadow Mode, Bloom → Glare; первичный.
- [S32] Blender Foundation. Blender 4.2 LTS: EEVEE — https://developer.blender.org/docs/release_notes/4.2/eevee/ — новый EEVEE; первичный.
- [S33] Blender Foundation. Slotted Actions: Upgrading to 4.4 — https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/ — перенос кода анимации; первичный (пример с позиционным index устарел).
- [S34] Blender Foundation. Blender 5.0: Compositor — https://developer.blender.org/docs/release_notes/5.0/compositor/ — Composite → Group Output; первичный.
- [S35] Blender Foundation. Blender 5.2 LTS: Geometry Nodes — https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/ — новые ноды; первичный.
- [S9] Blender Foundation. Quickstart (раздел Animation). API 5.2 — https://docs.blender.org/api/5.2/info_quickstart.html — пример слотового действия; первичный.
- [S15] Blender Foundation. bpy_struct.keyframe_insert. API 5.2 — https://docs.blender.org/api/5.2/bpy.types.bpy_struct.html — keyword-only параметры; первичный.
- [S19] Blender Foundation. Action. API 5.2 — https://docs.blender.org/api/5.2/bpy.types.Action.html — slots, layers, fcurve_ensure_for_datablock; первичный.
- [S40]–[S43] Blender Stack Exchange: вопросы 247520, 253001, 306355, 316696 (ответы 2021–2024), полученные через https://api.stackexchange.com (2026-09-23) — типичный «код по памяти»; проверены экспериментом 19.
