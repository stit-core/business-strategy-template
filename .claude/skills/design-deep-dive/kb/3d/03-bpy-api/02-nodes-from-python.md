# Ноды из Python в Blender 5.2: шейдеры, группы, geometry nodes, композитор

Волна 1 · агент B · 2026-09-23 · источников прочитано 47 (40 целиком; в этом файле цитируются 21) · экспериментов по теме 9
(00, 01, 02, 03, 11, 12, 13, 19, 40) · Blender 5.2.2 LTS. Все блоки `python` с меткой
`[проверено]` выполнены автоматически в чистой сцене 5.2.2.

## Выжимка для агента

1. **Перед кодом с нодой узнай её сокеты в ЭТОЙ версии**: `python3 ../../scripts/3d/bpy_probe.py node <bl_idname>
   [prop=value]` (или MCP `describe_node_type`) — identifier, имя, тип, доступность, умолчания. → §1 [проверено: 00-bpy-probe]
2. **Ноды ищи по `node.type` или `bl_idname`, не по имени**: в русском интерфейсе «Principled BSDF» называется
   «Принципиальный BSDF», `nodes["Principled BSDF"]` → KeyError. → §2.1 [проверено: 15-localization]
3. **У новых нод geometry nodes `node.type` — не константа** (`'GeometryNodeInputInstanceBounds'`, `'Split to
   Instances'`) → для GN сравнивай `bl_idname`. → §2.1 [проверено: 00-bpy-probe]
4. **Сначала режим ноды (`data_type`, `operation`, `blend_type`), потом поиск сокетов**: `inputs["A"]` ищет по имени
   СРЕДИ ДОСТУПНЫХ сокетов, ссылка, взятая до смены режима, указывает на ставший недоступным сокет. → §2.2 [проверено: 01-socket-lookup]
5. **Mix и Map Range не ищутся по identifier** (`mix.inputs["A_Color"]` → KeyError всегда — запрет в исходнике 5.2.2,
   сокеты планируют слить); у остальных нод строка сперва сверяется с identifier. → §2.2 [проверено: 01; исходник rna_nodetree.cc]
6. **Не обращайся к сокетам по индексу**: у Principled в 5.2 `inputs[7]` — скрытый «Weight», `inputs[9]` —
   «Subsurface Weight» (в 3.x это были Specular и Roughness); запись по старому индексу молча идёт не туда. → §3.2 [проверено: 11, 17]
7. **После `links.new` проверяй `link.is_valid`**: связь Shader → Color или с недоступным сокетом создаётся без
   исключения, но не работает (красная в UI). → §2.4 [проверено: 01, 11]
8. **Новый материал и мир в 5.x сразу с деревом**; `use_nodes = True` не нужен (DeprecationWarning, удаление в 6.0). → §3.1 [проверено: 03-version-drift]
9. **Principled BSDF v2 (4.0+)**: Specular → «Specular IOR Level», Transmission → «Transmission Weight», Clearcoat →
   «Coat Weight», Sheen → «Sheen Weight», Emission → «Emission Color» (+ «Emission Strength», по умолчанию 0),
   Subsurface → «Subsurface Weight», Specular Tint — цвет. → §3.2 [проверено: 03, 11]
10. **Цвета в сокетах — линейные RGBA из 4 чисел**; hex/CSS переводи из sRGB. → §3.3 [проверено: 17]
11. **Карты данных (roughness, metallic, normal, ORM) — `image.colorspace_settings.name = 'Non-Color'`**, цветовые — 'sRGB';
    значения 'Linear' в 5.2 нет. → §3.3 [проверено: 17; 00-bpy-probe]
12. **Процедурные ноды (Noise, Voronoi, Wave, ColorRamp, Bump, Math, Mix) не переживают экспорт glTF** — для веба их
    запекают в текстуры (агент E). → §3.5 [документация: E-notes; ../08-export-gltf/]
13. **ColorRamp: `color_ramp.elements.new(pos)`; последний элемент удалить нельзя** (RuntimeError). → §3.4 [проверено: 11]
14. **Musgrave удалён (4.1) → `ShaderNodeTexNoise` с `noise_type`; Separate/Combine RGB удалены (5.0) →
    `ShaderNodeSeparateColor/CombineColor(mode=…)`; `ShaderNodeMixRGB` — скрытая устаревшая, бери `ShaderNodeMix`.** → §3.4 [проверено: 03]
15. **Группа нод: `tree.interface.new_socket(name, in_out='INPUT', socket_type='NodeSocketFloat', parent=panel)`**;
    `socket_type` — только базовые типы (Factor — через `subtype='FACTOR'`); `NodeTree.inputs.new` удалён в 4.0. → §4 [проверено: 03, 11]
16. **`interface.move(item, to_position)`** (не `to_index`, как в заметках 4.0); элементы интерфейса ищутся по
    identifier: `interface.items_tree["Socket_2"]`. → §4 [проверено: 03, 42]
17. **Входы модификатора GN в 5.2 — `mod.properties.inputs.<identifier>.value`**; старый `mod["Socket_2"] = …` → TypeError. → §5.2 [проверено: 02, 19]
18. **Имя входа модификатора → identifier: `{p.name: p.identifier for p in mod.properties.inputs.bl_rna.properties}`**
    (у самого элемента `.name` пустой). → §5.2 [проверено: 02]
19. **После присвоения входа GN вызывай `ob.update_tag()`**: в 5.2.2 без него результат не пересчитывается даже после
    `view_layer.update()`. → §5.2 [проверено: 12-geonodes]
20. **Атрибут на вход GN — `item.type = 'ATTRIBUTE'; item.attribute_name = "…"`; выходной атрибут —
    `mod.properties.outputs.<id>.attribute_name`.** → §5.2 [проверено: 02]
21. **Типы входов статичны**: целочисленному входу float → TypeError. → §5.2 [проверено: 02]
22. **Свойства многих GN-нод и нод композитора стали входами-меню (5.x)**: Resample Curve `inputs["Mode"].default_value
    = "Count"` (не `node.mode = 'COUNT'`), Glare `inputs["Type"] = "Bloom"`; значения меню — отображаемые имена. → §2.3 [проверено: 00, 03, 12; исходник node.cc]
23. **Random Value и Compare в 5.2 — один динамический вход/выход** (`Min`, `Max`, `Value`; `A`, `B`): `outputs[1]`,
    `inputs["A_INT"]`, `"Value_001"` больше нет. → §5.5 [проверено: 03]
24. **Инстансы не попадают в меш**: перед применением и экспортом ставь Realize Instances (или `export_gn_mesh` у
    экспортёра — агент E); считать инстансы — `depsgraph.object_instances`. → §5.4 [проверено: 12]
25. **Применить GN для экспорта: `ob.data = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); ob.modifiers.clear()`.** → §5.6 [проверено: 12]
26. **Дерево GN, созданное кодом, имеет `is_modifier = False`**: модификатору назначается, но в выпадающем списке UI не
    видно — для человека ставь `tree.is_modifier = True`. → §5.1 [проверено: 42-doc-snippets]
27. **Композитор 5.x: `scene.compositing_node_group = bpy.data.node_groups.new(..., "CompositorNodeTree")`**, выход —
    `NodeGroupOutput` + сокет интерфейса «Image»; `scene.node_tree` и `CompositorNodeComposite` удалены. → §6 [проверено: 03, 13]
28. **Bloom EEVEE (удалён в 4.2) — Glare в композиторе**: `inputs["Type"].default_value = "Bloom"`; работает в фоновом
    рендере (средний RGB кадра 0,49 → 0,62). → §6 [проверено: 13]
29. **Раскладка: `node.location`; внутри рамки `location` относителен рамке, абсолют — `node.location_absolute`**. → §3.7 [проверено: 11]
30. **Ноды GN, которых нет**: тора (`GeometryNodeMeshTorus`) нет; Fill Curve — `GeometryNodeFillCurve`; Transform
    Geometry — `GeometryNodeTransform`; в 5.2 появился `GeometryNodeMeshBevel`. → §5.7 [проверено: 00, 12]

## 1. Интроспекция: как узнать сокеты, свойства и значения

