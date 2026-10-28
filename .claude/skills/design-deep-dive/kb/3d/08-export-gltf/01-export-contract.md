# Контракт экспорта Blender 5.2.2 → glTF 2.0 → three.js r186: что доживает до страницы

Волна 1 · агент E · 22–23.09.2026 · источников прочитано целиком: 25 (исходники экспортёра и загрузчика, руководство Blender 5.2,
16 спецификаций Khronos, release notes) · экспериментов: 26 папок `99-raw/experiments/E/01…26`, около 230 случаев · версии:
Blender 5.2.2 LTS (d13f752e3b9c), glTF-Blender-IO 5.2.40, three.js r186 (0.186.0), gltf-transform 4.5.0, gltfpack 1.2,
gltf-validator 2.0.0-dev.3.10, Chromium (Playwright) на Intel Iris Xe (ANGLE GL, Mesa).

Файл — контракт для агентов волны 2: моделирование (D1), материалы и свет (D2), анимация (H), рантайм (F). Каждая строка
матрицы проверена цепочкой «сцена в Blender → экспорт → JSON glTF → загрузка в three r186 → сравнение картинок» утилитами
`gltf_diff.py`, `gltf_web_inspect.py`, `gltf_load_bench.py` (описание — §1). Сжатие и бюджеты — `03-compression-textures-budgets.md`,
запекание — `02-baking.md`, валидатор, поломки и готовые пресеты — `04-validation-pitfalls-presets.md`.

## Выжимка для агента

1. **Формат и оси**: `export_format="GLB"`, `export_yup=True`; при `export_yup=False` модель в three лежит на спине → §4.9 [проверено]
2. **Модификаторы не применяются по умолчанию** (`export_apply=False`): уходит исходный меш, Subdivision/Bevel/Mirror/Array/Weighted Normal/GN теряются. Для веба `export_apply=True` → §4.6 [проверено]
3. `export_apply=True` берёт **уровень вьюпорта** (`levels`), а не `render_levels`; модификатор с `show_viewport=False` не применяется → §4.6 [проверено]
4. `export_apply=True` **молча уничтожает shape keys** у объектов, у которых есть модификаторы; у объектов без модификаторов морфы сохраняются. Морф-ассет: модификаторы применить до создания shape keys или экспорт без apply → §4.6 [проверено]
5. **Жёсткие рёбра — данными**: `mesh.set_sharp_from_angle(angle)` или `bpy.ops.object.shade_smooth_by_angle`; оператор `shade_auto_smooth` создаёт модификатор, и без apply рёбра пропадают (64 нормали вместо 34) → §4.2 [проверено]
6. **Flat-шейдинг дорогой**: UV-сфера 48×24 — 4512 вершин против 1223 у гладкой, файл ×3; гладкие грани + острые рёбра только где нужно → §4.1 [проверено]
7. **Экспортируются все UV-слои** (TEXCOORD_0…n по порядку списка); three r186 читает 4 (uv…uv3), texCoord ≥ 4 → ошибка шейдера и меш не рисуется. Держать 1–2 слоя → §4.3 [проверено]
8. Меш без текстур всё равно получает TEXCOORD_0 (INFO UNUSED_OBJECT в 195 из 242 файлов): `export_texcoords=False` для нетекстурных объектов или `gltf-transform prune` → §4.3 [проверено]
9. **Цвет вершин = только множитель Base Color** (нода Color Attribute → Base Color). Ставить `export_all_vertex_colors=False`: при умолчании и ≥ 2 цветовых атрибутах COLOR_0 белый (баг 5.2.40, ΔE 35) → §4.4 [проверено]
10. **Данные для шейдера** — атрибут с именем на «_» + `export_attributes=True`; в glTF имя ВЕРХНИМ регистром, в three — нижним (`geometry.attributes._wave`); int/bool → float32, домен EDGE и STRING теряются → §4.5 [проверено]
11. **Повторяющиеся объекты из GN**: `export_gn_mesh=True` + `export_gpu_instances=True` + `export_apply=True` → один узел `EXT_mesh_gpu_instancing` → `InstancedMesh`, 1 draw call, 11.8 КБ против 625 КБ у Realize Instances → §4.7 [проверено]
12. Связанные дубликаты (общий mesh, дети одного Empty) + `export_gpu_instances=True` → тоже `InstancedMesh` (100 объектов → 1 вызов) → §4.7 [проверено]
13. **Кривые и текст** экспортёр конвертирует сам; текст по умолчанию ≈ 1250 треуг./символ — `resolution_u` 3–4 и `bevel_resolution` 0–1 дают ×6.6 меньше → §4.8 [проверено]
14. **Масштаб**: 1 Blender unit = 1 м glTF, `scale_length` игнорируется; неприменённый и отрицательный масштаб переносятся верно, но масштаб лучше применить; origin объекта = точка вращения в JS → §4.9 [проверено]
15. **Скрытые объекты экспортируются**: `hide_viewport`, `hide_render`, исключённые коллекции — всё уходит по умолчанию. Фильтры: `use_renderable`, `use_visible`, `collection="WEB"`, служебная коллекция `glTF_not_exported` → §3.3 [проверено]
16. `use_selection=True` в фоне без выделения даёт **пустой GLB (132 байта) без ошибки** → §3.3 [проверено]
17. **Что переживает экспорт в материале**: Principled BSDF + Image Texture (+ Normal Map, Separate Color, Mix MULTIPLY / Math MULTIPLY на константу, Mapping POINT). Всё остальное запекать (`02-baking.md`) → §5.2 [проверено]
18. **Ноды между картинкой и Principled отбрасываются молча**: Color Ramp, Hue/Saturation, Mix с процедурой → в glTF сырая картинка (ΔE 18–33) → §5.8 [проверено]
19. **Bump от картинки** уходит как `normalTexture` с картой высот (мусорный рельеф, ΔE 8.9): рельеф — только Normal Map или запечённая нормаль → §5.8 [проверено]
20. **Процедурные текстуры** (Noise, Voronoi, Layer Weight, Fresnel, координаты Generated/Object) не экспортируются: сокет получает значение glTF по умолчанию (base color белый, roughness 1) → §5.8 [проверено]
21. **Цветовое пространство картинки в glTF не пишется**: base color и emission читаются как sRGB, остальные карты — как линейные. Ошибка «Non-Color на цвете» или «sRGB на данных» ломает вид в Blender, а в вебе картинка правильная — расхождение → §5.4 [проверено]
22. **Альфа задаётся нодами**, не `blend_method`/`surface_render_method`: Alpha-константа < 1 → BLEND (в three `transparent` + `depthWrite=false`), Math ROUND → MASK 0.5, `1 − (a < c)` → MASK c → §5.5 [проверено]
23. `doubleSided = not use_backface_culling`; по умолчанию culling выключен → **все материалы двусторонние**. Для замкнутых мешей включать culling → §5.5 [проверено]
24. **Occlusion, Thickness, Dispersion, Iridescence Factor** есть только в группе «glTF Material Output» (создаётся кодом, §5.7) → §5.7 [проверено]
25. **Стекло** = Transmission Weight 1 + Thickness в группе + Volume Absorption; без Thickness three рисует тонкостенную прозрачность без преломления → §6.2 [проверено]
26. **Теряются без предупреждения**: Coat Tint, Coat IOR, Sheen Weight как множитель, Subsurface, Diffuse Roughness, Thin Wall, IOR без transmission/specular, Thin Film без группы → §6.1 [проверено]
27. **Mix Shader** двух Principled → в glTF один из них (ΔE 27.7); Diffuse BSDF и прочие шейдеры → материал без PBR (в three белый «металл» metalness 1, roughness 1) → §5.8 [проверено]
28. **Unlit** (`KHR_materials_unlit` → `MeshBasicMaterial`): цвет или картинка прямо в Surface, трюк Light Path, нода Background. Одна нода Emission — не unlit, а PBR с отражениями → §6.3 [проверено]
29. **Emission Strength > 1** переносится (`KHR_materials_emissive_strength` → `emissiveIntensity`), ΔE ≤ 1 → §6.1 [проверено]
30. **Свет** по умолчанию не экспортируется — правильно для сайтов. Если нужен: `export_import_convert_lighting_mode="COMPAT"` (±2 % к Blender); умолчание SPEC даёт ×683, Area и мир не экспортируются → §8.1 [проверено]
31. **Камеры** по умолчанию не экспортируются; `yfov` пересчитывается по sensor fit и разрешению рендера; DOF и shift теряются → §8.2 [проверено]
32. **Анимация**: уходят только активное действие и действия в NLA-дорожках; действие с одним fake user теряется. Клип на каждое действие — `stash_action()` в свою дорожку → §9.1 [проверено]
33. **Констрейнты и драйверы** уходят только с `export_bake_animation=True` → §9.2 [проверено]
34. **Анимацию материалов, света, камер** (`KHR_animation_pointer`) three r186 не проигрывает (клип 0 с без треков) — анимировать кодом → §9.3 [проверено]
35. **Поза покоя = кадр 0**: экспортёр делает `frame_set(0)` перед сбором, если не `export_current_frame` → §9.4 [проверено]
36. **Данные для JS**: `export_extras=True` → `object.userData`; имена в three санитизируются («Cube.001» → «Cube001», оригинал в `userData.name`) — называть объекты `латиница_через_подчёркивание` → §10 [проверено]
37. **Картинки**: `AUTO` копирует исходные JPEG/PNG байт в байт (`export_image_quality` не действует), `WEBP` делает `EXT_texture_webp` обязательным, `export_image_add_webp` — +30 % мёртвого веса. Сжатие и ресайз — постобработкой → §11 [проверено]
38. **Встроенное сжатие экспортёра**: Meshopt без квантования (2.2 МБ против 0.8–1.25 МБ у gltfpack/gltf-transform), Draco не сжимает морфы — сжимать постобработкой (`03-compression-textures-budgets.md`) → §11 [проверено]

## 1. Метод: как проверялась каждая строка

### 1.1. Цепочка

1. Скрипт собирает сцену в Blender 5.2.2 без окна (`../../scripts/3d/blender_run.py`), сохраняет `.blend` и экспортирует GLB.
2. JSON glTF читается напрямую (`99-raw/experiments/E/_lib/gltfinfo.py`, `gltfread.py`): какие узлы, аксессоры, материалы,
   расширения записаны.
3. `../../scripts/3d/gltf_web_inspect.py model.glb` — что three r186 создал из файла: типы объектов (Mesh, InstancedMesh,
   SkinnedMesh), имена и `userData`, атрибуты геометрии, тип и параметры материалов, карты с `colorSpace` и `channel`, клипы и
   треки, `renderer.info` (вызовы, треугольники, память), ошибки консоли.
4. `../../scripts/3d/gltf_diff.py scene.blend out/ --glb model.glb` — одна камера (вертикальный FOV 40°, квадратный кадр), один HDRI
   (`studio_small_09`, Poly Haven CC0), один тонмаппинг в Blender и в three; метрики IoU силуэта, ΔE2000 (среднее и p95),
   SSIM по светлоте L*, тепловая карта.
5. `../../scripts/3d/gltf_load_bench.py a.glb b.glb` — холодная и тёплая загрузка, первый кадр, память GPU (для сжатия, §11 и 03).

### 1.2. Пороги (калибровка E/02)

| пара рендеров | IoU | ΔE2000 среднее (фронт) | вывод |
|---|---|---|---|
| EEVEE «Standard» ↔ three `NoToneMapping` | 0.996 | 3.1 (2.0–2.3) | эталонная пара |
| EEVEE «Khronos PBR Neutral» ↔ `NeutralToneMapping` | 0.996 | 3.2 | годится |
| EEVEE AgX ↔ `AgXToneMapping` | 0.996 | 4.3 (three светлее на 2–4 L*) | реализации AgX различаются |
| Cycles 64 spp ↔ `NoToneMapping` | 0.996 | 3.5 | эталон для стекла и анизотропии |

Правило чтения матрицы: ΔE2000 ≤ 3.5 и IoU ≥ 0.99 — «совпадает»; металлы и блики — до ≈ 5; ΔE > 6 или IoU < 0.95 — поломка
экспорта [проверено]. Шумовой порог определяется разницей IBL (PMREM three против
EEVEE), а не экспортом.

### 1.3. Обозначения

- «да» — переносится, вид совпадает; «≈» — переносится с оговоркой; «нет» — теряется или искажается.
- «вершина glTF» — уникальная комбинация позиции, нормали угла, UV, цвета: экспортёр называет их «dots» [S4].
- Все пути экспериментов — от корня базы: `99-raw/experiments/E/<NN-имя>/README.md` (цель, команда, таблица, версии).

## 2. Сводная матрица «Blender → glTF → three r186»

### 2.1. Геометрия и объекты

