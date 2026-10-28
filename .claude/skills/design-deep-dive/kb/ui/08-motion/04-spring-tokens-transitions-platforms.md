# Пружины как токены, переходы по шаблонам интерфейса и их перевод на веб, Compose и SwiftUI

Движение кабинета, экранов и мобильного приложения как часть дизайн-системы: пружина — токеном, который сборка ДС
переводит в CSS, а код — в Compose и SwiftUI; переходы шаблонов интерфейса — токенами ДС с поведением при сокращённом
движении и реализацией на трёх платформах; показ и проверка этого движения на этапе дизайна. Облик, в том числе
движение, живёт в слое дизайна и в ДС: в экранах, interface и мобильном слое проекта его нет (`CLAUDE.md` §3), поэтому
переходы экранов описывает ДС, а не слой экранов.

Смежные файлы: длительности, кривые и физика пружин — `01-durations-easings-springs.md`; каталог «компонент → движение»
— `02-what-to-animate-in-apps.md`; сокращённое движение и набор токенов — `03-reduced-motion-and-motion-tokens.md`;
схема токенов — `../09-design-tokens/04-reference-token-schema.md` §2.10; когда переход экрана нужен — `../../ux/06-feedback-states-motion/03-motion-and-microinteractions.md`
§4; движение страниц сайта — `../../creative/05-motion/`, пружина прогресса прокрутки — `../../creative/05-motion/01-motion-principles-and-access.md`
§7.3 и `../../3d/16-js-scenes/02-stage-runtime.md` §4. Сборка — `../../../scripts/project/ds_build.py`. Факты платформ
сверены в день снимка (источники и снимок — в конце файла).

## Выжимка для агента

1. **Пружина в ДС — токен `transition` с расширением `$extensions["org.design-deep-dive.spring"]`**: `dampingRatio`
   (ζ) и `stiffness` (k при массе 1, ω = √k). `$value` — переход-запас для инструментов без расширения, его длительность
   равна времени успокоения; значение режима `reduced` — переход без пружины. → §1.1 [мнение] (решение базы: форма
   Material 3 и Compose)
2. **Сборка ДС выводит в CSS `<время успокоения>ms linear(…)`**: время — последний выход кривой из полосы 1 % пути,
   вверх до 10 ms; точки — там, где кривая гнётся, ломаная отходит от неё не больше чем на 0,25 % пути, обычно 21–28
   точек; остаток до цели выбирается плавно на последней четверти; параметры — комментарием над переменной. → §1.2
   [проверено] (самопроверка `ds_build.py`, 14 пружин)
3. **Код получает параметры, а не строку**: токен DTCG — источник темы кода; передняя часть DESIGN.md несёт `x-springs`
   с `response` и `bounce` SwiftUI, перелётом и временем CSS; `ds_build show --json` — то же. В артефакт ДС движение не
   идёт. → §1.3 [проверено]
4. **Пружинит только геометрия от указателя и раскрытия**: положение, размер, масштаб. Цвет и прозрачность — временем
   и кривой, без перелёта; на прогрессе прокрутки — только ζ = 1. → §1.4 [консенсус]
5. **Пружины по поверхности**: кабинет пресета А — нет; пресет Б — одна `motion.spring.snap` (ζ 0.7, k 380: переключатель,
   подтверждение); мобильное приложение — ещё две геометрические Material 3 standard (ζ 0.9, k 700 и 1400). → §1.5
   [система] + [мнение]
6. **Перевод одной формулой**: Compose `spring(dampingRatio = ζ, stiffness = k)`; SwiftUI `response = 2π/ω`,
   `dampingFraction = ζ`, `bounce = 1 − ζ` (у передемпфированной `1/ζ − 1`); физическая тройка — ζ = c / (2√(k·m)),
   k/m; веб — `linear()` сборки. Слайд WWDC23 с формулой демпфирования содержит опечатку. → §2 [проверено: расчёт]
7. **Таблица шаблонов** — смена экрана, модальное окно, нижняя панель, выдвижная панель, вкладки, раскрытие, список,
   скелет, уведомление, отклик, общий элемент: токены и сокращённое движение (§3.1), веб, Compose, SwiftUI (§3.2).
8. **Смена экрана в кабинете — смена области содержимого**: мгновенно или проявлением 150 ms; сдвиг вперёд и назад —
   только у мастера. В мобильном приложении push и pop — системные, свои переходы — токенами. → §3 [мнение]
9. **View Transitions в документе — Baseline с октября 2025** (Chrome 111, Safari 18, Firefox 144): смена маршрута SPA и
   общий элемент — прогрессивным улучшением; при сокращённом движении переход не вызывают. → §4.1 [документация]
10. **Navigation Compose по умолчанию проявляет экран 700 ms** (`tween(700)`) — дольше потолков ДС: переходы `NavHost`
    задают токенами. → §4.2 [исходник]
11. **SwiftUI с iOS 17 анимирует пружиной по умолчанию** (`response` 0.55, ζ 1); `Spring` переводит формы друг в друга,
    `settlingDuration` считает успокоение до 0,1 % — дольше времени CSS сборки. → §4.3 [документация]
12. **Сокращённое движение платформ разное**: веб — режим `reduced` токенов; Android «Убрать анимацию» обнуляет масштаб
    аниматоров, и Compose кончает движение в следующем кадре; iOS «Уменьшение движения» растворяет системные переходы,
    свои — по `accessibilityReduceMotion`. → §4.4 [документация]
13. **На холсте компонент ДС показывает свои переходы в Play** — наведение, нажатие, раскрытие, появление и уход —
    по атрибутам состояния на переменных `system.tokens.css`; при сокращённом движении — конечные состояния. Смена
    экрана — состояниями одного артборда. → §5.1 [практика]
14. **Утилита меряет время, человек — характер**: `ui_audit.py` — `transition: all`, шкала и потолок длительностей,
    доля 300 ms, сокращение без нуля, циклы; кривую, перелёт, что пружинит, прерывание и направление ухода смотрит
    человек в Play. → §5.2, §5.3

---

## 1. Пружина как токен

### 1.1. Форма

Типа пружины в DTCG 2025.10 нет [стандарт] (`01-durations-easings-springs.md` §7.2). ДС пишет пружину расширением токена
`transition`:

