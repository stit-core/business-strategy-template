# 07 · Low-poly диорама: остров параметрами, палитра-текстура, разброс GN-инстансами (и путь к запечённому свету)

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, three r186 · сквозной прогон:
[проверено] · пример: `examples/07-lowpoly-diorama/`

## Выжимка рецепта

1. Low-poly — **параметрами** (тело вращения 12 сегментов, конусы 6–7, икосфера 1 + дрожание вершин с seed), не Decimate;
   `shade_flat` [проверено: D1/07, W4].
2. Цвет — **одна палитра-текстура 8 × 1 px** (`Closest`) на всю сцену: UV каждой грани → центр ячейки цвета; один материал = меньше
   вызовов; цвета вершин не годятся для AR (A `01/05 §3.2`) [проверено] [V:EhZwt9P4GP4 03:40].
3. Повторы (деревья, камни) — **GN-инстансы без Realize** → пресет E `instances` (`export_gn_mesh` + `export_gpu_instances`) →
   `EXT_mesh_gpu_instancing`: по узлу на прототип, в three — `InstancedMesh`; с Realize файл в 3,6 раза тяжелее [проверено].
4. Прототипы — в коллекции `glTF_not_exported` (экспортёр пропускает её всегда) и `hide_render` [проверено].
5. Изометрия — орто-камера az 45°, el 35,264° (D1 `frame(ortho=True)`); жанр «парящий остров» — клише портфолио (A `01/01 §22`):
   брать, когда диорама объясняет продукт (карта, процесс, «мир» бренда).
6. Свет «как в Blender» на странице — **запечь в unlit** (DIFFUSE DIRECT+INDIRECT+COLOR → `KHR_materials_unlit`): ΔE 0,73 к Cycles,
   лучшее совпадение Blender ↔ веб в базе; цена — уникальная карта 1024² ≈ 0,8–0,95 МБ и только статика [проверено].

## 1. Бриф-пример и границы

«Лендинг туристического сервиса: маленький остров с деревьями в изометрии, светлый фон, лёгкое вращение; на телефоне легко».

| годится | не годится → куда |
|---|---|
| стилизованная сцена-иллюстрация, 1 материал, ≤ 20 тыс. треуг. | фотореализм → PBR + HDRI, KTX2 (рецепт 01 §7.3) |
| повторяющиеся элементы (деревья, дома, люди) | уникальные детали без повторов → обычный экспорт (`static_hero`) |
| статика или вращение всей сцены | движущиеся объекты под запечённым светом → «прилипшие» тени: путь B lightMap или свет на странице (E `08/02 §6.5`) |

## 2. Паспорт

Палитра 8 hex (трава, листва, ствол, земля, камень ×2, песок, вода); остров Ø 1,04 м, высота 0,59 м; дерево 0,25 м, камень 0,04 м;
разброс: Пуассон, минимум 85 мм, только грани с нормалью z > 0,6, 28 % камней, масштаб 0,7–1,25, поворот Z; seed 7. Кадр — орто
изометрия, 512², фон #E8EEF2.

## 3. Код: build(P) → GN-разброс → изометрия → GLB с инстансами

