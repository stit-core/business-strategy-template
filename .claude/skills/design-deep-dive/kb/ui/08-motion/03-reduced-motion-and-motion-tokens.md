# Доступность движения и готовые токены

Волна 2, агент M, 22 сентября 2026. Источников прочитано целиком: 59.

Смежные файлы: значения и их происхождение — `01-durations-easings-springs.md`, каталог применения — `02-what-to-animate-in-apps.md`, пружина токеном, сокращённое движение на Android и iOS и переходы по шаблонам — `04-spring-tokens-transitions-platforms.md`. Архитектура токенов, формат DTCG, темы и режимы — `../09-design-tokens/` (агент F); формат `duration` и `cubicBezier` согласован с его эталонной схемой. Контраст и цвета, на которые ссылаются токены, — `../01-color/`. Доступность как процесс — `../../ux/`.

## Выжимка для агента

1. **`prefers-reduced-motion` — Baseline Widely available, во всех браузерах с января 2020.** Отсутствие поддержки в продукте 2026 года — не «недоработка», а дефект. → §1.1 [документация]
2. **Правило «reduce, not remove».** MDN в собственном примере заменяет `pulse` (scale 0.9…1.1) на `dissolve` (только непространственные свойства), причём **увеличивает** длительность с 1 s до 4 s. → §3.1 [документация]
3. **Опасно не движение вообще, а три фактора: доля экрана, покрытая движением; рассогласование направления и скорости; пройденная дистанция.** → §1.2 [консенсус]
4. **Оставляй: `opacity`, цвет, размытие. Убирай: перемещение, масштаб, вращение, параллакс, автозапуск.** Val Head: «Animation that involves only non-moving properties, like opacity, color, and blurs, **are unlikely to be problematic**». → §3.2 [консенсус]
5. **WCAG 2.3.3 Animation from Interactions — уровень AAA**, не AA. Требует возможности отключить неессенциальную анимацию, запущенную действием пользователя. → §2.1 [стандарт]
6. **WCAG 2.2.2 Pause, Stop, Hide — уровень A**, обязателен. Касается анимации, запущенной страницей автоматически и длящейся дольше 5 секунд параллельно с другим контентом. → §2.2 [стандарт]
7. **Анимация, запущенная наведением, фокусом или появлением в области видимости, считается запущенной автоматически** и попадает под оба критерия. → §2.2 [стандарт]
8. **Полноэкранный лоадер законен дольше 5 секунд** («not presented in parallel with other content»), а бесконечный шиммер рядом с уже загруженным контентом — нет. → §2.2 [стандарт]
9. **Мигание чаще 3 раз в секунду — это уже вспышка** (WCAG 2.3.1), а не мигание. → §2.3 [стандарт]
10. **Не пиши `* { transition: none !important }`.** Это ломает `transition-delay`, выключает нужные затухания и мешает компонентам, у которых состояние снимается по `transitionend`. → §3.3 [консенсус]
11. **Настройку ОС надо уважать, но не считать единственным сигналом**: WCAG допускает и собственный переключатель в интерфейсе (техника Gx). → §2.1 [стандарт]
12. **Готовый набор: 8 примитивов длительности, 5 кривых, 6 семантических длительностей, 4 семантические кривые, 14 составных переходов.** JSON DTCG — §5, CSS — §6. → §4
13. **Пресет «Плотная админка»: дефолт 100 ms, потолок 200 ms, никаких масштабов и перелётов, вкладки и навигация без анимации.** → §7.1
14. **Пресет «Клиентский сервис»: дефолт 150 ms, потолок 400 ms, scale 0.95, одна пружина на переключателе.** → §7.2
15. **`prefers-reduced-transparency`** — отдельная медиа-фича; при ней снимается `backdrop-filter` и полупрозрачные подложки. → §3.5 [документация]
16. **Реализуй reduced motion через переопределение токенов, а не через правки в компонентах.** Одна секция `@media` на файл токенов вместо двадцати в компонентах. → §3.4
17. **Ни один продукт из 24 измеренных не объявляет длительности, отличающиеся при reduced motion** — это дыра практики, а не решённая задача. → §8 [измерение]
18. **Уменьшай, а не обнуляй: 150 → 1 ms плохо, 150 → 100 ms с заменой `translate` на `opacity` хорошо.** → §3.1
19. **Пружину при reduced motion заменяй переходом без перелёта**: значение режима `reduced` токена пружины — кривая входа, 150 ms. → §3.2, §7.2
20. **В отчёте о доступности движения записывай три вещи: что отключается, что остаётся, где переключатель.** → §9

---

## 1. Кто страдает от движения и от чего именно

### 1.1 `prefers-reduced-motion`: статус и где включается

**Baseline Widely available**, доступно во всех браузерах с **января 2020** [S18].

Значения: `no-preference` (false) и `reduce` (true). Запись `@media (prefers-reduced-motion)` эквивалентна `@media (prefers-reduced-motion: reduce)`.

Где пользователь включает настройку (полный список из MDN, полезен для инструкции поддержки) [S18]:

| Платформа | Путь |
|---|---|
| GNOME | Accessibility → Seeing → Reduced animation |
| KDE | Animation speed → Instant |
| Windows 10 | Ease of Access → Display → Show animations |
| Windows 11 | Accessibility → Visual Effects → Animation Effects |
| macOS до 15 | Accessibility → Display → Reduce motion |
| macOS 26 (Tahoe) и выше | Accessibility → **Motion** → Reduce motion |
| iOS | Accessibility → Motion |
| Android 9+ | Accessibility → Remove animations |

### 1.2 Три фактора риска

Val Head, статья, с которой началась работа над медиа-фичей [S17]:

1. **Относительный размер движения.** Важен не размер экрана, а **доля экрана**, которую покрывает движение: «a small button with a 3D rotation probably won't cause trouble, but a **full-screen wipe transition covering the entire screen likely would**».
2. **Рассогласование направления и скорости.** Параллакс и scrolljacking: фон и передний план движутся с разной скоростью, движение идёт в направлении, отличном от прокрутки.
3. **Покрытая дистанция.** Большое виртуальное расстояние за короткое время (пример: 3D-зум iOS 7).

Масштаб проблемы: по данным vestibular.org около **8 млн** взрослых американцев сообщают о хронической проблеме с равновесием, ещё **2.4 млн** — о хроническом головокружении. Движение также влияет на людей с эпилепсией и мигренями [S17].

Тяжесть последствий, цитата W3C: «Triggered reactions include **nausea, migraine headaches, and potentially needing bed rest to recover**» [S21].

