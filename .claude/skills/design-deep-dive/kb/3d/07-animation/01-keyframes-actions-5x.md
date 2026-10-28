# Ключи и действия из Python в Blender 5.2: слоты, F-кривые, изинги, петли, NLA, паттерны для сайта

Волна 2 · агент H · 2026-09-23 · источников 14 (исходники glTF-Blender-IO 5.2.40 и three r186, API и руководство Blender 5.2,
release notes 4.4/5.0, файлы волны 1 B и E, дайджесты W3/W4) · экспериментов 9 (`99-raw/experiments/H/00…22`) · Blender 5.2.2 LTS,
glTF-IO 5.2.40, three r186 (0.186.0). Блоки `python` выполнены в напечатанном виде скриптом `99-raw/experiments/H/30-doc-snippets`.

## Выжимка для агента

1. **Кривые живут в слоте**: Action → `slots` → `layers[0]` → `strips[0]` (`ActionKeyframeStrip`) → `channelbag(slot)` → `fcurves`.
   `action.fcurves` в 5.x нет (AttributeError) — брать `anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)`. → §1 [проверено]
2. **`keyframe_insert(data_path, index=…, frame=…)` — всё после пути только именами**; позиционный вызов из руководства 4.4
   даёт TypeError. → §2 [проверено]
3. **Действие без слота не анимирует**: после `ad.action = act` на чужом объекте `ad.action_slot is None`; ставить
   `ad.action_slot = act.slots.new(id_type="OBJECT", name=ob.name)` или `ad.action_suitable_slots[0]`. → §1.3 [проверено]
4. **Ключ на shape key объекта с уже существующим действием кладётся в ТО ЖЕ действие** (слот `KEKey`, тип KEY);
   ключ на вход материала — в отдельное действие у `material.node_tree`. → §1.2 [проверено]
5. **Ключи, созданные `keyframe_points.add()`, имеют back = amplitude = period = 0** — BACK и ELASTIC «плоские»; задавать
   явно (у `keyframe_insert` умолчания 1,70158 / 0,8 / 4,1). → §2.2 [проверено]
6. **Умолчания новых ключей — BEZIER + AUTO_CLAMPED, `fcurve.auto_smoothing = 'CONT_ACCEL'`**: без правок любое движение с
   разгоном и торможением. Турнтейбл и бегущая лента — `LINEAR`. → §3 [проверено]
7. **glTF знает только LINEAR, STEP, CUBICSPLINE**: SINE/QUAD/…/BACK/BOUNCE/ELASTIC и смешанные интерполяции экспортёр
   всегда сэмплирует (warning «Baking animation because of an unsupported interpolation method»). → §3.2 [проверено]
8. **Экспортируй с сэмплированием (умолчание `export_force_sampling=True`)**: ключ на каждый кадр, совпадение с Blender до
   1e-5 м; CUBICSPLINE легче в 3–8 раз, но даёт ошибку (0,26° и 1,5 мм у парения, 0,07 веса у морфа) и теряет
   `export_anim_slide_to_zero`. → §3.3, `03-… §1.4` [проверено]
9. **Поворот ≥ 180° между ключами без сэмплирования ломается**: 2 ключа 0→360° → объект стоит; ключи 0/180/360° → крутится
   НАЗАД. С сэмплами или ключами через ≤ 90° — верно. → §4.2 [проверено]
10. **Длина клипа = ручной диапазон действия**: `action.use_frame_range = True; frame_start/frame_end` — экспортёр берёт
    `int(action.frame_range)`. Петля: первый и последний ключ равны, диапазон = ровно период. → §4.1 [проверено: H/10, исходник 5.2.40]
11. **Модификатор Cycles нужен только для просмотра в Blender**: в glTF уходит сэмплированный диапазон, петлю в three даёт
    `LoopRepeat`. → §4.1 [проверено]
12. **Для видео и секвенций рендерить 1…N−1**: кадр N петли = кадр 1, иначе «двойной кадр» на стыке. В glTF дубля нет:
    t = duration заворачивается в 0. → §4.1 [проверено: H/10; документация: руководство NLA]
13. **Несколько частей в одном клипе — одно действие со слотом на каждую часть** (`act.slots.new` + `ad.action_slot`); экспортёр
    сливает пообъектные анимации по имени действия. → §5.1 [проверено]
14. **Отдельные действия на части = отдельные клипы, КАЖДЫЙ сдвинут к 0**: стаггер между частями пропадает. Если действия уже
    раздельные — NLA-дорожки с одним именем + `export_merge_animation="NLA_TRACK"`. → §5.2 [проверено]
15. **Второй и следующие клипы — NLA-дорожка ровно с одной полосой** (`stash`): дорожку с 2+ полосами экспортёр в режиме
    ACTIONS пропускает (warning), нужна одна полоса или режим NLA_TRACKS. → §5.3 [проверено]
16. **Смешивание NLA (influence, blend, repeat, scale) в режиме ACTIONS не экспортируется**: экспортёр выключает `use_nla` и
    сэмплирует каждое действие отдельно. → §5.3 [исходник 5.2.40 action.py]
17. **Поза покоя в GLB = кадр 0** — ставь ключи так, чтобы кадр 0 был осмысленной позой (или `export_current_frame`). → §4.3 [проверено]
18. **Pivot = origin объекта**: двигающаяся часть — отдельный объект с origin на оси (петля, центр колеса). → §6.3 [проверено: H/12; V:OVbIOHAI3iY 07:52 по дайджесту W4]
19. **Имена действий = имена клипов в three** (латиница, без точек): `AnimationClip.findByName(gltf.animations, "Reveal")`. → §5.4 [проверено]
20. **Период «парения» 3–4 с, амплитуда 2–6 % высоты, наклон ≤ 5°**; экстремумы — AUTO_CLAMPED (нулевой наклон), фаза наклона
    сдвинута на четверть. → §6.2 [проверено: H/11; мнение: числа — практика, не исследование]

