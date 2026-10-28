# Площадки референсов: паспорт 62 площадок — жива ли, чем полезна, как искать, API, вход, условия, частота

Волна 1 · агент B, продолжатель B2 · 2026-09-24 · источников 31 (условия и правила 23 площадок, robots.txt 34 хостов,
документация Dribbble API v2 и Are.na API v3, разведки оркестратора и архитектора) · опыты B/01 (зонд браузером), B/02
(адаптеры галерей, серверный HTML 7 галерей), B/06 (Dribbble), B/07 (Dprofile) · Brave 153.1.95.101, Playwright 1.63,
безголовый режим без подмены UA. Машиночитаемо — `sources.yaml` (62 записи, `checked_at`): 36 площадок разобраны здесь, 26
площадок движения — группы `motion-kits` (12), `motion-rules` (9), `motion-generators` (2) и записи `animista`, `uiverse`,
`motion-dev-examples` группы `effects-code` — в `04-motion-libraries-and-rules.md` (§3–§6, 2026-10-28); клиент —
`02-refs-client-and-library.md`; мудборд — `03-moodboard-and-handoff.md`.

## Выжимка для агента

1. **Сервисы со входом — только через клиент и решения заказчика**: Dribbble и Dprofile — «поиск», Behance — `off`
   (24.09.2026). → §2.1 [практика: решение заказчика]
2. **Почти все площадки прямо запрещают автоматический сбор**: Dribbble 7.1/7.2/7.11, Dprofile 11.3, Refero, Mobbin, Vimeo,
   Pinterest, Are.na, Savee, Minimal Gallery, Land-book, Lapa Ninja, Cosmos 8(F), LottieFiles, Adobe 6.18 («data scraping
   for machine learning or other purposes»); CSSDA и Awwwards — копирование контента. «Можно, потому что публично» —
   неверно. → §3 [документация]
3. **Официальные API есть у Are.na (v3), Refero и Mobbin (API и MCP), Vimeo; у Dribbble API — только свои шоты**;
   One Page Love обещает API, но он в листе ожидания. → §2 [документация]
4. **Галерея — список адресов, а не источник картинок**: для выборки C берётся ссылка на сайт и награда, сайт мерится сам;
   скриншоты и описания галереи не копируются (CSSDA прямо запрещает). → §4 [документация: CSSDA /terms]
5. **Антиботы для безголового браузера**: Land-book и Lapa Ninja (Cloudflare), CodePen, LottieFiles, Shadertoy (403 для
   не-браузера), SiteInspire (429 для curl); не обходить — только ручные ссылки заказчика. → §2.2 [проверено]
6. **`robots.txt` читать по RFC 9309**: у Awwwards `Disallow: /websites/?` закрывает только адреса с параметрами — SOTD
   разрешён; Pinterest закрыт для «*» целиком. → §4.2 [стандарт: RFC 9309]
7. **Частота — 10 с + джиттер на площадку**, 40 страниц в сутки на галерею, 60 — на Dribbble и Dprofile. → §5 [практика: решение B]
8. **Награда — `[награда]`, не доказательство**: признание жюри, а не конверсия; у Awwwards весы Design 40 %, Usability 30 %,
   Creativity 20 %, Content 10 %. → §4.1 [награда]
9. **Dribbble и Behance — концепты; живые сайты — для структуры, ритма, движения** (выдача Dribbble «saas landing page» —
   средний SaaS). → §2.1 [проверено]
10. **Dprofile — главный русский источник** (кириллица, рынок РФ), но обложки кейсов — презентационные мокапы; дата
    публикации есть не у всех карточек. → §2.1 [проверено]
11. **Движение ищут в видео и коде** (Vimeo — только трек V, Codrops, витрина GSAP, Rive, LottieFiles), а не в шотах. → §2.4 [практика]
12. **Код брать только с лицензией**: демо Codrops — MIT, если не указано иное; GSAP — бесплатен и для коммерции;
    публичный пен CodePen — MIT по условиям CodePen (ред. 11.12.2017, с уведомлением об авторстве); шейдер Shadertoy без
    явной лицензии — CC BY-NC-SA 3.0, то есть **не для коммерческого сайта**; анимация LottieFiles — лицензия конкретного
    ассета (Free-план «strictly for non-commercial use») `[спорно]`. → §3.3 [документация]
13. **Каждая запись паспорта датирована** (`checked_at`), статусы «жива», «антибот», «условия» — скоропортящиеся: пересмотр
    раз в 6 месяцев или при сбое клиента. → §1 [практика: правило базы]
14. **Галереи для выборки — через клиент**: `search <галерея> latest` даёт сайт, награду с датой и теги без картинок галереи
    (Awwwards SOTD — 31 сайт с адресом и датой за 25.08–24.09.2026, Landingfolio — 80, godly.design — 40). → §4.1
    [проверено: B/02 офлайн]
15. **Recent — это прежний Godly** (`godly.website` → `recent.design/?ref=godly`, у сайтов в Recent — `?ref=godly`);
    godly.design — другой сайт с тем же именем. → §2.2 [данные]
