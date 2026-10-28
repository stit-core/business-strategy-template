# Единый словарь идентификаторов системы v0 и таблица соответствия

Волна 1 · агент B · 2026-09-24 · веб: 8 источников целиком, 11 по разделам; словари соседей и сестёр — 11 файлов (разбор
скриптом) · опыты `99-raw/experiments/B/01-landing-csv`, `02-crosswalk`, `03-lint-foreign`, `04-selftest` ·
артефакты: `vocabulary.yaml` (v0, draft rev. 2, 406 id в 15 пространствах), `crosswalk.tsv` (685 строк),
`../../scripts/site/vocab_lint.py`.

## Выжимка для агента

1. **Id только из `vocabulary.yaml`**: в `site-brief`, `site-map`, `page-plan`, `blocks.yaml`, чек-листах — ни одного
   самодельного id; проверка — `vocab_lint.py` до сдачи файла. → §8 [проверено: опыт B/04]
2. **Формат id**: kebab-case латиницей `^[a-z0-9]+(?:-[a-z0-9]+)*$`; единственное исключение — `L0`, `L1`, `L2`
   (как в контракте тройки). → §2 [практика] (соглашение базы)
3. **Id не переименовывается**: устаревший получает `status: deprecated` и `replaced_by`; удалять нельзя. → §2 [практика]
4. **Ссылка на чужой id — с префиксом**: `block:hero-media`, `slot:headline`, `section-role:faq`, `page-type:landing-saas`;
   чужие пространства — `effect:` (creative), `copy-rule:` и `fact:` (text), `task:` (ai-media), `recipe:` (3d). → §2 [практика] (контракт §3 п. 15)
5. **Новый id** — только через заметку «## Для B» (волна 1) или «## Для J» (волны 2–3) с определением в одну строку;
   до решения — пометка `(новый id)` и `status: proposed`. → §3 [_common.md, метод п.11]
6. **Роль ≠ блок**: `section_role` — работа секции в сюжете (порядок — C), `block` — анатомия и набор слотов (карточка — E);
   один блок служит разным ролям (`logo-wall` → `proof-logos`, `integrations`). → §4.3–4.4 [практика]
7. **Блок = назначение + набор слотов**; раскладка той же анатомии (split, по центру, на весь экран) — вариант блока (E),
   визуал — creative; поэтому H2 «Split diptych» Hallmark — вариант `hero-media`, а не отдельный id. → §4.4 [практика]
8. **Текстовые слоты site = `slot_type` text**: 69 id `copy-slots.yaml` взяты как есть (`equal`); правила текста — text по
   тому же id. → §6 [проверено: генератор B/02]
9. **Слот `data` — только ссылка на факт** `fact:<id>` нужного вида (`fact_kinds` из `facts.schema.yaml` text); нет факта —
   нет слота. → §4.5 [практика] (контракт §3 п. 10)
10. **Значения `treatment` и уровней амбиций задаёт creative**: у site только id слотов `visual-role`, `effect-ref`,
    `motion-level` и id `L0`–`L2`. → §4.5, §9 [практика] (контракт §3 п. 12)
11. **`measurement-only`** (`other`) — только для замера M; в планах — ошибка линтера. → §4.3 [проверено: опыт B/04]
12. **`out-of-scope`** (магазин, веб-сервис, медиа, документация, маркетплейс) — чтобы метить, а не строить. → §4.1–4.2 [практика] (решения 4, 8 PLAN)
13. **`action.level` — типичный**: макро-действие страницы назначает `page-plan`; вехи процесса (начал форму, шаг квиза) —
    события P, не `action`. → §4.6 [практика: NN/g 2024]
14. **`macrostructure` — 29 id с семейством `layout_family`** (grid, document, poster, flow — свод C); ось kimi grid-led /
    document-led / poster-led — проекция семейства, а не id; политика первого экрана — `first_screen_policy` (C). → §4.7
    [мнение вендора: Hallmark; практика C]
15. **Чужой термин → наш id** — по `crosswalk.tsv`: `relation` описывает источник относительно нашего id (equal, narrower,
    broader, related, none); при нескольких строках бери equal → narrower → related → broader. → §5 [проверено: опыт B/03]
16. **Проекция в чужие форматы** (ai-media `page_type`, kimi `project.type`) — по строкам `broader` crosswalk, не по памяти;
    свободные строки соседей (`primary_action` kimi) — через проекцию J. → §5.3, §7
17. **Чужие форматы линтуй с картой путей** (`--no-default-map --map site.sections.id=section_role`): у соседей ключи `role`,
    `family`, `id` значат другое (31–34 ложные ошибки без этого). → §8 [проверено: опыт B/03]
