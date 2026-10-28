# 02 · Серия 3D-иконок по паспорту: предрендер AVIF/WebP с альфой (+ GLB по запросу)

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS (Cycles CPU + OIDN), Pillow 11.3, three r186 · сквозной прогон:
[проверено] · пример: `examples/02-icon-series/`

## Выжимка рецепта

1. Набор 3D-иконок на сайте — **предрендер** (AVIF q60 с альфой — единицы КБ), не GLB: 0 JS, 0 вызовов, работает везде
   [проверено: D1/04, D2/05, этот прогон].
2. Серию держит **паспорт в коде** (доли радиусов, палитра hex, наклон, камера, свет, вид) — не «на глаз» в каждой иконке;
   паспорт D2 выравнивает тень (разброс 0,9 L* против 6,4) и бренд (C* 84–93 против 38–44 у «наивной» серии) [проверено].
3. Форма «мягкой глины»: пухлая кромка (радиус ≈ 0,35–0,4 толщины, `power` 2,4), суперэллипс, мелкие детали врастают на
   30–40 %, 2–3 цвета одной палитры, профили тел вращения — гладкой кривой [проверено].
4. Нормировка: радиус описанной сферы 0,5 м, одна камера 85 мм (az 35°, el 25°, поле 1,35), E_key 2, Khronos PBR Neutral,
   прозрачный фон + ловец теней (только Cycles) [проверено].
5. Выход: рендер 2× CSS-размера → AVIF q60 + WebP q80 для 1× и 2×, `<picture>` с `width/height` [проверено: D2 `06/04 §1.3`].

## 1. Бриф-пример и границы

«Три иконки фич для SaaS-лендинга (сообщения, уведомления, файлы), фирменный фиолетовый, светлые карточки 128–256 px».

| годится | не годится → куда |
|---|---|
| 3–12 иконок одной серии, статичные | иконка реагирует на курсор/прокрутку → GLB + three (вариант §7.2) или Lottie/SVG |
| бренд-цвет важен, фон страницы любой (альфа) | иконки 16–32 px в интерфейсе → SVG (`../../ui/07-iconography-imagery/`) |
| форма из SVG-пиктограммы | сложная иллюстрация-сцена → рецепт 07 (диорама) или предрендер сцены |

## 2. Паспорт серии

`S` — форма и палитра (D1/04), `PASSPORT` — кадр, свет, вид, размер (D2 `06/02 §6`). Меняется бренд — меняются только hex в `S`.
Одна иконка = одна функция `icon_<имя>(coll)` в метрах куба 10 см; всё остальное общее.

## 3. Код: иконки → паспорт → рендер с альфой → GLB

