# Shape keys, простые риги, констрейнты и драйверы, запечённые симуляции: что доходит до веба и чего стоит

Волна 2 · агент H · 2026-09-23 · источников 11 (руководство и API Blender 5.2, исходники glTF-Blender-IO 5.2.40 и GLTFLoader r186,
Codrops 2025-08-20 и 2026-09-19, файлы волны 1 A и E, дайджест W4) · экспериментов 3 (`99-raw/experiments/H/13-morph`,
`14-camera-path`, `22-size-postprocess`) + блоки этого файла, выполненные в `99-raw/experiments/H/30-doc-snippets` · Blender 5.2.2 LTS,
glTF-IO 5.2.40, three r186.

## Выжимка для агента

1. **Морф в вебе = относительные shape keys + ключи их `value`**: экспортёр пишет `targets` (дельты позиций и нормалей) и
   `weights`, три получает `morphTargetInfluences` и `morphTargetDictionary` из `extras.targetNames`. → §1.1 [проверено]
2. **Формы задавай массивами**: `key.points.foreach_set("co", float32)` (5.x, быстрый путь); топология у всех форм одна. → §1.1 [проверено]
3. **Модификатор + `export_apply=True` = морфов 0, молча** (клип остаётся, целей нет). Морф-ассет: модификаторы применить ДО
   shape keys или экспортировать с `export_apply=False` (`bpyx.export_glb(apply_modifiers=False)`). → §1.2 [проверено]
4. **Вес морфа = вершины glTF × цели × 12 Б (+12 Б с нормалями)**: 2 737 вершин × 2 цели = 253 КБ с нормалями, 187,5 КБ без;
   Meshopt — 66 КБ, gltfpack `-cc` — 56 КБ. → §1.3 [проверено]
5. **Трек морфов в three один на весь массив** (`mesh.morphTargetInfluences`): клип перезаписывает все веса меша — один морф из
   клипа, другой из кода на том же меше не смешать. → §1.4 [исходник GLTFLoader r186]
6. **Скелетный маскот: 3–20 костей, 4 влияния на вершину, ≤ 254 кости для AR**; автовеса в фоне работают
   (`parent_set(type='ARMATURE_AUTO')` через `temp_override`), после них `mesh.validate()` (веса 1,0000001). → §2 [проверено]
7. **Механизм из жёстких частей дешевле скиннинга**: деталь целиком на своей кости/родителе, без весов. → §2.1 [V:H1oNuKChsdU 27:30 по дайджесту W4]
8. **Каждый клип маскота — своё действие в своей NLA-дорожке с одной полосой**; экспортёр пишет каналы всех костей (12 на 4 кости). → §2.2 [проверено]
9. **Констрейнты и драйверы в glTF не уходят**: запекай в ключи — `anim_utils.bake_action_objects(... do_visual_keying=True,
   do_constraint_clear=True)` без операторов или `export_bake_animation=True` при экспорте. → §3 [проверено]
10. **Follow Path, добавленный после вычисленного depsgraph, молча не двигает объект**: сразу `curve.use_path = True;
    path.update_tag()`. → §3.2 [проверено]
11. **После запекания драйверов удали их** (`ob.driver_remove(path)`) — иначе драйвер продолжит перекрывать ключи в Blender. → §3.3 [проверено]
12. **Ткань → морфы без аддона MDD**: `object.modifier_apply_as_shapekey(keep_modifier=True, modifier="Cloth")` на каждом кадре
    (кэш считается последовательным `frame_set`), затем «ступенька» весов. MDD в ядре 5.2 нет. → §4.2 [проверено]
13. **Порог «морфы или VAT»**: морфы — до ≈ 20–30 форм и ≈ 10 тыс. вершин (каждая форма = полная копия дельт, все формы на GPU);
    дальше — VAT-текстура (позиции × кадры) с чтением в шейдере или на CPU. → §4.4 [не проверено: расчёт + Codrops 2026]
14. **Rigid body → ключи**: оператор `rigidbody.bake_to_keyframes` в фоне не проходит `poll()`; путь агента — последовательный
    `frame_set` + визуальное запекание. → §4.1 [проверено: poll — H/00; путь — не проверено]
15. **Симуляцию в вебе не пересчитывай**: ткань, бумага, разрушение — запечённые морфы/VAT/кости; физика в браузере — только
    для интерактива (Rapier), не для «кино». → §4 [практика: каталог A §21.1]
16. **Для AR (Scene Viewer) морфов нет, анимация одна**: отдельный AR-GLB — `../01-web-3d-landscape/05-… §3.7`. → §5 [документация Google]