```json
"motion": {
  "spring": {
    "$type": "transition",
    "snap": {
      "$value": {
        "duration": { "value": 340, "unit": "ms" },
        "delay": { "value": 0, "unit": "ms" },
        "timingFunction": "{motion.easing.entrance}"
      },
      "$description": "Бегунок переключателя и подтверждение: щелчок с перелётом 4,6 %.",
      "$extensions": {
        "org.design-deep-dive.spring": { "dampingRatio": 0.7, "stiffness": 380 },
        "org.design-deep-dive.modes": {
          "reduced": {
            "duration": "{motion.duration.default}",
            "delay": { "value": 0, "unit": "ms" },
            "timingFunction": "{motion.easing.entrance}"
          }
        },
        "org.design-deep-dive.llm": {
          "usage": ["switch-thumb", "confirm"],
          "rules": "Use for geometry only: transform of the thumb. Do NOT use for color or opacity: they do not spring."
        }
      }
    }
  },
  "switch": { "$type": "transition", "thumb": { "$value": "{motion.spring.snap}" } }
}
```

Почему так:

- **Токен `transition`, а не кривой или длительности.** Точки `linear()` разложены по времени успокоения: та же строка с
  другой длительностью — другая пружина (`01` §4.7). Кривая и время пружины — одно значение, и составной тип DTCG держит
  их вместе. Расширение пружины у токена другого типа сборка называет ошибкой.
- **`dampingRatio` и `stiffness`, масса 1.** Так заданы пружины Material 3 Expressive и `spring()` Compose; у Compose
  собственная частота — `sqrt(stiffness)`, массы в формуле нет [исходник: androidx `SpringSimulation.kt`]. Масса не
  пишется: при заданном ζ движение задаёт только k/m, и тройку другой библиотеки переводят в k/m (§2.1). Ключ вне двух
  — ошибка, чтобы масса не пропала молча.
- **`$value` — переход-запас.** Его читают инструменты без расширения (Style Dictionary, Figma, `ui_audit.py --tokens`
  по JSON). Длительность `$value` равна времени успокоения, которое выводит сборка, — иначе предупреждение с числом в
  подсказке; кривая запаса — кривая роли без перелёта, сборка её не читает.
- **Режим `reduced` — переход без пружины**: кривая входа и 150 ms (`03` §3.2, §7.2). Нет значения или в нём перелёт —
  предупреждение.
- **Алиас целиком** (`motion.switch.thumb`) даёт ту же кривую и те же параметры; своё значение режима у алиаса —
  переход без пружины в этом режиме.

Сборка ДС читает расширение (`EXT_SPRING` в `ds_build.py`) и проверяет его: форма — ошибка R-STRUCT-006, нормы движения —
предупреждения (§1.2).

### 1.2. Что собирает сборка: время, точки, допуск

Из токена §1.1 сборка выводит:

```css
:root {
  /* пружина: dampingRatio 0.7, stiffness 380 (масса 1, ω 19.49 рад/с), перелёт 4.6 %, успокоение до 1 % пути — 340 ms */
  --motion-spring-snap: 340ms linear(0, 0.007 1.85%, 0.028 3.8%, 0.063 5.9%, 0.114 8.2%, 0.162 10.1%, 0.223 12.3%, 0.469 20.5%, 0.574 24.15%, 0.672 27.9%, 0.754 31.45%, 0.819 34.7%, 0.874 37.95%, 0.921 41.25%, 0.959 44.65%, 0.994 48.75%, 1.02 53.15%, 1.037 57.9%, 1.045 63.2%, 1.045 68.7%, 1.04 75.55%, 1.009 93.1%, 1);
  /* пружина токена motion.spring.snap: … */
  --motion-switch-thumb: 340ms linear(…);
}
@media (prefers-reduced-motion: reduce) {
  :root:not([data-motion="full"]) {
    --motion-spring-snap: 150ms cubic-bezier(0, 0, 0.2, 1);
    --motion-switch-thumb: 150ms cubic-bezier(0, 0, 0.2, 1);
  }
}
:root[data-motion="reduced"] { /* те же две строки */ }
```

Применение — как у других составных токенов: `transition: transform var(--motion-switch-thumb);`, а цвет того же
элемента — своим токеном времени: `background-color var(--motion-transition-hover)`. Имя переменной — путь токена через
дефис (`../09-design-tokens/04-reference-token-schema.md` §6.3).

Нормы сборки:

| величина | норма | почему |
|---|---|---|
| кривая | единичный скачок пружины: старт в покое в 0, цель 1, масса 1 — точное решение для ζ < 1, ζ = 1 и ζ > 1 | кривая CSS-перехода всегда идёт из покоя; скорость жеста `linear()` не принимает (§1.4) |
| время успокоения | последний выход кривой из полосы ±1 % пути вокруг цели — дальше она в полосе навсегда; вверх до 10 ms | 1 % — порог базы (`01` §4.3); для ζ = 1 это и есть «воспринимаемая длительность» Apple: `Spring(duration: 0.5)` успокаивается до 1 % за 528 ms; пружины Material 3 дают 110–450 ms — вилка длительностей интерфейса; полоса 0,1 % (как `settlingDuration` SwiftUI) удлиняет время в 1,3–2 раза ради остатка, которого не видно [проверено: расчёт] |
| конец | остаток до цели в момент успокоения (≤ 1 % пути) кривая выбирает плавно на последней четверти времени | `linear()` кончается ровно в 1; остаток, снятый скачком, на панели 300 px — 3 px в последнем кадре |
| допуск точек | ломаная отходит от кривой не больше чем на 0,25 % пути вместе с округлением записи: прореживание — 0,2 %, прогресс — тремя знаками, время — процентами с двумя | на пути 200 px — 0,5 px, меньше пикселя; самопроверка: у 14 пружин наибольшее отклонение 0,21 % [проверено] |
| точки | столько, сколько требует допуск, — в местах изгиба (Рамер — Дуглас — Пекер по вертикали): 21–23 у пружин Material 3 и SwiftUI, 28 у ζ 0.5; больше 64 — предупреждение | 11 равномерных точек дают рывки, гладко — от 40 равномерных; точки с процентами ту же гладкость дают вдвое меньшим числом (Comeau: 25 вместо 50) [S48 через `01` §4.7] |
| вес | ≈ 290 знаков на пружину | три пружины — меньше 1 КБ CSS |

Предупреждения сборки (R-STRUCT-006, `warning`): перелёт больше 10 % (`01` §4.6: 3–10 % — потолок клиентского сервиса);
успокоение дольше 600 ms (`01` §1.3); точек больше 64; длительность `$value` не равна времени успокоения; нет значения
сокращённого движения или в нём кривая с перелётом; расширение `css` рядом с пружиной (CSS токена даёт пружина).
Запаса `@supports` сборка не выводит: `linear()` в Baseline Widely available с июня 2026 (`01` §4.7).

