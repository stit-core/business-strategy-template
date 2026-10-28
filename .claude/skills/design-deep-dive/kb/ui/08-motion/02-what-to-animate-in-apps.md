# Что анимировать в веб-сервисах и с какими числами

Волна 2, агент M, 22 сентября 2026. Источников прочитано целиком: 59, плюс измерения 24 живых продуктов.

Смежные файлы: сами числа длительностей и кривых — `01-durations-easings-springs.md`; доступность и готовые токены — `03-reduced-motion-and-motion-tokens.md`; переходы по шаблонам интерфейса токенами и их перевод на веб, Compose и SwiftUI — `04-spring-tokens-transitions-platforms.md` §3. Визуальные спецификации самих компонентов (размеры, отступы, состояния) — `../06-components-visual/` (агент E). Тени при подъёме карточки и фокус-кольцо — `../04-shape-elevation/02-shadows-layers-depth.md`. Сценарная сторона (когда показывать индикатор загрузки, какие задержки допустимы, тексты) — `../../ux/06-feedback-states-motion/`.

## Выжимка для агента

1. **Анимируй только `transform` и `opacity`.** Они задевают только последний шаг рендера (composite); `height`, `width`, `top`, `margin`, `padding` задевают все три. → §4.1 [консенсус]
2. **Бюджет кадра — 16.6 ms при 60 fps.** Для сравнения, моргание занимает 100–300 ms. → §4.1 [консенсус]
3. **Одно-два свойства на переход.** Atlassian: «Combine properties sparingly. Typically, aim for one or two properties per transition». Рекомендуемая пара — `opacity` + `translate`. → §1 [система]
4. **Поповер и меню растут из триггера.** `transform-origin` ставится в точку привязки; в Radix для этого есть готовая переменная `--radix-popover-content-transform-origin`. → §2.3 [консенсус]
5. **Масштаб появления 95 → 100 %, а не 80 → 100 % и никогда не от `scale(0)`.** Токен Atlassian `motion.keyframe.scale.in.small`. Mantine `pop` идёт от 0.9, Kowalski — от 0.9–0.97. → §2.3 [система]
6. **Смещение появления берётся из шкалы отступов: 4 или 8 px.** Polaris задаёт его ссылкой на `--p-space-100`. Mantine `pop` = 10 px, `fade-*` = 30 px. → §2.3 [система]
7. **Таблица: 70 ms на hover строки, без анимации самих данных.** Carbon DataTable держит 70 ms на 49 из 52 объявлений. Обновление чисел в ячейках не анимируется вовсе. → §3.4 [система + измерение]
8. **Стаггер 20 ms, общая длительность серии ≤ 500 ms.** Carbon: при 20 ms шаге это максимум ≈ 25 элементов. → §6.1 [система]
9. **Порядок появления: оболочка → статика тела → данные → первичная кнопка → графики.** → §6.2 [система]
10. **Аккордеон и раскрытие строки: `grid-template-rows: 0fr → 1fr`**, а не `height`. Второй вариант — `clip-path`, третий — `height: auto` с `interpolate-size` (ограниченная поддержка). → §4.2 [консенсус]
11. **Спиннер 0.75–1 s, `linear`, бесконечно.** Tailwind: `spin 1s linear infinite`. → §3.7 [система]
12. **Шиммер скелетона 1.5–2 s.** Tailwind `pulse 2s cubic-bezier(0.4,0,0.6,1) infinite`, keyframes `50% { opacity: 0.5 }`. Период не должен быть около 5 с (0.2 Hz — частота, к которой люди особенно чувствительны). → §3.7 [система + Apple]
13. **Подсветка изменившегося («flash») 1–2 s на затухание**, начинается сразу, без задержки. → §3.10 [мнение]
14. **Не анимируй числа в таблицах и дашбордах count-up'ом.** Kowalski про функциональный график: «no animation would be better». → §3.9 [мнение]
15. **`@starting-style` + `transition-behavior: allow-discrete` + `overlay` — три обязательных части** для анимации `<dialog>` и popover в top layer. → §5.1 [документация]
16. **`will-change` только на элементы, которые действительно вот-вот поедут**, и снимать после. Постоянный `will-change` на десятках элементов съедает память GPU. → §4.4 [консенсус]
17. **`backdrop-filter` анимировать нельзя.** Максимум — анимировать `opacity` слоя, у которого фильтр уже применён. → §4.3 [консенсус]
18. **View Transitions в приложении за авторизацией — прогрессивное улучшение, не основа.** Переходы в документе — Baseline с октября 2025 (Chrome 111, Safari 18, Firefox 144). → §5.3 [документация] (статус) [мнение] (правило)
19. **Scroll-driven animations в админке не нужны.** Единственное оправданное применение — индикатор прогресса чтения длинного документа. → §5.4 [мнение]
20. **Hover карточки: тень и смещение 1–2 px, не `scale`.** → §3.5, `../04-shape-elevation/02-shadows-layers-depth.md` [консенсус]
21. **Полоса под активной вкладкой переезжает через `clip-path` или `transform`, а не через две независимые анимации**, иначе подсветка и цвет текста рассинхронизируются. → §3.3 [мнение: Kowalski]
22. **Пути движения не идут по диагонали.** Carbon: горизонталь и вертикаль сдвигаются по времени, получается путь со скруглённым углом. → §6.3 [система]
23. **Затемнение фона (blanket) под модалкой — отдельный токен и отдельная длительность.** Atlassian: 250 ms, fade 0 → 100 %. Carbon отводит на это до 700 ms. → §3.2 [система]
24. **Ничего не анимируй в ответ на клавиатуру.** → §7.1 [мнение]
25. **Проверка перед добавлением движения: «если я это уберу, пользователь потеряет информацию или контекст?»** → §7 [система]

---

## 1. Как читать каталог

Каждая строка каталога ниже — четвёрка: **свойство → длительность → кривая → откуда значение**. Правила, общие для всех строк:

- **Свойств одно или два.** Atlassian: «Combine properties sparingly. Typically, aim for **one or two properties per transition**. Use opacity with a transform for directional transitions» [S25].
- **Четыре свойства движения, и больше ничего** (Atlassian): `scale`, `fade` (opacity), `slide` (translate X/Y), `color` [S23].
- **Вход и выход разные** (`01-durations-easings-springs.md` §3).
- **Значения смещений берутся из шкалы отступов**, а не изобретаются: 4, 8, 12, 16 px (`../03-spacing-sizing/01-spacing-scale.md`).
- **Темп — по размеру компонента.** Material 3 выбирает скорость пружины так: fast — переключатель и кнопка, default — нижняя
  панель и дровер, slow — полноэкранный переход [S59]; у длительностей то же правило — `01-durations-easings-springs.md` §5.2.

