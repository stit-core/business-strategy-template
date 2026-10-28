# Ворота экспорта и страницы: GLB, анимация, цвет, страница в браузере; сводный `qa_pipeline.py`

Волна 3 · агент J · 23.09.2026 · новых источников 2 (+ E `08/04`, F1 `09/05`, F2, H, D2, A) · эксперимент J/03 (3 GLB, 2 страницы,
2 турнтейбла) · Blender 5.2.2, glTF-IO 5.2.40, three r186 (jsDelivr), Chromium headless (ANGLE GL, Intel Iris Xe).

Конвейер: `../../scripts/3d/qa_pipeline.py scene | glb | page` — тонкая обёртка над готовыми утилитами E, F1, A, H; вердикт
`fail/review/pass` — в JSON; код выхода 0 — замер выполнен, 2 — сбой; с `--strict` — 1 / 3 / 0. Проверки сцены — `01-scene-geometry-checks.md`; рендер и критика — `02`.

## Выжимка для агента

1. **Цепочка GLB по порядку E**: `preflight()` в Blender → валидатор Khronos (`gltf_check.py`) → `glb_lint()` → что создал three
   (`gltf_web_inspect.py`) → Blender против three (`gltf_diff.py`) → цена загрузки (`gltf_load_bench.py`); первые четыре — секунды,
   гоняйте всегда; diff и бенч — перед сдачей. → §1 `[проверено]`
2. **Валидатор не видит смысловых потерь** (процедуры, цветовое пространство, морфы) — их ловят `preflight()` и `gltf_diff`. → §2 `[проверено: E]`
3. **`gltf_diff` сравнивает только ассет**: по `.blend` со студией он рендерит циклораму и пол, а GLB — без них → IoU 0,002, ΔE 9,96
   на кружке C1/12; копия `.blend` только с `ASSET_*` → IoU 0,997, ΔE 3,07. `qa_pipeline` делает копию сам. → §2.2 `[проверено]`
4. **Пороги `gltf_diff` (E/02)**: ΔE2000 ≤ 3,5 и IoU ≥ 0,99 — совпадает; ΔE > 6 или IoU < 0,95 — поломка; между — смотреть лист.
   Шум метода на одном файле ΔE ≈ 3,1. → §2.2 `[проверено]`
5. **Перед `gltf_diff` в EEVEE**: `world.sun_threshold = 0` (иначе яркое HDRI выносится в «солнце», +13 L* на гранях вверх);
   HDRI само даёт ±6 L*; материалы (стекло, анизотропия, плёнка) — `--engine cycles`. → §2.2 `[проверено: D2]`
6. **Цвет бренда — отдельная проверка**: пара Khronos PBR Neutral ↔ `NeutralToneMapping`, ΔE к hex ≤ 2, Blender ↔ three ≤ 1,1 (D2:
   0,23–0,36 и 1,8–1,9); AgX выцветает бренд (ΔE 7–9). → §4 `[проверено: D2]`
7. **Анимация проверяется числами без рендера**: список клипов и длительностей, начало в 0 с, углы турнтейбла в четвертях,
   позиции узлов в 3–5 моментах (`three_probe.py`); рендеры по кадрам (`anim_diff.py --mute-nla`, IoU ≥ 0,99) — только при
   расхождении. → §3 `[проверено]`
8. **Турнтейбл без сэмплирования ломается молча**: 3 ключа 0/180/360° → в three крутится назад (318 / 228 / 138 / 48° вместо
   45 / 135 / 225 / 315°); ворота по четвертям это ловят. → §3 `[проверено]`
9. **Ворота страницы** — `gate_check()` F1 по отчёту `site_probe.py`: LCP-элемент не canvas, LCP, CLS, TBT, вес, 3D-ассеты,
   вызовы в покое, DPR, 0 ошибок консоли, reduce → 0 вызовов и 0 движения. → §5 `[проверено: F1, J/03]`
10. **Порог TBT десктопа 150 мс** для hero с 3D — на границе: hero-lazy F1 175 мс, повтор J 172 мс на почти пустой странице;
    держите 150 как цель, 200 — как предел `[спорно]`. → §5.2
11. **Статика import map**: одна версия three у ядра и addons; `three.module.min.js` с jsDelivr только с переназначением
    `three.core.js → three.core.min.js` (иначе +204 КБ br). Оба демо F2 (`camera-path-scroll`, `shader-background`) эту
    ловушку F1 содержат. → §5.3 `[проверено]`
