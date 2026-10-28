# Ошибки нейросетей в bpy-коде и устойчивые паттерны (Blender 5.2)

Волна 1 · агент B · 2026-09-23 · эмпирика: 41 фрагмент «как пишет нейросеть по памяти» (эксперимент 17), 95 пар
дрейфа версий (03), 7 фрагментов из ответов Stack Exchange 2021–2024 и руководства 4.4 + 4 исправления (19), 56 вызовов операторов
в фоне (04), 4 собственные ошибки при написании bpyx, экспериментов и этого файла · источников в файле 16 · Blender 5.2.2 LTS.
Блоки `python` с меткой `[проверено]` выполнены автоматически в чистой сцене.

## Выжимка для агента

1. **Треть ошибок тихие**: из 41 фрагмента по памяти 27 падают с исключением, а 14 выполняются и дают неверный
   результат (цвет 0–255, градусы, индекс сокета, устаревший `context.object`, объект без коллекции, CANCELLED
   оператора, данные EDIT, bmesh без `to_mesh`, невалидная связь, нет Material Output, файл в cwd, `hasattr` на классе).
   Отсутствие исключения ничего не доказывает — нужна проверка результата. → §3 [проверено: 17]
2. **Каждый скрипт заканчивай проверкой**: число объектов и треугольников, габариты, `assert`, для рендера — файл
   существует и не пустой; печатай одну строку JSON с отчётом. → §4.5 [проверено: 41-bpyx-example]
3. **Не выдумывай параметры**: у `primitive_cube_add` нет `name`, у `render.render` — `filepath`, у `materials.new` —
   `use_nodes`, у света — `power` (есть `energy`), у камеры — `focal_length` (есть `lens`). Сомнение → `bpy_probe.py
   op/type/search`. → §2.1 [проверено: 17]
4. **Сообщение об ошибке Blender — подсказка**: `TypeError: … enum "X" not found in (…)` содержит список допустимых;
   `invalid keyword argument(s) (…), expected (…)` — список параметров; `did_you_mean` у bpy_probe. Читай его, а не
   угадывай снова. → §4.7 [проверено: 03, 17]
5. **Старый код ловится текстом ошибки** (`key "Specular" not found`, `no attribute 'use_auto_smooth'`,
   `BLENDER_EEVEE_NEXT not found`, `no attribute 'fcurves'`, `id properties not supported`) → строка таблицы в
   `03-version-drift-3.6-to-5.2.md §4`. → §2.2 [проверено: 03]
6. **Контекст и режимы**: `mode_set` без активного объекта → RuntimeError; `context.object` после data API — старый
   объект; `uv.*` и `mesh.*` — только в EDIT; данные EDIT видны в `ob.data` только после выхода. → §2.3 [проверено: 04, 17]
7. **Результат оператора проверяй `== {'FINISHED'}`**: `modifier_apply` с неверным именем, `transform_apply` без
   выделения, `join` с одним объектом или с override только `selected_objects`, `modifier_add_node_group` в фоне —
   CANCELLED без исключения. → §2.4, §2.13 [проверено: 04, 19]
8. **Объект без `collection.objects.link` не существует для сцены** (рендер, экспорт, активность, сохранение). → §2.5 [проверено: 05, 17]
9. **bmesh: `to_mesh` + `free`, `ensure_lookup_table()` после изменений, UV-слой до `create_*`.** → §2.6 [проверено: 06, 17]
10. **Значения: RGBA из 4 чисел в линейном пространстве, углы в радианах, векторы из 3 чисел, int для целых
    свойств, перечисления с точным регистром.** → §2.7 [проверено: 17]
11. **Ноды: по type/bl_idname, режим до сокета, сокет по имени среди доступных, `link.is_valid`, всегда Material
    Output.** → §2.8 [проверено: 01, 11, 15, 17]
12. **Висячие ссылки**: после `remove`, `mode_set`, `*.add()` перечитывай данные; старая ссылка — ReferenceError,
    мусор (`UnicodeDecodeError`) или краш. → §2.9 [проверено: 05, 40-bpyx-tests]
13. **Пути — абсолютные**; `//` — только при сохранённом `.blend`. → §2.10 [проверено: 17]
14. **MCP: состояние — в сцене, не в переменных**; в каждом вызове заново находи свои объекты (по тегу в custom
    property или своему имени); `if __name__ == "__main__"` в MCP не выполнится. → §2.11, §4.3 [проверено: 16]
15. **Проверка «есть ли» — `bl_rna.properties`, значения перечислений — по фактическому списку.** → §2.12 [проверено: 00, 03]
16. **Идемпотентность**: скрипт удаляет только своё (по тегу/коллекции) и собирает заново по словарю параметров;
    повторный запуск даёт тот же результат. → §4.1 [проверено: 42-doc-snippets]
17. **Операторы — через обёртку**: `poll()` → `temp_override` → вызов → проверка результата → понятная ошибка. → §4.2 [проверено: 42-doc-snippets]
18. **Исправляя ошибку, меняй одну вещь и перезапускай**; не оборачивай в `try: … except Exception: pass` — это
    превращает громкую ошибку в тихую. → §4.7 [практика; проверено на собственных ошибках §5]

## 1. Как собиралась эмпирика

- **41 фрагмент** (эксперимент 17): код в стиле туториалов и ответов 2019–2023 годов на типовые задачи агента —
  материалы, модификаторы, текст, свет, камера, рендер, экспорт, выделение, режимы, bmesh, ноды, пути. Каждый
  выполнялся в сцене по умолчанию (Cube/Light/Camera — как у пользователя), тихие ошибки ловились `assert` на то, что
  «хотел получить» код. Для каждого написано и проверено исправление (41/41 OK)
  [проверено].
