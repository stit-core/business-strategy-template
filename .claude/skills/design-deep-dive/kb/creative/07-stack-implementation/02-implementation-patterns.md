# Паттерны реализации подачи: прогрессивное улучшение, reduce, ленивая инициализация, пауза, модуль эффекта, склейка библиотек, платформы

Волна 2 · агент G · 2026-09-24 · источников: 16 (из них целиком 12) · опыты: `99-raw/experiments/G/02-st-lenis-vt` (ScrollTrigger + Lenis +
View Transitions, 10 прогонов), `G/03-effect-module` (контракт модуля эффекта, 3 версии, 9 прогонов), `G/01-lib-cost` (веса) ·
стенд: Chromium 153.0.8010.12 и WebKit 26.6 (Playwright 1.63, headless) · gsap 3.15.0, lenis 1.3.26, @paper-design/shaders 0.0.81,
esbuild 0.25.12, vite 8.3.1. Выбор библиотек — `01-stack-choice.md`; нормы движения и reduce по приёмам — E (`../05-motion/`);
каталог и цена эффектов — F (`../06-effects-catalog/`).

## Выжимка для агента

1. **Смысл — в HTML, эффект — надстройка**: текст, цифры, CTA и навигация видны без JS и без анимации; скрывать до анимации
   можно только под классом `js` на `<html>` и только если есть путь «показать» → §1. [документация: site 07/01 §1.3; практика]
2. **LCP-элемент не анимируется из `opacity: 0`** и не ждёт шрифт/скрипт; появление первого экрана — CSS, не библиотека → §1.3.
   [документация: ai-media 10/01 §4.3]
3. **Проверка SDA** — `@supports ((animation-timeline: scroll()) and (animation-range: 0% 100%))` и внутри
   `@media (prefers-reduced-motion: no-preference)`; `animation-timeline` пишется после шортката `animation` → §1.2. [документация: S3]
4. **Reduce — ветка кода, а не `duration: 0` везде**: CSS — медиазапрос, GSAP — `gsap.matchMedia()` с условиями, Lenis — сам
   (`prefersReducedMotion`), VT — не запускать; модуль эффекта имеет `reduce()` с конечным состоянием → §2. [проверено]
5. **В reduce не грузить тяжёлое**: загрузчик выбирает режим до `import()` — в G/03 при reduce GSAP и шейдер не загружались
   (JS ≈ 2 КБ br против ≈ 35 КБ) → §2, §5. [проверено]
6. **Переключатель «меньше движения» на L2** (CRV-AL-12): атрибут `data-motion="reduced"` на `<html>` + те же ветки, что у
   медиазапроса; GSAP — `gsap.matchMediaRefresh()` → §2.2. [документация: S5; не проверено прогоном]
7. **Ленивая инициализация**: эффект ниже первого экрана — `IntersectionObserver` с `rootMargin: '200px 0px'` → в простое
   (`requestIdleCallback`, в Safari его нет — `setTimeout`) → `import()` модуля → §3. [проверено: G/03; документация: S1]
8. **Тяжёлая зависимость — только внутри `init()` и через прокладку**: `import('./paper-mesh.js')`, где прокладка делает
   `export { … } from '@paper-design/shaders'`; прямой `import('@paper-design/shaders')` дал 54 КБ br вместо 5,8 → §5.
   [проверено]
9. **Пауза**: непрерывное движение останавливается вне экрана (IO) и при `document.hidden`; петля дольше 5 с — видимая кнопка
   паузы (WCAG 2.2.2) → §4. [проверено: G/03 — пауза шейдера по IO; стандарт]
10. **Модуль эффекта** — объект `{ id, budget, supports(), init(el), reduce(el), mobile?(el), pause?(el), resume?(el), destroy(el) }`;
    `destroy` снимает всё: ScrollTrigger, split, canvas, pin-spacer, слушатели → §6. DOM-эффекты (33 эффекта каталога) свой
    модуль и загрузчик не пишут — их исполняет набор движения `motion-kit` (`../11-motion-code/`, модуль острова,
    `MotionKit.mount`); модуль и загрузчик — для того, чего набор не делает: GSAP-сюжет, шейдер, WebGL, Lottie, Rive.
    [проверено]
11. **`pagehide` без `persisted` → `destroy`**, при bfcache (`persisted: true`) — не разрушать → §6.2. [практика]
12. **Lenis + ScrollTrigger — один цикл**: `lenis.on('scroll', ScrollTrigger.update); gsap.ticker.add(t => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0)`; `scrollerProxy` для Lenis не нужен → §7.1. [проверено]
13. **После любой смены раскладки — `ScrollTrigger.refresh()`**: после same-document VT без refresh старт закрепления устарел в
    Chromium и WebKit; также после `document.fonts.ready` и догрузки медиа без размеров → §7.2. [проверено]
