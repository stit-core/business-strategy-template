# Утилиты text

Утилиты текстов страницы: смысл и факты до текстов, тексты по слотам — copy deck (каркас из плана, сверка с фактами и
правом, линтер, статусы, выбор, утверждение, выгрузка во вход холста, приём правок с холста), голос бренда и продукта,
реестр текстов интерфейса. Нормы и данные живут в базе `kb/text/` и у соседей (словарь site, каталог блоков): утилиты
их читают, а не держат в коде. База, соседние утилиты и выходы находятся через `../lib/kbpaths.py`, запуск — Python
окружения скилла (`$DDD_HOME/venv/bin/python`, `../install.sh`). Модели, сеть и браузер не нужны: тексты пишет агент
сессии, утверждает человек, утилиты проверяют и переносят. Файлы проекта пишет только `copydeck.py` — туда, куда его
направили (`-o`, `--update`, `export --out`); производные файлы базы пересобирают `ux_dict_to_yaml.py` и
`copydeck.py before-after --write`. Ключи — `<утилита> --help` и шапка файла. Коды выхода — один порядок: 0 — `error`
нет; 1 — есть `error` (у самопроверки — она не прошла); 2 — ошибка вызова, входа или окружения; особые исходы — от 3,
они названы в колонке «выход».

| утилита | что делает | вызов | выход |
|---|---|---|---|
| `copydeck.py` | copy deck: каркас из плана страницы, проверки формата и стыка с планом, сверка с фактами и правом, линтер, статусы, слепой выбор вариантов, утверждение, выгрузка во вход холста, приём правок с холста | `skeleton PLAN -o DECK`; `check DECK [--update OUT --promote] [--final] [--all-variants]`; `validate`, `claims`, `lint`; `select DECK --page ID --slot СЕКЦИЯ/СЛОТ --variant ID --by КТО -o OUT`; `approve DECK --page ID --by КТО -o OUT`; `export DECK --page ID --stage directions\|mockup`; `import-copy`; `export-variants`, `apply-selection`, `export-assets`; `before-after [--write\|--check]`; `--selftest` | терминал, `--json`, `--md`; код 0 · 1 · 2, у `claims` и `check` 3 — сверка фактов не отработала (находка `COPY-D-TOOL`); `export` — `$DDD_HOME/out/text/export` или `--out` |
| `claims_check.py` | сверка текстов с белым списком фактов `facts.yaml` и право формулировок — ядро контура честности | `check ВХОД --facts ФАКТЫ [--final]` (copy deck, `copy.md`, Markdown, текст, HTML); `lint-facts ФАКТЫ [--final]`; `inventory`, `rules-schema`; `--selftest` | терминал, `--json`, `--md`; код 0 · 1 · 2 |
| `copy_lint.py` | линтер по жанру и роли строки: тексты сайта, строки интерфейса, реестр `texts.md` | `ВХОД --genre …`; `- --genre interface --role …`; `--selftest` | терминал, `--json`, `--md`; код 0 · 1 · 2 |
| `ux_dict_to_yaml.py` | производный словарь ux 07/06 и длины по ролям для линтера | без ключей — собрать; `--check`; `--selftest` | `kb/text/06-anti-slop/lexicon/ux-07-06.yaml`; `--check` — код 3, если производный словарь устарел |
| `chain_inputs.py` | сверка смысла до текстов и вход судьи текстов | `meaning-claims --meaning M [--hierarchy H …] [--brief B] -o OUT`; `judge-input`, `judge-score`; `--selftest` | YAML; `meaning-claims` — число несверенных возражений и секций в stderr; код 0 · 1 · 2 |
| `validate_any.py` | смысл или иерархия проекта: схема, смысловые проверки, счётчики `basis_kinds` | `<файл>.yaml …` | терминал; код 0 · 1 · 2 |
| `validate_voice.py` | профили голоса бренда и продукта проекта | `<профиль>.yaml …`; без файлов — схема и примеры базы; `--selftest` | терминал и `$DDD_HOME/out/text/validate_voice.last-run.txt`; код 0 · 1 · 2 |
| `validate_meaning.py` | схемы смысла и иерархии сообщений, примеры базы | `[--quiet]` | терминал; код 0 · 1 |
| `validate_facts.py` | схемы фактов и голоса клиента, примеры базы | без ключей | терминал; код 0 · 1 |
| `run_checks.py` | все проверки примеров copy deck базы по порядку аудита текстов | `[<пример>.yaml …] [--md <таблица>]` | `$DDD_HOME/out/text/run_checks/`; код 0 · 1 · 2 (2 — и утилита проверки не отработала) |

