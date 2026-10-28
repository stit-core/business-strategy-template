# Каталог эффектов подачи: реализация, цена, фолбэки, reduce, телефон, клише

Волна 2 · агент F (2026-09-24) и продолжатель F2 (2026-09-24/25) · 59 записей `effects.yaml` (42 лабораторные страницы `lab/<id>/` +
варианты, 12 внешних ссылок на 3d, ai-media и G) · опыты `99-raw/experiments/F/00–16` · Chromium 153.0.8010.12 и WebKit 26.6
(Playwright 1.63, WebKit 2359; десктоп, reduce, iPhone 13), ANGLE GL на Intel Iris Xe · GSAP 3.15.0, Lenis 1.3.26 · метод
замеров — `03-effects-lab-method.md`.

## Выжимка для агента

1. Эффект выбирай из `effects.yaml` по `id`; в `treatment.effects[].ref` пиши `effect:<id>`; запись без `demo` — чужая
   реализация (3d, ai-media), бери по `external_ref`. → §1.1 `[проверено]`
2. Смотри `level_min` и `limits`: L0 — только CSS-отклик, одно появление, бегущая строка с паузой, статичные градиент и
   зерно, синемаграф; WebGL, закрепление, видео-фон и нативный переход между страницами (`page-transition`, ≤ 400 мс) — с L1;
   свой курсор, плавная прокрутка, горизонталь, переходы страниц на библиотеках — L2 (запреты A `01-creative-direction/03-ambition-levels.md`
   §3.1; X-21). → §1.2, §6.2 `[практика]`
3. Цена эффекта — не частота кадров: в лаборатории все 36 страниц держат 60 кадров/с и 0 мс длинных кадров даже на эмуляции
   Pixel 7 с CPU ×4; эффекты различают время главного потока (мс/с), CLS, доля движения в покое и задержка клика. → §1.3 `[проверено]`
4. Грузи библиотеку только когда эффект включён: закреплённая сцена на GSAP — 45,7 КБ br на десктопе и 3,9 КБ на телефоне и
   при reduce (`LAB.load` по `matchMedia`). → §5.1 `[проверено]`
5. Каждая петля дольше 5 с (бегущая строка, живой фон, видео, бейдж) — видимая пауза на странице; чекбокс + `:has()`
   работает и без JS, JS добавляет остановку своих циклов. → §3.1 `[проверено]` `[стандарт: WCAG 2.2.2]`
6. Скорость бегущей строки 30–60 px/с (длительность = ширина дорожки / скорость), второй список `aria-hidden`, при reduce —
   статичный ряд с переносом; не больше одной строки на странице L0–L1. → §3.1 `[проверено]` `[данные: C]`
7. Крупная кинетическая строка слов даёт 3,8–4,6 % меняющихся пикселей в секунду — «заметная» петля (E §5.4): не под
   читаемым текстом, только L1–L2. → §3.2 `[проверено]`
8. Не разбивай H1 первого экрана: текст рисуется до JS (LCP 40 мс), потом прячется и выезжает — «мелькание»; спрятать до JS
   — значит задержать LCP. Split — для заголовков ниже первого экрана, по строкам, ≤ 1000 мс. → §2.1 `[проверено]`
9. Анимируя текст (scramble, вариативные оси, счётчик), запирай ширину: без неё scramble дал CLS 0,16 на телефоне, буквы
   вариативного шрифта без ячеек — CLS 0,03 и провалы до 33 кадров/с в WebKit. → §2.2, §2.3 `[проверено]`
10. Вращай обёртку `div`, а не `<svg>`: вращение `<svg>` в Chromium перерисовывается каждый кадр — 36 мс/с главного потока на
    десктопе и 127 мс/с на телефоне CPU ×4. → §2.4 `[проверено]`
11. Прогресс, параллакс, подсветка слов, линия, стопка, раскрытие маской — на `animation-timeline` (0 КБ JS) внутри
    `@supports` и `@media (prefers-reduced-motion: no-preference)`; без поддержки — конечное состояние, а не начальное. → §4 `[проверено]`
12. Скрытое начальное состояние появления ставь только при `html.js`: без JS контент обязан быть виден. → §4.2 `[проверено]`
13. У всех эффектов с reduce в лаборатории: 0 % движения, 0 бесконечных анимаций, 0 вызовов WebGL в покое, 0 байт видео;
    reduce — «убрать самопроизвольное и пространственное», а не «удалить эффект» (прожектор закрепляется, стопка липнет). → §1.4 `[проверено]`
14. Непрочитанные слова в подсветке по прокрутке — цвет с контрастом ≥ 3 : 1 при кегле ≥ 24 px, а не прозрачность 0,2. → §2.5 `[проверено]`
15. Счётчик — только для чисел из фактов: итог в HTML, анимируется `aria-hidden` копия, один раз, 1,2 с, `tabular-nums`. → §2.6 `[проверено]`
16. LCP-заголовок первого экрана не появляется из `opacity: 0`: в варианте `fade` LCP «ушёл» на мелкий абзац (40 мс), H1 не
    засчитан; безопасно — только сдвиг 12–16 px (LCP = H1, 84 мс). → §4.1 `[проверено]` `[данные: у ai-media]`
17. Появление при прокрутке должно срабатывать и у самого низа страницы: с зоной IO, урезанной снизу на 12 % (порог 0,12), в
    Chromium 1 из 6 последних элементов не появился даже на дне страницы; без обрезки + «добор» у конца — 0 (WebKit — 0 в обоих). → §4.2 `[проверено]`
18. GSAP-горизонталь, видимая в первом экране, дала CLS 0,35 на десктопе (и с раскладкой из `<head>`); CSS-вариант и нативная
    лента — 0: закреплённые сцены держи ниже первого экрана и проверяй CLS замером. → §5.3 `[проверено]`
19. Перерисовка на главном потоке дорога и там, где её не ждёшь: `@property`-фон — 29 мс/с против 6 у статичного, раскрытие
    `clip-path` на весь экран — 43 мс/с, анимация `box-shadow` — 28 против 20 у псевдоэлемента, шум на canvas — 41 против 7. → §8–§10 `[проверено]`
20. Плавная прокрутка удлиняет шаг колеса: Lenis `lerp 0,1` — хвост 974 мс (`motion_check.py` 0.1.3 — 1,28 с), `lerp 0,2` —
    423 мс, нативно — 0; умолчание — `lerp 0,15` (0,90 с; при 0,12 — 1,09–1,13 с, провал ворот ≤ 1 с); только L2 и только ради
    сцены. → §5.4 `[проверено]` `[данные: C 0,8–1,4 с]`
21. Громкость живого фона меряй долей пикселей: шейдер 2,1 %/с («дыхание»), голо-плёнка в первой настройке 8,3 %/с, CSS-фольга
    с автоповоротом — 57 %/с («громко») → фольга только от курсора, время шейдера ×⅓. → §8 `[проверено]`
22. Переходы между страницами — 0 КБ JS: `@view-transition { navigation: auto }` на обеих страницах, без поддержки — обычная
    навигация. → §6.2 `[проверено]`
23. На L2 — переключатель «Движение» (как в системе / меньше / полное) на `<html data-motion>`: выбор в `localStorage`, ставится
    строкой в `<head>`; «Меньше» останавливает всё без перезагрузки (WebGL — 0 вызовов, видео — пауза и постер, GSAP — `revert()`,
    Lenis — `destroy()`), «Полное» побеждает системный reduce. → §1.5 `[проверено]`
24. Lenis 1.3.26 (`respectReducedMotion: true` по умолчанию) и `gsap.matchMedia` видят только системную настройку: переключатель
    сайта сам создаёт и уничтожает их, Lenis — с `respectReducedMotion: false`. → §1.5 `[проверено]` `[документация]`
25. Закрепление — CSS `sticky` + скраб GSAP без `pin`: `pin` (`position: fixed`) даёт CLS при прокрутке — 0,35 в момент
    закрепления и 0,99 в момент отпускания (прокрутка — не «ввод» для CLS); `pinType: 'transform'` и `sticky` — 0. → §5.3 `[проверено]`
26. Наведение — тоже не «ввод» для CLS: раскрытие подписи кнопки меняй `clip-path` по полной коробке, а не шириной
    (`grid 0fr → 1fr`, `width → max-content`). → §12.3 `[проверено]`
27. Перелив читается материалом только как узкая яркая полоса со структурой (решётка, штрихи), идущая за углом зрения; размытые
    пятна спектра — «радуга ИИ». По умолчанию — окно тонов марки; текст — на скриме ≥ 0,84 (контраст ≥ 4,5 : 1 в худшем положении). → §8.4 `[проверено]`
28. Русскому тексту нужно и латинское подмножество шрифта (цифры, «», —, двоеточие): без его предзагрузки перенос строк при подмене
    дал CLS 0,15 при загрузке — `cls_after_fonts` его не видит. → §1.3 `[проверено]`
29. Проверяй телефонный WebKit отдельно: на iPhone-эмуляции `sticky-stack` — 20 кадров/с (p95 → 4/с), View Transitions — 41 кадр/с;
    `dialog` без `overlay` обрывает выход. → §5.2, §6, §12.1 `[проверено]`

## 1. Как пользоваться каталогом

### 1.1. Запись и ссылки
- Поля — `effects.schema.json` (`motion.kind`, `attention_cost`, `loop_control` — для норм движения `05-motion`); `reduce.strategy` —
  перечисление `treatment` v1 (с `stations`, X-05), `mobile.behavior` — `treatment.v0` A; `motion.kind` — строка или список классов
  моментов (`3d-scene`, X-64); роль эффекта — `effect_role` (было `roles`, X-54); `cliche.registry_id` — реестр H `08-uniqueness-anti-slop/cliche-registry.yaml`;
  `stack_ref` — G `07-stack-implementation/stack.yaml`; числа `cost.*` и `fallback.*.measured` — из замеров лаборатории (`03-effects-lab-method.md`). Каталог правится по месту: схема описывает поля, сверка — `registry_check.py` и `spec_check.py levels --check`; схема проходит метасхему при приёмке правки (`scripts/maint/accept.py`).