14. **Same-document VT при Lenis**: `lenis.stop()` → `startViewTransition` → `await t.finished` → `lenis.start()` →
    `ScrollTrigger.refresh()` → §7.2. [проверено: G/02 — без ошибок; визуально не оценивалось]
15. **Cross-document VT — одна строка CSS** и работает поверх Lenis + ScrollTrigger в Chromium и WebKit; при reduce не запускается,
    если правило внутри медиазапроса → §7.3. [проверено]
16. **SplitText**: после `document.fonts.ready`, `autoSplit: true` и анимация внутри `onSplit` (пересоздаётся при пересплите);
    `revert()` в `destroy` → §7.4. [проверено: G/03; документация: S4]
17. **SPA-переходы (Swup, Astro ClientRouter)**: на замене контента — `ctx.revert()` старых эффектов и `mount` новых; модульный
    скрипт Astro исполняется один раз — инициализация на `astro:page-load` → §7.5. [документация: S7, S8]
18. **Никаких CDN в сборке**: npm + свой домен; wasm dotLottie/Rive — `setWasmUrl()` на свой адрес, отдавать с brotli → §8.
    [проверено]
19. **Не вырезать лицензионные комментарии** (`legalComments` по умолчанию; не `'none'`) — GSAP требует сохранять уведомления → §8.
    [документация: S2]
20. **Шрифт — метрический фолбэк** (`size-adjust`, `ascent-override` или `next/font`/`fontaine`) и подмножества cyrillic + latin с ₽;
    SplitText и ScrollTrigger считаются после загрузки шрифтов → §9. [данные: D]
21. **Платформа определяет способ**: Тильда — T123 одним файлом/инлайн, WordPress — `wp_enqueue_script(… 'strategy' => 'defer')`,
    Битрикс — один файл `Asset::addJs` (порядок не гарантирован), Webflow — GSAP из настроек, Framer — Custom Code
    (проверять на опубликованном сайте) → §10. [документация: S9–S12]
22. **Проверка перед сдачей**: 0 ошибок консоли, JS слоя «подача» в бюджете уровня, reduce-прогон (0 GSAP-движения, 0 байт
    видео), телефонный прогон, `destroy` не оставляет ScrollTrigger → §11, чек-лист. [проверено: методика G/03]

## 1. Прогрессивное улучшение

### 1.1. Порядок слоёв

1. HTML сервера — весь смысл (H1, текст, цены, CTA, `<a href>`), картинки с размерами, постер вместо видео/WebGL.
2. CSS — раскладка, типографика, статичные фоны, CSS-движение под медиазапросом reduce.
3. Проверки возможностей — `@supports`, `CSS.supports()`, WebGL2, `matchMedia`.
4. JS эффектов — лениво, модулями (§5–6); ошибка модуля не ломает страницу (try/catch в загрузчике, контент уже видим).

### 1.2. Скрытое до анимации — только под `js` и только с выходом

```html
<!-- Chrome 153 · WebKit 26.6 · 2026-09-24 · [практика] класс js ставится до первой отрисовки -->
<script>document.documentElement.classList.add('js');</script>
<style>
  /* Без JS и в reduce всё видно. SDA — только где он полностью поддержан (проверка animation-range обязательна). */
  @media (prefers-reduced-motion: no-preference) {
    @supports ((animation-timeline: scroll()) and (animation-range: 0% 100%)) {
      .reveal { animation: reveal linear both; animation-timeline: view(); animation-range: entry 10% cover 30%; }
    }
    @supports not ((animation-timeline: scroll()) and (animation-range: 0% 100%)) {
      .js .reveal:not(.in) { opacity: 0; transform: translateY(24px); }      /* без SDA: IO-ветка ставит .in */
      .js .reveal { transition: opacity .6s ease, transform .6s cubic-bezier(.2,.7,.2,1); }
    }
  }
  @keyframes reveal { from { opacity: 0; transform: translateY(24px); } }
</style>
```
- IO-ветка для браузеров без SDA (Safari до 26, Firefox до 159) — наблюдатель по образцу загрузчика опыта G/03, ставящий `.in`;
  если скрипт упал, `.reveal` в таком браузере останется скрытым → в IO-ветке ставить таймер-предохранитель: через 3 с после
  `load` всем `.reveal` — `.in` [практика; не проверено].
- Декоративное (фоновые слои, параллакс) — без IO-ветки: в браузере без SDA просто статично [документация: S3].

### 1.3. Первый экран

- H1 и CTA — в HTML, видимы на первой отрисовке; появление hero — CSS 300–600 мс с `@starting-style` или `animation`
  по элементам, **кроме LCP-элемента** (LCP не из `opacity: 0`, `ai-media 10/01` §4.3) [документация].
