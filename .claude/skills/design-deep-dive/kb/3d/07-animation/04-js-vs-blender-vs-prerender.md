# Где делать движение: JS на странице, клип из Blender или предрендер (видео, секвенция) — дерево решений

Волна 2 · агент H · 2026-09-23 · источников 9 (каталог эффектов и карта поставок агента A, контракт экспорта E, исходники three r186,
Codrops 2025–2026, `../../ui/08-motion/`, Jake Archibald 2024 через A) · экспериментов 6 (`99-raw/experiments/H/10`, `11`, `12`,
`14`, `16`, `21`) · Blender 5.2.2 LTS, three r186, ffmpeg 7.1.5. Блоки кода выполнены в напечатанном виде: `99-raw/experiments/H/30-doc-snippets`
(`python` — Blender, `js` — страница с three r186), `bash` — команды эксперимента H/16.

## Выжимка для агента

1. **Сначала вопрос «движение управляется пользователем?»**: прокрутка, курсор, клик, смена варианта → реалтайм (JS или клип
   Blender); только самопроизвольная петля или интро без взаимодействия → предрендер (видео/секвенция) дешевле и надёжнее. → §1 [практика; проверено: H/16]
2. **Движение целых объектов по стандартным кривым (вращение, парение, пульс, наклон к курсору, параллакс) — JS** (`damp`, синус,
   GSAP): параметры правятся без Blender, адаптивны, 0 байт клипа. → §1, §2 [проверено: H/16 — JS повторяет клип с точностью 0,1 мм]
3. **Хореография многих частей, ручной тайминг аниматора, деформация (морф, скелет) — клип из Blender**: одно действие со слотами,
   скраб `action.time`. → §2 [проверено]
4. **Симуляции (ткань, бумага, разрушение) — запекать** (морфы/VAT) или предрендерить; в браузере не пересчитывать. → §2 [проверено: `02-… §4.2`]
5. **Анимация цвета, света, свечения — только JS** (треки на свойства материала или uniform): `KHR_animation_pointer` three r186 не
   играет. → §2 [проверено: E/15, `03-… §3.5`]
6. **Путь камеры на прокрутке по умолчанию — JSON-кривая из Blender → `CatmullRomCurve3`** (1,4 КБ, отклонение от запечённой камеры
   8 мм / 0,1°, свобода в JS: свой easing, damp, FOV под экран); запечённая камера — когда важны повороты/FOV аниматора. → §3 [проверено]
7. **Интро логотипа**: если на странице уже есть three — JS-таймлайн (+1,5 КБ) или клип Blender (+3,9 КБ к GLB); если WebGL нет —
   видео с альфой (VP9-alpha 32 КБ + stacked HEVC/AV1 для Safari, 512², 1,5 с). → §4 [проверено]
8. **Видео фиксирует разрешение, ракурс и цвет**: 512² при DPR 2 = 256 CSS px; для 512 CSS px — 1024² (в ≈ 3–4 раза тяжелее).
   Реалтайм-GLB резок при любом DPR. → §4 [расчёт; проверено: размеры H/16, A/06]
9. **Скраб видео прокруткой — только all-intra (×3–4 к весу) или секвенция кадров**; обычное видео при перемотке назад дёргается. → §2 [проверено]
10. **Петли для видео рендери кадрами 1…N−1** (кадр N = кадр 1), для glTF — ключи 1…N (t = duration заворачивается в 0). → §4 [проверено]
11. **Длительности 3D-движения**: интро/раскрытие 1–2,5 с однократно, петли 3–4 с и медленнее, турнтейбл 8–20 с на оборот;
    интерфейсные 150–300 мс — не для 3D-сцен; кривые ролей (вход ease-out, выход ease-in, цикл linear) — из `ui`. → §5 [мнение; документация: ui-research 08-motion]
12. **Reduced motion**: скраб — без инерции (0/1), петли стоят, видео на постере; «reduce, not remove»: затухание вместо полёта. → §6 [проверено: H/21; стандарт WCAG]