Два пресета: **А — плотная админка** (минимум движения), **Б — клиентский сервис** (движение как часть характера). Полные наборы токенов для обоих — в `03-reduced-motion-and-motion-tokens.md` §6.

---

## 2. Базовые приёмы появления

### 2.1 Fade (только прозрачность)

Самый дешёвый и самый безопасный приём: не задевает раскладку, не вызывает вестибулярных проблем (Val Head: «Animation that involves only non-moving properties, like opacity, color, and blurs, are unlikely to be problematic» [S17]), не требует `transform-origin`.

| Параметр | Значение |
|---|---|
| Свойство | `opacity: 0 → 1` |
| Вход | 150 ms, ease-out |
| Выход | 100 ms, ease-in |
| Когда | тултип, подложка, изменение содержимого на месте, всё при `prefers-reduced-motion` |

### 2.2 Slide (смещение)

| Параметр | Значение |
|---|---|
| Свойства | `opacity` + `transform: translateY(±4…8px)` |
| Вход | 150–200 ms, ease-out |
| Выход | 100–150 ms, ease-in |
| Смещение | **4 px** для мелких элементов (поповер, тултип), **8 px** для карточек и блоков, **16–24 px** для панелей |

Справочные значения систем: Polaris `appear-above` = `translateY(var(--p-space-100))` = 4 px [S2]; Mantine `pop` = `translateY(±10px)`, `fade-up/down` = 30 px [S13]. Значение 30 px у Mantine зарезервировано под самостоятельные блоки, а не под поповеры.

### 2.3 Scale (масштаб) и origin-aware появление

| Параметр | Значение |
|---|---|
| Свойства | `opacity` + `transform: scale(0.95 → 1)` |
| Вход | 120–200 ms, ease-out |
| Выход | 100–150 ms, ease-in, `scale(1 → 0.95)` |

**Число 0.95 — не произвольное.** Atlassian фиксирует его токеном: `motion.keyframe.scale.in.small` = **95 → 100 %**, `motion.keyframe.scale.out.small` = 100 → 95 % [S25]. Mantine `pop` начинает с 0.9 [S13]. Всё, что меньше 0.9, читается как «выпрыгивание» и в рабочем интерфейсе неуместно. Kowalski формулирует то же запретом: появление **никогда не начинается с `scale(0)`** — только с 0.9–0.97 вместе с `opacity: 0` [S64] `[мнение]`.

**Origin-aware — главная деталь, которую пропускают.** Kowalski: выпадающее меню должно расти **из кнопки**, а не из своего центра. Дефолтный `transform-origin: center` заменяется на точку привязки; у Radix есть готовая переменная `--radix-popover-content-transform-origin`, в shadcn/ui она уже подключена [S15].

Атлассиан формулирует то же как пространственный якорь: «A Dropdown should open **from its trigger**, and a dismissed panel should exit **in the direction it entered**» [S25]. Именно поэтому у них четыре токена входа поповера по направлениям: `motion.popup.enter.{top,bottom,left,right}`.

```css
/* Поповер, растущий из триггера */
.popover {
  transform-origin: var(--radix-popover-content-transform-origin);
  transition: opacity 150ms cubic-bezier(0,0,0.2,1), transform 150ms cubic-bezier(0,0,0.2,1);
}
.popover[data-state="closed"] { opacity: 0; transform: scale(0.95); }
```

### 2.4 Замена перемещения на затухание

Apple: «Consider using fades when you need to relocate an object… you can **fade the object out before moving it and fade it back in** after it's in the new location» [S12]. Приём полезен, когда путь объекта длинный или пересекает другой контент: вместо перелёта через половину экрана — исчезновение и появление на месте. Длительности: выход 100 ms, пауза 0, вход 150 ms.

---

## 3. Каталог: компонент → движение

### 3.1 Кнопка, ссылка, интерактивная строка

| Что | Свойства | Длительность | Кривая | Пресет А | Пресет Б |
|---|---|---|---|---|---|
| hover фона | `background-color` | 100–150 ms | ease / out-practical | 100 | 150 |
| hover строки списка или таблицы | `background-color` | **50–70 ms** | ease-out | 70 | 70 |
| pressed | `background-color`, `transform: scale(0.98)` | 100 ms | ease-out | 100, без scale | 100 |
| фокус | — | **0 ms** | — | 0 | 0 |
| disabled ↔ enabled | `opacity` | 100 ms | linear | 100 | 100 |

Обоснования: Atlassian `motion.duration.xxshort` 50 ms с примером «List item hover, 50 ms»; `motion.duration.instant` 0 ms «immediate feedback (focus state)»; кривая для интеракций только `out.practical` `cubic-bezier(0.4, 1, 0.6, 1)`: «At interaction-scale durations, easing differences are subtle but still matter. Use practical curves as they provide natural deceleration without the dramatic character of bold curves» [S25]. Carbon `duration-fast-01` 70 ms: «Micro-interactions such as button and toggle. Instant response to user action» [S4]; чек-лист Carbon требует укладывать микровзаимодействия в **90–120 ms** [S22].

Составной токен Atlassian целиком: `motion.button.hovered` = `background-color 150ms …, border-color 150ms …` [S14] — то есть цвет фона и цвет границы едут синхронно, одним токеном.

**Не анимируй:** кольцо фокуса, смену текста на кнопке, переход в состояние загрузки (спиннер появляется без анимации, иначе задержка удваивается).

### 3.2 Модальное окно и диалог

| Часть | Свойства | Вход | Выход |
|---|---|---|---|
| Подложка (blanket, scrim) | `opacity` 0 → 1 | 250 ms, ease-out | 200 ms, ease-in |
| Окно | `opacity` + `transform: scale(0.95 → 1)` или `translateY(8px → 0)` | 250 ms, ease-in-out-bold | 200 ms, ease-in-practical |

