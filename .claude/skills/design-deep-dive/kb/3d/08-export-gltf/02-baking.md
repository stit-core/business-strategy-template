# Запекание для веба: процедуры, AO, свет, нормали — из Blender 5.2.2 в three.js r186

Волна 1 · агент E · 23.09.2026 · источников прочитано целиком: 9 (руководство Blender 5.2 «Render Baking», API `BakeSettings`,
release notes 5.0, спецификации glTF, исходник GLTFLoader, три разбора практиков на Codrops и Awwwards) · экспериментов: 4
(`99-raw/experiments/E/19-bake-procedural`, `20-bake-ao`, `21-bake-lighting`, `27-bake-extra`) + сквозные E/12, E/16, E/18 ·
версии: Blender 5.2.2 LTS (Cycles CPU, 20 потоков), glTF-Blender-IO 5.2.40, three.js r186, Chromium (Playwright), Intel Iris Xe.

Запекание (baking) — перенос того, что glTF не умеет хранить (процедурные текстуры, Bump, смешивание шейдеров, свет,
затенение, детали high-poly), в картинки или цвета вершин, которые экспорт переносит без потерь (`01-export-contract.md` §5.8).
Сжатие запечённых карт — `03-compression-textures-budgets.md` §3; проверка — `04-validation-pitfalls-presets.md`.

## Выжимка для агента

1. **Запекать всё, что экспортёр теряет**: процедуры, Color Ramp, Mix, Bump, Mix Shader, Subsurface, Coat Tint. Незапечённый процедурный материал в three — белый гладкий объект (ΔE 23.5), запечённый — ΔE 5.5 → §4 [проверено]
2. **Движок — Cycles** (`scene.render.engine = "CYCLES"`, `cycles.device = "CPU"`): EEVEE не запекает → §3.1 [проверено]
3. **Цель запекания — активная нода Image Texture** в каждом материале объекта; материал без активной ноды с картинкой пропускается молча → §3.2 [проверено] [документация: S1]
4. **Картинку создавать до bake** с нужным пространством: цвет — sRGB, всё остальное (нормали, шероховатость, AO, металличность, свет) — Non-Color → §3.5 [проверено]
5. **UV в фоне работают без temp_override**: `object.mode_set(mode="EDIT")` → `mesh.select_all` → `uv.smart_project` / `uv.lightmap_pack` / `uv.average_islands_scale` / `uv.pack_islands` → обратно в OBJECT → §2.1 [проверено]
6. **Отступ (margin) 16 px** на 1–2k; тип по умолчанию ADJACENT_FACES; UV-острова с `island_margin` 0.01–0.02 → §2.3 [проверено] [документация: S2]
7. **Плотность текселей** считать функцией `texel_density()` (px/м); после смены масштаба — `view_layer.update()`, иначе `matrix_world` старая → §2.3 [проверено]
8. **«Данные» материала — 1 сэмпл**: DIFFUSE с `pass_filter={"COLOR"}`, ROUGHNESS, NORMAL (без high-poly), EMIT не трассируют свет: 1024² за 0.15–0.25 с, 2048² за 0.75–1.27 с → §3.4 [проверено]
9. **DIFFUSE без `pass_filter={"COLOR"}`** запекает цвет вместе со светом сцены — для PBR-экспорта нужен только COLOR → §3.3 [проверено]
10. **Metallic**: типа bake METALLIC в 5.2 нет — источник Metallic временно подаётся в Emission и печётся EMIT (0.28 с на 1024²) → §8 [проверено]
11. **ORM упаковывать в одну картинку** (R = AO, G = roughness, B = metallic) и подключать через Separate Color + группу «glTF Material Output» → в glTF одна текстура на occlusion и metallicRoughness → §8 [проверено]
12. **AO — в текстуру, 1024², 16–64 spp (0.9–3.6 с)**; подключать только через «glTF Material Output».Occlusion; в Blender этот вход не рендерится → §5 [проверено]
13. **aoMap в three затемняет только непрямой свет** (окружение, Hemisphere/Ambient); при одном DirectionalLight без окружения AO не виден → §5.3 [проверено]
14. **AO в цвет вершин** — 0.05 с и без UV, но нужна плотная сетка; на редкой — угловатые пятна → §5.2 [проверено]
15. **Запечённый свет «как у Bruno Simon»**: DIFFUSE с `{"DIRECT","INDIRECT","COLOR"}` → картинка прямо в Surface (unlit) → `MeshBasicMaterial`; ΔE 0.73 к Cycles — лучшее совпадение Blender↔веб во всех опытах → §6.1 [проверено]
16. **LightMap вместо unlit** (PBR сохраняется): свет без COLOR во второй UV → `material.lightMap`, `texture.channel = 1`, `flipY = false`, **`lightMapIntensity = Math.PI`** (при 1 — в π раз темнее, ΔE 22) → §6.2 [проверено]
17. **Свет > 1 в 8-битной PNG обрезается** (11 % пикселей упёрлись в 254): хранить .hdr/.exr или масштабировать ×k и ставить интенсивность π/k → §6.3 [проверено]
18. **Ловушка 5.2.2**: `Image.save()` float-картинки с пространством «Linear Rec.709» пишет sRGB-кодированные значения даже в .hdr/.exr (0.5 → 0.735); ставить Non-Color или сохранять `image.save_render(path, scene=…)` → §3.5 [проверено]
19. **Денойз** запечённой карты — нода Denoise композитора в фоне (0.54 с на 1024²); в 5.x дерево — `scene.compositing_node_group`, выход — Group Output, `scene.node_tree` удалён → §6.4 [проверено] [документация: S3]
20. **Нормали high→low**: high и low выделены, low активный, `use_selected_to_active=True`, **`cage_extrusion` ≈ 2 % размера** (0.02 на объекте 2 м): ΔE 3.66 к high; с 0 — артефакты хуже, чем без карты (ΔE 7.31) → §7 [проверено]
21. **Время high→low** (63k → 4k треуг.): 1024² 4 spp — 0.36 с, 2048² — 1.17 с → §7 [проверено]
22. **COMBINED и свет — 16–64 spp**: 1024² 64 spp 4.2–4.5 с на простой диораме, COMBINED 16 spp 5.4 с; время ∝ пиксели × сэмплы × сложность света → §3.4 [проверено]
23. **Эмиссия**: EMIT пишет цвет × силу; в 8-бит всё > 1 обрезается — печь цвет при Strength 1, силу ставить в материал (`KHR_materials_emissive_strength`) → §3.3 [проверено]
24. **После запекания — новый простой материал** (Image → Principled), старый процедурный не экспортировать; запечённые картинки без файла экспортёр пишет PNG → §4.2 [проверено]
25. **Вес запечённого**: 1024² PNG шумной карты ≈ 0.8–1 МБ, 3 карты 2k — 6.2 МБ GLB; в GPU 1024² = 5.3 МБ, 2048² = 21.3 МБ (RGBA8 + мипмапы) → сжимать (WebP/KTX2, `03` §3) → §10 [проверено]
26. **GN → меш**: `bpy.ops.object.modifier_apply(modifier=…)` в фоне работает (активный объект, OBJECT mode), либо `export_apply=True` при экспорте → §9 [проверено]

## 1. Что запекать и куда это попадает