12. **Консоль**: «Multiple instances of Three.js» — две копии three (import map + бандл); любая ошибка консоли — `fail`. → §5.3
13. **Метка первого кадра модели своя** (`performance.mark` после первого `render()` с моделью): первый вызов отрисовки на странице —
    PMREM окружения, а не модель (F1). → §5.4 `[проверено: F1]`
14. **Время кадра в headless** — через `readPixels`/`onSubmittedWorkDone`, не `gl.finish()`; ≥ 5 прогонов (машина шумит);
    эффект ≤ 2 мс/кадр на Iris Xe при 1440×900 (F2). → §5.4 `[проверено: F2]`
15. **Реальных телефонов нет**: мобильные числа — эмуляция Pixel 7 с CPU ×4 и сетью 1,6 Мбит/с; писать это ограничение в отчёт. → §6

## 1. Конвейер `qa_pipeline.py`

| стадия | вызывает | ловит | время (J/03) |
|---|---|---|---|
| `scene` | `scene_check.py` (J) + `preflight()` (E, `08/04 §5`) в одном фоновом Blender | геометрия, паспорт, кадр, материалы; потери экспорта | 32 сцены ≈ 2 с |
| `glb` | `gltf_check.py` → `glb_lint()` (E `08/04 §6`) → `gltf_web_inspect.py` → [`gltf_diff.py`] → [`gltf_load_bench.py`] | спецификация, декодеры, вызовы, память, ошибки three, расхождение вида, цена загрузки | 1,8–4,2 с; с diff 8,5–10,6 с |
| `page` | `site_probe.py` (A) → `gate_check()` (F1 `09/05 §7.2`) + статика import map | LCP, TBT, вес, вызовы, reduce, консоль, копии three | 12–16 с на режим |

Уровни: ошибки валидатора, ошибки консоли, `diff` за порогом поломки, не пройденные ворота страницы — ERROR; предупреждения
валидатора и `glb_lint`, подсказки о сжатии, `diff` между нормой и поломкой, import map — WARN.

```bash
# Python 3 + Blender 5.2.2 + three r186 — [проверено] GLB кружки: цепочка E + diff
C=99-raw/experiments/C1/12-protocol-objects/out
python3 ../../scripts/3d/qa_pipeline.py glb $C/mug.glb --blend $C/mug.blend --diff
```

Вывод: `{"verdict": "review", "codes": ["hint"], …}` — геометрия не сжата (Meshopt добавит постобработка, E `08/03`); diff:
IoU 0,997, ΔE2000 3,07 (p95 7,1) — совпадает [проверено].

## 2. Ворота экспорта

### 2.1. Что проверяет каждая утилита (E) и что с этим делать

| проверка | инструмент | порог / сигнал | действие |
|---|---|---|---|
| потери до экспорта | `preflight()` | ERROR: shape keys + apply, UV > 4; WARN: процедуры, Mix Shader, цветовое пространство, fake-user действия | исправить до экспорта (E `08/04 §5`) |
| спецификация | `gltf_check.py` (валидатор Khronos 2.0.0-dev) | ошибки > 0 → ERROR | исправить экспорт |
| сжатие и вес | подсказки `gltf_check.py` | нет Draco/Meshopt, PNG, > 2048, > 5 МБ | постобработка `gltf-transform`/`gltfpack` (E `08/03`) |
| декодеры, вызовы, память | `glb_lint()` | transmission → ×2 вызовов; свет > 500 кд → SPEC (×683); `KHR_animation_pointer` без плагина | пресет COMPAT, отдельный материал |
| что создал three | `gltf_web_inspect.py` | ошибки консоли, `colorSpace` карт, имена и `userData`, клипы | E `08/04 §4` |
| вид | `gltf_diff.py` | §2.2 | лист `diff_sheet.png`: где ΔE > 5 |
| цена | `gltf_load_bench.py` | холодная/тёплая загрузка, первый кадр, память GPU | бюджеты F1 `09/05 §1.1` |

Быстрый ручной осмотр веса, памяти и текстур до и после сжатия — браузерные gltf.report и glTF Compressor [V:BH1R29YvLOk W23:43],
[V:qZGGolpYby0 W10:41] (W13); normal map выбирать кодек и качество отдельно от цветовых карт — артефакты сжатия на ней видны
сильнее (Flight Helmet) [V:qZGGolpYby0 W05:28–W06:54].

