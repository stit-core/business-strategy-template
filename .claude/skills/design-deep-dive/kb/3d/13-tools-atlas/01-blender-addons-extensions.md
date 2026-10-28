# Аддоны и расширения Blender 5.2.2: ядро, extensions.blender.org, сторонние, ИИ-мосты

Волна 3, агент L, 23.09.2026. Источников: 14 (5 живых веб-запросов + 9 файлов базы разделами). Экспериментов: 2
(`99-raw/experiments/L/00-atlas-collect`, `L/01-addon-checks`). Версии: Blender 5.2.2 LTS (hash `d13f752e3b9c`,
build 2026-09-15). Машиночитаемая версия всех записей — `13-tools-atlas/atlas.tsv` (категории `blender-core`,
`blender-extension`, `blender-addon`, `blender-addon-ai`).

## Выжимка для агента

1. **В `addons_core` Blender 5.2.2 всего 13 модулей** — это весь список «встроенного», без исключений: `bl_pkg, cycles,
   hydra_storm, io_anim_bvh, io_curve_svg, io_mesh_uv_layout, io_scene_fbx, io_scene_gltf2, node_wrangler, pose_library,
   rigify, ui_translate, viewport_vr_preview`. Проверено `addon_utils.paths()` → §1 [проверено].
2. **Из них по умолчанию включены только 8**: `bl_pkg, cycles, io_anim_bvh, io_curve_svg, io_mesh_uv_layout, io_scene_fbx,
   io_scene_gltf2, pose_library`. Node Wrangler, Rigify, Hydra Storm, VR Scene Inspection, UI-переводы — выключены,
   включать явно в `build()`, если нужны → §1 [проверено].
3. **LoopTools в 5.2 частично встроены**: Flatten, Circle, Space — родные C-операторы `mesh.flatten`, `mesh.circularize`, `mesh.space_edge_loops_evenly` [проверено]; Relax, Curve, GStretch, Bridge — только в расширении `looptools` (GPL-2.0-or-later, v4.7.7). Целиком в расширениях — Bool
   Tool, F2, Bsurfaces. Наивная проверка `hasattr(bpy.ops.mesh, "looptools_circle")` лжёт (True для несуществующих
   операторов) — проверять `bpy.ops.mesh.<имя>.get_rna_type()` в `try/except KeyError` (`hasattr(bpy.types, "MESH_OT_…")` видит только Python-операторы и для C-операторов лжёт «нет») → §2, «Частые ошибки»
   [проверено].
4. **Платформа extensions.blender.org требует GPL-совместимую лицензию** для листинга — платных аддонов на ней нет;
   Hard Ops, BoxCutter, MESHmachine, RetopoFlow, BlenderKit, MACHIN3tools, fSpy, Quick Baker, Render Raw туда не попадают
   и распространяются отдельно (GitHub, Blender Market/Superhive, сайты авторов) → §3 [проверено].
5. **API `extensions.blender.org/api/v1/extensions/`** отдаёт весь каталог (1454 записи на 23.09.2026) одним ответом без
   рабочей серверной пагинации или поиска — фильтровать по `name`/`id` локально, кэшировать → §2 [проверено].
6. `blender_manifest.toml` — признак современного аддона-расширения (обязателен с 4.2); паковать командой
   `blender -c extension build-package` (проверяет манифест, не просто zip) — не `zip -r` вручную → §2
   [V:GP53gDHGiIQ 30:52, ≈36:10].
7. **RetopoFlow**: код GPL-3.0-or-later (в файле `RetopoFlow.LICENSE`, не `LICENSE` — поэтому GitHub Api показывает
   `license: null`, это не значит «без лицензии»), но кисти/иконки — проприетарны CG Cookie; использовать код можно
   бесплатно, покупка ($85.99/$151.99) — просьба разработчика, не юридическое требование → §3 [проверено].
