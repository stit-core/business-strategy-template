# 04 · Абстрактная скульптура для hero: лента с закрутом на цоколе (и два варианта из одного паспорта)

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, three r186 · сквозной прогон:
[проверено] · пример: `examples/04-abstract-sculpture/`

## Выжимка рецепта

1. Абстракция для бренда без физического товара: **лента с закрутом по торическому узлу** на цоколе + один акцент (≈ 0,1 главной
   формы) — самая «дорогая» форма набора D1: переменная видимая ширина ленты даёт ритм без лишних деталей [проверено].
2. Сечение ленты — «капсула» (`rrect_pts`), путь — `torus_knot_pts(p, q)`, протяжка `D.sweep` с параллельным переносом рамок
   (без переворотов Френе), закрут `twist = 2π·N` [проверено: D1/06, d1lib тесты].
3. Реальный масштаб «статуэтки» 0,25–0,30 м, лента **врастает в цоколь** на 4 мм — без парения (M2.2) [проверено: D1/06, этот прогон].
4. Один паспорт — много вариантов: `p, q, twist, ширина, палитра` → `build(P)` идемпотентен (коллекция пересоздаётся) —
   2 варианта в одном прогоне дают разные формы при том же кадре и свете [проверено: этот прогон].
5. Вес: 26 тыс. треуг. → **≈ 120 КБ** после meshopt — в бюджете hero; на странице — эталон hero-lazy (рецепт 01) или `r3f-hero` F2
   (он собран на скульптуре D1) [проверено: D1/06, F2 `09/examples/r3f-hero`].

## 1. Бриф-пример и границы

«SaaS для финансов: hero без продукта, спокойная премиальная абстракция в фирменных цветах, медленно вращается».

| годится | не годится → куда |
|---|---|
| бренд без предмета, нужен «объект-символ» | нужен фон, а не объект → шейдерный фон (рецепт 11): 1 вызов, 0 Blender |
| медленное вращение / покачивание, курсор | форма должна «течь» и морфиться → морф shape keys (рецепт 06 §вариант, H/13) или шейдерный блоб (F2 `09/04 §5`) |
| статичный кадр тоже годится | «блобы» в стиле 3D-клише 2023 → см. клише A `01/01 §22`; SDF-капля — вариант §7.1 |

## 2. Паспорт

Цоколь (опорная деталь): радиус 85 мм, высота 28 мм, фаски 2–4 мм. Главная форма: узел (p, q), радиусы R, r, сечение w × t,
закрут N оборотов, поворот вокруг Z. Акцент: золотой шар r = 13 мм у основания. Палитра: перламутр / камень / золото.
Кадр 16:9, объект по центру, поле 1,15 (для текста слева — сдвиг камеры `shift_x` [не проверено]).

## 3. Код: build(P) → два варианта паспорта → рендеры → GLB