Результаты J/03: `camera_1k.glb` (hero-lazy, KTX2 + Meshopt) — 22 предупреждения валидатора, `glb_lint`: transmission рисует
непрозрачное ещё раз (10 вызовов, 53 974 треугольника в кадре при 26 987 в файле), бенч: холодная загрузка 200 мс, тёплая 25,
первый кадр 242 мс; `rocket.glb` — ΔE 3,52 (граница), IoU 0,996 [проверено].

### 2.2. `gltf_diff`: как не получить ложную поломку

- Источник — только ассет: копия `.blend` без геометрии вне `ASSET_*` (J/03: IoU 0,002 → 0,997). `qa_pipeline glb --blend … --diff`
  делает её автоматически; вручную — открыть копию, удалить подложку, сохранить `copy=True`.
- Пара тонмаппинга одинаковая с обеих сторон (`--tone standard|neutral|agx`); проверка экспорта — `standard`, проверка бренда —
  `neutral` (§4).
- EEVEE: яркое HDRI превращается в «солнце» (`world.sun_threshold`, по умолчанию 10) → +13 L* на гранях, смотрящих вверх; для
  сравнения ставить 0 (D2, вопрос E/20 закрыт). Само освещение окружением даёт ±6 L* между движками — пороги под HDRI шире.
- Стекло, анизотропия, иридесценция — `--engine cycles --samples 64`; анизотропия (ΔE 12–16) и иридесценция (4,5–7,9) в вебе не
  совпадают принципиально (D2) — не «чинить», а принять или заменить материал.
- Гипотеза E «ΔE ≤ 3,5 слишком строг для тёмных сцен, bloom и AgX» — не перекалибрована (экономия) `[не проверено]`; на двух
  протокольных объектах в `standard` норма соблюдена (3,07 и 3,52).

## 3. Ворота анимации (H)

`../../scripts/3d/three_probe.py` (перенесён из H/_lib): загрузить GLB в three r186 и выполнить JS-проверку (тело async-функции с
`THREE, gltf, scene, renderer, camera, render`) → JSON. `../../scripts/3d/anim_diff.py`: кадры Blender против three в одни и те же
моменты (IoU, ΔE по кадрам, лист). Проверки по порядку (H `07-animation/03`):

| ворота | как | порог |
|---|---|---|
| клипы и длительности | `gltf.animations.map(c => [c.name, c.duration])` | имена и длительности по паспорту анимации |
| начало в 0 с | первый ключ каждого трека | `export_anim_slide_to_zero` работает только с сэмплированием (H/10) |
| позы узлов | позиция/угол целевых узлов в 3–5 моментах | ±1 мм, ±0,5° |
| турнтейбл | угол вокруг Y в моменты ¼, ½, ¾ | 45 / 135 / 225 / 315° ± 1° |
| картинка | `anim_diff.py --frames … --mute-nla` | IoU ≥ 0,99 на каждом кадре |

```bash
# three r186 (Chromium) — [проверено] турнтейбл: сэмплирование (a) против 3 ключей без сэмплов (f)
H=99-raw/experiments/H/10-turntable
for v in a_linear_2keys_sampled f_linear_3keys_curves_180; do
  python3 ../../scripts/3d/three_probe.py $H/out/$v.glb $H/check_rot.js --out "$OUT_DIR/$v.json" > /dev/null
  python3 -c "
import json, sys
d = json.load(open(sys.argv[1])); ang = dict((t, a) for t, a in d['angles'])
ok = all(abs(ang[t] - e) <= 1 for t, e in ((0.5, 45), (1.5, 135), (2.5, 225), (3.5, 315)))
print(sys.argv[2], d['clip'], d['duration'], 'OK' if ok else 'FAIL', [ang[t] for t in (0.5, 1.5, 2.5, 3.5)])
" "$OUT_DIR/$v.json" $v
done
```

Вывод: `a_linear_2keys_sampled Turntable 4 OK [45, 135, 225, 315]`; `f_linear_3keys_curves_180 Turntable 4.0333 FAIL [318, 228, 138, 48]`
— вращение назад и сдвиг на кадр ловятся числом без рендера [проверено]. Для других клипов — свой `check.js` по образцу
`99-raw/experiments/H/10-turntable/check_rot.js`.

## 4. Ворота цвета (D2)

