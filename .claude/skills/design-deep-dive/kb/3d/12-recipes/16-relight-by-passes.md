# 16 · Переосвещение по проходам Blender: «фонарик» за курсором поверх готового кадра (WebGL2, без three)

Испытание 15-showcase · рецепт по итогам фаз 1–2 · агент RC, 26.09.2026; итог ночи SD3–SD4 (тени по карте сверху, цена кадра, телефон,
ворота) — `99-raw/experiments/SD/HANDOFF-3.md`, `15-showcase/sdano/README.md` · черновик — `99-raw/experiments/SD/HANDOFF-2.md §7` ·
Blender 5.2.2 (Cycles CPU, многочастный EXR), OpenImageIO из Blender, Pillow 11.3 + SciPy (системный Python), WebGL2 без библиотек,
esbuild 0.28.2 · пример — «Сдано» C «фонарик инженера»: страница `15-showcase/sdano/c-hybrid/`, исходники `examples/16-relight-by-passes/src/`
(`examples/16-relight-by-passes/src/{run_v2.py,passes_convert.py,fx_assets.py,fonarik.js}`) · пробел базы: выжимка
`15-showcase/_shared/digests/03-web-delivery.md` A.1 п. 14 («шейдера параллакса или переосвещения в базе нет»).

## Выжимка рецепта

1. **Кадр Blender — это и постер (LCP), и «день»; проходы той же камеры — данные для света**: альбедо (Diffuse Color), нормали в
   пространстве камеры, глубина → **высота**, AO; в браузере — один полноэкранный треугольник WebGL2; итог SD3 — 6,05 КБ br кода (17,1 КБ
   min) и 172 КБ данных после `load` (альбедо 50 + нормали/высота 106 + AO 7 + карта высот сверху 10; у SD2 было 5,5 КБ br и 187,5 КБ)
   [проверено: SD2–SD3; `sdano/c-hybrid/`, `15-showcase/sdano/README.md`].
2. **Проходы — в многочастный EXR** (`use_pass_diffuse_color/normal/z/ambient_occlusion`, `media_type = "MULTI_LAYER_IMAGE"`,
   32 бита): альбедо в полном размере 16 спп — 11,5 с, нормали/глубина/AO в половинном 64 спп — 11,5 с (сам кадр 1800×1905 × 128 спп —
   103 с); на время проходов ловец теней заменить настоящим белым полом — у пола появятся альбедо, нормаль, глубина и AO [проверено: SD `run_v2.py`, `C_passes.json`].
3. **Читать EXR через OIIO по индексу части**: `read_image(i, …)`; `read_image(0, …)` всегда читает Combined; EXR из OIIO уже сверху
   вниз; проход AO называется «Ambient Occlusion», глубина — `Depth.Z` [проверено: SD `rules.md`].
4. **Нормали мира → пространство камеры** проекцией на столбцы матрицы камеры (вправо, вверх, к зрителю), упаковка `n·0,5 + 0,5` [проверено: SD].
5. **Для орто-изометрии хранить высоту, а не глубину**: `h = 0,8165·w − 0,57735·(d − 30)`, точка пикселя восстанавливается точно
   (`P = u·R + w·U + s·F`, `s = (0,8165·w − h)/0,57735`); 8 бит = 7 мм, канал ≈ 27 КБ против ≈ 150 КБ 16-битной глубины; сверка:
   бумага −0,02 у обоих краёв кадра, срез стен 1,10, каска 1,77 [проверено: SD `fx_assets.py`, `fxsrc/fx_meta.json`].
6. **Данные — четыре текстуры** (итог SD3; у SD2 — три, с «теневой» высотой в альфе): альбедо WebP q85 (с потерями — это цвет),
   нормаль XY + высота — одна WebP **без потерь** (`fx-nh.webp` 106 КБ, проверка байт в байт), AO — отдельная четверть-текстура 6,7 КБ
   (в альфе альбедо AO раздувал файл до 235 КБ), карта высот сверху — `fx-td.webp` 9,8 КБ [проверено: SD2–SD3; `15-showcase/sdano/README.md`].
7. **Загрузка данных без цветовых преобразований**: `createImageBitmap(blob, {colorSpaceConversion: 'none', premultiplyAlpha: 'none'})`
   + `UNPACK_COLORSPACE_CONVERSION_WEBGL = NONE`; постер — как цвет (sRGB) [проверено: `fonarik.js`].
