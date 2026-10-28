# Прокрутка, интерактив и анимация на странице: ScrollTrigger, Lenis, CSS scroll-driven, путь камеры и клип из Blender, курсор, damp

Волна 2 · агент F2 · 23.09.2026 · источников: 12 (лицензия GSAP, исходники Lenis 1.3.26 и three r186, MDN BCD, документация R3F/drei,
статья Codrops CurveGallery, заметки по 9 роликам, отчёты W3/W4/W7) · экспериментов: 5 (`99-raw/experiments/F2/03-camera-path`,
`06-anim-damp`, `08-css-scroll`, `02-r3f-hero`, `05-fx-lab`) · версии: three r186, GSAP 3.15.0 (ScrollTrigger), Lenis 1.3.26,
Blender 5.2.2 (glTF-IO 5.2.40), gltfpack 1.2, Chromium 153 headless (Iris Xe).
Что приходит из Blender (клипы, морфы, скелет, слоты действий) — `../07-animation/` (H); загрузка, цикл отрисовки, доступность —
`01-threejs-core.md` и `05-performance-a11y-fallbacks.md` (F1); длительности и кривые UI — `../../ui/08-motion/`.

## Выжимка для агента

1. **Демо-эталон — `examples/camera-path-scroll`**: кривая из Blender (JSON 2,7 КБ) → `CatmullRomCurve3`, клип сборки из Blender →
   `mixer.setTime`, hover по именам узлов, GSAP ScrollTrigger + Lenis; 0 вызовов отрисовки в покое, 60 fps и 7–12 вызовов при
   прокрутке, LCP 92 мс (текст), TBT 323 мс → §2, §5, §6. [проверено]
2. **Прокрутка — только источник прогресса**: ScrollTrigger (`onUpdate: st => ref.target = st.progress`) пишет число в ref/uniform;
   движение считает цикл кадра с `damp`; никакого React-состояния и твинов на каждый кадр → §2. [проверено: F2/03; практика Shopify]
3. **Связка Lenis + ScrollTrigger**: `lenis.on('scroll', ScrollTrigger.update); gsap.ticker.add(t => lenis.raf(t * 1000));
   gsap.ticker.lagSmoothing(0)`; Lenis 1.3.26 сам уважает reduce (`respectReducedMotion: true`), пакет — `lenis`, не
   `@studio-freight/lenis` → §2.1. [проверено: F2/03; исходник Lenis]
4. **Рендер по требованию на прокрутке**: рисуй кадр, только если изменились прогресс, курсор или размер (`|t − tPrev| > 1e-5`) —
   в покое 0 вызовов, при reduce кадры только на смене «станции» → §2.2. [проверено]
5. **Плавность — `THREE.MathUtils.damp(x, target, λ, dt)`**, не `lerp(x, target, k)` на кадр: `lerp 0.1` на 144 Гц через 0,25 с —
   97,7 % пути, `damp` — 79,4 % на любой частоте; перевод `λ = −ln(1 − k)·60`, 95 % пути за `3/λ` с → §4. [проверено]
6. **Путь камеры — кривая Безье в Blender → точки вычисленной кривой → JSON `[x, z, −y]`** (объект по имени, `resolution_u` задаёт
   плотность, 97 точек = 2,7 КБ) → `new CatmullRomCurve3(points, false, 'catmullrom', 0.5)`, `getPointAt(u)` (равномерно по длине) и
   взгляд на точку `u + 0,04` → §5. [проверено]
7. **Скраббинг клипа: `action.play()` один раз, затем `mixer.setTime(clamp(p) · (duration − 1e-4))`**; `action.paused = true` + `setTime`
   клип НЕ двигает (x = 0 вместо 5), `LoopOnce + clampWhenFinished` после конца сам ставит паузу, `LoopRepeat` на `setTime(duration)`
   заворачивается в 0 → §6. [проверено: F2/06 по исходнику r186]
8. **Один клип на все части** из Blender — `export_animation_mode="ACTIVE_ACTIONS"` (клип «Animation»), позы — кадры 1…N, `export_anim_slide_to_zero`;
   поза покоя GLB = кадр 0 (разлёт) — управляй `setTime` с первого кадра → §6. [проверено: F2/03; E `08-export-gltf/01` §9]
9. **Имена узлов из Blender управляют JS**: `ring_N` — кликабельные, `hotspot_N` с Custom Property `label` → `userData.label`
   (`export_extras=True`), сжатие только `gltfpack -cc -kn -ke` (421 → 33 КБ, имена и extras целы); после квантования меш — ребёнок
   узла: при рейкасте поднимайся по `parent` до имени → §7. [проверено]
