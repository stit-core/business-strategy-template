# 10 · Поле инстансов: 900 объектов — десятки КБ и 1 вызов (генеративный паттерн GN)

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, three r186 · сквозной прогон:
[проверено] · пример: `examples/10-instance-field/`

## Выжимка рецепта

1. Много одинаковых объектов (плитки, «город данных», колонны, листья) — **GN `Instance on Points` без Realize** → пресет E
   `instances` → `EXT_mesh_gpu_instancing` → в three `InstancedMesh`: **1 вызов на прототип**, вес — прототип + 40 байт
   трансформации на инстанс до сжатия [проверено: E/08, D1/07, этот прогон].
2. Вариации — атрибуты инстанса (масштаб, поворот) из `Random Value` с `Seed` — детерминированно; seed в паспорте [проверено: этот прогон].
3. Прототип — отдельный объект вне экспорта (`glTF_not_exported` + `hide_render`), pivot в основании (масштаб Z растит вверх) [проверено].
4. Realize Instances перед экспортом = мегабайты и тысячи вершин (E/08: 100 икосфер 11,8 против 625 КБ); связанные дубликаты
   (`Alt+D`) под одним родителем тоже уходят инстансами (E/24) [проверено].
5. Анимация отдельных инстансов на странице — через `InstancedMesh.setMatrixAt` в JS, не клипом glTF (клип двигает узел целиком)
   [документация three; не проверено здесь].

## 1. Бриф-пример и границы

«Аналитический SaaS: фон hero — поле из 900 скруглённых столбиков разной высоты («город данных»), фирменный цвет, медленный облёт».

| годится | не годится → куда |
|---|---|
| ≥ 20 одинаковых объектов с вариацией трансформации | каждый объект уникален по форме → обычный экспорт или слияние мешей |
| поле/паттерн как фон или иллюстрация | «волна» на тысячах инстансов каждый кадр → вершинный шейдер или шейдерный фон (рецепт 11) |
| телефон: 1 вызов вместо 900 | нужна разная окраска каждого инстанса → атрибут цвета инстанса [не проверено в glTF: `_COLOR_0` у EXT_mesh_gpu_instancing] |

## 2. Паспорт

Сетка 30 × 30 на 1,2 × 1,2 м (шаг 41 мм), прототип — скруглённый столбик 34 × 34 × 100 мм (углы 6 мм, кромка 3 мм), высота
инстанса × 0,2–1,6 (Random, seed 11), цвет #635BFF (пластик с coat), фон #EEF0F6.

## 3. Код: прототип → GN-сетка → инстансы → GLB

```python
# Blender 5.2.2 — [проверено] рецепт 10: 900 GN-инстансов → EXT_mesh_gpu_instancing
import sys, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "10-instance-field"
P = dict(n=30, size=1.2, tile=(0.034, 0.034, 0.1), corner=0.006, edge=0.003, h=(0.2, 1.6), seed=11, color="#635BFF",
         bg="#EEF0F6", cam=dict(az=35, el=32, lens=70, margin=1.05, res=(1280, 720)))


def field_tree(proto, P):
    t, gi, go = bpyx.gn_tree("Field", inputs=[("Seed", "NodeSocketInt", P["seed"])], geometry_input=False)
    grid = bpyx.node(t, "GeometryNodeMeshGrid")
    grid.inputs["Size X"].default_value = grid.inputs["Size Y"].default_value = P["size"]
    grid.inputs["Vertices X"].default_value = grid.inputs["Vertices Y"].default_value = P["n"]
    oi = bpyx.node(t, "GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = proto
    inst = bpyx.node(t, "GeometryNodeInstanceOnPoints")
    rnd = bpyx.node(t, "FunctionNodeRandomValue", data_type="FLOAT")
    rnd.inputs["Min"].default_value, rnd.inputs["Max"].default_value = P["h"]
    xyz = bpyx.node(t, "ShaderNodeCombineXYZ"); xyz.inputs["X"].default_value = xyz.inputs["Y"].default_value = 1.0
    L = lambda a, b: bpyx.link_sockets(t, a, b)  # noqa: E731
    L((grid, "Mesh"), (inst, "Points")); L((oi, "Geometry"), (inst, "Instance"))
    L((gi, "Seed"), (rnd, "Seed")); L((rnd, "Value"), (xyz, "Z")); L((xyz, "Vector"), (inst, "Scale"))
    L((inst, "Instances"), (go, "Geometry"))                          # без Realize
    return t


rk.reset()
C = D.fresh_collection("ASSET_field")
mat = rk.web_material("Field_Plastic", "plastic_gloss", P["color"])
proto = D.rounded_slab("TileProto", *P["tile"], P["corner"], (P["edge"], P["edge"]), None, corner_seg=4, edge_seg=2)
bpyx.assign_material(proto, mat)                                      # низ на z = 0 — масштаб Z растит столбик вверх
hidden = D.fresh_collection("glTF_not_exported"); hidden.objects.link(proto); proto.hide_render = True
for c in list(proto.users_collection):
    if c is not hidden:
        c.objects.unlink(proto)
field = bpy.data.objects.new("Field", bpy.data.meshes.new("Field_empty")); C.objects.link(field)
bpyx.gn_modifier(field, field_tree(proto, P))
dg = bpy.context.evaluated_depsgraph_get()
n_inst = sum(1 for oi in dg.object_instances if oi.is_instance and oi.parent and oi.parent.name == "Field")
assert n_inst == P["n"] ** 2, n_inst
# габарит объекта, у которого GN выдаёт только инстансы, bound_box не видит (кадр «в пустоту») → прокси-габарит из паспорта
hx = P["size"] / 2 + P["tile"][0] / 2; hz = P["tile"][2] * P["h"][1]
proxy = bpyx.mesh_object("FieldBounds", [(x, y, z) for x in (-hx, hx) for y in (-hx, hx) for z in (0, hz)],
                         faces=[(0, 1, 3, 2)], collection=hidden)
proxy.hide_render = True
rk.studio([proxy], bg=P["bg"], E_key=2.5, az=P["cam"]["az"], world=0.5)
rk.camera([proxy], **P["cam"])
rk.neutral(samples=32)
rk.render(SLUG, "field_blender", res=P["cam"]["res"], samples=32)
res = rk.ship(SLUG, "ASSET_field", "field", preset="instances", optimize="meshopt")
assert res["raw"]["instanced_nodes"] == 1 and res["raw"]["tris"] < 1000, res["raw"]   # один узел инстансинга, в файле — прототип
rk.save(SLUG, instances=n_inst, passport=P)
```

