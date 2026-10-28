# Свет, камера и композиция для сайта: студийные схемы, HDRI, калибровка мощности, кадр 16:9 / 9:16 / 1:1 и паспорт серии — Blender 5.2.2

Волна 2 · агент D2 · 23.09.2026 · источников: 8 (Poly Haven API, 4 дайджеста видео W3/W4, файлы C1, E, ui-research) ·
экспериментов: 3 (`99-raw/experiments/D2/04-light-icons` — 3 схемы, калибровка, серия иконок; `D2/01` — IBL; `D2/02` — время) ·
Blender 5.2.2 LTS, three 0.186.0.

Цвет и виды — `03-render-engines-color.md`; материалы — `01-materials-pbr.md`; свет на странице three — `../09-web-runtime/01-…`
(F1); свет в glTF и запекание — `../08-export-gltf/01 §8`, `02 §6` (E); протокол агента и рубрика — `../04-ai-agents-mcp/04` (C1).

## Выжимка для агента

1. **Свет — от габарита ассета, не «на глаз»**: радиус описанной сферы r, дистанция ламп d = 4r, размер area-лампы 1,5–4r, мощность `P = π·d²·E` (E — освещённость на оси, Вт/м²). → §1.2 [проверено]
2. **Калибровка под вид**: Khronos PBR Neutral — E_key 2–3 Вт/м² (объект без пересветов, светлый фон L* 63–76); AgX — в 2–3 раза больше (E_key 5–8; «900 Вт на 7 м» из bpyx = E 5,85 — это калибровка AgX). → §2 [проверено]
3. **Светлый фон — отдельной лампой или альбедо, не усилением key**: подъём key до E 4 выводит фон на L* 88, но 12,5 % пикселей объекта уходят в сжатие Neutral (при ×2,83 — 44 %). → §2 [проверено]
4. **Три схемы по умолчанию**: key/fill/rim (универсальная), большой софтбокс сверху + карты (продукт, глянец), контровые на тёмном (драма); у каждой лампы — своя цель, настраивать по одной. → §1 [проверено] [V:5UCc3Z_-ibs 11:08]
5. **Key сбоку 40–60°, не в анфас**: тень лепит форму; размер источника = мягкость тени, дистанция — спад (обратные квадраты). → §1.3 [V:5UCc3Z_-ibs 02:31, 06:10, 11:52] [V:Z8AAX-ENWvQ 02:09, 05:45]
6. **Циклорама вместо плоскости**: пол + скругление радиуса 0,7–1,2 м + стена, гладкие нормали — нет линии горизонта (M3.8). → §4 [проверено] [V:5UCc3Z_-ibs 04:35]
7. **Прозрачный фон + ловец теней (Cycles)** для иконок и продуктов на сайт: `ob.is_shadow_catcher = True`, `film_transparent = True`; тень уходит в альфу (0,16–0,20 у мягкого света). EEVEE ловца нет. → §4 [проверено]
8. **Мир = фон страницы** (цвет и сила 0,1–0,25) либо HDRI; для бренда — нейтральный (серый) свет, без цветовой температуры. → §3 [проверено] [V:0oIZoSg03PY 05:48]
9. **HDRI Poly Haven без ключа**: studio_small_09 (medium contrast), studio_small_08 (low contrast, 6000 K), brown_photostudio_02, photo_studio_01; в `/info/<id>` — `evs_cap` и `whitebalance` (К). → §3 [документация: Poly Haven API]
10. **EEVEE + HDRI: `world.sun_threshold = 0`**, если сравниваешь с вебом (иначе верхние грани +13 L*); для финала EEVEE умолчание 10 допустимо. → §3 [проверено]
11. **Сначала разрешение (аспект), потом кадрирование**: `camera_fit_coords` считает по текущему соотношению сторон; кадр под 16:9 при рендере 1:1 делает объект мелким. → §5.2 [проверено]
12. **Камера продукта 70–100 мм** (85 — по умолчанию), поворот объекта ≈ 20° к камере, подъём камеры 15–25°, `shift_y` вместо наклона. → §5.1 [V:5UCc3Z_-ibs 00:20–01:29]
13. **Кадр**: 16:9 hero — объект на трети, пустая треть под заголовок; 9:16 — объект в верхней/нижней половине; 1:1 иконка — full frame, поле 10–15 %. → §5.3 [V:O8i7OKbWmRM 14:29, 21:47]
14. **Один фокальный элемент, насыщенный цвет — только на нём**. → §5.3 [V:O8i7OKbWmRM 01:42, 05:50]
15. **Изометрия — ортокамера, наклон 35,264°, азимут 45°**; размер кадра — `ortho_scale`. → §5.1 [практика: C1 04 §3.1]
16. **Паспорт серии (проверен)**: нормированный размер, одна камера, одна схема, один вид Neutral, прозрачный фон — разброс тени 0,9 L* (без паспорта 6,4), кадра 0,19 (0,37), брендовый C* 84–93 (38–44). → §6 [проверено]
17. **Экспозицию проверять False Color**: серое на предмете, без жёлтого/красного на белом. → §2 [V:5UCc3Z_-ibs 08:49]
18. **Для веба свет ставит страница**: Area и HDRI-мир не экспортируются; реалтайм — окружение + 1–2 направленных; статика — запечь (unlit, ΔE 0,73). → §7 [проверено]