- **95 пар дрейфа** (эксперимент 03): «было» 87 ERR, 2 WARN, 6 OK; «стало» 95/95 OK — `03-version-drift-3.6-to-5.2.md`.
- **7 фрагментов из источников с высоким доверием** (эксперимент 19): ответы Blender Stack Exchange 2021–2024
  (получены через API stackexchange.com, в том числе принятые) и официальное руководство 4.4 — 5 из 7 не работают в
  5.2.2; из 4 исправленных вариантов 3 работают, четвёртый (оператор ассета в фоне) отменяется — нужен data API.
- **56 операторов в фоне** (эксперимент 04): 42 FINISHED, 9 — poll failed, 5 — тихий CANCELLED.
- **Собственные ошибки при работе** (§5): даже при знании правил четыре ошибки попали в код — доказательство, что
  правила нужно применять механически (проверкой), а не «помнить».

Каталог дополняет общий каталог ошибок агента в 3D (геометрия, эстетика, экспорт, процесс) у агента C1 —
`../04-ai-agents-mcp/05-failure-modes-catalog.md` (класс «код и API»); здесь — только ошибки Python API.

## 2. Каталог

Формат: **код** · что пишет нейросеть · симптом в 5.2.2 (дословно) · причина · исправление · правило. «Тихо» — без
исключения. Ссылки — на эксперименты `99-raw/experiments/B/`.

### 2.1 B1 — выдуманные API и параметры

| Код | Что пишет | Симптом 5.2.2 | Причина | Исправление |
|---|---|---|---|---|
| B1.1 | `bpy.ops.mesh.primitive_cube_add(size=2, name="Box")` | `TypeError: Converting py args to operator properties:: keyword "name" unrecognized` | у операторов нет «name»; параметры — свойства оператора | создать, затем `bpy.context.object.name = "Box"` |
| B1.2 | `nodes.new("Principled BSDF")` | `RuntimeError: Error: Node type Principled BSDF undefined` | ожидается bl_idname, не подпись | `nodes.new("ShaderNodeBsdfPrincipled")` |
| B1.3 | `bpy.data.materials.new("M", use_nodes=True)` | `TypeError: BlendDataMaterials.new(): takes at most 1 arguments, got 2` | параметров у `new` нет; 5.x — дерево создаётся само | `bpy.data.materials.new("M")` |
| B1.4 | `light.data.power = 1000` | `AttributeError: 'AreaLight' object has no attribute 'power'` | свойство — `energy` (Вт) | `light.data.energy = 1000` |
| B1.5 | `cam.data.focal_length = 85` | `AttributeError: 'Camera' object has no attribute 'focal_length'` | свойство — `lens` (мм) | `cam.data.lens = 85` |
| B1.6 | `bpy.ops.render.render(filepath=…, write_still=True)` | `TypeError: … keyword "filepath" unrecognized` | путь — в `scene.render.filepath` | задать `render.filepath`, затем `render.render(write_still=True)` |
| B1.7 | `bpy.data.objects.new("Box", "MESH")` | `TypeError: BlendDataObjects.new(): error with argument 2, "object_data" - Function.object_data expected a ID type, not str` | второй аргумент — ID данных или None | `objects.new("Box", bpy.data.meshes.new("Box"))` |
| B1.8 | `ob.material = mat` / `ob.set_material(mat)` | `AttributeError: 'Object' object has no attribute 'material'` | материалы — в слотах данных | `ob.data.materials.append(mat)` или `[0] = mat` |
| B1.9 | `bpy.data.images.new("T", 64, 64, generated_type="COLOR_GRID")` | `TypeError: BlendDataImages.new(): was called with invalid keyword argument(s) (generated_type), expected (name, width, height, alpha, float_buffer, stereo3d, is_data, tiled)` | `generated_type` — свойство картинки | `img = images.new(...); img.generated_type = "COLOR_GRID"` |
| B1.10 | `mirror.use_x = True`; `bevel.use_only_vertices = True` | `AttributeError: 'MirrorModifier' object has no attribute 'use_x'` | 2.7x/2.8x | `mirror.use_axis[0] = True`; `bevel.affect = 'VERTICES'` |
| B1.11 | `bmesh.ops.bevel(..., vertex_only=True)` | `TypeError: bevel: keyword "vertex_only" is invalid for this operator` | 2.8x | `affect='VERTICES'` |

[проверено: 06, 10, 14, 17]. Правило: **свойство или параметр, в котором нет уверенности, — через `bpy_probe.py
type X.prop` / `op cat.name` / `search слово` до написания кода**; при ошибке — читать список из сообщения.

### 2.2 B2 — устаревшие имена (дрейф версий)

Полная таблица на 105 строк — `03-version-drift-3.6-to-5.2.md §4`. Самые частые в коде нейросетей (все проверены в
5.2.2 [03, 19]):

