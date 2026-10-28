# Поставки не-GLB, AR и USDZ, текстурный конвейер KTX2, особенности WebGPU (three r186)

Волна 2 · агент F1 · 23.09.2026 · опора: эксперименты `99-raw/experiments/F1/01` (исходник r186), `03` (KTX2/WebP/AVIF на одной модели),
`05` (WebGL/WebGPU), `06` (прогон блоков), демо `examples/hero-lazy`; A `../01-web-3d-landscape/05-blender-deliverables-map.md` (карта
поставок, A/06 — одна сцена во всех форматах); E `../08-export-gltf/03` (сжатие); выписка по AR (`99-raw/notes/wave2/F1-sub-AR.md`:
model-viewer 4.3.1 — документация и исходник, Scene Viewer, Quick Look); Blender 5.2.2 — параметры `wm.usd_export` из самого
Blender (`bpy_probe.py`); W7 (дайджесты WebGPU) · версии: three 0.186.0, model-viewer 4.3.1 (three 0.183 внутри), Blender 5.2.2,
gltf-transform 4.5.0, toktx 4.4.2, gltfpack 1.2 · блоки JS и Python исполнены `99-raw/experiments/F1/06-doc-snippets`. Сплаты и
`KHR_gaussian_splatting` — у G (`../10-ai-3d-generation-assets/`); как поставки делаются в Blender — D2 (`../06-materials-lighting-render/`),
D1 (`../05-modeling/`), H (`../07-animation/`).

## Выжимка для агента

1. **Секвенция кадров — окно памяти, а не все кадры**: декодированный кадр 1080² = 4,5 МБ RGBA; окно 12 кадров ≈ 54 МБ; телефону — отдельный набор 720 px (2 МБ/кадр) → §1.1. [расчёт; проверено: F1/06 — окно держит ≤ 12 битмапов]
2. **Сначала первые 10 кадров, потом окно по направлению прокрутки** (OPTIKKA: ±5), кадры через `createImageBitmap` и `close()` вне окна → §1.1. [практика: A 02 §4.4; проверено: F1/06]
3. **Видео с альфой**: `<video>` с HEVC-alpha первым (Safari) и VP9-alpha WebM (Chrome/Firefox) или один stacked-файл (цвет сверху, альфа снизу) + шейдер; анимированный AVIF — нет → §1.2. [проверено: A/06 — альфа 0/255 в Chromium; практика: Archibald 2024]
4. **Stacked-альфа в three**: текстура без sRGB-декодирования (`NoColorSpace`), альфа из нижней половины по R, цвет — из верхней (при `flipY = true`), вывод без повторного перевода в sRGB → §1.2. [проверено]
5. **Точки для частиц**: `.bin` Float32 little-endian (x, y, z) уже в осях three (Blender (x, y, z) → (x, z, −y)), 12 Б/точку; для морфинга — одинаковое число и порядок точек на форму → §1.3. [проверено: F1/06 — загрузчик; формат — согласовать с D1]
6. **Путь камеры — JSON точек в осях three** → `CatmullRomCurve3(points, closed, 'catmullrom', 0.5)`; равномерный ход — `getPointAt(t)` → §1.4. [проверено: F1/06; практика: Codrops 2026-07-07]
7. **Маркеры — пустышки Blender с префиксом имени** (`hotspot_*`) и custom properties (`export_extras=True`) → `userData`; искать по санитизированному имени или `userData.name`, позиция — `getWorldPosition` → §1.5. [проверено]
8. **AR — отдельный GLB без сжатия**: Scene Viewer в документации знает только `KHR_materials_unlit` и `KHR_texture_transform`; Draco, Meshopt, KTX2, WebP не упомянуты, а model-viewer отдаёт Scene Viewer исходный `src` → `src` веб-версии со сжатием нельзя давать в AR на Android → §2.2. [документация: F1-sub-AR §1–2]
9. **Лимиты Scene Viewer**: ≤ 100 тыс. треуг. (идеал 30–50 тыс.), ≤ 10 материалов (2 с альфой), текстуры ≤ 2048², 1 UV, ≤ 254 кости, 4 веса, ≤ 10 МБ (15 — ошибка), морфы и цвета вершин — ошибки, одна анимация → §2.2. [документация: Scene Viewer, обновл. 2024-10-31]
10. **model-viewer: `ios-src` почти обязателен**: без него USDZ генерируется на лету (без анимаций), а в Chrome/Edge/Firefox на iOS Quick Look работает только с `ios-src`; в приложении Google на iOS Quick Look выключен → §2.3. [документация: исходник model-viewer 4.3.1 `ar.ts`]
11. **model-viewer 4.3.1 требует three ^0.183** — держать отдельным скриптом (CDN Google), не в бандле с r186 → §2.1. [проверено: A — npm ERESOLVE]
12. **USDZ из Blender 5.2.2**: `bpy.ops.wm.usd_export(filepath="….usdz", …)`, UsdPreviewSurface (`generate_preview_surface=True`), текстуры в пакет (`export_textures_mode="NEW"`), `usdz_downscale_size="2048"`, `export_subdivision="TESSELLATE"`, Y-up (`convert_orientation=True`); `visible_objects_only` и `export_textures` в 5.2 нет → §2.4. [проверено: bpy_probe (имена, умолчания), F1/06 (экспорт куба); вид в Quick Look — не проверено, нет Mac]
13. **three r186 читает USDZ** (`USDLoader`; `USDZLoader` — устаревшее имя с r179) и пишет (`USDZExporter`: `maxTextureSize` 1024, клипы анимации, KTX2 через `setTextureUtils`) → §2.4. [проверено]
14. **KTX2 выигрывает память и CPU, не байты**: Camera_01 1k — ETC1S 1157 КБ (WebP 940), GPU 12 МБ (48), первый кадр при CPU ×4 108 мс (206) → §3.1. [проверено]
15. **На медленной сети с текстурами 512² KTX2 проигрывает** (транскодер 212 КБ br: wasm 199 + js 13): первый кадр hero 7,1 с против 5,2 с у WebP → телефону при ≤ 512² и одной модели — WebP → §3.2. [проверено: hero-lazy]
16. **UASTC для веба — точечно**: с RDO по KTX Artist Guide (λ 0,25 нормали / 0,5 ORM, zstd 22) 1k-набор — 5,6 МБ против 6,0 без RDO, кодирование 139 с → только критичная нормаль крупного плана → §3.1. [проверено]
17. **ETC1S «по Artist Guide» (`--quality 255 --compression 4`) не лучше умолчаний** на этом ассете (ΔE 0,24 против 0,25) при файле ×1,5 → умолчание `etc1s` → §3.1. [проверено]
18. **KTX2 — из PNG, размеры кратны 4**, для телефона — `gltfpack -cc -tc -ts 0.5` или `gltf-transform etc1s` + `resize`; вход gltfpack `-tc` — JPEG/PNG, не WebP → §3.3. [проверено: F1/03, E/24; документация: KTX Artist Guide]
19. **Linux/Mesa — BC7, телефон — ETC/ASTC**: все наши замеры KTX2 — путь BC7 (KTX2Loader отключает ETC/ASTC на Mesa); ASTC 12×12 и XUASTC новых кодеров Basis `KTX2Loader` r186 не читает → §3.4. [проверено: E/18; документация: W7 §8]
20. **`WebGPURenderer` рисует GLB из Blender без правок**: классические материалы → node-материалы автоматически; lightMap, transmission, тени PCF поддержаны; `onBeforeCompile`/`ShaderMaterial` — нет → §4. [проверено]
21. **WebGPU-мелочи**: `await init()` до `KTX2Loader.detectSupport`; фон `scene.background` тонмаппится; `info.render.calls` накопительный; в compat mode MSAA выключен; постобработка — `RenderPipeline` → §4. [проверено: F1/05; документация: W7 §8]
22. **Когда WebGPU на сайте** — `01` §2.2: первый кадр не хуже WebGL, но откат на WebGL2 медленнее обычного `WebGLRenderer` в 1,7 раза → только ради compute/сплатов/TSL. [проверено]

