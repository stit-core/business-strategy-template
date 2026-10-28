# 09 · Веб-рантайм: three.js r186, R3F и другие движки — от GLB из Blender до кадра на странице

Волна 2 · агенты **F1** (ядро three, загрузка, цвет под Blender, производительность, доступность, запасные варианты, поставки
не-GLB, AR/USDZ, KTX2, WebGPU) и **F2** (R3F и другие движки, прокрутка и интерактив, шейдеры и каталог эффектов) · 23.09.2026 ·
версии: three 0.186.0, R3F 9.x + drei 10.x, model-viewer 4.3.1, Blender 5.2.2, Chromium (Playwright) · эксперименты:
`../99-raw/experiments/F1/` (01–06), `../99-raw/experiments/F2/` · заметки: `../99-raw/notes/wave2/F1-notes.md`, `F2-notes.md`.

| файл | агент | строк | о чём |
|---|---|---|---|
| `01-threejs-core.md` | F1 | 590 | импорт (бандлер против import map; ловушка jsDelivr `*.min.js`), `WebGLRenderer` против `WebGPURenderer` (замер первого кадра и отката), загрузка GLB одним запросом с декодерами по `extensionsUsed`, `compileAsync` (что он делает на самом деле), окружение, пара тонмаппинга под Blender (Neutral), материалы (lightMap, AO, transmission), тени, постобработка кратко, память и `dispose`, resize/DPR, поиск узлов, таблица «почему блёкло» |
| `02-r3f-drei-and-other-engines.md` | F2 | 415 | R3F 9.8 + drei 10.7.8: выбор против vanilla (чанк 293 КБ br, TBT ×2–3), дефолты `<Canvas>` (ACES → Neutral, DPR 1,5), `frameloop="demand"` и reduce, `useFrame` + `damp`, события и имена узлов, `useGLTF` = загрузчик three-stdlib (ловушка `KHR_meshopt_compression`), компоненты drei для лендинга, gltfjsx; эталон R3F-hero; model-viewer, Babylon, PlayCanvas (проверен), Needle, Spline; «живое превью» Blender ↔ R3F |
| `03-scroll-interaction-animation.md` | F2 | 397 | ScrollTrigger + Lenis → прогресс → `damp` → рендер по требованию (0 вызовов в покое), лицензия GSAP дословно, CSS scroll-driven и `ScrollTimeline` (поддержка, запас), путь камеры из Blender (кривая → JSON → `CatmullRomCurve3`), скраббинг клипа (`paused` + `setTime` не работает — что работает), hover по именам узлов, курсор, reduce по каждому приёму, физика |
| `04-shaders-effects-catalog-impl.md` | F2 | 457 | 17 вариантов эффектов каталога A с замером (вызовы, мс/кадр, fps без vsync): mesh gradient (фрагментный, вершинный Stripe, Paper Shaders), SDF ½/полное, стекло (transmission, scale 0,5, подделка), частицы с поверхности модели, шумовой блоб, дисторсия картинки, SDF-текст troika, контур hull против `OutlinePass`, matcap, пост pmndrs против CSS; цвет uniform против hex (ΔE 9,55 без `colorspace_fragment`) |
| `05-performance-a11y-fallbacks.md` | F1 | 407 | бюджеты телефона/десктопа с замером hero-lazy, наборы ассетов по устройству, detect-gpu, подстройка DPR, цикл «только когда нужен» (код), инстансинг и вызовы, доступность 3D (reduce, 2.2.2, 2.5.7, фокус), ожидание, запасные варианты, потеря контекста, **ворота публикации** с `gate_check()` по отчёту `site_probe.py` |
| `06-deliverables-ar-ktx2-webgpu.md` | F1 | 443 | загрузчики поставок не-GLB (секвенция с окном памяти, stacked-альфа, точки Float32, пути JSON, маркеры), AR (model-viewer, лимиты Scene Viewer, Quick Look), USDZ из Blender 5.2.2 (параметры и проверка пакета), конвейер KTX2 (замер WebP/AVIF/ETC1S/UASTC±RDO), особенности WebGPU для GLB |
| `page-3d-gates.yaml` | — | 91 | пороги ворот страницы с 3D для `../../../scripts/3d/gate_check.py`: LCP-элемент не canvas, 3D-ассеты, вызовы и DPR, первый кадр 3D, ошибки консоли, reduce, вклад 3D в TBT (прогон `site_probe.py --no-3d`); метрики страницы (LCP, CLS, TBT, вес) — зеркало строк site `page-gates.yaml`; описание — `05` §7.2 |
| `examples/hero-lazy/` | F1 | — | эталон hero: постер из того же GLB → 3D после LCP, наборы телефон/десктоп, reduce, стоп вне экрана, пауза; замеры `site_probe.py` |
| `examples/r3f-hero/`, `camera-path-scroll/`, `shader-background/` | F2 | — | R3F-hero (Lightformer, ContactShadows `frames={1}`, reduce → `demand`; 293 КБ br), путь камеры и клип сборки из Blender на прокрутке (GLB 33 КБ, JSON 2,7 КБ, hover по именам, 0 вызовов в покое, 60 fps), шейдерный фон в 4 вариантах (1 вызов, 1,45 мс) — README с замерами `web_view.py --page` и `fx_probe.py` |

