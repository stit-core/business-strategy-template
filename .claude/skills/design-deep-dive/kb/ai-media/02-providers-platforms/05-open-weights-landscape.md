# Открытые веса под задачи сайтов: генерация, постобработка, вектор, лицензии и что реально запускается здесь

Волна 1 · агент P (помощник, файл 05) · 2026-09-23 · источников: 31 прочитан целиком, ≈67 выборочно (карточки HF,
тексты LICENSE, README GitHub; из них 35 страниц llms.txt fal, прайсы Replicate/KIE) · опытов: 2 (`99-raw/experiments/P/09-open-weights-meta`,
`99-raw/experiments/P/10-local-runtime-check`) · снимок каталога polza 2026-09-23 · курс ЦБ 84,0657 ₽/$ (23.09.2026).

Соседние файлы: провайдеры и цены закрытых моделей — `03-aggregators-and-platforms.md`, `04-direct-apis-and-services.md`;
карточки моделей по качеству — `../03-image-models/`, `../04-video-models/` (агенты C1, C2). Здесь — «открытые веса:
можно ли, чем, где и почём». Право на результат подробно — у агента L (волна 3).

## Выжимка для агента

1. **Открытые веса ≠ разрешение на коммерцию.** Решай по тексту LICENSE и карточки, а не по тегу HF и не по слову
   «open»: у FLUX.2, Qwen-Image, Depth Anything лицензии различаются внутри одного семейства → §9 [документация]
2. **Self-host для коммерческих сайтов без оговорок** из генераторов картинок: FLUX.2 [klein] 4B (Apache 2.0),
   Qwen-Image / Edit-2509 / Edit-2511 / Layered / 2512 (Apache 2.0), Z-Image и Z-Image-Turbo (Apache 2.0) → §1.1 [документация]
3. **Не запускай у себя для клиентских сайтов** FLUX.2 [dev], FLUX.2 [klein] 9B/9B KV/Base 9B, Qwen-Image-2.1, Ideogram 4 —
   их лицензии некоммерческие → §1.2, §1.3, §1.6 [документация]
4. **FLUX.2 [dev] в коммерции — только через хостинг или платную лицензию**: fal `fal-ai/flux-2` $0,012/Мп (≈1,01 ₽,
   бейдж `commercial`) или BFL «Professional» (FLUX.2 [dev], 100K картинок/мес, 3 клиента включены; цены не опубликованы,
   23.09.2026) → §1.2 [документация]
5. **Qwen-Image-2.1 (веса с 20.09.2026) — Qwen Research License**, «for research or evaluation purposes only»; старые
   Qwen-Image 20B — Apache 2.0. Не переносить лицензию по имени семейства → §1.3 [документация]
6. **Ideogram 4 (открытые веса 9,3B)** прямо запрещает «generating Output to include in, or to advertise or promote,
   revenue-generating products or services» → коммерция только через API Ideogram или fal `ideogram/v4` → §1.6 [документация]
7. **Tencent Hunyuan (Image 2.1/3.0, Video 1.5) — не для сайтов с аудиторией ЕС/UK/Южной Кореи**: лицензия «DOES NOT APPLY
   IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA», запрещает показ выхода вне Территории и требует явной пометки
   «machine generated» в публичном контексте → §1.5 [документация]
8. **MiniMax H3 — ещё жёстче**: исключены ЕС, UK, Корея и **США**, надпись «MiniMax H3» в интерфейсе коммерческого
   продукта → для сайтов не использовать → §2.5 [документация]
9. **LTX-2 / 2.3 / 2.5 бесплатны при выручке группы < $10 млн в год**, но контент надо «expressly and intelligibly»
   помечать как машинный, водяные знаки и метаданные не удалять → §2.2 [документация]
10. **Самостоятельно разворачиваемый Wan — максимум 2.2** (Apache 2.0); весов Wan 2.5 / 2.6 / 2.7 / 3.0 нет, только API
    (HF Wan-AI, 23.09.2026) → §2.3 [документация]
11. **Генерацию (картинки и видео) на этой машине не планировать**: вендоры требуют от 8,19 ГБ (Wan2.1 1.3B) до
    ≥ 3×80 ГБ (HunyuanImage 3.0) видеопамяти NVIDIA; на Iris Xe проверен только запуск stable-diffusion.cpp → §1, §2, §8.2
    [документация; проверено: только запуск]
12. **rembg: всегда задавай модель явно** (`new_session("u2netp")`, `-m isnet-general-use`): в rembg 2.0.85 по умолчанию
    `bria-rmbg` = RMBG-2.0 (CC BY-NC 4.0, ≈1,02 ГБ скачивания) → §3.2 [проверено: код venv-p10]
13. **Локально для удаления фона — `u2netp` (0,10 с, 0,72 ГБ) или `isnet-general-use` (0,55 с, 1,48 ГБ)** на CPU;
    **BiRefNet-lite ONNX — 10 с и 6,5 ГБ RSS** на картинку → только по одной при ≥ 8 ГБ свободной памяти или хостинг
    fal `fal-ai/birefnet/v2` → §3.4, §10 [проверено]
14. **RMBG-1.4 и RMBG-2.0 — некоммерческие** (1.4 «source-available model for non-commercial use», 2.0 CC BY-NC 4.0);
    коммерчески — API Bria / fal / Replicate $0,018 (≈1,51 ₽) → §3.1 [документация]
15. **Матирование видео**: MatAnyone и MatAnyone 2 — S-Lab License (некоммерческая), RVM — GPL-3.0 и только люди;
    коммерчески чисто — покадрово BiRefNet/BEN2 или хостинг (fal `fal-ai/birefnet/v2/video`, Bria VRMBG 3.0) → §3.3 [документация]
16. **Сегментация**: SAM 2 / 2.1 — Apache 2.0; SAM 3 / 3.1 — SAM License (коммерция не запрещена, доступ к весам по
    ручному одобрению HF, пункт о санкциях) → §4 [документация]
17. **Глубина коммерчески — только Apache-модели**: Depth Anything V2 Small, DA3-Small, DA3-Base, DA3Mono-Large,
    DA3Metric-Large; V2 Base/Large/Giant и DA3 Large/Giant/Nested — CC BY-NC 4.0; Depth Pro по HF — research-only → §5 [документация]
18. **Глубина локально**: Depth Anything V2 Small ONNX fp32 — 0,25 с на 518², 0,41 ГБ, карта правдоподобна → годится для
    цепочки «2.5D-параллакс» (граф ассетов №5) → §5, §10 [проверено]
19. **Апскейл локально — `realesrgan-ncnn-vulkan -n realesrgan-x4plus` на Iris Xe**: ≈5 с на 1 Мп выхода, 0,7–1,3 ГБ
    памяти iGPU; всегда задавай `-n` (дефолт бинарника — `realesr-animevideov3`, README пишет x4plus) → §6.1 [проверено]
20. **x4plus съедает мелкий регулярный узор** (штриховка 6 px: ≈22 линии → ≈17) — бесшовные текстуры с тонким
    паттерном апскейлить только с проверкой глазами → §6.1 [проверено: 1 синтетический образец]
21. **SUPIR — только некоммерческий** («processing images that are intended for sale» — коммерция); **SeedVR2 — Apache 2.0**
    (картинки и видео, в обёртке ComfyUI сохраняет альфу) → §6.2 [документация]
22. **Интерполяция локально — `rife-ncnn-vulkan -m rife-v4.6`**: ≈0,17 с на кадр 720p в пакетном режиме на Iris Xe
    (CPU ≈0,75 с); для одиночных крошечных кадров `-g -1` быстрее → §6.3 [проверено]
23. **В сборке rife-ncnn-vulkan 20221029 модели только до v4.6**; автор RIFE советует 4.25 и «4.24+» для видео из
    диффузионных моделей → для 4.2x нужен PyTorch или хостинг (fal `fal-ai/rife/video` $0,0013/с GPU) → §6.3 [документация]
24. **StarVector — только иконки, логотипы, диаграммы** («will not work for natural images or illustrations»); OmniSVG 1.1
    8B — Apache 2.0, а OmniSVG-3B и 1.1-4B построены на Qwen2.5-VL-3B с лицензией `qwen-research` → §7 [документация; спорно]
25. **Трассировка растра в SVG локально — vtracer (MIT)**: `--preset poster`, `--palette '#…'` (ближайший цвет в OKLab),
    `--max-colors N`; potrace — GPL-2.0+ и только ч/б → §7.4 [документация]
26. **ComfyUI (GPL-3.0) не меняет лицензию весов**; запускай с `--disable-api-nodes`, чтобы не уйти в платные узлы → §8 [документация]
27. **Бейдж `commercial` у fal — условия fal, а не лицензия весов**: при self-host того же `flux-2` действует FLUX NCL → §11 [документация]
28. **Хостинг открытых моделей дешевле polza в 1,1–3,3 раза**: Z-Image Turbo fal $0,005/Мп (0,42 ₽) против polza 1,4 ₽;
    Qwen-Image Replicate $0,025 (2,10 ₽) против polza 2,25–3 ₽; Qwen-Image-2.1 KIE $0,02/$0,04 против polza 3/6 ₽ → §11 [документация]
29. **Публикуя выход Hunyuan, LTX, MiniMax — помечай на странице «сгенерировано ИИ»**: это прямые требования AUP (плюс
    EU AI Act ст. 50 — вопрос к L) → §9 [документация]
30. **Перед тяжёлым локальным шагом — `free -g`**: iGPU берёт ту же ОЗУ (x4plus 256² → 1,28 ГБ GPU-буферов), машина общая
    (во время P/10 свободно было 4,2–6,2 ГБ) → §10 [проверено]

## 1. Генерация картинок

### 1.1 Сводная таблица (23.09.2026)

Параметры — по HF API (`safetensors.total`, опыт P/09) или README; VRAM — как заявляет вендор (NVIDIA, bf16, если не
сказано иное); цены хостинга — по llms.txt fal, billingConfig Replicate, прайс-API KIE, каталогу polza.

| Модель (HF) | Параметры | Лицензия → коммерция self-host | VRAM (вендор) | Шаги · разрешение | Хостинг (цена) |
|---|---|---|---|---|---|
| `black-forest-labs/FLUX.2-dev` | 32,2B | FLUX Non-Commercial v2.1 → **нет** | «H100-equivalent»; 4-бит ≈18–20 ГБ | 50 (28 — компромисс), guidance 4; до 6 реф. | fal `fal-ai/flux-2` $0,012/Мп |
| `black-forest-labs/FLUX.2-klein-4B` (+ Base 4B) | 3,88B | **Apache 2.0 → да** | «~13GB» (HF, docs) / «~8GB» (GitHub) | 4 шага, guidance 1.0; до 4 реф. | fal `fal-ai/flux-2/klein/4b` $0,005/Мп; BFL $0,014 + $0,001/Мп; Replicate $0,001/Мп вход и выход |
| `…/FLUX.2-klein-9B` (+ 9B KV, Base 9B) | 9,08B | FLUX NCL → **нет** | «~29GB… RTX 4090» | 4 шага | fal `fal-ai/flux-2/klein/9b` $0,006/Мп; BFL $0,015 + $0,002/Мп |
| `Qwen/Qwen-Image` | 20,4B | **Apache 2.0 → да** | не указано; DiffSynth — «within 4GB VRAM» послойно | 50, `true_cfg_scale` 4; 1328², 16:9 1664×928 | fal `fal-ai/qwen-image` $0,02/Мп; Replicate `qwen/qwen-image` $0,025; polza `qwen/image` 2,25–3 ₽ |
| `Qwen/Qwen-Image-2512` | 20,4B | **Apache 2.0 → да** | — | 50; те же размеры (4:3 1472×1104) | fal `fal-ai/qwen-image-2512` $0,02/Мп |
| `Qwen/Qwen-Image-Edit-2509`, `-2511` | 20,4B | **Apache 2.0 → да** | — | 40, true_cfg 4; 1–3 входные картинки | fal `fal-ai/qwen-image-edit-2509`, `-2511` $0,03/Мп |
| `Qwen/Qwen-Image-Layered` | 20,4B | **Apache 2.0 → да** | — | 50; `resolution` 640 (рекоменд.) или 1024; `layers` 3–8+ | fal `fal-ai/qwen-image-layered` $0,05 за картинку |
| `Qwen/Qwen-Image-2.1` | 7,12B | Qwen Research → **нет** | — | 40; 2K; RGBA; до 10 реф. | polza `qwen/image-2.1` 3/6 ₽; KIE $0,02/$0,04 |
| `Tongyi-MAI/Z-Image-Turbo` | 6,15B | **Apache 2.0 → да** | «16G VRAM consumer devices»; sd.cpp «4GB» | 8 NFE (`num_inference_steps=9`), guidance 0 | fal $0,005/Мп; tiling $0,02/Мп; KIE $0,004; polza 1,4 ₽ |
| `Tongyi-MAI/Z-Image` (база) | 6,15B | **Apache 2.0 → да** | — | 28–50, CFG 3–5, негатив «strongly recommended»; 512²…2048² | fal `fal-ai/z-image/base` |
| `tencent/HunyuanImage-2.1` | 17B | Tencent Hunyuan Community → **условно** (не ЕС/UK/KR) | 24 ГБ (FP8 + выгрузка) | только 2K; 50 / 8 (distilled) + refiner | fal `fal-ai/hunyuan-image/v2.1/text-to-image` $0,1/Мп |
| `tencent/HunyuanImage-3.0` (+ Instruct, Distil) | 80B MoE, 13B акт. (83,0B в safetensors) | то же → **условно** | ≥ 3×80 ГБ; Instruct ≥ 8×80 ГБ | 50 / 8 (Distil) | fal $0,1/Мп; Replicate $0,08 |
| `ideogram-ai/ideogram-4-fp8` / `-nf4` | 9,3B | Ideogram 4 Non-Commercial → **нет** | nf4 — CUDA; fp8 — «All» | пресеты 12 / 20 / 48 шагов; 256–2048, до 6:1 | fal `ideogram/v4` $0,0075 / 0,015 / 0,025 за Мп (TURBO / BALANCED / QUALITY); + `fast`, `instant`, `tiling` — commercial |

Выводы для маршрутизации (детали — §1.2–§1.6):

