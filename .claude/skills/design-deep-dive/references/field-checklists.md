# Чек-листы полей по файлам

Что должно быть в файле, чтобы он закрылся, куда он ссылается, какие ошибки в нём типичны и в каком порядке его копать.
Поля и значения — из схемы базы или формы шаблона (пути `kb/…` — от папки скилла, `…` — папка проекта
`docs/projects/<slug>`); чек-лист их не заменяет, а говорит, на что смотреть при закрытии. Статусы и кто закрывает —
`docs/projects/_template/site/README.md § Форма и статусы` и `docs/projects/_template/design/README.md § Статусы`; как
повышать и понижать статус — `draft-stable.md`; какой этап пишет файл — `phases.md`.

Во всех файлах:

- **закрыто** — статус в самом файле, и файл проходит схему на этом статусе: у схем с условиями по статусу `proposed` и
  `approved` требуют больше полей, чем `draft`;
- **формулировки** — от владельца (`CLAUDE.md` §3): агент пишет варианты «допущением», факт — только с источником;
- **ссылки** — путём от файла; поля другого файла не копируются, на них ссылаются;
- **forward-only** — журнал процесса уходит при закрытии, в файле остаётся текущее значение и запись того, как оно
  получено и проверено (`.claude/rules/forward-only.md § Машинные файлы слоёв`).

## Слой страницы и уровень продукта

### `site-brief` — `…/site/<surface>/site-brief.yaml`

Схема — `kb/site/10-playbooks-contracts/schemas/site-brief.schema.json`.

- **Закрыто:** `project.status: approved` и `project.approval`. Всегда нужны `version`, `checked`, `project`,
  `site_type`, `business` (`name`, `what`, `goal`), `conversion.action`, `constraints.jurisdiction`, `languages`,
  `questions`; с `proposed` — ещё `traffic`, `offer`, `proof` (`facts_ref`, `required_kinds` по типу сайта), `pages`,
  `ambition`, `search`, `analytics`, `decision_context` и `meaning_ref`; при `approved` вопросы приоритета 1 —
  `assumed`, `answered` или `withdrawn`. Тема — блок `themes`: `default`, `dark` (`needed` и `why`), `switcher` — при
  двух темах.
- **Ссылки:** `project.slug` — slug проекта; `site_type` соответствует роду поверхности;
  `proof.facts_ref: ../../facts.yaml`, `meaning_ref: meaning.yaml`, `brand.ref: ../../design/brand.yaml`;
  `intake.raw_ref` — строка `docs/business/material.md`, если материал заведён; первая `constraints.jurisdiction` — она
  же `jurisdiction` фактов; каждый получатель заявок — строка `integration.md` с этой поверхностью (нет строки — долг в
  заметке, закрытию брифа он не мешает).
- **Anti-patterns:** уровень со `source` не `default` без `note`; секции конверсии выше L0; `site_type` из рамок
  `out-of-scope`; мудборд в `references[]`; поля бренда вместо `brand.ref`; разбор брифа в самом брифе; метрика `kpi`
  без источника-системы; вопросы `withdrawn` в утверждённом брифе.
- **Порядок:** `intake` → `project`, `site_type`, `primary_page_type` → `business` → `constraints` → `pages` →
  `ambition` → `brand`, `references`, `assets_available` → `questions`; на этапе воронки — `conversion`, `traffic`,
  `offer`, `analytics`, `business.kpi`, `search`, действия страниц в `pages.list`.

### `meaning` — `…/site/<surface>/meaning.yaml`

Схема — `kb/text/02-strategy-messaging/meaning.schema.yaml`.

- **Закрыто:** `status: approved`. Нужны `meaning_version`, `date`, `status`, `audience`, `awareness`, `positioning`,
  `value_proposition`, `objections`, `languages`. У каждого утверждения — основание `basis`: `assumption` — с
  `question_id`; `voc`, `fact`, `public-page`, `research`, `inferred` — с `ref`; доля допущений выше порога
  text 09/02 §1.1 — доклад заказчику, а не повод переписать основание. Возражение `answered` — с доказательствами
  (`proof_ids`) или снятием риска (`risk_reversal_ids`).
