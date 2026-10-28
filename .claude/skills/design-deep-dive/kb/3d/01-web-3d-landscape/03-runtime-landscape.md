# Движки и библиотеки веб-3D и стек по умолчанию для агента

Снимок: 28.10.2026 — версии, релизы за год и вес; доля WebGPU — caniuse от 22.10.2026; звёзды и push GitHub — 22.09.2026.
Версии — реестр npm: three 0.186.1 (r186; r187 — на выходе), @react-three/fiber 9.8.2 (альфа 10.0.0-alpha.6),
@react-three/drei 10.7.9, postprocessing 6.39.5, @react-three/postprocessing 3.2.2, @babylonjs/core 9.32.1, playcanvas
2.23.3, @google/model-viewer 4.4.0, @needle-tools/engine 5.1.16 (`stable`) и 6.0.0-alpha.7 (`latest`),
@splinetool/runtime 2.0.114, gsap 3.15.0, lenis 1.3.27, motion 14.7.1, @theatre/core 0.7.2. Вес — сборка минимальной
сцены (esbuild, ESM, minify, brotli q11). Весь спектр способов делать 3D на JavaScript, место сцены (холст, остров
Astro, React) и первоисточники снимка — `06-js-stack.md`.

## Выжимка для агента

1. **Стек по умолчанию**: объект, фон, частицы и мир из правил — **свой движок на WebGL2** (`../16-js-scenes/01-engine.md`); модель GLB на сайте без фреймворка — **three 0.186.1 vanilla** (`WebGLRenderer`, `GLTFLoader` + Meshopt/Draco/KTX2, бандлер); React/Next — **R3F 9.8 + drei 10.7**; простая витрина с AR — **model-viewer 4.4**; без интерактива — **предрендер/видео из Blender** → §12; весь спектр и место сцены — `06-js-stack.md` §2. [проверено: A/03, A/07, A/08; замер: three на 27 из 33 сайтов]
2. three.js — де-факто стандарт веб-3D: 27 из 33 наградных сайтов, 115 764★, релиз каждые 1–2,5 мес. (12 стабильных за 12 мес.); ревизии в продакшене — от r141 до r186 → §2. [проверено]
3. three **ломает API почти каждый релиз**: r180 `RGBELoader`→`HDRLoader`, r183 `Clock`→`Timer` и `PostProcessing`→`RenderPipeline`, r182 `PCFSoftShadowMap` устарел, r186 удалён в обоих рендерерах (предупреждение и `PCFShadowMap`), r185 `positionLocal` не учитывает скиннинг, r186 `Source`→`TextureSource`, r187 — PMREM на кубических целях (`CubeUVReflectionMapping` удалён), неявное приведение типов в TSL, `setViewport()`/`setScissor()` без DPR при привязанной цели → сверяйся с Migration Guide, а не с памятью → §2.3. [документация]
4. r186 **удалил минифицированные сборки** (`build/*.min.js`) и объявил CommonJS устаревшим → бандлер (esbuild/Vite) или автоминификация jsDelivr (`three.module.min.js` 90 КБ br — только с ключом import map `three.core.js` → `three.core.min.js` 104 КБ br, иначе тянет неминифицированное ядро 204 КБ br; `../09-web-runtime/01-threejs-core.md` §1.2) → §2.1. [документация; проверено: A/03]
5. `WebGPURenderer` + TSL в r186 — рабочий путь с автоматическим откатом на WebGL2: один и тот же TSL-материал проверен на обоих бэкендах (картинки совпали); manual three при этом зовёт `WebGPURenderer` экспериментальным, а `WebGLRenderer` — рекомендованным для чистого WebGL2. TSL идёт и на `WebGLRenderer` через `WebGLNodesHandler` (r184+), но с весом WebGPU-сборки: 201,8 против 108,9 КБ br у GLSL-патча → §2.2. [проверено; документация]
6. Выбирай WebGPU/TSL, когда нужны compute-частицы (100 тыс.+), сплаты three (`GaussianSplat` требует `WebGPURenderer`), TSL-эффекты r184+; иначе `WebGLRenderer` — меньше (108,5 против 173,1 КБ br) и вся экосистема pmndrs/postprocessing работает только с ним → §2.2. [проверено; документация]
7. WebGPU у пользователей: 85,8 % + 3,66 % частично (caniuse), по реальным адаптерам — 83,2 % (web3dsurvey: Linux 18 %, Android 75 %): Chrome/Edge 113+, Chrome Android 12+ (121), Chrome Linux — Intel Gen12+ (144) и NVIDIA на Wayland (147), iOS Safari 26+, Samsung 24+; Safari macOS — только Tahoe (26); Firefox — Windows (141) и macOS на Apple Silicon (145/147), Linux и Android — нет; в режиме совместимости (`featureLevel: 'compatibility'`, Android с OpenGL ES 3.1 с Chrome 146) three выключает MSAA → фолбэк обязателен → §2.2, `06-js-stack.md` §3. [данные; документация; исходник]
8. Всегда `await renderer.init()` у `WebGPURenderer` перед `render()` вне `setAnimationLoop` (с r181 async-методы `renderAsync` устарели) → §2.2. [документация; проверено: A/08]
9. R3F 9.8.2: React 19 (**peer: react ≥ 19 < 19.4**), async-фабрика `gl` для WebGPU, `useLoader(loaderInstance)`, типы `ThreeElements['mesh']` вместо `MeshProps`; DPR сам пересчитывается при переносе окна и зуме; с three r186 выдаёт 2 предупреждения (внутри `THREE.Clock` и `PCFSoftShadowMap`), но работает. R3F 10 — альфа (10.0.0-alpha.6): `WebGPURenderer` по умолчанию, `WebGLRenderer` — входом `'@react-three/fiber/legacy'`, проп `gl` на основном входе бросает ошибку, TSL-хуки — в @react-three/tsl (только альфа) → в продакшен — 9.8.2 → §3. [документация; проверено: A/08]
10. R3F стоит ≈ 140 КБ br сверх three (react-dom + fiber) и мешает tree-shaking three: сцена R3F 9 — 250,5 КБ br, + drei — 288,2, + пост — 361,4; R3F 10 с WebGPU по умолчанию — 392,9 КБ br → на лендинге без React не тянуть React ради 3D → §3. [проверено]
11. drei 10.7.9 закрывает большинство эффектов каталога готовыми компонентами (Environment, ContactShadows, Float, MeshTransmissionMaterial, Text, ScrollControls, Sampler, PerformanceMonitor, AdaptiveDpr, Instances, Splat…); ветка 11.0 — альфа со входом `/webgpu` → §3.2. [документация]
12. pmndrs `postprocessing` 6.39.5 (Zlib) — peer **three ≥ 0.168 < 0.187** и только `WebGLRenderer`: с выходом r187 `npm i three@latest postprocessing` даст ERESOLVE → держать `three@0.186.1` в паре; ветка v7 (7.0.0-beta.16) — peer `three < 0.184`, с r186 не ставится, WebGPU не заявлен → для WebGPU — пост на TSL (`RenderPipeline`, `bloom()` и т. п.) → §3.3. [данные: npm; документация]
13. Babylon.js 9 (9.32.1) — полный движок (Apache-2.0) с очень частыми релизами (138 за 12 мес.), сплаты (PLY/SPLAT/SPZ/SOG), Frame Graph, объёмный свет; WebGL-куб — 209,8 КБ br, WebGPU-движок с откатом — 266,5, **669,9 КБ br** с glTF и окружением → выбирать для приложений/конфигураторов, не для лендинга → §4. [документация; проверено]
14. PlayCanvas 2.23 (MIT) — движок + облачный редактор + лучший стек сплатов (SOG в 15–20 раз меньше PLY, compute-рендер WebGPU ×2 fps на iPhone); 404,5 КБ br → §5. [документация; проверено]
15. model-viewer 4.4.0 — веб-компонент «витрина + AR» за 229,9 КБ br (готовая сборка); **peer three ^0.183** (внутри 0.183.2; с r186 в одном бандле — ERESOLVE) → подключать его готовую сборку отдельно; тон по умолчанию Khronos PBR Neutral; AR Quick Look — и в сторонних браузерах iOS без `ios-src` → §6. [документация; проверено]
16. Needle Engine: бесплатный план только некоммерческий (логотип, 1 проект, только Needle Cloud), коммерция — Pro €49/место/мес.; **`npm i @needle-tools/engine` ставит 6.0.0-alpha.7** (стабильная — тег `stable` 5.1.16) → §7. [документация; данные: npm]
17. Spline: удобен дизайнеру, но рантайм 843,2 КБ br (2.0.114; + physics.wasm 419,3 КБ br), 192 draw calls в покое на spline.design; файл AGENTS.md пакета: адрес `.splinecode` даёт только экспорт редактора, `wasmPath` по умолчанию — CDN, водяной знак зашит в данные сцены; экспорт в three/R3F (анимации и события — только Vanilla JS/React); **Spline MCP — только в десктоп-приложении macOS/Windows** → агенту на Linux недоступен → §8.3. [проверено; документация]
18. OGL (12,1 КБ br) — для одного шейдера без three; но релизов и коммитов нет больше полутора лет → для каталога эффектов «только шейдер» проще свой WebGL2 (0,7 КБ br у SDF-примера, `06-js-stack.md` §1) или `@paper-design/shaders` (5,5 КБ br в минимальном бандле esbuild; на странице через jsDelivr — 119 КБ JS, F2 `../09-web-runtime/04-shaders-effects-catalog-impl.md` §2.4; 21 релиз за 12 мес.) — оба без three → §9. [проверено]
19. Vue — TresJS 5.10 (peer vue ≥ 3.4; WebGPU — эксперимент), Svelte 5 — Threlte 8.6.1; обе обёртки над three, живые (21 и 27 релизов/12 мес.) → §9. [данные: npm]
20. A-Frame 1.8 (276 КБ br) — WebXR-декларативка; на npm 12 не ставится без разрешения git-зависимостей (`three-bmfont-text` из GitHub → EALLOWGIT) → не выбирать для лендинга → §9. [проверено]
21. Прокрутка: GSAP 3.15 + ScrollTrigger (40,4 КБ br) + Lenis 1.3.27 (4,9 КБ br); связка — `lenis.on('scroll', ScrollTrigger.update); gsap.ticker.add(t => lenis.raf(t * 1000)); gsap.ticker.lagSmoothing(0)` → §10. [документация; проверено: A/03]
22. Лицензия GSAP (Webflow, с 30.04.2025): бесплатно, включая коммерцию и все плагины (SplitText, MorphSVG), **но запрещено** использовать в no-code-конструкторах анимаций, конкурирующих с Webflow; код GSAP, сгенерированный ИИ, прямо разрешён → для системы генеративного дизайна как продукта — юридическая проверка → §10.1. [документация; спорно]
23. Lenis: пакет `@studio-freight/lenis` устарел (переименован в `lenis`); `respectReducedMotion: true` по умолчанию; в Safari не больше 60 fps (30 в энергосбережении) → §10.2. [документация npm/README]
24. Theatre.js: npm 0.7.2 (05.2024), публичный репозиторий не обновлялся с 08.2024, `@theatre/studio` — AGPL-3.0 → для новых проектов не выбирать; анимацию камеры делать в Blender или GSAP → §10.3. [документация; проверено: A/02]
25. `framer-motion-3d` помечен на npm «Package no longer supported»; Motion 14 — только DOM/SVG → 3D-анимация не через Motion → §10.4. [документация npm]
26. Библиотека сплатов для three: Spark (`@sparkjsdev/spark` 2.4.0, World Labs, 782,2 КБ br вместе с three; LoD, SPZ v4) — живая; `@mkkellogg/gaussian-splats-3d` без релизов больше полутора лет; в three r186 свои `GaussianSplat` + `KHR_gaussian_splatting` (только WebGPURenderer, 216,6 КБ br); не путать Spark (сплаты) и spark.js (Ludicon, сжатие текстур) → §9. [проверено; документация three]
27. Нейросеть лучше всего «знает» three и GSAP (огромный корпус), но именно там больше всего устаревшего кода; model-viewer и Lenis — стабильный API, мало риска; R3F v8→v9, PlayCanvas v1→v2 (тег `lts` 1.77) и Needle — высокий риск старого API; TSL, `RenderPipeline` и R3F 10 — самый тонкий и быстро меняющийся слой → §11; корпус кода по маркерам — `06-js-stack.md` §4.1. [мнение A на основе Migration Guide и npm]
28. Перед генерацией кода агент проверяет: `npm view <пакет> version dist-tags peerDependencies`, Migration Guide three для версий выше своих знаний, и прогоняет страницу в headless (0 ошибок консоли, есть draw calls; в отчёте — `backend` и `isFallbackAdapter`); `tsc` с @types/three той же версии ловит удалённое API → §11. [практика; проверено: A/07, A/08]

