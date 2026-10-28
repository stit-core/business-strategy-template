# 01 · Hero-объект продукта: постер → 3D после LCP

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, three r186, Chromium (Playwright,
Iris Xe) · сквозной прогон: [проверено] · пример: `examples/01-hero-product/`

## Выжимка рецепта

1. Первый экран продуктового лендинга: **постер AVIF — LCP, 3D — после `load` в простое**; постер снимается со страницы из
   того же GLB и той же пары тонмаппинга → переход без скачка [проверено: F1 `09/examples/hero-lazy`, A/07].
2. Геометрия — один идемпотентный `build(P)` в метрах реального предмета, опорная деталь, фаски и мягкие кромки
   (`rounded_slab`, `power` 2,4–2,6), подвижная часть — отдельный объект с pivot на оси (→ рецепт 05) [проверено].
3. Цвет бренда — **Khronos PBR Neutral в Blender ↔ `NeutralToneMapping` в three** (ΔE 0,23–0,36), hex → линейный через
   `bpyx.color` [проверено].
4. Проверки до экспорта — кодом: аудит C1/10 + утверждения C1/16 (габарит ±5 %, стыки ≤ 1 мм, бюджет) [проверено: этот прогон].
5. Экспорт — пресет E `static_hero` (коллекция `ASSET_*`), постобработка `gltf-transform optimize` (meshopt + квантование);
   без текстур GLB весит десятки КБ — бюджет hero 0,8 / 1,5 МБ (телефон / десктоп) остаётся на текстуры [проверено: E/24, этот прогон].
6. Ворота — `site_probe.py` + `gate_check()` F1 (LCP-элемент не canvas, TBT, вес, вызовы, reduce → 0 вызовов).

## 1. Бриф-пример и границы

«Лендинг беспроводных наушников: в первом экране — кейс крупно, светлый фон #ECEEF2, лёгкое покачивание, на телефоне быстро».

| годится | не годится → куда |
|---|---|
| один предмет, который хочется «покрутить глазами»; бренд-цвет важен | нужен только красивый кадр без движения → предрендер AVIF 5–60 КБ (рецепт 08, A `01/05 §2`) |
| есть трёхмерная форма (корпус, крышка, кнопки) | товар «как на фото» с фактурами → скан/Poly Haven + доводка (G `10/02`, вариант §7.3) |
| телефон — основная аудитория, 3D — украшение | 3D — суть опыта (конфигуратор, мир) → кампания (A `01/02 §7`) |

## 2. Паспорт

Паспорт стиля — по умолчанию из `00-how-to-use.md §3` (Neutral, E_key 2–3 Вт/м², 85–100 мм, фон страницы). Паспорт ассета —
словарь `P` в коде: размеры условного кейса (64 × 24 × 50 мм), шов крышки на высоте 37 мм с зазором 0,3 мм, радиусы
углов и кромки, цвета hex, кадр (az 28°, el 16°, 90 мм, поле 1,25), бюджет (≤ 20 тыс. треуг., ≤ 300 КБ).

## 3. Код: build(P) → проверки → рендер → экспорт

