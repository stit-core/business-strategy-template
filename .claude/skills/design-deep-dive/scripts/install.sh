#!/usr/bin/env bash
# install.sh — окружение утилит скилла design-deep-dive вне репозитория: $DDD_HOME, по умолчанию
# ${XDG_CACHE_HOME:-~/.cache}/design-deep-dive — одно на машину для всех клонов шаблона. В репозиторий ничего не пишет.
#
#   scripts/install.sh --dry-run                     # план и что уже стоит; ничего не меняет, в сеть не ходит
#   scripts/install.sh                               # venv + pip (группа core), npm (группа page), каталоги out/cache/locks
#   scripts/install.sh --groups core,media --npm-groups page,3d    # группы pip и npm по задаче
#   scripts/install.sh --groups all --npm-groups all --bin --models --browsers --ffmpeg    # то же одним ключом: --all
#   scripts/install.sh --bin --from DIR [--from DIR2]  # бинарники из локальных папок (или --from DIR:DIR2)
#   scripts/install.sh --models --models-from DIR    # модели ONNX из локальных папок (то же правило поиска)
#   scripts/install.sh --ffmpeg                      # ffmpeg и ffprobe: статическая сборка в $DDD_HOME/bin, если системных нет
#   scripts/install.sh --playwright-match            # Playwright в venv — под Chromium из PLAYWRIGHT_BROWSERS_PATH
#   scripts/install.sh --catalogs                    # снимки каталогов polza, RouterAI, Gen-API и список доверия C2PA (сеть, 0 ₽)
#   scripts/install.sh --check                       # сверить установленное (версии, sha256), ничего не ставить
#
# Python — 3.12–3.13: закрепления numpy, scipy, networkx, tifffile требуют ≥ 3.12. Без --python (и переменной PYTHON)
# установка берёт python3.13, python3.12 или python3 не ниже 3.12; ниже — отказ с причиной: какая версия найдена, какая
# нужна и что сделать; venv на старом Python — тоже отказ. Python новее 3.13 — предупреждение: закрепления на нём не
# проверены. Шаги без pip (npm, бинарники, модели) при отказе идут дальше, код выхода — 1.
# Группы pip — секции «# [группа]» в requirements.txt: core, net, morph, svg, ocr, media (all — все). scipy стоит в
# media и svg: утилитам ai-media, которые считают метрики картинок и видео, нужна группа media.
# Группы npm — поле x-ddd-groups в package.json: page — замеры страницы и доступности (по умолчанию), media — SVG,
# иконки и плееры Lottie, 3d — проверка glTF и эталонные 3D-сборки базы (all — все). Группа ставится ключом
# --npm-groups; пакеты групп, поставленных раньше, остаются на месте — повторный запуск без ключа их не снимает.
# Идемпотентно: повторный запуск ставит только недостающее. Бинарник или модель с другим sha256 — ошибка, а не молчание;
# sha256 — установленного файла, в адресе — версия релиза или коммит. Архив не сошёлся с sha256 — поставьте файл вручную
# (раскладка — таблица ниже) или укажите --from. --from и --models-from ищут файл строки таблицы сначала по её пути, затем
# по имени в любой глубине папки и берут первый с тем же sha256; папка инструмента копируется целиком, если раскладка
# под ним та же, что в таблице, иначе — один файл.
# --playwright-match: браузеры уже лежат в PLAYWRIGHT_BROWSERS_PATH (образ без доступа к CDN Playwright), а их ревизия
# Chromium не та, что ждёт закреплённый playwright, — в venv ставится версия playwright под эту ревизию (таблица ниже).
# Системное, которое скрипт не ставит (путь — PATH или переменная DDD_*; --check показывает, что нашлось): Blender 5.2.2 LTS
# (DDD_BLENDER; агент работает с ним через blender -b под blender_supervisor), Node 24 + npm (DDD_NODE, DDD_NPM), Brave
# для refs_client (DDD_BRAVE), bwrap и systemd-run для blender_supervisor, flock, lzip для архива libjxl, системная
# libcairo2 для группы svg. Официальный MCP Blender Lab — по желанию, ставится вне скрипта: аддон из репозитория
# расширений Blender Lab, фоновый Blender с --online-mode --command blender_mcp в песочнице bwrap, сервер — закреплённым
# тегом:
#   uvx --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp
# Рецепт — kb/3d/04-ai-agents-mcp/06-headless-operations.md §6.1 и 07-security.md §8; к Claude Code сервер подключает
# владелец машины.
set -euo pipefail

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS="$SKILL/scripts"
DDD_HOME="${DDD_HOME:-${XDG_CACHE_HOME:-$HOME/.cache}/design-deep-dive}"
PYTHON_BASE="${PYTHON:-}"
DRY=0; CHECK=0; PIP_GROUPS="core"; DO_NPM=1; DO_BIN=0; DO_MODELS=0; DO_BROWSERS=0; DO_CATALOGS=0; DO_FFMPEG=0; PW_MATCH=0
NPM_GROUPS="page"
FROM=(); MODELS_FROM=()

