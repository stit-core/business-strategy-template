# Утилиты site

Утилиты слоя страницы сайта: проверяют контракты сайта (бриф, план страницы, карта сайта, каталог блоков, наборы форм) и
идентификаторы словаря, собирают и проверяют план ассетов страницы, меряют собранную или живую страницу и ставят ворота
после сборки, считают A/B-тест, собирают производные файлы базы (чек-лист сайта, маркетинговый профиль UX-чек-листа).
Нормы и числа живут в базе `kb/site/` и у соседей; утилиты их читают, а не держат в коде: база, соседние утилиты,
выходы, кэши и блокировки находятся через `../lib/kbpaths.py`, файлы проекта `docs/projects/<slug>/…` — через
`../lib/docpaths.py`; запуск — Python окружения скилла (`$DDD_HOME/venv`, `../install.sh`). Выходы по умолчанию —
`$DDD_HOME/out/site/<утилита>/` или ключ `--out`; в репозиторий пишут только генераторы производных файлов базы
(`checklist_export.py`, `build_profile.py`) и каркас плана ассетов с ключом `--write`. Код-репо запускает утилиты
соседним чекаутом `../strategy/…/scripts/site/…` со своей рабочей папкой. Ключи и форматы — `--help` утилиты.

Замок браузера (`kbpaths.lock('browser')`) каждая утилита с браузером берёт сама на время работы браузера; вложенный вызов
из процесса, который его уже держит, не ждёт, внешняя обёртка `flock` не нужна. Замер страницы — на тихой машине:
утилиты замера берут ещё общий тяжёлый замок и замок site (`page_gates.heavy_lock`; `--no-lock` — замер без замков),
перед тяжёлым прогоном — `free -g` не меньше 3 ГБ.
На чужой странице утилиты рекламу не кликают, формы не отправляют и ничего не вводят (для INP — только фокус в поле),
на cookie-баннере нажимают «Отклонить», если он есть; «Принять» не нажимают. К сторонним сервисам (страна сервера,
PageSpeed Insights) утилиты обращаются только по явному ключу; ключи API — только из окружения, не печатаются.

| утилита | что делает | самопроверка |
|---|---|---|
| `site_validate.py` | схемы и перекрёстные ссылки контрактов сайта: бриф, план страницы, карта сайта, каталог блоков, наборы форм; папка слоя страницы целиком | `--selftest` |
| `vocab_lint.py` | идентификаторы вне словаря site в YAML, JSON и Markdown; таблица соответствий словарей | `--selftest` |
| `plan_to_assets.py` | план ассетов страницы: каркас из медиа- и 3D-слотов плана страницы и проверка | `--selftest` |
| `page_anatomy.py` | анатомия собранной или живой страницы: секции, призывы, формы и согласия, мета, скорость, вес | `--selftest` |
| `page_gates.py` | ворота собранной страницы по профилю бюджета: сводит JSON утилит замера в вердикт | `--selftest` |
| `run_axe_targets.py` | axe-core с адресами узлов для ворот контраста | — |
| `geo_probe.py` | что видят поисковые и ИИ-боты: robots, коды, head, текст без JS, JSON-LD | `--selftest` |
| `ia_probe.py` | структура многостраничного сайта по HTTP: robots, sitemap, шаблоны адресов, шапка, подвал, крошки, 404 | `--selftest` |
| `ab_plan.py` | выборка, длительность и итог A/B-теста, проверка соотношения выборок | `--selftest` |
| `checklist_export.py` | сводный чек-лист сайта из Markdown в YAML | `--selftest`, `--check` |
| `build_profile.py` | маркетинговый профиль UX-чек-листа для страниц сайта | `--selftest`, `--check` |

## `site_validate.py` — контракты сайта

Проверяет бриф (`site-brief`), план страницы (`page-plan`), карту сайта (`site-map`), каталог блоков и наборы форм по
схемам v1 `kb/site/10-playbooks-contracts/schemas/` и связи между ними; файл другой версии — ошибка схемы. Коды находок
— `kb/site/10-playbooks-contracts/01-procedure-brief-to-pages.md` §12 и докстринг утилиты. Нужны PyYAML, jsonschema и
referencing: в системном python без них утилита перезапускается Python окружения скилла. Сеть и браузер не нужны.

