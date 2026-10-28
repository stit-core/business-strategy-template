# Доводка сгенерированного, отсканированного и скачанного ассета до веба

Волна 2 · агент G · 23.09.2026 · режим экономии заказчика · источников: 6 (README TRELLIS.2 и Stable Fast 3D, цены Rodin,
спецификация Rodin Gen-2.5, дайджесты W4, код аддона MCP) + файлы B/C1/E волны 1 · эксперименты:
`99-raw/experiments/G/03-cleanup-boulder` (Decimate, перепечка нормали, Remesh и QuadriFlow в фоне, ошибка в мм, веса),
`G/02-polyhaven-api` (путь до веба), `G/01-rodin-mcp` (импорт через MCP), `G/04-doc-snippets` (все блоки кода файла) · версии:
Blender 5.2.2 LTS (фон, Cycles CPU), glTF-IO 5.2.40, gltf-transform 4.5.0, gltfpack 1.2 (нативный), three r186 (Chromium,
Iris Xe).

Выход генератора 3D или скан — **один плотный треугольный меш с UV-атласом и запечёнными картами**. Живой выход Rodin в этой
сессии получить не удалось (пробный ключ исчерпан, G/01), поэтому конвейер проверен на скане Poly Haven
`namaqualand_boulder_05` (89 618 треуг., атлас, base/ORM/normal 1k) — той же структуры данных; поведение на выходе Rodin —
`[не проверено]`. Экспорт, запекание и сжатие как таковые — `../08-export-gltf/` (здесь не повторяю, только ссылки).

## Выжимка для агента

1. **Сначала входной осмотр, потом правка**: `asset_intake()` — треугольники по файлу, материалы, картинки и их пространства,
   UV, масштаб, габарит, смещение origin, открытые рёбра, число кусков; затем `render_views.py` и `gltf_load_bench.py`. → §2 `[проверено]`
2. **Первый шаг упрощения — Decimate COLLAPSE по целевому числу треугольников**: в фоне 1,7 с на 90 тыс., **UV и материал
   сохраняются**, карты генератора продолжают работать. → §3 `[проверено]`
3. **Меряй упрощение ошибкой в миллиметрах** (среднее, P95, максимум расстояния от вершин исходника до упрощённой поверхности):
   90 тыс. → 12 тыс. дало 0,99 / 2,55 / 13 мм на объекте 1,36 м (P95 = 0,19 % габарита) — на рендере не отличить. → §3.2 `[проверено]`
4. **Перепеки нормаль с исходника** (selected-to-active, `cage_extrusion` 1–2 % габарита, 1024², 4 сэмпла): +1,9 с, возвращает
   мелкий рельеф, после сжатия файл даже меньше (0,58 против 0,66 МБ). → §4.1 `[проверено]`
5. **Remesh VOXEL и QuadriFlow работают в фоне, но стирают UV** (0,3 с и 6 с) — после них полная перепечка base color, ORM и
   нормали; ошибка P95 7 и 24 мм против 2,6 мм у Decimate. Квады нужны для анимации и подразделения, не для статики сайта. → §3.3 `[проверено]`
6. **Не упрощай постобработкой то, что двигается или морфится**: `gltf-transform optimize` по умолчанию упрощает (252k → 94k),
   `gltfpack -si` ломает морфы (IoU 0,82) — для героя-статики допустимо, в остальных случаях `--simplify false` (E `03 §2.5`). → §3.4 `[проверено]`
7. **Текстуры: 1k десктоп / 512 телефон**, WebP для десктопа, KTX2 для телефона; нормали — не в JPEG низкого качества и не в ETC1S
   (E `03 §3`). → §5.1 `[проверено]`
8. **Один материал и одна текстура на ассет** — генераторы так и отдают; не плодить материалы при перекраске: каждый материал =
   вызов отрисовки. → §5.2 `[проверено: G/02 — 1 вызов]`
9. **Проверяй запечённый свет в альбедо**: тени и блики, нарисованные в base color, «спорят» со светом страницы; бери режим PBR
   генератора (SF3D отделяет освещение, Rodin и Meshy дают PBR), иначе — перегенерация или ручная правка. → §5.3 `[документация; не проверено]`
10. **Масштаб генератора условный** («normalized size» у инструмента Rodin в MCP) — задать реальные размеры из паспорта ассета,
    применить масштаб, origin у основания или в оси вращения (bpyx `apply_transforms`, `put_on_floor`, `origin_to_center`). → §6 `[исходник; проверено: bpyx]`
