# snippets — bpyx: проверенные помощники Python API для Blender 5.2

Волна 1 · агент B · 2026-09-23 · Blender 5.2.2 LTS (Python 3.13.13) · bpyx 1.0.0 · тесты 25/25 в `blender -b` и в
модуле `bpy` 5.2.2 из PyPI [проверено].

| Файл | Что это |
|---|---|
| `bpyx.py` | 47 функций (1098 строк): сцена и коллекции, геометрия без операторов, модификаторы, трансформации, габариты, цвет и материалы, ноды и связи с проверкой, камера и свет, движок и цвет, рендер, экспорт GLB, UV в фоне, geometry nodes (API 5.2) |
| `test_bpyx.py` | 25 тестов; запуск ниже; код выхода 0 = всё зелёное |
| `agent_scene.py` (агент I, перенесено U волна 4) | 13 функций: работа агента в сцене человека — тег вместо имени (`AGENT`/`ASSET`/`PART`), своя коллекция, `begin()`/`finish()` (идемпотентная пересборка, чужое не трогает, эвакуирует чужое из своей коллекции вместо удаления), своя сцена превью, ручные правки человека поверх сборки (`overrides`) |
| `hygiene.py` (агент I, перенесено U волна 4) | `hygiene_report()` — дубли имён/материалов/картинок, сироты, спрятанное в экспорте, далёкие объекты, повторные модификаторы, лишние UV и слоты материалов, упакованные байты; `hygiene_clean()` — чистка того же **только в своём фоновом файле** (в сцене человека — не применять, только отчёт) |
| `test_agent_helpers.py` (U) | 4 теста для `agent_scene.py`/`hygiene.py`; запуск ниже; код выхода 0 = всё зелёное |
| `README.md` | этот файл |

Библиотека опирается на правила файлов `../01-data-model-and-basics.md`, `../02-nodes-from-python.md`,
`../03-version-drift-3.6-to-5.2.md`, `../04-llm-failure-modes-and-patterns.md`; каждая «странность» в коде — это
проверенная ловушка 5.2 (ссылка в docstring).

## Подключение

**Фоновый скрипт** (`blender -b`, `../../scripts/3d/blender_run.py`, модуль `bpy` из PyPI):

```python
# Blender 5.2.2 — [проверено]
import sys
SNIPPETS = "../../scripts/3d"   # от корня базы kb/3d
if SNIPPETS not in sys.path:
    sys.path.insert(0, SNIPPETS)
import bpyx
```

**MCP (`execute_blender_code`)**. Аддон выполняет код через `exec(code, {"bpy": bpy})`: пространство имён свежее на
каждый вызов (переменные не живут, `__file__` нет, `__name__ == 'builtins'`), а модули в `sys.modules` живут
[проверено]. Поэтому:

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/B/40-bpyx-tests, тест t25]
# первый вызов в сеансе (и после каждой правки bpyx.py):
import sys, importlib
sys.dont_write_bytecode = True        # иначе reload может взять устаревший .pyc (правка в ту же секунду, тот же размер)
p = "../../scripts/3d"           # от корня базы kb/3d; в MCP — полный путь к этой папке
if p not in sys.path:
    sys.path.insert(0, p)
