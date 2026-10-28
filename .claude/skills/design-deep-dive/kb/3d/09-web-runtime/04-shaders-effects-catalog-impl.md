# Реализация эффектов каталога: шейдерные фоны, стекло, частицы, блоб, дисторсии, SDF-текст, контуры, пост-эффекты

Волна 2 · агент F2 · 23.09.2026 · источников: 12 (исходники three r186 и примеры `webgl_*`, документация drei, pmndrs/postprocessing,
@paper-design/shaders, заметки по 10 роликам, отчёты W3/W4/W7/D2) · экспериментов: 4 (`99-raw/experiments/F2/04-shader-bg`,
`05-fx-lab`, `02-r3f-hero`, `07-engines`), 17 вариантов эффектов с замером · версии: three r186 (0.186.0), postprocessing 6.39.5,
@paper-design/shaders 0.0.81, troika-three-text 0.52.5, cobe 2.0.1, Chromium 153 headless (Iris Xe, ANGLE GL).
Каталог эффектов, примеры сайтов и клише — `../01-web-3d-landscape/01-effects-catalog.md` (A; номера § ниже — его);
выбор постобработки (pmndrs / EffectComposer / RenderPipeline) — `01-threejs-core.md` §8 (F1); материалы и цвет в Blender — `../06-…` (D2).

## Выжимка для агента

1. **Шейдерный фон — самый дешёвый «вау» без Blender**: один полноэкранный фрагментный шейдер (fbm-шум с деформацией домена, 4 цвета бренда,
   дизеринг) — 1 вызов, 1,45 мс/кадр при 1440×900, 0 ассетов; LCP 60 мс (текст), TBT 19 мс → §2.1. [проверено]
2. **Цвета бренда в `ShaderMaterial` передавай `THREE.Color` и заканчивай шейдер `#include <colorspace_fragment>`** (с новой строки):
   без него `#ff6a3d` выводится как rgb(255, 37, 12), ΔE2000 = 9,55 — `Color` хранит линейные значения (r152+) → §2.2. [проверено]
3. **Фон не тонмаппить** (`NoToneMapping` на его рендерере); размытый фон — DPR ≤ 1, чёткость ему не нужна; фон с деталью
   1–2 px (точки, линии, решётки) — плотность как у объекта (§10) → §2.1. [проверено]
4. **Маски цвета ставь у медианы шума**: fbm из 3 октав имеет среднее ≈ 0,44; пороги 0,45–0,95 оставили «оранжевую кашу» без двух
   цветов; value-noise сглаживай квинтикой — иначе видны квадраты решётки → §2.1. [проверено: F2/04, до/после]
5. **Stripe-подход (деформация и цвет в вершинах сетки 100–128²)** на десктопном GPU не дешевле фрагментного (2,34 против 1,45 мс;
   533 против 1 053 fps без vsync, с MSAA); выигрывает, когда пикселей много, а вершин мало (Артюх: 10 тыс. вершин × 5 шумов против
   ~1 млн пикселей retina) → §2.3. [проверено: F2/04; V:LW9d2cqIHb4 54:12]
6. **`@paper-design/shaders` — готовый mesh gradient за 119 КБ JS**, но рендерит минимум при DPR 2 (`minPixelRatio = 2` по умолчанию):
   на экране 1440×900 холст 2880×1800 — задавай `minPixelRatio`/`maxPixelCount` в конструкторе `ShaderMount`; `speed 0` при reduce →
   0 вызовов → §2.4. [проверено]
7. **Полноэкранный SDF-raymarching без ограничивающего объёма** (метаболы, рельеф фона) — в ½ разрешения или фоном без
   мелкой детали: 64 шага на пиксель, полное разрешение в 6,6 раза дороже (7,04 против 1,07 мс) при ×4 пикселях; на Pixel 7
   в ½ — 1,81 мс, 60 fps. **SDF-объект в ограничивающем объёме** — полное разрешение под бюджетом пикселей: 4,7–13 мс при
   3,7 Мпикс, марш ≤ 140 шагов, край — по минимуму d/(t·px); норма — `../16-js-scenes/01-engine.md` §12 → §2.5. [проверено]
8. **Стекло — `MeshPhysicalMaterial` transmission + thickness + roughness + clearcoat** (так же приходит из Blender, E §6.2): +1 проход
   непрозрачных объектов (2 → 3 вызова), 1,72 мс; `renderer.transmissionResolutionScale = 0.5` — 1,39 мс без видимой потери → §3.
   [проверено]
9. **Фон, который должно преломлять стекло, рисуй внутри сцены**: three преломляет только отрисованное в canvas; на прозрачном canvas
   поверх HTML стекло выглядит серым диском (ΔE ≈ 10) → §3. [проверено D2: `../06-materials-lighting-render/`, отчёт D2 §2; F2/05 — фон-плоскость в сцене]
10. **«Дешёвое стекло» (прозрачность 0,35 + clearcoat, DoubleSide)** не преломляет и по GPU не дешевле (1,71 мс, треугольники ×2) —
    только запас для слабых устройств; для стилизации — `BackSide`-трюки (W4) → §3. [проверено: F2/05; V:H1oNuKChsdU 24:38]
11. **`MeshTransmissionMaterial` drei — отдельный проход сцены на каждый материал**: `resolution` 256–512, `samples` ≤ 6, `transmissionSampler`
    для нескольких объектов; на телефоне — 1 объект → §3. [документация drei; не замерено здесь]
12. **Частицы с поверхности модели**: `MeshSurfaceSampler` по мешу из GLB → 40 000 точек, морфинг в другую форму через атрибут `aTarget` и
    `uProgress` — 1 вызов, 1,06 мс; одна форма = N × 12 байт (480 КБ Float32); для морфинга — одинаковое N и порядок точек → §4.
    [проверено]
13. **Шумовой блоб — смещение в вершинном шейдере через `onBeforeCompile` и пересчёт нормали по двум соседним точкам**: `IcosahedronGeometry(1, 32)`
    (65 340 вершин), 1 вызов, 2,7 мс; без пересчёта нормали освещение «плоское» → §5. [проверено]
