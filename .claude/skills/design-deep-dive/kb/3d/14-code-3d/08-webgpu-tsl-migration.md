# 08 · WebGPU и TSL для сцены кода: когда переходить, сколько стоит вход, как откатываться, что переписывать, чем мерить

Дорожка CD · 26.09.2026 · фаза 3 (окончательно) · three 0.186.0 (`three/webgpu`, `three/tsl`) · Chromium 153 headless, Intel Iris Xe (Mesa),
Vulkan 1.4 · стенд — `99-raw/experiments/CD/tsl/` (`common.js`, `tsl.js`, `gl.js`, `tsl_run.py`) · метки — `README.md`. Замер — в тишине
(тяжёлый замок очереди), пропускная «окно 2,5 с / число кадров», 3 повтора, новый процесс браузера на каждый прогон (холодный кэш шейдеров).

## Выжимка для агента

1. **Для лендинга «Звена» WebGPU не нужен**: всё, что делает сцена кода (студия, IK, мир, AO, пост, лучи, деталь), есть на `WebGLRenderer`, и там
   оно дешевле по весу. Вход в WebGPU для **одного** процедурного материала — **+107 КБ br** (стенд TSL 260,5 против GLSL 153,1 КБ br) — это
   треть бюджета JS 3D L2 десктопа (≤ 350) и почти половина телефонного (≤ 250). `[проверено]` TSL идёт и на `WebGLRenderer`
   через `WebGLNodesHandler` (r184+), но вход по весу тот же: на минимальной сцене 201,8 против 108,9 КБ br у GLSL-патча (+93) —
   это путь миграции одним кодом, а не экономия (→ §2). `[исходник]` `[проверено]`
2. **Переходить, когда нужно то, чего на WebGL нет**: compute (частицы/симуляции от сотен тысяч элементов, поля), настоящий объём с тенью
   (`GodraysNode` — raymarch по карте теней), `SSGINode`/`SSRNode`/`TRAANode`, VXGI (`examples/jsm/lighting/vxgi`), сплаты с сортировкой на GPU.
   Всё это в r186 — **только** `WebGPURenderer` + TSL. `[документация: исходники three 0.186.0 examples/jsm/tsl/display, lighting/vxgi]`
3. **Цена кадра на крошечной сцене — не довод**: точёная крышка с TSL-шумом шероховатости (одна Physical-модель, 960×600, DPR 1,5):
   GLSL на WebGL — 0,71 мс, TSL на WebGPU — 1,13 мс, тот же TSL на откате WebGL2 — 1,04 мс; при такой нагрузке кадр — это накладные
   расходы бэкенда, не шейдер. Первый кадр: WebGPU 92–94 мс (холодный 210), GLSL 196–216, **откат 307–323 мс (×1,5 к GLSL)**. `[проверено]`
4. **Откат обязателен и дорог**: `WebGPURenderer` без адаптера сам уходит на WebGL2-бэкенд (`forceWebGL` — то же принудительно); на этом
   бэкенде первый кадр ×1,5 (CD/18) … ×1,7 и TBT ×1,6 (F1/05) к обычному `WebGLRenderer`, compute эмулируется, атомиков нет. Страница с WebGPU
   платит вес всем, а выгоду получают только браузеры с адаптером. `[проверено]`
