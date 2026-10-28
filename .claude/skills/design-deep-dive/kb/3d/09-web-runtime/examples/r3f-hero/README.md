# r3f-hero — эталон hero-сцены для React-проекта (R3F 9.8 + drei 10.7.8 + three r186)

Агент F2, волна 2, 23.09.2026. Эксперимент и сырые замеры: `../../../99-raw/experiments/F2/02-r3f-hero/`.

| Файл | Что |
|---|---|
| `index.html` | HTML-первый экран (H1, текст, CTA), место под 3D с `aspect-ratio` и CSS-градиентом-запасом; чанк `hero.js` грузится динамическим `import()` по `IntersectionObserver` + `requestIdleCallback` после `load` |
| `src/Hero.jsx` | сцена: `useGLTF` + `<Center>`, `<Environment>` из `<Lightformer>` (0 КБ файлов), `<ContactShadows frames={1}>`, `<Float>`, `<PresentationControls snap>`, `NeutralToneMapping`, `dpr={[1, 1.5]}`, reduce → `frameloop="demand"` и выключенные Float/контролы, стоп вне экрана (`setFrameloop('never')`) |
| `hero.js` | собранный чанк (esbuild 0.28, `--minify`): 1290 КБ min, 362 КБ gzip, **293 КБ br** |
| `sculpture.glb` | модель из `99-raw/experiments/C1/15-export-compress/sculpture_opt.glb` (63 КБ, `EXT_meshopt_compression`, 14 138 треуг.) |
| `build.sh` | пересборка: `NODE_PATH=<песочница>/node_modules npx esbuild src/Hero.jsx --bundle --minify --format=esm --jsx=automatic` |

Запуск: `python3 -m http.server` в папке → `http://localhost:8000/`. Проверка:
`python3 ../../scripts/3d/web_view.py --page 09-web-runtime/examples/r3f-hero/index.html OUT --scroll 0,0.5,1 --wait 12000`.

## Замеры (Chromium 153 headless, Intel Iris Xe, ANGLE GL; локальный сервер без сжатия)

| Режим | Первый кадр с draw call | Вызовов/кадр в покое | Движение в покое | Мс/кадр GPU (bench, readPixels) | TBT | Прочее |
|---|---|---|---|---|---|---|
| `web_view.py --page` 1440×900 | — | 3 (прокрутка, 60 fps, p95 16,8 мс) | — | — | 757 мс (4 долгие задачи) | LCP 156 мс = текст, CLS 0, heap 10 МБ |
| desktop (`fx_probe.py`) | 666 мс | 3 | 0,5 % (Float) | 2,05 (880×550) | 496 мс | canvas 880×550, DPR 1 |
| mobile Pixel 7 + CPU×4 | 1 115 мс | 3 | 0,7 % | 1,74 (568×355) | 765 мс | canvas 568×355 при CSS 379×237 → **DPR 1,5** |
| reduce | 610 мс | **0** | **0 %** | — | 289 мс | `frameloop="demand"`, Float и контролы выключены |
| uncapped (без vsync) | 560 мс | 3 | — | 0,81 | 360 мс | 2 325 fps в покое → ≈ 0,43 мс на кадр сцены |

- Консоль: 0 ошибок; 1 предупреждение `THREE.Clock: This module has been deprecated` — внутри R3F 9.8 (`state.clock`), не код страницы.
- `gl.toneMapping` = 7 (`NeutralToneMapping`) — проп `gl={{ toneMapping }}` перекрывает ACES по умолчанию у R3F.
- Сравнение с vanilla-паттерном A/07 (three r186, 7 тыс. треуг.): TBT 172 / 369 мс (десктоп / CPU×4) против 496–757 / 765 мс здесь — цена React + R3F + drei (1,3 МБ JS до сжатия) на главном потоке.
- Ловушка (проверено): `gltfpack -cc -ce khr` пишет `KHR_meshopt_compression`, drei `useGLTF` (загрузчик three-stdlib 2.36.1) падает: «Could not load …: Invalid typed array length: 28800»; тот же файл с `EXT_meshopt_compression` (умолчание gltfpack 1.2) грузится; three r186 `GLTFLoader` читает оба.

Скриншоты: `99-raw/experiments/F2/02-r3f-hero/out/hero2_desktop_0.png` (десктоп), `hero_mobile_0.png`, `hero_reduce_0.png`.