| что в Blender | проход bake | картинка | куда в glTF | как в three r186 | опыт |
|---|---|---|---|---|---|
| процедурный цвет (Noise, Ramp, Mix) | DIFFUSE, `pass_filter={"COLOR"}`, 1 spp | sRGB | `baseColorTexture` | `map` | E/19 |
| процедурная шероховатость | ROUGHNESS, 1 spp | Non-Color | `metallicRoughnessTexture` (G) | `roughnessMap` | E/19, E/27 |
| процедурная металличность | EMIT-трюк, 1 spp | Non-Color | `metallicRoughnessTexture` (B) | `metalnessMap` | E/27 |
| Bump, процедурный рельеф | NORMAL (TANGENT), 1 spp | Non-Color | `normalTexture` | `normalMap` | E/19 |
| детали high-poly | NORMAL + `use_selected_to_active`, 4 spp | Non-Color | `normalTexture` | `normalMap` | E/27 |
| контактные тени | AO, 16–64 spp | Non-Color | `occlusionTexture` (R) через группу | `aoMap` (только непрямой свет) | E/20 |
| контактные тени без UV | AO → VERTEX_COLORS | цвет вершин | `COLOR_0` × base color | `vertexColors` | E/20 |
| свет целиком (стиль «запечённого мира») | DIFFUSE `{"DIRECT","INDIRECT","COLOR"}` или COMBINED, 64 spp | sRGB | unlit `baseColorTexture` | `MeshBasicMaterial.map` | E/21 |
| только освещённость | DIFFUSE `{"DIRECT","INDIRECT"}`, 64 spp | .hdr (Non-Color) или PNG | нет слота — отдельный файл | `lightMap`, `channel = 1`, интенсивность π | E/21 |
| свечение | EMIT (Strength 1) | sRGB | `emissiveTexture` + strength | `emissiveMap`, `emissiveIntensity` | E/27 |
| GN / модификаторы | не bake — apply | — | меш | `Mesh` | E/08, E/27 |

Когда не запекать:
- Материал уже в разрешённом наборе нод (`01` §5.2) — запекание только добавит вес.
- Объект двигается относительно света или свет меняется на странице — запечённые тени и свет «прилипают» к объекту;
  для таких объектов — PBR + свет кодом, AO допустим [практика] [S9].
- Сцена большая, а текстура одна: 4096² на весь мир размывается; практики делят сцену на наборы текстур по зонам [S9].

## 2. UV для запекания

### 2.1. Операторы UV в фоне (без окна)

Проверено в фоновом Blender 5.2.2 без `temp_override`: активный объект, режим EDIT, всё выделено
[проверено].

| оператор | где проверен | время |
|---|---|---|
| `bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)` | икосфера 2562 вершины; Suzanne 3936 треуг. | < 0.01 с; с усреднением и упаковкой 0.84 с |
| `bpy.ops.uv.lightmap_pack(PREF_CONTEXT="ALL_FACES", PREF_PACK_IN_ONE=True, PREF_BOX_DIV=12, PREF_MARGIN_DIV=0.2)` | диорама 96 вершин | < 0.01 с |
| `bpy.ops.uv.average_islands_scale()` | Suzanne | входит в 0.84 с |
| `bpy.ops.uv.pack_islands(margin=0.02)` | Suzanne | входит в 0.84 с |
| `bpy.ops.object.modifier_apply(modifier="GN")` (OBJECT mode) | GN 100 икосфер + Realize | 0.004 с |

Smart UV заполнил 59 % квадрата на гальке (E/19) и 50 % на Suzanne (E/27); Lightmap Pack — все грани в отдельных
прямоугольниках, удобен для второго UV под свет [проверено].

### 2.2. Код: развёртка в фоне

```python
# Blender 5.2.2 — [проверено]
import bpy, math

def smart_uv(ob, angle_deg=66.0, margin=0.02, uv_name="UVMap"):
    """Smart UV Project в фоне: EDIT-режим, без temp_override."""
    if uv_name not in ob.data.uv_layers:
        ob.data.uv_layers.new(name=uv_name)
    ob.data.uv_layers.active = ob.data.uv_layers[uv_name]
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_deg), island_margin=margin)
    bpy.ops.uv.average_islands_scale()                 # одинаковая плотность текселей у островов
    bpy.ops.uv.pack_islands(margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")
```

Второй UV-слой под свет (становится `TEXCOORD_1` → `uv1` в three):

```python
# Blender 5.2.2 — [проверено]
def lightmap_uv(ob, name="LightUV"):
    uv = ob.data.uv_layers.new(name=name); ob.data.uv_layers.active = uv
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.lightmap_pack(PREF_CONTEXT="ALL_FACES", PREF_PACK_IN_ONE=True, PREF_BOX_DIV=12, PREF_MARGIN_DIV=0.2)
    bpy.ops.object.mode_set(mode="OBJECT")
    return uv
```

- `uv_layers.new()` делает новый слой активным для редактирования, но экспорт текстур берёт слой по ноде UV Map или по
  `active_render` (`01` §4.3). Порядок слоёв = номер `TEXCOORD_n`: UV0 — материалы, UV1 — свет/AO
  [проверено].
- Запекание пишет в **активный** UV-слой (`uv_layers.active`), если в материале нет ноды UV Map перед целевой Image Texture
  [проверено].
- Острова, наложенные друг на друга (зеркальные половины, повторяющиеся детали), при запекании перетирают друг друга —
  для запекания развёртка без наложений (Smart UV, Lightmap Pack) [документация: S1].

### 2.3. Отступы и плотность текселей

- `margin` (px) продлевает края островов после запекания, чтобы мипмапы и фильтрация не подтягивали фон на швах; по
  умолчанию 16, тип `ADJACENT_FACES` [S2]. В опытах: 16 px для 1–2k карт материала, 4–8 px для карт света 1024²
  [проверено]. Для 512² и меньше — 4–8 px; 16 px на 256² съедают острова [практика].
- `island_margin` UV-операторов — доля квадрата (0.02 = 2 %); вместе с `margin` bake задаёт зазор между островами.
- Плотность текселей (texel density) — пикселей текстуры на метр поверхности. Одинаковая плотность у соседних объектов
  делает резкость ровной; ориентиры для веба — 256–512 px/м для крупных поверхностей и 512–1024 px/м для hero-объекта
  на первом экране [практика; числа — ориентир, не замер восприятия].

```python
# Blender 5.2.2 — [проверено] (плоскость 2×2 м, 1024² → 512 px/м; scale ×2 → 256)
import bpy, math

def texel_density(ob, size, uv_name=None):
    """Текселей на метр для текстуры size×size: sqrt(доля площади UV · size² / площадь поверхности в мире)."""
    bpy.context.view_layer.update()                       # matrix_world обновляется только после update
    me = ob.data
    uv = me.uv_layers[uv_name] if uv_name else me.uv_layers.active
    mw = ob.matrix_world
    area_world = 0.0
    area_uv = 0.0
    for poly in me.polygons:
        co = [mw @ me.vertices[vi].co for vi in poly.vertices]
        for i in range(1, len(co) - 1):                       # веер треугольников
            area_world += (co[i] - co[0]).cross(co[i + 1] - co[0]).length / 2
        pts = [uv.data[li].uv for li in poly.loop_indices]
        area_uv += abs(sum(pts[i].x * pts[i - 1].y - pts[i - 1].x * pts[i].y for i in range(len(pts)))) / 2
    return math.sqrt(area_uv * size * size / area_world)
```