Источники: Atlassian «Modal entrance, 250 ms», `motion.modal.enter` / `motion.modal.exit`, `motion.blanket.enter` = `250ms cubic-bezier(0.4,0,0,1) FadeIn0to100 backwards` [S23], [S14], [S25]. MUI `enteringScreen` 225 / `leavingScreen` 195 [S9]. Carbon отводит на затемнение фона до 700 ms (`duration-slow-02`, «background dimming, large hero transitions») — это верхняя граница для крупных героических переходов, не для рабочей модалки [S4].

Кривая Atlassian для масштабирования модалок: `ease-in-out bold` `cubic-bezier(0.4, 0, 0, 1)` — «Gentle start and soft settle. Best for scaling Modals or repositioning elements» [S23].

Доступность: фокус переезжает в модалку **в начале** анимации, не после. «Move focus and trigger screen-reader announcements at the start of the animation» [S25].

**Пресет А (админка):** подложка fade 150 ms, окно fade 150 ms без масштаба. **Пресет Б:** как в таблице.

### 3.3 Вкладки

| Что | Свойства | Длительность | Кривая |
|---|---|---|---|
| Индикатор (полоса под активной вкладкой) | `transform: translateX` + `width` через `scaleX`, либо `clip-path` | 150–200 ms | ease-in-out |
| Цвет текста активной вкладки | `color` | 150 ms | ease |
| Смена панели контента | `opacity` | 100 ms, либо без анимации | linear |

**Ловушка, которую разбирает Kowalski:** если анимировать подсветку и цвет текста двумя независимыми переходами, они рассинхронизируются, и в середине пути текст уже белый, а полоса ещё не доехала. Правильное решение — `clip-path`: два слоя текста (обычный и активный) накладываются, а `clip-path: inset(...)` прорезает окно, которое едет вместе с полосой [S15], [S58].

`clip-path` аппаратно ускоряется, не влияет на раскладку и не вызывает layout shift [S58].

**Пресет А:** вкладки в админке переключаются горячими клавишами и мышью десятки раз за сессию. Индикатор либо не анимируется вовсе, либо 100 ms. Это прямое применение правила частоты (§7.1).

### 3.4 Таблица

| Что | Значение | Комментарий |
|---|---|---|
| hover строки | 70 ms, `background-color` | Carbon DataTable: 70 ms на 49 из 52 объявлений [S56] |
| Раскрытие строки (expandable row) | 200–250 ms, `grid-template-rows` 0fr → 1fr + `opacity` | у Carbon та же кривая, что у дропдауна, но другая длительность из-за размера [S52] |
| Шеврон раскрытия | 150–200 ms, `transform: rotate(90deg)` | синхронно с раскрытием |
| Сортировка и перестановка строк | **не анимировать** в плотных таблицах; при необходимости — FLIP, 200–300 ms, standard-easing | Carbon относит сортировку строк к standard-easing [S22] |
| Обновление значений в ячейках | **не анимировать** | §3.9 |
| Выделение строки (selected) | 100 ms, `background-color` | |
| Появление строк при загрузке | стаггер 20 ms, суммарно ≤ 500 ms | §6.1 [S52] |

Подтверждение практикой: `carbon-datatable` — самый дисциплинированный продукт выборки, 94 % его переходов это одно значение 70 ms [S56].

### 3.5 Карточка

| Что | Значение |
|---|---|
| hover: тень | 150 ms, ease |
| hover: подъём | `transform: translateY(-1…-2px)`, 150 ms |
| hover: `scale` | **не использовать** |

Подъём и тень описаны в `../04-shape-elevation/02-shadows-layers-depth.md`; здесь только длительность. `scale(1.02…1.05)` на карточке ломает выравнивание соседей в сетке, вызывает перерисовку текста и не встречается ни в одной из изученных систем — это маркер сгенерированного интерфейса (§8).

### 3.6 Выпадающее меню, поповер, тултип, комбобокс

| Компонент | Вход | Выход | Свойства |
|---|---|---|---|
| Dropdown / Menu | 150 ms, ease-out | 100 ms, ease-in | `opacity` + `scale(0.95→1)`, origin от триггера |
| Popover | 150 ms | 100 ms | то же, четыре направления |
| Tooltip | 100–150 ms, fade | 100 ms, fade | только `opacity`; задержка показа — UX-вопрос, см. ux-research |
| Combobox / Select список | 120–150 ms | 100 ms | `opacity` + `translateY(4px)` |

Atlassian: «Popup enter 150 ms, Popup exit 100 ms», кривая входа `ease-out practical` `cubic-bezier(0.4, 1, 0.6, 1)` — «Subtle, everyday entrance curve. Best for elements like Popup or hover background fades» [S23], [S25].

**Следующая подсказка — без задержки.** Пока одна подсказка открыта и курсор переходит к соседнему элементу, следующая показывается сразу, без задержки показа (Kowalski) [S64] `[мнение]`; задержка остаётся только у первой подсказки.

**Задержка на выходе против дрожания.** Comeau: `transition-delay: 300ms` на выходе меню (при входе 0). Если курсор вернулся в пределах 300 ms, перехода не будет вовсе; после 300 ms меню гаснет за 400 ms [S54]. Полезно для меню, раскрывающихся по наведению; для меню по клику не нужно.

### 3.7 Индикаторы загрузки

| Что | Длительность цикла | Кривая | Источник |
|---|---|---|---|
| Спиннер | **0.75–1 s**, бесконечно | `linear` | Tailwind `--animate-spin: spin 1s linear infinite` [S5] |
| Шиммер / пульсация скелетона | **1.5–2 s** | `cubic-bezier(0.4, 0, 0.6, 1)` | Tailwind `--animate-pulse: pulse 2s … infinite`, keyframes `50% { opacity: 0.5 }` [S5] |
| Ping (расходящееся кольцо) | 1 s | `cubic-bezier(0, 0, 0.2, 1)` | Tailwind [S5] |
| Линейный прогресс (неопределённый) | 1.5–2 s | `linear` | |
| Линейный прогресс (определённый) | 150–300 ms на шаг | `ease-out` или `linear` | |