| в Blender | в glTF (экспортёр 5.2.40) | в three r186 | условие / параметр | статус | доказательство |
|---|---|---|---|---|---|
| n-гоны, квады | треугольники (n-гон из k вершин → k−2, триангуляция Blender; вогнутые — корректно, D1/05) | `Mesh` | всегда | да | E/03 c04 |
| гладкие грани | общие вершины, нормаль на вершину | `NORMAL` | всегда | да | E/03 c05 |
| flat-грани | вершины размножаются: 1223 → 4512 (сфера 48×24) | то же | всегда | ≈ вес ×3 | E/03 c06 |
| острые рёбра (данные `sharp_edge`) | раздельные нормали: 34 уникальных | да | всегда | да | E/03 c07, E/26 |
| модификатор «Smooth by Angle» | исходные нормали (64) без apply; 34 с apply | «надутые» торцы без apply | `export_apply` | нет / да | E/03 c08–c09 |
| custom normals | как есть (`mesh.corner_normals`) | да | всегда | да | E/03 c10 |
| Bevel + Weighted Normal | голый куб без apply (IoU 0.915); 188 треуг. с apply | да с apply | `export_apply` | нет / да | E/03 c11–c12 |
| UV-слои | все → `TEXCOORD_0…n` по порядку списка | `uv`, `uv1`, `uv2`, `uv3`; texCoord ≥ 4 → ошибка шейдера | ≤ 4 слоёв | да / нет | E/04 |
| текстура без UV (`export_texcoords=False`) | нет `TEXCOORD_0` | объект одним цветом, без ошибок | — | нет | E/04 u4, E/22 |
| Color Attribute → Base Color | `COLOR_0` (FLOAT VEC3 или u16n VEC4 с альфой) | `vertexColors=true` (клон материала) | `export_vertex_color="MATERIAL"` | да | E/05 v01–v02 |
| цветовой атрибут, не используемый материалом | фиктивный белый `COLOR_0` u8 + реальный `COLOR_1` | лишний клон материала | `export_all_vertex_colors=True` (умолч.) | ≈ вес | E/05 v03 |
| ≥ 2 цветовых атрибута | используемый `COLOR_0` = белый | белый объект, ΔE 35 | `export_all_vertex_colors=True` | нет баг 5.2.40 | E/05 v05 |
| атрибут `_имя` FLOAT/VECTOR/QUATERNION/FLOAT4X4 | `_ИМЯ` SCALAR/VEC3/VEC4/MAT4 f32 | `geometry.attributes._имя` | `export_attributes=True` | да | E/06 |
| атрибут INT, INT8, BOOLEAN | f32 | Float32 | то же | ≈ | E/06 |
| атрибут EDGE, STRING, без «_» | нет | — | — | нет | E/06 |
| модификаторы (любые, кроме Armature) | игнорируются | — | `export_apply=False` (умолч.) | нет | E/07 |
| Subdivision `levels=1`, `render_levels=3` | 48 треуг. (уровень вьюпорта) | — | `export_apply=True` | ≈ | E/07 |
| shape keys + модификатор | морфы удалены молча | — | `export_apply=True` | нет | E/07, E/24 |
| shape keys без модификаторов | морфы сохраняются | `morphTargetDictionary` | любой `export_apply` | да | E/24 |
| GN без Realize | исходный меш (плоскость); с `export_apply=True` без `export_gn_mesh` у объекта из одних инстансов — пустой узел, 0 мешей (X/02) | — | без `export_gn_mesh` (умолчание False) | нет | E/08 g1, X/02 |
| GN-инстансы | 1 узел `EXT_mesh_gpu_instancing` (100 шт.) | `InstancedMesh`, 1 вызов | `export_gn_mesh` + `export_gpu_instances` + `export_apply` | да | E/08 g9, E/26 |
| GN + Realize Instances | один меш 8000 треуг., 625 КБ | `Mesh` | `export_apply` | ≈ вес ×53 | E/08 g5 |
| связанные дубликаты под Empty | 100 узлов, общий mesh | 100 `Mesh`, 100 вызовов | умолч. | ≈ | E/08 g7 |
| то же + `export_gpu_instances` | 1 узел с инстансингом | `InstancedMesh`, 1 вызов | `export_gpu_instances` | да | E/08 g8 |
| кривая с фаской, текст, поверхность | меш (to_mesh), с apply и без | `Mesh` | всегда | да | E/09 |
| кривая без фаски, свободные рёбра | нет примитивов / `LINES` | `LineSegments` | `use_mesh_edges=True` | ≈ | E/09 k3b, k7 |
| свободные вершины | `POINTS` | `Points` (1 px, без sizeAttenuation) | `use_mesh_vertices=True` | ≈ | E/09 k7 |
| PointCloud | `POINTS` + `_RADIUS` + атрибуты с «_» | `Points` | `use_mesh_vertices` + атрибут `radius`, иначе экспорт падает | ≈ | E/09 k8 |
| неприменённый масштаб, поворот | TRS узла (Z-up → Y-up) | габарит = Blender | всегда | да | E/10 t1 |
| отрицательный масштаб | scale [−1,−1,−1] + поворот 180° | зеркально, грани не вывернуты | всегда | да | E/10 t2 |
| родитель с `matrix_parent_inverse` | локальные TRS из мировых матриц | мир = Blender | всегда | да | E/10 t3 |
| `export_yup=False` | Z вверх | модель лежит | — | нет | E/10 t4b |
| `unit_settings.scale_length=0.01` | игнорируется | куб «1 м» = 100 м | — | нет | E/10 t6 |
| геометрия далеко от origin | вершины со смещением | вращение вокруг чужой точки | — | ≈ | E/10 t5 |
| инстанс коллекции | пустышка + копии; исходник из исключённой коллекции тоже уходит | лишний объект, IoU 0.638 | — | ≈ | E/10 t7 |
| скрытые / hide_render / исключённые | экспортируются | видны | умолч. | нет | E/10 t8 |
| коллекция `glTF_not_exported` | не экспортируется никогда | — | — | да | E/10 |

### 2.2. Материалы

| в Blender | в glTF | в three r186 | ΔE2000 | статус | доказательство |
|---|---|---|---|---|---|
| Principled: цвет, metallic, roughness | `baseColorFactor`, `metallicFactor`, `roughnessFactor` | `MeshStandardMaterial` | 2.7–4.9 | да | E/12 m01–m02 |
| Base Color > 1 | обрезается до [0, 1] | — | 5.2 | ≈ | E/12 m03 |
| Image Texture → Base Color (sRGB, PNG/JPEG) | `baseColorTexture`, байты исходника | `map`, sRGB | 3.3 | да | E/12 m04, m06 |
| та же картинка с Non-Color | то же (пространство не пишется) | sRGB | 15.9 | нет Blender бледнее | E/12 m05 |
| картинка × Mix MULTIPLY (Factor 1) × цвет | текстура + `baseColorFactor` | да | 3.5 | да | E/12 m07 |
| Roughness/Metallic из картинок (одна или две) | `metallicRoughnessTexture` (G, B; перепаковка) | `roughnessMap` = `metalnessMap` | 2.8–5.4 | да | E/12 m08, m10 |
| ORM: Separate Color → R в «glTF Material Output».Occlusion, G, B | одна текстура для MR и occlusion | `aoMap` + MR | 7.2 (AO виден только в three) | да | E/12 m11, E/26 |
| Roughness ← картинка × Math MULTIPLY 0.5 | `roughnessFactor` 0.5 + текстура | да | 2.8 | да | E/12 m12 |
| Normal Map (Tangent), Strength | `normalTexture` + `scale` | `normalMap`, `normalScale` | 3.3–3.9 | да | E/12 m13–m14 |
| карта нормалей с sRGB | байты как есть | верно в three, искажено в Blender | 7.3 | нет расхождение | E/12 m15 |
| Bump ← картинка высот | `normalTexture` = высоты | мусорный рельеф | 8.9 | нет | E/12 m16 |
| Emission Color/Strength ≤ 1 | `emissiveFactor` | `emissive` | 0.9 | да | E/12 m17 |
| Emission Strength 5, 10 | + `KHR_materials_emissive_strength` | `emissiveIntensity` | 0.7–1.0 | да | E/12 m18, E/13 x18 |
| Emission Color ← картинка | `emissiveTexture` | `emissiveMap`, sRGB | 2.2 | да | E/12 m19 |
| не-текстура в Emission Color (атрибут, процедура) | `emissiveFactor` [1,1,1] | объект светится белым | 6.6 | нет | E/05 v11 |
| Alpha-константа < 1 (любой `surface_render_method`) | `alphaMode` BLEND | `transparent`, `depthWrite=false` | 5.0–5.4 | ≈ | E/12 m21–m22 |
| Alpha ← Math ROUND | MASK, cutoff 0.5 | `alphaTest` 0.5 | 2.9 | да | E/12 m23 |
| Alpha ← 1 − (a < 0.3) | MASK, `alphaCutoff` 0.3 | `alphaTest` 0.3 | 3.0 | да | E/12 m24, E/26 |
| `use_backface_culling` | без `doubleSided` / `doubleSided: true` по умолчанию | `FrontSide` / `DoubleSide` | 2.9–3.2 | да | E/12 m26–m27 |
| Interpolation Closest, Extension EXTEND/MIRROR | sampler NEAREST, CLAMP, MIRRORED_REPEAT | да | 3.8–4.1 | да | E/12 m28–m29 |
| Mapping POINT (scale, rot Z, offset) | `KHR_texture_transform` | offset/repeat/rotation | 4.2 | да | E/12 m30 |
| координаты Generated/Object | текстура на UV | — | 36.2 | нет | E/12 m31 |
| Color Ramp, Hue/Saturation после картинки | сырая картинка | — | 33.0–33.5 | нет | E/12 m32–m33 |
| Mix(картинка, Noise) | только картинка | — | 18.3 | нет | E/12 m34 |
| Noise, Layer Weight → Base Color | белый (нет фактора) | — | 15.4–24.3 | нет | E/12 m35, m38 |
| Voronoi → Roughness; Bump ← Noise | roughness 1; нормали нет | — | 2.8–2.9 | нет (заметно на бликах) | E/12 m36–m37 |
| нода Ambient Occlusion → Base Color | `baseColorFactor` = цвет ноды | — | 2.5 | ≈ | E/12 m39 |
| Mix Shader двух Principled | один Principled | — | 27.7 | нет | E/12 m40 |
| только Diffuse BSDF | материал без PBR | metalness 1, roughness 1 | 26.4 | нет | E/12 m41 |
| Subsurface Weight | отброшен | — | 3.7 | нет | E/12 m42 |
| Principled внутри группы нод | распознан | да | 3.1 | да | E/12 m43 |
| Transmission Weight | `KHR_materials_transmission` | `transmission` (тонкостенно) | — | да | E/13 x01–x03 |
| + Thickness в группе + Volume Absorption | + `KHR_materials_volume` (attenuation, thickness) | преломление и поглощение | — | да | E/13 x04, E/26 |
| Volume Absorption без группы | только transmission | — | — | нет | E/13 x05 |
| IOR без transmission/specular | не пишется | ior 1.5 | — | нет | E/13 x06 |
| Dispersion в группе (+ volume) | `KHR_materials_dispersion` | `dispersion` | — | да | E/13 x07, E/26 |
| Specular IOR Level, Specular Tint | `KHR_materials_specular` (×2; > 0.5 → в цвет) | `specularIntensity`, `specularColor` | 1.7 | да | E/13 x08–x10 |
| Coat Weight, Coat Roughness | `KHR_materials_clearcoat` | `clearcoat` | 1.7 | да | E/13 x11 |
| Coat Tint, Coat IOR | нет в glTF | белое покрытие | — | нет | E/13 x12 |
| Sheen Weight 1, Tint, Roughness | `KHR_materials_sheen` | `sheen`, `sheenColor` | — | да | E/13 x13 |
| Sheen Weight 0.3 | тот же JSON, что при 1 | блеск как при весе 1 | — | нет | E/13 x14 |
| Thin Film + Iridescence Factor в группе | `KHR_materials_iridescence` (max = Thin Film Thickness) | `iridescence` | — | ≈ оттенок | E/13 x15 |
| Thin Film без группы | не пишется | — | — | нет | E/13 x16 |
| Anisotropic, Anisotropic Rotation | `KHR_materials_anisotropy` (rotation × 2π) | `anisotropy` по UV-касательной | — | ≈ направление | E/13 x17 |
| цвет/картинка/Background прямо в Surface; Light Path «Is Camera Ray» | `KHR_materials_unlit` | `MeshBasicMaterial` | 1.0–1.3 | да | E/13 x19–x22 |
| одна нода Emission (картинка) | PBR: base [0,0,0], `emissiveTexture` | `MeshStandardMaterial` | 1.3 | ≈ не unlit | E/13 x23 |
| объект без материала | примитив без material | `DefaultMaterial`: белый, metalness 1, roughness 1, FrontSide | — | ≈ | E/03 |

### 2.3. Свет, камеры, анимация, данные