Формулировка MDN, короткая и применимая как проверка: «Animations such as **scaling or panning large objects** can be vestibular motion triggers» [S18].

### 1.3 Польза движения, которую не надо терять

Val Head перечисляет доказанные эффекты, ради которых движение вообще существует [S17]: снижение когнитивной нагрузки (путь объекта виден на экране, его не надо держать в голове), улучшение принятия решений, помощь в запоминании пространственных отношений, предотвращение **change blindness** (слепоты к изменениям).

Отсюда и принцип «reduce, not remove»: у человека с вестибулярной чувствительностью change blindness никуда не делась.

---

## 2. Что требуют стандарты

### 2.1 SC 2.3.3 Animation from Interactions (уровень AAA)

Формулировка: «**Motion animation triggered by interaction can be disabled**, unless the animation is essential to the functionality or the information being conveyed» [S21].

Ключевые детали:
- **Уровень AAA**, не AA. То есть формально не входит в обычный юридический минимум, но практикой принят как норма.
- Определение «motion animation»: «addition of steps between conditions to create the illusion of movement or to give a sense of a smooth transition». Errata: определение поправлено так, чтобы **не исключать размытие (blurring)**.
- Три достаточных способа соответствия: (1) не использовать ненужную анимацию; (2) дать контрол выключения; (3) **использовать настройку reduce motion в ОС/браузере**.
- Достаточные техники: **C39** (CSS `prefers-reduced-motion`), **SCR40** (та же медиа-фича из JavaScript), **Gx** («Allowing users to set a preference that prevents animation»).
- Прокрутка: перемещение нового контента в область просмотра — essential и разрешено; **параллакс поверх прокрутки — нет**.

### 2.2 SC 2.2.2 Pause, Stop, Hide (уровень A)

Требование [S53]: для **движущейся, мигающей, прокручивающейся** информации, которая одновременно
(1) запускается автоматически, (2) длится дольше **пяти секунд** и (3) показана **параллельно с другим контентом**, должен быть механизм паузы, остановки или скрытия, кроме случая, когда движение essential.

Для **автообновляющейся** информации исключения «пять секунд» нет вовсе: «there is no five second exception for auto-updating since it makes little sense to auto-update for a few seconds and then stop». Дополнительно допускается управление частотой обновления.

Обоснование числа 5 с: «long enough to get a user's attention, but not so long that a user cannot wait out the distraction if necessary to use the page».

**Что считается «запуском автоматически» — самая недооценённая часть критерия:** «when it starts as a result of an **indirect interaction** (such as **focusing/hovering** over an element, or **scrolling an element into view**). Content that starts automatically from an indirect interaction **also potentially fails 2.3.3**» [S53]. То есть популярный паттерн «блок анимируется при появлении в области видимости» нарушает сразу оба критерия.

**Исключение для лоадеров, важное для скелетонов:** «A preloader animation is shown on a page… **Because the moving content is not presented in parallel with other content**, no mechanism to pause, stop or hide it needs to be provided, even though the animation may run for more than 5 seconds» [S53].

Практический перевод:

| Ситуация | Нужен ли контрол |
|---|---|
| Полноэкранный лоадер, кроме него на экране ничего нет | нет |
| Скелетон таблицы, пока остальная страница уже отрисована | **да**, если шиммер идёт дольше 5 с |
| Спиннер в кнопке во время отправки формы | нет (пользователь запустил действие, длится обычно < 5 с) |
| Бегущая строка с курсами валют на дашборде | **да** |
| Автообновляемый список событий | **да**, пауза или управление частотой |
| Видео или GIF с автопроигрыванием | **да** |

Лучшая практика оттуда же: **один общий механизм** на страницу, а не отдельный контрол у каждого анимированного элемента.

### 2.3 Граница мигания и вспышки

«Blinking usually does not occur at speeds of **3 per second or more**, but it can. If blinking occurs faster than 3 per second, it would also be considered a **flash**» [S53] — то есть попадает под SC 2.3.1 (Three Flashes or Below Threshold, уровень A).

Техники: G11 (мигание меньше 5 секунд), G152 (GIF останавливается в пределах 5 секунд).

Практический предел для интерфейса: **никаких повторяющихся изменений чаще 3 Гц**. Пульсация точки-индикатора с периодом 1–2 с (0.5–1 Гц) безопасна; «стробоскоп» ошибки — нет.

---

## 3. Как реализовать

### 3.1 Reduce, а не remove

Паттерн из собственного примера MDN [S18]: анимация `pulse` (`scale` 0.9…1.1) заменяется на `dissolve` (изменение только непространственных свойств), причём **длительность в примере увеличена с 1 s до 4 s**. Смысл: движение не исчезает, оно перестаёт быть пространственным.

Kowalski даёт тот же паттерн для веб-компонентов [S14]:

```css
.element { animation: bounce 0.2s; }
@media (prefers-reduced-motion: reduce) {
  .element { animation: fade 0.2s; }
}
```

В Framer Motion — хук `useReducedMotion` и обнуление смещения: `closedX = shouldReduceMotion ? 0 : "-100%"` [S14]. То есть панель не выезжает справа, а проявляется на месте.

Шкала замен:

| Было | Стало при reduced motion |
|---|---|
| `translateX(-100%) → 0`, 300 ms | `opacity 0 → 1`, 150 ms |
| `scale(0.95) → 1` + fade, 200 ms | только fade, 150 ms |
| Пружина с перелётом 9 % | `ease-out` без перелёта, та же длительность |
| Стаггер 20 ms × 15 элементов | всё появляется сразу |
| `rotate(180deg)` у шеврона, 200 ms | мгновенная смена иконки |
| Параллакс | статичный фон |
| Автопроигрывание карусели | остановлена, ручное переключение |
| Спиннер | статичный индикатор или текст, либо оставить (вращение маленького объекта не относится к рискованным) |

Последняя строка спорная: вращение спиннера формально это пространственное движение, но его площадь мала (16–32 px), что по критерию Val Head делает его безопасным. Большинство систем спиннер при reduced motion **оставляют**. `[спорно]`

### 3.2 Что оставлять

Прямое основание — Val Head: «Animation that involves only **non-moving properties, like opacity, color, and blurs**, are unlikely to be problematic» [S17].

| Оставлять всегда | Убирать или заменять |
|---|---|
| `opacity` | `transform: translate` на расстояние больше 8 px |
| `background-color`, `color`, `border-color` | `transform: scale` больше ±5 % |
| `filter: blur()` (статически) | `transform: rotate` |
| Короткие подсветки состояния | Параллакс, scrolljacking |
| Мгновенные смены состояния | Автозапуск любых циклов |
| | Перелёт и пружины |
| | Стаггер |
| | Переходы страниц и View Transitions |

