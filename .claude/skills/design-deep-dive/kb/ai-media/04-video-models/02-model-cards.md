# Модели видео: карточки 21 модели polza и важных моделей вне polza

Волна 1 · агент C2 · 23.09.2026 · 52 внешних источника [S1]–[S46], [S49]–[S54] (документация вендоров, API, арены,
статьи; 50 прочитаны целиком, 2 просмотрены) + 5 видео-дайджестов волны 2 [V:…] · 3 опыта без платных вызовов (`99-raw/experiments/C2/01-…` цены, `02-…` выходные файлы,
`03-…` генератор YAML) · снимок каталога polza 2026-09-23 (живой каталог 08:48 совпал) · машиночитаемые карточки —
`models/*.yaml` (`checked: 2026-09-23`).

## Выжимка для агента

1. **Сначала смотри, что модель умеет через polza, а не у вендора**: polza выставляет урезанный набор параметров
   (нет `negativePrompt` у Veo, нет `multi_prompt`/`elements` у Kling, нет `camera_fixed`/`draft`/`return_last_frame` у
   Seedance 2.x, нет `last_frame`/`keyframes` у Grok) → §2, §3 `[документация]`.
2. **Первый + последний кадр через polza** — только `google/veo3` и `google/veo3_fast` (`FIRST_AND_LAST_FRAMES_2_VIDEO`),
   `kling/v3` (`images` 0–2), `minimax/hailuo-3-max` (≤2) и, вероятно, `bytedance/seedance-1.5-pro` (≤2) → §2
   `[документация]` + `[не проверено]` для Seedance 1.5 [поправка фазы 5, 25.09.2026: Seedance 1.5 Pro — подтверждено: вторая картинка = последний кадр
   (SC-04, 1 образец); GA Omni 1.1 — поля `first_frame_url`/`last_frame_url` принимают URL хранилища polza (T9) →
   `../99-raw/phase5/runs/SC-showcase/SC-04_endpoints.jpg`].
3. **Не рассчитывай на строгий первый/последний кадр у Seedance 2 / 2 Fast / 2 Mini / 2.5 через polza**: каталог называет
   `images` «референсными», а у вендора FLF и референсы — взаимоисключающие режимы → §3.7 `[спорно]`, тест фазы 5
   [поправка фазы 5, 25.09.2026: подтверждено — Seedance 2 Mini [A, A]: SSIM кадра 0 к A 0,60, шов 7,21 (I-08); Seedance 2 Fast с фразой «Use @Image1 as the
   first frame.» стартовый кадр держит (SSIM 0,85, VM-01), 41,85 ₽ за 480p 4 с].
4. **Нативная петля (`loop`) есть только у Luma Ray 3.2** (`video.loop`, 5 с) — вне polza; у всех остальных петля
   собирается через одинаковые первый/последний кадр или в постобработке → §4.1 `[документация]`.
5. **Неподвижная камера параметром** — только `fixed_lens` у Seedance 1.5 Pro (= `camera_fixed` BytePlus); у остальных
   — прозой: «Locked camera. The camera remains still.» (Runway), «static shot», «[static]» (MiniMax) → §3.6, §5
   `[документация]`.
6. **Seedance 1.5 Pro у BytePlus снят (Retired, замена — Seedance 2.0 Mini)**, в polza пока есть; держи запасной
   маршрут → §3.6 `[документация]` [поправка фазы 5, 25.09.2026: в фазе 5 — 32 ролика, петля [A, A] + `fixed_lens` лучшая по шву (I-03 1,28), а
   премиумы по шву хуже (Kling 3 std 2,12, GA Omni 5,08, Kling 3 pro 1080p — почти стоп-кадр) → готовой замены петли нет].
7. **Самый дешёвый перебор**: Seedance 1.5 Pro 480p 4 с = **5,25 ₽**, Grok Imagine Video 1.5 480p = **1,62 ₽/с**,
   Seedance 2 Mini 480p = **2,57 ₽/с** (polza 2026-09-23) → §2 `[проверено]`
   [поправка фазы 5, 25.09.2026: цены по паспортам фазы 5: Seedance 1.5 Pro 720p 4 с — 10,5, 8 с — 21, **1080p 4 с — 22,5, 8 с — 45**; Kling 3 std 5 с 720p —
   50, **Kling 3 pro — 12 ₽/с, 1920×1080** (4 с — 48, 3 с — 36); Grok 1.5 720p 4 с — 12,15; GA Omni 1.1 1080p 4 с — 48].
8. **Veo 3.1 в polza — всегда 8 с и со звуком** (длительности и `resolution` нет в каталоге; по KIE — умолчания 8 с/720p);
   1080p/4K — отдельными операциями `upscale_1080p` 10 ₽ / `upscale_4k` 90 ₽ → §3.1 `[документация]` + `[не проверено]`.
9. **Veo `extend` в polza — 45 ₽ за шаг**, только для Veo; остальные 19 моделей операций не имеют, хотя эндпоинт указан
   → §3.1 `[документация]`.
10. **Звук по умолчанию включён** у Seedance 2 / Fast / Mini / 2.5 (`generate_audio: true`), Veo (всегда), Gemini Omni,
    Grok, MiniMax H3 Max — для фонов ставь `false`, где параметр есть, и вырезай дорожку при кодировании, где его нет
    → §2 `[документация]` [поправка фазы 5, 25.09.2026: вживую: звук есть у Grok 1.5 (AAC) и GA Omni 1.1 — всегда; у Seedance 1.5 Pro, Seedance 2.x и Kling 3 с
    `"false"` дорожки нет (T4, VM-01, ffprobe)].
11. **Kling 3.0 `aspect_ratio` по умолчанию 1:1** и игнорируется при стартовом кадре — всегда передавай 16:9 явно для t2v
    и готовь кадр нужных пропорций для i2v → §3.3 `[документация]`.
12. **Gemini Omni по умолчанию монтирует несколько планов** — для фона пиши «single continuous shot, no scene cuts»;
    1080p/4K у Omni — апскейл из 720p → §3.2 `[документация]`.
13. **Для i2v описывай движение, а не картинку**: Google, Runway, xAI и BytePlus согласны («Prompt for motion only»,
    «Refer to subjects in general terms like "the subject"») → §5 `[консенсус]`.
14. **Негатив прозой («no camera movement») у Runway даёт обратный эффект** — формулируй утвердительно («Locked camera»);
    параметр `negative_prompt` в polza есть только у `wan/2.5` → §5 `[документация]`.
15. **Кавычки в промте Veo/Omni могут отрисовать текст в кадре** (Google Vertex best practices) — для беззвучных фонов
    не используй кавычки вовсе → §5 `[документация]`, противоречит Cloud Blog → `[спорно]`.
16. **Картинку для i2v кадрируй точно под выходные пиксели** (Seedance 2.x: иначе «image stretching and compression» —
    рывки кадров; Runway и Grok «auto-crop»/«stretch» при несовпадении пропорций) → §3.7, §4 `[документация]`.
17. **Лидеры арен 09.2026** — Gemini Omni Flash, Wan 3.0, MiniMax H3 / H3 Max, Seedance 2.0/2.5; Veo 3.1 и Kling 3.0 —
    второй эшелон; это общий «что красивее», не пригодность под петли → `01-landscape-and-benchmarks.md` `[исследование]`.
18. **MiniMax H3 Max в polza — быстрый вариант (post-trained fal), не флагман 2K**: 480p/768p, 5–15 с; флагман H3 (2K)
    есть только у MiniMax/Runway/fal → §3.12 `[документация]` [поправка фазы 5, 25.09.2026: 25.09 через `openrouter` — 2 × 503 «нет провайдеров»
    (0 ₽) → выбыл (`../13-routing-matrix/routing.yaml` `defaults.unavailable_2026_09_25`)].
19. **Wan 3.0 в polza — плоские 23,6 ₽/с = цена 1080p у Alibaba**: на 480p переплата ~4×; первый+последний кадр у Wan 3.0
    есть у вендора, но не через polza (`images` ≤1) → §3.10 `[документация]` [поправка фазы 5, 25.09.2026: 25.09 — 503 «нет провайдеров» (0 ₽),
    выбыл вместе с H3 Max и Topaz видео (2 × `INTERNAL_ERROR`)].
20. **Grok Imagine Video 1.5 через polza в ~6 раз дешевле прайса xAI** — сверь выход (разрешение, fps, звук) в фазе 5,
    прежде чем строить на нём перебор → §3.13 `[спорно]` [поправка фазы 5, 25.09.2026: вживую 720p 4 с — 12,15 ₽, 1280×720, AAC и теги BT.709, C2PA Valid;
    при «камера неподвижна» сильно меняет форму (движение 2,65 против 0,61 у Seedance, VM-01) — годен для перехода раздела;
    с запретами движения дрейф объекта −58 % (D2-08)].
21. **Sora 2 снята**: приложение закрыто 26.04.2026, Videos API (`sora-2`, `sora-2-pro`) отключается 24.09.2026 — не
    рекомендовать и не маршрутизировать → §4.4 `[документация]`.
22. **Выходы не готовы для веба — перекодируй всегда**: звук (AAC) есть почти у всех; по документации Seedance 2.5 1080p
    и Seedance 2.0 4K — HEVC 10 бит, Seedance 2.5 `mov` — H.264 yuv444p + PCM, Runway Gen-4.5 HDR — HEVC Main 10; Kling 3.0
    отдаёт 1928×1072, MiniMax H3 кладёт `moov` в конец файла → профиль 3d `05` §3.15 (H.264 CRF 23 + `+faststart`,
    AV1/VP9 первым `<source>`, `-an`) и `../09-video-pipeline/` → §6 `[документация]` + `[проверено: опыт 02]`
    [поправка фазы 5, 25.09.2026: выходы фазы 5 (ffprobe): Kling 3 std — 1280×720, pro — 1920×1080; Seedance, Kling, Omni — без цветовых тегов, Kling и Omni
    ближе к BT.601 (n = 5) → BT.709 с полными тегами при кодировании; Grok — теги BT.709].
23. **Результаты живут недолго**: polza 7 дней, Seedance (BytePlus) URL 24 ч, Veo (Gemini API) 2 дня, Kling 30 дней,
    xAI/Runway/Luma — временные URL → скачивай сразу `[документация]`.
24. **Видимого водяного знака по умолчанию нет** у Kling API (`watermark_info.enabled=false`), BytePlus (`watermark=false`),
    Alibaba DashScope (`watermark=false`); **невидимый SynthID** — у всех Veo и Gemini Omni; у Veo в polza есть свой
    `watermark` (текст ≤50 символов, по умолчанию пусто) → §3, §6 `[документация]` [поправка фазы 5, 25.09.2026: машиночитаемые метки выходов фазы 5:
    Kling 3 — китайская AIGC в тегах MP4 (4 из 4), Grok 1.5 — C2PA Valid (7 из 7), GA Omni — C2PA Trusted + SynthID, Seedance 2 Fast —
    C2PA Valid, Seedance 1.5 Pro — ничего (0 из 32) → `../99-raw/experiments/L/05-phase5-provenance/2026-09-25-all/README.md`].
25. **Строгий первый + последний кадр у вендоров работает**: в официальном примере Seedance 2.5 кадр 0 совпал с заданным
    first frame (SSIM 0,979), последний — с last frame (SSIM 0,959); у Wan 3.0 вендор обещает «pixel-level reproduction» →
    для петли проблема не в точности шва, а в угасании движения → §6.3 `[проверено: опыт 02, 1 образец]` + `[документация]`
    [поправка фазы 5, 25.09.2026: в фазе 5 так и вышло: Kling 3 pro 1080p [A, A] — движение 0,024 (стоп-кадр), Kling 3 std — живость 0,42; у GA Omni FLF
    к кадру A не возвращается (SSIM 0,86 / 0,73)].
26. **Петля из одинаковых кадров: отрежь последний кадр** (он почти дублирует первый — будет микропауза) или смешай 2–4
    кадра → §6.3 `[мнение]`, проверка — агент I.
27. **Черновик вендора предсказывает хореографию, а не детали**: пара Seedance 2.5 Draft 480p → Final 1080p — кривая
    движения совпадает (корреляция 0,87), кадры в тот же момент похожи умеренно (SSIM 0,65) → выбирай движение на дешёвом
    ролике той же модели, лица/текст/логотип оценивай только на финале → §6.4 `[проверено: опыт 02, 1 пара]`.
28. **Метки происхождения теряются при кодировании**: у Gemini Omni в файле C2PA-манифест (+ SynthID в пикселях), у
    Seedance, Kling, MiniMax — китайская метка `AIGC` в метаданных MP4; любой ffmpeg (даже `-c copy`) выбрасывает C2PA,
    `AIGC` сохраняется только с `-map_metadata 0 -movflags use_metadata_tags` или в WebM → решение — с агентом L
    (`../12-legal-provenance/`) → §6.5 `[проверено: опыт 02]`.
29. **«Один непрерывный план» проверяй автоматически**: отношение максимального скачка межкадровой разницы к медиане > 10
    выдаёт склейку (мульти-шоты Seedance 2.5, Kling, Wan 2.6, MiniMax H3 — 18–84) → §6.3 `[проверено: опыт 02, 28 роликов]`.
30. **Gemini Omni: preview-эндпоинт Google снимается 30.09.2026**; GA — `gemini-omni-1.1-flash` (27.08.2026, с первым +
    последним кадром и продлением); какую версию отдаёт polza — неизвестно → тест №10 и повторная проверка после 30.09 →
    §3.2 `[документация]` + `[спорно]`.
