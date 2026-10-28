# Библиотеки движения, копипаст-киты анимированных компонентов и своды правил движения: источник приёмов, а не кода

2026-10-28 · источников 53: npm, bundlephobia, jsDelivr и репозитории 23 библиотек и наборов; файлы лицензий, `package.json` и
каталоги 13 копипаст-китов; 11 сводов правил движения; условия и тарифы 4 генераторов; robots.txt и условия 26 площадок · сеть —
WebSearch и WebFetch, обычный доступ: закрытое помечено «не проверено» · свой замер веса не делался. Паспорта площадок —
группы `motion-kits`, `motion-rules`, `motion-generators` и записи `animista`, `uiverse`, `motion-dev-examples` группы `effects-code`
в `sources.yaml`.

Границы: стек и его записи — `../07-stack-implementation/` (`stack.yaml`, `01-stack-choice.md`); эффекты — `../06-effects-catalog/`;
клише и политика «приём или клише» — `../08-uniqueness-anti-slop/`; нормы движения страницы — `../05-motion/`, приложения —
`../../ui/08-motion/`; свой набор движения (примитивы, их разметка и запуск на холсте) — `../11-motion-code/`; что исполняет холст —
`../../claude-design/05-design-artifacts/03-what-canvas-runs.md`; мудборд и роль `motion` — `03-moodboard-and-handoff.md`.

## Выжимка для агента

1. **Библиотека, кит и свод — источник приёма, а не кода**: идея становится `effect:<id>` каталога и примитивом набора
   (`../11-motion-code/primitives.yaml`, значение `data-mk`), числа — токенами `motion.marketing`; в код сайта библиотека
   попадает только записью `stack.yaml` по лестнице стоимости. → §1, §6 `[практика]`
2. **Холст чужого кода движения не исполняет по правилам типа**: сети нет, кроме шрифтов и загрузок, интерфейс скриптом не строят,
   чужой бандл файлом не кладут; разбивку текста, печать и частицы библиотек на холсте заменяет разметка и код набора; переходы
   страниц и плавную прокрутку показывают прототипом вне холста. → §1 `[документация]`
3. **Разбивка и печать текста**: Splitting 1.1.0 (2024-05-31) и SplitType 0.3.4 (2023-10-22) строят разметку и `aria` не ставят;
   typed.js 3.0.0 и TypeIt — GPL-3.0 с платной коммерческой лицензией → не брать; у Splitting берём идею индекса `--char-index`
   как CSS-переменной. → §2.1 `[исходник]` `[документация]`
4. **Появление при прокрутке**: AOS (2018), ScrollReveal (GPL-3.0 + коммерческая, 2021), sal.js (2021) — одно появление на каждый
   блок, reduce ни у одной нет → не брать; система появления — IntersectionObserver и CSS `view()` по ролям. → §2.2 `[исходник]`
5. **Переходы и прокрутка — позиции стека в силе**: Barba 2.10.3 — наследие, Swup 4.10.0 — по условию (`native: true` поверх View
   Transitions, плагин доступности с `respectReducedMotion`), Locomotive 5.0.1 — обёртка над Lenis 1.3.17 без учёта reduce →
   Lenis напрямую. → §2.3 `[документация]` `[исходник]`
6. **Твины и пружины**: Popmotion (2022) и Velocity (2018, бета 2020) заморожены, react-spring живой, но только для React →
   пружина в CSS — `linear()`, твин — WAAPI или `motion/mini`; AutoAnimate 0.10.0 живой и учитывает reduce сам — идея FLIP для
   списков, на сайте — View Transitions. → §2.4 `[документация]`
7. **SVG и псевдо-3D**: Vivus (2021), mo.js (2023, 30 КБ) и Zdog (2022, «бета») строят разметку и не обновляются → линия —
   `effect:svg-line-draw` на CSS, частицы и объём — свой движок WebGL2. → §2.5 `[исходник]`
8. **CSS-наборы**: Open Props — кривые и пружины на `linear()` как переменные: сверка с токенами, а не зависимость;
   tailwindcss-animate устарел, tw-animate-css — только в коде на Tailwind v4; Animate.css — пакет npm под MIT, ветка `main` под
   Hippocratic-2.1; их бесконечные «сигналы внимания» — приметы. → §2.6 `[исходник]`
9. **Копипаст-киты — React 19 + Tailwind v4 + `motion/react`, раздача через реестр shadcn**; лицензии разные: MIT (Magic UI,
   Animata, Cult UI, Eldora UI, Kokonut UI, Motion Primitives), MIT + Commons Clause с запретом портов (React Bits, Animate UI),
   своя без MIT (Aceternity UI), атрибуция обязательна (Skiper UI). → §3.1 `[документация]`
10. **Кит — главный источник «дефолтного вида» ИИ-сайтов**: аврора, стекло, частицы, бегущая строка, орбита, бенто, мокап
    устройства, split, свой курсор, магнит — записи реестра клише; один и тот же приём лежит в 4–8 китах сразу. → §3.2 `[данные]`
11. **Приметы китов вне реестра** — метеоры, лучи фоном, мерцающая сетка, луч по рамке и вечный блеск кнопки, карточка-прожектор,
    печать и смена слова в заголовке, док, конфетти: до записи в реестре — признаки насыщения по
    `../08-uniqueness-anti-slop/01-cliche-policy.md` §2.3. → §3.2 `[данные]`
12. **Своды сходятся с нормами базы** — вход тормозит, выход короче, только `transform` и `opacity`, интерфейс короче 300 мс,
    частое не анимируют, порядок Vercel «CSS → WAAPI → библиотека» — та же лестница стоимости; нового для базы — трансформ SVG
    на обёртке `<g>` (Vercel), запрет старта с `scale(0)` (Emil Kowalski), список Reduce Motion Apple. → §4.1–4.2 `[система]`
    `[мнение вендора]`
13. **Своды спорят о перелёте и о reduce**: Carbon запрещает перелёт, M3 Expressive его требует; Atlassian и
    `@fluentui/react-motion` при reduce выключают движение, база — сокращает; спор решает поверхность (страница или приложение) и норма базы, а не усреднение. → §4.3
    `[спорно]`
14. **Генератор по описанию** (Lottie Creator, Rive, Jitter) — черновик «допущением» под утверждение владельца: коммерческая
    страница из Lottie Creator — с тарифа Team, `.riv` без заставки — с Cadet; Motion AI Kit — помощник кода на Motion, а не
    генератор облика. → §5 `[документация]`
15. **Версии, лицензии и тарифы — скоропортящиеся**: сверка с npm и репозиторием на дату работы; паспорт площадки — не старше
    6 месяцев. → §1 `[практика]`

## 1. Как читать позиции и колонки

| Позиция | Что значит | Где дальше |
|---|---|---|
| **брать** | библиотека может стоять в коде сайта: запись `stack.yaml` со статусом `default` или `conditional` и условием `when`, вес — в бюджете уровня, уведомление лицензии — в бандле | `../07-stack-implementation/01-stack-choice.md` §1–§2, §9 |
| **брать идею, код — свой** | приём ценен, библиотека — нет (вес, лицензия, заброшена, строит разметку, тянет React): приём делается эффектом каталога или примитивом набора | `../06-effects-catalog/effects.yaml`; `../11-motion-code/` |
| **не брать** | ни кода, ни идеи как умолчания: пакет устарел или приём — примета «дефолтного вида»; ставить его по памяти — ошибка | `../07-stack-implementation/01-stack-choice.md` §7 |

- **Холст.** Правила типа Design: сети нет, кроме шрифтов Google и загрузок; интерфейс, построенный скриптом (`innerHTML`,
  `appendChild`), запрещён; чужой бандл файлом холста не кладётся (cd 05/03 §2, выжимка п. 5) `[документация]`. Переход между
  страницами и приёмы уровня страницы (плавная прокрутка) показывают прототипом вне холста (cd 05/03 §4). Колонка «Холст» говорит,
  проходит ли библиотека эти правила; приём на холсте собирает примитив набора: разметка написана заранее (текст по строкам и словам —
  тоже разметкой), движение — CSS, WAAPI или свой небольшой скрипт файлом поддержки.
- **Живость** — дата стабильной версии в npm и последнего коммита; «без релизов 12 месяцев и дольше» — признак наследия, как у Barba
  и lottie-web в `stack.yaml`.
- **Метки.** Версия, дата и лицензия — `[документация]` (npm, репозиторий, файл лицензии); «строит разметку», «reduce», «aria» —
  `[исходник]` (код дистрибутива той же версии); вес — `[данные]` (чужой замер с методом); заявление README — `[мнение вендора]`;
  позиция — выбор базы.
- **Вес** — min + gzip вместе с зависимостями без peer (bundlephobia [S2]), у CSS — размер файла без сжатия (jsDelivr [S3]). В
  `stack.yaml` — свой замер brotli минимального сценария: числа разных методов напрямую не сравнивают (Swup — 9,2 КБ gzip здесь и
  6,6 КБ br там).

## 2. Движки и библиотеки движения

Версия и дата — стабильная `latest` в npm на 2026-10-28 [S1]; активность — репозиторий [S4]; «строит разметку», «reduce», «aria» —
поиск по коду дистрибутива [S3] `[исходник]`. Библиотеки с записью в `stack.yaml` сверены с ней: расхождения — в строке.

### 2.1. Разбивка и печать текста

| Библиотека · версия | Лицензия | Вес | Без сборки · без React | Холст | Что делает наш набор | Позиция |
|---|---|---|---|---|---|---|
| Splitting.js (`splitting`) 1.1.0 · 2024-05-31; до неё 1.0.6 · 2018-10-15 | MIT | 1,8 КБ + CSS 1,8 КБ | UMD · да | нет: оборачивает слова и буквы в `span` с `--word-index`, `--char-index`; `aria` нет | `split` (`data-mk-split`: слова, строки, буквы): куски пишутся в разметке заранее, у букв — `aria-label` на заголовке и `aria-hidden` на кусках; шаг — `--i` (`../11-motion-code/02-primitives.md` §1.4) | **брать идею** (индекс как CSS-переменная, каскад через `calc()`) [S5], код — свой; пакет — не брать |
| SplitType (`split-type`) 0.3.4 · 2023-10-22 | ISC — только поле `package.json`, файла лицензии нет | 4,3 КБ | UMD, ESM · да | нет: `div` строк, слов и букв с инлайн-стилями; `aria` нет | то же | **не брать** |
| typed.js 3.0.0 · 2026-01-24 | GPL-3.0-or-later + платные Limited и Unlimited [S12]; 2.1.0 · 2023-11-08 — последняя под MIT | 3,2 КБ | UMD · да | нет: курсор `span`, свой `<style>`, текст через `innerHTML`; `aria-hidden` только у курсора, reduce нет | примитива печати нет — момент `custom`: свой печатающийся текст ≈ 1 КБ, фраза целиком в HTML и в `aria-label` (`stack.yaml#typed-js`); печать — только у «терминального» мира (`../05-motion/03-micro-motion-and-performance.md` §1.6) | **не брать** (как `stack.yaml#typed-js`) |
| TypeIt (`typeit`) 8.8.7 · 2024-10-25; последний коммит 2025-01-07 | GPL-3.0 + коммерческие $9 (один проект) и $29 (без ограничения) [S13] | 4,5 КБ | UMD · да | нет: вставляет узлы текста, курсор и `<style>`; `aria` и reduce нет | то же | **не брать** |

