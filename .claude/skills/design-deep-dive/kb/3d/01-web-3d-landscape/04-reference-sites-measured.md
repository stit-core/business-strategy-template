# Референсы веб-3D 2023–2026 и их замеры

Волна 1 · агент A · 2026-09-23 · измерено 33 сайта с 3D на десктопе (38 прогонов + 13 повторов), 10 — в мобильном
режиме с троттлингом, 18 — парами «обычный / prefers-reduced-motion»; ещё 17 референсов описаны без замера ·
Chromium 153 headless, ANGLE GL на Intel Iris Xe, WebGPU включён; three r186 актуальный (22.09.2026) · инструмент и
сырьё: `99-raw/experiments/A/` (`tools/site_probe.py`, `sites/<slug>/`, `sites_desktop.csv`).

## Выжимка для агента

1. Медианный наградной 3D-сайт 2023–2026 весит **12,6 МБ** на десктопе (IQR 7,3–20,8; n = 33), из них 3D-ассеты — 2,6 МБ (IQR 1,05–9,1), JS — 905 КБ; это в 4–5 раз больше медианной страницы веба (2,6–2,9 МБ, Web Almanac 2025). Для лендинга продукта это **антиориентир**, не норма → §4. [проверено]
2. Для коммерческого лендинга ориентир — нижняя четверть выборки: ≤ 3–7 МБ всего, ≤ 1–2 МБ 3D, первый 3D-кадр не раньше, чем текст стал LCP; примеры, укладывающиеся: Mana Yerba Mate (6,8 МБ, 3D = 0,4 МБ), Stripe (2,8 МБ), cobe (0,2 МБ), Messenger (5,7 МБ) → §4. [проверено]
3. three.js стоит на **27 из 33** сайтов с 3D (82 %), ревизии от r141 до r186, медиана ≈ r169: наградные сайты не обновляют three годами → код агента на r186 не должен копировать API из их бандлов → §5.1. [проверено]
4. WebGPU в продакшене редок: 2 из 33 (Bruno Simon — r183, IVRESS — r182, оба с запасным WebGL2); steven.com, объявленный «WebGPU» в подборке студии, в замере рисует WebGL2 → WebGPU — опция с фолбэком, а не требование → §5.1. [проверено]
5. Главный формат текстур у лидеров — **KTX2** (≈13 из 33, часто 4K атласы по 1–2 МБ), геометрии — **Draco** (GLB с Draco или «голые» `.drc`, ≈15 из 33); собственные форматы (`.buf` у Lusion, `.mdpc` у Shopify) — удел студий с инженерами → агенту: GLB + Meshopt/Draco + KTX2/WebP → §5.2. [проверено]
6. Гауссовы сплаты уже в маркетинге: Oryzo (`.sog`, 3 МБ), World Labs (`.spz` по 1,4 МБ × 12), SuperSplat, playcanvas.com; рисуются **одним draw call** → §5.2. [проверено]
7. Вызовов отрисовки за кадр при прокрутке: медиана **13**, p90 — медиана 33, максимум 274 (Bruno Simon после старта); 3D-лендинг укладывается в 10–80 → бюджет вызовов **при прокрутке** «≤ 100 на десктопе, ≤ 50 на телефоне» реалистичен (в покое — ≤ 60 / 30, `../09-web-runtime/05-performance-a11y-fallbacks.md` §7.2) → §4. [проверено]
8. Прелоадеры и «ворота» (Enter/Begin/Click to start) есть у 13 из 33 наградных сайтов (≈ 40 %); первый 3D-кадр на десктопе — медиана **14 с**, у Lusion 3D-сцена открывается на 32-й секунде → для продуктового лендинга ворота запрещены: контент и CTA должны быть доступны до 3D → §5.3. [проверено]
9. LCP на 3D-сайтах — текст (H1/P/DIV) или картинка, **никогда canvas**; десктопный LCP в выборке — медиана 5,8 с из-за прелоадеров, закрывающих текст (Immersive Garden 31,6 с) → не прячьте H1 под прелоадером → §6 и `02-when-3d-budgets-loading.md` §2. [проверено]
10. Мобильные версии лидеров легче в 1,5–6 раз (Igloo 2,8 против 16,6 МБ, Lusion 9,5 против 16,3), половина ограничивает DPR до **1,5**; Spline рисует в полном DPR 2,625 и даёт TBT 1,9 с при CPU×4 → на телефоне всегда `setPixelRatio(Math.min(devicePixelRatio, 1.5))` и лёгкий набор ассетов → §3. [проверено]
11. Первый 3D-кадр на «медленном 4G + CPU×4» — 4,5–25 с, TBT до 7,1 с (Stripe с «лёгким» градиентом) → на телефоне 3D грузить после интерактивности страницы и без блокировки главного потока → §3. [проверено]
12. **≈13 из 16** проверенных сайтов игнорируют `prefers-reduced-motion`: сцена анимируется так же; уважают Stripe (один кадр и стоп), частично Shopify Editions и Lando Norris → агент обязан выключать фоновые петли при reduce → §6. [проверено]
13. Почти все сайты рисуют каждый кадр даже без движения (draw calls в покое у 25 из 33) → рендер по требованию и остановка вне экрана — дешёвый выигрыш батареи → §6. [проверено]
14. Самые лёгкие приёмы с высокой отдачей: шейдерная лента-градиент (Stripe, 1–6 draw calls), точечный глобус (cobe, 5 КБ), одна банка-GLB в плоской иллюстрации (Mana, 15 КБ glTF + 425 КБ HDR) → §7. [проверено]
15. Тяжёлые «миры» (IVRESS 63 МБ, KPR 46 МБ, Immersive Garden 29 МБ, Primland 27 МБ) — жанр кампаний и студийных витрин; для продуктового сайта неприменимы → §7. [проверено]
16. Theatre.js (`@theatre/core`, npm не обновлялся с 05.2024) найден в бандлах 4 сайтов (Active Theory, Primland, Shopify Editions, Hubtown) → живёт в продакшене, но для нового кода агента не выбирать → `03-runtime-landscape.md` §6. [проверено]
17. Замер headless на встроенной графике — ориентир, не бенчмарк: FPS упирается в 60, сеть и кэш не контролировались, INP не измеряется → сравнивайте сайты между собой, а не с устройствами → §1. [проверено]