usage() { awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "${BASH_SOURCE[0]}"; }
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --check) CHECK=1; DRY=1 ;;
    --groups) PIP_GROUPS="$2"; shift ;;
    --npm-groups) NPM_GROUPS="$2"; shift ;;
    --python) PYTHON_BASE="$2"; shift ;;
    --no-npm) DO_NPM=0 ;;
    --bin) DO_BIN=1 ;;
    --from) IFS=':' read -r -a _dirs <<< "$2"; FROM+=("${_dirs[@]}"); DO_BIN=1; shift ;;
    --models) DO_MODELS=1 ;;
    --models-from) IFS=':' read -r -a _dirs <<< "$2"; MODELS_FROM+=("${_dirs[@]}"); DO_MODELS=1; shift ;;
    --browsers) DO_BROWSERS=1 ;;
    --ffmpeg) DO_FFMPEG=1 ;;
    --playwright-match) PW_MATCH=1 ;;
    --catalogs) DO_CATALOGS=1 ;;
    --all) PIP_GROUPS="all"; NPM_GROUPS="all"; DO_BIN=1; DO_MODELS=1; DO_BROWSERS=1; DO_FFMPEG=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "install.sh: неизвестный ключ $1 (см. --help)" >&2; exit 2 ;;
  esac
  shift
done
[ "$PIP_GROUPS" = "all" ] && PIP_GROUPS="core,net,morph,svg,ocr,media"
NPM_ALL="page,media,3d"
[ "$NPM_GROUPS" = "all" ] && NPM_GROUPS="$NPM_ALL"
IFS=',' read -r -a _groups <<< "$NPM_GROUPS"
for g in ${_groups[@]+"${_groups[@]}"}; do
  case ",$NPM_ALL," in *",$g,"*) ;; *) echo "install.sh: неизвестная группа npm «$g» (есть: $NPM_ALL, all)" >&2; exit 2 ;; esac
done
[ "$CHECK" = 1 ] && { DO_BIN=1; DO_MODELS=1; }

say()  { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
run()  { if [ "$DRY" = 1 ]; then printf '  (план) %s\n' "$*"; else printf '  + %s\n' "$*"; "$@"; fi; }
sha()  { sha256sum "$1" 2>/dev/null | cut -d' ' -f1; }
ERR=0; WARN=0
fail() { printf '  ОШИБКА: %s\n' "$*" >&2; ERR=1; }
warn() { printf '  ПРЕДУПРЕЖДЕНИЕ: %s\n' "$*" >&2; WARN=1; }   # установку не останавливает
py_ver() { "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true; }
py_ok()  { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; }
py_new() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 14) else 1)' 2>/dev/null; }   # новее проверенных
pick_python() {  # явный --python или PYTHON; иначе python3.13, python3.12, python3 не ниже 3.12
  if [ -n "$PYTHON_BASE" ]; then printf '%s\n' "$PYTHON_BASE"; return 0; fi
  local c
  for c in python3.13 python3.12 python3; do
    if command -v "$c" >/dev/null 2>&1 && py_ok "$c"; then printf '%s\n' "$c"; return 0; fi
  done
}

VENV="$DDD_HOME/venv"; PY="$VENV/bin/python"; NODE_HOME="$DDD_HOME/node"
say "скилл:     $SKILL"
say "DDD_HOME:  $DDD_HOME$([ "$DRY" = 1 ] && echo '   (--dry-run: ничего не меняется)')"

# ------------------------------------------------------------------ каталоги
step "каталоги окружения"
for d in "$DDD_HOME" "$DDD_HOME/out" "$DDD_HOME/cache" "$DDD_HOME/locks" "$DDD_HOME/bin" "$DDD_HOME/models" "$NODE_HOME"; do
  if [ -d "$d" ]; then say "  есть: $d"; else run mkdir -p "$d"; fi
done

# ------------------------------------------------------------------ Playwright ↔ Chromium
# версия playwright | ревизия Chromium, которую она ждёт | версия Chromium — browsers.json колеса playwright на PyPI
# (playwright/driver/package/browsers.json). По ревизии браузера из PLAYWRIGHT_BROWSERS_PATH --playwright-match выбирает
# новейшую версию playwright, которая её ждёт.
PW_REVS='1.48.0|1140|130.0.6723.31
1.49.1|1148|131.0.6778.33
1.50.0|1155|133.0.6943.16
1.51.0|1161|134.0.6998.35
1.52.0|1169|136.0.7103.25
1.53.0|1179|138.0.7204.23
1.54.0|1181|139.0.7258.5
1.55.0|1187|140.0.7339.16
1.56.0|1194|141.0.7390.37
1.57.0|1200|143.0.7499.4
1.58.0|1208|145.0.7632.6
1.59.0|1217|147.0.7727.15
1.60.0|1223|148.0.7778.96
1.61.0|1228|149.0.7827.55
1.62.0|1234|151.0.7922.34
1.63.0|1243|153.0.8010.12'
PW_PIN="$(sed -nE 's/^playwright==([0-9.]+).*/\1/p' "$SCRIPTS/requirements.txt")"
pw_rev()     { printf '%s\n' "$PW_REVS" | awk -F'|' -v v="$1" '$1 == v { print $2 }'; }
pw_for_rev() { printf '%s\n' "$PW_REVS" | awk -F'|' -v r="$1" '$2 == r { v = $1 } END { print v }'; }
pw_loc() {  # [папка браузеров] → где установленный playwright ждёт Chromium (headless shell)
  if [ -n "${1:-}" ]; then
    PLAYWRIGHT_BROWSERS_PATH="$1" "$PY" -m playwright install --dry-run chromium 2>/dev/null
  else
    "$PY" -m playwright install --dry-run chromium 2>/dev/null
  fi | sed -nE 's/^[[:space:]]*Install location:[[:space:]]*(.*chromium_headless_shell-[0-9]+)[[:space:]]*$/\1/p' | head -1
}
PW_WANT=""; PW_NOTE=""
PBP="${PLAYWRIGHT_BROWSERS_PATH:-}"
if [ -n "$PBP" ] && [ "$PBP" != "$DDD_HOME/browsers" ] && [ -d "$PBP" ]; then
  revs="$(ls "$PBP" 2>/dev/null | sed -nE 's/^chromium(_headless_shell)?-([0-9]+)$/\2/p' | sort -un | tr '\n' ' ' | sed 's/ $//')"
  want_rev="$(pw_rev "$PW_PIN")"
  case " $revs " in *" $want_rev "*) have_rev=1 ;; *) have_rev=0 ;; esac
  if [ -n "$revs" ] && [ -n "$want_rev" ] && [ "$have_rev" = 0 ]; then
    for r in $revs; do v="$(pw_for_rev "$r")"; if [ -n "$v" ]; then PW_WANT="$v"; fi; done
    if [ -z "$PW_WANT" ]; then
      PW_NOTE="в PLAYWRIGHT_BROWSERS_PATH Chromium $revs — ревизий нет в таблице версий; playwright==$PW_PIN ждёт $want_rev (install.sh --browsers)"
    elif [ "$PW_MATCH" = 1 ]; then
      PW_NOTE="в PLAYWRIGHT_BROWSERS_PATH Chromium $revs — ставится playwright==$PW_WANT (закрепление $PW_PIN ждёт $want_rev)"
    else
      PW_NOTE="в PLAYWRIGHT_BROWSERS_PATH Chromium $revs, а playwright==$PW_PIN ждёт $want_rev — --playwright-match поставит playwright==$PW_WANT"
      PW_WANT=""
    fi
  fi
