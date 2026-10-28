# Валидация, каталог поломок и готовые пресеты экспорта Blender 5.2.2 → glTF → three.js r186

Волна 1 · агент E · 23.09.2026 · источников прочитано целиком: 12 (валидатор Khronos и его коды, справка gltf-transform,
README gltfpack, исходники GLTFLoader и WebGLRenderer r186, руководство Blender 5.2, спецификации glTF) · экспериментов: 242 файла
через валидатор (E/22), каталог поломок (E/23), пресеты end-to-end (E/24), проверка кода (E/26) и все опыты E/01–E/28 как
источник симптомов · версии: Blender 5.2.2, glTF-Blender-IO 5.2.40, gltf-validator 2.0.0-dev.3.10, gltf-transform 4.5.0,
gltfpack 1.2, three.js r186, Chromium (Playwright) на Intel Iris Xe.

Файл отвечает на вопросы «как проверить GLB до выкладки», «почему в браузере не так, как в Blender» и «какие параметры
экспорта брать для типовых задач». Что именно теряет экспорт — `01-export-contract.md`; запекание — `02-baking.md`; сжатие и
бюджеты — `03-compression-textures-budgets.md`.

## Выжимка для агента

1. **Проверять в четыре слоя**: (1) предэкспортная проверка сцены `preflight()`, (2) валидатор Khronos, (3) что создал three (`gltf_web_inspect.py`), (4) сравнение картинок Blender↔three (`gltf_diff.py`, ΔE ≤ 3.5, IoU ≥ 0.99) → §1 [проверено]
2. **Валидатор ловит только структуру**: на 242 файлах единственная ошибка — текстура без UV; ни процедурные ноды, ни цветовые пространства, ни потерянные морфы, ни пересвет света он не видит → §2 [проверено]
3. **`UNUSED_OBJECT` (INFO) почти всегда = лишний TEXCOORD_0** у меша без текстур (195 из 242 файлов) → `export_texcoords=False` или `gltf-transform prune` → §2.1 [проверено]
4. **`GENERATED_TANGENT_SPACE` (WARNING)** — карта нормалей без касательных; three строит их сам, для точного совпадения — `export_tangents=True` → §2.1 [проверено]
5. **`NODE_SKINNED_MESH_NON_ROOT`** — норма для Blender (меш — ребёнок арматуры); двигать арматуру, а не родителя меша → §2.1 [проверено]
6. **Предупреждение про `image/ktx2`** у файлов gltfpack — ложная тревога этой сборки валидатора → §2.1 [проверено]
7. **Запускать `preflight()` перед каждым экспортом**: 20 проверок (морфы + модификаторы, UV > 4, два цветовых атрибута, процедурные ноды, цветовые пространства, скрытые объекты, fake-user действия, Area-свет, плотный текст, масштаб, origin) → §5 [проверено]
8. **Проверять готовый GLB `glb_lint()`**: декодеры для страницы, оценка вызовов и треугольников, память текстур, прозрачность, UV > 4, свет в SPEC, pointer-анимация → §6 [проверено]
9. **Чёрный металл** = нет окружения: `scene.environment` (RoomEnvironment через PMREM или HDR) обязателен для metallic > 0 → §3, §4.1 [проверено]
10. **Белый экран / пересвет** = свет экспортирован в SPEC (×683) → COMPAT или свет кодом → §3 [проверено]
11. **Белый объект** = процедурный материал, Noise/Layer Weight в Base Color, не подключённая картинка, баг двух цветовых атрибутов → запечь / `export_all_vertex_colors=False` → §3 [проверено]
12. **«Металлически-серый» объект без материала или с Diffuse BSDF** — в three metalness 1, roughness 1 → Principled BSDF → §3 [проверено]
13. **Цвет в Blender и в three разный при правильном файле** — разные тонмаппинги (AgX в Blender 5.x по умолчанию против `NoToneMapping` three) или неверное цветовое пространство картинки в Blender → §4.2 [проверено]
14. **Вывернутые нормали при doubleSided не видны** ни в Blender, ни в three; всплывают при culling, transmission/volume, в чужих движках → `bmesh.ops.recalc_face_normals` до экспорта → §4.3 [проверено]
15. **Прозрачность BLEND сортируется по объектам** (`depthWrite=false`): вложенные и пересекающиеся прозрачные объекты рисуются в неверном порядке (IoU 0.961, ΔE 7.8) → MASK, transmission, разнести объекты → §4.4 [проверено]
16. **Transmission удваивает вызовы и треугольники** в three r186 (все непрозрачные объекты рисуются ещё раз в текстуру): Camera_01 — 4 → 8 вызовов, 27k → 54k треуг. → §4.5 [проверено] [S7]
17. **Много draw calls** = много объектов × материалов: объект с тремя материалами = 3 вызова; 100 копий = 100 вызовов, инстансинг = 1 → §4.5 [проверено]
18. **Модель лежит на боку** — `export_yup=False`; **гигантская/крошечная** — `scale_length` или неприменённый масштаб импорта; **вращается вокруг чужой точки** — origin → §3 [проверено]
19. **Пропала анимация**: fake-user действие, констрейнты без запекания, pointer-анимация, `export_apply` убил морфы, `export_animations=False` в пресете статики → §4.6 [проверено]
20. **Текстуры не найдены** (404 + «Couldn't load texture», белый материал) — `.gltf` без папки текстур или `export_keep_originals` со ссылками вне папки → выкладывать GLB → §3 [проверено]
21. **Огромный файл**: Subdivision в `levels`, плотный текст, flat-шейдинг, Realize Instances, несжатые PNG 2k → §3 [проверено]
22. **Шесть пресетов** (`static_hero`, `anim_trs`, `anim_morph`, `anim_skin`, `instances`, `mobile_light`) + команда постобработки к каждому прошли валидатор (0 ошибок) и загрузились в three с нужными сущностями → §7 [проверено]
23. **Морф-пресет — без `export_apply`**; скелет — `export_def_bones`, `export_rest_position_armature`; инстансы — `export_gn_mesh` + `export_gpu_instances` → §7.2 [проверено]
24. **Телефонный пресет — картинки AUTO (JPEG/PNG), KTX2 делает gltfpack**; WebP на входе gltfpack `-tc` не перекодирует → §7.3 [проверено]
25. **Постобработка меняет имена**: optimize с join/flatten и gltfpack без `-kn` переименовывают узлы; квантование вставляет узел-обёртку → в JS искать меш через `traverse` → §7.4 [проверено]

## 1. Цепочка проверки ассета

| шаг | инструмент | что ловит | время |
|---|---|---|---|
| 1. до экспорта | `preflight()` в Blender (§5) | потери экспорта: морфы при apply, процедуры, цветовые пространства, UV > 4, скрытые объекты, fake-user действия, свет Area, масштаб, origin | < 0.1 с |
| 2. структура | `python3 ../../scripts/3d/gltf_check.py model.glb` (валидатор Khronos + `gltf-transform inspect`) | нарушения спецификации, лишние атрибуты, размеры текстур, расширения | 1–3 с |
| 3. содержимое | `glb_lint()` (§6) | нужные декодеры, вызовы, треугольники, память текстур, BLEND, SPEC-свет, pointer | < 0.1 с |
| 4. что создал three | `python3 ../../scripts/3d/gltf_web_inspect.py model.glb` | типы объектов и материалов, карты и их `colorSpace`/`channel`, клипы и треки, `userData`, ошибки консоли | 3–5 с |
| 5. как выглядит | `python3 ../../scripts/3d/gltf_diff.py scene.blend out/ --glb model.glb` | расхождение картинки: IoU силуэта, ΔE2000, SSIM, тепловая карта | 5–10 с |
| 6. сколько стоит | `python3 ../../scripts/3d/gltf_load_bench.py model.glb` | загрузка холодная/тёплая, первый кадр, вызовы, треугольники, память GPU | 5–15 с |

[проверено]. Пороги `gltf_diff.py` (калибровка E/02): одинаковый файл в EEVEE «Standard» и three
`NoToneMapping` даёт ΔE2000 ≈ 3.1 (фронт 2.0–2.3) и IoU 0.996 — это шум метода; поломка экспорта — ΔE > 6 или IoU < 0.95
[проверено]. Стекло, анизотропию и плёнку сравнивать с Cycles (`--engine cycles --samples 64`).

```bash
# Python 3 + Blender 5.2.2 + Playwright — [проверено: 99-raw/experiments/E/22, E/24; ../../scripts/3d/README.md]
python3 ../../scripts/3d/gltf_check.py /abs/path/model.glb                                   # валидатор + inspect + подсказки
python3 ../../scripts/3d/gltf_web_inspect.py /abs/path/model.glb --out /abs/path/three.json  # что создал three r186
python3 ../../scripts/3d/gltf_diff.py /abs/path/scene.blend /abs/path/diff --glb /abs/path/model.glb --views 3
python3 ../../scripts/3d/gltf_load_bench.py /abs/path/model.glb --runs 3 --json /abs/path/bench.json
```

## 2. Валидатор Khronos

### 2.1. Что он сказал о 242 файлах из экспериментов

Прогон `99-raw/experiments/E/22-validator/collect.py` (gltf-validator 2.0.0-dev.3.10 через `../../scripts/3d/node/validate.mjs`) по
всем GLB опытов E — экспорт Blender с разными настройками и выход gltf-transform/gltfpack [проверено]:

| уровень | код | файлов | что значит здесь | что делать |
|---|---|---|---|---|
| ERROR | `MESH_PRIMITIVE_TOO_FEW_TEXCOORDS` | 1 | у материала текстура, у меша нет `TEXCOORD_0` (`export_texcoords=False`) | не отключать UV у текстурированных мешей |
| WARNING | `MESH_PRIMITIVE_GENERATED_TANGENT_SPACE` | 12 | карта нормалей без атрибута `TANGENT`: three строит касательные по производным | допустимо; для точного совпадения — `export_tangents=True` или `gltf-transform tangents` |
| WARNING | `NODE_SKINNED_MESH_NON_ROOT` | 1 | скиннинг-меш — ребёнок арматуры (так экспортирует Blender); трансформ родителя на него не действует | норма; двигать арматуру |
| WARNING | `VALUE_NOT_IN_LIST 'image/ktx2'` + `IMAGE_UNRECOGNIZED_FORMAT` | 1 | выход `gltfpack -tc`: эта сборка валидатора не знает KTX2 в images | ложная тревога; проверять загрузкой в three |
| INFO | `UNUSED_OBJECT` | 195 | почти всегда `TEXCOORD_0` у меша без текстур: экспортёр пишет все UV-слои | 8 байт/вершину + вершины на швах UV; `export_texcoords=False` для нетекстурных, `gltf-transform prune` |
| INFO | `UNSUPPORTED_EXTENSION` | 43 | EXT_mesh_gpu_instancing, KHR/EXT_meshopt_compression — валидатор их не проверяет | норма |
| INFO | `NODE_EMPTY` | 10 | пустые узлы: пустышки, держатели инстансов | норма; убрать — `prune`/`flatten` |
| INFO | `INCOMPLETE_EXTENSION_SUPPORT` | 2 | KHR_animation_pointer | норма (но three его не проигрывает, `01` §9.3) |

`gltf-transform prune` удаляет неиспользуемый `TEXCOORD_0` у примитивов, у которых есть материал без текстур; у примитива без
материала оставляет [проверено].

### 2.2. Чего валидатор не видит

Все эти потери дают валидный файл без единого ERROR [проверено: 99-raw/experiments/E/22-validator и опыты-источники]:
- процедурные текстуры, Color Ramp, Mix, Bump, Mix Shader, Diffuse BSDF (`01` §5.8; E/12);
- неверное цветовое пространство картинки в Blender (E/12 m05, m09, m15);
- удалённые `export_apply` shape keys (E/07), модификаторы без apply (E/03, E/07), GN без флагов (E/08);
- белый `COLOR_0` (баг двух атрибутов, E/05);
- свет в SPEC (×683), Area-свет (E/14); анимация pointer, которую не проиграет three (E/15);
- скрытые и вспомогательные объекты в файле (E/10);
- texCoord ≥ 4 (файл валиден, three падает на компиляции шейдера, E/04);
- огромный вес и память GPU (E/17, E/18).

### 2.3. gltf-transform inspect: на что смотреть

`npx gltf-transform inspect model.glb` (входит в `gltf_check.py`) печатает таблицы [проверено: 99-raw/tools/node, 2026-09-23]:
- OVERVIEW — `generator`, `extensionsUsed`, `extensionsRequired` (какие декодеры нужны странице);
- SCENES — габарит (`bboxMin/Max`: модель в метрах? не 100 м?), `renderVertexCount`, `uploadVertexCount`;
- MESHES — режим (TRIANGLES/LINES/POINTS), число примитивов (= вызовов на экземпляр узла), вершины, индексы, **типы атрибутов**
  (`POSITION:u16`, `NORMAL:i8_norm` — квантовано; `f32` — нет), `instances`, оценка памяти;
- MATERIALS — какие текстуры, `alphaMode`, `doubleSided`;
- TEXTURES — `mimeType`, `compression` (ETC1S/UASTC), `resolution`, размер в файле и **`gpuSize`** (минимальная оценка VRAM:
  у KTX2 1024² ETC1S — 699 КБ, т. е. 0.5 байта/пиксель; на десктопе без ETC three возьмёт BC7 — вдвое больше);
- ANIMATIONS — каналы, ключи, длительность.

## 3. Каталог поломок: симптом в браузере → причина в Blender → исправление

| симптом в three r186 | причина в Blender / экспорте | исправление | доказательство |
|---|---|---|---|
| металл чёрный, виден один блик | металл отражает окружение, а у страницы нет `scene.environment` | RoomEnvironment/HDR через PMREM (§4.1) | E/23 p3 |
| сцена белая, пересвет | свет экспортирован в режиме SPEC (×683) | `export_import_convert_lighting_mode="COMPAT"` или свет кодом | E/14 |
| объект белый вместо узора | процедурные текстуры / Color Ramp / Layer Weight — не экспортируются | запечь (`02-baking.md` §4) | E/12 m35, m38; E/19 |
| узор есть, но «не тот» (без Ramp/Hue/Mix) | ноды между картинкой и Principled отброшены, ушла сырая картинка | запечь или поправить картинку | E/12 m32–m34 |
| объект белый при цвете вершин | ≥ 2 цветовых атрибута + `export_all_vertex_colors=True` (баг 5.2.40) | `export_all_vertex_colors=False` | E/05 v05 |
| объект светится белым | не-текстурный источник в Emission Color | эмиссию — константой или картинкой | E/05 v11 |
| серый «металл» вместо матового | нет материала (DefaultMaterial) или Diffuse/Glossy BSDF → metalness 1, roughness 1 | Principled BSDF | E/03, E/12 m41 |
| в Blender бледнее / темнее, чем в three | цветовое пространство картинки в Blender неверно (Non-Color на цвете, sRGB на данных) — веб правильный | sRGB для цвета, Non-Color для данных | E/12 m05, m09, m15 |
| цвета везде немного другие | AgX в Blender против `NoToneMapping` в three; разные IBL | сравнивать Standard↔None или Khronos PBR Neutral↔`NeutralToneMapping` | E/02 |
| мусорный рельеф | Bump от картинки уехал в `normalTexture` | Normal Map или запечённая нормаль | E/12 m16 |
| рельеф пропал, объект «надутый» | модификатор Smooth by Angle / Weighted Normal / Bevel без `export_apply` | `export_apply=True` или острые рёбра данными | E/03 c08, c11 |
| объект не рисуется, «'uv4' undeclared» в консоли | текстура на 5-м UV-слое | ≤ 4 UV, карты на UV0/UV1 | E/04 u3 |
| объект одним цветом | экспорт без UV (`export_texcoords=False`) при текстуре | включить UV | E/04 u4, E/22 |
| дыры, видна внутренняя сторона | вывернутые нормали + `use_backface_culling` (или volume, который делает doubleSided=false) | `recalc_face_normals` (§4.3) | E/23 p2 |
| прозрачные объекты «мигают»/перекрываются неверно | BLEND: `depthWrite=false`, сортировка по центрам объектов | MASK, transmission, разнести объекты (§4.4) | E/23 p4 |
| мыльные текстуры | ETC1S на нормалях/деталях; ресайз; KTX2 из JPEG | UASTC для данных, WebP/PNG для нормалей | E/18 |
| файл огромный | Subdivision в `levels`; текст `resolution_u` 12; flat-шейдинг; Realize Instances; PNG 2k без сжатия | `levels` меньше, текст 3–4/0–1, острые рёбра, инстансы, постобработка (`03`) | E/03, E/07, E/08, E/09, E/18 |
| пропала анимация | действие только с fake user; констрейнты без запекания; анимация материала/света (pointer) | NLA-дорожки, `export_bake_animation`, анимация в JS | E/15 |
| пропали морфы (`morphTargetDictionary` пуст) | `export_apply=True` на объекте с модификаторами | применить модификаторы до shape keys или без apply | E/07, E/24 |
| модель лежит на спине | `export_yup=False` | `export_yup=True` | E/10 t4b |
| модель в 100 раз больше | `scale_length=0.01` (сцена в см) игнорируется | метры, `scale_length=1`, применить масштаб | E/10 t6 |
| вращается вокруг чужой точки | геометрия далеко от origin | origin в центр (§4.7) | E/10 t5 |
| лишний объект, дубли имён `_1`, `_2` | скрытые/исключённые объекты и исходник инстанса коллекции экспортированы | `use_renderable`, `use_visible`, `collection=`, `glTF_not_exported` | E/10 t7, t8 |
| JS не находит объект по имени | «Cube.001» → «Cube001»; после постобработки — слит/переименован/обёрнут | латинские имена без точек; `--join false`, `-kn`; `traverse` | E/11, E/24, E/28 |
| `userData` пустой | `export_extras=False` или gltfpack без `-ke` | `export_extras=True`, `-ke` | E/11, E/28 |
| 404 и «Couldn't load texture», белый материал | `.gltf` выложен без папки текстур; `export_keep_originals` с путями вне папки | выкладывать GLB | E/16 i8, E/23 p5 |
| исключение при загрузке («No DRACOLoader instance provided» и т. п.) | файл сжат, декодер не подключён | подключить декодеры (`01` §7.1) | S5 |
| клип длиной 0 с | анимация pointer (материал, свет) | анимировать кодом | E/15 a15b |
| 100 вызовов на 100 одинаковых объектов | копии без инстансинга | `export_gpu_instances` / GN-инстансы | E/08 g7–g9 |
| вызовов вдвое больше ожидаемого | в сцене есть transmission (проход в текстуру) | считать ×2 или стекло unlit/MASK для фона | §4.5 |
| сцена в three темнее Blender на плоских светлых поверхностях | разное IBL (EEVEE против PMREM), ≈ 13 L* | принимать как шум метода или сверять с Cycles | E/20 |


## 4. Разбор поломок, которые требуют кода

### 4.1. Металл без окружения

Золото (metallic 1, roughness 0.2) на странице без окружения (HemisphereLight + DirectionalLight, `web_view.py --env none`) —
чёрное с одним бликом; с RoomEnvironment — нормальное золото; пластик в обоих случаях нормальный
[проверено]. Металл в PBR почти не имеет диффузной составляющей и показывает только отражение
окружения; лампы дают только точечные блики.

```js
// three r186 — [проверено: ../../scripts/3d/gltf_web_inspect.py (та же строка на странице), 99-raw/experiments/E/23-pitfalls (web_view --env room)]
import * as THREE from 'three';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;   // или HDR через HDRLoader + pmrem.fromEquirectangular
```

### 4.2. «Цвет не тот»: три разные причины

1. **Файл правильный, Blender показывает иначе** — цветовое пространство ноды Image Texture в Blender не совпадает со слотом glTF
   (Non-Color на base color → Blender бледнее на ΔE 15.9; sRGB на нормалях → в Blender искажён рельеф) [проверено].
2. **Разный тонмаппинг**: Blender 5.x по умолчанию — AgX, three — `NoToneMapping`. Для сверки: EEVEE «Standard» ↔ `NoToneMapping`
   (ΔE 3.1) или «Khronos PBR Neutral» ↔ `NeutralToneMapping` (3.2); AgX ↔ `AgXToneMapping` — 4.3, реализации различаются
   (three светлее на 2–4 L*) [проверено].
3. **Файл неправильный** — Base Color > 1 обрезан (ΔE 5.2), белый `COLOR_0` (баг), не-текстурная эмиссия → белый
   [проверено].

### 4.3. Вывернутые нормали

Сфера с вывернутыми гранями (`bmesh.ops.reverse_faces`) при материале по умолчанию (doubleSided) выглядит нормально и в Blender,
и в three (ΔE 3.2) — ошибка скрыта; с `use_backface_culling=True` в обоих видна внутренняя сторона дальней половины
[проверено]. Всплывает также в volume (экспортёр ставит doubleSided=false), в тенях и в движках
без двусторонности. Лечение до экспорта:

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/E/26-doc-snippets/run_md04.py (сфера 512 граней: все внутрь → все наружу)]
import bmesh

