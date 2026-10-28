# Организация сцены, имена и теги, единицы, оси, origin и соглашения Blender → JS

Волна 3 · агент I · 23.09.2026 · Blender 5.2.2 LTS (glTF-IO 5.2.40), three r186, gltfpack 1.2, gltf-transform 4.5.0 ·
эксперименты `99-raw/experiments/I/01-own-collection-vs-wipe`, `I/03-names-blender-to-js` · 7 внешних источников
(документация Blender 5.2, спецификация glTF, исходники three r186 и gltf-transform 4.5, README gltfpack) + файлы волн 1–2.

Сквозные коды ошибок: M… — каталог C1 (`../04-ai-agents-mcp/05-failure-modes-catalog.md`), B… — каталог B
(`../03-bpy-api/04-llm-failure-modes-and-patterns.md`).

## Выжимка для агента

1. **Никогда не стирай сцену в начале скрипта**: `select_all` + `delete`, `for o in bpy.data.objects: remove`,
   `bpyx.clear_scene()` в сцене человека уничтожают 4, 9 и 22 из 31 его ID; 24 из 24 скриптов «первой попытки» так
   начинались (M6.6). → §1 `[проверено]`
2. **«Моё» = помечено тегом, а не названо**: custom properties `agent`, `asset`, `part` на объектах, данных, материалах,
   коллекциях и своей сцене; искать и удалять только по тегу. → §2 `[проверено]`
3. **Коллекция и материал по имени — только в своём файле** (фон, `--factory-startup`); в сцене человека поиск по имени
   перекрасил его материал `Ceramic`, а `remove_default_scene_objects()` удалил его камеру и свет. → §1, §2 `[проверено]`
4. **Уборка — только своих ID без пользователей**, не `orphans_purge()` всего файла; сироты без fake user и так не
   пишутся в `.blend`, но до сохранения человек может их привязать обратно. → §2.3 `[проверено: I/01; документация]`
5. **Чужой объект в своей коллекции не удаляй** — выселяй в корень сцены и сообщай. → §2.4 `[проверено]`
6. **Ручную правку человека фиксируй, а не затирай**: при сборке записывай `matrix_world` и цвета частей; перед
   пересборкой сравни и перенеси отличия в `overrides` (режим «правка поверх»). → §2.5 `[проверено]`
7. **Камера, свет, мир и настройки рендера — в своей сцене превью** (`bpy.data.scenes.new`), рендер
   `render.render(write_still=True, scene=…)`; сцена человека не меняется (движок CYCLES ставили 24 из 24 наивных скриптов). → §3 `[проверено]`
8. **Структура**: `ASSET_<id>` — всё, что уйдёт в GLB; своя сцена превью с `STAGE_<id>`; вспомогательное — в
   `glTF_not_exported` или вне коллекции экспорта; экспорт `collection="ASSET_<id>"`. → §3 `[проверено]`
9. **Имя — метка для человека, тег — ключ для кода**: имена получают `.001`, переводятся при русском интерфейсе, их
   переименовывает человек. → §4 `[проверено]`
10. **Имена узлов для веба — `[a-z0-9_]`, уникальные после санитизации three**: `Mug.001` рядом с `Mug001` стал
    `Mug001_1`, `[hotspot] buy` отнял имя у `hotspot_buy` — `getObjectByName` вернул не тот узел. → §8.2 `[проверено]`
11. **Смысл для JS — custom property объекта** (`export_extras=True`): extras меша теряются после `gltfpack -ke`, свойства
    сцены не пишутся при экспорте коллекции (пишутся свойства коллекции). → §8.3 `[проверено]`
12. **Постобработка адресуемой сцены — `gltfpack -cc -kn -ke`**; `gltfpack -cc` оставил 3 имени из 13, `gltf-transform
    optimize` по умолчанию удалил все пустышки и склеил 6 мешей под одним именем. → §8.4 `[проверено]`
13. **После `-kn` меш — ребёнок именованного узла**: `getObjectByName()` даёт `Object3D`, материал — через `traverse`. → §8.4 `[проверено]`
14. **1 BU = 1 м, реальные размеры**; `scale_length` экспорт игнорирует (сцена в см → куб 100 м в three); кружка первой
    попытки была 1,4–2,2 м (M2.1). → §5 `[проверено]`
15. **Оси**: Blender Z-up → glTF Y-up, (x, y, z) → (x, z, −y); «лицо» ассета смотрит на −Y Blender = +Z glTF (к камере
    three по умолчанию). → §6 `[проверено: I/03; спецификация]`
16. **Origin = pivot в JS**: двигающаяся часть — отдельный объект с origin на оси движения (M2.4, M2.9). → §7.2 `[проверено]`
17. **Масштаб применяй без переноса**: `transform_apply(scale=True)` применяет и location, и rotation (все три флага
    по умолчанию True) — origin уезжает в ноль мира; нужен `location=False, rotation=False` или `bpyx.apply_transforms`. → §7.1 `[проверено: C1/11, bpy_probe]`
18. **Служебные узлы для JS** (`hotspot_*`, `cam_*`, `zone_*`, `collider_*`) — пустышки или меши, видимые и рендеримые в
    Blender; `hide_render` выкидывает их из экспорта пресетом E. → §8.1 `[проверено]`
19. **Родитель и ребёнок — в одной коллекции**, если включаешь `export_hierarchy_full_collections`: иначе ребёнок
    отрывается от родителя в glTF. → §8.3 `[проверено]`