## 1. Метод и ограничения

- Инструмент — `99-raw/experiments/A/tools/site_probe.py` (дополняет `../../scripts/3d/web_view.py --url`). Причины замены
  на пилоте lusion.co: `web_view.py` снял экраны во время 30-секундного прелоадера, не прокрутил сайт с виртуальным
  скроллом (`window.scrollTo` при `scrollHeight == innerHeight`), записал 0 байт для 13 из 122 ответов (br/zstd без
  `content-length`), отнёс `.buf`-модели и `.ogg` к «other». `site_probe.py` считает переданные байты через
  `request.sizes()`, распознаёт форматы по первым байтам (glTF, KTX2, DRACO, EXR, HDR, PLY, WASM, OggS…), перехватывает
  `getContext`/`transferControlToOffscreen`/`navigator.gpu.requestAdapter`, считает draw calls WebGL и WebGPU
  (`GPURenderPassEncoder.draw*`), крутит колесом мыши, пишет LCP с элементом и TBT до/во время прокрутки. [проверено]
- Условия: Chromium 153 headless (Playwright), ANGLE GL на Intel Iris Xe (Mesa), флаги `--enable-unsafe-webgpu
  --enable-features=Vulkan` (без них `requestAdapter()` возвращает null и WebGPU-сайты уходят на запасной путь);
  десктоп 1440×900 DPR 1; мобильный режим — дескриптор Pixel 7 (412×839 CSS, DPR 2,625, UA Android) + CPU ×4 + 150 мс
  RTT, 1,6 Мбит/с (как пресет Lighthouse). Сценарий: `load` → 8 с ожидания → 2 с простоя → 24 шага колеса → 4 снимка.
- Ограничения: headless с vsync 60 Гц (FPS ≤ 60); встроенная графика ноутбука, не телефон; сеть домашняя, кэш пуст;
  куки-баннеры не закрывались; ворота Messenger и IVRESS нажать не удалось; одна сетевая пауза испортила два прогона
  (перемерены); INP не измеряется (нет взаимодействий), TBT — лабораторный ориентир; «1-й 3D-кадр» — первый кадр rAF с
  ≥ 1 draw call, у сайтов с прелоадером на WebGL это кадр прелоадера.
- Байты — переданные (сжатые) по всем ответам за окно замера, включая аналитику и сторонние скрипты.

## 2. Таблица измеренных сайтов (десктоп)

Колонки: «3D, КБ» — модели (glb/gltf/bin/drc/buf/splat/sog/spz/splinecode) + 3D-текстуры (ktx2/ktx/hdr/exr);
«Draw calls» — медиана за кадр в покое / при прокрутке / 90-й перцентиль при прокрутке; LCP — последний кандидат и тег.