| в Blender | в glTF | в three r186 | условие | статус | доказательство |
|---|---|---|---|---|---|
| Sun / Point / Spot | `KHR_lights_punctual` | `DirectionalLight` / `PointLight` / `SpotLight` | `export_lights=True` | да | E/14 |
| мощность, режим SPEC (умолч.) | ×683 (лк, кд) | пересвет, белый кадр | — | нет | E/14 |
| мощность, режим COMPAT | W/m², W/(4π) | ±2 % к EEVEE | `export_import_convert_lighting_mode="COMPAT"` | да | E/14, E/26 |
| Area, мир (HDRI) | не экспортируются (warning) | — | — | нет | E/14 |
| камера perspective / ortho | `yfov` по sensor fit, `aspectRatio`; `xmag/ymag` | `PerspectiveCamera` / `OrthographicCamera` | `export_cameras=True` | да | E/15 c1–c3 |
| DOF, shift | не экспортируются | — | — | нет | E/15 |
| объектная анимация TRS (Bezier) | LINEAR, ключ на каждый кадр | `VectorKeyframeTrack`, `QuaternionKeyframeTrack` | умолч. (`export_force_sampling=True`) | да | E/15 a1, a5 |
| то же без сэмплирования | CUBICSPLINE, 2 ключа | свой интерполятор, форма Безье | `export_force_sampling=False` | да | E/15 a2 |
| действие в NLA-дорожке + активное | 2 клипа | 2 `AnimationClip` | `export_animation_mode="ACTIONS"` | да | E/15 a6, E/26 |
| действие только с fake user | нет | — | — | нет | E/15 a10 |
| Child Of / драйверы | анимирован только родитель | объект стоит | без `export_bake_animation` | нет | E/15 a11 |
| то же с запеканием | ключи на объекте | движется | `export_bake_animation=True` | да | E/15 a12 |
| shape keys с ключами | `weights` + `extras.targetNames` | `morphTargetInfluences`, `morphTargetDictionary` | без apply или без модификаторов | да | E/15 a16, E/24 |
| арматура + Armature | `skin`, клип | `SkinnedMesh` + `Bone` | умолч. | да | E/15 a17, E/24 |
| анимация цвета материала, мощности света | `KHR_animation_pointer` (только SCENE/NLA_TRACKS + `export_pointer_animation`) | клип 0 с без треков | — | нет | E/15 a14–a15b |
| custom properties объекта, меша, материала, камеры, сцены | `extras` | `userData` (меш и объект слиты) | `export_extras=True` | да | E/11, E/26 |
| имя «Cube.001», «My Object», «Кнопка/Главная» | как есть | «Cube001», «My_Object», «КнопкаГлавная»; оригинал в `userData.name` | всегда | ≈ | E/11, E/26 |
| исходные JPEG/PNG | байты копируются | `ImageBitmapLoader` | `export_image_format="AUTO"` | да | E/16 |
| `export_image_format="WEBP"` | `EXT_texture_webp` в required, −57 % | да (ΔE 0.53) | — | да | E/16 |

## 3. Параметры экспортёра, которые решают судьбу веб-ассета

У `bpy.ops.export_scene.gltf` в 5.2.40 — 110 параметров [S2] (полный дамп с типами и умолчаниями:
`99-raw/experiments/E/01-export-params/params.json`). Умолчания рассчитаны на обмен между программами, а не на сайт.

### 3.1. Умолчания, которые надо менять для веба

| параметр | умолчание | для веба | почему | доказательство |
|---|---|---|---|---|
| `export_apply` | False | **True** (кроме морф-ассетов) | иначе уходят исходные меши без модификаторов и GN | E/07, E/08 |
| `export_extras` | False | **True** | custom properties → `userData` для JS | E/11 |
| `export_all_vertex_colors` | True | **False** | фиктивный `COLOR_0` и баг «белый COLOR_0» | E/05, E/26 |
| `use_renderable` / `use_visible` | False / False | **True / True** | иначе уходят скрытые и `hide_render` объекты | E/10 t8 |
| `export_gpu_instances` | False | True для сцен с повторами | 100 вызовов → 1 | E/08 |
| `export_gn_mesh` | False | True для GN-инстансов | иначе инстансы GN теряются | E/08 |
| `export_lights` | False | False (свет кодом) или True + COMPAT | SPEC даёт ×683 | E/14 |
| `export_import_convert_lighting_mode` | SPEC | COMPAT, если свет экспортируется | совпадение ±2 % | E/14 |
| `export_cameras` | False | True только для «камеры из Blender» (скролл-сцены) | — | E/15 |
| `export_animations` | True | False для статики | лишние клипы от случайных ключей | E/24 |
| `export_texcoords` | True | False для нетекстурных мешей | 8 байт/вершину и +10 % вершин на швах | E/03, E/22 |
| `export_image_format` | AUTO | AUTO (сжатие постобработкой) | JPEG/PNG байт в байт; WebP/KTX2 делает gltf-transform/gltfpack лучше | E/16, E/18 |
| `export_draco_mesh_compression_enable` | False | False | Draco медленно декодируется и не сжимает морфы; сжатие — постобработкой | E/17 |
| `export_meshopt_compression_enable` | False | False | встроенный Meshopt без квантования | E/17 |
| `export_yup` | True | True | — | E/10 |
| `export_tangents` | False | False (True — если нужна точная карта нормалей) | three строит касательные сам; валидатор даёт WARNING | E/22 |

Остальные умолчания подходят вебу: `export_format="GLB"`, `export_materials="EXPORT"`, `export_normals=True`,
`export_morph=True`, `export_morph_normal=True`, `export_skins=True`, `export_influence_nb=4`, `export_force_sampling=True`,
`export_optimize_animation_size=True`, `export_try_sparse_sk=True` [проверено].

### 3.2. Базовый набор (из него собраны пресеты 04 §7)

```python
# Blender 5.2.2 / glTF-IO 5.2.40 — [проверено]
import bpy, os

WEB = dict(
    export_format="GLB", export_yup=True,
    export_apply=True,                 # модификаторы (уровень ВЬЮПОРТА); у объектов с модификаторами теряются shape keys
    export_texcoords=True, export_normals=True, export_tangents=False,
    export_materials="EXPORT", export_image_format="AUTO",
    export_vertex_color="MATERIAL", export_all_vertex_colors=False,
    export_attributes=False, export_extras=True,
    export_cameras=False, export_lights=False,
    use_renderable=True, use_visible=True,
    export_animations=False,
)


def export_web(path, **overrides):
    kw = dict(WEB); kw.update(overrides)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return bpy.ops.export_scene.gltf(filepath=os.path.abspath(path), **kw)

# export_web("/abs/path/hero.glb")
# export_web("/abs/path/anim.glb", export_animations=True, export_animation_mode="ACTIONS")
```

Защита от дрейфа версий — проверять ключи по RNA оператора до вызова; неизвестный ключ в 5.2 даёт
`TypeError: Converting py args to operator properties:: keyword "…" unrecognized` [проверено]:

```python
# Blender 5.2.2 — [проверено: ../../scripts/3d/presets.py]
valid = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
bad = [k for k in WEB if k not in valid]
if bad:
    raise KeyError(f"нет параметров {bad} в export_scene.gltf этой версии")
```

### 3.3. Выбор объектов

| способ | что попадает | доказательство |
|---|---|---|
| по умолчанию | **все** объекты сцены, включая `hide_set`, `hide_viewport`, `hide_render` и объекты в исключённых из слоя коллекциях | E/10 t8 |
| `use_visible=True` | видимые + `hide_render` | E/10 t8b |
| `use_renderable=True` | всё, кроме `hide_render` | E/10 t8c |
| `use_renderable=True, use_visible=True` | видимые и рендеримые | E/24 (hidden_render исключён) |
| `collection="WEB"` (из скрипта) | только коллекция WEB и вложенные | E/24: вспомогательный куб из Helpers не попал |
| коллекция с именем `glTF_not_exported` | никогда не экспортируется | E/10 |
| `use_selection=True` | выделенные; **в фоне без выделения — пустой GLB 132 байта, FINISHED, без ошибки** | E/25 |
| инстанс коллекции | пустышка + копии объектов; исходник из исключённой коллекции тоже уходит (лишний объект) | E/10 t7 |

Правило для агента: сцена для веба собирается в отдельной коллекции (например `WEB`), вспомогательное — в `glTF_not_exported`,
экспорт — `export_web(path, collection="WEB")`. Параметры `use_active_collection`, `use_active_scene`, `at_collection_center`,
`export_hierarchy_full_collections` существуют [S2], но не проверялись.

### 3.4. Прочие параметры, о которых стоит знать

- `export_format`: `GLB` (по умолчанию) или `GLTF_SEPARATE`; `GLTF_EMBEDDED` доступен только при настройке аддона
  `allow_embedded_format`, иначе `TypeError: enum "GLTF_EMBEDDED" not found in ('GLB', 'GLTF_SEPARATE')` [проверено].
- `export_texture_dir` — папка текстур для `.gltf`; `export_keep_originals` — ссылки на исходные файлы по относительным путям,
  в том числе **вне папки экспорта** (`../../../_assets/…`) — при выкладке текстуры теряются [проверено].
- `export_shared_accessors` (общие индексы для нескольких материалов), `export_hierarchy_flatten_objs`, `export_copyright`,
  `export_loglevel` — есть в 5.2.40 [S2], для веба не проверялись.
- `will_save_settings=True` сохраняет набор в `scene["glTF2ExportSettings"]` [S2].
- Хуки: классы `glTF2ExportUserExtension` и функции `glTF2_pre_export_callback` / `glTF2_post_export_callback` в модулях
  аддонов — способ дописать свои расширения [S2] [документация].
- Перед сбором экспортёр переводит активный объект в OBJECT mode и ставит кадр 0 (если не `export_current_frame`) [S3].

## 4. Геометрия

### 4.1. Триангуляция и число вершин

| случай (E/03) | Blender: вершины / грани / треуг. | glTF: вершины / треуг. | файл, КБ |
|---|---|---|---|
| куб flat + UV | 8 / 6 / 12 | 24 / 12 | 1.7 |
| куб smooth + UV | 8 / 6 / 12 | 14 / 12 (UV-швы) | 1.4 |
| куб smooth без UV | 8 / 6 / 12 | 8 / 12 | 1.0 |
| 8-угольник (n-гон) | 8 / 1 / 6 | 8 / 6 | 1.2 |
| UV-сфера 48×24 smooth | 1106 / 1152 / 2208 | 1223 / 2208 | 52.1 |
| та же flat | 1106 / 1152 / 2208 | **4512** / 2208 | **154.9** |

- Триангуляция всегда: n-гон из k вершин → k − 2 треугольника триангуляцией Blender, вогнутые (звезда, П-образная грань)
  тоже корректно [проверено]. Модификатор Triangulate — только чтобы
  зафиксировать разбиение перед запеканием нормалей (`../05-modeling/05-topology-budgets-cleanup.md` §1.3).
- Вершина glTF — уникальная комбинация позиции, нормали угла, всех UV и цветов [S4]: каждый шов UV и каждое острое ребро
  размножают вершины. Flat-шейдинг = ×3.7 вершин и ×3 файла.
- Бюджет считать по вершинам glTF, а не по вершинам Blender (`03-compression-textures-budgets.md` §6).

### 4.2. Нормали и гладкость

С 4.1 опция Auto Smooth заменена модификатором-ассетом «Smooth by Angle», базовое состояние меша = прежний Auto Smooth 180°,
custom normals используются, если есть [S22]. Для экспорта это значит:

| способ задать жёсткие рёбра | что создаёт | экспорт без apply | экспорт с apply |
|---|---|---|---|
| `mesh.set_sharp_from_angle(angle)` | атрибут `sharp_edge` (данные) | да 34 уникальные нормали | да |
| `bpy.ops.object.shade_smooth_by_angle(angle=…)` | то же, модификатора нет | да | да |
| `bpy.ops.object.shade_auto_smooth(angle=…)` | модификатор NODES «Smooth by Angle» | нет 64 нормали, «надутые» торцы (ΔE 4.0) | да 34 |
| custom normals (`normals_split_custom_set*`) | корневые нормали | да как есть | да |
| Weighted Normal (модификатор) | вычисленные нормали | нет | да |

[проверено]

```python
# Blender 5.2.2 — [проверено] (цилиндр 32 сегм.: 130 вершин glTF, 34 нормали)
import math

def sharp_by_angle(ob, degrees=30.0):
    me = ob.data
    me.shade_smooth()                                   # все грани гладкие
    me.set_sharp_from_angle(angle=math.radians(degrees))  # рёбра острее угла → sharp_edge (данные меша)
    # то же оператором: bpy.ops.object.shade_smooth_by_angle(angle=...) — модификатор НЕ создаёт;
    # bpy.ops.object.shade_auto_smooth(...) создаёт модификатор «Smooth by Angle» → нужен export_apply=True
```

- `mesh.use_auto_smooth` и `mesh.calc_normals_split()` в 5.2 — `AttributeError` (удалены в 4.1); нормали углов читаются
  сразу из `mesh.corner_normals` [проверено] [S22].
- Функции `Mesh.set_sharp_from_angle` и `normals_split_custom_set` не видны через `hasattr(bpy.types.Mesh, …)` — проверять
  через `bpy.types.Mesh.bl_rna.functions` или на экземпляре [проверено].
- Нулевые нормали экспортёр заменяет на (0, 0, 1) [S4]; нет атрибута `NORMAL` → three включает `flatShading` [S5].

### 4.3. UV-слои

- Уходят **все** слои `mesh.uv_layers` как `TEXCOORD_0…n-1` в порядке списка; `TEXCOORD_0` — первый слой, а не активный.
  v переворачивается (v → 1 − v) [S4] [проверено].
- `texCoord` текстуры выбирается так: нода UV Map (по имени) → нода Attribute с именем UV → активный рендер-UV
  (`uv_layers[i].active_render`) [проверено].
- three r186: `TEXCOORD_0…3` → атрибуты `uv`, `uv1`, `uv2`, `uv3`; карта на `texCoord > 0` получает клон текстуры с
  `texture.channel = texCoord`. `texCoord = 4` → `Shader Error 'uv4' : undeclared identifier`, меш не рисуется [S5]
  [проверено].
- Правило: UV0 — для материалов, UV1 — для lightmap/AO (`02-baking.md`), лишние слои удалять до экспорта.
- Атрибут FLOAT2 на CORNER — это UV-слой: уходит `TEXCOORD_n` всегда, даже без `export_attributes`
  [проверено].
