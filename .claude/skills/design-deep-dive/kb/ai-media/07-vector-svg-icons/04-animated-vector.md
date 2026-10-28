# Анимированный вектор: SVG + CSS, SMIL, Lottie, Rive и когда видео-модель лишняя

Волна 2 · агент G · 23.09.2026 · опыт G/05 (Chromium из Playwright: CSS/SMIL inline и в `<img>`, Lottie, 4 режима
reduce × тема; веса плееров lottie-web 5.13.0 и dotlottie-web 0.80.0) · ролики: 6 (LottieFiles, Rive, ИИ-маскот,
лоадер через видео, HeroUI/Gemini) · правила движения иконок — `../../ui/07-iconography-imagery/01-icons.md` §6.4,
доступность движения — `../../ux/08-accessibility/`.

## Выжимка для агента

1. **Иконки и лоадеры — inline SVG + CSS `@keyframes`**: 0 байт плеера, файл 0,3–0,5 КБ; блок
   `@media (prefers-reduced-motion: reduce){animation:none}` останавливает анимацию. → §2 [проверено]
2. **SMIL (`<animate>`, `<animateTransform>`) настройку reduce не слушает** — крутится при `reduce`; если SMIL
   нужен — `svg.pauseAnimations()` по `matchMedia`. → §2, §3 [проверено]
3. **Анимированный SVG через `<img>` крутится (и CSS, и SMIL), но `prefers-reduced-motion` внутри не срабатывает**
   (а `prefers-color-scheme` в `<img>` срабатывает) → статичный запасной файл через `<picture>`. → §2, §3 [проверено: G/05, Chromium]
4. **Lottie — только для сложного движения** (персонаж, морфинг, десятки слоёв): плеер lottie-web light 168 КБ
   (46 КБ gzip), полный 306 КБ (76 КБ gzip); dotLottie — 165 КБ JS + 1,24 МБ WASM (33 + 496 КБ gzip). → §1 [проверено: G/05, npm 23.09.2026]
5. **lottie-web reduce не слушает** — `matchMedia('(prefers-reduced-motion: reduce)')` → `anim.goToAndStop(кадр, true)`. → §3 [проверено]
6. **Анимировать иконку — только когда меняется смысл**: гамбургер → крестик 200 мс, шеврон 150–200 мс, галочка
   150 мс, спиннер 1 с линейно; не «подпрыгивание» и не покачивание. → §4 [система, ui 07/01 §6.4]
7. **LLM пишет простой Lottie вручную**: спиннер 809 байт (дуга с trim 0–75 %, штрих 2, поворот 360° за 30 кадров)
   загрузился в lottie-web 5.13 и крутится с первого раза. → §5 [проверено: G/05, n = 1]
8. **CSS-анимацию иконки LLM пишет надёжнее Lottie** — меньше полей и типов, проверяется рендером; Lottie — когда нужен
   экспорт в дизайн-инструмент или плеер уже на странице. → §5 [практика]
9. **Видео-модель для движения иконки избыточна**: очередь до ≈ 2 ч на одну анимацию, случайный результат, «высасыватель
   денег» (лоадер в Krea) [V:i5n8ysDXAr0 08:16, 36:54]; у GIF альфа 1-битная; API Sora 2 закрывается 24.09.2026. → §6 [мнение + факт]
10. **Видео оправдано для персонажа-маскота и «материальной» 3D-иконки**: хромакей-фон → i2v (промт «idle animation…
    slightly in a loop») → кеинг → WebM/GIF; все состояния — из одной исходной картинки; предзагрузка. → §6 [V:gi-y_O5v1FQ 03:04–09:09] [практика]
11. **Rive** — для интерактивных персонажей с состояниями: меш с минимумом вершин, именованные кости, петля 2 с;
    вес `.riv` и рантайма в роликах не назван — мерить перед выбором. → §1 [V:dxjQe6WOok8] [практика; вес не проверен]
12. **Цепочка «промт → вектор → Lottie» (LottieFiles)**: вектор «vector friendly» (минимум узлов), Smart Grouping слоёв
    для анимации, траекторию задавать явно; вендор сам оценивает результат как «80 % работы». → §5 [V:wzA5q75-PKc 06:07, 18:31, 24:41] [мнение вендора]