Замеры: Suzanne (≈ 2 м) с Smart UV, 1024² → 445 px/м при 50 % занятой площади UV; шар r = 0.6 м → 348 px/м
[проверено]. Без `view_layer.update()` после `ob.scale = …` функция вернула бы старое значение
(512 вместо 256) — классическая ловушка фонового скрипта [проверено].

## 3. Механика bake в Blender 5.2 из Python

### 3.1. Что должно быть готово перед `bpy.ops.object.bake`

1. `scene.render.engine = "CYCLES"`, `scene.cycles.device = "CPU"` (GPU на этой машине не используется), `scene.cycles.samples`
   по типу прохода (§3.4) [проверено].
2. Объект активен и выделен; для high→low — оба выделены, low активный (§7).
3. У меша есть UV без наложений; нужный слой активен (или нода UV Map перед целевой картинкой).
4. **В каждом материале** объекта — нода Image Texture с картинкой, выбранная и активная (`nt.nodes.active = node`);
   материал без неё пропускается («If a material does not contain an active and selected image texture node, nothing will be
   baked for this material») [S1] [проверено: 99-raw/experiments/E/21-bake-lighting — у диорамы 3 материала, нода добавлена в каждый].
5. Для запекания в цвета вершин — `scene.render.bake.target = "VERTEX_COLORS"` и активный цветовой атрибут
   (`me.color_attributes.active_color`) [проверено].
6. После bake — вернуть `target = "IMAGE_TEXTURES"`, удалить временные ноды, сохранить картинки (они живут только в памяти:
   «Baking map saved to internal image, save it externally or pack it») [проверено].

### 3.2. Код: картинка и цель запекания

```python
# Blender 5.2.2 — [проверено]
import bpy

def new_bake_image(name, size, colorspace="Non-Color", float_buffer=False):
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=float_buffer)
    img.colorspace_settings.name = colorspace          # "sRGB" — цвет; "Non-Color" — данные (нормали, шероховатость, AO, свет)
    return img


def set_bake_target(mat, img, uv_name=None):
    """Нода Image Texture с картинкой становится АКТИВНОЙ — bake пишет в неё. Возвращает ноду (удалить после bake)."""
    nt = mat.node_tree
    node = nt.nodes.new("ShaderNodeTexImage"); node.image = img
    if uv_name:
        uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = uv_name
        nt.links.new(uvn.outputs["UV"], node.inputs["Vector"])
    for n in nt.nodes:
        n.select = False
    node.select = True
    nt.nodes.active = node
    return node

# node = set_bake_target(mat, img)
# bpy.ops.object.bake(type="ROUGHNESS", margin=16, use_clear=True)
# mat.node_tree.nodes.remove(node)
```

Временная нода не подключена ни к чему — на шейдер она не влияет, но если её не удалить, экспортёр может принять её за
текстуру (предупреждение «More than one shader node tex image used») — удалять после bake.

### 3.3. Типы запекания в 5.2.2

`bpy.ops.object.bake(type=…)` принимает 12 значений: COMBINED, AO, SHADOW, POSITION, NORMAL, UV, ROUGHNESS, EMIT,
ENVIRONMENT, DIFFUSE, GLOSSY, TRANSMISSION; типа METALLIC нет [проверено] [S1].

| тип | `pass_filter` / параметры | что получается | для веба |
|---|---|---|---|
| DIFFUSE | `{"COLOR"}` | альбедо без света | base color из процедуры |
| DIFFUSE | `{"DIRECT","INDIRECT","COLOR"}` | цвет со светом (диффузная часть) | запечённый свет, unlit |
| DIFFUSE | `{"DIRECT","INDIRECT"}` | только освещённость (серо-цветная) | lightMap |
| ROUGHNESS | — | шероховатость | G-канал ORM |
| NORMAL | `normal_space="TANGENT"` | касательная карта нормалей (Bump, процедуры) | normalTexture |
| NORMAL | + `use_selected_to_active`, `cage_extrusion` | детали high-poly на low-poly | normalTexture |
| AO | — (сэмплы) | затенение по геометрии, свет сцены игнорируется | occlusionTexture |
| EMIT | — | цвет × сила эмиссии; удобно для трюков (металличность, маски) | emissiveTexture, B-канал ORM |
| COMBINED | фильтры `use_pass_*` | всё: материалы, свет, эмиссия (кроме бликов по умолчанию руководства) | запечённый свет |
| POSITION, UV, SHADOW, ENVIRONMENT, GLOSSY, TRANSMISSION | — | служебные | в опытах не использовались |

- «Если выбран только Color — получится цвет прохода, не зависящий от сэмплов; без Color — прямой/непрямой свет в оттенках
  серого; Color + Direct/Indirect — окрашенный свет» [S1]. Проверено на DIFFUSE: `{"COLOR"}` для PBR-экспорта, иначе в
  base color попадает свет сцены [проверено].
- EMIT при Emission Color (1, 0.3, 0.05) × Strength 2: в 8-битной sRGB-картинке R обрезан до 1.0 (линейное 2.0), G = 0.796
  (= sRGB от 0.6), B = 0.349 (= sRGB от 0.1) — значения > 1 теряются [проверено].
- `bpy.ops.object.bake_image` в 5.2 тоже существует («Bake image textures of selected objects»), но это запекание Multires,
  а не Cycles; модель по памяти путает их [проверено] [S1].

### 3.4. Время на этом CPU (Cycles CPU, 20 потоков)

| проход | 1024² | 2048² | сэмплы | объект | опыт |
|---|---|---|---|---|---|
| DIFFUSE `{"COLOR"}` | 0.15 с | 0.75 с (16 spp: 4.31 с) | 1 | галька 2562 вершины, процедуры | E/19 |
| ROUGHNESS | 0.15–0.25 с | 0.98 с (16 spp: 4.81 с) | 1 | то же / шар | E/19, E/27 |
| NORMAL (Bump из процедуры) | 0.16 с | 1.27 с (16 spp: 5.00 с) | 1 | галька | E/19 |
| NORMAL high→low | 0.36 с | 1.17 с | 4 | 63k → 4k треуг. | E/27 |
| METALLIC (EMIT-трюк) | 0.28 с | — | 1 | шар 64×32 | E/27 |
| EMIT | 1.39 с | — | 16 | шар | E/27 |
| AO | 0.92 с (16 spp), 1.42 с (16 spp, шар+пол), 3.57 с (64 spp) | — | 16–64 | диорама 2976 вершин | E/20, E/27 |
| AO → цвета вершин | 0.05 с | — | 64 | диорама | E/20 |
| DIFFUSE свет целиком | 4.24 с | — | 64 | диорама 96 вершин, солнце + небо | E/21 |
| DIFFUSE только свет | 4.53 с | — | 64 | то же | E/21 |
| COMBINED | 5.4 с | — | 16 | шар + пол + солнце | E/27 |
| денойз (композитор) | 0.54 с | — | — | карта света 1024² | E/21 |

[проверено]. Правило: проходы «данных»
(COLOR, ROUGHNESS, NORMAL без high-poly, EMIT, METALLIC) — 1 сэмпл, 16 дают только сглаживание внутри текселя ценой ×5 времени;
свет, AO, COMBINED — 16–64 сэмпла + денойз. Время растёт примерно как пиксели × сэмплы: 2048² при тех же сэмплах в 4–8 раз
дольше 1024².