```python
# Blender 5.2.2 — [проверено] рецепт 02: серия из 3 иконок (формы — 3d 05/04 §3, паспорт — 3d 06/02 §6)
import sys, math, bpy
from mathutils import Matrix, Vector
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "02-icon-series"
S = dict(unit=0.1, edge_k=0.38, corner_k=0.22, power=2.4, rough=0.35, coat=0.3, tilt_deg=14,
         primary="#635BFF", primary_dark="#4B44D6", accent="#FFD60A", white="#FFFFFF")
PASSPORT = {"radius": 0.5, "lens": 85, "az": 35, "el": 25, "margin": 1.35, "E_key": 2.0, "world": ("#F4F4F6", 0.25),
            "view": "Khronos PBR Neutral", "size": (512, 512), "samples": 32}
MAT = {}


def mats():
    for k in ("primary", "primary_dark", "accent", "white"):
        MAT[k] = bpyx.principled(f"Icon_{k}", base_color=S[k], roughness=S["rough"], coat_weight=S["coat"])[0]


def stand_up(objs, face_front=True):
    """Лицом к −Y (повороты — в вершины), один наклон серии, на пол."""
    Rm = Matrix.Rotation(math.radians(S["tilt_deg"]), 4, "Z")
    if face_front:
        Rm = Rm @ Matrix.Rotation(math.radians(90), 4, "X")
    bpy.context.view_layer.update()
    for o in objs:
        o.matrix_world = Rm @ o.matrix_world
        bpyx.apply_transforms(o, rotation=True, scale=True)
    bpyx.put_on_floor(objs)


def icon_chat(coll):
    u = S["unit"]; w, h, t = u, u * 0.78, u * 0.34
    body = D.rounded_slab("Chat_Body", w, h, t, min(w, h) * 0.45, (t * S["edge_k"], t * S["edge_k"]), coll,
                          kind="squircle", squircle_n=3.2, corner_seg=10, edge_seg=6, power=S["power"])
    x0, y0 = -w * 0.26, -h * 0.40
    path = D.bezier_pts([(x0, y0, t / 2), (x0 - w * 0.02, y0 - h * 0.12, t / 2), (x0 - w * 0.10, y0 - h * 0.20, t / 2),
                         (x0 - w * 0.19, y0 - h * 0.26, t / 2)], 24)
    tail = D.sweep("Chat_Tail", path, D.circle_pts(t * 0.42, 20), coll, scale=lambda k: 1.0 - 0.72 * k ** 1.3)
    dots = []
    for i, dx in enumerate((-0.22, 0.0, 0.22)):
        r = w * 0.058
        d = bpyx.primitive("uvsphere", f"Chat_Dot{i}", radius=r, segments=24, rings=12, collection=coll)
        d.location = (dx * w, 0.02 * h, t + r * 0.30)          # утоплена на 70 % радиуса — врастает, не парит
        bpyx.assign_material(d, MAT["white"]); dots.append(d)
    bpyx.assign_material(body, MAT["primary"]); bpyx.assign_material(tail, MAT["primary"])
    objs = [body, tail] + dots
    stand_up(objs)
    return objs


def icon_bell(coll):
    u = S["unit"]
    side = D.catmull_rom_pts([(0.041, 0.010), (0.049, 0.013), (0.046, 0.022), (0.038, 0.037), (0.034, 0.056),
                              (0.029, 0.071), (0.019, 0.083), (0.008, 0.0868)], 40)   # гладкий профиль — без полос
    bell = D.lathe("Bell_Body", [(0.0, 0.010)] + side + [(0.0, 0.087)], coll, segments=64, smooth_angle=50)
    clap = bpyx.primitive("uvsphere", "Bell_Clapper", radius=u * 0.085, segments=32, rings=16, collection=coll)
    clap.location = (0, 0, 0.010 - u * 0.03)
    knob = bpyx.primitive("torus", "Bell_Knob", radius=u * 0.07, minor_radius=u * 0.028, segments=32, rings=12,
                          collection=coll)
    knob.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    knob.location = (0, 0, 0.087 + u * 0.03)
    bpyx.assign_material(bell, MAT["accent"]); bpyx.assign_material(knob, MAT["accent"])
    bpyx.assign_material(clap, MAT["primary_dark"])
    objs = [bell, clap, knob]
    stand_up(objs, face_front=False)
    return objs


def icon_folder(coll):
    u = S["unit"]; w, h, t = u, u * 0.74, u * 0.07
    e = (t * S["edge_k"], t * S["edge_k"])
    back = D.rounded_slab("Folder_Back", w, h, t, min(w, h) * S["corner_k"] * 0.6, e, coll, corner_seg=8, edge_seg=4,
                          power=S["power"])
    tab = D.rounded_slab("Folder_Tab", w * 0.42, h * 0.3, t, h * 0.08, e, coll, corner_seg=8, edge_seg=4, power=S["power"])
    tab.location = (-w * 0.29, h * 0.5, 0)
    paper = D.rounded_slab("Folder_Paper", w * 0.84, h * 0.86, t * 0.35, h * 0.04, (t * 0.1, t * 0.1), coll,
                           corner_seg=4, edge_seg=2)
    paper.location = (0, h * 0.06, t)
    front = D.rounded_slab("Folder_Front", w, h * 0.84, t, min(w, h) * S["corner_k"] * 0.6, e, coll, corner_seg=8,
                           edge_seg=4, power=S["power"])
    front.location = (0, -h * 0.08, t + t * 0.35)
    D.set_origin(front, (0, -h * 0.5, t + t * 0.35))           # pivot на оси сгиба — панель приоткрыта на 16°
    front.rotation_euler = (math.radians(-16), 0, 0)
    for o, k in ((back, "primary_dark"), (tab, "primary_dark"), (front, "primary"), (paper, "white")):
        bpyx.assign_material(o, MAT[k])
    objs = [back, tab, paper, front]
    stand_up(objs)
    return objs


def apply_passport(objects, P=PASSPORT):
    """Паспорт серии D2 (06/02 §6): нормировка, key/fill/rim от r, мир, камера 85 мм, Neutral."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = P["size"]
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
    rk.d2lib.world_color(*P["world"])
    a, e = math.radians(P["az"]), math.radians(P["el"])
    cam = bpyx.add_camera(location=c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 6,
                          target=c, lens=P["lens"])
    bpyx.frame_camera(cam, objects, margin=P["margin"])
    bpyx.set_color_management(P["view"])
    catcher = bpyx.primitive("plane", "ShadowCatcher", size=6.0, location=(0, 0, mn.z))
    catcher.is_shadow_catcher = True                              # тень → альфа (только Cycles)
    return cam


for i, (name, fn) in enumerate((("chat", icon_chat), ("bell", icon_bell), ("folder", icon_folder))):
    rk.reset(keep_numbers=i > 0); mats()
    coll = D.fresh_collection(f"ASSET_icon_{name}")
    objs = fn(coll)
    rk.ship(SLUG, coll.name, f"icon_{name}", preset="static_hero", optimize="meshopt")   # GLB-вариант до нормировки
    apply_passport(objs)
    bpyx.set_engine("CYCLES")                                     # ловец теней есть только в Cycles; CPU + OIDN
    bpy.context.scene.cycles.device = "CPU"; bpy.context.scene.cycles.use_denoising = True
    rk.render(SLUG, f"icon-{name}-3d", res=PASSPORT["size"], samples=PASSPORT["samples"], transparent=True)
rk.save(SLUG, passport=PASSPORT, series=S)
```