13. **Автоповтор, который вместе длится дольше 5 с, — кнопка паузы или остановка ≤ 5 с** (WCAG 2.2.2: считается длительность
    движения, а не клипа — бесконечная петля 2 с тоже подпадает; `../10-web-integration/02-video-delivery.md` §5); вспышки ≤ 3
    в секунду (2.3.1). → §4 [документация WCAG; ux-research] [поправка X 24.09.2026: было «петли дольше 5 с»]
14. **Анимировать `transform` и `opacity`** (и `stroke-dashoffset` у маленьких иконок); `transform-origin` задавать
    в px viewBox (`12px 12px`), иначе вращение уезжает. → §3 [практика; проверено: G/05]

## 1. Выбор способа

| Способ | Вес | Плеер | `prefers-reduced-motion` | Когда |
|---|---|---|---|---|
| inline SVG + CSS | 0,3–0,5 КБ на иконку | нет | работает (`@media` в `<style>` или CSS страницы) [проверено] | иконки, лоадеры, draw-on, гамбургер → крестик |
| inline SVG + SMIL | 0,3 КБ | нет | **не работает** [проверено]; нужен JS | морфинг `d` между путями с одинаковым числом узлов, если CSS не хватает |
| SVG через `<img>` (CSS или SMIL внутри) | как файл | нет | **не работает внутри** [проверено]; менять файл через `<picture>` | декоративная анимация вне интерфейса |
| Lottie (lottie-web) | JSON 1–50 КБ + плеер 46–76 КБ gzip | JS | не работает, нужен JS [проверено] | сложная моушн-графика, персонажи, экспорт из After Effects/Lottie Creator |
| dotLottie (dotlottie-web) | `.lottie` (zip) + 33 КБ JS + 496 КБ WASM gzip | JS + WASM | своим кодом | много анимаций на сайте, state machines |
| Rive | `.riv` + рантайм (не мерили) | JS/WASM | своим кодом | интерактивный персонаж, состояния |
| Видео (WebM/MP4/GIF) | сотни КБ и больше | `<video>` | `<video>` не играть при reduce (ux-research) | фотореалистичный или «материальный» маскот |

## 2. Что проверено в Chromium (G/05)

Средняя разница пикселей ячейки между кадрами через 230 мс (0 — стоит):

| Способ | no-preference | reduce |
|---|---|---|
| inline, CSS + `@media reduce` | 17,0 | **0** |
| inline, SMIL | 16,8 | 16,4 |
| `<img>`, CSS внутри | 18,1 | 18,1 |
| `<img>`, SMIL внутри | 18,5 | 18,2 |
| Lottie (lottie-web 5.13, svg-рендер) | 21,0 | 20,9 |

- `document.getAnimations()`: 2 при no-preference, 0 при reduce — SMIL и Lottie в этот список не попадают, проверять
  «всё ли остановилось» только снимками.
- Тёмная тема внутри SVG в `<img>` сработала (фавикон G/04 потемнел), reduce — нет: два медиазапроса ведут себя
  по-разному в одном и том же `<img>`.

## 3. Код

```html
<!-- inline SVG + CSS · [проверено: 99-raw/experiments/G/05-animated-vector/spinner-css.svg, 387 байт] -->
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
  role="img" aria-label="Загрузка">
  <style>.s{transform-origin:12px 12px;animation:r 1s linear infinite}@keyframes r{to{transform:rotate(360deg)}}
  @media (prefers-reduced-motion:reduce){.s{animation:none}}</style>
  <path class="s" d="M21 12a9 9 0 1 1-6.2-8.56"/></svg>
```

```html
<!-- draw-on галочки · [проверено: check-draw.svg, 472 байта; финальное состояние при reduce] -->
<style>.c{stroke-dasharray:16;stroke-dashoffset:16;animation:d .6s ease-out .1s forwards}@keyframes d{to{stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){.c{animation:none;stroke-dashoffset:0}}</style>
```