### 3.5. Сохранение картинок и цветовые пространства

- Байтовая картинка (`float_buffer=False`) с sRGB — для цвета; с Non-Color — для данных; PNG, `image.filepath_raw = path;
  image.file_format = "PNG"; image.save()` [проверено].
- Float-картинка (`float_buffer=True`) нужна для света > 1 и AO без полос. **Ловушка Blender 5.2.2**: `Image.save()` для float-картинки
  с пространством «Linear Rec.709» пишет sRGB-кодированные значения в .hdr, .exr и .png (линейные 0.5 → 0.735 в файле). С
  «Non-Color» или через `image.save_render(filepath, scene=bpy.context.scene)` значения линейные
  [проверено]. Практики тоже пекут в 32-bit float EXR и потом переводят в PNG композитором [S9].
- Цветовое пространство картинки в glTF не пишется (`01` §5.4): карта нормалей, записанная в sRGB-картинку, в Blender
  выглядит неправильно, а в three — правильно (или наоборот) — ставить пространство до запекания.
- Картинка без файла (только в памяти) при экспорте уходит PNG; картинка, сохранённая в файл, — теми же байтами
  [проверено].

## 4. Процедурный материал → текстуры → простой Principled

### 4.1. Сквозной опыт (E/19)

Галька (икосфера 4, 2562 вершины, сплюснута) с материалом: Noise → Color Ramp → Base Color; Voronoi → Map Range → Roughness;
Noise → Bump → Normal. Экспорт «как есть» даёт в three белый гладкий шар (ΔE 23.5 к рендеру Blender); после запекания трёх
карт 1024² — ΔE 5.5, IoU 0.997 (остаток — блики на рельефе) [проверено].

| разрешение, сэмплы | DIFFUSE color | ROUGHNESS | NORMAL | экспорт | GLB (PNG) |
|---|---|---|---|---|---|
| 1024², 1 spp | 0.15 с | 0.15 с | 0.16 с | 0.08 с | 2.13 МБ |
| 2048², 1 spp | 0.75 с | 0.98 с | 1.27 с | 0.61 с | 6.16 МБ |
| 2048², 16 spp | 4.31 с | 4.81 с | 5.00 с | 0.23 с | 6.10 МБ |

### 4.2. Код: запечь три карты и собрать простой материал

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/E/26-doc-snippets/run_md.py (этот блок как есть), шаги — E/19-bake-procedural]
import bpy, os