20. **Анимированный узел с кириллицей или точкой в имени играет** (трек `Крышка001_(L).quaternion` привязан), но имена
    действий и объектов для кода — латиницей (H). → §8.2 `[проверено]`
21. **Сцену человека сначала осмотри** (объекты, коллекции, сцены, настройки) и запиши снимок; после своего шага сравни —
    разница только в своём. → §1.3 `[проверено: I/01; документация Blender Lab по C2]`

## 1. Чья это сцена: что агенту можно трогать

### 1.1. Два режима

| Режим | Где | Можно | Нельзя |
|---|---|---|---|
| **Свой файл** | `blender -b --factory-startup --python build.py` (`blender_run.py`), официальный MCP Blender Lab без окна | всё: сброс, `orphans_purge`, поиск по имени, настройки сцены | — |
| **Сцена человека** | mcp-for-blender с окном, открытый `.blend` пользователя | только своё по тегу; своя коллекция и своя сцена превью | стирать объекты, удалять по имени, `orphans_purge()` всего файла, `read_factory_settings`, `read_homefile`, менять движок, разрешение, камеру, мир и цветовой вид его сцены |

Режим «сцена человека» включается, если в файле есть хоть один объект без тега агента или `bpy.data.filepath` не
пустой. Работа в копии файла (`save_as_mainfile(copy=True)` до первого шага) обязательна в обоих режимах, если файл
чужой (`../04-ai-agents-mcp/04 §5.3`; эксплуатация без окна — O, `../04-ai-agents-mcp/06-headless-operations.md`).

### 1.2. Эксперимент: семь способов начать сборку в сцене человека

Сцена «пользователя» — 31 ID: настроенные Cube/Light/Camera, коллекция `Props` (Table; Vase с `hide_select`; Lamp с
`hide_viewport`; Poster скрыт «глазом»), исключённая коллекция `Reference`, вторая сцена `Layout_B`, материалы `Wood`,
`Ceramic` (имя совпадает с материалом агента), `Gold_Library` с fake user, текст `notes`; EEVEE, 1280×720, Standard.
Агент строит кружку дважды; между запусками человек повернул ручку, перекрасил кружку и положил в её коллекцию свой
`Sticker` [проверено]:

| Способ начала | Потеряно ID человека | Изменено у человека | `.001` / сироты агента после 2 запусков | Ручная правка | `Sticker` |
|---|---|---|---|---|---|
| `select_all` + `delete` (sonnet 8/8) | 4 объекта: видимые и выделяемые; скрытые, невыделяемые, исключённые и вторая сцена уцелели — и попадут в его рендер | камера сцены, движок, разрешение, мир | 7 / 5 — растут с каждым запуском | потеряна | удалён |
| то же + `outliner.orphans_purge()` (haiku 8/8) | 9 (объекты + меши, камера, свет, материал) | то же | 1 / 0 | потеряна | удалён |
| `for o in bpy.data.objects: remove` (opus 8/8) | 9 объектов **всех сцен файла** | то же | 7 / 5 | потеряна | удалён |
| `bpyx.clear_scene()` (B) | **22**: все объекты сцены со скрытыми и исключёнными, 3 коллекции, 3 материала, 6 мешей | камера сцены, разрешение | 0 / 0 | потеряна | удалён |
| протокол C1 (`remove_default_scene_objects`, `fresh_collection`, `material` по имени, `studio`, `frame_camera`, `render_setup`) | 6: его камера, свет и куб с данными | **цвет его материала `Ceramic`**, мир, камера сцены, разрешение, вид | 0 / 0 | потеряна | удалён |
| тег + своя коллекция + своя сцена превью | **0** | **нет** | 0 / 0 | найдена и названа, затёрта | выселен в корень |
| то же + «правка поверх» | **0** | **нет** | 0 / 0 | **сохранена** | выселен в корень |

Третий запуск «тег + правка поверх» без правок дал ту же сцену; рендер своей сцены превью не изменил сцену человека.
Идемпотентность «для своего» есть и у C1, и у B — разница в том, что происходит с чужим.

### 1.3. Осмотр и снимок до правок

Правило официального MCP Blender Lab (`prompts.yml`, по C2 `../04-ai-agents-mcp/02 §2.3`): «никогда не предполагай
значения — сначала осмотри сцену», «не изменяй разрушительно без подтверждения». Для агента это код: перед первым шагом
снять снимок (список ID по типам с `session_uid` и именем, настройки сцены, `scene.camera`, `scene.world`), после шага —
сравнить; всё, что изменилось вне своих тегов, — ошибка шага, откат к контрольной точке. Снимок и сравнение — функции
`snapshot()`/`diff_user()` в `99-raw/experiments/I/01-own-collection-vs-wipe/run.py`; инструменты наблюдения MCP для этого
не годятся (`get_scene_info` показывает 10 объектов, M6.9).

## 2. Своё — по тегу

### 2.1. Схема custom properties

| Ключ | На чём | Значение | Зачем |
|---|---|---|---|
| `agent` | объект, данные, материал, коллекция, сцена превью, мир превью | id агента или задачи (`"I01"`) | отличить своё от чужого |
| `asset` | то же | id ассета (`"mug"`) | несколько ассетов в одной сцене |
| `part` | объект, материал, своя коллекция | роль (`"body"`, `"handle"`, `"ceramic"`, `"stage"`) | стабильный ключ вместо имени; ключ `overrides` |
| `built_mw` | объект | 16 чисел `matrix_world` после сборки | увидеть ручную правку |
| `built_color` | материал | Base Color после сборки | увидеть ручную правку |
| `overrides` | своя коллекция | JSON ручных правок по `part` | «правка поверх» переживает пересборку и сохранение |