## 4. Числа прогона

Прогон: 2,9 с (прототип, GN-сетка 30 × 30, EEVEE 32 спп 1280 × 720 — 2,4 с, экспорт `instances`, meshopt). Итераций — 1: первый
рендер был пустым серым кадром — `bpyx.world_bbox` берёт `bound_box` объекта, а у объекта, чей GN выдаёт **только инстансы**,
габарит инстансов туда не попадает → студия и камера строились вокруг точки; исправлено прокси-габаритом из паспорта (8 вершин в
`glTF_not_exported`).

| величина | значение |
|---|---|
| инстансов | 900 (`assert n == 30²` по `depsgraph.object_instances`) |
| GLB: экспорт → meshopt | **44,8 → 22,0 КБ**; 1 узел `EXT_mesh_gpu_instancing`, в файле 236 треуг. (прототип) |
| three r186 (`gltf_web_inspect.py`) | `InstancedMesh` «Field», **1 вызов**, 212 400 треуг. в кадре (900 × 236); валидатор 0 / 0; 0 ошибок консоли |
| ориентир E/08 | 100 GN-инстансов: 11,8 КБ; с Realize 625 КБ [проверено] |

Взгляд на `examples/10-instance-field/field_blender.png`: поле читается как «город данных» в бренд-цвете, 1 вызов на 900 объектов.
Слабее: высоты — белый шум (`Random Value`) → визуально шумно; для «дорогого» паттерна — плавный шум по позиции
(`Noise Texture` → высота) или волна от центра [не проверено].

## 5. Страница

Загрузка как у любого GLB (эталон hero-lazy, рецепт 01) — `InstancedMesh` three создаёт сам. Движение: облёт камерой (JS, `damp`) или
волна — вершинный шейдер по `instanceMatrix`/`gl_InstanceID` через `onBeforeCompile` [не проверено]; анимировать 900 матриц на
CPU каждый кадр (`setMatrixAt` + `instanceMatrix.needsUpdate`) — дороже, но проще [документация three, не замерено].

## 6. Ворота

`n_inst == n²`, `instanced_nodes == 1`, треугольников в файле < 1000 (прототип, а не 900 копий) — в коде; вызовов в кадре — 1 на
прототип (`gltf_web_inspect.py`: `renderer.calls`); треугольников в кадре на телефоне — ориентир ≤ 300–500 тыс. [практика A/F1].

## 7. Варианты

1. **Несколько прототипов** — `Geometry to Instance` + `Pick Instance` + `Random Value` BOOLEAN (рецепт 07): узел
   `EXT_mesh_gpu_instancing` на прототип.
2. **Связанные дубликаты** (`obj.copy()` с общим `data`) под одним родителем — тоже инстансы (E/24: 100 → 6,3 КБ, 1 вызов).
3. **Точки из поверхности модели** вместо сетки — `Distribute Points on Faces` (рецепт 07) или `D.surface_points` (рецепт 06).
4. **Телефон** — та же сетка 20 × 20 (400 инстансов) или предрендер кадра (рецепт 08).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| Realize Instances «чтобы экспорт увидел» | файл в десятки раз тяжелее, 900 мешей | без Realize + `export_gn_mesh` + `export_gpu_instances` (пресет `instances`) |
| кадр/студия по объекту с GN-инстансами | пустой серый кадр, свет в точке | прокси-габарит или `world_bbox` по реализованной копии (этот прогон) |
| прототип в экспортируемой коллекции | лишний столбик в центре | `glTF_not_exported` + `hide_render` |
| pivot прототипа в центре | масштаб Z растит столбик вниз под пол | низ прототипа на z = 0 (`rounded_slab` строит от z = 0) |
| `bpy.ops.object.duplicate` в цикле 900 раз | минуты, 900 объектов и мешей | GN или связанные дубликаты data API |

## Ссылки

E `../08-export-gltf/01-export-contract.md §4.7`, `../08-export-gltf/03-compression-textures-budgets.md §2.6`, `../99-raw/experiments/E/08-geonodes-instances`;
D1 `../05-modeling/03-geometry-nodes-procedural.md §2`; bpyx `../03-bpy-api/snippets/README.md` (`gn_tree`, `gn_modifier`, `link_sockets`).