8. **MPFB2** (установлен у пользователя, версия 2.0.17) — лицензия на GitHub помечена `NOASSERTION` (детектор не смог
   классифицировать файл лицензии) — не заявлять как «MIT» или «GPL» без ручной проверки текста → §3 [проверено].
9. Встроенный экспортёр glTF — «Khronos glTF Blender I/O v5.2.40» (не путать с версией Blender) — апстрим-репозиторий
   `KhronosGroup/glTF-Blender-IO` (Apache-2.0, 1663★), туда же официальная hook-система расширения поведения без форка
   → §1, §5 [V:FIHu6-3rjX4 W50:58].
10. Мост «MCP for Blender» — это **аддон в Blender** (`blender_mcp.py`, версия 1.7, протокол 9) + внешний сервер
    `mcp-for-blender` 2.0.3 (MIT). Аддон работает только в Blender с окном — сервер и его 3 CVE разобраны в
    `13-tools-atlas/03-pipeline-cli-services.md §3`, здесь — только сторона аддона → §5.
11. Аддоны генераторов на Linux без CUDA практически бесполезны: Meshy Bridge и Tripo DCC Bridge — только Windows/Mac;
    StableGen, Dream Textures, meshgen — нужен CUDA/Apple Silicon, которого нет на машине базы → §4.
12. Hunyuan3D-2 аддон **не включать** в конвейер: лицензия Tencent Hunyuan Community не действует в ЕС, Великобритании,
    Южной Корее, плюс общий CVE-риск произвольных путей в MCP-обвязке → §4 [консенсус: C1, C2, G].
13. `bl_pkg` («Blender Extensions») сам по себе — системный аддон, всегда включён; именно он умеет
    `blender -c extension build-package` и синхронизацию с площадкой → §1, §2.
14. Online Essentials (процедурные материалы 5.2) требуют `use_online_access`/`--online-mode`; лицензия в обзоре версии
    не названа явно — до уточнения брать только локальные Essentials (`datafiles/assets/nodes/*.blend`, CC0, файл
    LICENSE подтверждён) → §1 [V:QkIr1-lDPW0, консенсус с G/03].
15. Node Arrange (GPL-3.0-or-later, extensions.blender.org) — гигиена графа нод перед сдачей файла; дешёвая привычка,
    не требует ручной раскладки → §2.
16. RIgify (в ядре, выключен по умолчанию) — для персонажной анимации; версия 0.6.10 — проверять актуальность при
    смене LTS, риг генерируется из мета-рига, сам по себе не экспортируется в glTF без bake → §1, ссылка
    `07-animation/`.
17. Не доверяй памяти сети об именах старых аддонов («Add Mesh: Extra Objects», «3D Print Toolbox», «Copy Global Transform») — на этой машине их нет ни в `addons_core`, ни как включённых
    по умолчанию расширений («Import Images as Planes» — в ядре с 4.2 как оператор `image.import_as_mesh_planes`, X/02); для 5.2.2 каждое такое имя проверять `addon_utils`/extensions.blender.org, а не писать по памяти
    → «Частые ошибки».
18. Cycles в фоне на этой машине — только CPU (нет CUDA); EEVEE — через EGL на Intel Iris Xe. Для генеративного агента
    это значит: рендер-превью — EEVEE, Cycles — только контрольные кадры с низким числом сэмплов → §1, ссылка
    `06-materials-lighting-render/`.
19. Hydra Storm (рендер-движок в ядре, выключен) — для конвейера сайта не нужен (USD/Hydra для DCC-интеграций, не для
    glTF-экспорта) → §1.
20. Платные Hard Ops/BoxCutter/MESHmachine — интерактивные операторы (кнопки, модальные режимы); ценность для
    **фонового** агента низкая (нужна человеческая работа мышью), ценность для описания шага человеку — высокая → §3.
21. `bpy_probe.py` и `blender_run.py --expr` — единственный надёжный способ узнать, какие операторы/модули реально
    доступны на конкретной сборке; результаты этого файла актуальны для build 2026-09-15, при смене сборки — перепроверить
    → «Чек-лист».