- **Ссылки:** `site` — slug проекта; `proof_ref` = `proof.facts_ref` брифа; `basis.ref` вверх — путь
  `docs/<слой>/<файл>.md#<slug>`; границы — из `boundary.md` и возможностей проекта.
- **Anti-patterns:** утверждение без основания; позиционирование оценочными словами вместо наблюдаемого отличия;
  обещание того, чего продукт не делает; число текстом вместо ссылки на факт.
- **Порядок:** аудитория → осведомлённость по источникам трафика → позиционирование → ценностное предложение →
  возражения и снятие риска → границы → открытые вопросы.

### `hierarchy` — `…/site/<surface>/hierarchy/<page-id>-<awareness>.yaml`

Схема — `kb/text/02-strategy-messaging/message-hierarchy.schema.yaml`.

- **Закрыто:** `status: approved`. Нужны `hierarchy_version`, `date`, `status`, `page` (`page_type`, `awareness`),
  `core_message`, `first_screen`, `pillars`, `sections`. Опора с `proof_status: has-proof` — с `proof_ids`; опора не из
  слоя трения — с `value_theme_refs`.
- **Ссылки:** `meaning_ref`; `page.page_id` — id страницы брифа или карты; секции — роли секций плана.
- **Anti-patterns:** одна иерархия на трафик разной осведомлённости; опора без доказательства; пустой `not_said` при
  названных границах смысла.
- **Порядок:** страница и уровень осведомлённости → главное сообщение → первый экран → опоры → секции → порядок
  доказательств → `not_said`.

### `site-map` — `…/site/<surface>/site-map.yaml` (род `site`)

Схема — `kb/site/10-playbooks-contracts/schemas/site-map.schema.json`.

- **Закрыто:** `status: approved`; `built` в стратегии не ставится. Нужны `site_map_version`, `checked`, `status`,
  `site`, `site_type`, `refs`, `derived_from`, `languages`, `url_policy`, `templates`, `pages`, `chrome`, `linking`,
  `utility_pages`, `build_order`; шаблон `collection` — с `collection`; языков больше одного — структура не `single`;
  поиск включён — есть страница результатов.
- **Ссылки:** `site` — slug проекта; у шаблона — путь к плану; `build_order` — главная первой; поля коллекций — ссылки
  на факты.
- **Anti-patterns:** посадочная под платный трафик отдельной поверхностью вместо страницы сайта; записи коллекций CMS в
  карте; разные шапки у страниц одного сайта; страница без плана.
- **Порядок:** шаблоны и страницы → коллекции → `chrome` → перелинковка → служебные страницы → адреса и языки →
  `build_order`.

### `page-plan` — `…/site/<surface>/plans/<page-id>.yaml`

Схема — `kb/site/10-playbooks-contracts/schemas/page-plan.schema.json`; подача `treatment` — ниже, в слое дизайна.

- **Закрыто:** `status: approved`. Нужны `page_plan_version`, `checked`, `status`, `site`, `refs` (`brief`, `facts`,
  `blocks`, `vocabulary`), `page` (`id`, `page_type`, `goal`, `primary_action`, `awareness`, `traffic`,
  `macrostructure`, `macrostructure_family`, `first_screen_policy`, `budget_profile`, `ambition_level`, `jurisdiction`,
  `locale`) и `sections`. У секции — `id`, `role`, `block`, `slots`; у ролей, кроме шапки, подвала, служебных и
  юридических, — ещё `question` и `next_step`. Слоты: текст — `id`, `slot`; медиа — `media_role`; 3D — `poster`;
  данные — `fact`; действие — `action`. Исключение ворот `x-gate-exception` — `id`, `why`, `who` и срок `until`.