8. **Свет**: точка над целью со смещением (как солнце кадра — тени в ту же сторону), конус 8°/17° + рассеяние до 38°, спад 1/r²;
   **тень — по карте высот сверху из той же сцены Blender** (итог SD3): лучи BVH вертикально вниз по клетке 2 см (508×366, 534 тыс.
   лучей за 2,1 с в `blender -b`), R — мягкий верх стоящих тел, G/B — низ/верх «парящих» (головки булавок, радиаторы) → `fx-td.webp`
   9,8 КБ; в шейдере — марш от точки к фонарю в мировых XY, **всегда 80 шагов** (переменное число шагов — крапинки на полутени), выше
   1,8 м заслонять нечему, полутень по наименьшему вертикальному зазору (2 см + 6 % расстояния), размытие σ 1 клетка у обоих слоёв;
   экранный марш по «теневой» высоте (SD2: 32 шага, допуск толщины, открытие 5×5, mip-конус) не годится — экранная высота не знает,
   что за стеной (4 попытки: зерно, полосы, «сетка», «кольчуга» mip-конуса — §6); приёмник — ближайший тексель [проверено: SD `rules.md`
   (SD3), `shots/sd3_dbg5/dbg0.png` → `shots/sd4_dbg_crack/dbg0.png`, `15-showcase/sdano/gallery/topdown-shadows.webp`].
9. **Первый кадр = постер**: ΔE постер → кадр 0 шейдера — среднее 0,27, p95 1,09 (p99 5,5, max 28,7 — края среза и пересэмплирование;
   SD3 — 0,27 / p95 1,08) [проверено: SD `shots/sd2_c2…c4/c_fx.json`; `15-showcase/sdano/README.md`].
10. **Кадры только по вводу**: наведение/касание → rAF с догонянием (λ 14 и 7), стоп при |Δ| < 0,5 px — 0 кадров за 1,5 с покоя; reduce,
    `saveData`, нет WebGL2 → только постер; «нашёл» — по точкам самих дефектов в конусе 13°: 4 из 4 [проверено: SD `c_fx.json`].
11. **Полумрак — только по маске макета** (бумага h = −0,02 остаётся днём); но мягкое плечо, наложенное на весь кадр, переводит белую
    бумагу 255 → 241 — серый прямоугольник сцены на белой странице: плечо — только там, где макет или свет фонаря; правка SD3 — бумага в
    полумраке снова #fff; пикселями кадра 1440×900 в полумраке: серого 238–244 — 8,7 % → 0,2 %, белого ≥ 254 — 63,3 → 71 % [проверено:
    RC-checks `rc_shift_shoulder.py` + пиксели `SD/shots/sd2_c4`, `sd3_c5` → `sd3_c10/c_beam-off.png` (проверка BU2); SD `rules.md`].
12. **Цена и ворота** (SD4, тишина): кадр — суммой 400 кадров (`scripts/fx_bench2.py`, луч на трещине, полумрак 1) — 1,31 мс с ожиданием
    GPU / 0,24 мс пропускная на Iris Xe при DPR 1 (холст 660×698), 1,84 / 0,67 при DPR 2, телефон-режим 1,17 / 0,24; `fx_probe` — 0 кадров
    в покое, 60 к/с под курсором (p95 16,8 мс), 1 вызов на кадр (его `__bench` в прогоне вернул 0 — перепроверять); телефон — касание
    ведёт луч + один показ 2,24 с после прокрутки посетителя; запись 10 с — найдены все 4 пункта; ворота C (L1): LCP 60 / 864 / 48 мс,
    TBT 0 / 42, `motion_check` 0/0/0 (после бюджета спеки 1 — §7) [проверено: SD `HANDOFF-3.md §1–2`, `gates/c-hybrid/fx/fx_bench2.json`,
    `fx_index.json`, `gates/c-hybrid/motion/gates.md`]. Слепое голосование (заказчик, 26.09): на кадре первого экрана «план с
    дефектами» B > C — фонарик в середине взаимодействия не выиграл у неподвижного кадра (пара s-beam-bc, вопрос page;
    `15-showcase/vote/results.md`); его довод — действие «найди сам», которое кадр не передаёт.

## 1. Бриф-пример и границы

