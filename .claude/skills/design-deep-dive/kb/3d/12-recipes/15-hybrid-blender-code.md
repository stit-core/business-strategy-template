# 15 · Гибрид Blender + код: меш и запечённый AO из Blender, всё живое — кодом

Испытание 15-showcase · рецепт по итогам фаз 1–2 · агент RC, 26.09.2026 · Blender 5.2.2 (glTF-IO 5.2.40), gltf-transform 4.5.0,
нативный gltfpack 1.2 (BasisU внутри), three 0.186.0, Chromium headless / Iris Xe · доказательства — «Звено» C (дорожка Z: ассет,
`examples/15-hybrid-blender-code/src/zweb_all.py`; дорожка CD: гибридный крюк `15-showcase/_shared/code3d/`), клавиатура «Ё» C (дорожка KB:
`examples/17-khr-materials-variants/src/export_web.py`, `examples/15-hybrid-blender-code/src/model_c.js`) · проверки RC — `99-raw/notes/trial/RC-checks/`.

## Выжимка рецепта

1. **Контракт GLB = пустышки с именами модулей кода**: узел-пустышка `base | j1 | j2 | l1 | j3 | l2 | wrist | grip` (или extras
   `zveno_module`), точка — шарнир, оси three (Y вверх), метры сцены кода; геометрия — дети. Код **отбрасывает TRS пустышки** (позу ставит
   кинематика) и **сохраняет TRS детей** (там сидит квантование) — GLB можно выгружать в любой позе [проверено: CD/11; RC-checks — 8 из 8
   пустышек пережили `optimize --flatten false --join false`].
2. **Роли материалов — по extras `role` или имени** (`led, decal, ring, shell, cap, alu, steel, rubber, copper, pcb, dark`): кольцо и
   светодиод — свой экземпляр на модуль (вспышка горит у одного), наклейки — без тени и не в зеркале; исходный материал GLB не мутировать
   (клон на ключ) [проверено: CD/11; 6 из 6 ролей J2 найдены по именам Z].
3. **AO — запечь в Blender одним атласом на изделие** (UV «AO» = TEXCOORD_1, Cycles 64 спп + денойз композитором), **модули на время
   запекания развести** (позы и разнос в коде меняют соседей — AO только своё), дальность 0,08 м (0,25 м — швы в three чернели);
   N8AO в гибриде по умолчанию выключен [проверено: Z `zweb_all.py`, `rules.md`].
4. **Анизотропию крышек и труб — в GLB** (`KHR_materials_anisotropy`): без неё точёные крышки в three — «чёрные динамики» [проверено: Z NOTES 21:14].
5. **Постобработка без слияния**: `gltf-transform optimize … --flatten false --join false --palette false --simplify false` или
   `gltfpack -cc -kn -ke -km`; после `optimize` AO уходит с texCoord 1 на 0 (неиспользуемый UV0 вырезан) — законно, но код, который
   ждёт `uv1`, сломается; gltfpack оставляет texCoord 1 [проверено: RC-checks `rc_glb_checks.py`].
6. **WebP по умолчанию, KTX2 — когда упираемся в память GPU** (итог ночи 26.09; прежняя позиция фазы 2 — «KTX2 десктопу, WebP 512
   телефону»): по сети KTX2 проигрывает — крюк v2 на GLB «Звена» (один атлас 2048²) +301 КБ br (+38 %: WebP 798 против KTX2 1 099 КБ br,
   транскодер basis 213 КБ br), первый кадр +18…25 мс, выигрыш — только память GPU 28,8 → 7,5 МБ (−74 %) и нет длинной задачи 53–68 мс;
   атлас надписей клавиатуры в ETC1S сдвигает почти-серые PBT в сиреневый (и при `-tq 10`), с декодером 212 КБ br — итого 388 КБ br против
   159 у WebP 2048 (−229 КБ br). KTX2 (ETC1S) делает нативный gltfpack (`-tc`, BasisU внутри — `toktx` не нужен), в крюке — флагом
   `build.sh --ktx2`; включать при ≥ 2 атласах 2048² или упоре в память; UASTC — цвет верный, но файл ×2 (347,7 КБ br); `-vpf` — без
   узлов деквантования (151 узел, иначе 296) [проверено: CD `out/hook2/q/summary.json`, CD `HANDOFF-3.md §3–4`; KB
   `12-metrics/kb3_atlas_webp_vs_ktx2.json`, `06-export/pack.sh`; RC-checks].
7. **Повторы — инстансами glTF + атлас по extras узла**: 67 колпачков = 13 общих мешей → `InstancedMesh` с атрибутом экземпляра `iUV`
   из extras `kb_uv4`, UV прототипа — в пустую ячейку атласа; 14 вызовов на 68 колпачков, в чужом просмотрщике колпачки чистые [проверено: KB].