```python
# run: system — Python 3 + Pillow — [проверено] PNG 512² → AVIF/WebP 1×/2× + страница-сетка
import os
from PIL import Image
EX = os.path.dirname(os.path.abspath(__file__))  # перенос: папка примера


def encode_web(png_path, out_dir, css_px, avif_q=60, webp_q=80):
    """PNG RGBA (рендер 2× CSS) → AVIF и WebP для 2× и 1×; возвращает {имя: КБ} и HTML <picture> (D2 06/04 §1.3)."""
    im = Image.open(png_path).convert("RGBA"); base = os.path.splitext(os.path.basename(png_path))[0]
    os.makedirs(out_dir, exist_ok=True); sizes = {}
    for scale in (2, 1):
        px = css_px * scale
        frame = im if im.width == px else im.resize((px, round(im.height * px / im.width)), Image.LANCZOS)
        for ext, kw in (("avif", {"quality": avif_q}), ("webp", {"quality": webp_q, "method": 6})):
            p = os.path.join(out_dir, f"{base}@{scale}x.{ext}"); frame.save(p, ext.upper(), **kw)
            sizes[os.path.basename(p)] = round(os.path.getsize(p) / 1024, 1)
    html = (f'<picture><source type="image/avif" srcset="{base}@1x.avif 1x, {base}@2x.avif 2x">'
            f'<source type="image/webp" srcset="{base}@1x.webp 1x, {base}@2x.webp 2x">'
            f'<img src="{base}@1x.webp" width="{css_px}" height="{css_px}" alt="" loading="lazy" decoding="async"></picture>')
    return sizes, html


cards, total = [], {}
for name, label in (("chat", "Сообщения"), ("bell", "Уведомления"), ("folder", "Файлы")):
    sizes, pic = encode_web(f"{EX}/icon-{name}-3d.png", f"{EX}/web", css_px=256)
    total.update(sizes)
    pic = pic.replace(f"icon-{name}-3d@", f"web/icon-{name}-3d@")          # страница лежит на уровень выше web/
    cards.append(f'<li><div class="ic">{pic}</div><h3>{label}</h3></li>')
html = ("<!doctype html><html lang='ru'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Иконки — рецепт 02</title><style>body{margin:0;font:18px/1.5 system-ui;background:#F4F4F6;color:#16181d}"
        "ul{list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px;padding:6vh 6vw;margin:0}"
        "li{background:#fff;border-radius:24px;padding:24px;text-align:center}.ic img{width:min(100%,256px);height:auto}"
        "h3{margin:.4em 0 0}</style></head><body><ul>" + "".join(cards) + "</ul></body></html>")
open(f"{EX}/index.html", "w", encoding="utf-8").write(html)
print(total)
```