## 1. Дерево решений

```
Движение управляется пользователем (прокрутка, курсор, клик, вариант)?
├─ нет → нужен ли 3D-интерактив рядом (вращать, выбирать цвет)?
│        ├─ нет → ПРЕДРЕНДЕР: видео-петля (без альфы: H.264/AV1), поверх контента — видео с альфой (VP9-alpha + HEVC/stacked),
│        │        фотореализм или тяжёлая сцена — всегда сюда (рендер Cycles не повторить в браузере)
│        └─ да  → РЕАЛТАЙМ, см. ниже (петля в JS или клип)
└─ да  → что двигается?
         ├─ объект целиком по простой кривой (вращение, парение, наклон, масштаб, параллакс) → JS: damp/синус/GSAP
         ├─ много частей с ручным таймингом, раскрытие, взрыв-схема, логотип из деталей → КЛИП BLENDER (одно действие со слотами),
         │    играть или скрабить `action.time`
         ├─ деформация формы (морф, лицо), персонаж → КЛИП BLENDER (shape keys / скелет) + кроссфейд
         ├─ ткань, бумага, разрушение → ЗАПЕЧЬ в морфы/VAT (реалтайм-скраб) или ПРЕДРЕНДЕР (секвенция/all-intra видео)
         ├─ камера по пути → JSON-кривая (по умолчанию) или запечённая камера (§3)
         ├─ цвет, свет, свечение, прозрачность → JS (треки материала, uniform)
         └─ продукт «как на фото», кадр в кадр по прокрутке → СЕКВЕНЦИЯ кадров (WebP/AVIF, окно памяти)
```

[практика; решения проверены на H/10–H/16, H/21; цены поставок — A/06, `../01-web-3d-landscape/05-… §2`]. Сама страница, прокрутка и
интерактив — F2 (`../09-web-runtime/`); загрузка и цена рантайма — F1; видео с альфой как формат — D2 (`../06-materials-lighting-render/`).

## 2. Эффекты каталога A: где делать движение

| эффект (каталог A §) | движение | где делать | почему / цена |
|---|---|---|---|
| 2.2 парящий/вращающийся hero | петля | JS (`sin`, `damp`) или клип Blender (H/11) | JS: 0 Б и параметры в коде; клип: 1–3 КБ, если тайминг задан аниматором |
| 2.3 hero от курсора | реакция | JS: `damp` к целевому повороту | клип не нужен; λ = 6–10 |
| 3.1 орбитальный вьюер | вращение | JS (OrbitControls) / model-viewer `auto-rotate` | без клипа |
| 3.5 взрыв-схема | разлёт по прокрутке | клип Blender (слоты, H/12) + скраб; или JS по конечным позициям из `extras` | клип хранит стаггер и изинги аниматора; JS — если нужна адаптивность |
| 3.6 горячие точки | нет (метки следуют) | пустышки Blender → узлы glTF | — |
| 4.1 путь камеры | пролёт | JSON-кривая → `CatmullRomCurve3` (H/14) | 1,4 КБ; запечённая камера 3,9 КБ (1 КБ после `gltfpack -af 10`) |
| 4.2 трансформации на прокрутке | поворот/приближение | JS (ScrollTrigger scrub / damp) | клип не нужен |
| 4.5 анимация Blender на прокрутке | хореография | клип Blender + `action.time = p·d` (H/21) | рецепт `paused + setTime` не работает (`03-… §3.3`) |
| 6.2 морфинг частиц | перетекание | шейдер (`uProgress`) по точкам из Blender | клип не нужен; точки — D1/F2 |
| 8.x 3D-текст, искажение | анимация букв | JS/шейдер; интро букв — клип или JS-таймлайн | как логотип (§4) |
| 11.3 физика и россыпь | интерактив | Rapier/cannon в JS; «кино» падения — запечённый клип | клип: ≈ 50–60 КБ на 20 тел × 90 кадров до resample (расчёт) |
| 12.1 маскот | Idle/Wave/Hover | клипы Blender (скелет) + `crossFadeTo` | 0,25–1 МБ на персонажа; 4 кости + 2 клипа — 36,6 КБ (H/30) |
| 12.2 лицо с морфами | мимика | shape keys → веса из кода (MediaPipe) | вершины × формы × 12–24 Б |
| 13.4 360° из кадров | поворот по drag | секвенция 24–72 кадров | 48 кадров WebP 183–386 КБ (A/06) |
| 14.1 секвенция на прокрутке | кадр в кадр | предрендер кадров | 100–300 кадров × 10–40 КБ; окно памяти |
| 15.1 видео-петля | петля | предрендер видео | 2 с 768² H.264 13–81 КБ (A/06) |
| 15.2 видео с альфой | поверх контента | VP9-alpha + HEVC/stacked | 1,5 с 512²: 24–34 КБ (H/16) |
| 15.3 прокрутка видео | скраб | all-intra видео или секвенция | ×3–4 к весу (A/06) |
| 21.1 запечённые симуляции | ткань/бумага | морфы (десятки форм) или VAT | `02-… §4.4` |
| логотип, айдентика | интро/петля | JS-таймлайн, клип или видео с альфой | §4 |

