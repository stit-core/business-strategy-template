# 03-live-sites-measured — замер эффектных сайтов 2025–2026 (агент C, волна 1)

## Выжимка (2026-09-24; 49 страниц десктопа, 15 телефонов, 22 пары reduce, 23 записи прокрутки)

1. Стек лидеров: GSAP 55 %, ScrollTrigger 47 %, Lenis активен у 35 %, three 45 %; продуктовые главные — React + Motion без GSAP.
2. CSS scroll-driven — 2 из 49, View Transitions объявлены — 1 из 49: прокрутку анимируют в JS.
3. Первый экран без видео — медиана 3,3 МБ (Q1 2,2), сессия 8,2 МБ, JS 694 КБ, LCP 2,0 с (лаборатория, десктоп).
4. Видео-поток > 5 МБ до прокрутки — у 15 из 49; автовидео с постером — 1 из 23, с паузой — 3 из 23.
5. Пауза у непрерывного движения — 1 из 20 страниц; переключателя «меньше движения» нет ни у кого.
6. Reduce уважают 4 из 21 страницы с движением (частично 4); WebGL под reduce рисует у 11 из 12.
7. Дисплей: максимум первого экрана 69 px, H1 72 px; font-size от vw у 76 %, clamp — у 33 %; H1 ≠ дисплей у 18 из 49.
8. Тёмный первый экран — 51 %; пурпур 270–320° — 8 %.
9. Ритм по записям: медиана 15 % пауз с движением; спокойные паузы между «вау» — у 21 из 23; «вау-переходов» 0–4.
10. Телефон: тот же JS, TBT 0,83 с при CPU ×4, LCP 7,2 с, H1 38 px; плавная прокрутка не отключается.

## Файлы

| Файл | Что внутри |
|---|---|
| `01-effects-sites-measured.md` | метод, выборка и отсев, библиотеки и конструкторы, анимации, WebGL и видео, типографика, цвет, веса и лабораторные CWV, reduced motion, плавная прокрутка, телефон, признаки уровней L0/L1/L2 в числах, «что копировать» |
| `02-motion-on-live-sites.md` | движение по записям прокрутки: hero, вход секций, скраб и закрепление, темп, одновременные движения, «вау», телефон, reduce |
| `03-reference-motion-probe.md` | замер движения референса и прототипа `motion_probe.py`: что снимается (CDP `Animation`, GSAP и ScrollTrigger, инлайн-стили по кадрам, прокрутка), паспорт движения, сверка `compare`, путь паспорта по этапам, допуски, этика, живая проверка |
| `sites.csv` | строка = страница × режим (`desktop`, `rm`, `mobile_thr`, `mobile_thr_rm`); колонки — ниже |
| `recordings/<slug>/` | записи прокрутки: `record[_mobile][_rm].json` и контактные листы `sheet_NN.jpg` 4×4 (без видео) |

Сырьё и опыты — `99-raw/experiments/C/` (`10-sites/<slug>/effects*.json` и `sheet*.jpg`, `00-exclusions`, `01-detector-signatures`,
`02-probe-lab`, `03-pilot`, `04-sample`, `05-scroll-record`, `run_batch.py`, `build_sites.py`). Утилиты — `99-raw/tools/effects_probe.py`,
`../../scripts/creative/scroll_record.py` (раздел в `../../scripts/creative/README.md`).

## Колонки `sites.csv`