Сплит в коде сайта — `stack.yaml#gsap-splittext` (`aria-label`, `autoSplit`); по буквам — только короткие постеры, LCP-заголовок не
разбивают (`../06-effects-catalog/01-effects-catalog.md` §2.1) `[проверено]`.

### 2.2. Появление при прокрутке

| Библиотека · версия | Лицензия | Вес | Без сборки · без React | Холст | Что делает наш набор | Позиция |
|---|---|---|---|---|---|---|
| AOS (`aos`) 2.3.4 · 2018-10-03; `next` 3.0.0-beta.6 — того же дня | MIT | 4,7 КБ + CSS 26 КБ | UMD · да | нет: сеть; разметку не строит | система появления по ролям — `rise`, `unmask`, `sweep`, `scale-in`, один раз, контент видим без JS (`../11-motion-code/02-primitives.md` §1; `../05-motion/02-choreography-scroll-transitions.md` §2.2–2.3) | **не брать** (как `stack.yaml#aos`): reduce нет, есть только отключение по типу устройства; кривые `cubic` и `quart` в исходнике равны `quad` [S15] |
| ScrollReveal (`scrollreveal`) 4.0.9 · 2021-03-05; коммит 2023-03-18 | GPL-3.0, README сужает её до открытых и некоммерческих проектов; коммерческие $30, $100, $400 [S14]; файла лицензии нет | 5,6 КБ | UMD · да | нет: инлайн-стили, слушатель `scroll` без IntersectionObserver; reduce нет | то же | **не брать** |
| sal.js 0.8.5 · 2021-05-01 | MIT | 1,3 КБ + CSS 7,5 КБ | UMD · да | нет: сеть | `rise` и соседи по ролям; в коде сайта — свой IntersectionObserver 0,2 КБ (`stack.yaml#intersection-observer`) | **брать идею** (атрибуты и переменные `--sal-duration`, `--sal-delay`) [S16], код — свой; пакет без релизов с 2021, reduce нет |

Все три ставят одно появление на каждый блок по атрибуту — прямая дорога к `cliche:section-fade-up` (`dated`, S).

### 2.3. Переходы страниц и плавная прокрутка

| Библиотека · версия | Лицензия | Вес | Без сборки · без React | Холст | Что делает наш набор | Позиция |
|---|---|---|---|---|---|---|
| Barba.js (`@barba/core`) 2.10.3 · 2024-08-12; push 2024-12-02 | MIT | 9,9 КБ (README заявляет 7) | UMD, ESM · да | нет: переход страниц — прототипом вне холста; подменяет контейнер страницы | `page-transition` — нативные View Transitions (`effect:page-transition`; `../11-motion-code/02-primitives.md` §7) | **не брать** в новый сайт; позиция `stack.yaml#barba` (`legacy-only`) в силе; View Transitions, reduce и фокуса в ядре нет [S10] |
| Swup (`swup`) 4.10.0 · 2026-09-03; push 2026-10-27 | MIT | 9,2 КБ | UMD, ESM · да | нет: как у Barba | то же; Swup — когда между страницами живёт состояние | **брать** по `stack.yaml#swup` (`conditional`): `native: true` — анимация средствами View Transitions с 4.5.0 (2023-12-01); доступность — плагин `@swup/a11y-plugin` 5.2.1, `respectReducedMotion: true` по умолчанию [S8] |
| Locomotive Scroll (`locomotive-scroll`) 5.0.1 · 2026-01-15 | MIT (файла лицензии в пакете нет) | 8,8 КБ с Lenis | UMD · да | нет: плавная прокрутка — прототипом вне холста | плавная прокрутка — Lenis напрямую, только L2 (`stack.yaml#lenis`) | **не брать** в новый сайт; позиция `stack.yaml#locomotive-scroll` (`legacy-only`) в силе: внутри Lenis зафиксирован на 1.3.17, reduce в коде нет (README обещает «proper ARIA support»), вход CommonJS ведёт на файл, которого нет в пакете [S9] `[исходник]` |

### 2.4. Твины, пружины, смена раскладки

| Библиотека · версия | Лицензия | Вес | Без сборки · без React | Холст | Что делает наш набор | Позиция |
|---|---|---|---|---|---|---|
| AutoAnimate (`@formkit/auto-animate`) 0.10.0 · 2026-07-10 | MIT | 3,2 КБ | только ESM без импортов — грузится `<script type="module">` · да, плюс входы React, Vue, Solid и др. | нет: сеть | `state` — смена состояния в View Transition (`effect:view-transition`); в коде сайта ещё `stack.yaml#gsap-flip` | **брать идею** (анимация появления, удаления и перестановки детей одной строкой), код — свой; reduce учитывает сам [S6]; в кабинете выбор библиотеки — за код-репо, числа — токены ДС |
| react-spring (`@react-spring/web`) 10.1.2 · 2026-06-24; 11.0.0-beta.1 · 2026-10-01, только ESM | MIT | 20,3 КБ без React | нет · только React, варианта на чистом JS нет | нет | пружина в CSS — строки `linear()` (`../../ui/08-motion/03-reduced-motion-and-motion-tokens.md` §7.2); следование за указателем — сглаживание `magnet` и `tilt` (λ 7–8) | **не брать** для сайта; на React-продукте пружины даёт `stack.yaml#motion-react`; reduce — хук, выключать вручную [S7] |
| Popmotion (`popmotion`) 11.0.5 · 2022-08-15 | MIT (© Framer BV) | 6,7 КБ | UMD · да | нет | твин и пружина в коде сайта — WAAPI или `stack.yaml#motion-mini`; на холсте — момент `custom` | **не брать**: заморожен, README о преемнике молчит |
| Velocity (`velocity-animate`) 1.5.2 · 2018-07-31; бета 2.0.6 · 2020-04-10 | MIT | 16,0 КБ (бета 17,3) | UMD · да | нет | WAAPI (`stack.yaml#waapi`) | **не брать**: эпоха jQuery, v2 не вышла из беты |

### 2.5. SVG, псевдо-3D, моушн-графика

| Библиотека · версия | Лицензия | Вес | Без сборки · без React | Холст | Что делает наш набор | Позиция |
|---|---|---|---|---|---|---|
| Vivus (`vivus`) 0.4.6 · 2021-04-17 | MIT | 4,3 КБ | UMD · да | нет: заменяет фигуры на `<path>`, с опцией `file` грузит SVG и вставляет через `innerHTML` | `draw` (один раз) и `scroll-draw` (по прокрутке): `pathLength="1"`, `stroke-dashoffset` (`effect:svg-line-draw`) | **брать идею**, код — свой; пакет без релизов 5 лет, текст не рисует, reduce нет |
| mo.js (`@mojs/core`) 1.7.1 · 2023-10-06 | MIT | 30,4 КБ | UMD · да | нет: создаёт `<svg>` в `body` | вспышки в наборе нет — момент `custom` (CSS или WAAPI); частицы — свой движок WebGL2 (`../../3d/16-js-scenes/`), набор WebGL не исполняет (`../11-motion-code/02-primitives.md` §9) | **не брать**: вес, разметка скриптом [S11], релизов нет 3 года; вспышка по нажатию — только по концепции |
| Zdog (`zdog`) 1.1.3 · 2022-01-22 | MIT — только README и поле `package.json`, файла нет | 7,1 КБ | UMD · да | рисует в `<canvas>` разметки, но чужой файл холсту не кладут; режим SVG строит `<path>` | объём — свой движок WebGL2 (`../../3d/16-js-scenes/`), плоский рисунок — canvas 2D кодом артборда | **брать идею** («круглые» плоские фигуры с поворотом), код — свой; v1 — «бета», релизов нет почти 5 лет |

### 2.6. CSS-наборы анимаций и кривых, галереи

| Набор · версия | Лицензия | Вес | Без сборки · без React | Холст | Что делает наш набор | Позиция |
|---|---|---|---|---|---|---|
| Open Props (`open-props`) 1.7.23 · 2026-01-31; 2.0 в бете | MIT | easings.min.css 5,5 КБ, animations.min.css 3,4 КБ без сжатия | файл с CDN · да | файлом с CDN — нет (сеть); фрагмент, переписанный сессией, — да | опции примитивов (`--mk-dur`, `--mk-ease`) по умолчанию — токены `motion.marketing` (`--motion-marketing-*`); пружины — строки `linear()` ui 08/03 §7.2 | **брать идею**, код — свой: кривые как переменные, пружины и отскоки на `linear()`; у анимаций reduce нет [S17] |
| tailwindcss-animate 1.0.7 · 2023-08-28 | MIT | плагин сборки | нет (Tailwind ≥ 3) · да | нет | — | **не брать**: shadcn/ui считает его устаревшим (2025-03-19) и ставит tw-animate-css [S18] |
| tw-animate-css 1.4.0 · 2025-09-24 | MIT | 14,9 КБ до сборки | нет (только Tailwind v4) · да | нет | — | **брать** только в коде на Tailwind v4 и shadcn/ui (кабинет): числа — токены ДС, reduce — варианты `motion-safe:` и `motion-reduce:`; в подаче страницы — не брать [S19] |
| Animate.css 4.1.1 · 2020-09-07 | MIT у пакета npm; в ветке `main` с 2021-09-13 — Hippocratic-2.1 при той же версии [S20] | animate.min.css 71,7 КБ без сжатия | файл с CDN · да | целиком — нет; 1–2 ключевых кадра, переписанных сессией, — да | вход и выход — `entrance`, `rise`, `scale-in`, `dialog` с токенами | **брать идею** входов и выходов, код — свой; reduce у него есть (1 мс) `[исходник]`, длительность по умолчанию 1 с; брать из npm, не из `main` |
| Animista (animista.net) — генератор, бета | результат — FreeBSD License (BSD с двумя пунктами), бесплатно и для коммерции [S21] | — | CSS · да | CSS, переписанный сессией, — да | то же | **брать идею**: ключевые кадры — с токенами длительностей и кривых; при копировании — уведомление BSD |
| Uiverse (uiverse.io) — элементы сообщества | MIT (README и LICENSE зеркала uiverse-io/galaxy); сайт отдаёт агенту 403 [S22] | — | HTML + CSS или Tailwind · да | CSS, переписанный сессией, — да | — | **брать идею** с осторожностью: много неона, свечения и стекла; зеркало кода не обновляется с 2024-09-02 |