| Код | Было | Симптом | Стало |
|---|---|---|---|
| B2.1 | `p.inputs["Specular"]`, `["Transmission"]`, `["Clearcoat"]`, `["Emission"]` | `KeyError: 'bpy_prop_collection[key]: key "Specular" not found'` | «Specular IOR Level», «Transmission Weight», «Coat Weight», «Emission Color» |
| B2.2 | `me.use_auto_smooth = True` | `AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'` | `me.shade_smooth(); me.set_sharp_from_angle(angle=…)` |
| B2.3 | `scene.render.engine = 'BLENDER_EEVEE_NEXT'` | `TypeError: … enum "BLENDER_EEVEE_NEXT" not found in ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES')` | `'BLENDER_EEVEE'` |
| B2.4 | `scene.eevee.use_bloom = True` | `AttributeError: 'SceneEEVEE' object has no attribute 'use_bloom'` | Glare (Bloom) в композиторе |
| B2.5 | `scene.use_nodes = True; scene.node_tree` | `AttributeError: 'Scene' object has no attribute 'node_tree'` | `scene.compositing_node_group = …` |
| B2.6 | `action.fcurves` | `AttributeError: 'Action' object has no attribute 'fcurves'` | `anim_utils.action_get_channelbag_for_slot(action, slot).fcurves` |
| B2.7 | `mod["Socket_2"] = 5` | `TypeError: bpy_struct[key] = val: id properties not supported for this type` | `mod.properties.inputs.Socket_2.value = 5; ob.update_tag()` |
| B2.8 | `tree.inputs.new("NodeSocketFloat", "Size")` | `AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'` | `tree.interface.new_socket(name="Size", in_out='INPUT', socket_type='NodeSocketFloat')` |
| B2.9 | `bpy.ops.object.delete(override)` | `ValueError: 1-2 args execution context is supported` | `with bpy.context.temp_override(...)` |
| B2.10 | `me.calc_normals()` | `AttributeError: 'Mesh' object has no attribute 'calc_normals'` | не нужно; `me.corner_normals` |
| B2.11 | `bpy.ops.import_scene.obj(...)` | `AttributeError: Calling operator "bpy.ops.import_scene.obj" error, could not be found` | `bpy.ops.wm.obj_import(...)` |
| B2.12 | `export_scene.gltf(..., export_selected=True)` | `TypeError: … keyword "export_selected" unrecognized` | `use_selection=True` |
| B2.13 | `ob.keyframe_insert("location", -1, 10)` | `TypeError: bpy_struct.keyframe_insert()() takes at most 1 positional argument (3 given)` | `keyframe_insert("location", index=-1, frame=10)` |

Правило: **встретил один из этих текстов — не чинить наугад, а взять строку «стало»**; в начале скрипта для 5.2 не
использовать эти имена вовсе.

### 2.3 B3 — контекст и режимы

| Код | Что пишет | Симптом | Причина | Исправление |
|---|---|---|---|---|
| B3.1 | `bpy.ops.object.mode_set(mode="EDIT")` в пустой сцене / после удаления | `RuntimeError: Operator bpy.ops.object.mode_set.poll() Context missing active object` | нет активного объекта | `view_layer.objects.active = ob` (ob в слое вида) |
| B3.2 | `bpy.context.view_layer.objects.active = ob` для объекта вне сцены | `RuntimeError: Error: ViewLayer 'ViewLayer' does not contain object 'Obj'` | объект не привязан | `scene.collection.objects.link(ob)` |
| B3.3 | создать данными, править `bpy.context.object.location` | тихо: сдвинут старый активный «Cube» | data API не меняет активный | работать по своей ссылке |
| B3.4 | `bpy.context.active_object = ob` | `AttributeError: bpy_struct: Context property "active_object" is read-only` | контекст только для чтения | `view_layer.objects.active = ob` |
| B3.5 | `mesh.subdivide` в EDIT и сразу `len(ob.data.vertices)` | тихо: 8 вершин | edit-данные пишутся при выходе из EDIT | `mode_set(OBJECT)` или `ob.update_from_editmode()` |
| B3.6 | `uv.smart_project()` в OBJECT | `RuntimeError: … uv.smart_project.poll() failed, context is incorrect` | нужен EDIT меша | `mode_set(EDIT)` + `mesh.select_all(action='SELECT')` |
| B3.7 | `uv.project_from_view()`, `view3d.view_all()` в фоне | `RuntimeError: … poll() failed, context is incorrect` / `Expected a view3d region` | нет области | override области VIEW_3D (`01 §4.5`) или `camera_fit_coords`; `uv.smart_project` вместо проекции из вида |
| B3.8 | `node.add_node(...)`, `image.save_as(...)` в фоне/MCP | `RuntimeError: … poll() failed, context is incorrect` | нужны редакторы | `tree.nodes.new(...)`, `img.save()` / `save_render()` |

[проверено: 04, 17]. Правило: **оператору нужны объект в слое вида, активность/выделение, режим и (для view3d)
область — задавай их явно через `temp_override`**.

### 2.4 B4 — выделение, активность, имена

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B4.1 | `bpy.ops.mesh.primitive_cube_add(); ob = bpy.data.objects["Cube"]` | тихо: взят старый «Cube», новый — «Cube.001» | `ob = bpy.context.object` сразу после оператора |
| B4.2 | `bpy.ops.object.transform_apply(scale=True)` для невыделенного объекта | тихо: `{'CANCELLED'}`, scale (2, 2, 2) | выделить или применить данными (`01 §9.2`) |
| B4.3 | `bpy.ops.object.modifier_apply(modifier="Subdivision")` при имени «Subsurf» | тихо: `{'CANCELLED'}` | `modifier=m.name` по ссылке на созданный модификатор |
| B4.4 | `temp_override(active_object=a, selected_objects=[a, b])` + `object.join()` | тихо: `{'CANCELLED'}` | переопределить `selected_editable_objects` (узнать — `logging_set(True)`) |
| B4.5 | `nodes["Principled BSDF"]`, `objects["Cube"]` в русском интерфейсе | `KeyError` («Принципиальный BSDF», «Куб») | по type/bl_idname; своё имя, заданное явно |

[проверено: 04, 15, 17, 19].