Время и перелёт пружин из базы по этим нормам [проверено: расчёт ds_build]:

| пружина | ζ | k | ω, рад/с | время CSS, ms | точек | перелёт, % |
|---|---|---|---|---|---|---|
| Material 3 standard fast spatial | 0.9 | 1400 | 37.42 | 140 | 22 | 0.15 — внутри полосы 1 %, кривая его не показывает |
| Material 3 standard default spatial | 0.9 | 700 | 26.46 | 200 | 22 | 0.15 — то же |
| Material 3 standard slow spatial | 0.9 | 300 | 17.32 | 300 | 22 | 0.15 — то же |
| Material 3 default effects | 1 | 1600 | 40.00 | 170 | 22 | 0 |
| Material 3 expressive default spatial | 0.8 | 380 | 19.49 | 330 | 22 | 1.5 |
| Material 3 expressive fast spatial | 0.6 | 800 | 28.28 | 230 | 22 | 9.5 |
| «щелчок» (`motion.spring.snap`) | 0.7 | 380 | 19.49 | 340 | 23 | 4.6 |
| Compose `spring()` по умолчанию | 1 | 1500 | 38.73 | 180 | 22 | 0 |
| Compose вход и выход по умолчанию (`StiffnessMediumLow`) | 1 | 400 | 20.00 | 340 | 22 | 0 |
| SwiftUI `.smooth` | 1 | 157.91 | 12.57 | 530 | 22 | 0 |
| SwiftUI `.snappy` | 0.85 | 157.91 | 12.57 | 360 | 21 | 0.6 — внутри полосы |
| SwiftUI `.bouncy` | 0.7 | 157.91 | 12.57 | 530 | 23 | 4.6 |
| SwiftUI `Animation.default` (`response` 0.55) | 1 | 130.51 | 11.42 | 590 | 22 | 0 |

Оценка по огибающей `t₉₉ = 4.6 / (ζω)` (`01` §4.2) расходится с временем успокоения кривой до 20 %: у ζ 0.6 — 271
против 221 ms, у ζ 0.8 — 295 против 326 ms. Время токена берут из сборки, а не из оценки.

### 1.3. Что получает код

- **Источник — токен DTCG.** `…/design/system.tokens.json` — источник темы кода (`docs/README.md`, связь «токены → `fsd`,
  `mobile`»): Compose и SwiftUI берут `dampingRatio` и `stiffness` из расширения.
- **Передняя часть DESIGN.md — `x-springs`.** Сборка пишет параметры для кода рядом с CSS-значением из `x-tokens`:

  ```yaml
  x-springs:
    motion-spring-snap:
      dampingRatio: 0.7
      stiffness: 380
      response: 0.3223
      bounce: 0.3
      overshoot: 0.046
      settle: "340ms"
  ```

  `response` и `bounce` — формы SwiftUI (§2.1), `overshoot` — доля пути, `settle` — время CSS. У алиаса — параметры цели.
- **`ds_build show --json`** — у токена пружины поле `spring` с теми же параметрами и токеном-источником.
- **Веб** — переменная `system.tokens.css` (§1.2); жест с отпусканием — пружина кодом с теми же ζ и k (§1.4).
- **Артефакт Design System движения не несёт**: у формата его токенов нет семейства движения
  (`../../claude-design/05-design-artifacts/01-design-system-and-canvas-in-session.md` §3.2). Переходы его превью и
  холста берут переменные движения с именами `system.tokens.css` (§5.1).

### 1.4. Где пружина уместна

- **Только геометрия от указателя, жеста и раскрытия**: отпускание перетаскивания, свайп, бегунок переключателя,
  отпускание нажатия, раскрытие карточки. Цвет и прозрачность не пружинят: у Material 3 пружины эффектов критически
  демпфированы, у ДС эффекты идут временем и кривой (`01` §4.3, §4.8) [консенсус].
- **Прогресс прокрутки — только ζ = 1**: пружина с отскоком на прогрессе сцены запрещена (`../../creative/05-motion/01-motion-principles-and-access.md`
  §7.3, `../../3d/16-js-scenes/02-stage-runtime.md` §4). Пружина рантайма сцен в этой форме — ζ 1 и k = ω² (§2.1).
- **Частое — без перелёта**: строки, вкладки, пункты меню, всё, что видят десятки раз за сессию (`01` §4.6).
- **Перелёт — на одном-двух элементах клиентского сервиса**, не больше 5 % (`03` §7.2); сборка предупреждает выше 10 %.
- **`linear()` — переход из покоя.** При прерывании CSS сокращает длительность (reversing shortening factor), и скорость
  жеста он не принимает (`01` §4.7). Перетаскивание и свайп с отпусканием ведёт пружина кодом — Motion, Web Animations с
  расчётом, Compose, SwiftUI — с теми же ζ и k токена; `linear()` — для переходов по смене состояния.
- **Сокращённое движение** — значение `reduced` токена: кривая входа без перелёта, 150 ms (`03` §3.2).

### 1.5. Пружины по поверхности

| поверхность | пружины | основание |
|---|---|---|
| кабинет, пресет А «плотная админка» | нет | Carbon запрещает перелёт; пресет без пружин (`03` §7.1) [система] |
| кабинет, пресет Б «клиентский сервис» | `motion.spring.snap` — ζ 0.7, k 380 (340 ms, перелёт 4.6 %): бегунок переключателя, подтверждение, отпускание перетаскивания | `03` §7.2 [мнение] |
| мобильное приложение | `motion.spring.snap` и две геометрические: `motion.spring.spatial` — ζ 0.9, k 700 (200 ms) и `motion.spring.spatial-fast` — ζ 0.9, k 1400 (140 ms): раскрытие, перестановка, своя нижняя панель, отпускание нажатия | Material 3 standard default и fast spatial [исходник: androidx `MotionScheme`, через `01` §4.3]; «комфорт — две пружины» (`01` §7.3) |
| страница сайта | пружины подачи — `../../creative/05-motion/01-motion-principles-and-access.md` §7.3 | — |

Цвет и прозрачность на всех поверхностях — токены времени и кривых (`motion.duration.*`, `motion.easing.*`); на Compose —
`tween(duration, easing)` с ними же. Системные переходы платформы (навигация iOS, системные диалоги и панели) ДС не
переопределяет: свои пружины — для своих компонентов, одни и те же на вебе и в приложении.

