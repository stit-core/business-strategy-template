# Атлас: утилиты, библиотеки, CLI и локальные модели — версии, лицензии, проверенность, место в конвейере

Волна 3 · агент N · 24.09.2026 · версии сняты на этой машине (Debian 13, 20 потоков, 15 ГБ ОЗУ, Intel Iris Xe/Vulkan, без
CUDA) командами `--version` и метаданными пакетов (`importlib.metadata`, `package.json`, файлы LICENSE в `99-raw/tools/bin/`)
· описание утилит — `../../scripts/ai-media/README.md` (владельцы — агенты B, B2, D2, E, F2, G, H, I, J, K, L, N).

## Выжимка для агента

1. **Все утилиты базы работают без сети и без ключей**, кроме `--live`-режимов клиентов (`polza.py`, `mp_client.py`) и
   снимков публичных каталогов; платных вызовов в утилитах по умолчанию нет. → §1 [проверено]
2. **Порядок в конвейере фиксирован**: каталог (`polza_catalog.py`) → маршрут (`routing.yaml` + `routing_check.py`) → промт
   (`prompt_compile.py`) → генерация (`polza.py`/`mp_client.py`) → провенанс мастера (`provenance_check.py scan`) → приёмка
   (`asset_audit.py`, `edit_check.py`, `video_loop_check.py`) → кодирование (`avif_pick.sh`, J `make_*`) → `stamp` → страница
   (`page_accept.py`). → §6 [практика]
3. **Кодеки — свои свежие сборки**: libavif 1.4.2 (aom 3.14.1 / dav1d 1.5.3), libjxl 0.12.0 (`cjxl`, `ssimulacra2`),
   libwebp 1.6.0, ffmpeg 7.1.5 (Debian). AVIF подбирать по SSIMULACRA2, не по `q`. → §2 [проверено]
4. **ffmpeg 7.1.5 теряет последний кадр MP4 при `trim` без `-r`** — `video_loop_check.py trim` это учитывает; свои команды —
   с `-r` исходника. → §2 [проверено]
5. **rembg 2.0.85 по умолчанию грузит некоммерческую RMBG-2.0** — модель всегда явно (`u2netp`, `isnet-general-use`),
   `REMBG_HOME=99-raw/tools/models/rembg`. → §3 [проверено]
6. **Тяжёлое — под блокировкой и после `free -g`**: Blender (`blender.lock`), ONNX > 300 МБ, Real-ESRGAN, RIFE, OCR
   (`heavy.lock`), Chromium (`browser.lock`); BiRefNet-lite на CPU съел 6,5 ГБ. → §4 [проверено]
7. **Real-ESRGAN — не для фото** (хуже Lanczos на 15–103 п.); RIFE — не для кадров с текстом. → §2 [проверено: H/02, I]
8. **OCR кириллицы — RapidOCR 3.9.2 + PP-OCRv5 eslav** (0,1 с на строку): пропуск, удвоение, лишнее слово ловит на 100 %,
   латинских «близнецов» не видит. → §3 [проверено]
9. **Провенанс — c2patool 0.27.22 + exiftool 13.59**: C2PA переживает только побайтное хранение; производной — XMP
   `DigitalSourceType` (+1–3 КБ). → §2 [проверено]
10. **Вектор — resvg-js 2.6.2, svgo 4.1.0, vtracer 1.0.0-alpha.4, potrace 1.16**; эталон иконок — `lucide-static` 1.47.0 (ISC). → §3
    [проверено: G/01–03]
11. **Лицензии в `bin/` и venv — разрешительные, кроме potrace/potracer (GPL-2.0+), exiftool (GPL-3.0 в сборке) и CairoSVG (LGPL-3.0)** — их используем как
    внешние инструменты, не встраиваем в продукт клиента. → §2–3 [документация: LICENSE, метаданные пакетов]
12. **Новые утилиты N**: `routing_check.py` (валидатор маршрутов, 0 ошибок, отрицательный тест 9/9) и `channel_diff.py`
    (разница снимков RouterAI и Gen-API). → §1 [проверено]

## 1. Утилиты базы (`99-raw/tools/`)

