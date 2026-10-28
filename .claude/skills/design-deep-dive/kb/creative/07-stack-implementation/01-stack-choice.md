# Выбор стека подачи: платформа браузера, GSAP, Motion, Lenis, View Transitions, WebGL, Lottie и Rive, no-code, фреймворки, платформы заказчика

Волна 2 · агент G · 2026-09-24 · источников: 31 + 3 дайджеста W (целиком 24, соседи и своя база — 7) · опыты: `99-raw/experiments/G/00-registry`
(npm 47 пакетов, GitHub 20, BCD и web-features), `01-lib-cost` (33 сценария: вес br и TBT при CPU ×4), `02-st-lenis-vt`
(совместимость), `03-effect-module` (модуль эффекта) · версии на 2026-09-24: Chrome 154 / Edge 153 / Firefox 156 / Safari 27 (BCD 8.1.3); стенд — Chromium 153.0.8010.12
(Playwright 1.63), WebKit 2359; gsap 3.15.0, lenis 1.3.26, motion 13.4.3, animejs 4.5.0, three 0.186.1, ogl 1.0.11, pixi.js 8.21.0,
lottie-web 5.13.0, @lottiefiles/dotlottie-web 0.80.0, @rive-app/canvas 2.43.1, @splinetool/runtime 2.0.57, swup 4.10.0,
@barba/core 2.10.3, astro 7.3.5, next 16.3.6, vite 8.3.1, react 19.3.0. Машиночитаемо — `stack.yaml`; паттерны кода — `02-implementation-patterns.md`.

Границы: список и цена эффектов — F (`../06-effects-catalog/`); правила движения и reduce — E (`../05-motion/`); 3D-рантайм в
деталях — `../../3d/01-web-3d-landscape/03-runtime-landscape.md` и `09-web-runtime/*`; ворота страницы — site.

## Выжимка для агента

1. **Стек выбирается снизу вверх по лестнице стоимости**: CSS и HTML (0 КБ) → свой код до 1 КБ → малые библиотеки (3–8 КБ br)
   → GSAP (24–52 КБ br) → WebGL (6–120 КБ br без 3D, 108–345 с 3D) → no-code-рантаймы (42 КБ + CDN, 833 КБ). Следующая ступень
   берётся, только если эффект не делается на предыдущей → §1. [проверено]
2. **Слой «подача» по уровням** (A): JS эффектов ≤ 20 / 100 / 150–200 КБ br для L0 / L1 / L2; `gsap + ScrollTrigger + SplitText`
   (42 КБ) помещается в L1, «набор Awwwards» GSAP (52 КБ) + Lenis (5 КБ) + свой код — в L2; React ради анимации (58 КБ базово,
   94 КБ с Motion) в L1 не помещается → §1.2. [проверено]
3. **L0 — без библиотек анимации**: CSS-переходы, `@starting-style`, одно появление первого экрана, IntersectionObserver
   (0,2 КБ, TBT 0); `scroll-driven`, закрепление и плавная прокрутка на L0 запрещены уровнем (A) → §2. [проверено]
4. **L1 по умолчанию — CSS**: появление и параллакс — `animation-timeline: view()` под `@supports ((animation-timeline: scroll())
   and (animation-range: 0% 100%))`; GSAP — только если в `treatment` есть закреплённая сцена, split-заголовок, Flip или
   сюжет прокрутки, который должен работать и в Firefox → §2, §3.1. [документация: S7, S10]
5. **Scroll-driven animations не Baseline** (2026-09-24): Chrome/Edge 115+, Safari/iOS 26+, Samsung 23+; Firefox 156 — только
   Nightly. Декоративное — улучшение без фолбэка; смысловое — фолбэк IO или GSAP; `scroll-timeline-polyfill` не ставить;
   scroll-triggered (`animation-trigger`) — только Chrome 146+, поверх IO → §3.1. [документация: S7, S9, S10]
6. **GSAP 3.15.0 бесплатен целиком** (SplitText, MorphSVG, ScrollSmoother), и для коммерции; сайты, собранные ИИ, — можно;
   нельзя — no-code-конструктор анимаций, конкурирующий с Webflow, и удаление `/*! … @license … */` из бандла → §3.2, §9. [документация: S1, S2]
7. **Не вырезай уведомления лицензий** (`legalComments: 'none'`, `comments: false` — запрещено разд. III п. 3 лицензии GSAP) → §9. [документация: S1]
8. **SplitText 3.13+** — выбор по умолчанию для split-заголовков: бесплатный, ставит `aria-label` на родителя и `aria-hidden` на
   части, `autoSplit` пересплитывает после шрифтов и ресайза; `splitText` Motion — платный Motion+ (разовая оплата, пожизненное членство; установка по токену доступа) → §3.2, §3.3.
   [документация: S2, S5]
9. **Motion — для сайтов на React/Next и для точечных задач**: `motion/mini` 3,5 КБ br (WAAPI), `animate` 18,3, `scroll` +
   `inView` 20,6; `scroll()` сам уходит на ScrollTimeline, где он есть → §3.3. [проверено: G/01; документация: S5]
10. **Плавная прокрутка — только L2 и только Lenis 1.3.x** (пакет `lenis`, 4,8 КБ br, TBT 0): `anchors: true`, reduce Lenis
    соблюдает сам, с ScrollTrigger — один цикл `gsap.ticker`; не сочетать с ScrollSmoother, Locomotive и CSS `scroll-snap` → §4.
    [документация: S6; проверено: G/01, G/02]
11. **Переходы между страницами — нативные View Transitions**: same-document — Baseline с 2025-10-14 (Chrome 111, Firefox 144,
    Safari 18); cross-document `@view-transition` — Chrome 126+, Safari 18.2+, Firefox нет → только как улучшение, внутри
    `@media (prefers-reduced-motion: no-preference)` → §5. [документация: S7, S10]
12. **Библиотека переходов — только когда нужно состояние между страницами** (играющее видео, WebGL-сцена, аудио): Swup 4.10
    (`native: true` — поверх VT, плагины head и a11y) или `<ClientRouter />` на Astro; Barba 2.10.3 без релизов с 2024-08 —
    только на существующих сайтах → §5. [документация: S11–S13]
13. **Один шейдерный фон — не three.js**: `@paper-design/shaders` 5,9 КБ br или свой шейдер на OGL (10,8 КБ) / WebGL2; three — при
    3D (3d); pixi.js 8 (120 КБ, TBT 116 мс) — только 2D-сцены с тысячами спрайтов → §6.1. [проверено]
14. **Lottie: для одной-двух небольших анимаций — `lottie-web` light** (41,6 КБ br, без wasm); dotLottie (12,2 КБ + wasm 379 КБ br)
    — когда анимаций много или нужен Worker; у dotLottie рендер на главном потоке стоит ≈ 0,95 с скрипта за 3 с проигрывания при
    CPU ×4 → `DotLottieWorker`; wasm dotLottie и Rive по умолчанию — с jsDelivr/unpkg → `setWasmUrl()` на свой домен → §6.2. [проверено]
15. **Rive**: вендор советует `@rive-app/webgl2`; для сайта без Rive Text, Layouts, Scripting и Audio — `canvas-lite`
    (42,5 КБ + wasm 272 КБ br) → §6.2. [документация: S14; проверено: G/01]
16. **Spline и Unicorn Studio — не по умолчанию**: Spline-рантайм 833 КБ br; Unicorn — SDK 42 КБ br с jsDelivr, сцена с их
    CDN, свой JSON — только тариф Legend, в репозитории SDK нет лицензии, reduce не описан → §6.3. [проверено: G/01; документация: S16]
17. **Не бери**: Theatre.js (релиз 2024-05, studio AGPL), `framer-motion-3d` (снят), AOS (релиз 2018), `@studio-freight/lenis`
    (переименован), `split-type` (2023), `typed.js` 3.0.0 (GPL-3.0), `vanta` (2022), `scroll-timeline-polyfill` → §7.
    [документация: S23]