## 1. Shape keys → morph targets

### 1.1 Создание, анимация, экспорт

- Для glTF годятся только относительные ключи (`Key.use_relative = True`, по умолчанию); абсолютные (Evaluation Time) переводить
  в относительные с ключами `value` [документация: руководство 5.2 Shape Keys, по заметкам H-sub/A].
- Ключи весов живут в действии объекта (слот `KE<Key>`), если у объекта уже есть действие, иначе в действии у `Key`
  (`me.shape_keys.animation_data`) [проверено].
- Экспортёр пишет цели для всех ключей кроме Basis, `mesh.extras.targetNames`, начальные `weights`; при `export_try_sparse_sk=True`
  (умолчание) — разреженные аксессоры, если так меньше [исходник 5.2.40; проверено: E/24].

```python
# Blender 5.2.2 — [проверено] морф «сфера → скруглённый куб → сфера» и проверка GLB
import os, tempfile, json, struct
import numpy as np
import bpy, bmesh
sc = bpy.context.scene; sc.render.fps = 30
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=0.5)
me = bpy.data.meshes.new("morph_blob"); bm.to_mesh(me); bm.free(); me.shade_smooth()
ob = bpy.data.objects.new("morph_blob", me); sc.collection.objects.link(ob)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
d = co / np.linalg.norm(co, axis=1, keepdims=True)
cube = d / (np.sum(np.abs(d) ** 8, axis=1, keepdims=True) ** (1 / 8)) * 0.42      # суперэллипсоид p = 8
ob.shape_key_add(name="Basis", from_mix=False)
k = ob.shape_key_add(name="Cube", from_mix=False)
k.points.foreach_set("co", cube.astype(np.float32).ravel())                         # 5.x: ShapeKey.points
for f, v in ((1, 0.0), (25, 1.0), (60, 0.0)):
    k.value = v; k.keyframe_insert("value", frame=f)
act = me.shape_keys.animation_data.action; act.name = "Morph"
act.use_frame_range = True; act.frame_start, act.frame_end = 1, 60
out = os.path.join(tempfile.mkdtemp(), "morph.glb")
assert bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=False, export_animations=True,
                                 export_morph=True, export_morph_normal=True, export_anim_slide_to_zero=True) == {"FINISHED"}
data = open(out, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
m = j["meshes"][0]
assert m["extras"]["targetNames"] == ["Cube"] and len(m["primitives"][0]["targets"]) == 1
assert j["animations"][0]["name"] == "Morph" and j["animations"][0]["channels"][0]["target"]["path"] == "weights"
print("verts", len(me.vertices), "GLB KB", round(len(data) / 1024, 1))
```

### 1.2 Ловушка модификаторов и как её обойти

`export_apply=True` применяет модификаторы и при этом выбрасывает shape keys у объектов С модификаторами (описание параметра в
5.2.40: «WARNING: prevents exporting shape keys»; в журнале экспорта предупреждения нет). Сфера с Subdivision и двумя ключами:
955 КБ, 0 целей, клип «Morph» пустой по смыслу [проверено]. Решение — применить модификаторы до создания
ключей (геометрия уже финальная) или экспортировать морф-объект с `export_apply=False` отдельным файлом (пресет `anim_morph`
агента E, `../08-export-gltf/04-… §7`).

```python
# Blender 5.2.2 — [проверено] ловушка и исправление: модификаторы применяются ДО shape keys
import os, tempfile, json, struct
import bpy, bmesh
def blob(name):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new("Sub", "SUBSURF").levels = 2
    return ob
def add_key(ob):
    ob.shape_key_add(name="Basis", from_mix=False); k = ob.shape_key_add(name="Tall", from_mix=False)
    for p in k.data:
        p.co.z *= 1.8
def targets(ob):
    out = os.path.join(tempfile.mkdtemp(), ob.name + ".glb")
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_apply=True, export_animations=False)
    data = open(out, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
    return len(j["meshes"][0]["primitives"][0].get("targets", []))
bad = blob("bad"); add_key(bad)
assert targets(bad) == 0                                     # модификатор + export_apply → морфы исчезли молча
good = blob("good")
dg = bpy.context.evaluated_depsgraph_get()
new_me = bpy.data.meshes.new_from_object(good.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
good.modifiers.clear(); good.data = new_me                   # модификаторы применены данными (без оператора)
add_key(good)
assert targets(good) == 1 and len(good.data.vertices) == 98
```

### 1.3 Вес и сжатие

