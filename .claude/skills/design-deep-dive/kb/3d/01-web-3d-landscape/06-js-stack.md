# 06 · 3D на JavaScript: весь спектр способов и что брать

Чем делать 3D для страницы на JavaScript — от CSS 3D и Canvas 2D через свой WebGL2, three.js и движки до сплатов, видео
и секвенций кадров: когда что брать, сколько весит минимальная сцена, какая лицензия, жив ли пакет и где сцена живёт —
холст Claude Design, остров Astro, React-кабинет. Контракт своего движка — `../16-js-scenes/01-engine.md`; здесь —
выбор между ним и библиотеками. Вес — сборка минимальной сцены (esbuild, ESM, minify, brotli q11; wasm и чанки по
требованию — отдельной цифрой), headless — Chrome 153 и Playwright 1.63; всё на одной машине: Linux, Intel Iris Xe
(Gen12, Mesa). Версии и живость — реестр npm и GitHub. Знание скоропортящееся, день снимка → §3.1; перед выбором стека
версии сверяются заново (`npm view`).

## Выжимка для агента

1. **Свой движок на WebGL2 — первым** для объекта, фона, частиц и мира, которые описываются кодом: пример SDF-raymarch
   весит 0,7 КБ br против 108,5 у куба three и живёт на холсте без сети; библиотека — когда есть модель GLB, физика или
   кодовая база команды. `[проверено]` → §1, §2.1
2. **Модель GLB — three 0.186.1 на `WebGLRenderer`**: manual three считает `WebGPURenderer` экспериментальным, а
   `WebGLRenderer` — рекомендованным для чистого WebGL2; llms.txt three для моделей говорит то же. Куб — 108,5 КБ br,
   набор под GLB (загрузчик, Draco, KTX2, Meshopt, орбита, `RoomEnvironment`) — 158,2. `[документация]` `[проверено]` → §1.1
3. **Лестница веса минимальной сцены, КБ br**: свой WebGL2 0,7 · `cobe` 5,4 · Paper Shaders 5,5 · twgl.js 9,7 · OGL 12,1 ·
   three WebGL 108,5–158,2 · three WebGPU 173,1–241,1 · Babylon 209,8 (с glTF 669,9) · model-viewer 229,9 · R3F 9
   250,5–361,4 · R3F 10 392,9 · PlayCanvas 404,5 · Spark 782,2 · Spline 843,2. `[проверено]` → §1
4. **WebGPU — когда без него нет эффекта**: compute от 100 тыс. частиц, нативные сплаты three, узлы TSL (SSGI, SSR,
   TRAA, TAAU). Вход — +64,6 КБ br к кубу (173,1 против 108,5); откат на WebGL2 обязателен. `[проверено]` → §1.1, §3
5. **TSL идёт и на `WebGLRenderer`** через `WebGLNodesHandler` (r184+), но весит как WebGPU-сборка — 201,8 против
   108,9 КБ br у GLSL-патча — и не умеет MRT, transmission, VSM, storage-текстуры и WebGPU-пост: это путь миграции одним
   кодом, а не экономия. `[исходник]` `[проверено]` → §1.1
6. **r187 ломает**: PMREM на кубических целях (`CubeUVReflectionMapping` удалён, материалы выглядят чуть иначе), неявное
   приведение типов в формулах TSL, `setViewport()` и `setScissor()` без умножения на DPR при привязанной цели,
   `storage(…).element(0)`. pmndrs `postprocessing` 6.39.5 требует `three < 0.187` → в паре с ним держать
   `three@0.186.1`. `[документация]` `[данные: npm]` → §1.1, §6
7. **R3F 10 — альфа с WebGPU по умолчанию**: `WebGLRenderer` — входом `'@react-three/fiber/legacy'`, проп `gl` на
   основном входе бросает ошибку, TSL-хуки — в пакете @react-three/tsl, у которого есть только альфа. В продакшен —
   R3F 9.8.2 (React ≥ 19 < 19.4). `[документация]` → §1.2
8. **Холст Claude Design**: свой WebGL2 кодом артборда — без сети; библиотека — только под модель GLB и по канону
   cd 05/03 §3 (`import()` с точной версией у живого прототипа, модель — base64 в `.json`). Сжатие модели — Meshopt:
   декодер 6,8 КБ br без отдельного wasm. `[проверено]` → §2.2
9. **Остров Astro**: постер AVIF или WebP в HTML — кандидат LCP; сцена — при подлёте к окну (`client:visible` с
   `rootMargin` или IntersectionObserver и `import()` после `load`); vanilla three (108,5–158,2 КБ br) вместо
   React-острова ради 3D (от 250,5). `[документация]` `[проверено]` → §2.3
10. **WebGPU у людей**: 85,8 % браузеров полностью и 3,66 % частично; по реальным адаптерам — 83,2 %, но Linux — 18 %,
    Android — 75 %; в России caniuse не видит 30 % трафика → откат на WebGL2 и постер обязательны. `[данные]` → §3.1
11. **На старом Android WebGPU-сцена three идёт без MSAA**: `WebGPUBackend` просит адаптер `featureLevel: 'compatibility'`,
    в режиме совместимости `_samples = 0` — `antialias: true` молча не действует → узел FXAA или SMAA. `[исходник]` → §3.3
12. **Headless без GPU WebGPU не проверяется**: `--enable-unsafe-webgpu` поверх флагов Playwright даёт программный
    SwiftShader (`isFallbackAdapter: true`) — `backend` = webgpu, а кадр чёрный или белый. С GPU —
    `--use-angle=vulkan --enable-features=Vulkan`; в отчёт — `backend` и `isFallbackAdapter`. `[проверено]` → §3.4
13. **Модели знают WebGL-three лучше TSL**: `new THREE.WebGLRenderer` — в 733 тыс. файлов GitHub, `WebGPURenderer` — в
    93 тыс., импорт TSL — в 75 тыс., удалённый `outputEncoding` — в 72 тыс. → TSL, `RenderPipeline` и R3F 10 писать по
    документации версии, а не по памяти. `[данные]` → §4.1
14. **Устаревший код ловят три сети**: версия закреплена без `^` в npm и в import map; агенту — llms.txt three и
    Migration Guide; `tsc` с @types/three той же версии; headless-прогон с провалом на `deprecated` и `removed` в консоли.
    `[проверено]` → §4.3
15. **Чёткость — бюджетом пикселей**: буфер считать самому по канону `../16-js-scenes/01-engine.md` §6 (потолок DPR 2),
    не через `setPixelRatio(devicePixelRatio)`; с постом MSAA — в цели композера; тон продукта — Neutral; текст в
    сцене — MSDF, заголовок — HTML. `[документация]` `[исходник]` → §5
16. **Лицензии, которых модели не знают**: `lygia` — Prosperity 3.0.0 (коммерция — 30 дней пробы, дальше платный
    Patron) → не в код заказчика; GSAP бесплатен целиком, запрет — только no-code-конструкторы, конкурирующие с Webflow;
    Needle Hobby — только некоммерческое; у Spline в npm нет лицензии, водяной знак — в данных сцены; @theatre/studio —
    AGPL. `[документация]` → §6
17. **Ловушки установки**: model-viewer 4.4.0 держит peer `three ^0.183` (ERESOLVE рядом с 0.186.1);
    `three-msdf-text-utils` 1.5.0 тянет общий файл аддонов three (305,3 и 416,0 КБ br вместо ≈ 115–180); `latest` у
    Needle и @react-three/tsl — альфа; wasm Rive и dotLottie по умолчанию идёт с CDN. `[проверено]` `[данные: npm]` → §6
18. **Мёртвое не брать**: OGL (коммитов нет больше полутора лет), PicoGL, Zdog, `cannon-es`, Theatre.js,
    @mkkellogg/gaussian-splats-3d, gltfjsx, r3f-perf — без релизов; @lumaai/luma-web — «no longer supported»;
    репозиторий rapier.js в архиве, а пакеты Rapier в npm живые. `[данные]` → §1, §6

## 1. Спектр способов

От лёгкого к тяжёлому, от слоёв DOM к движкам и обратно к предрендеру. Вес — минимальная сцена: куб, треугольник или
одна анимация. Живость — стабильных релизов за 12 месяцев до снимка и активность репозитория. Вес — `[проверено]` [S43],
версии и живость — `[данные: npm, GitHub]` [S1], поддержка CSS 3D и WebCodecs — `[данные: caniuse]` [S19]; «не
мерился» — веса нет.

