#!/usr/bin/env python3
"""build_pages.py — три страницы «Ё» из одного шаблона: $S/{a-code,b-blender,c-hybrid}/ (тексты и сетка одинаковые).

    python3 build_pages.py [a] [b] [c]
Каждая папка самодостаточна: index.html, assets/ (page.css, fonts, img, data, model), dist/ (esbuild), src/ (исходники).
B — кадры Blender без three; C — GLB из Blender + код; A — модель кодом (кадры A снимает 09-capture со своей же страницы).
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
K = os.path.normpath(os.path.join(HERE, ".."))
R = "/home/mm/Документы/app-design/blender-research"
S = f"{R}/15-showcase/keyboard"
B_WEB = f"{K}/07-b/web/assets/img"
CAMS = f"{K}/07-b/cams"
NODE = "/home/mm/.nvm/versions/node/v24.21.0/bin"
NM = os.path.expanduser("~/.cache/blender-research/npm-trial/node_modules")
FONTS = f"{K}/05-code-a/assets/fonts"
P = json.load(open(f"{S}/passport.json"))
DIRS = {"a": "a-code", "b": "b-blender", "c": "c-hybrid"}
# телефон, набор касанием (решение оркестратора 1): окно 700 px кадра T (1600 × 900) — левая половина раскладки, клавиша
# ≈ 82 px кадра → ≈ 44 CSS px при ширине сцены 374 px; полоса 60…1550 × 140…740 (корпус целиком по высоте) листается вбок
TYPE_BAND = {"bx": 60, "by": 140, "bw": 1490, "bh": 600, "ww": 700, "fw": 1600, "fh": 900}
CFG = {"a": {"variant": "a", "staticPressFrames": False, "staticTurnFrames": False},
       "b": {"variant": "b"},
       "c": {"variant": "c", "staticPressFrames": True, "staticTurnFrames": False}}


def keys_js():
    ks = [{k: v for k, v in d.items() if k in ("id", "code", "l1", "l2", "l3", "row", "w", "role")} for d in P["layout"]]
    js = ("// keys.js — сгенерирован build_pages.py из passport.json (не править руками)\n"
          f"export const KEYS = {json.dumps(ks, ensure_ascii=False)};\n"
          f"export const RANGES = {json.dumps(P['explode_ranges'])};\n")
    open(os.path.join(HERE, "src", "keys.js"), "w").write(js)


def img(src, cls="st-img", alt="", eager=False, w=1600, h=900, mob=True, extra="", sizes="(max-width: 700px) 100vw, 1440px"):
    ss = f' srcset="{src}_m.avif {w // 2}w, {src}.avif {w}w" sizes="{sizes}"' if mob else ""
    return (f'      <img class="{cls}" src="{src}.avif"{ss} width="{w}" height="{h}" loading="{"eager" if eager else "lazy"}" '
            f'decoding="async" alt="{alt}"{extra}>')


def stages(v):
    p3 = " poster3d" if v in ("a", "c") else ""
    # телефон: кадр набора крупнее экрана в 1600/700 раз (клавиша ≈ 44 px) — берём полный кадр 1600 px
    t = img("assets/img/type/base", "st-img" + p3, "Клавиатура «Ё» сверху, расцветка «Снег»",
            sizes="(max-width: 700px) 860px, 1440px") + '\n      <div class="keylayer" aria-hidden="true"></div>'
    r = img("assets/img/turn/snow/d_000", "st-img" + p3, "", w=1280, h=800, mob=False)
    alts = ["в сборе", "колпачки сняты, свитчи поднимаются", "пластина и плата отделились", "латунная плита и корпус"]
    x = "\n".join(img(f"assets/img/x/s{i}", "st-frame" + (" on" if i == 0 else "") + p3, f"Разборка: {alts[i]}", w=1600, h=1000)
                  for i in range(4))
    return t, r, x


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def build(v):
    out = f"{os.environ.get('KB_PAGES_OUT', S)}/{DIRS[v]}"
    for sub in ("dist", "src", "assets"):
        if os.path.isdir(f"{out}/{sub}"):
            shutil.rmtree(f"{out}/{sub}")
    os.makedirs(out, exist_ok=True)
    tpl = open(os.path.join(HERE, "template.html")).read()
    t, r, x = stages(v)
    html = (tpl.replace("{{VARIANT}}", v).replace("{{STAGE_TYPE}}", t).replace("{{STAGE_TURN}}", r).replace("{{STAGE_X}}", x)
            .replace("{{CFG}}", json.dumps(CFG[v]))
            .replace("{{TYPE_BAND}}", ";".join(f"--{k}:{n}" for k, n in TYPE_BAND.items())))
    open(f"{out}/index.html", "w").write(html)
    copy(os.path.join(HERE, "page.css"), f"{out}/assets/page.css")
    for f in os.listdir(FONTS):
        copy(f"{FONTS}/{f}", f"{out}/assets/fonts/{f}")
    copy(f"{CAMS}/T_keys.json", f"{out}/assets/data/T_keys.json")
    # кадры: B и C — Blender; A — со своей страницы (09-capture/out → 07-b-подобная раскладка)
    src_img = B_WEB if v in ("b", "c") else f"{K}/09-capture/web/assets/img"
    for root, _, files in os.walk(src_img):
        rel = os.path.relpath(root, src_img)
        for f in files:
            rp = os.path.normpath(os.path.join(rel, f))
            if v != "b" and rp.startswith("turn/") and not (f.startswith("d_000") or f.startswith("m_000")):
                continue                                  # A/C: секвенция не нужна — один кадр на расцветку (reduce/постер)
            if v == "a" and rp == "shadow_floor.webp":
                continue
            if v == "b" and rp == "shadow_floor.webp":
                continue
            copy(os.path.join(root, f), f"{out}/assets/img/{rp}")
    if v in ("a", "c"):
        for n in ("T", "R", "X"):
            copy(f"{CAMS}/{n}.json", f"{out}/assets/data/{n}.json")
    if v == "a":
        copy(f"{S}/passport.json", f"{out}/assets/data/passport.json")
        for n in ("H2v2_desk", "H2v2_mob"):
            copy(f"{CAMS}/{n}.json", f"{out}/assets/data/{n}.json")
    if v == "c":
        copy(f"{CAMS}/shadow_floor.json", f"{out}/assets/data/shadow_floor.json")
        for f in ("kb_desk.glb", "kb_mob.glb"):
            copy(f"{K}/06-export/out/{f}", f"{out}/assets/model/{f}")
    # исходники (для чтения) и сборка
    for f in os.listdir(os.path.join(HERE, "src")):
        copy(os.path.join(HERE, "src", f), f"{out}/src/{f}")
    env = dict(os.environ, PATH=f"{NODE}:{os.environ['PATH']}", NODE_PATH=NM)
    cmd = [f"{NM}/.bin/esbuild", f"src/main_{v}.js", "--bundle", "--format=esm", "--splitting", "--minify", "--outdir=dist",
           "--legal-comments=eof", "--entry-names=main", "--chunk-names=c-[hash]", "--target=es2022", "--metafile=dist/meta.json"]
    r = subprocess.run(cmd, cwd=out, env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr)
        raise SystemExit(f"esbuild {v} failed")
    js = {f: os.path.getsize(f"{out}/dist/{f}") for f in os.listdir(f"{out}/dist") if f.endswith(".js")}
    print(v, DIRS[v], {k: round(b / 1024, 1) for k, b in sorted(js.items())})


if __name__ == "__main__":
    keys_js()
    for v in (sys.argv[1:] or ["b", "c", "a"]):
        build(v)
