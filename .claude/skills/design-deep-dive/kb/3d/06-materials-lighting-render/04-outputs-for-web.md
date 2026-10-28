# Выходные форматы для сайта: PNG → AVIF/WebP, 1×/2×, секвенции, видео-петли и видео с альфой, карты глубины и matcap, композитинг 5.2

Волна 2 · агент D2 · 23.09.2026 · источников: 6 (эксперимент A/06 и карта поставок A, контракт и сжатие E, B, дайджесты
W3, RNA 5.2.2) · экспериментов: 2 своих (`99-raw/experiments/D2/05-avif-webp` — AVIF/WebP с альфой; `D2/02-engines` —
время кадра) + A/06 («одна сцена во всех поставках») · Blender 5.2.2 LTS, ffmpeg 7.1.5, Pillow 11.3, Chromium (Playwright).

Какая поставка нужна эффекту — A `../01-web-3d-landscape/05-blender-deliverables-map.md` §1 (здесь не повторяется);
загрузчики поставок на странице (секвенция с окном памяти, stacked-alpha-шейдер) — F1 `../09-web-runtime/06-…`; сжатие
текстур GLB (WebP/KTX2) — E `../08-export-gltf/03-…`; цвет файлов — `03-render-engines-color.md` §2.7.

## Выжимка для агента

1. **Из Blender — PNG RGBA 8 бит (`film_transparent`), кодирование — вне Blender**: PNG в продакшен не отдавать (в 30–100 раз тяжелее). → §1 [проверено]
2. **Рендеры с альфой и ровным фоном — AVIF q60–75**: иконка 512² — 4,8–6,3 КБ против 29,8 КБ у WebP q80 и 201 КБ PNG (ΔE после наложения 0,20–0,24); hero 1024² — 4,4 КБ против 10 КБ WebP q85 (A/06). → §1.2 [проверено]
3. **Альфа в AVIF сжимается с потерями** (край мягкой тени до 20–37 из 255), в WebP — без потерь: тень на пёстром фоне — AVIF q75 или WebP. → §1.2 [проверено]
4. **Фото-текстуры PBR — не AVIF**: выигрыш 5 % при ≈ 23 с кодирования; для GLB — WebP/KTX2 (E). → §1.2 [проверено]
5. **`<picture>`: AVIF → WebP → PNG-запас**; размер рендера = 2× CSS-размера (1024² под 512 CSS px), 1× — уменьшением 2×-кадра. → §1.3 [практика: A/06]
6. **Инструменты машины**: Pillow 11.3 (AVIF, WebP), ffmpeg 7.1.5 (libaom, SVT-AV1, rav1e, x264, x265, VP9, libwebp, libjxl); `avifenc`/`cwebp` нет; Blender сам пишет AVIF/WebP/PNG/JPEG/EXR/видео. → §1.1 [проверено: машина; RNA 5.2.2]
7. **Секвенции для прокрутки: два набора** — десктоп 120–200 кадров 1080–1440 px, телефон 60–100 кадров 720 px; кадры `f_0000.webp`; 48 кадров 512²: AVIF 105 КБ, WebP 183 КБ, JPEG 243 КБ (A/06). → §2 [проверено] [практика]
8. **Время секвенции**: EEVEE 1024² — 2,6 с/кадр (16 сэмплов) или 7,5 с (64): 120 кадров × 64 не влезают в 10 минут — рендерить пачками ≤ 60 кадров. → §2 [проверено]
9. **Видео в 5–10 раз легче секвенции тех же кадров**: 2 с @24 768² — stacked AV1 14–39 КБ, VP9-alpha 19–61 КБ, H.264 на фоне 13–81 КБ. → §3 [проверено]
10. **Видео с альфой — стандарт базы: stacked-alpha (AV1 + HEVC/H.264-запас) + WebGL-склейка; VP9-alpha WebM — для Chromium/Firefox**. HEVC with alpha на Linux не кодируется (libx265 без `yuva*`). → §3.2 [проверено: A/06; ffmpeg 7.1.5 на машине]
11. **Перемотка видео прокруткой — all-intra (`-g 1`)**: ×3–4 к весу, точный кадр; иначе — секвенция. → §3.3 [проверено]
12. **Постер = первый кадр той же поставки** (после запекания материалов), AVIF/WebP. → §3.4 [проверено]
13. **Глубина и нормали для 2,5D — проходы в многослойный EXR** (`use_pass_z`, `use_pass_normal`; в 5.x — `media_type = "MULTI_LAYER_IMAGE"`, не `file_format`), затем PNG16/WebP. → §4 [проверено: выполнение блока]
14. **Matcap — рендер сферы ортокамерой в студии** (256–512², прозрачный фон) → `MeshMatcapMaterial`. → §4.2 [проверено: выполнение блока] [не проверено: вид в three]
15. **Bloom — нода Glare «Bloom» в `scene.compositing_node_group`**; виньетку и зерно на сайте — CSS поверх (дёшево и настраиваемо), в кадр вшивать только для предрендера-«картинки». → §5 [проверено] [практика]