Что из наборов совпадает с базой и что — примета:

- Кривые Open Props (значения — по исходнику `src` ветки `main` [S17]) сходятся с токенами: `--ease-quint-out`
  `cubic-bezier(.23, 1, .32, 1)` — это `--motion-marketing-easing-out-strong`, `--ease-quart-in-out` `(.77, 0, .175, 1)` — кривая
  Emil Kowalski «сильнее нашей» (`../05-motion/01-motion-principles-and-access.md` §7.2), `--ease-expo-out` `(.19, 1, .22, 1)`
  близка к `--motion-marketing-easing-out-expo` `(.16, 1, .3, 1)` `[исходник]`. Имена не переносим: у страницы одна система —
  `motion.marketing`.
- Приметы в наборах — бесконечные «сигналы внимания»: у Animate.css группа attention seekers (`bounce`, `flash`, `pulse`,
  `rubberBand`, `shakeX`, `shakeY`, `headShake`, `swing`, `tada`, `wobble`, `jello`, `heartBeat`), у Open Props — `ping`, `blink`,
  `pulse` и `bounce` с `infinite`, кривые `--ease-elastic-*` и `--ease-bounce-*` [S17][S20]. Бесконечная пульсация —
  `cliche:pulsing-cta` (`dated`, S) и нарушение WCAG 2.2.2 рядом с текстом; отскок на тексте и кнопках — «датированный» приём
  (`../05-motion/01-motion-principles-and-access.md` §7.2) `[мнение вендора: Hallmark]`.
- `--animation-float` Open Props — 3 с `infinite`: период попадает в полосу 2,5–6 с, где укачивание сильнее всего
  (`../05-motion/01-motion-principles-and-access.md` §6.3) `[исследование]` → `cliche:floating-bob-loop`.

## 3. Копипаст-киты анимированных компонентов

Копипаст-кит — библиотека готовых эффектов для вставки (`../00-glossary/glossary.md`, «копипаст-кит»). Кит — референс, а не
решение: параметры эффекта задаёт арт-дирекция, у компонента меняются ≥ 2 параметра демо (`../08-uniqueness-anti-slop/01-cliche-policy.md`
§1.3, CRV-CL-07; позиция по спору X-67 — `../CONTRADICTIONS.md`).

### 3.1. Киты: лицензия, платная часть, на чём построены

| Кит | Лицензия бесплатной части | Платная часть (2026-10-28) | На чём | Раздача | Живость |
|---|---|---|---|---|---|
| Aceternity UI | своя, не MIT: в любом числе личных и коммерческих проектов, без перепродажи и без выпуска как конкурирующей библиотеки или шаблона; атрибуция не нужна; открытого репозитория нет [S23] | All-Access: 1-Year $169, Lifetime $199, Team $1 590 — блоки, шаблоны, MCP | React 18+, Tailwind v4, `motion/react`; по компоненту — three и r3f (3D Globe, Canvas Reveal Effect), tsparticles (Sparkles), simplex-noise; Aurora Background — на CSS | копипаст, реестр shadcn `@aceternity/<name>`, JSON `/api/components`, MCP через shadcn | ≈ 111 компонентов в каталоге |
| Magic UI | MIT [S24] | Pro — $199 разово; лицензия Pro — штраф 10 000 USD за каждое несанкционированное распространение | React 19, Next 15, Tailwind 4, `motion` 12, cobe (Globe), canvas-confetti, tw-animate-css | реестр shadcn `@magicui`, свой MCP `@magicuidesign/mcp` | 22 930★, push 2026-10-17; 77 компонентов |
| React Bits | MIT + Commons Clause (© 2026 David Haz): нельзя продавать, сублицензировать и распространять сами компоненты — отдельно, набором или портом; то же для инструментов и звуков [S25] | Pro: $129, $249, $349 разово; лицензия Pro запрещает обучать модели на продукте | React 19, Tailwind 4; по компоненту — `motion`, gsap, three, ogl, postprocessing, matter-js; с 2026-10-13 большинство фонов — чистый WebGL2 без зависимостей | 4 варианта кода (JS или TS × CSS или Tailwind), реестр shadcn `@react-bits`, jsrepo, MCP через shadcn | 50 509★, push 2026-10-19; ≈ 217 компонентов |
| Motion Primitives | MIT (LICENCE.md) [S26] | Pro — цена не проверена | React 18, Next 15, Tailwind 4, `motion` 11; проект помечен «бета» | свой CLI `motion-primitives` | 6 840★, push 2026-09-28; 33 компонента |
| Animata | MIT [S27] | нет | React 19, Next 16, Tailwind 4, `motion` 12, lenis | копипаст | 2 988★, push 2026-10-26; 157+ компонентов |
| Cult UI | MIT [S28] | Cult Pro закрыт с 2026-09-30, его 58 компонентов — в бесплатном реестре; платное — блоки AI SDK Agents | React 19, Next 16, Tailwind 4, `motion` 12, three, cobe, `@paper-design/shaders-react`, Rive | реестр shadcn `@cult-ui` | 6 821★, push 2026-10-14; 137 компонентов |
| Eldora UI | MIT [S29] | нет | React 19, Next 15, Tailwind 4, `motion` 12, three, r3f, ogl, cobe | реестр shadcn | 1 973★, push 2026-09-26; ≈ 46 файлов реестра |
| Kokonut UI | MIT [S30] | Pro — $159 разово | React 19, Next 16, Tailwind 4, `motion` 12 | реестр shadcn `@kokonutui` | 2 239★, push 2026-10-26; 105 компонентов |
| Animate UI | MIT + Commons Clause: в продукте можно, распространять компоненты — нельзя [S31] | не найдена | React 19, `motion` ^14, Radix, Base UI, React Aria; есть версия для Vue | реестр shadcn `@animate-ui`, npm `@animate-ui/react`, CLI, скилл | 4 722★, push 2026-10-27 |
| SmoothUI | MIT [S32] | не найдена | `motion`, Tailwind | CLI, реестр shadcn | ≈ 1 000★, коммит 2026-10-25; 181 компонент |
| Inspira UI (Vue, Nuxt) | MIT; по README — адаптация Aceternity UI с его разрешения и Magic UI [S33] | Pro — по ссылке на сайте, цена не проверена | Vue 3.5, Nuxt 4, Tailwind 4, `motion-v`, three, ogl, gsap, cobe | копипаст в духе shadcn-vue | ≈ 5 100★, коммит 2026-10-17; 187+ |
| Skiper UI | файла лицензии нет; бесплатные компоненты — с обязательной атрибуцией, Pro — без [S34] | Premium $129, Exclusive $549 разово | framer-motion, gsap | реестр shadcn `@skiper-ui/skiper<N>` | репозитория нет |
| Hover.dev | своя: без атрибуции, нельзя распространять компоненты как продукт; условия сайта запрещают автоматический доступ [S35] | Pro — $49 разово | React, Tailwind, Motion | копипаст | репозитория нет |

- **Порты.** Vue Bits — официальный порт React Bits под той же лицензией с запретом портов; порты Magic UI и Aceternity на Svelte —
  MIT [S36]. Inspira UI совпадает с React Bits по нескольким именам (Silk, Image Trail, Circular Gallery) — происхождение не
  проверено, а лицензия React Bits порты запрещает.
- **Общее у всех**: `motion` (`motion/react`) вместо пакета `framer-motion` (он остался только у Skiper UI), Tailwind v4, React 19
  (кроме Motion Primitives), установка — через пространство имён в CLI shadcn [S23]–[S35] `[документация]`. Вставка компонента в
  сайт без React — это React и `motion/react` в слое «подача», в L1 не помещается (`../07-stack-implementation/01-stack-choice.md`
  §1.2, §6.4) `[проверено]`.

### 3.2. Типичные приёмы и реестр клише

Имена — как в каталогах китов [S23]–[S35]; «у N китов» — число китов этой таблицы, где приём есть отдельным компонентом `[данные]`.
Приём в ките — первый признак насыщения (`../08-uniqueness-anti-slop/01-cliche-policy.md` §2.3).

