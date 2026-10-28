"""stamp_shots.py — «Образец акта» со штампом (B/C, SD2): середина клипа, конец, reduce, телефон; числа (какой источник
выбран, байты видео, стало ли видно видео, конечное состояние). A — тот же снимок секции (CSS-штамп «Образец»).
    python3 stamp_shots.py PAGE_DIR OUT_DIR PREFIX [--mobile] [--reduce] [--gpu]"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_shots import serve, GPU  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


def main():
    a = sys.argv[1:]
    root, out, pre = os.path.abspath(a[0]), os.path.abspath(a[1]), a[2]
    mobile, reduce = "--mobile" in a, "--reduce" in a
    os.makedirs(out, exist_ok=True)
    srv, port = serve(root)
    res = {"mobile": mobile, "reduce": reduce}
    vids = []
    with sync_playwright() as pw:
        # SD3: без GPU-флагов fx_probe — с ними декодер видео в headless-shell падает (MEDIA_ERR_DECODE, shots/sd3_video)
        b = pw.chromium.launch(headless=True, args=GPU if "--gpu" in a else [])
        kw = dict(pw.devices["Pixel 7"]) if mobile else dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        ctx = b.new_context(**kw, reduced_motion="reduce" if reduce else "no-preference")
        p = ctx.new_page()
        logs = []
        p.on("console", lambda m: logs.append(f"{m.type}: {m.text[:200]}"))
        p.on("response", lambda r: vids.append((r.url.split("/")[-1], r.headers.get("content-length"))) if r.url.endswith((".webm", ".mp4")) else None)
        p.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load")
        p.wait_for_timeout(600)
        has = p.evaluate("!!document.querySelector('.doc__stamp3d')")
        res["has_stamp"] = has
        # подвести акт в центр окна плавно (как прокрутка посетителя)
        y = p.evaluate("(() => { const d = document.querySelector('.doc'); const r = d.getBoundingClientRect(); return Math.round(scrollY + r.top + r.height / 2 - innerHeight / 2); })()")
        for k in range(1, 9):
            p.evaluate(f"window.scrollTo(0, {y * k / 8})"); p.wait_for_timeout(60)
        clip = p.evaluate("(() => { const s = document.querySelector('.sample'); const r = s.getBoundingClientRect(); return {x: 0, y: Math.max(0, r.top), width: innerWidth, height: Math.min(innerHeight, r.bottom) - Math.max(0, r.top)}; })()")
        if has and not reduce:
            t0 = time.time()
            try:
                p.wait_for_function("(() => { const v = document.querySelector('.stamp3d__clip'); return v && v.currentTime > 0.55; })()", timeout=8000, polling=16)
                p.screenshot(path=f"{out}/{pre}_mid.png", clip=clip)
                res["mid_t"] = p.evaluate("document.querySelector('.stamp3d__clip').currentTime")
            except Exception as e:
                res["mid_err"] = str(e)[:120]
            p.wait_for_timeout(2200)
            res["state"] = p.evaluate("""(() => { const v = document.querySelector('.stamp3d__clip'), sb = document.querySelector('.doc__stamp3d');
                return {cls: sb.className, src: v.currentSrc.split('/').pop(), ended: v.ended, t: v.currentTime, dur: v.duration}; })()""")
            res["wait_s"] = round(time.time() - t0, 2)
        else:
            p.wait_for_timeout(1500)
            if has:
                res["state"] = p.evaluate("""(() => { const v = document.querySelector('.stamp3d__clip'), sb = document.querySelector('.doc__stamp3d');
                    return {cls: sb.className, src: v.currentSrc, networkState: v.networkState}; })()""")
        p.screenshot(path=f"{out}/{pre}_end.png", clip=clip)
        res["videos"] = vids
        res["console"] = logs[:10]
        b.close()
    srv.shutdown()
    json.dump(res, open(f"{out}/{pre}_stamp.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
