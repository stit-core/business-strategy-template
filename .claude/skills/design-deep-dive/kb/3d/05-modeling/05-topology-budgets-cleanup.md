# Топология для веба: n-гоны, нормали, булевы с очисткой, трансформации, LOD, бюджеты и проверки перед экспортом

Волна 2 · агент D1 · 23.09.2026 · источники: эксперименты D1/01, D1/03, D1/05, D1/07 (вершины glTF, булевы, вогнутые n-гоны,
инстансы), E `../08-export-gltf/01 §4`, `03 §2, §6`, `04 §5` (`preflight`), B `../03-bpy-api/01 §6–§9`, C1 (коды M, аудит),
ролики Lampel/PzThree/Gambrell/Redd через W4 и заметки помощников · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0,
three r186. Все блоки `python` выполнены в напечатанном виде (`99-raw/experiments/D1/09-doc-snippets`).

## Выжимка для агента

1. **Вогнутые n-гоны экспортируются корректно**: звезда и П-образная грань — сумма площадей треугольников равна площади многоугольника, ориентация одна (экспортёр триангулирует через Blender, не веером). → §1.1 [проверено]
2. **N-гоны — только на плоских участках**: на кривой поверхности и под SubD/деформацией они дают артефакты затенения (перепад плотности у полюсов). → §1.2 [V:PAK5zQONgvs ≈18:09, 19:59] [V:MD1QmdqXRfc 07:21] [практика]
3. **Перед запеканием нормалей — Triangulate модификатором**: фиксирует разбиение, одинаковое при запекании и в движке. → §1.3 [V:PAK5zQONgvs ≈12:39] [практика]
4. **Острые рёбра — данными** (`set_sharp_from_angle`), гладкость — `shade_smooth()`: 34 нормали у цилиндра 32 без apply; модификатор «Smooth by Angle» без apply — 64 и «надутые» торцы. → §2.1 [проверено]
5. **Weighted Normal — последним, `keep_sharp=True`, после Bevel с `harden_normals`**; экспорт только с apply (иначе нормали теряются). Сила граней — атрибут `__mod_weightednormals_faceweight` (операторы edit mode в фоне не проходят poll). → §2.2 [проверено]
6. **Вершин glTF больше, чем в Blender**: каждая острая кромка и шов UV размножают вершину; flat ×1,5–3,7. Бюджет считай `gltf_vertex_estimate`, а не `len(me.vertices)`. → §2.3 [проверено]
7. **Булевы из кода — да, при условиях**: EXACT (умолчание 5.2.2), замкнутые меши, масштаб применён, резак одним мешем, затем Weld → limited dissolve 0,5° → нормали → острые рёбра → Bevel(harden) → WN. «Голые» FLOAT + «сгладить всё» — разводы по плоскостям. → §3 [проверено: D1/03; V:0T3QdLJOBF8 через W4]
8. **Плоская деталь с отверстиями — контуром через заливку кривой**, не булевыми: 4× быстрее, −12 % вершин glTF, n-гонов 0 (после сварки). → §3.2 [проверено]
9. **Для деформируемых частей булевы не годятся** — поток рёбер обрывается; только статичный hard-surface. → §3.3 [V:MD1QmdqXRfc 22:52 через W4] [практика]
10. **Меш из кривой, текста, SVG, метаболов — сварить и проверить на неманифолд** (без сварки 3 280 рёбер на решётке). → §4.1 [проверено]
11. **Масштаб объектов 1, повороты — в вершины**, если объект не анимируется поворотом; `transform_apply(scale=True)` применяет и location, и rotation (все флаги оператора True по умолчанию; проверено в 5.2.2) — только `bpyx.apply_transforms` или явные флаги. → §4.2 [проверено: C1/11, B]
12. **Origin = точка вращения в JS**: у двигающейся части — на оси (`set_origin`), у статичного ассета — центр основания или центр габарита по договорённости со страницей. → §4.3 [проверено]
13. **Отрицательный масштаб экспорт переносит верно** (зеркально, грани не вывернуты), но применять всё равно: физика, анимация и pivots в JS работают от узла. → §4.2 [проверено: E/10; практика]
14. **Нормали наружу и backface culling на замкнутых мешах**: в Blender по умолчанию всё двустороннее — вывернутые грани не видны до веба. → §4.4 [проверено: E/12; V:MD1QmdqXRfc 02:53]
15. **UV: одна развёртка для материала, вторая — для lightmap/AO**; ≤ 2 слоёв (three читает 4, лишние уходят в файл). Тела D1 (`loft_slab`, `lathe`, `sweep`) создают UV сами. → §5 [проверено: E/04; D1/_lib]
16. **LOD и упрощение**: стиль и low-poly — параметрами, не Decimate; LOD готовых/гладких мешей — Decimate с контролем глазами и ошибкой в мм или `gltf-transform simplify`/`gltfpack -si` только для статичных гладких мешей (морфы ломаются, IoU 0,82). → §6 [E/17; V:H1oNuKChsdU 26:17; V:7AR9-LxY6AQ 12:45 через W4] [не проверено в D1]
17. **Бюджеты архетипов по замерам D1**: иконка 2–7 тыс. треуг., продукт 2–5 тыс., скульптура 19–27 тыс., low-poly сцена < 1 тыс. — на порядок ниже порогов страницы (hero: телефон ≤ 50 тыс., десктоп ≤ 100 тыс. — A `../01-web-3d-landscape/02-when-3d-budgets-loading.md` §3.1; сцена первого экрана — до 50–100 / 200–300 тыс., E `../08-export-gltf/03-compression-textures-budgets.md` §6.5). → §7 [проверено: D1/02–07]
18. **Проверки перед экспортом — кодом**: `preflight()` E (материалы, UV, скрытые, shape keys + модификаторы) + проверки D1 (габарит, зазоры, неманифолд, n-гоны на кривых, сырые рёбра, масштаб, pivots, вершины glTF). → §8 [проверено: E/26, D1]