```python
# Blender 5.2.2 — [проверено] рецепт 07: low-poly остров (3d 05/04 §6: палитра, GN-инстансы)
import sys, random, bpy, bmesh
from mathutils import Vector, Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "07-lowpoly-diorama"
P = dict(palette=["#7CB36B", "#5E9451", "#8A6A4F", "#6B5242", "#B9B2A6", "#8F8A82", "#E8D8A8", "#6FA8C9"],
         seed=7, dist_min=0.085, rock_share=0.28, bg="#E8EEF2", res=(768, 768))


def palette_material(pal, path):
    img = bpy.data.images.new("palette", len(pal), 1)
    lin2srgb = lambda c: c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055   # noqa: E731
    px = [v for h in pal for v in bpyx.color(h)]
    img.pixels.foreach_set([lin2srgb(v) if i % 4 != 3 else v for i, v in enumerate(px)])
    img.filepath_raw = path; img.file_format = "PNG"; img.save()
    im = bpy.data.images.load(path); im.colorspace_settings.name = "sRGB"
    m, pr = bpyx.principled("LowPoly_Palette", roughness=0.85)
    tex = m.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = im; tex.interpolation = "Closest"
    bpyx.link_sockets(m.node_tree, (tex, "Color"), (pr, "Base Color"))
    return m


def paint(ob, idx_fn, mat, n):
    uv = ob.data.uv_layers.get("UVMap") or ob.data.uv_layers.new(name="UVMap")
    for p in ob.data.polygons:
        k = idx_fn(p)
        for li in p.loop_indices:
            uv.data[li].uv = ((k + 0.5) / n, 0.5)                  # грань → центр ячейки палитры
    ob.data.shade_flat()
    bpyx.assign_material(ob, mat)


def jitter(ob, amount, seed):
    rng = random.Random(seed)
    for v in ob.data.vertices:
        v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * amount
    ob.data.update()


def scatter_tree(tree, rock, P):
    t, gi, go = bpyx.gn_tree("Scatter", inputs=[("Seed", "NodeSocketInt", P["seed"])])
    nrm = bpyx.node(t, "GeometryNodeInputNormal"); sep = bpyx.node(t, "ShaderNodeSeparateXYZ")
    cmp = bpyx.node(t, "FunctionNodeCompare", data_type="FLOAT", operation="GREATER_THAN"); cmp.inputs["B"].default_value = 0.6
    dist = bpyx.node(t, "GeometryNodeDistributePointsOnFaces", distribute_method="POISSON")
    dist.inputs["Distance Min"].default_value = P["dist_min"]; dist.inputs["Density Max"].default_value = 60.0
    oi_t = bpyx.node(t, "GeometryNodeObjectInfo"); oi_t.inputs["Object"].default_value = tree
    oi_r = bpyx.node(t, "GeometryNodeObjectInfo"); oi_r.inputs["Object"].default_value = rock
    pick = bpyx.node(t, "FunctionNodeRandomValue", data_type="BOOLEAN"); pick.inputs["Probability"].default_value = P["rock_share"]
    g2i = bpyx.node(t, "GeometryNodeGeometryToInstance")
    inst = bpyx.node(t, "GeometryNodeInstanceOnPoints"); inst.inputs["Pick Instance"].default_value = True
    rs = bpyx.node(t, "FunctionNodeRandomValue", data_type="FLOAT"); rs.inputs["Min"].default_value = 0.7; rs.inputs["Max"].default_value = 1.25
    rr = bpyx.node(t, "FunctionNodeRandomValue", data_type="FLOAT_VECTOR"); rr.inputs["Max"].default_value = (0, 0, 6.283)
    L = lambda a, b: bpyx.link_sockets(t, a, b)  # noqa: E731
    L((nrm, "Normal"), (sep, "Vector")); L((sep, "Z"), (cmp, "A"))
    L((gi, "Geometry"), (dist, "Mesh")); L((cmp, "Result"), (dist, "Selection")); L((gi, "Seed"), (dist, "Seed"))
    L((dist, "Points"), (inst, "Points"))
    L((oi_t, "Geometry"), (g2i, "Geometry")); L((oi_r, "Geometry"), (g2i, "Geometry")); L((g2i, "Instances"), (inst, "Instance"))
    L((pick, "Value"), (inst, "Instance Index")); L((gi, "Seed"), (pick, "Seed"))
    L((rs, "Value"), (inst, "Scale")); L((rr, "Value"), (inst, "Rotation")); L((gi, "Seed"), (rs, "Seed")); L((gi, "Seed"), (rr, "Seed"))
    L((inst, "Instances"), (go, "Geometry"))                          # без Realize → EXT_mesh_gpu_instancing
    return t


def build(P):
    C = D.fresh_collection("ASSET_island")
    n = len(P["palette"]); mat = palette_material(P["palette"], f"{rk.out_dir(SLUG)}/palette.png")
    prof = [(0.0, -0.55), (0.18, -0.42), (0.34, -0.22), (0.46, -0.06), (0.52, 0.0), (0.5, 0.03), (0.0, 0.035)]
    island = D.lathe("Island", prof, C, segments=12, smooth_angle=None)
    jitter(island, 0.018, 1)
    paint(island, lambda p: 0 if p.normal.z > 0.6 else (3 if p.center.z > -0.2 else 5), mat, n)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.018, radius2=0.013, depth=0.09, matrix=Matrix.Translation((0, 0, 0.045)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.075, radius2=0.0, depth=0.13, matrix=Matrix.Translation((0, 0, 0.13)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.055, radius2=0.0, depth=0.10,
                          matrix=Matrix.Translation((0, 0, 0.2)) @ Matrix.Rotation(0.4, 4, "Z"))
    tree = D.obj_from_bm(bm, "TreeProto", C, smooth_angle=None)
    paint(tree, lambda p: 2 if p.center.z < 0.07 else (1 if p.center.z < 0.18 else 0), mat, n)
    rock = bpyx.primitive("icosphere", "RockProto", radius=0.04, subdivisions=1, collection=C)
    jitter(rock, 0.008, 3); rock.data.transform(Matrix.Scale(0.6, 4, (0, 0, 1)))
    paint(rock, lambda p: 4 if p.normal.z > 0.3 else 5, mat, n)
    hidden = D.fresh_collection("glTF_not_exported")                 # прототипы: экспортёр пропускает эту коллекцию
    for proto in (tree, rock):
        C.objects.unlink(proto); hidden.objects.link(proto); proto.hide_render = True
    flora = bpy.data.objects.new("Flora", island.data.copy()); C.objects.link(flora)
    flora.data.materials.clear(); flora.data.materials.append(mat)
    bpyx.gn_modifier(flora, scatter_tree(tree, rock, P))
    return C, island, flora


rk.reset()
C, island, flora = build(P)
dg = bpy.context.evaluated_depsgraph_get()
n_inst = sum(1 for oi in dg.object_instances if oi.is_instance and oi.parent and oi.parent.name == "Flora")
assert 10 <= n_inst <= 80, n_inst                                     # разброс не пустой и не «лес»
rk.studio([island, flora], bg=P["bg"], E_key=2.5, az=45, world=0.7)
rk.camera([island, flora], az=45, el=35.264, ortho=True, margin=1.08, res=P["res"])
rk.neutral(samples=32)
rk.audit()
rk.render(SLUG, "iso_blender", res=P["res"], samples=32)
res = rk.ship(SLUG, "ASSET_island", "island", preset="instances", optimize="meshopt")
assert res["raw"]["instanced_nodes"] >= 2, res["raw"]                 # по узлу EXT_mesh_gpu_instancing на прототип
rk.save(SLUG, instances=n_inst, passport=P)
```