## 1. Встроенные модули Blender 5.2.2 (`addons_core`)

Проверено `bpy.utils.script_paths(subdir="addons_core")` → `/…/blender-5.2.2-linux-x64/5.2/scripts/addons_core/` (13
папок) и `addon_utils.modules()` после `modules_refresh()` [проверено]. Это
**весь** список «бандла» — никаких дополнительных built-in-аддонов в этой сборке нет (в отличие от Blender ≤4.1, где
`scripts/addons/` включал десятки модулей — LoopTools, Extra Objects, Print3D Toolbox и т. п. были там; в 4.2+ они либо
удалены из поставки, либо переехали на extensions.blender.org).

| Модуль | Имя в UI | Версия | Включён по умолчанию | Категория | Ценность агенту |
|---|---|---|---|---|---|
| `io_scene_gltf2` | glTF 2.0 format | 5.2.40 | да | Import-Export | основной канал экспорта на сайт — `08-export-gltf/` |
| `io_scene_fbx` | FBX format | 5.15.0 | да | Import-Export | приём FBX от генераторов/сканов, дальше конвертировать в glTF |
| `io_curve_svg` | SVG 1.1 format | — | да | Import-Export | логотипы/иконки как кривые → экструзия в 3D |
| `io_mesh_uv_layout` | UV Layout | 1.2.0 | да | Import-Export | экспорт развёртки для проверки плотности текселей |
| `io_anim_bvh` | BVH mocap | 1.0.1 | да | Import-Export | приём mocap-анимации (нишево для сайтов) |
| `cycles` | Cycles Render Engine | — | да | Render | контрольный рендер; на машине только CPU |
| `pose_library` | Pose Library | 2.0 | да | Animation | библиотека поз как ассетов, малая ценность для конвейера |
| `bl_pkg` | Blender Extensions | 0.0.1 | да | System | менеджер площадки extensions.blender.org, `extension build-package` |
| `node_wrangler` | Node Wrangler | 4.1.0 | **нет** | Node | быстрые связи нод — включать в `build()`, если пишете материалы руками |
| `rigify` | Rigify | 0.6.10 | **нет** | Rigging | риги персонажей из мета-рига — включать точечно |
| `hydra_storm` | Hydra Storm render engine | 1.0.0 | **нет** | Render | USD/Hydra рендер, не нужен для glTF-конвейера |
| `ui_translate` | Manage UI translations | 2.1.0 | **нет** | System | локализация интерфейса, не для агента |
| `viewport_vr_preview` | VR Scene Inspection | 0.11.2 | **нет** | 3D View | предпросмотр в VR-гарнитуре, не для фонового агента |

Включение отсутствующих по умолчанию — `bpy.ops.preferences.addon_enable(module="node_wrangler")` (в фоне срабатывает
без GUI, проверено при запуске с `--user-prefs`). Папки `extensions/system` (для аддонов, поставляемых ОС-пакетом) —
пустая в этой сборке; `extensions/blender_org` (кэш площадки) — не скачан, пока пользователь ничего не ставил с неё
через интерфейс.

## 2. Платформа extensions.blender.org

С Blender 4.2 старая система «Preferences → Add-ons → Install» для новых аддонов почти не используется — актуальный
путь — извлечения из **платформы расширений**: `Edit → Preferences → Get Extensions` (в GUI) или `bl_pkg` в фоне.
Требования площадки: манифест `blender_manifest.toml` (id, версия, `blender_version_min`, лицензия из списка
SPDX/GPL-совместимых), сборка — `blender -c extension build-package` (не произвольный zip — проверяет обязательные
поля манифеста и структуру) [V:GP53gDHGiIQ 30:52]. Из-за требования GPL-совместимой лицензии **платных** аддонов на
площадке нет — модель монетизации (пожертвования, подписки на «расширенную» версию где-то ещё) видна на примере
LoopTools/Bool Tool ниже, которые бесплатны и там, и на GitHub.