| Утилита | Версия | Что делает | Проверка | Владелец |
|---|---|---|---|---|
| `polza.py` | 1.0 | клиент Media API polza: проверка по каталогу, явные ценовые default, `estimate`, сухой прогон, `--live`, паспорт, журнал, кэш, лимиты, загрузка файлов в хранилище (`mask_url`, `first/last_frame_url`) | макет 30/30, калькулятор 84, валидатор 51 ловушка | B (+ правка оркестратора 23.09) |
| `polza_catalog.py` | 1.0 | снимок каталога, нормализация, таблица, `diff`, `price`, `check`, `selftest` | selftest | B |
| `mp_client.py` | 1.0 | RouterAI, Gen-API, polza-chat, polza-images: `estimate`, `run`, `batch`, `snapshot`, журнал, бюджеты каналов (по умолчанию 0) | selftest 36/36, макет 44/44 | B2 |
| `prompt_compile.py` | 2.1 | спецификация ассета → промт в диалекте семейства (`dialects.yaml` v0.3) + параметры; правки, серии, видео | тесты 98/98, D 30/30, регресс 850 | D, D2, D2b |
| `ab_analyze.py` | — | A/B формы промта: симуляция мощности, манифест, судья, метрики, анализ | selftest | D2 |
| `stand_run.py` | — | стенд моделей: `build`, `estimate`, `run`, `collect`, `metrics`, `sheet`, `page` (слепые пары), `tally`, `ministand` | selftest 8/8, страница 6/6 | E |
| `asset_audit.py` | 0.1 | приёмка ассета: режимы `image`, `cutout`, `edit`, `texture`, `series`, `video-loop`, `video-alpha`, `svg-icon`, `og`; OCR; судья K | тесты 55/55 | K |
| `edit_check.py` | 0.2 | правка на месте, утечка, дрейф, полярность маски, аутпейнт (3 критерия), композит | selftest | H, H2 |
| `alpha_check.py` | — | альфа против эталона, ореол, «нарисованная шахматка» | — | H |
| `tile_check.py` | — | шов текстуры, разрез минимальной ошибки, превью 2×2 | — | H2 |
| `avif_pick.sh` | — | минимальный AVIF, проходящий порог SSIMULACRA2 | — | H2 |
| `video_loop_check.py` | 0.2 | шов, живость, склейки, дрейф, хромакей, стык, контактный лист, `trim`, `colormatch` | selftest 11 случаев | I, I2 |
| `vlm_to_dna.py` | — | паспорт визуала: сетка → VLM-задание → разбор → проверка → LUT → спецификация | selftest 23/23 | F2 |
| `provenance_check.py` | 0.1 | C2PA, XMP/IPTC, AIGC, подпись Recraft, углы кадра; `stamp` производной | selftest 11/11, корпус 70 файлов | L |
| `page_accept.py` | — | приёмка страницы: байты первого экрана, LCP, CLS, TBT, пауза, reduce, F83 по буквам и кадрам | 9 страниц, 27 прогонов | J |
| `asset_inventory.py` | — | инвентарь ассетов живого сайта (LCP, видео, SVG, Lottie, сеть) | 52 URL десктоп, 10 телефон | A |
| `site_probe.py`, `color.py`, `fetch.py`, `render_fetch.py`, `yt_transcript.py`, `vtt2md.py`, `yt_dl.py` | — | замер сайта; WCAG/APCA/OKLCH; чтение веба; субтитры YouTube | — | 3d-research, ui-research, V |
| **`routing_check.py`** | 1.0 | валидатор `routing.yaml`: модели, провайдеры, параметры, цены (± 1 %), диалекты, рубрики, флаги `legal`, тесты фазы 5 | 0 ошибок; отрицательный тест 9/9 | **N** |
| **`channel_diff.py`** (`99-raw/experiments/N/04-update-dryrun/`) | — | разница снимков RouterAI и Gen-API: новые, удалённые, сдвиг цен, параметры | прогон 23→24.09 | **N** |
| скрипты опытов | — | J `05-assets/{make_images,make_video,sweep_crf,finalize_video,make_alpha,make_og}.py`; G `check_icons.py`, `sheet.py`, `grid.py`, `02-…/process.py`, `slice.py`, `retrace.py`; H `00-reference-renders/make_refs.py`, `03-edit-check/ghost_zone.py`, `06-depth/depth_eval.py`; 3d `blender_run.py` | в README опытов | J, G, H, 3d |