## 1. Картинки: PNG → AVIF / WebP

### 1.1. Чем кодировать на этой машине

| инструмент | AVIF | WebP | альфа | заметка |
|---|---|---|---|---|
| Pillow 11.3 (`Image.save(..., "AVIF")`) | да (libavif) | да | да | < 0,1 с на 512² (D2/05) |
| ffmpeg 7.1.5 | libaom-av1 (кадр), SVT-AV1, rav1e | libwebp | VP9 `yuva420p`; x265 и SVT-AV1 — без альфы | видео и секвенции |
| Blender 5.2.2 | `file_format = "AVIF"` | `"WEBP"` | да | пишет с видом сцены; качество `image_settings.quality` [не проверено: сравнение с Pillow] |
| avifenc, cwebp | нет | нет | — | не установлены (sudo запрещён) |

[проверено: машина 23.09.2026; `ImageFormatSettings.file_format` в RNA 5.2.2: AVIF, JPEG, OPEN_EXR, PNG, WEBP, …, FFMPEG].

### 1.2. Что выбрать по типу контента

| кадр | AVIF | WebP | PNG | правило |
|---|---|---|---|---|
| иконка 512² с альфой и мягкой тенью (D2/05) | q60 4,8 КБ (ΔE 0,24; альфа ±29) | q80 29,8 КБ (ΔE 0,17; альфа точна) | 201 КБ | AVIF q60–75 |
| hero 1024² с альфой (A/06) | q60 4,4–6,0 КБ | q85 10–14 КБ; без потерь 95–135 КБ | 443–497 КБ | AVIF + WebP-запас |
| фото-текстуры PBR в GLB (E/18) | −5 % к WebP, ≈ 23 с | базовый | — | WebP / KTX2 (память GPU — только KTX2) |

[проверено: D2/05 `encode_check.json`; A/06 `sizes_simple.json`, `sizes_detail.json`; E `../08-export-gltf/03`]. Противоречие A ↔ E
(«AVIF вдвое меньше» против «5 %») разведено по типу контента: у рендеров с альфой и ровными областями AVIF выигрывает
2–6 раз, у фото-текстур — нет. Мягкая тень в альфе: у AVIF альфа с потерями (q60 — до 29 уровней на краю), на пёстром
фоне страницы проверять глазом или брать q75/WebP.

### 1.3. Код: AVIF/WebP и 1×/2×