| способ | что это | когда брать | вес, КБ br | лицензия | живость | версия |
|---|---|---|---|---|---|---|
| CSS 3D-трансформации (`perspective`, `preserve-3d`) и анимации от прокрутки | поворот DOM-слоёв без света и меша | карточки, переворот, параллакс слоёв, 3D-заголовок из HTML с SEO и доступностью | 0 | стандарт | поддержка 97,28 % браузеров | — |
| Canvas 2D и SVG псевдо-3D: `zdog` | плоский рендер «круглых» примитивов | иконки-объёмы, иллюстрации | 7,1 | MIT | заморожен: релизов нет больше четырёх лет | 1.1.3 |
| Lottie: `lottie-web` | JSON-анимация After Effects в SVG или canvas | 2D-движение рядом с 3D | light 41,6; full 64,4 | MIT | 0 релизов за год | 5.13.0 |
| Lottie: dotlottie-web (@lottiefiles/dotlottie-web) | плеер `.lottie` на wasm (ThorVG) | тяжёлые анимации | 12,1 + wasm 379,1 (по умолчанию с CDN) | MIT | живой: 36 | 0.81.0 |
| Rive: @rive-app/canvas-lite и @rive-app/canvas | векторная анимация со state machine | 2D-интерактив, персонажи интерфейса | lite 51,2 + wasm 261,3; full 72,6 + wasm 704,0 (wasm с CDN) | MIT | живой: 52 | 2.48.0 |
| свой WebGL2 в инлайн-скрипте | полноэкранный треугольник и фрагментный шейдер (SDF-raymarch) или растр своим кодом | объект, фон, частицы, мир; холст без сети | 0,7 (пример raymarch) | своя | — | — |
| twgl.js | хелперы WebGL: программы, буферы, униформы | свой шейдер с меньшим шаблоном | 9,7 | MIT | 0 релизов за год, репозиторий активен | 7.0.0 |
| Paper Shaders (@paper-design/shaders) | шейдерные фоны: mesh gradient и др. | фон без сцены | 5,5 | Apache-2.0 | живой: 21 | 0.0.82 |
| OGL (`ogl`) | мини-движок WebGL: сцена, камера, меш | только поддержка чужого кода на OGL | 12,1 | Unlicense | мёртв: релизов нет, коммитов нет больше полутора лет | 1.0.11 |
| PicoGL (`picogl`) | обёртка WebGL2 | — | 13,1 | MIT | мёртв: релизов нет больше четырёх лет | 0.17.9 |
| `regl` | функциональная обёртка, API WebGL1 | наследный код, датавиз | 35,7 | MIT | 0 релизов за год, репозиторий активен | 2.1.1 |
| three, `WebGLRenderer` | стандарт веб-3D, полный glTF | модель GLB, герой, история на прокрутке | 108,5 куб; 158,2 набор под GLB | MIT | живой: 12 | 0.186.1 (r186) |
| three, `WebGPURenderer` и TSL | рендерер с бэкендами WebGPU и WebGL2 | compute, нативные сплаты, TSL-эффекты | 173,1 куб; 198,5 TSL и bloom; 241,1 набор под GLB | MIT | живой: 12 | 0.186.1 |
| three, TSL на `WebGLRenderer` (`WebGLNodesHandler`) | узловые материалы без WebGPU | переход GLSL → TSL одним кодом | 201,8 | MIT | с r184 | 0.186.1 |
| R3F (@react-three/fiber) и drei | React-рендерер three и компоненты | кабинет или сайт уже на React | 250,5 куб; с drei 288,2; с постом 361,4 | MIT | живой: 9 и 3 | 9.8.2; drei 10.7.9 |
| R3F 10 | `WebGPURenderer` по умолчанию, WebGL — отдельным входом | только прототипы | 392,9 одним файлом: 115,4 сразу и ≈ 270 при монтировании `Canvas` | MIT | альфа | 10.0.0-alpha.6 |
| TresJS (Vue) | обёртка three | сайт на Vue или Nuxt | не мерился | MIT | живой: 21; WebGPU — эксперимент [S32] | 5.10.0 |
| Threlte (Svelte 5) | обёртка three | сайт на Svelte | не мерился | MIT | живой: 27 | core 8.6.1 |
| Babylon.js | полный движок: инспектор, физика Havok, GUI | конфигураторы, приложения, игры | 209,8 WebGL-куб; 266,5 WebGPU-движок с откатом; 669,9 с glTF и окружением | Apache-2.0 | живой: 138 | 9.32.1 |
| PlayCanvas | движок с облачным редактором; сильный стек сплатов | игры, сплаты, сцены из редактора | 404,5 | MIT | живой: 57 | 2.23.3 |
| WebGPU напрямую: WGSL, TypeGPU (`typegpu`) | свой конвейер; типизированный WebGPU с шейдерами на TS | compute-ядро, своя симуляция | свой код; TypeGPU 69,3 | MIT | TypeGPU живой: 27, до 1.0 далеко [S31] | 0.12.9 |
| model-viewer (@google/model-viewer) | веб-компонент «витрина и AR» | товар, AR без 3D-разработчика | 229,9 готовая сборка; 116,9 модуль без three | Apache-2.0 | живой: 4; peer `three ^0.183` | 4.4.0 |
| Spline (@splinetool/runtime) | рантайм сцен редактора Spline | дизайнер без разработчика | 843,2 + `physics.wasm` 419,3 | в npm не указана; водяной знак — в данных сцены | живой: 225 | 2.0.114 |
| Needle Engine | three и экспорт из Unity и Blender с компонентами | конвейер Unity или Blender с логикой | 311 + 209 | коммерческая: Hobby — некоммерческое, Pro — €49/мес | живой; `latest` — альфа | stable 5.1.16; latest 6.0.0-alpha.7 |
| сплаты: Spark (@sparkjsdev/spark) | сплаты на three `WebGLRenderer`: LoD, SPZ v4, SOG | реальное место на WebGL-стеке | 782,2 с three | MIT | живой: 6 | 2.4.0 |
| сплаты: нативные three (`GaussianSplat`) | только `WebGPURenderer`, сортировка подсчётом на GPU | сплат на WebGPU-стеке | 216,6 | MIT | ново в r186 | 0.186.1 |
| сплаты: PlayCanvas и SuperSplat | SOG (в 15–20 раз меньше PLY), потоковый LoD | сплат как главное содержимое | 404,5 + файл сплата | MIT | живой | 2.23.3 |
| видео `<video>` | предрендер из Blender или JS-сцены | движение без ввода | 0 | — | — | — |
| секвенция кадров в `<canvas>` | покадровый скраб без декодера | точное движение по прокрутке | 0–3 (свой код) | — | — | — |

- **Видео и секвенции**: скраб видео плавный только при «каждый кадр — ключевой» (`ffmpeg … -g 1`), иначе перемотка
  идёт рывками; цена — файл в разы больше; альтернатива — секвенция кадров в `<canvas>` без декодера `[практика]` [S38].
  WebCodecs для покадрового декода есть у 91,6 % браузеров `[данные: caniuse]` [S19]. Поставки из Blender —
  `../12-recipes/08-sequence-video-alpha.md`.
- **Декодеры three для загрузки файлами**: Draco — wasm 47,6 и обёртка 9,8; Basis — wasm 198,8 и JS 13,4; Meshopt — 6,8
  (JS со встроенным wasm); zstd — 14,7 КБ br `[проверено]` [S43].
- **Движки на снимке**: Spark 2.4 — SPZ v4, постраничная загрузка `FetchSource`, рендер по требованию, LoD
  `[документация]` [S16]; PlayCanvas 2.23 — движок без jsdom в Node.js, порог bloom в `CameraFrame`, ускорения WebGPU
  `[документация]` [S17]; Babylon 9 — 138 релизов за год, потоковые сплаты с LoD под бюджет `[документация]` [S18].

### 1.1. three.js: рендерер, TSL, ревизия

- **Версия**: `latest` в npm — 0.186.1 (патч r186), 12 стабильных версий за год; ревизия r187 на выходе — веха
  назначена на день снимка, 642 задачи закрыты `[данные: npm, GitHub]` [S1] [S3]. Перед кодом — `npm view three version`.
- **Позиция three**: по manual `WebGPURenderer` в экспериментальном состоянии, хотя зрелость сильно выросла;
  `WebGLRenderer` — рекомендованный выбор для чистого WebGL2, крупных новых функций в нём не будет. Под
  `WebGPURenderer` не работают `ShaderMaterial`, `RawShaderMaterial`, `onBeforeCompile()` и `EffectComposer`. llms.txt для
  моделей ставит WebGL по умолчанию, а WebGPU — когда нужны TSL, compute и узловые материалы `[документация]` [S5] [S7].
  Статьи «готов к продакшену с r171» и «рекомендован с r182» официальной позицией не подтверждаются `[мнение]`
  `[спорно]` [S42].
