# 11 · Шейдерный фон без Blender: mesh gradient, «лента» Stripe, Paper Shaders

Волна 3 · агент K · 23.09.2026 · three r186, @paper-design/shaders 0.0.81, Chromium · сборка из готового демо F2 (без Blender):
страница — копия `../09-web-runtime/examples/shader-background/` [проверено: F2/04; повторный прогон — 99-raw/experiments/K/10-shader-page]
· пример: `examples/11-shader-background/`

## Выжимка рецепта

1. Фон и настроение без предмета — **шейдер, не Blender**: 1 полноэкранный треугольник/плоскость, **1 вызов, ≈ 1,5 мс на кадр**,
   0 байт ассетов; Blender здесь не нужен (25 из 70 эффектов каталога A — без Blender, A `01/01 §23`) [проверено: F2/04, этот прогон].
2. Цвета бренда — hex → `THREE.Color` (хранит **линейные** значения) → в фрагментном шейдере `#include <colorspace_fragment>`;
   без него ΔE2000 9,55 (#ff6a3d → rgb(255, 37, 12)); `renderer.toneMapping = NoToneMapping` — hex бренда = пиксель [проверено].
3. Размытый фон — DPR ≤ 1 (чёткость ему не нужна); фон с деталью 1–2 px (точки, линии, решётки) — плотность как у объекта,
   бюджетом пикселей холста (`../16-js-scenes/01-engine.md` §6); полноэкранный SDF без ограничивающего объёма — в ½
   разрешения (× 6,6 дешевле) [проверено].
4. Цикл — только при видимости героя, открытой вкладке и без reduce; reduce → **один кадр, 0 вызовов в покое**; CSS-градиент под
   canvas — запас без WebGL [проверено].
5. Варианты: `gradient` (фрагментный fbm с деформацией домена, 4 цвета), `ribbon` (как у Stripe: деформация в вершинном шейдере сетки
   128 × 128), `paper` (`@paper-design/shaders`, 119 КБ JS, свой контекст, рендерит минимум при DPR 2) [проверено: F2/04, W7 `LW9d2cqIHb4`].
6. Чужой код с Shadertoy не копировать: лицензия по умолчанию CC BY-NC-SA 3.0 [практика: W7, PLAN 13:31].

## 1. Бриф-пример и границы

«Финтех-лендинг: живой градиент в фирменных цветах за заголовком, как у Stripe; быстро на телефоне; без 3D-модели».

| годится | не годится → куда |
|---|---|
| фон, настроение, бренд-цвета, «жидкий» градиент | нужен предмет/продукт → рецепты 01, 04 |
| бюджет JS ≤ 120–360 КБ, 1 вызов | нужна глубина и свет по форме → абстрактная скульптура (рецепт 04) |
| есть запас CSS-градиентом | «шейдер ради шейдера» на каждой секции — клише 2023–2025 (A `01/01 §22`) |

## 2. Паспорт

Палитра — 4 hex бренда (`PALETTE`), скорость 0,6 (reduce → 0), DPR ≤ 1 (фон размытый; с деталью 1–2 px — п.3),
`NoToneMapping`; текст и кнопка — HTML поверх canvas
(`aria-hidden`); высота героя 100vh; запас — CSS `linear-gradient` тех же цветов.

## 3. Код: палитра и вывод цвета (ядро страницы F2)

```js
// three r186 — [проверено: 99-raw/experiments/F2/04-shader-bg; повторно 99-raw/experiments/K/10-shader-page] цвет бренда в ShaderMaterial
const PALETTE = ['#ff6a3d', '#ffb36b', '#7a5cff', '#29c4ff'];            // бренд: hex в sRGB
const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'low-power' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1));                    // размытый фон: DPR ≤ 1
renderer.toneMapping = THREE.NoToneMapping;                               // фон не тонмаппится: hex = пиксель
const cols = PALETTE.map((h) => new THREE.Color(h));                      // ЛИНЕЙНЫЕ значения (ColorManagement)
const uniforms = { uTime: { value: 0 }, uRes: { value: new THREE.Vector2() },
  uC0: { value: cols[0] }, uC1: { value: cols[1] }, uC2: { value: cols[2] }, uC3: { value: cols[3] } };
// фрагментный шейдер: смешивание cols по fbm → gl_FragColor = vec4(col, 1.); затем строка
// #include <colorspace_fragment>                                           // линейный → sRGB вывода (с начала строки!)
```

Цикл и остановка (там же): `renderer.setAnimationLoop(visible && !document.hidden && !reduce.matches ? tick : null)`; при остановке —
`renderer.render()` один раз; `IntersectionObserver` на герой, `visibilitychange`, `reduce.addEventListener('change', …)`; время —
`THREE.Timer` (r183+, вместо `Clock`).

## 4. Числа

| вариант (1440 × 900) | вызовов | мс/кадр | JS | источник |
|---|---|---|---|---|
| `gradient` | 1 | **1,45** | three 361 КБ (jsDelivr) | F2/04; повтор K/10: 1 вызов, 60 fps, LCP 48 мс (текст), TBT 11 мс, 360 КБ, 0 ошибок |
| `ribbon` (вершинный, MSAA) | 1 | 2,34 | 361 КБ | F2/04 |
| `paper` | 1 | — (свой контекст) | **119 КБ** | F2/04 |
| `sdf` ½ | 1 | 1,07 (Pixel 7: 1,81, 60 fps) | 361 КБ | F2/04 |
| `swatch` без `colorspace_fragment` | 1 | — | — | ΔE2000 **9,55** |

Бандлер на своём домене вместо import map с CDN: 174 против 443 КБ br у three (F1 `09/01 §1`) — для продакшена.

## 5. Страница

`examples/11-shader-background/index.html` — копия демо F2 без изменений: `?v=gradient|ribbon|paper|sdf|swatch`, `&res=0.5`,
`&dpr=N`, `&cs=off`. Менять только `PALETTE` (и тексты). Для React — тот же шейдер в `<Canvas frameloop="demand">` (F2 `09/02 §3`).
Ловушка import map демо: `three.module.min.js` с jsDelivr импортирует **неминифицированный** `./three.core.js` (204 КБ br) — добавить
ключ-URL `…/build/three.core.js` → `…/build/three.core.min.js` в `imports` или собрать бандлером (F1 `09/01 §1.2`; замечание J).

## 6. Ворота

1 вызов в кадре; 0 вызовов в покое при reduce и вне экрана; DPR canvas ≤ 1 у размытого фона (фон с деталью — бюджетом
пикселей, п.3); цвет — `?v=swatch` даёт пиксель = hex (ΔE 0); LCP —
текст, не canvas; `gate_check()` рецепта 01 (мобильный + reduce).

## 7. Варианты

1. **Stripe-лента** (`?v=ribbon`): сетка 100–128², деформация и цвет в вершинном шейдере, `smoothstep` для полос
   [V:LW9d2cqIHb4 через W7; проверено: F2/04].
2. **Paper Shaders** (`?v=paper`): меньше JS (119 КБ), но свой контекст WebGL и DPR ≥ 2 — дороже на телефоне по пикселям.
3. **Блоб-SDF** (`?v=sdf`): 5 метаболов smooth-min, 64 шага, ½ разрешения.
4. **Фон под 3D-объектом** — тот же шейдер как `scene.background`-плоскость в той же сцене (1 renderer, стекло рецепта 09 его увидит).
5. **Зерно и виньетка** — CSS (не пост-проход) (F2 `09/04 §9`).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| hex в uniform без `colorspace_fragment` | бренд «кислотнее»/темнее, ΔE 9,55 | `THREE.Color` + `#include <colorspace_fragment>` |
| тонмаппинг на фоне | бренд смещён | `NoToneMapping` для фона |
| DPR 2–3 на размытом фоне | ×4–9 пикселей без пользы | DPR ≤ 1 |
| DPR 1 на фоне с деталью 1–2 px (точки, линии, решётки) | деталь мылится | бюджет пикселей, как у объекта (п.3) |
| `requestAnimationFrame` всегда | батарея, 60 кадров вне экрана | цикл по видимости, reduce → 1 кадр |
| пороги fbm выше медианы, кубический value-noise | «каша» с квадратами решётки (первая версия F2) | пороги у медианы, квинтика |
| шейдер с Shadertoy | CC BY-NC-SA 3.0 — нельзя в коммерческий сайт | свой код или MIT-библиотека |

## Ссылки

F2 `../09-web-runtime/04-shaders-effects-catalog-impl.md §2`, `../09-web-runtime/examples/shader-background/README.md`; W7 `../91-videos/digests/_index-W7.md`
(Stripe `LW9d2cqIHb4`, shader art); A `../01-web-3d-landscape/01-effects-catalog.md §5, §23`; F1 `../09-web-runtime/01-threejs-core.md §1`.