- Никаких библиотек в критическом пути: `<script type="module">` откладывается сам, эффекты hero стартуют после `load` или по
  `requestIdleCallback`; шейдер/видео hero — постер в HTML (`fetchpriority="high"` у постера-LCP), живой слой — поверх после LCP
  (`3d 01/02` §4.1) [документация: соседи].

## 2. Reduce и «меньше движения»

Нормы — какие приёмы как смягчать — у E (`../05-motion/`); здесь только механика в коде.

### 2.1. Одна точка правды для режима

```js
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено] */
const mqReduce = matchMedia('(prefers-reduced-motion: reduce)');
const mqMobile = matchMedia('(pointer: coarse), (max-width: 767px)');
const userReduce = () => document.documentElement.dataset.motion === 'reduced';   // переключатель L2
export const modeNow = () => (mqReduce.matches || userReduce() ? 'reduce' : mqMobile.matches ? 'mobile' : 'full');
```
- CSS читает то же: `@media (prefers-reduced-motion: reduce)` и `[data-motion="reduced"]` (оба селектора в одном правиле).
- GSAP — сцены только в ветке `no-preference` через `gsap.matchMedia()` (при смене настройки созданное в ветке откатывается
  автоматически) [документация: S5]:
```js
/* GSAP 3.15.0 · 2026-09-24 · [проверено] при reduce ScrollTrigger не создаётся */
const mm = gsap.matchMedia();
mm.add({ motion: '(prefers-reduced-motion: no-preference)', reduce: '(prefers-reduced-motion: reduce)' }, (ctx) => {
  if (ctx.conditions.reduce) return;                       // конечные состояния — в CSS
  gsap.timeline({ scrollTrigger: { trigger: '#pin', start: 'top top', end: '+=1500', pin: true, scrub: true } })
    .to('#pin .track', { xPercent: -66, ease: 'none' });
});
```
- Lenis сам переходит на `lerp = 1` и мгновенные `scrollTo`; признак — `lenis.prefersReducedMotion` (опция `options.lerp` при этом
  остаётся 0,1) [проверено].
- View Transitions: same-document — `if (!document.startViewTransition || modeNow() === 'reduce') return change();`;
  cross-document — правило `@view-transition` внутри `@media (prefers-reduced-motion: no-preference)` [проверено].

### 2.2. Переключатель на странице (L2)

Кнопка ставит `data-motion="reduced"` на `<html>` (и `localStorage`), затем: `gsap.matchMediaRefresh()` для сцен GSAP (для
условия переключателя — `mm.add({ reduce: '(prefers-reduced-motion: reduce)' }, …)` дополнить проверкой `userReduce()` внутри
обработчика), загрузчик — `destroy` + `mount` в новом режиме, Lenis — `lenis.destroy()` (родная прокрутка) или создание заново,
видео — `pause()` и постер [документация: S5, S1; не проверено прогоном → «Что проверить», K].

## 3. Ленивая инициализация

```js
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено] */
const idle = (fn) => ('requestIdleCallback' in window ? requestIdleCallback(fn, { timeout: 1500 }) : setTimeout(fn, 200));
const io = new IntersectionObserver((entries) => {
  for (const e of entries) if (e.isIntersecting && !live.has(e.target)) idle(() => mount(e.target));
}, { rootMargin: '200px 0px' });
const start = () => document.querySelectorAll('[data-effect]').forEach((el) => io.observe(el));
document.readyState === 'complete' ? start() : addEventListener('load', start, { once: true });
```
- `requestIdleCallback` нет в Safari/iOS (BCD 8.1.3: только Technology Preview) — фолбэк обязателен [документация: S1].
- `scheduler.yield()` (Chrome 129, Firefox 142, нет Safari) — для длинной инициализации (разбить SplitText на порции); с проверкой
  `'scheduler' in window` [документация: S1].
- Эффект первого экрана не ждёт IO: `mount` в `idle` после `load`, но LCP к этому моменту уже отрисован HTML-ом.
- G/03: чанк ScrollTrigger (16,1 КБ br) загрузился только при подходе к закреплённой сцене; на старте — загрузчик 0,8 КБ,
  ядро GSAP 24,5, SplitText 3,1, шейдер 5,8 (hero) [проверено].

## 4. Пауза: вне экрана, скрытая вкладка, кнопка