## 1. Сводная таблица

| Пакет | Версия | Назначение | Лицензия | Релизов за 12 мес. | ★ / push | Бандл, КБ br (минимальная сцена) | glTF | WebGPU |
|---|---|---|---|---|---|---|---|---|
| three | 0.186.1 | движок (сцена, рендер, лоадеры) | MIT | 12 | 115 764 / 2026-09-22 | 108,5 (куб), 158,2 (GLTF + декодеры), 173,1 (webgpu), 198,5 (webgpu + TSL + bloom), 201,8 (TSL на WebGL) | полный, KHR_* материалы, Draco/Meshopt/KTX2, сплаты | `WebGPURenderer` + TSL, откат WebGL2; TSL на `WebGLRenderer` — `WebGLNodesHandler` |
| @react-three/fiber | 9.8.2 (альфа 10.0.0-alpha.6) | React-рендерер three | MIT | 9 | 32 423 / 2026-09-22 | 250,5 (с react-dom и three); R3F 10 — 392,9 | через three | async `gl`; в 10 — WebGPU по умолчанию |
| @react-three/drei | 10.7.9 (альфа 11.0.0-alpha.7) | компоненты R3F | MIT | 3 | 9 883 / 2026-09-21 | 288,2 (+OrbitControls, useGLTF, Environment) | useGLTF, KTX2 | частично; в 11 — вход `/webgpu` |
| @react-three/postprocessing / postprocessing | 3.2.2 / 6.39.5 | постобработка | MIT / Zlib | 8 / 10 | 1 390 / 2 860 | +12 (three + Bloom/Noise/Vignette = 120) | — | нет (и в v7-бете не заявлен) |
| @babylonjs/core (+loaders) | 9.32.1 | полный движок | Apache-2.0 | 138 | 26 094 / 2026-09-21 | 209,8 (WebGL-куб), 266,5 (WebGPU-движок с откатом), 669,9 (с glTF и окружением), 1448 (`import *`) | полный | да, WebGPU и WebGL2 |
| playcanvas | 2.23.3 | движок (+ редактор) | MIT | 57 | 16 886 / 2026-09-22 | 404,5 | полный, сплаты SOG | да |
| @google/model-viewer | 4.4.0 | веб-компонент витрины и AR | Apache-2.0 | 4 | 8 254 / 2026-07-07 | 229,9 (готовая сборка, внутри three 0.183.2); 116,9 (модуль без three) | glTF/GLB, Draco/KTX2/Meshopt по требованию | нет (WebGL) |
| @needle-tools/engine | 5.1.16 stable / 6.0.0-alpha.7 latest | движок + экспорт из Unity/Blender | коммерческая (Hobby — некоммерч.) | 53 версии | — | 311 + 209 (three-core, сборка 5.1.13) | glTF + расширения Needle | — |
| @splinetool/runtime | 2.0.114 | рантайм сцен Spline | не указана в npm | 225 версий | 1 421 (react-spline) | 843,2 (+ physics.wasm 419,3) | импорт/экспорт GLB, свой .splinecode | по умолчанию WebGPU с откатом |
| ogl | 1.0.11 | минимальный WebGL | Unlicense | 0 (последний 2025-01) | 4 655 / 2025-04-13 | 12,1 | базовый | нет |
| @threlte/core | 8.6.1 | Svelte-обёртка three | MIT | 27 | 3 342 | — | через three | через three |
| @tresjs/core | 5.10.0 | Vue-обёртка three | MIT | 21 | 3 736 | — | через three | эксперимент |
| aframe | 1.8.0 | декларативный WebXR/3D | MIT | 1 | 17 635 / 2026-07-13 | 276 (dist min) | через three | — |
| gsap (+ScrollTrigger) | 3.15.0 | анимация, прокрутка | Standard «No Charge» (Webflow) | 4 | 28 567 | 40,4 | — | — |
| lenis | 1.3.27 | плавная прокрутка | MIT | 14 | 15 959 | 4,9 | — | — |
| @theatre/core / studio | 0.7.2 | таймлайн-анимация | Apache-2.0 / AGPL-3.0 | 0 (2024-05) | 12 693 / 2024-08-14 | — | — | — |
| motion | 14.7.1 | DOM/SVG-анимация | MIT | 85 | 33 693 | 22 | — | — |
| @sparkjsdev/spark | 2.4.0 | сплаты для three | MIT | 6 | 3 647 | 782,2 (с three) | — | — |
| @paper-design/shaders | 0.0.82 | шейдерные фоны | Apache-2.0 | 21 | 3 471 | 5,5 | — | — |
| cobe | 2.0.1 | точечный глобус | MIT | 2 | 5 888 | 5,4 | — | — |
| troika-three-text | 0.52.5 | SDF-текст | MIT | 2 | 1 972 | 143,5 (с three) | — | нет: PR #393 не влит |
| @pmndrs/detect-gpu | 6.0.28 | уровень GPU | MIT | 29 | 1 213 | 3,4 (+ JSON бенчмарков) | — | — |
Источник: реестр npm (`npm view`, 96 пакетов) и сборки минимальной сцены (esbuild ESM minify, brotli q11) [проверено];
★ / push — GitHub, день — в строке «Снимок». «Релизов» — стабильных версий за 365 дней до снимка.

