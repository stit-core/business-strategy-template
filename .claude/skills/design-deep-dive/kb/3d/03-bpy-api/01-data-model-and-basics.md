# Модель данных и основы Python API Blender 5.2 для ИИ-агента

Волна 1 · агент B · 2026-09-23 · источников прочитано 47 (40 целиком, 7 разделами; в этом файле цитируются 27) ·
экспериментов 23 папки (282 поштучно учтённые проверки, из них 25 тестов bpyx) · Blender 5.2.2 LTS (Python 3.13.13, numpy 2.3.4), модуль bpy 5.2.2 из
PyPI. Все блоки `python` с меткой `[проверено]` извлечены из этого файла и
выполнены в чистой сцене 5.2.2 автоматически (скрипт эксперимента 42).

## Выжимка для агента

1. **Работай через data API (`bpy.data`, методы ID), операторы — только где без них нельзя** (UV-развёртка, ассеты,
   view3d): data API быстрее в 50–700 раз и не зависит от выделения и окна. → §4.1, §11 [проверено: 07-speed]
2. **Каждый новый объект привязывай к коллекции сцены** (`scene.collection.objects.link(ob)`): без этого его нет в
   `scene.objects`, рендере, экспорте и `.blend`, и его нельзя сделать активным. → §3.2 [проверено: 05, 17]
3. **Не ищи данные по имени, которое не задавал сам; храни ссылку.** `primitive_cube_add` при существующем «Cube»
   создаёт «Cube.001»; в русском интерфейсе куб называется «Куб». → §2.4 [проверено: 15, 17]
4. **После `bpy.ops.*_add` бери `bpy.context.object`, после data API — свою ссылку**: data API не меняет
   `context.object`, правка «через контекст» уйдёт старому объекту. → §4.2 [проверено: 04, 17]
5. **Проверяй результат оператора `== {'FINISHED'}`**: `modifier_apply` с неверным именем, `transform_apply` без
   выделения, `join` с одним объектом возвращают `{'CANCELLED'}` без исключения. → §4.3 [проверено: 04]
6. **Контекст оператору — только через `bpy.context.temp_override(...)`** (словарь-аргумент удалён в 4.0:
   `ValueError: 1-2 args execution context is supported`); переопределяй член, который оператор читает (`join` —
   `selected_editable_objects`), узнать — `override.logging_set(True)`. → §4.4 [проверено: 03, 04, 19]
7. **view3d-операторы в фоне работают** с `temp_override(area=…VIEW_3D, region=…WINDOW)` из `context.screen.areas`;
   кадрирование без операторов — `Object.camera_fit_coords`. → §4.5 [проверено: 04]
8. **Edit-операторы (mesh.*, uv.*) — только в EDIT**; данные меша записываются в `ob.data` при выходе из EDIT;
   `mode_set` требует активный объект, который есть в слое вида. → §4.6 [проверено: 04, 17]
9. **После `mode_set`, `remove()` и добавления элементов перечитывай ссылки на сабданные** (вершины, UV-слои,
   точки сплайна): старая ссылка указывает на освобождённую память — мусор или краш. → §2.6 [проверено: 40-bpyx-tests; документация]
10. **Перед чтением `matrix_world`, `bound_box`, `dimensions` вызывай `bpy.context.view_layer.update()`**
    (7 мс на 500 объектов) — иначе значения устаревшие. → §5.3 [проверено: 05, 08]
11. **Вычисленная геометрия — `ob.evaluated_get(depsgraph)`; постоянный меш с модификаторами —
    `bpy.data.meshes.new_from_object(evaluated)`; временный — `evaluated.to_mesh()` + `to_mesh_clear()`.** → §5.2 [проверено: 05]
12. **Габариты текста и кривых — по `bound_box` оригинала после update**: у `evaluated_get(...)` FONT/CURVE
    `bound_box` не учитывает extrude и bevel. → §5.4 [проверено: 09]
13. **Меш из списков: `from_pydata(verts, edges, faces)` — все три аргумента (`[]` для рёбер) + `validate()` +
    `update()`**; грани по умолчанию плоские. → §6.1 [проверено: 06, 17]
14. **Примитивы — `bmesh.ops.create_*`, UV-слой создавать ДО create (`bm.loops.layers.uv.new()`), затем
    `bm.to_mesh(me); bm.free()`**: `calc_uvs=True` без слоя молча ничего не делает. → §6.2 [проверено: 06]
15. **Массовая правка координат — `mesh.attributes["position"].data.foreach_set("vector", float32)`**: 0,3 мс на
    250 тыс. вершин против 26 мс у `vertices.foreach_set("co")` и 158 мс у цикла. → §6.4, §11 [проверено: 07]
16. **Атрибуты — `mesh.attributes.new(name, type, domain)`; цвета — `mesh.color_attributes`**; повторное имя даёт
    «.001» без ошибки; `vertex_colors` — устаревшая обёртка (только BYTE_COLOR на CORNER). → §6.5 [проверено: 03, 06]
17. **Гладкость по углу: `me.shade_smooth()` + `me.set_sharp_from_angle(angle=…)`** (разрушающе) или оператор
    `object.shade_auto_smooth` (модификатор-ассет); `use_auto_smooth` удалён в 4.1. → §6.7 [проверено: 03, 06]
18. **Материалы живут в слотах данных**: `me.materials.append(mat)`; `material_index` — `polygons.foreach_set`;
    `ob.active_material = m` ЗАМЕНЯЕТ материал активного слота. → §6.6 [проверено: 06]
19. **Цвет сокета — линейный RGBA из 4 чисел**: `(1, 0, 0)` → ValueError, `(255, 128, 0, 1)` принимается молча
    (пересвет); hex/CSS переводить sRGB → linear. → §6.6 [проверено: 17]
20. **`ob.modifiers.new(name, TYPE)` возвращает None для типа, несовместимого с объектом** (GREASE_PENCIL_* на меше);
    порядок — `ob.modifiers.move(from_index, to_index)`. → §7.1 [проверено: 00, 10]
21. **Применить модификаторы без оператора: `new_from_object(evaluated, preserve_all_data_layers=True)` +
    `ob.data = new`** (материалы и группы вершин сохраняются, shape keys — нет). → §7.3 [проверено: 10]
22. **Применить трансформации без оператора: `ob.data.transform(M)` + сброс `matrix_basis`; сначала проверь
    `ob.data.users`** (общий меш изменится у всех владельцев). → §9.2 [проверено: 08]
23. **Сначала `rotation_mode`, потом значение вращения** (смена режима пересчитывает и перезаписывает поворот);
    углы в радианах — `(90, 0, 0)` молча превращается в 90 радиан. → §9.3 [проверено: 08, 17]
24. **Камера на цель: `(target - loc).to_track_quat('-Z', 'Y').to_euler()`**; с `'Z'` цель оказывается за камерой. → §9.4 [проверено: 08]
25. **Масштаб и оси: 1 BU = 1 м (glTF в метрах), Z вверх, вид спереди — камера на −Y смотрит на +Y.** → §9.6 [проверено: 08]
26. **Имена ID — до 255 байт** (чисто кириллическое имя ≈ 127 символов; в старых версиях предел был 63 байта —
    версия изменения не установлена); коллизия → «.001»;
    `ID.rename(name, mode='ALWAYS')` отнимает имя у другого ID. → §2.4 [проверено: 05]
27. **Пути — абсолютные**: относительный путь экспорта попадает в cwd процесса, `//` в несохранённом файле ломает
    запись рендера. → §10.2 [проверено: 17]
28. **Снимок сцены в фоне — `wm.save_as_mainfile(filepath=abs, copy=True)`**; объекты без коллекции не
    сохраняются, `use_fake_user = True` сохраняет ID без пользователей; сжатие Zstd по умолчанию. → §10.1 [проверено: 05, 14]
29. **Чистка — `bpy.data.orphans_purge(do_recursive=True)` и `bpy.data.batch_remove(ids)`** (функции, без оператора); глобальный `orphans_purge` — только в своём файле, в сцене человека — `batch_remove` своих ID по тегу (`../02-blender-workflow/01-scene-organization-naming-units.md` §2.3). → §2.5 [проверено: 05; I/01]
30. **«Есть ли свойство» — `"x" in bpy.types.T.bl_rna.properties`, а не `hasattr(bpy.types.T, "x")`**: на классе
    `hasattr` видит только Python-члены и для RNA всегда False. → §2.8 [проверено: 03, 17]
31. **Значения перечислений проверяй по фактическому списку**: RNA занижает динамические (движки, view transform,
    цветовые пространства); неверное присваивание даёт TypeError с полным списком. → §2.8 [проверено: 00, 13]
32. **Потоки Python с bpy запрещены** (краш); ждать — `bpy.app.timers`, параллелить — отдельные процессы Blender. → §4.7 [документация]
33. **MCP `execute_blender_code`: переменные между вызовами не живут, модули в `sys.modules` и данные сцены живут**;
    `__file__` нет, `__name__ == 'builtins'` (блок `if __name__ == "__main__"` не выполнится). → §1.2 [проверено: 16]
34. **Модуль `bpy` 5.2.2 из PyPI (Python 3.13) ведёт себя как `blender -b`**: то же окно без области, рендер, экспорт. → §1.3 [проверено: 18]
35. **Скрипт — идемпотентный**: очистить свою сцену/коллекцию, собрать по параметрам, в конце напечатать
    статистику и проверить `assert`. → §12 [проверено: 41-bpyx-example]

## 1. Где исполняется код

### 1.1 Три способа запуска

| Способ | Как | Контекст | Старт | Когда выбирать |
|---|---|---|---|---|
| MCP `execute_blender_code` | код уходит в Blender пользователя с окном; аддон делает `exec(code, {"bpy": bpy})` в таймере | GUI-сеанс пользователя; язык интерфейса пользователя (имена данных переводятся); `context.area` = None в таймере [не проверено вживую] | мгновенно (Blender уже запущен) | итеративная работа в сцене пользователя, скриншоты вьюпорта |
| `blender -b --factory-startup --python script.py -- args` | `python3 ../../scripts/3d/blender_run.py script.py -- args` (таймаут, журнал) | окно «Layout» есть, `area/region/space_data` = None; en_US; без аддонов пользователя | 0,34 с | воспроизводимые сборки, рендер и экспорт, тесты |
| модуль `bpy` из PyPI | `pip install bpy==5.2.2` в venv Python 3.13; `import bpy` | как у `blender -b` (`bpy.app.background` и `bpy.app.module` = True) | 0,37 с | один процесс с pip-пакетами, pytest |

