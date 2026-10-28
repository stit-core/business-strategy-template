#!/usr/bin/env bash
# build.sh · вес приёмов кода 3D (рецепт 12-recipes/14-product-in-code.md §5): общая сцена 15-showcase/_shared/code3d/src/
# собирается без сети (three 0.186.0, postprocessing 6.39.5, n8ao 2.0.1, esbuild 0.28.2) целиком и без каждого приёма.
#   ./build.sh kb         — варианты → $DDD_HOME/out/3d/recipes/14-product-in-code/kb/<вариант>/ и kb.json рядом (КБ br по чанкам)
# Страницу собирает сам 15-showcase/_shared/code3d/build.sh ПАПКА_JS.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$HERE/../../../.." && pwd)                       # корень базы kb/3d
C3=$R/15-showcase/_shared/code3d
H="${DDD_HOME:-${XDG_CACHE_HOME:-$HOME/.cache}/design-deep-dive}"       # окружение скилла: выходы и venv
OUT=$H/out/3d/recipes/14-product-in-code
PY=$H/venv/bin/python; [ -x "$PY" ] || PY=python3                      # brotli — из окружения скилла
if [ "${1:-}" = "kb" ]; then
  mkdir -p "$OUT/kb"
  rm -rf "$OUT/kb"/*
  "$C3/build.sh" "$OUT/kb/full" > /dev/null
  "$C3/build.sh" "$OUT/kb/no-studio" --no-studio > /dev/null
  "$C3/build.sh" "$OUT/kb/no-ik" --no-ik > /dev/null
  "$C3/build.sh" "$OUT/kb/no-world" --no-world > /dev/null
  "$C3/build.sh" "$OUT/kb/no-post" --no-post > /dev/null
  "$C3/build.sh" "$OUT/kb/no-detail" --no-detail > /dev/null
  "$C3/build.sh" "$OUT/kb/no-beam" --no-beam > /dev/null                 # приём 8 (лучи; живёт в чанке поста)
  "$C3/build.sh" "$OUT/kb/no-trail" --no-trail > /dev/null               # приём 10 (след)
  "$C3/build.sh" "$OUT/kb/no-beam-trail" --no-beam --no-trail > /dev/null
  "$C3/build.sh" "$OUT/kb/none" --no-studio --no-ik --no-world --no-post --no-detail --no-beam --no-trail > /dev/null
  "$PY" - "$OUT/kb" <<'EOF'
import brotli, json, os, sys
root = sys.argv[1]; res = {}
for v in sorted(os.listdir(root)):
    d = os.path.join(root, v)
    if not os.path.isdir(d): continue
    files = {}
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.endswith('.js'):
                b = open(os.path.join(dp, f), 'rb').read()
                files[os.path.relpath(os.path.join(dp, f), d)] = round(len(brotli.compress(b, quality=11)) / 1024, 1)
    post = sum(k for n, k in files.items() if 'post' in n)
    glb = sum(k for n, k in files.items() if 'glb' in n)
    res[v] = {'files': files, 'desktop_kb_br': round(sum(files.values()) - glb, 1), 'mobile_kb_br': round(sum(files.values()) - post - glb, 1),
              'glb_chunk_kb_br': round(glb, 1)}
json.dump(res, open(os.path.join(root, '..', 'kb.json'), 'w'), ensure_ascii=False, indent=1)
for v, r in res.items(): print(f"{v:10s} десктоп {r['desktop_kb_br']:6.1f} КБ br · телефон {r['mobile_kb_br']:6.1f} · чанк GLB {r['glb_chunk_kb_br']:5.1f} · {r['files']}")
EOF
  exit 0
fi
echo "build.sh: нужен режим kb (вес приёмов)" >&2; exit 2
