# Анимация через glTF на страницу: экспорт клипов, вес, постобработка, воспроизведение в three r186

Волна 2 · агент H · 2026-09-23 · источников 13 (исходники glTF-Blender-IO 5.2.40 и three r186 — анимационная система и GLTFLoader,
справка gltf-transform 4.5 и gltfpack 1.2, документация model-viewer 4 и Google Scene Viewer, файлы волны 1 A и E) · экспериментов 8
(`99-raw/experiments/H/10…22`) · Blender 5.2.2 LTS, glTF-IO 5.2.40, three r186 (0.186.0), gltf-transform 4.5.0, gltfpack 1.2, Chromium
(Playwright, ANGLE GL, Iris Xe). Блоки `python` и `js` выполнены в напечатанном виде: `99-raw/experiments/H/30-doc-snippets`.

## Выжимка для агента

1. **Экспорт анимации: `export_animations=True`, `export_animation_mode="ACTIONS"`, сэмплирование (умолчание),
   `export_anim_slide_to_zero=True`, `export_merge_animation="ACTION"`**; базовый веб-пресет агента E ставит
   `export_animations=False` — для анимации переопределять. → §1.1 [проверено: H/10–H/14]
2. **Режимы**: ACTIONS — клип на действие (активное + NLA-дорожки с одной полосой); ACTIVE_ACTIONS — всё в один клип «Animation»;
   NLA_TRACKS — клип на дорожку (запекается целиком, активные действия не уходят); SCENE — вся сцена одним клипом; BROADCAST —
   все действия всем объектам. → §1.2 [проверено: E/15, H/12; BROADCAST — исходник]
3. **Клип начинается с 0 с только при сэмплировании**: с `export_force_sampling=False` сдвиг к нулю не применяется (клип длиннее на
   кадр). → §1.4 [проверено]
4. **Анимация материалов, света, камеры-объектива (`KHR_animation_pointer`) в three r186 не играется** — клип 0 с без треков;
   делай такой эффект JS-треком на `mesh.material.color` в том же `AnimationMixer`. → §1.6, §3.5 [проверено]
5. **Вес анимации мал**: клип трансформаций 1–5 КБ; `gltf-transform optimize` (resample внутри) убирает 60–80 % ключей; камера
   244 → 82 ключа с `gltfpack -af 10`. Тяжелы морфы, не клипы. → §2 [проверено]
6. **`gltf-transform resample` после Meshopt снимает сжатие** (26 → 66 КБ); resample — до сжатия, а `optimize` делает его сам. → §2.2 [проверено]
7. **Постобработка по умолчанию клипы не ломает**: имена анимированных узлов сохраняются (узлы-цели ≤ 0,14 мм, ≤ 0,5°); ломается
   поиск МЕША по имени (`hero_1`, `mesh_N`) — искать через `traverse` от узла. → §2.3 [проверено]
8. **Клип по имени — `THREE.AnimationClip.findByName(gltf.animations, "Reveal")`**; `mixer.clipAction("Reveal")` на `gltf.scene`
   вернёт `null` (GLTFLoader не заполняет `gltf.scene.animations`). → §3.1 [проверено]
9. **Один проигрыш: `setLoop(THREE.LoopOnce)` + `clampWhenFinished = true`**, повтор — `action.reset().play()` (`play()` время не
   сбрасывает); конец — событие `finished` на миксере. → §3.2 [проверено]
10. **Скраб прокруткой: `action.play()` один раз, затем `action.time = p·clip.duration; mixer.update(0)`**. Рецепт
    `paused = true` + `mixer.setTime()` в r186 даёт позу кадра 0; `mixer.setTime(duration)` в LoopRepeat заворачивает в начало. → §3.3 [проверено]
11. **Сглаживание прокрутки — `THREE.MathUtils.damp(current, target, λ, dt)`** (λ = 10: 99 % пути за 0,46 с, порог 1e-4 — за 0,85 с), не `lerp` без dt;
    рендер только пока `|current − target| > 1e-4`. → §3.4 [проверено: H/21; V:LSNQuFEDOyQ по отчёту V]
12. **Время — `THREE.Timer` + `timer.connect(document)`** (r183+, `Clock` устарел и пишет предупреждение); dt ограничивать 0,1 с. → §3.4 [исходник r186; проверено: H/21]
13. **Кроссфейд клипов: `from.crossFadeTo(to, 0.3, false)`**; через половину перехода веса ≈ 0,5/0,5. → §3.2 [проверено]
14. **Морфы из клипа и из кода на одном меше не смешивать**: трек пишет весь `morphTargetInfluences`, но только когда его значение
    меняется — «последний пишущий» побеждает непредсказуемо. → §3.5 [проверено]
