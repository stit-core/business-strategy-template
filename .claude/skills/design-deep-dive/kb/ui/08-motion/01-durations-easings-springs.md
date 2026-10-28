# Длительности, кривые и пружины

Волна 2, агент M, 22 сентября 2026. Источников прочитано целиком: 59 (исходники токенов 15 дизайн-систем, документация, спецификации W3C и MDN, материалы практиков), плюс 9 видеодайджестов агента V и собственный пересчёт измерений 24 живых продуктов из `../99-raw/cache/measurements/`.

Смежные файлы: каталог «что анимировать» в `02-what-to-animate-in-apps.md`, доступность движения и готовые токены в `03-reduced-motion-and-motion-tokens.md`, пружина токеном ДС, переходы по шаблонам интерфейса и их перевод на веб, Compose и SwiftUI — `04-spring-tokens-transitions-platforms.md`. UX-сторона (когда движение нужно по сценарию, задержки обратной связи, микровзаимодействия как логика) — в `../../ux/06-feedback-states-motion/`, здесь только визуальные величины. Тени и подъём при hover — `../04-shape-elevation/02-shadows-layers-depth.md`; фокус-кольцо — там же §10.

## Выжимка для агента

1. **Шести длительностей хватает на весь продукт**: 0, 100, 150, 200, 300, 400 ms. Atlassian обходится восемью, Carbon шестью, Ant тремя. Material 3 объявляет шестнадцать и сам же признаёт их устаревшими. → §1, §7 [консенсус]
2. **Дефолт 150 ms.** Так у Tailwind (`--default-transition-duration: 150ms`), Carbon (`duration-moderate-01`), Atlassian (`motion.duration.short`). Измерения живых продуктов: 150 и 200 ms вместе дают 54 % всех объявлений `transition-duration`. → §1.1, §6 [консенсус]
3. **150 + 200 + 300 ms покрывают 70 % всех переходов в вебе** (1576 объявлений на 24 продуктах). Всё, что длиннее 300 ms, — 1.4 %. Не изобретай новых чисел. → §6 [исследование: измерение]
4. **Потолок 300 ms для рабочих интерфейсов, 400–600 ms только для полноэкранных переходов и онбординга.** Kowalski: «your animations should also usually be shorter than 300 ms». Spectrum обрезает шкалу на 500. → §1.3 [консенсус]
5. **Hover и press — 50–150 ms.** Atlassian разводит: hover элемента списка 50, тонкое pressed 100, акцентная подсветка 150. Carbon: микровзаимодействие укладывается в 90–120 ms. → §1.2 [система]
6. **Фокус не анимируется.** Atlassian вводит для этого отдельный токен `motion.duration.instant` = 0 ms. → §1.2, §8.3 [система]
7. **Вход — decelerate (ease-out), выход — accelerate (ease-in), перемещение внутри экрана — ease-in-out, цикл — linear.** Это единственное правило, на котором сходятся Carbon, Fluent, Primer, Spectrum, Atlassian и Material. → §2.1 [консенсус]
8. **Выход короче входа на 50–100 ms** для оверлеев: Atlassian Modal 250 → 200, Popup 150 → 100; MUI enteringScreen 225 → leavingScreen 195. → §3.1 [консенсус]
9. **У hover правило обратное:** приход быстрый (125 ms), уход расслабленный (450 ms). Это не противоречие, а разные жанры: оверлей «убирают с дороги», hover «отпускают». → §3.2 [спорно]
10. **Кривая входа: `cubic-bezier(0, 0, 0.2, 1)` (Tailwind/M2 ease-out) или `cubic-bezier(0, 0, 0, 1)` (M3 standard-decelerate).** Кривая выхода: `cubic-bezier(0.4, 0, 1, 1)`. Общая: `cubic-bezier(0.4, 0, 0.2, 1)`. → §2.2 [консенсус]
11. **Встроенные `ease-in`/`ease-out` слабоваты.** Kowalski: «I almost never use them… `ease` is an exception as it works well for basic hover effects like changing background color». Практика это подтверждает наоборот: `ease` занимает 34.7 % живых объявлений. → §2.4, §6.2 [спорно]
12. **Material 3 объявил всю систему длительностей и кривых устаревшей** («no longer maintained») и перешёл на пружины motion physics. Легаси-кривые оставлены только для не мигрировавших команд. → §4.1 [система]
13. **Пружина описывается либо (stiffness, damping, mass), либо (duration, bounce).** Перевод: `ω_n = √(k/m)`, `duration = response = 2π/ω_n`, `bounce = 1 − ζ` при ζ ≤ 1 и `1/ζ − 1` у передемпфированной. В ДС пружина — `dampingRatio` и `stiffness` при массе 1, перевод на Compose, SwiftUI и веб — `04-spring-tokens-transitions-platforms.md` §2. → §4.2 [консенсус] [проверено: расчёт]
14. **Геометрия пружинит, цвет и прозрачность — никогда.** В M3 Expressive все шесть effects-пружин имеют ζ = 1.0 (критическое демпфирование, перелёт 0) и совпадают у standard и expressive схем. Comeau: «I wouldn't use them [springs] for color or opacity changes». → §4.3 [консенсус]
15. **Готовая таблица M3 «пружина → cubic-bezier + длительность» для веба лежит в §4.5.** Все spatial-кривые имеют y₁ > 1, то есть перелёт зашит в кривую. → §4.5 [система]
16. **Carbon прямо запрещает перелёт в рабочем интерфейсе**: «Do not use easing curves that suggest bounce, stretch, or sudden stops». M3 Expressive его требует. Это настоящий конфликт систем, выбирай по типу продукта. → §4.6 [спорно]
17. **Длительность растёт от расстояния как корень четвёртой степени, а не линейно.** По формуле MUI: 36 px → 192 ms, 100 px → 239, 300 px → 311, 600 px → 376. Удвоение дистанции добавляет ≈ 19 % времени. → §5.1 [система]
18. **Пружину в чистом CSS даёт `linear()`** (Baseline Newly available с декабря 2023, Widely available с июня 2026). Равномерных точек нужно 40–75, точек с процентами там, где кривая гнётся, — вдвое меньше. В ДС пружина — токен с параметрами: строку из 21–28 точек и время успокоения собирает сборка (`04-spring-tokens-transitions-platforms.md` §1). → §4.7 [консенсус]
19. **`linear()`-пружина врёт на прерываниях:** CSS применяет reversing shortening factor и пружина на 1600 ms перезапускается за 400 ms. Настоящие прерываемые пружины — только JS. → §4.7 [мнение: Comeau]
20. **CSS `transition` прерываем, `@keyframes` — нет.** Для состояний бери `transition`, для циклов `@keyframes`. → §3.3 [консенсус]
21. **Атлас длительностей и кривых 15 систем — в §1.1 и §2.2.** Не усредняй, выбирай строку и следуй ей целиком.
22. **Шаг шкалы длительностей выбирают как шаг сетки отступов:** Atlassian 25 ms, Spectrum 30 ms, Material и Polaris 50 ms, Primer 100 ms после 100. → §1.4 [система]
23. **Один множитель на весь продукт полезен.** Ant: `motionUnit: 0.1` и `motion: true` — вся скорость интерфейса и его выключение в двух токенах. → §7.3 [система]
24. **Не анимируй действия, запускаемые с клавиатуры.** Kowalski: «never animate keyboard initiated actions» — их повторяют сотни раз в день. → §3.4, `02-what-to-animate-in-apps.md` §2 [мнение]
25. **Проверка Carbon: «Is your motion frequently noticed by average users? If so, consider removing or minimizing it.»** → §8.1 [система]

---

## 1. Длительности

### 1.1 Сводная таблица по системам

Значения взяты из исходников токенов (GitHub/npm), кроме отмеченных «док.».

| Система | Шкала, ms | Дефолт | Имена | Источник |
|---|---|---|---|---|
| **Material 3 (legacy)** | 50, 100, 150, 200 / 250, 300, 350, 400 / 450, 500, 550, 600 / 700, 800, 900, 1000 | нет | `short1–4`, `medium1–4`, `long1–4`, `extra-long1–4` | [S1] `_md-sys-motion.scss` v0.192 |
| **Shopify Polaris** | 0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 + 5000 | нет | `--p-motion-duration-<N>` | [S2] motion.ts (архив репозитория с сентября 2026) |
| **Microsoft Fluent 2** | 50, 100, 150, 200, 250, 300, 400, 500 | `durationNormal` 200 | `durationUltraFast … durationUltraSlow` | [S3] `durations.ts` |
| **IBM Carbon** | 70, 110, 150, 240, 400, 700 | `duration-moderate-01` 150 | `durationFast01/02`, `Moderate01/02`, `Slow01/02` | [S4] `@carbon/motion` |
| **Tailwind v3.4** | 0, 75, 100, 150, 200, 300, 500, 700, 1000 | 150 | `duration-<N>` | [S5] `config.full.js` |
| **Tailwind v4** | шкалы нет, число произвольное | `--default-transition-duration: 150ms` | `duration-<произвольное>` | [S5] `theme.css` |
| **Atlassian (@atlaskit/motion)** | 0, 100, 350, 700 (сетка 25) | `medium` 350 | `none/small/medium/large` | [S6] `durations.js` |
| **Atlassian (новая, 2026)** | 0, 50, 100, 150, 200, 250, 400, 600 | `short` 150 | `motion.duration.instant … xxlong` | [S14], [S23], [S25] |
| **GitHub Primer** | 0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 | нет | `--base-duration-<N>` | [S7] `motion.css` |
| **Adobe Spectrum** | 130, 160, 190, 220 (micro) / 250, 300, 350, 400, 450, 500 (macro) | нет | `duration-100 … duration-1000` | [S26] док. v5.0.0 |
| **Ant Design 5** | 100, 200, 300 (вычисляются от `motionUnit: 0.1`) | `Mid` 200 | `motionDurationFast/Mid/Slow` | [S8] `seed.ts` |
| **MUI** | 150, 195, 200, 225, 250, 300, 375 | `standard` 300 | `shortest … complex`, `enteringScreen`, `leavingScreen` | [S9] `createTransitions.js` |
| **Mantine** | по умолчанию 250 у `Transition` | 250 | — | [S13] |
| **Radix Themes** | токенов движения нет | — | — | [S10] |
| **Apple HIG** | числовых токенов нет вовсе | — | — | [S12] |

