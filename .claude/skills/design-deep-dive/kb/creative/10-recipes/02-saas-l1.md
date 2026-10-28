# Рецепт 02 · Лендинг SaaS · L1 — «продукт в движении»: интерфейс сам делает работу по прокрутке

Волна 3 · агент J · 2026-09-25 · входы: site «Окошко» (`saas-okoshko`), A `art-direction-okoshko.json`, I `okoshko-home.*` ·
рабочий пример `examples/l1-sverka/` (сверка платежей; 0 КБ JS; ворота K 0/0/0) · Chromium 153, WebKit 26.6 ·
YAML — `recipes/02-saas-l1.recipe.yaml`

## Выжимка для агента

1. **Фирменный приём L1 — одна sticky-сцена ≤ 150vh, где интерфейс продукта выполняет главную работу** (сверяет, записывает, собирает). `[проверено]` → §5
2. **Сцена — на CSS scroll-driven**: `view-timeline` секции, `animation-range: contain`, доли на элемент через `calc(8% + var(--i) * 15%)`; 0 КБ JS. `[проверено]` → §6
3. **Всё начальное состояние — внутри `@supports ((animation-timeline: scroll()) and (animation-range: 0% 100%))` и `no-preference`**: без поддержки (Safari до 26, Firefox до 159) — конечный кадр. `[проверено]` → §6
4. **Интерфейс — HTML-фрагмент, не скриншот в рамке браузера** (`cliche:dashboard-in-browser-frame`): текст ищется, масштабируется, анимируется. `[практика]` → §7
5. **Первый экран продолжает сцену**: верх интерфейса виден над сгибом (sticky-коробка прижата к верху, `padding-top: 7svh`). `[проверено]` → §4
6. **Hero по центру законен при ≤ 4 элементах** (надзаголовок, H1, лид, кнопка с примечанием). `[практика: D, поправка PLAN]` → §4
7. **H1 ≤ 2–3 строк**: антиква 600 с `max-width: 16ch`; при 13ch — 4 строки (прогон 1). `[проверено]` → §8
8. **Счётчик — только внутри сцены и из данных сцены**, не на цифрах доверия; делать **стопкой цифр** (6 `<span>` в одной ячейке грида, у каждой свой `animation-range`), а не `@property <integer>` + `counter()`: WebKit 26.6 не обновляет `counter()` от анимированного свойства — на станциях стоял 0, когда пары уже сошлись. `[проверено: J/03, J/05 — WebKit 26.6 Playwright]` → §6
9. **Цвета статуса — в интерфейсе**: зелёный «сошлось» — бренд, красный «нет счёта» — одна строка; страница не красная. `[мнение]` → §2
10. **Цены, тарифы, FAQ, финал — L0 без эффектов**; финальный призыв — полоса без формы (L1 допускает accent, не нужен). `[практика: A]` → §4
11. **Шрифты ≤ 250 КБ**: Literata opsz (172 КБ) + Commissioner (63 КБ) = 230 КБ — предел; без opsz — 80 КБ. `[проверено]` → §8
12. **Переключатель движения на L1 не нужен**, если петель нет и scroll-linked секция одна (E 05/01 §4.4). `[практика: E]` → §5
13. **Проверка — `motion_check.py --level L1 --spec`**; станции sticky-сцены — долей `at` и кадром, не DOM-якорем. `[проверено]` → §8

## 1. Бриф и уровень

`page_type: landing-saas`, `budget_profile: landing-saas@L1`, трафик — поиск (solution-aware), соцсети, рекомендации; действие —
регистрация пробного периода (`start-trial`). L1 — умолчание лендинга (решение заказчика п. 13). Не бери L1-сцену, если продукт
нельзя показать действием за 5–6 шагов (тогда L0 + скриншоты) или если главный трафик — горячий мобильный на тарифы.

## 2. Концепция

- **Тезис** (пример): «Движется только сверка: платежи банка встают напротив своих счетов, линии связывают пары, один платёж
  остаётся красным — остальная страница стоит». Для «Окошка» A: «журнал записи, который ведёт себя сам» — та же схема.
- **История**: герой — бухгалтер; конфликт — триста строк выписки руками; развязка — сервис оставляет одну строку.
- **Направления**: A «Книга учёта на холодной бумаге» (антиква, зелёный — выбран); B «Табло» (моно для данных, тёмный);
  C «Канон SaaS» (гротеск, градиент) — отклонено как почерк генератора (`cliche:purple-gradient-hero`).