## 1. Модель данных анимации 5.x

### 1.1 Цепочка и её свойства

| уровень | тип (5.2.2) | главное |
|---|---|---|
| действие | `Action` (ID) | `slots`, `layers`, `use_frame_range`, `frame_start`/`frame_end`, `frame_range`, `curve_frame_range`, `use_cyclic`, `is_action_layered` (всегда True), `fcurve_ensure_for_datablock()` |
| слот | `ActionSlot` | `identifier` («OBCube»: префикс типа + имя), `name_display`, `target_id_type` (OBJECT, KEY, NODETREE, CAMERA, LIGHT…), `handle`, `users()`, `duplicate()` |
| слой | `ActionLayer` | `layers.new(name)` — «Currently an Animation can only have at most one layer» |
| полоса | `ActionKeyframeStrip` | `strips.new(type='KEYFRAME')` — одна, бесконечная; `channelbag(slot, ensure=True)`, `channelbags`, `key_insert` |
| пакет каналов | `ActionChannelbag` | `slot`, `fcurves` (`new`, `ensure`, `find`, `new_from_fcurve`, `remove`, `clear`), `groups` |
| кривая | `FCurve` | `data_path`, `array_index`, `keyframe_points`, `modifiers`, `extrapolation` (CONSTANT/LINEAR), `auto_smoothing`, `evaluate(frame)`, `bake(start, end, step, remove)` |
| привязка | `AnimData` | `action`, `action_slot`, `action_suitable_slots`, `last_slot_identifier`, `nla_tracks`, `use_nla`, `drivers` |

[проверено] Слои и полосы есть только в Python API, в интерфейсе 5.2 их нет
(руководство, раздел Actions) [документация: Blender Manual 5.2 Actions]. Удалённые в 5.0 `action.fcurves`, `action.groups`,
`action.id_root` дают AttributeError [проверено: B/03 строки 68–70].

```python
# Blender 5.2.2 — [проверено] цепочка Action → слот → слой → полоса → channelbag → F-кривые
import bpy
from bpy_extras import anim_utils
ob = bpy.data.objects.new("hero", None); bpy.context.scene.collection.objects.link(ob)
ob.location = (0, 0, 0); ob.keyframe_insert("location", frame=1)
ob.location = (0, 0, 1); ob.keyframe_insert("location", index=2, frame=31)     # всё после data_path — именами
ad = ob.animation_data
act, slot = ad.action, ad.action_slot
strip = act.layers[0].strips[0]
cb = anim_utils.action_get_channelbag_for_slot(act, slot)                        # было: act.fcurves (удалено в 5.0)
assert (act.name, slot.identifier, slot.target_id_type) == ("hero" + "Action", "OBhero", "OBJECT")
assert type(strip).__name__ == "ActionKeyframeStrip" and len(act.layers) == 1 and cb == strip.channelbag(slot)
assert [(f.data_path, f.array_index, len(f.keyframe_points)) for f in cb.fcurves] == [("location", 0, 1), ("location", 1, 1), ("location", 2, 2)]
print(act.name, slot.identifier, [fc.evaluate(16) for fc in cb.fcurves])      # z на кадре 16 = 0.5 (Bezier, симметрично)
```

### 1.2 Что попадает в одно действие

- Объект и его shape keys: ключ на `key_blocks["X"].value` у объекта, у которого уже есть действие, добавляет в ЭТО действие
  слот `KE<имя Key>` (тип KEY) [проверено]; руководство называет это эвристикой «closely related» (объект + данные,
  материал + дерево нод) и даёт оператор Separate Slots для разделения [документация: Blender Manual 5.2 Actions, по заметкам H-sub/A].
- Вход материала (`p.inputs["Base Color"].keyframe_insert("default_value", …)`) — действие «<Материал>Action» у
  `material.node_tree` со слотом `NTShader Nodetree` [проверено]; в glTF такая анимация уходит только как
  `KHR_animation_pointer`, который three r186 не играет — `03-… §1.6`.
- Экспортёр складывает слоты одного действия в одну glTF-анимацию (TRS объекта + веса морфов) [исходник 5.2.40 `action.py`, ActionsData].

### 1.3 Назначение действия и слота

```python
# Blender 5.2.2 — [проверено] одно действие на два объекта: у каждого свой слот
import bpy
a = bpy.data.objects.new("part_a", None); b = bpy.data.objects.new("part_b", None)
for o in (a, b):
    bpy.context.scene.collection.objects.link(o)
a.keyframe_insert("location", frame=1)
act = a.animation_data.action
bad = b.animation_data_create(); bad.action = act
assert bad.action_slot is None                                  # 4.4+: чужое действие без слота НЕ анимирует
assert [s.identifier for s in bad.action_suitable_slots] == ["OBpart_a"]
bad.action_slot = act.slots.new(id_type="OBJECT", name=b.name)  # свой слот → свой channelbag в том же действии
b.location.z = 2; b.keyframe_insert("location", index=2, frame=20)
assert [s.identifier for s in act.slots] == ["OBpart_a", "OBpart_b"] and [u.name for u in act.slots[1].users()] == ["part_b"]
assert len(act.layers[0].strips[0].channelbags) == 2
```

`Action.fcurve_ensure_for_datablock(ob, "rotation_euler", index=2)` до присвоения действия объекту → `RuntimeError: Assign action
"…" to "…" before calling this function`; после присвоения создаёт слот сам [проверено].

## 2. Ключи из Python

### 2.1 `keyframe_insert`

