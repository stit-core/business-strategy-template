# M/10 — машиночитаемые рецепты: генератор, схема, валидатор

- `make_recipes.py` → `14-recipes/recipes/*.yaml` (17) + `recipe.schema.json`; `venv-D2/bin/python validate_recipes.py` → `validate_report.json`.
- Валидатор: схема (jsonschema 2020-12), существование `doc`, `spec.example`, заданий, доказательств, шаблонов, утилит в командах;
  коды задач — из таксономии `_common.md`; код маршрута — в `13-routing-matrix/routing.yaml` (v1; до поправки X2 — v0); ключи порогов — в
  `11-evaluation-qa/thresholds.yaml`; цена каждого шага маршрута с моделью polza — `polza_catalog.py price` (снимок «последний»).
- Результат: 17/17 без ошибок, 27 цен сверено (поправка X2 24.09.2026: было «28», в `validate_report.json` M — тоже 27); первый прогон нашёл 2 ошибки (Seedance 2 Mini 12,8 против 12,825 в каталоге —
  округление в routing v0; ложное срабатывание поиска утилиты в пути `../3d-research/…` — исправлен шаблон).
- **Поправка X2 (24.09.2026)**: `format-family` — маршрут по `routing.yaml` v1 и заданию H-08 (NB2 1K 9:16 4,8 ₽ + Sunburst 1K 21:9
  4,0 ₽; было из v0 — Flare 2K 7 ₽ и NB2 2K 7,2 ₽, которых H-08 не проверяет): правка в `make_recipes.py`, YAML перегенерирован
  (остальные 16 файлов побайтно те же); валидатор читает v1 — 17/17, 27 цен.
- **Поправка X2 (24.09.2026), 2**: `hero-loop` — шаг `lossless` снят, `audit-web --master loop_mezz.mp4`: `video_loop_check.py trim` 0.2.1
  сам пишет мезонин без потерь (`-qp 0`); перегенерирован только `hero-loop.yaml`, валидатор — 17/17, 27 цен.
- **Сессия 5 (25.09.2026, агент Q) — поправки фазы 5**: `illustration-series` — id Flare `openai/gpt-image-2.5-flare` (старого id в
  снимке `2026-09-25_1411` нет — было 2 предупреждения «калькулятор не ответил»); `hero-loop` — шаг `rife-bridge` (RIFE-мост 8 кадров
  вместо кроссфейда хвоста), шаг маршрута «финал 1080p 8 с» (45 ₽, MS-05), роли Omni и Kling std — «не для петли» (в `routing.yaml`
  v2 — `not`); `abstract-background` — видео по кадру Seedance 1.5 Pro 720p (10,5 ₽, основной в v2), Seedance 2 Mini — запас;
  `status.generation: checked` у 8 рецептов, где фаза 5 прогнала генерацию (hero-loop, hero-pair, illustration-series, icon3d-series,
  pdp-packshot-scene, product-in-interior, format-family, recraft-illustration); в `numbers` — числа фазы 5 с путями доказательств у
  15 рецептов; цены Recraft 8,74 → 8,83. Скрипт правок — `99-raw/notes/session5/Q-work/patch_recipes_phase5.py`; `make_recipes.py`
  эти правки не знает. Валидатор читает `routing.yaml` v2: **17/17 без ошибок, 29 цен сверено**.