| проверка | как | порог | источник |
|---|---|---|---|
| брендовый hex на рендере | `view_hex` (OCIO) по пикселям брендового материала | ΔE2000 ≤ 2 при Khronos PBR Neutral | D2 `../06-materials-lighting-render/03 §4–5` |
| Blender ↔ three | `gltf_diff.py --tone neutral` | ΔE ≤ 1,1 на брендовом материале (замер D2 0,23–0,36) | D2, F1 |
| тест «белой печи» | белое окружение, сфера base color = фон: центр сферы не ярче фона | равенство ±1 L* | W3 [V:DQeP363Xmn4 31:56]; D2 `03 §5` |
| серия | светлота света и тени, насыщенность, высота в кадре | разброс светлоты тени ≤ 1 L* (D2: 0,9 против 6,4 без паспорта) | D2 `04-light-icons/sheets.py` |
| unlit в three | `material.toneMapped = false` | иначе ΔE до 5,7 | D2 |
| шейдерный фон | цвет фона против hex | ΔE ≤ 1; без `#include <colorspace_fragment>` ΔE 9,6 | F2 |

Код и числа — в файлах D2 и F2; здесь только ворота. Отдельный прогон J не делал (экономия).

## 5. Ворота страницы

### 5.1. `gate_check()` F1 и прогоны

| # | проверка (поле `probe*.json`) | телефон (Pixel 7, CPU ×4, 1,6 Мбит/с) | десктоп 1440×900 |
|---|---|---|---|
| 1 | LCP-элемент (`vitals_pre_scroll.lcp.tag`) | не CANVAS (постер, текст) | не CANVAS |
| 2 | LCP | ≤ 2 500 мс | ≤ 1 000 мс |
| 3 | CLS | ≤ 0,1 | ≤ 0,1 |
| 4 | TBT до прокрутки (вклад 3D) | ≤ 300 мс | ≤ 150 мс (`[спорно]`, §5.2) |
| 5 | передано | ≤ 3 072 КБ | ≤ 7 168 КБ |
| 6 | 3D-ассеты (`model3d + texture3d`) | ≤ 820 КБ | ≤ 1 536 КБ |
| 7 | вызовов в кадре в покое | ≤ 30 | ≤ 60 |
| 8 | reduce: вызовов и движения в покое | 0 и ≤ 0,05 % | 0 и ≤ 0,05 % |
| 9 | ошибки консоли | 0 | 0 |
| 10 | DPR canvas | ≤ 1,5 | ≤ 2 |
| 11 | первый кадр модели (своя метка) | ≤ 5 000 мс | ≤ 2 000 мс |

```python
# run: system
# Python 3 — [проверено] ворота F1 по готовому отчёту site_probe.py + статика import map
import sys
sys.path.insert(0, "../../scripts/3d")
from qa_pipeline import gate_check, importmap_check
EX = "09-web-runtime/examples/"
for name, val, lim, ok in gate_check(EX + "hero-lazy/probe/desktop_0/probe_quick.json", "desktop"):
    print("OK  " if ok else "FAIL", name, val, lim)
for page in ("hero-lazy", "camera-path-scroll", "shader-background"):
    print(page, [i["code"] for i in importmap_check(EX + page + "/index.html")])
assert [i["code"] for i in importmap_check(EX + "camera-path-scroll/index.html")] == []   # до правки волны 4 — ["importmap_min_core"]
```

Вывод: у hero-lazy (замер F1) 8 из 9 ворот десктопа OK, TBT 175 > 150; статика: hero-lazy — чисто (бандл esbuild),
`camera-path-scroll` и `shader-background` — `importmap_min_core` [проверено]; после правки волны 4 (ключ import map
`…/three.core.js` → `…/three.core.min.js`, аудит X П-67) — чисто; `qa_pipeline.py page`: shader-background — pass, camera-path-scroll —
9/9 ворот в 5 из 7 прогонов (TBT 93–158 мс у порога 150, 373,7 КБ вместо 532) [проверено: S1].

```bash
# Python 3 + Chromium — [проверено] живой прогон страницы с prefers-reduced-motion
python3 ../../scripts/3d/qa_pipeline.py page 09-web-runtime/examples/hero-lazy --reduced
```

Вывод: `pass` — LCP 36 мс (постер), 0 вызовов и 0 % движения в покое, 0 ошибок консоли (≈ 12 с) [проверено].

### 5.2. Результаты J/03 на демо F1 и F2