- Экспорт без UV при текстурах не даёт предупреждений ни в Blender, ни в three — объект заливается цветом одного текселя (ΔE 46.6);
  ловит только валидатор (`MESH_PRIMITIVE_TOO_FEW_TEXCOORDS`, `04` §2) [проверено].

### 4.4. Цвета вершин (color attributes → COLOR_0)

В glTF у `COLOR_0` одна семантика — множитель базового цвета; экспортёр 5.2.40 пишет его, только если атрибут умножается в
Base Color нодой Color Attribute или Attribute (можно через Mix MULTIPLY с константой) [S4] [S1].

| случай (E/05) | glTF | three | ΔE |
|---|---|---|---|
| POINT FLOAT_COLOR → Color Attribute → Base Color | `COLOR_0` FLOAT VEC3 | `vertexColors=true` | 2.9 |
| CORNER BYTE_COLOR → то же | `COLOR_0` FLOAT VEC3 (байты sRGB → линейные, 0.503 вместо 0.5) | то же | 2.9 |
| с альфой (материал не OPAQUE) | `COLOR_0` UNSIGNED_SHORT normalized VEC4, BLEND | `transparent` | 7.5 |
| атрибут не используется материалом, умолчания | фиктивный белый `COLOR_0` u8 + реальный `COLOR_1` | клон материала с белыми цветами | — |
| два атрибута, умолчания | используемый `COLOR_0` **белый** | белый объект | **35.0** |
| два атрибута, `export_all_vertex_colors=False` | `COLOR_0` = нужный атрибут, `COLOR_1` нет | верно | — |
| атрибут → Emission Color | `emissiveFactor` [1,1,1] | светится белым | 6.6 |

Причина бага: цикл добавления остальных атрибутов в `primitive_extract.py` (`manage_material_info`) переназначает
`material_idxs_using_vc` на последний `COLOR_n` [S4] [проверено].

```python
# Blender 5.2.2 — [проверено] (2 цветовых атрибута + export_all_vertex_colors=False → COLOR_0 верный)
import bpy

def vertex_color_material(name, attr_name="Col"):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    ca = nt.nodes.new("ShaderNodeVertexColor")                 # нода «Color Attribute»
    ca.layer_name = attr_name
    nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])  # → COLOR_0 (export_all_vertex_colors=False!)
    return mat

# атрибут: me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")  (устаревший me.vertex_colors ещё существует)
```

Шероховатость, металличность или эмиссия из цвета вершин в glTF не переносятся — только запеканием в текстуру.

### 4.5. Произвольные атрибуты (данные для шейдера)

| атрибут Blender | `export_attributes=True` | three r186 |
|---|---|---|
| `_weight` FLOAT POINT | `_WEIGHT` SCALAR f32 | `geometry.attributes._weight` (itemSize 1) |
| `_id` INT, `_i8` INT8, `_flag` BOOLEAN FACE | f32 (знакового int в glTF нет); FACE разворачивается по углам | Float32 |
| `_dir` FLOAT_VECTOR, `_rot` QUATERNION, `_mat` FLOAT4X4 | VEC3 / VEC4 / MAT4 f32 | itemSize 3 / 4 / 16 |
| `_edgeval` EDGE, `_str` STRING, `noprefix` | **нет** | — |
| `_tint` FLOAT_COLOR, `_btint` BYTE_COLOR | `_TINT` + ещё и `COLOR_n` (цветовой тип) | `_tint`, `color_n` |

[проверено]. Имя: только с «_» или «KHR_»; в glTF — ВЕРХНИМ регистром, в three —
нижним (загрузчик приводит неизвестные атрибуты к нижнему регистру [S5]). Исключение — PointCloud: регистр сохраняется
(`_size`) [проверено]. Для данных брать FLOAT/FLOAT_VECTOR: цветовые типы
запускают логику COLOR_n и баг §4.4.

```python
# Blender 5.2.2 — [проверено] (→ _WAVE, −0.5…0.5; в three geometry.attributes._wave, itemSize 1)
def add_float_attribute(ob, name="_wave"):
    me = ob.data
    a = me.attributes.new(name, "FLOAT", "POINT")               # имя с «_»; тип FLOAT/FLOAT_VECTOR (int → float всё равно)
    a.data.foreach_set("value", [v.co.z for v in me.vertices])
    return a                                                   # экспорт: export_attributes=True → _WAVE; three: geometry.attributes._wave
```

В шейдере three атрибут объявляется как `attribute float _wave;` (ShaderMaterial / `onBeforeCompile`) [не проверено: чтение
атрибута в GLSL не запускалось; наличие атрибута в геометрии проверено в E/26].

### 4.6. Модификаторы, export_apply и shape keys

| сцена (куб 12 треуг., E/07) | Blender (вьюпорт) | `export_apply=False` | `export_apply=True` |
|---|---|---|---|
| Subdivision `levels=1`, `render_levels=3` | 48 | 12 треуг. | **48** (уровень вьюпорта; рендер дал бы 768) |
| Subdivision `show_viewport=False` | 12 | 12 | 12 (не применён) |
| Mirror + Array ×3 + Solidify | 144 | 12 | 144 |
| shape key + Subdivision 1 | 48 | 12 / 1 морф | 48 / **0 морфов** (без предупреждения) |
| только shape key | 12 | 12 / 1 | 12 / 1 |
| сфера с 8 shape keys, без модификаторов (E/24) | — | 8 морфов | **8 морфов** |

[проверено]. Описание параметра в 5.2.40 честно предупреждает:
«Apply modifiers (excluding Armatures) — WARNING: prevents exporting shape keys» [S2]; в журнале экспорта предупреждения нет.

Правила:
1. Для веба `export_apply=True`; уровень Subdivision задавать в `levels` (вьюпорт), модификаторы держать видимыми во вьюпорте.
2. Морф-ассет: применить все модификаторы до создания shape keys, затем экспорт с любым `export_apply`; либо экспорт
   морф-объектов отдельным файлом с `export_apply=False` (пресет `anim_morph`, 04 §7).
3. Armature не применяется никогда — это скиннинг.
4. Обёртка агента B `bpyx.export_glb(apply_modifiers=True)` по умолчанию попадает в эту ловушку для объектов с модификаторами
   и shape keys [S24] — для морфов передавать `apply_modifiers=False`.

### 4.7. Geometry Nodes и инстансинг

| случай (E/08: 10×10 икосфер по сетке) | флаги | узлов | КБ | three |
|---|---|---|---|---|
| GN-инстансы | по умолчанию | 1 | 1.1 | базовая плоскость, GN потерян |
| то же | `export_apply` | 1 (без примитивов) | 0.2 | пусто, warning «Mesh has no primitives» |
| то же | `export_gn_mesh` | 101 | 23.3 | 101 `Mesh`, 101 вызов |
| то же | `gn_mesh` + `gpu_instances` | 2 | 12.7 | `InstancedMesh(100)` + плоскость, 2 вызова |
| то же | `gn_mesh` + `gpu_instances` + `apply` | **1** | **11.8** | `InstancedMesh(100)`, **1 вызов** |
| GN + Realize Instances | `apply` | 1 | **625** | 1 `Mesh`, 8000 треуг. |
| 100 связанных дубликатов под Empty | по умолчанию | 101 | 15.6 | 100 `Mesh` с общей геометрией, 100 вызовов |
| то же | `gpu_instances` | 1 | 11.9 | `InstancedMesh(100)`, 1 вызов |

[проверено]

```python
# Blender 5.2.2 — [проверено] (→ 1 узел, EXT_mesh_gpu_instancing, 100 экземпляров)
import bpy

def gn_scatter_object(name, mat, count=10, size=4.0):
    ng = bpy.data.node_groups.new(name + "_GN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    out = N.new("NodeGroupOutput")
    grid = N.new("GeometryNodeMeshGrid")
    grid.inputs["Size X"].default_value = size; grid.inputs["Size Y"].default_value = size
    grid.inputs["Vertices X"].default_value = count; grid.inputs["Vertices Y"].default_value = count
    ico = N.new("GeometryNodeMeshIcoSphere")
    ico.inputs["Radius"].default_value = 0.15; ico.inputs["Subdivisions"].default_value = 2
    setm = N.new("GeometryNodeSetMaterial"); setm.inputs["Material"].default_value = mat
    iop = N.new("GeometryNodeInstanceOnPoints")
    L.new(ico.outputs["Mesh"], setm.inputs["Geometry"])
    L.new(grid.outputs["Mesh"], iop.inputs["Points"])
    L.new(setm.outputs["Geometry"], iop.inputs["Instance"])
    L.new(iop.outputs["Instances"], out.inputs["Geometry"])   # без Realize Instances
    me = bpy.data.meshes.new(name)                             # базовый меш не важен: GN заменяет геометрию
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new("Scatter", "NODES").node_group = ng
    return ob
# экспорт: export_web(path, export_gn_mesh=True, export_gpu_instances=True)  (export_apply=True уже в WEB)
```

Ограничения:
- Инстансинг экспортёра: экземпляры — меши без детей, дети одного объекта, с общим mesh; вариации материалов теряются
  («Multiple materials might be omitted» в описании `export_gpu_instances`) [S1] [S2].
- `export_gn_mesh` помечен Experimental [S2]. Предупреждение «Mesh '…' has no primitives and will be omitted» у пустого базового
  меша — норма [проверено].
- Экспортёр пишет `EXT_mesh_gpu_instancing` только в `extensionsUsed`, не в `extensionsRequired`, хотя спецификация рекомендует
  required [S20]: просмотрщик без поддержки покажет один экземпляр. three r186 поддерживает: `TRANSLATION/ROTATION/SCALE` →
  матрицы `InstancedMesh`, `_COLOR_0` → `instanceColor`, прочие → `InstancedBufferAttribute`; для POINTS/LINES и SkinnedMesh
  инстансинг не строится [S5] [проверено].
- Выгода: 900 икосфер — 20–61 КБ против 1–24 МБ развёрнутой геометрии и 1 вызов (`03` §2) [проверено].

### 4.8. Кривые, текст, рёбра, точки

- CURVE, SURFACE, FONT экспортёр сам переводит в меш (`to_mesh`) и с `export_apply`, и без; фаска и выдавливание входят
  [проверено]. Руководство советует конвертировать заранее [S1] — для экспорта не
  обязательно, но нужно для контроля плотности.
- Текст «Hello 3D» (extrude 0.08, bevel 0.01): `resolution_u` 12 и `bevel_resolution` 4 → **9968 треуг., 251 КБ**;
  `resolution_u` 3 и `bevel_resolution` 1 → **1520 треуг., 45 КБ** [проверено].
  Надписи для веба дешевле делать HTML/SDF-текстом (агент F).
- Кривая без фаски и свободные рёбра без `use_mesh_edges` исчезают (warning «has no primitives»); с флагом → `LINES` →
  `LineSegments`. Свободные вершины — `use_mesh_vertices` → `POINTS` → `Points` с `PointsMaterial` 1 px без `sizeAttenuation`;
  материал — из первого слота [проверено].
- PointCloud (новый тип данных) экспортируется только при `use_mesh_vertices=True` и **требует атрибут `radius`**, иначе экспорт
  падает с `KeyError: 'radius'`; пишет `_RADIUS` и атрибуты с «_». Создание в 5.2: `pc = bpy.data.pointclouds.new(name)`,
  затем `pc.resize(n)` (у `new()` нет второго аргумента) [проверено].
- Для частиц в вебе лучше экспортировать позиции (атрибут или extras) и строить свой `Points`/`InstancedMesh` в JS [практика].

### 4.9. Трансформации, оси, единицы, origin

- Оси: (x, y, z) Blender → (x, z, −y) glTF для позиций, нормалей и касательных; `export_yup=True` обязателен для three [S4]
  [проверено].
- TRS узла берутся из мировых матриц: `matrix_parent_inverse` безопасен, неприменённый масштаб (2, 1, 0.5) даёт узел
  scale [2, 0.5, 1]; отрицательный масштаб раскладывается в scale [−1, −1, −1] + поворот 180°, three меняет порядок обхода
  граней при отрицательном детерминанте — изнанки нет (IoU 0.997) [проверено].
- Масштаб всё равно применять (`bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)` или `bpyx.apply_transforms(ob, location=False, rotation=False, scale=True)`; вызов только с `scale=True` применяет и location, и rotation — origin уезжает в ноль мира) до экспорта: физика, анимация масштаба и
  пивоты в JS работают от узла [практика].
- `scene.unit_settings.scale_length` игнорируется: 1 BU = 1 м. Сцена в сантиметрах (`scale_length=0.01`) даёт в three куб 100 м
  [проверено].
- Origin объекта = pivot в three: геометрия, смещённая от origin на 5 м, в JS вращается вокруг далёкой точки. Перед экспортом
  ставить origin туда, вокруг чего объект будет двигаться [проверено].
- Узлы в glTF отсортированы по именам (как в Outliner), а не по порядку создания [проверено].

## 5. Материалы: ядро glTF (Principled BSDF → pbrMetallicRoughness)

### 5.1. Как экспортёр 5.2.40 читает материал

- С 5.2 материал сначала «встраивается» через `bpy.types.InlineShaderNodes.from_material(mat)` (группы разворачиваются), кроме
  случаев с pointer-анимацией, группой «glTF Material Output» с Occlusion и `export_unused_textures` [S3].
- Для каждого канала экспортёр идёт **вверх** от сокета Principled через любые ноды до первой Image Texture и берёт её картинку
  как есть; ноды по дороге (Color Ramp, Hue/Saturation, Mix, Bump, Math, кроме распознанных фактор-связок) не вычисляются
  [S3] [проверено].
