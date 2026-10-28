#!/bin/bash
# Z3: ворота C в тишине — две короткие тяжёлые задачи (site_probe×3 + gate_check; motion_check L2 + marketing_audit)
Z=/home/mm/Документы/app-design/blender-research/99-raw/experiments/Z; T=/home/mm/Документы/app-design/blender-research/99-raw/tools
python3 $T/slot_run.py --kind browser --heavy --min-mem 3000 --label Z3-gates-c -- $Z/run_gates.sh c-hybrid
python3 $T/slot_run.py --kind browser --heavy --min-mem 3000 --label Z3-motion-c -- $Z/run_motion.sh c-hybrid
date
