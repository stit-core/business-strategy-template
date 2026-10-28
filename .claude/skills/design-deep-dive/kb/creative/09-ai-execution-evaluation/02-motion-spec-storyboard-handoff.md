# Спецификация движения, раскадровка и видео-референсы для исполнителя

Волна 3 · агент I · 2026-09-24/25 · источников 31 (файлы базы, соседей и сестёр, 3 клона скиллов, 9 дайджестов роликов) · опытов 2
(`99-raw/experiments/I/01-schemas`, `02-spec-sufficiency`: 2 сборки × 2 движка × 3 режима + 3 записи прокрутки) · Chromium 1243, WebKit 2359
(Playwright 1.63) · CSS scroll-driven animations · артефакты: `motion-spec.schema.json` v1, `examples/*.motion-spec.yaml` (3), `spec_check.py`.

## Выжимка для агента

1. **Движение передавай таймлайном, не прилагательными**: у каждого момента — класс, функция, триггер, цель, свойство from → to, время
   (токен, мс или доля базы) или диапазон прокрутки, кривая-токен, reduce, телефон, пауза. → §1.2 `[консенсус: E, kimi T3c/T7]`
2. **Класс момента решает обязательное**: `loop` → период или скорость + пауза; `scroll-linked` → диапазон и subject; `one-shot` → длительность;
   `pointer` → телефон; пружина → параметры. → §1.3 `[практика: E §1.3]` `[проверено: схема]`
3. **Диапазон прокрутки задавай по геометрии того, что движется**: `subject` = сам элемент (его layout-box); диапазон по соседнему
   элементу дал отставание 98 px. → §3 `[проверено]`
4. **Станции — якорями, не долями**: «маркер шага N на середине окна», а не `at: 0.33`, если шаги разной высоты. → §2.2 `[проверено]`
5. **Не пиши чисел, которые требуют замера, при бюджете JS 0** (`var(--line-length)`): описывай видимое (`attach: {to, point}`). → §1.5 `[проверено]`
6. **Числа — из токенов `motion.marketing` или доли базы** (`page.base.duration_ms` × share); мс вне шкалы — предупреждение (CRV-MO-14). → §1.4 `[практика: E, Bramus]`
7. **LCP-элемент помечен** (`page.lcp`): без анимации или вход по CRV-AL-09 — transform со сдвигом ≤ 24 px, clip-path или opacity
   от 0,01; не из opacity 0, не маской строк. → §1.6 `[проверено]`
8. **Опиши выход и прерывание**: `transition_type` (entrance / exit / persistent), `exit`, `interrupt` — иначе исполнитель анимирует только вход. → §1.5 `[практика: V Ug_dwJa07Os, v5oxrZWAq78]`
9. **У каждого движения — функция** (`purpose`): attention, guide, inform, continuity, orient, narrate, feedback, personality, loading; без функции — удалить. → §1.2 `[мнение: V J6aNMFZogyk]`
10. **Характер — прилагательными бренда из словаря** (energetic … heavy), приёмы — из таблицы Val Head. → §1.4 `[практика: V OqvQhZ0bTYY]`
11. **Ветки без JS и без поддержки** (`fallback`) — отдельно от reduce: Firefox без CSS scroll-driven получает конечное состояние. → §1.6 `[документация: E §3.1]`
12. **Разметка по контракту**: `data-section`, `data-slot`, `data-group`, `data-fx`, `data-moment`, `data-effect` — проверка находит цели без угадывания. → §1.7 `[практика: K]`
13. **Раскадровка — кадры станций + кадр телефона + кадр reduce**, у каждого `check`, измеримый на записи. → §2 `[практика: V Ulgy6xIrdPg 14:57, 5MMm5DUjh78 34:51]`
14. **Запись прокрутки в паузах не видит скраб**: у scroll-linked в покое 0 % и при работе, и при поломке — проверяй зондом станций (геометрия на якорях). → §2.4 `[проверено]`
15. **Видео-референс — только отрезки «что взять» с таймкодами**, объект + свойство + число, и обязательное «чего не брать». → §4.3 `[практика: B, kimi]`
16. **Видео K3 видит только в Kimi Code + модель k3 + провайдер kimi**: mp4 H.264 ≤ 1080p, 10–20 с, ≤ 20 МБ, без звука; Claude — лист 3×3 и кадры. → §4.2 `[документация: kimi 07/03]`
17. **Источник видео-референса — своё**: запись публичного сайта для внутренней работы, лабораторная страница F, прототип, ролик заказчика; чужие ролики не качать. → §4.1 `[практика: решения заказчика 4, 6]`
18. **Сначала прототип главного эффекта** (лабораторная страница), его запись — видео-референс и доказательство для заказчика. → §4.1 `[практика: V 7nEvk6nFeS4 05:20]`
19. **Уводи «почерк» полями, а не просьбами**: `primitives` ≤ 3, `never`, `properties_allowed`, `page.lcp`, `scroll.smooth: false` — каждое проверяется. → §5 `[данные: kimi 05/03, H]`
20. **K3 T7 на маркетинге — со спецификацией**: моменты из motion-spec, свойства по уровню, LCP-правило, «no scroll-jacking» = не менять скорость и направление. → §6.4 `[мнение вендора: impeccable]` `[данные: kimi]`
21. **Уровни L0–L2 → none/subtle/expressive/cinematic**: L0 → subtle, L1 → expressive, L2 → cinematic только с роликами, иначе expressive. → §6.1 `[практика: E П11, A]`

