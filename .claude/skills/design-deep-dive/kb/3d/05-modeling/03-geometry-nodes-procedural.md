# Geometry nodes и процедурное для веба: разброс, инстансы, точки, SDF-блобы, Mesh Bevel — из кода Blender 5.2

Волна 2 · агент D1 · 23.09.2026 · источники: RNA/сокеты GN-нод Blender 5.2.2 (зонд D1/00, 84 ноды), release notes 5.2
Geometry Nodes (кэш), B `../03-bpy-api/02 §5` (API входов 5.2), E `../08-export-gltf/01 §4.7`, `03 §2.6`, C2/C1 (исследования
«GN из текста»), ролики через заметки помощников · эксперименты D1/01, D1/06, D1/07 · Blender 5.2.2 LTS, glTF-IO 5.2.40,
three r186. Все блоки `python` выполнены в напечатанном виде (`99-raw/experiments/D1/09-doc-snippets`).

## Выжимка для агента

1. **Дерево GN — только через проверенные обёртки**: `bpyx.gn_tree` (интерфейс), `bpyx.node` (режим до сокетов), `bpyx.link_sockets` (проверка `is_valid`), `bpyx.gn_modifier`/`gn_set_input` (входы 5.2). Сырые деревья из текста компилируются в 0 % (Proc3D, через C2). → §1 [проверено: B, D1/01, D1/06, D1/07; исследование через C2]
2. **Входы модификатора 5.2 — `mod.properties.inputs.<id>.value` + `ob.update_tag()`**; `mod["Socket_2"]` → TypeError. → §1 [проверено: B]
3. **Свойства многих нод стали входами-меню**: значение — отображаемое имя строкой (`"Edges"`, `"Count"`), не `node.mode = 'COUNT'`. → §1 [проверено: B, D1/00]
4. **Повторы — инстансы без Realize**: `Instance on Points` + экспорт `export_gn_mesh` + `export_gpu_instances` (пресет E `instances`) → узлы `EXT_mesh_gpu_instancing`: 25 деревьев/камней — 19,1 КБ против 69,2 КБ с Realize. → §2 [проверено]
5. **Разные прототипы в одном разбросе** — `Geometry to Instance` (оба прототипа) + `Instance on Points` с `Pick Instance=True` и индексом из `Random Value`; прототипы — в коллекции `glTF_not_exported`. → §2 [проверено]
6. **Разброс только по «верху»** — `Normal` → `Separate XYZ` → `Compare Z > 0,6` в `Selection`; ровный шаг — `POISSON` с `Distance Min`. → §2 [проверено]
7. **Точки GN детерминированы при том же seed** (869 = 869, координаты побайтно), **но их число = плотность × площадь**: для морфинга форм с одинаковым N — своя выборка `d1lib.surface_points(ob, N, seed)`. → §3 [проверено]
8. **Точки из GN читай через `Points to Vertices`** → `attributes["position"].foreach_get`; облако точек не лежит в `evaluated.data` меш-объекта. → §3 [проверено]
9. **Точки для частиц — Float32 (x, z, −y), 12 байт на точку**; путь — JSON по имени кривой. → §3 [проверено: D1/07; A `../01-web-3d-landscape/05 §3.8–3.9`]
10. **Блоб — SDF-ноды 5.2**: `Points to SDF Grid` → `SDF Grid Fillet` → `SDF Grid Mean` → `Grid to Mesh`; без Mean — «гроздь шаров». Воксель 3,5–4 мм на 0,2 м — 13–19 тыс. треуг., 0,2 с. → §4 [проверено]
11. **Метаболы быстрее SDF (0,01 с) и дают меньше треугольников при той же ячейке** (7,7 против 13,8 тыс.), но без сглаживания поля и булевых. → §4 [проверено]
12. **Нода `Mesh Bevel` (новое в 5.2)**: в режиме Edges ширину задают 4 входа `Start/End Left/Right Offset` (по умолчанию 0,1 м!), вход `Offset` на рёбра не влияет; результат = модификатор Bevel. Брать только внутри GN-деревьев. → §5 [проверено: D1/01 E, E0]
13. **Realize Instances — только если нужна общая геометрия** (булевы, сварка, запекание); иначе ×3–53 к весу (D1/07, E/08). → §2.3 [проверено]
14. **GN перед экспортом**: `export_apply=True` (пресет E) или `new_from_object`; инстансы без Realize в `new_from_object` не попадают. → §6 [проверено: B, E]
15. **Процедурный шум для формы — в вершины**: `d1lib.noise_displace` (mathutils.noise, seed) или GN `Set Position` + `Noise Texture` (поле) с применением; процедурная текстура в материале до веба не доедет. → §4.3 [проверено: D1/06; B; E]
16. **Не пиши большие деревья «одним куском»**: 5–12 нод на функцию, одна функция = одно дерево с интерфейсом и тестом числа вершин. → §1 [мнение D1; исследования через C2: 1–3 точных примера лучше 5+ общих]