| страница | режим | вердикт | главное |
|---|---|---|---|
| hero-lazy | десктоп | fail | 8/9 ворот; TBT 172 мс > 150 (у F1 175) — воспроизведено; LCP 44 мс (IMG), 1 274 КБ, 10 вызовов |
| hero-lazy | reduce | pass | 0 вызовов, 0 % движения, LCP 36 мс |
| camera-path-scroll (F2) | десктоп | review | 9/9 ворот (LCP 72 мс, TBT 93, 532 КБ, 0 вызовов в покое); import map без переназначения ядра |

TBT 172–175 мс на почти пустой странице — это цена парсинга и компиляции three + GLB (F1: `compileAsync` не снимает долгие
задачи). Предел 150 мс недостижим для паттерна «постер → 3D после LCP» без дробления загрузки по кадрам; F1 предлагает
кандидатов (разбиение загрузки, именованные импорты) — `[спорно]` до замера.

### 5.3. Статика страницы

- import map: одна версия `three@x` у `three` и `three/addons/`; `three.module.min.js` с jsDelivr — только с ключом-URL
  `…/build/three.core.js → …/build/three.core.min.js` (F1 `09/01 §1.2`: без него 401 против 243 КБ);
- в консоли нет «Multiple instances of Three.js» (import map + бандл с three внутри);
- `extensionsUsed` GLB сверены с подключёнными декодерами (`glb_lint` → `decoders`; KTX2Loader, MeshoptDecoder, DRACOLoader) —
  сверка со страницей не автоматизирована `[не проверено]`;
- имена узлов после санитизации three уникальны: `Mug.001` рядом с `Mug001` даёт `Mug001_1`, `[hotspot] buy` занимает `hotspot_buy`
  — JS находит не тот узел; `preflight()` коллизию не видит, ловит `names_for_js()` I (`../02-blender-workflow/01 §8.2`, I/03);
  в three — список имён из `gltf_web_inspect.py`;
- drei `useGLTF` грузит модель загрузчиком three-stdlib 2.36.1, а не three r186: после `gltfpack -ce khr` падает (F2) — проверять
  GLB именно тем загрузчиком, который на странице.

### 5.4. Метки и время кадра

- Первый кадр модели — своя метка: `performance.mark('hero-first-frame')` после первого `renderer.render()` с моделью;
  `site_probe` меряет первый вызов отрисовки, а это PMREM окружения (F1). В hero-lazy — `window.__t.firstFrame`.
- Логика анимации (без отрисовки) — не больше половины бюджета кадра [V:Eq_rXOyOX0I W13:35–W14:39] (W13).
- Время кадра эффекта — `fx_probe.py` F2 (`99-raw/experiments/F2/00-tools/`): режим без vsync, `readPixels` в конце кадра, покой и
  прокрутка, доля изменившихся пикселей; ≥ 5 прогонов; пороги F2: ≤ 2 мс/кадр на Iris Xe при 1440×900, reduce → 0 вызовов,
  ΔE фона к hex ≤ 1.
- Не сделано: сравнение постера с первым 3D-кадром (ΔE/SSIM — ловит незапечённые материалы, A), LoAF/INP со скриптованными
  кликами (A) — `[не проверено]`; кандидаты в `site_probe.py` (A).

## 6. Ограничения стенда

Chromium headless с ANGLE на Intel Iris Xe; телефон — эмуляция Pixel 7 (UA, 412×915, DPR 2,625, CPU ×4, 1,6 Мбит/с); реальных
iPhone/Android нет — Safari iOS (нет `requestIdleCallback`), мобильные GPU, тепловой троттлинг и AR Quick Look не проверены (A, E,
F1 называют этот пробел); лимит видеопамяти вкладки iOS ≈ 200–400 МБ проверяется только на реальном iPhone, не эмулятором
[V:BH1R29YvLOk W44:35] (W13). Машина общая: время шумит, ≥ 3 прогона для загрузки, ≥ 5 для кадра.

## Частые ошибки

- Сдавать GLB по «валидатор 0 ошибок» — валидатор не видит процедур, цветового пространства, потерянных морфов (E).
- Сравнивать `.blend` со студией и GLB ассета в `gltf_diff` — ложная «поломка» (IoU 0,002).
- Разные тонмапперы в Blender и three при сравнении (AgX против Neutral) — ΔE 7–9 «из ниоткуда».
- Проверять анимацию только глазами по видео: турнтейбл, крутящийся назад, на коротком ролике незаметен; четверти — числом.
- Считать первый вызов отрисовки первым кадром модели (это PMREM).
- Мерить кадр `gl.finish()` или одним прогоном.
- `three.module.min.js` с CDN «для скорости» без переназначения ядра — наоборот, +204 КБ.
- Писать «работает на телефонах» по эмуляции.

