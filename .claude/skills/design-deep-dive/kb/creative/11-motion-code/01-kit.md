# 01 · Контракт набора: файлы, `MotionKit.mount`, словарь `data-mk`, переменные токенов, состояния движения, запреты

Набор — два файла: `examples/motion-kit.js` (классический скрипт, одно глобальное имя `MotionKit`) и
`examples/motion-kit.css` (облик движения: начальные и конечные состояния, переходы, шкалы прокрутки, петли). Разметка
страницы называет примитив атрибутом `data-mk`, опции — атрибутами `data-mk-*` и CSS-переменными `--mk-*`; числа берутся
из токенов `motion.marketing`. Набор не создаёт, не переносит и не переписывает узлы DOM: он ставит атрибуты, классы и
CSS-переменные на элементы, которые уже есть. Отсюда три свойства: тот же код идёт на холст Claude Design и в код
сайта; без JS страница полна; проверка находит каждый момент по атрибутам. Примитивы по одному — `02`, DOM-сцены — `03`,
где набор живёт — `04`, машинный список — `primitives.yaml`.

## Выжимка для агента

1. **Момент спецификации движения собирается примитивом набора** (`moment.primitive` = значение `data-mk`, опции —
   `moment.params`): таблица §6 переводит поля `motion-spec` в разметку без отсебятины; что набор не выражает — там же.
   `spec_check.py` сверяет примитив, класс, уровень, эффекты и опции (MS-25). `[проверено: spec_check — 0 находок]` → §6
2. **`MotionKit.mount(root, opts)` → `{destroy, pause, resume, refresh, info, transition}`**: один вызов на документ или
   корень артборда; `destroy` снимает всё, что набор поставил, и страница возвращается к виду без JS. `[проверено]` → §2
3. **Скрытое начальное состояние — только под `data-mk-on="full"` корня**, который ставит скрипт: без JS, при «уменьшить
   движение», выборе «Меньше» и в обзоре холста видны конечные состояния. `[проверено: motion_smoke nojs, rm, reduced]` → §5
4. **Числа — переменные с каноническими именами токенов** (`--motion-marketing-<путь через дефисы>`, как `_var` в
   `ds_build.py`) и запасными значениями из `marketing-tokens.json`: дизайн-система проекта подменяет их без правки
   набора; ветка reduce — значения `$extensions.…reduce` токенов. `[проверено: 29 имён сверены]` → §4
5. **У каждой дорожки — своё время**: `--mk-o-*` прозрачность, `--mk-t-*` transform, `--mk-c-*` clip-path, `--mk-f-*`
   filter, у каждой `-dur`, `-ease`, `-delay`; по умолчанию прозрачность короче сдвига (0,6 у подъёма). Это поле
   `tracks[].duration | easing | delay_ms` спецификации. `[проверено: длительности по CSSTransition]` → §4.2
6. **Состояния `data-motion` на носителе** (по умолчанию `<html>`): нет атрибута — как в системе; `reduced`; `full` —
   полное вопреки ОС; `paused` — петли стоят. Первые три — контракт кода сайта (`data-motion-set`), `paused` — пауза
   набора. `[проверено]` → §5
7. **Пауза — механизм WCAG 2.2.2 для всех петель сразу**: кнопка `[data-mk~="pause"]` ставит `paused` и возвращает
   выбор до паузы; бюджет внимания (петель в окне L0 1, L1 2, L2 3, телефон — на одну меньше) набор считает и называет
   предупреждением. `[проверено: motion_check EG-A11Y-01…03, -17]` → §5.4
8. **LCP-элемент — только вход `entrance` с `data-mk-lcp`** (сдвиг без прозрачности); появления на нём не ставят; что
   видно при запуске, встаёт в конечное состояние сразу — без мелькания. `[проверено: EG-PERF-07, -10]` → §5.3
9. **Вес**: 8,0 КБ JS и 4,9 КБ CSS brotli в сжатом виде (12,9 КБ на всё) — в бюджете JS подачи L0 (20 КБ); исходники с
   комментариями — 12,1 и 7,9 КБ. `[проверено: esbuild 0.28, brotli 11]` → §8
10. **Запрещено**: `innerHTML`, `appendChild`, `cloneNode`, запись `textContent`, сеть, модули, перехват колеса, своя
    скорость прокрутки, общий reduce `* { animation-duration: .01ms }`. Проверка — `motion_smoke.py` (static).
    `[проверено]` → §9

## 1. Файлы и подключение