11. **Серия важнее «красоты» одного ассета**: перекраска base color в цвет палитры с сохранением нормали и шероховатости
    (`stylize_flat`) выравнивает ассеты разных источников. → §7 `[проверено]`
12. **Гипотеза A подтверждена на скане**: после Decimate + перепечки 12 тыс. треуг., **0,28 МБ телефон / 0,58 МБ десктоп** при
    бюджете 0,8 / 1,5 МБ героя (A `02 §3.1`); без упрощения тот же ассет — 0,68 / 1,16 МБ и 90 тыс. треуг. → §8 `[проверено]`
13. **Итог сжимай одной командой** (§5.1): десктоп `gltf-transform optimize … --compress meshopt --texture-compress webp
    --texture-size 1024 --simplify false`, телефон нативный `gltfpack -cc -tc -ts 0.5 -ke -kn`. → §5.1 `[проверено]`
14. **Перед экспортом — `preflight()`, после — валидатор и `glb_lint()`** (E `04 §5–6`): входной фильтр ловит процедурные
    ноды, лишние UV, скрытые объекты, пространства картинок. → §2.2 `[проверено]`
15. **Выход Rodin через MCP**: аддон ждёт «один меш» или «пустышка + меш», иначе ошибка импорта; скачанный GLB остаётся в
    `TMPDIR` (`NamedTemporaryFile(delete=False)`) — копируй его в рабочую папку как исходник и убирай за собой. → §9 `[исходник]`
16. **MCP всегда просит у Rodin `tier=Sketch`, `mesh_mode=Raw`** — треугольный суп низшего уровня; квад-сетка, Smart Low-Poly и
    «запечённые нормали из high-poly» у Rodin — параметры API и платные функции сайта. → §9 `[исходник; документация: цены Rodin]`
17. **Не доводить руками то, что дешевле перегенерировать**: дыры, слипшиеся части, лишние лица — признак отбраковать вариант, а
    не чинить (генераторы дают 2–4 варианта; best-of-N — C2 `03 §8`). → §2.3 `[исследование C2; практика]`
18. **Decimate портит стилизованную low-poly-геометрию и деформируемость** — проверяй силуэт рендером до и после
    `[V:H1oNuKChsdU 21:46]`; для статики авто-ремеш допустим, ручная ретопология не нужна `[V:7AR9-LxY6AQ 07:06]`. → §3 `[практика W4]`

## 1. Конвейер доводки (порядок и цена)

| Шаг | Что делать | Инструмент | Время (90 тыс. треуг., CPU 20 потоков) | Раздел |
|---|---|---|---|---|
| 0 | Сохранить исходник (GLB генератора/скана) рядом с проектом, записать лицензию | `tag_license()` (`03 §3.2`) | — | §9 |
| 1 | Входной осмотр: числа + рендеры с ракурсов | `asset_intake()`, `render_views.py` | < 1 с + 5–15 с | §2 |
| 2 | Масштаб, ориентация, origin | bpyx `apply_transforms`, `put_on_floor`, `origin_to_center` | < 0,1 с | §6 |
| 3 | Упростить до бюджета, сохранив UV | `decimate_keep_uv()` | 1,7 с | §3 |
| 4 | Проверить ошибку в мм | `approx_error_mm()` | < 1 с | §3.2 |
| 5 | Перепечь нормаль с исходника | `bake_normal_from_high()` | 1,9 с (1024², 4 spp) | §4 |
| 6 | Материал: один, PBR, без запечённого света; перекраска под серию | `stylize_flat()` при необходимости | < 0,1 с | §5, §7 |
| 7 | Экспорт пресетом и `preflight()` | E `04 §5, §7` | 0,3 с | — |
| 8 | Сжатие десктоп/телефон | gltf-transform / gltfpack (§5.1) | 1–3 с | §5.1 |
| 9 | Проверка в three: вес, вызовы, память, картинка | `gltf_load_bench.py`, `web_view.py`, `gltf_diff.py` | 10–30 с | §8 |

Весь путь на валуне — меньше 15 с машинного времени [проверено]. Правило остановки: ошибка P95 ≤ 0,5 % габарита, силуэт
на рендере совпадает, вес и треугольники в бюджете (A `02 §3.1`, E `03 §6.5`) — дальше не улучшать.

## 2. Диагностика

### 2.1. Входной осмотр кодом