«Услуга “приёмка квартиры” (L0 → ветка L1): изометрический разрез квартиры из Blender; наведи курсор — сцена гаснет, луч фонаря
инженера находит дефекты, пункт акта отмечается “найдено”; телефон — касание» (`15-showcase/sdano/art-direction.md §7`, `SD/HANDOFF.md §4.1`).

| годится | не годится → куда |
|---|---|
| неподвижная камера, кадр Blender уже есть (постер) — нужен «свет по вводу» | камера движется или предмет вращается → живое 3D (рецепты 14, 15) |
| ортокамера (изометрия, план, фасад) — высота восстанавливается точно | перспектива: реконструкция по глубине и проекции камеры [не проверено в испытании] |
| L1: без three, JS эффекта ≤ 100 КБ br (задание SD; вышло 5,5, итог SD3 — 6,05), данные после `load` | карты глубины «из нейросети» (Codrops Relighting Images) — у нас проходы точные |

## 2. Паспорт данных

| канал | откуда (Blender) | формат на странице | размер | зачем |
|---|---|---|---|---|
| постер | кадр Cycles 128 спп + OIDN, 1800×1905 | тот же `<img>` B (AVIF/WebP по `srcset`) | 0 лишних байт | LCP и текстура «дня» |
| альбедо | `Diffuse Color`, полный размер, 16 спп, линейное → sRGB 8 бит | WebP q85, 1440 w | 49,8 КБ | цвет под лучом фонаря |
| нормаль XY | `Normal` (мир) → камера, половинный размер, 64 спп | R, G в `fx-nh.webp` (без потерь, 900×952) | 131,0 КБ на всю текстуру | закон Ламберта `N·L` |
| высота | `Depth.Z` → `h` (орто) | B в `fx-nh.webp`, −0,02…1,78 м, шаг 7 мм | — | точка пикселя в мире, тень |
| «теневая» высота (SD2; в итоге SD3 заменена картой сверху) | `h` после открытия 5×5 + гаусс σ 0,7 | A в `fx-nh.webp` (инверсия: у пола ≈ 252) | — | марш тени без игл и ножек |
| карта высот сверху (SD3) | лучи BVH вниз по клетке 2 см: R — верх стоящих тел, G/B — низ/верх парящих | `fx-td.webp` 508×366, 9,8 КБ | — | марш тени от точки к фонарю в мировых XY, 80 шагов |
| AO | `Ambient Occlusion`, медиана 3 + гаусс σ 1,6 | серый WebP q80, 450×476 | 6,7 КБ | отражённый свет в пятне |
| телефон | вырезка того же рендера `crop_px [335, 105, 1737, 1863]` | те же текстуры, UV-преобразование | 0 | один набор данных на оба кадра |

Числа — `99-raw/experiments/SD/pagebuild/fxsrc/fx_meta.json`, `renders/v2/C_passes.json` [проверено: SD2].

## 3. Blender: проходы в многочастный EXR

```python
# [проверено: 12-recipes/examples/16-relight-by-passes/src/run_v2.py, запуск SD-v2 25.09 19:45] Blender 5.2.2 — отрывок [не исполняется] # run: skip
    catcher = bpy.data.objects.get("SD_ShadowCatcher")
    catcher.hide_render = True
    st = bpy.data.collections.get("STAGE")
    ground = bpyx.primitive("plane", "SD_GroundPaper", size=80.0, location=(4.7, 3.2, -0.02), collection=st)
    gm = bpyx.principled("SD_Paper", base_color="#f6f6f4", roughness=0.95)[0]
    bpyx.assign_material(ground, gm)
    sc = bpy.context.scene
    vl = bpy.context.view_layer
    vl.use_pass_diffuse_color = True
    vl.use_pass_normal = True
    vl.use_pass_z = True
    vl.use_pass_ambient_occlusion = True
    sc.world.light_settings.distance = 0.7

    def exr(path, rres, spp):
        S.cycles(spp, denoise=False)
        sc.render.film_transparent = False
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = rres[0], rres[1], 100
        ims = sc.render.image_settings
        ims.media_type = "MULTI_LAYER_IMAGE"
        ims.color_depth = "32"
        sc.render.filepath = path
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        return round(time.time() - t1, 2)

    T["pass_full_s"] = exr(f"{out}/passes_full.exr", full, 16)
    T["pass_half_s"] = exr(f"{out}/passes_half.exr", half, ps)
```

