# Какая модель картинок для какой задачи сайта: коды IMG-* → кандидаты, доказательства, разрывы, тесты фазы 5

Волна 1 · агент C1 · 2026-09-23 · прочитано целиком или существенно ≈ 60 источников, опытов 6 (`99-raw/experiments/C1/`) ·
снимок каталога polza 2026-09-23 · цены — ₽ polza (провайдер mie, если не сказано иное) на 23.09.2026. Карточки моделей —
`02-model-cards.md`, `models/*.yaml`; арены и бенчмарки — `01-landscape-and-benchmarks.md`. Промты ниже — тестовые
заготовки фазы 5, не проверены генерацией; метод промтинга — у D (`../05-prompting/`) [поправка X 24.09.2026: было «04-prompting» — такой папки нет].

## Выжимка для агента

1. Финальный фото-hero и продукт в polza — `gpt-image-2-5-flare` или `openai/gpt-image-2.5-sunburst` (4/7/11 ₽): №1–2 AA
   Live-Action, Human Anatomy, Retail; второй голос — Nano Banana 2 (4,8 ₽) и Seedream 5.0 Pro (5 ₽, LMArena Photoreal #9).
   → §2, §3 [исследование] [поправка фазы 5, 25.09.2026: E-08 (6 моделей, голос заказчика вслепую, 1 чел.) — «хорошо» Sunburst, Flare, NB2; NB Pro
   «слишком ровно», Seedream 5.0 Pro «сразу минус», FLUX.2 Pro «так себе»; id Flare с 25.09 — `openai/gpt-image-2.5-flare`;
   модели новых каналов (CM-09, 1 образец): Qwen Image 3 — настоящие 2K за 3,31 ₽, Krea 2 — самый естественный →
   `../99-raw/phase5/runs/2.5-stand/E-08_blind_sheet.jpg`]
2. Люди и руки на hero — только GPT Image 2.5: Human Anatomy AA 1225/1194 против 1135 у лучшего из остальных в polza (NB2).
   → §2 [исследование]
3. Продукт «как есть» (этикетка, логотип) ни одна модель не гарантирует: генерировать сцену, а настоящий вырезанный товар
   вставлять композитингом; модели — для сцены и света. → §3 [документация] [поправка фазы 5, 25.09.2026: E-10 (банка с этикеткой, 4 модели) —
   этикетка во фронте сохранена у всех 4 (OCR дословно — Sunburst, NB2, Seedream 5 Pro), сбоку дословно — только Sunburst,
   масштаб у Qwen завышен → правило в силе → `../99-raw/phase5/runs/2.5-stand/E-10_sheet.jpg`]
4. Иллюстрации: AA и LMArena расходятся во втором месте (AA Animation — NB2 #7, LMArena Cartoon/Art — Seedream 5.0 Pro
   #9–10); первый выбор — Flare (AA Animation #1). SVG — не здесь, а в VEC-* (G, Recraft). → §4 [исследование]
5. Серия с одним персонажем/продуктом: эталон → референс в каждой генерации + повтор определяющих деталей словами
   (рецепт OpenAI); seed в polza есть только у Qwen 2.1 и Seedream 4.0. Специализированные бенчмарки (ViStoryBench,
   OmniRef-Bench) ставят №1 Nano Banana Pro, №2 в OmniRef — Seedream 4.5; GPT 2.x в них нет, а в арене Identity №1 — GPT 2.5
   → тест 5: Flare против NB Pro против Seedream 4.5 (71,5 ₽). → §5 [исследование] [поправка фазы 5, 25.09.2026: E-12 (2 сюжета по эталону NB2) —
   стиль держит только Flare; NB2 — зелёные столбики, NB Pro — синие столбики и коралловая заливка, Seedream 4.5 — палитра
   распалась; F-01 — «3 референса + роль + блок» ΔE OKLab 0,031–0,035 → `../99-raw/phase5/runs/2.3-series/E-12_blind_sheet.jpg`]
6. Прозрачный фон в polza — только `qwen/image-2.1` (`background: transparent`, png/webp, 3 ₽); остальное — генерация на
   ровном фоне + удаление фона (H) или прямые API (OpenAI, Ideogram, Recraft). → §7 [документация] [поправка фазы 5, 25.09.2026: T2 — альфа Qwen 2.1
   настоящая (64 % прозрачных, лицензия research); вне polza — RouterAI GPT 2.5 `transparent` 1,45 ₽: мех годен, стекло — облако
   фона (H-03); Riverflow `transparent` — пусто]
7. Бесшовной текстуры «из коробки» нет ни у одной модели с API: параметра tile нет (есть только `--tile` у Midjourney без
   API) → сдвиг на 50 % + заделка шва маской (Qwen 2.1) или постобработка H. → §9 [документация]
8. Абстрактный фон под бренд-цвета: hex как механизм документирован у FLUX.2 (промт/JSON) — у остальных пожелание;
   проверять ΔE2000 (тест 8). Чистые градиенты и формы — кодом (CSS/SVG), не моделью. → §8 [документация]
9. Лента 8:1 / 4:1 в polza — только Nano Banana 2 Lite (2,9 ₽, 1K); 21:9 — GPT 2.5, Nano Banana, Seedream 4/4.5/5 Lite. → §8
   [документация]
10. Текст латиницей на картинке: GPT Image 2 (`openai/gpt-5.4-image-2`, AA TR #1) или 2.5; NB2 — с запретом лишнего текста.
    Любой текст — только после OCR-проверки дословности; интерфейсный текст, цены, кнопки — HTML/CSS поверх картинки. → §10
    [исследование]
11. Кириллица: кандидаты — GPT Image 2/2.5, Nano Banana 2, Seedream 5.0 Pro, Qwen 2.1. Независимо генерацию русского мерит
    только LingT2I на моделях 2025 года (русский 0.29 против 0.67 у английского; «Nano Banana» 0.47); публичные тесты — N ≤ 4
    на модель (дословно 4/4 у GPT Image 2, 2/4 у NB2) → тест 1 фазы 5 (88,6 ₽) до выбора модели по умолчанию. → §17
    [исследование] [поправка фазы 5, 25.09.2026: E-02 — дословно 6 из 9 (Flare, GPT Image 2, NB2, NB Pro, Seedream 5.0 Pro, Seedream 4.5), Qwen 2.1
    и FLUX.2 Pro — ошибки в словах; модель по умолчанию не выбрана (лесенка E-03…E-04 не прогонялась) → HTML-слой, короткая надпись —
    после OCR и чтения; см. §17.5]
12. Правка по инструкции: Sunburst/Flare (AA правка #1/#2); NB2 — лучший не-OpenAI в polza для правки текста (AA #5);
    Seedream 5.0 Pro — для правки с сохранением персонажа (Identity #8). Точечная правка по маске за 3 ₽ — Qwen 2.1. → §12
    [исследование] [поправка фазы 5, 25.09.2026: E-15 — перекраска: NB2 ближе всех к цвету (ΔE00 3,9); удаление: Seedream 5.0 Pro — PASS (утечка
    0,01), Qwen 2.1 + маска — «призрак», Sunburst сдвигает кадр → `../99-raw/phase5/runs/4-edits/E-15-check/`]
13. Пиксельную неизменность вне области правки даёт только композитинг — ни маска, ни промт её не гарантируют (OpenAI:
    «entirely prompt-based… may not follow its exact shape»). → §12 [документация]
14. Аутпейнт в polza — через правку с новым `aspect_ratio` (GPT 2.5 — AA Composition & Framing #1); специализированный
    FLUX Outpainting (холст + смещение, до 4 МП) — только прямой API BFL. → §13 [документация] [поправка фазы 5, 25.09.2026: H-08 — у NB2 и Sunburst
    центр перерисован (резкость 0,56 / 0,14 < 0,85) → композит исходника обязателен]
15. Мокап с настоящим скриншотом — композитингом (Blender/CSS-перспектива); модель рисует устройство и сцену, скриншот
    перерисует. → §14 [документация]
16. Апскейл в polza — только `topaz/image-upscale` (×2 7,5 ₽), модель Topaz внутри не указана; дешевле перегенерировать в
    4K (Seedream 4.0 — 3 ₽, 4.5 — 5 ₽), если сюжет позволяет. → §15 [документация] [поправка фазы 5, 25.09.2026: «4K» Seedream 4.0 через mie —
    2352×1008 при 21:9, не 4K; настоящий 4K — Sunburst 3840×2160 за 11 ₽ (E-01)]
17. Черновики: `tongyi-mai/z-image` 1,4 ₽ (≤ 1000 символов, без референсов) или `google/gemini-3.1-flash-lite-image` 2,9 ₽
    (AA #13 — лучше Z-Image на 150 Elo). Переносимость черновика на дорогую модель не измерена → тест 9. → §16 [исследование]
18. Черновик и финал на одной модели переносятся лучше всего: в прямом API OpenAI `low` стоит ≈ $0.006 за 1024² при том же
    понимании промта, что и `high` [документация; перенос — не проверено]. → §16
19. Seedream в прямом API ставит видимый «AI-generated»; до серий на Seedream — тест 2 (3 ₽). → §18 [документация]
20. Бюджет фазы 5 по этому файлу — 16 тестов ≈ 327 ₽; обязательные (ценность 3) — тесты 1–7 ≈ 200 ₽. → §18

## 1. Сводная таблица маршрутизации (23.09.2026)

| Код | Первый выбор в polza | Второй | Дешёвый вариант | Вне polza (для P) | Надёжность | Тест |
|---|---|---|---|---|---|---|
| `IMG-HERO-PHOTO` | Flare / Sunburst (4–11 ₽) | NB2 (4,8–10,8 ₽); Seedream 5.0 Pro (5/10 ₽) | Seedream 4.0 (3 ₽, 4K) | MAI-Image-2.6, Grok 2.0 | высокая (2 арены) | 3 |
| `IMG-PRODUCT` | Sunburst (Retail #1) + композитинг товара | NB2; Seedream 5.0 Pro | Qwen 2.1 (3 ₽, 10 реф.) | MAI-2.6, Recraft V4.1 Utility | средняя (нет бенчмарка «по референсу») | 6 |
| `IMG-ILLUSTR` | Flare (Animation #1) | Sunburst; NB2 / Seedream 5.0 Pro | NB2 Lite (2,9 ₽) | Grok 2.0; Recraft (вектор) | средняя (арены расходятся во 2-м месте) | 5 |
| `IMG-SERIES` | Flare/Sunburst + эталон (16 реф.) или NB Pro (ViStoryBench и OmniRef-Bench №1) | Seedream 4.5 (OmniRef #2, 14 реф., 5 ₽); NB2 (14 реф.) | Qwen 2.1 / Seedream 4.0 (seed) | Recraft `style_id`; Seedream `sequential` (API) | средняя (бенчмарки без GPT 2.x) | 5 |
| `IMG-ICON3D` | Sunburst/Flare (LMArena 3D #1/#2) | NB2 (3D #7); Seedream 5.0 Pro (#8) | Qwen 2.1 с альфой (3 ₽) | Blender (настоящее 3D) | средняя | 4 |
| `IMG-CUTOUT` | Qwen 2.1 `background: transparent` | — (в polza нет второго) | то же, 3 ₽ | OpenAI прямой API, Ideogram TB v4, Recraft `removeBackground`, удаление фона (H) | средняя (документация, без замеров) | 4, 14 |
| `IMG-BG-ABSTRACT` | FLUX.2 [pro] (hex/JSON) или Flare | NB2 (шаблон negative space) | NB2 Lite 8:1 (2,9 ₽); Seedream 4.0 4K (3 ₽) | Ideogram (палитра), Recraft `controls.colors`; CSS/SVG | низкая (нет замеров цвета) | 8, 11 |
| `IMG-TEXTURE` | Seedream 4.0 (4K, seed) + заделка шва | Flare / NB2 «seamless tileable» | Seedream 4.0 (3 ₽) | Midjourney `--tile` (нет API) | низкая | 13 |
| `IMG-TEXT-LATIN` | GPT Image 2 (`openai/gpt-5.4-image-2`) / Flare | Sunburst; NB2 (+ запрет лишнего текста) | GPT 1.5 medium (3 ₽, до 01.12.2026) | Grok 2.0 (TR #3), Qwen-3.0-Pro, Ideogram (bbox) | высокая (2 арены) | 15 |
| `IMG-TEXT-CYR` | кандидаты: GPT 2/2.5, NB2, Seedream 5.0 Pro, Qwen 2.1 | — | Qwen 2.1 (3 ₽) | Grok 2.0; Qwen-3.0-Pro | **низкая** (N ≤ 4) | 1 |
| `IMG-EDIT` | Sunburst / Flare | NB2 (текст), Seedream 5.0 Pro (идентичность) | Qwen 2.1 + маска (3 ₽) | MAI-2.6 (правка #3); BFL Erase | высокая (2 арены) | 12 |
| `IMG-OUTPAINT` | Flare/Sunburst: правка + новый `aspect_ratio` | NB2 (21:9) | NB2 (4,8 ₽) | FLUX Outpainting; Grok Smart resize; Ideogram Reframe | средняя | 10 |
| `IMG-MOCKUP` | Flare (UI/UX #1) для сцены + композитинг скриншота | NB2; NB Pro (GEBench #1) | — | Qwen-3.0-Pro; Recraft Utility; Blender | средняя | 16 |
| `IMG-UPSCALE` | Topaz ×2 (7,5 ₽) | перегенерация в 4K; Seedream 5.0 Lite «Enhancement» (4 ₽) | Seedream 4.0 4K (3 ₽) | Topaz API с выбором модели; Recraft upscale | низкая (модель Topaz неизвестна) | 14 |
| `IMG-DRAFT` | NB2 Lite (2,9 ₽, AA #13) | Z-Image (1,4 ₽) | Z-Image | OpenAI `low` ($0.006) | средняя; перенос — не измерен | 9 |

## 2. IMG-HERO-PHOTO — фотореалистичный hero

| Кандидат | Доказательства | Метка | Цена polza |
|---|---|---|---|
| `openai/gpt-image-2.5-sunburst` | AA All #1 1197, Live-Action #1 1227, Human Anatomy #1 1225, Lighting #1, Material #1; LMArena Photoreal #1 1427, Portraits #1 1459 | [исследование] | 4 / 7 / 11 ₽ |
| `gpt-image-2-5-flare` | AA #2 1191, Live-Action #3 1192, Human Anatomy #2 1194; LMArena Photoreal #2 1417 | [исследование] | 4 / 7 / 11 ₽ |
| `google/gemini-3.1-flash-image-preview` (NB2) | AA #6 1122, Live-Action #6, Human Anatomy #6 1135; LMArena Photoreal #10 1266; 8,9 с | [исследование] | 4,8 / 7,2 / 10,8 ₽ |
| `seedream/5-pro-text-to-image` | LMArena Photoreal #9 1278, Portraits #8 1293; AA Lighting/Material #11; но AA All #15 | [исследование] | basic 5 / high 10 ₽ (1K/2K) |

- **Почему не другие:** Nano Banana Pro — AA Live-Action #7 (1114) за 13,5 ₽, без выигрыша у NB2; FLUX.2 — #31–34
  Live-Action; Seedream 4.x — #24–26; Z-Image — #66; Nano Banana 2 Lite — только 1K.
- **Чем нельзя заменить:** GPT 2.5 — для людей в кадре (отрыв ~90 Elo в Human Anatomy от лучшего не-OpenAI в polza).
- **Разрыв:** арены меряют 1:1 и 1024²; широкий hero 21:9 / 16:9 с пустой зоной под заголовок не измерен; у Seedream 5.0
  Pro в polza нет 21:9 и 4K.
- **Фаза 5:** тест 3 — один и тот же промт на Sunburst и Flare, 16:9, 2K (14 ₽): фактические пиксели, время, детализация.

```text
// gpt-image-2-5-flare и openai/gpt-image-2.5-sunburst · polza 2026-09-23 · aspect_ratio 16:9, image_resolution 2K · [не проверено]
Website hero photograph, 16:9. Three product designers (two women, one man, 30s) discussing sketches at a large
whiteboard in a bright loft studio, late-morning window light from the left, natural skin texture, relaxed hands with
correct anatomy. Composition: people in the right two thirds; the left third is a calm, softly out-of-focus brick wall
with empty space for a headline. Real photograph, 35mm lens, shallow depth of field, muted warm palette.
No text, no logos, no watermarks.
```

## 3. IMG-PRODUCT — продукт по референсу

| Кандидат | Доказательства | Метка | Цена |
|---|---|---|---|
| Sunburst | AA Retail #1 1200; LMArena Product #1 1415; AA правка Identity #1 1209; 16 референсов в polza | [исследование] | 4–11 ₽ |
| NB2 | AA Retail #7 1101; LMArena Product #8 1269; до 14 реф. (10 объектов + 4 персонажа) | [исследование] | 4,8–10,8 ₽ |
| Seedream 5.0 Pro | AA правка Retail #8, Identity #8 1146; 10 реф. (+0,3 ₽ за реф. со 2-го) | [исследование] | 5–12,7 ₽ |
| `qwen/image-2.1` | «сохранение личности людей и продуктов» (README), 10 реф., маска, seed | [мнение вендора] | 3 / 6 ₽ |

- **Почему не другие:** Nano Banana Pro — Retail #15 при 13,5 ₽; FLUX.2 [pro] — Retail #36; NB2 Lite — «not optimized for
  multiple reference inputs».
- **Чем нельзя заменить:** настоящий товар (этикетка, логотип, пропорции) — только композитинг вырезанного фото в
  сгенерированную сцену; модель — для сцены, света и тени. OpenAI: «If a region must remain pixel-identical, composite
  the approved edit into the original image» [S6].
- **Разрыв:** нет независимого бенчмарка «товар по референсу» (AA Reference-to-Image — «upcoming» [S38]).
- **Фаза 5:** тест 6 — фото реального товара (CC0 или заказчика) → сцена на 4 моделях (16,8 ₽); критерий: текст этикетки
  по OCR совпадает, форма после выравнивания IoU ≥ 0,9, лишнего текста нет.

```text
// openai/gpt-image-2.5-sunburst (images: [product.png]) · polza 2026-09-23 · aspect_ratio 3:2, 1K · [не проверено]
Image 1 is the product reference. Place exactly this product — same shape, proportions, colors, label text and logo —
on a light travertine countertop next to a window. Soft morning light from the right, gentle contact shadow, shallow
depth of field, a sprig of eucalyptus out of focus in the background. Do not redesign, relabel or add text to the
product. No extra text, no watermark.
```

## 4. IMG-ILLUSTR — 2D-иллюстрация (пустые состояния, онбординг, 404)

| Кандидат | Доказательства | Метка | Цена |
|---|---|---|---|
| Flare | AA Animation & Gaming #1 1211; LMArena Cartoon #2 1418, Art #2 1375 | [исследование] | 4–11 ₽ |
| Sunburst | LMArena Cartoon #1 1443, Art #1 1384; AA Animation #3 1177 | [исследование] | 4–11 ₽ |
| NB2 | AA Animation #7 1139 (LMArena Cartoon #12) | [исследование] | 4,8 ₽ |
| Seedream 5.0 Pro | LMArena Cartoon #10 1271, Art #9 1265 (AA Animation #17) | [исследование] | 5 ₽ |

- **Почему не другие:** FLUX.2 [pro] — AA Animation #40; Qwen 2.1 — LMArena Art #14 (предварительно); Z-Image — #79.
- **Чем нельзя заменить:** SVG/вектор — только Recraft Vector и векторизация (вне polza) → `VEC-*` у G.
- **Разрыв:** AA и LMArena расходятся во втором эшелоне (NB2 против Seedream 5.0 Pro); «плоская продуктовая иллюстрация
  с ограниченной палитрой» — отдельно не измерена.
- **Фаза 5:** отдельного теста нет (бюджет); при необходимости — 2 промта «плоская иллюстрация пустого состояния» на Flare,
  NB2 и Seedream 5.0 Pro (≈ 27,6 ₽, вне плана §18): слепое сравнение и проверка единства стиля пары картинок.

## 5. IMG-SERIES — серия в одном стиле / с тем же персонажем или продуктом

| Кандидат | Инструмент серии | Доказательства | Цена |
|---|---|---|---|
| Flare / Sunburst | до 16 референсов; рецепт OpenAI: эталон → вход + повтор определяющих деталей («Do not redesign the character») | AA Identity Preserving #1–2 [исследование]; «may occasionally struggle to maintain visual consistency» [документация] | 4 ₽ (1K) |
| Nano Banana Pro / NB2 | Pro: до 6 объектов + 5 персонажей + 3 стилевых; NB2: 10 объектов + 4 персонажа | Pro: **ViStoryBench №1** (29.08.2026), **OmniRef-Bench 8.50 — №1**; AA Identity #9 / #11 [исследование] | 13,5 / 4,8 ₽ |
| Seedream 4.5 / 4.0 | 14 / 10 реф.; seed у 4.0; `sequential_image_generation` — только прямой API | 4.5: OmniRef-Bench 8.13 — #2; 4.0: ViStoryBench #17; AA Identity #32 / #34 [исследование] | 5 / 3 ₽ |
| `qwen/image-2.1` | 10 реф. + seed + маска | LMArena правка #16 (предв.) | 3 ₽ |

- **Почему не другие:** NB2 Lite — «not optimized for multiple reference inputs»; Z-Image — без референсов; Grok (база) и
  Qwen-Image — 1 референс.
- **Чем нельзя заменить:** воспроизводимость (seed + эталон) в polza — только Qwen 2.1 и Seedream 4.0; стиль-код без
  обучения — Recraft V4 Styles `style_id` и Midjourney `--sref` (вне polza, у G/F).
- **Разрыв:** в специализированных бенчмарках серий (ViStoryBench, OmniRef-Bench) нет GPT Image 1.5/2/2.5 и Nano Banana 2;
  «стиль серии иллюстраций/иконок» (а не персонаж) не мерил никто (§7 файла 01). MultiBanana: у старых моделей качество
  падает с ростом числа референсов → один эталон + словесное описание деталей. Seedream `sequential_image_generation`
  (до 15 связанных картинок за запрос) polza не выставляет.
- **Фаза 5:** тест 5 — эталон (Flare, 4 ₽) + 3 сцены на Seedream 4.5, Flare, Nano Banana Pro (71,5 ₽); критерий: VLM-судья
  «тот же объект» ≥ 4 из 5 в каждой паре, ΔE доминантных цветов ≤ 5.

```text
// эталон: gpt-image-2-5-flare · polza 2026-09-23 · 1:1, 1K · [не проверено]
Product reference sheet: a matte ceramic coffee mug, teal glaze (#1F7A7A), cream interior, small embossed fox logo on
the front, thick rounded handle on the right. Centered on a seamless light-grey background, soft studio light,
front three-quarter view. No text, no other objects.

// сцены: bytedance/seedream-4.5 · gpt-image-2-5-flare · google/gemini-3-pro-image-preview (images: [reference.png]) · [не проверено]
Image 1 is the reference mug. Keep the same mug — teal glaze, cream interior, embossed fox logo, rounded handle — and
place it: (A) on a wooden kitchen table in morning light; (B) on a desk beside a laptop, cool daylight; (C) held in two
hands outdoors, autumn park. Do not change the mug's shape, color or logo. No text.
```

## 6. IMG-ICON3D — объёмные иконки и объекты (clay, glass, 3D)

| Кандидат | Доказательства | Метка | Цена |
|---|---|---|---|
| Sunburst / Flare | LMArena 3D #1 1414 / #2 1384; AA Material #1 1179 / #2 1169 | [исследование] | 4 ₽ (1K) |
| NB2 | LMArena 3D #7 1255; AA Material #6 1106 | [исследование] | 4,8 ₽ |
| Seedream 5.0 Pro | LMArena 3D #8 1253; AA Material #11 | [исследование] | 5 ₽ |
| `qwen/image-2.1` + `background: transparent` | иконка сразу с альфой | [документация] | 3 ₽ |

- **Почему не другие:** FLUX.2 [flex] — LMArena 3D #25; NB Pro — #12 при 13,5 ₽.
- **Чем нельзя заменить:** настоящая 3D-геометрия (поворот, одинаковый свет в наборе) — Blender/3D-генераторы
  (`../../3d/`); модели картинок дают только 2D-рендер.
- **Разрыв:** набор иконок в одном свете и ракурсе — задача серии (§5); прозрачность — §7.
- **Фаза 5:** тест 4 (один из двух объектов — стеклянная 3D-иконка с альфой).

## 7. IMG-CUTOUT — объект с прозрачным фоном

| Кандидат | Как | Где | Метка |
|---|---|---|---|
| `qwen/image-2.1` | `background: transparent` + `output_format` png или webp; несовместимо с `mask_url` | **polza, 3 ₽** | [документация] |
| GPT Image 2.5 / 2 | `background: "transparent"` + png/webp; у GPT Image 2 — preview с 20.08.2026 | только прямой API OpenAI | [документация] |
| Ideogram 4.0 | эндпоинт Transparent Background v4 | прямой API Ideogram | [документация] |
| Recraft | `removeBackground` (растр или SVG) | прямой API Recraft | [документация] |
| Seedream 5.0 Pro | `layer_decomposition` (база + до 16 PNG-слоёв с альфой); `background: transparent` — только из входа с альфой | прямой API BytePlus | [документация] |
| Любая модель + удаление фона | генерация на ровном контрастном фоне → матирование | конвейер H | [практика] |

- **Почему не другие:** остальные 22 модели polza альфу не отдают.
- **Чем нельзя заменить:** полупрозрачные материалы (стекло, дым, волосы) — нативная альфа против матирования; OpenAI:
  «A drawn checkerboard is not transparency», проверять альфу на волосах, стекле, тенях, краях [S6].
- **Разрыв:** в polza одна модель, и её веса — под некоммерческой Qwen Research License (права на результат через mie —
  вопрос к L); прозрачность Topaz-апскейла в polza не известна.
- **Фаза 5:** тест 4 — 2 объекта на Qwen 2.1 (6 ₽); критерий: альфа-канал есть, полупрозрачность стекла сохранена, ореол
  ≤ 2 px на тёмном и светлом фоне; тест 14 — апскейл этого PNG ×2 через Topaz (7,5 ₽).

```text
// qwen/image-2.1 · polza 2026-09-23 · background: transparent, output_format: png, 1:1, 1K, enhance_prompt: false · [не проверено]
This is an RGBA image with transparency. A frosted glass perfume bottle with pale amber liquid and a brushed-gold cap,
three-quarter view, soft studio reflections, subtle caustics inside the glass. The image has alpha channel and the
background is transparent.
```

## 8. IMG-BG-ABSTRACT — абстрактный фон, градиенты, свет, «атмосфера»

| Кандидат | Доказательства | Метка | Цена |
|---|---|---|---|
| `black-forest-labs/flux.2-pro` | hex со словом «color»/«hex» и привязкой к объекту; `color_palette` в JSON-промте; градиенты — начальный и конечный цвет | [документация] | 5 / 7 ₽ |
| Flare | 21:9, 27:16, 4K; AA Lighting #2 | [исследование] | 4–11 ₽ |
| NB2 / NB2 Lite | шаблон «Minimalist & negative space design… backgrounds for websites… where text will be overlaid»; Lite — 8:1, 4:1 | [документация] | 4,8 / 2,9 ₽ |
| `bytedance/seedream-4` | 4K за 3 ₽, 21:9, seed | [документация] | 3 ₽ |

- **Почему не другие:** Seedream 5.0 Pro и Qwen в polza без 21:9; Z-Image — 1K.
- **Чем нельзя заменить:** точные градиенты, сетки, геометрия и анимация фона — кодом (CSS-градиенты, SVG, шейдеры);
  модель — для света, материала, «атмосферы» (рабочая гипотеза базы).
- **Разрыв:** попадание в бренд-цвет не измерено ни одним бенчмарком; hex у GPT/NB/Seedream — пожелание. Явные палитры в
  API — только вне polza: Ideogram `color_palette` (до 16 hex), Recraft `controls.colors` (до 10 RGB с весами), Wan 2.7
  `color_palette` (3–10 hex с долями).
- **Фаза 5:** тест 8 — 2 сцены × FLUX.2 [pro], Flare, NB2 (27,6 ₽), ΔE2000 доминант ≤ 5 для ≥ 2 из 3 цветов; тест 11 —
  лента 8:1 на NB2 Lite (5,8 ₽).

```json
// black-forest-labs/flux.2-pro · polza 2026-09-23 · aspect_ratio 16:9, 1K · [не проверено]
{
  "scene": "abstract website hero background",
  "subjects": [{"description": "three soft flowing ribbons of light", "position": "right half, diagonal from lower right to upper center"}],
  "style": "minimal 3D render, smooth gradients, subtle film grain",
  "color_palette": ["#0B3D91", "#FF6B35", "#F7F7F2"],
  "lighting": "soft diffuse glow",
  "background": "the ribbons are color #0B3D91 fading to #FF6B35; the background is color #F7F7F2",
  "composition": "left 40% calm and empty for a headline",
  "mood": "calm, premium"
}
```

## 9. IMG-TEXTURE — текстура и бесшовный паттерн

| Кандидат | Как | Метка | Цена |
|---|---|---|---|
| `bytedance/seedream-4` | 4K + seed; промт «seamless tileable…»; шов — постобработкой | [документация] | 3 ₽ |
| Flare / NB2 | «seamless tileable, top-down, even lighting» | [не проверено] | 4 / 4,8 ₽ |
| `qwen/image-2.1` + `mask_url` | сдвиг картинки на 50 % → маска на крест шва → заделка правкой | [не проверено] | 3 ₽ за проход |

- **Почему не другие:** параметра tile нет ни у одной модели polza и ни у одного изученного API; `--tile` есть только у
  Midjourney V8.x без официального API [S34].
- **Чем нельзя заменить:** бесшовность проверяется только сдвигом и метрикой шва — промт её не гарантирует.
- **Разрыв:** бесшовность — только постобработкой (у H: offset + inpaint, или mirror-tiling для паттернов; геометрические
  паттерны — `VEC-PATTERN` кодом у G).
- **Фаза 5:** тест 13 — «seamless tileable linen fabric» на Flare, NB2, Seedream 4.0 (11,8 ₽); критерий: после сдвига на 50 %
  ΔE по линии шва ≤ 3, шов не виден глазом.

## 10. IMG-TEXT-LATIN — картинка с текстом латиницей (баннер, постер, OG)

| Кандидат | Доказательства | Метка | Цена |
|---|---|---|---|
| `openai/gpt-5.4-image-2` (GPT Image 2) | AA Text Rendering #1 1195, Productivity #1 1229, Reasoning #1; LMArena TR #3; WeGenBench QA 0.97 | [исследование] | 4–11 ₽ (mie) |
| Flare / Sunburst | AA TR #2 1179 / #4 1161; LMArena TR #2 1436 / #1 1466; Marketing #1 (Flare) | [исследование] | 4–11 ₽ |
| NB2 | AA TR #8 1106; LMArena TR #9 1293; но лишний текст (WeGenBench precision 0.43) | [исследование] | 4,8 ₽ |

- **Почему не другие:** Nano Banana Pro — AA TR #11 при 13,5 ₽; FLUX.2 [flex] — #22 при 14 ₽; FLUX.2 [pro] — #41;
  Seedream 4.x/5 — #16–#42 (при том что Seedream 4.5 лучший по Char F1 в WeGenBench zh/en — [спорно]); Z-Image — #56.
- **Чем нельзя заменить:** текст интерфейса, цены, кнопки, юридические строки — HTML/CSS/SVG поверх картинки (доступность,
  перевод, правка без перегенерации); модели — для надписей как части изображения (вывеска, упаковка, леттеринг).
- **Разрыв:** дословность не гарантирует ни одна модель; OpenAI: «can still struggle with precise text placement and
  clarity» [S5]. Точное размещение текста по координатам — только Ideogram 4.0 (bbox в JSON; вне polza).
- **Фаза 5:** тест 15 — контроль на латинице (13,8 ₽) тем же макетом, что тест 1.

## 11. IMG-TEXT-CYR — картинка с текстом кириллицей

Кандидаты, доказательства и тест — в §17 «Кириллица в картинке». Кратко: GPT Image 2/2.5 (дословно в публичных тестах, N=4),
Nano Banana 2 (№1 MultiTextEdit по правке; перефразирует), Seedream 5.0 Pro (русский в официальном списке языков; ошибка в
слове, N=1), Qwen 2.1 («любой язык» в polza; данных нет). Низкая надёжность → тест 1.

## 12. IMG-EDIT — правка по инструкции или маске

| Кандидат | Доказательства | Метка | Цена |
|---|---|---|---|
| Sunburst / Flare | AA правка #1 1179 / #2 1159; Object-Level #1/#2; Text or Symbol #1/#2; LMArena правка #1 1526 / #2 1482 | [исследование] | 4–11 ₽ |
| NB2 | AA Object-Level #4 1126, Text or Symbol #5 1143, Reasoning-Based #4 1143 | [исследование] | 4,8 ₽ |
| Seedream 5.0 Pro | AA правка #8 1105, Identity #8 1146, Social Media #4 | [исследование] | 5 ₽ (+0,3 за реф.) |
| `qwen/image-2.1` + `mask_url` | маска (белое = менять), seed, 10 реф.; LMArena правка #16 (предв.) | [документация] | 3 ₽ |

- **Бенчмарки правки 2026:** GEditBench v2 (03.2026) — Nano Banana Pro 1096, Seedream 4.5 1089, GPT Image 1.5 1071 (лучшее
  выполнение 1260, худшая согласованность 846) [S63]; RISEBench (23.04.2026) — GPT-Image-1.5 51,4 %, GPT-Image-2 49,4 %,
  Nano Banana Pro 48,3 % [S64]. GPT Image 2.5 и Nano Banana 2 в них нет.
- **Почему не другие:** FLUX.2 — AA правка #37–45; NB2 Lite — #23 и «not optimized for multi-turn sequential editing»;
  `openai/gpt-5-image` (маска у mie) — выключается 23.10.2026.
- **Чем нельзя заменить:** пиксельная неизменность вне области — только композитинг результата в оригинал [S6]; маска GPT
  Image в прямом API — «guidance», не граница [S5].
- **Разрыв:** у GPT 2.5 маски в polza нет; полярности масок у Qwen 2.1 и GPT-5 Image@mie противоположны; удаление объектов
  по маске (FLUX Erase) — вне polza.
- **Фаза 5:** тест 12 — одна правка по маске на Qwen 2.1 в двух полярностях (6 ₽); критерий: изменения только в заявленной
  области (разница вне маски ≤ 2 % площади).

## 13. IMG-OUTPAINT — расширение кадра под другое соотношение

| Кандидат | Как | Доказательства | Цена |
|---|---|---|---|
| Flare / Sunburst | `images: [исходник]` + новый `aspect_ratio` (21:9, 27:16) + «extend the scene, keep everything unchanged» | AA Composition & Framing #2 1189 / #1 1218 [исследование] | 4–11 ₽ |
| NB2 | то же, 21:9 | AA Composition & Framing #8 1109 | 4,8 ₽ |
| FLUX Outpainting (вне polza) | `/v1/flux-tools/outpainting-v1`: холст `width`×`height` + `reference_offset_x/y`, `mode` high или fast, промт — «Experimental: optional», png по умолч., до 4 МП | [документация] | прямой API BFL |
| Grok Imagine 2.0 Smart resize; Ideogram Reframe; Recraft outpaint (только V3) | инструменты вне polza | [мнение вендора] / [документация] | — |

- **Почему не другие:** Seedream 5.0 Pro — без 21:9 в polza; FLUX.2 в polza — без инструмента аутпейнта.
- **Чем нельзя заменить:** неизменный центр — композитинг исходника поверх расширенного холста (код), модель дорисовывает
  только края.
- **Разрыв:** в polza нет «настоящего» аутпейнта с холстом и смещением.
- **Фаза 5:** тест 10 — исходник 16:9 из теста 3 → 21:9 на NB2 и Flare (8,8 ₽); критерий — три условия вместе
  (`edit_check.py outpaint`): SSIM центра ≥ 0,9 **и** ΔE00 медиана ≤ 3 **и** `edge_sharpness` ≥ 0,85, иначе REGENERATED; нет
  повторов объектов. Один SSIM перерисовку не ловит (0,993 у перерисованного центра) — `../08-image-post-processing/02-upscale-outpaint-edit.md`
  §4.3 [проверено] [поправка X 24.09.2026: было «центр… SSIM ≥ 0,9»].

## 14. IMG-MOCKUP — мокап устройства с настоящим скриншотом

| Кандидат | Доказательства | Метка | Цена |
|---|---|---|---|
| Flare | AA UI/UX Design #1 1229 | [исследование] | 4–11 ₽ |
| Sunburst / GPT Image 2 | UI/UX #2 1220 / #3 1204; Layout #1 / #2 | [исследование] | 4–11 ₽ |
| NB2 / NB Pro | UI/UX #6 / #8; GEBench — NB Pro №1 по UI-состояниям (69.62/61.20) | [исследование] | 4,8 / 13,5 ₽ |

- **Вне polza:** Qwen-Image-3.0-Pro («realistic simulation of mainstream interfaces such as web pages», Layout #5); Recraft
  V4.1 Utility («for mockups and product listing photos»).
- **Чем нельзя заменить:** настоящий скриншот — только композитингом (перспективная трансформация в Blender или CSS 3D);
  модели перерисовывают пиксели и текст (OpenAI: пиксельную неизменность даёт композитинг [S6]; GEBench: попадание по
  координате < 10 % у большинства).
- **Разрыв:** нет модели, которая вставляет скриншот без искажения.
- **Фаза 5:** тест 16 — скриншот 1280×800 + сцена ноутбука на Flare и NB2 (8,8 ₽); критерий: OCR текста скриншота в
  результате совпадает ≥ 95 % (ожидается провал → подтверждение композитинга).

## 15. IMG-UPSCALE — апскейл и доводка деталей

| Кандидат | Как | Метка | Цена |
|---|---|---|---|
| `topaz/image-upscale` | `upscale_factor` 1 / 2 / 4 / 8; какая модель Topaz — не указано | [документация] | 7,5 / 7,5 / 15 / 30 ₽ |
| Перегенерация в 4K | Seedream 4.0 (3 ₽), Seedream 4.5 high (5 ₽), NB2 (10,8 ₽), GPT 2.5 (11 ₽) | [документация] | 3–11 ₽ |
| Генеративная «доводка» правкой | Seedream 5.0 Lite — AA Enhancement & Restoration #11 1043 (выше NB2 #19 и NB Pro #22); Sunburst #1 1115 | [исследование] | 4 / 4–11 ₽ |

- **Вне polza:** Topaz API с выбором модели (High Fidelity, Bloom 2 «creative upscaling for GenAI images», Transparent Image
  Upscale с сохранением альфы) [S29]; Recraft crisp/creative upscale; локальные апскейлеры — у H (в волне 1 не
  запускались).
- **Разрыв:** не известно, сохраняет ли Topaz в polza альфу и какой режим (точный или генеративный).
- **Фаза 5:** тест 14 — ×2 PNG с альфой из теста 4 (7,5 ₽); критерий: альфа сохранена, размер ровно ×2, нет «пластиковых»
  текстур.

## 16. IMG-DRAFT — дешёвые эскизы и перебор направлений (ответ на вопрос 4)

| Кандидат | Цена | Качество | Ограничения | Метка |
|---|---|---|---|---|
| `tongyi-mai/z-image` | 1,4 ₽ | AA #74 942; LMArena #56; AA 2,1 с (Turbo) | промт ≤ 1000 символов, без референсов, 5 соотношений, текст только en/zh | [исследование] |
| `google/gemini-3.1-flash-lite-image` | 2,9 ₽ | AA #13 1092 (Marketing #9); LMArena #13; 3,1 с | только 1K; слабая правка | [исследование] |
| `bytedance/seedream-4` | 3 ₽ | AA #21 1026 | seed, 4K, 21:9 | [исследование] |
| `qwen/image-2.1` | 3 ₽ | LMArena #17 (предв.) | seed, 10 реф.; лицензия весов | [исследование] |
| OpenAI `low` (прямой API) | ≈ $0.006 за 1024² (≈ 0,7 ₽) | та же модель, что финал | не в polza | [проверено] |

- **Лучший дешёвый для перебора:** NB2 Lite — на 150 Elo выше Z-Image в AA при цене 2,9 против 1,4 ₽, есть 8:1 и 10
  референсов; Z-Image — когда нужны десятки вариантов композиции без текста.
- **Перенос черновика на дорогую модель:** опубликованных измерений нет [не проверено]. Гипотезы: (а) перенос по промту
  между семействами слабый — модели по-разному трактуют промт, FLUX.2 и Qwen переписывают его (upsampling, `enhance_prompt`);
  (б) черновик как референс для финальной модели («keep the composition of image 1») сохраняет раскладку лучше, чем
  повтор промта; (в) черновик внутри семейства (NB2 Lite → NB2; OpenAI `low` → `high`) переносится лучше всего.
- **Фаза 5:** тест 9 — 3 брифа × (Z-Image, NB2 Lite) → Flare: 3 по промту + 3 с черновиком-референсом (36,9 ₽); критерий:
  VLM-судья «та же композиция и раскладка» ≥ 2 из 3 для варианта с референсом.

## 17. Кириллица в картинке

### 17.1 Что заявляют вендоры (23.09.2026)

| Вендор / модель | Заявление | Источник | Метка |
|---|---|---|---|
| Google, все Nano Banana | ru-RU в списке 15 языков «for best performance»; 3.1 Flash — «Improved i18n text rendering»; «Write your prompt in one language and specify a target language» | [S10], [S11], [S14] | [мнение вендора] |
| ByteDance, Seedream 5.0 Pro и 5.0 flash | русский в списке языков промта API; блог: «over ten commonly used languages… Russian», рендер «adapts to the typographic rules of different languages»; ограничение: «room to improve in finer-grained text rendering» | [S20], [S21] | [мнение вендора] |
| ByteDance, Seedream 5.0 Lite / 4.5 / 4.0 | промт — только китайский и английский | [S21] | [документация] |
| Alibaba, Qwen-Image-3.0-Pro | «native rendering of 12 languages and multiple fonts» (список не найден); витрина Qwen-Image со словом «Виолета» — написано верно | [S24] | [мнение вендора] |
| polza, `qwen/image-2.1` | промт «любой язык» | [S1] | [документация polza] |
| OpenAI, GPT Image | языки не перечислены | [S5], [S6] | — |
| Ideogram 4.0 | «best-in-class multilingual text rendering» без списка | [S31] | [мнение вендора] |
| Recraft | V3 — кириллица вне набора символов (только «І А В Е К М Н О Р С Т У Х»); V4 — «multi-language» без списка | [S30] | [документация] |
| Z-Image | «bilingual text rendering (English & Chinese)» | [S25] | [документация] |
| Imagen 4 (выключена) | промт: English + preview zh, hi, ja, ko, pt, es — без русского | [S15] | [документация] |

### 17.2 Что показывают независимые данные

- **MultiTextEdit** [S41] (правка текста, 12 языков вкл. русский, судья LVM + LSF): Nano Banana 2 — SemAvg 4.006, разрыв
  EN/не-EN 0.100 (лучший и самый ровный); GPT-image-1.5 — 3.577, разрыв 0.517; открытые модели 2025 — 2.4–3.2. Русский —
  один из самых трудных языков (ΔLSF 1.038 в среднем по моделям). Ограничение: только правка, нет GPT 2.x, Seedream, Qwen 3.0.
- **LingT2I** [S67] (ACM MM 2026, 11.08.2026) — единственный найденный независимый бенчмарк **генерации** с русским: 300
  русских промтов из 3000, короткие строки (≈ 3 токена) в английском описании сцены, OCR — Gemini 2.5 Flash. Русский
  против английского: EasyText 0.59 / 0.87; «Nano Banana» (версия не указана) 0.47 / 0.68; Qwen-Image 0.32 / 0.69;
  AnyText2 0.14 / 0.56; FLUX.1-Krea 0.09 / 0.65; общие модели в среднем 0.29 / 0.67. Типичная ошибка — читаемый, но не тот
  текст (у Nano Banana точность 0.48 при качестве текста 0.94). Моделей 2026 года (GPT Image 2/2.5, NB2/Pro, Seedream 5,
  FLUX.2) нет.
- **WeGenBench, UniGenBench++** [S42], [S43] — только zh/en; OCRGenBench, STRICT, MultiBanana, StyleTextGen, Qwen-Image-Bench —
  без русского (сверено помощником C1-B).
- **Арены** — английские промты; о кириллице ничего [S38].
- **OCR как инструмент оценки:** кириллица распознаётся почти как латиница у ряда OCR-моделей (GlotOCR Bench) [S68], но
  латинские двойники путаются (MDPBench, ScriptMoE) [S44], [S45] → OCR + сравнение кодовых точек + выборочная ручная проверка.

### 17.3 Что показывают сообщества и публичные тесты (свидетельства, не истина)

- **klerk.ru / Genova AI** [S47] (26.08.2026) — партнёрский материал агрегатора; 4 бизнес-макета, один русский промт,
  первая генерация, 12 картинок просмотрены глазами (`99-raw/experiments/C1/05-cyrillic-public-samples/`): заданный текст без
  орфографических ошибок у GPT Image 2, Nano Banana 2 и Grok Imagine 2.0 (по 4/4); **дословно — GPT Image 2 и Grok 4/4, NB2
  2/4** (перефразирует: «ЗАРЕГИСТРИРОВАТЬСЯ» вместо «Записаться»; добавляет латинский псевдотекст и реальный бренд на
  наушниках); Grok и NB2 ошибаются в мелком тексте, который добавили сами («Прибыл», «Прибль», «Динокь» у Grok).
- **Хабр / StudyAI** [S48] (≈ 22.09.2026) — одно рекламное задание, 6 моделей, N=1: GPT Image 2.5 — без заметных ошибок;
  NB2 и Grok — хорошо; FLUX.2 — «можжевельник» с пропущенной буквой; Seedream 5.0 — «СОСТАД» вместо «СОСТАВ»; Midjourney —
  кириллица потеряна.
- Оба автора продают доступ к моделям по партнёрским ссылкам — это свидетельства, не измерение.
- Вывод [мнение]: крупные короткие строки у моделей 2026 года часто написаны без орфографических ошибок; главные сбои — в
  дословности (NB2 2/4; у моделей 2025 года в LingT2I — «читаемо, но не то»), в мелком тексте, который модель добавляет сама,
  и в редких буквах. Выборка мала (N ≤ 4 на модель), промты опубликованы не полностью.

### 17.4 Как работать с кириллицей сейчас

1. Текст, который важен (заголовки, цены, кнопки, юридические строки), — HTML/CSS/SVG поверх картинки; модели — для
   надписей внутри сцены (вывеска, упаковка, леттеринг) [практика; рабочая гипотеза базы].
2. Если текст рисует модель: строка в кавычках, «exactly once», «no other text»; шрифт — описанием; язык промта — любой,
   но строка — дословно; для NB2 — «text-first»: сначала утвердить текст, затем картинку [S6], [S14].
3. Проверка: OCR с языком `ru` → посимвольно по кодовым точкам; отдельный флаг латинских двойников (А/A, В/B, Е/E, К/K,
   М/M, Н/H, О/O, Р/P, С/C, Т/T, У/Y, Х/X); отдельно — лишний текст [S44], [S45].
4. Фолбэк: сгенерировать без текста (или с латинской заглушкой) и наложить текст кодом.

### 17.5 Тест фазы 5 (тест 1, 88,6 ₽)

8 моделей × 2 промта × 1 картинка, 16:9, 1K: `gpt-image-2-5-flare` (4), `openai/gpt-5.4-image-2` (4, mie),
`google/gemini-3.1-flash-image-preview` (4,8), `google/gemini-3-pro-image-preview` (13,5), `seedream/5-pro-text-to-image`
(basic, 5), `bytedance/seedream-4.5` (5), `qwen/image-2.1` (3), `black-forest-labs/flux.2-pro` (5). Критерий: все заданные
строки совпадают посимвольно (кодовые точки после OCR `ru` + ручная сверка), 0 латинских двойников, 0 лишних слов;
отдельно — оценка шрифта (кириллица не «латиница с подменой»). Ответ определяет модель по умолчанию для `IMG-TEXT-CYR`.

```text
// промт A (английский промт, русские строки) · все 8 моделей · polza 2026-09-23 · 16:9, 1K · [не проверено]
Web banner, 16:9, clean modern layout on a warm off-white background with a simple green sofa photo on the right.
Render exactly this Russian text, each line exactly once, in a bold geometric sans-serif, dark green, left-aligned:
line 1 (large headline): "Весенняя распродажа"
line 2 (medium): "Скидки до −30 % на всю мебель"
button (rounded, green, white text): "Подробнее"
No other text, no English words, no logos, no watermark.
```

```text
// промт B (русский промт, панграмма и знак ₽) · все 8 моделей · polza 2026-09-23 · 16:9, 1K · [не проверено]
Карточка товара для интернет-магазина, 16:9, светлый фон, слева фотография свежего багета на деревянной доске.
Справа напиши ровно этот текст на русском, каждую строку один раз, шрифт — строгий гротеск, тёмно-серый:
заголовок: «Съешь же ещё этих мягких французских булок»
цена (крупно): «Цена: 1 290 ₽»
строка: «Доставка завтра»
кнопка (оранжевая, белый текст): «В корзину»
Никакого другого текста, латиницы, логотипов и водяных знаков.
```

Панграмма «Съешь же ещё этих мягких французских булок» содержит все 33 буквы (включая Ё, Ъ, Ы, Щ, Э) — проверяет покрытие
алфавита; «₽» (U+20BD) и «−» (U+2212) — редкие знаки.

**Итог фазы 5 (25.09.2026, E-02)** `[проверено]`: прогнан промт A на 9 моделях (+ Sunburst,
1 образец на модель, 48,30 ₽); промт B (панграмма, ₽) не прогонялся (лесенка E-03…E-06 отменена заказчиком 25.09). Дословно (глаз;
OCR ложно тревожит на «д» ≈ g и на трафарете) — Flare, GPT Image 2, NB2, NB Pro, Seedream 5.0 Pro, Seedream 4.5 (шрифт-трафарет вместо
гротеска); Sunburst — «– 30» (пробел после минуса); Qwen 2.1 — «Весенная», «всеђ»; FLUX.2 Pro — «Весеннаія», «всіо». Тот же промт у
Recraft V4.1 через RouterAI (E-07, 3,86 ₽) — дословно, OCR pass. Модель по умолчанию для `IMG-TEXT-CYR` не выбрана: основной — HTML-слой;
короткая надпись моделью — после `asset_audit.py ocr --expect` и чтения человеком (K-05: OCR ловит 15 из 24 заложенных ошибок,
латинских «близнецов» — никто) → `../13-routing-matrix/routing.yaml` v2.

## 18. Фаза 5: сводный план тестов C1 (≈ 327 ₽ из 2000 ₽)

| № | Код | Гипотеза | Минимальный тест | Модель и параметры (polza) | ₽ | Критерий | Ценность |
|---|---|---|---|---|---|---|---|
| 1 | TEXT-CYR | Крупный русский текст верен у GPT 2.x / NB2 / Seedream 5.0 Pro / Qwen 2.1; мелкий и панграмма — нет | 2 промта (§17.5) × 8 моделей | см. §17.5; 16:9, 1K | 88,6 | 100 % посимвольно, 0 двойников, 0 лишних слов | 3 |
| 2 | все (Seedream) | mie не ставит видимый «AI-generated» | 1 картинка без текста | `bytedance/seedream-4` 1:1 1K | 3 | нет надписи справа внизу | 3 |
| 3 | HERO-PHOTO | GPT 2.5 в polza отдаёт заявленные 2K; Flare ≈ Sunburst при меньшем времени | промт §2 на обеих | Sunburst и Flare, 16:9, 2K | 14 | длинная сторона ≥ 2048 px; время; слепое предпочтение 2 человек | 3 |
| 4 | CUTOUT | нативная альфа Qwen 2.1 годится для веба | 2 объекта (стекло; волосы/мех) | `qwen/image-2.1` transparent, png, 1K | 6 | альфа есть; ореол ≤ 2 px; стекло полупрозрачно | 3 |
| 5 | SERIES | мульти-референс держит объект в 3 сценах; лидер арены (GPT 2.5) против лидера бенчмарков серий (NB Pro) | эталон + 3 сцены × 3 модели (§5) | Flare (эталон); Seedream 4.5 basic, Flare 1K, NB Pro (`google/gemini-3-pro-image-preview`) 1K | 71,5 | VLM «тот же объект» ≥ 4/5; ΔE ≤ 5 | 3 |
| 6 | PRODUCT | товар по фото переносится в сцену без искажения | 1 товар × 4 модели (§3) | Flare, NB2 preview, Seedream 5.0 Pro (1 реф.), Qwen 2.1 | 16,8 | OCR этикетки совпадает; IoU формы ≥ 0,9 | 3 |
| 7 | все | метаданные происхождения и фактическая модель | `exiftool -a -G1`, `c2patool` на всех файлах; поля ответа `model`/провайдер | — | 0 | таблица «модель → SynthID/C2PA/EXIF» | 3 |
| 8 | BG-ABSTRACT | hex попадает точнее у FLUX.2 (JSON) | 2 сцены × 3 hex (§8) | FLUX.2 [pro] 1K, Flare 1K, NB2 preview 1K | 27,6 | ΔE2000 ≤ 5 для ≥ 2 из 3 цветов | 2 |
| 9 | DRAFT | черновик-референс переносит композицию на Flare | 3 брифа × (Z-Image, NB2 Lite) → Flare ×6 | `tongyi-mai/z-image`, NB2 Lite, Flare 1K | 36,9 | VLM «та же композиция» ≥ 2/3 с референсом | 2 |
| 10 | OUTPAINT | 16:9 → 21:9 без искажения центра | исходник теста 3 × 2 модели | NB2 preview, Flare (images + 21:9) | 8,8 | SSIM центра ≥ 0,9 + ΔE00 ≤ 3 + `edge_sharpness` ≥ 0,85 (H `08/02` §4.3); нет повторов [поправка X 24.09.2026] | 2 |
| 11 | BG-ABSTRACT | лента 8:1 без повторов | 2 баннера | NB2 Lite 8:1 | 5,8 | нет дублей объектов; пустая зона сохранена | 2 |
| 12 | EDIT | маска Qwen 2.1: белое = менять | 1 правка × 2 полярности | `qwen/image-2.1` + `mask_url` | 6 | вне маски изменено ≤ 2 % площади | 2 |
| 13 | TEXTURE | без tile бесшовности нет | «seamless tileable linen» × 3 | Flare 1:1, NB2 1:1, Seedream 4.0 1:1 | 11,8 | шов после сдвига 50 %: ΔE ≤ 3 | 2 |
| 14 | UPSCALE | Topaz в polza сохраняет альфу | ×2 PNG из теста 4 | `topaz/image-upscale` factor 2 | 7,5 | альфа есть; ровно ×2 | 1 |
| 15 | TEXT-LATIN | контроль латиницы на том же макете | промт A на английском × 3 | Flare, NB2 preview, Seedream 5.0 Pro | 13,8 | 100 % посимвольно | 1 |
| 16 | MOCKUP | модели искажают вставленный скриншот | скриншот + сцена ноутбука × 2 | Flare, NB2 preview | 8,8 | OCR скриншота ≥ 95 % (ожидается провал) | 1 |

Порядок: 2 → 7 (на файле теста 2) → 3 → 1 → 4 → 6 → 5 → остальные. Если тест 2 покажет видимый знак — Seedream исключается
из тестов 1, 5, 6, 15 (экономия ≈ 45 ₽).

## Частые ошибки

1. **Выбор по общему рейтингу.** Для текста — срез Text Rendering (там №1 GPT Image 2, а не Sunburst в AA), для UI — UI/UX
   (Flare), для правки текста — Text or Symbol (NB2 — лучший не-OpenAI).
2. **«Прозрачный фон» словами.** Модель без альфы нарисует шахматку или белый фон; в polza альфу даёт только Qwen 2.1.
3. **Товар «как есть» генерацией.** Этикетка и логотип искажаются; нужен композитинг настоящего фото.
4. **Скриншот в мокапе генерацией.** Модель перерисует интерфейс; вставлять кодом/в Blender.
5. **Бесшовность промтом.** «seamless» без проверки сдвигом — не бесшовно.
6. **Текст интерфейса в картинке.** Кнопки, цены, заголовки — HTML; иначе нет доступности, перевода и правки.
7. **Кириллица без проверки кодовых точек.** «Р» латинская и кириллическая выглядят одинаково.
8. **NB Pro «для текста».** Дороже NB2 в 2,8 раза и ниже в текстовых срезах.
9. **FLUX.2 [flex] в polza ради типографики.** Steps/guidance не выставлены, TR #22, 14 ₽.
10. **Z-Image с длинным промтом.** Лимит 1000 символов.
11. **Серия без эталона и seed.** Без референса и зерна стиль «плывёт»; seed в polza — только Qwen 2.1 и Seedream 4.0.
12. **Seedream без проверки знака.** Видимый «AI-generated» по умолчанию в прямом API.
13. **Черновик на одной модели, финал на другой по тому же промту.** Перенос не гарантирован; передавать черновик как
    референс.

## Чек-лист

- Для задачи выбран срез арены с тем же смыслом (Text Rendering, UI/UX, Retail, Identity…)?
- Нужна ли альфа, и если да — выбрана модель с альфой (Qwen 2.1) или конвейер удаления фона?
- Весь важный текст вынесен в HTML/CSS/SVG, а в картинке — только декоративный?
- Для кириллицы есть OCR-проверка по кодовым точкам и фолбэк «текст кодом»?
- Для товара и скриншота предусмотрен композитинг?
- Для серии есть эталон, референс в каждой генерации и (по возможности) seed?
- Для текстуры запланирован сдвиг на 50 % и заделка шва?
- Нужное соотношение (21:9, 8:1) есть у выбранной модели в polza?
- Цена в ₽ посчитана по каталогу провайдера, который реально отвечает?
- Тест фазы 5 для этой задачи назначен (§18)?

## Открытые вопросы и противоречия

1. Генерацию кириллицы независимо мерил только LingT2I — на моделях 2025 года; для моделей 2026 года есть лишь публичные
   тесты с N ≤ 4 на модель и MultiTextEdit (правка) → тест 1.
2. Иллюстрации: AA (NB2 выше) против LMArena (Seedream 5.0 Pro выше) во втором эшелоне.
3. Текст: WeGenBench (Seedream 4.5 лучший по Char F1) против арен (Seedream — середина).
4. Серии: ViStoryBench и OmniRef-Bench ставят №1 Nano Banana Pro, но без GPT 1.5/2/2.5 и NB2; «стиль серии» (не персонаж) не
   мерил никто; `sequential_image_generation` Seedream в polza не выставлен → тест 5.
5. Qwen 2.1 — единственная прозрачность в polza при некоммерческой лицензии весов → решение L.
6. Topaz в polza — неизвестная модель и поведение альфы.
7. Перенос черновика на финальную модель — нет данных ни у кого.
8. Работает ли в polza правка с новым `aspect_ratio` у GPT 2.5 как аутпейнт (не описано в каталоге) → тест 10.

## Источники

Нумерация [S#] общая для `03-image-models/` (реестр — `99-raw/experiments/C1/06-model-cards-build/sources.py`).

- [S1] polza.ai. Каталог моделей API (type=image, с провайдерами). снят 2026-09-23 08:45. https://polza.ai/api/v1/models?type=image&include_providers=true — первичные данные: id, провайдеры, параметры с описаниями, цены ₽; бесплатный эндпоинт [проверено].
- [S5] OpenAI. Image generation guide (+ калькулятор токенов GptImageTokenCalculator). 2026-09-23. https://developers.openai.com/api/docs/guides/image-generation — параметры, размеры, маска, прозрачность, формула токенов [проверено].
- [S6] OpenAI. Image prompting guide (вкладки 2.5 / 2 / 1.5 / 1). 2026-09-23. https://developers.openai.com/api/docs/guides/image-prompting — канонический гайд по промтам GPT Image; заменил cookbook-гайд.
- [S10] Google. Gemini API — Image generation (Nano Banana). 2026-09-23. https://ai.google.dev/gemini-api/docs/image-generation — модели, размеры, токены, референсы, языки (ru-RU), лучшие практики.
- [S11] Google. Страницы моделей gemini-3-pro-image, gemini-3.1-flash-image, gemini-3.1-flash-lite-image. 2026-09-23. https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image — возможности, SynthID+C2PA у Lite, латентность.
- [S14] Google Cloud (K. Davaajav, H. Chinoy). Ultimate prompting guide for Nano Banana. 2026-03-06. https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-nano-banana — формулы промтов, текст, C2PA + SynthID.
- [S15] Google Cloud. Vertex AI: Imagen 4; Gemini 3 Pro Image; deprecations. 2026-09-23. https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/imagen/4-0-generate — Imagen 4 Discontinuation 30.06.2026, C2PA Not supported; Vertex → Gemini Enterprise Agent Platform.
- [S20] ByteDance Seed. Seedream 5.0 Pro — блог + страницы 5.0 Pro, 5.0 Lite, 4.5. 2026-07-08. https://seed.bytedance.com/en/blog/beyond-generation-it-understands-design-introducing-seedream-5-0-pro — заявления вендора: языки, инфографика, слои; ограничения текста.
- [S21] BytePlus ModelArk. Image generation API (Seedream 5.0 pro/flash/lite, 4.5, 4.0). 2026-09-23. https://docs.byteplus.com/en/docs/ModelArk/1541523 — языки промта, size, watermark default true, background, layers, sequential.
- [S24] Alibaba Cloud Model Studio. Qwen-Image-3.0-Pro; image generation & editing API reference; text-to-image; qwen-image API. 2026-09-23. https://www.alibabacloud.com/help/en/model-studio/qwen-image-3-0-pro — 12 языков (без списка), 1:8…8:1, цены; витрина «Виолета»; Wan 2.7 color_palette.
- [S25] Tongyi-MAI (Alibaba). Z-Image README (12 044★, push 2026-02-09). 2026-09-23. https://github.com/Tongyi-MAI/Z-Image — Turbo/Base, en/zh текст, Apache-2.0.
- [S29] Topaz Labs. Topaz API — список моделей (+ www.topazlabs.com/api). 2026-09-23. https://developer.topazlabs.com/llms.txt — Gigapixel, Wonder, Bloom, Transparent Image Upscale.
- [S30] Recraft. Recraft docs: V4.1, V4 Styles, API endpoints, текст и набор символов, права. 2026-09-23 (кэш соседей). https://www.recraft.ai/docs/recraft-models/recraft-v4-1 — style_id, controls.colors, SVG; V3 без кириллицы.
- [S31] Ideogram. Ideogram 4.0 — блог + GitHub ideogram-oss/ideogram-4 (README, docs/prompting.md) + API Generate v4. 2026-06 / 2026-09-23. https://ideogram.ai/blog/4.0 — JSON-подписи, bbox, палитра, лицензия весов.
- [S34] Midjourney. Version (V8.2, V8.1) + Enterprise API Survey. 2026-09-23 (через r.jina.ai; прямой — 403). https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version — параметры V8.x; официального API нет.
- [S38] Artificial Analysis. Image methodology. 2026-09-23. https://artificialanalysis.ai/image/methodology — дефолты вендора, 1:1, seed 42, английские промты, цена за 1000.
- [S41] Cheng et al. (HIT). MultiTextEdit: многоязычная правка текста в картинках, 12 языков. 2026-05 (v2). https://arxiv.org/abs/2605.08163 — правка текста, 12 языков вкл. русский; из закрытых — только GPT-image-1.5 и NB2.
- [S42] Tencent Weixin, UESTC, DLUT. WeGenBench. 2026-06. https://arxiv.org/abs/2606.20100 — 4000 промтов zh/en; текст: Char F1, precision; судья Qwen3.5-397B.
- [S43] —. UniGenBench++. 2025-10. https://arxiv.org/abs/2510.18701 — многоязычность = zh/en; прочитано частично.
- [S44] —. MDPBench (§3: путаница кириллицы с латиницей в OCR). 2026-03. https://arxiv.org/abs/2603.28130 — для метрики фазы 5.
- [S45] —. ScriptMoE / TextMuSS (Latin-Cyrillic homoglyph confusion). 2026-09. https://arxiv.org/abs/2609.24058 — прочитано частично.
- [S47] Genova AI (блог на Клерк.ру). Сравнение генераторов на русских промтах (4 макета × 3 модели, первая генерация). 2026-08-26. https://www.klerk.ru/blogs/genova-ai/706310/ — партнёрский материал агрегатора; картинки проверены глазами [мнение].
- [S48] StudyAI (Хабр). Сравнение 6 моделей на одном русском рекламном задании, N=1. ≈ 2026-09-22. https://habr.com/ru/companies/studyai/articles/1085264/ — корпоративный блог агрегатора [мнение].
- [S63] Jiang et al. GEditBench v2 (попарный Elo). 2026-03. https://arxiv.org/abs/2603.28547 — 1200 запросов, 23 задачи; ρ = 0.929 с Arena.
- [S64] RISEBench authors. RISEBench (NeurIPS 2025 D&B Oral) + живой лидерборд (GitHub PhoenixZ810/RISEBench 154★). обновлён 2026-04-23. https://arxiv.org/abs/2504.02826 — правка с рассуждением; 360 примеров; судья GPT-4.1.
- [S67] RISys-Lab. LingT2I: многоязычный рендер текста в генерации (ACM MM 2026), 10 языков вкл. русский. 2026-08-11. https://arxiv.org/abs/2608.11002 — единственный найденный независимый бенчмарк генерации русского текста; модели 2025 года; OCR — Gemini 2.5 Flash.
- [S68] —. GlotOCR Bench. 2026-04. https://arxiv.org/abs/2604.12978 — OCR кириллицы близок к латинице у ряда моделей.