[источник строк: `../01-web-3d-landscape/01-effects-catalog.md` §23 и `05-blender-deliverables-map.md` §1 (агент A); цены — эксперименты A/06
и H]. Эффекты без Blender (шейдерные фоны, эффекты над картинками, CSS 3D) движутся шейдером/CSS — сюда не входят.

### 2.1 Простое движение без клипа: JS-шаблон

Вращение, парение и реакция на курсор одного объекта — три строки в цикле рендера; клип и реэкспорт не нужны, параметры адаптивны
(на телефоне — меньше амплитуда), reduced motion — одно условие.

```js
// three r186 — [проверено] турнтейбл, «парение» и наклон к курсору кодом (без клипа Blender)
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const gltf = await new GLTFLoader().loadAsync('float_pulse_sampled.glb');   // клипы файла не используем — только геометрия
const hero = gltf.scene.getObjectByName('hero_gem');
const base = hero.position.clone();
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const pointer = new THREE.Vector2();                                        // −1…1, обновляется в pointermove
let t = 0, tiltX = 0, tiltY = 0;
function animate(dt) {                                                       // dt = Math.min(timer.getDelta(), 0.1)
  if (reduce) return false;                                                  // статичный кадр
  t += dt;
  hero.rotation.y = (t / 12) * Math.PI * 2;                                  // турнтейбл: оборот за 12 с, линейно
  hero.position.y = base.y + 0.03 * Math.sin((t / 3.5) * Math.PI * 2);       // парение: ±3 см, период 3,5 с
  tiltX = THREE.MathUtils.damp(tiltX, pointer.y * 0.15, 8, dt);              // наклон к курсору, до ±0,15 рад
  tiltY = THREE.MathUtils.damp(tiltY, pointer.x * 0.15, 8, dt);
  hero.rotation.x = tiltX; hero.rotation.z = -tiltY;
  return true;
}
pointer.set(1, 0.5);
for (let i = 0; i < 180; i++) animate(1 / 60);                              // 3 с при 60 Гц
if (Math.abs(hero.rotation.y - Math.PI / 2) > 1e-6 || Math.abs(tiltY - 0.15) > 1e-3) throw new Error('шаблон дал не то');
console.log('через 3 с: поворот', THREE.MathUtils.radToDeg(hero.rotation.y).toFixed(1), '°, высота', hero.position.y.toFixed(4));
```

## 3. Камера на прокрутке: три способа

