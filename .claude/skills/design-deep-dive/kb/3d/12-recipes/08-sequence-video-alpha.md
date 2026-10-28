# 08 · Секвенция кадров, вращение 360° и видео с альфой: предрендер вместо реалтайма

Волна 3 · агент K · 23.09.2026 · Blender 5.2.2 LTS (EEVEE), Pillow 11.3, ffmpeg 7.1 (libvpx-vp9, libaom-av1, libx265), Chromium ·
сквозной прогон: [проверено] · пример: `examples/08-sequence-video-alpha/`

## Выжимка рецепта

1. Когда интерактив не нужен, **предрендер легче реалтайма в 10–100 раз против текстурного GLB с JS** (для детальной формы без текстур видео ≈ GLB: VP9 1 с 124 КБ против 117 КБ — выигрыш в 0 КБ JS) и точнее по свету: hero AVIF 4–6 КБ, вращение 2 с видео
   с альфой 14–61 КБ, секвенция 48 кадров AVIF 105–186 КБ (A/06) — без three и без 174 КБ JS [проверено: A/06, этот прогон].
2. Кадры вращения — **поворот корня перед каждым кадром** (без анимационной системы; надёжно в 5.x), EEVEE 16 спп 512² ≈ 0,5–0,7 с на
   кадр, `film_transparent` [проверено: A/06, этот прогон].
3. Видео с альфой — **VP9 в WebM** (`yuva420p`, Chrome/Firefox/Edge) + запас **stacked-alpha** (кадр × 2 по высоте: цвет сверху,
   альфа снизу; AV1/HEVC) со склейкой в WebGL; HEVC-alpha на Linux не кодируется [проверено: A/06, D2 `06/04 §3`, H/16].
4. Секвенция по прокрутке — WebP/AVIF-кадры в `<canvas>` с окном памяти (кадр 1080² = 4,5 МБ в памяти — не держать все)
   (F1 `09/06 §1.1`); точный скраб видео — all-intra H.264 (`-g 1`) [проверено: A/06, F1].
5. Кадрам нужен тот же вид, что странице (Neutral для бренда); тень на прозрачном фоне — только Cycles (ловец), EEVEE — без тени
   или на фоне страницы.

## 1. Бриф-пример и границы

«Скульптура рецепта 04 медленно вращается рядом с текстом; без WebGL, телефон; второй вариант — вращение по прокрутке».

| годится | не годится → куда |
|---|---|
| петля или вращение без управления; телефон; нет WebGL | пользователь крутит сам, AR → GLB (рецепты 01, 12) |
| точный свет Cycles/EEVEE (стекло, каустика, мех) | вращение 360° с высоким разрешением на весь экран → вес 1–5 МБ (секвенция) — оценить против GLB |
| интро логотипа без three (VP9 32 КБ, H/16) | много состояний/вариантов цвета → GLB + `KHR_materials_variants` |

## 2. Паспорт

Ассет — `sculpture_ink_34_raw.glb` рецепта 04 (импорт glTF — тот же конвейер работает с любым GLB: библиотека, генератор, скан);
24 кадра на оборот (15°/кадр), 512², EEVEE 16 спп, Neutral, прозрачный фон; видео 24 fps (1 с на оборот; для петли 2–4 с — 48–96
кадров); кодирование: WebP q80, AVIF q55, VP9 CRF 40, AV1 stacked CRF 40.

## 3. Код Blender: GLB → студия без фона → 24 кадра с альфой