Наблюдения, которые важнее самих чисел:
- **Шкал два типа.** Числовые (`duration-200`, имя = значение: Polaris, Primer, Tailwind) и ролевые (`fast`, `moderate`, `enteringScreen`: Carbon, Fluent, MUI). Ролевые заставляют думать о назначении, числовые проще генерировать. Для агента лучше гибрид: ролевое имя + число в описании.
- **Количество шагов колеблется в 5 раз**: 3 у Ant, 4 у старого Atlassian, 6 у Carbon, 8 у Fluent, 12 у Polaris и Primer, 16 у Material. Больше восьми не нужно никому: у Polaris из 12 шагов на практике работают 5.
- **Radix Themes вообще не выделяет движение в токены**: в каталоге `src/styles/tokens` есть space, radius, shadow, typography, scaling, cursor, layout — и нет motion. Анимации живут в CSS компонентов, привязанные к `[data-state="open"]` [S10].
- **Apple не публикует ни одного числа** ни в HIG Motion, ни в разделе о переходах: «Aim for brevity and precision in feedback animations» — и всё [S12].

### 1.2 Роли и их вилки

| Роль | Вилка, ms | Обоснование |
|---|---|---|
| **Мгновенно (фокус)** | **0** | `motion.duration.instant` у Atlassian: «immediate feedback (focus state)» [S25]. Кольцо фокуса должно появляться в том же кадре, что и нажатие Tab |
| **Частый hover (строка списка, ячейка таблицы)** | **50** | Atlassian: «List item hover, 50 ms» [S23] |
| **Hover кнопки, смена цвета** | **100–150** | Carbon fast-01 70 «instant response to user action», fast-02 110 «subtle entrance or exit of small UI elements»; Atlassian xshort 100, short 150 [S4], [S25] |
| **Появление поповера, дропдауна, тултипа** | **120–200** | Atlassian «Dropdown entrance, 150 ms»; Fluent `durationNormal` 200; измерения: 150 и 200 ms доминируют [S23], [S3], [S56] |
| **Модалка, диалог** | **200–300** | Atlassian «Modal entrance, 250 ms»; MUI `enteringScreen` 225 [S25], [S9] |
| **Боковая панель, дровер** | **250–350** | Carbon moderate-02 240 «expansion, system communication, toast»; Atlassian новая шкала: transitions 150–400 [S4], [S23] |
| **Переход уровня страницы** | **400** | Atlassian `xlong` 400 «page-level transitions» [S25] |
| **Онбординг, полноэкранный оверлей** | **600** | Atlassian `xxlong` 600 «onboarding steps, full-screen overlays» [S25] |
| **Затемнение фона под модалкой** | **240–700** | Carbon slow-02 700 «background dimming, large hero transitions»; Atlassian `motion.blanket.enter` 250 [S4], [S14] |
| **Цикл спиннера** | **1000** | Tailwind `--animate-spin: spin 1s linear infinite` [S5] |
| **Цикл пульсации / шиммера** | **1500–2000** | Tailwind `--animate-pulse: pulse 2s cubic-bezier(0.4,0,0.6,1) infinite`, keyframes `50% { opacity: 0.5 }` [S5] |

Диапазоны Atlassian для двух классов движения, заданные прямо в документации: **Interactions 50–150 ms** (hover и press), **Transitions 150–400 ms** (вход, выход, перемещение) [S23]. Это самая аккуратная формулировка из найденных: она не задаёт число компоненту, а задаёт коридор классу.

### 1.3 Потолок

Три независимых ограничения сходятся на 300–400 ms:
- **Практика.** Из 1576 объявлений `transition-duration` на 24 живых продуктах длиннее 300 ms — 1.4 % (400 ms: 8 штук, 500 ms: 7, 3000 ms: 1 у холста tldraw) [S56].
- **Практик.** Kowalski: «Your animations should also usually be **shorter than 300 ms**» [S14].
- **Система.** Spectrum обрезает шкалу на 500 ms и делит её на micro (130–220) и macro (250–500); micro — «color fades, hovers, accordions, tooltips» [S26].

Исключения, где длиннее допустимо: затемнение фона под крупным оверлеем (до 700 ms, Carbon slow-02), пошаговый онбординг (600 ms, Atlassian xxlong), непрерывные циклы (спиннер 1 s, шиммер 2 s). Во всех трёх случаях пользователь не ждёт результата действия, а смотрит на смену контекста.

Антипример из Kowalski: гипотетическая анимация открытия Raycast на 500 ms. «Raycast has no animations and it feels right» [S14].

### 1.4 Шаг шкалы

Шкала длительностей строится как шкала отступов, от базового шага:

| Система | Шаг | Комментарий из исходника |
|---|---|---|
| Atlassian | **25 ms** | «Think of this as the motion equivalent of the `@atlaskit/theme` `grid()`» [S6] |
| Spectrum | **30 ms** | единственная система с «некруглыми» числами 130/160/190/220 [S26] |
| Material, Polaris | **50 ms** | 50 до 200, затем 50 до 600 [S1], [S2] |
| Primer | **50, затем 100** | 0, 50, 100, затем ровно по 100 до 1000 [S7] |
| Ant | **100 ms** (`motionUnit` 0.1 s) | вся шкала — три множителя одной ручки [S8] |
| Carbon | нерегулярный | 70 / 110 / 150 / 240 / 400 / 700: «Carbon uses a **non-linear duration scale** to achieve better perceived consistency across all distances» [S22] |

Рекомендация для генеративной системы: **шаг 50 ms в середине шкалы, 25 ms в нижней части** (0, 50, 100, 150, 200, 300, 400). Числа кратные 50 узнаются глазом разработчика и не требуют пояснений.

---

## 2. Кривые

### 2.1 Роли кривых: единственное правило, на котором сходятся все

| Роль | Смысл | Форма | Кто так говорит |
|---|---|---|---|
| **Entrance / decelerate / ease-out** | элемент появляется или влетает в кадр | резкий старт, мягкое торможение: первая пара координат близка к (0, 0) по X | Carbon, Fluent, Primer, Spectrum, Atlassian, Material, MUI |
| **Exit / accelerate / ease-in** | элемент уходит насовсем | мягкий старт, «в стену» на финише: вторая контрольная точка близка к (1, 1) | те же |
| **Standard / ease-in-out** | элемент виден от начала до конца и перемещается внутри экрана | симметричная | те же |
| **Linear** | циклы без начала и конца | прямая | Primer: «Use for continuous animations like progress bars or loaders»; Polaris: «for continuous and mechanical animations, such as rotating spinners» |

Формулировки из исходников, дословно:
- Primer: `easeOut` — «Decelerating motion. Use for elements **entering** the viewport or appearing on screen»; `easeIn` — «Accelerating motion. Use for elements **exiting** the viewport»; `easeInOut` — «Use for elements **moving or morphing within** the viewport» [S7].
- MUI: `easeOut` — «Objects **enter the screen at full velocity** from off-screen and slowly decelerate to a resting point»; `easeIn` — «Objects **leave the screen at full velocity**. They do not decelerate when off-screen» [S9].
- Carbon: `standard-easing` — элемент виден от начала до конца (раскрытие плиток, сортировка строк таблицы); `entrance-easing` — добавление элемента; `exit-easing` — удаление навсегда [S22].

**Важное исключение Carbon**, которого нет больше нигде: если элемент уходит за край, но «остаётся рядом» и готов вернуться (боковая панель), берётся **standard, а не exit**: «The panel leaves the view, but **slows down as it exits**, implying that it would come to rest just outside the view» [S22]. Практический вывод: дровер, который можно вернуть свайпом или кнопкой, уходит с торможением; модалка, которую закрыли, уходит с ускорением.

### 2.2 Атлас кривых