## 4. Числа прогона

Прогон: 2,3 с (сборка, GN-разброс, EEVEE 32 спп 768² орто — 1,9 с, экспорт `instances`, meshopt). Итераций — 0 (код D1/07).

| величина | значение |
|---|---|
| инстансов | 25 (деревья и камни, Пуассон 85 мм, seed 7) |
| GLB: экспорт → meshopt | **19,1 → 14,5 КБ**; 4 узла (остров, корень Flora, 2 узла `EXT_mesh_gpu_instancing` — по прототипу), 184 треуг. в файле; 1 материал + палитра 8 × 1 px |
| с Realize Instances (D1/07) | 69,2 КБ, 788 треуг. в файле (× 3,6) [проверено] |
| three r186 | `InstancedMesh` по прототипу, 3 меша, 1 текстура 8 px, 0 ошибок; валидатор 0 / 0 |
| аудит | кадр 67 %, `raw_sharp_edges` острова (low-poly — рёбра острые намеренно) |

Взгляд на `examples/07-lowpoly-diorama/iso_blender.png`: аккуратная стилизованная диорама, деревья и камни стоят на траве, ни один
не висит и не торчит за край; палитра читается. Слабее: «парящий остров» — клише; для продукта нужны объекты смысла (дома, маршрут,
маркеры `hotspot_*` с extras — D1/07).