| сцена (H/13: икосфера 5-го уровня, 2 562 → 2 737 вершин glTF) | GLB |
|---|---|
| 2 цели, позиции + нормали | 253 КБ |
| 2 цели, без нормалей (`export_morph_normal=False`) | 187,5 КБ (−26 %; освещение деформированной формы грубее) |
| `gltf-transform optimize --compress meshopt` | 66 КБ, веса совпадают до 1e-4 |
| `gltfpack -cc -kn -km` | 56 КБ, веса ±0,002, узел переименован в `mesh_0` |
| ткань 13×13 вершин, 12 форм по кадрам (§4.2) | 65 КБ вместе с шаром-коллайдером |

[проверено]. Формула до сжатия: `вершины_glTF × цели × (12 + 12 при нормалях) Б`; лицо с
52 формами ARKit на 10 тыс. вершин ≈ 12 МБ с нормалями до сжатия (каталог A оценивает 6 МБ без нормалей) [расчёт]. Draco морфы
не сжимает, Meshopt сжимает [проверено]. Нормали морфов нужны для блестящих материалов (блик «едет» с формой);
для матовых и unlit можно выключить.

### 1.4 Морфы в three r186

- Трек клипа — `<меш>.morphTargetInfluences` на весь массив (NumberKeyframeTrack со stride = число целей); имена целей — из
  `extras.targetNames` (если длина не совпадает — предупреждение и имена игнорируются) [исходник GLTFLoader r186, заметки H-sub/B].
- Веса в сэмплированном клипе совпадают с Blender до 1e-4 (6 контрольных кадров), в CUBICSPLINE — до 0,07 [проверено].
- Управлять весом из кода: `mesh.morphTargetInfluences[mesh.morphTargetDictionary.Cube] = v` — только если этот меш не
  анимирует клип (иначе клип перезапишет весь массив на следующем `mixer.update`) [исходник PropertyMixer: запись только при
  изменении значения, заметки H-sub/B; не проверено запуском].
- Цена кадра: морфы считаются в вершинном шейдере; число целей в three не ограничено 8, как в старых ревизиях (морф-текстура)
  [документация three: заметки H-sub/B; порог производительности на телефонах не мерялся — открытый вопрос].

## 2. Простые риги для маскотов

### 2.1 Когда скелет, когда части

| задача | решение | почему |
|---|---|---|
| робот, лампа, механизм, кейс | жёсткие части: каждая деталь — объект на своём родителе или кости целиком, без весов | дешевле скиннинга, нет «резины» в сгибах [V:H1oNuKChsdU 27:30 по W4] |
| персонаж-маскот, машет, дышит | арматура 3–20 костей + автовеса или веса формулой; рёбра сетки выше, ниже и посередине сустава [V:H1oNuKChsdU 27:15 по W4] | плавные изгибы |
| мимика, «надувание» | shape keys (§1) | точная форма, нет костей |
| готовый персонаж (MPFB у заказчика) | его риг + свои действия | `../05-modeling/` (D1) |

Лимиты веба и AR: 4 влияния на вершину (`export_influence_nb=4`), ≤ 254 кости для Scene Viewer, 1–3 клипа (Idle, Hover, Intro),
0,25–1 МБ на персонажа (маскоты GitHub 248–359 КБ) [документация Google; проверено сайтом: `../01-web-3d-landscape/01-… §12.1`, `05-… §3.4`].
Не деформировать n-гоны — пересчитывают разбиение [V:PAK5zQONgvs ≈17:42 по W4].

### 2.2 Код: маскот с автовесами и двумя клипами