| Приём | Имена в китах (примеры) | Реестр клише | Эффект каталога · примитив набора | Как у нас и при каком условии |
|---|---|---|---|---|
| аврора, размытые пятна | Aurora Background (Aceternity UI), Aurora, Soft Aurora (React Bits), Aurora (Inspira UI), aurora-curtain (SmoothUI); текст — Aurora Text (Magic UI, Eldora UI) | `aurora-blobs` (`saturated`, S) | `aurora-css` L1, `shader-bg` L1 · `drift` (пятна на `transform`) | только по `justify_if` записи: свет — предмет концепции, цвета бренда, пауза и reduce |
| живой градиент и шейдерные фоны | Background Gradient Animation, Wavy Background, Vortex (Aceternity UI); Silk, Plasma, Color Bends, Grainient (React Bits); moving-gradient (Animata) | `mesh-gradient-bg` (`saturated`, D) | `mesh-gradient-css` L0, `shader-bg` L1 · `drift` | поворот из бренда (`twist`), `@property` или шейдер своего движка |
| перелив, хром, тоннель | Iridescence, Liquid Chrome, Molten Metal, Hyperspeed, Light Tunnel (React Bits); Hero Liquid Metal (Cult UI); Warp Background (Magic UI); Holo Card, holographic-card (React Bits, Eldora UI) | `iridescent-holo`, `chrome-liquid-metal`, `hyperspeed-tunnel` (`saturated`, S) | `holo-shader-bg` L1 | перелив — свойство продукта, на предмете, не фоном |
| стекло | Liquid Glass (Aceternity UI), Fluid Glass, Glass Surface (React Bits), liquid-glass-card (Kokonut UI), Fluted Glass (Cult UI) — у 5 китов | `glassmorphism-panels`, `liquid-glass` (`saturated`, S); `fluted-glass` — в списке наблюдения | `glass-panel` L1 | ≤ 2 панели в зоне, плотная заливка в фолбэке |
| частицы, звёзды, искры | Sparkles, Glowing Stars (Aceternity UI), Particles (Magic UI, React Bits), Galaxy, Ballpit (React Bits), Stars, Gravity Stars (Animate UI) | `particle-swarm`, `floating-orbs` | `particles-webgl` L2 | свой движок WebGL2 (`../../3d/16-js-scenes/`), только по концепции |
| метеоры, падающие звёзды | Meteors (Aceternity UI, Magic UI, Inspira UI), Shooting Stars (Aceternity UI, Animata), Falling Stars (Inspira UI) | **нет — кандидат** | — | не ставить как фон hero |
| лучи и свет фоном | Background Beams, Lamp Effect, Spotlight (Aceternity UI); Light Rays (Magic UI, React Bits); Beams, Light Pillar (React Bits); photon-beam (Eldora UI); Grid Beam (Cult UI) | `god-rays-light` — в списке наблюдения; `neon-glow` (`dated`) | `glow-accent` L1 | свет из сцены с источником, статично; лучи без источника — **кандидат** |
| мерцающие сетки и паттерны | Flickering Grid, Animated Grid Pattern, Interactive Grid Pattern, Ripple (Magic UI); Background Boxes, Background Ripple Effect (Aceternity UI); Dot Grid, Ripple Grid (React Bits) | `synthwave-grid` (`dated`) — только ретро-сетка; мерцание — **кандидат** | — | статичный паттерн из бренда — да; мерцание и «волна» по сетке — нет |
| дизеринг и растр | Dither Shader (Aceternity UI, Inspira UI), Dither, Pixel Blast (React Bits), Hero Dithering (Cult UI), halftone-background (Kokonut UI) — у 5 китов | `dither-halftone-shader` — в списке наблюдения | `shader-bg` L1 | поворот, а не умолчание: признак «следующего умолчания» уже выполнен |
| бегущая строка | Marquee (Magic UI, Eldora UI, Animata, Inspira UI), Infinite Moving Cards (Aceternity UI), Logo Loop (React Bits), Infinite Slider (Motion Primitives), Scroll Based Velocity (Magic UI) | `marquee-strip` (`saturated`, S) | `marquee-logos` L0, `marquee-text` L1 · `marquee` | видимая пауза, 30–60 px/с, одна на страницу |
| орбита, лучи-связи, облако иконок | Orbiting Circles, Animated Beam, Icon Cloud (Magic UI); orbit-rotation, integrations (Eldora UI); animated-beam (Animata); Orbit Images (React Bits) | `logo-orbit-hero` (`saturated`, D, risk high); лучи-связи между логотипами — **кандидат** | — | интеграции — списком и фактами, не «схемой из лучей» |
| глобус и карта точками | Globe на cobe (Magic UI, Cult UI, Eldora UI, Inspira UI), 3D Globe, GitHub Globe, World Map (Aceternity UI), Dotted Map (Magic UI) | `category-rut-imagery` («глобус с дугами») | `3d-object` L1 | только как предмет концепции (карта своих маршрутов) |
| бенто | Bento Grid (Aceternity UI, Magic UI, Animata, Kokonut UI, Inspira UI), Magic Bento (React Bits) | `bento-uniform-tiles` | — | раскладка, а не движение: решение плана страницы |
| мокап устройства | Safari, iPhone, Android (Magic UI); Macbook Scroll, Container Scroll Animation (Aceternity UI); macbook-pro (Eldora UI); iPhone 17 Pro Max (Cult UI) — у 5 китов | `dashboard-in-browser-frame` (`saturated`, S) | `scroll-mask-expand` L1 · `frame-expand` | продукт — без нарисованной рамки |
| появление текста: split, размытие, подъём | Text Generate Effect (Aceternity UI); Text Animate, Blur Fade, Text Reveal (Magic UI); Split Text, Blur Text, Scroll Reveal (React Bits); Text Effect (Motion Primitives); ≈ 40 вариантов у Animata и SmoothUI | `split-text-reveal` (`saturated`, D); `section-fade-up` (`dated`, S) | `split-text-reveal` L1, `scroll-reveal-system` L1 · `split`, `rise`, `unmask` | разбивка в разметке, система по ролям, не на LCP-заголовке, ≤ 1 000 мс |
| печать и смена слова в заголовке | Typewriter Effect, Flip Words, Container Text Flip (Aceternity UI); Typing Animation, Word Rotate, Morphing Text (Magic UI); Text Type, Rotating Text (React Bits); Text Loop (Motion Primitives) — печать у 8+ китов | **нет — кандидат** (смежно `accent-word-headline`) | — | печать — только «терминальный» мир; смена слова в H1 — не ставить |
| перебор знаков | Encrypted Text (Aceternity UI), Hyper Text (Magic UI, Inspira UI), Decrypted Text, Scrambled Text (React Bits), Text Scramble (Motion Primitives) — у 7 китов | нет | `text-scramble` L1 · в наборе нет — свой код острова (`../11-motion-code/02-primitives.md` §9) | короткие подписи ≤ 24 знаков, по наведению, ширина заперта; не для фразы на русском |
| блестящий и градиентный текст | Animated Shiny Text, Animated Gradient Text (Magic UI); Shiny Text, Gradient Text (React Bits); Text Shimmer (Motion Primitives); Colourful Text (Aceternity UI) — у 7 китов | `gradient-text` (`dated`, S) | — | не брать |
| счётчик | Number Ticker (Magic UI, Inspira UI), Count Up (React Bits), Sliding Number (Motion Primitives), Rolling Number (Cult UI) — у 8 китов | нет; структура — `AIL-20` site (счётчик с нуля в HTML) | `counter-up` L0 · `count` | итоговое число в HTML, один раз, только факт с источником |
| свой курсор и след | Splash Cursor, Blob Cursor, Ghost Cursor, Image Trail, Click Spark (React Bits); Smooth Cursor, Pointer (Magic UI); Following Pointer (Aceternity UI); Fluid (Inspira UI) | `custom-cursor-follower`, `fluid-cursor-sim` (`saturated`, S) | `custom-cursor` L2, `cursor-accent` L1 · `spotlight` без замены курсора | только L2 и по концепции |
| магнит | Magnetic Button (Aceternity UI), Magnet (React Bits), Magnetic (Motion Primitives, Animate UI) | `magnetic-button` (`saturated`, D) | `magnetic-cta` L1 · `magnet` | ≤ 8 px, одна кнопка на экран |
| карточка-прожектор, свечение рамки за указателем | Card Spotlight, Glowing Effect (Aceternity UI); Magic Card, Neon Gradient Card (Magic UI); Spotlight Card, Border Glow (React Bits); Spotlight, Glow Effect (Motion Primitives) — у 4+ китов | **нет — кандидат**; Neon Gradient Card — `neon-glow` (`dated`) | `cursor-accent` (вариант `border`) L1 · `spotlight` | только `(hover: hover) and (pointer: fine)`, без автодвижения; Hallmark против следящих градиентов на SaaS-лендинге `[мнение вендора]` |
| наклон и блик карточки | 3D Card Effect, Glare Card, Wobble Card (Aceternity UI); Glare Hover (Magic UI, React Bits); Tilted Card (React Bits, Animata); Tilt (Motion Primitives) | `hover-lift-all`, если на каждой карточке | `tilt-card` L1, `light-sweep` L0 · `tilt`, `shine` | ≤ 7°, один ключевой ряд |
| луч по рамке, вечный блеск кнопки | Border Beam, Shine Border, Shimmer Button, Rainbow Button, Pulsating Button (Magic UI); Moving Border, Hover Border Gradient (Aceternity UI); Star Border, Electric Border (React Bits); Border Trail (Motion Primitives) — луч у 6 китов | **нет — кандидат**; Pulsating Button — `pulsing-cta` (`dated`, S) | `light-sweep` L0 · `shine` (разово по наведению или фокусу) | блик один раз по действию, без петли |
| док с увеличением | Floating Dock (Aceternity UI), Dock (Magic UI, React Bits, Motion Primitives), MacOS Dock (Cult UI) — у 8 китов | **нет — кандидат** | — | не на странице сайта |
| параллакс и сцены прокрутки | Hero Parallax, Parallax Scroll, Sticky Scroll Reveal, Tracing Beam (Aceternity UI); Scroll Stack (React Bits) | `parallax-everything` (`dated`) — если на каждом экране | `parallax-layers` L1, `sticky-stack` L0, `svg-line-draw` L1 · `parallax`, `stack`, `scroll-draw`, `scene` | одна сцена по концепции, CSS `view()` и `position: sticky` (`../11-motion-code/03-scroll-scenes.md`) |
| конфетти и вспышка по нажатию | Confetti, Cool Mode (Magic UI), Click Spark (React Bits), Fireworks (Animate UI), particle-button (Kokonut UI) | **нет — кандидат** | — | только наградой за действие, по концепции |

Связка с кластерами реестра: аврора, градиентный текст, бенто, орбита, мокап, пульсирующая кнопка и свечение — члены кластера
`ai-saas-2024`; курсор, магнит, split и параллакс — `studio-awwwards-kit`. Три приёма одного кластера на сцене без решения
арт-дирекции — провал (`cliche-registry.yaml#cluster_rule`).

### 3.3. Что годно как идея и через что делается у нас

- **Микровзаимодействия интерфейса** — диалог, аккордеон, раскрытие, морфинг карточки в окно (Morphing Dialog, Disclosure, Transition
  Panel у Motion Primitives; примитивы Radix у Animate UI): у страницы — `dialog`, `accordion`, `state` (`effect:dialog-entry-exit`,
  `effect:details-accordion`, `effect:view-transition`); у кабинета — компоненты ДС с токенами ui 08 (`../../ui/08-motion/02-what-to-animate-in-apps.md` §3).
- **Прогресс и одно появление** — Scroll Progress (Magic UI, Motion Primitives), In View (Motion Primitives): `progress` и `rise`
  (`effect:scroll-driven-progress`, `effect:scroll-reveal-system`).