---

## 2. Перевод параметров пружины между платформами

### 2.1. Формулы

При массе 1:

| куда | формула | основание |
|---|---|---|
| собственная частота | ω = √k, рад/с; обратно k = ω² | физика; Compose: `naturalFreq = sqrt(stiffness)` [исходник] |
| Compose | `spring(dampingRatio = ζ, stiffness = k)` | [исходник: androidx `AnimationSpec.kt`] |
| SwiftUI, период | `response = duration = 2π / ω`; обратно k = (2π / duration)² | WWDC23 «Animate with springs»: `stiffness = (2π ÷ duration)²` [документация]; `Spring(response:dampingRatio:)` — «stiffness of the spring as an approximate duration» [документация] |
| SwiftUI, отскок | `bounce = 1 − ζ` при ζ ≤ 1, `bounce = 1/ζ − 1` при ζ > 1; обратно ζ = 1 − bounce (bounce ≥ 0), ζ = 1 / (1 + bounce) (bounce < 0) | `Spring.bounce`: 0 — критическое демпфирование, до 1 — без трения, меньше нуля до −1 — передемпфированная [документация]; формула — расчёт |
| SwiftUI, физика | `Spring(mass: 1, stiffness: k, damping: 2ζω)` | c = 2ζ√(k·m) [проверено: расчёт] |
| физическая тройка (Motion, React Spring, Easing Wizard) | ζ = c / (2√(k·m)); жёсткость токена — k / m | физика |
| пружина рантайма сцен и страниц | ζ = 1, k = ω² (`data-tempo` 6.5 → k 42.25) | `../../3d/16-js-scenes/02-stage-runtime.md` §4 |
| веб | `<время успокоения>ms linear(…)` — сборка ДС | §1.2 |
| характеристики | перелёт = exp(−πζ / √(1 − ζ²)), пик — на t = π / ω_d, ω_d = ω√(1 − ζ²) | физика |

Слайд WWDC23 печатает демпфирование с опечаткой (`1 − 4π × bounce ÷ duration`): при bounce 0 это 1, а критическое
демпфирование пружины `duration` 0.5 — 25.1. Верно `damping = 4π(1 − bounce) / duration` при bounce ≥ 0 и
`4π / (duration · (1 + bounce))` при bounce < 0 — то же, что c = 2ζω с ζ из строки выше [проверено: расчёт] (разбор
опечатки — Apple Developer Forums, тема 739811 [практика]).

### 2.2. Пример: «щелчок» ζ 0.7, k 380

| представление | значение |
|---|---|
| токен | `dampingRatio` 0.7, `stiffness` 380 |
| частоты | ω = √380 = 19.494 рад/с; ω_d = 13.921 рад/с |
| Compose | `spring(dampingRatio = 0.7f, stiffness = 380f)` |
| SwiftUI | `.spring(response: 0.3223, dampingFraction: 0.7)` = `.spring(duration: 0.3223, bounce: 0.3)` = `Spring(mass: 1, stiffness: 380, damping: 27.29)` |
| физическая тройка | mass 1, stiffness 380, damping 27.29 |
| перелёт | exp(−π · 0.7 / √0.51) = 4.6 %, пик 1.046 на 226 ms |
| веб | `340ms linear(…)`: успокоение до 1 % — 337.3 ms, вверх до 340; 23 точки; ломаная отходит от кривой не больше чем на 0,18 % пути |

ω, `response`, `bounce`, перелёт, время и допуск точек этого примера сверяет самопроверка `ds_build.py --selftest`
[проверено].

Обратный перевод:

- **SwiftUI `.snappy`** (`duration` 0.5, `bounce` 0.15) → ζ 0.85, k 157.91 → на вебе 360 ms, перелёт 0.6 % внутри
  полосы 1 %.
- **SwiftUI `Animation.default`** (`response` 0.55, ζ 1) → k 130.51 → 590 ms.
- **Comeau `{mass: 1.75, tension: 200, friction: 12}`** → ζ 12 / (2√350) = 0.32, k 200 / 1.75 = 114.29 → перелёт
  34.5 %, успокоение 1330 ms: сборка предупредит о перелёте и времени — это пружина демонстрации, а не интерфейса.
- **Compose по умолчанию**: `spring()` — ζ 1, k 1500 (`StiffnessMedium`) → 180 ms; входы и выходы `AnimatedVisibility`
  и `AnimatedContent` — k 400 (`StiffnessMediumLow`) → 340 ms.

Значения Apple (≈ 0.5 s) в кабинет на вебе не переносят — переносят структуру: без перелёта, слабый, заметный (`01`
§4.4).

---

## 3. Переходы по шаблонам интерфейса

Для кабинета на вебе и мобильного приложения. Токены — схема `../09-design-tokens/04-reference-token-schema.md` §2.10
(`motion.duration.*`, `motion.easing.*`, `motion.transition.*`, `motionScale.*`) и пружины §1.5; длительности — `02` §3;
когда переход экрана нужен — `../../ux/06-feedback-states-motion/03-motion-and-microinteractions.md` §4. Действие с
клавиатуры не анимируется ни в одном шаблоне (`02` §7.1); фокус — 0 ms везде.

### 3.1. Шаблон → токены → сокращённое движение

