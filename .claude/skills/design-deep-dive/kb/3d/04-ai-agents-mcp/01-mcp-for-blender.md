# MCP for Blender (mcp-for-blender 2.0.3): разбор по исходникам и вживую

Волна 1 · агент C1 · 22–23.09.2026 · прочитано целиком: 9 файлов сервера и аддона (≈11 000 строк), аддон протокола 7,
README, TERMS, страница телеметрии, GitHub (API, 6 issues, PR, история коммитов), записи CVE (GHSA, NVD, OpenCVE),
исходники Blender 5.2.2 и CPython 3.13, замер mcp-context-cost; 26 источников · 14 экспериментов C1
(`99-raw/experiments/C1/01…14`) · Blender 5.2.2 LTS, сервер `mcp-for-blender` 2.0.3, аддон протокола 9 (bl_info 1.7),
библиотека `mcp` 1.30.0, three r186. Сравнение с официальным сервером Blender Lab — по файлу
`02-integrations-landscape.md` (C2) и эксперименту C2/02.

## Выжимка для агента

1. **Устройство**: сервер `mcp-for-blender` (stdio, FastMCP) держит одно TCP-соединение с аддоном в Blender
   (127.0.0.1:9876); аддон исполняет команды в главном потоке Blender из таймера каждые 50 мс. → §1.2 `[исходник]`
2. **В фоне (`blender -b`) штатно не работает**: аддон отказывается стартовать; мост C1 (копия аддона + ручной цикл
   `_drain_command_queue`) даёт все 32 инструмента без окна. → §8 `[проверено]`
3. **Первый вызов — `get_addon_status`**: ждать `protocol_version: 9`, `telemetry_consent: false`; после перезапуска
   Blender первый ответ бывает ложным («Addon handshake failed») — повторить. → §3.1 `[проверено: 04, 09]`
4. **`execute_blender_code` — новое пространство имён `{"bpy": bpy}` на каждый вызов**: переменные, функции и импорты
   не живут между вызовами, живут только данные `bpy.data`; `mathutils` надо импортировать. → §3.4 `[проверено: 02]`
5. **Вывод — только `print` в stdout**: значение последнего выражения и stderr не возвращаются; итог печатай одной
   последней строкой JSON. → §3.4 `[проверено: 02, 08]`
6. **`if __name__ == "__main__":` тихо не выполняется** (`__name__ == 'builtins'`) — ни ошибки, ни результата. → §3.4 `[проверено: 02]`
7. **Никогда `sys.exit()`, `exit()`, `quit()`**: в Blender с окном это закрывает Blender без сохранения; `raise
   KeyboardInterrupt` снимает таймер — мост слушает порт, но больше ничего не исполняет. → §3.4 `[проверено: 03, 09]`
8. **«Communication error with Blender: {…"traceback"…}» — ошибка в твоём коде, не в связи**; строка ошибки —
   `File "<string>", line N`. → §2.4 `[проверено: 04, 14]`
9. **Тексты сбоев различимы**: «Not connected to Blender» — Blender не слушает; «No data received» через 180 с —
   Blender занят, заглох или запущен в фоне без моста; «Connection closed before receiving any data» — Blender закрылся.
   → §2.4 `[проверено: 14]`
10. **Вызов дольше 180 с теряет ответ**, Blender всё равно доисполнит код, следующая команда ждёт его окончания; держи
    вызов < 30 с. → §2.3 `[проверено: 04]`
11. **Ответ длиннее ~5–6 МБ обрывается** (сервер перечитывает JSON после каждых 8 КБ, аддон отправляет с таймаутом 1 с) —
    не печатай дампы сцены и base64. → §2.3 `[проверено]`
12. **`get_scene_info` показывает только первые 10 объектов** (имя, тип, location до 0,01 м) — состав и габариты сцены
    проверяй своим аудитом кодом. → §3.2 `[проверено: 02, 08]`
13. **`get_object_info`: габарит учитывает модификаторы, счётчики вершин и граней — нет** (исходный меш). → §3.3 `[проверено: 02]`
14. **`get_viewport_screenshot` — снимок вьюпорта (вид пользователя, Solid, оверлеи), а не рендер**; в фоне работает
    только после `gpu.init()`, материалы там серые; вид для сайта проверяй рендером в PNG и чтением файла. → §3.5
    `[проверено: 01, 02, 04, 09]`
15. **`bpy_api_lookup` занижает динамические перечисления** (`RenderSettings.engine` → только `BLENDER_EEVEE`,
    `view_transform` → `NONE`) и отдаёт до 80 КБ на тип — спрашивай `Type.prop`, а не `Type`. → §3.6 `[проверено: 02]`
16. **`describe_node_type` не сообщает `enabled` сокетов**: у Mix все 10 входов при любом `data_type` — ставь режим, потом
    бери сокет по имени. → §3.7 `[проверено: 02]`
17. **`export_scene` = glTF-экспорт по умолчанию + применение модификаторов**: без Draco/Meshopt, без ламп, меняет
    выделение пользователя; после него — `gltf-transform` и `gltf_check.py`. → §3.8 `[проверено: 02, 04]`
18. **Интеграции включаются свойством сцены** (`scene.blendermcp_use_polyhaven = True` и т. п.) — кодом, без
    перезапуска; флаг сохраняется в .blend. → §3.9 `[проверено: 04]`
19. **Poly Haven — без ключа, CC0**; поиск семантический и промахивается («brushed aluminium» → ржавый металл) — смотри
    превью; скачанный текстурный материал пропадёт при сохранении, пока не применён. → §3.9 `[проверено: 04]`
20. **Sketchfab и Poly Pizza — нужен ключ; Hyper3D Rodin и Hunyuan3D — платные генераторы** (у Rodin в аддоне пробный
    ключ `vibecoding`, расход — только по разрешению). → §3.10–3.13 `[исходник]`
21. **`set_texture` удаляет все слоты материалов объекта**; загрузки Sketchfab и Poly Pizza оставляют неприменённый
    масштаб на корневых объектах. → §3.9–3.11 `[исходник]`
22. **Сокет без аутентификации, в окне сервер поднимается сам** при запуске Blender (`auto_start` = True) — любой
    локальный процесс может исполнить Python в Blender пользователя. → §6.1 `[исходник, проверено: 09]`