```html
<!-- SVG-анимация через <img>: статичная копия для reduce · [практика; необходимость проверена в G/05] -->
<picture><source srcset="/img/hero-anim-static.svg" media="(prefers-reduced-motion: reduce)">
  <img src="/img/hero-anim.svg" alt="" width="320" height="240"></picture>
```

```js
// SMIL и Lottie: остановка по настройке · [практика; что сами не останавливаются — проверено G/05]
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const apply = () => {
  document.querySelectorAll('svg.smil').forEach(s => reduce.matches ? s.pauseAnimations() : s.unpauseAnimations());
  if (window.anim) reduce.matches ? anim.goToAndStop(anim.totalFrames - 1, true) : anim.play();
};
reduce.addEventListener('change', apply); apply();
```

## 4. Движение по нормам

- Длительности и что анимировать — ui 07/01 §6.4 и `../../ui/08-motion/`: смена смысла 150–200 мс, спиннер
  1 с `linear`, «обновить» 500–700 мс один оборот; модель SF Symbols: однократная анимация — событие, непрерывная —
  процесс.
- Декоративные петли в hero с автоповтором дольше 5 с в сумме (любая бесконечная петля) — пауза или стоп ≤ 5 с (WCAG 2.2.2, J `../10-web-integration/02-video-delivery.md` §5) [поправка X 24.09.2026]; у лидеров она есть у 1 из 33 длинных петель (A §4) —
  делать правильно.
- Размер: анимированная иконка ≤ 24 px в интерфейсе и ≤ 96 px в маркетинге; больше — это иллюстрация (ui 07/02 §4.2).

## 5. Генерация анимации нейросетью

- **CSS-анимация кодом** — тот же конвейер, что у иконок (`01-svg-by-llm.md`): спецификация + проверка рендером.
  LLM-агент сам пишет `@keyframes`, `transform-origin` и блок reduce; проверка — снимки в браузере при no-preference и
  reduce (скрипт `99-raw/experiments/G/05-animated-vector/run_browser.py`, под `browser.lock`).
- **Lottie вручную**: минимальный валидный файл — `v`, `fr`, `ip`, `op`, `w`, `h`, `layers[]` со слоем `ty: 4`,
  `ks` (трансформации с ключами `{"t","s","i","o"}`) и `shapes` (`gr` → `el`/`sh`, `tm`, `st`/`fl`, `tr`). Спиннер 809 байт
  заработал с первого раза; сложные сцены вручную не писать — проверка только рендером.
- **LottieFiles Prompt to Vector / Motion Copilot** — «промт → вектор → Lottie» внутри Figma и Lottie Creator; удачный
  промт от LLM фиксировать и менять только объект; «No gradients, no realistic shading» [V:wzA5q75-PKc 07:09–08:11].
  Агент работает в редакторе через Lottie Creator MCP — локальный мост `@lottiefiles/creator-mcp` к открытой вкладке
  редактора (с 2026-04-15) — и WebMCP; публичного API генерации нет, поэтому это инструмент на аккаунте заказчика, а не
  ключ системы. ИИ расходует AI-кредиты тарифа; коммерческая страница — с тарифа Team или Enterprise (Free и Individual —
  только некоммерческое использование). Результат — черновик «допущением»: показ владельцу продукта, затем план ассетов
  [S7] [документация].
- **HeroUI Studio и Gemini Canvas** генерируют анимированный SVG; утверждение «работает только inline» — неверно для
  проигрывания (в `<img>` крутится), верно для reduce [V:UWseAJ5Vb58] + G/05.
- **OmniLottie** (открытые веса 4B, 15 ГБ GPU; fal `image-to-lottie` $0,10) — только обзор: ключа fal нет, лицензия
  базы Qwen2.5-VL-3B спорна (`../02-providers-platforms/05-open-weights-landscape.md` §7.2).

## 6. Видео вместо вектора: когда да

| Да | Нет |
|---|---|
| маскот с мимикой и телом, «живой» персонаж онбординга | лоадер, галочка, шеврон, гамбургер |
| 3D-«материальная» иконка (стекло, пластик) в маркетинге | иконки интерфейса любого размера |
| один ролик на экран, есть бюджет на кеинг и вес | десятки анимаций на странице |