31. **С двумя кадрами перечисляй движение всех элементов сцены и подгоняй цвет конечного кадра к начальному**: что не
    названо — стоит; правка кадра в редакторе сдвигает цвет (два независимых практика: Veo 3.1 в Adobe Firefly и Kling 3.0)
    → §3.1, §3.3 `[практика]`.

## 1. Как читать карточки

- **Два уровня правды.** (1) Каталог polza — что реально можно передать через `POST /api/v1/media` (параметры с
  описаниями на русском, `top_provider.pricing`) [S1]; гайды polza [S2] местами расходятся с каталогом — верь каталогу,
  расхождения выписаны в §7. (2) Документация вендора и провайдера `mie` (= KIE.ai: в описаниях каталога «передаётся в
  KIE как adaptive», «по документации KIE», «передано в KIE как video_list») [S3] — что модель умеет вообще и как
  трактуются параметры.
- **Провайдеры polza для видео** (23.09.2026): `mie` (KIE) — 16 моделей, `Alibaba` — 3 (`alibaba/wan-3.0`,
  `alibaba/happyhorse-1.0/1.1`), `openrouter` — 2 (`minimax/hailuo-3-max`, `alibaba/wan-3.0-prime`); у каждой модели
  один провайдер, выбирать не из чего [S1].
- **Цены**: «₽/с» — `unitParam: duration`; «за ролик» — tier с `duration` в условиях; «за запрос» — Veo. Минимальные
  тесты посчитаны скриптом [S47]. Прямые цены вендоров — в долларах, с датой; «курс polza» 117,992 ₽/$ выведен из
  совпадающих плоских тарифов (0,08 $ × 117,992 = 9,43936 ₽ у H3 Max) и не является курсом ЦБ.
- **Метки**: `[документация]` — официальный документ вендора/polza; `[мнение вендора]` — заявление без методики;
  `[исследование]` — арена или статья с методикой; `[не проверено]` — только генерацией в фазе 5.
- **Коды задач** — таксономия базы (`VID-HERO-LOOP`, `VID-CINEMAGRAPH`, `VID-I2V-PRODUCT`, `VID-ABSTRACT`, `VID-CAMERA`,
  `VID-CHARACTER`, `VID-LONG`, `VID-V2V`, `VID-ALPHA`, `VID-SCROLL`, `VID-UPSCALE`); разбор по задачам —
  `03-capabilities-by-task.md`.

## 2. Сводная таблица 21 видео-модели polza (2026-09-23)

«FLF» — первый + последний кадр; «мин. тест» — самый дешёвый ролик без звука [S47]; fps — по документации вендора
или замеру образцов [S48].

| id в polza | Модель (вендор) | В polza с | Режимы через polza | FLF через polza | Референсы (карт./видео) | Длит., с | Разрешения | fps | Звук по умолч. | Мин. тест, ₽ | ₽/с |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `google/veo3` | Veo 3.1 Quality (Google) | 2026-02-20 | t2v, i2v, FLF, extend, upscale 1080p/4K | да (2 картинки) | — | 8 (фикс.) | 720p (+апскейл) | 24 | всегда вкл. | 187,5 | 23,4 |
| `google/veo3_fast` | Veo 3.1 Fast (Google) | 2026-02-20 | t2v, i2v, FLF, референсы, extend, upscale | да | ≤3 / — | 8 | 720p (+апскейл) | 24 | всегда вкл. | 45 | 5,6 |
| `gemini-omni-video` | Gemini Omni Flash (Google) | 2026-06-08 | t2v, i2v-референсы, v2v | нет полей (теги в промте — ?) | ≤7 / ≤1 | 4/6/8/10 | 720p, 1080p↑, 4k↑ | 24 | вкл. | 35 | 8,75 |
| `kling/v3` | Kling 3.0 (Kuaishou) | 2026-02-20 | t2v, i2v, FLF | да (images 0–2) | — | 3–15 | std 720p / pro 1080p / 4K | 24? | выкл. | 30 | 10 |
| `kling/v2.6` | Kling 2.6 (Kuaishou) | 2026-02-20 | t2v, i2v | нет (1 картинка) | — | 5/10 | 720p? | 24? | выкл. | 42 | 8,4 |
| `kling/v3-motion-control` | Kling 3.0 Motion Control | 2026-03-12 | картинка + видео движения | — | 1 / 1 | ≤10 (по картинке), ≤30 (по видео) | 720p/1080p | — | — | 70 (5 с) | 14 |
| `kling/v2.6-motion-control` | Kling 2.6 Motion Control | 2026-02-20 | то же | — | 1 / 1 | то же | 720p/1080p | — | — | 41,25 (5 с) | 8,25 |
| `bytedance/seedance-1.5-pro` | Seedance 1.5 Pro (ByteDance; у BytePlus Retired) | 2026-02-20 | t2v, i2v, `fixed_lens` | вероятно (0–2 картинки) | — | 4/8/12 | 480p/720p/1080p | 24 | выкл. | **5,25** | 1,31 |
| `bytedance/seedance-2` | Seedance 2.0 (ByteDance) | 2026-04-15 | t2v, i2v/референсы | не гарантирован | ≤5 / ≤1 | 4–15 | 480p/720p/1080p | 24 | **вкл.** | 51,3 | 12,8 |
| `bytedance/seedance-2-fast` | Seedance 2.0 Fast | 2026-04-15 | то же | не гарантирован | ≤5 / ≤1 | 4–15 | 480p/720p | 24 | **вкл.** | 41,85 | 10,5 |
| `bytedance/seedance-2-mini` | Seedance 2.0 Mini | 2026-07-01 | то же | не гарантирован | ≤9 / ≤3 | 4–15 | 480p/720p | 24 | **вкл.** | 10,26 | 2,57 |
| `bytedance/seedance-2-5` | Seedance 2.5 | 2026-08-25 | то же, до 30 с | не гарантирован | ≤30 / ≤10 | 4–30 | 480p/720p | 24 | **вкл.** | 75,6 | 18,9 |
| `wan/2.5` | Wan 2.5 (Alibaba) | 2026-02-20 | t2v, i2v, `negative_prompt` | нет | — | 5/10 | 720p/1080p | 30 | ? | 45 | 9 |
| `wan/2.6` | Wan 2.6 (Alibaba) | 2026-02-20 | t2v, i2v, `multi_shots` | нет | — | 5/10/15 | 720p/1080p | 30 | ? | 52,5 | 10,5 |
| `alibaba/wan-3.0` | Wan 3.0 (Alibaba) | 2026-08-25 | t2v, i2v | нет (images ≤1) | — | 2–30 | 480p/720p/1080p | 30 | выкл. | 47,2 (2 с) | 23,6 |
| `alibaba/wan-3.0-prime` | Wan 3.0 Prime (Alibaba) | 2026-08-27 | t2v, i2v | нет | — | 2–30 | 480p/720p/1080p | 30 | выкл. | 66,1 (2 с) | 33,0 |
| `alibaba/happyhorse-1.0` | HappyHorse 1.0 (Alibaba-ATH) | 2026-06-24 | t2v, i2v | нет | — | 3–15 | 720p/1080p | ? | ? | 60 (3 с) | 20,0 |
| `alibaba/happyhorse-1.1` | HappyHorse 1.1 (Alibaba-ATH) | 2026-06-24 | t2v, i2v | нет | — | 3–15 | 720p/1080p | ? | ? | 45,2 (3 с) | 15,1 |
| `minimax/hailuo-3-max` | MiniMax H3 Max (MiniMax + fal) | 2026-09-02 | t2v, i2v, FLF | да (≤2) | — | 5–15 | 480p/768p | 24 | вкл.? | 47,2 (5 с) | 9,44 |
| `grok-imagine-video-1-5` | Grok Imagine Video 1.5 (xAI) | 2026-08-24 | t2v, i2v, референсы | нет | ≤7 / — | 1–15 | 480p/720p | ? | вкл.? | **1,62** (1 с) | 1,62 |
| `topaz/video-upscale` | Topaz Video Upscale | 2026-02-23 | апскейл ×1/×2/×4 | — | — / 1 | = входу | ×2/×4 | = входу | — | 30 (5 с ×2) | 6 / 10,5 |

Источники строк: каталог [S1], гайды polza [S2], KIE [S3], вендоры [S5]–[S27]; fps: Google [S5][S6], BytePlus [S19],
Alibaba [S21], MiniMax [S25]; «?» — вендор не публикует, проверить ffprobe в фазе 5.

## 3. Карточки моделей polza

### 3.1 Veo 3.1 Quality и Fast — `google/veo3`, `google/veo3_fast`

**Идентификаторы.** polza: `google/veo3` (Quality), `google/veo3_fast` (Fast); в cURL-примере гайда — короткие `veo3` /
`veo3_fast` [S2]; провайдер `mie` = KIE, эндпоинт KIE `POST /api/v1/veo/generate`, модели `veo3`, `veo3_fast`, `veo3_lite`
[S3]. Вендор: Google DeepMind; Gemini API `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview` («Latest update
January 2026»), `veo-3.1-lite-generate-preview` (март 2026; в polza нет); Veo 3 / 3 Fast — Deprecated [S5]; Veo 3.1 GA на
Vertex AI с 16.10.2025 [S4].

**Режимы через polza.** `generationType`: `TEXT_2_VIDEO` · `FIRST_AND_LAST_FRAMES_2_VIDEO` (1 картинка — «The generated
video will unfold around this image», 2 картинки — первый и последний кадр) · `REFERENCE_2_VIDEO` (1–3 картинки, только
Fast, только 8 с) [S3]; если не указан — определяется по наличию `images` [S2]. Операции: `extend` (45 ₽; параметры
`prompt` ≤16000, `seeds`, `watermark`, `model` fast|quality), `upscale_1080p` (10 ₽, синхронно), `upscale_4k` (90 ₽,
асинхронно, у KIE «~5–10 minutes») [S1][S3]. «Videos generated in 1080P cannot be extended» [S3].

**Длительность, fps, разрешение.** В polza длительность и разрешение не задаются → по умолчаниям KIE 8 с, 720p
`[не проверено]` [S3]; у Google 4/6/8 с, 720p (по умолч.)/1080p/4k, **24 fps**, 1080p и 4k — только 8 с, extension — только
720p [S5]. Соотношения: `16:9` (по умолч.), `9:16`, `Auto` («center-cropped based on whether your uploaded image is closer to
16:9 or 9:16») [S2][S3].

**Звук.** «Always on» у всех Veo 3.x [S5]; KIE: «All videos ship with background audio by default» [S3] — для фона
вырезать дорожку при кодировании (`-an`).

**Камера и петля.** Параметра камеры и петли нет; неподвижность — прозой («static shot», «The camera remains static as…»)
[S8]; петля — FLF с одной картинкой в обоих слотах `[не проверено]`. Google показывает FLF как «seamless transitions» между
разными кадрами [S4].

**Выход.** MP4 (URL `tempfile.aiquickdraw.com` у KIE, затем копия в хранилище polza на 7 дней) [S2][S3]; у Google видео
хранятся 2 дня [S5]. Водяные знаки: **SynthID** во всех видео [S4][S5]; параметр polza `watermark` — видимый текст
≤50 символов, по умолчанию пустой [S2].

**Цена.** polza: Quality **187,5 ₽/запрос** (≈23,4 ₽/с при 8 с), Fast **45 ₽** (≈5,6 ₽/с) [S1][S47]. Google Gemini API:
Standard $0,40/с (720p/1080p), $0,60 (4k); Fast $0,10 (720p), $0,12 (1080p), $0,30 (4k); Lite $0,05/$0,08 [S9] → polza ≈ 0,5
прайса Google. Время: «Min: 11 seconds; Max: 6 minutes (during peak hours)» [S5].

**Диалект промта** (официальные гайды [S4][S5][S7][S8]):
- Формула Cloud Blog: **[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]**; «Cinematography… the
  most powerful tool».
- Для i2v — только движение: «Prompt for motion only… Re-describe the character, the background, or the lighting…
  confuse the model»; героя называть общо («the subject») [S7].
- Движение камеры — самый надёжный способ оживить кадр: «Camera Motion… the simplest and most reliable way to add
  dynamism» [S7]; словарь: static shot, pan, tilt, dolly, truck, pedestal, zoom, crane, aerial, handheld, whip pan, arc [S8].
- Один короткий ролик — одна сцена («Focus short videos on a single scene») [S7]; многошотовость — таймкодами
  `[00:00-00:02] …` [S4].
- Негатив: в Gemini API и polza поля нет; прозой — описывать отсутствие («a desolate landscape with no buildings or
  roads») [S4]; поле `negativePrompt` есть у Vertex и Runway-обёртки (перечень «wall, frame», без «no») [S8][S29].
- Кавычки: Cloud Blog советует кавычки для реплик [S4], Vertex — «avoid quotation marks» (иначе текст в кадре) [S7] →
  для фонов без речи — без кавычек `[спорно]`.
- `enableTranslation` в polza по умолчанию `true` (перевод на английский; у KIE ошибка «Only English prompts are supported»)
  [S2][S3] → пиши промт сразу по-английски и ставь `"enableTranslation": "false"`, чтобы перевод не исказил термины камеры
  `[не проверено]`.

```json
// google/veo3_fast · polza 2026-09-23 · петля по одинаковым кадрам · [не проверено]
{"model": "google/veo3_fast",
 "input": {"prompt": "Static shot. Slow drifting morning fog over the lake surface, gentle ripples, soft diffuse light. The camera remains completely still. Single continuous shot.",
           "generationType": "FIRST_AND_LAST_FRAMES_2_VIDEO",
           "images": [{"type": "url", "data": "https://…/frame-A.png"}, {"type": "url", "data": "https://…/frame-A.png"}],
           "aspect_ratio": "16:9", "enableTranslation": "false"},
 "async": true}
```