| Система | ease / standard | ease-out / entrance | ease-in / exit | linear | Прочее |
|---|---|---|---|---|---|
| **Material 3 (legacy)** | `0.2, 0, 0, 1` | `0, 0, 0, 1` | `0.3, 0, 1, 1` | `0, 0, 1, 1` | emphasized-decelerate `0.05, 0.7, 0.1, 1`; emphasized-accelerate `0.3, 0, 0.8, 0.15`; `emphasized` = **N/A, составной путь** |
| **Material 2 (legacy в M3)** | `0.4, 0, 0.2, 1` | `0, 0, 0.2, 1` | `0.4, 0, 1, 1` | — | — |
| **Carbon productive** | `0.2, 0, 0.38, 0.9` | `0, 0, 0.38, 0.9` | `0.2, 0, 1, 0.9` | — | — |
| **Carbon expressive** | `0.4, 0.14, 0.3, 1` | `0, 0, 0.3, 1` | `0.4, 0.14, 1, 1` | — | — |
| **Fluent 2** | easyEase `0.33, 0, 0.67, 1`; easyEaseMax `0.8, 0, 0.2, 1` | decelerateMax `0.1, 0.9, 0.2, 1`; Mid `0, 0, 0, 1`; Min `0.33, 0, 0.1, 1` | accelerateMax `0.9, 0.1, 1, 0.2`; Mid `1, 0, 1, 1`; Min `0.8, 0, 0.78, 1` | `0, 0, 1, 1` | три силы у каждого семейства |
| **Primer** | ease `0.25, 0.1, 0.25, 1`; easeInOut `0.6, 0, 0.2, 1` | `0.3, 0.8, 0.6, 1` | `0.7, 0.1, 0.75, 0.9` | `0, 0, 1, 1` | — |
| **Polaris** | ease `0.25, 0.1, 0.25, 1`; easeInOut `0.42, 0, 0.58, 1` | `0.19, 0.91, 0.38, 1` | `0.42, 0, 1, 1` | `0, 0, 1, 1` | ease — действия пользователя, ease-in-out — системные изменения; «ease-in и ease-out — use sparingly»; `linear` — спиннеры [S63] |
| **Atlassian (новая)** | inout-bold `0.4, 0, 0, 1` | out-bold `0, 0.4, 0, 1`; out-practical `0.4, 1, 0.6, 1` | in-practical `0.6, 0, 0.8, 0.6` | — | `easing.spring` = `linear()` из 65 точек |
| **Atlassian (@atlaskit)** | easeInOut `0.15, 1, 0.3, 1` | easeOut `0.2, 0, 0, 1` | easeIn `0.8, 0, 0, 0.8` | `0, 0, 1, 1` | семейство `easeIn40/60/80Out` |
| **Spectrum** | `0.45, 0, 0.40, 1` | `0, 0, 0.40, 1` («most common in Spectrum») | `0.50, 0, 1, 1` | — | всего три кривые |
| **Ant Design 5** | easeInOut `0.645, 0.045, 0.355, 1`; easeInOutCirc `0.78, 0.14, 0.15, 0.86` | easeOut `0.215, 0.61, 0.355, 1`; easeOutCirc `0.08, 0.82, 0.17, 1`; easeOutQuint `0.23, 1, 0.32, 1` | easeInQuint `0.755, 0.05, 0.855, 0.06` | — | **easeOutBack `0.12, 0.4, 0.29, 1.46`** (перелёт), **easeInBack `0.71, −0.46, 0.88, 0.6`** (подсед) |
| **MUI** | easeInOut `0.4, 0, 0.2, 1`; sharp `0.4, 0, 0.6, 1` | `0, 0, 0.2, 1` | `0.4, 0, 1, 1` | — | sharp — «objects that may return to the screen at any time» |
| **Tailwind v3/v4** | `0.4, 0, 0.2, 1` | `0, 0, 0.2, 1` | `0.4, 0, 1, 1` | `linear` | — |

### 2.3 Кривые с перелётом

Из изученных систем перелёт (y > 1) есть только у трёх:
- **Ant Design**: `motionEaseOutBack (0.12, 0.4, 0.29, 1.46)` — перелёт до 146 % и `motionEaseInBack (0.71, −0.46, 0.88, 0.6)` — предварительный подсед до −46 % [S8].
- **Material 3 Expressive**, в официальной таблице перевода пружин в кривые: y₁ от 1.06 до **1.67** (§4.5) [S24].
- **Atlassian**: перелёт вынесен не в `cubic-bezier`, а в отдельный токен `easing.spring` — CSS-функция `linear()` из **65 точек** [S14].

Carbon прямо это запрещает: «Avoid easing curves that are unnatural, distracting, or purely decorative… **Do not use easing curves that suggest bounce, stretch, or sudden stops**» [S22]. Подробнее о конфликте — §4.6.

### 2.4 Насколько сильной должна быть кривая

Kowalski: «The built-in easing curves in CSS are usually **not strong enough**, which is why I almost never use them… `ease` is an exception as it works well for basic hover effects like changing background color, but anything else requires a custom curve» [S15]. Рекомендуемые генераторы: easing.dev, easings.co.

Сравнение силы на числах: браузерный `ease-out` = `cubic-bezier(0, 0, 0.58, 1)`; M2 `ease-out` = `(0, 0, 0.2, 1)`; M3 standard-decelerate = `(0, 0, 0, 1)`; Fluent decelerateMax = `(0.1, 0.9, 0.2, 1)`. Чем ближе последняя пара к (0, 1), тем резче старт и мягче финиш. Разница между браузерным 0.58 и Material 0.2 видна невооружённым глазом на смещении 8 px.

Но практика расходится с этим советом: в измерениях живых продуктов `ease` (браузерный дефолт) — **самая частая кривая, 34.7 % всех объявлений** [S56]. См. §6.2.

---

## 3. Асимметрия входа и выхода

### 3.1 Оверлеи: выход быстрее входа

| Система | Вход | Выход | Отношение |
|---|---|---|---|
| Atlassian Modal | 250 ms, ease-out-bold | 200 ms, ease-in-practical | 0.80 |
| Atlassian Popup | 150 ms | 100 ms | 0.67 |
| Atlassian Flag | 250 ms | 200 ms | 0.80 |
| MUI | `enteringScreen` 225 ms | `leavingScreen` 195 ms | 0.87 |

Правило Atlassian сформулировано численно: «Exits should be shorter, faster, and less dramatic. Use a practical easing curve and **reduce the duration by 50 ms or 100 ms compared to the entrance**» [S25]. Смысловое обоснование там же: «Entrances **orient the user** to new content and establish context, while exits **confirm a dismissal** and clear the way for what's next.»

Предельный случай — контекстное меню macOS в разборе Rauno Freiberg: **появляется без анимации вообще (0 ms), исчезает с затуханием**; выбранный пункт коротко мигает акцентным цветом как подтверждение [S16].

### 3.2 Hover: вход быстрее выхода (противоположное правило)

Comeau предлагает ровно обратную асимметрию для hover [S54]:

```css
.btn       { transition: transform 450ms; }                         /* уход курсора */
.btn:hover { transition: transform 125ms; transform: translateY(-10px); }  /* приход */
```

«For hover animations, I like to make the **enter animation quick and snappy**, while the **exit animation can be a bit more relaxed and lethargic**.» Для модалок он же советует классическую схему: вход `ease-out`, выход быстрее и `ease-in`.

Противоречие снимается разделением по жанрам, а не усреднением:
- **Оверлей** (модалка, поповер, тост): выход = «убрать с дороги», должен быть короче входа.
- **Состояние элемента** (hover, press): вход = «система заметила курсор», должен быть мгновенным; выход = «отпустили», может быть плавным.

Для базы это значит, что токенов движения нужно два комплекта: `enter/exit` для оверлеев и `hovered/pressed` для состояний. Именно так устроен новый набор Atlassian: `motion.avatar.hovered` и `motion.avatar.pressed` отдельно от `motion.avatar.enter` и `motion.avatar.exit` [S25].

### 3.3 Прерываемость

- **CSS `transition` прерываем и плавно уходит к новому значению даже до завершения. CSS `@keyframes` — нет** [S14]. Отсюда правило: всё, что зависит от состояния (hover, open/closed, selected), делается через `transition`; циклы (спиннер, шиммер) — через `@keyframes`.
- Apple HIG: «Let people cancel motion. As much as possible, don't make people wait for an animation to complete before they can do anything, especially if they have to experience the animation more than once» [S12].
- Rauno Freiberg: «Great interactions are modeled after properties from the real world, like **interruptability**… imagine if [flipping a page] were an animation that you had to wait for!» Антипример из iOS Settings: слой въезжает справа, и свайп назад сразу после ошибочного тапа не прерывает анимацию [S16].
- Пружины прерываемы физически: у них есть текущая скорость, которую можно передать новому движению. `cubic-bezier` при прерывании начинает заново; `linear()`-пружина прерывается плохо (§4.7).

### 3.4 Частота как параметр

Самое сильное правило раздела, и оно не про числа:

- Apple HIG: «**In apps, generally avoid adding motion to UI interactions that occur frequently**» [S12].
- Kowalski: «Before you add an animation, you should also consider **how often the user will see it**. A good tip here is to **never animate keyboard initiated actions**. These actions are repeated sometimes hundreds of times a day, an animation would make them feel slow» [S14].
- Rauno Freiberg, из личного опыта над bmrks.com: анимации активного индикатора и добавления элементов «began to feel sluggish» через пару дней; «I removed motion from core interactions and suddenly felt like I was moving much faster» [S16].
- Carbon, чек-лист: «The best interface motion may go unnoticed… **Is your motion frequently noticed by average users? If so, consider removing or minimizing it**» [S22].

Практическое следствие для плотных админок: движение уместно там, где действие редкое и меняет контекст (открылась модалка, пришёл тост), и вредно там, где действие повторяется (навигация по строкам, переключение вкладок горячими клавишами, открытие командного меню).

---

## 4. Пружины

### 4.1 Смена парадигмы: Material 3 отказался от длительностей

Дословно из документации M3 (сентябрь 2026): «In the expressive update, components and motion now use the **motion physics system**, which uses springs. Products should migrate to the new system. The easing and duration system is still used for transitions and can be used by teams that haven't yet updated to GM3 Expressive, but is **no longer maintained**.» И на странице спеков: «The **spring composite** tokens are used in the motion physics system… The easing, duration, and path tokens are used by the legacy system, so **can be ignored**» [S24].

Статус по платформам из той же таблицы:

| Платформа | Статус | Как применять |
|---|---|---|
| Jetpack Compose | Available | встроенные компоненты и spring-токены |
| Android Views (MDC) | Available, в компоненты не добавлено | spring-токены |
| **Web** | **Compatible** | «Use springs when possible, otherwise use **curves that mimic the springs** for animations without interruptions or gestures» |

То есть на вебе Google сам рекомендует кривые, если нет прерываний и жестов. Практический вывод для генеративной системы: **в веб-сервисе оставайся на длительностях и кривых, пружины бери точечно для перетаскивания, свайпов и переключателей**.

### 4.2 Две модели описания

| Модель | Параметры | Кто использует |
|---|---|---|
| Физическая | **mass** (масса), **stiffness / tension** (жёсткость), **damping / friction** (демпфирование) | Compose Material 3, React Spring, Framer Motion (`type: "spring"`), Easing Wizard |
| Воспринимаемая | **duration** (воспринимаемый темп), **bounce** (перелёт) | SwiftUI (Apple), Motion `spring(duration, bounce)` |

Перевод между ними (проверено расчётом при m = 1):
- собственная частота `ω_n = √(k / m)`;
- коэффициент демпфирования `ζ = c / (2√(k·m))`;
- `bounce = 1 − ζ` при ζ ≤ 1 и `bounce = 1/ζ − 1` у передемпфированной пружины (ζ > 1): у Apple bounce лежит от −1 до 1, ноль — критическое демпфирование;
- `duration = response = 2π / ω_n` — период колебания без трения: SwiftUI переводит длительность в жёсткость как `stiffness = (2π ÷ duration)²` (источники и проверка — `04-spring-tokens-transitions-platforms.md` §2.1);
- относительный перелёт `= exp(−πζ / √(1 − ζ²))`;
- огибающая колебаний падает до 1 % амплитуды за `t₉₉ = −ln(0.01) / (ζ · ω_n)` — оценка, а не время успокоения кривой: у ζ < 1 она расходится с ним до 20 % в обе стороны. Время успокоения (последний выход кривой из полосы 1 % пути) считает сборка ДС — `04-spring-tokens-transitions-platforms.md` §1.2.

Определение duration у Apple, которое часто перевирают: «The **perceptual duration**, which defines the pace of the spring. This is approximately equal to the settling duration, but for very bouncy springs, will be the duration of the period of oscillation» [S27]. Это не «время до остановки».

Comeau описывает те же три параметра словами: масса — «тяжёлый объект движется медленнее, но имеет больше инерции»; tension — «The tighter the spring, the more energy is released, leading to a snappy, bouncy animation»; friction — «the force that dampens the motion… High-friction springs are useful for creating buttery-smooth molasses motion that doesn't bounce around» [S33]. Его пример «приятной» комбинации из песочницы: `{ mass: 1.75, tension: 200, friction: 12 }`.

### 4.3 Пружины Material 3 Expressive

Архитектура: **6 пружин = 2 категории × 3 скорости**, и две схемы (standard и expressive).
- **spatial** — всё, что меняет форму или границы компонента (положение, размер, морфинг);
- **effects** — всё, что форму не меняет (цвет, альфа).

Комментарий в `MotionScheme.kt`: standard-схема «for utilitarian UI elements and recurring interactions, provides a linear motion feel»; expressive «recommended for prominent UI elements and hero interactions» [S11].

Значения (mass = 1.0, параметры Compose: dampingRatio ζ, stiffness k):

| Спека | ζ standard | k standard | ζ expressive | k expressive |
|---|---|---|---|---|
| default spatial | 0.9 | 700 | 0.8 | 380 |
| fast spatial | 0.9 | 1400 | 0.6 | 800 |
| slow spatial | 0.9 | 300 | 0.8 | 200 |
| default effects | 1.0 | 1600 | 1.0 | 1600 |
| fast effects | 1.0 | 3800 | 1.0 | 3800 |
| slow effects | 1.0 | 800 | 1.0 | 800 |

**Ключевое наблюдение: effects-пружины у standard и expressive идентичны и всегда критически задемпфированы (ζ = 1.0).** Цвет и прозрачность не пружинят никогда, даже в «выразительной» схеме. Пружинит только геометрия. То же говорит Comeau: «Springs are most impactful when it comes to **motion**; I wouldn't use them for color or opacity changes» [S33].

Пересчёт в веб-величины (m = 1, полоса 1 % пути): t₉₉ — оценка по огибающей (§4.2), время CSS — время успокоения кривой, которое выводит сборка ДС (`04-spring-tokens-transitions-platforms.md` §1.2) `[проверено: расчёт ds_build]`:

| Спека | ω_n, рад/с | t₉₉ огибающей, ms | время CSS, ms | Перелёт, % |
|---|---|---|---|---|
| standard default spatial | 26.5 | 193 | 200 | 0.15 |
| standard fast spatial | 37.4 | 137 | 140 | 0.15 |
| standard slow spatial | 17.3 | 295 | 300 | 0.15 |
| default effects (обе схемы) | 40.0 | 166 | 170 | 0 |
| fast effects (обе схемы) | 61.6 | 108 | 110 | 0 |
| slow effects (обе схемы) | 28.3 | 235 | 240 | 0 |
| expressive default spatial | 19.5 | 295 | 330 | 1.5 |
| expressive fast spatial | 28.3 | 271 | 230 | **9.5** |
| expressive slow spatial | 14.1 | 407 | 450 | 1.5 |

Перелёт 0.15 % у standard spatial лежит внутри полосы 1 %: кривая CSS успокаивается раньше пика и перелёта не показывает.

Вывод: по времени пружины M3 укладываются в 110–450 ms, то есть в ту же вилку, что и кривые. **Разница не в скорости, а в характере**: expressive fast spatial даёт ≈ 9.5 % перелёта.

### 4.4 Пружины Apple

Сигнатуры прямо из документации SwiftUI [S27]:
- `spring(response: 0.5, dampingFraction: 0.825, blendDuration: 0)`
- `smooth(duration: 0.5, extraBounce: 0.0)` — «base bounce of **0**»
- `snappy(duration: 0.5, extraBounce: 0.0)` — «base bounce of **0.15**»
- `bouncy(duration: 0.5, extraBounce: 0.0)` — «base bounce of **0.3**»

Пересчёт (m = 1; время CSS — успокоение кривой до 1 % пути, как его выводит сборка ДС) `[проверено: расчёт ds_build]`:

| Пресет | duration | bounce | ζ | k | t₉₉ огибающей, ms | время CSS, ms | Перелёт, % |
|---|---|---|---|---|---|---|---|
| smooth | 0.5 s | 0 | 1.00 | 158 | — | 530 | 0 |
| snappy | 0.5 s | 0.15 | 0.85 | 158 | 431 | 360 | 0.6 |
| bouncy | 0.5 s | 0.3 | 0.70 | 158 | 524 | 530 | 4.6 |

У критически демпфированной пружины огибающей нет; её время успокоения 528 ms и есть «perceptual duration» 0.5 s в определении Apple: «approximately equal to the settling duration». Сама SwiftUI считает `settlingDuration` строже — до 0,1 % (`epsilon` 0.001, `04-spring-tokens-transitions-platforms.md` §4.3): у `smooth` это 735 ms.

Все три системные пружины Apple — **около полусекунды по воспринимаемому темпу**, заметно медленнее веб-практики (≤ 300 ms по Kowalski). Причина — тач-экран: движение крупнее, его надо отследить взглядом. Переносить значения Apple в веб-сервис на десктопе нельзя, переносить структуру (три именованных пресета: без перелёта / слабый / заметный) — можно и нужно.

### 4.5 Официальная таблица M3 «пружина → cubic-bezier + длительность» для веба

Извлечена из HTML страницы спеков M3 (сентябрь 2026) [S24]. Это готовый инструмент: если пружина нужна, но проект на CSS-переходах, берётся строка целиком.

| Пружина | cubic-bezier | Длительность |
|---|---|---|
| Expressive fast spatial | `0.42, 1.67, 0.21, 0.90` | 350 ms |
| Expressive default spatial | `0.38, 1.21, 0.22, 1.00` | 500 ms |
| Expressive slow spatial | `0.39, 1.29, 0.35, 0.98` | 650 ms |
| Expressive fast effects | `0.31, 0.94, 0.34, 1.00` | 150 ms |
| Expressive default effects | `0.34, 0.80, 0.34, 1.00` | 200 ms |
| Expressive slow effects | `0.34, 0.88, 0.34, 1.00` | 300 ms |
| Standard fast spatial | `0.27, 1.06, 0.18, 1.00` | 350 ms |
| Standard default spatial | `0.27, 1.06, 0.18, 1.00` | 500 ms |
| Standard slow spatial | `0.27, 1.06, 0.18, 1.00` | 750 ms |
| Standard fast effects | `0.31, 0.94, 0.34, 1.00` | 150 ms |
| Standard default effects | `0.34, 0.80, 0.34, 1.00` | 200 ms |
| Standard slow effects | `0.34, 0.88, 0.34, 1.00` | 300 ms |

Что здесь важно:
- **Все spatial-кривые имеют y₁ > 1** (1.06…1.67), то есть перелёт зашит прямо в кривую. Expressive fast spatial `1.67` — самый сильный.
- **Standard spatial: одна и та же кривая `(0.27, 1.06, 0.18, 1.00)` на всех трёх скоростях**, отличаются только длительности 350 / 500 / 750 ms. Это подтверждает, что характер задаётся кривой, а темп — длительностью.
- **Effects-кривые у standard и expressive совпадают полностью**, y ≤ 1, перелёта нет. Полностью согласуется с ζ = 1.0 в исходниках.
- **Длительности конвертации (150–750 ms) заметно больше расчётного времени затухания пружин (110–410 ms)**: `cubic-bezier` догоняет «хвост» пружины дольше. Значит, при переводе пружины в кривую время растёт примерно в 1.5–1.8 раза.