18. **Смысл страницы — в HTML сервера**: статическая сборка или SSG/SSR; клиентский SPA для маркетинговой страницы запрещён
    (ИИ-боты JS не исполняют, Яндекс рендерит JS только по бета-опции) → §8. [документация: site 07/01 §1.3, 07/02 §3]
19. **Фреймворк по умолчанию — никакого** (HTML + Vite 8) для лендинга; Astro 7 — многостраничник и острова; Next 16 — если
    сайт уже на React/Next; у наградных сайтов C медиана JS 534 КБ без фреймворка против 1 143 КБ на Next/React → §8. [данные: C]
20. **Платформа заказчика (`constraints.cms`) задаёт потолок**: Тильда — Zero-анимация и T123 без сборки; WordPress и 1С-Битрикс —
    всё, через тему/шаблон и один собранный файл; Webflow — GSAP из настроек сайта и ≤ 50 000 символов кода на платном плане;
    Framer — Motion внутри и код-компоненты; на Тильде Zero-анимация на телефоне выключена по умолчанию, в Битриксе `addJs`
    не гарантирует порядок → §10. [документация: S18–S21]
21. **Версии — из `npm view` на дату сборки, не по памяти**: three 0.186.1 вышел 2026-09-24, motion — 75 релизов за 12 мес.;
    `stack.yaml` хранит `checked_at` → §11. [проверено]

## 1. Лестница стоимости

### 1.1. Замер: вес и инициализация на пустой странице

Метод G/01: сценарий «типовая инициализация» (20 секций, ScrollTrigger на каждую, split-заголовок и т. п.) → esbuild 0.25.12 ESM,
minify, production → brotli q11; страница в Chromium 153 headless, CPU ×4, холодный кэш, 5 прогонов, медиана; TBT — long tasks
до «готово» + 3 с. Машина общая: load average 6,8–10,3 на 20 потоках — TBT завышен и шумит, сравнивать порядок, а не единицы
мс. [проверено]

| Ступень | Сценарий | br КБ | +wasm br | TBT мс, медиана [мин–макс] | Готово, мс |
|---|---|---|---|---|---|
| 0 | CSS, `@starting-style`, SDA, VT, WAAPI | 0 | — | 0 | — |
| 0 | свой IntersectionObserver-reveal | 0,2 | — | 0 [0–0] | 30 |
| малые | `motion/mini` | 3,5 | — | 0 [0–0] | 46 |
| малые | taxi 1.9.1 · lenis 1.3.26 · paper-shaders · swup 4.10 · locomotive 5 | 4,4 · 4,8 · 5,9 · 6,6 · 7,8 | — | 0 у всех | 34–74 |
| малые | barba 2.10.3 · ogl · animejs 4.5 | 9,2 · 10,8 · 12,6 | — | 0–4 | 63–69 |
| средние | motion `animate` · `scroll`+`inView` · swiper 14.2 | 18,3 · 20,6 · 17,9 | — | 0 | 38–44 |
| GSAP | ядро · +Flip · +MorphSVG | 24,3 · 31,9 · 32,1 | — | 0 · 1 [0–57] · 0 | 46–95 |
| GSAP | +ScrollTrigger (20 триггеров) | 39,7 | — | 12 [0–17] | 84 |
| GSAP | +ST +SplitText (`autoSplit`, `mask`) | 42,3 | — | 39 [37–77] | 125 |
| GSAP | +ST +ScrollSmoother · +ST +Lenis | 43,6 · 44,1 | — | 59 [11–79] · 13 [0–56] | 91–134 |
| GSAP | «набор Awwwards»: ST, SplitText, Flip, CustomEase, Observer | 52,4 | — | 49 [34–156] | 134 |
| 2D | lottie-web light · полный | 41,6 · 64,4 | — | 25 · 21 | 94–97 |
| 2D | dotLottie-web | 12,2 | 379 | 20 [13–41] | 172 |
| 2D | Rive canvas-lite · canvas | 42,5 · 49,0 | 272 · 613 | 38 · 71 | 210–231 |
| фреймворк | React 19.3 (корень + div) · + `motion/react` | 57,9 · 93,8 | — | 32 · 74 | 117–166 |
| WebGL | three 0.186 (куб, 1 кадр) · pixi 8.21 (Application + прямоугольник) | 107,7 · 119,9 | — | 49 · 116 | 144–225 |
| no-code | Unicorn SDK 2.2.14 (без сцены, с jsDelivr) · Spline runtime 2.0.57 (Application без сцены) | 42,4 · 833,4 | — | — · 82 | — · 241 |

Unicorn — вес SDK снят в памяти без запуска; TBT главной unicorn.studio 254–1 158 мс — замер 3d (`3d 01/01` §5.7).
Theatre core (30,1 КБ, TBT 20) без экспорта состояния studio падает с ошибкой — см. §7. Полная таблица — `summary.md` опыта.

Выводы:
- «Малые» (≤ 8 КБ br, TBT 0) почти бесплатны; GSAP-набор (24–52 КБ, TBT до 60 мс при CPU ×4) укладывается в бюджет L1 (TBT ≤ 300/200
  мс, A); SplitText (+≈ 27 мс) и ScrollSmoother (+≈ 47 мс) — основная цена GSAP, запускать после LCP. [проверено]
- Цена «вау» — в WebGL, wasm и фреймворке: React без единой анимации (58 КБ, TBT 32) дороже GSAP с ScrollTrigger (40 КБ, TBT 12).
  [проверено]
- Замер C на живых сайтах: JS за сессию — медиана 694 КБ сжатого; библиотеки подачи из таблицы (40–60 КБ) — 6–9 % этого
  объёма, остальное — фреймворк, приложение, аналитика [не проверено: расчёт по данным C и G/01; разбор по назначению — открытый
  вопрос].

### 1.2. Бюджет слоя «подача» по уровням

| Уровень | JS подачи, КБ br (A) | Что помещается (G/01) | Что не помещается |
|---|---|---|---|
| L0 | ≤ 20 | CSS, свой IO (0,2), `motion/mini` (3,5), Lenis запрещён уровнем | GSAP (24+), любой WebGL |
| L1 | ≤ 100 | GSAP+ST+SplitText (42) + свой код; или `motion` (18–21); paper-shaders (6) или OGL (11) для одного шейдера | React ради анимации, pixi, three без 3D-задачи |
| L2 | ≤ 150 телефон / 200 десктоп (+ JS 3D ≤ 250/350) | «набор Awwwards» (52) + Lenis (5) + свой код ≈ 30–50; three (108–158) — в слое 3D | Spline-рантайм (833) без явного исключения в `budget.overrides` |

Wasm (dotLottie 379, Rive 272–613 КБ br) — после LCP по видимости; сторонние домены до ввода L0 ≤ 1, L1–L2 ≤ 2 (site `budgets.yaml`).

## 2. Уровень × эффект → стек

Id эффектов — временные `treatment.v0` (`x-effect-ids-v0`; каталог — F). «0 JS» — нативный CSS/HTML. Запреты — по A
(`../01-creative-direction/ambition-levels.yaml`).

