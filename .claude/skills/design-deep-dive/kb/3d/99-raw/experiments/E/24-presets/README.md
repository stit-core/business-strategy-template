# E/24 — пресеты экспорта для веба (Blender 5.2.2) + постобработка + валидатор + three r186

Цель: проверить сквозь всю цепочку шесть готовых наборов параметров `bpy.ops.export_scene.gltf` (presets.py) и команды
постобработки к ним.
Команды:
    python3 ../../scripts/3d/blender_run.py 99-raw/experiments/E/24-presets/export_all.py      # raw/*.glb, export_result.json
    python3 99-raw/experiments/E/24-presets/post_check.py                                  # post/*.glb, post_result.json (валидатор + three)
    python3 ../../scripts/3d/gltf_load_bench.py post/*.glb --json bench.json
Сцены: static_hero и mobile_light — Camera_01 (Poly Haven, 9 JPEG 2k); anim_trs — пьедестал + hero_orb (прыжок+поворот,
custom property hotspot) + вспомогательный куб в коллекции Helpers + объект с hide_render; anim_morph — сфера с 8 shape keys
(E/17 c4); anim_skin — колонна на арматуре из 2 костей (E/15 a17); instances — 100 GN-инстансов (E/08 g4) и 100 связанных
дубликатов (E/08 g7).
Результат:
| пресет | сырой GLB, КБ | постобработка | итог, КБ | валидатор | three r186 (проверено gltf_web_inspect) | загрузка тёплая, мс |
|---|---|---|---|---|---|---|
| static_hero | 6 049 | `gltf-transform optimize … --compress meshopt --texture-compress webp --texture-size 2048 --simplify false` | 2 452 | 0 ошибок, 3 warn (касательные) | 8 вызовов; **имена узлов потеряны** (join/flatten → «Mesh016») | 86 |
| anim_trs | 58 | `optimize … --flatten false --join false --simplify false` | 17.5 | 0 / 0 | клип hero_orbAction 1.97 с, 2 трека; userData {hotspot: "buy"}; guide_helper из Helpers попал | 1.8 |
| anim_trs + `collection="WEB"` | 57 | то же | 17 | 0 / 0 | только Pedestal и hero_orb (параметр collection работает при вызове из скрипта) | — |
| anim_morph | 1 104 | то же (meshopt сжимает морфы) | 301 | 0 / 0 | morphTargetDictionary Wave0…7, клип 3.97 с | 3.1 |
| anim_skin | 9.8 | то же | 5.9 | 0 / 1 warn (skinned mesh non-root) | SkinnedMesh + 2 Bone, клип 2.46 с, 6 треков | 1.5 |
| instances (GN) | 11.5 | то же | 8.6 | 0 / 0 | InstancedMesh ×100, 1 вызов | 1.6 |
| instances (связанные дубликаты) | 11.6 | то же | 6.3 | 0 / 0 | InstancedMesh ×100, 1 вызов | — |
| mobile_light (AUTO) | 6 049 | нативный `gltfpack -i IN -o OUT -cc -tc -ts 0.5` | **1 530** | 0 ошибок (warn: валидатор не знает image/ktx2) | KTX2 1024², GPU текстур **12 МБ** (против 192 МБ у hero); имена → mesh_0 | 33 (холодная 509 — wasm-транскодер) |
Находки:
- `export_apply=True` уничтожает shape keys только у объектов, у которых есть модификаторы (без модификаторов экспортёр берёт
  исходные данные, морфы сохраняются — проверено: anim_morph с apply=True → 8 морфов); E/07: Subdivision + apply → 0 морфов.
- Первый вариант mobile_light (export_image_format="WEBP" → gltfpack -tc) дал 2.43 МБ: **gltfpack -tc не перекодирует
  WebP-вход** (текстуры остались WebP), но объявил KHR_texture_basisu обязательным. Для KTX2 через gltfpack отдавать JPEG/PNG.
- `optimize` с квантованием добавляет дочерний узел под анимированным/родительским мешем (KHR_mesh_quantization: трансформ
  деквантования) — в three имя «hero_orb» у Object3D, а меш — «hero_orb_1»; искать меш через traverse.
- `optimize` по умолчанию (flatten+join) склеивает объекты и теряет имена — для адресуемых частей `--flatten false --join false`;
  gltfpack без `-kn` тоже переименовывает («mesh_0»).
Версии: Blender 5.2.2, glTF-IO 5.2.40, gltf-transform 4.5.0, gltfpack 1.2 (нативный), toktx 4.4.2, three 0.186.0.
