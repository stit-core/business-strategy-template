# Гауссовы сплаты и сканы как поставка 3D на сайт

Волна 2 · агент G · 23.09.2026 · режим экономии заказчика · источников: 4 первичных (README `KHR_gaussian_splatting` в
реестре Khronos, спецификация SOG PlayCanvas, исходники three r186 `GaussianSplat`/`GLTFGaussianSplatLoaderExtension`, npm) +
замеры живых сайтов агента A (`01-web-3d-landscape/04`) · эксперименты: интроспекция Blender 5.2.2 (`bpy_probe.py search splat`),
листинг three@0.186.0 (jsDelivr), сканы Poly Haven `G/02`–`G/03`, `G/04-doc-snippets` · версии: Blender 5.2.2 LTS, three r186,
@sparkjsdev/spark 2.2.0, @playcanvas/splat-transform 3.6.2, @mkkellogg/gaussian-splats-3d 0.4.7.

Сплат (3D Gaussian Splatting, 3DGS) — сцена как облако эллипсоидов с цветом (сферические гармоники), прозрачностью, масштабом
и поворотом, обученное по фото или видео (или сгенерированное нейросетью). Даёт «как на фото» с мягкими краями и отражениями,
но не меш: нет UV, материалов, освещения на странице, коллизий. Скан-меш (фотограмметрия) — обычная модель, доводится как
выход генератора (`02-cleanup-to-web.md`). Код загрузки на странице — зона агентов F1/F2 (`../09-web-runtime/`); здесь —
форматы, веса, выбор и границы.

## Выжимка для агента

1. **Blender 5.2.2 сплаты не делает и не читает**: интроспекция по «splat» — 0 типов, операторов и свойств; сплаты приходят со
   съёмки/обучения или от нейросети, Blender — только для сопутствующих мешей и постера. → §5 `[проверено: bpy_probe]`
2. **Стандарт glTF есть**: `KHR_gaussian_splatting` — «Complete, Ratified by the Khronos Group» (реестр Khronos, 09.2026):
   примитив POINTS, `kernel: "ellipse"` обязателен, атрибуты `KHR_gaussian_splatting:SCALE/ROTATION/OPACITY/SH_DEGREE_n_COEF_m`. → §1.2 `[документация]`
3. **three r186: сплаты только в `WebGPURenderer`** (откат `forceWebGL` поддержан, `WebGLRenderer` — нет): `GaussianSplat`,
   загрузчики PLY, SPLAT, KSPLAT, SPZ и `GLTFGaussianSplatLoaderExtension`, сортировка на GPU. → §2 `[проверено: исходник r186]`
4. **Для `WebGLRenderer` и обычного стека pmndrs — Spark** (`@sparkjsdev/spark` 2.2.0, MIT, World Labs, 11.09.2026); 744 КБ br
   вместе с three (A). `@mkkellogg/gaussian-splats-3d` заморожен с 01.2025. → §2 `[документация npm; проверено A/03]`
5. **Сырой PLY не отдавать**: 62 float на сплат при SH степени 3 = **248 байт** (1 млн сплатов ≈ 248 МБ); функция
   `splat_ply_stats()` читает это из заголовка. → §1.1 `[проверено]`
6. **Для сайта — SOG или SPZ**: SOG «~15–20× smaller» PLY (PlayCanvas; WebP без потерь + meta.json, ZIP `.sog`); SPZ у World
   Labs — ≈ 1,4 МБ на 100 тыс. сплатов (≈ 14 байт на сплат, A). → §1.1 `[документация; проверено A: замер сайта]`
7. **Бюджет героя ≤ 3 МБ ⇒ ≤ ~200 тыс. сплатов** в SOG/SPZ (≈ 14–16 байт на сплат); сайты: Oryzo — `.sog` 3 МБ ×2, World Labs —
   `.spz` 1,4 МБ ×12, 1 вызов отрисовки. → §3 `[расчёт по документации и замеру A]`
8. **Не жми SOG картинками с потерями**: спецификация требует lossless WebP — «lossy compression will corrupt values». → §1.1 `[документация]`
9. **Постер обязателен**: сплат не LCP-элемент и тяжёл для слабых телефонов; постер того же ракурса + загрузка после LCP
   (паттерн A `02 §4`). → §3 `[проверено A/04, A/07]`
