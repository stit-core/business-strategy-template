# 09 · Стекло и металл продукта: флакон с transmission + volume, фон — внутри canvas

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS (EEVEE с трассировкой), glTF-IO 5.2.40, gltf-transform 4.5.0, three r186,
Chromium · сквозной прогон: [проверено] · страница: [проверено]
· пример: `examples/09-glass-product/`

## Выжимка рецепта

1. Стекло для glTF = **Transmission 1 + Roughness 0–0,05 + IOR + Thickness в группе «glTF Material Output» + Volume Absorption**
   (цвет толстого стекла — объём, не Base Color), `alphaMode` OPAQUE → `KHR_materials_transmission` + `volume` + `ior`
   [проверено: E/13, D2/03, этот прогон].
2. **three преломляет только то, что нарисовано в canvas**: на прозрачном canvas со CSS-фоном стекло — «серый диск» (D2: ΔE ≈ 10);
   рабочий вариант — фон и предметы позади **в самой сцене** (`scene.background` + объекты за стеклом) [проверено: этот прогон — пара страниц].
3. Преломление видно, только если за стеклом есть рисунок: однотонный фон стекло «съедает» — ставить за флаконом предметы/полосы
   сцены [проверено: этот прогон].
4. Цена: transmission — **+1 проход** (непрозрачные объекты рисуются ещё раз в буфер пропускания), `transmissionResolutionScale 0,5`
   −20 % (F2 `09/04 §3`); металлу и стеклу нужен `scene.environment` [проверено: F2/05, этот прогон].
5. В Blender эталон стекла — EEVEE с `use_raytracing` + `material.use_raytrace_refraction` или Cycles (transmission bounces ≥ 12);
   EEVEE без трассировки — плохой эталон (E `08/01 §6`) [проверено: этот прогон, D2/03].
6. Телефон и слабые устройства — **предрендер** стекла картинкой (Cycles/EEVEE-RT честнее three); GLB со стеклом — только десктоп с
   фоном в canvas.

## 1. Бриф-пример и границы

«Парфюм: тяжёлый стеклянный флакон с янтарным оттенком и золотой крышкой; hero на тёплом светлом фоне; лёгкий поворот».

| годится | не годится → куда |
|---|---|
| стекло — суть продукта (флакон, бокал, линза) | стекло на прозрачном canvas поверх HTML-фона → предрендер (рецепт 08) или фон в canvas |
| десктоп, фон hero можно нарисовать в canvas | телефон с бюджетом ≤ 30 вызовов и слабым GPU → предрендер AVIF (единицы КБ) |
| металл — акцент (крышка, кольцо) | «стеклянный тор на градиенте» ради стекла — клише (A `01/01 §22`) |

## 2. Паспорт

Флакон 60 × 32 × 84 мм (скругления углов 9 мм, кромки 4 мм, `power` 2,4), стекло: IOR 1,52, roughness 0,02, Thickness 0,03 м (≈ толщина
флакона), поглощение янтарь #E8B27A, плотность 3; крышка Ø 26 × 22 мм — золото (`metal_polished`, roughness 0,22); подставка —
матовый камень; за флаконом — две «гальки» (терракота и оливковый) — рисунок для преломления. Фон #EFE9E1.

## 3. Код Blender: build(P) → проверки → EEVEE-RT постер → GLB