Сигнатура 5.2: `keyframe_insert(data_path, *, index=-1, frame=current, group="", options=set(), keytype='KEYFRAME')`
[документация: API 5.2 bpy_struct; проверено: B/03 №72, H/01]. `options`: `INSERTKEY_NEEDED` (не ставить, если значение не
изменилось — предупреждение «Due to the setting 'Only Insert Needed'»), `INSERTKEY_VISUAL` (итог с констрейнтами), …;
`INSERTKEY_XYZ_TO_RGB` удалён в 5.0 (ValueError) [проверено: B/03 №73, H/01]. Опечатка в пути → `TypeError: … property
"locaton" not found` [проверено]. Возвращает True/False — проверяй.

### 2.2 Кривые напрямую (без операторов и без смены значений объекта)

```python
# Blender 5.2.2 — [проверено] F-кривая «вручную»: слот, channelbag, ключи, изинг BACK
import bpy
from bpy_extras import anim_utils
ob = bpy.data.objects.new("lid", None); bpy.context.scene.collection.objects.link(ob)
act = bpy.data.actions.new("Open")
slot = act.slots.new(id_type="OBJECT", name=ob.name)
cb = anim_utils.action_ensure_channelbag_for_slot(act, slot)          # создаёт слой и полосу, если их нет
fc = cb.fcurves.new("rotation_euler", index=0, group_name="Object Transform")
fc.keyframe_points.add(2)
for kp, (f, v) in zip(fc.keyframe_points, ((1, 0.0), (25, -1.83))):   # −105° за 0,8 с при 30 fps
    kp.co = (f, v); kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
k0 = fc.keyframe_points[0]
assert (k0.back, k0.amplitude, k0.period) == (0.0, 0.0, 0.0)          # add() не ставит умолчаний изинга!
k0.interpolation, k0.easing, k0.back = "BACK", "EASE_OUT", 1.2          # перелёт ≈ 7 %
fc.update()
ad = ob.animation_data_create(); ad.action = act; ad.action_slot = slot
bpy.context.scene.frame_set(13)
assert -1.83 * 1.2 < ob.rotation_euler.x < -1.83 * 0.8 and abs(fc.evaluate(25) + 1.83) < 1e-6   # float32
```

- `fc.keyframe_points.insert(frame, value, options={'FAST'})` — альтернатива по одному ключу; после пакетной правки `co`
  вызывать `fc.update()` (сортировка и ручки) [документация: API 5.2 FCurve].
- Большие массивы ключей: `keyframe_points.add(n)` + `keyframe_points.foreach_set("co", flat)` [документация: API 5.2;
  не проверено на скорость].

## 3. Интерполяция, изинги, ручки

### 3.1 Что есть в 5.2

| свойство ключа | значения (5.2.2) | умолчание |
|---|---|---|
| `interpolation` | CONSTANT, LINEAR, BEZIER, SINE, QUAD, CUBIC, QUART, QUINT, EXPO, CIRC, BACK, BOUNCE, ELASTIC | BEZIER (`preferences.edit.keyframe_new_interpolation_type`) |
| `easing` | AUTO, EASE_IN, EASE_OUT, EASE_IN_OUT | AUTO |
| `handle_left_type` / `handle_right_type` | FREE, ALIGNED, VECTOR, AUTO, AUTO_CLAMPED | AUTO_CLAMPED |
| `back` / `amplitude` / `period` | float | 1,70158 / 0,8 / 4,1 у `keyframe_insert`; 0 / 0 / 0 у `keyframe_points.add()` |
| `FCurve.auto_smoothing` | NONE, CONT_ACCEL | CONT_ACCEL (`fcurve_new_auto_smoothing`) |

[проверено: H/00, H/01 и проверка умолчаний --expr 2026-09-23]. Интерполяция ключа действует на сегмент ДО следующего ключа.
AUTO_CLAMPED не даёт перелётов и обнуляет наклон в экстремумах — это и нужно для петель; AUTO с CONT_ACCEL может «перелетать»
[документация: руководство 5.2 F-Curve properties, по заметкам H-sub/A].

### 3.2 Что из этого доживает до glTF

- Без сэмплирования (`export_force_sampling=False`) свойство экспортируется кривой только если: интерполяция первого ключа ∈
  {BEZIER → CUBICSPLINE, LINEAR, CONSTANT → STEP}, у всех ключей она одинакова, у x/y/z одинаковые кадры ключей, ключей > 1,
  у кости нет констрейнтов. Иначе это свойство сэмплируется [исходник 5.2.40 `fcurves/channels.py`, `needs_baking`].
- Изинги SINE…ELASTIC и «смешанные» кривые всегда уходят сэмплами: Pulse с QUAD/SINE — 46 ключей LINEAR и при
  `force_sampling=False` [проверено]; BACK у крышки — warning «Baking animation because of an unsupported interpolation
  method: BACK» [проверено].
- Модификаторы F-кривых (Noise, Cycles, Stepped) в кривую не переносятся; при сэмплировании их эффект запекается
  (depsgraph вычисляет кадр целиком) [исходник 5.2.40: `fcurves/keyframes.py` берёт только `evaluate()` в кадрах ключей].

### 3.3 Сэмплы против кривых: точность и вес

| клип (H/…) | сэмплы: ключей / байт | кривые: ключей / байт | ошибка кривых в three |
|---|---|---|---|
| Float (bob + наклон, 3 с), H/11 | 91 + 91 / 3 648 (с Pulse) | 3 + 4 / 1 064 | до 1,5 мм и 0,26° + сдвиг на кадр |
| Morph (2 веса, 3 с), H/13 | 90 / 1 080 | 5 / 140 | до 0,07 веса |
| Turntable (4 с), H/10 | 121 / 2 420 | 2 / 40 | **нет вращения** |

