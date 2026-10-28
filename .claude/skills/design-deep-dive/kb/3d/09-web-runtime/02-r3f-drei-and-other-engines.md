# React Three Fiber 9 + drei 10 и другие движки: когда что брать и как агент встраивает модель из Blender

Волна 2 · агент F2 · 23.09.2026 · источников: 14 (документация R3F и drei с GitHub, исходники drei/three-stdlib/three в
node_modules, npm-реестр, статья arXiv 2601.05016, заметки по 11 роликам) · экспериментов: 5 (`99-raw/experiments/F2/01`,
`02`, `03`, `07`, `05`) · версии: three r186 (0.186.0), @react-three/fiber 9.8.0, @react-three/drei 10.7.8, react 19.3.0,
three-stdlib 2.36.1, PlayCanvas 2.22.3, Babylon.js 9.27.1, model-viewer 4.3.1, gltfjsx 6.5.3, Chromium 153 headless (Iris Xe).
Ядро three (загрузка, цвет, тени, пост, память) — `01-threejs-core.md` (F1); цикл отрисовки, бюджеты, доступность, запасные
варианты — `05-performance-a11y-fallbacks.md` (F1); обзор рынка движков и веса бандлов — `../01-web-3d-landscape/03-runtime-landscape.md` (A).

## Выжимка для агента

1. **React в проекте есть → R3F 9.8 + drei 10.7.8; нет → vanilla three r186.** R3F-чанк hero-сцены — 293 КБ br (three 727 КБ min + react-dom 205 + fiber 165 + three-stdlib 101), TBT 496–757 мс на десктопе против 172 мс у vanilla-паттерна A/07 → React ради одного 3D-блока не тянуть → §1. [проверено]
2. **Грузи R3F-сцену отдельным чанком** динамическим `import()` после `load` и в простое (`requestIdleCallback`) по `IntersectionObserver`; H1, текст и CTA — в HTML: LCP 156 мс = текст, CLS 0 → §4. [проверено]
3. **Меняй дефолты `<Canvas>`**: ACES (по умолчанию) → `gl={{ toneMapping: THREE.NeutralToneMapping }}` (пара с Blender «Khronos PBR Neutral» — `01-threejs-core.md` §5), `dpr={[1, 2]}` → `[1, 1.5]`, `shadows` не включать без нужды (даёт `PCFSoftShadowMap`, в r186 удалённый — three подменяет его на `PCFShadowMap` с предупреждением) → §2.1. [проверено: F2/02 — `gl.toneMapping` = 7; документация R3F Canvas]
4. **reduce → `frameloop="demand"`** и выключенные `Float`/контролы: 0 вызовов отрисовки в покое, 0 % движения; в обычном режиме — стоп вне экрана `setFrameloop('never')` по `IntersectionObserver` → §2.2. [проверено]
5. **Анимация — мутацией ref в `useFrame((state, delta) => …)`**, не `setState`; плавность — `THREE.MathUtils.damp(x, y, λ, delta)`: пример из документации R3F «`lerp(x, target, 0.1)` в useFrame» зависит от частоты (на 144 Гц в 2,4 раза быстрее) → §2.3, `03-scroll-interaction-animation.md` §4. [проверено: 99-raw/experiments/F2/06-anim-damp; документация R3F pitfalls]
6. **`useGLTF` drei грузит загрузчиком three-stdlib 2.36.1, а не three r186**: нет `KHR_meshopt_compression`, `KHR_materials_variants`, `KHR_animation_pointer`, `KHR_gaussian_splatting` → gltfpack с `-ce khr` ломает загрузку («Invalid typed array length»); оставляй умолчание `-ce ext` или грузи `useLoader(GLTFLoader из three/addons)` → §3.1. [проверено]
7. **Draco у `useGLTF` по умолчанию с CDN gstatic 1.5.5, пресеты `<Environment preset>` — с raw.githack** («not meant for production»): в продакшене — свои пути (`useGLTF(url, '/draco/')`) и свои файлы или `<Lightformer>` (0 КБ) → §3.2. [документация drei; проверено исходником]
8. **Окружение для продукта без файлов** — `<Environment resolution={256}>` c 3–4 `<Lightformer>`: снимается кубокамерой один раз, даёт студийные блики клиркоута → §4. [проверено]
9. **Статичные тени — `<ContactShadows frames={1}>`** (иначе рендер тени каждый кадр) или `<AccumulativeShadows>` (0 цены после накопления) → §3.2. [документация drei; проверено: F2/02]
10. **В drei нет ни одной проверки `prefers-reduced-motion`** (поиск по исходникам 10.7.8): `Float`, `PresentationControls`, `ScrollControls`, `MeshWobble/Distort` двигаются всегда — агент сам передаёт `speed={0}`, `enabled={false}`, `damping` → §3.3. [проверено: исходники drei]
11. **`ScrollControls` заменяет нативную прокрутку своим контейнером** (pages, damping 0,2 с): годится для полноэкранной сцены-истории, не для обычного лендинга с HTML-контентом → бери GSAP ScrollTrigger + Lenis (`03` §1) → §3.2. [документация drei; практика]
12. **`MeshTransmissionMaterial` = доп. проход сцены на каждый материал** (samples 6, буфер полноэкранный по умолчанию); ставь `resolution={256…512}` или `transmissionSampler` (общий буфер three); на телефоне — 1 объект → §3.2, `04` §3. [документация drei]
13. **gltfjsx 6.5.3 превращает GLB из Blender в JSX-компонент** (имена узлов сохраняются, `useAnimations` подключается сам); поза в JSX = кадр 0 экспорта; `userData` из `extras` — только с `--meta`; `--transform` сливает меши и материалы (ломает поиск по именам) → §3.4. [проверено: gltfjsx на сцене F2/03]
14. **События R3F — рейкаст по мешам** (`onPointerOver/Out/Click`), `stopPropagation` отсекает объекты позади; для hover без движения мыши при движении камеры — `events.update()` → §2.4. [документация R3F events]
15. **WebGPU в R3F 9.8** — `gl={async (props) => { const r = new WebGPURenderer(props); await r.init(); return r; }}` + `extend(THREE)` из `three/webgpu`: работает и на откате WebGL2, 400 КБ br, два предупреждения внутри R3F (`THREE.Clock`, `PCFSoftShadowMap`) → §2.5. [проверено]
16. **Предупреждение `THREE.Clock: This module has been deprecated` в R3F 9.8 — внутреннее** (`state.clock`), не ошибка кода страницы; в своём коде — `THREE.Timer` → §2.1. [проверено]
17. **Витрина товара + AR без кода** — model-viewer 4.3.1 отдельным скриптом (peer three ^0.183 конфликтует с r186 в одном бандле); AR и USDZ — у F1 (`06-…`) → §5.1. [документация; проверено A: npm ERESOLVE]
18. **PlayCanvas 2.22 встраивается ESM-модулем за 20 строк**, но GLB после gltfpack (`EXT_meshopt_compression`) не читает без явного декодера; для лендинга тяжелее three (393 КБ br) → §5.3. [проверено]
19. **Babylon.js 9 — только ES-модули через бандлер** (665 КБ br с glTF): `+esm` jsDelivr падает на CORS, полная UMD — 8,6 МБ по сети; в стенде UMD-вариант после загрузки не рисовал (не выяснено) → §5.2. [проверено частично]
20. **Needle Engine** — связка Blender/Unity-компонентов с three, но коммерция только по Pro-лицензии, `npm i` ставит альфу 6.0 → `@needle-tools/engine@stable` (5.1.13); **Spline** — дизайнерский рантайм 834 КБ br, MCP только в десктопе macOS/Windows → агенту на Linux — свой GLB + three → §5.4–5.5. [документация; A/03]
21. **«Живое превью» Blender ↔ R3F через WebSocket** (arXiv 2601.05016) агенту не нужно: превью в обход экспорта показывает не то, что приедет в GLB; проверка — экспорт → страница в headless → скриншоты и числа → §6. [мнение F2 на основе исследования]