```python
# run: system — Python 3 + Pillow 11.3 — [проверено: 99-raw/experiments/D2/99-doc-snippets; числа — D2/05]
import os, tempfile
from PIL import Image

def encode_web(png_path, out_dir, css_px, avif_q=60, webp_q=80):
    """PNG RGBA (рендер 2× CSS) → AVIF и WebP для 2× и 1×; возвращает {имя: КБ} и HTML <picture>."""
    im = Image.open(png_path).convert("RGBA"); base = os.path.splitext(os.path.basename(png_path))[0]
    os.makedirs(out_dir, exist_ok=True); sizes = {}
    for scale in (2, 1):
        px = css_px * scale
        frame = im if im.width == px else im.resize((px, round(im.height * px / im.width)), Image.LANCZOS)
        for ext, kw in (("avif", {"quality": avif_q}), ("webp", {"quality": webp_q, "method": 6})):
            p = os.path.join(out_dir, f"{base}@{scale}x.{ext}"); frame.save(p, ext.upper(), **kw)
            sizes[os.path.basename(p)] = round(os.path.getsize(p) / 1024, 1)
    html = (f'<picture><source type="image/avif" srcset="{base}@1x.avif 1x, {base}@2x.avif 2x">'
            f'<source type="image/webp" srcset="{base}@1x.webp 1x, {base}@2x.webp 2x">'
            f'<img src="{base}@1x.webp" width="{css_px}" height="{css_px}" alt="" loading="lazy" decoding="async"></picture>')
    return sizes, html

d = tempfile.mkdtemp(); src = os.path.join(d, "icon.png")
Image.new("RGBA", (512, 512), (99, 91, 255, 0)).save(src)          # пример: прозрачный кадр 2× для 256 CSS px
print(encode_web(src, os.path.join(d, "web"), css_px=256))
```

Для LCP-кадра hero — без `loading="lazy"`, с `fetchpriority="high"` (A `02 §4`); размеры `width/height` — против CLS.

## 2. Секвенции кадров для прокрутки

| параметр | десктоп | телефон | источник |
|---|---|---|---|
| кадров | 120–200 | 60–100 | [практика: A `05 §3.14`, OPTIKKA/Apple] |
| размер кадра | 1080–1440 px | 720 px | то же |
| формат | AVIF q55 / WebP q80 | то же | A/06 |
| вес (порядок) | 48 кадров 512²: AVIF 105 КБ, WebP 183 КБ, JPEG на фоне 243 КБ; фотореализм ×3–10 | — | [проверено] |

- Имена `f_0000.webp`, отдельная папка на набор; загрузка с окном памяти — F1.
- Время рендера (D2/02): EEVEE 1024² — 2,6 с/кадр при 16 сэмплах, 7,5 с при 64; Cycles 512² 16 + OIDN — 5,3 с. 120 кадров EEVEE-64
  1024² ≈ 15 мин > таймаута 10 мин → пачками по ≤ 60 кадров (`--frame-start/--frame-end` или цикл с продолжением)
  [проверено].
- Поворот (turntable) без анимационной системы — вращать пустышку-родителя на 360°/N за кадр (A/06); с анимацией —
  интерполяция Linear, иначе разгон и торможение [V:5UCc3Z_-ibs 20:48–22:08].
- Спрайт-листы (много кадров в одной картинке) — [не проверено]: экономят запросы, но ограничены 4096–8192 px по стороне
  и декодируются целиком.

```python
# Blender 5.2.2 — [проверено] секвенция поворота: пустышка-родитель, кадры f_0000.png
import sys, os, math, tempfile, bpy
sys.path.insert(0, "../../scripts/3d")
import bpyx

def render_turntable(objects, out_dir, frames=48, size=512, samples=32):
    pivot = bpy.data.objects.new("Turntable", None); bpyx.link(pivot)
    for o in objects:
        o.parent = pivot
    bpyx.set_engine("BLENDER_EEVEE")
    for i in range(frames):
        pivot.rotation_euler = (0, 0, 2 * math.pi * i / frames)
        bpyx.render_still(os.path.join(out_dir, f"f_{i:04d}.png"), resolution=(size, size), samples=samples, transparent=True)
    return sorted(os.listdir(out_dir))

bpyx.clear_scene()
obj = bpyx.primitive("monkey", "Hero", location=(0, 0, 0))
bpyx.principled("Clay", base_color="#D8CFC4", roughness=0.8); bpyx.assign_material(obj, bpy.data.materials["Clay"])
bpyx.frame_camera(bpyx.add_camera(location=(0, -4, 1.2), target=(0, 0, 0), lens=85), [obj], margin=1.3)
bpyx.add_light("AREA", "Key", (2, -2, 3), (0, 0, 0), energy=150, size=2)
out = os.environ.get("SEQ_DIR") or tempfile.mkdtemp()
print(render_turntable([obj], out, frames=3, size=64, samples=4))   # в работе: 48–200 кадров, 512–1440 px
```