### 4.6 Конфликт: перелёт нужен или запрещён

| Позиция | Кто | Формулировка |
|---|---|---|
| **Запрещён** | IBM Carbon | «Avoid easing curves that are unnatural, distracting, or purely decorative… **Do not use easing curves that suggest bounce, stretch, or sudden stops**» [S22] |
| **Требуется** | Material 3 Expressive | все spatial-кривые с перелётом до 67 %; expressive fast spatial даёт 9.5 % физического перелёта [S24], [S11] |
| **Допустим точечно** | Ant Design | `easeOutBack` и `easeInBack` есть в токенах, но в компонентах почти не применяются [S8] |
| **Вынесен в отдельный токен** | Atlassian | `easing.spring` = `linear()` из 65 точек [S14]; в документации переходы компонентов — на `practical` и `bold` [S25], а в пакете `@atlaskit/tokens` 20.8.2 пружина стоит в токене компонента `avatar.hovered` (помечен `experimental`, перелёт 2,4 %) [S60] |
| **Осторожно** | Polaris | готовый keyframe `bounce` есть (scale 1 → 0.85 → 1.05 → 1), но применяется к индикаторам, а не к переходам [S2] |

Это не «одни правы, другие нет», а разные продукты. Разрешение для базы:
- **Плотная админка, бэк-офис, инструмент для профессионала** — перелёта нет. Carbon прав: движение должно оставаться незамеченным.
- **Клиентский сервис, мобильное приложение, онбординг** — перелёт 3–10 % допустим на одном-двух ключевых элементах (переключатель, подтверждение, добавление в корзину).
- **Никогда**: перелёт на элементах, которые пользователь видит десятки раз за сессию (строки таблицы, вкладки, пункты меню).

Сведения, а не нормы:
- Пружина Atlassian на наведении аватара (`avatar.hovered`, 20.8.2, `experimental`) — единственный найденный случай перелёта в
  токене компонента; с разрешением выше он расходится (наведение — частое действие), правило из одного токена не выводится [S60].
- Детекторы примет считают перелётом разное: Hallmark 2.0.0 флагует кривую с y > 1.05 на состояниях интерфейса — под порог
  попадает и официальная кривая M3 standard spatial `(0.27, 1.06, 0.18, 1.00)` (§4.5) [S61]; правило `bounce-easing` Impeccable
  4.8.0 — имена bounce, elastic, wobble и кривые с y вне [−0.1; 1.1]: standard spatial оно пропускает, expressive spatial (y₁
  1.21–1.67) ловит [S65]. Находка детектора — сигнал проверить тип продукта, норма — разрешение выше `[мнение вендора]`.

### 4.7 Пружина в чистом CSS: `linear()`

**Статус: Baseline Newly available с декабря 2023, Widely available с июня 2026** [S19] (Chrome 113, Firefox 112, Safari 17.2; сверено с `../../creative/07-stack-implementation/01-stack-choice.md` §3.1). Пружину можно записать в CSS без JS.

Синтаксис: `linear(0, 0.25, 1)`, `linear(0, 0.25 75%, 1)`, `linear(0, 0.5 25% 75%, 1)`. Минимум два значения; 0 — начало, 1 — конец; значения вне [0, 1] разрешены — это и даёт перелёт. Механика — кусочно-линейная интерполяция между точками; без процентов точки распределяются равномерно [S19].

Числа, важные для практики [S48]:
- **11 точек мало**: ручная трассировка пружины по 11 значениям даёт видимое движение «рывками между дискретными точками».
- Реальные пружины: **40+ точек**; Easing Wizard в максимальной точности — в среднем **75 точек**.
- Расширенный синтаксис с процентами ужимает: та же пружина в **25 точках вместо 50**.
- **Вес**: три пружины максимальной точности (в среднем 75 значений) добавили к CSS-бандлу **≈ 1.3 КБ** (бандл 67.1 КБ, в gzip 11.5 КБ). На 3G это 5 ms загрузки.
- **Частота кадров от сложности `linear()` не страдает**: замер `linear(0, 1)` против строки со 100+ значений разницы не дал.

**Главное ограничение — прерывания.** «CSS transitions have special logic for handling interrupts… the **reversing shortening factor** that proportionally reduces the duration of interrupted transitions. So, a spring intended to take **1600 ms might re-run at only 400 ms**. This looks fine with Bézier curves, but we're trying to emulate physics here» [S48]. То есть `linear()`-пружина при быстром переключении туда-сюда ведёт себя не как пружина.

Второе ограничение: **длительность — часть кривой**. Точки `linear()` разложены по времени успокоения: та же строка с другой длительностью — другая пружина. Генератор Арчибальда выводит длительность из параметров пружины («based on how much time is necessary until the spring settles down»); Easing Wizard берёт её отдельным параметром и внутренне зажимает остальные, чтобы кривая оставалась возможной [S48]. Пружину с нулевым трением смоделировать нельзя.

**В ДС пружина — токен с параметрами**, а не строка: токен `transition` с расширением `org.design-deep-dive.spring` (`dampingRatio`, `stiffness`), из которого сборка выводит и строку `linear()`, и время успокоения, а параметры повторяет комментарием в CSS (`04-spring-tokens-transitions-platforms.md` §1). `@supports`-запас сборка не выводит: функция в Baseline Widely available; запас для инструментов без расширения — `$value` токена.

Способ хранения строки вне ДС — прототип, лабораторная страница (Comeau, адаптировано):

```css
:root {
  /* Фоллбэк для браузеров без linear() */
  --spring-smooth: cubic-bezier(0.27, 1.06, 0.18, 1);
  --spring-smooth-time: 500ms;
}

@supports (animation-timing-function: linear(0, 1)) {
  :root {
    /* stiffness: 235, damping: 10, mass: 1 — записывай параметры в комментарий,
       иначе строку потом нечем пересобрать */
    /* prettier-ignore */
    --spring-smooth: linear(0, 0.007, 0.029 2.2%, 0.118 4.7%, /* … 40+ точек … */ 1);
  }
}

.panel { transition: transform var(--spring-smooth-time) var(--spring-smooth); }
```

Инструменты: **linear-easing-generator.netlify.app** (Jake Archibald и Adam Argyle, упомянут прямо в MDN; «comes pre-loaded with all of the math required to convert spring parameters into a highly-optimized `linear()` string») и **easingwizard.com** (параметры stiffness/damping/mass, пружины, отскоки, wiggle) [S19], [S48].

Ещё один живой пример: **Atlassian хранит пружину именно так** — токен `easing.spring` = `linear(0, 0.021, 0.058, …, 1)` из 65 точек [S14].

### 4.8 Когда пружина оправдана в веб-сервисе

| Уместно | Не уместно |
|---|---|
| перетаскивание (drag) и его отпускание | смена цвета, прозрачности, границы |
| свайп-жесты на тач-экране | появление модалки в админке |
| переключатель (switch), чекбокс с «щелчком» | раскрытие строки таблицы |
| подтверждение редкого важного действия | любая анимация, которую видят чаще пяти раз за сессию |
| значения, привязанные к позиции курсора | функциональный график (Kowalski: «If this was a functional graph, in a banking app for example, **no animation would be better**») [S15] |

---

## 5. Масштабирование длительности

### 5.1 От расстояния

Реальная формула из библиотеки MUI (`getAutoHeightDuration`, применяется к раскрытию `Collapse`) [S9]:

```
constant = height / 36
duration = min( round( (4 + 15 · constant^0.25 + constant / 5) · 10 ), 3000 )   // ms
```

Проверка по точкам:

| Расстояние, px | Длительность, ms | Прирост |
|---|---|---|
| 36 | 192 | — |
| 100 | 239 | +24 % при росте пути в 2.8 раза |
| 300 | 311 | +30 % при росте пути в 3 раза |
| 600 | 376 | +21 % при удвоении |
| 1200 | ≈ 455 | +21 % при удвоении |

**Длительность растёт как корень четвёртой степени от расстояния: удвоение пути добавляет ≈ 19–21 % времени, а не удваивает его.** Это ключевая числовая модель для правила «масштабируй длительность от дистанции».

То же правило словами у Carbon: «the larger the change in distance (traveled) or size (scaling) of the element, the longer the animation takes… Carbon uses a **non-linear duration scale** to achieve better perceived consistency across all distances» [S22]. Инструмент IBM: `ibm.github.io/motion/`. И у Atlassian: «**Larger elements generally require longer durations to feel proportional**» [S23].

Практический перевод для веб-сервиса: возьми базовые 200 ms для перемещения на 100 px и меняй по таблице, а не пропорционально.

### 5.2 От размера элемента

Carbon в разделе хореографии даёт полезную формулировку: раскрытие строки таблицы и открытие дропдауна имеют один смысл, значит одинаковые личность и кривая, «however, they should use slightly **different durations due to their difference in size**» [S52]. То есть при одинаковой семантике длительность разводится по габариту, а не по компоненту. То же у Fluent 2 (крупному — дольше, мелкому — короче) [S62] и у пружин Material 3: скорость fast — переключатель и кнопка, default — нижняя панель и дровер, slow — полноэкранное (`02-what-to-animate-in-apps.md` §1) [S59].

### 5.3 Одна ручка на весь продукт

