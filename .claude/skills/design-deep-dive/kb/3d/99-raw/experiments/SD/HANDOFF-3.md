# SD4 · HANDOFF-3 («Сдано», 15-showcase) — 26.09.2026 ≈ 06:35

Агент SD4 продолжил после SD3 (завис 01:58 на цикле ffmpeg без `-nostdin`, остановлен оркестратором 05:40, HANDOFF-3 не
писал; его ход восстановлен в `NOTES.md` «СТАТУС SD3»). Корни: `R=/home/mm/Документы/app-design/blender-research`,
`X=$R/99-raw/experiments/SD`, `S=$R/15-showcase/sdano`, `CR=/home/mm/Документы/app-design/creative-research`.
Читать первым: KIT.md → этот файл → `$S/README.md` (итог, ворота, рецепт) → `NOTES.md` (СТАТУС SD4, решения SD4).
Процессы SD4 закрыты (проверено `ps`/`ss`: ни браузеров, ни серверов SD; :8790/:8791 — голосование оркестратора).

## 1. Готово по пунктам задания SD4

| Пункт | Статус | Где / что |
|---|---|---|
| 1. motion_check C `fail_S 1` | **сделано** | `EG-A11Y-17 mob` = 1 при бюджете спеки 0: однократный показ фонаря на телефоне (шаг прокрутки 1, WebGL рисует в паузе, 17,8 % пикселей за 1 с). Правка — спека `$X/pagebuild/motion-spec-c.yaml` (`loops_in_view_max` 0 → 1 = норма L1 телефона, комментарий в файле) → копия `$S/c-hybrid/motion-spec.yaml`, `spec_check` 0/0/0. Перепрогон `run_gates.sh c-hybrid L1 all` 05:45–05:56 → gate_check OK, motion **0/0/0**, marketing 0/0/39. Прогон SD3 — `$X/gates/c-hybrid_sd3-0455/` |
| 2. Штамп-клип | **сделано** (SD3 нашёл причину) | в headless-shell с GPU-флагами декодер VP9 падает (err 3, застывание 0,29–0,36 с), без флагов клип доигрывает 1,584 с (`$X/shots/sd3_video/video_probe.json`). Кадр судьи `act-stamp` у B/C — реальный конец клипа (снят браузером без GPU-флагов, `ended`); лист кадров — `$S/judge/work__stamp-clip-sheet.png`; в README — «ограничение проверки, не дефект» |
| 3. fx_probe C | **сделано** (+ свой точный замер) | `$X/gates/c-hybrid/fx/fx_index.json`: 0 кадров в покое, 60 к/с под курсором, 1 вызов/кадр; `__bench` в прогоне fx_probe = 0 (отдельно `scripts/bench_check.py`: 1,36–1,45 мс и при плане в кадре, и после прокрутки — причина в сценарии fx_probe, не найдена), `uncapped` — ошибка скриншота. Цена кадра — `$X/scripts/fx_bench2.py` → `fx_bench2.json`: 1,31 мс sync / 0,24 пропускная (Iris Xe, DPR 1), 1,84 / 0,67 (DPR 2), телефон 1,17 / 0,24 |
| 4. Кадры судьи | **сделано** | `$S/judge/{a-code,b-blender,c-hybrid}__{first-screen-desk,first-screen-mob,icons,act-stamp}.png`, `c-hybrid__{beam-on,beam-off,tour-mob}.png`, `c-hybrid__fonarik-10s.webm` (из `shots/sd3_video/`, проверен кадрами: найдены все 4); листы `sheet__{ab,bc,ac}__<состояние>.jpg` ×12 + `sheet__bc__beam.jpg`, `sheet__c__beam-off-on.jpg`. Старые кадры фазы 2 — `$X/shots/judge_phase2_backup/`. `vote/build_pairs.py --check` — 5/5 пар «Сдано» |
| 5. Документы | **сделано** | `$S/README.md` (переписан: итог, лучше/хуже A, ворота, fx, кадры, ограничения, рецепт «переосвещение по проходам», время, команды), `$S/numbers.json` (ключи `phase2`, `night`), `$S/art-direction.md` §10, `$S/gallery.json` + `$S/gallery/*.webp` (6 приёмов, 1200×750 WebP q80), `$X/rules.md` (12 строк SD3/SD4), `$X/NOTES.md` (СТАТУС SD4, архив SD3, решения SD4, находки) |
| 6. HANDOFF-3 и отчёт | **сделано** | этот файл |

## 2. Числа (замерено)

- Ворота (десктоп / телефон Pixel 7 CPU×4 4G / reduce): LCP A 56/596/56, B 52/856/80, **C 60/864/48** мс; TBT A 0/3, B 0/33,
  C 0/42; передано A 72,0, B 116,4/111,7, C 295,4/290,6 КБ; CLS 0, ошибок 0, вызовов в покое 0 у всех; motion_check 0/0/0
  (N/A 4) у всех; marketing 0 блокеров, 0 серьёзных, полировок 45/39/39. Load average у каждого замера — `gates/*/load.txt`
  (у C на старте site_probe 21,4: чужое кодирование без замков).
- C: модуль 17,1 КБ / 6,05 КБ br, данные 172 КБ; ΔE постер → кадр 0 среднее 0,27 / p95 1,08 (SD3); готов 0,15 с после load.
- Время SD4: агент 05:34 → 06:35 (≈ 60 мин); машина 753 с (ворота C 623, судья 40, fx_probe 66, fx_bench2 10, bench_check 4, галерея 10);
  ожидание очереди: ворота 320 с, fx_probe 921 с. SD3: машина 2803 с (ворота A/B/C 1811, проба видео 750, прочее 242).