| способ | что отдаёт Blender | вес | точность относительно замысла | гибкость в JS |
|---|---|---|---|---|
| запечённая камера в GLB (Follow Path/Track To → ключи, `export_cameras=True`) | узел камеры + клип | 3,9 КБ клип (0,98 КБ после `gltfpack -af 10`) | точная копия (IoU кадров 0,999) | FOV фиксирован (yfov по соотношению сторон рендера); прогресс → `action.time` |
| JSON-кривая (позиции + точки взгляда в осях three) | `camera_path.json` | 1,4 КБ (25 + 25 точек) | 8 мм и 0,10° от запечённой камеры | свой easing, damp, FOV и отступы под экран, вставка секций |
| кривая, написанная в JS (без Blender) | ничего | 0 | «на глаз» | полная; подходит для 3–5 опорных точек |

[проверено]. Оси: Blender (x, y, z) → three (x, z, −y); точки брать у вычисленной кривой по
ИМЕНИ объекта, не у `active_object` (скрипт Codrops 2026-07-07 зависит от активного объекта — каталог A §4.1).

```python
# Blender 5.2.2 — [проверено] кривая Blender → JSON точек в осях three (для CatmullRomCurve3)
import os, json, tempfile
import bpy
cu = bpy.data.curves.new("cam_path", "CURVE"); cu.dimensions = "3D"; cu.resolution_u = 6
sp = cu.splines.new("BEZIER"); pts = [(-5, -4, 1.6), (-1.5, -2.6, 2.2), (1.5, -3.4, 1.4), (5, -2.2, 2.0)]
sp.bezier_points.add(len(pts) - 1)
for bp, p in zip(sp.bezier_points, pts):
    bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
path = bpy.data.objects.new("cam_path", cu); bpy.context.scene.collection.objects.link(path)
def curve_points_three(name):
    """Вычисленная кривая объекта name → [[x, z, −y], …] в мировых координатах (оси three, метры)."""
    ob = bpy.data.objects[name]                                   # по имени, не active_object
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg); me = oe.to_mesh()
    order = [me.vertices[i].co.copy() for i in range(len(me.vertices))]   # вершины кривой идут по порядку сплайна
    mw = oe.matrix_world.copy(); oe.to_mesh_clear()
    return [[round(v.x, 4), round(v.z, 4), round(-v.y, 4)] for v in (mw @ c for c in order)]
P = curve_points_three("cam_path")
out = os.path.join(tempfile.mkdtemp(), "camera_path.json")
json.dump({"points": P, "axes": "three-yup", "units": "m"}, open(out, "w"))
assert len(P) == 3 * cu.resolution_u + 1 and P[0] == [-5.0, 1.6, 4.0] and P[-1] == [5.0, 2.0, 2.2]
print(len(P), "точек,", os.path.getsize(out), "байт")
```

```js
// three r186 — [проверено] JSON-путь камеры: прогресс прокрутки → точка кривой и взгляд, damp
import * as THREE from 'three';

const path = await (await fetch('camera_path.json')).json();          // {points: [[x,y,z]…], targets: [[x,y,z]…]} в осях three
const along = new THREE.CatmullRomCurve3(path.points.map((p) => new THREE.Vector3(...p)), false, 'catmullrom', 0.5);
const look = new THREE.CatmullRomCurve3(path.targets.map((p) => new THREE.Vector3(...p)), false, 'catmullrom', 0.5);
const camera = new THREE.PerspectiveCamera(54.4, innerWidth / innerHeight, 0.05, 100);
let u = 0;
function placeCamera(progress, dt) {                                  // progress 0…1 из прокрутки; dt — из THREE.Timer
  u = THREE.MathUtils.damp(u, THREE.MathUtils.clamp(progress, 0, 1), 8, dt);
  along.getPoint(u, camera.position);                                 // getPoint: точки сняты равномерно по кадрам клипа
  camera.lookAt(look.getPoint(u));
}
for (let i = 0; i < 240; i++) placeCamera(0.5, 1 / 60);               // 4 с при 60 Гц — догнал середину пути
const mid = path.points[(path.points.length - 1) / 2];
if (camera.position.distanceTo(new THREE.Vector3(...mid)) > 0.01) throw new Error('середина пути не совпала: ' + camera.position.toArray());
console.log('камера на середине пути', camera.position.toArray().map((v) => v.toFixed(3)).join(', '));
```