```python
# Blender 5.2.2 — [проверено] маскот: 4 кости, автовеса (ARMATURE_AUTO в фоне), клипы Idle и Wave
import math, os, tempfile, json, struct
import bpy, bmesh
from mathutils import Matrix
sc = bpy.context.scene; sc.render.fps = 30
bm = bmesh.new()                                                  # тело (эллипсоид) + рука (цилиндр) одним мешем
bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.35)
bmesh.ops.scale(bm, vec=(1.0, 0.8, 1.3), verts=bm.verts)
bmesh.ops.translate(bm, vec=(0, 0, 0.45), verts=bm.verts)
arm_geo = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.07, radius2=0.06, depth=0.42)
bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"), verts=arm_geo["verts"])
bmesh.ops.translate(bm, vec=(0.48, 0, 0.55), verts=arm_geo["verts"])
me = bpy.data.meshes.new("mascot_body"); bm.to_mesh(me); bm.free(); me.shade_smooth()
body = bpy.data.objects.new("mascot_body", me); sc.collection.objects.link(body)
arm = bpy.data.armatures.new("mascot_rig"); rig = bpy.data.objects.new("mascot_rig", arm); sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")                              # кости создаются только в EDIT (нужен активный объект)
eb = arm.edit_bones
for name, head, tail, parent in (("root", (0, 0, 0), (0, 0, 0.2), None), ("spine", (0, 0, 0.2), (0, 0, 0.7), "root"),
                                 ("head", (0, 0, 0.7), (0, 0, 1.0), "spine"), ("arm_r", (0.27, 0, 0.55), (0.69, 0, 0.55), "spine")):
    b = eb.new(name); b.head, b.tail = head, tail
    if parent:
        b.parent = eb[parent]
bpy.ops.object.mode_set(mode="OBJECT")
with bpy.context.temp_override(active_object=rig, object=rig, selected_objects=[body, rig], selected_editable_objects=[body, rig]):
    assert bpy.ops.object.parent_set(type="ARMATURE_AUTO") == {"FINISHED"}     # автовеса работают и в blender -b
body.data.validate()                     # автовеса оставляют веса 1,0000001 → иначе экспортёр пишет «Mesh … is not valid»
assert body.parent == rig and "arm_r" in body.vertex_groups
rig.animation_data_create()
for clip, bname, keys, axis in (("Wave", "arm_r", ((1, 0), (8, 35), (16, -20), (23, 35), (31, 0)), 0),
                                ("Idle", "spine", ((1, 0), (46, 4), (91, 0)), 1)):
    pb = rig.pose.bones[bname]; pb.rotation_mode = "XYZ"
    for f, deg in keys:
        pb.rotation_euler[axis] = math.radians(deg); pb.keyframe_insert("rotation_euler", index=axis, frame=f)
    act = rig.animation_data.action; act.name = clip
    act.use_frame_range = True; act.frame_start, act.frame_end = keys[0][0], keys[-1][0]
    tr = rig.animation_data.nla_tracks.new(); tr.name = clip; tr.strips.new(clip, keys[0][0], act)   # клип = дорожка с 1 полосой
    rig.animation_data.action = None; pb.rotation_euler = (0, 0, 0)
out = os.path.join(tempfile.mkdtemp(), "mascot.glb")
assert bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS",
                                 export_skins=True, export_influence_nb=4, export_def_bones=True, export_anim_slide_to_zero=True) == {"FINISHED"}
data = open(out, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
assert len(j["skins"]) == 1 and len(j["skins"][0]["joints"]) == 4
assert sorted(a["name"] for a in j["animations"]) == ["Idle", "Wave"]
print("mascot GLB KB", round(len(data) / 1024, 1), "channels per clip", [len(a["channels"]) for a in j["animations"]])
```

В three: `SkinnedMesh` + `Bone`, клипы кроссфейдом `idle.crossFadeTo(wave, 0.3)` — `03-… §3.2`. Валидатор Khronos выдаёт
`NODE_SKINNED_MESH_NON_ROOT` (меш — ребёнок арматуры) — норма для Blender [проверено]. Каждый клип несёт каналы
всех костей (12 на 4 кости: `export_reset_pose_bones`); весь GLB маскота (514 вершин Blender, 4 кости, 2 клипа) — 36,6 КБ без сжатия [проверено].

## 3. Констрейнты и драйверы → ключи

### 3.1 Что делает экспортёр

Констрейнты (Child Of, Follow Path, Track To, Damped Track) и драйверы glTF не описывает: без запекания анимирован только
родитель/цель, объект стоит [проверено: E/15 a11]. Варианты: (а) `export_bake_animation=True` — экспортёр сэмплирует каждый
объект сцены за диапазон сцены; (б) запечь в новое действие до экспорта (контролируемо: одно действие, имя клипа, диапазон) — путь
для агента [проверено: E/15 a12, H/14].

### 3.2 Запекание без операторов

`bpy_extras.anim_utils.bake_action_objects(pairs, frames=range(...), bake_options=BakeOptions(...))` — у `BakeOptions` 12 обязательных
полей (`only_selected, do_pose, do_object, do_visual_keying, do_constraint_clear, do_parents_clear, do_clean, do_location,
do_rotation, do_scale, do_bbone, do_custom_props`) [проверено: H/00 probe]. Оператор `nla.bake` (умолчание `bake_types={'POSE'}`,
для объектов нужен `{'OBJECT'}`, работает по выделению, `clear_constraints` требует `visual_keying`) проходит `poll()` в фоне, но
зависит от выделения — data-путь надёжнее [проверено: poll — H/00; документация: руководство 5.2, по заметкам H-sub/A].