## 1. Студийные схемы

### 1.1. Каталог

| схема | лампы (азимут° / угол места° / доля мощности / размер) | для чего | вид (D2/04) |
|---|---|---|---|
| key/fill/rim | key 40/45/1,0/2r; fill −70/15/0,35/3r; rim 170/50/0,6/1,5r | универсальный продукт, иконки | объём читается; фон светлый, стена темнеет кверху |
| большой софтбокс сверху + карты | top 10/80/1,0/4r; карты ±90/5/0,25/3r | глянец, лак, стекло — длинные блики | мягкий верх; лицевая сторона темнее — добавить фронт-карту |
| контровые на тёмном | rim ±135/25/0,9/1,5r; фронт 0/20/0,25/3r | драматичный hero, тёмная тема | кромка слабая при 0,9 — поднимать до 1,5–2 |
| HDRI-студия | мир = HDRI (§3), лампы по желанию | реализм, отражения в металле | отражения «настоящие», свет сложнее контролировать |
| циклорама + контактные тени | любая + циклорама §4 | предрендер на фон страницы | без линии горизонта |
| прозрачный фон + ловец теней | любая + ловец (Cycles) | иконки и продукты на произвольный фон | тень в альфе |

[проверено: D2/04 — три первые схемы на одной модели, `out/sheet_light.png`]. Честная оценка кадров: чисто, но не
уровень Awwwards — нужны отдельный свет фона, key сбоку для лепки и более сильный контровой. Area-лампы с растушёванными
краями дают мягкие блики в стекле и лаке [V:auTKRan7oPk 05:42] (W3). Вторую лампу-акцент прятать за край фона
[V:5UCc3Z_-ibs 11:41].

### 1.2. Код: схема от габарита

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/D2/99-doc-snippets; та же логика — D2/_lib/d2lib.py, эксп. D2/04]
import sys, math, bpy
from mathutils import Vector
sys.path.insert(0, "../../scripts/3d")
import bpyx

RIGS = {   # имя: (азимут°, угол места°, доля E_key, размер в r)
    "three_point": [("Key", 40, 45, 1.0, 2.0), ("Fill", -70, 15, 0.35, 3.0), ("Rim", 170, 50, 0.6, 1.5)],
    "top_softbox": [("Top", 10, 80, 1.0, 4.0), ("CardL", -90, 5, 0.25, 3.0), ("CardR", 90, 5, 0.25, 3.0)],
    "rim": [("RimL", -135, 25, 1.5, 1.5), ("RimR", 135, 25, 1.5, 1.5), ("Front", 0, 20, 0.25, 3.0)],
}