Ant Design — единственная из изученных систем, где скорость интерфейса это один токен: `motionUnit: 0.1`, далее `Fast = unit`, `Mid = unit × 2`, `Slow = unit × 3`. Смена `motionUnit` на 0.08 ускоряет весь продукт на 20 % разом. Плюс глобальный флаг `motion: true` выключает движение целиком [S8].

Честная цитата из исходника интерфейса токенов Ant (`components/theme/interface/seeds.ts`, строка 198):
`// TODO: 缺一个懂 motion 的人来收敛 Motion 相关的 Token` — «не хватает человека, который разбирается в motion, чтобы свести токены движения». Даже крупная система признаёт, что её набор движения не систематизирован [S8].

Аналог у Mantine: `respectReducedMotion: false` в дефолтной теме — один флаг на весь продукт [S13, через F-notes S16].

---

## 6. Что реально применяется: измерения 24 живых продуктов

Метод: computed styles через headless-браузер (утилита агента P, `../../scripts/ui/measure_ui.py`), 24 продукта на 1440 × 900, ключи `motion.transition_duration` и `motion.transition_easing`. Продукты: Ant Pro, Cal.com, Carbon DataTable, Consta, Discourse, Excalidraw, Gitea, GitHub (issues и repo), GitLab, Grafana, Gravity UI, Mantine, Matomo, MUI dashboard, phpMyAdmin, Plausible, Primer, Radix Themes, Redmine, shadcn dashboard, Stripe Docs, tldraw, Vercel Geist. Полный разбор — `../99-raw/notes/wave2/M-notes.md` §S56, атлас практики — `../10-design-systems-atlas/`.

### 6.1 Длительности: 1576 объявлений

| Значение | Объявлений | Доля |
|---|---|---|
| **200 ms** | 429 | **27.2 %** |
| **150 ms** | 416 | **26.4 %** |
| **300 ms** | 255 | **16.2 %** |
| 33.3 ms | 159 | 10.1 % |
| 100 ms | 82 | 5.2 % |
| 70 ms | 49 | 3.1 % |
| 120 ms | 49 | 3.1 % |
| 80 ms | 42 | 2.7 % |
| 250 ms | 32 | 2.0 % |
| 0 ms | 21 | 1.3 % |
| 140 ms | 18 | 1.1 % |
| 400 ms | 8 | 0.5 % |
| 500 ms | 7 | 0.4 % |
| остальное (320, 110, 225, 180, 240, 3000) | 7 | 0.4 % |

Выводы:
1. **Три значения (150, 200, 300 ms) покрывают 70 % всех переходов в вебе.** Шкала из шести длительностей — не упрощение, а описание реальности.
2. **Длиннее 300 ms — 1.4 % объявлений.** Единственные 3000 ms — у холста tldraw, то есть не интерфейс.
3. Модальная длительность по продуктам: 200 ms у 6 продуктов, 300 ms у 5, 150 ms у 3. Тяжеловесные системы (Ant, MUI, Stripe) стоят на 300, лёгкие (shadcn, Cal.com, Consta) — на 150.
4. Аномалия: 33.3 ms × 159 — целиком из Primer, в паре с `linear`. Это ровно 2 кадра при 60 fps; в опубликованных токенах Primer такого значения нет (там 0, 50, 100, 200…). Пример расхождения токенов и реализации.
5. Carbon DataTable держит 70 ms на 49 из 52 объявлений — это `duration-fast-01` из токенов, применённый буквально. Самый дисциплинированный продукт выборки.

### 6.2 Кривые: 1576 объявлений

| Кривая | Доля |
|---|---|
| **`ease` (дефолт CSS)** | **34.7 %** |
| `cubic-bezier(0.4, …)` — M2/Tailwind standard | 27.0 % |
| `linear` | 11.1 % |
| `ease-in-out` | 8.3 % |
| `cubic-bezier(0, …)` — decelerate-семейство | 3.7 % |
| `ease-out` | 1.9 % |
| `ease-in` | 0.8 % |
| прочие именные cubic-bezier | ≈ 12 % |

**Главное противоречие практики и деклараций:** все дизайн-системы пишут «вход — ease-out, выход — ease-in», а в живых продуктах `ease` (браузерный дефолт) встречается **в 18 раз чаще**, чем `ease-out`. Объяснение то же, что у Kowalski: встроенные кривые «not strong enough», поэтому их либо заменяют на собственный `cubic-bezier` (27 % — это в основном `0.4, 0, 0.2, 1`), либо не трогают вовсе.

Практический вывод для генеративной системы: **не рассчитывай, что кривые применятся сами**. Если токены кривых объявлены, но компоненты пишут `transition: all 150ms`, эффекта не будет: `all` без указания функции даёт `ease`. Проверка на это — в `../13-evaluation-checklists/` (волна 3), а пока в чек-листе §10.

---

## 7. Токены движения

### 7.1 Как их называют системы

| Система | Имя длительности | Имя кривой |
|---|---|---|
| Material 3 | `md.sys.motion.duration.short2` | `md.sys.motion.easing.emphasized-decelerate` |
| Polaris | `--p-motion-duration-150` | `--p-motion-ease-out` |
| Fluent 2 | `durationNormal` | `curveDecelerateMid` |
| Carbon | `$duration-moderate-01` | `$ease-entrance` (productive / expressive) |
| Primer | `--base-duration-200` | `--base-easing-easeOut` |
| Atlassian | `motion.duration.short` | `motion.easing.out.bold` |
| Tailwind v4 | `--default-transition-duration` | `--ease-out` |
| Ant | `motionDurationMid` | `motionEaseOut` |

Именование по правилам W3C DTCG и Nathan Curtis (см. `../09-design-tokens/`, агент F): категория + свойство + модификатор, без сокращений, числовой шаг не 1-2-3, а с запасом. Для длительностей числовое имя (`duration-150`) удобнее ролевого при генерации кода, ролевое (`duration-short`) — при ручной работе. Компромисс: ролевое имя + число в `$description`.

### 7.2 Типы DTCG

Формат Design Tokens Community Group 2025.10 (подробности — `../09-design-tokens/02-dtcg-format-and-tooling.md`, агент F) даёт три типа, которые нужны движению:

| `$type` | Значение | Пример |
|---|---|---|
| `duration` | объект `{value: number, unit: "ms" | "s"}` | `{"value": 150, "unit": "ms"}` |
| `cubicBezier` | массив из 4 чисел `[P1x, P1y, P2x, P2y]`, x в [0, 1], **y любые** (перелёт легален) | `[0, 0, 0.2, 1]` |
| `transition` (составной) | `{duration, delay, timingFunction}` | см. §7.4 |

Чего в спецификации нет: **типа для пружины и для keyframes**. Material в своём генераторе на этом уже споткнулся: тип `motion_path` в веб-экспорте выдаёт `null` [S1]. Atlassian кладёт пружину `linear()` строкой в собственный формат, не DTCG. ДС скилла пишет пружину параметрами в расширении `org.design-deep-dive.spring` токена `transition`, строку собирает сборка (`04-spring-tokens-transitions-platforms.md` §1.1).

### 7.3 Сколько токенов нужно

По промту и по практике систем:

| Категория | Минимум | Комфорт | Избыток |
|---|---|---|---|
| Длительности | 4 (100 / 150 / 250 / 400) | **6** (0 / 100 / 150 / 200 / 300 / 400) | 12+ (Polaris, Primer), 16 (Material) |
| Кривые | 3 (standard / entrance / exit) | **4** (+ linear) | 9 (Fluent), 8 (Ant) |
| Пружины | 0 | **2** (spatial default + spatial fast; по поверхности — `04-spring-tokens-transitions-platforms.md` §1.5) | 6 (Material 3) |
| Семантические связки | 0 | **8–12** (`motion.popup.enter`, `motion.modal.exit`…) | 72 (Atlassian) |

Готовый набор с JSON и CSS — в `03-reduced-motion-and-motion-tokens.md` §4–§6.

### 7.4 Семантические токены движения

Самый зрелый пример — Atlassian: токен упаковывает длительность, кривую, свойства и направление [S25]:

- Interactions: `motion.avatar.hovered`, `motion.avatar.pressed`.
- Transitions: `motion.flag.reposition`, `motion.avatar.enter/exit`, `motion.blanket.enter/exit`, `motion.flag.enter/exit`, `motion.modal.enter/exit`, `motion.spotlight.enter/exit`, и **`motion.popup.enter.{top,bottom,left,right}`** плюс `motion.popup.exit.{…}` — у поповера четыре направления, направление входа выбирается по положению относительно триггера.

Ключевые кадры тоже зафиксированы токенами: `motion.keyframe.scale.in.small` = **95 → 100 %**, `motion.keyframe.scale.out.small` = 100 → 95 %; fade 0 → 100 % и 100 → 0 % [S25]. Всего 18 токенов `motion.keyframe.*` и 72 токена движения из 596 в системе [S14].

Формулировка смысла у Atlassian: «named bundles that encode context, motion type, and tempo… **choose motion by intent rather than raw values**».

Второй пример — Polaris, где keyframes лежат прямо в токенах: `bounce`, `fade-in`, `pulse`, `spin`, `appear-above`, `appear-below`. Важная деталь: смещение появления задаётся ссылкой на токен отступа `--p-space-100` (= 4 px), то есть **движение привязано к шкале отступов, а не к произвольным пикселям** [S2]. Это правило стоит перенять: сдвиг при появлении берётся из шкалы 4 / 8 / 12, а не «на глаз».

---

## 8. Принципы, к которым сводятся числа

### 8.1 Чек-лист Carbon (переведён в вопросы)