```python
# Blender 5.2.2 — [проверено] Follow Path + драйвер → запекание в ключи → драйвер снят
import math
import bpy
from bpy_extras import anim_utils
sc = bpy.context.scene; sc.render.fps = 30
cu = bpy.data.curves.new("path", "CURVE"); cu.dimensions = "3D"
sp = cu.splines.new("BEZIER"); sp.bezier_points.add(1)
for bp, p in zip(sp.bezier_points, ((-2, 0, 1), (2, 0, 1))):
    bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
path = bpy.data.objects.new("path", cu); sc.collection.objects.link(path)
bpy.context.view_layer.update()                               # depsgraph уже вычислен — как после любых помощников
ob = bpy.data.objects.new("rider", None); sc.collection.objects.link(ob)
fp = ob.constraints.new("FOLLOW_PATH"); fp.target = path; fp.use_fixed_location = True
cu.use_path = True; path.update_tag()                         # БЕЗ этой строки объект молча стоит в (0, 0, 0)
fp.offset_factor = 0.0; fp.keyframe_insert("offset_factor", frame=1)
fp.offset_factor = 1.0; fp.keyframe_insert("offset_factor", frame=61)
fc = ob.driver_add("rotation_euler", 2)                       # драйвер: поворот от номера кадра
fc.driver.type = "SCRIPTED"; fc.driver.expression = "frame * 0.1"
sc.frame_set(31); assert abs(ob.matrix_world.translation.x) < 0.2 and abs(ob.rotation_euler.z - 3.1) < 1e-4
opts = anim_utils.BakeOptions(only_selected=False, do_pose=False, do_object=True, do_visual_keying=True,
                              do_constraint_clear=True, do_parents_clear=False, do_clean=False, do_location=True,
                              do_rotation=True, do_scale=False, do_bbone=False, do_custom_props=False)
(act,) = anim_utils.bake_action_objects([(ob, None)], frames=range(1, 62), bake_options=opts)
act.name = "Ride"
ob.driver_remove("rotation_euler", 2)                         # драйвер снят: теперь вращение — только ключи
assert len(ob.constraints) == 0 and not ob.animation_data.drivers
sc.frame_set(61); bpy.context.view_layer.update()
assert abs(ob.matrix_world.translation.x - 2) < 1e-3 and abs(ob.rotation_euler.z - 6.1) < 1e-3
print("baked keys per channel:", len(ob.animation_data.action.layers[0].strips[0].channelbag(ob.animation_data.action_slot).fcurves[0].keyframe_points))
```

### 3.3 После запекания

- Ключ на каждый кадр (61 на канал) — нормально: экспортёр всё равно сэмплирует, `gltf-transform optimize` (resample) сократит
  линейные участки в 3–5 раз [проверено].
- Драйвер остаётся в `animation_data.drivers` и в Blender перекрывает ключи — снять `driver_remove`; констрейнты снимаются
  опцией `do_constraint_clear` [проверено].
- Для камер на пути: запечённая камера или JSON-путь — сравнение в `04-… §3` [проверено].

## 4. Физика и симуляции → ключи, морфы, VAT

### 4.1 Жёсткие тела (падающие кубики, россыпь)

- Blender: Rigid Body World, объекты Active/Passive; кэш — `scene.rigidbody_world.point_cache`; в ключи — оператор
  `rigidbody.bake_to_keyframes(frame_start, frame_end, step)` (по выделенным), его `poll()` в фоне False [проверено: H/00 probe].
- Путь агента без окна: кадры по порядку от начала (`frame_set(f)` для f = start…end — кэш симуляции считается только
  последовательно) и визуальное запекание трансформаций (`bake_action_objects`, как в §3.2) [не проверено: указание заказчика
  23.09 13:40 — физику не проверять экспериментом].
- В GLB — клип трансформаций (N тел × 2 канала × кадры): 20 тел × 90 кадров × 2 канала × (12…16 Б) ≈ 50–60 КБ до resample [расчёт].
  В вебе: `LoopOnce + clampWhenFinished` (падение один раз) или скраб; интерактивная физика — Rapier/cannon-es, не клип
  (`../01-web-3d-landscape/01-… §11.3`).

### 4.2 Ткань, мягкие тела → shape key на кадр