| effect | L0 | L1 | L2 | Фолбэк без JS / без поддержки |
|---|---|---|---|---|
| `hero-entrance-once` | CSS keyframes, `@starting-style` | то же | то же или GSAP-таймлайн сцены | конечное состояние; LCP-элемент не из `opacity: 0` |
| `split-text-reveal` | — | GSAP SplitText | SplitText + таймлайн | текст целиком |
| `kinetic-headline` | — | CSS keyframes осей вариативного шрифта | GSAP | статичный заголовок |
| `scroll-reveal-system` | одно появление через IO | CSS `view()` + IO-ветка для Firefox | GSAP `ScrollTrigger.batch` | контент видим |
| `scroll-driven-progress` | — | CSS `scroll()` | CSS `scroll()` | нет полосы |
| `parallax-layers` | — | CSS `view()` | GSAP scrub (с Lenis) | статично |
| `sticky-stack` | CSS `position: sticky` | + `view()` масштаб | GSAP pin | обычный стек |
| `pin-scrub-story` | запрещено | 1 сцена: GSAP ST `pin`+`scrub`; декоративная — CSS sticky + `view-timeline` | GSAP ST | секции подряд, конечные кадры |
| `horizontal-scroll` | запрещено | запрещено | GSAP ST pin + tween `x`, `containerAnimation` | вертикальный стек; на телефоне — лента со snap |
| `marquee-logos`, `marquee-text` | CSS keyframes + кнопка паузы | то же | GSAP-цикл, если нужна реакция на скорость | статичный ряд |
| `counter-up` | CSS `@property` + `counter()` или IO + rAF | то же | то же | итоговое число в HTML |
| `mask-reveal` | — | CSS `clip-path`/`mask` + `view()` | GSAP scrub | видимо |
| `mesh-gradient-css` | статичный градиент | `@property` + keyframes | то же | статичный градиент |
| `grain-overlay` | SVG `feTurbulence`/PNG | то же | то же | — |
| `shader-bg`, `holo-shader-bg` | запрещено (WebGL) | paper-shaders или свой GLSL на OGL/WebGL2, 1 контекст | то же; three, если есть 3D | CSS-градиент или постер |
| `video-loop-hero`, `cinemagraph` | синемаграф ≤ 300 КБ (`quiet-loop`) | `<video muted loop playsinline poster>` + пауза | то же | постер |
| `video-scrub`, `image-sequence` | — | — | canvas + GSAP ST (или прогресс ScrollTimeline) | постер |
| `3d-object`, `3d-scene` | — | предрендер, model-viewer, three hero-GLB (3d) | three + ST (+ Lenis); R3F на React | постер/видео |
| `cursor-accent`, `magnetic-cta` | — | свой pointermove + rAF или `gsap.quickTo` | то же | системное поведение |
| `custom-cursor` | — | запрещено | `gsap.quickTo`/свой damp | системный курсор |
| `view-transition` | — | same-document VT | то же | мгновенная смена |
| `page-transition` | — | cross-document `@view-transition` | + Swup 4 / Astro ClientRouter для состояния между страницами | обычная навигация |
| `smooth-scroll` | запрещено | запрещено | Lenis 1.3.x | родная прокрутка |

В ячейке — сначала левый вариант; правый — для сюжета во всех браузерах или синхронизации с WebGL. Форма, цена, калькулятор — всегда L0 (A).

## 3. Анимация и прокрутка

### 3.1. Платформа браузера: CSS, scroll-driven, scroll-triggered, WAAPI

| Возможность | Chrome/Edge | Firefox | Safari/iOS | Baseline (web-features 3.39.0) |
|---|---|---|---|---|
| `animation-timeline: scroll()/view()`, `animation-range`, `ScrollTimeline`, `ViewTimeline` | 115 | только Nightly; Android — нет | 26 | нет |
| `timeline-scope` | 116 | Nightly | 26 | нет |
| `timeline-trigger`, `animation-trigger` (scroll-triggered) | 146 (exp.) | нет | нет | нет |
| `@starting-style`, `transition-behavior` | 117 | 129 | 17.5 / 17.4 | с 2024-08-06 |
| `@property` (анимация градиентов, счётчиков) | 85 | 128 | 16.4 | с 2024-07-09 |
| `linear()` (пружины и отскоки в CSS) | 113 | 112 | 17.2 | широко с 2026-06-11 |
| WAAPI `element.animate`, `getAnimations` | 84 | 75 | 14 | широко с 2023-03-16 |
| `interpolate-size`, `calc-size` (анимация к `auto`) | 129 | нет | нет | нет |
| `requestIdleCallback` | 47 | 55 | нет (Technology Preview) | нет |

Источник: BCD 8.1.3 от 2026-09-24 и web-features 3.39.0, `99-raw/experiments/G/00-registry/support.json` [документация: S7].

Правила:
- **Проверка поддержки SDA** — `@supports ((animation-timeline: scroll()) and (animation-range: 0% 100%))`: без второй части
  пропускаются частичные реализации; декларации `animation-timeline` и `animation-range` — после шортката `animation` (иначе
  шорткат сбросит таймлайн) [документация: S10].
- **Декоративное — без фолбэка, смысловое — с фолбэком.** Если на прокрутке раскрывается текст, цифра или шаг сюжета, в
  Firefox (и при выключенном JS) содержимое обязано быть видимо в конечном состоянии; для «разыгрывания» по порогам — IO
  с набором `threshold` или GSAP [документация: S10; практика]. Carmen Ansio (CSS Day 2024) — тот же принцип `@supports` →
  «basic experience» `[V:YGxOh85VtFg 27:25]`, но полифил она допускает `[V:YGxOh85VtFg 45:09]` — против запрета Chrome 2026 [спорно;
  позиция базы — без полифила].
- **CSS SDA — дешевле по главному потоку**: таймлайны прокрутки встроены в WAAPI и CSS Animations и для `transform`/`opacity`
  могут идти вне главного потока; обработчик `scroll` получает события асинхронно и подвержен рывкам [документация: вендор браузера — S8].
  Проверка на нашей машине — открытый вопрос (опыт «SDA против JS под нагрузкой» не выполнялся).
- **Scroll-triggered (Chrome 146+)**: `timeline-trigger: --t view() …; animation-trigger: --t play-forwards play-backwards;` —
  анимация по времени после пересечения порога (не скраб). Блог Chrome называл 145, BCD — 146. Только прогрессивное
  улучшение поверх IO [документация: S7, S9].
- **Практика отстаёт от платформы**: CSS SDA — у 2 из 49 наградных сайтов, View Transitions объявлены у 1 из 49 (строка
  `startViewTransition` в бандле роутера — ещё у 15) → генератор, выбирающий CSS, отличается от «среднего Awwwards» по коду,
  но не по виду [данные: C].

### 3.2. GSAP 3.15.0

- **Статус.** Webflow купил GSAP осенью 2024; с 30.04.2025 все плагины в публичном npm `gsap`; команда Jack, Cassie, Rodrigo
  продолжает; 3.15.0 — 2026-04-13, 4 релиза за 12 мес., 28 610★; `@gsap/react` 2.1.2 [документация: S2, S3; данные: S23].
- **Когда брать**: закреплённая сцена со скрабом (`pin` + `scrub`), горизонтальная секция (`containerAnimation`), таймлайн из
  4+ шагов, split-заголовки, Flip (смена раскладки с анимацией), MorphSVG, синхронизация с WebGL и Lenis через `gsap.ticker`,
  сюжет прокрутки, который обязан работать в Firefox. [практика; данные: C — GSAP у 27 из 49 наградных, ScrollTrigger у 23]
- **Когда не брать**: одно появление, hover, бегущая строка, параллакс слоёв, полоса прогресса — это CSS (0 КБ).
- **SplitText 3.13+**: −50 % размера, `aria-label` на родителе и `aria-hidden` на частях, `autoSplit` + `onSplit()` (пересплит при
  ресайзе и загрузке шрифтов, анимации пересоздаются), `mask` для «раскрытия», `deepSlice` (ссылки и `<strong>` через строки),
  `propIndex` (`--word: 3`), standalone без ядра; удалены `position: "absolute"` и `lineThreshold` — код «по памяти» с ними
  устарел [документация: S2].
- **Новое в 3.13**: анимация к CSS-переменной `gsap.to(el, { color: 'var(--accent)' })` [документация: S2].
- **Webflow**: ядро и плагины подключаются галочками в настройках сайта (хостит Webflow); «Interactions with GSAP» —
  визуальный билдер Webflow на GSAP [документация: S2, S3].