10. **CSS scroll-driven animations хватает для DOM-эффектов** (полоса прогресса, появление/наклон карточки, параллакс слоёв):
    `animation-timeline: scroll()` / `view()`, 0 JS; Chrome 115+, Safari 26+, Firefox — только preview → запас: элемент в конечном
    состоянии → §3. [проверено: F2/08; документация MDN BCD]
11. **`ScrollTimeline` из JS отдаёт прогресс в процентах** (`currentTime = {value: 50, unit: 'percent'}`) — можно кормить uniform без
    обработчика `scroll` (опрос в цикле кадра), но только в Chrome/Safari 26 → §3.2. [проверено]
12. **Лицензия GSAP (Webflow, «Standard No Charge»)**: разрешено на любых сайтах, включая коммерческие; запрещено — инструменты
    визуального создания анимаций без кода, конкурирующие с Webflow; код GSAP, написанный ИИ, прямо разрешён → система,
    генерирующая сайты с GSAP, — разрешено; сама система как визуальный конструктор анимаций на GSAP — юридическая проверка → §2.3.
    [документация; спорно]
13. **drei `ScrollControls`** — свой контейнер прокрутки внутри canvas; для лендинга с HTML-контентом — нативная прокрутка + ScrollTrigger
    (+ Lenis) → §1. [документация drei]
14. **Курсор**: нормированные координаты → цель, `damp(λ = 3…8)` → смещение камеры 0,15–0,25 м или uniform; на тач-экранах
    (`pointerType === 'touch'`) параллакс и hover выключать → §7. [проверено]
15. **Рейкаст только по кликабельному**, не по всей сцене: массив узлов `ring_N` (или невидимые увеличенные hit-области, сферы у
    Bruno Simon), пересчёт только при движении курсора или камеры → §7. [проверено: F2/03; V:5uTwZVGgDpA 26:10; V:EhZwt9P4GP4 15:01]
16. **Reduce для каждого приёма** (§8): полёт камеры → 5 «станций» без инерции; клип → конечная поза; параллакс, `Float`, автоповорот →
    выкл.; Lenis → сам без сглаживания; CSS scroll-driven — только внутри `@media (prefers-reduced-motion: no-preference)`. [проверено]
17. **Сюжет на прокрутке режь на сегменты по экранам**: жёстко привязанный к скроллу таймлайн оставляет пользователя «в нелепой
    промежуточной позе» при остановке; сегмент = экран, внутри — короткая анимация [V:5uTwZVGgDpA 09:44–13:03]. [практика]
18. **Физика — только когда она и есть эффект** (россыпь, толкание): Rapier wasm 0,5–2,4 МБ, `@react-three/rapier` 2.2.0; cannon-es
    не обновлялся с 2022-08; для «пружинки» при наведении хватает `damp` → §9. [проверено: npm; A `01` §11.3]

## 1. Какой механизм прокрутки брать

| Задача | Механизм | JS | Почему |
|---|---|---|---|
| Полоса прогресса, появление и наклон карточек, параллакс DOM-слоёв | CSS `animation-timeline: scroll()/view()` | 0 | идёт на композиторе; reduce — `@media` [проверено F2/08] |
| 3D-сцена за HTML-контентом: путь камеры, клип, uniform | ScrollTrigger (прогресс) + цикл кадра с `damp` | gsap + ST 40 КБ br | точный прогресс, `pin`, `scrub`, `matchMedia` [проверено F2/03] |
| Плавное колесо, синхрон DOM ↔ WebGL | + Lenis | 4,9 КБ br | нативный скролл не кадр-синхронен (Codrops 2025-06-05, A) [практика] |
| Полноэкранная история целиком в canvas (R3F) | drei `ScrollControls` + `useScroll` | в составе drei | свой контейнер прокрутки; HTML — внутри `<Scroll html>` [документация] |
| Прогресс без GSAP в Chrome/Safari 26 | `ScrollTimeline` в JS | 0 | нет Firefox → запас на `scroll`-событии [проверено F2/08] |
Не выбирать: Theatre.js (заморожен с 2024, studio — AGPL), `framer-motion-3d` (снят) — A `03` §10.

## 2. GSAP ScrollTrigger + Lenis + three r186