- **TSL на `WebGLRenderer`** — `renderer.setNodesHandler(new WebGLNodesHandler())`, импорт
  `'three/addons/tsl/WebGLNodesHandler.js'`, с r184 [S8]. Не поддержаны VSM, MRT, transmission, WebGPU-пост и
  storage-текстуры; туман и окружение сами не обновляются — нужен `dispose`; геометрию нельзя делить между
  `InstancedMesh` `[исходник]` [S11]. Вес — 201,8 против 108,9 КБ br у GLSL-патча `onBeforeCompile`; в headless рисует
  на Intel GL и на SwiftShader `[проверено]` [S43].
- **Ломающее r187** (Migration Guide 186→187) `[документация]` [S4]: операнды и параметры математики TSL неявно
  приводятся к более широкому общему типу — формулы могут дать другой результат; PMREM строится на кубических целях,
  `CubeUVReflectionMapping` удалён, качество выше, материалы выглядят чуть иначе — пересверить кадр;
  `WebGLRenderer.setViewport()` и `setScissor()` не умножают на pixel ratio при привязанной цели; у `pixelationPass()`
  `pixelSize` — только число; свой свет регистрируется `CustomLight.registerNode(…)`; struct-хранилище — всегда массив:
  `storage.element(0).get('member')`; `iridescenceThicknessRange` → `iridescenceThicknessMinimum` и `…Maximum`; внутри
  рендереров — `WeakRef` и `FinalizationRegistry`; матрицы XR-камеры — от первой подкамеры. Строки дрейфа —
  `03-runtime-landscape.md` §2.3.
- **Нужное страницам из r184–r186**: `SunLight` с каскадными тенями в `WebGLRenderer`; ретрорефлективность
  `MeshPhysicalMaterial`; `Object3D.dispose()` (свой класс с `dispose()` зовёт `super.dispose()`); полноэкранные
  проходы — без MSAA; `TAAUNode` (TAA с апскейлом, MSAA выключить) [S10], `TRAANode` с узлом скоростей, `SSRNode` с
  денойзером, `SSGINode`, нативные сплаты `[документация]` `[исходник]` [S3] [S11].
- **Откат по требованию** — PR #34334 (открыт): `WebGLBackend` и `GLSLNodeBuilder` уходят в отдельный чанк
  `'three/webgpu/fallback'`, сборка WebGPU легче на 24,3 КБ gzip `[документация]` [S9]; войдёт ли в r187 —
  `[не проверено]`.

### 1.2. R3F, drei и постобработка

- **R3F 9.8.2**: peer `react ≥ 19 < 19.4` (React 19.3.1 совместим); DPR сам пересчитывается при переносе окна на другой
  монитор и при зуме (проп `dpr` его перезаписывает); внутри — `new THREE.Clock()` и `PCFSoftShadowMap`, отсюда два
  предупреждения с r186, это не ошибка своего кода `[документация]` `[исходник]` [S12].
- **R3F 10.0.0-alpha.6**: `WebGPURenderer` по умолчанию с откатом на WebGL2; GLSL и библиотеки на GLSL — входом
  `'@react-three/fiber/legacy'`; GLSL-материал на WebGPU-холсте — предупреждение, узловой на legacy-входе — ошибка; проп
  `gl={…}` на основном входе бросает ошибку; вход `'@react-three/fiber/webgpu'` устарел; рендерер грузится чанком при
  первом `Canvas`; TSL-хуки (`useUniforms`, `useNodes`, `useRenderPipeline` и др.) — в пакете @react-three/tsl, где
  `latest` — альфа; фаза `physics` с шагом 1/60; общий рендерер для нескольких `Canvas` `[документация]` [S12]. Вес —
  392,9 КБ br одним файлом, legacy-вход — 432,8: WebGPU-чанк остаётся в бандле `[проверено]` [S43].
- **drei 10.7.9**: правки `AccumulativeShadows` и `SoftShadows` под новые three; 11.0.0-alpha.7 — вход для WebGPU и
  переписанные компоненты; `Text` (troika) под WebGPU — задача #2588 открыта `[документация]` [S13] [S28].
- **Пост на WebGL**: pmndrs `postprocessing` 6.39.5 — peer `three ≥ 0.168 < 0.187`; ветка v7 (7.0.0-beta.16) — peer
  `three ≥ 0.179 < 0.184`: с r186 не ставится, WebGPU не заявлен; сопровождающий связывает WebGPU с днём, когда
  `WebGPURenderer` официально заменит `WebGLRenderer`. @react-three/postprocessing 3.2.2 — peer fiber ≥ 9.7 и
  `postprocessing ^6.36`; `n8ao` 2.0.1 — только pmndrs и WebGL `[данные: npm]` `[документация]` [S1] [S14].
- **Пост на WebGPU** — TSL: `RenderPipeline` и `pass()`, узлы `bloom`, `fxaa`, `smaa`, `traa`, `taau`, `ssaaPass`, GTAO,
  SSR, SSGI, DOF, `GodraysNode`; в R3F 10 — `useRenderPipeline` `[исходник]` [S11].

### 1.3. Рядом со сценой: глобусы, карты, физика, текст, анимация

| пакет | назначение | вес, КБ br | лицензия | релизов за год · версия |
|---|---|---|---|---|
| `cobe` | декоративный точечный глобус | 5,4 | MIT | 2 · 2.0.1 |
| `globe.gl` и `three-globe` | глобус с данными на three | 435,2 | MIT | 7 и 7 · 2.46.2 и 2.45.6 |
| deck.gl, `_GlobeView` | большие данные на глобусе | 186,4 | MIT | 22 · 9.4.0; WebGPU у deck.gl по документации к продакшену не готов [S29] |
| MapLibre GL JS (`maplibre-gl`) | настоящая карта, проекция `globe`, рельеф | 232,6 + тайлы и стиль | BSD-3-Clause | 38 · 6.16.0 |
| CesiumJS (`cesium`) | 3D Tiles, геоточность | не мерился | Apache-2.0 | 13 · 1.146.0 |
| Rapier (@dimforge/rapier3d и compat-сборка) | физика на wasm | wasm 832,2; compat 1 167,2 | Apache-2.0 | 3 · 0.21.0; репозиторий rapier.js в архиве, код — в dimforge/rapier [S41] |
| Jolt (`jolt-physics`) | физика на wasm | wasm 499,2 + JS 92,8; compat 612,5 | MIT | 5 · 1.1.1 |
| `cannon-es` | физика на чистом JS | 20,9 | MIT | заморожен: 0 · 0.20.0 |
| `troika-three-text` | SDF-текст, глифы из файла шрифта на лету | 143,5 с three | MIT | 2 · 0.52.5; WebGPU — PR #393 открыт [S28] |
| `three-msdf-text-utils` | MSDF-текст по готовому атласу, есть вход для WebGPU (`MSDFTextNodeMaterial`) | 305,3 и 416,0 — раздут общим файлом аддонов → §6 | ISC | 7 · 1.5.0 |
| GSAP и ScrollTrigger (`gsap`) | таймлайны, прокрутка | 40,4; с Lenis 44,9 | Standard «No Charge» | 4 · 3.15.0 |
| `lenis` | плавная прокрутка | 4,9 | MIT | 14 · 1.3.27; ветка 2.0 — тег `dev` |
| Motion (`motion`) | DOM и SVG, 3D нет | 22 | MIT | 85 · 14.7.1 |
| Theatre.js | таймлайн-редактор | — | core Apache-2.0, studio AGPL | заморожен: релизов нет больше двух лет · 0.7.2 |

Вес — `[проверено]` [S43], версии — `[данные: npm]` [S1].

## 2. Что брать по задаче и месту

### 2.1. Задача → стек

