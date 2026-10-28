# Спецификация подачи: `treatment` секций, варианты блоков, `art-direction` v1, пакет исполнителя

Волна 3 · агент I · 2026-09-24/25 · источников 34 (файлы базы, сестёр и соседей, 3 клона скиллов, 9 дайджестов роликов) · опытов 2
(`99-raw/experiments/I/01-schemas`, `02-spec-sufficiency`) · Chromium 1243 и WebKit 2359 (Playwright 1.63) · jsonschema 4.26 ·
артефакты: `treatment.schema.json` v1, `block-treatments.yaml` 1.0, `examples/` (3 страницы), проверка `spec_check.py`.

## Выжимка для агента

1. **Подача передаётся исполнителю тремя слоями**: `art-direction` (почему и что главное) → `treatment` секции в `page-plan` (роль в ритме,
   уровень, эффекты, фон, композиция, reduce, телефон) → `motion-spec` (таймлайн). Прилагательное без поля — не передача. → §1 `[практика]`
2. **Каждой секции плана — `level`, `visual_role`, `motion_level`**; секции конверсии — L0 и `calm`; служебные — `chrome`. → §2.2 `[практика]` (A, site)
3. **Уровень эффекта — из `effects.yaml` (`level_min`)**, а не из вкуса: на L0 запрещены 40 из 56 эффектов, на L1 — 9 (`effects.yaml` v0.3: `page-transition` — L1, X-21; у F2 — 10, у F было 37 из 49). → §2.3 `[документация: F]`
4. **Пиков 0 / ≤ 2 / 2–4, акцентов ≤ 1 / ≤ 3 / ≤ 4, секций с фирменным приёмом ≤ 1 / ≤ 2 / ≤ 4** (L0 / L1 / L2); два пика подряд — нет. → §2.4 `[не проверено: E, A]`
5. **Пик обязан нести `purpose: signature`**, иначе это не пик, а шум; у пика и акцента в статусе proposed — `motion_spec_ref`. → §2.3 `[практика]`
6. **Цели — id v1 плана**: `секция.слот`, `секция.группа`, `секция.группа-N.элемент`; декоративное — `секция.fx-<имя>`; старые id E site
   (`kak-rabotaem`, `funktsii`) — ошибка. → §2.5 `[проверено]`
7. **`text-over` → `background.text_contrast`**, видео и прелоадер → `flash_check`, `cinematic` → ролик, секвенция или 3D (схема v1 ловит). → §2.3 `[стандарт: WCAG 2.3.1]` `[проверено]`
8. **Reduce пиши стратегией**: `final-state`, `crossfade`, `static-poster`, `stations` (скраб → 2–6 кадров), `no-motion-needed`. → §2.2 `[консенсус: E]`
9. **Телефон — объявленная деградация**: `mobile.strategy` + `note`, что именно меняется (`stacked`, `separate-asset` — нативный кадр, не центр-кроп). → §2.2 `[мнение вендора: higgsfield, scroll-world]`
10. **Петля ≥ 1 → `loop_control`**; `page-toggle` — только при `reduce_toggle: true` страницы. → §2.3 `[стандарт: WCAG 2.2.2]`
11. **Визуальный вариант блока — из `block-treatments.yaml`** (84 блока site): `visual_variant` + `structural` должен совпасть с `variant` плана. → §3 `[проверено]`
12. **Семейство блока задаёт потолок**: конверсия, FAQ, контакты, курс — L0; proof, offer, about, event, footer — ≤ L1; hero, value, портфолио — до L2. → §3.2 `[не проверено]`
13. **Не бери эффект вне списка блока** без решения art-direction: предупреждение TR-12 — сигнал «приём не из жанра блока». → §3.3 `[практика]`
14. **treatment v1 совместима с v0**: 69 известных документов проходят; page-plan site ссылается на `:1`, `site_validate.py` грузит схему v1. → §2.6 `[проверено]`
15. **В примерах базы treatment — overlay по id секций**, склейка с планом site и проверка — `spec_check.py plan`. → §2.7 `[проверено]`
16. **art-direction v1 = v0 + эмоциональная цель, money idea, мотив из бренда, характер и примитивы движения, статус прототипа главного эффекта,
    журнал вариативности, блок «чего не ставить»**; гарнитуры — из `cyrillic-display-fonts.yaml` (Oswald — нет, Nunito — средне). → §5 `[практика: W2, W3, H, D]`
17. **Прототип главного эффекта — до утверждения**: поле статуса `prototype`, запись лабораторной страницы — вход видео-референса. → §5 `[практика: V 7nEvk6nFeS4, Ulgy6xIrdPg]`
18. **Пакет исполнителя получает не слова, а файлы**: `DESIGN.md` (токены, в том числе `motion.marketing`), `MOTION.md` из motion-spec, `refs/README.md` с Take / Do not take,
    блок «чего не ставить» из реестра клише, `ACCEPTANCE` E-блок из acceptance. → §6 `[практика: kimi 07/02]`
19. **Разметка исполнителя несёт id**: `data-section`, `data-slot`, `data-group`, `data-fx`, `data-moment`, `data-effect` — иначе проверка гадает селекторы. → §6.3 `[практика: K]`
20. **Не копируй треатмент плана site как есть**: в примерах site hero «Окошка» с появлением, а art-direction A — без; источник подачи — art-direction. → §4 `[проверено]`