## 2. Бинарники и CLI

| Инструмент | Версия (24.09.2026) | Лицензия | Путь | Для чего | Проверено |
|---|---|---|---|---|---|
| Python | 3.13.5 | PSF | системный | всё | — |
| Node.js | 24.21.0 | MIT | `~/.nvm/versions/node/v24.21.0` | resvg, svgo, Lottie | G |
| ffmpeg | 7.1.5-0+deb13u1 (AV1 libsvtav1/aom, VP9, HEVC, WebP, JXL) | LGPL/GPL (сборка Debian) | системный | кодирование, кеинг, `maskedmerge`, кадры | I, J, H |
| libavif | 1.4.2 (aom 3.14.1 enc, dav1d 1.5.3 dec, libyuv) | BSD-2 по проекту (LICENSE в сборке нет — не сверялась) | `bin/libavif/{avifenc,avifdec}` | AVIF с альфой, `-y 420` | H/04 |
| libjxl | 0.12.0 | BSD (LICENSE.jpeg-xl) | `bin/libjxl/tools/{cjxl,djxl,ssimulacra2,butteraugli_main,jxlinfo}` | JPEG XL, **SSIMULACRA2** | H/04 |
| libwebp | 1.6.0 | BSD по проекту (LICENSE в сборке нет — не сверялась) | `bin/libwebp/{cwebp,dwebp,webpmux,get_disto,…}` | WebP-запас | H/04 |
| c2patool | 0.27.22 | по репозиторию contentauth (не сверялась) | `bin/c2patool/c2patool` | чтение и тестовая подпись C2PA; 0.28 — отдельный репозиторий | H/04b, L/01 |
| exiftool | 13.59 | GPL-3.0 (файл LICENSE в `bin/exiftool`) | `bin/exiftool/exiftool` | XMP `DigitalSourceType`, IPTC, EXIF | L/01 |
| vtracer | 1.0.0-alpha.4 (musl, 29.08.2026) | MIT (Python-обвязка 0.6.15 — MIT) | `bin/vtracer-1.0.0a4/vtracer` | векторизация с палитрой | G/03 |
| potrace + mkbitmap | 1.16 | **GPL-2.0** | `bin/potrace-1.16/` | ч/б трассировка, отверстия иконок | G/02 |
| Real-ESRGAN ncnn-vulkan | сборка ncnn (Vulkan на Iris Xe) | MIT | `bin/realesrgan-ncnn-vulkan/` | апскейл графики (не фото) | H/02, P/10 |
| RIFE ncnn-vulkan | rife-v4.6 | MIT | `bin/rife-ncnn-vulkan/` | интерполяция стыка петли | I, P/10 |
| stable-diffusion.cpp Vulkan | сборка P | MIT | `bin/sd-cpp-vulkan/` | проба локальной генерации — для продакшна не годится | P/10 |
| Playwright + Chromium | Playwright 1.63.0; Chrome for Testing 153.0.8010.12 (`chromium-1243`; есть и 151 — `chromium-1234`) | Apache-2.0 / BSD | `~/.cache/ms-playwright/` | рендер страниц, приёмка, слепые пары, скриншоты | J, E, K |
| pandoc | 3.1.11.1 | GPL-2.0 | системный | конвертация документов | — |
| yt-dlp | 2026.08.18 | Unlicense | системный | ролики и субтитры (под правилами V) | V |
| uv | 0.11.19 | MIT/Apache-2.0 | системный | venv и пакеты | все |

## 3. Библиотеки и окружения