18. **Словарь покрывает соседей**: план ассетов ai-media — 12 из 14 терминов, 2 без пары по делу; `landing.csv` — 115 из 115
    терминов; бриф «Кварц» — 4 из 8 id секций уже свои, 4 самодельные. → §7 [проверено: опыты B/01, B/03]
19. **Версии**: v0 (B, волна 1) → S0 сёстрам → замечания волны 2 и сестёр → v1 (J, волна 3); поле `checked` — дата сверки. → §2 [PLAN]
20. **Не называй CTA действием**: CTA — призыв (слот `cta-primary`), действие посетителя — `action` (омоним OOUX у ux). → §4.6
    [практика] (поправка PLAN №9)

## 1. Зачем словарь и кто им пользуется

До словаря в системе было 5 несогласованных словарей у ai-media (19 русских названий слотов, свободная строка `section`,
enum `page_type` плана ассетов, другой enum `page_type` спецификации, `slot` рубрик, 24 слага маршрутов), свои id секций у
kimi (`site.sections[].id` — свободные) и временный словарь text (аудит MEDIA §4.8; контракт §6 п.1). Связать «план
страницы → план ассетов → маршрут → рубрику → тексты» автоматически было нельзя.

| Потребитель | Что берёт |
|---|---|
| site: M (замер), C (роли, формы), E (блоки, слоты, `page-plan`), F, G, H, P, I, K, J | все пространства; M — классы секций и блоков (`detect`), P — `action` для `events.yaml`, I — `jurisdiction` |
| text | `slot` (правила по id), `section_role`, `page_type`, `awareness`, `traffic_*` |
| creative | `block` (варианты и эффекты по id), `section_role`, `ambition_level`, слоты `treatment` |
| ai-media | `page_type` → свой enum (crosswalk), `section_role` → поле `section`, медиа-`slot` |
| 3d | слоты `3d`, `block` (hero-media, feature-spotlight, interactive-demo) |
| kimi | `site.sections[].id` ← `section_role` или `block`; `project.type` ← `site_type` |

## 2. Принципы словаря

- **Формат**: id — kebab-case латиницей; у каждого — `name` (по-русски) и `def` (одна строка); у файла — `version`, `revision`,
  `status` (draft → released на S0 → v1), `checked` (дата сверки).
- **Статусы**: `active`; `proposed` (ждёт владельца темы: C, E, G, creative, text; использовать можно); `deprecated`
  (+ `replaced_by`; линтер предупреждает); `out-of-scope` (метка вне рамок); `measurement-only` (только замер).
- **Неизменность**: id не переименовывается и не удаляется; смысл не меняется молча — правка определения фиксируется в
  отчёте агента и в crosswalk (если меняется соответствие).
- **Префиксы ссылок** (`ref_prefixes` в YAML): `site-type:`, `page-type:`, `section-role:`, `block-family:`, `block:`,
  `slot-kind:`, `slot:`, `macrostructure:`, `action:`, `awareness:`, `traffic-temperature:`, `traffic-source:`,
  `jurisdiction:`, `ambition:`. Чужие (`foreign_prefixes`): `effect:`, `treatment:` (creative), `copy-rule:`, `fact:` (text),
  `task:` (ai-media), `recipe:` (3d), `event:` (P), `req:` (I). В YAML и TSV допустима короткая ссылка на раздел соседа
  `<база>:<папка>-<файл>#<§>` (контракт §3 п.15).
- **Одинаковая строка в двух пространствах** допустима, если блок — каноническая реализация роли (`faq` — роль и блок,
  `footer`, `header`, `lead-form`, `cta-band`, `article-body`); префикс снимает двусмысленность.
- **Исключение формата**: `L0`, `L1`, `L2` (`id_pattern_exceptions`) — как в контракте и PLAN creative.

## 3. Как добавить или изменить id

1. Агент пишет в своих заметках «## Для B» (волна 1) или «## Для J» (волны 2–3): пространство, id, название, определение,
   зачем (какой случай не покрыт), пример использования.
2. До решения — использует id с пометкой `(новый id)`; в машиночитаемых файлах — как есть (линтер покажет ошибку — это
   сигнал, не дефект сдачи).
3. B или J: принимает (строка в `vocabulary.yaml`, `status: proposed` до подтверждения владельцем темы), сводит с
   существующим (строка crosswalk `equal` или `narrower`) или отклоняет с причиной в отчёте.