- Факторы распознаются в связках: константа в сокете; нода RGB/Value; Mix (RGBA, MULTIPLY, Factor 1) с константой; Math MULTIPLY
  с константой; Color Attribute/Attribute → множитель-вершинный цвет. Reroute и группы проходятся [S3].
- Сокет, подключённый к процедуре без картинки, получает значение по умолчанию glTF: base color [1,1,1], roughness 1,
  metallic 1 не пишется, если его нет [проверено].
- `export_materials="VIEWPORT"` пишет только Base Color, Metallic, Roughness из Viewport Display [S1].

### 5.2. Что распознаётся: материал, который переживает экспорт

Разрешённый набор нод: Principled BSDF; Image Texture; Normal Map (Tangent Space); Separate Color (ORM); Mix (RGBA,
MULTIPLY, Factor 1) и Math MULTIPLY с константой (факторы); Mapping POINT + UV Map/Texture Coordinate UV
(`KHR_texture_transform`); группа «glTF Material Output»; Volume Absorption (для volume); Emission, Background, Light Path,
Transparent BSDF, Mix Shader — только в unlit-связках (§6.3) [проверено].

```python
# Blender 5.2.2 / glTF-IO 5.2.40 — [проверено]
# (→ baseColorTexture, metallicRoughnessTexture и occlusionTexture — одна ORM-текстура, normalTexture.scale = normal_strength)
import bpy
from io_scene_gltf2.blender.com.material_helpers import create_settings_group, get_gltf_node_name


def gltf_output_node(mat):
    """Нода-группа «glTF Material Output»: сокеты Occlusion, Thickness, Dispersion, Iridescence Factor,
    Iridescence Thickness Minimum. Blender её не рендерит, экспортёр читает."""
    name = get_gltf_node_name()                                  # "glTF Material Output"
    group = bpy.data.node_groups.get(name) or create_settings_group(name)
    node = mat.node_tree.nodes.new("ShaderNodeGroup")
    node.node_tree = group
    return node


def pbr_material(name, base_path, orm_path, normal_path, normal_strength=1.0):
    mat = bpy.data.materials.new(name)          # 5.x: дерево нод с Principled BSDF создаётся сразу
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")

    def tex(path, colorspace):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = colorspace       # "sRGB" — цвет, "Non-Color" — данные
        return t

    base = tex(base_path, "sRGB")
    nt.links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
    orm = tex(orm_path, "Non-Color")                         # R = AO, G = roughness, B = metallic
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(orm.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    nt.links.new(sep.outputs["Red"], gltf_output_node(mat).inputs["Occlusion"])
    nrm = tex(normal_path, "Non-Color")
    nmap = nt.nodes.new("ShaderNodeNormalMap")               # только Tangent Space
    nmap.inputs["Strength"].default_value = normal_strength   # → normalTexture.scale
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat
```

Примечания к коду: экспорт выводит предупреждение «More than one shader node tex image used for a texture» — для ORM это
норма (одна картинка на два канала). Если Metallic и Roughness взяты из двух разных картинок, экспортёр сам упакует их в одну
MR-текстуру (перепаковка при экспорте, E/12 m10); ORM упаковывается в одну текстуру, только если все каналы берутся из
картинок одного размера [S3].

### 5.3. Текстуры: texCoord, сэмплер, KHR_texture_transform

- Interpolation Closest → `NEAREST` / `NEAREST_MIPMAP_NEAREST`; Extension EXTEND → `CLAMP_TO_EDGE`; MIRROR → `MIRRORED_REPEAT`
  [проверено].
- Mapping типа POINT (и TEXTURE, VECTOR) → `KHR_texture_transform`; вращение только по Z; NORMAL — пропуск с warning; TEXTURE
  инвертируется в TRS и может не сойтись (warning) [S3]. Проверено: scale (2, 3), rot Z 30°, offset → offset/repeat/rotation
  в three, ΔE 4.2 [проверено].
- three клонирует текстуру для каждого своего набора `texCoord`/transform; порядок T·R·S пересчитывается в `matrix`
  (`matrixAutoUpdate=false` при вращении) [S5].
- Если одна картинка используется двумя нодами с разными настройками, сэмплер берётся от первой ноды (warning) [S3].

### 5.4. Цветовые пространства

| карта glTF | как читает three r186 [S5] | что ставить на ноде Image Texture в Blender |
|---|---|---|
| `baseColorTexture`, `emissiveTexture` | `SRGBColorSpace` | sRGB |
| `sheenColorTexture`, `specularColorTexture` | `SRGBColorSpace` | sRGB |
| `normalTexture`, `metallicRoughnessTexture`, `occlusionTexture` | без пространства (линейные данные) | Non-Color |
| clearcoat*, transmission, thickness, iridescence*, anisotropy, specular (сила) | линейные | Non-Color |
| факторы (`baseColorFactor`, `emissiveFactor`), `COLOR_0` | линейный sRGB | — (цвета в Blender уже линейные) |

Экспортёр **не записывает** цветовое пространство ноды — байты картинки уходят как есть, смысл задаёт слот glTF. Поэтому
ошибка в Blender не «доезжает» до веба, а создаёт расхождение: Non-Color на base color → Blender бледнее three (ΔE 15.9);
sRGB на карте нормалей → в Blender искажён рельеф, в three верно (ΔE 7.3, SSIM 0.50); sRGB на roughness → Blender
линеаризует, three нет (ΔE 3.0) [проверено].

### 5.5. Альфа, прозрачность, двусторонность

Режим `alphaMode` с 4.2 определяется **нодами**, а не настройками материала [S3] [S1]:

| связка на входе Alpha | alphaMode | three r186 [S5] |
|---|---|---|
| не подключён, значение 1 | OPAQUE | — |
| Math ROUND(alpha) | MASK, cutoff 0.5 | `alphaTest = 0.5` |
| 1 − (alpha < c) (LESS_THAN + SUBTRACT) | MASK, `alphaCutoff = c` | `alphaTest = c` |
| alpha > c (устаревший вариант) | MASK | `alphaTest` |
| константа < 1 или картинка напрямую | BLEND | `transparent = true`, `depthWrite = false` |
| константа 0 | MASK 0.5 | — |

- `material.blend_method` в 5.2 ещё существует (по умолчанию HASHED), но на экспорт не влияет: Alpha 1 + `blend_method="BLEND"` →
  OPAQUE; Alpha 0.5 + `blend_method="OPAQUE"` → BLEND. `surface_render_method` (DITHERED/BLENDED) тоже не влияет;
  `material.shadow_method` удалён (`AttributeError`) [проверено] [S23].
- `doubleSided = not material.use_backface_culling`; culling в Blender по умолчанию выключен → почти все материалы уходят
  двусторонними; volume принудительно делает `doubleSided=false` [S3] [проверено].
- BLEND в three: `depthWrite=false` и сортировка по объектам — вложенная и самопересекающаяся прозрачность рисуется в неверном
  порядке (IoU 0.961, ΔE 7.8) — `04` §4 [проверено]. Для листвы и сеток — MASK, для стекла —
  transmission (§6.2).

```python
# Blender 5.2.2 — [проверено] (→ MASK с alphaCutoff 0.3; BLEND)
def alpha_from_texture(mat, image_node, mode="MASK", cutoff=0.5):
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    if mode == "BLEND":                                      # alphaMode BLEND
        nt.links.new(image_node.outputs["Alpha"], bsdf.inputs["Alpha"])
    elif cutoff == 0.5:                                      # alphaMode MASK, alphaCutoff 0.5
        r = nt.nodes.new("ShaderNodeMath"); r.operation = "ROUND"
        nt.links.new(image_node.outputs["Alpha"], r.inputs[0])
        nt.links.new(r.outputs[0], bsdf.inputs["Alpha"])
    else:                                                    # alphaMode MASK, alphaCutoff = cutoff: 1 − (alpha < cutoff)
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = cutoff
        sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[0].default_value = 1.0
        nt.links.new(image_node.outputs["Alpha"], lt.inputs[0])
        nt.links.new(lt.outputs[0], sub.inputs[1])
        nt.links.new(sub.outputs[0], bsdf.inputs["Alpha"])
```

### 5.6. Эмиссия

- Emission Color × Emission Strength: если какой-то компонент > 1, фактор нормируется на максимум, а множитель уходит в
  `KHR_materials_emissive_strength` → в three `emissiveIntensity` [S3] [проверено].
- Отдельная нода Emission имеет приоритет над входом Emission Principled; нода Emission без Principled → `baseColorFactor`
  [0, 0, 0, 1] + эмиссия (PBR-материал, не unlit) [S3] [проверено].
- Любой не-текстурный источник в Emission Color (атрибут, процедура) → `emissiveFactor` [1, 1, 1]: объект светится белым
  [проверено].
- Свечение в вебе видно как «светится» только с постобработкой bloom (агент F); сам материал не освещает соседей.
  `KHR_materials_emissive_strength` нельзя сочетать с unlit [S8].

### 5.7. Группа «glTF Material Output»

Всё, что glTF хранит вне Principled, задаётся сокетами этой группы: **Occlusion**, **Thickness** (по умолчанию 0),
**Dispersion** (0), **Iridescence Factor** (0), **Iridescence Thickness Minimum** (100) [S3]. Старое имя — «glTF Settings»;
экспортёр ищет группу по префиксу имени дерева без учёта регистра [S3]. В интерфейсе она появляется в Add → Output только
при включённой настройке аддона «Shader Editor Add-ons» [S1]; из скрипта — функцией аддона (код в §5.2, `gltf_output_node`)
[проверено].

- Blender группу не рендерит: AO из неё виден только в three (`aoMap` действует на непрямой свет — `02-baking.md` §4)
  [проверено].
- У Principled BSDF 5.2 нет входа Occlusion; модель по памяти пишет `bsdf.inputs["Ambient Occlusion"]` → KeyError.

### 5.8. Что теряется молча и что делать

| в Blender | что уходит | что делать |
|---|---|---|
| Color Ramp, Hue/Saturation, Bright/Contrast, Gamma, Invert после картинки | сырая картинка | запечь цвет (DIFFUSE COLOR) или поправить картинку |
| Mix картинки с процедурой или другой картинкой (кроме MULTIPLY на константу) | одна картинка | запечь |
| Noise, Voronoi, Wave, Musgrave-подобные, Gradient, Layer Weight, Fresnel | ничего (значение по умолчанию glTF) | запечь в текстуры (`02-baking.md` §2) |
| Bump (от картинки или процедуры) | высоты как `normalTexture` / ничего | запечь NORMAL или сделать карту нормалей |
| Texture Coordinate Generated/Object/Window | UV-развёртка | развернуть UV и запечь |
| Mix Shader двух BSDF | один BSDF | запечь или разделить на объекты с разными материалами |
| Diffuse, Glossy, Toon, Hair и прочие BSDF | материал без PBR (metal 1 / rough 1) | Principled BSDF |
| Subsurface, Diffuse Roughness, Thin Wall, Coat Tint, Coat IOR | ничего | запечь цвет / принять потерю |
| нода Ambient Occlusion | цвет ноды как фактор | запечь AO (`02-baking.md` §4) |
| эффекты EEVEE (Shader to RGB, Raytracing, SSR, объёмы мира) | ничего | постобработка в three (агент F) |

[проверено]. Валидатор Khronos эти потери не видит — ловит только
сравнение картинок (`gltf_diff.py`) и осмотр материалов (`gltf_web_inspect.py`) [проверено].

## 6. Расширения материалов и unlit

### 6.1. Principled BSDF 5.2 → KHR_materials_* → three r186

| вход Blender | glTF | three r186 (`MeshPhysicalMaterial`) | результат (E/13) |
|---|---|---|---|
| Transmission Weight | `KHR_materials_transmission.transmissionFactor` | `transmission` | да тонкостенное стекло (фон без преломления), как требует спецификация [S9] |
| IOR (≠ 1.5) | `KHR_materials_ior` — только при transmission, volume или specular; связанный сокет не экспортируется | `ior` | да x02; нет без transmission (x06) |
| Volume Absorption (Color, Density) + Thickness в группе | `KHR_materials_volume`: `attenuationColor`, `attenuationDistance = 1/Density`, `thicknessFactor` | `attenuationColor`, `attenuationDistance`, `thickness` | да x04; без группы нет (x05) |
| Dispersion в группе (при volume) | `KHR_materials_dispersion` | `dispersion` | да x07 (цветные края) |
| Specular IOR Level | `KHR_materials_specular.specularFactor = 2 × level`; при level > 0.5 избыток уходит в `specularColorFactor` | `specularIntensity`, `specularColor` | да x08–x10, ΔE 1.7 |
| Specular Tint | `specularColorFactor` | `specularColor` | да x09 |
| Coat Weight, Coat Roughness (≠ 0.03), Coat Normal ← Normal Map | `KHR_materials_clearcoat` (+ `clearcoatNormalTexture`) | `clearcoat`, `clearcoatRoughness` | да x11, ΔE 1.7 |
| Coat Tint, Coat IOR | в glTF нет (IOR покрытия фиксирован 1.5 [S14]) | белое покрытие | нет x12 |
| Sheen Weight, Sheen Tint, Sheen Roughness | `KHR_materials_sheen`: `sheenColorFactor = Tint`, `sheenRoughnessFactor`; **вес не умножается** | `sheen = 1`, `sheenColor` | да x13; нет x14 (вес 0.3 = вес 1) |
| Thin Film Thickness, Thin Film IOR + Iridescence Factor в группе | `KHR_materials_iridescence`: factor, `iridescenceIor`, `thicknessMaximum = Thin Film Thickness`, `thicknessMinimum` из группы (100) | `iridescence`, `iridescenceIOR`, `iridescenceThicknessRange` | ≈ x15 (оттенок отличается от Cycles); без группы нет (x16) |
| Anisotropic, Anisotropic Rotation | `KHR_materials_anisotropy`: strength, `rotation × 2π` рад | `anisotropy`, `anisotropyRotation` | ≈ x17: glTF тянет блик вдоль UV-касательной [S18], Blender по умолчанию — радиальная касательная |
| Emission Strength > 1 | `KHR_materials_emissive_strength` | `emissiveIntensity` | да x18, ΔE 1.0 |
| Subsurface*, Diffuse Roughness, Thin Wall, Weight | нет | — | нет |