## 1. N-гоны и триангуляция

### 1.1. Вогнутые n-гоны в glTF (гипотеза E проверена)

Звезда из 10 вершин (одна грань) и П-образная грань из 8 вершин экспортированы пресетом E; индексы GLB разобраны: 8 и 6
треугольников, сумма |площадей| = площади многоугольника (0,002792 и 0,0044 м²), все треугольники одной ориентации —
перекрытий «веера» нет [проверено]. Экспортёр 5.2.40 использует триангуляцию Blender (loop triangles, корректную для
вогнутых), поэтому формулировку E «n-гон → веер» (`../08-export-gltf/01 §4.1`) следует читать как «k − 2 треугольника без
контроля качества разбиения». Контроль разбиения всё равно нужен для затенения и запекания (§1.2–1.3).

```python
# Blender 5.2.2 — [проверено] вогнутая грань → GLB → треугольники покрывают её без перекрытий
import sys, os, json, math, struct, tempfile; sys.path.insert(0, "../../scripts/3d")
import numpy as np, bpy, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
star = [(math.cos(2 * math.pi * i / 10) * (0.05 if i % 2 == 0 else 0.019),
         math.sin(2 * math.pi * i / 10) * (0.05 if i % 2 == 0 else 0.019)) for i in range(10)]
C = D.fresh_collection("NGON")
bpyx.mesh_object("Star", [(x, y, 0.0) for x, y in star], [tuple(range(10))], collection=C)
path = os.path.join(tempfile.mkdtemp(), "star.glb"); D.export_web(path, "NGON")
data = open(path, "rb").read(); ln = struct.unpack_from("<I", data, 12)[0]; j = json.loads(data[20:20 + ln]); off = 20 + ln + 8
def acc(i):
    a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]
    n = a["count"] * {"SCALAR": 1, "VEC3": 3}[a["type"]]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
    return np.frombuffer(data, dt, n, off + bv.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(a["count"], -1)
pr = j["meshes"][0]["primitives"][0]
tri = acc(pr["attributes"]["POSITION"])[acc(pr["indices"]).ravel()].reshape(-1, 3, 3)     # glTF: Blender XY → XZ
area = 0.5 * ((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 2] - tri[:, 0, 2]) - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 2] - tri[:, 0, 2]))
true = 0.5 * abs(sum(star[i][0] * star[(i + 1) % 10][1] - star[(i + 1) % 10][0] * star[i][1] for i in range(10)))
print(len(tri), round(float(np.abs(area).sum()), 7), round(true, 7))
assert len(tri) == 8 and abs(np.abs(area).sum() - true) < 1e-7 and len(set(np.sign(area))) == 1
```