## 5. Страница

GLB без текстур-фото (14,5 КБ) → эталон hero-lazy рецепта 01 (`HERO_CFG`), или `web_view.py`-подобный просмотрщик. Инстансы
three создаёт сам (`GLTFLoader` → `InstancedMesh`, 1 вызов на прототип) — ручной код не нужен. Маркеры для интерактива
(`hotspot_island_top` с `label`) → `userData` при `export_extras` (пресет E), поиск по имени после `optimize --flatten false`
(E/24: у квантованного меша имя — у родителя) [проверено]. Путь камеры по острову — JSON-кривая (рецепт 05).

## 6. Ворота

`assert 10 ≤ инстансов ≤ 80` (разброс не пуст); `instanced_nodes ≥ 2` в сыром GLB (инстансинг не потерян); вызовов в кадре ≤ 30 на
телефоне (здесь 3–4); вес ≤ 0,8 МБ; валидатор 0 ошибок.

## 7. Варианты

1. **Запечённый свет (путь A, unlit)**: второй UV `LightUV` → Cycles DIFFUSE `{"DIRECT","INDIRECT","COLOR"}` 1024², 64 спп (4,2 с) →
   `unlit_baked_material` → `KHR_materials_unlit`; ΔE 0,73 к Cycles; но инстансы при запекании — только после Realize (карта
   уникальна на всю сцену) → вес 0,8–0,95 МБ PNG, KTX2 ETC1S — меньше; код — E `../08-export-gltf/02-baking.md §6.1` [проверено].
2. **Путь B (lightMap)**: запечь только освещённость, PBR остаётся (ΔE 0,74–0,89), `lightMap` в three ×π (E `08/02 §6.2`).
3. **Больше объектов** — тот же GN-граф, другие прототипы; 900 объектов = 20 КБ и 1 вызов (рецепт 10).
4. **Изометрическая комната** — `rounded_slab` для стен/мебели + та же палитра [не проверено: D1 не достроил].
5. **Точки/путь для частиц и камеры** из того же острова — `D.surface_points`, `D.export_curve_json` (рецепты 05, 06).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| Decimate «для стиля» | рваная сетка, треугольники-иглы | low-poly параметрами (сегменты 6–16) (W4, D1) |
| цвет — отдельный материал на объект | десятки вызовов, материалов | палитра-текстура 8 × 1, `Closest` |
| палитра без `Closest` / без sRGB | цвета «плывут» между ячейками, блёклые | `interpolation = "Closest"`, `colorspace = sRGB`, значения в sRGB |
| Realize Instances перед экспортом | ×3,6 вес, нет инстансинга | без Realize + пресет `instances` |
| прототипы в экспортируемой коллекции | лишние объекты в центре сцены | коллекция `glTF_not_exported` + `hide_render` |
| орто-камера «на глаз» | изометрия с перекосом | az 45°, el 35,264° (`frame(ortho=True)`) |

## Ссылки

D1 `../05-modeling/04-styles-and-archetypes.md §6`, `../05-modeling/03-geometry-nodes-procedural.md §2`, `../99-raw/experiments/D1/07-lowpoly-gn-data`;
E `../08-export-gltf/01-export-contract.md §4.7`, `../08-export-gltf/02-baking.md §6`; A `../01-web-3d-landscape/05-blender-deliverables-map.md §3`.
