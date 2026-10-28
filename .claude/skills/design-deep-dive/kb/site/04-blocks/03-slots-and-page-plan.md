# Слоты блоков и план страницы (page-plan): модель, поля, сборка из брифа, проекции для сестёр и соседей

Волна 2 · агент E · 2026-09-24 · входы: контракт тройки §3, словарь B, C `01`–`03`, бриф A, copy-deck и copy-slots text,
план ассетов ai-media `01/01` §8, 3d `01/02` §7 и `12-recipes/`, пакет kimi `07-brief-handoff/` · опыты
`99-raw/experiments/E/01-validate`, `02-text-slot-defaults`, `03-saas-demo-brief`

Схемы v1 — `../10-playbooks-contracts/schemas/page-plan.schema.json` и `../10-playbooks-contracts/schemas/blocks.schema.json`; примеры — `../10-playbooks-contracts/examples/lead-services-otves/plans/home.yaml`
(лидогенерация услуг РФ), `../10-playbooks-contracts/examples/saas-okoshko/plans/home.yaml` (SaaS).
Проверка — `../../../scripts/site/site_validate.py` (схема + связи) и `../../../scripts/site/vocab_lint.py`. План — точка S1
тройки: по нему text пишет copy-deck, creative — подачу секций, ai-media — план ассетов, 3d — 3D, kimi получает секции.

## Выжимка для агента

1. **Один план — одна страница или шаблон**; секции по порядку DOM, шапка первой, подвал последним; липкое, баннеры и чат —
   в `overlays`, а не в потоке. [практика] → §3, §4
2. **У секции обязательно: `id`, `role`, `block`, `slots`; у содержательной — ещё `question` и `next_step`**; `job` —
   одной фразой для kimi. `role: other` запрещён. [практика: C 01 §1.1] → §3
3. **Уровень осведомлённости страницы выводи из брифа**: `pages.list[].main_sources` → `meaning.awareness.by_source`;
   записывай `awareness_basis` с долями и правилом сведения. [практика] (сообщение оркестратора 2026-09-24) → §2.1
4. **Политика первого экрана — поле плана** (`offer-cta` по умолчанию; при `paid-search` и у ЛУ — всегда `offer-cta`);
   она же — строка A3 пакета kimi. [практика: C 03 §2] → §2.2
5. **Слот плана ссылается на элемент анатомии блока**: `anatomy` = id элемента или `группа.элемент`; экземпляр повторяемого
   набора — `group: <группа>-N`; `slot` совпадает со слотом элемента. [проверено] → §1.2
6. **Текст в плане не пишется**: `intent` — что сказать, класс длины — из `text_slot_defaults`; тексты — copy-deck. [практика] (контракт §2) → §1.3
7. **Каждое число, цена, отзыв, логотип, человек — data-слот `fact:<id>` с `binds`** на слоты, которые его показывают;
   пробел — `missing:<id>` с `on_missing` (как `fallback` пробела в facts.yaml). [практика] (контракт §3 п. 10) → §1.6
8. **Факт должен подходить слоту по виду** (`fact_kinds` словаря) и иметь разрешение (`pending` — ошибка); блокирующий
   пробел (`blocking: true`) — страница не публикуется. [проверено] → §1.6
9. **Медиа-слот — вход плана ассетов**: роль (`media_role`), цель, источник, подлинность, соотношения по устройствам, зона
   текста, кандидат LCP, alt (id текстового слота). Формат плана ассетов — ai-media, второй не изобретать. [практика] (контракт §3 п. 9) → §1.4
10. **Людей-клиентов, команду, отзывы, работы, скриншоты — только `authenticity: real-only`**; нет материала —
    `source: customer-tbd` и вопрос заказчику. [практика] (решение 15 PLAN; I) → §1.4
11. **3D-слот — только с постером того же ракурса**, загрузка после LCP, призыв и форма работают до 3D; в тарифах и формах
    3D нет. [практика] (поправка PLAN №22) → §1.5
12. **action-слот — с действием словаря и стилем**: `primary` — главный призыв (повторяется), `secondary` — второй путь,
    `channel` — телефон и мессенджер того же действия, `link` — служебное. [практика] → §1.7