| задача | стек | почему | вес, КБ br | откат |
|---|---|---|---|---|
| один фирменный объект или фон на шейдере (SDF) | свой фрагментный шейдер WebGL2 (raymarch) в инлайн-скрипте; градиент — Paper Shaders | 0 зависимостей, холст без сети, полный контроль | 0,7–3; 5,5 | кадр той же сцены со стенда (`../16-js-scenes/01-engine.md` §9) или CSS-градиент; при `prefers-reduced-motion` — кадр |
| длинная сцена-мир: сотни объектов, путь камеры, такты по прокрутке | свой многопроходный движок: инстансы, движение шейдером, HDR → свечение → тон | сотни объектов одним вызовом, без ассетов | вес набора — `../16-js-scenes/01-engine.md` §10 | постер и раскадровка со стенда |
| продукт из GLB: вращение, свет, прокрутка | three 0.186.1 `WebGLRenderer` + `GLTFLoader` + Meshopt (KTX2 — при тяжёлых текстурах) + `RoomEnvironment` + `NeutralToneMapping`; прокрутка — GSAP и Lenis | самый распространённый и лёгкий путь с моделью; весь pmndrs-пост | 158,2 (+ 40,4–44,9 прокрутка) | постер AVIF или WebP — LCP; без WebGL2 — постер |
| витрина товара и AR | model-viewer 4.4.0 отдельным скриптом | AR (WebXR, Scene Viewer, Quick Look), постер, ленивость, доступность из коробки | 229,9 | атрибут `poster`; без WebGL — постер |
| сцена в React-кабинете | R3F 9.8.2 + drei 10.7.9 (+ @react-three/postprocessing 3.2.2), `frameloop="demand"`, `React.lazy` | стабильный стек; R3F 10 — альфа | 250,5–361,4 | заглушка `Suspense`, постер |
| ≥ 100 тыс. частиц, жидкость, поля (compute) | three WebGPU + TSL (`instancedArray`, `Fn().compute()`); своя симуляция — TypeGPU; на WebGL — `GPUComputationRenderer` до 1024² точек | compute есть только у WebGPU; откат на WebGL2 эмулирует простые ядра | 173,1–198,5 (+ 69,3 TypeGPU) | WebGL2-бэкенд three с меньшим числом частиц; видео-петля |
| реальное место (сплат) | Spark 2.4 (three WebGL, LoD, SOG и SPZ), нативные сплаты three r186 (`WebGPURenderer`, легче и новее) или вьюер PlayCanvas и SuperSplat (SOG, потоковый LoD) | зрелость Spark и PlayCanvas; нативные three — 216,6 против 782,2 | 216,6–782,2 + файл сплата | постер или видео пролёта |
| игровой мир с физикой | PlayCanvas (редактор) или Babylon (Havok: @babylonjs/havok 1.3.14, MIT); на three — Rapier (@react-three/rapier 2.2.0) или Jolt; простое — `cannon-es` | готовые физика, ввод, инспектор | 400–700 + wasm 500–830 | физику грузить после первого взаимодействия; постер |
| данные на глобусе или карте | декор — `cobe`; данные — deck.gl `_GlobeView` или `globe.gl`; настоящая карта — MapLibre GL 6 (проекция `globe`); 3D Tiles — Cesium | вес и назначение | 5,4; 186,4; 435,2; 232,6 | статичная карта-картинка |
| 3D-текст | заголовок — HTML и CSS 3D (SEO, доступность); в сцене — `troika-three-text` (WebGL, кириллица из файла шрифта) или MSDF (`three-msdf-text-utils`: WebGL и WebGPU, атлас с кириллицей заранее, алиас аддонов → §6); объёмные буквы — `TextGeometry` или запечь в GLB | чёткость на любом масштабе | 0; 143,5; ≈ 115–180 после алиаса | HTML-текст |
| движение без ввода; точное движение по прокрутке | видео; секвенция кадров в `<canvas>` | 0 WebGL | 0–3 | постер |

Позиция таблицы — `[мнение]` базы по замерам и документации; веса — `[проверено]` [S43].

### 2.2. Холст Claude Design

Сети на холсте нет, кроме шрифтов Google и загрузок (cd 05/03 §2); канон того, что холст исполняет и как класть на него
библиотеку и модель, — cd 05/03 §3. Здесь — что из спектра туда идёт.

1. **Свой WebGL2 кодом артборда** — основной путь для объекта, фона, частиц и мира: 0 загрузок, 0,7 КБ br у примера
   raymarch `[проверено]` [S43]; контракт сцены — `../16-js-scenes/01-engine.md`. WebGPU на холсте — только если без
   него нет эффекта, и с откатом; на холсте он не проверялся `[не проверено]`.
2. **Библиотека — только под модель GLB**: как её положить — cd 05/03 §3.1–3.3 (динамический `import()` с
   `cdn.jsdelivr.net/npm/` и точной версией у живого прототипа и прохода движения; модель — base64 в `.glb.json`,
   файл `.glb` холст не отдаёт). Вес three под GLB-сцену — 158,2 КБ br `[проверено]` [S43].
3. **Сжатие модели — Meshopt**: декодер — JS со встроенным wasm, 6,8 КБ br, холст его исполняет (cd 05/03 §1). Draco и
   KTX2 требуют отдельный wasm (57,4 и 212,2 КБ br) и пути декодеров, а файлы `.ktx2` холст не отдаёт. Окружение —
   `RoomEnvironment` кодом, а не файл `.hdr` `[проверено]` [S43].
4. **Что по умолчанию тянет wasm или сцену с CDN**: dotLottie (`dotlottie-player.wasm`), Rive (`rive.wasm`), декодеры
   model-viewer (свойства `dracoDecoderLocation`, `ktx2TranscoderLocation`, `meshoptDecoderLocation`), Spline
   (`wasmPath` и сцена с `prod.spline.design`), Babylon WebGPU с GLSL-шейдерами (`glslang` и `twgsl` с
   `cdn.babylonjs.com`) `[исходник]` [S18] [S27]. Rive, dotLottie и model-viewer на холсте не проверялись, Lottie через
   `lottie-web` и JSON работает (cd 05/03 §1).
5. **Не брать на холст**: Spline (сцена с сервера Spline, водяной знак, 843,2 КБ br), Needle (лицензия, облако), R3F
   (React ради холста).

### 2.3. Остров Astro

Сайт — форк `<org>/site` на Astro; сцена встаёт островом поверх постера.

- **LCP — постер в HTML** (`<img fetchpriority="high">` или `<picture>`): canvas в LCP не участвует
  (`02-when-3d-budgets-loading.md` §2.1), сцена встаёт поверх после загрузки; порядок — там же §4.1, бюджет JS 3D — §3.1
  (≤ 200 КБ br vanilla, ≤ 300 с React); исходы страницы — site 07/03 §2.1.
- **Ванильный остров**: `<script>` в компоненте `.astro` (Astro его собирает), внутри — IntersectionObserver и `import()`
  сцены после `load` и `requestIdleCallback`: three уходит отдельным чанком, React не нужен (108,5–158,2 КБ br против
  250,5 и больше) `[проверено: вес]` `[практика: схема]`.
- **Фреймворк-остров** (сцена — React-компонент): `client:visible={{rootMargin: "200px"}}` или
  `client:idle={{timeout: 2000}}`; `client:load` для 3D не брать `[документация: Astro]` [S30]. Astro 7.4.2,
  @astrojs/react 7.1.1 (React 17–19) `[данные: npm]` [S1].
- `prefers-reduced-motion: reduce` и `navigator.connection?.saveData` → остаётся постер.
- Свой движок в острове — тот же файл сцены, что на холсте; контракт — `../16-js-scenes/01-engine.md` §1.

```astro
<!-- схема ванильного острова — [практика], запуском в Astro не проверена -->
<div class="hero">
  <img src="/hero.avif" width="1200" height="800" alt="…" fetchpriority="high" />
  <canvas class="hero-3d" aria-hidden="true"></canvas>
</div>
<script>
  const canvas = document.querySelector('.hero-3d');
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches || navigator.connection?.saveData;
  const arm = () => new IntersectionObserver(([e], io) => {
    if (!e.isIntersecting) return;
    io.disconnect();
    import('../scenes/hero.js').then((m) => m.start(canvas));   // three — отдельным чанком
  }, { rootMargin: '200px' }).observe(canvas);
  const idle = window.requestIdleCallback ?? ((f) => setTimeout(f, 1));
  if (canvas && !calm) addEventListener('load', () => idle(arm, { timeout: 2000 }), { once: true });
</script>
```

## 3. WebGPU: поддержка, откат, headless

### 3.1. Браузеры и доля пользователей

Снимок: 28.10.2026 — caniuse (данные от 22.10.2026), доли StatCounter за 09.2026, web3dsurvey, gpuweb; версии и вес §1–2 — тот же день.

| браузер | платформа | WebGPU по умолчанию | метка |
|---|---|---|---|
| Chrome, Edge | Windows, macOS, ChromeOS | с 113 | `[документация]` [S20] |
| Chrome | Android 12+ (ARM, Qualcomm, Intel) | с 121; Imagination на Android 16+ — с 139; Samsung Xclipse — не назначено | `[документация]` [S20] |
| Chrome | Linux | Intel Gen12+ — с 144; NVIDIA (драйвер 535.183.01+) на Wayland — с 147; прочие — за флагами | `[документация]` [S20] |
| Chrome | Windows ARM64 | за флагом | `[документация]` [S20] |
| Chrome, режим совместимости | Android с OpenGL ES 3.1 | с 146, по запросу `featureLevel: 'compatibility'`; ChromeOS на GLES 3.1 и Windows D3D11 — в исследовании | `[документация]` [S21] |
| Firefox | Windows | с 141 | `[документация]` [S20] |
| Firefox | macOS, Apple Silicon | с 145 на macOS 26+, с 147 — на всех версиях; caniuse пишет только macOS 26 Tahoe+ | `[документация]` `[спорно]` |
| Firefox | Linux, Intel Mac | только Nightly; выпуск — в планах Mozilla | `[документация]` [S20] |
| Firefox | Android | за флагом; работа — в планах | `[документация]` [S20] |
| Safari | macOS | 26+, только на macOS 26 Tahoe | `[документация]` `[данные]` [S19] |
| Safari | iOS, iPadOS, visionOS | 26+ | `[документация]` [S20] |
| Samsung Internet | Android | 24+ | `[данные: caniuse]` [S19] |
| Opera | десктоп | 99+ (на Linux — не по умолчанию) | `[данные: caniuse]` [S19] |
| Яндекс Браузер | — | данных нет: основа Chromium, caniuse его не отслеживает | `[не проверено]` |