Custom property сохраняется в `.blend` и переживает переименование и перевод интерфейса (`../03-bpy-api/04 §4.3`);
`session_uid` живёт только в сеансе. На объектах ассета `agent`/`asset`/`part` уйдут в glTF как `extras` — это безвредно,
но служебные `built_*` лучше не экспортировать: перед экспортом удалять или экспортировать копию (`[не проверено]` —
влияние на вес GLB не мерилось; 16 чисел на узел). Свойства самой коллекции при экспорте `collection="ASSET_<id>"`
становятся extras сцены glTF (I/03) — туда же уйдёт и JSON `overrides`.

### 2.2. Помощники (проверенный код)

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/I/01-own-collection-vs-wipe; блок — I/04-doc-blocks] своё по тегу, уборка, правка поверх
import json
import bpy
from mathutils import Matrix

def tag(idb, agent, asset, part=None):
    idb["agent"], idb["asset"] = agent, asset
    if part is not None:
        idb["part"] = part
    return idb

def mine(seq, agent, asset=None, part=None):
    return [i for i in seq if i.get("agent") == agent and (asset is None or i.get("asset") == asset)
            and (part is None or i.get("part") == part)]

def own_collection(scene, agent, asset, part="asset", prefix="ASSET_"):
    coll = next(iter(mine(bpy.data.collections, agent, asset, part)), None)       # по тегу, не по имени
    if coll is None:
        coll = tag(bpy.data.collections.new(prefix + asset), agent, asset, part)
    if not any(c == coll for c in scene.collection.children):
        scene.collection.children.link(coll)
    return coll

def begin(scene, agent, asset, keep_manual=True):
    coll = own_collection(scene, agent, asset)
    moved = []
    for ob in list(coll.objects):                                                  # чужое — выселить, не удалять
        if ob.get("agent") != agent:
            if len(ob.users_collection) == 1:
                scene.collection.objects.link(ob)
            coll.objects.unlink(ob); moved.append(ob.name)
    over = json.loads(coll.get("overrides", "{}")) if keep_manual else {}
    for ob in mine(bpy.data.objects, agent, asset):                                # ручные правки → overrides
        cur = [x for row in ob.matrix_world for x in row]
        if keep_manual and ob.get("built_mw") and max(abs(a - b) for a, b in zip(cur, ob["built_mw"])) > 1e-6:
            over.setdefault(ob["part"], {})["matrix_world"] = cur
        bpy.data.objects.remove(ob, do_unlink=True)                                # удалить только своё
    for kind in ("meshes", "curves", "cameras", "lights"):
        seq = getattr(bpy.data, kind)
        for idb in mine(seq, agent, asset):
            if idb.users == 0:
                seq.remove(idb)                                                    # свои сироты, не orphans_purge()
    return coll, over, moved

def finish(coll, over, agent, asset):
    for ob in mine(bpy.data.objects, agent, asset):
        mw = over.get(ob.get("part"), {}).get("matrix_world")
        if mw:
            ob.matrix_world = Matrix([mw[i * 4:i * 4 + 4] for i in range(4)])
    coll["overrides"] = json.dumps(over)
    bpy.context.view_layer.update()
    for ob in mine(bpy.data.objects, agent, asset):
        ob["built_mw"] = [x for row in ob.matrix_world for x in row]

def build(scene, P):
    coll, over, moved = begin(scene, "I01", P["asset"])
    for part, loc in (("body", (0, 0, 0.05)), ("handle", (0.05, 0, 0.05))):
        me = tag(bpy.data.meshes.new(f"{P['asset']}_{part}"), "I01", P["asset"], part)
        me.from_pydata([(0, 0, 0), (0.01, 0, 0), (0, 0.01, 0)], [], [(0, 1, 2)])
        ob = tag(bpy.data.objects.new(f"{P['asset']}_{part}", me), "I01", P["asset"], part)
        ob.location = loc; coll.objects.link(ob)
    finish(coll, over, "I01", P["asset"])
    return coll, moved