### 1.2. Где n-гоны вредят

- Плоские крышки корпусов, торцы, плоские панели — n-гон безопасен и дешевле (крышки `loft_slab`, заливка кривых).
- На кривой поверхности, под Subdivision и в деформируемых зонах — артефакты затенения: не сами n-гоны и треугольники,
  а перепад плотности вершин у полюсов (3 ребра уплотняют, 5+ разрежают) [V:PAK5zQONgvs 19:59, ≈21:12–21:30]; «n-gons are not
  great on rounded surfaces» [≈18:09]; треугольники, n-гоны и полюса — на плоских участках [V:MD1QmdqXRfc 07:21] (через W4 и
  `D1-subnotes/videos-topology.md`) [практика].
- N-гоны не деформировать: разбиение пересчитывается каждый кадр [V:PAK5zQONgvs ≈17:42] (через W4).
- Автоматический признак D1: n-гон, у которого нормали углов расходятся больше 5° (неплоский), — флаг [мнение: порог не калиброван].

### 1.3. Фиксировать триангуляцию

Перед запеканием карты нормалей и экспортом ассета с запечёнными нормалями — модификатор Triangulate (Beauty) последним или
применённым: движок и запекатель видят одно и то же разбиение [V:PAK5zQONgvs ≈12:39–13:29] (через W4) [практика]. Для
ассетов без карт нормалей не обязательно (экспорт триангулирует сам, §1.1).

## 2. Нормали

### 2.1. Гладкость по углу

| Способ (5.2.2) | Где живёт | glTF без apply | glTF с apply |
|---|---|---|---|
| `me.shade_smooth(); me.set_sharp_from_angle(angle)` | атрибут `sharp_edge` (данные) | верно (34 нормали у цилиндра 32) | верно |
| `object.shade_smooth_by_angle` (оператор) | то же, модификатора нет | верно | верно |
| `object.shade_auto_smooth` / ассет «Smooth by Angle» | модификатор NODES | неверно (64, «надутые» торцы) | верно (130 вершин = данные) |
| custom normals (`harden_normals`, WN, `normals_split_custom_set`) | `custom_normal` | только применёнными | верно |

[проверено: E/03, E/25; D1/_lib t08]. `use_auto_smooth` удалён в 4.1 (B №21); угол 30° — значение Blender; «35°» у DECODED —
ошибка ролика (W4 §4).

### 2.2. Weighted Normal

Стек: Bevel (`harden_normals=True`, фаска 1–3 %) → Weighted Normal (`keep_sharp=True`, `mode='FACE_AREA'`, `weight=50`)
последним [проверено: D1/01 C — чистые плоскости у выреза, 956 треуг./854 вершины]. Для WN нужна хотя бы фаска на кромках,
плоским граням — Face Strength = Strong [V:MD1QmdqXRfc 20:45–21:38]; из кода — атрибут
`__mod_weightednormals_faceweight` (значение 16384 = Strong), оператор `mesh.mod_weighted_strength` в фоне не проходит poll —
замер W4 `99-raw/experiments/W4/03_face_strength_attr.py` [проверено W4].

### 2.3. Цена нормалей в вершинах glTF

| Случай | Вершин Blender → glTF | Источник |
|---|---|---|
| блок без фасок, flat | 128 → 360 | D1/01 A |
| тот же, гладкий + острые рёбра | 128 → 244 | D1/01 B |
| фаска 3 сегм. + harden + WN | → 854 при 956 треуг. | D1/01 C |
| UV-сфера 48 × 24 гладкая / flat | 1 106 → 1 223 / 4 512 | E/03 |
| решётка: булевы / контур | 4 920 → 9 846 / 8 653 | D1/03 |

`d1lib.gltf_vertex_estimate(ob)` считает уникальные (позиция, нормаль угла, UV0) по вычисленному мешу — совпало с GLB в D1/01
до вершины (360, 244, 854, 695) [проверено].

## 3. Булевы операции: техническая позиция для агента-кодера

### 3.1. Спор и позиция