| срез | WebGPU полностью | частично | WebGL2 | метка |
|---|---|---|---|---|
| мир, caniuse | 85,8 % | 3,66 % | 97,13 % | `[данные]` [S19] |
| Россия, caniuse × StatCounter | 56,6 % всего трафика = 81,3 % отслеживаемого | 2,8 % (4,0 % отслеживаемого) | 98,5 % отслеживаемого | `[данные]` [S19]; 30,4 % трафика России caniuse не отслеживает |
| реальные адаптеры, web3dsurvey | 83,21 % | — | 97,53 % | `[данные]` [S23]: сайты-участники, окно не указано |
| web3dsurvey по ОС | Windows 88 %, macOS 89 %, iOS 86 %, ChromeOS 92 %, Android 75 %, Linux 18 % | | | `[данные]` [S23] |

- caniuse считает поддержкой весь Chrome Android, а нужны Android 12+ и подходящий GPU — отсюда разница с web3dsurvey
  по Android `[практика]`.
- Неотслеживаемые 30 % трафика России — браузеры вне каталога caniuse, вероятно, в основном Яндекс Браузер `[мнение]`.
- Вывод: WebGPU есть у большинства телефонов (iOS 26+, Android 12+), но откат на WebGL2 обязателен, а последний рубеж —
  постер или видео: WebGL2 нет у ≈ 2,5–3 % `[данные]`.

### 3.2. Откат на WebGL2

```js
// three 0.186.1 — [проверено] headless: откат сам, бэкенд и вид адаптера — в отчёт
import * as THREE from 'three/webgpu';
const renderer = new THREE.WebGPURenderer({ antialias: true });   // forceWebGL: true — проверить откат
await renderer.init();                                            // обязательно вне setAnimationLoop
const adapterKind = !navigator.gpu ? 'none'
  : await navigator.gpu.requestAdapter({ featureLevel: 'compatibility' })
      .then((a) => (!a ? 'none' : a.info?.isFallbackAdapter ? 'software' : 'hardware'));
const backend = renderer.backend.isWebGPUBackend ? `webgpu-${adapterKind}` : 'webgl2-fallback';
```

- three уходит на WebGL2-бэкенд сам, если `requestAdapter()` вернул `null`; `forceWebGL: true` — принудительно; в консоли
  — «WebGPU is not available, running under WebGL2 backend»; простое compute-ядро (`instancedArray` и
  `Fn().compute()`) на откате считает верно `[проверено]` [S43].
- Babylon: `await WebGPUEngine.IsSupportedAsync`, иначе `new Engine(canvas)`; PlayCanvas: `createGraphicsDevice` с
  `deviceTypes: ['webgpu', 'webgl2']`, WebGL2 он добавляет в конец всегда; Spline выбирает бэкенд сам, один на страницу
  `[исходник]` `[документация]` [S18] [S27].
- «WebGPU или нет» решать до загрузки тяжёлого чанка: `navigator.gpu?.requestAdapter()` → динамический `import()` нужной
  сборки `[практика]`.

### 3.3. Режим совместимости и MSAA

`WebGPUBackend` three 0.186.1 всегда просит адаптер с `featureLevel: 'compatibility'`; без возможности
`core-features-and-limits` он включает `compatibilityMode = true` и ставит `renderer._samples = 0`: MSAA выключен,
`antialias: true` молча не действует `[исходник]` [S11]. Chrome открыл режим совместимости на Android с OpenGL ES 3.1 с
версии 146 `[документация]` [S21]. Сглаживание в этом режиме — узлом `fxaa()` или `smaa()` в `RenderPipeline`; TAAU и
так требует выключенного MSAA → §5.

### 3.4. Headless-проверка на Linux

| флаги поверх флагов Playwright (среди них `--use-angle=swiftshader-webgl`) | адаптер WebGPU | canvas на снимке | `WebGPURenderer` three |
|---|---|---|---|
| нет | нет: «No available adapters» | — | откат WebGL2, кадр верный |
| `--enable-unsafe-webgpu` (с `--enable-features=Vulkan` или без) | SwiftShader, `isFallbackAdapter: true` | чёрный, ошибка «A valid external Instance reference no longer exists» | `backend` webgpu, кадр чёрный, чтение буфера падает |
| `--use-angle=vulkan --enable-features=Vulkan`, без unsafe | Intel gen-12lp, не запасной | верный | webgpu: кадр и compute верны |
| то же с `--enable-unsafe-webgpu`; или `--use-angle=gl` с unsafe и Vulkan (флаги `site_probe.py` по умолчанию) | Intel gen-12lp | верный | webgpu, верно |
| `--use-angle=gl` без unsafe | нет | — | откат |
| только lavapipe, Vulkan и unsafe | SwiftShader: lavapipe Dawn не взял | белый | webgpu, кадр белый |
| «нет GPU»: `--use-angle=swiftshader --enable-unsafe-swiftshader` и unsafe | SwiftShader | чёрный | webgpu, кадр неверный, чтение буфера падает |
| «нет GPU» без unsafe | — | — | откат WebGL2, кадр верный при непрерывном цикле |

Шесть серий, 38 прогонов, Intel Iris Xe Gen12 и Mesa `[проверено]` [S43].

1. Без GPU WebGPU-кадр в headless не проверяется: проверять откат WebGL2 (он снимается верно), а логику WebGPU и compute
   — чтением буферов.
2. С GPU — `--use-angle=vulkan --enable-features=Vulkan`; Chrome советует для тестов ещё `--disable-vulkan-surface` и
   `--enable-unsafe-webgpu` `[документация]` [S22]. `site_probe.py` по умолчанию идёт с `--use-angle=gl` и флагами
   WebGPU — адаптер настоящий; режим `--gpu swiftshader` — только вместе с `--no-webgpu`, так ходит и самопроверка зонда
   `[исходник]`.
3. В отчёт замера — не только `backend`, но и `adapter.info.isFallbackAdapter`: иначе SwiftShader сойдёт за WebGPU.
4. Ловушка снимка: один кадр, затем другая работа GPU (compute) — в двух из трёх программных режимов canvas пустой;
   рендерить циклом до снимка.
5. Chrome for Testing 153 и chrome-headless-shell 153 ведут себя так же; обычный `WebGLRenderer` снимается верно во всех
   программных режимах (`MAX_SAMPLES`: SwiftShader 4, llvmpipe 8, Intel GL 16) `[проверено]` [S43].
6. `navigator.gpu` есть только в безопасном контексте: на странице с http://127.0.0.1 — да, на `about:blank` — нет
   (`../14-code-3d/08-webgpu-tsl-migration.md`).

## 4. Что агенты пишут уверенно и где ошибаются

### 4.1. Корпус кода в сети — прокси знаний модели

| маркер в поиске кода GitHub | файлов | что значит |
|---|---|---|
| `"@react-three/fiber"` | 868 352 | R3F — самый большой корпус |
| `new THREE.WebGLRenderer` | 733 184 | классический three — основа знаний |
| `WebGPURenderer` | 93 056 | в 8 раз меньше |
| `"three/tsl"` | 74 624 | TSL — новый и тонкий слой |
| `outputEncoding` рядом с `THREE` | 71 936 | удалённый API — столько же, сколько TSL |
| `"@babylonjs/core"` | 58 752 | — |
| `new THREE.Geometry()` | 56 384 | удалён в r125, но в корпусе |
| `physicallyCorrectLights` | 21 760 | удалён |
| `MeshStandardNodeMaterial` | 18 464 | — |
| `new THREE.PostProcessing` | 5 024 | имя до r183 |
| `RenderPipeline` рядом с `"three/tsl"` | 4 656 | имя с r183 |
| `WebGPUEngine` | 4 216 | Babylon WebGPU |
| `"@react-three/fiber/webgpu"` | 908 | вход R3F, устаревший в v10 |
| `from "typegpu"` | 689 | — |
| `setNodesHandler` | 247 | TSL на WebGL почти неизвестен |

`[данные: поиск кода GitHub]` [S39]: счётчики — оценки поиска, в них форки и копии библиотек. Загрузки npm за неделю до
снимка: `three` 20,7 млн, R3F 5,7 млн, `gsap` 5,2 млн, troika 4,0 млн, drei 3,8 млн, `lenis` 1,6 млн, `postprocessing`
1,1 млн, `regl` 0,85 млн, `ogl` 0,75 млн, model-viewer 0,60 млн, Spline 0,55 млн, Babylon 0,31 млн, Spark 0,25 млн,
`typegpu` 0,23 млн, `playcanvas` 0,11 млн, Needle 3,5 тыс. `[данные]` [S2]: с транзитивными установками.

