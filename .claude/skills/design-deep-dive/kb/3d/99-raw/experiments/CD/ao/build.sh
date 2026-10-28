#!/usr/bin/env bash
set -euo pipefail
export PATH=/home/mm/.nvm/versions/node/v24.21.0/bin:$PATH
N=$HOME/.cache/blender-research/npm-trial/node_modules; D=$(cd "$(dirname "$0")" && pwd)
cd $D && NODE_PATH=$N $N/.bin/esbuild ao.js --bundle --format=esm --minify --outfile=ao.bundle.js --log-level=warning \
  --define:__CD_STUDIO__=true --define:__CD_IK__=true --define:__CD_WORLD__=true --define:__CD_POST__=true --define:__CD_DETAIL__=true --define:__CD_GLB__=false --define:__CD_KTX2__=false --define:__CD_BEAM__=true --define:__CD_TRAIL__=true --splitting=false
for x in gtao ssao n8 base; do NODE_PATH=$N $N/.bin/esbuild w_$x.js --bundle --format=esm --minify --external:three --outfile=w_$x.out.js --log-level=warning; done
python3 - <<'PY'
import brotli, os, json
d = os.path.dirname(os.path.abspath('ao.bundle.js')); out = {}
for x in ('gtao', 'ssao', 'n8', 'base'):
    b = open(f'w_{x}.out.js', 'rb').read(); out[x] = {'min_kb': round(len(b) / 1024, 1), 'br_kb': round(len(brotli.compress(b, quality=11)) / 1024, 1)}
json.dump(out, open('weights.json', 'w'), indent=1); print(json.dumps(out))
PY