### 3.3 Чего не делать

**Не пиши глобальный «выключатель»:**

```css
/* Антипаттерн */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Почему этот популярный сниппет плох:
1. Он выключает и безопасные затухания цвета, которые по всем источникам оставлять нужно.
2. `!important` перебивает любую осознанную настройку компонента.
3. `animation-iteration-count: 1` вместе с длительностью 0.01 ms ломает компоненты, которые ждут `animationend` (элемент никогда не показывается или показывается на один кадр).
4. `transition-duration: 0.01ms` вместо `0s` оставляет событие `transitionend`, но некоторые реализации всё равно его теряют — поведение становится непредсказуемым.
5. Он ничего не заменяет: перемещение не превращается в затухание, оно просто становится мгновенным скачком. Скачок на 100 % ширины экрана — это тоже change blindness.

Приемлемое применение этого сниппета — **только как временная заглушка** на легаси-коде, который нельзя переписать. В новом продукте reduced motion строится на токенах (§3.4).

Тот же выключатель стоит по умолчанию в готовых наборах — их поведение не образец, а антипример:
- **Hallmark 2.0.0** (файл scripts/theme.mjs) пишет глобальный блок с `!important` и 0,01 ms, сохраняя только класс `.keep-motion`
  (затухание 150 ms) [S61] `[мнение вендора]`;
- **`@fluentui/react-motion` 9.16.5** при reduce по умолчанию сводит длительность движения к 1 ms [S62] — то же обнуление, что
  «150 → 1 ms» (выжимка п.18).

Норма базы — замена пространственного движения на затухание и сокращение длительностей (§3.1, §3.4), а не общий ноль.

### 3.4 Правильный уровень: токены, а не компоненты

Одна секция на файл токенов вместо двадцати правок в компонентах:

```css
:root {
  --motion-duration-instant: 0ms;
  --motion-duration-fast:    100ms;
  --motion-duration-default: 150ms;
  --motion-duration-slow:    200ms;
  --motion-duration-slower:  300ms;
  --motion-duration-slowest: 400ms;

  --motion-easing-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --motion-easing-entrance: cubic-bezier(0, 0, 0.2, 1);
  --motion-easing-exit:     cubic-bezier(0.4, 0, 1, 1);
  --motion-easing-linear:   linear;

  /* Переключатели «включено ли пространственное движение» */
  --motion-translate-sm: 4px;
  --motion-translate-md: 8px;
  --motion-scale-in:     0.95;
  --motion-stagger-step: 20ms;
}

