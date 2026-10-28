# 17 · `KHR_materials_variants` из Blender 5.2.2: расцветки одним GLB — экспорт, упаковка, переключение в three r186

Испытание 15-showcase · рецепт по итогам фаз 1–2 · агент RC, 26.09.2026 · Blender 5.2.2 LTS (glTF-IO 5.2.40), gltf-transform 4.5.0,
нативный gltfpack 1.2, валидатор Khronos 2.0.0-dev.3.10, three 0.186.0, Chromium headless · доказательства — дорожка KB (клавиатура «Ё»):
проба на 3 и 12 колпачках `examples/17-khr-materials-variants/src/`, полная модель — `examples/17-khr-materials-variants/src/export_web.py`, страница C — `examples/15-hybrid-blender-code/src/model_c.js`;
рецепт-кандидат — `15-showcase/keyboard/README.md` · проверки RC — `99-raw/notes/trial/RC-checks/rc_glb_checks.py` · пробел базы
закрыт: README «Что не покрыто», выжимка `15-showcase/_shared/digests/03-web-delivery.md` A.1–A.2 п. 15.

## Выжимка рецепта

1. **Работает при трёх условиях** [проверено: KB/04-variants, KB/06-export; исходник аддона — RC]:
   (1) в процессе Blender включена настройка аддона `KHR_materials_variants_ui = True` — без неё `primitives.py:336` молча не пишет
   расширение (в `-b --factory-startup` настройка живёт только в памяти процесса — ставить в каждом скрипте);
   (2) варианты — в `bpy.data.scenes[0].gltf2_KHR_materials_variants_variants` (именно `scenes[0]`, не `context.scene`), у меша —
   `gltf2_variant_mesh_data` (слот, материал, индексы вариантов) + `gltf2_variant_default_materials`;
   (3) постобработка без склейки примитивов: `gltf-transform optimize … --join false`; нативный gltfpack `-cc` варианты держит, имена
   и extras — с `-kn -ke`, материалы не сливать — `-km`.
2. **Виновник поломки — только `join`**: на 12 колпачках `optimize` по умолчанию склеил 7 примитивов в 3 и выбросил привязки у двух —
   в «Графите» сменилась только Ё; `--flatten false` и `--palette false` по отдельности не спасают, `--join false` — все 7 целы
   [проверено: KB `04-variants/post_flags_report.json`, `three_variants_report.json`].
3. **Привязка — на меш**: связанные дубликаты (инстансы) получают варианты все сразу; 13 прототипов на 67 колпачков [проверено: KB].
4. **Полная модель: 26 примитивов, 19 с вариантами — и в сыром GLB, и после упаковки** (десктоп KTX2, телефон WebP): упаковка не
   потеряла ни одной привязки; 7 без вариантов — детали без расцветки (латунная плита и полоса, силиконовые ножки, шток и проволока
   стабилизаторов, плата, порт USB) [проверено: RC-checks `rc_glb_checks.py`; KB `06-export/out/export_report.json`].
5. **three r186 сам не переключает**: расширение — в `gltf.userData.gltfExtensions`, у меша — в `mesh.userData.gltfExtensions`;
   переключение — `parser.getDependency('material', mapping.material)` + `parser.assignFinalMaterial(mesh)`, как в примере
   `webgl_loader_gltf_variants`; загрузка 20–111 мс, 0 ошибок консоли, цвет в кадре меняется (мятная Ё «Графита» `#77D9B7` при
   паспорте `#7BD3B4`) [проверено: KB `04-variants/run_three_test.py`].
6. **`InstancedMesh` из общих мешей** — перенести отображения вариантов с исходного меша на экземплярный
   (`im.userData.gltfExtensions = g.ext`) и патчить шейдер каждого материала варианта (`patchUV` внутри `getMat`,
   `customProgramCacheKey`): материал варианта приходит из `getDependency` без патча [проверено: KB `model_c.js` — так работает на
   странице C; вариант без патча не снимался].