## 1. Загрузчики поставок не-GLB (карта поставок — A `05` §1, §3)

### 1.1. Секвенция кадров с окном памяти

| параметр | десктоп | телефон | основание |
|---|---|---|---|
| кадров | 120–200 | 60–100 | A 05 §3.14 (OPTIKKA, Apple) |
| размер | 1080–1440 px | 720 px | то же |
| формат | WebP q80 / AVIF q55 | то же | A/06: 48 кадров 768² — WebP 183–386 КБ, AVIF 105–186 КБ |
| память кадра (RGBA) | 1080² — 4,5 МБ | 720² — 2,0 МБ | w × h × 4 |
| окно в памяти | 12–20 кадров (54–90 МБ) | 10–12 (20–24 МБ) | позиция; весь ряд 200 × 1080² = 900 МБ — падение вкладки |

```js
// Canvas 2D / createImageBitmap — [проверено] секвенция с окном памяти: кадр по индексу, соседние — заранее
export class ImageSequence {
  constructor(canvas, urls, { window: win = 12, preload = 10 } = {}) {
    Object.assign(this, { canvas, urls, win, preload, frames: new Map(), pending: new Map(), current: 0, dir: 1 });
    this.ctx = canvas.getContext('2d');
  }
  async init() {                                       // первые кадры сразу, первый кадр — на холст
    await Promise.all(this.urls.slice(0, this.preload).map((_, i) => this.#load(i)));
    this.#draw(0);
  }
  show(i) {                                            // i — целый индекс (прогресс прокрутки × (n − 1))
    i = Math.max(0, Math.min(this.urls.length - 1, Math.round(i)));
    if (i !== this.current) this.dir = Math.sign(i - this.current);
    this.current = i;
    this.#draw(i);
    const ahead = Math.ceil(this.win * 0.75), behind = this.win - ahead;   // больше кадров по направлению движения
    const lo = this.dir > 0 ? i - behind : i - ahead, hi = this.dir > 0 ? i + ahead : i + behind;
    for (let k = Math.max(0, lo); k <= Math.min(this.urls.length - 1, hi); k++) this.#load(k);
    for (const [k, bmp] of this.frames) if (k < lo || k > hi) { bmp.close(); this.frames.delete(k); }   // освободить вне окна
  }
  #draw(i) {                                           // нет кадра — ближайший загруженный (без пустого холста)
    let k = i, best = null;
    for (let d = 0; d < this.urls.length && !best; d++) best = this.frames.get(k + d) || this.frames.get(k - d);
    if (best) this.ctx.drawImage(best, 0, 0, this.canvas.width, this.canvas.height);
  }
  #load(i) {
    if (this.frames.has(i) || this.pending.has(i)) return this.pending.get(i);
    const p = fetch(this.urls[i]).then((r) => r.blob()).then((b) => createImageBitmap(b)).then((bmp) => {
      this.pending.delete(i); this.frames.set(i, bmp);
      if (i === this.current) this.#draw(i);
    });
    this.pending.set(i, p);
    return p;
  }
}
```