- Новые id — `text-scramble`, `variable-font-pointer`, `text-path`, `rotating-badge`, `scroll-text-highlight`,
  `svg-line-draw`, `tilt-card`, `hover-distort-dom`, `aurora-css`, `gradient-seams`, `glass-panel`, `glow-accent`, `scroll-mask-expand`,
  `text-mask-media`, `motion-toggle` и внешние `alpha-video-object`, `particles-webgl`, `webgl-image-distortion`, `depth-parallax-25d`, `preloader`.
- F2 (2026-09-25) id не менял, добавил 7: `dialog-entry-exit`, `details-accordion`, `button-expand-label`, `card-flip-3d`,
  `header-shrink-on-scroll` (семейство `micro`, страницы есть) и внешние `lottie-illustration-loop`, `rive-state-interaction`
  (семейство `vector`, цена — G); у `motion-toggle` появилась своя страница; новые варианты — `horizontal-scroll?pin=transform|sticky`.
- Соседи — по номерам без копирования: `3d:01-01#N.M`, `ai-media:10-03#4.N`; нормы движения — E `05-motion/01` §4–§7.

### 1.2. Уровни
| Уровень | Разрешено из каталога (сверх ниже стоящих) | Запрещено уровнем (A §3.1) |
|---|---|---|
| L0 | `hero-entrance-once` ≤ 600 мс, `marquee-logos` (1, с паузой), `counter-up`, `scroll-driven-progress`, `sticky-stack` без масштаба, `mask-reveal`, `grain-overlay`, `mesh-gradient-css` статичный, `cinemagraph`, `rotating-badge` (1), `motion-toggle` (на L2 обязателен), `dialog-entry-exit`, `details-accordion`, `button-expand-label`, `header-shrink-on-scroll`, `light-sweep`, `expanding-columns`, `overlay-viewer`, CSS-отклик | WebGL, закрепление со скрабом, плавная прокрутка, свой курсор, видео-фон, появление на каждой секции |
| L1 | + `split-text-reveal`, `kinetic-headline`, `scroll-reveal-system`, `parallax-layers`, `scroll-text-highlight`, `svg-line-draw`, `pin-scrub-story` (1 сцена ≤ 150vh), `scroll-mask-expand`, `view-transition`, `page-transition` (нативный кросс-документный VT, `@supports`, ≤ 400 мс), `cursor-accent`, `magnetic-cta`, `tilt-card`, `hover-distort-dom`, `shader-bg` или `holo-shader-bg` (1 контекст), `aurora-css`, `glass-panel`, `glow-accent`, `text-mask-media`, `video-loop-hero`, `marquee-text`, `3d-object`, `card-flip-3d`, `lottie-illustration-loop`, `rive-state-interaction` | горизонталь, свой курсор, плавная прокрутка, переходы страниц на библиотеках (Barba, Swup) и с заставкой, секвенции, 3D-сцена |
| L2 | + `horizontal-scroll`, `smooth-scroll`, `custom-cursor`, `page-transition` на библиотеках (Barba, Swup) и с заставкой, `variable-font-pointer`, `video-scrub`, `image-sequence`, `3d-scene`, `particles-webgl`; `preloader` — только кампания по явному решению | текст в canvas, изменение скорости прокрутки, эффекты в блоке конверсии |

Свойства приёма (`motion.properties`) на его минимальном уровне сверяет `spec_check.py levels --check` (LV-03).

### 1.3. Что значит «цена»
- `cost.bytes_br` — байты эффекта по сети (свой код, библиотеки, медиа; текст — brotli q11), без общей обвязки и шрифтов;
  `js_kb_br` — из них JS. `fps_*`, `loaf_ms`, `cls`, `input_delay_ms_mobile` — медианы `effect_bench.py` (4-секундный
  сценарий: покой, прокрутка колесом, движение указателя или клики); `frame_ms_unlimited` — цена кадра без vsync для эффектов,
  где кадр рисует JS или WebGL. Главный различитель — `measured.*.TaskDuration_ms_per_s` (работа главного потока в секунду);
  контроль без эффекта — 12,1 / 20,6 мс/с (десктоп / телефон ×4); таблицы разделов — из замеров лаборатории.
- Лаборатория ≠ поле (Iris Xe, headless, эмуляция телефона): сравнивай эффекты между собой; поле — ворота страницы site.

### 1.4. Обязательный контракт каждого эффекта (проверен на всех 36 страницах)
1. Без JS — контент виден (`fallback.no_js.measured.content_ok: true`), скрытые начальные состояния — только при `html.js`.
2. Reduce — 0 % движения в покое, 0 бесконечных анимаций, 0 вызовов WebGL, 0 байт видео (`fallback.reduce.measured`).
3. Петля > 5 с — пауза (чекбокс `#lab-pause` + `:has()`; JS слушает `change`); вне экрана и в скрытой вкладке — стоп (`LAB.loop`).
4. Тач — эффекты наведения выключены по `(hover: hover) and (pointer: fine)`; у эффекта прокрутки на телефоне — своё поведение (`mobile.behavior`).
5. Без поддержки возможности (`@supports`) — конечное состояние; без WebGL — CSS того же тона (`html[data-fallback=css]`).

```css
/* Chromium 153 · WebKit 26.6 · 2026-09-24 · [проверено: lab/_shared/lab.css] пауза без JS (WCAG 2.2.2) */
html:has(#lab-pause:checked) [data-loop], html:has(#lab-pause:checked) [data-loop] * { animation-play-state: paused !important; }
html:has(#lab-pause:checked) video[data-loop] { visibility: hidden; } /* «скрыть» — третий способ 2.2.2 */
```

### 1.5. Переключатель «меньше движения» и общая пауза (`motion-toggle`)
- L2 — обязателен (A CRV-AL-12, E `05-motion/01` §4.4), L1 — при петлях как механизм 2.2.2; L0 — достаточно чекбокса паузы ниже.
- Три состояния на `<html data-motion>`: нет атрибута — как в системе; `reduced`; `full` (вопреки ОС). Выбор — `localStorage`,
  ставится строкой в `<head>` до стилей; нативные радио в `fieldset` с `legend` «Движение», сегменты 44 px, подпись состояния —
  `aria-live` с зарезервированной шириной (иначе сдвиг шапки при загрузке).
- CSS-движение объявлять «от статики» и только когда оно разрешено; токены `--mm-*` E уже дают 0 мс и 0 px в reduce и `reduced`.
- JS-движение подписано на `Motion.on()`: WebGL — один статичный кадр и `cancelAnimationFrame`; видео — `pause()` + `hidden`
  (постер, 0 новых байт); GSAP — `gsap.context().revert()`; Lenis — `destroy()` и `new Lenis({ respectReducedMotion: false })`.
- Замер `lab/motion-toggle/` (F2/12): «Меньше» на лету — движение 3,9 → 0 %/с, 0 бесконечных анимаций, 0 вызовов WebGL; системный
  reduce — 0 %, GSAP, Lenis и видео не грузятся (11,4 против 58,2 КБ br страницы); сохранённое «Полное» при системном reduce —
  3,6 %/с; сохранённое «Меньше» + клик «Полное» — всё запускается без перезагрузки (Chromium и WebKit) `[проверено]`.

```css
/* Chromium 153 · WebKit 26.6 · 2026-09-25 · [проверено: lab/motion-toggle] движение разрешено: ОС без reduce и не «Меньше», или «Полное» */
@media (prefers-reduced-motion: no-preference) { :root:not([data-motion="reduced"]) .marquee__track { animation: marquee var(--dur) linear infinite; } }
:root[data-motion="full"] .marquee__track { animation: marquee var(--dur) linear infinite; }
html:has(#mt-reduced:checked) [data-loop] { animation-play-state: paused !important; }   /* без JS «Меньше» — пауза CSS-петель */
```
```js
/* Chromium 153 · WebKit 26.6 · 2026-09-25 · [проверено: lab/motion-toggle/motion.js, fx.js] ≈ 1 КБ br */
// <head>: try { const m = localStorage.getItem('motion'); if (m === 'reduced' || m === 'full') document.documentElement.dataset.motion = m; } catch (e) {}
Motion.on((reduced) => { syncWebGL(!reduced); video.hidden = reduced; reduced ? video.pause() : video.play();
  if (reduced) { ctx?.revert(); ctx = null; lenis?.destroy(); lenis = null; }
  else { ctx ??= gsap.context(buildScene); lenis ??= new Lenis({ autoRaf: true, anchors: true, respectReducedMotion: false }); } });
```

### 1.6. Эффекты из галерей компонентов (дополнение 25.09.2026 из claude-design-research)

Ролик для Claude Code [S18] советует брать эффекты из китов (Kokonut UI, React Bits, Magic UI). В каталоге это чужая реализация:
запись — по id ниже, пределы — `limits` записи, решение о клише — пять проверок (`../08-uniqueness-anti-slop/01-cliche-policy.md` §1,
X-67), у компонента кита меняются ≥ 2 параметра демо (CRV-CL-07), стек — `../07-stack-implementation/01-stack-choice.md` §6.4.

