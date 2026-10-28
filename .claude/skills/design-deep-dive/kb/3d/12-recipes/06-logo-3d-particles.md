# 06 · Логотип: выдавленный 3D-логотип и логотип из частиц (+ интро и морф из готовых экспериментов H)

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, three r186, Chromium · сквозной прогон:
[проверено] · страница частиц: [проверено] · пример:
`examples/06-logo-3d-particles/`

## Выжимка рецепта

1. Логотип-текст → меш: `D.text_mesh` (встроенный шрифт или файл проекта, `resolution_u` 3–4, `bevel_res` 0–1, фаска не утолщает
   буквы — `offset = −bevel`), SVG-логотип → `D.svg_mesh` (импорт `import_curve.svg` + сварка); стоит лицом к −Y, низ на z = 0
   [проверено: D1/05, этот прогон].
2. **Логотип из частиц** = ровно N точек поверхности логотипа (`D.surface_points(ob, N, seed)`, равномерно по площади,
   детерминированно) + вторая форма с **тем же N и порядком** → `.bin` Float32 LE в осях three `(x, z, −y)` — 12 Б/точку
   [проверено: D1/07, этот прогон].
3. На странице — **1 `THREE.Points`, 1 вызов**: вершинный шейдер смешивает две формы по `uP` (F2 `09/04 §4`), цвет бренда — `THREE.Color`
   + `#include <colorspace_fragment>` (без него ΔE 9,6) [проверено: F2/05, этот прогон].
4. Прокрутка даёт только прогресс → `damp` → кадр только при изменении (0 вызовов в покое); reduce → сразу логотип, один кадр;
   текст логотипа продублирован HTML, canvas `aria-hidden` [проверено: этот прогон].
5. Телефон — 20–30 тыс. точек (A `01/01 §6.2`); 20 тыс. × 2 формы = 480 КБ сырых Float32, brotli всего −14 % (412 КБ в сети; оценка «−20–40 %» F1 для случайных точек завышена) [проверено: вес этого прогона].
6. Интро логотипа (движение частей) — JS-таймлайн по клипу Blender или видео с альфой 24–32 КБ (H/16); морф формы — shape keys →
   морфы 66 КБ после meshopt (H/13) — ссылки, не пересборка [проверено].

## 1. Бриф-пример и границы

«Лендинг запуска бренда NOVA: при прокрутке облако точек собирается в логотип; на телефоне легко; без движения — просто логотип».

| годится | не годится → куда |
|---|---|
| логотип-слово или монограмма, 1 цвет | многоцветный логотип с градиентами → текстура/предрендер (рецепт 08) |
| эффект раскрывает смысл (сборка, «из хаоса — порядок») | частицы ради частиц — клише «шар/галактика/логотип из частиц» (A `01/01 §22`) |
| three уже на странице или бюджет ≤ 200 КБ JS | без WebGL — постер логотипа (SVG/PNG) и CSS-анимация |

## 2. Паспорт

Логотип: текст `NOVA`, кегль 0,2 м, выдавливание 24 мм, фаска 3 мм (`bevel_res` 1, `resolution_u` 4). Частицы: N = 20 000 (телефон и
десктоп одинаково), seed 7; вторая форма — облако на сфере радиусом 0,6 ширины логотипа. Цвет точек #8B7CFF на фоне #0E0F12;
логотип-GLB: белая керамика.

## 3. Код Blender: логотип → GLB + постер; точки двух форм → .bin