scene = bpy.context.scene
user_objects = {o.name for o in scene.objects}                     # заводские Cube, Light, Camera — «чужие»
build(scene, {"asset": "mug"})
bpy.data.objects["mug_handle"].rotation_euler.z += 0.4            # человек повернул ручку
bpy.context.view_layer.update()
coll, moved = build(scene, {"asset": "mug"})                      # пересборка сохраняет правку
assert abs(bpy.data.objects["mug_handle"].rotation_euler.z - 0.4) < 1e-5
assert user_objects <= {o.name for o in scene.objects} and len(coll.objects) == 2
assert not [i.name for i in bpy.data.meshes if i.name.endswith(".001")]
```

Полная версия (цвет материала в `overrides`, материалы по тегу и роли, своя сцена превью) —
`99-raw/experiments/I/01-own-collection-vs-wipe/agent_scene.py`.

### 2.3. Уборка и сироты

- Blender не записывает в `.blend` ID без пользователей, кроме защищённых fake user [S1]: в I/01 материал `Draft` и
  картинка `moodboard` исчезли после сохранения и открытия, текст из `texts.new()` в 5.2.2 создаётся с
  `use_fake_user=True` и остаётся [проверено].
- Значит, глобальный `orphans_purge()` в сеансе человека удаляет то, что он отвязал и ещё может привязать до
  сохранения (и снимает undo по этим данным); в своём файле — нормальный шаг гигиены (`02 §4`).
- Свои данные без пользователей удаляй по тегу сразу после удаления своих объектов — тогда `.001` не копятся (в I/01 у
  стирания без уборки после двух запусков 7 дублей и 5 сирот, у способа с тегом — 0 и 0).

### 2.4. Чужое в своей коллекции

Человек кладёт объект в коллекцию ассета руками (в I/01 — `Sticker`). Удаление по «всё в моей коллекции» уничтожает
его (`fresh_collection()` C1 удаляет `all_objects` коллекции); экспорт по коллекции унесёт его в GLB. Правило: объект без
своего тега выселить в корень сцены (или в коллекцию, откуда он пришёл), в отчёте шага назвать его имя.

### 2.5. «Правка поверх»: ручные правки в `P`

Открытый вопрос C1 (`../04-ai-agents-mcp/04`, «Открытые вопросы»): пересборка «с нуля» стирает правки человека. Решение
[проверено]: при сборке записать `built_mw` (и `built_color`), перед пересборкой сравнить; отличия — в `overrides`
по ключу `part`, хранить в custom property своей коллекции и в паспорте `P` рядом со скриптом; после сборки применить.
Ограничения `[не проверено]`: правки топологии (edit mode), новые модификаторы и смена материала слота так не ловятся —
для них отчёт «часть изменена вручную: <part>» и вопрос человеку; при изменении параметра `P`, от которого зависит часть
с override, спросить, оставлять ли override.

## 3. Коллекции, сцены, слои вида

| Что | Где | Экспорт | Почему |
|---|---|---|---|
| ассет для сайта | коллекция `ASSET_<id>` (тег `part="asset"`) | `collection="ASSET_<id>"` | только она уходит в GLB (E `../08-export-gltf/01 §3.3`) |
| камера, свет, мир, ловец теней, циклорама | своя сцена `PREVIEW_<id>` + коллекция `STAGE_<id>` | нет | не меняют сцену человека; настройки рендера — свои |
| заготовки, резаки булевых, копии до применения | `glTF_not_exported` или своя исключённая коллекция | никогда | E/10: коллекция с этим именем не экспортируется |
| референсы (картинки, чужие ассеты) | `REF_<id>`, исключена из слоя вида | нет | не мешают кадру |
| клиенту на телефон и в AR | отдельные коллекции/экспорт (F1 `../09-web-runtime/06 §2.4`) | отдельно | другой набор сжатия |

- Своя сцена: `bpy.data.scenes.new("PREVIEW_mug")`, в неё `collection.children.link(ASSET_mug)` — объекты общие
  с коллекцией в сцене человека, камера `pv.camera`, мир `pv.world`, движок и разрешение `pv.render` свои;
  `bpy.ops.render.render(write_still=True, scene=pv.name)` в фоне → `{'FINISHED'}` [проверено].
- Что наивные скрипты меняют в сцене человека (24 из 24 C1/11): `scene.render.engine = 'CYCLES'`, разрешение,
  `scene.camera`, цвет и сила фона мира, вид (AgX/Standard), сэмплы — всё это настройки сцены, а не ассета.
- Коллекция из `bpy.data.collections.new()` без `children.link` невидима; `layer_collection.exclude` действует после
  `view_layer.update()` (B5.2, B5.3; `../03-bpy-api/01 §3.2`).
- `ob.hide_set()` — только вьюпорт текущего слоя вида; скрытые так объекты экспорт по умолчанию уносит, пресет E с
  `use_visible=True` — нет (E `01 §3.3`); оператор `select_all` их не видит — стирание оператором их оставляет.

## 4. Имена: метка для человека, тег для кода

| Факт (Blender 5.2.2) | Следствие для агента | Доказательство |
|---|---|---|
| коллизия имени → новому ID суффикс `.001` | повтор неидемпотентного шага даёт `Ceramic.001`, `Mug.001` (M6.5) | B/05; I/01: 7 дублей за 2 запуска |
| `ID.rename(name, mode="ALWAYS")` отбирает имя у другого ID | не отбирать имя у чужого ID | B `01 §2.4` |
| при русском интерфейсе и `use_translate_new_dataname` куб — «Куб», нода — «Принципиальный BSDF» | `objects["Cube"]`, `nodes["Principled BSDF"]` → KeyError (B4.5) | B/15 |
| предел имени 255 байт UTF-8 (кириллица — 127 символов) | длинные «описательные» имена обрезаются | B/05 |
| имена узлов в glTF отсортированы как в Outliner, не по порядку создания | не полагаться на порядок узлов в JS | E/11 |

Правило: имя задавай явно при создании (`bpy.data.objects.new("mug_body", me)`) — это метка для человека и имя узла в
glTF; для кода — тег. Имя, которое прочитает JS, — по §8.2.

## 5. Единицы и реальные размеры

- 1 единица Blender = 1 м (`unit_settings.system='METRIC'`, `scale_length=1.0`), glTF — метры [S3]; экспорт
  **игнорирует** `scale_length`: сцена в сантиметрах (`scale_length=0.01`) даёт в three куб 100 м (E/10, `../08-export-gltf/01 §4.9`).
- `length_unit` меняет только отображение в интерфейсе.
- Строить в реальных размерах предмета и масштабировать на странице: кружка Ø 80–85 × 95 мм, смартфон 71,5 × 147 × 7,8 мм,
  ноутбук 13" 304 × 212 мм, комната 3 × 3 м (паспорта C1 `../04-ai-agents-mcp/05 §11`). Модели по памяти ошибаются в ×10–25
  (кружка 1,4–2,2 м у трёх моделей, M2.1) — размеры из паспорта `P`, проверка утверждением «габарит ±5 %» (C1 `04 §6.4`).
- Размеры в метрах держат согласованными фаски, толщины, мощность света (`P = π·d²·E`, D2) и физику в JS.

## 6. Оси и «лицо» ассета

| | Blender | glTF / three |
|---|---|---|
| вверх | +Z | +Y |
| «вперёд», лицо ассета | −Y (вид спереди: камера на −Y смотрит на +Y) | +Z (камера three по умолчанию на +Z смотрит на −Z) |
| преобразование точки | (x, y, z) | (x, z, −y) |
| камера и свет светят вдоль | −Z локальной оси | −Z локальной оси |

- glTF: правая система, +Y вверх, +Z вперёд, лицо ассета смотрит на +Z; метры и радианы [S3]; экспортёр с `export_yup=True`
  делает это сам (E/10); Z-up против Y-up как частая причина «лежащей» модели — в докладах [V:Inqt1fZ3QTI 30:06;
  V:ji6q_P-QY_E 23:15] (через W13). Проверено на I/03: пустышка `cam_start` в Blender (0,6; −0,6; 0,4) → в three (0,6; 0,4; 0,6).
- Правило: «лицо» продукта (экран телефона, логотип) — к −Y в Blender; тогда в three оно смотрит на стандартную камеру
  без поворота модели. Точки и пути для JS пишутся в осях three `[x, z, −y]` (F1 `../09-web-runtime/06 §1`).

## 7. Origin, pivot, трансформации

### 7.1. Применить масштаб, не сдвинув pivot

У `bpy.ops.object.transform_apply` все три флага `location`, `rotation`, `scale` по умолчанию `True` (`bpy_probe.py op
object.transform_apply`, 5.2.2); вызов `transform_apply(scale=True)` применяет и перенос — origin всех частей уезжает в
ноль мира (sonnet 7/8 в C1/11, M1.9); без выделения в фоне оператор тихо `{'CANCELLED'}` (B4.2).

```python
# Blender 5.2.2 — [проверено] масштаб в вершины, pivot на месте
import bpy
ob = bpy.data.objects["Cube"]
ob.location, ob.scale = (1.0, 2.0, 0.5), (2.0, 2.0, 2.0)
bpy.context.view_layer.update()
ov = dict(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob])
with bpy.context.temp_override(**ov):
    assert bpy.ops.object.transform_apply(location=False, rotation=False, scale=True) == {"FINISHED"}