14. **Искажение картинки под курсором — плоскость с шейдером**: «вздутие» к курсору + RGB-сдвиг, сила по `damp`, 1 вызов, 1,03 мс; `<img alt>`
    остаётся в DOM (LCP, SEO) → §6. [проверено: F2/05; A `01` §9]
15. **SDF-текст troika** — 14 глифов = 1 вызов, 1,5 мс; кириллица — шрифт woff/ttf с кириллицей (Inter cyrillic 700); текст всегда
    дублируется HTML → §7. [проверено]
16. **Контур: inverted hull (копия меша, `BackSide`, сдвиг по нормали)** — 2 вызова, 0,60 мс, чёткая линия; `OutlinePass` — 10 вызовов,
    1,35 мс, мягкий ореол → hull дешевле в 2,3 раза; в Blender — Solidify с отрицательной толщиной (A `01` §21.3) → §8. [проверено]
17. **Matcap из canvas-градиента или рендера сферы в Blender** — `MeshMatcapMaterial`, без света и окружения, самый дешёвый «глянец» → §8.
    [проверено]
18. **Пост-лук одним `EffectPass`** (pmndrs: Bloom mipmapBlur + Noise + Vignette + ToneMapping) — 18 вызовов, 1,9 мс; тонмаппинг в конце
    цепочки (`renderer.toneMapping = NoToneMapping`); зерно — поверх чистого кадра и слабо: SOFT_LIGHT ≈ 0,05 (*исправлено по T21*: было
    OVERLAY 0,25 — на тёмной сцене с бликами OVERLAY уже при 0,07 даёт пересвет 3,9 %, SOFT_LIGHT 0,12 — крапинку в тёмных) → §9.
    [проверено: F2/05; CD/06 — `99-raw/experiments/CD/rules.md`; V:Z8AAX-ENWvQ 22:38]
19. **Зерно и виньетку без bloom делай CSS** (SVG `feTurbulence` + `radial-gradient` поверх canvas): 0,63 мс против 1,9, 0 КБ JS → §9.
    [проверено]
20. **pmndrs `postprocessing` 6.39.5 — только `WebGLRenderer` и peer three < 0.187**; для `WebGPURenderer` — TSL `RenderPipeline` (F1 `01` §8) → §9.
    [документация npm]
21. **Каждый эффект: reduce → один кадр и стоп цикла; вне экрана и в скрытой вкладке — стоп** (все демо: 0 вызовов в покое при reduce) → §10.
    [проверено]
22. **Чужой шейдерный код с Shadertoy не копировать** — лицензия по умолчанию CC BY-NC-SA 3.0 (некоммерческая); формулы (fbm, smooth-min,
    палитра IQ) писать самому → §2. [документация; отчёт W7 §8]

## 1. Сводная таблица замеров

Метод: одна страница на эффект, холст 1440×900, DPR 1, NeutralToneMapping (фоны — NoToneMapping); «мс/кадр» — 120 кадров с
`readPixels` (GPU-синхронно) в режиме без vsync; «fps без vsync» — `--disable-gpu-vsync --disable-frame-rate-limit`, относительная
цена; инструмент `99-raw/experiments/F2/00-tools/fx_probe.py`. Машина общая (6–9 агентов): сравнивать строки между собой.

| § каталога A | Эффект, вариант | Вызовов | Мс/кадр | fps без vsync | JS/ассеты | Телефон / reduce | Статус |
|---|---|---|---|---|---|---|---|
| 5.1 | mesh gradient, фрагментный fbm | 1 | 1,45 | 1 053 | three; 0 ассетов | DPR ≤ 1; reduce 0 вызовов | [проверено F2/04] |
| 5.1 | «лента» Stripe, вершинный 128², MSAA | 1 | 2,34 | 533 | three | — | [проверено F2/04] |
| 5.1 | `@paper-design/shaders` mesh gradient | 1 | — | 1 073 (холст ×4) | 119 КБ по сети | speed 0 → 0 вызовов | [проверено F2/04] |
| 5.6 | SDF-метаболы ½ / полное разрешение | 1 | 1,07 / 7,04 | 1 467 / 491 | three | Pixel 7 ½: 1,81 мс, 60 fps | [проверено F2/04] |
| 7.1 | стекло transmission / scale 0,5 / подделка | 3 / 3 / 3 | 1,72 / 1,39 / 1,71 | 965 / 1 272 / 1 340 | three + GLB 63 КБ | 1 объект, scale 0,5 | [проверено F2/05] |
| 6.2 | частицы с поверхности, 40 тыс., морфинг | 1 | 1,06 | 1 669 | 480 КБ на форму (Float32) | 20–30 тыс. (A) | [проверено F2/05] |
| 5.2 | шумовой блоб, 65 тыс. вершин | 1 | 2,70 | 1 382 | three | detail 16–24 | [проверено F2/05] |
| 9.1 | искажение картинки под курсором | 1 | 1,03 | 2 607 | картинка | нет hover на тач | [проверено F2/05] |
| 8.2 | SDF-текст troika, 14 глифов | 1 | 1,50 | 981 | troika 117 КБ min + шрифт | — | [проверено F2/05] |
| 21.3 | контур inverted hull + matcap / `OutlinePass` | 2 / 10 | 0,60 / 1,35 | 3 881 / 1 298 | three | — | [проверено F2/05] |
| 18.1–18.2 | pmndrs Bloom + Noise + Vignette / CSS-зерно и виньетка | 18 / 1 | 1,90 / 0,63 | 1 170 / 3 263 | +postprocessing / 0 | 1–2 эффекта | [проверено F2/05] |
| 2.2 | R3F-hero: Float, ContactShadows frames 1, Lightformer | 3 | 2,05 (880×550) | 2 325 | 293 КБ br чанк | DPR 1,5; reduce 0 | [проверено F2/02] |
| 17.1 | точечный глобус cobe 2.0.1 | 0 перехвачено | — | 60 | 5 КБ br (A) | — | карта точек не отрисовалась — [не проверено] |

