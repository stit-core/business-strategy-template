# 03 · Мокап устройства со скриншотом: телефон с экраном-текстурой → постер и GLB

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS, glTF-IO 5.2.40, gltf-transform 4.5.0, gltfpack 1.2, three r186 · сквозной
прогон: [проверено] · пример: `examples/03-device-mockup/`

## Выжимка рецепта

1. Экран — **отдельный меш с UV 0–1 на весь экран** и материалом `Screen` (картинка в Base Color и Emission 1,0), на 0,1 мм над
   стеклом; скриншот обрезается под аспект экрана до загрузки — иначе растяжение [проверено: D1/02, этот прогон].
2. Корпус — `rounded_slab` по справочным размерам (смартфон 71,5 × 147 × 7,8 мм), материалы по нормали граней (рамка / спинка /
   стекло), островок камер и кнопки — **от габарита корпуса**, не числами наугад (sonnet: камера парит в 20–40 мм, M2.2) [проверено].
3. Устройство стоит экраном к −Y (в glTF — +Z), повороты — в вершины, общий pivot — пустышка в центре корпуса [проверено].
4. Скриншот — JPEG/PNG в sRGB → в GLB как есть, WebP — постобработкой; телефону — KTX2 ½ (`gltfpack -tc -ts 0.5`) [проверено: этот прогон].
5. Чаще всего мокапу на сайте хватает **постера** (рендер 1–2 кадров); GLB — если устройство крутят или оно раскрывается на прокрутке.

## 1. Бриф-пример и границы

«Лендинг мобильного приложения: телефон со скриншотом главного экрана, 3/4 сзади-сбоку не нужно — лицом, лёгкий наклон,
светлый фон; тот же телефон — во втором экране крупно».

| годится | не годится → куда |
|---|---|
| показать свой интерфейс «в руке», экран — главное | мокап с реальной моделью Apple/Samsung → брендовые 3D-модели, лицензия (G `10/03 §1`) |
| один скриншот или смена скриншотов (текстура меняется в JS) | видео в экране → `VideoTexture` на материал `Screen` [не проверено] |
| ноутбук/планшет — та же схема: корпус + экран + pivot крышки | «ноутбук с pivot на петле» D1 не достроен — схема как у крышки кейса (рецепт 01, `D.set_origin`) |

## 2. Паспорт

Размеры — справочные (C1 `04/04 §3.2`); цвета рамки/спинки — hex; скриншот — путь к картинке любого размера; кадр — az −18°,
el 8°, 85 мм (почти фронтально — экран читается); бюджет ≤ 10 тыс. треуг., текстура экрана 540 × 1170 (JPEG).

## 3. Код: скриншот под экран → build(P) → проверки → постер → GLB