[проверено]. Постобработка JSON в экспортёре: IOR пишется только при
transmission/volume/specular; volume — только при transmission; dispersion — только при volume; iridescence удаляется при
factor 0 или thicknessMaximum 0; пустые расширения выкидываются (кроме unlit) [S3].

Обход потерь:
- **Sheen Weight**: спецификация кодирует силу в `sheenColorFactor` (0 — слой выключен) [S13]; экспортёр пишет только Tint.
  Для веса < 1 задавать Sheen Weight = 1, а Sheen Tint = вес × цвет [документация: S13 + исходник S3; визуально не проверено].
- **Coat Tint**: glTF-покрытие бесцветное — оттенок переносить в Base Color или запекать [S14].
- **Anisotropy**: направление в glTF — касательная UV (атрибут `TANGENT` или производная) [S18]; UV развернуть так, чтобы U шёл
  вдоль нужных «штрихов» (для диска — полярная развёртка) [не проверено].
- Расширения переключают three на `MeshPhysicalMaterial` — шейдер дороже; `transmission` добавляет отдельный проход рендера
  сцены в текстуру. Компиляция `MeshPhysicalMaterial` с transmission в первом кадре заняла 387 мс против 38–88 мс у
  `MeshStandardMaterial` [проверено].
- EEVEE без Raytracing — плохой эталон для стекла, анизотропии и плёнки: сверять с Cycles (`gltf_diff.py --engine cycles`)
  [проверено].

### 6.2. Стекло, которое доезжает до three

```python
# Blender 5.2.2 / glTF-IO 5.2.40 — [проверено]
# (→ KHR_materials_transmission + volume + ior + dispersion); gltf_output_node() — из §5.2
import bpy

def glass_material(name, color=(0.2, 0.6, 1.0), density=2.0, thickness=0.5, ior=1.5, roughness=0.0, dispersion=0.0):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Transmission Weight"].default_value = 1.0     # → KHR_materials_transmission
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior                      # ≠ 1.5 → KHR_materials_ior
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")             # → attenuationColor, attenuationDistance = 1/Density
    va.inputs["Color"].default_value = (*color, 1.0)
    va.inputs["Density"].default_value = density
    nt.links.new(va.outputs["Volume"], out.inputs["Volume"])
    g = gltf_output_node(mat)
    g.inputs["Thickness"].default_value = thickness             # ≠ 0 → KHR_materials_volume (иначе тонкостенное стекло)
    g.inputs["Dispersion"].default_value = dispersion           # ≠ 0 → KHR_materials_dispersion (только вместе с volume)
    return mat
```

- Thickness — толщина объекта в метрах меша (0 = тонкостенный); меш для volume должен быть замкнутым [S10]. three берёт
  толщину константой по всей поверхности, поэтому толстое стекло в three темнее Cycles по краям
  [проверено].
- Стекло без вырезов — `alphaMode` OPAQUE: прозрачность — через transmission, не через Alpha; `alphaMode` в glTF — только «покрытие», MASK поверх transmission спецификация допускает (разбитое стекло) — в three r186 не проверено [S9].
- Метод рендера EEVEE для стекла — Dithered + Raytracing; это не влияет на экспорт [S23].

### 6.3. Unlit (KHR_materials_unlit → MeshBasicMaterial)

Распознаются четыре связки [S3] [проверено]:

| связка | glTF | ΔE |
|---|---|---|
| нода RGB (цвет) прямо в Surface выхода | unlit + `baseColorFactor` | 1.0 |
| Image Texture прямо в Surface | unlit + `baseColorTexture` | 1.3 |
| Mix Shader(Fac = Light Path «Is Camera Ray», Transparent BSDF, Emission(картинка)) | unlit + текстура (альфа — через Transparent) | 1.3 |
| Background → Surface | unlit + фактор | да |
| одна нода Emission(картинка) | **не unlit**: PBR с чёрной базой и эмиссией (отражения окружения остаются) | 1.3 по цвету |

```python
# Blender 5.2.2 — [проверено] (→ KHR_materials_unlit; в three MeshBasicMaterial)
import bpy

def unlit_material(name, image_path):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    nt.nodes.remove(next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"))
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(image_path, check_existing=True)
    nt.links.new(t.outputs["Color"], out.inputs["Surface"])     # цвет прямо в Surface → unlit, в three MeshBasicMaterial
    return mat
```

Unlit пишет metallic 0, roughness 0.9 (фолбэк для движков без расширения), без normal/occlusion/emissive [S3] [S15]. В three
`MeshBasicMaterial` использует только цвет, карту, `COLOR_0` и альфу [S5]. Это основной путь «запечённого света» —
`02-baking.md` §5 (ΔE 0.73 к Cycles).

## 7. Что делает GLTFLoader r186

### 7.1. Расширения

| расширение | three r186 | что нужно на странице |
|---|---|---|
| KHR_materials_{anisotropy, clearcoat, dispersion, emissive_strength, ior, iridescence, sheen, specular, transmission, unlit, volume}, EXT_materials_bump | ядро загрузчика | — |
| KHR_texture_transform, KHR_mesh_quantization, KHR_lights_punctual, EXT_mesh_gpu_instancing | ядро | — |
| EXT_texture_webp, EXT_texture_avif | ядро, без проверки поддержки браузером | браузер с WebP/AVIF |
| KHR_draco_mesh_compression | ядро + декодер | `setDRACOLoader(new DRACOLoader().setDecoderPath(…))`, иначе исключение «No DRACOLoader instance provided» |
| EXT_meshopt_compression, KHR_meshopt_compression | ядро + декодер | `setMeshoptDecoder(MeshoptDecoder)`; без него при required — исключение, без required — фолбэк-буфер |
| KHR_texture_basisu | ядро + транскодер | `setKTX2Loader(new KTX2Loader().setTranscoderPath(…).detectSupport(renderer))`; без него при required — исключение |
| KHR_animation_pointer, KHR_materials_variants, MSFT_texture_dds, NEEDLE_progressive, KHR_gaussian_splatting | отдельные плагины (`register`) | pointer-каналы ядро пропускает: `if (target.node === undefined) continue;` |
| неизвестные расширения | `userData.gltfExtensions` | — |

[S5] [S21]; поведение pointer проверено: клипы 0 с без треков [проверено].
Спецификация pointer прямо разрешает загрузчикам без поддержки игнорировать каналы без `node` [S21].

```js
// three r186 — [проверено: 99-raw/experiments/E/26-doc-snippets/js_check.py, ../../scripts/3d/gltf_load_bench.py]
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {KTX2Loader} from 'three/addons/loaders/KTX2Loader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';

const renderer = new THREE.WebGLRenderer({antialias: true});
const scene = new THREE.Scene();
const CDN = 'https://cdn.jsdelivr.net/npm/three@0.186.0/examples/jsm/libs/';
const loader = new GLTFLoader()
  .setDRACOLoader(new DRACOLoader().setDecoderPath(CDN + 'draco/gltf/'))
  .setKTX2Loader(new KTX2Loader().setTranscoderPath(CDN + 'basis/').detectSupport(renderer))
  .setMeshoptDecoder(MeshoptDecoder);
const gltf = await loader.loadAsync('model.glb');
scene.add(gltf.scene);
```

В продакшене декодеры (`libs/draco/gltf/`, `libs/basis/`) выкладывать рядом с сайтом, а не с CDN: холодная загрузка
wasm-декодера Draco с jsDelivr — 0.28–0.45 с, транскодера Basis — ≈ 0.6 с (`03` §2, §3) [проверено].

### 7.2. Материалы и карты

- Тип: `MeshStandardMaterial` по умолчанию; `MeshPhysicalMaterial`, если есть clearcoat, dispersion, iridescence, sheen,
  transmission, volume, ior, specular, bump или anisotropy; unlit → `MeshBasicMaterial` [S5].
- Нет `pbrMetallicRoughness` → metalness 1, roughness 1 (умолчание спецификации); примитив без материала →
  `DefaultMaterial`: белый, metalness 1, roughness 1, **FrontSide** [S5] [проверено].
- `metallicRoughnessTexture` назначается и в `roughnessMap` (G), и в `metalnessMap` (B); `occlusionTexture` → `aoMap`
  (`aoMapIntensity = strength`), R-канал; карта на `texCoord > 0` — клон текстуры с `channel = texCoord` [S5].
- `alphaMode` BLEND → `transparent = true` и `depthWrite = false`; MASK → `alphaTest = alphaCutoff ?? 0.5`; `doubleSided` →
  `DoubleSide` [S5] [проверено].
- Есть `COLOR_0` → клон материала с `vertexColors = true`; нет `NORMAL` → `flatShading = true`; нет `TANGENT` при карте
  нормалей → касательные по производным и `normalScale.y *= −1` (клон материала) [S5].
- Текстуры: `ImageBitmapLoader` (кроме Safari < 17 и Firefox < 98), `flipY = false`, фильтр `LinearMipmapLinear`, wrap Repeat,
  мипмапы генерируются для несжатых; ошибка загрузки картинки → `console.error("THREE.GLTFLoader: Couldn't load texture …")`,
  материал без карты (белый), модель грузится [S5] [проверено].
- Память: любая JPEG/PNG/WebP/AVIF в GPU — RGBA8 + мипмапы: 2048² = 21.3 МБ; KTX2 остаётся сжатой (5.3 МБ) — `03` §3
  [проверено].

### 7.3. Узлы, меши, имена

- Узел с одним примитивом = сам `Mesh`; узел с несколькими примитивами (материалами) → `Group` с дочерними `Mesh` — один draw
  call на примитив [S5]. Объект Blender с тремя материалами = три вызова.
- Общий mesh у нескольких узлов → разные `Object3D` с общими геометрией и материалом [S5].
- Имена проходят `PropertyBinding.sanitizeNodeName` (пробел → «_», удаляются `[ ] . : /`), дубликаты получают `_1`, `_2`;
  исходное имя — в `userData.name` [S5] [проверено].
- После `gltf-transform optimize` (квантование) у анимированного или родительского меша появляется дочерний узел: имя
  `hero_orb` получает `Object3D`, а сам меш — `hero_orb_1`; после `join/flatten` и gltfpack без `-kn` имена теряются
  («Mesh016», «mesh_0») — `04` §7 [проверено].

## 8. Свет и камеры

### 8.1. Свет: KHR_lights_punctual

Пересчёт мощности в экспортёре (lights.py, `PBR_WATTS_TO_LUMENS = 683`) [S4]:

| источник Blender | SPEC «Standard» (умолчание) | COMPAT «Unitless» | RAW |
|---|---|---|---|
| Sun, Вт/м² | ×683 → люкс | как есть | как есть |
| Point, Spot, Вт | W/(4π) × 683 → кандела | W/(4π) | W |
| Area, мир | не экспортируются: «WARNING: Unsupported light source AREA» | — | — |

Везде × 2^exposure и × цвет (× температура, если включена); Spot: `outerConeAngle = spot_size/2`,
`innerConeAngle = outer·(1 − spot_blend)`; `range` — только при `use_custom_distance` [S4].

| проверка (пол альбедо 0.5, чистый Ламберт, E/14) | Blender EEVEE | three SPEC | three COMPAT | three RAW |
|---|---|---|---|---|
| Sun 3 Вт/м², центр | 0.477 | 1.0 (пересвет) | **0.479** | 0.479 |
| Point 50 Вт, профиль 0 / 0.44 / 0.94 / 1.44 м | 0.156 / 0.121 / 0.061 / 0.028 | 1.0 везде | **0.159 / 0.123 / 0.064 / 0.031** | ×4π |
| Spot 50 Вт, профиль | 0.156 / 0.121 / 0.018 / 0 | пересвет | **0.159 / 0.123 / 0.008 / 0** | ×12.6 |

[проверено: 99-raw/experiments/E/14-lights, E/26-doc-snippets (солнце 3 → 3; точка 50 Вт → 3.979)].

- three r186 берёт `intensity` как есть; point/spot: `distance = range || 0` (без отсечки), `decay = 2`; spot: `angle = outer`,
  `penumbra = 1 − inner/outer`; направление — −Z узла [S5] [S7]. Край пятна прожектора в three другой (0.008 против 0.018 на
  1.44 м) — кривые penumbra не совпадают [проверено].
- Почему на сайтах свет ставят кодом или запекают: Area и HDRI-мир не экспортируются; окружение для металлов нужно в любом
  случае (`scene.environment`, `04` §4); тени, `RectAreaLight`, интенсивность под тонмаппинг страницы настраиваются в JS; запечённый
  свет даёт точное совпадение с Cycles (`02-baking.md` §5) [проверено].

### 8.2. Камеры