def light_power(d, E):
    """Вт area-лампы, дающей освещённость E (Вт/м²) на оси на расстоянии d (м): P = π·d²·E."""
    return math.pi * d * d * E

def studio_rig(objects, scheme="three_point", E_key=2.5, collection=None):
    """E_key: 2–3 под Khronos PBR Neutral, 5–8 под AgX (калибровка D2/04)."""
    mn, mx = bpyx.world_bbox(objects)
    c = (mn + mx) / 2; r = max((mx - mn).length / 2, 1e-3); d = 4 * r
    lights = []
    for name, az, el, share, size_r in RIGS[scheme]:
        a, e = math.radians(az), math.radians(el)
        loc = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
        lights.append(bpyx.add_light("AREA", name, loc, c, energy=light_power(d, E_key * share), size=r * size_r,
                                     collection=collection))
    return lights

bpyx.clear_scene()
obj = bpyx.primitive("uvsphere", "Hero", radius=0.25, location=(0, 0, 0.25))
L = studio_rig([obj], "three_point", E_key=2.5)
print([(l.name, round(l.data.energy, 1), round(l.data.size, 2)) for l in L])   # r ≈ 0.43 → d 1.73 м, key ≈ 23.5 Вт
```

### 1.3. Правила света

- Каждая лампа — с целью («зачем?»); настраивать по одной, остальные скрыть [V:5UCc3Z_-ibs 11:08–11:18].
- Key сбоку, не в анфас: тень должна показывать форму; тени не бояться [V:5UCc3Z_-ibs 02:31].
- Размер источника = мягкость: большой — мягко, скрывает дефекты; маленький — жёстко, подчёркивает [V:5UCc3Z_-ibs 11:52]
  [V:Z8AAX-ENWvQ 05:45]. Для веб-иконок — большие мягкие источники (тень альфа 0,16–0,20 в D2/04).
- Обратные квадраты: удвоение дистанции — вчетверо меньше света; ровный фон — отодвинуть лампу и поднять мощность
  [V:5UCc3Z_-ibs 06:10]; спад выделяет главный объект без масок [V:Z8AAX-ENWvQ 02:09, 05:30].
- Для глянца и хрома важнее, где отражается лампа, чем освещённость: двигать лампу, пока блик не встанет на форму
  [V:5UCc3Z_-ibs 03:29].
- Лампы витрины бренда — (1,1,1), без `use_temperature`; тёплое/холодное — только атмосфера [V:0oIZoSg03PY 41:17]
  [V:Z8AAX-ENWvQ 01:15].

## 2. Калибровка мощности под вид

Один линейный EXR схемы, умноженный на k и пропущенный через OCIO Blender (метод D2/01): L* светлого пола циклорамы
(#E9E9EC) и доля пикселей объекта с каналом > 0,8 (зона сжатия Neutral) [проверено: D2/04, `out/calib.json`]:

| E_key, Вт/м² | 1 | 1,4 | 2 | 2,8 | 4 | 5,7 | 8 |
|---|---|---|---|---|---|---|---|
| пол L*, Neutral / AgX (key/fill/rim) | 46 / 51 | 55 / 58 | 65,5 / 65,0 | 76 / 71 | 88 / 76 | 95 / 80 | 97 / 84 |
| объект в зоне сжатия | 0,5 % | 0,6 % | 0,7 % | 1,4 % | 12,5 % | 44 % | 73 % |
| пол L*, Neutral / AgX (софтбокс) | 44 / 49 | 53 / 57 | 63 / 63 | 74 / 69 | 85 / 75 | 94 / 79 | 97 / 83 |

Правила: под Neutral держать E_key 2–3 (объект в зоне 1:1) и светлый фон добирать отдельной лампой или альбедо фона;
AgX до E_key 8 не выводит белый фон выше L* 84 — его калибровка в 2–3 раза выше (bpyx `three_point_lights`: 900 Вт на 7 м
= E 5,85) [проверено]. Экспозиция вида (`view_settings.exposure`, стопы) = множитель всех ламп
[V:5UCc3Z_-ibs 10:25]; проверка — False Color (серое на предмете) [V:5UCc3Z_-ibs 08:49]. Мир подсвечивает всё: 0 — свет
только от ламп [V:5UCc3Z_-ibs 02:01], 0,1–0,25 — мягкое заполнение цветом страницы [проверено].

## 3. HDRI

| HDRI (Poly Haven, CC0) | контраст | white balance | загрузок | для чего |
|---|---|---|---|---|
| studio_small_09 | medium | 2750 K | 705 754 | эталон сравнений базы (E, D2), продукт |
| studio_small_08 | low | 6000 K | 592 963 | мягкий продукт, бренд |
| brown_photostudio_02 | medium | 5800 K | 774 681 | тёплая студия с окнами |
| photo_studio_01 | medium | 5622 K | 357 166 | фотостудия |
| studio_small_03 | high | — | 584 070 | контрастные отражения металла |

[документация: Poly Haven API `assets?t=hdris&c=studio`, `/info/<id>`, запрос 23.09.2026]. Сила 1 = как снято;
поворот — нода Mapping (Z) перед Environment Texture; для бренда — обесцветить HDRI (Hue/Saturation, насыщенность 0 в мире
Blender) — в вебе то же только предобработкой файла [практика: V:0oIZoSg03PY 05:48; не проверено]. Для веба 1k HDR
(0,4–0,6 МБ) или `RoomEnvironment` (0 КБ) (A `05 §3.12`). EEVEE выносит яркое из HDRI в «солнце» (`sun_threshold` 10) —
для сравнения с three ставить 0 (`03-render-engines-color.md` §3).

```python
# Blender 5.2.2 — [проверено] мир = HDRI с поворотом и силой
import math, bpy