[проверено: 04-ops-background, 16-mcp-namespace, 18-bpy-pypi]. MCP-мост поднимается только в Blender с окном — его
разбор и правила вызовов у агента C1 (`../04-ai-agents-mcp/01-mcp-for-blender.md`).

```bash
# Blender 5.2.2 — [проверено] запуск скрипта в фоне с таймаутом и журналом
python3 ../../scripts/3d/blender_run.py my_script.py -- out/        # код выхода 0 / 1 (исключение) / 124 (таймаут)
python3 ../../scripts/3d/blender_run.py --expr "import bpy; print(bpy.app.version_string)"
python3 ../../scripts/3d/bpy_probe.py node ShaderNodeMix data_type=RGBA   # справка по API из самого Blender (JSON)
```

Аргументы после `--` скрипт читает так: `argv = sys.argv[sys.argv.index("--") + 1:]`. Скрипт, который вызывает
`argparse` без `--`, закроет Blender через `sys.exit` [S1].

### 1.2 Что живёт между вызовами MCP

Аддон MCP протокола 7 (`~/.config/blender/5.2/scripts/addons/blender_mcp.py`, стр. 1490) выполняет присланный код в
**свежем** словаре `{"bpy": bpy}` и возвращает только напечатанное (`print`) [S38]. Имитация в фоне показала
[проверено: 16-mcp-namespace]:

| Что | Живёт между вызовами? | Следствие |
|---|---|---|
| переменные (`x = 5`) | нет — `NameError: name 'x' is not defined` | в каждом вызове заново находить объекты (по имени, которое задал сам, или `session_uid`) |
| данные сцены (`bpy.data`) | да | состояние хранить в сцене, а не в переменных |
| модули в `sys.modules` | да | библиотеку помощников импортировать один раз, дальше `import bpyx` мгновенно |
| `mathutils`, `bmesh`, `math` | не импортированы | импортировать в каждом вызове |
| `__file__` | нет (`NameError`) | не опираться на путь скрипта |
| `__name__` | `'builtins'` | блок `if __name__ == "__main__":` не выполнится |
| возвращаемое значение выражения | не видно | печатать результат |

`importlib.reload(mod)` может вернуть старый код: если файл перезаписан в ту же секунду и того же размера, Python
берёт `__pycache__/*.pyc` (проверено: 1 → reload → 1). Лечится `sys.dont_write_bytecode = True` до импорта.

```python
# Blender 5.2.2 — [проверено] первый вызов MCP: подключить помощники
import sys, importlib
import bpy                             # в MCP bpy уже есть в пространстве имён; импорт безвреден
sys.dont_write_bytecode = True
p = "../../scripts/3d"           # от корня базы kb/3d; в MCP — полный путь к этой папке
if p not in sys.path:
    sys.path.insert(0, p)
import bpyx
importlib.reload(bpyx)
print("bpyx", bpyx.__version__, "| Blender", bpy.app.version_string)
```

### 1.3 Модуль bpy из PyPI

На 2026-09-22 на PyPI есть `bpy` 5.2.2 (и 5.2.0–5.2.1, 5.1.x, 5.0.x, 4.5.x), `requires_python ==3.13.*`, колёса cp313
для Linux x86_64 (402 МБ), macOS arm64, Windows amd64/arm64 [S39]. Был установлен в среде `venv-bpy` базы (1,0 ГБ; удалена 23.09.2026 по решению владельца, пересоздать — строка `venv-bpy/` в `../../scripts/3d/README.md`).
Проверено: `import bpy` 0,33–0,37 с; окно «Layout» с областью VIEW_3D; `primitive_cube_add`, `mode_set`,
`uv.smart_project`, `view3d.camera_to_view_selected` с override, рендер EEVEE/Cycles/Workbench, экспорт glTF,
`save_as_mainfile`, `bpy.utils.expose_bundled_modules()` + OpenImageIO 3.1.13.1; тесты bpyx 25/25
[проверено: 18-bpy-pypi, 40-bpyx-tests]. Версия модуля должна совпадать с Blender, в котором откроют `.blend`.

## 2. ID-блоки, bpy.data и пользователи

### 2.1 Что такое ID

Всё, что сохраняется в `.blend` и видно в `bpy.data.*` (objects, meshes, materials, curves, lights, cameras,
images, node_groups, actions, worlds, collections, scenes), — ID-блок. Создавать только методами коллекций:
`bpy.types.Mesh()` → `TypeError: bpy_struct.__new__(type): expected a single argument` [S9]. У ID есть `users`
(сколько ссылок), `use_fake_user`, `session_uid` (стабилен в сеансе, не меняется при переименовании), `library`
(связанный из другого файла), `rename()` (4.3+). В 5.2 появился `bpy.data.all_ids` — итератор по всем ID [S16, S29].

```python
# Blender 5.2.2 — [проверено] пользователи ID и сироты
import bpy
me = bpy.data.meshes.new("M")
assert me.users == 0                         # сирота: не сохранится в .blend
ob = bpy.data.objects.new("A", me)
assert me.users == 1 and ob.users == 0       # объект ещё не в коллекции
bpy.context.scene.collection.objects.link(ob)
assert ob.users == 1 and ob.name in bpy.context.scene.objects
print("ID всего:", sum(1 for _ in bpy.data.all_ids), "| session_uid:", ob.session_uid)
```

### 2.2 Объект и данные объекта

Объект (`bpy.types.Object`) — трансформация, родитель, модификаторы, констрейнты, видимость, слоты материалов с
`link='OBJECT'`. Данные (`ob.data`) — геометрия и её свойства: `Mesh`, `Curve`/`TextCurve` (`curves.new(type=
'CURVE'|'FONT')`), `Light` (`lights.new(name, 'POINT'|'SUN'|'SPOT'|'AREA')`), `Camera`, `Armature`, `GreasePencil`
(v3, 4.3+), `Curves` (новые кривые/волосы), `PointCloud`, `Volume`. Пустышка (Empty) — объект с `data = None`:
`bpy.data.objects.new("E", None)`. Тип объекта задаётся типом данных и дальше не меняется (`ob.type` только чтение).

### 2.3 Общие данные и копии

```python
# Blender 5.2.2 — [проверено] общие данные (linked duplicates) и независимая копия
import bpy, bmesh
me = bpy.data.meshes.new("Cube")
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0); bm.to_mesh(me); bm.free()
a = bpy.data.objects.new("A", me); bpy.context.scene.collection.objects.link(a)
b = bpy.data.objects.new("B", me); bpy.context.scene.collection.objects.link(b)
assert me.users == 2                              # правка меша видна у обоих
c = a.copy()                                      # копия объекта ДЕЛИТ данные и не попадает в сцену
assert c.data == a.data and c.name not in bpy.context.scene.objects
c.data = a.data.copy()                            # независимая копия данных: «Cube.001»
bpy.context.scene.collection.objects.link(c)
assert c.data != a.data and me.users == 2
```

Общий меш — дешёвый способ сделать 500 одинаковых объектов (0,0034 с против 0,045 с со своим мешем у каждого)
[проверено: 07-speed]; но `ob.data.transform()`, `modifier_apply` и правка вершин изменят всех владельцев:
`modifier_apply` на меше с двумя пользователями падает с `RuntimeError: Error: Modifiers cannot be applied to
multi-user data`, помогает параметр `single_user=True` [проверено: 10-modifiers].

### 2.4 Имена

- Имя ID уникально в своей коллекции `bpy.data.*`; коллизия даёт суффикс «.001» новому (или переименовываемому) ID,
  старый не трогается [проверено: 05-data-model].
- **Предел — 255 байт UTF-8** в 5.2.2 (300 латинских символов → 255; кириллица 280 символов → 137 символов = 255
  байт) [проверено: 05-data-model]. Советы «имена ≤ 63 символов» относятся к старым версиям (предел 63 байта; в какой
  версии его подняли, в прочитанных release notes не найдено) [не проверено: старая версия].
- `ID.rename(name, mode=…)` (4.3+): `'NEVER'` (как присвоение), `'ALWAYS'` — забрать имя, другой ID получит «.001»
  (возврат `'RENAMED_COLLISION_FORCED'`), `'SAME_ROOT'` [проверено: 05-data-model, S25].
- Имена новых данных переводятся, если у пользователя язык интерфейса не английский и включено
  `use_translate_new_dataname` (по умолчанию включено): в ru_RU куб — «Куб», нода — «Принципиальный BSDF»,
  мир — «Фон»; имена и identifier сокетов не переводятся [проверено: 15-localization].
- Документация советует не ссылаться на данные по имени, а хранить ссылку или словарь «моё имя → ID» [S3].

```python
# Blender 5.2.2 — [проверено] имена: .001, rename, предел 255 байт
import bpy
x1 = bpy.data.objects.new("Mug", None); x2 = bpy.data.objects.new("Mug", None)
assert (x1.name, x2.name) == ("Mug", "Mug.001")
assert x2.rename("Mug", mode="ALWAYS") == "RENAMED_COLLISION_FORCED" and x1.name == "Mug.001"
x3 = bpy.data.objects.new("Кружка_" * 40, None)
assert len(x3.name.encode()) == 255 and len(x3.name) == 137
```

### 2.5 Удаление и чистка

- `bpy.data.objects.remove(ob, do_unlink=True)` — удаляет объект; любые ссылки на него после этого дают
  `ReferenceError: StructRNA of type Object has been removed` [проверено: 05-data-model]; ссылки на сабданные (вершины
  удалённого меша) могут привести к крашу [S1].
- `bpy.data.batch_remove(ids)` — пакетное удаление; `bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True,
  do_recursive=True)` — функция BlendData, возвращает число удалённых; оператор `outliner.orphans_purge` тоже работает
  в фоне [проверено: 04, 05].
- Для MCP-сеанса пользователя не применять `wm.read_factory_settings` (сбросит его интерфейс и настройки) и `bpyx.clear_scene()` (удалит все объекты сцены, её коллекции и сирот — 22 из 31 ID человека, I/01): убирать только своё по тегу (`../02-blender-workflow/01-scene-organization-naming-units.md` §2); `clear_scene()` — только для своего фонового файла. Удалить
  объекты своей коллекции — по тегу [проверено: 40-bpyx-tests; I/01].

### 2.6 Висячие ссылки