## 1. GN-дерево из кода

Правила B (`../03-bpy-api/02 §2, §5`): ноды ищутся и создаются по `bl_idname`; режим (`data_type`, `distribute_method`,
`operation`, `domain`) — до обращения к сокетам; сокет — по имени среди доступных (`enabled`); связь проверяется
`is_valid`; входы модификатора 5.2 — через `mod.properties.inputs` и `update_tag()`. Имена сокетов 5.2.2 брать из
`python3 ../../scripts/3d/bpy_probe.py node <bl_idname> [prop=value]` или зонда D1/00 (например, `GeometryNodeMeshBevel`:
Mesh, Selection, Affect Kind, Start Left Offset, Start Right Offset, End Left Offset, End Right Offset, Offset, Miter, Spread,
Segments, Shape, Profile → Mesh, Vertex Face, Edge Face, Outer Edge, Mid Edge) [проверено].

Почему обёртки: сырые geometry nodes из текста компилируются в 0 % (Proc3D), 1–3 точных похожих примера поднимают
компиляцию кода Blender 40,8 → 70 % (BlenderRAG), 5+ общих примеров вредят сильным моделям (C2 `../04-ai-agents-mcp/03`, через
C1 и задание) [исследование].

```python
# Blender 5.2.2 — [проверено] GN-дерево обёртками: интерфейс, режим до сокетов, is_valid
import sys; sys.path.insert(0, "../../scripts/3d")
import bpy, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
t, gi, go = bpyx.gn_tree("Pebbles", inputs=[("Density", "NodeSocketFloat", 300.0), ("Seed", "NodeSocketInt", 1)])
dist = bpyx.node(t, "GeometryNodeDistributePointsOnFaces", distribute_method="RANDOM")   # режим — до сокетов
ico = bpyx.node(t, "GeometryNodeMeshIcoSphere", inputs={"Radius": 0.01, "Subdivisions": 1})
inst = bpyx.node(t, "GeometryNodeInstanceOnPoints")
for a, b in [((gi, "Geometry"), (dist, "Mesh")), ((gi, "Density"), (dist, "Density")), ((gi, "Seed"), (dist, "Seed")),
             ((dist, "Points"), (inst, "Points")), ((ico, "Mesh"), (inst, "Instance")), ((inst, "Instances"), (go, "Geometry"))]:
    bpyx.link_sockets(t, a, b)                                     # невалидная связь → ValueError, а не тишина
plane = bpyx.primitive("plane", "Ground", size=0.5)
mod = bpyx.gn_modifier(plane, t, Density=300.0)
dg = bpy.context.evaluated_depsgraph_get()
n1 = sum(1 for oi in dg.object_instances if oi.is_instance and oi.parent and oi.parent.name == "Ground")
bpyx.gn_set_input(mod, "Density", 600.0)                           # вход 5.2 + update_tag внутри
dg = bpy.context.evaluated_depsgraph_get()
n2 = sum(1 for oi in dg.object_instances if oi.is_instance and oi.parent and oi.parent.name == "Ground")
print(n1, n2)
assert n1 > 0 and n2 > n1 * 1.5
```

## 2. Разброс и инстансы

### 2.1. Схема D1/07 (low-poly остров)

