# Ландшафт интеграций «нейросеть ↔ Blender» (сентябрь 2026)

Волна 1 · агент C2 · 22–23 сентября 2026. Источники: официальные страницы и код Blender Lab (10 файлов), политика Blender
Foundation по ИИ (4 документа, цитаты сверены), правила платформы расширений, анонс Anthropic, PyPI `bpy`; разведка GitHub
помощником C2 (879 репозиториев по запросу «blender mcp», просмотрено ~70 по звёздам + тематические запросы, ~60 страниц
проектов); звёзды, лицензии и даты коммитов 30 ключевых репозиториев перепроверены C2 через GitHub API и Atom-ленты
[S1]. Эксперимент: официальный MCP Blender Lab v1.0.3 в фоновом Blender 5.2.2 [S2]. Отдельно проверены: две CVE mcp-for-blender (третья, 10662, — у O `07-security.md` §5.3),
его страница телеметрии, тред разработчиков Blender о безопасности, два независимых опыта агентов с Blender. Версии: Blender 5.2.2 LTS,
MCP SDK Python <2 (официальный сервер). Детальный разбор mcp-for-blender — `01-mcp-for-blender.md` (C1); генераторы 3D из
текста и картинки — агент G (`../10-ai-3d-generation-assets/`); исследования — `03-research-llm-3d.md`.

## Выжимка для агента

1. **В самом Blender генеративного ИИ нет и не планируется**: «No generative AI functionality is currently available or
   planned to be integrated in Blender» (Blender Foundation, 01.05.2026). → §2.1 `[документация, 2026-09]`
2. **Официальный путь — MCP-сервер Blender Lab** (v1.0.3, 11.09.2026, GPL-3.0-or-later, Blender ≥5.1): он же коннектор
   Blender в каталоге Claude с 28.04.2026. → §2.2 `[документация]`
3. **Официальный сервер работает без окна**: `blender -b file.blend --command blender_mcp` (нужен `--online-mode`); в 5.2.2
   исполняет код, рендерит EEVEE, отдаёт 2 МБ. → §2.3 `[проверено]`
4. **Контракт официального `execute_blender_code`**: данные — в `dict` по имени `result`; `print` → `stdout`; ошибка → полный
   traceback; переменные Python между вызовами не живут, данные `bpy` — живут. → §2.3 `[проверено]`
5. **Справка API 5.2 встроена в официальный сервер** (`search_api_docs`, `get_python_api_docs`, `search_manual_docs`) —
   используй её при любой ошибке API, а не память модели. → §2.3 `[документация]`
6. **mcp-for-blender (ahujasid, 29 193★) — «комбайн» для работы с окном**: ассеты Poly Haven, Sketchfab, Poly Pizza и
   генераторы Rodin, Hunyuan3D; в фоне без самодельного моста не работает; телеметрия: минимальная запись по умолчанию, полное согласие в 2.0.3 — opt-in (до 21.09.2026 было включено; `07-security.md` §5.2). → §2.4 `[документация, C1]`
7. **Оба главных сервера слушают порт 9876** — один Blender с двумя аддонами или два процесса на одном порту конфликтуют;
   мосту агента давай отдельный порт. → §2.4 `[проверено]`
8. **Для агента без окна пригодны**: официальный сервер (`--command`), bpy-dev/blender-mcp (форк официального, `_for_cli`,
   бэкенд `bpy` из PyPI), dcc-mcp-blender (MCP внутри фонового Blender, CI на 5.2.1), sandraschi/blender-mcp (фон по
   умолчанию), и просто `blender -b --python`. → §3.2, §7.4 `[документация, по репозиториям]`
9. **Лучшая модель безопасности среди найденных — CallMeJones/blender-agent-bridge**: Python выключен до явного
   «доверия сессии», превью правок с Commit/Revert, файлы только в каталоге проекта. → §3.1 `[документация]`
10. **Проверки вместо свободного Python — отдельная ветка**: PatrykIti/blender-ai-mcp (`scene_measure_*`, `scene_assert_*`),
    bforge (138 операций по белому списку, воспроизводимость) — совпадает с выводом исследований «проверки кодом сильнее
    VLM». → §3.1 `[документация]`
11. **Не выставляй мост в сеть**: blender-open-mcp слушает `0.0.0.0:8000`, seehiong — `0.0.0.0` по умолчанию; совет
    «пробросить MCP через localtunnel» — антипример. → §3.1, §10 `[документация]`
12. **Встроенные чат-аддоны «текст → exec» 2023–2024 заброшены** (BlenderGPT — последний коммит 10.06.2023); ставку рынок
    сделал на MCP и навыки для кодовых агентов. → §4 `[консенсус]`
13. **«BlenderGPT» — минимум три разных продукта** (аддон gd3kr, облачный генератор blendergpt.org, платный аддон 2023 г.) —
    указывай URL. → §4.3 `[документация]`
14. **На extensions.blender.org нет ни LLM-ассистентов, ни MCP-мостов**: правила запрещают внешние ключи и регистрацию,
    блокирующие функции, и загрузку удалённого кода. ИИ-аддоны — только из GitHub и магазинов. → §2.1a `[документация]`
15. **Главный тренд 2026 — пакеты навыков (skills) для Claude Code, Codex, Cursor, Gemini CLI** поверх MCP или
    `blender -b`; самый заметный — dream-loop (1 514★). → §7.3 `[документация]`
16. **Для «Blender → сайт» MCP не обязателен**: навык cth9191/blender-to-web (Blender 5.2.1 → Three.js) собирал ассеты
    скриптами CLI, а MCP-соединение в той сборке не работало. → §7.3 `[документация, единичный пример]`
17. **`bpy` из PyPI = фоновый Blender в своём Python**: 5.2.2 (15.09.2026) требует ровно Python 3.13; один .blend на процесс;
    нет GUI-операторов; колесо Linux 401.7 МБ. → §8 `[документация]`
18. **`fake-bpy-module-5.2`** даёт автодополнение и статическую проверку в IDE — не исполнение. → §8 `[документация]`
19. **Infinigen и BlenderProc сидят на Blender 4.2** (`bpy==4.2.0`, Python 3.11; BlenderProc качает 4.2.1) — в 5.2 не ставятся.
    → §6 `[документация, 2026-09]`
20. **Исследовательские агенты с кодом** (LL3M, VIGA, BlenderGym, EZBlender, BlenderRAG, 3DCodeBench) — источники приёмов и
    тестов, не готовые инструменты: версии Blender 3.x–5.0, ключи облачных моделей. → §9 `[исследование]`
21. **Локальные модели — только для вспомогательных ролей**: официальная инструкция Blender Lab — llama.cpp с моделями
    ~26–35B; исследования: малые VLM дают 0 % рабочих скриптов Blender. → §2.3, `03` §8 `[документация + исследование]`
22. **Любой MCP-мост = исполнение произвольного кода**: изоляция процесса агента, рабочая папка, выключенная телеметрия,
    ключи вне аддонов. → §10 `[документация, консенсус]`
23. **У mcp-for-blender три CVE 2026 г., все не исправлены в 2.0.3**: CVE-2026-10661 (CVSS v4 2.1 / v3.1 4.3 — инъекция через `input_image_url`), CVE-2026-10662 (SSRF через `zip_file_url`, v3.1 6.3) и CVE-2026-10688
    (исполнение кода через `execute_blender_code`; OpenCVE 5.1, NVD v3.1 5.5 / v4 2.0); согласие на полную телеметрию (промты, код, скриншоты вьюпорта,
    данные сцены; «may be used… to train AI models») было включено по умолчанию до 2.0.3 `[устарело: до 21.09.2026]`. → §10 `[документация, 2026-09]`
24. **Разработчики Blender: безопасно только на отдельной машине или ВМ за файрволом**; песочница — «not something Blender
    can/should realistically solve»; на Linux опробованы лёгкие jai и bubblejail. → §10 `[мнение сотрудников Blender]`
25. **Независимые опыты 2026 работают через `blender --background --python` + рендер, а не через MCP** (Willison, бенчмарк
    на Blender 5.0.1, 3DCodeBench); в бенчмарке ни один из 15 скриптов не измерял референс — «семантическая
    реконструкция, а не обратная графика». → §7.5 `[практика]`
26. **Каталоги MCP (PulseMCP, mcp.so, Glama, awesome-списки) официального сервера не содержат** — поиск по каталогу
    приводит к ahujasid; официальный ставь по прямой ссылке projects.blender.org. → §7.5 `[документация]`

## 1. Карта ландшафта