## 1. `motion-spec` v1

### 1.1. Где живёт

Схема — `09-ai-execution-evaluation/motion-spec.schema.json` (`urn:app-design:creative:motion-spec:1`); документ — YAML или JSON на
страницу: `page` (тезис, характер, база, примитивы, LCP, переключатель, прокрутка, переходы, свойства, бюджет, `never`) → `sections[]` (id v1
плана, роль, сцена со станциями, моменты, раскадровка, видео-референсы, reduce, телефон, `fallback`, бюджет, `acceptance`). Treatment секции
ссылается `motion_spec_ref: <файл>#/sections/<id>`. Примеры: `examples/otves-home.motion-spec.yaml` (скраб-линия, CSS), `okoshko-home` (sticky-окно
и смена состояний, CSS), `stalkon-home` (кросс-документный View Transition) — `spec_check.py spec` 0 ошибок `[проверено]`.

### 1.2. Момент

| Поле | Значения | Правило |
|---|---|---|
| `class` | one-shot, scroll-linked, loop, pointer, transition | E `05/01` §1.3; от класса — 2.2.2, reduce, бюджет внимания |
| `purpose` | attention, guide, inform, continuity, orient, narrate, feedback, personality, loading | без функции — удалить (Paquet [V:J6aNMFZogyk 04:14]) |
| `transition_type` | entrance, exit, persistent | Cassie Evans [V:v5oxrZWAq78 18:41]: persistent — FLIP или View Transitions |
| `target`, `stagger_targets` | id v1: `секция.слот`, `секция.группа`, `секция.группа-N.элемент`, `секция.fx-имя` | разрешение — `spec_check.py`, в разметке — контракт §1.7 |
| `trigger` | load, in-view, scroll-scrub, pin-scrub, hover, focus, click, pointer, idle-loop, page-transition, state | + `subject`, `range` (CSS view-timeline), `range_vh`, `progress`, `threshold`, `after`, `delay_ms` |
| `model` | time, spring, scrub | пружина — только геометрия от указателя, bounce ≤ 0,2 (E §7.3) |
| `tracks[]` | `{property, from, to}` или `keyframes` | свойства по уровню §1.6; раскладку — никогда |
| `duration` | `{token}` / `{ms}` / `{share}` | доля базы — хореография одной переменной (Bramus [V:QA5f2loqtM4 27:30]) |
| `easing` | `{token}` / `{css}` / `{none: true}` (скраб) | входы — `out-expo`, перемещение — `in-out`, петли — linear |
| `stagger` | `{each, order, max_items, total_ms_max}` | 40–80 мс, сумма ≤ 600 мс (E §7.4) |
| `repeat`, `loop` | once / each-entry / infinite; `{period_ms, speed_px_s, autostop_ms, idle_pixels_pct_s_max}` | строка 30–60 px/с; «дыхание» ≤ 2,5 %/с; полоса 2,5–6 с — нет |
| `scrub` | `{smoothing_s ≤ 1, snap: none|stations}` | snap — только L2 |
| `interrupt` | jump-to-end, reverse, restart, ignore, follow-input | быстрая прокрутка — `jump-to-end` (fastScrollEnd) |
| `exit` | `{behavior, duration, easing}` | автомат entering → entered → exiting → exited (Тактаров [V:Ug_dwJa07Os 27:49]) |
| `attach` | `{to, point: start|end|center}` | видимое вместо чисел, требующих замера (§3) |
| `reduce`, `mobile`, `pause`, `lcp` | стратегии; `pause.control` page-toggle / pause-button / autostop / not-parallel-content | у каждого момента |
| `params`, `tunable` | числа эффекта в пределах `limits` F; что вынести в JSON секции | Claude правит числа, K3 не трогает код эффекта (W3) |

### 1.3. Что требует класс (схема и скрипт)

| Класс | Обязательно | Скрипт проверяет |
|---|---|---|
| `loop` | `loop`, `pause`, `repeat: infinite` | петель в секции ≤ 1 / 2 / 3; период 2,5–6 с у фона и 3D — ошибка (E §6.3); `page-toggle` без переключателя — ошибка |
| `scroll-linked` | `trigger.type` scroll-scrub / pin-scrub и `range`, `range_vh` или `progress` | длина сцены с закреплением: L1 ≤ 150vh, L2 ≤ 400vh, шаг между станциями ≤ 150vh; `snap` вне L2 — ошибка |
| `one-shot` | `duration`; `repeat` once или each-entry | сцена первого экрана ≤ 1 200 мс (задержка + длительность + стаггер) |
| `pointer` | `mobile` (замена касанием или статика) | — |
| `transition` | — | переход ≤ 400 мс в многостраничнике — через `never` и приёмку |
| любой с `lcp: is-lcp` | вход по CRV-AL-09: `transform`/`translate`, `clip-path` или opacity от 0,01 | сдвиг ≤ 24 px (токены раскрываются); `page.lcp.entrance: none` — анимация LCP-элемента запрещена |