## 3. Подсказки мудборда

| Роль | Что искать | Взять | Не брать |
|---|---|---|---|
| product | интерфейсы сервисов в действии (Refero, Mobbin — B) | реальные состояния: пусто → в работе → готово | «идеальный» дашборд с графиками ни о чём |
| type | антиква в интерфейсах и отчётах (Literata opsz, D) | цифры сумм антиквой `lining-nums tabular-nums` | курсивный акцент в H1 (`cliche:accent-word-headline`) |
| motion | sticky-сцены продуктовых страниц (Linear, Stripe — C: тихие, «вау» с прокрутки) | одна сцена, остальное стоит | появление всех секций |

## 4. План страницы

Макроструктура `workbench` (site 02 §1.1), первый экран `offer-cta`, 9 секций. Полный план с слотами — site
`../site/10-playbooks-contracts/examples/saas-okoshko/plans/home.yaml`.

| Секция | Блок | Роль (visual) | Уровень | Подача |
|---|---|---|---|---|
| header | `block:header` | chrome | L0 | логотип, 3 якоря, «Войти» — ссылка, призыв |
| hero | `block:hero-text` | accent | L1 | по центру, ≤ 4 элементов; лид и кнопка — появление 560 мс |
| product-demo | `block:product-showcase` | **peak** | L1 | sticky-книга 250svh: 5 пар сходятся, 1 красная |
| proof-stats | `block:stat-strip` | calm | L0 | 3 числа фактами |
| how-it-works | `block:steps` | support | L0 | 3 шага без анимации |
| pricing | `block:pricing-cards` | calm | L0 | 3 тарифа, средний выделен контуром |
| faq | `block:faq` | calm | L0 | ответ проявляется |
| final-cta | `block:cta-band` | calm | L0 | заголовок + кнопка |
| footer | `block:footer` | chrome | L0 | реквизиты, вход |

## 5. Подача: treatment и motion-spec

Спецификация — `examples/l1-sverka/motion-spec.yaml` (0 ошибок `spec_check.py`); для «Окошка» — I `okoshko-home.motion-spec.yaml`
(sticky и смена состояний). Хореография: hero — one-shot (лид, кнопка); product-demo — scroll-linked (строка счёта `translate
0 calc(var(--from) * 100%) → 0` в первых 70 % окна пары, фон `surface → match` в последних 28 %, линия `stroke-dashoffset 1 → 0`
во второй половине, счётчик — цифры стопкой, цифра k видна, пока сошлись k пар (0 до 22 %, 5 с 82 %; J2), флаг «нет счёта» на 84–94 %); станции 0,24 · 0,54 · 0,94; reduce —
конечное состояние; телефон — строки 54 px, имя и сумма в две строки, сцена 130vh.

## 6. Эффекты, стек и код

Эффекты: `effect:pin-scrub-story` (реализация sticky + view-timeline, без GSAP), `effect:svg-line-draw`, `effect:counter-up`
(внутри сцены), `effect:hero-entrance-once`. Стек — CSS; GSAP нужен, только если сцена длиннее одной секции или нужна синхронизация
с WebGL (G 01 §2). Закрепление ScrollTrigger `pin` без `pinType: 'transform'` даёт CLS 1,6–2,0 (E/02) — sticky даёт 0.