| # | Сайт | Что на экране, приём | Движок | Контекст | Вес, МБ | 3D, КБ | JS, КБ | 1-й 3D-кадр, с | LCP, с (элемент) | TBT, мс | Draw calls: покой / прокрутка мед. / p90 | FPS | Heap, МБ | Форматы и заметки |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | lusion.co | SOTY 2023. 3D-куча пластиковых «крестов» (matcap), видео-плоскость с искажением, WebGL-сетка проектов; прелоадер ≈30 с | three r158 | webgl2 | 16,3 | 2639 | 498 | 2,7 | 2,7 (H1) | 32 | 85 / 17 / 78 | 59,8 | 23 | .buf ×20 (свой формат), matcap.exr 0,59 МБ, аудио .ogg ×16 |
| 2 | oryzo.ai | SOTM 04.2026 (Lusion). Фотореальная пробковая подставка, камера по глубине на прокрутке, «рука» | three r178 (модиф. Lusion) | webgl2 | 16,1 | 7106 | 774 | 7,5 | 17,4 (IMG) | 460 | 38 / 24 / 24 | 59 | 16 | **сплаты .sog** ×2 (3 МБ) + splat_sorter.wasm, .buf ×25, Rive |
| 3 | messenger.abeto.co | Awwwards Developer Site of the Year 2025 (Abeto) [S14]. Low-poly мир-планета, ворота BEGIN (клик не удался) | three r180 | webgl2 | 5,7 | 1053 | 534 | 4,2 | нет | 383 | 25 / 25 / 25 | 60 | 23 | **.drc ×16**, KTX2 ×10 (LUT тоже KTX2), glyph.wasm |
| 4 | igloo.inc | SOTY 2024. Монохромный снежный рельеф, иглу из блоков, разлёт на прокрутке, хроматическая аберрация | three r165 | webgl2 | 16,6 | 13272 | 452 | 3,5 | 2,7 (::before) | 290 | 47 / 48 / 57 | 60 | 286 | .drc ×22, **KTX2 ×49 (12,7 МБ)**, EXR; heap 286 МБ |
| 5 | landonorris.com | SOTY 2025 (OFF+BRAND, Webflow). Портрет + 3D-шлем «полосами», крупная типографика | three r174 | webgl2 | 6,6 | 1774 | 585 | — | 5,8 (DIV) | 17 | 0 / 13 / 23 | 50,4 | 28 | GLB ×3, HDR 1k ×2, Rive ×8 |
| 6 | activetheory.net | Прелоадер из точек 18 с → радужно-хромовый 3D-логотип | свой/не опр. | webgl2 | 8,8 | 1916 | 538 | 18,6 | 10 (DIV) | 126 | 0 / 0 / 27 | 56,7 | 50 | свой движок; KTX2 ×32, Draco; @theatre/core |
| 7 | bruno-simon.com | Портфолио-игра на **WebGPU**: диорама с машинкой, физика | three r183 | webgpu | 7,3 | 1819 | 1223 | 32,9 | нет | 2352 | 267 / 273 / 274 | 60 | 109 | GLB ×23, .ktx ×25, basis+draco, wasm 2,4 МБ |
| 8 | unseen.co | Ворота Enter → пастельная комната с арками и водой, переливчатая сфера | three r143 | webgl,webgl2 | 7,3 | 2879 | 628 | 5 | 5 (P) | 306 | 46 / 46 / 46 | 60 | 50 | GLB ×12, **KTX2 ×14 (запечённый свет комнаты ≈0,9 МБ/шт.)** |
| 9 | hubtown.co.in | SOTD 06.2026 (Unseen). Светящийся куб-монолит над водой, световые трассы, распад на кубы | three r179 | webgl2 | 21,7 | 18046 | 1171 | 33,7 | 20,1 (DIV) | 1403 | 48 / 47 / 78 | 60 | 123 | GLB 12 МБ, KTX2 5,9 МБ, @theatre/core |
| 10 | immersive-g.com | Белые барельефы, 3D-карточки проектов (сундук LV, браслет Cartier) | three r151 | webgl,webgl2 | 28,6 | 18413 | 1090 | 12,2 | 31,6 (DIV) | 723 | 23 / 29 / 33 | 57,9 | 157 | GLB (reliefs 4,6 МБ br), KTX2 ×40; LCP 31,6 с |
| 11 | brand.ivress.co.jp | FWA SOTM 05.2026. **WebGPU** (TSL), тёмный готический интерьер, «Click to start» | three r182 | webgpu | 63,4 | 52652 | 1043 | 104,4 | 26,8 (SPAN) | 3392 | 116 / 116 / 127 | 57,1 | 364 | GLB-сцены 14/10/6 МБ **без сжатия**, EXR ×3; 63 МБ |
| 12 | explore.ownprimland.com | SOTD 02.2026. Интерактивная аэро-карта рельефа (drag/zoom), облака | three r179 | webgl2 | 27 | 21514 | 1804 | 21,5 | 20,6 (H1) | 779 | 40 / 40 / 40 | 60 | 13 | elevation.glb + **KTX2 10 МБ ×2** (осень/лето), @theatre/core |
| 13 | sleep-well-creatives.com | SOTD 01.2026. Иллюстративный NPR-мир: героиня на дюнах, ряд 3D-банок, 3D-книга | three r180 | webgl2 | 17,9 | 2255 | 495 | 18 | 4,2 (DIV) | 471 | 22 / 7 / 162 | 54,6 | 33 | GLB ×12 (Draco), видео 14,7 МБ |
| 14 | shopify.com/editions/spring2026 | Пуантилистский лес из точек, текст по кривой, объёмный свет из видео (R3F) | three r183 + R3F | webgl,webgl2 | 14,2 | 6687 | 892 | 27,3 | 20,5 (P) | 438 | 77 / 45 / 62 | 49,3 | 254 | **KTX2 ETC1S-«видео» по 50 кадров** ×14, HDR ×5, свой .mdpc, @theatre/core |
| 15 | apple.com/iphone-air | Фото-герой; 3D-вьюер телефона ниже (three r165) | three r165 | webgl,webgl2 | 26,1 | 11199 | 1348 | 16,9 | 4,9 (IMG) | 3055 | 0 / 261 / 264 | 55,5 | 410 | **KTX v1 ×87**, glTF ×4 + GLB, EXR ×3 (3,2 МБ); TBT 3 с |
| 16 | stripe.com | Анимированная лента-градиент в герое | three r178 | webgl,webgl2 | 2,8 | 0 | 1436 | 6,1 | 4,1 (IMG) | 380 | 2 / 1 / 2 | 55,6 | 50 | three r178, 1–6 draw calls; уважает reduce |
| 17 | spline.design | Глянцевые фигуры и кролик (Spline runtime) | three r149 + Spline | webgl2 | 12,6 | 63 | 2896 | 3,2 | 2,3 (DIV) | 392 | 192 / 191 / 191 | 58,7 | 60 | .splinecode ×3 (5–43 КБ gz), process.wasm; 192 draw calls в покое |
| 18 | unicorn.studio | Шейдерная «туманность», витрина no-code эффектов | UnicornStudio | webgl2 | 2,8 | 0 | 846 | 19,3 | 19,1 (H1) | 254 | 3 / 3 / 8 | 60 | 16 | рантайм Unicorn Studio |
| 19 | needle.tools | Low-poly диорама, диско-шар (Needle Engine) | three r169 + Needle | webgl,webgl2 | 12,2 | 9095 | 1289 | 15,7 | нет | 288 | 25 / 0 / 183 | 46,1 | 97 | GLB ×31, текстуры KTX2 ×48, basis; до 184 draw calls |
| 20 | github.com/home | 3D-маскоты (кот, Copilot) в фиолетовом свечении | three r148 | webgl | 7,6 | 1371 | 1810 | 13 | 8,1 (H1) | 205 | 0 / 0 / 5 | 55,5 | 29 | GLB ×6 по 248–359 КБ |
| 21 | cobe.vercel.app | Точечный глобус с метками (библиотека cobe) | свой/не опр. | webgl2 | 0,2 | 0 | 171 | 21,5 | 21 (text) | 35 | 6 / 5 / 6 | 60 | 10 | 5 КБ библиотека, 6 draw calls |
| 22 | worldlabs.ai | Страница Marble: картинки миров + сплат-сцены | three r170 + R3F | webgl2 | 16,7 | 8597 | 2669 | — | 4,6 (H1) | 33 | 0 / 1 / 1 | 58,4 | 45 | **.spz ×12 (≈1,4 МБ, 100k сплатов)**, 1 draw call |
| 23 | modelviewer.dev | Скафандр Армстронга в `<model-viewer>` | three r183 + model-viewer | webgl,webgl2 | 9 | 8692 | 342 | 8,7 | 3,8 (—) | 312 | 0 / 0 / 0 | 60 | 31 | GLB 8,7 МБ, HDR 1k |
| 24 | threejs.org/examples/webgl_animation_keyframes | Эталон: LittlestTokyo, скелетная анимация | three r186 | webgl2 | 4 | 3578 | 490 | 3,3 | 2,6 (DIV) | 734 | 79 / 1 / 79 | 60 | 10 | GLB 4 МБ (Draco), 79 draw calls |
| 25 | zentry.com | Прелоадер → проволочный радужный «цветок» (Spline) | three r163 + Spline | webgl2 | 5,8 | 895 | 3262 | — | 3,3 (SPAN) | 30 | 0 / 0 / 38 | 50,6 | 60 | .splinecode 892 КБ, Rive |
| 26 | steven.com | SOTD 06.2026 (OFF+BRAND). Металлические кольца с гравировкой, портрет в центре | three r182 | webgl2 | 13,1 | 11603 | 911 | 7,9 | 3,5 (P) | 167 | 13 / 13 / 13 | 60 | 97 | **KTX2 4K ×23**, GLB ×5, Rive; WebGL2 (не WebGPU) |
| 27 | noomoagency.com | SOTY 2023. Белые воксельные формы вокруг типографики, 3D-продукт | three r156 | webgl2 | 8,8 | 6197 | 905 | 14 | 22,4 (P) | 245 | 79 / 28 / 74 | 54 | 42 | GLB 6,2 МБ |
| 28 | kprverse.com | SOTY 2022 (Resn). Иллюстрированные персонажи, 3D-карусель карточек | three r150 | webgl2 | 46,1 | 35719 | 934 | 141,2 | 145,6 (DIV) | 33 | 37 / 25 / 42 | 59,7 | 410 | GLB с ETC1S 2048 (5,7/4,5/3,8 МБ), KTX2 ×34 — **46 МБ** |
| 29 | en.manayerbamate.com | SOTY 2023. 3D-банка напитка среди плоских иллюстраций | three r141 | webgl2 | 6,8 | 441 | 2272 | 11,2 | 3,2 (SPAN) | 225 | 2 / 2 / 2 | 60 | 131 | **glTF 15 КБ + HDR 425 КБ**, 2 draw calls |
| 30 | deepseecommerce.com | Подводный айсберг; прелоадер не завершился за окно замера | three r161 + R3F | webgl2 | 23,2 | 1666 | 684 | 23,1 | 18,2 (H1) | 84 | 8 / 8 / 8 | 60 | 28 | GLB (кит 1,2 МБ), видео 18 МБ |
| 31 | members-play.lacoste.com/ace-breaker-rg | Брендовая мини-игра: 3D-корт под заставкой | свой/не опр. | webgl,webgl2 | 20,8 | 1080 | 512 | 22,2 | нет | 768 | 19 / 19 / 19 | 59,8 | 45 | GLB 1,7 МБ (br 1,08), картинки 19,6 МБ |
| 32 | playcanvas.com | Пушистая игрушка «drag to rotate» (сплат) в герое | свой/не опр. | webgl2 | 21,1 | 0 | 530 | 9 | 4,2 (SECTION) | 4 | 2 / 0 / 0 | 59,8 | 16 | PlayCanvas; видео 14 МБ |
| 33 | superspl.at/scene/14bac5b2 | Сплат переулка Трогира в iframe-вьюере, потоковая загрузка | свой/не опр. | - | 11,1 | 0 | 1043 | — | 16,3 (IMG) | 0 | 0 / 0 / 0 | 60 | 45 | SOG = lossless WebP (4,7 МБ за окно) |