Python-объект, обёртывающий данные Blender, — указатель в память Blender. Память перевыделяется при: смене режима
`mode_set` (EDIT ↔ OBJECT перевыделяет данные меша, UV-слои, кости), добавлении элементов в коллекцию
(`bezier_points.add()`, `vertices.add()`, `CollectionProperty.add()`), удалении, undo/redo [S1]. Документация: доступ
к старой ссылке может уронить Blender; `remove()` защищает только сам удалённый ID. В тестах bpyx висячая ссылка на
`MeshUVLoopLayer`, взятая до `mode_set`, после возврата в OBJECT вернула мусор: `uv.name` →
`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa0` [проверено: 40-bpyx-tests]. Правило: хранить имена или
индексы, после операции перечитывать `ob.data.uv_layers[name]`.

```python
# Blender 5.2.2 — падает: ReferenceError [проверено] доступ к удалённому
import bpy
ob = bpy.data.objects.new("Tmp", None)
bpy.data.objects.remove(ob, do_unlink=True)
print(ob.name)            # ReferenceError: StructRNA of type Object has been removed
```

Ещё две ловушки из документации [S1]: итерация по `Collection.all_objects` ломается при смене `hide_viewport`,
`hide_select`, `hide_render` → итерировать копию `all_objects[:]`; переименование объектов в цикле по
`bpy.data.objects` пересортировывает коллекцию → сначала `list(bpy.data.objects)`.

### 2.7 Пользовательские свойства

`ob["brand"] = "Acme"`, `ob["size_cm"] = 12.5`, `ob["tags"] = {"a": 1}` — работают на ID (объект, меш, материал,
сцена, коллекция…), сохраняются в `.blend`, при экспорте glTF с `export_extras=True` уходят в `extras`
[проверено: 05-data-model; экспорт — агент E]. Вложенность словарей ≤ 1024 (5.2) [S29]. С 5.0 свойства,
объявленные через `bpy.props` (например, `scene.cycles`), больше не читаются как `scene["cycles"]` → `KeyError`
[проверено: 03-version-drift, S27].

### 2.8 Интроспекция: что есть в этой версии

```python
# Blender 5.2.2 — [проверено] проверка свойств и фактических значений перечислений
import ast, re
import bpy

assert not hasattr(bpy.types.Mesh, "vertices")                  # hasattr на КЛАССЕ не видит RNA
assert "vertices" in bpy.types.Mesh.bl_rna.properties            # правильно
assert "validate" in bpy.types.Mesh.bl_rna.functions
assert "use_auto_smooth" not in bpy.types.Mesh.bl_rna.properties  # удалено в 4.1

def enum_values(owner, prop):
    """Фактический список значений: неверное присваивание → TypeError перечисляет допустимые."""
    try:
        setattr(owner, prop, "__invalid__")
    except TypeError as e:
        return list(ast.literal_eval("(" + re.search(r"not found in \((.*)\)", str(e)).group(1) + ",)"))

r = bpy.context.scene.render
print([i.identifier for i in r.bl_rna.properties["engine"].enum_items])   # RNA: ['BLENDER_EEVEE'] — занижено
print(enum_values(r, "engine"))            # ['BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES']
print(enum_values(bpy.context.scene.view_settings, "view_transform"))
```

Фактические списки 5.2.2 [проверено: 00-bpy-probe, 17]: движки `BLENDER_EEVEE`, `BLENDER_WORKBENCH`, `CYCLES`;
view transform `Standard`, `ACES 1.3`, `ACES 2.0`, `Khronos PBR Neutral`, `AgX` (по умолчанию), `Filmic`,
`Filmic Log`, `False Color`, `Raw`; looks — `None` и 9 вариантов «AgX - …» («AgX - Punchy», «AgX - Medium High
Contrast» …); цветовые пространства картинок — 67 значений, среди них `sRGB`, `Non-Color`, `Linear Rec.709`,
`Linear Rec.2020`, `ACEScg`, `scene_linear`, `Display P3` (значения `Linear` нет — оно переименовано). Справочник без
ручного кода: `python3 ../../scripts/3d/bpy_probe.py enum scene.render.engine`, `… enum image.colorspace_settings.name`.

У RNA-свойств 5.2 есть `is_deprecated`, `deprecated_note`, `deprecated_version`, `deprecated_removal_version`:
`bpy_probe.py deprecated` выдаёт полный список из 32 пунктов (все с удалением в 6.0) — подробно в
`03-version-drift-3.6-to-5.2.md §3` [проверено: 00-bpy-probe].

## 3. Сцена, коллекции, слои вида

### 3.1 Иерархия

`Scene` → корневая коллекция `scene.collection` (не ID, встроенная) → дочерние `Collection` (ID). Объект может
лежать в нескольких коллекциях (`ob.users_collection`). `scene.objects` — все объекты сцены по всем коллекциям;
`bpy.data.objects` — все объекты файла, включая не привязанные ни к одной сцене. `ViewLayer` (`context.view_layer`)
— что из сцены включено: `view_layer.layer_collection.children[...]` с флагами `exclude`, `hide_viewport`;
`view_layer.objects` — объекты слоя, `view_layer.objects.active` — активный.

### 3.2 Привязка объекта и коллекции

```python
# Blender 5.2.2 — [проверено] объект и коллекция: что видно, а что нет
import bpy
scene, vl = bpy.context.scene, bpy.context.view_layer
coll = bpy.data.collections.new("Props")              # коллекция вне сцены — невидима
ob = bpy.data.objects.new("Box", bpy.data.meshes.new("Box"))
coll.objects.link(ob)
assert ob.name not in scene.objects
try:
    vl.objects.active = ob
except RuntimeError as e:
    print(e)          # Error: ViewLayer 'ViewLayer' does not contain object 'Box'
scene.collection.children.link(coll)                  # теперь в сцене
assert ob.name in scene.objects
vl.layer_collection.children["Props"].exclude = True
vl.update()                                           # exclude действует после update
assert ob.name not in vl.objects and not ob.visible_get()
vl.layer_collection.children["Props"].exclude = False
ob.hide_set(True)                                     # скрыть в этом слое вида (не для рендера)
assert not ob.visible_get() and not ob.hide_render
ob.hide_set(False)
```

- `ob.hide_set()` — только вьюпорт текущего слоя вида (не сохраняется в рендер); `ob.hide_viewport` — глобально
  во вьюпорте; `ob.hide_render` — в рендере. Старое `ob.hide = True` (2.7x) → `AttributeError` [проверено: 03].
- Объект, созданный data API и не привязанный, не сохраняется: после `save_as_mainfile` + `open_mainfile` его нет,
  а его меш (у которого в момент сохранения был пользователь) — есть [проверено: 05-data-model].

## 4. Контекст и операторы

### 4.1 bpy.data против bpy.ops

| | data API (`bpy.data`, методы ID) | операторы (`bpy.ops`) |
|---|---|---|
| Что принимают | объекты и параметры явно | только контекст (активный, выделенные, режим, область) |
| Возврат | созданный объект / значение | `{'FINISHED'}` / `{'CANCELLED'}`; ошибка — `RuntimeError` только при ERROR-отчёте [S12] |
| Скорость | 500 кубов за 0,045 с (свой меш) или 0,0034 с (общий) | 500 кубов за 2,44 с — ≈4,9 мс на вызов |
| Undo | не пишут шаг undo | пишут (в GUI) |
| В фоне | всегда | зависят от области/режима; часть не работает без override |

[проверено: 04-ops-background, 07-speed, S2, S12]. Операторы неизбежны для: UV-развёртки (`uv.smart_project`,
`uv.unwrap`, `uv.lightmap_pack`), добавления модификатора-ассета (`object.shade_auto_smooth`), view3d-кадрирования
(есть замена — `camera_fit_coords`), импорта файлов (`wm.obj_import`, `import_scene.gltf`), экспорта
(`export_scene.gltf`), рендера (`render.render`), сохранения (`wm.save_as_mainfile`), edit-моделирования, которое
неудобно в bmesh.

### 4.2 context.object после создания

```python
# Blender 5.2.2 — [проверено] кто «активный» после оператора и после data API
import bpy
bpy.ops.mesh.primitive_cube_add(size=1, location=(3, 0, 0))
new = bpy.context.object                       # оператор делает новый объект активным и единственным выделенным
assert new.location.x == 3 and bpy.context.selected_objects == [new]
ob = bpy.data.objects.new("DataCube", bpy.data.meshes.new("dc"))
bpy.context.scene.collection.objects.link(ob)
assert bpy.context.object == new               # data API активный объект НЕ меняет
bpy.context.view_layer.objects.active = ob     # сделать активным явно (context.active_object = … → ошибка: только чтение)
ob.select_set(True)
assert bpy.context.object == ob
```

В сцене по умолчанию (Cube/Light/Camera) `bpy.data.objects["Cube"]` после `primitive_cube_add` вернёт старый куб,
а новый — «Cube.001» [проверено: 17-llm-failure-modes].

### 4.3 poll и результат

Оператор с неподходящим контекстом падает на `poll()`: `RuntimeError: Operator bpy.ops.object.mode_set.poll()
Context missing active object`, `… uv.smart_project.poll() failed, context is incorrect`, `… view3d.view_all.poll()
Expected a view3d region` [проверено: 04]. Проверить заранее — `bpy.ops.x.y.poll()`. Хуже — оператор, который
проходит poll и отменяется без исключения:

| Вызов (5.2.2, фон) | Результат | Исключение |
|---|---|---|
| `object.modifier_apply(modifier="Nope")` | `{'CANCELLED'}` | нет |
| `object.transform_apply(scale=True)` без выделенных | `{'CANCELLED'}` | нет |
| `object.join()` с одним выделенным | `{'CANCELLED'}` («Warning: No mesh data to join») | нет |
| `object.join()` c override только `selected_objects` | `{'CANCELLED'}` (join читает `selected_editable_objects`) | нет |
| `mesh.separate(type='LOOSE')` на связном меше | `{'CANCELLED'}` | нет |
| `view3d.camera_to_view_selected()` без области | `{'CANCELLED'}` при `poll() == True` | нет |
| `object.modifier_add_node_group(asset_library_type='ESSENTIALS', …)` в фоне | `{'CANCELLED'}` («Asset loading is unfinished») | нет |

[проверено: 04-ops-background, 19-stackexchange-snippets]. Правило: `r = bpy.ops…(); assert r == {'FINISHED'}, r`.

### 4.4 temp_override

```python
# Blender 5.2.2 — [проверено] оператор над объектом без выделения и активности
import bpy, bmesh
def cube(name, x):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.location.x = x
    bpy.context.scene.collection.objects.link(ob); return ob
a, b = cube("A", 0), cube("B", 3)
with bpy.context.temp_override(active_object=a, object=a, selected_objects=[a], selected_editable_objects=[a]):
    assert bpy.ops.object.shade_smooth() == {"FINISHED"}
a.modifiers.new("Sub", "SUBSURF")
with bpy.context.temp_override(object=a, active_object=a):
    assert bpy.ops.object.modifier_apply(modifier="Sub") == {"FINISHED"}
with bpy.context.temp_override(active_object=a, selected_editable_objects=[a, b]) as ov:
    ov.logging_set(True, hide_missing=True)     # печатает, какие члены контекста читает оператор
    assert bpy.ops.object.join() == {"FINISHED"}
assert len(a.data.vertices) == 26 + 8
```