## 1. Контур передачи подачи

| Слой | Формат | Кто пишет | Что несёт | Кто читает и проверяет |
|---|---|---|---|---|
| концепция и решения | `art-direction` v1 (`01-creative-direction/art-direction.schema.json` v0 A + дельта §5) | Claude-арт-директор | тезис, главный приём, направление, палитра, гарнитуры, система движения словами, решения о клише | ai-media (паспорт визуала), 3d, `spec_check.py` (ссылки) |
| подача секций | `treatment` v1 в `page-plan` (этот файл §2) | Claude по art-direction и `block-treatments.yaml` | уровень, роль в ритме, эффекты с целями, фон, композиция, display-роль, reduce, телефон, петли, бюджет | site (`site_validate.py` PL-C01), `spec_check.py plan`, K |
| движение | `motion-spec` v1 (`02-motion-spec-storyboard-handoff.md`) | Claude | таймлайн моментов, станции, раскадровка, видео-референсы, acceptance | `spec_check.py spec`, K (`motion_check.py`) |
| пакет исполнителя | `DESIGN.md`, `MOTION.md`, `TASK.md`, `ACCEPTANCE.md`, `refs/` (kimi 07/02) | сборщик kimi + проекции `spec_check.py` | то же, в каналах, которые исполнитель читает | K3 или Claude-исполнитель; `k3_checks.py`, K |

- Treatment — **место в ритме и допустимое**, motion-spec — **время и прокрутка**; одно не заменяет другое: в опыте I/02 treatment «Отвеса» был
  верен, а сцена разошлась с замыслом на 98 px из-за неполной motion-spec (`02` §3) `[проверено]`.
- Порядок работы: art-direction (выбор направления) → treatment всех секций (§4) → motion-spec пиков и акцентов → проверка `spec_check.py`
  → проекции в пакет → сборка → запись и зонд станций (K) → правка чисел в спецификации, не в коде (W3: «designing in dev») `[практика]`.

## 2. `treatment` v1

### 2.1. Где живёт и что нового

Схема — `09-ai-execution-evaluation/treatment.schema.json`, `$id urn:app-design:creative:treatment:1`; корень — секция,
`$defs/page` — страница. В `page-plan` v1 site: `sections[].treatment` и `page.treatment` `[документация: site S1v1]`.

| Поле v1 | Против v0 | Зачем | Источник |
|---|---|---|---|
| `display_role` + `display-poster`, `display-quote` | было 5 значений | роли D (poster ≤ 12 зн., quote ≤ 120 зн.) | D `04/01` §2 |
| `reduce.strategy` + `stations`, `reduce.stations` | не было | скраб → 2–6 кадров-станций | E `05/01` §4.2 |
| `mobile.strategy` + `stacked` | не было | закреплённая сцена → стопка станций | E `05/02` §4.4 |
| `loop_control` + `page-toggle` | не было | единая пауза = переключатель страницы | E `05/01` §4.4 |
| `effects[].class`, `impl`, `params`, `moments` | не было | класс движения, слой реализации (G), параметры в пределах `limits` F, связь с моментами | E §1.3; G `07/02` §6; F |
| `effects[].trigger` + `pointer` | не было | курсорные эффекты отдельно от hover | F |
| `target` — шаблон id v1 и `fx-` | свободная строка | цели разрешаются по плану; декоративное — явно | site C2 |
| `flash_check {method, result, checked_at}` | не было | WCAG 2.3.1 для видео, секвенций, прелоадера | E `05/01` §3.4 |
| `lcp_note`, `storyboard_ref` | не было | элемент LCP и способ появления; раскадровка вне спецификации | E `05/02` §10 |
| `background.kind` + `sequence` | не было | видео-скраб и секвенция как фон сцены | F |
| `viewer {effect, target, note}` | не было | наложение-просмотр секции: окно кадра или работы поверх страницы (`effect:overlay-viewer`) | `06-effects-catalog` |
| page: `motion_spec_ref`, `accents`, `signature_sections`, `motion_system.primitives`, `.character`, `library` + `stack:<id>` | не было | сверка счёта, система появления E, характер (Val Head), стек G | E, W1, G |

### 2.2. Обязательное и умолчания

| Секция | Минимум | Добавить, если |
|---|---|---|
| любая | `level`, `visual_role`, `motion_level` (утверждённая — обязательно) | — |
| с эффектами | `effects[{ref, target, trigger, purpose, class}]`, `reduce`, `mobile` | петля → `loops` + `loop_control`; видео/прелоадер → `flash_check` |
| `peak` | эффект `purpose: signature`, `motion_spec_ref`, `composition.height` (часто `scene`) | фон-сцена → `background.kind`, `budget` |
| `accent` | один приём малой силы или визуальный акцент композицией | proposed/approved → `motion_spec_ref` |
| `text-over` | `background.text_contrast` | видео под текстом → F83 по кадрам (ai-media 10/03 §1) |
| конверсия (`lead-form`, `pricing`, блоки калькулятора, квиза, тарифов) | `level: L0`, `visual_role: calm`, эффектов нет | — |

