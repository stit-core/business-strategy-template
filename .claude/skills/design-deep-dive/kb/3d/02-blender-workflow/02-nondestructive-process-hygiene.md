# Неразрушающий процесс, порядок модификаторов, гигиена меша и файла

Волна 3 · агент I · 23.09.2026 · Blender 5.2.2 LTS (glTF-IO 5.2.40) · эксперименты `99-raw/experiments/I/02-file-hygiene`
(20 итераций → чистка; резаки булевых), `I/01` (сироты и fake user) · опора: D1 `../05-modeling/`, E `../08-export-gltf/`,
C1 `../04-ai-agents-mcp/04–05`, B `../03-bpy-api/01 §10`, дайджесты W4 · 3 внешних источника + файлы волн 1–2.

Техника моделирования (фаски, булевы, топология, UV-тела) — D1; здесь — **процесс**: в каком порядке, что держать
модификатором, когда применять, как не копить мусор и что проверять кодом. Детекторы антипаттернов кодом — J
(`../11-evaluation-qa/01-scene-geometry-checks.md §2, §5`, `../../scripts/3d/scene_check.py`), здесь — правило и ссылка.

## Выжимка для агента

1. **Источник правды — параметры `P` и `build(P)`**, не состояние сцены: форма — bmesh/кривые из параметров, отделка —
   модификаторы с явными значениями, применение — на экспорте. → §1.1 `[проверено: C1/05, D1]`
2. **Стек модификаторов сверху вниз**: Mirror → Boolean → Weld → Bevel (`harden_normals`) → Subdivision → Triangulate
   (если запекать нормали) → Weighted Normal последним (`keep_sharp`). → §1.2 `[проверено: D1/01, D1/03, W4/02–03; практика]`
3. **Модификатор не добавляй повторно**: ищи свой по имени-роли или пересобирай; 4 Bevel подряд за 20 шагов дали ×26
   треугольников в GLB (16 512 против 632). → §1.2, §6 `[проверено]`
4. **`export_apply=True` применяет уровень вьюпорта** (`levels`, не `render_levels`), выключенный во вьюпорте
   модификатор пропускает, у объектов с модификаторами удаляет shape keys. → §1.3 `[проверено]`
5. **Резак булевых держи в `glTF_not_exported`** (каркасом, скрытым): режет и при `hide_render`, `hide_viewport`,
   `hide_set` и даже из исключённой коллекции, в GLB не попадает. → §1.3, §8 `[проверено: I/02 cutter_visibility]`
6. **Контрольная точка — `save_as_mainfile(copy=True)` в папку задачи** перед разрушительным шагом (apply, join,
   Remesh, Decimate, булевы с применением) и после каждого принятого; undo через MCP нет. → §1.4 `[проверено]`
7. **Повторное сохранение в то же имя создаёт `.blend1`** — и с `copy=True` тоже (`save_version = 1`): история
   из одной копии; контрольные точки нумеруй (`checkpoint_NN.blend`). → §1.4 `[проверено]`
8. **Нормали наружу и острые рёбра данными** (`shade_smooth()` + `set_sharp_from_angle(30°)`); в Blender всё
   двустороннее — вывернутые грани видны только в вебе. → §2 `[проверено]`
9. **Сварка после кривых, текста, SVG, булевых** и проверка неманифолда (решётка без сварки — 3 280 сырых рёбер). → §2 `[проверено]`
10. **N-гоны — только на плоском**, не на изгибе и не под SubD. → §2 `[V:PAK5zQONgvs ≈18:09; V:MD1QmdqXRfc 07:21; через W4]`
11. **UV: ≤ 2 слоя** (материал + lightmap/AO), без перекрытий для запекания; нетекстурный меш — без UV (`export_texcoords=False`). → §3 `[проверено]`
12. **Плотность текселей одна на ассет**: 256–512 px/м для крупных поверхностей, 512–1024 px/м для hero. → §3 `[практика, E 02 §2.3]`
13. **Слоты до индексов граней**: `Mesh.materials.clear()` и `pop()` обнуляют `material_index`; неиспользуемые слоты
    убирай с пересчётом индексов. → §4 `[проверено]`