8. **Страница C**: постер (кадр Cycles) = LCP; three первого экрана — после `load` в простое, three раздела ниже первого экрана — по
   намерению (первое нажатие, касание, клик или остановка ≥ 2,5 с на разделе; «когда раздел подходит к экрану» давало длинные кадры
   прокрутки 4,2 % — EG-PERF-01); 0 кадров в покое, reduce → кадры и three не грузится, один WebGL-контекст на страницу. Итог ворот в
   тишине: клавиатура C (KB3) — `gate_check` 9/9 · 9/9 · 6/6, LCP 52 / 548 мс, TBT 0, `motion_check` L1 без нарушений, длинные кадры
   прокрутки 843 мс → 0; «Звено» C (Z3) — 0 FAIL, LCP 56 / 660 мс, TBT 56 / 146 мс, `motion_check` L2 0/0/0 [проверено: KB `HANDOFF-3.md §9`,
   `12-metrics/kb3_loaf_probe.json`; Z `HANDOFF-3.md §5`].
9. **«Звено» C в бюджете**: десктоп 1273 КБ / 87 903 треуг. / ≈ 66 вызовов, телефон 705 КБ / 47 883 / ≈ 57, валидатор 0/0; на странице
   (Z3) — основной GLB с касательными + начинка отдельным GLB в простое: 759 + 495 КБ br десктоп, ≈ 365 + 210 телефон — 3D 1 256 / 575 КБ br
   при лимитах 1 536 / 820 [проверено: `15-showcase/zveno/README.md` (C)]; кадр
   гибрида (J2 из GLB, N8AO выкл.) 2,77 мс против 4,32 у кода — запечённый AO дешевле живого [проверено: Z `out/c_web*/…_bake.json`; CD/15].
10. **Цена гибрида поверх кода**: +25,8 КБ br JS (чанк загрузчика 19,9 + 5,9 в чанке three; страница A их не платит — define
    `__CD_GLB__`) + GLB 0,26–1,27 МБ [проверено: CD/19; KB `numbers.json`].
11. **Гибрид несёт геометрию и AO Blender, но не свет Cycles**: у клавиатуры C после поправки экспозиции средняя ΔL* к кадру Blender
    ≈ ±1, но медиана |ΔL*| 5–14 — распределение света другое, металл холоднее [проверено: KB `12-metrics/abc_after_fix.json`].
12. **Когда окупается** — решают слепые пары гибрид ↔ код: доля побед ≥ 0,75 → Blender обязателен, 0,4–0,75 → по бюджету, < 0,4 → не
    нужен (`../11-evaluation-qa/06-wow-pairwise-3d.md`); кадры судьи C сняты в тех же состояниях, что A и B («Звено» — 7 состояний, вид p3,
    + запись `c-hybrid__ik-10s.webm`; клавиатура — 9 кадров + `c-hybrid__typing-10s.webm`). Итог слепого голосования (заказчик, 26.09,
    1 судья): доля побед гибрида над кодом **0,40** по 5 парам → «по бюджету» (граница); «Звено» C проиграл по ремеслу и A, и B (главный
    кадр, разборка), в движении B = C; клавиатура: A = C по кадрам, в записи набора C > A и C > B, по кадрам набора B > C
    (`15-showcase/vote/results.md`, блок VOTE `15-showcase/VERDICT.md`). **Вживую** (≈ 07:05, тот же судья прошёл живые страницы)
    заказчик выбрал гибрид C во всех трёх предметах («Звено», клавиатура, «Сдано»-фонарик; Velmora — равны): по кадрам гибрид уступает
    B в ремесле, его ценность — в живой странице (ответ на ввод + модель и материал Blender) — `15-showcase/vote/live-assessment.md`,
    правило 102 корневого README.

## 1. Бриф-пример и границы

«Запуск манипулятора (L2): всё живое как у “код v3” — IK за курсором, сборка по прокрутке, вспышка фиксации, скан сустава; но модули —
детальные, с крепежом, швами, маркировкой и начинкой из Blender, стыки — с запечённым AO» (`15-showcase/zveno/README.md`, вариант C).

| гибрид окупается | не окупается → куда |
|---|---|
| продукт с CAD-деталью (крепёж, рифление, начинка), статичные стыки, модули движутся только трансформами | интерактива нет → предрендер (рецепт 13, секвенции 08) |
| вес допускает +0,3–1,3 МБ GLB и +26 КБ br JS | форма задаётся правилом, < 30 уникальных деталей → код (рецепт 14) |
| нужен стандарт вариантов (расцветки в чужих просмотрщиках) | нужен свет уровня Cycles в живом кадре → только запекание света (lightMap, E/21) — в испытании не делалось |

