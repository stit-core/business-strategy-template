# Утилиты 3d

Утилиты 3D-слотов страницы: стенд и живая проверка сцен на своём движке WebGL2, запуск Blender без окна и под надзором,
помощники кода сцены Blender, проверки сцены и GLB, сверка «как в Blender» с «как в three.js», замер страницы с 3D и
ворота 3D, прогон рецептов и исполняемых блоков базы. Нормы,
процедуры и пороги живут в базе `kb/3d/` (проверки — `kb/3d/11-evaluation-qa/`, пороги ворот 3D —
`kb/3d/09-web-runtime/page-3d-gates.yaml`): утилиты их читают, а не держат в коде. База, соседние утилиты, выходы,
замки и бинарники находятся через `../lib/kbpaths.py`; запуск — Python окружения скилла (`$DDD_HOME/venv/bin/python`,
`../install.sh`). Нужны Blender 5.2.2 LTS (`DDD_BLENDER` или `blender` из PATH), Chromium Playwright и npm-зависимости
`$DDD_HOME/node` (gltf-transform, gltf-validator, gltfpack); страницы проверки в браузере берут three и декодеры с
jsDelivr, поэтому им нужна сеть. Выходы — папка, которую назвал вызов, или `$DDD_HOME/out/3d/`; исключение —
`rk.py`, он пишет результат рецепта рядом с рецептом базы. Код-репо запускает утилиты соседним чекаутом
`../strategy/.claude/skills/design-deep-dive/scripts/3d/…`. Ключи — `<утилита> --help`, у модулей и утилит без
`--help` — шапка файла.

Параллельно работают несколько агентов, а Blender и браузер тяжёлые: рендеры, замеры и пачки проверок идут через очередь
`slot_run.py` — она занимает слот и ждёт свободной памяти (`--min-mem`). Каждая утилита с браузером берёт замок браузера
`$DDD_HOME/locks/browser.lock` сама на время работы браузера (`kbpaths.lock`), замеры времени (`site_probe.py`,
`web_view.py`) — ещё общий тяжёлый замок тишины (`--no-lock` — без замков). Замки реентерабельны по дереву процессов:
утилита, запущенная из утилиты с тем же замком или из `slot_run.py`, который его держит (называет файл замка команде в
`DDD_LOCKS_HELD`), его не ждёт; внешний `flock` на файл замка не нужен.

## Blender без окна

| утилита | что делает | вызов | выход |
|---|---|---|---|
| `blender_run.py` | скрипт или выражение в Blender без окна: чистые настройки (`--factory-startup`), таймаут, фильтр шума рендера | `<скрипт>.py [--blend <сцена>.blend] [--timeout 600] [--user-prefs] [-- <аргументы>]`; `--expr "…"`; `--version` | stdout; журнал — `$DDD_HOME/out/3d/logs/`; код 0 · 1 исключение · 124 таймаут |
| `blender_supervisor.py` | Blender под надзором: процесс на рабочую папку, шаг — транзакция (успех — контрольная точка сцены, ошибка — откат), перезапуск после падения; лимиты `--mem`, `--cpu` и песочница `--sandbox` (`systemd-run`, `bwrap`); процедура — `kb/3d/04-ai-agents-mcp/06-headless-operations.md` | `start <WORK> [--mem 4G] [--sandbox]`; `exec <WORK> <скрипт>.py [--timeout 120] [-- …]`; `status`, `stop`, `replay` | журнал `<WORK>/sup/journal.jsonl`; код `exec` 0 · 1 исключение, сцена откатена · 2 процесс упал, восстановлен |
| `slot_run.py` | очередь тяжёлых запусков: слоты Blender, замок браузера, общий замок тяжёлых прогонов, ожидание свободной памяти; удержанные замки браузера и рендера названы команде в `DDD_LOCKS_HELD` | `[--kind blender\|browser\|none] [--heavy] [--min-mem MB] [--label ИМЯ] -- <команда> …`; `--status` | код команды (75 — ресурсов не дождались); замки и журнал — `$DDD_HOME/locks/` |
| `bpy_probe.py` | справочник по Python API из самого Blender: параметры операторов и `poll()` в фоне, свойства типов, фактические значения перечислений, сокеты нод, модификаторы, поиск, устаревшее | `op export_scene.gltf`; `type Object`; `node ShaderNodeMix data_type=RGBA`; `enum scene.render.engine`; `search …`; `deprecated`; `[--out <файл>.json]` | JSON в stdout или `--out`; код 3 — ошибка с `did_you_mean` |
| `render_views.py` | внутри Blender: рендер модели с нескольких ракурсов, контактный лист, статистика геометрии и материалов | `blender_run.py render_views.py -- <вход> <OUT_DIR> [--views 4\|6\|turntable:8] [--engine eevee\|cycles\|workbench] [--clay]` | `<OUT_DIR>/view_*.png`, `<OUT_DIR>/sheet.png`, `<OUT_DIR>/stats.json` |