```python
# Blender 5.2.2 — [проверено] рецепт 09: стеклянный флакон (transmission + volume) + сцена за ним
import sys, math, json, struct, bpy
from mathutils import Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "09-glass-product"
P = dict(W=0.060, D=0.032, H=0.084, corner=0.009, edge=0.004, cap_r=0.013, cap_h=0.022, neck_r=0.006, neck_h=0.006,
         glass_tint=("#E8B27A", 3.0), thickness=0.03, cap="gold", plinth="#CFC7BC", pebbles=("#C8674A", "#7C8B5A"),
         bg="#EFE9E1", cam=dict(az=22, el=9, lens=90, margin=1.18, res=(768, 1024)))


def build(P):
    C = D.fresh_collection("ASSET_glass")
    glass = rk.web_material("Glass_Amber", "glass", "#FFFFFF", thickness=P["thickness"], absorption=P["glass_tint"],
                            ior=1.52)                                        # 1,5 = умолчание glTF → KHR_materials_ior не пишется
    gold = rk.web_material("Cap_Gold", "metal_polished", P["cap"], roughness=0.22)
    stone = rk.web_material("Plinth_Stone", "plastic_matte", P["plinth"], roughness=0.75)
    plinth = D.rounded_slab("Plinth", 0.20, 0.12, 0.014, 0.012, (0.002, 0.004), C, corner_seg=8, edge_seg=3)
    bpyx.assign_material(plinth, stone)
    body = D.rounded_slab("Bottle_Glass", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), C,
                          corner_seg=10, edge_seg=6, power=2.4)
    body.location.z = 0.014 - 0.0005                                          # стоит на подставке, врастает на 0,5 мм
    bpyx.assign_material(body, glass)
    top = 0.014 - 0.0005 + P["H"]
    neck = D.lathe("Bottle_Neck", [(0.0, 0.0), (P["neck_r"], 0.0), (P["neck_r"], P["neck_h"]), (0.0, P["neck_h"])], C,
                   segments=48)
    neck.location.z = top - 0.001
    bpyx.assign_material(neck, gold)
    cap_prof = D.fillet_polyline([(0.0, 0.0), (P["cap_r"], 0.0), (P["cap_r"], P["cap_h"]), (0.0, P["cap_h"])],
                                 [0, 0.0015, 0.004, 0], 4)
    cap = D.lathe("Bottle_Cap", cap_prof, C, segments=64, smooth_angle=40)
    cap.location.z = top + P["neck_h"] - 0.002
    bpyx.assign_material(cap, gold)
    pebbles = []
    for i, (hexc, x, y, r) in enumerate(((P["pebbles"][0], -0.035, 0.035, 0.022), (P["pebbles"][1], 0.03, 0.028, 0.028))):
        m = rk.web_material(f"Pebble_{i}", "plastic_matte", hexc, roughness=0.6)
        pb = bpyx.primitive("uvsphere", f"Pebble_{i}", radius=r, segments=48, rings=24, collection=C)
        pb.data.transform(Matrix.Scale(0.62, 4, (0, 0, 1)))                 # сплюснутая галька
        pb.location = (x, y, 0.014 + r * 0.62 - 0.001)
        bpyx.assign_material(pb, m); pebbles.append(pb)
    return C, [plinth, body, neck, cap] + pebbles


rk.reset()
C, parts = build(P)
rk.asserts("ASSET_glass", (0.20, 0.12, 0.014 + P["H"] + P["neck_h"] + P["cap_h"] - 0.0035), tol=0.06,
           touch=[("Bottle_Glass", "Plinth"), ("Bottle_Neck", "Bottle_Glass"), ("Bottle_Cap", "Bottle_Neck"),
                  ("Pebble_0", "Plinth"), ("Pebble_1", "Plinth")], max_tris=30000)
rk.studio(parts, bg=P["bg"], E_key=2.5, az=P["cam"]["az"])
rk.camera(parts[1:4], **P["cam"])                                      # кадр — по флакону, подставка и галька — окружение
sc = rk.neutral(samples=64)
sc.eevee.use_raytracing = True                                          # преломление в EEVEE (иначе — эталон неверный)
rk.audit()
rk.render(SLUG, "poster_eevee_rt", res=P["cam"]["res"], samples=64)
res = rk.ship(SLUG, "ASSET_glass", "glass", preset="static_hero", optimize="meshopt")
raw = open(f"{rk.out_dir(SLUG)}/glass_raw.glb", "rb").read()
j = json.loads(raw[20:20 + struct.unpack_from("<I", raw, 12)[0]])
g = next(m for m in j["materials"] if m["name"] == "Glass_Amber")
assert {"KHR_materials_transmission", "KHR_materials_volume", "KHR_materials_ior"} <= set(g.get("extensions", {})), g
rk.save(SLUG, glass_material=g, passport=P)
```

## 4. Страница: фон в сцене против прозрачного canvas

`examples/09-glass-product/index.html` (фон в сцене) и `index_css.html` (прозрачный canvas, фон — CSS): three r186 (import map),
`GLTFLoader` + `MeshoptDecoder`, `NeutralToneMapping`, `RoomEnvironment` через PMREM, `transmissionResolutionScale = 0.5`, покачивание
±20° только при видимости и без reduce. Разница — одна строка:

```js
// three r186 — [проверено] стекло видит только то, что нарисовано в canvas
renderer.toneMapping = THREE.NeutralToneMapping;               // пара к Blender «Khronos PBR Neutral»
renderer.transmissionResolutionScale = 0.5;                    // −20 % цены прохода пропускания (3d 09/04 §3)
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.background = new THREE.Color('#EFE9E1');                 // фон В СЦЕНЕ — без этой строки стекло «белая плита»
```

## 5. Числа прогона

Blender: 7,1 с (сборка, утверждения, EEVEE 64 спп с трассировкой 768 × 1024 — 6,7 с, экспорт, meshopt). Итераций правки — 2:
(1) утверждение габарита поймало гальку, свисающую с подставки на 13 мм (y = 0,045 + r 0,028 > 0,06) — сдвинута на подставку;
(2) IOR 1,5 = умолчание glTF — `KHR_materials_ior` не пишется, утверждение по JSON требовало его — IOR 1,52 (реальное стекло).