13. **События плана — триггер, цель и действие**; id событий назначает P (`events.yaml`), план их не выдумывает. [практика] → §1.7
14. **`treatment{}` — пустой контейнер до подсхемы creative**; поля не выдумывать. [практика] (контракт §3 п. 12) → §3, §6.2
15. **Ровно один H1** (`seo.h1` = «секция.слот»); `first_screen.must_show` и `message_match` ссылаются на существующие
    слоты. [проверено] → §2.2
16. **Подстановка по UTM — белый список вариантов**, до первой отрисовки, с вариантом по умолчанию и параметром события.
    [практика: C 02 §3.3] → §2.2
17. **`budget_profile` = `<page_type>@<уровень амбиций>`** — ячейка профилей P; пороги в плане не пишутся. [практика] → §2.3
18. **Копия текста для copy-deck получается прямым переносом полей** (id → section_id, role → section_role, anatomy →
    site_slot_id, group → group); `fact_ids` слота — из `data[].binds`. [проверено: схема copy-deck v1] → §6.1
19. **Секции kimi — `site.sections[{id, job}]` из плана без самодельных id**. [практика] [проверено] → §6.5
20. **Перед сдачей — `site_validate.py` и `vocab_lint.py` с кодом 0**; info-строки о `use.slot_types` — сигнал для text, не ошибка. [проверено] → §7

## 1. Модель слота

### 1.1. Шесть видов слотов

| Вид (`slot_kind`) | Что | Владелец значений | Поля слота в плане |
|---|---|---|---|
| `text` (79 id) | заголовки, лиды, подписи, ответы, мета, письма | text (правила по id слота) | `id`, `slot`, `anatomy`, `group`, `heading`, `intent`, `length`, `variants` |
| `media` (17) | главный визуал, фото, скриншоты, иконки, логотипы, видео, карты, OG | ai-media (план ассетов), I (подлинность) | `media_role`, `goal`, `source`, `authenticity`, `task`, `ratio`, `text_zone`, `lcp_candidate`, `loading`, `alt`, `caption`, `motion` |
| `3d` (2) | 3D-объект, 3D-сцена | 3d (рецепты) | `recipe`, `poster`, `load`, `cta_before_3d` |
| `data` (8) | ссылки на факты | text (`facts.yaml`), заказчик | `fact`, `binds`, `on_missing` |
| `action` (9) | призывы, формы, ссылки, телефон, мессенджер, магазины, скачивание | site: F (формы), P (события) | `action`, `target`, `style`, `label`, `form`, `event` |
| `treatment` (3) | роль в ритме, эффект, уровень движения | creative | в плане — контейнер `treatment{}` (не слоты) |

Мета, Open Graph, фавиконы и письма после формы — слоты уровня страницы (`scope: page` словаря) → `page_slots`.

### 1.2. Элемент анатомии и слот плана

- В `blocks.yaml` у блока — элементы `{id, slot}` и группы (повторяемые наборы). В плане слот секции: `id` — локальный,
  уникален в секции; `slot` — id словаря; `anatomy` — элемент блока (`headline`) или `группа.элемент` (`step.title`);
  `group` — экземпляр `группа-N` (`step-1`). По умолчанию `anatomy` = `id` (кроме data-слотов — у них анатомия только явная).
- Пример (`steps`, «Отвес»): `{id: step-1-title, slot: step-title, anatomy: step.title, group: step-1, heading: h3}` и
  `{id: step-1-body, slot: step-body, anatomy: step.body, group: step-1}`.
- Подписи кнопок окна просмотра — слоты `viewer.close-label`, `viewer.prev-label`, `viewer.next-label`, экземпляр
  `viewer-1`.
- Обязательные элементы блока (`required: true`, `adds` варианта) должны быть в плане; кратность элемента без `max` — 1
  (кроме data); число экземпляров группы — в пределах `min`–`max` группы. Проверяет `site_validate.py` (PL-A05).

### 1.3. Текстовые слоты: назначение, длина, факт

