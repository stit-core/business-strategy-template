# 07 — стек реализации подачи (агент G, волна 2, 2026-09-24)

| Файл | О чём |
|---|---|
| `01-stack-choice.md` | Выбор стека: лестница стоимости (вес br и TBT при CPU ×4 для 33 сценариев), таблица «уровень × эффект → стек», GSAP (лицензия, SplitText, скиллы), Motion, CSS scroll-driven и scroll-triggered, Lenis, View Transitions и библиотеки переходов, WebGL без 3D, Lottie/dotLottie/Rive, Spline и Unicorn, от чего отказаться, фреймворки и SSR/SSG (SEO/GEO), лицензии, платформы заказчика `constraints.cms`, пакет kimi |
| `02-implementation-patterns.md` | Паттерны кода: прогрессивное улучшение, reduce и переключатель «меньше движения», ленивая инициализация, пауза, код-сплиттинг с прокладкой, контракт «модуль эффекта» и загрузчик, склейка ScrollTrigger + Lenis + VT + SplitText + Swup/Astro, самохостинг wasm и лицензии, шрифты, рецепты Тильды, WordPress, Битрикса, Webflow, Framer |
| `stack.yaml` | Машиночитаемый каталог: 51 запись (платформа, библиотеки, рантаймы, фреймворки, «не брать») с версией, лицензией, `size_br`, `init_tbt_ms`, поддержкой, `use_for` (все 29 id эффектов treatment.v0), уровнями, статусом, альтернативами, рисками, живостью + 8 платформ `constraints.cms`; валидатор `../../scripts/creative/validate_stack.py` |

Опыты: `99-raw/experiments/G/00-registry` (npm, GitHub, BCD/web-features), `01-lib-cost` (веса и TBT), `02-st-lenis-vt`
(совместимость), `03-effect-module` (контракт модуля эффекта).

## Выжимка

1. Стек выбирается снизу вверх: CSS/HTML (0 КБ) → свой код → малые библиотеки (3–8 КБ br, TBT 0) → GSAP (24–52 КБ, TBT ≤ 60 мс при CPU ×4) → WebGL → no-code (Spline 833 КБ).
2. L0 — без библиотек анимации; L1 — CSS по умолчанию, GSAP только для того, чего CSS не делает (pin со сложным сюжетом, split, Flip, синхрон с WebGL); L2 — GSAP-набор + Lenis + свой код в 150–200 КБ br.
3. CSS scroll-driven — во всех движках с Firefox 159 (2026-10-27): `@supports (… and (animation-range: 0% 100%))`; в старых версиях смысловое видно в конечном состоянии, без полифила; scroll-triggered — только Chrome 146+.
4. Same-document View Transitions — Baseline 2025-10-14; cross-document — Chrome 126+/Safari 18.2+ (Firefox — в Interop 2026), одной строкой CSS внутри медиазапроса reduce; Swup 4 — только для состояния между страницами; Barba — наследие.
5. GSAP бесплатен целиком (Webflow, 2025-04-30); нельзя: no-code-конструктор анимаций против Webflow и удаление `@license` из бандла.
6. Lenis 1.3 (1.3.27) — только L2, `anchors: true`, один цикл с `gsap.ticker`; после VT со сменой раскладки — `ScrollTrigger.refresh()` (проверено в Chromium и WebKit).
7. Шейдер-фон — paper-shaders (6 КБ) или OGL/WebGL2, не three; Lottie — `lottie-web` light или dotLottie с Worker; Rive — `canvas-lite` без текста и раскладок, Rive Renderer — только `webgl2`; wasm dotLottie и Rive — `setWasmUrl()` (по умолчанию CDN).
8. Модуль эффекта `{init, reduce, mobile, pause, resume, destroy, budget}` + загрузчик: в reduce GSAP и шейдер не грузятся (≈ 2 КБ против ≈ 35 КБ); тяжёлое — через прокладку (5,8 против 54 КБ).
9. Смысл страницы — в HTML сервера (статика/SSG/SSR), фреймворк по умолчанию — никакого (Vite 8), Astro 7 — многостраничник, Next 16 — если сайт уже на React.
10. Платформы: Тильда — Zero-анимация + T123 без сборки (на телефоне выкл.), WordPress/Битрикс — один собранный файл, Webflow — GSAP из настроек и ≤ 50 000 символов кода, Framer — Motion и Custom Code.
