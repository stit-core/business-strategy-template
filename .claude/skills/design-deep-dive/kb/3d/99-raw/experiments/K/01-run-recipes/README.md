# K/01 — сквозной прогон рецептов 12-recipes (Blender 5.2.2, three r186)

Цель: каждый рецепт исполняется в напечатанном виде от паспорта до GLB/рендера, затем валидатор и three в Chromium.
Команда: `python3 ../../scripts/3d/run_recipes.py 12-recipes/0[1-9]-*.md 12-recipes/1[0-2]-*.md` (2 мин 49 с).
Что делает: блоки ```python рецепта → `12-recipes/examples/<slug>/build.py` → `blender_run.py` (таймаут 600 с); блоки
`# run: system` → `post.py` → системный Python 3; для каждого `<name>.glb` (кроме `*_raw`, `*_ar`) — `gltf_check.py --json`
и `web_view.py` (Neutral, 4 вида) → `examples/<slug>/web/<name>/`.
Результат: `result.json` (финальный прогон: 11 рецептов с кодом — выход 0; system 2/2; 13 GLB — 0 ошибок валидатора);
`result_dev.json` — прогоны по ходу работы (с итерациями правки). Числа каждого рецепта — `examples/<slug>/numbers.json`.
Итерации правки, найденные прогоном: аудит до камеры (01), затирание чисел серии (02), габарит по цоколю (04), `ActionSlot.name`
(05), галька свисает с подставки и IOR 1,5 без `KHR_materials_ior` (09), пустой кадр у объекта с GN-инстансами (10).
Страницы и ворота: K/02 hero (gate_check 24/24), K/03 иконки, K/04 частицы (15/15), K/05 стекло (фон в сцене / прозрачный canvas),
K/06 инспекция инстансов (1 вызов), K/07 прокрутка, K/08 видео, K/09 model-viewer, K/10 шейдерный фон.
Версии: Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, gltfpack 1.2, three 0.186.0, model-viewer 4.3.1, ffmpeg 7.1, Chromium (Playwright).