- Self-host с коммерцией без условий — только строки «Apache 2.0 → да» [документация].
- Самая дешёвая генерация на 23.09.2026 — открытые модели на хостинге: klein 4B на Replicate $0,001 за 1 Мп выхода
  (+ $0,001/Мп за входные референсы), klein 4B и Z-Image Turbo на fal $0,005/Мп (0,42 ₽), klein 9B на fal $0,006/Мп
  [документация; качество — у C1].
- Прозрачность из текста — Qwen-Image-2.1 (некоммерческие веса; через polza/KIE — статус выхода не раскрыт, [спорно]);
  разложение готовой картинки на слои RGBA — Qwen-Image-Layered (Apache 2.0) [документация].

### 1.2 FLUX.2 [dev] и [klein] (Black Forest Labs)

- Линейка открытых весов [S1][S3][S4][S47]: [dev] 32B (HF-репозиторий создан 22.11.2025, «guidance-distilled»), [klein] 4B и 9B
  (15.01.2026, «step-distilled» до 4 шагов, 9B — «9B flow model with 8B Qwen3 text embedder»), 9B KV (09.03.2026,
  KV-кэш для мульти-референсной правки), Base 4B/9B (без дистилляции, для дообучения; «not offered on the public API»),
  fp8/NVFP4-варианты, `FLUX.2-small-decoder` (06.04.2026, Apache 2.0). Автоэнкодер FLUX.2 — Apache 2.0 отдельно [S1].
- **Лицензия FLUX Non-Commercial v2.1** [S2] (для [dev] — «FLUX [dev] Non-Commercial License v2.0», текст по сути тот же):
  - разрешено только «Non-Commercial Purpose»; «For clarity, use (a) for revenue-generating activity, (b) in direct
    interactions with or that has impact on end users, or (c) to train, fine tune, or distill other models for commercial
    use… is not a Non-Commercial Purpose»;
  - §2(d): «You may use Output for any purpose (including for commercial purposes), except as expressly prohibited herein»,
    но §4(a) запрещает использовать модель «(or any data produced by the FLUX Model)… for any commercial or production
    purposes» → генерация ассетов для клиентского сайта = запуск модели в коммерческих целях → **[спорно], считать
    запрещённым** до разбора у L;
  - §2(e): обязательны фильтры контента **или** ручная проверка каждого выхода + раскрытие ИИ «to the extent required
    under applicable law»; карточка [dev]: «We may approach known deployers… to verify that filters or manual review
    processes are in place» [S3];
  - §4(f)(iv–v): нельзя пользоваться из «comprehensively sanctioned jurisdiction» и «disguise your location through IP
    proxying» → работа через VPN из России — вопрос к L [спорно].
- **Коммерческие пути** [S3][S5]: (1) klein 4B / Base 4B по Apache 2.0 (фильтры «encourage», не обязательны); (2) хостинг:
  fal `fal-ai/flux-2` (= [dev]) $0,012/Мп и `fal-ai/flux-2/klein/9b` $0,006/Мп с бейджем `commercial` [S43], BFL API
  klein 4B $0,014 + $0,001/Мп, klein 9B $0,015 + $0,002/Мп [S4]; (3) лицензия BFL на веса (bfl.ai/licensing, цен нет):
  Builder — klein, 10K картинок/мес, 1 домен, «Not meant for client use or downstream applications»; Platform — Base 9B +
  [dev], 100K/мес, 1 домен (SaaS); **Professional — [dev], 100K/мес, до 3 доменов, «for agencies… on behalf of named
  clients. The first 3 clients are included»**; Enterprise — индивидуально [S5].
- Память и скорость [S1][S3][S6]: klein 4B — «~13GB VRAM» (карточка HF и docs.bfl.ml) против «fits in ~8GB VRAM»
  (README GitHub) — противоречие вендора; «sub-second» на потребительских GPU [мнение вендора]; klein 9B «~29GB»;
  [dev]: «Even an H100 can't hold the text-encoder, transformer and VAE at the same time», 4-бит (`diffusers/FLUX.2-dev-bnb-4bit`)
  + удалённый текст-энкодер ≈18 ГБ, 4-бит + 4-бит энкодер ≈20 ГБ (RTX 4090/5090). Промпт-апсемплинга у klein нет —
  писать подробный промт [S4].
- Локально здесь: stable-diffusion.cpp поддерживает FLUX.2-dev (30.11.2025) и FLUX.2-klein (18.01.2026) в GGUF с Vulkan
  [S41]; генерация на Iris Xe не проверялась [не проверено].

```python
# diffusers (main) · FLUX.2 [klein] 4B · Apache 2.0 · по карточке HF [S3] · [не проверено здесь: нужна NVIDIA ~13 ГБ]
import torch
from diffusers import Flux2KleinPipeline
pipe = Flux2KleinPipeline.from_pretrained("black-forest-labs/FLUX.2-klein-4B", torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()
img = pipe(prompt="…", height=1024, width=1024, guidance_scale=1.0, num_inference_steps=4,
           generator=torch.Generator("cuda").manual_seed(0)).images[0]
```

### 1.3 Семейство Qwen-Image (Alibaba Qwen)

- **Qwen-Image** (веса 04.08.2025, 20B MMDiT, Apache 2.0) [S7][S8]: 50 шагов, `true_cfg_scale=4.0`, негатив поддерживается;
  «exceptional performance in text rendering, especially for Chinese» [мнение вендора]; «positive magic» в примере —
  «, Ultra HD, 4K, cinematic composition.»; размеры: 1:1 1328², 16:9 1664×928, 9:16 928×1664, 4:3 1472×1140, 3:2 1584×1056.
  Сообщество: DiffSynth-Studio — «layer-by-layer offload (inference within 4GB VRAM), FP8»; Qwen-Image-Lightning
  (LightX2V) — «25x reduction in DiT NFEs… 42.55x overall speedup» [мнение вендора]; ComfyUI — нативно с 05.08.2025 [S8].
- **Qwen-Image-Edit-2509** (22.09.2025, Apache 2.0) [S7]: мульти-картинка — «Optimal performance is currently achieved
  with 1 to 3 input images»; согласованность людей, продуктов («product poster editing»), текста (шрифт, цвет, материал);
  «Native Support for ControlNet: Including depth maps, edge maps, keypoint maps». `QwenImageEditPlusPipeline`,
  40 шагов, `true_cfg_scale=4.0`, `guidance_scale=1.0`.
- **Qwen-Image-Edit-2511** (23.12.2025, Apache 2.0) [S7]: «mitigate image drift, improved character consistency,
  integrated LoRA capabilities [освещение, новые ракурсы], enhanced industrial design generation, strengthened geometric
  reasoning». Для сайтов — правка продукта и замена материала (граф ассетов №11) [не проверено].
- **Qwen-Image-Layered** (19.12.2025, arXiv 2512.15603, Apache 2.0) [S7][S8]: картинка → N слоёв RGBA (3, 4, 8…,
  рекурсивно любой слой ещё раз), экспорт в pptx/zip/psd (`src/app.py`), правка слоя через Qwen-Image-Edit
  (`src/tool/edit_rgba_image.py`), сборка обратно (`combine_layers.py`). Ограничения вендора: «The released weights are
  specifically fine-tuned for the image-to-multi-RGBA decomposition task… text-to-multi-RGBA generation is limited»;
  `resolution` 640 рекомендован → слои около 640 px, для hero нужен апскейл каждого слоя [не проверено]. Прямой кандидат
  для цепочек №6 «слои-параллакс» и №4 «объект без фона».
- **Qwen-Image-2512** (31.12.2025, Apache 2.0) [S7]: «Enhanced Human Realism… Finer Natural Detail… Improved Text Rendering»;
  «strongest open-source model» по 10 000+ слепым раундам AI Arena Alibaba [мнение вендора].
- **Qwen-Image-2.0** (10.02.2026) — только API и Qwen Chat, весов нет [S8]. **Qwen-Image-2.1** (веса 14–20.09.2026, 7,12B,
  «7B parameters in its visual generation component (32 Single-Stream DiT layers)»): t2i + правка в одних весах, **RGBA
  из текста** (рекомендуемый промт «This is an RGBA image with transparency. … The image has alpha channel and the background
  is transparent.»), до 10 референсов, маски, 2K, 40 шагов, рерайтеры `Qwen-Image-2.1-PE-T2I/-PE-I2I` [S9].
  Лицензия: «Qwen RESEARCH LICENSE AGREEMENT Release Date: September 20, 2026»; «"Non-Commercial" shall mean for research
  or evaluation purposes only»; «You shall not use the Materials for any commercial purpose without obtaining a separate
  commercial license from us… model-business@notice.qwencloud.com»; право КНР, суды Ханчжоу [S9]. polza `qwen/image-2.1`
  (mie/KIE, 3/6 ₽) и KIE ($0,02/$0,04) — есть ли у них коммерческая лицензия Alibaba, не раскрыто [спорно, вопрос к L и P].
- Локально: stable-diffusion.cpp — Qwen-Image (12.10.2025), Edit/2509 (13.10.2025), **2.1 — «Day-0» (20.09.2026)** [S41];
  на Iris Xe не проверялось [не проверено].

### 1.4 Z-Image и Z-Image-Turbo (Tongyi-MAI, Alibaba)

- 6,15B, «Scalable Single-Stream DiT (S3-DiT)»; Apache 2.0 [S11]. **Turbo** (26.11.2025): 8 NFE — в diffusers
  `num_inference_steps=9` («This actually results in 8 DiT forwards»), `guidance_scale=0.0` («Guidance should be 0 for the
  Turbo models»), «sub-second inference latency on enterprise-grade H800 GPUs and fits comfortably within 16G VRAM consumer
  devices», «bilingual text rendering (English & Chinese)» — кириллица не заявлена [S11]. **База** (27.01.2026): 28–50 шагов,
  guidance 3,0–5,0, «Negative prompts: Strongly recommended», `cfg_normalization` False для стилизации / True для реализма,
  512²…2048² [S11]. **Z-Image-Omni-Base и Z-Image-Edit — «To be released»** (README на 23.09.2026) [S11].
- Для сайтов: самый дешёвый перебор направлений (граф ассетов №16) и **бесшовные текстуры** — fal
  `fal-ai/z-image/turbo/tiling` ($0,02/Мп, `tiling_mode` both/horizontal/vertical); настоящий тайлинг подтверждён на
  публичном образце [проверено].
- Локально: stable-diffusion.cpp с Z-Image «on machines with as little as 4GB of VRAM» [S11][S41] — на Iris Xe не
  проверено; кандидат для отдельного опыта H/E (GGUF Q4, 512², 8 шагов) [не проверено].

### 1.5 HunyuanImage 2.1 и 3.0 (Tencent)

- **2.1** (08.09.2025): 17B, «only supports 2K image generation (e.g. 2048x2048 for 1:1 images, 2560x1536 for 16:9)», база
  50 шагов (guidance 3,5, shift 5) и distilled 8 шагов (3,25, shift 4) + refiner; ByT5 «Glyph-Aware Processing»; FP8
  «2K images with only 24GB GPU memory» (с выгрузкой на CPU) [S12].
- **3.0** (28.09.2025): «80 billion parameters, with 13 billion activated per token» (MoE, 64 эксперта), «Recommended VRAM
  ≥ 3 × 80 GB»; Instruct и Instruct-Distil (26.01.2026, 8 шагов) — «≥ 8 × 80 GB» [S13].
- **Лицензия TENCENT HUNYUAN COMMUNITY** (тексты 2.1, 3.0 и Video-1.5 сверены — по сути одинаковы) [S12]:
  - «THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA»; «Territory… excluding the
    territory of the European Union, United Kingdom and South Korea»;
  - §5(c): «You must not use, reproduce, modify, distribute, or display the Tencent Hunyuan Works, **Output** or results of the
    Tencent Hunyuan Works outside the Territory» → картинка на сайте, открытом из ЕС, формально «display… outside the
    Territory» [спорно, к L];
  - AUP п. 12: нельзя размещать сгенерированное «in any public context… without expressly and conspicuously identifying that
    the information and/or content is machine generated»;
  - §3(e): если сервис для третьих лиц — «disclose to all end users the full legal name and entity of the actual provider» и
    что Tencent не связан; §4: > 100 млн MAU — отдельная лицензия; §6(d): «Tencent claims no rights in Outputs»; право
    Гонконга.
- Вывод: для сайтов заказчика Hunyuan-картинки не брать ни локально, ни через хостинг (fal `fal-ai/hunyuan-image/v3/*`
  $0,1/Мп, Replicate `tencent/hunyuan-image-3` $0,08) без решения L [документация].

### 1.6 Ideogram 4 (открытые веса) и прочие

- **Ideogram 4** (03.06.2026, 9,3B, «trained from scratch», single-stream DiT 34 слоя) [S15]: веса gated на HF —
  `ideogram-ai/ideogram-4-nf4` (CUDA, есть diffusers) и `-fp8` («All» — любое железо, без diffusers); пресеты
  `V4_QUALITY_48` (48 шагов, по умолчанию), `V4_DEFAULT_20`, `V4_TURBO_12`; размеры кратно 16, 256–2048, до 6:1 (баннер
  1600×400); промт — структурный JSON, проза переписывается «magic prompt» (бесплатный API Ideogram или своя LLM);
  модерация через Hive (свои ключи) [S15]. Подробно о JSON-промте — у C1 (`99-raw/notes/wave1/C1-notes.md` §10).
- **Лицензия «Ideogram Non-Commercial Model Agreement» (03.06.2026)** [S15]: «any use that involves… generating Output to
  include in, or to advertise or promote, revenue-generating products or services… is not a Non-Commercial Purpose»;
  «non-production environment» — только тестирование; нельзя обучать конкурирующие модели на выходах. → В отличие от FLUX,
  запрет на коммерческий выход записан прямо. Коммерция — API Ideogram (у C1/P в файле 04) или fal `ideogram/v4`,
  `ideogram/v4/tiling` (бейдж `commercial`) [S43].
- Не изучались подробно (при необходимости проверить LICENSE): HiDream-I1-Full (17,1B, тег HF `mit`), Stable Diffusion
  3.5 Large (8,1B, `stabilityai-ai-community`, gated) [S47] [не проверено].

