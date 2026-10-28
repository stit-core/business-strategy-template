#!/usr/bin/env python3
"""stage_stand.py — кадры, листы кадров и замеры сцен на своём движке WebGL2 (стенд `stand.html` в Chromium с GPU).

    python3 stage_stand.py shot  OUT.png  m=world src=world-template.js w=1440 h=760 dsf=2 [p=0.5 t=2 hx=0.3 hy=0 tap=0,0 mobile rtl variant=hero]
    python3 stage_stand.py sheet OUT.jpg  КОЛОНОК  'm=world src=world-template.js w=1440 h=760 p=0' 'm=world … p=0.25' …
    python3 stage_stand.py perf  m=world src=world-template.js w=1440 h=760 dsf=2 [--budget 17]   медиана и p90 интервала кадров за 3 с
    python3 stage_stand.py bench m=world src=world-template.js w=1440 h=760 dsf=2 [ps=0.15,0.5,0.85] цена кадра: redraw + readPixels
    python3 stage_stand.py --selftest

Сцена — файл движка по контракту `kb/3d/16-js-scenes/01-engine.md`; стенд и набор — `kb/3d/16-js-scenes/examples/`.
Корень раздачи — `--root DIR` (по умолчанию папка набора): сцены проекта кладут рядом со своей копией `stand.html`.
Ключи кадра: m (имя регистрации), src (путь файла сцены от корня), p, t, hx, hy, tap, pulse, bg, tex, variant, bench, ps;
флаги: mobile, rtl, live; размер окна — w, h, плотность — dsf. Кадр при одинаковых p и t одинаков.
`--soft` — программный рендер SwiftShader: кадры годны, замеры — нет. `perf` даёт вердикт `ok` по бюджету `--budget`
(мс, медиана; по умолчанию 17 — одна живая сцена на эталонной встроенной графике). Ошибка шейдера — код 1 и журнал
сборки. Замок браузера утилита берёт сама (kbpaths.lock("browser")). Выход — путь файла или JSON в stdout; листы
собирает Pillow, промежуточные кадры — во временной папке.
"""
from __future__ import annotations

import functools
import http.server
import json
import os
import socketserver
import sys
import tempfile
import threading
import urllib.parse
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

ROOT = kbpaths.kb("3d", "16-js-scenes", "examples")
GPU = ["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=vulkan", "--enable-features=Vulkan"]
SOFT = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
KEYS = ("m", "src", "p", "t", "hx", "hy", "tap", "pulse", "bg", "tex", "variant", "bench", "ps")
FLAGS = ("mobile", "rtl", "live")
BUDGET_MS = 17.0


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


@contextmanager
def server(root):
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(root)))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def parse(args):
    """['m=world', 'mobile'] → {'m': 'world', 'mobile': True}."""
    spec = {}
    for a in args:
        k, eq, v = a.partition("=")
        spec[k] = v if eq else True
    return spec


def url_of(base, spec):
    q = urllib.parse.urlencode({k: spec[k] for k in KEYS if k in spec})
    flags = [f for f in FLAGS if spec.get(f)]
    tail = "&".join(flags)
    return f"{base}/stand.html?{q}" + (("&" if q else "") + tail if tail else "")


def launch(pw, soft):
    args = SOFT if soft else GPU
    try:
        return pw.chromium.launch(channel="chromium", args=args)
    except Exception:  # noqa: BLE001 — сборка Playwright без канала chromium
        return pw.chromium.launch(args=args)


def render(specs, root=ROOT, soft=False):
    """specs: [{'m': 'world', 'src': 'world-template.js', 'w': 1440, 'h': 760, 'dsf': 2, 'out': 'a.png', …}] →
    пути PNG или словари замеров, в порядке specs."""
    from playwright.sync_api import sync_playwright
    if not (Path(root) / "stand.html").is_file():
        raise FileNotFoundError(f"нет stand.html в {root}")
    out = []
    with kbpaths.lock("browser"), server(root) as base, sync_playwright() as pw:
        b = launch(pw, soft)
        try:
            for sp in specs:
                ctx = b.new_context(viewport={"width": int(sp.get("w", 1440)), "height": int(sp.get("h", 760))},
                                    device_scale_factor=float(sp.get("dsf", 1)))
                pg = ctx.new_page()
                pg.goto(url_of(base, sp), wait_until="load", timeout=60000)
                pg.wait_for_function("window.__ready === true", timeout=90000)
                err = pg.evaluate("window.__err || null")
                if err:
                    raise RuntimeError(f"{sp.get('m')} {sp.get('src')}: {err}")
                if sp.get("bench"):
                    out.append(pg.evaluate("window.__bench"))
                elif sp.get("live"):
                    out.append(pg.evaluate("window.__perf"))
                else:
                    path = Path(sp["out"])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    pg.screenshot(path=str(path))
                    out.append(path)
                ctx.close()
        finally:
            b.close()
    return out


