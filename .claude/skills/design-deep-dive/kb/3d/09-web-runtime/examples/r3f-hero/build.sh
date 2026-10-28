#!/bin/sh
# Сборка чанка hero.js: esbuild 0.28, React 19.3, R3F 9.8.0, drei 10.7.8, three 0.186.0 (песочница npm — $DDD_HOME/node)
set -e
NPM="${DDD_HOME:-${XDG_CACHE_HOME:-$HOME/.cache}/design-deep-dive}/node"  # перенос: npm-зависимости скилла (scripts/package.json)
HERE=$(cd "$(dirname "$0")" && pwd)
export PATH="${DDD_NODE:+$(dirname "$DDD_NODE"):}$PATH"  # перенос: node — из PATH или DDD_NODE
cd $NPM && NODE_PATH=$NPM/node_modules npx esbuild "$HERE/src/Hero.jsx" --bundle --minify --format=esm --jsx=automatic --target=es2022 \
  --define:process.env.NODE_ENV='"production"' --outfile="$HERE/hero.js" --metafile="$HERE/meta.json" --log-level=warning
python3 - "$HERE/hero.js" <<'PY'
import sys, gzip, brotli
b = open(sys.argv[1], 'rb').read()
print(f"hero.js min {len(b)/1024:.0f} KB, gzip {len(gzip.compress(b, 9))/1024:.0f} KB, br {len(brotli.compress(b, quality=11))/1024:.0f} KB")
PY
