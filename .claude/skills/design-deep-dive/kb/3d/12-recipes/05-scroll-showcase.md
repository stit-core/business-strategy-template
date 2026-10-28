# 05 · Витрина продукта на прокрутке: раскрытие по частям клипом Blender (скраб) и путь камеры

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, three r186 · сквозной прогон:
[проверено] · страница: [проверено] · пример:
`examples/05-scroll-showcase/`

## Выжимка рецепта

1. Хореография частей (крышка, вложения) — **клип Blender**; простое движение одного объекта — JS (H `07/04 §1`) [проверено: H].
2. **Одно действие со слотами на все части = один клип glTF** со стаггером; отдельные действия на части сдвигаются к 0 и теряют
   стаггер; NLA-дорожка с 2+ полосами молча выпадает [проверено].
3. Подвижная часть — отдельный объект с **pivot на оси** (петля крышки — `D.set_origin`), до ключей [проверено: D1/03, рецепт 01].
4. Экспорт — пресет E `anim_trs`: сэмплирование (`export_force_sampling`), `export_anim_slide_to_zero`; без сэмплов поворот ≥ 180°
   ломается; `optimize --flatten false --join false` — части адресуемы [проверено: H/12, E/24, этот прогон].
5. **Скраб**: `action.play()` один раз; каждый кадр `action.time = p · duration; mixer.update(0)`; `p = damp(p, target, 10, dt)`;
   рендер только пока догоняем; рецепт `paused + mixer.setTime` даёт кадр 0 (ошибка каталога A) [проверено: H/20, H/21, этот прогон].
6. Reduce: без промежуточных поз — сразу «закрыто»/«открыто» по порогу 0,5 [проверено].
7. Путь камеры по сцене — кривая Blender → JSON `[x, z, −y]` → `CatmullRomCurve3.getPointAt(u)`: 1,4–2,7 КБ вместо запечённой камеры
   (F2 `../09-web-runtime/examples/camera-path-scroll`, H/14) [проверено].

## 1. Бриф-пример и границы

«Второй экран лендинга наушников: при прокрутке кейс открывается, наушники поднимаются по очереди; подписи меняются по шагам».

| годится | не годится → куда |
|---|---|
| 2–6 частей двигаются согласованно, 1–3 с клипа | фильм на 20 с с деформациями → секвенция кадров/видео all-intra (рецепт 08) |
| прокрутка = время истории (скраб) | автопроигрывание без управления → клип `LoopOnce` по событию или видео |
| три/одна сцена на странице | 5+ сцен по секциям → кампания (A `01/02 §7`): прогрессивная загрузка, отдельный GLB на секцию |

## 2. Паспорт

Кейс рецепта 01 (тот же `build(P)`, pivot крышки на петле) + два «наушника» (сфера Ø 17 мм + стержень Ø 6 × 20 мм), утопленные в
базу на 60 %. Клип «Reveal» 30 fps: крышка 0 → −105° (кадры 1–24, BACK ease-out, back 1,2); наушники +30 мм со стаггером 6 кадров
(16–36 и 22–42). Страница: 3 экрана прокрутки = весь клип, `damp` λ = 10.

## 3. Код: build(P) → одно действие со слотами → GLB с клипом