| Вопрос | Без MCP (фон) | MCP (GUI) |
|---|---|---|
| сокеты ноды в нужном режиме | `bpy_probe.py node ShaderNodeMix data_type=RGBA` | `describe_node_type(bl_idname, property_overrides)` |
| все ноды, доступные в дереве | `bpy_probe.py nodes GeometryNodeTree [фильтр]` | нет |
| свойства/функции типа, одно свойство с enum | `bpy_probe.py type Object.rotation_mode` | `bpy_api_lookup("Object.rotation_mode")` |
| параметры оператора | `bpy_probe.py op export_scene.gltf` | `bpy_api_lookup("bpy.ops.export_scene.gltf")` |
| фактические значения динамического enum | `bpy_probe.py enum scene.view_settings.view_transform` | нет |
| допустимые `socket_type` интерфейса | `bpy_probe.py sockets GeometryNodeTree` | нет |
| что устарело в этой версии | `bpy_probe.py deprecated` | нет |

`bpy_probe.py` (`99-raw/tools/`) сам запускает Blender в фоне и печатает JSON за 0,3–1,5 с; код 3 — ошибка с
`did_you_mean` [проверено: 00-bpy-probe]. В отличие от MCP `describe_node_type` [S38] он сообщает доступность сокета
(`"enabled": false`), фактические значения перечисления в ЭТОМ дереве (`items_runtime`: Mix `data_type` в шейдерном
дереве принимает FLOAT/VECTOR/RGBA, хотя RNA перечисляет и ROTATION) и дубли имён. Числа по состоянию 5.2.2:
создаются в шейдерном дереве 118 нод, в GN — 360, в композиторе — 168; нет в меню Add (устаревшие/служебные):
`ShaderNodeBsdfAnisotropic` (алиас Glossy), `ShaderNodeMixRGB`, `ShaderNodeSqueeze`, `CompositorNodeSwitch`
[проверено: 00-bpy-probe]. Эталонные дампы: `99-raw/experiments/B/00-bpy-probe/` (Principled, Glare, списки нод).

То же руками внутри Blender:

```python
# Blender 5.2.2 — [проверено] сокеты ноды в нужном режиме — «probe» в своём коде
import bpy
tree = bpy.data.node_groups.new("__probe__", "ShaderNodeTree")
n = tree.nodes.new("ShaderNodeMix")
n.data_type = "RGBA"                                   # режим — до чтения сокетов
rows = [(i, s.identifier, s.name, s.type, s.enabled) for i, s in enumerate(n.inputs)]
enabled = [r[1] for r in rows if r[4]]
assert enabled == ["Factor_Float", "A_Color", "B_Color"], enabled
print(rows)
bpy.data.node_groups.remove(tree)
```

## 2. Ноды, сокеты, связи

### 2.1 Поиск и создание нод

- Создание — только по `bl_idname`: `tree.nodes.new("ShaderNodeBsdfPrincipled")`; `nodes.new("Principled BSDF")` →
  `RuntimeError: Error: Node type Principled BSDF undefined` [проверено: 17].
- Поиск — по `n.type == 'BSDF_PRINCIPLED'` (у шейдерных нод константа) или `n.bl_idname == 'ShaderNodeBsdfPrincipled'`.
  Имя `n.name` задаётся при создании и переводится (ru_RU: «Принципиальный BSDF», «Вывод материала»; de_DE:
  «Material-Ausgabe») [проверено: 15-localization]. У части новых GN-нод `type` равен `bl_idname` или даже подписи
  («Split to Instances») [проверено: 00-bpy-probe].
- Если нужно несколько однотипных нод — задать им свои имена/метки при создании и искать по ним.

```python
# Blender 5.2.2 — [проверено] найти ноды материала без опоры на имена
import bpy
mat = bpy.data.materials.new("Paint")                       # 5.x: дерево по умолчанию уже есть
nt = mat.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
assert out.inputs["Surface"].links[0].from_node == p
assert [s.name for s in out.inputs] == ["Surface", "Volume", "Displacement", "Thickness"] and out.target == "ALL"
```

### 2.2 Поиск сокета: правило 5.2.2

Исходник 5.2.2 (`source/blender/makesrna/intern/rna_nodetree.cc`, функция `find_socket_by_key`) [S36]: строковый ключ
`node.inputs[key]` сначала сравнивается с **identifier** доступных (`is_available`) сокетов, затем с **именем**
доступных. Для `SH_NODE_MIX` и `SH_NODE_MAP_RANGE` поиск по identifier выключен (`allow_identifier_lookup`) с
комментарием «identifiers are likely to change soon because dynamically typed sockets are joined into one».
Недоступный сокет по строке не находится вовсе. Эмпирика [проверено: 01-socket-lookup]:

| Ключ | FLOAT | VECTOR | RGBA |
|---|---|---|---|
| `mix.inputs["A"]` | A_Float | A_Vector | A_Color |
| `mix.inputs["Factor"]` | Factor_Float | Factor_Float (Factor_Vector при `factor_mode='NON_UNIFORM'`) | Factor_Float |
| `mix.outputs["Result"]` | Result_Float | Result_Vector | Result_Color |
| `mix.inputs["A_Color"]` / `.get("A_Color")` / `"A_Color" in inputs` | KeyError / None / False | то же | то же (запрет) |
| `mix.inputs[6]` | A_Color (`enabled=False`) | A_Color (`enabled=False`) | A_Color |

Прочее: `inputs.keys()` — имена с повторами; оператор `in` — по именам; `group_node.inputs["Socket_1"]` и
`["Size"]` работают (identifier разрешён); у Store Named Attribute с 4.1 один динамический сокет «Value»
(`"Value_Float"` → KeyError); у Math повторяются имена: `inputs[0]` = «Value», `inputs[1]` = «Value_001»,
`inputs[2]` = «Value_002» (третий недоступен при POWER) [проверено: 01, 12].

```python
# Blender 5.2.2 — [проверено] правильный порядок: режим → сокет → связь → проверка
import bpy
tree = bpy.data.node_groups.new("T", "ShaderNodeTree")
rgb = tree.nodes.new("ShaderNodeRGB")
bad = tree.nodes.new("ShaderNodeMix")
a_old = bad.inputs["A"]                        # при FLOAT это A_Float
bad.data_type = "RGBA"                         # режим сменили ПОСЛЕ — ссылка устарела
l_bad = tree.links.new(rgb.outputs["Color"], a_old)
assert l_bad.is_valid is False and a_old.enabled is False
good = tree.nodes.new("ShaderNodeMix")
good.data_type = "RGBA"; good.blend_type = "MULTIPLY"
l_ok = tree.links.new(rgb.outputs["Color"], good.inputs["A"])
assert l_ok.is_valid and good.inputs["A"].identifier == "A_Color"
def sock(node, ident):                          # identifier — перебором (для Mix/MapRange иначе нельзя)
    return next(s for s in node.inputs if s.identifier == ident)
assert sock(good, "B_Color").enabled
```

### 2.3 Входы-меню вместо свойств (5.x)

С 5.0 (композитор) и в серии 5.x (geometry nodes) многие перечисления нод стали входными сокетами типа MENU —
их можно подключать и выставлять в модификаторе. По исходнику 5.2.2 (`node.cc`, `write_legacy_properties`) [S37]
и заметкам 5.0 [S34] это: GN — Transform Geometry «Mode»; Points to Volume, Volume to Mesh, Mesh to Volume
«Resolution Mode»; Triangulate «Quad Method», «N-gon Method»; Fill Curve, Fillet Curve, Resample Curve, Distribute
Points in Volume, Merge by Distance, Set Curve Normal «Mode»; Raycast, Sample Grid «Interpolation»; Remove Named
Attribute «Pattern Mode»; Scale Elements «Scale Mode»; Subdivision Surface «UV Smooth», «Boundary Smooth»; UV Pack
Islands, UV Unwrap «Method»; Match String «Operation»; String to Curves «Overflow», «Align X», «Align Y», «Pivot
Point». Композитор — «Type» у Blur, Filter, Dilate/Erode, Tonemap, Lens Distortion, Kuwahara, Set Alpha, Color
Balance, Premultiply Key, Movie Distortion, Glare («Type», «Quality»); Denoise «Prefilter», «Quality»; Translate,
Transform, Corner Pin, Map UV, Scale, Rotate, Displace «Interpolation», «Extension X/Y» и др. Шейдерные ноды не
затронуты. Значения меню — отображаемые имена (`"Count"`, `"Bloom"`), а не константы:

```python
# Blender 5.2.2 — [проверено] входы-меню: значения и присвоение
import bpy
g = bpy.data.node_groups.new("G", "GeometryNodeTree")
rs = g.nodes.new("GeometryNodeResampleCurve")
assert "mode" not in rs.bl_rna.properties                       # rs.mode = 'COUNT' → AttributeError
m = rs.inputs["Mode"]
print(m.type, m.default_value, [i.identifier for i in m.bl_rna.properties["default_value"].enum_items])
try:
    m.default_value = "__x__"
except TypeError as e:
    print(e)                                                    # enum "__x__" not found in ('Evaluated', 'Count', 'Length')
m.default_value = "Count"
c = bpy.data.node_groups.new("C", "CompositorNodeTree")
gl = c.nodes.new("CompositorNodeGlare")
gl.inputs["Type"].default_value = "Bloom"; gl.inputs["Quality"].default_value = "High"
gl.inputs["Threshold"].default_value = 1.0                      # identifier «Highlights Threshold», имя «Threshold»
assert (m.default_value, gl.inputs["Type"].default_value) == ("Count", "Bloom")
```

Список значений меню так же даёт `bpy_probe.py node CompositorNodeGlare` (Type: Bloom, Ghosts, Streaks, Fog Glow,
Simple Star, Sun Beams, Kernel; Quality: High, Medium, Low) [проверено: 00-bpy-probe].

### 2.4 Связи

- `tree.links.new(from_output, to_input, verify_limits=True, handle_dynamic_sockets=False)`; перепутанные аргументы
  Blender разворачивает сам [проверено: 11].
- Связь создаётся без исключения и тогда, когда не работает: Shader → Color, на недоступный сокет → `link.is_valid ==
  False` (в UI — красная); проверка всех связей — `all(l.is_valid for l in tree.links)` [проверено: 01, 11, 17].
- Удаление — `tree.links.remove(link)`; связи входа — `socket.links`; `socket.is_linked`.
- Виртуальный сокет «__extend__» у Group Input/Output и Capture Attribute — для новых сокетов перетаскиванием;
  связь с ним из Python — `links.new(..., handle_dynamic_sockets=True)` [не проверено; S18].

## 3. Шейдерные деревья

### 3.1 Материал и мир по умолчанию

С 5.0 `bpy.data.materials.new()` сразу создаёт дерево «Principled BSDF» → «Material Output» (1 связь), мир —
«Background» → «World Output»; `material.use_nodes`, `world.use_nodes` устарели (DeprecationWarning «is expected to be
removed in Blender 6.0»), `scene.use_nodes` и `light.use_nodes` — тоже [проверено: 03, 11; S27]. Свойства материала
по умолчанию: `surface_render_method='DITHERED'`, `use_backface_culling=False`, `use_transparency_overlap=True`,
`use_transparent_shadow=True`, `displacement_method='BUMP'` [проверено: 42-doc-snippets]. `blend_method = 'BLEND'`
(до 4.2) ещё принимается как алиас и выставляет `surface_render_method = 'BLENDED'`; `shadow_method` удалён
[проверено: 03]. `material.diffuse_color` — только вьюпорт.

### 3.2 Principled BSDF 5.2: входы

32 входа, у всех имя == identifier; выход «BSDF»; свойства `distribution='MULTI_GGX'`,
`subsurface_method='RANDOM_WALK'`; 8 панелей в `node.panel_states` (`is_collapsed = True` по умолчанию; с 5.2 можно
открывать из Python) [проверено: 11-shader-nodes; S29].

| # | Имя (= identifier) | Тип | По умолчанию | Было в 3.x |
|---|---|---|---|---|
| 0 | Base Color | RGBA | (0.8, 0.8, 0.8, 1) | Base Color; Subsurface Color удалён |
| 1 | Metallic | VALUE factor | 0 | |
| 2 | Roughness | VALUE factor | 0.5 | (индекс 9 в 3.x) |
| 3 | IOR | VALUE | 1.5 | |
| 4 | Alpha | VALUE factor | 1.0 | |
| 5 | Thin Wall | BOOLEAN | False | новое |
| 6 | Normal | VECTOR | (0, 0, 0) | |
| 7 | Weight | VALUE | 0 | скрытый служебный |
| 8 | Diffuse Roughness | VALUE factor | 0 | новое |
| 9 | Subsurface Weight | VALUE factor | 0 | Subsurface |
| 10 | Subsurface Radius | VECTOR | (1, 0.2, 0.1) | |
| 11 | Subsurface Scale | VALUE distance | 0.005 | |
| 12 | Subsurface IOR | VALUE factor | 1.4 | |
| 13 | Subsurface Anisotropy | VALUE factor | 0 | |
| 14 | Specular IOR Level | VALUE factor | 0.5 | Specular |
| 15 | Specular Tint | RGBA | (1, 1, 1, 1) | был float |
| 16 | Anisotropic | VALUE factor | 0 | |
| 17 | Anisotropic Rotation | VALUE factor | 0 | |
| 18 | Tangent | VECTOR | (0, 0, 0) | |
| 19 | Transmission Weight | VALUE factor | 0 | Transmission |
| 20 | Coat Weight | VALUE factor | 0 | Clearcoat |
| 21 | Coat Roughness | VALUE factor | 0.03 | Clearcoat Roughness |
| 22 | Coat IOR | VALUE | 1.5 | |
| 23 | Coat Tint | RGBA | (1, 1, 1, 1) | |
| 24 | Coat Normal | VECTOR | (0, 0, 0) | Clearcoat Normal |
| 25 | Sheen Weight | VALUE factor | 0 | Sheen |
| 26 | Sheen Roughness | VALUE factor | 0.5 | |
| 27 | Sheen Tint | RGBA | (1, 1, 1, 1) | был float |
| 28 | Emission Color | RGBA | (1, 1, 1, 1) | Emission (по умолчанию чёрный) |
| 29 | Emission Strength | VALUE | 0 | |
| 30 | Thin Film Thickness | VALUE wavelength | 0 | новое (4.2) |
| 31 | Thin Film IOR | VALUE | 1.33 | новое (4.2) |

Старые имена дают `KeyError: 'bpy_prop_collection[key]: key "Specular" not found'`; `Specular Tint = 0.5` →
`TypeError` (нужен цвет) [проверено: 03]. Emission Color по умолчанию белый при силе 0 — задать цвет без
`Emission Strength` = нет свечения.

### 3.3 Материал с картинками

```python
# Blender 5.2.2 — [проверено] PBR-материал из текстур: цвет sRGB, данные Non-Color
import bpy
def img(name, color, non_color):
    im = bpy.data.images.new(name, 16, 16, alpha=False)
    im.pixels.foreach_set([c for _ in range(16 * 16) for c in color])
    if non_color:
        im.colorspace_settings.name = "Non-Color"       # roughness/metallic/normal/ORM
    return im
mat = bpy.data.materials.new("Tiles")
nt = mat.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
uvn = nt.nodes.new("ShaderNodeTexCoord")
base = nt.nodes.new("ShaderNodeTexImage"); base.image = img("base", (0.8, 0.4, 0.2, 1), False)
rough = nt.nodes.new("ShaderNodeTexImage"); rough.image = img("rough", (0.6, 0.6, 0.6, 1), True)
nrm = nt.nodes.new("ShaderNodeTexImage"); nrm.image = img("normal", (0.5, 0.5, 1.0, 1), True)
nmap = nt.nodes.new("ShaderNodeNormalMap")                # space 'TANGENT' — единственное, что понимает glTF
for t in (base, rough, nrm):
    t.interpolation = "Linear"; t.extension = "REPEAT"      # значения 5.2: 'Linear', 'Closest', 'Cubic', 'Smart'
    nt.links.new(uvn.outputs["UV"], t.inputs["Vector"])
nt.links.new(base.outputs["Color"], p.inputs["Base Color"])
nt.links.new(rough.outputs["Color"], p.inputs["Roughness"])
nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], p.inputs["Normal"])
assert all(l.is_valid for l in nt.links) and nmap.space == "TANGENT"
assert rough.image.colorspace_settings.name == "Non-Color"
```

- Цветовые пространства картинок 5.2 — 67 значений; нужные для веба: `sRGB` (цвет), `Non-Color` (данные),
  `Linear Rec.709` (линейные HDR/EXR); значение `Linear` не существует → `TypeError: … enum "Linear" not found in
  ('ACES 1.3 sRGB', …)` [проверено: 17; 00-bpy-probe].