## Что проверка останавливает, а что докладывает

- **Сверка смысла** (`chain_inputs.py meaning-claims` → `copydeck.py claims`) — сигнал до текстов. Возражения, страхи
  и альтернативы — слова аудитории: в проекцию смысла не идут, сверяются потом ответы на них в copy deck.
- **Факты** (`claims_check.py lint-facts`): разрешение `pending` и демо-данные — `warning`, с `--final` — `error`;
  `COPY-F-MACHINE` — значение для кода `machine` не по форме или не из `canonical` — `error`, контакт или реквизит вида
  `company` без `machine` — `warning` с готовым значением из формулировки.
- **Статус `checked`** ставит `copydeck.py check --update OUT --promote` у текстов без `error` сверки, линтера и
  `validate` (записи `lint` и `claims` с `text_hash`); страница — `checked`, когда проверены все её выбранные тексты.
  Текст с `error` остаётся в своём статусе — причина в заметках вывода. **`approved`** — только человек (`approve`).
  Пустая мета утверждению не мешает — `warning`.
- **Ворота публикации** — `copydeck.py validate DECK --final`: страница `approved`, 0 `[PLACEHOLDER]`, 0 демо-фактов,
  мета заполнена; обходы сверки — отдельным списком.

## Обход эвристик сверки — `claims_allow`

Ложную находку эвристик сверки снимает решение человека с записанной причиной, а не подгонка текста под корень слова:
`claims_allow` слота, мета (`meta.claims_allow`) или страницы — записи `{rule, reason, by}`, `rule` — семейство или id
находки: `COPY-F-CLASS` (маркер класса утверждения без факта), `COPY-F-NUM` (число без факта и число, не совпавшее с
фактом) или `COPY-F-NUM-MISMATCH` (только несовпавшее число); `value` (число) или `fragment` (слово или фраза находки)
называют, что именно снято, запись без них снимает все находки правила на своём месте. Обойдённая находка не
считается в error; `claims`, `check`, `approve` и `validate --final` перечисляют обходы отдельным списком (`--json` —
поле `allowed`), чтобы заказчик видел их на публикации. Право, `never_claim` и «утверждение шире факта» не обходятся.
Форма и правила записи — схема `kb/text/10-templates-recipes/copy-deck.schema.json` (`claims-allow`) и
`copydeck.py --help`. `claims_check.py`, запущенный сам по себе (в том числе на собранном HTML), записей copy deck не
знает: обходы применяет `copydeck.py`; с ключом `--allow` он читает те же записи из вывода
`copydeck.py validate --final --json` — место записи: слот, мета (`<page>/meta`, только тексты мета) или страница.

## Форматы

- **copy deck** — `kb/text/10-templates-recipes/copy-deck.schema.json`; стык с планом — карта `x-site-map`, выгрузка во
  вход холста — карта `x-canvas-map`; процесс — `kb/text/10-templates-recipes/01-copy-deck-workflow.md`.
- **`copy.md`** входа холста: синтаксис и статусы этапа — ключ `copy_md` карты `x-canvas-map` схемы copy deck; пишут и
  читают `copydeck.py` (`export`, `import-copy`), `claims_check.py --format copy-md` и разбор исходников холста. Пустая
  строка между строками продолжения — абзац внутри значения слота: значение тянется до следующей строки слота или
  секции.
- **JSON находок `copydeck.py`**: `{tool, version, date, command, input, today, summary{error, warning, info}, tools,
  findings[{tool, level, rule, where, message, fix, fragment, …}], allowed[{rule, where, reason, by, …}], notes}`; у
  `check` ещё `slots` (итоги по путям), у `export` — `export`; `tools.lint.facts` — файл фактов, который получил
  линтер. Правила: свои `COPY-D-…`; `COPY-F-…` и `COPY-L-…` — из `claims_check.py`; id линтера — из `copy_lint.py`;
  `meta-x-…` — проверки мета вне линтера.
- **Правила права** — `kb/text/08-russian-legal-typography/claims-rules.yaml` (формат — `claims_check.py rules-schema`):
  их читает только `claims_check.py`. Собранная страница и статичная копия артборда сверяются с привязкой:
  `claims_check.py page.html --facts facts.yaml --deck <copy deck страницы> --allow <вывод copydeck.py validate --final
  --json>` — текст слота сверяется как слот, находка под обходом `claims_allow` — `info` с причиной. Правила линтера — `kb/text/06-anti-slop/lexicon/`, профили жанров — `kb/text/06-anti-slop/profiles.yaml`.