14. **Для веба — Principled + Image Texture**; процедурное запекай до экспорта. → §4 `[проверено]`
15. **Не «удаляй сдвигом» (`x += 1000`), не прячь вместо удаления, не масштабируй в 0**: такой мусор уходит в GLB —
    габарит сцены 1000,1 м вместо 0,1 м ломает кадрирование в JS. → §6 `[проверено: I/02; C2 03 §8.2]`
16. **Картинки — один раз**: `images.load(path, check_existing=True)`; один PNG, загруженный 4 раза и упакованный,
    — 3,0 МБ в `.blend`. → §5 `[проверено]`
17. **Перед сохранением и экспортом своего файла — `hygiene_report()` и `hygiene_clean()`**: `.blend` 3,82 → 1,32 МБ,
    GLB 1,51 → 0,82 МБ, повторная чистка — 0 изменений. В сцене человека — только отчёт. → §5 `[проверено]`
18. **Сироты без fake user не сохраняются**; мусор держат ссылки (пустые слоты, спрятанные объекты), а не сироты. → §5 `[проверено: I/01, I/02; документация]`
19. **Пути — относительные, текстуры — рядом с файлом** (`//tex/…`); упаковка — только для передачи одним файлом. → §5.3 `[проверено]`
20. **Постер — из того же GLB и той же пары тонмаппинга**, после запекания, а не отдельным рендером сцены до него. → §7 `[проверено: A/07, F1 hero-lazy]`
21. **Булевы в процессе агента — да, для статичного hard-surface**, неразрушающе до экспорта, EXACT + чистка; плоские
    вырезы — контуром; деформируемое — без булевых. → §8 `[проверено: D1/03; спор — W4 §4]`

## 1. Неразрушающий процесс

### 1.1. Что где живёт

| Слой | Чем делается | Живёт в | Когда меняется |
|---|---|---|---|
| размеры, пропорции, отношения частей | паспорт `P` (метры) | словарь в файле скрипта рядом с задачей | правка брифа |
| базовая форма | bmesh, кривые, тела D1 (`loft_slab`, `lathe`, `sweep`), GN | `build(P)`, пересобирается целиком | каждый запуск |
| отделка: фаски, сглаживание, SubD, WN, булевы | модификаторы с явными значениями (`bpyx.add_modifier`) | стек объекта | параметр `P` или шаг отделки |
| материал | Principled + текстуры; процедурное — запечь | по тегу/роли (`01 §2`) | шаг материалов |
| анимация | действие со слотами после геометрии и pivots (H) | `build(P)` | шаг анимации |
| применение модификаторов | `export_apply=True` или копия с применением | только экспорт | экспорт |

«Модификатор против bmesh» (D1): модификатор — неразрушающая отделка поверх, bmesh — пересборка из параметров; порядок
проверок D1: форма → чистота меша → `preflight()` E → экспорт → `gltf_check` → `web_view` (`../05-modeling/README.md`).
Код частями против идемпотентного `build(P)`: после ошибки, смены параметра и потери сцены `build` приходит к тому же
состоянию, частями — к дублям `Ceramic.001`, `Mug.001` и `KeyError` (C1/05, M6.3, M6.5).

### 1.2. Порядок стека

| # | Модификатор | Зачем | Условие | Доказательство |
|---|---|---|---|---|
| 1 | Mirror | симметрия; шов на оси — `use_clip`, `use_mirror_merge` | до всего, что зависит от формы целиком | `[практика]` |
| 2 | Boolean (EXACT) | вырезы статичного hard-surface | замкнутые меши, масштаб применён, резак одним мешем | D1/03 |
| 3 | Weld | склеить швы после Boolean, кривых, текста | сразу после источника шва | D1/03 |
| 4 | Bevel | фаска 1–3 % размера; `harden_normals=True`; `limit_method='ANGLE'` | до SubD — как опорные петли (`segments=2`, `profile=1.0`: кромка 98,3 %) | D1/01, W4/02 |
| 5 | Subdivision | гладкие формы | `levels` = то, что уйдёт в GLB (экспорт берёт вьюпорт) | E/07, `preflight` `SUBSURF_LEVELS` |
| 6 | Triangulate | зафиксировать разбиение перед запеканием нормалей | только если запекаются карты нормалей | `[V:PAK5zQONgvs ≈12:39]` через W4, D1 §1.3 |
| 7 | Weighted Normal | ровный глянец плоских граней; `keep_sharp=True` | последним; сила граней — атрибут `__mod_weightednormals_faceweight` | D1/01, W4/03 |