```python
# Blender 5.2.2 — [проверено] рецепт 05: кейс рецепта 01 + клип «Reveal» (слоты — 3d 07/03 §1.2)
import sys, math, bpy, bmesh
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py и animx.py — scripts/3d
import rk, animx
D, bpyx = rk.D, rk.bpyx
SLUG = "05-scroll-showcase"
P = dict(W=0.0606, D=0.0217, H=0.0452, corner=0.0105, edge=0.0085, power=2.6, seam_z=0.0335, gap=0.0003,
         body="#F4F3F0", bud_r=0.0085, stem=(0.003, 0.020), lift=0.030, open_deg=105, fps=30)


def split_by_z(ob, z, keep_above):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z),
                                 plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
    bmesh.ops.edgeloop_fill(bm, edges=[e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()
    ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(35))


def build(P):
    C = D.fresh_collection("ASSET_case_reveal")
    body = rk.web_material("Case_Plastic", "plastic_gloss", P["body"])
    base = D.rounded_slab("Case_Base", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), C,
                          corner_seg=10, edge_seg=8, power=P["power"])
    lid = bpy.data.objects.new("Case_Lid", base.data.copy()); C.objects.link(lid)
    split_by_z(base, P["seam_z"] - P["gap"] / 2, keep_above=False)
    split_by_z(lid, P["seam_z"] + P["gap"] / 2, keep_above=True)
    D.set_origin(lid, (0, P["D"] / 2 - 0.0012, P["seam_z"]))                       # pivot — ось петли
    buds = []
    for i, x in enumerate((-0.014, 0.014)):
        bud = bpyx.primitive("uvsphere", f"Bud_{i}", radius=P["bud_r"], segments=32, rings=16, collection=C)
        stem = bpyx.primitive("cylinder", f"Bud_{i}_Stem", radius=P["stem"][0], depth=P["stem"][1], segments=24, collection=C)
        stem.location = (0, 0, -P["stem"][1] / 2)
        stem.parent = bud
        bud.location = (x, 0, P["seam_z"] - P["gap"] - P["bud_r"] * 0.2)                # утоплен в базу на 60 %
        buds.append(bud)
    for o in [base, lid] + buds + [b.children[0] for b in buds]:
        bpyx.assign_material(o, body)
    return C, base, lid, buds


def key_reveal(lid, buds, P):
    act = animx.new_action("Reveal", [lid, *buds])                      # ОДНО действие со слотами → один клип glTF
    lid.rotation_mode = "XYZ"
    animx.key(lid, "rotation_euler", 1, 0.0, index=0)
    animx.key(lid, "rotation_euler", 24, math.radians(-P["open_deg"]), index=0)
    for kp in animx.fcurves(lid)[0].keyframe_points[:1]:
        kp.interpolation = "BACK"; kp.easing = "EASE_OUT"; kp.back = 1.2
    for i, b in enumerate(buds):
        f0, z0 = 16 + 6 * i, b.location.z                                            # стаггер 6 кадров
        animx.key(b, "location", f0, z0, index=2)
        animx.key(b, "location", f0 + 20, z0 + P["lift"], index=2)
    bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, 42
    bpy.context.scene.render.fps = P["fps"]
    return act


rk.reset()
C, base, lid, buds = build(P)
act = key_reveal(lid, buds, P)
assert len(act.slots) == 3, [s.identifier for s in act.slots]
bpy.context.scene.frame_set(42)
mn, mx = bpyx.world_bbox([b for b in buds])
assert mn.z > P["seam_z"] - 0.012, mn.z                                   # наушники поднялись над швом
bpy.context.scene.frame_set(1)
res = rk.ship(SLUG, "ASSET_case_reveal", "case_reveal", preset="anim_trs", optimize="meshopt", keep_names=True)
j = rk.DX.glb_info(f"{rk.out_dir(SLUG)}/case_reveal.glb")
rk.save(SLUG, slots=[s.identifier for s in act.slots], passport=P)
```

## 4. Страница: прокрутка → время клипа

`examples/05-scroll-showcase/index.html` — страница H/21 без изменений логики: меняются имя GLB и камера (кадр по габариту вместо
чисел H — кейс 6 см, а сцена H/12 в метрах). Ядро (как в H/21):

```js
// three r186 — [проверено] скраб клипа прокруткой без заворота конца в 0
const clip = THREE.AnimationClip.findByName(gltf.animations, 'Reveal');   // clipAction('Reveal') на gltf.scene вернёт null
const action = mixer.clipAction(clip); action.play();                     // один раз; время дальше задаём сами
function draw() { action.time = current * clip.duration; mixer.update(0); renderer.render(scene, camera); }
// цикл: target = прогресс секции (getBoundingClientRect), current = damp(current, target, 10, dt),
// reduce → current = target < 0.5 ? 0 : 1; requestAnimationFrame только пока |current − target| > 1e-4
```

Подписи шагов — HTML (`position: sticky`), canvas `aria-hidden`; GSAP ScrollTrigger + Lenis — если уже есть на сайте, дают только
прогресс (F2 `09/03 §2`, лицензия GSAP — там же).

## 5. Числа прогона

Blender 0,4 с (сборка, ключи, экспорт `anim_trs`, meshopt). Итераций — 1: `ActionSlot.name` в 5.2 **нет** (AttributeError) — имя слота
`slot.identifier` («OBCase_Lid») или `slot.name_display`.

| величина | значение |
|---|---|
| действие «Reveal» | 3 слота (`OBCase_Lid`, `OBBud_0`, `OBBud_1`); экспортёр: «Baking animation because of an unsupported interpolation method: BACK» — BACK запекается в сэмплы (как H/12) |
| GLB: экспорт → meshopt | **104,9 → 25,9 КБ**; 1 клип; 6 мешей (узлов 6 → 9: квантование добавляет дочерние узлы, E/24); валидатор 0 / 0 |
| страница (`web_view.py --page`, прокрутка 0 / 0,3 / 0,55 / 0,8) | закрыт → крышка открыта → первый наушник выше → оба подняты; **6 вызовов**, 60 fps (p95 16,7 мс), 0 ошибок; 468 КБ (JS 437 с CDN, модель 26) |
| эталон H/21 (своя сцена) | 39,9 КБ, 7 вызовов, 60 fps, reduce — 0/1 без промежуточных поз [проверено] |