## 2. Контракт GLB (что ждёт код)

| что | требование | почему | доказательство |
|---|---|---|---|
| узлы модулей | пустышка с именем модуля кода (или extras `zveno_module`); меши — её дети | код ставит пустышке матрицу `T(разнос)·шарнир·R` | `_shared/code3d/README.md` |
| точка и оси | точка пустышки = шарнир; оси three (экспорт glTF +Y); метры сцены кода (у «Звена» ×2,7 к паспорту страницы) | подмена 1:1 процедурного модуля | Z `rules.md` («реальный масштаб» — уточнение) |
| меш на самом узле модуля | допустимо с предупреждением: мировой TRS сохраняется, модуль должен лежать в начале координат | квантование gltf-transform сидит в TRS меша (J2: масштаб 0,2575) — сброс сломал бы масштаб | CD `rules.md` |
| начинка | узел `j3_inner` (extras `zveno_inner`), дети-слои с extras `spread` (м вдоль X), `spin` (доля угла ротора) | станции «скан» и «внутри» | `zweb_all.py` |
| реквизит | узел `cable` (extras `zveno_prop: 'cable'`) ставится мировой матрицей | процедурный кабель выключается | там же |
| роли материалов | extras `role` или имя по правилам крюка | свет по сюжету и скан по ролям | `glb-modules.js` |
| светодиод кольца | emissive + `KHR_materials_emissive_strength` | вспышка × (1 + 6·вспышка) от базовой силы GLB | README крюка |
| AO | `occlusionTexture` (любой `texCoord`) | N8AO выключен | README крюка |
| адресуемые узлы клавиатуры | `Key_<id>` с extras `kb_id, kb_code, kb_row, kb_w, kb_role, kb_l1, kb_l2, kb_uv4`; слои разборки — узлы `L_keycaps, L_switches, L_stabs, Plate, PCB, Weight`; параметры разборки — extras `KB_root` | ввод по `event.code`, разборка по нормали деки | KB `export_web.py`; RC-checks (68 узлов, extras целы) |

## 3. Blender: веб-режим → слияние по модулям → атлас AO → запекание → Occlusion → экспорт

Один `build(P)` в двух режимах (рендер: 256/192/96 сегментов, начинка полностью; веб: 48/40/24; телефон `webl`: 32/24/16, начинка ⅕,
без мелких винтов). Слияние: детали модуля → `<модуль>_mesh`, наклейки → `<модуль>_decal` (без AO), материалы общие — вызовов не
больше, чем материалов в меше [проверено: Z `HANDOFF-2.md §2`].

```python
# [проверено: 12-recipes/examples/15-hybrid-blender-code/src/zweb_all.py, запуск run_c_export.sh 25.09 21:30] Blender 5.2.2 — отрывок [не исполняется] # run: skip
# --- разнести модули, слои и кабель в пространстве на время запекания (AO — только своё)
for e in movers:
    mw = e.matrix_world.copy(); e.parent = None; e.matrix_world = mw
for i, e in enumerate(movers):
    e.matrix_world = Matrix.Translation((6.0 * (i + 1), 0.0, 0.0))
# … запекание AO (Cycles): активная нода картинки в КАЖДОМ материале запекаемых мешей
w = bpy.data.worlds.new("bakeW"); sc.world = w
w.light_settings.distance = AO_DIST
img = bpy.data.images.new(f"{NAME}_ao", SIZE, SIZE, alpha=False, float_buffer=True)
img.colorspace_settings.name = "Non-Color"
# …
r = bpy.ops.object.bake(type="AO", margin=6, use_clear=True)
assert "FINISHED" in r, r
# … денойз композитором (вид Raw), затем AO → «glTF Material Output».Occlusion (texCoord 1 = UV «AO»)
from io_scene_gltf2.blender.com.material_helpers import create_settings_group, get_gltf_node_name  # noqa: E402
gname = get_gltf_node_name()
grp = bpy.data.node_groups.get(gname) or create_settings_group(gname)
for m in mats:
    nt = m.node_tree
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "AO"
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = ao_img
    nt.links.new(uvn.outputs["UV"], tn.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tn.outputs["Color"], sep.inputs["Color"])
    gn = nt.nodes.new("ShaderNodeGroup"); gn.node_tree = grp
    nt.links.new(sep.outputs["Red"], gn.inputs["Occlusion"])
```