## 1. Выбор: R3F, vanilla three или готовый движок

| Ситуация | Стек | Вес JS (brotli) | Что проверено |
|---|---|---|---|
| Сайт на React/Next, 3D — часть UI (витрина, конфигуратор, несколько сцен) | R3F 9.8 + drei 10.7.8 | 249 (Canvas + mesh) … 293 (hero с drei) … 345 (+пост, MTM, Text) | F2/02: 293 КБ; A/03 |
| Сайт без фреймворка, один hero или история на прокрутке | three r186 vanilla + GSAP/Lenis | 109–160 (бандлер), 361 по сети с jsDelivr `*.min.js` | A/03, A/07, F2/03 |
| Витрина + AR без своего кода | `<model-viewer>` 4.3.1 (свой three 0.183 внутри) | 230–240 | A/03 |
| Приложение/редактор, «всё в одном», команда знает движок | Babylon 9 или PlayCanvas 2 | 665 / 393 | A/03, F2/07 |
| Сцена из Unity/Blender с компонентами и логикой | Needle Engine 5 (`@stable`) | 311 + 209 | A/03 (не проверено здесь) |
| Дизайнер собирает в редакторе, разработчика нет | Spline | 834 (+ физика 419) | A/03 |

Правила выбора:
- React уже на сайте → R3F: компонентный код, готовые решения drei, `Suspense` для загрузки; цена — ≈ 140 КБ br react-dom +
  fiber и `import * as THREE` в каталоге R3F (tree-shaking three хуже: 727 КБ min против 522 у vanilla) [проверено: F2/02 meta.json; A/03].
- Без React → vanilla: меньше JS, меньше долгих задач (TBT hero: R3F 496–757 мс, vanilla A/07 172 мс на десктопе; CPU×4 —
  765 против 369 мс) [проверено].
- Vue/Svelte → TresJS/Threlte (A `03` §9), не R3F.
- Автор R3F: R3F — реконсилер React для three, а не набор обёрток, поэтому не отстаёт от three [V:YyqBdN71nFs 04:42];
  DOM — для типографики и вёрстки, GPU — для остального [V:YyqBdN71nFs 20:51]. [мнение автора]

## 2. R3F 9.8: что важно агенту

### 2.1. `<Canvas>`: дефолты и что менять
Дефолты (документация Canvas): `WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })`,
`outputColorSpace = SRGBColorSpace`, `toneMapping = ACESFilmicToneMapping` (`flat` → `NoToneMapping`), камера
`{ fov: 75, near: 0.1, far: 1000, position: [0, 0, 5] }`, `dpr = [1, 2]`, `frameloop = 'always'`, `shadows: true` →
`PCFSoftShadowMap`, `fallback` — DOM при отсутствии WebGL [документация R3F].