## 2. Шейдерные фоны без Blender (§5.1–5.7)

### 2.1. Mesh gradient: фрагментный шейдер
```js
// three r186 — [проверено: 09-web-runtime/examples/shader-background (?v=gradient)] 1 вызов, 1,45 мс/кадр при 1440×900
import * as THREE from 'three';
export function makeGradientBackground(hexes = ['#ff6a3d', '#ffb36b', '#7a5cff', '#29c4ff']) {
  const [c0, c1, c2, c3] = hexes.map((h) => new THREE.Color(h));        // линейные значения (ColorManagement)
  const uniforms = { uTime: { value: 0 }, uRes: { value: new THREE.Vector2(1, 1) },
    uC0: { value: c0 }, uC1: { value: c1 }, uC2: { value: c2 }, uC3: { value: c3 } };
  const material = new THREE.ShaderMaterial({ uniforms,
    vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }',
    fragmentShader: `uniform float uTime; uniform vec2 uRes; uniform vec3 uC0, uC1, uC2, uC3; varying vec2 vUv;
      float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
      float vnoise(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * f * (f * (f * 6. - 15.) + 10.);   // квинтика
        return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y); }
      float fbm(vec2 p) { float a = .5, s = 0.; for (int i = 0; i < 3; i++) { s += a * vnoise(p); p *= 2.03; a *= .5; } return s; }
      void main() {
        vec2 p = vUv * vec2(uRes.x / uRes.y, 1.) * 1.2;
        float t = uTime * .05;
        vec2 w = vec2(fbm(p + vec2(t, -t)), fbm(p + vec2(4.1 - t, 1.7 + t)));   // деформация домена
        float n = fbm(p * 1.3 + w * 1.6 + t);
        vec3 c = mix(uC0, uC1, smoothstep(.3, .6, n));                        // пороги у медианы fbm ≈ 0,44
        c = mix(c, uC2, smoothstep(.36, .56, w.x));
        c = mix(c, uC3, smoothstep(.42, .62, w.y));
        c += (hash(gl_FragCoord.xy + uTime) - .5) / 255.;                     // дизеринг против бандинга
        gl_FragColor = vec4(c, 1.);
#include <colorspace_fragment>
      }` });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material);
  mesh.frustumCulled = false;                                             // полноэкранный квад без камеры
  return { mesh, uniforms };
}
```
Подключение (демо `examples/shader-background`): отдельный `WebGLRenderer({ powerPreference: 'low-power' })`,
`toneMapping = NoToneMapping`, `setPixelRatio(min(devicePixelRatio, 1))`, `THREE.Timer` для `uTime`, цикл только при видимом герое и
без reduce, CSS-градиент под canvas — запас; текст и CTA — HTML поверх [проверено].
- Бандинг на плавных градиентах — шум/дизеринг ±0,5/255 [V:LW9d2cqIHb4 55:52]. Порядок сборки шейдерного фона: координаты 0…1 →
  центр и −1…1 → поправка на соотношение сторон → SDF/fract/итерации → палитра → `pow` для контраста [V:f4s1h2YETNY 05:16–21:29].
- Первая версия (пороги масок 0,45–0,95, кубическое сглаживание) — два цвета из четырёх не проявились, видны квадраты решётки; правка
  порогов к медиане fbm и квинтика — все цвета, пятен нет [проверено: F2/04, скриншоты до/после].
- Клише: «пастельный фиолетово-розовый mesh gradient» и «фиолетовая аврора» (A `01` §22) — брать цвета бренда, а не пресет.

### 2.2. Цвет uniform против hex
| Вывод шейдера | Пиксель для `new THREE.Color('#ff6a3d')` | ΔE2000 к hex |
|---|---|---|
| с `#include <colorspace_fragment>` (с начала строки) | (255, 106, 61) | 0,00 |
| без него | (255, 37, 12) | **9,55** |
[проверено]. Директива `#include` в той же строке, что код
(`gl_FragColor = …; #include <colorspace_fragment>`), не раскрывается — три-препроцессор ищет её с начала строки [проверено при
отладке F2/04]. Шейдер, перенесённый с Shadertoy (цвета заданы как sRGB-числа), — наоборот, без `colorspace_fragment` [отчёт W7 §4].

### 2.3. Вершинный вариант в духе Stripe
Stripe считает деформацию и цвет в вершинном шейдере плоскости: сетка 300×300 ≈ 100 тыс. точек [V:LW9d2cqIHb4 11:22], на 100×100
разницы не видно при ×10 меньше вычислений [V:LW9d2cqIHb4 52:53]; шум `uv * vec2(3, 4)` (асимметрия — «природные» формы), время в
двух скоростях, наклон `0.5 * uv.y`, `max(0, noise)` убирает впадины, `smoothstep` — чёткие границы цвета [V:LW9d2cqIHb4 20:30–50:30]. Код —
`examples/shader-background/index.html` (`?v=ribbon`): на Iris Xe 2,34 мс (с MSAA) против 1,45 у фрагментного → вершинный выбирать для
экранов высокой плотности (retina, 4K), где фрагментов в 4–9 раз больше [проверено: F2/04; расчёт].

### 2.4. Готовая библиотека `@paper-design/shaders`
```js
// @paper-design/shaders 0.0.81 — [проверено: examples/shader-background (?v=paper)] 119 КБ по сети; холст ×2 по умолчанию
import { ShaderMount, meshGradientFragmentShader, getShaderColorFromString } from '@paper-design/shaders';
const el = document.querySelector('.bg');
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const mount = new ShaderMount(el, meshGradientFragmentShader, {
  u_colors: ['#ff6a3d', '#ffb36b', '#7a5cff', '#29c4ff'].map(getShaderColorFromString), u_colorsCount: 4,
  u_distortion: 0.8, u_swirl: 0.15, u_grainMixer: 0, u_grainOverlay: 0 }, undefined, reduce.matches ? 0 : 0.6);
window.__paperMount = mount;                           // speed 0 → один кадр, 0 вызовов в покое
```
Параметры конструктора `ShaderMount` после скорости — `frame`, `minPixelRatio` (по умолчанию 2), `maxPixelCount`: на телефоне с DPR 3
библиотека рендерит в полном DPR → задавай явно [проверено: `shader-mount.d.ts`; F2/04: холст 2880×1800 при CSS 1440×900].