fi

# ------------------------------------------------------------------ Python
step "Python: venv и pip (группы: $PIP_GROUPS)"
PY_READY=1
if [ -x "$PY" ]; then
  say "  venv есть: $VENV ($("$PY" -c 'import sys; print(sys.version.split()[0])'))"
  if ! py_ok "$PY"; then
    fail "venv на Python $(py_ver "$PY"): закрепления требуют 3.12–3.13 — удалите $VENV и запустите install.sh снова (--python python3.13)"
    PY_READY=0
  elif py_new "$PY"; then
    warn "venv на Python $(py_ver "$PY"): закрепления проверены на 3.12–3.13 — при сбое pip пересоздайте venv (--python python3.13)"
  fi
else
  BASE="$(pick_python)"
  if [ -z "$BASE" ]; then
    v3="$(py_ver python3)"
    fail "нет Python 3.12–3.13 (python3 — ${v3:-нет}): закрепления numpy, scipy, networkx, tifffile требуют ≥ 3.12 — поставьте python3.13 или укажите --python"
    PY_READY=0
  elif ! command -v "$BASE" >/dev/null 2>&1; then
    fail "нет $BASE (--python или PYTHON)"; PY_READY=0
  elif ! py_ok "$BASE"; then
    fail "$BASE — Python $(py_ver "$BASE"): закрепления numpy, scipy, networkx, tifffile требуют 3.12–3.13 — укажите --python python3.13"
    PY_READY=0
  else
    say "  Python для venv: $BASE ($(py_ver "$BASE"))"
    if py_new "$BASE"; then
      warn "$BASE — Python $(py_ver "$BASE"): закрепления проверены на 3.12–3.13 — при сбое pip укажите --python python3.13"
    fi
    run "$BASE" -m venv "$VENV"
  fi