| Проп | Ставить | Почему |
|---|---|---|
| `gl={{ toneMapping: THREE.NeutralToneMapping }}` | всегда для продукта | ACES сдвигает брендовый цвет; проверено: проп перекрывает дефолт (`gl.toneMapping` = 7) [F2/02] |
| `dpr={[1, 1.5]}` | всегда | телефон Pixel 7: холст 568×355 при CSS 379×237 [F2/02] |
| `frameloop` | `'demand'` для статики и при reduce; `'always'` при постоянном движении | §2.2 |
| `camera={{ fov: 30–35, position }}` | по кадрированию | 75° — «рыбий глаз» для продукта; кадрирование — `<Center>` + дистанция |
| `shadows` | не включать без нужды | `PCFSoftShadowMap` в r186 удалён (подмена на `PCFShadowMap` с предупреждением); контактная тень дешевле |
| `onCreated={({ gl }) => gl.domElement.setAttribute('aria-hidden', 'true')}` | декоративный canvas | доступность — F1 `05` §5 |
| `fallback={<img …>}` | при нужде | постер, если WebGL не создан |

### 2.2. Рендер по требованию, reduce, стоп вне экрана
- `frameloop="demand"`: кадр только при смене пропов; мутации вне React (контролы, свои анимации) — `invalidate()`; drei-контролы
  вызывают его сами; `invalidate()` — флаг, несколько вызовов = один кадр; для синхронной анимации — сначала `invalidate()`, затем
  старт в `requestAnimationFrame` [документация R3F scaling-performance].
- `Float` в `demand` рисует только с `autoInvalidate` [документация drei].
- Стоп вне экрана и в скрытой вкладке: `setFrameloop('never')` из `useThree` по `IntersectionObserver` и `visibilitychange`,
  при возврате — прежний режим + `invalidate()` (код §4) [проверено].
- Регрессия качества при движении: `performance={{ min: 0.5 }}` + `regress()` + `<AdaptiveDpr pixelated />`; адаптация к FPS —
  `<PerformanceMonitor onDecline onIncline flipflops={3} onFallback>` (замер 250 мс × 10 итераций, порог 0,75, bounds по частоте
  экрана) [документация drei/R3F]. Не проверено здесь.

### 2.3. `useFrame` и частые значения
- `useFrame((state, delta) => { ref.current.rotation.y += delta * 0.6 })` — мутация по ref, `delta` в секундах; `setState` в
  `useFrame` и в быстрых событиях — ре-рендер React каждый кадр (антипаттерн документации R3F pitfalls) [документация].
- Документация R3F рядом с «используй дельты» показывает «✅ `THREE.MathUtils.lerp(x, target, 0.1)` в useFrame» — это
  frame-rate-зависимо: при 144 Гц объект через 0,25 с проходит 97,7 % пути против 79,4 % при 60 Гц; правильная форма —
  `damp(x, target, λ, delta)` (λ = −ln(1 − k)·60) [проверено]. Реальный антипример: поворот логотипа «0.2 за кадр» на
  экране 142 Гц крутится в ~2,3 раза быстрее задуманного [V:vmqMt8U8l6Y 25:48].
- Не создавай объекты в `useFrame` (`new Vector3` 60 раз в секунду → сборщик мусора) — переиспользуй [документация R3F].
- Прокрутку и курсор храни в ref/uniform, не в состоянии React (Shopify Editions; A `03` §3.1) [практика].
- `useFrame(cb, 1)` (приоритет > 0) забирает рендер у R3F — нужно для своих композеров; отрицательные приоритеты только
  упорядочивают [документация].

### 2.4. События и имена узлов из Blender
- Меши с `onClick`, `onPointerOver/Out/Move`: событие несёт `object`, `point`, `distance`, `intersections`; сначала ближайший
  объект, затем его предки, затем следующий объект; `e.stopPropagation()` отсекает объекты позади; `onPointerMissed` — клик мимо
  [документация R3F events].
- Hover при движущейся камере (прокрутка) без движения мыши не пересчитывается → `useThree(s => s.events).update()` в
  `useFrame`, когда изменилась `camera.matrixWorld` [документация].
- Поиск по имени: `const { nodes } = useGLTF(url)` → `nodes.ring_1`; имена из Blender санитизируются (`Cube.001` → `Cube001`) —
  называть `латиница_через_подчёркивание` (E `08-export-gltf/01` §10); после gltfpack с квантованием меш — ребёнок узла с именем
  (`01-threejs-core.md` §11) [проверено].
- Рейкаст по сотням мешей дорог (CPU): кликабельное — отдельные невидимые увеличенные hit-области [V:5uTwZVGgDpA 26:10],
  у Bruno Simon — сферы вместо треугольников [V:EhZwt9P4GP4 15:01] [практика].

### 2.5. WebGPU и дрейф v8 → v9
- WebGPU: код и замеры — A `03` §3.1 и `99-raw/experiments/A/08-webgpu-fallback` (оба бэкенда рисуют одинаково; 400 КБ br).
- v8 → v9 (документация Migration Guide): `useLoader(new GLTFLoader(), url)` принимает экземпляр; `extend(OrbitControls)` возвращает
  компонент; `gl={(props) => new WebGLRenderer(props)}` вместо `gl={(canvas) => …}`; снята авто-sRGB текстур из пропов (для своих
  шейдеров `texture.colorSpace = THREE.SRGBColorSpace`); `Props` → `CanvasProps`; `MeshProps` удалён → `ThreeElements['mesh']`;
  StrictMode наследуется от react-dom.
- Устаревшее в роликах 2020–2023: пакет `react-three-fiber` → `@react-three/fiber`; `<HTML>` → `<Html>`; `ReactDOM.render` →
  `createRoot`; `ambientLight intensity 1` для запечённого света после r155 темнее — лучше unlit-материал [V:YyqBdN71nFs; V:pXpckHDDNYo 03:13].