### 2.1. Связка и цикл кадра
```js
// three r186 + GSAP 3.15 + Lenis 1.3.26 — [проверено: 09-web-runtime/examples/camera-path-scroll (ядро страницы)]
import * as THREE from 'three';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

gsap.registerPlugin(ScrollTrigger);
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const state = { target: 0, t: 0, dirty: true };
ScrollTrigger.create({ trigger: '#track', start: 'top top', end: 'bottom bottom',
  onUpdate: (st) => { state.target = st.progress; state.dirty = true; } });   // прокрутка → только число
const lenis = new Lenis();                                   // respectReducedMotion: true по умолчанию
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add((time) => lenis.raf(time * 1000));           // один источник rAF для Lenis и ScrollTrigger
gsap.ticker.lagSmoothing(0);

let last = performance.now();
function tick(render) {
  const now = performance.now(), dt = Math.min((now - last) / 1000, 0.1); last = now;
  const target = reduce.matches ? Math.round(state.target * 4) / 4 : state.target;   // reduce: 5 «станций»
  const prev = state.t;
  state.t = reduce.matches ? target : THREE.MathUtils.damp(state.t, target, 4, dt);  // 95 % пути за 0,75 с
  if (Math.abs(state.t - prev) < 1e-5 && !state.dirty) return;                       // 0 вызовов в покое
  state.dirty = false;
  render(state.t);
}
window.__scrollTick = tick;                                  // в демо: gsap.ticker.add(() => tick(place));
```
- `scrub: true` у ScrollTrigger без сглаживания: сглаживание делает `damp` в цикле (не зависит от герцовки); `scrub: 1` — то же силами
  GSAP (твин догоняет за 1 с) [практика].
- Замер (Iris Xe, 1440×900): прокрутка 60 fps, 7 (медиана) / 12 (макс.) вызовов, p95 кадра 16,8 мс; Pixel 7 + CPU×4 — 59 fps
  (первый прогон 26 fps — нагрузка общей машины, повтор чистый); без Lenis (`?nolenis`) — те же 59 fps [проверено].
- `pin: true` для закреплённых секций — не проверялось здесь; Shopify Editions держит смонтированными только активную и соседние сцены
  (A `01` §4.3) [практика].

### 2.2. Рендер по требованию и стоп вне экрана
Цикл выше рисует только при изменении: в покое 0 вызовов (идёт только опрос `gsap.ticker`), движение 0 % пикселей; стоп при
`IntersectionObserver` (canvas вне вида) и `document.hidden`; `resize` ставит `dirty` [проверено]. Шаблон цикла для
статичных сцен — F1 `05-performance-a11y-fallbacks.md` §3.

### 2.3. Лицензия GSAP — дословно
«Permitted Uses» means the implementation and/or use of GSAP Products on any website, web application, or digital interface by any
person or entity … «Prohibited Uses» means any implementation and/or use of GSAP Products in tools that allow users to build visual
animations without code that encourages, induces, or materially assists in creating a solution that competes with Webflow's visual
animation building capabilities. FAQ: «Is it acceptable for AI tools like ChatGPT, Cursor, Lovable, Webstudio, etc. to generate GSAP
code? Absolutely! AI-generated code is not a "Prohibited Use".» Webflow вправе менять лицензию публикацией новой редакции
[документация: gsap.com/standard-license, кэш A, редакция 2025].
Условие для системы генеративного дизайна: сайты, которые она собирает с GSAP, — разрешённое использование; если продукт даёт
пользователю визуальный конструктор анимаций на GSAP, конкурирующий с Webflow, — зона запрета → решение юриста заказчика; запасной
вариант без GSAP — ScrollTimeline/CSS (§3) + свой прогресс на `scroll` [спорно].

## 3. CSS scroll-driven animations

### 3.1. Где их хватает
```css
/* Chrome 115+, Safari 26+ — [проверено] 0 JS, reduce — через @media */
.bar { position: fixed; top: 0; left: 0; height: 6px; width: 100%; transform-origin: 0 50%; transform: scaleX(0); }
@media (prefers-reduced-motion: no-preference) {
  .bar { animation: grow linear both; animation-timeline: scroll(root block); }
  .card { animation: tilt linear both; animation-timeline: view(); animation-range: entry 0% cover 50%; }
}
@keyframes grow { to { transform: scaleX(1); } }
@keyframes tilt { from { transform: perspective(800px) rotateX(35deg) translateY(80px); opacity: 0; } to { transform: none; opacity: 1; } }
```
Результат: на 50 % прокрутки полоса `scaleX(0.5)`, карточка видна полностью; при reduce анимация не применяется, элементы в
конечном состоянии [проверено]. Поддержка: `animation-timeline` и `ScrollTimeline` — Chrome/Edge 115+, Safari/iOS 26+, Firefox —
только preview (MDN BCD, 23.09.2026) [документация]. Без поддержки свойство игнорируется: `.card` без анимации видна сразу —
безопасный запас; `.bar` остаётся `scaleX(0)` — невидимой.
Ограничения: только DOM и CSS-свойства (canvas не получит прогресс); «появление при прокрутке» — автозапуск по WCAG 2.2.2 и
2.3.3 (`../../ui-research/08-motion/03` §2.2): на лендинге допустимо, на каждом блоке — клише [документация ui-research].