- `ShaderNodeTexImage`: входы Vector; выходы Color, Alpha; `projection='FLAT'`, `interpolation='Linear'`,
  `extension='REPEAT'` по умолчанию [проверено: 42-doc-snippets].
- Какие связки экспортёр glTF распознаёт (ORM через Separate Color, Normal Map только Tangent, «glTF Material Output»
  для occlusion, Mapping → KHR_texture_transform) — `../08-export-gltf/01-export-contract.md` (агент E).

### 3.4 Процедурный материал

```python
# Blender 5.2.2 — [проверено] шум → ColorRamp → цвет, Voronoi → шероховатость, бамп
import bpy
mat = bpy.data.materials.new("Proc"); nt = mat.node_tree; N, L = nt.nodes, nt.links
p = next(n for n in N if n.type == "BSDF_PRINCIPLED")
tc = N.new("ShaderNodeTexCoord")
mp = N.new("ShaderNodeMapping"); mp.vector_type = "POINT"; mp.inputs["Scale"].default_value = (3, 3, 3)
noise = N.new("ShaderNodeTexNoise"); noise.noise_type = "FBM"          # Musgrave слит сюда в 4.1
noise.inputs["Scale"].default_value = 4.0; noise.inputs["Detail"].default_value = 6.0
ramp = N.new("ShaderNodeValToRGB")                                     # Color Ramp
cr = ramp.color_ramp; cr.interpolation = "EASE"
cr.elements[0].position = 0.35; cr.elements[0].color = (0.05, 0.08, 0.20, 1)
cr.elements[1].position = 0.75; cr.elements[1].color = (0.95, 0.55, 0.20, 1)
cr.elements.new(0.55).color = (0.8, 0.2, 0.4, 1)
vor = N.new("ShaderNodeTexVoronoi"); vor.feature = "F1"; vor.distance = "EUCLIDEAN"
mr = N.new("ShaderNodeMapRange"); mr.data_type = "FLOAT"
mr.inputs["To Min"].default_value = 0.25; mr.inputs["To Max"].default_value = 0.7
bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4
wave = N.new("ShaderNodeTexWave"); wave.wave_type = "BANDS"; wave.bands_direction = "DIAGONAL"
mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "OVERLAY"
mix.inputs["Factor"].default_value = 0.25
pairs = [(tc.outputs["Object"], mp.inputs["Vector"]), (mp.outputs["Vector"], noise.inputs["Vector"]),
         (mp.outputs["Vector"], vor.inputs["Vector"]), (mp.outputs["Vector"], wave.inputs["Vector"]),
         (noise.outputs["Fac"], ramp.inputs["Fac"]), (ramp.outputs["Color"], mix.inputs["A"]),
         (wave.outputs["Color"], mix.inputs["B"]), (mix.outputs["Result"], p.inputs["Base Color"]),
         (noise.outputs["Fac"], bump.inputs["Height"]), (bump.outputs["Normal"], p.inputs["Normal"]),
         (vor.outputs["Distance"], mr.inputs["Value"]), (mr.outputs["Result"], p.inputs["Roughness"])]
links = [L.new(a, b) for a, b in pairs]
assert all(l.is_valid for l in links) and len(cr.elements) == 3
```

Рендер этого дерева на сфере — `99-raw/experiments/B/11-shader-nodes/procedural_sphere.png` (EEVEE 256 px, 16 сэмплов,
1,6 с) [проверено: 11]. Детали нод 5.2: Noise — `noise_dimensions` '3D', `noise_type` 'FBM' / 'RIDGED_MULTIFRACTAL' …,
`normalize` True, входы Vector, Scale, Detail, Roughness, Lacunarity, Distortion; Bump — Strength, Distance (0.001
по умолчанию, изменено в 4.5), Filter Width 0.1, Height, Normal; ColorRamp — 2 элемента, LINEAR, RGB; удалить
последний элемент нельзя (`RuntimeError: Error: Element not found in element collection or last element`)
[проверено: 11; S26].

Удалённое и устаревшее: `ShaderNodeTexMusgrave` (4.1) → Noise с `noise_type`; `ShaderNodeSeparateRGB`,
`CombineRGB`, `SeparateHSV`, `CombineHSV` (5.0) → `ShaderNodeSeparateColor`/`CombineColor` с `mode='RGB'|'HSV'|'HSL'`;
`ShaderNodeTexPointDensity` (5.0) — нет; `ShaderNodeBsdfGlossy` создаёт `ShaderNodeBsdfAnisotropic` (4.0);
`ShaderNodeMixRGB` работает, но скрыт из меню (замена — `ShaderNodeMix`, `data_type='RGBA'`) [проверено: 03].

### 3.5 Что из дерева доживёт до веба

Экспортёр glTF переносит только связки вокруг Principled BSDF: константы и Image Texture в Base Color, Metallic,
Roughness, Normal (через Normal Map), Emission, Alpha, Transmission, Coat, Sheen, Specular, IOR; ORM через Separate
Color; Mapping → KHR_texture_transform. Процедурные ноды (Noise, Voronoi, Wave, ColorRamp, Math, Mix, Bump, Layer
Weight, Fresnel) теряются молча — их запекают в текстуры [E-notes: search_node_tree.py, экспорт материалов; детали и
матрица — `../08-export-gltf/01-export-contract.md`, запекание — `../08-export-gltf/02-baking.md`, агент E].

### 3.6 Мир и свет

```python
# Blender 5.2.2 — [проверено] мир: небо Sky Texture и сила фона без опоры на имена
import math
import bpy
scene = bpy.context.scene
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
nt = scene.world.node_tree
bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
sky = nt.nodes.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"               # 5.x: 'SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETHAM', 'HOSEK_WILKIE'
sky.sun_elevation = math.radians(15); sky.sun_rotation = math.radians(45)
nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.8
assert nt.links[-1].is_valid
```

`sky_type = 'NISHITA'` (4.x) → TypeError со списком [проверено: 03]. HDRI — `ShaderNodeTexEnvironment` (`image =
bpy.data.images.load(path)`, `projection='EQUIRECTANGULAR'`). Свет в самом Blender задаётся свойствами Light
(`energy`, `color`, `size`/`shadow_soft_size`, `use_shadow`); `light.use_nodes` устарел (5.1) [проверено: 00-bpy-probe].
Для веба свет обычно ставят кодом в three.js или запекают (агенты D2, F, E).

### 3.7 Раскладка для человека

Результат от `location` не зависит, но дерево открывает человек или визуальная критика. Ставить колонки по глубине от
выхода (≈ 280 px по X, 200 по Y). Внутри рамки (`NodeFrame`, `node.parent = frame`) `node.location` становится
относительным к рамке; абсолютные координаты — `node.location_absolute` (5.x, можно присваивать) [проверено: 11].

```python
# Blender 5.2.2 — [проверено] раскладка по глубине от выхода, рамка
import bpy
mat = bpy.data.materials.new("L"); nt = mat.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
noise = nt.nodes.new("ShaderNodeTexNoise"); ramp = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
depth, frontier = {out: 0}, [out]
while frontier:
    nxt = []
    for n in frontier:
        for s in n.inputs:
            for l in s.links:
                if depth.get(l.from_node, -1) < depth[n] + 1:
                    depth[l.from_node] = depth[n] + 1; nxt.append(l.from_node)
    frontier = nxt
for n, d in depth.items():
    n.location_absolute = (-d * 280.0, 0.0)
frame = nt.nodes.new("NodeFrame"); frame.label = "Noise"; frame.location = (500, 300)
noise.parent = frame
assert tuple(noise.location_absolute) == (-840.0, 0.0) and tuple(noise.location) == (-1340.0, -300.0)
```

## 4. Группы нод и интерфейс (4.0+)