| шаблон | токены | при сокращённом движении |
|---|---|---|
| **Смена экрана вперёд и назад** (push/pop) | кабинет: область содержимого проявляется `motion.duration.default` + `motion.easing.entrance` (пресет Б), пресет А — без движения; мастер — сдвиг `motionScale.translateMedium` за `motion.duration.slower` + `motion.easing.standard`; мобильное: системный push и pop платформы, свой переход — сдвиг `motion.spring.spatial` и проявление `motion.duration.default` | проявление не дольше 150 ms без сдвига; iOS растворяет системный переход сам; Android «Убрать анимацию» — мгновенно |
| **Модальное окно и диалог** | `motion.transition.modalEnter` / `modalExit`; подложка — `blanketEnter` / `blanketExit`; масштаб входа `motionScale.scaleIn` | только прозрачность: `scaleIn` → 1, длительности → 150 ms (режим `reduced` схемы) |
| **Нижняя панель** (sheet) | вход `motion.transition.drawerEnter`; выход — `motion.transition.modalExit`: закрытая панель уходит насовсем, кривая выхода (`01` §2.1); своя панель в приложении — `motion.spring.spatial`; отпускание жестом — пружина кодом с ζ и k токена | проявление без выезда; системная панель — как решит система |
| **Выдвижная панель** (drawer) | `motion.transition.drawerEnter` / `drawerExit`: выход — кривая `standard`, панель остаётся «рядом» (исключение Carbon, `01` §2.1) | прозрачность без сдвига |
| **Вкладки** | индикатор — `motion.duration.slow` + `motion.easing.standard` (пресет Б), пресет А — без движения; панель — без движения или прозрачность `motion.duration.fast` | индикатор встаёт сразу, панель сменяется без движения |
| **Раскрытие строки и аккордеон** | `motion.transition.expand`; шеврон — та же длительность; в приложении — `motion.spring.spatial` | `expand` → 150 ms; шеврон — сменой значка |
| **Вставка и удаление в списке** (FLIP) | вставка — проявление на месте `motion.duration.default`; удаление — схлопывание `motion.transition.expand`; соседи — `motion.duration.slow` + `motion.easing.standard`, в приложении — `motion.spring.spatial`; сортировка и виртуальный список — без движения | соседи встают сразу, остаётся проявление |
| **Скелет → содержимое** | смена — прозрачность `motion.duration.default` + `motion.easing.standard`; мерцание скелета — цикл 1,5–2 s (`02` §3.7) | мерцания нет, содержимое — сразу или проявлением 150 ms |
| **Уведомление** (toast) | `motion.transition.toastEnter` / `toastExit`, сдвиг `motionScale.translateMedium`; перестановка стопки — `motion.duration.slow` | прозрачность без сдвига |
| **Отклик наведения, нажатия и фокуса** | наведение — `motion.transition.hover`; нажатие — `motion.transition.press`, в пресете Б — `scale(0.98)`; бегунок переключателя — `motion.spring.snap`; фокус — `motion.duration.instant` (0 ms) | цвет остаётся; масштаб нажатия 2 % можно оставить (порог — 5 %, `03` §3.2); бегунок — значение `reduced` пружины; фокус — 0 ms всегда |
| **Общий элемент между экранами** (shared element) | кабинет — `motion.duration.slower` + `motion.easing.standard` (200–300 ms, `02` §5.3); приложение — `motion.spring.spatial`; только там, где общий элемент есть: карточка → страница объекта, миниатюра → полный размер | перелёта нет: смена экрана проявлением |

### 3.2. Реализация: веб, Compose, SwiftUI

| шаблон | веб | Compose | SwiftUI |
|---|---|---|---|
| **Смена экрана** | `opacity` области содержимого, новый узел — с `@starting-style`; View Transitions в документе — `document.startViewTransition(update)` после проверки `matchMedia("(prefers-reduced-motion: reduce)")`, длительность — правилом `::view-transition-group(*)` из токена | `NavHost(enterTransition = { slideIntoContainer(SlideDirection.Start, spring(dampingRatio, stiffness)) + fadeIn(tween(150)) }, popEnterTransition = …)` — умолчание `tween(700)` переопределить; жест «назад» — `predictivePopEnterTransition` / `predictivePopExitTransition` | `NavigationStack` — системный push и pop с жестом от края, своего не делать; зум из карточки — `.navigationTransition(.zoom(sourceID:in:))` + `.matchedTransitionSource(id:in:)` (iOS 18) |
| **Модальное окно** | `<dialog>` + `showModal()`; `opacity` и `transform` с `@starting-style`, `overlay` и `display` с `allow-discrete` (`02` §5.1); подложка — `::backdrop` | `AlertDialog` и `Dialog` Material 3 — анимация окна системы; своё содержимое — `AnimatedVisibility(enter = fadeIn(tween(…)) + scaleIn(initialScale = 0.95f, tween(…)))` | `.alert`, `.confirmationDialog` — системные; свой слой — `.transition(.opacity.combined(with: .scale(scale: 0.95)))` внутри `withAnimation` |
| **Нижняя панель** | `<dialog>` у нижнего края, `transform: translateY(100%) → none`; закрытие жестом — пружина кодом | `ModalBottomSheet` Material 3 — свой жест и анимация; своя панель — `AnimatedVisibility(enter = slideInVertically(spring(…)) { it })` | `.sheet` + `.presentationDetents([.medium, .large])` (iOS 16) — системная |
| **Выдвижная панель** | `transform: translateX(-100%) → none` у `<dialog>` или `[popover]`; выход — кривая `standard` | `ModalNavigationDrawer`, `DismissibleNavigationDrawer` Material 3 | системной нет: на iPad — `NavigationSplitView`; своя — `.transition(.move(edge: .leading))` |
| **Вкладки** | индикатор — одним переходом `transform` или `clip-path` (`02` §3.3) | `PrimaryTabRow` — индикатор анимирует сам; панели — `HorizontalPager` или `AnimatedContent` | `TabView` — смена без движения; сегменты — `Picker` со стилем `.segmented`; свой индикатор — `matchedGeometryEffect` |
| **Раскрытие** | `grid-template-rows: 0fr → 1fr` + `opacity` (`02` §4.2) | `AnimatedVisibility(enter = expandVertically() + fadeIn(), exit = shrinkVertically() + fadeOut())` или `Modifier.animateContentSize()` с токенами | `DisclosureGroup` — системное; своё — `withAnimation { isOpen.toggle() }` + `.transition(.opacity)` |
| **Список** | FLIP: позиции до и после, `element.animate([{ transform: "translate(Δx, Δy)" }, { transform: "none" }], { duration, easing })`; или View Transitions с `view-transition-name` у строк | `LazyColumn` + `Modifier.animateItem(fadeInSpec, placementSpec, fadeOutSpec)` — умолчание `spring(stiffness = StiffnessMediumLow)` заменить токенами | `List` и `ForEach` в `withAnimation` — системные вставка и удаление; `.transition(.opacity)` |
| **Скелет** | скелет того же размера, что содержимое; смена — `opacity`; мерцание — `@keyframes`, при сокращённом движении — `animation: none` | `Crossfade(targetState, animationSpec = tween(150))`; мерцание — `rememberInfiniteTransition()` | `.redacted(reason: .placeholder)` (iOS 14) → содержимое; смена — `.transition(.opacity)` |
| **Уведомление** | `[popover]` или живая область `role="status"`; вход — `@starting-style` | `SnackbarHost` Material 3 — своя анимация | системного нет: слой `.overlay` с `.transition(.move(edge: .bottom).combined(with: .opacity))` |
| **Отклик** | `transition` на `background-color`, `color`, `border-color` токеном наведения; `:active` — `scale(0.98)`; `:focus-visible { transition: none; }` | `Modifier.clickable(interactionSource, indication = ripple())`; нажатие — `collectIsPressedAsState()` + `animateFloatAsState(if (pressed) 0.98f else 1f, tween(100))`; наведение — `collectIsHoveredAsState()` | `ButtonStyle`: `configuration.isPressed` → `.scaleEffect(0.98)` + `.animation(.spring(response:dampingFraction:), value: configuration.isPressed)`; наведение — `.hoverEffect()` (iPadOS); фокус — системное кольцо |
| **Общий элемент** | View Transitions: один `view-transition-name` у карточки и шапки страницы объекта, `document.startViewTransition(update)` | `SharedTransitionLayout` + `Modifier.sharedElement(rememberSharedContentState(key), animatedVisibilityScope)` или `sharedBounds` — в `AnimatedContent` и `NavHost`; стабильны с Compose Animation 1.10 (декабрь 2025) | в одном экране — `matchedGeometryEffect(id:in:)` (iOS 14); между экранами — `.matchedTransitionSource(id:in:)` + `.navigationTransition(.zoom(sourceID:in:))` (iOS 18) |