## 2. Видео

### 2.1 Сводная таблица (23.09.2026)

| Модель | Параметры | Лицензия → коммерция self-host | VRAM (вендор) | Выход | Хостинг (цена) |
|---|---|---|---|---|---|
| LTX-2.5 (`Lightricks/LTX-2.5`, gated) | 22B DiT + Gemma 4 12B энкодер | LTX-2.x Community → **да при выручке < $10 млн** | весь набор ≈66 GiB; `fp8-cast` + выгрузка | 1024×1536 @ 24 fps по умолч., до 3840×2176; звук | fal `lightricks/ltx-2.5/text-to-video/fast` $0,09/с 720p, $0,13 1080p, $0,19 1440p, $0,30 4K (звук включён); `…/pro` $0,12 720p, $0,17 1080p |
| LTX-2.3 / LTX-2 | 22B / 18,9B | LTX-2 Community (05.01.2026) → то же | — | 24 fps, до 4K | fal `fal-ai/ltx-2.3/text-to-video` $0,08/с 1080p, $0,16 1440p, $0,32 2160p; `…/image-to-video/fast` $0,06/с |
| Wan2.2 TI2V-5B | 5B | **Apache 2.0 → да** | «at least 24GB VRAM (e.g, RTX 4090)» | 720P (1280×704) @ 24 fps; «5-second 720P… under 9 minutes» | fal `fal-ai/wan/v2.2-5b/text-to-video` $0,15 за ролик (до 5 с 720p); KIE Wan 2.2 5 с 480p $0,20, 720p $0,40 |
| Wan2.2 T2V/I2V-A14B | MoE 27B (14B акт.) | **Apache 2.0 → да** | «at least 80GB VRAM» (1 GPU с выгрузкой) | 480P/720P | fal `fal-ai/wan/v2.2-a14b/text-to-video` $0,04/с 480p, $0,06 580p, $0,08 720p («video seconds… at 16 frames per second») |
| Wan2.1 T2V-1.3B / 14B, FLF2V-14B-720P, VACE | 1,3B / 14,3B / 16,4B / 17,3B | **Apache 2.0 → да** | 1.3B — «only 8.19 GB VRAM» | 480P (1.3B), 720P (14B); FLF — первый+последний кадр | fal `fal-ai/wan-flf2v`, `fal-ai/wan-vace-14b/*` |
| HunyuanVideo-1.5 | 8,3B | Tencent Hunyuan Community → **условно** (не ЕС/UK/KR) | «Minimum GPU Memory: 14 GB (with model offloading)» | 480p/720p + SR до 1080p, 121 кадр по умолч. | fal `fal-ai/hunyuan-video-v1.5/image-to-video` $0,075/с |
| MiniMax-H3 | 33,1B | MiniMax H3 Community → **нет для сайтов** (исключены ЕС, UK, KR, США) | пример SGLang на 4 GPU | 24 FPS, короткая сторона 768; 2K — только API | API MiniMax, fal (H3 Max — у C2) |

Вывод: для этой машины видео-генерация недоступна (нет NVIDIA; минимальные требования 8–24 ГБ VRAM), GPU-сервер заказчика
для генерации не рассматривается (решение заказчика) → открытые видео-модели полезны **только как дешёвый хостинг** и как
источник приёмов (ключевые кадры, петли, LoRA) [документация].

### 2.2 LTX-2 / 2.3 / 2.5 (Lightricks)

- Лицензии [S16]: файл `LICENSE` — указатель: «LTX-2 Community License Agreement… applicable to all LTX-2 versions released
  since January 5, 2026, including LTX-2.3 until August 11, 2026»; «LTX-2.x Community License Agreement… applicable to all
  LTX-2.5 versions released since August 11, 2026».
- Суть обеих: лицензия «for any purpose», **но «Entities with annual revenues of at least $10,000,000»** (с учётом всех
  аффилированных компаний) обязаны купить «Commercial Use Agreement» (в 2.x — ltxv-licensing@lightricks.com); в LICENSE-2
  за нарушение — «liquidated damages… double the amount» [S16]. Карточка LTX-2.5: «Under $10M annual revenue — Commercial and
  production use at no cost» [S17].
- Ограничения, важные для сайтов [S16]: Attachment A п. 5 — нельзя размещать контент «in any context… without expressly and
  intelligibly disclaiming that the information and/or content is machine generated» (→ пометка на странице обязательна);
  п. 20 — нельзя в продукте, конкурирующем с Lightricks; LICENSE-2_x §6 — соблюдать EU AI Act и California AI Transparency
  Act, **не удалять водяные знаки, метаданные, «latent disclosure»** выходов (иначе отзыв лицензии); §7 — нельзя из стран под
  всеобъемлющими санкциями и лицам из списков SDN.
- Технически [S16][S17]: LTX-2.5 — 22B, distilled (8 шагов, CFG=1) и dev; новый диффузионный видео-декодер; нативный
  мульти-шот; предсказатель длительности (`--num-frames` можно опустить); латентные апскейлеры ×2 по пространству и времени;
  конвейеры `DistilledPipeline`, `DFRPipeline` (production), `KeyframeInterpolationPipeline`, `RetakePipeline` (перегенерация
  участка), `ICLoraPipeline`, HDR/EXR; загрузка distilled-набора «roughly 66 GiB»; по умолчанию 1024×1536 @ 24 fps, UHD —
  `--width 3840 --height 2176`.
- LoRA вендора 2026 года, полезные сайтам (HF Lightricks, P/09): **Cinemagraph** (2.3 — 05.07, 2.5 — 10.09.2026) —
  прямо задача `VID-CINEMAGRAPH`; Slow-Motion-Control (15.09), Water-Simulation, Clean-Plate, Day-To-Night, Colorization,
  Deblur, Decompression, In-Outpainting, Pixel-Spatial-Upscaler. Часть есть как готовые эндпоинты fal
  `fal-ai/ltx-2.3-quality/{clean-plate,water-simulation,day-to-night,outpaint,hdr,…}` [S43] [не проверено: качество].

### 2.3 Wan 2.1 / 2.2 и статус Wan 2.5+

- Wan2.2 (28.07.2025, Apache 2.0: «We claim no rights over the your generated contents») [S18]: A14B — MoE «two-expert
  design… total of 27B parameters but only 14B active», 480P и 720P, «at least 80GB VRAM»; **TI2V-5B** — VAE 16×16×4,
  720P (1280×704) @ 24 fps, «at least 24GB VRAM (e.g, RTX 4090)», «5-second 720P video in under 9 minutes on a single
  consumer-grade GPU»; S2V-14B, Animate-14B, в 2026 — Wan2.2-Animate-2-14B (06.08.2026) и Wan-Dancer-14B (10.07.2026) [S47].
- Wan2.1 [S18]: T2V-1.3B — «only 8.19 GB VRAM… 5-second 480P video on an RTX 4090 in about 4 minutes»; **FLF2V-14B-720P**
  (первый + последний кадр, 17.04.2025) — «recommend using Chinese prompt»; VACE 1.3B/14B (правка, маски, аутпейнт кадра).
- **Статус Wan 2.5 / 2.6 / 2.7 / 3.0**: у организации Wan-AI на HF весов новее 2.2 нет (27 репозиториев, 23.09.2026) [S47];
  Alibaba Model Studio выставляет `wan2.5-t2v-preview`, `wan2.6-*`, `wan2.7-*`, `wan3.0-video` только как API (заметки C2 §6).
  SEO-сайты «Wan 2.5 open source» — не источник. → Wan выше 2.2 = закрытая модель (polza `wan/2.5`, `wan/2.6`,
  `alibaba/wan-3.0`) [документация].
- Петли на открытых моделях: одинаковый первый и последний кадр в Wan2.2 FLF2V «degenerates to a nearly static video»
  (исследование Loopy, ACM TOG 2026, по заметкам C2 §17); метод Loopy (сдвиг RoPE) работает на открытых Wan 2.1/2.2 и
  HunyuanVideo 1.5 — но требует своего GPU, поэтому для нас неприменим [исследование; не проверено].

### 2.4 HunyuanVideo 1.5 (Tencent)

- 8,3B DiT + 3D causal VAE (сжатие 16× по пространству, 4× по времени), SSTA-внимание; 480p и 720p, SR-сеть до 1080p;
  121 кадр по умолчанию, 50 шагов; «Minimum GPU Memory: 14 GB (with model offloading enabled)»; 480p I2V step-distilled
  (05.12.2025) — «a single RTX 4090 can generate videos within 75 seconds»; Wan2GP — «as low 6 GB of VRAM»; кэш-ускорения
  deepcache / teacache / taylorcache [S14].
- Лицензия — та же Tencent Hunyuan Community (§1.5): не ЕС/UK/KR, пометка машинной генерации в публичном контексте [S12][S14].

### 2.5 MiniMax H3 (открытые веса H3-Base)

- 33B «dense, single-stream Transformer» (≈13B в AdaLN-ветвях, для инференса предвычисляются), 24 FPS, стерео-звук,
  короткая сторона 768 по умолчанию, до 15 с; **открыт только H3-Base** — «H3-Context-IR… is not included in this
  open-source release», H3-Regenerate-2K «is not yet open-sourced» (оба — только API); пример SGLang `--num-gpus 4` [S19].
- **Лицензия MiniMax H3 Community** [S19]: «Excluded Territories means the European Union, the United Kingdom, the Republic of
  Korea and the United States of America»; нельзя «use, reproduce, modify, distribute, or display… Outputs… outside the
  Applicable Territory»; > $20 млн годовой выручки — письменное разрешение; «prominently display "MiniMax H3" on the user
  interface of commercial product or service»; AUP п. 12 — «clearly and prominently disclosing that such information… is
  machine-generated». → Для сайтов заказчика не использовать ни локально, ни как основание для хостинга без L.

## 3. Удаление фона и матирование

### 3.1 Картинки: модели и лицензии

| Модель | Размер | Лицензия → коммерция | Вход модели | Заметки | Хостинг (цена) |
|---|---|---|---|---|---|
| BiRefNet (general, SwinL) | 221M | **MIT → да** | 1024² (есть 2048² HR, dynamic 256–2304) | RTX 4090 FP16 57,7 мс (17 FPS), память 3,5 ГБ FP16 / 4,8 ГБ FP32; ONNX на 75–90 % медленнее | fal `fal-ai/birefnet/v2` (по GPU-секундам) |
| BiRefNet_lite (SwinT) | 44M | **MIT → да** | 1024² (lite-2K — 2560×1440) | здесь на CPU: 10 с, 6,5 ГБ RSS [проверено] | fal (в списке `model`) |
| BiRefNet-matting / HR-matting / portrait | 221M | **MIT → да** | 1024² / 2048² | мягкая альфа (волосы) | fal `model: Matting` |
| BEN2 (Base) | 95M | **MIT → да** (Base); полная модель — API вендора | 1024² | «Confidence Guided Matting», видео-режим | fal `fal-ai/ben/v2/image` $0,025/Мп, `…/video` |
| RMBG-1.4 (Bria) | 44M | bria-rmbg-1.4 → **нет** | — | «source-available model for non-commercial use» | — |
| RMBG-2.0 (Bria) | 221M | CC BY-NC 4.0 → **нет** | 1024² | архитектура BiRefNet на данных Bria | fal `fal-ai/bria/background/remove` $0,018; Replicate `bria/remove-background` $0,018 |
| U²-Net / u2netp (rembg) | 176 / 4,6 МБ | Apache 2.0 (репозиторий) → да | 320² | блочные края, помогает `-a` | fal `fal-ai/imageutils/rembg` (по GPU-секундам) |
| IS-Net `isnet-general-use` (rembg) | 179 МБ | код Apache 2.0; **лицензия весов не указана**, датасет DIS5K — «non-commercial» → **спорно** | 1024² | здесь 0,55 с [проверено] | — |

Источники таблицы: [S20][S21][S22][S23]; U²-Net и DIS — LICENSE репозиториев (Apache 2.0) и «DIS5K Terms of Use»:
«The Dataset is available for non-commercial use… commercial use of this dataset is prohibited even after copying,
editing, processing» [S23]. Для BiRefNet автор прямо даёт MIT; README BiRefNet отдельно предупреждает про RMBG-2.0: «their
weights are for only non-commercial use» [S20].

### 3.2 rembg 2.0.85 — ловушки (проверено в коде 23.09.2026)

- **Модель по умолчанию — `bria-rmbg`** (веса `bria-rmbg-2.0.onnx`, ≈1,02 ГБ, CC BY-NC): `session_factory.py:
  model_name: str = "bria-rmbg"`, `bg.py: new_session("bria-rmbg")`, во всех CLI-командах `default="bria-rmbg"`
  [проверено]; README: «bria-rmbg… **The default**… requires a
  paid agreement for commercial use. Model weights carry their own licenses, independent of rembg's MIT license» [S23].
  Вызов `remove(img)` без сессии = некоммерческая модель + скачивание 1 ГБ.
- **`withoutbg` — облачный API**, не локальная модель: «Images are sent to withoutBG's servers; max upload size is 20 MB» [S23].
- CLI не входит в `rembg[cpu]`: нужен `rembg[cpu,cli]`, иначе только Python API [проверено].
- Края [S23]: по умолчанию «naive»; `-dc` (деконтаминация цвета, «negligible» цена) — включать на цветном фоне; `-a` (alpha
  matting) — медленно, «can fail to converge»; `-vm` (ViTMatte, +≈110 МБ) — для волос; `-ppm` — бинарная маска (с `-dc`
  бессмысленно). Для старых моделей (`u2net`, `u2netp`) `-a` помогает больше всего.
- Хранилище моделей: `REMBG_HOME` (по умолчанию `~/.rembg`), устаревший `U2NET_HOME` приоритетнее; `OMP_NUM_THREADS` —
  потоки ORT; `MODEL_CHECKSUM_DISABLED=1` — свои ONNX без перекачки [S23].

```python
# rembg 2.0.85 + onnxruntime 1.30 (CPU) · venv 99-raw/tools/venv-p10 · [проверено]
import os
os.environ.setdefault("REMBG_HOME", "/путь/к/моделям")      # не засорять ~/.rembg
from rembg import new_session, remove
from PIL import Image
sess = new_session("isnet-general-use")                     # ЯВНО; дефолт — bria-rmbg (CC BY-NC)
out = remove(Image.open("in.png"), session=sess, decontaminate=True)   # -dc: убрать цветной ореол
out.save("out.png")                                         # RGBA
```