| вызов | что делает |
|---|---|
| `site_validate.py PATH… [--today ГГГГ-ММ-ДД] [--json [OUT]] [--quiet]` | тип файла по ключам: бриф (SB-*), план (PL-*), карта (SM-*), каталог (BL-*), формы (LF-*); папка слоя страницы `docs/projects/<slug>/site/<surface>/` — бриф, факты, карта и планы `plans/<page-id>.yaml` со связями (PJ-*) |
| `site_validate.py --all` | каталог блоков, наборы форм и примеры `kb/site/10-playbooks-contracts/examples/` |
| `site_validate.py --selftest` | примеры `lead-services-otves` и `corporate-b2b-stalkon` проходят; посеянные дефекты находятся каждый своим кодом и своей тяжестью, законные правки — без находки |

Выход — строки «уровень, код, где, сообщение» и итог по уровням; `--json OUT` — те же находки списком JSON (`level`,
`code`, `where`, `msg`) в файл, `--json` без файла — тот же список в stdout вместо строк отчёта, итог — в stderr;
`--quiet` — только `error` и `warning`. Код выхода: 1 — есть `error`, 2 — ошибка вызова: не названы пути, у `--today`
нет даты.

- **Тяжесть.** `error` правится до макета; `warning` — доклад: решает заказчик, обход — с записанной причиной. Страница
  брифа без плана и без строки карты — PJ-03 `error`, у служебной страницы (`thank-you-page`, `legal-page`,
  `not-found-page`) — `warning`: её короткий план строится по плейбуку перед её макетом. Шаблон карты без плана —
  SM-22 по трём уровням: `info` — планы пишутся по `build_order`, и шаблон ждёт своей очереди; `warning` — служебный
  шаблон без плана, когда планы уже пишутся; `error` — файл плана есть, а его `page.template_id` — не этот шаблон.
  Адреса страниц (PJ-04) — `warning`: адрес карты или плана не в форме `url_policy.trailing_slash` карты, у лендинга
  без карты — план без `page.url` или адреса планов в двух формах.
  Цель-контакт (PL-F08, у призыва шапки карты — SM-24) — `warning`: литерал цели плана (`tel:+7…`, `mailto:…`, адрес
  мессенджера) не равен `machine` ни одного факта или у факта цели `messenger:<fact-id>` нет `machine` с адресом
  ссылки; значение контакта живёт в факте. Цель-контакт не по форме (PL-F09) — `warning`: цель телефона — не литерал
  номера E.164, цель мессенджера — не адрес ссылки и не `messenger:<fact-id>`; ссылку по цели словами код не соберёт.
  Прелоадер вне кампании L2
  (SB-D02) и референс в двух местах (SB-A02) — `warning` с нормой в сообщении. Подача (PL-C01) несёт тяжесть находки
  `../creative/spec_check.py plan`: нормы облика — `warning`, схема, ссылки и уровень эффекта — `error`.
- **Даты.** Сроки фактов (`valid.until`) считаются от даты прогона: файлы проекта — сегодня или `--today`; `--all` —
  дата примеров базы (константа `EXAMPLES_TODAY`), `--today` её переопределяет; самопроверка — всегда на дате примеров,
  поэтому её итог не зависит от календаря.
- **Бриф.** Бренд продукта — ссылкой `brand.ref` на `docs/projects/<slug>/design/brand.yaml` (путь от брифа): файла
  нет — SB-B01, файл не проходит схему `kb/common/brand.schema.yaml` — SB-B02. Темы `themes`: две темы без переключателя
  — SB-C01; «по системе» без второй темы — SB-C02 `error`, одна тёмная тема без причины `themes.dark.why` — SB-C02
  `warning` (с причиной — `info`: решение брифа); при двух темах умолчание не по системе — SB-C03 (ui 11/03 §6.4).
  Правило лидогенерации услуг (SB-A03) — поля `levels[id=L0].appropriate_for.lead_services` файла
  `kb/creative/01-creative-direction/ambition-levels.yaml`.