10. **Когда сплат уместен**: место или объект «как на фото» (интерьер, товар ручной работы, скульптура), вращение/пролёт камеры;
    когда нет: брендовый продукт со строгими формами, смена цвета/материала в JS, интерактив со светом, много сцен на странице
    (Shopify отказались: 3–5 МБ × 10–20 сцен). → §3 `[практика A]`
11. **Скан-меш вместо сплата**, если нужен свет страницы, смена материала или AR: доводка как у генератора — Decimate до
    бюджета + перепечка нормали: скан-валун 90 тыс. → 12 тыс. треуг., **0,28 МБ телефон**. → §4 `[проверено]`
12. **Сплаты нейросетями** (World Labs Marble и др.) отдают те же форматы (SPZ) — к ним те же правила веса и постера;
    лицензии результатов — по условиям сервиса. → §6 `[проверено A: worldlabs.ai .spz; не проверено: условия]`

## 1. Форматы

### 1.1. Таблица

| Формат | Что внутри | Байт на сплат | Кто читает в вебе | Статус |
|---|---|---|---|---|
| PLY (формат обучения 3DGS) | `x y z`, `nx ny nz`, `f_dc_0..2`, `f_rest_0..44` (SH степени 3), `opacity`, `scale_0..2`, `rot_0..3` — float32 | **248** (SH 3), 68 (SH 0: 17 float с нулевыми нормалями) | three r186 `GaussianSplatPLYLoader`, Spark, PlayCanvas, Babylon | исходник, не для сайта |
| .splat (формат antimatter15) | позиция и масштаб float32, цвет RGBA и поворот uint8 | 32 | three `SPLATLoader`, Spark, Babylon | без SH (цвет без зависимости от ракурса) |
| KSPLAT | формат GaussianSplats3D, уровни сжатия | — | three `KSPLATLoader`, GaussianSplats3D | библиотека заморожена |
| SPZ | формат Niantic (открыт), квантование + gzip | ≈ 14 (World Labs: 1,4 МБ / 100 тыс.) | three `SPZLoader`, Spark, Babylon | используется World Labs |
| SOG (PlayCanvas) | `meta.json` + lossless WebP: `means_l/means_u` (позиция 16 бит), `scales` (кодбук), `quats`, `sh0` (цвет + прозрачность), `shN_centroids/labels` (палитра SH); ZIP `.sog` | ≈ 12–17 («~15–20× smaller» PLY) | PlayCanvas, SuperSplat (потоково, LOD), Babylon | вендорный, открытая спецификация |
| glTF `KHR_gaussian_splatting` | примитив POINTS + атрибуты `KHR_gaussian_splatting:*` | как у данных (float/нормированные целые) | three r186 `GLTFGaussianSplatLoaderExtension` (WebGPU) | **ратифицирован Khronos** |

[документация: SOG, KHR_gaussian_splatting; проверено: исходник three r186; проверено A: замер worldlabs.ai, oryzo.ai].
Байты PLY — расчёт по составу полей, проверен функцией §1.3 на синтетическом файле [проверено]; .splat — по описанию формата
`[практика; не проверено запуском]`.

### 1.2. `KHR_gaussian_splatting` (реестр Khronos, ветка main, 09.2026)

- Статус: «Complete, Ratified by the Khronos Group»; «Written against the glTF 2.0 spec»; соавторы — Cesium, Niantic Spatial и
  др. [документация].
- Свойства: `kernel` (обязателен; определён один — `"ellipse"`), `projection` (по умолчанию перспективная), `sortingMethod`,
  `colorSpace`; атрибуты примитива `KHR_gaussian_splatting:SCALE`, `:ROTATION`, `:OPACITY`, `:SH_DEGREE_0_COEF_0` и старшие
  степени; допускаются нормированные целые типы (квантование) [документация].
- Сжатие: «Other extensions that depend on this extension such as 3D Gaussian splatting compression extensions MAY require…» —
  отдельного KHR-расширения сжатия в папке Khronos на 23.09.2026 нет (GitHub API) [документация].
- three r186 проверяет ровно это: kernel ≠ `ellipse` → ошибка, нет `colorSpace` → ошибка, иная проекция/сортировка → предупреждение
  «Results may be incorrect» [проверено: исходник `GLTFGaussianSplatLoaderExtension.js`].

### 1.3. Оценка файла по заголовку PLY