15. **Reduced motion для скраба**: без инерции и промежуточных поз — сразу 0 или 1; для самозапускающихся петель — статичный кадр
    и стоп цикла. → §3.6 [проверено]
16. **model-viewer играет один клип (`animation-name`, по умолчанию первый) + `appendAnimation` для наложения; Scene Viewer (AR
    Android) — максимум 1 анимация, морфы запрещены, ≤ 254 кости** → отдельный AR-GLB. → §4 [документация model-viewer 4, Google]
17. **Стык с F2**: H отдаёт GLB с клипами, имена, длительности и рецепт времени; F2 — страницу, прокрутку, интерактив. → §5

## 1. Экспорт анимации из Blender 5.2

### 1.1 Параметры

| параметр 5.2.40 | умолчание | для веба | зачем |
|---|---|---|---|
| `export_animations` | True | True (в пресете E — False для статики) | клипы |
| `export_animation_mode` | ACTIONS | ACTIONS | клип на действие |
| `export_force_sampling` | True | True | точность, изинги, slide_to_zero |
| `export_frame_step` | 1 | 1 (2 — для длинных плавных клипов) | вес |
| `export_anim_slide_to_zero` | False | **True** | клип с 0 с |
| `export_merge_animation` | ACTION | ACTION (NLA_TRACK — для «одна дорожка = один клип») | слияние пообъектных анимаций |
| `export_optimize_animation_size` | True | True | удаляет только полностью постоянные каналы (2 ключа) |
| `export_bake_animation` | False | True, если есть констрейнты/драйверы и их не запекли | `02-… §3` |
| `export_apply` | False | True, но False у морф-объектов с модификаторами | `02-… §1.2` |
| `export_morph`, `export_morph_normal`, `export_morph_animation` | True | True (нормали — False для матовых) | морфы |
| `export_skins`, `export_influence_nb` | True, 4 | True, 4 | скиннинг |
| `export_cameras` | False | True для камеры из Blender | `04-… §3` |
| `export_pointer_animation` | False | False (three не играет) | §1.6 |
| `export_current_frame` | False | False (поза покоя = кадр 0) | `01-… §4.3` |

[проверено: 99-raw/experiments/H/00-api-probe — 43 анимационных параметра из 110; E/24 пресеты]. Неизвестный ключ оператора даёт
`TypeError: … keyword "…" unrecognized` — проверять по RNA до вызова (как ниже).

```python
# Blender 5.2.2 / glTF-IO 5.2.40 — [проверено] экспорт клипов для веба и разбор GLB
import os, tempfile, json, struct
import bpy
ANIM_WEB = dict(export_format="GLB", export_yup=True, export_apply=True, export_extras=True,
                export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
                export_anim_slide_to_zero=True, export_merge_animation="ACTION", export_optimize_animation_size=True,
                export_all_vertex_colors=False, use_renderable=True, use_visible=True)
def export_anim(path, **over):
    kw = dict(ANIM_WEB, **over)
    valid = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    bad = [k for k in kw if k not in valid]
    if bad:
        raise KeyError(f"нет параметров {bad} в export_scene.gltf этой версии")
    assert bpy.ops.export_scene.gltf(filepath=os.path.abspath(path), **kw) == {"FINISHED"}
    data = open(path, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
    clips = []
    for a in j.get("animations", []):
        inputs = [j["accessors"][a["samplers"][c["sampler"]]["input"]] for c in a["channels"]]
        clips.append({"name": a["name"], "duration": round(max(i["max"][0] for i in inputs), 4),
                      "start": round(min(i["min"][0] for i in inputs), 4),
                      "targets": sorted({j["nodes"][c["target"]["node"]]["name"] for c in a["channels"] if "node" in c["target"]})})
    return {"bytes": len(data), "clips": clips}
sc = bpy.context.scene; sc.render.fps = 30
ob = bpy.data.objects.new("hero_orb", None); sc.collection.objects.link(ob)
for f, z in ((10, 0.0), (40, 0.5), (70, 0.0)):                      # ключи с кадра 10
    ob.location.z = z; ob.keyframe_insert("location", index=2, frame=f)
ob.animation_data.action.name = "Bounce"
r = export_anim(os.path.join(tempfile.mkdtemp(), "bounce.glb"))
assert r["clips"] == [{"name": "Bounce", "duration": 2.0, "start": 0.0, "targets": ["hero_orb"]}], r
print(r)
```

### 1.2 Режимы и что становится клипом