4. После правки: `python3 ../../../scripts/site/vocab_lint.py --check-crosswalk` (проверка ссылок),
   `vocab_lint.py --selftest`.
- **Принято в волне 1** (заметки M, журнал text): роли `header`, `services`, `promo`, `audience`, `other`
  (measurement-only) и блоки `service-cards`, `audience-grid` (M); источники трафика `retargeting`, `maps-local`,
  `social-organic`, `marketplace`, `messenger`, `offline` (text B1); роль `specs`, слоты `spec-row`, `price-old`,
  `stat-source` (text B2); `article-date`, `article-sources` (text G); предложения E text `promise`, `image-caption`,
  `announcement`; от C (12:40) — поле `layout_family` у макроструктур, пространство `first_screen_policy`, роли
  `cross-sell` (10 из 30 страниц замера C) и `seo-text` (5 из 30).
- **Не принято как id site**: роль ux `meta` для мета-слотов (C, G text) — это поле `ux_role` у text; у site мета-слоты
  различаются `scope: page`. Составной слот `hero-core` — правило text (≤ 40 слов), не id.

## 4. Пространства имён

| Пространство | Id | Владелец значений | Сверено с text | Ключевые поля |
|---|---|---|---|---|
| `site_type` | 14 (9 + 5 вне рамок) | B, J; карты — G | — | `multipage`, `priority` |
| `page_type` | 36 (33 + 3 вне рамок) | B, J | 18 из 18 временного словаря и 13 из 13 корпуса — equal | `class`, `genre`, `priority` |
| `section_role` | 42 | id — B; определения и порядок — C | 28 из 28 — equal | `group` |
| `block_family` | 16 | B; состав — E | — | — |
| `block` | 84 | id — B; анатомия — E; визуал — creative | — | `family`, `serves`, `detect` |
| `slot_kind` | 6 | контракт §3 п.3 | — | — |
| `slot` | 118 (79 text, 17 media, 2 3d, 8 data, 9 action, 3 treatment) | id — B, E; тексты — text | 63 временного + 69 `copy-slots.yaml` — equal | `kind`, `scope`, `fact_kinds` |
| `macrostructure` | 29 | id — B; свод и семейства — C | — | `source`, `layout_family` |
| `first_screen_policy` | 3 | C (условия §2.2 файла `03`) | — | — |
| `action` | 23 (18 macro, 5 micro) | B; события — P | — | `level`, `commitment` |
| `awareness` | 5 | B; смысл — A, text B1 | 5 из 5 — equal | — |
| `traffic_temperature` | 3 | B | 3 из 3 — equal | — |
| `traffic_source` | 18 | B; атрибуция — P | 9 из 9 — equal + 6 предложений B1 | `temperature_hint`, `channel` |
| `jurisdiction` | 6 | B; требования — I | — | `support` |
| `ambition_level` | 3 | creative (определения, бюджеты) | — | `ref` |

### 4.1–4.2. `site_type` и `page_type`

Определения, действия, трафик и обязательные страницы — `01-site-and-page-taxonomy.md` §2–§5. `page_type.class`: `landing`
(9), `multipage` (19), `content` (2), `utility` (3); `genre` связывает тип с жанром линтера text (landing, site-page, article).
`priority` — приоритет заказчика (решение 10). Вне рамок: `ecommerce-store`, `web-app`, `media-portal`, `docs-site`,
`marketplace`; страницы `ecommerce-catalog-page`, `ecommerce-product-page`, `web-app-screen`.

### 4.3. `section_role` — группы сюжета (черновик B для C)

| `group` | Роли |
|---|---|
| `chrome` | `header`, `footer`, `utility`, `other` (measurement-only) |
| `promise` | `hero` |
| `problem` | `problem` |
| `value` | `solution`, `benefits`, `how-it-works`, `product-demo`, `specs`, `audience`, `integrations`, `story` |
| `proof` | `proof-logos`, `proof-stats`, `testimonials`, `case-studies`, `awards-press`, `portfolio`, `team` |
| `offer` | `services`, `offer`, `pricing`, `comparison`, `promo`, `cross-sell` |
| `risk` | `guarantee`, `objections`, `faq` |
| `action` | `cta-band`, `lead-form`, `final-cta` |
| `info` | `about`, `contacts`, `event-program`, `article-body`, `related`, `seo-text`, `legal`, `confirmation`, `not-found` |

Группы совпадают с «формулой конверсионного лендинга» Tilda (первый экран → рассказ о проекте → выгоды → блоки доверия →
целевое действие) [мнение вендора] и с ролями задания C; финальные определения, обязательность по типам и порядок — C
(`../03-page-structure/01-narratives-and-section-order.md`).