Мобильный режим (Pixel 7, CPU ×4, 150 мс / 1,6 Мбит/с):

| Сайт | Вес моб., МБ (десктоп) | 3D, КБ | JS, КБ | 1-й 3D-кадр, с | LCP, с (элемент) | TBT, мс | Draw calls прокрутка мед./p90 | FPS прокрутки | Heap, МБ |
|---|---|---|---|---|---|---|---|---|---|
| apple.com/iphone-air | 3,5 (26,1) | 0 | 911 | — | 14 (IMG) | 2099 | 0 / 0 | 24,3 | 17 |
| cobe.vercel.app | 0,2 (0,2) | 0 | 171 | 5,3 | 4,3 (text) | 1008 | 5 / 5 | 55,3 | 10 |
| github.com/home | 3,8 (7,6) | 807 | 1809 | 23,7 | 6,2 (H1) | 1020 | 0 / 4 | 46,8 | 28 |
| igloo.inc | 2,8 (16,6) | 2103 | 454 | 5,7 | 3,2 (::before) | 415 | 0 / 0 | 59,6 | 45 |
| landonorris.com | 4,5 (6,6) | 2546 | 601 | — | 4,9 (IMG) | 259 | 0 / 0 | 60 | 72 |
| lusion.co | 9,5 (16,3) | 2064 | 938 | 5 | 4,4 (H1) | 1300 | 16 / 49 | 56,2 | 28 |
| messenger | 5,7 (5,7) | 1053 | 582 | 4,5 | нет | 725 | 25 / 25 | 59,3 | 26 |
| oryzo.ai | 8 (16,1) | 3621 | 309 | 8,8 | 28,1 (IMG) | 1170 | 24 / 25 | 48,3 | 10 |
| spline.design | 8 (12,6) | 62 | 2755 | 15,5 | 13,1 (DIV) | 1930 | 185 / 185 | 52,7 | 77 |
| stripe.com | 3 (2,8) | 0 | 1419 | 25 | 6,5 (IMG) | 7133 | 1 / 1 | 23,3 | 45 |