- В npm уже есть R3F 10.0.0-alpha.5 и drei 11.0.0-alpha.7 — по тегу `latest` ставится 9.8 / 10.7.8; peer R3F 9.8: `react ≥ 19 < 19.4`
  (react 19.3.0 на 23.09) [проверено: npm view, F2/01].

## 3. drei 10.7.8: что брать для лендинга

### 3.1. `useGLTF` и загрузчик
- `useGLTF(url, useDraco = true, useMeshOpt = true, extendLoader)`; `useGLTF.preload(url)`; Draco по умолчанию — CDN
  `https://www.gstatic.com/draco/versioned/decoders/1.5.5/`, свой путь — вторым аргументом или `useGLTF.setDecoderPath` [документация drei].
- Исходник 10.7.8: `import { GLTFLoader, DRACOLoader, MeshoptDecoder } from 'three-stdlib'` — загрузчик three-stdlib 2.36.1 (ноябрь
  2025), а не three r186. Разница в расширениях (сравнение исходников): только в three r186 — `KHR_meshopt_compression`,
  `KHR_materials_variants` (плагин), `KHR_animation_pointer` (плагин), `KHR_gaussian_splatting` [проверено: исходники].
- Проверка: `gltfpack -cc -ce khr` → `KHR_meshopt_compression` → drei: «Could not load …: Invalid typed array length: 28800»;
  `-cc` (по умолчанию `EXT_meshopt_compression`) → грузится; three r186 `GLTFLoader` читает оба файла [проверено].
- KTX2 — через `extendLoader`: `loader.setKTX2Loader(new KTX2Loader().setTranscoderPath('/basis/').detectSupport(gl))` [документация drei].
- Нужен загрузчик three r186 (варианты материалов, KHR meshopt) → `useLoader(GLTFLoader, url, (l) => l.setMeshoptDecoder(MeshoptDecoder))`
  с импортом из `three/addons/…` [не проверено запуском; API useLoader — документация R3F].

### 3.2. Компоненты: что даёт, сколько стоит, ловушки
| Компонент | Для чего | Цена и ловушки |
|---|---|---|
| `<Environment preset>` / `files` / дети | `scene.environment` для PBR | пресеты тянутся с raw.githack.com — «not meant for production»; `.hdr` читает `RGBELoader` three-stdlib (в r186 у three — `HDRLoader`); дети (`<Lightformer>`) рендерятся кубокамерой один раз (`frames` 1), 0 КБ [документация; проверено F2/02] |
| `<Lightformer form="rect|ring" intensity scale position>` | студийные софтбоксы в окружении | блики на клиркоуте и металле без HDRI [проверено] |
| `<ContactShadows opacity scale blur far resolution frames={1}>` | мягкая тень под объектом | без `frames={1}` — рендер глубины каждый кадр («rather expensive») [документация] |
| `<AccumulativeShadows temporal frames={100}>` + `<RandomizedLight>` | мягкие тени и AO на полу | после накопления 0 цены [документация] |
| `<Float speed rotationIntensity floatIntensity floatingRange autoInvalidate>` | «дыхание» героя | reduce не учитывает — `speed={0}`; с `demand` только `autoInvalidate` [документация; проверено F2/02] |
| `<PresentationControls global snap polar azimuth config enabled>` | вращение модели мышью с пружиной (mass 1, tension 170, friction 26) и возвратом | вращает содержимое, не камеру; `enabled={!reduce}` [документация; проверено F2/02] |
| `<Center>` | центр габарита модели в 0 | без него модель из Blender «сидит» по origin сцены [проверено F2/02] |
| `<ScrollControls pages damping maxSpeed>` + `useScroll()` (`offset`, `delta`, `range`, `curve`, `visible`) + `<Scroll html>` | история на прокрутке внутри canvas | свой HTML-контейнер прокрутки вместо нативного: текст страницы внутри `<Scroll html>`; для лендинга с HTML-контентом — GSAP + Lenis (`03` §1) [документация; практика] |
| `<MeshTransmissionMaterial samples resolution thickness chromaticAberration anisotropicBlur transmissionSampler backside>` | стекло «лучше MeshPhysical» (видит прозрачные объекты, хроматическая аберрация) | доп. проход сцены на каждый материал; при шероховатости — `resolution={32}`; общий буфер — `transmissionSampler` или `buffer={useFBO().texture}` [документация] |
| `<Text font characters>` (troika) | SDF-текст в сцене | шрифт woff/ttf; `characters` против мигания; текст дублирует HTML (`04` §6) [документация; проверено troika в F2/05] |
| `<Sampler>` / `useSurfaceSampler` | точки на поверхности меша | для частиц — `04` §4 [документация] |
| `<Outlines thickness color screenspace>` | контур inverted hull | удваивает треугольники; дешевле пост-контура (`04` §7) [документация; проверено принцип в F2/05] |
| `<Html occlude transform>` | DOM-метки у 3D-точек | 1 DOM-узел на метку; `occlude="blending"` — дороже [документация] |
| `<Preload all />`, `<BakeShadows />` | компиляция шейдеров заранее, заморозка shadow map | снимает рывок первого появления [документация] |
| `<AdaptiveDpr pixelated />`, `<PerformanceMonitor>` | адаптация качества | §2.2 [документация] |

