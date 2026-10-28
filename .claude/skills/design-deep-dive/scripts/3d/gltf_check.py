#!/usr/bin/env python3
"""Проверка glTF/GLB: валидатор Khronos + инспекция gltf-transform + сводка «готово ли для веба».

Использование:
    python3 gltf_check.py model.glb [--out report.md] [--json]
Что печатает:
    - размер файла; версия генератора; extensionsUsed / extensionsRequired;
    - валидатор Khronos (gltf-validator 2.0.0-dev): число ошибок, предупреждений, info, hints и первые сообщения;
    - таблицы gltf-transform inspect (--format md): сцены, меши (вершины, индексы, атрибуты, размер в памяти GPU),
      материалы, текстуры (размер, формат, вес), анимации;
    - сводка-подсказка: несжатая геометрия (нет Draco/Meshopt), текстуры > 2048, PNG вместо WebP/KTX2,
      нет индексов, число мешей/материалов (оценка draw calls), тяжёлый файл (> 5 МБ).
Инструменты — npm-пакеты в $DDD_HOME/node (install.sh --npm-groups 3d): gltf-transform 4.5, gltfpack 1.2, gltf-validator,
meshoptimizer, draco3dgltf. Прямой вызов: cd $DDD_HOME/node && npx gltf-transform <команда> …  |  npx gltfpack -i in.glb
-o out.glb -cc
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import kbpaths  # noqa: E402
NODE_DIR = str(kbpaths.node_home())  # npm-зависимости — $DDD_HOME/node
NODE_BIN = os.path.dirname(kbpaths.node())
ENV = dict(os.environ, PATH=NODE_BIN + ":" + os.environ.get("PATH", ""))


def run(cmd, timeout=300):
    r = subprocess.run(cmd, cwd=NODE_DIR, capture_output=True, text=True, timeout=timeout, env=ENV)
    return r.returncode, r.stdout, r.stderr


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    f = os.path.abspath(a[0])
    out = a[a.index("--out") + 1] if "--out" in a else None
    size = os.path.getsize(f)
    lines = [f"# glTF check: {os.path.basename(f)}", "", f"- Файл: {f}", f"- Размер: {size/1024:.1f} КБ ({size} байт)"]
    code, so, se = run(["node", "validate.mjs", f])
    rep = {}
    try:
        rep = json.loads(so)
    except Exception:
        lines.append(f"- Валидатор не отработал: {se[-500:]}")
    issues = rep.get("issues", {})
    info = rep.get("info", {})
    if rep:
        lines += [f"- Генератор: {info.get('generator')}; версия glTF {info.get('version')}",
                  f"- extensionsUsed: {info.get('extensionsUsed') or []}; extensionsRequired: {info.get('extensionsRequired') or []}",
                  f"- Анимаций: {info.get('animationCount')}, материалов: {info.get('materialCount')}, "
                  f"вершин: {info.get('totalVertexCount')}, треугольников: {info.get('totalTriangleCount')}, "
                  f"draw calls: {info.get('drawCallCount')}, max UV: {info.get('maxUVs')}, max влияний: {info.get('maxInfluences')}, "
                  f"морф-таргеты: {info.get('hasMorphTargets')}, скины: {info.get('hasSkins')}, текстуры: {info.get('hasTextures')}",
                  "", "## Валидатор Khronos",
                  f"ошибок {issues.get('numErrors')}, предупреждений {issues.get('numWarnings')}, "
                  f"info {issues.get('numInfos')}, hints {issues.get('numHints')}"]
        for m in (issues.get("messages") or [])[:40]:
            sev = {0: "ERROR", 1: "WARN", 2: "INFO", 3: "HINT"}.get(m.get("severity"), m.get("severity"))
            lines.append(f"- [{sev}] {m.get('code')}: {m.get('message')} @ {m.get('pointer', '')}")
        res = info.get("resources") or []
        imgs = [r for r in res if r.get("image")]
        if imgs:
            lines += ["", "## Изображения (из валидатора)"]
            for r in imgs:
                im = r["image"]
                lines.append(f"- {r.get('pointer')}: {im.get('mimeType')} {im.get('width')}×{im.get('height')} "
                             f"{r.get('byteLength', '?')} байт, формат {im.get('format')}, primaries {im.get('primaries')}")
    code2, so2, se2 = run(["npx", "gltf-transform", "inspect", f, "--format", "md"])
    lines += ["", "## gltf-transform inspect", "", re.sub(r"\x1b\[[0-9;]*m", "", so2 or se2)]
    # подсказки
    hints = []
    ext = set((info.get("extensionsUsed") or []))
    if rep and not ({"KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_meshopt_compression"} & ext):
        hints.append("геометрия не сжата (нет Draco/Meshopt): для веба обычно сжимать")
    if rep and any((r.get("image") or {}).get("mimeType") == "image/png" for r in info.get("resources") or []):
        hints.append("есть PNG-текстуры: проверь WebP/AVIF/KTX2 (кроме карт, где нужна точность)")
    big = [r for r in (info.get("resources") or []) if r.get("image") and max(r["image"].get("width") or 0, r["image"].get("height") or 0) > 2048]
    if big:
        hints.append(f"текстур больше 2048 px: {len(big)}")
    if size > 5 * 1024 * 1024:
        hints.append("файл больше 5 МБ: тяжело для первого экрана лендинга")
    if rep and (info.get("drawCallCount") or 0) > 100:
        hints.append(f"draw calls {info.get('drawCallCount')}: подумай о join/instance/атласе материалов")
    lines += ["## Подсказки", ""] + ([f"- {h}" for h in hints] or ["- замечаний нет"])
    text = "\n".join(lines)
    if out:
        open(out, "w", encoding="utf-8").write(text)
    if "--json" in a:
        print(json.dumps({"size": size, "info": info, "issues": {k: v for k, v in issues.items() if k != "messages"},
                          "messages": (issues.get("messages") or [])[:50], "hints": hints}, ensure_ascii=False, indent=1))
    else:
        print(text)


if __name__ == "__main__":
    main()