### 2.5 B5 — коллекции и видимость

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B5.1 | `ob = bpy.data.objects.new(...)` без `link` | тихо: нет в сцене, рендере, экспорте; не сохраняется | `scene.collection.objects.link(ob)` |
| B5.2 | `bpy.data.collections.new("Props")` без привязки к сцене | тихо: объекты коллекции невидимы | `scene.collection.children.link(coll)` |
| B5.3 | `layer_collection.exclude = True` и сразу проверка `view_layer.objects` | тихо: объект ещё «в слое» | `view_layer.update()` |
| B5.4 | `ob.hide_set(True)` для скрытия в рендере | тихо: в рендере виден | `ob.hide_render = True` |

[проверено: 05, 17].

### 2.6 B6 — bmesh

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B6.1 | правка `bm` и `bm.free()` без `bm.to_mesh(me)` | тихо: изменений нет | `bm.to_mesh(me); bm.free(); me.update()` |
| B6.2 | `len(bm.verts)` после `bm.free()` | `ReferenceError: BMesh data of type BMesh has been removed` | читать до `free` |
| B6.3 | `bm.verts[10]` после `subdivide_edges` | `IndexError: BMElemSeq[index]: outdated internal index table, run ensure_lookup_table() first` | `bm.verts.ensure_lookup_table()` |
| B6.4 | `bmesh.ops.create_cube(bm, size=2, calc_uvs=True)` без UV-слоя | тихо: UV нет | `bm.loops.layers.uv.new("UVMap")` до `create_*` |
| B6.5 | `bmesh.from_edit_mesh(me)` без `bmesh.update_edit_mesh(me)` | тихо: вьюпорт/меш не обновлены | `update_edit_mesh(me)` и выход из EDIT |

[проверено: 01-файл §4.6, 06, 17].

### 2.7 B7 — значения и единицы

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B7.1 | `inputs["Base Color"].default_value = (1, 0, 0)` | `ValueError: … sequences of dimension 0 should contain 4 items, not 3` | `(1, 0, 0, 1)` |
| B7.2 | `= (255, 128, 0, 1)` | тихо: пересвет (значения > 1 приняты) | `/255` и sRGB → linear |
| B7.3 | `ob.rotation_euler = (90, 0, 0)` | тихо: 90 радиан | `math.radians(90)` |
| B7.4 | `ob.scale = 2` | `TypeError: bpy_struct: item.attr = val: …` | `(2, 2, 2)` |
| B7.5 | `ob.location = (0, 0)` | `ValueError: … should contain 3 items, not 2` | `(0, 0, 0)` |
| B7.6 | `subsurf.levels = 2.0` | `TypeError: … SubsurfModifier.levels expected an int type, not float` | `2` |
| B7.7 | `file_format = "png"`, `engine = "Cycles"` | `TypeError: … enum "png" not found in ('AVIF', 'JPEG', 'OPEN_EXR', 'PNG', …)` | `"PNG"`, `"CYCLES"` |
| B7.8 | `colorspace_settings.name = "Linear"` | `TypeError: … enum "Linear" not found in ('ACES 1.3 sRGB', …)` | `"Linear Rec.709"`, данные — `"Non-Color"` |
| B7.9 | `sun.data.energy = 1000` (как у area) | тихо: пересвет (у SUN — Вт/м², 1–10 — дневной свет) | SUN 1–10, AREA/POINT — Вт [мнение: калибровка — агент D2] |

[проверено: 17; B7.9 — не проверено замером].

### 2.8 B8 — ноды

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B8.1 | `p.inputs[7].default_value = 0.2` (Roughness по раскладке 3.x) | тихо: записано в «Weight» | по имени `p.inputs["Roughness"]` |
| B8.2 | `mix.inputs["A"]` до `mix.data_type = "RGBA"` | тихо: связь `is_valid = False` | режим до поиска сокета |
| B8.3 | `mix.inputs["A_Color"]` | `KeyError` (поиск по identifier для Mix/Map Range запрещён) | `mix.inputs["A"]` после режима или перебор по identifier |
| B8.4 | `links.new(emission.outputs["Emission"], p.inputs["Base Color"])` | тихо: `is_valid = False` | Emission Color + Strength у Principled |
| B8.5 | `nodes.clear()` и забыли Material Output | тихо: материал без вывода | `ShaderNodeOutputMaterial` + связь Surface |
| B8.6 | `me.materials[0] = mat` на пустом меше | `IndexError: bpy_prop_collection[index] = value: index 0 out of range, size 0` | `me.materials.append(mat)` |
| B8.7 | `node.mode = 'COUNT'` (Resample Curve), `glare.glare_type = 'BLOOM'` | `AttributeError` | `inputs["Mode"].default_value = "Count"`, `inputs["Type"] = "Bloom"` |
| B8.8 | `mod.properties.inputs.X.value = v` и сразу чтение результата | тихо: старый результат | `ob.update_tag()` |
| B8.9 | `FunctionNodeInputColor.color = (1, 0, 0)` | тихо: покрашена рамка ноды (Node.color) | `.value = (1, 0, 0, 1)` |
| B8.10 | `color_ramp.elements.remove(...)` до пустого | `RuntimeError: Error: Element not found in element collection or last element` | оставлять ≥ 1 элемент |

[проверено: 01, 03, 11, 12, 17].