- **Официальные скиллы `greensock/gsap-skills`** (MIT, 8 скиллов, 92,6 КБ, 2026-04-21): верны по API, очистке, `gsap.matchMedia()` с
  reduce, SplitText, производительности; **нет** Lenis (советуют `scrollerProxy`, Lenis он не нужен), VT, CSS SDA, бюджетов, «контент
  без JS», LCP; «recommend GSAP» [мнение вендора]. Исполнителю — core + scrolltrigger + performance (≈ 37 КБ) вместе с нашими
  правилами [документация: вендор — S22, прочитано целиком]. Практика студий: basement.studio — GSAP-таймлайн + ScrollTrigger в React с
  `timeline.revert()` при очистке `[V:ufHQG7fDLQc 09:13]`; «GSAP 26 KB» со слайда — ядро (наш замер 24,3 br / 26,9 gzip), с ScrollTrigger — 39,7.

### 3.3. Motion 13.4 (motion.dev), WAAPI, anime.js

- Motion (MIT, 75 стабильных релизов за 12 мес., 33 717★): `animate` в двух размерах — mini (вендор: 2,3 КБ; наш замер 3,5 br —
  WAAPI, стили HTML/SVG, зарегистрированные CSS-свойства, пружина) и hybrid (вендор 18 КБ; наш 18,3 — независимые `x/y/rotate`,
  SVG `pathLength`, JS-объекты, последовательности); `scroll()` использует ScrollTimeline, где он есть; для закрепления вендор
  советует `position: sticky` [документация: S5; проверено: G/01].
- Где Motion лучше GSAP: сайт уже на React/Next (`motion/react` ≈ +36 КБ br к React), продуктовые главные (C: Stripe, Linear,
  Vercel, Apple — React/Next + Motion, без GSAP и Lenis), микродвижение без таймлайнов [данные: C].
- Ограничения: `splitText` — только Motion+ (разовая оплата, установка по токену) → агенту недоступен; three.js и vgpu через
  `motion/three` (`threeEffect`) — «Motion+ early access», хотя код в публичном пакете 13.4.3 — поправка к `3d 01/03`
  п.25 («Motion 13 — только DOM/SVG») [документация: S5; проверено: типы пакета].
- WAAPI (`el.animate`) — 0 КБ, Baseline с 2020; для одиночных JS-анимаций без библиотек (раскрытие, счётчик, магнит).
- anime.js 4.5.0 (MIT, 12,6 КБ br, TBT 0; ветка 5.0 в бете) — живая альтернатива GSAP-ядру; своих scroll-сцен уровня
  ScrollTrigger и SplitText-аналога с aria в стеке базы не проверяли → не по умолчанию [проверено: G/01; практика].

## 4. Плавная прокрутка

- **Уровень**: только L2 (A: на L0–L1 запрещено); C — Lenis активен у 16 из 49 наградных, на телефоне не отключается
  [данные: C].
- **Lenis 1.3.26** (MIT, 2026-08-05, 15 стабильных релизов за 12 мес., 16 000★; 4,8 КБ br, TBT 0): оборачивает родную прокрутку —
  `position: sticky`, якоря и доступность работают; `respectReducedMotion: true` по умолчанию — при reduce `lerp = 1`
  (прокрутка 1:1), `scrollTo` и якоря мгновенно, настройка подхватывается без перезагрузки, `lenis.prefersReducedMotion`
  [документация: S6].
- **Умолчания Lenis, которые надо менять**: `anchors: false` → ставить `anchors: true` (README: иначе якоря блокируются во время
  прокрутки; в покое браузер прыгает к якорю сам — G/02, оба движка; `anchors: true` даёт плавный переход и `offset` под
  липкую шапку); `allowNestedScroll: false` → для модалок и списков `data-lenis-prevent` или `prevent(node)`; `autoRaf: false` →
  при GSAP — один цикл `gsap.ticker`, без GSAP — `autoRaf: true` [документация: S6; проверено: G/02].
- **Связка с ScrollTrigger и VT проверена** (Chromium 153, WebKit 26.6; 10 прогонов, 0 ошибок): `scrollY` = `lenis.scroll`,
  закреплённая сцена отрабатывает, cross-document VT идёт поверх Lenis + ScrollTrigger; после same-document VT, меняющего
  раскладку, без `ScrollTrigger.refresh()` старт закрепления устаревает в обоих движках; при reduce `lenis.prefersReducedMotion`
  = true, а `lenis.options.lerp` остаётся 0,1 — проверять признак, а не опцию [проверено].
- **Ограничения**: нет CSS `scroll-snap` (есть `lenis/snap`); Safari ≤ 60 fps (30 в энергосбережении); над iframe колесо не
  прокручивает; `position: fixed` запаздывает в Safari macOS до M1; `syncTouch` сбоит на iOS < 16 [документация: S6].
- **Пакеты**: `lenis` (не `@studio-freight/lenis` — переименован, последний 1.0.42); `lenis/react`, `lenis/vue`, сборка для Framer
  (dist-tag `framer` 1.3.25-framer); ветка 2.0 — `dev` (2.0.0-dev.5), не ставить [данные: S23].
- **Альтернативы**: GSAP ScrollSmoother (43,6 КБ с ST, TBT 59 мс — дороже; двигает контент `transform` внутри обёртки) —
  только на сайтах, уже построенных на нём; Locomotive Scroll 5 (7,8 КБ) построен на Lenis — брать Lenis напрямую.

## 5. Переходы: View Transitions и библиотеки

| Путь | Поддержка (BCD 8.1.3) | Когда |
|---|---|---|
| same-document `document.startViewTransition()` | Chrome 111, Firefox 144, Safari 18 — Baseline 2025-10-14 | смена состояния блока, фильтры, табы, раскрытие карточки (L1+) |
| типы переходов (`types`, `:active-view-transition-type`) | Chrome 125, Firefox 147, Safari 18.2 | направление «вперёд/назад» |
| `view-transition-class` | Chrome 125, Firefox 144, Safari 18.2 — Baseline 2025-10-14 | одна анимация на группу карточек |
| cross-document `@view-transition { navigation: auto }` | Chrome 126, Safari 18.2; Firefox — нет | переходы многостраничника (MPA): улучшение, без JS |
| `pageswap`/`pagereveal` | Chrome 124/123, Safari 18.2; Firefox — нет | выбрать тип перехода, проверить `e.viewTransition` |
| scoped `element.startViewTransition()`, `view-transition-group` | Chrome 147/140 (exp.) | не использовать без фолбэка |

- **Умолчание для MPA**: `@media (prefers-reduced-motion: no-preference) { @view-transition { navigation: auto; } }` +
  `view-transition-name` у 1–3 общих элементов (логотип, заголовок, обложка); Firefox и reduce получают обычную
  навигацию [документация: S10, S11].
- **Swup 4.10.0** (MIT, релиз 2026-09-03, 5 234★; 6,6 КБ br, TBT 0): «page transition library for server-rendered websites» —
  кэш, preload, история, доступность; `native: true` — анимация средствами VT; плагины head (обновляет meta и стили), a11y
  (объявление смены страницы), preload, scroll, forms. Брать, когда между страницами живёт состояние (видео, WebGL, аудио) или
  нужен переход в Firefox [документация: S12].
- **Astro 7 `<ClientRouter />`**: SPA-режим с `transition:persist`, фолбэк `animate` | `swap` | `none` для браузеров без VT, объявление
  маршрута (с astro 3.2), при reduce выключает все VT-анимации; минус — модульные скрипты исполняются один раз, эффекты
  переинициализировать на `astro:page-load`; сама Astro пишет, что ClientRouter «will increasingly become unnecessary» по мере
  развития браузеров [документация: S11].
- **Barba 2.10.3** (npm 2024-08-12, 0 релизов за 12 мес., push 2024-12-02; 9,2 КБ br): о VT ничего; C — у 4 из 49 (Webflow-студии).
  Только поддержка существующих сайтов [документация: S13; данные: C, S23].
- **SEO-условие для всех**: навигация — `<a href>` в сыром HTML, каждая страница отдаётся сервером целиком; библиотека
  перехода — только прогрессивное улучшение поверх обычной навигации [документация: site 07/01 §1.3].

## 6. Графика: WebGL, 2D-анимация, no-code

### 6.1. WebGL без 3D и с 3D