16. **Живость галереи проверять по дате последней записи**: Httpster — 2025-05-26, Recent `/websites` — 2026-07-04 (на
    24.09.2026); для «свежих приёмов» такие галереи отстают. → §2.2 [данные: B/02]

## 1. Как читать паспорт

| Поле | Что значит | Откуда |
|---|---|---|
| жива | открылась ли главная в безголовом Brave 153 без подмены UA; статус, время | зонд B/01 (16:00–16:10 24.09), живые запросы B/06, B/07; разведка оркестратора; curl архитектора (05:52) |
| чем полезна | статика, движение, код, кейсы с процессом | осмотр, заметки |
| как искать | шаблоны адресов, фильтры, порции | зонд, клиент, кэш других агентов |
| API | есть ли, доступ, лимиты | документация |
| вход | нужен ли, платно ли | главная, условия |
| антибот | что видит не-браузер и безголовый браузер | B/01, фундамент |
| robots | правила для «*» по RFC 9309 | фаза robots B/01 (34 хоста, `99-raw/cache/robots/`) |
| условия | URL, редакция, ключевые пункты | `99-raw/cache/*terms*`, WebFetch |
| режим клиента | `search`, `assistant`, `off` — решение заказчика; `public` — галерея без входа; `manual` — только ссылки заказчика; `api` | заказчик, B |
| ценность | 3 — основной источник, 2 — полезен в своей роли, 1 — редко | B |

Сеть 24.09.2026: VPN с раздельной маршрутизацией (зарубежное — выход в Литве), кратковременные обрывы: Dprofile 15:00
(тайм-аут 40 с), FWA и Adobe (тайм-аут `fetch.py`), главная Awwwards и One Page Love (тайм-аут 40 с в браузере) — такие
строки помечены и требуют перепроверки, а не вывода «площадка мертва».

## 2. Паспорт по группам

### 2.1. Портфолио и шоты

| Площадка | Жива (24.09) | Как искать | API · вход | Режим | Ценность |
|---|---|---|---|---|---|
| Dribbble | да: 6 запросов и 2 карточки через сессию, без челленджей | `/search?q=<q>` → `/search/<q-через-дефис>`; `/shots/<id>`; `/tags/<тег>`; `/colors/<hex>`; порции прокруткой ≈ 24–34 | API v2: OAuth, только свои шоты, 60/мин, 1 440/сутки · вход не нужен для выдачи | «поиск» (≈ 15:00) | 3 |
| Behance | по разведке: curl и безголовый без cookie → 403 JS-челлендж Fastly | `/search/projects?search=<q>`; `/gallery/<id>/<slug>`; порции — `POST /v3/graphql` страницы | новых ключей API нет · Adobe ID | `off` (15:33) | 2 |
| Dprofile | да: 0,7–1 с; 5 запросов через сессию, без челленджей | `/cases/search?query=<q>&sortType=DATE` (+ `isPro`, `hasAchievement`, `verified`); `/case/<id>/<slug>`; 1-я страница — серверный HTML, порции — `m-search/cases` | публичного API нет · вход не нужен для поиска | «поиск» (16:24) | 3 |

- Dribbble — лучший источник концептов и палитр (8 цветов у шота), видео-шоты дают идею движения; выдача по жанру тянет к
  «среднему», запросы по эпохе и предмету — нет (`03` §1.1).
- Dprofile — кириллическая вёрстка и русский рынок; награды площадки («Лучшее на Dprofile» — красная, «Dprofile рекомендует» —
  золотая, до 4 в день на категорию — справка `dprofile.ru/help`); обложки кейсов — ноутбук или телефон на эффектном фоне
  (мокап), а не страница: для композиции открывать сам кейс (`get`).

### 2.2. Галереи сайтов