```python
# Blender 5.2.2 — [проверено] рецепт 06: 3D-логотип (text_mesh) + точки для частиц (.bin)
import sys, json, math, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "06-logo-3d-particles"
P = dict(text="NOVA", size=0.2, extrude=0.024, bevel=0.003, res_u=4, color="#F2F0EC", bg="#E9E7E3",
         N=20000, seed=7, cloud_k=0.6, cam=dict(az=18, el=10, lens=85, margin=1.12, res=(1280, 720)))

rk.reset()
C = D.fresh_collection("ASSET_logo")
logo = D.text_mesh("Logo_NOVA", P["text"], C, size=P["size"], extrude=P["extrude"], bevel=P["bevel"], bevel_res=1,
                   resolution_u=P["res_u"])
bpyx.assign_material(logo, rk.web_material("Logo_Ceramic", "ceramic_glaze", P["color"]))
mn, mx = bpyx.world_bbox([logo]); W = mx.x - mn.x
assert 0.4 < W < 0.9 and abs(mn.z) < 1e-4, (W, mn.z)             # ширина в метрах, стоит на z = 0 (не плашмя, M2.12)
rk.studio([logo], bg=P["bg"], E_key=2.5, az=P["cam"]["az"])
rk.camera([logo], **P["cam"])
rk.neutral(samples=48)
rk.audit()
rk.render(SLUG, "logo_blender", res=P["cam"]["res"], samples=48)
rk.ship(SLUG, "ASSET_logo", "logo", preset="static_hero", optimize="meshopt")

# частицы: форма A — облако на сфере, форма B — поверхность логотипа; одинаковое N и порядок (морфинг по индексу)
pts_logo = D.surface_points(logo, P["N"], seed=P["seed"])
c = (mn + mx) / 2
sph = bpyx.primitive("uvsphere", "Cloud_Sphere", radius=W * P["cloud_k"], segments=64, rings=32, location=c)
pts_cloud = D.surface_points(sph, P["N"], seed=P["seed"] + 1)
bpy.data.objects.remove(sph, do_unlink=True)
out = rk.out_dir(SLUG)
a = D.export_points_f32(pts_cloud, f"{out}/cloud.bin")
b = D.export_points_f32(pts_logo, f"{out}/logo.bin")
meta = {"count": P["N"], "forms": ["cloud.bin", "logo.bin"], "axes": "three (x, z, -y)", "units": "m",
        "center": list(D.to_three(c)), "radius": W * P["cloud_k"]}
json.dump(meta, open(f"{out}/points.json", "w"))
assert a["bytes"] == b["bytes"] == P["N"] * 12
rk.save(SLUG, points={"cloud_kb": round(a["bytes"] / 1024, 1), "logo_kb": round(b["bytes"] / 1024, 1)}, passport=P)
```

## 4. Страница: облако → логотип на прокрутке

`examples/06-logo-3d-particles/index.html` (целиком в примере; ниже — ядро). three r186 с jsDelivr через import map (для продакшена —
бандлер на своём домене: 174 против 443 КБ br, F1 `09/01 §1`).

```js
// three r186 — [проверено] ядро страницы: две формы из Blender → 1 Points, прогресс прокрутки
const [A, B] = await Promise.all(['cloud.bin', 'logo.bin'].map(async (u) => new Float32Array(await (await fetch(u)).arrayBuffer())));
if (A.length !== B.length) throw new Error('формы с разным N — морфинг по индексу невозможен');
const g = new THREE.BufferGeometry();
g.setAttribute('position', new THREE.BufferAttribute(A, 3));
g.setAttribute('aTarget', new THREE.BufferAttribute(B, 3));
const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
  uniforms: { uP: { value: 0 }, uSize: { value: 2.0 * dpr }, uDist: { value: dist }, uColor: { value: new THREE.Color('#8B7CFF') } },
  vertexShader: `uniform float uP, uSize, uDist; attribute vec3 aTarget;
    void main() { vec3 pos = mix(position, aTarget, smoothstep(0., 1., uP));
      vec4 mv = modelViewMatrix * vec4(pos, 1.); gl_Position = projectionMatrix * mv; gl_PointSize = uSize * (uDist / -mv.z); }`,
  fragmentShader: `uniform vec3 uColor;
    void main() { float d = length(gl_PointCoord - .5); if (d > .5) discard; gl_FragColor = vec4(uColor, smoothstep(.5, .2, d));
    #include <colorspace_fragment>
    }` });
scene.add(new THREE.Points(g, mat));
```

Цикл: `target = scrollY / (scrollHeight − innerHeight)`; `current = THREE.MathUtils.damp(current, target, 6, dt)`; `uP = current`;
`renderer.render` только пока |current − target| > 1e-4 (будится событием `scroll`); reduce → `uP = 1`, один кадр, без слушателя.

## 5. Числа прогона

Blender: 3,4 с (текст → меш, утверждения, EEVEE 48 спп 1280 × 720 — 3,0 с, GLB, 2 × 20 000 точек); страница — `web_view.py --page`
(прокрутка 0 / 0,5 / 1) и `site_probe.py` (Pixel 7 CPU ×4 + медленный 4G; reduce) + `gate_check()` рецепта 01. Итераций правки — 0.

| величина | значение |
|---|---|
| логотип `NOVA` (кегль 0,2 м, выдавливание 24 мм, фаска 3 мм) | 712 треуг.; GLB 29,6 → **7,9 КБ**; валидатор 0 / 0 |
| точки | 2 × 20 000 × 12 Б = 2 × **234,4 КБ**; brotli всего −14 % (412 КБ в сети: случайные Float32 жмутся плохо) |
| страница, десктоп 1280 × 720 | 1 canvas, **1 вызов** в кадре при прокрутке, 60 fps (p95 16,8 мс), LCP 36 мс (текст), 0 ошибок |
| Pixel 7, CPU ×4, 1,6 Мбит/с | **9 / 9** ворот: LCP 196 мс (P), TBT 0, 805 КБ (JS 391 + точки 412), 0 вызовов в покое, DPR 1,5 |
| reduce | **6 / 6**: сразу логотип, 0 вызовов и 0 % движения в покое |