### 4.4. `block_family` и `block`

| Семейство | Блоки |
|---|---|
| `header-nav` | `header`, `announcement-bar`, `anchor-nav`, `breadcrumbs` |
| `hero` | `hero-text`, `hero-media`, `hero-form`, `hero-input`, `hero-stat`, `hero-quote`, `hero-letter`, `hero-carousel` |
| `proof` | `logo-wall`, `stat-strip`, `testimonial-cards`, `testimonial-single`, `review-aggregate`, `case-cards`, `case-study`, `before-after`, `awards-press`, `credentials` |
| `value` | `feature-grid`, `feature-bento`, `feature-alternating`, `feature-tabs`, `feature-spotlight`, `benefit-list`, `steps`, `product-showcase`, `video-showcase`, `interactive-demo`, `audience-grid`, `pain-points`, `integrations-grid`, `spec-sheet`, `prose`, `media-band` |
| `offer` | `service-cards`, `pricing-cards`, `pricing-table`, `pricing-single`, `comparison-table`, `offer-details`, `key-facts`, `promo-offer`, `guarantee` |
| `conversion` | `lead-form`, `quiz`, `calculator`, `callback-request`, `booking-widget`, `email-capture`, `lead-magnet`, `contact-channels`, `app-download` |
| `cta` | `cta-band`, `sticky-cta`, `capture-popup` (по умолчанию выключен — решение 15; на трафике Директа запрещён) |
| `faq` | `faq` |
| `about-team` | `about-story`, `team-grid`, `founder-note`, `timeline`, `job-list` |
| `contacts` | `contact-details`, `location-map` |
| `portfolio-gallery` | `portfolio-grid`, `gallery` |
| `event` · `course` | `event-agenda`, `speakers-grid` · `curriculum` |
| `resources-blog` | `article-cards`, `article-body`, `author-bio`, `resource-list`, `related-links` |
| `footer` · `utility` | `footer` · `cookie-banner`, `thank-you`, `not-found`, `legal-text`, `chat-widget`, `other` (measurement-only) |

- Правило различения: отдельный id — если отличается **назначение или набор слотов** (у `hero-form` есть поля формы и
  согласие, у `hero-stat` — число из факта); только раскладка — вариант (E). `key-facts` (параметры предложения) отделён
  от `stat-strip` (доказательство), потому что у доказательства обязателен факт и источник (`stat-source`), а у параметра —
  нет.
- Поле `detect` — подсказка распознавания в DOM для замера M (например, `logo-wall`: ≥ 4 мелких картинок в ряд, alt —
  названия компаний), **не норма**; поле `serves` — роли, которые блок обычно реализует (для таблицы C).
- Поправка к `../kimi-research/05-reviews-practice/03-default-look-k3.md §5.3` для сайта: «no marquee» — запрет визуального
  приёма, а блок `logo-wall` с вариантом бегущей строки законен при паузе (WCAG 2.2.2), потому что бегущая строка — вариант
  подачи (creative), а не отдельный блок.

### 4.5. `slot_kind` и `slot`

- `text` (79): 69 = `slot_type` text (`copy-slots.yaml`, включая предложения E: `promise`, `stat-source`, `price-old`,
  `spec-row`, `image-caption`, `announcement`) + `article-date`, `article-sources` (предложение G text) + 8 новых site:
  `disclaimer` (оговорка у утверждения), `ad-marking` («Реклама», рекламодатель, erid — 38-ФЗ ст. 18.1), `event-meta`
  (дата, время, место), `quiz-question`, `quiz-option`, `result-summary` (итог квиза или калькулятора), `contact-info`
  (адрес, часы), `cookie-text`. Мета-слоты и письма — `scope: page`. `messenger-prefill` — готовое сообщение мессенджера
  (текст, уровень секции).
- `media` (17): `hero-visual`, `background`, `photo`, `product-photo`, `screenshot`, `illustration`, `icon`, `logo` (клиента,
  партнёра, СМИ — не генерировать), `brand-logo`, `avatar`, `video`, `diagram`, `cover-image`, `document-image`, `map`,
  `og-image`, `favicon`. Коды задач (`task:IMG-HERO-PHOTO` …) и план ассетов — ai-media (`01-asset-slots-by-page-type.md §8`).
