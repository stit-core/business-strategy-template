#!/usr/bin/env bash
# run_gates.sh — ворота варианта «Сдано» (дорожка SD; SD2 → SD3): KIT §6. Замеры — «в тишине»: всё под
# slot_run --kind browser --heavy (очередь v2: замок тяжёлого рендера + замок браузера — никто не рендерит Cycles параллельно);
# SD4 (26.09 05:45): метки SD4-*; копия прогона SD3 — run_gates_sd3.sh.
# motion_check / marketing_audit — с --no-lock (замки уже взял slot_run; вкладывать slot_run в slot_run нельзя).
# Рядом с каждым замером — load average (/proc/loadavg) и память в журнал load.txt.
#   bash run_gates.sh a-code|b-blender|c-hybrid L0|L1 [probe|motion|audit|all]
set -u
# оркестратор, 26.09 03:35: самообёртка — весь прогон варианта ОДНОЙ задачей в очереди (slot_run v2.1: вложенные вызовы
# slot_run внутри проходят сразу, nested=render+browser); раньше каждый замер 12–20 с ждал тяжёлый замок 15–30 мин.
# Прежняя версия — run_gates_v3a.sh. Замена файла переименованием не задевает уже запущенный bash (он читает старый inode).
case ",${SLOT_RUN_HOLDS:-}," in
  *,render,*) ;;
  *) exec python3 /home/mm/Документы/app-design/blender-research/99-raw/tools/slot_run.py --kind browser --heavy --label "SD4-gates-$1" -- bash "$0" "$@" ;;
esac
R=/home/mm/Документы/app-design/blender-research; X=$R/99-raw/experiments/SD; S=$R/15-showcase/sdano
CR=/home/mm/Документы/app-design/creative-research
SCR=/tmp/claude-1000/-home-mm-----------app-design/d8f53347-66a5-40ec-a709-75f4623c7b47/scratchpad/sd3
V=$1; LV=$2; WHAT=${3:-all}
OUT=$X/gates/$V; mkdir -p "$OUT"
LOAD=$OUT/load.txt
stamp() { echo "$(date +%T) $1 loadavg=$(cut -d' ' -f1-3 /proc/loadavg) mem=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)MB" >> "$LOAD"; }
if [[ $WHAT == probe || $WHAT == all ]]; then
  TMP=$SCR/serve_$V
  rm -rf "$TMP"; mkdir -p "$SCR"; cp -r "$S/$V" "$TMP"
  python3 $R/99-raw/experiments/F1/02-hero-variants/serve_br.py "$TMP" 8784 > "$OUT/serve.log" 2>&1 &
  SRV=$!
  for i in $(seq 1 40); do curl -s -o /dev/null http://127.0.0.1:8784/index.html && break; sleep 0.5; done
  URL=http://127.0.0.1:8784/index.html
  stamp "probe-desk start"
  python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label SD4-probe-$V -- python3 $R/99-raw/tools/site_probe.py $URL $OUT/desk --quick > $OUT/probe_desk.txt 2>&1
  stamp "probe-desk end"; stamp "probe-mob start"
  python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label SD4-probe-$V -- python3 $R/99-raw/tools/site_probe.py $URL $OUT/mob --quick --mobile --throttle --wait 16000 > $OUT/probe_mob.txt 2>&1
  stamp "probe-mob end"; stamp "probe-rm start"
  python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label SD4-probe-$V -- python3 $R/99-raw/tools/site_probe.py $URL $OUT/rm --quick --reduced-motion > $OUT/probe_rm.txt 2>&1
  stamp "probe-rm end"
  kill $SRV 2>/dev/null; wait $SRV 2>/dev/null
  {
    echo "== desktop"; python3 $R/99-raw/tools/gate_check.py $OUT/desk/probe_quick.json desktop
    echo "== mobile (Pixel 7, CPU×4, 4G)"; python3 $R/99-raw/tools/gate_check.py $OUT/mob/probe_mobile_thr_quick.json mobile
    echo "== reduce"; python3 $R/99-raw/tools/gate_check.py $OUT/rm/probe_rm.json desktop --reduced
  } > $OUT/gate_check.txt 2>&1
  cat $OUT/gate_check.txt
fi
if [[ $WHAT == motion || $WHAT == all ]]; then
  stamp "motion start"
  python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label SD4-motion-$V -- python3 $CR/99-raw/tools/motion_check.py $S/$V/index.html --level $LV --out $OUT/motion --spec $S/$V/motion-spec.yaml --f83 "h1" --contrast "h1" --no-lock > $OUT/motion.txt 2>&1
  echo "motion exit=$?" >> $OUT/motion.txt
  stamp "motion end"
  tail -5 $OUT/motion.txt
fi
if [[ $WHAT == audit || $WHAT == all ]]; then
  stamp "audit start"
  python3 $R/99-raw/tools/slot_run.py --kind browser --heavy --label SD4-audit-$V -- python3 $CR/99-raw/tools/marketing_audit.py $S/$V/index.html --level $LV --out $OUT/audit --name sdano-$V --no-lock > $OUT/audit.txt 2>&1
  echo "audit exit=$?" >> $OUT/audit.txt
  stamp "audit end"
  tail -5 $OUT/audit.txt
fi