| В ролике (кит, таймкод) | `effect:` · уровень | `cliche:` | Что сверить |
|---|---|---|---|
| карточка «жидкое стекло» (Kokonut UI, 01:04, 01:38–01:43) | `glass-panel` · L1 | `glassmorphism-panels` | стекло над живым медиа, ≤ 2 слоя в зоне; Liquid Glass Apple — 2025, в ролике «2026» (01:41) |
| живой фон «как у Stripe», сетка градиентов (React Bits, 03:22–03:33) | `shader-bg` · L1; `mesh-gradient-css` · L0 | `mesh-gradient-bg`, `aurora-blobs` | у stripe.com фон — WebGL-шейдер (three r178, 2 контекста; каркас — Next/React, `03-live-sites-measured/sites.csv`), а не React-анимация; палитра бренда, пауза > 5 с |
| 3D-глобус (Magic UI, зависимость `cobe`; 02:39, 07:18) | `3d-object` · L1 | `category-rut-imagery` («глобус с дугами») | глобус — предмет концепции (карта своих маршрутов), иначе колея категории |
| видео в контуре букв (Magic UI через MCP, 07:18–07:20) | `text-mask-media` · L1 | — | настоящий текст, контраст по худшему кадру, reduce |
| бегущая строка (02:40–02:41) | `marquee-logos` · L0, `marquee-text` · L1 | `marquee-strip` | 30–60 px/с, видимая пауза, ≤ 1 на страницу |
| скролл-анимации (anime.js, 05:35–05:38) | `scroll-reveal-system`, `pin-scrub-story` · L1 | `section-fade-up` | система появления по ролям, а не fade на каждой секции |
| интерактивная графика (Rive, 06:19–06:22) | `rive-state-interaction` · L1 | `cursor-watching-eyes` (маскот) | файл `.riv` — с платного тарифа (`07/01` §9) |

Правило ролика «не собирать на одной странице жидкое стекло, 3D-глобус, бегущую строку и пять анимаций одновременно» (02:36–02:42)
совпадает с кластерным порогом H (`08/01` §1.5) и бюджетом внимания E [мнение: S18].

## 2. Текстовые эффекты

| id | Уровень | Реализация | Байт br / JS | Главный поток мс/с (десктоп / телефон ×4) | Особое |
|---|---|---|---|---|---|
| `split-text-reveal` | L1 | GSAP SplitText или свой split | 31 455 / 30 087 (GSAP); 2 493 / 1 125 (свой) | 16,2 / 47,5 (GSAP); 13,4 / 36,8 (свой) | LCP H1 40 мс — текст рисуется до JS |
| `text-scramble` | L1 | свой код | ≈ 2 000 / 775 | 11,6 / 41,1 | без запертой ширины CLS 0,16 (телефон) |
| `kinetic-headline` | L1 | CSS `view()` + оси wdth/wght | 4 816 / 1 449 (с шрифтом-частью) | 16,5 / 26,5 | CLS 0 при строке без переноса |
| `variable-font-pointer` | L2 | JS по требованию | 3 351 / 1 449 | 43,8 при движении курсора | без ячеек CLS 0,03, WebKit fps_low 33 |
| `text-path` | L1 | SVG `startOffset` в rAF | 2 398 / 630 | 17,3 / 26,5 | пересчёт только по прокрутке |
| `rotating-badge` | L0 | CSS rotate обёртки | ≈ 2 400 / 630 | `<svg>`: 36,0 / 126,7 | вращать div, не svg |
| `scroll-text-highlight` | L1 | CSS `view()` по индексу слова | 1 810 / 0 | 18,8 / 38,5 | контраст непрочитанного 3,41 : 1 |
| `counter-up` | L0 | JS ≈ 0,5 КБ | 2 088 / 816 | 10,6 / 38,4 | итог в HTML |

Контроль — страница без эффекта (`split-text-reveal?v=none`): 12,1 / 20,6 мс/с. Все — 60 кадров/с, LoAF 0, reduce 0 % `[проверено]`.

### 2.1. Раскрытие заголовка (`split-text-reveal`)
- По строкам (`mask: 'lines'`) или словам; шаг 60–90 мс; сцена ≤ 1000 мс; один раз; только display-роли D.
- Разбивать после `document.fonts.ready`, `autoSplit: true` (пересплит при смене ширины), доступность — `aria: 'auto'`
  (родителю `aria-label`, кускам `aria-hidden`) `[документация: GSAP SplitText 3.13+]`.
- H1 первого экрана не разбивать: в замере LCP = 40 мс (текст успел нарисоваться до JS), значит, пользователь видит
  «мелькание» — текст, исчезающий и выезжающий заново; прятать до JS — задержать LCP на время загрузки библиотеки. `[проверено]`
- Кириллица: не по буквам длинных слов (8–20 знаков → каскад 0,5–1,5 с на слово) `[не проверено: число E, не мерилось]`.
- Клише: `cliche:split-text-reveal` (saturated, у C — 25 из 49); поворот — одна система на страницу, не на каждом H2.

```js
/* Chrome 153 · GSAP 3.15.0 · 2026-09-24 · [проверено: lab/split-text-reveal] ≈ 30 КБ br, грузится только без reduce */
LAB.load(['gsap.min.js', 'SplitText.min.js']).then(() => { gsap.registerPlugin(SplitText); return document.fonts.ready; })
  .then(() => SplitText.create(el, { type: 'lines,words', mask: 'lines', aria: 'auto', autoSplit: true,
    onSplit: (s) => gsap.from(s.lines, { yPercent: 105, duration: 0.7, stagger: 0.09, ease: 'power3.out' }) }));
```

### 2.2. «Расшифровка» (`text-scramble`)
- Только короткие подписи ≤ 24 знаков, по наведению мыши и фокусу, 600 мс; символы — строчные кириллица и цифры (ближе по
  ширине к исходнику); подпись в `aria-label`, символы `aria-hidden`.
- Ширину запирать до старта: `width` + `white-space: nowrap` + `overflow: clip`. Только `min-width` (наивный вариант) — кнопка
  растёт, соседи прыгают: CLS 0,164 на эмуляции телефона `[проверено]`.

### 2.3. Вариативные оси в движении (`kinetic-headline`, `variable-font-pointer`)
- Гарнитура с кириллицей и осью ширины — Science Gothic (OFL, wdth 50–200, wght 100–900; 64 КБ кириллица) из
  `04-visual-language/cyrillic-display-fonts.yaml`; анимация `font-stretch`/`font-weight` = шейпинг и раскладка строки на
  каждый кадр → одна такая строка в зоне видимости, без переноса, в контейнере фиксированной высоты (CLS 0).
- «Буквы от курсора»: ячейка = ширина самого широкого состояния буквы; без ячеек — CLS 0,03 на десктопе (движение мыши не
  «недавний ввод» для CLS) и провалы до 33 кадров/с в WebKit `[проверено]`; цикл rAF по требованию.
- Клише `cliche:variable-axis-gimmick`: ось меняется по смыслу слова, а не «потому что умеем» `[V:luAqYCd_TC8 14:30]`.


### 2.4. Текст по кривой и круговой бейдж (`text-path`, `rotating-badge`)
- Подпись по кривой: `startOffset` в rAF после события прокрутки, только пока секция видна; SVG `aria-hidden` + тот же текст в
  `sr-only` заголовке.
- Бейдж: оборот 15–30 с, один на страницу, пауза общей кнопкой; **вращать обёртку `div` с `will-change: transform`** — вращение
  самого `<svg>` не композитится и перерисовывается каждый кадр: 36 мс/с главного потока на десктопе, 127 мс/с на
  телефоне CPU ×4 против 8–13 мс/с в покое `[проверено: F/03-batch-A; вариант div — F/08]`. Клише `cliche:circular-rotating-text`.

### 2.5. Подсветка слов по прокрутке (`scroll-text-highlight`)
- Слова разбиты в HTML при сборке (`<span style="--i:N">`), одна `view-timeline` на абзац, диапазон слова по индексу —
  подсветка идёт по словам, а не строками; 0 КБ JS; без поддержки — весь текст в конечном цвете.
- Непрочитанное — цвет, а не прозрачность: `#7b8086` на `#eceee9` = 3,41 : 1 (AA для крупного текста) при кегле ≥ 28 px
  `[проверено: color.py]`; прозрачность 0,2 даёт 1,52 : 1 и проваливает WCAG 1.4.3 `[проверено: color.py composite]`.

```css
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено: lab/scroll-text-highlight] 0 КБ JS */
.hl { view-timeline: --hl block; font-size: clamp(28px, 3.6vw, 56px); }
@media (prefers-reduced-motion: no-preference) { @supports (animation-timeline: view()) {
  .hl span { color: #7b8086; animation: lit linear both; animation-timeline: --hl;
    animation-range: cover calc(22% + var(--i) / var(--n) * 38%) cover calc(24% + var(--i) / var(--n) * 38%); } } }
@keyframes lit { to { color: var(--ink); } }
```

### 2.6. Честный счётчик (`counter-up`)
- Итог — в HTML (без JS, при reduce, для поисковиков и GEO); число — `fact:<id>` из `facts.yaml` text, без «+» и округления
  вверх; анимируется видимая копия `aria-hidden`, итог для скринридера — `sr-only`; один раз при 60 % видимости, 1,2 с,
  ease-out, `tabular-nums`; не в тарифах, ценах и формах.

## 3. Бегущая строка

### 3.1. Логотипы (`marquee-logos`)
- Два одинаковых списка, второй `aria-hidden`; оба едут на `translateX(-100%)` своей ширины — шов не виден; маска краёв
  `mask-image: linear-gradient(90deg, transparent, #000 6%, #000 94%, transparent)`.
- Скорость 30–60 px/с: длительность = ширина списка / скорость (JS после `fonts.ready`), без JS — запас 48 с. Практика: Stripe
  30, Trevor Noah 40, Lama Lama 48 px/с; K3 — 155–164 px/с (почерк генератора) `[данные: C]`.