## Чек-лист

- [ ] `qa_pipeline glb` без ERROR; предупреждения валидатора и `glb_lint` разобраны?
- [ ] `preflight()` без ERROR, WARN исправлены или объяснены?
- [ ] `gltf_diff` по копии «только ассет»: ΔE ≤ 3,5 и IoU ≥ 0,99 (или объяснено: стекло, анизотропия)?
- [ ] Брендовый материал: ΔE к hex ≤ 2 в паре Neutral ↔ `NeutralToneMapping`?
- [ ] Клипы, длительности, начало в 0, позы в 3–5 моментах, четверти турнтейбла — числом в three?
- [ ] `qa_pipeline page` десктоп и телефон (эмуляция): ворота F1 пройдены или отклонение объяснено (TBT)?
- [ ] reduce: 0 вызовов и 0 движения в покое?
- [ ] 0 ошибок консоли, нет «Multiple instances of Three.js», import map без ловушки min-ядра?
- [ ] Своя метка первого кадра модели есть и ≤ 2 с десктоп / ≤ 5 с телефон?
- [ ] В отчёте написано, что телефоны — эмуляция?

## Открытые вопросы и противоречия

- **TBT 150 мс десктопа** (F1 `09/05 §1.1`) против замеров hero-lazy 172–175 мс — порог или паттерн? `[спорно]`.
- **Демо F2 против правила F1**: `camera-path-scroll` и `shader-background` используют `three.module.min.js` без переназначения
  ядра — F1 прямо пишет «не использовать» (`09/01 §1.2`, таблица). Решено в волне 4: ключ `three.core.js` → `three.core.min.js`
  добавлен в import map обоих демо (аудит X П-67).
- **`gltf_diff` и подложка**: инструмент E рендерит всю видимую геометрию источника — это не ошибка кода, но ловушка
  использования; в README утилит стоит одна строка об этом (предложение оркестратору).
- **Вывернутое кольцо ракеты** (J/01): материалы `doubleSided: true` — кольцо видно в three, но освещено изнанкой; ΔE ракеты 3,52
  (граница) — вклад кольца не выделен `[не проверено]`.
- Пороги `gltf_diff` под bloom, AgX, тёмные сцены и стекло — не перекалиброваны (гипотеза E) `[не проверено]`.
- Постер ↔ первый 3D-кадр (ΔE/SSIM), LoAF/INP, сверка `extensionsUsed` со страницей — не автоматизированы.

## Источники

- [S1] E, `../08-export-gltf/04-validation-pitfalls-presets.md` §1–6, 2026; утилиты `gltf_check.py`, `gltf_diff.py`, `gltf_web_inspect.py`, `gltf_load_bench.py`; калибровка `99-raw/experiments/E/02-diff-baseline`.
- [S2] F1, `../09-web-runtime/05-performance-a11y-fallbacks.md` §1, §7 (`gate_check`), `01-threejs-core.md` §1.2 (ловушка min-ядра), демо `../09-web-runtime/examples/hero-lazy` с замерами, 2026.
- [S3] F2, `../09-web-runtime/02–04`, демо `camera-path-scroll`, `shader-background`, `99-raw/experiments/F2/00-tools/fx_probe.py`, 2026.
- [S4] A, `../01-web-3d-landscape/02 §8`, `../../scripts/3d/site_probe.py`, 2026 — ворота страницы, зонд.
- [S5] H, `../07-animation/03`, `99-raw/experiments/H/10-turntable` (варианты a–f), `_lib/anim_diff.py`, `three_probe.py`, 2026.
- [S6] D2, `../06-materials-lighting-render/03 §4–5`, `04-light-icons/sheets.py`, 2026 — пара Neutral, `view_hex`, белая печь, `sun_threshold`.
- [S7] Дайджест W3 `DQeP363Xmn4` (Lukas Stockner, Principled v2, тест белого фона) — через `_index-W3.md`.
- [S8] Эксперимент J/03 `99-raw/experiments/J/03-qa-pipeline` — прогоны и найденные ловушки склейки.