- `3d` (2): `model-3d`, `scene-3d` → рецепты 3d (`recipe:`).
- `data` (8): `fact-ref` (любой вид), `testimonial-ref` [testimonial, expert-quote], `client-ref` [client, partner],
  `metric-ref` [metric, rating, research], `price-ref` [price, offer-terms, promo], `case-ref` [case], `person-ref` [person],
  `credential-ref` [award, certificate, press] — виды из `facts.schema.yaml` text (22 вида).
- `action` (9): `cta-primary`, `cta-secondary`, `form`, `link`, `phone-link`, `messenger-link`, `email-link`,
  `app-store-link`, `download-link`; у слота — id `action` и событие P.
- `treatment` (3): `visual-role`, `effect-ref`, `motion-level` — значения creative (контейнер `treatment{}` в `page-plan`).

### 4.6. `action`

Macro: `lead-request`, `request-quote`, `callback-request`, `call`, `message`, `booking`, `request-demo`, `sign-up`,
`start-trial`, `purchase`, `preorder`, `join-waitlist`, `event-registration`, `download`, `subscribe`, `install-app`,
`apply-job`, `visit-location`. Micro: `view-pricing`, `watch-video`, `explore-product`, `read-more`, `log-in` (служебное).
`commitment` (low, medium, high) — порог для посетителя [практика] (синтез B): подписка и лист ожидания — low, заявка и
звонок — medium, покупка и визит — high; F использует его для числа полей и места формы, A — для брифа. NN/g делит микро на
вехи процесса и вторичные действия [S6]: вехи — события `events.yaml` (P), вторичные — micro `action`.

### 4.7. `macrostructure` и `first_screen_policy`

21 форма Hallmark (kebab-case названия, `source: hallmark:NN`) и 8 вне Hallmark: `sales-longread`, `quiz-funnel`,
`form-first` (рынок РФ и `landing.csv`), `scroll-story` (сайт-референс W3, `landing.csv`), `pricing-first`, `comparison-led`,
`event-schedule`, `directory` (`landing.csv`). C принял все 29 id и свёл их в `../03-page-structure/01-narratives-and-section-order.md`
§4.2 с семейством `layout_family`: grid (8), document (11), poster (8), flow (2 — `quiz-funnel`, `form-first`; новое семейство C
для страниц, где убеждение идёт через ввод посетителя). Ось kimi `grid-led` / `document-led` / `poster-led` — группы Hallmark
(«one grid-led like Bento, one document-led like Long Document, one poster-led like Manifesto», `SKILL.md` стр. 286); проекция:
flow → `document-led` (или `flow-led` — предложение kimi от C). Поле названо `layout_family`, а не `family`: ключ `family`
занят семейством блоков в карте `vocab_lint.py`.
`first_screen_policy` — поле `page-plan` по заметке C: `offer-cta` (по умолчанию), `offer-cta-header`, `poster`; условия и
примеры — `../03-page-structure/03-first-screen-and-mobile.md` §2.2.

### 4.8. `awareness`, `traffic_*`, `jurisdiction`, `ambition_level`

- `awareness` — 5 уровней Шварца (id text как есть); что меняют на странице — A и text B1
  (`../text/02-strategy-messaging/02-awareness-hierarchy-objections.md`).
- `traffic_temperature` — cold, warm, hot; `def` пространства: температура ≠ осведомлённость;
  `traffic_source` — 18 (9 text + 6 предложений B1 + `paid-display`, `influencer`,
  `internal`); `temperature_hint` — типичная температура, не правило; `channel` — группа для атрибуции (P).
- `jurisdiction` — `ru` (по умолчанию, решение 11), `eu` (профиль по запросу), `kz`, `by`, `us`, `other` (не покрыты v0).
- `ambition_level` — `L0`, `L1`, `L2`; определения и бюджеты — `../creative/PLAN.md`, «Стартовые позиции» §1
  (стр. 238–253, `[гипотеза]` до агента A creative); умолчания решения 15: сервисы L0, лендинги L1, кампании L2.

## 5. `crosswalk.tsv`

### 5.1. Формат

Колонки строго: `source_base	source_file	source_section	source_vocab	source_term	namespace	our_id	relation	note`. Пути
соседей — относительные от корня базы (`../ai-media/...`); внешние — URL, в скобках — файл репозитория или дата. `relation`
описывает **источник относительно нашего id**: `equal` — тот же смысл; `narrower` — термин источника уже (наш шире);
`broader` — термин источника шире (по строке на каждый наш id); `related` — пересекаются; `none` — пары нет, `our_id` пуст,
причина в `note`. Таблицу сверяет `vocab_lint.py --check-crosswalk`: колонки строго по формату, `relation` — из перечня,
каждый `our_id` есть в словаре своего пространства, у `none` — `our_id` пуст и причина в `note`.