| Категория | Что это | Лидеры и примеры (сентябрь 2026) | Живость | Раздел |
|---|---|---|---|---|
| Официальная интеграция | MCP-сервер Blender Lab + коннектор Claude | lab/blender_mcp v1.0.3 | живой (11.09.2026) | §2 |
| MCP-серверы сообщества | мост «модель ↔ аддон в Blender» | ahujasid/mcp-for-blender (29 193★); далее на 2–3 порядка меньше: blend-ai 142★, blender-open-mcp 117★, bpy-dev 93★ | «один гигант + длинный хвост» из сотен серверов | §2.4, §3 |
| Чат-аддоны внутри Blender | панель «текст → код → исполнить» | BlenderGPT (4 984★, заброшен), meshgen (Hugging Face, заморожен), Chat Companion (платный) | классика мертва, новые — коммерческие | §4 |
| Аддоны генераторов 3D и текстур | вызов облачного/локального генератора из Blender | интеграции в MCP-серверах (Rodin, Hunyuan3D, Meshy, Tripo); форк Mixar | разные | §5, агент G |
| Процедурные генераторы на Blender | фабрики сцен и объектов | Infinigen (7 274★), BlenderProc (3 725★ по G5) | живы, но на Blender 4.2 | §6 |
| Агентные IDE и навыки | Claude Code, Codex, Cursor, Gemini CLI + skills | dream-loop 1 514★, blender-skills, design-os-3d-blender, blender-agent-studio, blender-kiln | главный тренд 2026 | §7 |
| Blender как библиотека | `bpy` из PyPI, `fake-bpy-module` | bpy 5.2.2 | синхронно с релизами | §8 |
| Исследовательские агенты | код статей | VIGA 1 308★, LL3M 554★, 3DCodeBench 99★ | препринты 2025–2026 | §9 |

## 2. Официальная линия: Blender Foundation и ИИ

### 2.1. Хронология и политика

| Дата | Событие | Источник |
|---|---|---|
| 07.11.2025 | объявлен **Blender Lab** — «innovation space»; среди планов — «AI and ML technologies, starting with a Blender MCP server» | [S3] |
| 21.02.2026 | создан репозиторий `lab/blender_mcp`; v0.1.0 — 24.03.2026 | [S4] |
| 24.04.2026 | отчёт Lab за I квартал: «The Blender project keeps a firm artist-centric policy when it comes to AI»; упор на локальную среду с открытыми моделями | [S5] |
| 27–28.04.2026 | MCP v1.0.0; Anthropic объявляет коннектор Blender в Claude («Claude for Creative Work») и поддержку проекта | [S4][S6] |
| 01.05.2026 | после критики сообщества членство Anthropic в Development Fund заменено **разовым пожертвованием**; заявление: «Blender is a tool for artists and creators, it's made by humans for humans. **No generative AI functionality is currently available or planned to be integrated in Blender.**» | [S7] |
| 02.06.2026 | «Guidelines for AI-enabled features»: «There are no plans to develop or implement "generative" AI features (e.g. prompt-based artwork generation, mesh generation, etc.) in Blender»; допустимые функции — **вспомогательные**, модель «local and sovereign» (запуск локально, лицензия, совместимая с copyleft) и «IP conscious» (обучена на законно лицензированном контенте); исследования — в Blender Lab | [S8] |
| 2026 | «AI Contributions Policy» для кода Blender: авторы коммитов — только люди; **на расширения не распространяется** | [S9] |
| 08–11.09.2026 | MCP v1.0.2 (пин MCP SDK <2), v1.0.3 (исправлен захват скриншотов); справочник обновлён до 5.2 | [S4] |

**Вывод для базы** `[документация, 2026-09]`: генеративных функций (меши, картинки по промту) **в самом Blender нет и не
планируется**; официальная поддержка ИИ — это MCP-мост для анализа, отладки и скриптов, с акцентом на локальные модели.
Всё генеративное (текст → 3D, текстуры) — сторонние аддоны и сервисы.

### 2.1a. Платформа расширений и ИИ-аддоны

- Правила extensions.blender.org (обновлены 10.08.2026) **не упоминают ИИ**, но фактически закрывают путь облачным
  ИИ-аддонам [S10]: «It is not allowed to have additional requirements (such as purchasing additional content,
  registration on external service, payments or keys, etc.) blocking functionality of the extension» (3.10); сетевые
  расширения обязаны запрашивать разрешение `network` в манифесте и уважать настройку «Allow Online Access»
  (`bpy.app.online_access`; в фоне — `--online-mode`/`--offline-mode`) (4.1–4.2) [S11]; «must not send data to
  any remote locations without authorization from the user» (4.5); «not load remote code for execution» (5.1).
- Поиск по платформе 22.09.2026: «LLM», «MCP», «Ollama» — 0 результатов; ИИ-ассистентов, MCP-мостов и генераторов 3D на
  официальной платформе нет; официальный MCP распространяется через **отдельный репозиторий расширений Blender Lab** [S12].
- Следствие для нас: ИИ-аддоны ставятся из GitHub/магазинов (Superhive, Gumroad) — проверять их код и лицензию самим.

### 2.2. Blender Lab и официальный MCP-сервер

- **В самом Blender ИИ нет.** Дословно со страницы Blender Lab: «Blender does not have any built-in functionality for
  connecting to LLMs». Для связи с моделью нужны три внешних компонента: аддон, LLM-клиент, MCP-сервер [S13].
  `[документация, 2026-09]`
- **Blender Lab — площадка экспериментальных проектов Foundation**; её первый заметный проект — **MCP Server**
  (`projects.blender.org/lab/blender_mcp`): создан 21.02.2026, v0.1.0 — 24.03.2026, **v1.0.0 — 27.04.2026**, v1.0.2 —
  08.09.2026, **v1.0.3 — 11.09.2026** («Screenshot Fix»); последний коммит 11.09.2026 — «Update 5.2: manual & API»;
  ведут ключевые разработчики Blender (Campbell Barton, Dalai Felinto); лицензия **GPL-3.0-or-later**; 25 звёзд, 23 форка
  на projects.blender.org [S4]. `[документация]`
- **28.04.2026 Anthropic** объявил «Claude for Creative Work»: в каталоге коннекторов Claude появился Blender —
  «The Blender developers have created an MCP connector, which is now officially available for Claude»; коннектор построен
  на MCP и доступен другим моделям. Anthropic сделал пожертвование; правка 01.05.2026: Blender принял его **как разовое
  пожертвование, а не через Blender Development Fund** [S6]. `[документация]`
- **Позиционирование — анализ и отладка, не генерация ассетов.** Формулировка проекта: «natural language interface with
  Blender's Python API, improving access to documentation, and allowing users to explore and understand complex setups».
  Примеры на странице: поиск «тяжёлых» объектов на экране (сцена Classroom: `alphabet` 20k полигонов, `coat 1` 37k из-за
  Subsurf), переименование датаблоков по соглашению, поиск по связям («какие объекты используют материал pebbles»),
  документирование дерева geometry nodes фреймами и текстовым блоком. Страница сама честно показывает ошибку модели:
  анализ учёл только модификаторы вьюпорта и пропустил Solidify, удваивающий полигоны [S13].
- **Предупреждение о безопасности** (дословно): «The MCP server will execute LLM generated code in Blender without any
  guards in place to protect your data from removal or being sent to a remote location. To keep your data safe it is
  recommended to use a virtual machine, or a system without access to sensitive information.» [S13]

### 2.3. Официальный MCP-сервер Blender Lab: устройство

| Параметр | Значение (v1.0.3, 11.09.2026) |
|---|---|
| Состав | аддон-расширение `mcp` (манифест: `blender_version_min = "5.1.0"`, `permissions.network`) + пакет `blender-mcp` (Python ≥3.10; зависимости `docutils`, `mcp[cli]>=1.2,<2`, `pyyaml`) |
| Связь | клиент ⇄ stdio (или HTTP `--transport http --port 9191`) ⇄ `blender-mcp` ⇄ TCP ⇄ аддон; кадр — JSON + `\0`, одно соединение — один запрос |
| Порт по умолчанию | **9876** (тот же, что у mcp-for-blender) |
| Требование | **Online Access** в настройках Blender или `--online-mode` в фоне; без него мост не стартует [S2] |
| Фоновый режим | `blender --background file.blend --command blender_mcp`: блокирующий цикл на `select`, запросы исполняются синхронно на главном потоке; отложенные ответы не поддерживаются |
| Инструменты (29) | `execute_blender_code` (+ `_for_cli` — в отдельном фоновом процессе по пути .blend); сводки файла (`get_blendfile_summary_datablocks`, `_missing_files`, `_of_linked_libraries`, `_path_info`, `_usage_guess`, у каждого вариант `_for_cli`); `get_objects_summary`, `get_object_detail_summary`; `get_python_api_docs`, `search_api_docs`, `search_manual_docs`; `get_screenshot_of_area_as_image`, `get_screenshot_of_window_as_image`, `get_screenshot_of_window_as_json`; `jump_to_tab_by_name`, `jump_to_tab_by_space_type`, `jump_to_view3d_object_by_name`, `jump_to_view3d_object_data_by_name`; `render_thumbnail_to_path`, `render_viewport_to_path` |
| Документация внутри | справочник Python API и руководство пользователя в RST, **обновлены до 5.2** (коммит 11.09.2026); поиск по ним — инструментами |
| Контракт исполнения | вернуть данные — присвоить `dict` переменной `result`; `print` → поле `stdout`; ошибка → полный traceback; переменные Python между вызовами не сохраняются, данные `bpy` — сохраняются [S2] |
| «Песочница» | `weak_sandbox.py` — «не песочница, а шлепок по рукам»: подмена `sys.exit`, блок `wm.quit_blender`, `wm.read_factory_settings`, `wm.read_factory_userpref`, `wm.read_userpref` |
| Инструкция модели | `prompts.yml` (123 строки): «никогда не предполагай значения — сначала осмотри сцену», «не изменяй разрушительно без подтверждения», `execute_blender_code` — последнее средство; режим, active и selection задавать явно; обновлять depsgraph перед чтением вычисляемых свойств; bmesh в режиме правки + запись обратно; объекты из data API линковать в коллекцию; держать ссылку на объект, а не искать по имени (`.001`); проверять `rotation_mode`; применять масштаб перед булевыми; осматривать большие сцены постепенно |
| Локальные модели | официальная инструкция — llama.cpp (сборка ≥8218) + свой текстовый клиент или веб-интерфейс llama.cpp; пример модели Qwen3.5-35B-A3B GGUF |
| Установка | через репозиторий расширений Blender Lab (перетащить ссылку дважды: добавить репозиторий, затем аддон — будут уведомления об обновлениях) или zip «Install from Disk»; сервер — пакет `.mcpb` (MCP Bundle) или из исходников |
| Интеграции ассетов и генераторов | **нет** (ни Poly Haven, ни Sketchfab, ни Rodin/Hunyuan) |
| Телеметрия | не заявлена в документации; в прочитанных файлах сетевых вызовов, кроме локального сокета, нет |