[проверено: 99-raw/experiments/H/10-turntable, 11-float-pulse, 13-morph]. Тангенсы CUBICSPLINE экспортёр строит из ручек
Безье приближением «через t + 1» (комментарий в исходнике: «only works for locally linear transformation»), а
`export_anim_slide_to_zero` применяет только в сэмплированном пути (`sampled/*/sampler.py`) → клип кривых начинается с 1/fps
[исходник 5.2.40; проверено: H/10 — длительность 4,0333 вместо 4,0]. Вес сэмплов — единицы КБ на клип и режется
`gltf-transform optimize` (resample) в 3–5 раз без видимой разницы — `03-… §2` [проверено]. Вывод: сэмплы по умолчанию.

### 3.4 Изинги Blender в JS (если движение делаешь кодом, а тайминг — в Blender)

BACK ease-out: `u' = u − 1; y = u'²·((s + 1)·u' + s) + 1`, `s = keyframe.back`; EXPO ease-out в 5.2 нормирован:
`y = (1 − 2^(−10u)) / (1 − 2^(−10))`. JS-таймлайн с этими формулами повторяет клип Blender с точностью 0,1 мм и 0,02°
[проверено: 99-raw/experiments/H/16-logo-motion, logo_timeline.js]. Длительности и кривые для интерфейсного движения —
`../../ui/08-motion/01-durations-easings-springs.md` (не дублируем).

## 4. Петли и диапазоны

### 4.1 Правила петли

1. Первый и последний ключ равны (или отличаются на период угла), диапазон действия — ровно период:
   `action.use_frame_range = True; action.frame_start, action.frame_end = 1, 1 + период`. Экспортёр режет клип по
   `int(action.frame_range)` [исходник 5.2.40 `action.py`, `prepare_actions_range`; проверено: H/10 — 1…121 → 4,0 с].
2. Экстремумы — AUTO_CLAMPED (нулевой наклон), тогда стык гладкий; для фазового сдвига (наклон на четверть периода позже)
   добавь модификатор Cycles, чтобы участок до первого ключа тоже был периодическим — экспортёр сэмплирует с модификатором
   [проверено: H/11: 9 контрольных кадров совпали до 1e-5].
3. `use_cyclic` — только пометка намерения, сам ничего не зацикливает [документация: руководство 5.2 Actions].
4. В three петля — `LoopRepeat` (умолчание AnimationAction); t = duration заворачивается в 0, поэтому ключ «N = 1» не даёт
   двойного кадра [проверено]. В видео/секвенции рендерить кадры 1…N−1.

```python
# Blender 5.2.2 — [проверено] петли: турнтейбл (LINEAR) и «парение» (AUTO_CLAMPED + Cycles)
import math
import bpy
from bpy_extras import anim_utils
sc = bpy.context.scene; sc.render.fps = 30
def curves(ob):
    ad = ob.animation_data
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot).fcurves
turn = bpy.data.objects.new("turntable", None); sc.collection.objects.link(turn)    # ось вращения = пустышка, продукт — ребёнок
for f, deg in ((1, 0), (121, 360)):                                                  # 4 с при 30 fps
    turn.rotation_euler.z = math.radians(deg); turn.keyframe_insert("rotation_euler", index=2, frame=f)
for kp in curves(turn)[0].keyframe_points:
    kp.interpolation = "LINEAR"                                                      # равномерно, без «запинки» на стыке
a = turn.animation_data.action; a.name = "Turntable"
a.use_frame_range = True; a.frame_start, a.frame_end = 1, 121                        # клип glTF = ровно один оборот
hero = bpy.data.objects.new("hero_gem", None); sc.collection.objects.link(hero)
for f, z in ((1, 0.60), (46, 0.66), (91, 0.60)):                                     # bob 6 см, период 3 с
    hero.location.z = z; hero.keyframe_insert("location", index=2, frame=f)
for f, deg in ((1, 0.0), (23, 4.0), (68, -4.0), (91, 0.0)):                          # наклон ±4°, фаза сдвинута на четверть
    hero.rotation_euler.x = math.radians(deg); hero.keyframe_insert("rotation_euler", index=0, frame=f)
for fc in curves(hero):
    for kp in fc.keyframe_points:
        kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
    fc.modifiers.new(type="CYCLES")                                                  # только для просмотра в Blender
    fc.update()
h = hero.animation_data.action; h.name = "Float"
h.use_frame_range = True; h.frame_start, h.frame_end = 1, 91
sc.frame_set(61); assert abs(math.degrees(turn.rotation_euler.z) - 180) < 1e-3
sc.frame_set(91); assert abs(hero.location.z - 0.60) < 1e-6
sc.frame_set(181); assert abs(hero.location.z - 0.60) < 1e-4                          # Cycles: вторая петля в Blender
```

### 4.2 Турнтейбл: как сломать и как правильно

| вариант (H/10) | в three r186 при t = 0,5 / 1,5 / 2,5 / 3,5 с |
|---|---|
| 2 ключа 0→360° LINEAR, сэмплы (умолч.) | 45 / 135 / 225 / 315° ✔ |
| то же без сэмплирования | 0 / 0 / 0 / 0 — **стоит** (оба кватерниона = (0, 0, 0, 1)) |
| ключи 0/180/360° без сэмплов | 318 / 228 / 138 / 48° — **крутится назад** |
| ключи через 90° без сэмплов | 42 / 132 / 222 / 312° (сдвиг на кадр) |
| 2 ключа BEZIER, сэмплы | 15,5 / 113,9 / 246,1 / 344,5° — разгон и торможение, запинка на стыке |