API `GET https://extensions.blender.org/api/v1/extensions/` отдаёт **всё** одним JSON без реальной пагинации:
параметры `?search=`/`?q=` на 23.09.2026 не фильтруют результат (проверено — ответ идентичен без параметров), общий
объём — 1454 записи, ≈940 КБ. Практический метод — скачать раз, кэшировать, фильтровать по полю `name`/`id` локально.

Проверенные записи площадки, относящиеся к инструментам, названным в базе волнами 1–2 (версия/лицензия — прямой ответ
API 23.09.2026):

| Расширение | id | Версия | Лицензия | `blender_version_min` | Что делает |
|---|---|---|---|---|---|
| LoopTools | `looptools` | 4.7.7 | GPL-2.0-or-later | не проверялось отдельно | circle/space/relax/flatten/curve/bridge — стандартный набор ретопологии |
| Bool Tool | `bool_tool` | 2.1.0 | GPL-3.0-or-later | 4.5.0 | быстрые булевы (auto difference/union/intersect) с оверлеем |
| F2 | `f2` | 1.8.5 | GPL-3.0-or-later | 4.2.0 | умный fill (клавиша F) — заплатки по контексту вместо n-гона |
| Bsurfaces GPL Edition | `bsurfaces_gpl_edition` | 1.8.4 | GPL-3.0-or-later | 4.3.0 | ретопология по опорным кривым (surface sketch) |
| Modifier List (форк) | `Modifier_List_Fork` | 2.0.4 | GPL-3.0-or-later | 4.2.0 | компактная панель стека модификаторов |
| Cell Fracture | `cell_fracture` | 0.2.1 | GPL-3.0-or-later | 4.2.0 | разлом меша на осколки — эффект разрушения |
| Node Arrange | `node_arrange` | 1.12.1 | GPL-3.0-or-later | 4.2.0 | автовыравнивание графа нод |

Ни одно из семи **не входит** в `addons_core` — все нужно ставить отдельно (`bl_pkg` умеет это в фоне через CLI, но
команда не проверялась этой волной — риск сетевого вызова из Blender без надзора, см. `04-ai-agents-mcp/07`).

## 3. Сторонние аддоны (не на официальной площадке)

Не найдены в каталоге extensions.blender.org (проверено запросами по названию/id в скачанном каталоге §2) — значит,
устанавливаются вручную (zip → Preferences → Install, или собственный установщик BlenderKit).

| Аддон | Лицензия | Живость | Цена | Headless | Ценность агенту |
|---|---|---|---|---|---|
| RetopoFlow 4 | GPL-3.0-or-later (код); ассеты — проприетарны CG Cookie | живой, push 2026-09-16, 3252★ | $85.99/$151.99 (Superhive) | нет — интерактивный | низкая для фонового агента; полезен для описания шага человеку |
| BlenderKit | GPL-2.0 (аддон); подписка — на сами ассеты | живой, push 2026-09-18, 272★ | бесплатный тир + подписка | частично, нужен сетевой доступ | библиотека материалов/HDRI внутри Blender — см. `10-ai-3d-generation-assets/` |
| MPFB2 | NOASSERTION (GitHub не распознал файл) | живой, push 2026-09-22, 606★ | бесплатно | да | человеческие модели параметрически; тяжёлый для лёгкого лендинга |
| fSpy | MIT | **заброшен** — нет коммитов с 2022-12 (2598★) | бесплатно | частично (CLI-часть) | камера-матчинг по фото; для новых проектов искать альтернативу |
| Hard Ops / BoxCutter | продаётся через Blender Market, публичного репозитория нет | `[не проверено]` | платно, разово | нет | hard-surface моделирование интерактивно, для агента без пользы |
| MESHmachine | продаётся через Blender Market | `[не проверено]` | платно, разово | нет | довод hard-surface поверх Hard Ops |
| MACHIN3tools | публичный репозиторий не найден (сайт автора) | `[не проверено]` | бесплатно | частично | утилиты удобства выделения/трансформа |
| Quick Baker | `[не проверено]` | `[не проверено]` | `[не проверено]` | `[не проверено]` | пакетное запекание карт — кандидат для текстурного конвейера |
| Render Raw | `[не проверено]` (CG Cookie, платный) | `[не проверено]` | платно (Blender Market) | `[не проверено]` | рендер без view transform для точной цветокоррекции AgX/Neutral |