## Выжимка папки (15 строк: 1–10 — F1, 11–15 — F2)

1. **Стек по умолчанию для модели GLB** (форма из правил, свет, частицы и миры — свой движок, `../16-js-scenes/`; дорога — `../README.md §Что брать`): `WebGLRenderer` + `GLTFLoader` (Meshopt; KTX2/Draco по `extensionsUsed`) + бандлер на своём домене — JS 174 КБ br, three готов за 2,0 с на эмуляции Pixel 7 против 3,8 с у import map с CDN (`01` §1).
2. **Постер из того же GLB — LCP; 3D после `load` в простое**: hero-lazy — LCP 52 / 460 мс, TBT 175 / 280 мс, первый кадр модели 0,63 / 5,2 с, reduce — 0 вызовов (`examples/hero-lazy`, `05` §6).
3. **Пара цвета**: Blender «Khronos PBR Neutral» ↔ `NeutralToneMapping`, `toneMappingExposure = 2^E`, unlit — `toneMapped = false`; AgX three светлее на 3,4–3,7 L* (`01` §5, D2 `../06-materials-lighting-render/03`).
4. **`compileAsync` не лечит TBT** (синхронный `compile()` внутри), а убирает тяжёлый первый кадр (14 против 541 мс) (`01` §3.4).
5. **WebGPU — не для hero**: первый кадр не хуже WebGL (922 / 1353 мс), но откат на WebGL2 — 2299 мс и TBT ×1,6; фон `scene.background` на WebGPU тонмаппится (`01` §2, `06` §4).
6. **KTX2 — память и CPU, не байты**: 1k-набор ETC1S 1,16 МБ (WebP 0,94), GPU 12 МБ (48), первый кадр при CPU ×4 108 мс (206); на медленной сети с 512² телефону — WebP (`06` §3).
7. **Цикл только при видимости, открытой вкладке и без reduce**, статичное — кадр по требованию; автодвижение > 5 с — кнопка паузы (WCAG 2.2.2) (`05` §3, §5).
8. **AR — отдельный несжатый GLB** (Scene Viewer знает только unlit и texture_transform) + `ios-src`; USDZ из Blender 5.2.2 — `wm.usd_export`, Y-up, UsdPreviewSurface (`06` §2).
9. **Поставки не-GLB**: секвенция с окном памяти (кадр 1080² = 4,5 МБ), stacked-альфа без sRGB-декодирования, точки и пути — в осях three (`06` §1).
10. **Ворота публикации** — `site_probe.py` (десктоп, Pixel 7 CPU ×4, reduce) + `gate_check()`; первый кадр модели — меткой страницы, не первым draw call (`05` §7).
11. **React есть → R3F 9.8 + drei 10.7.8 отдельным чанком после LCP** (293 КБ br; `gl={{ toneMapping: NeutralToneMapping }}`, `dpr={[1, 2]}` под бюджетом пикселей `../16-js-scenes/01-engine.md` §6.1, reduce → `frameloop="demand"`); drei `useGLTF` грузит three-stdlib — без `KHR_meshopt_compression` (`02` §1–4).
12. **Прокрутка даёт только прогресс**: ScrollTrigger (+ Lenis) → ref → `MathUtils.damp` в цикле → кадр только при изменении (0 вызовов в покое); `lerp(k)` без dt на 144 Гц в 2,4 раза быстрее (`03` §2, §4).
13. **Путь камеры и клип — из Blender**: кривая → JSON `[x, z, −y]` → `CatmullRomCurve3`; клип — `play()` + `setTime(p · (duration − 1e-4))`, `paused = true` клип не двигает (`03` §5–6, H `../07-animation/03` §3).
14. **Шейдерный фон — 1 вызов, ≈ 1,5 мс**, цвета бренда — `THREE.Color` + `#include <colorspace_fragment>` (без него ΔE 9,55), DPR ≤ 1, SDF — ½ разрешения (×6,6 дешевле) (`04` §2).
15. **Стекло transmission +1 проход (scale 0,5 −20 %), фон для преломления — в сцене; контур hull в 2,3 раза дешевле `OutlinePass`; зерно и виньетка — CSS** (`04` §3, §8, §9).

Код всех блоков F1 исполнен в напечатанном виде: **JS 15/15, Python 2/2** (`../99-raw/experiments/F1/06-doc-snippets`). Блоки F2 (`02`–`04`): **22 из 22 исполняемых — ok** (JS/JSX/CSS/HTML 21 на тестовых страницах, Python 1 в Blender 5.2.2), 1 блок
`[не проверено]` (Babylon) — `../99-raw/experiments/F2/09-doc-blocks`. Ограничение обоих: реальные телефоны не мерились (эмуляция Chromium на Intel Iris Xe).