### 3.3 Видео: матирование и удаление фона

| Инструмент | Лицензия → коммерция | Что нужно на вход | Скорость (вендор) | Хостинг |
|---|---|---|---|---|
| MatAnyone (CVPR 2025) / MatAnyone 2 (CVPR 2026) | S-Lab License 1.0 → **нет** | видео + маска первого кадра (из SAM 2) | 720p/1080p, `--max_size` | нет на fal/Replicate (23.09.2026) |
| RobustVideoMatting | **GPL-3.0** → спорно (копилефт) | только видео, **только люди** | «4K 76FPS and HD 104FPS on an Nvidia GTX 1080 Ti» | Replicate `arielreplicate/robust_video_matting` (по GPU-времени) |
| BiRefNet покадрово | MIT → да | кадры | как картинки (§3.1) | fal `fal-ai/birefnet/v2/video` |
| BEN2 видео-режим | MIT (Base) → да | видео | — | fal `fal-ai/ben/v2/video` |
| Bria VRMBG 3.0 | коммерческий API | видео | «Realtime» вариант | fal `bria/video/background-removal/v3`, `…/realtime`, `…/green-screen-despill` |

- S-Lab License: «Redistribution and use for non-commercial purpose… In the event that redistribution and/or use for
  commercial purpose… is required, please contact the contributor(s)» [S25]. RVM: «Code is re-released under GPL-3.0
  license»; ONNX (opset 12) «Tested on ONNX Runtime with CPU», есть TF.js int8 и CoreML [S26] — технически RVM MobileNetV3
  годится для CPU, но GPL-копилефт в закрытом конвейере — вопрос к L [спорно].
- Для задачи `VID-ALPHA` на сайтах практичнее сгенерировать объект на ровном фоне и матировать покадрово BiRefNet
  (MIT) или хромакеем ffmpeg, затем VP9-alpha + stacked alpha — это тема агента I [не проверено].

### 3.4 Что из этого запускается здесь (кратко; полностью — §10)

u2netp — 0,10–0,12 с инференса, 0,72 ГБ RSS; isnet-general-use — 0,55–0,58 с, 1,48 ГБ; BiRefNet-lite ONNX — 10,1 с
(повтор 25 с из-за нехватки памяти), 6,52 ГБ RSS. Все три срезают мягкую тень объекта; isnet оставил полупрозрачное пятно
на «коробке» синтетического образца [проверено: P/10, 1 образец 256×256].

## 4. Сегментация (SAM 2 / 2.1, SAM 3 / 3.1)

- **SAM 2.1** (Apache 2.0 — «The SAM 2 model checkpoints, SAM 2 demo code… and SAM 2 training code are licensed under
  Apache 2.0») [S24]: tiny 38,9M — 91,2 FPS, small 46M — 84,8, base+ 80,8M — 64,1, large 224,4M — 39,5 FPS (A100, torch
  2.5.1); картинки и видео (streaming memory). Роль в конвейере: маска первого кадра для матирования (§3.3), отделение
  переднего плана для «слоёв-параллакса» (граф ассетов №6).
- **SAM 3** (веса на HF — ноябрь 2025, 848M) [S24][S47]: «exhaustively segment all instances of an open-vocabulary concept specified by a
  short text phrase or exemplars» — маска по слову («cup», «person in red»), трекинг в видео; **SAM 3.1 Object Multiplex
  (27.03.2026)** — быстрее для многих объектов. Веса gated «manual» на HF (нужен запрос доступа) [S47].
- **SAM License** (19.11.2025) [S24]: грант «to use, reproduce, distribute, copy, create derivative works of, and make
  modifications» без запрета коммерции; условия: соблюдать Trade Controls («You are not the target of Trade Controls»; санкции
  США, ООН, ЕС, UK), не разбирать модель (reverse engineering), упоминать SAM в публикациях; право Калифорнии → коммерция
  разрешена, но доступ из России и одобрение запроса HF — [спорно].
- Хостинг: fal `fal-ai/sam-3/image` $0,005 за запрос (0,42 ₽), `fal-ai/sam-3/video`, `fal-ai/sam-3-1/*`; `fal-ai/sam2/*`
  (license None в каталоге fal) [S43]. Локально SAM 2 tiny на CPU здесь не проверялся [не проверено].

## 5. Глубина (Depth Anything V2 / 3, Depth Pro)

| Модель | Параметры | Лицензия → коммерция | Что выдаёт | Заметки |
|---|---|---|---|---|
| Depth Anything V2 Small | 24,8M | **Apache 2.0 → да** | относительная (диспаритет) | ONNX 99 МБ (fp32) / 27 МБ (int8) / 19 МБ (q4f16); здесь 0,25 с на 518² [проверено] |
| Depth Anything V2 Base / Large / Giant | 97,5M / 335,3M / 1,3B | **CC BY-NC 4.0 → нет** | относительная | Large лучше держит видео («better temporal consistency») |
| DA3-Small / DA3-Base | 0,08B / 0,12B | **Apache 2.0 → да** | глубина + лучи/поза (any-view) | 13.11.2025 |
| **DA3Mono-Large** | 0,35B | **Apache 2.0 → да** | относительная **глубина (не диспаритет)** | «superior geometric accuracy» [мнение вендора] |
| DA3Metric-Large | 0,35B | **Apache 2.0 → да** | метрическая: `focal * net_output / 300` | + сегментация неба |
| DA3-Large (-1.1), DA3-Giant (-1.1), DA3Nested | 0,35B / 1,15B / 1,40B | **CC BY-NC 4.0 → нет** | any-view, 3DGS | «-1.1… prefer these»; **README — CC BY-NC, тег HF у DA3-LARGE-1.1 — apache-2.0** → брать строгое |
| Depth Pro (Apple) | — | HF: `apple-amlr` («exclusively for Research Purposes») → **нет**; README GitHub: веса «under the [LICENSE] terms» | метрическая + фокусное | «2.25-megapixel depth map in 0.3 seconds on a standard GPU» |

- Источники: [S27] («Depth-Anything-V2-Small model is under the Apache-2.0 license. Depth-Anything-V2-Base/Large/Giant models
  are under the CC-BY-NC-4.0 license»), [S28] (таблица лицензий DA3), [S29] (AMLR: «"Research Purposes" does not include any
  commercial exploitation, product development or use in any commercial product or service»), [S47] (теги HF).
- Для сайтов (граф ассетов №5 «2.5D-глубина» и 3d `01` §9.5): локально — DA-V2 Small ONNX (готов, §10); если нужна
  геометрически точнее — DA3Mono-Large (Apache 2.0; ONNX-сборку не искал) [не проверено]; видео-глубина — Video-Depth-Anything
  Small (Apache 2.0 по тегу HF) или fal `fal-ai/depth-anything-video` $0,04/с (3,36 ₽/с) [S43][S47].
- **В браузере**: `onnx-community/depth-anything-v2-small` сделан для Transformers.js (`pipeline('depth-estimation', …)`) —
  карту глубины можно считать на клиенте (WebGPU/WASM) и делать параллакс без сервера; веса 19–99 МБ — тяжело для
  первого экрана, годится для «по требованию» [S42] [не проверено: тема J].

## 6. Апскейл и интерполяция

### 6.1 Real-ESRGAN (ncnn-Vulkan — основной локальный путь)

- Код Real-ESRGAN — BSD-3-Clause (★36 880, последний push 06.08.2024); ncnn-сборка `xinntao/Real-ESRGAN-ncnn-vulkan` — MIT
  (★2 239, push 10.05.2024); «Portable… executable files for Intel/AMD/Nvidia GPU… No CUDA or PyTorch environment is
  needed» [S30]. Репозитория `nihui/realesrgan-ncnn-vulkan` не существует (404) — брать релиз xinntao [проверено].
- Модели сборки 20220424: `realesrgan-x4plus` (фото, 33,4 МБ), `realesrnet-x4plus`, `realesrgan-x4plus-anime` (6B),
  `realesr-animevideov3` ×2/×3/×4 (1,2 МБ, для кадров видео) [S30]. **Дефолт**: README — «realesrgan-x4plus (default)», а
  `-h` бинарника — «default=realesr-animevideov3» → всегда `-n` [проверено].
- Ключи [S30]: `-s` 2/3/4, `-t` тайл (0 = авто; меньше — меньше памяти), `-j load:proc:save` («4:4:4» для множества
  маленьких, «2:2:2» для больших), `-g` GPU, `-x` TTA, `-f` jpg/png/webp. Python-версия: тайлы, альфа-канал, 16 бит,
  `--outscale` (досжатие LANCZOS4), GFPGAN для лиц.
- Измерено здесь (Iris Xe, Vulkan, 23.09.2026) [проверено]:

| Модель | Вход → выход | Время процесса | GPU-буферы (= ОЗУ) | Замечание |
|---|---|---|---|---|
| x4plus | 128² → 512² | 2,94 с (холодный), 1,95 с (тёплый кэш шейдеров Mesa) | 708 МБ | |
| x4plus | 256² → 1024² | 6,05 с | 1 276 МБ | ≈5 с на 1 Мп выхода |
| x4plus, 4 файла одной командой | 4 × 128² | 5,62 с (1,4 с/файл) | 708 МБ | загрузка модели ≈1 с амортизируется |
| x4plus на llvmpipe (`-g 1`, CPU-Vulkan) | 128² → 512² | 13,5 с (97 с CPU) | — | в 5–7 раз медленнее iGPU |
| animevideov3 ×4 | 128² → 512² | 0,29 с | 82 МБ | |
| animevideov3 ×2 | 640×360 → 1280×720 | 0,59 с | 116 МБ | кадр видео < 1 с |

- Качество на синтетике: x4plus сглаживает край и шрифт, но **теряет часть тонких регулярных линий** (≈22 → ≈17 на
  штриховке 6 px), animevideov3 ближе к оригиналу → для `IMG-TEXTURE` апскейл проверять глазами или брать SeedVR2
  «seamless» [проверено: 1 образец; SeedVR2 — не проверено].

```bash
# realesrgan-ncnn-vulkan 20220424 · Iris Xe (Mesa ANV) · [проверено]
cd 99-raw/tools/bin/realesrgan-ncnn-vulkan
./realesrgan-ncnn-vulkan -i in.png -o out.png -n realesrgan-x4plus -s 4 -m models -g 0        # фото/иллюстрация
mkdir -p frames_x2   # каталог вывода создать заранее (пакетный запуск P/10 шёл в существующий каталог)
./realesrgan-ncnn-vulkan -i frames/ -o frames_x2/ -n realesr-animevideov3 -s 2 -m models -g 0  # кадры видео пакетом
```

### 6.2 SUPIR и SeedVR2 (генеративная реставрация)

- **SUPIR** (★5 667) — «SUPIR Software License Agreement» (SupPixel Pty Ltd, право Нового Южного Уэльса): код и веса —
  «for non-commercial purposes only»; к коммерции прямо отнесены «Using the software to process images that are intended
  for sale», «Deploying the software on a server to provide a service to users for a fee», «commercial consulting or
  contracting services, such as image… enhancement… for clients» [S33]. Требует SDXL + LLaVA 13B: «12G for Diffusion, 16G
  for LLaVA» в режиме экономии [S33]. → Для сайтов заказчика **нет** (и локально не потянуть).
- **SeedVR2** (ByteDance-Seed, arXiv 2506.05301) — «One-Step Video Restoration via Diffusion Adversarial Post-Training»;
  веса 3B и 7B — **Apache 2.0** (HF и LICENSE репозитория) [S34]. Обёртка ComfyUI `numz/ComfyUI-SeedVR2_VideoUpscaler`
  (Apache 2.0, ★2 868): картинки и видео, «RGBA Support: Native alpha channel processing with edge-guided upscaling for clean
  transparency», GGUF 4/8 бит «for inference on low-VRAM systems», BlockSwap [S34]. Хостинг: fal `fal-ai/seedvr/upscale/image`
  $0,001/Мп (0,084 ₽), `…/image/seamless` $0,0025/Мп (для бесшовных текстур), `…/video` [S43]. Локально на Iris Xe — нет
  (PyTorch CUDA/MPS) [не проверено].
- Альтернативы для апскейла RGBA без обучения: Real-ESRGAN Python-версия (альфа отдельно), Topaz Transparent (закрытый, у P
  в файле 04) [S30].

### 6.3 RIFE и FILM (интерполяция кадров)

- **RIFE**: Practical-RIFE (MIT, ★1 022, push 27.08.2026) — «Currently, it is recommended to choose 4.25 by default for most
  scenes»; «4.24+ is quite suitable for post-processing of some diffusion model generated videos»; для 4K — `--scale=0.5`
  или `--UHD` [S31]. **rife-ncnn-vulkan** (nihui, MIT, ★1 102, последний push 02.01.2024; релиз 20221029, архив 431 МБ) —
  модели rife, rife-HD/UHD/anime, v2…v4, **v4.6 — последняя** в сборке [проверено: список архива]; ключи: `-0/-1` пара или
  `-i каталог`, `-n` число кадров (по умолчанию N×2), `-s` доля времени, `-m` путь к модели (по умолчанию `rife-v2.3`!),
  `-g -1` — CPU, `-x/-z` TTA, `-u` UHD [S31].
- Измерено здесь (rife-v4.6) [проверено]:

| Режим | Устройство | Время | Память |
|---|---|---|---|
| 2 кадра 256×144 | Iris Xe | 0,83 с (с инициализацией) | 0,29 ГБ + 110 МБ GPU |
| 2 кадра 256×144 | CPU ncnn (`-g -1`) | 0,16 с | 0,17 ГБ |
| 2 кадра 1280×720 | Iris Xe / CPU | 0,63 с / 0,98 с | 0,31 ГБ + 280 МБ / 0,77 ГБ |
| каталог 8 кадров 720p → 16 | Iris Xe | 1,38 с (≈0,17 с на кадр) | 0,39 ГБ + 468 МБ |
| каталог 8 кадров 720p → 16 | CPU ncnn | 6,02 с (≈0,75 с на кадр) | 0,98 ГБ |

  Выходы GPU и CPU почти совпадают (средняя разница 0,008 из 255). На кадре 256×144 с полосатым фоном — ореол-искажение
  вокруг движущегося объекта; на 720p того же сюжета не видно [проверено: 1 синтетический сюжет].