### 3.2. Прогресс для WebGL без обработчика scroll
```js
// Chrome 115+/Safari 26+ — [проверено] currentTime = {value: 0…100, unit: 'percent'}
const timeline = window.ScrollTimeline ? new ScrollTimeline({ source: document.documentElement, axis: 'block' }) : null;
function scrollProgress() {                                   // вызывать в цикле кадра
  if (timeline && timeline.currentTime) return timeline.currentTime.value / 100;
  const max = document.documentElement.scrollHeight - innerHeight;   // запас (Firefox)
  return max > 0 ? scrollY / max : 0;
}
window.__scrollProgress = scrollProgress;
```

## 4. Плавность: damp, пружины, частота кадров

| Частота | `lerp(x, 1, 0.1)` на кадр | `damp(x, 1, 6.32, dt)` |
|---|---|---|
| 30 Гц, t = 0,5 с | 0,794 | 0,958 |
| 60 Гц, t = 0,25 с | 0,794 | 0,794 |
| 144 Гц, t = 0,25 с | 0,977 | 0,794 |
[проверено: 99-raw/experiments/F2/06-anim-damp, Node + three 0.186.0]

- Формула r186: `damp(x, y, λ, dt) = lerp(x, y, 1 − exp(−λ·dt))` (`src/math/MathUtils.js`) [проверено: исходник]; перевод из «k на кадр
  при 60 Гц»: `λ = −ln(1 − k)·60` (k 0,1 → 6,32; 0,05 → 3,08); 95 % пути за `ln 20 / λ ≈ 3/λ` с. Ориентиры: камера за прокруткой
  λ 3–5 (0,6–1 с), курсор-параллакс λ 3–8, сила hover-эффекта λ 6–8 [проверено F2/03, F2/05; ориентиры — мнение F2].
- dt ограничивать сверху (`min(dt, 0.1)`): после неактивной вкладки не «прыгать» [практика].
- Пружина с перелётом (UI-кнопки, `PresentationControls`: mass 1, tension 170, friction 26) — только для геометрии; цвет и
  прозрачность не пружинят; параметры и перевод в CSS `linear()` — `../../ui-research/08-motion/01` §4 [документация ui-research].
- Idle-движение без «машинности»: периоды без общих делителей, `cos³` [V:8--5LwHRhjk 13:07, 14:09]; не колебать с периодом ≈ 5 с
  (0,2 Гц, Apple) [документация ui-research]; две скорости шума во времени [V:LW9d2cqIHb4 23:06].

## 5. Путь камеры из Blender

### 5.1. Экспорт кривой (Blender 5.2.2)
```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/F2/03-camera-path/build_scene.py; блок прогнан отдельно]
import bpy, json, os, tempfile

def export_curve_json(name, path, samples_per_segment=24):
    """Кривая по имени → JSON точек вычисленной кривой в осях three (x, z, −y), метры."""
    ob = bpy.data.objects[name]                       # по имени, не active_object
    ob.data.resolution_u = samples_per_segment
    deps = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(deps)
    me = ev.to_mesh()
    pts = [ob.matrix_world @ v.co for v in me.vertices]   # вершины по порядку сплайна
    ev.to_mesh_clear()
    data = {"name": name, "closed": bool(ob.data.splines[0].use_cyclic_u), "units": "m", "axes": "three-yup",
            "count": len(pts), "points": [[round(p.x, 4), round(p.z, 4), round(-p.y, 4)] for p in pts]}
    with open(path, "w") as f:
        json.dump(data, f)
    return data

# самопроверка: кривая из 3 точек Безье → 2 сегмента × 24 + 1 = 49 точек
cu = bpy.data.curves.new("demo_path", "CURVE"); cu.dimensions = "3D"
sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
for bp, co in zip(sp.bezier_points, [(0, 4, 1), (1, 0, 1.2), (0, -4, 1)]):
    bp.co = co; bp.handle_left_type = bp.handle_right_type = "AUTO"
bpy.context.scene.collection.objects.link(bpy.data.objects.new("demo_path", cu))
out = export_curve_json("demo_path", os.path.join(tempfile.gettempdir(), "demo_path.json"))
assert out["count"] == 49 and out["points"][0] == [0.0, 1.0, -4.0], out["points"][0]
print("export_curve_json ok", out["count"])
```
- Z-up → Y-up: `(x, y, z)_Blender → (x, z, −y)_three` — без этого путь «лежит на боку» [проверено]. Альтернатива —
  анимированная камера (Follow Path, `export_bake_animation=True`) → клип камеры; JSON-кривая проще: 2,7 КБ, взгляд и скорость
  задаются в JS, путь не зависит от fps клипа [мнение F2].