```python
# Blender 5.2.2 — [проверено] входной осмотр ассета (генератор, скан, библиотека)
import bpy, bmesh
from mathutils import Vector


def asset_intake(objects=None, phone_tris=50_000, desktop_tris=100_000, max_tex=2048):
    """Числа до правки: треуг. по вычисленной геометрии, куски, открытые рёбра, UV, материалы, картинки, масштаб, origin."""
    objs = [o for o in (objects or bpy.context.scene.objects) if o.type == "MESH"]
    dg = bpy.context.evaluated_depsgraph_get()
    rep = {"meshes": len(objs), "tris": 0, "objects": [], "images": [], "warnings": []}
    mats = set()
    for ob in objs:
        me = ob.evaluated_get(dg).to_mesh()
        bm = bmesh.new(); bm.from_mesh(me)
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        open_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2)
        bm.verts.index_update()
        seen, parts = set(), 0                               # связные куски (парящие обломки генераторов)
        for v in bm.verts:
            if v.index in seen:
                continue
            parts += 1; stack = [v]; seen.add(v.index)
            while stack:
                cur = stack.pop()
                for e in cur.link_edges:
                    w = e.other_vert(cur)
                    if w.index not in seen:
                        seen.add(w.index); stack.append(w)
        bm.free(); ob.evaluated_get(dg).to_mesh_clear()
        center = sum((Vector(c) for c in ob.bound_box), Vector()) / 8
        rep["tris"] += tris
        rep["objects"].append({"name": ob.name, "tris": tris, "parts": parts, "open_edges": open_edges,
                               "uv": [u.name for u in ob.data.uv_layers], "scale": [round(s, 4) for s in ob.scale],
                               "dims_m": [round(d, 4) for d in ob.dimensions],
                               "origin_offset_m": round((ob.matrix_world @ center - ob.matrix_world.translation).length, 4),
                               "materials": [s.material.name for s in ob.material_slots if s.material]})
        mats.update(s.material for s in ob.material_slots if s.material)
        if any(abs(s - 1) > 1e-4 for s in ob.scale):
            rep["warnings"].append(f"{ob.name}: масштаб не применён {tuple(round(s, 3) for s in ob.scale)}")
        if not ob.data.uv_layers:
            rep["warnings"].append(f"{ob.name}: нет UV — текстуры не лягут, перепечка невозможна")
        if parts > 1:
            rep["warnings"].append(f"{ob.name}: {parts} несвязных кусков — проверить парящие обломки")
    for m in mats:
        for n in (m.node_tree.nodes if m.node_tree else []):
            if n.type == "TEX_IMAGE" and n.image:
                w, h = n.image.size
                rep["images"].append({"image": n.image.name, "size": [w, h], "colorspace": n.image.colorspace_settings.name})
                if max(w, h) > max_tex:
                    rep["warnings"].append(f"{n.image.name}: {w}×{h} > {max_tex}")
    rep["materials"] = len(mats)
    rep["budget"] = "phone" if rep["tris"] <= phone_tris else "desktop" if rep["tris"] <= desktop_tris else "over"
    return rep
```

Что смотреть в ответе: `tris` против бюджета (50/100 тыс. героя, A `02 §3.1`); `parts` > 1 у генератора — обломки и «плавающие»
куски (главный дефект формы у кода — C2, у генераторов — отдельные слипшиеся части); `open_edges` > 0 — дыры или открытые
края (у сканов — нормально на основании); картинки > 2048 и пространства (альбедо sRGB, данные Non-Color — C1 M4.3); масштаб
≠ 1 (Sketchfab/Poly Pizza через MCP — C1 M2.10). На валуне Poly Haven: 1 меш, 89 618 треуг., атлас `UVMap`, масштаб 1, габарит =
паспорт API, 3 карты 1k [проверено].

### 2.2. Инструменты базы

- `render_views.py` (4–6 ракурсов, `--clay` для формы, `stats.json`) и `gltf_check.py` (валидатор + inspect) — `../../scripts/3d/README.md`.
- `gltf_load_bench.py` — вес, загрузка, первый кадр, память GPU; `gltf_web_inspect.py` — что создал three; `gltf_diff.py` — Blender
  против three (ΔE ≤ 3,5, IoU ≥ 0,99) — E `04 §1`.
- `preflight()` до экспорта и `glb_lint()` после — E `04 §5–6` (код там; здесь не дублирую).

### 2.3. Когда не доводить, а перегенерировать или взять другое