**Проверка на этой машине** [S2]: аддон v1.0.3 (исходники, без установки в настройки пользователя) в
`blender -b --factory-startup --online-mode` на **Blender 5.2.2**: регистрация и CLI-команда работают; 9 проверок
пройдены (создание меша, traceback, блок выхода, `result` не dict, `stdout`, рендер EEVEE 256² за 2.89 с, ответ 2 МБ);
без `--online-mode` — отказ. `[проверено]`

### 2.4. Официальный сервер против mcp-for-blender (ahujasid)

| | Blender Lab MCP [S4] | mcp-for-blender [S14] (детали — файл 01, C1 [S15]) |
|---|---|---|
| Кто | Blender Foundation (Blender Lab) | сообщество (Siddharth Ahuja и участники) |
| Лицензия | GPL-3.0-or-later | MIT |
| Популярность | 25★ на projects.blender.org (основная аудитория — через каталог Claude) | 29 193★ на GitHub |
| Живость | коммит 11.09.2026, релиз v1.0.3 | коммит 21.09.2026, пакет 2.0.3 |
| Версии Blender | ≥5.1 (справка обновлена до 5.2) | аддон заявляет ≥3.0; у пользователя аддон протокола 7 при сервере, ждущем 9 (разбор — C1) |
| Назначение | анализ, отладка, документация, скрипты | создание сцен и ассетов: исполнение кода + ассеты Poly Haven, Sketchfab, Poly Pizza + генераторы Hyper3D Rodin, Hunyuan3D + экспорт |
| Инструменты | 29, упор на чтение сцены и документации | 32 + промт `asset_creation_strategy` (по C1: описания инструментов ≈9.3 тыс. токенов контекста) |
| Фон без окна | **штатно**: `--command blender_mcp`, инструменты `*_for_cli` | авторы: в `blender -b` команды не исполняются; нужен GUI или `xvfb-run` (обход — самодельный мост, см. C1) |
| Документация API в сервере | встроена (RST 5.2) + поиск | инструмент `bpy_api_lookup` (разбор — C1) |
| Телеметрия | не заявлена | «anonymous usage telemetry by default… Consent is on by default» (сайт; `[устарело: до 21.09.2026]` — в коде 2.0.3 полное согласие opt-in, `07-security.md` §5.2): при согласии — промты, исполненный код, скриншоты вьюпорта, данные сцены, «may be used… to train AI models»; выключение — галочка Telemetry Consent + `DISABLE_TELEMETRY=true` [S16]; детали — C1 |
| Уязвимости (CVE) | публичных не найдено (22.09.2026) | CVE-2026-10661 (низкая, v4 2.1: инъекция через `input_image_url`) [S17]; CVE-2026-10662 (SSRF, v3.1 6.3; `07-security.md` §5.3); CVE-2026-10688 (5.1 по OpenCVE: исполнение кода через `execute_blender_code`) [S18]; в 2.0.3 не исправлена ни одна |
| Защита | блок выхода/сброса настроек; требование Online Access | необязательный «safe mode» (AST-проверка на сервере, `BLENDER_MCP_SAFE_MODE`); сокет без аутентификации |
| Порт | 9876 | 9876 |

Итог: официальный сервер — **надёжная база для агента без окна** (фон, документация 5.2, простой контракт), но в нём
нет ассетов и генераторов; mcp-for-blender — «комбайн» для интерактивной работы с окном и внешними ассетами, с
телеметрией и конфликтом протоколов у пользователя. Оба используют порт 9876 — одновременно не поднять без смены порта.

## 3. Другие MCP-серверы (кроме официального и mcp-for-blender)

По запросу «blender mcp» на GitHub — 879 репозиториев (22.09.2026) [S12]. Ниже — живые и заметные; звёзды, лицензии и
даты — GitHub API 22.09.2026 [S1].

### 3.1. Живые серверы

| Проект | ★, последняя активность | Лицензия | Blender | Чем отличается | Безопасность |
|---|---|---|---|---|---|
| bpy-dev/blender-mcp [S19] | 93, 2026-09-12 | GPL-3.0 | как официальный | **форк официального Blender Lab MCP**: `_for_cli` в подпроцессах без окна, бэкенд `bpy` из PyPI (`BLENDER_MCP_CLI_BACKEND=bpy`), поиск по живому API, бенчмарк BlenderBench; «developer preview» | изоляция процессов, «not an OS sandbox» |
| HoldMyBeer-gg/blend-ai [S20] | 142, релиз 2026-09-21 | AGPL-3.0 | 4.2+, проверен на 5.1 | 175 инструментов в 24 модулях, 12 «экспертных» промтов (топология, масштаб, свет, самокритика по скриншоту) | блок-лист импортов (обходится); «zero telemetry» |
| dhakalnirajan/blender-open-mcp [S21] | 117, 2026-09-04 | MIT | не указаны | выбор поставщика модели: Ollama, LM Studio, llama.cpp, OpenAI-совместимые, Azure; «модель внутри сервера» | **по умолчанию `0.0.0.0:8000`** + исполнение кода |
| PatrykIti/blender-ai-mcp [S22] | 57, 2026-05-04 | Apache-2.0 | 4.0+, E2E на 5.0 | **курированные инструменты вместо свободного Python**; детерминированные проверки `scene_measure_*`, `scene_assert_*` (контакт, габариты, симметрия) | отказ от свободного exec |
| seehiong/blender-mcp-bridge [S23] | 56, 2026-09-13 | MIT | 4.0+ | 93 инструмента, HTTP MCP, веб-студия записи сессий | **`MCP_BRIDGE_HOST = 0.0.0.0` по умолчанию** |
| sandraschi/blender-mcp [S24] | 46, 2026-09-18 | MIT | 3.0+ | **фон по умолчанию** (`blender --background`), мост к окну опционален; 41 составной инструмент | — |
| dcc-mcp/dcc-mcp-blender [S25] | 37, релиз 2026-09-22 | MIT | CI на **5.2.1 LTS** и 4.5.13 LTS | MCP по HTTP **внутри процесса Blender**, headless-загрузчик; часть экосистемы DCC-MCP (Maya, Houdini) | exec выключается переменными окружения |
| djeada/blender-mcp-server [S26] | 27, 2026-06-21 | MIT | — | транспорт `bridge` или `headless` (отдельный `blender -b` для тяжёлых задач) | safe mode, белые списки |
| CallMeJones/blender-agent-bridge [S27] | 22, 2026-08-11 | GPL-3.0 | 4.2 / 4.5 / 5.1 | превью правок с Commit/Revert; ассеты Poly Haven, Sketchfab, генераторы Tripo, Meshy, локальный TripoSR с оценкой стоимости | **Python выключен до «session trust»**; мост по умолчанию выключен; bearer-токен; ключи не пишутся в .blend |
| minihellboy/claude-blender [S28] | 5, 2026-07-30 | MIT | 4.0+ | MCP SDK v2; headless-скрипт (всё, кроме скриншотов и undo) | — |
| lxsolutions/studio-foundation (bforge) [S29] | 26, 2026-09-14 | **source-available** (PolyForm Perimeter) | — | headless-демон, 138 типизированных операций по белому списку, побайтово воспроизводимая регенерация, гейты качества, выход glTF/GLB для Godot/Babylon/three | без произвольного кода |
| Mixar-AI/mixar-app [S30] | 255, 2026-09-15 | GPL-3.0 (клиент) | форк Blender 5.0 | целиком «AI-Blender» со встроенным агентом и генерацией | облачный бэкенд, аккаунт |

Ещё живые, но мелкие (по G5): harveyxiacn/blender-mcp («359 tools», исправления для Blender 5.x), RFingAdam/mcp-blender
(218 инструментов, AGPL-3.0), newo-ether/blender-mcp (версионно-точные запросы к руководству и API), ellmos-ai (без
аддона и порта: каждый вызов — `blender --background`), cUDGk/blender-mcp (постоянный фоновый Blender с токеном),
Show2Instruct/ifc-bonsai-mcp (BIM/IFC). Платные: youichi-uda/blender-mcp-pro (15 USD разово или 5 USD/мес), ai-forge-mcp
(подписка) [S12].