- **Подчёркивание и выделение слова** — Text Highlighter (Magic UI), double-underline (Animata): `highlight` и `draw`
  (`effect:scroll-text-highlight`, `effect:svg-line-draw`) — один раз, на смысловом слове.
- **Раскрытие кадра, окно кадра, сравнение «до и после»** — Lens, Compare (Aceternity UI), Image Comparison (Motion Primitives):
  раскрытие — `frame-expand`, `scroll-mask` (`effect:scroll-mask-expand`, `effect:mask-reveal`), окно кадра — `dialog`
  (`effect:overlay-viewer`); сравнения «до и после» в наборе нет — момент `custom` с причиной.
- **Шейдерный фон без зависимостей** — переписанные на WebGL2 фоны React Bits (2026-10-13) подтверждают дорогу базы «свой движок,
  без библиотеки» (`../../3d/16-js-scenes/`): из кита берётся идея формы, палитра и скорость — из бренда и токенов.

## 4. Своды правил движения

Метка правила дизайн-системы — `[система]`, автора — `[мнение]`, свода для агентов — `[мнение вендора]` (`../../common/evidence.md`).
Норма базы стоит выше свода: «совпадает» — свод подтверждает норму, «расходится» — действует норма базы с её условием.

### 4.1. Дизайн-системы

| Свод | Главные правила с числами | Сокращённое движение | С нормами базы | Что база берёт |
|---|---|---|---|---|
| Material 3 Expressive (motion physics) [S37] | 6 пружин: spatial и effects × fast, default, slow, mass 1; standard — spatial ζ 0,9 при k 1400 / 700 / 300, effects ζ 1,0 при k 3800 / 1600 / 800; expressive — spatial fast ζ 0,6 k 800, default ζ 0,8 k 380, slow ζ 0,8 k 200, effects — как у standard; standard — для утилитарных и повторяющихся взаимодействий, expressive — для заметных элементов и hero; скорость по размеру: fast — переключатель, кнопка, default — нижняя панель, дровер, slow — полноэкранное; у effects перелёта нет; легаси — 16 длительностей 50–1 000 мс и кривые | в исходниках токенов нет; страницы M3 — JS-оболочка, не проверено | значения совпадают с ui 08/01 §4.3; новое — выбор скорости по размеру компонента | структура «две схемы по роли элемента» — позиция ui 08/01 §4.6; на странице — пружины только у геометрии от указателя (bounce ≤ 0,2) и без перелёта у прогресса (`../05-motion/01-motion-principles-and-access.md` §7.3) |
| Apple HIG — Motion, Accessibility [S38] | числа — только ≈ 0,2 Гц (не показывать устойчивых колебаний) и 30–60 кадров/с в играх; движение с целью, необязательное, короткое и точное; частое не анимировать; движение можно отменить; visionOS: не вращать мир, давать неподвижную рамку, крупным движущимся объектам — прозрачность | убрать автоматические и повторяющиеся анимации (зум, масштаб, периферия); пружины без отскока; движение — прямо за жестом; переходы по x, y, z — затуханием; не анимировать вход в размытие и выход из него; без элементов, исчезающих по таймеру | 0,2 Гц — `../05-motion/01-motion-principles-and-access.md` §6.3; затухание вместо перемещения — ui 08/03 §3.1; размытие — **расходится** с ui 08/03 §3.2 | список Reduce Motion — опора «reduce, not remove» (`../05-motion/01-motion-principles-and-access.md` §4.1) `[система]`; размытие — открытый вопрос |
| IBM Carbon [S39] | длительности 70 / 110 / 150 / 240 / 400 / 700 мс; productive — `(0.2, 0, 0.38, 0.9)` / `(0, 0, 0.38, 0.9)` / `(0.2, 0, 1, 0.9)` для кнопок, меню, таблиц; expressive — `(0.4, 0.14, 0.3, 1)` / `(0, 0, 0.3, 1)` / `(0.4, 0.14, 1, 1)` для открытия страницы, главной кнопки, оповещений; микровзаимодействие 90–120 мс с ease-out; без отскока; стаггер 20 мс, всё ≤ 500 мс | всегда давать альтернативу переходам состояний; упрощать на телефоне | совпадает с ui 08/01 §1–2, §8.1; стаггер 20 мс — приложения, у страницы 40–80 мс (`../05-motion/01-motion-principles-and-access.md` §7.4) | productive — кабинет; запрет отскока — рабочий интерфейс (ui 08/01 §4.6) |
| Microsoft Fluent 2 [S40] | длительности 50–500 мс (`durationNormal` 200); кривые `decelerateMax (0.1, 0.9, 0.2, 1)`, `accelerateMax (0.9, 0.1, 1, 0.2)`, `easyEase (0.33, 0, 0.67, 1)` и др.; крупному — дольше, мелкому — короче; `linear` — только вращение; смена страницы — быстрое затухание, а не сдвиг; очень крупные группы — без стаггера | настройка «без движения», без вспышек, движение в пределах элемента в фокусе, смысл — дублировать `aria-live`; в `@fluentui/react-motion` reduce по умолчанию — 1 мс | токены совпадают с ui 08/01 §1–2; правила страницы — в первоисточнике, нового числа нет; 1 мс по умолчанию — **расходится** с «reduce, not remove» | правила как `[система]` для кабинета; reduce — норма базы |
| Atlassian Design System (новая) [S41] | длительности 0 / 50 / 100 / 150 / 200 / 250 / 400 / 600 мс; взаимодействия 50–150, переходы 150–400; выход короче входа на 50 или 100 мс; что повторяют десятки раз в день — короче 150 мс; без вспышек, быстрых колебаний и движения во весь экран; фокус и объявление — в начале анимации; в `@atlaskit/tokens` 20.8.2 пружина с перелётом 2,4 % — на наведении аватара (`experimental`) | при reduce движение выключено и мгновенно | совпадает с ui 08/01 §1.1, §3.1, §8.2–8.3; пружина в токене компонента — **расходится** с ui 08/01 §4.6; выключение — **расходится** с нормой базы | «десятки раз в день → < 150 мс» — к правилу частоты ui 08/01 §3.4 `[система]` |
| Shopify Polaris [S42] | 0–500 мс шагом 50 и 5 000; `ease (0.25, 0.1, 0.25, 1)` — действия пользователя, `ease-in-out (0.42, 0, 0.58, 1)` — системные; ease-in и ease-out — «use sparingly»; `linear` — спиннеры; не анимировать всю страницу разом | в токенах и текстах нет | токены совпадают с ui 08/01 [S2]; репозиторий в архиве с 2026-09-11, Polaris React заменён Web Components, токенов движения там не найдено | ничего нового; источник — архив |

### 4.2. Авторы и своды для агентов

| Свод | Главные правила с числами | Сокращённое движение | С нормами базы | Что база берёт |
|---|---|---|---|---|
| Emil Kowalski — заметки emilkowal.ski, скиллы, курс animations.dev [S43] | интерфейс короче 300 мс (180 лучше 400); нажатие 100–160, тултип 125–200, меню 150–250, модалка и дровер 200–300 (в скилле — до 500: противоречие внутри свода); выход ≈ на 20 % быстрее; кривые `(0.23, 1, 0.32, 1)`, `(0.77, 0, 0.175, 1)`, дровер iOS `(0.32, 0.72, 0, 1)`; ease-in в интерфейсе — нет; нажатие `scale(0.97)` (0,95–0,98); никогда не с `scale(0)` — от 0,9–0,97 с `opacity: 0`; `transform-origin` от триггера; что видят 100+ раз в день и запускают с клавиатуры — без анимации; следующий тултип — без задержки; стаггер 30–80 мс; отскок 0,1–0,3 только в игривом; прерываемость — переход, а не ключевые кадры | убрать `transform` и перемещение, оставить затухание и цвет: «меньше, а не ноль» | совпадает с `../05-motion/01-motion-principles-and-access.md` §7.1–7.4 (скиллы автора там — `[мнение вендора]`) и ui 08/01 §8.5; `scale-press` 0,97 — токен `--motion-marketing-scale-press` | позиция: запрет `scale(0)`, тултипы без повторной задержки, кривая дровера — кандидаты в ui 08/02 для кабинета `[мнение]` |
| Vercel — Web Interface Guidelines, раздел Animations (MIT; последний коммит 2026-10-05) [S44] | уважать `prefers-reduced-motion`; порядок — CSS, затем WAAPI, затем JS-библиотеки; только свойства компоновщика; анимировать ради причины и следствия или осознанного «приятного момента»; кривая — по тому, что меняется; прерываемость вводом; без автозапуска, кроме беззвучных необязательных петель, дольше 5 с — пауза; верный `transform-origin`; никогда `transition: all`; трансформ SVG — на обёртке `<g>` с `transform-box: fill-box; transform-origin: center` (обход ошибки Safari) | сокращённый вариант или отключение; беззвучные петли при reduce останавливать | совпадает: порядок — лестница стоимости (`../07-stack-implementation/01-stack-choice.md` §1), 5 с — WCAG 2.2.2 (`../05-motion/01-motion-principles-and-access.md` §3), `transition: all` — ui 08/01 §9.1; нового в базе — правило SVG `<g>` | правило SVG — кандидат нормы каталога (`../06-effects-catalog/01-effects-catalog.md`, вращение обёртки, а не `<svg>`) `[мнение вендора]` |
| Hallmark 2.0.0 (правила движения — в craft.md §5, microinteractions.md, scroll-choreography.md, gates.md; файла motion.md в этой версии нет) [S45] | токены 120 / 220 / 420 мс; кривые `(0.16, 1, 0.3, 1)`, `(0.7, 0, 0.84, 0)`, `(0.65, 0, 0.35, 1)`; выход — 60–75 % входа; стаггер 30–50 мс по строкам и 60–100 мс по блокам, всё ≤ 500 мс, раз на страницу; один приём прокрутки на страницу, скраб только `linear`, текст не движется, не на hero; запреты: отскок, перелёт на состояниях интерфейса (y > 1,05), параллакс, свой курсор, петли короче 4 с, бегущая строка без паузы | глобальный блок с `!important` 0,01 мс, кроме класса `.keep-motion` (затухание 150 мс); перемещение → кроссфейд 150 мс | кривые совпадают с `motion.marketing` (`../05-motion/01-motion-principles-and-access.md` §7.2 — оттуда); ссылки базы ведут на 1.1.0 (`../../../references/external-tools.md` § Hallmark); глобальный `!important` — **расходится** (`../05-motion/01-motion-principles-and-access.md` §4.3); запрет параллакса и курсора — **расходится** с уровнями (`../01-creative-direction/ambition-levels.yaml`) | находки — сигнал второго детектора; запреты — не законы: у базы приём решает арт-дирекция |
| Impeccable 4.8.0 (62 правила детектора) [S46] | 100–150 мс — мгновенный отклик, 150–300 — смена состояния, 300–500 — раскладка, оверлей, смена вида, 500–800 — поставленный фокусный вход; выход быстрее входа; кривая `(0.16, 1, 0.3, 1)`, отскок и упругость — не по умолчанию; один поставленный момент, а не одинаковый вход на каждой секции; детектор `bounce-easing` — имена bounce, elastic, wobble и кривые с y вне [−0,1; 1,1]; правила `layout-transition` в 4.8.0 нет (снято 2026-10-07), `transition: all` детектор не ловит; масштаб картинки 1,04–1,05 при наведении — «конвенция» | у каждой анимации — свой вариант для reduce: убрать перемещение, оставить прозрачность и цвет | 500–800 и «не на каждой секции» — уже в `../05-motion/01-motion-principles-and-access.md` §7.1, §7.4; масштаб при наведении — **расходится** с `cliche:hover-lift-all` | находки — сигнал; `transition: all` и свойства раскладки ловят наши проверки (`../../common/tells.yaml#layout-property-animation`) |
| UX in Motion — 12 принципов (Issara Willenskomer; перепечатка UX Magazine 2022-07-21, первоисточник на Medium — не проверен) [S47] | Easing, Offset & Delay, Parenting, Transformation, Value Change, Masking, Overlay, Cloning, Obscuration, Parallax, Dimensionality, Dolly & Zoom; четыре роли — ожидание, непрерывность, повествование, отношения; чисел нет | нет | словарь ложится на семейства каталога: Masking — `mask-reveal`, Parallax — `parallax-layers`, Value Change — `counter-up`, Transformation — `view-transition`, Dimensionality — `card-flip-3d`, `tilt-card`, Dolly & Zoom — `scroll-mask-expand`, Offset & Delay — стаггер; роли — поле `purpose` в `motion-spec` | словарь приёмов — позиция; норм с числами нет |