### 2.9 B9 — висячие ссылки и память

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B9.1 | `bpy.data.objects.remove(ob)`, затем `ob.name` | `ReferenceError: StructRNA of type Object has been removed` | не трогать после удаления; хранить имена |
| B9.2 | `m = ob.modifiers.new(...)`; `ob.modifiers.remove(m)`; затем `m.bl_rna` | `ReferenceError: StructRNA of type MirrorModifier has been removed` (моя ошибка в bpyx) | прочитать нужное до `remove` |
| B9.3 | `uv = me.uv_layers.new(...)`; `mode_set(EDIT)`…`mode_set(OBJECT)`; `uv.name` | `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa0` — мусор из освобождённой памяти (моя ошибка в bpyx) | запомнить имя строкой, после смены режима — `me.uv_layers[name]` |
| B9.4 | `point = spline.bezier_points[0]; spline.bezier_points.add(); point.co = …` | по документации — краш | добавлять все точки сразу, ссылки брать после |
| B9.5 | `for o in coll.all_objects: o.hide_viewport = True` | по документации — неверная итерация/краш | `for o in coll.all_objects[:]` |

[проверено: 05, 40-bpyx-tests; B9.4–B9.5 — документация S1].

### 2.10 B10 — пути и файлы

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B10.1 | `export_scene.gltf(filepath="model.glb")` | тихо: файл в cwd процесса (у MCP — в каталоге запуска Blender) | `os.path.abspath(...)` |
| B10.2 | `render.filepath = "//out.png"` в несохранённом файле | `RuntimeError: Error: Render error (No such file or directory) cannot save: 'out_rel.png'` | абсолютный путь или сначала `save_as_mainfile` |
| B10.3 | `bpy.data.images.load("textures/wood.png")` | `RuntimeError: Error: Cannot read 'textures/wood.png': No such file or directory` | абсолютный путь, проверка `os.path.exists` |
| B10.4 | `scene.world.node_tree` в пустой сцене | `AttributeError: 'NoneType' object has no attribute 'node_tree'` | создать мир: `scene.world = bpy.data.worlds.new("World")` |
| B10.5 | рендер без камеры | `RuntimeError: Error: Cannot render, no camera` | `scene.camera = cam` |

[проверено: 17].

### 2.11 B11 — состояние между вызовами MCP

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B11.1 | переменная из прошлого вызова | `NameError: name 'x' is not defined` | найти объект заново (тег/имя) |
| B11.2 | `mathutils.Vector(...)` без импорта | `NameError: name 'mathutils' is not defined` | импорт в каждом вызове |
| B11.3 | код под `if __name__ == "__main__":` | тихо: не выполнился (`__name__ == 'builtins'`) | вызывать функцию явно |
| B11.4 | `os.path.dirname(__file__)` | `NameError: name '__file__' is not defined` | абсолютные пути из параметров |
| B11.5 | правка своего модуля и `importlib.reload` в ту же секунду | тихо: старый код (устаревший `.pyc`) | `sys.dont_write_bytecode = True` до импорта |

[проверено: 16].

### 2.12 B12 — интроспекция

| Код | Что пишет | Симптом | Исправление |
|---|---|---|---|
| B12.1 | `hasattr(bpy.types.Material, "use_nodes")` | тихо: False (всегда для RNA на классе) | `"use_nodes" in bpy.types.Material.bl_rna.properties` |
| B12.2 | `[i.identifier for i in r.bl_rna.properties["engine"].enum_items]` | тихо: `['BLENDER_EEVEE']` (занижено) | фактический список — из TypeError (`01 §2.8`), `bpy_probe.py enum` |
| B12.3 | MCP `describe_node_type("ShaderNodeMix")` без `property_overrides` | тихо: 10 входов подряд, без признака доступности | смотреть `s.enabled` или `bpy_probe.py node ShaderNodeMix data_type=RGBA` |
| B12.4 | `hasattr(bpy.ops.mesh, "looptools_relax")` | тихо: True для любого имени | `bpy.ops.mesh.looptools_relax.get_rna_type()` в `try/except KeyError` |
| B12.5 | `hasattr(bpy.types, "MESH_OT_flatten")` | тихо: False у всех C-операторов (True только у Python-операторов) | то же `get_rna_type()` |

[проверено: 00, 03, 17; S38].

### 2.13 B13 — тихий CANCELLED операторов (сводка)

`modifier_apply` (неверное имя), `transform_apply` (нет выделения), `join` (один объект / override не того члена),
`mesh.separate(type='LOOSE')` (связный меш), `view3d.camera_to_view_selected` (нет области, при этом `poll() == True`),
`modifier_add_node_group` (ассет не загружен в фоне) — все возвращают `{'CANCELLED'}` без исключения
[проверено: 04, 19]. Документация: CANCELLED без ERROR-отчёта не бросает исключение [S12].

### 2.14 B14 — потоки

Python-потоки, трогающие bpy, роняют Blender в произвольный момент (документация, `info_gotchas_threading`) [S5].
В экспериментах не запускалось (намеренно). Замены: `bpy.app.timers.register`, отдельные процессы `blender -b`.

## 3. Где опаснее всего

| Класс | Громких (ERR) | Тихих | Комментарий |
|---|---|---|---|
| Выдуманные API и параметры (B1) | 11 | 0 | ловятся сразу, сообщение содержит список допустимого |
| Устаревшие имена (B2) | 87 из 95 | 0 (2 WARN, 6 с оговорками) | ловятся сразу; см. таблицу дрейфа |
| Контекст и режимы (B3) | 6 | 2 | тихие — `context.object` и данные EDIT |
| Выделение, имена (B4) | 1 | 4 | самые коварные: CANCELLED и «не тот объект» |
| Коллекции (B5) | 0 | 4 | объект «пропадает» из рендера и экспорта |
| bmesh (B6) | 2 | 3 | |
| Значения и единицы (B7) | 6 | 3 | |
| Ноды (B8) | 4 | 6 | невалидные связи и индексы — визуально «не тот материал» |
| Пути (B10) | 4 | 1 | |
| Интроспекция (B12) | 0 | 3 | неверная ветка кода |