RetopoFlow, BlenderKit, MPFB2 проверены живыми запросами (GitHub REST API/ungh.cc, 23.09.2026); Hard Ops, BoxCutter,
MESHmachine, MACHIN3tools, Quick Baker, Render Raw — публичных репозиториев с метаданными не нашёл за отведённое время
(экономия волны 3 — не гнаться за каждым нишевым платным аддоном; статусы честно `[не проверено]`, не выдуманы).

## 4. Аддоны с генераторами 3D и ИИ внутри

Связь с Blender — только сторона аддона; качество результата для веба разобрано в `10-ai-3d-generation-assets/`. Полная
таблица (12 записей) — `atlas.tsv` (`category=blender-addon-ai`). Сводка по пригодности **на этой машине** (Linux,
без CUDA):

- **Не работает / не имеет смысла на машине базы**: Meshy for Blender (мост — Windows/Mac и Pro+), Tripo DCC Bridge
  (только Windows/Mac), StableGen (нужен GPU ≥8 ГБ), Dream Textures (CUDA/Apple Silicon; к тому же последний релиз
  2024-09 — заморожен), huggingface/meshgen (нужен GPU ≥8 ГБ или платное облако; последний функциональный релиз
  2025-04 — заморожен), Pallaidium (Windows + NVIDIA).
- **Работает без окна и без GPU**: `tripo-3d-for-blender` (VAST, MIT, API-путь, ключ + кредиты), Hyper3D Rodin add-on
  (аккаунт + кредиты, но реально вызывается через MCP-инструменты — см. `03-pipeline-cli-services.md`).
- **Не включать**: Hunyuan3D-2 `blender_addon.py` (лицензия не для ЕС/UK/Южной Кореи, шлёт запросы на
  `localhost:8080` без проверки содержимого) и Hunyuan3DBlenderBridge (сообщество — загружает картинки на публичные
  файлообменники, риск приватности) [консенсус: C1, C2, G].
- **Исторический пример, не использовать**: `gd3kr/BlenderGPT` (MIT, 4984★, заброшен с 2023-06) — предок всех
  чат-аддонов, текст→Python через OpenAI, исполняет сразу без проверки; во всех академических сравнениях (BlenderAlchemy,
  SceneCraft, EZBlender) — худший бейзлайн.

## 5. Аддон-мост для MCP (сторона Blender)

`blender_mcp.py` (пользовательский аддон, категория Interface, версия **1.7**, протокол **9** — проверено
`addon_utils.modules()`, `bl_info.version == (1, 7)`) — часть mcp-for-blender 2.0.3. Работает **только** в Blender с
окном (в фоне MCP-мост не поднимается — проверено оркестратором, `PLAN.md` «Окружение»). Телеметрия выключается
дважды: `DISABLE_TELEMETRY=true` у сервера и отдельная галочка в настройках аддона (по умолчанию **включена** в
аддоне — выключить явно). Версии сервера, 3 CVE (не 2, см. «Открытые вопросы»), сравнение с официальным Blender Lab
MCP и список из ~14 альтернативных серверов — `03-pipeline-cli-services.md §3` (это файл про MCP-серверы; здесь —
только сторона аддона, чтобы не дублировать).