```css
/* Chrome 153 · WebKit 26.6 (Playwright) · без SDA (Safari до 26, Firefox до 159) — конечный кадр · 2026-09-25 · [проверено]
   Safari на устройстве — [не проверено]; var() в animation-range в WebKit 26.6 работает (строки и линии совпали с Chromium) */
.demo { height: 250svh; }                                    /* 150svh прокрутки сцены (L1: ≤ 150vh) */
.demo__sticky { position: sticky; top: 0; height: 100svh; }
/* счётчик: <b class="demo__n"><span>0</span>…<span>5</span></b> — цифры стопкой, без JS и без @property */
.demo__n { display: inline-grid; } .demo__n > span { grid-area: 1 / 1; } .demo__n > span:not(:last-child) { opacity: 0; }
@supports ((animation-timeline: scroll()) and (animation-range: 0% 100%)) {
  @media (prefers-reduced-motion: no-preference) {
    .demo { view-timeline: --demo block; }
    .docs .row { animation: slot linear both, matched linear both; animation-timeline: --demo, --demo;
      animation-range: contain calc(8% + var(--i) * 15%) contain calc(24% + var(--i) * 15%); }
    .demo__n > span { opacity: 0; animation: digit linear none; animation-timeline: --demo; }   /* цифра k — пока сошлись k пар */
    .demo__n > span:nth-child(1) { animation-fill-mode: backwards; animation-range: contain 0% contain 22%; }
    .demo__n > span:nth-child(2) { animation-range: contain 22% contain 37%; }   /* …(3) 37–52, (4) 52–67, (5) 67–82 */
    .demo__n > span:nth-child(6) { animation-fill-mode: forwards; animation-range: contain 82% contain 100%; }
    /* границы — на середине позеленения пары (22 + 15·i %), не на её конце: граница ровно на станции даёт «0» и «2» вместо 1 и 3 */
  }
}
@keyframes slot { from { translate: 0 calc(var(--from, 0) * 100%); } 70%, to { translate: 0 0; } }
@keyframes digit { from, to { opacity: 1; } }
```

Антипример (J, до J2): `@property --matched { syntax: "<integer>" }` + `counter-reset: m var(--matched)` + `@keyframes count { from
{ --matched: 0 } to { --matched: 5 } }` — в Chromium 153 работает, в WebKit 26.6 счётчик стоит на 0 до конца отрезка (`J/05-webkit/sheet-l1.jpg`).

## 7. Ассеты и тексты

| Слот | Лестница | Источник | Код | Бюджет |
|---|---|---|---|---|
| screenshot (интерфейс сцены) | html | code | — (фрагмент DOM из реального UI продукта) | 0 КБ картинок |
| logo, favicon | svg | real | — | ≤ 10 КБ |
| og-image | image | template | `IMG-TEXT-CYR` | ≤ 300 КБ |
| скриншоты функций (если нужны) | image | real | `IMG-MOCKUP` без рамки устройства | ≤ 150 КБ |

Тексты — copy-deck v1 (`../text/10-templates-recipes/examples/ru-okoshko-saas.yaml`): `eyebrow`, `headline` (≤ 36 знаков),
`subheadline` («обычно три-пять строк вместо трёхсот» — `fact:`), `cta-label`, `cta-note` (без карты), `stat-*`, `step-*`,
`pricing-*`, `faq-*`; подписи внутри интерфейса (контрагенты, суммы) — демо-данные с пометкой, в проекте — обезличенные реальные.

## 8. Бюджет и ворота

| Ворота (K) | Пример J/03 | Порог L1 | Вердикт |
|---|---|---|---|
| EG-WEIGHT-01 JS эффектов, КБ br | 0 | ≤ 100 (spec 0) | PASS |
| EG-WEIGHT-07 шрифты, КБ | 229,9 | ≤ 250 | PASS (запас 20 КБ) |
| EG-WEIGHT-08/09 первый экран / сессия, МБ | 0,236 / 0,236 | ≤ 2,0–3,5 / ≤ 5–10 | PASS |
| EG-PERF-01 LoAF, % | 0 / 0 | ≤ 2 / 10 | PASS |
| EG-PERF-02 CLS прокрутки | 0 / 0 | ≤ 0,1 | PASS (sticky) |
| EG-PERF-06 LCP лаб., мс | 96 / 120 | ≤ 2500 | PASS |
| EG-A11Y-06/10 reduce: движение / скрытое | 0 / 0 | ≤ 0,3 / 0 | PASS |
| EG-A11Y-17 петель в зоне | 0 | ≤ 2 (spec 0) | PASS |
| **Итог motion_check L1** | **FAIL 0 (B 0, S 0, D 0), N/A 2** | 0 B, 0 S | **прошёл** |
| Сверка motion-spec | моменты 3/3 PASS; станции с DOM-якорем — неприменимо (переведены на `at`) | — | — |