- **Назначение** — `def` словаря и `purpose` copy-slots.yaml; блок уточняет своё (`purpose` элемента), план — что сказать
  (`intent`: «4,8 из 5 на Яндекс Картах по 214 оценкам»). Текст пишет text в copy-deck.
- **Класс длины** — `text_slot_defaults` в `blocks.yaml` (выведено из `copy-slots.yaml`,
  target RU): label ≤ 3 слов, phrase 4–10, sentence 11–25, paragraph 26–80, long > 80. Распределение 79 слотов: phrase 37,
  sentence 16, label 16, paragraph 10. [проверено]
- **Нужен ли факт** — `fact` (always, if-claim, never) как `fact_required` text: `hero-proof`, `stat-value`,
  `testimonial-quote`, `case-result`, `pricing-price`, `guarantee-text`, `footer-legal`, `announcement` — всегда.
- **10 слотов site без правил text** (запрос S1): `disclaimer`, `ad-marking`, `event-meta`, `quiz-question`, `quiz-option`,
  `result-summary`, `contact-info`, `cookie-text`, `article-date`, `article-sources` — класс длины и правило факта пока
  оценка E (помечено в `text_slot_defaults`).
- **Уровень заголовка** — `heading`: H1 — только `headline` hero или `article-title`; секции — H2; карточки и шаги — H3.

### 1.4. Медиа-слоты → план ассетов ai-media

| Поле плана | Поле плана ассетов (ai-media `01/01` §8) | Правило |
|---|---|---|
| `<секция>-<id>` | `slots[].id` | уникально на странице |
| `id` секции | `slots[].section` | вместо свободной строки (предложение B к ai-media) |
| `media_role` | `role` | informational — несёт смысл (alt обязателен); decorative — alt пустой |
| `goal` | `goal` | что показать за 3 секунды |
| `source` | `source` | real, edit-real, generate, code, template; `customer-tbd` — ждём материалы |
| `task` | `task_codes` | подсказка; итог выбирает ai-media (`routing.yaml`) |
| `ratio.desktop`, `ratio.mobile` | `variants[]` | свой кадр телефона 4:5 или 9:16 у hero и битов истории |
| `text_zone` | `variants[].text_zone` | где будет текст поверх кадра |
| `lcp_candidate`, `loading` | `delivery` | кандидат LCP — eager и `fetchpriority=high` |
| `alt` → id `image-alt` | `alt` | текст пишет text |
| `authenticity` | `policy.no_ai_subjects`, `ai_fit` | real-only: люди-клиенты, команда, отзывы, работы, товар, скриншоты |
| `motion` | `motion.type` | параметры движения — creative; пауза и reduce — ворота |

- Генератор каркаса плана ассетов из медиа-слотов — `plan_to_assets.py` (J, волна 3); бюджеты ассетов — ai-media, профиль
  страницы — P. [практика] (контракт §3 п. 9)

### 1.5. 3D-слоты → 3d

- `recipe: recipe:<id>` — рецепт `../../3d/12-recipes/` (`01-hero-product`, `05-scroll-showcase`,
  `12-model-viewer-ar` …); `poster` — id медиа-слота того же ракурса (запасной кадр и кандидат LCP); `load: after-lcp`
  (по умолчанию), `on-visible`, `on-interaction`; `cta_before_3d: true`.
- Когда 3D помогает — товар с неочевидной формой, объяснение устройства, варианты комплектации, кампания и портфолио;
  вредит — там, где задача быстро прочитать и купить (`../../3d/01-web-3d-landscape/02-when-3d-budgets-loading.md`
  §1.3, §7). Поправка к этому правилу для сайта — `01-blocks-catalog.md` §3.2 (PLAN, поправка 22).

### 1.6. data-слоты: факты, пробелы, связи

- `fact: fact:<id>` — факт из `facts.yaml` проекта (`refs.facts`); `missing:<id>` — пробел из `missing[]` того же файла;
  `binds` — слоты этой секции (text, media), которые показывают факт; `on_missing` — что делать до ответа заказчика:

| `on_missing` | = `fallback` пробела text | Действие |
|---|---|---|
| `omit-block` | `omit-block` | секция снимается (логотипов нет — `logo-wall` не ставится) |
| `omit-slot` | — | снимается слот (фото кейса), секция остаётся |
| `rewrite-without` | `rewrite-without` | текст без этого утверждения («один прораб на объект» не пишем) |
| `placeholder` | `placeholder` | `[PLACEHOLDER: …]`; при `blocking: true` страница не публикуется (реквизиты) |

- **Проверки** (E/01): факт есть; вид факта ∈ `fact_kinds` data-слота (`metric-ref` — metric, rating, research; `price-ref` —
  price, offer-terms, promo …); разрешение не `pending`/`denied`; `binds` ведут на слоты секции; тип связанного текстового
  слота есть в `fact.use.slot_types` — иначе info (у демо-фактов text `use` уже реальных мест: цена в `subheadline`,
  `list-item`, `result-summary`; фото человека — медиа-слоты не описаны).
- **Минимум по типу страницы** (виды фактов, без которых страница не публикуется) — `proof.required_kinds` брифа A
  (`../10-playbooks-contracts/schemas/site-brief.schema.json`, allOf): у SaaS — `demo` (скриншоты); валидатор A даёт SB-P01, если в фактах нет
  ни вида, ни блокирующего пробела (опыт E/03 на демо «Окошко»).

### 1.7. action-слоты и события

- `action` — id словаря (macro: `booking`, `start-trial`, `request-demo` …; micro: `view-pricing`, `explore-product`,
  `read-more`, `log-in`); `target` — как `conversion.target` брифа (`anchor`, `route`, `url`, `tel`, `messenger`, `store`);
  `style`: `primary` (главный призыв; повторяется), `secondary` (второй путь иным стилем), `channel` (телефон, мессенджер
  того же действия), `link` (служебное); `label` — id текстового слота с подписью.
- Готовое сообщение мессенджера — текстовый слот `messenger-prefill` той же секции, на него ссылается `target.prefill`.
- `form` — `ref` (набор полей F, `lead-forms.yaml#…`), `fields_visible_max`, `steps`, `consent` (`separate-checkbox` по
  умолчанию для РФ — I), `success` (`inline` или `thank-you-page`).
- `events[]` секции: `trigger` (view, click, submit, start, step, play, expand, scroll-depth, copy, error), `target` (слот
  или секция), `action`; `event: event:<id>` — только из `events.yaml` P. Вариант подстановки hero — параметр события.

## 2. page-plan: поля страницы

| Поле | Откуда | Кто читает |
|---|---|---|
| `id`, `page_type`, `url` | бриф `pages.list[]`, карта сайта G | все; copy-deck `page_id` |
| `goal`, `primary_action`, `secondary_actions`, `cta_target`, `secondary_goal` | бриф `conversion`, `meaning.conversion.secondary_goal` | F, P, text, kimi (`site.cta`) |
| `awareness`, `awareness_basis` | бриф `pages.list[].main_sources` → `meaning.awareness.by_source` | C-порядок, text (иерархия) |
| `traffic[]` | бриф `traffic.sources[]` (с `entry_page` = id страницы) | C, text, P |
| `macrostructure`, `macrostructure_family`, `macrostructure_alternatives` | выбор по C 01 §4.3 | creative, kimi (`direction.macrostructure`) |
| `first_screen_policy`, `first_screen{}` | C 03 §2; бриф `promise_of_source` | kimi A3, text (обещание), K |
| `length` | C 02 §1.3 | K |
| `budget_profile`, `ambition_level` | P (`budgets.yaml`), бриф `ambition` | P, creative, ворота |
| `navigation` | C 02 §2.3, G | G, kimi |
| `seo`, `legal`, `analytics` | H, I, P | H, I, P, K |
| `treatment{}` | creative | creative |

Запись утверждения — `approval {by, date, note}` в корне плана; у плана `approved` она обязательна по смыслу
(валидатор — warning PL-U01).

### 2.1. Происхождение осведомлённости

- Правило оркестратора (2026-09-24): уровень страницы выводится из `pages.list[].main_sources` брифа через
  `meaning.awareness.by_source`. Запись: `awareness_basis: {from: brief-main-sources, main_sources, by_source[{traffic_source,
  awareness, share}], rule}`.