| файл | что | вес исходника, raw / gzip / brotli | в сжатом виде (esbuild), raw / gzip / brotli |
|---|---|---|---|
| `examples/motion-kit.js` | скрипт: режим, появления, счётчик, петли, сцены, указатель, кнопки, View Transition | 45,8 / 13,9 / 12,1 КБ | 26,9 / 8,9 / 8,0 КБ |
| `examples/motion-kit.css` | облик движения: состояния, переходы, шкалы прокрутки, петли, переключатель | 41,4 / 9,2 / 7,9 КБ | 29,3 / 5,5 / 4,9 КБ |
| `examples/look.css` | облик демо (бумага, графит, «пластины» кодом) — к набору не относится | — | — |

```html
<!-- страница: выбор движения — до первой отрисовки; набор — в конце body или модулем острова после LCP -->
<script>try { var m = localStorage.getItem('motion'); if (m === 'reduced' || m === 'full') document.documentElement.setAttribute('data-motion', m); } catch (e) {}</script>
<link rel="stylesheet" href="motion-kit.css">
…
<script src="motion-kit.js" data-motion-toggle></script>
<script>var mk = MotionKit.mount(document, { remember: 'local', level: 'L1' });</script>
```

- Строку `<head>` на сайте уже ставит остров предпочтений кода сайта
  (`<org>/site/src/features/preferences/ui/preferences-init.astro`): ключ `motion`, значения `reduced` и `full`. Набор читает тот же ключ (`opts.key`). `[исходник]`
- Атрибут `data-motion-toggle` у тега скрипта говорит `motion_check.py`, что скрипт несёт переключатель и грузится и в
  reduce (EG-A11Y-11). `[проверено]`
- Холст и сайт — `04`.

## 2. API

`MotionKit.mount(root, opts)` — `root`: `document` или элемент (корень артборда); возвращает ручку:

| метод | что делает |
|---|---|
| `destroy()` | снимает слушатели, наблюдатели, кадры и всё, что набор поставил: атрибуты возвращаются к значениям разметки, переменные `--mk-*` уходят; страница — как без JS |
| `pause()`, `resume()` | то же, что кнопка паузы: `data-motion="paused"` и возврат к выбору до паузы |
| `refresh()` | заново ищет контейнер прокрутки, новые элементы `[data-mk]` и режим (`isLive`); сцены сбрасывает к точке покоя только при смене режима; адаптер холста зовёт раз в 1,5 с |
| `info()` | `{version, mode, paused, choice, phone, fine, sda, scroller, counts, reveals: {shown, total}, loopsInView, budget, scenes[], warnings[]}` |
| `transition(fn, type)` | смена состояния в `document.startViewTransition` с типом `mk-state`; не full или нет поддержки — просто `fn()` |

| опция | по умолчанию | что |
|---|---|---|
| `level` | `'L1'` | уровень страницы — бюджет внимания (§5.4) |
| `remember` | `'session'` | где помнить выбор: `'local'` (L2, переключатель на странице), `'session'`, `false` (холст) |
| `key` | `'motion'` | ключ хранилища — тот же, что у острова предпочтений сайта |
| `toggle` | `true` | обслуживать `[data-motion-set]` и `[data-mk~="pause"]`; на сайте кнопки ведёт остров — `false`, набор слушает `data-motion` сам |
| `host` | `<html>` | носитель `data-motion`; на холсте — корень артборда: выбор не уходит на соседние артборды |
| `scroller` | ближайший прокручиваемый | контейнер прокрутки; на холсте прокрутка идёт во внутреннем окне |
| `header` | `--mk-header` | высота липкой шапки, px: сцены закрепляются под ней |
| `isLive` | всегда да | `() => bool` — показан ли документ вживую; холст — `MotionKit.viewMode(root)` |
| `phone`, `fine` | `(max-width: 40rem), (pointer: coarse)`; `(hover: hover) and (pointer: fine)` | телефон; указатель-мышь |
| `onState` | — | `(info) => void` на каждую смену режима — строка состояния артборда |

Статические члены: `MotionKit.version`, `MotionKit.spring(x, v, target, ω, dt)` — пружина сцен (`03` §2),
`MotionKit.damp(x, y, λ, dt)` — сглаживание указателя, `MotionKit.viewMode(root)` — эвристика Play (`04` §1). Событие
`mk:state` с `detail = info()` — на корне при смене режима.

## 3. Словарь атрибутов

**Пишет автор** (разметка): `data-mk="<примитив> …"` — один или несколько примитивов через пробел; опции примитивов —
`data-mk-*` и `style="--mk-*: …"` (`02`, `primitives.yaml`). Служебные метки внутри примитивов:

| метка | где | что |
|---|---|---|
| `data-mk-stagger` | родитель группы появлений | один триггер на группу, каскад по месту (§4.3) |
| `data-mk-inner` | внутри `sweep`, `scroll-mask` | слой с обратным масштабом |
| `data-mk-track` | внутри `marquee` | дорожка; вторая — `aria-hidden="true"` |
| `data-mk-stage`, `data-mk-steps`, `data-mk-beat`, `data-mk-k`, `data-mk-seg`, `data-mk-rail` / `data-mk-dot`, `data-mk-skip`, `data-mk-veil`, `data-mk-story` | внутри `scene` | окно, карточки тактов, подписи, отрезки, рельс, «Пропустить», затемнение выхода, раскадровка (`03`) |
| `data-mk-frame`, `data-mk-caption` | внутри `frame-expand` | кадр и подпись |
| `data-mk-plate`, `data-mk-logo`, `data-mk-row`, `data-mk-shadow`, `data-mk-fade` | внутри `header` | части шапки, которые сжимаются |
| `data-mk-label`, `data-mk-glare`, `data-mk-area` | `magnet`, `tilt`, `spotlight` | подпись магнита, блик наклона, зона прожектора |
| `data-mk-face`, `data-mk-back`, `data-mk-flip-toggle` | внутри `flip` | лицо, оборот, кнопка для тача |
| `data-mk-col`, `data-mk-col-media`, `data-mk-marker`, `data-mk-when` | `columns`, `accordion`, `pause` | колонка и её окно, значок, подпись паузы |
| `data-motion-set="" \| reduced \| full` | кнопки переключателя | контракт кода сайта |

**Ставит набор** (читать можно, писать — нет): корню `data-mk-on="full | reduced | still"`; появлению `data-mk-in`
(`""` — с движением, `"instant"` — сразу); счётчику `--mk-to`, `--mk-dec`, `--mk-group`, `data-mk-fmt`, `data-mk-done`;
петле `--mk-period`, `data-mk-idle`; сцене `--mk-p`, `--mk-len`, `--mk-vh`, `data-beat`, подписям `data-on` и `--mk-fill`,
отрезкам `--mk-a`, `--mk-b`, `data-on`, затемнению `--mk-veil`, рельсу `aria-current`, кнопкам `hidden`; указателю
`--mk-mx`, `--mk-my`, `--mk-rx`, `--mk-ry`, `--mk-gx`, `--mk-gy`, `--mk-glare`, `--mk-x`, `--mk-y`; шапке без шкал
прокрутки `data-mk-shrunk`; перевороту `data-mk-flipped`; кнопкам `aria-pressed`; горизонтали `--mk-panels`; подписи по
кривой — атрибут `startOffset`. Набор не читает DOM-контракт спецификации (`data-section`, `data-slot`, `data-group`,
`data-fx`, `data-moment`): он для проверок, разметка несёт оба словаря.

## 4. Переменные: токены, запасные значения, дорожки

### 4.1. Токены → переменные набора

Имя переменной токена — `--` + путь DTCG через дефисы: `motion.marketing.duration.reveal` →
`--motion-marketing-duration-reveal` (`scripts/project/ds_build.py`, `_var`). Набор объявляет свои переменные через них
с запасным значением: `--mk-dur-reveal: var(--motion-marketing-duration-reveal, 560ms)`. Ветка reduce — значения
`$extensions.org.design-deep-dive.reduce` токенов (`../04-visual-language/marketing-tokens.json`); выбор «Полное»
(`[data-motion="full"]`) возвращает полные значения и при системном reduce.

