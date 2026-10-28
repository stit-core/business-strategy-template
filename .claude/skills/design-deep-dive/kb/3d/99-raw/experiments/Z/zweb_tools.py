#!/usr/bin/env python3
"""zweb_tools — web_view.py и gltf_diff.py базы без интернета: import map и декодеры → локальный three 0.186.0
(~/.cache/blender-research/npm-trial/node_modules/three, симлинк в папку раздачи). Инструменты базы не меняются —
подменяются только строка страницы и функция раздачи в памяти процесса.

    python3 zweb_tools.py view  model.glb OUT --tone neutral --env room --bg '#101215' [остальные ключи web_view]
    python3 zweb_tools.py diff  source.blend OUT --glb model.glb --tone neutral --engine cycles [ключи gltf_diff]
    python3 zweb_tools.py inspect model.glb --out r.json   (gltf_web_inspect без CDN: материалы, colorSpace, channel, имена, вызовы)
"""
import os
import sys

T = "/home/mm/Документы/app-design/blender-research/99-raw/tools"
N3 = os.path.expanduser("~/.cache/blender-research/npm-trial/node_modules/three")
sys.path.insert(0, T)


def localize(page):
    return (page.replace("https://cdn.jsdelivr.net/npm/three@__VER__/build/three.module.js", "./three/build/three.module.js")
                .replace("https://cdn.jsdelivr.net/npm/three@__VER__/examples/jsm/", "./three/examples/jsm/")
                .replace("`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/draco/gltf/`", "'./three/examples/jsm/libs/draco/gltf/'")
                .replace("`https://cdn.jsdelivr.net/npm/three@${CFG.ver}/examples/jsm/libs/basis/`", "'./three/examples/jsm/libs/basis/'"))


def wrap_serve(mod):
    orig = mod.serve

    def serve(d):
        link = os.path.join(d, "three")
        if not os.path.exists(link):
            os.symlink(N3, link)
        return orig(d)
    mod.serve = serve


def main():
    what, args = sys.argv[1], sys.argv[2:]
    if what == "view":
        import web_view as M
        M.VIEWER = localize(M.VIEWER)
        assert "jsdelivr" not in M.VIEWER, "в странице осталась ссылка на CDN"
        wrap_serve(M)
        sys.argv = ["web_view.py"] + args
        M.main()
    elif what == "diff":
        import gltf_diff as M
        M.PAGE = localize(M.PAGE)
        assert "jsdelivr" not in M.PAGE, "в странице осталась ссылка на CDN"
        wrap_serve(M)
        sys.argv = ["gltf_diff.py"] + args
        M.main()
    elif what == "inspect":                   # фаза 2: третий слой проверки GLB (что создал three) без сети
        import types
        import gltf_web_inspect as M
        M.PAGE = localize(M.PAGE)
        assert "jsdelivr" not in M.PAGE, "в странице осталась ссылка на CDN"
        # Z3: у gltf_web_inspect нет serve() — раздаёт свою временную папку; кладём туда симлинк локального three
        orig_mk = M.tempfile.mkdtemp

        def mkdtemp(*a, **k):
            d = orig_mk(*a, **k)
            os.symlink(N3, os.path.join(d, "three"))
            return d
        M.tempfile = types.SimpleNamespace(mkdtemp=mkdtemp)
        sys.argv = ["gltf_web_inspect.py"] + args
        M.main()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