## 3. Видео-петли и видео с альфой

### 3.1. Без альфы

H.264 (универсально) + AV1/VP9 первым `<source>`; `<video autoplay muted loop playsinline>` и постер (A `05 §3.15`).
Размер 2 с @24 768²: H.264 на фоне 13–81 КБ, all-intra 100–249 КБ [проверено].

### 3.2. С альфой

| путь | где работает | кодирование на Linux | 2 с @24 768² (A/06) |
|---|---|---|---|
| VP9-alpha WebM (`yuva420p`) | Chromium, Firefox; Safari — нет [практика: Archibald 2024] | да (libvpx-vp9) | 19–61 КБ |
| stacked-alpha: цвет сверху, альфа снизу, двойная высота + WebGL-склейка | везде, где есть WebGL2 | да (AV1 libaom, HEVC x265, H.264) | AV1 14–39 КБ, HEVC 28–77 КБ |
| HEVC with alpha (Safari) | Safari | **нет**: libx265 в ffmpeg 7.1.5 без `yuva*`, кодируют только macOS-энкодеры | — |

Стандарт базы: **stacked-alpha** (AV1 + HEVC-запас для Safari) с шейдером склейки (A/06 `playback.html`, F1) и VP9-alpha как
простой путь для Chromium [проверено: A/06 — альфа 0/255 в Chromium 153; ffmpeg на машине 23.09].

```bash
# ffmpeg 7.1.5 — [проверено: A/06 encode.py (команды), 99-raw/experiments/D2/99-doc-snippets (запуск на 3 кадрах)]
IN="${SEQ_DIR:-frames}/f_%04d.png"; OUT="${OUT_DIR:-video}"; mkdir -p "$OUT"
STACK="[0:v]format=pix_fmts=yuva444p[main];[main]split[main][alpha];[alpha]alphaextract[alpha];[main][alpha]vstack"
# VP9 с альфой (Chromium/Firefox)
ffmpeg -loglevel error -y -framerate 24 -i "$IN" -pix_fmt yuva420p -c:v libvpx-vp9 -crf 40 -b:v 0 -row-mt 1 -an "$OUT/alpha_vp9.webm"
# stacked-alpha: AV1 (основной) и HEVC (запас для Safari); высота кадра ×2
ffmpeg -loglevel error -y -framerate 24 -i "$IN" -filter_complex "$STACK" -pix_fmt yuv420p -c:v libaom-av1 -cpu-used 6 -crf 40 -b:v 0 -movflags +faststart -an "$OUT/stacked_av1.mp4"
ffmpeg -loglevel error -y -framerate 24 -i "$IN" -filter_complex "$STACK" -pix_fmt yuv420p -c:v libx265 -preset medium -crf 28 -tag:v hvc1 -movflags +faststart -an "$OUT/stacked_hevc.mp4"
# без альфы: на цвет страницы, H.264 (+ all-intra для перемотки прокруткой)
ffmpeg -loglevel error -y -framerate 24 -i "$IN" -filter_complex "color=c=0xF4F4F6:s=64x64[bg];[bg][0:v]overlay=shortest=1" -pix_fmt yuv420p -c:v libx264 -crf 23 -preset slow -movflags +faststart -an "$OUT/flat_h264.mp4"
ffmpeg -loglevel error -y -framerate 24 -i "$IN" -filter_complex "color=c=0xF4F4F6:s=64x64[bg];[bg][0:v]overlay=shortest=1" -pix_fmt yuv420p -c:v libx264 -crf 23 -g 1 -movflags +faststart -an "$OUT/flat_h264_allintra.mp4"
# постер — первый кадр в AVIF
ffmpeg -loglevel error -y -i "${SEQ_DIR:-frames}/f_0000.png" -c:v libaom-av1 -still-picture 1 -crf 30 "$OUT/poster.avif"
ls -la "$OUT"
```