- **Ссылки:** `page.id` — id страницы брифа или карты, он же `page_id` copy deck; `refs.brief: ../site-brief.yaml`,
  `refs.facts: ../../../facts.yaml`, `refs.copy_deck` — пишется на этапе плана, а файл появляется на этапе `copy`: до
  него аудит даёт подсказку, а не ошибку; `refs.asset_plan` и `refs.treatment` — в слой дизайна; `block` —
  id `blocks.yaml`; слоты — `vocabulary.yaml#slot`; `fact:<id>`, `event:<id>`, `form.ref` — на форму `lead-forms.yaml`.
- **Anti-patterns:** kind `block`, `section`, `slot`; значения подачи до выбора направления; `built`; секция без блока
  каталога; форма страницы без двух альтернатив; призыв не к главному действию.
- **Порядок:** цель и главное действие → осведомлённость и трафик → форма страницы и альтернативы → первый экран →
  секции по ролям → слоты → навигация, SEO, право, аналитика → профиль бюджета и исключения ворот → пустые контейнеры
  `treatment`.

### `copy-deck` — `…/site/<surface>/copy/<page-id>.yaml`

Схема — `kb/text/10-templates-recipes/copy-deck.schema.json`.

- **Закрыто:** страница и выбранные варианты `approved` — только человеком (`copydeck.py approve --by`), с записью, кто
  и когда. Нужны `version`, `date`, `site`, `lang`, `pages`; у страницы — `page_id`, `page_type`, `sections`; у секции —
  `section_id`, `slots`; у слота — `slot_id`, `slot_type`, `variants`; у варианта — `id`, `text`, `status`. У каждого
  слота выбран вариант (`chosen`, `selection`); записи проверок — с актуальным `text_hash`; журнала правки и отклонённых
  вариантов в утверждённом файле нет.
- **Ссылки:** стык с планом — `docs/projects/_template/site/README.md § Связь copy deck с планом`; `page_plan_ref`,
  `facts_ref`, `voice_ref`, `meaning_ref`, `hierarchy_ref`; `fact_ids` — только существующие факты; `legal_category` и
  `jurisdiction` — как в брифе.
- **Anti-patterns:** тексты без плана; число или отзыв текстом без `fact_ids`; `approved` от агента; юридический
  документ, написанный агентом; правка утверждённого текста без снятия статуса; обход сверки `claims_allow` без
  причины или решением агента.
- **Порядок:** каркас по плану (`copydeck.py skeleton`) → тексты секций → мета, OG, FAQ → строки ассетов → проверки
  (`copydeck.py check`) → выбор (открытый; вслепую — по желанию) → утверждение.

### `facts` — `…/facts.yaml`

Схема — `kb/text/02-strategy-messaging/facts.schema.yaml`; анкета сбора — `proof-intake.md` базы text.

- **Закрыто:** `status: confirmed` — словом заказчика. Нужны `facts_version`, `date`, `site`, `lang`, `facts`; у факта —
  `id`, `kind`, `claim_class`, `verbatim`, `canonical`, `source` (`type`, `who`, `date`), `verification`, `permission`,
  `lang`. Отзыв — с атрибуцией, оригиналом и разрешением; превосходная степень, сравнение, прогноз — с основанием
  `basis`; срок акции и дефицит — с `valid.until`; здоровье и деньги — с юридической проверкой. Пробел — `missing[]`
  (`id`, `what`, `placeholder`, `who`, `blocking`, `fallback`); непроверенное — `never_claim`.
- **Ссылки:** `site` — slug проекта; `jurisdiction` — основная юрисдикция брифа; второй язык — `…/facts.<lang>.yaml` с
  теми же id; документ-источник — строка `docs/business/material.md`, если материал заведён, иначе — путь файла или
  «сообщение заказчика» с датой.
- **Anti-patterns:** модель как источник; факт из головы; поля фактов в брифе, плане или copy deck; отзыв без
  разрешения; «№ 1» без основания.