Прочие коды `spec_check.py spec`: MS-01 секция есть в плане и уровень совпадает; MS-02 роль = `visual_role` treatment; MS-03 цель найдена; MS-04
эффект есть и по уровню; MS-05 класс = `motion.kind` каталога (строка или список классов — у `3d-scene` скраб и разовое пробуждение, X-64); MS-06 токен есть; MS-07 мс вне шкалы; MS-08 свойство по уровню и blur ≤ 8 px;
MS-11 стаггер; MS-12 скорость строки по `limits` F; MS-16/MS-21 пик без раздела или эффект treatment без момента; MS-17/MS-18 станции;
MS-19 появление из opacity 0 в первом экране; MS-22 ворота `acceptance.gate` есть в `effect-gates.yaml` K.
Шкала длительностей (MS-06, MS-07) — токены `motion.marketing` базы и токены времени ветки `motion` файла `refs.tokens` проекта: ссылка
на токен проекта и длительность, равная его значению, — не находка.

### 1.4. Числа, характер, база

- Длительности и кривые — токены `motion.marketing` (`04-visual-language/marketing-tokens.json`, CSS `--mm-*`): duration.feedback 120, hover 200,
  state 320, page 400, reveal 560, split-line 800, hero-scene 900, counter 1 200; stagger.group 60; easing.out-expo `(0.16, 1, 0.3, 1)`,
  in-out `(0.65, 0, 0.35, 1)`; длина закрепления — токены `scroll.pin-l1-max-vh` и `scroll.pin-l2-max-vh`; loop.marquee-speed 40 `[практика: E]`.
- `page.base.duration_ms` + `share` у моментов: темп страницы меняется одной правкой; у «Отвеса» база 400, подъём текста 0,8 × 400 = 320 мс.
- `page.character` — до трёх слов; приёмы по Val Head [V:OqvQhZ0bTYY 37:11–39:46]: follow-through → energetic, friendly, bold; squash and
  stretch → playful; ease-in-out → balanced, measured; малые сдвиги → calm, subtle; прозрачность и blur → soft, stable `[практика]`.
  Свои: precise (короткие пути, без пружин), heavy (медленный разгон, без bounce).

### 1.5. Геометрия, станции, выход

- `trigger.subject` — чей layout-box задаёт диапазон (по умолчанию — цель). `range` — синтаксис CSS view-timeline с длинами:
  `cover 50vh` → `cover calc(100% - 50vh)` = «от верха subject на середине окна до низа subject на середине окна» `[проверено: I/02, Chromium 1243, WebKit 2359]`.
- `station.anchor` + `anchor_line` — станция по элементу (точка — `data-anchor-point` на маркере шага); `at` (доля) — только при равных
  шагах: сцена выше окна — `contain` (0 — верх секции у верха окна, 1 — низ у низа), иначе — `cover`; допуск станции — ±24 px
  включительно после округления; `scene.length_vh` — путь прокрутки сцены, а не высота секции (схема, X-57, S1 2026-09-25).
- `attach` — «ромб на конце линии»: исполнитель выбирает механизм без JS (прозрачная коробка длиной линии и `translateY(-100%) → 0` на том же
  таймлайне совпала с концом линии до 0,2 px) `[проверено]`.
- Выход: `exit.behavior` none / reverse / fade / remove-after; для переходов состояний — `transition_type: persistent` и FLIP или View Transitions.

```css
/* Chrome 115+ · Safari 26+ · Firefox — конечное состояние · 2026-09-25 · [проверено] */
.steps { position: relative; timeline-scope: --line; }                 /* грузик видит таймлайн линии-соседа */
.steps__line { position: absolute; left: 5px; top: calc(.35em + 6px); bottom: 0; width: 2px; transform-origin: top; view-timeline: --line block; }
.steps__bob  { position: absolute; left: 0; top: calc(.35em + 6px); bottom: 0; width: 12px; }   /* ромб — ::before у низа */
@media (prefers-reduced-motion: no-preference) {
  @supports (animation-timeline: view()) {
    .steps__line { animation: drop linear both; animation-timeline: --line; animation-range: cover 50vh cover calc(100% - 50vh); }
    .steps__bob  { animation: bob  linear both; animation-timeline: --line; animation-range: cover 50vh cover calc(100% - 50vh); }
    .step__marker { animation: fill linear both; animation-timeline: --marker; animation-range: cover calc(50vh - 6px) cover calc(50vh + 6px); }
  }
}
@keyframes drop { from { transform: scaleY(0); } to { transform: scaleY(1); } }
@keyframes bob  { from { transform: translateY(-100%); } to { transform: translateY(0); } }
```

### 1.6. Уровень, LCP, ветки

- Свойства: L0 — transform, opacity, color, background-color; L1–L2 — ещё clip-path, mask, filter (blur ≤ 8 px), stroke-dashoffset,
  @property-переменные, font-variation-settings (E П12); раскладка — никогда `[мнение вендора: impeccable]` `[данные: kimi — 13 из 13]`.
  Исключение — `block-size` у `::details-content` аккордеона `<details>` (`effect:details-accordion`, класс `transition`, `interpolate-size:
  allow-keywords`, ≤ 300 мс, reduce — мгновенно): UI-отклик по клику, не сцена; схема пускает его только с этим `effect` (X-11, S1 2026-09-25).
- `page.lcp {target, entrance: none|transform-only}`; LCP-элемент: без анимации или вход по CRV-AL-09 — transform со сдвигом ≤ 24 px,
  clip-path или opacity от 0,01; не из opacity 0, не маской строк (E/01: opacity 0, маска строк, скрытие скриптом выбивают H1 из
  кандидатов LCP) `[данные: у E]`.
- `page.toggle`: L2 — всегда, L1 — при петле с `page-toggle` или ≥ 2 scroll-linked секциях; `data-motion` на `<html>`: нет — как в системе,
  `reduced`, `full`, `paused`; кнопка с `aria-pressed` (E §4.4). У G `reduce` — K принимает оба; предложение G — `reduced`.