| Площадка | Жива (24.09, безголовый Brave) | Как искать | Антибот · robots | Режим | Ценность |
|---|---|---|---|---|---|
| Awwwards | HTTP 200 за 0,7 с (B/02, 17:02); SOTD в браузере — тайм-аут 40 с (16:00, перемерить) | `/websites/sites_of_the_day/` (31 сайт, `?page=N`), `…/sites_of_the_month/`, `…/sites_of_the_year/`, `/sites/<slug>` | не замечен · `Disallow: /websites/?` (не задевает `…/sites_of_the_day/?page=N`), `/inspiration/search`, `/gallery/` | `public`: `search awwwards sotd` (вживую 20/20, 18:00) | 3 |
| CSS Design Awards | 200, 3,9 с в браузере; честному UA — 403 (и robots.txt) | `/wotd-award-winners` (WOTD с датой), `…/wotm-…`, `…/woty-…`, `/special-kudos-award-winners`, главная; `/sites/<slug>/<id>/` | 403 не-браузеру | `public`: `search cssda wotd` (вживую 18/18, 18:00) | 3 |
| FWA | 200, 7,7 с | главная (FOTD; 3 верхних — JSON `caseMenu` в HTML, лента — запросами страницы), `/cases/<slug>` | · `Disallow: /admin/`; условия II.4 запрещают «create a database… of these web pages» | **hold** до решения заказчика (вживую 19/19 до hold, 18:02) | 2 |
| Recent (прежний Godly) | 200, 10 с, Cloudflare; `godly.website` → `recent.design/?ref=godly` | `/websites` (20 сайтов, последняя запись 2026-07-04), лента `/i/<id>-<slug>` — работы, не только сайты | · `Allow: /` | `public`: `search recent latest` | 3 |
| godly.design | 200, 23 с, «Godly — Design Inspiration»; другой сайт (ссылки с `?ref=saaspo.com`) | `/websites` (40), разделы `/hero`, `/cta`, `/footer` | · `Allow: /` | `public`: `search godly websites` | 2 |
| Land-book | **челлендж Cloudflare** безголовому браузеру; обычный HTTP пускает (условия прочитаны) | — | ИИ-краулеры явно разрешены; условия: «use bots, crawlers, or scrapers to collect or copy content» — запрещено | `manual` | 2 |
| Lapa Ninja | **Cloudflare «Attention Required!» 403** безголовому браузеру; обычный HTTP — 200 | — | · `Disallow: /api/`; условия (13.09.2026): «may not scrape, bulk-download» | `manual` | 2 |
| SiteInspire | 200, 4,1 с в браузере (Vercel); не-браузеру — 429 «Vercel Security Checkpoint» | главная; `/website/<id>-<slug>` | 32 именованных агента; условий нет (`/terms` в браузере — «Page not found») | `public`: `search siteinspire latest` (вживую 20/20 с адресом сайта) | 2 |
| One Page Love | главная — тайм-аут 40 с (перемерить) | главная, `/llms.txt` | robots зовёт к API | ждать API | 2 |
| Httpster | 200, 11 с; **последняя запись 2025-05-26** | `/` (24), `/page/N/`, стиль `/style/<slug>/` | robots 404 (24.09 — и сетевой сбой) | `public`: `search httpster latest` | 1 |
| Minimal Gallery | 200, 20 с | `/` (23), `/websites/page/N/`, тег `/tag/<тег>/` | `Disallow: /wp-admin/` | `public`: `search minimal latest` | 1 |
| Landingfolio | 200, 26 с | `/` (80), отрасль `/inspiration/landing-page/<slug>` | `Disallow: /dashboard, /login` | `public`: `search landingfolio latest` | 2 |

- На SOTD Awwwards стоит невидимый reCAPTCHA v3 для форм (`recaptcha/api.js?render=…`); клиент различает «капча на
  странице» и «вызов» (пустая страница, не-200, `bframe`, DataDome): первый запуск 24.09 17:59 дал ложную паузу — детектор
  исправлен, повтор с разрешения оркестратора — 20 записей без вызова [проверено].
- Живой прогон 24.09 17:59–18:05 (Brave 153, 1 страница на галерею): 9 галерей → 173 записи сайтов, 4 сайта сразу в двух
  галереях, ни одной картинки галереи; галерея — 3–19 с [проверено].

### 2.3. Интерфейсы и сценарии

| Площадка | Жива | Что даёт | API · вход | Режим | Ценность |
|---|---|---|---|---|---|
| Refero | 200, 11 с | экраны продуктов и веб-страницы, потоки | API и MCP по тарифу · подписка | `manual` (кандидат — API) | 2 |
| Mobbin | 200, 10 с | экраны приложений и веба | API и MCP — «personal or internal business use» · подписка | `manual` (кандидат — API) | 2 |
| Page Flows | 200, 9 с | видео и скриншоты сценариев | — · подписка | `manual` | 1 |

### 2.4. Эффекты с кодом и движение

| Площадка | Жива | Что даёт | Лицензия кода · антибот | Режим | Ценность |
|---|---|---|---|---|---|
| Codrops | curl 200 | эффекты с кодом и разбором | демо — MIT, если не указано иное | `manual` (F) | 3 |
| CodePen | 403 для не-браузера | пены | публичный пен — MIT (ToS, ред. 11.12.2017); приватный, никогда не публичный — без лицензии | `manual` | 3 |
| Витрина GSAP | 200 | сайты на GSAP | GSAP — бесплатно и для коммерции | `public` | 2 |
| Форум three.js, Showcase | 200 | WebGL-проекты | у автора | `manual` | 2 |
| Shadertoy | 403 для не-браузера | шейдеры | лицензия автора; без неё — CC BY-NC-SA 3.0 (некоммерческая) | `manual` | 2 |
| Vimeo | 200 | ролики кейсов | запрет автоматов, кроме API | только трек V | 2 |
| LottieFiles | 403 для не-браузера | Lottie | бесплатные — Lottie Simple License; Free- и Individual-планы — «strictly for non-commercial use» `[спорно]`; роботы запрещены | `manual` | 2 |
| Rive | marketplace, community/files — 200 | `.riv` | не найдены | `manual` | 2 |