### 3.3. reduce в drei — ответственность агента
Поиск `matchMedia|reduced` по исходникам drei 10.7.8 — 0 совпадений [проверено]. Всё, что двигается само (`Float`,
`MeshWobbleMaterial`, `MeshDistortMaterial`, `Sparkles`, `Cloud`, `ScrollControls` с `damping`), нужно выключать пропами при
`prefers-reduced-motion: reduce`; хук и компоненты — в коде §4. Lenis уважает reduce сам (`respectReducedMotion: true`), drei — нет.

### 3.4. gltfjsx: GLB из Blender → JSX-компонент
- `npx gltfjsx@6.5.3 model.glb -o Model.jsx` → компонент с `useGLTF`, `<mesh name geometry material position rotation>` на каждый
  узел, `useAnimations` при наличии клипов; флаги: `-t` типы, `-k` исходные имена, `-m` `userData` (extras), `-i`/`-I` инстансинг
  повторов, `-s` тени, `-T` трансформация (Draco, prune, текстуры 1024 WebP, слияние мешей `-j` и материалов `-M` отключаемо),
  `-S` упрощение [проверено: `--help` 6.5.3].
- На сцене F2/03 (18 объектов, клип сборки): 39 строк, имена `ring_N`, `hotspot_N`, `slab_N` сохранены, пустышки стали `<group>`
  с позицией, подключён `useAnimations`; позиции в JSX = поза кадра 0 экспорта (разлёт плит) — анимация должна управляться
  явно [проверено: gltfjsx на `99-raw/experiments/F2/03-camera-path/out/scene.glb`].
- Не запускай `-T` для ассетов, где JS ищет узлы по имени или читает `extras`: слияние мешей и материалов ломает адресацию
  (то же у gltf-transform `optimize` — E `04` §7); сжатие — gltfpack `-cc -kn -ke` (F2/03: 421 → 33 КБ, имена и extras целы).
- Последний релиз gltfjsx — 2024-11 (6.5.3) [проверено: npm view]; генерированный код использует `useGLTF` drei (ограничения §3.1).

## 4. Эталон: R3F-hero

```jsx
// R3F 9.8 + drei 10.7.8 + three r186 — [проверено: 09-web-runtime/examples/r3f-hero (тот же код + служебный Probe для замера)]
import { createRoot } from 'react-dom/client';
import { Suspense, useEffect, useState } from 'react';
import * as THREE from 'three';
import { Canvas, useThree } from '@react-three/fiber';
import { useGLTF, Center, Environment, Lightformer, ContactShadows, Float, PresentationControls } from '@react-three/drei';

const reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');
function useReducedMotion() {
  const [reduce, setReduce] = useState(reduceMQ.matches);
  useEffect(() => {
    const on = () => setReduce(reduceMQ.matches);
    reduceMQ.addEventListener('change', on);
    return () => reduceMQ.removeEventListener('change', on);
  }, []);
  return reduce;
}

// стоп рендера вне экрана и в скрытой вкладке; при возврате — прежний режим и один кадр
function PauseWhenHidden({ mode }) {
  const { gl, setFrameloop, invalidate } = useThree();
  useEffect(() => {
    let visible = true;
    const apply = () => { setFrameloop(visible && !document.hidden ? mode : 'never'); invalidate(); };
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; apply(); });
    io.observe(gl.domElement);
    document.addEventListener('visibilitychange', apply);
    apply();
    return () => { io.disconnect(); document.removeEventListener('visibilitychange', apply); };
  }, [gl, mode, setFrameloop, invalidate]);
  return null;
}

function Model() {
  const { scene } = useGLTF('./sculpture.glb');           // EXT_meshopt_compression (не -ce khr, §3.1)
  return <Center><primitive object={scene} /></Center>;
}

function Hero() {
  const reduce = useReducedMotion();
  const mode = reduce ? 'demand' : 'always';
  return (
    <Canvas frameloop={mode} dpr={[1, 1.5]} camera={{ position: [0, 0.15, 2.3], fov: 30 }}
      gl={{ toneMapping: THREE.NeutralToneMapping }}
      onCreated={({ gl }) => gl.domElement.setAttribute('aria-hidden', 'true')}>
      <PauseWhenHidden mode={mode} />
      <Suspense fallback={null}>
        <PresentationControls global snap polar={[-0.15, 0.25]} azimuth={[-0.7, 0.7]} enabled={!reduce}>
          <Float speed={reduce ? 0 : 1.4} rotationIntensity={reduce ? 0 : 0.35} floatIntensity={reduce ? 0 : 0.5}>
            <Model />
          </Float>
        </PresentationControls>
        <ContactShadows position={[0, -0.335, 0]} opacity={0.5} scale={3} blur={2.4} far={1} resolution={256} frames={1} color="#3b2f5a" />
        <Environment resolution={256}>
          <Lightformer form="rect" intensity={3} position={[0, 4, -3]} scale={[8, 3, 1]} />
          <Lightformer form="rect" intensity={1.5} position={[-4, 1, 1]} rotation-y={Math.PI / 2} scale={[4, 6, 1]} />
          <Lightformer form="rect" intensity={1} position={[4, 0.5, 2]} rotation-y={-Math.PI / 2} scale={[4, 4, 1]} color="#ffe2c4" />
          <Lightformer form="ring" intensity={2} position={[0, 2, 4]} scale={2} />
        </Environment>
      </Suspense>
    </Canvas>
  );
}

export function mount(el) { createRoot(el).render(<Hero />); }
```