- **План.** Умолчания уровня по типу страницы (PL-P02) — `defaults_by_page_type` того же файла вместе с разделом
  `proposed`. Уровни эффектов секций и переходов страниц (PL-C02) — `x-effect-levels` подсхемы `treatment` и
  `limits.library_level_min` эффекта `page-transition` (`kb/creative/06-effects-catalog/effects.yaml`). 3D-слот: рецепт
  `recipe:<id>` есть в `kb/3d/12-recipes/` (PL-D02); ниже первого экрана загрузка по намерению `on-interaction`,
  `on-visible` и `after-lcp` — предупреждение (PL-D03).
- **Ограничения.** Длины текстов проверяет text; порядок ролей из осведомлённости — человек и судья.

## `vocab_lint.py` — словарь site

`vocab_lint.py ФАЙЛ… [--map КЛЮЧ=ПРОСТРАНСТВО …] [--crosswalk ТАБЛИЦА] [--stats]` — id вне словаря
`kb/site/02-site-types/vocabulary.yaml` в YAML, JSON и Markdown: значения ключей из карты «ключ → пространство» на
любой глубине, ссылки с префиксом (`block:`, `slot:`, `section-role:`, `page-type:` …; чужие префиксы `effect:`,
`fact:`, `recipe:` пропускаются), статусы (`deprecated`, `out-of-scope` — предупреждение, `measurement-only` —
ошибка). Карта по умолчанию знает и copy deck — `slot_type`, `section_role`, `block`, `page_type` (локальный `slot_id` и
действие страницы словами в неё не входят), и `facts.yaml` — места `use` (роли людей `owner`, `responsible`,
`attribution` — нет): эти файлы сверяются тем же вызовом, без `--map`. Роль ассета у плана и манифеста ассетов
(`slots[].role`, `assets[].role`) — не id словаря; типы слотов сверяются и вне плана: места `use` фактов и голоса клиента
(`use.slot_types`), место ответа на возражение в смысле (`where.slot_type`), образец голоса (`samples.slot_type`).
`--check-crosswalk` — таблица соответствий
`kb/site/02-site-types/crosswalk.tsv`: колонки, отношение `relation`,
`our_id` из словаря. Выход — строки «путь:строка: уровень пространство 'id' — сообщение» и сводка, подсказка — ближайший
id и строка таблицы соответствий; код 1 при ошибках. Разрешён ли слот блоку и есть ли факт — это `site_validate.py`;
для чужих форматов без карты — `--no-default-map`.

## `plan_to_assets.py` — план ассетов страницы

План ассетов — файл `docs/projects/<slug>/design/<surface>/assets/plans/<page-id>.yaml` в формате ai-media 01/01 §8,
схема — `../../kb/ai-media/05-prompting/asset-plan.schema.json`; канон слоя — `docs/projects/_template/design/README.md
§ Ассеты`. Id — словарь site: `page.page_type`, `slots[].slot`, `slots[].section` — id секции плана страницы; класс
ai-media `page.media_class` — проекция по строке §8 `../../kb/site/02-site-types/crosswalk.tsv`. Утверждает заказчик до
генерации: `status: approved` и `approval`.

| вызов | что делает |
|---|---|
| `plan_to_assets.py PAGE_PLAN [--out F]` | каркас из файла плана страницы: строка на медиа- и 3D-слот (`<секция>-<id>`) и на медиа-слот уровня страницы — его источник и подлинность читаются из плана страницы, `source` (постер 3D-слота — `render`; `edit-real` при подлинности `real-only` — строкой `real` с заметкой: кадр доводится без генерации), `key` у визуала и фона первого экрана и постера 3D, `alt_ref`, `three_d`, бюджеты профиля; размер, форматы, вес, предмет и дорога 3D — заглушки `TODO` |
| `plan_to_assets.py --check FILE … [--plan PAGE_PLAN] [--json]` | проверка плана ассетов — находки контракта `../project/findings.py`: форма по схеме и id словаря (R-STRUCT-005), поля утверждённого плана (R-MAT-002), покрытие слотов плана страницы, подлинность и постеры (R-COV-004), ссылки (R-REF-001) |
| `plan_to_assets.py build <slug> [<surface>] [--page ID] [--out DIR] [--write]` | каркасы страниц поверхности со слоем страницы: в `$DDD_HOME/out/site/plan_to_assets/<slug>/` или `--out`; `--write` — в проект, только на пустое место |
| `plan_to_assets.py check <slug> [<surface>] [--page ID …] [--json]` | планы ассетов проекта: всё из `--check`, план ассетов у страницы с медиа- и 3D-слотами (нет плана — `error` у страницы партии входа холста, поле `units` манифеста `INPUT.md`; у остальных страниц и до входа — `hint`), `refs.asset_plan` плана страницы, утверждённое на неутверждённом (R-MAT-001), форма манифеста ассетов поверхности по схеме `asset-manifest.schema.json` (предупреждение), у принятых строк манифестов поверхности и продукта — файл (R-REF-001) и `sha256`, равный файлу (R-STRUCT-005, `error`: по нему код-репо сверяет снимок); `--page` — находки и код выхода только по этим страницам, у манифеста — строки этих страниц, манифест продукта не сверяется |
| `plan_to_assets.py --spec-role FILE SLOT` | блок `role` спецификации ассета (`asset-spec.schema.json`): `page_type` словаря и проекция `page_class` |
| `plan_to_assets.py --types [new\|all]` | каркас на каждый тип страницы словаря из плана-образца и его проверка |