```python
# Blender 5.2.2 — [проверено] рецепт 08: вращение 360° импортированного GLB → PNG RGBA
import sys, math, os, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "08-sequence-video-alpha"
P = dict(glb=f"{rk.ROOT}/12-recipes/examples/04-abstract-sculpture/sculpture_ink_34_raw.glb", frames=24, res=(512, 512),
         samples=16, cam=dict(az=30, el=12, lens=85, margin=1.12))

rk.reset()
C = D.fresh_collection("ASSET_turntable")
before = set(bpy.data.objects)
assert bpy.ops.import_scene.gltf(filepath=P["glb"]) == {"FINISHED"}
imported = [o for o in bpy.data.objects if o not in before]
for o in imported:                                                    # в свою коллекцию (импорт кладёт в активную)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    C.objects.link(o)
meshes = [o for o in imported if o.type == "MESH"]
root = bpy.data.objects.new("Turntable", None); C.objects.link(root)
for o in imported:
    if o.parent is None:
        o.parent = root
rk.studio(meshes, E_key=2.5, az=P["cam"]["az"], backdrop=False, world=0.3)   # без циклорамы: фон — альфа
rk.camera(meshes, res=P["res"], **P["cam"])
rk.neutral(samples=P["samples"], transparent=True)
out = f"{rk.out_dir(SLUG)}/seq"; os.makedirs(out, exist_ok=True)
secs = []
for i in range(P["frames"]):
    root.rotation_euler.z = 2 * math.pi * i / P["frames"]              # поворот корня перед кадром — без ключей
    r = bpyx.render_still(f"{out}/f_{i + 1:04d}.png", resolution=P["res"], samples=P["samples"], transparent=True)
    secs.append(r["sec"])
assert len(os.listdir(out)) >= P["frames"]
rk.save(SLUG, frames=P["frames"], sec_per_frame=round(sum(secs) / len(secs), 2), sec_frames=round(sum(secs), 1), passport=P)
```

## 4. Кодирование: WebP/AVIF-секвенция, VP9 с альфой, stacked AV1

```python
# run: system — Python 3 + Pillow + ffmpeg — [проверено] команды кодирования (3d 06/04 §2–3) на кадрах рецепта
import glob, json, os, subprocess
from PIL import Image
EX = os.path.dirname(os.path.abspath(__file__))  # перенос: папка примера
frames = sorted(glob.glob(f"{EX}/seq/f_*.png")); os.makedirs(f"{EX}/web/seq", exist_ok=True)
kb = lambda p: round(os.path.getsize(p) / 1024, 1)  # noqa: E731
tot = {"png": 0, "webp_q80": 0, "avif_q55": 0}
for f in frames:
    im = Image.open(f); b = os.path.basename(f)[:-4]; tot["png"] += os.path.getsize(f)
    im.save(p := f"{EX}/web/seq/{b}.webp", quality=80, method=6); tot["webp_q80"] += os.path.getsize(p)
    im.save(p := f"{EX}/web/seq/{b}.avif", quality=55, speed=6); tot["avif_q55"] += os.path.getsize(p)
IN = f"{EX}/seq/f_%04d.png"
STACK = "[0:v]format=pix_fmts=yuva444p[main];[main]split[main][alpha];[alpha]alphaextract[alpha];[main][alpha]vstack"
cmds = {"turn_vp9_alpha.webm": ["-pix_fmt", "yuva420p", "-c:v", "libvpx-vp9", "-crf", "40", "-b:v", "0", "-deadline", "good", "-row-mt", "1"],
        "turn_stacked_av1.mp4": ["-filter_complex", STACK, "-pix_fmt", "yuv420p", "-c:v", "libaom-av1", "-cpu-used", "6", "-crf", "40",
                                 "-b:v", "0", "-movflags", "+faststart"]}
video = {}
for name, args in cmds.items():
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "24", "-i", IN] + args + ["-an", f"{EX}/web/{name}"], check=True)
    video[name] = kb(f"{EX}/web/{name}")
res = {"frames": len(frames), "seq_total_kb": {k: round(v / 1024, 1) for k, v in tot.items()}, "video_kb": video}
json.dump(res, open(f"{EX}/web/sizes.json", "w"), ensure_ascii=False, indent=1)
print(res)
```

## 5. Числа прогона

Blender 17,7 с (импорт GLB, студия без фона, 24 кадра EEVEE 16 спп 512² — **0,73 с на кадр**); кодирование 56 с (AVIF-секвенция и AV1 —
самые долгие). Итераций — 0.

| поставка (24 кадра 512², лента 26 тыс. треуг.) | вес | A/06 (простая «банка», 48 кадров) |
|---|---|---|
| PNG RGBA (исходник, не отдавать) | 5 111 КБ | 5 642 КБ |
| секвенция WebP q80 | **381,5 КБ** (15,9 КБ/кадр) | 183 КБ (3,8/кадр) |
| секвенция AVIF q55 | **228,0 КБ** (9,5 КБ/кадр) | 105 КБ (2,2/кадр) |
| видео VP9 с альфой (WebM, CRF 40) | **124,4 КБ** | 19 КБ (2 с) |
| stacked-alpha AV1 (512 × 1024, CRF 40) | **80,1 КБ** | 14 КБ |