def sheet(paths, cols, out, width=1440):
    """Лист кадров: колонки одной ширины, строки — по самому высокому кадру ряда."""
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    cw = width // cols
    tiles = [im.resize((cw, round(im.height * cw / im.width)), Image.LANCZOS) for im in ims]
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    hs = [max(t.height for t in r) for r in rows]
    canvas = Image.new("RGB", (cw * cols, sum(hs)), (10, 11, 14))
    y = 0
    for r, h in zip(rows, hs):
        for j, t in enumerate(r):
            canvas.paste(t, (j * cw, y))
        y += h
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, quality=86)
    return Path(out)


def verdict(perf, budget=BUDGET_MS, soft=False):
    """perf от стенда ({median, p90, …}) → он же с полями budget_ms, ok; на программном рендере ok — None."""
    res = dict(perf or {})
    med = res.get("median")
    res["budget_ms"] = budget
    res["ok"] = None if soft or med is None else bool(med <= budget)
    if soft:
        res["note"] = "программный рендер: замер недействителен"
    return res


def opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        val = argv[i + 1]
        del argv[i:i + 2]
        return val
    return default


def selftest():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(("OK   " if cond else "FAIL ") + name)

    sp = parse(["m=world", "src=world-template.js", "p=0.5", "mobile", "w=390"])
    check("parse: ключи и флаги", sp == {"m": "world", "src": "world-template.js", "p": "0.5", "mobile": True, "w": "390"})
    u = url_of("http://x", sp)
    check("url_of: ключи стенда, флаг в хвосте, размер окна не в адресе",
          u.startswith("http://x/stand.html?m=world&src=world-template.js&p=0.5") and u.endswith("&mobile")
          and "w=390" not in u)
    check("verdict: медиана в бюджете — ok", verdict({"median": 9.5, "p90": 12})["ok"] is True)
    check("verdict: медиана сверх бюджета — не ok", verdict({"median": 21})["ok"] is False)
    check("verdict: программный рендер — без вердикта", verdict({"median": 5}, soft=True)["ok"] is None)
    check("набор на месте: stand.html и шаблоны", all((ROOT / f).is_file() for f in
                                                      ("stand.html", "scene-template.js", "world-template.js")))
    try:
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            ps = []
            for i, (w, h) in enumerate([(200, 100), (200, 140), (200, 100)]):
                p = Path(td) / f"{i}.png"
                Image.new("RGB", (w, h), (i * 60, 40, 40)).save(p)
                ps.append(p)
            sh = Image.open(sheet(ps, 2, Path(td) / "s.jpg", width=400))
            check("sheet: 2 колонки по 200 px, строки по самому высокому кадру", sh.size == (400, 240))
    except ImportError:
        check("sheet: Pillow стоит (группа pip core)", False)
    print("stage_stand selftest: " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv):
    argv = list(argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "--selftest":
        return selftest()
    soft = "--soft" in argv
    if soft:
        argv.remove("--soft")
    root = Path(opt(argv, "--root", str(ROOT))).resolve()
    budget = float(opt(argv, "--budget", BUDGET_MS))
    cmd = argv[0]
    try:
        if cmd == "shot" and len(argv) >= 2:
            sp = parse(argv[2:])
            sp["out"] = str(Path(argv[1]).resolve())
            print(render([sp], root, soft)[0])
        elif cmd == "sheet" and len(argv) >= 4:
            out, cols = Path(argv[1]).resolve(), int(argv[2])
            with tempfile.TemporaryDirectory(prefix="stage_sheet_") as td:
                specs = [parse(s.split()) for s in argv[3:]]
                for i, sp in enumerate(specs):
                    sp["out"] = str(Path(td) / f"{i:02d}.png")
                print(sheet(render(specs, root, soft), cols, out))
        elif cmd in ("perf", "bench"):
            sp = parse(argv[1:])
            if cmd == "perf":
                sp["live"] = True
                res = verdict(render([sp], root, soft)[0], budget, soft)
            else:
                sp.setdefault("bench", "15")
                res = render([sp], root, soft)[0]
            print(json.dumps(res, ensure_ascii=False))
            if cmd == "perf" and res.get("ok") is False:
                return 1
        else:
            print(__doc__)
            return 2
    except RuntimeError as e:
        print(f"ошибка сцены: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