Контрольные (без активного WebGL в окне замера): vercel.com (2,5 МБ, JS 1,3 МБ, LCP H1 3,5 с), linear.app (3,9 МБ,
LCP IMG 6,3 с), threejs-journey.com (главная без WebGL, видео 1,5 МБ), dontboardme.com (SOTY 2024: ворота «Bounce a
ball», картинки 7,9 МБ, без WebGL), apple.com/airpods-pro (WebGL-контексты создаются, но 0 draw calls; видео 8,2 МБ,
LCP — картинка героя 8,7 с), samsung.com Galaxy Z Fold7 (three r142 в бандле, контекстов нет; 5,3 МБ).

## 3. Мобильный режим: что меняется

- Лидеры отдают телефону облегчённый набор: Igloo 2,8 МБ (десктоп 16,6), Lusion 9,5 (16,3), Oryzo 8,0 (16,1), Spline
  8,0 (12,6), GitHub 3,8 (7,6); Apple iPhone Air на телефоне за окно замера 3D не грузит вовсе (3,5 МБ против 26,1).
  [проверено]
- DPR: Lusion, Oryzo, GitHub рендерят canvas 618×1259 при CSS 412×839 → **DPR 1,5**; Stripe — 2,0; Spline — полный
  2,625 (1081×2202) и при этом самый высокий TBT среди 3D (1,9 с). [проверено]
- Главный поток: TBT при CPU×4 — Stripe **7,1 с** (Next.js + аналитика + WebGL-градиент), Spline 1,9 с, Lusion 1,3 с,
  Oryzo 1,2 с; у Stripe FPS прокрутки падает до 23 (p95 кадра 117 мс). Тяжесть JS важнее тяжести 3D. [проверено]
- Первый 3D-кадр: 4,5 с (Messenger) … 25 с (Stripe); Lando Norris и Apple — ни одного за окно 20 с. [проверено]

## 4. Эмпирические бюджеты против заявленных норм

Медиана и квартили по 33 сайтам с 3D (десктоп, `99-raw/experiments/A/empirical_budgets_desktop.json`):

| Показатель | min | Q1 | **медиана** | Q3 | max |
|---|---|---|---|---|---|
| Вес страницы (переданные байты), МБ | 0,2 | 7,3 | **12,6** | 20,8 | 63,4 |
| 3D-ассеты (модели + 3D-текстуры), МБ | 0 | 1,05 | **2,6** | 9,1 | 52,7 |
| Картинки, МБ | 0 | 0,22 | **1,7** | 3,9 | 19,6 |
| Видео, МБ | 0 | 0 | **0** | 1,3 | 18,3 |
| JS, КБ | 171 | 534 | **905** | 1289 | 3262 |
| WASM (декодеры, физика, сортировка сплатов), КБ | 0 | 0 | **182** | 327 | 2453 |
| Первый 3D-кадр, с | 2,7 | 7,5 | **14,0** | 21,5 | 141 |
| LCP, с | 2,3 | 3,8 | **5,8** | 20,1 | 146 |
| TBT до прокрутки, мс | 0 | 84 | **290** | 471 | 3392 |
| Draw calls/кадр при прокрутке (медиана) | 0 | 1 | **13** | 40 | 273 |
| Draw calls/кадр при прокрутке (p90) | 0 | 8 | **33** | 78 | 274 |
| Draw calls/кадр в покое | 0 | 2 | **22** | 47 | 267 |
| FPS при прокрутке (headless, потолок 60) | 46 | 55,6 | **59,8** | 60 | 60 |
| JS heap, МБ | 10 | 28 | **45** | 109 | 410 |

Сравнение с нормами из источников (подробности и условия — `02-when-3d-budgets-loading.md` §3):

| Норма | Источник | Выборка наградных сайтов | Вывод |
|---|---|---|---|
| Модель ≤ 10 МБ (≤ 15 МБ жёстко), ≤ 100 000 треугольников (идеал 30–50 тыс.), текстуры ≤ 2048² | Google Scene Viewer / Merchant [документация] | 3D-ассеты сайта: медиана 2,6 МБ, но у Q3 9,1 МБ и максимум 52,7 МБ; KTX2 4K у Steven | нормы AR-вьюера строже, чем практика «миров» |
| Ассет ≤ 3 МБ, ≤ 30 000 вершин, ≤ 15 draw calls | Google DV360, 3D-реклама Swirl [документация] | медиана 13 draw calls при прокрутке | рекламная норма ≈ медиана наградных сайтов |
| Медианная страница веба 2,6 МБ (моб.) / 2,9 МБ (десктоп), JS 632/697 КБ | Web Almanac 2025 [исследование] | 12,6 МБ, JS 905 КБ | 3D-сайт тяжелее в 4–5 раз по весу, в 1,3 раза по JS |
| Страницы ≥ 5 МБ проходят LCP реже: 57 % десктоп / 44 % моб. против 82/72 % у лёгких | Web Almanac 2025 [исследование, корреляция] | 29 из 33 тяжелее 5 МБ; LCP медиана 5,8 с даже на десктопе | тяжёлый 3D-лендинг почти гарантированно проваливает LCP в поле |
| JS ≤ 365 КБ для загрузки < 3 с на p75-телефоне | Alex Russell 2024 через Web Almanac [мнение эксперта] | JS медиана 905 КБ | ни один 3D-сайт, кроме cobe, не укладывается |

## 5. Закономерности у лидеров

### 5.1. Движки и версии
- three.js — 27 из 33 (из них R3F — Shopify Editions, DeepSee, World Labs; Spline-рантайм на форке three — spline.design r149,
  Zentry r163; model-viewer на r183; Needle на r169). Остальные: свой движок Active Theory, PlayCanvas (playcanvas.com,
  SuperSplat в iframe), Unicorn Studio, 1 не определён (Lacoste). [проверено]