### 4.3. Где своды спорят и что действует у нас

| Спор | Стороны | Что действует |
|---|---|---|
| перелёт | Carbon запрещает; M3 Expressive закладывает в spatial; Atlassian — пружина 2,4 % на наведении; Emil — 0,1–0,3 в игривом; Apple при Reduce Motion — без отскока; детекторы: Hallmark флагует y > 1,05 (ловит M3 standard spatial `(0.27, 1.06, 0.18, 1)`), Impeccable — y вне [−0,1; 1,1] | ui 08/01 §4.6 — по типу продукта; на странице — `../05-motion/01-motion-principles-and-access.md` §7.3: текст, цвет и прозрачность не пружинят, прогресс сцены — без перелёта `[спорно]` |
| reduce: сократить или выключить | сократить — база, Emil, Impeccable, Apple (затухание), Hallmark (кроссфейд); выключить — Atlassian, `@fluentui/react-motion` (1 мс), Hallmark theme.mjs (`!important` 0,01 мс), Vercel («или отключить») | «reduce, not remove» (`../05-motion/01-motion-principles-and-access.md` §4; ui 08/03 §3.1); глобальный `!important` — антипример |
| размытие при reduce | ui 08/03 §3.2 оставляет размытие (Val Head); Apple просит не анимировать вход в размытие; Emil берёт размытие маской < 20 px | открытый вопрос; до решения — размытие в reduce только статичное |
| длительности | интерфейс: Emil < 300 мс, Atlassian < 150 для частого, Carbon 70–700; страница: появление 400–700, фокусный вход 500–800 (Impeccable), появление при загрузке 0,4–0,8 с (Hallmark) | граница «страница ↔ приложение» — `../05-motion/01-motion-principles-and-access.md` §2: нормы приложений на странице — умолчание L0 |
| асимметрия выхода | Atlassian — короче на 50–100 мс; Hallmark — 60–75 %; Emil — ≈ на 20 % | страница — `easing.in` ≈ 75 % входа (`../05-motion/01-motion-principles-and-access.md` §7.2); оверлеи приложения — ui 08/01 §3.1 |
| запреты Hallmark (параллакс, свой курсор) | Hallmark — гейты; база — приём по уровню и концепции | уровни `../01-creative-direction/ambition-levels.yaml` и пять проверок реестра клише |

## 5. Генераторы анимации по описанию

Генератор отдаёт облик — движение, форму, цвет, — а облик выбирает и утверждает владелец продукта (`CLAUDE.md` §3, строка
«Визуальная»). Поэтому результат генератора — **черновик «допущением»**: его показывают владельцу рядом с вариантом из каталога
эффектов, числа движения сверяют с токенами `motion.marketing`, файл идёт в план ассетов как любой ассет
(`../../ai-media/07-vector-svg-icons/04-animated-vector.md` §5) `[практика]`.

| Генератор | Что умеет ИИ | Тариф | Права на результат | Экспорт | Агентный доступ |
|---|---|---|---|---|---|
| Lottie Creator · Motion Copilot (LottieFiles) [S48] | анимация по тексту в веб-редакторе: фигуры, текст, слои, ключевые кадры, кривые, циклы, стаггер; правка выделенного; рядом — Prompt to State Machines, Prompt to Themes, Prompt to Vector; Motion Copilot — с 2024-06-12, версия 2.0 — к 2026-07-22 | редактор бесплатный, на Free — 5 экспортов; ИИ — AI-кредиты: Individual 300 в месяц, Team 600 на место, Team+ 1 500; Individual $19,99, Team $24,99 за место в месяц при годовой оплате | условия (Last Modified 22nd August 2025): Free и Individual — только некоммерческое использование, коммерция — Team или Enterprise; об ИИ-результате и о владении сделанным в Creator — ничего; модели на файлах пользователя, по словам вендора, не обучают | dotLottie, Lottie JSON, MP4, WebM, MOV, GIF, TGS | Lottie Creator MCP — локальный мост `@lottiefiles/creator-mcp` через открытую вкладку редактора (с 2026-04-15), WebMCP; публичного API генерации нет |
| Rive — AI Agent, MCP, CLI [S49] | агент в редакторе пишет скрипты Luau, раскладки, модели данных и анимацию (с 2026-04-30 — и на Free, с почасовым лимитом); CLI собирает `.riv` из текстового описания RML | Free — экспорт `.riv` с заставкой Rive; Cadet — $9 за место в месяц при годовой оплате ($17 помесячно), без заставки; Voyager $32; Enterprise $120 — обязателен при выручке от $10 млн в год | условия от 2026-05-20: контент принадлежит пользователю (D.4); права на контент во входах и выходах ИИ — у пользователя, обучения на нём нет, выход — «как есть» (D.8) | `.riv` | MCP в десктопном редакторе (ранний доступ, `http://127.0.0.1:9791/mcp`), CLI |
| Jitter — Animate with AI, Superagents [S50] | ИИ-эффекты на пиксельных шейдерах с ручками параметров (2026-05-13); Superagents — сцены с нуля, ремикс шаблонов, версии под размеры и языки (2026-07-09) | Free — ограниченные AI-кредиты, 3 файла, 720p с водяным знаком; Pro, Max, Ultra, Enterprise; цены без скрипта страницы не видны | сами условия не прочитаны (адрес закрыт robots.txt); по справке от 2026-08-24 права на контент — у пользователя, шаблоны Jitter — и в коммерции без атрибуции `[не проверено]` по условиям | MP4, GIF, Lottie, WebM, MOV; ИИ-эффекты на шейдерах в Lottie не выводятся | Jitter MCP — бета с 2026-10-20, удалённый сервер; экспорт через MCP пока не поддержан |
| Motion AI Kit (motion.dev) [S51] | не генератор облика: контекст для агента, который пишет код на Motion (документация, переходы, исходники 510+ примеров Motion+), разбор цены анимаций в коде (Performance Doctor), CSS-пружины на `linear()`, редактор переходов; `npx motion-ai`, версия 6.0.0 — 2026-05-27 | бесплатно и без аккаунта — лучшие практики и поиск по документации (MIT); остальное — Motion+, $399 разово за разработчика | код остаётся в репозитории; условия Motion+ (2026-02-20) запрещают перераспространять исходники Motion+ отдельной библиотекой | код Motion и CSS `linear()` | MCP Motion+ со входом в настройках агента, скилл `/motion`, расширение редактора; адрес сервера в документации не назван |

- Генератор не отменяет правил стека: Lottie идёт плеером `stack.yaml#lottie-web` или `#dotlottie-web`, `.riv` — рантаймом
  `stack.yaml#rive` с `setWasmUrl` на свой домен (`../07-stack-implementation/01-stack-choice.md` §6.2) `[проверено]`; на холсте Lottie —
  рисунком в `<canvas>` разметки, `.riv` — прототипом вне холста (cd 05/03 §4); стоковая анимация вместо своей — `cliche:stock-lottie`.
- Коммерческая страница из Lottie Creator — только с тарифа Team или Enterprise заказчика; `.riv` без заставки — с Cadet: тариф и
  аккаунт — решение заказчика, как любой платный шаг (`.claude/rules/guiding.md` §6).
- Motion AI Kit к холсту не относится: он помогает коду на Motion в код-репо; его пружины `linear()` сверяют со строками ui 08/03
  §7.2, разбор цены — входной сигнал, а не ворота (ворота — `../09-ai-execution-evaluation/effect-gates.yaml`) `[мнение]`.

## 6. Как это использовать на этапах