Корень данных — `--repo`, переменная `DDD_REPO` или репозиторий скилла; код выхода 0 — нет `error`, 1 — есть, 2 — вызов
или окружение.

## `page_anatomy.py` — анатомия страницы

`page_anatomy.py URL OUT_DIR [--mobile] [--inp] [--quick] [--label PAGE_TYPE] [--crux] [--net [auto|метка]]
[--exit-country CC] [--timezone TZ]` — один прогон «страница × устройство»: секции с ролью (`section_role`) и блоком
(`block`) по словарю site, призывы, формы и согласия, шапка и подвал, заголовки, мета, Open Graph, JSON-LD, платформа,
сторонние домены по категориям, cookie-баннер и трекинг до выбора, LCP, CLS, TBT, FCP, TTFB, показ H1 во времени
(`h1_paint`), лабораторный INP по сценарию, текст без JS, контактный лист секций. Условия лаборатории — `budgets.yaml`
`conditions` через `page_gates.py`: окно первого экрана, телефон — дескриптор Pixel 7 и CPU ×4, десктоп 1440×900; UA —
как у браузера (HeadlessChrome), признак автоматизации не выключается. web-vitals — из npm-зависимостей окружения
(`$DDD_HOME/node`).

- **Выход.** `OUT_DIR/anatomy_<desktop|mobile>.json` (сырые признаки `dom`, классы секций `classes` с top-3 и
  причинами, строка сводки `summary`, `network`, `cmp`, `inp`, `nojs`, `first_screen`, `h1_paint`, `ua`, `webdriver`),
  `sheet_<устройство>.jpg` — контактный лист с границами и подписями секций, `cmp_<устройство>.jpg` — кадр с баннером;
  краткая сводка — в stdout. `anatomy_<устройство>.json` читает `page_gates.py --anatomy` — первое звено ворот после
  сборки.
- **Сеть** — только ключом `--net`: без него замер к сторонним сервисам не обращается (поле `net: unknown`); `--net` или
  `--net auto` — страна и организация сервера (ipinfo.io, IP не сохраняется) и проверка раздельной маршрутизации VPN до
  и после замера; `--net <метка>` — своя метка сети и та же проверка маршрута. `--crux` — поле CrUX через PageSpeed
  Insights (ключ только из `PSI_API_KEY`). Поле `route_ok` — адреса обеих проб маршрута разошлись; `--exit-country CC`
  добавляет сверку страны выхода (без ключа она не сверяется). Часовой пояс браузера — `--timezone` (имя IANA); без
  ключа — `Europe/Moscow` для рынка `ru`, `UTC` для остальных.
- **Классы секций** — эвристики с баллами: для выводов брать роли с `conf` не ниже 0,5, остальные — подсказка; надёжнее
  всего `hero`, `footer`, `faq`, `pricing`, `testimonials`.
- **Ограничения.** Лаборатория — не поле (сеть без замедления, телефон — эмуляция); INP — до четырёх взаимодействий
  после загрузки; антибот и заглушки — `blocked`; сегментация срывается, когда подвал или общая обёртка проглатывают
  страницу (`seg_flag=fail`); «умная» шапка, появляющаяся при прокрутке вверх, не ловится.