- `section.fallback {no_js, unsupported}`: CSS scroll-driven — Chrome 115+, Safari 26+, Firefox только Nightly — BCD `preview` (E `05/02` §3.1,
  2026-09-24) → без поддержки — конечное состояние; sticky без смены состояний не оставлять (окно показывало бы только первое состояние).

### 1.7. Контракт разметки

`x-dom-contract` схемы (предложение K, 2026-09-24): `data-section="<id секции>"` (или `id`), `data-slot`, `data-group="<группа-N>"`, `data-fx="<имя>"`
для целей `секция.fx-имя`, `data-moment="<id момента>"` на элемент, который двигает момент, `data-effect` — модуль эффекта G. Порядок поиска
`motion_check.py`: `[data-moment]` → `[data-section] [data-slot|data-group|data-fx]` → `#секция [data-slot]` → `selector_hint`. Проекция
`motion-md` пишет контракт в `MOTION.md`, строки T7 — `[data-moment=id]` у каждого момента `[проверено: I/01 out/]`.

## 2. Раскадровка

### 2.1. Что это для исполнителя, который не видит видео

VLM видит конечные кадры, не движение (PLAN, риск 4); раскадровка переводит замысел в **кадры, которые можно снять и сравнить**. Кадр —
`storyboard.frames[]`: `at` (`{station}`, `{progress}`, `{time_ms}`, `{scroll_vh}`), `viewport` (desktop, mobile, reduce), `describe` (что где, какой
крупности, что движется), `visible[]`, `sketch`, `sketch_kind`, `check` (что должно совпасть на кадре записи).

| Вид кадра | Когда | Источник |
|---|---|---|
| `keyframe` — кадр станции | каждая станция сцены + первый и последний кадр первого экрана | E `05/02` §4.1: сцена заканчивается станцией |
| `onion-skin` — «advanced wireframe» | путь объекта через страницу (карта, отвес, продукт): полупрозрачные положения вдоль пути на одном листе | Dogstudio [V:Ulgy6xIrdPg 14:57] `[практика]` |
| `wireframe` по размерам экрана | раскладка меняется по ширине (лента на телефоне, разворот на широком) | Andy Clarke [V:5MMm5DUjh78 34:51] `[практика]` |
| `contact-sheet` | все станции и режимы одним листом для VLM-судьи K | `shoot_stations.py` I/02 |

### 2.2. Правила

- Минимум для сцены прокрутки: станция начала, одна средняя, станция конца, кадр телефона, кадр reduce — 5 кадров; для hero — 0 мс и конец сцены.
- Станции — якорями (`anchor` + `anchor_line`); `describe` — объект, место, крупность, состояние («конец линии у маркера 2, маркеры 1–2 залиты»),
  не оценка («красиво опускается»).
- `check` — измеримое на кадре: «конец линии ±24 px от маркера», «состояние 2 непрозрачно», «пометка прочерчена целиком».
- Эскиз без генерации: кадр прототипа (лабораторная страница F или своя), SVG-прямоугольники раскладки; ИИ-картинка эскиза — только через
  ai-media (платно — живая фаза).

### 2.3. Пример («Окошко», product-demo)

```yaml
# motion-spec v1 · 2026-09-24 · [проверено: spec_check.py spec — 0 ошибок]
stations:
  - {id: s1, anchor: product-demo.row-1, anchor_line: viewport-center, describe: "функция 1: окно — день с пустыми окнами"}
  - {id: s2, anchor: product-demo.row-2, anchor_line: viewport-center, describe: "функция 2: окна заполнены записями"}
  - {id: s3, anchor: product-demo.row-3, anchor_line: viewport-center, describe: "функция 3: неявка исправлена, вокруг записи красная рамка"}
frames:
  - {id: pd-s2, at: {station: s2}, viewport: desktop, describe: "текст функции 2 на середине; окно то же, внутри заполненный день",
     check: "состояние 2 непрозрачно, состояние 1 под ним"}
  - {id: pd-r, at: {station: s2}, viewport: reduce, describe: "три кадра рядом с абзацами, без закрепления", check: "движение 0 %, закрепления нет"}
```

### 2.4. Как проверяется

- `scroll_record.py` (C) снимает паузы между шагами колеса: у scroll-linked движение в паузах 0 % и при работающем, и при сломанном скрабе —
  записи «Отвеса» v1.1 на десктопе, телефоне и в reduce дали 0,0 % во всех трёх `[проверено]`.
- Хореографию прокрутки проверяет **зонд станций**: прокрутить к якорю, замерить геометрию (конец линии относительно линии окна, число залитых
  маркеров, непрозрачность состояния) и снять кадр — `99-raw/experiments/I/02-spec-sufficiency/shoot_stations.py` (Chromium + WebKit, 3 режима,
  ≈ 40 с); предложено K как метрики `stations.tip_offset_px`, `stations.filled` в `motion_check.py`.

## 3. Опыт I/02: достаточна ли спецификация

Секция-пик «Отвеса» (линия-отвес с грузиком через четыре шага, CSS scroll-driven, 0 КБ JS) собрана **только** по `otves-home.motion-spec.yaml` v1.0,
затем по ревизии 1.1; кадры станций — в двух движках и трёх режимах. Метод и файлы — `99-raw/experiments/I/02-spec-sufficiency/README.md`.