- **Порядок:** анкета → виды фактов, которые требует бриф → пробелы с запасным поведением → `never_claim` →
  подтверждение заказчика.

### `voice` — `…/voice.yaml`, `…/voice.product.yaml`

Схема — `kb/text/05-voice-editorial/voice.schema.yaml`, у голоса бренда и голоса продукта одна.

- **Закрыто:** `status: approved` — заказчик подтвердил, образцы прошли `claims_check.py` и `copy_lint.py`. Нужны
  `voice_version`, `date`, `status`, `voice_id`, `brand`, `scope` (`genres`, `surfaces`), `derived_from`, `summary`,
  `principles`, `pairs`, `axes`, `address`, `vocabulary`, `punctuation`, `humor`, `samples`, `projections`, `languages`.
- **Ссылки:** `scope.surfaces` — каналы схемы (`marketing-site`, `product-ui`, `legal` …) с голосом `brand`, `product`
  или `neutral-legal`; профиль бренда ссылается на голос продукта `scope.product_voice_ref`; проза ДС и бриф холста
  берут проекцию `projections.tone_of_voice`.
- **Anti-patterns:** свой текст голоса в прозе ДС или во входе холста вместо проекции; нет голоса продукта у проекта с
  кабинетом, приложением или ботом; прилагательные без пар «мы — мы не» и образцов.
- **Порядок:** источники → сводка и принципы → пары и оси → обращение, словарь, пунктуация, юмор → образцы → `scope` →
  проекции.

### `voc` — `…/voc.yaml` (по желанию)

Схема — `kb/text/02-strategy-messaging/voc.schema.yaml`.

- **Закрыто:** статуса нет. Нужны `voc_version`, `date`, `site`, `lang`, `sources`, `snippets`; у цитаты — источник
  (интервью, отзыв) и дословный текст.
- **Ссылки:** `facts_ref`; сегменты — аудитория смысла; транскрипты `/jtbd-interview` — источник.
- **Anti-patterns:** пересказ вместо цитаты; цитата без источника; придуманная цитата.
- **Порядок:** источники → цитаты → темы → разбор.

## Слой дизайна

### `brand` — `…/design/brand.yaml`

Форма — `docs/projects/_template/design/_template/brand.yaml`.

- **Закрыто:** `status: verified` и `approval` — заказчик подтвердил факты бренда; `none` — бренда нет, поля пустые.
  Поля: `name`, `guidelines_ref`, логотип только в SVG (`logo.files`, `never`), цвета ролями (`colors.roles`, `avoid` с
  причиной), шрифты (`fonts.families`: роль, семейство, `cyrillic`, `license`, замена `replaces` с причиной),
  `voice_ref: ../voice.yaml`, `sources`.
- **Ссылки:** его читают бриф сайта и бриф на вид (`brand.ref`), ДС и вход холста; файлы — `…/design/_assets/brand/` и
  `…/design/_assets/fonts/`.
- **Anti-patterns:** цвет без роли; шрифт без проверенной кириллицы или веб-лицензии; бренд со слов модели; извлечение
  внешним сервисом как окончательный источник; выражение бренда в этом файле — оно в брифе сайта.
- **Порядок:** источники → логотип → цвета ролями → шрифты → запреты → подтверждение.

### ДС — `…/design/system.tokens.json`, `…/design/DESIGN.md`, `system.yaml`

Канон — `docs/projects/_template/design/README.md § ДС`; форма карты решений —
`docs/projects/_template/design/_template/system.yaml`.

- **Закрыто:** `status: approved` и `approval` в карте решений — «Keep» заказчика до экранов; статус карты — статус всей
  ДС; `ds_build check <slug>` без ошибок — формат DTCG и производные равны сборке.