Для экрана уже 16:9 вертикальный FOV glTF-камеры оставляет по бокам меньше сцены, чем в Blender (горизонт обрезается) — при JSON-пути
FOV и отступ считают от `camera.aspect` сами [практика: E `../08-export-gltf/01 §8.2`].

## 4. Моушн-брендинг: интро логотипа тремя способами

Одна анимация (монограмма «H» из трёх деталей + кольцо, 1,5 с, BACK/EXPO ease-out, стаггер 4 кадра) [проверено]:

| поставка | вес | точность | управляемость | условия |
|---|---|---|---|---|
| клип Blender в GLB (Meshopt) | 26,2 КБ (статика 22,3 + анимация 3,9) | эталон | пауза, скорость, скраб, реверс (`03-… §3`) | three на странице (≥ 110 КБ br) |
| статичный GLB + JS-таймлайн | 22,3 КБ + 1,5 КБ JS | ≤ 0,1 мм, 0,02° от клипа | полная: тайминг в коде, привязка к событиям | three на странице |
| VP9 с альфой (WebM) | 31,9 КБ | кадр Blender (EEVEE) | play/pause/currentTime | Chrome/Firefox/Edge; Safari — HEVC-alpha или stacked |
| stacked-alpha AV1 (MP4 512×1024) | 23,8 КБ | то же | то же | + 20 строк WebGL-шейдера для склейки альфы (A/06) |
| stacked-alpha HEVC | 34,2 КБ | то же | то же | запас для Safari |
| H.264 на фоне страницы | 22,1 КБ | фон «вшит» | то же | везде; фон должен совпасть с CSS |

Правила: (1) интро — однократно, 1–1,5 с, детали со стаггером 3–6 кадров, перелёт BACK 1,2–1,6 для «вставших на место» деталей,
EXPO ease-out для «выезжающих»; (2) деталь, появляющаяся из масштаба 0 по одной оси, оставляет полоску фаски (кадр 4 в H/16) — прятать
по всем осям или за другой деталью; (3) металл логотипа без HDRI тёмный — окружение обязательно (D2); (4) PNG-кадры (5,47 МБ на
46 кадров) — только исходник [проверено]. Генеративная айдентика кодом (шейдер, частицы) — вне Blender, `../09-web-runtime/`.

```bash
# ffmpeg 7.1.5 — [проверено] кадры RGBA из Blender (1…N−1 для петли) → видео с альфой и запасы
IN=out/frames/f_%04d.png
STACK="[0:v]format=pix_fmts=yuva444p[main];[main]split[main][alpha];[alpha]alphaextract[alpha];[main][alpha]vstack"
ffmpeg -loglevel error -y -framerate 30 -i $IN -pix_fmt yuva420p -c:v libvpx-vp9 -crf 40 -b:v 0 -deadline good -row-mt 1 -an out/logo_vp9_alpha.webm
ffmpeg -loglevel error -y -framerate 30 -i $IN -filter_complex "$STACK" -pix_fmt yuv420p -c:v libaom-av1 -cpu-used 6 -crf 40 -b:v 0 -movflags +faststart -an out/logo_stacked_av1.mp4
ffmpeg -loglevel error -y -framerate 30 -i $IN -filter_complex "$STACK" -pix_fmt yuv420p -c:v libx265 -preset medium -crf 28 -tag:v hvc1 -movflags +faststart -an out/logo_stacked_hevc.mp4
```