- Сплайн, построенный в JS по 5 опорным точкам, годится для абстрактной сцены; если путь должен проходить сквозь объекты сцены
  (кольца, двери), рисуй его в Blender рядом с ними — промахи видны сразу [практика: Codrops CurveGallery 2026-07-07].

### 5.2. Камера на кривой
```js
// three r186 — [проверено: 09-web-runtime/examples/camera-path-scroll] path = содержимое cam_path.json
import * as THREE from 'three';
export function makeCameraRig(path, camera, lookTarget = null) {
  const curve = new THREE.CatmullRomCurve3(path.points.map((p) => new THREE.Vector3(...p)), path.closed, 'catmullrom', 0.5);
  const pos = new THREE.Vector3(), ahead = new THREE.Vector3(), look = new THREE.Vector3();
  return function place(t) {                         // t ∈ [0, 1] — прогресс прокрутки после damp
    const u = Math.min(t / 0.8, 1);                  // 0–80 % прокрутки — полёт, остаток — финальная сцена
    curve.getPointAt(u, pos);                        // равномерно по длине (arc length), не по параметру
    curve.getPointAt(Math.min(u + 0.04, 1), ahead);  // взгляд на точку впереди
    look.copy(ahead);
    if (lookTarget) look.lerp(lookTarget, THREE.MathUtils.smoothstep(t, 0.7, 1.0));   // к концу — на объект
    camera.position.copy(pos);
    camera.lookAt(look);
    return curve;
  };
}
```
Найдено глазами при проверке F2/03: (1) кольца с центром 1,2 м при радиусе 1,25 + 0,07 «проросли» в пол — на пролёте низ кольца
выглядел прямой «хордой» (ошибка M2.3 каталога C1) → центр = R + r; (2) конец пути в 1,2 м от финального объекта при FOV 50° —
объект во весь кадр → дистанция 3,2 м (≈ 50 % высоты кадра) [проверено].

## 6. Скраббинг клипа glTF прокруткой

| Способ (клип 2 с, x 0 → 10) | x при t = 1 с | Вывод |
|---|---|---|
| `action.play(); action.paused = true; mixer.setTime(1)` | **0** | не работает (у паузы `timeScale` 0) |
| `action.play(); mixer.setTime(1)`, затем `setTime(0.5)` | 5 → 2,5 | работает в обе стороны |
| `paused = true; action.time = 1.5; mixer.update(0)` | 7,5 | работает |
| `LoopOnce + clampWhenFinished`: `setTime(2)`, затем `setTime(1.9999)` | 10 → **0** | после конца действие само встаёт на паузу |
| `LoopRepeat`: `setTime(duration)` | **0** | конец заворачивается в начало |
[проверено: 99-raw/experiments/F2/06-anim-damp, исходник `AnimationMixer.setTime` / `AnimationAction._updateTimeScale` r186]

```js
// three r186 — [проверено: 99-raw/experiments/F2/06-anim-damp и examples/camera-path-scroll]
import * as THREE from 'three';
export function makeScrubber(root, clip) {
  const mixer = new THREE.AnimationMixer(root);
  mixer.clipAction(clip).play();                      // LoopRepeat по умолчанию; НЕ paused
  const end = clip.duration - 1e-4;                   // не дойти до заворота в 0
  return (p) => mixer.setTime(THREE.MathUtils.clamp(p, 0, 1) * end);   // mixer.update() в цикле не вызывать
}
// в цикле кадра: scrub((t - 0.78) / 0.22) — клип на последних 22 % прокрутки; reduce → scrub(1) (конечная поза)
```
- Независимое подтверждение — агент H (H/20, H/21, three r186): `paused = true` + `setTime` даёт позу кадра 0; его рецепт —
  `action.play()` один раз, затем `action.time = p · duration; mixer.update(0)`; `LoopOnce + clamp` застревает при прокрутке назад;
  клип брать `THREE.AnimationClip.findByName(gltf.animations, 'имя')` (`mixer.clipAction('имя')` без клипа вернёт null). Подробно и
  готовая страница (60 fps, reduce, рендер по требованию) — `../07-animation/03` §3, `99-raw/experiments/H/21-scroll-page/` [проверено H].