| Сборка | Chromium desktop, конец линии − середина окна, px (s1 · s2 · s3 · s4) | WebKit desktop | Телефон (Chromium) | Reduce |
|---|---|---|---|---|
| по v1.0 | +10 · −27 · −65 · **−98** | +10 · −25 · −61 · −96 | +10 · −24 · −62 · −96 | линия целиком, 4 маркера |
| по v1.1 | 0,0 · 0,0 · 0,0 · 0,0 | 0,0 · 0,0 · 0,0 · 0,0 | ≤ 0,5 | линия целиком, 4 маркера |

Что пришлось додумать по v1.0 (8 пунктов): чей view() задаёт диапазон (был в `note`); `var(--line-length)` при бюджете JS 0; низ линии «до центра
маркера 4» без JS (118 px на глаз); шаг или маркер — subject заливки; станции долями при разной высоте шагов; маркеры без поддержки механизма;
маркеры на телефоне; шрифты и отступы (это `DESIGN.md`, не motion-spec). Правки схемы: `trigger.subject`, `trigger.axis`, `station.anchor`,
`anchor_line`, `moment.attach`, `section.fallback` — после них та же сборка совпала с замыслом до 0,5 px `[проверено]`.

Вывод: таймлайн «триггер → свойство → время» необходим, но **недостаточен для сцен прокрутки**: диапазон и станции должны быть привязаны к
геометрии элементов, иначе исполнитель соберёт «правильно по буквам», а VLM по скриншоту расхождения не увидит.

## 4. Видео-референсы для K3

### 4.1. Когда и откуда

- Видео нужно, когда характер движения не сводится к числам спецификации: ощущение кривой, темп монтажа, «вес» объекта, работа камеры.
  Всё, что выражается числами, — в motion-spec; видео — дополнение с отрезками «что взять», не замена.
- Источники по правам (решения заказчика 4 и 6): (1) **своя лабораторная страница или прототип** главного эффекта (лучший: это и есть замысел);
  (2) запись публичного сайта для внутренней работы — `scroll_record.py --keep-video` (C), отрезок сцены, `rights: internal-only`, референс
  никогда не становится ассетом; (3) ролик-прототип Figma или After Effects (Paquet [V:J6aNMFZogyk 24:43]); (4) ролик заказчика. Чужие ролики с
  YouTube и площадок не качать (видео — только трек V).
- Прототип главного эффекта до утверждения направления — «сначала R&D, потом обещание» ([V:7nEvk6nFeS4 05:20]; Dogstudio — код-прототип до
  макетов [V:Ulgy6xIrdPg 11:31]) `[практика]`: его запись — и доказательство для заказчика, и видео-референс для K3 (`art-direction.prototype`, `01` §5).

### 4.2. Формат

| Исполнитель | Что класть | Предел |
|---|---|---|
| Kimi Code 2.0.2 + модель `k3` + провайдер kimi (`video_in`) | `refs/motion-NN.mp4`: H.264, ≤ 1080p, 10–20 с, без звука, `+faststart` | ≤ 20 МБ (сборщик kimi — ошибка `ref-video-size`); API — до 100 МБ, T3c пишет «≤ 100 МБ» — брать 20 |
| Claude Code, `k3-256k`, OpenAI-совместимый шлюз | лист 3×3 (1920×1080) + 6–10 кадров 1280×720 с таймкодами + таймлайн текстом (моменты motion-spec) | видео не доходит |

K3 сэмплирует ≈ 8 кадров/с; ролик 720p 10 с ≈ 23 тыс. токенов, до ≈ 41 тыс. на ролик — оценка kimi по конфигу препроцессора `[не проверено: сервер]`.
Команды ffmpeg (обрезка, лист 3×3, кадры) — `../../kimi-research/07-brief-handoff/03-references-brand-assets.md` §2.3; запись `scroll_record.py`
(VP8/WebM) перекодировать в H.264 (`-threads 4`), вырезать 10–20 с вокруг сцены, исходную запись удалить.

### 4.3. Отрезки «что взять»

```yaml
# motion-spec v1 · references[] · 2026-09-25 · [не проверено: реакция K3 на отрезки]
references:
  - id: plumb-proto
    kind: video
    file: refs/motion-01.mp4
    source: {type: lab-page, url: 99-raw/experiments/I/02-spec-sufficiency/page/v11.html, recorded_at: "2026-09-25", rights: own}
    format: {codec: h264, height: 1080, duration_s: 14, size_mb: 3.1, audio: false}
    take:
      - {from: "00:02.0", to: "00:07.5", what: "линия растёт ровно под серединой окна, 2 px, без инерции: 1 шаг ≈ 30 % высоты окна прокрутки", maps_to: [plumb-line-drop]}
      - {from: "00:07.5", to: "00:09.0", what: "маркер шага заливается за последние 12 px подхода линии, цвет мгновенно не прыгает", maps_to: [step-marker-fill]}
    do_not_take: ["шрифт и тексты лабораторной страницы", "серые заглушки выше и ниже секции"]
```

- `take[].what` — объект + свойство + число (B `02/03` §3.2), `maps_to` — id моментов; `do_not_take` обязателен (минимум один пункт).
- ≤ 2 референса на секцию; один референс — одна секция (как у библиотеки B).
- K3 по T3c пишет `MOTION.md` своим таймлайном: сверить его с нашей спецификацией построчно — тест живой фазы «понимает ли K3 видео» (§6.5).

## 5. «Почерк» исполнителей в движении и как его уводить