def recalc_normals_outside(ob):
    """Развернуть грани меша наружу (эквивалент Shift+N в режиме редактирования)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
```

Для незамкнутых мешей (плоскости, листья) направление не определено — проверять глазами: в Blender Viewport Overlays → Face
Orientation (синий — лицевая сторона) [практика; разбор Codrops S10].

### 4.4. Прозрачность

- `alphaMode` BLEND в three: `transparent = true`, `depthWrite = false`; прозрачные объекты сортируются по расстоянию центров
  объектов до камеры, а не по пикселям [S5]. Полупрозрачная сфера с полупрозрачным кубом внутри (центры совпадают) — порядок
  смешивания не определён: IoU 0.961, ΔE 7.8, SSIM 0.43 к EEVEE [проверено].
- Что делать: вырез по альфе — MASK (`alphaTest`, пишет глубину, без сортировки) [проверено];
  стекло — transmission (`01` §6.2); вложенные прозрачные объекты — разнести или объединить в один меш; порядок вручную —
  `mesh.renderOrder` в JS [документация three; не проверено].
- Одна константа Alpha < 1 на весь материал уже даёт BLEND — для «чуть прозрачного» фона это лишняя сортировка и отключённая
  запись глубины [проверено].

### 4.5. Draw calls

- Вызов = примитив glTF × экземпляр узла: объект Blender с тремя материалами — 3 примитива (в three `Group` с тремя `Mesh`) —
  3 вызова [S5]. 100 связанных дубликатов — 100 вызовов; с `export_gpu_instances` — 1 [проверено].
- `gltf-transform optimize` (join) сливает меши с одинаковым материалом: 36 объектов → 4 вызова, но имена теряются
  [проверено].
- **Transmission удваивает работу**: `WebGLRenderer.renderTransmissionPass` r186 рисует все непрозрачные объекты ещё раз в
  отдельную цель (MSAA ≥ 4, half-float, мипмапы), а двусторонние прозрачные материалы — ещё и задней стороной [S7]. Camera_01
  (линза с KHR_materials_transmission): 4 примитива в файле → 8 вызовов и 53 974 треуг. вместо 26 987 [проверено].
  Для стекла в Blender включать `use_backface_culling` (doubleSided=false); `renderer.transmissionResolutionScale` уменьшает
  цель [S7; не проверено].
- Бюджеты вызовов — `03` §6.5.

### 4.6. Пропала анимация: проверки по порядку

1. `export_animations=True` (в пресете статики выключен намеренно) [проверено].
2. Действие назначено объекту или лежит в NLA-дорожке; fake user не считается [проверено].
3. Движение от констрейнтов/драйверов — `export_bake_animation=True` [проверено].
4. Морфы: у объекта нет модификаторов или экспорт без apply [проверено].
5. Анимируется материал/свет/камера — это pointer, three не проиграет: переносить в JS [проверено].
6. На странице: `new AnimationMixer(gltf.scene)`, `clipAction(clip).play()`, `mixer.update(delta)` в цикле (`01` §9.1)
   [проверено].
7. После постобработки — клипы на месте (`gltf_web_inspect.py`: список клипов и треков) [проверено].

### 4.7. Origin и масштаб

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/E/26-doc-snippets/run_md04.py (origin в центр габарита, масштаб 1)]
import bpy

def origin_to_bounds_and_apply_scale(ob):
    """Origin — в центр габарита (pivot для вращения в JS), масштаб применить (узел glTF со scale 1)."""
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
```

Origin — точка, вокруг которой объект будет вращаться и масштабироваться на странице; для «двери» или «крышки» origin ставят на
петлю, а не в центр [практика]. Масштаб применять до экспорта: экспортёр переносит неприменённый и даже отрицательный масштаб
верно (`01` §4.9), но анимации и физика в JS работают от «кривого» узла.

## 5. Предэкспортная проверка сцены: `preflight()`

Функция обходит объекты, модификаторы, материалы (включая группы нод) и действия и возвращает список `(уровень, код, объект,
сообщение)`. На тестовой сцене с 20 заложенными проблемами нашла все 20; на чистой сцене — ни одного WARN/ERROR
[проверено].

```python
# Blender 5.2.2 / glTF-IO 5.2.40 — [проверено: 99-raw/experiments/E/26-doc-snippets/preflight_test.py, run_md04.py] предэкспортная проверка сцены для веба
import bpy
from mathutils import Vector

LOST_NODES = {"TEX_NOISE", "TEX_VORONOI", "TEX_WAVE", "TEX_MAGIC", "TEX_GRADIENT", "TEX_CHECKER", "TEX_BRICK",
              "TEX_WHITE_NOISE", "TEX_GABOR", "LAYER_WEIGHT", "FRESNEL", "BUMP", "VALTORGB", "HUE_SAT",
              "BRIGHTCONTRAST", "GAMMA", "INVERT", "CURVE_RGB", "AMBIENT_OCCLUSION", "SHADERTORGB", "WIREFRAME",
              "BEVEL", "TEX_ENVIRONMENT", "TEX_SKY", "DISPLACEMENT"}
LOST_SHADERS = {"ADD_SHADER", "BSDF_DIFFUSE", "BSDF_GLOSSY", "BSDF_TOON", "BSDF_METALLIC", "BSDF_SHEEN",
                "SUBSURFACE_SCATTERING", "BSDF_TRANSLUCENT"}
BAD_NAME_CHARS = set(" .[]:/")


def _tree_nodes(tree, depth=0):
    """Все ноды дерева материала, включая вложенные группы."""
    out = []
    for n in tree.nodes:
        out.append(n)
        if n.type == "GROUP" and n.node_tree and depth < 8:
            out += _tree_nodes(n.node_tree, depth + 1)
    return out


def _material_issues(mat):
    issues = []
    if not mat.node_tree:
        return issues
    nodes = _tree_nodes(mat.node_tree)
    types = {n.type for n in nodes}
    for t in sorted(types & LOST_NODES):
        issues.append(("WARN", "NODE_LOST", f"нода {t} не экспортируется — запечь (02-baking)"))
    for t in sorted(types & LOST_SHADERS):
        issues.append(("WARN", "SHADER_LOST", f"шейдер {t} → материал без PBR (metal 1 / rough 1)"))
    if "MIX_SHADER" in types and "LIGHT_PATH" not in types:
        issues.append(("WARN", "MIX_SHADER", "Mix Shader → в glTF останется один BSDF"))
    for n in nodes:
        if n.type != "TEX_IMAGE" or not n.image:
            continue
        cs = n.image.colorspace_settings.name
        for link in n.outputs["Color"].links:
            to_node, to_name = link.to_node, link.to_socket.name
            if to_node.type == "BSDF_PRINCIPLED" and to_name in ("Base Color", "Emission Color") and cs != "sRGB":
                issues.append(("WARN", "COLORSPACE", f"{n.image.name}: {cs} на цветовом входе {to_name} (нужен sRGB)"))
            if (to_node.type in ("NORMAL_MAP", "SEPARATE_COLOR") or to_name in ("Roughness", "Metallic")) and cs == "sRGB":
                issues.append(("WARN", "COLORSPACE", f"{n.image.name}: sRGB на данных ({to_node.type}.{to_name}) — нужен Non-Color"))
    return issues


def preflight(scene=None):
    """Список (уровень, код, объект, сообщение). Уровни: ERROR — сломается, WARN — потеряется/исказится, INFO — проверить."""
    sc = scene or bpy.context.scene
    rep = []
    add = lambda lvl, code, ob, msg: rep.append((lvl, code, ob, msg))
    if abs(sc.unit_settings.scale_length - 1.0) > 1e-6:
        add("WARN", "UNIT_SCALE", "scene", f"scale_length {sc.unit_settings.scale_length} игнорируется экспортом (1 BU = 1 м)")
    for ob in sc.objects:
        name = ob.name
        if BAD_NAME_CHARS & set(name):
            add("INFO", "NAME_SANITIZED", name, "three переименует узел (пробел → _, удалит . [ ] : /)")
        if ob.hide_get() or ob.hide_viewport or ob.hide_render:
            add("INFO", "HIDDEN_OBJECT", name, "скрытые объекты экспортируются по умолчанию (use_visible/use_renderable)")
        if ob.type == "LIGHT":
            add("INFO", "LIGHT", name, "свет не экспортируется по умолчанию; при export_lights — режим COMPAT")
            if ob.data.type == "AREA":
                add("WARN", "AREA_LIGHT", name, "Area-свет не экспортируется никогда")
        if ob.type == "FONT" and (ob.data.resolution_u > 4 or ob.data.bevel_resolution > 1):
            add("WARN", "TEXT_DENSE", name, f"resolution_u {ob.data.resolution_u}, bevel_resolution {ob.data.bevel_resolution} → тысячи треуг.")
        if any(abs(s - 1.0) > 1e-4 for s in ob.scale):
            add("INFO", "UNAPPLIED_SCALE", name, f"масштаб {tuple(round(s, 3) for s in ob.scale)} — применить (Ctrl+A)")
        if any(s < 0 for s in ob.scale):
            add("INFO", "NEGATIVE_SCALE", name, "отрицательный масштаб")
        if ob.type != "MESH":
            continue
        me = ob.data
        mods = [m for m in ob.modifiers if m.type != "ARMATURE"]
        if me.shape_keys and mods:
            add("ERROR", "SHAPEKEYS_WITH_MODIFIERS", name, "export_apply=True удалит shape keys молча")
        for m in mods:
            if not m.show_viewport and m.show_render:
                add("WARN", "MOD_VIEWPORT_OFF", name, f"модификатор {m.name} выключен во вьюпорте — export_apply его не применит")
            if m.type == "SUBSURF" and m.levels != m.render_levels:
                add("INFO", "SUBSURF_LEVELS", name, f"экспорт возьмёт levels={m.levels}, а не render_levels={m.render_levels}")
            if m.type == "NODES":
                add("INFO", "GEONODES", name, "нужен export_apply (+ export_gn_mesh/export_gpu_instances для инстансов)")
        if len(me.uv_layers) > 4:
            add("ERROR", "UV_OVER_4", name, f"{len(me.uv_layers)} UV-слоёв: three читает 4, texCoord ≥ 4 ломает шейдер")
        elif len(me.uv_layers) > 2:
            add("WARN", "UV_MANY", name, f"{len(me.uv_layers)} UV-слоёв уходят в файл")
        if len(me.color_attributes) >= 2:
            add("WARN", "MULTI_COLOR_ATTR", name, "≥ 2 цветовых атрибута: export_all_vertex_colors=False (баг белого COLOR_0)")
        if not any(slot.material for slot in ob.material_slots):
            add("INFO", "NO_MATERIAL", name, "в three DefaultMaterial: белый, metalness 1, roughness 1")
        if me.vertices:
            c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8      # центр габарита в координатах объекта
            if c.length > max(max(ob.dimensions), 1e-6):
                add("INFO", "ORIGIN_FAR", name, f"геометрия в {c.length:.2f} BU от origin — pivot в JS будет чужим")
    for mat in bpy.data.materials:
        if mat.users:
            for lvl, code, msg in _material_issues(mat):
                add(lvl, code, f"material:{mat.name}", msg)
    for act in bpy.data.actions:
        if act.use_fake_user and act.users <= 1:
            add("WARN", "FAKE_USER_ACTION", f"action:{act.name}", "действие только с fake user — не экспортируется")
    return rep
```

Использование: `for lvl, code, ob, msg in preflight(): print(lvl, code, ob, msg)`; перед экспортом останавливаться на ERROR и
исправлять WARN. Коды и что делать:

| код | уровень | что делать |
|---|---|---|
| `SHAPEKEYS_WITH_MODIFIERS` | ERROR | применить модификаторы до shape keys или пресет `anim_morph` (без apply) |
| `UV_OVER_4` | ERROR | удалить лишние UV-слои |
| `UV_MANY`, `MULTI_COLOR_ATTR` | WARN | удалить лишнее; `export_all_vertex_colors=False` |
| `MOD_VIEWPORT_OFF` | WARN | включить модификатор во вьюпорте или удалить |
| `NODE_LOST`, `SHADER_LOST`, `MIX_SHADER` | WARN | запечь (`02-baking.md`) или заменить на Principled |
| `COLORSPACE` | WARN | sRGB — цвет, Non-Color — данные |
| `FAKE_USER_ACTION` | WARN | положить действие в NLA-дорожку (`01` §9.1) |
| `AREA_LIGHT`, `TEXT_DENSE`, `UNIT_SCALE` | WARN | свет кодом; `resolution_u` 3–4; метры |
| `SUBSURF_LEVELS`, `GEONODES`, `HIDDEN_OBJECT`, `UNAPPLIED_SCALE`, `NEGATIVE_SCALE`, `ORIGIN_FAR`, `NO_MATERIAL`, `NAME_SANITIZED`, `LIGHT` | INFO | проверить намерение |

## 6. Проверка готового GLB: `glb_lint()`

Чистый Python без bpy: читает JSON-чанк и заголовки картинок. Прогон на выходе пресетов E/24 и файлах E/14–E/26: mobile_light —
декодеры KTX2Loader + MeshoptDecoder, 4 вызова по файлу (×2 в three из-за transmission — предупреждение), 26 987 треуг., 12 МБ
текстур; static_hero — MeshoptDecoder, 192 МБ текстур; файл со светом в SPEC — предупреждение «> 500»
[проверено].

```python
# Python 3.10+ (без bpy) — [проверено: 99-raw/experiments/E/26-doc-snippets/glb_lint_result.json, run_md04.py] проверка готового GLB:
# расширения и декодеры, вызовы, треугольники, текстуры и память GPU, прозрачность, UV, свет, анимация
import json, struct

DECODERS = {"KHR_draco_mesh_compression": "DRACOLoader", "EXT_meshopt_compression": "MeshoptDecoder",
            "KHR_meshopt_compression": "MeshoptDecoder", "KHR_texture_basisu": "KTX2Loader"}


def _image_size(data):
    """(ширина, высота) из заголовка PNG, JPEG, WebP или KTX2."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:12] == b"\xabKTX 20\xbb\r\n\x1a\n":
        return struct.unpack("<II", data[20:28])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if data[12:16] == b"VP8L":
            b = int.from_bytes(data[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
        return struct.unpack("<HH", data[26:30])[0] & 0x3FFF, struct.unpack("<HH", data[26:30])[1] & 0x3FFF
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1; continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9]); return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def glb_lint(path):
    raw = open(path, "rb").read()
    jlen = struct.unpack_from("<I", raw, 12)[0]
    j = json.loads(raw[20:20 + jlen])
    binc = raw[20 + jlen + 8:] if len(raw) > 20 + jlen else b""
    rep = {"file_kb": round(len(raw) / 1024, 1), "extensionsRequired": j.get("extensionsRequired", []), "warnings": []}
    warn = rep["warnings"].append
    rep["decoders"] = sorted({DECODERS[e] for e in rep["extensionsRequired"] if e in DECODERS})
    acc = j.get("accessors", [])
    # вызовы и треугольники: примитивы × экземпляры узлов (инстансинг — 1 вызов на примитив)
    calls = tris = 0
    for n in j.get("nodes", []):
        if "mesh" not in n:
            continue
        inst = n.get("extensions", {}).get("EXT_mesh_gpu_instancing")
        count = acc[inst["attributes"]["TRANSLATION"]]["count"] if inst and "TRANSLATION" in inst["attributes"] else 1
        for prim in j["meshes"][n["mesh"]]["primitives"]:
            calls += 1
            if prim.get("mode", 4) == 4:
                k = acc[prim["indices"]]["count"] if "indices" in prim else acc[prim["attributes"]["POSITION"]]["count"]
                tris += k // 3 * count
            uv = [a for a in prim["attributes"] if a.startswith("TEXCOORD_")]
            if len(uv) > 4:
                warn(f"mesh {j['meshes'][n['mesh']].get('name')}: {len(uv)} наборов UV (three читает 4)")
    rep["draw_calls_estimate"], rep["triangles"] = calls, tris
    # материалы
    mats = j.get("materials", [])
    rep["materials"] = len(mats)
    rep["blend_materials"] = [m.get("name") for m in mats if m.get("alphaMode") == "BLEND"]
    rep["unlit_materials"] = [m.get("name") for m in mats if "KHR_materials_unlit" in m.get("extensions", {})]
    if any("KHR_materials_transmission" in m.get("extensions", {}) for m in mats):
        warn("transmission: three r186 рисует все непрозрачные объекты ещё раз в текстуру — вызовы и треугольники ×2")
    # текстуры и память GPU (RGBA8 + мипмапы; KTX2 ≈ 1 байт/пиксель + мипмапы)
    gpu = 0.0; imgs = []
    for im in j.get("images", []):
        size = None
        if "bufferView" in im:
            bv = j["bufferViews"][im["bufferView"]]; data = binc[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
            size = _image_size(data)
        mime = im.get("mimeType", "uri")
        if size:
            bpp = 1 if mime == "image/ktx2" else 4
            gpu += size[0] * size[1] * bpp * 4 / 3
            if max(size) > 2048:
                warn(f"текстура {im.get('name')} {size[0]}×{size[1]} > 2048")
            if mime == "image/ktx2" and (size[0] % 4 or size[1] % 4):
                warn(f"KTX2 {im.get('name')}: размер не кратен 4")
        imgs.append((im.get("name"), mime, size))
    rep["images"], rep["gpu_textures_mb"] = imgs, round(gpu / 2 ** 20, 1)
    # свет и анимация
    lights = j.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])
    if any(l.get("intensity", 1) > 500 for l in lights):
        warn("интенсивность света > 500 — похоже на режим SPEC (×683): экспортировать с COMPAT")
    anims = j.get("animations", [])
    rep["animations"] = [a.get("name") for a in anims]
    if any("node" not in c.get("target", {}) for a in anims for c in a["channels"]):
        warn("есть каналы KHR_animation_pointer — three r186 без плагина их не проигрывает")
    if not any(n.get("extras") for n in j.get("nodes", [])):
        rep["note_extras"] = "extras у узлов нет (export_extras=False или постобработка без -ke)"
    return rep