```python
# Blender 5.2.2 — [проверено] рецепт 03: телефон (3d 05/04 §2) + скриншот из файла → постер + GLB
import sys, math, bpy, bmesh
import numpy as np
from mathutils import Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "03-device-mockup"
P = dict(W=0.0715, D=0.147, H=0.0078, corner=0.0115, edge=0.0011, bezel=0.0018, screen_corner=0.0098,
         island=0.034, island_corner=0.0085, island_h=0.0011, island_margin=0.0045, lens_r=0.0056, lens_h=0.0016,
         btn_t=0.0006, frame="#8E9196", back="#C9C4BC", glass="#0B0C0E", lens="#1A1C20", ring="#B7BABF", bg="#ECEEF2",
         screenshot=f"{rk.ROOT}/99-raw/experiments/K/02-hero-page/mobile/shot_mobile_thr_quick_0.png", tex_w=540,
         cam=dict(az=-18, el=8, lens=85, margin=1.2, res=(768, 1024)), max_tris=10000)


def fit_screenshot(src, dst, aspect, width):
    """Обрезать скриншот под аспект экрана (ширина/высота), верх страницы сохранить; ужать до width; JPEG sRGB."""
    im = bpy.data.images.load(src, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)   # строки снизу вверх
    if w / h > aspect:
        nw = round(h * aspect); x0 = (w - nw) // 2; px = px[:, x0:x0 + nw]
    else:
        nh = round(w / aspect); px = px[h - nh:, :]                                           # верх = последние строки
    out = bpy.data.images.new("screen_ui", px.shape[1], px.shape[0], alpha=False)
    out.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    out.scale(width, round(width / aspect))
    out.filepath_raw = dst; out.file_format = "JPEG"; out.save(quality=88)
    bpy.data.images.remove(im)
    img = bpy.data.images.load(dst, check_existing=False); img.colorspace_settings.name = "sRGB"
    return img


def build(P, coll):
    parts = {}
    body = D.rounded_slab("Phone_Body", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), coll,
                          corner_seg=10, edge_seg=4, smooth_angle=35)
    m_frame, _ = bpyx.principled("Phone_Frame", base_color=P["frame"], metallic=1.0, roughness=0.32)
    m_back, _ = bpyx.principled("Phone_BackGlass", base_color=P["back"], roughness=0.45, coat_weight=0.6)
    m_glass, _ = bpyx.principled("Phone_FrontGlass", base_color=P["glass"], roughness=0.05, coat_weight=1.0)
    for m in (m_frame, m_back, m_glass):
        body.data.materials.append(m)
    body.data.polygons.foreach_set("material_index", [1 if p.normal.z < -0.99 else 2 if p.normal.z > 0.99 else 0
                                                      for p in body.data.polygons])
    parts["body"] = body
    sw, sd = P["W"] - 2 * P["bezel"], P["D"] - 2 * P["bezel"]          # экран: UV 0–1, на 0,1 мм над стеклом
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    f = bm.faces.new([bm.verts.new((x, y, P["H"] + 0.0001)) for x, y in D.rrect_pts(sw, sd, P["screen_corner"], 10)])
    for loop in f.loops:
        loop[uvl].uv = (loop.vert.co.x / sw + 0.5, loop.vert.co.y / sd + 0.5)
    bmesh.ops.triangulate(bm, faces=[f], quad_method="BEAUTY", ngon_method="BEAUTY")
    screen = D.obj_from_bm(bm, "Phone_Screen", coll, smooth_angle=None)
    img = fit_screenshot(P["screenshot"], f"{rk.out_dir(SLUG)}/screen_ui.jpg", sw / sd, P["tex_w"])
    m_scr, p = bpyx.principled("Screen", roughness=0.08, emission_strength=1.0)
    tex = m_scr.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = img
    bpyx.link_sockets(m_scr.node_tree, (tex, "Color"), (p, "Base Color"))
    bpyx.link_sockets(m_scr.node_tree, (tex, "Color"), (p, "Emission Color"))
    bpyx.assign_material(screen, m_scr)
    parts["screen"] = screen
    isl = D.rounded_slab("Phone_CameraIsland", P["island"], P["island"], P["island_h"], P["island_corner"],
                         (0.0, P["island_h"] * 0.6), coll, corner_seg=8, edge_seg=3)
    ix = P["W"] / 2 - P["island_margin"] - P["island"] / 2
    iy = P["D"] / 2 - P["island_margin"] - P["island"] / 2
    isl.data.transform(Matrix.Rotation(math.pi, 4, "X")); isl.location = (ix, iy, 0.0)
    bpyx.assign_material(isl, m_back); parts["island"] = isl
    m_lens, _ = bpyx.principled("Phone_Lens", base_color=P["lens"], roughness=0.08, coat_weight=1.0)
    m_ring, _ = bpyx.principled("Phone_LensRing", base_color=P["ring"], metallic=1.0, roughness=0.25)
    r, h = P["lens_r"], P["lens_h"]
    prof = D.fillet_polyline([(0.0, -0.7 * h), (0.78 * r, -0.7 * h), (0.78 * r, -h), (r, -h), (r, 0.0), (0.0, 0.0)],
                             [0, 0.00015, 0.00015, 0.0004, 0, 0], 3)
    off = P["island"] * 0.24
    for k, (dx, dy) in enumerate(((-off, off), (-off, -off), (off, 0.0))):
        lens = D.lathe(f"Phone_Lens{k}", prof, coll, segments=40, smooth_angle=40)
        lens.location = (ix + dx, iy + dy, -P["island_h"])
        lens.data.materials.append(m_ring); lens.data.materials.append(m_lens)
        lens.data.polygons.foreach_set("material_index", [1 if (abs(q.center.z + 0.7 * h) < 1e-5 and
                                       math.hypot(q.center.x, q.center.y) < 0.78 * r) else 0 for q in lens.data.polygons])
        parts[f"lens{k}"] = lens

    def button(name, side, y0, length):
        b = D.rounded_slab(name, P["btn_t"] * 2, length, P["H"] * 0.42, P["btn_t"], 0.0, coll, corner_seg=6)
        b.data.transform(Matrix.Translation((0, 0, -P["H"] * 0.21)))
        b.location = (side * P["W"] / 2, y0, P["H"] / 2)
        bpyx.assign_material(b, m_frame)
        return b
    parts["action"] = button("Phone_BtnAction", -1, P["D"] * 0.30, 0.008)
    parts["volup"] = button("Phone_BtnVolUp", -1, P["D"] * 0.20, 0.012)
    parts["power"] = button("Phone_BtnPower", 1, P["D"] * 0.16, 0.018)
    Rm = Matrix.Translation((0, 0, P["D"] / 2)) @ Matrix.Rotation(math.radians(90), 4, "X")   # экраном к −Y, низом на пол
    bpy.context.view_layer.update()
    for o in parts.values():
        o.matrix_world = Rm @ o.matrix_world
        bpyx.apply_transforms(o, rotation=True, scale=True)
    root = bpy.data.objects.new("Phone", None); coll.objects.link(root)
    root.location = (0, -P["H"] / 2, P["D"] / 2); bpy.context.view_layer.update()
    for o in parts.values():
        o.parent = root; o.matrix_parent_inverse = root.matrix_world.inverted()
    return root, list(parts.values())


rk.reset()
C = D.fresh_collection("ASSET_phone")
root, parts = build(P, C)
rk.asserts("ASSET_phone", (P["W"] + 2 * P["btn_t"], P["H"] + P["island_h"] + P["lens_h"], P["D"]), tol=0.06,
           touch=[("Phone_CameraIsland", "Phone_Body"), ("Phone_Lens0", "Phone_CameraIsland"),
                  ("Phone_Screen", "Phone_Body"), ("Phone_BtnPower", "Phone_Body")], max_tris=P["max_tris"])
rk.studio(parts, bg=P["bg"], E_key=2.5, az=-18)
rk.camera(parts, **P["cam"])
rk.neutral(samples=48)
rk.audit()
rk.render(SLUG, "poster_blender", res=P["cam"]["res"], samples=48)
rk.ship(SLUG, "ASSET_phone", "phone", preset="static_hero", optimize="meshopt", phone=True)
rk.save(SLUG, passport={k: v for k, v in P.items() if k != "screenshot"})
```