| режим | что уходит (кейс H/12: Reveal со слотами на 3 части + Idle в NLA) |
|---|---|
| ACTIONS + merge ACTION | Reveal (3 узла) + Idle — по клипу на действие |
| ACTIONS + merge NONE | Idle + три клипа «Reveal» по одному узлу (одинаковые имена) |
| ACTIONS + merge NLA_TRACK | клипы по именам дорожек (кроме «NlaTrack…», «[Action Stash]») |
| NLA_TRACKS | клип на дорожку, все полосы дорожки запечены; активные действия не уходят |
| ACTIVE_ACTIONS | один клип «Animation» (`export_nla_strips_merged_animation_name`) |
| SCENE | один клип всей сцены (как во вьюпорте); `export_anim_scene_split_object` делит по объектам |
| BROADCAST | каждое совместимое действие файла — каждому анимированному объекту (как FBX) |

[проверено: E/15 a6–a9, H/12; BROADCAST — исходник 5.2.40 `action.py`, запуском не проверен]. Правила выбора действий в ACTIONS,
слоты, NLA-дорожки с одной полосой — `01-… §5`.

### 1.3 Время

`t = кадр / fps` (fps × fps_base сцены); при `export_anim_slide_to_zero` из времени вычитается начало действия (или дорожки);
отрицательные кадры — `export_negative_frame` SLIDE/CROP [исходник 5.2.40]. Клип с кадров 10–70 → 0…2,0 с [проверено: блок выше].
Длина клипа = `int(action.frame_range)` — ручной диапазон действия (`01-… §4.1`). Выбирай fps сцены 30 (или 24, 60) ДО ключей:
смена fps после ключей растягивает время клипа [практика; не проверено].

### 1.4 Сэмплы или кривые

| | сэмплы (`export_force_sampling=True`) | кривые (`False`) |
|---|---|---|
| ключи | каждый кадр диапазона, LINEAR (STEP для CONSTANT) | исходные ключи: CUBICSPLINE для BEZIER, LINEAR, STEP |
| изинги SINE…ELASTIC, смешанные интерполяции, модификаторы F-кривых | запекаются | свойство всё равно сэмплируется |
| точность в three | до 1e-5 м, 0,001° (H/11) | 1,5 мм, 0,26°, 0,07 веса (H/11, H/13); поворот ≥ 180° между ключами ломается (H/10) |
| `export_anim_slide_to_zero` | работает | **не работает** (клип с 1/fps) |
| вес данных | 16 Б/ключ вектора, 20 Б/ключ кватерниона (со временем) | в 3–8 раз меньше |

[проверено: 99-raw/experiments/H/10-turntable, 11-float-pulse, 13-morph; исходник 5.2.40 `fcurves/channels.py`, `sampled/*/sampler.py`].
Гипотеза E «кривые + gltf-transform resample = минимальный вес без потерь» не подтверждена: кривые теряют точность и сдвиг к нулю,
а сэмплы после `optimize` (resample) весят 0,3–1,3 КБ на клип — выигрыш кривых меньше 1 КБ [проверено].

### 1.5 Поза покоя, скрытые объекты, констрейнты

Поза покоя в GLB = кадр 0 (`export_current_frame=False`) [проверено: E/15 a13]; констрейнты и драйверы без запекания не
экспортируются — `02-… §3` [проверено: E/15 a11–a12]; скрытые объекты уходят в файл, если не `use_visible`/`use_renderable`
[проверено]. Анимацию видимости (hide) glTF не описывает — анимировать масштаб 0 → 1 или прозрачность в JS [практика].

### 1.6 Анимация материалов, света, камеры → JS

Экспортёр пишет `KHR_animation_pointer` только в режимах NLA_TRACKS/SCENE с `export_pointer_animation=True`
(`/materials/0/pbrMetallicRoughness/baseColorFactor`, `/extensions/KHR_lights_punctual/lights/0/intensity`), но GLTFLoader r186
пропускает каналы без `node` (`if (target.node === undefined) continue;`) — клип 0 с без треков [проверено: E/15 a15b; исходник
GLTFLoader r186]. Плагин `needle-tools/three-animation-pointer` указан в шапке GLTFLoader как отдельный — не проверялся. Рабочий
путь — трек three на свойство материала (`ColorKeyframeTrack('cta_dot.material.color', …)`) в том же миксере, §3.5 [проверено].

## 2. Вес и постобработка

### 2.1 Сколько весит клип

| клип (H/…) | экспорт 5.2.40: ключей / данные | после `gltf-transform optimize` (resample) | gltfpack |
|---|---|---|---|
| Reveal: 5 каналов, 2 с | 300 / 4,56 КБ | 104 / 1,33 КБ | 300 / 3,12 КБ (`-cc`, квантование) |
| Idle: 1 канал, 3 с | 91 / 1,46 КБ | 18 / 0,29 КБ | 91 / 1,46 КБ |
| CameraMove: T + R + S, 4 с | 244 / 3,9 КБ | 224 / 3,18 КБ | 242 / 2,9 КБ; `-af 10`: **82 / 0,98 КБ** |
| LogoIntro: 6 каналов, 1,5 с | 276 / 3,68 КБ | 148 ключей | — |
| Morph: 2 веса, 3 с | 90 / 1,08 КБ | — | — |