`motion_level` проецируется из уровня (E П11, A `maps_to.kimi`): страница L0 → `subtle` (секции `none|subtle`), L1 → `expressive`,
L2 → `cinematic` только с роликом, секвенцией или рендером, иначе `expressive` `[практика]`.

### 2.3. Условия, которые проверяет схема

| Условие | Что требует | Доказательность |
|---|---|---|
| `level: L0` | `motion_level` none/subtle; не `peak`; `loops ≤ 1`; фон не shader/webgl-3d/video-loop/sequence; нет 40 эффектов с `level_min` L1–L2 (`effects.yaml` v0.3; у F — 37) | `[документация: F level_min]` |
| `level: L1` | `motion_level ≤ expressive`; `loops ≤ 2`; нет 9 эффектов `level_min` L2 (v0.3; списки — `treatment.schema.json` `x-effect-levels`) | `[документация: F]` |
| `level: L2` | `loops ≤ 3` | `[не проверено: E §5.2]` |
| `motion_level: cinematic` | фон video-loop/webgl-3d/sequence или эффект video-scrub, image-sequence, 3d-*, video-loop-hero, alpha-video-object | `[практика: kimi 07/01 §6.2]` |
| есть эффекты или движение ≥ expressive | `reduce` | `[стандарт: WCAG 2.3.3 через reduce]` |
| эффекты, L2 или тяжёлый фон | `mobile` | `[практика: CRV-AL-06]` |
| `loops ≥ 1` | `loop_control` | `[стандарт: 2.2.2]` |
| `visual_role: peak` | эффект с `purpose: signature` | `[практика]` |
| peak/accent + proposed/approved | `motion_spec_ref` | `[практика]` |
| `text_media: text-over` | `background.text_contrast` | `[практика: CRV-AL-08]` |
| видео, секвенция, прелоадер | `flash_check` | `[стандарт: 2.3.1]` |
| `visual_role: chrome` | `motion_level` none/subtle, `loops 0` | `[практика]` |

Самопроверка `spec_check.py --selftest` подбрасывает пять нарушений (L0 + pin, пик без signature, text-over без контраста, видео без
`flash_check`, cinematic без ролика) — схема ловит все `[проверено]`.

### 2.4. Что проверяет скрипт, а не схема

| Код | Правило | Число |
|---|---|---|
| TR-01 | уровень секции ≤ уровня страницы | — |
| TR-02, TR-03 | секция конверсии — L0 и без `signature` | `section_caps` A |
| TR-04 | пиков по уровню | 0 / 0–2 / 2–4 |
| TR-05 | акцентов по уровню; на L0 акцент — только hero | ≤ 1 / ≤ 3 / ≤ 4 |
| TR-06 | секций с `signature` | ≤ 1 / ≤ 2 / ≤ 4 |
| TR-07, TR-08 | `page.peaks`, `accents`, `signature_sections` — необязательная сводка, выводится из секций; записанный список, разошедшийся с секциями, — предупреждение | — |
| TR-09 | цель эффекта найдена в плане (слот, группа, anatomy, `fx-`) | — |
| TR-10, TR-11 | эффект есть в каталоге; `level_min` ≤ уровня секции | — |
| TR-12 | эффект в списке блока (`block-treatments.yaml`) — предупреждение | — |
| TR-13 | `visual_variant` есть у блока; `structural` и `levels` совпадают — предупреждение | — |
| TR-14 | один референс — одна секция | — |
| TR-16 | `page-toggle` без `reduce_toggle` | — |
| TR-19, TR-20 | два пика подряд (L0–L1 — ошибка, L2 — предупреждение); на L2 между пиками calm или pause | — |
| TR-21 | петель по уровню | 1 / 2 / 3 |
| TR-23, TR-24 | уровень ≤ `level_max` блока; роль из ролей блока | — |
| TR-25 | плавная прокрутка — только L2 | — |
| TR-27, TR-28 | `params` в пределах `limits` эффекта; `background.token` есть в `marketing-tokens.json` | — |

Счёт — примирение A и E: у A (L1) «≤ 2 секции с фирменным приёмом (peak или accent)», у E — пики ≤ 2 и акценты ≤ 3; схема считает
**три величины** отдельно: пики (`visual_role`), акценты (`visual_role`), секции с `signature` (A «фирменный приём»). «Окошко»: 1 пик +
2 акцента + 1 секция с signature — проходит обе нормы `[проверено]`. Числа акцентов — `[не проверено]` E, калибрует K.

### 2.5. Цели: id v1 и разметка

- `target` = `section` | `<секция>` | `<секция>.<слот>` | `<секция>.<группа>` | `<секция>.<группа-N>.<элемент>` | `<секция>.fx-<имя>`;
  группа без номера (`how-it-works.step`) — все экземпляры; `fx-` — декоративный элемент подачи, которого нет в плане (линия, маркер, пометка).
- Id секций — из роли или блока (site v1: `hero`, `how-it-works`, `final-cta`); треатменты примеров site ссылаются на старые id E
  (`kak-rabotaem.step`, `funktsii.row`) — `spec_check.py` отвечает TR-09 (C2 site) `[проверено]`.