Официальный `KhronosGroup/glTF-Blender-IO` (Apache-2.0, 1663★, push 2026-09-21) — апстрим экспортёра из §1; там же
документированная **hook-система** — официальная точка расширения поведения импортёра/экспортёра без форка
[V:FIHu6-3rjX4 W50:58–W51:09]. Разработчик прямым текстом предупреждает: «можно всё сломать» при неверном
использовании — обращаться с той же осторожностью, что к любому стороннему коду внутри Blender (совпадает с
предупреждением O про исполнение произвольного кода).

## Частые ошибки

- **Предполагать по памяти, что LoopTools целиком/Bool Tool/Extra Objects/Print3D Toolbox встроены** (из LoopTools в ядре только Flatten, Circle, Space) — в 5.2.2 их нет ни в
  `addons_core`, ни включены по умолчанию; для каждого имени аддона — проверка `addon_utils`/extensions.blender.org
  → M-подобная ошибка «версия по памяти», см. `03-bpy-api/04`.
- **Проверять доступность оператора через `hasattr(bpy.ops.<cat>, "имя")`** — всегда `True`, `bpy.ops` создаёт обёртку
  динамически; правильно — `bpy.ops.<cat>.<имя>.get_rna_type()` в `try/except KeyError`; `hasattr(bpy.types, "КАТЕГОРИЯ_OT_имя")` верен только для Python-операторов (C-операторы, например `mesh.flatten`, `object.delete`, в `bpy.types` не видны — X/02)
  [проверено].
- **Забыть, что Node Wrangler и Rigify выключены по умолчанию** — код, который использует их операторы без
  `addon_enable()`, упадёт в чистой сессии (в т. ч. в CI/тестах на факторной установке).
- **Принять «GPL» и «бесплатно» как синонимы законности переиспользования ассетов** — у RetopoFlow код GPL, но
  кисти/иконки нет; копировать не-код части в свой проект нельзя без отдельного разрешения.
- **Включать Hunyuan3D-интеграции по умолчанию** — лицензионный риск (территориальные ограничения) и повышенная
  CVE-поверхность (localhost-сервер без проверки содержимого запроса).
- **Считать площадку extensions.blender.org полным каталогом всех Blender-аддонов** — платных и части старых
  бесплатных там нет; для конкретного инструмента всегда проверять и площадку, и GitHub/сайт автора.

## Чек-лист

- [ ] Список нужных модулей `addons_core` явно включён в `build()` (`node_wrangler`, `rigify` и т. п.), а не
      предполагается «уже работает»?
- [ ] Для каждого стороннего аддона, названного в коде/промте, проверена live-запись в `atlas.tsv`
      (`version != "[не проверено]"`)?
- [ ] Если аддон с extensions.blender.org — версия и лицензия свежие (запись `source=live:extensions.blender.org`,
      не старый кэш)?
- [ ] Для Hunyuan3D-путей — подтверждена территория заказчика (не ЕС/UK/Южная Корея) перед включением?
- [ ] Проверка наличия оператора сделана через `get_rna_type()` (не `hasattr(bpy.ops…)` и не `hasattr(bpy.types…)`)?
- [ ] MCP-аддон (`blender_mcp.py`) телеметрия выключена в обоих местах (сервер и галочка аддона)?

## Открытые вопросы и противоречия

1. **LoopTools** — решено X/02 и оркестратором: Flatten/Circle/Space встроены родными операторами 5.2 (дайджест `g4OXlrxqIx0` 00:17 верен), Relax/Curve/GStretch — в расширении; «не в ядре» было следствием проверки через `bpy.types`, которая C-операторы не видит. Исходная запись: W12 (`wave3-W12-report.md`, «Для L») — «LoopTools в ядре 5.2» против прямой проверки этой волны
   (не в ядре, отдельное расширение GPL-2.0-or-later v4.7.7) и находки волны 2 (D1/W4/B: «с 4.2 расширения» — с ней
   совпадает). Источник W12 — таймкод видео `[g4OXlrxqIx0 00:17]`, возможно неточная передача на слух или речь о
   другой версии/контексте. **В реестр аудита X**: поправить `wave3-W12-report.md` или явно пометить видео-источник
   как неточный — чужой файл не правил.