- **3D** — стек и бюджеты 3d: three r186 `WebGLRenderer` + GLTFLoader, R3F 9 + drei на React, model-viewer 4.3.1 для витрины
  с AR (`3d 01/03` §12, `09/05`) — здесь не повторяется. На 2026-09-24 вышел three 0.186.1 (патч); куб на three — 107,7 КБ br,
  TBT 49 мс [проверено].
- **Один шейдерный фон** (аврора, mesh, перелив): `@paper-design/shaders` 0.0.81 (Apache-2.0, 27 релизов за 12 мес.; 5,9 КБ br,
  TBT 0 [0–38]) или свой фрагментный шейдер на OGL 1.0.11 (Unlicense, 10,8 КБ, TBT 4; релизов нет с 2025-01) или на голом
  WebGL2 (0 КБ библиотек) [проверено].
- **pixi.js 8.21** (MIT, 14 релизов за 12 мес.; 119,9 КБ br, TBT 116 мс, «готово» 225 мс): 2D-движок для тысяч спрайтов,
  фильтров и игр; на маркетинговой странице — только если эффект и есть 2D-сцена (C: 0 из 49) [проверено: G/01; данные: C].

### 6.2. 2D-анимация: Lottie, dotLottie, Rive

| Рантайм | br КБ JS + wasm | TBT / готово | Живость | Когда |
|---|---|---|---|---|
| `lottie-web` 5.13.0 light (SVG) | 41,6 + 0 | 25 / 94 мс | последний релиз 2025-05-21, 857 открытых issues | 1–2 небольшие анимации, без wasm |
| `lottie-web` полный | 64,4 + 0 | 21 / 97 | то же | нужны выражения и canvas-рендер |
| `@lottiefiles/dotlottie-web` 0.80.0 | 12,2 + 379 | 20 / 172 | 40 релизов за 12 мес. | много анимаций, `.lottie`, темы, Worker |
| `@rive-app/canvas-lite` 2.43.1 | 42,5 + 272 | 38 / 210 | 45 релизов за 12 мес. | интерактив (state machine) без Text/Layouts/Scripting/Audio |
| `@rive-app/canvas` 2.43.1 | 49,0 + 613 | 71 / 231 | то же | Rive Text и пр., много холстов (нет лимита WebGL-контекстов) |
| `@rive-app/webgl2` 2.43.1 | не мерили | — | то же | рекомендация вендора «для большинства проектов» (Rive Renderer) |

[проверено: G/01; документация: S14, S15]

- **Главный поток при проигрывании**: dotLottie рендерит в wasm на главном потоке — скрипт ≈ 0,95 с за ≈ 3,2 с проигрывания
  (CPU ×4), `lottie-web` SVG — 0,15 с; для длинных петель dotLottie — `DotLottieWorker` (OffscreenCanvas) [проверено: G/01;
  одна тестовая анимация 200×200].
- **CDN по умолчанию**: dotLottie грузит `dotlottie-player.wasm` с jsDelivr (запас unpkg), Rive — `rive.wasm` с jsDelivr/unpkg;
  документация Rive ставит рантайм через `unpkg.com/@rive-app/webgl2@latest` → в нашей сборке `DotLottie.setWasmUrl()` и
  `RuntimeLoader.setWasmUrl()` на свой домен, версию фиксировать [документация: исходники пакетов; документация: S14, S15].
- **Лицензии**: рантаймы MIT; лицензия анимации — у каждого ассета своя (LottieFiles — противоречиво, B2) → ассет только со
  своей лицензией в паспорте визуала ai-media.
- **Доклад Прокопьева (HolyJS 2023)**: Lottie — только прогресс/проигрывание, Rive — state machine (Boolean, Trigger, Number) и
  события в код `[V:iqtCk5cY5Xs 19:29]`; память Rive на порядок меньше при сопоставимом FPS (один Pixel 7) `[V:iqtCk5cY5Xs 28:43]`;
  веса 2023 — `@rive-app/canvas` 2.7.3: 24,7 КБ gzip + `rive.wasm` 83,7 КБ `[V:iqtCk5cY5Xs 32:47]` — в 2.43.1 wasm вырос до 613 КБ br
  (canvas) / 272 (lite) [проверено] → вывод доклада «по весу Rive чуть проигрывает» сегодня сильнее; интерактивность
  появилась и у dotLottie (README 2026) [мнение вендора; данные низкой надёжности].

### 6.3. No-code-рантаймы: Spline, Unicorn Studio

- **Spline** (`@splinetool/runtime` 2.0.57, 192 релиза за 12 мес.; лицензия в npm не указана): 833,4 КБ br, TBT 82 мс уже при
  `Application` без сцены (сцена и `physics.wasm` 419 КБ — сверху, `3d 01/03` §8); экспорт кода — архивом на свой хостинг;
  анимации и события — только в экспорте Vanilla JS и React [проверено: G/01; документация: S17].
- **Unicorn Studio**: SDK «~50kb gzipped» (наш замер 49,6 gzip / 42,4 br, v2.2.14) — с `cdn.jsdelivr.net/gh/hiunicornstudio/…`; сцена —
  с серверов Unicorn, свой JSON (`data-us-project-src`) — только тариф Legend; есть `data-us-lazyload`, `-fps`, `-dpi` (1,5),
  `-disablemobile`, `-alttext`; reduce не описан; лицензии SDK в репозитории нет [документация: S16; проверено: G/01].
- **Вывод**: для генерации по умолчанию — шейдер кодом (§6.1); Spline — если заказчик приносит сцену и уровень L2 с явным
  `budget.overrides`, после LCP, с постером; Unicorn — только по решению заказчика (третьи домены, тариф, лицензия SDK).
  В выборке C: Spline, Unicorn, Pixi, dotLottie — 0 из 49 [данные: C].

### 6.4. Галереи компонентов для Claude Code (дополнение 25.09.2026 из claude-design-research)

- **Что тянет в стек** (`package.json` на GitHub, 2026-09-25): Kokonut UI и Magic UI — React 19 + Tailwind 4 + `motion` 12 (глобус
  Magic UI — `cobe`); React Bits — React 19 + Tailwind 4, по компоненту `motion`, `gsap`, `three`, `ogl`, `lenis`, `postprocessing`;
  Bklit UI (графики) — React 19 + visx + `motion`; daisyUI 5.7.46 — CSS-плагин Tailwind без JS [документация: S33].
- **Сайт без React**: вставка компонента кита — это React ≈ 58 КБ br + `motion/react` ≈ +36 (§1.1), в L1 не помещается (§1.2);
  механику переносить на ступень лестницы (CSS, WAAPI, GSAP, OGL) по формулировке ролика — «используете этот компонент как
  визуальный референс, сохранить механику… адаптировать цвета, размер и содержимое» (02:02–02:10), сначала «попросить нейросеть
  разобрать, как сделан этот конкретный компонент» (01:48–01:54) [мнение: S32]; сайт уже на React/Next — компонент допустим в бюджете.
- **Magic UI MCP** (`@magicuidesign/mcp` 2.0.0, `npx @magicuidesign/cli@latest install claude`): компонент выбирает агент — выбор
  облика уходит модели (X-67); лицензия — MIT в LICENSE.md, ISC в `package.json` [документация: S33].
- **anime.js** в ролике — для «сложного скролла» уровня Awwwards (05:35–05:44) [мнение: S32]; позиция базы прежняя — не по умолчанию
  (§3.3). **Rive** — «встроенной интеграции с нейросетями нет» (06:23): на 2026-09-25 неточно, в редакторе с 12.01.2026 есть AI Coding
  Agent (Luau-скрипты) [документация: S34]; экспорт `.riv` для сайта — с тарифа Cadet (§9).

## 7. От чего отказаться