Страница подключает чанк так (HTML-первый экран, место под canvas с `aspect-ratio`, CSS-градиент — запас):
```html
<!-- three r186 / R3F 9.8 — [проверено: 09-web-runtime/examples/r3f-hero/index.html] -->
<div class="hero" id="hero"></div>
<script type="module">
const hero = document.getElementById('hero');
const io = new IntersectionObserver((es) => {
  if (!es.some((e) => e.isIntersecting)) return;
  io.disconnect();
  const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 200));
  const go = () => idle(async () => { const { mount } = await import('./hero.js'); mount(hero); }, { timeout: 2000 });
  if (document.readyState === 'complete') go(); else addEventListener('load', go, { once: true });
}, { rootMargin: '200px' });
io.observe(hero);
</script>
```
Сборка чанка: `esbuild src/Hero.jsx --bundle --minify --format=esm --jsx=automatic --define:process.env.NODE_ENV='"production"'`.

| Режим (Chromium 153, Iris Xe) | 1-й кадр | Вызовов/кадр в покое | Мс/кадр GPU | TBT | Итог |
|---|---|---|---|---|---|
| десктоп 1440×900 | 666 мс | 3 | 2,05 (880×550) | 496 мс | узел с клиркоутом, мягкая тень |
| `web_view.py --page` | — | 3 (60 fps прокрутки) | — | 757 мс | LCP 156 мс = текст, CLS 0 |
| Pixel 7 + CPU×4 | 1 115 мс | 3 | 1,74 (568×355, DPR 1,5) | 765 мс | — |
| reduce | 610 мс | **0** | — | 289 мс | статичный кадр |
[проверено: 99-raw/experiments/F2/02-r3f-hero, таблица полностью — `examples/r3f-hero/README.md`]

Первая версия кадрировала модель мелко и низко (модель из Blender с origin пьедестала) — исправлено `<Center>` и дистанцией камеры
2,3 м при FOV 30° (модель ≈ 45 % высоты кадра).

## 5. Другие движки: когда и как встраивать

### 5.1. model-viewer 4.3.1 — витрина и AR без своего кода
- Веб-компонент: `src`, `poster`, `alt`, `loading="lazy"`, `camera-controls`, `auto-rotate`, `tone-mapping` (по умолчанию `neutral`
  с 4.0), `environment-image`, `ar ar-modes="webxr scene-viewer quick-look"`, варианты `variant-name`, аннотации `slot="hotspot-*"`,
  `camera-orbit` с `env(window-scroll-y)` — орбита от прокрутки без JS [документация; A `03` §6].
- peer three ^0.183 → в одном бандле с r186 ERESOLVE; подключать готовый `model-viewer.min.js` (230 КБ br) отдельным скриптом
  [проверено]. AR, USDZ, Scene Viewer — F1 `06-…` и его демо `model-viewer-ar`.
- Когда: товар, e-commerce, нет 3D-разработчика. Когда нет: свои шейдеры, прокрутка-история, несколько объектов с логикой.

### 5.2. Babylon.js 9 — приложения и конфигураторы
- Вес: ядро 209 КБ br, с glTF и `createDefaultEnvironment` — 665 КБ br (ES-модули поимпортно, бандлер) [проверено].
- Проверка F2/07: `import … from 'https://cdn.jsdelivr.net/npm/@babylonjs/core@9.27.1/+esm'` — CORS-ошибка, 75 запросов / 3,4 МБ;
  UMD официального CDN (`cdn.babylonjs.com/babylon.js` + `loaders/babylonjs.loaders.min.js`) — 8,6 МБ по сети, GLB загрузился
  (4 меша, камера по габариту `createDefaultCameraOrLight`), но в headless-стенде кадры после загрузки не рисовались (0 вызовов,
  заставка Babylon не ушла и с `hideLoadingUI()`) — причина не найдена [проверено частично].
- Для кода агента — бандлер и именованные импорты [не проверено запуском в F2]:
```js
// Babylon.js 9.27 — [не проверено: сборка поимпортно по A/03 entries/babylon-gltf.js; рендер в стенде F2/07 не подтверждён]
import { Engine } from '@babylonjs/core/Engines/engine';
import { Scene } from '@babylonjs/core/scene';
import { AppendSceneAsync } from '@babylonjs/core/Loading/sceneLoader';
import '@babylonjs/loaders/glTF/2.0';
import '@babylonjs/core/Helpers/sceneHelpers';
const canvas = document.querySelector('canvas');
const engine = new Engine(canvas, true);
engine.setHardwareScalingLevel(1 / Math.min(devicePixelRatio, 1.5));   // аналог setPixelRatio
const scene = new Scene(engine);
await AppendSceneAsync('/model.glb', scene);
scene.createDefaultCameraOrLight(true, true, true);
scene.createDefaultEnvironment({ createGround: false, createSkybox: false });
engine.runRenderLoop(() => scene.render());
```
- Когда: редакторы, конфигураторы, игровая логика, инспектор, сплаты (PLY/SPLAT/SPZ/SOG), команда знает Babylon; когда нет —
  лендинг (в 4–6 раз тяжелее three) [A `03` §4].

