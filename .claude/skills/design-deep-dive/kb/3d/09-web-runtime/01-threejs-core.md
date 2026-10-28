# Ядро three.js r186 для страницы с моделью из Blender: импорт, рендерер, загрузка, окружение, цвет, тени, память

Волна 2 · агент F1 · 23.09.2026 · опора: исходник пакета three@0.186.0 и 5 экспериментов `99-raw/experiments/F1/01–05`, волна 1
(A `01-web-3d-landscape/02–03`, E `08-export-gltf/01–04`), D2/01 (цвет), выписки помощников: 12 докладов
(`99-raw/notes/wave2/F1-sub-core.md`), AR (`F1-sub-AR.md`), соседние базы (`F1-sub-neighbors.md`); источников по разделам ≈ 15 ·
версии: three 0.186.0, Chromium (Playwright, headless, ANGLE GL/Vulkan, Intel Iris Xe), esbuild 0.28.2, gltf-transform 4.5.0,
toktx 4.4.2, Blender 5.2.2 · JS-блоки файла исполнены прогоном `99-raw/experiments/F1/06-doc-snippets`. Эффекты, R3F, прокрутка —
у F2 (`02–04` этой папки); производительность и запасные варианты — `05`, поставки не-GLB, AR, KTX2, WebGPU — `06`.

## Выжимка для агента