| величина | значение |
|---|---|
| треугольники / материалы | 7 688 / 5; касания всех 5 пар — 0 мм |
| GLB → meshopt | 195,3 → **49,3 КБ**; `KHR_materials_transmission` (1,0), `KHR_materials_volume` (attenuationColor янтарь, attenuationDistance 0,333 = 1/3, thickness 0,03), `KHR_materials_ior` 1,52; валидатор 0 / 0 |
| страница (обе версии) | **11 вызовов в кадре** = 5 непрозрачных × 2 (проход пропускания + основной) + 1 стекло; 60 fps (p95 16,7 мс), 0 ошибок; 490 КБ (JS 437 с CDN, модель 49) |

Взгляд на `examples/09-glass-product/sheet.png` (Blender EEVEE-RT | three, фон в сцене | three, прозрачный canvas):
- **фон в сцене** — стекло читается: галька за флаконом видна сквозь стекло со сдвигом, янтарный оттенок объёма есть, золото крышки
  с отражениями окружения;
- **прозрачный canvas** — флакон превращается в **белую непрозрачную плиту**: проходу пропускания нечего преломлять, кроме пустоты
  (D2 видел «серый диск» на своём фоне — симптом тот же, вид зависит от фона и тонмаппинга) — подтверждено парой;
- Blender EEVEE-RT преломляет сильнее (режим толщины SPHERE — объёмная линза), three — тонкий сдвиг по `thickness`; тон стекла в
  Blender серее из-за тёмной стены циклорамы за флаконом. Точное совпадение стекла Blender ↔ three не цель: эталон для
  постера — Cycles/EEVEE-RT, для страницы — вид в three.

## 6. Ворота

JSON GLB: у материала стекла есть `transmission`, `volume`, `ior` (`assert` в коде — ловит IOR 1,5 и Thickness без группы); касания
≤ 1 мм; вызовов ≤ 60 на десктопе (11); телефон — предрендер вместо GLB (правило, не замер); ошибки консоли 0.

## 7. Варианты

1. **Матовое стекло**: `web_material(..., "glass_frosted")` (roughness 0,3) — в three размытие прохода пропускания грубее
   [не проверено: D2 `06/01 §2` помечает так же].
2. **Тонкостенный бокал**: `thickness=0` → тонкое стекло без преломления, цвет — Base Color (W3 §4).
3. **Стекло на телефоне**: EEVEE-RT/Cycles-постер (рецепт 01 `make_poster` не подходит — нужен рендер Blender) → AVIF; или
   `MeshPhysicalMaterial` без transmission (`opacity` + `envMap`) — «подделка стекла» F2 `09/04 §3` (дешевле, без прохода).
4. **Флакон вращают** — transmission пересчитывает проход каждый кадр: только при видимости; reduce → один кадр.
5. **Дисперсия** (радужные края): `Dispersion` в группе при volume → `KHR_materials_dispersion` (E/13 x07) [проверено: E].

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| Alpha < 1 вместо transmission | в three `transparent`, сортировка ломается | transmission, `alphaMode` OPAQUE (E `08/01 §5.5`) |
| нет Thickness в группе | тонкое стекло без преломления | `gltf_output(mat).inputs["Thickness"]` (в `rk.web_material`) |
| IOR ровно 1,5 и проверка на `KHR_materials_ior` | расширения нет — это не ошибка экспорта | IOR 1,52 (стекло) или не требовать расширение |
| прозрачный canvas + CSS-фон | белая/серая плита вместо стекла | `scene.background` + предметы за стеклом в сцене |
| нет `scene.environment` | чёрный металл и тусклое стекло | PMREM от `RoomEnvironment` или HDRI 512² (G) |
| EEVEE без `use_raytracing` как эталон | «стекло» без преломления в постере | `scene.eevee.use_raytracing = True` или Cycles, bounces ≥ 12 |
| галька «на глаз» | свисает с подставки на 13 мм | утверждение габарита по подставке поймало (этот прогон) |

## Ссылки

E `../08-export-gltf/01-export-contract.md §6.2`, `../99-raw/experiments/E/13-materials-extensions`; D2 `../06-materials-lighting-render/01-materials-pbr.md §3.1`;
F2 `../09-web-runtime/04-shaders-effects-catalog-impl.md §3`; F1 `../09-web-runtime/01-threejs-core.md §6.3`; W3 дайджесты `DQeP363Xmn4`, `Sv2wqwsvx-8`
(через D2).