## Код сцены — модули

Подключение — `sys.path.insert(0, "<скилл>/scripts/3d")` и импорт; модули с `bpy` работают внутри Blender.

| модуль | что даёт |
|---|---|
| `bpyx.py` | проверенные помощники Python API Blender 5.2: data API вместо операторов, ноды по типу, сокеты среди доступных, проверка перечислений; тесты — `test_bpyx.py` |
| `animx.py` | помощники анимации через слои, полосы и channelbag слота |
| `agent_scene.py`, `hygiene.py` | работа в сцене человека по тегу (своя коллекция, уборка только своего) и гигиена своего фонового файла; тесты — `test_agent_helpers.py` |
| `d1lib.py`, `d2lib.py`, `d1exp.py` | моделирование кодом (профили, формы, фаски, гладкость); циклорама и свет от габарита ассета; рендер варианта в плитку, разбор GLB, постобработка `gltf-transform` |
| `presets.py` | пресеты экспорта glTF для веба и команды постобработки (`gltfpack`, `toktx`) |
| `rk.py` | обёртка рецептов `kb/3d/12-recipes/`: паспорт → `build(P)` → проверки → рендер → экспорт; результат — `kb/3d/12-recipes/examples/<рецепт>/`, пути в `numbers.json` — от папки примера (вне скилла — имя файла) |
| `scene_audit.py`, `passport_asserts.py`, `preflight_block.py` | проверки внутри Blender: аудит сцены, утверждения паспорта ассета, предэкспортная проверка для веба; первые два текстом годятся и для `execute_blender_code` |
| `glb_lint_block.py` | проверка готового GLB без Blender: расширения и декодеры, вызовы, треугольники, текстуры и память GPU |

Тесты помощников — в Blender: `blender_run.py test_bpyx.py [-- <OUT_DIR>]`, `blender_run.py test_agent_helpers.py`; код 0
— все зелёные.

## Сцены на своём движке WebGL2

Контракт движка, рантайм сцен и бюджеты — `kb/3d/16-js-scenes/`; набор — `kb/3d/16-js-scenes/examples/`. Сети и
библиотек утилитам не нужно; Blender — тоже.

| утилита | что делает | вызов | выход |
|---|---|---|---|
| `stage_stand.py` | стенд сцены: кадр при заданных `p`, `t`, курсоре и касании, лист кадров, интервал кадров с вердиктом по бюджету (`perf`), цена кадра (`bench`); `--soft` — кадры на программном рендере | `shot OUT.png m=… src=…`, `sheet OUT.jpg 3 '…' '…'`, `perf …`, `bench …`; `--root DIR` — папка со своей копией `stand.html` | PNG, JPG или JSON в stdout; код 1 — ошибка шейдера или медиана сверх бюджета |
| `stage_smoke.py` | живая проверка рантайма и шаблонов на `demo.html`: такты по одному, живых сцен ≤ 2, `play` и `glide`, при «уменьшить движение» и на программном рендере — только раскадровка | `[--shots] [--json ОТЧЁТ]` | JSON с `ok` и находками; кадры — `$DDD_HOME/out/3d/stage-smoke/` |

## Проверка сцены, GLB и страницы

Процедура и пороги — `kb/3d/11-evaluation-qa/` (сводный чек-лист — `kb/3d/11-evaluation-qa/05-master-checklist.md`).