### 5.2. Покрытие (2026-09-24 12:35, перепроверено 12:49)

| Источник | Строк | Что покрыто |
|---|---|---|
| text | 234 | временный словарь целиком (6 жанров, 18 `page_type`, 28 ролей, 63 `slot_type`, 5 `awareness`, 3 температуры, 9 источников), 69 `slot_type` + составной `hero-core` из `copy-slots.yaml`, 13 `page_type` корпуса, 13 предложений агентов text |
| ai-media | 213 | `01/01` §2.1 (19 слотов), §3 (8 типов), §8 (`page_type` плана — проекция всех наших типов, `section`, id слотов примеров, `role`), `asset-spec.schema.json` (`page_type` — проекция, `role.section`, `role.slot`, `role.priority`, `text_zone.purpose`), рубрики (`slot`), `routing.yaml` (24 слага), `sites.csv` (19 значений `type`) |
| hallmark | 85 | 21 макроструктура, 14 доменов трио, 50 архетипов (H1–H9, S1–S5, F1–F6, C1–C4, T1–T4, Ft1–Ft8, N1a–N13) |
| tilda | 53 | 28 префиксов индекса блоков (2021, вторично) + 25 функциональных блоков Tilda Education |
| ui-ux-pro-max | 34 | 34 паттерна `landing.csv` |
| schema.org | 23 | 11 подтипов `WebPage` + 10 типов сущностей |
| relume | 18 | категории библиотеки (неполно: список рисуется скриптом) |
| 3d | 16 | 12 рецептов, 3 цели страницы `01/02` §7 |
| unbounce | 13 | 13 «типов» лендингов |
| jack-roberts | 10 | карточка брифа скилла: типы сайта и результаты |
| claude-design | 9 | словарь брифа холста: `project.type`, `direction.macrostructure`, `site.sections[].id`, `product.primary_action`, признаки описания §2 |
| ux | 1 | CTA OOUX (омоним) |

Всего 709 строк: equal 350, related 156, broader 110, none 51, narrower 42. Все термины временного словаря text и
`copy-slots.yaml` — `equal`: переименований у сестры не требуется.

### 5.3. Как пользоваться

- **Чужой термин → наш id**: `vocab_lint.py файл --crosswalk 02-site-types/crosswalk.tsv --source-base <база>`; при
  нескольких строках брать `equal` → `narrower` → `related` → `broader`.
- **Наш id → чужой формат** (проекция): строки `broader` с нужным `source_vocab` (например, `page_type` плана ассетов:
  `landing-lead-services` → `corporate`, `landing-event` → `campaign`); J встраивает это в `plan_to_assets.py` и
  `site_brief_to_kimi.py`.
- `none` — осознанное «нет пары»: вне рамок (маркетплейс, магазин), свойство, а не словарь (`role: informational`,
  `priority: lcp`), или правило другой базы (`hero-core`).

## 6. Сведение с text (S0)

- **Совпадения**: все 63 `slot_type` временного словаря, все 69 `copy-slots.yaml` (файл прочитан в 11:35, перепроверен в
  12:49; изменений с 11:14 нет), 28 ролей, 18 типов страниц, 13 значений корпуса, 5 уровней осведомлённости, 3 температуры,
  9 источников — `equal`, id взяты как есть. Колонка `site_slot` в `copy-slots.yaml` может заполняться тем же id.
- **Расхождения и как закрыть**:
  - у site есть 10 текстовых слотов, которых нет в `copy-slots.yaml`: `disclaimer`, `ad-marking`, `event-meta`,
    `quiz-question`, `quiz-option`, `result-summary`, `contact-info`, `cookie-text` и предложения G `article-date`,
    `article-sources` → text добавляет правила текста (или отвечает «правил не нужно»);
  - `portfolio-page` в корпусе text — главные студий; у site допустимы оба прочтения (§7.7 файла 01);
  - жанры text (`landing`, `site-page`, `article`, `meta`, `geo`, `email-form`) — не пространство site: связь через
    `page_type.genre` и `slot.scope`;
  - роль ux `meta` (C, G text) — поле text `ux_role`, у site не нужна;
  - составной `hero-core` (≤ 40 слов) — правило text, не id.
- **Новые id site, о которых text надо знать**: роли `header`, `specs`, `offer`, `services`, `audience`, `promo`,
  `cross-sell`, `story`, `seo-text`, `legal`, `utility`, `confirmation`, `not-found`; источники `paid-display`, `influencer`, `internal`; типы страниц §4 файла 01
  (например, `services-index-page`, `form-page`, `thank-you-page`).