### 3.2. Какие годятся агенту без окна

| Путь | Без GUI | Замечание |
|---|---|---|
| Официальный Blender Lab MCP, `--command blender_mcp` | **да** (проверено C2) | документированный путь — с окном; фон — через CLI-команду аддона [S2] |
| bpy-dev/blender-mcp | да | `_for_cli` + бэкенд `bpy` [S19] |
| dcc-mcp-blender | да | загрузчик в `blender --background` [S25] |
| sandraschi/blender-mcp | да | по умолчанию [S24] |
| djeada, minihellboy | частично/да | headless-транспорт; без скриншотов и undo [S26][S28] |
| mcp-for-blender (ahujasid) | нет | аддон в окне; обход — самодельный мост (C1) [S15] |
| Чат-аддоны (§4) | нет | живут в N-панели |

### 3.3. Заброшенные (активность >6–9 мес. назад)

VxASI/blender-mcp-vxai (299★, последний коммит 21.03.2025) [S31]; AIGODLIKE/GenesisCore (135★, 18.04.2025, лицензии нет);
saofund/LLM-Blender-Agent (39★, 27.03.2025; в статье 3DCodeBench указан как пример); victordibia/blenderlm (15★, 05.06.2025);
клоны ранней волны 2025 г. Удалены (404 на 22.09.2026): CommonSenseMachines/blender-mcp, poly-mcp/Blender-MCP-Server — ещё
числятся в каталогах MCP [S12].

**Вывод.** Почти все серверы дают исполнение произвольного Python; «песочницы» — блок-листы импортов (обходятся) или
ручное доверие. Несколько серверов по умолчанию слушают `0.0.0.0` — риск удалённого исполнения кода в локальной сети.

## 4. Аддоны с LLM внутри Blender

### 4.1. Классика 2023–2024 — заброшена

| Проект | ★ | Последняя активность | Суть |
|---|---|---|---|
| gd3kr/BlenderGPT [S32] | 4 984 | коммит 10.06.2023 | панель «GPT-4 Assistant»: текст → Python через OpenAI → **сразу исполняет**; Blender 3.1+; бейзлайн в статьях BlenderAlchemy, SceneCraft, EZBlender, CADBench — везде проигрывает |
| pramishp/BlenderCopilot, nutti/OpenAI-Bridge, TREE-Ind/Blender-GPT, joshuaKnauber/bpy-chat-gpt, ryvn-dev/blender-gpt | 16–137 | 2023–2024 | заброшены; kennethjyang/blender-ai-assistant — в архиве [S12] |

### 4.2. Волна 2025–2026

- **huggingface/meshgen** [S33] (~920★): агент внутри Blender (llama.cpp с CUDA ≥8 ГБ, Ollama, облака), LLaMA-Mesh,
  Hyper3D; последний функциональный релиз v0.7.1 — 14.04.2025, дальше только CI → фактически заморожен.
- **Коммерческие**: Chat Companion (19.90 USD, Blender 3.3–5.0, исполняет код из ответа), Vibe4D (подписка, Blender 4.4+),
  3D-Agent (подписка), BlendAI (19.95 USD) [S12].
- Мелкие бесплатные «чат + exec»: suryansh00001/Blender-Extension, Oli97430/UNIFICATION (Ollama, «100 % local»),
  haseebahmed295/Free-Gpt (через неофициальные «бесплатные» провайдеры — серая зона) и др. [S12].
- Сдвиг рынка: встроенные чаты проиграли MCP (внешний агент видит сцену и скриншоты); новые ассистенты либо добавляют свой
  MCP, либо становятся коммерческими приложениями и форками Blender.

### 4.3. «BlenderGPT» — три разных продукта

(1) аддон gd3kr/BlenderGPT (MIT, заброшен) [S32]; (2) облачный сервис blendergpt.org — генерация мешей по тексту и
фото с «Send to Blender», не связан с Blender Foundation; (3) платный аддон «Blender Copilot (Blender GPT)» на Superhive
(Blender 3.2–3.5, 2023) [S12]. Всегда указывай URL.

## 5. Аддоны генераторов 3D и текстур (только связь с Blender; качество для веба — агент G)

| Генератор / аддон | Связь с Blender | Blender | Платность, лицензия, ограничения | Живость (22.09.2026) |
|---|---|---|---|---|
| Meshy for Blender (офиц.) | ZIP-аддон + «DCC Bridge» — локальный HTTP-мост из веб-приложения Meshy | 4.2.6+, проверены 4.2.6, 5.0.1, 5.1.0, 5.2.0 | аддон бесплатный, **мост — только Meshy Pro+**; Linux официально не поддерживается | v0.6.1 [S12] |
| Tripo DCC Bridge (офиц.) | аддон-мост «Tripo Studio → Blender» (локальный порт) | 4.1.0+; **только Windows и Mac** | аккаунт Tripo | активен [S12] |
| Tripo для Blender на API (VAST-AI-Research/tripo-3d-for-blender) | текст/картинка/мультивид → 3D через API | — | MIT; платные кредиты | релиз 0.7.7 от 06.11.2025 [S12] |
| Hyper3D Rodin add-on (Deemos) | аддон + окно веб-страницы Rodin (нужен браузер Chrome ≥116) | 4.0+ | аккаунт, кредиты | документация обновлялась ~год назад [S12] |
| Hunyuan3D-2 (Tencent), `blender_addon.py` | аддон шлёт запросы на **локальный API-сервер** `localhost:8080` | `bl_info` 3.0+ | **лицензия модели не действует в ЕС, Великобритании и Южной Корее**; 6–16 ГБ VRAM | последний коммит 28.10.2025 [S34] |
| Hunyuan3DBlenderBridge (сообщество) | аддон к облачному Hunyuan3D 2.5 | 4.4+ | по коммитам загружает картинки на **публичные файлообменники** — риск приватности | 21.05.2026 [S12] |
| trellis_blender (FishWoWater) | аддон + свой MCP к локальному серверу TRELLIS/TRELLIS.2 | 3.6+ | без LICENSE; нужен свой GPU | 29.12.2025 [S12] |
| StableGen (sakalond) | аддон ↔ ComfyUI: текстурирование по ракурсам (SDXL, FLUX.1, Qwen Image Edit), меши через TRELLIS.2 | **4.2–4.5 или 5.1+; 5.0 не поддерживается** | GPL-3.0; свой GPU ≥8 ГБ (16+ для FLUX/Qwen) | релиз 12.06.2026 [S35] |
| Dream Textures (carson-katri) | Stable Diffusion внутри Blender | CUDA или Apple Silicon | GPL-3.0 | последний релиз v0.4.1 от 08.09.2024 — фактически не развивается [S12] |
| ComfyUI-BlenderAI-node (AIGODLIKE) | нодовый редактор ComfyUI в Blender | рекомендованы 3.5–4.0 | GPL-3.0 | v2.0.0 от 25.07.2025 [S12] |
| AI Render (benrugg) | Stable Diffusion по сцене (облако или локально) | 3.0+ (исправления для 5.0 — 12.2025) | MIT + платная версия | v1.1.1 от 28.12.2025 [S12] |
| Pallaidium (tin2tin) | генеративная «киностудия» в видеоредакторе (картинки, видео, звук) — не 3D | **5.2+**, Windows, NVIDIA 6–16 ГБ | GPL-3.0 | очень активен (20.09.2026) [S12] |
| Внутри MCP-серверов | mcp-for-blender — Rodin, Hunyuan3D [S15]; CallMeJones — Tripo, Meshy, TripoSR с подтверждением расходов [S27]; meshgen — LLaMA-Mesh, Hyper3D [S33]; форк Mixar — облачная генерация [S30] | — | ключи API | — |

Выводы для нас: (1) на нашей машине нет CUDA — локальные генераторы (TRELLIS, Hunyuan3D, StableGen) недоступны, остаются
облачные API по разрешению; (2) Tripo-мост не работает на Linux, Meshy на Linux официально не поддержан — для агента на
Linux путь только через API; (3) лицензию Hunyuan3D учитывать при работе с заказчиками из ЕС и Великобритании;
(4) проверку качества ассетов этих генераторов для веба (топология, UV, вес) делает агент G.

## 6. Процедурные генераторы на Blender

| Проект | ★, активность | Лицензия | Blender | Для нас |
|---|---|---|---|---|
| Infinigen (Princeton) [S36] | 7 274; релиз 2.0.0a2 от 27.08.2026 | BSD-3-Clause | **`bpy==4.2.0`, Python 3.11** — в 5.2 не ставится | источник идей и кода фабрик (3DCodeBench перевёл 212 фабрик в скрипты Blender 5.0); не поставщик веб-ассетов (сцена природы — 16M полигонов) |
| BlenderProc (DLR) [S37] | ~3 725 (по G5); релиз 2.8.0 от 22.10.2024; коммит 07.01.2026 | GPL-3.0 | сам скачивает Blender **4.2.1** | генерация обучающих данных; живость низкая; для сайтов не нужен |

## 7. Агентные IDE и пакеты навыков

### 7.1. Подключение официального сервера