- **FILM** (Google Research, Apache 2.0, ★3 153): «Frame Interpolation for Large Motion», TensorFlow 2, «a unified
  single-network approach that doesn't use additional pre-trained networks, like optical flow or depth» — рассчитана на
  большие сдвиги между кадрами [мнение вендора; сравнения с RIFE не делал]; локальной ncnn-сборки не искал [S32].
- Хостинг: fal `fal-ai/rife/video` и `fal-ai/film/video` — $0,0013 за секунду GPU (≈0,11 ₽) [S43]; Topaz interpolate
  (закрытый) — у P в файле 04.

```bash
# rife-ncnn-vulkan 20221029, модель v4.6 · [проверено]
cd 99-raw/tools/bin/rife-ncnn-vulkan
mkdir -p frames_2x   # без существующего каталога: «invalid outputpath extension type» [проверено]
./rife-ncnn-vulkan -i frames/ -o frames_2x/ -m "$PWD/rife-v4.6" -g 0      # удвоение fps каталога кадров (%08d.png)
./rife-ncnn-vulkan -0 a.png -1 b.png -o mid.png -m "$PWD/rife-v4.6" -g -1  # одна пара маленьких кадров — CPU быстрее
```

## 7. Вектор: генеративный SVG, Lottie, трассировка

### 7.1 StarVector (image→SVG, text→SVG)

- 1B и 8B (HF `starvector/starvector-{1b,8b}-im2svg`, Apache 2.0; GitHub ★4 598) — VLM на базе StarCoder, пишет SVG-код с
  примитивами (эллипсы, полигоны, текст), а не только `path` [S35]. SVG-Bench (DinoScore, вендор): 8B — иконки 0,984, эмодзи
  0,981, шрифты 0,982, диаграммы 0,959 [мнение вендора, методика в статье].
- Ограничение вендора: «StarVector models will not work for natural images or illustrations… They excel in vectorizing icons,
  logotypes, technical diagrams, graphs, and charts» [S35]. `max_length=4000` токенов в примере; vLLM-бэкенд «substantially
  faster». fal `fal-ai/star-vector` — **deprecated** (каталог 23.09.2026) [S43].
- Лицензия: Apache 2.0 на веса; база StarCoder распространяется под BigCode OpenRAIL-M — наследование ограничений не
  проверено [открытый вопрос, к L].

### 7.2 OmniSVG (text/image→SVG) и OmniLottie (→Lottie)

- **OmniSVG** (NeurIPS 2025; GitHub ★2 627): «from simple icons to intricate anime characters»; OmniSVG1.1_8B (17,2 ГБ,
  02.12.2025), 1.1_4B (7,69 ГБ), OmniSVG-3B (8,49 ГБ); GPU: 26 ГБ (8B) / 17 ГБ (4B, 3B); время — 20,1 с на 1024 SVG-токена
  (8B), 18,1 с (4B) [S36]. Лицензия: модель Apache 2.0, датасет MMSVG — CC BY-NC-SA 4.0 [S36]. **Нюанс**: по `cardData.base_model`
  OmniSVG-3B и 1.1_4B — дообучение `Qwen/Qwen2.5-VL-3B-Instruct`, у которого `qwen-research` («FOR NON-COMMERCIAL PURPOSES
  ONLY»), а 1.1_8B — `Qwen2.5-VL-7B-Instruct` (Apache 2.0) → для коммерции безопаснее только 8B [S10][S36] [спорно].
- **OmniLottie** (OpenVGLab, веса 02.03.2026, 4B, 8,46 ГБ; LICENSE Apache 2.0, датасет MMLottie-2M — CC BY-NC-SA 4.0):
  text-, text+image-, video-to-Lottie; 15,2 ГБ GPU, 33,4 с на 1024 Lottie-токена; токенизатор Qwen2.5-VL-3B — то же
  наследование, что у OmniSVG-3B [S37] [спорно]. Хостинг: fal `fal-ai/omnilottie/image-to-lottie` — $0,10 за картинку
  (8,41 ₽), обязательны `prompt` и `image_url`, `max_tokens` 256–8192 (по умолчанию 4096), `temperature` 0,9, `top_p` 0,25,
  `top_k` 5 [S43]. Для `VEC-ANIM` — кандидат на один дешёвый тест в живой фазе.
- Прочие хостинговые векторизаторы fal (закрытые): `fal-ai/image2svg` $0,005, `fal-ai/vecglypher/image-to-svg` $0,005,
  `fal-ai/recraft/vectorize` — сравнение — у агента G [S43].

### 7.3 Выбор для задач сайта

| Задача | Открытый путь | Коммерция | Локально здесь |
|---|---|---|---|
| `VEC-ICON-LINE`, `VEC-ICON-FILLED` | LLM пишет SVG по сетке (агент G); StarVector 8B для перевода растровой иконки в SVG | да (Apache; база — вопрос) | нет (7,5B, GPU) |
| `VEC-ILLUSTR` | OmniSVG1.1_8B (text→SVG) | да (8B) | нет (26 ГБ GPU) |
| `VEC-TRACE` плоская графика | vtracer `--preset poster --max-colors N` | да (MIT) | да (CLI, pip, npm) [не проверено здесь] |
| `VEC-TRACE` ч/б (лого, скан) | potrace / vtracer `--preset bw` | potrace GPL (запуск как отдельной программы — обычно допустим), vtracer MIT | да |
| `VEC-ANIM` | OmniLottie 4B | спорно (база) | нет (15 ГБ GPU); fal $0,10 |

### 7.4 vtracer и potrace (детерминированная трассировка)

- **vtracer** (visioncortex, MIT; ★7 099, push 20.09.2026; PyPI `vtracer` 0.6.15 от 23.03.2026; в master — 1.0.0-alpha.4 от
  29.08.2026) [S38]: цветная трассировка со стеком слоёв без дыр («much more compact» чем Image Trace Illustrator [мнение
  вендора]); 1.0: пресеты `bw`/`poster`/`photo`, `--clustering color-cluster|bw|watershed`, `--hierarchical stacked|cutout`,
  `-m pixel|polygon|spline`, `-p` точность цвета (бит), `--palette '#112233,#445566'` / `--palette-file` (ближайший цвет в
  **OKLab**), `--max-colors N`, адаптивный порог для сканов; `vtracer-bench` — слепая оценка трассировщиков (PSNR + SSIM +
  «missing patch»). Привязка к палитре бренда на этапе трассировки — прямой инструмент для серии иллюстраций (граф №7).
- **potrace** 1.16 (17.09.2019): «free software… under the terms of the GNU General Public License… either version 2, or
  (at your option) any later version»; «Potrace Professional» — не-GPL версия для встраивания в закрытый софт (Icosasoft)
  [S39]. Только ч/б, «optimal-polygon search» (медленнее vtracer на больших картинках [мнение vtracer]).

```bash
# vtracer 1.0 CLI (cargo install vtracer-cli) · синтаксис по README 1.0.0-alpha.4 [S38] · [не проверено здесь]
vtracer input.png output.svg --preset poster --max-colors 6
vtracer input.png output.svg --preset poster --palette '#0B1F3A,#F2C14E,#F7F7F2'   # снап к палитре бренда (OKLab)
vtracer scan.jpg  output.svg --clustering bw --adaptive                              # скан/фото линейного рисунка
```

## 8. ComfyUI, stable-diffusion.cpp и оркестрация

### 8.1 ComfyUI

- GPL-3.0; ★134 544, push 23.09.2026; стабильный релиз примерно раз в 2 недели [S40]. Поддерживает из этого файла: FLUX.2,
  Flux.2 Klein, Qwen Image и Qwen Image Edit, Z-Image, Hunyuan Image 2.1, Ideogram 4, Wan 2.1/2.2, LTX-Video 2/2.3,
  HunyuanVideo 1.5, MiniMax H3, SeedVR2, SUPIR, Depth Anything 3, SAM 3 и 3.1, BiRefNet [S40].
- «Runs fully offline: core does not download anything unless you request it. Use `--disable-api-nodes` to disable the
  optional paid Comfy API nodes»; Partner nodes — платный доступ к закрытым моделям (Nano Banana, Seedance…); Comfy Cloud —
  «official paid cloud version» [S40].
- Железо: NVIDIA, AMD (ROCm), Intel через `torch.xpu` («Intel Arc GPU users») — на этой машине нет драйвера Level Zero/OpenCL
  Intel (ставится только с sudo), остаётся CPU; → ComfyUI здесь не даёт ускорения [проверено: `ldconfig` в P/10; сам ComfyUI не
  запускался].
- **ComfyUI не лицензирует модели**: GPL-3.0 относится к коду ComfyUI; веса, загруженные в него, остаются под своими
  лицензиями (FLUX NCL, Tencent, S-Lab…) [документация]. Workflow хранится в JSON — удобный формат «паспорта генерации»
  для открытых моделей на хостинге с ComfyUI [практика].

### 8.2 stable-diffusion.cpp (ggml) — единственный кандидат на локальную генерацию через Vulkan

- MIT; ★7 114, push 22.09.2026; C/C++ на ggml; бэкенды CPU (AVX/AVX2/AVX512), CUDA, **Vulkan**, Metal, OpenCL, SYCL;
  форматы ckpt/safetensors/GGUF; режимы `img_gen`, `vid_gen`, `upscale` (ESRGAN), `convert`; модели: FLUX.2-dev/klein,
  Z-Image, Qwen Image / Edit / **2.1 (day-0, 20.09.2026)**, Ideogram4, Wan2.1/2.2, LTX-2.3/2.5, HunyuanVideo 1.5, MiniMax-H3
  [S41]. Ключи памяти: `--backend diffusion=vulkan0`, `--offload-to-cpu`, `--max-vram`, `--mmap`, `--fa`, VAE tiling [S41].
- **Установка проверена**: готовая сборка `sd-master-c92d73c-bin-Linux-Ubuntu-24.04-x86_64-vulkan.zip` (22.09.2026) запускается
  без sudo, `--list-devices` → «Intel(R) Iris(R) Xe Graphics (RPL-P)… uma: 1 | fp16: 1 | bf16: 0 | … | matrix cores: none»
  [проверено: P/10 (д)]. Генерация не запускалась (веса 3–20+ ГБ); отсутствие матричных ядер и общая с CPU память
  15 ГБ → ожидать минуты на картинку [не проверено; оценка].

### 8.3 Оркестрация на практике (для N и I)

- Открытые модели в системе заказчика — через **хостинг** (fal/Replicate/KIE, §11) с тем же JSON-паспортом, что и закрытые;
  локально — только детерминированная постобработка (§10) [вывод по §1–§8].
- Обёртка вызова локальных инструментов: подпроцесс с таймаутом, `free -g` перед запуском, один тяжёлый шаг за раз,
  явная модель (`-n`, `-m`, `new_session(имя)`), запись версии бинарника/модели и sha256 в паспорт ассета [практика; P/10].

## 9. Лицензии: сводная таблица «модель → лицензия → коммерция → оговорка»

«Коммерция» = можно ли **самому запускать веса** и ставить результат на коммерческий сайт клиента. «Условно» — можно при
выполнении условий из оговорки. Сверено по текстам LICENSE и карточкам 23.09.2026; теги HF — только подсказка.