- Blender: все части — отдельные объекты с origin в центре детали; ключи кадров 1 (разлёт) и 60 (сборка) @30 fps;
  `export_animation_mode="ACTIVE_ACTIONS"` → один клип «Animation» 1,967 с на 9 треков; у детали без поворота трек вращения
  выброшен оптимизацией экспортёра [проверено]. Много клипов и NLA — H `../07-animation/`, E `08-export-gltf/01` §9.
- Анимацию материалов и света (`KHR_animation_pointer`) three r186 не играет — такие свойства анимировать в JS (E §9.3).
- Секвенция кадров на прокрутке — загрузчик с окном памяти у F1 (`06-…`); индекс кадра = `round(p · (N − 1))`, рисовать только при
  смене индекса [практика].

## 7. Курсор, наклон, hover и имена узлов

### 7.1. Hover по именам из Blender
```js
// three r186 — [проверено: 09-web-runtime/examples/camera-path-scroll] rings = узлы ring_N, labels из userData hotspot_N
import * as THREE from 'three';
export function makePicker(root, camera, pattern = /^ring_\d+$/) {
  const targets = [], labels = {};
  root.traverse((o) => {
    if (pattern.test(o.name)) targets.push(o);
    if (o.name.startsWith('hotspot_')) labels['ring_' + o.name.split('_')[1]] = o.userData.label;   // extras → userData
  });
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  return function pick(clientX, clientY) {           // вызывать при движении мыши или камеры, не каждый кадр
    ndc.set((clientX / innerWidth) * 2 - 1, -(clientY / innerHeight) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    let o = ray.intersectObjects(targets, true)[0]?.object || null;
    while (o && !pattern.test(o.name)) o = o.parent;  // после gltfpack меш — ребёнок узла с именем
    return o ? { node: o, label: labels[o.name] || o.name } : null;
  };
}
```
- Подсветка — `material.emissive.copy(material.color); emissiveIntensity = 0.35` на время hover; подпись — DOM-элемент у курсора
  (`aria-hidden`, смысл — в HTML-секциях); `pointerType === 'touch'` → без hover [проверено: F2/03: hover 12 вызовов/кадр].
- Соглашение имён (Blender → JS): `латиница_через_подчёркивание` без точек (`Cube.001` → `Cube001`), префиксы `hotspot_*`
  (метки), `collider_*` (упрощённые формы для рейкаста/физики), `cam_*` (точки камеры), `zone_*` (пустышка Empty Circle — зона,
  которую JS сравнивает с проекцией кадра, у Bruno Simon — для отсечения и сна физики [V:EhZwt9P4GP4 09:38–11:44]); смысл
  дублируется Custom Property (`e['label']`), потому что имя санитизируется [проверено F2/03; E `01` §10; практика].

### 7.2. Параллакс, наклон, «магнит»
```js
// three r186 — [проверено: 99-raw/experiments/F2/05-fx-lab (hover) и F2/03 (параллакс)] курсор → damp → камера/uniform
import * as THREE from 'three';
export function makePointerFollower(lambda = 3) {
  const target = new THREE.Vector2(), value = new THREE.Vector2();
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  addEventListener('pointermove', (e) => {
    if (e.pointerType === 'touch') return;          // нет hover на тач-экранах
    target.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  });
  return (dt) => {                                  // в цикле кадра; возвращает сглаженное значение −1…1
    if (reduce.matches) return value.set(0, 0);
    value.x = THREE.MathUtils.damp(value.x, target.x, lambda, dt);
    value.y = THREE.MathUtils.damp(value.y, target.y, lambda, dt);
    return value;
  };
}
// camera.position.x = base.x + v.x * 0.25; camera.position.y = base.y + v.y * 0.15 (F2/03)
```
- Наклон DOM-карточки — CSS `perspective` + `rotateX/Y` от курсора, 0 КБ WebGL; «магнитная» кнопка — клише 2021–2024 (A `01` §10.1).
- Телефон: гироскоп (`DeviceOrientationEvent`, на iOS — запрос разрешения жестом) или без эффекта [не проверено].