assert tuple(ob.location) == (1.0, 2.0, 0.5) and tuple(ob.scale) == (1.0, 1.0, 1.0)
with bpy.context.temp_override(**ov):
    ob.scale = (2.0, 2.0, 2.0)
    bpy.ops.object.transform_apply(scale=True)          # антипример: location тоже применён
assert tuple(ob.location) == (0.0, 0.0, 0.0)             # pivot уехал в ноль мира
```

Без оператора и выделения — `bpyx.apply_transforms(ob, location=False, rotation=True, scale=True)` (компенсирует детей,
копирует общий меш; `../03-bpy-api/01 §9.2`).

### 7.2. Pivot для JS

- Origin объекта = точка вращения узла в three: геометрия в 5 м от origin вращается вокруг далёкой точки (E/10).
- Двигающаяся часть (крышка, дверца, экран ноутбука, стрелка) — **отдельный объект** с origin на оси движения, родитель —
  корпус (C1 `04 §5.2`, D1 `../05-modeling/04 §1.2`, `05 §4.3`); поворот сборки — через общий pivot (M2.4).
- Неприменённый масштаб экспортёр переносит в `scale` узла, отрицательный — в scale −1 + поворот 180° (E/10): вид верный,
  но физика, анимация масштаба и `Box3` в JS считают от узла — применять до экспорта (`preflight()` E: `UNAPPLIED_SCALE`,
  `NEGATIVE_SCALE`, `ORIGIN_FAR`).
- Родитель без inverse: ребёнок «прыгает» в систему родителя; чтобы остался на месте — `child.matrix_parent_inverse =
  parent.matrix_world.inverted()` после `view_layer.update()` (`../03-bpy-api/01 §9.3`); экспорт `matrix_parent_inverse`
  переносит корректно (E/10).

## 8. Соглашения Blender → JS

### 8.1. Таблица договорённостей (с D1, F1/F2, H, E)

| Что | Blender | glTF / three | Кто договорился |
|---|---|---|---|
| имя узла, клипа, материала для кода | `латиница_через_подчёркивание`: `hero_body`, `btn_buy`; уникально после санитизации | то же имя в `Object3D.name`, `AnimationClip.name` | E `01 §10`, F2 `03 §7.1`, H `07/01 §5.4`, I/03 |
| метка на странице | пустышка `hotspot_<id>` + custom property `label`, `href`, `order` | `Object3D` с `userData` | F1 `06 §1.5`, F2 `03 §7.1` |
| точка и цель камеры | пустышка `cam_<id>` (+ `fov`) | `Object3D` | F2, A `05 §3.10` |
| зона кадра, отсечение, сон физики | пустышка `zone_<id>` (Circle, `radius`) | `Object3D` | F2 (Bruno Simon) |
| упрощённая форма для рейкаста или физики | меш `collider_<id>`, `display_type='WIRE'`, **рендеримый** | `Mesh`, в JS `visible = false` | F2, I/03 |
| двигающаяся часть | отдельный объект, origin на оси | узел со своим pivot | C1, D1, E/10 |
| клип | одно действие = один клип; имя латиницей; второй клип — NLA-дорожка с одной полосой | `AnimationClip.findByName` | H `07/01` |
| путь камеры | кривая `cam_path`, плотность — `resolution_u` | JSON `[x, z, −y]` → `CatmullRomCurve3` | D1 `05/03`, H `07/04`, F2 `03 §5` |
| данные уровня страницы | custom property **коллекции ассета** (при `collection=`) или сцены (при экспорте сцены) | `gltf.scene.userData` | I/03 |
| цвет бренда | hex в custom property + материал | `material.userData` | D2, I/03 |
| имена материалов и мешей | латиница, как у узлов: в JS это ключи доступа (`nodes`, `materials` у gltfjsx/`useGLTF`) | `material.name`, `mesh.name` | [V:KTPdNUGwIGc ≈36:05; V:ji6q_P-QY_E 17:38–20:14] через W13 |
| свой атрибут для шейдера | имя с `_` (`_wave`), без строковых типов; `export_attributes=True` | `geometry.attributes._wave`; gltfpack выбрасывает (E/28) — только gltf-transform | E/06, E/28; [V:KTPdNUGwIGc ≈36:05] |

### 8.2. Имена: что делает three r186

GLTFLoader r186: `createUniqueName()` прогоняет имя через `PropertyBinding.sanitizeNodeName` (пробел → `_`, удаляются
`[ ] . : /`) и при повторе дописывает `_1`, `_2`; исходное имя пишет в `userData.name` при любом `export_extras` [S4]
[проверено: I/03 — `userData.name` есть и при `export_extras=False`].

| Имя в Blender | Имя в three (сырой GLB) | Проблема |
|---|---|---|
| `hero_body` | `hero_body` | нет |
| `Кружка` | `Кружка` | нет, но ключ для кода — латиница |
| `Handle (L)` | `Handle_(L)` | круглые скобки остаются |
| `btn:main/cta` | `btnmaincta` | двоеточие и косая удалены |
| `Mug.001` при наличии `Mug001` | `Mug001_1` | коллизия после санитизации |
| `[hotspot] buy` и `hotspot_buy` | `hotspot_buy` и `hotspot_buy_1` | **правильный узел потерял имя**: `getObjectByName('hotspot_buy')` вернул дубль |
| `Крышка.001 (L)` + действие «Открыть крышку» | `Крышка001_(L)`, клип «Открыть крышку» | трек привязан (поворот 45° в t = 0,5) |

[проверено]. `preflight()` E помечает санитизацию (`NAME_SANITIZED`, INFO),
но не коллизии после неё — проверку уникальности даёт код ниже.

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/I/03-names-blender-to-js; блок — I/04-doc-blocks] имена для JS: коллизии после санитизации
import re
import bpy

SANITIZE = re.compile(r"[\[\].:/]")
GOOD = re.compile(r"^[a-z][a-z0-9_]*$")

def three_name(name):
    """Как PropertyBinding.sanitizeNodeName three r186: пробельные → '_', удалить [ ] . : /"""
    return SANITIZE.sub("", re.sub(r"\s", "_", name))

def names_for_js(objects):
    issues, seen = [], {}
    for ob in objects:
        t = three_name(ob.name)
        if not GOOD.match(ob.name):
            issues.append(("WARN", "NAME_NOT_SNAKE", ob.name, f"в three: {t!r}"))
        if t in seen:
            issues.append(("ERROR", "NAME_COLLISION", ob.name, f"и {seen[t]!r} → оба {t!r}; один получит суффикс _1"))
        seen.setdefault(t, ob.name)
        if ob.name.startswith("collider_") and ob.hide_render:
            issues.append(("ERROR", "COLLIDER_NOT_EXPORTED", ob.name, "hide_render: пресет E (use_renderable) его выбросит"))
        if ob.type == "MESH" and [k for k in ob.data.keys() if not k.startswith("_")]:
            issues.append(("WARN", "EXTRAS_ON_MESH", ob.name, "custom property меша теряется после gltfpack -ke — перенести на объект"))
    return issues

bpy.ops.wm.read_factory_settings(use_empty=True)
for n in ("Mug.001", "Mug001", "hotspot_buy", "[hotspot] buy", "hero_body", "collider_body"):
    ob = bpy.data.objects.new(n, bpy.data.meshes.new(n))
    bpy.context.scene.collection.objects.link(ob)
bpy.data.objects["collider_body"].hide_render = True
bpy.data.objects["hero_body"].data["lod"] = 0
codes = sorted((c, n) for _, c, n, _ in names_for_js(sorted(bpy.context.scene.objects, key=lambda o: o.name)))
assert ("NAME_COLLISION", "Mug001") in codes and ("COLLIDER_NOT_EXPORTED", "collider_body") in codes
assert ("EXTRAS_ON_MESH", "hero_body") in codes and ("NAME_COLLISION", "hotspot_buy") in codes
print(codes)
```