- Несколько уровней на одной странице: порядок — под уровень с наибольшей долей; остальные — вариантными слотами (рейтинг в
  hero для `product-aware`) или отдельной страницей, если различаются ≥ 2 признака из четырёх (C 02 §3.4). «Отвес»: Директ
  0,5 `solution-aware`, карты и рекомендации 0,4 `product-aware` → одна страница, рейтинг в первом экране.
- Смысла в брифе нет (демо) — `from: assumption` и уровни по таблице источников C 02 §4 с вопросом заказчику.

### 2.2. Первый экран

- `first_screen_policy` — `offer-cta` (обещание и призыв в hero), `offer-cta-header` (призыв в шапке или липкой панели),
  `poster` (образ и признак продолжения, призыв в шапке; только кампании L2, портфолио, письма, манифесты; не при
  `paid-search` и не у ЛУ и SaaS под рекламу). Вариант hero должен ей отвечать (`variants[].first_screen_policy` в блоке);
  у варианта каталога `first_screen_policy` — значение или список допустимых политик.
- `must_show` — «секция.слот», которые обязаны быть выше черты первого экрана (C 03 §1.3 по типу страницы); `core_words_max`
  — ядро ≤ 40 слов (text `hero-core`).
- `message_match[]` — источник, его обещание, что совпадает (`subject`, `price`, `offer`, `geo`, `audience`, `action`,
  `visual`) и в каких слотах (C 02 §3.1).
- `variant_map` — параметр (`utm_term`, `utm_content`, `keyword` …), `render: server` (до первой отрисовки), вариант по
  умолчанию, белый список вариантов с условиями и слотами; тексты вариантов — copy-deck; вариант — параметр события (P).
  Сырой `utm_term` в разметку не вставлять (C 02 §3.3).

### 2.3. Бюджет, амбиции, навигация, SEO, право, аналитика

- `budget_profile: <page_type>@<L0|L1|L2>` — ячейка профилей P (`budgets.yaml`, волна 2); пороги LCP, INP, веса — у P.
- `ambition_level` — id `L0`–`L2` (определения — creative; умолчания: лендинги L1, кампании L2 — решение заказчика 15).
- `navigation.header`: `landing-minimal` (платный трафик), `site` (внутри сайта; архетип — G); `anchor_nav` — страница
  > ≈ 8 экранов десктопа.
- `seo`: `indexable`, `canonical`, `h1` («секция.слот»), `structured_data` (типы — H), `ssr_required: true` (смысл, цены,
  призывы — в HTML); `legal`: согласие (`separate-document` для РФ), баннер cookie, маркировка, реквизиты (I);
  `analytics`: системы, цели по `action`, загрузка после согласия (P, I). Поля с префиксом `x-` — расширения владельцев.

## 3. Секция