## 3. Команды (с длительностью)

```bash
R=/home/mm/Документы/app-design/blender-research; X=$R/99-raw/experiments/SD; S=$R/15-showcase/sdano; CR=/home/mm/Документы/app-design/creative-research
bash $X/gates/run_gates.sh c-hybrid L1 all        # сам встаёт в очередь одной задачей (--heavy), 10,5 мин замеров; метки SD4-*
python3 $R/99-raw/tools/slot_run.py --kind browser --label SD4-judge -- bash -c "for v in a-code b-blender c-hybrid; do timeout 240 python3 $X/scripts/judge_shots.py $S/\$v \$v $X/shots/sd4_judge; done"   # 40 с
python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label SD4-bench -- python3 $R/99-raw/tools/fx_probe.py $S/c-hybrid index.html $X/gates/c-hybrid/fx --modes desktop,mobile,reduce,uncapped --pointer --bench 120   # 66 с
python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label SD4-bench2 -- timeout 300 python3 $X/scripts/fx_bench2.py $S/c-hybrid $X/gates/c-hybrid/fx/fx_bench2.json --n 400   # 10 с
python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --wait 900 --label SD4-benchcheck -- timeout 120 python3 $X/scripts/bench_check.py $S/c-hybrid $X/gates/c-hybrid/fx/bench_check.json   # 4 с: __bench в кадре / после прокрутки
python3 $R/99-raw/tools/slot_run.py --kind browser --label SD4-gallery -- timeout 180 python3 $X/scripts/gallery_shots.py $S $X/shots/sd4_gallery   # 7 с
python3 $X/scripts/gallery_compose.py SCR/stampf  # кадры клипа: for t in 0.00 0.30 0.55 0.75 0.95 1.20; do ffmpeg -nostdin -y -loglevel error -ss $t -i $S/b-blender/assets/stamp.webm -frames:v 1 SCR/stampf/s_$t.png; done (+ -sseof -0.05 → s_end.png)
cd $CR && $CR/99-raw/tools/venv-I/bin/python $CR/99-raw/experiments/I/01-schemas/spec_check.py spec $S/c-hybrid/motion-spec.yaml
timeout 60 python3 $R/15-showcase/vote/build_pairs.py --check      # только проверка, ничего не пишет
```
ffmpeg — только `ffmpeg -nostdin -y -loglevel error …` под `timeout` или в фоне с журналом.

## 4. Решения и почему

1. `fail_S` C — правка спеки, не страницы: показ на телефоне — решение оркестратора (однократный, 2,24 с, без петли); бюджет 0
   писался до него; «запускать позже» не лечит (ворота ждут паузу после прокрутки, как живой посетитель). motion_check читает
   одно число `budget.loops_in_view_max` на оба режима (`loops_in_view_max_mobile` не читается).
2. `act-stamp` — настоящий конец клипа на странице (не подстановка `stamp-end.webp`): кадр = то, что видит посетитель.
3. Телефонные кадры — DPR 3 у всех трёх (как `plan-mob` фазы 1): вектор A и растр B/C на плотности реального телефона.
4. Цена кадра — суммой N кадров (sync и пропускная отдельно), т. к. покадровый `__bench` дал 0.

## 5. Где остановился, что проверить первым, дальше (оценки)

Остановился после документов; всё по заданию готово. Если будет следующий круг:
1. Первым — глазами пары голосования «Сдано» после сборки оркестратором (`vote/`, 5 пар) — ≈ 5 мин.
2. (по желанию) Цена кадра фонаря на реальном телефоне (EG-LIVE-01, вручную): Android среднего класса, chrome://inspect,
   `window.__fonarik.aim(0.43, 0.63)` + замер как в `fx_bench2.py` — ≈ 20 мин с устройством.
3. (по желанию) Полировки marketing_audit (39–45, общие с A: доля секционных значений и т. п.) — не блокируют; ≈ 30–60 мин.
4. (по желанию) Отметки 5–7 на плане B/C (сейчас 4 = пункты первой страницы акта; кухня за краем кадра) — кадр шире или
   второй ракурс; ≈ 1 ч с рендером.

## 6. Баги и грабли (новое за ночь)

- ffmpeg без `-nostdin` в цикле оболочки подвесил SD3 на 3 ч 40 мин (01:58 → 05:40). Исправлены `fx_video.py`, `stamp_comp.py`.
- fx_probe: `__bench(120)` в его прогоне → 0 мс (сам по себе `__bench` работает: 1,36–1,45 мс, `gates/c-hybrid/fx/bench_check.json`); `--modes uncapped` → таймаут скриншота 30 с (на этой машине).
- Тишина `--heavy` не останавливает задачи `--kind none` соседей (load average 21 на старте замера) — писать load average.
- Полный Chromium Playwright (chromium-1243) не запускается — только headless-shell (SD3, `video_probe.json`).

## 7. Вопросы оркестратору

1. Бюджет «движений в видимой зоне» C поднят в спеке до 1 (норма L1 телефона) ради однократного показа на телефоне — принять?
   Альтернатива — убрать показ (тогда телефон C без касания = B).
2. Кадры фазы 1 (`*__plan*.png`, `b-blender__render.png`, `sheet__{first-screen-desk,plan,plan-mob}.jpg`) остались в `judge/`
   как архив — убрать их в подпапку, чтобы не путать судью?