## 4. Числа прогона

Прогон: 3,7 с на весь рецепт (сборка, обрезка скриншота 1082 × 2202 → 540 × 1140 JPEG q88, утверждения, EEVEE 48 спп 768 × 1024 —
2,8 с, экспорт, meshopt, gltfpack); итераций правки — 0 (код D1/02 + загрузка скриншота из файла).

| величина | значение |
|---|---|
| треугольники в кадре / уникальные в файле | 4 718 / 2 638 (`optimize` склеил три одинаковые линзы в один меш — `dedup`, узлов по-прежнему 3) |
| утверждения C1/16 | габарит 72,7 × 10,6 × 147 мм (±6 %), зазоры островок/линза/экран/кнопка 0 / 0 / 0,1 / 0 мм — ok |
| аудит C1/10 | кадр 44 %; `ngons`, `raw_sharp_edges`, `interpenetration` (кнопки, островок, линзы врастают в корпус — намеренно) |
| GLB: экспорт → десктоп → телефон | 186 → **53,1 КБ** (meshopt + WebP 540 × 1140) → **30,9 КБ** (`gltfpack -cc -tc -ts 0.5`: KTX2 270 × 570) |
| валидатор | десктоп 0 / 0; телефон 0 ошибок, 2 предупреждения (валидатор не знает `image/ktx2` — как у E/24) |
| three r186 | 0 ошибок консоли; текстуры 1140 px (десктоп) / 572 px (телефон) |