| Этап | Что берём из библиотеки, кита или свода | Во что это превращается | Норма |
|---|---|---|---|
| `moodboard`, роль `motion` | демо библиотеки или компонента кита — референс движения, как запись сайта: что движется, от чего, сколько длится | Take — объект + свойство + число («заголовок раскрывается маской по строкам, 700 мс, шаг 60 мс»); Do not take — демо-цвета, демо-скорость, имя компонента | `03-moodboard-and-handoff.md` §3.2, §4.3; замер движения референса — `../03-live-sites-measured/03-reference-motion-probe.md` |
| карта возможностей подачи, «Креатив» и `art-direction` | приём, разрешённый уровнем | `effect:<id>` каталога (семейство, уровень, цена) и решение по пяти проверкам, если приём есть в реестре клише или в §3.2 как кандидат; концепт «Креатива» — из продукта, приём кита в нём — только с поворотом | `../06-effects-catalog/effects.yaml`; `../08-uniqueness-anti-slop/01-cliche-policy.md` §1 |
| `motion` (`motion-spec`) | идея момента | момент с `effect` и `primitive` набора; числа — токены `motion.marketing` или замер референса (`source`); `custom` — только когда нет ни эффекта, ни примитива | `../09-ai-execution-evaluation/motion-spec.schema.json`; `../05-motion/01-motion-principles-and-access.md` §7 |
| холст: макет и проход движения | ничего из чужого кода | примитивы набора и CSS, написанные сессией; переход страниц и плавная прокрутка — прототипом вне холста | `../../claude-design/05-design-artifacts/03-what-canvas-runs.md` §2–§4; `../11-motion-code/04-where-it-runs.md` §1 |
| `package` — пакет для кода | библиотеку — только если приём не делается ступенью ниже | запись `stack.yaml` со статусом `default` или `conditional`, версия на дату сборки, лицензия и уведомления в бандле | `../07-stack-implementation/01-stack-choice.md` §1, §7, §9 |

- Свод правил — не вход этапа, а проверка нормы: агент берёт числа из токенов и норм базы (`../05-motion/`, `../../ui/08-motion/`), а
  свод называет, когда норма спорна → §4.3.
- Генератор — по слову владельца продукта и на его аккаунте: черновик, показ, утверждение, затем план ассетов (§5).
- Паспорт площадки (`sources.yaml` [S53]) говорит, можно ли агенту читать сайт: у Motion Primitives robots.txt закрыт для Claude-User,
  у Hover.dev и UX in Motion условия запрещают автоматический доступ, Uiverse отдаёт 403 — только ссылки человека (`manual`).

## Частые ошибки

- Библиотека ради одного приёма, который делает CSS: AOS ради fade-up, Vivus ради линии, typed.js ради печати, Animate.css ради
  одного входа.
- Код «по памяти»: Popmotion, Velocity, AOS `next`, tailwindcss-animate в проекте на Tailwind v4, Locomotive Scroll вместо Lenis.
- Копилефт в коммерческом бандле: typed.js 3, TypeIt и ScrollReveal — GPL-3.0 с платной коммерческой лицензией; «MIT, потому что
  раньше была MIT» (typed.js 2.1.0).
- «Кит под MIT» без проверки файла: Aceternity UI — своя лицензия, React Bits и Animate UI — Commons Clause с запретом портов,
  Skiper UI — атрибуция; Animate.css из ветки `main` — Hippocratic-2.1.
- Компонент кита с демо-параметрами (`cliche:tool-preset-look`); подбор компонента агентом через MCP кита — выбор облика уходит
  модели.
- React и `motion/react` на сайте без React ради одного эффекта кита.
- Разметка, построенная скриптом, и библиотека с CDN на холсте: Splitting, typed.js, mo.js, Vivus с `file`.
- Доверие README вместо кода: Locomotive обещает ARIA — в коде её нет; из разобранных reduce сами учитывают только AutoAnimate,
  Animate.css и плагин доступности Swup.
- Правило одного свода как закон: запрет перелёта Carbon на странице кампании, перелёт M3 Expressive в админке, запреты Hallmark
  против уровней базы.
- Reduce глобальным `!important` по образцу theme.mjs Hallmark или выключение движения целиком по образцу Atlassian.
- «Почерк» китов на первом экране: метеоры за hero, лучи без источника, мерцающая сетка, луч по рамке и вечный блеск CTA.
- Генератор вместо решения: анимация Motion Copilot без утверждения владельца; Lottie Creator на Free или Individual для
  коммерческой страницы; `.riv` с заставкой Rive на сайте.

## Чек-лист

- [ ] CRV-ML-01 Версия, дата и лицензия каждой библиотеки, кита и генератора, на которые опирается решение, — из npm, репозитория или условий на дату работы, а не по памяти?
- [ ] CRV-ML-02 Приём из библиотеки или кита записан как `effect:<id>` каталога или `primitive` набора; `custom` — с причиной?
- [ ] CRV-ML-03 Библиотека в коде сайта — только с записью `stack.yaml` (`default` или `conditional`), в бюджете уровня, с уведомлением лицензии в бандле?
- [ ] CRV-ML-04 Лицензия проверена по файлу: GPL с платной коммерческой — не взята; своя или Commons Clause — без перепродажи и портов; атрибуция — выполнена?
- [ ] CRV-ML-05 На холсте нет чужого кода движения, сети и разметки, построенной скриптом; переход страниц и плавная прокрутка — прототипом вне холста?
- [ ] CRV-ML-06 У приёма кита — `cliche:<id>` или отметка «нет в реестре» с проверкой признаков насыщения; ≥ 2 параметра демо изменены?
- [ ] CRV-ML-07 Числа движения — из токенов `motion.marketing` или замера референса, а не из демо кита или чужого свода?
- [ ] CRV-ML-08 Норма свода взята по поверхности: правила приложений (Carbon, Atlassian, Fluent, Emil) — для кабинета, для страницы — нормы `../05-motion/`?
- [ ] CRV-ML-09 Reduce — «сократить», а не выключить глобально; поведение библиотеки при reduce проверено по коду?
- [ ] CRV-ML-10 Результат генератора показан владельцу «допущением»; тариф заказчика разрешает коммерческое использование и экспорт без заставки и водяного знака?
- [ ] CRV-ML-11 Площадка источника есть в `sources.yaml` с `checked_at` не старше 6 месяцев; сайт, закрытый robots.txt или условиями, — только по ссылкам человека?

## Открытые вопросы и противоречия

- **Приёмы библиотек без примитива набора**: печать текста, вспышка по нажатию, твин произвольного свойства, сравнение «до и
  после», перебор знаков — сейчас момент `custom` или свой код острова (`../11-motion-code/02-primitives.md` §9); повторится в
  проектах — кандидат в `../11-motion-code/primitives.yaml`.
- **Лицензия бесплатных компонентов Aceternity UI** — своя, по llms-full.txt; открытого репозитория нет, страница `/licence`
  описывает покупки; перенос кода компонента в сайт — с проверкой юристом заказчика `[спорно]`.
- **React Bits**: файл LICENSE (Commons Clause, запрет портов) против страницы сравнения Pro, где бесплатная часть названа MIT, —
  действует файл; совпадения имён Inspira UI с React Bits — происхождение не проверено `[спорно]`.
- **Размытие при reduce**: ui 08/03 §3.2 оставляет, Apple просит не анимировать вход в размытие и выход из него — решить при
  пересмотре ui 08/03 `[спорно]`.
- **Перелёт и детекторы**: Hallmark ловит y > 1,05 и с ним официальную кривую M3 standard spatial; Impeccable — y вне [−0,1; 1,1];
  находка — сигнал, норма — ui 08/01 §4.6 и `../05-motion/01-motion-principles-and-access.md` §7.3.
- **Atlassian**: документация (меню входит на out-bold) и пакет 20.8.2 (`popup.enter` на out-practical) расходятся; пружина в
  `avatar.hovered` — против записи ui 08/01 §4.6.
- **Не проверено**: цены Motion Primitives Pro, Jitter и курса animations.dev; условия Jitter (адрес закрыт robots.txt); страницы
  Uiverse (403); токены движения Polaris Web Components; страницы M3 (JS-оболочка) — таблица «пружина → cubic-bezier», «no longer
  maintained», правила reduce; первоисточник UX in Motion на Medium (403); Lottielab Magic Animator [S52]; адрес MCP Motion+; вход
  CommonJS Locomotive 5.0.1 — не проверено запуском.
- **Веса** — min + gzip чужого замера; для решения о бюджете — свой замер brotli по методу `stack.yaml` (`measure.size_br`).
- **robots.txt китов**: Motion Primitives закрыт для ClaudeBot и Claude-User, Animata — для ClaudeBot с `ai-train=no, use=reference`;
  агент их не обходит, страницы — по ссылке человека.

## Источники

- [S1] npm registry — `https://registry.npmjs.org/<пакет>/latest`, `/-/v1/search?text=<пакет>`, полный документ пакета; 23 пакета:
  splitting, split-type, typed.js, typeit, aos, scrollreveal, sal.js, @barba/core, swup, @swup/a11y-plugin, locomotive-scroll,
  @formkit/auto-animate, @react-spring/web, @react-spring/core, @react-spring/rafz, popmotion, velocity-animate, vivus, @mojs/core,
  zdog, open-props, tailwindcss-animate, tw-animate-css, animate.css, @carbon/motion — 2026-10-28. `[документация]`
- [S2] bundlephobia API, `https://bundlephobia.com/api/size?package=<пакет>@<версия>` — min и gzip с зависимостями без peer,
  2026-10-28. `[данные]`
- [S3] jsDelivr: листинг файлов версии `https://data.jsdelivr.com/v1/packages/npm/<пакет>@<версия>` и файлы дистрибутивов
  `https://cdn.jsdelivr.net/npm/<пакет>@<версия>/…` — поиск `aria`, `prefers-reduced-motion`, `matchMedia`, `createElement`,
  `innerHTML`, 2026-10-28. `[исходник]`
- [S4] GitHub API и страницы репозиториев (звёзды, `pushed_at`, релизы, история коммитов, файлы лицензий): shshaw/splitting,
  lukePeavey/SplitType, mattboldt/typed.js, alexmacarthur/typeit, michalsnik/aos, jlmakes/scrollreveal, mciastek/sal, barbajs/barba,
  swup/swup, locomotivemtl/locomotive-scroll, formkit/auto-animate, pmndrs/react-spring, Popmotion/popmotion, julianshapiro/velocity,
  maxwellito/vivus, mojs/mojs, metafizzy/zdog, argyleink/open-props, jamiebuilds/tailwindcss-animate, Wombosvideo/tw-animate-css,
  animate-css/animate.css — 2026-10-28.
- [S5] Splitting — https://splitting.js.org/guide.html (2026-10-28).
- [S6] AutoAnimate — https://auto-animate.formkit.com/ (2026-10-28).
- [S7] react-spring — https://www.react-spring.dev/docs/getting-started, /docs/utilities/use-reduced-motion,
  /docs/concepts/animated-elements; релизы v11.0.0-beta.0 и beta.1 на GitHub (2026-10-28).