| Что | Пауза | Возобновление | Где |
|---|---|---|---|
| CSS-петля (бегущая строка, градиент) | `el.style.setProperty('--play','paused')` при `animation-play-state: var(--play, running)` | `running`, если пользователь не нажал паузу | модуль marquee G/03 |
| шейдер paper-shaders | `mount.setSpeed(0)` | `setSpeed(v)` | G/03: вне экрана `speed = 0`, в экране 0,6 |
| свой WebGL-цикл | не вызывать `render`, `setAnimationLoop(null)` | вернуть цикл | `3d 09/03` §2.2 |
| видео | `video.pause()` | `play()` при видимости и без reduce | ai-media 10/* |
| lottie-web / dotLottie / Rive | `anim.pause()` / `dotLottie.pause()` / `rive.pause()` | `play()` | документация рантаймов |
| GSAP-таймлайн петли | `tl.pause()` | `tl.resume()` | — |

- Триггеры: IO (`isIntersecting`), `visibilitychange` (`document.hidden`) — оба в загрузчике G/03; кнопка паузы у любой петли
  дольше 5 с, идущей вместе с контентом (WCAG 2.2.2; нормы — E) [стандарт; проверено: G/03 — IO].
- `requestAnimationFrame` в скрытой вкладке браузер и так останавливает, но аудио, видео, таймеры и WebGL-работа в
  `setInterval` — нет → явная пауза [практика].

## 5. Код-сплиттинг и бюджет слоя «подача»

- Сборка: одна точка входа-загрузчик (≤ 1 КБ br) + чанки эффектов (esbuild `splitting: true` / Vite по умолчанию для `import()`).
- **Правило прокладки** (G/03): модуль эффекта не импортирует тяжёлое на верхнем уровне; внутри `init()` —
  `await import('./paper-mesh.js')`, а `paper-mesh.js` — `export { ShaderMount, meshGradientFragmentShader,
  getShaderColorFromString } from '@paper-design/shaders';`. Итог: 5,8 КБ br и только в режиме full; прямой
  `import('@paper-design/shaders')` — 54,0 КБ br (пакет целиком), статический импорт — чанк грузится и в reduce [проверено].
- Бюджет проверяется сборкой: сумма br чанков, которые грузятся до первого взаимодействия, ≤ `js_presentation_kb_br` уровня
  (20 / 100 / 150–200); отчёт — metafile esbuild или `vite build` + brotli; K включает в ворота [не проверено: предложение G → K].
- Замер G/03 (desktop, full): старт ≈ 35 КБ br (загрузчик, GSAP-ядро, SplitText, шейдер, модули), после прокрутки к сцене + 16,1;
  reduce — ≈ 2 КБ br [проверено].

## 6. Модуль эффекта

DOM-эффекты — появления, разбиение текста, счётчик, эффекты прокрутки и DOM-сцены, петли, указатель, микродвижение, переходы и
переключатель движения (33 эффекта, `../11-motion-code/primitives.yaml`, поле `effects`) — исполняет набор движения
`motion-kit` (`stack.yaml#motion-kit`): один скрипт без зависимостей и сети, `MotionKit.mount(root, opts)` с режимом,
паузой, `destroy` и реакцией на смену настройки; в коде сайта — модуль острова (`../11-motion-code/04-where-it-runs.md` §2), на
холсте — файл поддержки. Контракт модуля и загрузчик ниже — для того, чего набор не делает: GSAP-сюжет (сложный таймлайн,
Flip), шейдер, WebGL и 3D, Lottie, Rive; на странице с набором загрузчик ведёт только такие эффекты, а режим берёт тот же, что
набор (`data-motion`, §2.1).

### 6.1. Контракт

```ts
// TypeScript-описание · 2026-09-24 · [проверено: 99-raw/experiments/G/03-effect-module — реализация на JS]
export interface EffectBudget {
  js_kb_br: number;          // вклад модуля в слой «подача» (с зависимостями, которые грузит только он)
  wasm_kb_br?: number;       // dotLottie, Rive
  webgl_contexts?: 0 | 1 | 2;
  continuous?: boolean;      // бесконечное движение → нужна пауза (WCAG 2.2.2) и учёт в бюджете внимания (E)
}
export interface EffectModule {
  id: string;                               // effect:<id> из effects.yaml (F); у элемента — data-effect="<id>"
  budget: EffectBudget;
  supports(): boolean;                      // WebGL2, CSS.supports, API — иначе элемент остаётся в HTML-состоянии
  init(el: HTMLElement): void | Promise<void>;     // полная версия; тяжёлые зависимости — только здесь (§5)
  reduce(el: HTMLElement): void;            // конечное состояние или спокойная альтернатива (reduce, not remove)
  mobile?(el: HTMLElement): void;           // облегчённая версия (touch / < 768 px); нет — используется init
  pause?(el: HTMLElement): void;            // вне экрана, скрытая вкладка, кнопка
  resume?(el: HTMLElement): void;
  destroy(el: HTMLElement): void;           // снять всё: твины и ScrollTrigger (ctx.revert()), split.revert(), canvas, слушатели
}
```
Соответствие `treatment` (A, I): `effects[]` секции → элементы с `data-effect`; `reduce` и `mobile` из `treatment` → методы
`reduce()` и `mobile()`; `loop_control` → `pause()/resume()` и кнопка; `budget` → поле `budget` модуля [не проверено: предложение G → I].

### 6.2. Загрузчик (ядро, 0,8 КБ br)

```js
/* Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено] */
const REGISTRY = { 'pin-scrub-story': () => import('./effects/pin-scene.js'), 'shader-bg': () => import('./effects/shader-bg.js') };
const live = new Map();                                    // element → { mod, mode, visible }
async function mount(el) {
  const load = REGISTRY[el.dataset.effect]; if (!load || live.has(el)) return;
  const mode = modeNow();                                  // §2.1 — режим выбирается ДО загрузки тяжёлого
  const mod = (await load()).default;
  if (mode !== 'reduce' && mod.supports && !mod.supports()) { el.dataset.fx = 'unsupported'; return; }
  live.set(el, { mod, mode, visible: true });
  if (mode === 'reduce') mod.reduce(el); else if (mode === 'mobile' && mod.mobile) mod.mobile(el); else await mod.init(el);
  el.dataset.fx = mode;
}
function destroy(el) { const r = live.get(el); if (!r) return; r.mod.destroy(el); live.delete(el); delete el.dataset.fx; }
matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', () => { for (const el of [...live.keys()]) { destroy(el); mount(el); } });
document.addEventListener('visibilitychange', () => { for (const [el, r] of live) r.mod.pause && (document.hidden || !r.visible ? r.mod.pause(el) : r.mod.resume(el)); });
addEventListener('pagehide', (e) => { if (!e.persisted) for (const el of [...live.keys()]) destroy(el); });   // bfcache — не трогать
```

### 6.3. Пример модуля: закреплённая сцена

```js
/* GSAP 3.15.0 · Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено] */
let ctx = null;
export default {
  id: 'pin-scrub-story', budget: { js_kb_br: 40 },
  supports: () => true,
  async init(el) {
    const [{ gsap }, { ScrollTrigger }] = await Promise.all([import('gsap'), import('gsap/ScrollTrigger')]);
    gsap.registerPlugin(ScrollTrigger);
    ctx = gsap.context(() => {
      gsap.timeline({ scrollTrigger: { trigger: el, start: 'top top', end: '+=1200', pin: true, scrub: true } })
        .to(el.querySelector('.track'), { xPercent: -66, ease: 'none' });
    }, el);
  },
  mobile(el) { el.classList.add('stacked'); },   // телефон: кадры стопкой, без закрепления
  reduce(el) { el.classList.add('stacked'); },   // reduce: все кадры видны
  destroy(el) { ctx?.revert(); ctx = null; el.classList.remove('stacked'); },   // G/03: 0 ScrollTrigger, pin-spacer удалён
};
```
Результат G/03 (оба движка): desktop — сцена работает, чанк ScrollTrigger грузится при подходе; reduce и mobile — стопка кадров,
ScrollTrigger не создаётся; `destroy` — 0 ScrollTrigger, 0 обёрток SplitText, canvas и pin-spacer удалены [проверено].

## 7. Склейка: ScrollTrigger + Lenis + View Transitions + SplitText + переходы

### 7.1. Lenis + ScrollTrigger

```js
/* GSAP 3.15.0 · Lenis 1.3.26 · Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено] */
const lenis = new Lenis({ anchors: true });               // autoRaf: false — цикл общий с GSAP
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add((t) => lenis.raf(t * 1000));
gsap.ticker.lagSmoothing(0);
```
G/02: после 8 шагов колеса `scrollY` = `lenis.scroll` (3200 = 3200), закреплённая сцена отработала, якорь `#s5` — точно в цель
(оба движка). Не добавлять `ScrollTrigger.scrollerProxy` для Lenis (он на родной прокрутке; `gsap-skills` советует proxy для
сторонних скроллеров вообще) [проверено: G/02; S4].