| шаг | «Звено» C десктоп (`web`) | телефон (`webl`) | доказательство |
|---|---|---|---|
| треугольники (начинка) | 87 903 (24 072) | 47 883 (11 444) | `Z/out/c_web/zveno_bake.json`, `c_webl/zveno-low_bake.json` |
| атлас AO, запекание + денойз | 2048², 23,97 + 2,09 с | 1024², 6,38 + 0,64 с | там же |
| вызовов по оценке (материалы в мешах) | 66 | 57 | там же |
| сырой GLB → после `optimize` | 5 660 → 1 273 КБ | 2 687 → 705 КБ | там же; `c-hybrid/assets/` |
| KTX2-вариант (gltfpack `-tc`) | 1 340 КБ | — | `Z/out/c_web/zveno_ktx2.glb` |

## 4. Экспорт и сжатие

```bash
# run: skip — [проверено] постобработка без слияния
T=$DDD_HOME
export PATH="$T/bin/KTX-Software-4.4.2-Linux-x86_64/bin:$T/bin/gltfpack-1.2:$PATH"
cd $T/node && npx --no-install gltf-transform optimize zveno_raw.glb zveno.glb --compress meshopt --texture-compress webp \
  --flatten false --join false --palette false --simplify false                   # «Звено»: узлы модулей и материалы по ролям целы
gltfpack -i kb_web_raw.glb -o kb_desk.glb -cc -tw -kn -ke -km -vtf -vpf             # клавиатура, десктоп (KB3): WebP, атлас 2048
gltfpack -i kb_web_raw.glb -o kb_mob.glb -cc -tw -tl 512 -kn -ke -km -vtf -vpf -si 0.4   # телефон: WebP ≤ 512, 107 → 43 тыс. треуг.
gltfpack -i kb_web_raw.glb -o kb_desk_ktx2.glb -cc -tc -tq 8 -kn -ke -km -vtf -vpf  # для сравнения (KB2): KTX2 ETC1S — сиреневый сдвиг серых
node $T/node/validate.mjs $PWD/kb_desk.glb                                          # валидатор Khronos: 0 ошибок
```

| флаг | зачем | что будет без него | доказательство |
|---|---|---|---|
| `--flatten false --join false` | узлы модулей и слои разборки остаются адресуемыми | части склеены, имена `Mesh016`, модуль не найти | E/24; Z, KB |
| `--palette false` | материалы по ролям не сливаются в `PaletteMaterial` | роли крюка и варианты материалов теряются | выжимка `03-web-delivery.md §0 п. 8`; Z |
| `-kn -ke` (gltfpack) | имена узлов и extras (`kb_uv4`, `kb_code`) | имена и extras потеряны | KB; RC-checks |
| `-km` | материалы не сливаются (варианты, роли) | слияние материалов | KB `pack.sh` |
| `-vtf` | UV без квантования (страница сдвигает UV на ячейку атласа) | сдвиг ячейки в квантованных UV | KB `pack.sh` |
| `-vpf` | позиции float — без узлов деквантования (страница ищет узлы по имени) | 296 узлов вместо 151; цена `-vpf` — +9 КБ к файлу | KB `rules.md`; RC-checks |
| `-tc` (нативный gltfpack) | KTX2 ETC1S — атлас 2048×1536 29–33 КБ | UASTC — файл ×1,5 (510 против 340 КБ) | KB `rules.md`; `kb_desk_uastc.glb` |

KTX2 против WebP: KTX2 остаётся сжатым в памяти GPU, но требует транскодер basis со своего домена (у клавиатуры `decoders/basis`
571 КБ на диске, 212 КБ br; крюк v2 «Звена» — 213 КБ br); замер CD3 на GLB «Звена» (тишина, `CD/out/hook2/q/summary.json`): WebP —
798 КБ br сети / 28,8 МБ памяти GPU / первый кадр 323 мс, KTX2 — 1 099 / 7,5 / 348, без начинки в первом экране — 679 (+121 после) / 309 мс.
Итог ночи: WebP по умолчанию у обоих гибридов (Z3, KB3; оркестратор подтвердил 05:30), KTX2 — при упоре в память GPU (≥ 2 атласа 2048²);
на медленной сети телефону — WebP (F1 `../09-web-runtime/06` §3). У «Звена» KTX2-файл больше WebP (1 340 против 1 273 КБ).

## 5. Проверка в 4 слоя