| Пакет | Статус на 2026-09-24 | Почему | Вместо |
|---|---|---|---|
| Theatre.js (`@theatre/core`, `studio`) | 0.7.2 от 2024-05-19, push 2024-08-14; studio AGPL-3.0 | заморожен; 30,1 КБ br, TBT 20 | GSAP-таймлайн, анимация из Blender |
| `framer-motion-3d` | npm: «Package no longer supported» | снят | three + GSAP или `motion/three` (Motion+) |
| AOS 2.3.4 | релиз 2018-10-03 | мёртв; «fade-up на каждом блоке» — почерк генераторов | CSS `view()` + IO по системе E |
| `@studio-freight/lenis` | 1.0.42, deprecated | переименован | `lenis` 1.3.x |
| `split-type` 0.3.4, `splitting` 1.1.0 | 2023-10 и 2024-05 | без релизов, без aria | GSAP SplitText 3.13+ |
| `typed.js` 3.0.0 | 2026-01-24, **GPL-3.0** (2.1.0 была MIT) | копилефт в коммерческом бандле | свой «печатающийся» текст (≈ 1 КБ) с `aria-label` |
| `vanta` 0.5.24 | 2022-09 | мёртв, тянет three | paper-shaders или свой шейдер |
| `scroll-timeline-polyfill` | — | «not feature complete» (Chrome) | IO-фолбэк |
| `@motionone/dom` 10.18; Locomotive Scroll ≤ 4 | 2024-06; — | влился в `motion`; заменён v5 на Lenis | `motion`; `lenis` |
| `@bsmnt/scrollytelling` 0.3.3 | 2024-02-22, push тот же | застой; идея API (Root, Waypoint, Parallax, ImageSequenceCanvas) — взять `[V:ufHQG7fDLQc 11:14]` | GSAP ST + свой модуль (`02` §6) |

[документация: S23 (npm, GitHub API), S10; проверено: G/01]

## 8. Фреймворки, SSR и SSG — стык с SEO и GEO

- **Правило site**: H1, текст, цены, условия, CTA, навигация `<a href>`, canonical, JSON-LD и OG — в HTML ответа сервера; ИИ-боты
  OpenAI, Anthropic, Perplexity JS не исполняют (прямого заявления платформ нет — `[спорно]` у site), Яндекс рендерит JS по
  бета-опции Вебмастера → любой стек подачи — надстройка над готовым HTML (`../../site-research/07-seo-geo-performance-analytics/
  01-seo-google-yandex.md` §1.3, `02-geo-ai-search.md` §3). Текст в canvas не индексируется и не становится LCP (`3d 01/02` §6.1).
- **Выбор по типу проекта** (версии npm 2026-09-24):

| Проект | Стек | Почему | Данные |
|---|---|---|---|
| лендинг, одна-три страницы, K3 | HTML + CSS + модули JS, сборка Vite 8.3 (или без сборщика) | пакет kimi (`07/02` §8.1), 0 КБ фреймворка | у C без фреймворка — медиана JS 534 КБ за сессию (n 19) |
| многостраничник с контентом, острова эффектов | Astro 7.3 (SSG, острова, нативный или ClientRouter VT) | HTML по умолчанию, JS только у островов | Astro у 2 из 49, медиана 366 КБ (мало данных) |
| сайт уже на React/Next, продуктовая главная с приложением | Next 16.3 (SSG/SSR, `next/font`) + Motion или GSAP с `@gsap/react` | общий код с продуктом | Next/React у 17 из 49, медиана 1 143 КБ |
| Vue/Nuxt | Nuxt (SSR/SSG) + GSAP | стек заказчика | nuxt/vue 11 из 49, 865 КБ |

  [данные: C `sites.csv`, десктоп, JS сжатый за сессию; документация: S11, S23]
- **Клиентский SPA** (Vite + React без SSR/SSG) для маркетинговой страницы — запрет: пустой HTML для ботов, LCP ждёт JS.
- **Шрифты** (из D): метрический фолбэк — `next/font` (Next), `fontaine` 1.0.0 (Vite/Nuxt, 2026-09-21) или ручной `@font-face` с
  `size-adjust`/`ascent-override` по k_ru; подмножества cyrillic + latin с ₽ (`../04-visual-language/` D, CLS 0 в 8 из 8) —
  паттерн в `02` §9.

## 9. Лицензии и права

| Что | Лицензия (2026-09-24) | Условие для генератора сайтов |
|---|---|---|
| GSAP 3.15 и все плагины | Standard «No Charge» (Webflow; eff. 2025-04-30, ред. 2025-05-30) | сайты любого вида, включая коммерцию и конкурентов Webflow, — можно; код, написанный ИИ, — можно; **нельзя**: no-code-билдер анимаций, конкурирующий с Webflow, реверс для такого продукта, удаление уведомлений; Webflow может менять лицензию (без «material degradation»), прекратить за нарушение; при сомнении — «contact us» |
| `@gsap/react` | та же | то же |
| Lenis, Motion, anime.js, three, pixi, swup, barba, lottie-web, dotLottie, Rive-рантаймы, swiper | MIT | уведомление MIT в бандле (legal comments) |
| OGL | Unlicense | — |
| @paper-design/shaders, Theatre core | Apache-2.0 | NOTICE при распространении |
| Theatre studio | AGPL-3.0 | не включать |
| taxi | BSD-3-Clause | уведомление |
| typed.js 3.0.0 | GPL-3.0 | не включать |
| `@splinetool/runtime` | не указана в npm | условия Spline (ToS не читались) → только по решению заказчика |
| unicornstudio.js | файла лицензии нет в репозитории | не вендорить; только их загрузчик по решению заказчика |
| Motion+ (`splitText`, `motion/three`) | платное членство: разовая оплата, lifetime (кэш `motion.dev_docs_split-text`, 2026-09-25); установка по токену | агенту недоступно |
| React Bits — компоненты (дополнение 25.09.2026) | MIT + Commons Clause License Condition v1.0 (LICENSE.md, 2026-09-25) [документация: S33] | сайт, в том числе коммерческий, — можно; продавать, сублицензировать и распространять сами компоненты (набором, по одному, портом) — нельзя: не класть в продаваемый шаблон или кит |
| Kokonut UI, Magic UI, Bklit UI, daisyUI (дополнение 25.09.2026) | MIT (у Magic UI MCP — MIT в LICENSE.md, ISC в `package.json`) [документация: S33] | уведомление MIT |
| Rive — редактор (дополнение 25.09.2026) | Free — 3 совместных файла; экспорт `.riv` («to ship») — с Cadet, $9 за место в месяц (rive.app/pricing, 2026-09-25) [документация: S34] | рантайм MIT, но файл для сайта — с платного тарифа |

[документация: S1, S23; npm `license`, GitHub API]

- **Продукт как «конструктор»**: система, которая сама собирает сайты с GSAP, — разрешённое использование (FAQ про ИИ-инструменты);
  визуальный no-code-редактор анимаций на GSAP для пользователя — зона запрета → юрист заказчика (PLAN, вопрос 10); запасной путь —
  CSS SDA/VT + Motion/anime.js [спорно]. Уведомления: esbuild не с `legalComments: 'none'`, Terser — `comments: 'some'` [документация: S1].

## 10. Платформы заказчика (`constraints.cms`)