## 7. Сведение с соседями и предложения (соседей не правим)

| Сосед, файл § | Что было | Предложение | Почему |
|---|---|---|---|
| ai-media `01-web-assets-landscape/01-asset-slots-by-page-type.md` стр. 47–48 и чек-лист стр. 591 | «секции — из UX» (висячая ссылка) | заменить ссылкой на `../site/02-site-types/vocabulary.yaml` и порядок C | UX лендинги исключает (`ux 13/02:10`) |
| там же §8 `slots[].section` | свободная строка | перечисление `section_role`; `section` = id секции `page-plan` | опыт B/03: `social-proof`, `meta` не сводятся однозначно |
| там же §8 `page.page_type` и `asset-spec.schema.json` `role.page_type` | два разных enum | один enum ai-media + проекция из `page_type` site по crosswalk | два словаря в одной базе |
| `11-evaluation-qa/rubrics/*.json` `slot` | hero, section, product, icon, og | медиа-`slot` site (`hero-visual`, `background`, `product-photo`, `icon`, `og-image`) | «section» не различает фон и иллюстрацию |
| `13-routing-matrix/routing.yaml` `slots` | 24 слага (секции и ассеты вперемешку) | разделить: секция → `section_role`, ассет → `slot` | связка «маршрут → рубрика → план» |
| kimi `07-brief-handoff/templates/brief.yaml` `site.sections[].id` | свободные id (`how`, `object3d`, `price`, `final_cta` в «Кварце») | id = `section_role` (или `block`), `lint_brief` — проверка по `vocabulary.yaml` | опыт B/03: 4 из 8 id самодельные |
| kimi `brief.yaml` `project.type` | landing \| webapp | + поле-ссылка `x_site` с `site_type` и `page_type` | тип сайта теряется |
| kimi `brief.yaml` `direction.macrostructure` | grid-led \| document-led \| poster-led | id `macrostructure` site + `layout_mode` | группа не задаёт форму |
| 3d `12-recipes/00-how-to-use.md` | задачи рецептов без связи со слотами | тег рецепта `slot:model-3d` / `scene-3d` / `background` и `block:` | подбор рецепта по `page-plan` |

## 8. `vocab_lint.py` в конвейере

- Где запускать: E — на `blocks.yaml` и примерах `page-plan`; G — на `site-map`; K — на чек-листе (Markdown: префиксные
  ссылки); J — на всех YAML базы и итоговых примерах; M — классы замера с `--allow-measurement`.
- Своё: `python3 ../../scripts/site/vocab_lint.py 04-blocks/blocks.yaml --keys-as-ids blocks=block`; чужое:
  `--no-default-map --map site.sections.id=section_role --crosswalk 02-site-types/crosswalk.tsv --source-base claude-design`.
- Проверено: `--selftest` 9/9 (опыт B/04); на плане ассетов ai-media — 16 id, 12 сопоставлены через crosswalk, 3 — «нет пары» по
  делу; на брифе «Кварц» — 4 самодельных id секций (опыт B/03). Ограничения: не проверяет, что слот разрешён блоку и что факт
  существует — это `site_validate.py` (J).

## 9. Для сестёр (S0)

- Пути: `../site/02-site-types/vocabulary.yaml`, `../site/02-site-types/crosswalk.tsv`, описание — этот
  файл; утилита — `../../scripts/site/vocab_lint.py`.
- **text**: id слотов совпадают — `site_slot` = `slot_type`; нужны правила текста для 10 слотов §6; роли и типы страниц
  временного словаря — те же id; `site_id` временного словаря заполняется тем же значением.
- **creative**: ждём значения `ambition_level` (определения, бюджеты — `ambition-levels.yaml`) и значения слотов
  `visual-role`, `effect-ref`, `motion-level` (подсхема `treatment`); варианты и эффекты — по id `block` (84) и
  `section_role` (42).

## Частые ошибки

1. Самодельные id секций в брифе и плане (`how`, `final_cta`) — ломают связку с текстами и ассетами.
2. Snake_case и CamelCase (`final_cta`, `HeroSplit`) — формат id kebab-case.
3. Раскладка как отдельный блок (`hero-split`, `hero-centered`) — это варианты одного `hero-media`.
4. Роль и блок перепутаны (`role: logo-wall`) — линтер ловит только, если id нет в пространстве; различайте по смыслу.
5. Число в слоте `data` без факта (`stat-value` «10 000+» без `fact:`) — выдуманное доказательство.
6. Переименование id вместо `deprecated` — у сестёр ломаются правила по старому id.
7. Линтер по умолчанию на чужом формате — десятки ложных ошибок (`role: informational`, `family: Golos Text`).
8. `other` из замера в плане страницы — только для классификации.
9. Проекция в формат соседа «по памяти» вместо строки crosswalk (`landing-lead-services` → `corporate`, не `saas-landing`).