С 4.0 сокеты группы объявляются в `tree.interface` (`NodeTreeInterface`); `tree.inputs.new(...)` и
`tree.outputs.new(...)` удалены [S21; проверено: 03]. Сигнатуры 5.2 [S18; проверено: 11, 42]:
`new_socket(name, description='', in_out='INPUT', socket_type='DEFAULT', parent=None)`,
`new_panel(name, description='', default_closed=False)`, `copy(item)`, `remove(item, move_content_to_parent=True)`,
`clear()`, `move(item, to_position)`, `move_to_parent(item, parent, to_position)`, `items_tree` (выходы
перечисляются первыми), `items_tree[identifier]` (5.0+). Допустимые `socket_type` (5.2, GeometryNodeTree):
NodeSocketFloat, NodeSocketInt, NodeSocketBool, NodeSocketVector, NodeSocketColor, NodeSocketRotation,
NodeSocketMatrix, NodeSocketString, NodeSocketMenu, NodeSocketGeometry, NodeSocketObject, NodeSocketCollection,
NodeSocketImage, NodeSocketMaterial, NodeSocketFont, NodeSocketSound, NodeSocketBundle, NodeSocketClosure
(`bpy_probe.py sockets GeometryNodeTree`) [проверено: 00-bpy-probe]. Подтипы (Factor, Distance, Angle…) — свойство
`subtype` у сокета интерфейса; `socket_type='NodeSocketFloatFactor'` → `TypeError: … enum "NodeSocketFloatFactor" not
found` [проверено: 03].

```python
# Blender 5.2.2 — [проверено] шейдерная группа с панелью и её использование
import bpy
g = bpy.data.node_groups.new("TintGroup", "ShaderNodeTree")
iface = g.interface
panel = iface.new_panel("Tint", description="Оттенок", default_closed=False)
iface.new_socket(name="Color", in_out="INPUT", socket_type="NodeSocketColor")
amt = iface.new_socket(name="Amount", in_out="INPUT", socket_type="NodeSocketFloat", parent=panel)
amt.subtype = "FACTOR"; amt.min_value = 0.0; amt.max_value = 1.0; amt.default_value = 0.5
tint = iface.new_socket(name="Tint", in_out="INPUT", socket_type="NodeSocketColor", parent=panel)
tint.default_value = (1.0, 0.3, 0.2, 1.0)
iface.new_socket(name="Color", in_out="OUTPUT", socket_type="NodeSocketColor")
gi = g.nodes.new("NodeGroupInput"); go = g.nodes.new("NodeGroupOutput")
mix = g.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
g.links.new(gi.outputs["Color"], mix.inputs["A"]); g.links.new(gi.outputs["Tint"], mix.inputs["B"])
g.links.new(gi.outputs["Amount"], mix.inputs["Factor"]); g.links.new(mix.outputs["Result"], go.inputs["Color"])
iface.move(tint, 0)                                   # move(item, to_position); to_index= → TypeError
assert iface.items_tree[amt.identifier].name == "Amount"
mat = bpy.data.materials.new("Tinted"); nt = mat.node_tree
node = nt.nodes.new("ShaderNodeGroup"); node.node_tree = g
node.inputs["Amount"].default_value = 0.3
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
assert nt.links.new(node.outputs["Color"], p.inputs["Base Color"]).is_valid
assert [s.name for s in node.inputs] == ["Color", "Amount", "Tint"] or len(node.inputs) == 3
```

Идентификаторы сокетов интерфейса — `Socket_0`, `Socket_1`… по порядку создания (выходы, созданные позже входов,
получают следующие номера); у ассетов из 4.0 и раньше встречаются `Input_0`, `Input_1` («Smooth by Angle»:
`Input_0` Mesh, `Input_1` Angle, `Socket_1` Ignore Sharpness) — не угадывать, читать из интерфейса [проверено: 02, 06].
Пример `interface.move(socket, to_index=2)` из заметок 4.0 в 5.2 даёт `TypeError: NodeTreeInterface.move(): required
parameter "to_position" not specified` [проверено: 42-doc-snippets; S21].

## 5. Geometry nodes из Python

### 5.1 Дерево и модификатор

```python
# Blender 5.2.2 — [проверено] дерево GN с интерфейсом, модификатор, входы по имени
import bpy
tree = bpy.data.node_groups.new("Line", "GeometryNodeTree")
assert tree.is_modifier is False                         # кодом назначить можно, в выпадающем списке UI не видно
tree.is_modifier = True
iface = tree.interface
count = iface.new_socket(name="Count", in_out="INPUT", socket_type="NodeSocketInt")
count.default_value = 4; count.min_value = 2; count.max_value = 1000
spacing = iface.new_socket(name="Spacing", in_out="INPUT", socket_type="NodeSocketFloat")
spacing.default_value = 0.5; spacing.subtype = "DISTANCE"
iface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = tree.nodes.new("NodeGroupInput"); go = tree.nodes.new("NodeGroupOutput")
line = tree.nodes.new("GeometryNodeMeshLine"); comb = tree.nodes.new("ShaderNodeCombineXYZ")
L = tree.links
for a, b in ((gi.outputs["Count"], line.inputs["Count"]), (gi.outputs["Spacing"], comb.inputs["X"]),
             (comb.outputs["Vector"], line.inputs["Offset"]), (line.outputs["Mesh"], go.inputs["Geometry"])):
    assert L.new(a, b).is_valid
ob = bpy.data.objects.new("GN", bpy.data.meshes.new("GN")); bpy.context.scene.collection.objects.link(ob)
mod = ob.modifiers.new("Line", "NODES"); mod.node_group = tree
ids = {p.name: p.identifier for p in mod.properties.inputs.bl_rna.properties if p.identifier not in ("rna_type", "name")}
getattr(mod.properties.inputs, ids["Count"]).value = 25
ob.update_tag()                                          # 5.2.2: без этого пересчёта нет
dg = bpy.context.evaluated_depsgraph_get()
assert len(ob.evaluated_get(dg).data.vertices) == 25
```

Модификатор-объект может быть и пустышкой (5.2: GN-модификаторы на Empty) [S35]. Для деревьев-инструментов —
`is_tool` [проверено: 42-doc-snippets].

### 5.2 Входы модификатора: API 5.2

| Задача | 4.0–5.1 (IDProperty) | 5.2 |
|---|---|---|
| значение входа | `mod["Socket_2"] = 5.0` | `mod.properties.inputs.Socket_2.value = 5.0` |
| брать из атрибута | `mod["Socket_2_use_attribute"] = True` | `….type = 'ATTRIBUTE'` (или 'VALUE') |
| имя входного атрибута | `mod["Socket_2_attribute_name"] = "w"` | `….attribute_name = "w"` |
| имя выходного атрибута | `mod["Socket_5_attribute_name"] = "out"` | `mod.properties.outputs.Socket_5.attribute_name = "out"` |
| использован ли вход | — | `mod.is_input_used("Socket_2")`, `mod.is_input_visible(...)` |
| список входов | `mod.keys()` | `mod.properties.inputs.bl_rna.properties` (RNA-имя = имя сокета) |

В 5.2.2 старый способ сломан полностью: `mod["Socket_1"]` → `TypeError: this type doesn't support IDProperties`;
`mod["Socket_1"] = 3.0` → `TypeError: bpy_struct[key] = val: id properties not supported for this type`;
`mod.keys()` → TypeError [проверено: 02, 03, 19; S29]. Значение по умолчанию берётся из `default_value` сокета
интерфейса, мягкий диапазон — из `min_value/max_value` (жёсткого нет: 20 при max 10 принимается), тип статичен
(int ← float → `TypeError: … Socket_2.value expected an int type, not float`) [проверено: 02]. После присвоения —
`ob.update_tag()`: в 5.2.2 без него результат прежний даже после `view_layer.update()`; пересчёт вызывают также
`node_group.interface_update(context)` и касание любого RNA-свойства модификатора (`mod.show_viewport = True`)
[проверено: 12-geonodes]. Универсальная функция с откатом на IDProperty для < 5.2 — `bpyx.gn_set_input(mod,
"Count", 25)` [проверено: 40-bpyx-tests; ветка < 5.2 — не проверено].