```python
# Blender 5.2.2 — [проверено] рецепт 01: кейс наушников → постер Blender + GLB для hero
import sys, math, bpy, bmesh
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "01-hero-product"
P = dict(W=0.064, D=0.024, H=0.050, corner=0.0115, edge=0.0095, power=2.6, seam_z=0.037, gap=0.0003,
         lid_open_deg=0, body="#F4F3F0", led="#39D98A", bg="#ECEEF2",
         cam=dict(az=28, el=16, lens=90, margin=1.25, res=(1024, 1024)), max_tris=20000)


def split_by_z(ob, z, keep_above):
    """Разрез меша плоскостью z с заливкой среза — две замкнутые детали (3d 05/04 §1)."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z),
                                 plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
    bmesh.ops.edgeloop_fill(bm, edges=[e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()
    ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(35))


def build(P):
    C = D.fresh_collection("ASSET_case")                       # идемпотентно: своя коллекция пересоздаётся
    body = rk.web_material("Case_Plastic", "plastic_gloss", P["body"])
    led, _ = bpyx.principled("Case_LED", base_color=P["led"], emission_color=P["led"], emission_strength=3.0)
    base = D.rounded_slab("Case_Base", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), C,
                          corner_seg=10, edge_seg=8, power=P["power"])
    lid = bpy.data.objects.new("Case_Lid", base.data.copy()); C.objects.link(lid)
    split_by_z(base, P["seam_z"] - P["gap"] / 2, keep_above=False)
    split_by_z(lid, P["seam_z"] + P["gap"] / 2, keep_above=True)
    for o in (base, lid):
        bpyx.assign_material(o, body)
    dot = bpyx.primitive("uvsphere", "Case_LED", radius=0.0009, segments=16, rings=8, collection=C)
    dot.location = (0, -P["D"] / 2 + 0.0003, P["seam_z"] - 0.008)   # от габарита базы: передняя стенка, 8 мм ниже шва
    bpyx.assign_material(dot, led)
    D.set_origin(lid, (0, P["D"] / 2 - 0.0012, P["seam_z"]))          # pivot крышки — ось петли (для рецепта 05)
    lid.rotation_euler.x = -math.radians(P["lid_open_deg"])
    lid["hinge_axis"] = "X"                                            # extras → userData в three
    return C, [base, lid, dot]


rk.reset()
C, parts = build(P)
rk.asserts("ASSET_case", (P["W"], P["D"], P["H"]), touch=[("Case_LED", "Case_Base")], max_tris=P["max_tris"])
rk.studio(parts, bg=P["bg"], E_key=2.5)
rk.camera(parts, **P["cam"])
rk.neutral(samples=48)
rk.audit()                                                          # после камеры и вида: кадр и тонмаппинг тоже проверяются
rk.render(SLUG, "poster_blender", res=P["cam"]["res"], samples=48)
rk.ship(SLUG, "ASSET_case", "case", preset="static_hero", optimize="meshopt")
rk.save(SLUG, passport=P)
```

Что делает каждый шаг (подробности — по ссылкам, здесь не повторяются):

| шаг | функция | откуда | ловит |
|---|---|---|---|
| форма | `D.rounded_slab(..., power=2.6)`, разрез `bisect_plane` + `edgeloop_fill`, `D.set_origin` | D1 `05/04 §1`, `05/01 §4` | «мыло без кромки», pivot в центре (M2.4) |
| материал | `rk.web_material(..., "plastic_gloss")` = roughness 0,18 + coat 0,5 | D2 `06/01 §2.3` | процедурные ноды, которые не доедут (M4.1) |
| утверждения | `rk.asserts(коллекция, габарит, touch=…, max_tris)` → C1/16 | C1 `04/04 §6.4` | масштаб ×10–25 (M2.1), парящие детали (M2.2) |
| свет и кадр | `rk.studio(E_key=2.5)` (d1lib.stage под Neutral), `rk.camera(az, el, lens, margin)` | D2 `06/02 §1–2, §5`, D1 | тёмный/пересвеченный бренд, кадр «на глаз» (M3.7) |
| аудит | `rk.audit()` → C1/10 после камеры | C1 `04/05` | неприменённый масштаб, дефолтные имена, кадр |
| экспорт | `rk.ship(..., preset="static_hero", optimize="meshopt")` → E/24 + `gltf-transform optimize` | E `08/04 §7` | молчаливые умолчания экспортёра, несжатая геометрия |

## 4. Числа прогона

`python3 ../../scripts/3d/run_recipes.py 12-recipes/01-hero-product.md` — 3,8 с на весь рецепт (сборка,
утверждения, рендер EEVEE 48 спп 1024² — 3,2 с, экспорт, meshopt), итераций правки кода — 1 (аудит был поставлен до камеры).