В `color=…:s=64x64` подставлять размер кадра (в примере — 64 px кадров из блока §2). Числа качества (`-crf`) — из A/06:
AV1 40, HEVC 28, H.264 23, VP9 40.

### 3.3. Перемотка прокруткой

`video.currentTime` по прогрессу прокрутки работает точно только с all-intra (`-g 1`, ×3–4 к весу); с обычным GOP кадр
«догоняет» ключевой — дёргается; альтернатива — секвенция (§2) [проверено].

### 3.4. Постер

Постер — первый кадр той же поставки, отрендеренный из того же (запечённого) состояния, что GLB/видео, иначе при замене
картинка «прыгает» [проверено]. LCP-постер — `<img fetchpriority="high">`, 3D или видео — после `load` (A `02 §4`).

## 4. Карты для 2,5D и matcap

### 4.1. Глубина и нормали

Проходы View Layer: `use_pass_z` (глубина, метры от камеры), `use_pass_normal` (мировые нормали) → многослойный EXR
(в 5.x — `image_settings.media_type = "MULTI_LAYER_IMAGE"`; `file_format = "OPEN_EXR_MULTILAYER"` при `media_type` IMAGE → ошибка
перечисления [проверено]; файл многочастный — часть на проход: `ViewLayer.Combined`,
`ViewLayer.Depth.Z`, `ViewLayer.Normal.X/Y/Z`, читать все части, `seek_subimage` в OIIO); для страницы — нормировать глубину в 0..1 и сохранить PNG16/WebP (шейдер параллакса — F2). Имена
проходов 5.x: `Depth` (было `Z`), `Normal` (B `02 §6`).

```python
# Blender 5.2.2 — [проверено] кадр + глубина + нормали в многослойный EXR
import sys, os, tempfile, bpy
sys.path.insert(0, "../../scripts/3d")
import bpyx

def render_with_passes(path, size=256):
    sc = bpy.context.scene; vl = bpy.context.view_layer
    vl.use_pass_z = True; vl.use_pass_normal = True
    bpyx.set_engine("BLENDER_EEVEE"); sc.eevee.taa_render_samples = 16
    sc.render.resolution_x = sc.render.resolution_y = size; sc.render.resolution_percentage = 100
    ims = sc.render.image_settings
    ims.media_type = "MULTI_LAYER_IMAGE"            # 5.x: многослойный EXR — через media_type, не file_format (bpyx.render_still ставит IMAGE)
    ims.color_depth = "32"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return {"path": path, "bytes": os.path.getsize(path), "format": ims.file_format}

bpyx.clear_scene()
ob = bpyx.primitive("monkey", "Hero")
bpyx.frame_camera(bpyx.add_camera(location=(0, -4, 1), target=(0, 0, 0), lens=70), [ob], margin=1.3)
bpyx.add_light("AREA", "Key", (2, -2, 3), (0, 0, 0), energy=150, size=2)
r = render_with_passes(os.path.join(tempfile.mkdtemp(), "hero_passes.exr"), size=64)
import OpenImageIO as oiio
inp, ch, i = oiio.ImageInput.open(r["path"]), [], 0
while inp.seek_subimage(i, 0):                   # 5.x пишет многочастный EXR: часть на проход
    ch += list(inp.spec().channelnames); i += 1
print(r["bytes"], i, [c for c in ch if "Depth" in c or "Normal" in c])   # 3 части; ViewLayer.Depth.Z, ViewLayer.Normal.X/Y/Z
```

### 4.2. Matcap

Сфера, ортокамера, студийный свет паспорта, прозрачный фон, 256–512² → `MeshMatcapMaterial.matcap` (стилизация без
света на странице; Lusion — EXR 590 КБ, A `05 §3.11`). Рендер matcap — тот же вид, что и у сайта (Neutral), иначе
цвета «съедут» [практика; вид в three не проверен].

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/D2/99-doc-snippets (выполнение)] matcap-сфера для MeshMatcapMaterial
import sys, os, tempfile, bpy
sys.path.insert(0, "../../scripts/3d")
import bpyx