- Canvas 2D, а не WebGL: одна операция `drawImage` на кадр, нет three (0 КБ JS), не нужен контекст WebGL [практика: A 05 §3.14].
- Reduce: один ключевой кадр без привязки к прокрутке; привязку к прокрутке (ScrollTrigger/Lenis/CSS) — F2 `03`.
- Короткий ролик (≤ 3–5 с) с перемоткой — all-intra видео (`-g 1`, ×3–4 к весу) вместо секвенции [проверено].

### 1.2. Видео с альфой

```html
<!-- [проверено: 99-raw/experiments/A/06-deliverable-sizes/playback.html — VP9-alpha в Chromium; HEVC-alpha — только Safari, не проверено] -->
<video autoplay muted loop playsinline poster="hero.webp" width="768" height="768" aria-hidden="true">
  <source src="hero-hevc-alpha.mov" type='video/mp4; codecs="hvc1"'>   <!-- Safari: первым -->
  <source src="hero-vp9-alpha.webm" type="video/webm">                <!-- Chrome, Firefox, Edge -->
</video>
```

Размеры (A/06, 2 с, 768²): VP9-alpha 19–61 КБ, stacked AV1 14–39 КБ, stacked HEVC 28–77 КБ; HEVC-alpha кодируется только на macOS
(VideoToolbox) — поэтому stacked-путь для генерации на Linux [проверено]. Команды ffmpeg — A `05` §3.15. Reduce и WCAG 2.2.2:
петля > 5 с — пауза (или постер при reduce) [документация: UM3 §2.2].

```js
// three r186 — [проверено] stacked-alpha: цвет — верх кадра, альфа — низ (ffmpeg vstack), VideoTexture с flipY
import * as THREE from 'three';

export function createStackedAlphaMaterial(texture) {
  texture.colorSpace = THREE.NoColorSpace;             // байты sRGB как есть: альфу нельзя «линеаризовать»
  texture.minFilter = texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  return new THREE.ShaderMaterial({
    uniforms: { map: { value: texture } },
    vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `uniform sampler2D map; varying vec2 vUv;
      void main() {
        vec3 rgb = texture2D(map, vec2(vUv.x, 0.5 + vUv.y * 0.5)).rgb;   // верхняя половина (flipY: верх = большие v)
        float a = texture2D(map, vec2(vUv.x, vUv.y * 0.5)).r;            // нижняя половина: маска в R
        gl_FragColor = vec4(rgb, a);                                     // уже sRGB: без colorspace_fragment
      }`,
    transparent: true, depthWrite: false,
  });
}
// const video = document.querySelector('video'); const mat = createStackedAlphaMaterial(new THREE.VideoTexture(video));
// scene.add(new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat));   // плоскость с пропорциями половины кадра
```

Для stacked-видео без three хватает WebGL2-квада на 20 строк (A/06 `playback.html`, фильтрация `NEAREST`) [проверено].

### 1.3. Точки для частиц (Float32)

Формат поставки (предложение F1 для D1/F2, согласовать в `05-modeling/`): `name.bin` — little-endian Float32 `x, y, z` подряд,
уже в осях three (Blender `(x, y, z)` → `(x, z, −y)`), 12 Б/точку (100 тыс. = 1,2 МБ; brotli на случайных точках поверхности −14 %, K/04); при нескольких формах — одинаковое
число точек и стабильный порядок (морфинг по индексу); цвет/нормаль — отдельные файлы того же порядка [практика: A 05 §3.8].

```js
// three r186 — [проверено] точки из .bin (Float32 xyz в осях three) → THREE.Points
import * as THREE from 'three';

export async function loadPoints(url, { size = 0.01, color = 0xffffff } = {}) {
  const buf = await (await fetch(url)).arrayBuffer();
  if (buf.byteLength % 12) throw new Error(`${url}: длина ${buf.byteLength} не кратна 12 (Float32 × 3)`);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(buf), 3));
  geometry.computeBoundingSphere();
  return new THREE.Points(geometry, new THREE.PointsMaterial({ size, color, sizeAttenuation: true }));
}
```

Для морфинга второй формы — `geometry.setAttribute('aPositionB', …)` и смешивание в шейдере по `uProgress` (F2 `04`). Телефон —
20–30 тыс. точек (A 01 §6.2) [практика].

### 1.4. Путь камеры (JSON)

Формат: `{"points": [[x, y, z], …], "closed": false}` в осях three; число точек — `resolution_u` кривой Blender; объект кривой брать
по имени, а не `active_object` [практика: A 05 §3.9; Codrops 2026-07-07].