Счёт — по строкам каталога §2 (для B2 — по таблице дрейфа из 95 пар); источники строк — эксперименты 03, 04, 06, 10, 15, 16, 17, 19. Вывод: **тихие ошибки
концентрируются там, где код «работает с контекстом» (активный объект, выделение, имена) и где значение принимается
без проверки диапазона** — именно там нужны `assert` и отчёт в конце скрипта.

## 4. Паттерны устойчивого кода

### 4.1 Идемпотентная сборка «с нуля по параметрам» с тегами

Состояние между вызовами (MCP, повторные запуски) хранится в сцене: свои объекты помечаются custom property и
собираются в свою коллекцию; каждый запуск удаляет только помеченное и строит заново по словарю параметров.

```python
# Blender 5.2.2 — [проверено] идемпотентная сборка по параметрам с тегом
import math
import bpy, bmesh

TAG = "agent_asset"
PARAMS = {"name": "Stool", "seat_r": 0.35, "seat_h": 0.45, "legs": 3, "leg_r": 0.03}

def clear_tagged(tag_value):
    for ob in [o for o in bpy.data.objects if o.get(TAG) == tag_value]:
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)

def cylinder(name, r, depth, loc, coll, tag_value):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=depth)
    bm.to_mesh(me); bm.free(); me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(30))
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob[TAG] = tag_value
    coll.objects.link(ob)
    return ob

def build(p):
    clear_tagged(p["name"])
    coll = bpy.data.collections.get(p["name"]) or bpy.data.collections.new(p["name"])
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    seat = cylinder("Seat", p["seat_r"], 0.04, (0, 0, p["seat_h"]), coll, p["name"])
    bpy.context.view_layer.update()        # без этого seat.matrix_world — устаревшая единичная, ножки «повиснут»
    for i in range(p["legs"]):
        a = 2 * math.pi * i / p["legs"]
        leg = cylinder(f"Leg{i}", p["leg_r"], p["seat_h"], (0.7 * p["seat_r"] * math.cos(a), 0.7 * p["seat_r"] * math.sin(a),
                                                         p["seat_h"] / 2), coll, p["name"])
        leg.parent = seat; leg.matrix_parent_inverse = seat.matrix_world.inverted()
    return coll

def verify(coll, p):
    bpy.context.view_layer.update()
    obs = list(coll.objects)
    zmin = min((o.matrix_world @ v.co).z for o in obs for v in o.data.vertices)
    report = {"objects": len(obs), "tagged": sum(o.get(TAG) == p["name"] for o in obs), "z_min": round(zmin, 4)}
    assert report["objects"] == 1 + p["legs"] and report["tagged"] == report["objects"], report
    assert abs(zmin) < 1e-4, report                              # стоит на полу
    print("REPORT", report)
    return report

r1 = verify(build(PARAMS), PARAMS)
r2 = verify(build(PARAMS), PARAMS)                                # повторный запуск — тот же результат
assert r1 == r2 and len([o for o in bpy.data.objects if o.get(TAG)]) == 4
```

### 4.2 Обёртка оператора

```python
# Blender 5.2.2 — [проверено] вызов оператора: poll, override, результат, понятная ошибка
import bpy

def run_op(op, *, override=None, **props):
    """op — например bpy.ops.object.shade_smooth. Возвращает set; при отказе — RuntimeError с причиной."""
    ctx = bpy.context.temp_override(**(override or {}))
    with ctx:
        if not op.poll():
            raise RuntimeError(f"{op.idname_py()}: poll() = False в этом контексте "
                               f"(режим {bpy.context.mode}, активный {getattr(bpy.context.object, 'name', None)})")
        result = op(**props)
    if result != {"FINISHED"}:
        raise RuntimeError(f"{op.idname_py()}({props}) → {result}: проверь имена, выделение, режим")
    return result

ob = bpy.data.objects["Cube"]
ov = dict(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob])
ob.modifiers.new("Sub", "SUBSURF")
run_op(bpy.ops.object.modifier_apply, override=ov, modifier="Sub")
try:
    run_op(bpy.ops.object.modifier_apply, override=ov, modifier="Nope")
except RuntimeError as e:
    print(e)                          # object.modifier_apply({'modifier': 'Nope'}) → {'CANCELLED'}: …
assert len(ob.data.vertices) == 26
```

### 4.3 Поиск своих объектов между вызовами MCP

```python
# Blender 5.2.2 — [проверено] «вызов 1» ставит тег, «вызов 2» находит по тегу, а не по имени
import bpy
# вызов 1
ob = bpy.data.objects.new("Hero", bpy.data.meshes.new("Hero"))
bpy.context.scene.collection.objects.link(ob)
ob["agent_role"] = "hero"
uid = ob.session_uid
del ob                                                     # переменные в MCP между вызовами не живут
# вызов 2 (новое пространство имён)
hero = next(o for o in bpy.data.objects if o.get("agent_role") == "hero")
assert hero.session_uid == uid
bpy.data.objects["Hero"].name = "Кружка"                   # переименование (или перевод UI) не ломает поиск по тегу
assert next(o for o in bpy.data.objects if o.get("agent_role") == "hero").name == "Кружка"
```

Тег в custom property сохраняется в `.blend` и переживает переименование и перевод интерфейса; `session_uid` —
только в пределах сеанса Blender [проверено: 05, 42].

### 4.4 Перечисления и движок