```python
# Blender 5.2.2 — [проверено] симуляция ткани → shape key на кадр → морф-клип (без аддона MDD)
import os, tempfile, json, struct
import bpy, bmesh
sc = bpy.context.scene; sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, 24
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=12, y_segments=12, size=0.5)       # платок 1 × 1 м, 169 вершин
me = bpy.data.meshes.new("cloth"); bm.to_mesh(me); bm.free()
cloth = bpy.data.objects.new("cloth", me); cloth.location.z = 0.8; sc.collection.objects.link(cloth)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.3)
sme = bpy.data.meshes.new("ball"); bm.to_mesh(sme); bm.free()
ball = bpy.data.objects.new("ball", sme); ball.location.z = 0.3; sc.collection.objects.link(ball)
ball.modifiers.new("Collision", "COLLISION")
cm = cloth.modifiers.new("Cloth", "CLOTH")
cm.point_cache.frame_start, cm.point_cache.frame_end = 1, 24
cloth.shape_key_add(name="Basis", from_mix=False)
for f in range(2, 25):                                        # кадры строго подряд: кэш ткани считает только следующий кадр
    sc.frame_set(f)
    if f % 2:
        continue                                             # 12 форм на 0,8 с (каждый второй кадр)
    with bpy.context.temp_override(object=cloth, active_object=cloth):
        assert bpy.ops.object.modifier_apply_as_shapekey(keep_modifier=True, modifier="Cloth") == {"FINISHED"}
    cloth.data.shape_keys.key_blocks[-1].name = f"f{f:02d}"
cloth.modifiers.remove(cloth.modifiers["Cloth"])             # дальше анимируют только веса ключей
kb = cloth.data.shape_keys.key_blocks
keys = [k for k in kb if k.name.startswith("f")]
for i, k in enumerate(keys):                                  # «ступенька» весов: в кадре своей формы вес 1, у соседей 0
    for f, v in ((2 * i, 0.0), (2 * i + 2, 1.0), (2 * i + 4, 0.0)):
        if 1 <= f <= 26:
            k.value = v; k.keyframe_insert("value", frame=f)
kb[-1].value = 1.0; kb[-1].keyframe_insert("value", frame=26)   # последняя форма остаётся
cloth.data.shape_keys.animation_data.action.name = "Drape"
z_last = sum(p.co.z for p in keys[-1].data) / len(keys[-1].data) + cloth.location.z
assert z_last < 0.7, z_last                                   # последняя форма: ткань опустилась (средняя высота ниже 0,7 м)
out = os.path.join(tempfile.mkdtemp(), "drape.glb")
assert bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=False, export_animations=True,
                                 export_morph=True, export_morph_normal=False, export_anim_slide_to_zero=True) == {"FINISHED"}
data = open(out, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
prim = next(m for m in j["meshes"] if m["name"] == "cloth")["primitives"][0]
assert len(prim["targets"]) == len(keys) == 12 and [a["name"] for a in j["animations"]] == ["Drape"]
print("cloth: targets", len(prim["targets"]), "GLB KB", round(len(data) / 1024, 1))
```

- Путь Codrops (BalloonButton, 2025-08-20): аддон «Import-Export: NewTek MDD format» → экспорт `.mdd` → импорт обратно как
  shape keys → GLB с Shape Keys и Animations; в three `LoopOnce`, `clampWhenFinished = true`, `setDuration(6)`, проигрыш по клику
  [практика: Codrops 2025-08-20]. В Blender 5.2.2 MDD в ядре нет (категории `import_shape`/`export_shape` пусты, аддоны ядра — BVH,
  FBX, glTF, SVG, UV layout) [проверено] — доступность как расширения не проверялась; путь `modifier_apply_as_shapekey`
  (выше) аддона не требует [проверено].
- «Ступенька» весов даёт смену форм по кадрам; для плавности между формами — перекрывающиеся треугольники весов (вес формы i
  растёт от кадра i−1 до i и падает к i+1) — так и сделано выше; при LINEAR-сэмплах three интерполирует линейно [проверено].

### 4.3 Geometry nodes: симуляция и процедурная анимация

Зона симуляции GN запекается в кэш модификатора (`object.simulation_nodes_cache_bake`, `object.geometry_node_bake_single`
проходят `poll()` в фоне) [проверено]; в glTF уходит только текущий кадр геометрии — анимацию GN переносить так же, как
ткань: форма на кадр → shape keys (если топология постоянна) или VAT (если меняется число вершин — только VAT/точки)
[не проверено: указание заказчика 23.09]. Процедурную анимацию (волна, шум) дешевле повторить шейдером в вебе
(`../01-web-3d-landscape/01-… §5`), чем запекать.

### 4.4 Морфы или VAT: расчёт