5. **Headless-проверка WebGPU**: настоящий адаптер Chromium 153 на Linux даёт только с явным ANGLE-бэкендом —
   `--use-angle=vulkan --enable-features=Vulkan` (на Intel Gen12+ даже без `--enable-unsafe-webgpu`) или `--use-angle=gl` вместе с
   `--enable-unsafe-webgpu --enable-features=Vulkan` (флаги `site_probe.py` по умолчанию) — и **только в безопасном контексте**
   (http://127.0.0.1 — да, `about:blank` — нет `navigator.gpu`); адаптер Intel gen-12lp не запасной (BC, ETC2, ASTC, timestamp-query).
   Без явного ANGLE Playwright ставит `--use-angle=swiftshader-webgl`, и `--enable-unsafe-webgpu` отдаёт программный SwiftShader
   (`isFallbackAdapter: true`): `backend` = webgpu, а кадр чёрный — ложный WebGPU; тот же обман даёт `site_probe.py --gpu swiftshader`
   без `--no-webgpu`. В отчёте замера — поля `backend` (`webgpu` / `webgl2-fallback`) и `isFallbackAdapter`, иначе «замер WebGPU»
   окажется откатом или SwiftShader (→ §4). `[проверено]`
6. **Ворота слепы к WebGPU**: `motion_check` перехватывает только вызовы WebGL — «0 кадров в покое» на WebGPU будет ложно чистым; мерить
   `site_probe.py` (перехват `GPURenderPassEncoder.draw*`) и своим счётчиком кадров. `[документация: дайджест 04 §B; проверено на WebGL: CD/16]`
7. **Перенос на `WebGPURenderer` ломает GLSL-мир**: troika даёт белые квадраты (замена — `three-msdf-text-utils` 1.5.0 с
   `MSDFTextNodeMaterial`), drei `MeshPortalMaterial`, `onBeforeCompile` и `ShaderMaterial` не работают, pmndrs-пост — тоже
   (замена — `RenderPipeline`), `toneMapped: false` игнорируется — тон стал проходом цепочки; WebGPU есть у iOS 26+ и Android 12+,
   но нет у Firefox на Android и Linux → откат на WebGL2 обязателен (→ §2). `[документация]` `[исходник]`
8. **Апскейл — только на `WebGPURenderer`**: рендер в ½ и `taau()` или `fsr1()` с `sharpen()` (RCAS) — пикселей в 4 раза меньше за
   +1,0…2,5 КБ br; FSR1 нужен, только если упор во фрагментный шейдер (→ §2). `[исходник]` `[проверено: замер веса]`

## 1. Опыт CD/18: тот же материал на трёх путях (тишина 26.09 00:55–00:56, load 1,9–2,2)

Сцена: белый корпус (Physical, лак) + точёная крышка сустава J2 (профиль `capX`, 192 сегмента), окружение `RoomEnvironment` → PMREM, ключ,
Neutral 1,22. Материал крышки — процедурная шлифовка: шероховатость = 0,2 + 0,12 · кольца (шум по радиусу ×900) + 0,06 · штрихи (шум по углу ×60),
0 байт карт. TSL: `MeshPhysicalNodeMaterial.roughnessNode` = `mx_noise_float(…)`; GLSL: тот же градиентный шум в `onBeforeCompile`
(`#include <roughnessmap_fragment>`). Кадры `out/cd3/tsl/{gl,webgpu,fallback}.png`, лист `out/cd3/tsl_sheet.jpg`, числа `out/cd3/ao_tsl_summary.json`.

| Путь | `backend` | Вес бандла, КБ br | Первый кадр, мс | Инициализация, мс | Кадр, мс (пропускная) |
|---|---|---|---|---|---|
| GLSL `onBeforeCompile`, `WebGLRenderer` | webgl2 | **153,1** | 196–216 | 151–190 | **0,71** |
| TSL, `WebGPURenderer` | **webgpu** | 260,5 (+107,4) | 92–94 (холодный 210) | 95–102 | 1,13 |
| TSL, `WebGPURenderer({ forceWebGL: true })` | webgl2-fallback | 260,5 | 307–323 | 200–207 | 1,04 |

Вид всех трёх одинаков на глаз (кольца точения тонкие; разница — только цвет очистки фона у WebGPU). Вывод: TSL — удобный язык одного исходника
для двух бэкендов, но ради одной процедурной фактуры он не окупается: GLSL-патч даёт то же за 0 КБ сверх `WebGLRenderer`. `[проверено]`

## 2. Когда переходить (дерево)

| Задача | WebGL (`WebGLRenderer`) | WebGPU (`WebGPURenderer` + TSL) |
|---|---|---|
| продуктовая сцена со светом, миром, постом, IK (как «Звено») | **да**: всё есть, вес меньше, ворота видят | нет выгоды |
| процедурная фактура (шум, анизотропия) | `onBeforeCompile` / `ShaderMaterial` | удобнее (узлы), но +107 КБ br |
| один код узлов для WebGL сейчас и WebGPU потом | `WebGLRenderer` + `WebGLNodesHandler` (r184+): без MRT, transmission, VSM, storage-текстур; 201,8 КБ br против 108,9 у GLSL-патча | тот же код узлов на `WebGPURenderer` |
| частицы до 65 тыс. (след, поток, пыль в луче) | вершинный шейдер / `GPUComputationRenderer` 256² | не нужно |
| частицы/симуляции от 200 тыс., поля, ткань, жидкость | тяжело (ping-pong текстур) | **да** (`compute`, `instancedArray`, атомики) |
| объём с тенью от источника, SSGI, SSR, TRAA, VXGI | нет готового (pmndrs GodRays — маска + радиальная свёртка) | **да** (`GodraysNode`, `SSGINode`, `SSRNode`, `TRAANode`, vxgi) |
| сплаты | Spark (782,2 КБ br с three) | нативная сортировка на GPU: `GaussianSplat` r186 — только `WebGPURenderer` (216,6 КБ br) |

Правило: WebGPU — когда без него **нет эффекта**, а не когда «так современнее»; и только с замером отката на той же странице.

Покрытие и ловушки переноса; снимок поддержки и доли — `../01-web-3d-landscape/06-js-stack.md` §3.1:

- **Где WebGPU есть**: Chrome и Edge на Windows, macOS и ChromeOS (с 113), Chrome на Android 12+ (с 121), на Linux — Intel
  Gen12+ (с 144); Safari 26 на macOS 26, iOS, iPadOS и visionOS; Firefox на Windows (с 141) и на macOS с Apple Silicon. Нет —
  у Firefox на Android и Linux и на Intel Mac → откат на WebGL2 обязателен. `[документация: MDN BCD, gpuweb]`
- **Что не переносится**: troika (`troika-three-text`) — белые квадраты, замена — `three-msdf-text-utils` 1.5.0
  (`MSDFTextNodeMaterial`); drei `MeshPortalMaterial` — это GLSL `shaderMaterial`; `onBeforeCompile` и `ShaderMaterial` —
  только узлы TSL; pmndrs `postprocessing` — `RenderPipeline`; `toneMapped: false` игнорируется — тон стал проходом цепочки;
  `GaussianSplat` r186 — только `WebGPURenderer`, в том числе с `forceWebGL`. `[документация]` `[исходник]`
- **Апскейл**: рендер в ½ и `taau()` (TAA с апскейлом, r184) или `fsr1()` (FSR 1, r184) с `sharpen()` (RCAS); в примерах r186
  `webgpu_upscaling_taau` и `webgpu_upscaling_fsr1` масштаб 0,5 по умолчанию (0,25–1), резкость 0,2 из 0–2; пикселей в 4 раза
  меньше за +1,0…2,5 КБ br; FSR1 нужен, только если упор во фрагментный шейдер; TAAU требует выключенного MSAA, TRAA с MSAA
  несовместим. `[исходник]` `[проверено: замер веса]`
- **Режим совместимости** (старый Android, OpenGL ES 3.1): `WebGPUBackend` просит адаптер `featureLevel: 'compatibility'` и в
  этом режиме ставит `_samples = 0` — `antialias: true` молча не действует, сглаживание — узлом `fxaa()` или `smaa()`.
  `[исходник]`

## 3. Что переписывать в сцене «Звена», если переходить (оценка по коду `_shared/code3d`)

| Что сейчас (WebGL) | Где | Во что на WebGPU | Оценка |
|---|---|---|---|
| туман по высоте и зеркальная альфа — патч `onBeforeCompile` во все материалы (`withHF`) | `world.js` | общий узел `fogNode`/свой узел в `colorNode` каждого `…NodeMaterial` | 2–3 ч, риск кэша программ |
| зеркало пола (свой Reflector: косая плоскость, ½ + размытие ¼) | `world.js` | `ReflectorNode` (TSL) + размытие узлом | 2 ч |
| скан-срез со светящейся кромкой (`scanify`, `clippingPlanes` + патч) | `modules-code.js` | узел в `colorNode`/`emissiveNode`, `clippingGroup` | 1–2 ч |
| LED-полоса кольца (атрибут `band`, патч) | `modules-code.js` | `emissiveNode` = маска по `attribute('band')` | 0,5 ч |
| фон-шейдер (горизонт, ореол), размытие зеркала | `world.js` (`ShaderMaterial`) | `QuadMesh` + узлы | 1 ч |
| пост pmndrs (N8AO, bloom, Neutral, LUT, зерно, FXAA, лучи) | `post.js` | `RenderPipeline` (в r183 переименован из `PostProcessing`) + `ao()`/`gtao`, `bloom()`, `lut3D()`, `fxaa()`, `GodraysNode` | 3–4 ч; pmndrs на WebGPU не работает |
| студии PMREM из панелей | `studio.js` | `PMREMGenerator` есть и там | 0 |
| загрузка KTX2 (крюк v2) | `ktx2.js` | `detectSupport` сам понимает `WebGPURenderer` (`hasFeature('texture-compression-bc')`) | 0 |

Итого ≈ 10–13 агент-часов и новый прогон всех ворот — ради эффекта, которого на странице A нет. `[мнение, по коду]`

## 4. Частые ошибки

| Ошибка | Последствие | Правка |
|---|---|---|
| «замер WebGPU» без поля `backend` | измерили откат WebGL2 и записали как WebGPU | писать `renderer.backend.isWebGPUBackend` в отчёт |
| headless без явного ANGLE или на `about:blank` | `navigator.gpu` нет или адаптер — SwiftShader: молчаливый откат или ложный WebGPU | `--use-angle=vulkan --enable-features=Vulkan` (или `--use-angle=gl` с `--enable-unsafe-webgpu --enable-features=Vulkan`), страница с http://127.0.0.1 |
| WebGPU на SwiftShader засчитан как WebGPU | `backend` = webgpu, кадр чёрный или белый, чтение буфера падает | писать `adapter.info.isFallbackAdapter`; без GPU проверять откат WebGL2, а compute — чтением буфера; `site_probe.py --gpu swiftshader` — только с `--no-webgpu` |
| снимок после одного кадра и compute | в программных режимах canvas пустой | рендерить циклом до снимка |
| `antialias: true` в режиме совместимости | MSAA молча 0 — лесенки на старом Android | узел `fxaa()` или `smaa()` в `RenderPipeline` |
| troika, `MeshPortalMaterial`, `onBeforeCompile` после перехода на WebGPU | белые квадраты, пустой портал, пропавший патч шейдера | MSDF-текст (`three-msdf-text-utils`), узлы TSL |
| `toneMapped: false` на WebGPU | игнорируется: тон — проход цепочки | учесть в `RenderPipeline`: тон применяется проходом ко всему кадру |
| WebGPU ради одной фактуры | +107 КБ br всем | GLSL-патч на `WebGLRenderer` |
| ворота покоя `motion_check` на WebGPU | ложное «0 кадров» | `site_probe.py` с перехватом WebGPU |
| pmndrs/n8ao с `WebGPURenderer` | не работает (только WebGL) | узлы `three/tsl` (`RenderPipeline`) |
| `PostProcessing` в новом коде | предупреждение устаревания (r183) | `RenderPipeline` |

## 5. Чек-лист

- [ ] есть эффект, которого нет на WebGL (compute, объём с тенью, SSGI/SSR/TRAA, VXGI) — иначе остаться на WebGL;
- [ ] вес входа посчитан сборкой (esbuild) и уложен в бюджет L2; телефон — отдельным чанком или без WebGPU;
- [ ] откат замерен на той же странице: первый кадр, TBT, кадр; `backend` в каждом отчёте;
- [ ] покой проверен инструментом, который видит WebGPU;
- [ ] в отчёте — `backend` и `isFallbackAdapter`; снимок — после цикла рендера;
- [ ] режим совместимости — без MSAA: проверен узел сглаживания (`fxaa()` или `smaa()`);
- [ ] текст, порталы и свои шейдеры переведены на узлы (troika → MSDF); апскейл — только на `WebGPURenderer`.

## Открытые вопросы и противоречия

- PR #34334 (открыт) выносит откат WebGL2 в чанк по требованию — сборка WebGPU легче на 24,3 КБ gzip; войдёт ли он в r187 и
  сколько тогда стоит вход в WebGPU — `[не проверено]`.
- Без видеокарты WebGPU-кадр в headless не проверяется: стенд без GPU видит только откат и чтение буферов.
- На реальных телефонах WebGPU, откат и апскейл не мерились.

## Источники

- Стенд: `99-raw/experiments/CD/tsl/` (сборка `build.sh`, вес `weights.txt`), замер `out/cd3/tsl/tsl.json`; проба адаптера — `NOTES.md` CD 00:36 (CD/24).
- three.js r186: `src/renderers/common/PostProcessing.js` (устарел с r183 → `RenderPipeline`), `examples/jsm/tsl/display/{GodraysNode,SSGINode,SSRNode,TRAANode}.js`,
  `examples/jsm/lighting/vxgi/`, `examples/jsm/loaders/KTX2Loader.js` (`detectSupport` для WebGPU); [TSL](https://threejs.org/docs/pages/TSL.html).
- База: `99-raw/experiments/F1/05-webgl-webgpu/README.md` (откат ×1,7 первого кадра, TBT ×1,6), `09-web-runtime/`; `06-compute-particles-sim.md`.
- three.js: PR #32851 (`WebGLNodesHandler`, r184) — https://github.com/mrdoob/three.js/pull/32851 ; PR #34334 (откат по
  требованию) — https://github.com/mrdoob/three.js/pull/34334 ; TAAU — https://github.com/mrdoob/three.js/pull/33368 ; FSR1 —
  https://github.com/mrdoob/three.js/pull/33339 ; примеры r186 `webgpu_upscaling_taau`, `webgpu_upscaling_fsr1` —
  https://github.com/mrdoob/three.js/tree/r186/examples ; исходники 0.186.1: `WebGPUBackend`, `WebGLNodesHandler`, `TRAANode`.
- Headless-пробы WebGPU и WebGL на Linux, Intel Iris Xe: 6 серий, 38 прогонов (Chrome 153, Playwright 1.63) —
  `../01-web-3d-landscape/06-js-stack.md` §3.4 `[проверено]`; Chrome, «Supercharge Web AI model testing» —
  https://developer.chrome.com/blog/supercharge-web-ai-testing .
- Покрытие WebGPU: MDN BCD, раздел api, файл GPU — https://github.com/mdn/browser-compat-data ; web.dev, «WebGPU is now supported in
  major browsers» — https://web.dev/blog/webgpu-supported-major-browsers ; gpuweb Implementation Status —
  https://github.com/gpuweb/gpuweb/wiki/Implementation-Status .
