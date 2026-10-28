# 12 · model-viewer + AR: «посмотреть у себя» — AR-GLB по лимитам Scene Viewer и USDZ из Blender

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS (`wm.usd_export`, `pxr`), glTF-IO 5.2.40, @google/model-viewer 4.3.1, Chromium ·
сквозной прогон: [проверено] · страница: [проверено] · пример:
`examples/12-model-viewer-ar/`

## Выжимка рецепта

1. Витрина «покрутить + в AR» без своего three — **model-viewer 4.3.1**: `src` (GLB), `ios-src` (USDZ), `poster`, `ar-modes="webxr
   scene-viewer quick-look"`, `tone-mapping="neutral"` (пара к Blender Neutral) [документация: F1 `09/06 §2.1`; страница — этот прогон].
2. **AR-GLB — отдельный несжатый файл**: Scene Viewer (Android) заново скачивает `src` и знает только `KHR_materials_unlit` и
   `KHR_texture_transform` — без Meshopt/Draco/KTX2/квантования; ≤ 100 тыс. треуг., ≤ 10 материалов, текстуры ≤ 2048² PNG/JPEG,
   без морфов и цветов вершин, ≤ 1 анимации, ≤ 10 МБ [документация: F1 `09/06 §2.2`].
3. Лимиты проверять кодом по JSON GLB (`ar_lint`) до публикации — валидатор Khronos их не знает [проверено: этот прогон].
4. **USDZ из Blender 5.2.2** — `wm.usd_export` в фоне, Y-up, метры, UsdPreviewSurface, `usdz_downscale_size` 2048; проверка пакета —
   `pxr` из Blender (upAxis, metersPerUnit, габарит) [проверено: F1/06, этот прогон]; вид в Quick Look без Mac/iPhone
   [не проверено].
5. Если на странице нужен лёгкий сжатый GLB (hero), AR-файл — отдельный, а витрина — свой three (рецепт 01) + кнопка AR
   (intent/`rel="ar"`) [вывод F1 из документации].

## 1. Бриф-пример и границы

«Карточка товара: кейс наушников можно покрутить и „поставить на стол“ в AR; без своей разработки WebGL».

| годится | не годится → куда |
|---|---|
| e-commerce, «покрутить» + AR-кнопка, нет инженера WebGL | hero с жёстким бюджетом TBT/веса → свой three (рецепт 01): model-viewer тянет свой three |
| реальный размер предмета важен (AR 1:1, `ar-scale="fixed"`) | сцена/мир, частицы, прокрутка → three (рецепты 05, 06) |
| одна анимация (открытие крышки) | несколько клипов в AR → Scene Viewer играет только первый |

## 2. Паспорт

Ассет — `case_raw.glb` рецепта 01 (пресет `static_hero` без постобработки: 53,4 КБ, 1 976 треуг., 2 материала); постер — `poster.webp`
рецепта 01; реальный размер 60,6 × 45,2 × 21,7 мм (AR показывает 1:1).

## 3. Код Blender: AR-GLB по лимитам + USDZ + проверка пакета