| что | морфы (shape keys) | VAT (текстура позиций) |
|---|---|---|
| данные на кадр | дельты вершин: `V × 12 Б` (+12 с нормалями), каждая форма — отдельная цель в GPU | `V` текселей RGBA (half 8 Б или float 16 Б) |
| 3 500 точек × 50 кадров | 50 целей × 3 500 × 12 Б ≈ 2,1 МБ до сжатия | 1024 × 200 float RGBA EXR = 1,7 МБ (Codrops, Houdini VAT 3.0) |
| 169 вершин × 12 кадров (§4.2) | 12 целей, GLB 65 КБ (с шаром) | избыточно |
| смена числа вершин (разрушение, жидкость) | нельзя | можно (точки/индекс вершины в UV2) |
| где считается | вершинный шейдер three (все цели активны) | вершинный шейдер (texelFetch) или CPU раз при загрузке |

[расчёт; практика: Codrops 2026-09-19 — 3 500 точек сетки 50 × 70, 20 292 вершины «супа треугольников», EXR 1,7 МБ + FBX 1,2 МБ;
UV2 = индекс пикселя; EXRLoader переворачивает строки (`height − 1 − y`), знак X в экспорте Houdini инвертирован; декодирование на
CPU один раз, между кадрами — линейная интерполяция на CPU, нормали пересчитаны по позициям; с деформацией в шейдере надо
повторять её и в материале глубины для теней]. Гипотеза каталога A «VAT нужен при > 60 кадров или > 10 тыс. вершин» — порядок
подтверждается расчётом (при 10 тыс. вершин 60 форм = 7,2 МБ до сжатия), экспериментом не проверена. VAT из Blender 5.2 без Houdini:
позиции кадров — `evaluated.to_mesh()` + `vertices.foreach_get("co")` на каждом кадре, запись float-массива в EXR — встроенный
OpenImageIO; шейдер — `texelFetch` по индексу вершины из второго UV [не проверено: путь собран из проверенных частей B и E].

## 5. Что реально доходит до веба и чего стоит

| в Blender | в glTF / three r186 | цена | статус |
|---|---|---|---|
| ключи трансформаций объекта | клип TRS | 1–5 КБ на клип после resample | [проверено: H/10–H/14, H/22] |
| shape keys + ключи value | `targets` + `weights` → morphTargetInfluences | вершины × цели × 12–24 Б; Meshopt ×4 | [проверено] |
| арматура + веса | `skin` → SkinnedMesh, 4 влияния | каналы всех костей в каждом клипе | [проверено] |
| констрейнты, драйверы | нет | запечь (`bake_action_objects`) | [проверено] |
| ткань, мягкие тела | нет | shape key на кадр или VAT | [проверено: H/30 (морфы); VAT — не проверено] |
| rigid body | нет | запечь в ключи | [не проверено] |
| GN-симуляция, процедурная анимация | только текущий кадр | формы/VAT или шейдер в вебе | [не проверено] |
| NLA-смешивание (influence, add) | нет в ACTIONS | запечь или NLA_TRACKS | [исходник 5.2.40; проверено: H/12] |
| анимация материала, света, камеры (свойства) | `KHR_animation_pointer` — three не играет | JS-треки/uniform — `03-… §1.6` | [проверено] |
| модификаторы F-кривых (Noise, Cycles) | запекаются сэмплированием | как ключи | [проверено] |

## Частые ошибки

1. Морф-объект с модификатором и `export_apply=True` (или `bpyx.export_glb(apply_modifiers=True)`) — морфов 0, клип пустой, без
   предупреждения.
2. Разная топология форм (shape key от другого меша, модификатор после ключей) — `foreach_set` падает на длине или форма «рвётся».
3. Надежда, что констрейнт Follow Path/Track To или драйвер «уедет» в GLB — объект стоит; надо запекать.
4. Запекли, но драйвер оставили — в Blender итог перекрыт драйвером, рендер-сверка не совпадает с GLB.
5. Follow Path после `view_layer.update()` без `update_tag()` — объект в (0, 0, 0), запекание сохранит неподвижность.
6. Автовеса без `mesh.validate()` — предупреждение экспортёра «Mesh … is not valid» (веса > 1).
7. Два клипа маскота в одной NLA-дорожке — дорожка выпадает из GLB (`01-… §5.3`).
8. Ткань «кадр в кадр» на сотни кадров морфами — десятки МБ; для длинных симуляций — VAT или прореживание кадров (каждый 2–3-й).
9. Физика, пересчитываемая в браузере ради «красивого падения», — дорого и недетерминированно; клип дешевле.
10. Скелет с десятками костей для механизма, где хватило бы жёстких частей на родителях.

## Чек-лист