```js
// three r186 — [проверено] путь из Blender (JSON, оси three) → кривая с равномерным ходом
import * as THREE from 'three';

export async function loadPath(url) {
  const { points, closed = false } = await (await fetch(url)).json();
  const curve = new THREE.CatmullRomCurve3(points.map(([x, y, z]) => new THREE.Vector3(x, y, z)), closed, 'catmullrom', 0.5);
  curve.arcLengthDivisions = Math.max(200, points.length * 8);   // точность getPointAt (равный шаг по длине)
  return curve;                                                  // camera.position.copy(curve.getPointAt(t)); lookAt(curve.getPointAt(t + 0.01))
}
```

`getPoint(t)` идёт по параметру (неравномерно по длине), `getPointAt(t)` — по длине дуги [документация three]. Прокрутка → `t` с
затуханием (`MathUtils.damp`) — F2 `03`.

### 1.5. Маркеры (пустышки) и extras

Пустышки Blender (Empty) с именами-соглашениями (`hotspot_*`, `cam_*`, `collider_*`) и custom properties → узлы glTF (`export_extras=True`)
→ `Object3D` с `userData`; имя санитизируется (`hotspot.buy` → `hotspotbuy`, исходное — `userData.name`); gltfpack без `-kn -ke`
выбрасывает и то, и другое [проверено].

```js
// three r186 — [проверено] маркеры из GLB: пустышки по префиксу имени, мировые позиции, проекция на экран
import * as THREE from 'three';

export function collectMarkers(root, prefix = 'hotspot_') {
  const out = [];
  root.updateMatrixWorld(true);
  root.traverse((o) => {
    const name = o.userData.name || o.name;                      // исходное имя Blender (GLTFLoader пишет всегда, от export_extras не зависит)
    if (name.startsWith(prefix)) out.push({ name, object: o, position: o.getWorldPosition(new THREE.Vector3()), data: o.userData });
  });
  return out;
}

export function projectToScreen(position, camera, width, height) {   // для DOM-меток: CSS px внутри canvas
  const p = position.clone().project(camera);
  return { x: (p.x + 1) / 2 * width, y: (1 - p.y) / 2 * height, visible: p.z > -1 && p.z < 1 && Math.abs(p.x) <= 1 && Math.abs(p.y) <= 1 };
}
```

Метки — DOM-кнопки поверх canvas (фокус, клавиатура, скринридер), не текст в WebGL [документация: A 01 §3.6; XA2 §8].

## 2. AR: «посмотреть у себя»

### 2.1. model-viewer 4.3.1: как устроено

| режим | где | как запускается | что уходит |
|---|---|---|---|
| WebXR | Chrome Android 83+ (режим по умолчанию на Android), HTTPS | `immersive-ar` сессия внутри страницы | та же модель, правки материалов видны; DOM-оверлеи работают |
| Scene Viewer | Android (не Firefox, не Oculus) | intent `scene-viewer/1.2`, `mode=ar_preferred`, `disable_occlusion=true` | **исходный `src`** (Scene Viewer заново скачивает URL) |
| Quick Look | iOS Safari (`<a rel="ar">`) | `ios-src` или USDZ, сгенерированный на лету `USDZExporter` | USDZ без анимаций при автогенерации |

[документация: F1-sub-AR §1 — docs и исходник `src/features/ar.ts` @4.3.1]. Кнопка AR видна, если AR «потенциально доступен» (бывают
ложные срабатывания). В Chrome/Edge/Firefox на iOS Quick Look работает только с `ios-src`; в приложении Google на iOS — выключен
(противоречит заметке к 4.3.0, где заявлено исправление для GSA). `activateAR()` — только из обработчика жеста. `ar-scale="fixed"` → 100 %,
без масштабирования; `ar-placement="wall"` — задней гранью (−Z) к стене [документация: F1-sub-AR §1].

```html
<!-- model-viewer 4.3.1 — [документация: modelviewer.dev/docs, исходник 4.3.1; не проверено запуском в AR] витрина + AR: веб-GLB, AR-GLB и USDZ отдельно -->
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.3.1/model-viewer.min.js"></script>
<model-viewer src="product-ar.glb" ios-src="product.usdz" poster="poster.webp" alt="Красная кружка 350 мл с матовой глазурью"
  loading="lazy" reveal="auto" camera-controls touch-action="pan-y" tone-mapping="neutral" shadow-intensity="0.6"
  ar ar-modes="webxr scene-viewer quick-look" ar-scale="fixed" style="display:block;width:100%;height:auto;aspect-ratio:1">
  <button slot="ar-button">Посмотреть у себя в комнате</button>
</model-viewer>
```

- `src` — GLB, который примет Scene Viewer (§2.2): без Meshopt/Draco/KTX2. Если на странице нужен лёгкий сжатый GLB, AR-файл
  отдельный, а витрину делать своим three (hero-lazy) + кнопка AR с intent/`rel="ar"` [вывод F1 из документации].
- Подпись кнопки — словами («Посмотреть у себя»): иконки AR непонятны [исследование: NN/g через A 02 §6.2].
- Декодеры model-viewer: Draco и KTX2 — с CDN Google по требованию, Meshopt — только при `meshoptDecoderLocation` [документация].

### 2.2. Лимиты Scene Viewer (AR-файл Android)