2. **RetopoFlow/Hard Ops/BoxCutter лицензионная модель** — GPL-код за деньги: юридически бесплатно использовать код,
   но индустриальная норма — платить, если используешь профессионально. Для системы генеративного дизайна заказчика
   это `[спорно]`: юридически можно, этически/репутационно — решение заказчика.
3. **MACHIN3tools, Hard Ops, BoxCutter, MESHmachine, Quick Baker, Render Raw** — не нашёл публичных репозиториев с
   метаданными за время волны (экономия); статус, версия, точная лицензия — `[не проверено]`. Кандидат на точечную
   проверку волной 4 или отдельным запросом, если эти инструменты понадобятся в рецептах K.
4. **MPFB2 лицензия** — GitHub `NOASSERTION`; нужно вручную прочитать `docs/`/заголовки файлов исходников, если
   MPFB2 попадёт в реальный конвейер (пока используется как локальный инструмент, не переиспользуется в вебе — риск
   низкий).
5. **`extension build-package` в фоне без надзора** — не проверялась этой волной как реальная команда (риск: сетевой
   вызов к площадке от имени агента); для O — кандидат в модель угроз headless-эксплуатации.

## Источники

- [S1] extensions.blender.org, `GET /api/v1/extensions/`, весь каталог, 23.09.2026 — версии/лицензии LoopTools, Bool
  Tool, F2, Bsurfaces, Modifier List, Cell Fracture, Node Arrange [проверено].
- [S2] GitHub REST API + ungh.cc, 23.09.2026 — `CGCookie/retopoflow` (3252★, GPL-3.0-or-later по `RetopoFlow.LICENSE`),
  `BlenderKit/Blendkit` (272★, GPL-2.0), `makehumancommunity/mpfb2` (606★, NOASSERTION), `stuffmatic/fSpy` (2598★,
  MIT, заброшен), `KhronosGroup/glTF-Blender-IO` (1663★, Apache-2.0) [проверено].
- [S3] WebSearch «RetopoFlow license GPL Blender Market» 23.09.2026 — код GPL-3.0, ассеты проприетарны, цены Superhive
  [проверено].
- [S4] `99-raw/experiments/L/01-addon-checks/` — собственные эксперименты: `addon_utils.paths()`,
  `addon_utils.modules()`, строгая проверка `bpy.types` для LoopTools/Bool Tool/F2/Bsurfaces [проверено].
- [S5] `../../scripts/3d/README.md` — окружение (Blender 5.2.2, аддоны пользователя MCP for Blender 1.7 + MPFB).
- [S6] `PLAN.md` «Окружение» — версии, ограничения железа, MCP-мост только с окном.
- [S7] `99-raw/reports/wave3-W12-report.md` §«Для L» — LoopTools (частично верно: три инструмента встроены, X/02), `blender_manifest.toml`,
  ahujasid/blender-mcp как предок, Higgsfield.
- [S8] `04-ai-agents-mcp/02-integrations-landscape.md` §4–5 — аддоны с LLM, аддоны генераторов, живость на 22.09.2026.
- [S9] `10-ai-3d-generation-assets/01-generators-landscape.md` §4 — вызов генераторов через MCP-аддон протокола 9.
- [S10] `10-ai-3d-generation-assets/03-asset-libraries-licenses.md` §4.1 — Online Essentials, лицензия не названа в
  обзоре.
- [S11] Reports волны 2 (D1, W4, B — через «Учти из волны 2» задания L) — Bool Tool/LoopTools/F2/Bsurfaces как
  расширения с 4.2, платные Hard Ops/BoxCutter/MESHmachine, бесплатные MACHIN3tools/Modifier List/fSpy;
  RetopoFlow 4 «статус проверить» — закрыто этой волной (§3).