- Конвейер маскота: фон — сплошной хромакей, персонаж по центру снизу в одной позиции для всех состояний; i2v с
  промтом «idle animation… moving slightly in a loop» (без второй части модель двигает камеру); кеинг; 4 состояния из
  одной исходной картинки [V:gi-y_O5v1FQ 03:04–08:07]. Модели и петли — агент I (`../09-video-pipeline/`).
- Видео-модель для лоадера у практика: 2 ч ожидания на одну анимацию, первый рендер крутил весь предмет вместо колеса
  [V:i5n8ysDXAr0 08:16, 25:40] [мнение].

## Частые ошибки

1. SMIL или анимированный `<img>` без запасного пути для reduce.
2. Lottie-плеер (46–500 КБ gzip) ради спиннера на 0,4 КБ CSS.
3. `transform-origin` не задан — иконка вращается вокруг угла.
4. Бесконечное покачивание и «прыжки» иконок уведомлений.
5. Видео-модель для лоадера: часы очереди, альфа 1 бит в GIF, звук в дорожке.
6. Ошибки агентов «по памяти»: «prefers-reduced-motion выключает любую анимацию» (SMIL, `<img>` и Lottie — нет);
   плеер Lottie (`lottie-web`, `@lottiefiles/lottie-player` 2.0.12, `dotlottie-web`) без своей остановки по reduce;
   Sora 2 как маршрут.

## Чек-лист

- [ ] Анимация иконки меняет смысл и длится ≤ 200 мс (спиннер — 1 с линейно)?
- [ ] Inline SVG + CSS с блоком `prefers-reduced-motion`?
- [ ] Для SMIL, `<img>` и Lottie есть остановка по reduce (JS или `<picture>`)?
- [ ] Плеер Lottie/Rive оправдан сложностью движения; его вес учтён в бюджете страницы?
- [ ] Автоповтор дольше 5 с в сумме (бесконечная петля любой длины) — с паузой или остановкой ≤ 5 с?
- [ ] Остановка проверена снимками в браузере при reduce?

## Открытые вопросы и противоречия

1. Вес рантайма Rive и `.riv` для типового персонажа — не мерили.
2. Поведение reduce внутри SVG в `<img>` проверено только в Chromium из Playwright; Safari и Firefox — нет.
3. Качество LLM-Lottie на сложном движении (морфинг, несколько слоёв) — не проверено; простой спиннер — работает.
4. Видео против Lottie для маскота по весу при одинаковом качестве — чисел нет ни в одном ролике.

## Источники

- [S1] Опыт G/05 (`99-raw/experiments/G/05-animated-vector/`: `browser-results.json`, README) — все числа §1–§2.
- [S2] lottie-web 5.13.0, @lottiefiles/dotlottie-web 0.80.0 — пакеты npm, 23.09.2026; вес файлов сборки измерен.
- [S3] ui-research `07-iconography-imagery/01-icons.md` §6.4 (длительности анимации иконок).
- [S4] Дайджест роликов помощника G: `wzA5q75-PKc` (LottieFiles), `gi-y_O5v1FQ` (ИИ вместо Lottie), `dxjQe6WOok8` (Rive), `i5n8ysDXAr0` (лоадер через видео), `UWseAJ5Vb58` (HeroUI + Gemini) — `99-raw/notes/wave2/G-notes.md`.
- [S5] `../02-providers-platforms/05-open-weights-landscape.md` §7.2 (OmniLottie) — агент P.
- [S6] Отчёт агента A волны 1, §4 (пауза у 1 из 33 длинных петель) — `99-raw/reports/wave1-A-report.md`.
- [S7] LottieFiles: https://docs.lottiefiles.com/en/creator/13_ai-tools (обновлено 2026-10-08), …/motion-copilot,
  …/lottie-creator-mcp, …/lottie-creator-webmcp; https://lottiefiles.com/pricing; https://lottiefiles.com/page/terms-and-conditions
  (Last Modified 22nd August 2025) — снято 2026-10-28, через `../../creative/02-references-moodboards/04-motion-libraries-and-rules.md`
  §5 [S48].