- Добавлять модификатор идемпотентно: `m = ob.modifiers.get("bevel_main") or ob.modifiers.new("bevel_main", "BEVEL")` и
  задать все значения явно — повторный шаг не создаст второй. В I/02 «добавь фаску» четырежды дало 4 Bevel подряд:
  632 → 16 512 треугольников после `export_apply` [проверено].
- Имя модификатора для кода — своё и стабильное (`bevel_main`); умолчание «Bevel» при повторе становится «Bevel.001».
- Значения — явно: у `bmesh.ops.bevel` и модификатора разные умолчания (D1 `../05-modeling/02`); вход GN-модификатора —
  `mod.properties.inputs.<id>.value` + `ob.update_tag()` (B `../03-bpy-api/02 §5.2`).

### 1.3. Что применять и когда

| Ситуация | Действие | Почему | Доказательство |
|---|---|---|---|
| экспорт статики | `export_apply=True` (пресет E), стек не трогать | экспорт берёт вычисленный меш | E/07, E/24 |
| SubD: `levels` ≠ `render_levels` | выставить `levels` на нужное для веба | экспорт берёт уровень вьюпорта | E, `preflight` |
| модификатор выключен во вьюпорте, включён в рендере | включить или удалить | `export_apply` его не применит (`MOD_VIEWPORT_OFF`) | E/26 |
| морфы (shape keys) + модификаторы | применить модификаторы **до** создания ключей или `export_apply=False` | `export_apply` удаляет shape keys молча (`SHAPEKEYS_WITH_MODIFIERS`) | E/07, H `../07-animation/02 §1` |
| GN-инстансы | `export_apply` + `export_gn_mesh` + `export_gpu_instances` | иначе инстансы теряются | E/08 |
| резак Boolean | в `glTF_not_exported`, каркасом, скрыт | режет из любой видимости и из исключённой коллекции; в GLB не идёт | I/02 `cutter_visibility.py` |
| перед Remesh, Decimate, join, применением булевых | контрольная точка | разрушительно, undo нет | C1 `04 §10.2` |
| масштаб объекта ≠ 1 | применить без переноса origin (`01 §7.1`) | фаски и модификаторы искажаются масштабом | M2.10 |

### 1.4. Контрольные точки

```python
# Blender 5.2.2 — [проверено] контрольная точка без смены текущего файла; нумерация вместо .blend1
import os, tempfile
import bpy

def checkpoint(workdir, label):
    os.makedirs(workdir, exist_ok=True)
    n = len([f for f in os.listdir(workdir) if f.startswith("checkpoint_") and f.endswith(".blend")])
    path = os.path.join(workdir, f"checkpoint_{n:02d}_{label}.blend")
    current = bpy.data.filepath
    assert bpy.ops.wm.save_as_mainfile(filepath=path, copy=True, compress=True) == {"FINISHED"}
    assert bpy.data.filepath == current                        # copy=True не переключает файл
    return path

work = tempfile.mkdtemp(prefix="task_")
p1 = checkpoint(work, "blockout")
p2 = checkpoint(work, "bevels")
assert os.path.basename(p2) == "checkpoint_01_bevels.blend" and not os.path.exists(p2 + "1")
print(sorted(os.listdir(work)))
```

- `save_as_mainfile(copy=True)` не меняет `bpy.data.filepath` (B/14); сохранение в существующее имя — с `copy=True`
  или без — оставляет `.blend1`, одну резервную копию по `preferences.filepaths.save_version = 1` (два сохранения
  `copy=True` в `c.blend` → `c.blend` + `c.blend1`) [проверено].
- Заводские настройки: `use_file_compression = True` (Zstd; сетка 201×201: 3,06 → 0,91 МБ, B/14), `use_relative_paths = True`.
- Где хранить: папка задачи C1 `04 §10.3` (`<task>/checkpoint_NN.blend`, `runs/NN/`); восстановление после сбоя —
  C1 `04 §10.2` и O (`../04-ai-agents-mcp/06-headless-operations.md`).