Взгляд на `examples/03-device-mockup/poster_blender.png`: экран — скриншот страницы рецепта 01 (мобильный вид), без растяжения и
переворота; рамка и стекло читаются; экран светится (Emission 1,0) и выглядит «включённым». Слабее: спинка и линзы в этом ракурсе не
видны — для второго экрана нужен ракурс az 150–200° (островок камер — главная «дорогая» деталь телефона).

## 5. Страница

- **Постер** (частый случай): рендер Blender → AVIF/WebP (блок `encode_web` рецепта 02) → `<picture>`; 2 ракурса — 2 картинки.
- **3D**: страница рецепта 01 (hero-lazy) без пересборки — `window.HERO_CFG = { modelPhone: 'phone_phone.glb', modelDesktop: 'phone.glb' }`;
  телефонный файл с KTX2 требует транскодер (`assets/decoders/basis/` эталона, 204 КБ br) — на медленной сети при текстуре ≤ 512²
  выгоднее WebP (F1 `09/06 §3`) [не проверено на этом ассете].
- **Смена скриншота в JS** (карусель экранов): найти материал `Screen` и заменить `map`/`emissiveMap` — у новой текстуры
  `colorSpace = THREE.SRGBColorSpace` и `flipY = false` (как у текстур glTF), иначе экран вверх ногами и блёклый
  [документация: three `GLTFLoader`; не проверено в этом прогоне].

## 6. Ворота

Утверждения (габарит ±6 %, 4 пары касаний ≤ 1 мм) — в коде; кадр — аудит (`frame.area` 0,3–0,7); вес — ≤ 0,8 / 1,5 МБ на hero
(53 / 31 КБ); страница — ворота рецепта 01 (`gate_check`). Проверка экрана глазом по одному кадру: текст скриншота читается, не
зеркален, углы экрана скруглены как у корпуса.

## 7. Варианты

1. **Ноутбук**: корпус-основание + крышка отдельным объектом, `D.set_origin(lid, ось петли)`, экран — тот же приём UV 0–1
   (C1/12 `laptop.py`: 304 × 212 мм, открытие 110°) [проверено: C1/12 без скриншота].
2. **Экран «горит» ярче фона** — Emission 1,0 и Neutral; для тёмного hero — Emission 1,5–2 и снизить экспозицию сцены
   [практика; не проверено].
3. **Раскрытие/поворот телефона на прокрутке** — корень `Phone` (pivot в центре корпуса) → клип или JS (рецепт 05).
4. **AR «положить на стол»** — AR-GLB без сжатия + USDZ (рецепт 12).
5. **Видео в экранах нескольких устройств** — одно видео + UV-развёртка экранов по его областям вместо N видеотекстур
   [V:BH1R29YvLOk 47:40] [не проверено].

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| экран — часть корпуса, UV «как получилось» | скриншот растянут, повёрнут, лезет на рамку | отдельный меш, UV 0–1 по габариту экрана (D1 `05/04 §2`) |
| скриншот другого аспекта | растяжение 3–10 % (1082 × 2202 против 0,474) | `fit_screenshot` — обрезка под аспект, верх страницы сохранён |
| картинка без sRGB | экран блёклый в Blender и three | `colorspace_settings.name = "sRGB"` (E `08/01 §5.4`) |
| процедурный градиент на экране | в glTF экран белый (M4.1) | только картинка (Image Texture) |
| камера/кнопки числами «на глаз» | парят в 20–40 мм (sonnet, M2.2) | координаты от габарита корпуса + `rk.asserts(touch=…)` |
| масштаб «в юнитах» | телефон 1–3 м (M2.1) | метры из справочника, утверждение габарита |

## Ссылки

D1 `../05-modeling/04-styles-and-archetypes.md §2`, `../99-raw/experiments/D1/02-phone-mockup`; C1 `../04-ai-agents-mcp/04-agent-operating-protocol.md §3.2`
(справочные размеры), `../99-raw/experiments/C1/12-protocol-objects` (`phone.py`, `laptop.py`); E `../08-export-gltf/01-export-contract.md §5`;
F1 `../09-web-runtime/06-deliverables-ar-ktx2-webgpu.md §3`.
