# Материалы PBR для сайта: Principled BSDF v2 в Blender 5.2.2 — что доезжает до three r186, пресеты «для веба» и «для рендера»

Волна 2 · агент D2 · 23.09.2026 · источников: 9 (physicallybased.info API, Poly Haven API, спецификации Khronos из кэша E,
3 дайджеста видео, файлы E, B, C2) · экспериментов: 2 (`99-raw/experiments/D2/03-materials` — 10 материалов + палитра,
EEVEE-RT/Cycles против three; `D2/01-brand-color` — цвет) · Blender 5.2.2 LTS, glTF-IO 5.2.40, three 0.186.0.

Матрица «что переживает экспорт» и расширения KHR — `../08-export-gltf/01-export-contract.md` §2.2, §5–6 (E; здесь не
повторяется); запекание процедур — `../08-export-gltf/02-baking.md`; 32 входа Principled 5.2 — `../03-bpy-api/02 §3.2` (B);
цвет и виды — `03-render-engines-color.md`; свет — `02-lighting-camera-composition.md`.

## Выжимка для агента

1. **Материал для веба = Principled BSDF + константы/картинки + группа «glTF Material Output»**; всё остальное (Noise, Color Ramp, Mix Shader, Bump, Shader to RGB) теряется молча и запекается. → §1 [проверено: E/12–13; D2/03]
2. **Доезжают почти 1:1** (ΔE2000 к Cycles 1,7–2,7): глянцевый пластик с coat, глина, хром, керамика с глазурью, ткань с обходом Sheen, неон, палитра-текстура. → §2 [проверено]
3. **Цвет — из hex через линейный** (`bpyx.color`), металлы — по таблице измеренных F0 (алюминий (0,916; 0,923; 0,924), золото (1,0; 0,773; 0,307) — канал > 1 glTF обрежет). → §2.2 [документация: physicallybased.info]
4. **Не трогать Specular IOR Level 0,5 у диэлектриков**: «матовость» — только roughness (все неметаллы отражают ≈ 4 %). → §2.1 [V:Z8AAX-ENWvQ 07:54–09:12]
5. **Sheen Weight не экспортируется — обход проверен**: вес 1 + Sheen Tint = вес × цвет (ΔE 2,2–2,7 против 3,8–5,1 без обхода). → §3.3 [проверено]
6. **Coat Roughness 0,03 (умолчание) не пишется** → в three coat зеркальный (0); задавать ≠ 0,03 явно (0,05). → §3.2 [проверено]
7. **Стекло = Transmission 1 + Thickness в группе + Volume Absorption** (цвет — объём, не Base Color, у толстого); EEVEE — `use_raytracing` + `material.use_raytrace_refraction`, Cycles — transmission bounces ≥ 12. → §3.1 [проверено] [V:DQeP363Xmn4 47:54]
8. **Стекло в three преломляет только то, что нарисовано в canvas**: на прозрачном canvas — серый диск (ΔE ≈ 10); нужен фон в самой сцене. → §3.1 [проверено]
9. **Анизотропия (шлифованный металл) в three не совпадает** даже с касательной из UV: ΔE 12–16, three темнее на 15–19 L* — для hero запекать нормаль/вид или не использовать. → §3.4 [проверено]
10. **Иридесценция доезжает приблизительно** (ΔE 4,5–7,9, другая кромка): голографию для веба — шейдером на странице или текстурой. → §3.5 [проверено]
11. **Неон = Emission Color + Strength > 1** → `KHR_materials_emissive_strength` (ΔE 0,2); свечение вокруг — bloom на странице или Glare в предрендере. → §3.6 [проверено]
12. **Low-poly — палитра-текстура 4–16 px с Closest** (сэмплер NEAREST) или цвет вершин (`export_all_vertex_colors=False`): 1 материал, мало вызовов. → §5 [проверено]
13. **Картинке задавать `colorspace_settings.name` ДО записи пикселей**: смена пространства сбрасывает сгенерированный буфер (палитра стала чёрной). → §5 [проверено]
14. **Текстуры: цвет — sRGB, данные (roughness, metallic, normal, ORM) — Non-Color**; в glTF пространство не пишется, ошибка в Blender = расхождение с вебом (ΔE 15,9). → §4 [проверено] [V:qt1GidFwVt0 10:42]
15. **Масштаб текстур — из реального размера**: Poly Haven `api.polyhaven.com/info/<id>` → `dimensions` в мм (2000 × 2000 = 2 × 2 м) → Mapping Scale = 1 / размер в метрах (при UV «1 единица = 1 м»). → §4.2 [документация: Poly Haven API]
16. **Эталон для сравнения материалов с вебом — Cycles**, не EEVEE-RT (EEVEE отражает соседей, three — нет: хром 4,2 против 1,7). → §2 [проверено]
17. **Шейдерный граф агента ≤ 20 нод**; после 22 валидность генерации падает резко; план словами → код. → §6 [исследование: C2 `../04-ai-agents-mcp/03`]
18. **Тун-заливка для веба — не Shader to RGB** (EEVEE-only, не экспортируется): unlit + запечённые ступени или `MeshToonMaterial` на странице. → §3.7 [проверено: E §5.8] [не проверено: MeshToonMaterial]