- Пауза: общая видимая кнопка (WCAG 2.2.2), плюс пауза при наведении и фокусе как удобство; reduce — статичный ряд с
  переносом, дубль скрыт. Доля движения 0,63 %/с — «дыхание»; главный поток 17 / 38 мс/с (десктоп / телефон) против 10 при
  reduce `[проверено]`. Пауза у непрерывного движения на живых сайтах — у 1 из 20 `[данные: C]`.
- Логотипы — только SVG клиента из фактов (ai-media `01/01` §2.3); клише `cliche:marquee-strip` (saturated); ≤ 1 строки на L0–L1.

```css
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено: lab/marquee-logos] 0 КБ JS на движение */
.marquee { display: flex; overflow: hidden; --dur: 48s; }
.marquee__track { flex: none; display: flex; gap: var(--gap); padding-right: var(--gap); }
@media (prefers-reduced-motion: no-preference) {
  .marquee__track { animation: marquee-x var(--dur) linear infinite; }
  .marquee:hover .marquee__track, .marquee:focus-within .marquee__track { animation-play-state: paused; } }
@keyframes marquee-x { to { transform: translateX(-100%); } }
@media (prefers-reduced-motion: reduce) { .marquee, .marquee__track { flex-wrap: wrap; } .marquee__track--dup { display: none; } }
```

### 3.2. Кинетическая строка слов (`marquee-text`)
- Крупные слова 56–168 px: 3,8 % (JS) и 4,6 % (CSS) меняющихся пикселей в секунду — класс «заметная» E §5.4: не под
  читаемым текстом, L1–L2, одна на страницу `[проверено]`.
- Реакция на скорость прокрутки: `x += (60·dir − |v|·0,35)·dt`, вход ограничен 900 px/с — строка не «улетает»; цикл в
  `LAB.loop`; дорожка `aria-hidden`, текст — одной строкой в `sr-only` заголовке (D).

## 4. Прокрутка: появление, прогресс, параллакс, линия

<!-- TABLE:scroll -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `hero-entrance-once` | L0 | 2041 / 0,1 | 5,6 / 18,8 | 0 | 0 | — | 0 · да | 62,4 |
| `scroll-reveal-system` | L1 | 3081 / 0,7 | 19,9 / 79,3 | 0 | 0 | 0,16 | 0 · да | 61,6 |
| `scroll-driven-progress` | L0 | 2096 / 0,2 | 11,4 / 41,9 | 0 | 0 | 0,13 | 0 · да | 62,2 |
| `parallax-layers` | L1 | 2057 / 0,2 | 12,5 / 42,8 | 0 | 0 | 0,16 | 0 · да | 62,4 |
| `svg-line-draw` | L1 | 1774 / 0,2 | 14,7 / 54,4 | 0 | 0 | 0,58 | 0 · да | 62,3 |
<!-- /TABLE -->

### 4.1. Одно появление первого экрана (`hero-entrance-once`)
- ≤ 5 элементов, шаг 80 мс, всё ≤ 900 мс (L0 ≤ 600), один раз; LCP-элемент (H1, постер) — только сдвиг 12–16 px, без
  `opacity: 0` (вариант `fade` — антипример, у ai-media 10/01 §4.3 появление из прозрачности выключает LCP); CSS-анимация с
  `fill-mode: both` заканчивается видимой и без JS.

```css
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено: lab/hero-entrance-once] 0 КБ JS */
@media (prefers-reduced-motion: no-preference) {
  .hero__title { animation: rise 520ms var(--ease-out) both; }            /* LCP: без прозрачности */
  .hero__lede { animation: rise-fade 480ms var(--ease-out) 160ms both; }
  .hero__cta  { animation: rise-fade 480ms var(--ease-out) 240ms both; } }
@keyframes rise { from { transform: translateY(14px); } }
@keyframes rise-fade { from { opacity: 0; transform: translateY(14px); } }
```

### 4.2. Система появления по ролям (`scroll-reveal-system`)
- 2–3 примитива по ролям вместо одного fade-up: текст — сдвиг 16 px + прозрачность 560 мс; медиа — `clip-path` 800 мс;
  карточки — каскад ≤ 3 с шагом 70 мс; один раз на элемент (`IntersectionObserver` + `unobserve`), часть секций — без появления.
- Скрытое состояние — только при `html.js` и `no-preference`: без JS и при reduce всё видно `[проверено: nojs, rm]`.
- У низа страницы: зона IO без обрезки снизу (`rootMargin: 0 0 -4% 0`, `threshold: 0.01`) + «добор» при достижении конца;
  с обрезкой −12 % и порогом 0,12 в Chromium 1 из 6 последних элементов не появился никогда `[проверено]`.
- Вариант `?v=sda` — те же примитивы на `view()`, 0 КБ JS, но обратимый (элемент «уходит» при прокрутке вверх) и без Firefox.
- Клише `cliche:section-fade-up` (dated, high) — одинаковое появление на всех секциях; у C «система ≥ 5 элементов» — 10 из 49.

### 4.3. Полоса прогресса (`scroll-driven-progress`)
- `animation-timeline: scroll(root block)` на `transform: scaleX()`; вне `@supports` полосы нет (`display: none`), а не пустая
  полоса в нуле (антипример 3d 09/03 §3.1 `.bar` с `scaleX(0)`); при reduce остаётся как индикатор положения.

### 4.4. Параллакс слоёв (`parallax-layers`)
- 4 слоя на `view-timeline` сцены: разница скоростей в демо — 30 % высоты сцены (умолчание лаборатории и рецептов; предел уровня —
  40 %, норма E `05-motion/01` §6.2 и `limits` записи; X-08) (дальний ±9 %, ближний ±4 %, передний ∓3 %), без
  масштаба и поворота крупных слоёв; текст едет со страницей; на телефоне — половина амплитуды (`@keyframes` внутри `@media`).
  Тот же приём с картинками ai-media — `ai-media:10-03#4.4` (24vh на 100vh ≈ 40 % — верхняя граница); глубина из карты —
  `3d:01-01#9.5`. Клише `cliche:parallax-everything` — не на каждом экране.

### 4.5. Линия рисуется прокруткой (`svg-line-draw`)
- `pathLength="1"` + `stroke-dasharray: 1`, `stroke-dashoffset` 1 → 0 по `view()`; без поддержки — линия целиком;
  `vector-effect: non-scaling-stroke` при растянутом `viewBox`.

## 5. Закрепление, стопка, горизонталь, плавная прокрутка

<!-- TABLE:pin -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `pin-scrub-story` | L1 | 45751 / 42,1 | 22,3 / 29,9 | 0 | 0 | — | 0 · да | 62,4 |
| `sticky-stack` | L0 | 1967 / 0,2 | 10,9 / 62,4 | 0 | 0 | 0,22 | 0 · да | 22,1 |
| `horizontal-scroll` | L2 | 45454 / 42 | 28,3 / 24 | 0,346 | 0 | 0,29 | 0 · да | 62,3 |
| `smooth-scroll` | L2 | 7055 / 5,3 | 19,3 / 45,3 | 0 | 0 | 0,13 | 0 · да | 62,3 |
| `motion-toggle` | L0 | 3197 / 1,1 | 12,7 / 26,1 | 0 | 3,94 | — | 0 · да | 64 |
<!-- /TABLE -->

### 5.1. Закреплённая сцена (`pin-scrub-story`)
- Длина закрепления — токены `motion.marketing.scroll.pin-l1-max-vh` (L1, одна сцена) и `pin-l2-max-vh` (L2), шаги делят длину
  сцены; не закреплять форму, тарифы и CTA-блок.
- GSAP ScrollTrigger (`pin`, `scrub: 0.6`, `end: '+=' + LEN + '%'`, `invalidateOnRefresh`) грузится только при ≥ 768 px и без
  reduce (`LAB.load` + `gsap.matchMedia`): 45,7 КБ br на десктопе, 3,9 КБ на телефоне; `refresh()` после `fonts.ready`.
- Без JS, при reduce и < 768 px — шаги стопкой в конечных состояниях (`reduce.strategy: custom`, «станции» — предложение E для
  `treatment` v1). CSS-вариант (sticky + `view-timeline`, 0 КБ JS) — те же кадры по долям; без поддержки — стопка.


### 5.2. Стопка липких карточек (`sticky-stack`)
- Все карточки в одном контейнере (`position: sticky` работает в пределах родителя), `top: calc(72px + i·24px)`; масштаб
  предыдущей 1 → 0,94 по `view-timeline` следующей через `timeline-scope` на контейнере; 0 КБ JS; при reduce — без масштаба.
- WebKit: 22 кадра/с на десктопе и 20 на iPhone-эмуляции (p95 → 4 кадра/с) при 62 у остальных страниц — вероятная цена
  `filter: brightness()` на липких карточках; для Safari — только `transform` `[проверено: F2/11; причина — гипотеза]`.

```css
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено: lab/sticky-stack] */
.stack { timeline-scope: --c0, --c1, --c2, --c3; display: grid; gap: 36vh; }
.card { position: sticky; top: calc(72px + var(--i) * 24px); view-timeline-name: var(--self); transform-origin: 50% 0; }
@media (prefers-reduced-motion: no-preference) { @supports (animation-timeline: view()) {
  .card { animation: sink linear both; animation-timeline: var(--next); animation-range: entry 0% entry 100%; } } }
@keyframes sink { to { transform: scale(.94); filter: brightness(.82); } }
```

### 5.3. Горизонтальная лента (`horizontal-scroll`)
- Только L2 (A); ≤ 5 панелей; GSAP: `pin` обёртки + `x: -(scrollWidth − innerWidth)`, `end: '+=' + ширина`, `scrub: 1`,
  `invalidateOnRefresh` (taste §5.B: `start: 'top top'`).