Взгляд на `99-raw/experiments/K/07-scroll-page/page_sheet.png`: стаггер виден (первый наушник выше второго на 0,55), крышка
открывается с перелётом BACK, ни одна часть не проходит сквозь корпус. Слабее: белое на светло-сером — низкий контраст; для витрины —
тёмный фон или цветной корпус.

## 6. Ворота

`len(action.slots) == 3` (одно действие на все части), наушники выше шва на последнем кадре — `assert`; в three — 1 клип с нужным
именем; прокрутка: 0 вызовов в покое (кадр только при изменении), reduce без промежуточных поз, 60 fps; вес ≤ 0,8 МБ; для страницы —
`gate_check()` рецепта 01.

## 7. Варианты

1. **Путь камеры по сцене** вместо клипа предмета: кривая Безье в Blender → `D.export_curve_json(name, path, samples=96)` →
   `CatmullRomCurve3.getPointAt(u)`, взгляд — точка впереди; готовая страница F2 `../09-web-runtime/examples/camera-path-scroll/`
   (GLB 33 КБ, JSON 2,7 КБ, hover по именам узлов, 0 вызовов в покое, 60 fps) [проверено]; JSON-кривая 1,4 КБ отличается от
   запечённой камеры на 8 мм / 0,1° (H/14).
2. **Idle-движение** после раскрытия — второй клип на корне (NLA-дорожка ровно с одной полосой) или JS-покачивание (H `07/01 §5`).
3. **Раскрытие без прокрутки** (по клику) — `action.setLoop(THREE.LoopOnce)`, `clampWhenFinished = true`, событие `finished` (H `07/03 §3`).
4. **Много секций** — секция = свой GLB и клип, загрузка при приближении (`IntersectionObserver`, `rootMargin`), один renderer.
5. **Секвенция кадров** вместо GLB (рецепт 08): точная картинка Cycles, 1–5 МБ, без интерактива.
6. **NLA-трюк** (одинаковое имя дорожек NLA у частей → один клип, режим `NLA_TRACK`) [V:KTPdNUGwIGc 28:05] — в 5.2.2 работает
   (H/12 вариант C: один клип 1,567 с, сдвиги сохранены), но одно действие со слотами (вариант A, этот рецепт) проще и не зависит от
   NLA — ответ на вопрос W13 «снимают ли слоты NLA-трюк» [проверено].
7. **Движущиеся части без рига** — констрейнт Geometry Attribute (5.x: вектор/кватернион/матрица из атрибута) [V:4wEqD-jK0DU 06:50]
   [не проверено]; в glTF констрейнты не уходят — запекать (H `07/02 §3`).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| `mixer.setTime(t)` при `action.paused = true` | кадр 0 при любой прокрутке | `action.time = p·d; mixer.update(0)` (H/20; ошибка каталога A `01/01 §4.5`) |
| отдельные действия на части | каждая часть с 0 — стаггер потерян | одно действие со слотами (`animx.new_action`) |
| `action.fcurves` (по памяти 3.x/4.x) | AttributeError в 5.x | `animx.fcurves` через channelbag слота (H `07/01 §1`) |
| `slot.name` | AttributeError в 5.2 | `slot.identifier` / `slot.name_display` (этот прогон) |
| экспорт без сэмплов | поворот ≥ 180° крутится назад/стоит | пресет `anim_trs` (`export_force_sampling=True`) |
| `optimize` со склейкой | части слиты — крышку не найти | `--flatten false --join false` (`keep_names=True`) |
| цикл `requestAnimationFrame` всегда | 60 кадров/с в покое | рендер только пока догоняем |
| камера числами из чужой сцены | предмет вне кадра (кейс 6 см против сцены в метрах) | кадр по `Box3` модели |

## Ссылки

H `../07-animation/01-keyframes-actions-5x.md §5`, `../07-animation/03-gltf-to-web-playback.md §3`, `../99-raw/experiments/H/12-reveal-parts`,
`../99-raw/experiments/H/21-scroll-page`; F2 `../09-web-runtime/03-scroll-interaction-animation.md §5–6`,
`../09-web-runtime/examples/camera-path-scroll/`; E `../08-export-gltf/04-validation-pitfalls-presets.md §7` (`anim_trs`).