## 2. Топология и нормали как гигиена

Что агент проверяет после каждого `build(P)` (детекторы и пороги — J `../11-evaluation-qa/01-scene-geometry-checks.md §2, §5`
и `../../scripts/3d/scene_check.py`; техника — D1 `05 §1–4`):

| Правило | Как выполнить кодом | Как проверить кодом | Доказательство |
|---|---|---|---|
| нормали наружу | `bmesh.ops.recalc_face_normals` после ручных граней | глина-рендер; доля граней, смотрящих к центру | D1 §4.4, E/12 |
| острые рёбра — данными | `me.shade_smooth(); me.set_sharp_from_angle(angle=radians(30))` | атрибут `sharp_edge`; вершин glTF | D1/01, E/03 |
| угол сглаживания | 30° (умолчание 5.2) | — | W4: в ролике DECODED 35° — ошибка |
| сварка швов | `bmesh.ops.remove_doubles(dist=1e-5)` после кривых, SVG, текста, Boolean | число открытых рёбер = 0 для замкнутых | D1/03 |
| n-гоны только на плоском | строить квадами; `cap_tris` на видимых торцах | n-гон с отклонением нормалей вершин > порога | W4 (Lampel, PzThree), D1 §1.2 |
| двойные вершины и внутренняя геометрия | идемпотентная сборка (нет повторов объектов) | совпадающие вершины; пересечение BVH | C1 M2.3, J |
| неприменённый масштаб | `01 §7.1` | `preflight` `UNAPPLIED_SCALE` | E/26 |
| неманифолд | замкнутые тела | `bmesh` рёбра с ≠ 2 гранями | D1 §4.1 |

## 3. UV и плотность текселей

- Тела D1 создают UV при построении (`loft_slab`, `lathe`, `sweep`; экран мокапа — 0–1) — в фоне развёртка
  `bpyx.uv_unwrap(ob, "SMART" | "LIGHTMAP")`; CUBE перекрывает острова (D1 `05 §5`, E `02`).
- ≤ 2 UV-слоёв: материал и lightmap/AO; three читает 4, лишние уходят в файл (E `01 §4.3`). В I/02 дописывающий агент
  накопил 4 слоя — `hygiene_clean()` их не трогает (не знает, какие нужны), отчёт показывает `extra_uv`.
- Нетекстурный меш — `export_texcoords=False` или `gltf-transform prune`: UV без текстуры — 8 байт на вершину и +10 %
  вершин на швах (E/03, E/22).
- Плотность текселей — `texel_density()` E `02 §2.3` (плоскость 2×2 м, 1024² → 512 px/м) после `view_layer.update()`;
  ориентиры 256–512 px/м для крупных поверхностей, 512–1024 px/м для hero `[практика]`; отступы запекания 16 px для 1–2k,
  4–8 px для 512² и меньше (E/19–21).

## 4. Материалы и слоты

- `Mesh.materials.clear()` и `pop()` в 5.2.2 обнуляют `material_index` всех граней (C1/12) — сначала слоты, потом индексы;
  убирать слоты — с запоминанием индексов (`remove_unused_slots()` в I/02 `hygiene.py`).
- Материал — один на роль: в своём файле по имени с переиспользованием, в сцене человека по тегу (`01 §2`); новый
  материал на каждый шаг «поменяй цвет» дал в I/02 9 материалов и 4 пустых слота из 5.
- Дубли по содержимому (одинаковые ноды, значения, картинки, связи) сливаются `dup.user_remap(base)`; имя в сигнатуру
  не входит [проверено].
- Для веба — Principled BSDF + Image Texture (+ Normal Map, Separate Color); процедурные ноды и Color Ramp теряются
  (ΔE 18–33, E) — запекать (`../08-export-gltf/02`), `preflight()` E ловит `NODE_LOST`, `SHADER_LOST`, `MIX_SHADER`.
- Цвет — sRGB-картинки и hex → линейный; данные (roughness, normal) — Non-Color (E `01 §5.4`, D2, W3).

## 5. Гигиена файла

### 5.1. Что копится (эксперимент I/02)