Значения перечислений не угадывать: брать из `bl_rna.properties[...].enum_items` для статических и из текста
`TypeError` для динамических (`01 §2.8`); движок — `try: engine = 'BLENDER_EEVEE' except TypeError` (для кода,
который должен работать и в 4.2–4.5, — запасной `'BLENDER_EEVEE_NEXT'`); view transform — по списку сборки (в 5.2 есть
«ACES 1.3», «ACES 2.0», «Khronos PBR Neutral»). Готовые функции: `bpyx.enum_values`, `set_enum`, `set_engine`,
`set_color_management` [проверено: 40-bpyx-tests].

### 4.5 Проверка результата в конце скрипта

```python
# Blender 5.2.2 — [проверено] отчёт сцены одной строкой JSON и жёсткие проверки
import json
import bpy
from mathutils import Vector

def scene_report(scene):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    geo = [o for o in scene.objects if o.type in {"MESH", "CURVE", "FONT"} and o.visible_get()]
    tris, pts = 0, []
    for o in geo:
        me = o.evaluated_get(dg).to_mesh()
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]      # bound_box ОРИГИНАЛА (текст/кривые)
    mn, mx = Vector(map(min, *pts)), Vector(map(max, *pts))
    return {"objects": len(geo), "tris": tris, "dims": [round(v, 3) for v in (mx - mn)],
            "z_min": round(mn.z, 4), "camera": scene.camera.name if scene.camera else None,
            "materials_missing": [o.name for o in geo if not any(s.material for s in o.material_slots)]}

rep = scene_report(bpy.context.scene)
print("SCENE_REPORT", json.dumps(rep, ensure_ascii=False))
assert rep["objects"] >= 1 and 0 < rep["tris"] < 1_000_000, rep     # бюджет треугольников — из брифа
assert rep["camera"] is not None, "без камеры рендер падает"
assert not rep["materials_missing"], f"без материала: {rep['materials_missing']}"
```

Для рендера — проверить, что файл существует и больше нескольких килобайт; для GLB — `gltf_check.py` (валидатор
Khronos) и `web_view.py` (агент E, инструменты в `99-raw/tools/`); для визуальной проверки — `render_views.py`
(помнить про габариты текста, §5.4 файла 01).

### 4.6 Стиль «только data API»

| Задача | Вместо оператора | Файл |
|---|---|---|
| создать примитив | `bmesh.ops.create_*` + `bm.to_mesh` | 01 §6.2 |
| сгладить / по углу | `me.shade_smooth()`, `me.set_sharp_from_angle()` | 01 §6.7 |
| применить модификаторы | `bpy.data.meshes.new_from_object(evaluated)` | 01 §7.3 |
| применить трансформации | `ob.data.transform(M)` | 01 §9.2 |
| origin в центр, на пол | `ob.data.transform` + `matrix_world` | 01 §9.5 |
| текст → меш | `new_from_object(evaluated)` | 01 §8 |
| камера на объекты | `cam.camera_fit_coords(dg, coords)` | 01 §4.5 |
| удалить / почистить | `bpy.data.objects.remove`, `orphans_purge()` | 01 §2.5 |
| сохранить копию | `bpy.data.libraries.write` / `save_as_mainfile(copy=True)` | 01 §10.1 |

Операторы остаются для UV-развёртки, ассетов, импорта/экспорта, рендера, сохранения и сложного edit-моделирования.

### 4.7 Протокол «ошибка → действие»

| Текст ошибки | Что это | Действие |
|---|---|---|
| `KeyError: 'bpy_prop_collection[key]: key "X" not found'` | нет элемента с таким именем (переименован, недоступен, переведён) | `bpy_probe.py node/type …`, таблица дрейфа, поиск по type/identifier |
| `AttributeError: 'T' object has no attribute 'x'` | свойство удалено/выдумано | `bpy_probe.py search x`, `type T`, таблица дрейфа |
| `TypeError: … enum "X" not found in (…)` | неверное значение перечисления | взять значение из списка в сообщении |
| `TypeError: … keyword "x" unrecognized` / `invalid keyword argument(s) (…), expected (…)` | нет такого параметра | `bpy_probe.py op cat.name` / список в сообщении |
| `ValueError: … should contain N items, not M` | не та размерность | привести к N компонентам |
| `TypeError: … expected an int type, not float` | тип | `int(...)` |
| `RuntimeError: Operator bpy.ops.X.poll() …` | контекст/режим/область | активный объект в слое вида, режим, `temp_override`, область VIEW_3D |
| `RuntimeError: Error: Node type X undefined` | нет ноды с таким bl_idname | `bpy_probe.py nodes <Tree> <слово>` |
| `ReferenceError: StructRNA of type X has been removed` | ссылка на удалённое | получить объект заново |
| `{'CANCELLED'}` без исключения | оператор отказался | имена, выделение, `logging_set(True)` |
| `DeprecationWarning: 'X' is expected to be removed in Blender 6.0` | устаревшее свойство | убрать (для `use_nodes` — просто удалить строку) |

Правило исправления: **одно изменение → перезапуск → чтение нового сообщения**; не заворачивать в `except
Exception`; при второй неудаче на том же месте — справка (`bpy_probe.py`) вместо новой догадки [практика].

## 5. Собственные ошибки при работе (показательно)