def bake_pbr_maps(ob, out_dir, size=1024):
    """Процедурный материал ob → base (sRGB), roughness, normal (Non-Color) PNG. UV уже есть (§2.2)."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 1   # «данные» — 1 сэмпл
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    mat = ob.active_material
    maps = {"base": new_bake_image("baked_base", size, "sRGB"),
            "rough": new_bake_image("baked_rough", size, "Non-Color"),
            "normal": new_bake_image("baked_normal", size, "Non-Color")}
    jobs = [("base", "DIFFUSE", {"pass_filter": {"COLOR"}}),            # только альбедо, без света сцены
            ("rough", "ROUGHNESS", {}),
            ("normal", "NORMAL", {"normal_space": "TANGENT"})]
    for key, bake_type, kw in jobs:
        node = set_bake_target(mat, maps[key])
        res = bpy.ops.object.bake(type=bake_type, margin=16, use_clear=True, **kw)
        mat.node_tree.nodes.remove(node)
        if "FINISHED" not in res:
            raise RuntimeError(f"bake {bake_type}: {res}")              # без целевой ноды bake возвращает CANCELLED
        img = maps[key]
        img.filepath_raw = os.path.join(out_dir, f"{ob.name}_{key}_{size}.png"); img.file_format = "PNG"; img.save()
    return maps


def baked_material(name, maps):
    """Простой Principled из запечённых карт — переживает экспорт glTF без потерь."""
    m = bpy.data.materials.new(name); nt = m.node_tree
    p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tb = nt.nodes.new("ShaderNodeTexImage"); tb.image = maps["base"]; nt.links.new(tb.outputs["Color"], p.inputs["Base Color"])
    tr = nt.nodes.new("ShaderNodeTexImage"); tr.image = maps["rough"]; nt.links.new(tr.outputs["Color"], p.inputs["Roughness"])
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = maps["normal"]
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    return m

# maps = bake_pbr_maps(ob, "/abs/tex"); ob.data.materials[0] = baked_material("Baked", maps); затем экспорт (01 §3.2)
```

Функция собрана из шагов E/19 (запекание, сохранение, новый материал) и функций E/27 (§3.2); проверка результата `bake()` —
из E/25c. Все блоки кода этого файла исполнены в напечатанном виде скриптом `99-raw/experiments/E/26-doc-snippets/run_md.py`. Процедурный материал после этого не нужен: экспортируется только `Baked`.

## 5. Ambient Occlusion

### 5.1. В текстуру (occlusionTexture)

Диорама (плита 3×3 м, три ящика, цилиндр; 2976 вершин, 5932 треуг.), материал Clay [проверено]:

| вариант | время | GLB | three (HDRI studio_small_09, без тонмаппинга) |
|---|---|---|---|
| без AO | — | 166 КБ | стыки плоские, объекты «висят», L* 80–83 |
| AO 1024², 16 spp | 0.92 с | — | — |
| AO 1024², 64 spp → `occlusionTexture` | 3.57 с | 634 КБ (PNG) | мягкие контактные тени, L* 71–74 |
| AO → цвета вершин (64 spp) → `COLOR_0` | **0.05 с** | 214 КБ | те же тени, но угловатые пятна по треугольникам |

```python
# Blender 5.2.2 — [проверено]; gltf_output_node() — 01 §5.2, set_bake_target — §3.2
def bake_ao_to_occlusion(ob, mat, out_path, size=1024, samples=64):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples
    img = new_bake_image("ao", size, "Non-Color")
    node = set_bake_target(mat, img)
    bpy.ops.object.bake(type="AO", margin=8, use_clear=True)
    mat.node_tree.nodes.remove(node)
    img.filepath_raw = out_path; img.file_format = "PNG"; img.save()
    nt = mat.node_tree                                      # AO → «glTF Material Output».Occlusion (R-канал)
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tex.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Red"], gltf_output_node(mat).inputs["Occlusion"])
    return img
```

### 5.2. В цвета вершин

```python
# Blender 5.2.2 — [проверено] (0.05 с на 2976 вершин; экспорт с export_all_vertex_colors=False)
def bake_ao_to_vertices(ob, mat, base_rgb=(0.8, 0.78, 0.74), samples=64):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.samples = samples
    ca = ob.data.color_attributes.new("AO", "BYTE_COLOR", "POINT")
    ob.data.color_attributes.active_color = ca
    sc.render.bake.target = "VERTEX_COLORS"
    bpy.ops.object.bake(type="AO")
    sc.render.bake.target = "IMAGE_TEXTURES"
    nt = mat.node_tree                                      # AO × цвет → Base Color (→ COLOR_0 × baseColorFactor)
    p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "AO"
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
    next(s for s in mx.inputs if s.identifier == "Factor_Float").default_value = 1.0
    nt.links.new(vc.outputs["Color"], next(s for s in mx.inputs if s.identifier == "A_Color"))
    next(s for s in mx.inputs if s.identifier == "B_Color").default_value = (*base_rgb, 1)
    nt.links.new(next(s for s in mx.outputs if s.identifier == "Result_Color"), p.inputs["Base Color"])
```

Сокеты ноды Mix искать по `identifier` перебором: `inputs["A_Color"]` по identifier не работает (KeyError), имена «A»/«B»
повторяются для разных типов данных [проверено] [S8].

### 5.3. Как AO работает в three r186

- `occlusionTexture` → `aoMap` (R-канал, `aoMapIntensity = strength`) на том же UV, что указан в `texCoord` [S5].
- aoMap гасит только **непрямой** свет: окружение (`scene.environment`), HemisphereLight, AmbientLight. От DirectionalLight и
  PointLight тени AO не появляются — при сцене «одно солнце без окружения» AO не виден [проверено].
- AO в цветах вершин — это множитель базового цвета: действует на весь свет, включая прямой (физически неверно, но для
  стилизованного low-poly выглядит естественно).
- Blender не рендерит вход Occlusion группы: сравнивать AO только в three [проверено].

## 6. Запечённый свет

Сцена E/21: диорама (плита 3×3 м, 3 ящика, цилиндр; 96 вершин), 3 матовых материала (Roughness 1, Specular IOR Level 0),
солнце 3 Вт/м² (угол 3°) + мир (0.25, 0.35, 0.55) × 0.6. Второй UV «LightUV» — Lightmap Pack (§2.2). Эталон — Cycles 64 spp
[проверено].

### 6.1. Путь A: свет целиком → unlit (стиль «запечённого мира»)

DIFFUSE с `{"DIRECT","INDIRECT","COLOR"}` (1024², 64 spp: 4.24 с) → одна картинка на всю диораму → Image Texture (UV Map
«LightUV») прямо в Surface → `KHR_materials_unlit` → в three `MeshBasicMaterial` с `map` на `channel 1`.
Результат: **ΔE2000 0.73 к Cycles, SSIM 0.95** — лучшее совпадение Blender↔веб во всех экспериментах E; GLB 950 КБ (PNG 1024²),
после денойза 795 КБ [проверено].

```python
# Blender 5.2.2 — [проверено] (bake_to — запекание во все материалы объекта)
import bpy

def bake_to(ob, mats, image, pass_filter, uvname):
    nodes = []
    for m in mats:                                          # цель — в КАЖДОМ материале, иначе его грани не запекутся
        nt = m.node_tree
        uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = uvname
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = image; nt.links.new(uvn.outputs["UV"], n.inputs["Vector"])
        for x in nt.nodes:
            x.select = False
        n.select = True; nt.nodes.active = n; nodes.append((nt, n, uvn))
    ob.data.uv_layers.active = ob.data.uv_layers[uvname]     # запекание пишет в активный UV-слой
    bpy.ops.object.bake(type="DIFFUSE", pass_filter=pass_filter, margin=4, use_clear=True)
    for nt, n, uvn in nodes:
        nt.nodes.remove(n); nt.nodes.remove(uvn)


def unlit_baked_material(name, image, uvname="LightUV"):
    m = bpy.data.materials.new(name); nt = m.node_tree
    nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = uvname
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = image; nt.links.new(uvn.outputs["UV"], t.inputs["Vector"])
    nt.links.new(t.outputs["Color"], out.inputs["Surface"])   # → KHR_materials_unlit
    return m

# sc.render.engine = "CYCLES"; sc.cycles.samples = 64
# img = bpy.data.images.new("baked_full", 1024, 1024); img.colorspace_settings.name = "sRGB"
# bake_to(ob, list(ob.data.materials), img, {"DIRECT", "INDIRECT", "COLOR"}, "LightUV")
# ob.data.materials.clear(); ob.data.materials.append(unlit_baked_material("Baked", img)); экспорт
```

На странице ничего настраивать не нужно: загрузчик сам создаёт `MeshBasicMaterial` и ставит `map.channel = 1` по `texCoord`
[S5]. Свет и тонмаппинг страницы на unlit не влияют (для совпадения — `renderer.toneMapping = NoToneMapping` или тот же
тонмаппинг, что в Blender при запекании; запечённая картинка уже в sRGB).

### 6.2. Путь B: только освещённость → lightMap (PBR остаётся)

DIFFUSE с `{"DIRECT","INDIRECT"}` (без COLOR) → отдельный файл карты; материалы экспортируются как PBR, в GLB уходят
`TEXCOORD_0` и `TEXCOORD_1` («LightUV»). В glTF нет слота lightMap — карта назначается кодом.

| карта освещения | `lightMapIntensity` | ΔE2000 к Cycles | L* three / Cycles |
|---|---|---|---|
| PNG 8 бит (обрезка: 11 % пикселей ≥ 254, линейный максимум 1.34) | 1 | 22.3 | 47 / 76 (в π раз темнее) |
| та же PNG | **π** | 0.89 | 75.9 / 76.1 |
| PNG с линейными значениями ×0.25 (sRGB-кодирование numpy) | **4π** | 0.77 | 75.9 / 76.1 |
| Radiance .hdr (`HDRLoader`, `LinearSRGBColorSpace`, `flipY=false`) | **π** | **0.74** | 76.0 / 76.1 |
| .hdr с `flipY=true` | π | 23.2 | карта перевёрнута |

[проверено]. Почему π: шейдер three r155+ делит освещённость на π в BRDF Ламберта, а
DIFFUSE-проход Blender хранит освещённость без этого деления.

```js
// three r186 — [проверено]
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {HDRLoader} from 'three/addons/loaders/HDRLoader.js';

const gltf = await new GLTFLoader().loadAsync('pbr_lightmap.glb');   // PBR-материалы + TEXCOORD_1
scene.add(gltf.scene);
let lm;
if (useHdr) {                                        // .hdr: без обрезки света > 1
  lm = await new HDRLoader().loadAsync('light_1024.hdr');
  lm.colorSpace = THREE.LinearSRGBColorSpace;
} else {                                             // PNG: свет > 1 обрезан, для ×0.25-карты интенсивность 4π
  lm = await new THREE.TextureLoader().loadAsync('light_1024.png');
  lm.colorSpace = THREE.SRGBColorSpace;
}
lm.flipY = false;                                    // UV glTF, как у GLTFLoader (TextureLoader по умолчанию flipY = true)
lm.channel = 1;                                      // TEXCOORD_1 = второй UV-слой Blender («LightUV»)
gltf.scene.traverse(o => {
  if (!o.isMesh) return;
  for (const m of [o.material].flat()) { m.lightMap = lm; m.lightMapIntensity = Math.PI; m.needsUpdate = true; }
});
```

В опыте сцена рисовалась без окружения и ламп: lightMap уже содержит и прямой, и непрямой свет. Если добавить на странице
ещё и `scene.environment` или лампы, свет посчитается дважды — оставлять только блики (например, environment с малой
`envMapIntensity`) [практика; не проверено].

### 6.3. Формат карты света

- 8-битная PNG обрезает всё > 1: у диорамы 11 % пикселей упёрлись в потолок (линейный максимум 1.34)
  [проверено].
- Варианты без обрезки: Radiance .hdr (float, HDRLoader; 1024² — несколько МБ) или масштаб ×k в 8-бит (×0.25 → интенсивность
  4π, ΔE 0.77) — второе в разы легче и сжимается WebP/KTX2 [проверено].
- Запекать в float-картинку с **Non-Color** — ловушка §3.5; код из опыта:

```python
# Blender 5.2.2 — [проверено]
import numpy as np
img = bpy.data.images.new("light_float", 1024, 1024, float_buffer=True)
img.colorspace_settings.name = "Non-Color"      # иначе Image.save() пишет sRGB-кодированные значения даже в .hdr/.exr (5.2.2)
bake_to(ob, mats, img, {"DIRECT", "INDIRECT"}, "LightUV")
img.filepath_raw = "/abs/tex/light_1024.hdr"; img.file_format = "HDR"; img.save()
px = np.empty(1024 * 1024 * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(-1, 4)
s = px.copy(); s[:, :3] = np.clip(s[:, :3] * 0.25, 0, 1)                       # ×0.25 → интенсивность 4π на странице
s[:, :3] = np.where(s[:, :3] <= 0.0031308, s[:, :3] * 12.92, 1.055 * np.power(s[:, :3], 1 / 2.4) - 0.055)
s[:, 3] = 1
out = bpy.data.images.new("light_q", 1024, 1024); out.colorspace_settings.name = "sRGB"
out.pixels.foreach_set(s.ravel()); out.filepath_raw = "/abs/tex/light_1024_x0.25.png"; out.file_format = "PNG"; out.save()
```

### 6.4. Денойз запечённой карты в фоне

Запечённый свет с 64 spp шумит; нода Denoise (OIDN) композитора убирает шум за 0.54 с на 1024² (PNG 1032 → 868 КБ, шум хуже
жмётся; ΔE к Cycles 0.68 вместо 0.73) [проверено]. В 5.0 композитор перешёл на
node groups: `scene.node_tree` удалён (`AttributeError`), нода Composite удалена (`RuntimeError: Node type
CompositorNodeComposite undefined`) — выход дерева — Group Output [S3] [проверено].

```python
# Blender 5.2.2 — [проверено] (0.54 с на 1024²)
import bpy

def denoise(image, out_path):
    """Денойз картинки нодой Denoise (OIDN): рендер «пустой» сцены EEVEE с деревом Image → Denoise → Group Output."""
    sc = bpy.context.scene
    old_engine = sc.render.engine
    ng = bpy.data.node_groups.new("DenoiseBake", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    im = ng.nodes.new("CompositorNodeImage"); im.image = image
    dn = ng.nodes.new("CompositorNodeDenoise")
    go = ng.nodes.new("NodeGroupOutput")
    ng.links.new(im.outputs["Image"], dn.inputs["Image"]); ng.links.new(dn.outputs["Image"], go.inputs[0])
    sc.compositing_node_group = ng                      # 5.x: вместо scene.node_tree
    sc.render.use_compositing = True
    sc.render.resolution_x = image.size[0]; sc.render.resolution_y = image.size[1]; sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"
    vs = sc.view_settings; old_vt = vs.view_transform; vs.view_transform = "Standard"; vs.look = "None"
    sc.render.engine = "BLENDER_EEVEE"
    hidden = [o for o in sc.objects if not o.hide_render]
    for o in hidden:
        o.hide_render = True                            # рендерится пустая сцена, композитор берёт картинку
    sc.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    sc.render.engine = old_engine; vs.view_transform = old_vt; sc.render.use_compositing = False; sc.compositing_node_group = None
```

`view_transform = "Standard"` обязателен: иначе AgX (умолчание 5.x) применится к уже готовой картинке и изменит цвета.

### 6.5. Путь A против пути B и цена «запечённого мира»

| | A: свет целиком → unlit | B: освещённость → lightMap |
|---|---|---|
| совпадение с Cycles | ΔE 0.73 | ΔE 0.74–0.89 |
| шейдер в three | `MeshBasicMaterial`: 1 выборка текстуры, без расчёта света | PBR + lightMap: полный расчёт |
| блики, отражения, смена цвета материала в JS | нет | есть |
| карта | уникальна на всю сцену (атлас), цвет + свет | только свет (можно ниже разрешением) |
| вес | растёт с площадью сцены: диорама 950 КБ (PNG 1024²) | 14 КБ GLB + карта отдельно |
| движущиеся объекты | тени «прилипают» — только статика | то же для карты; динамика — отдельным светом |

[проверено]. Практики:
- Andrew Woan (Codrops, 2025): вся сцена запечена COMBINED в 4096² EXR 32-bit float с денойзом композитором, второй UV
  «SimpleBake», Smart UV + UVPackmaster, затем PNG → KTX2 ETC1S (`gltf-transform etc1s --quality 255`); в коде все материалы
  заменены на `MeshBasicMaterial`; загрузка ≈ 6 с оценена как приемлемая цена [S9].
- Он же (Codrops, 2026): аддон «One Shot Baking» — второй UV на всех объектах, развёртка коллекции на одну картинку, упаковка,
  запекание, денойз композитором, оптимизация картинки, дубликат меша с запечённой текстурой [S10].
- Bruno Simon (Awwwards, 2026): цвета моделей — одна палитра-текстура и UV-выборка из неё (без запекания цвета), геометрии
  слиты, скрытые грани удалены; текстуры ETC1S/UASTC; инстансинг деревьев, скамеек, фонарей [S11]. Это альтернатива запеканию
  цвета для стилизованных сцен.

## 7. Нормали high-poly → low-poly

High: Suzanne + Subdivision 3 + Displace (Clouds, 0.03) = 62 976 треуг.; low: Suzanne + Subdivision 1 = 3936 треуг., Smart UV.
Сравнение: Blender рендерит high, three — low из GLB [проверено].

| вариант low-poly | время bake | IoU | ΔE2000 | SSIM L* | вид |
|---|---|---|---|---|---|
| без карты нормалей | — | 0.982 | 4.29 | 0.693 | гладкий, рельеф пропал |
| NORMAL, `cage_extrusion=0.02`, 1024², 4 spp | 0.36 с | 0.982 | **3.66** | **0.785** | рельеф восстановлен |
| то же, 2048² | 1.17 с | — | — | — | — |
| NORMAL, `cage_extrusion=0` | 0.37 с | 0.982 | 7.31 | 0.424 | пятна-артефакты: хуже, чем без карты |

```python
# Blender 5.2.2 — [проверено]; new_bake_image/set_bake_target — §3.2
import bpy, time

def bake_normal_high_to_low(high, low, img, extrusion=0.02, max_ray=0.0, samples=4):
    """Нормали high-poly → tangent-space карта low-poly. low — активный, оба выделены; картинка — активная нода low."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples
    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True); low.select_set(True)
    bpy.context.view_layer.objects.active = low
    node = set_bake_target(low.active_material, img)
    t = time.time()
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", use_selected_to_active=True,
                        cage_extrusion=extrusion, max_ray_distance=max_ray, margin=16, use_clear=True)
    dt = time.time() - t
    low.active_material.node_tree.nodes.remove(node)
    return dt