20 итераций «кодом частями» по кругу: «поменяй цвет» (новый материал + слот), «переделай ручку» (старая сдвинута на
`x += 1000`), «добавь фаску» (ещё один Bevel), «глазурь текстурой» (`images.load()` того же PNG + `pack()` + новый
материал + UV-слой), «поправь ракурс» (новая камера), каждые 7 шагов — спрятанная копия [проверено]:

| | После 20 итераций | После `hygiene_clean()` |
|---|---|---|
| `.blend` без сжатия | 3,82 МБ | 1,32 МБ (сжатый 0,84 МБ) |
| объекты / меши / материалы / картинки / камеры | 13 / 8 / 9 / 4 / 5 | 3 / 2 / 2 / 1 / 1 |
| имён `.NNN` | 28 | 0 |
| упаковано | 3,0 МБ (PNG ×4) | 0,75 МБ |
| «удалены сдвигом» / спрятанные копии | 4 / 2 | 0 / 0 |
| Bevel подряд / пустые слоты | 4 / 4 из 5 | 1 / 0 |
| GLB `static_hero` | 1,51 МБ, 6 узлов, 5 материалов, 16 512 треуг., габарит X 1000,1 м | 0,82 МБ, 2 узла, 2 материала, 632 треуг., 0,103 м |

Сирот до чистки — 0: старые материалы держались пустыми слотами; после удаления мусора `orphans_purge` снял 20 ID.
Повторная чистка — 0 изменений.

### 5.2. Функция чистки своего файла

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/I/02-file-hygiene; напечатанный блок — I/04-doc-blocks] чистка СВОЕГО файла
import re
import bmesh
import bpy
from mathutils import Vector

DUP = re.compile(r"^(.*)\.\d{3}$")

def world_center(ob):
    return sum((ob.matrix_world @ Vector(c) for c in ob.bound_box), Vector()) / 8

def mat_signature(mat):
    """Материал как данные (ноды, несвязанные входы, картинки, связи); имя не входит."""
    nodes = []
    for n in sorted(mat.node_tree.nodes, key=lambda n: (n.bl_idname, n.name)):
        vals = []
        for s in n.inputs:
            v = getattr(s, "default_value", None)
            if s.is_linked or v is None:
                continue
            if isinstance(v, float):
                v = round(v, 4)
            elif not isinstance(v, (str, int)):
                v = tuple(round(float(x), 4) for x in v)
            vals.append((s.identifier, v))
        img = getattr(n, "image", None)
        nodes.append((n.bl_idname, tuple(vals), img.filepath if img else None))
    links = sorted((l.from_node.bl_idname, l.from_socket.identifier, l.to_node.bl_idname, l.to_socket.identifier)
                   for l in mat.node_tree.links)
    return tuple(nodes), tuple(links)

def hygiene_clean(export_coll, far=100.0):
    sc, done = bpy.context.scene, {}
    bpy.context.view_layer.update()                                                 # иначе matrix_world устаревшая
    exp = set(export_coll.all_objects)
    junk = [o for o in sc.objects if o.type == "MESH" and (world_center(o).length > far
            or (o in exp and (o.hide_render or o.hide_viewport)))]                  # «сдвинутые» и спрятанные
    junk += [o for o in sc.objects if o.type == "CAMERA" and o != sc.camera]        # лишние камеры
    for o in junk:
        bpy.data.objects.remove(o, do_unlink=True)
    done["objects"] = len(junk)
    done["modifiers"] = 0
    for o in sc.objects:                                                            # повтор шага → один модификатор типа
        seen = set()
        for m in reversed(list(o.modifiers)):
            t = m.type                                                              # до remove: потом ссылка висячая
            if t in seen:
                o.modifiers.remove(m); done["modifiers"] += 1
            seen.add(t)
    for o in sc.objects:                                                            # пустые слоты, индексы граней сохраняются
        if o.type == "MESH" and len(o.material_slots) > 1:
            me = o.data
            idx = [0] * len(me.polygons); me.polygons.foreach_get("material_index", idx)
            used = sorted(set(idx)); keep = [me.materials[i] for i in used]
            me.materials.clear()
            for m in keep:
                me.materials.append(m)
            me.polygons.foreach_set("material_index", [used.index(i) for i in idx]); me.update()
    groups = {}
    for m in sorted((m for m in bpy.data.materials if m.users), key=lambda m: (len(m.name), m.name)):
        groups.setdefault(mat_signature(m), []).append(m)
    done["materials_merged"] = sum(len(g) - 1 for g in groups.values())
    for g in groups.values():
        for dup in g[1:]:
            dup.user_remap(g[0])
    done["orphans"] = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.cameras):
        for idb in list(coll):
            m = DUP.match(idb.name)
            if m and m.group(1) not in coll:
                idb.name = m.group(1)
    return done