@media (prefers-reduced-motion: reduce) {
  :root {
    /* длительности не обнуляются, а сокращаются */
    --motion-duration-slow:    150ms;
    --motion-duration-slower:  150ms;
    --motion-duration-slowest: 150ms;

    /* пространственные величины обнуляются: движение остаётся только по прозрачности */
    --motion-translate-sm: 0px;
    --motion-translate-md: 0px;
    --motion-scale-in:     1;
    --motion-stagger-step: 0ms;

    /* пружина падает на кривую без перелёта */
    --motion-spring-spatial: var(--motion-easing-entrance);
  }
}
```

Компоненты при этом написаны один раз и работают в обоих режимах:

```css
.popover {
  opacity: 0;
  transform: translateY(var(--motion-translate-sm)) scale(var(--motion-scale-in));
  transition: opacity var(--motion-duration-default) var(--motion-easing-entrance),
              transform var(--motion-duration-default) var(--motion-easing-entrance);
}
.popover[data-state="open"] { opacity: 1; transform: none; }
```

Три вещи, которые нельзя выразить переменными и которые надо выключать отдельно:
- `@keyframes` с циклом (шиммер, пульсация) — нужен отдельный `animation: none` или замена на статичную заливку;
- `View Transitions` — отключается проверкой `matchMedia('(prefers-reduced-motion: reduce)')` перед вызовом `startViewTransition`;
- `scroll-behavior: smooth` — отдельное правило.

```css
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .skeleton { animation: none; background: var(--color-bg-subtle); }
  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) { animation: none !important; }
}
```

### 3.5 Смежные медиа-фичи

| Фича | Что делает | Что делать при `reduce` |
|---|---|---|
| `prefers-reduced-motion` | движение | §3.1–3.4 |
| `prefers-reduced-transparency` | прозрачность | убрать `backdrop-filter`, сделать подложки непрозрачными, поднять контраст границ |
| `prefers-contrast` | контраст | усилить границы, убрать полупрозрачные разделители (см. `../01-color/03-contrast.md`) |
| `forced-colors` | режим высокой контрастности ОС | см. `../01-color/04-dark-theme.md` |
| `update: slow` | дисплеи с медленным обновлением (e-ink) | отключить все анимации полностью |

`prefers-reduced-transparency` особенно важен в связке со стеклом (`backdrop-filter`): см. `../04-shape-elevation/02-shadows-layers-depth.md` о правиле «не больше двух стеклянных элементов на экран».

### 3.6 Собственный переключатель в интерфейсе

Техника Gx из WCAG допускает свой контрол вместо (или вместе с) настройки ОС [S21]. Когда он нужен:
- продукт используется на общих машинах, где настройку ОС менять нельзя;
- продукт содержит визуализации данных с анимацией, которую пользователь может захотеть отключить отдельно;
- корпоративная среда с образами Windows, где Ease of Access закрыт политикой.

Реализация: три состояния — «как в системе» (по умолчанию), «полное движение», «сокращённое движение». Значение кладётся в атрибут на `<html>`, CSS учитывает оба источника:

```css
@media (prefers-reduced-motion: reduce) { :root { /* … */ } }
:root[data-motion="reduced"]  { /* те же переопределения */ }
:root[data-motion="full"]     { /* явный возврат полных значений */ }
```

Порядок важен: явный выбор пользователя в интерфейсе должен побеждать настройку ОС в обе стороны.

---

## 4. Состав готового набора токенов

| Уровень | Категория | Штук | Значения |
|---|---|---|---|
| Примитивы | `duration` | **8** | 0, 50, 100, 150, 200, 300, 400, 600 ms |
| Примитивы | `cubicBezier` | **5** | standard, entrance, exit, emphasized-decelerate, linear |
| Примитивы | `number` (пространственные величины) | **4** | translate-sm 4, translate-md 8, scale-in 0.95, stagger 20 |
| Семантика | `duration` | **6** | instant, fast, default, slow, slower, slowest |
| Семантика | `cubicBezier` | **4** | standard, entrance, exit, linear |
| Семантика | `transition` (составные) | **14** | hover, press, popup.enter/exit, menu.enter/exit, modal.enter/exit, blanket.enter/exit, drawer.enter/exit, toast.enter/exit, expand |

Итого **41 токен движения**. Для сравнения: Atlassian 72 из 596 токенов системы [S14], Material 3 — 16 длительностей + 10 кривых + 6 пружин, Radix Themes — 0 [S10].

Это укладывается в эталонную схему агента F (`../09-design-tokens/04-reference-token-schema.md`), где на движение отведено 5 примитивов длительности, 4 кривые и 7 семантических токенов: набор ниже — расширенный вариант с составными переходами; если нужен минимум, оставь §5.1 и §5.2 и выброси §5.3.

---

## 5. Токены в формате W3C DTCG

Формат: Design Tokens Format Module 2025.10. Типы согласованы с `../09-design-tokens/02-dtcg-format-and-tooling.md`: `duration` — объект `{value, unit}`; `cubicBezier` — массив из четырёх чисел; `transition` — составной `{duration, delay, timingFunction}`. Никаких строк `"150ms"`.

### 5.1 Примитивы

```json
{
  "$schema": "https://www.designtokens.org/schemas/2025.10/tokens.json",
  "duration": {
    "$type": "duration",
    "$description": "Примитивы длительности. Имя равно числу миллисекунд.",
    "0":   { "$value": { "value": 0,   "unit": "ms" } },
    "50":  { "$value": { "value": 50,  "unit": "ms" } },
    "100": { "$value": { "value": 100, "unit": "ms" } },
    "150": { "$value": { "value": 150, "unit": "ms" } },
    "200": { "$value": { "value": 200, "unit": "ms" } },
    "300": { "$value": { "value": 300, "unit": "ms" } },
    "400": { "$value": { "value": 400, "unit": "ms" } },
    "600": { "$value": { "value": 600, "unit": "ms" } }
  },
  "easing": {
    "$type": "cubicBezier",
    "standard":   { "$value": [0.4, 0, 0.2, 1], "$description": "Перемещение внутри экрана. Material 2 / Tailwind / MUI easeInOut." },
    "entrance":   { "$value": [0, 0, 0.2, 1],   "$description": "Появление, влёт в кадр. Торможение к покою." },
    "exit":       { "$value": [0.4, 0, 1, 1],   "$description": "Уход насовсем. Ускорение за край." },
    "emphasized": { "$value": [0.05, 0.7, 0.1, 1], "$description": "Material 3 emphasized-decelerate. Для крупных акцентных входов." },
    "linear":     { "$value": [0, 0, 1, 1],     "$description": "Циклы: спиннер, прогресс, шиммер." }
  },
  "motionScale": {
    "$type": "number",
    "$description": "Пространственные величины движения. При reduced motion обнуляются.",
    "translateSmall":  { "$value": 4,    "$description": "Смещение появления мелких слоёв, px. Совпадает с space.100." },
    "translateMedium": { "$value": 8,    "$description": "Смещение появления карточек и блоков, px. Совпадает с space.200." },
    "scaleIn":         { "$value": 0.95, "$description": "Начальный масштаб появления. Atlassian motion.keyframe.scale.in.small." },
    "staggerStep":     { "$value": 20,   "$description": "Шаг задержки в серии, ms. Carbon: суммарно не более 500 ms." }
  }
}
```

### 5.2 Семантика

```json
{
  "motion": {
    "duration": {
      "$type": "duration",
      "instant": { "$value": "{duration.0}",   "$description": "Фокус и всё, что должно попасть в тот же кадр." },
      "fast":    { "$value": "{duration.100}", "$description": "Hover, press, смена цвета." },
      "default": { "$value": "{duration.150}", "$description": "Значение по умолчанию для любого перехода." },
      "slow":    { "$value": "{duration.200}", "$description": "Вход поповеров и меню, раскрытие блоков." },
      "slower":  { "$value": "{duration.300}", "$description": "Модалки, дроверы, крупные панели." },
      "slowest": { "$value": "{duration.400}", "$description": "Переходы уровня страницы. Потолок для рабочего интерфейса." }
    },
    "easing": {
      "$type": "cubicBezier",
      "standard": { "$value": "{easing.standard}" },
      "entrance": { "$value": "{easing.entrance}" },
      "exit":     { "$value": "{easing.exit}" },
      "linear":   { "$value": "{easing.linear}" }
    },
    "transition": {
      "$type": "transition",
      "hover":          { "$value": { "duration": "{motion.duration.fast}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.standard}" } },
      "press":          { "$value": { "duration": "{motion.duration.fast}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.entrance}" } },
      "popupEnter":     { "$value": { "duration": "{motion.duration.default}", "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.entrance}" } },
      "popupExit":      { "$value": { "duration": "{motion.duration.fast}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.exit}" } },
      "menuEnter":      { "$value": { "duration": "{motion.duration.default}", "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.entrance}" } },
      "menuExit":       { "$value": { "duration": "{motion.duration.fast}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.exit}" } },
      "modalEnter":     { "$value": { "duration": "{motion.duration.slower}",  "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.entrance}" } },
      "modalExit":      { "$value": { "duration": "{motion.duration.slow}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.exit}" } },
      "blanketEnter":   { "$value": { "duration": "{motion.duration.slower}",  "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.entrance}" } },
      "blanketExit":    { "$value": { "duration": "{motion.duration.slow}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.exit}" } },
      "drawerEnter":    { "$value": { "duration": "{motion.duration.slower}",  "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.entrance}" } },
      "drawerExit":     { "$value": { "duration": "{motion.duration.slow}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.standard}" } },
      "toastEnter":     { "$value": { "duration": "{motion.duration.slower}",  "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.entrance}" } },
      "toastExit":      { "$value": { "duration": "{motion.duration.slow}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.exit}" } },
      "expand":         { "$value": { "duration": "{motion.duration.slow}",    "delay": { "value": 0, "unit": "ms" }, "timingFunction": "{motion.easing.standard}" } }
    }
  }
}
```

Замечание о `drawerExit`: кривая **standard**, а не exit. Это прямое применение исключения Carbon: панель уходит за край, но остаётся «рядом» и готова вернуться, поэтому тормозит на выходе [S22].

### 5.3 Режим reduced motion как модификатор резолвера

Спецификация DTCG Resolver Module 2025.10 описывает ровно эту задачу (подробно — `../09-design-tokens/03-theming-and-modes.md`, агент F). Движение становится третьим измерением темы наравне с светлая/тёмная и обычная/плотная:

```json
{
  "$schema": "https://www.designtokens.org/schemas/2025.10/resolver.json",
  "name": "ui-research-base",
  "version": "2025.10",
  "sets": [
    { "name": "primitives", "sources": [{ "$ref": "./primitives.tokens.json" }] },
    { "name": "semantic",   "sources": [{ "$ref": "./semantic.tokens.json" }] }
  ],
  "modifiers": [
    {
      "name": "motion",
      "contexts": {
        "full":    { "sources": [{ "$ref": "./motion-full.tokens.json" }] },
        "reduced": { "sources": [{ "$ref": "./motion-reduced.tokens.json" }] }
      },
      "default": "full"
    }
  ],
  "resolutionOrder": ["primitives", "semantic", "motion"]
}
```

Содержимое `motion-reduced.tokens.json` (переопределяются только пространственные величины и длинные длительности):

```json
{
  "motion": {
    "duration": {
      "$type": "duration",
      "slow":    { "$value": "{duration.150}" },
      "slower":  { "$value": "{duration.150}" },
      "slowest": { "$value": "{duration.150}" }
    }
  },
  "motionScale": {
    "$type": "number",
    "translateSmall":  { "$value": 0 },
    "translateMedium": { "$value": 0 },
    "scaleIn":         { "$value": 1 },
    "staggerStep":     { "$value": 0 }
  }
}
```

Модификатор ортогонален теме и плотности: он трогает только токены движения и не пересекается с цветом и размерами. Это то, чего требует спецификация резолвера («контексты должны трогать непересекающиеся токены»).

---

## 6. Тот же набор в CSS

Готов к вставке целиком. Значения соответствуют §5.

```css
:root {
  /* ── Примитивы ──────────────────────────────────────────── */
  --duration-0:   0ms;
  --duration-50:  50ms;
  --duration-100: 100ms;
  --duration-150: 150ms;
  --duration-200: 200ms;
  --duration-300: 300ms;
  --duration-400: 400ms;
  --duration-600: 600ms;

  --easing-standard:   cubic-bezier(0.4, 0, 0.2, 1);
  --easing-entrance:   cubic-bezier(0, 0, 0.2, 1);
  --easing-exit:       cubic-bezier(0.4, 0, 1, 1);
  --easing-emphasized: cubic-bezier(0.05, 0.7, 0.1, 1);
  --easing-linear:     linear;

  /* ── Семантика: длительности ───────────────────────────── */
  --motion-duration-instant: var(--duration-0);
  --motion-duration-fast:    var(--duration-100);
  --motion-duration-default: var(--duration-150);
  --motion-duration-slow:    var(--duration-200);
  --motion-duration-slower:  var(--duration-300);
  --motion-duration-slowest: var(--duration-400);

  /* ── Семантика: кривые ─────────────────────────────────── */
  --motion-easing-standard: var(--easing-standard);
  --motion-easing-entrance: var(--easing-entrance);
  --motion-easing-exit:     var(--easing-exit);
  --motion-easing-linear:   var(--easing-linear);

  /* ── Пространственные величины (обнуляются при reduce) ─── */
  --motion-translate-sm: 4px;
  --motion-translate-md: 8px;
  --motion-scale-in:     0.95;
  --motion-stagger-step: 20ms;

  /* ── Составные переходы ────────────────────────────────── */
  --motion-hover:         var(--motion-duration-fast)    var(--motion-easing-standard);
  --motion-press:         var(--motion-duration-fast)    var(--motion-easing-entrance);
  --motion-popup-enter:   var(--motion-duration-default) var(--motion-easing-entrance);
  --motion-popup-exit:    var(--motion-duration-fast)    var(--motion-easing-exit);
  --motion-modal-enter:   var(--motion-duration-slower)  var(--motion-easing-entrance);
  --motion-modal-exit:    var(--motion-duration-slow)    var(--motion-easing-exit);
  --motion-blanket-enter: var(--motion-duration-slower)  var(--motion-easing-entrance);
  --motion-blanket-exit:  var(--motion-duration-slow)    var(--motion-easing-exit);
  --motion-drawer-enter:  var(--motion-duration-slower)  var(--motion-easing-entrance);
  --motion-drawer-exit:   var(--motion-duration-slow)    var(--motion-easing-standard);
  --motion-toast-enter:   var(--motion-duration-slower)  var(--motion-easing-entrance);
  --motion-toast-exit:    var(--motion-duration-slow)    var(--motion-easing-exit);
  --motion-expand:        var(--motion-duration-slow)    var(--motion-easing-standard);

  /* ── Циклы ─────────────────────────────────────────────── */
  --motion-spin:    1s   var(--easing-linear) infinite;
  --motion-shimmer: 1.8s var(--easing-standard) infinite;
}