import bpyx
importlib.reload(bpyx)
print(bpyx.__version__)
```

```python
# каждый следующий вызов: модуль уже в sys.modules, импорт мгновенный
import bpyx
bpyx.scene_report()
```

Вариант без `sys.path` — вставить исходник в вызов: `exec(compile(open(p).read(), p, "exec"), globals())` (функции
живут только в этом вызове; traceback покажет строку файла). [проверено: 40-bpyx-tests, t25]

**GUI-сеанс пользователя через MCP**: bpyx не трогает настройки и интерфейс; `clear_scene()` удаляет только объекты и
коллекции текущей сцены (без `read_factory_settings`). Имена нод пользователя могут быть переведены (русский
интерфейс: «Принципиальный BSDF») — bpyx ищет ноды по `type`/`bl_idname`. [проверено]

## Функции

| Группа | Функция | Что делает (5.2.2) |
|---|---|---|
| Интроспекция | `version_at_least(5, 2)` | версия Blender не ниже |
| | `rna_has(obj_or_type, name)` | есть ли RNA-свойство/функция (`hasattr` на классе всегда False) |
| | `enum_values(owner, prop)` | фактические значения перечисления, включая динамические (движки, view transform, цветовые пространства) |
| | `set_enum(owner, prop, value)` | присвоение с понятной ошибкой: список допустимых + похожие |
| | `did_you_mean(name, pool)` | подсказки похожих имён |
| | `ensure_object_mode()` | выйти в Object Mode (данные EDIT синхронизируются) |
| | `view3d_override()` | `dict` для `context.temp_override(**d)` с областью VIEW_3D — работает и в фоне |
| Сцена | `clear_scene(purge=True)` | удалить объекты и вложенные коллекции сцены + сироты, без операторов |
| | `ensure_collection(name, parent=None)` | коллекция, привязанная к сцене/родителю |
| | `link(ob, collection=None)` | привязать объект (без этого его нет в сцене, рендере, экспорте, .blend) |
| Геометрия | `mesh_object(name, verts, faces, edges=(), smooth=False)` | from_pydata + validate + update + link |
| | `primitive(kind, name, size=, radius=, …)` | cube, uvsphere, icosphere, cylinder, cone, plane/grid, circle, torus, monkey через bmesh.ops с UV |
| | `convert_to_mesh(ob)` | текст/кривая/меш с модификаторами → меш без оператора |
| Модификаторы | `add_modifier(ob, TYPE, **props)` | с проверкой имён свойств по RNA и подсказкой |
| | `apply_modifiers(ob, count=None)` | применить все/первые N без оператора (shape keys теряются — предупреждение) |
| | `apply_transforms(ob, rotation=True, scale=True)` | «Apply» через данные, дети остаются на месте |
| | `smooth_by_angle(ob, 30, method="DATA"/"MODIFIER")` | замена `use_auto_smooth` |
| Габариты | `world_bbox(objects)` | мировые min/max по вычисленной геометрии (корректно для текста и кривых) |
| | `put_on_floor(objects, z=0)`, `center_objects(objects, "XY")`, `origin_to_center(ob)` | расстановка без операторов |
| | `object_stats(ob)`, `scene_report()` | статистика для проверки в конце скрипта (строка `SCENE_REPORT {…}`) |
| Цвет и материалы | `color("#RRGGBB")`, `srgb_to_linear(c)` | hex/CSS (sRGB) → линейный RGBA для сокетов |
| | `principled(name, base_color=, roughness=, …)` | материал Principled BSDF v2; старые имена 3.x переводятся с предупреждением |
| | `assign_material(ob, mat, replace=True / slot=i)` | назначение в данные меша |
| Ноды | `find_node(tree, "BSDF_PRINCIPLED")` | поиск по type/bl_idname, не по имени |
| | `node(tree, "ShaderNodeMix", data_type="RGBA", inputs={…})` | нода с проверкой свойств, режим до сокетов |
| | `sock(node, key, out=False)` | сокет по identifier/имени среди доступных, ошибка с подсказкой |
| | `set_input(node, key, value)`, `link_sockets(tree, (a, "Out"), (b, "In"))` | значение входа, связь с проверкой `is_valid` |
| | `layout_tree(tree)`, `assert_valid_links(tree)` | раскладка для человека, проверка связей |
| Камера и свет | `look_at(ob, target)`, `add_camera(…)`, `frame_camera(cam, objects, margin, extra_points=())` | камера без операторов (`camera_fit_coords`; ORTHO — проекция вершин на оси камеры, исправлено FX 26.09 по T22) |
| | `add_light(kind, …, energy=, size=)`, `three_point_lights(objects)` | свет по габаритам (калибровка render_views.py) |
| Рендер | `set_engine("EEVEE")`, `set_color_management("AgX", look=)` | движок с псевдонимами (EEVEE_NEXT → EEVEE), view transform по фактическому списку |
| | `render_still(path, resolution=, engine=, samples=, transparent=, file_format=)` | кадр в файл, проверка камеры и результата |
| Экспорт | `export_glb(path, objects=None, **params)` | GLB, параметры проверяются по RNA, выделение восстанавливается |
| UV | `uv_unwrap(ob, "SMART"/"ANGLE_BASED"/"LIGHTMAP"/"CUBE")` | развёртка в фоне с входом/выходом из EDIT |
| Geometry nodes | `gn_tree(name, inputs=[…])` | дерево с интерфейсом → (tree, group_input, group_output) |
| | `gn_modifier(ob, tree, **values)`, `gn_set_input(mod, "Count", 25)`, `gn_inputs(mod)` | входы по имени сокета через `mod.properties` (5.2) с `update_tag()` |

## Пример: собрать сцену по параметрам, отрендерить и экспортировать

```python
# Blender 5.2.2 — [проверено] (3,1 с; GLB валиден: 0 ошибок Khronos)
import os, sys
sys.path.insert(0, "../../scripts/3d")
import bpyx