```python
# Blender 5.2.2 — [проверено] рецепт 04: лента по узлу (3d 05/04 §5), два варианта паспорта
import sys, math, bpy
from mathutils import Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "04-abstract-sculpture"
BASE = dict(plinth_r=0.085, plinth_h=0.028, knot=(2, 3), knot_R=0.075, knot_r=0.034, ribbon_w=0.034, ribbon_t=0.0075,
            twist_turns=3, spin_deg=18, orb_r=0.013, embed=0.004, ribbon="#EDE7E1", plinth="#8C8680", orb="gold",
            bg="#E9E6E1", cam=dict(az=30, el=12, lens=85, margin=1.15, res=(1280, 720)))
VARIANTS = {"pearl_23": {}, "ink_34": dict(knot=(3, 4), knot_R=0.07, knot_r=0.03, ribbon_w=0.026, twist_turns=5,
                                           ribbon="#1F2A44", plinth="#D9D4CC", orb="copper", bg="#F1EEE9")}


def build(P):
    C = D.fresh_collection("ASSET_sculpture")                    # тот же слот коллекции для всех вариантов — идемпотентно
    stone = rk.web_material("Sc_Stone", "plastic_matte", P["plinth"], roughness=0.7)
    ribbon_m = rk.web_material("Sc_Ribbon", "ceramic_glaze", P["ribbon"])
    orb_m = rk.web_material("Sc_Orb", "metal_polished", P["orb"], roughness=0.22)
    prof = D.fillet_polyline([(0.0, 0.0), (P["plinth_r"], 0.0), (P["plinth_r"], P["plinth_h"]), (0.0, P["plinth_h"])],
                             [0, 0.002, 0.004, 0], 4)
    plinth = D.lathe("Sc_Plinth", prof, C, segments=96, smooth_angle=40)
    bpyx.assign_material(plinth, stone)
    path = D.torus_knot_pts(*P["knot"], P["knot_R"], P["knot_r"], 420)
    sec = D.rrect_pts(P["ribbon_w"], P["ribbon_t"], P["ribbon_t"] / 2 * 0.95, 6)       # «капсула» — без острых кромок
    ribbon = D.sweep("Sc_Ribbon", path, sec, C, closed=True, twist=2 * math.pi * P["twist_turns"], smooth_angle=60)
    ribbon.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))                    # узел встаёт вертикально
    ribbon.data.transform(Matrix.Rotation(math.radians(P["spin_deg"]), 4, "Z"))
    zmin = min(v.co.z for v in ribbon.data.vertices)
    ribbon.location.z = P["plinth_h"] - zmin - P["embed"]                               # врастает в цоколь
    bpyx.assign_material(ribbon, ribbon_m)
    orb = bpyx.primitive("uvsphere", "Sc_Orb", radius=P["orb_r"], segments=32, rings=16, collection=C)
    orb.location = (P["plinth_r"] * 0.55, -P["plinth_r"] * 0.45, P["plinth_h"] + P["orb_r"] * 0.92)
    bpyx.assign_material(orb, orb_m)
    return C, [plinth, ribbon, orb]


for i, (name, over) in enumerate(VARIANTS.items()):
    P = dict(BASE, **over)
    rk.reset(keep_numbers=i > 0)
    C, parts = build(P)
    mn, mx = bpyx.world_bbox(parts)
    assert 0.20 <= mx.z - mn.z <= 0.32, f"высота статуэтки {mx.z - mn.z:.3f} м вне 0,20–0,32"   # масштаб (M2.1)
    rk.asserts("ASSET_sculpture", tuple(mx - mn), touch=[("Sc_Ribbon", "Sc_Plinth"), ("Sc_Orb", "Sc_Plinth")],
               max_tris=40000)                                    # габарит — из bbox; смысл — касания и бюджет
    rk.studio(parts, bg=P["bg"], E_key=2.5, az=P["cam"]["az"])
    rk.camera(parts, **P["cam"])
    rk.neutral(samples=48)
    rk.audit()
    rk.render(SLUG, f"hero_{name}", res=P["cam"]["res"], samples=48)
    rk.ship(SLUG, "ASSET_sculpture", f"sculpture_{name}", preset="static_hero", optimize="meshopt")
rk.save(SLUG, variants=list(VARIANTS))
```

## 4. Числа прогона

Прогон: 7,0 с на два варианта (сборка 0,1–0,2 с каждый, EEVEE 48 спп 1280 × 720 — 3,0–3,2 с), итераций — 1 (утверждение габарита
по цоколю не подходит ленте, выходящей за цоколь: заменено утверждением высоты 0,20–0,32 м + касания).

| вариант | узел, закрут | треуг. | GLB → meshopt | высота | касания (C1/16) |
|---|---|---|---|---|---|
| `pearl_23` (перламутр, камень, золото) | (2, 3), 3 оборота | 26 400 | 593,4 → **117,3 КБ** | 0,25 м | лента ↔ цоколь 0, шар ↔ цоколь 0 мм |
| `ink_34` (тёмно-синий, светлый камень, медь) | (3, 4), 5 оборотов | 26 400 | 593,4 → **117,2 КБ** | 0,25 м | 0 / 0 мм |