- CLS — от самого закрепления, а не от «первого экрана»: `pin` GSAP (`position: fixed`) при прокрутке даёт сдвиг `div.hs__sticky`
  0,35 в момент закрепления и 0,99 в момент отпускания (атрибуция `LayoutShift.sources`, F2/15; прокрутка — не «ввод», сдвиги
  засчитываются). Схема по умолчанию — CSS `position: sticky` + скраб GSAP без `pin` (`?pin=sticky`, CLS 0); `pinType: 'transform'`
  (`?pin=transform`) — тоже 0, но на нативной прокрутке документа возможно дрожание (E/02, проверять записью) `[проверено]`.
- По умолчанию (телефон, reduce, без JS) — нативная лента `overflow-x: auto` + `scroll-snap-type: x mandatory`, `tabindex="0"` и
  `aria-label` для клавиатуры: перехват оси прокрутки на телефоне не делать.

### 5.4. Плавная прокрутка (`smooth-scroll`)
- Только L2 и только когда есть сцена, которой нужна синхронизация (WebGL, скраб); Lenis 1.3.26 (4,9 КБ br): `autoRaf: true`,
  `anchors: true`, `respectReducedMotion` — по умолчанию `true` (README 1.3.26); грузить только при `(hover: hover) and
  (pointer: fine)` и без reduce. Хвост после шага колеса — ≤ 1,0 с (C: Lenis 0,8–1,4 с, нативно ≤ 0,06 с). Клише
  `cliche:smooth-scroll-default` (saturated, high).
- **Умолчание `lerp: 0.15`** (S1 2026-09-25, X-10): хвост по `motion_check.py` 0.1.3 (десктоп, Chromium 153) — 0,1 → 1,28 с,
  0,12 → 1,09–1,13 с (провал EG-PERF-03), 0,15 → 0,90 с, 0,2 → 0,72 с; расчёт по формуле 99 % (0,6 с при 0,12) занижает — хвост
  мерить; токен `motion.marketing.scroll.lenis-lerp` = 0,15. Таблица выше — замер F при прежнем 0,1. На L2-странице Lenis живёт
  только вместе с переключателем движения (`motion-toggle`, EG-A11Y-12, §1.5); демо `lab/smooth-scroll` — страница эффекта без
  переключателя: S EG-A11Y-12 при `--level L2` ожидаем (`lab.json` `gate_note`). `[проверено]`

## 6. Переходы (View Transitions)

<!-- TABLE:transition -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `view-transition` | L1 | 2141 / 0,7 | 26,9 / 143 | 0 | 0 | — | 0 · да | 57,8 |
| `page-transition` | L1 | 12297 / 2,9 | 0,3 / — | 0 | 0 | — | 0 · да | 52,3 |
<!-- /TABLE -->

### 6.1. Внутри страницы (`view-transition`)
- `document.startViewTransition(render)`; общий `view-transition-name` у главного медиа (группа 420 мс), текст — перекрёстно
  260 мс; без поддержки — тот же `render()` без обёртки; reduce — `::view-transition-group(*) { animation: none }`.
- Практика: VT объявлены у 1 из 49 наградных (строка `startViewTransition` в коде роутеров — у 16) `[данные: C]`.
- iPhone-эмуляция WebKit: 41 кадр/с (p95 → 17/с) и задержка клика 64 мс у `view-transition`, 41 кадр/с у `page-transition` —
  переходы на телефоне короче и с одной группой `[проверено]`.

### 6.2. Между страницами (`page-transition`)
- Обе страницы: `@view-transition { navigation: auto; }` + общие `view-transition-name` у обложки и заголовка; 0 КБ JS;
  настоящие страницы с URL — SEO и доступность не меняются; без поддержки — обычная навигация.
- **Уровень — L1** для нативного кросс-документного VT: прогрессивное улучшение (`@supports`, без поддержки — обычная навигация),
  анимация только при `prefers-reduced-motion: no-preference`, ≤ 400 мс на многостраничнике (E `05-motion/02` §8.3); переходы на
  библиотеках (Barba, Swup) и JS-переходы с заставкой — L2 (`limits.library_level_min`). Решение оркестратора 2026-09-25 по X-21
  (`CONTRADICTIONS.md`); до него — `level_min: L2` и «кандидат в L1» `[практика]`.

```css
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено: lab/page-transition] 0 КБ JS */
@view-transition { navigation: auto; }
.vt-hero { view-transition-name: case-hero; }
::view-transition-group(case-hero) { animation-duration: 400ms; animation-timing-function: cubic-bezier(.2, .7, .2, 1); }
@media (prefers-reduced-motion: reduce) { ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; } }
```

## 7. Курсор и наведение

<!-- TABLE:cursor -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `custom-cursor` | L2 | 2512 / 0,8 | 22,3 / 27,7 | 0 | 0 | 1,79 | 0 · да | 62 |
| `cursor-accent` | L1 | 2249 / 0,6 | 22,9 / 44,7 | 0 | 0 | 10,57 | 0 · да | 62,3 |
| `magnetic-cta` | L1 | 1902 / 0,6 | 12,8 / 31 | 0 | 0 | — | 0 · да | 62,6 |
| `tilt-card` | L1 | 2104 / 0,6 | 27,8 / 35,4 | 0 | 0 | 0,14 | 0 · да | 60,7 |
| `hover-distort-dom` | L1 | 2216 / 0,7 | 15,3 / 28,5 | 0 | 0 | 2,93 | 0 · да | 62,5 |
<!-- /TABLE -->

- Все эффекты указателя — только `(hover: hover) and (pointer: fine)` и без reduce; обновление стилей — раз в кадр после
  `pointermove` (rAF по требованию), не в каждом событии и не в вечном цикле.
- `custom-cursor` (L2): точка без задержки, кольцо догоняет с λ ≈ 18 (≈ 120 мс), `mix-blend-mode: difference`; `cursor: none`
  только на `html.has-cursor`, на полях ввода — системный курсор; клише `cliche:custom-cursor-follower` (C: 10 из 49).
- `cursor-accent` (L1): пятно цвета акцента только внутри hero и под текстом (`z-index: -1`); при reduce и на тач — закреплено в
  70 %/30 %, акцент остаётся (Hallmark HP3); вариант `border` — подсветка рамок карточек маской на псевдоэлементе. Hallmark
  запрещает mouse-follow градиенты на SaaS-лендингах и разрешает в портфолио `[мнение]`; близкий приём J — прожектор маской
  `ai-media:10-03#4.1` (две петли, клавиатура — кнопкой `aria-pressed`).
- `magnetic-cta` (L1): смещение ≤ 8 px (норма E `05-motion/03` §1.4, токен `--mm-magnet-max`; до S1 2026-09-25 — 10 px, X-09) в
  радиусе 1,6 размера, подпись +40 %, возврат CSS-пружиной 450 мс; зона клика не уходит дальше 8 px (WCAG 2.5.8); одна кнопка на
  экран; клише `cliche:magnetic-button`.
- `tilt-card` (L1): ≤ 7°, `perspective: 900px`, блик `soft-light`; один ключевой ряд, не все карточки; higgsfield считает
  наклон «приправой», а не «вау» `[мнение вендора]`.
- `hover-distort-dom` (L1): SVG `feTurbulence` + `feDisplacementMap`, `scale` 0 → 26 за 420 мс; фильтр висит на элементе только
  во время анимации (в покое — 0 работы); растеризация фильтра — на процессоре. WebGL-версии (1 вызов на картинку, переходы по
  карте смещения, искажение от скорости) — `3d:01-01#9.1`, `#9.2`, `#9.4`; клише `cliche:liquid-hover-distortion` —
  на каждой карточке.
- `light-sweep` (L0, семейство `image`): наклонная полоса света — отдельный слой поверх кадра внутри его рамки
  (`overflow: hidden`) — один раз проходит по кадру на наведение или фокус с клавиатуры (`:hover`, `:focus-visible`), без петли;
  движется только полоса (`transform`), проявляется и гаснет прозрачностью, коробка карточки, кадр и текст стоят. Наведение —
  в `(hover: hover) and (pointer: fine)`, на тач блика нет; длительность — шкала `motion.marketing.duration`; reduce — блика нет;
  полоса — декоративный слой (`aria-hidden`). Лабораторной страницы и замера нет.

## 8. Фоны

<!-- TABLE:background -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `shader-bg` | L1 | 3622 / 2 | 14,4 / 31,8 | 0 | 2,08 | 0,45 | 0 · да | 62,4 |
| `mesh-gradient-css` | L0 | 2094 / 0,2 | 28,8 / 114,1 | 0 | 0 | 0,47 | 0 · да | 62,5 |
| `aurora-css` | L1 | 2271 / 0,6 | 15 / 44,1 | 0 | 0 | 0,17 | 0 · да | 62,5 |
| `holo-shader-bg` | L1 | 5354 / 2,9 | 20,3 / 47,6 | 0 | 0 | 0,58 | 0 · да | 62,6 |
| `grain-overlay` | L0 | 2278 / 0,5 | 7,3 / 29,6 | 0 | 0 | — | 0 · да | 62 |
<!-- /TABLE -->

### 8.1. Шейдерный фон (`shader-bg`)
- WebGL2 без библиотек: полноэкранный треугольник по `gl_VertexID` (без буферов), градиентный шум с деформацией домена — дрейф
  непериодический (нет качания 0,2 Гц, E §6.3), палитра — CSS-токены страницы (`getComputedStyle`), дизеринг ±0,5/255;
  1 вызов на кадр, DPR ≤ 1 (телефон 0,75), `powerPreference: 'low-power'`. Код с three и замер 1,45 мс/кадр — `3d:09-04#2.1`.