`Distribute Points on Faces` (POISSON, `Distance Min` 85 мм, `Density Max` 60; `Selection` = нормаль Z > 0,6) →
`Instance on Points` (`Pick Instance=True`; `Instance` = `Geometry to Instance`(дерево, камень); `Instance Index` =
`Random Value` BOOLEAN с вероятностью 0,28; `Scale` = `Random Value` FLOAT 0,7–1,25; `Rotation` = `Random Value` FLOAT_VECTOR
(0, 0, 0…2π)). Прототипы — объекты в коллекции `glTF_not_exported` (экспортёр её никогда не пишет, E `01 §3.3`), в дерево —
через `Object Info`. 25 инстансов [проверено].

| Экспорт (пресет E) | Узлы | Треуг. в файле | GLB |
|---|---|---|---|
| `instances` (`export_gn_mesh` + `export_gpu_instances`), без Realize | 4: остров, корень, 2 × `EXT_mesh_gpu_instancing` (по прототипу) | 184 | **19,1 КБ** |
| `static_hero` + Realize Instances в дереве | 2 | 788 | 69,2 КБ (×3,6) |

E/08: 100 икосфер — 11,8 КБ и 1 вызов отрисовки против 625 КБ; 900 инстансов — 20–61 КБ против 0,8–24 МБ (E `03 §2.6`)
[проверено E]. Ограничения экспортёра: экземпляры — меши без детей с общим mesh; вариации материалов теряются; расширение
пишется только в `extensionsUsed` (E `01 §4.7`).

```python
# Blender 5.2.2 — [проверено] два прототипа по случайному выбору + разброс по «верху»
import sys; sys.path.insert(0, "../../scripts/3d")
import bpy, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
hidden = bpy.data.collections.new("glTF_not_exported"); bpy.context.scene.collection.children.link(hidden)
tree = bpyx.primitive("cone", "TreeProto", radius=0.05, depth=0.15, segments=7, collection=hidden)
rock = bpyx.primitive("icosphere", "RockProto", radius=0.03, subdivisions=1, collection=hidden)
t, gi, go = bpyx.gn_tree("Scatter", inputs=[("Seed", "NodeSocketInt", 7)])
N = lambda idn, **kw: bpyx.node(t, idn, **kw)
nrm, sep = N("GeometryNodeInputNormal"), N("ShaderNodeSeparateXYZ")
cmp = N("FunctionNodeCompare", data_type="FLOAT", operation="GREATER_THAN"); cmp.inputs["B"].default_value = 0.6
dist = N("GeometryNodeDistributePointsOnFaces", distribute_method="POISSON")
dist.inputs["Distance Min"].default_value = 0.08; dist.inputs["Density Max"].default_value = 60.0
oi_t = N("GeometryNodeObjectInfo"); oi_t.inputs["Object"].default_value = tree
oi_r = N("GeometryNodeObjectInfo"); oi_r.inputs["Object"].default_value = rock
g2i, inst = N("GeometryNodeGeometryToInstance"), N("GeometryNodeInstanceOnPoints")
inst.inputs["Pick Instance"].default_value = True
pick = N("FunctionNodeRandomValue", data_type="BOOLEAN"); pick.inputs["Probability"].default_value = 0.3
L = lambda a, b: bpyx.link_sockets(t, a, b)
L((nrm, "Normal"), (sep, "Vector")); L((sep, "Z"), (cmp, "A"))
L((gi, "Geometry"), (dist, "Mesh")); L((cmp, "Result"), (dist, "Selection")); L((gi, "Seed"), (dist, "Seed"))
L((oi_t, "Geometry"), (g2i, "Geometry")); L((oi_r, "Geometry"), (g2i, "Geometry"))   # индекс 0 — дерево, 1 — камень
L((dist, "Points"), (inst, "Points")); L((g2i, "Instances"), (inst, "Instance"))
L((pick, "Value"), (inst, "Instance Index")); L((inst, "Instances"), (go, "Geometry"))
ground = bpyx.primitive("plane", "Ground", size=1.0)
bpyx.gn_modifier(ground, t)
dg = bpy.context.evaluated_depsgraph_get()
kinds = [oi.object.data.name for oi in dg.object_instances if oi.is_instance and oi.parent and oi.parent.name == "Ground"]
print(len(kinds), sorted(set(kinds)))
assert len(kinds) > 20 and len(set(kinds)) == 2
```

### 2.2. Разнообразие без клонов