VideoSmile (Артём Слаква) — булевы вредят обучению моделированию; Josh Gambrell (Blender Bros) — строит hard-surface на булевых
с опорной топологией, Weld и Weighted Normal [V:0T3QdLJOBF8 03:43, 11:49]; PzThree — «boolean + n-gon» как отдельный процесс для
статики и запекания, не для деформации [V:MD1QmdqXRfc 22:52]; Lampel — булевы из примитивов → ремеш → ретопология как быстрый
путь к сложной форме [V:PAK5zQONgvs ≈43:09] (через W4 §4). Вопрос «учиться ли на булевых» к агенту не относится; позиция
D1 для кода — по эксперименту D1/03 (решётка 7 × 7 отверстий Ø 4 мм в пластине 60 × 60 × 4 мм):

| Путь | Треуг. | Вершин glTF | КБ | Время | Вид |
|---|---|---|---|---|---|
| «по памяти»: Boolean FLOAT, без очистки, `shade_smooth` всего | 3 472 | 4 850 | 173 | — | разводы по всей пластине (M3.3) |
| EXACT + Weld + limited dissolve + острые рёбра + Bevel 0,4 мм × 2 + WN | 10 032 | 9 846 | 368 | 0,7–2,2 с | чисто; 17 n-гонов на плоскостях; неманифолда 0 |
| контур с отверстиями (заливка кривой) + сварка | 10 032 | 8 653 | 331 | 0,2–0,6 с | чисто; n-гонов 0 |

Позиция: (1) статичный hard-surface — булевы допустимы, но только EXACT и с очисткой (`d1lib.boolean_apply`); (2) плоские детали
с вырезами — контур с отверстиями; (3) деформируемые части и SubD-формы — bmesh-построение с опорными петлями (файл 02),
без булевых; (4) перфорация ≥ 20–30 отверстий — карта на простой пластине [мнение D1].

```python
# Blender 5.2.2 — [проверено] «голые» булевы против EXACT с очисткой
import sys; sys.path.insert(0, "../../scripts/3d")
import bpy, bmesh, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
def plate_and_cutter(tag):
    C = D.fresh_collection("B_" + tag)
    plate = D.rounded_slab("Plate_" + tag, 0.06, 0.06, 0.004, 0.008, 0.0, C, corner_seg=8, smooth_angle=None)
    cut = bpyx.primitive("cylinder", "Cut_" + tag, radius=0.004, depth=0.02, segments=24, collection=C)
    cut.location = (0.0, 0.0, 0.002)
    return plate, cut
naive, c1 = plate_and_cutter("naive")
bpyx.add_modifier(naive, "BOOLEAN", operation="DIFFERENCE", solver="FLOAT", object=c1)
bpyx.apply_modifiers(naive); bpy.data.objects.remove(c1, do_unlink=True)
naive.data.shade_smooth()                                           # «сгладить всё» — без острых рёбер
clean, c2 = plate_and_cutter("clean")
rep = D.boolean_apply(clean, [c2], solver="EXACT")                  # Weld → dissolve → нормали → острые рёбра 30°
D.hard_surface(clean, bevel_width=0.0004, segments=2, angle=30)
def sharp_count(o):
    return sum(1 for d in o.data.attributes["sharp_edge"].data if d.value) if "sharp_edge" in o.data.attributes else 0
print(rep, sharp_count(naive), sharp_count(clean))
assert rep["nonmanifold"] == 0 and sharp_count(naive) == 0 and sharp_count(clean) > 0
```

### 3.2. Опорный разрез и чистка

Перед булевым — опорный разрез через центр будущего выреза (чтобы вокруг отверстия были рёбра, а не длинные треугольники);
после — Boolean → Bevel → Weld → WN [V:0T3QdLJOBF8 03:43, 11:49] (через W4) [практика]. В коде D1 роль «чистки» выполняет
`boolean_apply`: `remove_doubles(1e-5)`, `dissolve_limit(0,5°, delimit NORMAL)`, `dissolve_degenerate`, `recalc_face_normals`,
острые рёбра 30° [проверено: D1/03, D1/_lib t09]. Самопересечения после булевых видно в оверлее Face Orientation только как
изнанку, не как пересечение (W4 §4).

### 3.3. Когда не булевы

Деформация (скиннинг, морфы), SubD-поверхности (обрыв потока рёбер), ретопология под анимацию — bmesh-построение по профилям
(`loft_slab`, `lathe`, `sweep`) или ремеш + ретопология (Lampel) [практика].

## 4. Чистота меша и трансформации

### 4.1. Неманифолд и сварка