| Окружение | Пакеты (версия, лицензия) | Для чего |
|---|---|---|
| системный Python | Pillow 11.3.0 (AVIF/WebP), numpy 2.3.2, scipy 1.16.1, PyYAML 6.0.2, Playwright 1.63.0 | утилиты B, E, H, I, J, K, L, N |
| `venv-p10` (506 МБ) | rembg 2.0.85 (MIT), onnxruntime 1.30.0 (MIT), PyMatting 1.1.16 (MIT), scikit-image 0.26.0 (BSD), Pillow 12.3.0 (MIT-CMU), numpy 2.5.3, scipy 1.18.1 | вырез, матирование, глубина (H) |
| `venv-K` (379 МБ) | RapidOCR 3.9.2 (Apache-2.0, 7 938 ★ по K), onnxruntime 1.30.0, opencv-python 5.0.0.93 (Apache-2.0), PyYAML 6.0.3 | OCR кириллицы (K) |
| `venv-G` (237 МБ) | vtracer 0.6.15 (MIT), potracer 0.0.4 (**GPL-2.0+**), svgelements 1.9.6 (MIT), CairoSVG 2.9.1 (**LGPL-3.0+**), scikit-image 0.26.0 | векторизация, разбор SVG (G) |
| `venv-D`, `venv-D2` | jsonschema 4.26.0 (MIT), PyYAML 6.0.3, numpy, scipy, Pillow | компилятор промтов, A/B, стенд (D, D2, E) |
| `99-raw/tools/node` (npm) | @resvg/resvg-js 2.6.2 (MPL-2.0), svgo 4.1.0 (MIT), lucide-static 1.47.0 (ISC), lottie-web 5.13.0 (MIT), @lottiefiles/dotlottie-web 0.80.0 (MIT) | рендер и чистка SVG, эталон иконок, плееры Lottie (G) |

## 4. Локальные модели (`99-raw/tools/models/`, 270 МБ + OCR 29 МБ)

| Модель | Файл | Лицензия | Ресурсы | Для чего | Проверено |
|---|---|---|---|---|---|
| u2netp | `rembg/u2netp.onnx` | Apache 2.0 | 0,1–0,6 с на CPU | вырез по умолчанию (мех — с matting) | H/01 |
| isnet-general-use | `rembg/isnet-general-use.onnx` (sha256 60920e99…) | веса без лицензии, DIS5K NC | как u2netp | тонкие детали — черновик | H/01 |
| Depth Anything V2 Small | `depth/depth_anything_v2_small.onnx` (sha256 afb6a5c2…) | Apache 2.0 | вход 518², 0,30 с и 0,48 ГБ на кадр, 4 потока | 2.5D, слои | H/06 |
| PP-OCRv5 rec eslav / cyrillic / en; det PP-OCRv5 mobile; det PP-OCRv6 small (из колеса RapidOCR) | `ocr/*.onnx` (sha256 — `11-evaluation-qa/thresholds.yaml`) | Apache-2.0 | 0,1 с | OCR кириллицы, «латинский нюх» | K/01 |
| RMBG-2.0 (bria-rmbg) | не скачана | CC BY-NC | 1 ГБ | **не использовать** | P/10 |
| BiRefNet-lite | не держим | MIT | 6,5 ГБ ОЗУ на CPU | только хостинг или ≥ 8 ГБ свободно | P/10 |

## 5. Данные и справочники

| Что | Где | Лицензия / дата | Для чего |
|---|---|---|---|
| Снимки каталогов polza, RouterAI, Gen-API | `99-raw/cache/polza/<дата>/`, `routerai/…`, `genapi/…` | публичные GET, 24.09.2026 | маршруты, цены, валидатор |
| Список доверия C2PA | `99-raw/cache/c2pa-trust-2026-09-23/C2PA-TRUST-LIST.pem` | 30 корней, 23.09.2026 | `provenance_check.py scan --trust` |
| Иконки ЕС «AI GENERATED / MODIFIED» | `99-raw/cache/eu-ai-act-2026-09-23/` | свободно без атрибуции | видимая метка дипфейка (L/03) |
| Эталон иконок Lucide | `node/node_modules/lucide-static` | ISC | сравнение LLM-иконок |
| Входы фазы 5 | `99-raw/phase5/inputs/<агент>/` (`LICENSES.md`) | CC0 (Poly Haven, ambientCG) и свои рендеры Blender 5.2.2 | тесты, эталоны альфы и масок |
| Регрессионный набор правки | HF `PaintBench/PaintBench` (не скачан) | CC-BY-4.0 | пиксельная проверка правок без генераций |
| Галереи слепых пар | Rapidata T2I v1 (API, лицензия не указана) | — | голосование без генераций, внутренне (`13/02` §2.2) |