| переменная набора | токен | запас | reduce | кто берёт |
|---|---|---|---|---|
| `--mk-dur-reveal` | `duration.reveal` | 560ms | 0ms | подъём, вход, слова и буквы разбиения, переворот |
| `--mk-dur-line` | `duration.split-line` | 800ms | 0ms | маска, строки разбиения, шторка, проявление, линия |
| `--mk-dur-split-max` | `duration.split-total-max` | 1000ms | — | потолок разбиения со стаггером |
| `--mk-dur-hero` | `duration.hero-scene` | 900ms | 0ms | сцена первого экрана |
| `--mk-dur-state` | `duration.state` | 320ms | 180ms (`crossfade-reduce`) | окно, подписи сцены, колонки, смена состояния |
| `--mk-dur-page` | `duration.page` | 400ms | 0ms | общий кадр перехода страниц |
| `--mk-dur-counter` | `duration.counter` | 1200ms | 0ms | счётчик |
| `--mk-dur-ui` | `duration.hover` | 200ms | 0ms | аккордеон, подпись кнопки |
| `--mk-dur-feedback`, `--mk-dur-hover` | `duration.feedback`, `duration.hover` | 120ms, 200ms | те же | отклик, уход корня перехода |
| `--mk-dur-crossfade` | `duration.crossfade-reduce` | 180ms | — | затухание вместо смещения |
| `--mk-dur-breathe` | `duration.breathe-period` | 12000ms | — | период дыхания |
| `--mk-stagger-text`, `--mk-stagger-group`, `--mk-stagger-max` | `stagger.text`, `stagger.group`, `stagger.group-total-max` | 60ms, 60ms, 600ms | 0ms, 0ms, — | каскады |
| `--mk-ease-out-expo`, `-out-strong`, `-in-out`, `-in`, `-linear`, `-breathe` | `easing.*` | кривые токенов | — | §4.2 |
| `--mk-shift`, `--mk-shift-hero`, `--mk-lift`, `--mk-magnet` | `distance.shift-reveal`, `shift-hero`, `lift-hover`, `magnet-max` | 16px, 24px, 2px, 8px | 0px | сдвиги |
| `--mk-scale-press`, `--mk-scale-in` | `scale.press`, `scale.reveal-in` | 0.97, 0.96 | 1 | нажатие, проявление, окно |
| `--mk-parallax-max` | `scroll.parallax-ratio-max` | 0.4 | 0 | предел параллакса |
| `--mk-marquee-speed`, `--mk-float` | `loop.marquee-speed`, `loop.float-amplitude-pct` | 40, 3 | 0 | бегущая строка, дыхание |
| `--mk-m` | — | 1 | 0 | множитель пространственного движения у чисто CSS-примитивов |
| `--mk-header`, `--mk-step-h`, `--mk-depth-k`, `--mk-stack-step` | — | 72px, 480px, 1, 24px | — | телефон: 64px, 420px, 0.5, 14px |

Свои числа токенов шкала не держит: `--mk-header` и шаг тактов — геометрия страницы (`03` §3), их задаёт облик.

### 4.2. Своё время у дорожки

Классика ремесла — прозрачность короче сдвига: глаз ловит появление раньше, чем элемент «сел». У примитивов появления
каждая дорожка берёт свою длительность, кривую и задержку; поле `tracks[].duration | easing | delay_ms` спецификации
пишется в эти переменные элемента:

| дорожка | переменные | умолчание |
|---|---|---|
| opacity | `--mk-o-dur`, `--mk-o-ease`, `--mk-o-delay` | подъём и вход — 0,6 × длительности, `out-strong`; проявление — 0,5 × |
| transform | `--mk-t-dur`, `--mk-t-ease`, `--mk-t-delay` | длительность примитива, его кривая |
| clip-path | `--mk-c-dur`, `--mk-c-ease`, `--mk-c-delay` | длительность примитива, его кривая |
| filter | `--mk-f-dur`, `--mk-f-ease`, `--mk-f-delay` | проявление — 0,7 × длительности, `out-strong` |

Общие на элемент: `--mk-dur`, `--mk-ease` (основная длительность и кривая), `--mk-wait` (задержка момента — `trigger.delay_ms`).
Замер в Chromium по объектам `CSSTransition` сразу после срабатывания: подъём — opacity 336 мс и transform 560 мс;
маска — transform и clip-path по 800 мс; шторка — clip-path 800 мс; проявление — opacity 400, transform 800, filter
560 мс; счётчик — `--mk-num` 1200 мс `[проверено: motion_smoke desk]`.

### 4.3. Место в группе и каскад

- Место — `sibling-index()` (Baseline с августа 2026), запасной путь — `--i` в разметке; размер группы — `sibling-count()`
  или `--n`. `--i` в разметке сильнее `sibling-index()`: им пропускают неучастника группы. Переменные `--mk-k` и
  `--mk-cnt` зарегистрированы (`@property`, `<integer>`) — индекс считается у самого элемента. `[документация: MDN]`
- Группа-список (`[data-mk-stagger]`): шаг `min(stagger.group, stagger.group-total-max / (n − 1))`, первые 8 — с шагом,
  остальные сразу; сумма ≤ 600 мс (05/01 §7.4). Разбиение: шаг `min(stagger.text, (split-total-max − длительность) /
  (n − 1))` — вся сцена со стаггером ≤ 1000 мс считается в CSS. `[проверено: шаг 60 мс, задержки по порядку]`

## 5. Состояния движения

### 5.1. Выбор и режим