- Цикл — только при видимости, без паузы и reduce; при reduce — один кадр (0 вызовов); без WebGL — CSS-градиент того же тона
  под canvas (`html[data-fallback=css]`) `[проверено: nogl]`. Движение 2,1 %/с — «дыхание»; скрим под текстом.
- Клише: `cliche:mesh-gradient-bg` (saturated) и, при пурпуре 270–320° без бренда, `cliche:purple-neon-band` (high).

### 8.2. Mesh-градиент на CSS (`mesh-gradient-css`)
- 3–4 `radial-gradient` цветов марки; живой вариант — зарегистрированные `@property` (центры, цвет) с периодами 29/37/43 с
  (некратные — рисунок не повторяется); статичный — L0. Анимация `@property` фона — стиль и перерисовка на главном потоке каждый
  кадр (см. таблицу); вариант `blobs` — размытые пятна на `transform` (композитор + размытие на GPU).

### 8.3. «Сияние» (`aurora-css`)
- 3 «занавеса» — полосы градиента, `filter: blur(48px)`, `mix-blend-mode: screen`, дрейф `transform` 31/41/53 с. Только когда
  сияние — сюжет (северный туризм); клише `cliche:aurora-blobs` (saturated, high — «фиолетовая аврора ИИ-стартапов»). Готовые
  no-code авроры (Unicorn Studio) — TBT 254–1158 мс (`3d:01-01#5.7`). Цена кадра без vsync — 9,6 мс против 0,45 мс у
  `shader-bg`: CSS-размытие на весь экран в 21 раз дороже шейдера `[проверено]`.

### 8.4. Иридесцентный фон (`holo-shader-bg`) — закрывает висячую ссылку `3d 06/01 §3.5`
- Оценка глазами F2 (пары «до → после» — `99-raw/experiments/F/14-holo-look/before-after-*.jpg`): первая модель (тонкая плёнка +
  френель) давала тусклые размытые пятна спектра на тёмном — «радугу ИИ» и соседство с `cliche:mesh-gradient-bg`, окно марки — плоский
  бирюзовый градиент, CSS-фольга — оранжевые полосы. Перелив читается материалом, только когда это **узкая яркая полоса со структурой,
  идущая за углом зрения** `[проверено: оценка F2; показ людям — живая фаза]`.
- Модель F2 — дифракционная решётка: полоса блика (гаусс по `dot(p, L)`, смещение — наклон от курсора, на тач — от прокрутки,
  сглаживание λ = 6), в ней спектр по порядку и второй порядок 0,35; ориентация решётки меняется пятнами (шум, «мозаика» защитной
  голограммы) и неподвижна во времени — иначе штрихи от абсолютных координат «ползут» (3,8 %/с в покое против 0–0,02); штрихи ≈ 5 px
  (±10 % яркости); белое ядро блика; тёмная «металлическая» основа; 2 шума на пиксель вместо ≈ 11; кадр без vsync — ≈ 0,6 мс против 1,74.
- По умолчанию — окно тонов марки (`?palette=brand`: рампа `--sea → --sun → --accent`, «золотая плёнка»); полный спектр — только
  если продукт буквально голограмма (клише `cliche:iridescent-holo`, пурпурный край — `cliche:purple-neon-band`).
- Текст: скрим ≥ 0,84 под всей текстовой колонкой (десктоп) или сверху вниз (телефон), полоса в покое — вне колонки (`uOff` 0,18;
  телефон 0,36 — над текстом). Худший контраст из 7 положений полосы по границам текста ≥ 4,5 : 1 (eyebrow в окне марки на
  телефоне — 4,52; H1 ≥ 9,6; лид ≥ 9,4; `contrast.py`) `[проверено]`. Без WebGL — CSS-фольга той же конструкции (`@property --p`).
- Запрет 3d MAT-07 «нет иридесценции в hero» касается рендера (ΔE 4,5–7,9 к Blender), а не веб-шейдера (поправка PLAN).

```glsl
// WebGL2 · 2026-09-25 · [проверено: lab/holo-shader-bg/fx.js] дифракционная полоса (gn — градиентный шум; uTilt — наклон; uOff — положение покоя)
float ang = 1.05 + 1.3 * gn(p * 1.1);  vec2 g = vec2(cos(ang), sin(ang));                         // «мозаика» ориентации, неподвижна во времени
float ph = fract(dot(p, g) * 1.8 + dot(uTilt, g) * .8 + .12 * gn(p * 2.6 - t));                       // фаза: цвет меняется с углом
float s = dot(p, normalize(vec2(.62, .78))) - (uTilt.x * .5 + uTilt.y * .32) - uOff;                  // полоса идёт за углом зрения
float b1 = exp(-s * s / .03), band = b1 + .35 * exp(-(s + .62) * (s + .62) / .018);                    // первый и второй порядок
vec3 col = base + mix(spec(ph), ramp(ph), uBrand) * band * .95 * (.9 + .1 * sin(dot(gl_FragCoord.xy, g) * 1.15))
         + vec3(1., .97, .92) * pow(b1, 8.) * .35;                                                     // штрихи ≈ 5 px и белое ядро
```

### 8.5. Зерно (`grain-overlay`) и стыки
- Статичное: SVG `feTurbulence` тайлом 220 px (0,3 КБ), 6–9 %, `soft-light`, слой под текстом в `isolation: isolate` —
  по сути бесплатно; анимированное (8 шагов/с) — петля с паузой; шум на canvas каждый кадр — антипример (см. таблицу).
  Бандинг и дозировка — `ai-media:10-03#4.3`; цена CSS-зерна против постобработки — `3d:09-04#9` (0,63 против 1,9 мс).
- Стыки секций (`gradient-seams`) — CSS-градиенты 140 px под навигацию и 96–120 px в цвет следующей секции (`ai-media:10-03#4.2`).

## 9. Поверхности

<!-- TABLE:surface -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `glass-panel` | L1 | 2636 / 0,9 | 15,5 / 101,8 | 0,062 | 2,09 | 0,12 | 0 · да | 62,3 |
| `glow-accent` | L1 | 1831 / 0,1 | 13,7 / 37,1 | 0 | 0 | 0,11 | 0 · да | 62,2 |
<!-- /TABLE -->

- `glass-panel`: над движущимся фоном — 7,5 мс на кадр без vsync (3 панели, blur 24; 6 панелей и blur 48 — 7,6: цена почти не
  растёт с числом панелей, её задаёт перерисовка фона); лимит стекла — бюджет кадра, а не
  стиль (поправка PLAN к `ui 11/04:192`): число панелей в зоне видимости и радиус — по таблице; фолбэк без поддержки и при
  `prefers-reduced-transparency` — плотная заливка с тем же контрастом; клише `cliche:glassmorphism-panels`.
- `glow-accent`: анимировать `opacity` и `transform` размытого псевдоэлемента, а не `box-shadow` (перерисовка каждый кадр);
  по умолчанию — статичное свечение; вечная пульсация CTA — `cliche:pulsing-cta` (dated) и сигнал внимания по E §6.4.

## 10. Маски и clip-path

<!-- TABLE:mask -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `scroll-mask-expand` | L1 | 1683 / 0,2 | 16,9 / 27,2 | 0 | 0 | 0,42 | 0 · да | 62,3 |
| `mask-reveal` | L0 | 2263 / 0,4 | 27,7 / 39 | 0 | 0,48 | 0,12 | 0 · да | 62,2 |
| `text-mask-media` | L1 | 1522 / 0,2 | 20,5 / 36,1 | 0 | 0 | 0,38 | 0 · да | 62,4 |
<!-- /TABLE -->

- `mask-reveal` (L0): `clip-path: inset(100% 0 0 0)` → `inset(0)` за 900 мс + обратный масштаб 1,06 → 1, один раз по IO,
  скрытие только при `html.js`; вариант «окно-арка» — `mask-image` из SVG 0,2 КБ растёт по `view()` (окно в форме знака —
  кандидат W2 `[V:xQnJLYTVl_E 24:06]`). Два класса движения (`motion.kind`): `one-shot` — раскрытие по IO, `scroll-linked` —
  окно-арка по `view()`.
- `scroll-mask-expand` (L1): sticky-сцена 100svh в обёртке 100svh + 150vh; кадр из `inset(22% 30% round 28px)` раскрывается до
  полного вылета за 70 % пути, подпись — в последней четверти; < 768 px и при reduce — кадр сразу на всю ширину (механика C3
  higgsfield `[мнение вендора]`).
- `text-mask-media` (L1): `background-clip: text` с кадром; `background-position` по `view()` — перерисовка на главном
  потоке; настоящий текст (выделяется, читается), контраст — тёмная часть кадра + обводка 1 px; без поддержки — сплошной цвет.
  Два класса движения (`motion.kind`): `scroll-linked` и `one-shot`.

## 11. 3D, WebGL над картинками, секвенции, прелоадер — ссылками

| id | Уровень | Где реализация и ворота | Клише H |
|---|---|---|---|
| `3d-object` | L1 | `3d:01-01#2.1`, `#2.2`; ворота `3d:09-05#7.2` | — |
| `3d-scene` | L2 | `3d:01-01#4.1`, `3d:09-03#2`; ворота `09-05#7.2` | `cliche:webgl-centerpiece` |
| `particles-webgl` | L2 | `3d:01-01#6.1`, `#6.2` | `cliche:particle-swarm` |
| `webgl-image-distortion` | L1 | `3d:01-01#9.1`, `#9.2`, `#9.4` | `cliche:liquid-hover-distortion` |
| `depth-parallax-25d` | L1 | `ai-media:10-03#4.5`, `3d:01-01#9.5` | — |
| `alpha-video-object` | L1 | `3d:01-01#15.2`, `ai-media:10-02#7` | — |
| `video-scrub` / `image-sequence` | L2 | `3d:01-01#15.3`, `#14.1`; `ai-media:10-02#9` | — |
| `preloader` | L2 (кампания) | правила — E `05-motion/02`; запрет на продуктовых — `3d:01-02#26` | `cliche:preloader` |