- Разметка исполнителя повторяет id атрибутами (контракт K, `motion-spec.schema.json` `x-dom-contract`): `data-section`, `data-slot`,
  `data-group`, `data-fx`, `data-moment`, `data-effect`; `motion_check.py` ищет `[data-moment]` → `[data-section] [data-slot|data-group|data-fx]`
  → `#секция [data-slot]` → `selector_hint` `[практика: K]`.

### 2.6. Совместимость и подключение у site

- 69 treatment v0 (27 в примерах site v1, 42 в опыте A/02) валидны по v1; первая версия v1 давала 2 регрессии (обязательный
  `mobile.note`) — перенесено в предупреждение TR-17 `[проверено: I/01 compat_check.py]`.
- `site_validate.py` грузит treatment v1 (`P['treatment']` — `creative/09-ai-execution-evaluation/treatment.schema.json`), `page-plan` v1 ссылается
  на `urn:…:treatment:1` — план с полями v1 проходит site.
- `spec_check.py plan` валидирует план схемой page-plan v1 с подсхемой `treatment` v1 `[проверено]`.

### 2.7. Пример: «Отвес», главная (L1)

`examples/otves-home.treatment.yaml` (overlay по id секций плана site `lead-services-otves/plans/home.yaml`):

```yaml
# treatment v1 · 2026-09-24 · [проверено: 99-raw/experiments/I/01-schemas — plan 0 ошибок, 0 предупреждений]
how-it-works:
  level: L1
  visual_role: peak
  motion_level: expressive
  visual_variant: vertical-progress-line          # block-treatments.yaml → steps
  effects:
    - {ref: "effect:scroll-driven-progress", target: how-it-works.fx-plumb-line, trigger: scroll, purpose: signature,
       class: scroll-linked, impl: css-sda, moments: [plumb-line-drop, plumb-bob-follow, step-marker-fill]}
  composition: {align: left, asymmetry: mild, text_media: text-only, density: airy, height: content}
  display_role: display-m
  reduce: {strategy: final-state, note: "линия целиком, грузик внизу, маркеры залиты"}
  mobile: {strategy: simplified, note: "линия 2 px у левого края, без грузика; маркеры на линии"}
  budget: {js_kb_br: 0, load: eager}
  motion_spec_ref: otves-home.motion-spec.yaml#/sections/how-it-works
```

Антипример (treatment v0 в плане site): `target: kak-rabotaem.step` — старый id; `reduce` без стратегии станций для скраба; нет
`motion_spec_ref` — исполнитель получает «линия-отвес с грузиком» словами и додумывает диапазон (`02` §3).

## 3. `block-treatments.yaml`

### 3.1. Формат

Файл — `09-ai-execution-evaluation/block-treatments.yaml` 1.0: 16 семейств (`families`, по `family` блоков site) и 84 блока (`blocks`, все id
`blocks.yaml` 1.0). Поля: `level_max`, `roles`, `signature`, `effects {L0, L1, L2}` (накопительно), `visual_variants[{id, structural, composition,
display_role, background, levels, note, level_max, roles, signature}]`, `mobile {strategy, note}`, `a11y[]`, `avoid[cliche:<id>]`. Блок наследует
поля семейства; вариант со своими `level_max`, `roles`, `signature` меняет потолок и роли только для себя (`routes-scene` у `audience-grid` —
секция-маршрут главной многостраничника, потолок L2); `grid-quiet` у `portfolio-grid` — роль `calm`: обложки и подписи стоят, появления,
каскада и эффекта наведения нет.
Проверка: `spec_check.py blocks` (84 ↔ 84 id, эффекты есть и по уровню, клише есть, `structural` — варианты site) и `vocab_lint.py` site
(168 id — 0 ошибок) `[проверено]`.

### 3.2. Потолки по семействам

| Семейство (site) | `level_max` | Роли | Фирменный приём | Характерные эффекты по уровням |
|---|---|---|---|---|
| hero | L2 | accent, peak, pause | да | L0: hero-entrance-once, mask-reveal, mesh-gradient-css, cinemagraph; L1: split-text-reveal, shader-bg, video-loop-hero, 3d-object, scroll-mask-expand; L2: 3d-scene, video-scrub, image-sequence |
| value | L2 | все | да | L0: scroll-driven-progress, sticky-stack; L1: pin-scrub-story, svg-line-draw, parallax-layers, view-transition; L2: horizontal-scroll, 3d-scene |
| portfolio-gallery | L2 | support, calm, accent, peak, pause | да | L1: hover-distort-dom, view-transition, page-transition (нативный VT; решение X-21, S1 2026-09-25); L2: horizontal-scroll, custom-cursor |
| proof, offer, about-team, event, cta, footer, resources-blog | L1 | по семейству | about — да, прочие — нет | counter-up, marquee-logos (proof), scroll-reveal-system, scroll-text-highlight |
| conversion, faq, contacts, course, utility, header-nav | L0 | calm / chrome | нет | только отклик; `motion-toggle` в шапке |