| утилита | что делает | вызов | выход |
|---|---|---|---|
| `qa_pipeline.py` | сводный конвейер с вердиктом fail · review · pass: `scene` — `scene_check.py` и предэкспортная проверка в одном фоновом Blender; `glb` — коллизии имён узлов, валидатор, `glb_lint`, что создал three, по запросу сверка вида и цена загрузки; `page` — `site_probe.py`, ворота 3D и import map | `scene <сцена>.blend … [--passport <паспорт>.json]`; `glb <модель>.glb [--blend <сцена>.blend --diff] [--bench] [--max-tris N] [--max-kb N]`; `page <URL или папка> [--mobile] [--reduced]`; `[--out <отчёт>.json] [--keep] [--strict]`; `--selftest` | короткий JSON в stdout, полный — `--out`; код 0 — замер выполнен, вердикт в JSON · 2 — ошибка вызова или стадия без результата; с `--strict` — 1 fail · 3 review |
| `scene_check.py` | внутри Blender: геометрия, паспорт (`dims_m`, касания, бюджет), кадр, материалы, свет; одна строка `SCENE_CHECK {json}` | через `qa_pipeline.py scene` или текстом в `execute_blender_code` | вердикт и коды находок |
| `lint_agent_code.py` | текст скрипта агента до отправки в Blender: опасные приёмы в сцене человека, выход из процесса, устаревший API | `<скрипт>.py …`; `-` — stdin | JSON в stdout; код 0 чисто · 1 есть замечания |
| `gltf_check.py` | валидатор Khronos, `gltf-transform inspect` и подсказки для веба (сжатие, размеры текстур, вес) | `<модель>.glb [--json] [--out <отчёт>.md]` | Markdown или JSON |
| `gltf_diff.py` | «как в Blender» против «как в three.js» при одной камере, HDRI и тонмаппинге: IoU силуэтов, ΔE2000, SSIM; пороги — `kb/3d/11-evaluation-qa/03-export-and-page-gates.md` §2.2 | `<источник> <OUT_DIR> --glb <модель>.glb [--tone neutral] [--engine cycles]`; `--compare <A>.png <B>.png <префикс>` | `<OUT_DIR>/diff_metrics.json`, `<OUT_DIR>/diff_sheet.png` |
| `gltf_web_inspect.py` | что three.js создал из файла: объекты и имена после санитизации, атрибуты, материалы с картами, клипы, вызовы первого кадра | `<модель>.glb [--out <отчёт>.json] [--anim-sample T]` | JSON |
| `gltf_load_bench.py` | цена загрузки в three.js: холодная и тёплая загрузка, первый кадр, память GPU, вызовы | `<модель>.glb … [--runs 3] [--throttle 4] [--json <отчёт>.json]` | stdout, `--json` |
| `three_probe.py` | GLB в three.js и своя JS-проверка — тело async-функции с `THREE`, `gltf`, `scene`, `render` | `<модель>.glb <проверка>.js [--out <отчёт>.json]` | JSON |
| `anim_diff.py` | анимация в Blender против three.js в одни и те же моменты | `<сцена>.blend <OUT_DIR> --glb <модель>.glb --frames 1,31,61 [--clip ИМЯ] [--mute-nla]` | кадры, метрики, лист сравнения |
| `img_metrics.py` | числа кадра до глаз и до судьи: контраст объекта и фона, пересвет, шум, насыщенность, визуальный вес, совпадение фона со страницей | `<кадр>.png [--mask <маска>.png \| --alpha] [--bg-hex '#101215'] [--text-zone x0,y0,x1,y1] [--out <отчёт>.json]` | JSON |
| `sheet.py` | лист сравнения кадров с подписями (судье — не больше двух кадров на лист) | `--out <лист>.jpg [--cols 2] [--tile 960] <кадр>.png:<подпись> …` | JPEG |

Слепые пары кадров для выбора человеком — общая страница голосования `../ai-media/stand_run.py page`.

## Браузер и страница с 3D