```

Оценка вызовов — по файлу; three добавляет вызовы за transmission (×2), тени (по вызову на объект на каждую тень) и
постобработку. Память текстур — нижняя оценка для KTX2 (1 байт/пиксель) и точная для RGBA8.

## 7. Пресеты экспорта

### 7.1. Сводка

| пресет | для чего | ключевые параметры | постобработка | результат E/24 |
|---|---|---|---|---|
| `static_hero` | статичный объект первого экрана | база (§3.2 `01`): apply, extras, UV, без анимации, света, камер | `optimize --compress meshopt --texture-compress webp --texture-size 2048 --simplify false` | Camera_01 6 049 → 2 452 КБ, 0 ошибок, 8 вызовов в three, текстуры 192 МБ |
| `anim_trs` | анимация трансформаций объектов/пустышек | + `export_animations`, ACTIONS, сэмплирование, `slide_to_zero` | `optimize … --flatten false --join false --simplify false` | 58 → 17.5 КБ; клип 1.97 с; `userData.hotspot` на месте |
| `anim_morph` | shape keys | **`export_apply=False`**, `export_morph*`, sparse | то же | 1 104 → 301 КБ; `morphTargetDictionary` Wave0…7, клип 3.97 с |
| `anim_skin` | скелет | `export_apply=False`, `export_skins`, 4 влияния, только деформирующие кости, поза покоя арматуры | то же | 9.8 → 5.9 КБ; SkinnedMesh + кости, клип 2.46 с |
| `instances` | GN-инстансы и связанные дубликаты | + `export_gn_mesh`, `export_gpu_instances` | то же | 11.5 → 8.6 КБ (GN), 11.6 → 6.3 КБ (дубликаты); InstancedMesh ×100, 1 вызов |
| `mobile_light` | телефон | база, картинки **AUTO** (JPEG/PNG) | нативный `gltfpack -cc -tc -ts 0.5` | 6 049 → **1 530 КБ**, KTX2 1024², текстуры **12 МБ**, тёплая загрузка 33 мс |
| вариант «адресуемые узлы» | метки `hotspot_*`, `cam_*`, extras, клики по частям | база `static_hero` | `gltfpack -cc -kn -ke` (или `optimize --flatten false --join false --simplify false`; `prune` по умолчанию удаляет пустышки) | имена и extras узлов сохраняются, extras мешей — нет (I/03, E/28) |

[проверено]. Все выходы прошли валидатор без ошибок (предупреждения: касательные у hero,
non-root skinned mesh у скелета, ложное `image/ktx2` у gltfpack) и загрузились в three r186 с ожидаемыми сущностями.

### 7.2. Код пресетов

Файл `../../scripts/3d/presets.py` целиком; подключается `exec(open(path).read())` в фоновом скрипте Blender.
Функция `export()` проверяет ключи по RNA оператора и падает с понятной ошибкой на параметре, которого нет в этой версии.

```python
# Blender 5.2.2 / glTF-Blender-IO 5.2.40 — пресеты bpy.ops.export_scene.gltf для веба (three r186). [проверено]
# Импорт: exec(open(".../presets.py").read()) или sys.path + import presets; export(path, PRESET, **overrides)