- [ ] Все формы — относительные shape keys одной топологии, заданные массивами?
- [ ] У морф-объекта нет модификаторов при `export_apply=True` (или экспорт без apply)?
- [ ] В GLB `targets` > 0 и `extras.targetNames` совпадают с именами ключей?
- [ ] Вес морфов посчитан (вершины × цели × 12–24 Б) и сжат Meshopt?
- [ ] Риг: ≤ 20 костей для маскота, 4 влияния, `mesh.validate()` после автовесов, клип = действие в своей дорожке?
- [ ] Все констрейнты и драйверы запечены, драйверы сняты, констрейнты удалены?
- [ ] Follow Path: `curve.use_path = True` и `update_tag()` сразу после создания?
- [ ] Симуляция запечена (морфы/VAT/ключи), а не пересчитывается в браузере?
- [ ] Для AR — отдельный GLB без морфов и с одной анимацией?

## Открытые вопросы и противоречия

- Rigid body → ключи в фоне (последовательный `frame_set` + `bake_action_objects`) и GN-симуляция → формы — не проверены
  (указание заказчика экономить); оператор `rigidbody.bake_to_keyframes` в фоне не проходит `poll()`.
- VAT из Blender 5.2 без Houdini — собран из проверенных частей, целиком не запускался; расширения Blender для VAT (например, OpenVAT) —
  не проверены.
- MDD как расширение в 5.2 (наличие, лицензия) не проверялось; путь `modifier_apply_as_shapekey` его заменяет.
- Цена морфов и скиннинга на телефонах (кадр, память) не мерялась: на стенде Iris Xe 2 737 вершин × 2 цели и 4 кости не влияют на 60 fps.
- Порог «морфы или VAT» — расчёт; восприятие качества интерполяции форм не оценивалось.

## Источники

- [S1] Blender Foundation. Blender Manual 5.2: Shape Keys, Armatures (Skinning), Constraints, Drivers, Physics (Rigid Body, Cloth, Baking) — https://docs.blender.org/manual/en/5.2/animation/shape_keys/introduction.html и соседние; shape keys прочитаны помощником (`99-raw/notes/wave2/H-sub/A-blender-docs.md`), остальное — по именам операторов из RNA; первичный.
- [S2] Blender Foundation. Python API 5.2: ShapeKey (points), Key, bpy_extras.anim_utils (BakeOptions, bake_action_objects), bpy.ops.object.modifier_apply_as_shapekey, parent_set, rigidbody.bake_to_keyframes — дамп RNA `99-raw/experiments/H/00-api-probe/probe.json`; первичный.
- [S3] KhronosGroup/glTF-Blender-IO 5.2.40: `__init__.py` (export_apply, морфы, скины), `blender/exp/nodes.py` (проверка `mesh.validate()`), `action.py`; первоисточник.
- [S4] mrdoob/three.js r186: `GLTFLoader.js` (морф-треки, targetNames), `PropertyMixer.js` — заметки помощника `H-sub/B-web-docs.md`; первичный.
- [S5] Codrops, «Exporting a Cloth Simulation from Blender to an Interactive Three.js Scene», 2025-08-20 — https://tympanus.net/codrops/2025/08/20/exporting-a-cloth-simulation-from-blender-to-an-interactive-three-js-scene/ (кэш `99-raw/cache/tympanus.net_codrops_2025_08_20_…`) — путь cloth → MDD → shape keys → GLB; практика, версия Blender в статье не указана.
- [S6] Codrops, T. Nagasawa, «Interactive Crumpled Paper Effect with Houdini VAT and Three.js», 2026-09-19 — https://tympanus.net/codrops/2026/09/19/crumbled-paper-houdini-vat-threejs/ + https://github.com/item-develop/paper-crumple-demo — VAT: размеры, UV2, переворот строк, знак X, декодирование на CPU; практика.
- [S7] Агент E, волна 1. `../08-export-gltf/01-export-contract.md` §4.6, §9; эксперименты E/07, E/15, E/17, E/22, E/24 — ловушка модификаторов, скиннинг, Draco против морфов; внутренний.
- [S8] Агент A, волна 1. `../01-web-3d-landscape/01-effects-catalog.md` §12, §21.1; `05-blender-deliverables-map.md` §3.3–3.4, §3.7, §3.16 — поставки и лимиты AR; внутренний.
- [S9] Google ARCore. Scene Viewer — требования к моделям (через A `05 §3.7`); документация.
- [S10] Дайджест W4 (волна 2): `[V:H1oNuKChsdU 27:15, 27:30]`, `[V:PAK5zQONgvs ≈17:42]` — по отчёту `99-raw/reports/wave2-W4-report.md`.
- [S11] Эксперименты H: `13-morph`, `14-camera-path`, `22-size-postprocess`, `00-api-probe`, `30-doc-snippets` — [проверено].