### 7.2. Same-document View Transition, меняющий раскладку

```js
/* GSAP 3.15.0 · Lenis 1.3.26 · Chrome 153 · WebKit 26.6 · 2026-09-24 · [проверено] */
async function switchLayout(change) {
  if (!document.startViewTransition || modeNow() === 'reduce') { change(); ScrollTrigger.refresh(); return; }
  lenis?.stop();                                           // прокрутка не едет под снимком перехода
  const t = document.startViewTransition(change);
  try { await t.finished; } finally { lenis?.start(); ScrollTrigger.refresh(); }   // без refresh старт pin устаревает
}
```
G/02: без `refresh()` старт закрепления не совпал с новой раскладкой в Chromium и WebKit; с `refresh()` — совпал [проверено].
Также `ScrollTrigger.refresh()` после `document.fonts.ready` и после догрузки медиа без заданных размеров [практика; S4].

### 7.3. Cross-document View Transitions поверх всего

```css
/* Chrome 126+ · Safari 18.2+ · Firefox — нет (обычная навигация) · 2026-09-24 · [проверено] */
@media (prefers-reduced-motion: no-preference) { @view-transition { navigation: auto; } }
.site-logo { view-transition-name: logo; }  .page-title { view-transition-name: title; }   /* 1–3 общих элемента */
```
G/02: переход a → b шёл при работающих Lenis и ScrollTrigger (`pagereveal` → `e.viewTransition` есть) в Chromium 153 и WebKit
26.6; при reduce — не запускался. «Назад» перезагружал страницу (bfcache в headless не сработал), эффекты поднимались заново;
WebKit после «Назад» прокручивал к `#hash` из адреса, а не к сохранённой позиции [проверено].