| слой | чем | «Звено» (J2, фаза 1; вся рука — Z3, `15-showcase/zveno/README.md` (C)) | клавиатура |
|---|---|---|---|
| 1. сцена веб-.blend | `qa_pipeline.py scene` | вся рука (`Z/out/c_post.log`): review — hidden_inside 8 (начинка в корпусе — задумано), nonmanifold 1, big_textures (атлас 2048²) | — |
| 2. структура | валидатор Khronos (`gltf_check.py`) | 0 ошибок / 0 предупреждений (десктоп, телефон, KTX2) | 0 ошибок (предупреждение `image/ktx2` у gltfpack — ложное) |
| 3. что создаст three | `glb_lint`, `gltf_web_inspect` (без CDN — `Z/zweb_tools.py inspect`) | `glb_lint` 0 предупреждений; вся рука — 0 ошибок консоли, 66 вызовов, 87 903 треуг. | three: загрузка, варианты переключаются, 0 ошибок консоли |
| 4. вид | `gltf_diff.py` Cycles ↔ three (`--tone neutral`) | J2: IoU 0,999, ΔE 2,85 (норма ≤ 3,5), p95 7,5, SSIM 0,90, 6 вызовов; вся рука (3 вида 512²): IoU 0,986, ΔE 8,3 / p95 28 — почти целиком анизотропный металл (у three и Cycles разные модели анизотропии), лак, графит и резина в норме | та же камера A/B/C: `12-metrics/abc_after_fix.json` |

Утилиты проверки модели базы берут three с jsDelivr — без сети через обёртку с локальным three (Z `zweb_tools.py`: import map и декодеры
→ `three` 0.186.0 симлинком) [проверено: Z `rules.md`].

## 6. Код: подключение GLB

«Звено»: одна опция в `main.js` страницы, найденный в GLB модуль заменяет процедурный, ненайденные остаются кодом.

```js
// [проверено: 15-showcase/zveno/c-hybrid/js/main.js; сборка _shared/code3d/build.sh c-hybrid/js --glb] — отрывок
S = createScene(canvas, { context: gl, dprMax: mqMobile.matches ? 1.25 : 1.5, quality: mqMobile.matches ? 'low' : 'high',
  // вариант C (дорожка Z2): модули и начинка — GLB из Blender (крюк _shared/code3d), всё живое — кодом
  glb: { url: 'assets/zveno.glb', lowUrl: 'assets/zveno-low.glb' } });
```

```js
// [проверено: 15-showcase/_shared/code3d/src/glb-modules.js, adaptModules() — версия файла 26.09 00:14] — отрывок
    if (!meshNode) {                                               // контракт: пустышка — её TRS = шарнир, код его отбрасывает
      n.removeFromParent();
      n.position.set(0, 0, 0); n.quaternion.identity(); n.scale.set(1, 1, 1);
      n.updateMatrix(); h = n;
    } else {
      // узел модуля сам несёт меш: в его TRS может сидеть квантование (gltf-transform) — сбросить нельзя; геометрия берётся в
      // мировых координатах GLB (ждём выгрузку модуля в начале координат, как j2.glb дорожки Z)
      warnings.push(`${k}: узел «${n.name}» — меш, а не пустышка: мировой TRS узла сохранён (модуль должен лежать в начале координат)`);
      const mw = n.matrixWorld.clone();
      n.removeFromParent(); n.matrixAutoUpdate = false; n.matrix.copy(mw); n.matrix.decompose(n.position, n.quaternion, n.scale);
      h = new Group(); h.add(n);
    }
```

Клавиатура: общие меши glTF → `InstancedMesh`, ячейка атласа — атрибут экземпляра из extras узла; патч шейдера — на каждый материал
варианта (`customProgramCacheKey`).

```js
// [проверено: 12-recipes/examples/15-hybrid-blender-code/src/model_c.js, buildModelC()] three r186 — отрывок
function patchUV(mat) {
  if (mat.userData.kbPatched) return mat;
  mat.userData.kbPatched = true;
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec4 iUV;')
      .replace('#include <uv_vertex>', '#include <uv_vertex>\n#ifdef USE_MAP\n\tvMapUv = iUV.xy + iUV.zw * vMapUv;\n#endif');
  };
  mat.customProgramCacheKey = () => 'kb-iuv';
  mat.needsUpdate = true;
  return mat;
}
  for (const g of groups.values()) {
    const n = g.items.length;
    const im = new InstancedMesh(g.geo, patchUV(g.mat), n);
    const iuv = new Float32Array(n * 4);
    g.items.forEach((o, i) => {
      o.updateMatrix();
      im.setMatrixAt(i, o.matrix);
      iuv.set(o.userData.kb_uv4 || [0, 0, 1, 1], i * 4);
      // … (ссылки клавиша → экземпляр для нажатий)
    });
    g.geo.setAttribute('iUV', new InstancedBufferAttribute(iuv, 4));
```

## 7. Страница C: постер = LCP, 3D после `load`, 0 кадров в покое