Правила:
- **Спиннер только `linear`.** Polaris прямо: «Moves with constant speed. Use for continuous and mechanical animations, such as rotating spinners» [S2]; Primer: «Use for continuous animations like progress bars or loaders» [S7]; Fluent 2: `linear` — только для вращения [S62].
- **Быстрее вращающийся спиннер воспринимается как «работает изо всех сил»** при том же реальном времени загрузки. Наблюдение Kowalski на паре демонстраций [S14]. `[мнение]`
- **Период цикла не должен быть около 5 секунд.** Apple: «avoid showing an oscillation that has a frequency of around **0.2 Hz** because people can be very sensitive to this frequency» [S12]. 0.2 Hz = период 5 с. Поэтому шиммер на 1.5–2 с безопасен, а «дыхание» на 4–6 с — нет.
- **Шиммер скелетона — это анимация, запущенная страницей**, значит под WCAG 2.2.2. Подробнее в `03-reduced-motion-and-motion-tokens.md` §2.2: полноэкранный лоадер законен, бесконечный шиммер рядом с уже загруженным контентом — нет.

Пульсация Polaris как токен-keyframe: `from, 75% { transform: scale(0.85); opacity: 1 } to { transform: scale(2.5); opacity: 0 }` — расходящееся кольцо для точки-индикатора [S2].

### 3.8 Тост, флажок, системное уведомление

| Что | Вход | Выход |
|---|---|---|
| Тост | 250 ms, ease-out-bold, `translateY` + `opacity` | 200 ms, ease-in-practical |
| Перестановка стопки тостов | 200 ms, ease-in-out | — |

Atlassian: `motion.flag.enter` 250 ms ease-out-bold, `motion.flag.exit` 200 ms ease-in-practical, плюс отдельный токен `motion.flag.reposition` для сдвига оставшихся флажков [S25]. Кривая входа `ease-out bold` `cubic-bezier(0, 0.4, 0, 1)` — «Elements arrive quickly and decelerate to a stop. Best for elements like Panel or Flag entering the screen» [S23].

Деталь от автора библиотеки Sonner: тосты сделаны «a bit slower than usual and use `ease` as the easing type rather than `ease-out` to make it feel more elegant» [S14]. Логика: пользователь тост не запрашивал, резкий влёт читается как тревога.

### 3.9 Числа, графики, данные

**Не анимировать:**
- count-up (перебор цифр от 0 до значения) в дашбордах и таблицах;
- перерисовку графика при смене фильтра;
- пересчёт итогов в форме.

Kowalski про пружину на значении, привязанном к курсору: «If this was a **functional graph, in a banking app** for example, **no animation would be better**» [S15]. Rauno Freiberg о том же со стороны частоты: индикатор, который перерисовывается при каждом действии, через два дня начинает раздражать [S16].

**Исключение** — первое появление графика на пустом дашборде: Carbon ставит визуализации данных **последними** в порядке появления (пятая, последняя категория), то есть их анимация допустима один раз при загрузке страницы [S52].

### 3.10 Подсветка изменившегося («flash»)

Приём: элемент, значение которого изменилось извне (пришло по сокету, обновил другой пользователь), коротко подсвечивается и гаснет.

| Параметр | Значение |
|---|---|
| Свойство | `background-color` |
| Появление подсветки | 0 ms (мгновенно) |
| Затухание | **1000–2000 ms**, `ease-out` |
| Цвет | `accent.bg` или `warning.bg` с низкой насыщенностью, см. `../01-color/02-semantic-roles-and-architecture.md` |

Это единственный случай, когда длительность больше 400 ms оправдана в рабочем интерфейсе: анимация не задерживает действие, а сообщает о событии, которого пользователь не совершал. Реализуется через `@keyframes` (цикл однократный), не через `transition`. `[мнение]`

Ограничение: если подсветок больше трёх одновременно, экран превращается в ёлку. Порог — не более 3 одновременных подсветок, дальше показывать сводку «обновлено N строк».

### 3.11 Аккордеон, раскрытие блока, «показать ещё»

| Что | Значение |
|---|---|
| Длительность | 200–250 ms (мелкий блок), до 300 ms (крупный) |
| Кривая | standard / ease-in-out |
| Свойство | `grid-template-rows: 0fr → 1fr` (см. §4.2), плюс `opacity` на содержимом |
| Шеврон | `transform: rotate(180deg)`, та же длительность |

Формула длительности от высоты (MUI `getAutoHeightDuration`, `01-durations-easings-springs.md` §5.1): 36 px → 192 ms, 100 px → 239, 300 px → 311. Для генеративной системы проще две ступени: блок ниже 200 px — 200 ms, выше — 300 ms.

### 3.12 Боковая панель, дровер, инспектор

| Что | Вход | Выход |
|---|---|---|
| Дровер (выезжает сбоку) | 250–300 ms, ease-out, `translateX(100% → 0)` | 200–250 ms |
| Сворачивание сайдбара | 200–250 ms, ease-in-out, `width` через `transform` или `grid-template-columns` | то же |
| Инспектор (правая панель) | 200 ms, ease-out | 150 ms |

Кривая выдвижной панели у Kowalski — кривая дровера iOS `cubic-bezier(0.32, 0.72, 0, 1)` [S64] `[мнение]`: резкий старт и долгое
торможение, вход пресета Б; в пресете А — обычный ease-out.

**Важное исключение Carbon:** если панель уходит за край, но остаётся «рядом» и готова вернуться, берётся **standard, а не exit**: «The panel leaves the view, but **slows down as it exits**, implying that it would come to rest just outside the view» [S22]. То есть дровер с кнопкой «вернуть» уходит с торможением, а модалка после «Отмена» — с ускорением.

Сворачивание сайдбара трогает раскладку всего контента, поэтому дешевле всего анимировать `grid-template-columns` на контейнере (одно свойство, один слой), а не `width` панели плюс `margin-left` контента.

### 3.13 Переключатель, чекбокс, радио

| Что | Значение |
|---|---|
| Switch: бегунок | 150–200 ms, `transform: translateX`, ease-out (или пружина в пресете Б) |
| Switch: фон дорожки | 150 ms, `background-color` |
| Checkbox: галочка | 150 ms, `stroke-dashoffset` или `opacity` + `scale` |
| Checkbox: фон | 100 ms |

Переключатель — один из двух-трёх компонентов, где пружина в клиентском сервисе оправдана: движение короткое, элемент маленький, перелёт 3–5 % читается как щелчок. Для админки — обычный ease-out 150 ms.

### 3.14 Аватар

Atlassian даёт два интеракционных токена и константу [S25], [S50]:
- `motion.avatar.hovered`, `motion.avatar.pressed`;
- `motion.avatar.enter` = `150ms cubic-bezier(0.4,1,0.6,1) ScaleIn80to100 backwards, 150ms … FadeIn0to100 backwards` — то есть вход аватара масштабируется от **80 %**, а не от 95 % (аватар круглый и мелкий, более сильный масштаб на нём читается нормально);
- `ACTIVE_SCALE_FACTOR = 0.9` — нажатый аватар ужимается до 90 %.