```python
# Python 3.10+ (в Blender 5.2.2 и без него) — [проверено] число сплатов, SH, вес
def splat_ply_stats(path, sog_ratio=(15, 20)):
    """Читает только заголовок PLY 3DGS: число сплатов, поля, степень SH, байт на сплат, оценка веса SOG (÷15…20)."""
    size = {"char": 1, "uchar": 1, "short": 2, "ushort": 2, "int": 4, "uint": 4, "float": 4, "double": 8}
    with open(path, "rb") as f:
        head = b""
        while not head.endswith(b"end_header\n"):
            line = f.readline()
            if not line:
                raise ValueError("нет end_header — не PLY")
            head += line
    n, props, fmt = 0, [], ""
    for ln in head.decode("ascii", "replace").splitlines():
        parts = ln.split()
        if parts[:1] == ["format"]:
            fmt = parts[1]
        elif parts[:2] == ["element", "vertex"]:
            n = int(parts[2])
        elif parts[:1] == ["property"] and n and len(parts) == 3:
            props.append((parts[2], size.get(parts[1], 4)))
    rest = sum(1 for p, _ in props if p.startswith("f_rest_"))
    sh = {0: 0, 9: 1, 24: 2, 45: 3}.get(rest, -1)          # коэффициентов на 3 канала: (deg+1)^2-1
    bps = sum(b for _, b in props)
    return {"format": fmt, "splats": n, "properties": len(props), "sh_degree": sh, "bytes_per_splat": bps,
            "ply_mb": round(n * bps / 1e6, 2),
            "sog_mb_est": [round(n * bps / r / 1e6, 2) for r in sog_ratio[::-1]]}
```

Проверка: синтетический PLY на 1 000 сплатов с полями стандартного 3DGS — `splats 1000`, `sh_degree 3`, `bytes_per_splat 248`
[проверено]. Оценка SOG — по коэффициенту из спецификации PlayCanvas, не замер.

## 2. Веб-рендереры (23.09.2026)

| Библиотека | Версия, лицензия | Рендерер | Форматы | Замечания |
|---|---|---|---|---|
| three r186 `examples/jsm/objects/GaussianSplat.js` | 0.186.0, MIT | **только `WebGPURenderer`** (+ его откат WebGL), не `WebGLRenderer` | `GaussianSplatPLYLoader`, `SPLATLoader`, `KSPLATLoader`, `SPZLoader`, `GLTFGaussianSplatLoaderExtension` (регистрировать в GLTFLoader) | сортировка `CountingSort` на GPU; нужны `three/webgpu` и `three/tsl` в import map [проверено: исходник] |
| Spark (`@sparkjsdev/spark`) | 2.2.0, MIT, 11.09.2026 | three `WebGLRenderer` | форматы по документации Spark `[не проверено]` (World Labs отдаёт SPZ) | 744 КБ br вместе с three (A/03) [npm; проверено A] |
| PlayCanvas engine + SuperSplat | engine 2.22.3, MIT | WebGL2 / WebGPU (compute-рендер, ×2 fps на iPhone 13 Pro Max по вендору) | SOG (потоково, LOD, бюджет гауссиан на устройство), PLY | 393 КБ br движка (A/03) [документация; проверено A] |
| `@playcanvas/splat-transform` | 3.6.2, MIT, 23.09.2026 | CLI | конвертация PLY → SOG/сжатый PLY и др. | инструмент подготовки [npm] |
| Babylon.js 9 | 9.27.1, Apache-2.0 | WebGL2/WebGPU | PLY, SPLAT, SPZ, SOG | 665 КБ br с glTF (A) [документация A] |
| `@mkkellogg/gaussian-splats-3d` | 0.4.7, MIT | three WebGL | PLY, SPLAT, KSPLAT | без релизов с 25.01.2025 — не брать для нового [npm] |
| drei `<Splat>` | drei 10.7.8 | R3F | `[не проверено]` | компонент есть в drei (A `03 §3.2`) |

Код загрузки на странице (import map `three/webgpu`, регистрация расширения, постер, остановка цикла) — агенты F1/F2
(`../09-web-runtime/`); в этом файле JS не приводится.

## 3. Где сплат уместен на лендинге и сколько он стоит

| Сайт (замер A, 2026) | Что | Вес сплатов | Движок | Вызовы |
|---|---|---|---|---|
| oryzo.ai (SOTM 04.2026) | продукт «как на фото», камера на прокрутке | `.sog` ×2, 3 МБ + `splat_sorter.wasm` | three r178 (Lusion) | — |
| worldlabs.ai (Marble) | миры-сплаты в витрине | `.spz` ×12 по ≈ 1,4 МБ (100 тыс. сплатов) | three r170 + R3F | **1** |
| superspl.at | вьюер SuperSplat, потоковый SOG | 4,7 МБ за окно просмотра | PlayCanvas | — |
| playcanvas.com | герой «drag to rotate» (игрушка) | — | PlayCanvas | — |