### 5.3. PlayCanvas 2.22 — движок + облачный редактор, сильные сплаты
```js
// PlayCanvas 2.22.3 — [проверено] 2 вызова, 1-й кадр 3,3 с (CDN), 0 ошибок
import * as pc from 'https://cdn.jsdelivr.net/npm/playcanvas@2.22.3/+esm';
const canvas = document.querySelector('canvas');
const app = new pc.Application(canvas, { graphicsDeviceOptions: { antialias: true } });
app.setCanvasFillMode(pc.FILLMODE_FILL_WINDOW); app.setCanvasResolution(pc.RESOLUTION_AUTO);
app.graphicsDevice.maxPixelRatio = Math.min(devicePixelRatio, 1.5);
app.start();
const cam = new pc.Entity('cam'); cam.addComponent('camera', { clearColor: new pc.Color(0.93, 0.91, 0.96), fov: 35 });
cam.setPosition(0, 0.35, 2.4); app.root.addChild(cam);
const light = new pc.Entity('light'); light.addComponent('light', { type: 'directional', intensity: 1.5 });
light.setEulerAngles(45, 30, 0); app.root.addChild(light);
app.scene.ambientLight = new pc.Color(0.45, 0.45, 0.5);
const asset = await new Promise((res, rej) => app.assets.loadFromUrl('model_raw.glb', 'container', (e, a) => (e ? rej(e) : res(a))));
const model = asset.resource.instantiateRenderEntity(); app.root.addChild(model);
cam.lookAt(0, 0.2, 0);
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
app.on('update', (dt) => { if (!reduce.matches) model.rotate(0, 20 * dt, 0); });
```
- GLB после gltfpack (`EXT_meshopt_compression`) — ошибка «Invalid typed array length: 93312»: декодер meshopt в PlayCanvas надо
  подключать явно (как именно — не проверено); несжатая GLB 346 КБ — грузится [проверено].
- Вес: 393 КБ br в бандле, 602 КБ по сети ESM с jsDelivr [проверено]; тег npm `lts` = старая ветка 1.77 — код
  нейросетей «по памяти» часто v1 (`pc.Application` со старыми скриптами) [A `03` §5].
- Когда: сплаты как главное содержимое (SOG, потоковый LOD), редакторный конвейер, игры; когда нет — простой hero.

### 5.4. Needle Engine — Blender/Unity-компоненты на three
- Экспорт сцен с компонентами (физика, анимационные машины состояний, сеть, WebXR) из Unity и Blender (аддон), прогрессивная
  загрузка LOD; npm `latest` = 6.0.0-alpha.3, стабильная — `npm i @needle-tools/engine@stable` (5.1.13); лицензия в npm не указана;
  Hobby — только некоммерческое (логотип, 1 проект, хостинг в Needle Cloud), коммерция — Pro €49/место/мес. [документация; A `03` §7].
- Для агента-кодогенератора: свой экспорт GLB (E) + three даёт тот же результат без лицензии и без аддона; Needle — если заказчик
  уже работает в Unity/Needle [мнение F2]. Код не проверялся (нужна лицензия и собственный конвейер Needle).

### 5.5. Spline — рантайм дизайнерских сцен
- `@splinetool/runtime` 2.0.55 (лицензии в npm нет): `new Application(canvas).load('https://prod.spline.design/…/scene.splinecode')`;
  React — `@splinetool/react-spline` 4.1.0 (последний релиз 2025-07); 834 КБ br + `physics.wasm` 419 КБ; на spline.design — 192 вызова
  в покое, на телефоне полный DPR 2,625 и TBT 1,9 с [проверено A: A/03, замер сайтов].
- Экспорт кода в three/R3F: анимации и события — только Vanilla JS и React-рантайм; Spline MCP — только в десктоп-приложении
  macOS/Windows → агенту на Linux недоступен [документация Spline; A `03` §8]. Код не проверялся (нужна сцена на prod.spline.design).
- Когда: сцену делает дизайнер в Spline; агент только встраивает и проверяет вес/draw calls/reduce (`05` F1 §7).

## 6. «Живое превью» Blender ↔ R3F: нужно ли агенту

Работа Gao, Juluri (arXiv 2601.05016, 2026): Planner–Actor–Critic поверх Blender-MCP; двусторонний WebSocket-канал обменивается
геометрией, светом и текстурами между Blender и фронтендом на Next.js + React Three Fiber; агенты на CopilotKit/LangGraph, базовая
модель GPT-4.1; критик оценивает сцену по состоянию и скриншотам; оценка — качественная (примеры), без чисел [исследование,
прочитаны разделы 3–4]. Для нашей системы: превью в обход экспорта показывает не то, что приедет на страницу (модификаторы,
процедурные материалы, имена — E `01`), а агенту «смотреть» всё равно нужно скриншотами. Надёжный цикл — идемпотентный скрипт
Blender → экспорт по пресету → gltfpack → страница в headless (`web_view.py --page`, `99-raw/experiments/F2/00-tools/fx_probe.py`) →
скриншоты и числа; WebSocket-превью оправдано только для человека-соавтора [мнение F2].

## Частые ошибки

- **Нейросеть по памяти**: `import { Canvas } from 'react-three-fiber'`, `gl={(canvas) => new WebGLRenderer({ canvas })}`, `MeshProps`,
  `<HTML>`, `ReactDOM.render` — всё v7–v8; в 9.x — `@react-three/fiber`, `gl={(props) => …}`, `ThreeElements['mesh']`, `<Html>`,
  `createRoot` [документация v9].
- **`setState` в `useFrame` и в `onPointerMove`** — ре-рендер React каждый кадр; `lerp(x, t, 0.1)` без `delta` — скорость зависит от
  герцовки экрана [документация; проверено F2/06].