Исключения внутри семейств: `pricing-*`, `comparison-table`, `offer-details`, `benefit-list`, `spec-sheet`, `integrations-grid`, `job-list`,
`article-body` — L0; `hero-form`, `hero-input`, `hero-letter`, `hero-carousel`, `video-showcase`, `interactive-demo`, `feature-grid`,
`feature-bento`, `feature-tabs`, `prose`, `gallery` — ≤ L1; `timeline` — до L2 (горизонталь) `[не проверено]`.

### 3.3. Как выбирать вариант

1. Взять `variant` блока из плана site → варианты с этим `structural`.
2. Отбросить варианты, чьи `levels` не содержат уровень секции.
3. Сверить с главным приёмом art-direction: вариант пика несёт `signature`, вариант спокойной секции — нет.
4. Проверить `avoid` блока против решений art-direction (`decisions[]`): клише без решения — не брать.
5. Записать `visual_variant`, перенести умолчания `composition` и `display_role` в treatment, уточнить.

Новое из C3 site: `service-area` — `districts-columns`, `zone-map-static` (статичная SVG-зона, живая карта по нажатию), `address-check-form`
(форма — L0); `capture-popup.engaged-slide-in` → `engaged-slide-in-corner`: немодальная карточка ≤ 25 % высоты экрана телефона, без затемнения
и захвата фокуса, вход `translateY(16px)→0` + opacity 320 мс, один раз за визит, не на посадочной под платный трафик `[практика: site F]`.

Поправка к `../../site/04-blocks/blocks.yaml` `steps.mobile` («соединительные линии убираются» < 40rem) для сайта с концепцией
линии: линия-прогресс, которая несёт тезис движения («Отвес»), остаётся 2 px у левого края — потому что убранная линия удаляет главный приём
страницы на 60–70 % визитов с телефона `[не проверено]` (предложение site, отчёт I §6).

## 4. Процедура: treatment всех секций за один проход

1. Прочитать `page.ambition_level`, `budget_profile`, секции плана (id, роль, блок, вариант, слоты, `lcp_candidate`).
2. Из art-direction выбранного направления взять главный приём (`signature_move.where`) → секция-пик; тезис движения → `page.motion_system.thesis`;
   `entrance_system` → `primitives` (2–3 из fade-up, type-unmask, sweep, number-tick, line-draw или `none`).
3. Разметить ритм: пики по норме уровня, между пиками calm или pause; hero — accent, не обязательно peak (у 15 из 23 записанных страниц hero
   неподвижен после входа — E `05/02` §1.3); конверсия — L0 calm; служебные — chrome `[данные: C через E]`.
4. Для каждой секции: `visual_variant` по §3.3 → `effects` из списка блока с целями id v1 → `background`, `composition`, `display_role` →
   `reduce` по таблице E `05/01` §4.2 → `mobile` с `note` → петли и `loop_control` → `motion_spec_ref` у пика и акцента.
5. Страница: `peaks`, `accents`, `signature_sections`, `library` (стек G), `reduce_toggle` (L2 — всегда; L1 — при `page-toggle`), `status`.
6. `spec_check.py plan … --overlay … --spec …` → 0 ошибок; предупреждения — решить или записать причину в `notes`.
7. Расхождение плана site и art-direction (hero «Окошка»: в плане появление, в art-direction — нет) решает art-direction; site — сообщить
   (в пример «Окошка» заложено решение art-direction) `[проверено]`.

## 5. `art-direction` v1: дельта к v0 A

Схема v0 — `../01-creative-direction/art-direction.schema.json` (`urn:…:art-direction:0`, 459 строк); v1 — те же поля плюс перечисленные ниже
(аддитивно). Схема v1 собрана скриптом из v0 без правки файла A: `09-ai-execution-evaluation/art-direction.v1.schema.json`
(`urn:…:art-direction:1`); все 5 примеров A (v0) валидны по v1; пример `examples/art-direction-okoshko.v1.json` — новые поля и гарнитуры по
каталогу D, 0 ошибок `[проверено]`. Владелец формата — A: перенос в
`01-creative-direction/` — синтез S или продолжатель A.