| камера Blender (E/15) | glTF | three r186 |
|---|---|---|
| lens 50, sensor 36, рендер 1920×1080 | perspective `yfov` 0.3996 рад (22.9°), `aspectRatio` 1.778, `znear/zfar` = clip | `PerspectiveCamera(fov 22.9°)` |
| то же, рендер 1080×1920 | `yfov` 0.691 (39.6°), `aspectRatio` 0.5625 | — |
| ortho_scale 4, 16:9 | orthographic `xmag` 2, `ymag` 1.125 | `OrthographicCamera` |
| DOF (f/1.4), shift_x 0.1 | не экспортируются | — |
| панорамная | не экспортируется | — |

[проверено]. `yfov` пересчитывается по `sensor_fit` и соотношению сторон рендера [S4];
three создаёт `PerspectiveCamera(yfov в градусах, aspectRatio || 1, znear || 1, zfar || 2e6)` [S5]. На странице
`camera.aspect` задаётся по размеру canvas; вертикальный FOV остаётся фиксированным, поэтому на узком экране по бокам
обрезается больше, чем в Blender [практика]. Камеры по умолчанию не экспортируются (`export_cameras=False`).

## 9. Анимация

Глубокая анимация — агент H (волна 2); здесь контракт на 17 случаях E/15 и сквозной проверке E/24, E/26.

### 9.1. Какие действия становятся клипами

| режим `export_animation_mode` | что экспортируется (сцена: действие «Jump» в NLA-дорожке + активное «Slide») |
|---|---|
| `ACTIONS` (умолчание) | 2 клипа: Jump (30 ключей), Slide (60): активное действие + каждое действие в NLA-дорожке |
| `NLA_TRACKS` | 1 клип: только дорожки, активное действие не попало; `export_force_sampling` принудительно включён |
| `SCENE` | 1 клип «Box» — сцена, как её видно во вьюпорте (полное запекание) |
| `ACTIVE_ACTIONS` | 1 клип «Animation» — активные действия всех объектов слиты |
| действие только с fake user | 0 клипов |

[проверено] [S1]. С 4.4 действия «слотовые» (слои → полосы → channelbag): у
`Action` нет `fcurves`, кривые читаются через `strip.channelbag(slot).fcurves` [проверено].

```python
# Blender 5.2.2 — [проверено] (→ клипы Jump и Slide; three: AnimationClip.findByName)
def stash_action(ob, clip_name):
    """Текущее действие объекта → NLA-дорожка clip_name; объект освобождается для следующего действия."""
    ad = ob.animation_data
    act = ad.action
    act.name = clip_name                                       # имя клипа в glTF = имя действия
    track = ad.nla_tracks.new(); track.name = clip_name
    track.strips.new(clip_name, int(act.frame_range[0]), act)
    ad.action = None


def key_location(ob, keys):
    for frame, loc in keys:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame)

# key_location(hero, [(1, (0, 0, 0)), (30, (0, 0, 1)), (60, (0, 0, 0))]); stash_action(hero, "Jump")
# key_location(hero, [(1, (0, 0, 0)), (60, (2, 0, 0))]);                 stash_action(hero, "Slide")
# export_web(path, export_animations=True, export_animation_mode="ACTIONS", export_anim_slide_to_zero=True)
```

```js
// three r186 — [проверено] (Jump 1.967 с; на половине y = 0.998)
const mixer = new THREE.AnimationMixer(gltf.scene);
const jump = THREE.AnimationClip.findByName(gltf.animations, 'Jump');
const action = mixer.clipAction(jump);
action.setLoop(THREE.LoopOnce, 1); action.clampWhenFinished = true; action.play();
// в цикле рендера: mixer.update(clock.getDelta());
```

### 9.2. Сэмплирование, время, констрейнты

- `export_force_sampling=True` (умолчание): Bezier → LINEAR, ключ на каждый кадр (60 ключей на 2 с); `export_frame_step=2` → 30.
  `export_force_sampling=False` → CUBICSPLINE с исходными ключами (2 ключа), three проигрывает своим интерполятором с формой
  Безье [проверено]. При `force_sampling=False` экспортёр принудительно выключает
  `export_def_bones` и `export_bake_animation` [S2].
- Время glTF = кадр / fps: клип с кадра 1 начинается на 1/30 с; `export_anim_slide_to_zero=True` сдвигает к 0 (клип кадров
  1–60 = 1.967 с) [проверено].
- Вращение 0→360° в сэмплированных кватернионах сохраняет полный оборот [проверено].
- Констрейнты (Child Of, Follow Path, Track To) и драйверы без `export_bake_animation=True` не экспортируются: анимирован
  только родитель-пустышка, объект стоит; с запеканием — по ключу на кадр [проверено].
- Неанимированные каналы кости уходят STEP с 2 ключами [проверено].
- Лёгкий файл: `export_optimize_animation_size=True` (умолчание, удаляет повторяющиеся ключи), затем `gltf-transform resample`
  (`03` §5).

### 9.3. Морфы, скиннинг, pointer

- Shape keys с ключами → `weights` + `mesh.extras.targetNames` → `morphTargetInfluences` и `morphTargetDictionary`
  ({Tall, Wide}); морфы — дельты POSITION/NORMAL (`export_morph_normal`), `morphTargetsRelative = true` [S5]
  [проверено]. Условие — §4.6 (нет модификаторов или нет apply).
- Арматура + модификатор Armature → `skin`, клип, `SkinnedMesh` + `Bone`; валидатор предупреждает
  `NODE_SKINNED_MESH_NON_ROOT` (меш — ребёнок арматуры) — норма для Blender [проверено].
- Анимация цвета материала, мощности света, параметров камеры возможна только как `KHR_animation_pointer`: режим SCENE или
  NLA_TRACKS + `export_pointer_animation=True` (в ACTIONS флаг принудительно выключается) [S2]. Экспорт записывает каналы
  `/materials/0/pbrMetallicRoughness/baseColorFactor` и `/extensions/KHR_lights_punctual/lights/0/intensity`, но three r186
  создаёт клипы длительностью 0 без треков [проверено]. Решение — анимировать такие
  свойства кодом (GSAP, uniform, `AnimationMixer` по своему треку) или плагин `@needle-tools/three-animation-pointer`
  (7 зв., последний коммит 2026-06-17 — [не проверено]).

### 9.4. Поза покоя и кадр экспорта

Экспортёр перед сбором делает `scene.frame_set(0)` (если не `export_current_frame`), статичные трансформации и поза покоя
берутся с кадра 0, а не с текущего [S3]; для клипа с кадра 10 времена 0.333–2.0 с [проверено].
Если кадр 0 не является «правильной» позой (объект вне сцены, свёрнутая арматура) — модель на странице без анимации
окажется в этой позе. `export_rest_position_armature=True` берёт для скелета позу покоя арматуры [S2].

## 10. Данные для JS: extras, имена, поиск узлов

- `export_extras=True`: custom properties объекта → `node.extras` → `object.userData`; данных меша → `mesh.extras` →
  сливаются в `userData` того же `Mesh`; материала → `material.userData`; камеры (данные + объект) → слиты; сцены →
  `gltf.scene.userData` (только при экспорте всей сцены; при `collection=…` — свойства коллекции, свойства сцены не пишутся, I/03). Типы сохраняются: строка, число, bool, список, вложенный dict [проверено].
- Имена (без коллизий; при совпадении после санитизации один из узлов получает `_1` — может «правильный», `getObjectByName` найдёт не тот; уникальность проверять `names_for_js()`, `../02-blender-workflow/01-scene-organization-naming-units.md` §8.2): «Cube.001» → «Cube001», «My Object» → «My_Object», «Obj[1]» → «Obj1», «a:b» → «ab», «Кнопка/Главная» →
  «КнопкаГлавная»; кириллица остаётся [проверено].
- Правило: имена объектов — латиница, цифры и «_», без точек (`hero_body`, `btn_main`): тогда имя одинаково в Blender, glTF и JS.

```js
// three r186 — [проверено]
const hero = gltf.scene.getObjectByName('hero_orb');       // Mesh; userData = {name: 'hero_orb', hotspot: 'buy', price: 199}
const dot = gltf.scene.getObjectByName('Cube001');         // в Blender объект назывался «Cube.001»
let byOriginal = null;
gltf.scene.traverse(o => { if (o.userData.name === 'Cube.001') byOriginal = o; });
const wave = dot.geometry.attributes._wave;                // атрибут «_wave» (export_attributes=True), itemSize 1
```

После постобработки с квантованием имя может принадлежать узлу-обёртке, а меш быть его ребёнком (§7.3): искать меш через
`obj.traverse(o => o.isMesh && …)`.

## 11. Картинки и сжатие внутри экспортёра

Подробно — `03-compression-textures-budgets.md`; здесь — что умеет сам экспортёр 5.2.40.

| настройка (Camera_01, 9 JPEG 2048², E/16) | GLB | время экспорта | результат |
|---|---|---|---|
| `export_image_format="AUTO"` | 6.19 МБ | 0.16 с | JPEG скопированы **байт в байт** |
| `"JPEG"`, quality 75 / 50 | 6.19 МБ | 0.14–0.16 с | те же байты: качество действует только при перекодировании |
| `"WEBP"`, quality 75 | **2.69 МБ (−57 %)** | 2.07 с | `EXT_texture_webp` в **required**, ΔE 0.53 к AUTO в three |
| `"WEBP"`, quality 90 | 4.90 МБ | 2.32 с | ΔE 0.42 |
| AUTO + `export_image_add_webp` | **8.02 МБ** | 2.0 с | JPEG + WebP; three грузит WebP, JPEG — мёртвый груз (+30 %) |
| `"NONE"` | 0.86 МБ | 0.02 с | материалы без карт |
| `GLTF_SEPARATE` + `export_keep_originals` | .gltf + .bin | 0.02 с | пути ведут вне папки экспорта |

[проверено]. `export_image_format="PNG"` в 5.2 нет (`TypeError: … not found in
('AUTO', 'JPEG', 'WEBP', 'NONE')`); `export_jpeg_quality` принимается ради совместимости, актуальный — `export_image_quality`
[проверено]. Экспортёр не меняет разрешение текстур; запечённые и сгенерированные картинки
(без файла) пишет PNG [проверено].

Сжатие геометрии в экспортёре (E/17, Suzanne 252k треуг., сырой GLB 7.1 МБ):
- Draco (`export_draco_mesh_compression_enable`, уровень 6, квантование 14/10/12/10/12): 383 КБ, но декодирование 57 мс
  (тёплый старт) и 282–450 мс (холодный, с загрузкой wasm), в GPU снова float32 7.2 МБ; морфы не сжимает (1.10 → 0.98 МБ).
- Meshopt (`export_meshopt_compression_enable`, `EXT_`/`KHR_meshopt_compression`): **без квантования** — 2.2 МБ против
  0.82 МБ у `gltfpack -cc` и 1.25 МБ у `gltf-transform meshopt`.
- Оба флага сразу экспортёр не запрещает (TODO в исходнике): в required оба расширения, примитив сжат Draco — файл требует
  оба декодера [проверено].
- `export_use_gltfpack=True` вызывает внешний gltfpack: путь к бинарнику берётся из настройки аддона `gltfpack_path_ui`
  (без неё панель скрыта), результат пишется в подпапку `gltfpacked/`, по умолчанию передаётся `-noq` (квантование выключено!),
  ошибка — только строка в журнале «Calling gltfpack was not successful» [S3] [документация: исходник; запуском из экспортёра не проверено].

Вывод: экспортёр отдаёт «сырой» GLB (`AUTO`, без сжатия), постобработка делает остальное — команды в `03` §4 и пресеты в `04` §7.

## Частые ошибки

Ошибки агентов и нейросетей, пишущих код по памяти (Blender 2.8–3.x, three r1xx до 2023), и что на них отвечают 5.2.2 / r186:

1. `bpy.ops.export_scene.gltf(export_selected=True)` → `TypeError: … keyword "export_selected" unrecognized`; в 5.2 —
   `use_selection` [проверено].
2. `export_colors=True` → тот же `TypeError`; в 5.2 — `export_vertex_color="MATERIAL"` + `export_all_vertex_colors=False`
   [проверено].
3. `export_format="GLTF_EMBEDDED"`, `export_image_format="PNG"` → `TypeError` (enum) [проверено].
4. `mesh.use_auto_smooth = True`, `mesh.calc_normals_split()` → `AttributeError` (удалены в 4.1); замена —
   `set_sharp_from_angle` / `shade_smooth_by_angle` [проверено] [S22].
5. `bpy.ops.object.shade_auto_smooth()` без `export_apply=True`: модификатор «Smooth by Angle» не применяется, острые рёбра
   в вебе пропадают (64 нормали вместо 34) [проверено].
6. `bsdf.inputs["Specular"]`, `["Subsurface"]`, `["Clearcoat"]`, `["Sheen"]`, `["Transmission"]`, `["Emission"]` → `KeyError`;
   в 4.0+ — «Specular IOR Level», «Subsurface Weight», «Coat Weight», «Sheen Weight», «Transmission Weight», «Emission Color»
   [проверено].
7. Прозрачность через `material.blend_method = "BLEND"` — на `alphaMode` не влияет; нужна связка нод (§5.5); `shadow_method`
   → `AttributeError` [проверено].
8. Экспорт с умолчаниями: модификаторы не применены, extras не записаны, скрытые объекты попали в файл, свет и камеры
   пропали — все четыре ошибки дают валидный GLB без предупреждений [проверено].