- Claude Code (`.mcp.json`): `"command": "uv", "args": ["--directory", "…/blender_mcp/mcp", "run", "blender-mcp"]`; Codex
  (`~/.codex/config.toml`): `[mcp_servers.blender] command = "uv" args = ["run", "blender-mcp"] cwd = "…/blender_mcp/mcp"`;
  без клона — `uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.0#subdirectory=mcp" blender-mcp` (пин
  тега) [S38][S12]. В Claude Desktop — коннектор из каталога; аддон в Blender всё равно ставится отдельно [S6].
- Автоодобрение `mcp__blender__execute_blender_code` в `.claude/settings.json` — только в своём доверенном репозитории:
  агент исполняет Python без вопросов [S38].
- mcp-for-blender: `claude mcp add blender uvx blender-mcp`, `codex mcp add blender -- uvx blender-mcp`; «Only run ONE
  instance of the MCP server at a time» [S39].

### 7.2. VS Code без MCP

JacquesLucke/blender_vscode [S40] (742★, MIT, коммит 10.07.2026): запускает Blender **с окном**, «Run Script»,
перезагрузка аддонов, отладчик; «Running scripts from VS Code occasionally crashes Blender». Инструмент разработчика аддонов,
не ИИ-мост.

### 7.3. Пакеты навыков — главный тренд 2026

| Проект | ★, активность | Для кого | Суть | Blender |
|---|---|---|---|---|
| achimala/dream-loop [S41] | 1 514, 2026-09-09 | Codex (по README), другие сильные модели | цикл «целевая картинка → строить → субагент-критик сравнивает скриншоты»; «Blender MCP or scripting interface is preferred to computer use» | — |
| jangtrinh/design-os-3d-blender [S42] | 79, 2026-09-22 | Claude Code, Codex, Cursor… | контракт исполнения AGENT_OK/AGENT_FAIL, проверенная база bpy, «production gate», свой FastMCP | **5.2 LTS** |
| ifBars/blender-agent-studio [S43] | 43, 2026-09-22 | Codex-плагин | 11 навыков + локальный MCP, регрессии сцен, бенчмарки | **5.2 LTS** (тестируемая) |
| cth9191/blender-to-web [S44] | 66 (по G5), 2026-09-12 | Codex-навык + эталонный проект Three.js | **ровно наш сценарий «Blender → сайт»**; ассеты собраны скриптами CLI, MCP в сборке не сработал | 5.2.1 LTS |
| elithril/blender-kiln [S45] | 13, 2026-08-26 | Claude Code | mcp-for-blender + headless-скрипты + оптимизация gltf-transform/gltfpack | 4.4+, CI на 5.2 LTS |
| ra100/blender-claude-plugin [S46] | 15, 2026-04-29 | Claude Code, opencode | навыки Blender 5.x поверх официального MCP; без MCP — генерирует скрипты | 5.0/5.1 |

Ещё: arjun988/blender-skills («94 specialist Blender skills»), RobLe3/cc-blender-skill, ThanhNguyxnOrg/blendops (26
«целей установки», путь через официальный MCP, ahujasid или `blender -b`), MAX-786/claude-3d-harness, расширения Gemini
CLI (одно указывает прямо на порт аддона с `"trust": true` — без подтверждений) [S12].

### 7.4. Что работает без окна

`blender --background --python script.py` (и `--command`) — базовый путь, им пользуются blender-to-web, blender-kiln,
bforge, sandraschi; `bpy` из PyPI — эквивалент фона; официальный MCP — через `--command blender_mcp` [S2];
dcc-mcp-blender, sandraschi, minihellboy — фон штатно; mcp-for-blender, blender_vscode, чат-аддоны — только с окном [S12].

### 7.5. Независимые опыты и каталоги

- **Simon Willison** (TIL, 05.09.2026) [S47]: «Modern frontier models have got really good at using Blender»; агент в
  Codex получил одну строку — «Use Blender like this: …/Blender --background --python scene.py» — и сам собрал сцену,
  рендер и переиспользуемый навык «Blender Local». Без MCP и без окна.
- **Бенчмарк «Pixels to Polygons»** (R. Boltshauser, 2026) [S48]: 15 прогонов GPT-5.5/5.6 по одной картинке,
  Codex + Ubuntu + **Blender 5.0.1**, ручная рубрика «сначала геометрия» (40 геометрия, 25 композиция, 20 финиш,
  15 сходство); лучший — 92/100; **усилие размышлений немонотонно** (Terra xhigh 77 против Terra Ultra 70; Luna High 74
  против Luna xhigh 69 при трети токенов); «None of the 15 scripts loaded, sampled, calibrated or measured the reference…
  semantic reconstruction, not inverse graphics».
- Вместе с 3DCodeBench (Blender 5.0, повторы в Claude Code/Codex/Gemini CLI) и cth9191/blender-to-web это общий вывод
  практики 2026 г.: **агенты работают с Blender через фоновые скрипты + рендер для самопроверки**; MCP выигрывает там, где
  нужен живой сеанс с пользователем (осмотр открытой сцены, правки «на глазах») [S12].
- **Каталоги MCP отстают**: в PulseMCP (№1 — ahujasid), mcp.so, Glama и awesome-списках официального сервера Blender Lab
  нет (он на projects.blender.org, не на GitHub) — агент, ищущий «blender mcp» в каталоге, придёт к ahujasid [S12].

## 8. `bpy` из PyPI и `fake-bpy-module`

- **`bpy` 5.2.2** (15.09.2026) — «Blender as a Python module», мейнтейнер Blender Foundation, GPL-3.0 [S49].
  **Ровно одна версия Python на ветку**: 4.2–5.0 → 3.11; **5.1/5.2 → 3.13** (нужен свой venv). Колёса 5.2.2:
  manylinux_2_28 x86_64 **401.7 МБ**, macOS arm64, Windows x64/arm64; нет Linux ARM и macOS x86_64 с 5.0. Версии вне окна
  LTS удаляются с PyPI (архив — download.blender.org/pypi/bpy/).
- Ограничения (официальная страница API): «equivalent to running a script in background-mode»; стартовая сцена как
  `--factory-startup`; один .blend на процесс (параллель — `multiprocessing`); нет аргументов командной строки и обработчиков
  сигналов; `gpu`/`mathutils` импортировать после `bpy`; GUI-операторы (скриншот вьюпорта) недоступны; EEVEE на Linux — через
  GPU, как в `blender -b` [S49].
- Где пригодится: конвейеры без Blender-приложения (CI, проверки GLB, пакетная обработка), бэкенд bpy-dev/blender-mcp
  [S19]. На нашей машине проще `blender -b` (5.2.2 уже установлен; `../../scripts/3d/blender_run.py`).
- **`fake-bpy-module`** (nutti, MIT) [S50]: заглушки API для автодополнения и статической проверки; есть
  `fake-bpy-module-5.2` (сборка 20260730) и ежедневный `-latest`. Исполнения нет.

## 9. Исследовательские агенты с открытым кодом

| Проект | ★, активность | Blender | Что взять |
|---|---|---|---|
| VIGA [S51] | 1 308, MIT, 2026-02-25 | не указана | разделение инструментов «смотреть/менять», дифф + полный код, скользящая память, BlenderBench |
| LL3M [S52] | 554, 2026-03-07 | 4.4 | роли планировщик/поиск/кодер/критик/верификатор; база документации |
| 3DCodeBench [S53] | 99, Apache-2.0, 2026-06-02 | **5.0** | промты, справка API 5.0, протокол исполнения, 212 эталонных скриптов, логи 82 042 прогонов |
| BlenderGym [S54] | 45, 2025-07-08 | 3.x/4.x | 245 задач правки с метриками без судьи |
| BlenderRAG [S55] | 19, 2026-05-08 | не указана | аддон с поиском 3 похожих примеров |
| EZBlender [S56] | 7, 2026-07-17 | не указана | планировщик по доменам + отладчик |
| BlenderAlchemy [S57] | 2024-12-06 | 3.x | поиск с отбором, tweak/leap |

Все — источники приёмов и тестов, не готовые инструменты для 5.2: версии старше, ключи облачных моделей, обёртки
Infinigen. Подробности — `03-research-llm-3d.md`.

## 10. Безопасность интеграций

### 10.1. Модель угроз