Меш из кривой, текста и SVG (`new_from_object`) приходит несваренным по швам заливки и фаски: решётка 7 × 7 — 3 280
неманифолдных рёбер; `weld_mesh(me, 1e-6)` → 0 [проверено]. Метаболы и SDF дают манифолд сразу [проверено: D1/06, t07].
Для веба неманифолд не ломает отрисовку (Lampel: герметичность «не нужна» кроме печати — W4 §4), но ломает Solidify, булевы,
запекание и считается флагом аудита (`scene_audit.py` C1/10) — сваривать всегда [мнение D1].

### 4.2. Масштаб, повороты, отрицательный масштаб

- Размеры — в вершинах (`bmesh`, `me.transform`), масштаб объекта 1 (M2.10); проверка — `bpyx.object_stats(ob)["scale_applied"]`
  [проверено: все объекты D1].
- `bpy.ops.object.transform_apply(scale=True)` применяет и location, и rotation (все флаги оператора по умолчанию True; проверено в 5.2.2) — pivots
  уезжают в ноль мира (M1.9); применять `bpyx.apply_transforms(ob, rotation=True, scale=True)` (location остаётся pivot'ом,
  дети не сдвигаются) [проверено: C1/11, B t09, D1/02].
- Отрицательный масштаб экспортёр переносит зеркально без вывернутых граней (E/10), но физика и анимация в JS работают от
  узла — применять [практика E].

### 4.3. Origin и pivots

Origin = точка вращения и масштабирования в three (E `01 §4.9`). Правила D1: статичный ассет — pivot в центре основания
(стоит на полу страницы) или в центре габарита (вращение «на месте») — по договорённости со страницей; двигающаяся часть —
на оси (петля, сустав, ось колеса: `set_origin`); деталь для взрыв-схемы — в центре детали (A `05 §3.5`); группа — пустышка-корень
(`Phone` в D1/02) [проверено].

```python
# Blender 5.2.2 — [проверено] применить поворот и масштаб, не трогая pivot; pivot на ось
import sys, math; sys.path.insert(0, "../../scripts/3d")
import bpy, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
ob = bpyx.primitive("cube", "Door", size=1.0)
ob.location = (0.4, 0.0, 0.5); ob.rotation_euler = (0, 0, math.radians(30)); ob.scale = (0.8, 0.04, 1.0)
bpy.context.view_layer.update()
before = [ob.matrix_world @ v.co for v in ob.data.vertices]
bpyx.apply_transforms(ob, rotation=True, scale=True)               # НЕ transform_apply(scale=True): тот двигает и location
after = [ob.matrix_world @ v.co for v in ob.data.vertices]
assert all((a - b).length < 1e-6 for a, b in zip(before, after))  # мир не сдвинулся (float32 — допуск, не ==)
assert tuple(ob.scale) == (1, 1, 1) and abs(ob.location.x - 0.4) < 1e-6
hinge = min((ob.matrix_world @ v.co for v in ob.data.vertices), key=lambda p: (p.x, p.y))   # «левый» край двери
D.set_origin(ob, (hinge.x, hinge.y, 0.5))                          # pivot на ось петли (вертикаль через край)
print(tuple(round(c, 4) for c in ob.location), bpyx.object_stats(ob)["scale_applied"])
```

### 4.4. Нормали наружу и двусторонность

После ручных граней — `bmesh.ops.recalc_face_normals` (все построители D1 делают это сами). В Blender по умолчанию backface
culling выключен → вывернутые грани не видны, а glTF-материал уходит `doubleSided` (E `01 §5.5`); для замкнутых мешей включать
`use_backface_culling` [проверено: E/12; V:MD1QmdqXRfc 02:53 через W4].

## 5. UV

- Тела D1 создают UV при построении: `loft_slab` (боковина — длина контура × длина профиля, крышки — планарно), `lathe`
  (угол × длина профиля), `sweep` (длина пути × периметр сечения), экран мокапа — 0–1 на всю область [проверено: D1/_lib, D1/02].
- Для запекания — развёртка без перекрытий (`bpyx.uv_unwrap(ob, "SMART"/"LIGHTMAP")` в фоне; CUBE перекрывает острова) и
  второй слой для lightmap/AO; ≤ 2 слоя (E `01 §4.3`, `02`).