### 7.4. SplitText

```js
/* GSAP 3.15.0 · 2026-09-24 · [проверено] */
await document.fonts.ready;                                // строки считаются по настоящему шрифту
const split = SplitText.create(el, { type: 'lines,words', mask: 'lines', autoSplit: true,
  onSplit: (self) => gsap.from(self.words, { yPercent: 110, stagger: 0.04, duration: 0.7, ease: 'power3.out' }) });
// destroy: split.revert()  — G/03: 0 обёрток после revert, aria-label на родителе ставит SplitText
```

### 7.5. Переходы с состоянием (Swup, Astro) и фреймворки

- Swup 4: на `content:replace` — `destroy` эффектов старой страницы, после — `mount` новой; плагин head (meta, стили) и a11y
  обязательны; `native: true` отдаёт анимацию VT [документация: S7].
- Astro `<ClientRouter />`: модульный скрипт исполняется один раз → `document.addEventListener('astro:page-load', mountAll)` и
  `astro:before-swap` → `destroyAll`; ClientRouter сам выключает VT-анимации при reduce [документация: S8].
- React/Next: `useGSAP()` из `@gsap/react` (очистка по размонтированию) или `gsap.context()` в `useLayoutEffect`; прокрутка → ref,
  не состояние React (`3d 09/03` §2) [документация: S4].

## 8. Самохостинг и лицензии в сборке

```js
/* dotLottie-web 0.80.0 · Rive 2.43.1 · 2026-09-24 · [проверено] по умолчанию — jsDelivr/unpkg */
import { DotLottie } from '@lottiefiles/dotlottie-web';
import { RuntimeLoader } from '@rive-app/canvas-lite';
DotLottie.setWasmUrl(new URL('/wasm/dotlottie-player.wasm', location.origin).href);   // файл копируется из node_modules при сборке
RuntimeLoader.setWasmUrl(new URL('/wasm/rive.wasm', location.origin).href);
```
- Wasm отдавать с `Content-Type: application/wasm` и brotli (Rive советует) [документация: S6].
- Worker dotLottie (`DotLottieWorker`) под CSP — `setWorkerUrl()` на свой домен (dotlottie-web 0.81) [документация: README пакета].
- Версии фиксировать (`"gsap": "3.15.0"`, без `^`, или lock-файл); `npm view <пакет> version dist-tags` перед сборкой.
- Лицензии: esbuild — не ставить `legalComments: 'none'`; Terser — не `comments: false`; GSAP-уведомление `/*! … @license … */`
  остаётся в бандле [документация: S2].
- Никаких `<script src="https://cdn…">` и `@import url(https://fonts…)` в сборке (kimi `07/02` §8.1); исключение — платформы без
  сборки (Тильда, Webflow, Framer), где скрипт берётся с домена платформы или своего поддомена (§10).

## 9. Шрифты для движения текста

- Метрический фолбэк: `@font-face { font-family: 'Display Fallback'; src: local('Arial'); size-adjust: …; ascent-override: …;
  descent-override: …; line-gap-override: …; }` по метрикам k_ru; автоматически — `next/font` (Next) или `fontaine` 1.0.0
  (Vite/Nuxt, 2026-09-21); у D подогнанный фолбэк дал CLS 0 в 8 из 8 [данные: D `../04-visual-language/`].
- Подмножества cyrillic + latin (+ ₽ U+20BD) в WOFF2, самохостинг `@fontsource/<id>@5` (kimi) [документация: соседи].
- SplitText, ScrollTrigger и замеры строк — после `document.fonts.ready` (§7.4); `autoSplit` пересплитывает при подмене шрифта.
- Вариативная ось в анимации (`wght`, `wdth`) меняет ширину строк → переносы и CLS; анимировать ось только у элемента с
  фиксированной шириной строки или у одиночного слова [практика; цену меряет F]. В `@keyframes` с `font-variation-settings`
  перечислять **все** оси в каждом кадре (неуказанные сбрасываются), теги осей брать из файла шрифта `[V:luAqYCd_TC8 11:14]`.

## 10. Платформенные рецепты