```js
// three r186 — [проверено] интро логотипа JS-таймлайном по timeline.json из Blender (без клипа)
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import {applyLogoPose} from './logo_timeline.js';                    // 1,5 КБ: изинги BACK/EXPO как в Blender

const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync('logo_static_meshopt.glb');
const TL = (await (await fetch('timeline.json')).json()).timeline;   // кадры и изинги, записанные скриптом Blender
const nodes = Object.fromEntries(['post_l', 'post_r', 'bar_mid', 'ring'].map((n) => [n, gltf.scene.getObjectByName(n)]));
const duration = 45 / 30;
let t = 0;
function tick(dt) {                                                  // в цикле rAF; reduced motion → сразу t = duration
  t = Math.min(t + dt, duration);
  applyLogoPose(t, TL, nodes);
  return t < duration;
}
while (tick(1 / 60));
if (Math.abs(nodes.post_l.position.y) > 1e-4 || Math.abs(nodes.ring.scale.x - 1) > 1e-4) throw new Error('конечная поза не достигнута');
console.log('интро завершено за', duration, 'с; кольцо', nodes.ring.scale.x.toFixed(3));
```

## 5. Длительности и кривые для 3D на странице

- Интерфейсное движение (кнопки, панели, модалки): 150/200/300 мс, вход ease-out, выход ease-in, цикл linear, пружины — только
  геометрия, цвет и прозрачность не пружинят — `../../ui/08-motion/01-durations-easings-springs.md` (не дублируем) [консенсус].
- 3D-сцены живут дольше интерфейса [мнение: практика H/10–H/16, каталог A]:

| движение | длительность | кривая | пример |
|---|---|---|---|
| интро логотипа, «вставание» деталей | 1–1,5 с, один раз | BACK/EXPO ease-out, стаггер 3–6 кадров (100–200 мс) | H/16 |
| раскрытие продукта | 1,5–2,5 с или по прокрутке | BACK ease-out на петлях, BEZIER на подъёмах | H/12 |
| «парение» | 3–4 с на цикл | синусоида (AUTO_CLAMPED), амплитуда 2–6 % высоты, наклон ≤ 5° | H/11 |
| пульсация CTA | 1–1,5 с + пауза | ease-out вверх, ease-in-out вниз, пик 1,15–1,25 | H/11 |
| турнтейбл | 8–20 с на оборот | LINEAR | H/10 (4 с — демонстрация) |
| пролёт камеры | длина прокрутки 100–150vh на «сцену» | damp λ = 6–10 поверх прогресса | H/14, H/21 |

- Колебания около 0,2 Гц (период ≈ 5 с) Apple советует избегать (visionOS) — для веба не проверено; «парение» с периодом 3–4 с
  лежит рядом, но это не VR [документация Apple через ui-research §8.4; мнение о переносе].
- Скорость реакции на курсор/прокрутку задаёт `damp` (λ): 10 — 99 % пути за 0,46 с, 6 — за 0,77 с [расчёт `ln(100)/λ`; проверено].

## 6. Reduced motion и доступность движения в 3D

- Скраб прокруткой: при `prefers-reduced-motion: reduce` — без инерции и промежуточных поз, сразу 0 или 1 (или кроссфейд
  прозрачностью) [проверено].
- Самозапускающиеся петли (турнтейбл, парение, пульс, видео): статичный кадр, `setAnimationLoop(null)`, видео — `pause()` на постере;
  автоматическое движение дольше 5 с параллельно с контентом требует механизма паузы (WCAG 2.2.2, уровень A); появление в области
  видимости считается автозапуском [стандарт: `../../ui/08-motion/03-reduced-motion-and-motion-tokens.md §2`].
- Мигание/вспышки свечения — не чаще 3 раз в секунду (WCAG 2.3.1) [стандарт].
- 13 из 16 наградных 3D-сайтов reduce игнорируют — это антиориентир [проверено: A `../01-web-3d-landscape/04-… §6`].

## Частые ошибки

1. Реалтайм-GLB + three ради бесконечной декоративной петли без взаимодействия — предрендер-видео легче в разы и не грузит GPU.
2. Видео ради эффекта, который скрабится прокруткой назад, — рывки (нужно all-intra или секвенция).
3. Клип Blender ради вращения или парения одного объекта — то же делает 3 строки JS, и параметры правятся без реэкспорта.
4. JS-анимация многодетального раскрытия «на глаз» — теряется тайминг аниматора; такие вещи делать клипом (слоты).
5. Цвет/свечение в клипе Blender — в three не играет (`KHR_animation_pointer`).
6. Запечённая камера при адаптивной вёрстке — на узком экране кадр обрезается; JSON-путь позволяет подстроить FOV.
7. Видео 512² на экране DPR 2 размером 512 CSS px — мыло; нужна двойная плотность.
8. Кадр N петли в видео — двойной кадр на стыке.
9. Интерфейсные 150–300 мс для 3D-раскрытия — «дёрг»; 3D-сцене нужны 1–2,5 с или привязка к прокрутке.
10. Нет reduced motion и паузы у петель > 5 с.