| утилита | что делает | вызов | выход |
|---|---|---|---|
| `site_probe.py` | замер страницы с 3D: переданные байты по категориям и сигнатурам, контексты WebGL и WebGPU, вызовы отрисовки, первый 3D-кадр, LCP с элементом, TBT; `--no-3d` — прогон «постер без 3D» для вклада 3D в TBT | `<URL> <OUT_DIR> --quick [--mobile --throttle] [--reduced-motion] [--no-3d]`; `--selftest` | `<OUT_DIR>/probe[…].json`, скриншоты |
| `gate_check.py` | ворота 3D по отчёту `site_probe.py` (§ ниже) | `<проба>.json mobile\|desktop [--reduced] [--baseline <проба без 3D>.json] [--profile P] [--json] [--strict]`; `--selftest` | таблица или JSON (`rows`, `summary`) |
| `web_view.py` | GLB в three.js или страница в Chromium на видеокарте: ракурсы, вызовы отрисовки, время кадра, ошибки консоли; живой сайт — ещё сеть по категориям и библиотеки по рантайму | `<модель>.glb <OUT_DIR> [--tone …] [--anim]`; `--page <страница>.html <OUT_DIR> [--scroll 0,0.5,1] [--mobile]`; `--url <URL> <OUT_DIR> [--throttle]`; `--selftest` | скриншоты, `<OUT_DIR>/web_stats.json` (пути — от папки модели) или `<OUT_DIR>/page_stats.json` |
| `fx_probe.py` | замер своей демо-страницы с 3D или шейдерным эффектом: режимы desktop, mobile, reduce, uncapped, покой отдельно от прокрутки | `<ROOT_DIR> <страница> <OUT_DIR> [--modes desktop,mobile,reduce,uncapped]` | `<OUT_DIR>/fx_<метка>.json`, скриншоты |
| `serve_br.py` | локальный сервер «как хостинг»: предсжатые brotli-файлы, типы файлов, без кэша | `<папка> <порт>`; модуль — `from serve_br import start` | — |

## Ворота 3D — что останавливает, а что докладывает

Ворота 3D отвечают за долю 3D на странице; LCP, CLS, TBT и вес страницы целиком — у ворот страницы
`../site/page_gates.py`, в отчёте `gate_check.py` они зеркало D с порогом профиля `--profile`. Вердикт собранной страницы
ставит `page_gates.py --gate3d` (указатель `../README.md` § Ворота после сборки).
- **`gate_check.py`** — код 0 при выполненном замере, находки — в отчёте; с `--strict` — код 1 при провале строки B:
  LCP-элемент canvas, 3D-ассеты сверх предела, ошибки консоли, при reduce — вызовы или движение в покое. Провал S
  (вызовы в покое, DPR холста, первый 3D-кадр, вклад 3D в TBT) — в отчёте, код 0 и со `--strict`: S исправляют или
  записывают исключением плана страницы.
- **`qa_pipeline.py page`** — та же тяжесть: провал B — ошибка и вердикт fail, провал S — предупреждение и review,
  зеркала D — сведения; все строки ворот — в поле `gates`, итог — `gate_summary`.

## Рецепты и исполняемые блоки базы

| утилита | что делает | вызов | выход |
|---|---|---|---|
| `run_recipes.py` | прогон рецептов `kb/3d/12-recipes/`: блоки python рецепта → Blender без окна → валидатор и three.js для каждого GLB | `<рецепт>.md … [--no-web]`; `--selftest` | `$DDD_HOME/out/3d/run_recipes/result.json` |
| `run_doc_blocks.py` | блоки python и bash итоговых md-файлов базы в напечатанном виде: python — в фоновом Blender с заводской сценой перед каждым блоком | `<файл>.md … [--json <отчёт>.json] [--only python,bash] [--dry-run]`; `--selftest` | строка `RESULT ok/total`, у `--dry-run` — строки `PLAN` и `BLOCKS`; `--json` |

## Данные

`data/studio_small_09_1k.hdr` — HDRI по умолчанию `gltf_diff.py` (CC0); `node/validate.mjs` — запуск валидатора Khronos
для `gltf_check.py`, `../install.sh` копирует его в `$DDD_HOME/node`.