```python
# Blender 5.2.2 — [проверено] вход из атрибута, выходной атрибут, объект и материал
import bpy
t = bpy.data.node_groups.new("Attr", "GeometryNodeTree")
iface = t.interface
iface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
w = iface.new_socket(name="Weight", in_out="INPUT", socket_type="NodeSocketFloat")
mat = iface.new_socket(name="Material", in_out="INPUT", socket_type="NodeSocketMaterial")
iface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
out_attr = iface.new_socket(name="Mask", in_out="OUTPUT", socket_type="NodeSocketFloat")
gi = t.nodes.new("NodeGroupInput"); go = t.nodes.new("NodeGroupOutput")
t.links.new(gi.outputs["Geometry"], go.inputs["Geometry"]); t.links.new(gi.outputs["Weight"], go.inputs["Mask"])
ob = bpy.data.objects["Cube"]
m = ob.modifiers.new("Attr", "NODES"); m.node_group = t
inp = getattr(m.properties.inputs, w.identifier)
inp.type = "ATTRIBUTE"; inp.attribute_name = "height"           # поле из атрибута меша
getattr(m.properties.inputs, mat.identifier).value = bpy.data.materials.new("Red")
getattr(m.properties.outputs, out_attr.identifier).attribute_name = "mask"
ob.update_tag()
try:
    m[w.identifier] = 1.0                                        # как в 4.x
except TypeError as e:
    print("старый способ:", e)
assert m.is_input_used(w.identifier) is True and inp.type == "ATTRIBUTE"
```

### 5.3 Поля и атрибуты

- Поля вычисляются в домене ноды, которая их потребляет: Position, Normal, Index, Named Attribute — входы полей;
  Set Position, Store Named Attribute (один динамический сокет «Value» с 4.1, тип — `data_type`, домен — `domain`),
  Capture Attribute (5.x: `capture_items.new('FLOAT', 'Foo')`, сокеты «Value»/«Attribute» с именем «Foo»; в 5.2 —
  вход Selection) [проверено: 01; S35].
- Атрибут, записанный GN, доступен в вычисленном меше (`ob.evaluated_get(dg).data.attributes`) и после
  `new_from_object`; экспорт произвольных атрибутов в glTF — `export_attributes=True` (агент E).

### 5.4 Инстансы и Realize

Instance on Points создаёт инстансы: в вычисленном меше их нет, они в `depsgraph.object_instances`; `new_from_object`
без Realize Instances даёт только основную геометрию (разброс по плоскости: 4 вершины основы и 160 инстансов; с
Realize — 1924 вершины, 3202 треугольника) [проверено: 12]. Для экспорта: Realize в дереве или экспорт инстансов
расширением `EXT_mesh_gpu_instancing` (`export_gpu_instances`, агент E).

### 5.5 Четыре рабочих примера

Все четыре построены, отрендерены (EEVEE 640×400, 0,97 с — `99-raw/experiments/B/12-geonodes/geonodes_4_examples.png`)
и применены в меш [проверено: 12-geonodes]. Ниже — компактная версия с общей функцией входов.

```python
# Blender 5.2.2 — [проверено] разброс инстансов по поверхности со случайным масштабом
import bpy, bmesh
def gn(name, ins=(), geo_in=True):
    t = bpy.data.node_groups.new(name, "GeometryNodeTree")
    if geo_in:
        t.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm, st, dv in ins:
        t.interface.new_socket(name=nm, in_out="INPUT", socket_type=st).default_value = dv
    t.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    return t, t.nodes.new("NodeGroupInput"), t.nodes.new("NodeGroupOutput")
t, gi, go = gn("Scatter", [("Density", "NodeSocketFloat", 40.0), ("Seed", "NodeSocketInt", 3),
                           ("Scale Min", "NodeSocketFloat", 0.05), ("Scale Max", "NodeSocketFloat", 0.15)])
N = t.nodes
dist = N.new("GeometryNodeDistributePointsOnFaces")      # distribute_method 'RANDOM' | 'POISSON'
ico = N.new("GeometryNodeMeshIcoSphere"); ico.inputs["Subdivisions"].default_value = 1
inst = N.new("GeometryNodeInstanceOnPoints")
rnd = N.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT"   # режим до сокетов; выход один — «Value»
real = N.new("GeometryNodeRealizeInstances")
join = N.new("GeometryNodeJoinGeometry")
for a, b in [(gi.outputs["Geometry"], dist.inputs["Mesh"]), (gi.outputs["Density"], dist.inputs["Density"]),
             (gi.outputs["Seed"], dist.inputs["Seed"]), (dist.outputs["Points"], inst.inputs["Points"]),
             (ico.outputs["Mesh"], inst.inputs["Instance"]), (dist.outputs["Rotation"], inst.inputs["Rotation"]),
             (gi.outputs["Scale Min"], rnd.inputs["Min"]), (gi.outputs["Scale Max"], rnd.inputs["Max"]),
             (gi.outputs["Seed"], rnd.inputs["Seed"]), (rnd.outputs["Value"], inst.inputs["Scale"]),
             (inst.outputs["Instances"], real.inputs["Geometry"]), (gi.outputs["Geometry"], join.inputs["Geometry"]),
             (real.outputs["Geometry"], join.inputs["Geometry"]), (join.outputs["Geometry"], go.inputs["Geometry"])]:
    assert t.links.new(a, b).is_valid
me = bpy.data.meshes.new("Base"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("Scatter", me); bpy.context.scene.collection.objects.link(ob)
m = ob.modifiers.new("Scatter", "NODES"); m.node_group = t
dg = bpy.context.evaluated_depsgraph_get()
assert len(ob.evaluated_get(dg).data.vertices) == 1924     # 160 икосфер по 12 вершин + 4 вершины основы
```

```python
# Blender 5.2.2 — [проверено] сетка со смещением по шуму (рельеф)
import bpy
t = bpy.data.node_groups.new("NoiseGrid", "GeometryNodeTree")
for nm, st, dv in (("Size", "NodeSocketFloat", 2.0), ("Resolution", "NodeSocketInt", 80),
                   ("Height", "NodeSocketFloat", 0.4), ("Noise Scale", "NodeSocketFloat", 2.5)):
    t.interface.new_socket(name=nm, in_out="INPUT", socket_type=st).default_value = dv
t.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N = t.nodes; gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
grid = N.new("GeometryNodeMeshGrid")                     # Size X/Y, Vertices X/Y (число вершин, не делений)
pos = N.new("GeometryNodeInputPosition")
noise = N.new("ShaderNodeTexNoise")                      # шейдерная нода работает как поле в GN
sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5   # inputs[1] = «Value_001»
mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
comb = N.new("ShaderNodeCombineXYZ"); setp = N.new("GeometryNodeSetPosition"); smooth = N.new("GeometryNodeSetShadeSmooth")
for a, b in [(gi.outputs["Size"], grid.inputs["Size X"]), (gi.outputs["Size"], grid.inputs["Size Y"]),
             (gi.outputs["Resolution"], grid.inputs["Vertices X"]), (gi.outputs["Resolution"], grid.inputs["Vertices Y"]),
             (pos.outputs["Position"], noise.inputs["Vector"]), (gi.outputs["Noise Scale"], noise.inputs["Scale"]),
             (noise.outputs["Fac"], sub.inputs[0]), (sub.outputs["Value"], mul.inputs[0]),
             (gi.outputs["Height"], mul.inputs[1]), (mul.outputs["Value"], comb.inputs["Z"]),
             (grid.outputs["Mesh"], setp.inputs["Geometry"]), (comb.outputs["Vector"], setp.inputs["Offset"]),
             (setp.outputs["Geometry"], smooth.inputs["Geometry"]), (smooth.outputs["Geometry"], go.inputs["Geometry"])]:
    assert t.links.new(a, b).is_valid
ob = bpy.data.objects.new("Terrain", bpy.data.meshes.new("Terrain")); bpy.context.scene.collection.objects.link(ob)
ob.modifiers.new("NoiseGrid", "NODES").node_group = t
dg = bpy.context.evaluated_depsgraph_get()
me = ob.evaluated_get(dg).data
assert len(me.vertices) == 6400 and sum(len(p.vertices) - 2 for p in me.polygons) == 12482
```