| Примета | Где замечена | Поле спецификации, которое уводит | Проверка |
|---|---|---|---|
| одинаковый fade-and-slide-up на всех секциях | K3 6 из 15; AOS 8,1 млн загрузок за 8 мес. 2026 (H) | `page.primitives` ≤ 3, секции без моментов «do not animate», `never` | запись; `cliche:section-fade-up` (H) |
| анимация свойств раскладки | K3 13 из 13 (kimi 05/03) | `properties_allowed`, свойство `track.property` из списка | grep T7; `spec_check` MS-08; K |
| WebGL-«центр», крутящийся сам | K3 11 из 15 | `cinematic` только с роликом/3D по задаче; эффекты из списка блока; `never` | `webgl_idle_dc` C |
| плавная прокрутка без сцен | K3 4 из 17 | `page.scroll.smooth: false` (L0–L1), `never` | `smooth_scroll` C |
| свой курсор, магнит, бегущая строка | K3 по 2 из 15 | `never`; строка — `loop.speed_px_s` ≤ 60 и пауза | EG-A11Y-19 (K) |
| длительности 0.35 / 0.45 / 0.65 s | K3 — вне шкалы в 12 из 15 (E) | `duration.token` или `share` | MS-07 |
| H1 из opacity 0, split на LCP | генераторы (E/01) | `page.lcp`, `lcp: is-lcp` | MS-09; EG-PERF-07 |
| скраб-фильм прокрутки на каждом сайте | higgsfield: «animated website» по умолчанию (wow-catalog A4) | один фирменный приём по концепции: `signature_sections` ≤ 2 на L1 | TR-06 |
| прилагательные вместо чисел, забытый выход и reduce у JS-анимаций | Claude (наблюдение I в примерах site v0; E «reduce только в CSS при JS-анимациях») | `exit`, `reduce` у каждого момента, `gsap.matchMedia` (G) | `spec_check` схема |
| «кино-hero» на заглушке | K3 без роликов (kimi 07/01 §6.2) | `cinematic` → ролик, секвенция или 3D (схема treatment v1) | схема |

Запрет смещает вероятность, но не исключает (H `08/01` §6.2): блок «чего не ставить» работает только с токенами и проверкой результата.

## 6. Предложения к пакету kimi (файлы kimi не правим)

### 6.1. Уровни

`../../kimi-research/07-brief-handoff/01-from-app-description-to-brief.md` §6.2 (`subtle` — лендинг по умолчанию): для маркетинговой страницы
`decisions.motion.level` — проекция уровня амбиций (E П11, A `maps_to.kimi`): L0 → `subtle`, L1 → `expressive`, L2 → `cinematic` только с роликами
16:9 и 9:16 и постерами ai-media или рендером 3d, иначе `expressive`; сервисы → `none`. Умолчание заказчика для лендинга — L1 (решение 13)
→ `expressive` `[практика]`.

### 6.2. «Разрешённые приметы» → `k3_checks.py --allow`

- Путь: бриф site `ambition.allow.markers` и `art-direction.exclusions.k3_allow` (решения `decisions[].k3_allow`) → `--allow` в команде приёмки.
  Все 14 значений `k3_allow` реестра H входят в `ALLOW_KEYS` `k3_checks.py` 1.0 (19 ключей: warm, accent-word, serif, eyebrow, photo-hero,
  center-hero, stats, cards, gradient, glass, pill, dots, arrows, mono, numbered, marquee, chrome, caps, external) `[проверено: сверка I]`.
- Пробел: у движения в `k3_checks.py` одна примета (`marquee`); свой курсор, Lenis, прелоадер, split на LCP, появление на всех секциях не
  детектируются — предложение kimi: ключи `cursor`, `smooth-scroll`, `preloader`, `reveal-all` с детекторами из `effects_probe.py` C или
  передать эти приметы `motion_check.py` K.

### 6.3. Свойства сверх transform/opacity по уровню

T7 («animate only transform and opacity»), `ACCEPTANCE` E1 и строки `build_package.py` (`MOTION_LINE`, `MOTION_PROSE` — «Transform and opacity only»
при любом уровне): L0 — в силе; L1–L2 — `transform, opacity, clip-path, mask, filter: blur() ≤ 8 px, color, @property` в бюджете кадра и с reduce;
раскладка — никогда (E П12; impeccable «Reach past transform and opacity» `[мнение вендора]`); строку брать из `page.properties_allowed` motion-spec.

### 6.4. T7 со спецификацией

```text
// K3 · Kimi Code 2.0.2 · 2026-09-25 · [не проверено] · T7s — проход движения по MOTION.md (маркетинговая страница L1–L2)
Non-interactive run: follow your agent instructions. Add motion to the existing page exactly as MOTION.md specifies; do not change layout, copy or colors.
Read MOTION.md first. Implement only the moments listed there, each on the element marked data-moment="<moment id>" (add data-section, data-slot,
data-group, data-fx attributes as MOTION.md "Markup contract" says). Take numbers only from src/styles/tokens.css (--mm-*) or from motion/<section>.motion.json;
never invent durations.
Rules: animate only the properties MOTION.md allows for this page; never width, height, top, left, margin, padding; no "transition: all".
The LCP element named in MOTION.md never animates from opacity 0 or behind a line mask — transform (shift at most 24 px), clip-path or opacity from 0.01 only.
No scroll-jacking: never change scroll speed or direction; pinning with scrub is allowed only where MOTION.md has a scene.
Scroll ranges use the subject element named in MOTION.md; stations are positions where the anchor element is at the named viewport line.
Every moment has its reduced-motion branch (prefers-reduced-motion: reduce and html[data-motion="reduced"]) and its phone branch; loops pause
with html[data-motion="paused"]. Without scroll-driven CSS support show the final states.
Verification: python3 scripts/shot.py <url> screenshots/motion-<N> --views 1440x900,390x844; for every scene scroll to each station and read the frame;
describe in REPORT.md each moment (trigger, element, timing) and what each station frame shows. Grep: no animated layout properties, no "transition: all".
```