| Модель / инструмент | Лицензия | Коммерция | Оговорка | Источник |
|---|---|---|---|---|
| FLUX.2 [dev] | FLUX [dev] Non-Commercial v2.0 (= FLUX NCL v2.1) | **нет** | выход «for any purpose», но запуск модели «for revenue-generating activity… impact on end users» запрещён; фильтры или ручная проверка обязательны; коммерция — хостинг или BFL Professional | [S2][S3][S5] |
| FLUX.2 [klein] 4B, Base 4B | Apache 2.0 | **да** | фильтры «encourage» | [S1][S3] |
| FLUX.2 [klein] 9B, 9B KV, Base 9B | FLUX NCL v2.1 | **нет** | как [dev]; BFL Builder/Platform | [S1][S5] |
| FLUX.2 autoencoder, small-decoder | Apache 2.0 | **да** | — | [S1][S47] |
| Qwen-Image, -Edit, -Edit-2509, -Edit-2511, -Layered, -2512 | Apache 2.0 | **да** | — | [S7] |
| Qwen-Image-2.1 (+ PE-T2I/PE-I2I) | Qwen Research License (20.09.2026) | **нет** | «research or evaluation purposes only»; коммерческая лицензия — model-business@notice.qwencloud.com | [S9] |
| Z-Image, Z-Image-Turbo | Apache 2.0 | **да** | кириллица не заявлена (только en/zh) | [S11] |
| HunyuanImage 2.1, 3.0, 3.0-Instruct(-Distil) | Tencent Hunyuan Community | **условно** | не действует в ЕС/UK/KR; выход нельзя «display… outside the Territory»; пометка «machine generated» в публичном контексте; раскрыть поставщика; > 100 млн MAU — отдельно | [S12][S13] |
| Ideogram 4 (fp8, nf4) | Ideogram Non-Commercial Model Agreement | **нет** | выход нельзя «to include in, or to advertise or promote, revenue-generating products» | [S15] |
| LTX-2, LTX-2.3 | LTX-2 Community (05.01.2026) | **условно** | выручка группы < $10 млн/год; пометка «machine generated»; не конкурировать с Lightricks | [S16] |
| LTX-2.5 | LTX-2.x Community (11.08.2026) | **условно** | то же + соблюдать EU AI Act / CA AI Transparency Act, не удалять водяные знаки, метаданные, «latent disclosure» | [S16][S17] |
| Wan 2.1, 2.2 (все варианты) | Apache 2.0 | **да** | «We claim no rights over the your generated contents» | [S18] |
| HunyuanVideo 1.5 | Tencent Hunyuan Community | **условно** | как HunyuanImage | [S14] |
| MiniMax H3 (H3-Base) | MiniMax H3 Community | **нет** (для сайтов) | исключены ЕС, UK, KR и **США**; «MiniMax H3» в UI; > $20 млн — разрешение | [S19] |
| BiRefNet (все варианты, ONNX) | MIT | **да** | среди обучающих данных — DIS5K (некоммерческий датасет) → остаточный риск, к L | [S20][S23] |
| BEN2 (Base) | MIT | **да** | полная модель — коммерческий API вендора | [S21] |
| RMBG-1.4 | bria-rmbg-1.4 (CC, non-commercial) | **нет** | коммерция — договор с Bria | [S22] |
| RMBG-2.0 | CC BY-NC 4.0 | **нет** | **модель по умолчанию в rembg 2.0.85**; API Bria — с лицензией | [S22][S23] |
| rembg (код) | MIT | **да** | лицензии весов — отдельно («independent of rembg's MIT license») | [S23] |
| U²-Net / u2netp | Apache 2.0 (репозиторий) | **да** | — | [S23] |
| IS-Net `isnet-general-use` | код Apache 2.0; веса без явной лицензии | **условно** | обучена на DIS5K — «commercial use of this dataset is prohibited even after… processing» | [S23] |
| SAM 2 / 2.1 | Apache 2.0 | **да** | — | [S24] |
| SAM 3 / 3.1 | SAM License (19.11.2025) | **да, условно** | Trade Controls (санкции США/ООН/ЕС/UK), без reverse engineering; веса — по ручному одобрению HF | [S24] |
| MatAnyone, MatAnyone 2 | S-Lab License 1.0 | **нет** | коммерция — по запросу авторам | [S25] |
| RobustVideoMatting | GPL-3.0 | **условно** | копилефт на код; запуск отдельной программой — вопрос к L | [S26] |
| Depth Anything V2 Small (+ ONNX) | Apache 2.0 | **да** | — | [S27][S42] |
| Depth Anything V2 Base / Large / Giant | CC BY-NC 4.0 | **нет** | — | [S27] |
| DA3-Small, DA3-Base, DA3Mono-Large, DA3Metric-Large | Apache 2.0 | **да** | — | [S28] |
| DA3-Large(-1.1), DA3-Giant(-1.1), DA3Nested | CC BY-NC 4.0 | **нет** | тег HF у DA3-LARGE-1.1 — `apache-2.0`, README — CC BY-NC → строгое | [S28][S47] |
| Depth Pro | Apple AMLR (HF) / Apple sample-code (GitHub) | **нет** | «exclusively for Research Purposes»; GitHub README противоречит | [S29] |
| Real-ESRGAN (код, модели), realesrgan-ncnn-vulkan | BSD-3-Clause; MIT | **да** | — | [S30] |
| RIFE (Practical-RIFE, ECCV2022-RIFE), rife-ncnn-vulkan | MIT | **да** | — | [S31] |
| FILM | Apache 2.0 | **да** | — | [S32] |
| SUPIR | SUPIR Software License | **нет** | обработка «images that are intended for sale» — коммерция | [S33] |
| SeedVR / SeedVR2 (3B, 7B) | Apache 2.0 | **да** | — | [S34] |
| StarVector 1B / 8B | Apache 2.0 | **да, условно** | база StarCoder (BigCode OpenRAIL-M) — не проверено | [S35] |
| OmniSVG1.1_8B | Apache 2.0 | **да** | датасет MMSVG — CC BY-NC-SA (на веса не переносится [спорно]) | [S36] |
| OmniSVG-3B, OmniSVG1.1_4B | Apache 2.0 (заявлено) | **спорно** | база Qwen2.5-VL-3B-Instruct — `qwen-research` | [S10][S36] |
| OmniLottie 4B | Apache 2.0 (заявлено) | **спорно** | токенизатор/база Qwen2.5-VL-3B; датасет MMLottie-2M — CC BY-NC-SA | [S37] |
| vtracer | MIT | **да** | — | [S38] |
| potrace | GPL-2.0-or-later | **да** как отдельная программа | встраивание в закрытый код — Potrace Professional | [S39] |
| ComfyUI | GPL-3.0 | **да** (инструмент) | лицензии моделей не меняет | [S40] |
| stable-diffusion.cpp | MIT | **да** | — | [S41] |

Итого: из 43 строк «да» — 21 (включая potrace как отдельную программу и ComfyUI как инструмент), «условно» / «да, условно» /
«спорно» — 10, «нет» — 12 (одна строка может охватывать несколько весов).
Требования **пометить контент как машинный** (Tencent AUP п. 12, LTX Attachment A п. 5, MiniMax AUP п. 12, FLUX NCL §2(e)
«to the extent required under applicable law», Ideogram §4) пересекаются с EU AI Act ст. 50 — это решение агента L;
до него: **на странице с таким ассетом — видимая пометка «Изображение создано ИИ»** [документация + практика].

## 10. Что реально запускается здесь локально (результаты P/10)

Машина: i9-13900H (14 ядер / 20 потоков), 15,7 ГБ ОЗУ (свободно 4,2–6,2 ГБ во время опыта), Intel Iris Xe (RPL-P),
Vulkan 1.4.348, Mesa 26.1.2 (ANV), fp16/int8 — да, bf16 — нет, матричных ядер нет; второй Vulkan-«GPU» — llvmpipe (CPU).
Intel OpenCL-ICD и Level Zero **не установлены** → OpenVINO-GPU, PyTorch-XPU и ORT на iGPU без sudo недоступны; GNU `time`
отсутствует → замер своим `timev.py` (VmHWM + drm fdinfo) [проверено].

### 10.1 Итоговая таблица (23.09.2026, по одному прогону на шаг)

| Задача (код) | Инструмент · модель | Устройство | Вход | Время | Пик памяти | Вердикт |
|---|---|---|---|---|---|---|
| `IMG-UPSCALE` | realesrgan-ncnn-vulkan · x4plus | Iris Xe | 256² → 1024² | 6,05 с | 0,9 ГБ RSS + 1,28 ГБ GPU | **работает** (≈5 с/Мп выхода) |
| `IMG-UPSCALE` | то же | Iris Xe | 128² → 512² | 1,95–2,94 с | 0,9 ГБ + 0,71 ГБ | работает |
| `VID-UPSCALE` | realesrgan-ncnn-vulkan · animevideov3 ×2 | Iris Xe | 640×360 → 720p | 0,59 с | 0,12 ГБ + 0,12 ГБ | **работает** (кадр < 1 с) |
| `VID-UPSCALE` (интерполяция) | rife-ncnn-vulkan · v4.6 | Iris Xe | 8 кадров 720p → 16 | 1,38 с (0,17 с/кадр) | 0,39 ГБ + 0,47 ГБ | **работает** |
| то же | rife-ncnn-vulkan · v4.6 | CPU ncnn | 8 кадров 720p → 16 | 6,02 с (0,75 с/кадр) | 0,98 ГБ | работает, в 4,4 раза медленнее |
| `IMG-CUTOUT` | rembg · u2netp (4,6 МБ) | CPU ORT 1.30 | 256² (модель 320²) | инференс 0,10 с; процесс 1,1 с | 0,72 ГБ | **работает**, края грубее |
| `IMG-CUTOUT` | rembg · isnet-general-use (179 МБ) | CPU ORT | 256² (модель 1024²) | 0,55 с; процесс 2,4 с | 1,48 ГБ | **работает** (лицензия весов — условно) |
| `IMG-CUTOUT` | rembg · birefnet-general-lite (224 МБ) | CPU ORT | 256² (модель 1024²) | 10,1 с (повтор 25 с — своп) | **6,52 ГБ** | на грани: только по одной, ≥ 8 ГБ свободно |
| 2.5D-глубина (граф №5) | Depth Anything V2 Small ONNX fp32 (99 МБ) | CPU ORT | 518² | 0,24–0,26 с; процесс 0,9 с | 0,41 ГБ | **работает**, карта правдоподобна |
| Генерация (любая) | stable-diffusion.cpp Vulkan (22.09.2026) | Iris Xe | — | запуск + `--list-devices` | — | **только установка**; генерация [не проверено] |

Почему время rembg почти не зависит от размера картинки: модель всегда работает на фиксированном входе (u2netp 320²,
isnet и BiRefNet 1024² — `sessions/*.py`, `normalize(…, (1024, 1024))`), остальное — ресайз маски [проверено: код].

### 10.2 Рецепты для H и I (готово к копированию)

```bash
# без sudo · [проверено: P/10 и recipe_check/ — 8 кадров 640×360 → 16 → AV1 webm 48 fps] · бинарники в 99-raw/tools/bin/, venv — 99-raw/tools/venv-p10
free -g                                                     # перед каждым тяжёлым шагом; iGPU берёт ту же ОЗУ
BIN=99-raw/tools/bin
# апскейл картинки ×4 (фото/иллюстрация); модель задавать явно
(cd $BIN/realesrgan-ncnn-vulkan && ./realesrgan-ncnn-vulkan -i /abs/in.png -o /abs/out.png -n realesrgan-x4plus -s 4 -m models -g 0)
# интерполяция: каталог кадров %08d.png → вдвое больше кадров; КАТАЛОГ ВЫВОДА СОЗДАТЬ ЗАРАНЕЕ,
# иначе «invalid outputpath extension type» [проверено]
mkdir -p /abs/frames2x
(cd $BIN/rife-ncnn-vulkan && ./rife-ncnn-vulkan -i /abs/frames -o /abs/frames2x -m "$PWD/rife-v4.6" -g 0)
# сборка обратно в видео (ffmpeg 7.1.5, SVT-AV1 2.3.0): исходные 24 fps → 48 fps
ffmpeg -framerate 48 -i /abs/frames2x/%08d.png -c:v libsvtav1 -crf 35 -pix_fmt yuv420p out_48fps.webm
```

```python
# depth · onnxruntime 1.30 CPU · Depth Anything V2 Small (Apache-2.0) · [проверено 1:1: P/10 recipe_check/snippet_depth.py]
import numpy as np, onnxruntime as ort
from PIL import Image
sess = ort.InferenceSession("model.onnx", providers=["CPUExecutionProvider"])  # onnx-community/depth-anything-v2-small, onnx/model.onnx
img = Image.open("in.png").convert("RGB").resize((518, 518), Image.BICUBIC)      # сторона кратна 14; вход динамический
x = (np.asarray(img, np.float32) / 255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
d = sess.run(None, {"pixel_values": x.transpose(2, 0, 1)[None].astype(np.float32)})[0].squeeze()
Image.fromarray(((d - d.min()) / (d.max() - d.min()) * 255).astype(np.uint8)).save("depth.png")  # светлее = ближе (диспаритет)
```

### 10.3 Правила ресурсов и что не делать локально

- Один тяжёлый шаг за раз; BiRefNet ONNX на CPU — только при `free -g` ≥ 8 ГБ «available», иначе своп (повтор 25 с вместо 10 с)
  [проверено].
- Для одиночных маленьких кадров RIFE `-g -1` (CPU) быстрее: нет инициализации Vulkan (0,16 с против 0,83 с) [проверено].
- Первый запуск ncnn-модели после загрузки системы медленнее (компиляция шейдеров, кэш Mesa на диске): x4plus 2,94 → 1,95 с
  [проверено].
- Не запускать локально: генераторы (FLUX.2, Qwen, Z-Image, Wan, LTX, Hunyuan) через PyTorch — нет CUDA; SUPIR, SeedVR2,
  MatAnyone, SAM 3 — PyTorch/GPU [документация]. Кандидаты на отдельные опыты волны 2: SAM 2.1 tiny (38,9M) на CPU, RVM
  MobileNetV3 ONNX на CPU (лицензия GPL — к L), BiRefNet_512x512 ONNX для экономии памяти, Z-Image-Turbo GGUF в
  stable-diffusion.cpp на Vulkan [не проверено].

## 11. Хостинг открытых моделей и цены (23.09.2026)

### 11.1 Где взять хостинг-версию

Цены: fal — per-model `llms.txt` (кэш `99-raw/cache/fal-2026-09-23/models/`) и каталог `api.fal.ai/v1/models`
(`99-raw/experiments/P/03-fal-catalog`); Replicate — billingConfig страниц моделей (`…/P/05-price-compare/`); KIE — прайс-API
(`…/P/02-kie-vs-polza/`); polza — снимок каталога. ₽ — по курсу ЦБ 84,0657. «—» = не нашлось.

| Модель | fal | Replicate | KIE | polza |
|---|---|---|---|---|
| FLUX.2 [dev] | `fal-ai/flux-2` $0,012/Мп (1,01 ₽) | — | — | — |
| FLUX.2 [klein] 4B | `fal-ai/flux-2/klein/4b` $0,005/Мп (0,42 ₽) | `black-forest-labs/flux-2-klein-4b` $0,001/Мп выход + $0,001/Мп вход (0,084 ₽) | — | — |
| FLUX.2 [klein] 9B | `fal-ai/flux-2/klein/9b` $0,006/Мп (0,50 ₽) | — | — | — |
| Qwen-Image (20B) | `fal-ai/qwen-image` $0,02/Мп (1,68 ₽) | `qwen/qwen-image` $0,025 (2,10 ₽) | — | `qwen/image` 2,25–3 ₽ |
| Qwen-Image-2512 | `fal-ai/qwen-image-2512` $0,02/Мп, с округлением до целого Мп (1,68 ₽) | — | — | — |
| Qwen-Image-Edit-2509 / -2511 | `fal-ai/qwen-image-edit-2509`, `-2511` $0,03/Мп (2,52 ₽) | — | — | — |
| Qwen-Image-Layered | `fal-ai/qwen-image-layered` $0,05 за картинку (4,20 ₽) | — | — | — |
| Qwen-Image-2.1 | — | — | $0,02 (1K) / $0,04 (2K) (1,68 / 3,36 ₽) | `qwen/image-2.1` 3 / 6 ₽ |
| Z-Image-Turbo | `fal-ai/z-image/turbo` $0,005/Мп (0,42 ₽); `…/turbo/tiling` $0,02/Мп (1,68 ₽) | `prunaai/z-image-turbo` $0,005/Мп при 1 Мп, $0,01/Мп при 2 Мп | $0,004 (0,34 ₽) | `tongyi-mai/z-image` 1,4 ₽ |
| HunyuanImage 3.0 | `fal-ai/hunyuan-image/v3/text-to-image` $0,1/Мп (8,41 ₽) | `tencent/hunyuan-image-3` $0,08 (6,73 ₽) | — | — |
| Ideogram 4 | `ideogram/v4` $0,0075 / 0,015 / 0,025 за Мп (TURBO / BALANCED / QUALITY; 2048² — $0,03 / 0,06 / 0,10); `/fast`, `/instant`, `/tiling` | — | — | — |
| LTX-2.3 | `fal-ai/ltx-2.3/text-to-video` $0,08/с 1080p (6,73 ₽/с), $0,16 1440p, $0,32 2160p; `…/image-to-video/fast` $0,06/с | — | — | — |
| LTX-2.5 | `lightricks/ltx-2.5/text-to-video/fast` $0,09/с 720p (7,57 ₽/с) … $0,30 4K; `…/pro` $0,12 720p, $0,17 1080p | — | — | — |
| Wan 2.2 | 5B t2v $0,15 за ролик (12,61 ₽); A14B t2v $0,04–0,08 за «видео-секунду» (16 кадров) | — | 5 с: 480p $0,20 (16,81 ₽), 580p $0,30, 720p $0,40 (33,63 ₽) | — |
| HunyuanVideo 1.5 | `fal-ai/hunyuan-video-v1.5/image-to-video` $0,075/с (6,30 ₽/с) | — | — | — |
| BiRefNet | `fal-ai/birefnet/v2`, `…/v2/video` — «$0 per compute seconds» (ставка GPU не видна) | `men1scus/birefnet` (по GPU-времени) | — | — |
| BEN2 | `fal-ai/ben/v2/image` $0,025/Мп (2,10 ₽) | — | — | — |
| RMBG-2.0 (с лицензией Bria) | `fal-ai/bria/background/remove` $0,018 (1,51 ₽) | `bria/remove-background` $0,018 | — | — |
| SAM 3 | `fal-ai/sam-3/image` $0,005 за запрос (0,42 ₽) | — | — | — |
| Depth Anything (видео) | `fal-ai/depth-anything-video` $0,04/с (3,36 ₽/с) | — | — | — |
| Real-ESRGAN | `fal-ai/esrgan` $0,00111/с GPU (0,093 ₽/с) | — | — | — |
| SeedVR2 | `fal-ai/seedvr/upscale/image` $0,001/Мп (0,084 ₽); `…/seamless` $0,0025/Мп; `…/video` | — | — | — |
| RIFE / FILM | `fal-ai/rife/video`, `fal-ai/film/video` $0,0013/с GPU (0,109 ₽/с) | — | — | — |
| RVM | — | `arielreplicate/robust_video_matting` (по GPU-времени) | — | — |
| OmniLottie | `fal-ai/omnilottie/image-to-lottie` $0,10 (8,41 ₽) | — | — | — |

- **Хостинг против polza** (по возможности одинаковая модель): Z-Image Turbo fal 0,42 ₽/Мп против polza `tongyi-mai/z-image`
  1,4 ₽ (×3,3; вариант Turbo/база у polza не указан); Qwen-Image Replicate 2,10 ₽ против polza `qwen/image` 2,25–3 ₽ (×1,07–1,43;
  что `qwen/image` = Qwen-Image 20B — предположение C1 по параметрам); Qwen-Image-2.1 KIE 1,68 / 3,36 ₽ против polza 3 / 6 ₽
  (×1,78; polza ходит к KIE — P-notes §2) [документация; доступ из России, оплата и ключи — в файлах 03 и 06].
- **Бейдж лицензии у fal** — поле `license_type` каталога: `commercial` у `fal-ai/flux-2` ([dev]!), `fal-ai/flux-2/klein/9b`,
  `ideogram/v4`, всех `ltx-2.x`, Wan, Qwen; `research` — у старого `fal-ai/ltx-video` (LTX-Video 0.9); без значения — у
  `fal-ai/sam2/*`, `fal-ai/amt-interpolation`, `fal-ai/image-preprocessors/depth-anything/v2` [S43]. Это условия fal на выход,
  а не лицензия весов; при самостоятельном запуске тех же весов действует их LICENSE [документация; условия договоров fal с
  вендорами не публичны — не проверено].
- Не нашлось на хостингах (23.09.2026): MatAnyone/MatAnyone 2, SUPIR, Qwen-Image-2.1 на fal, HunyuanVideo 1.5 t2v на fal
  (только i2v); `fal-ai/star-vector` — deprecated [S43].

### 11.2 Что проверить в живой фазе (минимально, по открытым моделям)

| № | Код задачи | Гипотеза | Минимальный тест | Модель · где | Цена | Критерий | Ценность |
|---|---|---|---|---|---|---|---|
| 1 | `IMG-CUTOUT` | Нативная прозрачность Qwen-Image-2.1 даёт край не хуже локального isnet/u2netp на том же сюжете | 2 продукта: `background: transparent` + те же с `opaque` → локально rembg isnet и u2netp | polza `qwen/image-2.1` (1K) | 2 × 2 × 3 = 12 ₽ | нет ореола на тёмном и светлом фоне; альфа-край ≤ 2 px; решение L по лицензии 2.1 | 3 |
| 2 | `IMG-DRAFT` | polza `tongyi-mai/z-image` = Turbo (8 шагов), текст — только латиница | 4 картинки: 2 с латиницей, 2 с кириллицей | polza `tongyi-mai/z-image` | 4 × 1,4 = 5,6 ₽ | латиница по OCR ≥ 90 %; кириллица — ожидаем провал | 2 |
| 3 | `IMG-UPSCALE` | Real-ESRGAN x4plus локально (0 ₽) сопоставим с Topaz ×2 на ИИ-картинке | 1 картинка 1K из любого теста → x4plus локально и `topaz/image-upscale` ×2 | локально + polza `topaz/image-upscale` | 7,5 ₽ | слепой выбор заказчика; нет «съеденного» мелкого узора | 2 |
| 4 | `VID-UPSCALE` | RIFE v4.6 локально удваивает fps ИИ-петли без заметных артефактов | 1 ролик 5 с из видео-тестов → 24→48 fps на Iris Xe | локально rife-ncnn-vulkan | 0 ₽ | нет ореолов на краях объектов при просмотре 1:1; время ≤ 60 с | 2 |
| 5 | 2.5D-глубина (граф №5) | DA-V2 Small даёт карту, пригодную для параллакса hero | 2 hero-картинки из тестов → глубина → прототип параллакса (J) | локально ONNX | 0 ₽ | нет «прилипания» фона к объекту при сдвиге 10–20 px | 2 |
| 6 | `VEC-TRACE` | vtracer с `--palette` бренда даёт чистый SVG из плоской ИИ-иллюстрации | 2 плоские иллюстрации из тестов C1 → vtracer 1.0 | локально (MIT) | 0 ₽ | ≤ 8 цветов, ≤ 150 КБ после svgo, без «крошки» < 4 px | 2 |

(Тесты на fal — Qwen-Image-Layered $0,05, Z-Image tiling $0,02/Мп, OmniLottie $0,10, BiRefNet v2 — только если по итогам
файла 06 заказчик заведёт ключ fal.)

## Частые ошибки

1. **«Открытые веса — значит, можно в коммерцию».** Некоммерческие веса в этом файле: FLUX.2 [dev] и все 9B-klein,
   Qwen-Image-2.1, Ideogram 4, RMBG-1.4/2.0, MatAnyone 1/2, SUPIR, Depth Anything V2 Base/Large/Giant, DA3 Large/Giant/Nested,
   Depth Pro; условные — Tencent Hunyuan, LTX, MiniMax H3 → §9.
2. **Перенос лицензии по имени семейства**: «Qwen-Image — Apache, значит и 2.1» (2.1 — research); «Depth Anything V2 —
   Apache» (только Small); «FLUX.2 klein — Apache» (только 4B); «SAM 3 — Apache, как SAM 2» (SAM License, gated) → §9.
3. **Вера тегу HF**: у DA3-LARGE-1.1 тег `apache-2.0`, а README — CC BY-NC 4.0; у MatAnyone тег пустой, а LICENSE — S-Lab
   non-commercial; у Depth Pro README GitHub и лицензия HF противоречат → решать по тексту, брать строгое → §5, §9.
4. **«RMBG-2.0 внутри rembg, значит MIT»**: rembg — MIT, веса — CC BY-NC; и это **модель по умолчанию** rembg 2.0.85; вызов
   `remove(img)` без сессии тянет 1 ГБ некоммерческих весов → §3.2.
5. **«RMBG-1.4 — свободная старая версия»**: тоже «for non-commercial use» → §3.1.
6. **«Depth Anything V2 Large — лучшая, беру её»**: CC BY-NC 4.0; для коммерции — V2 Small или DA3Mono-Large → §5.
7. **«Tencent/Hunyuan — открытая лицензия как Apache»**: исключены ЕС, UK, Южная Корея, запрет показа выхода вне
   Территории, обязательная пометка машинной генерации → §1.5.
8. **«MiniMax H3 открыт — можно для сайта в США/ЕС»**: США тоже в исключённых территориях, плюс надпись «MiniMax H3» в UI → §2.5.
9. **«У FLUX.2 [dev] выход можно в коммерцию — значит, можно генерировать для клиента»**: запуск модели «for
   revenue-generating activity» не является Non-Commercial Purpose; фильтры или ручная проверка обязательны → §1.2 [спорно].
10. **«fal пишет commercial — значит, веса коммерческие»**: это условия fal на выход; self-host тех же весов — по их LICENSE → §11.
11. **«Wan 2.5 / 2.6 / 3.0 — open source»** (SEO-статьи): весов нет, последний открытый — Wan 2.2 (+ Animate-2, Dancer) → §2.3.
12. **Ссылка на несуществующий `nihui/realesrgan-ncnn-vulkan`**: официальная ncnn-сборка — xinntao (Real-ESRGAN v0.2.5.0,
    Real-ESRGAN-ncnn-vulkan v0.2.0) → §6.1.
13. **realesrgan-ncnn-vulkan без `-n`**: бинарник 20220424 берёт `realesr-animevideov3`, а не x4plus из README → «мультяшный»
    апскейл фото → §6.1.
14. **rife-ncnn-vulkan без `-m` и без каталога вывода**: по умолчанию модель `rife-v2.3`; несуществующий `-o каталог` →
    «invalid outputpath extension type» → §6.3, §10.2.
15. **«BiRefNet-lite лёгкая — запущу пачкой на CPU»**: 10 с и 6,5 ГБ RSS на картинку через ONNX; на общей машине — своп → §10.
16. **rembg `withoutbg` как локальная модель**: это облачный API, картинка уходит на сторонний сервер → §3.2.
17. **OmniSVG-3B / 1.1-4B и OmniLottie как «Apache 2.0»**: основа — Qwen2.5-VL-3B с `qwen-research` → §7.2 [спорно].
18. **StarVector для иллюстраций или фото**: «will not work for natural images or illustrations» → §7.1.
19. **«ComfyUI под GPL — значит, модели в нём свободные» (или «GPL заражает выход»)**: лицензия ComfyUI касается его кода;
    веса и их выходы — по лицензиям моделей → §8.1.
20. **«Qwen-Image-Layered нарисует слои по тексту»**: веса обучены на разложение готовой картинки, «text-to-multi-RGBA
    generation is limited»; рекомендован `resolution` 640 → нужен апскейл слоёв → §1.3.
21. **«Z-Image напишет кириллицу»**: вендор заявляет только английский и китайский → §1.4.
22. **«LTX бесплатна до $10 млн — значит, без условий»**: пометка машинного контента обязательна, водяные знаки и
    метаданные удалять нельзя, выручка считается по группе компаний → §2.2.
23. **Параметры и VRAM «по памяти»**: klein 4B — 13 или 8 ГБ (вендор противоречит сам себе), HunyuanImage 3.0 — не 24 ГБ, а
    ≥ 3×80 ГБ; всегда ссылаться на карточку с датой → §1.1.

## Чек-лист

- [ ] Лицензия проверена по тексту LICENSE/карточки (не по тегу HF), дата снятия записана в паспорт ассета?
- [ ] Модель стоит в §9 со значением «да» — или все условия из оговорки выполнены и записаны?
- [ ] Для FLUX.2 [dev], klein 9B, Ideogram 4, Qwen-Image-2.1 выбран хостинг с коммерческими условиями или купленная лицензия,
      а не self-host?
- [ ] Аудитория сайта вне ЕС/UK/Южной Кореи (для Tencent Hunyuan) и вне ЕС/UK/Кореи/США (для MiniMax H3) — или модель не используется?
- [ ] Если лицензия модели требует пометки машинного контента (Tencent, LTX, MiniMax) — пометка на странице предусмотрена?
- [ ] В rembg модель задана явно, и это не `bria-rmbg` и не `withoutbg`?
- [ ] Перед тяжёлым локальным шагом выполнен `free -g`, и свободной памяти хватает (BiRefNet ONNX — ≥ 8 ГБ)?
- [ ] Для realesrgan-ncnn-vulkan задан `-n`, для rife-ncnn-vulkan — `-m` и заранее созданный каталог вывода?
- [ ] Апскейл текстуры/узора просмотрен глазами (мелкий регулярный узор не «съеден»)?
- [ ] Для глубины взята Apache-модель (V2 Small, DA3 Small/Base/Mono-Large/Metric-Large)?
- [ ] Для видео-матирования не выбраны MatAnyone (S-Lab) и RVM (GPL) без решения L?
- [ ] Версия бинарника/модели и sha256 записаны (см. `99-raw/experiments/P/10-local-runtime-check/sha256_*.txt`)?
- [ ] Цена хостинга сверена с polza (одна и та же открытая модель у fal/KIE/Replicate дешевле в 1,1–3,3 раза)?
- [ ] Для SVG: StarVector — только иконки/логотипы/диаграммы; для коммерции OmniSVG — только 1.1_8B?
- [ ] Бейдж `commercial` у fal воспринят как условия fal, а не как лицензия весов?

## Открытые вопросы и противоречия

1. **FLUX NCL §2(d) против §4(a)**: «You may use Output for any purpose (including for commercial purposes)» против запрета
   использовать модель «(or any data produced by the FLUX Model)… for any commercial or production purposes» и определения
   Non-Commercial Purpose — можно ли продавать клиенту ассеты, сгенерированные локально [dev]? → L [спорно].
2. **FLUX NCL §4(f)(v)** «will not disguise your location through IP proxying» и LTX §7, SAM «Trade Controls»: работа из
   России через VPN и статус пользователей из России → L.
3. **Территориальные лицензии (Tencent, MiniMax)**: запрет «display… Output… outside the Territory» при сайте, открытом всему
   миру — нарушение ли это при аудитории ЕС? → L.
4. **polza/KIE `qwen/image-2.1`**: есть ли у провайдера коммерческая лицензия Alibaba на веса с Qwen Research License
   (выход 20.09.2026, в polza — с 21.09.2026)? Вопрос к polza и L.
5. **FLUX.2 [klein] 4B VRAM**: «~13GB» (HF, docs.bfl.ml) против «~8GB» (README GitHub) — противоречие вендора.
6. **Real-ESRGAN, модель по умолчанию**: README «realesrgan-x4plus (default)» против `-h` бинарника 20220424
   «default=realesr-animevideov3» (проверено запуском).
7. **DA3-LARGE-1.1**: README — CC BY-NC 4.0, тег HF — `apache-2.0` (P/09).
8. **Depth Pro**: README GitHub «The model weights are released under the LICENSE terms» (разрешительная Apple) против HF
   `apple-amlr` «exclusively for Research Purposes».
9. **Наследование лицензий базовых моделей**: OmniSVG-3B/1.1-4B и OmniLottie (Qwen2.5-VL-3B, `qwen-research`), StarVector
   (StarCoder, BigCode OpenRAIL-M) — действует ли ограничение базы на дообученные веса под Apache 2.0? → L.
10. **Датасетные ограничения**: IS-Net (веса без явной лицензии) и BiRefNet (MIT) обучены в том числе на DIS5K, чьи Terms of
    Use запрещают коммерцию «even after copying, editing, processing» — переходит ли это на веса? → L.
11. **fal BiRefNet v2**: в описании `model` «General Use (Light)» сопоставлен полной BiRefNet, а «General Use (Heavy)» —
    BiRefNet_lite (названия, похоже, перепутаны) [документация fal, 23.09.2026]; ставка «$0 per compute seconds» не раскрыта без ключа.
12. **Цены не опубликованы**: BFL — лицензии Builder/Platform/Professional (только «Contact Sales»/dashboard); fal BiRefNet v2 и
    rembg — «$0 per compute seconds» (ставка GPU без ключа не видна); Replicate — `men1scus/birefnet`, RVM (по GPU-времени).
13. **Генерация на Iris Xe**: stable-diffusion.cpp с Vulkan видит устройство, но скорость (Z-Image-Turbo GGUF, 512², 8 шагов) не
    измерена — отдельный опыт при ≥ 10 ГБ свободной памяти.
14. **Память BiRefNet на CPU**: снизят ли fp16-ONNX (114,5 МБ), `BiRefNet_512x512` или `OMP_NUM_THREADS` пик 6,5 ГБ — не проверено.
15. **Коммерческое высококачественное матирование видео** без S-Lab/GPL: остаются покадровый BiRefNet/BEN2 (временная
    стабильность не проверена) или закрытые Bria VRMBG 3.0 / veed / pixelcut на fal — сравнение — у агента I.
16. **SAM 3 из России**: одобрение gated-доступа «manual» на HF не проверено; SAM 2.1 (Apache, без gate) — запасной путь.
17. **Статус Wan 2.5+**: весов нет на 23.09.2026; при выходе — перепроверить лицензию (Wan 2.1/2.2 — Apache 2.0).

## Источники

Даты снятия — 23.09.2026, если не указано иное; звёзды и последний push GitHub — `99-raw/experiments/P/09-open-weights-meta/gh_meta_2026-09-23.json`
(через ungh.cc); кэш текстов — `99-raw/cache/` (имена `raw.githubusercontent.com_*`, `huggingface.co_*`).

- [S1] Black Forest Labs. README `github.com/black-forest-labs/flux2` (★2 702, push 2026-03-12) — таблица моделей и лицензий, VRAM klein, [dev] 32B; первоисточник, высокая надёжность.
- [S2] Black Forest Labs. «FLUX Non-Commercial License v2.1» и «FLUX [dev] Non-Commercial License v2.0» (`model_licenses/` в том же репо) — прочитаны целиком, сверены diff; первоисточник.
- [S3] Black Forest Labs. Карточки HF `FLUX.2-dev`, `FLUX.2-klein-4B`, `FLUX.2-klein-9B` (gated — через HTML-страницу, `hf_card_html.py`) — VRAM, фильтры, политика; первоисточник.
- [S4] Black Forest Labs. docs.bfl.ml «FLUX.2 Overview» (кэш C1 `docs.bfl.ml_flux_2_flux2_overview_ddeeb151.md`) — цены API klein, открытые веса Base; первоисточник.
- [S5] Black Forest Labs. bfl.ai/licensing «Open Weights Licensing» — тарифы Builder/Platform/Professional/Enterprise без цен; первоисточник.
- [S6] BFL/Hugging Face. `flux2/docs/flux2_dev_hf.md` — 4-бит, удалённый текст-энкодер, ≈18–20 ГБ; первоисточник.
- [S7] Qwen (Alibaba). Карточки HF `Qwen-Image`, `Qwen-Image-Edit-2509`, `-2511`, `-Layered`, `-2512` + LICENSE (Apache 2.0) — прочитаны целиком; первоисточник.
- [S8] Qwen. README `github.com/QwenLM/Qwen-Image` (★8 363, push 2026-02-10) и `QwenLM/Qwen-Image-Layered` (★2 112, push 2025-12-31) — хронология, сообщество, экспорт слоёв; первоисточник.
- [S9] Qwen. Карточка HF `Qwen/Qwen-Image-2.1` + «Qwen RESEARCH LICENSE AGREEMENT» (20.09.2026); GitHub `QwenLM/Qwen-Image-2.1` ★1 289, push 2026-09-20; первоисточник.
- [S10] Qwen. LICENSE `Qwen/Qwen2.5-VL-3B-Instruct` (qwen-research, «FOR NON-COMMERCIAL PURPOSES ONLY») + cardData `base_model` OmniSVG (HF API); первоисточник.
- [S11] Tongyi-MAI. README `github.com/Tongyi-MAI/Z-Image` (★12 044, push 2026-02-09) и карточки HF Z-Image, Z-Image-Turbo; первоисточник.
- [S12] Tencent Hunyuan. README и LICENSE `HunyuanImage-2.1` (★674, push 2025-10-14) — «Tencent Hunyuan Community License» прочитана целиком; первоисточник.
- [S13] Tencent Hunyuan. README и LICENSE `HunyuanImage-3.0` (★3 271, push 2026-06-23) — VRAM, Instruct/Distil; первоисточник.
- [S14] Tencent Hunyuan. README и LICENSE `HunyuanVideo-1.5` (★4 562, push 2026-04-10); первоисточник.
- [S15] Ideogram. `github.com/ideogram-oss/ideogram-4` README, `docs/inference.md`, `model_licenses/LICENSE-IDEOGRAM-4-NON-COMMERCIAL` (★2 849, push 2026-06-30) — лицензия прочитана целиком; первоисточник.
- [S16] Lightricks. `github.com/Lightricks/LTX-2` README, LICENSE, LICENSE-2 (05.01.2026), LICENSE-2_x (11.08.2026) (★9 508, push 2026-08-26); первоисточник.
- [S17] Lightricks. Карточка HF `Lightricks/LTX-2.5` (gated, HTML); первоисточник.
- [S18] Wan (Alibaba). README и LICENSE.txt `github.com/Wan-Video/Wan2.2` (★17 606, push 2026-09-21), README `Wan-Video/Wan2.1` (★17 028, push 2026-03-05); первоисточник.
- [S19] MiniMax. README `github.com/MiniMax-AI/MiniMax-H3` (★9 120, push 2026-08-15) и LICENSE HF `MiniMaxAI/MiniMax-H3`; первоисточник.
- [S20] Zheng Peng. README и LICENSE (MIT) `github.com/ZhengPeng7/BiRefNet` (★4 217, push 2026-09-02), карточки HF; первоисточник.
- [S21] Prama LLC. Карточка HF `PramaLLC/BEN2` (MIT; GitHub ★287); первоисточник.
- [S22] BRIA AI. Карточки HF `briaai/RMBG-1.4` и `briaai/RMBG-2.0` — прочитаны целиком; первоисточник.
- [S23] D. Gatis. README и LICENSE `github.com/danielgatis/rembg` (★24 847, push 2026-09-20) + исходный код rembg 2.0.85 (venv-p10); LICENSE U²-Net (Apache 2.0), LICENSE.md и README DIS, «DIS5K Terms of Use» (PDF); первоисточник.
- [S24] Meta. README и LICENSE `facebookresearch/sam2` (★19 908, push 2026-05-30), README и «SAM License» (19.11.2025) `facebookresearch/sam3` (★11 761, push 2026-09-18); первоисточник.
- [S25] P. Yang и др. README и LICENSE `pq-yang/MatAnyone` (★1 625, push 2026-03-04), README и LICENSE.txt `pq-yang/MatAnyone2` — S-Lab License 1.0; первоисточник.
- [S26] P. Lin. README и LICENSE (GPL-3.0) `PeterL1n/RobustVideoMatting` (★9 532, push 2024-04-02); первоисточник.
- [S27] Depth Anything. README и LICENSE `DepthAnything/Depth-Anything-V2` (★8 857, push 2026-03-24); первоисточник.
- [S28] ByteDance Seed. README `ByteDance-Seed/Depth-Anything-3` (★6 387, push 2026-07-27) — таблица лицензий; первоисточник.
- [S29] Apple. README и LICENSE `apple/ml-depth-pro` (★5 725, push 2026-09-11); LICENSE HF `apple/DepthPro` (AMLR) — прочитан целиком; первоисточник, противоречат друг другу.
- [S30] X. Wang. README и LICENSE (BSD-3) `xinntao/Real-ESRGAN` (★36 880, push 2024-08-06); README и LICENSE (MIT) `xinntao/Real-ESRGAN-ncnn-vulkan` (★2 239, push 2024-05-10); первоисточник.
- [S31] nihui. `nihui/rife-ncnn-vulkan` README и LICENSE из релиза 20221029 (★1 102, push 2024-01-02); hzwer, README и LICENSE `hzwer/Practical-RIFE` (★1 022, push 2026-08-27), LICENSE `hzwer/ECCV2022-RIFE` (★5 586); первоисточник.
- [S32] Google Research. README и LICENSE (Apache 2.0) `google-research/frame-interpolation` (★3 153, push 2024-08-10); первоисточник.
- [S33] SupPixel. README и «SUPIR Software License Agreement» `Fanghua-Yu/SUPIR` (★5 667, push 2025-05-12) — лицензия прочитана целиком; первоисточник.
- [S34] ByteDance Seed. Карточка HF `SeedVR2-3B` и LICENSE `ByteDance-Seed/SeedVR` (★1 367, push 2026-01-27); README `numz/ComfyUI-SeedVR2_VideoUpscaler` (★2 868, push 2025-12-24); первоисточник + обёртка сообщества.
- [S35] J. Rodriguez и др. Карточка HF `starvector/starvector-8b-im2svg`, README и LICENSE `joanrod/star-vector` (★4 598, push 2025-11-07); первоисточник.
- [S36] OmniSVG. README и LICENSE `github.com/OmniSVG/OmniSVG` (★2 627, push 2026-03-01), карточка HF `OmniSVG1.1_8B`; первоисточник.
- [S37] OpenVGLab. README и LICENSE `github.com/OpenVGLab/OmniLottie`, карточка HF `OmniLottie/OmniLottie`; fal `omnilottie/image-to-lottie` llms.txt; первоисточник.
- [S38] visioncortex. README, LICENSE (MIT), CHANGELOG `visioncortex/vtracer` (★7 099, push 2026-09-20); PyPI `vtracer` 0.6.15 (23.03.2026); первоисточник.
- [S39] P. Selinger. potrace.sourceforge.net (разделы License и Dual licensing через WebFetch; выпуск 1.16 от 17.09.2019); первоисточник.
- [S40] Comfy Org. README и LICENSE (GPL-3.0) `comfyanonymous/ComfyUI` (★134 544, push 2026-09-23); первоисточник.
- [S41] leejet. README и LICENSE (MIT) `leejet/stable-diffusion.cpp` (★7 114, push 2026-09-22); релиз `master-900-c92d73c` (22.09.2026) — установлен и запущен в P/10 (д); первоисточник.
- [S42] ONNX Community. Карточки HF `onnx-community/depth-anything-v2-small` и `BiRefNet_lite-ONNX`; размеры файлов — HF tree API; первоисточник.
- [S43] fal.ai. Per-model `llms.txt` (кэш `99-raw/cache/fal-2026-09-23/models/`) и каталог `api.fal.ai/v1/models` (`99-raw/experiments/P/03-fal-catalog/fal_models_2026-09-23.json`, 1 239 эндпоинтов) — цены и `license_type`; документация провайдера.
- [S44] Replicate. billingConfig страниц моделей (`99-raw/experiments/P/05-price-compare/replicate_prices_2026-09-23.txt`); документация провайдера.
- [S45] KIE.ai. Прайс-API (`99-raw/experiments/P/02-kie-vs-polza/kie_pricing_2026-09-23.json`, 489 позиций); документация провайдера.
- [S46] polza.ai. Снимок каталога `GET /api/v1/models` (`99-raw/notes/orchestrator/polza-media-models-2026-09-23.md`); документация провайдера.
- [S47] Hugging Face Hub API и ungh.cc — лицензии-теги, gated, параметры, загрузки, даты, списки моделей 21 организации (`99-raw/experiments/P/09-open-weights-meta/`); метаданные, средняя надёжность (теги расходятся с README).
- Вторичные (не первоисточник): заметки C1 (`99-raw/notes/wave1/C1-notes.md` §8–§11: Qwen API, Ideogram 4 JSON, HunyuanImage 3.0) и C2 (`C2-notes.md` §6, §13, §17: Model Studio Wan, открытые видео-веса, исследование Loopy).