```python
# Blender 5.2.2 — [проверено] кривая → трубка и кубы вдоль кривой (входы-меню)
import bpy
def tree(name):
    t = bpy.data.node_groups.new(name, "GeometryNodeTree")
    t.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    return t, t.nodes, t.nodes.new("NodeGroupOutput")
t1, N, go = tree("Tube")
spiral = N.new("GeometryNodeCurveSpiral")                # Resolution, Rotations, Start/End Radius, Height, Reverse
spiral.inputs["Rotations"].default_value = 4; spiral.inputs["Resolution"].default_value = 48
spiral.inputs["Start Radius"].default_value = spiral.inputs["End Radius"].default_value = 0.6
circ = N.new("GeometryNodeCurvePrimitiveCircle"); circ.inputs["Resolution"].default_value = 12
circ.inputs["Radius"].default_value = 0.08
c2m = N.new("GeometryNodeCurveToMesh"); c2m.inputs["Fill Caps"].default_value = True
t1.links.new(spiral.outputs["Curve"], c2m.inputs["Curve"]); t1.links.new(circ.outputs["Curve"], c2m.inputs["Profile Curve"])
t1.links.new(c2m.outputs["Mesh"], go.inputs["Geometry"])
t2, N, go = tree("AlongCurve")
bez = N.new("GeometryNodeCurvePrimitiveBezierSegment")
res = N.new("GeometryNodeResampleCurve"); res.inputs["Mode"].default_value = "Count"; res.inputs["Count"].default_value = 16
tan = N.new("GeometryNodeInputTangent"); align = N.new("FunctionNodeAlignRotationToVector"); align.axis = "X"
cube = N.new("GeometryNodeMeshCube"); cube.inputs["Size"].default_value = (0.15, 0.15, 0.15)
inst = N.new("GeometryNodeInstanceOnPoints"); real = N.new("GeometryNodeRealizeInstances")
for a, b in [(bez.outputs["Curve"], res.inputs["Curve"]), (res.outputs["Curve"], inst.inputs["Points"]),
             (tan.outputs["Tangent"], align.inputs["Vector"]), (align.outputs["Rotation"], inst.inputs["Rotation"]),
             (cube.outputs["Mesh"], inst.inputs["Instance"]), (inst.outputs["Instances"], real.inputs["Geometry"]),
             (real.outputs["Geometry"], go.inputs["Geometry"])]:
    assert t2.links.new(a, b).is_valid
counts = []
for t in (t1, t2):
    ob = bpy.data.objects.new(t.name, bpy.data.meshes.new(t.name)); bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new(t.name, "NODES").node_group = t
    counts.append(len(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices))
assert counts[1] == 16 * 8, counts                        # 16 кубов по 8 вершин
```

### 5.6 Применение для экспорта

```python
# Blender 5.2.2 — [проверено] применить GN (все модификаторы) в меш без оператора
import bpy
t = bpy.data.node_groups.new("Ico", "GeometryNodeTree")
t.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
ico = t.nodes.new("GeometryNodeMeshIcoSphere"); ico.inputs["Subdivisions"].default_value = 3
t.links.new(ico.outputs["Mesh"], t.nodes.new("NodeGroupOutput").inputs["Geometry"])
ob = bpy.data.objects.new("Ico", bpy.data.meshes.new("Ico")); bpy.context.scene.collection.objects.link(ob)
ob.modifiers.new("Ico", "NODES").node_group = t
dg = bpy.context.evaluated_depsgraph_get()
new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
ob.modifiers.clear(); ob.data = new_me
assert len(ob.data.vertices) == 162 and not ob.modifiers      # Subdivisions 1 → 12, 2 → 42, 3 → 162
```

Оператор `object.modifier_apply` тоже работает в фоне с `temp_override(object=ob)`; у экспортёра glTF есть
`export_apply=True` (модификаторы применяются при экспорте) и `export_gn_mesh` — подробности у агента E.

### 5.7 Что есть и чего нет в 5.2

- Нет: `GeometryNodeMeshTorus` (тор — Curve Circle + Curve to Mesh или bmesh), `GeometryNodeCurveFill` (правильно
  `GeometryNodeFillCurve`), `GeometryNodeTransformGeometry` (правильно `GeometryNodeTransform`) [проверено: 12].
- Новое в 5.2 [S35]: `GeometryNodeMeshBevel` (фаска как нода; 13 входов, 5 выходов — `bpy_probe.py nodes
  GeometryNodeTree bevel`), списки (Field to List, Get List Item, Sort/Filter List), Geometry Bundles, GN-модификаторы
  на пустышках, Merge Points / Cluster by Distance, Rename / Transfer Attributes, атрибуты FLOAT4, узлы 3D → экран.
- Compare и Random Value (5.2): identifiers изменены — один динамический сокет на роль (Compare: `A`, `B`; Random:
  входы `Min`, `Max`, `ID`, `Seed`, выход `Value`); `outputs[1]` → `IndexError: … index 1 out of range, size 1`,
  `inputs["A_INT"]` → KeyError [проверено: 03; S29]. GN Color node: значение — `.value`; `.color` — это цвет рамки
  ноды (Node.color, 3 числа) — `n.color = (1, 0, 0)` молча красит рамку [проверено: 03].

## 6. Композитор (5.x)

```python
# Blender 5.2.2 — [проверено] дерево композитора с Bloom для рендера в фоне
import bpy
scene = bpy.context.scene
tree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")        # 5.0+: отдельный ID, можно переиспользовать
scene.compositing_node_group = tree
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = tree.nodes.new("CompositorNodeRLayers")
glare = tree.nodes.new("CompositorNodeGlare")
glare.inputs["Type"].default_value = "Bloom"
glare.inputs["Threshold"].default_value = 1.0
glare.inputs["Strength"].default_value = 1.0
glare.inputs["Size"].default_value = 0.6
out = tree.nodes.new("NodeGroupOutput")                                # вместо удалённого CompositorNodeComposite
tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
tree.links.new(glare.outputs["Image"], out.inputs["Image"])
assert scene.render.use_compositing and all(l.is_valid for l in tree.links)
```

- `scene.node_tree` удалён (5.0) → `AttributeError: 'Scene' object has no attribute 'node_tree'`;
  `CompositorNodeComposite` удалён → `RuntimeError: … Node type CompositorNodeComposite undefined`; выход — Group
  Output, первый вход — Color [проверено: 03; S34]. `scene.use_nodes` устарел: включение/выключение —
  `scene.render.use_compositing` [проверено: 00-bpy-probe].
- Часть нод композитора заменена шейдерными: `CompositorNodeGamma` → `ShaderNodeGamma` в дереве композитора
  [проверено: 03]; Z Combine → Depth Combine; Alpha Over — входы Background/Foreground [S34].
- Имена проходов Render Layers (5.0): `'DiffCol'` → `'Diffuse Color'`, `'IndexMA'` → `'Material Index'`, `'Z'` →
  `'Depth'`; `rl.outputs["DiffCol"]` → KeyError [проверено: 03; S27].
- Bloom работает при фоновом рендере EEVEE: средний RGB кадра 0,49 → 0,62, свечение видно
  (`99-raw/experiments/B/13-render-compositor/compare_eevee_bloom_cycles.png`) [проверено: 13].

## Частые ошибки

| Что пишет нейросеть | 5.2.2 | Как надо |
|---|---|---|
| `mat.use_nodes = True; nodes = mat.node_tree.nodes; p = nodes["Principled BSDF"]` | DeprecationWarning; KeyError в локализованном UI | `next(n for n in nodes if n.type == "BSDF_PRINCIPLED")` |
| `p.inputs["Specular"]`, `["Transmission"]`, `["Clearcoat"]`, `["Sheen"]`, `["Emission"]` | `KeyError: … key "Specular" not found` | имена 4.0+ (§3.2) |
| `p.inputs[7].default_value = 0.2` («Roughness» по старой раскладке) | тихо: пишет в «Weight» | `p.inputs["Roughness"]` |
| `p.inputs["Base Color"].default_value = (1, 0, 0)` | `ValueError: … should contain 4 items, not 3` | `(1, 0, 0, 1)` |
| `nodes.new("Principled BSDF")` | `RuntimeError: Error: Node type Principled BSDF undefined` | `nodes.new("ShaderNodeBsdfPrincipled")` |
| `mix.inputs["A"]` до `mix.data_type = "RGBA"` | тихо: связь `is_valid = False` | режим до поиска |
| `mix.inputs["A_Color"]` | KeyError | `inputs["A"]` после режима или перебор по identifier |
| `links.new(emission.outputs[0], p.inputs["Base Color"])` | тихо: невалидная связь | эмиссия — `Emission Color` + `Emission Strength` |
| `nodes.clear()` без Material Output | тихо: нет вывода материала | создать `ShaderNodeOutputMaterial` и связать |
| `nodes.new("ShaderNodeTexMusgrave")`, `"ShaderNodeSeparateRGB"` | `RuntimeError: … undefined` | Noise с `noise_type`; `ShaderNodeSeparateColor` |
| `group.inputs.new("NodeSocketFloat", "Size")` | `AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'` | `group.interface.new_socket(...)` |
| `interface.new_socket(..., socket_type="NodeSocketFloatFactor")` | TypeError | `NodeSocketFloat` + `subtype = 'FACTOR'` |
| `mod["Socket_2"] = 5` / `mod["Input_2"] = 5` | `TypeError: … id properties not supported for this type` | `mod.properties.inputs.Socket_2.value = 5` + `ob.update_tag()` |
| `node.mode = 'COUNT'` (Resample Curve) | `AttributeError` | `node.inputs["Mode"].default_value = "Count"` |
| `rnd.outputs[1]`, `rnd.outputs["Value_001"]` | IndexError / KeyError | `rnd.outputs["Value"]` после `data_type` |
| `glare.glare_type = 'BLOOM'`; `scene.eevee.use_bloom = True` | AttributeError | композитор + `glare.inputs["Type"] = "Bloom"` |
| `scene.use_nodes = True; scene.node_tree.nodes[...]` | AttributeError (`node_tree` удалён) | `scene.compositing_node_group = …` |
| `ramp.color_ramp.elements.remove(...)` до пустого | RuntimeError на последнем | оставлять ≥ 1 элемент, менять позиции |