- Старый способ `bpy.ops.object.delete(override_dict)` удалён в 4.0 → `ValueError: 1-2 args execution context is
  supported` [проверено: 03, S21]. Позиционные аргументы оператора — только `execution_context` ('EXEC_DEFAULT',
  'INVOKE_DEFAULT', …) и `undo` [S12].
- Вложенные `temp_override` складываются; после выхода из `with` контекст восстанавливается [S13].

### 4.5 Операторы view3d в фоне

В фоне у `context` есть окно (`len(wm.windows) == 1`, экран «Layout» с областями PROPERTIES, OUTLINER,
DOPESHEET_EDITOR, VIEW_3D), но `context.area`, `context.region`, `context.space_data` — None; окно сохраняется после
`read_factory_settings(use_empty=True)` и `open_mainfile` [проверено: 04-ops-background]. Регион VIEW_3D имеет
размер 1574×954 — view3d-операторы работают с override:

```python
# Blender 5.2.2 — [проверено] view3d-оператор в фоне и замена без оператора
import bpy
from mathutils import Vector
cam, cube = bpy.data.objects["Camera"], bpy.data.objects["Cube"]      # сцена по умолчанию
area = next(a for a in bpy.context.screen.areas if a.type == "VIEW_3D")
region = next(r for r in area.regions if r.type == "WINDOW")
for o in bpy.context.selected_objects:
    o.select_set(False)
cube.select_set(True); bpy.context.view_layer.objects.active = cube
with bpy.context.temp_override(area=area, region=region):
    assert bpy.ops.view3d.camera_to_view_selected() == {"FINISHED"}
by_op = cam.location.copy()
dg = bpy.context.evaluated_depsgraph_get()                            # то же без оператора:
coords = [c for v in cube.bound_box for c in (cube.matrix_world @ Vector(v))]
loc, scale = cam.camera_fit_coords(dg, coords)
assert (Vector(loc) - by_op).length < 1e-3
```

Без регионов (файл, сохранённый без VIEW_3D) override невозможен — используйте `camera_fit_coords` и
`bpyx.frame_camera`. Не работают в фоне даже с override: `node.add_node`, `image.save_as` (нужны их редакторы) —
в data API есть `tree.nodes.new(...)` и `Image.save_render(filepath=…)` / `image.save()` [проверено: 04, 13].

### 4.6 Режимы и edit mode

- `bpy.ops.object.mode_set(mode='EDIT')` требует активный объект, который есть в слое вида; редактируемые операторы
  `mesh.*` и `uv.*` проходят poll только в EDIT [проверено: 04].
- В EDIT у меша свои данные: после `mesh.subdivide` `ob.data.vertices` всё ещё 8 — данные пишутся в меш при выходе
  из EDIT (или `ob.update_from_editmode()`, или `bmesh.update_edit_mesh(me)` при работе через
  `bmesh.from_edit_mesh`) [проверено: 04, 17, S4, S14].
- В фоне работают: `mesh.subdivide`, `mesh.bevel`, `mesh.inset`, `mesh.extrude_region_move`, `mesh.remove_doubles`,
  `mesh.normals_make_consistent`, `uv.smart_project`, `uv.unwrap`, `uv.lightmap_pack`, `uv.cube_project`,
  `uv.cylinder_project`; не работает `uv.project_from_view` [проверено: 04].

```python
# Blender 5.2.2 — [проверено] edit mode: правка через bmesh и синхронизация
import bpy, bmesh
ob = bpy.data.objects["Cube"]
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(ob.data)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
bmesh.update_edit_mesh(ob.data, loop_triangles=True, destructive=True)
assert len(ob.data.vertices) == 8            # ob.data ещё не знает об изменениях
ob.update_from_editmode()                    # или mode_set(OBJECT)
assert len(ob.data.vertices) == 26
bpy.ops.object.mode_set(mode="OBJECT")
```

### 4.7 Потоки, таймеры, прерывания

Python-потоки с доступом к bpy не поддерживаются: краш в произвольном месте; допустимо, только если потоки
завершаются (`join`) до конца скрипта и не трогают bpy [S5]. Для ожидания в GUI — `bpy.app.timers.register(fn)`;
для параллели — отдельные процессы `blender -b` (на этой машине — не больше одного процесса Blender на агента).
Отладка краша — модуль `faulthandler` [S1].

## 5. Depsgraph и вычисленные данные

### 5.1 Оригинал и вычисленная копия

Модификаторы, geometry nodes, анимация, драйверы и констрейнты применяются в граф зависимостей (depsgraph) к копии
объекта. `bpy.context.evaluated_depsgraph_get()` обновляет граф и возвращает его; `ob.evaluated_get(dg)` —
вычисленный объект; `evaluated.original` — обратно [S17]. Для MESH `evaluated.data` — меш с модификаторами; для других
типов (кривые, текст) `evaluated.data` модификаторов НЕ содержит — отсюда ловушка §5.4 [S17].

### 5.2 Меш из вычисленного объекта

```python
# Blender 5.2.2 — [проверено] evaluated, to_mesh, new_from_object
import bpy
ob = bpy.data.objects["Cube"]
sub = ob.modifiers.new("Sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
dg = bpy.context.evaluated_depsgraph_get()
oe = ob.evaluated_get(dg)
assert (len(ob.data.vertices), len(oe.data.vertices)) == (8, 26)   # граф вьюпорта: levels, не render_levels
tmp = oe.to_mesh()                                    # временный: не в bpy.data, имя совпадает с оригиналом
assert len(tmp.vertices) == 26 and not any(m.as_pointer() == tmp.as_pointer() for m in bpy.data.meshes)
oe.to_mesh_clear()
keep = bpy.data.meshes.new_from_object(oe)            # постоянный, users = 0 — назначьте объекту
assert len(keep.vertices) == 26 and keep.users == 0
assert len(bpy.data.meshes.new_from_object(ob).vertices) == 8   # от оригинала — без модификаторов
```

`new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=dg)` сохраняет пользовательские атрибуты и
группы вершин; ссылки на материалы переназначаются на оригинальные [S17, проверено: 10-modifiers].

### 5.3 Когда пересчитывается

`ob.location = …` не меняет `ob.matrix_world` до `bpy.context.view_layer.update()` (или
`evaluated_depsgraph_get()`) [проверено: 05, S3]. `ob.bound_box` оригинала — это границы ВЫЧИСЛЕННОЙ геометрии, но
тоже только после обновления: после добавления Array max.x = 0.5 (устарел), после `evaluated_depsgraph_get()` — 2.5
[проверено: 08]. Стоимость `view_layer.update()` — 7 мс на 500 объектов [проверено: 07]. Входы модификатора GN через
`mod.properties.inputs.X.value` (5.2) пересчёт не запускают даже после `view_layer.update()` — нужен `ob.update_tag()`
(`02-nodes-from-python.md §6.3`) [проверено: 12-geonodes].

### 5.4 Габариты

```python
# Blender 5.2.2 — [проверено] мировые габариты: оригинал после update, а не evaluated
import bpy
from mathutils import Vector
cu = bpy.data.curves.new("T", "FONT"); cu.body = "Hello"; cu.extrude = 0.1; cu.bevel_depth = 0.02
ob = bpy.data.objects.new("T", cu); bpy.context.scene.collection.objects.link(ob)
dg = bpy.context.evaluated_depsgraph_get()
def dims(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector(map(max, *pts)) - Vector(map(min, *pts))
assert abs(dims(ob).z - 0.24) < 1e-3                    # оригинал: extrude + bevel учтены
assert dims(ob.evaluated_get(dg)).z < 1e-6               # evaluated FONT: 0 — ловушка 5.2.2
```

Для кольца-кривой r = 1 с `bevel_depth = 0.1` `bound_box` вычисленного объекта дал ±2 × ±2 × ±1 вместо
±1.1 × ±1.1 × ±0.1 [проверено: 09-text-curves]. Общая утилита `../../scripts/3d/render_views.py` берёт габариты с
evaluated-объекта — для текста и кривых её кадр и свет считаются по неверным габаритам (передано оркестратору в отчёте).

### 5.5 Инстансы

Инстансы (коллекция-инстанс, GN Instance on Points без Realize) не попадают в `evaluated.data` и
`new_from_object`: в примере разброса без Realize — 4 вершины основы в меше и 160 инстансов в
`depsgraph.object_instances` [проверено: 12-geonodes].

```python
# Blender 5.2.2 — [проверено] обход объектов и инстансов графа
import bpy
coll = bpy.data.collections.new("Src")
src = bpy.data.objects.new("Src", bpy.data.meshes.new("s")); coll.objects.link(src)
inst = bpy.data.objects.new("Inst", None)
inst.instance_type = "COLLECTION"; inst.instance_collection = coll
bpy.context.scene.collection.objects.link(inst)
dg = bpy.context.evaluated_depsgraph_get()
rows = [(oi.object.name, oi.is_instance, oi.parent.name if oi.parent else None) for oi in dg.object_instances]
assert ("Src", True, "Inst") in rows
```

## 6. Геометрия без операторов

### 6.1 from_pydata

```python
# Blender 5.2.2 — [проверено] меш из списков
import bpy
verts = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0), (0, 0, 1)]
faces = [(0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
me = bpy.data.meshes.new("Pyramid")
me.from_pydata(verts, [], faces)         # edges=[] → рёбра выводятся из граней; shade_flat=True по умолчанию
if me.validate(verbose=False):           # True = что-то исправлено (дубли индексов, вырожденные грани)
    print("меш исправлен")
me.update()
ob = bpy.data.objects.new("Pyramid", me); bpy.context.scene.collection.objects.link(ob)
assert (len(me.vertices), len(me.edges), len(me.polygons)) == (5, 8, 5)
assert not me.polygons[0].use_smooth
```

- Сигнатура 5.2: `from_pydata(vertices, edges, faces, shade_flat=True)`; вызов с двумя списками →
  `TypeError: Mesh.from_pydata() missing 1 required positional argument: 'faces'` [проверено: 17].
- Грань `(0, 0, 1)` `validate()` удаляет (в журнале «ERROR Face 2 has duplicate vertex 0») [проверено: 06].
  Индексы за пределами массива `from_pydata` не проверяет [S9-doc from_pydata: «Invalid mesh data … not prevented»].