- Ревизии three: r141, r143, r148, r149, r150, r151, r156, r158, r161, r163, r165 ×2, r169, r170, r174, r178 ×2, r179 ×2,
  r180 ×2, r182 ×2, r183 ×3, r186 → 10 из 27 на r180+ (последние 12 месяцев), 13 — старше r170. [проверено]
- WebGPU: Bruno Simon (r183) и IVRESS (r182) реально создают контекст `webgpu` при доступном адаптере; остальные — WebGL2
  (8 сайтов создают и WebGL1, и WebGL2 контексты — обычно проба возможностей или второй canvas). [проверено]
- Библиотеки по сигнатурам в JS: GSAP ≈ 15 сайтов, Lenis ≈ 8, `postprocessing` ≈ 14, Rive ≈ 6 (2D-анимация рядом с 3D),
  `@theatre/core` 4. Фреймворки: Nuxt/Vue 7, Next.js 5, Webflow 3, Astro у Lusion. [проверено; сигнатуры `DRACOLoader`/
  `KTX2Loader` в тексте JS означают лишь наличие GLTFLoader — реальное использование установлено по сети]

### 5.2. Форматы ассетов
- **KTX2** (Basis ETC1S/UASTC): Igloo 49 файлов (12,7 МБ, нормали по ≈1 МБ), Active Theory 32, Immersive Garden 40,
  KPR 34 + GLB со встроенными ETC1S-текстурами, Steven 23 (фото-атласы 4K по 1,5–2,2 МБ), Primland (диффуз рельефа
  10 МБ ×2 — сезоны), Unseen (запечённый свет комнаты), Shopify (кадры видео как массив текстур). Apple — **KTX v1** ×87.
- **Draco**: GLB с Draco или отдельные `.drc` (Igloo 22, Messenger 16) + `draco_decoder.wasm`; Meshopt виден реже (у
  bruno-simon `-compressed.glb`).
- **Окружение**: HDR 1k (Lando 378 КБ, Mana 425 КБ, model-viewer moon_1k), EXR (Lusion matcap 590 КБ, Apple 3,2 МБ).
- **Сплаты**: `.sog` (Oryzo, PlayCanvas-формат: lossless WebP + meta.json в ZIP), `.spz` (World Labs, 100k сплатов ≈ 1,4 МБ),
  потоковый SOG в SuperSplat; сортировка — `splat_sorter.wasm` или GPU.
- **Свои бинарные форматы**: Lusion `.buf` (геометрия и анимации), Shopify `.mdpc` (облака точек: квантование, luma/chroma,
  deflate + DecompressionStream) — оправданы только в студийном конвейере.
- **Spline**: `.splinecode` 5–892 КБ + `process.wasm`; **Rive** `.riv` рядом с 3D для 2D-анимации интерфейса.
- **Без сжатия**: IVRESS отдаёт GLB-сцены 14/10/6 МБ без Draco/Meshopt — главная причина 63 МБ.

### 5.3. Прелоадеры, ворота, первый кадр
- Явные ворота (кнопка до входа): Messenger (BEGIN), Unseen (Enter / Enter without audio), Sleep Well (Enter Site),
  Primland (Start without audio, появляется на 168-й с при 27 МБ), IVRESS (Click to start), Bruno Simon (Click to start),
  Lacoste (Play), Don't Board Me («Bounce a ball»). Прелоадеры: Lusion (≈30 с), Active Theory (18 с, проценты),
  Lando Norris (жёлтый экран), Zentry (логотип), DeepSee (Loading experience %), KPR. [проверено]
- Ворота со звуком («Enter with/without audio») — способ получить жест пользователя для WebAudio/автовоспроизведения и
  прогреть шейдеры; цена — невидимый для поиска и нетерпеливых пользователей контент.

## 6. Доступность, reduced motion, энергопотребление

Пары прогонов «обычный / `prefers-reduced-motion: reduce`» (доля пикселей, изменившихся за 1 с простоя):

| Сайт | Обычный | Reduce | Вывод |
|---|---|---|---|
| Stripe | 4,46 % (2 dc) | 0,01 % (0 dc) | **уважает**: рисует кадр и останавливает цикл |
| Shopify Editions | 71,4 % | 5,9 % | частично: движение приглушено, рендер 77 dc/кадр продолжается |
| Lando Norris | 10,2 % | 4,9 % | частично |
| Lusion / Igloo / Messenger / Unseen | 32,9 / 45,8 / 12,0 / 35,0 % | 31,1 / 41,9 / 12,0 / 37,4 % | не уважают |
| Hubtown / Spline / Steven / Noomo / Unicorn / Mana / Active Theory / model-viewer / cobe | 7,7 / 0,7 / 0,8 / 1,5 / 17,5 / 3,2 / 6,2 / 5,9 / 1,9 % | 7,6 / 0,6 / 0,8 / 1,6 / 22,8 / 4,9 / 6,4 / 4,9 / 1,9 % | не уважают |

- Итог: 1 из 16 полностью уважает reduce, 2 — частично, 13 — нет. [проверено, 1 прогон на сайт]
- Непрерывный рендер: у 25 из 33 draw calls идут каждый кадр в покое (Spline — 192 dc/кадр при неподвижной сцене).
- LCP-элемент: H1 (Lusion, GitHub, DeepSee, Primland, Vercel), P (Unseen, Steven, Shopify), DIV/SPAN (Lando, Immersive,
  Hubtown, Sleep Well, IVRESS, Mana, Zentry, KPR, Spline), IMG (Oryzo, Apple, Stripe, Lando-моб., Linear), `::before`
  (Igloo), «нет записи» (Messenger, Bruno Simon, Lacoste, Needle — весь контент в canvas или за воротами). Сайты без
  LCP-записи — те же, где текст рисуется в canvas: для поиска и скринридера там пусто.