Чтение частей EXR и перевод нормалей в пространство камеры (тот же код — в `passes_convert.py`, чтобы не рендерить заново):

```python
# [проверено: 12-recipes/examples/16-relight-by-passes/src/passes_convert.py, запуск SD-passconv] Blender 5.2.2 + OIIO — отрывок [не исполняется] # run: skip
def read_parts(path):
    inp = oiio.ImageInput.open(path)
    chans = {}
    i = 0
    while inp.seek_subimage(i, 0):
        spec = inp.spec()
        px = inp.read_image(i, 0, 0, spec.nchannels, "float")   # i-я часть многочастного EXR, не 0
        px = np.asarray(px).reshape(spec.height, spec.width, spec.nchannels)
        for ci, nm in enumerate(spec.channelnames):
            chans[nm] = px[..., ci]
        i += 1
    inp.close()
    return chans

nrm, nN = pick(chH, "normal", ("X", "Y", "Z"))
Rm = cam.matrix_world.to_3x3()
right, up, back = [np.array(Rm.col[i].normalized()) for i in range(3)]
ncam = np.stack([nrm @ right, nrm @ up, nrm @ back], -1)
ln = np.linalg.norm(ncam, axis=-1, keepdims=True)
ncam = ncam / np.maximum(ln, 1e-6)
```

Глубина ортокамеры Cycles — расстояние от плоскости камеры: у кадра «Сдано» 29,193–42,049 м (`C_passes.json`). В Blender нет Pillow —
PNG/WebP делаются системным Python (SD `rules.md`).

## 4. Высота вместо глубины (орто-изометрия)

Истинная изометрия: орто, азимут −45°, угол места 35,264° (tg = 1/√2). Экранные оси кадра `(u, w)` в метрах (`frame_uw`: u −4,9…3,7,
w −0,6…8,5), оси камеры `R, U, F`. Точка пикселя с высотой `h` над полом: `P = u·R + w·U + s·F`, `s = (0,8165·w − h)/0,57735`
(глубина = 30 + s). Отсюда `h = 0,8165·w − 0,57735·(d − 30)` — точная реконструкция в 8 битах.

```python
# [проверено: 12-recipes/examples/16-relight-by-passes/src/fx_assets.py, main()] Python 3 + Pillow + SciPy — отрывок [не исполняется] # run: skip
    d = dmin + (da[..., 0] * 256 + da[..., 1]) / 65535 * (dmax - dmin)
    Hh, Wh = d.shape
    w = FR["w1"] - (np.arange(Hh) + 0.5) / Hh * (FR["w1"] - FR["w0"])
    h = 0.81649658 * w[:, None] - 0.57735027 * (d - 30.0)
    h8 = np.clip(np.round((h - H_OFF) / H_RANGE * 255), 0, 255).astype(np.uint8)
    nrm = np.asarray(Image.open(f"{V}/C_normal_cam.png").convert("RGB"))
    ao = ndimage.gaussian_filter(ndimage.median_filter(da[..., 2], 3), 1.6)
    ao8 = (np.round(ao / 255 * 23) / 23 * 255).astype(np.uint8)
    hs = ndimage.gaussian_filter(ndimage.grey_opening(h, size=(5, 5)), 0.7)
    hs8 = np.clip(np.round((hs - H_OFF) / H_RANGE * 255), 0, 255).astype(np.uint8)
    nh = np.dstack([nrm[..., 0], nrm[..., 1], h8, 255 - hs8]).astype(np.uint8)
    Image.fromarray(nh).save(f"{OUT}/fx-nh.webp", "WEBP", lossless=True, quality=100, method=6, exact=True)
    back = np.asarray(Image.open(f"{OUT}/fx-nh.webp").convert("RGBA"))
    assert int(np.abs(back.astype(int) - nh.astype(int)).max()) == 0, "WebP без потерь изменил данные"
```

`exact=True` у WebP без потерь обязателен: иначе кодер вправе менять RGB под прозрачной альфой (данные — не картинка)
[документация: Pillow, параметр WebP `exact`; проверено: `assert` байт в байт выше].

## 5. Шейдер: свет фонаря, тень по высоте, полумрак