**Практика с двумя кадрами** (Veo 3.1 / Fast внутри Adobe Firefly Generate Video: 720p и 1080p по одной цене, 24 fps,
4–8 с; Fast в 5 раз дешевле Quality по кредитам) [V:OA4xB5EY02g]: при первом + последнем кадре перечислять движение
**всех** элементов сцены («There is a lake and the clouds are moving…»), иначе движется только событие, а фон «not
lively» [30:43, 32:46]; даже при одинаковом ракурсе кадров модель добавила лёгкий наклон — дописывать «The camera remains
completely still» [33:47]; ключевой объект должен быть в кадре от модели картинок — без последнего кадра видео-модель
рисует его «cartoonish» [37:53]; длительность — по размаху движения (8 с — пролёт, 4 с — короткое действие) [08:06]
`[практика, одиночные генерации]`. Петля с одинаковыми кадрами в ролике не показана.

**Сильные / слабые (VID-*)**: `VID-CAMERA` (словарь камеры в гайдах), `VID-LONG` (extend до 148 с у Google; в polza
шагами по 45 ₽), `VID-I2V-PRODUCT` (референсы у Fast); слабее по физике движения: V-PC 0,519 против 0,840 у Seedance 2.0
в AV-Phys Bench [S43]; арены — второй эшелон (AA T2V без звука 1213, Fast 1207; LMArena I2V 1398/1385) [S40][S41].
**Дефекты** (по бенчмаркам): физика и кросс-модальная согласованность [S43]; «weaker on audio» (вендор-конкурент [S20]).
**Тесты фазы 5**: FLF [A,A] на Fast (45 ₽) + `upscale_1080p` (10 ₽) — шов, «живость», fps/кодек после апскейла.

### 3.2 Gemini Omni Video — `gemini-omni-video`

**Идентификаторы.** polza: `gemini-omni-video` (без префикса), провайдер `mie`; KIE-модель `gemini-omni-video`
(отдельно у KIE есть `google/gemini-omni-flash-1-1` с `first_frame_url`/`last_frame_url` — в polza нет) [S1][S3]. Вендор:
Google, Gemini API `gemini-omni-1.1-flash` (Interactions API) [S6]. **Хронология**: анонс Omni Flash 1.0 — Google I/O
19.05.2026 [V:5T0yRNmNRi4]; `gemini-omni-flash-preview` в API — 30.06.2026 (3–10 с, 720p); GA `gemini-omni-1.1-flash` —
27.08.2026 (продление, **интерполяция первый + последний кадр** задачей `image_to_video` до 2 картинок, `resolution`
360p–4k с апскейлом 1080p/4K); **preview снимается 30.09.2026** [S54]. Какую версию (1.0/preview или 1.1) отдаёт polza —
неизвестно; у Runway `gemini_omni_flash` (1.0) — «only supports a first frame», у `gemini_omni_flash_1.1` — first + last
[S29]. Если KIE работает через preview-эндпоинт, после 30.09.2026 модель в polza может смениться или сломаться `[спорно]`.

**Режимы через polza.** t2v; `images` ≤7 — «референсные изображения» (у KIE — «reference images for characters, scenes,
styles, or storyboard guidance»); `videos` ≤1 (v2v-правка, отрезок ≤10 с из файла ≤30 с, ≤100 МБ; при видео `duration`
игнорируется); `audio_ids`, `character_ids`; квота `images + 2·videos + character_ids ≤ 7` [S1][S3]. У Google картинка
«Depending on your prompt, the model will decide how to use the image»; роль задаётся тегами `<FIRST_FRAME>`,
`<LAST_FRAME>`, `<IMAGE_REF_N>` или `video_config.task` [S6].

**Длительность, разрешение.** 4/6/8/10 с (обязательный параметр); `720p` (по умолч.), `1080p`, `4k` — у Google 1080p и 4k
помечены «(upscaled)», есть ещё 360p [S6]; 16:9 или 9:16; 24 fps («12 frames at 24fps») [S6].

**Петля.** Документирована вендором: «`[# Sources <FIRST_FRAME>@Image1 <LAST_FRAME>@Image1]` will use the first image as
both the first frame and the last frame, creating a video that loops» + фраза «Use this image as the first frame and the
last frame.» [S6]. Пройдут ли теги через polza/KIE — `[не проверено]`.

**Мульти-шот по умолчанию.** «By default Omni Flash will try to create a video with a few different shots» → для фона:
«In a single continuous shot / No scene cuts» [S6].

**Звук.** Генерируется по умолчанию; управлять прозой («No dialogue», «No extra sound effects») [S6].

**Цена.** polza за ролик: 720p/1080p — 4 с 35 ₽, 6 с 45 ₽, 8 с 50 ₽, 10 с 60 ₽; 4k — 70/75/82/95 ₽; с видео на входе 70 ₽
(4k 115 ₽) [S1]; **1080p по цене 720p**. Прямая: ≈$0,10/с (AA $6/мин, Runway 10 кредитов/с) [S29][S40].

**Водяные знаки.** SynthID во всех видео [S6]; C2PA-манифест в файле найден нашим замером (атом `uuid`) и теряется при
любом ffmpeg [S48]; вендор: C2PA «in all of our content», «SynthID persists across edits… and if people make modifications
in post» [V:5T0yRNmNRi4 38:58] `[мнение вендора]`.

**Скорость и правка (со слов авторов модели).** Генерация «60 seconds plus, sometimes 90» [V:5T0yRNmNRi4 09:15]; правка
надёжна на 2–4 хода, дальше следование инструкции падает; недоопределённая правка меняет больше, чем просили [10:15];
для поворота субъекта важны ракурсы референсов, а не их число («only a front photo… might look a different person»)
[07:10] `[мнение вендора]`. Через polza каждый ход правки — новый вызов с `videos` (70 ₽).

**Диалект** [S6]: простые правки («Make this video anime», «Keep everything else the same»); таймкоды «[0-3s] …»; негатив
только прозой («Do not do X»; параметров negative/temperature нет); текст в кадре «will render in a way that is correct and
readable» [мнение вендора]; мета-промты («Consider micro-detail, expression and timing…»).

```text
// gemini-omni-video · polza 2026-09-23 · петля тегами Google · [не проверено]
[# Sources <FIRST_FRAME>@Image1 <LAST_FRAME>@Image1] In a single continuous shot, no scene cuts: steam rises slowly from the cup, soft window light flickers on the table. The camera is completely still. No dialogue. No music. Use this image as the first frame and the last frame.
```

**Сильные**: лидер арен (AA T2V со звуком 1233, I2V без звука 1369; LMArena T2V 1513–1516) [S40][S41]; `VID-V2V`
(правка по инструкции), `VID-LONG` (extension до 40 с у Google). **Слабые**: только 16:9/9:16; нативно 720p; мульти-шот
по умолчанию. **Тест фазы 5**: 1 ролик 4 с 720p с тегами петли (35 ₽).

### 3.3 Kling 3.0 — `kling/v3`

**Идентификаторы.** polza `kling/v3`, провайдер `mie`; KIE `kling-3.0/video` [S3]; Kling API `kling-v3`
(`/image-to-video/kling-3.0`, легаси `/v1/videos/image2video`) [S10][S11]. Вендор: Kuaishou; релиз Kling 3.0 и 3.0 Omni —
**06.02.2026** [S13].

**Режимы через polza.** t2v; i2v; **FLF** — `images` 0–2: «Start/end frame (single-shot) или start frame (multi-shot)»
[S1]. Мульти-шот (`multi_prompt`, до 5–6 планов) и элементы (`kling_elements`, ≤3) у KIE/Kling есть, в каталоге polza —
нет; при этом каталог требует `sound: true` при `multi_shots` [S1][S3].

**Длительность, разрешение.** 3–15 с (обязательный); `mode` `std` = **1280×720**, `pro` = **1920×1080**, `4K` = 3840×2160
[S3]; `aspect_ratio` 16:9, 9:16, **1:1 (по умолчанию в polza)**, «Игнорируется при наличии start frame» [S1].
Картинки: jpg/png, ≥300 px, пропорции 1:2,5…2,5:1 [S10]. «last-frame-only video generation is not supported» [S10].

**Камера.** Параметра `camera_control` у 3.0 нет (был у v1.x) [S11]; камера — прозой; в гайде вендора: «one continuous
long take without any cuts», «The camera remains fixed on the word "KLING"», «The camera orbits the perfume bottle in slow
motion», привязка к секундам «At the 4th second…» [S13]. Исторически сильна в камере: VBench-2.0 Camera Motion у Kling 1.6
61,73 % против 27–34 % у Sora/HunyuanVideo/CogVideoX [S42] (старая версия).

**Петля.** Пример API вендора передаёт **один и тот же URL** в `first_frame` и `last_frame` [S10] — одинаковые кадры
допустимы; качество шва и «живость» — `[не проверено]`.

**Звук.** `sound` по умолчанию `false` [S1][S2]; у вендора `audio: native|off` (по умолч. off) [S10].

**Цена.** polza ₽/с: std 10 (со звуком 14), pro 12 (18), 4K 45 [S1]; снижено с 18.03.2026 (std 15→10) [S2 changelog].
Прямая (AA): без звука 720p $0,168/с, 1080p $0,224/с [S40]; кредиты Kling: 1080p 8 кр/с, 720p 6 кр/с без звука [S13].
Время (AA, fal): 720p ≈74 с, 1080p ≈95 с на 5 с ролик [S40].

**Водяной знак.** `watermark_info.enabled` по умолчанию false — «Whether to also generate a watermarked result»; свой
знак не поддерживается [S10]. Результаты у Kling чистятся через 30 дней [S10].

**Диалект** [S10][S13]: промт ≤2500 (API до 3072); «The prompt can include positive and negative descriptions» — отдельного
негатива нет (легаси `negative_prompt` рекомендует «supplement negative prompt via negative sentences within positive
prompts») [S11]; мульти-шот — «shot n, m, words;»; текст на картинке сохраняется («preserves textual details from original
images… logos») [мнение вендора] — полезно для `VID-I2V-PRODUCT`.

```json
// kling/v3 · polza 2026-09-23 · FLF одной картинкой · [не проверено]
{"model": "kling/v3",
 "input": {"prompt": "One continuous shot without any cuts. The camera stays fixed. Soft wind moves the tall grass and thin clouds drift slowly across the sky; the light stays constant.",
           "images": [{"type": "url", "data": "https://…/frame-A.png"}, {"type": "url", "data": "https://…/frame-A.png"}],
           "duration": "5", "mode": "std", "sound": "false", "aspect_ratio": "16:9"},
 "async": true}
```

**Практика** (туториал на канале Kling) [V:WmC1nqz10Qk]: конечный кадр, сделанный правкой исходника в редакторе картинок,
слегка сдвигает цвет — **подгонять цвет конечного кадра к начальному до FLF** [06:19]; что не названо в промте, то стоит
(второстепенный персонаж «waiting… for the last 3 hours») [05:17]; слова качества («cinematic, 4K, masterpiece») не
работают — жанр, сцена, субъект, действие, камера, звук [00:00] `[практика]`; нативный звук добавляет музыку даже при
негативе (комментарии) → `sound: "false"`.

**Сильные**: `VID-I2V-PRODUCT` (текст/логотип — заявление вендора), `VID-CAMERA`; SeedVideoBench вендора-конкурента: Kling 3.0
«the most balanced overall», motion 3,10 (выше Veo 3.1 2,73) [S20]. **Слабые**: арены — середина (AA T2V со звуком 1089–1095,
LMArena I2V `kling-v3-pro` 1354) [S40][S41]; V-PC 0,716 у Kling 3.0 Omni [S43]. **Тест**: FLF [A,A] std 5 с (50 ₽).

### 3.4 Kling 2.6 — `kling/v2.6`

polza: t2v/i2v, `images` ≤1 (без конечного кадра), `duration` 5|10, `sound`, `aspect_ratio` 1:1/16:9/9:16 (игнорируется
при картинке); цена за ролик: 5 с 42 ₽, 10 с 82,5 ₽ (со звуком 82,5/165) [S1]. У вендора FLF есть, но «only 1080p» и
native audio «only 1080p» [S11]; через polza/KIE — только первый кадр [S3]. AA: T2V без звука 1196 (Pro), I2V без звука
1265 [S40]. **Роль в базе**: запасной вариант Kling 3.0 для i2v; дешевле за ролик не выходит (8,4 ₽/с против 10 ₽/с у v3 std).

### 3.5 Kling 3.0 и 2.6 Motion Control — `kling/v3-motion-control`, `kling/v2.6-motion-control`

Перенос движения из видео на персонажа с картинки: `images` ровно 1, `videos` ровно 1, `mode` 720p|1080p,
`character_orientation` image (≤10 с) | video (≤30 с); промт необязателен (≤2500) [S1][S2]. Требования KIE: картинка
>340 px, пропорции 2:5…5:2, «голова, плечи, торс» в кадре; видео 3–30 с, ≤100 МБ; у KIE есть `background_source`
(input_video|input_image), в polza нет [S3]. Цена: v3 720p 14 ₽/с, 1080p 19 ₽/с (с 18.03.2026; было 8/14); v2.6 8,25 /
13,5 ₽/с [S1][S2]. **Для сайтов**: `VID-CHARACTER` (маскот повторяет движение из референса) — узкая ниша; для фонов не
нужна.