| `data-motion` на носителе | системный reduce | `data-mk-on` | что видно |
|---|---|---|---|
| нет атрибута | нет | `full` | всё движение |
| нет атрибута | да | `reduced` | конечные состояния; окно, переходы — затуханием |
| `reduced` | любой | `reduced` | то же |
| `full` | любой | `full` | всё движение вопреки ОС |
| `paused` | по выбору до паузы | режим до паузы | петли и проигрыш сцен стоят; появления и прокрутка работают |
| — (обзор холста: `isLive` — нет) | любой | `still` | конечные состояния, петли стоят |

- Набор слушает `prefers-reduced-motion` (`change`) и сам атрибут `data-motion` (`MutationObserver`): выбор, поставленный
  островом сайта или логикой артборда, действует без перезагрузки. `[проверено]`
- Кнопки `[data-motion-set]` ставят `""`, `reduced`, `full`; `aria-pressed` у нажатой. Выбор — в `localStorage`
  (`remember: 'local'`) или `sessionStorage`. `[проверено]`
- `paused` в контракт кода сайта не входит: там единая пауза — «Меньше» (`reduced`, 05/01 §4.4), остров предпочтений
  `paused` не хранит (§ Открытые вопросы).

### 5.2. Видимость без JS

- Скрытое начальное состояние появлений, петли, шкалы прокрутки, сцены и указатель — только под `[data-mk-on="full"]`.
  Без JS атрибута нет: всё в конечном состоянии, сцены — конечным кадром без закрепления, строка — статичным рядом.
  `[проверено: nojs — скрытого текста 0]`
- Вход первого экрана (`entrance`) — CSS-анимация на загрузке с `fill-mode: both`: идёт и без JS и кончается видимым
  (06/01 §4.1). Чисто CSS-примитивы отклика (окно, аккордеон, подпись кнопки, переворот, блик, колонки) работают без JS;
  в reduce их длительности и сдвиги — значения ветки reduce (затухание вместо смещения).
- Полоса прогресса — индикатор: работает без JS и в reduce; без поддержки шкал прокрутки её нет.

### 5.3. LCP и запуск

- LCP-элемент (обычно H1 или постер) — без анимации или `entrance` с `data-mk-lcp`: только сдвиг на `distance.shift-reveal`,
  прозрачность не трогается (05/02 §10). Появления (`rise`, `unmask`, `split`) на LCP-элементе не ставят.
- В момент запуска в full всё, что в окне или выше него, получает `data-mk-in="instant"` до смены атрибута корня: ничего
  не прячется и не «мелькает»; ниже окна — скрытое состояние до прокрутки. `[проверено: EG-PERF-07, EG-PERF-10 — PASS]`
- На сайте набор — модуль острова после `load` в простое (`04` §2): LCP рисуется HTML-ом.

### 5.4. Пауза и бюджет внимания

- Кнопка `[data-mk~="pause"]` — `aria-pressed`, подписи `[data-mk-when="run"]` «Остановить движение» и
  `[data-mk-when="paused"]` «Запустить движение»; видна, только когда движение идёт (`data-mk-on="full"`). Нажатие ставит
  `data-motion="paused"`, повторное возвращает выбор до паузы; пауза помнится в `sessionStorage` (`motion-paused`).
  `[проверено: EG-A11Y-03 — после нажатия 0 бегущих петель]`
- `paused` останавливает самопроизвольное: бегущие строки, дыхание, проигрыш сцены `play` (время сдвигается на длину
  паузы). Появления, шкалы прокрутки, доигрыш тактов и указатель — движение по действию человека — работают.
- Петли стоят вне экрана (`IntersectionObserver` → `data-mk-idle`), в скрытой вкладке (браузер не рисует), при наведении
  и фокусе (бегущая строка) — удобство, а не механизм (05/01 §3.3).
- Бюджет: набор считает петли в окне и один раз предупреждает в консоли, если их больше `level` (L0 1, L1 2, L2 3,
  телефон — на одну меньше, минимум 1; 05/01 §5.2). Предупреждение — ошибка облика, а не набора: петлю убирают или
  разводят секции. `[проверено: EG-A11Y-17 — 1 ≤ 2]`

## 6. Поле `motion-spec` → разметка набора

Момент собирается так: `primitive` — значение `data-mk` на элементе цели (`target` по DOM-контракту), `params` — опции
примитива, поля ниже — в атрибуты и переменные. Чего нет в правом столбце, набор не выражает: такой момент пишется своим
кодом с пометкой `custom` (MS-26).