Отрывок ниже — шейдер SD2 (экранный марш по «теневой» высоте, 32 шага); итог SD3 заменил тень картой высот сверху (выжимка п. 8, §6) —
актуальный код — `examples/16-relight-by-passes/src/fonarik.js`.

```js
// [проверено: 12-recipes/examples/16-relight-by-passes/src/fonarik.js, фрагментный шейдер (сборка 21:20)] WebGL2 GLSL ES 3.0 — отрывок
vec3 world(vec2 uv, float h) { float u = FR.x + uv.x * (FR.y - FR.x), w = FR.w - uv.y * (FR.w - FR.z);
  return u * R + w * U + ((0.81649658 * w - h) / 0.57735027) * F; }
vec2 toUV(vec3 p) { return vec2((dot(p, R) - FR.x) / (FR.y - FR.x), (FR.w - dot(p, U)) / (FR.w - FR.z)); }
float hgtS(vec2 uv, float lod) { return (1.0 - textureLod(uNH, uv, lod).a) * HR + HO; }   /* «теневая» высота (без игл), mip — по конусу */
  // … в main():
  vec4 nh = nhN(uf);                                         /* приёмник — ближайший тексель: без «висящих» точек на силуэтах */
  vec3 alb = s2l(texture(uAlb, uf).rgb); float ao = texture(uAO, uf).r;
  vec2 nxy = nh.rg * 2.0 - 1.0;
  vec3 N = normalize(nxy.x * R + nxy.y * U - sqrt(max(0.0, 1.0 - dot(nxy, nxy))) * F);
  float h = nh.b * HR + HO;
  vec3 P = world(uf, h);
  vec3 T = world(uTarget, hgt(uTarget));
  vec3 Lp = world(uLamp, hgt(uLamp)) + uOff;
  vec3 Ld = Lp - P; float dist = length(Ld); vec3 L = Ld / dist;
  float ct = dot(-L, normalize(T - Lp));
  float cone = smoothstep(0.9563, 0.9903, ct) + 0.06 * smoothstep(0.788, 0.9563, ct);
  float ndl = max(dot(N, L), 0.0);
  float sh = 1.0;
  if (cone * ndl > 0.001) {                                  /* мягкая тень по карте высот: полутень растёт с расстоянием */
    float tm = clamp((1.9 - P.z) / max(Ld.z, 1e-3), 0.0, 1.0), len = dist * tm;
    vec3 P0 = P + N * 0.03;
    for (int i = 1; i <= 32; i++) {                          /* шаг по высоте ≈ 6 см < полутени: без дизеринга и штриховки */
      float t = (float(i) - 0.5) / 32.0;
      vec3 Q = P0 + Ld * (tm * t);
      vec2 q = toUV(Q);
      if (q.x < 0.0 || q.x > 1.0 || q.y < 0.0 || q.y > 1.0) break;
      float pen = 0.035 + 0.10 * t * len;                    /* ширина полутени, м: растёт с расстоянием от приёмника */
      float dh = hgtS(q, clamp(log2(max(1.0, pen * 52.0)), 0.0, 4.0)) - Q.z;   /* 104,7 текс./м × ½ ширины → уровень mip */
      float wgt = 1.0 - smoothstep(0.18, 0.30, dh);
      sh = min(sh, mix(1.0, smoothstep(-0.5, 0.5, -dh / pen), wgt));
    }
  }
  float fall = dot(uOff, uOff) / (dist * dist);
  vec3 E = vec3(1.0, 0.93, 0.82) * uPower * cone * ndl * fall * sh;
  float red = smoothstep(0.18, 0.40, alb.r - max(alb.g, alb.b));
  vec3 day = s2l(poster);
  float model = smoothstep(-0.016, -0.008, h);                 /* бумага (h = −0,02) — это страница: она остаётся днём */
  float dk = uDark * model;
  vec3 lit = day * (1.0 - 0.88 * dk) * mix(vec3(1.0), vec3(0.78, 0.85, 1.05), dk)
           + alb * E * (1.0 + 0.9 * red) * mix(1.0, ao, 0.4)
           + alb * (0.10 * uPower * cone * fall) * ao * vec3(1.0, 0.93, 0.82)              /* отражённый свет в пятне, AO */
           + day * red * (1.0 - smoothstep(0.02, 0.06, abs(h - 0.34))) * 0.8 * dk;          /* лазерная линия светится и в темноте */
  o = vec4(l2s(mix(lit, shoulder(lit), uDark)), 1.0);
```

