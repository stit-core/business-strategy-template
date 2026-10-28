# Движки и управление цветом: EEVEE, Cycles, Workbench, виды AgX / Standard / Khronos PBR Neutral — цвет бренда от hex до пикселя в Blender 5.2.2 и three r186

Волна 2 · агент D2 · 23.09.2026 · источников: 13 (конфиг OCIO Blender 5.2.2, руководство 5.2, исходники three r186,
спецификация Khronos PBR Neutral и статья её автора, пресс-релиз Khronos, RNA 5.2.2, 3 дайджеста видео, файлы волны 1) ·
экспериментов: 2 (`99-raw/experiments/D2/01-brand-color` — 16 цветов × 11 видов Blender × 5 тонмапперов three, рендеры
EEVEE/Cycles/three, IBL; `D2/02-engines` — время и шум) · Blender 5.2.2 LTS (OCIO 2.5.0), three 0.186.0, Chromium (ANGLE GL,
Intel Iris Xe), CPU 20 потоков.

Материалы — `01-materials-pbr.md`, свет и камера — `02-lighting-camera-composition.md`, форматы и композитинг —
`04-outputs-for-web.md`; тонмаппинг на странице целиком — `../09-web-runtime/01-…` (F1), экспорт — `../08-export-gltf/01-…`.

## Выжимка для агента