Пружина `spring(dampingRatio, stiffness)` в Compose и `.spring(response:dampingFraction:)` в SwiftUI — значения токена
по §2.1; длительности `tween(…)` и кривые — токены времени: `FastOutSlowInEasing` = `standard`, `LinearOutSlowInEasing`
= `entrance`, `FastOutLinearInEasing` = `exit` (§4.2).

---

## 4. Механизмы платформ и сокращённое движение

### 4.1. Веб

- **Переходы CSS** прерываемы и годятся для смены состояния; появление из `display: none` и вход в top layer —
  `@starting-style`, `transition-behavior: allow-discrete`, `overlay` (Baseline 2024, `02` §5.1).
- **`linear()`** — Baseline Newly available с декабря 2023, Widely available с июня 2026 (`01` §4.7).
- **View Transitions в документе** — Baseline Newly available с октября 2025: Chrome 111, Safari 18, Firefox 144;
  `view-transition-class` и `view-transition-name: match-element` — там же, типы переходов первая версия Firefox не
  несёт [документация: web.dev, Chrome for Developers]. В кабинете — прогрессивное улучшение: без переходов интерфейс тот
  же (`02` §5.3); при сокращённом движении `startViewTransition` не вызывают (`03` §3.4).
- **Сокращённое движение** — блоки `@media (prefers-reduced-motion: reduce)` и `[data-motion="reduced"]` из режима
  `reduced` токенов, их выводит сборка; плавную прокрутку, циклы и View Transitions выключают отдельные правила (`03`
  §3.4).
- **Жест** — пружина кодом с ζ и k токена: перетаскивание и свайп передают скорость, `linear()` — нет.

### 4.2. Jetpack Compose

- **Кривые и время**: `tween(durationMillis = 300, delayMillis = 0, easing = FastOutSlowInEasing)` по умолчанию;
  `FastOutSlowInEasing` = `cubic-bezier(0.4, 0, 0.2, 1)`, `LinearOutSlowInEasing` = `(0, 0, 0.2, 1)`,
  `FastOutLinearInEasing` = `(0.4, 0, 1, 1)` — те же числа, что `standard`, `entrance`, `exit` схемы ДС [исходник:
  androidx `Easing.kt`, `AnimationSpec.kt`].
- **Пружина**: `spring(dampingRatio = Spring.DampingRatioNoBouncy, stiffness = Spring.StiffnessMedium)` по умолчанию —
  ζ 1, k 1500; она же — спецификация `animate*AsState` и `updateTransition` по умолчанию [исходник; документация:
  Android Developers, «Customize animations»].

  | константа `Spring` | значение |
  |---|---|
  | `StiffnessHigh` · `StiffnessMedium` · `StiffnessMediumLow` · `StiffnessLow` · `StiffnessVeryLow` | 10 000 · 1500 · 400 (входы и выходы) · 200 · 50 |
  | `DampingRatioHighBouncy` · `DampingRatioMediumBouncy` · `DampingRatioLowBouncy` · `DampingRatioNoBouncy` | 0.2 · 0.5 · 0.75 · 1 |
  | `DefaultDisplacementThreshold` | 0.01 |

- **Умолчания переходов**: `AnimatedVisibility` — `fadeIn() + expandIn()` и `shrinkOut() + fadeOut()` на пружинах
  `StiffnessMediumLow`; `AnimatedContent` — `fadeIn(tween(220, delayMillis = 90)) + scaleIn(initialScale = 0.92f, …)`
  против `fadeOut(tween(90))`; `Modifier.animateItem()` — пружины `StiffnessMediumLow` [исходник]. В ДС их заменяют
  токенами.
- **Навигация**: `NavHost` по умолчанию — `fadeIn(tween(700))` и `fadeOut(tween(700))` вперёд и назад; жест «назад» —
  `fadeIn(spring(1f, 1600f))` и `scaleOut(0.7f)` [исходник: androidx `DefaultNavTransitions.android.kt`]. 700 ms —
  дольше потолка ДС (400 ms у пресета Б): переходы `NavHost` задают явно.
- **Общий элемент**: `SharedTransitionLayout`, `sharedElement`, `sharedBounds` — стабильны с Compose Animation 1.10
  (декабрь 2025); текущая стабильная версия — 1.12.1 [документация: release notes].
- **Сокращённое движение**: «Убрать анимацию» (Remove animations, Android 9+) ставит масштаб длительности аниматоров
  `ANIMATOR_DURATION_SCALE` в 0; Compose с версии 1.2 следует ему через `MotionDurationScale`, и движение кончается в
  следующем кадре [документация: Android Developers `MotionDurationScale`; практика: E.-J. Panula]. Система движение
  убирает, а не сокращает: «reduce, not remove» на Android даёт свой переключатель приложения «меньше движения» —
  он ставит значения `reduced` токенов; начальное положение переключателя читают из `Settings.Global.ANIMATOR_DURATION_SCALE`.

### 4.3. SwiftUI

- **Анимация по умолчанию — пружина**: `Animation.default` — `response` 0.55, `dampingFraction` 1 с iOS 17, раньше —
  `easeInOut` [документация].