OUT = os.path.abspath("out")
P = dict(accent="#FF6A3D", base="#1E2A44", bevel=0.03, n_spheres=5)

bpyx.clear_scene()                                        # идемпотентность: пересобрать с нуля
coll = bpyx.ensure_collection("Hero")
body = bpyx.primitive("cube", "Body", size=1.2, location=(0, 0, 0.6), collection=coll)
bpyx.add_modifier(body, "BEVEL", width=P["bevel"], segments=4, limit_method="ANGLE", harden_normals=True)
bpyx.smooth_by_angle(body, 30)
mat_body, _ = bpyx.principled("Body", base_color=P["base"], roughness=0.35, coat_weight=0.3)
bpyx.assign_material(body, mat_body)
mat_acc, _ = bpyx.principled("Accent", base_color=P["accent"], roughness=0.25,
                             emission_color=P["accent"], emission_strength=0.6)
for i in range(P["n_spheres"]):
    s = bpyx.primitive("uvsphere", f"Dot{i}", radius=0.12, location=(-0.5 + i * 0.25, -0.62, 0.9), collection=coll)
    bpyx.assign_material(s, mat_acc)
floor = bpyx.primitive("plane", "Floor", size=8)
bpyx.assign_material(floor, bpyx.principled("Floor", base_color="#D4D4D8", roughness=0.8)[0])
cam = bpyx.add_camera(location=(3.2, -4.5, 2.6), target=(0, 0, 0.6), lens=60)
bpyx.frame_camera(cam, list(coll.objects), margin=1.25)
bpyx.three_point_lights(list(coll.objects))
bpyx.set_color_management("AgX", look="AgX - Medium High Contrast")
bpyx.render_still(os.path.join(OUT, "hero.png"), resolution=(640, 480), engine="EEVEE", samples=32)
bpyx.export_glb(os.path.join(OUT, "hero.glb"), list(coll.objects))
bpyx.scene_report()        # SCENE_REPORT {"objects": 11, "tris": 5102, "materials": ["Accent", "Body", "Floor"], …}
```

## Тесты

```bash
python3 ../../scripts/3d/blender_run.py ../../scripts/3d/test_bpyx.py -- 99-raw/experiments/B/40-bpyx-tests
# тот же набор в модуле bpy из PyPI: среда venv-bpy удалена 23.09.2026 — пересоздать по ../../scripts/3d/README.md и запустить её python с test_bpyx.py
```

Вывод 2026-09-23: `RESULT 25/25 passed in 1.32 s (Blender 5.2.2 LTS, bpyx 1.0.0)`; в PyPI-bpy — 25/25 за 1,58 с.
Полный список проверок каждого теста — `99-raw/experiments/B/40-bpyx-tests/README.md`.

## Помощники агента: своя сцена и гигиена (агент I, перенесено агентом U, волна 4)

Перенесены по рекомендации `99-raw/reports/wave4-X-audit.md` §12 (приоритет 1) рядом с `bpyx` без изменения кода —
у обоих файлов не было внутренних `sys.path`/относительных импортов, только `bpy`/`mathutils`/`json`/`re`, поэтому
перенос не потребовал правки импортов. Подключение — как у `bpyx` (`sys.path.insert(0, SNIPPETS)`, затем `import
agent_scene, hygiene`). Оригиналы с экспериментами, доказавшими код, — `99-raw/experiments/I/01-own-collection-vs-wipe/`
и `I/02-file-hygiene/`; не трогать (владеет I).

- **`agent_scene.py`** реализует правило №1 README для агентов «не стирай сцену»: `begin(scene, agent, asset)` —
  находит/создаёт свою коллекцию по тегу (custom properties `agent`/`asset`/`part`, не по имени — имя может стать
  `.001`), эвакуирует чужие объекты, оказавшиеся в ней, в корень сцены (не удаляет), снимает ручные правки человека
  (`matrix_world`, Base Color) со времени прошлой сборки; `finish(coll, overrides, agent, asset)` — накатывает эти
  правки обратно и запоминает контрольное состояние. Идемпотентно: повторный `begin()`/`finish()` с той же парой
  agent/asset не плодит новых объектов и не трогает ничего чужого — проверено `test_agent_helpers.py` t01–t02.
- **`hygiene.py`**: `hygiene_report(export_coll=None, far=100.0)` — только отчёт (дубли `.001`, сироты без fake user,
  далёкие/спрятанные в экспортируемой коллекции объекты, дубли материалов/картинок по содержимому, а не имени,
  повторные модификаторы одного типа, неиспользуемые слоты материалов, лишние UV-слои, упакованные байты);
  `hygiene_clean(export_coll=None, far=100.0)` — чистка того же. **В сцене человека — только `hygiene_report()`**;
  `hygiene_clean()` — исключительно в своём фоновом файле агента (`02-blender-workflow/02-... §5`), иначе удалит
  чужое, что окажется «далеко» или скрыто.
- `test_agent_helpers.py` (4 теста, см. «Тесты» выше по формату): сцена «человека» с чужим объектом (стол со своим
  материалом, коллекцией, движком рендера) — два цикла `begin()`/добавить деталь/`finish()` не меняют его location,
  цвет материала, коллекции, настройки рендера сцены и не создают вторую копию объекта агента; чужой объект, попавший
  в коллекцию агента, эвакуируется, а не удаляется; `hygiene_report()` на пустой сцене — все находки нулевые; на
  заводской сцене (Cube/Light/Camera) корректно видит реальный сиротский материал кисти Grease Pencil «Dots Stroke»
  (это устройство стартового файла 5.2.2, а не баг отчёта).

```bash
python3 ../../scripts/3d/blender_run.py ../../scripts/3d/test_agent_helpers.py -- 99-raw/experiments/U/01-agent-helpers-test
```

Вывод 2026-09-23: `RESULT 4/4 passed in 0.16 s (Blender 5.2.2 LTS)`.

## Границы и оговорки

- Проверено только в 5.2.2. Ветки для < 5.2 (`mod["Socket_N"]` в `gn_set_input`, `use_nodes = True` в `principled`,
  `BLENDER_EEVEE_NEXT` в `set_engine`) написаны по release notes и не запускались [не проверено: нет Blender 4.x на машине].
- Операторы внутри: `uv_unwrap`, `smooth_by_angle(method="MODIFIER")`, `export_glb`, `render_still` — требуют, чтобы
  объект был в слое вида (привязан к коллекции сцены). В GUI через MCP они выполняются в контексте таймера аддона
  (без области) — как в фоне [не проверено вживую: MCP-мост поднимается только в Blender с окном; разбор — агент C1,
  `../../04-ai-agents-mcp/01-mcp-for-blender.md`].
- `export_glb` даёт разумные умолчания (`export_format='GLB'`, `export_apply`), но не пресеты под задачу: что переживает
  экспорт, сжатие и пресеты — `../../08-export-gltf/` (агент E).
- `three_point_lights` калиброван под AgX и 1 BU = 1 м; для других единиц масштабируйте `power`.
- `apply_modifiers` не переносит shape keys (Blender теряет их при применении модификаторов) — предупреждение в журнал.
