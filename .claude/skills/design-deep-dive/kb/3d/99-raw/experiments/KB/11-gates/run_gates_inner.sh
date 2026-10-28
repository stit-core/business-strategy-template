#!/bin/bash
# run_gates_inner.sh VARIANT — как run_gates.sh, но без своих входов в очередь;(a|b|c) [steps: probe,motion,mkt] — ворота KIT §6 для страницы «Ё» в «тишине» (render.lock + browser.lock).
V=$1; STEPS=${2:-probe,motion,mkt}
R=/home/mm/Документы/app-design/blender-research; CR=/home/mm/Документы/app-design/creative-research
declare -A DIR=([a]=a-code [b]=b-blender [c]=c-hybrid)
PAGE=$R/15-showcase/keyboard/${DIR[$V]}
SCR=/tmp/claude-1000/-home-mm-----------app-design/2e530199-ecfd-48ab-994b-f3dd1c91c010/scratchpad
OUT=$(dirname "$0")/$V; OUT=$(cd "$(dirname "$0")" && pwd)/$V; mkdir -p $OUT
COPY=$SCR/kb_gate_$V; rm -rf $COPY; cp -r $PAGE $COPY
python3 $R/99-raw/experiments/F1/02-hero-variants/serve_br.py $COPY 8783 > $OUT/serve.log 2>&1 &
SRV=$!
for i in $(seq 1 240); do (echo > /dev/tcp/127.0.0.1/8783) 2>/dev/null && break; sleep 0.25; done
U=http://127.0.0.1:8783/index.html
Q=""   # внутри одного входа slot_run --heavy (run_final_kb3.sh)
echo "=== $V $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg)" | tee -a $OUT/gates.log
if [[ $STEPS == *probe* ]]; then
  python3 $R/99-raw/tools/site_probe.py $U $OUT/desktop --quick >> $OUT/gates.log 2>&1
  echo "desktop load $(cut -d' ' -f1-3 /proc/loadavg)" >> $OUT/gates.log
  python3 $R/99-raw/tools/site_probe.py $U $OUT/mobile --quick --mobile --throttle --wait 16000 >> $OUT/gates.log 2>&1
  echo "mobile load $(cut -d' ' -f1-3 /proc/loadavg)" >> $OUT/gates.log
  python3 $R/99-raw/tools/site_probe.py $U $OUT/reduce --quick --reduced-motion >> $OUT/gates.log 2>&1
  echo "reduce load $(cut -d' ' -f1-3 /proc/loadavg)" >> $OUT/gates.log
  python3 $R/99-raw/tools/gate_check.py $OUT/desktop/probe_quick.json desktop > $OUT/gate_desktop.txt 2>&1; echo "gate desktop exit $?" | tee -a $OUT/gates.log
  python3 $R/99-raw/tools/gate_check.py $OUT/mobile/probe_mobile_thr_quick.json mobile > $OUT/gate_mobile.txt 2>&1; echo "gate mobile exit $?" | tee -a $OUT/gates.log
  RM=$(ls $OUT/reduce/probe*rm*.json 2>/dev/null | head -1)
  python3 $R/99-raw/tools/gate_check.py $RM desktop --reduced > $OUT/gate_reduce.txt 2>&1; echo "gate reduce exit $? ($RM)" | tee -a $OUT/gates.log
fi
if [[ $STEPS == *motion* ]]; then
  python3 $CR/99-raw/tools/motion_check.py $U --level L1 --out $OUT/motion --f83 "h1" --contrast "h1" --no-lock >> $OUT/gates.log 2>&1
  echo "motion exit $? load $(cut -d' ' -f1-3 /proc/loadavg)" | tee -a $OUT/gates.log
fi
if [[ $STEPS == *mkt* ]]; then
  python3 $CR/99-raw/tools/marketing_audit.py $U --level L1 --out $OUT/mkt --name kb-$V --no-lock >> $OUT/gates.log 2>&1
  echo "mkt exit $? load $(cut -d' ' -f1-3 /proc/loadavg)" | tee -a $OUT/gates.log
fi
kill $SRV; wait $SRV 2>/dev/null
echo "=== $V done $(date +%T)" | tee -a $OUT/gates.log