[проверено: 99-raw/experiments/H/22-size-postprocess, 16-logo-motion, 13-morph; вес — `npx gltf-transform inspect --format md`, раздел
ANIMATIONS]. Для сравнения: геометрия и текстуры тех же GLB — 40–250 КБ; морфы — вершины × цели × 12–24 Б (`02-… §1.3`).

### 2.2 Порядок постобработки

- `gltf-transform optimize` по умолчанию делает `--resample true` («losslessly deduplicating keyframes») [проверено: `optimize --help`,
  4.5.0]; отдельный `resample` ПОСЛЕ Meshopt снимает `EXT_meshopt_compression`: 26,2 → 66,2 КБ [проверено].
- gltfpack 1.2: `-af N` — пересэмплировать анимацию в N Гц (умолчание 30, 0 — выключить), `-at/-ar/-as` — биты квантования
  переноса/поворота/масштаба (16/12/16), `-ac` — сохранить постоянные треки [проверено: `gltfpack -h`]; постоянный scale камеры
  выброшен без `-ac` [проверено].
- Для анимированных файлов E советует `--flatten false --join false` (адресуемые части); на клипы это не влияет — анимированные узлы
  gltf-transform не сливает [проверено: H/22 — с умолчаниями клипы целы].

### 2.3 Имена после постобработки

| инструмент | узлы-цели треков (`case_lid`, `bud_l`…) | меши |
|---|---|---|
| `gltf-transform optimize` (квантование) | имя остаётся у узла-родителя, треки находят его | ребёнок `case_lid_1` |
| gltfpack `-cc` | имена анимированных узлов остаются | `mesh_N`, дубли → `mesh_0_instance_*` |

[проверено]. В three имена ещё санитизируются (`PropertyBinding.sanitizeNodeName`: пробел → «_», удаляются `[ ] . : /`), дубли
получают `_1`, `_2`; трек ищет узел по имени обходом в глубину — первое совпадение [исходник r186, заметки H-sub/B].

## 3. Воспроизведение в three r186

### 3.1 Загрузка и клип по имени

```js
// three r186 — [проверено] клип по имени, один проигрыш с фиксацией, событие finished, повтор
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';

const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync('reveal.glb');
const mixer = new THREE.AnimationMixer(gltf.scene);
const clip = THREE.AnimationClip.findByName(gltf.animations, 'Reveal');   // mixer.clipAction('Reveal') на gltf.scene → null
const reveal = mixer.clipAction(clip);
reveal.setLoop(THREE.LoopOnce);
reveal.clampWhenFinished = true;                                          // остаться в последней позе
let finished = false;
mixer.addEventListener('finished', (e) => { if (e.action === reveal) finished = true; });
reveal.play();
for (let t = 0; t < clip.duration + 0.2; t += 1 / 60) mixer.update(1 / 60);   // на странице: mixer.update(dt) в цикле рендера
const lid = gltf.scene.getObjectByName('case_lid');
const deg = THREE.MathUtils.radToDeg(new THREE.Euler().setFromQuaternion(lid.quaternion).x);
if (!finished || Math.abs(deg + 105) > 0.5) throw new Error(`finished=${finished}, крышка ${deg}°`);
reveal.reset().play();                                                    // повтор с начала: play() время не сбрасывает
console.log(`Reveal ${clip.duration.toFixed(3)} с, крышка ${deg.toFixed(1)}°`);
```

### 3.2 Кроссфейд и веса

```js
// three r186 — [проверено] кроссфейд Idle → Reveal за 0,4 с: веса на середине ≈ 0,5
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';

const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync('reveal.glb');
const mixer = new THREE.AnimationMixer(gltf.scene);
const idle = mixer.clipAction(THREE.AnimationClip.findByName(gltf.animations, 'Idle'));
const reveal = mixer.clipAction(THREE.AnimationClip.findByName(gltf.animations, 'Reveal'));
idle.play();
mixer.update(0.5);
reveal.setLoop(THREE.LoopOnce); reveal.clampWhenFinished = true;
reveal.reset().play();
idle.crossFadeTo(reveal, 0.4, false);                                     // warp=false: скорость клипов не подгоняется
mixer.update(0.2);
const w = [idle.getEffectiveWeight(), reveal.getEffectiveWeight()];
if (Math.abs(w[0] - 0.5) > 0.05 || Math.abs(w[1] - 0.5) > 0.05) throw new Error('веса ' + w);
mixer.update(0.3);
if (idle.getEffectiveWeight() > 0.01 || reveal.getEffectiveWeight() < 0.99) throw new Error('кроссфейд не завершился');
console.log('веса на середине', w.map((x) => x.toFixed(2)).join(' / '));
```