### 8.3. Данные: extras, сцена, коллекции

| Где custom property | Сырой GLB (пресет E) | `gltfpack -cc -kn -ke` | Правило |
|---|---|---|---|
| объект (str, float, bool, список, dict) | `node.extras` → `userData`, типы сохранены | сохранены | смысл — сюда |
| данные меша | сливаются в `userData` меша | **потеряны** (`-ke` хранит extras материалов, узлов, примитивов и сцен [S5]) | не использовать |
| материал | `material.userData` | сохранены | цвет бренда, id варианта |
| сцена | `gltf.scene.userData` — только при экспорте всей сцены | — | при `collection=` не пишется |
| коллекция | при `collection=` → extras сцены glTF [S2] | не проверено | данные страницы при экспорте коллекции |

- `collection="WEB"` даёт сцене glTF имя коллекции и extras из свойств коллекции; свойства сцены Blender не пишутся
  [проверено: I/03 `scene_extras_check.py`; руководство 5.2 S2].
- `export_hierarchy_full_collections=True` превращает коллекции в узлы (`WEB_1`, `Hotspots`) и кладёт объект «в первую
  коллекцию, где он найден» [S2]: пустышка `hotspot_buy`, ребёнок `hero_body` из другой коллекции, стала ребёнком
  `Hotspots` и больше не следует за `hero_body` [проверено]. По умолчанию выключено — не включать без нужды.