- **Сигнатуры**: `.spring(response: 0.5, dampingFraction: 0.825, blendDuration: 0)` и `.spring(duration: 0.5, bounce: 0,
  blendDuration: 0)` — значения по умолчанию; пресеты `.smooth`, `.snappy`, `.bouncy` (`01` §4.4) [документация].
- **`Spring`** (iOS 17): `init(duration:bounce:)` — bounce от −1 до 1; `init(response:dampingRatio:)`;
  `init(mass:stiffness:damping:allowOverDamping:)`; `settlingDuration` — цель 1, скорость 0, `epsilon` 0.001, то есть
  успокоение до 0,1 % [документация]. Время CSS сборки считается до 1 % (§1.2): `settlingDuration` той же пружины
  длиннее в 1,3–2 раза.
- **Общий элемент**: `matchedGeometryEffect(id:in:)` — iOS 14; `navigationTransition(_:)`, `.zoom(sourceID:in:)`,
  `matchedTransitionSource(id:in:)` — iOS 18 [документация].
- **Сокращённое движение**: `@Environment(\.accessibilityReduceMotion)` (iOS 13) — «UI should avoid large animations,
  especially those that simulate the third dimension» [документация]; системные переходы при «Уменьшении движения»
  идут растворением вместо зума и сдвига [документация: Apple Support]. Свои переходы читают значение среды и берут
  значения `reduced` токенов.

### 4.4. Сокращённое движение по платформам

| платформа | что включает человек | что делает система | что делает ДС |
|---|---|---|---|
| веб | «уменьшить движение» в ОС (`prefers-reduced-motion: reduce`); переключатель продукта `data-motion` | ничего | блоки режима `reduced` из сборки; выбор посетителя сильнее системы в обе стороны (`03` §3.6) |
| Android | «Убрать анимацию» | масштаб аниматоров 0: движение Compose кончается в следующем кадре | свой переключатель «меньше движения» ставит значения `reduced` |
| iOS | «Уменьшение движения» | системные переходы — растворением | свои переходы по `accessibilityReduceMotion` берут значения `reduced` |

---

## 5. Движение ДС на этапе дизайна: показ и проверка

### 5.1. Что показывает холст

- **Компонент ДС показывает свои переходы в Play**: наведение, нажатие, раскрытие, появление и уход (открыть и закрыть
  диалог, показать и снять уведомление), переключение бегунка. Переходы заданы правилами по атрибутам состояния
  (`[data-state]`, `[data-open]`, `:hover`, `:active`) на переменных движения `system.tokens.css`; состояние меняет
  кнопка в логике артборда (`setState`). Где на артборде стоят такие правила — справка холста
  (`../../claude-design/05-design-artifacts/01-design-system-and-canvas-in-session.md` §3.1) [практика].
- **Имена переменных движения** — как в `system.tokens.css`: `--` и путь токена DTCG через дефисы. В превью артефакта
  Design System переменные движения приходят из `…/components/bundle.css` — его блок движения повторяет
  `system.tokens.css` с блоками сокращённого движения, иначе превью и холст двигаются не так, как код [мнение].
- **Сокращённое движение** — переключатель `data-motion="reduced"` на артборде (твик): компонент проходит те же состояния
  по значениям `reduced` и встаёт в те же конечные состояния. Каждое конечное состояние — открыто и закрыто, включено и
  выключено — стоит на артборде и неподвижным экземпляром: обзор холста и статичная копия для проверок показывают
  состояние покоя, середины движения у них нет (`../../claude-design/05-design-artifacts/03-what-canvas-runs.md` §5).
- **Смена экрана и общий элемент** — состояниями одного артборда: ссылку между артбордами Play сменяет сам холст, своего
  перехода у неё нет (`../../claude-design/05-design-artifacts/03-what-canvas-runs.md` §4) [документация типа].
- **Пружина** на холсте — та же переменная `linear()`; пружина жеста (перетаскивание) — логикой артборда с ζ и k токена.

### 5.2. Что проверяет утилита

`ui_audit.py` на статичной копии артборда с `--tokens system.tokens.css` и `--reduced-motion` (движение CSS в копии
остаётся, `../../claude-design/05-design-artifacts/03-what-canvas-runs.md` §5):

| проверка | что меряет | граница |
|---|---|---|
| K1 | `transition: all` с ненулевой длительностью | 0 |
| K2 | длительности переходов — в шкале токенов ДС (время пружин из CSS входит в шкалу) и не длиннее потолка пресета: А — 200 ms (подложка 250), Б — 400 ms (онбординг 600) | 0 вне шкалы и выше потолка |
| K3 | доля 300 ms среди длительностей | ≤ 20 % |
| M1 | при `prefers-reduced-motion: reduce` наибольшая длительность не растёт и не обнуляется | — |
| M2 | циклические анимации при сокращённом движении выключены | 0, кроме единственного спиннера |
| G1–G5 | индикатор фокуса: виден, толщина, контраст, не обрезан | — |

Утилита читает вычисленные стили в покое и на прогонах наведения и Tab. Формы кривой, перелёта, того, какое свойство
пружинит, прерывания, направления ухода и порядка хореографии она не видит.

### 5.3. Что смотрит человек в Play

1. Наведение отвечает сразу, уход мягче; фокус появляется без движения.
2. Нажатие короткое и не задерживает действие.
3. Появление и раскрытие — откуда пришло, туда и уходит; выход короче входа.
4. Перелёт — только у геометрии (бегунок, подтверждение); цвет и прозрачность не прыгают.
5. Повторное нажатие посреди перехода разворачивает движение с текущей точки.
6. Частое — строки, вкладки, меню — без перелёта и почти незаметно.
7. С переключателем «меньше движения» — те же конечные состояния, без сдвигов и перелётов.

Утверждает движение ДС владелец продукта (`CLAUDE.md` §3, облик); проверка — шаг, который он заказывает: смотрит в Play
сам (`../../claude-design/05-design-artifacts/01-design-system-and-canvas-in-session.md` §7).

---

## Частые ошибки