- Ключи обслуживания базы — замер и пересчёт корпуса страниц: `--batch` (с `--devices`, `--only`, `--skip-done`,
  `--page-timeout`), `--crux-batch`, метки `--market` и `--industry`, `--reclassify`, `--csv` с `--pages`, `--net-of` —
  отдельной группой в `--help`; замеру страницы проекта они не нужны.

## `page_gates.py` — ворота собранной страницы

Вердикт `accepted` / `accepted_with_notes` / `blocked` по `../../kb/site/07-seo-geo-performance-analytics/page-gates.yaml` с
порогами профиля `<page_type>@L<n>` из `budgets.yaml`; умолчание уровня по типу страницы и правило лидогенерации услуг —
поля `../../kb/creative/01-creative-direction/ambition-levels.yaml`. Браузер утилита не запускает: сводит JSON утилит
замера. Метрику страницы воротами ставит только она; те же метрики, измеренные соседями (`motion_check.py`, зонд 3D),
идут в отчёт зеркалом (серьёзность D) и на вердикт не влияют; ворота эффектов и 3D — слоями отчёта. Числа строк без
профиля — поле `limits` строки `page-gates.yaml`. Цепочка после сборки: `page_anatomy.py` →
`page_accept.py --budget-profile …` → `page_gates.py --brief … --plan … --ready … --anatomy … --accept …` (+
`--motion`, `--gate3d`, `--geo`, `--ia`, `--axe`, `--html`); ключи вердикта из брифа и плана, исход пунктов
`after_build` и вывод JSON для кода — `../README.md § Ворота после сборки`.

| вызов | что делает |
|---|---|
| `page_gates.py --brief FILE --plan FILE [--ready FILE] --anatomy DIR [--accept DIR] [--motion DIR] [--gate3d FILE …] [--json]` | вердикт, строки PASS/FAIL/SKIP с порогом, серьёзностью и источником; профиль и ключи — из плана и брифа, явный ключ (`--profile`, `--jurisdiction ru\|eu\|none` и другие) сильнее; с `--ready` — исход пунктов `after_build` единицы со способом `gates`; JSON — `tool`, `skill_version`, `params`, `verdict`, `B`, `S`, `after_build`; код 1 при B, 2 — ошибка вызова |
| `page_gates.py --resolve landing-lead-services [--site-level L1] [--hot-mobile-share 0.6 --price-band mid]` | профиль (JSON: `id`, `level`, `page_type`, `outcome`, `weight`, `all_levels`, `log`) — его читает сборщик входа холста |
| `page_gates.py --conditions` | условия замера `budgets.yaml` для утилит: окно первого экрана, телефон, десктоп, замок тишины |
| `page_gates.py --selftest` | строки и `limits` ворот, профиль и правило лидогенерации из данных, контракты JSON соседей, зеркала, ключи из брифа и плана, исход пунктов `after_build` (`--ready`) |