BASE_WEB = dict(
    export_format="GLB",
    export_yup=True,                      # glTF Y-up (иначе модель «лежит»)
    export_apply=True,                    # модификаторы — уровень ВЬЮПОРТА (levels); у объектов С модификаторами теряются shape keys
    export_texcoords=True,
    export_normals=True,
    export_tangents=False,                # three строит касательные сам; True — если нужна точная карта нормалей
    export_materials="EXPORT",
    export_image_format="AUTO",           # исходные JPEG/PNG байт в байт; WebP/KTX2 — постобработкой
    export_vertex_color="MATERIAL",
    export_all_vertex_colors=False,       # иначе фиктивный COLOR_0 и баг 5.2.40 с несколькими атрибутами
    export_attributes=False,
    export_extras=True,                   # custom properties → userData для JS
    export_cameras=False,
    export_lights=False,                  # свет — кодом на странице (или COMPAT, см. 01 §7)
    use_renderable=True,                  # без объектов с hide_render
    use_visible=True,                     # без скрытых и исключённых коллекций
    export_animations=False,
    export_draco_mesh_compression_enable=False,
    export_meshopt_compression_enable=False,   # сжатие — постобработкой (встроенный meshopt не квантует)
)

PRESETS = {
    # 1. Статичный hero-объект (витрина, первый экран)
    "static_hero": dict(BASE_WEB),
    # 2. Анимация трансформаций (объекты/пустышки): клипы из действий
    "anim_trs": dict(BASE_WEB, export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
                     export_frame_step=1, export_optimize_animation_size=True, export_anim_slide_to_zero=True,
                     export_bake_animation=False, export_merge_animation="ACTION"),
    # 3. Морф-анимация (shape keys): БЕЗ применения модификаторов
    "anim_morph": dict(BASE_WEB, export_apply=False, export_animations=True, export_animation_mode="ACTIONS",
                       export_morph=True, export_morph_normal=True, export_morph_animation=True,
                       export_try_sparse_sk=True, export_anim_slide_to_zero=True),
    # 4. Скелетная анимация
    "anim_skin": dict(BASE_WEB, export_apply=False, export_animations=True, export_animation_mode="ACTIONS",
                      export_skins=True, export_influence_nb=4, export_def_bones=True, export_rest_position_armature=True,
                      export_anim_single_armature=True, export_anim_slide_to_zero=True),
    # 5. Сцена с инстансами (связанные дубликаты под одним родителем и/или GN-инстансы)
    "instances": dict(BASE_WEB, export_gpu_instances=True, export_gn_mesh=True),
    # 6. «Лёгкий» для телефона: картинки как есть (JPEG/PNG!) — KTX2 и ресайз делает gltfpack; WebP-вход gltfpack -tc НЕ перекодирует
    "mobile_light": dict(BASE_WEB, export_image_format="AUTO"),
}