7. **Цена**: вариант = целый материал; у колпачков — свой полноцветный атлас надписей на расцветку (KTX2 ETC1S 2048×1536 — 29–33 КБ,
   WebP 512 — ≈ 5 КБ; итог KB3 — WebP 2048 и на десктопе, открытый вопрос 4); материалы и текстуры варианта грузятся по первому требованию
   (`getDependency` кэширует) [проверено: KB README].
8. **Валидатор Khronos — 0 ошибок у всех 11 проб и у полной модели**; предупреждение `image/ktx2` у файлов gltfpack — ложное [проверено: KB].
9. Обход без стандарта — менять `material.color` по имени из JS: 0 КБ, но расцветок не увидят model-viewer (`variant-name`) и другие
   просмотрщики; drei `useGLTF` (three-stdlib) варианты не знает [проверено: KB NOTES; документация: выжимка 03 A.1 п. 15].

## 1. Бриф-пример и границы

«Три расцветки клавиатуры — “Снег”, “Графит”, “Лён”: чипы под живым 3D, смена мгновенная, фон раздела плавно меняется под расцветку;
одна GLB на все расцветки» (`15-showcase/keyboard/art-direction.md §7, §11`).

| годится | не годится → куда |
|---|---|
| конфигуратор: 2–10 вариантов материалов у тех же мешей | варианты формы (другая геометрия) → разные узлы/GLB, видимость из JS |
| стандарт нужен вне своей страницы (model-viewer, чужие просмотрщики, AR) | только своя страница и 1–2 цвета → `material.color` из JS (0 КБ) |
| текстуры вариантов дешёвые (атлас на вариант) | тяжёлые PBR-наборы на вариант → грузить по требованию и считать вес каждого |

## 2. Экспорт: условия 1 и 2 (Blender 5.2.2)

```python
# [проверено: 12-recipes/examples/17-khr-materials-variants/src/variants_export.py, запуск KB-variants 25.09 19:24] Blender 5.2.2 — отрывок [не исполняется] # run: skip
prefs = bpy.context.preferences.addons["io_scene_gltf2"].preferences
before = {"KHR_materials_variants_ui": prefs.KHR_materials_variants_ui,
          "scene_has_prop": "gltf2_KHR_materials_variants_variants" in bpy.types.Scene.bl_rna.properties}
prefs.KHR_materials_variants_ui = True                       # update-колбэк регистрирует типы variant_register()
# … материалы вариантов mats[(роль, расцветка)]
sc0 = bpy.data.scenes[0]                                     # аддон читает именно scenes[0], не context.scene
for i, cwn in enumerate(CWS):
    v = sc0.gltf2_KHR_materials_variants_variants.add()
    v.variant_idx = i
    v.name = cwn
# … для каждого колпачка: меш me, объект ob
    me.materials.append(mats[(role, "snow")])               # текущий материал = вариант по умолчанию
    for i, cwn in enumerate(CWS):
        d = me.gltf2_variant_mesh_data.add()
        d.material_slot_index = 0
        d.material = mats[(role, cwn)]
        vv = d.variants.add()
        vv.variant.variant_idx = i
    dm = me.gltf2_variant_default_materials.add()
    dm.material_slot_index = 0
    dm.default_material = mats[(role, "snow")]
```

До включения настройки у сцены **нет даже свойства** `gltf2_KHR_materials_variants_variants` (`pref_before: scene_has_prop false` →
`pref_after: true`, `variants_export_report.json`): типы регистрирует колбэк настройки. В исходнике аддона: `__init__.py:2214`
(`KHR_materials_variants_ui`, по умолчанию `False`, `update=gltf_variant_ui_update`), `blender/exp/primitives.py:336–340` (выход, если
настройка выключена или у `scenes[0]` нет вариантов) [проверено: RC — чтение исходника glTF-IO 5.2.40 в `blender-5.2.2-linux-x64/5.2/scripts/addons_core/io_scene_gltf2/`].

Для многослотовых мешей (корпус: металл + фаска) — привязка на каждый слот:

```python
# [проверено: 12-recipes/examples/17-khr-materials-variants/src/export_web.py, запуск KB2-export 25.09 20:30] Blender 5.2.2 — отрывок [не исполняется] # run: skip
def variants(me, slot_roles):
    """slot_roles: {индекс слота: ключ роли MW} → привязки вариантов (по умолчанию — «Снег»)."""
    me.gltf2_variant_mesh_data.clear()
    me.gltf2_variant_default_materials.clear()
    for slot, role in slot_roles.items():
        for i, cw in enumerate(CWS):
            d = me.gltf2_variant_mesh_data.add()
            d.material_slot_index = slot
            d.material = MW[(role, cw)]
            d.variants.add().variant.variant_idx = i
        dm = me.gltf2_variant_default_materials.add()
        dm.material_slot_index = slot
        dm.default_material = MW[(role, "snow")]
# … variants(me, {0: "case", 1: "chamfer"}) для Case_Top/Case_Bottom; экспорт пресетом E/24 static_hero по коллекции
```

## 3. Условие 3: что переживает постобработка

| файл (проба) | постобработка | примитивов | без привязок | итог в three | доказательство |
|---|---|---|---|---|---|
| `variants_raw.glb` (3 колпачка) | — (экспорт) | 3 | 0 | 3 из 3 меняются, загрузка 111 мс | `post_report.json`, `three_variants_report.json` |
| `v_opt_default.glb` | `optimize` по умолчанию | 3 | 0 | привязки целы (склеивать было нечего) | `post_report.txt` |
| `v12_opt_default.glb` (12 колпачков) | `optimize` по умолчанию | 3 (из 7) | 2 | в «Графите» сменилась только Ё | `three_variants_report.json` |
| `v12_flatoff` / `v12_paloff` | `--flatten false` / `--palette false` | 3 | 2 | ломается так же | `post_flags_report.json` |
| `v12_joinoff`, `v12_joinflatoff` | `--join false` (± `--flatten false`) | 7 | 0 | 12 из 12 | там же |
| `v_pack_cc` / `v12_pack_cc` | `gltfpack -cc` | меши слиты, имена потеряны | 0 | 10 из 10 мешей с привязками | `post_report.txt` |
| `v_pack_kn` / `v12_pack_kn` | `gltfpack -cc -kn -ke` | узлы `Key_*` по имени | 0 | 12 из 12 | там же |
| `v_pack_tw` | `gltfpack -cc -tw` (WebP) | — | 0 | варианты целы | там же |
| `kb_desk.glb` (полная модель) | `gltfpack -cc -tc -tq 8 -kn -ke -km -vtf -vpf` (KTX2) | 26 | 7 (без расцветки по замыслу) | 19 из 19 | RC-checks |
| `kb_mob.glb` | `gltfpack -cc -tw -tl 512 -kn -ke -km -vtf -vpf` (WebP) | 26 | 7 | 19 из 19 | RC-checks |

Проверка кодом (без three и сети — разбор JSON-чанка GLB), сколько примитивов несут варианты до и после упаковки.
Блок ждёт три модели одного предмета — сырой экспорт («kb_web_raw.glb», его пишет `examples/17-khr-materials-variants/src/export_web.py`) и две после
постобработки §3 («kb_desk.glb», «kb_mob.glb»); в базе их нет — подставьте в `KB` папку с моделями своего проекта, а числа в `assert`
(26 примитивов, 19 с вариантами) замените своими.

```python
# run: skip [не исполняется] — блоку нужны три модели проекта: сырой экспорт и две после постобработки
# Python 3 — [проверено] только чтение GLB
import json
import struct

KB = "<папка с моделями проекта>"


def gj(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])


for f in ("kb_web_raw.glb", "kb_desk.glb", "kb_mob.glb"):
    j = gj(f"{KB}/{f}")
    mats = j["materials"]
    prims = [(p.get("material"), bool(p.get("extensions", {}).get("KHR_materials_variants")))
             for m in j["meshes"] for p in m["primitives"]]
    without = sorted({mats[m]["name"] for m, v in prims if not v and m is not None})
    names = [v["name"] for v in j["extensions"]["KHR_materials_variants"]["variants"]]
    print(f, len(prims), "примитивов,", sum(v for _, v in prims), "с вариантами", names, "без:", without)
    assert (len(prims), sum(v for _, v in prims)) == (26, 19)
```