Отличия от T7 kimi: моменты — из файла, не из промта; свойства по уровню; subject и станции; контракт разметки; ветки reduce, `paused` и без поддержки;
проверка по станциям. Опирается на поправки E П11, П12 и опыт I/02 `[проверено: I/02 — только для исполнителя-Claude (агент I)]`.

### 6.5. Прочее

- T10 (`../../kimi-research/03-prompting/04-template-library.md`): видео `preload="metadata"` и «pause with prefers-reduced-motion» → при reduce
  **0 байт видео**: `preload="none"`, источник не назначать (`data-src`), постер (CRV-AL-01, E §4.2) `[данные: C — у Linear в reduce 76 бесконечных анимаций]`.
- T3c: предел видео 100 МБ (лимит `ReadMediaFile`) против 20 МБ шаблона `refs-README` и сборщика — брать 20 МБ, 10–20 с; выход T3c (`MOTION.md`)
  привести к полям motion-spec (класс, subject, станции, reduce, телефон), чтобы разбор K3 сравнивался со спецификацией машинно.
- `brief.yaml`: `decisions.motion.spec_ref` (путь к motion-spec) и `MOTION.md` в дереве пакета; `design_system.motion_tokens` для маркетинга —
  из `motion.marketing` (E), а не 150/240/400 мс.
- `refs/README.md`: для видео — строки `Take 00:02.0–00:07.5: …` с id моментов.

## Частые ошибки

1. Диапазон прокрутки «по секции» или «по списку», а движется элемент другой длины — сцена отстаёт от замысла (I/02: до 98 px).
2. Станции долями прогресса при шагах разной высоты; раскадровка без `check` — проверять нечего.
3. Числа, требующие замера (`--line-length`), при бюджете JS 0 — исполнитель добавит JS или угадает.
4. Спецификация только входа: нет `exit`, `interrupt`, reduce у JS-анимаций, ветки без поддержки CSS scroll-driven.
5. Длительности «на глаз» (0.35s, 0.45s) вместо токенов; стаггер 100–150 мс на 10 элементов.
6. Петля без паузы и без периода; «парение» 3–5 с у крупного объекта (полоса 2,5–6 с).
7. Видео-референс целиком без отрезков «что взять»; видео для Claude Code (не дойдёт); чужой ролик с YouTube.
8. **Ошибки нейросетей**: K3 анимирует раскладку и ставит появление на всё; Claude пишет прилагательные («плавно появляется») и CSS-селекторы
   вместо id; генератор кладёт `transition: all`; K3 по T7 без спецификации ограничен transform/opacity даже на L2 — сцены «плоские».
9. Проверка движения скриншотом: VLM видит конечный кадр; запись в паузах не видит скраб — нужен зонд станций.
10. Переход страниц 600–800 мс в многостраничнике — видят на каждом клике (E §8.3: 250–400 мс).

## Чек-лист

- [ ] CRV-MS-01 У каждого момента есть class, purpose, target (id v1), trigger, tracks, reduce; у loop — период/скорость и пауза?
- [ ] CRV-MS-02 Диапазоны scroll-linked заданы по subject того, что движется, станции — якорями?
- [ ] CRV-MS-03 Нет чисел, требующих замера геометрии, при бюджете JS 0 (`attach` вместо них)?
- [ ] CRV-MS-04 Длительности и кривые — токены `motion.marketing` или доли базы; стаггер 40–80 мс, сумма ≤ 600?
- [ ] CRV-MS-05 LCP-элемент помечен; без анимации или вход по CRV-AL-09 — transform со сдвигом ≤ 24 px, clip-path или opacity от 0,01;
  не из opacity 0, не маской строк; сцена первого экрана ≤ 1 200 мс?
- [ ] CRV-MS-06 Описаны выход (`exit`, `transition_type`) и прерывание (`interrupt`)?
- [ ] CRV-MS-07 Есть ветки reduce, телефон, `fallback.no_js`, `fallback.unsupported`; на L2 — переключатель (`data-motion`)?
- [ ] CRV-MS-08 Раскадровка: ≥ 3 станции сцены + телефон + reduce, у кадров измеримый `check`?
- [ ] CRV-MS-09 `acceptance[]` ссылается на ворота K (`gate`) или метрику с порогом?
- [ ] CRV-MS-10 Видео-референс: только для `k3` + kimi, ≤ 20 МБ, 10–20 с, отрезки take с `maps_to`, `do_not_take`, права своё/internal-only?
- [ ] CRV-MS-11 Проекции в пакет собраны скриптом (`moments`, `motion-md`, `values`), а не переписаны руками?
- [ ] CRV-MS-12 `spec_check.py spec … --plan … --overlay …` — 0 ошибок?

## Открытые вопросы и противоречия