| параметр | значение | тип |
|---|---|---|
| расширения glTF | `KHR_materials_unlit`, `KHR_texture_transform` (валидатор ещё `KHR_materials_pbrSpecularGlossiness`); Draco, Meshopt, KTX2, WebP, `KHR_mesh_quantization` — не упомянуты | требования к файлу |
| треугольники | ≤ 100 000 (идеал 30–50 тыс.) | предупреждение |
| материалы | ≤ 10, из них с альфой ≤ 2; 1 меш на материал | предупреждение |
| текстуры | ≤ 2048²; PNG-24/PNG-8/JPEG, sRGB | предупреждение |
| UV | 1 набор на меш | ошибка |
| кости / веса | ≤ 254 / ≤ 4 | ошибка |
| морфы, цвета вершин | запрещены | ошибка |
| анимации | одна (играет первую по кругу) | ошибка при > 1 |
| размер | 10 МБ рекомендовано, 15 МБ — ошибка | |
| оси, единицы | +Y вверх, «перед» к +Z, 1 ед. = 1 м (= экспорт Blender с `export_yup`) | |
| тени | рисуются сами — не запекать | |

[документация: developers.google.com/ar/develop/scene-viewer, обновл. 2024-10-31, через F1-sub-AR §2]. Проверка файла —
arvr.google.com/scene-viewer-preview [не проверено]. Для товаров в Google — Merchant: GLB ≤ 10 (15) МБ, «4K — лучше всего» (противоречит
2048² Scene Viewer) [документация: F1-sub-AR §6].

AR-GLB из Blender: пресет E `static_hero` без постобработки сжатием геометрии, текстуры JPEG/PNG ≤ 2048², ≤ 100 тыс. треуг.,
`export_all_vertex_colors=False` и без цветов вершин в материале, без shape keys (E `../08-export-gltf/04` §7) [вывод F1].

### 2.3. iOS Quick Look

- Ссылка `<a rel="ar" href="product.usdz"><img src="poster.webp" alt="…"></a>` — Safari открывает Quick Look; параметры во фрагменте:
  `#allowsContentScaling=0`, `callToAction=…&checkoutTitle=…&price=…` (баннер действия), `custom=…&customHeight=large` [документация:
  галерея Apple AR Quick Look через F1-sub-AR §3].
- visionOS 26: элемент `<model>` в Safari [документация: там же]. Требования Apple к USDZ (UsdPreviewSurface, размеры) — не прочитаны
  [не проверено].

### 2.4. USDZ из Blender 5.2.2

Параметры оператора — из самого Blender 5.2.2 (`bpy_probe.py op wm.usd_export`, 69 параметров, работает в фоне):

| параметр | умолчание | для AR |
|---|---|---|
| `filepath` | — | путь с расширением `.usdz` → пакет USDZ |
| `selected_objects_only` | False | False + отдельная сцена/коллекция |
| `export_materials` / `generate_preview_surface` | True / True | True / True (UsdPreviewSurface — то, что читает Quick Look) |
| `generate_materialx_network` | False | False |
| `export_textures_mode` | `NEW` (`KEEP`, `PRESERVE`) | `NEW` — текстуры в пакет |
| `usdz_downscale_size` | `KEEP` (`256`…`4096`, `CUSTOM`) | `2048` (или `1024`) |
| `export_subdivision` | `BEST_MATCH` (`IGNORE`, `TESSELLATE`) | `TESSELLATE` — геометрия как в рендере |
| `evaluation_mode` | `RENDER` (`VIEWPORT`) | `RENDER` (у glTF-экспортёра — уровень вьюпорта, E 01 §4.6) |
| `convert_orientation` + `export_global_forward_selection` / `…_up_selection` | False, `NEGATIVE_Z` / `Y` | True, `NEGATIVE_Z`, `Y` — Y-up |
| `convert_scene_units` / `meters_per_unit` | `METERS` / 1.0 | метры |
| `export_animation`, `export_shapekeys`, `export_armatures` | False, True, True | по задаче |
| `export_lights`, `export_cameras` | True, True | False |
| `root_prim_path`, `xform_op_mode` | `/root`, `TRS` | как есть |

`visible_objects_only` и `export_textures` в 5.2.2 нет (есть в старых примерах) — модель по памяти получит `TypeError` [проверено: bpy_probe].

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/F1/06-doc-snippets (куб с Principled и картинкой → .usdz, пакет читается pxr)] USDZ для AR Quick Look
import bpy, os

def export_usdz(path, **overrides):
    kw = dict(selected_objects_only=False, export_animation=False, export_materials=True, generate_preview_surface=True,
              export_textures_mode="NEW", usdz_downscale_size="2048", export_subdivision="TESSELLATE", evaluation_mode="RENDER",
              convert_orientation=True, export_global_forward_selection="NEGATIVE_Z", export_global_up_selection="Y",
              convert_scene_units="METERS", export_lights=False, export_cameras=False)
    kw.update(overrides)
    valid = {p.identifier for p in bpy.ops.wm.usd_export.get_rna_type().properties}
    bad = [k for k in kw if k not in valid]
    if bad:
        raise KeyError(f"нет параметров {bad} в wm.usd_export этой версии")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return bpy.ops.wm.usd_export(filepath=os.path.abspath(path), **kw)