### 8.4. Постобработка и адресуемые узлы

| Команда | Имён из 13 | Пустышки | Extras | Что ещё |
|---|---|---|---|---|
| сырой GLB (пресет E `anim_trs`) | 13 | есть | есть | 11,7 КБ |
| `gltfpack -cc` | 3 (два инстанса и анимированный) | удалены | удалены | 5,3 КБ |
| `gltfpack -cc -kn -ke` | 13 | есть | объекта и материала есть, меша — нет | меш → `Object3D` + ребёнок `mesh_N`; 8,4 КБ |
| `gltf-transform optimize` (умолчание) | 3 | удалены (prune, `keepLeaves: false` [S6]) | у уцелевших есть | 6 мешей без материала склеены в `btnmaincta` (144 вершины) |

[проверено: I/03; совпадает с E/28 и E/24]. Пресеты E: постобработка `static_hero` (`optimize` по умолчанию) и
`mobile_light` (`gltfpack -cc -tc -ts 0.5` без `-kn -ke`) для ассета с пустышками и extras не годятся — добавлять
`-kn -ke` (для KTX2-варианта — `gltfpack -cc -tc -kn -ke`, не проверено вместе с `-tc`).

Поиск в JS после `-kn` (меш — ребёнок узла с именем; F2 `../09-web-runtime/02` §3, I/03):

```js
// three r186 — [проверено] узел по имени из Blender, меш, метки, коллайдеры
export function nodeByBlenderName(root, blenderName) {
  let hit = null;
  root.traverse((o) => { if (!hit && o.userData.name === blenderName) hit = o; });   // userData.name = имя в Blender
  return hit;
}
export function meshOf(node) {
  let mesh = null;
  node.traverse((o) => { if (!mesh && o.isMesh) mesh = o; });                     // после gltfpack -kn меш — ребёнок
  return mesh;
}
export function markers(root, prefix = 'hotspot_') {
  const out = [];
  root.traverse((o) => { if ((o.userData.name || '').startsWith(prefix)) out.push({ name: o.userData.name, data: o.userData, object: o }); });
  return out;
}
export function hideColliders(root) {
  root.traverse((o) => { if ((o.userData.name || '').startsWith('collider_')) o.visible = false; });
}
```

## Частые ошибки

1. **«Сначала очистим сцену»** (`select_all` + `delete`, удаление всех `bpy.data.objects`, `orphans_purge`) — M6.6; модели
   делают это в 24 из 24 первых попыток; в сцене человека — потеря его работы [I/01].
2. **`clear_scene()` как «безопасная» очистка** — безопасна только для настроек интерфейса; удаляет всю сцену [I/01].
3. **Поиск своего по имени**: `collections.get("STAGE")`, `materials.get("Ceramic") or new(...)` — в чужой сцене берёт
   чужое и перекрашивает; в своей — `.001` при повторах [I/01, C1/05].
4. **Удаление «по умолчанию» Camera/Light/Cube по имени** — у человека это его камера и свет [I/01].
5. **Настройки рендера в сцене человека** (движок, разрешение, `scene.camera`, мир, вид) [I/01, C1/11].
6. **`transform_apply(scale=True)`** — pivot в ноль мира (M1.9) [C1/11].
7. **Точка в имени для JS** (`Mug.001`, `v1.2`) — коллизии после санитизации, `getObjectByName` находит не тот узел [I/03].
8. **Коллайдер «спрятан» `hide_render`** — не доезжает до GLB [I/03].
9. **Смысл в имени, а не в extras** (`hotspot_buy_Купить`) — имя санитизируется, текст для страницы — в custom property [E/11, F2].
10. **`optimize` по умолчанию для сцены с метками** — пустышки удалены, меши склеены [I/03, E/24].
11. **Сцена в сантиметрах** (`scale_length=0.01`) — в three в 100 раз больше [E/10].
12. **Лицо ассета к +Y Blender** — в three смотрит от камеры [спецификация S3; I/03].

## Чек-лист

