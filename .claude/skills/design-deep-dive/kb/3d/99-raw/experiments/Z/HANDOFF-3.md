# HANDOFF-3 — «Звено», дорожка Z3 (фаза 2: B — страница из секвенций Blender, C — гибрид) · ночь 26.09.2026

Чек-поинт Z3: 00:05 → 05:30 (итог). Blender 5.2.2 (Cycles CPU, 20 потоков), three 0.186.0, крюк `_shared/code3d` v2 (CD3, вид `p3`).
`R=/home/mm/Документы/app-design/blender-research`, `Z=$R/99-raw/experiments/Z`, предмет — `$R/15-showcase/zveno`.
Читать: `$R/15-showcase/KIT.md`, этот файл, `$Z/NOTES.md` (журнал Z3 с 00:05, `## СТАТУС` 05:25), `$Z/rules.md` (раздел
«Фаза 2, продолжение (Z3)»), `$R/15-showcase/zveno/README.md` (B · фаза 2, C, «Выводы дорожки Z для базы»), `art-direction.md` §11.
Предыдущие чек-поинты — `HANDOFF-2.md` (Z2), `HANDOFF.md` (фаза 1). **Своих процессов нет** (сервер на 8785 — дорожки VD).

## 0. Где остановился и что проверить первым

- Всё по заданию Z3 сделано: страницы B и C полностью рабочие, кадры судьи A/B/C и записи 10 с на месте, ворота обеих страниц в тишине —
  0 FAIL, `motion_check` L2 — 0/0/0, документы и галерея обновлены.
- Проверить первым (если продолжать): (1) не сменила ли CD страницу A после 01:36 (`a-code/js/main.js`, `three-scene.js`) — C должна
  оставаться «A + строка glb» (`diff a-code/js/main.js c-hybrid/js/main.js`; при смене — `build.sh c-hybrid/js --glb` и пересъёмка C,
  см. §4); (2) листы пар — по кадрам A 01:38 (если CD переснимет A — `make_sheets.py pairs`, `make_judge2.py sheets`).

## 1. Готовность по пунктам задания Z3

| Пункт | Статус | Что есть |
|---|---|---|
| 1. Пересборка `.blend` + пробы | сделано | оба `.blend` (378 объектов, 520 387 треуг.; полый J3, медь пазами); пробы it3/it4/it5 — ореол к H4m числом, вспышка, скан (чёрные обрывки → правка), цельная начинка |
| 2. Кадры судьи B + постеры + станции | сделано | `judge/b-blender__{hero,hero-best,hero-v2cam,exploded,locking,first-move,scan-half,inside}.png` (1600×1000, 128 спп), `b-blender/img/` |
| 3. Секвенции B → страница | сделано | `b-blender/seq/{story-d 90, scan-d 60, story-m 60, scan-m 60}`; проверка страницы (стык, окно, 0 в покое, reduce, телефон) |
| 4. C: проверка 4 слоя, постеры, судья, запись, снимки | сделано | крюк v2 (начинка отдельным GLB с AO), вид `p3` как у A, основной GLB с касательными; `judge/c-hybrid__*` |
| 5. Ворота B и C в тишине + motion_check L2 + marketing_audit | сделано | 0 FAIL (десктоп/телефон/reduce) у обеих; motion 0/0/0; маркетинг — 0 серьёзных |
| 6. Документы | сделано | README B/C + «Выводы Z для базы», art-direction §11, `numbers.json`, rules.md, NOTES, `gallery-Z.json` (7 приёмов) |

## 2. Файлы Z3 (новые и изменённые)