Вывод: модель лучше всего пишет классический three на `WebGLRenderer` с GLSL, R3F 9 и GSAP; TSL, `RenderPipeline`,
R3F 10, TypeGPU и нативные сплаты three — тонкий и быстро меняющийся слой, где модель помнит старые имена: TSL
переименовывался в r179, r181, r183, r185 и r187 `[мнение]`. Всё, что вышло после отсечки знаний модели, она не знает
вовсе — у практиков отставание данных обучения оценивают в 6–18 месяцев `[мнение]` [S40].

### 4.2. Типичные ошибки в three.js

| модель пишет | правильно (three 0.186.1, r187) | как проявится | чем ловится |
|---|---|---|---|
| `renderer.outputEncoding = THREE.sRGBEncoding`, `texture.encoding` | `outputColorSpace = SRGBColorSpace` (по умолчанию); `texture.colorSpace = SRGBColorSpace` у цветовых карт | тихо: цвета «вымыты» или темнее у карт из `TextureLoader` | `tsc` (ошибка), сравнение кадра |
| `physicallyCorrectLights`, `useLegacyLights` | ничего; свет в физических единицах | тихо: свет из старых уроков темнее или ярче | `tsc` |
| `THREE.Geometry`, `BoxBufferGeometry` | `BufferGeometry`, `BoxGeometry` | ошибка выполнения | `tsc`, консоль |
| `<script src="…/three.min.js">`, `'three/examples/js/…'`, `THREE.OrbitControls` | ES-модули, `'three/addons/…'` | 404 или undefined | консоль |
| import map с разными версиями в ключах `"three"` и `"three/addons/"` | одна версия в обоих | поломка загрузчиков | ревью карты |
| `RGBELoader`, `new THREE.Clock()`, `PCFSoftShadowMap` | `HDRLoader`, `Timer`, `PCFShadowMap` | предупреждение | `@deprecated` в типах, консоль |
| `ShaderMaterial`, `onBeforeCompile`, `EffectComposer` при `WebGPURenderer` | узловые материалы и TSL, `RenderPipeline` | пусто или ошибка | консоль; правило React Doctor `three-webgpu-no-legacy-material-api` [S36] |
| `renderer.render()` до `await renderer.init()` вне `setAnimationLoop` | `await renderer.init()` | ошибка | консоль |
| TSL: `PI2`, `label()`, `PostProcessing`, `directionToColor()`, `positionLocal` у скиннинга, `storage().get()` у struct | `TWO_PI`, `setName()`, `RenderPipeline`, `packNormalToRGB()`, `positionGeometry`, `.element(0).get()` (r187) | ошибка или неверный кадр | Migration Guide [S4], консоль |
| pmndrs `postprocessing` при `WebGPURenderer` | TSL-пост | не работает | консоль |
| R3F: `gl={canvas => …}`, `MeshProps`; в v10 — `gl` на основном входе, GLSL на WebGPU-холсте | v9: `gl={(props) => …}`, `ThreeElements['mesh']`; v10: `'@react-three/fiber/legacy'` или узловые материалы | ошибки типов или выполнения | `tsc`, консоль |
| `renderer.setPixelRatio(window.devicePixelRatio)` без потолка | бюджет пикселей и свой размер буфера → §5 | 9× пикселей на телефоне с DPR 3 | правило React Doctor `three-cap-device-pixel-ratio` [S36] |
| пакеты-покойники: @studio-freight/lenis, `framer-motion-3d`, @mkkellogg/gaussian-splats-3d, @lumaai/luma-web, Theatre.js | `lenis`; GSAP или анимация из Blender; Spark или нативные сплаты three | устаревание | `npm view … deprecated time` |
| `npm i @needle-tools/engine`, `npm i @react-three/tsl` | `@stable` у Needle; у TSL-хуков — только альфа | альфа в продакшене | `npm view … dist-tags` |
| model-viewer и `three@latest` в одном бандле | model-viewer отдельным скриптом | ERESOLVE | установка `[проверено]` |
| `lygia` в коммерческом проекте | свои функции или Patron License | лицензионный риск | `npm view lygia license` |

Строки — Migration Guide, типы и пакеты `[документация]` `[исходник]` [S4] [S11]; «тихие» последствия — по механизму
`[практика]`; у практиков перечень частых ошибок совпадает: `Geometry`, `sRGBEncoding` `[мнение]` [S40].

### 4.3. Как ловить устаревший код

1. Закрепить версии без `^` (`three@0.186.1`) и так же в import map; перед кодом —
   `npm view <пакет> version dist-tags peerDependencies` у Needle, R3F, `postprocessing`, model-viewer `[практика]`.
2. Дать агенту `https://threejs.org/llms.txt` (и полную версию llms-full.txt, с r183) и разделы Migration Guide от
   «своей» версии до текущей `[документация]` [S4] [S7]. Ловушка: пример import map в llms.txt указывает на
   неминифицированную сборку three с jsDelivr — ядро 204 КБ br (`../09-web-runtime/01-threejs-core.md` §1.2).
3. `tsc --noEmit` (или `// @ts-check`) с @types/three той же версии: удалённое — ошибка TS2339 (`outputEncoding`,
   `Geometry`, `useLegacyLights`), устаревшее помечено `@deprecated` (`Clock`, `RGBELoader`, `PCFSoftShadowMap`) и
   ловится правилом no-deprecated линтера typescript-eslint `[проверено]` [S43].
4. Headless-прогон с перехватом консоли: провал на `/deprecated|has been removed|not supported/i` и на любую ошибку;
   вызовов отрисовки больше нуля; в отчёте `backend` и `isFallbackAdapter`; кадр — после цикла рендера `[проверено]` → §3.4
5. React-код — линтеры правил кода от ИИ: oxlint-plugin-react-doctor 0.9.18 с правилами three и R3F,
   @react-three/eslint-plugin 0.1.2 `[данные: npm]` `[документация]` [S36].

## 5. Чёткость

Канон своего движка — `../16-js-scenes/01-engine.md` §6: формула DPR, бюджеты холста ПК и телефона, множитель плотности
с гистерезисом. Здесь — рычаги three и библиотек.

| рычаг | правило | метка |
|---|---|---|
| размер буфера | считать самому по бюджету пикселей канона (`../16-js-scenes/01-engine.md` §6, потолок DPR 2) и задавать `setSize(w, h, false)`; manual three не рекомендует `setPixelRatio(window.devicePixelRatio)`: при DPR 3 — 9× пикселей | `[проверено]` (канон движка); `[документация]` [S6] |
| пересчёт | зум и перенос окна на другой монитор меняют DPR — пересчитывать буфер; примеры three этого не делают, R3F 9.8.2 делает сам | `[практика]` [S35]; `[документация]` [S12] |
| точный размер | `ResizeObserver` с `devicePixelContentBoxSize` (Chrome 84+, Firefox 108+; в Safari нет → `Math.round(clientWidth * dpr)`) — без пересэмплирования | `[данные: MDN BCD]` [S37] |
| MSAA на WebGL | `antialias: true` сглаживает только основной буфер; с постом MSAA — в цели: pmndrs `new EffectComposer(renderer, { multisampling: 4 })` и `antialias: false` у рендерера; у `EffectComposer` three цель по умолчанию — `HalfFloatType` без `samples` → своя цель с `samples: 4` | `[исходник]` [S11] |
| MSAA на WebGPU | `antialias: true` → 4 сэмпла; `pass(scene, camera)` наследует `renderer.samples`; полноэкранные проходы — без MSAA; в режиме совместимости MSAA = 0 → §3.3; TAAU требует выключенного MSAA | `[исходник]` [S11] |
| FXAA, SMAA, TAA | FXAA — дешевле всех, но мылит мелочь и текст; SMAA чище по кромкам, 3 прохода; TAA и TRAA лучше всех против мерцания бликов и тонких линий, но дают шлейф в движении; на WebGL — `TAARenderPass` (накопление при неподвижной камере), на WebGPU — `TRAANode` (со скоростями) и `TAAUNode` (с апскейлом) | `[консенсус]`; узлы — `[исходник]` [S11] |
| адаптивное разрешение | свой движок — множитель плотности канона (`../16-js-scenes/01-engine.md` §6); drei `PerformanceMonitor` и `AdaptiveDpr`; WebGPU — `PassNode.setResolutionScale()` и TAAU; model-viewer — `minimumRenderScale` | `[документация]` [S13] |
| полосы на градиентах | `material.dithering = true`; pmndrs `EffectPass.dithering = true`; буферы поста — `HalfFloatType`; свой движок — дизеринг после sRGB (`../16-js-scenes/01-engine.md` §5) | `[исходник]` [S11] |
| тон-маппинг | продукт и честный цвет — `NeutralToneMapping` (Khronos PBR Neutral: базовые цвета 1:1 до порога, запас под блики; у model-viewer он по умолчанию); сильный HDR (закат, неон) — `AgXToneMapping`; ACES сдвигает тон и теряет насыщенность; тон — один раз в конце цепочки: у pmndrs — `ToneMappingEffect` при `renderer.toneMapping = NoToneMapping`, у композера three — `OutputPass`; пара с видом Blender — `../09-web-runtime/01-threejs-core.md` §5.1 | `[документация]` [S15] [S33]; цепочка — `[практика]` |
| цвет | `outputColorSpace = SRGBColorSpace`; цветовые карты — `SRGBColorSpace`, данные (нормали, шероховатость) — линейно; `GLTFLoader` ставит сам | `[документация]` |
| анизотропия и мипы | `texture.anisotropy = renderer.capabilities.getMaxAnisotropy()` у поверхностей под углом (пол, надписи); мипы — по умолчанию или заранее в KTX2; свой движок — анизотропия 4 (`../16-js-scenes/01-engine.md` §4) | `[исходник]`; `[практика]` |
| линии | толстые — `Line2` и `LineSegments2` с `LineMaterial` (ширина в пикселях), на WebGPU — `Line2NodeMaterial`; в шейдере — сглаживание `smoothstep` с шириной `fwidth()` (сетки, SDF); вырезы под MSAA — `alphaToCoverage` | `[исходник]`; `[практика]` [S34] |
| текст | MSDF держит острые углы на любом масштабе (атлас с кириллицей — заранее); troika — SDF из файла шрифта на лету (WebGL); HTML-текст поверх canvas — самый чёткий | `[практика]`; пакеты — `[проверено]` [S43] |