| ключ | что читает | какие ворота |
|---|---|---|
| `--anatomy DIR` | `anatomy_<устройство>.json` `page_anatomy.py` | SG-PERF-01…06 (LCP-элемент, H1 в LCP с признаком показа H1), 09; SG-WEIGHT-01…07, 09 (видео — только D); SG-SEO-02, 03; SG-GEO-01; SG-MOB-01 (когда строк `acceptance[]` нет — с пометкой), 02; SG-CONTENT-07; SG-LEGAL-01…05, 07 |
| `--accept DIR` | `accept_<режим>.json` `page_accept.py`: поля `device`, `throttle`, `no_preference` (`lcp`, `first_screen_total_kb`, `weight_measured`, `dom.imgs`, `media_first`, `motion_6s`, `loops`, `console`), `reduce` (`media_kb`, `motion.fail`), `acceptance[]` (`width`, `device`, `overflow_px`; ключ `--acceptance`) | SG-PERF-01/02 (LCP с троттлингом), SG-PERF-06 (lazy, fetchpriority), SG-PERF-14, SG-PERF-16 (энтропия и площадь постера), SG-WEIGHT-01 без анатомии (прогон без замедления), SG-MOB-01 (вылет на телефонных ширинах приёмки), SG-A11Y-03, SG-A11Y-07, SG-CONTENT-04 |
| `--motion DIR` | `<DIR>/results.json` (`<режим>.derived`, `vitals`, `cls`, `net`) и `<DIR>/gates.json` (`rows`) `motion_check.py` | SG-A11Y-03 (петли всей страницы), SG-A11Y-04 (вспышки), SG-A11Y-07 (EG-A11Y-05…07); зеркала LCP, TBT, CLS, веса и шрифтов; слой эффектов |
| `--gate3d FILE …` | JSON `gate_check.py --json` (`rows`: `id`, `check`, `value`, `limit`, `severity`, `status`, `mirror`) | SG-WEIGHT-08 (D), SG-CONTENT-04 (зонд), зеркала LCP, CLS, TBT и веса; слой 3D |
| `--geo FILE` | JSON `geo_probe.py` (флаги `head-kit.yaml checks`) | SG-SEO-01…05, SG-GEO-01…02 (строка `device: raw`) |
| `--ia FILE` | `<id>/ia.json` `ia_probe.py` | SG-SEO-01 (мягкая 404), SG-SEO-06, SG-SEO-08, SG-NAV-01, SG-NAV-02 |
| `--axe FILE` | узлы с адресами `run_axe_targets.py` или `axe.run` | SG-A11Y-01 (контраст ключевых узлов — B, прочих — S; без адресов — S, которое исключение не снимает), SG-A11Y-02 |
| `--plan FILE` | page-plan: `budget_profile` (профиль без `--profile`), `jurisdiction` (основная — первая), `first_screen_policy`, `seo.indexable`, `seo.structured_data`, `x-gate-exception[{id, why, who, until}]` | профиль; строки права; SG-CONTENT-07; условия SEO; исключения (S снимается до `until`, B — никогда) |
| `--brief FILE` | site-brief: `constraints.jurisdiction` (без плана), `search.ai_bots_policy` (`ask` — умолчание `crawlers.yaml`), `ambition.level`, `traffic.sources[]` (доля горячего мобильного трафика, `paid-search`), `decision_context.price_band`, `search.engines` | уровень профиля и правило лидогенерации; флаги ботов; строки права |
| `--html FILE`, `--css FILE …` | сохранённый HTML и CSS | SG-CONTENT-05, SG-CONTENT-06, признаки невидимого H1 (SG-PERF-06), SG-A11Y-08 (clamp кеглей) |
| `--ai-bots-policy`, `--ads-google` / `--no-ads-google` | условия брифа для флагов ботов (без ключа — из `--brief`) | закрытые ИИ-боты при `deny-all` — не дефект; AdsBot — B только для посадочной под Google Ads |

Замер без троттлинга сети (анатомия телефона) для SG-PERF-01 — строка диагностики (`diagnostic`, пометка
`lab-unthrottled`): пункт `after_build` она не решает; для приёмки — `page_accept.py --mobile --throttle`. Ограничения: сторонние КБ первого экрана — верхняя оценка (КБ домена
за сессию); INP-сценарий после загрузки занижен; классы узлов контраста и распознавание призыва — эвристики, ключевой
провал подтверждать кадром. Модуль для утилит замера (`kbpaths.use("site")`, `import page_gates`): `resolve_profile()`,
`profile_value()`, `conditions()`, `cdp_network()`, `mobile_device()`, `heavy_lock()` — одно место условий лаборатории и
тишины машины; `PAUSE_LABELS` и `pause_label_re_js()` — подписи механизма паузы движения для `page_accept.py`,
`motion_check.py` и `marketing_audit.py`.

## `run_axe_targets.py` — axe-core с адресами узлов

`run_axe_targets.py ID URL MARKET OUTDIR` — axe-core на странице (десктоп 1440×900, без кликов и ввода, баннер cookie не
трогается) и для каждого провала `color-contrast` и прочих правил SG-A11Y-01 — селектор, тег, текст, в H1 ли, действие
ли, в форме, в подвале, в первом экране ли, кегль. Выход — `OUTDIR/<ID>.json`: его читает `page_gates.py --axe`, чтобы
отличить H1, лид, призыв и согласие (B) от прочего текста (S). Замок браузера утилита берёт сама; axe-core — из
npm-зависимостей окружения.