Последняя строка — источник серого прямоугольника: `shoulder()` сжимает и белую бумагу (1,0 → 0,88 линейно → 241/255). Проверка
арифметикой (формула плеча — та же, что в шейдере):

```python
# run: system
# Python 3 — [проверено: 99-raw/notes/trial/RC-checks/rc_shift_shoulder.py; пиксели SD/shots/sd2_c4 и sd3_c5: бумага 240–241 при 255 вокруг]
def shoulder(c):
    pk = max(c)
    s, d = 0.76, 0.24
    if pk < s:
        return list(c)
    npk = 1 - d * d / (pk + d - s)
    c = [v * npk / pk for v in c]
    g = 1 - 1 / (0.15 * (pk - npk) + 1)
    return [v * (1 - g) + npk * g for v in c]


def l2s(x):
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055


paper = shoulder([1.0, 1.0, 1.0])[0]
px = round(l2s(paper) * 255)
assert abs(paper - 0.88) < 1e-9 and px == 241
print("shoulder: бумага 1,0 → %.3f линейно → sRGB %d (замер на снимках 240–241)" % (paper, px))
```

Правка-кандидат: `o = vec4(l2s(mix(lit, shoulder(lit), uDark * model)), 1.0);` — плечо только по маске макета (бумага остаётся 255, в пятне
фонаря бумага уходит в белое) — сделано SD3: бумага в полумраке снова #fff [проверено: SD `rules.md`, `SD/shots/sd3_c10/c_beam-off.png`].

## 6. Тени: четыре попытки экранного марша и итог — карта высот сверху

| попытка | как | что видно | причина | доказательство |
|---|---|---|---|---|
| 1 | жёсткий тест + дизеринг | зерно | 16 шагов, случайный сдвиг | SD `HANDOFF-2.md §5` |
| 2 | мягкая тень по «углу возвышения», без дизеринга | полосы и «сетка» | допуск толщины 0,45 м по высоте (≈ 0,8 м глубины), шаг луча ≈ 7 текселей против иглы 2–3 | `shots/sd2_dbg*/` |
| 3 | допуск 0,18–0,30 м + отдельная «теневая» высота (открытие 5×5) | полосы ушли, «сетка» у фигуры осталась | тонкое убрано; силуэт фигуры — ступенями текселей | `sd2_dbg3/dbg_crop_shadow_vs_final.png` |
| 4 | mip-конус: высота с mip по ширине полутени | «кольчуга» у фигуры | экранная высота не знает, что за стеной: любой допуск «толщины» ошибается | SD `shots/sd3_dbg5/dbg0.png` |
| итог (SD3) | карта высот сверху из Blender (лучи BVH вниз, клетка 2 см; стоящие и парящие тела — разные каналы) + марш 80 шагов в мировых XY | тени чистые; совмещение с кадром — медиана −2 мм на горизонтальных гранях | — | SD `shots/sd4_dbg_crack/dbg0.png`, `15-showcase/sdano/gallery/topdown-shadows.webp`, `scripts/topdown_hf.py` |

Правила из попыток: допуск «толщины» — по реальной толщине вдоль луча зрения (стена ≈ 0,12 м по высоте, фигура ≈ 0,2 м), тонкое — из
теневой карты убрать, приёмник брать ближайшим текселем (линейная интерполяция на силуэтах даёт светлый ореол) [проверено: SD `rules.md`].

## 7. Поведение страницы

```js
// [проверено] — отрывок: данные без преобразований цвета, кадры только по вводу
async function bitmap(url) {
  const r = await fetch(url); const b = await r.blob();
  return createImageBitmap(b, { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
}
  // …
  const [bA, bN, bO] = await Promise.all(['albedo', 'nh', 'ao'].map(n => bitmap(`assets/fx-${n}.webp`)));
  gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
  // …
  const tick = ts => {
    const dt = Math.min(0.05, last ? (ts - last) / 1000 : 0.016); last = ts;
    const k1 = 1 - Math.exp(-14 * dt), k2 = 1 - Math.exp(-7 * dt);
    for (let i = 0; i < 2; i++) { beam[i] += (aim[i] - beam[i]) * k1; lamp[i] += (beam[i] - lamp[i]) * k2; }
    const sp = darkTo > dark ? dt / 0.45 : dt / 0.6; dark = darkTo > dark ? Math.min(darkTo, dark + sp) : Math.max(darkTo, dark - sp);
    draw(); check();
    const r = stage.getBoundingClientRect(), px = Math.hypot((aim[0] - lamp[0]) * r.width, (aim[1] - lamp[1]) * r.height);
    if (dark === darkTo && px < 0.5) { raf = 0; last = 0;
      if (dark === 0) { on = false; fig.classList.remove('is-dark', 'fx-on'); pins.forEach(p => p.classList.remove('is-lit')); } return; }
    raf = requestAnimationFrame(tick);
  };
```