- **Токены DTCG:** примитивы и семантика по схеме ui 09/04; режимы тем, плотности, сокращённого движения;
  `breakpoint.*` рядом с `size.panel.*`; одна шкала `space.*`; у сайта — расширение страниц; правила применения — в
  `$extensions`. Пути токенов — они же имена CSS-переменных: код их читает, они не переименовываются.
- **Проза:** разделы — ui 12/04 §2.3; роли цвета с частотой и контрастом, правила с именами токенов, иконография,
  доступность, известные проблемы (слабые пары контраста), источник; голос — проекцией профиля; передняя часть с
  токенами — производная (`ds_build build`; в ней `x-narrow` — основной кегль узкой ширины).
- **Карта решений:** `components` — ключ на каждый тип экранов (у сайта — типы слотов действия и форм), один компонент
  на тип; `extensions` — с `keyboard` и `text_roles`; `text_styles` — роли ux 07/06 §7.2 и `body`; `conventions` — знак
  диапазона, пробел в разрядах, пустое состояние, иконки, цвета статусов, маркеры объектов; `starter` — после первой
  приёмки кабинета. Покрытие типов — `ds_coverage check <slug> [<surface>]`.
- **Anti-patterns:** литерал вне токенов; правка артефакта ДС без подъёма в токены; два компонента на один тип; тип «по
  месту» вместо словаря или расширения; обязательные состояния, скопированные из словаря; производные, правленые руками.
- **Порядок:** токены (база → ручки или палитра → режимы → брейкпоинты) → контраст → проза → карта решений → артефакт →
  публикация.

### `app-brief` — `…/design/app-brief.yaml`

Форма — `docs/projects/_template/design/_template/app-brief.yaml`.

- **Закрыто:** `project.status: approved` и `project.approval` — владелец продукта; вопросы приоритета 1 закрыты; ядро
  `core` заполнено, его проекции равны источникам; `choice` — после карточек стиля; раздел `surfaces.<surface>` — на
  втором входе дизайна кабинета.
- **Ссылки:** `brand.ref: brand.yaml`; проекции — vision `Name` и `Devices and accessibility`, таблица «Постура»
  `user.md`, `surface.md`, `object.md`, паспорта `ai` возможностей, `constraint.md`; `intake.raw_ref`.
- **Anti-patterns:** бриф на поверхность вместо одного на продукт; проекция, правленая в брифе, а не в источнике;
  плотность без причины; характер прилагательными без выбора карточки; уровень амбиций у рабочих экранов.
- **Порядок:** общие поля → проекции ядра → плотность и темы → характер и запреты → карточки стиля → выбор →
  `surfaces.<surface>`.

### `visual-dna` — `…/design/<surface>/visual-dna.json` (сайт), `…/design/visual-dna.json` (продукт)

Схема — `kb/ai-media/06-art-direction-consistency/visual-dna.schema.json`. Заводится, когда его читает генерация
(сайт) или иллюстрации и генерация (продукт); иначе — «не применимо: причина» в заметке этапа.

- **Закрыто:** `status: approved` и `approved_by` — человек; `vlm_to_dna.py validate ФАЙЛ --art-direction <арт-дирекция>`
  без ошибок; предупреждение «скрим: …» — расхождение значений арт-дирекции и паспорта, их приводят к одному. Нужны `dna_version`,
  `id`, `checked_at`, `status`, `character`, `palette`, `grade`, `light`, `camera`, `composition`, `subject_matter`,
  `style_blocks`, `exclusions`, `acceptance`; у продуктового паспорта — раздел `illustration`: места `places`, формат
  `format`, перекраска `recolor`, список метафор `metaphors`; у 3D-иконок — паспорт серии `icon3d.series_passport`.
- **Ссылки:** сайт — из паспорта в `handoff` арт-дирекции (путь к ней — `provenance.art_direction`), после ДС —
  `derived_from_ui.tokens: ../system.tokens.json`; продукт — из токенов (`vlm_to_dna.py from-tokens`), разбор эталонов —
  пакетом сессии Opus (`vlm_to_dna.py build` → агент `design-judge` → `vlm_to_dna.py parse`); метафоры пустых состояний
  экранов — id списка `illustration.metaphors`.