# демонстрация: мусор «кодом частями» → чистка → повторная чистка ничего не меняет
bpy.ops.wm.read_factory_settings(use_empty=True)
web = bpy.data.collections.new("WEB"); bpy.context.scene.collection.children.link(web)
def cyl(name, x):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.04, radius2=0.04, depth=0.1); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.location.x = x; web.objects.link(ob); return ob
body = cyl("Mug", 0)
for i in range(3):
    cyl("Handle", 1000 + i)                                  # «удалено сдвигом»
    body.modifiers.new("Bevel", "BEVEL")                     # фаска повторно
    body.data.materials.append(bpy.data.materials.new("Ceramic"))
assert [m.name for m in body.modifiers] == ["Bevel", "Bevel.001", "Bevel.002"]   # имя по умолчанию получает .001
first = hygiene_clean(web)
again = hygiene_clean(web)
assert first["objects"] == 3 and first["modifiers"] == 2 and len(body.data.materials) == 1
assert body.data.materials[0].name == "Ceramic" and len(bpy.data.materials) == 1
assert again == {"objects": 0, "modifiers": 0, "materials_merged": 0, "orphans": 0}
print(first, again)
```

Полная версия с отчётом (`hygiene_report()`: `.NNN`, сироты, fake user, далёкие и спрятанные объекты, дубли
материалов и картинок, упакованные байты, повторные модификаторы, пустые слоты, лишние UV, камеры) и слиянием картинок —
`99-raw/experiments/I/02-file-hygiene/hygiene.py`. **В сцене человека не применять** (удаляет скрытое и сирот всего
файла) — там только `hygiene_report()` и уборка своего по тегу (`01 §2`).

### 5.3. Сироты, fake user, пути, упаковка

- ID без пользователей и без fake user Blender в `.blend` не пишет [S1] — в I/01 материал `Draft` и картинка `moodboard`
  пропали после сохранения; `texts.new()` в 5.2.2 создаёт текст сразу с `use_fake_user=True`.
- Fake user держит ID вечно: действие только с fake user **не экспортируется** (`preflight` `FAKE_USER_ACTION`, E) —
  снимать fake user со своих рабочих действий и материалов перед сдачей.
- Пути — абсолютные в коде (`os.path.abspath`), относительные в файле: `save_as_mainfile(relative_remap=True)` перепривязывает
  картинки (`//../tex/a.png`); `//` без сохранённого `.blend` указывает в никуда (B `../03-bpy-api/01 §10.2`).
- Упаковка (`img.pack()`) — только для передачи одним файлом; иначе текстуры — файлами в папке задачи. `images.load(path,
  check_existing=True)` вместо повторной загрузки (в I/02 четыре копии одного PNG — 3,0 МБ).
- `export_keep_originals` в glTF ссылается на исходные картинки по относительным путям, в том числе вне папки экспорта —
  при выкладке текстуры теряются (E/16).

## 6. Костыли нейросетей: запрещено