### 3.15 Переход между страницами

| Вариант | Когда |
|---|---|
| **Без анимации** | плотная админка, переходы по левому меню, всё, что делается с клавиатуры |
| Fade 150 ms на области контента | клиентский сервис, переход между разделами |
| View Transitions, 200–300 ms | клиентский сервис, где есть общий элемент (карточка → страница объекта); только как прогрессивное улучшение, §5.3 |

Atlassian `motion.duration.xlong` 400 ms помечен как «page-level transitions», `xxlong` 600 — «onboarding steps, full-screen overlays» [S25]. Это верхняя граница, а не рекомендация: в веб-сервисе переход страницы обычно ждёт данных, и анимация складывается с сетевой задержкой. Fluent 2 меняет страницу быстрым затуханием, а не сдвигом [S62]; Polaris не анимирует всю страницу разом [S63].

---

## 4. Производительность

### 4.1 Три шага рендера и цена свойств

| Слой | Свойства | Цена |
|---|---|---|
| **Composite** (дёшево) | `transform`, `opacity`, `filter` (частично), `clip-path` | GPU, не трогает раскладку |
| **Paint** (дороже) | `background-color`, `color`, `box-shadow`, `border-color`, `border-radius` | перерисовка слоя |
| **Layout** (дорого) | `width`, `height`, `top`, `left`, `margin`, `padding`, `font-size` | пересчёт раскладки каждый кадр |

Kowalski: `transform` и `opacity` «задевают только третий шаг рендера, тогда как padding/margin задевают все три» [S14]. Atlassian формулирует как запрет: «**Don't animate layout-triggering properties.** Avoid animating width, height, or top. They trigger layout work on every frame and cause stuttering on older hardware» [S25].

Бюджет: «animations ought to run at 60 fps… the browser only has **16.6 milliseconds** to paint each frame. For reference, it takes us about 100–300 ms to blink» [S54]. Apple, про игры, но применимо: «maintaining a consistent frame rate of **30 to 60 fps** typically results in a smooth, visually appealing experience» [S12].

Практическое следствие: **цвет фона анимировать можно** (paint на маленькой площади дёшев), и все системы это делают (hover кнопок). Нельзя анимировать `box-shadow` на десятке карточек одновременно — это paint на большой площади с размытием.

### 4.2 Как анимировать высоту, не анимируя `height`

Четыре способа, по убыванию надёжности:

1. **`grid-template-rows: 0fr → 1fr`** на контейнере-гриде с `overflow: hidden` у ребёнка. Работает с содержимым любой высоты, анимируется браузером как число. Поддержка полная с 2023 года.
   ```css
   .accordion { display: grid; grid-template-rows: 0fr; transition: grid-template-rows 200ms ease-in-out; }
   .accordion[data-open] { grid-template-rows: 1fr; }
   .accordion > * { overflow: hidden; }
   ```
2. **`clip-path: inset(0 0 100% 0) → inset(0)`.** Аппаратно ускоряется, не вызывает layout shift, но содержимое занимает место сразу (годится для раскрытия изображения, не годится для аккордеона в потоке) [S58].
3. **`transform: scaleY`** с компенсацией масштаба у содержимого. Дёшево, но искажает текст в процессе.
4. **Измерить высоту в JS и анимировать `height` от числа к числу.** Так делает MUI `Collapse`; там же живёт формула длительности от высоты [S9]. Работает всегда, но это layout-анимация.

Пятый, новый способ — `interpolate-size: allow-keywords` плюс `transition: height` к `auto`. На сентябрь 2026 поддержка ограничена Chromium; годится только как прогрессивное улучшение поверх варианта 1.

### 4.3 `filter` и `backdrop-filter`

Количественных замеров FPS найти не удалось (открытый вопрос агента C остаётся частично открытым, см. §9). Что установлено:

- `backdrop-filter` заставляет браузер брать снимок того, что под элементом, и фильтровать его **каждый кадр**, пока элемент или фон движется. Это самая дорогая из «визуальных» операций.
- **Анимировать сам `backdrop-filter` (менять радиус размытия) не следует.** Приём, который работает: применить фильтр статически и анимировать `opacity` слоя.
- `filter: blur()` на большой площади дорог по той же причине; на маленькой иконке дёшев.
- Ограничение волны 1 остаётся в силе: не больше **двух** элементов с `backdrop-filter` на экран (`../04-shape-elevation/02-shadows-layers-depth.md`).

Косвенное подтверждение: ни в одной из 15 изученных систем нет токена, который анимировал бы `filter` или `backdrop-filter`. Atlassian прямо перечисляет четыре допустимых свойства движения: scale, fade, slide, color [S23].

### 4.4 `will-change`

Что даёт [S54]:
- убирает «щелчок» при передаче элемента между CPU и GPU: «GPUs and CPUs render things slightly differently. When the CPU hands it to the GPU, and vice versa, you get a snap of things shifting slightly»;
- включает **субпиксельный рендер**: «Properties like `margin-top` can't sub-pixel-render, which means they need to round to the nearest pixel, creating a stepped, janky effect. `transform`, meanwhile, can smoothly shift between pixels».

Что стоит:
- каждый элемент с `will-change` получает собственный слой композитора и занимает память GPU;
- `will-change` на всех строках таблицы или всех карточках сетки — типичная причина падения производительности на слабых машинах.

Правило: ставить `will-change` на **единицы** элементов, которые действительно вот-вот поедут (открывающийся дровер, перетаскиваемый элемент), и снимать после. В CSS-правиле `:hover` ставить `will-change` не на сам `:hover`, а на базовое состояние элемента, иначе слой создаётся уже во время анимации и щелчок остаётся.

### 4.5 CSS против JavaScript

| | CSS `transition` / `@keyframes` | WAAPI | JS-библиотеки (Framer Motion, React Spring) |
|---|---|---|---|
| Аппаратное ускорение | да | да | **нет** (обычно `requestAnimationFrame`) |
| Работа при занятом главном потоке | продолжается | продолжается | **кадры теряются** |
| Прерываемость | `transition` да, `@keyframes` нет | да | да, с сохранением скорости |
| Пружины | только через `linear()` | через `linear()` | нативно |