```

- Лучи идут от low-poly внутрь к high-poly; `cage_extrusion` «раздувает» low на заданное расстояние перед пуском лучей,
  `max_ray_distance` ограничивает длину (0 — без ограничения) [S1] [S2]. Без раздувания (0) лучи из точек, где low лежит
  снаружи high, промахиваются — артефакты. Начальное значение — 1–2 % размера объекта, затем проверить картинку
  [проверено].
- Руководство описывает Extrusion как параметр режима Cage, а Max Ray Distance — как режим без Cage [S1]; в 5.2.2
  `cage_extrusion` действует и без `use_cage` (0 → артефакты, 0.02 → норма), что совпадает с описанием свойства в API
  («Inflate the active object by the specified distance for baking») [S2] [проверено].
- Для сложных форм — объект-клетка (`cage_object`) с той же топологией, что low [S1] (не проверено).
- Low-poly для такого запекания — гладкий (без острых рёбер или с ними по швам UV): жёсткие рёбра без шва дают полосы
  [S1: «Hard splits … should be avoided»].
- GLB low без карты — 115 КБ, с картой нормалей 1024² PNG — 986 КБ: шумная нормаль тяжелее геометрии; сжимать (UASTC для
  нормалей — `03` §3) [проверено].

## 8. Металличность через EMIT и упаковка ORM

В 5.2 нет прохода METALLIC; источник металличности временно подаётся в Emission и запекается EMIT [проверено].
Затем AO (R), roughness (G) и metallic (B) складываются в одну картинку — экспортёр запишет одну текстуру для
`occlusionTexture` и `metallicRoughnessTexture` (в опыте оба индекса 0, одна картинка).

```python
# Blender 5.2.2 — [проверено] (металл 0/1 на 31 % площади; ORM → одна текстура в glTF)
import bpy, numpy as np