## 4. three r186: переключение

Проба (все файлы §3 подряд, цвет пикселя в центре каждого колпачка):

```js
// [проверено: 12-recipes/examples/17-khr-materials-variants/src/test.js, run_three_test.py 25.09 19:26] three r186 — отрывок
async function selectVariant(root, parser, ext, name) {
  const idx = ext.variants.findIndex((v) => v.name === name);
  const jobs = [];
  root.traverse((o) => {
    if (!o.isMesh || !o.userData.gltfExtensions) return;
    const def = o.userData.gltfExtensions.KHR_materials_variants;
    if (!def) return;
    if (!o.userData.originalMaterial) o.userData.originalMaterial = o.material;
    const m = def.mappings.find((mp) => mp.variants.includes(idx));
    jobs.push((async () => {
      if (m) { o.material = await parser.getDependency('material', m.material); parser.assignFinalMaterial(o); }
      else o.material = o.userData.originalMaterial;
    })());
  });
  await Promise.all(jobs);
}
```

Страница C (колпачки уже собраны в `InstancedMesh`, у каждого — отображения исходного меша; материал колпачка патчится под атлас):

```js
// [проверено: 12-recipes/examples/15-hybrid-blender-code/src/model_c.js, buildModelC() → setColorway] three r186 — отрывок
  const getMat = async (idx, keycap) => {
    const key = `${idx}`;
    if (!mats.has(key)) mats.set(key, parser.getDependency('material', idx).then((m) => (keycap ? patchUV(m) : m)));
    return mats.get(key);
  };
    async setColorway(cw) {
      const vi = CWS.indexOf(cw);
      curCw = cw;
      await Promise.all(withVariants.map(async (m) => {
        const maps = m.userData.gltfExtensions.KHR_materials_variants.mappings;
        const mp = maps.find((x) => x.variants.includes(vi));
        if (!mp) return;
        m.material = await getMat(mp.material, !!m.userData.isKeycap);
        if (m === yoIm) yoMat = null;
      }));
    },
```

Индекс варианта — по порядку `CWS` (`snow, graphite, linen`), а не по имени: в полной модели имена вариантов — «Снег», «Графит», «Лён»
(`kbp.COLORWAYS[cw]["title"]`, модуль — `examples/13-wow-light-hero/src/kbp.py`). Надёжнее — искать индекс по имени из `gltf.userData.gltfExtensions.KHR_materials_variants.variants`
(как в пробе) [проверено: KB — оба пути работают на своих файлах].

## 5. Числа

| величина | значение | доказательство |
|---|---|---|
| проба: 3 колпачка × 3 варианта | 9 материалов, 3 текстуры, 80,6 КБ сырой GLB → 19,5–24,1 КБ после упаковки | `post_report.txt` |
| полная модель: узлы / меши / примитивы / материалы | 151 / 24 / 26 (19 с вариантами) / 24 | `export_report.json`; RC-checks |
| сырой → десктоп KTX2 → телефон WebP | 1 279,6 КБ → 340,0 КБ (176,2 br) → 254,9 КБ (98,0 br) | KB README; RC-checks |
| атлас надписей на расцветку | KTX2 ETC1S 2048×1536 — 29–33 КБ; UASTC — файл ×1,5 (510,5 КБ вместо 340) | KB `rules.md`; RC-checks |
| three: загрузка GLB с вариантами | 20–111 мс, 0 ошибок консоли | `three_variants_report.json` |
| экспорт + упаковка + валидатор | 4 с Blender + 5 с `pack.sh` | KB `HANDOFF-2.md §3` |

## Частые ошибки