Нормальное смешивание в three — нормированное среднее (два действия с весом 1 дают 50/50), при суммарном весе < 1 досмешивается
исходная поза; `stop()` возвращает свойства в состояние на момент `play()` [исходник r186 PropertyMixer/AnimationMixer, заметки
H-sub/B]. Аддитивные клипы — `THREE.AnimationUtils.makeClipAdditive(clip)` + `blendMode` [исходник r186; не проверено].

### 3.3 Скраб по прокрутке

| способ (клип 4 с, ожидание p·360°) | результат в r186 |
|---|---|
| `action.play(); action.paused = true; mixer.setTime(p·d)` | 0° при любом p |
| `action.play(); action.time = p·d; mixer.update(0)` | 90 / 180 / 270° ✔ (и при `paused = true`) |
| `mixer.setTime(p·d)`, LoopRepeat | верно внутри, p = 1 → 0° (заворот) |
| LoopOnce + clamp + `setTime` | после конца обратный скраб застревает |
| LoopOnce без clamp | после конца `enabled = false`, исходная поза |

[проверено]. Цена `action.time = …; mixer.update(0)` — 1,1 мкс на вызов (клип из 1 трека).
Рецепт каталога A (`../01-web-3d-landscape/01-… §4.5`, выжимка п. 12) с `paused` + `setTime` в r186 не работает — передано в отчёт.

```js
// three r186 — [проверено] скраб: прогресс → время клипа, сглаживание damp, без заворота в конце
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';

const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync('reveal.glb');
const mixer = new THREE.AnimationMixer(gltf.scene);
const clip = THREE.AnimationClip.findByName(gltf.animations, 'Reveal');
const action = mixer.clipAction(clip);
action.play();                                                            // один раз; дальше время задаём сами

function scrubTo(p) {                                                     // p = 0…1 из прокрутки секции
  action.time = THREE.MathUtils.clamp(p, 0, 1) * clip.duration;           // не mixer.setTime: он заворачивает конец в 0
  mixer.update(0);
}
let current = 0;
function step(target, dt) {                                               // в цикле rAF: dt = Math.min(timer.getDelta(), 0.1)
  current = THREE.MathUtils.damp(current, target, 10, dt);                // λ = 10: 99 % пути за 0,46 с при любой частоте кадров
  scrubTo(current);
  return Math.abs(current - target) > 1e-4;                               // false — можно не рендерить
}
const lid = gltf.scene.getObjectByName('case_lid');
const lidDeg = () => THREE.MathUtils.radToDeg(new THREE.Euler().setFromQuaternion(lid.quaternion).x);
scrubTo(1);
if (Math.abs(lidDeg() + 105) > 0.5) throw new Error('p = 1 должен давать конечную позу, а не начало: ' + lidDeg());
let frames = 0;
while (step(0.5, 1 / 60)) frames++;
console.log(`p=1 → ${lidDeg().toFixed(1)}°, догнал p=0.5 за ${frames} кадров`);
```

Полная страница (секция 400vh, `THREE.Timer`, рендер по требованию, reduced motion) — `99-raw/experiments/H/21-scroll-page/index.html`:
60 fps, 7 вызовов отрисовки, 0 ошибок консоли [проверено]. Прокрутку, закрепление секций (GSAP ScrollTrigger, Lenis) и
интерактив пишет F2 — `../09-web-runtime/`.

### 3.4 Время и плавность

- `THREE.Clock` помечен устаревшим с r183 и пишет предупреждение; `THREE.Timer` + `timer.connect(document)` обнуляет dt, пока
  вкладка скрыта (нет «скачка» после возврата) [исходник r186, заметки H-sub/B; проверено: H/21].
- `MathUtils.damp(x, y, λ, dt) = lerp(x, y, 1 − e^(−λ·dt))` — независимое от частоты кадров экспоненциальное сглаживание
  [исходник r186; V:LSNQuFEDOyQ по отчёту V волны 1]; `lerp(x, target, 0.1)` в rAF на 120 Гц вдвое быстрее, чем на 60 Гц.
- `mixer.timeScale` — пауза/скорость всех действий; `action.setEffectiveTimeScale(k)` — одного; `action.setDuration(s)` — растянуть
  клип до длительности [исходник r186; не проверено].

### 3.5 Свойства материалов и морфы из кода