| Поле v1 | Тип | Что пишет Claude | Зачем | Источник |
|---|---|---|---|---|
| `concept.emotional_goal` | строка ≤ 160 | как человек должен себя почувствовать на пике страницы | движение и визуал служат чувству, а не приёму | W2 (Dogstudio) `[практика]` |
| `concept.money_idea` | строка | «сайт, где …» — одна фраза, которой проект пересказывают | главный приём проверяется пересказом | `[V:Ulgy6xIrdPg 07:23]` `[практика]` |
| `concept.motif_source` | enum logo, product, material, ritual, place, none + строка | откуда мотив (логотип, продукт, материал) | концепты без мотива разрозненны | `[V:xQnJLYTVl_E 23:30]` `[практика]` |
| `motion_system.character[]` | до 3 прилагательных | energetic, friendly, bold, playful, balanced, measured, calm, subtle, soft, stable, precise, heavy | мост «прилагательные бренда → приёмы» | `[V:OqvQhZ0bTYY 37:11–39:46]` `[практика]` |
| `motion_system.primitives[]` | ≤ 3 | система появления | не одинаковый fade на всём | E `05/02` §2.2 |
| `motion_system.spec_ref` | путь | motion-spec страницы | тезис движения → таймлайн | I |
| `prototype` | `{status: none|planned|built|approved, effect, lab_path, recording, notes}` | прототип главного эффекта до утверждения направления | «сначала R&D, потом обещание» | `[V:7nEvk6nFeS4 05:20]`, `[V:Ulgy6xIrdPg 11:31]` `[практика]` |
| `variation` | `{ledger_ref, entry{paper, display_style, accent_hue, macrostructure, hero_architecture, main_technique, motion_signature, corner_language}}` | запись журнала вариативности | проекты подряд различаются ≥ 4 из 8 осей | H `08/02` §3.2 `[практика: принято из мнения вендора]` |
| `exclusions.executor_block` | путь или текст | блок «чего не ставить» для K3 из реестра клише и `avoid` | запреты — из решений, не из привычки | H `08/01` §6.2 |
| `ambition.scale` | `{approval_chain: short|long, project_scale: small|mid|large}` | масштаб и длина согласования | «вау» реже доживает в длинной цепочке | `[V:ilNOMaR6x_U 23:48]` `[мнение]` — через site-brief |
| `handoff.generated` | `{by, at}` | проекции в visual-dna и brief.yaml собраны скриптом | сейчас `handoff` пишется руками (A) | A отчёт §4 |

```json
/* art-direction v1 · фрагмент · 2026-09-25 · [проверено: валиден по art-direction.v1.schema.json — build_ad_v1.py] */
"concept": {"money_idea": "сайт, где линия-отвес проходит через весь ремонт", "emotional_goal": "спокойствие: за ремонт отвечает один человек",
            "motif_source": {"kind": "product", "note": "отвес — инструмент прораба"}},
"motion_system": {"thesis": "…", "level": "expressive", "character": ["precise", "calm"], "primitives": ["fade-up", "line-draw"],
                  "spec_ref": "../../09-ai-execution-evaluation/examples/otves-home.motion-spec.yaml"},
"prototype": {"status": "built", "effect": "effect:scroll-driven-progress",
              "lab_path": "99-raw/experiments/I/02-spec-sufficiency/page/v11.html", "recording": "99-raw/experiments/I/02-spec-sufficiency/out/v11/sheet.jpg"}
```

Гарнитуры: в примерах A Oswald (Лесная обжарка L0/L2, «Окошко» напр. C, «Кварц») и Nunito («Лесная обжарка» L0, «Окошко» напр. B) — в v1
заменить по `../04-visual-language/cyrillic-display-fonts.yaml`: Oswald → Sofia Sans Condensed или PT Sans Narrow (Druk — коммерческая опция),
Nunito → Commissioner или Golos Text; поле `type.cyrillic_checked: true` только после сверки с каталогом D `[документация: D, type.today]`.
Счёт `accent` — не в art-direction, а в treatment страницы (§2.4).

## 6. Пакет исполнителя: что куда

### 6.1. Проекции

| Из | В пакет kimi (07/02) | Как |
|---|---|---|
| `treatment.page.motion_system.thesis`, max `motion_level` | `brief.yaml decisions.motion.level`, `.thesis` → `TASK.md`, `DESIGN.md ## Motion` | сборщик kimi `build_package.py` |
| motion-spec моменты | `decisions.motion.moments` (строки T7) → `TASK.md`, `ACCEPTANCE E3` | `spec_check.py moments` |
| motion-spec целиком | `MOTION.md` (таймлайн, станции, раскадровка, reduce, телефон, контракт разметки) — новый файл пакета | `spec_check.py motion-md` |
| числа моментов | `motion/<секция>.motion.json` для модуля эффекта (правит Claude, K3 не трогает код) | `spec_check.py values` |
| `motion.marketing` токены | `DESIGN.md` + `tokens.css` (вместо `design_system.motion_tokens` kimi 150/240/400) | сборщик kimi — предложение §6.2 |
| референсы движения | `refs/motion-NN.mp4` или лист 3×3 + кадры + таймлайн; `refs/README.md` Take / Do not take | B `02/03` §5.1, `02` §4 |
| решения о клише | блок «чего не ставить» + `--allow` из `k3_allow` | H `08/01` §6.2 |
| `acceptance[]` motion-spec | `ACCEPTANCE.md` E-блок и H-блок (ворота K) | вручную / K |

Проверено на трёх примерах: `moments`, `motion-md`, `values` строят файлы без ошибок (`99-raw/experiments/I/01-schemas/out/`) `[проверено]`.

### 6.2. Что сборщику kimi не хватает (предложения, их файлы не правим)

- `build_package.py` пишет «Transform and opacity only» в `MOTION_LINE` и `MOTION_PROSE` **при любом уровне** — на L1–L2 разрешены clip-path,
  mask, filter (blur ≤ 8 px), @property (E П12): строка должна браться из `page.properties_allowed` motion-spec.
- `design_system.motion_tokens` kimi (150/240/400 мс, in-out `(0.77, 0, 0.175, 1)`) расходятся с `motion.marketing` (E): для маркетинговой
  страницы — наши токены.