### 3.6 Seedance 1.5 Pro — `bytedance/seedance-1.5-pro`

**Идентификаторы.** polza `bytedance/seedance-1.5-pro` (`mie`); KIE `bytedance/seedance-1.5-pro` [S3]; BytePlus
`seedance-1-5-pro-251215` (сборка 15.12.2025) — **в Model list помечен «Retired», рекомендованная замена
`dreamina-seedance-2-0-mini-260615`** [S19]; в Doubao — `doubao-seedance-1-5-pro-251215` [S14].

**Режимы через polza.** t2v; i2v `images` 0–2; у BytePlus для 1.5 Pro заявлены «Image-to-video — First and last frames» и
«First frame» [S19], у KIE — `input_urls` 0–2 без описания ролей [S3] → вторая картинка = последний кадр — вероятно,
`[не проверено]`. **`fixed_lens`** — «Статичная камера без движения» (по умолч. false) [S1]; KIE: «Seedance adds dynamic
camera movement. Enable this feature to lock the camera for stable, static shots» [S3]; у BytePlus — `camera_fixed`
(легаси-флаг в тексте `--cf` / `--camerafixed`) [S14][S15].

**Длительность, разрешение.** polza 4/8/12 с (у KIE 4–12); 480p/720p/1080p; 1:1, 21:9, 4:3, 3:4, 16:9, 9:16; **24 fps**
[S1][S19]. **Звук** выключен по умолчанию; включение удваивает цену [S1][S18].

**Цена.** polza за ролик без звука: 480p 4/8/12 с — **5,25 / 10,5 / 14,25 ₽**; 720p — 10,5 / 21 / 31,5; 1080p — 22,5 / 45 /
67,5 [S1]. BytePlus 5 с без звука: 480p $0,06, 720p $0,13, 1080p $0,29; Draft 480p $0,04 [S18] → polza ≈0,9 прайса [S47].

**Диалект** [S14]: формула «**Subject + Movement + Environment + Camera movement + Aesthetic + Sound**»; камера —
«**Starting frame composition + Shot movement + Shot movement amplitude + Ending frame composition**»; словарь:
dolly-in/out, pan, track, follow, rise, fall, whirl, rotate, surround, zoom; комбинации (Hitchcock = dolly + zoom; bullet time
= замедление + облёт); «Use degree adverbs effectively»; при включённом звуке «automatically generates background music».
Смена планов управляется словами «The shot cuts to…» — для фона такие обороты не писать.

```json
// bytedance/seedance-1.5-pro · polza 2026-09-23 · синемаграф: камера заблокирована · [не проверено]
{"model": "bytedance/seedance-1.5-pro",
 "input": {"prompt": "Steam rises slowly from the coffee cup and the curtain sways gently in the breeze; everything else in the room stays still. Soft morning light.",
           "images": [{"type": "url", "data": "https://…/room.png"}],
           "fixed_lens": "true", "resolution": "480p", "duration": "4", "aspect_ratio": "16:9", "generate_audio": "false"},
 "async": true}
```

**Сильные**: единственный `fixed_lens` → `VID-CINEMAGRAPH`; самый дешёвый перебор (5,25 ₽). **Слабые**: арены — якорь 1000
у AA (T2V/I2V со звуком), 1176/1256 без звука; LMArena 1256/1307 [S40][S41]; SeedVideoBench motion 2,39, usability motion
46,9 % [S20] — движение слабее Seedance 2.0 и Kling 3.0. **Риск**: снят у BytePlus → может исчезнуть из KIE/polza.
**Тесты**: `fixed_lens` true/false на одной картинке (2 × 5,25 ₽); FLF [A,A] 480p 4 с (5,25 ₽).

### 3.7 Seedance 2.0 / 2.0 Fast / 2.0 Mini — `bytedance/seedance-2`, `bytedance/seedance-2-fast`, `bytedance/seedance-2-mini`

**Идентификаторы.** BytePlus: `dreamina-seedance-2-0-260128`, `dreamina-seedance-2-0-fast-260128`,
`dreamina-seedance-2-0-mini-260615` [S16]; релиз 2.0 в Китае — начало февраля 2026 [S20]; polza добавил 2 и 2 Fast
15.04.2026, Mini — 01.07.2026 [S1].

**Режимы у вендора.** t2v; i2v (первый кадр); **i2v первый + последний кадр (роли `first_frame`/`last_frame`)**; omni
reference (картинки 0–9, видео 0–3, аудио 0–3); edit video; extend video (вперёд/назад; **сшивка 2–3 клипов с генерацией
переходов**); `return_last_frame`; **`camera_fixed`** есть в API [S15][S16]. «Image-to-Video (First Frame), Image-to-Video
(First & Last Frames), and Multimodal Reference-to-Video… are three mutually exclusive scenarios» [S3][S16].

**Через polza.** Только `images` («Референсные изображения»: 2 и Fast ≤5, Mini ≤9), `videos` (2 и Fast ≤1, Mini ≤3),
`generate_audio` (**по умолчанию true**), `resolution`, `duration` 4–15 (по умолчанию **15**!), `aspect_ratio` [S1]. Нет
`camera_fixed`, `return_last_frame`, ролей кадров, `seed`. Попадают ли `images` в `reference_image_urls` или в
`first_frame_url` — неизвестно → строгий FLF и даже «первый кадр = картинка» `[не проверено]`; вендор: «If you need to
strictly ensure that the first and last frames are consistent… always use image-to-video (first and last frame)» [S16].

**Разрешения, fps, кодеки.** 2.0: 480p/720p/1080p (8 бит) и **4K (10 бит, H.265/HEVC)** — у BytePlus; polza — до 1080p;
Fast и Mini — 480p/720p; **24 fps**; 4–15 с; mp4 [S16][S19]. Нативно модель генерирует **480p и 720p** («native output
resolutions of 480p and 720p») [S20] — 1080p/4K выше натива. Таблица пикселей: 480p 16:9 = 854×480 (у 2.0 в Runway-обёртке —
864×496), 720p 16:9 = 1280×720, 21:9 720p = 1470×630 [S17][S29].

**Практическое правило вендора.** FAQ «Video frames contain abrupt jumps»: в i2v и FLF кадры растягиваются/сжимаются,
если разрешение входной картинки не совпадает с выходом → **кадрировать вход точно под пиксели выхода** или
`ratio: adaptive` [S16].

**Цена.** polza ₽/с (без видео на входе / с видео): 2.0 480p 12,825/15,39, 720p 27,675/33,75, 1080p 68,85/83,7; Fast 480p
10,4625, 720p 22,275; **Mini 480p 2,565/3,24, 720p 5,535/6,75** [S1]. BytePlus (прайс, 5 с 16:9): 2.0 480p $0,07/с, 720p
$0,15, 1080p $0,37, 4K $0,78; Fast $0,06/$0,12; Mini $0,04/$0,08 (скидки −25 %/−60 % до 07.10.2026) [S18]. polza дороже
прайса на 2.0/Fast (≈1,55×), дешевле на Mini (≈0,55×) [S47].

**Диалект** [S16][S17]: ссылки на ассеты «Image n», «Video n», «Audio n» (номер по порядку в массиве; по asset ID нельзя);
формулы omni reference, edit («Add… appearance timing + position», «emphasize the elements that remain unchanged»),
extend («Extend "Video n" forward/backward…», «Track completion: Video 1 + transition + Video 2»); скилл `/sd2-pe`.
Реальные лица в референсах запрещены (есть библиотека «digital characters») [S16].

**Сильные**: физика движения — лучший из трёх коммерческих в AV-Phys Bench (V-PC 0,840) [S43]; арены — верхушка (AA T2V со
звуком 1210, I2V 1174; без звука 1259/1336; LMArena 1479/1475) [S40][S41]; `VID-LONG` (extend, сшивка клипов). **Слабые**:
через polza — нет контроля роли картинки и камеры; звук включён по умолчанию. **Тесты**: Mini 480p 4 с с `images` [A] и
[A,B] — какая роль у картинок (2 × 10,26 ₽); «сшивка» петли через `videos` [клип] + промт «Extend Video 1… end on its first
frame» на Mini (≈16 ₽) `[не проверено]`.

### 3.8 Seedance 2.5 — `bytedance/seedance-2-5`

BytePlus `dreamina-seedance-2-5-260628` [S17]; polza с 25.08.2026 [S1]. До **30 с**; до 50 референсов (30 картинок + 10
видео + 10 аудио; в polza — `images` ≤30, `videos` ≤10, суммарно ≤30 с); 11 языков; разрешения 480p/720p (8 бит) и
**1080p (10 бит, H.265/HEVC)**; `output_format` mp4 | **mov (H.264 + yuv444p + PCM)**; **Draft mode** (`draft: true` →
480p черновик по цене 480p, финал по `draft_task.id` только 1080p, «Reuse key parameters… to generate a consistent final
video»); FLF требует `ratio: adaptive` (выход в пропорциях первого кадра) [S17]. **Официальный пример FLF вендора — одна
и та же картинка в `first_frame` и `last_frame`**: «A strawberry sandwich cookie slowly completes one full rotation while the
camera moves smoothly around it and keeps the product centered» — петля-оборот продукта [S17] (шов не измерен; см. опыт 02).

**Через polza.** `images`/`videos` как референсы (роли не задаются), `generate_audio` (по умолч. **true**), 480p/720p
(«1080p у Seedance 2.5 нет» — в описании каталога; у KIE и BytePlus 1080p есть — противоречие), duration 4–30 или −1 (по
длине видео-референса), `aspect_ratio` с `auto` («передаётся в KIE как adaptive») [S1][S3]. Цена polza: 480p **18,9 ₽/с**
(с видео 22,95), 720p 42,525 (51,3) [S1]; BytePlus 5 с: 480p $0,103/с, 720p $0,231, 1080p $0,569 [S18] → polza ≈1,56×.
Промт [S17]: «subject + action/event + scene and environment + visual style + camera movement/shot cuts + sound»;
() музыка, <> звуковые эффекты, {} реплики, 【】 субтитры; `@Image 1`, `@Video 1`; скилл `/sd25-pe`. Хранение: URL видео
**24 ч**, ≤100 скачиваний [S17]. **Арены**: только LMArena — T2V 1474, I2V 1477 (≈ Seedance 2.0) [S41]; у AA нет.
**Роль**: `VID-LONG` (30 с за проход), `VID-I2V-PRODUCT` (оборот продукта по одной картинке — у вендора). **Тест**:
480p 4 с FLF-проверка через `images` [A] (75,6 ₽) — только если №3.7 покажет, что `images` = первый кадр.

### 3.9 Wan 2.5 и Wan 2.6 — `wan/2.5`, `wan/2.6`

**Wan 2.5** (`wan2.5-t2v-preview`/`i2v-preview` у Alibaba; 480p/720p/1080p, 5/10 с, звук, 30 fps [S21]): в polza
prompt ≤800, `aspect_ratio` 16:9/9:16/1:1, 720p/1080p, 5/10 с, `images` ≤1 (первый кадр), `seed`, **`negative_prompt` ≤500**
(единственный негатив-параметр среди видео polza), `enable_prompt_expansion` (по умолч. false) [S1][S2]. Пример KIE:
негатив «blurry, flicker, camera shake, distorted face, low quality» [S3]. Цена за ролик: 720p 5 с 45 ₽, 10 с 90; 1080p
75/150 [S1]. AA: T2V без звука 1160, I2V 1243; LMArena 1245/1321 [S40][S41].

**Wan 2.6** (декабрь 2025; `wan2.6-t2v`/`i2v`, 720P/1080P, 2–15 с, «Multi-shot narrative, audio-video synchronization»,
**30 fps, MP4 H.264** [S21]): в polza prompt ≤5000, 720p/1080p, 5/10/15 с, `images` ≤1, **`multi_shots`** («single continuous
shot or multiple shots with transitions» — для фона false) [S1][S3]; **нет `aspect_ratio`** (выход по картинке/умолчанию)
[S1]. Цена: 720p 5 с 52,5 ₽, 10 с 105, 15 с 157,13; 1080p 78,38/157,13/236,25 [S1]. AA: T2V без звука 1197, I2V 1219;
LMArena 1327/1310 [S40][S41]. **Роль**: устаревшие поколения; оставить Wan 2.5 как единственную модель с явным
`negative_prompt` (например, «flicker, camera shake») для `VID-ABSTRACT` — `[не проверено]`.

### 3.10 Wan 3.0 и Wan 3.0 Prime — `alibaba/wan-3.0`, `alibaba/wan-3.0-prime`

**Вендор.** Alibaba, публичная бета 06.08.2026, GA 24.08.2026, модель `wan3.0-video`; до 30 с за проход; входы — текст,
картинки, аудио, видео и **документы** (doc/xls/ppt/pdf/txt/key/pages/numbers/md, 1 файл ≤100 МБ/≤50 стр., или веб-ссылка);
480P/720P/1080P; правка видео; smart duration; цена **$0,05/с 480P, $0,10/с 720P, $0,20/с 1080P** [S22]. Ограничения от
вендора: «audio texture and on-screen text rendering accuracy» ещё улучшаются [S22]. У KIE: `first_frame_url` +
`last_frame_url` («first-and-last-frame-to-video»), `reference_image_urls` ≤10 (Image1…), видео ≤5, аудио ≤5, `audio` по
умолч. **true**, seed; Prime — «high-speed model» [S3]; у Runway `wan3`/`wan3_prime` — first/last или референсы, ratio
`auto_480p/720p/1080p` для кадров [S29].