| поле `motion-spec` | разметка набора |
|---|---|
| `class` | выбирает примитив: one-shot — появления и `entrance`, `shine`; scroll-linked — шкалы CSS, `scene`, `frame-expand`, `horizontal`, `header`, `text-path`; loop — `marquee`, `drift`; pointer — `magnet`, `tilt`, `spotlight`, `button-label`, `flip`, `columns`; transition — `dialog`, `accordion`, `state`, `page-transition` |
| `primitive`, `params` | `data-mk="<id>"`; опция — атрибут `data-mk-<имя>` или переменная `--mk-<имя>` (`primitives.yaml`, поле `options`) |
| `target`, `stagger_targets` | элемент по DOM-контракту (`data-section` → `data-slot` / `data-group` / `data-fx`, `data-moment`); цели стаггера — дети `[data-mk-stagger]` |
| `trigger.type` | `load` → `entrance`; `in-view` → примитивы появления; `scroll-scrub` → `parallax`, `scroll-draw`, `highlight`, `scroll-mask`, `text-mask`, `stack`; `pin-scrub` → `scene`, `frame-expand`, `horizontal`; `hover`, `focus` → `button-label`, `flip`, `shine`, `columns`; `click` → `dialog`, `accordion`, `state`; `pointer` → `magnet`, `tilt`, `spotlight`; `idle-loop` → `marquee`, `drift`; `page-transition` → `page-transition`; `state` → `state` |
| `trigger.delay_ms` | `--mk-wait` (у `entrance` — ещё `--i`) |
| `trigger.threshold`, `root_margin` | не выражается: зона появления — окно без нижних 4 % (06/01 §4.2) |
| `trigger.once` | всегда: появление одно; `each-entry` набор не исполняет |
| `trigger.range` | `scroll-draw` — `--mk-from`, `--mk-to`; у остальных шкал диапазон задан примитивом (`02`); другой — свой CSS по той же шкале |
| `trigger.range_vh.length` | `scene` (scrub, glide) — `data-mk-length`; `frame-expand` — `--mk-len` |
| `trigger.progress` | отрезок сцены — `data-mk-seg="start,end"` (`data-on` и `--mk-a`, `--mk-b`) |
| `trigger.subject` | шкала — коробка самого примитива (у `highlight`, `scroll-draw`, `scroll-mask` — именованная `view-timeline` на нём); другой subject — свой CSS |
| `tracks[].property`, `from`, `to` | начальное и конечное состояния заданы примитивом (`02`); у сцены — CSS автора от `--mk-p`, `--mk-q`, `data-beat` |
| `tracks[].duration`, `easing`, `delay_ms` | `--mk-o-*`, `--mk-t-*`, `--mk-c-*`, `--mk-f-*` (§4.2) |
| `duration` | `--mk-dur`; токен — `var(--motion-marketing-duration-…)`; `share` — число мс от `page.base` |
| `easing` | `--mk-ease: var(--motion-marketing-easing-…)`; `none` — шкалы прокрутки (кривой нет) |
| `stagger.each` | токены `stagger.group` / `stagger.text`; свой шаг — `--mk-stagger-group` на группе |
| `stagger.order` | `dom`; `reverse`, `center`, `edges` — порядок `--i` в разметке |
| `stagger.max_items`, `total_ms_max` | 8 у группы и 12 у разбиения — с шагом, остальные сразу; потолок — `--mk-stagger-max`, у разбиения — `split-total-max` |
| `repeat` | `once` — появления; `infinite` — петли |
| `loop.period_ms` | `--mk-period` (у `drift`; дыхание — половина периода с `alternate`) |
| `loop.speed_px_s` | `data-mk-speed` (30–60, вне — предупреждение и предел) |
| `loop.direction` | `float`, `glow` — alternate; `spin`, `orbit`, строка — normal; `reverse` — не выражается |
| `loop.autostop_ms` | не выражается: петля стоит по паузе, вне экрана и при reduce |
| `scrub.smoothing_s` | сцена — ω пружины `data-mk-tempo` (95 % пути за 4,74/ω: 0,73 с ↔ ω 6,5); шкалы CSS — без сглаживания |
| `scrub.snap` | не выражается: набор прокрутку не двигает |
| `interrupt` | `jump-to-end` — встроено (пролетели — сразу); `follow-input` — шкалы и сцены; `reverse`, `restart` — нет |
| `exit` | `dialog` — выход 0,78 длительности входа кривой `in`; у появлений выхода нет |
| `attach` | не выражается: «грузик на конце линии» — свой CSS по той же шкале |
| `model: spring`, `spring` | сцена — критически демпфированная пружина ω (`data-mk-tempo`), указатель — `damp`; `bounce` > 0 — нет |
| `reduce.strategy` | `final-state`, `stations` (сцена — конечный кадр и карточки), `stop-loop`, `crossfade` (окно, состояние, страницы) — встроены; `static-poster` — не набор (видео, 3D) |
| `mobile.strategy` | встроено у примитива (`02`): указатель — нет, параллакс — половина, горизонталь и кадр до вылета — родные |
| `pause.control` | `page-toggle` — переключатель и пауза; `pause-button` — `[data-mk~="pause"]`; `autostop` — нет; `offscreen`, `hidden_tab` — встроены |
| `lcp: is-lcp` | `entrance` с `data-mk-lcp` |
| `scene.scroll_mode` | `data-mk-mode`: `scrub`, `beats`, `glide`, `play` |
| `scene.pin` | `sticky` — встроено; `pin-transform`, `pin-padding` — нет |
| `scene.length_vh` | scrub, glide — `data-mk-length`; beats — высоты карточек тактов (`03` §3) |
| `scene.stations` | beats — `data-mk-beats` и карточки `[data-mk-beat]`; якоря станций — `data-group` карточек |
| `page.toggle` | `fieldset` с `[data-motion-set]` и `[data-mk~="pause"]` |
| `page.transitions` | `state`, `page-transition`; имена групп — `view-transition-name` в разметке |
| `page.primitives` | §7 |
| `page.lcp`, `page.never`, `page.budget` | разметка и проверки; бюджет — `opts.level` и `motion_check.py` |