[проверено: 03, 11, 12, 15, 17, 19]. Полный каталог — `04-llm-failure-modes-and-patterns.md`.

## Чек-лист

- [ ] Сокеты новой/редкой ноды сверены через `bpy_probe.py node …` для этой версии?
- [ ] Ноды найдены по `type`/`bl_idname`, а не по имени?
- [ ] Режимы нод (`data_type`, `operation`, `blend_type`, `input_type`) заданы до поиска сокетов?
- [ ] Нигде нет доступа к сокету по индексу (кроме повторяющихся имён Math, где индекс проверен)?
- [ ] Все связи `is_valid` (`all(l.is_valid for l in tree.links)`)?
- [ ] Цвета — 4 компоненты, линейные; карты данных — `Non-Color`?
- [ ] В материале есть Material Output, подключённый к Surface?
- [ ] Процедурные ноды, если модель идёт в веб, запланированы к запеканию?
- [ ] Интерфейс групп создан через `tree.interface`, типы сокетов базовые, подтип через `subtype`?
- [ ] Входы модификатора GN — через `mod.properties.inputs`, после присвоения `ob.update_tag()`?
- [ ] Перед применением/экспортом инстансы реализованы (Realize Instances)?
- [ ] Композитор — `compositing_node_group` с Group Output; Bloom — через Glare?
- [ ] Дерево читаемо: колонки по глубине, рамки, метки?

## Открытые вопросы и противоречия

- **Поиск по identifier.** Заметки 4.0 («inputs[xxx] take socket identifiers and availability into account») и 4.1
  («use node.outputs[some_socket_identifier]») верны для большинства нод, но для Mix и Map Range исходник 5.2.2 этот
  поиск запрещает. Комментарий разработчиков обещает слить сокеты Mix/Map Range в один динамический — тогда
  `A_Color`-identifier исчезнут, а код «режим → имя» переживёт изменение.
- **`update_tag()` после входов GN** — вероятная недоработка 5.2 (новые RNA-свойства без update-колбэка); проверить в
  следующих выпусках 5.2.x. Ответ SE 2024 года вызывал `object.update_tag()` и для старого IDProperty-способа.
- **Заметка 5.0 про Sky Texture** («sun_direction, turbidity, ground_albedo inputs … were removed») не совпадает с RNA
  5.2.2: эти свойства есть и присваиваются (Preetham/Hosek-Wilkie). Возможно, речь о сокетах; не выяснено.
- **`handle_dynamic_sockets=True`** в `links.new` для виртуальных сокетов «__extend__» не проверялся.
- **Интерфейс MCP `describe_node_type`** (аддон протокола 7) не показывает доступность сокетов — для Mix он выдаёт
  все 10 входов подряд; агенту по MCP надо дополнительно смотреть `enabled` своим кодом [S38].

## Источники

- [S16] Blender Foundation. Change Log 5.1 → 5.2. API 5.2 — https://docs.blender.org/api/5.2/change_log.html — NodesModifier.properties, is_input_used, Node.panel_states; первичный.
- [S18] Blender Foundation. NodeTreeInterface. API 5.2 — https://docs.blender.org/api/5.2/bpy.types.NodeTreeInterface.html — new_socket, new_panel, move(to_position); первичный.
- [S20] Blender Foundation. Blender 3.6: Python API — https://developer.blender.org/docs/release_notes/3.6/python_api/ — connect_sockets, атрибуты mesh; первичный.
- [S21] Blender Foundation. Blender 4.0: Python API — https://developer.blender.org/docs/release_notes/4.0/python_api/ — Principled v2, interface, Glossy/Anisotropic; первичный.
- [S22] Blender Foundation. Blender 4.1: Python API — https://developer.blender.org/docs/release_notes/4.1/python_api/ — динамические сокеты, identifier; первичный.
- [S23] Blender Foundation. Blender 4.2 LTS: Python API — https://developer.blender.org/docs/release_notes/4.2/python_api/ — блум, blend_method, GN Color value; первичный.
- [S24] Blender Foundation. Blender 4.3: Python API — https://developer.blender.org/docs/release_notes/4.3/python_api/ — reroute socket_idname; первичный.
- [S26] Blender Foundation. Blender 4.5 LTS: Python API — https://developer.blender.org/docs/release_notes/4.5/python_api/ — Bump/Displacement distance, is_inactive; первичный.
- [S27] Blender Foundation. Blender 5.0: Python API — https://developer.blender.org/docs/release_notes/5.0/python_api/ — compositing_node_group, проходы, use_nodes; первичный.
- [S29] Blender Foundation. Blender 5.2 LTS: Python API — https://developer.blender.org/docs/release_notes/5.2/python_api/ — API входов GN-модификатора, Compare/Random Value; первичный.
- [S31] Blender Foundation. EEVEE migration (4.2) — https://developer.blender.org/docs/release_notes/4.2/eevee_migration/ — Bloom → Glare, Render Method; первичный.
- [S34] Blender Foundation. Blender 5.0: Compositor — https://developer.blender.org/docs/release_notes/5.0/compositor/ — Composite → Group Output, меню-входы, Gamma → ShaderNodeGamma; первичный.
- [S35] Blender Foundation. Blender 5.2 LTS: Geometry Nodes — https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/ — Mesh Bevel, Lists, Bundles, Empty; первичный.
- [S36] Blender Foundation. `source/blender/makesrna/intern/rna_nodetree.cc`, тег v5.2.2 (GitHub-зеркало blender/blender) — `find_socket_by_key`, `allow_identifier_lookup`; исходник, прочитан раздел.
- [S37] Blender Foundation. `source/blender/blenkernel/intern/node.cc`, тег v5.2.2 — `forward_compat::write_legacy_properties` (свойства → меню-входы); исходник, прочитан раздел.
- [S38] BlenderMCP, `blender_mcp.py` (протокол 7) — `describe_node_type`, `bpy_api_lookup`; исходник.
- [S40] Blender Stack Exchange, вопрос 247520 «How to get Geometry nodes modifier inputs and its type using python», ответы 2021-12-20 (принятый, score 9) и 2023-12-15 (score 8) — https://blender.stackexchange.com/q/247520 — `node_group.inputs` → `interface.items_tree`; проверено экспериментом 19.
- [S41] Blender Stack Exchange, вопрос 253001 «Changing Geometry Nodes Modifier Input with Python», ответ 2022-02-06 — https://blender.stackexchange.com/q/253001 — `mod["Input_6"] = obj`; в 5.2 TypeError.
- [S42] Blender Stack Exchange, вопрос 306355 «adding modifier input with python API in 4.0», ответ 2023-12-06 — https://blender.stackexchange.com/q/306355 — `interface.new_socket(... socket_type=...)`; работает.
- [S43] Blender Stack Exchange, вопрос 316696, ответы 2024-04-17 и 2024-05-29 — https://blender.stackexchange.com/q/316696 — ассет Smooth by Angle + `mod["Input_1"]`; в 5.2 не работает.
- [E] Заметки агента E `99-raw/notes/wave1/E-notes.md` (исходники io_scene_gltf2 5.2.40: распознаваемые связки материалов) и его файлы `../08-export-gltf/`.