[проверено A: `../01-web-3d-landscape/04-reference-sites-measured.md`]. Shopify (Editions, 2026) отказались от сплатов из-за
3–5 МБ на сцену × 10–20 сцен и перешли на облака точек (A `01 §6.5`, Codrops 2026-06-26) [практика].

Правила:
- **Вес**: герой ≤ 3 МБ (десктоп, E `03 §6.5`) → ≤ ~200 тыс. сплатов в SOG/SPZ; телефон — вдвое меньше и потоковая загрузка
  (SuperSplat) или постер вместо сплата [расчёт; практика].
- **Порядок загрузки**: постер-картинка того же ракурса → сплат после `load` в простое → кроссфейд (A `02 §4`); canvas не LCP
  (A/04) [проверено A].
- **Рендерер**: three-сайт на `WebGLRenderer` — Spark; новый проект на WebGPU — `GaussianSplat` three r186; сцены с потоковым
  LOD — PlayCanvas [документация].
- **Что сплат не умеет**: свет страницы и тени на нём, смену материала/цвета, коллизии, AR Quick Look/Scene Viewer (нужен меш) —
  тогда скан-меш (§4).

## 4. Скан-меш (фотограмметрия) для сайта

- Структура та же, что у выхода генератора: плотный треугольный меш + UV-атлас + запечённые карты. Поэтому конвейер — `02`:
  `asset_intake()` → Decimate COLLAPSE до бюджета (UV сохраняется) → перепечка нормали с исходника → сжатие [проверено].
- Числа на скане Poly Haven `namaqualand_boulder_05` (1,36 м): 89 618 → 11 999 треуг., ошибка P95 2,55 мм; итог 0,58 МБ
  десктоп / **0,28 МБ телефон**, текстуры в GPU 1 МБ (KTX2 512), 1 вызов [проверено]. Без упрощения — 0,68 МБ, но 90 тыс.
  треугольников (выше бюджета телефона 50 тыс.) [проверено].
- Готовые сканы без съёмки: Poly Haven (CC0; сканы природы, еды, предметов; медиана моделей 11 тыс., p90 154 тыс. полигонов) —
  `03 §2` [проверено].
- Съёмка своих предметов (Apple Object Capture → USDZ, RealityScan, Polycam, Meshroom) и их лицензии в этой сессии не
  проверялись `[не проверено]`; для сайта ориентир — сырой скан 50–500 МБ → доведённый 1–5 МБ (A `01 §16.2`, практика).

## 5. Blender и сплаты

- **Blender 5.2.2 LTS**: `bpy_probe.py search splat` — 0 типов, 0 операторов, 0 свойств; `search gaussian` — только
  `GaussianBlurStrip` (видеоредактор) и `graph.gaussian_smooth` (кривые) → нативных сплатов нет [проверено].
- По каталогу видео, нативные сплаты появились в ежедневных сборках 5.3 (ролик CGMatter `CniycUnvcX4`, каталог V) — не
  проверялось: сборки 5.3 на машине нет `[не проверено]`.
- Аддоны сплатов для Blender (импорт PLY как облака точек/инстансов с шейдером, рендер EEVEE) существуют у сообщества и
  вендоров сканирования; их совместимость с 5.2.2 и лицензии в этой сессии не проверялись `[не проверено]`.
- Роль Blender в конвейере сплата: сопутствующие меши (пол, коллайдеры, пути камеры), постер (рендер меш-версии или кадр из
  вьюера) и сцена-окружение вокруг сплата — через обычный экспорт glTF (E) [практика].

## 6. Сплаты и 3D-миры от нейросетей

- World Labs (Marble) показывает свои миры на сайте сплатами SPZ по ≈ 1,4 МБ на 100 тыс. сплатов, 1 вызов отрисовки
  [проверено A: замер worldlabs.ai]. Условия использования результатов и цены — `[не проверено]` (режим экономии).
- Генераторы мешей (Rodin, Meshy, Tripo, TRELLIS.2) выдают меш, не сплат (`01`); TRELLIS.2 работает с собственным представлением
  O-Voxel и экспортирует GLB [документация: README TRELLIS.2].
- Правила для сгенерированного сплата те же, что для снятого: формат SOG/SPZ, бюджет ≤ ~200 тыс. сплатов на героя, постер,
  лицензия результата у сервиса (как у генераторов мешей, `01 §3`).