1. **Стек по умолчанию**: `WebGLRenderer` + `GLTFLoader` (Meshopt; KTX2/Draco — по `extensionsUsed` файла) + бандлер + свой домен → §1–3. [проверено]
2. **Бандлер (esbuild/Vite) со своего домена**: JS 174 КБ br, three готов через 2,0 с на эмуляции Pixel 7, первый кадр модели 3,7 с; import map с jsDelivr — 443 КБ, 3,8 и 4,9 с → §1.1. [проверено]
3. **jsDelivr `three.module.min.js` импортирует неминифицированный `./three.core.js`** (204 КБ br): «min с CDN» без настройки экономит 10 %; ключ-URL в import map, переназначающий ядро на `three.core.min.js`, даёт 243 КБ → §1.2. [проверено]
4. В пакете r186 нет `*.min.js`, CJS устарел; адреса декодеров — `examples/jsm/libs/draco/gltf/` и `…/libs/basis/` (старый `examples/js/…` — 404) → §1, §3.3. [проверено: F1/01; E 03 п. 17]
5. **GLB — одним запросом, декодеры — только нужные** (по `extensionsUsed`): Meshopt 7 КБ br, Draco 58, KTX2 ≈ 239 (транскодер 212 + zstddec 15 + ktx-parse 5 + загрузчик 7,5) → §3.2. [проверено]
6. **Декодеры — со своего домена**: транскодер KTX2 с jsDelivr +0,8–1,2 с к первому кадру на медленном 4G (чужой домен, gzip вместо br) → §3.3. [проверено]
7. **`compileAsync` не снимает долгие задачи** (внутри синхронный `compile()` + опрос `isReady()` раз в 10 мс), но первый `render()` — 14 мс вместо 541 мс: звать перед первым кадром ради кадра перехода постер → canvas → §3.4. [проверено]
8. Умолчания `WebGLRenderer`: `toneMapping = NoToneMapping`, `toneMappingExposure = 1`, `outputColorSpace = SRGBColorSpace` → тонмаппинг включать явно → §5. [проверено]
9. **Пара по умолчанию (одинаково с D2)**: Blender «Khronos PBR Neutral», look None, exposure E ↔ `renderer.toneMapping = THREE.NeutralToneMapping`, `toneMappingExposure = 2^E` (E = 0 → 1), `outputColorSpace = SRGBColorSpace` → §5.1. [проверено: D2/01 — ΔE2000 Blender↔three 0,23–0,36 (белая печь), макс. 1,08; F1/01 — одна формула]
10. **AgX three ≠ AgX Blender**: приближение Filament, look выключен, степень 2,2 вместо 2,4 → three светлее на 3,4–3,7 L*; если AgX обязателен — подменить степень на 2,4 до первой компиляции (D2) → §5.2. [проверено]
11. **Unlit тоже тонмаппится** (`MeshBasicMaterial` из `KHR_materials_unlit`): для точного hex логотипа — `material.toneMapped = false` → §5.3. [проверено]
12. **Металлу нужно окружение**: `RoomEnvironment` через PMREM (0 КБ) или HDRI 1k (0,4–0,6 МБ) через `HDRLoader`; без него металл чёрный → §4. [проверено]
13. `scene.environment = hdrTexture` (mapping `EquirectangularReflectionMapping`) — рендерер сам строит и кэширует PMREM; руками `PMREMGenerator` — только для `fromScene` → §4.1. [проверено]
14. `new RoomEnvironment()` — без аргументов; `ColorEnvironment(color)` — однотонный IBL; яркость и поворот — `scene.environmentIntensity`, `environmentRotation` → §4.1. [проверено]
15. **`WebGPURenderer` тонмаппит сплошной `scene.background`, `WebGLRenderer` — нет**: фон canvas расходится с CSS-фоном (#eceef2 → 228,230,234); лечение — прозрачный canvas → §2.3. [проверено]
16. **WebGPU — не по умолчанию для лендинга**: первый кадр WebGPU 922 мс против 1353 мс у WebGL (не хуже), но откат `WebGPURenderer` на WebGL2 — 2299 мс и TBT ×1,6; это получат ≈ 16 % посетителей без WebGPU → §2.2. [проверено]
17. `await renderer.init()` у `WebGPURenderer` — до `render()` вне `setAnimationLoop` и до `KTX2Loader.detectSupport(renderer)` → §2.1. [документация: Migration Guide r181; проверено: A/08, F1/05]
18. Не смешивать `three` и `three/webgpu` в одной странице — два экземпляра three, «Multiple instances» → §2.1. [документация]
19. **`PCFSoftShadowMap` в r186 удалён в обоих рендерерах** (warn и `PCFShadowMap`) — поправка к A `03 §2.3` → §7. [проверено]
20. **Тени shadow map** — лишний проход глубины на источник (точечный — 6); hero: запечь свет и тень в Blender или плоскость с запечённой тенью; реальные тени — только движущимся → §7. [практика: V:Inqt1fZ3QTI 23:15; E 04 §6]
21. **Transmission удваивает вызовы и треугольники**; `transmissionResolutionScale` по умолчанию 1 → на телефоне 0,5 → §6.3. [проверено: E/24 (×2), F1/01 (умолчание); эффект 0,5 — 1,72 → 1,39 мс без видимой потери, F2/05]
22. **lightMap из Blender**: `channel = 1`, `flipY = false`, `lightMapIntensity = Math.PI`; `aoMap` гасит только непрямой свет → §6.2. [проверено]
23. Постобработка: WebGL — pmndrs `postprocessing` 6.39.5 (peer three < 0.187) или `EffectComposer` + `OutputPass`; WebGPU — `RenderPipeline`; без `OutputPass` тонмаппинг и sRGB в цепочке теряются → §8. [документация]
24. **Освобождать всё**: геометрии, материалы, текстуры материалов (в т. ч. `ImageBitmap`), render targets, PMREM; `renderer.info.memory` → 0 → §9. [проверено]
25. **Resize**: `ResizeObserver` на контейнере, `setSize(w, h, false)`, `setPixelRatio(Math.min(devicePixelRatio, 1.5))` на телефоне; DPR 2,625 с MSAA — 89 МБ одних буферов кадра → §10. [проверено: F1/04 (расчёт), A/04]
26. **Узлы после постобработки**: имена санитизируются (`. [ ] : /` удаляются, пробел → `_`), квантование добавляет обёртку — искать по `userData.name` и `traverse(o => o.isMesh)` → §11. [проверено]
27. `renderer.info.render.calls` у `WebGPURenderer` накопительный (за кадр — `frameCalls`) → §2.3. [проверено]
28. **Первый кадр модели метить самому** (после первого `render()` модели): первый draw call страницы — это PMREM окружения (≈ 1,9 с в F1/02), а не модель → §3.5. [проверено]

## 1. Модули и импорт

### 1.1. Бандлер против import map (замер F1/02, Pixel 7: CPU ×4, 1,6 Мбит/с, 150 мс; 2 прогона)

| способ | JS передано | three загружен | 1-й кадр модели | когда |
|---|---|---|---|---|
| import map → jsDelivr `build/three.module.js` (+ неминиф. ядро) | 443 КБ | 3,8 с | 4,9 с | только прототип |
| import map → jsDelivr `three.module.min.js` без переназначения | 401 КБ | 3,7 с | 4,9 с | не использовать |
| import map → min + ключ-URL для ядра (§1.2) | 243 КБ | 3,4 с | 5,9 с (1 прогон) | страница без сборки, CDN допустим |
| **бандлер** (esbuild `--splitting`), свой домен, brotli | **174 КБ** | **2,0 с** | **3,7 с** | **продакшен** |

LCP во всех вариантах — постер 404–482 мс, CLS 0 [проверено]. Выигрыш бандлера — вес и
отсутствие чужого домена: DNS/TLS к CDN на медленной сети и gzip вместо br. Размеры частей (brotli q11, F1/01): `three.module.js`
102 КБ + `three.core.js` 204 КБ (неминиф.), `three.module.min.js` 74 + `three.core.min.js` 84 КБ (jsDelivr, Terser),
`three.webgpu.js` 316 КБ, `GLTFLoader.js` 21 КБ; бандл с `import('three')` целиком — ядро-чанк 153 КБ (весь namespace, tree-shaking
не работает на `import * as` при динамическом импорте) [проверено]. С именованными импортами и статической сборкой A/03
получал 109–160 КБ br [проверено].

```bash
# esbuild 0.28 — [проверено] бандл с чанками: import('three') → отдельный файл
npm i three@0.186.0 esbuild
npx esbuild hero.js --bundle --format=esm --splitting --minify --outdir=dist --legal-comments=none
# хостинг: brotli для .js/.wasm/.glb, хэш в именах чанков + Cache-Control: public, max-age=31536000, immutable
```

Vite делает то же (`import()` → чанк); `vite build` не проверялся здесь [не проверено]. Перед сборкой — `npm view three version`
и Migration Guide между версией знаний модели и r186 (таблица дрейфа — A `../01-web-3d-landscape/03-runtime-landscape.md` §2.3).

### 1.2. Прототип без сборки: import map с переназначением ядра

jsDelivr минифицирует файлы на лету (`*.min.js` для любого файла пакета), но минифицированный модуль сохраняет относительные импорты:
`three.module.min.js` содержит `from"./three.core.js"`, `three.webgpu.min.js` — тоже [проверено: F1/01 `jsdelivr_min.txt`].
Import map умеет переназначать разрешённые URL, не только «голые» имена:

```html
<!-- three r186 — [проверено] прототип: min-сборки jsDelivr + ядро тоже min -->
<script type="importmap">
{ "imports": {
  "three": "https://cdn.jsdelivr.net/npm/three@0.186.0/build/three.module.min.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.186.0/examples/jsm/",
  "https://cdn.jsdelivr.net/npm/three@0.186.0/build/three.core.js": "https://cdn.jsdelivr.net/npm/three@0.186.0/build/three.core.min.js"
} }
</script>
```

Проверка — в Network должны быть только `three.module.min.js` и `three.core.min.js` (3 из 3 прогонов) [проверено]. jsDelivr
пишет «Do NOT use SRI with dynamically generated files» — без атрибута `integrity`. Версию — всегда полную (`@0.186.0`), не `@latest`.
Модули addons (`GLTFLoader.js` и т. п.) импортируют `"three"` — все получат один экземпляр через import map.

## 2. WebGLRenderer и WebGPURenderer

### 2.1. Правила

- `WebGLRenderer` (`import * as THREE from 'three'`) — зрелый путь; вся экосистема (pmndrs `postprocessing`, большинство drei)
  работает только с ним [документация: A 03 §2.2].
- `WebGPURenderer` (`import * as THREE from 'three/webgpu'`) — бэкенды WebGPU и WebGL2 с автоматическим откатом; классические
  материалы из `GLTFLoader` он сам переводит в node-материалы (NodeLibrary: `MeshStandardMaterial → MeshStandardNodeMaterial`,
  `MeshPhysicalMaterial → MeshPhysicalNodeMaterial`, `MeshBasicMaterial → MeshBasicNodeMaterial`) — GLB рисуется без правок кода
  [проверено: F1/01 исходник, F1/05 — кадры WebGL/WebGPU/отката совпали]. `onBeforeCompile` и `ShaderMaterial` на нём не работают —
  своё — на TSL [документация: A 03 §2.2].
- `await renderer.init()` — до первого `render()` вне `setAnimationLoop` и до `KTX2Loader.detectSupport(renderer)` (r181: async-
  методы вроде `renderAsync` устарели) [документация: Migration Guide r181; проверено: A/08, F1/05].
- В одной странице — один «мир»: либо `three`, либо `three/webgpu` (+ `three/tsl`); import map для WebGPU-страницы переназначает
  и `"three"` → `three.webgpu.js`, иначе addons потянут второй экземпляр [проверено].
- В режиме совместимости WebGPU (compat mode, старые Android, Chrome 146+) three r186 выключает MSAA (`_samples = 0` в
  `WebGPUBackend.js`); не запрашивать функций и лимитов сверх умолчаний — лимиты разнятся по браузерам [V:3YP5Ck-7NZk 07:45, 40:25].

```js
// three r186 — [проверено] WebGPURenderer: init() до кадра, откат на WebGL2 сам
import * as THREE from 'three/webgpu';

export async function createWebGPURenderer(host, { maxDpr = 1.5 } = {}) {
  const renderer = new THREE.WebGPURenderer({ antialias: true, alpha: true });   // alpha: фон рисует CSS (§2.3)
  await renderer.init();                                    // r181+: обязательно до render() вне setAnimationLoop
  renderer.setPixelRatio(Math.min(devicePixelRatio, maxDpr));
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.domElement.setAttribute('aria-hidden', 'true');
  host.appendChild(renderer.domElement);
  const backend = renderer.backend.isWebGPUBackend ? 'webgpu' : 'webgl2';   // без WebGPU-адаптера — WebGL2, с warn в консоли
  return { renderer, backend };
}
```

### 2.2. Замер: одна сцена на трёх путях (F1/05, 6 прогонов, медианы)

| путь | 1-й кадр от создания рендерера | TBT до 1-го кадра | самая долгая задача | кадр подряд |
|---|---|---|---|---|
| `WebGLRenderer` | 1353 мс [943–1648] | 636 мс | 686 мс | 0,8 мс |
| `WebGPURenderer`, WebGPU | **922 мс** [637–1467] | 506 мс | 360 мс | 1,9 мс |
| `WebGPURenderer({ forceWebGL: true })` — откат | **2299 мс** [1769–3522] | **1015 мс** | 1044 мс | 2,4 мс |

Сцена `product.glb` (7,3 тыс. треуг., clearcoat), RoomEnvironment, Neutral, 800², Iris Xe, новый процесс браузера на прогон
[проверено]. Спор «готов ли WebGPU» (mrdoob 06.2024: «not ready for production» [V:7we9mqIOKyw
17:34]; HolyJS 03.2025: «больше проблем, чем пользы» [V:sqkSrTq1Kos 37:43]; Khronos 07.2026: во всех основных браузерах
[V:3YP5Ck-7NZk 08:48]) замер разрешает так: **WebGPU уже не медленнее на первом кадре, но худший случай аудитории — откат, а он
медленнее обычного `WebGLRenderer` в 1,7 раза**. Позиция базы (совпадает с W7 §4):

| брать `WebGPURenderer` | брать `WebGLRenderer` |
|---|---|
| compute-частицы и симуляции (10⁵+), сплаты three (`GaussianSplat` — только WebGPU), TSL-эффекты r184+ (OIT, новые SSAO/DOF) | hero-GLB, витрина, шейдерный фон, прокрутка, pmndrs-постобработка |
| есть время проверить оба бэкенда и откат на телефонном профиле | жёсткий бюджет JS (≤ 200 КБ br: `three.webgpu.js` один — 316) и первого кадра |

[проверено: F1/05; документация: A 03 §2.2; V: W7 §4]

### 2.3. Различия, которые видны на странице

- **Фон**: `WebGPURenderer` пропускает сплошной `scene.background` через тонмаппинг (#eceef2 → пиксель 228,230,234 = Neutral от
  236,238,242), `WebGLRenderer` — нет (236,238,242) [проверено]. Canvas поверх CSS-фона — `alpha: true` и без
  `scene.background`; или цвет фона только в CSS.
- **`renderer.info`**: у `WebGPURenderer` `render.calls` накапливается (333 после 150 кадров), за кадр — `render.frameCalls`; у
  `WebGLRenderer` `render.calls` — за последний кадр (`info.autoReset = true`) [проверено].
- **Устойчивый кадр** лёгкой сцены у WebGL ниже (0,8 против 1,9 мс подачи) — WebGPU окупается на CPU-bound сценах с тысячами
  объектов (render bundles, BundleGroup: 20 → 50 FPS в демо [V:sqkSrTq1Kos 13:52]) [проверено: F1/05; практика].

## 3. Загрузка GLB

### 3.1. Порядок (шаблон hero, `examples/hero-lazy/`)

Постер и H1 в HTML → `load` + видимость + простой → `import()` three → рендерер и окружение → GLB одним `fetch` → декодеры по
`extensionsUsed` → `parseAsync` → кадр по габариту → `compileAsync` → первый `render()` → класс `is-live` (кроссфейд на CSS) →
цикл только при видимости, открытой вкладке и без reduce. Условия запуска и цикл — `05-performance-a11y-fallbacks.md` §2–3; сам
паттерн и LCP — A `../01-web-3d-landscape/02-when-3d-budgets-loading.md` §4 [проверено].

### 3.2. Один запрос, нужные декодеры, прогресс

```js
// three r186 — [проверено] (логика — F1/02 hero.js): GLB одним fetch, декодеры по extensionsUsed
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export function glbExtensions(buf) {                     // JSON-чанк GLB: заголовок 12 байт + заголовок чанка 8 байт
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x46546C67) throw new Error('не GLB');          // 'glTF'
  const json = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, dv.getUint32(12, true))));
  return new Set([...(json.extensionsUsed || []), ...(json.extensionsRequired || [])]);
}

export async function loadGLB(url, renderer, { decoders = '/decoders/', onProgress } = {}) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const total = +res.headers.get('content-length') || 0;    // при Content-Encoding: br это сжатый размер — прогресс ограничивать 1
  const reader = res.body.getReader(); const parts = []; let got = 0;
  for (;;) { const { done, value } = await reader.read(); if (done) break; parts.push(value); got += value.length; onProgress?.(got, total); }
  const buf = await new Blob(parts).arrayBuffer();
  const ext = glbExtensions(buf);
  const loader = new GLTFLoader();
  if (ext.has('EXT_meshopt_compression') || ext.has('KHR_meshopt_compression')) {
    const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js');
    loader.setMeshoptDecoder(MeshoptDecoder);
  }
  let draco = null, ktx2 = null;
  if (ext.has('KHR_draco_mesh_compression')) {
    const { DRACOLoader } = await import('three/addons/loaders/DRACOLoader.js');
    loader.setDRACOLoader(draco = new DRACOLoader().setDecoderPath(decoders + 'draco/gltf/'));
  }
  if (ext.has('KHR_texture_basisu')) {
    const { KTX2Loader } = await import('three/addons/loaders/KTX2Loader.js');
    loader.setKTX2Loader(ktx2 = new KTX2Loader().setTranscoderPath(decoders + 'basis/').detectSupport(renderer));
  }
  const gltf = await loader.parseAsync(buf, url.replace(/[^/]*$/, ''));
  draco?.dispose(); ktx2?.dispose();                        // воркеры декодеров больше не нужны (одна модель на странице)
  return { gltf, extensions: ext, bytes: buf.byteLength };
}
```

- Без нужного декодера `GLTFLoader` бросает исключение («No DRACOLoader instance provided» и т. п.) [документация: E 01 §7.1].
- `content-length` при сжатии на лету отсутствует или равен сжатому размеру, а поток отдаёт распакованные байты — прогресс
  больше 100 %; надёжнее известный размер из манифеста или неопределённый индикатор [практика]. Когда показывать индикатор (200–300 мс
  задержки, минимум 300–500 мс показа, определённый — с 5 с) — `../../ux/06-feedback-states-motion/02-system-status-and-waiting.md` §2.2–2.5.
- Для нескольких моделей держать один `KTX2Loader`/`DRACOLoader` на страницу и `dispose()` при уходе: каждый экземпляр поднимает
  свои воркеры (`DRACOLoader.workerLimit = 4` по умолчанию) [документация: E 03 §2.2].

### 3.3. Декодеры: свой домен против CDN (F1/02)

| что | br, КБ (F1/01) | CDN jsDelivr | свой домен |
|---|---|---|---|
| Meshopt (`libs/meshopt_decoder.module.js`) | 7 | — | в бандле |
| Draco (`libs/draco/gltf/draco_decoder.wasm` + `draco_wasm_wrapper.js`) | 48 + 10 | холодная загрузка 0,28–0,45 с (E/17) | копировать папку `draco/gltf/` |
| KTX2 (`libs/basis/basis_transcoder.wasm` + `.js`, `KTX2Loader`, `zstddec`, `ktx-parse`) | 199 + 13 + 7,5 + 15 + 5 | первый кадр 8,7 с; wasm отдан gzip (240 КБ) | **7,5–7,9 с**; wasm br 199 КБ |

[проверено: F1/01, F1/02; E/17–18]. Копии декодеров — из `node_modules/three/examples/jsm/libs/` той же версии, что three
(транскодер и загрузчик меняются вместе). Сервер: `application/wasm` для `.wasm` (иначе нет потоковой компиляции), brotli, вечный кэш
с версией в пути (`/decoders/0.186.0/basis/`).

### 3.4. `compileAsync`: что он делает на самом деле

Исходник r186: `compileAsync(scene, camera)` вызывает синхронный `compile()` (сборка GLSL, `compileShader`/`linkProgram` для всех
материалов сцены с учётом окружения и света), затем раз в 10 мс опрашивает `program.isReady()` через `KHR_parallel_shader_compile`
[проверено]. Замер F1/02 (бандл, эмуляция телефона): с ним — компиляция 300 мс, первый `render()` 14 мс; без него — первый
`render()` 541 мс; TBT 867 против 854 мс — в пределах шума [проверено]. Вывод: гипотеза «`compileAsync` снимает долгие задачи»
(A) **не подтверждена**; он нужен, чтобы тяжёлый кадр не пришёлся на кроссфейд постер → canvas и на первую секунду анимации. Для
сцены с transmission первый кадр без прогрева — 387–480 мс только на шейдер `MeshPhysicalMaterial` [проверено].
Вызывать после того, как в сцене есть окружение и все материалы: `scene.environment`, добавленный позже, меняет программы.

### 3.5. Метка первого кадра

Первый draw call страницы — рендер `RoomEnvironment` в PMREM (≈ 1,9 с на эмуляции Pixel 7), а модель рисуется на 1,8–6 с позже;
зонд `site_probe.py` (`first_draw_ms`) ловит первый. Страница должна сама отмечать первый кадр модели (`performance.mark('hero-first-frame')`
или `window.__t.firstFrame`) — это метрика ворот качества в `05` §6 [проверено].

## 4. Окружение и свет

### 4.1. Окружение (IBL)

| вариант | вес | когда | код |
|---|---|---|---|
| `RoomEnvironment` → `PMREMGenerator.fromScene(env, 0.04)` | 0 КБ (1,4 КБ br модуль) | нейтральная студия по умолчанию, продукт | §4.2 |
| `ColorEnvironment(color)` → `fromScene` | 0 КБ | ровный «ambient» без бликов, стилизация | как RoomEnvironment |
| HDRI 1k `.hdr` → `HDRLoader`, `mapping = EquirectangularReflectionMapping`, `scene.environment = tex` | 0,4–1,6 МБ (Poly Haven 1k — 1,6 МБ; на сайтах 378–425 КБ) | фирменный свет, металл и стекло с «живыми» отражениями | §4.2 |
| тот же HDRI, свой рендер студии из Blender (панорама, EXR → HDR) | 0,4–0,6 МБ | свет «как в Blender-рендере» | `../06-materials-lighting-render/` (D2) |

- `PMREMGenerator.fromScene(scene, sigma = 0, near = 0.1, far = 100, { size = 256, position })`: `sigma` — размытие в радианах (0,04 —
  как у A/07); `RoomEnvironment()` конструктор без аргументов [проверено].
- Эквиректангулярную текстуру PMREM-ит сам рендерер при первом использовании и кэширует (`getPMREM` в `WebGLRenderer`); свой
  `PMREMGenerator.fromEquirectangular` — только чтобы прогреть заранее [проверено]. Идеальный вход — 1k (1024×512): под
  выход PMREM 256² [документация: JSDoc r186].
- Яркость и поворот окружения: `scene.environmentIntensity` (1), `scene.environmentRotation` (Euler); фон отдельно —
  `backgroundIntensity`, `backgroundBlurriness`, `backgroundRotation` [проверено].
- Металл (metallic 1) без окружения — чёрный с одним бликом; пластик — нормальный [проверено]. Окружение нужно в любой сцене
  с металлом, даже если свет запечён.
- `HDRLoader` (r180) вместо `RGBELoader` (наследник с `console.warn`, `@deprecated r180`) [проверено].

### 4.2. Код: рендерер, окружение, пара тонмаппинга

```js
// three r186 — [проверено] рендерер под рендер Blender «Khronos PBR Neutral», окружение, кадр по габариту
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';

export function createRenderer(host, { maxDpr = 1.5, alpha = true } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, maxDpr));
  renderer.toneMapping = THREE.NeutralToneMapping;           // пара к Blender «Khronos PBR Neutral», look None, exposure 0
  renderer.toneMappingExposure = 1;                           // outputColorSpace = SRGBColorSpace — умолчание, не трогать
  renderer.domElement.setAttribute('aria-hidden', 'true');    // декоративный canvas (интерактивный — 05 §5)
  host.appendChild(renderer.domElement);
  return renderer;
}

export async function setEnvironment(renderer, scene, { hdr = null, intensity = 1 } = {}) {
  if (hdr) {                                                  // HDRI 1k: PMREM рендерер построит сам и закэширует
    const tex = await new HDRLoader().loadAsync(hdr);
    tex.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = tex;
  } else {                                                    // 0 КБ: нейтральная студия
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose();                                          // результат живёт, служебные цели генератора — нет
  }
  scene.environmentIntensity = intensity;
  return scene.environment;
}

export function frameObject(camera, object, { margin = 1.05, dir = [0.55, 0.3, 0.78] } = {}) {
  const s = new THREE.Box3().setFromObject(object).getBoundingSphere(new THREE.Sphere());
  const v = THREE.MathUtils.degToRad(camera.fov);
  const h = 2 * Math.atan(Math.tan(v / 2) * camera.aspect);   // горизонтальный FOV: на узком экране он меньше вертикального
  const d = s.radius / Math.sin(Math.min(v, h) / 2) * margin;
  camera.position.copy(s.center).add(new THREE.Vector3(...dir).normalize().multiplyScalar(d));
  camera.near = d / 50; camera.far = d * 10; camera.updateProjectionMatrix();
  camera.lookAt(s.center);
  return s;
}
```

`frameObject` решает «на телефоне модель обрезана»: вертикальный FOV фиксирован, и в портретном кадре горизонталь уже — камеру надо
отодвигать по меньшему углу (так же рассуждает Bruno Simon о портретном экране [V:Uc3Ujdh8Ba4 04:16]) [проверено].

### 4.3. Лампы

- Свет из Blender по умолчанию не экспортируется (правильно для сайтов); если экспортировать — только `COMPAT` (±2 %), умолчание
  `SPEC` даёт ×683 и белый кадр; Area и мир не экспортируются [проверено]. Интенсивности three — физические (кандела, люкс),
  `physicallyCorrectLights`/`useLegacyLights` удалены [документация: A 03 §2.3].
- Для hero обычно хватает окружения; ключевой `DirectionalLight` добавлять ради тени или акцентного блика. ≤ 4 источников на сцену,
  без area на телефоне [V:Inqt1fZ3QTI 16:05]. Запечённый свет и lightMap + окружение/лампы — свет посчитается дважды [практика: E 02 §6.2].

## 5. Цвет: тонмаппинг и цветовое пространство под рендер Blender

### 5.1. Пары «вид Blender ↔ тонмаппинг three»

| Blender 5.2.2 (Color Management → View) | three r186 | расхождение рендеров | когда |
|---|---|---|---|
| **Khronos PBR Neutral**, look None, exposure E | **`NeutralToneMapping`**, `toneMappingExposure = 2^E` | **0,23–0,36** (белая печь), макс. 1,08; под HDRI 0,64 (EEVEE) | **по умолчанию**: продукт, брендовый цвет, hex клиента |
| Standard | `NoToneMapping` | 0,22–0,30, макс. 0,73 | unlit/запечённый свет, UI-графика, точный цвет плоских заливок |
| AgX (умолчание Blender) | `AgXToneMapping` | 3,3–3,8, макс. 7,1; three светлее на 3,4–3,7 L* | только если сцена авторилась в AgX; лучше перейти на Neutral |
| ACES 1.3 / 2.0 | `ACESFilmicToneMapping` | 9–13, three светлее на 10–14 L* — разные ACES | не использовать для совпадения |

[проверено: D2/01 `99-raw/experiments/D2/01-brand-color` — таблица и код пары: `../06-materials-lighting-render/03-render-engines-color.md`
§2.2–2.6 (не дублирую); E/02; F1/01 — исходник шейдеров]. Почему Neutral совпадает: в three `NeutralToneMapping` — формула Khronos
PBR Neutral 1:1 (`StartCompression = 0.8 − 0.04`, `Desaturation = 0.15`), в Blender — 3D-LUT того же тонмаппера [проверено: F1/01,
D2]. Зона гарантии — линейные 0,08…0,8 (≈ 80…231 в 8-битном sRGB); каналы у 255 (ярко-жёлтый, оранжевый) бледнеют на ΔE 3–4 — компромисс
Neutral [проверено]. model-viewer 4.x по умолчанию тоже `tone-mapping="neutral"` (до 4.0 — ACES) [документация:
`F1-sub-AR.md` §1; V:0oIZoSg03PY ≈38:00].

### 5.2. AgX: почему не совпадает и что делать

three r186 реализует AgX как приближение Filament (матрицы Rec.2020, полиномиальная сигмоида), вызов «look» закомментирован
(`// v = agxLook(v, look)`), гамут-маппинг — простой clamp, линеаризация `pow(2.2)` [проверено]. D2/01: с `pow 2.4` вместо 2,2
(как у Blender, Rec.1886) расхождение падает с 3,78 до 1,91 ΔE и с +3,4 до +0,9 L* — если AgX обязателен, подменить степень до первой
компиляции шейдеров (код — D2 `../06-materials-lighting-render/03-render-engines-color.md` §2.6) [проверено]. Расхождение
AgX — не поломка экспорта; C1 `../04-ai-agents-mcp/05-failure-modes-catalog.md` M4.6 («одинаковый AgX в Blender и three») этого не
учитывает [спорно → вывод F1/D2: Neutral].

### 5.3. Цветовые пространства текстур и unlit

- `outputColorSpace = SRGBColorSpace` — умолчание; менять не нужно. Рабочее пространство — линейный sRGB [проверено].
- `GLTFLoader` сам ставит `colorSpace = SRGBColorSpace` картам `baseColorTexture`, `emissiveTexture`, `sheenColorTexture`,
  `specularColorTexture`, остальным — линейное [документация: E 01 §5.4]. Свои текстуры (`TextureLoader`, lightMap, видео, canvas):
  цветовым — `tex.colorSpace = THREE.SRGBColorSpace`, данным (нормали, шероховатость) — оставить `NoColorSpace`; карта света
  PNG — sRGB, `.hdr` — `LinearSRGBColorSpace` [проверено].
- `new THREE.Color('#e4002b')` и `color.setHex()` принимают sRGB и переводят в рабочее линейное — hex клиента писать как есть;
  сырой `ShaderMaterial` без `colorspace_fragment` выдаст цвета темнее hex [документация; V: W7 §4].
- **Unlit**: `GLTFLoader` создаёт `MeshBasicMaterial` без `toneMapped = false`, и Neutral сдвигает плоские цвета до ΔE 5,7
  (терракота, navy, violet, серые) — для логотипов и плашек с точным hex `material.toneMapped = false` [проверено].
  Запечённый в Blender свет (unlit-атлас) — тоже `toneMapped = false` или тот же вид при запекании (E 02 §6.1).

## 6. Материалы из Blender в three: что настраивать на странице

### 6.1. Что приходит из GLB само

Контракт экспорта — E `../08-export-gltf/01-export-contract.md` §2, §6–7. Для рантайма важно: `MeshStandardMaterial` по умолчанию;
`MeshPhysicalMaterial` — при clearcoat, transmission, volume, sheen, iridescence, specular, anisotropy, dispersion; `clearcoat` из
`KHR_materials_clearcoat` (ΔE 1,7 к Blender), `emissiveIntensity` из `KHR_materials_emissive_strength` (ΔE ≤ 1) — само, без кода;
«светится» эмиссия только с bloom (F2 `04`) [проверено: E/12–13; F1/01 — список расширений GLTFLoader]. Thin film экспортируется
только через группу «glTF Material Output» (иначе теряется; заменить — `iridescence` в JS или текстура) [проверено].

### 6.2. lightMap и aoMap из Blender

- В glTF нет слота lightMap: карта грузится отдельно и назначается кодом — `channel = 1` (второй UV Blender), `flipY = false`,
  `lightMapIntensity = Math.PI` (для PNG ×0,25 — `4π`; `.hdr` — π, `LinearSRGBColorSpace`); при интенсивности 1 — в π раз темнее,
  ΔE 22. Код — E `../08-export-gltf/02-baking.md` §6.2 [проверено].
- `aoMap` (из `occlusionTexture`) гасит только непрямой свет (окружение, Hemisphere/Ambient): при одном `DirectionalLight` без
  окружения AO не виден [проверено].
- Запечённый свет целиком → unlit (`MeshBasicMaterial`, ΔE 0,73 к Cycles) — самый точный путь «как в Blender», если сцена статична
  [проверено].

### 6.3. Прозрачность и transmission

- `alphaMode` BLEND → `transparent = true`, `depthWrite = false`, сортировка по центрам объектов: вложенные прозрачные объекты
  рисуются в неверном порядке; MASK (`alphaTest`) сортировки не требует [проверено]. `renderOrder` для ручного порядка — не проверено.
- Transmission: `WebGLRenderer` рисует все непрозрачные объекты ещё раз в цель transmission (MSAA, half float, мипмапы) — вызовы и
  треугольники ×2 (Camera_01: 4 → 8 вызовов) [проверено]; первый кадр с компиляцией `MeshPhysicalMaterial` — 387–480 мс [проверено:
  E/18, F1/03]. `renderer.transmissionResolutionScale` (умолчание 1) уменьшает цель — на телефоне 0,5 [проверено: F1/01 — свойство;
  визуально не проверено]. Движки вправе упрощать transmission до альфы [V:MFzmj1TUEKk 02:45] — для телефона стекло лучше предрендером.
- **Стеклу нужен фон внутри canvas**: transmission преломляет только то, что нарисовано в canvas; прозрачный canvas поверх CSS-фона
  (правило §2.3) даёт за стеклом пустоту — для сцены со стеклом `scene.background` или плоскость-фон того же цвета, что CSS
  (в `WebGPURenderer` цвет фона тонмаппится — предкомпенсировать) [проверено: D2 — `../06-materials-lighting-render/03-render-engines-color.md`].

## 7. Тени

| способ | цена | когда |
|---|---|---|
| нет теней, только окружение + AO (запечён в Blender) | 0 | hero-продукт по умолчанию |
| плоскость с запечённой тенью (PNG/KTX2 с альфой под объектом, `MeshBasicMaterial`, `transparent`, `depthWrite: false`) | 1 вызов, 1 текстура 256–512² | «контактная» тень статичного продукта |
| `ShadowMaterial` на плоскости + `castShadow` у модели + один `DirectionalLight` | +1 проход глубины по всем отбрасывающим тень, +1 вызов на объект | объект движется или вращается |
| shadow map от `PointLight` | +6 проходов (кубическая карта) | избегать на телефоне |
| `AccumulativeShadows`/`ContactShadows` drei | несколько проходов (R3F) | F2 `02` |

- r186: `shadowMap.type` по умолчанию `PCFShadowMap` (с r182 он мягкий); `PCFSoftShadowMap` удалён в **обоих** рендерерах — предупреждение
  и замена на `PCFShadowMap` [проверено]. `VSMShadowMap` остался.
- Реальные тени — только движущимся объектам; статичное — запечь в Blender (AO, lightMap, тень-подложка) [V:Inqt1fZ3QTI 23:15;
  V:BH1R29YvLOk 29:49]. Размер карты: 1024² для hero, `shadow.camera` ужать до габарита объекта (иначе лесенка) [практика].
- Цена в вызовах добавляется к оценке `glb_lint()` (E 04 §6) — считать при бюджете вызовов (`05` §4).

## 8. Постобработка (что выбрать; реализация эффектов — F2 `04`)

| рендерер | библиотека | вес сверх three | ограничение |
|---|---|---|---|
| `WebGLRenderer` | pmndrs `postprocessing` 6.39.5 (`EffectComposer`, `EffectPass` сливает эффекты в один проход) | ≈ 12 КБ br | peer three ≥ 0.168 < 0.187; только WebGL; v7 в бете |
| `WebGLRenderer` | `EffectComposer` из addons + `RenderPass` + … + **`OutputPass`** | по проходу | каждый эффект — полноэкранный проход |
| `WebGPURenderer` | `RenderPipeline` (r183: переименован из `PostProcessing`) + узлы TSL (`bloom()`, DOF, GTAO, SSR, TRAA) | в `three.webgpu.js` | только WebGPURenderer |

[документация: A 03 §3.3; W7 §4]. Правило цвета: при `EffectComposer` тонмаппинг и перевод в sRGB делает `OutputPass` (последним);
без него картинка «плоская» и темнее [документация: manual «Post processing»]. У `RenderPipeline` то же делает `outputColorTransform`
(по умолчанию включён; при своих проходах цвета — выключать и применять вручную) [документация: JSDoc r186]. На телефоне — 1–2
эффекта; MSAA при посте включать на цели композера, а не в `antialias` рендерера [практика: A 01 §18].

## 9. Память и жизненный цикл

- GPU-ресурсы не собираются сборщиком мусора: `geometry.dispose()`, `material.dispose()`, `texture.dispose()` для каждой карты
  материала, `renderTarget.dispose()`, `pmrem.dispose()`, `renderer.dispose()` при уходе со страницы/секции [документация: manual
  «How to dispose of objects»]. Картинки `GLTFLoader` в r186 — `ImageBitmap` (кроме Safari < 17, Firefox < 98): закрывать `close()`,
  иначе декодированный битмап живёт в памяти процесса [документация: E 01 §7.2; проверено: F1/06].
- Контроль: `renderer.info.memory.geometries`/`.textures` после выгрузки возвращаются к исходным значениям: Camera_01 — геометрии
  15 → 19 → 15, текстуры 5 → 15 → 6; лишняя одна — цель transmission, которую держит рендерер (у модели стекло), до `renderer.dispose()`
  [проверено].
- Сцены по секциям (Shopify Editions): смонтированы только активная и соседние, остальные — `dispose()` [практика: A 02 §4.4].
- iOS Safari перезагружает вкладку при ≈ 200–400 МБ памяти [V:BH1R29YvLOk 43:28; данные 2024, не проверено на 2026] — текстуры
  RGBA8 2048² ×9 = 192 МБ (E/18) хватит, чтобы уронить вкладку; KTX2 и 1k — `06` §3.

```js
// three r186 — [проверено] выгрузка модели: геометрии, материалы, текстуры (ImageBitmap — close)
export function disposeObject(root) {
  const textures = new Set();
  root.traverse((o) => {
    o.geometry?.dispose();
    for (const m of [o.material].flat().filter(Boolean)) {
      for (const v of Object.values(m)) if (v?.isTexture) textures.add(v);
      m.dispose();
    }
  });
  for (const t of textures) { t.source?.data?.close?.(); t.dispose(); }   // ImageBitmap из GLTFLoader освобождаем явно
  root.removeFromParent();
  return textures.size;
}
```

Потеря контекста (моб. Safari, переключение GPU): слушать `webglcontextlost` (`event.preventDefault()`, остановить цикл, вернуть
постер) и `webglcontextrestored` (пересоздать рендерер и сцену) — `05` §7 [документация: MDN; не проверено].

## 10. Resize и devicePixelRatio

- Размер задаёт CSS контейнера (`aspect-ratio` — CLS 0), canvas — `width:100%; height:100%`; буфер — `renderer.setSize(w, h, false)`
  (третий аргумент `false`: не писать inline-стили) по `ResizeObserver` контейнера, а не `window.resize` [практика: A 02 §2.3].
- `setPixelRatio(Math.min(devicePixelRatio, 1.5))` на телефоне, до 2 на десктопе; лидеры рендерят телефон в 1,5 (A/04:
  canvas 618×1259 при CSS 412×839), Spline в полном 2,625 — TBT 1,9 с [проверено]. Память одних буферов кадра (цвет + глубина,
  MSAA 4×) для экрана Pixel 7: DPR 1 — 13 МБ, 1,5 — 29 МБ, 2 — 52 МБ, 2,625 — 89 МБ, 3 — 116 МБ; без MSAA — 3/6/12/20/26 МБ; цель
  transmission — ещё столько же [проверено: F1/04 (расчёт)]. При DPR ≥ 2 MSAA можно выключать (резкость даёт сам DPR; антиалиасинг на
  ретине — лишние до ×2 [V:yibGMQ7GGVo 45:32]) [практика].
- Время кадра от DPR на встроенной графике ноутбука не растёт (×1,2–1,3 при ×6,9 пикселей, F1/04) — стенд не упирается в заполнение;
  на телефоне упирается, но на устройствах не мерилось [не проверено]. Тяжёлый пересчёт (PMREM, render targets) — после окончания
  resize, не на каждый кадр ресайза [V:Uc3Ujdh8Ba4 06:19].

```js
// three r186 — [проверено] размер буфера = размер контейнера × ограниченный DPR
export function autoResize(renderer, camera, host, { maxDpr = 1.5, onResize } = {}) {
  const ro = new ResizeObserver(([entry]) => {
    const { width: w, height: h } = entry.contentRect;
    if (!w || !h) return;
    renderer.setPixelRatio(Math.min(devicePixelRatio, maxDpr));   // DPR меняется при переносе окна между экранами
    renderer.setSize(w, h, false);                                  // CSS задаёт размер, false — без inline-стилей
    camera.aspect = w / h; camera.updateProjectionMatrix();
    onResize?.(w, h);                                               // сюда — перерисовать кадр, если цикл остановлен
  });
  ro.observe(host);
  return () => ro.disconnect();
}
```

## 11. Поиск узлов после экспорта и постобработки

- three санитизирует имена узлов: пробел → `_`, удаляются `[ ] . : /` («Cube.001» → «Cube001»); исходное имя — `userData.name`
  (при `export_extras`) [проверено]. Имена в Blender — латиница, цифры и `_` (`hero_body`, `btn_buy`) — тогда одинаковы везде.
- `gltf-transform optimize` с квантованием вставляет узел-обёртку: имя у родителя, меш — ребёнок (`hero_orb` → `hero_orb_1`);
  `optimize` по умолчанию сливает меши и теряет имена; gltfpack без `-kn -ke` выбрасывает имена и extras [проверено].

```js
// three r186 — [проверено] узел по имени из Blender: санитизация three + обёртка квантования
export function findNode(root, blenderName) {
  const safe = blenderName.replace(/\s/g, '_').replace(/[[\].:/]/g, '');   // как PropertyBinding.sanitizeNodeName
  let node = root.getObjectByName(safe);
  if (!node) root.traverse((o) => { if (!node && o.userData.name === blenderName) node = o; });
  if (!node) return { node: null, mesh: null };
  let mesh = node.isMesh ? node : null;
  if (!mesh) node.traverse((o) => { if (!mesh && o.isMesh) mesh = o; });   // квантование: меш — ребёнок узла с именем
  return { node, mesh };
}
```

## 12. Почему картинка блёклая или «не такая, как в Blender» — проверки по порядку

| # | симптом | причина | исправление | источник |
|---|---|---|---|---|
| 1 | всё серое, «плоское», белые пересвечены | тонмаппинг не включён (умолчание `NoToneMapping`), а сцена светлее 1 | `NeutralToneMapping` (пара Neutral) | F1/01, D2/01 |
| 2 | цвет бренда розовеет/бледнеет | Blender-рендер в AgX, в three другой тонмаппер или AgX без поправки | вид «Khronos PBR Neutral» в Blender и `NeutralToneMapping` | D2/01, A/06 |
| 3 | three светлее Blender на 2–4 L* при AgX | разные реализации AgX (степень 2,2 и 2,4) | Neutral или `CustomToneMapping` D2 | D2/01, E/02 |
| 4 | верхние грани в Blender на ≈ 13 L* светлее | EEVEE выносит яркое из HDRI в «солнце» (`world.sun_threshold` 10) | сверять с Cycles или `sun_threshold = 0` | D2 `../06-materials-lighting-render/03` §3, E/20 |
| 4а | стекло «пустое», за ним чёрное/прозрачное | прозрачный canvas: transmission не видит CSS-фон | фон внутри canvas для сцен со стеклом (§6.3) | D2 03 |
| 5 | металл чёрный | нет `scene.environment` | RoomEnvironment/HDRI (§4) | E/23 |
| 6 | всё темнее в π раз | `lightMapIntensity` 1 для карты Blender | `Math.PI` (§6.2) | E/21 |
| 7 | плоский логотип сдвинут по цвету | unlit тонмаппится | `toneMapped = false` | D2/01 |
| 8 | фон canvas темнее CSS-фона | `WebGPURenderer` тонмаппит `scene.background` | прозрачный canvas | F1/05 |
| 9 | после постобработки цвета тусклые | нет `OutputPass` в `EffectComposer` | `OutputPass` последним (§8) | документация |
| 10 | своя текстура/видео выцветшие или «кислотные» | не задан `colorSpace` | цвет — `SRGBColorSpace`, данные — нет | E 01 §5.4 |
| 11 | цвет модели верный, а в Blender бледнее | Non-Color на цветовой карте в Blender (веб прав) | sRGB для цвета в Blender | E/12 |
| 12 | узор/градиент пропал, объект белый | процедурные ноды не экспортируются | запечь (E 02) | E/12, A/06 |
| 13 | «мыло», мерцание на мелких деталях | ETC1S на детальных картах, нет мипмапов, DPR 1 на ретине | UASTC для нормалей, мипмапы, DPR ≤ 1,5–2 | F1/03, V:yibGMQ7GGVo 30:55 |
| 14 | лесенка по краям | `antialias: false` (умолчание рендерера) при DPR 1 | `antialias: true` или DPR 1,5 | V:yibGMQ7GGVo 28:52 |
| 15 | тёмная кайма у прозрачных краёв | непредумноженная альфа (PNG/видео) | `premultipliedAlpha`, «bleed» краёв | V:yibGMQ7GGVo 36:10 |
| 16 | сцена «грязная», тусклая | AO и в Base Color, и в `aoMap` (двойное затемнение) | одно из двух | E 02 ч. ош. 16 |
| 17 | постер и 3D отличаются при подмене | постер отрендерен до запекания или в другом виде | постер из того же GLB и той же пары (hero-lazy) | A/07 |
| 18 | модель слишком тёмная без ламп | сцена авторилась с лампами Blender, свет не экспортирован | окружение + `environmentIntensity`, либо запечь | E/14 |

Сравнение «как в Blender» — `../../scripts/3d/gltf_diff.py … --tone neutral` (порог ΔE2000 ≤ 3,5, IoU ≥ 0,99; E/02).

## Частые ошибки

Нейросеть пишет по памяти (three r1xx до 2024) и получает в r186:
1. `renderer.outputEncoding = THREE.sRGBEncoding` — удалено (r152) → `outputColorSpace` (и его не трогать) [документация].
2. `new RGBELoader()` → предупреждение (r180) → `HDRLoader` [проверено].
3. `new THREE.Clock()` → предупреждение (r183) → `THREE.Timer` + `timer.update()` каждый кадр [проверено].
4. `renderer.shadowMap.type = THREE.PCFSoftShadowMap` → «has been removed. Using PCFShadowMap» в обоих рендерерах [проверено].
5. `new USDZLoader()` → предупреждение (r179) → `USDLoader` [проверено].
6. `new RoomEnvironment(renderer)` — лишний аргумент (игнорируется) [проверено].
7. `renderer.render()` у `WebGPURenderer` до `await renderer.init()` [документация r181].
8. Декодеры с `examples/js/libs/draco/` — 404 в r186 → `examples/jsm/libs/draco/gltf/` [проверено: E 03].
9. `<script src="three.min.js">` — в r186 нет min-сборок и UMD; import map с `three.module.min.js` без переназначения ядра тянет
   неминифицированное ядро [проверено].
10. `renderer.physicallyCorrectLights = true` — удалено; интенсивности уже физические [документация].
11. Тонмаппинг не включён «потому что в Blender так» — в Blender AgX включён всегда (умолчание), в three — выключен [проверено].
12. Все декодеры подключены «на всякий случай» — +212 КБ br за транскодер KTX2 без KTX2-текстур [проверено].
13. `compileAsync` как средство от TBT — не снимает синхронную часть [проверено].
14. Поиск `getObjectByName('Cube.001')` → `undefined` [проверено].
15. `renderer.info.render.calls` как «вызовов за кадр» у `WebGPURenderer` — накопительный [проверено].

## Чек-лист

- [ ] three из бандла на своём домене (или import map с переназначением ядра), версия закреплена `0.186.0`?
- [ ] Декодеры подключаются по `extensionsUsed`, лежат на своём домене той же версии, отдаются с brotli и `application/wasm`?
- [ ] `WebGLRenderer`, если нет compute/сплатов/TSL; при `WebGPURenderer` — `await init()`, откат проверен?
- [ ] Тонмаппинг `NeutralToneMapping` и рендер Blender в «Khronos PBR Neutral»; unlit-логотипы — `toneMapped = false`?
- [ ] Окружение есть (RoomEnvironment или HDRI 1k), металл не чёрный?
- [ ] `compileAsync` до первого кадра, первый кадр модели помечен своей меткой?
- [ ] lightMap — `channel 1`, `flipY false`, интенсивность π; свет не удвоен?
- [ ] Тени запечены или одна `DirectionalLight` только для движущегося; `PCFSoftShadowMap` не используется?
- [ ] `setPixelRatio(min(dpr, 1.5))` на телефоне, `ResizeObserver`, `setSize(w, h, false)`?
- [ ] При уходе — `disposeObject`, `renderer.dispose()`; `info.memory` вернулся к исходному?
- [ ] Узлы находятся по имени после постобработки (`findNode`)?
- [ ] Консоль без предупреждений `deprecated` от своего кода?

## Открытые вопросы и противоречия

- Телефоны не мерились: все числа — Chromium headless на Iris Xe (эмуляция CPU ×4 и сети); цена DPR и KTX2-транскодирования на
  ETC/ASTC — [не проверено] на устройствах (A, E — тот же пробел).
- `transmissionResolutionScale = 0.5` — проверено F2/05: −20 % времени кадра без видимой потери (`04-shaders-effects-catalog-impl.md` §3).
- Vite (`vite build`) — не проверялся, только esbuild (тот же принцип чанков).
- Потеря контекста (`webglcontextlost`) и восстановление сцены — по документации, не проверено.
- Лимит памяти вкладки iOS 200–400 МБ — источник 2024 (через доклад), актуальность 2026 не проверена.
- A/08 (4,4 с первого кадра WebGPU) против F1/05 (922 мс) — разные сцены (TSL-смещение 48 подразбиений против PBR GLB), 1 и 6 прогонов;
  позиция: первый кадр WebGPU зависит от числа и сложности пайплайнов, для PBR-hero не хуже WebGL.

## Источники

- [S1] three.js r186, npm `three@0.186.0` — `build/three.module.js`, `three.core.js`, `three.webgpu.js`, `examples/jsm/*`, шейдер
  `tonemapping_pars_fragment.glsl.js`; прочитаны разделы (grep) — `99-raw/experiments/F1/01-package-facts/facts.txt`; первоисточник.
- [S2] jsDelivr, автоминификация `three@0.186.0/build/*.min.js` (Terser 5.48.0), 23.09.2026 — `F1/01/jsdelivr_min.txt`.
- [S3] Эксперименты F1: `99-raw/experiments/F1/01-package-facts`, `02-hero-variants`, `03-ktx2-webp`, `04-dpr`, `05-webgl-webgpu`,
  `06-doc-snippets` (README с командами и таблицами) — [проверено].
- [S4] D2, волна 2: `99-raw/experiments/D2/01-brand-color` и `99-raw/notes/wave2/D2-notes.md` (раздел «Для F1») — пары тонмаппинга,
  unlit, AgX 2,2/2,4 — [проверено D2].
- [S5] E, волна 1: `../08-export-gltf/01–04` — контракт, lightMap ×π, AO, transmission ×2, декодеры, санитизация — [проверено E].
- [S6] A, волна 1: `../01-web-3d-landscape/02` §4, `03` §2–3 — паттерн A/07, WebGPU A/08, бандлы A/03 — [проверено A].
- [S7] three.js wiki, Migration Guide r150→r186 (через A 03 §2.3) — переименования; [документация].
- [S8] Khronos, PBR Neutral tone mapper (через D2 и исходник three) — [документация].
- [S9] model-viewer 4.3.1 docs/FAQ/исходник — тонмаппинг по умолчанию (через `F1-sub-AR.md`) — [документация].
- [S10] Доклады (выписка помощника по 12 транскриптам, `99-raw/notes/wave2/F1-sub-core.md`): [V:3YP5Ck-7NZk] Khronos SIGGRAPH 2026;
  [V:7we9mqIOKyw] mrdoob 2024; [V:sqkSrTq1Kos] HolyJS 2025; [V:yibGMQ7GGVo] Попелышев 2020 (2D-артефакты, не цвет);
  [V:Inqt1fZ3QTI] Optimization Iceberg (Babylon); [V:Uc3Ujdh8Ba4] Bruno Simon, девлог 10; [V:BH1R29YvLOk] Самокат — [практика/мнение].
- [S11] W7 (дайджесты three.js/WebGPU), `99-raw/reports/wave2-W7-report.md` §4, §8 — compat mode и MSAA, лимиты WebGPU — [V].
- [S12] W3, `99-raw/reports/wave2-W3-report.md` §8 → F1 — Neutral, transmission [V:0oIZoSg03PY, V:MFzmj1TUEKk] — [V].