23. **CVE-2026-10661 (чтение любого файла через `input_image_url` Hunyuan3D) в 2.0.3 не исправлена, SSRF (#203, CVE-2026-10662) — тоже;
    безопасный режим их не закрывает.** → §6.2 `[проверено]`
24. **CVE-2026-10688 — это сам свободный `exec`**; `BLENDER_MCP_SAFE_MODE=1` фильтрует только `execute_blender_code`
    и отвергает 23 из 40 типичных фрагментов (lambda, numpy, `time`, `class`, `getattr` с вычисляемым именем). → §4
    `[проверено: 07]`
25. **Телеметрия**: минимальная анонимная запись уходит по умолчанию (гасит только `DISABLE_TELEMETRY=true`); полное
    согласие (промты, код, скриншоты, сцена, ручные правки — для обучения ИИ) до 21.09.2026 было включено по умолчанию,
    в 2.0.3 выключено; сайт на 23.09 всё ещё пишет «Consent is on by default». → §5 `[исходник + документация]`
26. **`user_prompt` — поле датасета траекторий**, Blender его не читает; передавай короткую нейтральную строку задачи,
    не личные данные (обязателен только у `get_scene_info`). → §5.3 `[исходник]`
27. **Изоляция — ответственность того, кто запускает агента**: сотрудники Blender советуют отдельную машину или ВМ; мосту
    агента — отдельный процесс Blender, рабочая папка, копии .blend. → §6.4 `[мнение сотрудников Blender, через C2]`
28. **Аддон протокола 7 с сервером 2.0.3**: поиск Poly Haven сломан целиком, HDRI перезаписывает чужой мир, альбедо
    текстур помечается Non-Color. У пользователя обновлено до 9 в 22:51 22.09.2026. → §7 `[исходник]`
29. **Цена контекста**: 32 инструмента = 9 285 токенов o200k (оценка ≈14 500 токенов Claude) в каждом запросе клиентов без
    отложенной загрузки; Claude Code платит только имена и инструкции (≈500). → §9 `[проверено: 06]`
30. **Официальный MCP Blender Lab (v1.0.3)**: штатный фон (`--command blender_mcp`), справка 5.2 внутри, блок
    `sys.exit`, телеметрии нет, ассетов нет; порт по умолчанию тоже 9876. → §10 `[документация, проверено C2/02]`
31. **Рекомендация**: агент без окна — официальный сервер Blender Lab или `blender -b --python`; mcp-for-blender — для
    сеансов с окном и Poly Haven, с `DISABLE_TELEMETRY=true` и выключенными Hunyuan/Hyper3D. → §10.3 `[мнение C1]`
32. **Промт `asset_creation_strategy` ставит библиотеки и генераторы впереди кода** — для стилизованных hero-объектов
    сайта это неверный порядок; источник геометрии выбирай по протоколу `04 §4`. → §3.14 `[исходник, мнение]`
33. **Undo через MCP нет**: перед разрушительным шагом — `save_as_mainfile(copy=True)` в рабочую папку. → §11 `[проверено: 04]`
34. **Один Blender — один агент**: команды всех клиентов идут одной очередью, а stdout чужих потоков попадает в ответ
    (`redirect_stdout` глобален). → §2.5 `[проверено: 08]`

## 1. Что это и как устроено

### 1.1. Компоненты и версии

| Часть | Что | Версия, путь |
|---|---|---|
| MCP-сервер | пакет PyPI `mcp-for-blender` (бывш. `blender-mcp`), вход `mcp-for-blender = blender_mcp.server:main`, FastMCP «BlenderMCP» | 2.0.3 от 21.09.2026; зависимости `mcp>=1.9,<2` (в окружении 1.30.0), `httpx>=0.27`; Python ≥3.10 [S1][S2] |
| Модули сервера | `server.py` (2 207 строк, 32 инструмента и промт), `addon_manager.py` (516), `safe_mode.py` (988), `telemetry.py` (385), `telemetry_decorator.py` (487), `trajectory.py` (1 453), `consent_prompt.py` (220), `config.py` (26) | `~/.cache/uv/archive-v0/wTx2X5JSXJEWP78L/lib/python3.12/site-packages/blender_mcp/` |
| Аддон | один файл `addon.py` → ставится как `blender_mcp.py`; «Interface: MCP for Blender»; bl_info `version (1, 7)`, `blender (3, 0, 0)` | в пакете `bundled/addon.py` (5 344 строки, `ADDON_PROTOCOL_VERSION = 9`) [S9] |
| Аддон у пользователя | `~/.config/blender/5.2/scripts/addons/blender_mcp.py` | до 22.09.2026 22:51 — протокол 7 (4 673 строки, копия `99-raw/experiments/_orchestrator/mcp-addon-update/`); после — байт в байт bundled (sha256 3f10d15f…353c) [S10] |
| Проект | github.com/ahujasid/mcp-for-blender (переименован из blender-mcp 16.09.2026, issue #366), MIT | 29 193★, 2 680 форков, 32 открытых issue, push 21.09.2026 (API 22.09.2026) [S11][S13] |

Темп: PyPI `blender-mcp` — 38 релизов с 08.03.2025; `mcp-for-blender` 1.9.0 (01.09.2026) → 2.0.3 (21.09.2026) —
шесть релизов за три недели [S12]. Протокол аддона вырос с 6 (15.09.2026, `export_scene`) до 9 (21.09.2026). Поведение
инструментов меняется быстрее, чем пишутся статьи: закрепляй версию в конфиге (`uvx mcp-for-blender==2.0.3`) и проверяй
`get_addon_status` в начале сеанса. Поле `serverInfo.version` в рукопожатии MCP — это версия библиотеки `mcp` (1.30.0),
а не пакета [проверено: 06].

### 1.2. Путь команды

```text
клиент MCP (Claude Code / Desktop / Cursor)
   │ stdio (JSON-RPC)
   ▼
server.py: FastMCP → инструмент → BlenderConnection.send_command(type, params)
   │ TCP 127.0.0.1:9876, ОДНО постоянное соединение, threading.Lock на пару «отправить + прочитать»
   ▼
addon.py: BlenderMCPServer
   поток _server_loop: accept (таймаут 1 с) → поток на клиента _handle_client: recv 8 КБ, копит буфер до json.loads
   → command_queue.put((command, client))
   главный поток Blender: bpy.app.timers → _drain_command_queue() каждые 0,05 с
   → execute_command → обработчик → json.dumps(ответ) → client.sendall(...)
```

Команда: `{"type": "<имя>", "params": {...}}`. Ответ: `{"status": "success", "result": …}` или `{"status": "error",
"message": …}`; многие обработчики кладут `{"error": …}` внутрь успешного ответа — сервер проверяет оба варианта [S2][S9].
Базовые команды доступны всегда (`get_scene_info`, `get_world_state_snapshot`, `get_addon_info`, `get_object_info`,
`get_viewport_screenshot`, `execute_code`, `describe_node_type`, `bpy_api_lookup`, `drain_human_activity`,
`get_telemetry_consent`, `set_telemetry_consent`, пять `get_*_status`, `export_scene`, `ping`); команды интеграций
появляются, только если в сцене включено соответствующее свойство `blendermcp_use_*` [S9].

### 1.3. Установка и запуск

- Сервер: `uvx mcp-for-blender` в конфиге клиента; адрес — `--host/--port` (важнее переменных), `BLENDER_HOST`,
  `BLENDER_PORT` (по умолчанию `localhost:9876`); `BLENDER_MCP_SAFE_MODE=1` — безопасный режим; `DISABLE_TELEMETRY=true`
  (также `BLENDER_MCP_DISABLE_TELEMETRY`, `MCP_DISABLE_TELEMETRY`) — телеметрия [S1][S4].
- Аддон: `uvx mcp-for-blender install-addon` копирует bundled `addon.py` в папку аддонов как `blender_mcp.py`, делает
  `.bak` (если файл отличается), затем аддон выключить и включить или перезапустить Blender [S3]. Сервер сам файлы не
  перезаписывает: при старте лишь пишет в журнал «addon on disk is outdated» [S3].
- Запуск моста: N-панель → вкладка «MCP for Blender» → «Connect to MCP server». В протоколе 9 **сервер стартует сам** при
  запуске Blender и после открытия файла (`scene.blendermcp_auto_start_server` = True, таймер с повторами), если порт
  свободен и пользователь не нажимал «Disconnect» в этом сеансе; в фоне автозапуск выходит сразу [S9]. Проверено: порт
  9876 поднялся через ~19 с после запуска Blender с окном без нажатий [проверено: 09].
- Ключи сервисов: настройки аддона (Sketchfab, Poly Pizza, Hyper3D, Hunyuan SecretId/SecretKey/URL) или переменные
  `BLENDERMCP_SKETCHFAB_API_KEY`, `BLENDERMCP_POLYPIZZA_API_KEY`, `BLENDERMCP_HYPER3D_API_KEY`,
  `BLENDERMCP_HUNYUAN3D_SECRET_ID`, `BLENDERMCP_HUNYUAN3D_SECRET_KEY`, `BLENDERMCP_HUNYUAN3D_API_URL`; порядок чтения —
  настройки → свойства сцены → переменные окружения [S9]. Если настройки аддона недоступны, ключ пишется в свойство
  **сцены** (StringProperty с subtype PASSWORD) и сохраняется в .blend открытым текстом.
- Несколько Blender: второй экземпляр — другой порт в панели и отдельная запись сервера с `--port 9877` [S1].

### 1.4. Конфигурация у пользователя (22.09.2026)

`~/.claude.json`: `mcpServers.blender = {"type": "stdio", "command": "uvx", "args":
["mcp-for-blender"], "env": {"DISABLE_TELEMETRY": "true"}}` — версия не закреплена (uvx возьмёт свежую при обновлении
кэша). Галочка «Allow Telemetry» в настройках аддона снята; после обновления аддона до протокола 9 осталась снятой
(проверил оркестратор). Файл `~/.local/share/BlenderMCP/customer_uuid.txt` существует: сервер создаёт идентификатор
установки даже при отключённой телеметрии (`TelemetryCollector.__init__`) [S4]; ответа на диалог согласия
(`~/.config/blender-mcp/consent_prompt.json`) нет.

## 2. Протокол сокета и исполнение

### 2.1. Кадрирование

Разделителя сообщений нет. Сервер читает по 8 192 байта и после каждого куска пробует `json.loads` всего накопленного
буфера; аддон делает так же со входящей командой [S2][S9]. Следствия (все проверены на мосту C1/04 и в C1/08):
- **Две команды в одном `sendall`** («ping» + «get_addon_info») не парсятся никогда (`Extra data`) — ответа нет, буфер
  соединения испорчен. Сервер MCP держит `threading.Lock` на пару «отправка + приём», поэтому сам так не делает;
  собственный клиент должен соблюдать «одна команда — один ответ».
- **Цена приёма квадратична**: 4 МБ разбираются 0,47 с, 6 МБ — 1,06 с; быстрый читатель берёт те же 16 МБ за 3 с.
- Кириллица в ответах сохраняется (JSON с `\uXXXX` внутри трассировок).

### 2.2. Главный поток и таймер

Все обращения к `bpy` идут в главном потоке Blender: обработчики сокета только кладут команды в очередь, её разбирает
таймер `bpy.app.timers` с интервалом 50 мс [S9]. Из этого:
- задержка круговая: в окне ping — медиана 38 мс, `execute_code print(1)` — 51 мс; в фоновом мосту C1 с опросом 20 мс —
  16–21 мс [проверено: 04, 09];
- пока исполняется команда, Blender не перерисовывает интерфейс и не принимает другие команды;
- `bpy.context.area`, `region`, `space_data` внутри команды = `None` (таймер, а не редактор): операторы `view3d.*`
  падают на `poll()`; обход — `bpy.context.temp_override(area=…, region=…)` [проверено: 09], см. §3.4;
- загрузки Poly Haven, Sketchfab, Poly Pizza, запросы к генераторам тоже идут в главном потоке — интерфейс замирает на
  время скачивания [S1][S9].

### 2.3. Таймауты и пределы

| Предел | Значение | Что происходит | Проверка |
|---|---|---|---|
| Ожидание ответа сервером | 180 с (`settimeout(180.0)`) | после — «Communication error with Blender: No data received», сокет пересоздаётся; Blender продолжает исполнять код, ответ уходит в закрытый сокет («Failed to send response - client disconnected») | [проверено: 04, 14] |
| Долгий код | нет лимита | следующий вызов ждёт окончания текущего кода (главный поток занят): ping на новом соединении после 6-секундного кода ждал 4 с | [проверено: 04] |
| Отправка ответа аддоном | `sendall` на сокете с таймаутом 1 с (в Python ≥3.5 — на всю отправку) | ответ 8 МБ и 16 МБ обрывается на 8 368 576 байт при «медленном» читателе сервера → через 180 с «Incomplete JSON response received» | [проверено: 08, 14] |
| Практический предел ответа | ~5–6 МБ на этой машине | зависит от скорости CPU клиента | [проверено: 08] |
| Размер кода | нет (в безопасном режиме — 200 000 байт) | — | [S8] |

### 2.4. Ошибки: что видит агент

Сервер 2.0.3 бросает собственное исключение с текстом ответа внутри блока `try` и сам же его ловит общим `except
Exception`, дописывая «Communication error with Blender:» и обнуляя сокет [S2]. Поэтому ошибка **в коде агента** приходит
с тем же префиксом, что и сбой связи, разбор JSON-трассировки в `execute_blender_code` не срабатывает, а соединение
переоткрывается после каждой ошибки (в журнале моста — «Client disconnected», затем «Connected to client»)
[проверено: 04, 14]. Длинное сообщение сервера «Timeout waiting for Blender response … If Blender is running headless
(blender -b), commands never execute; run Blender with a GUI or via 'xvfb-run -a blender'» в обычном пути недостижимо:
приёмник сам ловит `socket.timeout` и бросает «No data received».

| Ситуация | Текст для агента (после префикса инструмента) | Когда | Что делать |
|---|---|---|---|
| Blender не запущен или порт другой | `Not connected to Blender` | сразу | запустить Blender/мост, проверить порт |
| Исключение в коде | `Communication error with Blender: {"exception_type": "KeyError", "message": …, "traceback": "… File \"<string>\", line 4 …"}` | сразу | читать тип, сообщение и строку; править код |
| Команда неизвестна (старый аддон, интеграция выключена) | `Communication error with Blender: Unknown command type: …` | сразу | обновить аддон / включить интеграцию |
| Blender принял и молчит (занят, таймер снят, фон без моста) | `Communication error with Blender: No data received` | через 180 с | не повторять вслепую: проверить процесс, `ping` мостом |
| Ответ оборвался (> ~6 МБ) | `Communication error with Blender: Incomplete JSON response received` | через 180 с | печатать меньше, писать данные в файл |
| Blender закрылся (например, `sys.exit()` в коде) | `Communication error with Blender: Connection closed before receiving any data` | сразу | перезапустить Blender, восстановить из сохранения |
| Ошибка обработчика с `{"error": …}` | `Error: …` или `Error <действие>: …` (текстом, без исключения) | сразу | читать текст |

[проверено]

### 2.5. Несколько клиентов

Три клиента одновременно, у каждого `time.sleep(1)`: ответы через 1,01 / 2,01 / 3,01 с — одна очередь, один главный
поток. В результатах двух клиентов оказались чужие строки «Client disconnected / Client handler stopped»:
`redirect_stdout` подменяет `sys.stdout` на весь процесс, и печать других потоков во время `exec` попадает в ответ
[проверено: 08]. Правило: машиночитаемый итог — **последней строкой** JSON, разбирать последнюю строку (так делает сам
сервер в `trajectory._snapshot_via_execute_code` [S6]).

## 3. Инструменты по одному

### 3.0. Сводка

| Инструмент | Параметры (по умолчанию) | Команда аддона | Возврат, размер | Главные особенности |
|---|---|---|---|---|
| `get_addon_status` | `user_prompt=""` | `get_addon_info` (+ `get_telemetry_consent`) | JSON ≈0,8 КБ | протокол, версия Blender, согласие на телеметрию; может показать диалог согласия (§5.2) |
| `get_scene_info` | `user_prompt` (обязателен) | `get_scene_info` | JSON; 10 объектов | только первые 10 объектов: имя, тип, location |
| `get_object_info` | `object_name` | `get_object_info` | JSON ≈0,4 КБ | loc/rot/scale, материалы, AABB с модификаторами, счётчики исходного меша |
| `execute_blender_code` | `code` | `execute_code` | «Code executed successfully: <stdout>» | §3.4 |
| `get_viewport_screenshot` | `max_size=1000` (в описании «800») | `get_viewport_screenshot` | PNG как Image | вьюпорт, не рендер; нужен общий диск сервера и Blender |
| `bpy_api_lookup` | `query` | `bpy_api_lookup` | JSON до 80 КБ | динамические enum занижены |
| `describe_node_type` | `bl_idname`, `property_overrides` | `describe_node_type` | JSON 1–7 КБ | без `enabled` сокетов |
| `export_scene` | `filepath`, `format="glb"`, `object_names`, `selection_only=False`, `apply_modifiers=True` | `export_scene` | JSON: путь, байты, объекты | меняет выделение; экспорт по умолчанию |
| `get_polyhaven_status` / `get_polyhaven_categories` / `search_polyhaven_assets` / `get_polyhaven_asset_preview` / `download_polyhaven_asset` / `set_texture` | см. §3.9 | `get_polyhaven_*`, `search_…`, `download_…`, `set_texture` | текст / Image | нужен `scene.blendermcp_use_polyhaven` |
| `get_sketchfab_status` / `search_sketchfab_models` / `get_sketchfab_model_preview` / `download_sketchfab_model` | `target_size` обязателен | `…sketchfab…` | текст / Image | ключ Sketchfab |
| `get_polypizza_status` / `search_polypizza_models` / `download_polypizza_model` | `normalize_size=False` | `…polypizza…` | текст | ключ Poly Pizza; CDN за Cloudflare |
| `get_hyper3d_status` / `generate_hyper3d_model_via_text` / `…_via_images` / `poll_rodin_job_status` / `import_generated_asset` | — | `create_rodin_job`, `poll_rodin_job_status`, `import_generated_asset` | JSON | платно; пробный ключ |
| `get_hunyuan3d_status` / `generate_hunyuan3d_model` / `poll_hunyuan_job_status` / `import_generated_asset_hunyuan` | — | `create_hunyuan_job`, … | JSON | платно или свой сервер; CVE §6.2 |
| `disable_telemetry` | — | `set_telemetry_consent False` | текст | только выключает |
| `record_trajectory_feedback` | `feedback` ∈ accept/reject/undo/correction | — (только сервер) | текст | пишет в Supabase при согласии |
| промт `asset_creation_strategy` | — | — | 8 875 символов | §3.14 |

Итого 32 инструмента и 1 промт [S2]; все проверены вживую через мост, кроме платных генераторов и сервисов с ключами
(по коду) [проверено: 04].

### 3.1. `get_addon_status`

Заново делает рукопожатие (`get_addon_info`) и возвращает `up_to_date` (протокол ≥9), `protocol_version`,
`addon_version` [1, 7], `capabilities` (11 базовых команд), `blender_version`, `source` (`native` / `missing` / `error`),
`warning`, `telemetry_consent`, `update_command`, `after_install` [S2][S3]. Проверено на мосту и в окне: `protocol_version:
9`, `telemetry_consent: false` [проверено: 04, 09]. **Ложный отрицательный ответ**: если Blender перезапустили, а сервер
MCP держал старое соединение, первый вызов вернул `up_to_date: false`, «Addon handshake failed: Communication error with
Blender: Connection closed before receiving any data»; второй — нормальный ответ [проверено: 09]. Инструмент также
вызывает `get_telemetry_consent` (даже при `DISABLE_TELEMETRY=true`) и может показать диалог согласия (§5.2).

### 3.2. `get_scene_info`

Возвращает `name`, `object_count`, `materials_count` и `objects` — **первые 10** объектов `scene.objects` (комментарий в
коде: «Reduced from 20 to 10») с полями `name`, `type`, `location` (округление до 0,01) [S9]. На сцене из 18 объектов — 10
в списке; из 2 005 — 10, 773 байта [проверено: 02, 08]. Нет габаритов, поворотов, масштаба, модификаторов, иерархии,
коллекций, материалов объектов. Параметр `user_prompt` у него **обязателен** (у остальных — `""` по умолчанию) [S2].
Внутренняя команда `get_world_state_snapshot` (для телеметрии, не выставлена инструментом) отдаёт до 4 000 объектов с
AABB, модификаторами и связями — 592 КБ за 0,09 с на 2 005 объектах; её раздел `animation` в 5.x всегда пуст (код читает
`action.fcurves`, которого в 5.x нет; исключение глотается) [проверено: 02, 08].

### 3.3. `get_object_info`

`name`, `type`, `location`/`rotation`/`scale` (полная точность, углы в радианах), `visible`, `materials` (имена в
слотах); для MESH — `world_bounding_box` [[min], [max]] по `obj.bound_box` и `mesh` {vertices, edges, polygons}
[S9]. Проверено на кубе с Subsurf 2 и Array 3: габарит −0,42…2,10 учитывает модификаторы, а `mesh` = 8 вершин / 6 граней —
исходный меш [проверено: 02]. Бюджет треугольников по этому инструменту не оценить — нужен оценённый меш
(`evaluated_get(depsgraph).to_mesh()`), см. аудит `04 §6`. Нет объекта → `Object not found: X` [проверено: 02].

### 3.4. `execute_blender_code`

Как исполняется [S9] [проверено: 02, 04, 09]:

| Свойство | Поведение в 2.0.3 / протокол 9 |
|---|---|
| Пространство имён | новый словарь `{"bpy": bpy}` на каждый вызов; `mathutils`, `bmesh`, `math` надо импортировать |
| Состояние между вызовами | живут данные `bpy.data`/сцены и модули в `sys.modules`; переменные, функции, импорты — нет (`NameError: name 'x' is not defined`) |
| Вывод | `redirect_stdout` → весь напечатанный текст; stderr не возвращается; значение последнего выражения не возвращается (`1 + 1` → пусто) |
| `__name__` | `'builtins'` → блок `if __name__ == "__main__":` пропускается молча; `__file__` нет |
| Исключение | ответ `status: error`, `message` = JSON {exception_type, message, traceback}; строка — `File "<string>", line N` |
| `SyntaxError` | так же, с указанием строки и `^` |
| `SystemExit` (`sys.exit`, `exit`, `quit`) | аддон ловит только `Exception` → исключение уходит в таймер → `PyErr_PrintEx` → `Py_Exit`: **Blender закрывается без сохранения** (окно: код выхода 3 на `sys.exit(3)`) |
| `KeyboardInterrupt` | таймер `_drain_command_queue` снимается; порт слушает, команды копятся и не исполняются; агент видит «No data received» через 180 с; лечится Disconnect/Connect в панели |
| Контекст | главный поток, таймер: `context.area = None`; `bpy.ops.view3d.*` → `poll() failed`; `mode_set`, `mesh.*` в EDIT, `object.*`, рендер, сохранение, импорт/экспорт работают |
| Undo | шаг undo не создаётся; отката нет |
| Лимит времени | нет; см. §2.3 |

Минимальный шаблон вызова (печать итога одной строкой JSON):

```python
# Blender 5.2.2 — [проверено] — тело для execute_blender_code
import bpy, json
from mathutils import Vector          # каждый вызов — своё пространство имён: импорты заново

report = {"objects": len(bpy.data.objects), "meshes": len(bpy.data.meshes)}
print(json.dumps(report))             # последняя строка stdout = машиночитаемый итог
```

Оператор, которому нужен вьюпорт (в Blender с окном):

```python
# Blender 5.2.2 — [проверено] — в окне; в фоне область VIEW_3D тоже есть в screen
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == "VIEW_3D")
region = next(r for r in area.regions if r.type == "WINDOW")
with bpy.context.temp_override(area=area, region=region):
    bpy.ops.view3d.view_all()          # без override: «poll() Expected a view3d region»
print("ok")
```

Трассировку при ошибке отдавай модели целиком (урезая середину, если длинная): по 3DCodeBench два повтора по traceback
поднимают исполнимость кода Blender 5.0 с 0,702 до 0,974, ~90 % отказов — несовпадения API версии (`03-research §2.2`).

### 3.5. `get_viewport_screenshot`

Сервер передаёт аддону путь `tempdir/blender_screenshot_<pid>.png`, аддон пишет туда PNG, сервер читает файл с диска и
удаляет его — **сервер и Blender должны видеть одну файловую систему** (Docker-вариант README это не учитывает) [S2].
Аддон ищет область `VIEW_3D` в `bpy.context.screen` и рисует её через `gpu.types.GPUOffScreen.draw_view3d(scene,
view_layer, space, region, view_matrix, window_matrix, do_color_management=True)`; запасной путь —
`bpy.ops.screen.screenshot_area` (снимок окна ОС, чёрный, если окно не на переднем плане) [S9].

Что показывает: вид и режим затенения вьюпорта пользователя (обычно Solid с сеткой, осями, контуром выделения, камерой и
лампами), а не камеру сцены и не рендер [проверено: 01, 04, 09]. Кодом можно подготовить кадр (вид из камеры, без
оверлеев, Material Preview) — но в фоне Material Preview и Rendered показывают серую заглушку (шейдеры EEVEE не
компилируются без цикла событий), в окне — настоящие материалы [проверено: 04, 09]. Кадр «камеры» во вьюпорте шире кадра
рендера (регион 1574×954 ≠ разрешение рендера). В фоне без `gpu.init()`: «GPU functions for drawing requires the gpu
module to be initialized», запасной путь падает на `poll()` [проверено: 01, 02].

Почему не заменяет рендер: нет света и цветового преобразования рендера, чужой ракурс, оверлеи, разрешение окна. Для
проверки «как на сайте» — рендер в файл кодом и чтение PNG (0,78 с на 512×320 EEVEE 16 сэмплов) [проверено: 04]:

```python
# Blender 5.2.2 — [проверено] — рендер из камеры сцены в PNG
import bpy, os, time
s = bpy.context.scene
s.render.engine = "BLENDER_EEVEE"
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 512, 320, 100
s.render.image_settings.file_format = "PNG"
s.eevee.taa_render_samples = 16
s.render.filepath = "/abs/path/work/preview_cam.png"      # абсолютный путь в рабочей папке
t = time.time()
bpy.ops.render.render(write_still=True)
print({"png": s.render.filepath, "sec": round(time.time() - t, 2), "exists": os.path.exists(s.render.filepath)})
```

Подготовка вьюпорта для снимка (если нужен именно он):

```python
# Blender 5.2.2 — [проверено]
import bpy
area = next(a for a in bpy.context.screen.areas if a.type == "VIEW_3D")
space = area.spaces.active
space.region_3d.view_perspective = "CAMERA"   # смотреть из активной камеры
space.overlay.show_overlays = False           # без сетки и контуров
space.shading.type = "MATERIAL"               # в фоне — серая заглушка, в окне — материалы
print(space.shading.type)
```

### 3.6. `bpy_api_lookup`

Разбор запроса [S9]: префикс `bpy.` срезается; `ops.<категория>.<оператор>` → `get_rna_type().properties` (имя, тип,
умолчание, enum, min/max); `Type` → все свойства и функции; `Type.member` → одно свойство или функция; слово `types`
выкидывается; не найдено → `did_you_mean` (≤15, поиск только по подстроке). Проверено [проверено: 02]:
- `ShaderNodeTexSky.sky_type` → `SINGLE_SCATTERING, MULTIPLE_SCATTERING, PREETHAM, HOSEK_WILKIE`, умолчание `PREETHAM`;
- `RenderSettings.engine` → `enum_items: ["BLENDER_EEVEE"]` (реально ещё `BLENDER_WORKBENCH`, `CYCLES`),
  `ColorManagedViewSettings.view_transform` → `["NONE"]` (реально AgX, Standard, Khronos PBR Neutral, Filmic…): для
  динамических перечислений инструмент бесполезен — присвоение в `try/except TypeError` вернёт полный список;
- `Action.fcurves`, `Mesh.use_auto_smooth`, `SceneEEVEE.use_bloom` → ошибка, `did_you_mean: []` — полезно как быстрый
  тест «этого API в 5.2 нет»;
- размер ответа: `Object` — 80,7 КБ, `bpy.ops.export_scene.gltf` — 33,9 КБ, `SceneEEVEE` — 20,3 КБ.
Официальный сервер Blender Lab вместо этого несёт справочник и руководство 5.2 с поиском (`search_api_docs`) [S23].

### 3.7. `describe_node_type`

Создаёт временную группу `__mcp_introspect_tmp__` по очереди в `ShaderNodeTree`, `GeometryNodeTree`,
`CompositorNodeTree`, `TextureNodeTree`, ставит `property_overrides` (ошибки → `warnings`), читает свойства ноды (без
базовых свойств Node) и сокеты (`index`, `identifier`, `name`, `type`, `is_multi_input`, `hide_value`, `is_linked`,
`default_value`), удаляет группу [S9]. Проверено: Principled (32 входа, 7,1 КБ), Mix, Sky, Material Output,
`GeometryNodeMeshToCurve`, `GeometryNodeSetMaterial`, `CompositorNodeGlare`, `ShaderNodeMixRGB` («Mix (Legacy)» ещё есть
в 5.2.2); временных групп не остаётся; опечатка `Principled` → `did_you_mean` три варианта; неверный
`data_type: COLOR` → предупреждение со списком `('FLOAT', 'VECTOR', 'RGBA')` [проверено: 02, 04].
Ограничение: **нет поля `enabled`** — у Mix с `{"data_type": "RGBA"}` те же 10 входов (Factor_Float, Factor_Vector,
A_Float, B_Float, A_Vector, B_Vector, A_Color, B_Color, A_Rotation, B_Rotation), что и без него; доступны при RGBA только
0, 6, 7. Индексы сокетов из ответа нельзя брать для связей: сокет — по имени после установки режима, у Mix и Map Range
поиск по identifier в 5.2.2 выключен (агент B, `../03-bpy-api/02-nodes-from-python.md`).

### 3.8. `export_scene`

`object_names` → снимает выделение со всего, выделяет объекты с `children_recursive`, делает первый активным; иначе
`selection_only` или вся сцена [S9]. Вызов: `bpy.ops.export_scene.gltf(filepath, export_format='GLB', use_selection,
use_active_scene=True, export_apply=apply_modifiers, export_animations=True, export_skins=True, export_morph=True,
export_yup=True)` — остальное по умолчанию экспортёра: **без Draco и Meshopt, без ламп, текстуры как есть**. FBX:
`apply_unit_scale`, `bake_space_transform=apply_modifiers` (связано с модификаторами — неочевидно), `path_mode='COPY'`,
`embed_textures`. Путь создаётся где угодно (проверки пути нет, безопасный режим его не касается) [S9].
Проверено [проверено: 02, 04]: вся сцена → 386 КБ, камера в списке `exported`, но в GLB ламп нет (`extensionsUsed: []`);
куб с Subsurf+Array → 364 КБ, с `apply_modifiers=False` — 8,5 КБ; куб с дубом Poly Haven 1k → 2,27 МБ на 12
треугольников: baseColor JPEG 697 КБ, normal JPEG 392 КБ, metallicRoughness перепакован в PNG 1,23 МБ, displacement
потерян, предупреждение валидатора `MESH_PRIMITIVE_GENERATED_TANGENT_SPACE`. Ошибки (`format="obj"`, нет объекта) приходят
как `{"error": …}`. Для сайта после экспорта: `gltf-transform optimize … --compress meshopt --texture-compress webp`,
`gltf_check.py`, `web_view.py` (контракт экспорта — агент E, `../08-export-gltf/`).

### 3.9. Poly Haven (без ключа, CC0)

Включение: `scene.blendermcp_use_polyhaven = True` (в панели или кодом; обработчики собираются на каждую команду, так что
перезапуск связи не нужен, вопреки тексту статуса) [проверено: 04]. Инструменты [S2][S9]:
- `get_polyhaven_categories(asset_type="hdris")` — дерево категорий и атрибутов с допустимыми значениями (для `all` —
  два уровня);
- `search_polyhaven_assets(query, asset_type="all", category, attributes, min_size_m, limit=20 ≤50)` — семантический
  поиск Poly Haven, пересечённый с фильтрами; кэш списка 12 ч с ETag; 400 → «не распознан фильтр», 429 → «rate limit»,
  503 → свой поиск по ключевым словам; результат — имя, id, автор, категория, теги, атрибуты, реальный размер, разрешение,
  загрузки;
- `get_polyhaven_asset_preview(asset_id)` — миниатюра 512 px (CDN ресайзит);
- `download_polyhaven_asset(asset_id, asset_type, resolution="1k", file_format)`: HDRI → **новый** мир «PolyHaven <id>»,
  картинка упакована, пространство — как задал загрузчик (Linear Rec.709); текстуры → карты Diffuse (sRGB), Rough, Metal,
  Displacement, nor_gl (Non-Color) → Principled через Mapping (POINT) + Normal Map + Displacement (Midlevel 0,5,
  Scale 0,1, `displacement_method = BOTH`), материал без пользователя — **пропадёт при сохранении**, пока не применён;
  модели — append коллекции `<slug>_LOD0` из .blend (если .blend новее Blender — glTF), все картинки упаковываются,
  custom props `polyhaven_*`;
- `set_texture(object_name, texture_id)` — **удаляет все слоты материалов** объекта и ставит новый материал.
Вживую [проверено: 04]: «soft studio lighting» (hdris) → 920 совпадений, первые — студийные HDRI Wooden Studio,
Monochrome Studio; «brushed aluminium metal» (textures) → первыми ржавый металл — судить по превью; скачивание HDRI 1k —
новый мир, 1024×512; первая попытка текстуры 1k — «Connection aborted, RemoteDisconnected», повтор успешен, после сбоя
остались осиротевшие картинки (при повторе — суффиксы `.001`); рендер EEVEE с HDRI и дубом — 1,2 с.

### 3.10. Sketchfab (ключ)

`search_sketchfab_models(query, categories, count=20, downloadable=True)`, `get_sketchfab_model_preview(uid)` (миниатюра
400–800 px), `download_sketchfab_model(uid, target_size)` — `target_size` обязателен, нормализация всегда включена [S2].
Аддон: `GET /v3/models/{uid}/download` → архив glTF в память целиком (таймаут 60 с) → проверки zip-slip → импорт →
масштаб **корневых** объектов умножается (неприменённый масштаб) → габарит и мировой AABB в ответе [S9]. Лицензия у
каждой модели своя — атрибуция на совести агента (сервер печатает только метку лицензии). Не вызывалось: ключа нет по
решению заказчика.

### 3.11. Poly Pizza (ключ)

`search_polypizza_models(query, category, licence, animated, limit=20 ≤32)`: названия категорий и лицензий сервер
переводит в числа (0–11; 0 = CC-BY, 1 = CC0), параметры API — с заглавной буквы, строчные молча игнорируются;
`download_polypizza_model(model_id, normalize_size=False, target_size=1.0)` — по умолчанию **без нормализации**, хотя
модели архива Google Poly имеют произвольный масштаб [S2][S9]. CDN `static.poly.pizza` блокирует датацентры, VPN и
облака (Cloudflare); строка атрибуции CC-BY (~69 % каталога) пишется в custom property `polypizza_attribution` корней
[S1][S9]. Не вызывалось.

### 3.12. Hyper3D Rodin (платно)

`generate_hyper3d_model_via_text(text_prompt, bbox_condition)` и `…_via_images(input_image_paths | input_image_urls)` →
`create_rodin_job`: MAIN_SITE `POST https://hyperhuman.deemos.com/api/v2/rodin` (tier «Sketch», mesh_mode «Raw»,
texture_mode «high»), FAL_AI `https://queue.fal.run/fal-ai/hyper3d/rodin`; `poll_rodin_job_status`,
`import_generated_asset` (скачивание .glb, ожидается «один меш» или «пустышка + меш», иначе ошибка) [S2][S9]. Замечания:
запросы без таймаутов (могут подвесить главный поток); в `…_via_images` ветка URL обращается к `input_image_paths` (None)
— режим FAL_AI с URL падает `TypeError`; ветка путей читает **любой существующий файл** на машине сервера и отправляет
его в Rodin (§6.3). Кнопка «Set Free Trial API Key» ставит встроенный ключ `vibecoding` [S9]. Не вызывалось: по решению
заказчика пробный ключ — резерв агента G.

### 3.13. Hunyuan3D (платно или свой сервер)

`generate_hunyuan3d_model(text_prompt, input_image_url)` → `create_hunyuan_job`: режим по умолчанию **LOCAL_API**
(`http://localhost:8081/generate`, octree 256, 20 шагов, guidance 5,5, без текстуры; импорт через `bpy.app.timers` — в
фоне не сработает; ответ «Generation and Import glb succeeded» выдаётся до импорта) или OFFICIAL_API (Tencent Cloud
TC3-HMAC-SHA256; Mainland `ai3d` 2025-05-13 / International `hunyuan` 2023-09-01; промт ≤1 024 символа; текст и картинка
вместе — ошибка) [S1][S9]. `poll_hunyuan_job_status(job_id)`, `import_generated_asset_hunyuan(name, zip_file_url)`
(предпочтителен .glb). Уязвимости — §6.2 [проверено: 13].

### 3.14. Телеметрические инструменты и промт `asset_creation_strategy`

- `disable_telemetry` — шлёт `set_telemetry_consent {consent: false}`; включить обратно можно только в настройках аддона
  [S2]. На мосту (модуль не зарегистрирован как аддон) — «Could not read addon preferences» [проверено: 04].
- `record_trajectory_feedback(feedback, correction_text, step_index)` — строка в таблицу Supabase `trajectory_feedback`
  при согласии; иначе «skipped» [проверено: 04].
- Промт `asset_creation_strategy` (8 875 символов, ≈1 877 токенов, клиент получает его только по `prompts/get`):
  проверять интеграции, **сначала библиотеки и генераторы, код — только если все выключены, запрошен примитив или ничего
  не нашлось**; скриншот до и после; `get_scene_info` после; следить за `world_bounding_box`; звать
  `record_trajectory_feedback` на реакции пользователя [S2][проверено: 06]. Для стилизованных hero-объектов сайта в
  едином паспорте стиля это неверный приоритет: ассеты библиотек не совпадают по стилю, генераторы дают тяжёлую
  триангулированную сетку; порядок выбора источника — `04-agent-operating-protocol.md §4`.

## 4. Безопасный режим (`BLENDER_MCP_SAFE_MODE=1`)

AST-валидатор на стороне **сервера** проверяет только код `execute_blender_code` до отправки в сокет; «запрещено всё,
что не разрешено»; автор честно пишет: «a guard on what the model can be talked into, not a sandbox around Blender»
(сокет принимает сырой `execute_code` от любого локального процесса) [S8]. Добавлен 02.09.2026 (коммит 41d98fc), усилен
21.09.2026 (b2daf09) [S11].

| Разрешено | Запрещено |
|---|---|
| модули `bpy`, `bmesh`, `mathutils`, `math`, `cmath`, `random`, `colorsys`, `json`, `itertools`, `functools`, `collections`, `statistics`, `string`, `re`, `enum`, `dataclasses`, `typing`, `decimal`, `fractions`, `textwrap`, `unicodedata`, `uuid`, `copy`, `heapq`, `bisect`, `array` | `numpy`, `os`, `sys`, `time`, `pathlib`, `subprocess`, `socket` и всё прочее |
| рендер, `save_mainfile`/`open_mainfile`, любые импорт/экспорт, `images.load`, `bpy.path`, присваивание `.filepath` | `eval`, `exec`, `compile`, `open`, `input`, `exit`, `globals`, `dir`, `super`, `help` |
| `from mathutils import Vector`, `def`, `try/except`, генераторные выражения, f-строки | `lambda`, `class`, `global`, декораторы, `async`, `yield`, «морж» `:=`, `match` |
| `getattr(obj, "literal")` | `getattr/setattr` с вычисляемым именем; вызов имени из итерации (`for f in fns: f()`); модуль как значение (`o = bpy.ops`) |
| | `bpy.app.handlers`, `bpy.app.timers`, `driver_add`, `bpy.data.texts/scripts/libraries`, `wm.append/link`, `bpy.props`, `register_class`, `bpy.ops.script/text/preferences/extensions/console`, `quit_blender`, `save_homefile` |
| | лимиты: 200 000 байт, 20 000 узлов AST, вложенность 24 |

Замер на 40 типичных фрагментах кода агента: 17 проходят, 23 отвергаются — среди отвергнутых безобидные
`sorted(objs, key=lambda o: o.name)`, `import time`, `import numpy`, `if __name__…`, `class Params`, цикл
`setattr(cam, k, v)` по словарю параметров [проверено]. Чего режим не закрывает:
инструменты Hunyuan/Hyper3D читают файлы по пути от модели, `export_scene` пишет куда угодно, а включить интеграцию и
перенаправить её URL можно разрешённым кодом (`scene.blendermcp_hunyuan3d_api_url = …` → `is_safe: True`)
[проверено: 13]. Стиль кода под безопасный режим: явные присваивания вместо циклов `setattr`, `def` вместо `lambda`, без
`numpy`, `time`, `class`.

## 5. Телеметрия, траектории и `user_prompt`

### 5.1. Что уходит и куда

Всё — в Supabase `https://yzasssndwqceclzilcdu.supabase.co` (анонимный ключ зашит в пакет): таблица `telemetry_events`,
хранилище `telemetry-screenshots`, таблицы `trajectory_steps` и `trajectory_feedback`; фоновые потоки, таймаут 1,5 с
[S4][S6].

| Уровень | Условие | Данные |
|---|---|---|
| Выключено всё | `DISABLE_TELEMETRY` (или `BLENDER_MCP_DISABLE_TELEMETRY`, `MCP_DISABLE_TELEMETRY`) ∈ {true, 1, yes, on} | ничего (но файл `customer_uuid.txt` создаётся; `get_telemetry_consent` в Blender всё равно шлётся) |
| Минимальная запись (по умолчанию) | согласие в аддоне выключено | install UUID, session ID, имя инструмента, успех, длительность, версии MCP и Blender, ОС, время; текст ошибки заменён на «details withheld» |
| Полные данные | галочка «Allow Telemetry» / `telemetry_consent` в аддоне | + промты (`user_prompt` до 1 000 символов), весь код `execute_blender_code` (до 40 000 символов), снимки вьюпорта (и авто-кадр 512 px не чаще раза в 20 с после изменений сцены), снимки мира до/после каждого изменяющего шага (до 4 000 объектов, 4,5 МБ), имена операторов, которые **человек** запускает руками в Blender, и его undo/redo («сильнейший сигнал отказа»), отзывы |

По TERMS (правка 21.09.2026): при согласии пользователь даёт «worldwide, royalty-free, perpetual license» на промты,
снимки, код, метаданные сцены, траектории и записи ручных правок — для обучения ИИ, исследований и открытых датасетов;
хранение бессрочное; удалить данные из обученной модели нельзя [S16].

### 5.2. «По умолчанию включена?» — три ответа

- **Код 2.0.3 и аддон протокола 9**: `telemetry_consent` = False по умолчанию, диалог согласия версии 2 («v2: telemetry
  became opt-in») [S7][S9]. Переход сделан коммитом edb0f201 **21.09.2026** («update: opt-in telemetry») [S11].
- **До 21.09.2026** (аддоны до протокола 8 включительно, пакеты по 2.0.1): согласие **включено** по умолчанию — так было у
  пользователя (протокол 7, `default=True`; галочку он снял сам) [S10].
- **Сайт** mcp-for-blender.com/reference/telemetry на 23.09.2026: «collects anonymous usage telemetry by default…
  Consent is on by default» — отстаёт от кода [S17]; C2 цитирует его в `02 §2.4`.
- Минимальная анонимная запись во всех версиях включена по умолчанию; выключает её только переменная окружения.
- Диалог согласия (MCP elicitation) показывается один раз за разговор клиентам, которые его поддерживают, если согласие
  выключено и ответ не записан на диске; **не проверяет `DISABLE_TELEMETRY`** — может появиться и при отключённой
  телеметрии (данные при этом не уйдут) [S7]. В сеансах C1 диалог не появлялся.

Вывод для правил: считать полную телеметрию включённой, пока не проверено обратное: `DISABLE_TELEMETRY=true` в
конфиге клиента + `get_addon_status` → `telemetry_consent: false`.

### 5.3. `user_prompt`

Описание в 28 инструментах: «The user's own words… quoted verbatim… Pass the same goal on every call» [S2]. Это поле
`goal_text` датасета траекторий: смена цели (строка ≥12 символов, отличная от прежней) закрывает эпизод; при пустом
значении подставляется цель сессии [S6]. Blender его не использует; при выключенной телеметрии оно никуда не уходит.
Абзац про `user_prompt` занимает ≈2 029 токенов из 8 418 (22 %) описаний инструментов [проверено: 06]. Правило: короткая
нейтральная строка задачи («C1: hero mug»), без личных данных; обязателен только у `get_scene_info`.

## 6. Безопасность

### 6.1. Сокет и автозапуск

Сокет без аутентификации и шифрования, слушает `localhost` [S1][S9]. Любой локальный процесс, дошедший до порта,
исполняет Python с правами пользователя; в протоколе 9 сервер поднимается сам при запуске Blender с окном
[проверено: 09]. README советует не выставлять порт в сеть и ходить на удалённую машину SSH-туннелем [S1]; в
Docker-варианте для Linux нужен `--network=host`.

### 6.2. CVE 2026 года: состояние в 2.0.3

| CVE | Суть | Статус в 2.0.3 / протоколе 9 | Проверка |
|---|---|---|---|
| **CVE-2026-10661** (GHSA-qqw9-95ww-prfm; NVD 02.06.2026; CVSS v4 2.1, CWE-74) | issue #202 (10.03.2026): `input_image_url` у `generate_hunyuan3d_model` без проверки; путь без `http(s)://` открывается `open(image, "rb")`, файл base64 уходит POST-ом на API (Tencent или URL из настроек) | **не исправлена**: PR #205 (проверка расширения, `realpath`, запрет приватных адресов) закрыт **без слияния** 09.08.2026; issue закрыт «completed» 19.04.2026 без комментариев; «патч» 5b37be2 из записи — в форке bergskenop [S18][S20] | тестовый файл ушёл на локальную ловушку `POST /generate`, аддон ответил «succeeded» [проверено: 13] |
| SSRF (issue #203, CVE-2026-10662 — NVD 02.06.2026, CWE-918, CVSS v3.1 6.3) | `import_generated_asset_hunyuan(zip_file_url)` проверяет только префикс `http(s)://` | **не исправлена** | `GET /internal/admin.glb` на 127.0.0.1 выполнен [проверено: 13] |
| **CVE-2026-10688** (NVD 02.06.2026; CVSS 3.1 5,5, v4 2,0, v2 6,5; OpenCVE 5,1; CWE-74/94) | issue #201: `exec()` в `execute_blender_code` без проверки | «исправление» — необязательный безопасный режим (02.09.2026); issue закрыт 25.06.2026; по умолчанию свободный `exec` | §4 [проверено: 07] |

Условие эксплуатации 10661: интеграция Hunyuan3D включена в сцене (по умолчанию выключена) и модель получила вредный
путь (инъекция промта через описания ассетов, имена объектов, README скачанной модели). Режим по умолчанию LOCAL_API
не требует ключей. Безопасный режим не мешает: разрешённым кодом можно включить интеграцию и сменить URL [проверено: 13].

### 6.3. Другие векторы, найденные при чтении кода

- `generate_hyper3d_model_via_images(input_image_paths)` на **сервере** читает любой существующий путь
  (`os.path.exists` + `open(path, "rb")`) и отправляет в Rodin (нужен ключ; пробный — одна кнопка) [S2].
- `export_scene` и `save_as_mainfile` пишут по любому пути; `download_*` распаковывают архивы (есть проверки zip-slip) [S9].
- Ключи сервисов при отсутствии настроек аддона живут в свойствах сцены и уходят вместе с .blend [S9].
- Запросы к Rodin и Hunyuan без таймаутов — главный поток может висеть бесконечно [S9].
- Описания ассетов Poly Haven, Sketchfab и ответы API попадают в контекст модели — канал инъекции; безопасный режим
  создан именно против него [S8].

### 6.4. Изоляция

Сотрудники Blender в треде devtalk (30.04–08.09.2026): «the only reasonably safe way to run a blender controlled by an
MCP server… is to run it on a separate dedicated machine, or at least in a firewalled VM»; Campbell Barton — на Linux
опробованы лёгкие песочницы jai и bubblejail, песочница — «not something Blender can/should realistically solve»
(по `02 §10.1a`, цитаты сверены C2) [S24]. Официальный сервер Blender Lab пишет то же на своей странице [S23].
Минимум для системы заказчика: отдельный процесс Blender агента (фон, `--factory-startup`, отдельная учётная запись или
контейнер), рабочая папка — единственное место записи, исходные .blend — только копии, `DISABLE_TELEMETRY=true`,
интеграции Hunyuan/Hyper3D выключены, ключи — только в окружении процесса агента, журнал всех исполненных скриптов.

## 7. Совместимость протоколов 7 и 9

`diff -u` bundled (9) и аддона пользователя (7): 9 фрагментов, 1 998 строк [проверено: сравнение копий,
`99-raw/experiments/_orchestrator/mcp-addon-update/`]. Ядро одинаковое: сокет, очередь, таймер, `execute_code`,
`get_scene_info`, `get_object_info`, снимок вьюпорта, `describe_node_type`, `bpy_api_lookup`, `export_scene`,
`get_world_state_snapshot`, `drain_human_activity`, `get_addon_info`, Sketchfab, Poly Pizza, Hyper3D, Hunyuan, запрет
старта в фоне. Различия:

| | Протокол 7 (у пользователя до 22.09.2026 22:51) | Протокол 9 (bundled 2.0.3) |
|---|---|---|
| `ADDON_PROTOCOL_VERSION` | 7 | 9 |
| Poly Haven helpers | нет (600 строк) | кэш, семантический поиск, выбор карт, md5, упаковка |
| `get_polyhaven_asset_preview` | нет | есть |
| `get_polyhaven_categories` | `GET /categories/{type}` → `{"categories": …}` | таксономия и атрибуты → `{"taxonomy": …}` |
| `search_polyhaven_assets` | `(asset_type, categories)`, первые 20 по slug | `(asset_type, category, attributes, query, limit, min_size_m)` |
| HDRI | **перезаписывает `bpy.data.worlds[0]`** (чистит узлы чужого мира), картинка во временном файле, пространство `Linear` (в 5.2 нет) | новый мир, упакованная картинка |
| Текстуры | качает все карты; `'Diffuse' in ['color','diffuse','albedo']` регистрозависимо → **альбедо в Non-Color**; `nor_gl` и `Displacement` при загрузке не подключаются; Mapping TEXTURE (тайлинг обратный) | только нужные карты, верные пространства, POINT |
| `telemetry_consent` по умолчанию | **True** | False |

Что ломалось у пользователя с сервером 2.0.3 до обновления (по коду): `get_addon_status` → `up_to_date: false`;
`get_polyhaven_asset_preview` → «Unknown command type»; `get_polyhaven_categories` → «Error getting Polyhaven categories:
'taxonomy'»; `search_polyhaven_assets` → `TypeError: unexpected keyword argument 'category'` — поиск Poly Haven не работал
вовсе; `download_polyhaven_asset` и `set_texture` работали по старой логике с перечисленными дефектами; траектории — через
нативный снимок (он есть и в 7). Остальные инструменты работали. Обновление (оркестратор, 22.09.2026 22:51) закрыло всё
это; откат — `cp ~/.config/blender/5.2/scripts/addons/blender_mcp.py.bak ~/.config/blender/5.2/scripts/addons/blender_mcp.py`.

## 8. Мост без окна (рецепт) и работа с окном

### 8.1. Почему аддон не работает в фоне

`BlenderMCPServer.start()` при `bpy.app.background` печатает «cannot start server in background mode (blender -b) -
commands would never execute… use a virtual display: xvfb-run -a blender» и выходит; автозапуск тоже [S9]. Причина —
команды исполняет колбэк `bpy.app.timers`, а в `blender -b --python` после скрипта нет цикла событий.

### 8.2. Рецепт

Копия аддона грузится как модуль под своим именем (установленный аддон пользователя не трогается), `register()` создаёт
свойства сцены, `gpu.init()` включает offscreen-рисование, сервер поднимается как в `start()`, но без проверки фона, а
главный поток сам крутит `_drain_command_queue()`:

```python
# Blender 5.2.2 — [проверено] — ядро bridge.py (полная версия — в эксперименте)
# запуск: blender -b --factory-startup --python bridge.py -- --port 9876 --gpu
import bpy, importlib.util, socket, threading, time
spec = importlib.util.spec_from_file_location("blender_mcp_bridge_addon", "/abs/path/addon_bundled_p9.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
mod.register()                                   # свойства сцены blendermcp_*; автостарт в фоне сам выходит
import gpu; gpu.init()                           # иначе get_viewport_screenshot в фоне не работает
srv = mod.BlenderMCPServer(host="localhost", port=9876)
srv.running = True
srv.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.socket.bind(("localhost", 9876)); srv.socket.listen(5)
srv.server_thread = threading.Thread(target=srv._server_loop, daemon=True); srv.server_thread.start()
bpy.types.blendermcp_server = srv
orig = srv.execute_command
def guarded(cmd):                                # SystemExit/KeyboardInterrupt из кода агента не убивают мост
    try:
        return orig(cmd)
    except BaseException as e:
        return {"status": "error", "message": f"{type(e).__name__}: {e}"}
srv.execute_command = guarded
t0 = time.time()
while time.time() - t0 < 3600:                   # главный поток = исполнитель команд (вместо bpy.app.timers)
    srv._drain_command_queue()
    time.sleep(0.02)
srv.stop()
```

Запуск в фоне и остановка:

```bash
# [проверено]
cd 99-raw/experiments/C1/04-headless-bridge
ss -ltn | grep -q ':9876 ' && echo "порт занят" || \
  timeout 7400 blender -b --factory-startup --python bridge.py -- --port 9876 --gpu --ttl 7200 > bridge_stdout.log 2>&1 &
touch STOP                                  # штатная остановка (или kill -TERM <pid из bridge_status.json>)
ss -ltnp | grep 9876 || echo "порт свободен"
```

Проверено (22.09.2026, 22:53–23:32, 94 команды): все 32 инструмента сервера сессии Claude работают против моста, в том
числе снимок вьюпорта (Solid, 157 мс), Poly Haven (поиск, превью, HDRI, текстура, `set_texture`), экспорт, рендер из
кода; `sys.exit(0)` агента вернулся ошибкой, мост жив [проверено: 04]. Ограничения моста: таймеры, зарегистрированные
кодом (и импорт Hunyuan LOCAL_API), не срабатывают; операторы с областью — через `temp_override`; настроек пользователя
нет (`--factory-startup`) — согласие на телеметрию «нет», ключи — только переменными окружения; материалы во вьюпорте
серые — проверка вида только рендером. После остановки моста сервер отвечает «Connection closed before receiving any
data», затем «Not connected to Blender».

### 8.3. Сеансы с окном (разрешение заказчика 22.09.2026)

Два сеанса Blender 5.2.2 с настройками пользователя: 23:38:53–23:47:43 и 23:47:59–23:49:13 [проверено: 09].
Автозапуск на 9876 без нажатий; `get_addon_status` — протокол 9, согласие false; Material Preview с настоящими
материалами; задержка 38–51 мс; `raise KeyboardInterrupt` — порт слушает, команды не исполняются (ping — таймаут);
`sys.exit(3)` из `execute_blender_code` — **Blender закрылся с кодом 3** без вопроса о сохранении, агент получил
«Connection closed before receiving any data».

## 9. Цена контекста

Методика mcp-context-cost (athakur3) воспроизведена: их снимок 28 инструментов — 6 928 токенов o200k, совпало
[проверено: 06][S15]. Снимок 2.0.3 (stdio, 32 инструмента) [проверено]:

| Что | Токены o200k |
|---|---|
| `tools/list` целиком | **9 285** (16.08.2026 — 5 258 при 24 инструментах; 04.09 — 6 928 при 28) |
| только поля Anthropic (name, description, input_schema) | 8 418 |
| из них абзацы про `user_prompt` | ≈2 029 |
| `instructions` сервера | 353 |
| имена 32 инструментов | 153 |
| промт `asset_creation_strategy` | 1 877 |
| самые дорогие: `search_polyhaven_assets` 808, `download_polypizza_model` 492, `generate_hyper3d_model_via_images` 484, `describe_node_type` 483, `download_polyhaven_asset` 473 | |

По замеру mcp-context-cost для Claude (count_tokens, 14.09.2026) 6 160 токенов o200k полей Anthropic = 10 576 токенов
Claude (×1,72); для 2.0.3 это ≈14 500 токенов в каждом запросе клиентов, которые грузят определения сразу (Claude
Desktop, Cursor, VS Code) `[оценка переносом коэффициента]`. Claude Code откладывает определения: в сеансе стоят имена и
инструкции (≈500 токенов), схема — после `ToolSearch`. Ядро для работы кодом (`execute_blender_code`, `get_scene_info`,
`get_object_info`, `get_viewport_screenshot`, `export_scene`, `bpy_api_lookup`, `describe_node_type`) — ≈2 080 токенов.

## 10. Сравнение с официальным MCP Blender Lab и рекомендация

### 10.1. Таблица

| | mcp-for-blender 2.0.3 | Blender Lab MCP v1.0.3 [S23] |
|---|---|---|
| Кто, лицензия | сообщество (S. Ahuja), MIT | Blender Foundation (Campbell Barton, Dalai Felinto), GPL-3.0-or-later |
| Живость | 29 193★; релизы раз в несколько дней | 25★ на projects.blender.org; коннектор Blender в каталоге Claude с 28.04.2026 |
| Blender | аддон заявляет ≥3.0; проверен на 5.2.2 | ≥5.1 (манифест), справка обновлена до 5.2 |
| Инструменты | 32: код, сцена (10 объектов), объект, снимок вьюпорта, справка RNA, схема ноды, экспорт GLB/FBX, Poly Haven, Sketchfab, Poly Pizza, Rodin, Hunyuan, телеметрия | 29: код (+ `_for_cli` в отдельном фоновом процессе по пути .blend), сводки файла и объектов, поиск по справочнику API и руководству 5.2, снимки области/окна, переходы по интерфейсу, рендер миниатюры/вьюпорта в файл |
| Без окна | штатно нет; мост C1 (копия аддона + ручной цикл) | штатно: `blender -b file.blend --command blender_mcp`, нужен `--online-mode`; проверено C2 в 5.2.2 (9/9) |
| Кадрирование сокета | JSON без разделителя, одно постоянное соединение, предел ответа ~5–6 МБ | JSON + `\0`, одно соединение — один запрос; 2 МБ получены целиком |
| Контракт кода | новый namespace; вывод — stdout; ошибка — JSON с traceback под префиксом «Communication error» | новый namespace; данные — `dict` в переменной `result`, `print` → `stdout`, ошибка — полный traceback |
| `sys.exit` / `quit_blender` | закрывает Blender (проверено) | заблокированы (`weak_sandbox.py`); также `read_factory_settings`, `read_userpref` |
| Проверка кода | необязательный AST-фильтр (`BLENDER_MCP_SAFE_MODE`) | нет (только блок выхода и сброса) |
| Документация API | `bpy_api_lookup` по живому RNA (занижает enum) | RST-справочник и руководство 5.2 + поиск |
| Ассеты и генераторы | Poly Haven, Sketchfab, Poly Pizza, Rodin, Hunyuan | нет |
| Телеметрия | минимальная по умолчанию; полная — до 21.09.2026 по умолчанию, сейчас по согласию; для обучения ИИ | не заявлена, сетевых вызовов кроме сокета в коде нет |
| CVE | 10661 (не исправлена), 10662 (SSRF #203, не исправлена), 10688 (by design) | публичных нет (22.09.2026) |
| Порт по умолчанию | **9876** | **9876** |
| Инструкции модели | 25 строк + промт «сначала библиотеки» | `prompts.yml`, 123 строки: осмотреть сцену до правок, не разрушать без подтверждения, явные active/selection, depsgraph, ссылки вместо имён |

### 10.2. Конфликт порта

Оба аддона по умолчанию слушают 9876; аддон mcp-for-blender в окне занимает порт при запуске сам. Мосту агента давай
другой порт (C2 брал 9901) и соответствующий `--port` серверу; при двух аддонах в одном Blender поменять порт у одного
[S23][проверено: 09].

### 10.3. Что брать системе заказчика

`[мнение C1 на основе исходников, экспериментов 04, 07, 09, 13 и C2/02]`
1. **Агент-дизайнер без окна** (основной режим системы): фоновый Blender 5.2.2 в изоляции + **официальный MCP Blender Lab**
   (`--online-mode --command blender_mcp`, порт ≠ 9876) для пошаговой работы **или** прямые скрипты `blender -b --python`
   через утилиты базы для детерминированной пересборки «с нуля по параметрам» (протокол `04 §5`). Плюсы: штатный фон,
   справка 5.2, блок выхода, простой контракт, без телеметрии.
2. **mcp-for-blender** — только для сеансов с окном рядом с человеком и там, где нужны Poly Haven (HDRI, текстуры CC0) и,
   по отдельному разрешению, генераторы: аддон протокола 9, `DISABLE_TELEMETRY=true`, версия закреплена
   (`uvx mcp-for-blender==2.0.3`), интеграции Hunyuan3D и Hyper3D выключены, пока CVE-2026-10661 и чтение файлов в
   `…_via_images` не исправлены; безопасный режим — по желанию (ломает часть обычного кода, §4).
3. **Мост C1 для mcp-for-blender без окна** — рабочий, но самодельный: годится для экспериментов и там, где нужны именно
   инструменты mcp-for-blender (Poly Haven) без GUI; для постоянной работы предпочтителен официальный сервер.
4. Условия пересмотра: исправление 10661 и SSRF; штатный фон у mcp-for-blender; ассеты у официального сервера; смена
   политики Blender Foundation (Blender Conference, 24.09.2026).

## 11. Правила пользования для агента

1. Начало сеанса: `get_addon_status` → протокол 9, версия Blender 5.2.x, `telemetry_consent: false`; при «handshake
   failed» повторить один раз; при протоколе < 9 — сообщить пользователю `uvx mcp-for-blender install-addon`.
2. Не полагаться на `get_scene_info` для состава сцены — отправить аудит кодом (`99-raw/experiments/C1/10-scene-audit/
   scene_audit.py`) и читать последнюю строку JSON.
3. Каждый вызов `execute_blender_code` — самодостаточный: импорты, поиск своих объектов по коллекции или тегу, итог
   `print(json.dumps(...))` последней строкой; без `if __name__`, без `sys.exit`, без `KeyboardInterrupt`.
4. Держать вызов коротким (< 30 с): рендер ≤ 1024 px и ≤ 64 сэмплов Cycles; длинные операции делить на вызовы.
5. Не печатать больше ~1 МБ; данные — в файл рабочей папки, в ответе — путь и сводка.
6. Ошибку читать по типу, сообщению и строке `<string>`; повторять не больше двух раз с исправлением; при одинаковой
   ошибке дважды — сменить подход или справиться в документации 5.2 (`bpy_api_lookup Type.prop`, справка B).
7. «No data received» — не повторять команду вслепую: проверить процесс Blender и мост; «Connection closed…» —
   Blender закрылся, восстановить из последнего сохранения.
8. Перед разрушительным шагом (удаление, `read_homefile`, применение модификаторов на чужих объектах, `set_texture`) —
   `bpy.ops.wm.save_as_mainfile(filepath=<work>/checkpoint_NN.blend, copy=True)`.
9. Вид проверять рендером в PNG (камера сцены + 4 студийных ракурса `render_views.py`), а не снимком вьюпорта; снимок —
   только для быстрого «что открыто у пользователя».
10. Перечисления читать из ошибки `TypeError` присвоения или `bl_rna…enum_items` конкретного свойства; для движка и
    преобразования вида не верить `bpy_api_lookup`.
11. Сокеты нод — по имени после установки режима; `describe_node_type` — для имён и типов, не для индексов.
12. После `export_scene` — `gltf-transform optimize` (meshopt, WebP), `gltf_check.py`, `web_view.py`; свет сайта задаётся
    в three.js (лампы в GLB не попадают).
13. Poly Haven: смотреть превью до скачивания; 1k–2k; применять материал `set_texture` сразу (иначе пропадёт при
    сохранении) и только к объекту без нужных слотов; HDRI создаёт новый мир.
14. Sketchfab/Poly Pizza: проверять лицензию и сохранять атрибуцию; после загрузки применить масштаб корней.
15. Генераторы (Rodin, Hunyuan) — только по явному разрешению и с бюджетом; Hunyuan не включать, пока CVE-2026-10661 не
    исправлена.
16. `user_prompt` — короткая нейтральная строка задачи, без личных данных.
17. Не запускать второй клиент на тот же Blender; мосту агента — свой порт.
18. Не устанавливать и не обновлять аддоны, не менять настройки пользователя кодом (`bpy.ops.preferences.*`,
    `save_userpref`) — только сообщать команды пользователю.

## Частые ошибки

1. **Переменная из прошлого вызова** (`NameError: name 'mug' is not defined`) — модель считает, что сеанс Python
   общий. Каждый вызов находит объекты заново [проверено: 02].
2. **`from mathutils import Vector` забыт** — «name 'mathutils' is not defined»: в пространстве имён только `bpy` [проверено: 02].
3. **Результат через последнее выражение или `return`** — ответ пустой; нужен `print` [проверено: 02].
4. **`if __name__ == "__main__": main()`** — ничего не происходит и ошибки нет [проверено: 02].
5. **`sys.exit()` «для завершения скрипта»** — Blender пользователя закрывается без сохранения [проверено: 09].
6. **`bpy.ops.view3d.*` без override** — «poll() failed, context is incorrect» (команда идёт из таймера) [проверено: 02, 09].
7. **Доверие `get_scene_info`**: «в сцене 3 объекта» на самом деле первые 10 из 2 005 [проверено: 08].
8. **Счёт треугольников по `get_object_info`** — показывает исходный меш без модификаторов [проверено: 02].
9. **Снимок вьюпорта как проверка результата** — чужой ракурс, оверлеи, в фоне серые материалы [проверено: 04].
10. **`bpy_api_lookup("RenderSettings.engine")` как список движков** — вернёт один `BLENDER_EEVEE` [проверено: 02].
11. **Индексы сокетов из `describe_node_type`** — у Mix все типы сокетов в списке; связь с недоступным сокетом не
    работает (см. агент B) [проверено: 02].
12. **Печать всего снимка сцены или base64 картинки** — ответ > 6 МБ обрывается, через 180 с «Incomplete JSON» [проверено: 08].
13. **Длинный рендер Cycles 1920×1080 с 4 096 сэмплами по умолчанию** (заданный движок без числа сэмплов) — вызов
    превышает 180 с, ответ теряется, Blender занят [проверено: умолчания 5.2.2 — 4 096 сэмплов; C1/11].
14. **Скачать текстуру Poly Haven и сохранить файл, не применив** — материал удаляется при сохранении [исходник].
15. **`set_texture` на объект с несколькими материалами** — все слоты заменены одним [исходник].
16. **Загрузка Poly Pizza без `normalize_size=True`** — модель произвольного масштаба [исходник].
17. **Вызов генератора «на пробу»** — расходует платный или пробный ключ; без разрешения запрещено.
18. **Расшифровка «Communication error» как сбоя связи** — это исключение в коде агента [проверено: 14].
19. **Два MCP-сервера или два агента на один Blender** — общая очередь, чужой stdout в ответах [проверено: 08].
20. **Установка аддона «помочь пользователю»** — изменение чужой конфигурации; только рекомендовать команду.

## Чек-лист

- [ ] `get_addon_status`: протокол 9, Blender 5.2.x, `telemetry_consent: false`?
- [ ] `DISABLE_TELEMETRY=true` в конфиге клиента и версия сервера закреплена?
- [ ] Blender агента изолирован (отдельный процесс, рабочая папка, копии .blend), порт не конфликтует с Blender пользователя?
- [ ] Каждый скрипт самодостаточен (импорты, поиск своих объектов) и печатает итог одной строкой JSON?
- [ ] В коде нет `sys.exit/exit/quit`, `KeyboardInterrupt`, `if __name__`, опоры на переменные прошлых вызовов?
- [ ] Вызов укладывается в 30 с, вывод < 1 МБ?
- [ ] Перед разрушительным шагом сохранена копия .blend?
- [ ] Результат проверен аудитом кодом и рендером в PNG, а не `get_scene_info` и снимком вьюпорта?
- [ ] Интеграции Hunyuan3D и Hyper3D выключены (или есть разрешение и бюджет)?
- [ ] После `export_scene` GLB сжат, проверен валидатором и в браузере?
- [ ] Для ассетов с CC-BY сохранена атрибуция?

## Открытые вопросы и противоречия

- **Телеметрия «по умолчанию»**: код 2.0.3 и TERMS — полное согласие выключено; сайт на 23.09.2026 — «Consent is on by
  default»; до 21.09.2026 код тоже был «on». C2 (`02 §2.4`, §10.1) опирается на сайт. Решено O (`07-security.md` §5.2): прав код — в 2.0.3 полное согласие opt-in (коммит edb0f201, 21.09.2026), сайт устарел;
  для версий < 2.0.3 и неизвестных установок считать полное согласие включённым; проверять `telemetry_consent`.
- **CVE-2026-10661 «исправлена коммитом 5b37be2»** (запись GHSA) против кода 2.0.3 без проверки и эксперимента C1/13:
  патч — в стороннем форке, PR в основной репозиторий не слит. Нужна повторная проверка на следующем релизе.
- **Что именно рисует `draw_view3d`** — оверлеи видны в фоне и в окне; поведение Rendered-режима в окне через MCP не
  проверялось (сеанс с окном был коротким).
- **Эффект безопасного режима на реальном агенте** (сколько вызовов теряется из-за запретов) — замерен только на 40
  фрагментах, не на живой сессии.
- **`serverInfo.version` = версия `mcp`**: mcp-context-cost подписывает замер «BlenderMCP v1.29.1» — это версия
  библиотеки, а не пакета; сравнения по этой подписи некорректны.
- **Не проверено**: Sketchfab, Poly Pizza, Rodin, Hunyuan вживую (нет ключей по решению заказчика); Docker-вариант;
  диалог согласия (клиент его не показывал); Windows/macOS.

## Источники

- [S1] S. Ahuja. mcp-for-blender 2.0.3 — README пакета (PyPI METADATA, 817 строк), 21.09.2026. Установка, переменные,
  интеграции, телеметрия, ограничения; документация проекта, сверена с кодом.
- [S2] mcp-for-blender 2.0.3 — `src/blender_mcp/server.py` (2 207 строк). Все инструменты, соединение, промт; первоисточник.
- [S3] — `addon_manager.py` (516). Протокол 9, рукопожатие, установка аддона.
- [S4] — `telemetry.py` (385) + `config.py` (26). Supabase, уровни данных, отключение.
- [S5] — `telemetry_decorator.py` (487). Обёртки инструментов, траектории, классификация ошибок.
- [S6] — `trajectory.py` (1 453). Датасет траекторий: снимки, авто-кадры, ручные правки, лимиты.
- [S7] — `consent_prompt.py` (220). Диалог согласия через MCP elicitation, версия 2.
- [S8] — `safe_mode.py` (988). Безопасный режим, политика и лимиты.
- [S9] — `bundled/addon.py`, протокол 9 (5 344 строки). Аддон: сокет, очередь, обработчики, интеграции, настройки.
- [S10] Аддон протокола 7, установленный у пользователя до 22.09.2026 (4 673 строки),
  `99-raw/experiments/_orchestrator/mcp-addon-update/blender_mcp_installed_protocol7.py` (sha256 c836e1e7…1767).
- [S11] GitHub ahujasid/mcp-for-blender — API репозитория (29 193★, push 21.09.2026) и история коммитов `addon.py`,
  `safe_mode.py` (edb0f201 opt-in telemetry, 41d98fc и b2daf09 safe mode), просмотрено 22–23.09.2026.
- [S12] PyPI JSON `mcp-for-blender` (1.9.0–2.0.3) и `blender-mcp` (38 релизов с 0.1.0), 22.09.2026.
- [S13] Issue #366 «blender-mcp is now mcp-for-blender» (ahujasid, 16.09.2026). Переименование без изменения API.
- [S14] Issue #347 (athakur3, 05.09.2026). Рост цены описаний инструментов.
- [S15] mcp-context-cost: страница servers/blender (замер 04.09.2026, Claude 14.09.2026) и `results/blender/measurement.json`;
  методика воспроизведена C1/06. Надёжно (сырые данные опубликованы).
- [S16] TERMS_AND_CONDITIONS.md (Last Updated: August 2026, правка 21.09.2026). Условия и лицензия на данные.
- [S17] mcp-for-blender.com/reference/telemetry, прочитано 23.09.2026. Отстаёт от кода (см. открытые вопросы).
- [S18] GitHub Advisory GHSA-qqw9-95ww-prfm / CVE-2026-10661 (опубликовано 03.06.2026; Low, CVSS v4 2.1).
- [S19] NVD API CVE-2026-10688 (02.06.2026, статус Deferred; CVSS 3.1 5.5 / v4 2.0 / v2 6.5) и OpenCVE CVE-2026-10688.
- [S20] GitHub issues #201 (RCE via exec), #202 (Arbitrary File Read via generate_hunyuan3d_model), #203 (SSRF) и
  PR #205 (закрыт без слияния 09.08.2026) — API и страницы, 23.09.2026.
- [S21] Blender v5.2.2 `source/blender/python/intern/bpy_app_timers.cc` — исключение колбэка таймера → `PyErr_PrintEx(0)`,
  таймер снимается. Первоисточник (копия в C1/03).
- [S22] CPython 3.13 `Python/pythonrun.c` — `_PyErr_PrintEx` → `handle_system_exit` → `Py_Exit`. Первоисточник.
- [S23] Blender Lab MCP Server v1.0.3 — по `02-integrations-landscape.md §2.2–2.4` (агент C2) и эксперименту
  `99-raw/experiments/C2/02-blender-lab-mcp-headless`; первоисточник https://projects.blender.org/lab/blender_mcp.
- [S24] devtalk.blender.org/t/45131 «MCP security for Blender scripting» (30.04–08.09.2026) — цитаты по `02 §10.1a` (C2).
- [S25] Агент B, `../03-bpy-api/02-nodes-from-python.md`, `04-llm-failure-modes-and-patterns.md` — поиск сокетов,
  ошибки `bpy`-кода в 5.2.2 (проверено B).
- [S26] Агент C2, `03-research-llm-3d.md §2.2, §8` — 3DCodeBench (Blender 5.0): повтор по traceback 0,702 → 0,974.