### 2.5. Типографика, мудборды, русские

| Площадка | Жива | Что даёт | Режим | Ценность |
|---|---|---|---|---|
| Fonts In Use | 200 | шрифты в реальном применении, кириллица | `manual` | 3 |
| Typewolf | 200 | пары шрифтов, сайт дня | `manual` | 2 |
| Are.na | 200; API v3 | хранилище мудбордов заказчика | `api` (`arena pull`, `push` в private) | 3 |
| Pinterest | 200; robots закрыт для «*» | доски заказчика | `manual` | 1 |
| Savee | `savee.it` → `savee.com` | закладки дизайнеров | `manual` | 2 |
| Cosmos | 200; условия — `/legal/terms-conditions` (`/terms` — профиль пользователя) | коллекции; условия 8(F): только браузеры и агенты Cosmos | `manual` | 2 |
| Milanote | 200 | инструмент досок, не источник | `manual` | 1 |
| «Рейтинг Рунета» | 200; итоги — `awards.ratingruneta.ru` | победители по отраслям РФ | `public` | 2 |
| «Золотой сайт» | 200; итоги — `goldensite.ru/results/` | конкурсные сайты РФ | `public` | 2 |
| Tagline | curl 200 за 16 с | Tagline Awards | `public` | 2 |

Зонд главных 24.09 18:08–18:11 (безголовый Chromium 153 без подмены UA, B/01): 200 — Codrops, витрина GSAP (28 с),
форум three.js, Vimeo, Rive, Fonts In Use, Are.na, Pinterest (стена «зарегистрируйтесь, чтобы…»), Savee, Cosmos, Milanote,
«Рейтинг Рунета», «Золотой сайт», Tagline, Awwwards (5,7 с), One Page Love (2,9 с); **403** — CodePen, Shadertoy, LottieFiles;
тайм-аут 40 с — Typewolf. Вместе с зондом 16:00 — все 34 площадки [проверено].

## 3. Условия площадок — дословно, с редакцией

### 3.1. Сервисы со входом

- **Dribbble** (`dribbble.com/terms`, «Updated March 17, 2025»): 7.1 «Copying, distributing, or disclosing any part of the
  Website or any Services in any medium, including without limitation by any automated or non-automated "scraping"»; 7.2 —
  автоматы, которые шлют больше запросов, «than a human can reasonably produce in the same period of time by using a
  conventional online web browser»; 7.7 «Collecting or harvesting any personally identifiable information or User
  information, including account names and emails»; 7.11 «Accessing any User Content … through any technology or means other
  than those provided or authorized by the Service»; 7.12 — обход мер ограничения доступа; 11 — не «copy, reproduce, transmit,
  publicly display … or create derivative works from any Dribbble Content». Правила API: «Scraping, copying, saving, or storing
  our data is strictly prohibited»; удалить шот или персональные данные в течение 24 ч по просьбе владельца [S1][S2].
- **Dprofile** (`dprofile.ru/terms` → PDF, `Last-Modified` 2026-08-11): п. 2.1 — соглашение принимается «включая просмотр
  размещенных на Сайте материалов»; п. 11.1 — «Копировать информацию на другие сайты только с указанием источника и с
  разрешения правообладателя», «Использовать информацию сайта в личных некоммерческих целях»; п. 11.3 — «Не использовать
  скрипты (программы) для автоматизированного сбора Информации и/или взаимодействия с Сайтом и его сервисами»; п. 15.2 — не
  копировать ПО и не «проникать в программное обеспечение с целью получения кодов программ» [S3].
- **Behance** (Product Specific Terms, «Last updated June 18, 2024»): 2.1 «You may not phish or collect other people's
  information without their consent. You may not frame the Services…»; API (п. 6): «solely for non-commercial purposes»,
  6.4 — не скрывать личность приложения, 6.6 — не хранить контент дольше 30 дней [S4]. Поверх — **Adobe General Terms**
  («Published October 3, 2025. Effective as of October 3, 2025»; при конфликте главнее Product Specific Terms, п. 1.2),
  разд. 6 «User Conduct»: 6.6 «access or attempt to access the Services and Software by any means other than the interface
  we provide or authorize»; 6.7 — не обходить ограничения доступа; 6.18 «use any data mining or similar data gathering and
  extraction methods in connection with the Services and Software, including data scraping for machine learning or other
  purposes»; 6.19 — не накручивать «appreciations on Behance»; 6.21 — не показывать сервис во фрейме; разд. 17 — не
  использовать «any content, data, output… to directly or indirectly create, train, test, or otherwise improve any machine
  learning algorithms or artificial intelligence system» [S25]. Для клиента это значит: «поиск» по Behance — тот же класс
  риска, что Dribbble 7.11; режим остаётся `off` до решения заказчика.