/* ── Сокращённое движение ─────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  :root {
    --motion-duration-slow:    var(--duration-150);
    --motion-duration-slower:  var(--duration-150);
    --motion-duration-slowest: var(--duration-150);
    --motion-translate-sm: 0px;
    --motion-translate-md: 0px;
    --motion-scale-in:     1;
    --motion-stagger-step: 0ms;
    --motion-easing-emphasized: var(--easing-entrance);
  }
  html { scroll-behavior: auto; }
  .skeleton, [data-loading] { animation: none; }
  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) { animation: none !important; }
}

/* Явный выбор пользователя в интерфейсе перебивает настройку ОС */
:root[data-motion="reduced"] {
  --motion-duration-slow:    var(--duration-150);
  --motion-duration-slower:  var(--duration-150);
  --motion-duration-slowest: var(--duration-150);
  --motion-translate-sm: 0px;
  --motion-translate-md: 0px;
  --motion-scale-in:     1;
  --motion-stagger-step: 0ms;
}
:root[data-motion="full"] {
  --motion-duration-slow:    var(--duration-200);
  --motion-duration-slower:  var(--duration-300);
  --motion-duration-slowest: var(--duration-400);
  --motion-translate-sm: 4px;
  --motion-translate-md: 8px;
  --motion-scale-in:     0.95;
  --motion-stagger-step: 20ms;
}

/* ── Примеры применения ───────────────────────────────────── */
.button {
  transition: background-color var(--motion-hover),
              border-color     var(--motion-hover),
              color            var(--motion-hover);
}
.button:focus-visible { transition: none; }          /* фокус в том же кадре */

.popover {
  opacity: 0;
  transform: translateY(var(--motion-translate-sm)) scale(var(--motion-scale-in));
  transform-origin: var(--radix-popover-content-transform-origin, center);
  transition: opacity var(--motion-popup-exit), transform var(--motion-popup-exit);
}
.popover[data-state="open"] {
  opacity: 1;
  transform: none;
  transition: opacity var(--motion-popup-enter), transform var(--motion-popup-enter);
}