## 12. Микровзаимодействия (F2): диалог, аккордеон, кнопка, переворот, шапка

<!-- TABLE:micro -->
| id | Ур. | Байт br / JS КБ | Главный поток мс/с (деск / тел ×4) | CLS | Движение %/с | Кадр без vsync, мс | Reduce: движение · контент | WebKit fps |
|---|---|---|---|---|---|---|---|---|
| `dialog-entry-exit` | L0 | 3085 / 0,7 | 18,6 / 46,8 | 0 | 0 | — | 0 · да | 62,8 |
| `details-accordion` | L0 | 2775 / 0,4 | 25 / 70,7 | 0 | 0 | — | 0 · да | 64,6 |
| `button-expand-label` | L0 | 2895 / 0,4 | 17,1 / 21 | 0 | 0 | 1,88 | 0 · да | 62,4 |
| `card-flip-3d` | L1 | 2956 / 0,4 | 17,1 / 35,9 | 0 | 0 | 0,31 | 0 · да | 62,3 |
| `header-shrink-on-scroll` | L0 | 3384 / 0,3 | 15 / 27,4 | 0 | 0 | 0,14 | 0 · да | 61,7 |
<!-- /TABLE -->

Правила движения — E `05-motion/03` §1–§2; здесь — реализация и замер (`99-raw/experiments/F/16-micro`, клик каждые 0,7 с, указатель по
кривой, прокрутка колесом; телефон — Pixel 7 CPU ×4).

### 12.1. Вход и выход окна (`dialog-entry-exit`)
- `<dialog>` + `showModal()`; вход 300 мс `cubic-bezier(0,0,.2,1)`, выход 250 мс `cubic-bezier(.4,0,1,1)` (выход короче входа
  [V:UcXWY057YuQ 05:15]), сдвиг ≤ 24 px, `::backdrop` вместе с окном; `@starting-style` + `overlay`/`display` с `allow-discrete`.
- Chromium 153: на 60 мс после открытия прозрачность 0,33, после закрытия 0,93 — выход виден; WebKit 26.6: `overlay` нет — выход
  обрывается (на 60 мс уже `display: none`), вход работает, прыжка нет `[проверено]`. Цена — главный поток 18,6 против 14,5 мс/с без
  перехода (десктоп), 46,8 против 30,1 (телефон ×4); reduce — проявление 180 мс без сдвига.

```css
/* Chromium 153 · WebKit 26.6 · 2026-09-25 · [проверено: lab/dialog-entry-exit] 0 КБ JS на движение */
@media (prefers-reduced-motion: no-preference) {
  .sheet { opacity: 0; transform: translateY(24px) scale(.98);
    transition: opacity 250ms cubic-bezier(.4,0,1,1), transform 250ms cubic-bezier(.4,0,1,1), overlay 250ms allow-discrete, display 250ms allow-discrete; }
  .sheet[open] { opacity: 1; transform: none; transition-duration: 300ms; transition-timing-function: cubic-bezier(0,0,.2,1); }
  @starting-style { .sheet[open] { opacity: 0; transform: translateY(24px) scale(.98); } } }
```

### 12.2. Аккордеон (`details-accordion`)
- `<details name>` (эксклюзивный, без JS) + `::details-content { block-size: 0; overflow-y: clip }`, `[open]` — `auto`,
  `:root { interpolate-size: allow-keywords }`, `content-visibility … allow-discrete`; вне Chromium 129+ — мгновенное открытие.
- Анимация высоты — раскладка на каждом кадре (исключение из E `03` §2.1 п. 9 только для раскрытия по клику): CLS 0 и при 250, и
  при 800 мс (сдвиги идут за кликом), но главный поток телефона ×4 — 70,7 мс/с при 250 мс и 163,4 при 800 мс против 35,6 без
  анимации → **≤ 300 мс** `[проверено]`.

### 12.3. Кнопка-значок раскрывает подпись (`button-expand-label`)
- Раскрытие — `clip-path` по полной коробке кнопки: CLS 0, раскладка 0 мс/с; дорожка сетки `0fr → 1fr` и `width → max-content`
  (`interpolate-size`, только Chromium) — CLS 0,0028 за 3 наведения и 2,0–2,3 мс/с раскладки: наведение — не «ввод», сдвиги
  копятся за сессию `[проверено]`. Скрытая часть не ловит наведение (попадание учитывает `clip-path`); тач — подписи видны всегда.

### 12.4. Переворот карточки (`card-flip-3d`)
- Громкое — только в `no-preference`: `rotateY(180deg)` 500 мс; по умолчанию и в reduce — оборот проявляется 180 мс (Una Kravets
  [V:_ZdZh-ESOHY 04:05]). Паритет `:hover` / `:focus-within`, на тач — кнопка «Подробнее» (`aria-expanded`), фокус — на ссылку оборота.
- Оборот скрывать `opacity` + `pointer-events`, не `visibility`: иначе ссылка оборота выпадает из порядка Tab (ошибка исправлена F2).
- Грани `position: absolute`, лицу `transform: rotateY(0)` и `z-index: 2`, обеим `-webkit-backface-visibility: hidden`. В WebKit
  Playwright на Linux переворот не проверяется (нет 3D-композитинга, эталон тоже «ломается») — Safari только на iPhone.

### 12.5. Шапка сжимается при прокрутке (`header-shrink-on-scroll`)
- `animation-timeline: scroll(root)` + `animation-range: 0 160px`; шапка `fixed` постоянной высоты, «сжатие» — только
  `transform`/`opacity` (плашка `scaleY` от верха, строка −18 px, логотип `scale .78`, подпись гаснет, тень — отдельный слой
  с `opacity`, не `box-shadow`); без SDA (Firefox) — класс по порогу 40 px из rAF + переходы 240 мс (`?v=class`).
- Антипример `?v=height` (высота шапки в потоке по прокрутке) — CLS 0,0004 и раскладка на кадре при 0 у варианта `transform`: мало, но
  не ноль, и растёт с высотой шапки `[проверено]`; reduce — сразу компактная шапка.

### 12.6. Раздвижные колонки (`expanding-columns`)
- L0, роли `signature` и `support`: колонка-кадр под указателем или фокусом раскрывается шире соседних — `clip-path` окна
  колонки и сдвиг соседних `transform`; раскладка ряда стоит, свойства раскладки (`flex-grow`, `width`,
  `grid-template-columns`) не анимируются.
- Без указателя и фокуса раскрыта первая колонка; фокус с клавиатуры (`:focus-visible`) раскрывает так же, как наведение,
  наведение — в `(hover: hover) and (pointer: fine)`; на тач колонки стоят раскрытыми — одна под другой или равным рядом.
  Колонка — ссылка или кнопка в порядке чтения, содержимое закрытой колонки остаётся в DOM.
- Reduce — раскрытие без перехода; длительность — шкала `motion.marketing.duration`. Лабораторной страницы и замера нет.

### 12.7. Наложение-просмотр (`overlay-viewer`)
- L0, роль `feedback`: кадр галереи или работа из сетки открывается крупно поверх страницы, с переходом к соседним. Окно —
  нативный `<dialog>`, открытый `showModal()`: фокус в окне, Esc и «закрыть» закрывают, страница под окном не прокручивается,
  после закрытия фокус возвращается на миниатюру, которая открыла окно.
- Кнопки «закрыть», «вперёд», «назад» — `<button>` с подписями из текстов страницы (слоты подписей управления блока); у окна —
  доступное имя, у кадра в окне — alt миниатюры. Без JS миниатюра — ссылка на кадр или страницу работы.
- Вход и выход окна — `effect:dialog-entry-exit` (движение и reduce — оттуда, §12.1); смена кадра в окне — без движения или
  проявлением; на телефоне окно во всю ширину. Лабораторной страницы и замера нет.

## 13. Векторная анимация: Lottie и Rive (ссылки на G, без лаборатории)

| id | Уровень | Когда | Рантайм и цена (G `stack.yaml`, `G/01-lib-cost`) | Клише |
|---|---|---|---|---|
| `lottie-illustration-loop` | L1 | неинтерактивная иллюстрация или онбординг из After Effects | `lottie-web` 5.13.0 light 41,6 КБ br, TBT 25 мс; dotLottie 0.80.0 — 12,2 + wasm 379,1 КБ br, 0,95 с скрипта за 3,2 с проигрывания | `cliche:stock-lottie` |
| `rive-state-interaction` | L1 | состояния и входы: кнопка с прогрессом, переключатель, маскот формы | `@rive-app/canvas-lite` 2.43.1 — 42,5 + wasm 272,4 КБ br, TBT 38 мс | маскот с глазами — `cliche:cursor-watching-eyes` |

- Выбор: есть состояния и входы (Boolean, Trigger, Number) — Rive, нет — Lottie [V:iqtCk5cY5Xs 14:24, 19:29]; Lottie в Rive не
  конвертировать — анимации теряются, файлы падают [V:iqtCk5cY5Xs 29:45] `[практика]`.
- wasm обоих по умолчанию грузится с jsDelivr/unpkg — `setWasmUrl` на свой домен (CDN в пакете kimi запрещён) `[данные: у G]`.
- Текст и CTA — в HTML, не в анимации; canvas `aria-hidden`; управление Rive — настоящим элементом, его состояние → вход машины.
- Петля Lottie > 5 с — пауза, вне экрана — стоп, reduce — стоп-кадр; ассет — свой или с явной лицензией (у LottieFiles лицензии
  противоречивы, B2). Лабораторной страницы нет: своего `.riv` без редактора Rive не собрать, простой Lottie-JSON — задача F3.