Решения заказчика: Dribbble — «поиск» (≈ 15:00, п. 7.1, 7.2, 7.11 объяснены оркестратором); Dprofile — «поиск» (16:24,
п. 11.3, риск блокировки аккаунта и «некоммерческие цели» переданы дословно, риск принял он); Behance — отложен (15:33).
Не вынесены заказчику: Dribbble 7.7 (поле `author`) и правило API о хранении — в отчёте B.

### 3.2. Галереи, интерфейсы, мудборды

| Площадка | Редакция | Ключевой пункт (дословно) |
|---|---|---|
| Awwwards `/terms/` | даты нет | «any unauthorized use or reproduction is strictly prohibited. Our content may not be used for commercial purposes unless expressly authorized by Awwwards»; «Websites featured on our site remain the intellectual property of their creators» |
| CSSDA `/terms` | даты нет | «It is a strong condition of use that you do not copy any content and data from the CSSDA website without our permission. This includes but is not limited to website screenshots, website descriptions, designer information…» |
| Minimal Gallery `/legal/` | May 2026 | «may not reproduce… any images (screenshots/thumbnails)… for commercial or public purposes without our prior written permission. This includes scraping, downloading images in bulk…»; «Limited personal use (e.g., viewing and bookmarking for inspiration) is permitted» |
| Landingfolio T&C | даты нет | «You agree to not copy, duplicate or otherwise reproduce any part of our website, product or any other services» |
| Refero ToU | August 3, 2026 | запрещено «use scraping, crawling, automation, or systematic extraction to copy Refero Content outside documented download features»; «normal design work and product improvement based on what you learn from Refero are allowed» |
| Mobbin Terms | May 16, 2026 | запрещено «unauthorised use of any scraper, robot, bot, spider, crawler or any other automated device»; поисковикам — по robots.txt с условиями; API и MCP — «personal or internal business use» |
| Page Flows Terms | January 16th, 2025 | контент — скриншоты чужих интерфейсов, удаление по DMCA |
| Vimeo ToS | July 8, 2024 (с 15.08.2024) | запрещено «Access the Services using any automated means (such as robots, botnets, or scrapers) except (1) using our APIs… (2) … public search engines… robots.txt; or (3) with our prior written permission» |
| Are.na Terms + API | даты не извлечено | запрещены «Automated data scraping or crawling», «Bulk and Automated Downloads», «excessive, or abusive use» API; API «not for scraping or bulk data collection» |
| Pinterest ToS | April 30, 2025 | «not scrape, collect, search, copy or otherwise access data or content from Pinterest in unauthorized ways, such as by using automated means (without our express prior permission)»; Developer Guidelines — данные API не хранить |
| Savee Terms | даты не извлечено | запрещено «Scrape, crawl, or otherwise extract data or content from Savee without our prior written permission» |
| Land-book `/terms_of_use` | January 2026 | не «use bots, crawlers, or scrapers to collect or copy content»; «You may not use Landbook's content or data for machine learning, AI training, or commercial reuse without written consent»; права на сайты — у авторов |
| Lapa Ninja `/policy/` | September 13, 2026 | «You may browse, save and share content for personal or professional inspiration. You may not scrape, bulk-download, or redistribute the gallery, its screenshots or its data without written permission»; скриншоты — «© of their respective owners» |
| Cosmos `/legal/terms-conditions` | September 25, 2025 | 8(F) не «access or search the Services or download content… using any engine, software, tool, agent, device, or mechanism (including spiders, robots, crawlers, data mining tools…) other than… generally available third-party web browsers»; 8(I) — не собирать персональные данные пользователей |
| FWA `/terms-conditions` | даты нет (`render_fetch.py`, 2026-09-24) | II.2 «FWA reserves all its rights and strictly forbids any unauthorised use or duplication… No material, however, can be used for any commercial purpose whatsoever»; II.3 сохранённые копии — только «for subsequent viewing purposes or to print extracts for personal use»; II.4 «Unless otherwise expressly permitted in writing, you may not create a database in any form whatsoever of these web pages» `[спорно]` → адаптер FWA в hold |
| SiteInspire | условий нет | ссылки на главной нет; `/terms` — 429 не-браузеру, в браузере — «Page not found»; в Wayback страниц условий нет |

### 3.3. Код и лицензии

- Codrops: «Our downloadable demos are licensed under the MIT license, if not specifically mentioned otherwise»; freebies — в
  личных и коммерческих проектах, без перепродажи; статьи целиком не перепубликовать [S5].
- GSAP: «Commercial usage is covered under the standard license», включая бывшие плагины Club (Webflow, стандартная лицензия)
  [S6]; оговорка о визуальных конструкторах — G (`../07-stack-implementation/`).
- CodePen (условия в блоге CodePen, «Last Update: December 11, 2017»; `codepen.io/legal/tos/` — 403 не-браузеру): доступ —
  «solely with supported browsers through the Internet for your own internal purposes»; контент публичного пена лицензирован
  другим пользователям — «Specifically, the MIT license. If you specifically save a Pen as private… and that Pen has never
  been public… the code in that particular Pen is unlicensed» [S26]. Значит, публичный пен можно брать в коммерческий сайт
  с сохранением уведомления MIT; актуальность редакции 2017 года — перепроверить по `codepen.io/legal/tos/` в браузере.