| Поле | Обязательно | Смысл |
|---|---|---|
| `id` | да | = `site.sections[].id` kimi = `section_id` copy-deck = `section` плана ассетов |
| `role` | да | `section_role` словаря; `other` — нет |
| `block`, `variant` | блок — да | id блока и его структурного варианта |
| `question`, `next_step` | да (кроме шапки, подвала, служебных) | вопрос посетителя и куда секция ведёт |
| `job` | желательно | одна фраза для kimi (`site.sections[].job`) |
| `objections`, `carries` | по брифу | id возражений `meaning` и опор иерархии text |
| `anchor`, `condition` | по случаю | якорь (#zamer); условие существования (до даты акции) |
| `mobile[]` | желательно | `stack`, `accordion`, `rail`, `hide-decor`, `reframe`, `toggle`, `none` |
| `slots{text, media, 3d, data, action}` | да | §1 |
| `treatment{}` | контейнер | подача — creative (пусто до C1) |
| `notes{seo, a11y, conversion, legal, structure}` | по случаю | заметки для H, I, F, C |
| `events[]` | для действий | §1.7 |

- Проверки секции (E/01): блок есть и не устарел; роль среди `serves` блока (иначе warning); вариант объявлен; обязательные
  элементы заполнены; id слотов уникальны; ровно один H1 на странице.

## 4. `overlays` и `page_slots`

- `overlays[]` — вне потока: `sticky-cta` (`on` на телефоне, `hide_when`: видим призыв hero, форма, финал, клавиатура),
  `cookie-banner` (`auto` — по юрисдикции и скриптам, I), `chat-widget` (по брифу `policies.chat_widget`), `capture-popup`
  (`off` — решение 15), `contact-channels` (плавающий кластер мессенджеров). Значения `on`/`off` в YAML — в кавычках.
- `page_slots` — мета, OG, фавиконы, письма: `meta-title`, `meta-description`, `og-title`, `og-description`, `og-image-alt`,
  `og-image` (шаблон 1200×630), письма после формы (`email-*`, механика — F, тексты — text).

## 5. Процедура «бриф → план страницы»

| Шаг | Действие | Артефакт | Проверка |
|---|---|---|---|
| 1 | Взять страницу из брифа: `pages.list[]` (тип, цель, действие, источники) | `page.id`, `page_type`, `primary_action` | тип и действие — в словаре |
| 2 | Вывести уровень осведомлённости из `main_sources` и `by_source`, записать правило | `awareness_basis` | сумма долей ≤ 1; правило записано |
| 3 | Выбрать макроструктуру: три формы разных семейств, по фактам (нет чисел — не `stat-led`) | `macrostructure`, семейство, альтернативы | семейство = `layout_family` |
| 4 | Политика первого экрана по макроструктуре и источнику | `first_screen_policy`, `must_show`, `message_match` | `paid-search` → `offer-cta` |
| 5 | Порядок ролей по типу и уровню (C 01 §3.2–3.3), хвост — из возражений | список ролей | длина в диапазоне типа (C 02 §1.3) |
| 6 | Роль → блок и вариант (`01`, `02`), без повтора блока в одном варианте | `sections[].block`, `variant` | роль ∈ `serves` блока |
| 7 | Разложить слоты по анатомии; тексты — `intent` | `slots.text[]` | обязательные элементы есть |
| 8 | Факты: каждое утверждение — `data` с `binds`; пробелы — `missing` с `on_missing` | `slots.data[]` | вид факта и разрешение |
| 9 | Медиа и 3D: роль, источник, подлинность, соотношения, LCP, постер | `slots.media[]`, `slots.3d[]` | real-only у людей и работ |
| 10 | Действия и события: главный призыв повторяется, второй путь иным стилем | `slots.action[]`, `events[]` | действие в словаре |
| 11 | Overlays, мета, SEO, право, аналитика — ссылками на владельцев | `overlays`, `page_slots`, `page.seo/legal/analytics` | баннер и согласие — по юрисдикции |
| 12 | Проверка и вопросы заказчику | `site_validate.py`, `vocab_lint.py`, `open_questions` | код 0; блокирующие пробелы названы |

Полная процедура «бриф → карта → планы → пакет → приёмка» — J (`../10-playbooks-contracts/01-procedure-brief-to-pages.md`, волна 3).

## 6. Проекции

### 6.1. text — copy-deck v1

| page-plan | copy-deck (`../../text/10-templates-recipes/copy-deck.schema.json`) |
|---|---|
| `site` | `site` |
| `page.id`, `page_type`, `awareness` | `page_id`, `page_type`, `awareness` |
| `sections[].id` | `section_id` и `site_section_id` |
| `role`, `block`, `question` | `section_role`, `block`, `question` |
| текстовый слот `id`, `slot`, `anatomy`, `group` | `slot_id`, `slot_type`, `site_slot_id`, `group` |
| `data[].fact` с этим слотом в `binds` | `fact_ids` / `missing_ids` |
| `intent` | `notes` (что сказать) |
| путь к плану | `page_plan_ref` |

- Правило текста — по `slot_type` (= `slot`) в `copy-slots.yaml`, поле `site_slot` там же = `anatomy` плана.
  `primary_action` copy-deck — текст «глагол + объект», в плане — id действия; соответствие — text.

### 6.2. creative — `treatment{}` и варианты

- Контейнер на странице и в секции; подсхема — creative (`treatment.schema.json` после C1), ключи site для treatment-слотов
  (`visual-role`, `effect-ref`, `motion-level`) — предложение имён. Визуальные варианты и эффекты — `block-treatments.yaml`
  по 83 id блоков; структурный `variant` плана — ограничение для подачи (split, фон, плакат).

### 6.3. ai-media — план ассетов

- Медиа-слоты плана → слоты плана ассетов по таблице §1.4; `page.page_type` → `page_type` плана ассетов по строкам
  `broader` crosswalk (например, `landing-lead-services` → `corporate`); формат плана ассетов не меняется.

### 6.4. 3d — 3D

- 3d-слоты → рецепты по `recipe:`; постер — медиа-слот плана ассетов; бюджет доли 3D — 3d, вся страница — P.

### 6.5. kimi — пакет исполнителя

- `sections[].id` и `job` → `site.sections[{id, job}]` (других ключей `lint_brief` не принимает); `site.cta{label, target}`
  ← подпись главного призыва (copy-deck) и `cta_target`; `direction.macrostructure` ← `macrostructure_family` (grid-led,
  document-led, poster-led; `flow` → document-led до решения kimi); `first_screen_policy` → строка A3 в `ACCEPTANCE.md`
  (три формулировки — C 03 §2.3); тексты — `copy.md` из copy-deck. Проекция — `site_brief_to_kimi.py` (J).

### 6.6. site: F, H, I, P, G, K

- F — `form.ref`, поля и шаги, места призывов; H — `seo`, разметка по блокам, `ssr_required`; I — `legal`, согласия,
  баннер, реквизиты, подлинность; P — `budget_profile`, события, цели; G — `navigation`, `related-links`, шаблоны;
  K — ворота и чек-лист по плану (что из плана обязано попасть в TASK и ACCEPTANCE).

## 7. Проверка плана

- `site_validate.py` (коды `PL-*`): JSON Schema 2020-12 + связи (блок, вариант, анатомия, обязательные элементы, факты и
  их вид, разрешения, binds, label, alt, события, H1, семейство макроструктуры, профиль бюджета, «секция.слот» в первом
  экране и SEO); id словаря — `vocab_lint.py`.
- Для `site_validate.py` (J, v1): длины текстов — не проверять (text); добавить сверку `awareness_basis` с брифом,
  `entry_page` источников с `page.id`, фактов `use.page_types` с `page_type`, согласованность `overlays` с `policies` брифа.

## 8. Примеры

| Пример | Что показывает |
|---|---|
| `page-plan-lead-services-otves.yaml` | ЛУ РФ, `split-studio`, `offer-cta`, осведомлённость из трёх источников, строка акции с условием снятия, калькулятор с 2 полями, гарантия у цены, форма после цены, кейс против блокера срока, рейтинг площадки, сравнение подходов, FAQ-остаток, финал со второй целью, подвал с блокирующим пробелом реквизитов, липкий призыв |
| `page-plan-saas-okoshko.yaml` | SaaS, `workbench`, продукт в рамке (скриншоты `customer-tbd`), ряд чисел вместо логотипов (логотипов нет — `omit-block`), боли для соцсетей, функции «утверждение + доказательство», кейс с типичным результатом рядом, тарифы с переключателем периода и условием SMS, FAQ про данные и отмену |
| `page-plan-event-*.yaml` | мероприятие: `event-schedule`, дата и формат в первом экране, программа с часовым поясом, спикеры с согласием, билеты, площадка |

## Частые ошибки

- Самодельные id секций и блоков (`how`, `final_cta`) — рвут связку с текстами, ассетами и kimi.
- Текст вместо `intent` в плане — дублирует copy-deck и уходит мимо правил text.
- Число без data-слота или data без `binds` — факт не доходит до текста.
- `missing` без `on_missing` — генератор допишет выдумку.
- Медиа без `media_role` и alt-слота; люди и скриншоты без `real-only`.
- 3D без постера или 3D в тарифах и форме.
- Второй H1 (в шапке или в hero-цитате); `seo.h1` не совпадает со слотом.
- `poster` при `paid-search`; `variant_map` со вставкой сырого `utm_term`.
- Липкий призыв и баннер cookie в потоке секций вместо `overlays`; `on`/`off` без кавычек (YAML читает как true/false).
- `treatment{}` с выдуманными полями до подсхемы creative; пороги бюджета в плане вместо ссылки на профиль P.

## Чек-лист

- [ ] Все id — из словаря и `blocks.yaml`; `vocab_lint.py` и `site_validate.py` — код 0?
- [ ] `awareness_basis` выведен из `main_sources` брифа, правило сведения записано?
- [ ] Политика первого экрана соответствует макроструктуре и источнику; `must_show` и `message_match` ссылаются на слоты?
- [ ] У содержательных секций есть `question` и `next_step`; у всех — роль, блок, вариант?
- [ ] Обязательные элементы блоков заполнены; группы — в пределах min–max?
- [ ] Каждое число, отзыв, цена, человек — `fact:` с `binds`; пробелы — `missing:` с `on_missing`?
- [ ] Медиа: роль, источник, подлинность, соотношения, кандидат LCP, alt?
- [ ] Действия: главный призыв повторяется, второй путь `secondary`, каналы `channel`; события без выдуманных id?
- [ ] Overlays и `page_slots` вынесены из потока; `treatment{}` пуст до C1?
- [ ] Открытые вопросы и блокирующие пробелы перечислены в `open_questions`?

## Открытые вопросы и противоречия

1. **Подсхема `treatment`** — нет до C1 (creative не запущена); ключи site — предложение.
2. **id событий** — P (`events.yaml`) ещё пишется; в плане — триггеры без `event:`.
3. **Наборы полей форм** — F (`lead-forms.yaml`) ещё пишется; `form.ref` в примерах не заполнен.
4. **`budget_profile`** — формат ключа `<page_type>@<уровень>` — предложение E; P может назвать профили иначе.
5. **`use.slot_types` фактов text** уже реальных мест в планах — сделать ориентиром или расширить (вопрос text, S1).
6. **Проекция `flow` в kimi** (`document-led` или `flow-led`) — решение kimi (C 01 §4.1).
7. **Секции, общие для нескольких страниц** (шапка, подвал многостраничника) — в каждом плане или в шаблоне G (`site-map`) —
   решение G и J.

## Источники

- [S1] Контракт тройки v2.1, `../99-raw/notes/triad-contract-2026-09-24.md` §2, §3 (п.3, 9, 10, 12, 15), §5.
- [S2] Словарь B `../02-site-types/vocabulary.yaml` v0 r2; `02-vocabulary-and-crosswalk.md` §4.5–4.7. Свой агент.
- [S3] C `../03-page-structure/01-narratives-and-section-order.md` §1.1, §3–4; `02-length-goal-message-match.md` §1.3, §2–4;
  `03-first-screen-and-mobile.md` §1.3, §2, §5. Свой агент.
- [S4] A `../10-playbooks-contracts/schemas/site-brief.schema.json`, `../10-playbooks-contracts/examples/lead-services-otves/site-brief.yaml`,
  `03-site-brief.md`; валидатор
  `../../../scripts/site/site_validate.py`. Свой агент.
- [S5] text `../../text/10-templates-recipes/copy-deck.schema.json` (v1), `04-copy-by-block/copy-slots.yaml`,
  `02-strategy-messaging/facts.schema.yaml`, примеры фактов «Отвес» и демо «Окошко» (`99-raw/experiments/E/`). Сестра.
- [S6] ai-media `../../ai-media/01-web-assets-landscape/01-asset-slots-by-page-type.md` §2.1, §8. Сосед.
- [S7] 3d `../../3d/01-web-3d-landscape/02-when-3d-budgets-loading.md` §1.3, §5, §7; `12-recipes/`. Сосед.
- [S8] kimi `../../kimi-research/07-brief-handoff/templates/brief.yaml`, `build_package.py` (`site.sections`, `REQ_LANDING`,
  A3). Сосед.
- [S9] Опыты E/01 (валидатор), E/02 (классы длины), E/03 (демо-бриф SaaS). [проверено]