- Текст в DOM: у Messenger и Bruno Simon первый экран — только canvas; у Lusion, Stripe, GitHub, Vercel заголовок — HTML.

## 7. Что копировать, что нет (уроки для агента)

| Приём сайта | Копировать для продуктового лендинга? | Почему |
|---|---|---|
| Шейдерная лента/градиент в герое (Stripe) | да | 1–6 draw calls, без ассетов, уважает reduce; но следить за JS фреймворка (TBT 7 с при CPU×4) |
| Одна 3D-банка среди плоской иллюстрации (Mana) | да | 15 КБ glTF + HDR 425 КБ, 2 draw calls; 3D как акцент, контент — HTML |
| 3D-маскоты-GLB по 250–360 КБ (GitHub) | да, с ленивой загрузкой | первый 3D-кадр 13 с десктоп / 24 с моб. — не мешает, т. к. LCP = H1 |
| Точечный глобус (cobe) | да | 5 КБ библиотека, 6 draw calls |
| Hero-продукт с запечённым светом и KTX2 (Unseen, Steven) | да, в пределах 2–5 МБ | запекание в Blender → текстуры KTX2/WebP; Steven — 4K-атласы, это верхняя граница |
| Сплаты продукта/места (Oryzo, World Labs) | осторожно | 1,4–3 МБ на сцену, 1 draw call; нет стандарта (SOG/SPZ/glTF-расширение), нужен фолбэк-картинка |
| Облака точек из видео (Shopify) | нет (без студийного конвейера) | свой формат, VGGT, уровни 0–3 |
| Прелоадер 18–30 с, ворота «Enter» | нет | LCP и контент за воротами; для лендинга продукта — потеря конверсии |
| Миры 27–63 МБ (IVRESS, KPR, Primland) | нет | жанр кампании/портфолио; без сжатия геометрии |
| Непрерывный рендер без движения, игнор reduce | нет | см. §6 |

## 8. Референсы без замера (описание по источникам)

| Референс | Что | Источник, дата |
|---|---|---|
| cartier.com/en-fr/watchesandwonders | 6 3D-«альковов» по часам, прокрутка между комнатами, Web Audio; дизайн и 3D — Immersive Garden, WebGL-разработка — 60fps, звук — Mooders: связка «дизайн-студия + WebGL-студия + звуковая студия», типичная для люкса | кейс Awwwards [S13] [кейс]; Utsubo 2026-06 [мнение вендора]; сайт отдал 403 скрипту |
| explore.ownprimland.com (Codrops-кейс нет) | см. таблицу | Awwwards SOTD 02.2026 |
| tympanus.net/Tutorials/CurveGallery/ | Галерея 500 плоскостей по пути камеры из Blender (JSON), GSAP Observer | Codrops 2026-07-07 |
| tympanus.net/Tutorials/BalloonButton/ | Кнопка-подушка: симуляция ткани Blender → shape keys → glTF | Codrops 2025-08-20 |
| tympanus.net/Demos/PaperCrumble/ | Сминаемая бумага: VAT из Houdini (EXR 1024×200) | Codrops 2026-09-19 |
| tympanus.net/Tutorials/DreamyParticles/ | GPGPU-частицы на поверхности модели, отталкивание курсором | Codrops 2024-12-19 |
| tympanus.net/Tutorials/AccessibleWebGLText/ | WebGL-текст поверх скрытого, но доступного HTML | Codrops 2025-06-05 |
| tympanus.net/Tutorials/CodropsFanMuseum/ | Музей-мир из Blender с полностью запечённым светом | Codrops 2025-04-08 |
| singularity-codrops.netlify.app | 27 мешей, 184 текстуры, 40k треугольников, физика и пост — 2,1 МБ | Codrops 2025-02-11 |
| projects.thibautfoussard.com/the-sleepers/ | Фальшивый туман, контур inverted hull из Blender, бесконечный город 3×3 | Codrops 2026-07-10 |
| optikka.com | Секвенция кадров WebP в canvas вместо прокрутки видео | Codrops 2025-10-16 |
| html-in-canvas.vercel.app | HTML-in-Canvas (флаг Chrome), `HTMLTexture` в three r184+ | Codrops 2026-05-13 |
| shaders.paper.design | Библиотека шейдерных фонов (mesh gradient и др.), 6 КБ br | npm @paper-design/shaders 0.0.81 |
| sparkjs.dev | Рендер сплатов для three.js (World Labs) | npm @sparkjsdev/spark 2.2.0 |
| threejs.org/examples/#webgpu_gaussian_splat | Официальные сплаты three r186 (`GaussianSplat`, SPZ/PLY/glTF) | релиз r186 |
| getty.edu/persepolis (persepolis.getty.edu) | SOTY 2022: реконструкция Персеполя | Awwwards SOTY |
| kodeclubs.com | Developer Site of the Year 2020 и Site of the Month 11.2020 (Merci-Michel) — эталон прошлого поколения | Awwwards [S15] [награда] |
| prometheusfuels.com, umamiland.withgoogle.com | SOTY 2020–2021 (Active Theory, Monks) — эталоны прошлого поколения | Awwwards SOTY |

## Частые ошибки

- Снимать живой 3D-сайт через 2–8 с после `load`: у половины лидеров в это время ещё прелоадер или ворота → выводы о
  «пустом» сайте ложные. Ждать первого кадра с draw calls и/или нажимать ворота.
- Мерить вес по `content-length`: у сжатых на лету ответов его нет → недоучёт JS/CSS; брать переданные байты.
- Прокручивать `window.scrollTo`: сайты с виртуальным скроллом (Lusion, Igloo, Messenger, Hubtown) не двигаются; нужна
  прокрутка колесом.