- Запуск: после `load` + `requestIdleCallback` (≤ 2 с); reduce, `saveData`, нет WebGL2 → только постер; контекст `webgl2` с
  `powerPreference: 'low-power'`, без глубины и сглаживания; DPR ≤ 2 (телефон ≤ 1,5).
- «Нашёл»: расстояние от оси луча до **точек самих дефектов** (трещина, шов окна на 0,87 м, пол, розетка), а не до головок булавок;
  конус 13°; подсказка — у ближайшей к центру луча; пункт акта получает «найдено».
- Телефон: касание переносит луч, гашение через 9 с; решение оркестратора — один показ 2,24 с (окно → трещина → уклон, свет возвращается
  0,6 с) только после прокрутки посетителя (scrollY > 40, план ≥ 70 % в кадре, задержка 0,35 с), без петли, reduce — без него; первый
  экран при загрузке неподвижен. `motion_check` L1 видит показ как «движение в видимой зоне» (EG-A11Y-17, 17,8 % пикселей за 1 с) — бюджет
  спеки `budget.loops_in_view_max` ≥ 1 (читается одно число на оба режима; с 0 — fail_S 1) [проверено: SD `HANDOFF-3.md §1, §4`,
  `gates/c-hybrid_sd3-0455/` → `gates/c-hybrid/motion/gates.md`].
- Вне ввода страница C = B: для кадров судьи — снимки по сценарию курсора (`__fonarik.aim(x, y)`) и запись 10 с.

## 8. Вес, время, точность

| величина | значение | доказательство |
|---|---|---|
| JS эффекта | 15,4 КБ min / 5,5 КБ br (SD2) → итог SD3: 17,1 КБ / **6,05 КБ br**, без three | SD `HANDOFF-2.md §1`, `HANDOFF-3.md §2` |
| данные после `load` | 49,8 + 131,0 + 6,7 = 187,5 КБ (SD2) → итог SD3: 50 + 106 + 7 + 10 (карта сверху) = **172 КБ** | `fx_meta.json`; `15-showcase/sdano/README.md` |
| карта высот сверху | 508×366, 534 тыс. лучей BVH — 2,1 с в `blender -b`; `fx-td.webp` 9,8 КБ | SD `scripts/topdown_hf.py` |
| встроенный скрипт страницы B/C | 2 582 Б / 1 006 Б br (бюджет спеки B — 1 КБ, на грани) | SD `HANDOFF-2.md §2` |
| готовность `__ready` | 0,19–0,68 с после `load` (локально) | `c_fx.json` (4 прогона) |
| покой | 0 кадров за 1,5 с | `c_fx.json` |
| ΔE постер → кадр 0 | 0,27 среднее, 1,09 p95, 5,5 p99, 28,7 max (десктоп, DPR 1) | `c_fx.json` |
| проходы Blender | 11,45 с (альбедо 1800×1905, 16 спп) + 11,47 с (половинный, 64 спп); кадр 103 с | `C_passes.json` |
| мс на кадр шейдера | 1,31 с ожиданием GPU / 0,24 пропускная (DPR 1, 660×698); 1,84 / 0,67 (DPR 2); телефон-режим 1,17 / 0,24 | SD `gates/c-hybrid/fx/fx_bench2.json` |

## Частые ошибки