- [ ] До первого шага снят снимок сцены человека; после шага изменилось только помеченное тегом?
- [ ] Ни одной операции «стереть сцену», `orphans_purge()` всего файла, удаления по имени в чужом файле?
- [ ] У всех своих ID есть `agent`, `asset`, `part`; своя коллекция и материалы найдены по тегу?
- [ ] Камера, свет, мир, движок и разрешение — в своей сцене превью, не в сцене человека?
- [ ] Ручные правки человека найдены и перенесены в `overrides` (или названы в отчёте)?
- [ ] Размеры частей в метрах совпадают с паспортом ±5 %; `scale_length == 1`?
- [ ] Лицо ассета — к −Y Blender?
- [ ] Масштаб применён без переноса origin; у двигающихся частей origin на оси?
- [ ] Имена узлов `[a-z0-9_]`, `names_for_js()` без `ERROR`?
- [ ] Смысл для JS — в custom properties объектов (не меша), `export_extras=True`?
- [ ] Постобработка `gltfpack -cc -kn -ke`; в `gltf_web_inspect.py` все `hotspot_*`/`cam_*`/`collider_*` на месте?

## Открытые вопросы и противоречия

- **Материалы по имени** — C1 `04` выжимка п. 10 («материалы — по имени с переиспользованием») против I/01: верно для
  своего файла, в сцене человека перекрашивает его материал. Предложение для синтеза: «по имени — в своём файле, по тегу —
  в чужом».
- **`bpyx.clear_scene()`** — B `01 §2.5` называет его способом «удалить объекты своей коллекции и сирот» для MCP-сеанса;
  код удаляет все объекты сцены (I/01: 22 из 31 ID) — нужна правка текста B и докстринга (решает оркестратор).
- **E `08/01 §4.9`** советует `bpy.ops.object.transform_apply(scale=True)` перед экспортом — это переносит и location
  (флаги по умолчанию True); нужно `location=False, rotation=False` (C1 M1.9, D1 `../05-modeling/05 §4.2`, I §7.1).
- **Служебные `built_*` в extras** — не мерили влияние на вес и не пробовали удалять перед экспортом (`[не проверено]`).
- **`gltf-transform` с сохранением пустышек** (`prune` с `keepLeaves`/`keepExtras` из CLI) — не проверено; сейчас для
  адресуемых сцен проверен только `gltfpack -cc -kn -ke`.
- **Режим «правка поверх»** ловит только трансформации и цвет; правки топологии и модификаторов — вопрос человеку.

## Источники

- [S1] Blender Foundation. Blender Manual 5.2 — Data-Blocks: Life Time, Protected (fake user). 2026.
  https://docs.blender.org/manual/en/5.2/files/data_blocks.html — «zero user data-blocks are not saved»; официально, 5.2.
- [S2] Blender Foundation / Khronos. Blender Manual 5.2 — glTF 2.0 add-on (Include, Custom Properties, Full Collection
  Hierarchy, Collection Exporters). 2026. https://docs.blender.org/manual/en/5.2/addons/import_export/scene_gltf2.html —
  официально, 5.2 (glTF-IO 5.2.x); из кэша `99-raw/cache`.
- [S3] Khronos Group. glTF 2.0 Specification §3.4 Coordinate System and Units. https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
  — +Y вверх, +Z вперёд, лицо к +Z, метры, радианы; первоисточник.
- [S4] three.js r186. `examples/jsm/loaders/GLTFLoader.js` (`createUniqueName`, `userData.name`, `assignExtrasToUserData`).
  https://raw.githubusercontent.com/mrdoob/three.js/r186/examples/jsm/loaders/GLTFLoader.js — исходник, тег r186.
- [S5] A. Kapoulkine. gltfpack README (meshoptimizer 1.2): `-kn`, `-km`, `-ke`; «extras in materials, nodes, primitives
  and scenes». https://github.com/zeux/meshoptimizer/blob/master/gltf/README.md — первоисточник; из кэша.
- [S6] Don McCurdy. glTF Transform 4.5.0, `@gltf-transform/functions` — `prune()` по умолчанию `keepLeaves: false`,
  `keepExtras: false` (исходник в `99-raw/tools/node/node_modules`). https://gltf-transform.dev/modules/functions/functions/prune
- Видео (через дайджесты W13 `../91-videos/digests/`): [V:KTPdNUGwIGc] J. Duroure, The Complete glTF Asset Creation Pipeline;
  [V:ji6q_P-QY_E] S. Vieira, From Blender to the Web (Nordic.js 2022); [V:Inqt1fZ3QTI] D. Deckert, The Optimization Iceberg
  (BCon 2025).
- [S7] Blender Lab. `prompts.yml` официального MCP-сервера (по C2 `../04-ai-agents-mcp/02 §2.3`, S4 там): осмотр сцены,
  без разрушительных правок без подтверждения, ссылки вместо имён.
- Файлы базы: B `../03-bpy-api/01 §2.4–2.7, §3, §9, §10`, `04 §4.1–4.3`; C1 `../04-ai-agents-mcp/04 §5`, `05` M1.9, M2.1,
  M2.4, M2.9, M6.5, M6.6, M6.9; D1 `../05-modeling/04 §1.2`, `05 §4.2–4.3`; E `../08-export-gltf/01 §3, §4.9, §7.3, §10`, эксперименты E/10, E/11, E/24, E/28;
  F1 `../09-web-runtime/06 §1`; F2 `../09-web-runtime/03 §5, §7.1`; H `../07-animation/01 §5`.
