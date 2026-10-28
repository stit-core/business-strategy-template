# Предложение соседним базам: что `blender` заменяет и на что ссылается

> **Решение владельца 23.09.2026: правки в соседние базы не вносить.** Записка остаётся справкой на будущее.

Волна 4 · агент S1 · 23.09.2026 · по заданию `99-raw/prompts/wave4-S-synthesis.md` п. 7. **Правки в `../ui/` и
`../ux/` не вносились** — только с согласия заказчика; ниже готовый текст и адреса. Основание: греп ссылок
`../ui/`, `../ux/` в папках 01–13 и дайджестах (46 строк в 17 файлах, §2), паспорт серии D2 (`06/02 §6`),
рецепты K (`12-recipes/`), аудит X (`99-raw/reports/wave4-X-audit.md` §11: «`../ui-research/12-ai-generated-ui/01 §6` заменяет эта база»).
Пути ниже — от файла соседней базы: из `ui-research/12-ai-generated-ui/01-…md` до этой базы — `../../3d/`.

## 1. Главное: раздел §6 `../ui/12-ai-generated-ui/01-image-models-for-ui.md` («Blender и 3D в конвейере»)

Раздел написан в ui-research без проверки руками (запись `PLAN.md` 22.09 22:05). Эта база проверила его запуском: паспорт серии —
D2/04 (серия из 4 иконок, метрики по брендовому материалу), рецепты K 01–10 (Blender 5.2.2, three r186). Предложение: §6 сократить
до границы и ссылок, таблицу §6.2 заменить ссылкой на проверенный паспорт.

### 1.1. Что заменить и чем

| Подраздел ui-research | Что сделать | Куда ссылаться (от `ui/12-ai-generated-ui/`) |
|---|---|---|
| §6, вступление | тезис «геометрия и свет задаются, а не угадываются» оставить; добавить ссылку на сценарии входа | `../../3d/README.md`; когда 3D вообще оправдан — `../../3d/01-web-3d-landscape/02-when-3d-budgets-loading.md` §1, §7 |
| §6.1 «Что отдавать Blender» | строки оставить, добавить колонку «рецепт» | устройство со скриншотом — `…/12-recipes/03-device-mockup.md`; серия 3D-иконок — `…/12-recipes/02-icon-series.md`; продуктовая сцена — `…/12-recipes/01-hero-product.md`, повтор объекта — `…/12-recipes/10-instance-field.md` (900 GN-инстансов — десятки КБ, 1 вызов); изометрия серией — `…/12-recipes/07-lowpoly-diorama.md`; абстрактный фон — `…/12-recipes/04-abstract-sculpture.md`, без Blender — `…/12-recipes/11-shader-background.md` |
| §6.2 «Паспорт 3D-серии» | таблицу заменить ссылкой и строкой «прежние значения не проверялись» (расхождения — §1.2) | `../../3d/06-materials-lighting-render/02-lighting-camera-composition.md` §6; паспорт по умолчанию для рецептов — `../../3d/12-recipes/00-how-to-use.md` §3 |
| §6.3 «Гибрид» (рендер → img2img) | оставить с пометкой `[не проверено]`: в 3d-research img2img поверх рендера не исследовался | сверка палитры рендера с hex — `../../3d/06-materials-lighting-render/03-render-engines-color.md` §2.3 (ΔE 1,8–1,9 под Khronos PBR Neutral) |
| §6.4 «Границы» | оставить (3D не на рабочих экранах — совпадает с позицией этой базы) | польза и вред 3D на странице — `../../3d/01-web-3d-landscape/02-when-3d-budgets-loading.md` §1 |
| выжимка п. 19, «Частые ошибки» п. 15, чек-лист п. 21 | текст оставить, дописать ссылку | `../../3d/README.md` |

### 1.2. Паспорт серии: черновик ui-research против проверенного (D2 `06/02 §6`, K `12/00 §3`)