Взгляд на `99-raw/experiments/K/04-particles-page/desktop/page_sheet.png`: 0 — сфера точек, 0,5 — сжатое облако, 1 — читаемый
логотип NOVA контуром из точек (боковины букв тоже засеяны — буквы «объёмные»). Слабее: логотип занимает ≈ 40 % ширины (кадр по
радиусу облака) — для первого экрана крупнее: радиус облака 0,5 ширины логотипа или отдельная камера на форму.

Находка для ворот (J): `gate_check()` F1 считает 3D-ассетами только категории `model3d` и `texture3d` зонда — поставки `.bin`
(точки, пути) в «3D-ассеты» не попадают (здесь 412 КБ учтены только в общем весе). Для частиц и путей порог 820 КБ проверять по
категории `bin` отдельно.

## 6. Ворота

Логотип: ширина 0,4–0,9 м и низ на z = 0 — `assert` (закрывает M2.12 «текст плашмя» и M2.1); точки: `bytes == N × 12` для обеих
форм, одинаковое N (иначе морфинг по индексу рвётся); страница: `gate_check()` (мобильный + reduce), отдельно — вес `.bin` ≤ 820 КБ.

## 7. Варианты

1. **SVG-логотип** вместо текста: `D.svg_mesh(name, "logo.svg", C, size=0.5, depth=0.024, bevel=0.003, resolution_u=…)` — кривые
   SVG всегда сваривать, `resolution_u` на сегмент Безье (D1/05) [проверено].
2. **Интро логотипа (движение частей)**: одно действие со слотами на части → клип; на странице — JS-таймлайн по `timeline.json`
   (22,3 КБ статичный GLB + 1,5 КБ JS, отклонение ≤ 0,1 мм и 0,02°) или без three — VP9 с альфой **31,9 КБ** / stacked AV1 23,8 КБ
   [проверено: H/16, `../07-animation/04-js-vs-blender-vs-prerender.md §4`].
3. **Морф формы** (логотип «перетекает»): shape keys одной топологии → морфы glTF, пресет `anim_morph` (`export_apply=False`!),
   253 КБ → **66 КБ** после meshopt, веса в three совпадают до 1e-4 [проверено].
4. **Третья форма** (логотип → продукт → текст): ещё один `.bin` того же N; смешивание — `mix` по двум `uP` или атрибут на форму.
5. **Больше точек на десктопе**: 40 тыс. — 1 вызов, 1,06 мс (F2/05); телефону 20–30 тыс.
6. **Без WebGL / save-data**: логотип SVG + CSS-анимация сборки (без canvas).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| точки из GN `Distribute Points on Faces` для морфинга | у форм разное N (плотность × площадь) | `D.surface_points(ob, N, seed)` — ровно N (D1/07) |
| оси Blender в `.bin` | логотип лежит/смотрит вверх | `export_points_f32` пишет `(x, z, −y)` |
| цвет uniform без `colorspace_fragment` | бренд темнее (ΔE 9,6) | `#include <colorspace_fragment>` в фрагментном шейдере (F2) |
| цикл `requestAnimationFrame` всегда | 60 кадров/с в покое, батарея | кадр только при изменении прогресса (0 вызовов в покое) |
| `lerp(current, target, 0.1)` на кадр | на 144 Гц в 2,4 раза быстрее | `THREE.MathUtils.damp(…, λ, dt)` + `THREE.Timer` (F2) |
| текст логотипа только в canvas | скринридер и поиск не видят бренд | `<h1>` в HTML, canvas `aria-hidden="true"` |
| `text_mesh` без `offset_bevel` | фаска утолщает буквы, «слипаются» | `offset = −bevel` (по умолчанию в `D.text_mesh`) |

## Ссылки

D1 `../05-modeling/03-geometry-nodes-procedural.md §3` (точки), `../05-modeling/02-modifiers-bmesh-curves.md §6` (текст, SVG);
F2 `../09-web-runtime/04-shaders-effects-catalog-impl.md §4`; F1 `../09-web-runtime/06-deliverables-ar-ktx2-webgpu.md §1.3`;
H `../07-animation/04-js-vs-blender-vs-prerender.md §4`, `../99-raw/experiments/H/16-logo-motion`, `../99-raw/experiments/H/13-morph`.