## `geo_probe.py` — страница глазами ботов

`geo_probe.py URL [--out DIR] [--id ID] [--render] [--ua-probe]` — без браузера: robots.txt и решение для каждого бота из
`../../kb/site/07-seo-geo-performance-analytics/crawlers.yaml`, `/llms.txt`, код и редиректы страницы, `X-Robots-Tag`,
head (title, description, robots, canonical, hreflang, lang, OG), текст без JS, H1, цены, JSON-LD и микроразметка;
`--render` — ещё Chromium без взаимодействия (доля текста без JS, H1 и главный призыв в сыром HTML; берёт блокировки
браузера сам); `--ua-probe` — запросы с UA ботов (только сигнал). Выход — флаги и решения robots по ботам в stdout, с
`--out DIR` — полный JSON `DIR/<id>.json` (у партии папка по умолчанию — `$DDD_HOME/out/site/geo_probe/`); флаги — по
`head-kit.yaml` `checks`, JSON читает `page_gates.py --geo`. Партия, сводная таблица и пересчёт по сохранённым данным —
`--help`. Не больше одного запроса в секунду на хост; формы не
отправляет. Без `--render` не видит текст, меню и телефон, которые вставляет скрипт.

## `ia_probe.py` — структура многостраничника

`ia_probe.py https://example.ru [--out DIR] [--id ID] [--sample 14]` — без браузера: robots.txt → sitemap.xml → шаблоны
адресов, глубина, языковые префиксы → выборка страниц только из sitemap и корень: шапка, подвал, крошки, `hreflang`,
canonical, контекстные ссылки → ответ на несуществующий адрес (честная 404, мягкая 404, редирект на главную). Выход —
`DIR/<id>/ia.json` и `DIR/<id>/ia.md` (по умолчанию `$DDD_HOME/out/site/ia_probe/`); JSON читает `page_gates.py --ia`.
Вежливость: не больше одного запроса в секунду на хост и 200 запросов на сайт, robots.txt соблюдается, антибот-заглушка
— отметка `blocked` и остановка. Без браузера не видит меню, панели и телефон, которые вставляет скрипт. Обход корпуса
сайтов базы — `--batch` с `--skip-done`: группа «обслуживание базы» в `--help`; сводная таблица и пересчёт по
сохранённому HTML — там же.

## `ab_plan.py` — A/B-тест

Подкоманды: `size` — выборка на вариант для двух долей (поправка Бонферрони для A/B/n), `duration` — дни и полные недели
при заданном трафике с вердиктом, `mde` — обнаружимый эффект, `srm` — соотношение выборок, `fpr` — риск ложной победы,
`analyze` — итог теста (SRM, z-тест двух долей, интервал, FPR), `peeking` — ложные срабатывания при k просмотрах и порог
Pocock. Вывод — текстом, `--json` — JSON; код 1 — SRM или вердикт «нереально», 2 — ошибка вызова или ввода. Ограничения: доли
(конверсии), а не средние выручки; последовательные методы не реализованы.

## `checklist_export.py` и `build_profile.py` — производные файлы базы

- `checklist_export.py` собирает `../../kb/site/09-ai-generation-evaluation/site-checklist.yaml` из таблиц
  `02-site-checklist.md` (пункты `SITE-*` и каталог дефектов `DEF-*`) с проверками целостности; `--check` — YAML
  совпадает с Markdown (код 1 — нет, ничего не пишет); правки — только в Markdown.
- `build_profile.py` собирает `../../kb/site/09-ai-generation-evaluation/ux-marketing-profile.tsv` — решение по каждому
  пункту `UX-*` сводного чек-листа ux для страниц сайта (`keep`, `modify`, `off`, `replaced` с заменой, причиной и
  основанием), таблицу наследования автопроверок `AC-*` (`../../kb/site/09-ai-generation-evaluation/ac-profile.tsv`,
  рядом с профилем) и сводку в `$DDD_HOME/out/site/build_profile/`; решения — в коде утилиты (по блокам с точечными
  исключениями), профиль правится решением и пересборкой. `--check` — профиль и `ac-profile.tsv` на диске совпадают со
  сборкой и сверенной версией чек-листа ux; новая версия чек-листа — отказ записи со списком новых, снятых и
  изменённых пунктов.