| Колонка | Значение |
|---|---|
| `slug`, `url`, `group`, `genre`, `award`, `award_date`, `studio` | страница и откуда она (`group`: product-major, product-launch, award-campaign, award-culture, studio, ru-award, ai-control) |
| `level_observed`, `level_basis` | L0/L1/L2 **предварительно** (по приёмам `01-creative-direction/ambition-levels.yaml` v0) и найденные приёмы |
| `mode`, `net`, `locale`, `status` | режим; сеть `ru-direct`/`eu-vpn`/`unknown`; язык контекста; `ok`/`blocked`/`http-…` |
| `libs`, `builder`, `framework` | библиотеки с версиями (`gsap@3.15.0`), конструктор, фреймворк |
| `anim_total`, `anim_running_idle`, `anim_infinite_idle` | `getAnimations()` в покое: всего / бегущие по времени / бесконечные |
| `gsap_tweens`, `gsap_active_idle`, `gsap_targets`, `scrolltriggers`, `st_pinned`, `st_scrub` | GSAP: твины, активные в покое, элементы с `_gsap`, ScrollTrigger (с закреплением, со скрабом); «?» — GSAP есть, счёт недоступен |
| `scroll_driven_css`, `scroll_driven_waapi`, `sda_css_decl` | CSS scroll-driven в рантайме, WAAPI со ScrollTimeline (Motion), объявления `animation-timeline`/`*-timeline` в стилях |
| `view_transitions` | `mpa` (`@view-transition`), `names` (`view-transition-name`), `js` (`startViewTransition` в коде), `called`; `0` — нет |
| `sticky`, `pins` (`fixed_big` — только в сырье `effects*.json`) | `position: sticky`; `.pin-spacer`; fixed-элементы > 50 % экрана |
| `webgl`, `webgl_idle_dc` | созданные контексты WebGL/WebGPU; медиана вызовов отрисовки за кадр в покое |
| `video_n`, `video_autoplay`, `pause_control`, `motion_toggle` | видимые `<video>`; играющие без действия; пауза у движущегося (`all`/`some`/`none`/`-`); общий переключатель движения |
| `fonts`, `variable_fonts` | загруженные семейства; `N:оси` файлов с таблицей `fvar` |
| `display_max_px`, `display_max_first_px`, `h1_px`, `text_ge64_n`, `clamp`, `vw_font` | максимальный кегль (страница / первый экран), H1, текстов ≥ 64 px, font-size с clamp() и vw в стилях |
| `palette`, `dark` | 6 доминант первого экрана (k-means в OKLab) `#hex:%`; средняя светлота < 0,5 |
| `kb_first`, `kb_total`, `js_kb` | КБ к `load` + 8 с; за сессию; JS сжатый за сессию |
| `lcp_ms`, `lcp_el`, `cls`, `cls_scroll`, `tbt_ms` | лабораторные: LCP до прокрутки и элемент, CLS до и во время прокрутки, TBT до прокрутки |
| `loaf_scroll_ms`, `loaf_scroll_n`, `loaf_scroll_pct`, `fps_scroll` | Long Animation Frames при прокрутке: сумма, число, доля окна; частота rAF (потолок 60) |
| `rm_respected`, `rm_why` | итог пары с reduce и объяснение |
| `smooth_scroll`, `scroll_settle_ms` | lenis / locomotive / scrollsmoother / css-smooth / native; время успокоения после шага колеса |
| `cursor`, `marquee`, `autoslide`, `split_text`, `h_scroll`, `reveal` | свой курсор; бегущие строки; автопрокрутка без непрерывности; split-заголовки; горизонтальные секции; тексты, появившиеся при прокрутке |
| `rm_css`, `rm_js` | упоминаний `prefers-reduced-motion` в стилях; есть ли в JS |
| `motion_idle_pct`, `moving_regions_idle` | первый экран: доля меняющихся пикселей за 1 с, связные области |
| `motion_idle_max_rec`, `moving_regions_idle_max`, `windows_moving_pct` | по записи прокрутки: максимум по паузам, максимум областей, доля пауз с непрерывным движением |
| `cmp`, `gate`, `date`, `title` | cookie-баннер; ворота (`suspect:Enter` / `clicked:…`); время прогона; заголовок |

INP не измеряется (нет взаимодействий). Все числа — лаборатория, один прогон на режим (ограничения — `01` §1.3).