- **Anti-patterns:** один средний паспорт на два мира; палитра со слов модели, а не замером; утверждённый паспорт,
  правленый молча; статус `retired` в проекте.
- **Порядок:** характер → палитра и цветокоррекция → свет и камера → композиция и сюжеты → блоки стиля → запреты →
  приёмка.

### `art-direction` — `…/design/<surface>/art-direction.json`

Схема — `kb/creative/09-ai-execution-evaluation/art-direction.v1.schema.json`; документ — creative 01/02.

- **Закрыто:** `status: approved` с `approved_by`, `approved_at`, `choice`, `visual_language`, `motion_system`,
  `handoff`. Нужны `art_direction_version`, `id`, `site`, `status`, `checked_at`, `inputs`, `ambition`, `concept`,
  `territories`, `directions`, `lifecycle`; у `proposed` — одна рекомендация среди направлений; решения `use` и `twist`
  не проваливают ни одной из пяти проверок.
- **Ссылки:** `ambition` — проекция брифа; бюджет — профиль бюджета плана; у референса — одно место (`applies_to`);
  `k3_allow` и `lifted_markers` — с решением (`decision_ref`, вид решения — `use` или `twist`; необязательные `page` и
  `section` сужают снятую примету до страницы или секции); `decisions[].k3_allow` — строка: один ключ `--allow` на
  решение, список ключей — `exclusions.k3_allow`.
- **Запреты направлений до выбора:** поле `bans` направления (`directions[].bans`), с ним — заметка `notes`: на
  странице «Направления» каждый список идёт своему артборду; после выбора запреты живут в `exclusions`.
- **Anti-patterns:** направление без риска и цены; приметы сняты без решения; мудборд больше предела схемы; статус
  `superseded`, история старше текущей версии; арт-дирекция у кабинета.
- **Порядок:** `inputs` и `ambition` → концепция и территории → направления → выбор → мудборд → визуальный язык →
  движение и эффекты → решения и исключения → бюджет → `handoff`.

### `asset-plan` — `…/design/<surface>/assets/plans/<page-id>.yaml`

Схема — `kb/ai-media/05-prompting/asset-plan.schema.json` (формат — ai-media 01/01 §8); каркас —
`plan_to_assets.py build <slug> <surface> --write`: слот `edit-real` при подлинности `real-only` он пишет строкой `real`
с заметкой — кадр доводится без генерации.

- **Закрыто:** `status: approved` и `approval` — заказчик, до генерации;
  `plan_to_assets.py check <slug> <surface> [--page ID …]` без ошибок.
- **Поля:** `plan_version`, `checked`, `status`, `approval`, `page` (`page_type` — id словаря site, `media_class` —
  проекция), `brand`, `budgets`, `policy`, `slots[]`: `id` (`<секция>-<id>` плана), `section`, `slot`, `role`, `goal`,
  `key` — ключевой ассет, `ladder`, `source` (`generate` · `edit-real` · `real` · `code` · `template` · `render`),
  `task_codes` или `recipe:`, `three_d.road` — дорога 3D, `variants` (соотношение, размер, форматы, вес, фокус),
  `delivery`, `alt_ref` и `caption_ref` — текстовые слоты плана страницы, `acceptance`, `ai_fit`. Расширение слота
  `x-demo` — демо-картинка макета вне git: `x-demo.file` — путь или `x-demo.files` — `{<вариант>: <путь>}`,
  `x-demo.what` — что это за картинка; вход холста ставит её строкой с пометкой «демо».
- **Ссылки:** `refs.asset_plan` плана ведёт сюда; готовые файлы — строки `…/design/<surface>/assets/manifest.yaml`;
  загрузки холста — `ARTIFACTS.md`.
- **Anti-patterns:** генерация до утверждения; `generate` у людей-доказательств, товара «как есть» и чужих знаков;
  3D-слот без постера; ассет вне бюджета типа.