Реальный кейс Kowalski: «в дашборде Vercel анимация активной вкладки через Shared Layout Animations роняла кадры во время загрузки страницы; починили переходом на CSS» [S14]. Comeau формулирует иначе, но о том же: «JavaScript animations aren't inherently bad — they're just as performant as CSS transitions. The trouble is the JavaScript is a busy beaver; if the main thread is busy with some other operation, your animation might stutter» [S33].

Правило для веб-сервиса: **всё, что происходит во время загрузки данных, делай на CSS.** JS-анимации оставь для жестов и перетаскивания, где нужна реакция на скорость ввода.

---

## 5. Современные механизмы CSS и их статус на 2026

### 5.1 `@starting-style`, `transition-behavior: allow-discrete`, `overlay`

**Baseline 2024, Newly available с августа 2024** [S20].

Проблема: переходы по умолчанию не запускаются при первом рендере элемента и при смене `display: none` → видимое. Для поповеров и `<dialog>` в top layer нужны **три** вещи:
1. `@starting-style` с начальными `opacity`/`transform`;
2. `display` в списке переходов с `transition-behavior: allow-discrete` (иначе выхода не видно — элемент просто исчезает);
3. `overlay` в списке переходов с `allow-discrete` — чтобы удаление из top layer отложилось до конца анимации.

```css
dialog {
  opacity: 0;
  transform: scale(0.95);
  transition: opacity 200ms, transform 200ms,
              overlay 200ms allow-discrete, display 200ms allow-discrete;
}
dialog[open] { opacity: 1; transform: scale(1); }
@starting-style { dialog[open] { opacity: 0; transform: scale(0.95); } }
```

Замечание MDN: «`@starting-style` is only relevant to CSS transitions» — для `@keyframes` он не нужен [S20].

### 5.2 `linear()`

**Baseline Newly available с декабря 2023, Widely available с июня 2026.** Подробно в `01-durations-easings-springs.md` §4.7; пружину ДС в `linear()` собирает сборка из токена — `04-spring-tokens-transitions-platforms.md` §1.

### 5.3 View Transitions API

Статус: переходы в документе — `document.startViewTransition()`, `view-transition-name`, `view-transition-class` — **Baseline Newly available с октября 2025**: Chrome 111, Safari 18, Firefox 144; типы переходов в первой версии Firefox не вошли `[документация: web.dev, октябрь 2025; Chrome for Developers, «What's new in view transitions (2025 update)»]`. У кросс-документных переходов (`@view-transition { navigation: auto }`) Baseline на снимке MDN нет [S57]; это сторона страниц сайта (`../../creative/05-motion/01-motion-principles-and-access.md` §7.1). Смена маршрута в SPA и общий элемент по шаблонам интерфейса — `04-spring-tokens-transitions-platforms.md` §3.

Правила применения в веб-сервисе:
- **Прогрессивное улучшение, не основа.** Интерфейс должен работать одинаково без переходов.
- Длительность **200–300 ms**, не больше: переход страницы складывается с ожиданием данных.
- Оправдан там, где есть **общий элемент**: карточка списка раскрывается в страницу объекта, миниатюра — в полный размер.
- В плотной админке не нужен вовсе: переходы по левому меню происходят десятки раз за сессию (правило частоты, §7.1).
- Обязательно отключается при `prefers-reduced-motion` (`03-reduced-motion-and-motion-tokens.md` §3).

### 5.4 Scroll-driven animations

`animation-timeline: scroll()` и `view()`. В веб-сервисах уместность близка к нулю:
- **Полоса прогресса чтения** длинного документа (единственное честное применение);
- **Появление блоков при прокрутке** — паттерн лендинга, в приложении за авторизацией выглядит чужеродно и дополнительно нарушает WCAG 2.2.2 и 2.3.3: анимация, запущенная появлением элемента в области видимости, считается запущенной автоматически (§`03-reduced-motion-and-motion-tokens.md` §2.2) [S53].
- **Параллакс** — прямой вестибулярный триггер (Val Head: «рассогласование направления и скорости») [S17].

### 5.5 `corner-shape`, морфинг формы

Морфинг формы M3 Expressive (35 фигур) разобран в `../04-shape-elevation/01-radius-and-borders.md` §8. Здесь только физика: морфинг относится к **spatial**-пружинам, то есть в веб-переводе это 350–650 ms с кривой, имеющей перелёт (`01-durations-easings-springs.md` §4.5). В рабочем интерфейсе не применяется.

---

## 6. Хореография: несколько элементов сразу

### 6.1 Стаггер

Carbon даёт единственное найденное точное число: «staggering the entrance of table content by **20 ms** significantly reduces the cognitive load. Depending on the number of staggered elements, the delay should be adjusted to ensure that **total time is still within 500 ms**» [S52].

Расчёт: при шаге 20 ms и потолке 500 ms максимум ≈ 25 элементов. Дальше шаг уменьшается: 40 строк → 12 ms, 60 строк → 8 ms. На практике проще ограничить стаггер первыми 10–15 элементами, остальные показывать сразу. Fluent 2 очень крупные группы не стаггерит вовсе [S62].

| Число элементов | Шаг | Суммарно |
|---|---|---|
| до 10 | 30 ms | 300 ms |
| 10–25 | 20 ms | 200–500 ms |
| больше 25 | стаггер только для первых 15, остальные без задержки | 300 ms |

### 6.2 Порядок появления контента

Таблица Carbon, применимая к любому дашборду [S52]:

| № | Категория | Примеры |
|---|---|---|
| 1 | Статика оболочки | UI shell, верхняя и боковая навигация |
| 2 | Статика тела | заголовки, текст, изображения |
| 3 | Динамический контент | содержимое таблицы, результаты запроса |
| 4 | Первичное действие | primary button |
| 5 | Анимированный контент | визуализации данных |

Логика: «Start with the most stable content… and **end with the most important information**, such as the primary button or a calculation result, to focus the user's attention on them.»

### 6.3 Пути движения

Carbon: «Elements in Carbon dance on the grid. Motion paths trace lines along the grid which **never run diagonally**. When expanding or moving elements across the screen, **stagger the timing of horizontal and vertical animations** to create a path with a rounded corner» [S52].

Антипримеры оттуда же: диагональный путь «breaks the grid and is harsh to the eye»; при сортировке «criss cross sorting appears disorganized».