**Через polza.** Провайдер `Alibaba` (Wan 3.0) и `openrouter` (Prime); `images` ≤**1** (подпись «first/last frame», но
второй кадр не передать), 2–30 с (по умолч. 2), 480p/720p/1080p, 5 соотношений (без 21:9), `seed`, `generate_audio` (по
умолч. **false**) [S1]. Цена **плоская**: 23,5984 ₽/с (= $0,20 × 117,992) и Prime 33,03776 ₽/с (= $0,28) при любом
разрешении [S1][S47] → тестировать на минимальной длительности (2 с = 47,2 ₽).

**Арены**: AA T2V без звука **№1 1336**, I2V без звука 1361, T2V со звуком 1229, Video Editing №1 1190; LMArena T2V 1476,
I2V 1480 [S40][S41]. Выход Wan 3.0 у Alibaba — **MP4, 30 fps**, 1080P по умолчанию, звук у вендора по умолчанию
**включён** (`audio=false`), URL живёт 24 ч [S49]; у всего семейства Wan — 30 fps, H.264 [S21]. Первый/последний кадр у
вендора строгий: «achieving pixel-level reproduction of the reference image»; FLF и референсы взаимоисключающие; пример
вендора для FLF — «[One continuous take, slow aesthetic camera movement, no cuts, 15-second long shot…]» с тайм-сегментами
`[0-3s: …]` [S49]. **Роль**: сильный кандидат `VID-LONG`, `VID-ABSTRACT`, `VID-V2V` вне polza; через polza — дорогой i2v
без конечного кадра.

### 3.11 HappyHorse 1.0 и 1.1 — `alibaba/happyhorse-1.0`, `alibaba/happyhorse-1.1`

Alibaba-ATH; 1.0 — апрель 2026, 1.1 — июнь 2026 [S40]. polza (провайдер Alibaba): `images` ≤1 (первый кадр; у KIE
«Exactly one image is required» для i2v), 720p/1080p (у KIE по умолч. 1080p), 3–15 с, 7 соотношений (включая 21:9 и 9:21),
`seed`; плоско 1.0 **19,99 ₽/с**, 1.1 **15,08 ₽/с** [S1][S3]. Прямые: AA $13,20/мин (1.0) и $9,90/мин (1.1) для 1080p;
Runway `happyhorse_1_0` 15/30 кредитов/с (720p/1080p) [S29][S40]. Арены: AA T2V без звука 1287 (1.0) и 1272 (1.1) — выше
Seedance 2.0 (1259); I2V без звука 1293/1312; LMArena `happyhorse-1.0` 1427/1442 [S40][S41]. Время (AA): HappyHorse-1.1 T2V
на Alibaba Cloud ≈112 с [S40]. У KIE есть r2v и video-edit (в polza нет). **Роль**: i2v-кандидат среднего ценового класса;
FLF нет.

### 3.12 MiniMax H3 Max — `minimax/hailuo-3-max`

**Что это.** `MiniMax-H3-Max` — «jointly released by MiniMax and fal.ai; post-trained by fal.ai on MiniMax H3 and optimized
for high-speed generation… 480P and 768P» [S24]; флагман `MiniMax-H3` (768P/2K, 4–15 с, открытые веса) — отдельная модель,
в polza его нет [S24][S25]. Релиз H3 ≈31.07.2026, H3 Max в AA — август 2026 [S23][S40].

**Через polza** (провайдер `openrouter`): `images` ≤2 «Опорные кадры для image-to-video (first/last frame)», 480p/768p
(по умолч. 768p), 5–15 с (по умолч. 5), соотношения 21:9 (по умолч.), 16:9, 4:3, 1:1, 3:4, 9:16; нет seed, нет параметра
звука, нет `prompt_expansion_mode` [S1]. У вендора: i2v — первый, последний (у MiniMax — «only last frame» допустим; у Runway
«A last frame requires a first frame») или оба; при i2v `ratio` всегда adaptive; `extra.prompt_expansion_mode` (по умолч.
balanced; для воспроизводимости — disabled) [S24][S29]. Выход H3: **24 FPS**, стерео 32 кГц [S25].

**Камера.** «add camera motion instructions (e.g., [pan], [zoom], [static]) directly after key descriptions» [S24] —
скобочные команды.

**Цена.** polza **9,43936 ₽/с плоско** (= $0,08, прайс 768P) → 480p переплата 1,6× [S1][S47]; MiniMax: H3-Max 480P $0,05/с,
768P $0,08/с; H3 768P $0,08, 2K $0,13; Regeneration 768P→2K $0,05/с [S24].

**Арены**: AA I2V со звуком **№1 1195**, T2V со звуком 1227 (при $2,40/мин — самое дешёвое в топ-5) [S40]. **Роль**:
главный кандидат дешёвых петель по FLF [A,A] и `VID-I2V-PRODUCT` в polza; «accurate text and brand rendering»
[мнение вендора, S23]. **Тест**: FLF [A,A] 480p 5 с (47,2 ₽).

```text
// minimax/hailuo-3-max · polza 2026-09-23 · камера скобками · [не проверено]
Morning mist drifts slowly across a pine forest valley, sunbeams shift gently through the trees [static]. Single continuous shot, no cuts, calm natural motion.
```

### 3.13 Grok Imagine Video 1.5 — `grok-imagine-video-1-5`

xAI: превью `grok-imagine-video-1.5-preview` 03.06.2026, GA `grok-imagine-video-1.5` 16.06.2026; «Video 1.5 Fast» в
приложениях — «6-second, 720p videos in about 25 seconds» [мнение вендора] [S26]. У xAI: 1–15 с, 480p (по умолч.)/720p/1080p,
t2v делается как t2i → i2v внутри; **`last_frame`** (первый+последний или только последний) и **`keyframes` ≤4 на сетке
1/3 с**; `generate_audio` по умолч. true; i2v берёт пропорции картинки, заданный `aspect_ratio` **растягивает** картинку
[S27]. Цена xAI: 480p $0,08/с, 720p $0,14/с, 1080p $0,25/с [S27].

**Через polza** (`mie`, имя «Preview»): prompt ≤4096, `images` ≤7 («Входные изображения (image-to-video)»; у KIE — «Only
one is supported when the resolution is 1080p», aspect «invalid if it is a single image»), 480p/720p, 1–15 с (по умолч. 8),
aspect 1:1/16:9/9:16/3:2/2:3/auto; нет `last_frame`, `keyframes`, `generate_audio` [S1][S3]. Цена **1,62 ₽/с (480p), 3,04 ₽/с
(720p)** — ≈0,17 прайса xAI [S47] `[спорно]`. Арены: AA I2V со звуком 1099, без звука 1329; LMArena I2V 1456 (720p) [S40][S41].
**Роль**: дешёвый перебор движения (5 с 480p = 8,1 ₽) и эскизы i2v; для петли через polza — нет конечного кадра.
Промт (xAI): «Slow cinematic push-in as embers drift across the battlefield…» — камера + среда в одном предложении [S26].

### 3.14 Topaz Video Upscale — `topaz/video-upscale`

polza/KIE: `videos` ровно 1 (mp4/mov/mkv, ≤50 МБ), `upscale_factor` 1|2|4 (по умолч. 2); цена ×1/×2 **6 ₽/с**, ×4 **10,5 ₽/с**
[S1][S3]. Выбора модели Topaz (Proteus, Starlight, Astra…) и интерполяции кадров нет; у Topaz API интерполяция Apollo/
Chronos/Aion отдельными моделями (1–6 кредитов/GP) [S28]. **Роль**: `VID-UPSCALE` «чёрным ящиком»; альтернативы — Veo
`upscale_1080p` (10 ₽ за ролик, только Veo), MiniMax Regeneration 2K (вне polza), локально Real-ESRGAN/RIFE (агент I).

## 4. Модели и возможности вне polza

### 4.1 Luma Ray 3.2 — единственная нативная петля

**API.** Luma Agents API: `POST https://agents.lumalabs.ai/v1/generations`, `model: "ray-3.2"`, `type: "video"` (также
`video_edit`, `video_reframe`); prompt 1–6000; соотношения 9:16, 3:4, 1:1, 4:3, 16:9, 21:9; `video.resolution` **360p
(draft)** / 540p / 720p (по умолч.) / 1080p; `video.duration` 5s | 10s; **24 fps** (сетка keyframe_indexes «duration ×
24fps») [S34]. Легаси Dream Machine API: `ray-2`, `ray-flash-2`, `loop=True`, `keyframes.frame0/frame1`, камера строками из
`/generations/camera_motion/list` («camera orbit left»), `concepts` [S33].

**Петля.** `video.loop` — «When true, generates a seamlessly looping video»; только `type: video`, **5 с**; несовместим с
10s, `hdr`, **`end_frame`**, `keyframes`; со `start_frame` — допустим [S34]. Это единственный документированный
параметр петли среди видео-API на 23.09.2026 `[документация]`; качество шва — `[не проверено]`.

**Прочее.** `start_frame`/`end_frame`; multi-keyframe (1–64 якоря с индексами кадров); extend вперёд/назад по
`generation_id`; HDR MP4 и EXR (ACES2065-1) [S34]; «Modify Video V2… Up to 20 seconds, all at 1080p», Reframe [S35].
**Цены** (SDR, за 5 с): 360p **$0,06**, 540p $0,15, 720p $0,30, 1080p $1,20; 10 с: $0,18/$0,45/$0,90/$3,60; HDR ×2,
HDR+EXR ×3 [S34]. «a 5s/720p generation typically completes in well under two minutes» [мнение вендора, S34].
**Арены**: Ray 3 (сентябрь 2025) — AA T2V без звука 1185, I2V 1215; LMArena 1206/1226; Ray 3.2 в аренах нет [S40][S41].
**Для базы**: первый кандидат `VID-HERO-LOOP` вне polza (дёшево: 360p-черновик $0,06, финал 720p $0,30) — доступ из
России и ключ — вопрос агента P.

### 4.2 Runway Dev — Gen-4.5, Aleph 2 и агрегатор чужих моделей

**Что это в 2026.** API Runway Dev отдаёт свои модели (`gen4.5`, `gen4_turbo`, `aleph2`, `act_two`) и чужие (`veo3.1`,
`veo3.1_fast`, `seedance2`, `seedance2_5`, `wan3`, `wan3_prime`, `hailuo3` = MiniMax H3 2K, `h3_max`, `happyhorse_1_0`,
`grok_imagine_1_5`, `gemini_omni_flash`, `gemini_omni_flash_1.1`) через единый `POST /v1/image_to_video`,
`/v1/text_to_video`, `/v1/video_to_video`; кредит = $0,01; `X-Runway-Version: 2024-11-06` обязателен [S29].
Нормализованные поля `promptImage[].position` (`first`/`last`) показывают, где у моделей есть конечный кадр (сводка —
в `03-capabilities-by-task.md` §2.2).

**Gen-4.5.** prompt ≤1000; t2v только 1280:720 / 720:1280; i2v — 1280:720, 720:1280, 1104:832, 960:960, 832:1104, 1584:672;
2–10 с; **только первый кадр** (`position: first`); параметра звука нет; `outputFormat`: `mp4` (H.264), `prores` (4444 по
умолч.), `png_sequence`, `sdr_rec709_10bit` (HEVC Main 10), **`hdr10`/`hlg`** (HEVC Main 10 BT.2020), EXR/ACEScg; 12
кредитов/с ($0,12/с) + доплата за профессиональные форматы (5–40 кредитов/с) [S29]. **ProRes 4444: «generated content
contains no transparency — the alpha channel… is present but fully opaque»** [S29] → нативной альфы нет. AA: T2V без звука
1214, I2V 1263 («No API available» — устарело: API есть); LMArena 1225 [S40][S41].

**Aleph 2.** v2v-правка ≤30 с; `keyframes` ≤5 (картинки-ориентиры по времени, окно `range`); **`targetAspectRatio`** —
outpaint видео под 16:9/4:3/3:2/1:1/2:3/3:4/9:16/21:9 («Letterboxes the input video and keyframes before generation»);
28 кредитов/с (мин. 56); AA Video Editing 1011 [S29][S40].

**Промтинг (официальные гайды Runway [S30][S31][S32])**: простота, «focus on describing the motion», **только
утвердительные формулировки** («❌ No camera movement… ✅ Locked camera. The camera remains still.»), «the subject»,
структура «The camera [motion] as the subject [action]. [Additional descriptions]», таймкоды «[00:01] X occurs», длинные ряды —
последний кадр как вход следующего ролика. FAQ: против нежелательных склеек — увеличить длительность и добавить
«Continuous, seamless shot»; против движения камеры — «The locked-off camera remains perfectly still.», «**The camera must
start and end on the exact same frame to create a perfect loop.**», «Minimal subject motion only.» + стабилизация; подсказки
движения в исходной картинке (смаз, пыль) мешают статике — убрать их до генерации [S31]; статика труднее всего на
«establishing or wide landscape shots» [S32]. «Inputs are auto-cropped to the target aspect ratio», «Moderated generations
cost the same as successful ones» [S29].

### 4.3 Прямые API вендоров: что есть сверх polza