- Нетекстурный меш: `export_texcoords=False` или `gltf-transform prune` — UV без текстур раздувают файл (8 байт/вершину и
  швы +10 % вершин, E/03, E/22) [проверено E].
- UV «под метры» (1 UV = 1 м²) — для материалов из библиотек (Essentials) [V:QkIr1-lDPW0 02:37 через W3] [практика].

## 6. LOD и упрощение

Эксперимент D1 с LOD снят по решению заказчика (экономия) — раздел по E и роликам, `[не проверено в D1]`.

| Инструмент | Что делает | Замер/источник | Когда |
|---|---|---|---|
| модификатор Decimate COLLAPSE (`ratio`, `use_symmetry`, `delimit`) | схлопывание рёбер в Blender, под глазом | E: «упрощать в Blender (Decimate/ремеш с контролем глазами)» `03 §2.5` | LOD готовых гладких мешей, сканов, генераторов |
| Decimate UNSUBDIV / DISSOLVE (планарный, `angle_limit` 5°) | обратное подразделение / слияние плоскостей | RNA 5.2.2 (D1/00) | квад-сетки после SubD; плоские булевы |
| `gltf-transform optimize` (simplify по умолчанию, ошибка 0,0001) / `simplify --ratio` | meshoptimizer | c1 252k → 94k, ΔE 0,26; меняет тонкие детали | статичные гладкие меши с запасом |
| `gltfpack -si 0.5` | meshoptimizer | 252k → 126k; морф-меш — IoU 0,82 в позе | только без морфов и скиннинга |