- `decisions.motion.moments` — список строк; для сцены прокрутки строки не хватает (станции, subject диапазона, reduce) → поле
  `decisions.motion.spec_ref` + `MOTION.md` в пакете.

### 6.3. Разметка и штамп

Исполнитель ставит атрибуты контракта (§2.5) и штамп в начале CSS секции — какие решения он реализовал (идея Hallmark «Output stamp»,
`hero-enrichment.md` `[мнение вендора]`):

```css
/* treatment: how-it-works · peak · L1 · vertical-progress-line · effect:scroll-driven-progress
 * motion-spec: otves-home 1.1 · moments: plumb-line-drop, plumb-bob-follow, step-marker-fill
 * reduce: final-state · mobile: simplified · js: 0 KB · [проверено] */
```

## Частые ошибки

1. Треатмент словами («линия-отвес с грузиком») без `motion_spec_ref` — исполнитель додумывает диапазон; в опыте I/02 — отставание до 98 px.
2. Старые id секций (`kak-rabotaem.step`, `funktsii.row`) после перехода site на v1 — цель не находится (TR-09).
3. Пик без `purpose: signature` или два пика подряд на L1 — «вау» без ритма (генератор ставит приёмы подряд — E `05/02` §1.1).
4. Эффект с `level_min` выше уровня секции (pin на L0, custom-cursor на L1) — схема v1 ловит.
5. Эффекты на форме, тарифах, калькуляторе — конверсия всегда L0.
6. `text-over` без контраста; видео без `flash_check`; `cinematic` без ролика — «кино-hero» на заглушке.
7. `mobile: same` у тяжёлой сцены или центр-кроп 16:9 как «мобильная версия» (scroll-world: «Never ship the centre-crop»).
8. **Ошибки нейросетей**: K3 копирует план site без art-direction (появление hero вопреки решению); Claude пишет в `target` CSS-селектор
   вместо id; генераторы ставят `scroll-reveal-system` на каждую секцию (`section-fade-up`, H) и `smooth-scroll` по умолчанию (K3 4 из 17).
9. `visual_variant` «из головы» — вариант, которого нет у блока (TR-13); или вариант для `split`, применённый к `background`.
10. Треатмент в одном файле, числа движения в коде исполнителя — правка чисел требует правки кода (W3: числа — в JSON секции).

## Чек-лист

- [ ] CRV-TR-01 У каждой секции есть `level`, `visual_role`, `motion_level`, а у утверждённой — `status: approved`?
- [ ] CRV-TR-02 Пики, акценты и секции с `signature` — в норме уровня, двух пиков подряд нет, `page.peaks/accents/signature_sections` сходятся?
- [ ] CRV-TR-03 Секции конверсии — L0, `calm`, без эффектов?
- [ ] CRV-TR-04 Все эффекты есть в `effects.yaml`, `level_min` ≤ уровня секции, эффект — из списка блока или с решением art-direction?
- [ ] CRV-TR-05 Цели — id v1 плана (`секция.слот`, `секция.группа`, `секция.fx-…`), `spec_check.py plan` без TR-09?
- [ ] CRV-TR-06 У эффектов и сцен есть `reduce` (стратегия) и `mobile` (стратегия + что меняется)?
- [ ] CRV-TR-07 Петли — `loops` и `loop_control`; `page-toggle` — только при `reduce_toggle`?
- [ ] CRV-TR-08 `text-over` — `text_contrast`; видео и прелоадер — `flash_check`; `cinematic` — ролик или рендер?
- [ ] CRV-TR-09 `visual_variant` из `block-treatments.yaml`, совпадает со структурным вариантом плана?
- [ ] CRV-TR-10 У пика и акцента — `motion_spec_ref` на существующий раздел motion-spec?
- [ ] CRV-TR-11 Гарнитуры art-direction — из каталога D с кириллицей (нет Oswald; Nunito — только с причиной)?
- [ ] CRV-TR-12 Пакет исполнителя получил `MOTION.md`, токены `motion.marketing`, блок «чего не ставить» и `--allow`?

## Открытые вопросы и противоречия

- **A ↔ E о счёте**: «≤ 2 секции с приёмом (peak или accent)» (A, L1) против «пиков ≤ 2, акцентов ≤ 3» (E) — принято три величины (§2.4);
  нормы акцентов — `[не проверено]` до калибровки K. Текст правила L1 в `ambition-levels.yaml` приведён к трём счётам — S1 2026-09-25 (X-19).
- **План site ↔ art-direction A** («Окошко»: hero с появлением в плане, без появления в art-direction) — примеры следуют art-direction; site
  поправит план при переходе на treatment v1.
- **site ↔ creative о линии шагов на телефоне** (`blocks.yaml` steps — линии убираются) — предложение §3.3, решение за site.
- **F ↔ E**: `parallax-layers.limits.layer_speed_diff_pct_max` 30 % (F) против 40 % (E, токен `scroll.parallax-ratio-max 0.4`) — в схеме
  не зашито; `spec_check` сверяет `params` с `limits` F; нужно одно число (синтез S). **Закрыто S1 2026-09-25**: `limits` —
  `layer_speed_diff_pct_max: 40` (= E и токен), `layer_speed_diff_pct_default: 30` (лаборатория, рецепты) (`CONTRADICTIONS.md` X-08).