`motion_check.py` сверяет моменты с разметкой по `data-moment` после своего прохода прокруткой: одноразовые появления к
выборке уже доиграли и получают N/A; их длительности и кривые меряет `motion_smoke.py` (§4.2).

## 7. Приём появления → примитив набора

Словарь `page.primitives` спецификации и `motion_system.primitives` арт-дирекции переводится в разметку так:

| приём | примитив | разметка | кому |
|---|---|---|---|
| `fade-up` | `rise`; на загрузке первого экрана — `entrance` | `data-mk="rise"`, группа — `data-mk-stagger` на родителе | лиды, абзацы, карточки групп |
| `type-unmask` | `unmask` — блок целиком; `split` — по строкам или словам | `data-mk="unmask"`; `data-mk="split" data-mk-split="lines"` | display-заголовки секций, не LCP |
| `sweep` | `sweep` | `data-mk="sweep" data-mk-from="left"`, внутри `[data-mk-inner]` | кадры, полосы, разделители |
| `number-tick` | `count` | `data-mk="count"` на числе | цифры доказательств, один раз |
| `line-draw` | `draw` — один раз; `scroll-draw` — по прокрутке | `data-mk="draw"`, пути с `pathLength="1"` | схемы, линии этапов |
| `none` | без `data-mk` | — | спокойные секции, формы, цены, юридическое |
| `scale-in` | `scale-in` | `data-mk="scale-in"`, размытие — `data-mk-blur` | фигуры, иллюстрации |

## 8. Вес

| что | raw | gzip 9 | brotli 11 |
|---|---|---|---|
| `motion-kit.js` с комментариями | 45,8 КБ | 13,9 КБ | 12,1 КБ |
| `motion-kit.js`, esbuild `--minify` | 26,9 КБ | 8,9 КБ | 8,0 КБ |
| `motion-kit.css` с комментариями | 41,4 КБ | 9,2 КБ | 7,9 КБ |
| `motion-kit.css`, esbuild `--minify` | 29,3 КБ | 5,5 КБ | 4,9 КБ |
| набор в сжатом виде, JS + CSS | 56,1 КБ | 14,3 КБ | 12,9 КБ |

`[проверено: esbuild 0.28.2, gzip 9, brotli 11]`. Бюджет JS подачи (`ambition-levels.yaml`, `js_presentation_kb_br`):
L0 — 20, L1 — 100, L2 — 150 / 200 КБ; `motion_check.py` на демо — 12,2 КБ JS исходника при пороге спецификации демо
13 КБ (EG-WEIGHT-01, PASS); на сайт идёт сжатый файл — 8,0 КБ. Для сравнения: GSAP + ScrollTrigger — 41,9 КБ brotli
(05/02 §3.5).

## 9. Что запрещено

- Набору: строить и переносить узлы (`innerHTML`, `appendChild`, `append`, `cloneNode`, `createElement`), переписывать
  текст (`textContent =`), ходить в сеть (`fetch`, `XMLHttpRequest`, `import()`), быть модулем (`export`), исполнять
  строки, перехватывать колесо и менять скорость прокрутки, привязывать прокрутку к станциям. Проверка — `motion_smoke.py`
  режим `static`. `[проверено]`
