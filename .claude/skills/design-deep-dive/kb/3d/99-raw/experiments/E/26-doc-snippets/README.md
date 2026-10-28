# E/26 — блоки кода итоговых файлов 08-export-gltf/01…04, прогнанные ровно в напечатанном виде

Цель: код в итоговых файлах работает с первого запуска в Blender 5.2.2 и three r186.
Команды:
    python3 ../../scripts/3d/blender_run.py 99-raw/experiments/E/26-doc-snippets/snippets.py     # Python-блоки + assert по JSON glTF → result.json, out/*.glb (0.9 с)
    python3 99-raw/experiments/E/26-doc-snippets/js_check.py                                  # JS-блоки на three r186 (Chromium) → js_result.json
Проверено (все assert прошли):
- WEB-набор параметров + export_web(); жёсткие рёбра `mesh.set_sharp_from_angle(30°)` без модификатора → 130 вершин,
  34 уникальные нормали (как E/03 c07);
- pbr_material(): baseColorTexture, metallicRoughnessTexture и occlusionTexture — одна текстура (ORM), normalTexture.scale 0.8;
- alpha_from_texture(): MASK с alphaCutoff 0.3 (1 − (a < 0.3)); BLEND; glass_material(): transmission + volume + ior 1.45 +
  dispersion 0.3; unlit_material(): KHR_materials_unlit;
- vertex_color_material() при двух цветовых атрибутах и export_all_vertex_colors=False: COLOR_0 = реальные цвета
  (min/max 1/0.2/0.1…1/0.8/0.1), COLOR_1 нет; add_float_attribute(): _WAVE (−0.5…0.5);
- gn_scatter_object() + export_gn_mesh + export_gpu_instances: 1 узел, EXT_mesh_gpu_instancing, 100 экземпляров
  (предупреждение «Mesh 'Scatter' has no primitives» — базовый меш пуст, это норма);
- stash_action(): два клипа Jump и Slide; extras {hotspot: "buy", price: 199};
- свет COMPAT: солнце 3 Вт/м² → directional 3; точка 50 Вт → 3.979 (50/4π).
JS (js_result.json): загрузчик с DRACOLoader/KTX2Loader/MeshoptDecoder; getObjectByName('hero_orb') → Mesh, userData
{name, hotspot, price}; «Cube.001» → 'Cube001', поиск по userData.name работает; AnimationClip.findByName → клипы Jump 1.967 с,
Slide 1.967 с; mixer.update(duration/2) → y = 0.998 (вершина прыжка); geometry.attributes._wave itemSize 1.
Версии: Blender 5.2.2, glTF-IO 5.2.40, three 0.186.0 (jsDelivr), Chromium (Playwright).

## E/26b — блоки из самих .md (run_md.py)
`python3 md_blocks.py 08-export-gltf/0N-….md blocks_0N.json` извлекает блоки ```python по порядку; `run_md.py` (Blender, 5.4 с)
исполняет их без правок (пути `/abs/...` → временная папка) и прогоняет сценарии с assert: процедурный материал → bake_pbr_maps →
baked_material → glTF (baseColor + MR + normal); AO → occlusionTexture и COLOR_0; свет → bake_to → unlit с texCoord 1; HDR-фрагмент
(.hdr и PNG ×0.25 записаны); denoise; high→low нормаль (синий канал ≈ 0.86); METALLIC через EMIT (39.6 % металла) → pack_orm;
применение модификаторов. Результат: все 11 блоков 01 и 13 блоков 02 — ok (result_md.json). После правки .md — перезапуск обоих скриптов.

## E/26c–d — preflight(), glb_lint() и блоки 04 (preflight_test.py, run_md04.py)
- `preflight_block.py` (= §5 файла 04): сцена с 20 заложенными проблемами → найдены все 20 кодов; чистая сцена → 0 WARN/ERROR.
- `glb_lint_block.py` (= §6 файла 04): на выходах E/24 и файлах E/14–E/26 (glb_lint_result.json): декодеры, вызовы по файлу,
  треугольники, память текстур (mobile_light 12.0 МБ, static_hero 192 МБ), предупреждения transmission и SPEC-света.
- `run_md04.py`: все 6 блоков ```python из 04 исполнены как напечатаны: recalc_normals_outside (512 граней внутрь → наружу),
  origin_to_bounds_and_apply_scale (центр габарита 0, масштаб 1), preflight, glb_lint, presets.py + примеры вызова
  (hero, коллекция WEB с анимацией → 1 узел и 1 клип, морфы, инстансы → EXT_mesh_gpu_instancing).
Transmission в three r186 (`build/three.module.js`, `renderTransmissionPass`): непрозрачные объекты рисуются повторно в цель
transmission — отсюда 8 вызовов и 53 974 треуг. у Camera_01 при 4 примитивах и 26 987 треуг. в файле (E/24).