```html
<!-- Тильда · блок T123 (HTML) · 2026-09-24 · [документация: S9; не проверено на опубликованной странице] -->
<style>
  @media (prefers-reduced-motion: no-preference) {
    @supports ((animation-timeline: scroll()) and (animation-range: 0% 100%)) {
      .t-rec .reveal-me { animation: fx-reveal linear both; animation-timeline: view(); animation-range: entry 10% cover 30%; }
    }
  }
  @keyframes fx-reveal { from { opacity: 0; transform: translateY(24px); } }
</style>
<script src="/files/fx-bundle.js" defer></script>   <!-- один собранный файл на своём хостинге; не CDN библиотек -->
```
- Тильда: свои классы — на элементах Zero Block (поле CSS class name) или в T123; код работает только после публикации; анимацию
  Zero на телефоне включать явно; собственные скрипты Тильды на странице — вне нашего бюджета, но в весе страницы [документация: S9].

```php
<?php // WordPress 6.9 · functions.php темы · 2026-09-24 · [документация: S10]
add_action('wp_enqueue_scripts', function () {
  wp_enqueue_script_module('site-fx', get_theme_file_uri('dist/fx.js'), [], '1.0.0', ['in_footer' => true]); // ES-модуль (6.5+)
  // классический скрипт: wp_enqueue_script('site-fx', …, [], '1.0.0', ['strategy' => 'defer', 'in_footer' => true]); (6.3+)
});
```

```php
<?php // 1С-Битрикс · header.php шаблона · main 14.9.4+ · 2026-09-24 · [документация: S11]
use Bitrix\Main\Page\Asset;
// addJs не гарантирует порядок — GSAP, плагины и эффекты собраны в ОДИН файл:
Asset::getInstance()->addString('<script type="module" src="' . SITE_TEMPLATE_PATH . '/dist/fx.js"></script>');
```

- Webflow: Site settings → GSAP integration (ядро и плагины галочками, хостит Webflow); свой код (≤ 50 000 символов, платный план) —
  в Page settings «Before </body>»: `gsap.registerPlugin(ScrollTrigger)` и сцены; Lenis — отдельным внешним файлом [документация: S12].
- Framer: Site Settings → Custom Code (конец body) или код-компонент; проверять на опубликованном сайте — в холсте код не
  исполняется [документация: S13].

## 11. Типовые ошибки исполнителей (K3, Claude, генераторы)

1. Контент с `opacity: 0` в CSS и анимация «из невидимого» без JS-ветки — в браузере без SDA (Safari до 26, Firefox до 159) и
   при ошибке скрипта текста нет.
2. LCP-заголовок в SplitText с `from({ opacity: 0 })` — LCP сдвигается на время анимации.
3. `@supports (animation-timeline: scroll())` без `animation-range`; `animation` шорткат после `animation-timeline`.
4. `duration: 0` вместо reduce-ветки — GSAP, шейдер и видео всё равно грузятся и работают.
5. Статический импорт тяжёлой зависимости в модуле эффекта; `import('пакет')` целиком вместо прокладки (54 против 5,8 КБ br).
6. Нет `destroy`: при SPA-переходе или HMR копятся ScrollTrigger и pin-spacer; нет `ScrollTrigger.refresh()` после смены раскладки.
7. `scrollerProxy` для Lenis; два цикла rAF (Lenis `autoRaf: true` и `gsap.ticker`); Lenis без `anchors: true`.
8. Петля без паузы и без остановки вне экрана; WebGL рисует в покое и в скрытой вкладке.
9. `requestIdleCallback` без фолбэка — в Safari эффект не стартует.
10. Wasm с CDN по умолчанию (dotLottie, Rive); `<script src="https://unpkg…@latest">` из документации вендора.
11. `legalComments: 'none'` при GSAP; версии «по памяти» (`gsap-trial`, `@studio-freight/lenis`, SplitText `position: "absolute"`).
12. Битрикс — несколько `addJs` с GSAP и плагинами; Webflow — собранный GSAP в Code Embed; Тильда — проверка кода в редакторе, а не
    на опубликованной странице.

## Чек-лист

- [ ] Без JS и без SDA (старые версии) весь смысл страницы видим; скрытое до анимации — только под `.js` и с предохранителем?
- [ ] LCP-элемент не анимируется из `opacity: 0`, эффекты hero стартуют после `load`/в простое?
- [ ] SDA под полной проверкой `@supports` и медиазапросом reduce; `animation-timeline` после шортката?
- [ ] Режим (`full | mobile | reduce`) выбирается до загрузки тяжёлых зависимостей; в reduce GSAP/шейдер/видео не грузятся?
- [ ] У каждой петли есть пауза вне экрана и при скрытой вкладке, у петли > 5 с — видимая кнопка?
- [ ] У каждого эффекта — модуль с `init`, `reduce`, `destroy` (и `mobile`, `pause`, если нужно) и полем `budget`?
- [ ] Тяжёлое — внутри `init()` через прокладку с именованным ре-экспортом; сумма br до первого взаимодействия ≤ бюджета уровня?
- [ ] Lenis + ScrollTrigger — один цикл, `anchors: true`, без `scrollerProxy`; `ScrollTrigger.refresh()` после VT, шрифтов, медиа?
- [ ] Cross-document VT — одной строкой CSS внутри медиазапроса; same-document — с остановкой Lenis и refresh?
- [ ] SplitText — после `document.fonts.ready`, `autoSplit`, `revert()` в `destroy`?
- [ ] Wasm и шрифты — со своего домена, версии зафиксированы, лицензионные комментарии в бандле?
- [ ] Способ подключения соответствует `constraints.cms` и проверен на опубликованной странице (Тильда, Webflow, Framer)?