## 6. Лицензии и ловушки

| что | ловушка | что делать | метка |
|---|---|---|---|
| `lygia` 1.4.1 | Prosperity Public License 3.0.0: бесплатно — некоммерческое; коммерция — 30-дневная проба на компанию, дальше Patron License | в код заказчика не вставлять: свои функции или Patron | `[документация]` [S26] |
| GSAP 3.15.0 | «Standard No Charge» (Webflow): бесплатно всё, включая SplitText и MorphSVG; запрет — no-code-конструкторы анимаций, конкурирующие с Webflow | сайты кодом — можно; продукт-конструктор — к юристу | `[документация]` [S25] |
| Needle Engine | Hobby — только некоммерческое, логотип, 1 проект; Pro — €49/мес (€588/год); `latest` в npm — альфа 6.0.0-alpha.7 | ставить `@stable` (5.1.16); Pro — в смету до выбора | `[документация]` [S24] |
| Spline | в npm лицензии нет; водяной знак зашит издателем в данные сцены; AGENTS.md пакета просит кредит «Made with Spline»; адрес `.splinecode` даёт только экспорт редактора | ToS Spline — до встраивания в продукт заказчика | `[документация]` `[мнение вендора]` [S27] |
| @theatre/studio | AGPL | не в продакшен-бандл | `[документация]` |
| model-viewer 4.4.0 | peer `three ^0.183` (внутри 0.183.2): ERESOLVE рядом с `three@0.186.1` в одном бандле | отдельным скриптом — готовая сборка `…/dist/model-viewer.min.js` | `[проверено]` [S15] |
| `three-msdf-text-utils` 1.5.0 | оба входа импортируют `'three/examples/jsm/Addons.js'` → в бандл попадают таблицы RectAreaLight, chevrotain, GLTFExporter: 305,3 и 416,0 КБ br | алиас бандлера `'…/Addons.js'` → `'…/loaders/FontLoader.js'` (≈ 115–180) | `[проверено]` [S43] |
| wasm Rive и dotLottie | по умолчанию грузятся с jsDelivr или unpkg | свой путь к wasm; на холсте — не брать → §2.2 | `[исходник]` |
| pmndrs `postprocessing` 6.39.5 | peer `three ≥ 0.168 < 0.187`: с выходом r187 `npm i three@latest postprocessing` даст ERESOLVE; v7 (7.0.0-beta.16) — peer `three < 0.184`, с r186 не ставится, WebGPU не заявлен | `three@0.186.1` в паре; на WebGPU — TSL `RenderPipeline` | `[данные: npm]` [S1] [S14] |
| @react-three/tsl | только альфа: `latest` = 10.0.0-alpha.6 | в продакшен не брать | `[данные: npm]` [S1] |
| @react-three/rapier 2.2.0 | поле лицензии в npm пусто | проверить LICENSE репозитория | `[данные: npm]` [S1] |
| Rapier | репозиторий rapier.js в архиве, JS-обвязка — в dimforge/rapier | пакеты @dimforge/rapier3d 0.21.0 живые | `[документация]` [S41] |
| @lumaai/luma-web | «no longer supported» | Spark или нативные сплаты three | `[данные: npm]` [S1] |

## Частые ошибки

- Тянуть three или R3F ради объекта, который один шейдер рисует за 0,7–3 КБ br.
- Брать WebGPU «потому что современнее»: +64,6 КБ br к кубу, дорогой откат, pmndrs-пост не работает.
- Ставить `three@latest` рядом с pmndrs `postprocessing` или model-viewer — ERESOLVE.
- Ставить Needle или @react-three/tsl по тегу `latest` — альфа в продакшене.
- Нести R3F 10 в продакшен: проп `gl` на основном входе бросает ошибку, GLSL-материал на WebGPU-холсте не рисуется.
- Засчитать SwiftShader за WebGPU в headless: `backend` = webgpu, а кадр пустой.
- Снять кадр после одного рендера и compute — canvas пустой.
- Надеяться на `antialias: true` у WebGPU на старом Android — MSAA там 0.
- `setPixelRatio(devicePixelRatio)` без потолка — 9× пикселей при DPR 3.
- Вставлять `lygia` в коммерческий код.
- Писать по памяти пакеты-покойники: @studio-freight/lenis, `framer-motion-3d`, @mkkellogg/gaussian-splats-3d,
  @lumaai/luma-web, Theatre.js.
- Класть на холст Spline, бандл библиотеки файлом, `.glb`, Draco или KTX2 (cd 05/03 §2).
- Брать минифицированный модуль three с CDN без переназначения ядра в import map — тянется неминифицированное ядро
  204 КБ br (`../09-web-runtime/01-threejs-core.md` §1.2).

## Чек-лист

- [ ] Свой движок проверен первым; библиотека выбрана по задаче (→ §2.1) и месту (→ §2.2, §2.3)?
- [ ] Версии закреплены без `^` и одинаково в import map; перед кодом — `npm view <пакет> version dist-tags peerDependencies`?
- [ ] Вес JS 3D посчитан сборкой и уложен в бюджет `02-when-3d-budgets-loading.md` §3.1?
- [ ] WebGPU — только при эффекте, которого нет на WebGL; откат на WebGL2 и постер проверены?
- [ ] В отчёте замера — `backend` и `isFallbackAdapter`; кадр снят после цикла рендера?
- [ ] `tsc` с @types/three той же версии; в консоли нет `deprecated`, `removed`, `not supported`?
- [ ] Буфер — по бюджету пикселей; MSAA — в цепочке поста; в режиме совместимости — узел сглаживания?
- [ ] Лицензии `lygia`, GSAP, Needle, Spline и Theatre studio сверены (→ §6)?
- [ ] Холст: свой WebGL2, библиотека — только под GLB по cd 05/03 §3; остров: постер — LCP, сцена — при подлёте к окну?

## Открытые вопросы и противоречия

1. **Холст и бандл библиотеки.** Вариант «один самодостаточный ESM-файл загрузкой» (esbuild; three 108,5–158,2 КБ br)
   расходится с каноном cd 05/03 §3.1–3.2: бандл библиотеки файлом холста не публикуется, адрес загрузки
   `/_blob/<id>` на claude.ai не проверен, проверен `import()` с CDN у живого прототипа. Позиция базы — канон cd; сцены
   этого файла на самом холсте не запускались `[не проверено]`.
2. **Яндекс Браузер** — WebGPU в нём не проверен; 30 % трафика России caniuse не видит, и за ними, вероятно, в основном
   он `[мнение]`.
3. **Телефоны** — производительность WebGPU и отката на реальных телефонах не мерилась; первый кадр WebGPU в headless
   медленнее WebGL2 (`03-runtime-landscape.md` §2.2).
4. **r187** — войдёт ли PR #34334 (откат по требованию); когда pmndrs `postprocessing` снимет предел `< 0.187` и придёт
   ли в v7 WebGPU.