- CSS: общий reduce `* { animation-duration: .01ms !important }` (ui 08/03 §3.3) — reduce набора — конечные состояния
  и затухание вместо смещения по приёмам; анимация свойств раскладки (кроме `block-size` аккордеона, исключение
  `property_exceptions`); `transition: all`; скрытое начальное состояние вне `[data-mk-on="full"]`.
- Разметке: появление на LCP-элементе; разбиение без доступного текста (у букв — `aria-label` на заголовке и
  `aria-hidden` у кусков); петля под абзацем; второй экземпляр `mount` на том же документе с `toggle: true`.

## Частые ошибки

- **Свой `transition` или `transform` на элементе примитива** — примитив владеет ими: отклик наведения — на внутреннем
  элементе.
- **Начальное состояние в CSS без `[data-mk-on="full"]`** — без JS, в reduce и в обзоре холста элемент скрыт навсегда.
- **Длительность числом вместо токена** (`0.45s`) — примета генератора; бери `var(--motion-marketing-…)` или долю базы.
- **Одинаковый подъём на всех секциях** — маркер 28; система — три приёма по ролям, спокойные секции без `data-mk`.
- **`paused` как четвёртая кнопка `data-motion-set`** — пауза — переключатель с возвратом, кнопка `[data-mk~="pause"]`.
- **Второй `mount` с кнопками** — двойная обработка: на сайте с островом предпочтений — `toggle: false`.

## Чек-лист

- [ ] Каждый момент спецификации — `primitive` и `params` из `primitives.yaml` или `custom` с причиной?
- [ ] LCP — `entrance` с `data-mk-lcp` или без движения; появлений на нём нет?
- [ ] Без JS, в reduce и при «Меньше» видно всё (`motion_smoke.py` nojs, rm, reduced)?
- [ ] Числа — переменные токенов, длительности по дорожкам — `--mk-o-*`, `--mk-t-*`?
- [ ] Петли — с паузой в шапке и в бюджете внимания уровня; под абзацем петель нет?
- [ ] На сайте с островом предпочтений — `toggle: false`; на холсте — `host` = корень артборда, `remember: false`?

## Открытые вопросы

- **`paused` и код сайта.** Остров предпочтений хранит только `reduced` и `full` и при `paused` не останавливает
  видео-петли (`video[loop]`); единая пауза сайта — кнопка «Меньше» (05/01 §4.4). Решение — либо `paused` в контракт
  сайта, либо пауза набора на сайте не ставится (`toggle: false`, кнопки `[data-mk~="pause"]` нет).
- **Зона появления.** 05/02 §2.3 — порог 15–25 % элемента; набор берёт окно без нижних 4 % (06/01 §4.2): с обрезкой
  снизу в Chromium часть элементов у дна не появлялась. Нормы выровнять в 05/02.
- **IntersectionObserver и clip-path.** Chromium не сообщает пересечение цели, скрытой собственным `clip-path`
  (маска, шторка), и элементов, пролетевших прыжком; основной триггер набора — коробка элемента в кадре прокрутки
  `[проверено]`, IO — второй.

## Источники

- [S1] Набор `examples/` и его прогоны: `motion_smoke.py` (8 режимов), `motion_check.py --level L1 --spec`,
  `spec_check.py spec` — `[проверено]`, Chromium Playwright 1.63.
- [S2] Нормы: creative 05/01 §3.3, §4, §5, §7; 05/02 §2, §3, §10; 05/03 §1, §2; токены
  `../04-visual-language/marketing-tokens.json`; уровни `../01-creative-direction/ambition-levels.yaml`; каталог
  `../06-effects-catalog/effects.yaml`; спецификация `../09-ai-execution-evaluation/motion-spec.schema.json`, 09/02 §1.7.
- [S3] Сборка ДС — `../../../scripts/project/ds_build.py` (`_var`, ветка reduce с `:root:not([data-motion="full"])`).
- [S4] Код сайта (шаблон `seo-frontend-template`, форк `<org>/site`):
  `<org>/site/src/features/preferences/ui/motion-toggle.astro`, `preferences-init.astro` — контракт `data-motion` и `data-motion-set` `[исходник]`.
- [S5] MDN: `sibling-index()`, `sibling-count()` (Baseline с августа 2026); `@property`; `mod()`, `round()`, `pow()`;
  `@counter-style`; `content` с альтернативным текстом — https://developer.mozilla.org/en-US/docs/Web/CSS `[документация]`.
- [S6] WCAG 2.2 SC 2.2.2, 2.3.3 — https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html `[стандарт]`.