```

Что переживает экспорт — проверено на уровне пакета (куб 0,2 × 0,2 × 0,6 м, высота по Z Blender, Principled с картинкой): `FINISHED`,
62,7 КБ; внутри `tall_box.usdc` и `textures/uvgrid_512.png` (текстура упакована); `upAxis = Y`, `metersPerUnit = 1`, габарит в USD
0,2 × 0,6 × 0,2 — высота стала осью Y; материал — `UsdPreviewSurface` + `UsdUVTexture` + `UsdPrimvarReader_float2`
[проверено: 99-raw/experiments/F1/06-doc-snippets, чтение `pxr` из Blender 5.2.2]. Вид в Quick Look без Mac/iPhone проверить нельзя
[не проверено]; сложные ноды Principled (процедуры, coat, transmission) в UsdPreviewSurface не проверялись — запекать, как для glTF. Альтернатива без Blender — USDZ из того же GLB через three `USDZExporter` (как делает model-viewer): `maxTextureSize`
1024 по умолчанию, `quickLookCompatible` false, клипы анимации поддержаны в r186 (в model-viewer 4.3.1 с three 0.183 — «animations are
not yet supported»), KTX2-текстуры — через `setTextureUtils(WebGLTextureUtils)` [проверено: F1/01 исходник; документация: F1-sub-AR §1].
Прочитать USDZ в three — `USDLoader` (`.usdz`, `.usda`, `.usdc`) [проверено].

## 3. Текстурный конвейер KTX2

### 3.1. Замер на одной модели (F1/03: Camera_01, 9 карт 1024² PNG, meshopt; Chromium, Iris Xe → BC7)

| вариант | GLB | кодирование | тёплая загрузка ×1 / CPU ×4 | 1-й кадр ×1 / ×4 | GPU текстуры | ΔE2000 к PNG (ср. / p95) |
|---|---|---|---|---|---|---|
| PNG | 9 370 КБ | — | 193 / 547 мс | 127 / 352 мс | 48 МБ | — |
| WebP q80 | **940 КБ** | 1,3 с | 100 / 228 мс | 95 / 206 мс | 48 МБ | 0,10 / 0,55 |
| AVIF q60 | **828 КБ** | 14,2 с | 85 / 256 мс | 93 / 229 мс | 48 МБ | 0,08 / 0,51 |
| KTX2 ETC1S (умолчания) | 1 157 КБ | 2,6 с | **64 / 172 мс** | **82 / 108 мс** | **12 МБ** | 0,25 / 1,50 |
| KTX2 ETC1S `--quality 255 --compression 4` | 1 770 КБ | 9,8 с | 102 / 205 мс | 58 / 83 мс | 12 МБ | 0,24 / 1,48 |
| ETC1S цвет + UASTC данные без RDO | 6 048 КБ | 5,9 с | 216 / 440 мс | 45 / 107 мс | 12 МБ | — |
| ETC1S цвет + UASTC RDO (нормали λ 0,25, ORM λ 0,5) | 5 601 КБ | **139 с** | 242 / 581 мс | 61 / 122 мс | 12 МБ | 0,20 / 1,14 |

[проверено: 99-raw/experiments/F1/03-ktx2-webp; ΔE по всему кадру, модель ≈ 40 % — абсолютные значения занижены, ранжирование верно].
Первая загрузка KTX2 — +транскодер: холодная 919 мс против 64 мс тёплой (скачивание 212 КБ wasm) [проверено]. В hero на
медленном 4G (512²): KTX2 7,1 с до первого кадра против 5,2 с у WebP [проверено: hero-lazy].

### 3.2. Какой формат когда

| ситуация | формат | почему |
|---|---|---|
| телефон, одна модель, карты ≤ 512² | WebP q80 | нет транскодера (−204 КБ br), GPU 512² × 9 ≈ 12 МБ и так мало |
| телефон, карты 1024²+ или несколько моделей | KTX2 ETC1S (+ ресайз) | память ×4 меньше, первый кадр при CPU ×4 быстрее вдвое |
| десктоп, детальный продукт 1–2k | KTX2 ETC1S; нормаль крупного плана — UASTC | память, мягкие блики |
| десктоп, одна простая модель | WebP | меньше байт, память не критична |
| запечённый свет (плавные градиенты) | WebP q85+ или UASTC | ETC1S полосит на градиентах (E 03 §3.6) [не проверено на картах света] |
| AR (Scene Viewer) | JPEG/PNG ≤ 2048² | KTX2/WebP не заявлены (§2.2) |
| картинки-кадры, постеры | AVIF + WebP (`<picture>`) | для рендеров с альфой AVIF вдвое меньше (A/06); для текстур glTF — WebP (кодирование AVIF ×11) |

[проверено: F1/03, hero-lazy, A/06, E/18].

### 3.3. Команды

```bash
# gltf-transform 4.5.0 + toktx 4.4.2 (PATH), gltfpack 1.2 нативный — [проверено]
R=$DDD_HOME
export PATH="$R/bin/KTX-Software-4.4.2-Linux-x86_64/bin:$R/bin/gltfpack-1.2:$PATH"
cd $R/node
npx --no-install gltf-transform etc1s in.glb etc1s.glb                         # всё ETC1S: q128, compression 1, RDO — умолчания
npx --no-install gltf-transform uastc etc1s.glb out.glb --slots "normalTexture" --rdo --rdo-lambda 0.25 --rdo-dictionary-size 65536 --zstd 22
npx --no-install gltf-transform meshopt out.glb final.glb                      # геометрия: квантование + meshopt
gltfpack -i in.glb -o mobile.glb -cc -tc -ts 0.5                               # одной командой: meshopt + ETC1S + ресайз ×0,5 (вход — JPEG/PNG!)
npx --no-install gltf-transform webp in.glb webp.glb --quality 80               # WebP-вариант для телефона
```

Соответствие флагов (KTX Artist Guide → gltf-transform): `--clevel` → `--compression` (0–5, умолч. 1), `--qlevel` → `--quality`
(1–255, умолч. 128), `--uastc_quality` → `--level` (0–4, умолч. 2: 47,47 дБ), `--uastc_rdo_l` → `--rdo-lambda`, `--uastc_rdo_d` →
`--rdo-dictionary-size`, `--zcmp` → `--zstd` (умолч. 18); цветовое пространство (`--assign_oetf`) gltf-transform ставит сам по слоту
[проверено: справка CLI 4.5.0 в F1/03]. Источник — PNG, не JPEG (артефакты JPEG усиливаются блочным сжатием); размеры кратны 4;
≤ 2048 для веба; ORM можно в ¼ площади цвета [документация: KTX Artist Guide через E 03 §3.4–3.5].

### 3.4. Во что превращается KTX2 на устройстве

`KTX2Loader` r186 выбирает формат GPU: ETC1S → ETC2 → ETC1 → BC7 → BC1/BC3 → PVRTC → RGBA32; UASTC → ASTC 4×4 → BC7 → ETC2 → … →
RGBA32; на Linux с Mesa отключает ETC/ASTC (драйвер их эмулирует) — все наши замеры = BC7 (1 Б/пикс.); на Android ETC1S → ETC1/ETC2
(0,5 Б/пикс. для RGB) [документация: исходник KTX2Loader через E 03 §3.1]. Новые кодеры Basis (ASTC 12×12, XUASTC) `KTX2Loader` r186
не читает [документация: W7 §8 → V:3YP5Ck-7NZk 27:17]. UASTC без ASTC/BC7 (старые телефоны) транскодируется в несжатый RGBA —
выигрыш памяти пропадает [документация: KHR_texture_basisu через E]. Basis в продакшене у Esri — память клиента −60 % и больше
[V:3YP5Ck-7NZk 23:25]; 2K WebP в GPU 22,4 МБ против 2,8 МБ у KTX2 [V:BH1R29YvLOk 36:16].

## 4. WebGPU/TSL: что меняется для GLB из Blender

| тема | `WebGPURenderer` r186 | источник |
|---|---|---|
| материалы GLTFLoader | `MeshStandard/Physical/Basic` → node-материалы автоматически (NodeLibrary), картинка совпадает с WebGL | [проверено] |
| свой шейдер | `ShaderMaterial`, `onBeforeCompile` — нет; TSL (`colorNode`, `positionNode`, `Fn`) — один код на WebGPU и WebGL2 | [проверено: A/08; документация] |
| lightMap, aoMap, transmission | поддержаны в node-материалах | [проверено: F1/01 исходник] |
| тени | `PCFShadowMap` по умолчанию, `PCFSoftShadowMap` удалён (warn) | [проверено] |
| постобработка | `RenderPipeline` (r183) + TSL-узлы; pmndrs `postprocessing` — нет | [документация: A 03 §3.3] |
| фон | сплошной `scene.background` тонмаппится (в WebGL — нет) → прозрачный canvas | [проверено] |
| `renderer.info` | `render.calls` накопительный, за кадр — `frameCalls` | [проверено] |
| KTX2 | `await renderer.init()` до `KTX2Loader.detectSupport(renderer)` | [документация: Migration Guide r181] |
| MSAA | в compat mode (старые Android) выключен (`_samples = 0`) | [документация: W7 §8] |
| лимиты | не запрашивать функций/лимитов сверх умолчаний; `powerPreference` на Windows игнорируется | [V:3YP5Ck-7NZk 34:13, 40:25] |
| сплаты | `GaussianSplat`, `GLTFGaussianSplatLoaderExtension` (`KHR_gaussian_splatting`) — только WebGPU | G `../10-ai-3d-generation-assets/`; A 03 §9 |
| первый кадр | 922 мс против 1353 у WebGL; откат на WebGL2 — 2299 мс, TBT ×1,6 | [проверено] |

Код рендерера — `01` §2.1 (`createWebGPURenderer`); `loadGLB` из `01` §3.2 работает на WebGPU-странице без правок, если import map
переназначает `"three"` на `three.webgpu.js` (addons импортируют `"three"`) [проверено: F1/05 — та же схема импорта].

## Частые ошибки

1. Секвенция: все 200 кадров в памяти (≈ 900 МБ декодированных) — вкладка падает на телефоне [расчёт; практика: A 01 §14].
2. Видео с альфой только VP9 (в Safari прозрачности нет) или только HEVC (в Chrome нет) [практика: A 05].
3. Stacked-альфа с `SRGBColorSpace` на текстуре — маска «линеаризуется», края темнеют; с `colorspace_fragment` — двойной перевод [проверено].
4. Точки/пути в осях Blender (Z-up) — всё «лежит на боку» [практика: A 05].
5. Один GLB для веба и AR: Meshopt/KTX2 в `src` model-viewer уходят в Scene Viewer [документация].
6. model-viewer в одном бандле с three r186 — конфликт peer ^0.183 [проверено: A].
7. USDZ по памяти: `visible_objects_only=True`, `export_textures=True` → `TypeError` в 5.2.2 [проверено: bpy_probe].
8. KTX2 из WebP-входа в gltfpack `-tc` — картинки остаются WebP, а файл требует `KHR_texture_basisu` [проверено].
9. UASTC «для качества» на всех картах — 5–6 МБ вместо 1,2 [проверено].
10. `WebGPURenderer` без `await init()` перед `KTX2Loader.detectSupport` [документация].
11. Шейдер через `onBeforeCompile` на WebGPU-странице — не применится; TSL [документация].

## Чек-лист

- [ ] Секвенция: окно ≤ 12–20 кадров, телефонный набор, `close()` вне окна, reduce — один кадр?
- [ ] Видео с альфой: HEVC + VP9 или stacked; петля > 5 с — пауза; постер?
- [ ] Точки/пути/маркеры — в осях three, формат согласован (D1), имена без точек и пробелов?
- [ ] AR-GLB отдельный: без Meshopt/Draco/KTX2/WebP, ≤ 100 тыс. треуг., ≤ 2048², без морфов и цветов вершин, ≤ 10 МБ?
- [ ] `ios-src` задан (USDZ из Blender или `USDZExporter`), кнопка AR подписана словами?
- [ ] Текстуры: формат по таблице §3.2, KTX2 из PNG, размеры кратны 4, транскодер на своём домене?
- [ ] WebGPU только ради compute/сплатов/TSL; откат проверен; фон — прозрачный canvas?

## Открытые вопросы и противоречия

- Scene Viewer и сжатие: документация Google (2024-10-31) не упоминает Draco/Meshopt/KTX2, intent версии 1.2 (её шлёт model-viewer) не
  описан; практика Scene Viewer с Draco не проверена (нет Android с ARCore) [спорно].
- USDZ из Blender 5.2.2 в Quick Look — не проверен (нет Mac/iPhone); проверена только структура пакета.
- Anim-USDZ: `USDZExporter` r186 умеет клипы, model-viewer 4.3.1 (three 0.183) заявляет «not yet supported» — поведение Quick Look с
  клипами не проверено.
- KTX2 на телефонах (ETC/ASTC) — не мерилось; все числа — BC7 на Linux/Mesa (как у E).
- UASTC RDO: выигрыш −7 % при λ 0,25/0,5 — на картах высокой частоты (Camera_01); на плавных картах (свет, градиенты) выигрыш может быть
  больше — не проверено.
- Merchant «4K лучше» против Scene Viewer 2048² — противоречие документов Google (A, E, F1-sub-AR).

## Источники

- [S1] Эксперименты F1: `99-raw/experiments/F1/01-package-facts` (USDLoader/USDZExporter, KTX2Loader, NodeLibrary), `03-ktx2-webp`,
  `05-webgl-webgpu`, `06-doc-snippets`; демо `examples/hero-lazy` — [проверено].
- [S2] `../../scripts/3d/bpy_probe.py op wm.usd_export` на Blender 5.2.2 — 69 параметров оператора с умолчаниями — [проверено].
- [S3] model-viewer 4.3.1: modelviewer.dev/docs (снимок 22.09.2026), /examples/augmentedreality/, /examples/loading/, FAQ; исходник
  `src/features/ar.ts`, `constants.ts`, `three-components/ARRenderer.ts` @1685fd04; npm (через `99-raw/notes/wave2/F1-sub-AR.md`) — [документация].
- [S4] Google ARCore, «Scene Viewer» (developers.google.com/ar/develop/scene-viewer, обновл. 2024-10-31) — требования, intent, коды валидатора — [документация].
- [S5] Apple, AR Quick Look gallery (developer.apple.com/augmented-reality/quick-look/) — `rel="ar"`, параметры фрагмента, `<model>` — [документация, неполно].
- [S6] Google Merchant Center 13674896, 13675100; DV360 9794085 — 3D-товары, лимиты — [документация].
- [S7] A, волна 1: `../01-web-3d-landscape/05-blender-deliverables-map.md` §1–4, A/06 (`playback.html`, размеры поставок) — [проверено A].
- [S8] E, волна 1: `../08-export-gltf/03-compression-textures-budgets.md` §3–4 (KTX Artist Guide, KTX2Loader, gltfpack, E/18, E/24) — [проверено E].
- [S9] gltf-transform 4.5.0 CLI (`etc1s --help`, `uastc --help`) — флаги и умолчания — [документация].
- [S10] W7, `99-raw/reports/wave2-W7-report.md` §4, §8 → F1: compat mode и MSAA, ASTC 12×12/XUASTC, лимиты [V:3YP5Ck-7NZk] — [V].
- [S11] Доклады через `F1-sub-core.md`: [V:3YP5Ck-7NZk] Khronos 2026 (Basis −60 % памяти), [V:BH1R29YvLOk] Самокат (2K WebP 22,4 МБ против 2,8) — [практика].
- [S12] J. Archibald, «Video with alpha transparency on the web», 2024 (через A 05) — форматы альфа-видео — [практика].