| величина | значение |
|---|---|
| треугольники / узлы / материалы | 1 976 / 3 / 2 (`KHR_materials_clearcoat`, `KHR_materials_emissive_strength`) |
| GLB после экспорта → после `optimize` | 53,4 → **12,3 КБ** (5,5 КБ brotli в сети); валидатор 0 ошибок, 0 предупреждений |
| утверждения C1/16 | габарит 64,0 × 24,6 × 50,0 мм (±5 %), зазор LED ↔ корпус 0 мм — ok |
| аудит C1/10 | кадр 55 % площади; флаги `ngons` (крышки `rounded_slab` — n-гоны, в glTF корректны, D1 `05/05 §1`), `raw_sharp_edges` (шов — намеренно острый), `interpenetration` LED ↔ корпус (врастание детали на 30–40 % — правило D1) |
| three r186 (`web_view.py`, Neutral) | загрузка 9 мс, 3 меша, `MeshPhysicalMaterial` (clearcoat) + `MeshStandardMaterial`, 0 ошибок консоли |
| постер со страницы (`make_poster.py`) | AVIF q60 **8,0 КБ**, WebP q85 7,9 КБ (1024² с альфой) |

Файлы: `examples/01-hero-product/` — `build.py` (блок выше), `case.glb`, `case_raw.glb`, `poster_blender.png` (рендер Blender для
просмотра), `numbers.json`, `web/case/web_sheet.png` (4 ракурса в three), страница `index.html` + `dist/` + `poster.*`.

## 5. Страница

Берётся эталон F1 `../09-web-runtime/examples/hero-lazy/` целиком: `index.html`, бандл `dist/` (three r186, esbuild), `make_poster.py`.
Меняются только ассет и тексты — модуль читает `window.HERO_CFG`:

```html
<!-- three r186 — [проверено] подмена ассета в эталоне hero-lazy без пересборки бандла -->
<script>window.HERO_CFG = { modelPhone: 'case.glb', modelDesktop: 'case.glb' };</script>
<script type="module" src="dist/hero.js"></script>
```

Порядок: (1) `build.py` → `case.glb`; (2) скопировать `index.html`, `dist/`, `make_poster.py` из hero-lazy, поправить пути постера и
`alt` (описание предмета словами — доступность); (3) `python3 make_poster.py` — постер снимается со страницы `?poster` тем же
рендерером и тонмаппингом; (4) ворота §6. Что эталон уже умеет: постер — LCP, three после `load` в простое, наборы телефон/десктоп,
кадр по проекции вершин, покачивание ±20° с периодом ≈ 16 с, кнопка паузы (WCAG 2.2.2), стоп вне экрана и в скрытой вкладке,
reduce → один кадр (F1 `09/05 §3, §5`). Если на странице React — тот же ассет в `r3f-hero` (F2 `09/02 §1–4`), но чанк 293 КБ br; компонент из GLB — `gltfjsx`
[V:ji6q_P-QY_E 10:21] (drei `useGLTF` грузит three-stdlib — без `KHR_meshopt_compression`, F2).

## 6. Ворота

Прогон (раздача с brotli `serve_br.py` F1, `site_probe.py --quick`, `gate_check()` из F1 `09/05 §7.2`):

```bash
# bash — [проверено] ворота hero-страницы: десктоп, Pixel 7 CPU ×4 + 1,6 Мбит/с, reduce
python3 ../../scripts/3d/serve_br.py 12-recipes/examples/01-hero-product 8791 &
U=http://127.0.0.1:8791/index.html; O=99-raw/experiments/K/02-hero-page
python3 ../../scripts/3d/site_probe.py $U $O/desktop --quick
python3 ../../scripts/3d/site_probe.py $U $O/mobile --quick --mobile --throttle --wait 16000
python3 ../../scripts/3d/site_probe.py $U $O/reduce --quick --reduced-motion
python3 $O/gates.py            # gate_check() F1 в напечатанном виде → gates.json
```

| режим | LCP (элемент) | TBT | передано (JS / 3D) | вызовов в кадре | DPR | итог |
|---|---|---|---|---|---|---|
| десктоп 1440×900 | 52 мс (IMG) | 79 мс | 187 КБ (174 / 5,3) | 3 | 1,0 | **9 / 9** |
| Pixel 7, CPU ×4, медленный 4G | 388 мс (IMG) | 148 мс | 187 КБ | 3 | 1,5 | **9 / 9** |
| reduce | 40 мс | — | — | 0 в покое, движение 0 % | — | **6 / 6** |