- Shadertoy (снимок Wayback 2025-10-01; прямой адрес — 403): «if you don't place a license on a shader, it will be protected
  by our default license… Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported» [S27] → шейдер без явной
  лицензии автора — **не для коммерческого сайта**; переписывать по мотивам — своими словами и кодом.
- LottieFiles (снимок Wayback 2026-07-12; прямой адрес — 403; даты редакции в тексте нет): бесплатные ассеты под «Lottie
  Simple License» исключены из запрета копирования; одновременно «The Individual Plan and Free Plan are strictly for
  non-commercial use only», коммерческое использование — «animations created through or obtained from Lottiefiles… Advertising
  and Marketing… websites»; роботы и data mining запрещены [S28] → перед использованием проверять лицензию конкретной
  анимации `[спорно]`.
- Форум three.js: страница условий на JS — не прочитана; лицензия проекта — у автора.

## 4. Галереи как данные для выборки C

### 4.1. Что брать и как

| Источник | Адрес | Что даёт C | Как брать |
|---|---|---|---|
| Awwwards SOTD, SOTM, SOTY | `https://www.awwwards.com/websites/sites_of_the_day/` (`…/sites_of_the_month/`, `…/sites_of_the_year/`); карточка `/sites/<slug>` | ссылка на сайт, дата SOTD, студия, теги (в т. ч. приёмы: GSAP, WebGL, Three.js, Parallax) | `refs_client.py search awwwards sotd [--pages 2]` → записи сайтов; сайт мерится сам (`effects_probe.py` C); ≤ 1 страницы в 10 с |
| CSSDA WOTD, WOTM, WOTY, Special Kudos | `/wotd-award-winners` (и `wotm-`, `woty-`, `/special-kudos-award-winners`), `/sites/<slug>/<id>/` | ссылка на сайт, «WOTD SEP 24» (год — из пути картинки `cdasites/2026/202609/…`) | `search cssda wotd`; только сайт, название, награда с датой; баллы, описания, дизайнеры, скриншоты — нет (условия) |
| FWA FOTD | главная (`caseMenu` — 3 верхних FOTD с адресом сайта), `/cases/<slug>` | кейсы студий, FOTD с датой, категории | `search fwa latest`; имена агентств — только имя |
| Recent (прежний Godly) | `/websites` | сайты с датой, категорией и тегами стека | `search recent latest`; превью — только наш снимок сайта |
| godly.design, Minimal Gallery, Landingfolio, Httpster | `/websites`, `/`, `/`, `/` | сайты с датой показа (кроме godly.design); у Landingfolio — отрасль и палитра | `search <галерея> latest`; Httpster не обновляется с 2025-05-26 |
| «Золотой сайт», «Рейтинг Рунета», Tagline | `goldensite.ru/results/`, `awards.ratingruneta.ru`, `tagline.ru/awards/` | русские победители по номинациям | ссылки; кэш других агентов уже есть (`99-raw/cache/goldensite.ru_results_*`, `awards.ratingruneta.ru_*`, `tagline.ru_awards_*`) |
| Dprofile | награды «Лучшее на Dprofile», «Dprofile рекомендует» | русские кейсы (мокапы) | только через клиент (режим «поиск») |

- Метка у награды — `[награда]` с датой: `(Awwwards SOTD 2026-08-14)`; награда — признание жюри, не конверсия и не удобство.
  Весы Awwwards: Design 40 %, Usability 30 %, Creativity 20 %, Content 10 %; CSSDA WOTD — средний балл > 8,0 (фундамент).
- Сайты с галерей, которые не пускают безголовый браузер или показывают «Not Supported» (так ответил
  `secure-the-unknown.cyera.com`), — отметка в выборке, а не обход.

### 4.2. `robots.txt` галерей (24.09.2026, по RFC 9309)

Awwwards: `Disallow: /websites/?` — только адреса с параметрами (`?page=`), SOTD без параметров разрешён; закрыты
`/inspiration/search`, `/search-websites`, `/gallery/`, `/vote/`, `/*/likes$`. `urllib.robotparser` отбрасывает `?` и
ошибочно закрывает всю `/websites/…` [проверено: самопроверка клиента]. Pinterest — закрыт для «*». Land-book прямо
приглашает ИИ-краулеров на общих правилах. One Page Love предлагает API вместо scraping и блокирует Bytespider, Amazonbot,
meta-externalagent. Файлы — `99-raw/cache/robots/<хост>.txt`.

## 5. Частоты и режимы по группам