fi
PYU="$PY"; [ -x "$PYU" ] || PYU="$(pick_python)"; [ -n "$PYU" ] || PYU=python3   # Python служебных шагов (распаковка, kbpaths)
REQ_TMP="$(mktemp)"; NPM_TMP="$(mktemp)"; trap 'rm -f "$REQ_TMP" "$NPM_TMP"' EXIT   # вне $DDD_HOME: сухой прогон туда не пишет
awk -v groups=",$PIP_GROUPS," '
  /^# \[[a-z]+\]/ { g = $2; gsub(/[\[\]]/, "", g); take = index(groups, "," g ",") > 0; next }
  /^[[:space:]]*(#|$)/ { next }
  take && !seen[$0]++ { print }' "$SCRIPTS/requirements.txt" > "$REQ_TMP"   # пакет двух групп берётся один раз
if [ -n "$PW_NOTE" ]; then say "  $PW_NOTE"; fi
if [ -n "$PW_WANT" ] && grep -q '^playwright==' "$REQ_TMP"; then     # версия под браузеры; pyee и greenlet — по её требованиям
  grep -vE '^(playwright|pyee|greenlet)==' "$REQ_TMP" > "$REQ_TMP.pw" || true
  printf 'playwright==%s\n' "$PW_WANT" >> "$REQ_TMP.pw"; mv "$REQ_TMP.pw" "$REQ_TMP"
fi
say "  пакетов к установке: $(wc -l < "$REQ_TMP")"
if [ "$PY_READY" = 0 ]; then
  say "  pip — пропуск: нет подходящего Python"
elif [ -x "$PY" ] && [ "$DRY" = 1 ]; then
  missing=$("$PY" - "$REQ_TMP" <<'PYEOF'
import sys
from importlib import metadata
miss = []
for line in open(sys.argv[1]):
    name, _, ver = line.strip().partition("==")
    try:
        have = metadata.version(name)
        if ver and have != ver:
            miss.append(f"{name} {have} → {ver}")
    except metadata.PackageNotFoundError:
        miss.append(f"{name}=={ver} (нет)")
print("\n".join(miss))
PYEOF
)
  if [ -n "$missing" ]; then say "  не хватает или другая версия:"; printf '%s\n' "$missing" | sed 's/^/    /'; else say "  все пакеты групп уже стоят"; fi
else
  run "$PY" -m pip install --disable-pip-version-check -q -r "$REQ_TMP"
fi
if [ -x "$PY" ] && "$PY" -c 'import playwright' >/dev/null 2>&1; then
  PBE="${PLAYWRIGHT_BROWSERS_PATH:-}"; if [ -z "$PBE" ] && [ -d "$DDD_HOME/browsers" ]; then PBE="$DDD_HOME/browsers"; fi
  pwv="$("$PY" -c 'from importlib.metadata import version; print(version("playwright"))' 2>/dev/null || true)"
  loc="$(pw_loc "$PBE" || true)"
  if [ -z "$loc" ]; then say "  Playwright $pwv: где браузер — не определено"
  elif [ -d "$loc" ]; then say "  Playwright $pwv: браузер есть — $loc"
  else say "  Playwright $pwv: браузера нет ($loc) — install.sh --browsers или --playwright-match под PLAYWRIGHT_BROWSERS_PATH"; fi
fi

# ------------------------------------------------------------------ npm
npm_manifest() {  # манифест npm → $NPM_TMP: пакеты выбранных групп (x-ddd-groups) и пакеты, которые уже стоят в $NODE_HOME
  "$PYU" - "$SCRIPTS/package.json" "$NODE_HOME" "$NPM_GROUPS" "$NPM_TMP" <<'PYEOF'
import json, os, sys
src, home, asked, out = sys.argv[1:5]
pkg = json.load(open(src, encoding="utf-8"))
groups, deps = pkg.get("x-ddd-groups", {}), pkg.get("dependencies", {})
names = [g for g in asked.split(",") if g]
unknown = [g for g in names if g not in groups]
if unknown or not names:
    sys.exit(f"  группы npm: нет «{', '.join(unknown)}» в x-ddd-groups (есть: {', '.join(groups)})")
loose = sorted(set(deps) ^ {n for g in groups.values() for n in g})
if loose:
    sys.exit(f"  scripts/package.json: dependencies и x-ddd-groups расходятся: {', '.join(loose)}")
try:
    had = json.load(open(os.path.join(home, "package.json"), encoding="utf-8")).get("dependencies", {})
except (OSError, ValueError):
    had = {}
take = {n for g in names for n in groups[g]} | {n for n in had if n in deps}
kept = [g for g in groups if g not in names and any(n in had for n in groups[g])]
pkg["dependencies"] = {n: v for n, v in deps.items() if n in take}
if "allowScripts" in pkg:                                # разрешения скриптов установки — только взятым пакетам
    pkg["allowScripts"] = {k: v for k, v in pkg["allowScripts"].items() if k.rsplit("@", 1)[0] in take}
    if not pkg["allowScripts"]:
        del pkg["allowScripts"]
with open(out, "w", encoding="utf-8") as f:
    f.write(json.dumps(pkg, indent=2, ensure_ascii=False) + "\n")
print(f"  группы: {', '.join(names)}" + (f"; стоят с прошлых запусков и остаются: {', '.join(kept)}" if kept else ""))
PYEOF
}
npm_plan() {  # --dry-run и --check: что npm install поменяет в прямых зависимостях $NODE_HOME против манифеста групп
  "$PYU" - "$NPM_TMP" "$NODE_HOME" <<'PYEOF' || say "  план npm не посчитан ($PYU)"
import json, os, sys
want = json.load(open(sys.argv[1], encoding="utf-8")).get("dependencies", {})
home = sys.argv[2]
try:
    had = json.load(open(os.path.join(home, "package.json"), encoding="utf-8")).get("dependencies", {})
except (OSError, ValueError):
    had = {}
def version(name):
    try:
        return json.load(open(os.path.join(home, "node_modules", name, "package.json"), encoding="utf-8")).get("version")
    except (OSError, ValueError):
        return None
miss = [f"{n} {version(n)} → {v}" if version(n) else f"{n}@{v} (нет)" for n, v in want.items() if version(n) != v]
gone = sorted(set(had) - set(want))
print(f"  пакетов в манифесте групп: {len(want)}")
if miss:
    print("  не хватает или другая версия: " + ", ".join(miss))
if gone:
    print("  уходят из package.json (npm снимет те, что не нужны другим пакетам): " + ", ".join(gone))
if not miss and not gone:
    print("  пакеты уже стоят — npm install сверит дерево")
PYEOF
}
if [ "$DO_NPM" = 1 ]; then
  step "npm: зависимости утилит в $NODE_HOME (группы: $NPM_GROUPS)"
  NODE="${DDD_NODE:-$(command -v node || true)}"; NPM="${DDD_NPM:-$(command -v npm || true)}"
  if [ -z "$NODE" ] || [ -z "$NPM" ]; then
    say "  нет node/npm в PATH (DDD_NODE, DDD_NPM) — пропуск; нужен Node 24"
  elif ! npm_manifest; then
    fail "манифест npm не собран ($PYU, scripts/package.json) — пакеты npm не ставятся"
  else
    say "  node $("$NODE" --version) ($NODE), npm $("$NPM" --version 2>/dev/null || echo '?')"
    want="$(sha "$NPM_TMP")"
    have="$(cat "$NODE_HOME/.package.sha256" 2>/dev/null || true)"
    if [ "$want" = "$have" ] && [ -d "$NODE_HOME/node_modules" ]; then
      say "  node_modules соответствует манифесту групп"
    else
      if [ "$DRY" = 1 ]; then npm_plan; fi
      run cp "$NPM_TMP" "$NODE_HOME/package.json"
      run "$NPM" install --prefix "$NODE_HOME" --no-audit --no-fund
      if [ "$DRY" = 0 ]; then printf '%s\n' "$want" > "$NODE_HOME/.package.sha256"; fi
    fi
    if grep -q '^    "esbuild":' "$NPM_TMP"; then
      # esbuild (группа 3d) нужен только эталонным 3D-сборкам базы (сборки и постеры примеров kb/3d), утилитам
      # скилла — нет: его сбой — предупреждение, установка идёт дальше. Скрипт установки esbuild разрешён полем
      # allowScripts в package.json (npm ≥ 12 без разрешения его пропускает); на дереве, поставленном без разрешения,
      # его запускает npm rebuild
      ESB="$NODE_HOME/node_modules/esbuild/bin/esbuild"
      ESB_WHY="эталонные 3D-сборки базы (примеры kb/3d) без него не соберутся, утилитам скилла он не нужен"
      if [ -f "$ESB" ] && [ "$(head -c 2 "$ESB")" = '#!' ]; then
        if ! run "$NPM" rebuild esbuild --prefix "$NODE_HOME"; then warn "npm rebuild esbuild не прошёл — $ESB_WHY"; fi
      fi
      if [ -x "$NODE_HOME/node_modules/.bin/esbuild" ]; then
        if v="$("$NODE_HOME/node_modules/.bin/esbuild" --version 2>/dev/null)"; then say "  esbuild $v";
        else warn "esbuild не запускается — $ESB_WHY: $NPM rebuild esbuild --prefix $NODE_HOME"; fi
      elif [ "$DRY" = 0 ]; then warn "нет esbuild в $NODE_HOME/node_modules — $ESB_WHY: $NPM install --prefix $NODE_HOME"; fi
    fi
    if grep -q '^    "gltf-validator":' "$NPM_TMP"; then
      # validate.mjs (gltf_check.py, группа 3d) ищет gltf-validator рядом с собой: копия в $DDD_HOME/node, не симлинк
      # (ESM идёт по realpath)
      if cmp -s "$SCRIPTS/3d/node/validate.mjs" "$NODE_HOME/validate.mjs"; then say "  validate.mjs на месте";
      else run cp "$SCRIPTS/3d/node/validate.mjs" "$NODE_HOME/validate.mjs"; fi
    fi
  fi
fi

# ------------------------------------------------------------------ бинарники
# id | версия | файл для сверки (от $DDD_HOME/bin) | sha256 файла | адрес архива: релиз с версией в пути; «#папка» — какая
# папка архива ложится в $DDD_HOME/bin/<первая папка пути файла>; «-» — ставить вручную
BINS='c2patool|0.27.22|c2patool/c2patool|0707d482c319f70bb668e4cafc96274abffa381b7e51063c86071dd7556c8b67|https://github.com/contentauth/c2pa-rs/releases/download/c2patool-v0.27.22/c2patool-v0.27.22-x86_64-unknown-linux-gnu.tar.gz
exiftool|13.59|exiftool/exiftool|a6b8018093845ac93011307bac4ab630d6604b2365fc7f66bb88c88d7dedb5ed|https://sourceforge.net/projects/exiftool/files/Image-ExifTool-13.59.tar.gz/download
libavif|1.4.2|libavif/avifenc|bfa76fdb43b4903972ed2baedbff889d4f1e0b19efe7fe934044cf83e4b709a5|https://github.com/AOMediaCodec/libavif/releases/download/v1.4.2/linux-artifacts.zip
libavif|1.4.2|libavif/avifdec|a71ee96957d05b6a288b3269fc14227340a2a2b64da84b721e1ed09567df641e|https://github.com/AOMediaCodec/libavif/releases/download/v1.4.2/linux-artifacts.zip
libjxl|0.12.0|libjxl/tools/ssimulacra2|a7de3fb2fcc802bec6d7c8372060c2853c6e03fc06879a0263385dfa7a069691|https://github.com/libjxl/libjxl/releases/download/v0.12.0/jxl-linux-x86_64-static.tar.lz
libjxl|0.12.0|libjxl/tools/cjxl|c43d5bfbf1b359947a6edb61edb0bfc079924ee9801b30895533ff1fce83ee28|https://github.com/libjxl/libjxl/releases/download/v0.12.0/jxl-linux-x86_64-static.tar.lz
libjxl|0.12.0|libjxl/tools/djxl|67bdc98fdca7f93d7b77f3473e818b251ba107109ee83b3b37ccbd90066f2454|https://github.com/libjxl/libjxl/releases/download/v0.12.0/jxl-linux-x86_64-static.tar.lz
libwebp|1.6.0|libwebp/cwebp|5ac7ece6bdda1587f3c169ce74ab2734994f9d14e07fc5358208443c1b29edec|https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0-linux-x86-64.tar.gz#bin
libwebp|1.6.0|libwebp/dwebp|f4b035afc457f08d18124c822e554af5f8537c9e6c1e0e4a871297f90eda145b|https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-1.6.0-linux-x86-64.tar.gz#bin
rife-ncnn-vulkan|20221029 (модель rife-v4.6)|rife-ncnn-vulkan/rife-ncnn-vulkan|5c256556195216ddfca103073b0fd37e33e154c8aa40666775fcae8d6a6580b4|https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-ubuntu.zip
realesrgan-ncnn-vulkan|v0.2.0 (20220424)|realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan|22c2296a39b40cc43ac92615c827ab6d4b60b7142e8cee59f718e3f8e2cdbda9|https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip
vtracer|1.0.0-alpha.4 (musl)|vtracer-1.0.0a4/vtracer|43ad969fdac4f9d36e31a2f5d8650781248ba8bb7438c3778b378d9a7eaaa52e|https://github.com/visioncortex/vtracer/releases/download/1.0.0-alpha.4/vtracer-x86_64-unknown-linux-musl.tar.gz
potrace|1.16|potrace-1.16/potrace|e2d26f8322a7770a6ccdcf30889503b6c61e27ed8a30f13fc8f340174eb435b0|https://potrace.sourceforge.net/download/1.16/potrace-1.16.linux-x86_64.tar.gz
gltfpack|1.2|gltfpack-1.2/gltfpack|7e0dc08489835df804a83ca111c2cac6f8431f5a7b0e5453d94d6749a988b32f|https://github.com/zeux/meshoptimizer/releases/download/v1.2/gltfpack-ubuntu.zip
KTX-Software|4.4.2|KTX-Software-4.4.2-Linux-x86_64/bin/toktx|2a11939550fcc2d9b324c66d08f756ce3f512c8a02f6f5b03885e1a8b28f67f4|https://github.com/KhronosGroup/KTX-Software/releases/download/v4.4.2/KTX-Software-4.4.2-Linux-x86_64.tar.bz2'

# id | файл (от $DDD_HOME/models) | sha256 | адрес (OCR — модели RapidOCR 3.9.2, адреса и sha256 из его default_models.yaml)
MODELS='u2netp|rembg/u2netp.onnx|309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8|https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx
isnet-general-use|rembg/isnet-general-use.onnx|60920e99c45464f2ba57bee2ad08c919a52bbf852739e96947fbb4358c0d964a|https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx
depth-anything-v2-small|depth/depth_anything_v2_small.onnx|afb6a5c28f3b6bf1618c6e43f02073ef9dfdc70e937502d51603e57b0a1df10c|https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/4472b7362082ad9968fee890ca0f1e5aca36b93d/onnx/model.onnx
pp-ocrv5-rec-eslav|ocr/eslav_PP-OCRv5_rec_mobile.onnx|08705d6721849b1347d26187f15a5e362c431963a2a62bfff4feac578c489aab|https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv5/rec/eslav_PP-OCRv5_rec_mobile.onnx
pp-ocrv5-rec-en|ocr/en_PP-OCRv5_rec_mobile.onnx|c3461add59bb4323ecba96a492ab75e06dda42467c9e3d0c18db5d1d21924be8|https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv5/rec/en_PP-OCRv5_rec_mobile.onnx
pp-ocrv5-rec-cyrillic|ocr/cyrillic_PP-OCRv5_rec_mobile.onnx|90f761b4bfcce0c8c561c0cb5c887b0971d3ec01c32164bdf7374a35b0982711|https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv5/rec/cyrillic_PP-OCRv5_rec_mobile.onnx
pp-ocrv5-det|ocr/ch_PP-OCRv5_det_mobile.onnx|4d97c44a20d30a81aad087d6a396b08f786c4635742afc391f6621f5c6ae78ae|https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv5/det/ch_PP-OCRv5_det_mobile.onnx'

# ffmpeg и ffprobe — статическая сборка Martin Riedl (ffmpeg.martin-riedl.de: релизы с версией в пути, у файла — .sha256);
# kbpaths ставит $DDD_HOME/bin/ffmpeg первой в PATH утилит
FFMPEG='ffmpeg|7.1.1|ffmpeg/ffmpeg|8080c6b8f81eeb3b3a0e57d942f2a42de924f01c931f0acf12ee650535c52cff|https://ffmpeg.martin-riedl.de/download/linux/amd64/1741000776_7.1.1/ffmpeg.zip
ffprobe|7.1.1|ffmpeg/ffprobe|112411a7db4c60b3d553a7e648c69e1fb8bd7751d6b394c53968a1cc799916dd|https://ffmpeg.martin-riedl.de/download/linux/amd64/1741000776_7.1.1/ffprobe.zip'

fetch_unpack() {  # url[#папка] top → распаковать архив в $DDD_HOME/bin/<top>; корень архива с одной папкой снимается
  local url="${1%%#*}" sub="" top="$2" tmp n src
  case "$1" in *'#'*) sub="${1#*#}" ;; esac
  tmp="$(mktemp -d)"
  if ! run curl -fL --retry 2 -o "$tmp/pkg" "$url"; then
    fail "$url: загрузка не удалась — поставьте вручную или --from"; rm -rf "$tmp"; return 0
  fi
  if [ "$DRY" = 1 ]; then rm -rf "$tmp"; return 0; fi
  if ! "$PYU" - "$tmp/pkg" "$tmp/x" <<'PYEOF'
import os, shutil, subprocess, sys, tarfile, zipfile
src, dst = sys.argv[1], sys.argv[2]
with open(src, "rb") as f:
    magic = f.read(4)
if magic == b"LZIP":                    # .tar.lz (libjxl) — распаковывает системный lzip
    with open(src + ".tar", "wb") as out:
        subprocess.run(["lzip", "-dc", src], stdout=out, check=True)
    src += ".tar"
if zipfile.is_zipfile(src):
    zipfile.ZipFile(src).extractall(dst)
elif tarfile.is_tarfile(src):
    t = tarfile.open(src)
    try:
        t.extractall(dst, filter="data")
    except TypeError:                   # Python < 3.12
        t.extractall(dst)
else:
    os.makedirs(dst); shutil.copy(src, dst + "/file")
PYEOF
  then
    fail "$url: архив не распаковался (.tar.lz — нужен lzip) — поставьте вручную или --from"; rm -rf "$tmp"; return 0
  fi
  n=$(find "$tmp/x" -mindepth 1 -maxdepth 1 | wc -l)
  if [ "$n" = 1 ] && [ -d "$(find "$tmp/x" -mindepth 1 -maxdepth 1)" ]; then src="$(find "$tmp/x" -mindepth 1 -maxdepth 1)"; else src="$tmp/x"; fi
  if [ -n "$sub" ]; then src="$src/$sub"; fi
  mkdir -p "$DDD_HOME/bin/$top"; cp -a "$src/." "$DDD_HOME/bin/$top/"; rm -rf "$tmp"
}