dialog {
  opacity: 0;
  transform: scale(var(--motion-scale-in));
  transition: opacity var(--motion-modal-exit),
              transform var(--motion-modal-exit),
              overlay var(--motion-modal-exit) allow-discrete,
              display var(--motion-modal-exit) allow-discrete;
}
dialog[open] {
  opacity: 1;
  transform: none;
  transition: opacity var(--motion-modal-enter), transform var(--motion-modal-enter),
              overlay var(--motion-modal-enter) allow-discrete,
              display var(--motion-modal-enter) allow-discrete;
}
@starting-style { dialog[open] { opacity: 0; transform: scale(var(--motion-scale-in)); } }

.accordion { display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--motion-expand); }
.accordion[data-open] { grid-template-rows: 1fr; }
.accordion > * { overflow: hidden; }

.spinner  { animation: spin var(--motion-spin); }
.skeleton { animation: shimmer var(--motion-shimmer); }
@keyframes spin    { to { transform: rotate(360deg); } }
@keyframes shimmer { 50% { opacity: 0.5; } }

/* Стаггер: индекс строки передаётся из шаблона */
.row { animation: fade-in var(--motion-duration-default) var(--motion-easing-entrance) backwards;
       animation-delay: calc(var(--row-index, 0) * var(--motion-stagger-step)); }
@keyframes fade-in { from { opacity: 0; } }
```

Вариант для Tailwind v4 (`@theme`):

```css
@theme {
  --default-transition-duration: 150ms;
  --default-transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-entrance: cubic-bezier(0, 0, 0.2, 1);
  --ease-exit:     cubic-bezier(0.4, 0, 1, 1);
  --animate-spin:    spin 1s linear infinite;
  --animate-shimmer: shimmer 1.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}
```

---

## 7. Два пресета движения

Оба опираются на пресеты волны 1: «Плотная админка» и «Клиентский сервис» из `../03-spacing-sizing/03-control-and-panel-sizes.md` §8–§9 и `../02-typography/02-type-scale.md` §7–§8. Числа ниже не переопределяют их, а дополняют движением.

### 7.1 Пресет А: плотная админка, бэк-офис, инструмент

Установка: **движение не должно быть заметно**. Пользователь проводит в интерфейсе весь рабочий день и повторяет одни и те же действия сотни раз.

| Параметр | Значение |
|---|---|
| Длительность по умолчанию | **100 ms** |
| Потолок | **200 ms** (кроме затемнения фона модалки — 250) |
| Кривые | две: `standard` `cubic-bezier(0.4, 0, 0.2, 1)` и `linear` для циклов |
| Перелёт | **нет** |
| Пружины | **нет** |
| Масштаб при появлении | **нет** (`scaleIn` = 1) |
| Смещение при появлении | 4 px для поповеров, 0 для остального |
| Стаггер | **нет** |
| Переходы страниц | **нет** |
| View Transitions | **нет** |

Каталог:

| Элемент | Значение |
|---|---|
| hover строки таблицы, ячейки, пункта меню | **70 ms**, `background-color` |
| hover кнопки, ссылки | 100 ms, `background-color`, `border-color`, `color` |
| pressed | 100 ms, только цвет, без `scale` |
| фокус | **0 ms** |
| поповер, дропдаун, комбобокс | вход 150 ms fade + 4 px, выход 100 ms fade |
| тултип | вход 100 ms fade, выход 100 ms |
| модалка | подложка 150 ms fade, окно 150 ms fade (без масштаба) |
| дровер, инспектор | 200 ms, `translateX`, ease-out; выход 150 ms, standard |
| сворачивание сайдбара | 200 ms, `grid-template-columns` |
| раскрытие строки, аккордеон | 200 ms, `grid-template-rows` |
| шеврон | 150 ms, `rotate` |
| вкладки | **без анимации** (переключаются с клавиатуры) |
| тост | вход 200 ms, выход 150 ms |
| чекбокс, переключатель | 100 ms |
| спиннер | 1 s linear |
| скелетон | 1.8 s, opacity 1 → 0.5 |
| подсветка изменившегося | затухание 1500 ms |
| сортировка и перестановка строк | **без анимации** |
| обновление данных | **без анимации** |

Переопределение токенов относительно §6:

```css
:root[data-preset="admin"] {
  --motion-duration-default: 100ms;
  --motion-duration-slow:    150ms;
  --motion-duration-slower:  200ms;
  --motion-duration-slowest: 200ms;
  --motion-translate-sm: 4px;
  --motion-translate-md: 0px;
  --motion-scale-in:     1;
  --motion-stagger-step: 0ms;
  --motion-easing-entrance: var(--easing-standard);
  --motion-easing-exit:     var(--easing-standard);
}
```

Обоснование: Carbon (productive-личность, длительности 70–240 ms), Atlassian (interactions 50–150), измерения плотных продуктов выборки — Carbon DataTable 70 ms, Consta 150 ms, shadcn 150 ms [S4], [S23], [S56].

### 7.2 Пресет Б: клиентский сервис, личный кабинет, SaaS

Установка: **движение помогает понять, что произошло**, и несёт характер продукта, но остаётся коротким.

| Параметр | Значение |
|---|---|
| Длительность по умолчанию | **150 ms** |
| Потолок | **400 ms** (600 для онбординга) |
| Кривые | четыре: standard, entrance, exit, linear |
| Перелёт | допустим **на одном-двух элементах** (переключатель, подтверждение), не больше 5 % |
| Пружины | одна, на переключателе и перетаскивании |
| Масштаб при появлении | **0.95** |
| Смещение при появлении | 4 px мелкое, 8 px блоки |
| Стаггер | 20 ms, до 15 элементов |
| Переходы страниц | fade 150 ms |
| View Transitions | как прогрессивное улучшение, 200–250 ms |

Каталог:

| Элемент | Значение |
|---|---|
| hover строки списка | 70–100 ms |
| hover кнопки, карточки | 150 ms; карточка поднимается на 1–2 px с тенью |
| pressed | 100 ms, `scale(0.98)` допустим |
| фокус | **0 ms** |
| поповер, дропдаун | вход 150 ms, `opacity` + `scale(0.95→1)` от триггера; выход 100 ms |
| тултип | вход 150 ms fade, выход 100 ms |
| модалка | подложка 250 ms, окно 250 ms `opacity` + `scale(0.95→1)`; выход 200 / 200 |
| дровер | вход 300 ms ease-out, выход 250 ms standard |
| раскрытие блока | 200 ms (< 200 px), 300 ms (крупный) |
| вкладки | индикатор 200 ms через `clip-path` или `transform` |
| тост | вход 250 ms ease-out-bold, выход 200 ms ease-in-practical; перестановка стопки 200 ms |
| чекбокс | 150 ms |
| переключатель | 200 ms или пружина `motion.spring.snap` (ζ 0.7, k 380: 340 ms, перелёт 4.6 %) |
| загрузка страницы | стаггер 20 ms по порядку Carbon (§`02-what-to-animate-in-apps.md` §6.2) |
| спиннер | 0.8 s linear |
| скелетон | 1.8 s |
| переход между разделами | fade 150 ms контентной области |
| онбординг, полноэкранный шаг | 400–600 ms |

Переопределение токенов: базовый набор §6 применяется как есть; добавляется пружина — токен `transition` с расширением
пружины (форма и нормы сборки — `04-spring-tokens-transitions-platforms.md` §1):

```json
{
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
          }
        }
      }
    }
  }
}
```

Сборка ДС (`ds_build`) выводит из него переменную, её параметры и блок сокращённого движения `[проверено: вывод ds_build]`:

```css
:root {
  /* пружина: dampingRatio 0.7, stiffness 380 (масса 1, ω 19.49 рад/с), перелёт 4.6 %, успокоение до 1 % пути — 340 ms */
  --motion-spring-snap: 340ms linear(0, 0.007 1.85%, 0.028 3.8%, 0.063 5.9%, 0.114 8.2%, 0.162 10.1%, 0.223 12.3%, 0.469 20.5%, 0.574 24.15%, 0.672 27.9%, 0.754 31.45%, 0.819 34.7%, 0.874 37.95%, 0.921 41.25%, 0.959 44.65%, 0.994 48.75%, 1.02 53.15%, 1.037 57.9%, 1.045 63.2%, 1.045 68.7%, 1.04 75.55%, 1.009 93.1%, 1);
}
@media (prefers-reduced-motion: reduce) {
  :root:not([data-motion="full"]) { --motion-spring-snap: 150ms cubic-bezier(0, 0, 0.2, 1); }
}
:root[data-motion="reduced"] { --motion-spring-snap: 150ms cubic-bezier(0, 0, 0.2, 1); }