## 1. Два режима: «для веба» и «для рендера»

| режим | что можно | куда | проверка |
|---|---|---|---|
| для веба (GLB → three) | Principled BSDF; Image Texture; Normal Map (Tangent); Separate Color (ORM); Mix MULTIPLY / Math MULTIPLY на константу; Mapping POINT; группа «glTF Material Output»; Volume Absorption; unlit-связки | `KHR_materials_*` → `MeshStandardMaterial` / `MeshPhysicalMaterial` / `MeshBasicMaterial` | `gltf_diff.py --engine cycles --tone neutral` ≤ 3,5 ΔE |
| для рендера (PNG/видео) | всё: процедуры, Mix Shader, Bump, Shader to RGB, Sheen BSDF, Metallic BSDF (F82) | пиксели | взгляд + рубрика (C1 `04 §7`) |

Разрешённый набор и цена каждой потери — E `../08-export-gltf/01 §5.2, §5.8`. Процедурный материал, нужный в вебе, —
запекать (E `02 §4`: ΔE 23,5 → 5,5). Principled v2 сохраняет энергию и совместим с glTF/MaterialX/OpenPBR (описание RNA
5.2.2 — «based on the OpenPBR model», W3) [V:DQeP363Xmn4 31:50, 10:20]; самосборы «Diffuse + Glossy через Mix» не нужны и в
glTF дают один BSDF (E §5.8) [V:Z8AAX-ENWvQ 09:46].

## 2. Пресеты «для веба» (проверенные значения)

### 2.1. Таблица