## Открытые вопросы и противоречия

1. **Переключатель «меньше движения» (L2)** и смена reduce «на лету» — обработчики написаны, прогона нет (K: сценарий в
   `motion_check.py`).
2. **`visibilitychange`** в headless не эмулировался; пауза при скрытой вкладке проверена только чтением кода.
3. **bfcache**: в headless «Назад» перезагружал страницу (`persisted: false`); поведение эффектов при восстановлении из bfcache
   на реальном браузере не проверено.
4. **Визуальная разница** «Lenis остановлен / не остановлен на время VT» не оценивалась (запись — K).
5. **IO-предохранитель** для `.reveal` в браузерах без SDA — практика, не прогон: Chromium 153 и WebKit 26 стенда SDA
   поддерживают, Firefox в Playwright не установлен (решение заказчика 13 разрешает поставить).
6. **Платформенные рецепты** (Тильда, Webflow, Framer, Битрикс) не проверены на живых аккаунтах — вход в сервисы запрещён; только
   документация.

## Источники

- [S1] MDN browser-compat-data 8.1.3 (2026-09-24) и web-features 3.39.0 — `99-raw/experiments/G/00-registry/support.json`. Надёжно.
- [S2] Webflow, «Standard "No Charge" GSAP License», gsap.com/community/standard-license (eff. 2025-04-30, ред. 2025-05-30), разд. III. Надёжно.
- [S3] GoogleChrome/modern-web-guidance 0.0.190: `guides/ui-behaviors/scrollytelling.md`, `cross-document-transitions.md`
  (клон `../../kimi-research/99-raw/cache/repos/GoogleChrome__modern-web-guidance/`). Официальный скилл Chrome.
- [S4] greensock/gsap-skills (aed9cfd, 2026-04-21, MIT): `gsap-core` («Accessibility and responsive»), `gsap-scrolltrigger`,
  `gsap-performance`, `gsap-react` — клон `99-raw/cache/repos/greensock__gsap-skills/`. Вендор.
- [S5] gsap-skills `gsap-core` §gsap.matchMedia (условия, `matchMediaRefresh`); документация gsap.matchMedia (кэш
  `99-raw/cache/gsap.com_docs_v3_GSAP_gsap.matchMedia__*.md`). Вендор.
- [S6] Rive, «Web (JS) — Getting started», rive.app/docs/runtimes/web/web-js; README @rive-app/canvas 2.43.1; README dotlottie-web 0.80.0. Вендоры.
- [S7] swup.js.org — options (`native`), getting started (плагины head, a11y). Документация.
- [S8] Astro, «View transitions» — script re-execution, lifecycle events, reduce, fallback. Документация.
- [S9] Тильда: tilda.cc/ru/answers/a/html, help-ru.tilda.ws/html, help-ru.tilda.cc/zero/advanced-animation, answers/a/mobile-animation. Вендор.
- [S10] WordPress: developer.wordpress.org `wp_enqueue_script_module()` (6.5, `$args` 6.9); make.wordpress.org/core 2023-07-14 (strategy, 6.3). Документация.
- [S11] 1С-Битрикс: dev.1c-bitrix.ru API D7 `Asset::addJs` (14.9.4, порядок не гарантирован). Документация.
- [S12] Webflow Updates: «Webflow makes GSAP 100% free» (2025-04-30), «Increased custom code character limit» (2024-05-07). Вендор.
- [S13] Framer Academy «Add Custom Code…», Framer Developers «Custom Code». Вендор.
- [S14] Lenis README (main, 2026-09-24): anchors, prevent, reduced motion, ограничения. Документация.
- [S15] Соседи: `3d 09/03` §2 (цикл кадра, рендер по требованию), `3d 01/02` §4.1 (порядок загрузки hero),
  `ai-media 10/01` §4.3 (LCP не из opacity 0), `kimi 07/02` §8.1 (CDN запрещены); D — `../04-visual-language/` (метрический фолбэк).
- [S16] Опыты G/01, G/02, G/03 — `99-raw/experiments/G/` (README в каждой папке).