Повторы глаз узнаёт: случайные масштаб и поворот, 2–3 прототипа, неравномерная плотность [V:H1oNuKChsdU 27:53, 28:48]
[V:OVbIOHAI3iY 08:18]. В GN — `Random Value` с общим `Seed` на входе дерева (одна ручка на вариант), прототипы — по
`Pick Instance`. Для веба каждый прототип — отдельный узел инстансинга (1 вызов отрисовки на прототип).

### 2.3. Когда Realize

Нужна общая геометрия: булево с разбросом, сварка, запекание света/AO в один атлас, `optimize` без поддержки инстансов у
потребителя. Цена — ×3,6 (D1/07) … ×53 (E/08) к весу и столько же к памяти GPU (E `03 §2.6`) [проверено].

## 3. Точки поверхности и данные для веба

| Способ | Число точек | Порядок | Время | Где |
|---|---|---|---|---|
| GN `Distribute Points on Faces` (RANDOM, Density 400) + `Points to Vertices` | = плотность × площадь (869 на острове), не заказывается | тот же seed → идентичны побайтно; другой seed → другие точки | единицы мс | D1/07 |
| `d1lib.surface_points(ob, N, seed)` (площади треугольников + `random.Random(seed)`) | ровно N | детерминирован; одинаковый N на каждую форму — для морфинга | 2 048 точек < 0,1 с | D1/07, t10 |

Вывод на диск: `export_points_f32(points, path)` — Float32 LE в осях three `(x, z, −y)`, 12 байт на точку (2 048 точек —
24 576 байт); путь камеры — `export_curve_json("cam_orbit", path, samples=96)`: кривая берётся **по имени** (не
`active_object`), точки вычисленной кривой в мире, равномерная пересборка, JSON `[[x, z, −y], …]` + флаг замкнутости
[проверено]. Формат и загрузчики на странице — A `../01-web-3d-landscape/05 §3.8–3.9`, F.

```python
# Blender 5.2.2 — [проверено] точки GN (детерминизм) и ровно N точек для морфинга
import sys, os, tempfile; sys.path.insert(0, "../../scripts/3d")
import numpy as np, bpy, d1lib as D, bpyx         # d1lib первым: он добавляет путь к bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
src = bpyx.primitive("uvsphere", "Shape", radius=0.1)
def gn_points(ob, density, seed):
    t, gi, go = bpyx.gn_tree("Pts", inputs=[("Seed", "NodeSocketInt", seed)])
    dist = bpyx.node(t, "GeometryNodeDistributePointsOnFaces", distribute_method="RANDOM")
    dist.inputs["Density"].default_value = density
    p2v = bpyx.node(t, "GeometryNodePointsToVertices")              # облако точек → вершины (читаются foreach_get)
    for a, b in [((gi, "Geometry"), (dist, "Mesh")), ((gi, "Seed"), (dist, "Seed")), ((dist, "Points"), (p2v, "Points")),
                 ((p2v, "Mesh"), (go, "Geometry"))]:
        bpyx.link_sockets(t, a, b)
    tmp = bpy.data.objects.new("Probe", ob.data); bpy.context.scene.collection.objects.link(tmp)
    bpyx.gn_modifier(tmp, t)
    me = tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    buf = np.empty(len(me.vertices) * 3, np.float32); me.attributes["position"].data.foreach_get("vector", buf)
    bpy.data.objects.remove(tmp, do_unlink=True)
    return buf.reshape(-1, 3)
a, b = gn_points(src, 2000.0, 1), gn_points(src, 2000.0, 1)
assert len(a) == len(b) and np.array_equal(a, b)                    # тот же seed → тот же порядок
pts = D.surface_points(src, 1024, seed=3)                            # ровно 1024 — одинаково для каждой формы морфинга
info = D.export_points_f32(pts, os.path.join(tempfile.mkdtemp(), "shape.bin"))
print(len(a), info["count"], info["bytes"])
assert info["bytes"] == 1024 * 12
```

## 4. Органика: SDF, метаболы, шум

### 4.1. SDF-блоб (новые ноды grid/SDF в 5.2.2)