## 4. Числа прогона

Прогон `run_recipes.py 12-recipes/02-icon-series.md`: Blender 12,2 с на три иконки (сборка, GLB, Cycles 32 спп + OIDN 512² —
3,4–3,6 с на иконку), системный блок 12,1 с (кодирование AVIF — самое долгое). Итераций правки — 2 (цикл без `keep_numbers`
затирал числа предыдущих иконок; наклон колокола — без поворота «лицом к −Y», он и так стоит по Z).

| иконка | треуг. | PNG 512² | AVIF q60 1× / 2× | WebP q80 1× / 2× | GLB → meshopt |
|---|---|---|---|---|---|
| сообщения | 4 816 | 191 КБ | 2,8 / 4,0 КБ | 10,2 / 26,4 КБ | 121,7 → 32,2 КБ |
| уведомления | 6 848 | 167 КБ | 2,4 / 3,8 КБ | 7,9 / 19,7 КБ | 159,6 → 33,8 КБ |
| файлы | 2 384 | 202 КБ | 2,6 / 4,0 КБ | 9,9 / 25,9 КБ | 57,8 → 17,0 КБ |

Страница-сетка (`examples/02-icon-series/index.html`, `web_view.py --page`): 4 запроса, **9,4 КБ всего**, LCP 48 мс, 0 вызовов
отрисовки, 0 ошибок консоли [проверено]. Три GLB — валидатор 0 ошибок, three r186 грузит без
ошибок (`examples/02-icon-series/web/icon_*/web_sheet.png`). Предрендер в 8–13 раз легче GLB той же иконки и не тянет three
(≈ 174 КБ br JS, рецепт 01).

Взгляд на `examples/02-icon-series/sheet.png`: серия читается как один набор (одна камера, свет, наклон 14°, мягкие тени альфой),
фиолетовый #635BFF насыщенный (не «лаванда» AgX), кромки пухлые, точки чата вросли в корпус. Слабее всего папка: белый лист
плоский и крупный — для «дорогого» вида ему нужна своя фаска и лёгкий наклон.

## 5. Страница

`<picture>` с AVIF и WebP-запасом, `width`/`height` против CLS, `loading="lazy"` ниже первого экрана (для иконки в первом экране —
без `lazy`, `fetchpriority="high"`), `alt` — если иконка несёт смысл, иначе `alt=""` при подписи рядом (D2 `06/04 §1.3`).

```html
<!-- HTML — [проверено] разметка одной карточки (генерирует блок 2) -->
<picture><source type="image/avif" srcset="web/icon-chat-3d@1x.avif 1x, web/icon-chat-3d@2x.avif 2x">
  <source type="image/webp" srcset="web/icon-chat-3d@1x.webp 1x, web/icon-chat-3d@2x.webp 2x">
  <img src="web/icon-chat-3d@1x.webp" width="256" height="256" alt="" loading="lazy" decoding="async"></picture>
```