9. `export_apply=True` для объекта с shape keys и модификаторами → морфы исчезают молча; `morphTargetDictionary` в three пустой
   [проверено].
10. Процедурный материал (Noise → Color Ramp → Base Color, Bump от Noise) «как есть» → белый гладкий объект в вебе (ΔE 23.5);
    запекать [проверено].
11. Bump-нода для рельефа от картинки → высоты уезжают в `normalTexture` (ΔE 8.9) [проверено].
12. Смешивание двух материалов через Mix Shader → в файле один из них [проверено].
13. AO подключают в несуществующий вход Principled или умножают в Base Color: первое — `KeyError`, второе — AO действует и на
    прямой свет и дублирует `aoMap`; правильно — «glTF Material Output».Occlusion (§5.7).
14. Одна нода Emission для «плоского» вида → PBR-материал с отражениями, а не unlit (§6.3) [проверено].
15. Свет экспортируется с умолчанием SPEC → сцена в three белая (×683) [проверено].
16. `scene.unit_settings.scale_length` для масштаба экспорта → игнорируется; модель в 100 раз больше [проверено].
17. Анимация цвета/света в Blender в расчёте, что three её проиграет → клип 0 с (§9.3) [проверено].
18. Действия хранятся только с fake user (Action Editor без назначения) → в файле нет анимации [проверено].
19. `use_selection=True` в фоновом скрипте без явного выделения → пустой файл 132 байта, FINISHED [проверено].
20. JS: `scene.getObjectByName('Cube.001')` → `undefined` (имя «Cube001») [проверено].
21. JS: сжатый файл без `setDRACOLoader`/`setMeshoptDecoder`/`setKTX2Loader` → исключение при загрузке [S5].
22. JS: ожидание, что lightMap придёт из glTF: в glTF нет слота lightMap — карта назначается кодом, `channel = 1`,
    `lightMapIntensity = Math.PI` (`02-baking.md` §5) [проверено].
23. Пятый UV-слой под текстуру → `'uv4' : undeclared identifier`, объект невидим [проверено].
24. Цвет вершин при двух цветовых атрибутах и умолчаниях → белый объект [проверено].
25. `bpy.data.pointclouds.new("PC", 500)` → `TypeError`; в 5.2 — `new(name)` + `resize(n)`; PointCloud без атрибута `radius` —
    экспорт падает [проверено].
26. Проверка результата только валидатором: он не видит ни одной смысловой потери из списка выше [проверено].

## Чек-лист

Геометрия и объекты:
- [ ] Экспорт `GLB`, `export_yup=True`? Модель в three стоит, а не лежит?
- [ ] `export_apply=True` (или модификаторов нет)? Уровень Subdivision задан в `levels` (вьюпорт)?
- [ ] У объектов с shape keys нет модификаторов (или экспорт без apply) — `morphTargetDictionary` в three не пустой?
- [ ] Жёсткие рёбра заданы данными (`set_sharp_from_angle`), а не модификатором без apply?
- [ ] Число вершин glTF (не Blender) в бюджете; flat-шейдинг только где нужен?
- [ ] UV-слоёв ≤ 2; текстуры на UV0/UV1; у нетекстурных мешей UV не экспортируются?
- [ ] Цвет вершин подключён в Base Color, `export_all_vertex_colors=False`?
- [ ] Повторяющиеся объекты — `InstancedMesh` (GN + `export_gn_mesh` + `export_gpu_instances` или связанные дубликаты)?
- [ ] Масштаб применён, сцена в метрах (`scale_length = 1`), origin стоит в точке вращения?
- [ ] В файл не попали скрытые и вспомогательные объекты (`use_renderable`, `use_visible`, `collection=` или `glTF_not_exported`)?

Материалы:
- [ ] Каждый материал — Principled BSDF + Image Texture (+ Normal Map, Separate Color, факторы) без процедур и Mix Shader?
- [ ] Цветовые карты в sRGB, данные в Non-Color (иначе Blender и веб разойдутся)?
- [ ] Рельеф — Normal Map (Tangent), не Bump?
- [ ] Альфа задана нодами; BLEND только там, где нужна полупрозрачность, иначе MASK или OPAQUE?
- [ ] `use_backface_culling=True` у замкнутых мешей?
- [ ] Occlusion/Thickness/Dispersion/Iridescence — через группу «glTF Material Output»?
- [ ] Coat Tint, Sheen Weight < 1, Subsurface не несут смысл, который пропадёт?
- [ ] «Плоские» материалы собраны unlit-связкой, а не одной нодой Emission?

Свет, анимация, данные:
- [ ] Свет не экспортируется (ставится кодом) или экспортируется в COMPAT?
- [ ] Каждое нужное действие назначено или лежит в своей NLA-дорожке; fake-user-действий нет?
- [ ] Констрейнты и драйверы запечены (`export_bake_animation=True`)?
- [ ] Анимация материалов и света перенесена в JS (pointer three не проигрывает)?
- [ ] Кадр 0 — правильная поза покоя?
- [ ] `export_extras=True`, имена объектов без точек и пробелов, JS находит узлы по имени?
- [ ] Результат проверен в three: `gltf_web_inspect.py` (материалы, клипы, userData) и `gltf_diff.py` (ΔE ≤ 3.5, IoU ≥ 0.99)?

## Открытые вопросы и противоречия

1. **Руководство против кода (iridescence)**: руководство 5.2 связывает «Thickness Maximum» с сокетом Thickness группы, а «Factor» —
   с Thin Film Thickness Principled [S1]; код 5.2.40 берёт Factor из «Iridescence Factor» группы, максимум — из Thin Film
   Thickness Principled, минимум — из группы [S3]. Эксперимент подтвердил код (x15: `thicknessMaximum` 500 = Thin Film Thickness)
   [проверено]. Руководство устарело.
2. **Баг COLOR_0 при ≥ 2 цветовых атрибутах** (5.2.40) — найден по коду и эксперименту; есть ли issue в glTF-Blender-IO, не
   проверялось.
3. **Sheen Weight не умножается в цвет** (подтверждено X/02: вес 0,5 + оттенок (1,0,0) → `sheenColorFactor` (1,0,0); обход «вес 1, Tint = вес × цвет» проверен D2/03, ΔE 2,2–2,7) — по спецификации [S13] вес закодирован в `sheenColorFactor`; это похоже на ошибку
   экспортёра.
4. **EXT_mesh_gpu_instancing не в extensionsRequired** — спецификация рекомендует required [S20]; как поведут себя model-viewer,
   Babylon.js и Needle — не проверялось (только three r186).
5. **Анизотропия**: как в Blender задать касательную, совпадающую с UV-касательной glTF (нода Tangent → UV Map), и совпадёт ли
   картинка — не проверено.
6. **IBL Blender против three**: на плоских светлых поверхностях под студийным HDRI EEVEE светлее three на ≈ 13 L*
   (E/20); причина найдена D2/01: EEVEE выносит яркое из HDRI в «солнце» (`world.sun_threshold` = 10) — для сравнений Cycles или `sun_threshold = 0` (`../06-materials-lighting-render/03-render-engines-color.md` §3).
7. **AgX**: реализации в Blender и three различаются (three светлее на 3,4–3,7 L*: степень 2,2 против 2,4 у Blender, D2/01) — для совпадения брать Standard/None или
   Khronos PBR Neutral.
8. **Плагин KHR_animation_pointer** для three (needle-tools) — не проверялся; репозиторий маленький (7 зв.).
9. **Collection Exporters** (экспортёр как свойство коллекции, `at_collection_center`), `export_shared_accessors`,
   `export_hierarchy_flatten_objs`, запуск gltfpack из экспортёра — в 5.2.40 есть, не проверены.
10. **Только Chromium на Linux/Mesa**: Safari/iOS (ImageBitmap, WebP/AVIF, ASTC), Windows (ANGLE D3D11) не проверялись.

## Источники

- [S1] Blender Foundation. Blender 5.2 Manual — glTF 2.0 (Import/Export). 2026. https://docs.blender.org/manual/en/5.2/addons/import_export/scene_gltf2.html — официальное описание экспортёра 5.2; прочитано целиком (1029 строк); раздел iridescence расходится с кодом.
- [S2] Khronos Group. glTF-Blender-IO v5.2.40, `io_scene_gltf2/__init__.py` (2313 строк) в составе Blender 5.2.2 (`scripts/addons_core/io_scene_gltf2`). https://github.com/KhronosGroup/glTF-Blender-IO (1661 зв., последний push 2026-09-21) — параметры, умолчания, зависимости флагов; первоисточник.
- [S3] glTF-Blender-IO v5.2.40: `blender/exp/export.py`, `material/materials.py`, `pbr_metallic_roughness.py`, `search_node_tree.py`, `unlit.py`, `material/extensions/*.py`, `com/material_helpers.py` — чтение нод, alphaMode, unlit, расширения, группа «glTF Material Output»; прочитаны целиком.
- [S4] glTF-Blender-IO v5.2.40: `blender/exp/primitive_extract.py` (1684 строки), `conversion.py`, `attribute_utils.py`, `lights.py`, `light_spots.py`, `cameras.py`, `pointcloud.py` — вершины, UV, цвета, атрибуты, свет, камеры; прочитаны целиком.
- [S5] mrdoob / three.js r186. `examples/jsm/loaders/GLTFLoader.js` (4925 строк), jsDelivr three@0.186.0. https://github.com/mrdoob/three.js (115 767 зв., push 2026-09-22) — что создаёт загрузчик; прочитан целиком.
- [S6] three.js r186. `DRACOLoader.js` (772), `KTX2Loader.js` (1276), `libs/meshopt_decoder.module.js` (196) — декодеры; прочитаны.
- [S7] Khronos. KHR_lights_punctual (Ratified). https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_lights_punctual (репозиторий 7846 зв., push 2026-09-21) — единицы (кд, лк), конусы, range.
- [S8] Khronos. KHR_materials_emissive_strength. https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_emissive_strength — множитель эмиссии, несовместим с unlit.
- [S9] Khronos. KHR_materials_transmission. …/Khronos/KHR_materials_transmission — тонкостенная прозрачность, alphaMode OPAQUE.
- [S10] Khronos. KHR_materials_volume. …/Khronos/KHR_materials_volume — thickness, attenuation, замкнутый меш.
- [S11] Khronos. KHR_materials_ior. …/Khronos/KHR_materials_ior — умолчание 1.5.
- [S12] Khronos. KHR_materials_specular. …/Khronos/KHR_materials_specular — specularFactor, specularColorFactor.
- [S13] Khronos. KHR_materials_sheen. …/Khronos/KHR_materials_sheen — sheenColorFactor как сила и цвет.
- [S14] Khronos. KHR_materials_clearcoat. …/Khronos/KHR_materials_clearcoat — покрытие без цвета, IOR 1.5.
- [S15] Khronos. KHR_materials_unlit. …/Khronos/KHR_materials_unlit — только base color; фолбэк metallic 0, roughness > 0.5.
- [S16] Khronos. KHR_texture_transform. …/Khronos/KHR_texture_transform — offset/rotation/scale, порядок T·R·S.
- [S17] Khronos. KHR_materials_dispersion (2024). …/Khronos/KHR_materials_dispersion — 20/Abbe, только с volume.
- [S18] Khronos. KHR_materials_anisotropy. …/Khronos/KHR_materials_anisotropy — направление по касательной, rotation против часовой от tangent.
- [S19] Khronos. KHR_materials_iridescence. …/Khronos/KHR_materials_iridescence — factor, IOR 1.3, толщина 100–400 нм.
- [S20] EXT_mesh_gpu_instancing (Vendor). https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Vendor/EXT_mesh_gpu_instancing — TRS-атрибуты экземпляров; «should» в extensionsRequired.
- [S21] Khronos. KHR_animation_pointer. …/Khronos/KHR_animation_pointer — JSON-указатели; каналы без `node` игнорируются загрузчиками без поддержки.
- [S22] Blender Foundation. Blender 4.1 Release Notes — Modeling. https://developer.blender.org/docs/release_notes/4.1/modeling/ — Auto Smooth заменён модификатором-ассетом; Shade Smooth by Angle.
- [S23] Blender Foundation. Blender 4.2 LTS — EEVEE migration. https://developer.blender.org/docs/release_notes/4.2/eevee_migration/ — Blend Mode → Render Method, Shadow Mode удалён.
- [S24] Агент B, волна 1. `99-raw/reports/wave1-B-report.md` (bpy API 5.2, обёртка `bpyx`) — внутренний отчёт; сверено: гипотезы B по нормалям подтверждены E/03, ловушка `apply_modifiers` в `bpyx.export_glb`.
- [S25] Khronos. glTF-Validator 2.0.0-dev.3.10 (npm). https://github.com/KhronosGroup/glTF-Validator (471 зв., push 2026-09-18) — проверка 242 файлов в E/22.

Эксперименты (все — `99-raw/experiments/E/`): 01-export-params, 02-diff-baseline, 03-geometry-normals, 04-uv-layers,
05-vertex-colors, 06-custom-attributes, 07-modifiers-shapekeys, 08-geonodes-instances, 09-curves-text-points,
10-transforms-hierarchy, 11-extras-names, 12-materials-core (43 случая), 13-materials-extensions (23), 14-lights, 15-cameras-animation
(20), 16-image-formats, 17-compression-geometry, 18-compression-textures, 19–21 bake, 22-validator, 23-pitfalls, 24-presets,
25-api-drift, 26-doc-snippets.