.switch__thumb { transition: transform var(--motion-spring-snap); }
```

Строка — кривая затухающего осциллятора `x(t) = 1 − e^(−ζω_n·t)·(cos(ω_d·t) + (ζω_n/ω_d)·sin(ω_d·t))` при m = 1,
k = 380, ζ = 0.7: ω_n = 19.49 рад/с, ω_d = 13.92, пик 1.046 на 226 ms; время — последний выход кривой из полосы 1 %
пути (337 ms, вверх до 340); 23 точки стоят там, где кривая гнётся, ломаная отходит от кривой не больше чем на 0,18 %
пути. Параметры в токене — то, из чего строку пересобирают; переносится она на Compose и SwiftUI теми же числами
(`04-spring-tokens-transitions-platforms.md` §2.2).

Те же нормы сборки для двух других пружин:

| Пружина | k | ζ | Время CSS (успокоение до 1 %) | Перелёт | Точек `linear()` |
|---|---|---|---|---|---|
| M3 standard default spatial | 700 | 0.9 | **200 ms** | 0.15 %: кривая успокаивается раньше пика | 22 |
| M3 expressive default spatial | 380 | 0.8 | **330 ms** | 1.5 % | 22 |
| «Щелчок» переключателя | 380 | 0.7 | **340 ms** | 4.6 % | 23 |

### 7.3 Сравнение пресетов

| Параметр | А: админка | Б: клиентский |
|---|---|---|
| Дефолт | 100 ms | 150 ms |
| Потолок | 200 ms | 400 ms |
| Кривых | 2 | 4 |
| Пружин | 0 | 1 |
| `scaleIn` | 1 (нет) | 0.95 |
| Стаггер | нет | 20 ms |
| Переход страниц | нет | fade 150 ms |
| Перелёт | нет | до 5 %, точечно |
| Число токенов движения | 20 | 41 |

---

## 8. Что показывают измерения

Из 24 живых продуктов (`01-durations-easings-springs.md` §6) **ни один не объявляет отдельных длительностей для `prefers-reduced-motion` в computed styles**, снятых при обычных настройках. Метод измерения этого и не показал бы (браузер запускался без флага reduced motion), поэтому строго говорится не «никто не поддерживает», а «проверить не удалось». Это дыра метода, а не вывод.

Что метод показал:
- 21 продукт из 24 имеет хотя бы одно объявление `transition-duration`; два (Gitea, Redmine) не имеют ни одного и работают полностью без движения — и выглядят при этом нормально, что само по себе аргумент в пользу пресета А.
- 0 ms встречается 21 раз (MUI dashboard) — то есть выключение перехода через токен применяется на практике.

Рекомендация для следующей волны: прогнать `measure_ui.py` с `reduced_motion: 'reduce'` в контексте Playwright и сравнить. Это дешёвая и показательная проверка, которой сейчас нет ни у кого.

---

## 9. Частые ошибки

1. **Нет блока `@media (prefers-reduced-motion: reduce)` вообще** при двадцати анимациях в продукте.
2. **Глобальный `!important`-выключатель** вместо замены пространственного движения на непространственное (§3.3).
3. **Обнуление длительности до 0.01 ms**, из-за чего ломаются компоненты, ждущие `transitionend`.
4. **Reduced motion реализован в компонентах, а не в токенах** — при добавлении двадцать первого компонента про него забывают.
5. **`scroll-behavior: smooth` остаётся включённым** при reduced motion.
6. **View Transitions не отключаются**: `startViewTransition` вызывается без проверки `matchMedia`.
7. **Циклические `@keyframes` (шиммер, пульсация) не выключаются**, потому что их не покрывает переопределение переменных.
8. **Автопроигрывание карусели или видео без контрола паузы** — прямое нарушение SC 2.2.2 (уровень A).
9. **Скелетон шиммерит дольше 5 секунд рядом с уже загруженным контентом** — то же нарушение.
10. **Анимация, запускаемая появлением блока в области видимости** — нарушает 2.2.2 и 2.3.3 одновременно (§2.2).
11. **Мигание индикатора чаще 3 Гц** — попадает под SC 2.3.1.
12. **Пружина остаётся пружиной при reduced motion** (перелёт — пространственное движение).
13. **Стаггер остаётся при reduced motion**: серия из пятнадцати последовательно выезжающих строк — ровно тот случай, ради которого фича создана.
14. **Собственный переключатель движения не побеждает настройку ОС** в обе стороны (§3.6).
15. **`prefers-reduced-transparency` не обработан** там, где применён `backdrop-filter`.

### 9.1 Ошибки, характерные для нейросетей

16. **Сгенерированный код содержит `framer-motion` с дюжиной анимаций и ни одной проверки `useReducedMotion`.**
17. **В `tailwind.config` добавлены кастомные `keyframes`, но `@media (prefers-reduced-motion)` не добавлен нигде.**
18. **Копируется популярный сниппет глобального выключателя** (§3.3) и подаётся как «поддержка доступности»; так же — общий reduce
    готовых наборов (Hallmark theme.mjs, 1 ms у `@fluentui/react-motion`) без своей замены движения.
19. **Анимации появления при прокрутке (`whileInView`, AOS)** переносятся из лендингов в приложение.
20. **Токены движения объявлены как строки `"150ms"`**, а не как `duration`-объекты DTCG, из-за чего валидатор токенов их не проверяет.

---

## 10. Чек-лист

1. Есть ли в проекте хотя бы один блок `@media (prefers-reduced-motion: reduce)`?
2. Реализован ли он переопределением токенов, а не правками в компонентах?
3. Пространственные величины (`translate`, `scale`, стаггер) обнуляются, а длительности сокращаются, а не обнуляются?
4. Переходы по `opacity` и цвету остаются работать?
5. Циклические анимации (шиммер, пульсация) выключаются отдельным правилом?
6. `scroll-behavior` возвращается к `auto`?
7. View Transitions отключаются проверкой `matchMedia`?
8. Пружины заменяются на кривую без перелёта?
9. Есть ли в интерфейсе собственный переключатель движения, и побеждает ли он настройку ОС в обе стороны?
10. Ни одна анимация, запущенная страницей, не идёт дольше 5 секунд параллельно с другим контентом без контрола паузы?
11. Нет ли анимаций, запускаемых появлением элемента в области видимости?
12. Нет ли повторяющихся изменений чаще 3 раз в секунду?
13. Период цикла шиммера или пульсации не попадает в диапазон 4–6 секунд?
14. Обработан ли `prefers-reduced-transparency` там, где есть `backdrop-filter`?
15. Все токены движения записаны типами `duration` и `cubicBezier` по DTCG?
16. Выбран ли пресет (А или Б) и зафиксирован ли он в токенах целиком, без смешения?
17. Совпадает ли набор токенов движения со схемой агента F (`../09-design-tokens/`)?
18. Проверен ли интерфейс с включённой настройкой ОС вручную, а не только по коду?

---

## 11. Открытые вопросы

1. **Спиннер при reduced motion: оставлять или заменять?** Формально это пространственное движение; по критерию площади (Val Head) — безопасное. Единого ответа в источниках нет. `[спорно]` (§3.1)
2. **Измерения не покрывают reduced motion** (§8): нужен повторный прогон `measure_ui.py` с `reduced_motion: 'reduce'`.
3. **`web.dev/articles/prefers-reduced-motion`** недоступен из этой среды (Errno 101); рекомендации Google по этой теме в базе отсутствуют.
4. **Количественных исследований того, насколько сокращённое движение помогает**, найти не удалось: все источники ссылаются на клинические описания вестибулярных нарушений, а не на измерения в интерфейсах. Уровень всех правил раздела — `[консенсус]` и `[стандарт]`, но не `[исследование]`.
5. **Порог «не более 3 одновременных подсветок»** и **потолок стаггера в 15 элементов** выведены из практики, первичных источников нет. `[мнение]`
6. **Материал по `update: slow` (e-ink)** не проверялся; строка в таблице §3.5 основана на определении медиа-фичи, а не на опыте.
7. **Размытие при reduced motion**: §3.2 оставляет размытие (Val Head), Apple при Reduce Motion просит не анимировать вход в
   размытие и выход из него [S66]; до решения — размытие при reduce только статичное, без анимации радиуса `[спорно]`.

---

## Источники

Снимок: 28.10.2026 — день сверки источников S61, S62 и S66.

Полные аннотации — в `01-durations-easings-springs.md` и `../99-raw/notes/wave2/M-notes.md`.

- `[S4]` IBM `@carbon/motion` — длительности с назначением.
- `[S10]` Radix Themes — отсутствие токенов движения (листинг каталога).
- `[S14]` Emil Kowalski, «Great Animations» — паттерн замены bounce на fade, `useReducedMotion`.
- `[S17]` Val Head, «Designing Safer Web Animation For Motion Sensitivity», A List Apart, 2015 — три фактора риска, цифры по вестибулярным нарушениям, список безопасных свойств.
- `[S18]` MDN, `prefers-reduced-motion` — Baseline с января 2020, таблица настроек ОС, пример «pulse → dissolve».
- `[S20]` MDN, `@starting-style` — три условия для анимации top layer.
- `[S21]` W3C, WCAG 2.2 Understanding SC 2.3.3 (через web.archive) — уровень AAA, техники C39, SCR40, Gx.
- `[S22]` IBM Carbon, Motion: overview — исключение для уходящей панели, чек-лист.
- `[S23]` Atlassian Design System, Motion — диапазоны длительностей, четыре кривые.
- `[S53]` W3C, WCAG 2.2 Understanding SC 2.2.2 Pause, Stop, Hide (через web.archive) — уровень A, правило пяти секунд, косвенный запуск, исключение для лоадеров, порог 3 Гц.
- `[S56]` Собственный пересчёт измерений агента P, 24 продукта.
- `[S61]` Hallmark 2.0.0, https://github.com/Nutlope/hallmark: scripts/theme.mjs (глобальный блок reduce с `!important` 0,01 ms, класс `.keep-motion`); через `../../creative/02-references-moodboards/04-motion-libraries-and-rules.md` §4.2 [S45] — `[мнение вендора]`.
- `[S62]` Microsoft Fluent 2, https://fluent2.microsoft.design/motion; `@fluentui/react-motion` 9.16.5, файл dist/index.d.ts (reduce по умолчанию — 1 ms); через тот же обзор §4.1 [S40].
- `[S66]` Apple, Human Interface Guidelines (JSON API): `…/human-interface-guidelines/accessibility.json` (запись журнала — июнь 2025), `…/motion.json` (сентябрь 2025) — список Reduce Motion: убрать автоматические и повторяющиеся анимации, пружины без отскока, переходы по x, y, z — затуханием, не анимировать вход в размытие и выход из него; через тот же обзор §4.1 [S38].
- Формат токенов согласован с `../09-design-tokens/` (агент F, заметки `../99-raw/notes/wave2/F-notes.md` §S1: `duration` = объект `{value, unit}`, `cubicBezier` = массив из 4 чисел, `transition` = составной тип, Resolver Module 2025.10).