- Как K3 читает `MOTION.md`, `stations`, контракт разметки и видео-отрезки — не проверено (K3 не запускался) → живая фаза.
- kimi внутри себя: T3c «≤ 100 МБ» против шаблона и сборщика «≤ 20 МБ» — принято 20.
- A ↔ E П11: схема treatment v0 A — «L0 → none|subtle», E и `ambition-levels.yaml` — «L0 → subtle»: страница L0 — `subtle`, секции могут быть `none`.
- G ↔ E/D: `data-motion="reduce"` против `reduced` (§1.6) — закрыто X 2026-09-25: `07/02` приведён к `reduced` (`CONTRADICTIONS.md` X-12); K принимает оба.
- `range` с длинами (`cover calc(100% - 50vh)`) и `timeline-scope` проверены в Chromium 1243 и WebKit 2359 (Playwright), не в выпущенном Safari
  и не в Firefox (нет в Playwright на машине — открытый вопрос 6 заказчику).
- Зонд станций пока в опыте I (`shoot_stations.py`), а не в `motion_check.py` K — предложение K.
- Эскизы кадров (`sketch`) без генерации — только кадры прототипа; SVG-эскизы по раскадровке не делались.

## Источники

- [S1] creative E, `../05-motion/01-motion-principles-and-access.md` — классы §1.3, 2.2.2 §3, reduce §4, бюджет §5, длительности и кривые §7, П11–П12.
- [S2] creative E, `../05-motion/02-choreography-scroll-transitions.md` — хореография §1.4, примитивы §2.2, поддержка SDA §3.1, pin §4, переходы §8, LCP §10.
- [S3] creative D/E, `../04-visual-language/marketing-tokens.json` и `.css` (`motion.marketing`, `--mm-*`, ветки reduce и `data-motion`).
- [S4] creative F, `../06-effects-catalog/effects.yaml` 0.1 — `motion.kind`, `limits`, reduce; лаборатория `lab/scroll-driven-progress`, `lab/svg-line-draw`, `_vendor/fonts`.
- [S5] creative G, `../07-stack-implementation/02-implementation-patterns.md` §2.1–2.2, §6 — режим, переключатель, модуль эффекта.
- [S6] creative H, `../08-uniqueness-anti-slop/02-uniqueness-and-variation.md` §4 — почерк генераторов; `01-cliche-policy.md` §6.2 — блок K3.
- [S7] creative B, `../02-references-moodboards/03-moodboard-and-handoff.md` §3.2, §5.1 — Take / Do not take, видео движения.
- [S8] creative C, `../../../scripts/creative/scroll_record.py` и `README.md` — запись прокрутки, `--keep-video`.
- [S9] creative K, `effect-gates.yaml`, `../../../scripts/creative/motion_check.py`, `../99-raw/notes/wave3/K-notes.md` «## Для I» — ворота, метрики, контракт разметки.
- [S10] kimi, `../../kimi-research/03-prompting/04-template-library.md` — T3c, T7, T10, T0 (бан-лист).
- [S11] kimi, `../../kimi-research/07-brief-handoff/01-from-app-description-to-brief.md` §6.2; `02-task-package.md` §1–2; `03-references-brand-assets.md` §2.3, §3.
- [S12] kimi, `../../kimi-research/07-brief-handoff/templates/` (brief.yaml, DESIGN.md, ACCEPTANCE.md, refs-README.md, build_package.py) — каналы и проверки пакета.
- [S13] kimi, `../../kimi-research/99-raw/tools/k3_checks.py` 1.0 — `ALLOW_KEYS`, приметы K3.
- [S14] kimi, `../../kimi-research/05-reviews-practice/03-default-look-k3.md` — почерк K3 (через H).
- [S15] site, `../../site-research/10-playbooks-contracts/examples/*/plans/home.yaml` — планы «Отвеса», «Окошка», «Сталькона».
- [S16] higgsfield-ai/skills `wow-catalog.md` — контракты реализации, скраб по умолчанию `[мнение вендора]`.
- [S17] oso95/scroll-world `SKILL.md` (71cc36d, 2026-07-28) — камера и телефон «ALWAYS ask», `scroll` и `linger` на секцию, шов без смены знака скорости `[мнение вендора]`.
- [S18] Nutlope/hallmark `hero-enrichment.md` — одна оркестрованная сцена, Output stamp `[мнение вендора]`.
- [S19] Дайджест Dogstudio `[V:Ulgy6xIrdPg]` — advanced wireframe 14:57, прототип 11:31, «no hijack» 14:36.
- [S20] Дайджест Andy Clarke `[V:5MMm5DUjh78]` — раскадровка по размерам экрана 34:51, 37:59.
- [S21] Дайджест Тактаров `[V:Ug_dwJa07Os]` — автомат входа и выхода 27:49–31:54, `time | spring`.
- [S22] Дайджест Val Head `[V:OqvQhZ0bTYY]` — прилагательные → приёмы 37:11–39:46.
- [S23] Дайджест Bramus `[V:QA5f2loqtM4]` — хореография долями 27:30.
- [S24] Дайджест Cassie Evans `[V:v5oxrZWAq78]` — exit / entrance / persistent 18:41, FLIP 24:51.
- [S25] Дайджест Paquet `[V:J6aNMFZogyk]` — функция движения 04:14, прототип рядом с макетом 24:43.
- [S26] Дайджест `[V:7nEvk6nFeS4]` — R&D до обещания 05:20.
- [S27] Опыт I/02 — `../99-raw/experiments/I/02-spec-sufficiency/README.md`; результаты — раздел 3 этого файла.
- [S28] Опыт I/01 — `../99-raw/experiments/I/01-schemas/README.md` (проверки и проекции).