Carbon формулирует четыре критерия оценки движения [S22]:
1. **Purposeful**: какую задачу решает движение? помогает ли понять действие?
2. **Responsive**: получают ли действия немедленную обратную связь? используют ли микровзаимодействия `ease-out` на ввод пользователя? **укладываются ли микровзаимодействия в 90–120 ms?** есть ли непрерывные элементы в крупных переходах?
3. **Meticulous**: верные ли кривые? согласованы ли связанные движения? работает ли на всех размерах экрана?
4. **Unobtrusive**: «The best interface motion may go unnoticed… **Is your motion frequently noticed by average users? If so, consider removing or minimizing it.**»

### 8.2 Вопрос Atlassian

«Before adding motion ask, **if I remove this, does the user lose information or context?**» И: «Don't make users wait without reason. **Avoid motion that blocks the next step in a flow**» [S23].

### 8.3 Доступность внутри самого движения

Atlassian: «Move focus and trigger screen-reader announcements **at the start** of the animation»; «Don't gate critical feedback such as errors or focus states behind a slow entrance» [S25]. То есть фокус переезжает в модалку в момент запуска её анимации, а не после. Это же объясняет, почему у них `motion.duration.instant` = 0 для фокуса.

### 8.4 Формулировки Apple

- «Add motion purposefully… Don't add motion for the sake of adding motion. Gratuitous or excessive animation can distract people and may make them feel disconnected or physically uncomfortable.»
- «Make motion optional… avoid using it as the only way to communicate important information.»
- «**Aim for brevity and precision in feedback animations.** When animated feedback is brief and precise, it tends to feel lightweight and unobtrusive, and it can often convey information more effectively than prominent animation.»
- «Consider using **fades** when you need to relocate an object… you can fade the object out before moving it and fade it back in after it's in the new location.» — готовый приём замены перемещения на затухание.
- Про частоту колебаний (из раздела visionOS, но переносимо): «Avoid showing objects that oscillate in a sustained way. In particular, you want to avoid showing an oscillation that has a frequency of around **0.2 Hz** because people can be very sensitive to this frequency.» 0.2 Hz — это период 5 секунд. Практический вывод: **цикл «дыхания» скелетона или пульсации не должен иметь период ≈ 5 с** [S12].

### 8.5 Пять признаков хорошей анимации по Kowalski

Natural, Fast, Purpose, Performant, Interruptible, Accessible, «Feel right» [S14]. Числовые следствия уже разнесены по разделам выше; здесь важно одно наблюдение, которое не сводится к числу: Sonner (библиотека тостов того же автора) специально «a bit slower than usual and uses `ease` as the easing type rather than `ease-out` to make it feel more elegant». То есть у тостов, которые пользователь не запрашивал, замедление осознанное.

---

## 9. Частые ошибки

### 9.1 Общие

1. **`transition: all`.** Анимируются свойства, которых не планировали (в том числе `height`, `width`, `top`), кривая падает в `ease`, стоимость кадра растёт. Перечисляй свойства явно.
2. **Одна длительность на всё.** 200 ms одинаково плохи для hover кнопки (слишком долго) и для дровера (слишком быстро).
3. **Симметричные вход и выход у оверлея.** Выход должен быть на 50–100 ms короче (§3.1).
4. **Длительность, не зависящая от расстояния.** Тост на 300 px и панель на 900 px за одно и то же время читаются как разные скорости (§5.1).
5. **Перелёт в рабочем интерфейсе.** Carbon запрещает прямо (§4.6).
6. **Анимация фокуса.** Кольцо фокуса должно появляться в том же кадре (§1.2).
7. **Анимация действий с клавиатуры.** Командное меню, переключение вкладок, переходы по списку (§3.4).
8. **`@keyframes` там, где нужно прерывание.** Открыли-закрыли поповер быстрее анимации — он «доигрывает» (§3.3).
9. **Задержка перед показом состояния загрузки, реализованная как анимация.** Задержка (200–400 ms) и анимация (150 ms) — разные вещи; смешивать нельзя, UX-часть в `../../ux/06-feedback-states-motion/`.
10. **Пружина на цвете.** M3 и Comeau сходятся: effects не пружинят (§4.3).

### 9.2 Характерные для нейросетей

11. **`transition-duration: 0.3s` везде.** Модель воспроизводит самое частое значение из обучающих данных (Bootstrap и старый Material). В измерениях 300 ms действительно третья по частоте, но у Ant и MUI, а не у современных систем. Проверка: доля объявлений 300 ms не должна превышать 20 %.
12. **`animate-bounce`, `animate-pulse` и `animate-ping` из Tailwind на боевых элементах.** Это демонстрационные утилиты; `animate-bounce` на кнопке «Купить» — маркер сгенерированного интерфейса.
13. **Анимация появления каждого блока при прокрутке (scroll reveal).** В веб-сервисе за авторизацией её не бывает; это паттерн лендинга. Дополнительно нарушает WCAG 2.2.2 и 2.3.3 (§`03-reduced-motion-and-motion-tokens.md` §2).
14. **Параллакс и «плавающие» градиентные пятна на фоне админки.**
15. **Длительность вида `0.35s`, `0.45s`, `0.65s`.** Не из шкалы; при генерации числа берутся «красивые», а не токенные. Проверка: все значения должны быть в объявленном наборе.
16. **`transform: scale(1.05)` на hover карточки.** Ломает выравнивание соседних карточек, не входит ни в одну из изученных систем и особенно заметен в плотной сетке. Подъём карточки решается тенью и смещением 1–2 px, см. `../04-shape-elevation/02-shadows-layers-depth.md`.
17. **Отсутствие `prefers-reduced-motion` вообще.** См. отдельный файл.
18. **Анимация `height`, `width`, `top`, `margin`.** Layout-свойства, каждый кадр пересчитывает раскладку (§`02-what-to-animate-in-apps.md` §4).
19. **Кривая с перелётом, взятая из примера M3 Expressive, применённая к строкам таблицы.**
20. **Дублирование строки `linear()` из 60 значений в каждом правиле** вместо одной переменной (§4.7).

---

## 10. Чек-лист

1. Все длительности берутся из объявленного набора из 4–6 значений? Постороннее число вроде `0.35s` в коде отсутствует?
2. Дефолтная длительность перехода — 150 ms (или осознанно другая и записана в токен)?
3. Hover и press укладываются в 50–150 ms?
4. Фокус-кольцо появляется без анимации (0 ms)?
5. Есть ли хоть одна анимация длиннее 400 ms? Если да, это полноэкранный переход, онбординг или затемнение фона?
6. Выход оверлея короче входа на 50–100 ms?
7. Каждая кривая указана явно (не полагается на дефолтный `ease` из `transition: all`)?
8. Роли кривых соблюдены: вход decelerate, выход accelerate, перемещение внутри экрана ease-in-out, цикл linear?
9. Есть ли в интерфейсе перелёт (y > 1 в `cubic-bezier` или bounce > 0 в пружине)? Оправдан ли он типом продукта?
10. Длительность перемещений масштабируется от расстояния (хотя бы двумя ступенями: близко 150–200, далеко 250–350)?
11. Анимации, зависящие от состояния, сделаны через `transition`, а не `@keyframes`?
12. Ни одно действие, запускаемое с клавиатуры, не анимировано?
13. Пружина ДС — токен `transition` с расширением `org.design-deep-dive.spring`, а строка `linear()` и её время — из сборки, а не вписаны руками?
14. Параметры пружины (`dampingRatio`, `stiffness`) записаны в токене, а CSS повторяет их комментарием над переменной?
15. Цвет и прозрачность анимируются без пружины и без перелёта?
16. Есть ли движение, которое средний пользователь замечает? (Carbon: если да, убрать или ослабить.)
17. Токены движения объявлены как `duration` и `cubicBezier` по DTCG, а не строками `"150ms"`?
18. Сдвиг при появлении (`translateY`) взят из шкалы отступов (4 / 8 / 12), а не произвольный?

---

## 11. Открытые вопросы и противоречия

1. **Перелёт: Carbon против M3 Expressive** (§4.6). Не сглажено намеренно: это разные классы продуктов. Требуется решение на уровне брифа («характер продукта»), которое собирает агент G в `../11-styles-trends/` (волна 3).
2. **Асимметрия hover: Comeau против Atlassian** (§3.2). Разрешено разделением на жанры, но экспериментального подтверждения ни у одной стороны нет. `[спорно]`
3. **`ease` в практике против `ease-out` в декларациях** (§6.2). Не найдено ни одного исследования, которое бы сравнивало восприятие. Вопрос к агенту волны 3 (оценка): сделать A/B на двух вариантах одного интерфейса.
4. **Расхождение исходника и документации у Material 3**: в `_md-sys-motion.scss` `easing-emphasized` = `cubic-bezier(0.2, 0, 0, 1)` (то же, что standard), в документации честно написано **N/A**, потому что на Android это составной путь из двух кривых Безье (`M 0,0 C 0.05,0 0.133333,0.06 0.166666,0.4 C 0.208333,0.82 0.25,1 1,1`). В CSS-экспорте подменено. Для веба **emphasized использовать нельзя**, только decelerate/accelerate-варианты [S1], [S24].
5. **Аномалия 33.3 ms у Primer** (§6.1): в опубликованных токенах такого значения нет. Источник не найден; возможно, это анимация спиннера или деталь `@primer/css`. Требует отдельной проверки.
6. **Стоимость `filter` и `backdrop-filter` в анимации** (открытый вопрос агента C): количественных замеров FPS найти не удалось ни у MDN, ни у web.dev (`web.dev/articles/prefers-reduced-motion` недоступен из этой среды). Качественные основания — в `02-what-to-animate-in-apps.md` §4.3.
7. **GOV.UK и движение**: у GOV.UK Design System раздела о движении нет вообще. Проверено перечислением подразделов styles/ (13 штук): colour, font-override-classes, headings, images, layout, links, lists, page-template, paragraphs, section-break, spacing, typeface, type-scale. Движения среди них нет, и объяснения этому в документации тоже нет. Отсутствие раздела само по себе позиция: сервис, который человек посещает раз в год, не нуждается в языке движения.
8. **Apple WWDC 2018 «Designing Fluid Interfaces»** не расшифрован: докачка транскрипта упирается в лимит YouTube; доклад остаётся вторичной ссылкой через Rauno Freiberg [S16]. Из WWDC 2023 «Animate with springs» взяты формулы перевода длительности и отскока в жёсткость и демпфирование и правило «пружина — анимация SwiftUI по умолчанию» (`04-spring-tokens-transitions-platforms.md` §2.1, §4.3); целиком доклад не расшифрован.