- **ACES по умолчанию у `<Canvas>`** — брендовый цвет «уплывает»; `dpr [1, 2]` — полный DPR на телефоне.
- **`<Environment preset="city">` в продакшене** — внешний CDN raw.githack, может упасть; свои файлы или `<Lightformer>`.
- **gltfpack `-ce khr` + drei `useGLTF`** — «Invalid typed array length» [проверено].
- **`<ContactShadows>` без `frames={1}` у статичной модели** — рендер глубины каждый кадр.
- **drei-анимации при reduce** — `Float`, `Wobble`, `Sparkles` продолжают двигаться; drei reduce не проверяет [проверено].
- **gltfjsx `-T` на ассете с логикой по именам** — меши и материалы слиты, `nodes.ring_1` исчезает.
- **model-viewer и three r186 в одном `package.json`** — ERESOLVE (peer ^0.183) [проверено A].
- **`npm i @needle-tools/engine`** — ставит 6.0.0-alpha.3 [проверено A, F2/01].
- **Babylon с `+esm` jsDelivr** — CORS и 75 запросов [проверено F2/07].

## Чек-лист

- [ ] Стек выбран по §1 (React есть → R3F; нет → vanilla three; витрина+AR → model-viewer)?
- [ ] R3F-сцена — отдельный чанк после LCP, HTML-первый экран, место под canvas зарезервировано?
- [ ] `<Canvas gl={{ toneMapping: NeutralToneMapping }} dpr={[1, 1.5]}>`, `shadows` только при нужде?
- [ ] reduce → `frameloop="demand"`, `Float speed={0}`, контролы выключены; вне экрана — `setFrameloop('never')`?
- [ ] Анимации в `useFrame` через ref и `delta`/`damp`, без `setState`?
- [ ] `useGLTF`: GLB без `KHR_meshopt_compression`, свои пути Draco/KTX2, `useGLTF.preload`?
- [ ] Окружение — свои файлы или `<Lightformer>`, не `preset` с CDN?
- [ ] Консоль: 0 ошибок; предупреждение `THREE.Clock` от R3F 9.8 — допустимо, своих `deprecated` нет?
- [ ] Вес чанка ≤ 300 КБ br (R3F) и TBT измерен (`web_view.py --page`, `fx_probe.py --modes mobile`)?

## Открытые вопросы и противоречия

- Документация R3F (pitfalls) советует `lerp(x, target, 0.1)` в `useFrame` и одновременно «use deltas» — противоречие внутри
  документации; позиция базы — `damp` с `delta` [проверено F2/06].
- Babylon UMD в headless-стенде не рисует после загрузки GLB (0 вызовов) — не выяснено, особенность стенда или кода; код §5.2 —
  по A/03 без запуска.
- Подключение декодера meshopt в PlayCanvas 2.22 не проверено.
- R3F 10 (alpha) и drei 11 (alpha) — что изменится (WebGPU по умолчанию? отказ от `THREE.Clock`?) — не изучалось.
- Needle и Spline — только документация и замеры A, без своего запуска.
- TBT R3F-чанка 496–757 мс измерен на общей машине (разброс между прогонами до 1,5 раза); на реальных телефонах не мерили.

## Источники

- [S1] pmndrs/react-three-fiber, docs: API/canvas, API/hooks, API/events, advanced/pitfalls, advanced/scaling-performance,
  tutorials/v9-migration-guide (raw GitHub, master; 32 429★, push 2026-09-22) — [документация], кэш `99-raw/cache/pmndrs/`.
- [S2] pmndrs/drei, docs 10.7.8: useGLTF, Environment, Lightformer, ContactShadows, AccumulativeShadows, Float, PresentationControls,
  ScrollControls, MeshTransmissionMaterial, Text, Sampler, useSurfaceSampler, Outlines, Html, AdaptiveDpr, PerformanceMonitor,
  Preload, BakeShadows, Center (9 886★, push 2026-09-21) — [документация].
- [S3] Исходники `@react-three/drei` 10.7.8 (core/Gltf.js, core/useEnvironment.js), `three-stdlib` 2.36.1 и `three` 0.186.0
  (GLTFLoader) в `$DDD_HOME/node` — [проверено].
- [S4] npm registry, 23.09.2026 (`99-raw/experiments/F2/01-npm-registry/npm_view_2026-09-23.txt`) — версии, теги, peer, лицензии.
- [S5] Агент A: `../01-web-3d-landscape/03-runtime-landscape.md` §3–8, эксперименты A/03 (бандлы), A/07 (vanilla hero), A/08
  (R3F + WebGPU) — [проверено A].
- [S6] Эксперименты F2: 02-r3f-hero, 03-camera-path (gltfjsx), 06-anim-damp, 07-engines — [проверено].
- [S7] J. Gao, S. Juluri, «From Idea to Co-Creation: A Planner–Actor–Critic Framework for Agent Augmented 3D Modeling», arXiv
  2601.05016 (2026) — архитектура Blender-MCP + WebSocket + R3F; [исследование, качественная оценка].
- [S8] gltfjsx 6.5.3 (`npx gltfjsx --help`, запуск на сцене F2/03) — [проверено].
- [S9] Needle, «Pricing & Plans» (кэш A `needle.tools_pricing_…`); Spline docs «Exporting as Code», «Spline MCP Server» (кэш A) —
  через A `03` §7–8 [документация].
- [S10] model-viewer 4.x docs (через A `03` §6 и F1) — [документация].
- [S11] Видео (заметки `99-raw/notes/wave2/F2-video-A.md`, `F2-video-C.md`): P. Henschel «Bringing WebGL to React» (ReactEurope 2020)
  [V:YyqBdN71nFs]; Wawa Sensei «R3F Scroll Animations» (2023) [V:pXpckHDDNYo]; Б. Борбеков «Как я делал 3D-сайт» (HolyJS 2024)
  [V:vmqMt8U8l6Y]; И. Тельтевский «Пять приёмов» (FrontendConf 2023) [V:5uTwZVGgDpA]; B. Simon, Devlog 13 [V:EhZwt9P4GP4].
