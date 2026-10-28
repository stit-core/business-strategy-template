#!/usr/bin/env bash
set -euo pipefail
export PATH=/home/mm/.nvm/versions/node/v24.21.0/bin:$PATH
N=$HOME/.cache/blender-research/npm-trial/node_modules; D=$(cd "$(dirname "$0")" && pwd); cd $D
for x in tsl gl; do NODE_PATH=$N $N/.bin/esbuild $x.js --bundle --format=esm --minify --outfile=$x.bundle.js --log-level=warning; done
python3 -c "
import brotli
for x in ('tsl', 'gl'):
    b = open(f'{x}.bundle.js', 'rb').read(); print(x, round(len(b)/1024, 1), 'КБ min,', round(len(brotli.compress(b, quality=11))/1024, 1), 'КБ br')
" | tee weights.txt
