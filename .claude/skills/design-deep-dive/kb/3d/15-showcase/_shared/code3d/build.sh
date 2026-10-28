#!/usr/bin/env bash
# build.sh · общий код 3D «Звена» (_shared/code3d) · сборка без сети из npm-зависимостей скилла
# (three 0.186.0, postprocessing 6.39.5, n8ao 2.0.1, esbuild 0.28.2)
#   build.sh OUT_JS_DIR [--glb] [--ktx2] [--no-studio] [--no-ik] [--no-world] [--no-post] [--no-detail] [--no-beam] [--no-trail]
#     → OUT_JS_DIR/three-scene.js (вход, import из main.js) + OUT_JS_DIR/chunks/ (three, пост, GLB-загрузчик — отдельными чанками:
#       пост качает только десктоп). --glb — гибридный крюк (opts.glb): без флага код загрузчика и его зависимости в three
#       (≈ +29 КБ min в общем чанке) в сборку не попадают — страница A (код) его не платит.
#   --ktx2 (крюк v2, включает --glb) — KTX2Loader отдельным чанком (качается, только если GLB с KHR_texture_basisu) + транскодер
#       basis (three 0.186.0: basis_transcoder.js + .wasm, Apache-2.0) копией в OUT_JS_DIR/basis/ — со своего домена, без CDN.
#   Флаги --no-* выбрасывают код приёма из бандла (define __CD_*__=false) — так меряется вес приёма в КБ br.
# Пример (гибрид C): _shared/code3d/build.sh zveno/c-hybrid/js --glb
set -euo pipefail
export PATH="${DDD_NODE:+$(dirname "$DDD_NODE"):}$PATH"  # перенос: node — из PATH или DDD_NODE
N="${DDD_HOME:-${XDG_CACHE_HOME:-$HOME/.cache}/design-deep-dive}/node/node_modules"  # перенос: npm-зависимости скилла (scripts/package.json)
C3=$(cd "$(dirname "$0")" && pwd)
OUT=${1:?"папка js страницы, напр. …/zveno/c-hybrid/js"}; shift
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
STUDIO=true; IK=true; WORLD=true; POST=true; DETAIL=true; GLB=false; KTX2=false; BEAM=true; TRAIL=true
for a in "$@"; do case "$a" in
  --glb) GLB=true;; --ktx2) GLB=true; KTX2=true;; --no-studio) STUDIO=false;; --no-ik) IK=false;; --no-world) WORLD=false;; --no-post) POST=false;; --no-detail) DETAIL=false;; --no-beam) BEAM=false;; --no-trail) TRAIL=false;;
  *) echo "неизвестный флаг $a" >&2; exit 2;; esac; done
TMP=$(mktemp -d)
(cd "$C3" && NODE_PATH=$N "$N/.bin/esbuild" three-scene=src/scene.js --bundle --format=esm --splitting --minify \
   --legal-comments=eof --outdir="$TMP" --chunk-names='chunks/[name]-[hash]' --log-level=warning \
   --define:__CD_STUDIO__=$STUDIO --define:__CD_IK__=$IK --define:__CD_WORLD__=$WORLD --define:__CD_POST__=$POST --define:__CD_DETAIL__=$DETAIL --define:__CD_GLB__=$GLB --define:__CD_KTX2__=$KTX2 --define:__CD_BEAM__=$BEAM --define:__CD_TRAIL__=$TRAIL)
[ -d "$OUT/chunks" ] && find "$OUT/chunks" -maxdepth 1 -name '*.js' -delete
mkdir -p "$OUT/chunks"; if ls "$TMP"/chunks/*.js > /dev/null 2>&1; then mv "$TMP"/chunks/*.js "$OUT/chunks/"; fi   # без import() чанков нет
mv "$TMP/three-scene.js" "$OUT/three-scene.js"; rm -rf "$TMP"
if [ "$KTX2" = true ]; then                                        # транскодер basis — рядом со страницей (путь по умолчанию: chunks/../basis/)
  mkdir -p "$OUT/basis"; cp "$N/three/examples/jsm/libs/basis/basis_transcoder.js" "$N/three/examples/jsm/libs/basis/basis_transcoder.wasm" "$OUT/basis/"
  printf 'basis_transcoder.js / .wasm — Basis Universal (Binomial LLC), Apache License 2.0; копия из three 0.186.0 examples/jsm/libs/basis/\n' > "$OUT/basis/LICENSE.txt"
  ls -la "$OUT/basis"
fi
ls -la "$OUT/three-scene.js" "$OUT/chunks"