- `Mesh.update(calc_edges=False, calc_edges_loose=False)` — параметра `calc_loop_triangles` в 5.2 нет [проверено: 03].

### 6.2 bmesh: примитивы и жизненный цикл

`bm = bmesh.new()` → операции → `bm.to_mesh(me)` → `bm.free()`; без `to_mesh` изменения теряются (тихо), после
`free()` доступ → `ReferenceError: BMesh data of type BMesh has been removed`; индекс `bm.verts[i]` после изменений —
`IndexError: … outdated internal index table, run ensure_lookup_table() first` [проверено: 17, S14].

| `bmesh.ops.…` (5.2.2) | Вершин / граней | Замечания |
|---|---|---|
| `create_cube(bm, size=2)` | 8 / 6 | size — полная сторона |
| `create_uvsphere(bm, u_segments=32, v_segments=16, radius=1)` | 482 / 512 | |
| `create_icosphere(bm, subdivisions=2, radius=1)` | 42 / 80 | габарит X 1.902 (вершины не на ±X); subdivisions=3 → 162 / 320 |
| `create_cone(bm, cap_ends=True, segments=32, radius1=1, radius2=0, depth=2)` | 33 / 33 | центр в начале координат, z ∈ [−1, 1] |
| то же с `radius1 = radius2 = 1` (цилиндр) | 64 / 34 | |
| `create_circle(bm, cap_ends=True, segments=32, radius=1)` | 32 / 1 | одна 32-угольная грань; веер — `cap_tris=True` |
| `create_grid(bm, x_segments=10, y_segments=10, size=1)` | 121 / 100 | size — ПОЛОВИНА стороны |
| `create_monkey(bm)` | 507 / 500 | |
| тор | — | в `bmesh.ops` нет; `bpyx.primitive("torus")` (32×16 → 512/512) |

[проверено: 06-geometry-data-api, 40-bpyx-tests]. `calc_uvs=True` работает, только если UV-слой создан заранее:

```python
# Blender 5.2.2 — [проверено] примитив с UV без операторов
import bpy, bmesh
bm = bmesh.new()
bm.loops.layers.uv.new("UVMap")                     # ДО create_*: иначе calc_uvs молча ничего не делает
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.5, calc_uvs=True)
me = bpy.data.meshes.new("Sphere"); bm.to_mesh(me); bm.free()
me.shade_smooth()
ob = bpy.data.objects.new("Sphere", me); bpy.context.scene.collection.objects.link(ob)
assert me.uv_layers.get("UVMap") and len(me.vertices) == 482
```

### 6.3 bmesh: операции

```python
# Blender 5.2.2 — [проверено] inset → extrude → сдвиг → фаска
import math
import bpy, bmesh
from mathutils import Vector
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
top = [f for f in bm.faces if f.normal.z > 0.9]
bmesh.ops.inset_region(bm, faces=top, thickness=0.2, depth=0.0)
ext = bmesh.ops.extrude_face_region(bm, geom=top)
bmesh.ops.translate(bm, vec=Vector((0, 0, 0.5)), verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)])
edges = [e for e in bm.edges if e.calc_face_angle(0) > math.radians(30)]
bmesh.ops.bevel(bm, geom=edges, offset=0.05, offset_type="OFFSET", segments=3, profile=0.5, affect="EDGES",
                clamp_overlap=True)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("Block"); bm.to_mesh(me); bm.free()
bpy.context.scene.collection.objects.link(bpy.data.objects.new("Block", me))
assert (len(me.vertices), len(me.polygons)) == (164, 171)
```

`bmesh.ops.bevel(..., vertex_only=True)` (2.8x) → `TypeError: bevel: keyword "vertex_only" is invalid for this
operator` — теперь `affect='VERTICES'` [проверено: 06]. Прочее проверенное: `triangulate(bm, faces=…,
quad_method='BEAUTY', ngon_method='BEAUTY')`, `remove_doubles(bm, verts=…, dist=1e-4)`, `subdivide_edges(bm,
edges=…, cuts=1, use_grid_fill=True)`.

### 6.4 foreach_get / foreach_set и numpy

```python
# Blender 5.2.2 — [проверено] сетка 200×200 и правка координат массивами
import numpy as np
import bpy
n = 200
xs, ys = np.meshgrid(np.linspace(-1, 1, n), np.linspace(-1, 1, n))
co = np.stack([xs.ravel(), ys.ravel(), np.zeros(n * n)], axis=1).astype(np.float32)
i, j = np.meshgrid(np.arange(n - 1), np.arange(n - 1))
a = (j * n + i).ravel()
quads = np.stack([a, a + 1, a + n + 1, a + n], axis=1).astype(np.int32)
me = bpy.data.meshes.new("Grid")
me.vertices.add(len(co)); me.vertices.foreach_set("co", co.ravel())
me.loops.add(quads.size); me.loops.foreach_set("vertex_index", quads.ravel())
me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4, dtype=np.int32))
me.update(calc_edges=True); me.validate()
pos = me.attributes["position"]                       # быстрый путь к координатам
buf = np.empty(len(me.vertices) * 3, dtype=np.float32)
pos.data.foreach_get("vector", buf)
buf[2::3] = 0.1 * np.sin(buf[0::3] * 6)               # z = f(x)
pos.data.foreach_set("vector", buf)
me.update()
bpy.context.scene.collection.objects.link(bpy.data.objects.new("Grid", me))
assert len(me.polygons) == 199 * 199
```

- Длина буфера строго `len × компонент`; иначе `RuntimeError: internal error setting the array` («Array length
  mismatch (expected 8, got 3)») [проверено: 06, 07].
- `float32` — родной тип: с `float64` та же операция вдвое медленнее (0,058 с против 0,027 с на 250 тыс. вершин)
  [проверено: 07]. С 5.0 `mathutils` отдаёт в numpy float32 через buffer protocol [S27, проверено: 08].

### 6.5 Атрибуты и цвета вершин

Типы атрибутов 5.2: FLOAT, INT, BOOLEAN, FLOAT_VECTOR, FLOAT_COLOR, QUATERNION, FLOAT4X4, STRING, INT8, INT16_2D,
INT32_2D, FLOAT2, FLOAT4, BYTE_COLOR; домены: POINT, EDGE, FACE, CORNER, CURVE, INSTANCE, LAYER [проверено: 06].
Встроенные: `position` (FLOAT_VECTOR/POINT), `sharp_face`, `sharp_edge`, `material_index`, UV-слои (FLOAT2/CORNER);
служебные с точкой: `.corner_vert`, `.corner_edge`, `.edge_verts`, `.select_*` [RN 3.6, проверено: 06]. Фаски и
складки 4.0+: `bevel_weight_edge`, `bevel_weight_vert`, `crease_edge`, `crease_vert` вместо удалённых
`MeshEdge.bevel_weight` и `MeshEdge.crease` [проверено: 03].

```python
# Blender 5.2.2 — [проверено] атрибуты и цвет вершин без операторов
import numpy as np
import bpy
me = bpy.data.objects["Cube"].data
h = me.attributes.new("height", "FLOAT", "POINT")
z = np.empty(len(me.vertices) * 3, np.float32); me.attributes["position"].data.foreach_get("vector", z)
h.data.foreach_set("value", z[2::3].copy())
col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
col.data.foreach_set("color", np.tile([1.0, 0.3, 0.1, 1.0], len(me.vertices)).astype(np.float32))
me.color_attributes.active_color = col
me.color_attributes.render_color_index = me.color_attributes.find("Col")
bw = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
bw.data[0].value = 1.0
dup = me.attributes.new("height", "FLOAT", "POINT")      # повтор имени — без ошибки
assert dup.name == "height.001" and me.attributes.domain_size("CORNER") == 24
```

`mesh.vertex_colors` в 5.2 ещё есть, но это обёртка только над BYTE_COLOR на CORNER — FLOAT_COLOR и POINT она не
видит; писать через `color_attributes` [проверено: 03].

### 6.6 UV, материалы, цвета

```python
# Blender 5.2.2 — [проверено] UV, два материала, material_index, линейный цвет
import numpy as np
import bpy
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
ob = bpy.data.objects["Cube"]; me = ob.data
uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
flat = np.zeros(len(me.loops) * 2, np.float32); uv.uv.foreach_get("vector", flat)   # быстрый путь 4.0+
red = bpy.data.materials.new("Red"); blue = bpy.data.materials.new("Blue")
for m, hexcol in ((red, "E63946"), (blue, "1D3557")):
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")   # use_nodes не нужен (5.0+)
    rgb = [srgb_to_linear(int(hexcol[k:k + 2], 16) / 255) for k in (0, 2, 4)]
    p.inputs["Base Color"].default_value = (*rgb, 1.0)                     # RGBA, 4 числа
me.materials.clear(); me.materials.append(red); me.materials.append(blue)
idx = np.array([1 if p.normal.z > 0.5 else 0 for p in me.polygons], np.int32)
me.polygons.foreach_set("material_index", idx)
assert [s.material.name for s in ob.material_slots] == ["Red", "Blue"] and ob.material_slots[0].link == "DATA"
```

- `uv_layers.new(name=)` → `MeshUVLoopLayer`; UV — атрибут FLOAT2 на CORNER; быстрый доступ `uv.uv` (`vector`),
  старый `uv.data[i].uv` тоже работает; `uv_textures` (2.7x) → AttributeError [проверено: 03, 06].
- `me.materials.append()` создаёт слот у всех объектов с этим мешем (`link='DATA'`); слот с `link='OBJECT'` хранит
  материал в объекте; `ob.active_material = m` ЗАМЕНЯЕТ материал активного слота; `me.materials[0] = m` на пустом
  списке → `IndexError: bpy_prop_collection[index] = value: index 0 out of range, size 0` [проверено: 06, 17].
- `material.diffuse_color` — только цвет вьюпорта (Solid), не рендер и не glTF [проверено: 03].
- Цвет сокета — линейный RGBA: `(1, 0, 0)` → `ValueError: … sequences of dimension 0 should contain 4 items, not 3`;
  `(255, 128, 0, 1)` принимается без ошибки и даёт пересвет [проверено: 17]. Подробно о нодах — `02-nodes-from-python.md`.

### 6.7 Нормали и гладкость (4.1+)

В 4.1 `Mesh.use_auto_smooth` и `auto_smooth_angle` удалены; базовое состояние меша — как старый auto smooth 180°:
угловые (corner) нормали считаются, если есть смесь острых и гладких элементов, custom normals используются всегда
[S30, S22]. Гладкость управляется атрибутами `sharp_face` (грань) и `sharp_edge` (ребро).