| Признак на рендере/в числах | Действие |
|---|---|
| лишние части тела, слипшиеся детали, нечитаемый силуэт | перегенерировать (2–4 кандидата, отбор попарно — C2 `03 §7–8`) |
| дыры в видимых местах, сквозные «пузыри» | перегенерировать; мелкие дыры на невидимом основании — оставить |
| тени и блики, нарисованные в альбедо (§5.3) | режим PBR генератора или перегенерация |
| стиль не совпадает с серией (фотореализм среди стилизованных) | стилизация §7 или код по паспорту (C1 `04 §4`) |
| товарные знаки, логотипы в текстуре | не использовать |

## 3. Упрощение геометрии

### 3.1. Сравнение способов (G/03, валун 89 618 треуг., 1,36 м)

| Способ | Результат | Время | UV | Ошибка, мм (сред. / P95 / макс.) | Что потом |
|---|---|---|---|---|---|
| **Decimate COLLAPSE**, ratio 0,134 | 11 999 треуг. | 1,74 с | **сохранён** | **0,99 / 2,55 / 13,2** | карты работают; перепечь нормаль (§4) |
| Remesh VOXEL 0,02 м (модификатор) | 16 112 треуг. | 0,31 с | стёрт | 2,63 / 7,11 / 74,8 | новая UV + перепечка всех карт |
| QuadriFlow `target_faces=6000` (оператор в фоне) | 4 868 квадов | 6,04 с | стёрт | 5,70 / 24,4 / 75,4 | то же; квады — для подразделения/анимации |
| `gltf-transform optimize` (simplify по умолчанию) | до ~37 % треуг. на гладком high-poly (E/17) | < 3 с | сохраняется | ΔE 0,26 (E) | для статики героя; не для морфов |
| `gltfpack -si 0.5` | 50 % | < 2 с | сохраняется | IoU 0,82 на морфах (E) | только статика |

[проверено]. Оба ремеша закрыли тонкие выступы (максимум 75 мм) — для «как на фото» ассета это видимо, для
стилизации под low-poly может быть желательно.

### 3.2. Код: децимация с сохранением UV и ошибка в миллиметрах

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/G/04-doc-snippets; числа — G/03] Decimate COLLAPSE до бюджета + ошибка в мм
import bpy
from mathutils.bvhtree import BVHTree