### 2.5. SDF-raymarching (метаболы, «жидкие» формы)
```js
// three r186 — [проверено: examples/shader-background (?v=sdf)] ½ разрешения: 1,07 мс; полное: 7,04 мс (1440×900)
import * as THREE from 'three';
export function makeMetaballs(hexes = ['#ff6a3d', '#ffb36b', '#7a5cff', '#29c4ff']) {
  const [a, b, c, d] = hexes.map((h) => new THREE.Color(h));
  const uniforms = { uTime: { value: 0 }, uRes: { value: new THREE.Vector2(1, 1) }, uC0: { value: a }, uC1: { value: b }, uC2: { value: c }, uC3: { value: d } };
  const material = new THREE.ShaderMaterial({ uniforms,
    vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }',
    fragmentShader: `uniform float uTime; uniform vec2 uRes; uniform vec3 uC0, uC1, uC2, uC3; varying vec2 vUv;
      float smin(float a, float b, float k) { float h = max(k - abs(a - b), 0.) / k; return min(a, b) - h * h * h * k / 6.; }
      float map(vec3 p) { float d = 1e3; float t = uTime * .35;
        for (int i = 0; i < 5; i++) { float fi = float(i);
          vec3 c = vec3(sin(t * (.7 + .13 * fi) + fi * 1.7) * 1.1, cos(t * (.5 + .11 * fi) + fi * 2.3) * .6, sin(t * .3 + fi) * .4);
          d = smin(d, length(p - c) - (.42 + .06 * fi), .55); }
        return d; }
      vec3 nrm(vec3 p) { const vec2 e = vec2(1e-3, -1e-3);
        return normalize(e.xyy * map(p + e.xyy) + e.yyx * map(p + e.yyx) + e.yxy * map(p + e.yxy) + e.xxx * map(p + e.xxx)); }
      void main() {
        vec2 p = (vUv - .5) * vec2(uRes.x / uRes.y, 1.);
        vec3 ro = vec3(0., 0., 4.), rd = normalize(vec3(p, -1.6));
        float t = 0.; bool hit = false;
        for (int i = 0; i < 64; i++) { float h = map(ro + rd * t); if (h < 1e-3) { hit = true; break; } t += h; if (t > 9.) break; }
        vec3 col = mix(uC1, uC3, vUv.y) * .35 + .62;
        if (hit) { vec3 n = nrm(ro + rd * t); vec3 l = normalize(vec3(.5, .8, .6));
          vec3 base = mix(mix(uC0, uC2, n.y * .5 + .5), uC3, pow(1. - max(dot(n, -rd), 0.), 2.));
          col = base * (.45 + .6 * max(dot(n, l), 0.)) + pow(max(dot(reflect(rd, n), l), 0.), 24.) * .35; }
        gl_FragColor = vec4(col, 1.);
#include <colorspace_fragment>
      }` });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material);
  mesh.frustumCulled = false;
  return { mesh, uniforms };                         // renderer.setPixelRatio(0.5 * min(dpr, 1)) — половинное разрешение
}
```
- Разрешение: метаболы выше — полноэкранный марш без ограничивающего объёма, до 64 шагов в каждом пикселе кадра, поэтому ½
  разрешения или фон без мелкой детали. SDF-объект, у которого марш идёт только внутри ограничивающей коробки, рисуется в
  полном разрешении под бюджетом пикселей: 4,7–13 мс при 3,7 Мпикс на Iris Xe, ≤ 140 шагов; промах ближе 1,25 px смешивается
  с фоном по минимуму d/(t·px) — край без лесенки при DPR ≤ 2 (`../16-js-scenes/01-engine.md` §12) [проверено].
- Формулы: объединение `min`, smooth-min на кубическом полиноме (непрерывные производные), нормаль — градиент SDF (4 выборки
  «тетраэдром»), мягкая тень и AO из самой SDF без трассировки [V:8--5LwHRhjk 00:25–05:51] [документация IQ].
- Клише: «лава-лампа на тёмном фоне», «хромированный блоб» (A `01` §22) — матовые цвета бренда, медленное движение.

## 3. Стекло и преломление (§7.1–7.4)

```js
// three r186 — [проверено: 99-raw/experiments/F2/05-fx-lab (?fx=glass)] 3 вызова, 1,72 мс; scale 0.5 → 1,39 мс
import * as THREE from 'three';
export function glassMaterial({ tint = '#b9c8ff', thickness = 0.6, roughness = 0.12 } = {}) {
  return new THREE.MeshPhysicalMaterial({ color: '#ffffff', transmission: 1, thickness, roughness, ior: 1.5,
    clearcoat: 1, clearcoatRoughness: 0.05,                               // блеск сверху (W3: transmission + roughness + coat)
    attenuationColor: new THREE.Color(tint), attenuationDistance: 1.2 });
}
// renderer.transmissionResolutionScale = 0.5;   // буфер прохода в ¼ пикселей; фон для преломления — объект В сцене
```
- Цена: three рисует все непрозрачные объекты второй раз в буфер прохода transmission (здесь фон-плоскость: 2 → 3 вызова), компиляция
  `MeshPhysicalMaterial` с transmission — 387 мс против 38–88 у Standard (E `08-export-gltf/01` §6.1) [проверено F2/05; E].
- Из Blender стекло приезжает тем же материалом: Transmission Weight 1 + Thickness в группе «glTF Material Output» + Volume Absorption
  (E §6.2); без Thickness — тонкостенная прозрачность без преломления [проверено E].