| ошибка | симптом | исправление | где поймано |
|---|---|---|---|
| `read_image(0, …)` для всех частей EXR | все каналы = Combined | `read_image(i, …)` после `seek_subimage(i, 0)` | SD |
| перевернули EXR из OIIO | данные вверх ногами | OIIO отдаёт сверху вниз — как PNG | SD |
| искали проход «AO» / «Z» | канал не найден | «Ambient Occlusion», `Depth.Z` (5.x) | SD; выжимка 03 A.2 п. 14 |
| мировые нормали в шейдере кадра | свет «с другой стороны» | проекция на столбцы матрицы камеры | SD |
| 16-битная глубина hi/lo в PNG | ≈ 150 КБ канала | высота 8 бит (орто) — 27 КБ, 7 мм | SD2 |
| AO в альфе альбедо WebP | альбедо 235 КБ | AO отдельной четверть-текстурой 6,7 КБ | SD2 |
| данные через `<img>`/текстуру с преобразованием цвета | нормали и высота «поехали» | `createImageBitmap` без преобразований + `UNPACK_COLORSPACE_CONVERSION_WEBGL = NONE` | SD |
| линейная интерполяция высоты на силуэтах | «висящие» точки, светлый ореол у фигуры | ближайший тексель приёмника (`texelFetch`) | SD2 |
| большой допуск «толщины» и тонкие иглы в теневой карте | полосы, «сетка» | допуск по толщине вдоль луча 0,18–0,30; открытие 5×5 | SD2 |
| полумрак на всём кадре | серый прямоугольник на белой странице | гасить только макет (`model` по высоте) | SD2 |
| плечо тона на всём кадре | бумага 241 вместо 255 | плечо по маске макета (правка-кандидат §5) | RC |
| «нашёл» по головкам булавок | дефект «найден» мимо | по точкам самих дефектов | SD2 |
| `timeout N` поверх `slot_run` | ожидание очереди убито | не ставить (ожидание замка бывает 1–30 мин) | SD2 |

## Чек-лист

- [ ] Постер = кадр той же камеры, что проходы; телефонный кадр — вырезка того же орто-рендера?
- [ ] Проходы: альбедо полного размера, нормали/глубина/AO половинного; пол — настоящий, не ловец?
- [ ] Нормали — в пространстве камеры; для орто — высота 8 бит; WebP без потерь `exact=True` с проверкой байт в байт?
- [ ] Загрузка данных без преобразований цвета; постер — как цвет?
- [ ] Тень: карта высот сверху из той же сцены (стоящие и парящие тела — разные каналы), марш 80 шагов в мировых XY, ближайший тексель
  приёмника; полумрак и плечо — только по маске макета (бумага #fff)?
- [ ] ΔE постер → кадр 0 ≤ 0,3 (среднее); 0 кадров в покое; reduce/saveData/без WebGL2 → постер?
- [ ] `fx_probe` (мс/кадр), ворота L1, запись 10 с, телефон касанием?

## Открытые вопросы и противоречия

1. Выжимка 03 (A.1 п. 14) держала «переосвещение/параллакс» пробелом базы — рецепт закрывает переосвещение для орто-кадра; **параллакс
   по глубине** из плана C (`sdano/art-direction.md §7`) не делался [не проверено].
2. Перспективная камера: высота как 8-битный канал теряет точность реконструкции — нужна глубина и матрица проекции [не проверено].
3. Сравнение с нейросетевой глубиной Codrops (Relighting Images) по виду и весу не проводилось [не проверено].
4. mip-конус тени (не годится — §6), показ на телефоне, `fx_probe`, ворота и кадры судьи C — сняты SD3–SD4 (выжимка п. 8, 12; §7–§8);
   открыто: цена кадра на реальном телефоне (EG-LIVE-01 — вручную с устройством), `__bench` в прогоне `fx_probe` = 0 (причина не найдена),
   отметки 5–7 плана за краем кадра (кадр шире или второй ракурс, ≈ 1 ч с рендером) [SD `HANDOFF-3.md §5–6`].

## Ссылки

Черновик — `99-raw/experiments/SD/HANDOFF-2.md §7`; план — `SD/HANDOFF.md §4.1`; журнал правил — `SD/rules.md`; страница —
`15-showcase/sdano/c-hybrid/`; проходы в базе — `../06-materials-lighting-render/04` §4.1 (многочастный EXR); изометрия —
`../05-modeling/04-styles-and-archetypes.md §6.2`; постер → живое без прыжка — `12-recipes/01 §5`; выжимка `15-showcase/_shared/digests/03-web-delivery.md` A.1–A.2 п. 14.