## Частые ошибки
- Библиотека грузится всегда, даже когда эффект выключен (reduce, телефон, CSS-вариант): +30–46 КБ br зря — грузить по `matchMedia`.
- Скрытое состояние без `html.js` (без JS контент невидим) и `scaleX(0)`/`opacity: 0` вне `@supports` (в Firefox — начальное состояние).
- Вращение, масштаб и фильтры на самом `<svg>` вместо обёртки: перерисовка каждый кадр (127 мс/с на телефоне).
- Текстовые эффекты без запертой ширины: scramble — CLS 0,16, оси по буквам — CLS 0,03 и провалы в WebKit.
- Split на LCP-заголовке; побуквенный split длинных кириллических слов; одинаковое появление на каждой секции.
- Петля без паузы (у C пауза — у 1 из 20 страниц с непрерывным движением); пауза только по наведению (тач и клавиатура без неё).
- Непрочитанный текст прозрачностью 0,2 (контраст ≈ 1,5 : 1); градиент или шум под мелким текстом без скрима.
- Анимация `box-shadow`, `background-position`, `@property` фона на большой площади — перерисовка на главном потоке; стекло
  на каждой карточке над движущимся фоном.
- `pin` GSAP по умолчанию (`position: fixed`) в сцене прокрутки — CLS 0,35–0,99 при каждом проходе; закреплять `sticky`.
- Раскрытие по наведению шириной или высотой (подпись кнопки, шапка по прокрутке высотой) — сдвиги считаются в CLS: наведение и
  прокрутка — не «ввод»; менять `clip-path` и `transform`.
- Переключатель движения, который не управляет Lenis и GSAP сам: «Полное» не работает при системном reduce, «Меньше» не снимает скраб.
- Перелив «на весь экран» размытыми пятнами спектра — «радуга ИИ»; нужен узкий блик со структурой и окно тонов марки.
- Генераторы (K3, Claude): бегущая строка 155–164 px/с, свой курсор и плавная прокрутка «для вау» без сюжета, WebGL-«центр»
  без задачи, анимация свойств раскладки (у K3 13 из 13 работ, `kimi 05/03` §3.5), `transition: all` на всём.

## Чек-лист
- [ ] Эффект из `effects.yaml`, уровень страницы ≥ `level_min`, `limits` на странице соблюдены?
- [ ] Без JS контент виден; без поддержки — конечное состояние; без WebGL — CSS того же тона?
- [ ] Reduce: 0 % движения, 0 бесконечных анимаций, 0 вызовов WebGL, 0 байт видео (замер `rm`)?
- [ ] Каждая петля > 5 с — видимая пауза; вне экрана и в скрытой вкладке — стоп?
- [ ] Эффекты указателя — только `(hover: hover) and (pointer: fine)`; на телефоне — `mobile.behavior`?
- [ ] Библиотека грузится по условию; байты эффекта ≤ бюджета слоя «подача» A (L0 20, L1 100, L2 150/200 КБ br JS)?
- [ ] Главный поток сценария ≤ контроль + 25 мс/с на телефоне CPU ×4, CLS эффекта 0, LoAF 0 (замер `mob`)?
- [ ] Текст на эффекте — контраст AA (крупный ≥ 3 : 1) в худшем кадре; движение под читаемым текстом — нет?
- [ ] Клише: `cliche.registry_id` проверен по реестру H, поворот записан в `art-direction.decisions`?
- [ ] L2: есть переключатель «Движение» (3 состояния, помнится, побеждает ОС) и он останавливает WebGL, видео, GSAP и Lenis без перезагрузки?
- [ ] Закрепление — `sticky` (не `pin` через `position: fixed`); раскрытия по наведению и прокрутке — без изменения раскладки (CLS 0)?

## Открытые вопросы и противоречия
- Реальные телефоны, Safari и Firefox не проверены: эмуляция CPU ×4 без мобильного GPU; WebKit Playwright ≠ Safari; Firefox
  не ставился — поведение SDA-фолбэков в Firefox выведено из `@supports`, а не замерено `[не проверено]`.
- Порог главного потока «контроль + 25 мс/с» — предложение F для ворот K по нашей выборке; нужна калибровка на страницах C.
- `reduce.strategy: stations` и уровень `page-transition` — закрыто S1 2026-09-25: `stations` в схеме (перечисление treatment v1,
  `pin-scrub-story`, X-05); нативный кросс-документный VT — L1, библиотеки переходов — L2 (X-21).
- Hallmark: вход hero ≤ 220 мс и «аврора и mesh не проходят»; A/E: hero-сцены 600–1200 мс, шейдерный фон — «самый дешёвый
  вау». База держит A/E, Hallmark — `[мнение вендора]` для L0.
- Голо-шейдер F2 (решётка) не калибровался к Blender (ΔE); «материал продукта или радуга ИИ» — оценка F2 глазами, показ людям —
  живая фаза `[не проверено]`.
- Playwright-WebKit на Linux рисует без 3D-композитинга: `backface-visibility` не соблюдается даже у эталона (F2/16) — CSS-3D
  (переворот, наклон) в Safari проверяется только на iPhone `[проверено: ограничение среды]`.
- `pinType: 'transform'` убирает CLS, но возможное дрожание на нативной прокрутке документа замером rAF не видно — нужна запись экрана.

## Источники
- [S1] 3d-research `01-web-3d-landscape/01-effects-catalog.md` (агент A, 2026-09-22/23) — 70 эффектов, §5, §7.4, §9–§10,
  §14–§15, §18–§19, §22–§23 (прочитаны разделы). Надёжно: замер 33 сайтов + опыты A.
- [S2] 3d-research `09-web-runtime/04-shaders-effects-catalog-impl.md` §1–§2, §9–§10 и `03-scroll-interaction-animation.md`
  §3–§4, §7.2, §8 — шейдерный фон, CSS-зерно, SDA, reduce по приёмам (опыты F2, 2026-09-22).
- [S3] ai-media-research `10-web-integration/03-text-over-media-and-effects.md` §4–§5 (J, 2026-09-23) — прожектор, стыки, зерно,
  параллакс, 2.5D; `02-video-delivery.md` — видео (см. `02-hero-video-background.md`).
- [S4] creative C `03-live-sites-measured/01-effects-sites-measured.md` §4–§5, §9–§11, §13 и `02-motion-on-live-sites.md` §10
  (2026-09-24) — частоты эффектов на 49 страницах, скорости бегущей строки, reduce, хвост Lenis.
- [S5] creative A `01-creative-direction/03-ambition-levels.md` §3.1–§4.2, `drafts-for-site/treatment.v0.schema.json` — уровни,
  запреты, 29 временных id, перечисления reduce и mobile.
- [S6] creative E `05-motion/01-motion-principles-and-access.md` §4.2, §5.4 (черновик, 2026-09-24) и заметки «Для F» — поля движения.
- [S7] creative H `08-uniqueness-anti-slop/cliche-registry.yaml` v0.1 (53 записи, 2026-09-24) — `cliche.registry_id`.
- [S8] creative G `07-stack-implementation/stack.yaml` (2026-09-24) — `stack_ref`, версии библиотек.
- [S9] GSAP Standard "No Charge" License, gsap.com/standard-license (снимок 2026-09-24, ред. 2025-05-30) — лицензия `_vendor`.
- [S10] lenis README 1.3.26 (npm, 2026-09-18) — `respectReducedMotion`, `autoRaf`, `anchors` `[документация]`.
- [S11] Клоны внешних скиллов (`../kimi-research/99-raw/cache/repos/`): higgsfield `wow-catalog.md` (семейства A–D, контракты), taste
  `SKILL.md` §5, §10 (словарь, «marquee ≤ 1»), Hallmark `hero-enrichment.md` (Tier 0–E, HP2–HP3) — `[мнение вендора]`.
- [S12] creative W2 `99-raw/notes/wave2/W2-notes.md` «Для F» — кандидаты с таймкодами `[V:luAqYCd_TC8 14:30]`, `[V:ufHQG7fDLQc 13:41]`, `[V:xQnJLYTVl_E 24:06]`.
- [S13] Опыты F: `99-raw/experiments/F/01-pilot`, `02-trace-probe`, `03-batch-A`, `04-hero-video`, `05-batch-BG`, `06-unl`, `08-remeasure`.
- [S14] creative E, `99-raw/experiments/E/02-scroll-scene` (pin 1,6–2,0 CLS, `pinType: 'transform'` 0) и `E/03-motion-tokens` (токены в 5 состояниях).
- [S15] Дайджесты W1: `91-videos/digests/UcXWY057YuQ.md` (Bramus, Chrome I/O 2025: `@starting-style`, `interpolate-size`,
  `::details-content`, шапка по прокрутке), `_ZdZh-ESOHY.md` (Una Kravets: переворот и reduce-ветка, переключатель).
- [S16] Дайджест W2 `91-videos/digests/iqtCk5cY5Xs.md` (Прокопьев, HolyJS 2023: Lottie против Rive) и G `99-raw/experiments/G/01-lib-cost`.
- [S17] Опыты F2: `99-raw/experiments/F/11-wkmob`, `12-motion-toggle`, `13-unl`, `14-holo-look`, `15-hscroll-cls`, `16-micro`.
- [S18] Евгений (канал Вкалывают Роботы), «7 библиотек для красивых AI-приложений с вайб-кодингом», YouTube, 11 августа 2026, 8:56,
  https://www.youtube.com/watch?v=6XNhZu6mJlE — эффекты из китов Kokonut UI, React Bits, Magic UI для Claude Code; дайджест
  `../../claude-design-research/91-videos/digests/6XNhZu6mJlE.md`; один практик без замеров [мнение]. Дополнение 25.09.2026.