Правила: стиль и low-poly — параметрами построения («please don't hit decimate» [V:H1oNuKChsdU 26:17]); LOD и доводка
сгенерированных/сканированных ассетов — автоматикой с метрикой ошибки аппроксимации в мм (средняя, p95, max) и проверкой
силуэта [V:7AR9-LxY6AQ 12:45] (через W4); для сцен с JS-логикой — `--simplify false` (E `03 §4.1`). Порог ошибки для hero —
≤ 0,5 мм на 10-см предмете (≈ 0,5 %) [мнение D1, не калибровано].

## 7. Бюджеты

### 7.1. Замеры D1 по архетипам (GLB пресетом E, до и после meshopt)

| Ассет | Треуг. | Вершин glTF | GLB | meshopt |
|---|---|---|---|---|
| корпус-блок с фаской 3 сегм. + WN | 956 | 854 | 34 КБ | — |
| кейс наушников (3 части) | 1 976 | 1 227 | 53 КБ | — |
| мягкие иконки (3) | 2 384–6 848 | 1 534–3 716 | 58–160 КБ | — |
| телефон-мокап (10 мешей, картинка экрана) | 4 826 | 3 412 | 153 КБ | — |
| логотип SVG (res 16) / текст «Nova» (6/2) | 2 556 / 2 472 | 1 860 / ≈ 2 000 | 74 КБ / — | — |
| скульптура-лента / SDF-капля | 26 400 / 18 788 | 13 930 / 9 598 | 593 / 346 КБ | 117 / 79 КБ |
| low-poly остров, 25 инстансов | 184 (788 развёрнуто) | 416 | 19 КБ (69 КБ Realize) | — |

[проверено: D1/01–07]. Сырой GLB из Blender не выкладывать: meshopt + квантование дают ×4–5 (D1/06) — ×20 (E/17) (E `03 §2`).

### 7.2. Пороги страницы (E, A) и позиция D1

| Параметр | Телефон, первый экран | Десктоп, первый экран | Источник |
|---|---|---|---|
| 3D по сети (brotli) | ≤ 1–1,5 МБ | ≤ 3 МБ (hero ≤ 1,5 МБ по A) | E `03 §6.5`; A `02 §3.1` [спорно A ↔ E] |
| треугольники в кадре | ≤ 50–100 тыс. | ≤ 200–300 тыс. (hero ≤ 100 тыс. по A) | там же |
| draw calls | ≤ 15–30 | ≤ 30–50 | E |
| материалы | ≤ 5–10 | ≤ 10–20 | E |
| hero-ассет по протоколу C1 | ≤ 300 КБ сжатого, ≤ 50 тыс. треуг., ≤ 8 материалов, ≤ 10 вызовов | | C1 `04 §9` |

Позиция D1: архетипы §7.1 укладываются в 20–600 КБ и ≤ 27 тыс. треуг. — бюджет формы почти никогда не упирается в
треугольники, упирается в текстуры (E: 9 карт 2k = 192 МБ GPU) и в число мешей/материалов (draw calls). Дорогие приёмы формы:
перфорация и мелкие повторы (решётка 10 тыс.), ленты и блобы (19–27 тыс.), SubD без применения уровня (×4 на уровень),
текст с умолчаниями (6,9 тыс. на слово) [проверено].

## 8. Автоматические проверки перед экспортом

Порядок: (1) исключения скрипта → (2) проверки формы D1 (габарит, зазоры, иерархия, сырые рёбра — файл 01 §7) → (3)
чистота меша (неманифолд, n-гоны на кривых, масштаб, pivots, нормали) → (4) `preflight()` E (процедурные материалы, UV,
скрытые объекты, shape keys + модификаторы, текст с высоким разрешением, свет) → (5) экспорт пресетом E → (6) `gltf_check.py`
(валидатор + inspect) → (7) `web_view.py` (C1 `04 §9`, E `04 §1`).

```python
# Blender 5.2.2 — [проверено] чистота меша (D1) + preflight() агента E перед экспортом
import sys, json, math; sys.path.insert(0, "../../scripts/3d")
import bpy, bmesh, d1lib as D, bpyx
bpy.ops.wm.read_factory_settings(use_empty=True)
C = D.fresh_collection("ASSET_hero")
body = D.rounded_slab("Body", 0.12, 0.08, 0.03, 0.02, 0.006, C, power=2.4)
logo = D.text_mesh("Logo", "D1", C, size=0.02, extrude=0.002, bevel=0.0004, resolution_u=4)
logo.location = (0, -0.04, 0.008)
bad = bpyx.primitive("cube", "Leftover", size=0.02, collection=C); bad.scale = (2, 1, 1)   # заложенная ошибка

def mesh_checks(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    curved_ngons = sum(1 for f in bm.faces if len(f.verts) > 4 and max(
        math.degrees(f.normal.angle(l.vert.normal, 0.0)) for l in f.loops) > 5 and f.smooth)
    bm.free()
    st = bpyx.object_stats(ob)
    return {"nonmanifold": nonman, "curved_ngons": curved_ngons, "scale_applied": st["scale_applied"],
            "gltf_verts": D.gltf_vertex_estimate(ob)["gltf_verts_est"]}
rep = {o.name: mesh_checks(o) for o in C.objects if o.type == "MESH"}
exec(open("../../scripts/3d/preflight_block.py").read())
pf = [(lvl, code, obn) for lvl, code, obn, msg in preflight()]          # функция агента E (08-export-gltf/04 §5)
print(json.dumps(rep), pf)
assert rep["Body"]["nonmanifold"] == 0 and rep["Logo"]["nonmanifold"] == 0
assert not rep["Leftover"]["scale_applied"] and ("INFO", "UNAPPLIED_SCALE", "Leftover") in pf
```

## Частые ошибки

1. **«N-гоны экспортируются веером и ломаются»** — нет, вогнутые n-гоны экспортируются верно; реальная проблема n-гонов —
   затенение на кривых и деформация [проверено].
2. **`transform_apply(scale=True)` для «применить масштаб»** — pivots уезжают в ноль мира (M1.9) [C1/11].
3. **Weighted Normal / «Smooth by Angle» без применения при экспорте** — нормали и острые рёбра теряются [E/03].
4. **Булевы FLOAT + `shade_smooth` всего** — разводы (M3.3) [проверено].
5. **Меш из кривой без сварки** — неманифолд [проверено].
6. **Бюджет по `len(me.vertices)`** — glTF в 1,5–3,7 раза больше [проверено].
7. **Decimate для «стиля low-poly»** — рваная стилистика; сегменты — параметрами [V:H1oNuKChsdU 26:17].
8. **`gltf-transform optimize` с умолчаниями на сцене с частями** — join/flatten/simplify сливают и упрощают (M5.6) [E/17].
9. **UV «на всякий случай» на нетекстурных мешах и 3+ UV-слоя** — вес и ошибки шейдера (E/04).
10. **Вывернутые нормали, скрытые двусторонностью** — в вебе дыры при `doubleSided=false` [E/12].

## Чек-лист

- [ ] N-гоны только на плоских участках; перед запеканием нормалей — Triangulate?
- [ ] Острые рёбра данными; WN последним с `keep_sharp`; экспорт с apply?
- [ ] Бюджет посчитан по вершинам glTF (`gltf_vertex_estimate`), а не Blender?
- [ ] Булевы: EXACT + очистка; плоские вырезы — контуром; деформируемое — без булевых?
- [ ] Меши из кривых/текста/SVG сварены, неманифолда 0?
- [ ] Масштаб 1, повороты в вершинах (`apply_transforms`), pivots на осях двигающихся частей?
- [ ] Нормали наружу, backface culling на замкнутых мешах?
- [ ] UV: есть у текстурных, нет у нетекстурных, ≤ 2 слоя?
- [ ] LOD — Decimate с ошибкой в мм или simplify только для статичных гладких мешей?
- [ ] Треугольники и КБ архетипа — в таблице §7, страница — в пределах E/A?
- [ ] Проверки D1 + `preflight()` E зелёные до экспорта; после — `gltf_check.py` и `web_view.py`?

## Открытые вопросы и противоречия

- LOD (Decimate против simplify с ошибкой в мм) и контур inverted hull в D1 не проверены — эксперимент снят по решению
  заказчика; кандидат для J/K (волна 3). `[не проверено]`
- Флаг «n-гон на кривой» (разброс нормалей углов > 5° у гладкой грани) — порог D1 без калибровки. `[мнение]`
- Порог ошибки LOD ≤ 0,5 % размера предмета — не калиброван. `[мнение]`
- Формулировка E «n-гон уходит веером» (`../08-export-gltf/01 §4.1`) расходится с D1/05 (вогнутые — корректно) — для аудитора X:
  править у E на «k − 2 треугольника через триангуляцию Blender».
- Бюджеты hero: A ≤ 1,5 МБ / 100 тыс. против E ≤ 3 МБ / 200–300 тыс. — `[спорно]` (PLAN, контрольная точка волны 1).

## Источники

- [S1] Эксперименты D1: `99-raw/experiments/D1/01-normals-bevel`, `03-product-hinge-grille`, `05-logo-text-ngons`, `07-lowpoly-gn-data`,
  `_lib/test_d1lib.py` [проверено].
- [S2] E: `../08-export-gltf/01-export-contract.md` §4 (триангуляция, нормали, UV, трансформации), §5.5; `03-compression-textures-budgets.md`
  §2, §4, §6; `04-validation-pitfalls-presets.md` §5 (`preflight`, код `../../scripts/3d/preflight_block.py`) [проверено E].
- [S3] B: `../03-bpy-api/01-data-model-and-basics.md` §6.7, §9; `03-version-drift-3.6-to-5.2.md` №21–24 [проверено B].
- [S4] C1: `../04-ai-agents-mcp/04-agent-operating-protocol.md` §6, §9; `05-failure-modes-catalog.md` (M1.9, M2.x, M3.3, M5.6);
  `../../scripts/3d/scene_audit.py` [проверено C1].
- [S5] A: `../01-web-3d-landscape/02-when-3d-budgets-loading.md` §3.1, `05-blender-deliverables-map.md` §3.5 [практика A].
- [S6] Jonathan Lampel, «Building Good Topology and Retopology», BCon 2024, https://www.youtube.com/watch?v=PAK5zQONgvs — через
  `D1-subnotes/videos-topology.md` и W4 [практика].
- [S7] PzThree, «Blender - Topology Fundamentals», 2023, https://www.youtube.com/watch?v=MD1QmdqXRfc — там же [практика].
- [S8] Josh Gambrell (Blender Bros), «How to fix artifacts in Blender», 2020, https://www.youtube.com/watch?v=0T3QdLJOBF8 — через W4 §8 [практика].
- [S9] Ethan Redd, «Low Poly Modeling: Style Through Economy», GDC 2017, https://www.youtube.com/watch?v=H1oNuKChsdU [практика].
- [S10] Vilém Duha, «A new approach to Retopology», BCon 2023, https://www.youtube.com/watch?v=7AR9-LxY6AQ — через W4 (ошибка в мм) [практика].
- [S11] W4 (волна 2): отчёт `99-raw/reports/wave2-W4-report.md` §4, §8; замеры `99-raw/experiments/W4/` [проверено W4].
