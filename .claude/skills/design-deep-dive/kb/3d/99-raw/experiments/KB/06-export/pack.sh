#!/bin/bash
# pack.sh — веб-GLB «Ё» для C: десктоп WebP (атлас 2048; KTX2 ETC1S — только для сравнения), телефон WebP ≤ 512 px.
# -kn -ke -km — имена узлов/материалов и extras (kb_uv4, kb_code…) целы, материалы не сливаются (варианты);
# -vtf — UV без квантования (страница двигает UV на ячейку атласа), -vpf — позиции float (без узлов деквантования).
T=/home/mm/Документы/app-design/blender-research/99-raw/tools
GP=$T/bin/gltfpack-1.2/gltfpack
cd "$(dirname "$0")/out"
$GP -i kb_web_raw.glb -o kb_desk_ktx2.glb -cc -tc -tq 8 -kn -ke -km -vtf -vpf   # KB2: ETC1S — сиреневый сдвиг серых, +транскодер 212 КБ br
$GP -i kb_web_raw.glb -o kb_desk.glb -cc -tw -kn -ke -km -vtf -vpf             # KB3: WebP, атлас 2048 без уменьшения
$GP -i kb_web_raw.glb -o kb_mob.glb -cc -tw -tl 512 -kn -ke -km -vtf -vpf -si 0.4   # KB3: телефон 107 → 43 тыс. треуг. (глазами без разницы)
export PATH=/home/mm/.nvm/versions/node/v24.21.0/bin:$PATH
for f in kb_desk.glb kb_mob.glb kb_desk_ktx2.glb; do node $T/node/validate.mjs $PWD/$f 2>&1 | tail -3; done
ls -la kb_desk.glb kb_mob.glb kb_desk_ktx2.glb