- **G ↔ E/D**: атрибут переключателя `data-motion="reduce"` (G) против `reduced | full | paused` (E, токены D) — motion-spec фиксирует `reduced`,
  K принимает оба; предложение G. **Закрыто X 2026-09-25**: `07/02` приведён к `reduced` (`CONTRADICTIONS.md` X-12).
- art-direction v1 — схема в папке 09 (генерируется из v0 A); перенос к владельцу формата и примеры A на v1 — A или S; генератор проекций
  art-direction → visual-dna и brief.yaml не написан.
- Как K3 прочтёт `MOTION.md`, контракт разметки и `stations` — не проверено (K3 не запускался) → живая фаза.

## Источники

- [S1] creative A, `../01-creative-direction/drafts-for-site/treatment.v0.schema.json` (304 строки, 2026-09-24) — исходная подсхема; основа v1.
- [S2] creative A, `../01-creative-direction/art-direction.schema.json` v0 и `examples/*.json` (5 примеров) — поля, гарнитуры, решения.
- [S3] creative A, `../01-creative-direction/ambition-levels.yaml` v0.1 — `section_caps`, `section_distribution`, `maps_to.kimi`, CRV-AL-01…12.
- [S4] site, `../../site/10-playbooks-contracts/schemas/page-plan.schema.json` v1, `99-raw/notes/sync/S1v1-site-2026-09-24/README.md`,
  `99-raw/handoff-to-neighbours.md` (C1–C3) — подключение treatment, media-slot, id v1.
- [S5] site, `../../site/04-blocks/blocks.yaml` 1.0 (84 блока, sha256 83fc60eb1e6f) — варианты, телефон, C3.
- [S6] site, `../../../scripts/site/site_validate.py` (PL-C01) и `vocab_lint.py` — проверки, путь к схеме treatment.
- [S7] site, примеры `../../site/10-playbooks-contracts/examples/` («Отвес», «Окошко», «Сталькон») — планы для опытов.
- [S8] creative E, `../05-motion/01-motion-principles-and-access.md` — классы, reduce (§4.2), бюджет (§5), П11–П12, CRV-MO-*.
- [S9] creative E, `../05-motion/02-choreography-scroll-transitions.md` — роли §1.2, хореография §1.4, примитивы §2.2, pin §4, LCP §10.
- [S10] creative D, `../04-visual-language/01-display-typography.md` §2, `02-composition-rhythm-sections.md` §2.1, `marketing-tokens.json/.css`.
- [S11] creative D, `../04-visual-language/cyrillic-display-fonts.yaml` — замены Oswald и Nunito.
- [S12] creative F, `../06-effects-catalog/effects.yaml` 0.1 и `effects.schema.json` — 49 id, `level_min`, `limits`.
- [S13] creative G, `../07-stack-implementation/02-implementation-patterns.md` §2, §6 — модуль эффекта, режим, загрузчик.
- [S14] creative H, `../08-uniqueness-anti-slop/01-cliche-policy.md` §3, §6; `02-uniqueness-and-variation.md` §3–4; `cliche-registry.yaml` 0.1.
- [S15] creative B, `../02-references-moodboards/03-moodboard-and-handoff.md` §3–5 — Take / Do not take, передача исполнителю.
- [S16] kimi, `../../kimi-research/07-brief-handoff/02-task-package.md` §1–2 и `templates/` (DESIGN.md, ACCEPTANCE.md, brief.yaml, build_package.py).
- [S17] kimi, `../../kimi-research/07-brief-handoff/01-from-app-description-to-brief.md` §6.2 — шкала движения.
- [S18] text, `../../text/10-templates-recipes/copy-deck.schema.json` v1, `04-copy-by-block/copy-slots.yaml` — слоты, длины H1.
- [S19] higgsfield-ai/skills, `higgsfield-websites/references/wow-catalog.md` (клон kimi, 2026-09-24) — контракты реализации `[мнение вендора]`.
- [S20] oso95/scroll-world, `skills/scroll-world/SKILL.md` (коммит 71cc36d, 2026-07-28) — интервью, камера и телефон «ALWAYS ask» `[мнение вендора]`.
- [S21] Nutlope/hallmark, `skills/hallmark/references/hero-enrichment.md` — иерархия обогащения, Output stamp `[мнение вендора]`.
- [S22] Дайджест Dogstudio `[V:Ulgy6xIrdPg]` — money idea 07:23, прототип 11:31, advanced wireframe 14:57.
- [S23] Дайджест Val Head `[V:OqvQhZ0bTYY]` — прилагательные → приёмы 37:11–39:46.
- [S24] Дайджесты Arizio `[V:xQnJLYTVl_E 23:30]`, `[V:7nEvk6nFeS4 05:20]`, `[V:ilNOMaR6x_U 23:48]` — мотив, R&D до обещания, масштаб.
- [S25] creative K, `effect-gates.yaml` и `99-raw/notes/wave3/K-notes.md` «## Для I» — ворота, контракт разметки.
- [S26] Опыты I/01 и I/02 — `../99-raw/experiments/I/`; результаты — разделы 2.3–2.7 этого файла.