Аудит: единственный флаг — `interpenetration` цоколь × лента/шар (врастание 4 мм — намеренно); кадр 35 % площади. Валидатор 0 / 0,
three r186 без ошибок (`examples/04-abstract-sculpture/web/*/web_sheet.png`).

Взгляд на `examples/04-abstract-sculpture/sheet.png`: оба варианта — цельная скульптура уровня галереи/Awwwards-hero, не «суп из
примитивов»: закрут даёт ритм толщины, блики керамики читают форму, акцент-шар масштабирует предмет. `ink_34` (тёмная лента на светлом)
выразительнее: контраст силуэта. Слабее: стена циклорамы темнеет к верху (как у D2/04) — для hero на светлом фоне лучше прозрачный
canvas (фон рисует CSS) или отдельная лампа на фон.

## 5. Страница

Тот же эталон hero-lazy (рецепт 01): `window.HERO_CFG = { modelPhone: 'sculpture_ink_34.glb', modelDesktop: 'sculpture_ink_34.glb' }`
+ `make_poster.py`. 117 КБ без текстур — телефонный набор не нужен. Металлу акцента нужен `scene.environment` (в эталоне —
`RoomEnvironment`), иначе шар чёрный (H/16, E `08/01 §8`). Для React — `09-web-runtime/examples/r3f-hero/` (F2) уже собран на
скульптуре D1: Lightformer, `ContactShadows frames={1}`, reduce → `frameloop="demand"`, 293 КБ br [проверено: F2].

## 6. Ворота

Высота 0,20–0,32 м и касания ≤ 1 мм — `assert` в коде (закрывают M2.1 и M2.2); бюджет ≤ 40 тыс. треуг.; GLB ≤ 300 КБ (C1 `04/04 §3.1`);
страница — `gate_check()` рецепта 01.

## 7. Варианты

1. **SDF-капля** вместо ленты: `D.sdf_blob_gn(name, balls, C, voxel=0.0035, fillet_iter=10, smooth_width=3, smooth_iter=4)` +
   `noise_displace` 4 мм — 18,8 тыс. треуг., 79 КБ после meshopt; без `SDF Grid Mean` — «гроздь шаров» [проверено].
2. **Тёмный атмосферный hero**: фон #0E0F12, AgX, контровые ×2, ключ сбоку 45–60° (D2 `06/02 §1.3`) [не проверено этим прогоном].
3. **Больше вариантов из паспорта**: `(p, q)` ∈ {(2, 3), (2, 5), (3, 4), (3, 5)}, `twist_turns` 2–6, `ribbon_w/ribbon_t` 3–5 — best-of-N
   с выбором по картинкам лучше длинных итераций (C2 `04/03 §7`).
4. **Вращение на странице** — JS (поворот корня, `damp`), не клип: простое движение одного объекта — JS (H `07/04 §1`).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| труба постоянного сечения (`curve.bevel_depth`) | «шланг», нет ритма | лента-капсула с закрутом (`D.sweep(..., twist)`) |
| рамки Френе на узле | перекручивание и изломы ленты | параллельный перенос рамок (`d1lib.sweep`) |
| форма висит над цоколем | тень отдельно, «парит» (M2.2) | `embed` 4 мм + `touch` в утверждениях |
| масштаб 3–4 м (opus, sonnet по памяти) | свет и тени «игрушечные», DPR и кадр не те | высота 0,20–0,32 м утверждением |
| thin film/иридесценция на ленте | в glTF/three не доезжает (ΔE 4,5–8, M4.2) | керамика/лак (`ceramic_glaze`), металл только на акценте |
| утверждение габарита «по цоколю» | ложный провал (лента шире цоколя) | габарит главной формы — отдельным правилом (высота) |

## Ссылки

D1 `../05-modeling/01-form-and-aesthetics.md §5`, `../05-modeling/04-styles-and-archetypes.md §5`, `../99-raw/experiments/D1/06-sculpture`;
F2 `../09-web-runtime/examples/r3f-hero/`; материалы D2 `../06-materials-lighting-render/01-materials-pbr.md §2`; клише A `../01-web-3d-landscape/01-effects-catalog.md §22`.