```python
# Blender 5.2.2 — [проверено] рецепт 12: AR-GLB (лимиты Scene Viewer) + USDZ (Quick Look)
import sys, os, json, shutil, struct, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
SLUG = "12-model-viewer-ar"
SRC = f"{rk.ROOT}/12-recipes/examples/01-hero-product"
OUT = rk.out_dir(SLUG)
AR_EXT_OK = {"KHR_materials_unlit", "KHR_texture_transform"}             # что знает Scene Viewer (F1 09/06 §2.2)


def ar_lint(path, max_tris=100_000, max_mats=10, max_tex=2048, max_mb=10):
    """Лимиты Scene Viewer по JSON GLB: расширения, треугольники, материалы, морфы, цвета вершин, анимации, размер."""
    data = open(path, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
    acc, fails = j.get("accessors", []), []
    tris = sum(acc[p["indices"]]["count"] // 3 for m in j.get("meshes", []) for p in m["primitives"] if "indices" in p)
    req = set(j.get("extensionsRequired", [])) - AR_EXT_OK                  # обязательное неизвестное → файл не откроется
    if req: fails.append(f"обязательные расширения вне Scene Viewer: {sorted(req)}")
    warn = sorted(set(j.get("extensionsUsed", [])) - AR_EXT_OK - req)       # необязательное → в AR молча без эффекта
    if tris > max_tris: fails.append(f"треугольников {tris} > {max_tris}")
    if len(j.get("materials", [])) > max_mats: fails.append("материалов > 10")
    if any("targets" in p for m in j.get("meshes", []) for p in m["primitives"]): fails.append("морфы запрещены")
    if any("COLOR_0" in p["attributes"] for m in j.get("meshes", []) for p in m["primitives"]): fails.append("цвета вершин запрещены")
    if len(j.get("animations", [])) > 1: fails.append("анимаций > 1")
    if len(data) > max_mb * 2**20: fails.append(f"размер {len(data) / 2**20:.1f} МБ > {max_mb}")
    return {"ok": not fails, "fails": fails, "ignored_in_ar": warn, "tris": tris, "materials": len(j.get("materials", [])),
            "extensionsUsed": j.get("extensionsUsed", []), "kb": round(len(data) / 1024, 1)}


def export_usdz(path, **overrides):                                       # F1 09/06 §2.4 [проверено]
    kw = dict(selected_objects_only=False, export_animation=False, export_materials=True, generate_preview_surface=True,
              export_textures_mode="NEW", usdz_downscale_size="2048", export_subdivision="TESSELLATE", evaluation_mode="RENDER",
              convert_orientation=True, export_global_forward_selection="NEGATIVE_Z", export_global_up_selection="Y",
              convert_scene_units="METERS", export_lights=False, export_cameras=False)
    kw.update(overrides)
    valid = {p.identifier for p in bpy.ops.wm.usd_export.get_rna_type().properties}
    bad = [k for k in kw if k not in valid]
    if bad:
        raise KeyError(f"нет параметров {bad} в wm.usd_export этой версии")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return bpy.ops.wm.usd_export(filepath=os.path.abspath(path), **kw)


shutil.copy(f"{SRC}/case_raw.glb", f"{OUT}/case_ar.glb")                  # AR-файл = экспорт static_hero БЕЗ сжатия
shutil.copy(f"{SRC}/poster.webp", f"{OUT}/poster.webp")
lint = ar_lint(f"{OUT}/case_ar.glb"); print("AR_LINT", lint); assert lint["ok"], lint
lint_web = ar_lint(f"{SRC}/case.glb")                                     # сжатый веб-GLB Scene Viewer не годится
assert not lint_web["ok"] and "EXT_meshopt_compression" in str(lint_web["fails"]), lint_web
rk.reset()
assert bpy.ops.import_scene.gltf(filepath=f"{OUT}/case_ar.glb") == {"FINISHED"}
assert export_usdz(f"{OUT}/case.usdz") == {"FINISHED"}
from pxr import Usd, UsdGeom                                                 # проверка пакета тем же Blender
st = Usd.Stage.Open(f"{OUT}/case.usdz")
bb = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"]).ComputeWorldBound(st.GetPseudoRoot()).ComputeAlignedRange()
size = [round(v, 4) for v in (bb.GetMax() - bb.GetMin())]
usd = {"upAxis": UsdGeom.GetStageUpAxis(st), "metersPerUnit": UsdGeom.GetStageMetersPerUnit(st), "size_m": size,
       "kb": round(os.path.getsize(f"{OUT}/case.usdz") / 1024, 1),
       "shaders": sorted({p.GetAttribute("info:id").Get() for p in st.Traverse() if p.GetTypeName() == "Shader"} - {None})}
print("USDZ", usd)
assert usd["upAxis"] == "Y" and abs(usd["metersPerUnit"] - 1) < 1e-6 and abs(size[1] - 0.0452) < 0.002, usd   # высота кейса — ось Y
rk.save(SLUG, ar_lint=lint, web_glb_lint=lint_web, usdz=usd)
```

## 4. Страница

`examples/12-model-viewer-ar/index.html` — разметка F1 `09/06 §2.1` с ассетами рецепта; model-viewer 4.3.1 с jsDelivr (npm-пакет;
F1 брал `ajax.googleapis.com` — оба адреса отдают 4.3.1):

```html
<!-- model-viewer 4.3.1 — [проверено: загрузка и рендер в Chromium; AR на устройствах не проверен] -->
<script type="module" src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.3.1/dist/model-viewer.min.js"></script>
<style> model-viewer { display: block; width: 100%; height: auto; aspect-ratio: 1; } </style>  <!-- :host задаёт 300×150 -->
<model-viewer src="case_ar.glb" ios-src="case.usdz" poster="poster.webp"
  alt="Белый глянцевый кейс для беспроводных наушников с зелёным индикатором"
  loading="eager" reveal="auto" camera-controls touch-action="pan-y" tone-mapping="neutral" shadow-intensity="0.6"
  ar ar-modes="webxr scene-viewer quick-look" ar-scale="fixed">
  <button slot="ar-button">Посмотреть у себя на столе</button>
</model-viewer>
```