5. **Зрелость `WebGPURenderer`** — сторонние статьи зовут его готовым к продакшену, manual three — экспериментальным;
   позиция базы — manual `[спорно]` [S42].
6. **DPR тяжёлых сцен** — форум three.js советует DPR 1,5 для сцен, упёртых в заливку [S35]; канон движка — бюджет
   пикселей с потолком 2 и полом множителя 0,7, потому что потолок 1,5 на телефоне заказчик назвал «нечётко»
   (`../16-js-scenes/01-engine.md` §6); бюджет `02-when-3d-budgets-loading.md` §3.1 держит DPR телефона ≤ 1,5
   `[спорно]`. Позиция базы — канон движка.
7. **Firefox на macOS** — gpuweb wiki: с 145 на macOS 26+ и с 147 на всех версиях; caniuse — только macOS 26 Tahoe+
   `[спорно]`.
8. **Не мерились**: вес TresJS, Threlte, CesiumJS и Unicorn Studio.

## Источники

Все адреса открыты на день снимка (→ §3.1).

- [S1] Реестр npm, `npm view <пакет> --json` по 96 пакетам: версия, dist-tags, даты публикаций, лицензия, peerDependencies,
  deprecated — `[данные]`.
- [S2] npm downloads API, неделя до снимка: https://api.npmjs.org/downloads/point/ — `[данные]`.
- [S3] three.js, release r186: https://github.com/mrdoob/three.js/releases/tag/r186 ; вехи:
  https://github.com/mrdoob/three.js/milestones — `[документация]` `[данные]`.
- [S4] three.js, Migration Guide (разделы 179→187): https://github.com/mrdoob/three.js/wiki/Migration-Guide — `[документация]`.
- [S5] three.js manual, WebGPURenderer: https://threejs.org/manual/#en/webgpurenderer — `[документация]`.
- [S6] three.js manual, Responsive Design (HD-DPI): https://threejs.org/manual/#en/responsive — `[документация]`.
- [S7] three.js llms.txt: https://threejs.org/llms.txt ; PR добавления: https://github.com/mrdoob/three.js/pull/32673 —
  `[документация]`.
- [S8] PR «WebGLRenderer: Add NodeMaterial compatibility layer» (r184): https://github.com/mrdoob/three.js/pull/32851 —
  `[документация]`.
- [S9] PR «WebGPURenderer: Load the WebGL fallback on demand»: https://github.com/mrdoob/three.js/pull/34334 —
  `[документация]`.
- [S10] PR «TAAUNode»: https://github.com/mrdoob/three.js/pull/33368 — `[документация]`.
- [S11] Исходники three 0.186.1 из npm: `WebGPUBackend`, `Renderer`, `PassNode`, `EffectComposer`, `WebGLNodesHandler`,
  `TAAUNode`, `constants`, `WebGLCapabilities`, узлы TSL display — `[исходник]`.
- [S12] R3F, релизы v9.8.0, v9.8.2, v10.0.0-alpha.4–6: https://github.com/pmndrs/react-three-fiber/releases —
  `[документация]`.
- [S13] drei, релизы v10.7.9 и v11.0.0-alpha: https://github.com/pmndrs/drei/releases ; AdaptiveDpr и PerformanceMonitor:
  https://github.com/pmndrs/drei/tree/master/docs/performances — `[документация]`.
- [S14] pmndrs postprocessing, релизы: https://github.com/pmndrs/postprocessing/releases ; issue #643:
  https://github.com/pmndrs/postprocessing/issues/643 — `[документация]`.
- [S15] model-viewer v4.4.0: https://github.com/google/model-viewer/releases/tag/v4.4.0 ; тон-маппинг:
  https://modelviewer.dev/examples/tone-mapping — `[документация]`.
- [S16] Spark, релизы v2.0.0–v2.4.0: https://github.com/sparkjsdev/spark/releases — `[документация]`.
- [S17] PlayCanvas engine v2.23.0: https://github.com/playcanvas/engine/releases/tag/v2.23.0 — `[документация]`.
- [S18] Babylon.js 9.x: https://gamedev.net/news/5369-babylonjs-9230-released/ (через поиск); исходник WebGPU-движка
  @babylonjs/core 9.32.1 — `[документация]` `[исходник]`.
- [S19] caniuse: https://github.com/Fyrd/caniuse/blob/main/features-json/webgpu.json и соседние webgl2, transforms3d,
  webcodecs; региональные доли StatCounter — папка region-usage-json там же — `[данные]`.
- [S20] gpuweb, Implementation Status: https://github.com/gpuweb/gpuweb/wiki/Implementation-Status — `[документация]`.
- [S21] Chrome, «What's New in WebGPU (Chrome 146)»: https://developer.chrome.com/blog/new-in-webgpu-146 — `[документация]`.
- [S22] Chrome, «Supercharge Web AI model testing: WebGPU, WebGL, and Headless Chrome»:
  https://developer.chrome.com/blog/supercharge-web-ai-testing — `[документация]`.
- [S23] web3dsurvey: https://web3dsurvey.com/ — `[данные]`.
- [S24] Needle, тарифы: https://cloud.needle.tools/pricing ; файл LICENSE пакета 5.1.16 — `[документация]`.
- [S25] GSAP, Standard License: https://gsap.com/standard-license ; история правок: https://tostracker.app/document/gsap —
  `[документация]` `[данные]`.
- [S26] lygia, LICENSE: https://github.com/patriciogonzalezvivo/lygia/blob/main/LICENSE.md — `[документация]`.
- [S27] Spline runtime 2.0.114, файл AGENTS.md в пакете npm — `[документация]`.
- [S28] troika, PR #393 (WebGPU): https://github.com/protectwise/troika/pull/393 ; drei, issue #2588:
  https://github.com/pmndrs/drei/issues/2588 — `[данные]`.
- [S29] deck.gl, WebGPU: https://deck.gl/docs/developer-guide/webgpu — `[документация]`.
- [S30] Astro, директивы: https://docs.astro.build/en/reference/directives-reference/ — `[документация]`.
- [S31] TypeGPU: https://docs.swmansion.com/TypeGPU/ ; связка с three: https://docs.swmansion.com/TypeGPU/ecosystem/typegpu-three/
  — `[документация]`.
- [S32] TresJS, WebGPU: https://tresjs-docs.netlify.app/api/advanced/web-gpu — `[документация]` (через поиск).
- [S33] Khronos, PBR Neutral:
  https://www.khronos.org/news/press/khronos-pbr-neutral-tone-mapper-released-for-true-to-life-color-rendering-of-3d-products
  — `[документация]`.
- [S34] Ben Golus, «The Best Darn Grid Shader (Yet)»: https://bgolus.medium.com/the-best-darn-grid-shader-yet-727f9278b9d8 —
  `[практика]`.
- [S35] Форум three.js, «HiDPI + fractional scaling»:
  https://discourse.threejs.org/t/hidpi-fractional-scaling-performance-pitfalls-and-best-practices/87114 — `[практика]`.
- [S36] React Doctor, правила three: https://www.react.doctor/docs/rules/react-doctor/three-cap-device-pixel-ratio ;
  https://www.react.doctor/prompts/rules/react-doctor/three-webgpu-no-legacy-material-api.md — `[документация]`.
- [S37] MDN BCD, ResizeObserverEntry: https://github.com/mdn/browser-compat-data/blob/main/api/ResizeObserverEntry.json —
  `[данные]`.
- [S38] Скраб видео: https://www.hontran.dev/blog/scroll-scrubbed-video-stutters-fix ;
  https://muffinman.io/blog/scrubbing-videos-using-javascript/ — `[практика]`.
- [S39] GitHub, поиск кода через API: https://api.github.com/search/code — `[данные]`.
- [S40] «Why LLMs Fail at Modern Three.js»: https://yugmastudio.web.app/blog/teaching-llms-the-modern-three-js-api/ —
  `[мнение]`.
- [S41] rapier.js (архив): https://github.com/dimforge/rapier.js — `[документация]`.
- [S42] Сторонние оценки зрелости WebGPU: https://www.utsubo.com/blog/webgpu-threejs-migration-guide ;
  https://www.buildmvpfast.com/blog/threejs-webgl-to-webgpu-renderer-migration-2026 — `[мнение]`.
- [S43] Замеры базы на одной машине (Linux, Intel Iris Xe Gen12, Mesa, Debian 13): 45 сборок минимальных сцен (esbuild
  0.28.2, ESM, minify, brotli q11; wasm и чанки — отдельно); 6 серий headless-проб WebGPU и WebGL, 38 прогонов (Chrome
  153, Chromium 152, Chrome for Testing 153, chrome-headless-shell 153, Playwright 1.63); `tsc` с @types/three 0.186.0;
  установка пакетов с проверкой ERESOLVE — `[проверено]`.
