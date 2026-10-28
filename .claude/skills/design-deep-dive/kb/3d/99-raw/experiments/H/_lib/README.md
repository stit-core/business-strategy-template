# H/_lib — инструменты агента H (анимация)

| файл | что делает | пример |
|---|---|---|
| `animx.py` | помощники анимации 5.2 поверх bpyx: `key()` (keyframe_insert только именами), `fcurves()` (слот → channelbag), `set_interpolation()`, `add_cycles()`, `loop_range()` (ручной диапазон = клип), `new_action()` (одно действие со слотами на несколько ID), `assign()`, `stash()` (NLA-дорожка с одной полосой), `bake_visual()` (`anim_utils.bake_action_objects`), `export_glb()` (анимационный пресет с проверкой ключей по RNA), `anim_summary()` (клипы, каналы, ключи, байты данных из JSON GLB), `render_frames()` | `sys.path.insert(0, ".../H/_lib"); import animx` |
| `anim_diff.py` | анимация «Blender против three r186» в одни и те же моменты: рендер кадров EEVEE (общая камера по габаритам всех кадров или камера сцены), те же моменты в three (`action.time = (f − start)/fps; mixer.update(0)`), IoU / ΔE2000 / SSIM по кадрам (функции `gltf_diff.py`), лист Blender \| three \| ΔE | `python3 anim_diff.py scene.blend out/ --glb m.glb --frames 1,31,61 [--clip Reveal] [--scene-camera] [--mute-nla]` |
| `three_probe.py` | загрузить GLB в three r186 (Chromium, GPU) и выполнить JS-проверку (тело async-функции с THREE, gltf, scene, renderer) → JSON | `python3 three_probe.py m.glb check.js --out r.json` |
Кандидаты в `99-raw/tools/` (решение оркестратора/агента J). Проверено: Blender 5.2.2, three 0.186.0.