## 8. Reduce для каждого приёма

| Приём | Обычный режим | `prefers-reduced-motion: reduce` | Проверено |
|---|---|---|---|
| Полёт камеры по пути | `damp(λ 4)` за прокруткой | 5 «станций» (`round(p·4)/4`), без инерции; кадры только на смене | F2/03: 0 вызовов в покое |
| Клип на прокрутке | `setTime` по прогрессу | конечная поза (`scrub(1)`) или по станциям | F2/03 |
| Параллакс от курсора | `damp(λ 3)` | 0 | F2/03 |
| Hover-подсветка | подсветка + подпись | оставить (не движение), без анимации | F2/03 |
| Lenis | сглаживание колеса | сам: без сглаживания (`respectReducedMotion`) | исходник Lenis |
| CSS scroll-driven | анимация | в `@media (… no-preference)`, иначе конечное состояние | F2/08 |
| R3F `Float`, `PresentationControls` | движение | `speed={0}`, `enabled={false}`, `frameloop="demand"` | F2/02: 0 вызовов |
| Шейдерный фон | время идёт | один кадр, цикл стоп | F2/04: 0 вызовов |
| Автоповорот, idle-анимации | цикл | стоп | F2/05 (общий цикл) |
Правило: reduce — не «выключить 3D», а убрать самопроизвольное и пространственное движение; изменения по прозрачности и цвету
допустимы (`../../ui-research/08-motion/03` §3.2).

## 9. Физика: когда стоит своих КБ

- Rapier (`@dimforge/rapier3d-compat` 0.20.0, `@react-three/rapier` 2.2.0): wasm 0,5–2,4 МБ на наградных сайтах; cannon-es 0.20.0 не
  обновлялся с 2022-08 [проверено: npm view F2/01; A `01` §2.3, §11.3]. Bruno Simon выбрал Rapier, синхронизирует миры копированием
  позиций и кватернионов [V:OBZtVz6IM18 06:13–09:26], физику вне кадра усыпляет [V:EhZwt9P4GP4 11:44].
- Брать, когда физика — суть эффекта (россыпь объектов, толкание курсором, мини-игра); не брать для «пружинки» при наведении, парения
  и сборки по прокрутке — это `damp`, клип Blender или GSAP. Коллайдеры — простыми формами-пустышками из Blender (`collider_*`), не
  по визуальной сетке [практика; A `01` §11.3]. Код физики здесь не проверялся.

## Частые ошибки

- **`action.paused = true; mixer.setTime(p · duration)`** — клип стоит на кадре 0 (совет каталога A §4.5 неверен) [проверено F2/06].
- **`LoopOnce` + `clampWhenFinished` для скраббинга** — после первого доезда до конца прокрутка назад не работает [проверено].
- **`setTime(duration)` при `LoopRepeat`** — последний кадр прокрутки показывает начало клипа [проверено].
- **`lerp(x, target, 0.1)` в `requestAnimationFrame`** — разная скорость на 60/120/144 Гц (Freya Holmér «Lerp smoothing is broken»,
  2024; формула проверена по исходнику r186) [проверено F2/06].
- **React-состояние или новый твин GSAP на каждый кадр прокрутки** — лаги; прогресс в ref, `gsap.quickTo` для повторяющихся твинов (A `01` §4.1).
- **Путь из Blender без смены осей** — сцена «на боку»; объект пути через `active_object` — в фоне его нет [проверено F2/03].
- **gltfpack без `-kn -ke`** — имена `ring_N` и `userData.label` пропадают, hover по именам ломается (E/28).
- **Рейкаст по всей сцене каждый кадр** — CPU; только кликабельные узлы и только при движении.
- **Постоянный рендер 60 fps за статичной прокруткой** — 25 из 33 наградных сайтов так делают (A `04` §6); здесь 0 вызовов в покое.
- **Нейросеть по памяти**: `@studio-freight/lenis`, `new Lenis({ smooth: true })` (старые опции), `ScrollTrigger` без `registerPlugin`,
  `THREE.Clock` вместо `THREE.Timer` [документация npm/A].

## Чек-лист