## 2. three.js r186

### 2.1. Состояние и сборка
- `latest` в npm — патч 0.186.1; r187 — на выходе: веха назначена на день снимка, ломающее уже описано в Migration
  Guide 186→187 (таблица §2.3) [данные: npm, GitHub; документация].
- Релизы: r186 2026-09-08, r185 07-01, r184 04-16, r183 02-20, r182 2025-12-10, r181 11-19, r180 09-03 — каждые 1–2,5
  месяца [документация: GitHub releases].
- Состав пакета r186: `build/three.module.js` (обёртка), `three.core.js`, `three.webgpu.js`, `three.webgpu.nodes.js`,
  `three.tsl.js`, `three.cjs`; **минифицированные сборки удалены** (#33893), **CommonJS устарел** (#33891); addons —
  `examples/jsm/` (импорт `three/addons/...`) [проверено: пакет 0.186.0].
- Размер: неминифицированные `three.module.js` + `three.core.js` = 102 + 204 КБ br; jsDelivr-автоминификация
  `three.module.min.js` + `three.core.min.js` = 90 + 104 КБ br (только если import map переназначает `three.core.js` на `three.core.min.js`: min-модуль импортирует `./three.core.js` — 204 КБ br, F1/01); `three.webgpu.js` = 316 КБ br; бандлер с именованными
  импортами — 109 КБ br (куб), 158 КБ br (GLTF + декодеры + OrbitControls + RoomEnvironment) [проверено].
- Документация: новая JSDoc-документация с r181 (только английский), manual, 607 примеров (files.json), «TSL Guide»,
  «llms build» документации [документация].

### 2.2. WebGLRenderer, WebGPURenderer, TSL
- `WebGLRenderer` — зрелый путь; весь каталог эффектов реализуем; экосистема (pmndrs/postprocessing, большинство
  drei) — для него.
- `WebGPURenderer` (`import * as THREE from 'three/webgpu'`) — рендерер с бэкендами WebGPU и **WebGL2 (автоматический
  откат)**; материалы — node-материалы (`MeshStandardNodeMaterial` и др.), шейдеры — **TSL** (`three/tsl`: `color`, `mix`,
  `uv`, `positionLocal`, `time`…), компилируется в WGSL и GLSL. Пометка «wip» с WebGPU-примеров снята в r186
  [документация].
- Проверено (A/08): TSL-материал с `colorNode` и `positionNode` рисует одинаково на WebGPU и на откате WebGL2; при
  откате в консоли «THREE.WebGPURenderer: WebGPU is not available, running under WebGL2 backend.»; первый кадр в
  headless-стенде — 4,4 с WebGPU против 1,2 с WebGL2 (компиляция пайплайнов; 1 прогон) [проверено].
- Правила: `await renderer.init()` до `render()` вне `setAnimationLoop` и до `KTX2Loader.detectSupport(renderer)`
  (r181: async-методы устарели); `outputBufferType` вместо `colorBufferType` (r182); `RenderPipeline` вместо
  `PostProcessing` (r183); в r185 изменена премультипликация альфы — задавать непрозрачный фон, если не нужен прозрачный
  canvas [документация: Migration Guide].
- Позиция manual three: `WebGPURenderer` — в экспериментальном состоянии, хотя зрелость сильно выросла; `WebGLRenderer`
  — рекомендованный выбор для чистого WebGL2, крупных новых функций в нём не будет; под `WebGPURenderer` не работают
  `ShaderMaterial`, `RawShaderMaterial`, `onBeforeCompile()`, `EffectComposer` [документация: manual three]. Статьи
  «готов к продакшену с r171» и «рекомендован с r182» этим не подтверждаются [мнение; спорно].
- TSL на `WebGLRenderer` — `WebGLNodesHandler` (r184, PR #32851): `renderer.setNodesHandler(new WebGLNodesHandler())`;
  не поддержаны VSM, MRT, transmission, WebGPU-пост и storage-текстуры; вес — 201,8 против 108,9 КБ br у GLSL-патча:
  путь миграции одним кодом, а не экономия; в headless рисует [исходник; проверено] → `06-js-stack.md` §1.1.
- Режим совместимости: `WebGPUBackend` просит адаптер с `featureLevel: 'compatibility'`; без
  `core-features-and-limits` — `compatibilityMode = true` и `renderer._samples = 0`: MSAA выключен, `antialias: true`
  молча не действует → сглаживание узлом `fxaa()` или `smaa()` [исходник: three 0.186.1]. Chrome 146 открыл режим
  совместимости на Android с OpenGL ES 3.1 [документация].
- Откат по требованию — PR #34334 (открыт): WebGL2-бэкенд отдельным чанком `'three/webgpu/fallback'`, сборка WebGPU
  легче на 24,3 КБ gzip [документация; не проверено — войдёт ли в r187].
- Только в WebGPURenderer: compute (частицы/физика на GPU), `GaussianSplat` и `GLTFGaussianSplatLoaderExtension`
  (`KHR_gaussian_splatting`, регистрировать вручную), OIT (`OITPassNode`), VXGI, новый SSAO/DOF/объёмный туман на TSL,
  `LightProbeGrid` (WebGPU-версия) [документация: r186 release notes].
- Поддержка WebGPU (caniuse, день — в строке «Снимок»): 85,8 % полная + 3,66 % частичная; по реальным адаптерам —
  83,21 % (web3dsurvey: Linux 18 %, Android 75 %); Chrome/Edge 113+, Opera 99+, Samsung 24+, Chrome Android 12+ (с 121),
  iOS Safari 26+; Safari macOS — только macOS 26 Tahoe; Firefox — Windows (141) и macOS на Apple Silicon (145 на
  macOS 26+, 147 — на всех); Firefox Linux и Android — нет; Chrome Linux — Intel Gen12+ (144) и NVIDIA на Wayland (147);
  Россия — 81,3 % отслеживаемого трафика, но 30,4 % трафика caniuse не видит [данные; документация] →
  `06-js-stack.md` §3.1.
  PlayCanvas приводит «≈ 85 % пользователей» [документация вендора].
- Когда WebGPU: compute-частицы 100 тыс.+ (PlayCanvas: сплаты 35 млн — 75,8 против 13,3 fps на M4 Max; 1 млн на iPhone
  13 Pro Max — 77,6 против 38,1) [замеры вендора], сплаты three, TSL-эффекты. Когда WebGL: лендинг/hero/витрина —
  меньше JS (108,5 против 173,1 КБ br), быстрее первый кадр в стенде, вся экосистема [проверено].

### 2.3. Дрейф API: что нейросеть напишет по памяти и как правильно (r150 → r187)
| По памяти (старое) | С какой версии иначе | Правильно в r186–r187 |
|---|---|---|
| `renderer.outputEncoding = THREE.sRGBEncoding`, `texture.encoding` | r152 | `renderer.outputColorSpace = THREE.SRGBColorSpace`, `texture.colorSpace` |
| `renderer.physicallyCorrectLights = true` / `useLegacyLights` | r155 (физичный свет по умолчанию), позже удалено | ничего не задавать; интенсивности в физических единицах |
| `BoxBufferGeometry`, `THREE.Geometry` | удалены (r125/r144) | `BoxGeometry`, `BufferGeometry` |
| `material.skinning = true`, `morphTargets = true` | удалены | не нужно |
| `new RGBELoader()` | r180 | `HDRLoader` (RGBELoader — наследник с предупреждением) |
| `RGBMLoader` | r180 удалён | `EXRLoader`, `HDRLoader`, `UltraHDRLoader` |
| `new THREE.Clock()` | r183 устарел | `new THREE.Timer()` + `timer.update()` каждый кадр (Timer в ядре с r179) |
| `PostProcessing` (WebGPU) | r183 | `RenderPipeline` |
| `renderer.shadowMap.type = PCFSoftShadowMap` | r182 устарел, r186 удалён в `WebGLRenderer` и `WebGPURenderer` (предупреждение, подмена на `PCFShadowMap`; F1/01) | `PCFShadowMap` (теперь мягкий) |
| `await renderer.renderAsync()` | r181 устарел | `await renderer.init()` один раз, затем `render()` |
| `KTX2Loader.detectSupportAsync()` | r181 | `detectSupport(renderer)` после `init()` |
| TSL `PI2`, `label()`, `directionToColor()` | r181, r179, r185 | `TWO_PI`, `setName()`, `packNormalToRGB()` |
| `CapsuleGeometry(radius, length)` | r176 | `CapsuleGeometry(radius, height)` |
| `ColorManagement.fromWorkingColorSpace()` | r177 | `workingToColorSpace()` |
| `reverseDepthBuffer: true` | r179 | `reversedDepthBuffer: true` |
| `USDZLoader` | r179 устарел | `USDLoader` |
| `Source` (текстуры) | r186 | `TextureSource` |
| `SimplifyModifier.modify()` синхронно | r186 | async, реализация на meshoptimizer |
| `LightProbeGrid` | r186 | `LightProbeGridWebGL` (имя освобождено под WebGPU-версию) |
| `FileLoader.load()` возвращает значение | r184 | только колбэк `onLoad` |
| FBX Z-up поворачивать вручную | r184 | FBXLoader сам переводит Z-up → Y-up |
| `positionLocal` в `positionNode` для скиннинга | r185 | `positionGeometry` |
| свой класс с `dispose()` без `super.dispose()` | r186 (`Object3D.dispose()`) | в своём `dispose()` звать `super.dispose()` |
| `GTAONode`: `distanceExponent`, `distanceFallOff` | r186 устарели и на AO не влияют | не задавать: модель расстояния у `GTAONode` своя |
| `BufferGeometryUtils.toTrianglesDrawMode()` отдаёт копию | r186: индекс меняется на месте | нужна исходная геометрия — `clone()` до вызова |
| униформ `up` у `Sky` / `SkyMesh` | r186 удалён | не задавать: вверх всегда +Y |
| `CubeUVReflectionMapping`, PMREM на старой раскладке | r187 удалён: PMREM на кубических рендер-таргетах | ничего не задавать; материалы выглядят чуть иначе — пересверить кадр |
| математика TSL на операндах разных типов | r187: операнды и параметры неявно приводятся к более широкому общему типу | пересверить формулы и кадр, где важен тип (целые, `float` против `vec3`) |
| `WebGLRenderer.setViewport()` / `setScissor()` умножают на pixel ratio всегда | r187: при привязанном рендер-таргете — не умножают | размеры для рендер-таргета — в его пикселях |
| `pixelationPass()` с узлом в `pixelSize` | r187 | `pixelSize` — только число |
| `renderer.library.addLight(CustomLightNode, CustomLight)` | r187 | `CustomLight.registerNode(CustomLightNode)` |
| `storage(buffer, Struct).get('member')` | r187: struct-хранилище — всегда массив | `storage(buffer, Struct).element(0).get('member')` |
| `iridescenceThicknessRange` | r187 устарел | `iridescenceThicknessMinimum`, `iridescenceThicknessMaximum` |
Источник: Migration Guide (wiki mrdoob/three.js, разделы 175→187), release notes r186, пакет 0.186.0 (RGBELoader,
Clock `@deprecated since 183`, предупреждение PCFSoftShadowMap проверены в коде) [документация; проверено]. Каталог
дрейфа Blender-стороны — `../03-bpy-api/03-version-drift-3.6-to-5.2.md`.

## 3. React Three Fiber 9, drei 10, постобработка

### 3.1. R3F 9.8
- v9 — совместимость с React 19; peer: `react ≥ 19 < 19.4`, `three ≥ 0.156` [документация npm]. Изменения (v9 Migration
  Guide): `useLoader(new GLTFLoader(), url)` принимает экземпляр; `extend(Class)` возвращает компонент;
  `gl={(props) => new WebGLRenderer(props)}` (раньше — canvas); **`gl` может вернуть промис → WebGPU**; снята
  автоматическая sRGB-конвертация текстур из пропов (для своих шейдеров — `texture.colorSpace = SRGBColorSpace`);
  `Props`→`CanvasProps`, `MeshProps` удалён → `ThreeElements['mesh']`; StrictMode наследуется [документация].
- R3F 9.8.2: DPR сам пересчитывается при переносе окна на другой монитор и зуме (проп `dpr` его перезаписывает)
  [документация]. R3F 10.0.0-alpha.6 — альфа: `WebGPURenderer` по умолчанию с откатом на WebGL2; `WebGLRenderer` и
  GLSL-библиотеки — входом `'@react-three/fiber/legacy'`; проп `gl` на основном входе бросает ошибку; вход
  `'@react-three/fiber/webgpu'` устарел; TSL-хуки — в @react-three/tsl (только альфа); вес — 392,9 КБ br одним файлом
  → в продакшен — 9.8.2 [документация; проверено] → `06-js-stack.md` §1.2.
- WebGPU в R3F (проверено A/08, r186 + R3F 9.8, работает на WebGPU и на откате WebGL2):
```jsx
// R3F 9.8 + three r186 WebGPURenderer — [проверено] (бандл 400 КБ br)
import * as THREE from 'three/webgpu';
import { color, mix, uv } from 'three/tsl';
import { Canvas, extend, useFrame } from '@react-three/fiber';
import { useRef } from 'react';
extend(THREE);                                        // классы three/webgpu для JSX
const mat = new THREE.MeshStandardNodeMaterial({ roughness: 0.4 });
mat.colorNode = mix(color(0xff9500), color(0x5856d6), uv().y);
function Spin() {
  const ref = useRef();
  useFrame((_, dt) => { ref.current.rotation.y += dt * 0.6; });
  return <mesh ref={ref} material={mat}><torusKnotGeometry args={[0.8, 0.28, 256, 32]} /></mesh>;
}
export default function App() {
  return (
    <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 4], fov: 40 }}
      gl={async (props) => { const r = new THREE.WebGPURenderer(props); await r.init(); return r; }}>
      <hemisphereLight args={[0xffffff, 0x445566, 1.5]} />
      <directionalLight position={[2, 3, 4]} intensity={2} />
      <Spin />
    </Canvas>
  );
}
```
  В консоли r186: «THREE.Clock: This module has been deprecated» и «PCFSoftShadowMap has been removed. Using
  PCFShadowMap» — это внутренности R3F 9.8, не ошибка кода [проверено].
- Производительность R3F: прокрутку и частые значения — в `useFrame` через refs, **не** в React-состояние (Shopify
  Editions; Codrops 2026-06-26); `frameloop="demand"` + `invalidate()` для статичных сцен; `dpr={[1, 1.5]}` [практика].
- Цена: +≈ 140 КБ br (react-dom 205 КБ min + fiber 165 КБ min) и `* as THREE` в каталоге ломает tree-shaking three
  (729 КБ min three в сборке против 522 у vanilla) [проверено].

### 3.2. drei 10.7.9 — что закрывает из каталога
- Постановка: `Environment` (пресеты HDR — внешняя загрузка), `ContactShadows`, `AccumulativeShadows`, `Lightformer`,
  `Stage`, `Backdrop`, `Float`, `Sparkles`, `Stars`, `Sky`, `Cloud`, `Caustics`.
- Материалы: `MeshTransmissionMaterial`, `MeshRefractionMaterial`, `MeshDistortMaterial`, `MeshWobbleMaterial`,
  `MeshReflectorMaterial`, `MeshPortalMaterial`, `PointMaterial`, `shaderMaterial`.
- Текст: `Text` (troika SDF), `Text3D` (выдавленный). Данные: `Sampler`/`useSurfaceSampler` (точки на поверхности меша
  для частиц), `MarchingCubes` (метаболы), `Splat` (сплаты), `Decal`, `Outlines`, `Edges`, `AsciiRenderer`, `Trail`.
- Прокрутка и управление: `ScrollControls`, `PresentationControls`, `MotionPathControls`, `CameraControls`.
- Производительность: `PerformanceMonitor`, `AdaptiveDpr`, `AdaptiveEvents`, `BakeShadows`, `Bvh`, `Detailed` (LOD),
  `Instances`, `Merged`, `Preload`, `useDetectGPU`.
- HTML: `Html` (DOM поверх/внутри сцены), `View` (несколько 3D-вьюпортов в одном canvas), `Hud`.
  [документация: 134 страницы docs drei]
- Ловушка: drei тянет `stats-gl 2.4.2` со своей копией `three@0.170` (если использовать StatsGl) [проверено: npm ls].

### 3.3. Постобработка
- `postprocessing` 6.39.5 (pmndrs, Zlib): `EffectComposer` → `RenderPass` → `EffectPass(camera, bloom, noise, vignette…)`
  — эффекты сливаются в один проход; peer **three ≥ 0.168 < 0.187** (r187 потребует обновления); README — только
  `WebGLRenderer` (атрибуты `powerPreference: 'high-performance', antialias: false, stencil: false, depth: false`); ветка
  v7 — 7.0.0-beta.16 с peer `three < 0.184`: с r186 не ставится, WebGPU не заявлен [данные: npm; документация].
  `@react-three/postprocessing` 3.2.2 (peer fiber ≥ 9.7) — обёртка для R3F.
- Для `WebGPURenderer` — пост на TSL: `RenderPipeline` (r183+), узлы `bloom()`, DOF, SSAO, GTAO, SSR, TRAA, `pass()`
  [документация three r186].
- Цена: pmndrs-пост ≈ 12 КБ br сверх three [проверено]; GPU — каждый эффект-проход полноэкранный (discoverthreejs:
  объединять проходы) [практика].

## 4. Babylon.js 9
- 9.0 анонсирован 2026-03-26 (Microsoft): Clustered Lighting (WebGPU и WebGL2), текстурные area lights, Node Particle
  Editor, flow maps и аттракторы частиц, объёмный свет (compute WebGPU с откатом), **Frame Graph v1** (до −40 % памяти
  GPU в примерах), ретаргетинг анимации, **сплаты: PLY, .splat, SPZ, SOG/SOGS, треугольные сплаты, тени, сборка
  нескольких сплатов**, Inspector v2, OpenPBR (часть 3) [документация].
- npm @babylonjs/core 9.32.1 — 138 стабильных релизов за 12 месяцев (почти еженедельно), Apache-2.0, 26 094★ [данные: npm].
- Бандл (ES6 поимпортно): ядро + куб 209,8 КБ br; WebGPU-движок с откатом — 266,5; + glTF-загрузчик и
  `createDefaultEnvironment` — 669,9 КБ br; `import *` — 1 448 КБ br [проверено]. WebGPU-движок: шейдеры ядра на WGSL,
  GLSL-конвертеры (`glslang`, `twgsl`) грузятся лениво с `cdn.babylonjs.com` только для GLSL-шейдеров [исходник]. Движок печатает в консоль «Babylon.js vX - WebGL2/WebGPU» (удобно для детекции).
- Когда: сложные приложения (конфигураторы, редакторы, игровые механики), нужна «всё-в-одном» функциональность, команда
  знает Babylon; когда нет: лендинг/hero (в 4–6 раз тяжелее three). В замере 33 сайтов Babylon не встретился [проверено].
- Нейросети знают Babylon хорошо (стабильный API, Playground); риск — частые релизы 9.x меняют мелочи.

## 5. PlayCanvas 2
- Движок 2.23.3 (MIT, 16 886★, 57 релизов/12 мес.; бета 2.24; тег `lts` = 1.77.0 — ветка v1), облачный редактор,
  `@playcanvas/react` 0.11.7 (peer playcanvas ^2.11.8, React 18/19), веб-компоненты @playcanvas/web-components 0.28.1
  [данные: npm].
- Бандл: Application + куб + загрузка glb — 404,5 КБ br (Node-воркеры `node:worker_threads` в сборке надо исключить)
  [проверено].
- Сплаты — сильнейшая сторона: формат **SOG** (lossless WebP-атласы + meta.json, ZIP `.sog`; в 15–20 раз меньше PLY;
  `splat-transform`), потоковый SOG с LOD и бюджетом гауссиан на устройство, compute-рендер на WebGPU (engine 2.19+),
  SuperSplat (редактор и вьюер) — всё MIT [документация].
- В замере: playcanvas.com (герой-сплат «drag to rotate»), superspl.at (вьюер в iframe) [проверено].
- Нейросети: риск API v1 (`pc.Application`, старые скрипты) против v2 — сверять с документацией v2.

## 6. model-viewer 4.4.0
- Веб-компонент Google (Apache-2.0, 8 254★): `src`, `poster`, `alt`, `loading` (auto = lazy,
  eager), `reveal` (auto, manual), `camera-controls`, `camera-orbit` (с `env(window-scroll-y)` — орбита от прокрутки без
  JS), `auto-rotate`, `environment-image` (`neutral`, `legacy`, URL HDR/JPG), **`tone-mapping` по умолчанию `neutral`
  (Khronos PBR Neutral) с v4.0, раньше ACES**, `shadow-intensity`, `ar` + `ar-modes` (`webxr scene-viewer quick-look`; USDZ
  генерируется на лету без анимаций), варианты, аннотации (hotspot-слоты), `toBlob({idealAspect})` для постера,
  `registerRenderer` (свой рендерер), `minimumRenderScale` (динамическое снижение разрешения, 38–60 fps), `powerPreference`
  по умолчанию high-performance [документация].
- Декодеры: Draco и KTX2 — по требованию с CDN Google (Draco > 100 КБ), Meshopt — только при `meshoptDecoderLocation`
  [документация].
- 4.4.0: AR Quick Look в сторонних браузерах iOS без `ios-src`, исправлен `ar-placement="wall"`, единицы `m`/`cm`/`mm` у
  `<extra-model offset>` [документация: release v4.4.0].
- Бандл 4.4.0: `dist/model-viewer.min.js` 229,9 КБ br (внутри three 0.183.2); модуль без three — 116,9 КБ br [проверено].
  **peer three ^0.183** → с three 0.186.1 в одном бандле — ERESOLVE; держать model-viewer отдельным скриптом
  [проверено: npm ERESOLVE].
- Когда: витрина товара, AR, e-commerce без 3D-разработчика; когда нет: кастомные шейдеры, прокрутка-сторителлинг,
  несколько объектов со сложной логикой.

## 7. Needle Engine
- Движок на three с экспортом из **Unity и Blender** (аддон), компоненты (физика, анимационные машины состояний, сеть,
  WebXR), Needle Cloud (оптимизация и хостинг ассетов, прогрессивная загрузка LOD) [документация Needle pricing].
- Лицензия: Hobby (бесплатно) — **только некоммерческое**, логотип Needle, 1 проект, деплой только в Needle Cloud; Pro —
  €49/место/мес. (€588/год) — коммерция, без водяного знака, self-hosting; Enterprise — договор [документация].
- npm: `latest` = **6.0.0-alpha.7**, `stable` = 5.1.16, `version-4` = 4.16.13 → `npm i @needle-tools/engine@stable`
  [проверено: npm dist-tags]. Сборка 5.1.13: `needle-engine.bundle.min.js` 311 КБ br + `three-core.min.js` 209 КБ br
  (+ `rapier` 2,2 МБ и `materialx` 9,5 МБ по требованию) [проверено].
- В замере: needle.tools (диорама, до 184 draw calls, 12–15 МБ) [проверено].
- Для агента: Blender-путь Needle требует аддона и лицензии для коммерции; альтернатива без лицензии — свой экспорт GLB
  (`../08-export-gltf/`) + three.

## 8. Spline и no-code-рантаймы

### 8.1. Spline (редактор, рантайм)
- Редактор в браузере/десктопе; **Spline v2 (2026-08-20)** — редактор переписан на WebGPU, ИИ-агент, MCP [документация].
- Рантайм `@splinetool/runtime` 2.0.114 (225 версий за 12 мес., лицензия в npm не указана): standalone-сборка WebGL —
  457,5 КБ br, WebGPU-micro — 385,9 КБ br; через бандлер — 843,2 КБ br; `physics.wasm` — 419,3 КБ br, `hana-ui.wasm`
  для Hana — 787,6 КБ br [проверено]. Рантайм рисует на WebGPU по умолчанию с откатом на WebGL, один бэкенд на страницу
  [документация].
- В пакете — файл AGENTS.md «для кодовых агентов»: адрес `.splinecode` даёт только экспорт редактора (из id сцены не
  выводится), `wasmPath` по умолчанию — CDN, водяной знак зашит издателем в данные сцены, просьба добавлять кредит
  «Made with Spline» [документация; мнение вендора — просьба о кредите].
- В замере: spline.design (three-форк r149, 192 draw calls в покое, JS 2,9 МБ), zentry.com (`.splinecode` 892 КБ)
  [проверено].

### 8.2. Экспорт из Spline
- Код: Vanilla JS (`@splinetool/runtime`), three.js (`@splinetool/loader`), React/Next (`@splinetool/react-spline` 4.1.0,
  последний релиз 2025-07-15), r3f (`r3f-spline`); **анимации и события — только Vanilla JS и React** [документация].
- Файлы: GLB/GLTF, USDZ, FBX, OBJ (для переноса в three/Blender) [документация через поиск; не проверено].

### 8.3. Spline MCP — можно ли агенту работать программно
- Официальный MCP встроен в **десктоп-приложение Spline (macOS, Windows)**; из браузера не работает, отдельного пакета
  нет; регистрируется в Claude Code (`~/.claude.json`), Cursor, VS Code и др.; сервер слушает 127.0.0.1 с allowlist
  origin; инструменты `mcp__Spline__3d_run_code`, `mcp__Spline__2d_write_html` и др.: создавать/править сцены, генерировать
  модели и картинки Spline AI, снимать скриншоты, писать «слой кода», Hana (2D-дизайн) [документация].
- На Linux-машине базы Spline MCP недоступен. Сообщественные MCP (например, архивный aydinfer/spline-mcp-server)
  обращаются к несуществующему REST API [документация через поиск; не проверено].

### 8.4. Unicorn Studio, Paper Shaders, ShaderGradient
- Unicorn Studio — no-code-редактор шейдерных/медиа-эффектов (75+ эффектов, ИИ-ассистент, нужен WebGL2, рантайм
  «≈ 50 КБ gzip» по словам вендора), `unicornstudio-react` 2.4.0 (MIT); в замере — главная Unicorn (3 draw calls,
  TBT 0,25–1,2 с) [документация вендора; проверено].
- `@paper-design/shaders` 0.0.82 (Apache-2.0, 21 релиз/12 мес.) — mesh gradient и др. шейдеры, 5,5 КБ br; сайт
  shaders.paper.design [проверено].
- `@shadergradient/react` 2.4.20 (R3F, последний релиз 2025-12-08) — градиенты-формы [проверено].
- Rive (`@rive-app/canvas` 2.48; wasm 261,3 КБ br у lite и 704,0 у полной сборки — по умолчанию с CDN) и Lottie
  (`dotlottie-web` 0.81 с wasm 379,1 КБ br с CDN; `lottie-web` 5.13.0 — light 41,6 КБ br) — 2D-анимация; на наградных 3D-сайтах Rive встречается
  рядом с 3D (6 из 33) [проверено].

## 9. Лёгкие и специальные библиотеки
- **OGL** 1.0.11 (Unlicense, 12,1 КБ br для куба): минимальная обёртка WebGL; популярна в Codrops-демо эффектов над
  картинками; **релизов и коммитов нет больше полутора лет** → для нового кода не брать: сверхмалый вес даёт свой
  WebGL2 (0,7 КБ br у SDF-примера) [проверено; данные: GitHub].
- **Threlte** 8.6.1 (Svelte 5, three ≥ 0.172) и **TresJS** 5.10.0 (Vue ≥ 3.4, three ≥ 0.133; WebGPU — эксперимент) —
  живые обёртки (27 и 21 релиз за 12 мес.) [данные: npm]. Пример Codrops 2026-09-06: маска лица MediaPipe + Threlte.
- **A-Frame** 1.8.0 (MIT, 17 635★, 1 релиз за год): 276 КБ br (dist); npm 12 отказывается ставить из-за git-зависимости
  `three-bmfont-text` (EALLOWGIT) → нужен `--allow-git` или dist-скрипт [проверено].
- **Сплаты для three**: Spark `@sparkjsdev/spark` 2.4.0 (MIT, World Labs, 3 647★, 782,2 КБ br вместе с three; LoD, SPZ v4,
  постраничная загрузка) — живая; `@mkkellogg/gaussian-splats-3d` 0.4.7 — без релизов больше полутора лет; нативные
  сплаты three — 216,6 КБ br (`'three/webgpu'` + SPZ); three r186 `GaussianSplat` + лоадеры PLY/SPLAT/KSPLAT/SPZ
  и `GLTFGaussianSplatLoaderExtension` (`KHR_gaussian_splatting`, только `WebGPURenderer`) [проверено: A/02, A/03;
  документация]. Не путать **Spark** (sparkjs.dev, сплаты) и **spark.js** (Ludicon, сжатие текстур в реальном времени —
  каталог V).
- Прочее: `cobe` 2.0.1 (глобус, 5 КБ br), `globe.gl` 2.46.2, `troika-three-text` 0.52.5, `camera-controls` 3.1.2,
  `three-mesh-bvh` 0.9.17 (рейкаст/коллизии), `@dimforge/rapier3d-compat` 0.21 / `@react-three/rapier` 2.2 (физика wasm;
  репозиторий rapier.js в архиве, код — в dimforge/rapier),
  `leva`/`lil-gui` (отладочный GUI), `maath` (сглаживание; с r186 есть `THREE.MathUtils.damp` — отчёт V), `pixi.js`
  8.22 (2D, для сравнения) [проверено].

## 10. Анимация и прокрутка

### 10.1. GSAP 3.15 и ScrollTrigger
- gsap 3.15.0 (2026-04-13), 28 567★; ScrollTrigger (`scrub`, `pin`), Observer (единый ввод колесо/тач/указатель),
  `quickTo` (переиспользуемые твины — Codrops 2026-07-07: без него 500 новых твинов на кадр); + ScrollTrigger = 40 КБ br
  [проверено: A/03; практика].
- Лицензия «Standard No Charge» (Webflow; действует с 2025-04-30, изменена 2025-05-30): бесплатно для любых сайтов,
  включая коммерцию и бывшие платные плагины (SplitText, MorphSVG); **запрещено**: использовать GSAP в инструментах
  визуального создания анимаций без кода, конкурирующих с Webflow, и обратная разработка для таких продуктов; FAQ:
  «код GSAP, сгенерированный ИИ (ChatGPT, Cursor, Lovable, Webstudio…), — не запрещённое использование»; Webflow может
  менять лицензию [документация]. Для системы генеративного дизайна: сгенерированные ею сайты с GSAP — разрешено; сама
  система как визуальный конструктор анимаций на GSAP — зона риска → юридическая проверка [спорно].
- В замере GSAP — примерно на 15 из 33 сайтов [проверено].

### 10.2. Lenis 1.3.27
- MIT, 15 959★, 14 релизов/12 мес.; ветка 2.0 — тег `dev` (2.0.0-dev.5); пакет **`lenis`** (старые `@studio-freight/lenis`, `@studio-freight/react-lenis`
  помечены устаревшими) [проверено: npm].
- `new Lenis({ autoRaf: true })` или свой цикл `lenis.raf(time)`; `respectReducedMotion: true` по умолчанию (lerp = 1,
  программные прокрутки мгновенные); связка с ScrollTrigger: `lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000)); gsap.ticker.lagSmoothing(0)` [документация].
- Ограничения: нет CSS scroll-snap (есть `lenis/snap`), Safari ≤ 60 fps и 30 fps в энергосбережении, над iframe не
  прокручивает, `position: fixed` дёргается в Safari до M1 [документация].
- Зачем в 3D: синхронная с кадром прокрутка для DOM↔WebGL (Codrops 2025-06-05: нативный скролл не кадр-синхронен)
  [практика]. В замере — ≈ 8 из 33 [проверено].

### 10.3. Theatre.js
- `@theatre/core` 0.7.2 (Apache-2.0) и `@theatre/studio` 0.7.2 (**AGPL-3.0**), последний релиз 2024-05-19, публичный
  репозиторий не обновлялся с 2024-08-14; README: «1.0 скоро, разработка временно в закрытом репо» [проверено: A/02;
  документация]. В бандлах 4 из 33 сайтов (Active Theory, Primland, Shopify Editions, Hubtown) [проверено].
- Для нового кода агента — не выбирать: камера/таймлайн — анимацией из Blender (glTF, `mixer.setTime`) или GSAP-таймлайном.

### 10.4. Motion
- `motion` 14.7.1 (MIT, 85 релизов/12 мес.): `animate`, `scroll` для DOM/SVG (22 КБ br); **`framer-motion-3d` на npm —
  «Package no longer supported»** → 3D-анимацию через Motion не делать [проверено].

### 10.5. Нативная прокрутка CSS
- `animation-timeline: scroll()` / `view()` — анимации CSS от прокрутки без JS (Codrops 2024-01-17, 2024-01-24);
  для CSS 3D-эффектов (каталог §19) и простых параллаксов [практика].

## 11. Что нейросеть знает по памяти и как проверять

| Библиотека | Объём кода в сети | Изменчивость API | Риск «старого» кода | Как проверять |
|---|---|---|---|---|
| three | огромный | высокая (переименования почти каждый релиз) | **высокий**: `outputEncoding`, `Geometry`, `RGBELoader`, `Clock`, `physicallyCorrectLights` | Migration Guide + запуск (0 предупреждений `deprecated`) |
| R3F / drei | большой | средняя (v8→v9 типы, `gl`) | средний: `MeshProps`, `gl={canvas => …}`, sRGB в пропах | peer-зависимости npm, v9 Migration Guide |
| postprocessing | средний | низкая (6.x); бета v7 с r186 не ставится | низкий; ловушка — peer three < 0.187: с r187 — ERESOLVE | `npm view postprocessing peerDependencies` |
| Babylon | большой | средняя (частые релизы) | средний | Playground, docs 9.x |
| PlayCanvas | средний | высокая v1 → v2 | высокий (v1-скрипты) | docs v2, тег `lts` = v1 |
| model-viewer | средний | низкая | низкий; ловушка — tone-mapping по умолчанию сменился на neutral в 4.0 | docs 4.x |
| Needle | малый | высокая | высокий; ловушка — alpha по тегу latest | `npm view … dist-tags` |
| Spline runtime | малый | средняя | средний | docs Spline |
| GSAP | огромный | низкая | низкий по API; **ложное «SplitText платный»** | gsap.com/standard-license |
| Lenis | средний | средняя (переименование пакета) | средний: `@studio-freight/lenis` | npm deprecated |
| Theatre.js | средний | заморожен | высокий смысловой (проект стоит) | npm time |
| TSL / `WebGPURenderer` | тонкий: `"three/tsl"` — 75 тыс. файлов против 733 тыс. у `new THREE.WebGLRenderer` | очень высокая (переименования r179–r187) | **высокий**: `PostProcessing`, `PI2`, `label()`, `storage().get()` | Migration Guide, `tsc` с @types/three той же версии, headless с провалом на `deprecated` |
| R3F 10 (альфа) | малый | высокая | высокий: `gl` на основном входе, вход `'@react-three/fiber/webgpu'` | `npm view … dist-tags`, релизы R3F |
| TypeGPU | малый (≈ 0,7 тыс. файлов) | высокая (до 1.0) | средний | документация TypeGPU |
[мнение A: на основе Migration Guide, npm-меток deprecated и A/08]

Процедура для агента перед кодом рантайма:
1. `npm view <пакет> version dist-tags peerDependencies` — актуальная стабильная версия и совместимость (Needle, model-viewer,
   postprocessing, R3F).
2. Для three — прочитать разделы Migration Guide между «своей» версией и r187 (таблица §2.3 — выжимка).
3. Прогнать страницу в headless (`../../scripts/3d/web_view.py --page` или `99-raw/experiments/A/tools/site_probe.py`):
   0 ошибок консоли, предупреждения `deprecated` разобрать, draw calls > 0, первый кадр есть; в отчёте — `backend` и
   `isFallbackAdapter`, иначе программный SwiftShader сойдёт за WebGPU [проверено].
4. `tsc --noEmit` с @types/three той же версии: удалённое API — ошибка, устаревшее — `@deprecated` [проверено] →
   `06-js-stack.md` §4.3.

## 12. Стек по умолчанию для агента

| Ситуация | Стек | Вес JS (br) | Почему | Оговорки |
|---|---|---|---|---|
| Интерактив не нужен: кадр, иконки, иллюстрации | предрендер Blender → AVIF/WebP | 0 | 4–15 КБ на картинку, LCP-друг | цвет: view transform (`../06-materials-lighting-render/`) |
| Движение без управления | `<video>` (H.264 + AV1/VP9), альфа — VP9 + HEVC или stacked | 0–3 | 40–500 КБ | HEVC-alpha кодируется только на macOS |
| Движение по прокрутке, точное | секвенция WebP/AVIF в `<canvas>` | ≈ 2 | покадрово, без декодера видео | память кадров |
| Фон-шейдер, объект или мир из правил | свой движок на WebGL2 (`../16-js-scenes/01-engine.md`) или `@paper-design/shaders` | 0,7–6 | без ассетов и библиотек; живёт на холсте без сети | reduce → статичный кадр |
| Витрина товара + AR | **model-viewer 4.4.0** (dist отдельным скриптом) | 230 | poster/lazy/AR/клавиатура «из коробки» | отдельный AR-GLB; не смешивать с three r186 в бандле |
| Hero-GLB, история на прокрутке, сайт без фреймворка | **three 0.186.1 `WebGLRenderer`** + GLTFLoader (Meshopt/Draco/KTX2) + GSAP/ScrollTrigger + Lenis, бандлер | 150–210 | самый распространённый, лёгкий, проверенный паттерн (A/07) | Migration Guide; `*.min.js` при CDN |
| Сайт на React/Next | **R3F 9.8.2 + drei 10.7.9** (+ `@react-three/postprocessing`) | 250–361 | компонентный стек, готовые эффекты drei | peer react < 19.4; `frameloop="demand"` для статики; R3F 10 — альфа |
| Сайт на Vue / Svelte | TresJS 5.10 / Threlte 8.6 | ≈ three + 20–60 | родной фреймворк сайта | меньше примеров в сети |
| Compute-частицы 100 тыс.+, TSL-эффекты, сплаты three | `three/webgpu` + TSL (откат WebGL2 встроен) | 173–400 | один код на два бэкенда (A/08) | pmndrs-пост не работает; первый кадр дольше |
| Переход GLSL → TSL без WebGPU | `WebGLRenderer` + `WebGLNodesHandler` (r184+) | 202 | один код узлов для WebGL и для будущего WebGPU | нет MRT, transmission, VSM, storage-текстур; вес как у WebGPU-сборки |
| Сплаты как главное содержимое | Spark (three), нативные сплаты three на `WebGPURenderer` или PlayCanvas/SuperSplat (SOG, стриминг) | 217–782 | зрелые рендереры сплатов | постер-фолбэк; формат не устоялся |
| Приложение/конфигуратор/редактор, «всё в одном» | Babylon 9 (WebGPU-движок с откатом — 266,5) или PlayCanvas 2 | 210–670 | инспектор, физика, частицы, GUI | тяжело для лендинга |
| Конвейер Unity или Blender-компоненты с логикой | Needle Engine 5 (`@stable`) | 520+ | экспорт сцен с компонентами | коммерция — Pro-лицензия |
| Дизайнер без разработчика | Spline (оценить вес и draw calls), Unicorn Studio для эффектов | 50–843 | скорость создания | MCP Spline не на Linux; узнаваемые пресеты |
| Холст Claude Design (сети нет, кроме шрифтов и загрузок) | свой движок на WebGL2 кодом артборда; библиотека — только под модель GLB, по cd 05/03 §3 | 0,7–3 (three под GLB — 158) | 0 загрузок; холст и сайт делят один файл сцены | Meshopt вместо Draco и KTX2; wasm с CDN не брать (`06-js-stack.md` §2.2) |
| Остров Astro (`<org>/site`) | постер в HTML — LCP; сцена — ванильным `<script>` с IntersectionObserver и `import()` после `load` или `client:visible` с `rootMargin` | 108–158 | three — отдельным чанком, React ради 3D не нужен | reduce и `saveData` → постер; `client:load` для 3D не брать (`06-js-stack.md` §2.3) |
Позиция: [проверено] для строк с экспериментами A/03, A/07, A/08 и для весов строк (сборка минимальной сцены);
остальное — [практика]. Не выбирать для нового кода: Theatre.js (заморожен), `framer-motion-3d` (снят), A-Frame для
лендинга, OGL (релизов и коммитов нет больше полутора лет), `@mkkellogg/gaussian-splats-3d` (заморожен).

## Частые ошибки

- `npm i @needle-tools/engine` → альфа 6.0; `npm i three@latest` вместе с model-viewer → ERESOLVE (peer ^0.183), а с
  выходом r187 — и вместе с pmndrs `postprocessing` (peer < 0.187) [проверено; данные: npm].
- Импорт three в R3F-проекте из двух мест (`three` и `three/webgpu`) — два экземпляра, «Multiple instances of Three.js»;
  WebGPU-сцена целиком на `three/webgpu`.
- pmndrs `postprocessing` с `WebGPURenderer` — не поддерживается; пост — TSL `RenderPipeline` [документация].
- Код «по памяти» с `THREE.Clock`, `RGBELoader`, `outputEncoding`, `PCFSoftShadowMap` — предупреждения/поломки в r186
  (таблица §2.3) [проверено].
- `renderer.render()` у `WebGPURenderer` до `await renderer.init()` вне `setAnimationLoop` [документация r181].
- three из CDN неминифицированными `three.module.js` + `three.core.js` (391 КБ вместо 194 КБ br) [проверено].
- Lenis из `@studio-freight/lenis` [проверено: npm deprecated]; «SplitText платный» — неверно с 2025-04-30 [документация].
- Theatre.js в новом проекте (заморожен с 2024; studio — AGPL) [проверено].
- R3F-состояние, обновляемое прокруткой каждый кадр (ре-рендер React) — лаги; прокрутка → refs/uniforms [практика].
- Spline-сцена как «лёгкий» вариант: рантайм 834 КБ br + физика, полный DPR на телефоне [проверено].

## Чек-лист

- [ ] Стек выбран по таблице §12 и стеку сайта (vanilla / React / Vue / Svelte)?
- [ ] Версии и peer-зависимости проверены `npm view` (three 0.186.1, R3F 9.8.2, drei 10.7.9, model-viewer 4.4.0, Needle `@stable`)?
- [ ] Код без устаревших API three (§2.3); в консоли нет `deprecated` от своего кода?
- [ ] WebGPU только при нужде (compute/TSL/сплаты), откат на WebGL2 проверен?
- [ ] Вес JS рантайма в бюджете (`02-when-3d-budgets-loading.md` §3.1): ≤ 200 КБ br (vanilla) / ≤ 300 КБ br (React)?
- [ ] Лицензии: GSAP (запрет конкурирующих no-code), Needle (коммерция — Pro), Theatre studio (AGPL), Spline (npm без лицензии) — учтены?
- [ ] Страница прогнана в headless: 0 ошибок, draw calls > 0, reduce работает?

## Открытые вопросы и противоречия

- pmndrs/postprocessing: ветка v7 (7.0.0-beta.16) — peer `three < 0.184`, с r186 не ставится, WebGPU не заявлен; у 6.39.5
  peer `three < 0.187` — с выходом r187 ERESOLVE, пока не выйдет совместимый релиз.
- Первый кадр WebGPU медленнее WebGL2 в headless-стенде (4,4 против 1,2 с) — на реальных устройствах не измерено (F).
- Лицензия `@splinetool/runtime` в npm не указана; условия использования экспорта — по ToS Spline (не прочитаны).
- GSAP-лицензия и продукт «генеративный дизайн» — юридический вопрос для заказчика [спорно].
- Unicorn Studio: вес рантайма и цены не проверены (страница цен за логином).
- Spline-экспорт в GLB/USDZ: качество и перенос материалов не проверены (G или F).
- Babylon в выборке наградных сайтов не встретился — выводы о нём по документации и бандлу, без замера живых сайтов.

## Источники

- [S1] mrdoob/three.js, release r186 (2026-09-08) и r180–r185, GitHub (через ungh.cc) — изменения, сплаты, удаление min-сборок; 115 764★, push 2026-09-22; [документация].
- [S2] three.js wiki, «Migration Guide» (разделы 175→187), raw.githubusercontent.com/wiki/mrdoob/three.js/Migration-Guide.md — переименования; [документация].
- [S3] npm-пакет three 0.186.0 (build/, examples/jsm/) — проверка RGBELoader, Clock, PCFSoftShadowMap, HTMLTexture, GaussianSplat; [проверено].
- [S4] pmndrs/react-three-fiber, «v9 Migration Guide» (docs/tutorials/v9-migration-guide.mdx) — React 19, async gl; [документация].
- [S5] pmndrs/drei, docs (134 страницы, дерево репозитория) — каталог компонентов; [документация].
- [S6] pmndrs/postprocessing README + npm (peer three ≥ 0.168 < 0.187, dist-tags alpha/beta 7) — [документация].
- [S7] Windows Developer Blog, «Announcing Babylon.js 9.0», 2026-03-26 — возможности 9.0; [документация].
- [S8] PlayCanvas, «The SOG Format» + блог «SuperSplat: WebGPU and Streaming» — сплаты, замеры fps; [документация вендора].
- [S9] model-viewer docs 4.x (modelviewer.dev/docs) — атрибуты, тонмаппинг, декодеры; [документация].
- [S10] Needle, «Pricing & Plans», needle.tools/pricing (2026-09) — лицензия; [документация].
- [S11] Spline docs: «Spline MCP Server», «Exporting as Code»; блог «Introducing Spline V2», 2026-08-20 — [документация].
- [S12] GSAP, «Standard No Charge License», gsap.com/standard-license (эфф. 2025-04-30) — [документация].
- [S13] darkroomengineering/lenis README (1.3.26) + npm deprecated `@studio-freight/lenis` — [документация].
- [S14] theatre-js/theatre README + npm 0.7.2 — статус проекта; [документация].
- [S15] Unicorn Studio docs (unicorn.studio/docs, пересказ WebFetch) — [документация вендора, частично].
- [S16] Fyrd/caniuse, features-json/webgpu.json (день — в строке «Снимок») — поддержка WebGPU; [данные].
- [S21] Снимок реестра npm (96 пакетов) и сборки минимальной сцены (esbuild, brotli q11), headless-пробы WebGPU на Linux,
  Intel Iris Xe; первоисточники версий, долей и поведения WebGPU — `06-js-stack.md` § Источники — [проверено; данные].
- [S17] L. Blue, discoverthreejs «Tips and Tricks» (2018–2020) — устаревшие API как пример дрейфа; [практика].
- [S18] Codrops, A. Thelander (Shopify, 2026-06-26); «SEO-friendly WebGL Text» (2025-06-05); «Blender camera path» (2026-07-07) — практика R3F/GSAP/Lenis; [практика].
- [S19] Эксперименты A: `02-runtime-registry` (npm + GitHub по 42 пакетам), `03-bundle-sizes`, `07-lazy-hero-pattern`, `08-webgpu-fallback`; замер 33 сайтов — [проверено].
- [S20] Отчёт V (каталог видео): `MathUtils.damp` в r186, Khronos PBR Neutral в Blender 5.2.2, spark.js (Ludicon) — [проверено V].