[проверено]. Ось вращения — пустышка, продукт — ребёнок, интерполяция Linear
[V:5UCc3Z_-ibs 20:48–22:08 по дайджесту W3] [практика]. Эйлеровы кривые с резкими скачками перед экспортом прогоняй через
Euler Filter (Graph Editor → Channel → Discontinuity (Euler) Filter) [документация: руководство 5.2, по заметкам H-sub/A].

### 4.3 Кадр 0 и начало клипа

Экспортёр ставит `frame_set(0)` перед сбором (поза покоя = кадр 0, если не `export_current_frame=True`) [проверено: E/15 a13].
До первого ключа кривая держит первое значение (CONSTANT), поэтому кадр 0 = первый ключ — нормальная поза. Клип с кадра 1
при `export_anim_slide_to_zero=True` начинается с 0 с; без него — с 1/fps (клип «длиннее» на кадр) [проверено].

## 5. Несколько действий, слоты, NLA → несколько клипов

### 5.1 Один клип на много частей — одно действие со слотами

Режим экспорта ACTIONS (умолчание): для каждого объекта берутся активное действие+слот и каждая NLA-дорожка с одной полосой;
пообъектные анимации затем сливаются по `export_merge_animation`: `ACTION` (умолчание) — по имени действия, `NLA_TRACK` —
по имени дорожки (кроме «NlaTrack…» и «[Action Stash]»), `NONE` — не сливать [исходник 5.2.40 `action.py`]. Итог на кейсе
наушников (крышка + 2 наушника + корень) [проверено]:

| как устроены действия | клипы в GLB |
|---|---|
| одно «Reveal» со слотами OBcase_lid/OBbud_l/OBbud_r + Idle в NLA | **Reveal** 1,967 с (3 узла) + Idle 3,0 с |
| то же + `export_merge_animation="NONE"` | Idle + ТРИ клипа с одним именем «Reveal» |
| отдельное действие на каждую часть | Reveal_bud_l 0,867, Reveal_bud_r 0,867, Reveal_case_lid 0,767 с — **каждый сдвинут к 0, стаггер 6 кадров потерян** |
| отдельные действия в NLA-дорожках «Reveal» + merge NLA_TRACK | один клип Reveal 1,567 с, сдвиги сохранены |

### 5.2 Код: раскрытие по частям одним действием + второй клип в NLA

```python
# Blender 5.2.2 — [проверено] клип «Reveal» на 3 части (одно действие, 3 слота) + «Idle» в NLA
import math, os, tempfile, json, struct
import bpy
sc = bpy.context.scene; sc.render.fps = 30
coll = bpy.data.collections.new("WEB"); sc.collection.children.link(coll)
def part(name, z=0.0):
    ob = bpy.data.objects.new(name, None); ob.location.z = z; coll.objects.link(ob); return ob
root, lid, bud_l, bud_r = part("case_root"), part("case_lid", 0.26), part("bud_l", 0.22), part("bud_r", 0.22)
for o in (lid, bud_l, bud_r):
    o.parent = root
act = bpy.data.actions.new("Reveal")
for o in (lid, bud_l, bud_r):                                   # один клип на все части: слот на каждый объект
    ad = o.animation_data_create(); ad.action = act
    ad.action_slot = act.slots.new(id_type="OBJECT", name=o.name)
lid.keyframe_insert("rotation_euler", index=0, frame=1)
lid.rotation_euler.x = math.radians(-105); lid.keyframe_insert("rotation_euler", index=0, frame=24)
for i, b in enumerate((bud_l, bud_r)):                          # стаггер 6 кадров
    f0 = 16 + 6 * i
    b.keyframe_insert("location", index=2, frame=f0)
    b.location.z += 0.13; b.keyframe_insert("location", index=2, frame=f0 + 20)
act.use_frame_range = True; act.frame_start, act.frame_end = 1, 60
root.location.z = 0.0; root.keyframe_insert("location", index=2, frame=1)   # второй клип: Idle на корне
root.location.z = 0.03; root.keyframe_insert("location", index=2, frame=46)
root.location.z = 0.0; root.keyframe_insert("location", index=2, frame=91)
idle = root.animation_data.action; idle.name = "Idle"
tr = root.animation_data.nla_tracks.new(); tr.name = "Idle"
tr.strips.new("Idle", 1, idle)                                  # ОДНА полоса на дорожку (иначе ACTIONS её пропустит)
root.animation_data.action = None                               # освободить объект
out = os.path.join(tempfile.mkdtemp(), "reveal.glb")
assert bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", collection="WEB", export_animations=True,
                                 export_animation_mode="ACTIONS", export_anim_slide_to_zero=True) == {"FINISHED"}
data = open(out, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
clips = {a["name"]: sorted({j["nodes"][c["target"]["node"]]["name"] for c in a["channels"]}) for a in j["animations"]}
assert clips == {"Idle": ["case_root"], "Reveal": ["bud_l", "bud_r", "case_lid"]}, clips
```

### 5.3 NLA: что экспортёр понимает

- Дорожка с 2+ незаглушёнными полосами в ACTIONS пропускается: «NLA track 'LidTwice' has 2 strips, but only single-strip
  tracks are supported in 'actions' mode» — анимация крышки пропала целиком; в режиме NLA_TRACKS та же дорожка запечена в
  клип «LidTwice» 2,067 с, но активные действия в NLA_TRACKS не уходят [проверено].
- Полоса без `action_slot` пропускается с предупреждением; фильтр — `strip.mute`, а не `track.mute` [исходник 5.2.40 `action.py`].
- Push Down / Stash оставляют объект без активного действия; Stash кладёт действие в заглушённую дорожку «[Action Stash]»
  [документация: руководство 5.2 NLA, по заметкам H-sub/A].
