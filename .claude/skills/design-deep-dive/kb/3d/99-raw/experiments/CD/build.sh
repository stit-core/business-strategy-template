#!/usr/bin/env bash
# build.sh · CD «код v3» · сборка без сети из npm-trial (three 0.186.0, postprocessing 6.39.5, n8ao 2.0.1, esbuild 0.28.2)
# С фазы 2 исходник сцены — общий: 15-showcase/_shared/code3d/src/ (scene.js, glb-modules.js, post.js, …); фаза 1 — src/scene-v3p1.js.
#   ./build.sh            — страница A: 15-showcase/zveno/a-code/js/three-scene.js + chunks/ (пост и GLB-загрузчик — отдельные чанки)
#   ./build.sh kb         — варианты без каждого приёма → out/kb/<вариант>/ + out/kb.json (КБ br по чанкам)
set -euo pipefail
CD=$(cd "$(dirname "$0")" && pwd)
R=$(cd "$CD/../../.." && pwd)
C3=$R/15-showcase/_shared/code3d
A=$R/15-showcase/zveno/a-code
if [ "${1:-}" = "kb" ]; then
  mkdir -p "$CD/out/kb"
  rm -rf "$CD/out/kb"/*
  "$C3/build.sh" "$CD/out/kb/full" > /dev/null
  "$C3/build.sh" "$CD/out/kb/no-studio" --no-studio > /dev/null
  "$C3/build.sh" "$CD/out/kb/no-ik" --no-ik > /dev/null
  "$C3/build.sh" "$CD/out/kb/no-world" --no-world > /dev/null
  "$C3/build.sh" "$CD/out/kb/no-post" --no-post > /dev/null
  "$C3/build.sh" "$CD/out/kb/no-detail" --no-detail > /dev/null
  "$C3/build.sh" "$CD/out/kb/no-beam" --no-beam > /dev/null                 # CD3: приём 8 (лучи; живёт в чанке поста)
  "$C3/build.sh" "$CD/out/kb/no-trail" --no-trail > /dev/null               # CD3: приём 10 (след)
  "$C3/build.sh" "$CD/out/kb/no-beam-trail" --no-beam --no-trail > /dev/null
  "$C3/build.sh" "$CD/out/kb/none" --no-studio --no-ik --no-world --no-post --no-detail --no-beam --no-trail > /dev/null
  python3 - "$CD/out/kb" <<'EOF'
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
"$C3/build.sh" "$A/js"