## 6. Ворота

| проверка | как | порог | прогон |
|---|---|---|---|
| серия ровная | одна камера/свет/вид из `PASSPORT`; метрики D2/04 (L* тени, C* бренда) | разброс тени ≤ 2 L* | паспорт D2 (0,9 L*), в этом прогоне не пересчитывалось |
| детали не парят | `rk.asserts(..., touch=[("Chat_Dot0", "Chat_Body")])` | зазор ≤ 1 мм | D1/04: 0 мм (здесь — только глазом) |
| вес | сумма AVIF 1× на экран | ≤ 15 КБ на иконку | 2,4–2,8 КБ |
| альфа на фоне страницы | глазом на реальном фоне (AVIF: альфа с потерями, до ±29 уровней на краю тени) | нет ореола | белые карточки — ok; пёстрый фон — q75 или WebP (D2) |
| страница | `web_view.py --page`: ошибки консоли, вызовы | 0 / 0 | 0 / 0 |

## 7. Варианты

1. **Иконки из SVG** (логотипы фич уже нарисованы): `D.svg_mesh(name, svg_path, size, depth, bevel)` — импорт
   `import_curve.svg`, сварка, выдавливание, фаска долей размера (D1 `05/02 §6`, W4 `zthvZvw-yJE`) → тот же паспорт.
2. **Иконка реагирует на курсор** — GLB (17–34 КБ после meshopt, в прогоне уже экспортированы) + three: 1 canvas на
   страницу, не на иконку (контекстов WebGL ≤ 8–16 на страницу); иначе — hover-смена двух кадров предрендера.
3. **Тёмная тема**: мир `#16181D × 0,25`, отдельный рендер серии (альфа с тенью на тёмном фоне читается хуже — тень слабее,
   добавить rim ×2, D2 `06/02 §1.3`).
4. **Стеклянные иконки** — transmission в Cycles рендерится честно (предрендер), в GLB — только с фоном в canvas (рецепт 09).
5. **Анимированная иконка** — 24–48 кадров → WebP/AVIF-секвенция или видео с альфой (рецепт 08).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| каждая иконка со своей камерой/светом | «разваливается на третьей картинке», разный размер и тень | один `PASSPORT`, нормировка радиуса 0,5 м (D2) |
| AgX + светлый мир | бренд выбелен до пастели (C* 38–44) | Neutral, мир × 0,25 (D2/04) |
| тень — плоскость с материалом | серая подложка в PNG | ловец теней `is_shadow_catcher` + `film_transparent` (только Cycles) |
| Cycles без явных сэмплов | 4096 сэмплов по умолчанию, минуты на кадр | `samples=32` + OIDN (D2 `06/03`) |
| `primitive_uv_sphere_add` + `scale` без применения (по памяти) | масштаб ×26, точки висят в 21 мм (M2.10, M2.2) | `bpyx.primitive(...)` в метрах, врастание 30–40 % (D1/04) |
| профиль колокола ломаной | горизонтальные полосы затенения | `catmull_rom_pts` 30–60 точек |
| цикл серии без `keep_numbers` | в `numbers.json` только последняя иконка | `rk.reset(keep_numbers=i > 0)` |

## Ссылки

Формы D1 `../05-modeling/04-styles-and-archetypes.md §3`, `../99-raw/experiments/D1/04-clay-icons`; паспорт D2
`../06-materials-lighting-render/02-lighting-camera-composition.md §4, §6`, `../99-raw/experiments/D2/04-light-icons`; форматы D2
`../06-materials-lighting-render/04-outputs-for-web.md §1`; поставки A `../01-web-3d-landscape/05-blender-deliverables-map.md §2`;
паспорт серии 2D/3D — `../../ui-research/07-iconography-imagery/02 §5`.