| Способ | Код | Итог |
|---|---|---|
| data API, разрушающе | `me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(30))` | цилиндр 32: 64 острых ребра из 96, без модификатора |
| оператор, неразрушающе | `bpy.ops.object.shade_auto_smooth(angle=…)` | модификатор NODES «Smooth by Angle» (ассет), входы `Input_0` Mesh, `Input_1` Angle, `Socket_1` Ignore Sharpness |
| оператор, разрушающе | `bpy.ops.object.shade_smooth_by_angle(angle=…, keep_sharp_edges=True)` | модификатор не добавляет |
| edit mode | `bpy.ops.mesh.set_sharpness_by_angle(angle=…)` | только EDIT |
| плоско / гладко | `me.shade_flat()` / `me.shade_smooth()` (3.6+) | одна строка вместо цикла по `polygons` |

[проверено: 04, 06, 40-bpyx-tests]. `me.normals_domain` сообщает, какие нормали нужны: 'POINT' (всё гладкое),
'FACE' (всё плоское), 'CORNER' (смешанное или custom). Нормали: `me.vertex_normals`, `me.polygon_normals`,
`me.corner_normals` (вместо удалённых `calc_normals`, `calc_normals_split`); `MeshLoop.normal` только для чтения,
custom normals — `me.normals_split_custom_set(...)` [проверено: 03, 06].

```python
# Blender 5.2.2 — [проверено] гладкость по углу без модификатора и с ним
import math
import bpy, bmesh
me = bpy.data.meshes.new("Cyl")
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=1, radius2=1, depth=2)
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("Cyl", me); bpy.context.scene.collection.objects.link(ob)
me.shade_smooth()
me.set_sharp_from_angle(angle=math.radians(30))
assert sum(d.value for d in me.attributes["sharp_edge"].data) == 64 and me.normals_domain == "CORNER"
with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
    assert bpy.ops.object.shade_auto_smooth(angle=math.radians(30)) == {"FINISHED"}
mod = ob.modifiers[-1]
assert mod.type == "NODES" and mod.node_group.name.startswith("Smooth by Angle")
mod.properties.inputs.Input_1.value = math.radians(45); ob.update_tag()    # вход модификатора 5.2
```

## 7. Модификаторы через API

### 7.1 Создание, параметры, порядок

- `m = ob.modifiers.new(name, 'SUBSURF')` добавляет в КОНЕЦ стека. Неизвестный тип → `TypeError: ObjectModifiers.new():
  error with argument 2, "type" - enum "SUBDIVISION" not found in (…)`; тип, несовместимый с объектом
  (GREASE_PENCIL_*, MESH_TO_VOLUME на меше), → `None` без исключения [проверено: 00, 10].
- Имена параметров «по памяти» у 18 частых типов в 5.2 верны, кроме `BevelModifier.use_only_vertices` (→
  `affect='VERTICES'`) и `MirrorModifier.use_x` (→ `use_axis[0]`); `BooleanModifier.solver = 'FAST'` → в 5.0 'FLOAT'
  [проверено: 03, 10]. Несуществующее свойство → `AttributeError: 'MirrorModifier' object has no attribute 'use_x'`.
- Порядок: `ob.modifiers.move(from_index, to_index)`; оператор `object.modifier_move_to_index(modifier=, index=)`;
  флаг `use_pin_to_last` [проверено: 10].
- Граф вьюпорта считает `levels` (не `render_levels`) и пропускает модификаторы с `show_viewport = False`
  [проверено: 05, 10] — это же влияет на `new_from_object` и экспорт (экспортёр glTF — у агента E, `../08-export-gltf/`).

### 7.2 Проверка перед применением

```python
# Blender 5.2.2 — [проверено] стек модификаторов и его порядок
import bpy
ob = bpy.data.objects["Cube"]
for t in ("BEVEL", "SUBSURF", "WEIGHTED_NORMAL"):
    ob.modifiers.new(t.title(), t)
b = ob.modifiers["Bevel"]; b.width = 0.05; b.segments = 3; b.limit_method = "ANGLE"; b.affect = "EDGES"
ob.modifiers.move(2, 0)
assert [m.type for m in ob.modifiers] == ["WEIGHTED_NORMAL", "BEVEL", "SUBSURF"]
assert ob.modifiers.new("gp", "GREASE_PENCIL_TINT") is None
```

### 7.3 Применение без оператора

```python
# Blender 5.2.2 — [проверено] применить первые N модификаторов без оператора
import bpy, bmesh
me = bpy.data.meshes.new("Box")
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("Box", me); bpy.context.scene.collection.objects.link(ob)
ob.data.materials.append(bpy.data.materials.new("Red"))
vg = ob.vertex_groups.new(name="all"); vg.add(list(range(8)), 1.0, "REPLACE")
ob.modifiers.new("Sub", "SUBSURF").levels = 2
tri = ob.modifiers.new("Tri", "TRIANGULATE")
tri.show_viewport = False                                  # применяем только первый
dg = bpy.context.evaluated_depsgraph_get()
new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
old = ob.data
ob.modifiers.remove(ob.modifiers["Sub"])
tri.show_viewport = True
ob.data = new_me
if old.users == 0:
    bpy.data.meshes.remove(old)
assert len(ob.data.vertices) == 98 and ob.data.materials[0].name == "Red"
assert sum(1 for v in ob.data.vertices if v.groups) == 98 and [m.name for m in ob.modifiers] == ["Tri"]
```

Shape keys при таком применении теряются; оператор `object.modifier_apply` работает в фоне с
`temp_override(object=ob)`, но отказывает для общего меша без `single_user=True` и молча отменяется при неверном имени
[проверено: 04, 10]. Готовая функция — `bpyx.apply_modifiers(ob, count=None)` [проверено: 40-bpyx-tests].

## 8. Текст и кривые

```python
# Blender 5.2.2 — [проверено] 3D-текст → меш без оператора
import bpy
cu = bpy.data.curves.new("Title", type="FONT")
cu.body = "Hello"; cu.size = 1.0; cu.extrude = 0.1; cu.bevel_depth = 0.02; cu.bevel_resolution = 2
cu.resolution_u = 4                                   # 12 по умолчанию; 4 — в 2,5 раза меньше треугольников
cu.align_x = "CENTER"; cu.align_y = "CENTER"
ob = bpy.data.objects.new("Title", cu); bpy.context.scene.collection.objects.link(ob)
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
mesh_ob = bpy.data.objects.new("TitleMesh", me); mesh_ob.matrix_world = ob.matrix_world
bpy.context.scene.collection.objects.link(mesh_ob)
bpy.data.objects.remove(ob)
assert sum(len(p.vertices) - 2 for p in me.polygons) == 1380
```

- Шрифт по умолчанию — «Bfont Regular» (`<builtin>`, кириллица есть); свой — `bpy.data.fonts.load(path,
  check_existing=True)` [проверено: 09].
- Треугольники «Hello» (size 1): плоский 209; extrude 0.1 → 848; + bevel 0.02 (resolution 2) → 3428; resolution_u 4
  вместо 12 → 1380 [проверено: 09]. Для веба `resolution_u` 3–5 и `bevel_resolution` 1–2 обычно достаточно
  [мнение: визуальная разница не мерялась].
- Кривая: `curves.new(name, 'CURVE')`, `dimensions='3D'`, `splines.new('BEZIER')` — у нового сплайна уже 1 точка
  (`bezier_points.add(n - 1)`); POLY/NURBS `points.foreach_set("co", …)` — 4 компоненты (x, y, z, w), с тремя →
  `RuntimeError: internal error setting the array`; трубка — `bevel_depth`, `bevel_resolution`, `use_fill_caps`;
  `bevel_mode` ∈ ROUND / OBJECT / PROFILE [проверено: 09].

```python
# Blender 5.2.2 — [проверено] кривая Безье и замкнутая POLY-кривая данными
import math
import numpy as np
import bpy
cv = bpy.data.curves.new("Path", "CURVE"); cv.dimensions = "3D"
sp = cv.splines.new("BEZIER")
pts = np.array([(0, 0, 0), (1, 1, 0), (2, 0, 1), (3, 1, 1)], np.float32)
sp.bezier_points.add(len(pts) - 1)
sp.bezier_points.foreach_set("co", pts.ravel())
for bp in sp.bezier_points:
    bp.handle_left_type = bp.handle_right_type = "AUTO"
cv.bevel_depth = 0.05; cv.bevel_resolution = 4; cv.use_fill_caps = True
ring = bpy.data.curves.new("Ring", "CURVE"); ring.dimensions = "3D"
sp2 = ring.splines.new("POLY"); n = 16
sp2.points.add(n - 1)
sp2.points.foreach_set("co", np.array([(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n), 0, 1)
                                       for i in range(n)], np.float32).ravel())
sp2.use_cyclic_u = True
for c in (cv, ring):
    bpy.context.scene.collection.objects.link(bpy.data.objects.new(c.name, c))
assert len(sp.bezier_points) == 4 and len(sp2.points) == 16
```

## 9. Трансформации и mathutils

### 9.1 Матрицы

`matrix_basis` — собственные location/rotation/scale; `matrix_local` — относительно родителя (с inverse);
`matrix_world` — итог (после `view_layer.update()`). Присвоение `ob.matrix_world = Matrix.LocRotScale(loc, quat,
scale)` раскладывается в location/rotation/scale. Умножение матриц и векторов — `@` (оператор `*` из 2.7x →
`TypeError: Element-wise multiplication: not supported between 'Matrix' and 'Vector' types`) [проверено: 03, 08].
mathutils-объекты, полученные из свойств (`ob.location`), — ссылки: `loc = ob.location; loc *= 2` меняет объект;
копия — `.copy()` [S9].

### 9.2 Применить трансформации данными

```python
# Blender 5.2.2 — [проверено] «Apply rotation & scale» без оператора
import math
import bpy
from mathutils import Matrix
ob = bpy.data.objects["Cube"]
ob.location = (5, 0, 0); ob.rotation_euler = (0, 0, math.radians(30)); ob.scale = (2, 1, 0.5)
bpy.context.view_layer.update()
before = [ob.matrix_world @ v.co for v in ob.data.vertices]
if ob.data.users > 1:
    ob.data = ob.data.copy()                 # не испортить другие объекты с этим мешем
mb = ob.matrix_basis.copy()
keep = Matrix.Translation(mb.to_translation())
ob.data.transform(keep.inverted() @ mb)      # вращение и масштаб — в вершины
ob.matrix_basis = keep
bpy.context.view_layer.update()
after = [ob.matrix_world @ v.co for v in ob.data.vertices]
assert all((a - b).length < 1e-5 for a, b in zip(before, after)) and tuple(ob.scale) == (1, 1, 1)
```