- [ ] Прокрутка даёт только прогресс (ref/uniform), движение — `damp` в цикле кадра, dt ограничен 0,1 с?
- [ ] В покое 0 вызовов отрисовки (рендер по изменению), вне экрана и в скрытой вкладке цикл стоит?
- [ ] Путь камеры — JSON из Blender в осях three, `getPointAt` (по длине), ничто не пересекает путь и пол?
- [ ] Клип: `play()` без паузы, `setTime(clamp(p) · (duration − 1e-4))`, `mixer.update` не вызывается?
- [ ] Имена узлов `латиница_через_подчёркивание`, `export_extras=True`, gltfpack `-kn -ke`, рейкаст с подъёмом по `parent`?
- [ ] Для каждого приёма есть вариант reduce из §8; CSS scroll-driven — внутри `@media (prefers-reduced-motion: no-preference)`?
- [ ] Firefox (нет `animation-timeline`) видит конечное состояние элементов, а не пустоту?
- [ ] Лицензия GSAP проверена под продукт (сайт — можно; визуальный конструктор анимаций — юрист)?
- [ ] Замер: `web_view.py --page` (60 fps, вызовы при прокрутке), `fx_probe.py --modes desktop,mobile,reduce` (0 вызовов в покое)?

## Открытые вопросы и противоречия

- Каталог A (`01-effects-catalog.md` выжимка п. 12, §4.5) советует `action.paused = true; mixer.setTime(...)` — опровергнуто F2/06;
  правка — за аудитором X.
- `pin` ScrollTrigger с canvas за DOM, горизонтальная прокрутка секций и `ScrollTrigger.matchMedia`/`gsap.matchMedia` для reduce — не
  проверялись.
- Первый мобильный прогон камеры (26 fps при CPU×4) против повторных 59 fps — шум общей машины; на реальных телефонах не мерили.
- Firefox без `animation-timeline` (только preview) — сроки стабильной поддержки неизвестны.
- Лицензия GSAP для продукта «генеративный дизайн» — вопрос юристу заказчика, позиция базы — [спорно].
- Физика (Rapier) и гироскоп на телефоне — только документация и замеры A.

## Источники

- [S1] GSAP «Standard No Charge License» и FAQ, gsap.com/standard-license (редакция 2025, кэш `99-raw/cache/gsap.com_standard-license_…`) — [документация].
- [S2] Lenis 1.3.26, исходник `dist/lenis.mjs` (опции конструктора: `lerp 0.1`, `autoRaf false`, `respectReducedMotion true`) — [проверено: исходник].
- [S3] three r186 (0.186.0): `src/math/MathUtils.js` (`damp`), `src/animation/AnimationMixer.js` (`setTime`), `AnimationAction.js` — [проверено].
- [S4] MDN browser-compat-data: `css/properties/animation-timeline.json`, `api/ScrollTimeline.json` (GitHub main, 23.09.2026) — [документация].
- [S5] drei docs: ScrollControls, Float, PresentationControls (10.7.8); R3F docs: pitfalls, scaling-performance — [документация].
- [S6] Codrops, «Building a Scroll-Driven 3D Gallery Using a Blender Camera Path», 2026-07-07 (через A `01` §4.1 и `05` §3.9) — [практика].
- [S7] Эксперименты F2: 03-camera-path, 06-anim-damp, 08-css-scroll, 02-r3f-hero, 05-fx-lab — [проверено].
- [S8] E `../08-export-gltf/01` §9–10 (клипы, extras, имена), E/28 (gltfpack `-kn -ke`) — [проверено E].
- [S9] `../../ui-research/08-motion/01` (пружины, длительности), `03` (reduce, WCAG 2.2.2/2.3.3) — [документация ui-research].
- [S10] Видео (заметки `99-raw/notes/wave2/F2-video-A/B/C.md`): И. Тельтевский «Пять приёмов» [V:5uTwZVGgDpA 07:37–13:03, 26:10];
  B. Simon Devlog 1 [V:OBZtVz6IM18 06:13–09:26], Devlog 13 [V:EhZwt9P4GP4 09:38–15:01]; Ю. Артюх «Stripe gradients» [V:LW9d2cqIHb4 23:06];
  I. Quilez [V:8--5LwHRhjk 13:07, 14:09]; Wawa Sensei [V:pXpckHDDNYo]; P. Henschel [V:YyqBdN71nFs 21:16–21:42].
- [S11] Отчёты W3, W4, W7 (разделы «→ F2»), 23.09.2026 — [дайджесты видео].
- [S12] F. Holmér, «Lerp smoothing is broken» (2024) — транскрипт не разобран помощником; формула сверена по исходнику three r186.