- **Порядок:** каркас → решение по слоту (лестница, источник, задача) → варианты и вес → тексты ассетов → ключевые →
  утверждение.

### `motion-spec` — `…/design/<surface>/motion/<page-id>.motion-spec.yaml`

Схема — `kb/creative/09-ai-execution-evaluation/motion-spec.schema.json`.

- **Закрыто:** `status: approved`. Нужны `motion_spec_version`, `id`, `status`, `checked_at`, `refs`, `level`, `page`,
  `sections`; у петли — пауза; у движения по прокрутке — диапазон; у одноразового — длительность; у движения за
  указателем — поведение на телефоне; у момента кандидата LCP — только свойства `transform` и `translate`.
- **Ссылки:** секции — id плана; уровень — из брифа через `ambition-levels.yaml#levels.maps_to`; подача ссылается
  `motion_spec_ref`.
- **Anti-patterns:** спецификация до принятого статичного макета; моменты без привязки к раскладке; нет сокращённого
  движения или поведения на телефоне.
- **Порядок:** страница (тезис, характер, примитивы, LCP) → секции пиков и акцентов → моменты → станции и раскадровка →
  сокращённое движение и телефон → `fallback`.

### `treatment` — подача в плане страницы

Схема — `kb/creative/09-ai-execution-evaluation/treatment.schema.json` через `page-plan`.

- **Закрыто:** `status: approved` с `level`, `visual_role`, `motion_level`; у пика и акцента с `proposed` —
  `motion_spec_ref`. Условия схемы: на L0 движение не выше `subtle`, без пика и тяжёлых фонов; эффекты или выразительное
  движение — нужен `reduce`; эффекты, L2 или видео-фон — нужен `mobile`; петли — `loop_control`; текст поверх медиа —
  контраст фона; видео — проверка вспышек.
- **Ссылки:** `page.treatment.tokens_ref`, `refs.treatment`; `display_role` — роли `marketing-tokens.json`.
- **Anti-patterns:** подача выше уровня брифа; секция конверсии выше L0; значения подачи до выбора направления.
- **Порядок:** уровень → визуальная роль → уровень движения → эффекты → фон и композиция → `display_role` → сокращённое
  движение и телефон.

## Холст

### вход холста — `…/design/<surface>/input/`

Раскладка — `claude-design.md § Вход холста`.

- **Закрыто:** своего статуса нет — вход производный; проверка входа `canvas_input check` без `error` — гейт 2 у
  единиц партии и целостность входа, предупреждения — доклад заказчику. Манифест называет этап, партию (`units`),
  источники с путём, статусом и отпечатком, что заполнил агент («Going with»), пробелы со строкой «вне партии» и итог
  проверки; вход собран `canvas_input build` или, когда окружения нет, помечен «собран без утилиты».
- **Состав:** бриф холста, факты с разделом «Нельзя утверждать», референсы исполнителю, критерии приёмки; у сайта — на
  страницу структура, тексты, ассеты, блок движения; у кабинета — контракт генерации, тексты, демо-набор, ассеты.
- **Anti-patterns:** копии токенов, прозы ДС, арт-дирекции или плана во входе; вход, правленый руками; тексты не того
  статуса; факт без источника.
- **Порядок:** манифест → бриф холста → факты → тексты → структура → ассеты → критерии.

### макет — страница холста «Макет и прототип»

- **Закрыто:** «Keep» по странице или экрану — он принимает и структуру, и облик; вердикт и одобрение — на приёмке.
- **Что должно быть:** артборды ширин `kb/common/acceptance-widths.yaml#artboards` — все адаптивы в холсте, тёмная
  тема — твиком, если она есть в ДС; секции по плану, экраны по карте; литералы токенов ДС; утверждённые тексты
  дословно из входа; картинки из загрузок входа, у пустого слота — заглушка; прототип пути главного действия; у
  кабинета — артборды состояний, у коллекций — состояния данных.