def bake_metallic_via_emit(ob, mat, img):
    """В 5.2 нет типа bake METALLIC: временно подаём источник Metallic в Emission и печём EMIT."""
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    src = bsdf.inputs["Metallic"].links[0].from_socket if bsdf.inputs["Metallic"].is_linked else None
    em = nt.nodes.new("ShaderNodeEmission")
    if src:
        nt.links.new(src, em.inputs["Color"])
    else:
        v = bsdf.inputs["Metallic"].default_value; em.inputs["Color"].default_value = (v, v, v, 1)
    old = out.inputs["Surface"].links[0].from_socket
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    node = set_bake_target(mat, img)
    bpy.ops.object.bake(type="EMIT", margin=16, use_clear=True)
    nt.links.new(old, out.inputs["Surface"])
    nt.nodes.remove(em); nt.nodes.remove(node)


def pack_orm(ao, rough, metal, name, path):
    """R = AO, G = roughness, B = metallic → одна PNG (Non-Color) для glTF (occlusion + metallicRoughness)."""
    w, h = ao.size
    px = {}
    for key, im in (("ao", ao), ("r", rough), ("m", metal)):
        a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); px[key] = a.reshape(-1, 4)
    out = np.ones((w * h, 4), np.float32)
    out[:, 0] = px["ao"][:, 0]; out[:, 1] = px["r"][:, 0]; out[:, 2] = px["m"][:, 0]
    orm = bpy.data.images.new(name, w, h, alpha=False)
    orm.colorspace_settings.name = "Non-Color"
    orm.pixels.foreach_set(out.ravel())
    orm.filepath_raw = path; orm.file_format = "PNG"; orm.save()
    return orm
```

Подключение ORM — `01-export-contract.md` §5.2 (`pbr_material`: Separate Color → G Roughness, B Metallic, R → Occlusion группы).
Все три карты должны быть одного размера — иначе экспортёр не упакует их в одну текстуру [S4].

## 9. Geometry Nodes и модификаторы → меш

«Запекание» GN для glTF — это применение модификатора: экспорт с `export_apply=True` или явное применение. В фоне
`bpy.ops.object.modifier_apply(modifier=name)` работает для активного объекта в OBJECT mode: GN с Realize Instances
(100 икосфер) → меш 8000 треуг. за 0.004 с, модификаторов не остаётся [проверено].
Повторяющиеся объекты лучше не реализовывать, а экспортировать инстансами (`01` §4.7: 11.8 КБ против 625 КБ).

```python
# Blender 5.2.2 — [проверено]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
for md in list(ob.modifiers):
    bpy.ops.object.modifier_apply(modifier=md.name)   # применение в порядке стека; shape keys мешают применению
