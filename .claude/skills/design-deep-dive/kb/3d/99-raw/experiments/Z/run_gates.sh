#!/bin/bash
# ворота страницы «Звено» (KIT §6): копия папки → serve_br :8781 → site_probe десктоп / Pixel 7 (CPU×4, 1,6 Мбит/с) / reduce →
# gate_check; load average — до и после (замеры «в тишине»: запускать под zq.py --kind browser или slot_run --kind browser --heavy)
#   run_gates.sh b-blender|c-hybrid [метка]
set -u
R=/home/mm/Документы/app-design/blender-research; T=$R/99-raw/tools; Z=$R/99-raw/experiments/Z
PAGE=${1:?b-blender|c-hybrid}; TAG=${2:-$PAGE}
OUT=$Z/out/gates/$TAG; SRV=/tmp/claude-1000/-home-mm-----------app-design/d8f53347-66a5-40ec-a709-75f4623c7b47/scratchpad/serve_$TAG
rm -rf "$OUT" "$SRV"; mkdir -p "$OUT" "$SRV"
cp -r $R/15-showcase/zveno/$PAGE "$SRV/$PAGE"
python3 $R/99-raw/experiments/F1/02-hero-variants/serve_br.py "$SRV" 8781 > "$OUT/serve.log" 2>&1 &
SP=$!
U=http://127.0.0.1:8781/$PAGE/index.html
# Z3: serve_br сначала сжимает всё в *.br (GLB по мегабайту — секунды): ждать ответа, а не 2 с (иначе ERR_CONNECTION_REFUSED у первой пробы)
for i in $(seq 1 90); do curl -s -o /dev/null -w '%{http_code}' $U 2>/dev/null | grep -q 200 && break; sleep 1; done
echo "server_ready_s $i" > "$OUT/server.txt"
{ echo "load_before $(cut -d' ' -f1-3 /proc/loadavg)"; date; } > "$OUT/load.txt"
python3 $T/site_probe.py $U "$OUT/desk" --quick > "$OUT/desk.log" 2>&1
echo "load_after_desk $(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/load.txt"
python3 $T/site_probe.py $U "$OUT/mob" --quick --mobile --throttle --wait 16000 > "$OUT/mob.log" 2>&1
echo "load_after_mob $(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/load.txt"
python3 $T/site_probe.py $U "$OUT/rm" --quick --reduced-motion > "$OUT/rm.log" 2>&1
echo "load_after_rm $(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/load.txt"
kill $SP 2>/dev/null; wait $SP 2>/dev/null
python3 $T/gate_check.py "$OUT/desk/probe_quick.json" desktop > "$OUT/gate_desk.txt" 2>&1; echo "desk exit $?" >> "$OUT/load.txt"
python3 $T/gate_check.py "$OUT/mob/probe_mobile_thr_quick.json" mobile > "$OUT/gate_mob.txt" 2>&1; echo "mob exit $?" >> "$OUT/load.txt"
RM=$(ls "$OUT"/rm/probe*rm*.json 2>/dev/null | head -1)
python3 $T/gate_check.py "$RM" desktop --reduced > "$OUT/gate_rm.txt" 2>&1; echo "rm exit $?" >> "$OUT/load.txt"
date >> "$OUT/load.txt"
cat "$OUT/load.txt"
for g in desk mob rm; do echo "== $g"; grep -E "FAIL|WARN|PASS|итог|verdict" "$OUT/gate_$g.txt" | head -30; done
# Z3 (slot_run v2.1 — наследование замков): ворота подачи creative-research в той же задаче «тишины» (утилиты с --no-lock)
$Z/run_motion.sh $PAGE >> "$OUT/load.txt" 2>&1
tail -4 "$OUT/load.txt"
