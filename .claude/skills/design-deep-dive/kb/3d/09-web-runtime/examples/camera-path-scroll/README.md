# camera-path-scroll — путь камеры и клип из Blender на прокрутке (three r186 + GSAP ScrollTrigger + Lenis)

Агент F2, волна 2, 23.09.2026. Эксперимент: `../../../99-raw/experiments/F2/03-camera-path/` (замеры, скриншоты),
скраббинг и `damp` отдельно — `../../../99-raw/experiments/F2/06-anim-damp/`.

| Файл | Что |
|---|---|
| `build_scene.py` | Blender 5.2.2 (фон, `bpyx`): кривая Безье `cam_path` (5 точек, `resolution_u` 24) → `cam_path.json`; 6 колец-торов на пути (стоят на полу: центр = R + r), пустышки `hotspot_N` с `label` → `userData`; стопка из 5 плит (Bevel) с клипом сборки кадры 1–60 @30 fps; экспорт `export_yup`, `export_extras`, `ACTIVE_ACTIONS` (один клип «Animation»), `export_anim_slide_to_zero` |
| `cam_path.json` | 97 точек в осях three `[x, z, −y]`, метры, 2,7 КБ |
| `scene_opt.glb` | `gltfpack -cc -kn -ke`: 421 → **33 КБ**, 19 374 треуг.; имена и `userData.label` сохранены (без `-kn -ke` теряются — E/28) |
| `index.html` | three r186 (import map, jsDelivr) + GSAP 3.15 ScrollTrigger (только прогресс) + Lenis 1.3.26; камера `CatmullRomCurve3.getPointAt(u)`, взгляд — точка впереди, к концу — на стопку (`smoothstep`); прогресс сглаживается `MathUtils.damp(λ = 4)`; 78–100 % прокрутки — `mixer.setTime(p · (duration − 1e-4))`; hover — `Raycaster` по узлам `ring_N` (меш после квантования — ребёнок узла, подъём по `parent`), подпись из `userData`; рендер только при изменении (0 draw calls в покое); стоп вне экрана и в скрытой вкладке; reduce → 5 «станций» без пролёта, без параллакса и инерции, клип в конечной позе |

Пересборка: `python3 ../../scripts/3d/blender_run.py 09-web-runtime/examples/camera-path-scroll/build_scene.py -- OUT` →
`99-raw/tools/bin/gltfpack-1.2/gltfpack -i OUT/scene.glb -o scene_opt.glb -cc -kn -ke`.

## Замеры (Chromium 153 headless, Iris Xe, ANGLE GL; `fx_probe.py` и `web_view.py --page`)

| Режим | Вызовов/кадр в покое | Прокрутка: fps / вызовов (мед., макс.) / p95 кадра | Hover | Bench мс/кадр | TBT |
|---|---|---|---|---|---|
| `web_view.py --page` 1440×900 | — | 60 / 8, 11 / 16,7 мс | — | — | 323 мс; LCP 92 мс (текст), CLS 0, heap 10 МБ, 0 ошибок |
| desktop | **0** (движение 0 %) | 60 / 7, 12 / 16,8 мс | 12 | 2,96–3,89 (1440×900) | 405 мс |
| mobile Pixel 7 + CPU×4 | 0 | 59 / 3–4, 11 / 16,8 мс (1-й прогон 26 fps — нагрузка общей машины) | — | 8,5 (618×1258, DPR 1,5) | — |
| mobile без Lenis (`?nolenis`) | 0 | 59 / 4 / 16,8 мс | — | — | — |
| reduce | 0 | 60 / 0 (кадры только на смене «станции», 104 из 282) | 0 | — | 353 мс |
| uncapped | 0 | 200 (сколько прокрутка даёт кадров) | — | 3,07 | 373 мс |

Сеть: JS 515 КБ (13 модулей с jsDelivr, three `three.module.min.js`), GLB 32 КБ, JSON 2,6 КБ.
Найдено при проверке: (1) кольца с центром на высоте 1,2 м при радиусе 1,25 + 0,07 «проросли» в пол — на прокрутке низ кольца
выглядел как прямая хорда (ошибка M2.3 каталога C1) → центр = R + r; (2) конец пути в 1,2 м от стопки — камера упиралась в
модель → стопка отодвинута на 3,2 м (≈ 50 % высоты кадра при FOV 50°). Улучшить: мягкая тень под стопкой и кольцами
(запечь в Blender или `ContactShadows`-аналог), сейчас объекты выглядят слегка «парящими».