- Считать сигнатуру `DRACOLoader`/`KTX2Loader` в JS доказательством использования Draco/KTX2 — это строки GLTFLoader.
- Переносить бюджеты «миров» на продуктовый лендинг: медиана 12,6 МБ — не цель.
- Считать FPS 60 в headless признаком «быстро»: ограничение vsync и десктопный GPU; смотреть TBT при CPU×4 и draw calls.
- Копировать версию three и API из чужого бандла (r141–r165): в r186 другие имена (`HDRLoader`, `Timer`,
  `RenderPipeline`) — см. `03-runtime-landscape.md` §2.

## Чек-лист

- [ ] Страница-кандидат в референсы измерена `site_probe.py` (десктоп + Pixel 7 с троттлингом)?
- [ ] Вес ≤ 7 МБ (десктоп) и ≤ 3 МБ (телефон) при 3D ≤ 2 МБ — или есть письменное обоснование «мира»?
- [ ] LCP-элемент — HTML-текст или постер ≤ 80 % вьюпорта, не за прелоадером?
- [ ] Первый экран читается без 3D (контент в DOM, CTA доступна до загрузки сцены)?
- [ ] Draw calls при прокрутке ≤ 100 (десктоп) / ≤ 50 (телефон)?
- [ ] DPR на телефоне ≤ 1,5–2?
- [ ] При `prefers-reduced-motion: reduce` доля движения в покое ≈ 0 % и нет рендера каждый кадр?
- [ ] Геометрия сжата (Draco/Meshopt), текстуры — KTX2/WebP, декодеры грузятся только при необходимости?

## Открытые вопросы и противоречия

- Утверждение подборки Utsubo (2026) «Steven.com — Three.js + WebGPU» замером не подтверждено (WebGL2, адаптер WebGPU
  не запрашивался); возможно, WebGPU включается по условиям (устройство, флаг) — не проверено.
- «Первый 3D-кадр» зависит от сети машины (не фиксировалась); для сравнения между сайтами годится, для абсолютных
  порогов — нет. Нужен повтор с фиксированной пропускной способностью (например, 20 Мбит/с) — задача волны 3 (J).
- Мобильный режим — эмуляция Pixel 7 на ноутбучном GPU; реальная тепловая просадка и память телефона не измерены.
- Messenger и IVRESS не удалось провести через ворота (селектор не кликабелен) — их «после входа» не измерено.
- Выборка смещена к наградным витринам (Awwwards/FWA); продуктовые страницы брендов (Apple, Samsung) почти не
  используют реалтайм-3D в первом экране — отдельная выборка e-commerce с model-viewer нужна волне 2 (F/G).

## Источники

- [S1] Awwwards, «Sites of the Year» (список победителей 2017–2025), https://www.awwwards.com/websites/sites_of_the_year/ — даты и студии SOTY; надёжно для атрибуции.
- [S2] Awwwards, «Best Three.js Websites», https://www.awwwards.com/websites/three-js/ — лента номинантов сентября 2026; для поиска кандидатов.
- [S3] Utsubo (J. Lecamus), «8 Best Three.js Websites of 2026», 2026-06-30, https://www.utsubo.com/blog/best-threejs-websites-2026 — подборка студии с самопродвижением [мнение вендора]; даты наград — сверять.
- [S4] Hon Tran, «WebGL Website Examples 2026» и «Best Award-Winning Websites of 2026», hontran.dev, 2026-06/07 — самореклама фрилансера, низкая доказательность [мнение].
- [S5] Codrops (A. Thelander), «Engineering the Web Experience Behind Shopify’s Spring ’26 Edition», 2026-06-26, https://tympanus.net/codrops/2026/06/26/engineering-the-web-experience-behind-shopifys-spring-26-edition-everywhere/ — первоисточник команды; объясняет KTX2-массивы кадров, stacked-alpha, .mdpc, уровни 0–3.
- [S6] Codrops (N. Fanton), «Building Efficient Three.js Scenes», 2025-02-11, https://tympanus.net/codrops/2025/02/11/building-efficient-three-js-scenes-optimize-performance-while-maintaining-quality/ — бюджет демо 2,1 МБ; практика.
- [S7] Web Almanac 2025, Page Weight, https://almanac.httparchive.org/en/2025/page-weight — медианы веса, связь веса и прохождения LCP [исследование].
- [S8] Web Almanac 2024, JavaScript и Page Weight, https://almanac.httparchive.org/en/2024/javascript — медианы JS, TBT, INP [исследование].
- [S9] Google ARCore, «Scene Viewer», https://developers.google.com/ar/develop/scene-viewer — лимиты AR-моделей [документация].
- [S10] Google, «3D assets guide» (Display & Video 360), https://support.google.com/displayvideo/answer/9794085 — лимиты 3D-рекламы [документация].
- [S11] PlayCanvas, «The SOG Format», https://developer.playcanvas.com/user-manual/gaussian-splatting/formats/sog/ — спецификация SOG [документация].
- [S12] Собственные замеры: `99-raw/experiments/A/sites/`, `sites_desktop.csv`, `sites_mobile_thr.csv`, `empirical_budgets_desktop.json` (2026-09-22/23) [проверено].
- [S13] Awwwards, кейс «Watches & Wonders: immersive experience for Cartier», https://www.awwwards.com/watches-wonders-immersive-experience-for-cartier.html ; карточка сайта: https://www.awwwards.com/sites/cartier-watches-wonders-2025 — роли студий (Immersive Garden, 60fps, Mooders) [кейс].
- [S14] Awwwards, Annual Awards — победители 2025, https://www.awwwards.com/annual-awards/winners — Developer Site of the Year 2025: Messenger (Abeto); Site of the Year 2025: Lando Norris (OFF+BRAND) [награда].
- [S15] Awwwards, Developer Site of the Year 2020, https://www.awwwards.com/annual-awards-2020/developer-site-of-the-year ; Site of the Month за ноябрь 2020: https://www.awwwards.com/kode-sports-club-by-merci-michel-wins-site-of-the-month-november-2020.html — Kode Clubs (Merci-Michel) [награда].