## Чек-лист

- [ ] Решено по дереву §1: пользователь управляет движением → реалтайм; нет → рассмотрен предрендер?
- [ ] Простое движение целых объектов сделано в JS, хореография частей и деформации — клипом Blender?
- [ ] Цвет/свет/свечение анимируются в JS?
- [ ] Камера на прокрутке — JSON-кривая (или обоснованно запечённая камера)?
- [ ] Логотип: выбран способ по наличию three на странице; у видео есть альфа для Chrome и Safari?
- [ ] Видео и секвенции отрендерены кадрами 1…N−1 и в двойной плотности?
- [ ] Длительности 3D — секунды (или прокрутка), интерфейсные токены не перенесены на сцену?
- [ ] Reduced motion: скраб без инерции, петли стоят, у длинных петель есть пауза?

## Открытые вопросы и противоречия

- Восприятие «клип против JS» для одного и того же движения не измерялось (у нас совпадение по позам 0,1 мм — визуально одинаково);
  выбор делается по управляемости и весу, а не по качеству.
- Числа длительностей 3D-движения — практика и мнение; исследований для 3D на сайтах не найдено; переносимость ограничения 0,2 Гц
  (visionOS) на веб не проверена.
- Доклады о моушн-брендинге (BCon 2024 `BjCRQ9EFubQ`) не прочитаны — решение заказчика об экономии; дайджест — у W9.
- Цена рантайма three (≥ 110 КБ br) против видео учтена по замерам A; на странице без WebGL выигрыш видео однозначен, на странице с three —
  нет.

## Источники

- [S1] Агент A, волна 1. `../01-web-3d-landscape/01-effects-catalog.md` (§1.4, §2–4, §12–15, §21, §23), `05-blender-deliverables-map.md` §1–3,
  эксперименты A/03 (вес рантаймов), A/06 (одна сцена во всех поставках: видео, секвенции, альфа) — внутренний, [проверено A].
- [S2] Агент E, волна 1. `../08-export-gltf/01-export-contract.md` §8.2 (камеры), §9.3 (pointer) — внутренний.
- [S3] mrdoob/three.js r186: `CatmullRomCurve3`, `MathUtils.damp`, анимационная система — заметки `99-raw/notes/wave2/H-sub/B-web-docs.md`; первичный.
- [S4] Codrops, «Building a Scroll-Driven 3D Gallery Using a Blender Camera Path», 2026-07-07 (через каталог A §4.1) — путь из Blender в JSON; практика.
- [S5] Codrops, T. Nagasawa, «Interactive Crumpled Paper Effect with Houdini VAT and Three.js», 2026-09-19 — предрендер/запекание симуляций; практика.
- [S6] J. Archibald, «Video with alpha transparency on the web», 2024-08-05 (через A `05 §3.15`) — форматы видео с альфой, stacked alpha; практика с замерами.
- [S7] `../../ui/08-motion/01-durations-easings-springs.md`, `03-reduced-motion-and-motion-tokens.md` — длительности, кривые, WCAG 2.2.2/2.3.1/2.3.3, «reduce, not remove»; соседняя база.
- [S8] Apple HIG Motion (0,2 Гц, visionOS) — через `../../ui-research/08-motion/01 §8.4`; документация.
- [S9] Эксперименты H: `10-turntable`, `11-float-pulse`, `12-reveal-parts`, `14-camera-path`, `16-logo-motion`, `21-scroll-page`, `30-doc-snippets` — [проверено].