- [S8] Swup — https://swup.js.org/options/, /getting-started/animations/, /getting-started/installation/, /plugins/a11y-plugin/;
  CHANGELOG (4.4.0, 4.5.0, 4.10.0) (2026-10-28).
- [S9] Locomotive Scroll — https://scroll.locomotive.ca/docs, релиз v5.0.1 (2026-01-15), `package.json` пакета 5.0.1 (2026-10-28).
- [S10] Barba.js — https://barba.js.org/docs/getstarted/install/, README (2026-10-28).
- [S11] mo.js — https://mojs.github.io/tutorials/getting-started.html, /api/modules/shape/ (2026-10-28).
- [S12] typed.js — README, LICENSE.txt, LIMITED_COMMERCIAL_LICENSE.md, UNLIMITED_COMMERCIAL_LICENSE.md ветки `main` (2026-10-28).
- [S13] TypeIt — https://www.typeitjs.com/, /licenses/purchase/ (2026-10-28).
- [S14] ScrollReveal — https://scrollrevealjs.org/pricing/, README и `package.json` ветки `master` (2026-10-28).
- [S15] AOS — README веток `next` и `v2`, src/sass/_easing.scss (2026-10-28).
- [S16] sal.js — README ветки `master` (2026-10-28).
- [S17] Open Props — https://open-props.style/; src/props.easing.js, src/props.animations.js ветки `main`; easings.min.css,
  animations.min.css пакета 1.7.23 (2026-10-28).
- [S18] tailwindcss-animate — index.js, README; shadcn/ui, «Tailwind v4», https://ui.shadcn.com/docs/tailwind-v4 (страница от
  2025-03-19) (2026-10-28).
- [S19] tw-animate-css — README, dist/tw-animate.css 1.4.0, релиз v1.4.0 (2026-10-28).
- [S20] Animate.css — https://animate.style/; LICENSE пакета 4.1.1 (MIT); LICENSE и `package.json` ветки `main` (Hippocratic-2.1,
  2021-09-13); список лицензий OSI https://opensource.org/licenses (2026-10-28).
- [S21] Animista — https://animista.net/license, /about, /how-to (2026-10-28).
- [S22] Uiverse — README и LICENSE https://github.com/uiverse-io/galaxy (последняя синхронизация 2024-09-02);
  https://uiverse.io/robots.txt (2026-10-28).
- [S23] Aceternity UI — https://ui.aceternity.com/licence, /pricing, /terms, /llms.txt, /llms-full.txt, /ai-recommendations,
  /components, /docs/cli, реестр `/registry/<name>.json` (2026-10-28).
- [S24] Magic UI — LICENSE.md и apps/www/package.json magicuidesign/magicui; https://magicui.design/r/registry.json, /docs/mcp;
  https://pro.magicui.design/, /license (2026-10-28).
- [S25] React Bits — LICENSE.md, `package.json`, src/constants/Categories.js DavidHDev/react-bits; https://reactbits.dev/get-started/installation,
  /get-started/mcp, /get-started/changelog; https://pro.reactbits.dev/, /license (обновлена 2026-09-11), /llms.txt (2026-10-28).
- [S26] Motion Primitives — LICENCE.md и `package.json` ibelick/motion-primitives; https://motion-primitives.com/docs, /docs/installation;
  robots.txt (2026-10-28).
- [S27] Animata — LICENSE.md и `package.json` codse/animata; https://animata.design/ (2026-10-28).
- [S28] Cult UI — LICENSE.md и apps/www/package.json nolly-studio/cult-ui; https://pro.cult-ui.com/, /pricing (2026-10-28).
- [S29] Eldora UI — LICENSE.md и apps/www/package.json karthikmudunuri/eldoraui; https://www.eldoraui.site/r/registry.json (2026-10-28).
- [S30] Kokonut UI — LICENSE и `package.json` kokonut-labs/kokonutui; https://kokonutui.com/r/registry.json; https://kokonutui.pro/ (2026-10-28).
- [S31] Animate UI — LICENSE.md, packages/react/package.json imskyleen/animate-ui; https://animate-ui.com/r/registry.json (2026-10-28).
- [S32] SmoothUI — LICENSE и packages/smoothui/package.json educlopez/smoothui; https://smoothui.dev/llms.txt (2026-10-28).
- [S33] Inspira UI — LICENSE, `package.json`, README unovue/inspira-ui; https://inspira-ui.com/llms.txt (2026-10-28).
- [S34] Skiper UI — https://skiper-ui.com/docs/quick-start, /pricing, /docs/terms-of-service (Last updated September 07, 2025) (2026-10-28).
- [S35] Hover.dev — https://www.hover.dev/license, /pricing, /terms.html (Last Updated September 16, 2023) (2026-10-28).
- [S36] Vue Bits — LICENSE.md DavidHDev/vue-bits; порты на Svelte — SikandarJODD/svelte-animations, SikandarJODD/animations (2026-10-28).
- [S37] Material 3 — androidx Compose Material3: `MotionScheme.kt`, tokens/StandardMotionTokens.kt, tokens/ExpressiveMotionTokens.kt
  (VERSION v0_14_0); material-components-android docs/theming/Motion.md; material-web tokens/versions/v0_192/_md-sys-motion.scss;
  выпуски Compose Material3 (1.4.0 — 2026-10-21); m3.material.io — JS-оболочка, не прочитана (2026-10-28). `[система]`
- [S38] Apple — Human Interface Guidelines, JSON: `…/human-interface-guidelines/motion.json` (последняя запись журнала 2025-09-09),
  `…/accessibility.json` (2025-06-09) (2026-10-28). `[система]`
- [S39] IBM Carbon — https://carbondesignsystem.com/elements/motion/overview/, /choreography/ (Last updated Aug 12, 2026);
  `@carbon/motion` 11.55.0 lib/index.js (2026-10-28). `[система]`
- [S40] Microsoft Fluent 2 — https://fluent2.microsoft.design/motion; fluentui packages/tokens/src/global/durations.ts, curves.ts;
  `@fluentui/react-motion` 9.16.5 dist/index.d.ts (2026-10-28). `[система]`
- [S41] Atlassian — https://atlassian.design/foundations/motion, /foundations/motion/applying-motion; `@atlaskit/tokens` 20.8.2
  artifacts/themes/atlassian-motion.js (2026-10-28). `[система]`
- [S42] Shopify Polaris — polaris-tokens/src/themes/base/motion.ts, `polaris.shopify.com/content/design/motion/*.mdx` в архиве
  репозитория Shopify/polaris (архив с 2026-09-11); polaris-react.shopify.com — соединение рвётся (2026-10-28). `[система]`
- [S43] Emil Kowalski — https://emilkowal.ski/ui/7-practical-animation-tips, /ui/you-dont-need-animations, /ui/great-animations,
  /ui/good-vs-great-animations, /ui/agents-with-taste; emilkowalski/skills (emil-design-eng/SKILL.md, review-animations/STANDARDS.md,
  apple-design/SKILL.md); https://animations.dev/ (2026-10-28). `[мнение]` `[мнение вендора]`
- [S44] Vercel — Web Interface Guidelines, https://vercel.com/design/guidelines; README и `command.md`
  vercel-labs/web-interface-guidelines (последний коммит 2026-10-05) (2026-10-28). `[мнение вендора]`
- [S45] Hallmark 2.0.0 — https://github.com/Nutlope/hallmark: skills/hallmark/references/craft.md §5, microinteractions.md,
  scroll-choreography.md, gates.md; scripts/theme.mjs, scripts/sloplint.mjs (2026-10-28). `[мнение вендора]`
- [S46] Impeccable 4.8.0 — https://github.com/pbakaus/impeccable: skill/reference/animate.md, craft-floor.md,
  tests/fixtures/antipatterns/motion.html, crates/core/src/checks/rules.rs; https://www.impeccable.style/docs/animate, /slop
  (2026-10-28). `[мнение вендора]`
- [S47] Willenskomer I. «Creating Usability with Motion: The UX in Motion Manifesto», перепечатка UX Magazine 2022-07-21,
  https://uxmag.com/articles/creating-usability-with-motion-the-ux-in-motion-manifesto; https://uxinmotion.com/ (2026-10-28). `[мнение]`
- [S48] LottieFiles — блог «Introducing Motion Copilot on Lottie Creator»; https://lottiefiles.com/ai; https://docs.lottiefiles.com/en/creator/13_ai-tools
  (обновлено 2026-10-08), …/motion-copilot, …/lottie-creator-mcp, …/lottie-creator-webmcp; https://lottiefiles.com/pricing;
  https://help.lottiefiles.com/lottiefiles-ai-credit; форматы экспорта; https://lottiefiles.com/page/terms-and-conditions (Last
  Modified 22nd August 2025) (2026-10-28). `[документация]`
- [S49] Rive — https://rive.app/blog/rive-ai-coding-agent-faq (2026-01-12), https://rive.app/blog/free-rive-ai-agent (2026-04-30),
  https://rive.app/docs/editor/ai-agent, https://rive.app/docs/editor/ai/mcp.md, https://rive.app/docs/cli/overview.md,
  https://rive.app/pricing, https://rive.app/docs/legal/terms-of-service (2026-05-20) (2026-10-28). `[документация]`
- [S50] Jitter — https://jitter.video/changelog/ (2026-05-13, 2026-07-09, 2026-10-14, 2026-10-20), https://jitter.video/pricing/,
  справка help.jitter.video: «Create custom effects with AI», «Animate with AI: Superagents», «Export your work», «Templates,
  ownership and licensing» (2026-08-24), «Jitter's terms and policies» (2026-08-31) (2026-10-28). `[документация]`
- [S51] Motion — https://motion.dev/docs/ai-kit, /docs/ai-kit-install, /ai-kit, /plus, /plus/terms (2026-02-20), /changelog
  (2026-10-28). `[документация]`
- [S52] Lottielab — https://docs.lottielab.com/ (экспорт; ИИ-функции не подтверждены) (2026-10-28).
- [S53] Паспорта площадок — главные страницы, robots.txt и условия 26 сайтов групп `motion-kits`, `motion-rules`,
  `motion-generators` и записей `effects-code` (`sources.yaml`, `checked_at` 2026-10-28).