`d1lib.sdf_blob_gn(name, balls, voxel, fillet_iter, smooth_width, smooth_iter)`: вершины-центры с атрибутом `radius` →
`Mesh to Points` (Radius = атрибут) → `Points to SDF Grid` (Radius, Voxel Size) → `SDF Grid Fillet` (Iterations —
скругляет впадины между шарами) → `SDF Grid Mean` (Width, Iterations — общее сглаживание поля) → `Grid to Mesh` (Threshold 0)
→ `Set Shade Smooth` → применить. В 5.2.2 есть также `Mesh to SDF Grid`, `SDF Grid Boolean` (Union/Difference/Intersect),
`SDF Grid Offset`, `SDF Grid Laplacian`, `Mesh to Volume`/`Volume to Mesh` (зонд D1/00) [проверено: D1/00; в экспериментах —
только цепочка точек].

| Вариант | Треуг. | Время | Вид |
|---|---|---|---|
| 3 шара, воксель 4 мм, fillet 4 (блоб 0,2 м) | 13 756 | 0,23 с | гладкие стыки |
| метаболы, ячейка 4 мм (те же шары, радиус ×1,6) | 7 664 | 0,01 с | похоже, без управления сглаживанием |
| 5 шаров, воксель 3,5 мм, fillet 6, без Mean | 24 988 | — | «гроздь шаров» |
| 5 шаров, воксель 3,5 мм, fillet 10, Mean 3/4 + шум 4 мм | 18 788 (79 КБ meshopt) | — | цельная капля |

[проверено: D1/06, smoke-тест `sdf_blob_gn` в D1/06]. Треугольники растут как (размер / воксель)²: воксель ×2 → ×¼ треугольников
[мнение: по геометрии изоповерхности, отдельно не мерялось].

```python
# Blender 5.2.2 — [проверено] SDF-капля из перекрывающихся шаров и метаболы
import sys; sys.path.insert(0, "../../scripts/3d")
import bpy, bmesh, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
balls = [(0.0, 0.0, 0.085, 0.065), (0.022, 0.008, 0.135, 0.052), (0.008, -0.006, 0.18, 0.04), (-0.014, 0.004, 0.215, 0.03)]
blob = D.sdf_blob_gn("Blob", balls, voxel=0.005, fillet_iter=10, smooth_width=3, smooth_iter=4)
D.noise_displace(blob, strength=0.003, scale=18, octaves=2, seed=5)   # детерминированный шум — сразу в вершины
meta = D.metaball_mesh("Meta", [(x + 0.3, y, z, r * 1.6) for x, y, z, r in balls], resolution=0.005)
for o in (blob, meta):
    bm = bmesh.new(); bm.from_mesh(o.data)
    assert all(e.is_manifold for e in bm.edges) and not o.modifiers, o.name
    bm.free()
print(bpyx.object_stats(blob)["tris"], bpyx.object_stats(meta)["tris"])
```

### 4.2. Когда SDF, когда метаболы, когда шейдер

- Статичный блоб на странице — меш (SDF или метаболы) в GLB, 80–120 КБ после meshopt (D1/06).
- Анимированный «живой» блоб — не в Blender: шейдер со смещением вершин или raymarching SDF на странице (A: эффект «блобы» —
  класс «шейдер», Blender не нужен — `../01-web-3d-landscape/01 §5`); хромированный блоб — клише (A §22).
- Шум формы — в вершины (`noise_displace`, `mathutils.noise`, seed) — экспортируется как обычная геометрия; процедурная
  текстура в материале в glTF теряется (E `01 §5.8`).

### 4.3. Кривые в меш

Трубки и кабели: GN `Curve to Mesh` (профиль `Curve Circle`, Fill Caps) — пример B `../03-bpy-api/02 §5.5` [проверено B];
в 5.2 есть ассет «Curve to Tube» (руководство, через помощника) [не проверено]. Если нужны закрут, переменное сечение и UV —
`d1lib.sweep` (файл 02 §4.2).

## 5. Нода `Mesh Bevel` (5.2)

«The long awaited Mesh Bevel node is now available» (release notes 5.2 GN, коммит c53b03f46a) [документация]. В 5.2.2 у ноды
в режиме `Affect Kind = "Edges"` ширину задают четыре входа `Start Left Offset`, `Start Right Offset`, `End Left Offset`,
`End Right Offset` (по умолчанию **0,1 м** каждый); вход `Offset` (тоже 0,1) в этом режиме на ширину не влияет: дерево с
поданным только `Offset = 1,5 мм` разрушило блок 10 см (диск и стенки) [проверено: D1/01 E0]. С шириной во всех четырёх
входах результат совпал с модификатором Bevel 3 сегм. до числа: 956 треуг., 854 вершины glTF, 33,7 КБ [проверено: D1/01 E].
Выход `Outer Edge` — выборка внешних рёбер фаски (удобно пометить их острыми через `Set Shade Smooth` domain EDGE).
Правило: для модели вне GN — модификатор Bevel (проще, меньше ловушек); нода — когда фаска нужна посреди GN-дерева (после
разброса, булевых GN, процедурных панелей).