| Вендор / модель | Сверх polza (вендор) | Источник |
|---|---|---|
| Google Veo 3.1 (Gemini API/Vertex) | `durationSeconds` 4/6/8; `resolution` 720p/1080p/4k; `negativePrompt` (Vertex); `referenceImages` ≤3 `asset`; extension +7 с до 20 раз (≤148 с, 720p); `seed` («slightly improves» детерминизм); Veo 3.1 Lite ($0,05/с); хранение 2 дня | [S5][S8][S9] |
| Google Gemini Omni Flash 1.1 | first + last frame, теги ролей, 360p, extension до 40 с, правка по диалогу (`previous_interaction_id`), `delivery: uri` | [S6] |
| Kling 3.0 (Kling API) | `multi_shot` (**по умолчанию true** в новом API), промт-синтаксис «shot n, m, words;», `element` ≤3, `audio: native`, 4k, `watermark_info`, 30 дней хранения; Kling 3.0 Turbo (без FLF); Capability Map | [S10][S11][S12] |
| Seedance 2.0 / 2.5 (BytePlus) | роли `first_frame`/`last_frame`, `camera_fixed`, `return_last_frame`, `seed`, `watermark` (по умолч. false), edit/extend/сшивка до 3 клипов, 4K (2.0), mov yuv444p (2.5), **Draft** (2.5 и 1.5 Pro) | [S15][S16][S17] |
| Wan 3.0 (Model Studio, KIE) | first + last frame, документы и веб-ссылки на входе, референсы ≤10, аудио ≤5, `audio` по умолч. true | [S3][S22] |
| MiniMax H3 (API) | флагман 2K, last-frame-only, `prompt_expansion_mode`, H3-Context-IR (улучшатель промта), **Regeneration 768P→2K $0,05/с** | [S24] |
| xAI Grok Imagine 1.5 | `last_frame`, `keyframes` ≤4 (1/3 с), `generate_audio: false`, 1080p, edit, extend | [S27] |
| Topaz (API) | выбор модели апскейла, интерполяция Apollo/Chronos/Aion | [S28] |
| Luma Ray 3.2 | `loop`, 360p draft, HDR/EXR, 64 keyframes, reframe | [S34] |

### 4.4 OpenAI Sora 2 — снимается с API 24.09.2026

«The Sora 2 video generation models and Videos API are deprecated and will shut down on September 24, 2026» — Videos API,
`sora-2`, `sora-2-pro`, снапшоты `sora-2-2025-10-06`, `sora-2-2025-12-08`, `sora-2-pro-2025-10-06`; рекомендованной замены
нет; уведомление от 24.03.2026 [S36]. Приложение Sora закрыто ещё 26.04.2026 (OpenAI Help Center, по дайджесту
[V:KLDdXOw6jIc 55:55]). Справочно: 16/20 с, `sora-2-pro` 1080p ($0,70/с), картинка = первый кадр, лица людей на входе
запрещены [S36]. Арены: Sora 2 Pro AA T2V без звука 1179, LMArena 1368 [S40][S41]. **Статус — снята; в рекомендации и
маршрутизацию не включать.**

### 4.5 Открытые веса (обзор; запуск — вне волны 1, GPU-сервер только под транскрипцию)

| Модель | Лицензия | Характеристики | Память | Арены | Источник |
|---|---|---|---|---|---|
| MiniMax H3 (FL2VA, Ref2VA) | MiniMax H3 Community License | 24 FPS, стерео 32 кГц, 768p (2K — только API), первый/последний/оба кадра; 33B + Qwen3-VL-32B | пример SGLang на 4 GPU | AA T2V без звука 1302 (лучшие открытые) | [S25][S40] |
| LTX-2.5 (Lightricks, 22B) | своя, gated на HF | 24 fps, 1024×1536 по умолч., 4K, `KeyframeInterpolationPipeline`, `RetakePipeline`, HDR/EXR; ~66 ГиБ весов, fp8 | fp8 + offload | AA T2V без звука 1217 (Fast) | [S39][S40] |
| Wan2.2 (Alibaba) | Apache-2.0 | TI2V-5B 720P@24fps (1280×704) на 24 ГБ; A14B 480P/720P (80 ГБ на одной GPU); FLF — в Wan2.1-FLF2V-14B | 24 ГБ (5B) | AA T2V без звука 1116 (A14B), 950 (5B) | [S37][S40] |
| HunyuanVideo-1.5 (Tencent, 8,3B) | Tencent Hunyuan Community | 480p/720p + SR до 1080p, 121 кадр, step-distilled 8–12 шагов | ≥14 ГБ с offload | AA T2V без звука 1020, LMArena 1169 | [S38][S40][S41] |

Для видеокарта 24 ГБ реалистичны Wan2.2-TI2V-5B, HunyuanVideo-1.5 и LTX-2.5 в fp8 `[не проверено]` — тема агента P и
«после сигнала» по GPU. Исследовательский метод петель Loopy работает на Wan 2.1/2.2 и HunyuanVideo 1.5 [S44].

## 5. Диалекты промтов: сводка правил по моделям

Общее для всех (консенсус гайдов Google [S7][S8], Runway [S30][S31], BytePlus [S14][S17], xAI [S26][S27], Kling [S13]):
для i2v описывать **только движение** (камера → субъект → среда), героя называть общо, одна сцена на короткий ролик,
язык кино для камеры, звук — отдельными фразами (для фонов — прямо запрещать речь и музыку, где звук нельзя выключить).

| Модель | Структура промта (официальная) | Камера / статика | Негатив | Особенности |
|---|---|---|---|---|
| Veo 3.1 | [Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance] [S4] | «static shot», «The camera remains static as…» [S8] | нет в polza/Gemini API; прозой «with no buildings» [S4] | таймкоды `[00:00-00:02]`; кавычки — `[спорно]` [S4][S7]; `enableTranslation: false` для англ. промта |
| Gemini Omni | свободный текст + теги `<FIRST_FRAME>`, `<LAST_FRAME>`, `<IMAGE_REF_N>` [S6] | «In a single continuous shot / No scene cuts» | «No dialogue», «Do not do X» | правки: «Keep everything else the same»; таймкоды `[0-3s]` |
| Kling 3.0 | сцена + движение + камера + время («At the 4th second…») [S13] | «one continuous long take without any cuts», «The camera remains fixed on…» | в тексте промта [S10][S11] | мульти-шот «shot n, m, words;» (только прямой API/KIE) |
| Seedance 1.5 Pro | Subject + Movement + Environment + Camera + Aesthetic + Sound [S14] | `fixed_lens: true`; «Starting frame + Shot movement + amplitude + Ending frame» | нет | «Use degree adverbs effectively»; «The shot cuts to…» = монтаж |
| Seedance 2.x / 2.5 | subject + action/event + scene + visual style + camera/shot cuts + sound [S17] | прозой; у вендора `camera_fixed` [S15] | нет | `@Image 1`/`Image n`; () музыка, <> SFX, {} речь, 【】 субтитры |
| Wan 2.5 / 2.6 / 3.0 | пять измерений (сущность, движение, эстетика, стиль, звук); для i2v — «focus on motion and camera movements» [S50] | прозой; орбита «under 45 degrees» (шире — искажения пространства) [S50] | **`negative_prompt` ≤500 только у `wan/2.5`** | «Generate single shot.» для одного плана; `multi_shots: false` у 2.6; у 3.0 `Image 1`, `Video 1`, скилл `/wan3-pe` [S49] |
| MiniMax H3 / H3 Max | контекст + цель; H3-Context-IR строит «integrated_multimodal_description» [S24][S25] | скобки `[pan]`, `[zoom]`, `[static]` [S24] | нет | `prompt_expansion_mode: disabled` для воспроизводимости (вне polza) |
| Grok Imagine 1.5 | камера + движение + атмосфера одним предложением [S26] | прозой | нет | `<IMAGE_1>` для референсов; aspect_ratio растягивает картинку [S27] |
| Runway Gen-4.5 | «The camera [motion] as the subject [action]. [Additional]» [S31] | «Locked camera. The camera remains still.» | **негатив прозой запрещён** («opposite results») [S30] | «Continuous, seamless shot» против склеек |
| Luma Ray | язык + строки из `camera_motion/list` [S33] | «camera orbit left» и т.п. | нет | `loop: true` |

```text
// шаблон фона-петли для i2v · любая модель без параметра камеры · [не проверено]
The camera remains completely still for the whole shot. [ОДНО медленное непрерывное движение среды: mist drifts slowly left to right / water ripples gently / light shifts softly]. Single continuous shot, no cuts. The final moment matches the opening frame. No people, no text, no dialogue, no music.
```

## 6. Выходные файлы: что отдают модели и что с этим делать

### 6.1 Форматы по документации и по замеру публичных образцов

Замер — опыт 02 [S48]: 28 официальных примеров вендоров, ffprobe 7.1.5 и метрики кадров; своих генераций не было.
Демо-файлы документации часто перекодированы (Apple Core Media, DaVinci Resolve, libx264 на 0,75 Мбит/с), поэтому
«родной» выход API подтверждается только на своих роликах в фазе 5.

| Модель | По документации | Замер образца (опыт 02) | fps | Звук | МБ на 5 с | Хранение результата |
|---|---|---|---|---|---|---|
| Veo 3.1 (polza/KIE) | MP4; 720p, 1080p/4K — операциями апскейла [S3][S5] | не измерялся (сырых образцов нет) | 24 [S5] | всегда | ? | polza 7 дн., KIE — `tempfile.aiquickdraw.com`, Google 2 дня |
| Gemini Omni | 720p натив, 1080p/4K — апскейл [S6] | **H.264 High, yuv420p, 1280×720** (и в «1080p»-примере), `moov` в начале | 24 | AAC 48 кГц | 1,5–2,8 | polza 7 дн. |
| Kling 3.0 | MP4; std 1280×720, pro 1920×1080, 4K 3840×2160 (KIE) [S3][S10] | веб-выходы Kling: **H.264 Main, 1928×1072 / 1924×1076**, 12,6 Мбит/с | 24 | AAC 44,1 кГц | 7,9 | Kling 30 дн. [S10] |
| Seedance 1.5 Pro | MP4 [S19] | не измерялся | 24 [S19] | выкл. | ? | polza 7 дн. |
| Seedance 2.0 / Fast / Mini | MP4; 480p–1080p 8 бит, **4K — HEVC 10 бит** [S16] | уроки: H.264 1280×720, 1,1–5,5 Мбит/с; «4K»-пример — H.264 25 fps после DaVinci (не доказательство) | 24 | вкл. | 0,7–3,5 | BytePlus URL 24 ч; polza 7 дн. |
| Seedance 2.5 | MP4: 480p/720p 8 бит, **1080p HEVC 10 бит**; MOV: **H.264 yuv444p + PCM** [S17] | FLF 720p 1:1: **H.264 High 960×960**, 3,6 Мбит/с; финал 1080p из пары Draft→Final: **H.264 Constrained Baseline 8 бит**, 28 Мбит/с | 24 | вкл. | 2,3 (720p) / 17,6 (1080p) | BytePlus URL 24 ч, ≤100 скачиваний [S17] |
| Wan 2.5 / 2.6 | MP4, H.264 [S21] | демо пережаты (0,75–0,79 Мбит/с); старый пример FLF — 16 fps без звука | 30 | ? | ≈0,5 (демо) | polza 7 дн. |
| Wan 3.0 / Prime | MP4, 1080P по умолч. [S49] | не измерялся | 30 [S49] | у вендора вкл., в polza выкл. | ? | Alibaba URL 24 ч [S49] |
| MiniMax H3 / H3 Max | 24 FPS, стерео 32 кГц [S25] | «прямой выход API» H3: **H.264 High 1344×768** (768P), 1,88 Мбит/с; 2K — 2560×1440, 7,07 Мбит/с; **`moov` в конце** | 24 | AAC 32 кГц | 1,18 / 4,42 | MiniMax задачи 7 дн. [S24] |
| Grok Imagine 1.5 | MP4 по временному URL [S27] | не измерялся (примеры xAI закрыты) | ? | вкл. у xAI | ? | xAI — временный URL |
| HappyHorse 1.0 / 1.1 | не опубликовано | не измерялся | ? | ? | ? | polza 7 дн. |
| Topaz Video Upscale | fps = входу, ×1/×2/×4 [S3] | — | = вход | = вход | — | polza 7 дн. |
| Luma Ray 3.2 | SDR MP4, HDR MP4, EXR ACES2065-1 [S34] | маркетинговые ролики не замерялись | 24 | — | — | временный URL |
| Runway Gen-4.5 | mp4 H.264, ProRes 4444 (альфа непрозрачна), PNG, HEVC Main 10 SDR/HDR10/HLG, EXR [S29] | — | ? | нет | — | временный URL |

### 6.2 Что перекодировать для сайта (правила)

1. **Перекодировать всегда**, даже если исходник уже H.264: профиль сайта — 3d `05` §3.15
   (`../../3d/01-web-3d-landscape/05-blender-deliverables-map.md`): H.264 `libx264 -crf 23 -preset slow
   -movflags +faststart` + AV1/VP9 первым `<source>`, постер — первый кадр; фон — без звука (`-an`). Детали конвейера —
   `../09-video-pipeline/` (агент I) `[практика; проверено 3d A/06]`. **Поправка X 24.09.2026 (I, J, L):** постер — из
   декодированного кадра 0 **финального** файла (PNG ffmpeg → Pillow → AVIF, `../09-video-pipeline/03-encoding-and-budgets.md`
   §5, `../10-web-integration/02-video-delivery.md` §2.2); полные теги BT.709 и `-map_metadata 0 -movflags
   use_metadata_tags+faststart` одной строкой; CRF — по `motion_keep` ≥ 0,75 (H.264 18–20, AV1 24–28; `10/02` §6.1).