| материал | Principled 5.2 (сокеты) | расширение glTF → three | ΔE three к Cycles (D2/03) |
|---|---|---|---|
| глянцевый пластик | Base = бренд, Roughness 0,15–0,25, Coat Weight 0,3–0,5, Coat Roughness 0,05 | clearcoat → `MeshPhysicalMaterial.clearcoat` | 2,03 |
| матовый пластик | Roughness 0,45–0,6 | — | [не проверено отдельно; между пластиком и глиной] |
| глина (clay) | Base тёплый светлый (#D8CFC4), Roughness 0,8–0,9 | — | 2,55 |
| резина | Base тёмный (#2B2B2B), Roughness 0,85–0,95, Specular IOR Level 0,3–0,4 | specular | [не проверено] |
| керамика с глазурью | Roughness 0,4–0,5, Coat Weight 1,0, Coat Roughness 0,02–0,05 | clearcoat | 2,70 |
| полированный металл | Metallic 1, Base = F0 металла (§2.2), Roughness 0,03–0,08 | — | хром 1,68 |
| сатинированный металл | Metallic 1, Roughness 0,3–0,45 | — | [не проверено отдельно] |
| анодированный (цветной) металл | Metallic 1, Base = цвет анодирования, Roughness 0,25–0,4 | — | см. анизотропию §3.4 |
| ткань | Roughness 0,85–0,95, Sheen Weight 1, Sheen Tint = вес × цвет, Sheen Roughness 0,4–0,6 | sheen | 2,22 (с обходом) |
| прозрачное стекло | Transmission 1, Roughness 0–0,05, IOR 1,5, Thickness (группа), Volume Absorption | transmission + volume + ior | ≈ 9,7 на прозрачном canvas (§3.1) |
| матовое стекло | то же, Roughness 0,2–0,4 | transmission + volume | [не проверено] |
| цветное стекло | Volume Absorption Color = цвет, Density 0,5–3 (1/Density = attenuationDistance, м) | volume | E/13 x04 |
| иридесценция | Thin Film Thickness 300–600 нм, Thin Film IOR 1,33, группа Iridescence Factor 1 | iridescence | 7,93 |
| неон | Base тёмный, Emission Color = цвет, Emission Strength 4–8 | emissive_strength | 0,19 |

Specular IOR Level 0,5 (F0 4 %) у всех диэлектриков по умолчанию; меньше — только для пористых (резина, ткань) по
референсу [V:Z8AAX-ENWvQ 09:12] (W3: спор с зрителями — `[спорно]`, умолчание базы 0,5). Roughness — главный рычаг
вида: одна и та же база 0,05 (зеркало) → 0,5 (пластик) → 0,9 (глина).

### 2.2. Металлы и IOR — измеренные значения

Линейные base color металлов (physicallybased.info, 86 материалов, API без ключа) [документация: S1]:

| металл | Base Color (линейный) | заметка |
|---|---|---|
| алюминий | (0,916; 0,923; 0,924) | серебристый холодный |
| серебро | (0,991; 0,985; 0,974) | почти белый |
| золото | (1,059; 0,773; 0,307) → (1,0; 0,773; 0,307) | glTF обрежет > 1 (E §2.2: ΔE 5,2) |
| медь | (0,932; 0,623; 0,522) | |
| латунь | (0,910; 0,778; 0,423) | |
| хром | (0,654; 0,685; 0,701) | темнее, чем кажется |
| никель | (0,697; 0,641; 0,563) | |
| титан | (0,441; 0,400; 0,361) | |
| железо | (0,530; 0,513; 0,494) | |

IOR диэлектриков: стекло 1,52, акрил 1,49, поликарбонат 1,585, PET 1,575, PVC 1,542, вода 1,333; фарфор base
(0,745; 0,745; 0,723) [документация: S1]. Для металла тонирует блик только Base Color при Metallic 1; у диэлектрика блик
белый [V:DQeP363Xmn4 15:26] [V:Z8AAX-ENWvQ 10:46].

### 2.3. Код: фабрика материалов «для веба»

```python
# Blender 5.2.2 / glTF-IO 5.2.40 — [проверено: 99-raw/experiments/D2/99-doc-snippets; значения — D2/03]
import sys, bpy
sys.path.insert(0, "../../scripts/3d")
import bpyx
from io_scene_gltf2.blender.com.material_helpers import create_settings_group, get_gltf_node_name

WEB = {   # входы Principled 5.2 в snake_case (bpyx.principled переводит в «Coat Weight» и т. п.)
    "plastic_gloss": dict(roughness=0.18, coat_weight=0.5, coat_roughness=0.05),
    "plastic_matte": dict(roughness=0.55),
    "clay": dict(roughness=0.85),
    "rubber": dict(roughness=0.9, specular_ior_level=0.35),
    "ceramic_glaze": dict(roughness=0.45, coat_weight=1.0, coat_roughness=0.05),   # 0.03 = не экспортируется
    "metal_polished": dict(metallic=1.0, roughness=0.05),
    "metal_satin": dict(metallic=1.0, roughness=0.35),
    "fabric": dict(roughness=0.9, sheen_roughness=0.5),
    "glass": dict(roughness=0.02, ior=1.5, transmission_weight=1.0),
    "glass_frosted": dict(roughness=0.3, ior=1.5, transmission_weight=1.0),
    "iridescent": dict(metallic=1.0, roughness=0.15, thin_film_thickness=450.0, thin_film_ior=1.33),
    "neon": dict(roughness=0.4),
}
METALS = {"aluminum": (0.916, 0.923, 0.924, 1), "silver": (0.991, 0.985, 0.974, 1), "gold": (1.0, 0.773, 0.307, 1),
          "copper": (0.932, 0.623, 0.522, 1), "brass": (0.91, 0.778, 0.423, 1), "chromium": (0.654, 0.685, 0.701, 1)}


def gltf_output(mat):
    """Группа «glTF Material Output»: Thickness, Iridescence Factor, Occlusion — читает экспортёр, Blender не рендерит."""
    name = get_gltf_node_name()
    node = mat.node_tree.nodes.new("ShaderNodeGroup")
    node.node_tree = bpy.data.node_groups.get(name) or create_settings_group(name)
    return node


def web_material(name, kind, color="#FFFFFF", sheen=0.0, thickness=0.0, absorption=None, emission=0.0):
    """Материал, который переживает glTF. color — hex (sRGB) или ключ METALS; sheen — желаемый вес (обход экспорта);
    thickness — толщина стекла в метрах (0 = тонкостенное); absorption — (hex, density) цветного стекла."""
    base = METALS.get(color, color)
    mat, bsdf = bpyx.principled(name, base_color=base if kind != "neon" else "#111111", **WEB[kind])
    if sheen > 0:                                   # вес Sheen в glTF не пишется: вес 1, Tint = вес × цвет
        bsdf.inputs["Sheen Weight"].default_value = 1.0
        bsdf.inputs["Sheen Tint"].default_value = (sheen, sheen, sheen, 1.0)
    if kind.startswith("glass"):
        mat.use_raytrace_refraction = True          # EEVEE: + scene.eevee.use_raytracing = True
        mat.thickness_mode = "SPHERE" if thickness > 0.02 else "SLAB"
        if thickness > 0:
            gltf_output(mat).inputs["Thickness"].default_value = thickness    # → KHR_materials_volume
        if absorption:
            va = mat.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
            va.inputs["Color"].default_value = bpyx.color(absorption[0]); va.inputs["Density"].default_value = absorption[1]
            out = next(n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL")
            mat.node_tree.links.new(va.outputs["Volume"], out.inputs["Volume"])
    if kind == "iridescent":
        gltf_output(mat).inputs["Iridescence Factor"].default_value = 1.0     # без группы iridescence не пишется
    if kind == "neon":
        bsdf.inputs["Emission Color"].default_value = bpyx.color(color)
        bsdf.inputs["Emission Strength"].default_value = emission or 6.0      # > 1 → KHR_materials_emissive_strength
    mat.use_backface_culling = True                 # замкнутые меши: без doubleSided
    return mat


mats = [web_material("red_gloss", "plastic_gloss", "#E4002B"), web_material("alu", "metal_satin", "aluminum"),
        web_material("velvet", "fabric", "#6B2D5C", sheen=0.5), web_material("bottle", "glass", "#FFFFFF", thickness=0.08,
        absorption=("#CDEFFF", 0.6)), web_material("holo", "iridescent", "#202020"), web_material("sign", "neon", "#FF2E88")]
print([m.name for m in mats])
```

## 3. Трудные материалы: что доезжает и чем заменить

### 3.1. Стекло

- Рецепт для glTF (E §6.2, проверен в E/13 и D2/03): Transmission Weight 1, Roughness 0–0,05, IOR (≠ 1,5 пишется только
  при transmission/volume), Thickness в группе (толщина объекта в метрах; 0 — тонкостенное), Volume Absorption (цвет толстого
  стекла), `alphaMode` OPAQUE — прозрачность через transmission, не Alpha [проверено: D2/03 — ушли transmission + volume,
  attenuationDistance = 1/Density].
- Цвет: тонкое стекло тонирует Base Color, толстое — объём (путь в стекле); оба верны (W3 §4) [V:DQeP363Xmn4 47:54]
  [V:Sv2wqwsvx-8 12:35]. Базовый цвет стекла — белый (1,1,1) [V:Sv2wqwsvx-8 02:40].
- **three: стекло преломляет содержимое прохода transmission — объекты сцены и фон canvas**, а не HTML под canvas и не
  окружение `scene.environment` [проверено: D2/03 — на прозрачном canvas серый диск, L* 78 против 93 в Blender, ΔE ≈ 10].
  Для витрины со стеклом — `scene.background` (HDRI, цвет страницы) или объект-подложка в сцене
  [проверено K/05: с фоном и предметами внутри сцены стекло преломляет; на прозрачном canvas вид зависит от фона и тонмаппинга — у K белая непрозрачная плита, `../12-recipes/09-glass-product.md`]; transmission удваивает вызовы и дорого компилируется (E: 387 мс).
- Blender: EEVEE — `scene.eevee.use_raytracing = True` + `material.use_raytrace_refraction = True`, `thickness_mode`
  SPHERE (сплошное) или SLAB (лист); Cycles — `transmission_bounces` ≥ 12 (умолчание 12), чёрные пятна — мало
  glossy/transmission-отскоков [V:Sv2wqwsvx-8 03:53]; лёгкая roughness 0,02–0,05 снижает шум [V:Sv2wqwsvx-8 27:24].
- Спор: Alpha MASK вместе с transmission — Khronos допускает (разбитое окно) [V:MFzmj1TUEKk 02:21], E требует OPAQUE
  (`[спорно]`, W3 §4) — по умолчанию OPAQUE.

### 3.2. Coat (лак, глазурь, автоэмаль)

Coat Weight и Coat Roughness → `KHR_materials_clearcoat` (E: ΔE 1,7); Coat Tint и Coat IOR теряются (покрытие в glTF
бесцветное, IOR 1,5) — оттенок лака переносить в Base Color [проверено] [V:DQeP363Xmn4 45:14]. Coat Roughness 0,03
(умолчание Principled) экспортёр не пишет — в three `clearcoatRoughness` 0 (зеркально); задавать 0,05 [проверено].

### 3.3. Sheen (ткань, бархат, персик)

Sheen в Principled 5.2 — модель микроволокон Imageworks (как в glTF и MaterialX) [V:DQeP363Xmn4 42:49]. Экспортёр
5.2.40 пишет `sheenColorFactor = Sheen Tint` и не умножает на вес [E §6.1]. **Обход проверен**: Sheen Weight 1 и Sheen Tint =
вес × цвет. D2/03: ткань #6B2D5C, желаемый вес 0,5 — с обходом ΔE three к Cycles 2,22 (к EEVEE 2,73); «как есть» (вес 0,5,
Tint белый) — 3,82 / 5,08, блеск в three сильнее на 3–5 L*. В самом Blender вес 1 × Tint 0,5 ≈ вес 0,5 × Tint 1
(L* 21,5 против 20,9 в EEVEE) [проверено]. Для рендера — узел Sheen BSDF (MICROFIBER) поверх (W3 §1).

### 3.4. Анизотропия (шлифованный металл)

Anisotropic и Anisotropic Rotation → `KHR_materials_anisotropy` (strength, rotation × 2π); направление в glTF — вдоль
касательной UV [E §6.1]. В Blender касательную из UV дают нода Tangent (`direction_type = "UV_MAP"`) → вход Tangent
Principled. Проверка D2/03 (сфера, anisotropic 0,75, roughness 0,35, металл #3E7BD6): ΔE three к EEVEE 11,8, к Cycles 16,1,
three темнее на 15–19 L* и блик другой формы [проверено]. Правило: для hero в вебе анизотропию не полагать на
расширение — запечь вид в карту нормалей со «штрихами» или выбрать изотропный сатин (roughness 0,3–0,4)
[не проверено: запечённая альтернатива]. Анизотропия действует и на блик диэлектрика («шлифованный пластик»)
[V:DQeP363Xmn4 35:27].

### 3.5. Иридесценция, голография

Thin Film Thickness (нм) + Thin Film IOR + группа Iridescence Factor → `KHR_materials_iridescence` (без группы не пишется)
[E §6.1]. D2/03 (тёмный металл + плёнка 450 нм): ΔE 4,5 (EEVEE) / 7,9 (Cycles), p95 ≈ 24 — радужная кромка в three
иначе окрашена [проверено]. Для сайта «голография» — шейдер на странице (F2) или текстура-градиент по френелю,
запечённая в base color; в предрендере — плёнка в Cycles.

### 3.6. Неон и светящееся

Emission Color + Emission Strength > 1 → `emissiveFactor` + `KHR_materials_emissive_strength` → `emissiveIntensity`: D2/03 —
ΔE 0,19–0,24 (ярко-розовый #FF2E88, сила 6, вид Neutral) [проверено]. Материал сам не освещает соседей и не
светится ореолом: ореол — bloom на странице (F2) или нода Glare в предрендере (`04-outputs-for-web.md` §5). Одна нода
Emission вместо Principled — не unlit (E §6.3).

### 3.7. Тун-заливка, стилизация

Shader to RGB + Color Ramp — только EEVEE и не экспортируется (E §5.8). Для веба: (а) unlit с запечённой светотенью
(`../08-export-gltf/02 §6.1`, ΔE 0,73 к Cycles); (б) замена на `MeshToonMaterial` с ступенчатой `gradientMap` по имени
материала в JS [не проверено]; (в) контур — inverted hull (Solidify, отрицательная толщина, flip normals) → замена на
`MeshBasicMaterial` (A `05 §1`). Для предрендера — Shader to RGB → Color Ramp (Constant, 3–4 ступени) [практика].

## 4. Текстуры: наборы, масштаб, цветовые пространства

### 4.1. Где брать без ключа

| библиотека | лицензия | доступ | что знать |
|---|---|---|---|
| Poly Haven | CC0 | `https://api.polyhaven.com/assets?t=textures`, `/info/<id>`, `/files/<id>` | у текстуры `dimensions` [ширина, высота] мм; HDRI — `evs_cap`, `whitebalance` (К) |
| ambientCG | CC0 | загрузка ZIP по ID | [не проверено здесь — каталог и API у G] |

Каталог, лицензии и доводка ассетов — агент G (`../10-ai-3d-generation-assets/`). Набор PBR одного источника согласован
лучше разрозненных карт [V:Z8AAX-ENWvQ 13:41].

### 4.2. Масштаб в метрах и пространства карт

- Цвет (albedo, base color, emission) — `sRGB`; данные (roughness, metallic, normal, AO, ORM, height) — `Non-Color`
  [V:qt1GidFwVt0 10:42–11:00] [проверено: E/12 — Non-Color на цвете ΔE 15,9, sRGB на нормали ΔE 7,3].
- Масштаб: при развёртке «1 единица UV = 1 м» (кубическая/по площади) Mapping Scale = 1000 / dimensions_mm; у Poly Haven
  Rubberized Track `dimensions` [2000, 2000] → Scale 0,5 [документация: Poly Haven API]. Mapping POINT уходит в
  `KHR_texture_transform` (E §5.3).
- Плотность текселей 256–512 px/м для крупных поверхностей, 512–1024 px/м для hero (E `02 §2.3`, функция `texel_density`).
- Normal Map — только Tangent; карты нормалей glTF — соглашение OpenGL (DirectX-карты переворачивать по зелёному) (W4 → F1).

```python
# Blender 5.2.2 — [проверено] набор PBR-карт с реальным масштабом (Poly Haven dimensions)
import bpy, os, tempfile

def texture_set_material(name, maps, dimensions_mm=(2000, 2000)):
    """maps: {"color": path, "rough": path, "normal": path}; масштаб — из размера образца в мм (UV: 1 ед. = 1 м)."""
    mat = bpy.data.materials.new(name); nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.vector_type = "POINT"
    mp.inputs["Scale"].default_value = (1000.0 / dimensions_mm[0], 1000.0 / dimensions_mm[1], 1.0)   # → KHR_texture_transform
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    def tex(path, colorspace):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = colorspace                 # цвет — sRGB, данные — Non-Color
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    nt.links.new(tex(maps["color"], "sRGB").outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex(maps["rough"], "Non-Color").outputs["Color"], bsdf.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(maps["normal"], "Non-Color").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

d = tempfile.mkdtemp(); paths = {}
for k, px in (("color", (0.6, 0.3, 0.2, 1)), ("rough", (0.7, 0.7, 0.7, 1)), ("normal", (0.5, 0.5, 1.0, 1))):
    im = bpy.data.images.new(k, 8, 8); im.pixels.foreach_set(list(px) * 64)
    im.filepath_raw = paths.setdefault(k, os.path.join(d, k + ".png")); im.file_format = "PNG"; im.save()
m = texture_set_material("rubber_track", paths, (2000, 2000))
print(m.name, [n.bl_idname for n in m.node_tree.nodes])
```

## 5. Low-poly: палитра-текстура и цвет вершин

| способ | вес | вызовы | в glTF | когда |
|---|---|---|---|---|
| палитра-текстура 4–16 px, Closest | +0,1–1 КБ | 1 материал на сцену | `baseColorTexture`, сэмплер NEAREST | стилизованные сцены, AR (Scene Viewer не понимает цвет вершин — A `05 §3.2`) |
| цвет вершин (Color Attribute → Base Color) | 12 байт на вершину | 1 материал | `COLOR_0` (`export_all_vertex_colors=False`) | плавные переходы, запечённый AO (E `02 §5.2`) |
| материал на цвет | 0 | вызов на материал | факторы | ≤ 3–5 цветов |

Палитра (приём Bruno Simon, E `02 §6.5`) проверена в D2/03: икосфера, 4 цвета по наклону граней, ΔE three к EEVEE 2,25, к
Cycles 3,99 [проверено]. Ловушка 5.2.2: `image.colorspace_settings.name = …` после `image.pixels.foreach_set` у
сгенерированной картинки сбрасывает буфер — палитра чёрная и в рендере, и в GLB [проверено]. Палитра-текстура и
2–3 материала на сцену — меньше вызовов отрисовки [V:H1oNuKChsdU 23:59] (W4).

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/D2/99-doc-snippets; приём — D2/03] палитра-текстура для low-poly
import sys, bpy, os, tempfile
sys.path.insert(0, "../../scripts/3d")
import bpyx

def palette_material(name, hexes, path):
    img = bpy.data.images.new(name + "_px", len(hexes), 1, alpha=False)
    img.colorspace_settings.name = "sRGB"                     # ДО пикселей: иначе буфер сбросится (чёрная палитра)
    px = []
    for h in hexes:                                           # в sRGB-картинку — значения hex как есть (0..1)
        px += [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1.0]
    img.pixels.foreach_set(px); img.filepath_raw = path; img.file_format = "PNG"; img.save()
    mat = bpy.data.materials.new(name); nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"   # → sampler NEAREST
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"); bsdf.inputs["Roughness"].default_value = 0.8
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def paint_faces(ob, cell_of_face, n_cells):
    """cell_of_face(poly) → индекс цвета; UV всех углов грани — в центр клетки палитры."""
    uv = ob.data.uv_layers.active.data
    for poly in ob.data.polygons:
        c = cell_of_face(poly)
        for li in poly.loop_indices:
            uv[li].uv = ((c + 0.5) / n_cells, 0.5)

ob = bpyx.primitive("icosphere", "Tree", radius=0.4, subdivisions=1, smooth=False)
pal = ["#2F6B3F", "#4E9A5B", "#8A5A3B", "#E9E4DA"]
bpyx.assign_material(ob, palette_material("palette", pal, os.path.join(tempfile.mkdtemp(), "pal.png")))
paint_faces(ob, lambda p: 3 if p.normal.z > 0.75 else (1 if p.normal.z > 0.1 else (0 if p.normal.z > -0.5 else 2)), len(pal))
print(bpy.data.images["palette_px"].pixels[:4])               # (0.184, 0.42, 0.247, 1.0) = #2F6B3F
```

## 6. Шейдерные графы, которые пишет агент

- Держать граф ≤ 20 нод: у моделей валидность шейдерных графов резко падает после ≈ 22 нод; план построения словами → код
  даёт 100 % исполнимости против 30 % провалов «напрямую» (C2 `../04-ai-agents-mcp/03`: VLMaterial, MaterialApprentice,
  MultiMat) [исследование].
- Ноды — по `type`/`bl_idname`, сокеты — по имени после режима, `link.is_valid` (B `../03-bpy-api/02 §2`).
- Для веба граф почти всегда 1–6 нод (Principled + картинки + группа); сложный граф — сигнал «это для рендера, веб — запечь».

## Частые ошибки

1. `bsdf.inputs["Specular"]`, `["Transmission"]`, `["Clearcoat"]`, `["Sheen"]`, `["Emission"]` → KeyError в 5.2 (имена 4.0+) (B, M1.2).
2. Sheen Weight 0,3 «как в Blender» → в three блеск как при весе 1 (+3…5 L*) — обход §3.3 [проверено].
3. Стекло через Alpha < 1 → в three `transparent`, сортировка ломается; стекло — transmission (E §5.5).
4. Стекло на прозрачном canvas → серый диск в three; нужен фон в сцене [проверено].
5. Анизотропия «как в Blender» для hero → в three тёмный металл с другим бликом (ΔE 12–16) [проверено].
6. Coat Roughness оставлен 0,03 → в three зеркальный лак (не экспортируется) [проверено].
7. Цвет металла подобран «на глаз» тёмным (хром как #777777) → металл без блеска; брать F0 из §2.2.
8. Золото (1,059; …) в Base Color → в glTF обрезается до 1 (E: ΔE 5,2).
9. Процедурная «вариативность» roughness (Noise → Map Range) в веб-ассете → в three roughness 1 (E §5.8); запекать.
10. Карта roughness с sRGB, альбедо с Non-Color → Blender и веб расходятся (E §5.4, M4.3).
11. `colorspace_settings` после записи пикселей → чёрная картинка [проверено].
12. Одна нода Emission для «плоского» логотипа → PBR с отражениями, не unlit (E §6.3); неон — через Principled Emission.

## Чек-лист

- [ ] Материал из разрешённого набора нод (или запечён)?
- [ ] Цвета — из hex через линейный; металлы — по таблице F0; золото ≤ 1?
- [ ] Specular IOR Level 0,5 у диэлектриков, вид задан roughness?
- [ ] Coat Roughness ≠ 0,03, если лак не зеркальный?
- [ ] Sheen: вес 1, Tint = вес × цвет?
- [ ] Стекло: transmission + Thickness + Volume Absorption, OPAQUE; в three есть фон в canvas?
- [ ] Нет анизотропии/иридесценции в hero веб-ассете (или вид запечён)?
- [ ] Текстуры: цвет sRGB, данные Non-Color; масштаб от реального размера образца?
- [ ] Low-poly: палитра-текстура Closest или цвет вершин с `export_all_vertex_colors=False`?
- [ ] `gltf_diff.py --engine cycles --tone neutral` по материалам ≤ 3,5 ΔE?

## Открытые вопросы и противоречия

1. **Анизотропия** (ΔE 12–16): причина — соглашение касательной (UV-производные в three против ноды Tangent) или IBL-приближение
   анизотропии в three (изогнутая нормаль) — не выяснено; запечённая альтернатива не проверена.
2. **Стекло с фоном в canvas** — закрыто K/05: работает (фон и предметы в сцене; `../12-recipes/09-glass-product.md`); вид на прозрачном canvas зависит от фона и тонмаппинга.
3. **Иридесценция** расходится и с EEVEE, и с Cycles (p95 ≈ 24): Blender и three считают плёнку по-разному (E: «оттенок отличается»).
4. **Specular 0,5 всегда** (Price) против «ниже для пористых» (зрители) и «нефизичный контрол» (Stockner) — `[спорно]` (W3 §4).
5. **ambientCG** — API и лицензия в этой сессии не проверялись (за G).
6. Матовый пластик, резина, матовое стекло, сатин — значения из практики, отдельного замера нет.

## Источники

- [S1] Anton Palmqvist и соавторы. Physically Based — база значений материалов. `https://api.physicallybased.info/materials`
  (86 материалов, линейные base color, IOR; ответ сохранён в `99-raw/experiments/D2/03-materials/physicallybased_materials.json`) — измеренные/справочные данные, открытая база.
- [S2] Poly Haven. Public API `https://api.polyhaven.com` (`/assets`, `/info/<id>`) — CC0, без ключа; поля `dimensions`,
  `evs_cap`, `whitebalance` проверены запросом 23.09.2026.
- [S3] Khronos. KHR_materials_sheen, clearcoat, transmission, volume, anisotropy, iridescence, emissive_strength
  (кэш `99-raw/cache/khronos/`) — через контракт E.
- [S4] [V:DQeP363Xmn4] L. Stockner, «The new Principled BSDF model in Cycles», BCon 2022 — дайджест W3.
- [S5] [V:Z8AAX-ENWvQ] A. Price, «The Secrets of Photorealism», BCon 2022 — дайджест W3.
- [S6] [V:Sv2wqwsvx-8] V. Duha, «Rendering Glass», BCon 2019 — дайджест W3.
- [S7] [V:MFzmj1TUEKk], [V:qt1GidFwVt0], [V:H1oNuKChsdU] — через отчёты W3/W4 (`99-raw/reports/wave2-W3-report.md`, `wave2-W4-report.md`).
- [S8] Агент E: `../08-export-gltf/01-export-contract.md` §2.2, §5–6; `02-baking.md` §4–6 — внутренний, проверенный.
- [S9] Агенты B и C2: `../03-bpy-api/02-nodes-from-python.md` §3; `../04-ai-agents-mcp/03-research-llm-3d.md` (графы ≤ 22 нод).

Эксперименты: `99-raw/experiments/D2/03-materials` (библиотека, gltf_diff EEVEE/Cycles, по объектам), `D2/01-brand-color`.