```python
# Blender 5.2.2 — [проверено] Mesh Bevel (5.2): ширина — во все 4 входа сторон
import sys, math; sys.path.insert(0, "../../scripts/3d")
import bpy, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
ob = D.rounded_slab("Block", 0.10, 0.07, 0.035, 0.012, 0.0, smooth_angle=30.0)     # острые рёбра → атрибут sharp_edge
t, gi, go = bpyx.gn_tree("Bevel", inputs=[("Width", "NodeSocketFloat", 0.0015), ("Segments", "NodeSocketInt", 3)])
sel = bpyx.node(t, "GeometryNodeInputNamedAttribute", data_type="BOOLEAN"); sel.inputs["Name"].default_value = "sharp_edge"
bev = bpyx.node(t, "GeometryNodeMeshBevel")
bpyx.link_sockets(t, (gi, "Geometry"), (bev, "Mesh")); bpyx.link_sockets(t, (sel, "Attribute"), (bev, "Selection"))
for side in ("Start Left Offset", "Start Right Offset", "End Left Offset", "End Right Offset"):
    bpyx.link_sockets(t, (gi, "Width"), (bev, side))                 # умолчание каждого — 0,1 м
bpyx.link_sockets(t, (gi, "Segments"), (bev, "Segments")); bpyx.link_sockets(t, (bev, "Mesh"), (go, "Geometry"))
bpyx.gn_modifier(ob, t)
mn, mx = bpyx.world_bbox([ob])
print([round(v, 4) for v in (mx - mn)], bpyx.object_stats(ob)["tris"])
assert abs((mx - mn).x - 0.10) < 1e-4 and abs((mx - mn).z - 0.035) < 1e-4   # габарит не «разнесло»
```

## 6. Перед экспортом

- `export_apply=True` (все пресеты E, кроме морфов) применяет GN с уровнем вьюпорта; инстансы — только с `export_gn_mesh`
  (+ `export_gpu_instances` для `EXT_mesh_gpu_instancing`), иначе в glTF уходит базовый меш (E/08) [проверено E].
- Применить в данные без экспорта: `bpyx.apply_modifiers(ob)` / `new_from_object`; инстансы без Realize туда не попадают
  (B `02 §5.4`) [проверено B].
- Атрибуты, записанные GN, в glTF — только с именем на «_» и `export_attributes=True` (E `01 §4.5`) [проверено E].
- Точки и пути для страницы — не через glTF, а файлами `.bin`/`.json` (§3) — gltfpack выбрасывает свои атрибуты (E `03 §4.3`).

## 7. Цена в треугольниках и килобайтах (замеры D1)

| Объект | Треуг. | GLB | После meshopt |
|---|---|---|---|
| разброс 25 инстансов (low-poly) | 184 в файле (788 развёрнуто) | 19,1 КБ (69,2 КБ Realize) | — |
| SDF-капля 0,25 м, воксель 3,5 мм | 18 788 | 346 КБ | 79 КБ |
| лента по узлу (sweep, не GN) | 26 400 | 593 КБ | 117 КБ |
| блок с `Mesh Bevel` 3 сегм. | 956 | 33,7 КБ | — |

[проверено]. Бюджеты — файл 05 §4.

## Частые ошибки