2. **HEVC 10 бит, yuv444p и PCM в MOV** (Seedance 2.x 4K/1080p, Seedance 2.5 `mov`, Runway `sdr_rec709_10bit`/HDR) на сайт не
   отдавать — перевести в 8 бит `-pix_fmt yuv420p`; HDR (Runway HDR10/HLG, Luma HDR/EXR) — отдельное решение с тонмаппингом
   `[документация]`.
3. **Нестандартные размеры** (Kling 3.0 1928×1072, 1924×1076) — масштабировать или обрезать до чётного стандартного
   размера (`scale=1920:1080:flags=lanczos,setsar=1`) `[проверено: опыт 02, 2 образца]`.
4. **`moov` в конце** (MiniMax H3; и любой remux ffmpeg без флага) — обязательно `-movflags +faststart`, иначе
   видео не начнёт играть до полной загрузки `[проверено: опыт 02]`.
5. **fps не смешивать**: Veo, Omni, Kling, Seedance, MiniMax, Luma, LTX — 24 fps; Wan (2.x API и 3.0) — 30 fps; открытые
   Wan 2.1/2.2 — 16 fps. Склейка роликов разных моделей — через приведение fps (или интерполяцию RIFE у агента I).
6. **Порядок величин после перекодирования** (2-секундные фрагменты без звука, ffmpeg 7.1.5, качество не оценивалось):
   Gemini Omni 720p — x264 CRF 23 (veryfast) ≈0,67 МБ/5 с (исходник 1,6), AV1 CRF 40 (SVT preset 10) ≈0,29 МБ/5 с;
   Seedance 2.5 960×960 с быстрым облётом — x264 ≈2,3 МБ/5 с (как исходник), AV1 ≈1,3 МБ/5 с. Быстрое движение по всему
   кадру (облёт, частицы) стоит в 3–4 раза дороже по весу, чем медленный дрейф — это аргумент за медленные фоны
   `[проверено: опыт 02, 2 ролика]`; подбор CRF по VMAF — агент I.
7. **Скачивать сразу**: polza хранит 7 дней, BytePlus и Alibaba отдают URL на 24 ч, Google — 2 дня [S2][S5][S17][S49].

### 6.3 Шов, склейки и «живость»: что показали образцы

- **Ни один из 28 официальных примеров не замкнут**: отношение «шов / медианный шаг кадра» (seam_ratio) — от 3,4 до 102
  (медиана ≈16). Для приёмки петли предлагаю порог **seam_ratio ≤ 1,5–2** — шов не заметнее обычного шага кадра `[мнение]`.
- **Строгий FLF у прямого API Seedance 2.5**: кадр 0 ↔ заданный first frame — SSIM 0,979 (PSNR 36,8 дБ), последний кадр ↔
  last frame — SSIM 0,959 (PSNR 36,5 дБ), при сильном движении внутри ролика (SSIM соседних кадров 0,56). Значит, при
  одинаковых кадрах стык будет на уровне SSIM ≈0,96–0,98: последний кадр почти дублирует первый → **отрезать последний
  кадр** или смешать 2–4 кадра `[проверено: 1 образец; вывод — мнение]`.
- **Склейки внутри ролика** надёжно ловятся отношением «максимальный скачок / медиана» (cut_ratio): у мульти-шотов 18–84,
  у однопланных роликов 1,4–7 → порог 10 для автопроверки «single continuous shot» (агент K) `[проверено: 28 роликов]`.
- Пример Gemini Omni «keyframe interpolation» (10 с между двумя разными кадрами) — переход, а не петля (seam_ratio 68).

### 6.4 Предсказывает ли дешёвый черновик финал (пара Seedance 2.5 Draft 480p → Final 1080p)

| Сравнение (432×248, серый, 123 кадра) | Значение | Контроль |
|---|---|---|
| SSIM кадров в один и тот же момент, медиана / минимум | **0,649** / 0,573 | со сдвигом 0,5 с — 0,509; с обращённым временем — 0,340 |
| Корреляция кривых «сколько движется» по времени | **0,867** | — |
| Корреляция карт «где движется» (шаг 0,25 с), медиана | 0,405 | — |

Вывод `[проверено: 1 пара]`: финал повторяет раскадровку, композицию и темп движения черновика, но перерисовывает детали.
Черновик годится для выбора движения и камеры; лица, текст, логотип — только по финалу. Предсказывает ли дешёвая **другая**
модель (Grok 480p) дорогую — не проверено (тест №7 фазы 5).

### 6.5 Метки происхождения в файлах

| Образец | Что найдено в файле | После ffmpeg `-c copy` | После перекодирования (x264) | С `-map_metadata 0 -movflags use_metadata_tags` | WebM (AV1) |
|---|---|---|---|---|---|
| Gemini Omni (Google) | C2PA-манифест в атоме `uuid` (JUMBF/CBOR) + упоминание SynthID; SynthID — в пикселях [S6] | C2PA **теряется** | теряется | теряется | теряется |
| Seedance 2.5 (BytePlus) | ключ `AIGC` {Label, ContentProducer, ProduceID} — неявная метка по китайскому стандарту | **теряется** | теряется | **сохраняется** | сохраняется |
| Kling 3.0, MiniMax H3 | `AIGC`; у MiniMax ещё `TC260PG SecurityData` (подпись) | (как у Seedance — не проверялось отдельно) | — | — | — |
| Wan 2.6 (демо) | ничего (демо пережаты) | — | — | — | — |

Сохранять ли метки на сайте, раскрывать ли ИИ-происхождение — решение агента L (`../12-legal-provenance/`); технически
C2PA при веб-кодировании можно только переподписать заново (c2patool и т. п. — `[не проверено]`)
`[проверено: опыт 02, metadata_survival.py]`.

## 7. polza ↔ вендор и гайд ↔ каталог: расхождения

| № | Что | polza (каталог / гайд) | Вендор / KIE | Что делать |
|---|---|---|---|---|
| 1 | Veo: длительность и разрешение | нет параметров; 45 / 187,5 ₽ за запрос | KIE: 4/6/8 с, 720p/1080p/4k, по умолч. 8 с 720p [S3] | считать 8 с 720p; подтвердить ffprobe первого ролика |
| 2 | Veo: длина промта | гайд 2000, каталог 60 000 (extend 2000 ↔ 16 000) [S1][S2] | Gemini API — 1024 токена [S5] | держать промт ≤1000 символов |
| 3 | Veo `upscale_4k` | operations.mdx «синхронная», каталог `async: true` [S1][S2] | KIE ~5–10 мин [S3] | вызывать асинхронно и опрашивать |
| 4 | Veo `extend` | в operations.mdx есть `duration` 3–10 с, в каталоге нет [S1][S2] | Google +7 с за шаг [S5] | длительность не передавать; мерить результат |
| 5 | Veo `enableTranslation` | по умолч. `true` [S1] | KIE: описание «true», схема `false`; «Only English prompts» [S3] | писать по-английски, ставить `false` |
| 6 | Seedance 2 / 2.5: роль `images` | «Референсные изображения» [S1] | у вендора FLF и референсы взаимоисключающие [S16][S17] | тест №5 фазы 5; до него не строить петли на Seedance 2.x через polza |
| 7 | Seedance 2.5: 1080p | «1080p у Seedance 2.5 нет» [S1] | BytePlus и KIE: 1080p есть (HEVC 10 бит) [S3][S17] | через polza — только 480p/720p |
| 8 | Seedance 2: 1080p и `multi_shots` | гайд: 480p/720p и `multi_shots`; каталог: 1080p «по документации KIE», `multi_shots` нет [S1][S2] | — | верить каталогу |
| 9 | Seedance 2 Fast: длина промта | описание «до 1536 символов», `max_length` 20 000 [S1] | — | держать ≤1500 |
| 10 | Seedance 2 Mini: edit/extend/аудио | гайд обещает, каталог не даёт [S1][S2] | у BytePlus есть [S16] | не рассчитывать через polza |
| 11 | Seedance 2.x: длительность по умолчанию | **15 с** (цена ×3–4 от минимума) [S1] | — | всегда передавать `duration` явно |
| 12 | Kling 3: `sound` при `multi_shots` | «обязательно true при multi_shots», параметра `multi_shots` нет [S1] | у Kling API `multi_shot` по умолч. **true** [S10] | промт «one continuous long take»; проверять cut_ratio |
| 13 | Kling 3: `aspect_ratio` | по умолч. **1:1**, игнорируется при стартовом кадре [S1] | — | передавать 16:9 явно; кадр — нужных пропорций |
| 14 | Wan 3.0 / Prime, HappyHorse | «first/last frame» в описании, но `images` ≤1 [S1] | у Wan 3.0 FLF есть [S3][S49] | FLF Wan 3.0 — только вне polza |
| 15 | Wan 3.0: звук | `generate_audio` по умолч. false [S1] | у вендора по умолч. вкл. [S49] | проверить дорожку ffprobe |
| 16 | Wan 3.0: цена | плоско 23,6 ₽/с [S1] | $0,05/$0,10/$0,20 за 480P/720P/1080P [S22] | тестировать на 2 с |
| 17 | Gemini Omni: версия и роли картинок | `images` — «референсные» [S1] | KIE-модель без first/last; 1.1 с FLF — отдельно, в polza нет [S3] | петля только тегами; тест №10 |
| 18 | Grok 1.5: цена | 1,62 ₽/с (480p) [S1] | xAI $0,08/с (≈9,4 ₽) [S27] | сверить выход (разрешение, fps, звук) |
| 19 | MiniMax H3 Max: aspect | по умолч. **21:9** [S1] | у MiniMax при i2v — по картинке [S24] | передавать 16:9 явно для t2v |
| 20 | Kling 2.5 Turbo | гайд есть, модели нет [S2] | — | не использовать |
| 21 | Seedance 1.5 Pro | есть [S1] | у BytePlus Retired, замена — 2.0 Mini [S19] | держать запасной маршрут |

## Частые ошибки

1. **Имена и возможности моделей по памяти** («Veo 3», «Kling 2.1», «Sora 2», «Hailuo 02») вместо свежего каталога — в
   09.2026 актуальны Veo 3.1, Kling 3.0, Seedance 2.x/2.5, Wan 3.0, MiniMax H3; Sora 2 отключается 24.09.2026.
2. **Параметры вендора в запросе polza** (`negativePrompt` для Veo, `camera_fixed`/`return_last_frame` для Seedance 2,
   `multi_prompt` для Kling, `last_frame` для Grok) — их нет в каталоге; сверяй каждое поле с `GET /api/v1/models`.
3. **«Одинаковые first/last = готовая петля»** — шов будет, но движение может угаснуть (Loopy [S44], практика [S45]);
   мерить и шов, и «живость».
4. **`images` у Seedance 2.x через polza считать первым кадром** — это «референсы»; строгий первый кадр не гарантирован.
5. **Не задавать длительность у Seedance 2.x** — по умолчанию 15 с: 480p ролик Seedance 2 стоит 192 ₽ вместо 51 ₽ за 4 с.
6. **Оставлять звук там, где он платный**: Kling 3 std со звуком 14 ₽/с вместо 10; Seedance 1.5 Pro со звуком ×2.
7. **Ждать от Veo в polza 4–6 с или 1080p сразу** — в polza это запрос за 8 с 720p и отдельные операции апскейла.
8. **Экономить на разрешении у плоских тарифов** (Wan 3.0/Prime, MiniMax H3 Max, HappyHorse) — 480p стоит столько же, что
   и старшее разрешение; экономия только длительностью.
9. **Kling 3 без `aspect_ratio`** — получите 1:1.
10. **Негатив «no camera movement» у Runway и в промтах без поля негатива** — «opposite results»; писать «Locked camera.
    The camera remains still.» [S30].
11. **Кавычки в беззвучном фоне Veo/Omni** — модель может нарисовать текст в кадре [S7].
12. **Gemini Omni без «single continuous shot»** — по умолчанию смонтирует несколько планов [S6].
13. **Отдавать выход модели на сайт как есть** — звук, HEVC 10 бит, `moov` в конце, 1928×1072, 12 Мбит/с.
14. **Судить о пригодности для петли по месту в арене** — арены меряют общее предпочтение на обычных промтах.
15. **Сравнивать цены только «за секунду»** — у Seedance 1.5 Pro, Wan 2.x, Kling 2.6, Gemini Omni цена за ролик (tier), у
    Veo — за запрос; считать «ставка × длительность × условия» по опыту 01 [S47].
16. **Картинка для i2v в других пропорциях** — растяжение (Grok), автокроп (Runway, Veo `Auto`), рывки кадров (Seedance).

## Чек-лист

- [ ] Модель есть в свежем каталоге polza (`GET /api/v1/models?type=video`), дата снимка записана.
- [ ] Каждый параметр запроса есть в каталоге этой модели; `duration`, `resolution`, `aspect_ratio`, звук заданы явно.
- [ ] Режим (t2v / i2v / FLF / референсы) реально доступен через polza (§2), а не только у вендора.
- [ ] Входная картинка обрезана точно под пропорции и пиксели выхода.
- [ ] Промт по диалекту модели (§5): для i2v — только движение; фраза камеры; «single continuous shot»; без кавычек;
      утвердительно.
- [ ] Цена посчитана до вызова (ставка × длительность × условия) и укладывается в лимит.
- [ ] Результат скачан сразу; ffprobe: кодек, fps, размер кадра, звук, длительность совпадают с ожиданием.
- [ ] Для петли: шов (seam_ratio ≤ 1,5–2), «живость», отсутствие склеек (cut_ratio < 10); последний кадр-дубль отрезан.
- [ ] Перекодировано по `../10-web-integration/02-video-delivery.md` §2.1 (`-an`, полные теги BT.709, `-map_metadata 0 -movflags
  use_metadata_tags+faststart`, AV1 10 бит + H.264, CRF по `motion_keep` ≥ 0,75), постер — кадр 0 финального файла
  [поправка X 24.09.2026: было «по 3d `05` §3.15, 8 бит yuv420p, постер — первый кадр»].