| Ошибка | Где | Симптом | Урок |
|---|---|---|---|
| `images.new(..., generated_type="COLOR_GRID")` | эксперимент 14 | `TypeError: … invalid keyword argument(s) (generated_type), expected (name, width, height, alpha, float_buffer, stereo3d, is_data, tiled)` | даже «знающий» агент выдумывает параметры; сообщение сразу дало список |
| доступ к `m.bl_rna` после `ob.modifiers.remove(m)` | bpyx `add_modifier`, `node` | `ReferenceError: StructRNA of type MirrorModifier has been removed` | читать всё нужное до удаления |
| ссылка на UV-слой через `mode_set` | bpyx `uv_unwrap` | `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa0` | после смены режима — только перечитывание по имени |
| ожидания тестов (икосфера 1.902 по X, тор 32×16, cube_project 4 UV-точки, икосфера GN 162 вершины) | test_bpyx, 02 §5.6 | assert | числа — только из запуска, не «из головы» |
| `child.matrix_parent_inverse = parent.matrix_world.inverted()` сразу после `parent.location = …` | пример §4.1 этого файла | тихо: ножки табурета на 0,43 м выше пола (поймано `assert z_min`) | перед чтением `matrix_world` — `view_layer.update()`; отчёт с `assert` ловит такие ошибки |

[проверено: 14, 40-bpyx-tests, 42-doc-snippets].

## Частые ошибки (при исправлении ошибок)

- Повторять тот же код с мелкой перестановкой вместо чтения сообщения — в 5.2 почти все сообщения содержат ответ
  (список допустимых значений или параметров).
- Глушить исключения (`except Exception: pass`) — громкая ошибка становится тихой; тихие ошибки находятся только
  отчётом и визуальной проверкой.
- Чинить `KeyError` у сокета, перебирая индексы, — индекс может попасть в скрытый или недоступный сокет (B8.1).
- Добавлять `bpy.ops.object.select_all(action='SELECT')` «чтобы заработало» — операция уйдёт на все объекты сцены
  пользователя; нужен `temp_override` с конкретными объектами.
- После ошибки в середине длинного MCP-скрипта считать, что первая половина не выполнилась, — данные сцены уже
  изменены; идемпотентная сборка (§4.1) снимает проблему.

## Чек-лист

- [ ] Код проверен на имена из таблицы дрейфа (нет `use_auto_smooth`, `fcurves`, `node_tree`, `use_bloom`, `mod[...]`)?
- [ ] Незнакомые свойства/параметры/ноды сверены через `bpy_probe.py` до запуска?
- [ ] Результаты всех операторов проверены на `{'FINISHED'}`?
- [ ] Новые объекты привязаны к коллекции и помечены тегом (для MCP)?
- [ ] Нет обращений к данным после `remove`/`mode_set` без перечитывания?
- [ ] Цвета RGBA линейные, углы в радианах, размерности векторов верны?
- [ ] Связи нод `is_valid`, у материала есть Material Output?
- [ ] Пути абсолютные?
- [ ] В конце — строка отчёта и `assert` на ожидаемые числа?
- [ ] Повторный запуск скрипта даёт тот же результат?

## Открытые вопросы и противоречия

- Доля тихих ошибок (14 из 41) получена на выборке, составленной автором по памяти о типичном коде; на реальных
  логах агента (MCP-траектории) она может отличаться — кандидат на измерение для агента J (волна 3).
- Класс B9 (висячие ссылки) проверен на двух своих ошибках; краш (а не исключение/мусор) не воспроизводился
  намеренно — на общей машине.
- Коды B1–B14 не согласованы с кодами M* каталога C1 (пишется параллельно); синтез (волна 4) должен свести их в один
  реестр.
- MCP-специфика (таймаут 180 с, телеметрия, протоколы 7/9) — вне этого файла (C1).

## Источники

- [S1] Blender Foundation. Troubleshooting Errors & Crashes. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_crashes.html — висячие ссылки, перевыделение; первичный.
- [S2] Blender Foundation. Using Operators. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_operators.html — poll, контекст; первичный.
- [S3] Blender Foundation. Internal Data & Their Python Objects. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_internal_data_and_python_objects.html — имена, устаревшие значения; первичный.
- [S4] Blender Foundation. Modes and Mesh Access. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_meshes.html — edit mode; первичный.
- [S5] Blender Foundation. Python Threads are Not Supported. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_threading.html — потоки; первичный.
- [S6] Blender Foundation. File Paths & String Encoding. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_file_paths_and_encoding.html — пути; первичный.
- [S9] Blender Foundation. Quickstart. API 5.2 — https://docs.blender.org/api/5.2/info_quickstart.html — контекст только для чтения; первичный.
- [S11] Blender Foundation. Tips and Tricks. API 5.2 — https://docs.blender.org/api/5.2/info_tips_and_tricks.html — перезагрузка модулей; первичный.
- [S12] Blender Foundation. Operators (bpy.ops). API 5.2 — https://docs.blender.org/api/5.2/bpy.ops.html — CANCELLED без исключения; первичный.
- [S13] Blender Foundation. Context.temp_override. API 5.2 — https://docs.blender.org/api/5.2/bpy.types.Context.html — logging_set; первичный.
- [S14] Blender Foundation. BMesh Module. API 5.2 — https://docs.blender.org/api/5.2/bmesh.html — жизненный цикл bmesh; первичный.
- [S38] BlenderMCP, `blender_mcp.py` (протокол 7) — execute_code, describe_node_type; исходник.
- [S40]–[S44] Blender Stack Exchange: вопросы 247520, 253001, 306355, 316696, 290746 (ответы 2021–2024; API stackexchange.com, 2026-09-23) — «код по памяти» с высоким рейтингом; проверены в 5.2.2 (эксперимент 19).
- [C1] Агент C1, каталог ошибок нейросетей в 3D — `../04-ai-agents-mcp/05-failure-modes-catalog.md` (пишется параллельно).