def world_hdri(path, strength=1.0, rotation_deg=0.0, sun_threshold=0.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("HDRI"); sc.world = w
    nt = w.node_tree; bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(path, check_existing=True)
    mp.inputs["Rotation"].default_value[2] = math.radians(rotation_deg)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = strength
    w.sun_threshold = sun_threshold          # 0 — без «солнца» EEVEE (сравнение с three); 10 — умолчание
    return w

w = world_hdri("../../scripts/3d/data/studio_small_09_1k.hdr", 1.0, 30)
print(w.name, w.sun_threshold)
```

## 4. Фон: циклорама или прозрачный с ловцом теней

| | циклорама | прозрачный фон + ловец теней |
|---|---|---|
| выход | PNG/AVIF с фоном цвета страницы | RGBA: объект + тень в альфе |
| движок | любой | **Cycles** (`is_shadow_catcher`); в EEVEE ловца нет |
| цвет фона | должен совпасть с CSS-фоном (вид Standard для точного hex фона) | любой фон страницы |
| риск | линия стыка, спад на стене | тень на тёмном фоне — альфа-чёрная, на цветном — серая |

- Циклорама: профиль «пол → дуга радиуса 0,7–1,2 м → стена», гладкие нормали [проверено]
  [V:5UCc3Z_-ibs 04:35]; стена темнеет кверху из-за спада — свет фона отдельно.
- Ловец теней: плоскость `is_shadow_catcher = True`, `render.film_transparent = True`, Cycles; для композитинга —
  `view_layer.cycles.use_pass_shadow_catcher` (W3) [проверено: D2/04 — тень альфа 0,16–0,20 при мягком key, 0,46–0,52
  при солнце]. В GLB ловец не класть (M5.4).

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/D2/99-doc-snippets; режим — эксп. D2/04] прозрачный фон + ловец теней
import sys, bpy
sys.path.insert(0, "../../scripts/3d")
import bpyx

def shadow_catcher(size=6.0, z=0.0):
    sc = bpy.context.scene
    floor = bpyx.primitive("plane", "ShadowCatcher", size=size, location=(0, 0, z))
    floor.is_shadow_catcher = True                     # только Cycles
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 32; sc.cycles.use_denoising = True
    sc.render.film_transparent = True                  # фон → альфа 0, тень → частичная альфа
    return floor

print(shadow_catcher().is_shadow_catcher, bpy.context.scene.render.film_transparent)
```

## 5. Камера и кадр

### 5.1. Фокусное, ракурс, изометрия

| задача | камера | почему |
|---|---|---|
| продукт, иконка | 70–100 мм (85 по умолчанию), угол места 15–25°, объект повёрнут ≈ 20° | мало перспективных искажений [V:5UCc3Z_-ibs 00:20, 01:05] |
| «нейтрально», среда | 50 мм | как глаз [V:5UCc3Z_-ibs 00:43] |
| интерьер, диорама | 24–35 мм | глубина |
| изометрия | `type = "ORTHO"`, наклон 35,264°, азимут 45°, `ortho_scale` = размер кадра | без схождения линий [практика] |
| вертикали не заваливать | `shift_y` вместо наклона камеры вниз | [V:5UCc3Z_-ibs 01:29] |

Глубина резкости и shift в glTF не экспортируются (E `01 §8.2`); размытие на странице — постобработкой (F2). ГРИП зависит
от масштаба сцены — моделировать в реальных метрах [V:Z8AAX-ENWvQ 17:24].

### 5.2. Кадр под формат: сначала аспект

`Object.camera_fit_coords` (основа `bpyx.frame_camera`) считает по текущему `resolution_x/y`: в D2/04 кадр, посчитанный при
умолчании 1920×1080 и отрендеренный в 768², дал объект втрое мельче [проверено].

*Исправлено FX 26.09.2026 по T22* (реестр противоречий корневого README): для ORTHO `camera_fit_coords` точен только в
квадратном кадре — ответ зависит от прежнего `ortho_scale`, в 16:9 модель режется (квартира SD 960×540: 9,1–9,8 м при нужных
13,4; из 19 орто-случаев теста до правки обрезаны 9, в одном `ortho_scale` = 0). Теперь `bpyx.frame_camera` для ORTHO считает
кадр проекцией вершин вычисленной геометрии на оси камеры (`ortho_scale` — по `sensor_fit` и `pixel_aspect`, центр с учётом
`shift`), `extra_points=` — концы тени на земле; перспектива не изменилась — положение камеры на 7 сценах совпало бит в бит
[проверено].

```python
# Blender 5.2.2 — [проверено] кадр под 16:9 / 9:16 / 1:1 с местом под текст
import sys, math, bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, "../../scripts/3d")
import bpyx

FORMATS = {"hero_16x9": (1920, 1080, 1.30, -0.17), "mobile_9x16": (1080, 1920, 1.25, 0.0), "icon_1x1": (1024, 1024, 1.30, 0.0)}

def frame_for(objects, fmt="hero_16x9", lens=85.0, az=30.0, el=20.0):
    """Разрешение → камера по азимуту/углу места → frame_camera → shift_x: объект на правой трети, слева место под заголовок."""
    w, h, margin, shift = FORMATS[fmt]
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100   # ДО кадрирования
    mn, mx = bpyx.world_bbox(objects); c = (mn + mx) / 2
    a, e = math.radians(az), math.radians(el)
    cam = bpyx.add_camera(location=c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 5,
                          target=c, lens=lens)
    bpyx.frame_camera(cam, objects, margin=margin)
    cam.data.shift_x = shift                           # −0.17 ширины: объект уезжает к правой трети
    return cam

bpyx.clear_scene()
ob = bpyx.primitive("cube", "Product", size=0.3, location=(0, 0, 0.15))
cam = frame_for([ob], "hero_16x9")
u, v, _ = world_to_camera_view(bpy.context.scene, cam, Vector((0, 0, 0.15)))
print(round(u, 2), round(v, 2))                        # ≈ 0.67 — центр объекта на правой трети
```

### 5.3. Композиция

- Один фокальный элемент; фокус создают насыщенность, контраст и резкость; насыщенный цвет — только на главном
  [V:O8i7OKbWmRM 01:42, 03:06, 05:50]. Контраст «крадёт» взгляд — самое светлое место кадра = главное [V:O8i7OKbWmRM 04:17].
- Hero 16:9: объект на трети (shift_x ±0,15–0,2), противовес — заголовок в пустой трети [V:O8i7OKbWmRM 14:29]; мобильный
  9:16: объект в верхней или нижней половине, текст — в другой; иконка 1:1 — full frame [V:O8i7OKbWmRM 21:47], поле
  10–15 % (паспорт D2/04: высота объекта 44–63 % кадра).
- «Воздух»: объект 30–70 % площади кадра, поля 8–12 % (C1 `04 §3.1`, аудит `frame`); баланс — squint test (прищуриться/
  размыть) [V:O8i7OKbWmRM 25:06].
- Направляющие линии и повтор ведут к фокусу [V:O8i7OKbWmRM 06:12, 09:05].

## 6. Паспорт серии (проверенный, заменяет черновик ui-research `12-ai-generated-ui/01 §6.2`)

Поля и значения, проверенные на серии из 4 иконок (D2/04; было: орто-изометрия 30°, key 45° + fill 20 %, roughness 0,45,
тень альфа ≤ 0,15 — без проверки):

| поле | значение (иконки, светлая страница) | зачем |
|---|---|---|
| нормировка | радиус описанной сферы 0,5 м (масштаб корня) | одинаковый свет и тень при разных формах |
| камера | 85 мм, азимут 35°, угол места 25°, `frame_camera` поле 1,35 | единый ракурс; высота объекта 44–63 % кадра |
| свет | key/fill/rim от r, E_key 2 (Neutral) | тень разброс 0,9 L*, контраст 2,2 |
| мир | цвет фона страницы × 0,25 | заполнение без цветного каста |
| вид | Khronos PBR Neutral, look None, экспозиция 0 | брендовый C* 84–93 при hex 94,6 |
| материалы | primary + accent из палитры (roughness 0,3–0,35, coat 0,3), акцент ≤ 15–25 % площади | один «материальный язык» |
| фон | прозрачный + ловец теней (Cycles 32 + OIDN), 512–1024² | на любой фон страницы; 3–6 с на иконку |
| выход | PNG RGBA 8 бит → AVIF/WebP (`04-outputs-for-web.md`) | вес |
| имена | `icon-<name>-3d.png`, коллекция `ICON`, служебное — вне экспорта | порядок |

Результат (4 иконки, метрики по брендовому материалу): паспорт — L* освещённой грани 45,1–47,4 (hex 48,7), тень
39,7–40,6, C* 84–93; «наивно» (реальные размеры, разные камеры, солнце + мир 0,5, AgX) — L* 61–64, тень 53–60, C* 38–44
(фиолетовый выбелен до лаванды) [проверено: D2/04, `out/sheet_icons.png`]. Паспорт хранить в файле рядом со скриптом
(C1 `04 §3.1`), не в промте.

```python
# Blender 5.2.2 — [проверено] применить паспорт серии к ассету
import sys, math, bpy
from mathutils import Vector
sys.path.insert(0, "../../scripts/3d")
import bpyx

PASSPORT = {"radius": 0.5, "lens": 85, "az": 35, "el": 25, "margin": 1.35, "E_key": 2.0, "world": ("#F4F4F6", 0.25),
            "view": "Khronos PBR Neutral", "size": (512, 512)}

def apply_passport(objects, P=PASSPORT):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = P["size"]                 # аспект до кадрирования
    mn, mx = bpyx.world_bbox(objects); c = (mn + mx) / 2; k = P["radius"] / ((mx - mn).length / 2)
    root = bpy.data.objects.new("PassportRoot", None); bpyx.link(root); root.location = (c.x, c.y, mn.z)
    for o in objects:
        o.parent = root; o.matrix_parent_inverse = root.matrix_world.inverted()
    root.scale = (k, k, k); root.location = (0, 0, 0); bpy.context.view_layer.update()
    mn, mx = bpyx.world_bbox(objects); c = (mn + mx) / 2; r = (mx - mn).length / 2; d = 4 * r
    for name, az, el, share, sz in (("Key", 40, 45, 1.0, 2.0), ("Fill", -70, 15, 0.35, 3.0), ("Rim", 170, 50, 0.6, 1.5)):
        a, e = math.radians(az), math.radians(el)
        bpyx.add_light("AREA", name, c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d,
                       c, energy=math.pi * d * d * P["E_key"] * share, size=r * sz)
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = bpyx.color(P["world"][0]); bg.inputs["Strength"].default_value = P["world"][1]
    a, e = math.radians(P["az"]), math.radians(P["el"])
    cam = bpyx.add_camera(location=c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 6,
                          target=c, lens=P["lens"])
    bpyx.frame_camera(cam, objects, margin=P["margin"])
    bpyx.set_color_management(P["view"])
    return cam

bpyx.clear_scene()
parts = [bpyx.primitive("cube", "Box", size=1.2, location=(0, 0, 0.6)), bpyx.primitive("uvsphere", "Knob", radius=0.2, location=(0, -0.7, 0.9))]
cam = apply_passport(parts)
mn, mx = bpyx.world_bbox(parts); print(round((mx - mn).length / 2, 3), cam.data.lens)   # 0.5 85.0
```

## 7. Свет для веба: что запечь, что поставить на странице

| задача | решение | числа |
|---|---|---|
| статичная сцена/диорама | запечь свет целиком → unlit (`KHR_materials_unlit`) | ΔE 0,73 к Cycles (E `02 §6.1`) |
| PBR + статичный свет | lightMap во втором UV, `lightMapIntensity = π` | ΔE 0,74–0,89 (E `02 §6.2`) |
| интерактивный продукт | окружение (HDRI/`RoomEnvironment`) + 1–2 `DirectionalLight` кодом | F1 |
| лампы из Blender | `export_lights` + режим COMPAT (±2 %); Area и мир не экспортируются | E `01 §8.1` |
| контактные тени | AO в текстуру/цвет вершин (E `02 §5`) или тень-плоскость на странице | — |

Пара тонмаппинга и окружение на странице — у F1 (`../09-web-runtime/01-…`); для совпадения с предрендером — тот же HDRI
в `scene.environment` и Neutral на обеих сторонах (`03-render-engines-color.md` §2.3).

## Частые ошибки

1. Одно солнце или area 0,6 Вт на 6 м — плоский/тёмный свет (M3.4) → мощность от габарита (§1.2).
2. Мощность «как в bpyx» (900 Вт на 7 м) под Neutral — пересвет: это калибровка AgX (×2–3) [проверено].
3. Поднять key, чтобы осветлить фон → объект уходит в сжатие Neutral (12,5 → 44 % пикселей) [проверено].
4. Тёмный «киношный» мир на светлой странице (M3.6) → мир = фон страницы.
5. Плоскость-пол до горизонта → линия горизонта в кадре (M3.8) → циклорама.
6. `is_shadow_catcher` в EEVEE → тени нет (только Cycles).
7. `frame_camera` до установки разрешения → кадр под другой аспект [проверено].
8. Камера углами Эйлера «на глаз» → объект вне кадра (M3.7) → `frame_camera`/`to_track_quat`.
9. Детали сложного объекта поворачивать каждую вокруг своего центра → разъехалась сборка (M2.4) [проверено: D2/04, таблетка].
10. Цветные лампы и тёплый HDRI в кадре с брендом → цвет «плывёт» [V:0oIZoSg03PY 41:27].
11. Каждая иконка серии со своими светом, камерой и видом → разнобой и выбеленный бренд (M3.9) [проверено].

## Чек-лист

- [ ] Свет от габарита (d = 4r, `P = π·d²·E`), E_key под вид (Neutral 2–3, AgX 5–8)?
- [ ] У каждой лампы цель; key сбоку; размер источника выбран под мягкость?
- [ ] Светлый фон — своей лампой/альбедо, объект вне зоны сжатия (False Color)?
- [ ] Фон: циклорама цвета страницы или прозрачный + ловец (Cycles)?
- [ ] HDRI из Poly Haven нейтральный; в EEVEE для сравнений `sun_threshold = 0`?
- [ ] Разрешение задано до кадрирования; фокусное 70–100 мм для продукта; вертикали — `shift_y`?
- [ ] Кадр под формат: трети для hero, full frame для иконки, поле 10–15 %?
- [ ] Серия — по паспорту из файла (размер, камера, свет, вид, фон)?
- [ ] Для веба свет задаёт страница или он запечён?

## Открытые вопросы и противоречия

1. **Качество схем**: проверены на одной модели; уровень «аккуратно», не Awwwards — нужна итерация со светом фона и
   сильным контровым (не делалась из-за лимита).
2. **Калибровка** — одна модель и один фон; для тёмной темы (фон L* 10–20) и крупных сцен не проверена.
3. **Паспорт C1 (AgX + Punchy) против паспорта D2 (Neutral)**: замер D2/04 и D2/01 — Neutral держит бренд (C* 84–93 против
   38–44); AgX оставлен для атмосферных кадров (`03 §4`).
4. **HDRI для бренда**: обесцвечивание HDRI в мире Blender и предобработка HDR для three — не проверены.
5. **Изометрия** (орто 35,264°/45°) — [практика], отдельно не рендерилась.

## Источники

- [S1] Poly Haven. API `https://api.polyhaven.com/assets?t=hdris&c=studio`, `/info/<id>` — метаданные студийных HDRI
  (контраст, white balance, `evs_cap`, загрузки), CC0, без ключа; запрос 23.09.2026.
- [S2] [V:5UCc3Z_-ibs] A. Price (Blender Guru), «How to Make Studio Lighting in Blender», 2020 — дайджест W3.
- [S3] [V:Z8AAX-ENWvQ] A. Price, «The Secrets of Photorealism», BCon 2022 — дайджест W3.
- [S4] [V:O8i7OKbWmRM] A. Price, «Understanding Composition», 2014 — дайджест W3.
- [S5] [V:0oIZoSg03PY] E. Lalish (Khronos), PBR Neutral, 2024 — дайджест W3 (серый свет витрины, D65).
- [S6] [V:auTKRan7oPk], [V:zthvZvw-yJE] — через отчёты W3/W4 (`99-raw/reports/wave2-W3-report.md`, `wave2-W4-report.md`).
- [S7] Агент C1: `../04-ai-agents-mcp/04-agent-operating-protocol.md` §3.1, §5.5 (паспорт, свет 900 Вт × (d/7)²); `05` (M-коды).
- [S8] ui-research: `../../ui/12-ai-generated-ui/01-image-models-for-ui.md` §6.2 — черновик паспорта 3D-серии (заменён §6).

Эксперименты: `99-raw/experiments/D2/04-light-icons` (схемы, калибровка, иконки), `D2/01-brand-color` (IBL), `D2/02-engines`.