| Поле | Черновик `12/01 §6.2` | Проверено в 3d-research |
|---|---|---|
| нормировка | — | радиус описанной сферы 0,5 м (масштаб корня): одинаковые свет и тень при разных формах |
| камера | орто-изометрия 30°, 50 мм для перспективных кадров | иконки и продукт — 85 мм, азимут 35°, угол места 25°, `frame_camera` с полем 1,35; изометрия — `ORTHO`, наклон **35,264°** (не 30°), азимут 45° (`06/02 §5.1`) |
| свет | key сверху-слева 45°, fill 20 % справа, нейтральный HDRI | key/fill/rim от радиуса объекта, E_key 2 Вт/м² под Neutral; мир — цвет фона страницы × 0,25 |
| вид (тонмаппинг) | — | Khronos PBR Neutral, look None, экспозиция 0 (AgX выбеливает бренд: C* 38–44 против 84–93) |
| материалы | матовый пластик roughness 0,45, металл только на акценте | primary + accent из палитры, roughness 0,3–0,35, coat 0,3 |
| палитра | 6–10 hex карточки стиля, акцент ≤ 15 % площади | те же hex, в сцену — через `from_srgb_to_scene_linear`; акцент ≤ 15–25 % площади |
| кадр и фон | 1024 × 1024, прозрачный фон | 512–1024², прозрачный фон + ловец теней (Cycles 32 сэмпла + OIDN), 3–6 с на иконку |
| поля | 8 % от стороны | высота объекта 44–63 % кадра (поле 1,35); поля по типу кадра 8–15 % (`11-evaluation-qa/05-master-checklist.md`, CAM-02) |
| тень | контактная, мягкая, альфа ≤ 0,15, отдельным слоем | ловцом теней в том же PNG RGBA; разброс тени по серии 0,9 L* (без паспорта 6,4) |
| выход | — | PNG RGBA 8 бит → AVIF/WebP (`06-materials-lighting-render/04-outputs-for-web.md`) |
| имена | `icon-<name>-3d.png`, `device-<model>-<angle>.png` | `icon-<name>-3d.png`, коллекция `ICON`, служебное — вне экспорта |
| где хранить | в файле сцены и описании пайплайна, не в промте | так же: файл рядом со скриптом (словарь `P` для `build(P)`), не в промте |

Итог замера D2/04 (4 иконки): по паспорту — L* освещённой грани 45,1–47,4 (hex 48,7), тень 39,7–40,6, C* 84–93; «наивно»
(реальные размеры, разные камеры, солнце + мир 0,5, AgX) — L* 61–64, тень 53–60, C* 38–44.

### 1.3. Готовый текст для §6 (если заказчик согласует)

```markdown
## 6. Blender и 3D в конвейере

Проверенная база по 3D для сайтов — `../../3d/` (Blender 5.2.2, three r186; сценарии входа — её `README.md`).
Здесь — только граница: растровый генератор не держит геометрию, ракурс и свет серии, поэтому эти задачи отдаются Blender.

| Задача | Рецепт `../../3d/12-recipes/` |
|---|---|
| рендер устройства со скриншотом на экране | `03-device-mockup.md` |
| серия 3D-иконок | `02-icon-series.md` (паспорт — `../../3d/06-materials-lighting-render/02-lighting-camera-composition.md` §6) |
| продуктовая сцена, повторяющийся объект | `01-hero-product.md`, `10-instance-field.md` |
| изометрические иллюстрации серией | `07-lowpoly-diorama.md` |
| абстрактный 3D-фон | `04-abstract-sculpture.md`; без Blender — `11-shader-background.md` |

Паспорт 3D-серии этого раздела заменён проверенным (ссылка выше); прежние значения (изометрия 30°, roughness 0,45, тень
альфа ≤ 0,15) не проверялись. Гибрид «рендер → img2img → сверка палитры» — `[не проверено]` ни здесь, ни в 3d-research.
На рабочих экранах приложения 3D не нужен (`../07-iconography-imagery/02` §1).
```

## 2. Где 3d-research ссылается на соседей (не переименовывать без предупреждения)