```js
// three r186 — [проверено] анимация цвета и свечения материала JS-треками (вместо KHR_animation_pointer)
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const gltf = await new GLTFLoader().loadAsync('float_pulse_sampled.glb');
const dot = gltf.scene.getObjectByName('cta_dot');
dot.material = dot.material.clone();                                      // свой материал: не красить соседей с тем же материалом
const glow = new THREE.AnimationClip('Glow', 1.5, [
  new THREE.ColorKeyframeTrack('cta_dot.material.color', [0, 0.75, 1.5], [1, 0.45, 0.09, 1, 0.9, 0.3, 1, 0.45, 0.09]),
  new THREE.NumberKeyframeTrack('cta_dot.material.emissiveIntensity', [0, 0.75, 1.5], [2, 6, 2]),
]);
const mixer = new THREE.AnimationMixer(gltf.scene);
const pulse = THREE.AnimationClip.findByName(gltf.animations, 'Pulse');   // клип из Blender (масштаб) + JS-клип (материал)
mixer.clipAction(pulse).play();
mixer.clipAction(glow).play();
mixer.update(0.75);
const c = dot.material.color, e = dot.material.emissiveIntensity;
if (Math.abs(c.g - 0.9) > 1e-3 || Math.abs(e - 6) > 1e-3) throw new Error(`цвет ${c.getHexString()}, свечение ${e}`);
console.log('на 0,75 с: цвет #' + c.getHexString() + ', emissiveIntensity ' + e + ', масштаб ' + dot.scale.x.toFixed(3));
```

Каждое изменение свойства материала через трек ставит `material.needsUpdate = true` [исходник r186 PropertyBinding, заметки H-sub/B];
для частых изменений нескольких материалов дешевле uniform своего шейдера (цена не мерялась).

```js
// three r186 — [проверено] вес морфа по имени из кода; клип и код на одном меше конфликтуют
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';

const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync('morph_meshopt.glb');
let blob = null;
gltf.scene.traverse((o) => { if (o.isMesh && o.morphTargetDictionary) blob = o; });
const flower = blob.morphTargetDictionary.Flower;                         // имена — из extras.targetNames экспортёра
blob.morphTargetInfluences[flower] = 0.7;                                 // без клипа: вес задаёт код
const mixer = new THREE.AnimationMixer(gltf.scene);
const action = mixer.clipAction(THREE.AnimationClip.findByName(gltf.animations, 'Morph'));
action.play();
action.time = 60 / 30; mixer.update(0);                                   // клип: кадр 61 → Cube 0,3 / Flower 0,7? — смотрим, что стало
const fromClip = blob.morphTargetInfluences[flower];
blob.morphTargetInfluences[flower] = 0.1;                                 // код переписал вес…
mixer.update(0);                                                          // …клип не изменил значение → не перезаписал
const stale = blob.morphTargetInfluences[flower];
action.time = 70 / 30; mixer.update(0);                                   // значение клипа изменилось → перезаписал весь массив
if (stale !== 0.1 || Math.abs(blob.morphTargetInfluences[flower] - fromClip) < 1e-6) throw new Error('поведение изменилось');
console.log(`из клипа ${fromClip.toFixed(3)}, после правки кода ${stale}, после следующего кадра клипа ${blob.morphTargetInfluences[flower].toFixed(3)}`);
```

Вывод: на меше, который анимирует клип, весом из кода не управлять — либо отдельный меш, либо свой трек в том же клипе/миксере.

### 3.6 Reduced motion и экономия

- Скраб: при `prefers-reduced-motion: reduce` — без damp и промежуточных поз (0 или 1 по порогу 0,5) [проверено].
- Самозапускающиеся петли (турнтейбл, парение, пульс) — статичный кадр и остановка цикла; вне экрана — `IntersectionObserver`,
  скрытая вкладка — `document.hidden` [практика: `../01-web-3d-landscape/01-… §1.4`]; WCAG 2.2.2: автоматическое движение дольше 5 с
  параллельно с контентом — нужен механизм паузы; появление в области видимости = автозапуск [стандарт: `../../ui-research/08-motion/03-… §2.2`].
- Рендер по требованию: цикл rAF только пока идёт анимация или догоняет damp [проверено].

### 3.7 Цена воспроизведения

| что | замер | статус |
|---|---|---|
| скраб `action.time + update(0)` | 1,1 мкс на вызов | [проверено] |
| страница: кейс 7 мешей, клип 5 треков, damp | 60 fps, p95 16,7 мс, 7 вызовов | [проверено] |
| морф 2 737 вершин × 2 цели | без влияния на 60 fps (стенд) | [проверено] |
| скиннинг 4 кости, 514 вершин | GLB 36,6 КБ; кадр не мерялся | [проверено: H/30 — только экспорт] |
| много морфов/костей на телефоне | не мерялось | [не проверено] |