| `cms` | Как подключать код подачи | Сборка | GSAP и библиотеки | Потолок по уровням | Ограничения и риски |
|---|---|---|---|---|---|
| `tilda` | Zero Block: Basic (появление, параллакс, фиксация) и Step-by-step (Element/Block on Screen, **On Scroll** — скраб, Hover, Click; Move, Scale, Opacity, Rotate, Easing, Delay, Loop); свой код — блок T123 или HTML-элемент в Zero (HTML, `<script>`, `<style>`), в head сайта или страницы | нет; код исполняется только на опубликованной странице | файлом со своего домена/хостинга или инлайн в T123; npm нет; экспорт исходного кода — тариф Business | L0 — родными блоками; L1 — Zero Step-by-step + T123 (CSS SDA, IO, GSAP одним файлом); L2 — возможно, но вес и порядок скриптов Тильды не контролируются | анимация Zero на телефоне выключена по умолчанию; reduce не документирован; поддержка по своему коду не консультирует; «сторонние решения могут перестать работать… из-за нововведений Тильды»; полная коллекция блоков — с Personal (500 ₽/мес при оплате за год) |
| `wordpress` | тема или дочерняя тема / свой плагин: `wp_enqueue_script(…, ['strategy' => 'defer', 'in_footer' => true])` (с 6.3), ES-модули — `wp_enqueue_script_module()` (с 6.5, import map; `$args` с 6.9) | Vite в теме → `dist/` | npm-пакеты в сборке темы; GSAP — одним модулем | L0–L2 | конструкторы страниц (Elementor и др.) несут свой JS — вне нашего замера; кэш-плагины объединяют/отложенно грузят скрипты — проверять порядок |
| `1c-bitrix` | шаблон сайта: `Asset::getInstance()->addJs($path)` (с main 14.9.4), `addString('<script type="module" …>')`; в шаблоне компонента — `$this->addExternalJS()` | Vite вне Битрикса → файлы в `SITE_TEMPLATE_PATH` | одним собранным файлом: **addJs не гарантирует порядок** | L0–L2 | композитный кэш и «объединение JS» ядра; ядро `BX` уже весит — считать в бюджете; блоги разработчиков — `[практика]` |
| `webflow` | нативные «Interactions with GSAP»; GSAP ядро и плагины — галочками в Site settings (хостит Webflow); свой код — Site/Page settings, Code Embed | нет (свой бандл — внешним файлом) | GSAP — из настроек; прочее — внешним скриптом | L0–L2 (C: 7 из 49 наградных на Webflow, 5 — GSAP + Lenis) | **≤ 50 000 символов** своего кода на поле, **только платный план** (gsap+ST минифицированный — 111,7 КБ → только из настроек или внешним файлом) |
| `framer` | встроенные эффекты Framer (на Motion); Custom Code глобально или на странице (начало/конец head и body); код-компоненты React | нет (код-компоненты и overrides — внутри Framer) | Motion — внутри; Lenis — сборка `framer`; GSAP — в код-компоненте | L0–L2 | в холсте Custom Code не исполняется — проверять на опубликованном сайте; импорт npm через ESM-CDN и тарифы — `[не проверено]` (вторичные источники) |
| `custom` | стек проекта по §8 | по проекту | npm | L0–L2 | стек заказчика в `constraints.stack` → `build.stack` kimi |
| `static` | HTML + CSS + модули JS | Vite 8 или без сборщика | npm, самохостинг wasm | L0–L2 | — |
| `none` | выбираем сами: лендинг — `static`, многостраничник — Astro 7 | Vite / Astro | npm | L0–L2 | — |

[документация: S3, S4, S18–S21; данные: C]

Порядок решения: `constraints.cms` → потолок уровня и способ подключения → уровень страницы из `ambition` → стек эффектов по §2.
Если уровень выше потолка платформы (например, L2-сцена на Тильде без экспорта) — предупреждение в `art-direction` и выбор:
понизить уровень секции или вынести сцену в отдельную страницу на `static`.

## 11. Пакет kimi и дисциплина версий

- **Сейчас** (`kimi 07/02` §8.1, 2026-09-24): static — `vite@8`, `typescript@7`; React — `react@19`, `react-dom@19`,
  `@vitejs/plugin-react@6`, `react-router@8`; шрифты — `@fontsource/<id>@5`; 3D — `@google/model-viewer@4`, `three@0.186`;
  движение — `gsap@3` (+ `lenis@1`) только при `expressive`/`cinematic`; CDN и глобальные установки запрещены.
- **Предложения kimi** (в отчёт; файлы kimi не правим): (1) при `expressive` без pin/split/Flip/горизонтали — без GSAP (CSS SDA + IO),
  `lenis@1` — только при `cinematic` (L2; совпадает с запретом A на L1); (2) добавить в «You MAY install exactly»
  `@paper-design/shaders@0.0.81`, `lottie-web@5` или `@lottiefiles/dotlottie-web@0.80` (если дан ассет), `@rive-app/canvas-lite@2`
  (если дан `.riv`), `motion@13` (webapp на React), `swup@4`, `astro@7` (по решению site); (3) wasm — в `public/` и `setWasmUrl()`
  (иначе скрытый CDN); (4) не вырезать legal comments GSAP; (5) версии 2026-09-24: gsap 3.15.0, lenis 1.3.26, motion 13.4.3,
  three 0.186.1, vite 8.3.1, astro 7.3.5, next 16.3.6, react 19.3.0 + `npm view … dist-tags` (lenis `dev` 2.0.0-dev.5, animejs `beta`).
- **Скоропортящееся** (перепроверять раз в квартал и перед сборкой): поддержка SDA в Firefox, cross-document VT в Firefox,
  scroll-triggered в Safari/Firefox, лицензия GSAP (право Webflow менять), живость Barba и lottie-web, тарифы Webflow/Tilda/
  Unicorn — поле `checked_at` в `stack.yaml`.

## Частые ошибки

1. GSAP на странице ради одного fade-up или бегущей строки (24–40 КБ и TBT вместо 0) — K3 и генераторы повторяют наградной стек
   (C: K3 набирает L2 «за курсор и плавную прокрутку»).
2. Lenis на L0–L1 и Lenis без `anchors: true` — якоря в меню перестают работать.
3. `@studio-freight/lenis`, `@theatre/*`, `framer-motion-3d`, `split-type`, AOS, `typed.js` 3 — код «по памяти» из 2022–2024.
4. «SplitText платный» и подключение `SplitText` из `gsap-trial`/чужих «nulled»-репозиториев — с 3.13 всё в npm `gsap`.
5. `@supports (animation-timeline: scroll())` без `animation-range` — ловит частичные реализации; `scroll-timeline-polyfill`.
6. Содержимое скрыто до анимации (`opacity: 0` в CSS) без JS-фолбэка — в Firefox (нет SDA) или при ошибке скрипта текст невидим.
7. dotLottie/Rive без `setWasmUrl` — скрытый запрос к jsDelivr/unpkg при запрете CDN; Rive по документации — `unpkg …@latest`.
8. three.js ради одного шейдерного фона (108 КБ вместо 6–11); pixi.js ради частиц в hero (120 КБ, TBT 116).
9. Spline-сцена «как лёгкий вариант» 3D (833 КБ br рантайма) и Unicorn-аврора без решения заказчика (третьи домены, тариф).
10. React SPA для лендинга: пустой HTML для ИИ-ботов, LCP после JS.
11. `legalComments: 'none'` в сборке с GSAP.
12. Barba для нового сайта (без релизов с 2024-08) вместо нативных VT или Swup 4.
13. Платформы: GSAP-бандл в Code Embed Webflow (> 50 000 символов) вместо интеграции; в Битриксе GSAP и плагины отдельными
    `addJs` (плагин раньше ядра); на Тильде «анимация не работает на телефоне» — она выключена по умолчанию.

## Чек-лист

- [ ] Эффект разложен по лестнице: взята самая низкая ступень, которая его делает?
- [ ] JS слоя «подача» ≤ 20 / 100 / 150–200 КБ br по уровню, wasm — после LCP?
- [ ] GSAP есть, только если в `treatment` pin, split, Flip, горизонталь или сюжет для Firefox?
- [ ] SDA под `@supports (… and (animation-range: 0% 100%))`, смысловое содержимое видно без SDA и без JS?
- [ ] Lenis только на L2, пакет `lenis`, `anchors: true`, один цикл с `gsap.ticker`?
- [ ] Переходы: нативный `@view-transition` в `prefers-reduced-motion: no-preference`; библиотека — только для состояния между страницами?
- [ ] Шейдер-фон на paper-shaders/OGL/WebGL2, three — только при 3D?
- [ ] Wasm dotLottie/Rive — со своего домена (`setWasmUrl`), с brotli?
- [ ] Нет пакетов из §7; версии проверены `npm view` на дату сборки?
- [ ] Смысл страницы в HTML сервера (статика/SSG/SSR), не SPA?
- [ ] Способ подключения соответствует `constraints.cms` (§10), лимиты платформы учтены?
- [ ] Уведомления лицензий в бандле сохранены; продукт не становится no-code-билдером анимаций на GSAP?