## 6. Инструменты по слоям конвейера

| Слой (PLAN «Слои конвейера») | Инструменты |
|---|---|
| визуальная ДНК → паспорт | `vlm_to_dna.py` (`from-tokens`, `build`, `parse`, `validate`, `lut`, `to-spec`) |
| маршрутизация | `routing.yaml` v1, `routing_check.py`, `polza_catalog.py`, `channel_diff.py`, `stand_run.py ministand` |
| компилятор промта | `prompt_compile.py` 2.1, `dialects.yaml` 0.3, `asset-spec.schema.json` 0.2 |
| генерация | `polza.py`, `mp_client.py` (паспорта, журнал `_ledger.jsonl`, кэш) |
| отбор | `stand_run.py page/tally`, `asset_audit.py judge-jobs/agree`, `ab_analyze.py` |
| постобработка | rembg, `alpha_check.py`, `edit_check.py`, `tile_check.py`, Depth Anything, Real-ESRGAN (графика), RIFE, vtracer/potrace, svgo, `video_loop_check.py trim/colormatch`, ffmpeg |
| проверка | `asset_audit.py` (+ OCR), `video_loop_check.py`, `provenance_check.py scan` |
| доставка | `avif_pick.sh`, cwebp, cjxl, ffmpeg (AV1/H.264 с тегами BT.709), J `make_*`, `provenance_check.py stamp`, `page_accept.py` |

## Частые ошибки

1. **rembg без модели** — некоммерческая RMBG-2.0 по умолчанию.
2. **AVIF по фиксированному `q`** вместо порога SSIMULACRA2 — либо тяжело, либо бандинг.
3. **`trim` в ffmpeg без `-r`** — теряется последний кадр MP4 (7.1.5).
4. **Real-ESRGAN на фото и RIFE на тексте** — выдумывает структуру / рвёт буквы.
5. **Запуск Chromium, Blender, OCR без `flock`** — соседи в своп.
6. **GPL-инструменты (potrace, potracer) внутри продукта клиента** — только как внешний шаг конвейера.
7. **Правка файла с валидным C2PA через exiftool** — подпись ломается; штамп — только в производную.

## Чек-лист

- Утилита запущена сухим прогоном (`--live` только с заказчиком)?
- Тяжёлый шаг под `flock` и после `free -g` (≥ 3 ГБ available)?
- Модель выреза и OCR заданы явно, лицензия весов — разрешительная?
- Кодирование по SSIMULACRA2 / `motion_keep`, теги BT.709, `-an`, `-movflags use_metadata_tags+faststart`?
- Провенанс: мастер побайтно, производная со `stamp`, `asset_audit --stage web`?

## Открытые вопросы и противоречия

1. Лицензия c2patool не сверена (в `bin/c2patool` нет LICENSE); у exiftool в сборке — GPL-3.0; libavif и libwebp — без LICENSE в сборке.
2. `page_accept.py` меряет лабораторию (Chromium 153); поле (CrUX), Safari и INP — не меряются.
3. Мини-стенда для моделей RouterAI/Gen-API нет (`stand_run.py` — только polza).

## Источники

- [S1] `../../scripts/ai-media/README.md` (разделы B, E, G, D2, I, F2, H, B2, L, K, J) — описание и проверка утилит.
- [S2] Метаданные пакетов на машине (`importlib.metadata`, `package.json`), `--version` бинарников, файлы LICENSE в
  `99-raw/tools/bin/` — сняты 24.09.2026 [проверено].
- [S3] `../12-legal-provenance/01-licenses-by-vendor-and-channel.md` §4 (L) — решения по весам.
- [S4] Опыты `99-raw/experiments/{G,H,I,J,K,L,P,N}/` — README с версиями и временем прогонов.