1. **Дерево GN «по памяти»**: `node.mode = 'COUNT'`, `mod["Socket_2"]`, `outputs[1]` у Random Value — ошибки 5.x (B B8.7, №79–84).
2. **Сокет до режима ноды** — связь с недоступным сокетом, `is_valid=False` молча (B8.2).
3. **Вход модификатора без `update_tag()`** — результат не пересчитан (B8.8).
4. **`Mesh Bevel` c одним `Offset`** — фаска 10 см [проверено].
5. **Realize Instances «на всякий случай»** — ×3,6–53 к весу [проверено].
6. **Прототипы разброса в экспортируемой коллекции** — лишние узлы в GLB; класть в `glTF_not_exported` [проверено].
7. **Точки морфинга из Distribute Points** — разное N у разных форм; нужна своя выборка ровно N [проверено].
8. **Чтение точек из `evaluated.data` при выходе Points** — облака там нет; `Points to Vertices` [проверено].
9. **Блоб из шаров без сглаживания поля** — «гроздь» [проверено].
10. **Процедурная текстура в материале как «форма»** — в glTF теряется; форма — в вершины [E; D1/06].

## Чек-лист

- [ ] Дерево собрано обёртками bpyx, все связи `is_valid`, режимы нод заданы до сокетов?
- [ ] Входы модификатора — `mod.properties.inputs` + `update_tag()`?
- [ ] Повторы — инстансы без Realize, прототипы в `glTF_not_exported`, экспорт пресетом `instances`?
- [ ] Разброс: выборка по нормали, POISSON для ровного шага, случайные масштаб/поворот от одного seed?
- [ ] Точки для страницы: ровно N, детерминированно, Float32 (x, z, −y); путь — JSON по имени кривой?
- [ ] Блоб: SDF с fillet и Mean (или метаболы), воксель под бюджет, шум — в вершины?
- [ ] `Mesh Bevel`: ширина во всех 4 входах сторон?
- [ ] GN применены (`export_apply`) и число треугольников после применения — в бюджете?

## Открытые вопросы и противоречия

- Число точек `Distribute Points on Faces` (RANDOM) не изменилось при смене seed (869 = 869) — похоже, число на грань
  считается от площади и плотности без случайности; точки другие. Для POISSON не проверялось. `[не проверено]`
- Ассеты 5.2 «Array» (GN), «Scatter on Surface», «Curve to Tube» из Essentials — описаны в руководстве (через помощника), из кода
  не проверялись. `[не проверено]`
- Сравнение цены GN-дерева и Python-построения по времени пересборки на больших сценах не делалось. `[не проверено]`
- Как экспортёр ведёт себя с инстансами, у которых разные материалы на прототипах (два прототипа — два узла — в D1/07 работало;
  вариации материала на инстанс теряются по E). 

## Источники

- [S1] Blender 5.2.2 RNA/сокеты GN-нод — зонд `99-raw/experiments/D1/00-api-probe/probe.json` [проверено].
- [S2] Blender Foundation. Release notes 5.2 — Geometry Nodes, https://developer.blender.org/docs/release_notes/5.2/geometry_nodes/
  (кэш `99-raw/cache/developer.blender.org_docs_release_notes_5.2_geometry_nodes_2051d459.md`; разделы Mesh Bevel, Lists,
  Attributes) [документация].
- [S3] B: `../03-bpy-api/02-nodes-from-python.md` §2, §5 (API входов 5.2, 4 примера GN), `03-version-drift-3.6-to-5.2.md` №79–85 [проверено B].
- [S4] E: `../08-export-gltf/01-export-contract.md` §4.5, §4.7; `03-compression-textures-budgets.md` §2.6, §4.3 [проверено E].
- [S5] A: `../01-web-3d-landscape/05-blender-deliverables-map.md` §3.8–3.10 (точки, пути, маркеры) [практика A].
- [S6] C2: `../04-ai-agents-mcp/03-research-llm-3d.md` (Proc3D — 0 % компиляции сырых GN; BlenderRAG — 1–3 примера) [исследование через C2].
- [S7] Эксперименты D1/01, D1/06, D1/07, `_lib/test_d1lib.py` [проверено].
- [S8] Ethan Redd, «Low Poly Modeling: Style Through Economy», GDC 2017, https://www.youtube.com/watch?v=H1oNuKChsdU — вариативность и
  повторы, через `D1-subnotes/videos-style-gn.md` [практика].
- [S9] CG Cookie, «6 key principles for 3D modeling», 2019, https://www.youtube.com/watch?v=OVbIOHAI3iY — повтор с вариацией [практика].
- [S10] Blender 5.2 Manual — Modifiers (новый Array на GN, Curve to Tube, Scatter on Surface), через `D1-subnotes/manual-modifiers-curves.md` [документация].