```js
// [проверено: 12-recipes/examples/15-hybrid-blender-code/src/main_3d.js и page.js] — отрывок
  if (reduceMQ.matches) {                        // reduce: three не грузится, 0 кадров WebGL
    startPage(createAdapterB({ pressFrames: cfg.staticPressFrames, turnFrames: cfg.staticTurnFrames }));
    logTiming({ mode: 'reduce-static' });
    return;
  }
  // …
  const gl2 = typeof WebGL2RenderingContext !== 'undefined';   // без пробного контекста: на странице ровно один WebGL
  // …
  afterLoadIdle(() => whenNear(document.getElementById('stage-type'), '0px 0px 10% 0px', go));

export function afterLoadIdle(fn) {
  const go = () => ('requestIdleCallback' in window ? requestIdleCallback(fn, { timeout: 2000 }) : setTimeout(fn, 200));
  if (document.readyState === 'complete') go(); else addEventListener('load', go, { once: true });
}
```

| правило (KIT §5) | «Звено» C | клавиатура C | доказательство |
|---|---|---|---|
| постер = LCP (`<picture>`, `fetchpriority="high"`) | постер — первый кадр той же сцены кода (та же камера), иначе «прыжок»; постеры C (Z3) — кадр сцены кода с GLB (`c-hybrid/img/`), LCP 56 / 660 мс (H1) | кадр Cycles H2v2 (как у B), AVIF 1920×1200 — 9 КБ | Z `HANDOFF-3.md §2, §5`; KB `rules.md` |
| 3D после `load` в простое | `requestIdleCallback` → `import('./three-scene.js')`; начинка — отдельным GLB в простое, через ≈ 51 мс после первого кадра | по намерению: первое нажатие, касание, клик или остановка ≥ 2,5 с на разделе (KB3; «при подходе к разделу» — EG-PERF-01 4,2 %) | `main.js`; `main_3d.js`; KB `12-metrics/kb3_loaf_probe.json` |
| один контекст WebGL | контекст берётся на том же холсте и отдаётся three | canvas переезжает между сценами «набор / расцветки / разборка» | CD `main.js`; KB `rules.md` (пробный `getContext` = 2-й контекст, EG-WEIGHT-03) |
| 0 кадров в покое, reduce | рендер по требованию; reduce → станции | reduce → кадры, three не грузится | ворота ниже |

| ворота | клавиатура C (KB2 → итог KB3 в тишине) | «Звено» C (итог Z3 в тишине, 03:45) |
|---|---|---|
| `gate_check` десктоп / Pixel 7 / reduce | KB2: 9/9, 9/9, 6/6, LCP 72 / 556 мс, TBT 0 / 9 → **KB3: 9/9 · 9/9 · 6/6, LCP 52 / 548 мс, TBT 0**, 0 вызовов в покое, 3D первого экрана 0 КБ | **0 FAIL**: LCP 56 / 660 мс (H1), TBT 56 / 146 мс, 0 вызовов в покое, 3D 1 256 / 575 КБ br (≤ 1 536 / 820), DPR 1,0 / 1,25 |
| `motion_check` | L1: KB2 — B 0, S 3 (длинные кадры прокрутки 4,2 %, два контекста WebGL) → **KB3: 79 PASS, 0 FAIL** | L2: **0/0/0** (`Z/out/motion_c/`) |
| `marketing_audit` | KB2 — 3 блокера контраста шапки → **KB3: 0 блокеров**, полировка D 38 | L2: серьёзных 0, полировка D — общий `style.css` A (`Z/out/mkt_c/`) |
| JS 3D, КБ br: телефон / десктоп | KB2: 164,7 / 245,3 → **KB3: 139 / 220** (L1 ≤ 200 / 300) | 159,5 / 256,3 (фаза 2; L2 ≤ 250 / 350) + GLB |

## 8. Числа гибрида против кода

| что | «Звено» A (код) | «Звено» C (гибрид) | клавиатура A | клавиатура C | доказательство |
|---|---|---|---|---|---|
| 3D-ассеты | 0 | 1 273 КБ десктоп / 705 КБ телефон (фаза 2) → на странице 1 256 / 575 КБ br (основной + начинка, Z3) | 0 | KB2: 340 КБ (176 br) KTX2 / 255 КБ (98 br) WebP → KB3: 159 / 84,5 КБ br (WebP 2048 / 512, телефон 42,8 тыс. треуг.) + тень 4 КБ | `c-hybrid/assets`; `15-showcase/zveno/README.md` (C); KB `HANDOFF-3.md §9` |
| JS 3D, КБ br (десктоп / телефон) | 231,2 / 134,3 → p3: 234,1 / 135,7 | 256,3 / 159,5 (фаза 2) | 213,7 / 133,1 → KB3: 208 / 127 | 245,3 / 164,7 → KB3: 220 / 139 | CD/19, CD `HANDOFF-3.md §4`; KB README, KB `HANDOFF-3.md §9` |
| кадр, мс (тишина, десктоп) | 4,32 (сборка c3) | 2,77 (J2 из GLB, N8AO выкл.) | — | — | CD/15 |
| вызовов в кадре | 92 / 40 | 86 / 33 (только J2 из GLB); стенд со старым GLB всей руки — 115 / 54 | 23 | 27 | CD/15; Z `HANDOFF-2.md §5`; KB |
| треугольников в кадре (десктоп) | 77 190 | 88 285 (J2); стенд всей руки — 137 тыс. | 126 368 | 107 тыс. (телефонный GLB — 42,8 тыс. после `-si 0.4`, KB3) | там же; KB `12-metrics/kb3_phone_glb.json` |
| вид к кадру Blender (та же камера) | — | — | оборот ΔL* −1,6 / мед. 5,3 | −1,1 / 5,3 | KB `abc_after_fix.json` |