| ошибка | симптом | исправление | где поймано |
|---|---|---|---|
| не включили `KHR_materials_variants_ui` в процессе | расширения нет, ошибок нет; у сцены нет свойства вариантов | `prefs.KHR_materials_variants_ui = True` до создания данных | KB; исходник аддона |
| варианты записаны в `context.scene`, а она не первая | экспорт без вариантов (аддон читает `scenes[0]`) | `bpy.data.scenes[0]` | KB; исходник `primitives.py:339` |
| `optimize` по умолчанию | меняется одна клавиша из многих | `--join false` | KB |
| gltfpack без `-kn -ke` | узлы без имён, страница не находит `Key_*` и extras | `-kn -ke` (+ `-km`, `-vpf`) | KB |
| `InstancedMesh` без отображений исходного меша | экземплярный меш не попадает в список переключаемых — цвет не меняется (по логике кода) | перенести `userData.gltfExtensions` с исходного меша | KB `model_c.js` |
| свой патч шейдера только на исходный материал | в другой расцветке UV ячейки атласа не сдвинуты — надписи не на своих клавишах (по логике кода, не снималось) | патч на каждый материал варианта, `customProgramCacheKey` | KB `model_c.js` |
| индекс варианта «по порядку» при других именах | не та расцветка | индекс по имени из `variants` | RC (по коду KB) |

## Чек-лист

- [ ] `KHR_materials_variants_ui = True` в каждом фоновом скрипте экспорта; варианты — в `bpy.data.scenes[0]`?
- [ ] Привязки на каждый слот меша, умолчание задано; у инстансов — на общем меше?
- [ ] Постобработка без `join` (`--join false` или gltfpack `-kn -ke -km`); примитивов с вариантами столько же, сколько в сыром GLB?
- [ ] Детали без расцветки — осознанно без привязок (записаны в README)?
- [ ] three: `getDependency` + `assignFinalMaterial`, индекс по имени варианта; патчи шейдера — на все материалы варианта?
- [ ] Валидатор 0 ошибок; проверено переключение всех вариантов на кадре?

## Открытые вопросы

1. model-viewer (`variant-name`) и Quick Look / Scene Viewer с этим GLB не проверялись [не проверено].
2. `KHR_materials_variants` вместе с `KHR_texture_basisu`: в three работает (страница C фазы 2, KB2; с KB3 страница — на WebP), в чужих
   просмотрщиках без транскодера — нет [не проверено].
3. Анимация перехода между вариантами (кросс-фейд материала) — не делалась; сейчас смена мгновенная, плавно меняется только фон раздела (CSS).
4. Кадры судьи раздела «Три цвета» сняты KB3 у всех трёх вариантов: `15-showcase/keyboard/judge/{a-code,b-blender,c-hybrid}__colorways-{snow,graphite,linen}.png`
   (в голосование — «Графит», пара k-colors-ac); повтор ворот страницы C после правок (KB3, тишина): `gate_check` 9/9 · 9/9 · 6/6, LCP 52 / 548 мс,
   TBT 0, `motion_check` L1 — 79 PASS, 0 FAIL, `marketing_audit` — 0 блокеров [проверено: KB `HANDOFF-3.md §2, §9`]. С KB3 атлас надписей
   страницы C — WebP и на десктопе (159,0 КБ br против 176,2 у KTX2 ETC1S и 388,4 вместе с транскодером; ETC1S сдвигал почти-серые PBT
   в сиреневый — `KB/12-metrics/kb3_atlas_webp_vs_ktx2.json`); варианты в упакованном WebP-файле RC-checks заново не считал — переключение
   видно на кадрах трёх расцветок C. Слепое голосование (заказчик, 26.09): расцветка «Графит» A ↔ C — ничья (`15-showcase/vote/results.md`).

## Ссылки

Рецепт-кандидат — `15-showcase/keyboard/README.md` («три условия»); опыты — `examples/17-khr-materials-variants/src/`, журнал
`KB/rules.md`, `KB/NOTES.md`; пример three — `99-raw/cache/three-r186-examples/webgl_loader_gltf_variants.html`; постобработка базы —
`../08-export-gltf/04-validation-pitfalls-presets.md §7`; гибрид — `15-hybrid-blender-code.md`.