## Чек-лист

- [ ] Все id файла есть в `vocabulary.yaml` (`vocab_lint.py` — код 0)?
- [ ] Новый id оформлен через «## Для B / J» и помечен `(новый id)`?
- [ ] Ссылки на чужие id — с префиксом (`effect:`, `fact:`, `task:`, `recipe:`)?
- [ ] Каждый слот `data` ссылается на факт нужного вида?
- [ ] Значения `treatment` и уровней — из creative, а не придуманы site?
- [ ] После правки словаря сверен `crosswalk.tsv` (`vocab_lint.py --check-crosswalk` без ошибок)?
- [ ] Для чужих форматов линтер запущен с картой путей?

## Открытые вопросы и противоречия

1. **Проекция семейства flow в kimi** — `document-led` сейчас или новое `flow-led` (предложение kimi от C); до ответа kimi —
   `document-led`.
2. **Гранулярность `hero-*`**: `hero-carousel` и `hero-letter` — отдельные анатомии или варианты? Решает E по карточкам.
3. **`services` против `offer` против `pricing`** — три роли оффера; C может свести к двум.
4. **`commitment` действий** — синтез B без измерения; F проверит на данных форм.
5. **Relume**: список категорий неполный (страница категорий рисуется скриптом); Tilda — индекс 2021 года (вторично).
6. **Юрисдикции `kz`, `by`, `us`** — только метки; покрытия правом нет (решение 11: РФ по умолчанию, ЕС — профиль).

## Источники

- [S1] Контракт тройки v2.1, `99-raw/notes/triad-contract-2026-09-24.md` §2, §3, §6 п.1 — рамка словаря.
- [S2] Аудит MEDIA §4.8, аудит KIMI §2.3, §2.8, §8.2 — `99-raw/notes/audit-2026-09-24/`.
- [S3] Временный словарь text v0 (06:51) — 189 строк; сверено скриптом.
- [S4] `../text/04-copy-by-block/copy-slots.yaml` (11:14; прочитан 11:35, перепроверен 12:49) — 69 slot_type.
- [S5] `../text-research/03-corpus-measured/corpus.tsv` — 13 значений `page_type`; `../site-research/99-raw/notes/sync/T1-text-2026-09-24/facts.schema.yaml` — 22 вида фактов.
- [S6] NN/g «Macro vs. Micro Conversions», 2024-07-19, https://www.nngroup.com/articles/micro-conversions/ — уровни действий.
- [S7] ai-media `01-web-assets-landscape/01-asset-slots-by-page-type.md` §2.1, §3, §8; `05-prompting/asset-spec.schema.json`; `11-evaluation-qa/rubrics/*.json`; `13-routing-matrix/routing.yaml` (v1, 2026-09-24); `01-web-assets-landscape/sites.csv`.
- [S8] kimi `07-brief-handoff/templates/brief.yaml`; `05-reviews-practice/03-default-look-k3.md` §3.3; `91-videos/digests/weoV4dm-X1A.md`; `99-raw/experiments/F/03-package-from-description/landing-kvarts/brief.yaml`.
- [S9] 3d `12-recipes/00-how-to-use.md` §1; `01-web-3d-landscape/02-when-3d-budgets-loading.md` §7.
- [S10] Hallmark (MIT) `references/macrostructures.md`, `structure.md`, `component-cookbook.md`, `SKILL.md` стр. 286 — https://github.com/Nutlope/hallmark.
- [S11] ui-ux-pro-max (MIT) `data/landing.csv` — https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.
- [S12] Relume Library — https://www.relume.io/react/marketing-components, дока «How to use the Relume Webflow Library» (2026-09-24) — мнение вендора, неполно.
- [S13] Индекс блоков Tilda, https://roman-kosov.ru/blocks/ (2021-08-25) — вторично; Tilda Education «Анатомия лендинга», https://tilda.education/courses/landing-page/anatomiya-landing-page/ (2024) — мнение вендора.
- [S14] schema.org «WebPage», https://schema.org/WebPage (2026-09-24) — спецификация.
- [S15] Unbounce «13 types of landing pages», https://unbounce.com/landing-pages/7-types-of-landing-page/ (2024-06-07) — мнение вендора.