Время: Z2 (страница B и ассет C) — 1 ч 20 мин агента, 646 с машины; крюк CD2 — окно 20:21–20:43 (+ паритет пиксель в пиксель с фазой 1);
KB2 (B, C и A клавиатуры) — 20:14–21:40, машина 3331 с [проверено: `HANDOFF-2.md` дорожек].

## 9. Когда гибрид окупается

Гипотеза D7 (`15-showcase/_shared/digests/04-code-3d-inventory.md` D): «продукту с CAD выгоден гибрид — меш и AO из Blender, всё живое кодом; окупается, если доля побед по craft
≥ 0,75 при ≤ +1,5 МБ». Что уже известно по числам: вес «Звена» C в бюджете (1,27 МБ ≤ 1,5 десктоп; 0,7 ≤ 0,8 телефон); кадр гибрида
дешевле кода на 1,55 мс (AO запечён); JS дороже на 25,8 КБ br. В единицах «вау на рубль» (1 ед. = 1 мс = 50 КБ br = 0,5 МБ):
десктоп +2,5 (GLB) + 0,5 (JS) − 1,55 (кадр) ≈ **+1,5 ед.**, телефон +1,4 + 0,5 + 0,01 ≈ **+1,9 ед.** [расчёт RC по числам CD/Z].
На странице (Z3) вес «Звена» C — 1 256 / 575 КБ br при лимитах 1 536 / 820. Решение — по слепым парам C ↔ A
(`../11-evaluation-qa/06-wow-pairwise-3d.md §7`): голосование 26.09 — 0,40 по 5 парам (1 победа C — запись набора клавиатуры,
2 ничьи — разборка и расцветка клавиатуры, 2 поражения — главный кадр и разборка «Звена») → «по бюджету»: гибрид окупается там, где
3D отвечает на ввод (набор), а не в неподвижном кадре (`15-showcase/vote/results.md`); вживую тот же судья выбрал гибрид во всех трёх
предметах (`15-showcase/vote/live-assessment.md`) — решение по дороге для живой страницы — по живому проходу (`../11-evaluation-qa/06-wow-pairwise-3d.md §1`).

Предварительно (без голосов людей): у «Звена» Blender обходит v2 кодом по ремеслу (крепёж, маркировка, лепка формы светом — оркестратор,
`99-raw/notes/trial/orchestrator.md` 25.09 20:05); у клавиатуры C = A по живому, плюс модель и стандарт вариантов, но свет кода — металл
«холоднее» Cycles, а макро с ГРИП остаётся за кадром Blender [проверено: KB `NOTES.md`].

## Частые ошибки

| ошибка | симптом | исправление | где поймано |
|---|---|---|---|
| `optimize` по умолчанию | модули склеены, роли и варианты потеряны | `--flatten false --join false --palette false` или gltfpack `-kn -ke -km` | E/24; Z; KB |
| AO всей руки в собранной позе | в разносе на модуле тень соседа | развести модули на время запекания | Z `zweb_all.py` |
| AO 0,25 м + тонкая канавка шва | в three швы — тёмный «пунктир» | AO 0,08 м; шов ≥ 2 px кадра или линией в текстуре | Z грабли 8 |
| анизотропия только в Cycles | крышки — «чёрные динамики» | `KHR_materials_anisotropy` в веб-материал | Z |
| сброс TRS меша модуля | неверный масштаб (квантование 0,2575) | сбрасывать TRS только пустышки | CD `rules.md` |
| общий материал кольца на всю руку | вспышка зажгла бы все кольца разом | клон на модуль по роли | CD `rules.md` |
| код ждёт `uv1` для AO после `optimize` | AO пропал или по чужим UV (по логике; крюк «Звена» не ломался — three берёт `texCoord` материала) | читать `texCoord` материала (three: `aoMap.channel`) | RC-checks |
| gltfpack без `-vpf` | узлы деквантования, 296 вместо 151 | `-vpf` | KB |
| пробный `getContext('webgl2')` | второй контекст WebGL (EG-WEIGHT-03) | проверять `WebGL2RenderingContext` без контекста | KB |
| постер C взят с другой страницы | «прыжок» при подмене на 3D | постер = первый кадр той же сцены и камеры | Z (в `c-hybrid/img/` — постеры A) |
| печать под камеру не той позы | маркировка смотрит в сторону | печать и кабель — под позу hero кода (`--cam-az`) | Z `zweb_all.py` |

