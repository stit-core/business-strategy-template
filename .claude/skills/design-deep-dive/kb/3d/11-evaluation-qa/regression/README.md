# regression/ — регрессионный набор J (волна 3)

- `manifest.json` — 33 записи: 17 эталонов-ассетов (C1/12 ×8, D1 ×5, D2/04, H ×3), 3 страницы (F1, F2), 4 отрицательных контроля
  (C1/11 ×3, H/10 f), 9 эталонов K (в работе). Поля: `id, tier, archetype, source, brief, passport, build, blend, glb, page,
  anim_check, anim_expect, expect_codes, ref_images, numbers`. Пути — от корня базы; файлы не копируются (только ссылки).
- `make_manifest.py` — собрать манифест заново (проверяет, что пути существуют).
- `run_set.py` — прогон через `../../scripts/3d/qa_pipeline.py` (+ `three_probe.py` для анимации) и сравнение с базовой линией:
  `python3 ../../scripts/3d/regression/run_set.py --label baseline --tiers core,negative,k` (57 с);
  `… --label new --compare baseline` → список регрессий, код выхода 1.
- `results_baseline.json` — базовая линия 23.09.2026 (Blender 5.2.2, three r186); `results_negcheck.json` — прогон контролей из
  блока кода `../04-regression-set.md §2`.
Описание, метрики версии агента и правила «что считать регрессией» — `../04-regression-set.md`.