- **Anti-patterns:** секции не по плану или экраны не по карте; литерал вне токенов; текст не из входа; «рыба»;
  картинка не из загрузок; твик, который не рычаг ДС; приметы «дефолтного вида» из бан-листа задания;
  «сверх задания».

### раунд правок

- **Закрыто:** пункты пакета — `fixed` или с решением заказчика; при просьбе о проверке — сравнение кадров по пунктам
  пакета без неожиданностей; паспорт итерации записан.
- **Что должно быть:** правки заказчика подняты в источники; пакет с «Keep» и «ничего сверх»; эхо до правки; итог по
  пунктам; счёт раундов в заметке холста.
- **Anti-patterns:** правка вне пакета; потерянная правка заказчика; публикация с `force` без прямой просьбы; раунд
  сверх бюджета без решения заказчика.

### `REVIEW.md` — `…/design/<surface>/review/REVIEW.md`

Форма — `docs/projects/_template/design/_template/REVIEW.md`.

- **Закрыто:** у страницы или экрана вердикт `accepted` или `accepted_with_notes` и одобрение заказчика с отпечатком
  артбордов и источников единицы, совпадающим с текущим (`ready show <slug> <surface>`).
- **Поля:** передняя часть — `stage`, `model`, `artifacts`, `synced` (с `lifted`), `checks`, `items`, `decision`,
  `reason`, `hashes` (паспорт итерации, не одобрение); таблица «Приёмка»; таблица «Пункты ACCEPTANCE» с колонкой
  «страница или экран».
- **Anti-patterns:** вердикт руками; журнал итераций; кадры PNG в git; одобрение без отпечатка; S без записи.
- **Порядок:** паспорт итерации → пункты → вердикт → одобрение.

### `ARTIFACTS.md` — `…/design/ARTIFACTS.md`

Форма — `docs/projects/_template/design/_template/ARTIFACTS.md`.

- **Закрыто:** статуса нет. У каждого артефакта — адрес, релиз типа и версия контракта, последнее чтение, чей аккаунт;
  загрузки связаны с файлами ассетов; «Условия холста» — по поверхностям; строки просьбы о проверке и «Ссылки» — только
  словом заказчика.
- **Anti-patterns:** правила формата типов в файле; журнал публикаций; результаты проверок артефакта без строки
  просьбы; просьба или «Ссылки» по умолчанию.
- **Порядок:** артефакты → загрузки → условия холста → просьба → ссылки.

## Пакет

### `ready.yaml` — `…/design/<surface>/ready.yaml`

Форма — `docs/projects/_template/design/_template/ready.yaml`.

- **Закрыто:** своего статуса нет — манифест производный: собирает `ready build <slug> <surface>`, свежесть —
  `ready check` (R-FRESH-006); его `status` (`ready`, `partial`, `not-ready`) выводится из единиц, а единица
  `ready: true` — только по правилу готовности формы; неутверждённая ДС, неполное покрытие ДС, FSD-карта не `stable`
  и открытый источник контекста — строки `open` «решение заказчика: …», готовность они не держат; `publishable` —
  готовность без заглушек, демо-фактов и демо-кадров.
- **Поля:** `skill_version`, `surface`, `type`, `web_kind`, `consumer`, `status`, `sources` (путь, статус, `sha256`),
  `units` (`id`, `ready`, `publishable`, `composition`, `texts`, `mockup`, `budget_profile`, `gate_exceptions`,
  `after_build` — пункты `{id, severity, check}`, `open`), `perf`, `frontend_design`, `blockers`.
- **Anti-patterns:** манифест, правленый руками; `ready: true` при несовпавшем отпечатке; `mockup: skipped` без решения
  заказчика в заметке пропусков; отпечатки, отставшие от файлов.
- **Порядок:** источники → единицы → `perf` → `frontend_design` → `blockers` → статус.