from_find() {  # rel папка… → кандидаты: <папка>/<rel>, затем файлы с тем же именем в любой глубине папки
  local rel="$1" d
  shift
  for d in "$@"; do
    if [ ! -d "$d" ]; then continue; fi
    if [ -f "$d/$rel" ]; then printf '%s\n' "$d/$rel"; fi
    find "$d" -type f -name "$(basename "$rel")" 2>/dev/null | sort
  done | awk '!seen[$0]++'
}

place() {  # kind(bin|models) rel sha url [папка --from…]
  local kind="$1" rel="$2" want="$3" url="$4" dst="$DDD_HOME/$1/$2" found="" c base="" top inner
  shift 4
  if [ -f "$dst" ]; then
    if [ "$(sha "$dst")" = "$want" ]; then
      say "  ok   $rel"
      if [ "$kind" = bin ] && [ ! -x "$dst" ]; then run chmod +x "$dst"; fi
      return 0
    fi
    fail "$rel: sha256 $(sha "$dst" | cut -c1-12)… ≠ $(printf %.12s "$want")…"; return 0
  fi
  if [ $# -gt 0 ]; then
    while IFS= read -r c; do
      if [ -z "$c" ]; then continue; fi
      if [ "$(sha "$c")" = "$want" ]; then found="$c"; break; fi
      say "  в --from: $c — sha256 другой ($(sha "$c" | cut -c1-12)…)"
    done < <(from_find "$rel" "$@")
  fi
  if [ "$CHECK" = 1 ]; then
    if [ -n "$found" ]; then say "  нет  $rel — в --from есть, sha256 $(printf %.12s "$want")… сходится: $found"
    else say "  нет  $rel"; fi
    return 0
  fi
  if [ -n "$found" ]; then
    top="${rel%%/*}"; inner="${rel#*/}"
    case "$found" in */"$inner") base="${found%/"$inner"}" ;; esac
    for c in "$@"; do if [ "$base" = "${c%/}" ]; then base=""; fi; done   # сама папка --from — не папка инструмента
    say "  из --from: $found (sha256 $(printf %.12s "$want")… сходится)"
    if [ "$kind" = bin ] && [ -n "$base" ] && [ "$rel" != "$inner" ]; then
      run mkdir -p "$DDD_HOME/bin/$top"; run cp -a "$base/." "$DDD_HOME/bin/$top/"
    else
      run mkdir -p "$(dirname "$dst")"; run cp "$found" "$dst"
    fi
    if [ "$DRY" = 0 ]; then
      if [ "$(sha "$dst")" = "$want" ]; then say "  ok   $rel"; if [ "$kind" = bin ]; then chmod +x "$dst" 2>/dev/null || true; fi
      else fail "$rel: после копирования из --from sha256 другой"; fi
    fi
    return 0
  fi
  if [ $# -gt 0 ]; then say "  в --from нет $rel с этим sha256"; fi
  if [ "$url" = "-" ]; then say "  вручную: $rel (sha256 $want)"; return 0; fi
  if [ "$kind" = models ]; then
    run mkdir -p "$(dirname "$dst")"
    if ! run curl -fL --retry 2 -o "$dst" "$url"; then fail "$rel: загрузка не удалась — поставьте вручную или --models-from"; return 0; fi
  else fetch_unpack "$url" "${rel%%/*}"; fi
  if [ "$DRY" = 0 ]; then
    if [ -f "$dst" ] && [ "$(sha "$dst")" = "$want" ]; then say "  ok   $rel"; chmod +x "$dst" 2>/dev/null || true;
    else fail "$rel: после загрузки файла нет или sha256 другой — поставьте вручную (раскладка выше) или --from"; fi
  fi
}

if [ "$DO_BIN" = 1 ]; then
  step "бинарники в $DDD_HOME/bin (версии и sha256)"
  while IFS='|' read -r id ver rel want url; do
    say "  $id $ver"; place bin "$rel" "$want" "$url" ${FROM[@]+"${FROM[@]}"}
  done <<< "$BINS"
fi
if [ "$DO_MODELS" = 1 ]; then
  step "модели ONNX в $DDD_HOME/models (sha256; OCR — kb/ai-media/11-evaluation-qa/thresholds.yaml → ocr_models)"
  while IFS='|' read -r id rel want url; do
    say "  $id"; place models "$rel" "$want" "$url" ${MODELS_FROM[@]+"${MODELS_FROM[@]}"}
  done <<< "$MODELS"
fi

# ------------------------------------------------------------------ ffmpeg
if [ "$DO_FFMPEG" = 1 ] || [ "$CHECK" = 1 ]; then
  step "ffmpeg и ffprobe: системные, иначе статическая сборка в $DDD_HOME/bin/ffmpeg"
  SYS_FF="${DDD_FFMPEG:-$(command -v ffmpeg || true)}"; SYS_FP="${DDD_FFPROBE:-$(command -v ffprobe || true)}"
  if [ -d "$DDD_HOME/bin/ffmpeg" ]; then
    while IFS='|' read -r id ver rel want url; do say "  $id $ver"; place bin "$rel" "$want" "$url"; done <<< "$FFMPEG"
  elif [ -n "$SYS_FF" ] && [ -n "$SYS_FP" ]; then
    say "  системные: $SYS_FF, $SYS_FP — статическая сборка не нужна"
  elif [ "$CHECK" = 1 ]; then
    say "  нет  ffmpeg и ffprobe — install.sh --ffmpeg (статическая сборка) или системный пакет ffmpeg"
  else
    while IFS='|' read -r id ver rel want url; do
      say "  $id $ver"; place bin "$rel" "$want" "$url" ${FROM[@]+"${FROM[@]}"}
    done <<< "$FFMPEG"
  fi
fi

# ------------------------------------------------------------------ браузеры Playwright
if [ "$DO_BROWSERS" = 1 ]; then
  step "браузеры Playwright в $DDD_HOME/browsers (kbpaths ставит PLAYWRIGHT_BROWSERS_PATH, если каталог есть)"
  loc=""; if [ -x "$PY" ]; then loc="$(pw_loc "$DDD_HOME/browsers" || true)"; fi
  if [ -n "$loc" ] && [ -d "$loc" ]; then say "  chromium есть: $loc";
  else run env PLAYWRIGHT_BROWSERS_PATH="$DDD_HOME/browsers" "$PY" -m playwright install chromium; fi
fi

# ------------------------------------------------------------------ снимки каталогов (данные, пересоздаются бесплатно)
if [ "$DO_CATALOGS" = 1 ]; then
  step "снимки каталогов и список доверия C2PA в $DDD_HOME/cache/ai-media (бесплатные GET)"
  run "$PY" "$SCRIPTS/ai-media/polza_catalog.py" snapshot
  run "$PY" "$SCRIPTS/ai-media/mp_client.py" snapshot --channel all
  TRUST_DIR="$DDD_HOME/cache/ai-media/c2pa-trust-2026-09-23"
  TRUST_SHA=75cacc98b79ecac33713c7ecfb58d4a0ef383f3c1f886e7409f9e37e8664aea5
  if [ -f "$TRUST_DIR/C2PA-TRUST-LIST.pem" ]; then say "  список доверия C2PA есть";
  else
    run mkdir -p "$TRUST_DIR"
    run curl -fL --retry 2 -o "$TRUST_DIR/C2PA-TRUST-LIST.pem" https://raw.githubusercontent.com/c2pa-org/conformance-public/main/trust-list/C2PA-TRUST-LIST.pem
    if [ "$DRY" = 0 ] && [ "$(sha "$TRUST_DIR/C2PA-TRUST-LIST.pem")" != "$TRUST_SHA" ]; then
      say "  список доверия C2PA новее закреплённого снимка (sha256 другой) — это нормально; путь задаёт C2PA_TRUST_PEM"
    fi
  fi
fi

# ------------------------------------------------------------------ системное (только проверка)
step "системное (не ставится отсюда; путь — PATH или переменная DDD_*, поиск — scripts/lib/kbpaths.py)"
DDD_HOME="$DDD_HOME" "$PYU" "$SCRIPTS/lib/kbpaths.py" --bins 2>/dev/null | awk -F'\t' '
  $3 != "" { printf "  есть %s: %s%s\n", $1, $3, ($4 != "" ? " (" $4 ")" : ""); next }
  { printf "  нет  %s (путь — %s или PATH)\n", $1, $2 }' || say "  kbpaths.py --bins не запустился ($PYU)"
for b in flock bwrap systemd-run lzip uvx; do
  case "$b" in lzip) why="архив libjxl" ;; uvx) why="MCP Blender Lab — по желанию" ;; *) why="blender_supervisor" ;; esac
  p="$(command -v "$b" || true)"
  if [ -n "$p" ]; then say "  есть $b: $p"; else say "  нет  $b ($why)"; fi
done
say ""
[ "$ERR" = 0 ] && say "готово$([ "$DRY" = 1 ] && echo ' (--dry-run: ничего не менялось)')$([ "$WARN" = 1 ] && echo '; есть предупреждения (выше)')" || { say "есть ошибки (выше)"; exit 1; }