```

Анимацию GN и симуляции для веба запекают в вершинную анимацию или кэш (VAT, морфы) — тема агента H (волна 2).

## 10. Цена запечённого в вебе

| что | файл | память GPU | опыт |
|---|---|---|---|
| 3 карты 1024² PNG (base, rough, normal) | GLB 2.13 МБ | 3 × 5.3 МБ | E/19 |
| 3 карты 2048² PNG | GLB 6.2 МБ | 3 × 21.3 МБ = 64 МБ | E/19, E/18 |
| AO 1024² PNG | +468 КБ к GLB | 5.3 МБ | E/20 |
| нормаль high→low 1024² PNG | +870 КБ к GLB | 5.3 МБ | E/27 |
| запечённый свет диорамы 1024² PNG (unlit) | GLB 950 КБ (795 КБ после денойза) | 5.3 МБ | E/21 |
| та же карта в KTX2 | — | 1.3 МБ (BC7/ASTC, 1 байт/пиксель + мипмапы) | расчёт по E/18 |

[проверено]. Выводы:
- Запечённые PNG — самые тяжёлые картинки в ассете (шум плохо жмётся); после запекания обязательна постобработка:
  WebP/AVIF для цвета, KTX2 (ETC1S цвет, UASTC нормали) для памяти GPU, ресайз 2048 → 1024 (вес ×2.3, память ×4) — `03` §3.
- Для веба пекут 1024² на объект первого экрана и 512² на второстепенные; 2048² — только hero крупным планом [практика; сверено с
  бюджетами `03` §6].
- Один атлас на много объектов = меньше вызовов отрисовки при слиянии мешей, но больше пикселей впустую (Smart UV занимает
  50–60 % квадрата) [проверено].

## Частые ошибки

1. Запекание при `scene.render.engine = "BLENDER_EEVEE"` → `RuntimeError: Current render engine does not support baking`
   [проверено].
2. Старый API: `scene.render.bake_type = "AO"` → `AttributeError` (в 5.2 — `bpy.ops.object.bake(type="AO")`, а
   `scene.render.bake.type` относится к Multires); `bpy.ops.object.bake_image()` — это Multires-запекание, не Cycles
   [проверено].
3. Нет активной ноды Image Texture в материале → `{'CANCELLED'}` без исключения; если цель есть не во всех материалах —
   `{'FINISHED'}`, но грани остальных материалов не запечены [проверено].
4. DIFFUSE с фильтрами по умолчанию для PBR-карты → свет и тени сцены попадают в base color (двойное освещение в three)
   [проверено].
5. Картинка для нормалей/шероховатости создана с пространством sRGB по умолчанию → неверные значения в Blender и
   расхождение с three [проверено].
6. Float-картинка с «Linear Rec.709» сохранена `Image.save()` → в .hdr/.exr/.png записаны sRGB-значения (0.5 → 0.735)
   [проверено].
7. Карта света в 8-битной PNG без масштаба → блики и солнечные пятна обрезаны [проверено].
8. `lightMapIntensity` оставлен 1 → всё в π раз темнее (ΔE 22) [проверено].
9. Карта света загружена `TextureLoader` без `flipY = false` → карта перевёрнута (ΔE 23); без `channel = 1` читается UV0
   [проверено].
10. High→low с `cage_extrusion = 0` → пятна хуже, чем без карты [проверено].
11. Развёртка с наложением островов (зеркальные половины) → запекание перетирает острова [документация: S1].
12. UV-операторы вызываются в OBJECT mode или через `temp_override` с несуществующей областью окна — в фоне достаточно EDIT
    mode и выделения [проверено].
13. После `ob.scale = …` в скрипте читается `matrix_world` без `view_layer.update()` → старые значения [проверено].
14. Композитор по памяти: `scene.use_nodes = True; scene.node_tree.nodes[...]`, нода Composite → `AttributeError`/`RuntimeError`
    в 5.x [проверено] [S3].
15. Денойз без `view_transform = "Standard"` → AgX второй раз применяется к готовой карте [проверено].
16. AO умножен в base color и одновременно подан в Occlusion → двойное затемнение; выбрать одно.
17. Запечённый свет + лампы и environment на странице → свет считается дважды.
18. Процедурный материал оставлен на объекте после запекания → экспортёр возьмёт его, а не запечённый (белый объект в вебе).
19. Emission Strength > 1 запечена в 8-бит → обрезка; печь цвет при силе 1 [проверено].

## Чек-лист

- [ ] Движок Cycles, устройство CPU, сэмплы по типу прохода (данные — 1, свет/AO — 16–64)?
- [ ] У меша UV без наложений; для света — отдельный второй слой (Lightmap Pack)?
- [ ] Плотность текселей посчитана и сопоставима у соседних объектов (px/м)?
- [ ] В каждом материале объекта есть активная выбранная нода Image Texture с целевой картинкой?
- [ ] Картинка создана до bake с правильным пространством (sRGB — цвет, Non-Color — данные)?
- [ ] DIFFUSE для PBR-альбедо — `pass_filter={"COLOR"}`?
- [ ] Результат `bpy.ops.object.bake` проверен (`FINISHED`, не `CANCELLED`)?
- [ ] Картинки сохранены в файлы (или упакованы) до выхода из скрипта?
- [ ] Float-карты сохранены с Non-Color или через `save_render`?
- [ ] Карта света без обрезки (HDR или масштаб ×k) и `lightMapIntensity = π/k`?
- [ ] High→low: `cage_extrusion` ≈ 1–2 % размера, low-poly активный, оба выделены?
- [ ] ORM собран в одну картинку одного размера и подключён через Separate Color + группу?
- [ ] Объект получил новый простой материал, процедурный не экспортируется?
- [ ] В three: AO виден (есть окружение), lightMap на `channel 1` с `flipY = false`, свет не удвоен?
- [ ] Запечённые PNG сжаты (WebP/KTX2) и разрешение соответствует бюджету (`03` §6)?

## Открытые вопросы и противоречия

1. **Руководство против API** по `cage_extrusion` без Cage: руководство относит Extrusion к режиму Cage [S1], описание свойства и
   эксперимент показывают, что раздувание действует и без клетки [S2] [проверено].
2. **Двойной свет с lightMap**: как сочетать lightMap (прямой + непрямой свет) с `scene.environment` для бликов без пересвета —
   не проверено; вероятно, нужен запечённый только непрямой свет + реальные лампы на странице.
3. **KTX2 для карт света**: ETC1S мылит градиенты (на нормалях SSIM 0.91, `03` §3); как ведёт себя UASTC/ETC1S на плавных
   картах освещения — не проверено.
4. **GPU-запекание** (OptiX/HIP/oneAPI) на этой машине не проверялось: все времена — CPU 20 потоков; на GPU запекание света
   быстрее, но в фоновом режиме с Iris Xe не тестировалось.
5. **Ориентиры плотности текселей** (256–1024 px/м) — практика, не замер восприятия; нужна проверка на реальных экранах (агент J).
6. **Высокое разрешение атласов** (4096², как у практиков [S9]) против памяти телефонов (`03` §6): 4096² RGBA8 = 85 МБ в GPU —
   на телефоне только KTX2.
7. **Bake для анимированных объектов** (свет на движущихся частях, VAT) — не входило в тему (агент H).

## Источники

- [S1] Blender Foundation. Blender 5.2 Manual — Render Baking (Cycles). 2026. https://docs.blender.org/manual/en/5.2/render/cycles/baking.html — типы, фильтры, Selected to Active, Cage, Margin, цели; официальный, прочитан целиком.
- [S2] Blender Foundation. Blender 5.2 Python API — `bpy.types.BakeSettings`. https://docs.blender.org/api/5.2/bpy.types.BakeSettings.html — `cage_extrusion`, `max_ray_distance`, `margin_type` (ADJACENT_FACES), `target`, умолчания; официальный.
- [S3] Blender Foundation. Blender 5.0 Release Notes — Python API и Compositor. https://developer.blender.org/docs/release_notes/5.0/python_api/ , …/5.0/compositor/ — `scene.node_tree` → `compositing_node_group`, Composite → Group Output, `use_nodes` устарели.
- [S4] glTF-Blender-IO v5.2.40 (в составе Blender 5.2.2): `material/materials.py`, `pbr_metallic_roughness.py` — упаковка ORM, группа «glTF Material Output»; прочитаны целиком.
- [S5] three.js r186. `examples/jsm/loaders/GLTFLoader.js` — `occlusionTexture` → `aoMap`, `texCoord` → `channel`, unlit → `MeshBasicMaterial`; прочитан целиком.
- [S6] Khronos. glTF 2.0 extensions KHR_materials_unlit, KHR_texture_transform — https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos — unlit как носитель запечённого света.
- [S7] Отчёт агента E, `01-export-contract.md` (эта папка) — что теряет экспортёр и почему нужно запекание.
- [S8] Агент B, волна 1. `99-raw/reports/wave1-B-report.md` — правило поиска сокетов Mix по identifier (совпало с практикой E/20).
- [S9] Andrew Woan. Building a Fully-Featured 3D World in the Browser with Blender and Three.js. Codrops, 2025-04-08. https://tympanus.net/codrops/2025/04/08/3d-world-in-the-browser-with-blender-and-three-js/ — полное запекание сцены (COMBINED, 4096², EXR, денойз), MeshBasicMaterial в коде, KTX2 ETC1S; практика, подробно.
- [S10] Andrew Woan. Blender to Three.js and Back: 10 Tips for a Better Workflow. Codrops, 2026-08-24. https://tympanus.net/codrops/2026/08/24/blender-to-three-js-and-back-10-tips-for-a-better-workflow/ — «One Shot Baking» через Python-аддон, MCP; практика, кратко.
- [S11] Bruno Simon. Bruno’s Portfolio — case study. Awwwards, 2026. https://www.awwwards.com/brunos-portfolio-case-study.html — палитра-текстура вместо запечённого цвета, инстансинг, ETC1S/UASTC, Draco с квантованием; практика автора эталонного сайта.

Эксперименты: `99-raw/experiments/E/19-bake-procedural`, `20-bake-ao`, `21-bake-lighting`, `27-bake-extra`, `25-api-drift`
(запекание и композитор), сквозные `12-materials-core`, `16-image-formats`, `18-compression-textures`.