1. **Цвет бренда на сайте — пара «Khronos PBR Neutral» (Blender) ↔ `THREE.NeutralToneMapping`**: между рендерами ≤ 1,1 ΔE2000, к hex под ровным серым светом 1,8–1,9 в среднем (макс. 4,3). → §2.3 [проверено]
2. **Hex — это sRGB: переводить в линейный** (`bpyx.color("#C65D3B")` → (0,5647; 0,1095; 0,0437)); числа sRGB в сокете дают бледный цвет (M3.10). → §2.1 [проверено]
3. **AgX (умолчание 5.x) не для брендового цвета**: ΔE к hex 7,1 в среднем и до 14,3 даже без освещения; жёлтый #FFD60A → #CAAF5C, почти белый #F5F5F4 → #C1C1C1, салатовый #3DDC84 → #72B789. → §2.2 [проверено]
4. **«AgX делает красный розовым» — на ярко освещённых участках**: при свете ×2 красный #E4002B → #EA605C, терракота → #D68568; при эмиссии 1,0 сдвиг мал (ΔE 3,8). → §2.2 [проверено]
5. **Look «AgX - Punchy» темнит на 0,10 OKLab L** (ΔE 12,9 к hex), «AgX - Base Contrast» = look None (тождество в конфиге). → §2.2 [проверено: D2/01; конфиг OCIO]
6. **Неосвещённые элементы (логотип, экран, UI-плашка)**: в Blender точный hex даёт только Standard; PBR Neutral сдвигает на −0,04 (ΔE до 5,5); в three — `material.toneMapped = false` у `MeshBasicMaterial` (GLTFLoader сам этого не делает). → §2.4 [проверено]
7. **Standard под светом сереет в тёмных**: +0,04 белого блика (Френель F0 0,04) — navy ΔE 9,7, почти чёрный 12,6; «выключить тонмаппинг ради точности» хуже Neutral. → §2.2 [проверено] [V:0oIZoSg03PY 04:02]
8. **Зона точности Neutral — линейные каналы 0,08…0,8 (sRGB ≈ 80…231)**: канал > 0,8 (ярко-жёлтый, оранжевый #FF6B00) сжимается — ΔE 3,6–4,3; 255 на входе → 243 на выходе. → §2.3 [документация: S4, S5] [проверено]
9. **Свет витрины бренда — серый (1, 1, 1), без цветовой температуры**; цвет «не похож» — меняй экспозицию и свет, а не base color. → §2.5 [V:0oIZoSg03PY 05:48, 30:03, 41:17]
10. **AgX Blender ≠ AgX three**: three светлее на +3,4…+3,7 L* (ΔE 3,3–3,8, макс. 7,1): three линеаризует выход AgX степенью 2,2, Blender для sRGB берёт «AgX Base Rec.1886» (степень 2,4); замена на 2,4 до первой компиляции — ΔE 1,3–1,9. → §2.6 [проверено]
11. **ACES Blender ≠ ACES three**: «ACES 1.3/2.0» против `ACESFilmicToneMapping` — ΔE 9–12, three светлее на 10–14 L*; для совпадения не использовать. → §2.2 [проверено]
12. **EEVEE выносит яркое из HDRI в «солнце»** (`world.sun_threshold` = 10 по умолчанию): грани вверх на +13,4 L* светлее Cycles и на +19 L* светлее three — это и есть «EEVEE светлее three на ≈ 13 L*» (E/20). Для сравнения с вебом — Cycles или `sun_threshold = 0`. → §3 [проверено]
13. **three (PMREM) ближе к Cycles, чем EEVEE**: на белой сфере под студийным HDRI |ΔL*| макс. 5,8 (three), 13,4 (EEVEE по умолчанию), 11,9 (EEVEE без «солнца»). → §3 [проверено]
14. **Сравнивать цвет Blender и three — под ровным миром** («белая печь», мир (1,1,1) × 1): EEVEE, Cycles и three совпадают до 0,3 ΔE; HDRI добавляет ±6 L* от IBL. → §3, §5 [проверено]
15. **Превью — EEVEE 16 сэмплов (2,6 с на 1024²), финал EEVEE ≥ 64** (7,5 с; при 16 — зерно в мягких тенях: шум 4,2 против 2,4). → §1.2 [проверено]
16. **Трассировка EEVEE (`use_raytracing`) +60 % времени** (12,3 с против 7,5 с на 1024²) — включать, когда металл и глянец должны отражать соседей; для матового не нужна. → §1.2 [проверено]
17. **Cycles на этом CPU — только с явными сэмплами** (умолчание 4096!): 64 + OIDN — 12 с на 512², 40 с на 1024², 67 с на 1920×1080; OIDN — единственный денойзер. → §1.3 [проверено]
18. **Workbench (0,6 с на 1024²)** — проверка силуэта, кадра и габаритов, не вид материалов. → §1.4 [проверено]
19. **Bloom в EEVEE 5.x нет — нода Glare «Bloom»** в `scene.compositing_node_group`. → `04-outputs-for-web.md` §5 [проверено]
20. **PNG/JPEG/WebP/AVIF сохраняются с видом сцены, EXR — линейно без вида**; переопределение — `image_settings.color_management = "OVERRIDE"`. → §2.7 [V:qt1GidFwVt0 19:07] [проверено: RNA 5.2.2]
21. **Рабочее пространство оставлять Linear Rec.709** (glTF и sRGB-экраны — та же гамма); ACEScg/Rec.2020 — только для печати и кино; `bpy.data.colorspace.working_space` только для чтения, смена — `bpy.ops.wm.set_working_color_space` (W3). → §2.1 [документация: S2] [проверено: RNA; W3 §1]
22. **Проверку цвета делать до рендеров**: OCIO внутри Blender (PyOpenColorIO 2.5.0) считает «hex → пиксель» для любого вида за миллисекунды — совпадает с рендером до 0,73 ΔE. → §5 [проверено]

## 1. Движки Blender 5.2.2: что есть и сколько стоит

### 1.1. Выбор движка

| задача | движок | почему |
|---|---|---|
| превью кадра, серия иконок, секвенция, рендер в MCP-вызове | EEVEE (`BLENDER_EEVEE`) | 2–12 с на кадр 1024²–1920×1080 на Iris Xe |
| финал с металлом/глянцем, отражающим соседей | EEVEE + `use_raytracing` | отражения как в Cycles за ×1,6 времени |
| стекло с преломлением, каустики, точная IBL-освещённость, запекание | Cycles CPU | EEVEE не запекает; стекло и анизотропию сверять с Cycles (E `../08-export-gltf/01 §6.1`) |
| проверка силуэта, кадра, габаритов | Workbench | 0,6 с на 1024² |

`BLENDER_EEVEE_NEXT` в 5.2 не принимается (TypeError) — движок один, `BLENDER_EEVEE`; список движков RNA занижает —
присваивать и ловить `TypeError` (`bpyx.set_engine`) [проверено: B, PLAN]. У EEVEE 5.2 нет `use_bloom`, `use_gtao`,
`use_ssr` (удалены в 4.2); bloom — нода Glare в композиторе (B `../03-bpy-api/02 §6`).

### 1.2. EEVEE: сэмплы, тени, трассировка

Свойства `scene.eevee` в 5.2.2 (RNA, умолчания): `taa_render_samples` 64, `taa_samples` 16 (вьюпорт),
`use_raytracing` False, `ray_tracing_method` SCREEN | PROBE, `use_shadows` True, `shadow_ray_count` 1, `shadow_step_count` 6,
`shadow_resolution_scale` 1.0, `use_fast_gi` False (`fast_gi_method` AMBIENT_OCCLUSION_ONLY | GLOBAL_ILLUMINATION),
`clamp_surface_indirect` 10, `volumetric_samples` 64, `gi_diffuse_bounces` 3 [проверено: bpy_probe SceneEEVEE].
Мир: `world.sun_threshold` 10, `sun_angle` 0,00918, `use_sun_shadow` True, `probe_resolution` 1024 [проверено: RNA World].

| рендер (D2/02, студийная сцена, вид PBR Neutral) | время | шум в мягкой тени |
|---|---|---|
| EEVEE 512², 16 / 64 сэмплов | 1,9 / 5,3 с | 4,17 / 2,41 |
| EEVEE 1024², 16 / 64 | 2,6 / 7,5 с | 4,15 / 2,37 |
| EEVEE 1024², 64 + трассировка | 12,3 с | 2,27 |
| EEVEE 1920×1080, 64 | 11,3 с | — |

[проверено]. Шум от сэмплов почти не зависит от размера кадра; 16 сэмплов — зерно в
полутени (заметно на увеличении), 64 — чисто. Правило C1 «превью ≤ 30 с» выполняется EEVEE до 1920×1080 с запасом
(`../04-ai-agents-mcp/05`, M6.7).

### 1.3. Cycles на CPU этой машины

Умолчания 5.2.2: `samples` **4096**, `preview_samples` 1024, адаптивная выборка с порогом 0,01, `use_denoising` True,
`denoiser` — только `OPENIMAGEDENOISE` (OptiX на машине без NVIDIA недоступен), отскоки: всего 12, diffuse 4, glossy 4,
transmission 12, volume 0, transparent 8 [проверено: RNA 5.2.2]. Скрипт «для красоты» без числа сэмплов рендерит 4096 и
не укладывается в вызов MCP (M6.7).

| Cycles CPU + OIDN | 16 сэмплов | 64 сэмпла |
|---|---|---|
| 512² | 5,3 с (шум 1,48) | 11,9 с |
| 1024² | — | 39,8 с |
| 1920×1080 | — | 67,1 с |

[проверено]. OIDN на 16 сэмплах уже чище EEVEE-64 в тенях. Правила машины (≤ 64 сэмплов, ≤ 10 мин на запуск):
Cycles 1024² × 64 — до ~15 кадров за запуск; секвенции длиннее — EEVEE. Чёрные пятна внутри стекла — нехватка
glossy/transmission-отскоков [V:Sv2wqwsvx-8 03:53].

### 1.4. Workbench

0,62 с на 1024² [проверено]: плоские цвета и студийный matcap, без мягких теней и материалов. Для проверки
кадра, силуэта и «глиняного» вида (`render_views.py --engine workbench`).

```python
# Blender 5.2.2 — [проверено] пресеты рендера по задаче
import bpy

def render_preset(mode="eevee_final", scene=None):
    """workbench | eevee_preview (16) | eevee_final (64) | eevee_rt (64 + трассировка) | cycles (CPU, 64 + OIDN)."""
    s = scene or bpy.context.scene
    if mode == "workbench":
        s.render.engine = "BLENDER_WORKBENCH"
    elif mode.startswith("eevee"):
        s.render.engine = "BLENDER_EEVEE"                      # не BLENDER_EEVEE_NEXT (TypeError в 5.2)
        s.eevee.taa_render_samples = 16 if mode == "eevee_preview" else 64
        s.eevee.use_raytracing = (mode == "eevee_rt")
    elif mode == "cycles":
        s.render.engine = "CYCLES"
        s.cycles.device = "CPU"
        s.cycles.samples = 64                                  # умолчание 4096 — всегда задавать
        s.cycles.use_denoising = True
        s.cycles.denoiser = "OPENIMAGEDENOISE"
    else:
        raise ValueError(mode)
    return s.render.engine

for m in ("workbench", "eevee_preview", "eevee_final", "eevee_rt", "cycles"):
    print(m, render_preset(m))
```

## 2. Управление цветом: что происходит с цветом бренда

### 2.1. Конвейер Blender 5.2.2

Сцена хранит линейные значения в рабочем пространстве файла (Linear Rec.709 по умолчанию; Linear Rec.2020 и ACEScg —
по выбору; `bpy.data.colorspace.working_space` в Python только для чтения, меняется оператором
`bpy.ops.wm.set_working_color_space`; цвета при смене пересчитываются приблизительно) [документация: S2] [проверено: RNA; W3 §1].
Показ и запись PNG: экспозиция (×2^exposure) → look → вид (view transform) → дисплей (sRGB) → gamma [документация: S2].
Что внутри видов (конфиг `datafiles/colormanagement/config.ocio`, OCIO 2.5, «RRT version ut33») [S1]:

| вид (дисплей sRGB) | как устроен | для чего |
|---|---|---|
| Standard | только кривая sRGB (кусочная); всё > 1 обрезается по каналам | неосвещённое, UI-плашки, запечённое |
| Khronos PBR Neutral | 3D-LUT `pbrNeutral.cube` (лог-шейпер lg2 −9…+10, тетраэдрическая интерполяция) — приближение формулы | продукт и бренд при ровном свете |
| AgX | E-Gamut → лог (−12,47…+12,53) → LUT `AgX_Base_sRGB.cube` → трактуется как Rec.1886 (степень 2,4) → sRGB | атмосферный hero, HDR-свет |
| Filmic | лог + 1D-LUT; помечен устаревшим | старые файлы |
| ACES 1.3 / 2.0 | встроенные преобразования OCIO (SDR-VIDEO 1.0 / SDR-100nit-REC709 2.0) | кино-конвейер |

Looks AgX [S1]: «Base Contrast» — контраст 1 (тождество), «Medium High» 1,2, «High» 1,4 (насыщенность 0,95),
«Very High» 1,57 (0,9), «Medium Low» 0,9, «Low» 0,8, «Very Low» 0,7, «Punchy» — подъём теней + степень 1,0912 в лог-пространстве
(темнит), «Greyscale». Для Filmic — свои looks («Medium High Contrast» и т. д.); список looks зависит от выбранного вида
(проверять `bpyx.enum_values(view_settings, "look")`).

Цвет из дизайн-системы — sRGB (hex/CSS); в сокеты Blender — линейный: `c ≤ 0,04045 ? c/12,92 : ((c+0,055)/1,055)^2,4`
(`bpyx.color`, `Color.from_srgb_to_scene_linear()`). Карты цвета — `sRGB`, карты данных — `Non-Color`
[V:qt1GidFwVt0 10:42–11:00].

```python
# Blender 5.2.2 — [проверено] цвет для веб-продукта: вид, запись, hex → линейный
import sys, bpy
sys.path.insert(0, "../../scripts/3d")
import bpyx

def web_color_setup(scene=None, view="Khronos PBR Neutral"):
    scene = scene or bpy.context.scene
    scene.display_settings.display_device = "sRGB"
    bpyx.set_color_management(view, look="None", exposure=0.0, gamma=1.0, scene=scene)  # проверка по фактическому списку
    scene.render.image_settings.color_management = "FOLLOW_SCENE"   # PNG/WebP/AVIF — с видом сцены (EXR — линейно)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.sun_threshold = 0.0      # EEVEE: не выносить яркое из HDRI в «солнце» (верхние грани +13 L*, §3)
    return scene.view_settings.view_transform, scene.view_settings.look

mat, bsdf = bpyx.principled("Brand_Terracotta", base_color="#C65D3B", roughness=0.5)   # hex = sRGB → линейный
print(web_color_setup(), [round(v, 4) for v in bsdf.inputs["Base Color"].default_value])  # (0.5647, 0.1095, 0.0437, 1)
```

### 2.2. Виды Blender и тонмапперы three против hex: числа

16 брендовых цветов (насыщенные, пастели, почти чёрный, почти белый, серые), ΔE2000 к исходному hex, среднее / максимум.
«Неосвещённый» — эмиссия 1,0 / `KHR_materials_unlit`; «белая печь» — PBR-плитка (Principled по умолчанию, roughness 0,5)
лицом к камере под миром (1,1,1) × 1; «свет ×2» — вдвое ярче (расчёт OCIO) [проверено]:

| вид / тонмаппер | неосвещённый | белая печь | свет ×2 |
|---|---|---|---|
| Blender Standard = three `NoToneMapping` | 0,00 / 0,00 | 3,8 / 12,6 | 11,1 / 18,5 |
| **Blender Khronos PBR Neutral** | 2,87 / 5,49 | **1,90 / 4,30** | 7,9 / 15,5 |
| **three `NeutralToneMapping`** | 2,85 / 5,73 (0 с `toneMapped=false`) | **1,77 / 4,10** | 7,8 / 15,3 |
| Blender AgX (look None) | 7,07 / 14,27 | 9,4 / 15,5 | 11,2 / 20,3 |
| Blender AgX + Medium High / High | 6,04 / 11,2 · 5,82 / 10,7 | 7,8 / 13,2 · 6,9 / 13,5 | — |
| Blender AgX + Punchy | 12,94 / 18,14 | 11,9 / 18,8 | 7,1 / 13,6 |
| three `AgXToneMapping` | 8,44 / 14,45 | 11,5 / 15,6 | 12,9 / 21,8 |
| Blender Filmic | 6,7 / 11,8 | 9,4 / 15,0 | 10,3 / 18,5 |
| Blender ACES 1.3 / 2.0 | 9,3 / 11,0 · 12,4 / 16,4 | 7,5 / 9,6 · 10,9 / 16,4 | 6,8 / 11,3 · 5,5 / 10,7 |
| three `ACESFilmicToneMapping` | 4,77 / 8,03 | 7,0 / 8,9 | 13,0 / 21,6 |

Что видно по цветам (неосвещённый, выход вида, сдвиг OKLCH ΔL / ΔC / Δh) [проверено: D2/01, `table_report.md`]:

| hex | AgX | AgX Punchy | PBR Neutral |
|---|---|---|---|
| красный #E4002B | #CE2D2E (−0,022 / −0,038 / +2,3°) | #AC0407 (−0,109) | #E2082B (−0,002 / −0,003 / +0,2°) |
| терракота #C65D3B | #B85E3B (−0,018 / −0,016 / +2,9°) | #99431B (−0,111) | #C14F1D (−0,030 / +0,016) |
| оранжевый #FF6B00 | #D56F30 (−0,053 / −0,052) | #BA5301 | #F06923 (−0,023 / −0,017) |
| жёлтый #FFD60A | #CAAF5C (−0,124 / −0,072) | #B5972A | #F0CB23 (−0,036 / −0,013) |
| синий #0969DA | #2275BF (+0,013 / −0,053 / −7,5°) | #045BA3 | #0068DA (−0,003 / +0,001) |
| фиолетовый #635BFF | #6A79CE (+0,025 / −0,105 / −4,0°) | #495BB8 | #544BEF (−0,048 / 0,000) |
| пастель #BDE0FE | #ADBBC5 (−0,107 / −0,035) | #93A4B1 | #AFD2EE (−0,044) |
| почти белый #F5F5F4 | #C1C1C1 (−0,158) | #ADADAC | #EBEBEA (−0,029) |

Выводы: AgX выцветает (хрома −0,04…−0,105) и смещает синие к голубому (−4…−8°); PBR Neutral сохраняет оттенок
(|Δh| ≤ 1,5° у насыщенных) и на неосвещённом темнит на смещение 0,04. Standard точен только без освещения: под светом
Френель добавляет 4 % белого, и тёмные сереют (navy 9,7, почти чёрный 12,6). Причина — спецификация: Neutral вычитает
именно эти 0,04 [S4, S5] [V:0oIZoSg03PY 15:19–16:45].

### 2.3. Пара по умолчанию: Blender «Khronos PBR Neutral» ↔ three `NeutralToneMapping`

Формула Khronos (F90 = 0,04; Ks = 0,76; Kd = 0,15): `c_out = c_in − 0,04` при всех каналах в [0,08; 0,8]; выше — сжатие
с путём к белому; ниже — квадратичный «носок»; оттенок не меняется; обратима аналитически [S4]. three реализует формулу
1:1, Blender — 3D-LUT из того же репозитория Khronos [S1, S3]. Замер рендеров (ΔE2000 между Blender и three) [проверено]:

| пара | неосвещённый | белая печь (плитка / сфера) | HDRI (плитка) |
|---|---|---|---|
| Standard ↔ `NoToneMapping` | 0,01 / 0,02 | 0,22–0,30 / макс. 0,73 | 0,53 / 0,70 |
| **Khronos PBR Neutral ↔ `NeutralToneMapping`** | 0,19 / 0,44 | **0,23–0,36 / макс. 1,08** | 0,64 / 1,02 (EEVEE) |
| AgX ↔ `AgXToneMapping` | 3,78 / 7,14 (three +3,4 L*) | 3,3–3,6 / 6,2 (+3,6 L*) | 3,78 / 6,84 |
| AgX ↔ AgX three со степенью 2,4 | 1,91 / 4,58 (+0,9 L*) | 1,31–1,50 / 3,5 (+1,0 L*) | 2,17 / 4,98 |
| AgX Punchy ↔ `AgXToneMapping` | 12,2 / 16,5 (+13 L*) | 12,5 / 16,1 (+14 L*) | 12,0 / 15,3 |

Зона гарантии: линейные 0,08…0,8 → в 8-битном sRGB ≈ 80…231 на каждом канале [S5] [V:0oIZoSg03PY 18:29]. Цвета с
каналом 255 (ярко-жёлтый, оранжевый, почти белый) сжимаются к 243 и бледнеют на ΔE 3–4 — это компромисс Neutral, не
ошибка [проверено: D2/01: orange 4,3, yellow 3,6].

```js
// three r186 — [проверено] пара к Blender «Khronos PBR Neutral»
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {HDRLoader} from 'three/addons/loaders/HDRLoader.js';

const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
renderer.outputColorSpace = THREE.SRGBColorSpace;      // умолчание, но писать явно
renderer.toneMapping = THREE.NeutralToneMapping;       // = Blender view «Khronos PBR Neutral», look None
renderer.toneMappingExposure = 1.0;                    // = view_settings.exposure 0 (2^0); +1 стоп в Blender = 2.0
const scene = new THREE.Scene();
const hdr = await new HDRLoader().loadAsync('studio.hdr');
hdr.mapping = THREE.EquirectangularReflectionMapping;
scene.environment = hdr;                               // PMREM строится автоматически
const gltf = await new GLTFLoader().loadAsync('model.glb');
gltf.scene.traverse((o) => {                           // unlit (KHR_materials_unlit) → точный hex, как Standard в Blender
  if (o.isMesh && o.material.isMeshBasicMaterial) o.material.toneMapped = false;
});
scene.add(gltf.scene);
```

### 2.4. Неосвещённые элементы: логотипы, экраны, UI-плашки

- В Blender вид применяется ко всему, включая эмиссию и unlit [S5]; точный hex на плашке даёт только Standard
  [проверено: D2/01: Standard 0,00, Neutral 2,87 / 5,49, AgX 7,07 / 14,27].
- В three GLTFLoader создаёт для `KHR_materials_unlit` `MeshBasicMaterial` без `toneMapped = false` — тонмаппер
  применяется и к unlit [S7] [проверено: D2/01: three Neutral 2,85 → 0,00 с `toneMapped = false`]. model-viewer unlit не
  тонмаппит [S5].
- Вариант «весь кадр в AgX, а логотип точный»: обратить вид (OCIO `DisplayViewTransform` с `TRANSFORM_DIR_INVERSE`) и
  задать эмиссию обращённым значением. Работает для 13 из 16 цветов; AgX не достигает оранжевого (остаток 6,0),
  жёлтого (10,3), фиолетового (4,75), пастель #BDE0FE требует отрицательного красного [проверено].
- Экран-скриншот в мокапе: картинка → прямо в Surface (unlit), Standard или отдельный проход без тонмаппинга
  (`01-materials-pbr.md` §5, E `../08-export-gltf/01 §6.3`).

### 2.5. Свет и экспозиция под брендовый цвет

- Свет витрины серый: лампы (1,1,1), HDRI нейтральный; тёплый/холодный — только в атмосферном кадре [V:0oIZoSg03PY 05:48,
  41:17] [S5: D65 против D50 у маркетинга — брать маркетинговый hex как base color].
- Цвет не совпал — менять экспозицию (`view_settings.exposure` в Blender, `toneMappingExposure = 2^exposure` в three) и
  свет, не base color: «we don't paint the product; we change the lighting» [V:0oIZoSg03PY 30:03–31:26].
- Под Neutral белые и светлые поверхности держать в линейных ≤ 0,8 (иначе сжатие и путь к белому): калибровка ламп —
  `02-lighting-camera-composition.md` §2.
- Экспозицию проверять видом False Color (серый — норма, зелёный — +1 стоп, голубой — −1 стоп) [V:5UCc3Z_-ibs 08:49].

### 2.6. AgX: когда брать и как совпасть с three

AgX — для hero с контрастным светом, закатом, сильными бликами, где важны плавные переходы, а не hex [S6]
[V:0oIZoSg03PY 23:07]. Сравнение видов в одном кадре [V:bIYysN4KheI 04:57–05:47]: Standard держит оттенок в тёмных, но
блики уходят в «неон» (циан, жёлтый, маджента); PBR Neutral — «perfect for real-time product visualization on the web», но
при цветном или очень ярком свете ломается; AgX лучше всех держит яркий и цветной свет. Если AgX нужен и в Blender, и на странице: three светлее на 3,4–3,7 L*, потому что линеаризует
выход степенью 2,2 (`tonemapping_pars_fragment.glsl.js`), а Blender для дисплея sRGB использует вид «AgX Base Rec.1886»
(степень 2,4) [S1, S3]. Замена 2,2 → 2,4 в шейдере до первой компиляции сводит расхождение к 1,3–1,9 ΔE
(+0,8…+1,1 L*); остаток — LUT Blender против полиномиального приближения three [проверено]. Замена после первого
рендера не действует: программа берётся из кэша [проверено].

```js
// three r186 — [проверено] AgX «как в Blender» (степень 2,4)
import * as THREE from 'three';
// до создания материалов и ПЕРВОГО рендера: иначе three возьмёт скомпилированную программу из кэша
THREE.ShaderChunk.tonemapping_pars_fragment = THREE.ShaderChunk.tonemapping_pars_fragment.replace(
  'color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );',
  'color = pow( max( vec3( 0.0 ), color ), vec3( 2.4 ) );');
const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.toneMapping = THREE.AgXToneMapping;           // Blender view «AgX», look None; Punchy не повторяется (+13 L*)
```

Look «Punchy» и другие looks AgX в three не повторить встроенными средствами (three без looks) — либо Neutral на обеих
сторонах, либо принять разницу.

### 2.7. Запись файлов и цвет

- PNG, JPEG, WebP, AVIF, видео пишутся с видом, look и экспозицией сцены (`FOLLOW_SCENE`); EXR — линейный, без вида;
  `image_settings.color_management = "OVERRIDE"` задаёт свой вид для вывода [V:qt1GidFwVt0 19:07–20:38] [проверено: RNA
  5.2.2: `FOLLOW_SCENE | OVERRIDE`].
- Для постобработки (денойз запечённых карт, перекодирование) вид Standard, иначе AgX применится второй раз (E
  `../08-export-gltf/02 §6.4`).
- Широкая гамма и HDR: Blender 5.2 пишет PNG/JPEG/WebP/AVIF/TIFF с гаммой Display P3, HDR — AVIF/PNG (203 нит), видео HDR —
  H.265/AV1 10–12 бит [S2]. Для сайта по умолчанию — sRGB 8 бит: glTF, three и большинство экранов живут в Rec.709
  [V:0oIZoSg03PY 38:24] [S5].

## 3. IBL: почему EEVEE, Cycles и three расходятся под HDRI

Изолированная белая сфера (альбедо 0,8, `Specular IOR Level` 0 — чистый Ламберт), HDRI `studio_small_09` × 1, вид
Standard; L* по нормалям, отклонение от Cycles (эталон) [проверено: D2/01, `out_ibl/ibl_table.txt`]:

| нормаль | Cycles | EEVEE, `sun_threshold` 10 (умолч.) | EEVEE, `sun_threshold` 0 | three r186 |
|---|---|---|---|---|
| вверх 80° | 85,8 | 99,2 (+13,4) | 88,5 (+2,7) | 80,0 (−5,8) |
| вперёд | 84,2 | 79,5 (−4,8) | 81,1 (−3,1) | 78,6 (−5,6) |
| вперёд-вверх 45° | 89,4 | 95,3 (+5,9) | 85,1 (−4,3) | 86,2 (−3,1) |
| влево 45° | 68,7 | 64,0 (−4,6) | 74,0 (+5,3) | 74,2 (+5,6) |
| вправо 45° | 96,2 | 98,0 (+1,8) | 89,8 (−6,4) | 99,6 (+3,4) |
| вниз-вперёд | 68,0 | 70,8 (+2,8) | 79,9 (+11,9) | 70,1 (+2,1) |
| макс / среднее \|ΔL*\| | — | 13,4 / 5,5 | 11,9 / 5,6 | **5,8 / 4,3** |

Механизмы:
- EEVEE по умолчанию переносит всё ярче `sun_threshold` = 10 в одно направленное «солнце» (описание свойства в RNA:
  «the excess contribution is converted to a sun light») — софтбоксы студии сливаются в солнце сверху, верхние грани
  пересвечены, боковые темнее [проверено: RNA World; D2/01]. Это объясняет открытый вопрос E/20: вверх EEVEE 99,2 против
  three 80,0 (+19 L*).
- Без «солнца» EEVEE считает диффузный свет мира по сглаженному представлению (разброс ±12 L*, тёмная сторона светлее).
- three: `getIBLIrradiance = π · textureCubeUV(env, n, 1.0)` по PMREM (GGX-выборка, 256 сэмплов) [S3] — ошибка до 6 L*.
- Под равномерным миром все трое совпадают (линейная яркость плитки EEVEE 0,478 / Cycles 0,478; ΔE Blender↔three ≤ 0,36)
  [проверено].
- Cycles считает переотражения соседей (светящиеся unlit-плитки, пол, стены), EEVEE без трассировки и three — нет: в сценах
  с соседями Cycles ещё на ≈ 5 L* светлее [проверено: D2/01, палитра под HDRI].

Правила: для сравнения «Blender против веба» — мир равномерный или Cycles; если EEVEE — `world.sun_threshold = 0`; пороги
`gltf_diff.py` (ΔE ≤ 3,5) под направленным HDRI не достижимы даже при идеальном экспорте: для IBL заложить ±6 L*.

## 4. Как выбрать вид под задачу

| задача | Blender | three | почему |
|---|---|---|---|
| продукт/иконка с цветом бренда, светлый сайт | Khronos PBR Neutral | `NeutralToneMapping` | ΔE к hex ≈ 2, пара ≤ 1,1 |
| атмосферный hero (контровой свет, закат, неон) | AgX (+ High Contrast по вкусу) | `AgXToneMapping` (+ степень 2,4) | плавные блики; бренд не критичен |
| неосвещённое: запечённый свет, экран, логотип | Standard | `toneMapped = false` / `NoToneMapping` | точный hex |
| предрендер без реалтайма | Neutral (бренд) или AgX (атмосфера) | — | пиксель = файл |
| запечённые карты, денойз, служебные рендеры | Standard | — | без повторного тонмаппинга |

Filmic устарел (заменён AgX) [S2]; ACES 1.3/2.0 для сайта не брать — выцветает бренд [V:0oIZoSg03PY 02:18], в three
другой ACES [проверено].

## 5. Проверка цвета кодом (до и после рендера)

«hex → пиксель» для любого вида без рендера — PyOpenColorIO внутри Blender и его же конфиг (совпадает с рендером до
0,73 ΔE) [проверено]:

```python
# Blender 5.2.2 — [проверено] что вид сделает с hex (без рендера)
import os, bpy
import PyOpenColorIO as OCIO

CFG = OCIO.Config.CreateFromFile(os.path.join(os.path.dirname(bpy.app.binary_path), "%d.%d" % bpy.app.version[:2],
                                              "datafiles", "colormanagement", "config.ocio"))

def view_hex(hexcolor, view="Khronos PBR Neutral", look=None, light=1.0):
    """light=1 — неосвещённый (эмиссия 1.0); 2.0 — вдвое больше света. Возвращает hex на экране sRGB."""
    s = [int(hexcolor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in s]
    g = OCIO.GroupTransform()
    if look:
        g.appendTransform(OCIO.LookTransform(src="Linear Rec.709", dst="Linear Rec.709", looks=look))
    g.appendTransform(OCIO.DisplayViewTransform(src="Linear Rec.709", display="sRGB", view=view))
    out = CFG.getProcessor(g).getDefaultCPUProcessor().applyRGB([light * c for c in lin])
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c * 255))) for c in out)

for v, lk in (("Standard", None), ("AgX", None), ("AgX", "AgX - Punchy"), ("Khronos PBR Neutral", None)):
    print(v, lk, view_hex("#E4002B", v, lk), view_hex("#E4002B", v, lk, light=2.0))
# Standard #E4002B / #FF003D; AgX #CE2D2E / #EA605C; Punchy #AC0407 / …; Neutral #E2082B / #F8505B
```

Тест «белой печи» по рендеру (как «3D Macbeth» Khronos [V:0oIZoSg03PY 10:58]): плитка лицом к ортокамере под миром
(1,1,1) — центр должен дать hex с ΔE ≤ 2 (Neutral); выше 4 — ошибка цвета или вида:

```python
# Blender 5.2.2 — [проверено] «белая печь»: hex → рендер EEVEE → hex и ΔE2000
import bpy, math, os, sys, tempfile
sys.path.insert(0, "../../scripts/3d")
sys.path.insert(0, "99-raw/experiments/D2/01-brand-color")
import bpyx
from palette import de2000, srgb2lab, hex2srgb      # CIEDE2000 (сверено с парой Sharma 2005)

def furnace_check(hexes, view="Khronos PBR Neutral", size=32):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Furnace"); sc.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 1.0
    tile = bpyx.primitive("plane", "Tile", size=1.0)
    tile.rotation_euler = (math.radians(90), 0, 0)             # нормаль −Y, к камере
    mat, bsdf = bpyx.principled("Tile", roughness=0.5); bpyx.assign_material(tile, mat)
    cam = bpyx.add_camera(location=(0, -3, 0), target=(0, 0, 0)); cam.data.type = "ORTHO"; cam.data.ortho_scale = 0.8
    bpyx.set_color_management(view)
    out, path = {}, os.path.join(tempfile.mkdtemp(), "f.png")
    for hx in hexes:
        bsdf.inputs["Base Color"].default_value = bpyx.color(hx)
        bpyx.render_still(path, resolution=(size, size), engine="EEVEE", samples=16)
        img = bpy.data.images.load(path); px = img.pixels[:]; bpy.data.images.remove(img)
        i = ((size // 2) * size + size // 2) * 4
        got = "#%02X%02X%02X" % tuple(round(px[i + k] * 255) for k in range(3))
        out[hx] = (got, round(float(de2000(srgb2lab(hex2srgb(got)), srgb2lab(hex2srgb(hx)))), 2))
    return out

print(furnace_check(["#C65D3B", "#0969DA", "#0F7A52"]))       # Neutral: ΔE ≈ 0,6–0,9
```

## Частые ошибки

1. `default_value = (0.85, 0.35, 0.25, 1)` «как в hex» — числа sRGB как линейные: цвет бледнее и розовее (M3.10) →
   `bpyx.color(hex)` [проверено].
2. Оставить AgX (умолчание 5.x) для продукта с брендовым цветом → ΔE 7–15, жёлтые и зелёные тускнеют, белый серый
   [проверено].
3. Добавить look «AgX - Punchy» «для сочности» → кадр темнее на 0,10 L, в three не повторяется (+13 L*) [проверено].
4. «Выключить тонмаппинг ради точного цвета» (Standard/`NoToneMapping`) под светом → тёмные сереют, блики обрываются
   [проверено] [V:0oIZoSg03PY 04:02].
5. Считать `AgXToneMapping` в three копией AgX Blender → +3,5 L*; и `ACESFilmicToneMapping` копией «ACES 2.0» → +14 L*
   [проверено].
6. Сравнивать Blender и three под HDRI в EEVEE по умолчанию → верхние грани +13…+19 L*; «баг экспорта», которого нет
   [проверено].
7. Ожидать точный hex на unlit-логотипе в three при `NeutralToneMapping` → −0,04 (ΔE до 5,7); нужен `toneMapped = false`
   [проверено].
8. Менять `ShaderChunk` после первого рендера → без эффекта (кэш программ) [проверено].
9. Cycles без числа сэмплов → 4096 и > 180 с в MCP-вызове (M6.7) [проверено: RNA 5.2.2].
10. `scene.render.engine = "BLENDER_EEVEE_NEXT"`, `scene.eevee.use_bloom = True` → TypeError / AttributeError в 5.2
    [проверено: B, PLAN].
11. Подгонять base color «пипеткой», пока на рендере не станет похоже → ломает разделение модели и света; менять свет
    и экспозицию [V:0oIZoSg03PY 30:03].
12. Денойз или перекодирование готового кадра под AgX → вид применяется второй раз (E `08/02 §6.4`).

## Чек-лист

- [ ] Цвета бренда заданы из hex через перевод в линейный (`bpyx.color`)?
- [ ] Вид Blender — Khronos PBR Neutral (бренд) или AgX (атмосфера) — выбран по §4, look None?
- [ ] На странице та же пара: `NeutralToneMapping` (или AgX со степенью 2,4), `toneMappingExposure = 2^exposure`?
- [ ] Unlit-элементы: Standard в Blender, `toneMapped = false` в three?
- [ ] Лампы витрины серые (1,1,1), HDRI нейтральный?
- [ ] Белые поверхности ≤ 0,8 линейного под Neutral (False Color без зелёного/жёлтого на белом)?
- [ ] Тест «белой печи» по палитре бренда: ΔE ≤ 2 (Neutral)?
- [ ] Для сравнения с three — равномерный мир, Cycles или `world.sun_threshold = 0`?
- [ ] Сэмплы заданы явно: EEVEE 16 (превью) / 64 (финал), Cycles ≤ 64 + OIDN?
- [ ] Трассировка EEVEE включена, только если металл/глянец отражают соседей?
- [ ] PNG/AVIF/WebP пишутся с видом сцены, EXR — линейные, служебные рендеры в Standard?

## Открытые вопросы и противоречия

1. **Автор тонмаппера против умолчаний**: Lalish советует AgX для HDR-сцен и Neutral для товара [V:0oIZoSg03PY 23:07];
   паспорт C1 (`../04-ai-agents-mcp/04 §3.1`) ставил AgX + Base Contrast/Punchy и `AgXToneMapping` на сайте — по замеру D2/01
   для бренда это хуже (ΔE 9–12 против 1,8–1,9); позиция базы: Neutral по умолчанию, AgX — по брифу «атмосфера».
2. **Остаток AgX Blender ↔ three после степени 2,4** (1,3–1,9 ΔE, до 4,6 на фиолетовых и жёлтых) — LUT Blender (Eary Chow)
   против полинома three (Filament); точнее — своя `CustomToneMapping` с 3D-LUT Blender (не проверено).
3. **OCIO-обращение LUT Neutral приблизительно** (остаток до 7 у тёмных): для «обратного» расчёта brand-цвета под Neutral
   брать аналитическое обращение из спецификации [S4] (не реализовано здесь).
4. **IBL**: ни EEVEE, ни three не повторяют Cycles под направленным HDRI (±6…13 L*); как калибровать HDRI для совпадения
   (размытие, `sun_threshold`, SH-проба three `LightProbeGenerator`) — не проверено.
5. **Одна машина**: Chromium/Linux/Mesa на Iris Xe; Safari, мобильные GPU и P3-экраны не проверены; на P3-экране без
   управления цветом sRGB-цвета перенасыщаются [S2].
6. **Neutral и цветной свет**: Lampel [V:bIYysN4KheI 05:26] — «серьёзные проблемы с цветным светом», Lalish — гарантия
   только при сером свете [V:0oIZoSg03PY 04:51]; совпадают: Neutral — для витрины под нейтральным светом, неон, закат,
   цветные лампы — AgX (цветной свет в D2 не замерялся).

## Источники

- [S1] Blender Foundation. `datafiles/colormanagement/config.ocio`, Blender 5.2.2 (OCIO 2.5, «RRT version ut33»; AgX по
  Sobotka / Eary Chow). Локально, прочитан целиком (1550 строк) — первоисточник видов и looks.
- [S2] Blender Foundation. Blender 5.2 Manual — Color Management (Color Spaces, Displays and Views, System Configuration,
  OpenColorIO). https://docs.blender.org/manual/en/5.2/render/color_management.html — официальный, прочитан.
- [S3] mrdoob/three.js r186: `src/renderers/shaders/ShaderChunk/tonemapping_pars_fragment.glsl.js`,
  `envmap_physical_pars_fragment.glsl.js`, `lights_fragment_maps.glsl.js`, `src/extras/PMREMGenerator.js`
  (jsDelivr three@0.186.0; репозиторий 115 767 ★, push 2026-09-22) — прочитаны нужные функции.
- [S4] Khronos Group. PBR Neutral Specification, `KhronosGroup/ToneMapping/PBR_Neutral/README.md` (2024) — формула, зона
  0,08…0,8, обратимость; первоисточник.
- [S5] E. Lalish. Tone Mapping Considerations for Physically-Based Rendering. modelviewer.dev (Google, 2024) — мотивация,
  0,8 → 231, 255 → 243, белая печь, D65/D50; автор тонмаппера.
- [S6] Khronos Group. Khronos PBR Neutral Tone Mapper Released… Press release, 2024-05-16 — принятие в Blender 4.2, three,
  model-viewer, Babylon, Filament; назначение против ACES/AgX.
- [S7] three.js r186 `examples/jsm/loaders/GLTFLoader.js` (`GLTFMaterialsUnlitExtension`) — unlit → `MeshBasicMaterial`
  без `toneMapped = false`; кэш `99-raw/cache/three-r186/`.
- [S8] Blender 5.2.2 RNA через `../../scripts/3d/bpy_probe.py`: `World.sun_threshold` (описание), `SceneEEVEE`, `CyclesRenderSettings`,
  `ImageFormatSettings.color_management` — проверено запуском.
- [S9] [V:0oIZoSg03PY] Khronos, «True-to-Life 3D Color Rendering with the PBR Neutral Tone Mapper», 2024, E. Lalish —
  дайджест W3 `91-videos/digests/0oIZoSg03PY.md`.
- [S10] [V:qt1GidFwVt0] J. Holiday, «Why Color Management Absolutely Sucks», Blender Conference 2024 — дайджест W3.
- [S11] [V:5UCc3Z_-ibs] A. Price, «How to Make Studio Lighting in Blender», 2020 — дайджест W3 (False Color, контраст).
- [S12] Агент E, `../08-export-gltf/01-export-contract.md` §1.2 (калибровка пар E/02), открытый вопрос 6 (E/20) — внутренний.
- [S13] Агент B, `../03-bpy-api/02-nodes-from-python.md` §6 (композитор 5.x, Glare) и `snippets/bpyx.py` — внутренний.
- [S14] [V:bIYysN4KheI] J. Lampel, «How to "Fix" Blender's AgX and Render Exact Colors», CG Cookie, 2026 — дайджест W3;
  проверки W3 в 5.2.2 (виды, рабочее пространство, умолчания Cycles, ловец теней) — `99-raw/reports/wave2-W3-report.md` §1.

Эксперименты: `99-raw/experiments/D2/01-brand-color` (таблица OCIO, рендеры палитры, three, IBL),
`99-raw/experiments/D2/02-engines` (время, шум).