- Смешивание полос (influence, Combine/Add, repeat, scale) в ACTIONS не экспортируется: экспортёр выключает `use_nla`, снимает
  solo и сэмплирует каждое действие отдельно [исходник 5.2.40 `action.py`]. Нужна «сборка» из нескольких полос — режим
  NLA_TRACKS (каждая дорожка запекается целиком) или запекание в новое действие (`02-… §3`).
- Режим BROADCAST (новое в 5.2.40): все совместимые действия файла раздаются всем анимированным объектам, как в FBX
  [исходник 5.2.40 `__init__.py`, `action.py`; не проверено запуском].

### 5.4 Имена

Имя клипа = имя действия; при слиянии NONE или повторе на том же объекте — «Действие-ИмяСлота» [исходник 5.2.40]. В three
клип ищется `THREE.AnimationClip.findByName(gltf.animations, "Reveal")`; `mixer.clipAction("Reveal")` на `gltf.scene` вернёт
`null` [проверено]. Имена узлов санитизируются (`Cube.001` → `Cube001`) — называй объекты латиницей через «_» [проверено].

## 6. Паттерны движения для сайта

### 6.1 Параметры, с которых начинать

| паттерн | где делать | длительность / петля | кривая | пример |
|---|---|---|---|---|
| турнтейбл продукта | Blender-клип или JS (`rotation.y += ω·dt`) | 8–20 с на оборот, LoopRepeat | LINEAR | H/10 |
| «парение» hero | Blender-клип или JS (sin/damp) | 3–4 с, петля | AUTO_CLAMPED, фазовый сдвиг наклона | H/11 |
| пульсация CTA | Blender-клип или CSS | 1–1,5 с, петля с паузой | QUAD ease-out вверх, SINE вниз | H/11 |
| раскрытие по частям | Blender-клип (слоты) | 1,5–2,5 с, один раз / скраб | BACK ease-out для крышки, BEZIER + стаггер 4–8 кадров | H/12 |
| взрыв-схема | Blender-клип (слоты) или JS по `extras` | скраб по прокрутке | BEZIER ease-in-out | H/12 (тот же механизм) |
| облёт/пролёт камеры | запечённая камера или JSON-путь | скраб | ease-in-out по пути | H/14 |
| интро логотипа | Blender-клип или JS-таймлайн | 1–1,5 с, один раз | BACK/EXPO ease-out, стаггер 4 кадра | H/16 |

Числа периодов и амплитуд — практика (H/10–H/16 и каталог A §2.2), не исследование восприятия [мнение]. Устойчивые
колебания около 0,2 Гц (период ≈ 5 с) Apple советует избегать (руководство visionOS) — переносимость на веб не проверена
[документация: Apple HIG, через `../../ui-research/08-motion/01-… §8.4`].

### 6.2 Библиотека паттернов (одно действие на паттерн)

```python
# Blender 5.2.2 — [проверено] паттерны: пульсация, взрыв-схема (слоты), облёт камеры
import math
import bpy
from mathutils import Vector
sc = bpy.context.scene; sc.render.fps = 30
def empty(name, loc=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None); ob.location = loc; sc.collection.objects.link(ob); return ob

def pulse(ob, peak=1.2, rise=12, total=45, name="Pulse"):
    """Масштаб 1 → peak (QUAD ease-out) → 1 (SINE), петля total кадров."""
    for f, s in ((1, 1.0), (1 + rise, peak), (1 + total, 1.0)):
        ob.scale = (s, s, s); ob.keyframe_insert("scale", frame=f)
    act = ob.animation_data.action; act.name = name
    for fc in act.layers[0].strips[0].channelbag(ob.animation_data.action_slot).fcurves:
        k = fc.keyframe_points
        k[0].interpolation, k[0].easing = "QUAD", "EASE_OUT"
        k[1].interpolation, k[1].easing = "SINE", "EASE_IN_OUT"
    act.use_frame_range = True; act.frame_start, act.frame_end = 1, 1 + total
    return act

def explode(parts, center, dist=0.35, start=1, dur=30, stagger=3, name="Explode"):
    """Каждая деталь уходит от центра вдоль (origin − center); одно действие, слот на деталь → один клип."""
    act = bpy.data.actions.new(name)
    for i, ob in enumerate(parts):
        ad = ob.animation_data_create(); ad.action = act
        ad.action_slot = act.slots.new(id_type="OBJECT", name=ob.name)
        d = (ob.location - Vector(center)); d = d.normalized() if d.length > 1e-6 else Vector((0, 0, 1))
        f0 = start + i * stagger
        ob.keyframe_insert("location", frame=f0)
        ob.location = ob.location + d * dist; ob.keyframe_insert("location", frame=f0 + dur)
    act.use_frame_range = True; act.frame_start, act.frame_end = start, start + dur + stagger * (len(parts) - 1)
    return act

def orbit_camera(cam, target, radius=3.0, height=1.2, deg=90, frames=120, name="Orbit"):
    """Облёт: пустышка-ось в цели вращается, камера — её ребёнок с Track To; запекать не нужно (TRS пустышки)."""
    pivot = empty(cam.name + "_pivot", target)
    cam.parent = pivot; cam.location = (0, -radius, height)
    tt = cam.constraints.new("TRACK_TO"); tt.target = pivot; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler.z = math.radians(deg); pivot.keyframe_insert("rotation_euler", index=2, frame=1 + frames)
    pivot.animation_data.action.name = name
    return pivot

dot = empty("cta_dot"); a1 = pulse(dot)
parts = [empty(f"layer_{i}", (0, 0, 0.1 * i)) for i in range(4)]
a2 = explode(parts, center=(0, 0, 0.15))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
pv = orbit_camera(cam, (0, 0, 0.3))
sc.frame_set(13); assert abs(dot.scale.x - 1.2) < 1e-4
sc.frame_set(40); assert (parts[3].location - Vector((0, 0, 0.3))).length > 0.3
sc.frame_set(121); bpy.context.view_layer.update()
assert abs(math.degrees(pv.rotation_euler.z) - 90) < 1e-3 and len(a2.slots) == 4
```