## Частые ошибки

1. **Сплат через `WebGLRenderer` штатными классами three r186** — `GaussianSplat` «can only be used with WebGPURenderer»;
   для WebGL — Spark [проверено: исходник].
2. **Выложить PLY с обучения** — 248 байт на сплат, сотни МБ [проверено: G/04 — расчёт по заголовку].
3. **SOG, пережатый в WebP с потерями** — ломает квантованные значения (спецификация) [документация].
4. **Ожидать от сплата реакции на свет страницы** или перекраски — это «запечённая» съёмка; нужен меш (§4) [практика].
5. **Нет постера** — пустой экран до загрузки и на слабых устройствах; сплат не LCP [проверено A].
6. **Модель по памяти**: «в glTF нет стандарта для сплатов» (устарело: KHR ратифицировано), «GaussianSplats3D — основная
   библиотека» (заморожена с 01.2025), «Blender импортирует сплаты» (в 5.2.2 — нет) [проверено].

## Чек-лист

- [ ] Сплат нужен (фотореальное место/объект, камера движется), а не меш (свет, материал, AR)?
- [ ] Формат SOG или SPZ (или glTF `KHR_gaussian_splatting` для WebGPU), не PLY?
- [ ] Число сплатов и вес в бюджете (герой ≤ ~200 тыс., ≤ 3 МБ; телефон — меньше или постер)?
- [ ] Рендерер соответствует стеку (Spark для `WebGLRenderer`, `GaussianSplat` для `WebGPURenderer`, PlayCanvas для потоков)?
- [ ] Постер того же ракурса, загрузка после LCP, остановка цикла вне экрана и при reduced motion (A `02 §4–5`)?
- [ ] Лицензия съёмки или сервиса-генератора позволяет коммерческое использование?

## Открытые вопросы и противоречия

- **Сжатие сплатов в glTF**: KHR-расширения сжатия нет; SPZ/SOG остаются вне glTF — какой формат станет стандартом доставки,
  неясно (реестр Khronos, 09.2026).
- **Замеров своих нет**: конвертация PLY → SOG/SPZ (`splat-transform`), вес и FPS Spark против three `GaussianSplat` на этой
  машине не проводились (режим экономии) — числа из документации и замеров сайтов агентом A.
- **Blender 5.3 и аддоны сплатов** — не проверены; SIGGRAPH 2026 «glTF 2.1 and Beyond» и доклад Khronos о сплатах (каталог V)
  не читались.

## Источники

- [S1] Khronos. KHR_gaussian_splatting (README, ветка main). https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_gaussian_splatting — статус «Complete, Ratified», kernel, атрибуты; прочитано 23.09.2026. Первоисточник.
- [S2] PlayCanvas. The SOG Format. https://developer.playcanvas.com/user-manual/gaussian-splatting/formats/sog/ — состав, «~15–20× smaller», lossless WebP (кэш агента A). Первоисточник.
- [S3] three.js r186: `examples/jsm/objects/GaussianSplat.js`, `loaders/GLTFGaussianSplatLoaderExtension.js`, список загрузчиков (jsDelivr, three@0.186.0) — прочитаны нужные места. [проверено]
- [S4] npm registry (23.09.2026): @sparkjsdev/spark 2.2.0, @playcanvas/splat-transform 3.6.2, @mkkellogg/gaussian-splats-3d 0.4.7 — версии, даты, лицензии.
- [S5] Агент A: `../01-web-3d-landscape/04-reference-sites-measured.md` (oryzo, worldlabs, superspl.at), `01-effects-catalog.md` §16, `03-runtime-landscape.md` §5, §9 (бандлы, PlayCanvas, Babylon), `02-when-3d-budgets-loading.md` §4 (постер). [проверено A]
- [S6] Эксперименты G: `99-raw/experiments/G/02-polyhaven-api`, `03-cleanup-boulder` (скан-меш), `04-doc-snippets` (PLY-заголовок); `bpy_probe.py search splat|gaussian` в Blender 5.2.2. [проверено]
- [S7] Microsoft. TRELLIS.2 README — O-Voxel, экспорт GLB. Первоисточник.
- [S8] Каталог видео V: `CniycUnvcX4` (CGMatter, сплаты в 5.3), `wWFOEJc8z60` (Khronos, сплаты в glTF) — только строки каталога, транскрипты не читались (режим экономии).