Страница `examples/08-sequence-video-alpha/index.html` (`web_view.py --page`): видео играет с альфой поверх CSS-градиента, 144 КБ всего
(видео 124 + постер-кадр 18), 0 ошибок консоли, 0 вызовов WebGL [проверено]. Детальная форма
(лента с бликами) весит в 2–6 раз больше простой сцены A/06 — оценивать вес на своём ассете, а не по таблице A.

Взгляд на `examples/08-sequence-video-alpha/sheet.png` (кадры 1, 5, 9, 13, 17, 21): оборот ровный, альфа чистая, тени нет (EEVEE без
ловца); у узла (3, 4) при этом ракурсе период 180° — кадры 1 и 13 (0° и 180°) совпадают: для петли хватило бы половины оборота =
12 кадров (вес ×½).

## 6. Страница: варианты разметки

```html
<!-- HTML — [проверено] петля без JS; reduce → пауза на постере (скрипт в примере) -->
<video src="web/turn_vp9_alpha.webm" poster="web/seq/f_0001.webp" width="512" height="512"
       autoplay muted loop playsinline aria-label="Скульптура из тёмно-синей ленты медленно вращается"></video>
```

- **Safari** VP9-alpha не играет → stacked-alpha (HEVC для Safari, AV1 для остальных) + склейка в WebGL-шейдере без
  sRGB-декодирования — загрузчик F1 `../09-web-runtime/06-deliverables-ar-ktx2-webgpu.md §1.2` (`createStackedAlphaMaterial`) [проверено: F1].
- **Секвенция по прокрутке** — `ImageSequence` с окном памяти (F1 `09/06 §1.1`); кадр по прогрессу прокрутки (как рецепт 05), без
  видео-декодера; для точного скраба видео — all-intra H.264 (`-g 1`) на фоне (A/06).
- Постер — первый кадр WebP/AVIF; `width/height` против CLS; автодвижение > 5 с — кнопка паузы (WCAG 2.2.2).

## 7. Ворота

Кадров = N (`assert`), альфа по краю (глазом на фоне страницы), вес: hero-петля ≤ 150 КБ, секвенция на телефон ≤ 1–2 МБ; reduce →
пауза; 0 ошибок консоли.

## 8. Варианты

1. **Тень под объектом с альфой** — Cycles + ловец теней (рецепт 02), 32 спп + OIDN: ≈ 3,5 с на кадр 512² (× 5 к EEVEE).
2. **Интро логотипа** — те же команды на кадрах клипа (H/16: VP9 31,9 КБ, stacked AV1 23,8 КБ).
3. **Hero-кадр вместо видео** — один кадр AVIF q60 (рецепт 02, `encode_web`): 4–6 КБ.
4. **Меньше кадров** — симметричная форма → поворот на период симметрии; 12 fps для медленного вращения.

## Частые ошибки рецепта

| ошибка | симптом | исправление |
|---|---|---|
| ключи вращения + экспорт/рендер анимации | лишняя сложность, 5.x-ловушки слотов | поворот корня перед кадром (A/06) |
| HEVC-alpha на Linux | не кодируется | VP9-alpha + stacked AV1/HEVC (D2 `06/04 §3`) |
| stacked-альфа с sRGB-декодированием текстуры | ореол/тёмный край | `colorSpace = NoColorSpace` для альфа-половины (F1 `09/06 §1.2`) |
| все кадры секвенции в памяти | 4,5 МБ на кадр 1080², вылет на телефоне | окно памяти (F1 `09/06 §1.1`) |
| PNG-кадры на сайте | 5 МБ за оборот | WebP/AVIF (в 13–22 раза меньше) или видео |
| EEVEE-тень на прозрачном фоне | тени нет | Cycles-ловец или фон страницы в кадре |

## Ссылки

A `../01-web-3d-landscape/05-blender-deliverables-map.md §2`, `../99-raw/experiments/A/06-deliverable-sizes` (`encode.py`, `playback.html`);
D2 `../06-materials-lighting-render/04-outputs-for-web.md §2–3`; F1 `../09-web-runtime/06-deliverables-ar-ktx2-webgpu.md §1.1–1.2`;
H `../07-animation/04-js-vs-blender-vs-prerender.md §4`.