Сравнение с эталоном F1 (Camera_01, KTX2): TBT десктопа 175 → 79 мс — ворота «≤ 150» не проходил эталон, проходит лёгкий ассет;
значит TBT hero-страницы определяют текстуры и транскодер, а не three (174 КБ JS одинаковы). Не проверено: первый 3D-кадр меткой
(в режиме `--quick` зонд её не пишет), реальные телефоны, клавиатурный проход.

## 7. Варианты

1. **Телефон**: ассет без текстур — один файл на оба набора; с текстурами — `rk.ship(..., phone=True)` → `<name>_phone.glb`
   (`gltfpack -cc -tc -ts 0.5`, KTX2 ½) или WebP 512² — на медленной сети WebP выгоднее (транскодер KTX2 204 КБ br, F1 `09/06 §3`).
2. **Reduced motion / без WebGL2 / save-data / < 2 ГБ памяти** — эталон оставляет постер (проверено: reduce 0 вызовов).
3. **Реквизит «как на фото» вместо своей модели** — Poly Haven glTF (CC0) → `gltf-transform optimize` → 0,15–1,2 МБ
   (G `10/03 §2`, `99-raw/experiments/G/02-polyhaven-api`); эталон hero-lazy сам собран на Camera_01 Poly Haven: 564 КБ телефон /
   1,18 МБ десктоп, LCP 460 мс (F1). Скан/генератор — доводка G `10/02` (0,28 МБ на телефон).
4. **Атмосферный hero вместо товарного** — AgX в Blender ↔ `AgXToneMapping` (светлее на 3,4–3,7 L*, D2 `06/03`); бренд-hex тогда
   не гарантирован (ΔE 7–9).
5. **Крышка открывается при прокрутке** — тот же `build(P)` (pivot на петле уже есть) → рецепт 05.

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| canvas вместо постера в первом экране | LCP = текст/ничего, 3D грузится до контента, TBT телефона > 300 мс | постер `<picture>` AVIF/WebP + 3D после `load` (эталон) |
| постер отрендерен Blender, а 3D — three | «прыжок» цвета и кадра при подмене | постер со страницы `make_poster.py` (тот же рендерер) или Neutral ↔ Neutral и одна камера |
| AgX в Blender, `NeutralToneMapping` (или наоборот) | бренд тусклее/ярче на 3–9 ΔE | одна пара: Neutral ↔ Neutral (D2) |
| кадр до установки разрешения | объект мелкий в кадре 1:1 | `rk.camera(res=…)` ставит разрешение до подгонки (D2 `06/02 §5.2`) |
| `optimize` без `--flatten false --join false` | части склеены, имена `Mesh016`, крышку не найти из JS | `rk.ship(keep_names=True)` (E/24) |
| аудит до камеры | флаг `no_camera`, вид AgX в отчёте | `rk.audit()` после `rk.camera` и `rk.neutral` (найдено этим прогоном) |
| модель по памяти в метрах «примерно» | кейс 1–3 м (M2.1), свет и DPR не те | размеры из паспорта + `rk.asserts` габарита ±5 % |

## Ссылки

Эталон страницы F1 `../09-web-runtime/examples/hero-lazy/README.md`; паттерн A `../01-web-3d-landscape/02-when-3d-budgets-loading.md §4.2`;
форма D1 `../05-modeling/04-styles-and-archetypes.md §1`, `../99-raw/experiments/D1/03-product-hinge-grille`; свет D2
`../06-materials-lighting-render/02-lighting-camera-composition.md §1–2`; пресеты E `../08-export-gltf/04-validation-pitfalls-presets.md §7`;
ворота F1 `../09-web-runtime/05-performance-a11y-fallbacks.md §7`; протокол C1 `../04-ai-agents-mcp/04-agent-operating-protocol.md §1`.