Практически: если элемент едет и вправо, и вниз, запусти горизонтальное смещение на 50–80 ms раньше вертикального (или наоборот) — получится дуга вместо диагонали.

### 6.4 Консистентность и намеренная несогласованность

- **Семантическая консистентность:** одинаковый смысл — одинаковое движение. Раскрытие строки таблицы и открытие дропдауна используют один шеврон и один смысл, значит одинаковые личность и кривая, но разные длительности из-за разницы в размере [S52].
- **Пространственная консистентность:** панель на слое выше — «sliding» плюс обязательное затемнение содержимого под ней; панель на том же слое — «pushing» с раскрытием через маску [S52].
- **Намеренная несогласованность:** «forward motion in the direction of entrance signals **affirmation**, while **reversing** entrance motion signals **cancellation**» — подтверждение и отмена модалки уходят по-разному [S52]. Это редкий случай, когда разное движение несёт разный смысл, а не является небрежностью.

---

## 7. Что не анимировать

### 7.1 Правило частоты

| Источник | Формулировка |
|---|---|
| Apple HIG | «In apps, generally avoid adding motion to UI interactions that **occur frequently**» [S12] |
| Kowalski | «**Never animate keyboard initiated actions.** These actions are repeated sometimes hundreds of times a day» [S14] |
| Rauno Freiberg | «if we for a moment consider the interaction frequency being **hundreds of times a day**, it does start to feel more like cognitive burden after seeing the same animation for the hundredth time» [S16] |
| Carbon | «**Is your motion frequently noticed by average users?** If so, consider removing or minimizing it» [S22] |
| Atlassian | что повторяют десятки раз в день — короче 150 ms [S60] |

Разбор macOS у Rauno Freiberg как образец: контекстное меню **появляется без анимации**, но **исчезает с fade**; App Switcher не анимируется вообще, а при малой дельте между Command и Tab окно переключается без показа меню [S16].

Список того, что в плотной админке не анимируется вовсе:
- открытие командного меню (Cmd+K);
- переключение вкладок и разделов с клавиатуры;
- переход по строкам списка стрелками;
- появление и исчезновение кольца фокуса;
- обновление данных в таблице;
- переключение страниц пагинации;
- раскрытие автодополнения при вводе.

### 7.2 Вопрос перед добавлением

Atlassian: «Before adding motion ask, **if I remove this, does the user lose information or context?**» И: «Don't make users wait without reason. Avoid motion that **blocks the next step in a flow**» [S23].

Apple: «Make motion optional… avoid using it as the **only** way to communicate important information» [S12].

### 7.3 Анти-каталог

| Чего не делать | Почему |
|---|---|
| Параллакс в интерфейсе приложения | вестибулярный триггер, рассогласование скоростей [S17] |
| Анимация появления каждого блока при прокрутке | паттерн лендинга; нарушает 2.2.2 и 2.3.3 [S53] |
| `scale` карточки на hover | ломает сетку, перерисовывает текст |
| Count-up чисел в дашборде | мешает читать значение [S15] |
| Анимация загрузочного скелетона дольше, чем идёт загрузка | пользователь видит движение после того, как данные пришли |
| Автопроигрывание видео или GIF в интерфейсе | 2.2.2, нужен контрол паузы [S53] |
| Мигание чаще 3 раз в секунду | это уже вспышка, WCAG 2.3.1 [S53] |
| Анимация, блокирующая ввод | Apple: «don't make people wait for an animation to complete» [S12] |
| Разные длительности у элементов одного ряда | читается как рассинхрон |
| Анимация на `:hover` у элементов, недоступных для мыши на тач-устройстве | залипшее состояние hover |

---

## 8. Частые ошибки

Общие ошибки движения перечислены в `01-durations-easings-springs.md` §9. Здесь — специфичные для каталога.

1. **`transition: all`** — самая частая. Анимируются `height` и `width`, которых не планировали.
2. **Поповер растёт из центра**, а не из триггера (§2.3).
3. **Масштаб появления 0.8, 0.5 или `scale(0)`** вместо 0.9–0.97 — элемент «выпрыгивает».
4. **Смещение появления 20–40 px** для поповера вместо 4–8.
5. **Анимация `height` аккордеона через JS-измерение** там, где хватает `grid-template-rows` (§4.2).
6. **Спиннер с `ease-in-out`** — видно рывки на каждом обороте, нужен `linear`.
7. **Шиммер скелетона с периодом 4–6 с** — попадает в опасную зону 0.2 Hz (§3.7).
8. **Затемнение фона и модалка с одной длительностью и одной кривой** — подложка должна успевать раньше.
9. **`will-change` на всех строках таблицы** (§4.4).
10. **Анимация `box-shadow` вместо `opacity` у псевдоэлемента с тенью** — paint на большой площади каждый кадр.

### 8.1 Ошибки, характерные для нейросетей

11. **Каждый экран открывается `fadeIn` с `translateY(20px)`.** Это шаблон из обучающих данных лендингов. В приложении за авторизацией переходы либо мгновенные, либо 150 ms fade.
12. **`animate-bounce` / `animate-pulse` / `animate-ping` из Tailwind на боевых элементах** — демонстрационные утилиты, воспринимаются как незаконченная вёрстка.
13. **Hover-эффект `scale(1.05)` + `shadow-2xl` на каждой карточке.** Связка встречается в сгенерированном коде почти всегда и не встречается ни в одной дизайн-системе.
14. **Скелетон, который анимируется, но никогда не заменяется данными** (статическая демонстрация выдаёт себя).
15. **Счётчики с count-up на дашборде** (§3.9).
16. **`transition-duration` вразнобой:** `0.3s` на кнопке, `0.2s` на карточке, `0.5s` на модалке — без системы.
17. **Анимация графика при каждом ререндере** из-за того, что библиотеке не передан ключ стабильности.
18. **Параллакс-фон или «дышащий» градиент в админ-панели.**
19. **Плавная прокрутка (`scroll-behavior: smooth`) на всём документе**, из-за чего переход по якорю в длинной таблице занимает секунды.
20. **Отсутствие блока `@media (prefers-reduced-motion: reduce)`** при наличии двадцати анимаций.

---

## 9. Чек-лист