| Группа | Режим клиента | Частота | Страниц в сутки |
|---|---|---|---|
| Dribbble, Dprofile | «поиск» по решению заказчика | 10 с + U(0; 6) с; порций ≤ 5 | 60 |
| Behance | `off` | — | 40 (при включении) |
| галереи без антибота (9 адаптеров: Awwwards, CSSDA, FWA, Recent, godly.design, Httpster, Minimal Gallery, Landingfolio, SiteInspire) | `public`: robots.txt + 10 с, 1 страница на запрос | 10 с + U(0; 6) с | 40 на галерею |
| галереи с антиботом, UI-библиотеки, пены, шейдеры | `manual`: ссылки заказчика → `get`, если хост пустит | 10 с на хост | 40 на хост |
| Are.na | API | ≤ 24 запроса в минуту | — |
| Vimeo, YouTube | только трек V | — | — |

## Частые ошибки

- «Публичная страница — значит, можно собирать» — условия почти всех площадок запрещают автоматический сбор (§3).
- Копирование скриншотов и описаний галереи в базу вместо ссылки на сайт (CSSDA прямо запрещает).
- Вывод «площадка мертва» по одному тайм-ауту через VPN (Awwwards, One Page Love, FWA 24.09) — перемерить.
- Обход Cloudflare Land-book и Lapa Ninja подменой UA или «стелсом» — запрещено; только ручные ссылки.
- Проверка `robots.txt` через `urllib.robotparser` при правилах с `?`, `*`, `$`.
- Награда жюри как довод «работает» — это признание, не конверсия.
- Шейдер Shadertoy без явной лицензии в коммерческом сайте — по умолчанию это CC BY-NC-SA 3.0; пен CodePen — без
  уведомления MIT; анимация LottieFiles «раз бесплатная, значит можно» — у Free-плана запрет коммерческого использования.
- Условия Cosmos по адресу `/terms` («Content not found» — это профиль пользователя) и вывод «условий нет»: искать ссылку в
  подвале или поиском (`/legal/terms-conditions`); так же у Land-book (`/terms_of_use`) и Lapa Ninja (`/policy/`).
- Ошибки агентов: поиск роликов на YouTube вне трека V (решение 6); доверие к листиклам «топ-20 галерей 2026».

## Чек-лист

- [ ] CRV-SRC-01 Для площадки есть запись в `sources.yaml` с `checked_at` не старше 6 месяцев?
- [ ] CRV-SRC-02 Режим клиента на площадке — решение заказчика (или `public` / `manual` по паспорту)?
- [ ] CRV-SRC-03 Условия прочитаны, ключевой пункт о доступе и копировании записан дословно с редакцией?
- [ ] CRV-SRC-04 `robots.txt` проверен по RFC 9309 для каждого адреса галереи?
- [ ] CRV-SRC-05 Частота ≤ 1 страницы в 10 с на площадку и дневной лимит соблюдены?
- [ ] CRV-SRC-06 Антибот не обходился (стоп и пауза, ручные ссылки)?
- [ ] CRV-SRC-07 Из галерей в выборку C ушли ссылки на сайты и награды с датой, а не картинки галерей?
- [ ] CRV-SRC-08 Код взят только с явной лицензией (MIT у Codrops, стандартная GSAP)?

## Открытые вопросы и противоречия

- **Три решения заказчика по условиям** (вопросы переданы оркестратором, ответа на 24.09 18:11 нет): Dribbble п. 7.7 —
  хранить ли имя автора со ссылкой; правила API Dribbble — «Scraping, copying, saving, or storing our data is strictly
  prohibited» против локальной библиотеки; FWA II.4 — «may not create a database in any form whatsoever of these web pages»
  (адаптер FWA в hold, снятые 19 записей остались во временной библиотеке опыта). Похожие широкие запреты — CSSDA («do not
  copy any content and data») и Awwwards («any unauthorized use or reproduction») `[спорно]`.
- Не прочитаны: форум three.js (JS); у SiteInspire, Recent,
  godly.design, Httpster, Typewolf, Rive, Milanote, One Page Love условий не найдено (ссылок нет, стандартные адреса — 404 или
  429). Условия CodePen — редакция 2017 года из блога CodePen; текущая `codepen.io/legal/tos/` закрыта для не-браузера.
  Shadertoy и LottieFiles — по снимкам Wayback (2025-10-01, 2026-07-12), не по живой странице.
- Adobe General Terms прочитаны только через WebFetch (два запроса дали одинаковые цитаты; сам `www.adobe.com` из этой сети
  не отвечает 40 с) — сверить с первоисточником при живом доступе.
- LottieFiles: «Lottie Simple License» у бесплатных ассетов против «Free Plan… strictly for non-commercial use» и
  «animations… obtained from Lottiefiles» в определении коммерческого использования — противоречие внутри условий `[спорно]`.
- Awwwards и One Page Love: в 16:00 — тайм-аут 40 с (VPN), в 18:08 — 200 за 5,7 и 2,9 с: единичный тайм-аут — не «мертва»;
  Typewolf в 18:08 — тайм-аут 40 с (перемерить).
- One Page Love: robots.txt обещает API с бесплатным ключом, страница API — лист ожидания.
- Refero и Mobbin дают API и MCP для «internal business use» — возможный законный путь «ассистента» для UI-референсов
  (платно; не проверено).