| Путь | Что |
|---|---|
| `$Z/zseq.py` | `HALO_STORY` k 6,5 / r 0,42 (телефон 6 / 0,3); `FLASH_W` 6 Вт, лампа вспышки в 0,7 м от кольца к камере (у захвата кольца нет — точка модуля); `L_scan` 1,2·(glow − 0,6) + 0,1 Вт; медь сечения (0,88; 0,40; 0,17); `Scan(inner_mode)`: `cut` (Z2) / **`whole`** (итог: режется только корпус); детали целиком над плоскостью скрываются на кадр, `transparent_max_bounces` 48; режим начинки — ключ `--inner-mode` или файл `jobs/scan_inner_mode.txt` (сейчас `whole`); `opts` задания кадра (`halo_k`, `halo_r`, `flash_w`); прежняя версия — `zseq_z2.py` |
| `$Z/run_seq.sh` | пачки `--budget 480`, `--min-mem 4000`, метки `Z3-seq-*`, телефонные наборы 28 спп (прежняя — `run_seq_z2.sh`) |
| `$Z/jobs/seq_scan_d.json` | 60 кадров (было 90 — `seq_scan_d_90.json`); `jobs/it3_*`, `it4_*`, `it5_scan_whole.json` — пробы |
| `$Z/run_it3.sh`, `run_it4.sh`, `run_it5.sh`, `run_z3_chain.sh` | пробы и цепочка секвенций |
| `$Z/check_b.py` | проверка страницы B (`--only desk\|mob\|reduce`): стык постер → кадр 0, окно памяти, 0 кадров в покое, reduce, телефон |
| `$Z/rec_b.py` | запись 10 с прокрутки B (прогрев кэша, 0–6 с сюжет, 6,8–10 с скан) |
| `$Z/run_b_desk.sh`, `run_b_final.sh` | проверки и ворота B: лёгкая задача (check_b, снимки, маркетинг) + тихая (запись, site_probe ×3, motion_check) |
| `$Z/run_gates.sh` | ждёт ответа сервера (до 90 с), в конце зовёт `run_motion.sh`; `run_motion.sh` — только motion_check; `run_mkt.sh` — marketing_audit лёгкой задачей |
| `$Z/zweb_all.py` | `--tangents` → `export_tangents` (прежняя — `zweb_all_z2.py`) |
| `$Z/zweb_tools.py` | `inspect` без CDN: симлинк three во временную папку `gltf_web_inspect` |
| `$Z/run_c_post2.sh`, `run_c_frames2.sh`, `run_c_p3.sh`, `run_c_tan.sh`, `run_c_tan2.sh`, `run_gates_c.sh`, `run_shots.sh` | C: слои 3–4, кадры, постеры, касательные, ворота, снимки |
| `$Z/make_judge2.py`, `make_sheets.py` | раскладка под имена голосования (hero B = камера кода; H4m → `hero-best`); `pairs` по кадрам фазы 2 (прежние — `*_z2.py`) |
| `$Z/make_gallery_z.py` + `gallery_spec.json` | галерея → `zveno/gallery-Z.json`, `zveno/gallery/z-*.webp` |
| `$Z/write_numbers3.py` | фаза 2 в `zveno/numbers.json` (`b-blender.phase2`, `c-hybrid`, `z_machine_phase2`) |
| `$Z/dbg/scan_black.py`, `dbg/cap_uv.py` | отладка: материалы скана; UV0 крышек |
| `zveno/b-blender/` | `img/` (постеры AVIF/WebP, станции со сканом `whole`), `seq/*/f*.avif`, `js/main.js` (`SETS.d.scan.n` 60, `window.__zseq()`) |
| `zveno/c-hybrid/` | `js/` — крюк v2 `--glb`, вид p3; `main.js` = A + `glb {url, lowUrl, innerUrl, innerLowUrl}`; `assets/zveno-{main,inner,low-main,low-inner}.glb`; `img/` — постеры C |
| `$Z/out/` | `it3/ it4/ it5/`, `judge/` (+ `metrics.json`), `judge_prev/` (история), `seq/<набор>/` (+ `scan-d_cut/` — сечение), `c_split/` (drop), `c_split_keep/` (итог начинки), `c_web_tan/`, `c_full/` (полные GLB для стенда), `c_judge_p3/`, `c_judge_tan/`, `c_v1_page/` (откат C v1), `gates/`, `motion_{b,c}/`, `mkt_{b,c}/`, `check_b/`, `shots_*` |

## 3. Решения и почему

- **Скан B — корпус в разрезе, начинка цельная** (`whole`): обзор A/B/C (`judge/sheet_z2_overview.jpg`) показал, что сечение всей начинки
  (Z2) читается «ящиком с брусками» и проигрывает цельным деталям A/C; проба it5 (84 с машины) — предметный разрез привода.
- **Ореол B числом к H4m**: кольцо фона за рукой L* p50/p90 — H4m 37/49, выбранные k 6,5 / r 0,45 → 39/44 (4 пробы за 11 с машины).
- **Вспышка** — облучённость, не мощность: лампа в 5 см от лака (Z2) розовила сустав при любой мощности, 24 Вт в 0,7 м ≈ 1,5 ключа —
  «лосось»; итог 6 Вт в 0,7 м, вспышку несут LED и лак кольца; кадры со вспышкой перерендерены по формуле (lock_k > 0).
- **Лампа скана** 8,6 Вт в 0,06 от плоскости ≈ 44 Вт/м² (18× ключа) — всё оранжевое → волна только во время прохода.
- **Скан десктопа 60 кадров**, телефон **28 спп** — плотность по svh прокрутки и размер показа; −≈ 15 мин машины.
- **Кадры судьи** — те же камера и состояния, что у A (решение оркестратора); H4m-кадр — `hero-best` для пары «лучший против лучшего».
- **C = A + ассет**: `main.js` A (CD3 01:36, `p3`) + строка `glb`; крюк v2 — начинка отдельным GLB (да: −119 КБ br первого экрана),
  KTX2 (нет: +301 КБ br ради памяти GPU); основной десктопный GLB **с касательными** (без TANGENT анизотропия крышек в three — «веер»;
  `gltf-transform optimize --prune-attributes false`); начинка — `--inner-ao=keep` (страница = кадрам судьи со стенда).
- Очередь: порог 4000 для zseq (пик 1,7–2,2 ГБ), пачки 480 с, замеры одной задачей (v2.1), тишина только для замеров времени (v2.2).

## 4. Команды (длительность)