| Костыль | Откуда | Что ломает | Вместо |
|---|---|---|---|
| «удалить» сдвигом `x += 1000` | промт SceneCraft (C2 `03 §8.2`) | мусор в GLB: габарит 1000,1 м, +узлы, +материалы (I/02) | `bpy.data.objects.remove(ob)` своего по тегу |
| спрятать вместо удалить (`hide_viewport`, `hide_render`) | «на время» | экспорт по умолчанию уносит скрытое (E/10); в файле растёт мусор | удалить или в `glTF_not_exported` |
| масштаб 0 «чтобы не было видно» | по памяти | вырожденные матрицы, NaN нормалей `[не проверено]` | удалить |
| новый материал / модификатор / камера на каждый шаг | диалоговый стиль | `.001`, пустые слоты, ×26 треугольников (I/02) | идемпотентный `build(P)`, поиск по роли |
| стирание сцены в начале скрипта | 24/24 первых попыток (C1/11) | работа человека (I/01) | своя коллекция и тег (`01 §1–2`) |
| `orphans_purge()` в сцене человека | haiku 8/8 | его отвязанные данные (I/01) | своё по тегу |
| `bpy.ops.wm.read_factory_settings` в MCP-сеансе | «чистый лист» | интерфейс и настройки человека (B `01 §2.5`) | своя сцена превью |
| `sys.exit()` в `execute_blender_code` | привычка скриптов | закрывает Blender человека без сохранения (M7.1) | `raise` |
| оператор в цикле по объектам | `bpy.ops.mesh.primitive_*_add` ×N | ×50–700 медленнее data API (B `01 §11`), зависит от выделения | bmesh/data API |

## 7. Постер из запечённого состояния

Постер (картинка до загрузки 3D) — из того же состояния модели, что уходит в GLB (после запекания), иначе при замене
картинка «прыгает» (A `../01-web-3d-landscape/05` п. 5, A/07). F1 пошёл дальше: постер снимается из **того же GLB в
three** той же парой тонмаппинга и тем же кадром (`../09-web-runtime/examples/hero-lazy/make_poster.py`, AVIF 19,8 КБ,
F1 `05 §6`). Процесс агента: запекание → экспорт → постобработка → `make_poster.py` → проверка ворот `gate_check()` F1;
рендер Blender для постера — только если 3D на странице нет (D2 `../06-materials-lighting-render/04`).

## 8. Булевы в процессе агента

Спор (V §3, W4 §4): VideoSmile — булевы вредят обучению моделированию; Gambrell — hard-surface на булевых с опорным
разрезом и стеком Boolean → Bevel → Weld → WN [V:0T3QdLJOBF8 03:43, 11:49]; PzThree — «boolean + n-gon» только для
статики и запекания [V:MD1QmdqXRfc 22:52]; Lampel — булевы → ремеш → ретопология как быстрый путь [V:PAK5zQONgvs ≈43:09]
(все — через W4). Аргумент «учиться ли на булевых» агенту не нужен. Техническая позиция — D1 `../05-modeling/05 §3`
(EXACT + очистка для статики, контур с отверстиями для плоских вырезов ×4 быстрее, деформируемое — без булевых).
Позиция о процессе:

1. Boolean — **неразрушающий шаг** до экспорта: резак — отдельный объект с тегом `part="cutter_*"` в
   `glTF_not_exported`, каркасом; режет при любой видимости и из исключённой коллекции [проверено].
2. Применять булевы (`export_apply` или `modifier_apply`) — после контрольной точки; после применения — Weld, limited
   dissolve, пересчёт нормалей, острые рёбра, Bevel(harden), WN (`d1lib.boolean_apply`, D1/03).
3. Параметр выреза (радиус, шаг) — в `P`; менять параметр, а не двигать резак руками.
4. Перфорация ≥ 20–30 отверстий — карта на простой пластине, а не булевы (D1 `[мнение]`).
5. Под деформацию (скиннинг, морфы) и SubD-поверхности — без булевых (обрыв потока рёбер; W4 PzThree, D1 §3.3).

## Частые ошибки

1. **Повторный шаг добавляет второй модификатор, материал, камеру** — `.001`, пустые слоты, ×26 треугольников [I/02].
2. **SubD `levels` 0–1 во вьюпорте «для скорости»** — в GLB уходит грубая форма (экспорт берёт вьюпорт) [E].
3. **Shape keys на объекте с модификаторами + `export_apply`** — морфы молча удалены [E/07, H].
4. **Резак булевых в коллекции экспорта** без `hide_render` — уходит в GLB как объект [E/10; I/02].
5. **Сохранение поверх одного имени** как «контрольная точка» — одна `.blend1`, история потеряна [I/02].
6. **`materials.clear()` после назначения индексов** — все грани на слоте 0 [C1/12].
7. **`images.load()` без `check_existing` в цикле + `pack()`** — копии картинки в `.blend` [I/02].
8. **Скрытые «на время» объекты** — в файле и в экспорте по умолчанию [E/10, I/02].
9. **`orphans_purge()` как «чистка» в сцене человека** — его отвязанные данные [I/01].
10. **Процедурный материал до веба** — теряется (ΔE 18–33) [E].
11. **Постер отдельным рендером до запекания** — «прыжок» при замене [A/07].