Облёт пустышкой с камерой-ребёнком экспортируется без запекания: в glTF уходит TRS пустышки, а Track To — констрейнт, его
нужно запечь (`02-… §3`) или заменить ключами поворота камеры; для прокрутки чаще берут путь (`04-… §3`).

### 6.3 Pivots и части

- Двигающаяся часть — отдельный объект с origin на оси движения; перенос origin без оператора: `local = ob.matrix_world.inverted()
  @ p; ob.data.transform(Matrix.Translation(-local)); ob.matrix_world = ob.matrix_world @ Matrix.Translation(local)`
  [проверено: H/12 `set_pivot`]; в three pivot = origin узла [проверено].
- Ориентации и точки вращения задавать заранее, до ключей [V:OVbIOHAI3iY 07:52 по дайджесту W4] [практика].
- Механизм из отдельных частей, каждая целиком на своём родителе/кости, дешевле скиннинга [V:H1oNuKChsdU 27:30 по дайджесту W4] —
  `02-… §2`.
- Вложенные детали не должны иметь совпадающих граней: в H/12 пластина на уровне крышки корпуса дала z-конфликт — Blender и three
  «выбрали» разные грани (ΔE 5 → 2,4 после подъёма на 3,5 мм) [проверено].

## 7. Как писали в 3.x → как в 5.2

| № | задача | 3.x–4.3 (по памяти нейросети) | в 5.2.2 | как в 5.2 | доказательство |
|---|---|---|---|---|---|
| 1 | кривые действия | `ob.animation_data.action.fcurves` | AttributeError | `anim_utils.action_get_channelbag_for_slot(act, slot).fcurves` | B/03 №68, H/01 |
| 2 | новая кривая | `act.fcurves.new(path, index=0, action_group="G")` | AttributeError | `cb.fcurves.new(path, index=0, group_name="G")` | B/03 №69, §2.2 |
| 3 | тип ID действия | `act.id_root = "OBJECT"` | AttributeError | `act.slots.new(id_type="OBJECT", name=…)`; `slot.target_id_type` | B/03 №70 |
| 4 | действие на другой объект | `ob2.animation_data.action = act` | тихо: `action_slot = None`, не анимирован | `+ ad.action_slot = slot` | B/03 №71, H/01 |
| 5 | ключ с индексом | `ob.keyframe_insert("location", 2, 10)` | TypeError «takes at most 1 positional argument» | `keyframe_insert("location", index=2, frame=10)` | B/03 №72, H/01 |
| 6 | опция XYZ→RGB | `options={'INSERTKEY_XYZ_TO_RGB'}` | ValueError | убрать (цвет кривых — настройка) | B/03 №73 |
| 7 | группа кривых | `act.groups.new("G")` | AttributeError | `cb.groups.new("G")` | H/00 probe |
| 8 | диапазон действия | `act.frame_range` только по ключам | работает; ручной — `use_frame_range` | `act.use_frame_range = True; frame_start/end` | H/01, H/10 |
| 9 | кривые shape keys | `me.shape_keys.animation_data.action.fcurves` | AttributeError; и это часто действие объекта (слот KEKey) | `channelbag(Key-слот)` | H/01 |
| 10 | слои костей | `arm.layers[i] = True` | AttributeError | `arm.collections.new(…)` | B/03 №74 |
| 11 | выделение кости | `bone.select = True` | AttributeError (5.0) | `pose_bone.select` | B/03 №75 |
| 12 | Back/Elastic из `add()` | «умолчания как в интерфейсе» | 0 / 0 / 0 — плоский изинг | задавать `back`, `amplitude`, `period` | §2.2 |
| 13 | Follow Path после `view_layer.update()` | «работает сам» | тихо: объект не движется | `curve.use_path = True; path.update_tag()` | H/14, `02-… §3` |
| 14 | скраб в three | `action.paused = true; mixer.setTime(p·d)` | поза кадра 0 | `action.time = p·d; mixer.update(0)` | H/20, `03-… §3.3` |

Официальный пример «Slotted Actions: Upgrading to 4.4» с позиционным индексом в 5.2 не работает (№5) [проверено];
снимок сцены mcp-for-blender 2.0.3 читает `action.fcurves` и теряет анимацию — проверять анимацию не инструментами
наблюдения MCP, а экспортом и `anim_summary` [проверено: C1 `../04-ai-agents-mcp/01 §3.2`].

## Частые ошибки

1. `act.fcurves` / `act.groups` / `act.id_root` из кода 3.x–4.3 — AttributeError в 5.x (M-коды дрейфа — `../03-bpy-api/04-…`).
2. Присвоить готовое действие второму объекту и считать его анимированным — слот не назначен, объект стоит (тихо).
3. Позиционные аргументы `keyframe_insert` из официального руководства 4.4 — TypeError.
4. Ключи турнтейбла с BEZIER по умолчанию — «запинка» каждые N секунд; поворот ≥ 180° между ключами без сэмплов — стоит/назад.
5. Экспорт с `export_force_sampling=False` «для лёгкости»: теряются изинги, slide_to_zero, точность поворотов.
6. Отдельное действие на каждую часть раскрытия — клипы разъезжаются по времени (каждый сдвинут к 0).
7. Второй клип в NLA-дорожке с двумя полосами (например, повтор) — дорожка молча (warning) выпадает из GLB.
8. Модификатор Cycles вместо честного диапазона — в Blender петля есть, в GLB клип длиной до последнего ключа.
9. Изинг BACK/ELASTIC на ключах из `keyframe_points.add()` без `back`/`amplitude`/`period` — перелёта нет.
10. Кадр 0 = «объект за кадром» — модель на странице до старта клипа висит в этой позе.
11. Рендер петли для видео кадрами 1…N — двойной кадр на стыке.
12. Проверка анимации инструментами наблюдения MCP — они читают `action.fcurves` и анимацию не видят.