## Чек-лист

- [ ] Пустышки модулей с именами кода, точка = шарнир, оси three, метры сцены кода; геометрия — дети?
- [ ] Роли материалов по extras/имени; кольца и LED — на модуль; наклейки — без AO?
- [ ] AO одним атласом, модули разведены на запекание, дальность ≈ 0,08 м, денойз; анизотропия в GLB?
- [ ] Постобработка без слияния (`--flatten/--join/--palette false` или `-kn -ke -km -vpf`); валидатор 0 ошибок; `gltf_diff` ΔE ≤ 3,5?
- [ ] WebP по умолчанию (десктоп 2048, телефон 512); KTX2 — только при упоре в память GPU (≥ 2 атласа 2048²), с учётом транскодера 212 КБ br; бюджет 0,8 / 1,5 МБ?
- [ ] Страница: постер = первый кадр той же сцены, 3D первого экрана после `load`, 3D раздела — по намерению, один контекст, 0 кадров в покое, reduce без three?
- [ ] Пары C ↔ A (craft, motion) в двух порядках — доля побед гибрида посчитана?

## Открытые вопросы и противоречия

1. **KTX2 «недоступен»** (KB фаза 1: нет `toktx`/`basisu`) — ошибочно: нативный gltfpack 1.2 сам кодирует BasisU (`-tc`), KB фазы 2 и Z
   собрали KTX2. Крюк «Звена» до 26.09 KTX2 не грузил (README: «Draco и KTX2 — нет»); крюк v2 (CD3, 26.09 00:34): `glb.ktx2` — KTX2Loader
   в чанке GLB, транскодер со своего домена; `glb.innerUrl` — начинка отдельным GLB в простое с подстановкой по именам (−119 / −62 КБ br
   первого экрана, начинка через ≈ 51 мс после первого кадра); KTX2 по умолчанию не включён — см. п. 6 выжимки
   (`15-showcase/_shared/code3d/CHANGELOG.md`, CD `HANDOFF-3.md §1, §3`).
2. `00-how-to-use.md §4`: «пустышки этим прогоном не проверялись» после `optimize --flatten false --join false` — закрыто: 8 пустышек
   модулей, `j3_inner`, `cable` целы (RC-checks), имена и extras 68 узлов клавиатуры целы после gltfpack `-kn -ke`.
3. Свет гибрида — код (PMREM); запечённый свет (lightMap из Cycles, E/21) в испытании не пробовали — кандидат закрыть разрыв «металл
   холоднее Cycles» у клавиатуры [не проверено].
4. Бюджет треугольников героя (≤ 50 / 100 тыс.) к сцене ниже первого экрана: у клавиатуры C в кадре телефона было 107 тыс. — KB3 упростил
   телефонный GLB до 42,8 тыс. (`-si 0.4`, глазами без разницы); на десктопе 107 тыс. в кадре набора — ворота не меряют [спорно].
5. Кадры судьи C, записи 10 с, ворота «Звена» C, постеры C — сделаны Z3 (§7, выжимка п. 8, 12); открыто: начинка C несёт копию атласа руки
   2048² (+375 КБ br после первого кадра, ≈ +16 МБ памяти GPU) — своя выгрузка с атласом AO 512² даст −≈ 350 КБ br (Z `HANDOFF-3.md §6–7`).

## Ссылки

Крюк и контракт — `15-showcase/_shared/code3d/README.md`; ассет — `99-raw/experiments/Z/HANDOFF-2.md`, `examples/15-hybrid-blender-code/src/zweb_all.py`, `examples/15-hybrid-blender-code/src/zbuild.py`, `run_c_post.sh`;
клавиатура — `99-raw/experiments/KB/HANDOFF-2.md`, `examples/17-khr-materials-variants/src/export_web.py`, `examples/15-hybrid-blender-code/src/`, `15-showcase/keyboard/README.md`; экспорт — пресеты E
`../08-export-gltf/04-validation-pitfalls-presets.md §7`, выжимка `15-showcase/_shared/digests/03-web-delivery.md` D; запекание базы —
`../08-export-gltf/02` §5–6; страница — `../09-web-runtime/examples/hero-lazy/`; варианты — `17-khr-materials-variants.md`; код — `14-product-in-code.md`.