1. Все анимации используют только `transform`, `opacity`, `color`/`background-color` и (точечно) `clip-path`?
2. Нет ли в коде `transition: all`?
3. Число свойств в одном переходе — одно или два?
4. Поповеры, меню и тултипы растут из триггера (`transform-origin` привязан)?
5. Масштаб появления в диапазоне 0.9–0.97 (никогда не от `scale(0)`), смещение 4–8 px?
6. Смещения взяты из шкалы отступов, а не произвольные?
7. Раскрытие блоков сделано без анимации `height` (grid-rows, clip-path или измеренная высота)?
8. Спиннер `linear` с циклом 0.75–1 s?
9. Период шиммера скелетона вне диапазона 4–6 с?
10. Затемнение фона модалки — отдельный переход со своей длительностью?
11. Обновление данных в таблице и на графиках не анимируется?
12. Действия, запускаемые с клавиатуры, не анимируются?
13. Стаггер не превышает 20–30 ms на элемент и 500 ms суммарно?
14. Путь движения не идёт по диагонали?
15. `will-change` стоит не более чем на единицах элементов и снимается после?
16. Нет анимации `backdrop-filter` и `filter` на больших площадях?
17. Для `<dialog>` и popover прописаны `@starting-style`, `allow-discrete` для `display` и `overlay`?
18. View Transitions и scroll-driven animations подключены как прогрессивное улучшение и отключаются при reduced motion?
19. Для каждой анимации можно ответить на вопрос «если её убрать, пользователь потеряет информацию или контекст?»
20. Ни одна анимация не блокирует следующий шаг сценария?

---

## 10. Открытые вопросы

1. **Количественная стоимость `backdrop-filter` в анимации** не найдена (§4.3). Открытый вопрос агента C закрыт только качественно. Кандидаты для следующей волны: Chrome DevTools Performance на синтетическом стенде, `web.dev/articles/animations-guide` (из этой среды недоступен), доклады Chrome Dev Summit о композитинге.
2. **`interpolate-size: allow-keywords`** (§4.2) — статус поддержки не проверен по первичному источнику, описан как «ограниченный» по косвенным признакам. `[спорно]`
3. **Число «не более трёх одновременных подсветок»** (§3.10) выведено из практики, источника нет. `[мнение]`
4. **Нет исследований**, сравнивающих восприятие интерфейса со стаггером и без него, кроме утверждения Carbon о снижении когнитивной нагрузки без ссылки на данные. `[система]`

---

## Источники

Снимок: 28.10.2026 — день сверки источников S59–S64 и статуса View Transitions.

Нумерация сквозная с `../99-raw/notes/wave2/M-notes.md` и `01-durations-easings-springs.md`, где даны полные аннотации.

- `[S2]` Shopify Polaris, `motion.ts` (keyframes как токены, смещение через токен отступа).
- `[S4]` IBM `@carbon/motion` (длительности с назначением в JSDoc).
- `[S5]` Tailwind CSS v4 `theme.css` (spin, ping, pulse, bounce с точными значениями).
- `[S9]` MUI `createTransitions.js` (формула длительности от высоты).
- `[S12]` Apple HIG: Motion (частота, brevity, fades вместо перемещения, 0.2 Hz).
- `[S13]` Mantine `transitions.ts` (числа смещений: pop 10 px, fade 30 px).
- `[S14]` Emil Kowalski, «Great Animations».
- `[S15]` Emil Kowalski, «Good vs Great Animations» (origin-aware, clip-path для вкладок).
- `[S16]` Rauno Freiberg, «Invisible Details of Interaction Design» (частота, разбор macOS).
- `[S17]` Val Head, «Designing Safer Web Animation For Motion Sensitivity» (три фактора риска).
- `[S20]` MDN, `@starting-style` (три условия для top layer).
- `[S22]` IBM Carbon, Motion: overview (роли кривых, исключение для панели, чек-лист).
- `[S23]` Atlassian Design System, Motion (четыре свойства движения, диапазоны, кривые).
- `[S25]` Atlassian, Applying motion (семантические токены, keyframes 95 ↔ 100 %, запрет layout-свойств).
- `[S33]` Josh W. Comeau, «A Friendly Introduction to Spring Physics».
- `[S52]` IBM Carbon, Motion: choreography (стаггер 20 ms, порядок появления, пути по сетке).
- `[S53]` W3C WCAG 2.2, Understanding SC 2.2.2 Pause, Stop, Hide (через web.archive).
- `[S54]` Josh W. Comeau, «An Interactive Guide to CSS Transitions» (16.6 ms, will-change, action-driven motion, transition-delay).
- `[S50]` Atlassian, `@atlaskit/avatar@28.0.3` — `motion.avatar.*` и `ACTIVE_SCALE_FACTOR = 0.9`; полная аннотация в `../07-iconography-imagery/02-illustration-system-avatars-images.md`.
- `[S56]` Собственный пересчёт измерений агента P (24 продукта).
- `[S57]` MDN, View Transition API (статус на июнь 2026).
- `[S58]` Emil Kowalski, «The Magic of clip-path».
- `[S59]` Google, Material 3: material-components-android, файл docs/theming/Motion.md, androidx Compose Material3 `MotionScheme.kt` (VERSION v0_14_0) — скорость пружины по размеру компонента; через `../../creative/02-references-moodboards/04-motion-libraries-and-rules.md` §4.1 [S37].
- `[S60]` Atlassian Design System, https://atlassian.design/foundations/motion и /foundations/motion/applying-motion; `@atlaskit/tokens` 20.8.2, файл artifacts/themes/atlassian-motion.js — «что повторяют десятки раз в день — короче 150 ms»; через тот же обзор §4.1 [S41].
- `[S62]` Microsoft Fluent 2, https://fluent2.microsoft.design/motion; `@fluentui/react-motion` 9.16.5, файл dist/index.d.ts — правила применения: крупному дольше, `linear` только у вращения, смена страницы затуханием, крупные группы без стаггера; через тот же обзор §4.1 [S40].
- `[S63]` Shopify Polaris, `polaris.shopify.com/content/design/motion/*.mdx` и polaris-tokens/src/themes/base/motion.ts в архиве репозитория Shopify/polaris (архив с сентября 2026; Polaris React заменён Web Components, токенов движения там не найдено); через тот же обзор §4.1 [S42].
- `[S64]` Emil Kowalski, https://emilkowal.ski/ui/7-practical-animation-tips и /ui/great-animations; emilkowalski/skills (emil-design-eng/SKILL.md, review-animations/STANDARDS.md) — не начинать с `scale(0)`, кривая дровера iOS, следующая подсказка без задержки; через тот же обзор §4.2 [S43].