# Постобработка (из 99-raw/tools/node; нативный gltfpack для текстур: 99-raw/tools/bin/gltfpack-1.2/gltfpack; toktx в PATH для ktx2)
POST = {
    "static_hero": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --texture-size 2048 --simplify false",
    "anim_trs": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "anim_morph": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "anim_skin": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "instances": "npx gltf-transform optimize IN OUT --compress meshopt --texture-compress webp --flatten false --join false --simplify false",
    "mobile_light": "gltfpack -i IN -o OUT -cc -tc -ts 0.5",
}


def export(path, preset, **overrides):
    import bpy, os
    kw = dict(PRESETS[preset] if isinstance(preset, str) else preset); kw.update(overrides)
    valid = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    bad = [k for k in kw if k not in valid]
    if bad:
        raise KeyError(f"нет параметров {bad} в export_scene.gltf этой версии")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return bpy.ops.export_scene.gltf(filepath=os.path.abspath(path), **kw)
```

Примеры вызова (из `99-raw/experiments/E/24-presets/export_all.py`) [проверено]:

```python
# Blender 5.2.2 — [проверено]
exec(open("/abs/path/99-raw/experiments/E/24-presets/presets.py").read())
export("/abs/out/hero_raw.glb", "static_hero")
export("/abs/out/scene_raw.glb", "anim_trs", collection="WEB")          # только коллекция WEB (и вложенные)
export("/abs/out/morph_raw.glb", "anim_morph")
export("/abs/out/instances_raw.glb", "instances")
```

### 7.3. Постобработка к пресетам

```bash
# gltf-transform 4.5.0, gltfpack 1.2 (нативный) — [проверено]
BASE=$DDD_HOME
export PATH="$BASE/bin/KTX-Software-4.4.2-Linux-x86_64/bin:$BASE/bin/gltfpack-1.2:$PATH"
cd "$BASE/node"
npx --no-install gltf-transform optimize /abs/out/hero_raw.glb /abs/out/hero.glb --compress meshopt --texture-compress webp --texture-size 2048 --simplify false
npx --no-install gltf-transform optimize /abs/out/scene_raw.glb /abs/out/scene.glb --compress meshopt --texture-compress webp --flatten false --join false --simplify false
gltfpack -i /abs/out/hero_raw.glb -o /abs/out/hero_mobile.glb -cc -tc -ts 0.5
node validate.mjs /abs/out/hero.glb                                         # валидатор Khronos (JSON с numErrors/numWarnings)
```

### 7.4. Ловушки пресетов (найдены при проверке)

- **Телефонный пресет с `export_image_format="WEBP"`** дал 2.43 МБ вместо 1.53: `gltfpack -tc` не перекодирует WebP-вход, но
  объявляет KHR_texture_basisu обязательным → пресет держит AUTO [проверено].
- `export_apply=True` на объекте с shape keys **без** модификаторов морфы сохраняет (8 из 8); теряет — только при модификаторах
  [проверено].
- `optimize` с квантованием у анимированного объекта: имя `hero_orb` получает обёртка, меш — `hero_orb_1` (`03` §2.4)
  [проверено].
- `optimize` по умолчанию (hero) и gltfpack без `-kn` переименовывают узлы («Mesh016», «mesh_0») — для hero это допустимо, для
  сцен с JS-логикой — нет [проверено].
- `collection="WEB"` из скрипта работает (вспомогательный объект из другой коллекции не попал); `use_renderable` исключил объект с
  `hide_render` [проверено].
- Пресеты не включают `export_lights`/`export_cameras`: свет — кодом (`01` §8.1); «камера из Blender» для скролл-сцен —
  `export_cameras=True` отдельно [проверено].

## Частые ошибки

1. Считать файл готовым, потому что валидатор не выдал ошибок: смысловые потери (процедуры, цветовые пространства, морфы, свет)
   валидатор не видит [проверено].
2. Проверять только в Blender: EEVEE показывает процедурный материал, AO из группы не рендерит, свет Area есть — в three всего
   этого нет; сравнивать в three (`gltf_diff.py`) [проверено].
3. Сравнивать AgX Blender с `NoToneMapping` three и «чинить» материалы из-за разницы тонмаппинга [проверено].
4. Страница без `scene.environment` для металлических материалов — чёрный металл [проверено].
5. Прозрачность «на всякий случай» (Alpha 0.99) — BLEND, выключенная запись глубины, ошибки сортировки [проверено].
6. Стекло в сцене без учёта цены: transmission удваивает вызовы и треугольники [проверено] [S7].
7. Экспорт с умолчаниями оператора вместо пресета: без apply, без extras, со скрытыми объектами [проверено].
8. Модель по памяти пишет параметры 3.x (`export_selected`, `export_colors`) — `TypeError` в 5.2 [проверено].
9. `use_selection=True` в фоне без выделения — пустой файл без ошибки [проверено].
10. Выкладывать `.gltf` + `.bin` + текстуры по частям или с `export_keep_originals` — 404 и белые материалы [проверено].
11. Телефонный пресет с WebP-картинками перед `gltfpack -tc` — KTX2 не получится [проверено].
12. Искать в JS меш по имени после optimize/gltfpack без учёта обёрток и переименований [проверено].
13. Не проверять результат `bpy.ops.object.bake` и экспорта: `{'CANCELLED'}` и пустые файлы проходят молча [проверено].
14. Лечить вывернутые нормали включением двусторонности — ошибка остаётся для volume, теней и других движков [проверено].
15. Предупреждение валидатора `image/ktx2` у gltfpack принимать за поломку [проверено].

## Чек-лист

До экспорта:
- [ ] `preflight()` не выдаёт ERROR, все WARN разобраны?
- [ ] Выбран пресет под задачу (§7), параметры проверены по RNA (`export()` из presets.py)?
- [ ] Сцена в метрах, масштаб применён, origin — в точке вращения?
- [ ] Вспомогательное — в `glTF_not_exported` или вне экспортируемой коллекции?

После экспорта и постобработки:
- [ ] Валидатор: 0 ошибок; предупреждения известны (касательные, non-root skin, `image/ktx2`)?
- [ ] `glb_lint()`: нужные декодеры подключены на странице; вызовы, треугольники и память текстур в бюджете (`03` §6.5)?
- [ ] `gltf_web_inspect.py`: типы материалов и карты с верными `colorSpace`/`channel`; клипы, морфы, `userData` на месте?
- [ ] `gltf_diff.py`: ΔE2000 ≤ 3.5 и IoU ≥ 0.99 к Blender (для стекла — к Cycles)?
- [ ] На странице есть `scene.environment` (если есть металл), свет не удвоен с запечённым?
- [ ] В сцене нет BLEND-прозрачности, где хватает MASK; стекло учтено в бюджете вызовов?
- [ ] Файл выкладывается одним GLB (или папкой целиком), с brotli/gzip на сервере?

## Открытые вопросы и противоречия

1. **Сборка валидатора** (2.0.0-dev.3.10 из npm) не знает `image/ktx2` в images — есть ли новее сборка с поддержкой KTX2 в npm, не
   проверялось; до тех пор предупреждение у gltfpack считать ложным.
2. **Пороги `gltf_diff.py`** (≤ 3.5 / ≥ 0.99) откалиброваны на одной сцене и одном HDRI (E/02); для тёмных сцен, сильного
   тонмаппинга и постобработки их надо перекалибровать (агент J).
3. **Transmission**: `renderer.transmissionResolutionScale = 0.5` — 1,72 → 1,39 мс без видимой потери (F2/05, `../09-web-runtime/04-shaders-effects-catalog-impl.md` §3).
4. **Прозрачность**: `renderOrder`, раздельные меши и `depthWrite=true` для BLEND как лечение сортировки — не проверены в E/23.
5. **Preflight** проверяет материал целиком, а не путь от конкретного сокета: процедурная нода, которая ни к чему не подключена,
   тоже даст WARN (ложная тревога); точный обход по связям от Principled — улучшение для волны 3 (агенты I, J).
6. **Тени** (`castShadow`/`receiveShadow`) не входят в glTF и в пресеты; их цена в вызовах — тема агента F.
7. **Пресеты проверены на Chromium/Linux**; поведение KTX2 и памяти на iOS/Android — не проверено (`03` §3.1).

## Источники

- [S1] Khronos. glTF-Validator 2.0.0-dev.3.10 (npm), коды сообщений. https://github.com/KhronosGroup/glTF-Validator (471 зв., push 2026-09-18) — проверка 242 файлов в E/22.
- [S2] Don McCurdy. glTF Transform 4.5.0 CLI — `inspect`, `optimize --help`, `prune --help`. https://gltf-transform.dev — таблицы inspect, флаги.
- [S3] Arseny Kapoulkine. gltfpack README (meshoptimizer 1.2). https://github.com/zeux/meshoptimizer/tree/master/gltf — `-kn`, `-ke`, `-vpf`, что выбрасывается.
- [S4] Blender Foundation. Blender 5.2 Manual — glTF 2.0. https://docs.blender.org/manual/en/5.2/addons/import_export/scene_gltf2.html — параметры экспорта, выбор объектов, анимация.
- [S5] three.js r186. `examples/jsm/loaders/GLTFLoader.js` — BLEND → `depthWrite=false`, группы примитивов, санитизация имён, ошибки текстур и декодеров; прочитан целиком.
- [S6] glTF-Blender-IO 5.2.40 (в Blender 5.2.2) — `__init__.py`, `blender/exp/*` — умолчания, doubleSided, alphaMode, pointer.
- [S7] three.js r186. `build/three.module.js`, функция `renderTransmissionPass` (WebGLRenderer) — повторный рендер непрозрачных объектов в цель transmission, задние стороны двусторонних прозрачных материалов, `transmissionResolutionScale`; прочитана.
- [S8] Khronos. glTF 2.0 extensions: KHR_materials_transmission, KHR_materials_volume, EXT_mesh_gpu_instancing, KHR_animation_pointer — https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0 — требования, на которые опираются проверки.
- [S9] Агент B, волна 1. `99-raw/reports/wave1-B-report.md` — обёртка `bpyx.export_glb(apply_modifiers=True)` и морфы (сверено с E/07, E/24).
- [S10] Andrew Woan. Building a Fully-Featured 3D World in the Browser with Blender and Three.js. Codrops, 2025-04-08 — проверка ориентации граней (Face Orientation) до текстурирования и запекания; практика.

Эксперименты: `99-raw/experiments/E/22-validator` (242 файла), `23-pitfalls` (6 поломок), `24-presets` (6 пресетов + 3 варианта),
`25-api-drift`, `26-doc-snippets` (preflight, glb_lint, код разделов 4.3 и 4.7), `28-postprocess-data`; симптомы — из E/01–E/21.