Кэш привязок AnimationMixer: одно свойство — один PropertyMixer на все действия; второй `clipAction` того же клипа дешевле первого
[исходник r186, заметки H-sub/B]. Много одинаковых объектов с одной анимацией — `AnimationObjectGroup` (одно время на всех) [исходник; не проверено].

## 4. model-viewer и AR

- `<model-viewer animation-name="Reveal" autoplay>`: без `animation-name` играет первый клип; смена клипа — автоматический
  кроссфейд `animation-crossfade-duration` (300 мс); `play({repetitions, pingpong})`, `pause()`, `timeScale`, `availableAnimations`;
  `appendAnimation(name, {weight, timeScale, fade, …})` накладывает клипы одновременно [документация: modelviewer.dev/docs, 4.x].
- Scene Viewer (Android AR): ошибки валидатора `ANIMATION_LIMIT_EXCEEDED` (максимум 1 анимация), `MORPH_TARGET_USED` (морфы запрещены),
  `JOINT_LIMIT_EXCEEDED` (254 кости); звук зацикливается вместе с «animation 0» [документация: developers.google.com/ar/develop/scene-viewer].
- iOS Quick Look: model-viewer генерирует USDZ на лету без анимаций; анимированный USDZ — отдельная поставка [документация через A
  `../01-web-3d-landscape/05-… §3.7`; не проверено].
- Правило: AR-GLB — один клип (первым в файле), без морфов; веб-GLB — сколько нужно клипов.

## 5. Стык с F1/F2 и тем, кто пишет страницу

| кто | отдаёт | где |
|---|---|---|
| H (этот файл) | GLB с клипами (имена = действия, 30 fps, с 0 с), длительности, узлы-цели, рецепт времени (§3.3), JSON-путь камеры (`04-… §3`) | `99-raw/experiments/H/*/out`, `99-raw/notes/wave2/H-notes.md` «Для F2» |
| F2 | страница: прокрутка (ScrollTrigger/Lenis), закрепление секций, интерактив, reduced motion страницы | `../09-web-runtime/02-…`, `03-…` |
| F1 | загрузка, декодеры (Meshopt), память, производительность на телефонах | `../09-web-runtime/01-…`, `05-…` |

Готовые клипы: Reveal 1,967 с (узлы case_lid, bud_l, bud_r) и Idle 3,0 с (H/12, H/21), Turntable 4,0 с (H/10), Float 3,0 с и Pulse 1,5 с
(H/11), Morph 2,967 с (H/13), CameraMove 4,0 с + `camera_path.json` (H/14), LogoIntro 1,5 с + `timeline.json` (H/16).

## Частые ошибки

1. Экспорт с базовым веб-пресетом (`export_animations=False`) — в GLB нет клипов.
2. `mixer.clipAction('Имя')` на `gltf.scene` → `null` → `TypeError` на `.play()`.
3. Скраб через `paused = true` + `mixer.setTime` — модель стоит в первой позе (рецепт из сети и каталога A).
4. `mixer.setTime(duration)` в конце прокрутки — прыжок в начало клипа (LoopRepeat).
5. `LoopOnce` без `clampWhenFinished` — после конца объект возвращается в исходную позу; повтор без `reset()` не играет.
6. `lerp(x, target, 0.1)` без dt — плавность зависит от частоты экрана; `Clock` вместо `Timer` — предупреждение r183+.
7. Анимация цвета/света в Blender в расчёте на `KHR_animation_pointer` — в three клип 0 с.
8. `gltf-transform resample` после Meshopt — файл вырос в 2,5 раза.
9. Поиск меша по имени после постобработки (`getObjectByName('case_lid')` вернёт узел, меш — `case_lid_1`) — менять материал у узла бессмысленно.
10. Вес морфа из кода на меше, который анимирует клип, — «плавающий» результат.
11. Один GLB для веба и AR — Scene Viewer отказывает (морфы, >1 анимации, Draco/KTX2 — `../08-export-gltf/`).
12. Бесконечный цикл рендера при остановленной анимации и при reduced motion.

## Чек-лист

- [ ] В GLB есть все нужные клипы с ожидаемыми именами и длительностями (`gltf-transform inspect`, раздел ANIMATIONS)?
- [ ] Клипы начинаются с 0 с (`start = 0`)?
- [ ] Постобработка: `optimize` (resample внутри) или gltfpack; отдельный resample — только до сжатия?
- [ ] После постобработки клип двигает нужные узлы (сравнение позиций узлов-целей в 3–5 моментах)?
- [ ] Клип находится `findByName(gltf.animations, …)`?
- [ ] Один проигрыш — LoopOnce + clampWhenFinished, повтор — `reset().play()`?
- [ ] Скраб — `action.time = p·duration; mixer.update(0)`, конец без заворота?
- [ ] Сглаживание — `damp` с dt, время — `Timer`, dt ≤ 0,1 с, рендер по требованию?
- [ ] Reduced motion: скраб без инерции, петли стоят; вне экрана цикл стоит?
- [ ] Анимация материалов/света — JS-треками, не pointer?
- [ ] Для AR — отдельный GLB с одним клипом без морфов?