```bash
R=/home/mm/Документы/app-design/blender-research; Z=$R/99-raw/experiments/Z; cd $Z
python3 zq.py --min-mem 5000 --label Z3-it3 -- $Z/run_it3.sh               # пересборка обоих .blend + пробы (≈ 2 мин машины)
./run_seq.sh judge|story-d|scan-d|story-m|scan-m|all                       # пачки ≤ 480 с, пропуск готовых (≈ 46 мин машины на 4 набора)
python3 encode_seq.py posters; python3 encode_seq.py stations; python3 encode_seq.py seq <набор>; python3 encode_seq.py report   # ≈ 0,1–2 с/кадр
python3 zmetrics.py out/judge/{hero,hero-v2cam,exploded,locking,first-move}.png --out out/judge/metrics.json
python3 make_judge2.py b; python3 make_judge2.py c out/c_judge_p3; python3 make_judge2.py sheets; python3 make_sheets.py pairs
# C: пересборка при смене A: копия main.js A + строка glb (см. README C), затем
$R/15-showcase/_shared/code3d/build.sh $R/15-showcase/zveno/c-hybrid/js --glb; $Z/run_c_tan2.sh    # кадры, постеры, снимки, запись (≈ 5 мин браузера)
python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --min-mem 3000 --label Z3-gates -- bash $Z/run_gates.sh <b-blender|c-hybrid>   # ≈ 5–7 мин
python3 $R/99-raw/tools/slot_run.py --kind browser --label Z3-mkt -- $Z/run_mkt.sh <страница>             # ≈ 15 с
python3 $R/99-raw/tools/slot_run.py --kind browser --label Z3-checkb -- python3 check_b.py out/check_b      # ≈ 2 мин
python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label Z3-rec -- python3 rec_b.py $R/15-showcase/zveno/judge/b-blender__scroll-10s.webm
python3 make_gallery_z.py; python3 write_numbers3.py                                                    # < 10 с
```

## 5. Числа

| Что | B | C |
|---|---|---|
| ворота в тишине (десктоп / телефон / reduce) | 0 / 0 / 0 FAIL | 0 / 0 / 0 FAIL |
| LCP десктоп / телефон | 56 / 660 мс | 56 / 660 мс |
| TBT десктоп / телефон | 0 / 28 мс | 56 / 146 мс |
| передано при открытии | 569 / 695 КБ | 1746 / 962 КБ |
| 3D-ассеты | 0 (кадры — картинки; за полную прокрутку 1,7 / 1,8 МБ AVIF) | 1256 / 575 КБ br |
| motion_check L2 (B/S/D) | 0/0/0 | 0/0/0 |
| marketing_audit | 0 серьёзных, 65 «полировка» (общий style.css A) | то же |
| кадр | Cycles ≈ 10 с (1280×800, 40/28 спп), судья 37–44 с (128 спп) | стенд: hero 122 вызова / 137 тыс. треуг. |
| проверка страницы | стык 0,12 / p99 1; покой 0 отрисовок; окно 4–6 ImageBitmap ≤ 12/10 | — |

- Лак B (p50/p75/p90): hero 81/91/97, сборка 87/96/97 (p75 ≥ 85 ✓); шум гладкого лака 1,84–2,07·10⁻³; низ кадра к странице ΔE 2,1–2,6.
- Веса B: сюжет 942 / 905 КБ, скан 704 / 911 КБ (десктоп / телефон), постеры AVIF 21 / 20 КБ, станции 10–18 КБ.
- GLB C: основной 1255 КБ (759 br, с TANGENT) + начинка 641 КБ (495 br), телефон 569 + 284 КБ; валидатор 0/0; gltf_diff IoU 0,986.
- Машина Z3 (журнал очереди, метки Z3-*): **5835 с** запусков; ожидание номерков суммарно 28 306 с (параллельные ожидания складываются).
- Время агента Z3: 00:05–05:30 (≈ 5,4 ч).

## 6. Следующие шаги (если продолжать)

1. C: своя выгрузка начинки со своим атласом AO 512² (материалы начинки — копии с суффиксом) вместо копии атласа руки: −≈ 350 КБ br
   в простое (≈ 30 мин агента + 1 запекание ≈ 40 с).
2. B: кадры 1600×1000 для сюжета десктопа (широкие экраны мягче): ×1,56 машины (≈ 25 мин) — если голосование отметит мягкость.
3. Синхронизация C с A при смене A (см. §0).

## 7. Баги и слабые места

- B не отвечает на ввод (предрендер): IK и «пружина» — только у A/C.
- Вспышка фиксации — по одному кадру секвенции на модуль (формула `storyFrame`): при обычной прокрутке почти незаметна.
- C: начинка несёт копию атласа руки 2048² (+375 КБ br в простое, +≈ 16 МБ памяти GPU); крышки светлее тёмного графита B (кодовая студия).
- `slot_run.log` ожидания Z3 велики (9–25 мин на номерок при плотной очереди соседей) — пачки по 8 мин и замеры одной задачей помогли.
- Одна пачка `story-d` упала (у захвата нет `grip_ring`) — исправлено, кадры дорендерены.

## 8. Вопросы

Нет открытых. Решение по KTX2 и начинке C принято по замерам CD3 (записано в README C и rules.md).