## Чек-лист

- [ ] Форма строится `build(P)` из параметров, модификаторы добавлены идемпотентно (по имени-роли), значения явные?
- [ ] Порядок стека: Mirror → Boolean → Weld → Bevel → SubD → (Triangulate) → WN?
- [ ] SubD `levels` = уровень для веба; нет модификаторов, выключенных только во вьюпорте?
- [ ] Морфы: модификаторы применены до ключей или `export_apply=False`?
- [ ] Резаки — в `glTF_not_exported`; после применения булевых — сварка и чистка?
- [ ] Контрольная точка `checkpoint_NN` перед разрушительным шагом?
- [ ] Нормали наружу, острые рёбра данными, швы сварены, неманифолда нет?
- [ ] ≤ 2 UV-слоя, нетекстурный меш без UV, плотность текселей одна?
- [ ] Нет пустых слотов; материалы — Principled + текстуры?
- [ ] `hygiene_report()`: нет `.NNN`, далёких и спрятанных объектов в коллекции экспорта, повторных модификаторов, дублей?
- [ ] Пути относительные, картинки не упакованы (или упакованы ради передачи одним файлом)?
- [ ] Постер — из того же GLB (`make_poster.py`)?

## Открытые вопросы и противоречия

- **Повторные модификаторы**: `hygiene_clean()` оставляет последний модификатор каждого типа — верно для «повтора
  шага», неверно для намеренного стека (два Bevel с разными ширинами, два Array). Для своего файла с `build(P)` повторов
  быть не должно; для чужих ассетов — только отчёт.
- **Визуальная равноценность «до/после чистки»** не сравнивалась рендером (удаление повторных Bevel меняет форму) — после
  чистки прогнать проверки J заново.
- **Порог «далёкого» объекта** 100 м — для сцен-комнат и ландшафтов нужен порог от паспорта (размер сцены × 10).
- **Масштаб 0 как «скрытие»** — последствия не проверялись (`[не проверено]`).
- **Mirror первым** — `[практика]`, в эксперименте не проверялось.

## Источники

- [S1] Blender Foundation. Blender Manual 5.2 — Data-Blocks: Life Time, Protected. https://docs.blender.org/manual/en/5.2/files/data_blocks.html
  — ID без пользователей не пишутся в файл; fake user защищает; официально.
- [S2] Blender Foundation / Khronos. Blender Manual 5.2 — glTF 2.0 add-on (Apply Modifiers: «evaluated mesh»; Include).
  https://docs.blender.org/manual/en/5.2/addons/import_export/scene_gltf2.html — официально.
- [S3] Blender Python API 5.2 — Gotchas: Internal Data and Python Objects. https://docs.blender.org/api/5.2/info_gotchas_internal_data_and_python_objects.html
  — висячие ссылки после удаления и смены режима (подробно — B `01 §2.6`); из кэша.
- Видео (через дайджесты W4): [V:PAK5zQONgvs] Lampel, BCon 2024; [V:MD1QmdqXRfc] PzThree; [V:0T3QdLJOBF8] Gambrell;
  индекс `../91-videos/digests/_index-W4.md`.
- Файлы базы: D1 `../05-modeling/05 §1–5`, `02`, README; E `../08-export-gltf/01 §3, §4.3, §4.6, §5`, `02 §2.3`, `04 §5`;
  C1 `../04-ai-agents-mcp/04 §5, §10`, `05` M2.3, M2.10, M6.3, M6.5, M7.1; C2 `../04-ai-agents-mcp/03 §8.2`; B `../03-bpy-api/01 §2.5, §10, §11`;
  A `../01-web-3d-landscape/05` п. 5; F1 `../09-web-runtime/05 §6`, `../09-web-runtime/examples/hero-lazy`; H `../07-animation/02 §1`.