def render_matcap(path, base="#C65D3B", roughness=0.35, size=256):
    bpyx.clear_scene()
    s = bpyx.primitive("uvsphere", "MatcapSphere", radius=1.0, segments=96, rings=48)
    bpyx.assign_material(s, bpyx.principled("Matcap", base_color=base, roughness=roughness, coat_weight=0.4)[0])
    cam = bpyx.add_camera(location=(0, -5, 0), target=(0, 0, 0)); cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.0
    bpyx.add_light("AREA", "Key", (-2.5, -3, 2.5), (0, 0, 0), energy=250, size=2.5)
    bpyx.add_light("AREA", "Rim", (2.5, 2, 1.5), (0, 0, 0), energy=120, size=1.5)
    bpyx.set_color_management("Khronos PBR Neutral")
    return bpyx.render_still(path, resolution=(size, size), engine="EEVEE", samples=32, transparent=True)

print(render_matcap(os.path.join(tempfile.mkdtemp(), "matcap.png"), size=64)["bytes"])
```

### 4.3. Каустики

Запекание каустик пола (Cycles, свет через стекло) в текстуру для `map`/`lightMap` — [не проверено]; A `05 §1` относит к
редким поставкам. Для сайта чаще — шейдер на странице (F2).

## 5. Композитинг 5.2: что в кадр, что в CSS

| эффект | в Blender 5.2 | на сайте | где делать |
|---|---|---|---|
| bloom/свечение | нода Glare «Bloom» в `scene.compositing_node_group` (B/13: средний RGB 0,49 → 0,62) | bloom-проход (F2) | предрендер — Blender; реалтайм — страница |
| виньетка | Ellipse Mask + размытие + Mix [не проверено] | `radial-gradient` поверх | CSS: дешевле, настраивается, не портит AVIF |
| зерно | шум поверх [не проверено] | PNG-шум `mix-blend-mode: overlay` | CSS: зерно плохо сжимается (AVIF/WebP раздувает) |
| цветокоррекция, AgX-look | look вида (`03`) | — | только Blender (в three looks нет) |
| тени-контакты | ловец теней (`02 §4`) | — | Blender |

Зерно и блики — «эффекты камеры», поверх чистого кадра [V:Z8AAX-ENWvQ 21:28, 22:59] (W3). Композитор 5.x: дерево —
`bpy.data.node_groups.new(..., "CompositorNodeTree")`, выход — Group Output, `scene.node_tree` удалён (B `02 §6`).

```python
# Blender 5.2.2 — [проверено: 99-raw/experiments/D2/99-doc-snippets; узел — B/13] bloom в предрендере
import bpy

def add_bloom(threshold=1.0, strength=0.6, size=0.5, scene=None):
    sc = scene or bpy.context.scene
    tree = bpy.data.node_groups.new("Bloom", "CompositorNodeTree")
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers"); gl = tree.nodes.new("CompositorNodeGlare")
    out = tree.nodes.new("NodeGroupOutput")
    gl.inputs["Type"].default_value = "Bloom"                 # вход-меню 5.x, не gl.glare_type
    gl.inputs["Threshold"].default_value = threshold          # светится только то, что ярче порога (эмиссия > 1)
    gl.inputs["Strength"].default_value = strength; gl.inputs["Size"].default_value = size
    tree.links.new(rl.outputs["Image"], gl.inputs["Image"]); tree.links.new(gl.outputs["Image"], out.inputs["Image"])
    sc.compositing_node_group = tree; sc.render.use_compositing = True
    return tree