- Прозрачный canvas поверх HTML: преломлять нечего — серый диск (ΔE ≈ 10) → фон-плоскость или окружение внутри сцены [проверено D2].
- Подделка без transmission (`transparent`, `opacity 0.35`, `clearcoat 1`, `DoubleSide`, `depthWrite: false`): 1,71 мс, треугольники ×2,
  вид «молочного пластика» — только запас [проверено F2/05]. Дешёвая стилизация: перевёрнутые нормали/`BackSide` [V:H1oNuKChsdU 24:38].
- drei `MeshTransmissionMaterial`: видит другие прозрачные объекты, хроматическая аберрация, `samples` 6, отдельный буфер на материал —
  дороже MPM при нескольких объектах; `resolution={256}`, `transmissionSampler` [документация drei; не замерено здесь].
- Дисперсия (`KHR_materials_dispersion` → `dispersion`), иридесценция (`iridescence`) переносятся из Blender через группу «glTF Material
  Output» (E §6.1); без `scene.environment` металл и стекло «чёрные» (F1 `01` §4).
- Клише §22: «стеклянный тор/капля на градиенте» — стекло с продуктом или данными бренда; на телефоне — предрендер Cycles картинкой.

## 4. Частицы с поверхности модели (§6.1–6.4)

```js
// three r186 — [проверено: 99-raw/experiments/F2/05-fx-lab (?fx=particles)] 40 000 точек, 1 вызов, 1,06 мс
import * as THREE from 'three';
import { MeshSurfaceSampler } from 'three/addons/math/MeshSurfaceSampler.js';
export function makeSurfaceParticles(geometry, N = 40000, color = '#5b3fd6', pixelRatio = 1) {
  const sampler = new MeshSurfaceSampler(new THREE.Mesh(geometry)).build();
  const a = new Float32Array(N * 3), b = new Float32Array(N * 3), p = new THREE.Vector3();
  for (let i = 0; i < N; i++) {
    sampler.sample(p); p.toArray(a, i * 3);                                // форма 1: поверхность модели
    p.randomDirection().multiplyScalar(1.1); p.toArray(b, i * 3);          // форма 2: сфера (то же N, тот же порядок)
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(a, 3));
  g.setAttribute('aTarget', new THREE.BufferAttribute(b, 3));
  const material = new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
    uniforms: { uP: { value: 0 }, uSize: { value: 2.2 * pixelRatio }, uColor: { value: new THREE.Color(color) } },
    vertexShader: `uniform float uP, uSize; attribute vec3 aTarget;
      void main() { vec3 pos = mix(position, aTarget, smoothstep(0., 1., uP));
        vec4 mv = modelViewMatrix * vec4(pos, 1.); gl_Position = projectionMatrix * mv; gl_PointSize = uSize * (4. / -mv.z); }`,
    fragmentShader: `uniform vec3 uColor;
      void main() { float d = length(gl_PointCoord - .5); if (d > .5) discard; gl_FragColor = vec4(uColor, smoothstep(.5, .2, d));
#include <colorspace_fragment>
      }` });
  return new THREE.Points(g, material);                                    // points.material.uniforms.uP.value = прогресс 0…1
}
```
- Формы из Blender (логотип → продукт → текст): точки поверхности пишет D1 — `.bin` Float32 LE, xyz подряд в осях three (x, z, −y),
  одинаковое N и порядок на все формы, заголовок JSON {count, forms, axes, units} (предложение F2 в заметках, A `05` §3.8); в JS —
  `new THREE.BufferAttribute(new Float32Array(await (await fetch(url)).arrayBuffer()), 3)`. 100 тыс. точек × 3 формы ≈ 3,6 МБ до
  сжатия — на телефоне 20–30 тыс. (A `01` §6.2) [практика].
- Ориентир производительности: 400 тыс. объектов на телефоне при ~60 fps у Артюха [V:Eq_rXOyOX0I 42:52]; крупные точки и аддитивное
  смешивание — overdraw [практика].
- GPGPU (текстуры позиций/скоростей, `GPUComputationRenderer`, `examples/webgl_gpgpu_birds`) и WebGPU compute (`webgpu_compute_particles`,
  storage-буферы TSL) — не проверялись здесь [не проверено]; нужен float render target (`EXT_color_buffer_float`, не на всех телефонах).
- Клише §22: «шар/галактика/логотип из частиц» — частицы, которые объясняют (продукт → схема).

## 5. Шумовой блоб (§5.2)