## Открытые вопросы и противоречия

- Каталог A (`01-web-3d-landscape/01 §4.5`, выжимка п. 12) рекомендует `action.paused = true; mixer.setTime(progress·duration)` —
  в r186 это поза кадра 0 (H/20). Нужна правка при аудите (X) и учёт в F2 (записано в заметках H «Для F2»).
- Гипотеза E (кривые + resample) опровергнута на наших клипах; на длинных клипах камеры с множеством ключей Безье не мерялась.
- Плагин `KHR_animation_pointer` для three (needle-tools) и поддержка pointer в model-viewer/Babylon — не проверены.
- Цена скиннинга и морфов на телефонах (кадр, память), `AnimationObjectGroup` на сотнях объектов — не мерялись.
- Поворот клипа 0,49° после optimize/gltfpack (H/22) — источник (resample или квантование 12 бит) не выяснен; визуально незаметно.

## Источники

- [S1] KhronosGroup/glTF-Blender-IO 5.2.40 (в Blender 5.2.2): `__init__.py` (параметры анимации, связи флагов), `blender/exp/animation/action.py`, `fcurves/channels.py`, `sampled/*/sampler.py` (slide), `tracks.py`; https://github.com/KhronosGroup/glTF-Blender-IO ; первоисточник.
- [S2] Blender Foundation. Blender Manual 5.2 — glTF 2.0 (раздел Animation) — https://docs.blender.org/manual/en/5.2/addons/import_export/scene_gltf2.html (через E `../08-export-gltf/01 §9`); документация.
- [S3] mrdoob/three.js r186: `src/animation/AnimationMixer.js`, `AnimationAction.js`, `AnimationClip.js`, `PropertyBinding.js`, `PropertyMixer.js`, `core/Timer.js`, `math/MathUtils.js`, `examples/jsm/loaders/GLTFLoader.js` — прочитаны помощником целиком (`99-raw/notes/wave2/H-sub/B-web-docs.md`); https://github.com/mrdoob/three.js ; первичный.
- [S4] Khronos. KHR_animation_pointer — https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_animation_pointer (через E `01 §7.1`); спецификация.
- [S5] Don McCurdy. glTF-Transform 4.5.0 CLI — справка `gltf-transform optimize --help`, `inspect`; https://gltf-transform.dev ; документация (проверено запуском).
- [S6] Arseny Kapoulkine. gltfpack 1.2 (meshoptimizer) — справка `gltfpack -h` (раздел Animations); https://github.com/zeux/meshoptimizer ; документация (проверено запуском).
- [S7] Google. model-viewer 4.x docs — https://modelviewer.dev/docs/ (кэш `99-raw/cache/modelviewer.dev_docs_index.html_…`): animation-name, autoplay, animation-crossfade-duration, play, appendAnimation; документация.
- [S8] Google ARCore. Scene Viewer — https://developers.google.com/ar/develop/scene-viewer (кэш): ANIMATION_LIMIT_EXCEEDED, MORPH_TARGET_USED, JOINT_LIMIT_EXCEEDED 254; документация.
- [S9] Агент E, волна 1. `../08-export-gltf/01-export-contract.md` §3, §7, §9; `04-validation-pitfalls-presets.md` §7; эксперименты E/15, E/24 — внутренний.
- [S10] Агент A, волна 1. `../01-web-3d-landscape/01-effects-catalog.md` §1.4, §4.5; `05-blender-deliverables-map.md` §3.7 — внутренний (рецепт §4.5 опровергнут H/20).
- [S11] Отчёт V, волна 1 — Freya Holmér «Lerp smoothing is broken» `[V:LSNQuFEDOyQ]` и проверка `MathUtils.damp` в r186; внутренний.
- [S12] `../../ui/08-motion/03-reduced-motion-and-motion-tokens.md` §2 — WCAG 2.2.2, 2.3.3, «reduce, not remove»; соседняя база.
- [S13] Эксперименты H: `10-turntable`, `11-float-pulse`, `12-reveal-parts`, `13-morph`, `14-camera-path`, `16-logo-motion`, `20-scrub-api`, `21-scroll-page`, `22-size-postprocess`, `30-doc-snippets` — [проверено].