---

## Источники

Снимок: 28.10.2026 — день сверки источников S59–S65 и статусов Baseline.

Нумерация сквозная с сырыми заметками `../99-raw/notes/wave2/M-notes.md`.

1. `[S1]` Google. Material Web, `tokens/versions/v0_192/_md-sys-motion.scss`, 2026. https://raw.githubusercontent.com/material-components/material-web/main/tokens/versions/v0_192/_md-sys-motion.scss — автогенерированный исходник токенов M3 для веба; первичный, значения точные.
2. `[S2]` Shopify. Polaris tokens, файл polaris-tokens/src/themes/base/motion.ts, 2026. https://raw.githubusercontent.com/Shopify/polaris/main/polaris-tokens/src/themes/base/motion.ts — исходник с авторскими описаниями кривых и готовыми keyframes; репозиторий в архиве с сентября 2026, Polaris React заменён Web Components, токенов движения там не найдено [S63].
3. `[S3]` Microsoft. Fluent UI v9, `packages/tokens/src/global/durations.ts` и `curves.ts`, 2026. https://raw.githubusercontent.com/microsoft/fluentui/master/packages/tokens/src/global/ — первичный исходник.
4. `[S4]` IBM. `@carbon/motion`, `lib/index.js` (Copyright IBM Corp. 2018, 2026). https://cdn.jsdelivr.net/npm/@carbon/motion/lib/index.js — исходник с JSDoc, где у каждой длительности написано назначение.
5. `[S5]` Tailwind Labs. Tailwind CSS v3.4 `stubs/config.full.js` и v4 `packages/tailwindcss/theme.css`, 2026 — исходники обеих версий; показывают отказ от шкалы длительностей в v4.
6. `[S6]` Atlassian. `@atlaskit/motion`, `utils/durations.js`, `utils/curves.js`. https://cdn.jsdelivr.net/npm/@atlaskit/motion/ — старая система движения, сетка 25 ms.
7. `[S7]` GitHub. `@primer/primitives`, `dist/css/base/motion/motion.css` — исходник с назначением каждой кривой в комментариях.
8. `[S8]` Ant Design 5. `components/theme/themes/seed.ts`, `shared/genCommonMapToken.ts`, `interface/seeds.ts` — вычисляемые длительности и честный TODO о несистематизированности движения.
9. `[S9]` MUI. `packages/mui-material/src/styles/createTransitions.js` — формула «длительность от расстояния» и пара enteringScreen/leavingScreen.
10. `[S10]` Radix Themes. Листинг `packages/radix-ui-themes/src/styles/tokens` через GitHub API — доказательство отсутствия токенов движения.
11. `[S11]` Google. androidx Compose Material3: `MotionScheme.kt`, `tokens/StandardMotionTokens.kt`, `tokens/ExpressiveMotionTokens.kt` (VERSION v0_14_0) — значения шести пружин M3 Expressive.
12. `[S12]` Apple. Human Interface Guidelines: Motion (JSON-API документации), 2026. https://developer.apple.com/tutorials/data/design/human-interface-guidelines/motion.json — формулировки принципов, числовых токенов нет.
13. `[S13]` Mantine. `packages/@mantine/core/src/components/Transition/transitions.ts` — набор именованных переходов с числами смещений.
14. `[S14]` Emil Kowalski. «Great Animations», emilkowal.ski/ui/great-animations — практик (Vercel, Linear, автор Sonner и Vaul); правило «короче 300 ms», прерываемость, производительность.
15. `[S15]` Emil Kowalski. «Good vs Great Animations» — origin-aware поповеры, сила встроенных кривых, clip-path вместо двух параллельных анимаций.
16. `[S16]` Rauno Freiberg. «Invisible Details of Interaction Design», rauno.me/craft/interaction-design, 2023 — прерываемость, частота и новизна, разбор macOS.
17. `[S17]` Val Head. «Designing Safer Web Animation For Motion Sensitivity», A List Apart, 2015 — база для `prefers-reduced-motion`, три фактора риска, цифры по вестибулярным нарушениям.
18. `[S18]` MDN. `prefers-reduced-motion` — Baseline с января 2020, где пользователь включает настройку в семи ОС.
19. `[S19]` MDN. `linear()` easing function — Baseline Newly available с декабря 2023, Widely available с июня 2026; синтаксис, ссылка на генератор Арчибальда.
20. `[S20]` MDN. `@starting-style` — Baseline 2024; три условия для анимации поповеров и `<dialog>`.
21. `[S21]` W3C. WCAG 2.2, Understanding SC 2.3.3 Animation from Interactions (через web.archive) — уровень AAA, техники C39 и SCR40.
22. `[S22]` IBM. Carbon Design System, Motion: overview — две личности, роли кривых, нелинейная шкала, чек-лист из четырёх критериев.
23. `[S23]` Atlassian Design System. Motion (новая система, 2026, Early Access) — диапазоны 50–150 и 150–400 ms, четыре кривые с назначением.
24. `[S24]` Google. Material 3: Motion overview specs и Easing and duration tokens specs (через headless-браузер) — объявление легаси-системы устаревшей, официальная таблица перевода пружин в кривые.
25. `[S25]` Atlassian Design System. Applying motion — таблицы «токен → компонент», правило «выход короче на 50–100 ms», keyframes 95 ↔ 100 %.
26. `[S26]` Adobe. Spectrum: Motion v5.0.0 (через headless-браузер) — три кривые, шкала 130–500 ms с шагом 30, деление micro/macro.
27. `[S27]` Apple. SwiftUI `Animation.spring/smooth/snappy/bouncy` (JSON-API документации) — сигнатуры, определение perceptual duration.
33. `[S33]` Josh W. Comeau. «A Friendly Introduction to Spring Physics» (обновлено 03.11.2025) — mass/tension/friction, ограничение «springs only from JS», правило «не пружинить цвет».
48. `[S48]` Josh W. Comeau. «Springs and Bounces in Native CSS» — `linear()` на практике: число точек, вес в КБ, reversing shortening factor, шаблон хранения с `@supports`.
49. `[S49]` Smashing Magazine. «The Path To Awesome CSS Easing With The linear() Function», 09.2023 — просмотрено, подтверждает происхождение функции.
52. `[S52]` IBM. Carbon Design System, Motion: choreography — стаггер 20 ms и потолок 500 ms, порядок появления контента из пяти категорий.
54. `[S54]` Josh W. Comeau. «An Interactive Guide to CSS Transitions» — 16.6 ms на кадр, `will-change` и субпиксельный рендер, action-driven motion (125/450 ms), `transition-delay` 300 ms.
56. `[S56]` Собственный пересчёт измерений агента P: `../99-raw/cache/measurements/*_1440x900.json`, 24 продукта, 1576 объявлений `transition-duration`. Метод и ограничения — `../99-raw/notes/wave2/P-notes.md`.
59. `[S59]` Google. Material 3: material-components-android, файл docs/theming/Motion.md, androidx Compose Material3 `MotionScheme.kt` (VERSION v0_14_0) — скорость пружины по размеру компонента; через `../../creative/02-references-moodboards/04-motion-libraries-and-rules.md` §4.1 [S37].
60. `[S60]` Atlassian Design System. https://atlassian.design/foundations/motion и /foundations/motion/applying-motion; `@atlaskit/tokens` 20.8.2, файл artifacts/themes/atlassian-motion.js — пружина с перелётом 2,4 % в `avatar.hovered` (`experimental`); через тот же обзор §4.1 [S41].
61. `[S61]` Hallmark 2.0.0. https://github.com/Nutlope/hallmark: skills/hallmark/references/craft.md §5, gates.md, scripts/sloplint.mjs — запрет перелёта на состояниях интерфейса, порог y > 1.05; через тот же обзор §4.2 [S45] — `[мнение вендора]`.
62. `[S62]` Microsoft. Fluent 2 Motion, https://fluent2.microsoft.design/motion (страница правил читается) — длительности по размеру, `linear` только у вращения, смена страницы затуханием; через тот же обзор §4.1 [S40].
63. `[S63]` Shopify. Polaris, `polaris.shopify.com/content/design/motion/*.mdx` в архиве репозитория Shopify/polaris (архив с сентября 2026; polaris-react.shopify.com — соединение рвётся) — роли кривых: ease — действия пользователя, ease-in-out — системные; через тот же обзор §4.1 [S42].
65. `[S65]` Impeccable 4.8.0. https://github.com/pbakaus/impeccable: skill/reference/animate.md, crates/core/src/checks/rules.rs — правило детектора `bounce-easing`; через тот же обзор §4.2 [S46] — `[мнение вендора]`.