Кнопка AR — словами (иконки AR непонятны, NN/g через A `01/02 §6.2`); `activateAR()` — только из жеста; `ar-placement="wall"` для
настенных предметов (F1).

## 5. Числа прогона

Blender 0,3 с (копия AR-GLB, `ar_lint`, импорт, `wm.usd_export` 65 мс, проверка `pxr`); страница — `web_view.py --page`. Итераций — 1:
`aspect-ratio` у `<model-viewer>` не действует без `height: auto` (стиль `:host` задаёт 300 × 150) — первый скриншот показал полоску
высотой 150 px.

| величина | значение |
|---|---|
| AR-GLB (`case_ar.glb` = экспорт `static_hero` без сжатия) | 53,4 КБ, 1 976 треуг., 2 материала — `ar_lint` ok; `clearcoat` и `emissive_strength` — не обязательны, в AR молча без эффекта |
| веб-GLB рецепта 01 (`case.glb`, meshopt) | `ar_lint` **провал**: обязательное `EXT_meshopt_compression` (и квантование) — Scene Viewer файл не откроет |
| USDZ | **98,9 КБ**, `upAxis = Y`, `metersPerUnit = 1`, габарит 60,6 × 45,2 × 22,3 мм (высота — ось Y), шейдер `UsdPreviewSurface` |
| страница model-viewer | 346 КБ (JS 282 — свой three внутри, модель 53, постер 8), 0 ошибок; событие `load` пришло, `canActivateAR` = false на десктопе |

Замечание к зонду (для J): `web_view.py --page` показал **0 вызовов** у model-viewer — перехват WebGL не видит его контекст (рендер
внутри shadow DOM); ноль в отчёте здесь не означает «0 вызовов». Время загрузки страницы в двух прогонах — 0,7 и 16,9 с (CDN через
нестабильную сеть) — для замеров раздавать model-viewer со своего сервера.

## 6. Ворота

`ar_lint(AR-GLB).ok` и `not ar_lint(веб-GLB).ok` (не перепутать файлы), USDZ: Y-up, метры, высота ±2 мм — `assert` в коде; страница:
событие `load`, 0 ошибок консоли; вид в Scene Viewer — `arvr.google.com/scene-viewer-preview`, в Quick Look — Mac/iPhone [не проверено].

## 7. Варианты

1. **Клип в AR** (открытие крышки) — AR-GLB с одной анимацией (пресет `anim_trs` без сжатия, рецепт 05); в USDZ — `export_animation=True`
   [не проверено в Quick Look].
2. **Сжатая витрина + AR** — свой three (рецепт 01, 12,3 КБ) + кнопка: Android — intent `scene-viewer/1.2` с `file=<AR-GLB>`,
   iOS — `<a rel="ar" href="case.usdz"><img …></a>` (F1 `09/06 §2.3`).
3. **Текстурный товар** — текстуры AR-GLB JPEG/PNG ≤ 2048²; KTX2/WebP — только в веб-версии.
4. **USDZ без Blender** — three `USDZExporter` из того же GLB (как делает model-viewer, `maxTextureSize` 1024) (F1).

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| один сжатый GLB и для страницы, и для AR | Scene Viewer не открывает (Meshopt/Draco/KTX2 обязательны) | отдельный AR-GLB без сжатия; `ar_lint` |
| цвета вершин / морфы в AR-GLB | ошибка Scene Viewer | материал + текстура; без shape keys |
| `visible_objects_only`, `export_textures` (по памяти) в `wm.usd_export` | TypeError в 5.2.2 | параметры 5.2.2 (F1 `09/06 §2.4`, проверка по RNA в `export_usdz`) |
| USDZ Z-up | предмет лежит в Quick Look | `convert_orientation=True`, `NEGATIVE_Z` / `Y` |
| `<model-viewer>` с `aspect-ratio` без `height: auto` | полоска 150 px | `display: block; height: auto` |
| кнопка AR — иконка | не понимают | текст «Посмотреть у себя …» |

## Ссылки

F1 `../09-web-runtime/06-deliverables-ar-ktx2-webgpu.md §2`, `../99-raw/experiments/F1/06-doc-snippets`; E `../08-export-gltf/04-validation-pitfalls-presets.md §7`;
A `../01-web-3d-landscape/02-when-3d-budgets-loading.md §6.2`; model-viewer — `modelviewer.dev/docs` (через F1).