- [ ] Решение по меткам происхождения (C2PA/AIGC) принято по правилам агента L; паспорт генерации записан.

## Открытые вопросы и противоречия

1. **Роль `images` у Seedance 2 / 2 Fast / 2 Mini / 2.5 через polza** — референс или первый/последний кадр? KIE разделяет
   поля, polza — нет. `[спорно]` → тест №5 фазы 5.
2. **Вторая картинка у Seedance 1.5 Pro через polza** — последний кадр? BytePlus заявляет FLF для 1.5 Pro, KIE роли не
   описывает `[не проверено]` → тест №1.
3. **Статичный коллапс при одинаковых кадрах у коммерческих моделей**: вендоры (Seedance 2.5, Kling, Runway, Gemini Omni)
   показывают такие петли, исследование [S44] и практика [S45] фиксируют угасание движения на Wan 2.2/EDEN и «most models»
   (апр. 2026) — замеров по коммерческим моделям нет `[спорно]` → тесты №1–4, №10.
4. **Seedance 2.5 1080p: HEVC 10 бит (документация) или H.264 8 бит** (официальный пример финала 1080p)? Через polza 1080p
   нет — вопрос для прямого API `[спорно]`.
5. **Veo через polza**: действительно ли 8 с и 720p по умолчанию; сколько добавляет `extend` `[не проверено]`.
6. **Gemini Omni в polza**: версия 1.0/preview или 1.1; проходят ли теги `<FIRST_FRAME>`/`<LAST_FRAME>` через KIE; что
   будет с моделью после снятия preview-эндпоинта Google 30.09.2026 [S54] `[не проверено]`.
7. **Grok Imagine 1.5 в polza в ~6 раз дешевле xAI** — та же модель и разрешение? `[спорно]`.
8. **Размер кадра Kling 3.0 через API**: 1920×1080 (KIE) против 1928×1072 в веб-выходах `[спорно]`.
9. **Кавычки в промтах Veo**: Cloud Blog — «для реплик», Vertex — «avoid quotation marks» (иначе текст в кадре) `[спорно,
   внутри Google]`.
10. **Звук Wan 3.0 через polza**: каталог — выкл., вендор — вкл. по умолчанию `[не проверено]`.
11. **fps и кодек HappyHorse, Grok 1.5, Seedance 1.5 Pro** — не опубликованы/не измерены `[не проверено]`.
12. **Переживает ли SynthID перекодирование** в AV1/H.264 — детектора нет; вопрос агенту L.
13. **Сколько проживёт Seedance 1.5 Pro в polza** после снятия у BytePlus — единственный параметр неподвижной камеры.

## Источники

Нумерация общая для трёх файлов папки (`01-…`, `02-…`, `03-…`). Даты — публикации или снятия; все страницы сняты
23.09.2026, копии — в `99-raw/cache/` (имена файлов — по URL).

- [S1] polza.ai — каталог `GET https://polza.ai/api/v1/models?type=video&include_providers=true` (снимок 2026-09-23 08:48;
  `99-raw/cache/polza/2026-09-23/api-v1-models.json`, копия в опыте 01) — [документация].
- [S2] polza.ai — документация (гайды моделей `gaidy/*.mdx`, `operations`, `changelog.mdx`; `99-raw/cache/polza/2026-09-23/docs-repo/`) — [документация].
- [S3] KIE.ai — страницы видео-моделей `docs.kie.ai/market/*` и Veo 3.1 API (`99-raw/cache/kie-video-C2-2026-09-23/`,
  `99-raw/cache/kie-2026-09-23/`) — [документация провайдера `mie`].
- [S4] Google Cloud Blog, K. Davaajav, H. Chinoy, «The ultimate prompting guide for Veo 3.1», 16.10.2025 —
  https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1 — [документация].
- [S5] Gemini API, «Generate videos with Veo 3.1» — https://ai.google.dev/gemini-api/docs/veo — [документация].
- [S6] Gemini API, «Generate and edit videos with Gemini Omni Flash» — https://ai.google.dev/gemini-api/docs/omni — [документация].
- [S7] Google Cloud, «Best practices for generating videos» — https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/best-practice — [документация].
- [S8] Google Cloud, «Video generation prompt guide» — https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide — [документация].
- [S9] Gemini API, «Pricing» — https://ai.google.dev/gemini-api/docs/pricing — [документация].
- [S10] Kling API, «Kling 3.0 & 3.0 Omni — Image to Video» — https://kling.ai/document-api/apiReference/model/imageToVideo — [документация].
- [S11] Kling API, «Kling 2.6» и легаси image2video — https://kling.ai/document-api/api/video/2-6,
  https://kling.ai/document-api/api/video/2-6/image-to-video/legacy — [документация].
- [S12] Kling API, «Video Capability Map» — https://kling.ai/document-api/guides/capability-map/video — [документация].
- [S13] Kling, «Kling VIDEO 3.0 Model User Guide», 06.02.2026 — https://kling.ai/quickstart/klingai-video-3-model-user-guide — [документация / мнение вендора].
- [S14] BytePlus ModelArk, «Seedance-1.5-pro prompt guide» — https://docs.byteplus.com/en/docs/ModelArk/2168087 — [документация].
- [S15] BytePlus ModelArk, «Create a video generation task» (обновл. 22.09.2026) — https://docs.byteplus.com/en/docs/ModelArk/1520757 — [документация].
- [S16] BytePlus ModelArk, «Dreamina Seedance 2.0 series tutorial» (обновл. 08.09.2026) — https://docs.byteplus.com/en/docs/ModelArk/2291680 — [документация].
- [S17] BytePlus ModelArk, «Dreamina Seedance 2.5 tutorial» (обновл. 23.09.2026) — https://docs.byteplus.com/en/docs/ModelArk/2607688 — [документация].
- [S18] BytePlus ModelArk, «Pricing» (обновл. 22.09.2026) — https://docs.byteplus.com/en/docs/ModelArk/1099320 — [документация].
- [S19] BytePlus ModelArk, «Model list» (обновл. 22.09.2026) — https://docs.byteplus.com/en/docs/ModelArk/1330310 — [документация].
- [S20] ByteDance Seed, «Seedance 2.0: Advancing Video Generation for World Complexity», arXiv 2604.14148, апр. 2026 —
  https://arxiv.org/abs/2604.14148 — [мнение вендора с методикой].
- [S21] Alibaba Cloud Model Studio, «Video generation» — https://www.alibabacloud.com/help/en/model-studio/use-video-generation — [документация].
- [S22] Alibaba Cloud Blog, «Wan3.0: 30-Second AI Video Generation from Any Input» (13.08.2026) и «Wan3.0 at General
  Availability…» (27.08.2026) — https://www.alibabacloud.com/blog/wan3-0-30-second-ai-video-generation-from-any-input_603452 — [мнение вендора].
- [S23] MiniMax, «MiniMax H3: An Open Model Breaking the Boundaries Between Tasks and Modalities» — https://www.minimax.io/blog/minimax-h3 — [мнение вендора].
- [S24] MiniMax API Docs, «Video Generation», «Create Video Generation Task», «Pay as You Go» —
  https://platform.minimax.io/docs/guides/video-generation — [документация].
- [S25] MiniMax-AI/MiniMax-H3, README (GitHub, push 15.08.2026) — https://github.com/MiniMax-AI/MiniMax-H3 — [документация].
- [S26] xAI, «Grok Imagine 1.5» (03.06.2026) и «Grok Imagine Video 1.5» (16.06.2026) — https://x.ai/news/grok-imagine-1-5,
  https://x.ai/news/grok-imagine-video-1-5 — [мнение вендора].
- [S27] xAI Docs, «Video generation», «Image to video», «Reference to video», «Pricing» (обновл. 21.09.2026) —
  https://docs.x.ai/developers/model-capabilities/video/generation — [документация].
- [S28] Topaz Labs Developer Docs, «Frame Interpolation» — https://developer.topazlabs.com/video-models/frame-interpolation — [документация].
- [S29] Runway API docs (`api/`, `guides/models/`, `guides/pricing/`, `ai-context.md`) — https://docs.dev.runwayml.com/api/ — [документация].
- [S30] Runway, «Gen-4 Video Prompting Guide» — https://help.runwayml.com/hc/en-us/articles/39789879462419 — [документация].
- [S31] Runway, «Image to Video Prompting Guide» (Gen-4.5) — https://help.runwayml.com/hc/en-us/articles/48324313115155 — [документация].
- [S32] Runway, «Camera Terms, Prompts, & Examples» — https://help.runwayml.com/hc/en-us/articles/47313504791059 — [документация].
- [S33] Luma, Dream Machine API (легаси) «Video Generation» — https://docs.lumalabs.ai/docs/python-video-generation — [документация].
- [S34] Luma Agents API, «Video generation», «Models», «Pricing» — https://docs.agents.lumalabs.ai/guides/videos/generation — [документация].
- [S35] Luma, страница Ray — https://lumalabs.ai/ray — [мнение вендора].
- [S36] OpenAI, «Video generation with Sora», «Deprecations», «Changelog» — https://developers.openai.com/api/docs/guides/video-generation — [документация].
- [S37] Wan-Video/Wan2.2, README (★17 605, Apache-2.0) — https://github.com/Wan-Video/Wan2.2 — [документация].
- [S38] Tencent-Hunyuan/HunyuanVideo-1.5, README — https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5 — [документация].
- [S39] Lightricks/LTX-2, README (LTX-2.5) — https://github.com/Lightricks/LTX-2 — [документация].
- [S40] Artificial Analysis, Video Arena (T2V, I2V, Video Editing; со звуком и без; страница моделей и провайдеров), снято
  23.09.2026 — https://artificialanalysis.ai/video/leaderboard/text-to-video — [исследование].
- [S41] LMArena, Text-to-Video и Image-to-Video Arena (данные на 21.09.2026) — https://lmarena.ai/leaderboard/text-to-video — [исследование].
- [S42] Zheng et al., «VBench-2.0», arXiv 2503.21755v2, 2025 — https://arxiv.org/abs/2503.21755 — [исследование].
- [S43] Cui et al., «Do Joint Audio-Video Generation Models Understand Physics?» (AV-Phys Bench), arXiv 2605.07061, май 2026 —
  https://arxiv.org/abs/2605.07061 — [исследование].
- [S44] Dong et al., «Loopy: Seamless Video Loop Generation via Anchored Looping Shift of Positional Embedding», ACM TOG 45,
  2026, arXiv 2608.23090 — https://arxiv.org/abs/2608.23090 — [исследование].
- [S45] ffmpeg.party, «Seamless AI video loops», апр. 2026 — https://ffmpeg.party/guides/ai-video-loop/ — [практика, единичный].
- [S46] Morphic, «Looping» (глоссарий) — https://morphic.com/ai-glossary/looping — [мнение].
- [S47] Опыт C2/01, «Матрица цен тестовых роликов polza» — `99-raw/experiments/C2/01-polza-video-price-matrix/` — [проверено].
- [S48] Опыт C2/02, «Выходные файлы: ffprobe, FLF, черновик → финал, метки» — `99-raw/experiments/C2/02-vendor-output-ffprobe/` — [проверено].
- [S49] Alibaba Cloud Model Studio, «How to use Wanx wan3.0 video generation model» —
  https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-guide — [документация].
- [S50] Alibaba Cloud Model Studio, «Text-to-video / image-to-video prompt guide | Wan» —
  https://www.alibabacloud.com/help/en/model-studio/text-to-video-prompt — [документация; просмотрен].
- [S51] Luma, «Ray3: User Guide» — https://lumalabs.ai/learning-hub/ray3-user-guide — [мнение вендора].
- [S52] Kling, «Kling AI Prompt Guide», 07.08.2026 — https://kling.ai/blog/kling-ai-prompt-guide — [мнение вендора].
- [S53] Kling, «Kling VIDEO 3.0 Omni Model User Guide», 06.02.2026 — https://kling.ai/quickstart/klingai-video-3-omni-model-user-guide — [документация].
- [S54] Gemini API, «Release notes / Changelog» (записи 30.06.2026 и 27.08.2026: preview и GA Gemini Omni Flash, снятие
  preview 30.09.2026) — https://ai.google.dev/gemini-api/docs/changelog — [документация].

Видео (дайджесты волны 2, агент W3; ссылки вида [V:id мм:сс], файлы — `../91-videos/digests/<id>.md`):
- [V:5T0yRNmNRi4] Google «Release Notes: Introducing Gemini Omni», 19.05.2026 — [мнение вендора].
- [V:KLDdXOw6jIc] AI Engineer World's Fair, «SOTA Generative Media Panel» (Google DeepMind), 30.08.2026 — [мнение вендора].
- [V:OA4xB5EY02g] Adobe Live, «AI Art Direction: From Frames to Motion» (Veo 3.1 в Firefly), 20.08.2026 — [практика].
- [V:WmC1nqz10Qk] Kling AI (T. Simmons), «Cinematic AI Films with Kling 3.0 & 3.0 Omni», 07.04.2026 — [практика / мнение вендора].
- [V:b_PmGocP4rc] AI Engineer World's Fair, M. Bril (Character.ai), «Evaling Video Slop», 25.07.2026 — [практика].