```js
// three r186 — [проверено: 99-raw/experiments/F2/05-fx-lab (?fx=blob)] 65 340 вершин, 1 вызов, 2,70 мс
import * as THREE from 'three';
export function makeNoiseBlob(color = '#8f7cff') {
  const material = new THREE.MeshPhysicalMaterial({ color, roughness: 0.25, clearcoat: 0.6 });
  const uniforms = { uTime: { value: 0 } };
  material.onBeforeCompile = (s) => {
    s.uniforms.uTime = uniforms.uTime;
    s.vertexShader = s.vertexShader.replace('#include <common>', `#include <common>
      uniform float uTime;
      float h3(vec3 p) { p = fract(p * .3183099 + .1); p *= 17.; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
      float n3(vec3 x) { vec3 i = floor(x), f = fract(x); f = f * f * (3. - 2. * f);
        return mix(mix(mix(h3(i), h3(i + vec3(1, 0, 0)), f.x), mix(h3(i + vec3(0, 1, 0)), h3(i + vec3(1, 1, 0)), f.x), f.y),
                   mix(mix(h3(i + vec3(0, 0, 1)), h3(i + vec3(1, 0, 1)), f.x), mix(h3(i + vec3(0, 1, 1)), h3(i + 1.), f.x), f.y), f.z); }
      vec3 disp(vec3 p) { return p + normalize(p) * (n3(p * 1.8 + uTime * .35) - .5) * .35; }`)
      .replace('#include <beginnormal_vertex>', `vec3 bt = normalize(cross(normal, abs(normal.y) < .99 ? vec3(0, 1, 0) : vec3(1, 0, 0)));
      vec3 bb = cross(normal, bt); vec3 P = disp(position), PA = disp(position + bt * .01), PB = disp(position + bb * .01);
      vec3 objectNormal = normalize(cross(PA - P, PB - P));`)                   // нормаль по двум соседним точкам
      .replace('#include <begin_vertex>', 'vec3 transformed = P;');
  };
  return { mesh: new THREE.Mesh(new THREE.IcosahedronGeometry(1, 32), material), uniforms };
}
```
Шум в вершинах дешевле, чем во фрагментах; на `WebGPURenderer` слоты материала — TSL `positionNode`/`normalNode` (onBeforeCompile там не
работает) [V:EQ5m0Jhz-qs 18:43]; клише «радужный/хромированный блоб» (§22) — матовый цвет бренда.

## 6. Эффекты над картинками (§9)

```js
// three r186 — [проверено: 99-raw/experiments/F2/05-fx-lab (?fx=hover)] 1 вызов, 1,03 мс; сила — damp(λ 6)
import * as THREE from 'three';
export function makeHoverImage(texture, w = 3.2, h = 2.4) {
  texture.colorSpace = THREE.SRGBColorSpace;                              // своя ShaderMaterial: пространство картинки явно
  const uniforms = { uTex: { value: texture }, uMouse: { value: new THREE.Vector2(0.5, 0.5) }, uStrength: { value: 0 } };
  const material = new THREE.ShaderMaterial({ uniforms,
    vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
    fragmentShader: `uniform sampler2D uTex; uniform vec2 uMouse; uniform float uStrength; varying vec2 vUv;
      void main() { vec2 d = vUv - uMouse; float k = uStrength * smoothstep(.35, 0., length(d));
        vec2 uv = uMouse + d * (1. - .45 * k);                                // «вздутие» к курсору
        vec3 c = vec3(texture2D(uTex, uv + d * k * .02).r, texture2D(uTex, uv).g, texture2D(uTex, uv - d * k * .02).b);
        gl_FragColor = vec4(c, 1.);
#include <colorspace_fragment>
      }` });
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(w, h), material);
  const ray = new THREE.Raycaster();
  plane.userData.update = (ndc, camera, dt) => {                          // в цикле кадра
    ray.setFromCamera(ndc, camera); const hit = ray.intersectObject(plane)[0];
    uniforms.uStrength.value = THREE.MathUtils.damp(uniforms.uStrength.value, hit ? 1 : 0, 6, dt);
    if (hit) uniforms.uMouse.value.copy(hit.uv);
  };
  return plane;
}
```
- Плоскость стоит на месте `<img>` (размер и позиция — `getBoundingClientRect`, синхронно с прокруткой через Lenis); `<img alt>` остаётся в
  DOM — LCP, SEO, запас без WebGL (A `01` §9.1) [практика; A/04].
- Переход между картинками по карте смещения (§9.2): `mix(texture(uFrom, uv + d·p), texture(uTo, uv − d·(1 − p)), p)`, `p` от GSAP
  [не проверено]. Искажение от скорости прокрутки (§9.4): скорость Lenis (`lenis.velocity`) → uniform [V:YyqBdN71nFs 21:42] [не проверено].
- Клише: «жидкое искажение на каждой карточке портфолио» — эффект на одном ключевом элементе; на тач-экране нет hover.

## 7. Текст в WebGL (§8)

```js
// troika-three-text 0.52.5 + three r186 — [проверено: 99-raw/experiments/F2/05-fx-lab (?fx=text)] 14 глифов, 1 вызов, 1,5 мс
export async function makeSdfText(Text, str, { font, size = 0.42, color = '#2d2150' } = {}) {
  const t = new Text();                                    // Text из troika (сборка с three внешним — один экземпляр three)
  t.text = str; t.fontSize = size; t.anchorX = 'center'; t.anchorY = 'middle'; t.color = color;
  if (font) t.font = font;                                 // woff/ttf; для кириллицы — шрифт с кириллицей (Inter cyrillic 700)
  await new Promise((resolve) => t.sync(resolve));         // SDF генерируется в воркере
  return t;
}
```
- troika из jsDelivr `+esm` тянет свой three → «Multiple instances of Three.js»; собирай troika бандлером с `--external:three` (F2/05:
  117 КБ min) или через drei `<Text>` [проверено].
- WebGL-текст только дублирует HTML-заголовок (прозрачный, но выделяемый текст в DOM; синхрон размеров — `getComputedStyle`, камера
  `fov = 2·atan((h/2)/z)`) — LCP и поиск видят HTML (A `01` §8.2; A/04) [практика].
- Выдавленный 3D-текст — GLB из Blender (текст → меш с фаской, `resolution_u` 3–4 даёт ×6,6 меньше треугольников — E `01` §4.8), не
  `TextGeometry` с typeface-JSON 50–400 КБ [проверено E].
- SDF 128×128 даёт чёткий крупный контур, предел ≈ 100 px кегля [V:Eq_rXOyOX0I 28:34–29:32] [практика].

## 8. Контур, тун, matcap (§21.3)

```js
// three r186 — [проверено: 99-raw/experiments/F2/05-fx-lab (?fx=outline)] hull: 2 вызова, 0,60 мс; OutlinePass: 10 вызовов, 1,35 мс
import * as THREE from 'three';
export function addInvertedHull(mesh, thickness = 0.018, color = '#17132b') {
  const hull = new THREE.Mesh(mesh.geometry, new THREE.MeshBasicMaterial({ color, side: THREE.BackSide }));
  hull.material.onBeforeCompile = (s) => {
    s.vertexShader = s.vertexShader.replace('#include <begin_vertex>', `vec3 transformed = position + normal * ${thickness.toFixed(4)};`);
  };
  mesh.add(hull);                                          // двигается вместе с мешем
  return hull;
}
export function canvasMatcap() {                           // matcap без файла; из Blender — рендер сферы в студии (A `05` §3.11)
  const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d');
  const g = x.createRadialGradient(96, 80, 10, 128, 128, 128);
  g.addColorStop(0, '#fff6e8'); g.addColorStop(0.5, '#e9965a'); g.addColorStop(1, '#5a2a1c');
  x.fillStyle = g; x.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshMatcapMaterial({ matcap: tex });
}
```
- Hull требует гладких нормалей: на острых рёбрах оболочка рвётся (расщеплённые нормали) — для hard-surface сглаживать нормали копии
  или брать Solidify из Blender (отрицательная толщина, flip normals, material offset — A `01` §21.3, в glTF с apply) [практика].
- `OutlinePass` (addons; + `RenderPass`, `OutputPass`) — контур выделения/hover, мягкий ореол; drei `<Outlines>` — тот же hull в R3F.
- Matcap: нет света и окружения — дешевле PBR, но вид не меняется при повороте модели (свет «прилип» к камере) [практика].

## 9. Пост-эффекты (§18)

```js
// three r186 + postprocessing 6.39.5 — [проверено: 99-raw/experiments/F2/05-fx-lab (?fx=post)] 18 вызовов, 1,9 мс
import * as THREE from 'three';
import * as P from 'postprocessing';
export function makePostLook(renderer, scene, camera) {
  renderer.toneMapping = THREE.NoToneMapping;                              // тонмаппинг — последним эффектом цепочки
  const composer = new P.EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType });
  composer.addPass(new P.RenderPass(scene, camera));
  // исправлено по T21 (CD/06): OVERLAY выбивал блики в 255 (0,07 — пересвет 3,9 %), SOFT_LIGHT 0,12 — «крапинка» в тёмных;
  // в проверенной цепочке CD зерно стоит после тона и LUT (15-showcase/_shared/code3d/src/post.js, 14-code-3d/05 п. 4)
  const noise = new P.NoiseEffect({ blendFunction: P.BlendFunction.SOFT_LIGHT, premultiply: false });
  noise.blendMode.opacity.value = 0.05;                                    // зерно слабое, поверх чистого кадра
  composer.addPass(new P.EffectPass(camera,                                // все эффекты сливаются в один проход
    new P.BloomEffect({ intensity: 1.4, luminanceThreshold: 0.6, mipmapBlur: true }),
    noise, new P.VignetteEffect({ darkness: 0.55 }), new P.ToneMappingEffect({ mode: P.ToneMappingMode.NEUTRAL })));
  return composer;                                                         // в цикле: composer.render() вместо renderer.render()
}
```
```css
/* CSS-зерно и виньетка поверх canvas — [проверено: F2/05 (?fx=post&css=1)] 0,63 мс против 1,9; bloom так не сделать */
.css-grain::after { content: ''; position: fixed; inset: 0; pointer-events: none; opacity: .12; mix-blend-mode: multiply;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
.css-grain::before { content: ''; position: fixed; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse at center, transparent 55%, rgba(20, 10, 40, .45) 100%); }
```
- Bloom срабатывает на пикселях ярче порога: в Blender — Emission Strength > 1 → `KHR_materials_emissive_strength` (E §6.1); на
  unlit-элементах без тонмаппинга — `toneMapped = false` (отчёт D2 §2).
- Зерно и glare — эффекты камеры, зерно только поверх чистого кадра [V:Z8AAX-ENWvQ 22:38, 23:50]; мерцание/глитч — не чаще 3 вспышек
  в секунду (WCAG 2.3.1). Пикселизация, ASCII, дизеринг — примеры three `webgl_postprocessing_pixel`, `webgl_effects_ascii` [не проверено].
- `postprocessing` 6.39.5 — peer three ≥ 0.168 < 0.187, только `WebGLRenderer`; v7 — beta 16; для WebGPU — TSL `RenderPipeline` + `bloom()`
  (F1 `01` §8) [документация npm].

## 10. Общая обвязка каждого эффекта

- Цикл: `renderer.setAnimationLoop(visible && !document.hidden && !reduce ? tick : null)`, при остановке — один `render()`; время —
  `THREE.Timer` (`timer.connect(document)` — пауза в скрытой вкладке) [проверено].
- Плотность — бюджетом пикселей холста (`../16-js-scenes/01-engine.md` §6): размытый фон — DPR ≤ 1; фон с деталью 1–2 px
  (точки, линии, решётки) и объект — DPR ≤ 2 под бюджетом 4,6 Мпикс ПК / 1,9 телефон; полноэкранный SDF без ограничивающего
  объёма — ½ (§2.5); пост — `HalfFloatType` буферы; сцене three.js с текстурами и MSAA на телефоне — DPR ≤ 1,5 ради памяти
  буферов (`01` §10). Сниженная плотность дала отзыв заказчика «модели нечёткие» [проверено] ПК, [кейс] телефон.
- Бюджет: эффект-накладка поверх страницы — ≤ 2 мс GPU на Iris Xe при 1440×900 (все эффекты таблицы §1, кроме полноэкранного
  SDF в полном разрешении, укладываются) [мнение F2 по замерам]. Сцена, которая занимает секцию целиком, — не накладка: одна
  живая сцена — медиана интервала кадров ≤ 17 мс (60 кадров/с) на эталонной встроенной графике, цена кадра желательно
  ≤ 8–10 мс, чтобы в 17 мс помещались две живые (`../16-js-scenes/01-engine.md`) [проверено].
- Запас: CSS-градиент/постер под canvas; `aria-hidden` у декоративного canvas; смысл — в HTML.
- Глобус cobe 2.0.1 (§17.1) в стенде не отрисовал карту точек (маркеры вне сферы, 0 перехваченных вызовов WebGL) — причину не искали
  [не проверено]; A замерил живой cobe.vercel.app: 5 КБ br, 6 вызовов (A `01` §17.1).

## Частые ошибки

- **`new THREE.Color(hex)` в `ShaderMaterial` без `#include <colorspace_fragment>`** — цвета темнее и насыщеннее hex (ΔE 9,55) [проверено].
- **`#include <colorspace_fragment>` в строке после кода** — директива не раскрывается (нужна отдельная строка) [проверено].
- **Маски шума с порогами «на глаз»** — половина палитры не проявляется; пороги у медианы fbm (≈ 0,44 для 3 октав) [проверено].
- **Полноэкранный raymarching без ограничивающего объёма в полном DPR** — ×6,6 цены; ½ разрешения, ≤ 64 шагов; SDF-объект
  в ограничивающем объёме — полное разрешение (§2.5) [проверено].
- **Потолок DPR вместо бюджета пикселей** — объект и фон с деталью 1–2 px мылятся, отзыв «модели нечёткие»; плотность —
  бюджетом пикселей (§10) [проверено].
- **Библиотечный фон с `minPixelRatio = 2`** на телефоне DPR 3 — лишние пиксели [проверено по коду].
- **Стекло на прозрачном canvas поверх HTML** — серый диск без преломления [проверено D2].
- **Смещение вершин без пересчёта нормали** — блоб освещён как исходная сфера.
- **Шейдер с Shadertoy «как есть»** — CC BY-NC-SA (некоммерческая) и sRGB-цвета без учёта цветового конвейера three [отчёт W7].
- **troika или другой addon с `+esm` CDN** — второй экземпляр three [проверено].
- **Пост-эффекты цепочкой отдельных проходов** вместо одного `EffectPass`; на телефоне больше 1–2 эффектов (A `01` §18).
- **Нейросеть по памяти**: `THREE.Clock`, `renderer.outputEncoding`, `THREE.Geometry`, `UnrealBloomPass` без `OutputPass` (r152+), `PostProcessing`
  (WebGPU, r183 → `RenderPipeline`) — таблица дрейфа A `03` §2.3.

## Чек-лист

- [ ] Эффект выбран по задаче (A `01` §1–§22), не клише §22 без причины?
- [ ] Цвета бренда: `THREE.Color` + `colorspace_fragment`; фон — `NoToneMapping`; ΔE пикселя к hex ≤ 1?
- [ ] Цена измерена: вызовы, мс/кадр при 1440×900 и на телефоне (`fx_probe.py --bench 120 --modes desktop,uncapped,mobile`)?
- [ ] Плотность: размытый фон — DPR ≤ 1; фон с деталью 1–2 px и объект — бюджетом пикселей (DPR ≤ 2, ≤ 4,6 / 1,9 Мпикс);
  полноэкранный SDF без объёма — ½, SDF-объект в объёме — полное разрешение; transmission `resolutionScale 0.5` на телефоне?
- [ ] reduce → один кадр; вне экрана и в скрытой вкладке цикл стоит (0 вызовов в покое)?
- [ ] Текст эффекта (SDF, частицы-логотип) продублирован HTML, canvas `aria-hidden`?
- [ ] Нет чужого кода с Shadertoy; формулы свои или из источников с разрешающей лицензией?
- [ ] Консоль: 0 ошибок, нет «Multiple instances of Three.js»?

## Открытые вопросы и противоречия

- `MeshTransmissionMaterial` против `MeshPhysicalMaterial` — цена по документации drei; свой замер не делался.
- GPGPU и WebGPU-compute частицы — без запуска; ориентиры числа частиц на телефоне — практика (Артюх, A), не замер.
- cobe 2.0.1 в headless-стенде не рисует карту — стенд или API 2.0 (маркеры как DOM?) — не выяснено.
- Stripe-вершинный вариант против фрагментного на телефонах с высокой плотностью пикселей — расчёт, не замер (реальных телефонов нет).
- Абсолютные мс на общей машине шумят в 1,5–3 раза (градиент 1,45–4,3 мс в разных прогонах); ранжирование устойчиво.

## Источники

- [S1] three.js r186: исходники `ShaderMaterial`/`ShaderChunk` (`colorspace_fragment`), `MeshSurfaceSampler`, `OutlinePass`, `WebGLRenderer.transmissionResolutionScale`;
  примеры `webgl_materials_physical_transmission`, `webgl_postprocessing_outline`, `webgl_gpgpu_birds`, `webgpu_compute_particles`,
  `webgl_materials_matcap` (кэш `99-raw/cache/three-r186-examples/`) — [документация; проверено].
- [S2] pmndrs/postprocessing 6.39.5 (npm, README через A; peer three < 0.187) — [документация].
- [S3] @paper-design/shaders 0.0.81: `dist/shader-mount.d.ts`, `shaders/mesh-gradient` (uniforms `u_colors`, `u_colorsCount`, `u_distortion`,
  `u_swirl`, `u_grainMixer`, `u_grainOverlay`) — [проверено: исходник].
- [S4] troika-three-text 0.52.5; drei `Text`, `Outlines`, `MeshTransmissionMaterial` docs 10.7.8 — [документация].
- [S5] Эксперименты F2: 04-shader-bg (+ `swatch_result.json`), 05-fx-lab (`shots/fx_sheet.png`, `fx_*.json`), 02-r3f-hero — [проверено].
- [S6] Ю. Артюх, «Stripe.com gradients with three.js» [V:LW9d2cqIHb4]; «История одной анимации» (РИТ++ 2019) [V:Eq_rXOyOX0I]; kishimisu,
  «An introduction to Shader Art Coding» [V:f4s1h2YETNY]; I. Quilez, «Painting a Character with Maths» [V:8--5LwHRhjk]; П. Мажуга, TSL
  (HolyJS 2025) [V:EQ5m0Jhz-qs] — заметки `99-raw/notes/wave2/F2-video-B.md`, `F2-video-C.md`.
- [S7] Отчёты W3 (стекло, зерно [V:MFzmj1TUEKk, V:Z8AAX-ENWvQ]), W4 (дешёвое стекло `BackSide` [V:H1oNuKChsdU]), W7 (§4 цвет uniform, §8 →F2:
  Shadertoy CC BY-NC-SA, дизеринг), D2 (§2: стекло на прозрачном canvas, `toneMapped = false`) — 23.09.2026.
- [S8] E `../08-export-gltf/01` §6 (стекло, дисперсия, иридесценция из Blender), §4.8 (текст) — [проверено E].
- [S9] A `../01-web-3d-landscape/01-effects-catalog.md` (§ эффектов, клише §22), `05` §3.8, §3.11 — [проверено A].
