#!/usr/bin/env bash
P=/home/mm/Документы/app-design/blender-research/99-raw/tools/site_probe.py
U3=http://127.0.0.1:8782/a-code/index.html; U2=http://127.0.0.1:8782/v2/l2-zveno/index.html
python3 $P $U3 /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v3-desk --quick > /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v3-desk.log 2>&1
python3 $P $U3 /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v3-mob --quick --mobile --throttle --wait 16000 > /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v3-mob.log 2>&1
python3 $P $U3 /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v3-rm --quick --reduced-motion > /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v3-rm.log 2>&1
python3 $P $U2 /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v2-desk --quick > /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v2-desk.log 2>&1
python3 $P $U2 /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v2-mob --quick --mobile --throttle --wait 16000 > /home/mm/Документы/app-design/blender-research/99-raw/experiments/CD/out/gates/final/v2-mob.log 2>&1
echo done