Детей такого объекта надо компенсировать (`child.matrix_parent_inverse = applied @ child.matrix_parent_inverse`) —
это делает `bpyx.apply_transforms` [проверено: 40-bpyx-tests]. Оператор `object.transform_apply` работает в фоне
только для выделенных объектов (иначе тихий CANCELLED) [проверено: 04].

### 9.3 Родитель, вращения

- `child.parent = ob` без inverse — ребёнок «прыгает» в систему родителя (локальный (0,0,0) → мировой location
  родителя); чтобы остаться на месте: `child.matrix_parent_inverse = ob.matrix_world.inverted()` [проверено: 05].
- `rotation_euler` действует при `rotation_mode` ∈ XYZ…ZYX; при 'XYZ' присвоенный `rotation_quaternion`
  игнорируется; **смена `rotation_mode` пересчитывает текущий поворот в новый формат и перезаписывает ранее заданное
  значение** — сначала режим, потом значение [проверено: 08].
- Углы в радианах: `math.radians(90)`; `(90, 0, 0)` принимается молча (90 рад) [проверено: 17].

### 9.4 look_at

```python
# Blender 5.2.2 — [проверено] направить камеру на точку и проверить проекцией
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
cam = bpy.data.objects["Camera"]
target = Vector((1.0, 2.0, 0.5))
cam.location = (6, -6, 4)
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()   # камера смотрит вдоль −Z
bpy.context.view_layer.update()
p = world_to_camera_view(bpy.context.scene, cam, target)
assert abs(p.x - 0.5) < 1e-3 and abs(p.y - 0.5) < 1e-3 and p.z > 0
```

С `to_track_quat('Z', 'Y')` глубина −10,06 — цель за камерой. Источники света тоже светят вдоль −Z. Альтернатива —
констрейнт `TRACK_TO` (`ob.constraints.new('TRACK_TO')`, `track_axis='TRACK_NEGATIVE_Z'`, `up_axis='UP_Y'`)
[проверено: 08; констрейнт — не проверено].

### 9.5 Размер, габариты, origin

- `ob.dimensions = (2, 1, 3)` у куба 1 м пишет scale (2, 1, 3); габариты в мире — 8 углов `bound_box`
  через `matrix_world`; поставить на пол — `ob.location.z -= world_min.z` [проверено: 08].
- Origin в центр габаритов без оператора: `c = среднее(bound_box); ob.data.transform(Matrix.Translation(-c));
  ob.matrix_world = ob.matrix_world @ Matrix.Translation(c)` — объект визуально не сдвигается [проверено: 08].
  Готовые функции: `bpyx.world_bbox`, `put_on_floor`, `center_objects`, `origin_to_center` [проверено: 40-bpyx-tests].

### 9.6 Единицы и оси

`scene.unit_settings`: system 'METRIC', scale_length 1.0, length_unit 'METERS' — 1 единица Blender = 1 м, glTF тоже
в метрах [проверено: 08]. Ось Z вверх; «вид спереди» — камера на −Y смотрит на +Y (`rotation_euler = (90°, 0, 0)`);
камера с нулевым вращением смотрит вниз (−Z) [проверено: 08]. Экспорт glTF по умолчанию переводит в Y-up
(`export_yup=True`) — подробности у агента E. Для веба удобно моделировать в реальном размере (кружка ≈ 0,1 м, телефон
≈ 0,15 м) и масштабировать на странице [мнение].

## 10. Сохранение, пути, библиотеки

### 10.1 .blend в фоне

```python
# Blender 5.2.2 — [проверено] снимок сцены, упаковка, частичная запись и append
import os, tempfile
import bpy
d = tempfile.mkdtemp()
img = bpy.data.images.new("Checker", 64, 64); img.generated_type = "COLOR_GRID"   # generated_type — свойство
img.filepath_raw = os.path.join(d, "checker.png"); img.file_format = "PNG"; img.save()
img.pack()                                               # картинка внутри .blend
snap = os.path.join(d, "snap.blend")
assert bpy.ops.wm.save_as_mainfile(filepath=snap, copy=True, compress=True) == {"FINISHED"}
assert bpy.data.filepath == ""                           # copy=True не меняет текущий файл
lib = os.path.join(d, "assets.blend")
bpy.data.libraries.write(lib, {bpy.data.materials.new("Paint"), bpy.data.objects["Cube"].data}, fake_user=True)
with bpy.data.libraries.load(lib, link=False) as (src, dst):
    dst.materials = [n for n in src.materials if n == "Paint"]
assert os.path.getsize(snap) > 0 and "Paint.001" in bpy.data.materials
```

- `save_as_mainfile(filepath, copy=False, compress=…, relative_remap=True)`: без `copy` меняется
  `bpy.data.filepath`, пути картинок перепривязываются относительно нового места (`//../tex/checker.png`)
  [проверено: 14]. Заводская настройка `preferences.filepaths.use_file_compression = True`: сетка 201×201 — 3,06 МБ
  без сжатия и 0,91 МБ со сжатием Zstd [проверено: 14].
- `bpy.data.libraries.write(path, {ID…}, fake_user=True)` — файл только с выбранными ID; `libraries.load(path,
  link=False)` — append (объекты сцены не создаются, привязать самому), `link=True` — связанные ID, `is_editable ==
  False` [проверено: 14]. Ассеты Blender: `bpy.utils.system_resource('DATAFILES')/assets/nodes/geometry_nodes_essentials.blend`
  (33 группы, «Smooth by Angle» и др.) — append этим способом работает в фоне, оператор `modifier_add_node_group` —
  нет [проверено: 19].

### 10.2 Пути

- `bpy.path.abspath("//tex/a.png")` — относительно открытого `.blend`; для связанных данных —
  `bpy.path.abspath(p, library=id.library)` [S6]. В несохранённом файле `//` указывает в никуда:
  `render.filepath = "//out.png"` → `RuntimeError: Error: Render error (No such file or directory) cannot save:
  'out_rel.png'` [проверено: 17].
- Относительный путь операторам экспорта считается от cwd процесса: `export_scene.gltf(filepath="model.glb")`
  записал файл в каталог запуска, а не рядом со скриптом [проверено: 17]. Всегда `os.path.abspath(...)`.
- `bpy.ops.file.make_paths_absolute()` / `make_paths_relative()` работают в фоне [проверено: 14]. Строки в `.blend` —
  UTF-8, пути с не-UTF-8 байтами — через `os.fsencode/fsdecode` [S6].

## 11. Скорость

| Операция (Blender 5.2.2, CPU 20 потоков) | Время |
|---|---|
| 500 кубов `bpy.ops.mesh.primitive_cube_add` в цикле | 2,44 с |
| 500 кубов data API (свой меш через bmesh) | 0,045 с |
| 500 кубов data API с общим мешем | 0,0034 с |
| `view_layer.update()` после 500 объектов | 0,0073 с |
| `shade_smooth` оператором ×500 / одним вызовом по выделению / `Mesh.shade_smooth()` ×500 | 0,26 / 0,0037 / 0,0005 с |
| сетка 250 000 вершин: `from_pydata` (списки) / `foreach_set` (numpy) | 0,29 / 0,105 с |
| сдвиг 250 000 вершин: цикл / `vertices.foreach_set("co")` / `attributes["position"]…("vector")` | 0,158 / 0,026 / 0,0003 с |
| старт `blender -b --factory-startup` / `import bpy` (PyPI) | 0,34 / 0,37 с |

[проверено: 07-speed, 18-bpy-pypi]. Правила: не вызывать операторы в цикле по объектам (один вызов по выделению или
data API); массивы — numpy float32 одним `foreach_*`; не читать `matrix_world` в цикле без нужды обновлять граф.

## 12. Шаблон устойчивого скрипта

```python
# Blender 5.2.2 — [проверено] идемпотентная сборка: очистить своё, собрать, проверить
import math
import bpy, bmesh

P = dict(size=1.2, bevel=0.03, color=(0.02, 0.06, 0.3, 1.0))          # параметры брифа
COLL = "Hero"

def ensure_clean_collection(name):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):                                   # удалить только своё
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    # только свой фоновый файл: в сцене человека поиск по имени и глобальный purge задевают его данные (I/01)
    return coll

coll = ensure_clean_collection(COLL)
me = bpy.data.meshes.new("Body")
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=P["size"]); bm.to_mesh(me); bm.free()
body = bpy.data.objects.new("Body", me); coll.objects.link(body)
body.location.z = P["size"] / 2
bev = body.modifiers.new("Bevel", "BEVEL"); bev.width = P["bevel"]; bev.segments = 3; bev.limit_method = "ANGLE"
me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(30))
mat = bpy.data.materials.get("Body") or bpy.data.materials.new("Body")
next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = P["color"]
me.materials.append(mat)
# проверка результата в конце — агент видит ошибку сразу
dg = bpy.context.evaluated_depsgraph_get()
tris = sum(len(p.vertices) - 2 for p in body.evaluated_get(dg).data.polygons)
bpy.context.view_layer.update()
zmin = min((body.matrix_world @ v.co).z for v in me.vertices)
print("REPORT", {"objects": len(coll.objects), "tris": tris, "z_min": round(zmin, 4)})
assert len(coll.objects) == 1 and abs(zmin) < 1e-6 and 100 < tris < 1000
```

Повторный запуск даёт тот же результат (сначала удаляется своё). Полный пример с камерой, светом, рендером и
экспортом на bpyx — `snippets/README.md` [проверено: 41-bpyx-example].

## Частые ошибки