1. **Пружина на токене кривой или длительности**: кривую берут с одним временем, а точки разложены по другому.
2. **Строка `linear()` вписана руками** без параметров: пересобрать её нечем, Compose и SwiftUI её не прочтут.
3. **Длительность `$value` не равна времени успокоения**: инструменты без расширения показывают другое время.
4. **Пружина без значения `reduced`**: при «уменьшить движение» бегунок перелетает и качается.
5. **Пружина на цвете или прозрачности**.
6. **Перелёт на строках, вкладках, пунктах меню**.
7. **`linear()` на перетаскивании с отпусканием**: скорость жеста теряется, при прерывании время сжимается.
8. **`NavHost` с умолчанием 700 ms**.
9. **Свой push и pop поверх системного в SwiftUI**: ломает жест от края и растворение при «Уменьшении движения».
10. **`startViewTransition` без проверки сокращённого движения**.
11. **Переход экрана показан ссылкой между артбордами**: Play сменяет артборды сам, перехода никто не видит.
12. **Значения пружин SwiftUI (≈ 0.5 s) в кабинете на вебе** (`01` §4.4).
13. **`response` путают с `settlingDuration`**: первое — период, второе — успокоение до 0,1 %.
14. **Перевод `bounce` в демпфирование по слайду WWDC23** с опечаткой (§2.1).
15. **Переменные движения в `bundle.css` под другими именами**, чем в `system.tokens.css`: превью двигается не как код.

## Чек-лист

1. Каждая пружина ДС — токен `transition` с `dampingRatio` и `stiffness`, без массы и других ключей?
2. `$value.duration` пружины равна времени успокоения из сборки (`ds_build check` без предупреждений пружины)?
3. У каждой пружины есть значение `reduced` без перелёта?
4. Пружинит только геометрия; цвет и прозрачность — токенами времени?
5. Перелёт — только у одного-двух элементов клиентского сервиса и не больше 5 %; у частых элементов его нет?
6. Число пружин соответствует поверхности (§1.5)?
7. Код берёт параметры из токена или `x-springs`, а не пересчитывает строку `linear()`?
8. Переходы шаблонов взяты из §3, а не придуманы для экрана?
9. `NavHost` и свои переходы Compose заданы токенами; системные переходы SwiftUI не подменены?
10. View Transitions — прогрессивное улучшение с проверкой сокращённого движения?
11. На холсте компоненты ДС проходят свои состояния в Play, а с `data-motion="reduced"` — те же состояния без сдвигов?
12. `ui_audit.py` с `--reduced-motion` на копиях — без находок K1, K2, M1, M2?

## Открытые вопросы

1. **Полоса 1 % и допуск 0,25 % на длинном пути** (нижняя панель на всю высоту телефона, 600–800 px) людьми не
   сравнивались с полосой 0,1 % [гипотеза]: проверит показ панели в Play на телефоне рядом с системной панелью.
2. **Следует ли холст Claude Design `prefers-reduced-motion` системы зрителя в Play** — не проверено: до проверки
   сокращённое движение на холсте показывают переключателем `data-motion` (§5.1).
3. **Растворение системного push при «Уменьшении движения»** подтверждено описанием Apple для системных переходов, а не
   прогоном `NavigationStack` [не проверено] (проверит прогон на устройстве).
4. **Перестановка соседей в списке** — пружиной в приложении, временем в кабинете (§3.1): позиция базы без замера на
   реальных данных [мнение]; проверит показ списка из 20–50 строк в Play.

## Источники

Снимок: 28.10.2026 — день сверки фактов платформ и версий.

- **Сборка и самопроверка ДС** — `../../../scripts/project/ds_build.py` (`spring_curve`, `--selftest`): время
  успокоения, точки и допуск 14 пружин, перевод параметров, вывод CSS, передней части и `show`.
- **MDN, `linear()`** — Baseline: Newly available с декабря 2023, Widely available с июня 2026; синтаксис с процентами
  (`01` [S19]; даты — `../../creative/07-stack-implementation/01-stack-choice.md` §3.1).
- **web.dev**, «Same-document view transitions are now Baseline Newly available», октябрь 2025 — Firefox 144 (октябрь 2025);
  `view-transition-class`, `match-element`, `:active-view-transition`; типов нет в первой версии Firefox.
- **Chrome for Developers**, «What's new in view transitions (2025 update)» — Chrome 111, Safari 18, Firefox 144.
- **androidx, ветка `androidx-main`** — compose/animation/animation-core: `AnimationSpec.kt` (`spring`, `tween`,
  `DefaultDurationMillis` 300), `Easing.kt`, `SpringSimulation.kt`; compose/animation/animation: `AnimatedContent.kt`,
  `AnimatedVisibility.kt`, `EnterExitTransition.kt`, `SharedTransitionScope.kt`; compose/foundation: `LazyItemScope.kt`
  (`animateItem`); navigation/navigation-compose: `DefaultNavTransitions.android.kt`.
- **composables.com**, `androidx.compose.animation.core.Spring` — значения констант с описаниями из исходника.
- **Android Developers**, «Customize animations» (Compose) — пружина как спецификация по умолчанию; release notes
  Compose Animation — 1.10.0 (декабрь 2025): «Shared transition APIs are stable in 1.10»; 1.12.1 (сентябрь 2026).
- **Android Developers**, `MotionDurationScale`; **Eeva-Jonna Panula**, «Android Animations and Reduced Motion» (DEV) —
  «Убрать анимацию» = `ANIMATOR_DURATION_SCALE` 0, Compose следует с 1.2.0.
- **Apple Developer Documentation (JSON API)**: `Spring`, `init(duration:bounce:)`, `bounce`, `dampingRatio`,
  `init(response:dampingRatio:)`, `init(mass:stiffness:damping:allowOverDamping:)`, `settlingDuration`;
  `Animation.default`, `spring(response:dampingFraction:blendDuration:)`, `spring(duration:bounce:blendDuration:)`,
  `smooth`, `snappy`, `bouncy`; `matchedGeometryEffect(id:in:properties:anchor:isSource:)`, `navigationTransition(_:)`,
  `zoom(sourceID:in:)`, `matchedTransitionSource(id:in:)`; `EnvironmentValues.accessibilityReduceMotion`.
- **Apple, WWDC23 «Animate with springs»** (сессия 10158) — `stiffness = (2π ÷ duration)²`, пружина — анимация по
  умолчанию (конспект WWDC Notes); **Apple Developer Forums**, тема 739811 — опечатка формулы демпфирования на слайде.
- **Apple Support**, «Reduce screen motion on your iPhone, iPad, or iPod touch» (111781) — растворение вместо зума и
  сдвига.
- **Janum Trivedi, Wave** (файл Sources/Wave/Spring.swift) — `stiffness = (2π / response)² · mass`,
  `damping = 4π · ζ · mass / response` [практика].
- Josh W. Comeau, «Springs and Bounces in Native CSS» — `01` [S48].