def tri_count(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh(); n = sum(len(p.vertices) - 2 for p in me.polygons)
    ob.evaluated_get(dg).to_mesh_clear()
    return n


def decimate_keep_uv(ob, target_tris):
    """Упростить меш до ≈target_tris; UV-швы, материалы и группы вершин сохраняются. Применяет модификатор данными."""
    n = tri_count(ob)
    if n <= target_tris:
        return n
    mod = ob.modifiers.new("DecimateWeb", "DECIMATE")
    mod.decimate_type = "COLLAPSE"; mod.ratio = target_tris / n; mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    ob.modifiers.remove(mod)
    old, ob.data = ob.data, new_me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return tri_count(ob)


def approx_error_mm(high, low):
    """Расстояние от вершин high до поверхности low (мм): среднее, P95, максимум; P95 в % от наибольшего габарита high."""
    dg = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(low, dg)
    inv = low.matrix_world.inverted()
    d = sorted(tree.find_nearest(inv @ (high.matrix_world @ v.co))[3] * 1000.0 for v in high.data.vertices)
    p95 = d[int(0.95 * (len(d) - 1))]
    return {"mean": round(sum(d) / len(d), 2), "p95": round(p95, 2), "max": round(d[-1], 2),
            "p95_pct": round(p95 / (10.0 * max(high.dimensions)), 3)}
```

Порог-ориентир (предложение G, по G/03): P95 ≤ 0,5 % габарита для героя «как на фото»; 0,19 % на рендере 384 px неотличимо от
исходника. Расстояние меряется в одну сторону (исходник → упрощённый меш) и в метрах сцены — ассет до этого приведён к реальному
масштабу (§6). Метрика — по W4 `[V:7AR9-LxY6AQ 12:45]`.

### 3.3. Когда нужен ремеш, а не децимация

- Нужны квады: подразделение на странице, скиннинг/морфы с чистыми деформациями, дальнейшая ручная доработка — QuadriFlow
  (`bpy.ops.object.quadriflow_remesh`, работает в фоне без `temp_override`, активный выделенный объект) или квад-режим генератора
  (Rodin `mesh_mode=Quad` 1 000–200 000 граней, Meshy `topology=quad`, SF3D `--remesh_option Quad`) `[проверено: G/03;
  поиск/документация — 01 §2]`.
- Меш «рваный» (самопересечения, дыры, много кусков) и нужна замкнутая оболочка: Remesh VOXEL (размер вокселя ≈ 1–2 % габарита).
- После обоих: `uv_unwrap(ob, "SMART")` (bpyx) и перепечка base color (DIFFUSE `pass_filter={"COLOR"}`), ORM и нормали
  selected-to-active с исходника — функции E `02 §3–8`.

### 3.4. Упрощение постобработкой

`gltf-transform optimize` упрощает по умолчанию с ошибкой 0,0001 габарита (252k → 94k, ΔE 0,26), `gltfpack -si R` — до доли R;
оба не видят морфов и мелких деталей силуэта (E `03 §2.5`) [проверено]. Для героя-статики «как на фото» это быстрый
путь без Blender; для частей с анимацией, морфов и адресуемых объектов — только Decimate в Blender с проверкой ошибки.

## 4. Перепечка карт

### 4.1. Нормаль с исходника на упрощённый меш

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/G/04-doc-snippets; числа — G/03] нормали high → low (UV low сохранён или новый)
import bpy


def bake_normal_from_high(high, low, size=1024, extrusion_pct=1.5, samples=4):
    """Касательная карта нормалей: high и low выделены, low активный; результат подключается к Principled low."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples
    img = bpy.data.images.new(f"{low.name}_nor_{size}", size, size, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    for slot in low.material_slots:                          # материал, общий с high, не портить — копия для low
        if slot.material and slot.material.users > 1:
            slot.material = slot.material.copy()
    targets = []
    for slot in low.material_slots:                          # цель bake — активная Image Texture в КАЖДОМ материале (E 02 §3.1)
        nt = slot.material.node_tree
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
        for n in nt.nodes:
            n.select = False
        t.select = True; nt.nodes.active = t; targets.append((nt, t))
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    high.select_set(True); low.select_set(True); bpy.context.view_layer.objects.active = low
    ext = extrusion_pct / 100.0 * max(high.dimensions)
    res = bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", use_selected_to_active=True,
                              cage_extrusion=ext, max_ray_distance=0.0, margin=16, use_clear=True)
    if res != {"FINISHED"}:
        raise RuntimeError(f"bake NORMAL: {res}")
    for nt, t in targets:
        nt.nodes.remove(t)
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        nmap = bsdf.inputs["Normal"].links[0].from_node if bsdf.inputs["Normal"].is_linked else None
        if nmap is None or nmap.type != "NORMAL_MAP":
            nmap = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        src = nmap.inputs["Color"].links[0].from_node if nmap.inputs["Color"].is_linked else None
        if src is None or src.type != "TEX_IMAGE":
            src = nt.nodes.new("ShaderNodeTexImage"); nt.links.new(src.outputs["Color"], nmap.inputs["Color"])
        src.image = img                                       # старая нормаль high заменена запечённой
    return img
```

- `cage_extrusion` 1–2 % наибольшего габарита (валун 1,36 м → 0,0205 м); 0 даёт пятна хуже, чем без карты (E/27)
  [проверено]. 1024², 4 сэмпла — 1,86 с на 90 тыс. → 12 тыс. треуг. [проверено].
- Запечённая нормаль сохраняется PNG 8 бит (сырой GLB 3,6 МБ вместо 3,0 МБ), но после WebP/KTX2 итог меньше исходного
  варианта: 0,58 против 0,66 МБ — нормаль с упрощённого меша глаже [проверено].
- Base color и ORM при Decimate не перепекаются — UV тот же; после ремеша — перепекать все карты (E `02 §4, §8`).

### 4.2. Что видно глазами

Лист `99-raw/experiments/G/03-cleanup-boulder/out/compare_high_low.png` (EEVEE, два ракурса): Decimate без перепечки мягче
исходника по мелкому рельефу (старая нормаль лежит в чужом касательном пространстве, выступы геометрии ушли); с перепечённой
нормалью — почти неотличим; силуэт сохранён в обоих вариантах [проверено].

## 5. Текстуры и материалы

### 5.1. Сжатие итогового GLB

```bash
# gltf-transform 4.5.0, gltfpack 1.2 (нативный, с BasisU) — [проверено: 99-raw/experiments/G/04-doc-snippets; числа — G/02, G/03]
BASE=$DDD_HOME
export PATH="$BASE/bin/KTX-Software-4.4.2-Linux-x86_64/bin:$BASE/bin/gltfpack-1.2:$PATH"
IN=/abs/path/asset_low.glb
OUT=/abs/path/asset
cd "$BASE/node"
npx --no-install gltf-transform optimize "$IN" "${OUT}_desktop.glb" --compress meshopt --texture-compress webp --texture-size 1024 --simplify false
gltfpack -i "$IN" -o "${OUT}_phone.glb" -cc -tc -ts 0.5 -ke -kn
```

`-ke -kn` сохраняют extras (лицензия, `03 §3.2`) и имена узлов; вход gltfpack — JPEG/PNG, не WebP (E `03 §4.3`). Результаты:
валун 90 тыс. — 1,16 / 0,68 МБ; упрощённый 12 тыс. — 0,58 / 0,28 МБ; плита с текстурой — 0,29 / 0,15 МБ [проверено].
KTX2 из JPEG-источников даёт артефакты сильнее (E `03 §3.4`); у генераторов карты обычно PNG/JPG — если есть PNG, брать его.

### 5.2. Материал

- Генераторы отдают один Principled с base color (+ metallic/roughness/normal в PBR-режимах) и одним UV — это 1 вызов отрисовки;
  не разбивать на части без нужды (C1 M4.10). Скан Poly Haven: base + ORM (`arm`) + normal, `doubleSided` [проверено].
- Двусторонность: генераторы и glTF Poly Haven часто `doubleSided: true` — для замкнутых мешей выключить (`use_backface_culling`),
  если нет открытых краёв (`asset_intake.open_edges = 0`) — дешевле, и правильнее для transmission/теней (E `04 §4.3`).
- Процедурные ноды и Displacement в glTF не попадают — запекать (E `02`, C1 M4.1, M4.4).

### 5.3. Запечённый свет в альбедо (делайтинг)

- Признак: в base color видны тени от «солнца», блики, затемнения в щелях сильнее AO; на странице с другим светом объект
  выглядит «наклеенным». Генераторы 2025–2026 это решают по-разному: SF3D — «illumination disentanglement» в модели (README),
  TRELLIS.2 — PBR-атрибуты base color/roughness/metallic/opacity, Rodin Gen-2.5 и Meshy — PBR-материалы в API `[документация: README; §01]`.
- Правило: заказывать у генератора PBR-материал (не «shaded»), проверять альбедо на плоском свете (рендер `render_views.py` с
  равномерной студией) и сравнивать с «глиной» (`--clay`); сильный запечённый свет — отбраковка варианта `[практика; не проверено
  на выходе генератора]`.
- Для скан-ассетов Poly Haven делайтинг сделан авторами (альбедо ровное, AO — отдельной картой в `arm`) [проверено глазами].

## 6. Масштаб, ориентация, origin

- Генераторы возвращают модель в условном масштабе: инструмент Rodin в MCP прямо пишет «The generated model has a normalized
  size, so re-scaling after generation can be useful», промт `asset_creation_strategy` требует смотреть `world_bounding_box` после
  импорта [исходник сервера 2.0.3]. Правило: реальный размер — из паспорта ассета (C1 `04 §3.2`), масштаб применить данными
  (bpyx `apply_transforms`), нижнюю точку на пол (`put_on_floor`), origin — в центр габарита (`origin_to_center`) или в ось вращения
  для анимируемых частей (C1 M2.9, M2.10).
- Poly Haven: масштаб уже реальный и применён, origin у основания [проверено]. Sketchfab/Poly Pizza через MCP: масштаб
  корней не применён (C1 `01 §3.10–3.11`).
- Ориентация: glTF — Y-вверх, импорт Blender переводит в Z-вверх сам; «перед» у генераторов не гарантирован — смотреть вид
  спереди `render_views.py` (азимут 0) и поворачивать до экспорта.

## 7. Стилизация под серию

Ассеты разных генераторов и библиотек выглядят «из разных миров» (C1 M3.9). Самый дешёвый выравниватель — общий паспорт
света/камеры (D2, C1 `04 §3.1`) и перекраска base color в цвет палитры с сохранением рельефа:

```python
# Blender 5.2.2 — [проверено] перекраска под палитру серии, рельеф и шероховатость остаются
import bpy


def srgb_hex_to_linear(hex_color):
    h = hex_color.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def stylize_flat(objects, hex_color, roughness=None):
    """Отцепить текстуру от Base Color и задать цвет палитры (hex как в CSS). Материал копируется — чужие не страдают."""
    done = []
    for ob in objects:
        for slot in ob.material_slots:
            if not slot.material:
                continue
            m = slot.material.copy(); slot.material = m
            bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            for link in list(bsdf.inputs["Base Color"].links):
                m.node_tree.links.remove(link)
            bsdf.inputs["Base Color"].default_value = srgb_hex_to_linear(hex_color)
            if roughness is not None:
                for link in list(bsdf.inputs["Roughness"].links):
                    m.node_tree.links.remove(link)
                bsdf.inputs["Roughness"].default_value = roughness
            done.append(m.name)
    return done
```

После перекраски неиспользуемая картинка base color в экспорт не попадёт (экспортёр берёт только подключённые), вес падает;
нормаль остаётся — форма читается. Полная стилизация (low-poly, toon) — задача D1/D2; на выходах генераторов — `[не проверено]`.

## 8. Итоговый вес против бюджетов

| Ассет | Треуг. | Десктоп (meshopt + WebP 1k) | Телефон (KTX2 512) | Текстуры GPU десктоп / телефон | Бюджет героя (A `02 §3.1`) |
|---|---|---|---|---|---|
| скан как есть (Poly Haven glTF 1k) | 89 618 | 1,16 МБ | 0,68 МБ | 16,4 / 1,0 МБ | вес — да; треуг. телефона — **нет** |
| скан после Decimate + нормали | 11 999 | **0,58 МБ** | **0,28 МБ** | 16,4 / 1,0 МБ | **да** |
| кресло Poly Haven (MCP, 8 916) | 8 916 | 0,31 МБ | 0,30 МБ | — | да |
| выход Rodin/Meshy/Tripo | по документации 18 тыс.–1 млн (`01 §2`) | — | — | — | `[не проверено]` |

[проверено: G/01–G/03]. Гипотеза агента A «сгенерированная модель после ретопологии и запекания укладывается в 0,8 МБ для
телефона» — подтверждена на ассете той же структуры (скан, атлас, 3 карты): 0,28 МБ; на живом выходе генератора — не проверена.

## 9. Особенности выхода генераторов при импорте через MCP

- `import_generated_asset` (Rodin, режим MAIN_SITE): `POST …/api/v2/download` → первый `*.glb` из списка → файл в
  `tempfile.NamedTemporaryFile(prefix=<task_uuid>, suffix=".glb", delete=False)` → `import_scene.gltf` → ожидается ровно «один меш»
  или «пустышка + один меш» (пустышка удаляется, меш переименовывается), иначе «Expected an empty node with one mesh child or a
  single mesh object» [исходник аддона протокола 9]. Файл во временной папке не удаляется — копировать как исходник в проект.
- Параметры, которые шлёт MCP: `tier=Sketch`, `mesh_mode=Raw`, `texture_mode=high`, `prompt`, `bbox_condition` (пропорции,
  нормированные к 100) — изменить без правки аддона нельзя [исходник]. Квад-сетка, уровни Gen-2.5, форматы, кроме GLB, — только
  прямой API (платный план Business, `01 §2–3`).
- Запросы к Rodin идут без таймаутов в главном потоке Blender — при обрыве сети интерфейс висит (C1 `01 §3.12`).

## Частые ошибки

1. **Ремеш «для чистой топологии» статичного ассета** — стирает UV и добавляет перепечку всего; для статики Decimate [проверено].
2. **Децимация без перепечки нормали** — объект «оплывает» по мелкому рельефу [проверено].
3. **`cage_extrusion = 0`** — пятна хуже, чем без карты (E/27) [проверено: E].
4. **Цель bake только в одном из материалов** — остальные грани не запекутся, bake вернёт FINISHED (E `02 §3.1`) [проверено: E].
5. **Общий материал high и low** при перепечке — нормаль high перезаписывается запечённой (функция §4.1 копирует) [проверено].
6. **Оценка «на глаз» вместо ошибки в мм** — упрощение до разваливающегося силуэта незаметно на миниатюре [проверено].
7. **Бюджет по `polycount` карточки или по `get_object_info`** — первое расходится с файлом на 24 % (G/02), второе не учитывает
   модификаторы (C1) [проверено].
8. **gltfpack без `-ke`** — пропадают метки лицензии (`03 §3.2`, E/28) [проверено: E].
9. **Упрощение постобработкой морфируемого или анимируемого ассета** — IoU 0,82 (E/17) [проверено: E].
10. **Масштаб «как пришёл»**: генератор — нормированный размер, Poly Pizza — произвольный (C1 M2.1) [исходник].
11. **Модель по памяти**: `bpy.ops.object.decimate` (нет такого оператора — модификатор DECIMATE), `mesh.use_auto_smooth` (удалён
    в 4.1), `scene.render.bake_type` (нет в 5.x; `bpy.ops.object.bake(type=…)`) — B `03`, E `02 §Частые ошибки`.

## Чек-лист

- [ ] Исходник сохранён рядом с проектом, лицензия записана в метаданные?
- [ ] `asset_intake()`: масштаб 1, реальные размеры, один материал, UV есть, лишних кусков нет?
- [ ] Треугольники ≤ бюджета после `decimate_keep_uv()`, ошибка P95 ≤ 0,5 % габарита?
- [ ] Нормаль перепечена с исходника (`cage_extrusion` 1–2 %), материал high не задет?
- [ ] В альбедо нет запечённых теней и бликов (рендер при ровном свете против `--clay`)?
- [ ] origin и ориентация «вперёд» заданы, масштаб применён?
- [ ] `preflight()` без ERROR, экспорт пресетом, сжатие десктоп/телефон, extras на месте?
- [ ] Вес и память GPU в бюджете по `gltf_load_bench.py`, вид в three совпадает с Blender (`gltf_diff.py`)?

## Открытые вопросы и противоречия

- **Выход живого генератора не доведён**: пробный ключ Rodin исчерпан (G/01); конвейер проверен на скане той же структуры.
  Проверить на 2–3 выходах Rodin/Meshy при ключе заказчика: топология Raw (сотни тысяч треуг.), запечённый свет, число кусков.
- **Порог ошибки P95 ≤ 0,5 % габарита** — предложение по одному объекту; откалибровать на серии (агент J).
- **Делайтинг** — только по документации генераторов; готового инструмента «снять свет с альбедо» в Blender нет, проверено не было.
- **Remesh/QuadriFlow + полная перепечка** по времени и качеству против Decimate не сравнивались (режим экономии).

## Источники

- [S1] Эксперимент G/03: Decimate, перепечка нормали, Remesh VOXEL, QuadriFlow, ошибка в мм, веса — `99-raw/experiments/G/03-cleanup-boulder/README.md`. [проверено]
- [S2] Эксперимент G/02: Poly Haven glTF → сжатие → three r186 — `99-raw/experiments/G/02-polyhaven-api/README.md`. [проверено]
- [S3] Эксперимент G/01: импорт Poly Haven через MCP, экспорт 11,4 МБ; попытки Rodin — `99-raw/experiments/G/01-rodin-mcp/README.md`. [проверено]
- [S4] mcp-for-blender 2.0.3: `server.py` (описание `generate_hyper3d_model_via_text`: «normalized size»), `bundled/addon.py`
  (`create_rodin_job_main_site`, `import_generated_asset_main_site`, `_clean_imported_glb`). Первоисточник.
- [S5] Microsoft. TRELLIS.2 README (GitHub, MIT, 11 332★, push 2026-07-10) — PBR-атрибуты, `to_glb(decimation_target=1000000, texture_size=4096)`. Первоисточник.
- [S6] Stability AI. Stable Fast 3D README (GitHub, 1 826★, push 2025-01-22) — «UV-unwrapping and Illumination Disentanglement», `--remesh_option None|Triangle|Quad`, ≈ 6 ГБ VRAM. Первоисточник.
- [S7] Hyper3D. Rodin Gen-2.5 API (docs.hyper3d.ai, через WebFetch) и Pricing (hyper3d.ai/pricing, 23.09.2026) — уровни, текстуры 2K–12K, «Запечённые нормали из high-poly» и Smart Low-Poly в платных тарифах. Первоисточник.
- [S8] Агент E: `../08-export-gltf/02-baking.md` (цель bake, `cage_extrusion`, типы проходов), `03-compression-textures-budgets.md` (упрощение, форматы), `04-validation-pitfalls-presets.md` (`preflight`, `glb_lint`, пресеты). [проверено E]
- [S9] Агент B: `../../../scripts/3d/bpyx.py` — `apply_transforms`, `put_on_floor`, `origin_to_center`, `uv_unwrap`, `object_stats`. [проверено B]
- [S10] Агенты C1, C2: `../04-ai-agents-mcp/01 §3.12`, `04 §3–4`, `05` (коды M), `03 §7–8` (best-of-N, попарный судья). [проверено/исследование]
- [S11] Дайджесты W4: `[V:7AR9-LxY6AQ 07:06, 12:45]` (авто-ремеш для статики, ошибка в мм), `[V:H1oNuKChsdU 21:46]` (Decimate и стиль) — по отчёту `99-raw/reports/wave2-W4-report.md` §8.