## Чек-лист

- [ ] Кривые берутся через слот/channelbag, нигде нет `action.fcurves`, `action.groups`, `action.id_root`?
- [ ] У каждого анимированного объекта `animation_data.action_slot` не None?
- [ ] `keyframe_insert` — только именованные аргументы, результат True?
- [ ] Турнтейбл и ленты — LINEAR; петли — первый ключ = последний, AUTO_CLAMPED в экстремумах?
- [ ] У каждого клипа ручной диапазон (`use_frame_range`) = ровно период или длительность эффекта?
- [ ] Части одного эффекта — в одном действии со слотами (или в NLA-дорожках с одним именем + merge NLA_TRACK)?
- [ ] Каждая NLA-дорожка для клипа содержит ровно одну полосу со слотом?
- [ ] Экспорт с сэмплированием и `export_anim_slide_to_zero=True`?
- [ ] Кадр 0 — осмысленная поза покоя?
- [ ] Имена действий и объектов — латиница без точек; клип в three находится `findByName`?
- [ ] Двигающиеся части — отдельные объекты с origin на оси движения?

## Открытые вопросы и противоречия

- Режим BROADCAST и `export_extra_animations` (5.2.40) описаны по исходнику, запуском не проверены.
- Второй слой действия: API говорит «at most one layer»; экспортёр перебирает `layers` в `get_channelbag_for_slot` — поведение
  при появлении слоёв (6.x) неизвестно.
- Порог «CUBICSPLINE приемлем»: на наших клипах ошибка 0,26°/1,5 мм/0,07 веса; на длинных плавных клипах камеры не мерялась.
- Числа паттернов (периоды, амплитуды, стаггер) — практика; исследований восприятия для 3D на сайтах не найдено.
- Эвристика «closely related» (объект + shape keys в одном действии): экспортёр её переваривает (одна анимация), но если
  нужен отдельный клип весов — делить действие оператором Separate Slots (`anim.separate_slots`) — не проверено.

## Источники

- [S1] Blender Foundation. Python API 5.2: Action, ActionSlot, ActionChannelbag, FCurve, Keyframe, AnimData, NlaStrip — https://docs.blender.org/api/5.2/bpy.types.Action.html и соседние; дамп RNA сборки 5.2.2 — `99-raw/experiments/H/00-api-probe/probe.json`; первичный.
- [S2] Blender Foundation. Blender Manual 5.2: Actions, F-Curves (properties, modifiers, editing), NLA — https://docs.blender.org/manual/en/5.2/animation/actions.html и соседние; прочитано помощником (заметки `99-raw/notes/wave2/H-sub/A-blender-docs.md`); первичный.
- [S3] Blender Foundation. Release notes 4.4 Slotted Actions: Upgrading — https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/ ; 5.0 Python API — https://developer.blender.org/docs/release_notes/5.0/python_api/ ; первичные (цитируются через B/03).
- [S4] KhronosGroup/glTF-Blender-IO 5.2.40 в составе Blender 5.2.2: `blender/exp/animation/action.py` (1107 строк, прочитан целиком), `fcurves/channels.py` (`needs_baking`), `fcurves/keyframes.py`, `sampled/object/keyframes.py`, `keyframes.py`, `tracks.py`, `__init__.py` (параметры анимации); https://github.com/KhronosGroup/glTF-Blender-IO (1661★, push 2026-09-21 по данным E); первоисточник.
- [S5] mrdoob/three.js r186: `src/animation/*` и `GLTFLoader.js` (раздел анимации) — прочитаны помощником целиком, заметки `H-sub/B-web-docs.md`; 115 767★; первичный.
- [S6] Агент B, волна 1. `../03-bpy-api/03-version-drift-3.6-to-5.2.md` §4 (строки 68–75), §5.5, §6 — проверенная таблица дрейфа; внутренний.
- [S7] Агент E, волна 1. `../08-export-gltf/01-export-contract.md` §9 и эксперименты E/15, E/24, E/26 — контракт экспорта анимации; внутренний.
- [S8] Агент C1, волна 1. `../04-ai-agents-mcp/01-mcp-for-blender.md` §3.2 — снимок мира MCP теряет анимацию 5.x; внутренний.
- [S9] Дайджест W3 (волна 2): «How to Make Studio Lighting in Blender», Blender Guru — `[V:5UCc3Z_-ibs 20:48–22:08]` поворотный стол: Empty-ось, Linear; по отчёту `99-raw/reports/wave2-W3-report.md`.
- [S10] Дайджест W4 (волна 2): `[V:OVbIOHAI3iY 07:52]` pivots заранее; `[V:H1oNuKChsdU 27:15, 27:30]` механика из частей; по отчёту `99-raw/reports/wave2-W4-report.md`.
- [S11] Apple. Human Interface Guidelines: Motion (visionOS, 0,2 Гц) — через `../../ui/08-motion/01-durations-easings-springs.md §8.4`; документация, перенос на веб — мнение.
- [S12] Эксперименты H: `99-raw/experiments/H/00-api-probe`, `01-api-basics`, `10-turntable`, `11-float-pulse`, `12-reveal-parts`, `13-morph`, `16-logo-motion`, `20-scrub-api`, `22-size-postprocess` — [проверено].