| Что пишет нейросеть (по памяти) | Что в 5.2.2 | Как надо |
|---|---|---|
| `bpy.context.scene.objects.link(ob)` | `AttributeError: bpy_prop_collection: attribute "link" not found` | `bpy.context.scene.collection.objects.link(ob)` |
| `ob.select = True`, `scene.objects.active = ob` | `AttributeError` | `ob.select_set(True)`, `view_layer.objects.active = ob` |
| `bpy.context.active_object = ob` | `AttributeError: … Context property "active_object" is read-only` | `view_layer.objects.active = ob` |
| `bpy.data.objects.new("Box", "MESH")` | `TypeError: … expected a ID type, not str` | `objects.new("Box", bpy.data.meshes.new("Box"))` |
| `objects.new(...)` без `link` | тихо: объекта нет в сцене, рендере, экспорте, `.blend` | `scene.collection.objects.link(ob)` |
| `bpy.ops.mesh.primitive_cube_add(); ob = bpy.data.objects["Cube"]` | тихо: взят старый «Cube» | `ob = bpy.context.object` |
| `bpy.context.object.location.x = 5` после data API | тихо: сдвинут старый активный | работать по своей ссылке |
| `bpy.ops.object.delete(override)` | `ValueError: 1-2 args execution context is supported` | `with bpy.context.temp_override(...)` |
| `bpy.ops.object.mode_set(mode="EDIT")` в пустой сцене | `RuntimeError: … poll() Context missing active object` | сделать объект активным (он должен быть в слое вида) |
| правка в EDIT и чтение `ob.data` | тихо: старые данные | выйти из EDIT / `ob.update_from_editmode()` |
| `bm` без `bm.to_mesh(me)` | тихо: изменения потеряны | `bm.to_mesh(me); bm.free()` |
| `me.from_pydata(verts, faces)` | `TypeError: … missing 1 required positional argument: 'faces'` | `from_pydata(verts, [], faces)` |
| `me.calc_normals()` / `calc_normals_split()` | `AttributeError` (удалены в 4.0 / 4.1) | нормали актуальны сами; `me.corner_normals` |
| `me.use_auto_smooth = True` | `AttributeError` (удалено в 4.1) | `me.shade_smooth(); me.set_sharp_from_angle(...)` |
| `ob.matrix_world * v` | `TypeError: Element-wise multiplication…` | `ob.matrix_world @ v` |
| `ob.rotation_euler = (90, 0, 0)` | тихо: 90 радиан | `math.radians(90)` |
| `ob.scale = 2` / `ob.location = (0, 0)` | `TypeError` / `ValueError: … should contain 3 items, not 2` | `(2, 2, 2)` / `(0, 0, 0)` |
| `hasattr(bpy.types.Material, "use_nodes")` | тихо: False всегда | `"use_nodes" in bpy.types.Material.bl_rna.properties` |
| `export_scene.gltf(filepath="model.glb")` | тихо: файл в cwd процесса | `os.path.abspath(...)` |
| `threading.Thread(...)` с bpy | краш (документация) | `bpy.app.timers`, отдельные процессы |

[проверено: 03-version-drift, 17-llm-failure-modes]. Полный каталог с классами и правилами — `04-llm-failure-modes-and-patterns.md`.

## Чек-лист

- [ ] Все созданные объекты привязаны к коллекции сцены (`ob.name in scene.objects`)?
- [ ] Нигде не ищутся данные по имени, которое не задано явно в этом же скрипте (особенно «Cube», «Principled BSDF»)?
- [ ] Результат каждого оператора сравнивается с `{'FINISHED'}`?
- [ ] Операторам контекст передаётся через `temp_override`, а не через выделение «на удачу»?
- [ ] Перед чтением `matrix_world`/`bound_box`/`dimensions` вызван `view_layer.update()`?
- [ ] Габариты текста/кривых берутся с оригинала, а не с `evaluated_get`?
- [ ] После `mode_set`, `remove`, `*.add()` ссылки на сабданные перечитаны?
- [ ] `from_pydata` вызван с тремя списками, затем `validate()` и `update()`?
- [ ] bmesh: UV-слой создан до `create_*`, в конце `to_mesh` и `free`?
- [ ] Массовые правки — через `foreach_*` и numpy float32, без операторов в цикле?
- [ ] Цвета — 4 компоненты, линейные (hex переведён из sRGB)?
- [ ] Углы — в радианах; `rotation_mode` задан до значения?
- [ ] Перед `ob.data.transform` проверено `ob.data.users`?
- [ ] Пути абсолютные; `.blend` для снимков сохраняется с `copy=True`?
- [ ] Проверки наличия свойств — через `bl_rna.properties`, значения перечислений — по фактическому списку?
- [ ] Скрипт идемпотентный и в конце печатает статистику и проверяет её `assert`?

## Открытые вопросы и противоречия

- **Поиск сокета по identifier.** Release notes 4.0/4.1 советуют `node.outputs[identifier]`, но в 5.2.2 для Mix и
  Map Range поиск по identifier выключен в исходнике (`allow_identifier_lookup`) — подробно в `02 §2.2`.
- **Контекст таймера MCP.** Что именно видит код, пришедший через MCP в GUI (есть ли `context.area`, работают ли
  view3d-операторы без override), вживую не проверялось: MCP-мост поднимается только в Blender с окном. Разбор —
  агент C1. Гипотеза: как в фоне — `area = None`, override из `context.screen.areas` работает.
- **`update_tag()` после входов GN.** В 5.2.2 новое присвоение `mod.properties.inputs.X.value` не запускает пересчёт —
  похоже на недоработку 5.2 (в ответе SE 2024 года `object.update_tag()` звали и для старого способа). Проверять в
  5.2.3+.
- **`bound_box` у вычисленных FONT/CURVE** не учитывает extrude/bevel — не найдено ни в документации, ни в release
  notes; документация Depsgraph говорит лишь, что `evaluated.data` не-мешей не содержит модификаторов [S17].
- Лимит имени 255 байт найден экспериментом; в прочитанных release notes 4.0–5.2 (Python API) упоминания нет — версия
  изменения не установлена (прежний предел 63 байта — по памяти практиков, не проверено) [спорно].
- Стоимость `view_layer.update()` мерялась на простой сцене (500 кубов); на тяжёлых GN-сценах не мерялась.

## Источники

- [S1] Blender Foundation. Troubleshooting Errors & Crashes. Python API 5.2, 2026 — https://docs.blender.org/api/5.2/info_gotchas_crashes.html — перевыделение памяти, висячие ссылки, undo, all_objects[:]; первичный.
- [S2] Blender Foundation. Using Operators. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_operators.html — poll, poll_message_set, операторы только из редакторов; первичный.
- [S3] Blender Foundation. Internal Data & Their Python Objects. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_internal_data_and_python_objects.html — имена, view_layer.update, отложенные изменения UI; первичный.
- [S4] Blender Foundation. Modes and Mesh Access. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_meshes.html — edit mode, polygons/loop_triangles/BMFace; первичный.
- [S5] Blender Foundation. Python Threads are Not Supported. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_threading.html — потоки; первичный.
- [S6] Blender Foundation. File Paths & String Encoding. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_file_paths_and_encoding.html — `//`, abspath, UTF-8; первичный.
- [S7] Blender Foundation. Bones & Armatures. API 5.2 — https://docs.blender.org/api/5.2/info_gotchas_armatures_and_bones.html — edit/pose/bones; первичный.
- [S8] Blender Foundation. Best Practice. API 5.2 — https://docs.blender.org/api/5.2/info_best_practice.html — стиль, эффективность; первичный.
- [S9] Blender Foundation. Quickstart. API 5.2 — https://docs.blender.org/api/5.2/info_quickstart.html — bpy.data, context только чтение, mathutils-ссылки, пример слотовых действий; первичный.
- [S10] Blender Foundation. API Overview. API 5.2 — https://docs.blender.org/api/5.2/info_overview.html — регистрация, расширения, super().__init__ с 4.4; первичный.
- [S11] Blender Foundation. Tips and Tricks. API 5.2 — https://docs.blender.org/api/5.2/info_tips_and_tricks.html — exec/compile, importlib.reload, фон, --debug-wm; первичный.
- [S12] Blender Foundation. Operators (bpy.ops). API 5.2 — https://docs.blender.org/api/5.2/bpy.ops.html — возвращаемые значения, execution context, override; первичный.
- [S13] Blender Foundation. Context.temp_override. API 5.2 — https://docs.blender.org/api/5.2/bpy.types.Context.html — параметры, вложенность, logging_set; первичный.
- [S14] Blender Foundation. BMesh Module. API 5.2 — https://docs.blender.org/api/5.2/bmesh.html — жизненный цикл, слои, edit mesh; первичный.
- [S15] Blender Foundation. bpy_struct. API 5.2 — https://docs.blender.org/api/5.2/bpy.types.bpy_struct.html — keyframe_insert (keyword-only), path_resolve; первичный.
- [S16] Blender Foundation. Change Log 5.1 → 5.2. API 5.2 — https://docs.blender.org/api/5.2/change_log.html — all_ids, NodesModifier.properties и др.; первичный.
- [S17] Blender Foundation. Depsgraph. API 5.2 — https://docs.blender.org/api/5.2/bpy.types.Depsgraph.html — evaluated, to_mesh, new_from_object, object_instances; первичный.
- [S21] Blender Foundation. Blender 4.0: Python API. Release notes — https://developer.blender.org/docs/release_notes/4.0/python_api/ — удаление словаря-override, атрибуты mesh; первичный.
- [S22] Blender Foundation. Blender 4.1: Python API — https://developer.blender.org/docs/release_notes/4.1/python_api/ — auto smooth, corner_normals, foreach_set; первичный.
- [S25] Blender Foundation. Blender 4.3: Python API — https://developer.blender.org/docs/release_notes/4.3/python_api/ — ID.rename, AttributeGroupMesh; первичный.
- [S27] Blender Foundation. Blender 5.0: Python API — https://developer.blender.org/docs/release_notes/5.0/python_api/ — bpy.props вне IDProperty, float32 mathutils; первичный.
- [S29] Blender Foundation. Blender 5.2 LTS: Python API — https://developer.blender.org/docs/release_notes/5.2/python_api/ — all_ids, вложенность IDProperties, GN-модификатор; первичный.
- [S30] Blender Foundation. Blender 4.1: Modeling — https://developer.blender.org/docs/release_notes/4.1/modeling/ — замена Auto Smooth; первичный.
- [S38] BlenderMCP (ahujasid), аддон `blender_mcp.py`, протокол 7, 4673 строки (установлен у пользователя, 2026-09-16) — execute_code, describe_node_type, bpy_api_lookup; исходник, прочитаны нужные функции.
- [S39] PyPI. bpy 5.2.2 (JSON API), загружено 2026-09-15 — https://pypi.org/pypi/bpy/json — версии, requires_python ==3.13.*, колёса; первичный.
- [S43] Blender Stack Exchange, вопрос 316696 «AttributeError: 'Mesh' object has no attribute 'use_auto_smooth'», ответы 2024-04-17 (принятый) и 2024-05-29 — https://blender.stackexchange.com/q/316696 — типичный код замены auto smooth; в 5.2 не работает (эксперимент 19).
- [S44] Blender Stack Exchange, вопрос 290746 «Active object is not a selected mesh. temp_override is invalid?», 2023-04-15 — https://blender.stackexchange.com/q/290746 — join и override; уточнено экспериментом 19.