t = add_bloom()
print(t.name, all(l.is_valid for l in t.links))
```

## Частые ошибки

1. PNG из Blender прямо на сайт (201–497 КБ вместо 4–30 КБ) [проверено].
2. AVIF для фото-текстур GLB «потому что меньше» → 5 % выигрыша и 23 с на карту; для GLB — WebP/KTX2 (E).
3. Мягкая тень в AVIF q50 на пёстром фоне → ступеньки альфы (ошибка до 37/255) [проверено].
4. Видео с альфой только в VP9 → в Safari прозрачности нет; только HEVC-alpha → в Chrome нет и на Linux не закодировать (A, D2).
5. `video.currentTime` по прокрутке на обычном GOP → рывки; нужен all-intra или секвенция (A/06).
6. Секвенция 120 × EEVEE-64 1024² одним запуском → превышение таймаута 10 мин [проверено: D2/02 — 7,5 с/кадр].
7. Постер отрендерен до запекания или с другим видом → скачок при замене на 3D (A/07).
8. Рендер 1× для ретины → мыло на 2× экранах; рендер = 2× CSS.
9. Виньетка и зерно вшиты в кадр для сайта → тяжелее файл, не настраивается; делать CSS.
10. Композитор по памяти (`scene.node_tree`, `glare.glare_type`, `CompositorNodeComposite`) → ошибки в 5.x (B).
11. PNG/AVIF, сохранённые из Blender, уже содержат вид (AgX/Neutral); повторное применение вида при перекодировании
    в Blender → двойной тонмаппинг (`03 §2.7`).

## Чек-лист

- [ ] Рендер — PNG RGBA 8 бит (2× CSS), кодирование AVIF (+ WebP-запас) вне Blender?
- [ ] Тип контента учтён: рендеры с альфой — AVIF q60–75; фото-текстуры — WebP/KTX2?
- [ ] `<picture>` с 1×/2×, `width/height`, LCP-кадр без lazy?
- [ ] Секвенция: два набора (десктоп/телефон), WebP/AVIF, рендер пачками ≤ 10 мин?
- [ ] Видео с альфой: stacked-alpha (AV1 + HEVC) и/или VP9-alpha; перемотка — all-intra?
- [ ] Постер — первый кадр той же поставки после запекания?
- [ ] Bloom в предрендере — Glare; виньетка/зерно — CSS?
- [ ] Вес поставки сверен с бюджетом страницы (A `02 §3.1`)?

## Открытые вопросы и противоречия

1. **AVIF против WebP**: A/06 — ×2, D2/05 — ×5–6 на иконке с мягкой тенью; зависимость от доли прозрачного и градиентов не
   измерена; качество альфы AVIF на цветных фонах — глазом не проверено.
2. **Родной AVIF/WebP из Blender** (`file_format="AVIF"`) против Pillow — не сравнивался.
3. **Спрайт-листы, каустики, виньетка и зерно в композиторе** — не проверены.
4. **HEVC with alpha** — на Linux не кодируется; путь для Safari — stacked HEVC (A/06) или внешняя сборка на macOS.
5. **Matcap** — вид в `MeshMatcapMaterial` three не сверялся с Blender.

## Источники

- [S1] Агент A. Эксперимент A/06 «Одна сцена во всех поставках» (`99-raw/experiments/A/06-deliverable-sizes/`, `encode.py`,
  `sizes_*.json`, `playback.html`) и `../01-web-3d-landscape/05-blender-deliverables-map.md` §2–3 — проверенные размеры и команды
  ffmpeg (Blender 5.2.2, ffmpeg 7.1.5, Chromium 153).
- [S2] Агент A. Эксперимент A/07 (постер → 3D после LCP) — `../01-web-3d-landscape/02 §4`.
- [S3] Агент E. `../08-export-gltf/03-compression-textures-budgets.md` (E/18: AVIF/WebP/KTX2 для текстур, память GPU).
- [S4] Агент B. `../03-bpy-api/02-nodes-from-python.md` §6 (композитор 5.x, Glare «Bloom», B/13).
- [S5] J. Archibald. «Video with alpha transparency on the web», 2024-08-05 — через A (форматы альфа-видео, поддержка браузеров).
- [S6] [V:5UCc3Z_-ibs], [V:Z8AAX-ENWvQ] — дайджесты W3 (поворотный стол, эффекты камеры).

Эксперименты: `99-raw/experiments/D2/05-avif-webp`, `D2/02-engines`; чужие: A/06, A/07, E/18, B/13.