| Цель в соседней базе | Файлы 3d-research (число строк) | Зачем |
|---|---|---|
| `ui-research/12-ai-generated-ui/01` (§6, §6.2, «частые ошибки») | `04-ai-agents-mcp/03-research-llm-3d.md`, `04-agent-operating-protocol.md` (2), `06-materials-lighting-render/02-lighting-camera-composition.md`, `12-recipes/00-how-to-use.md` | исходный черновик паспорта, заменённый §6 D2 |
| `ui/12-ai-generated-ui/03-research-2024-2026.md` §6.1 | `04-ai-agents-mcp/03-research-llm-3d.md` | «судья без рубрики — шум» |
| `ui/07-iconography-imagery/02-illustration-system-avatars-images.md` (§2.5, §5, §5.2) и папка | `01-web-3d-landscape/01-effects-catalog.md`, `05-blender-deliverables-map.md`, `04-ai-agents-mcp/04-agent-operating-protocol.md`, `05-modeling/01-form-and-aesthetics.md` (4), `12-recipes/02-icon-series.md` (2) | 2D против 3D, паспорт серии иллюстраций, иконки 16–32 px — SVG |
| `ui/08-motion/` (`01-durations-easings-springs.md`, `03-reduced-motion-and-motion-tokens.md`) | `01-web-3d-landscape/01`, `02`; `07-animation/01` (3), `03` (2), `04` (5), `README.md`; `09-web-runtime/03` (5), `05` (2) | длительности, пружины, reduced motion, WCAG 2.2.2/2.3.3 — не дублируем |
| `ui/11-styles-trends/` | `01-web-3d-landscape/01-effects-catalog.md` (2) | стили и «нейрослоп» |
| `ux/08-accessibility/` (`01-wcag22-as-build-rules.md`, `02-keyboard-focus-semantics.md`) | `01-web-3d-landscape/01` (2), `02` (2); `09-web-runtime/05` | WCAG, фокус, клавиатура |
| `ux/06-feedback-states-motion/` (`02-system-status-and-waiting.md`, `03-motion-and-microinteractions.md`) | `01-web-3d-landscape/02`; `09-web-runtime/01`, `05` | ожидание загрузки, микровзаимодействия |
| `ui/` (граница «цвет интерфейса — там») | дайджест `91-videos/digests/Qj1FK8n7WgY.md` (2) | гармонии и доли цвета рендера против цвета UI |

## 3. Что предложить соседям добавить (обратные ссылки; решение — за заказчиком)

1. **`ux/08-accessibility/01-wcag22-as-build-rules.md` и `06-feedback-states-motion/02-system-status-and-waiting.md`** — про
   canvas и 3D там нет ни слова (вывод F1, `09-web-runtime/05-performance-a11y-fallbacks.md`, шапка). Строка-указатель: доступность
   3D-блока — `../../3d/09-web-runtime/05-performance-a11y-fallbacks.md` §5 (смысл в HTML, движение, клавиатура у
   вьюера, ожидание загрузки) и `../../3d/01-web-3d-landscape/02-when-3d-budgets-loading.md` §6 (SEO и доступность).
2. **`ui/08-motion/03-reduced-motion-and-motion-tokens.md`** — 3D-движение под `prefers-reduced-motion` (прокрутка, клипы,
   пауза цикла отрисовки): `../../3d/09-web-runtime/03-scroll-interaction-animation.md`,
   `../../3d/07-animation/04-js-vs-blender-vs-prerender.md`.
3. **`ui/07-iconography-imagery/02-illustration-system-avatars-images.md` §5** (паспорт серии 2D/3D) — ссылка на
   `../../3d/12-recipes/02-icon-series.md` и `06-materials-lighting-render/02-lighting-camera-composition.md` §6.
4. **`ui/11-styles-trends/04-anti-slop-ui.md`** — клише 3D 2024–2026 (стеклянный тор на градиенте и т. п.):
   `../../3d/01-web-3d-landscape/01-effects-catalog.md`, выжимка п. 26.
5. **`ui/12-ai-generated-ui/03-research-2024-2026.md` §6.1** — практическое применение «судья после кода»:
   `../../3d/11-evaluation-qa/02-render-critique.md` §4.2.
6. Видео (лежат в `3d-research/91-videos/`): дайджест `Qj1FK8n7WgY` (Blender Guru, «Understanding Color») — гармонии и доли цвета,
   полезен `ui` для цвета иллюстраций; транскрипт `LSNQuFEDOyQ` (Freya Holmér, «Lerp smoothing is broken», без дайджеста) —
   математика сглаживания движения (`damp` вместо `lerp` с долей кадра), кандидат для `ui-research/08-motion/01`.

## 4. Порядок, если заказчик согласует

Агент соседней базы вносит §1.3 и строки §3, прогоняет её `../../scripts/maint/check_links.py` (пути `../../3d-research/…` у неё
не проверяются — сверить глазами), отмечает правку в её `PLAN.md`. Со стороны 3d-research после этого менять нечего: ссылки
§2 ведут на файлы, которые остаются на месте (при переименовании у соседей — обновить строки §2 грепом `ui/`, `ux/`).