## Открытые вопросы и противоречия

1. **TBT шумит**: замер на общей машине при load average 6,8–10,3; порядок величин надёжен, единицы мс — нет; на реальных
   телефонах не мерили → «Что проверить в живой фазе».
2. **Позиция базы «scroll-driven — основной инструмент подачи»** (поправки PLAN) против практики (2 из 49) и поддержки (нет Firefox) —
   в стеке: CSS SDA — умолчание L1 для декоративного, GSAP — для смыслового; решение E о нормах движения может сдвинуть границу.
3. **Главный поток SDA против GSAP под нагрузкой** — тезис вендора браузера («off the main thread»), нашим опытом не проверен.
4. **Разбор JS по назначению** (фреймворк / эффекты / аналитика) на живых сайтах не сделан: сырьё C без списка скриптов;
   доля библиотек подачи 6–9 % — расчёт.
5. **Тарифы и лимиты платформ**: T123 во Free Тильды, тарифы кода Framer, лимит Code Embed Webflow — из вторичных источников или
   косвенно; справка Webflow отдала 403.
6. **Не прочитано/не замерено**: лицензия Spline-рантайма и SDK Unicorn; Rive webgl2 и dotLottie Worker; условия `motion/three`
   («Motion+ early access», но код в публичном пакете).
7. **Firefox** не установлен в Playwright (решение заказчика 13 разрешает) — фолбэки для Firefox проверены только чтением BCD.

## Источники

- [S1] Webflow, «Standard "No Charge" GSAP License», gsap.com/community/standard-license — eff. 2025-04-30, ред. 2025-05-30; снято 2026-09-24. Первоисточник.
- [S2] GSAP, «3.13 release», https://gsap.com/blog/3-13/ (2025-04-30): бесплатность, SplitText 3.13, интеграция Webflow. Надёжно.
- [S3] Webflow Updates, «Webflow makes GSAP 100% free», https://webflow.com/updates/gsap-becomes-free (2025-04-30); ленты «Interactions with GSAP». Вендор.
- [S4] Webflow Updates, «Increased custom code character limit», https://webflow.com/updates/increased-custom-code-character-limit (2024-05-07). Справка help.webflow.com — 403.
- [S5] Motion: https://motion.dev/docs/animate, /docs/scroll, /docs/split-text (снято 2026-09-24). Вендор.
- [S6] darkroomengineering/lenis README (main, 2026-09-24), npm lenis 1.3.26; 16 000★, push 2026-09-22. Надёжно.
- [S7] @mdn/browser-compat-data 8.1.3 (2026-09-24T13:25Z), web-features 3.39.0 — опыт G/00. Надёжно.
- [S8] Chrome for Developers, «Scroll-driven animations», https://developer.chrome.com/docs/css-ui/scroll-driven-animations. Вендор браузера.
- [S9] Chrome for Developers, «CSS scroll-triggered animations are coming», https://developer.chrome.com/blog/scroll-triggered-animations (145 против 146 в BCD).
- [S10] GoogleChrome/modern-web-guidance 0.0.190 (Apache-2.0): `scrollytelling.md`, `cross-document-transitions.md` — клон `../../kimi-research/99-raw/cache/repos/`. Официальный скилл Chrome.
- [S11] Astro, «View transitions», https://docs.astro.build/en/guides/view-transitions/ (astro 7.3.5). Надёжно.
- [S12] swup, https://swup.js.org/options/, /getting-started/ (4.10.0, 2026-09-03; 5 234★). Надёжно.
- [S13] barba.js, https://barba.js.org/docs/getstarted/intro/ (@barba/core 2.10.3; без релизов с 2024-08).
- [S14] Rive, https://rive.app/docs/runtimes/web/web-js; README @rive-app/canvas 2.43.1. Вендор.
- [S15] LottieFiles, README @lottiefiles/dotlottie-web 0.80.0 (npm). Вендор.
- [S16] Unicorn Studio, https://www.unicorn.studio/docs/embed/ (2026-09-24); GitHub hiunicornstudio/unicornstudio.js (258★, без лицензии). Вендор.
- [S17] Spline, «Exporting as Code», https://docs.spline.design/exporting-your-scene/web/exporting-as-code. Вендор.
- [S18] Тильда: tilda.cc/ru/answers/a/html, help-ru.tilda.ws/html, help-ru.tilda.cc/zero/advanced-animation, answers/a/mobile-animation, tilda.cc/ru/pricing (2026-09-24).
- [S19] WordPress: developer.wordpress.org `wp_enqueue_script_module()` (6.5; `$args` 6.9); make.wordpress.org/core, async/defer в 6.3 (2023-07-14).
- [S20] 1С-Битрикс, API D7 `Asset::addJs` (с 14.9.4), https://dev.1c-bitrix.ru/api_d7/bitrix/main/page/asset/addjs.php.
- [S21] Framer: https://www.framer.com/academy/lessons/custom-code; https://www.framer.com/developers/custom-code. Тарифы — не из первоисточника.
- [S22] greensock/gsap-skills (aed9cfd, 2026-04-21, MIT, 15 642★) — клон `99-raw/cache/repos/greensock__gsap-skills/`. Вендор.
- [S23] npm registry (47 пакетов) и GitHub API (20 репозиториев), 2026-09-24 — `99-raw/experiments/G/00-registry/`. Данные.
- [S24] 3d: `01-web-3d-landscape/03-runtime-landscape.md` §1, §8–12; `09-web-runtime/03-scroll-interaction-animation.md` §1–3; `01/01` §5.7; `01/02` §6.1.
- [S25] kimi: `07-brief-handoff/02-task-package.md` §8.1.
- [S26] site: `07-seo-geo-performance-analytics/01` §1.3, `02` §3, `budgets.yaml`; `06-multipage-ia/01` §4.5; `site-brief.schema.json` (`constraints`).
- [S27] C: `../03-live-sites-measured/sites.csv` (49 десктоп), `01-effects-sites-measured.md`. [S28] A: `../01-creative-direction/ambition-levels.yaml` v0.1.
- [S29] Опыт G/01 `99-raw/experiments/G/01-lib-cost/`; [S30] G/02 `02-st-lenis-vt/`; [S31] G/00 `00-registry/`; G/03 `03-effect-module/`.
- Дайджесты W: `[V:YGxOh85VtFg]` Carmen Ansio (CSS Day 2024), `[V:iqtCk5cY5Xs]` Е. Прокопьев (HolyJS 2023), `[V:ufHQG7fDLQc]` J. Benegas (React Miami 2023) — `../91-videos/digests/`.
- [S32] Евгений (канал Вкалывают Роботы), «7 библиотек для красивых AI-приложений с вайб-кодингом», YouTube, 11 августа 2026, 8:56,
  https://www.youtube.com/watch?v=6XNhZu6mJlE — киты для Claude Code, anime.js, Rive; дайджест
  `../../claude-design-research/91-videos/digests/6XNhZu6mJlE.md`; один практик без замеров [мнение]. Дополнение 25.09.2026.
- [S33] Лицензии и зависимости китов (файлы LICENSE и package.json на GitHub, raw HEAD, 2026-09-25): DavidHDev/react-bits,
  kokonut-labs/kokonutui, magicuidesign/magicui, magicuidesign/mcp, bklit/bklit-ui, saadeghi/daisyui, juliangarnier/anime,
  https://github.com/DavidHDev/react-bits — первоисточник [документация]. Дополнение 25.09.2026.
- [S34] Rive, «Pricing», https://rive.app/pricing, и «FAQ: Rive AI Coding Agent» (12.01.2026), https://rive.app/blog/rive-ai-coding-agent-faq —
  сняты 2026-09-25, кэш `../../claude-design-research/99-raw/cache/rive.app_pricing_ebd26c5e.md`; вендор [документация]. Дополнение 25.09.2026.