- Адаптеры галерей проверены офлайн и вживую (B/02); пагинация CSSDA и SiteInspire вживую не проверялась (хватило 1 страницы).

## Источники

- [S1] Dribbble. Terms of Service, «Updated March 17, 2025», https://dribbble.com/terms (WebFetch 2026-09-24) — первоисточник.
- [S2] Dribbble API v2: Overview, Shots, Terms & Guidelines, https://developer.dribbble.com/v2/ (кэш 2026-09-24).
- [S3] ООО «Дипрофайл». Пользовательское соглашение, https://dprofile.ru/terms (PDF, `Last-Modified` 2026-08-11); справка
  https://dprofile.ru/help (кэш 2026-09-24).
- [S4] Adobe. Behance Product Specific Terms, «Last updated June 18, 2024» (PDF, кэш 2026-09-24).
- [S5] Codrops. Licensing, https://tympanus.net/codrops/licensing/ (2026).
- [S6] Webflow. GSAP Standard License, https://gsap.com/community/standard-license (кэш 2026-09-24).
- [S7] Awwwards. Terms, https://www.awwwards.com/terms/; About evaluation (кэш других агентов `www.awwwards.com_about-evaluation_*`).
- [S8] CSS Design Awards. Terms, https://www.cssdesignawards.com/terms (кэш 2026-09-24).
- [S9] Minimal Gallery. Legal, «Last updated May, 2026», https://minimal.gallery/legal/.
- [S10] Landingfolio. Terms and Conditions; Licensing Agreement, https://www.landingfolio.com/legal/.
- [S11] Refero. Terms of Use, «Last updated: August 3, 2026», https://doc.refero.design/legal/terms-of-use.
- [S12] Mobbin. Terms, «Effective date: May 16, 2026», https://mobbin.com/terms.
- [S13] Page Flows. Terms, «Last updated: January 16th, 2025», https://pageflows.com/terms/.
- [S14] Vimeo. Terms of Service, «Last Updated: July 8, 2024», https://vimeo.com/terms.
- [S15] Are.na. Terms, https://www.are.na/terms; API v3 OpenAPI, https://api.are.na/v3/openapi.json (2026-09-24).
- [S16] Pinterest. Terms of Service, «Effective date: April 30, 2025»; Developer Guidelines, https://policy.pinterest.com/.
- [S17] Savee. Terms, https://savee.com/terms.
- [S18] One Page Love: robots.txt, https://onepagelove.com/api, https://onepagelove.com/llms.txt (2026-09-24).
- [S19] IETF RFC 9309 «Robots Exclusion Protocol» (сентябрь 2022).
- [S20] robots.txt 34 хостов — `99-raw/cache/robots/` (2026-09-24, фаза robots опыта B/01).
- [S21] Зонд B/01 — `99-raw/experiments/B/01-sources-probe/results.json` (главные 16 площадок в безголовом Brave).
- [S22] Живые запросы клиента: B/06 (Dribbble), B/07 (Dprofile).
- [S23] Разведка оркестратора `99-raw/notes/refs-recon-orchestrator-2026-09-24.md`; разведка архитектора
  `99-raw/notes/foundation-notes.md` (curl-статусы 05:52, условия Dribbble, критерии Awwwards и CSSDA).
- [S24] Справка Dprofile о наградах площадки, https://dprofile.ru/help (раздел «Жюри, награды»).
- [S25] Adobe. General Terms of Use, «Published October 3, 2025. Effective as of October 3, 2025», https://www.adobe.com/legal/terms.html
  (WebFetch ×2, 2026-09-24; прямой доступ из этой сети — тайм-аут) — разд. 1.2, 6, 17.
- [S26] CodePen. Terms of Service, «Last Update: December 11, 2017», https://blog.codepen.io/legal/terms-of-service/
  (`fetch.py`, 2026-09-24) — лицензия MIT у публичных пенов; актуальная `codepen.io/legal/tos/` — 403 не-браузеру.
- [S27] Shadertoy. Terms & Privacy, снимок Wayback 2025-10-01, https://web.archive.org/web/20251001020819/https://www.shadertoy.com/terms
  — лицензия по умолчанию CC BY-NC-SA 3.0.
- [S28] LottieFiles. Terms and Conditions, снимок Wayback 2026-07-12, https://lottiefiles.com/page/terms-and-conditions — роботы,
  data mining, Lottie Simple License, ограничение Free-плана.
- [S29] Landbook Sp. z o.o. Terms & Conditions, «Last updated: January 2026», https://land-book.com/terms_of_use (`fetch.py`).
- [S30] Lapa Ninja. Policy, «Last updated: September 13, 2026», https://www.lapa.ninja/policy/ (`fetch.py`).
- [S31] Cosmos. Terms & Conditions, «Last updated September 25, 2025», https://www.cosmos.so/legal/terms-conditions (`fetch.py`).
- [S32] Опыт B/02 — серверный HTML 7 галерей (1 страница, честный UA, 2026-09-24), jsdom 30.1.1: `99-raw/experiments/B/02-gallery-adapters/`.