**Перепрогон J2** (2026-09-25 04:26, после счётчика стопкой цифр): motion_check 0.1.3, ворота v0.2, 5 режимов — **B 0, S 0, D 0**
(N/A 5), F83 h1 15,6:1 (`99-raw/experiments/J/03-l1-sverka/motion-0.1.3/gates.md`); сверка spec — 9 FAIL станций (десктоп, телефон,
reduce × 3) ложные: цель `[data-moment=ledger-match]` внутри sticky-слоя сама не движется (край +224 px), кадры станций — 1 · 3 · 5 пар и
счётчик совпали (отчёт J `99-raw/reports/wave3-J-report.md` §11.3; предложение K там же, §11.8). Статус `verified` в силе.

## 9. Решения о клише

| id | Приём | Решение | Почему |
|---|---|---|---|
| d-frame | `cliche:dashboard-in-browser-frame` | avoid | интерфейс — живой HTML без рамки устройства |
| d-serif | `cliche:cream-serif-terracotta` | twist | антиква — язык бухгалтерской книги, бумага холодная серая, акцент зелёный, не терракота |
| d-accent-word | `cliche:accent-word-headline` | avoid | в H1 нет выделенного слова; цвет — только у статусов |
| d-mono | `cliche:mono-captions` | avoid | суммы — антиквой с табличными цифрами, моно не нужен |

## Частые ошибки

1. Скриншот дашборда в рамке браузера с тенью в hero — почерк генераторов (Kilo, K3 — H 02 §4).
2. Появление карточек тарифов и FAQ — «продукт в движении» превращается в «всё в движении».
3. ScrollTrigger `pin` для одной декоративной сцены — 42 КБ JS и CLS 1,6–2,0 вместо sticky с 0.
4. Начальное состояние сцены вне `@supports` — в браузере без SDA книга навсегда «перемешана».
5. Счётчик пользователей «0 → 12 000» в hero — число доверия анимируют ради движения.
6. Антиква + крем + терракота — «редакционный люкс» генератора; антиква на холодной бумаге — поворот.
7. Шрифт с opsz без учёта бюджета: 172 КБ на одну гарнитуру.

## Чек-лист

- [ ] Сцена одна, ≤ 150vh прокрутки, показывает работу продукта (не абстракцию)?
- [ ] Интерфейс — HTML, без рамки устройства; данные демо помечены?
- [ ] Начальное состояние — в `@supports` + `no-preference`; без поддержки и в reduce — конечный кадр?
- [ ] H1 ≤ 3 строк на 1440 и 390; первый экран показывает начало сцены?
- [ ] Тарифы, FAQ, финал — без эффектов; JS подачи 0–100 КБ; шрифты ≤ 250 КБ?
- [ ] `motion_check.py --level L1 --spec` → 0 B, 0 S; кадры станций глазами?

## Открытые вопросы и противоречия

- `var()` внутри `animation-range` (calc с долей элемента) — проверено в Chromium 153 и кадрами WebKit 26.6 Playwright (J2,
  `99-raw/experiments/J/05-webkit/`: строки и линии совпали); Safari на устройстве — «Что проверить в живой фазе» (J № 5, № 12).
- Шаблон I «Окошко» — sticky со сменой состояний; пример J — сдвиг строк и линии: оба укладываются в `pin-scrub-story` L1; в `effects.yaml`
  v0.2 у него уже есть вариант `css` (sticky + view-timeline, 0 КБ JS, `lab/pin-scrub-story/?v=css`) — просьба к F2 закрыта.

## Источники

- [S1] site — `../../site/10-playbooks-contracts/02-playbooks-landings.md` §4; пример `saas-okoshko`, 2026-09-24.
- [S2] I — `../09-ai-execution-evaluation/examples/okoshko-home.*`, `motion-spec.schema.json` v1, 2026-09-25.
- [S3] E — `../05-motion/02-choreography-scroll-transitions.md` §3.3, §3.5 (E/02: sticky CLS 0, pin 1,6–2,0), §4.
- [S4] G — `../07-stack-implementation/01-stack-choice.md` §2; `02-implementation-patterns.md` §1.2.
- [S5] H — `../08-uniqueness-anti-slop/cliche-registry.yaml` (dashboard-in-browser-frame, cream-serif-terracotta, accent-word-headline).
- [S6] D — `../04-visual-language/cyrillic-display-fonts.yaml` (Literata opsz, трекинг ≥ 0; Commissioner без tnum).
- [S7] K — `effect-gates.yaml` v0.1, `motion_check.py` 0.1 (перепрогон J2 — v0.2, 0.1.3); опыт J/03 — `99-raw/experiments/J/03-l1-sverka/`.