| Риск | Где возникает | Что известно | Мера |
|---|---|---|---|
| **Исполнение произвольного кода** | любой MCP-мост с `execute_*code`, любой LLM-аддон с «выполнить скрипт» | официальный сервер прямо предупреждает: код LLM исполняется «without any guards in place to protect your data from removal or being sent to a remote location», советует ВМ [S13]; «песочница» Blender Lab блокирует только выход и сброс настроек [S4] | запускать Blender агента в отдельной учётной записи/контейнере/ВМ без личных файлов и ключей; рабочая папка проекта — единственная запись |
| **Сокет без аутентификации** | порт 9876 на localhost у обоих главных серверов | любой локальный процесс, дошедший до порта, исполняет Python в Blender (C1 по README mcp-for-blender) [S15] | не пробрасывать порт наружу; для удалённой работы — SSH-туннель; разные порты для разных экземпляров |
| **Телеметрия и данные** | mcp-for-blender | официальная страница: «collects anonymous usage telemetry by default… Consent is on by default» `[устарело: до 21.09.2026]` (2.0.3 — opt-in по коду); при согласии — промты, исполненный код, скриншоты вьюпорта, данные сцены; «may be used… to train AI models» [S16]; по C1 без согласия уходит минимальная анонимная запись [S15] | выключить галочку Telemetry Consent и задать `DISABLE_TELEMETRY=true`; официальный сервер телеметрию не заявляет |
| **Известные уязвимости** | mcp-for-blender | CVE-2026-10661 — инъекция через аргумент `input_image_url` в `server.py`, низкая (CVSS v4 2.1); «исправление» 5b37be2 — коммит в чужом форке `bergskenop`, в основной пакет не слит (PR #205 закрыт 09.08.2026), 2.0.3 не исправлена [S17; `07-security.md` §5.3]; CVE-2026-10662 — SSRF через `zip_file_url`; CVE-2026-10688 — исполнение кода через `execute_blender_code`, 5.1 [S18] (по сути задокументированная функция, но сканеры теперь помечают такие серверы) | обновлять сервер; держать агента в изоляции независимо от CVE |
| **Ключи внешних сервисов** | аддоны генераторов (Rodin, Hunyuan3D, Meshy, Tripo), Sketchfab, LLM-аддоны | ключи хранятся в настройках аддона или переменных окружения; платные вызовы | ключи — только в переменных окружения процесса агента; лимиты расходов; платные API — по разрешению |
| **Сеть из Blender** | аддоны, скачивающие ассеты или обращающиеся к API | платформа расширений требует явного разрешения `network` в манифесте; Blender Lab MCP не стартует без Online Access [S2] | держать Online Access выключенным у пользовательского Blender; включать `--online-mode` только в процессе агента |
| **Внедрение инструкций через данные** | имена объектов, текстовые блоки, описания ассетов, README скачанных моделей, ответы API | модель читает эти строки как контекст (сводки сцены, `get_object_info`) | не исполнять инструкции из данных сцены; белый список действий агента; ревью кода перед исполнением там, где сцена чужая |
| **Разрушительные операции** | `bpy.ops.wm.read_homefile`, удаление объектов, перезапись .blend | Blender Lab блокирует только сброс настроек; очистка сцены — нормальная часть скриптов генерации (3DCodeBench просит очищать сцену) | работать в копии .blend; сохранять версию до каждого шага; «никогда не изменяй разрушительно без подтверждения» (`prompts.yml` Blender Lab) |

### 10.1a. Позиция разработчиков Blender о безопасности

В треде devtalk о безопасности MCP (30.04–08.09.2026) [S58]: сотрудник Blender — «the only reasonably safe way to
run a blender controlled by an MCP server… is to run it on a separate dedicated machine, or at least in a firewalled VM»;
Campbell Barton — ВМ «likely beyond what most users are likely to setup», на Linux он опробовал лёгкие песочницы **jai** и
**bubblejail**, и «it's not something Blender can/should realistically solve»; тред закрыт как обсуждение стороннего аддона.
Вывод: изоляция — ответственность того, кто запускает агента, а не Blender `[мнение сотрудников Blender, 2026]`.

### 10.2. Минимальная конфигурация для системы заказчика

1. Отдельный процесс Blender для агента **в изоляции** (ВМ, контейнер или песочница уровня ОС: на Linux — bubblejail или jai [S58]): `blender -b --factory-startup --online-mode` + мост на нестандартном порту
   (не 9876, если у пользователя открыт свой Blender с MCP-аддоном) [S2].
2. Рабочая папка проекта как единственное место записи; исходные .blend — только копии.
3. Телеметрия выключена везде, где она есть; ключи платных API — вне аддонов, с лимитом расходов.
4. Журнал всех исполненных скриптов (код + stdout + traceback) — для отладки и регрессии (так делает 3DCodeBench).

## 11. Сравнение и рекомендация для системы заказчика

| Вариант | Фон без окна | Документация 5.2 | Ассеты/генераторы | Безопасность | Живость | Для чего |
|---|---|---|---|---|---|---|
| **Официальный MCP Blender Lab** | да (`--command`, проверено) | встроена | нет | слабая «песочница»; Online Access; без телеметрии | высокая (BF) | **основной мост агента-дизайнера без окна** |
| mcp-for-blender (ahujasid) | нет (самодельный мост) | `bpy_api_lookup` | Poly Haven, Sketchfab, Poly Pizza, Rodin, Hunyuan3D | телеметрия по умолчанию, протокол 7/9 у пользователя | очень высокая | интерактив с окном; ассеты и генераторы по разрешению |
| `blender -b --python` + свои утилиты | да | через справку/эксперименты | любые через код | контролируем сами | — | детерминированные сборки, CI, пакетные рендеры (уже есть `99-raw/tools/`) |
| bpy-dev/blender-mcp | да | поиск по живому API | нет | изоляция процессов | developer preview | запасной вариант, если официальному не хватит `_for_cli` |
| PatrykIti/blender-ai-mcp, bforge | да/частично | — | нет | без свободного exec | средняя | идеи: утверждения и белые списки |
| Пакеты навыков (design-os, agent-studio, blender-to-web) | через CLI/MCP | свои базы | разные | зависят от моста | высокая, но мелкие проекты | источники рецептов и контрактов исполнения |

**Рекомендация** `[мнение C2 на основе документации, эксперимента C2/02 и исследований]`:
1. **Основной путь агента** — фоновый Blender 5.2.2 с официальным MCP-мостом Blender Lab (`--online-mode --command
   blender_mcp`, отдельный порт, рабочая копия .blend) **или** прямые скрипты `blender -b --python` через утилиты базы;
   выбор — по месту: MCP удобен для пошаговой интерактивной сборки агентом, скрипт — для воспроизводимой пересборки
   «с нуля по параметрам».
2. **mcp-for-blender** оставить для сеансов с окном и для ассетов/генераторов — после обновления аддона до протокола 9 и
   с выключенной телеметрией (решение за заказчиком, разбор — C1).
3. Встроенные чат-аддоны не использовать; LLM-аддоны из магазинов — только после чтения кода.
4. Из экосистемы навыков взять идеи: контракт «AGENT_OK/AGENT_FAIL», утверждения `scene_assert_*`, гейты качества перед
   экспортом, пин версий MCP SDK.
5. Условия пересмотра: если официальный сервер получит интеграции ассетов, или mcp-for-blender — штатный фон, или
   Blender Foundation изменит политику (Blender Conference 2026, SIG «AI-enabled tools», 24.09.2026) — обновить раздел.

## Частые ошибки

1. **Считать, что «Blender умеет ИИ»**: в Blender нет встроенной связи с моделями и генеративных функций; всё — внешние
   мосты и аддоны [S13][S7].
2. **Думать, что официальный MCP требует окна**: документирован путь с окном, но `--command blender_mcp` работает в фоне
   [S2].
3. **Запускать официальный мост без `--online-mode`** в фоне — не стартует [S2].
4. **Два MCP-аддона на порту 9876** в одном Blender или двух процессах — конфликт [S2][S15].
5. **Возвращать данные через `print`** в официальном `execute_blender_code` — нужен `dict` в `result`; `print` уйдёт в
   `stdout` [S2].
6. **Надеяться на переменные между вызовами** — пространство имён новое при каждом вызове; живут только данные `bpy` [S2].
7. **Выставлять мост в сеть** (`0.0.0.0`, localtunnel) — удалённое исполнение кода [S21][S23][S12].
8. **Автоодобрять `execute_blender_code`** в настройках агента в чужом репозитории [S38].
9. **Путать «BlenderGPT»** — три разных продукта [S32][S12].
10. **Ставить Infinigen/BlenderProc в Blender 5.2** — они на 4.2 [S36][S37].
11. **Ставить `bpy` 5.2 в Python 3.11/3.12** — только 3.13 [S49].
12. **Искать ИИ-аддоны на extensions.blender.org** — их там нет по правилам платформы [S10][S12].
13. **Оставлять телеметрию mcp-for-blender включённой** в проектах заказчика [S15].
14. **Обновлять MCP SDK вслепую**: официальный сервер пинует `mcp<2` после выхода несовместимого SDK 2.x [S4][S12].
15. **Ошибка модели по памяти**: предлагать BlenderGPT или «Blender Copilot» как актуальные инструменты — они заброшены с
    2023 г.; не знать про официальный сервер Blender Lab (появился в 2026 г.).
16. **Брать сервер из каталога MCP**: в PulseMCP, mcp.so, Glama и awesome-списках официального сервера нет — ставь его по
    прямой ссылке projects.blender.org [S12].
17. **Не обновлять mcp-for-blender** после CVE-2026-10661 и CVE-2026-10688 [S17][S18].
18. **Ставить StableGen на Blender 5.0** — не поддерживается (нужны 4.2–4.5 или 5.1+) [S35].
19. **Использовать Hunyuan3D-2 в проектах для ЕС, Великобритании или Южной Кореи** — лицензия там не действует [S34].
20. **Верить, что без MCP агент не справится**: независимые опыты 2026 г. работают фоновыми скриптами и рендером
    [S47][S48].

## Чек-лист

- [ ] Мост агента — фоновый Blender 5.2.2 (официальный MCP через `--command` или `blender -b --python`), отдельный порт?
- [ ] `--online-mode` включён только у процесса агента, у пользовательского Blender — по его настройке?
- [ ] Телеметрия выключена во всех установленных MCP-аддонах и серверах?
- [ ] Мост слушает только `127.0.0.1`, не `0.0.0.0`?
- [ ] Процесс агента работает в изолированной среде с одной рабочей папкой, без личных файлов и ключей?
- [ ] Ключи платных API — в переменных окружения процесса, с лимитом расходов, вызовы — по разрешению?
- [ ] При ошибке API агент ищет в справке 5.2 (официальный сервер) до повторной попытки?
- [ ] Версии зависимостей закреплены (тег официального сервера, `mcp<2`, версия `bpy`)?
- [ ] Установленные MCP-серверы обновлены после известных CVE, их страницы уязвимостей проверены?
- [ ] Лицензии генераторов проверены на географию заказчика (Hunyuan3D — не ЕС, Великобритания, Южная Корея)?
- [ ] Каждый сторонний аддон/сервер прочитан по коду, указаны лицензия, звёзды, дата коммита?
- [ ] Журнал исполненного кода (код + stdout + traceback) сохраняется?

## Открытые вопросы и противоречия

1. **Официальный сервер и фон**: документация и сторонние авторы говорят «нужен запущенный Blender с аддоном»
   [S38]; код и эксперимент C2/02 показывают штатный фон через `--command blender_mcp`. Позиция базы: фон работает
   (проверено на 5.2.2), но в документации Blender Lab этот путь описан только в `cli.py` — следить за изменениями.
2. **Телеметрия официального сервера**: не заявлена и в прочитанных файлах не найдена; полный аудит всех 29 модулей не
   проводился.
3. **Звёзды официального сервера (25★)** не отражают реальную аудиторию: основное распространение — каталог коннекторов
   Claude и `.mcpb`; число установок неизвестно.
4. **Позиция Blender Foundation может измениться**: SIG «AI-enabled tools and workflows» на Blender Conference 24.09.2026;
   «Guidelines for AI-enabled features» — обсуждение, а не окончательный документ.
5. **Инвентаризация генераторов** (Meshy, Tripo, Rodin, Hunyuan3D, TRELLIS, Dream Textures, StableGen) в этом файле неполна —
   передано агенту G (волна 2).
6. **Не проверено C2 по коду**: лицензии части мелких проектов (у нескольких нет файла LICENSE), реальная работоспособность
   навыков design-os-3d-blender и blender-agent-studio на 5.2.2.

## Источники

- [S1] Эксперимент C2/00: живость репозиториев (звёзды, лицензии — GitHub API; даты последних коммитов и релизов — Atom-ленты github.com), 22.09.2026 — 99-raw/experiments/C2/00-repo-liveness/repos.json.
- [S2] Эксперимент C2/02: официальный аддон Blender Lab MCP v1.0.3 в фоновом Blender 5.2.2 — 99-raw/experiments/C2/02-blender-lab-mcp-headless/README.md.
- [S3] Blender Foundation. Introducing Blender Lab (F. Siddi), 07.11.2025. https://www.blender.org/news/introducing-blender-lab ; Blender Lab. https://www.blender.org/lab/ — площадка экспериментальных проектов, «AI and ML technologies, starting with a Blender MCP server». Первоисточник (по G5).
- [S4] Blender Lab. lab/blender_mcp (исходный код: readme.md, readme_tools.rst, readme_local_llm.rst, prompts.yml, weak_sandbox.py, cli.py, execute_blocking.py, mcp_to_blender_server.py, blender_manifest.toml, pyproject.toml). https://projects.blender.org/lab/blender_mcp — GPL-3.0-or-later; 25★, 23 форка (Gitea API 22.09.2026); v1.0.3 от 11.09.2026; последний коммит 11.09.2026 (Campbell Barton). Прочитано; первоисточник.
- [S5] Blender Foundation. Blender Lab Activity Report – Q1 2026 (D. Felinto), 24.04.2026. https://www.blender.org/development/blender-lab-activity-report-q1-2026/ — «The Blender project keeps a firm artist-centric policy when it comes to AI». Первоисточник (по G5).
- [S6] Anthropic. Claude for Creative Work. 28.04.2026, правка 01.05.2026. https://www.anthropic.com/news/claude-for-creative-work — официальный коннектор Blender в Claude, пожертвование Blender. Прочитано целиком; первоисточник.
- [S7] Blender Foundation. Upcoming Blender Development Fund and AI Policies (F. Siddi), 01.05.2026. https://www.blender.org/news/upcoming-blender-development-fund-and-ai-policies/ — разовое пожертвование Anthropic вместо членства в фонде; «No generative AI functionality is currently available or planned to be integrated in Blender». Цитаты сверены C2.
- [S8] Siddi F. Guidelines for AI-enabled features. devtalk.blender.org, 02.06.2026. https://devtalk.blender.org/t/guidelines-for-ai-enabled-features/45354 — нет планов генеративных функций; требования «local and sovereign», «IP conscious», только вспомогательные функции; исследования — в Blender Lab. Цитаты сверены C2 через JSON Discourse.
- [S9] Blender Developer Handbook. AI Contributions Policy (2026). https://developer.blender.org/docs/handbook/contributing/ai_contributions/ — правила ИИ-вкладов в код Blender; не распространяется на расширения. По G5.
- [S10] Blender Extensions Platform. Terms of Service (обновлено 10.08.2026). https://extensions.blender.org/terms-of-service/ — запрет внешних ключей/регистраций, блокирующих функции (3.10); разрешение network и уважение online_access (4.1–4.2); без отправки данных без согласия (4.5); без загрузки удалённого кода (5.1). Цитаты сверены C2.
- [S11] Blender Manual 5.2. Extensions: Add-ons; Getting Started (манифест, permissions). https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html — проверка bpy.app.online_access, флаги --online-mode/--offline-mode. Документация.
- [S12] Разведка ландшафта помощником C2 (G5), 22.09.2026: поиск GitHub «blender mcp» (879 репозиториев), каталоги MCP, страницы репозиториев и Atom-ленты; заметки scratchpad C2 → перенесены в 99-raw/notes/wave1/C2-notes.md. Звёзды/лицензии/даты ключевых репозиториев перепроверены C2 через GitHub API (эксперимент C2/00).
- [S13] Blender Foundation, Blender Lab. MCP Server (страница проекта). 2026. https://www.blender.org/lab/mcp-server/ — установка, предупреждение о безопасности, примеры анализа сцен. Прочитано целиком 22.09.2026; первоисточник.
- [S14] Ahuja S. и участники. mcp-for-blender (бывш. blender-mcp). https://github.com/ahujasid/mcp-for-blender — MIT; 29 193★, последний коммит 2026-09-21 (GitHub API 22.09.2026); пакет PyPI mcp-for-blender 2.0.3. Детальный разбор — файл 01 (агент C1).
- [S15] Агент C1, волна 1. 04-ai-agents-mcp/01-mcp-for-blender.md и заметки 99-raw/notes/wave1/C1-notes.md — разбор сервера mcp-for-blender 2.0.3 и аддона по исходникам и вживую.
- [S16] MCP for Blender. Telemetry: What Is Collected and How to Opt Out. https://mcp-for-blender.com/reference/telemetry — «collects anonymous usage telemetry by default… Consent is on by default»; при согласии — промты, исполненный код, скриншоты вьюпорта, данные сцены; «may be used… to train AI models»; выключение — галочка Telemetry Consent или DISABLE_TELEMETRY=true. Прочитано C2 22.09.2026.
- [S17] GitHub Advisory Database. GHSA-qqw9-95ww-prfm / CVE-2026-10661: «A vulnerability has been found in ahujasid blender-mcp up to 7636d13… The manipulation of the argument input_image_url leads to injection». NVD 02.06.2026, GitHub 03.06.2026; Low, CVSS v4 2.1; исправление — коммит 5b37be2 (форк bergskenop). https://github.com/advisories/GHSA-qqw9-95ww-prfm — прочитано C2.
- [S18] OpenCVE. CVE-2026-10688: уязвимость в функции execute_blender_code сервера blender-mcp, исполнение произвольного кода; «With a CVSS score of 5.1 the vulnerability is considered moderate, but the exploit is possible remotely and publicly available». https://app.opencve.io/cve/CVE-2026-10688 — прочитано C2.
- [S19] bpy-dev/blender-mcp. https://github.com/bpy-dev/blender-mcp — GPL-3.0, 93★, коммит 2026-09-12 (API, C2/00): форк официального Blender Lab MCP, `_for_cli` в подпроцессах, бэкенд bpy из PyPI, BlenderBench.
- [S20] HoldMyBeer-gg/blend-ai. https://github.com/HoldMyBeer-gg/blend-ai — AGPL-3.0, 142★, релиз 2026-09-21: 175 инструментов, «zero telemetry», протестирован на Blender 5.1.
- [S21] dhakalnirajan/blender-open-mcp. https://github.com/dhakalnirajan/blender-open-mcp — MIT, 117★, коммит 2026-09-04: MCP с выбором поставщика модели (Ollama, LM Studio, llama.cpp, OpenAI-совместимые); по умолчанию слушает 0.0.0.0:8000.
- [S22] PatrykIti/blender-ai-mcp. https://github.com/PatrykIti/blender-ai-mcp — Apache-2.0, 57★, релиз 2026-05-04: курированные инструменты вместо свободного Python, `scene_measure_*`/`scene_assert_*`, E2E на Blender 5.0.
- [S23] seehiong/blender-mcp-bridge. https://github.com/seehiong/blender-mcp-bridge — MIT, 56★, релиз 2026-09-13: 93 инструмента, HTTP MCP, по умолчанию MCP_BRIDGE_HOST = 0.0.0.0.
- [S24] sandraschi/blender-mcp. https://github.com/sandraschi/blender-mcp — MIT, 46★, коммит 2026-09-18: по умолчанию headless (`blender --background`).
- [S25] dcc-mcp/dcc-mcp-blender. https://github.com/dcc-mcp/dcc-mcp-blender — MIT, 37★, релиз 2026-09-22: MCP (Streamable HTTP) внутри Blender, CI на 5.2.1 LTS и 4.5.13 LTS, headless-загрузчик.
- [S26] djeada/blender-mcp-server. https://github.com/djeada/blender-mcp-server — MIT, 27★, коммит 2026-06-21: транспорт bridge или headless, safe mode.
- [S27] CallMeJones/blender-agent-bridge. https://github.com/CallMeJones/blender-agent-bridge — GPL-3.0, 22★, релиз 2026-08-11: превью правок с Commit/Revert, Python выключен до «session trust», файлы только в каталоге проекта; проверен на 4.2/4.5/5.1.
- [S28] minihellboy/claude-blender. https://github.com/minihellboy/claude-blender — MIT, 5★, коммит 2026-07-30: MCP SDK v2, headless-скрипт, `.mcp.json` для Claude Code.
- [S29] lxsolutions/studio-foundation (bforge). https://github.com/lxsolutions/studio-foundation — source-available PolyForm Perimeter, 26★, коммит 2026-09-14: headless-демон Blender, 138 операций по белому списку, воспроизводимая регенерация, выход glTF.
- [S30] Mixar-AI/mixar-app. https://github.com/Mixar-AI/mixar-app — GPL-3.0 (клиент), 255★, релиз 2026-09-07: форк Blender 5.0 со встроенным агентом и облачным бэкендом.
- [S31] VxASI/blender-mcp-vxai. https://github.com/VxASI/blender-mcp-vxai — MIT, 299★, последний коммит 2025-03-21 — заброшен.
- [S32] gd3kr. BlenderGPT. https://github.com/gd3kr/BlenderGPT — MIT, 4 984★, последний коммит 2023-06-10 (GitHub API 22.09.2026). Заброшен.
- [S33] huggingface/meshgen. https://github.com/huggingface/meshgen — MIT, ~920★ (по странице), последний функциональный релиз v0.7.1 2025-04-14, далее CI-коммиты (2026-09-17): агент внутри Blender, LLaMA-Mesh.
- [S34] Tencent Hunyuan. Hunyuan3D-2: LICENSE и blender_addon.py. https://github.com/Tencent-Hunyuan/Hunyuan3D-2 — аддон шлёт запросы на локальный сервер localhost:8080, bl_info blender (3, 0, 0); лицензия «DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA». Проверено C2 по сырым файлам.
- [S35] sakalond. StableGen. https://github.com/sakalond/StableGen — GPL-3.0, ~918★ (по G5); ComfyUI-текстурирование и меши через TRELLIS.2; «Blender 4.2 – 4.5… or Blender 5.1+… Blender 5.0 is not supported». Требования проверены C2.
- [S36] Princeton VL. Infinigen. https://github.com/princeton-vl/infinigen — BSD-3-Clause, 7 274★, последний коммит и релиз 2.0.0a2 от 2026-08-27 (GitHub API/Atom 22.09.2026).
- [S37] DLR-RM. BlenderProc. https://github.com/DLR-RM/BlenderProc — GPL-3.0; релиз 2.8.0 от 22.10.2024, последний коммит 07.01.2026 (Atom, C2/00); скачивает Blender 4.2.1 (по G5: InstallUtility.py).
- [S38] Müller J.-H. Blender MCP config for Codex, Claude Code and OpenCode. Блог, 22.07.2026. https://jan-hendrik-mueller.de/blog/blender-mcp-config-codex-claude-code-opencode/ — конфиги официального сервера для агентных CLI. [мнение/практика] По G5.
- [S39] mcp-for-blender.com. MCP clients. https://mcp-for-blender.com/mcp-clients — подключение сервера ahujasid к Claude, Codex, Cursor, VS Code. По G5.
- [S40] Lucke J. blender_vscode. https://github.com/JacquesLucke/blender_vscode — MIT, 742★, коммит 2026-07-10 (API, C2/00): расширение VS Code для разработки аддонов.
- [S41] achimala/dream-loop. https://github.com/achimala/dream-loop — MIT, 1 514★, коммит 2026-09-09 (API, C2/00): навык «целевая картинка → строить → критик».
- [S42] jangtrinh/design-os-3d-blender. https://github.com/jangtrinh/design-os-3d-blender — MIT, 79★, коммит 2026-09-22 (API): навыки и FastMCP для Blender 5.2 LTS.
- [S43] ifBars/blender-agent-studio. https://github.com/ifBars/blender-agent-studio — MIT, 43★, коммит 2026-09-22 (API): Codex-плагин, Blender 5.2 LTS.
- [S44] cth9191/blender-to-web. https://github.com/cth9191/blender-to-web — без LICENSE, 66★ (по G5; API не ответил), коммит 2026-09-12: навык «Blender 5.2.1 → Three.js».
- [S45] elithril/blender-kiln. https://github.com/elithril/blender-kiln — MIT, 13★, релиз 2026-08-26: конвейер ассетов для Claude Code.
- [S46] ra100/blender-claude-plugin. https://github.com/ra100/blender-claude-plugin — MIT, 15★, коммит 2026-04-29: навыки Blender 5.x для кодовых агентов поверх официального MCP.
- [S47] Willison S. Using Blender with coding agents on macOS. TIL, 05.09.2026. https://til.simonwillison.net/llms/blender-coding-agents-macos — «Modern frontier models have got really good at using Blender»; агент в Codex через `Blender --background --python scene.py`; навык «Blender Local». [практика] Прочитано C2.
- [S48] Boltshauser R. Pixels to Polygons — GPT-5.6 Blender benchmark. 2026. https://blender-bench.ralfboltshauser.com/ — 15 прогонов по одной картинке, Codex + Ubuntu + Blender 5.0.1, ручная рубрика 40/25/20/15; «None of the 15 scripts loaded, sampled, calibrated or measured the reference»; усилие размышлений немонотонно. [практика, один автор] Прочитано C2.
- [S49] PyPI. bpy — Blender as a Python module. https://pypi.org/pypi/bpy/json (22.09.2026) — версия 5.2.2 от 15.09.2026, Python ==3.13.*; колёса manylinux_2_28 x86_64 401.7 МБ, macOS arm64, Windows x64/arm64. Документация: https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html. По G5.
- [S50] nutti. fake-bpy-module. https://github.com/nutti/fake-bpy-module ; PyPI fake-bpy-module-5.2 (20260730) — заглушки bpy для автодополнения и статической проверки. По G5.
- [S51] Yin S. et al. VIGA. arXiv 2601.11109, 2026; github.com/Fugtemypt123/VIGA (1 308★, MIT, коммит 2026-02-25). Прочитано целиком.
- [S52] Lu S. et al. LL3M: Large Language 3D Modelers. arXiv 2508.08228, 2025; github.com/threedle/ll3m (554★, лицензия не указана SPDX, коммит 2026-03-07). Прочитано целиком.
- [S53] Gao Y. et al. (Google DeepMind, USC). 3DCodeBench: Benchmarking Agentic Procedural 3D Modeling Via Code. arXiv 2606.01057, 2026 — перечень MCP-серверов и агентов Blender во введении; прогон Claude Code/Codex/Gemini CLI с Blender 5.0. Прочитано целиком.
- [S54] Gu Y. et al. BlenderGym. CVPR 2025; github.com/richard-guyunqi/BlenderGym-Open (45★, коммит 2025-07-08). Прочитано целиком.
- [S55] Rondelli M. et al. BlenderRAG. arXiv 2605.00632, 2026; github.com/MaxRondelli/BlenderRAG (19★, коммит 2026-05-08). Прочитано целиком.
- [S56] Wang H. et al. EZBlender. arXiv 2601.07143, 2026; github.com/Aztech-Lab/EZ_Blender (7★, коммит 2026-07-17). Прочитано целиком.
- [S57] Huang I. et al. BlenderAlchemy. ECCV 2024; github.com/ianhuang0630/BlenderAlchemyOfficial (коммит 2024-12-06). Прочитано целиком.
- [S58] devtalk.blender.org. «Blender MCP Server after Claude: MCP security for Blender scripting — 3D-Agent notes», 30.04–08.09.2026, 13 сообщений. https://devtalk.blender.org/t/45131 — сотрудники Blender: безопасно только на отдельной машине или ВМ за файрволом (Baardaap, #5); на Linux опробованы jai и bubblejail, песочница — «not something Blender can/should realistically solve» (Campbell Barton, #9); тред закрыт (Brecht Van Lommel, #13). Цитаты сверены C2 через JSON.
